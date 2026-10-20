from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from audiobooks.source_units import (
    SectionProjection,
    Unit,
    admit,
    partition,
    project_section_titles,
    sections,
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
    def test_navigation_only_title_projection_and_existing_heading_are_exact(self):
        units = [
            Unit(
                id="u000001",
                ordinal=1,
                section_id="old",
                kind="heading",
                role="body",
                source_locators=["book.xhtml#one"],
                source_text="One",
                prepared_text="One",
                print_pages=[],
                note_call_spans=[],
                preparation_changes=[],
                heading_level=1,
            ),
            Unit(
                id="u000002",
                ordinal=2,
                section_id="old",
                kind="paragraph",
                role="body",
                source_locators=["book.xhtml#one-p"],
                source_text="A.",
                prepared_text="A.",
                print_pages=[],
                note_call_spans=[],
                preparation_changes=[],
            ),
            Unit(
                id="u000003",
                ordinal=3,
                section_id="old",
                kind="paragraph",
                role="body",
                source_locators=["book.xhtml#two"],
                source_text="B.",
                prepared_text="B.",
                print_pages=[],
                note_call_spans=[],
                preparation_changes=[],
            ),
        ]
        shared_projection_fields = {
            "parent_section_id": None,
            "level": 1,
            "role": "body",
            "navigation_source": "epub3-nav",
            "target_href": "book.xhtml",
            "delivery_chapter": True,
            "issues": [],
        }
        decisions = [
            SectionProjection(
                section_id="one",
                raw_title="One",
                boundary_unit_id="u000001",
                content_title_unit_id="u000001",
                source_location="nav:one",
                target_fragment="one",
                **shared_projection_fields,
            ),
            SectionProjection(
                section_id="two",
                raw_title="Two",
                boundary_unit_id="u000003",
                content_title_unit_id=None,
                source_location="nav:two",
                target_fragment="two",
                **shared_projection_fields,
            ),
        ]
        projected, section_records = project_section_titles(units, decisions)
        self.assertEqual([unit.prepared_text for unit in projected], ["One", "A.", "Two", "B."])
        self.assertEqual(sum(unit.prepared_text == "One" for unit in projected), 1)
        self.assertEqual(projected[2].preparation_changes, ["navigation-label projection"])
        self.assertEqual(section_records[1].start_unit_id, projected[2].id)
        self.assertEqual(section_records[1].title_unit_id, projected[2].id)

    def test_plotinus_version_two_covers_units_and_binds_delivery_title(self):
        with TemporaryDirectory() as directory:
            bundle = migrated_plotinus(Path(directory))
            manifest, units = admit(bundle, required_version=2)
            section_records = sections(bundle, manifest, units)

        self.assertEqual(len(units), 69)
        self.assertEqual([record.section_id for record in section_records], manifest["section_ids"])
        delivery_sections = [record for record in section_records if record.delivery_chapter]
        self.assertEqual(
            [
                (record.section_id, record.start_unit_id, record.title_unit_id)
                for record in delivery_sections
            ],
            [("essay", "u000026", "u000026")],
        )
        plan = partition(units)
        essay_batches = [batch for batch in plan["batches"] if batch["section_id"] == "essay"]
        self.assertEqual(
            [(batch["words"], len(batch["page_ids"])) for batch in essay_batches], [(4708, 10)]
        )

    def test_section_start_must_match_first_unit_of_contiguous_membership(self):
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
            with self.assertRaisesRegex(ValueError, "section start differs"):
                admit(bundle, required_version=2)

    def test_new_adaptation_contract_rejects_unmigrated_version_one(self):
        with self.assertRaisesRegex(ValueError, "lacks sections.jsonl"):
            admit(FIXTURE / "prepared", required_version=2)


if __name__ == "__main__":
    unittest.main()
