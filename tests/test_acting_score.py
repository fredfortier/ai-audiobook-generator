from __future__ import annotations

import unittest

from pydantic import ValidationError

from audiobooks.adaptation import (
    ACTION_PARAMETERS,
    Action,
    Beat,
    Brief,
    DirectionContext,
    DirectorMove,
    Disposition,
    Edit,
    ProductionCue,
    check_disposition,
    check_score_moves,
    retained_note_call,
)
from audiobooks.rendering import Calibration, CalibrationEvidence, validate_calibration_provenance
from audiobooks.script_contract import Parameters
from audiobooks.source_units import Unit

DEFAULT_PARAMETERS = Parameters(
    exaggeration=0.5, cfg_weight=0.5, temperature=0.8, repetition_penalty=1.2, min_p=0.05, top_p=1.0
)


def acting_score_fixture() -> tuple[Unit, Brief, list[DirectorMove]]:
    unit = Unit(
        id="u000001",
        ordinal=1,
        section_id="essay",
        kind="paragraph",
        role="body",
        source_locators=["fixture#p1"],
        source_text="Alpha beta gamma",
        prepared_text="Alpha beta gamma",
        print_pages=[],
        note_call_spans=[],
        preparation_changes=[],
    )
    cue = ProductionCue(
        id="engaged",
        intent="Address the reasoning actively.",
        scope="The essay.",
        avoid="Uniform force.",
        priority=1,
        unit_ids=[unit.id],
    )
    brief = Brief(
        brief_version=2,
        prepared_source_hash="prepared",
        survey_unit_ids=[unit.id],
        narrator="narrator",
        voices={"narrator": "assets/voices/enoch.wav"},
        defaults=DEFAULT_PARAMETERS,
        performance_choices={},
        section_baselines={"essay": None},
        rules=[],
        pronunciation_watchlist=[],
        section_dependencies={"essay": []},
        unresolved_questions=[],
        direction=DirectionContext(
            addressee="One listener.",
            throughline="Test and resolve.",
            stakes="Clear judgment.",
            macro_trajectory=["test", "resolve"],
            performance_limits=["Preserve the words."],
            user_cues=[cue],
        ),
    )
    spans: list[tuple[int, int, str, Action]] = [
        (0, 6, "Alpha", "CLARIFY"),
        (6, 10, "beta", "PROBE"),
        (10, 16, "gamma", "RESOLVE"),
    ]
    moves = [
        DirectorMove(
            id=f"m{position:06d}",
            unit_id=unit.id,
            start=start,
            end=end,
            action=action,
            objective=(f"{action} the listener to follow move {position} " f"by using {evidence}."),
            textual_evidence=evidence,
        )
        for position, (start, end, evidence, action) in enumerate(spans, 1)
    ]
    return unit, brief, moves


class ActingScoreTest(unittest.TestCase):
    def test_removed_letter_calls_do_not_reject_authored_letters(self) -> None:
        for source, call, normalized in [
            ("Trutha is a good beginning.", "a", "Truth is a good beginning."),
            ("Bodyb is beloved.", "b", "Body is beloved."),
            ("Alphaa beta gamma", "a", "Alpha beta gamma"),
        ]:
            with self.subTest(source=source):
                unit, brief, _ = acting_score_fixture()
                start = source.index(call, 5 if source.startswith("Alpha") else 4)
                unit = unit.model_copy(
                    update={
                        "source_text": source,
                        "prepared_text": source,
                        "note_call_spans": [(start, start + 1)],
                    }
                )
                move = DirectorMove(
                    id="m000001",
                    unit_id=unit.id,
                    start=0,
                    end=len(source),
                    action="CLARIFY",
                    textual_evidence=source,
                    objective="CLARIFY the listener to follow the claim by stating it.",
                )
                disposition = Disposition(
                    id=unit.id,
                    disposition="narrated",
                    normalized_text=normalized,
                    edits=[Edit(before=call, after="", reason="Remove the indexed citation call.")],
                    beats=[
                        Beat(
                            start=0,
                            end=len(normalized),
                            voice="narrator",
                            action="CLARIFY",
                            parameters=ACTION_PARAMETERS["CLARIFY"],
                            score_move_ids=[move.id],
                        )
                    ],
                )
                check_disposition(disposition, unit, brief, [move])

    def test_retained_letter_call_is_rejected_at_its_source_position(self) -> None:
        source = "Trutha is a good beginning."
        unit, brief, _ = acting_score_fixture()
        unit = unit.model_copy(
            update={"source_text": source, "prepared_text": source, "note_call_spans": [(5, 6)]}
        )
        move = DirectorMove(
            id="m000001",
            unit_id=unit.id,
            start=0,
            end=len(source),
            action="CLARIFY",
            textual_evidence=source,
            objective="CLARIFY the listener to follow the claim by stating it.",
        )
        for normalized in [source, source[:-1] + "!"]:
            with self.subTest(normalized=normalized):
                disposition = Disposition(
                    id=unit.id,
                    disposition="narrated",
                    normalized_text=normalized,
                    edits=[Edit(before=".", after="!", reason="Change terminal punctuation.")],
                    beats=[
                        Beat(
                            start=0,
                            end=len(normalized),
                            voice="narrator",
                            action="CLARIFY",
                            parameters=ACTION_PARAMETERS["CLARIFY"],
                            score_move_ids=[move.id],
                        )
                    ],
                )
                with self.assertRaisesRegex(ValueError, "retained citation call"):
                    check_disposition(disposition, unit, brief, [move])

    def test_removed_numeric_call_does_not_match_brackets_or_spacing(self) -> None:
        for source, normalized in [
            ("She [lost her] [128] virginity.", "She lost her virginity."),
            (
                "My heart turned away. [137] I want to return.",
                "My heart turned away. I want to return.",
            ),
            ("[and if] [136] you return", "and if you return"),
        ]:
            with self.subTest(source=source):
                unit, _, _ = acting_score_fixture()
                start = source.index("[1")
                end = source.index("]", start) + 2
                unit = unit.model_copy(
                    update={
                        "source_text": source,
                        "prepared_text": source,
                        "note_call_spans": [(start, end)],
                    }
                )
                self.assertFalse(retained_note_call(unit, normalized))
                self.assertTrue(retained_note_call(unit, source))

    def test_removed_reference_punctuation_is_not_a_retained_call(self) -> None:
        source = "St Paul speaks (cf. John 1:5)."
        unit, _, _ = acting_score_fixture()
        unit = unit.model_copy(
            update={"source_text": source, "prepared_text": source, "note_call_spans": [(14, 28)]}
        )
        self.assertFalse(retained_note_call(unit, "Saint Paul speaks."))
        self.assertTrue(retained_note_call(unit, "Saint Paul speaks (cf. John 1:5)."))

    def test_score_rejects_source_gaps_and_evidence_outside_move(self) -> None:
        unit, brief, moves = acting_score_fixture()

        with self.assertRaisesRegex(ValueError, "partition"):
            check_score_moves(
                [moves[0].model_copy(update={"start": 1, "textual_evidence": "lpha"}), *moves[1:]],
                [unit],
                brief,
            )
        with self.assertRaisesRegex(ValueError, "outside its move"):
            check_score_moves(
                [moves[0].model_copy(update={"textual_evidence": "gamma"}), *moves[1:]],
                [unit],
                brief,
            )

    def test_move_rejects_objective_without_listener_action(self) -> None:
        _, _, moves = acting_score_fixture()
        move_fields = moves[0].model_dump()
        with self.assertRaisesRegex(ValidationError, "listener objective"):
            DirectorMove(**{**move_fields, "objective": "Be mystical."})

    def test_directed_beats_derive_vectors_from_actions_and_preserve_lineage(self) -> None:
        unit, brief, moves = acting_score_fixture()
        disposition = Disposition(
            id=unit.id,
            disposition="narrated",
            normalized_text=unit.prepared_text,
            beats=[
                Beat(
                    start=0,
                    end=6,
                    voice="narrator",
                    action="CLARIFY",
                    parameters=ACTION_PARAMETERS["CLARIFY"],
                    score_move_ids=["m000001"],
                ),
                Beat(
                    start=6,
                    end=10,
                    voice="narrator",
                    action="PROBE",
                    parameters=ACTION_PARAMETERS["PROBE"],
                    score_move_ids=["m000002"],
                ),
                Beat(
                    start=10,
                    end=16,
                    voice="narrator",
                    action="RESOLVE",
                    parameters=ACTION_PARAMETERS["RESOLVE"],
                    score_move_ids=["m000003"],
                ),
            ],
        )
        check_disposition(disposition, unit, brief, moves)

        wrong_vector = disposition.model_copy(
            update={
                "beats": [
                    disposition.beats[0].model_copy(
                        update={"parameters": ACTION_PARAMETERS["PROBE"]}
                    ),
                    *disposition.beats[1:],
                ]
            }
        )
        with self.assertRaisesRegex(ValueError, "registered action vector"):
            check_disposition(wrong_vector, unit, brief, moves)

        omitted = disposition.model_copy(
            update={
                "beats": [
                    disposition.beats[0],
                    disposition.beats[1].model_copy(
                        update={
                            "action": "RESOLVE",
                            "parameters": ACTION_PARAMETERS["RESOLVE"],
                            "score_move_ids": ["m000003"],
                        }
                    ),
                    disposition.beats[2],
                ]
            }
        )
        with self.assertRaisesRegex(ValueError, "omit or reorder"):
            check_disposition(omitted, unit, brief, moves)

    def test_directed_calibration_binds_action_moves_and_both_vectors(self) -> None:
        proposed = ACTION_PARAMETERS["CLARIFY"]
        realized = proposed.model_copy(update={"exaggeration": 0.6, "cfg_weight": 0.4})
        evidence = CalibrationEvidence(
            action="CLARIFY",
            score_move_ids=["m000001"],
            proposed=proposed,
            realized=realized,
            audition_evidence="Matched text retained clarity.",
        )
        calibration = Calibration(
            source_script_hashes={}, candidate_script_hashes={}, reasons={"s000001": evidence}
        )
        directions = {"s000001": {"action": "CLARIFY", "score_move_ids": ["m000001"]}}
        validate_calibration_provenance(
            calibration, {"s000001"}, directions, {"s000001": proposed}, {"s000001": realized}, True
        )

        changed_lineage = calibration.model_copy(
            update={
                "reasons": {"s000001": evidence.model_copy(update={"score_move_ids": ["m000002"]})}
            }
        )
        with self.assertRaisesRegex(ValueError, "provenance differs"):
            validate_calibration_provenance(
                changed_lineage,
                {"s000001"},
                directions,
                {"s000001": proposed},
                {"s000001": realized},
                True,
            )
