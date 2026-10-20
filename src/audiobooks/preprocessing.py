"""EPUB inspection and reviewed prepared-bundle migration commands."""

import json
import shutil
from pathlib import Path

import typer
from pydantic import TypeAdapter

from audiobooks.epub_sections import select_sections
from audiobooks.epub_structure import inventory_epub
from audiobooks.source_units import Section, admit, sha256

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)


@app.command("inspect")
def inspect(epub: Path, output: Path | None = None) -> None:
    """Emit the lossless EPUB package and navigation inventory as JSON."""
    inventory = inventory_epub(epub)
    rendered = inventory.model_dump_json(indent=2)
    if output is None:
        typer.echo(rendered)
    else:
        if output.exists():
            raise ValueError("refusing to replace existing inventory")
        output.write_text(rendered + "\n")
        typer.echo(
            f"wrote {len(inventory.spine)} spine items and {len(inventory.navigation)} navigation nodes"
        )


@app.command("select-sections")
def select(epub: Path, output: Path | None = None) -> None:
    """Emit conservative section decisions; exit with status two when blocked."""
    inventory = inventory_epub(epub)
    selection = select_sections(inventory, epub_path=epub)
    rendered = selection.model_dump_json(indent=2)
    if output is None:
        typer.echo(rendered)
    else:
        if output.exists():
            raise ValueError("refusing to replace existing section report")
        output.write_text(rendered + "\n")
        typer.echo(f"{selection.status}: {len(selection.boundaries)} section boundaries")
    if selection.status == "blocked":
        raise typer.Exit(code=2)


@app.command("upgrade")
def upgrade(version_one: Path, decisions: Path, output: Path) -> None:
    """Freeze explicit section decisions without guessing them from version one."""
    manifest, _ = admit(version_one, required_version=1)
    if output.exists():
        raise ValueError("output bundle already exists")
    section_records = TypeAdapter(list[Section]).validate_json(decisions.read_text())
    if [record.section_id for record in section_records] != manifest["section_ids"]:
        raise ValueError("decision records must cover the version-one section spine in order")
    shutil.copytree(version_one, output)
    section_path = output / "sections.jsonl"
    section_path.write_text("".join(record.model_dump_json() + "\n" for record in section_records))
    revised = {
        **manifest,
        "prepared_text_version": 2,
        "hashes": {**manifest["hashes"], "sections.jsonl": sha256(section_path)},
        "checks": [
            *manifest.get("checks", []),
            "Reviewed explicit sections cover every prepared unit contiguously and bind delivery titles.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(revised, ensure_ascii=False, indent=2) + "\n")
    admit(output, required_version=2)
    typer.echo(f"{len(section_records)} reviewed sections frozen as prepared version two")
