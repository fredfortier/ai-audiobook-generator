"""Verify prepared provenance and partition complete units without changing prose."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import panflute as pf
from pydantic import Field

from audiobooks.script_contract import Record, parse_document, project_text


def sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def identity(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


class Unit(Record):
    id: str = Field(pattern=r"^u[0-9]{6,}$")
    ordinal: int = Field(ge=1)
    section_id: str
    kind: Literal["heading", "paragraph", "verse", "list_item"]
    role: Literal["body", "paratext", "unknown"]
    source_locators: list[str] = Field(min_length=1)
    source_text: str
    prepared_text: str = Field(min_length=1)
    print_pages: list[str]
    note_call_spans: list[tuple[int, int]]
    preparation_changes: list[str]
    heading_level: int | None = Field(default=None, ge=1, le=6)


class SectionEvidence(Record):
    source_kind: Literal["epub3-nav", "epub2-ncx", "content-structure", "calibre-candidate", "manual"]
    source_location: str
    raw_value: str | None
    resolved_value: str | None
    decision: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class Section(Record):
    section_id: str
    ordinal: int = Field(ge=1)
    parent_section_id: str | None
    level: int = Field(ge=1)
    role: Literal["body", "paratext", "unknown"]
    navigation_source: Literal["epub3-nav", "epub2-ncx", "content-structure", "calibre-candidate", "manual"]
    raw_title: str | None
    title_unit_id: str | None
    target_href: str | None
    target_fragment: str | None
    start_unit_id: str
    delivery_chapter: bool
    evidence: list[SectionEvidence] = Field(min_length=1)
    issues: list[str]


class SectionProjection(Record):
    """Reviewed bridge from a source boundary to the prepared unit spine."""
    section_id: str
    parent_section_id: str | None
    level: int = Field(ge=1)
    role: Literal["body", "paratext", "unknown"]
    navigation_source: Literal["epub3-nav", "epub2-ncx", "content-structure", "calibre-candidate", "manual"]
    raw_title: str
    boundary_unit_id: str
    content_title_unit_id: str | None
    source_location: str
    target_href: str | None
    target_fragment: str | None
    delivery_chapter: bool
    issues: list[str]


def _comparable_title(value: str) -> str:
    return " ".join(value.casefold().strip(" \t\r\n.,:;!?—–-_'\"").split())


def project_section_titles(
    units: list[Unit], projections: list[SectionProjection]
) -> tuple[list[Unit], list[Section]]:
    """Assign contiguous sections and insert navigation-only titles exactly once.

    Boundary-to-unit mapping is deliberately reviewed input: DOM-to-Markdown
    conversion can change element shape, so this function does not guess it.
    """
    if not units or not projections:
        raise ValueError("units and section decisions are required")
    if len({unit.id for unit in units}) != len(units):
        raise ValueError("duplicate source unit IDs")
    if len({projection.section_id for projection in projections}) != len(projections):
        raise ValueError("duplicate section IDs")
    unit_by_id = {unit.id: unit for unit in units}
    position_by_unit_id = {unit.id: index for index, unit in enumerate(units)}
    boundary_positions: list[int] = []
    for projection in projections:
        if projection.boundary_unit_id not in unit_by_id:
            raise ValueError(f"unknown boundary unit: {projection.boundary_unit_id}")
        boundary_positions.append(position_by_unit_id[projection.boundary_unit_id])
    if boundary_positions != sorted(boundary_positions) or len(set(boundary_positions)) != len(boundary_positions):
        raise ValueError("section boundaries must be unique and monotonic")
    if boundary_positions[0] != 0:
        raise ValueError("first included unit must belong to a selected section")

    next_numeric_id = max(int(unit.id[1:]) for unit in units) + 1
    projected: list[Unit] = []
    projected_sections: list[Section] = []
    for projection_index, projection in enumerate(projections):
        start = boundary_positions[projection_index]
        stop = (boundary_positions[projection_index + 1]
                if projection_index + 1 < len(projections) else len(units))
        source_slice = units[start:stop]
        if projection.content_title_unit_id is not None:
            if projection.content_title_unit_id != projection.boundary_unit_id:
                raise ValueError(f"content title must be the section start: {projection.section_id}")
            title_unit = unit_by_id[projection.content_title_unit_id]
            if title_unit.kind != "heading":
                raise ValueError(f"content title is not a heading: {projection.section_id}")
            projected_title = title_unit.model_copy(update={"section_id": projection.section_id})
            projected.append(projected_title)
            projected.extend(unit.model_copy(update={"section_id": projection.section_id})
                             for unit in source_slice[1:])
            title_unit_id = projected_title.id
            start_unit_id = projected_title.id
            reason = "authored content heading retained without duplication"
        else:
            title_unit_id = f"u{next_numeric_id:06d}"
            next_numeric_id += 1
            projected_title = Unit(
                id=title_unit_id, ordinal=1, section_id=projection.section_id, kind="heading",
                role=projection.role, source_locators=[projection.source_location],
                source_text=projection.raw_title, prepared_text=projection.raw_title,
                print_pages=[], note_call_spans=[],
                preparation_changes=["navigation-label projection"],
                heading_level=min(projection.level, 6))
            projected.append(projected_title)
            projected.extend(unit.model_copy(update={"section_id": projection.section_id})
                             for unit in source_slice)
            start_unit_id = title_unit_id
            reason = "navigation label projected because no equivalent content heading exists"
        projected_sections.append(Section(
            section_id=projection.section_id, ordinal=projection_index + 1,
            parent_section_id=projection.parent_section_id, level=projection.level,
            role=projection.role, navigation_source=projection.navigation_source,
            raw_title=projection.raw_title, title_unit_id=title_unit_id,
            target_href=projection.target_href, target_fragment=projection.target_fragment,
            start_unit_id=start_unit_id, delivery_chapter=projection.delivery_chapter,
            evidence=[SectionEvidence(
                source_kind=projection.navigation_source,
                source_location=projection.source_location,
                raw_value=projection.raw_title, resolved_value=title_unit_id,
                decision="selected", reason=reason)], issues=projection.issues))
    projected = [unit.model_copy(update={"ordinal": index}) for index, unit in enumerate(projected, 1)]
    return projected, projected_sections


def sections(bundle: Path, manifest: dict, units: list[Unit]) -> list[Section]:
    if manifest.get("prepared_text_version") != 2:
        raise ValueError("prepared bundle has no explicit section contract; migrate version one")
    path = bundle / "sections.jsonl"
    if sha256(path) != manifest["hashes"].get("sections.jsonl"):
        raise ValueError("changed prepared file: sections.jsonl")
    result = [Section.model_validate_json(line) for line in path.read_text().splitlines()]
    if not result or [section.ordinal for section in result] != list(range(1, len(result) + 1)):
        raise ValueError("section ordinals must be contiguous")
    if len({section.section_id for section in result}) != len(result):
        raise ValueError("duplicate section IDs")
    ids = [section.section_id for section in result]
    if ids != manifest["section_ids"]:
        raise ValueError("section records differ from manifest spine")
    by_id = {unit.id: unit for unit in units}
    first_units: dict[str, str] = {}
    for unit in units:
        first_units.setdefault(unit.section_id, unit.id)
    if set(first_units) != set(ids):
        raise ValueError("section records do not cover the unit spine exactly")
    for section in result:
        if section.start_unit_id != first_units[section.section_id]:
            raise ValueError(f"section start differs from unit spine: {section.section_id}")
        if section.parent_section_id is not None and section.parent_section_id not in ids:
            raise ValueError(f"unknown parent section: {section.section_id}")
        if section.parent_section_id == section.section_id:
            raise ValueError(f"self-parented section: {section.section_id}")
        if section.delivery_chapter:
            if section.title_unit_id is None or section.raw_title is None:
                raise ValueError(f"delivery section lacks a title unit: {section.section_id}")
            title = by_id.get(section.title_unit_id)
            if title is None or title.section_id != section.section_id or title.kind != "heading":
                raise ValueError(f"invalid delivery title unit: {section.section_id}")
            if (_comparable_title(section.raw_title) != _comparable_title(title.prepared_text)
                    and not section.issues):
                raise ValueError(f"substantive navigation/content title difference needs an issue: {section.section_id}")
    return result


def admit(bundle: Path, required_version: int | None = None) -> tuple[dict, list[Unit]]:
    manifest = json.loads((bundle / "manifest.json").read_text())
    version = manifest.get("prepared_text_version")
    if version not in (1, 2) or manifest.get("admission") != "ready":
        raise ValueError("prepared bundle is not an admitted supported version")
    if required_version is not None and version != required_version:
        if required_version == 2 and version == 1:
            raise ValueError("prepared version one lacks sections.jsonl; migrate to version two")
        raise ValueError(f"prepared version {required_version} required")
    hashes = manifest["hashes"]
    for name in ("prepared.md", "units.jsonl"):
        if sha256(bundle / name) != hashes[name]:
            raise ValueError(f"changed prepared file: {name}")
    originals = manifest["original_file_hashes"]
    if not originals:
        raise ValueError("missing retained witness")
    for name, digest in originals.items():
        path = bundle / name
        if not path.resolve().is_relative_to((bundle / "original").resolve()):
            raise ValueError("witness path must be inside original/")
        if sha256(path) != digest:
            raise ValueError(f"changed witness: {name}")
    units = [Unit.model_validate_json(line) for line in (bundle / "units.jsonl").read_text().splitlines()]
    if not units or [u.ordinal for u in units] != list(range(1, len(units) + 1)):
        raise ValueError("unit ordinals must be contiguous")
    if len({u.id for u in units}) != len(units):
        raise ValueError("duplicate source unit IDs")
    section_ids = list(dict.fromkeys(u.section_id for u in units))
    if section_ids != manifest["section_ids"]:
        raise ValueError("section spine differs from source inventory")
    closed = set()
    previous = None
    for u in units:
        if u.section_id != previous:
            if u.section_id in closed:
                raise ValueError("noncontiguous section")
            if previous is not None:
                closed.add(previous)
            previous = u.section_id
        end = 0
        for start, stop in u.note_call_spans:
            if not end <= start < stop <= len(u.prepared_text):
                raise ValueError(f"invalid note-call spans: {u.id}")
            end = stop
    doc = parse_document((bundle / "prepared.md").read_text())
    if len(doc.content) != len(units):
        raise ValueError("Markdown/index unit count differs")
    for block, unit in zip(doc.content, units, strict=True):
        attrs = {"kind": unit.kind, "role": unit.role, "section": unit.section_id}
        if (not isinstance(block, pf.Div) or block.identifier != unit.id
                or list(block.classes) != ["source"] or dict(block.attributes) != attrs):
            raise ValueError(f"Markdown/index identity differs: {unit.id}")
        body = list(block.content)
        expected = pf.Header if unit.kind == "heading" else pf.Para
        if len(body) != 1 or not isinstance(body[0], expected):
            raise ValueError(f"source kind differs: {unit.id}")
        if unit.kind == "heading":
            if unit.heading_level is not None and unit.heading_level != body[0].level:
                raise ValueError(f"heading hierarchy differs: {unit.id}")
            unit.heading_level = body[0].level
        elif unit.heading_level is not None:
            raise ValueError(f"heading level on a nonheading: {unit.id}")
        if project_text(body[0]) != unit.prepared_text:
            raise ValueError(f"Markdown/index text differs: {unit.id}")
    if version == 2:
        sections(bundle, manifest, units)
    return manifest, units


def partition(units: list[Unit], *, max_batch_pages: int = 10, max_batch_words: int = 6000) -> dict:
    if max_batch_pages < 1 or max_batch_words < 1:
        raise ValueError("positive batch limits required")
    pages = []
    for unit in units:
        words = len(unit.prepared_text.split())
        if (not pages or pages[-1]["section_id"] != unit.section_id
                or pages[-1]["words"] + words > 600):
            pages.append({"id": f"wp{len(pages)+1:06d}", "section_id": unit.section_id,
                          "unit_ids": [], "words": 0})
        pages[-1]["unit_ids"].append(unit.id)
        pages[-1]["words"] += words
    batches = []
    for page in pages:
        if (not batches or batches[-1]["section_id"] != page["section_id"]
                or len(batches[-1]["page_ids"]) >= max_batch_pages
                or batches[-1]["words"] + page["words"] > max_batch_words):
            batches.append({"id": f"b{len(batches)+1:06d}", "section_id": page["section_id"],
                            "page_ids": [], "unit_ids": [], "words": 0})
        batch = batches[-1]
        batch["page_ids"].append(page["id"])
        batch["unit_ids"].extend(page["unit_ids"])
        batch["words"] += page["words"]
    return {"plan_version": 2, "max_batch_pages": max_batch_pages,
            "max_batch_words": max_batch_words, "pages": pages, "batches": batches}
