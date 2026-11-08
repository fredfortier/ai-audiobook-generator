"""Exported script identities must survive until rendering freezes its inputs."""

from pathlib import Path

import pytest
from pydantic import TypeAdapter

from audiobooks.adaptation import (
    AcceptedBatch,
    Beat,
    Brief,
    Choice,
    Coverage,
    Disposition,
    Edit,
    Result,
    Review,
    WorkerPacket,
    accept,
    export,
    init,
    task,
    verify_exported_scripts,
)
from audiobooks.files import write_atomic
from audiobooks.source_units import AdaptationPlan, admit, identity, sha256
from tests.test_acting_score import acting_score_fixture
from tests.test_section_contract import migrated_plotinus


def test_render_input_rejects_speech_changed_after_export(tmp_path: Path) -> None:
    script = tmp_path / "script" / "0001.md"
    script.parent.mkdir()
    script.write_text("The admitted words.\n", encoding="utf-8")
    hashes = {"script/0001.md": sha256(script)}
    verify_exported_scripts(tmp_path, list(hashes), hashes)

    script.write_text("Different words.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exported script changed"):
        verify_exported_scripts(tmp_path, list(hashes), hashes)


def test_unbound_script_inventory_requires_reviewed_reexport(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="complete script hashes required"):
        verify_exported_scripts(tmp_path, ["script/0001.md"], {})


def test_export_preserves_narrated_span_ledger(tmp_path: Path) -> None:
    prepared = migrated_plotinus(tmp_path)
    manifest, units = admit(prepared)
    _, template, _ = acting_score_fixture()
    brief = Brief(
        prepared_source_hash=identity(manifest),
        survey_unit_ids=[unit.id for unit in units],
        narrator=template.narrator,
        voices=template.voices,
        defaults=template.defaults,
        performance_choices={
            "plain": Choice(
                trigger="Read the fixture prose.",
                avoid="Changing the fixture words.",
                parameters=template.defaults,
            )
        },
        section_baselines={section: "plain" for section in manifest.section_ids},
        rules=[],
        pronunciation_watchlist=[],
        section_dependencies={section: [] for section in manifest.section_ids},
        unresolved_questions=[],
    )
    brief_path = tmp_path / "brief.json"
    write_atomic(brief_path, brief.model_dump())
    workspace = tmp_path / "adaptation"
    init(prepared, brief_path, workspace)
    plan = AdaptationPlan.model_validate_json((workspace / "plan.json").read_text())
    indexed = {unit.id: unit for unit in units}
    for batch in plan.batches:
        task(workspace, batch.id)
        packet_path = next(
            path
            for path in (workspace / "tasks" / batch.id).glob("*.json")
            if path.name != "active.json"
        )
        packet = WorkerPacket.model_validate_json(packet_path.read_text())
        dispositions: list[Disposition] = []
        for uid in batch.unit_ids:
            unit = indexed[uid]
            if unit.role == "paratext":
                dispositions.append(Disposition(id=uid, disposition="excluded", reason="paratext"))
                continue
            text = unit.prepared_text
            for start, end in reversed(unit.note_call_spans):
                text = text[:start] + text[end:]
            text = "\n".join(" ".join(line.split()) for line in text.splitlines())
            dispositions.append(
                Disposition(
                    id=uid,
                    disposition="narrated",
                    normalized_text=text,
                    edits=(
                        [Edit(before=unit.prepared_text, after=text, reason="Remove note calls.")]
                        if text != unit.prepared_text
                        else []
                    ),
                    beats=[
                        Beat(
                            start=0,
                            end=len(text),
                            voice=brief.narrator,
                            choice="plain",
                            parameters=brief.defaults,
                        )
                    ],
                )
            )
        result = Result.model_validate(
            {
                **{
                    key: value
                    for key, value in packet.model_dump().items()
                    if key in Result.model_fields
                },
                "units": [item.model_dump() for item in dispositions],
                "continuity": "Complete fixture batch.",
                "issues": [],
            }
        )
        draft = Path(packet.draft_path)
        write_atomic(draft, result.model_dump())
        review_path = draft.with_name("review.json")
        write_atomic(
            review_path,
            Review(
                result_hash=identity(result.model_dump()),
                reviewed_unit_ids=batch.unit_ids,
                editorial_changes_checked=True,
                boundary_checked=True,
                fidelity_and_performance_checked=True,
                notes="Fixture words, note removals and source boundaries checked.",
            ).model_dump(),
        )
        accept(workspace, draft, review_path)
    export(workspace)
    ledger = TypeAdapter(list[Coverage]).validate_json((workspace / "coverage.json").read_text())
    narrated = [item for item in ledger if item.disposition == "narrated"]
    assert narrated
    assert all((item.speech_spans for item in narrated))
    accepted = [
        AcceptedBatch.model_validate_json(path.read_text())
        for path in (workspace / "work").glob("*.json")
    ]
    assert sum((len(item.speech_spans) for item in narrated)) == sum(
        (len(unit.beats) for batch in accepted for unit in batch.result.units)
    )
