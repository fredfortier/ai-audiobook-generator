import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from audiobooks.source_units import (
    SectionProjection,
    Unit,
    admit,
    project_section_titles,
    sha256,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "plotinus"


def migrated_plotinus(directory: Path) -> Path:
    source = FIXTURE / "prepared"
    output = directory / "prepared"
    shutil.copytree(source, output)
    decisions = json.loads((FIXTURE / "section-decisions.json").read_text())
    section_path = output / "sections.jsonl"
    section_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in decisions)
    )
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["prepared_text_version"] = 2
    manifest["hashes"]["sections.jsonl"] = sha256(section_path)
    manifest_path.write_text(json.dumps(manifest))
    return output


class SectionContractTest(unittest.TestCase):
    def test_navigation_only_title_projection_and_existing_heading_are_exact(self) -> None:
        units = [
            Unit(
                id=f"u{ordinal:06d}",
                ordinal=ordinal,
                section_id="old",
                kind="heading" if ordinal == 1 else "paragraph",
                role="body",
                source_locators=[f"book.xhtml#{fragment}"],
                source_text=text,
                prepared_text=text,
                print_pages=[],
                note_call_spans=[],
                preparation_changes=[],
                heading_level=1 if ordinal == 1 else None,
            )
            for ordinal, (fragment, text) in enumerate(
                [("one", "One"), ("one-p", "A."), ("two", "B.")], 1
            )
        ]
        decisions = [
            SectionProjection(
                section_id=section,
                raw_title=title,
                boundary_unit_id=start,
                content_title_unit_id=title_id,
                source_location=f"nav:{section}",
                target_fragment=section,
                parent_section_id=None,
                level=1,
                role="body",
                navigation_source="epub3-nav",
                target_href="book.xhtml",
                delivery_chapter=True,
                issues=[],
            )
            for section, title, start, title_id in [
                ("one", "One", "u000001", "u000001"),
                ("two", "Two", "u000003", None),
            ]
        ]
        projected, section_records = project_section_titles(units, decisions)
        assert [unit.prepared_text for unit in projected] == ["One", "A.", "Two", "B."]
        assert sum((unit.prepared_text == "One" for unit in projected)) == 1
        assert projected[2].preparation_changes == ["navigation-label projection"]
        assert section_records[1].start_unit_id == projected[2].id
        assert section_records[1].title_unit_id == projected[2].id

    def test_admission_rejects_unrecorded_prepared_file_change(self) -> None:
        with TemporaryDirectory() as directory:
            bundle = migrated_plotinus(Path(directory))
            path = bundle / "prepared.md"
            path.write_text(path.read_text() + "\n")
            with pytest.raises(ValueError, match="changed prepared file: prepared.md"):
                admit(bundle, required_version=2)

    def test_section_start_must_match_first_unit_of_contiguous_membership(self) -> None:
        with TemporaryDirectory() as directory:
            bundle = migrated_plotinus(Path(directory))
            path = bundle / "sections.jsonl"
            records = [json.loads(line) for line in path.read_text().splitlines()]
            records[3]["start_unit_id"] = "u000027"
            path.write_text("".join(json.dumps(item) + "\n" for item in records))
            manifest_path = bundle / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["hashes"]["sections.jsonl"] = sha256(path)
            manifest_path.write_text(json.dumps(manifest))
            with pytest.raises(ValueError, match="section start differs"):
                admit(bundle, required_version=2)

    def test_new_adaptation_contract_rejects_unmigrated_version_one(self) -> None:
        with pytest.raises(ValueError, match="lacks sections.jsonl"):
            admit(FIXTURE / "prepared", required_version=2)
