"""Opt-in structural acceptance probe for a private EPUB corpus.

The report contains relative file identifiers, hashes, structural metrics, tool
versions, and discrepancy classes.  It never serializes navigation labels or
book prose.
"""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
import shutil
import subprocess
import unicodedata
from collections import Counter
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory

import ebooklib
import pypandoc
import typer
from lxml import etree

from audiobooks.epub_sections import select_sections
from audiobooks.epub_structure import EpubInventory, NavigationNode, inventory_epub
from audiobooks.source_units import sha256

CALIBRE_PROBE = r"""
from calibre.ebooks.oeb.polish.container import get_container
from calibre.ebooks.oeb.polish.toc import get_toc
import json, sys
container = get_container(sys.argv[-2])
toc = get_toc(container, verify_destinations=True)
with open(sys.argv[-1], 'w', encoding='utf-8') as stream:
    json.dump({'opf_name': container.opf_name, 'toc': toc.to_dict()}, stream, ensure_ascii=False, sort_keys=True)
"""


def tool_version(command: list[str]) -> str | None:
    if shutil.which(command[0]) is None:
        return None
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    text = (result.stdout or result.stderr).strip().splitlines()
    return text[0] if text else f"exit {result.returncode}"


def normalized_label(value: str | None) -> str:
    return " ".join(unicodedata.normalize("NFC", value or "").split())


def private_hash(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def selected_nodes(inventory: EpubInventory) -> tuple[str | None, list[NavigationNode]]:
    nav = [node for node in inventory.navigation if node.source == "epub3-nav"]
    ncx = [node for node in inventory.navigation if node.source == "epub2-ncx"]
    try:
        major = int((inventory.package_version or "0").split(".", 1)[0])
    except ValueError:
        major = 0
    if major >= 3 and nav:
        return "epub3-nav", nav
    if ncx:
        return "epub2-ncx", ncx
    if nav:
        return "epub3-nav", nav
    return None, []


def node_signature(node: NavigationNode) -> tuple:
    valid = node.resource_exists and (node.fragment is None or node.fragment_exists is True)
    return (
        normalized_label(node.raw_label),
        node.resource_href,
        node.fragment,
        node.level,
        valid if node.raw_target is not None else None,
    )


def navigation_relationship(inventory: EpubInventory) -> str:
    nav = [node_signature(node) for node in inventory.navigation if node.source == "epub3-nav"]
    ncx = [node_signature(node) for node in inventory.navigation if node.source == "epub2-ncx"]
    if not nav or not ncx:
        return "single-source"
    if nav == ncx:
        return "equivalent"
    if len(ncx) == len(nav) + 1 and any(
        ncx[:index] + ncx[index + 1 :] == nav for index in range(len(ncx))
    ):
        return "ncx-single-extra"
    if len(nav) == len(ncx) + 1 and any(
        nav[:index] + nav[index + 1 :] == ncx for index in range(len(nav))
    ):
        return "nav-single-extra"
    return "material-candidate"


def flatten_calibre(root: dict, opf_name: str) -> list[tuple]:
    flattened: list[tuple] = []

    def walk(node: dict, level: int) -> None:
        for child in node.get("children", []):
            destination = child.get("dest")
            if destination is not None:
                destination = posixpath.relpath(destination, posixpath.dirname(opf_name) or ".")
            flattened.append(
                (
                    normalized_label(child.get("title")),
                    destination,
                    child.get("frag"),
                    level,
                    child.get("dest_exists"),
                )
            )
            walk(child, level + 1)

    walk(root, 1)
    return flattened


def calibre_toc(path: Path, temporary: Path) -> tuple[list[tuple] | None, str | None]:
    output = temporary / (hashlib.sha256(str(path).encode()).hexdigest() + ".json")
    result = subprocess.run(
        ["calibre-debug", "-c", CALIBRE_PROBE, str(path), str(output)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode or not output.exists():
        return None, f"exit-{result.returncode}"
    payload = json.loads(output.read_text())
    return flatten_calibre(payload["toc"], payload["opf_name"]), None


def compare_with_calibre(nodes: list[NavigationNode], calibre: list[tuple]) -> dict:
    ours = [node_signature(node) for node in nodes]
    differences: list[dict] = []
    for index in range(max(len(ours), len(calibre))):
        left = ours[index] if index < len(ours) else None
        right = calibre[index] if index < len(calibre) else None
        if left != right:
            differences.append(
                {
                    "ordinal": index + 1,
                    "label_agrees": bool(left and right and left[0] == right[0]),
                    "target_agrees": bool(left and right and left[1:3] == right[1:3]),
                    "level_agrees": bool(left and right and left[3] == right[3]),
                    "validity_agrees": bool(left and right and left[4] == right[4]),
                }
            )
    return {
        "ours_count": len(ours),
        "calibre_count": len(calibre),
        "signature_hash": private_hash(ours),
        "calibre_signature_hash": private_hash(calibre),
        "differences": differences,
    }


def run_diagnostics(path: Path, temporary: Path, run: bool) -> dict:
    if not run:
        return {"pandoc": "skipped", "epubcheck": "skipped"}
    pandoc_output = temporary / (hashlib.sha256(str(path).encode()).hexdigest() + ".pandoc.json")
    pandoc = subprocess.run(
        [pypandoc.get_pandoc_path(), str(path), "-t", "json", "-o", str(pandoc_output)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    epubcheck = subprocess.run(
        ["epubcheck", "-q", str(path)], capture_output=True, text=True, timeout=120
    )
    fatal = bool(re.search(r"\bFATAL\b", epubcheck.stdout + epubcheck.stderr, flags=re.IGNORECASE))
    return {
        "pandoc": {"exit_code": pandoc.returncode, "json_created": pandoc_output.exists()},
        "epubcheck": {"exit_code": epubcheck.returncode, "fatal_reported": fatal},
    }


def audit_corpus(
    output: Path,
    corpus: Path | None = typer.Option(None, envvar="TEXTS_CORPUS"),
    seed: int = 20260919,
    sample_size: int = 40,
    diagnostics: bool = True,
) -> None:
    """Compare deterministic corpus structure with Calibre and diagnostics."""
    if corpus is None or not corpus.is_dir():
        raise ValueError("set TEXTS_CORPUS or pass --corpus with an EPUB directory")
    if output.exists():
        raise ValueError("refusing to replace an existing acceptance report")
    paths = sorted(
        path for path in corpus.rglob("*") if path.is_file() and path.suffix.lower() == ".epub"
    )
    if len(paths) < sample_size:
        raise ValueError(f"corpus has {len(paths)} EPUBs; {sample_size} required")
    calibre_version = tool_version(["calibre-debug", "--version"])
    epubcheck_version = tool_version(["epubcheck", "--version"])
    if calibre_version is None or (diagnostics and epubcheck_version is None):
        raise ValueError("Calibre and, when diagnostics run, EPUBCheck must be installed")

    inventories = {path: inventory_epub(path) for path in paths}
    deficient = {path for path, inv in inventories.items() if len(selected_nodes(inv)[1]) <= 1}
    seeded = set(Random(seed).sample(paths, sample_size))
    selected = seeded | deficient
    records: list[dict] = []
    with TemporaryDirectory() as directory:
        temporary = Path(directory)
        for path in sorted(selected):
            inventory = inventories[path]
            source, nodes = selected_nodes(inventory)
            selection = select_sections(inventory, epub_path=path)
            calibre, calibre_error = calibre_toc(path, temporary)
            comparison = None if calibre is None else compare_with_calibre(nodes, calibre)
            diagnostics_record = run_diagnostics(path, temporary, diagnostics)
            relative = path.relative_to(corpus).as_posix()
            records.append(
                {
                    "relative_id": relative,
                    "file_hash": sha256(path),
                    "selected_by_seed": path in seeded,
                    "deficient_included": path in deficient,
                    "package_version": inventory.package_version,
                    "spine_items": len(inventory.spine),
                    "nonlinear_spine_items": sum(not item.linear for item in inventory.spine),
                    "navigation_counts": dict(
                        Counter(node.source for node in inventory.navigation)
                    ),
                    "navigation_relationship": navigation_relationship(inventory),
                    "selected_source": source,
                    "section_selection_source": selection.primary_source,
                    "section_selection_status": selection.status,
                    "section_boundary_count": len(selection.boundaries),
                    "section_issue_classes": sorted(
                        {issue.split(":", 1)[0] for issue in selection.issues}
                    ),
                    "unresolved_resources": sum(
                        node.raw_target is not None and not node.resource_exists
                        for node in inventory.navigation
                    ),
                    "unresolved_fragments": sum(
                        node.fragment is not None and node.fragment_exists is False
                        for node in inventory.navigation
                    ),
                    "calibre_error": calibre_error,
                    "calibre_comparison": comparison,
                    "diagnostics": diagnostics_record,
                }
            )
    aggregates = {
        "corpus_books": len(paths),
        "selected_books": len(records),
        "deficient_books": len(deficient),
        "calibre_failures": sum(record["calibre_error"] is not None for record in records),
        "calibre_discrepancy_books": sum(
            bool(record["calibre_comparison"] and record["calibre_comparison"]["differences"])
            for record in records
        ),
        "material_nav_ncx_candidates": sum(
            record["navigation_relationship"] == "material-candidate" for record in records
        ),
        "fallback_selection_books": sum(
            record["section_selection_source"] == "content-structure" for record in records
        ),
        "blocked_admissions": sum(
            record["section_selection_status"] == "blocked" for record in records
        ),
        "unresolved_resources": sum(record["unresolved_resources"] for record in records),
        "unresolved_fragments": sum(record["unresolved_fragments"] for record in records),
        "pandoc_failures": sum(
            record["diagnostics"]["pandoc"] != "skipped"
            and record["diagnostics"]["pandoc"]["exit_code"] != 0
            for record in records
        ),
        "epubcheck_nonzero_books": sum(
            record["diagnostics"]["epubcheck"] != "skipped"
            and record["diagnostics"]["epubcheck"]["exit_code"] != 0
            for record in records
        ),
        "epubcheck_fatal_books": sum(
            record["diagnostics"]["epubcheck"] != "skipped"
            and record["diagnostics"]["epubcheck"]["fatal_reported"]
            for record in records
        ),
    }
    report = {
        "acceptance_version": 2,
        "seed": seed,
        "sample_size": sample_size,
        "tools": {
            "ebooklib": ".".join(map(str, ebooklib.VERSION)),
            "lxml": ".".join(map(str, etree.LXML_VERSION)),
            "pandoc": pypandoc.get_pandoc_version(),
            "calibre": calibre_version,
            "epubcheck": epubcheck_version,
            "readium": "unavailable-not-run",
        },
        "aggregates": aggregates,
        "books": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    typer.echo(json.dumps(aggregates, sort_keys=True))
