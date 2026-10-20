"""Regression checks at score ordering, fragment validation, and revision boundaries."""

import json
from pathlib import Path

import pytest

from audiobooks.adaptation import (
    ACTION_PARAMETERS,
    Beat,
    Brief,
    DirectorMove,
    Disposition,
    Edit,
    FragmentResult,
    Result,
    Review,
    Rule,
    ScoreDraft,
    ScoreReview,
    WorkerPacket,
    accept,
    accept_score,
    check_score_moves,
    checked_fragment,
    direction_task,
    fragment_paths,
    init,
    revise,
    task,
)
from audiobooks.files import write_atomic
from audiobooks.source_units import admit, identity
from tests.test_acting_score import acting_score_fixture
from tests.test_section_contract import migrated_plotinus


def test_score_rejects_interleaved_units() -> None:
    unit, brief, moves = acting_score_fixture()
    second = unit.model_copy(update={"id": "u000002"})
    other_moves = [
        move.model_copy(update={"id": "second-" + move.id, "unit_id": second.id}) for move in moves
    ]
    with pytest.raises(ValueError, match="exactly in order"):
        check_score_moves([moves[0], *other_moves, *moves[1:]], [unit, second], brief)


def test_directed_fragment_preserves_accepted_move_lineage(tmp_path: Path) -> None:
    unit, brief, moves = acting_score_fixture()
    packet = WorkerPacket.model_validate(
        {
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
    )
    path, draft = fragment_paths(tmp_path, packet, "f000001")
    write_atomic(
        path,
        {**packet.model_dump(exclude_unset=True), "fragment_predecessor_hash": "fragment-start"},
    )
    result = Result.model_validate(
        {
            **{
                key: packet.model_dump()[key]
                for key in Result.model_fields
                if key in packet.model_dump()
            },
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
    corrupted = fragment.model_dump()
    corrupted["result"]["units"][0]["beats"][0]["score_move_ids"] = [moves[1].id]
    write_atomic(draft, corrupted)
    with pytest.raises(ValueError, match="action differs"):
        checked_fragment(tmp_path, packet, brief, 0, "fragment-start")


def test_directed_revision_does_not_freeze_old_score_moves(tmp_path: Path) -> None:
    prepared = migrated_plotinus(tmp_path)
    manifest, units = admit(prepared)
    _, template, _ = acting_score_fixture()
    assert template.direction is not None
    narrated = [unit for unit in units if unit.role == "body"]
    brief = Brief.model_validate(
        {
            **template.model_dump(),
            "prepared_source_hash": identity(manifest),
            "survey_unit_ids": [unit.id for unit in narrated],
            "section_baselines": {section: None for section in manifest.section_ids},
            "section_dependencies": {section: [] for section in manifest.section_ids},
            "rules": [
                Rule(
                    id="literal-digits",
                    unit_ids=[unit.id for unit in narrated],
                    evidence="The fixture retains source digits while testing score-lineage reuse.",
                    instruction="Retain source digits for this revision-boundary test.",
                    allow_digits=True,
                ).model_dump()
            ],
            "direction": {**template.direction.model_dump(), "user_cues": []},
        }
    )
    brief_path = tmp_path / "brief.json"
    write_atomic(brief_path, brief.model_dump())
    original = tmp_path / "old-adaptation"
    init(prepared, brief_path, original)
    direction_task(original, section_ids=None)
    score_packet_path = next(
        path
        for path in (original / "direction" / "tasks").glob("d*.json")
        if not path.name.endswith(".active.json")
    )
    score_packet = json.loads(score_packet_path.read_text())
    moves = [
        DirectorMove(
            id="old-" + unit.id,
            unit_id=unit.id,
            start=0,
            end=len(unit.prepared_text),
            action="CLARIFY",
            objective="CLARIFY the listener to follow the claim by stating it.",
            textual_evidence=unit.prepared_text,
        )
        for unit in narrated
    ]
    score = ScoreDraft.model_validate(
        {
            **{key: score_packet[key] for key in ScoreDraft.model_fields if key in score_packet},
            "moves": [move.model_dump() for move in moves],
        }
    )
    score_draft = Path(score_packet["draft_path"])
    write_atomic(score_draft, score.model_dump())
    score_review = tmp_path / "score-review.json"
    write_atomic(
        score_review,
        ScoreReview(
            score_hash=identity(score.model_dump()),
            reviewed_move_ids=[move.id for move in moves],
            source_coverage_checked=True,
            direction_context_checked=True,
            action_and_objective_checked=True,
            continuity_checked=True,
            notes="Reviewed complete fixture score for this revision-boundary test.",
        ).model_dump(),
    )
    accept_score(original, score_draft, score_review)
    plan = json.loads((original / "plan.json").read_text())
    batch = next(
        batch for batch in plan["batches"] if batch["section_id"] == narrated[0].section_id
    )
    task(original, batch["id"], fragment_boundaries=None, owned_word_budget=6000)
    active = json.loads((original / "tasks" / batch["id"] / "active.json").read_text())
    packet = WorkerPacket.model_validate_json(Path(active["packet_path"]).read_text())
    owned = [unit for unit in narrated if unit.id in batch["unit_ids"]]
    dispositions: list[Disposition] = []
    for unit in owned:
        text = unit.prepared_text
        for start, end in reversed(unit.note_call_spans):
            text = text[:start] + text[end:]
        text = "\n".join(" ".join(line.split()) for line in text.split("\n"))
        dispositions.append(
            Disposition(
                id=unit.id,
                disposition="narrated",
                normalized_text=text,
                edits=(
                    [
                        Edit(
                            before=unit.prepared_text,
                            after=text,
                            reason="Remove indexed reference calls.",
                        )
                    ]
                    if text != unit.prepared_text
                    else []
                ),
                applied_rule_ids=["literal-digits"],
                beats=[
                    Beat(
                        start=0,
                        end=len(text),
                        voice=brief.narrator,
                        action="CLARIFY",
                        parameters=ACTION_PARAMETERS["CLARIFY"],
                        score_move_ids=["old-" + unit.id],
                    )
                ],
            )
        )
    result = Result.model_validate(
        {
            **{
                key: packet.model_dump()[key]
                for key in Result.model_fields
                if key in packet.model_dump()
            },
            "units": [item.model_dump() for item in dispositions],
            "continuity": "The reviewed section is complete.",
            "issues": [],
        }
    )
    draft = Path(packet.draft_path)
    write_atomic(draft, result.model_dump())
    review = tmp_path / "review.json"
    write_atomic(
        review,
        Review(
            result_hash=identity(result.model_dump()),
            reviewed_unit_ids=[unit.id for unit in owned],
            editorial_changes_checked=True,
            boundary_checked=True,
            fidelity_and_performance_checked=True,
            notes="Reviewed narrated words, edits, and actual old score-move lineage.",
        ).model_dump(),
    )
    accept(original, draft, review)
    revised = tmp_path / "new-adaptation"
    revise(original, prepared, brief_path, revised)
    assert json.loads((revised / "reuse.json").read_text())["units"] == {}
