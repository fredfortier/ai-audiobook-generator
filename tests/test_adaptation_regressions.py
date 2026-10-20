"""Regression checks at score ordering, fragment validation, and revision boundaries."""

import json
from pathlib import Path

from audiobooks.adaptation import (
    ACTION_PARAMETERS,
    Beat,
    Brief,
    Disposition,
    FragmentResult,
    Result,
    Review,
    check_score_moves,
    checked_fragment,
    fragment_paths,
    init,
    revise,
)
from audiobooks.files import write_atomic
from audiobooks.source_units import identity
from tests.test_acting_score import acting_score_fixture
from tests.test_section_contract import migrated_plotinus


def test_score_rejects_interleaved_units() -> None:
    import pytest

    unit, brief, moves = acting_score_fixture()
    second = unit.model_copy(update={"id": "u000002"})
    other_moves = [
        move.model_copy(update={"id": "second-" + move.id, "unit_id": second.id}) for move in moves
    ]
    with pytest.raises(ValueError, match="exactly in order"):
        check_score_moves([moves[0], *other_moves, *moves[1:]], [unit, second], brief)


def test_directed_fragment_preserves_accepted_move_lineage(tmp_path: Path) -> None:
    unit, brief, moves = acting_score_fixture()
    packet = {
        "batch_id": "b000001",
        "attempt_id": "attempt",
        "prepared_hash": "prepared",
        "plan_hash": "plan",
        "configuration_hash": "configuration",
        "brief_hash": "brief",
        "acting_score_hash": "score",
        "predecessor_hash": "section-start",
        "fragment_plan_hash": "fragment-plan",
        "fragments": [{"id": "f000001", "start": 0, "end": 10}],
        "owned_units": [unit.model_dump()],
        "acting_score_moves": [move.model_dump() for move in moves],
    }
    path, draft = fragment_paths(tmp_path, packet, "f000001")
    write_atomic(path, {**packet, "fragment_predecessor_hash": "fragment-start"})
    result = Result.model_validate(
        {
            **{key: packet[key] for key in Result.model_fields if key in packet},
            "units": [
                Disposition(
                    id=unit.id,
                    disposition="narrated",
                    normalized_text="Alpha beta",
                    beats=[
                        Beat(
                            start=0,
                            end=6,
                            voice="narrator",
                            action="CLARIFY",
                            parameters=ACTION_PARAMETERS["CLARIFY"],
                            score_move_ids=[moves[0].id],
                        ),
                        Beat(
                            start=6,
                            end=10,
                            voice="narrator",
                            action="PROBE",
                            parameters=ACTION_PARAMETERS["PROBE"],
                            score_move_ids=[moves[1].id],
                        ),
                    ],
                ).model_dump()
            ],
            "continuity": "Continue the accepted score.",
            "issues": [],
        }
    )
    fragment = FragmentResult(
        result=result,
        fragment_id="f000001",
        fragment_plan_hash="fragment-plan",
        fragment_predecessor_hash="fragment-start",
        source_start=0,
        source_end=10,
    )
    write_atomic(draft, fragment.model_dump())
    assert checked_fragment(tmp_path, packet, brief, 0, "fragment-start") == fragment


def test_directed_revision_does_not_freeze_old_score_moves(tmp_path: Path) -> None:
    prepared = migrated_plotinus(tmp_path)
    manifest = json.loads((prepared / "manifest.json").read_text())
    _, template, _ = acting_score_fixture()
    assert template.direction is not None
    brief = Brief.model_validate(
        {
            **template.model_dump(),
            "prepared_source_hash": identity(manifest),
            "survey_unit_ids": ["u000027"],
            "section_baselines": {section: None for section in manifest["section_ids"]},
            "section_dependencies": {section: [] for section in manifest["section_ids"]},
            "direction": {
                **template.direction.model_dump(),
                "user_cues": [],
            },
        }
    )
    brief_path = tmp_path / "brief.json"
    write_atomic(brief_path, brief.model_dump())
    original = tmp_path / "old-adaptation"
    init(prepared, brief_path, original)
    saved = json.loads((original / "manifest.json").read_text())
    plan = json.loads((original / "plan.json").read_text())
    batch = plan["batches"][0]
    result = Result.model_validate(
        {
            **{key: saved[key] for key in Result.model_fields if key in saved},
            "batch_id": batch["id"],
            "attempt_id": "prior",
            "predecessor_hash": "section-start",
            "units": [
                Disposition(
                    id=unit_id, disposition="excluded", reason="Source paratext."
                ).model_dump()
                for unit_id in batch["unit_ids"]
            ],
            "continuity": "Section complete.",
            "issues": [],
        }
    )
    digest = identity(result.model_dump())
    review = Review(
        result_hash=digest,
        reviewed_unit_ids=batch["unit_ids"],
        editorial_changes_checked=True,
        boundary_checked=True,
        fidelity_and_performance_checked=True,
        notes="Reviewed against the source.",
    )
    write_atomic(
        original / "work" / (batch["id"] + ".json"),
        {"result": result.model_dump(), "result_hash": digest, "review": review.model_dump()},
    )
    revised = tmp_path / "new-adaptation"
    revise(original, prepared, brief_path, revised)
    assert json.loads((revised / "reuse.json").read_text())["units"] == {}
