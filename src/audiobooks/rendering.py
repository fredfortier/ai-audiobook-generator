"""Frozen original-Chatterbox plans and recoverable public-API generation."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import random
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

import typer
from pydantic import Field, TypeAdapter

from audiobooks.adaptation import (
    ActingScore,
    Action,
    AdaptationManifest,
    AdaptedSection,
    Coverage,
    DirectionLineage,
    SpeechSpan,
    verify_exported_scripts,
)

# Keep the local name in the verified-revision AST fingerprint while ownership
# lives in the shared persistence module.
from audiobooks.files import read_json
from audiobooks.files import write_atomic as atomic
from audiobooks.script_contract import Parameters, Record, read_script
from audiobooks.segmentation import generation_spans
from audiobooks.source_units import identity, sha256
from audiobooks.workspaces import REPOSITORY_ROOT, work_path

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
MODEL_FILES = (
    "ve.safetensors",
    "t3_cfg.safetensors",
    "s3gen.safetensors",
    "tokenizer.json",
    "conds.pt",
)
ROOT = REPOSITORY_ROOT


class ClauseCut(Record):
    speech_id: str
    paragraph: int = Field(ge=0)
    offset: int = Field(gt=0)
    reason: str = Field(min_length=1)


class CalibrationEvidence(Record):
    action: Action
    score_move_ids: list[str] = Field(min_length=1)
    proposed: Parameters
    realized: Parameters
    audition_evidence: str = Field(min_length=1)


class Calibration(Record):
    source_script_hashes: dict[str, str]
    candidate_script_hashes: dict[str, str]
    reasons: dict[str, str | CalibrationEvidence]


class RecordedChoiceEvidence(Record):
    """Historical choice provenance retained verbatim in frozen render-plan hashes."""

    choice: str
    score_move_ids: list[str]
    proposed: Parameters
    realized: Parameters
    audition_evidence: str


class RecordedCalibration(Record):
    """Read existing plans without accepting historical choices as new directed auditions."""

    source_script_hashes: dict[str, str]
    candidate_script_hashes: dict[str, str]
    reasons: dict[str, str | CalibrationEvidence | RecordedChoiceEvidence]


class SeedOverride(Record):
    segment_id: str
    seed: int = Field(ge=0, lt=2**32)
    reason: str = Field(min_length=1)


class AudioProperties(Record):
    sample_rate: int
    channels: int
    frames: int
    duration_seconds: float
    peak: float
    rms: float
    dc_offset: float


class RenderSegment(Record):
    id: str
    script: str
    section_id: str | None = None
    speech_id: str
    paragraph: int
    start: int
    end: int
    text: str
    native_text: str
    native_tokens: int
    voice: str
    parameters: Parameters
    seed: int
    heading_level: int | None
    score_move_ids: list[str] = Field(default_factory=list)
    directing_action: Action | None = None
    directing_choice: str | None = None
    proposed_parameters: Parameters | None = None


class ChapterSource(Record):
    section_id: str
    title: str


class DeliverySection(ChapterSource):
    title_speech_id: str
    start_segment_id: str


class RenderPlan(Record):
    render_version: Literal[1, 2]
    title: str
    author: str | None = None
    model_path: str
    device: Literal["cpu", "cuda", "mps"]
    token_limit: int | None = None
    voices: dict[str, str]
    runtime_hashes: dict[str, str]
    input_hashes: dict[str, str]
    clause_cuts: list[ClauseCut] = Field(default_factory=list)
    segments: list[RenderSegment]
    delivery_sections: list[DeliverySection]
    acting_score_hash: str | None = None
    seed_overrides: list[SeedOverride] = Field(default_factory=list)
    calibration: RecordedCalibration | None = None


class RenderManifest(Record):
    plan_hash: str
    audio_quality_verified: bool = False
    verified_revision_import_hash: str | None = None


class AudioRecord(Record):
    generation_hash: str
    audio_hash: str
    properties: AudioProperties


@app.command()
def schema(kind: str) -> None:
    """Print strict native schemas for clause-cut lists or calibration records."""
    models = {
        "clause-cuts": TypeAdapter(list[ClauseCut]),
        "calibration": TypeAdapter(Calibration),
        "seed-overrides": TypeAdapter(list[SeedOverride]),
    }
    if kind not in models:
        raise ValueError("unknown rendering schema")
    typer.echo(json.dumps(models[kind].json_schema(), indent=2))


def validate_calibration_provenance(
    calibration: Calibration | None,
    changed: set[str],
    directing_by_speech: Mapping[str, DirectionLineage],
    proposed_parameters: dict[str, Parameters],
    realized_parameters: dict[str, Parameters],
    directed: bool,
) -> None:
    if calibration is None:
        return
    if set(calibration.reasons) != changed:
        raise ValueError("every changed speech vector requires an exact scoped calibration reason")
    for speech_id, reason in calibration.reasons.items():
        if directed:
            if not isinstance(reason, CalibrationEvidence):
                raise ValueError("directed calibration requires structured score provenance")
            direction = directing_by_speech[speech_id]
            if (
                reason.action != direction.action
                or reason.score_move_ids != direction.score_move_ids
                or reason.proposed != proposed_parameters[speech_id]
                or reason.realized != realized_parameters[speech_id]
            ):
                raise ValueError(
                    "calibration provenance differs from score or scripts: " + speech_id
                )
        elif not isinstance(reason, str) or not reason.strip():
            raise ValueError("legacy calibration reason must be nonblank")


def runtime_hashes() -> dict[str, str]:
    paths = [
        ROOT / "uv.lock",
        *(
            Path(__file__).parent / name
            for name in ("rendering.py", "segmentation.py", "sentences.py", "script_contract.py")
        ),
    ]
    return {str(p.relative_to(ROOT)): sha256(p) for p in paths}


def load_plan(workspace: Path) -> RenderPlan:
    plan = RenderPlan.model_validate_json((workspace / "plan.json").read_text())
    manifest = RenderManifest.model_validate_json((workspace / "manifest.json").read_text())
    if identity(plan) != manifest.plan_hash:
        raise ValueError("frozen generation plan changed")
    if plan.runtime_hashes != runtime_hashes():
        raise ValueError("render runtime changed; freeze a new plan")
    for path, digest in plan.input_hashes.items():
        if sha256(Path(path)) != digest:
            raise ValueError(f"render input changed: {path}")
    if manifest.verified_revision_import_hash is not None:
        import_path = workspace / "verified-revision-import.json"
        if identity(read_json(import_path)) != manifest.verified_revision_import_hash:
            raise ValueError("verified revision import record changed")
    return plan


@app.command()
def plan(
    adaptation: Path,
    model_path: Path,
    workspace: Path,
    clause_cuts: Path,
    token_limit: int = 220,
    seed: int = 0,
    device: Literal["cuda", "cpu", "mps"] = "cuda",
    calibrated_script_dir: Path | None = None,
    calibration_record: Path | None = None,
    seed_overrides: Path | None = None,
    reuse_from: Path | None = None,
) -> None:
    """Freeze complete script order, native counts, model and reviewed clause cuts."""
    from chatterbox.models.t3.modules.t3_config import T3Config
    from chatterbox.models.tokenizers import EnTokenizer
    from chatterbox.tts import punc_norm

    workspace = work_path(workspace)
    if workspace.exists():
        raise ValueError("use a new render workspace")
    if not 0 < token_limit <= T3Config().max_text_tokens:
        raise ValueError("explicit supported device and budget within original T3 context required")
    adaptation = adaptation.resolve()
    model_path = model_path.resolve()
    manifest_path = adaptation / "manifest.json"
    manifest = AdaptationManifest.model_validate_json(manifest_path.read_text())
    coverage_path = adaptation / "coverage.json"
    coverage = TypeAdapter(list[Coverage]).validate_json(coverage_path.read_text())
    if not manifest.complete or identity(coverage) != manifest.coverage_hash:
        raise ValueError("complete verified adaptation coverage required")
    verify_exported_scripts(adaptation, manifest.script_files, manifest.script_hashes)
    directing_by_speech: dict[str, SpeechSpan] = {}
    for item in coverage:
        for span in item.speech_spans:
            if span.speech_id in directing_by_speech:
                raise ValueError("speech has duplicate adaptation coverage")
            directing_by_speech[span.speech_id] = span
    acting_score_path = None
    if manifest.acting_score_hash:
        acting_score_path = adaptation / manifest.acting_score_file
        if (
            not acting_score_path.is_file()
            or identity(ActingScore.model_validate_json(acting_score_path.read_text()))
            != manifest.acting_score_hash
        ):
            raise ValueError("exact accepted acting score required")
        for speech_id, span in directing_by_speech.items():
            if not span.score_move_ids or not span.action or not span.proposed_parameters:
                raise ValueError(
                    "directed speech lacks score and proposed-vector lineage: " + speech_id
                )
    section_path = adaptation / manifest.section_file
    if not manifest.section_file or not section_path.is_file():
        raise ValueError("explicit adapted section contract required")
    adapted_sections = TypeAdapter(list[AdaptedSection]).validate_json(section_path.read_text())
    if identity(adapted_sections) != manifest.sections_hash:
        raise ValueError("adapted section contract changed")
    script_to_section = {
        section.script_file: section.section_id
        for section in adapted_sections
        if section.script_file is not None
    }
    if len(script_to_section) != sum(
        section.script_file is not None for section in adapted_sections
    ):
        raise ValueError("a script file cannot represent multiple sections")
    if set(script_to_section) != set(manifest.script_files):
        raise ValueError("every script must bind to exactly one explicit section")
    cuts = TypeAdapter(list[ClauseCut]).validate_json(clause_cuts.read_text())
    if (calibrated_script_dir is None) != (calibration_record is None):
        raise ValueError("calibrated scripts require their source-hash and reason record")
    calibration = (
        None
        if calibration_record is None
        else Calibration.model_validate_json(calibration_record.read_text())
    )
    if calibration is not None and (
        set(calibration.source_script_hashes) != set(manifest.script_files)
        or set(calibration.candidate_script_hashes) != set(manifest.script_files)
    ):
        raise ValueError("calibration hash inventories must match the exact script inventory")
    if len({(c.speech_id, c.paragraph, c.offset) for c in cuts}) != len(cuts):
        raise ValueError("duplicate clause cut")
    sources = [
        manifest_path,
        coverage_path,
        section_path,
        clause_cuts.resolve(),
        *(model_path / name for name in MODEL_FILES),
    ]
    if acting_score_path is not None:
        sources.append(acting_score_path)
    tokenizer = EnTokenizer(str(model_path / "tokenizer.json"))
    if calibration_record is not None:
        sources.append(calibration_record.resolve())
    segments: list[RenderSegment] = []
    seen: set[str] = set()
    used_cuts: set[tuple[str, int, int]] = set()
    references: dict[str, str] = {}
    changed: set[str] = set()
    proposed_parameters: dict[str, Parameters] = {}
    realized_parameters: dict[str, Parameters] = {}
    for script_name in manifest.script_files:
        path = adaptation / script_name
        sources.append(path)
        script = read_script(path.read_text())
        proposed_parameters.update({speech.id: speech.parameters for speech in script.speech})
        if calibration is not None:
            if calibrated_script_dir is None:
                raise ValueError("calibrated scripts require a candidate directory")
            candidate_path = (calibrated_script_dir / Path(script_name).name).resolve()
            if calibration.source_script_hashes.get(script_name) != sha256(
                path
            ) or calibration.candidate_script_hashes.get(script_name) != sha256(candidate_path):
                raise ValueError(
                    "calibration record does not attest exact source/candidate scripts"
                )
            candidate = read_script(candidate_path.read_text())
            if len(candidate.speech) != len(script.speech):
                raise ValueError("calibration changed speech coverage")
            restored = candidate.model_copy(
                update={
                    "speech": [
                        s.model_copy(update={"parameters": original.parameters})
                        for s, original in zip(candidate.speech, script.speech)
                    ]
                }
            )
            if restored != script:
                raise ValueError(
                    "calibration may change only six speech controls; preserve source/voice/structure"
                )
            changed.update(
                s.id
                for s, original in zip(candidate.speech, script.speech)
                if s.parameters != original.parameters
            )
            sources.append(candidate_path)
            script = candidate
        realized_parameters.update({speech.id: speech.parameters for speech in script.speech})
        for voice, binding in script.voices.items():
            resolved = "builtin" if binding == "builtin" else str((ROOT / binding).resolve())
            if voice in references and references[voice] != resolved:
                raise ValueError("conflicting voice bindings")
            references[voice] = resolved
            if resolved != "builtin":
                source = Path(resolved)
                source.relative_to(ROOT)
                if not source.is_file():
                    raise ValueError(f"missing voice: {binding}")
                sources.append(source)
        for speech in script.speech:
            if speech.id in seen:
                raise ValueError("duplicate speech across scripts")
            seen.add(speech.id)
            for number, text in enumerate(speech.paragraphs):
                relevant = [c for c in cuts if c.speech_id == speech.id and c.paragraph == number]
                used_cuts.update((c.speech_id, c.paragraph, c.offset) for c in relevant)
                try:
                    spans = generation_spans(
                        text, tokenizer, token_limit, [c.offset for c in relevant]
                    )
                except ValueError as error:
                    raise ValueError(
                        f"{script_name} {speech.id} paragraph {number}: {error}"
                    ) from error
                for start, end in spans:
                    raw = text[start:end].strip()
                    native = punc_norm(raw)
                    data: dict[str, object] = {
                        "id": f"g{len(segments)+1:06d}",
                        "script": script_name,
                        "section_id": script_to_section[script_name],
                        "speech_id": speech.id,
                        "paragraph": number,
                        "start": start,
                        "end": end,
                        "text": raw,
                        "native_text": native,
                        "native_tokens": int(tokenizer.text_to_tokens(native).shape[-1]),
                        "voice": speech.voice,
                        "parameters": speech.parameters.model_dump(),
                        "seed": seed + len(segments),
                        "heading_level": speech.heading_level,
                    }
                    if manifest.acting_score_hash:
                        direction = directing_by_speech[speech.id]
                        if (
                            Parameters.model_validate(direction.proposed_parameters)
                            != proposed_parameters[speech.id]
                        ):
                            raise ValueError(
                                "coverage proposed vector differs from source script: " + speech.id
                            )
                        data.update(
                            {
                                "score_move_ids": direction.score_move_ids,
                                "directing_action": direction.action,
                                "proposed_parameters": proposed_parameters[speech.id].model_dump(),
                            }
                        )
                    segments.append(RenderSegment.model_validate(data))
    if len(used_cuts) != len(cuts):
        raise ValueError("clause cut does not locate speech")
    if seed < 0 or seed + len(segments) - 1 >= 2**32:
        raise ValueError("segment seeds must fit NumPy native unsigned 32-bit range")
    overrides = (
        []
        if seed_overrides is None
        else TypeAdapter(list[SeedOverride]).validate_json(seed_overrides.read_text())
    )
    if len({item.segment_id for item in overrides}) != len(overrides):
        raise ValueError("duplicate segment seed override")
    by_id = {segment.id: segment for segment in segments}
    for item in overrides:
        if item.segment_id not in by_id or not item.reason.strip():
            raise ValueError("seed override requires a known segment and scoped reason")
        by_id[item.segment_id].seed = item.seed
    if seed_overrides is not None:
        sources.append(seed_overrides.resolve())
    validate_calibration_provenance(
        calibration,
        changed,
        directing_by_speech,
        proposed_parameters,
        realized_parameters,
        bool(manifest.acting_score_hash),
    )
    expected = [span.speech_id for item in coverage for span in item.speech_spans]
    actual = list(dict.fromkeys(segment.speech_id for segment in segments))
    if expected != actual:
        raise ValueError("script order does not match adaptation ledger")
    delivery_sections: list[DeliverySection] = []
    for section in adapted_sections:
        if not section.delivery_chapter:
            continue
        matching = [segment for segment in segments if segment.speech_id == section.title_speech_id]
        if not matching or matching[0].start != 0:
            raise ValueError(
                "delivery section title has no exact render start: " + section.section_id
            )
        title = " ".join(segment.text for segment in matching)
        if " ".join(title.split()) != " ".join(section.normalized_title.split()):
            raise ValueError("delivery title bypassed normalized speech: " + section.section_id)
        delivery_sections.append(
            DeliverySection(
                section_id=section.section_id,
                title=section.normalized_title,
                title_speech_id=section.title_speech_id or "",
                start_segment_id=matching[0].id,
            )
        )
    if not delivery_sections:
        raise ValueError("at least one explicit delivery section required")
    data_plan: dict[str, object] = {
        "render_version": 2,
        "title": manifest.title,
        "author": manifest.author,
        "model_path": str(model_path),
        "device": device,
        "token_limit": token_limit,
        "voices": references,
        "runtime_hashes": runtime_hashes(),
        "input_hashes": {str(p): sha256(p) for p in sources},
        "clause_cuts": [c.model_dump() for c in cuts],
        "segments": segments,
        "delivery_sections": delivery_sections,
    }
    if manifest.acting_score_hash:
        data_plan["acting_score_hash"] = manifest.acting_score_hash
    data_plan["seed_overrides"] = [item.model_dump() for item in overrides]
    if calibration is not None:
        data_plan["calibration"] = calibration.model_dump()
    result = RenderPlan.model_validate(data_plan)
    workspace.mkdir(parents=True)
    atomic(workspace / "plan.json", result)
    atomic(
        workspace / "manifest.json",
        {"plan_hash": identity(result), "audio_quality_verified": False},
    )
    if reuse_from is not None:
        prior = load_plan(reuse_from)
        prior_segments = {item.id: item for item in prior.segments}
        reused = 0
        for segment in segments:
            previous = prior_segments.get(segment.id)
            if previous is None or generation_identity(prior, previous) != generation_identity(
                result, segment
            ):
                continue
            record = verified_segment(reuse_from, prior, previous)
            if record is None:
                continue
            directory = workspace / "audio"
            directory.mkdir(exist_ok=True)
            target = directory / (segment.id + ".wav")
            temporary = target.with_suffix(".tmp.wav")
            shutil.copyfile(reuse_from / "audio" / target.name, temporary)
            temporary.replace(target)
            atomic(target.with_suffix(".json"), record)
            reused += 1
        typer.echo(f"{reused} unchanged generation requests reused with verified audio")
    typer.echo(f"{len(segments)} native-tokenized generation segments; plan {identity(result)}")


def audio_properties(path: Path) -> AudioProperties:
    import numpy as np

    # SoundFile 0.14 annotates this API but ships no py.typed marker (docs/typing-boundaries.md).
    import soundfile as sf  # pyright: ignore[reportMissingTypeStubs]

    audio, rate = sf.read(path, dtype="float32", always_2d=True)
    if not len(audio) or not np.isfinite(audio).all():
        raise ValueError("empty or nonfinite saved audio")
    return AudioProperties(
        sample_rate=rate,
        channels=int(audio.shape[1]),
        frames=len(audio),
        duration_seconds=len(audio) / rate,
        peak=float(np.max(np.abs(audio))),
        rms=float(np.sqrt(np.mean(audio.astype(np.float64) ** 2))),
        dc_offset=float(np.mean(audio.astype(np.float64))),
    )


def generation_identity(plan: RenderPlan, segment: RenderSegment) -> str:
    if plan.render_version == 1:
        return identity({"plan": identity(plan), "segment": segment})
    binding = plan.voices[segment.voice]
    return identity(
        {
            "segment": segment,
            "runtime_hashes": plan.runtime_hashes,
            "device": plan.device,
            "model_hashes": {
                name: plan.input_hashes[str(Path(plan.model_path) / name)] for name in MODEL_FILES
            },
            "reference": (
                binding
                if binding == "builtin"
                else {"path": binding, "hash": plan.input_hashes[binding]}
            ),
        }
    )


def verified_segment(
    workspace: Path, plan: RenderPlan, segment: RenderSegment
) -> AudioRecord | None:
    path = workspace / "audio" / (segment.id + ".wav")
    record_path = path.with_suffix(".json")
    if not record_path.exists():
        return None
    record = AudioRecord.model_validate_json(record_path.read_text())
    if record.generation_hash != generation_identity(plan, segment):
        raise ValueError("saved segment has a different generation identity")
    if record.audio_hash != sha256(path) or record.properties != audio_properties(path):
        raise ValueError("saved audio changed or failed decoded verification")
    return record


def _definition_fingerprint(path: Path, names: set[str]) -> str:
    tree = ast.parse(path.read_text())
    definitions: list[ast.stmt] = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name in names
    ]
    if {
        node.name
        for node in definitions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    } != names:
        raise ValueError("generation implementation definition missing")
    return hashlib.sha256(
        ast.dump(ast.Module(body=definitions, type_ignores=[]), include_attributes=False).encode()
    ).hexdigest()


@app.command("import-verified-revision")
def import_verified_revision(
    workspace: Path, prior_workspace: Path, verifier_checkout: Path
) -> None:
    """Reuse waveforms only after their recorded runtime verifies in an isolated checkout."""
    workspace = work_path(workspace)
    prior_workspace = work_path(prior_workspace)
    plan = load_plan(workspace)
    prior_plan = RenderPlan.model_validate_json((prior_workspace / "plan.json").read_text())
    verifier_source = verifier_checkout / "src" / "audiobooks" / "rendering.py"
    if not (verifier_checkout / "pyproject.toml").is_file() or not verifier_source.is_file():
        raise ValueError("isolated verifier checkout lacks the recorded rendering implementation")
    status_result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(verifier_checkout),
            "--locked",
            "audiobooks",
            "render",
            "status",
            str(prior_workspace.resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    expected_status = (
        f"{len(prior_plan.segments)}/{len(prior_plan.segments)} saved segments verified"
    )
    if status_result.returncode or expected_status not in status_result.stdout:
        raise ValueError("recorded revision did not verify every prior waveform")
    fingerprint_names = {"render", "audio_properties"}
    current_fingerprint = _definition_fingerprint(Path(__file__), fingerprint_names)
    verifier_fingerprint = _definition_fingerprint(verifier_source, fingerprint_names)
    if current_fingerprint != verifier_fingerprint:
        raise ValueError("waveform-producing implementation differs from the verified revision")
    current_parameters = _definition_fingerprint(
        ROOT / "src" / "audiobooks" / "script_contract.py", {"Record", "Parameters"}
    )
    verifier_parameters = _definition_fingerprint(
        verifier_checkout / "src" / "audiobooks" / "script_contract.py", {"Record", "Parameters"}
    )
    if current_parameters != verifier_parameters:
        raise ValueError("generation control schema differs from the verified revision")
    revision = subprocess.run(
        ["git", "-C", str(verifier_checkout), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if plan.device != prior_plan.device or plan.voices != prior_plan.voices:
        raise ValueError("device or voice conditioning differs from the verified plan")
    for name in MODEL_FILES:
        old = prior_plan.input_hashes[str(Path(prior_plan.model_path) / name)]
        new = plan.input_hashes[str(Path(plan.model_path) / name)]
        if old != new:
            raise ValueError("model snapshot bytes differ from the verified plan")
    for dependency in ("uv.lock",):
        if prior_plan.runtime_hashes.get(dependency) != plan.runtime_hashes.get(dependency):
            raise ValueError("generation dependency differs from the verified plan: " + dependency)
    prior_by_id = {segment.id: segment for segment in prior_plan.segments}
    imported: list[dict[str, str]] = []
    directory = workspace / "audio"
    directory.mkdir(exist_ok=True)
    for segment in plan.segments:
        previous = prior_by_id.get(segment.id)
        current_request = segment.model_dump(exclude_unset=True, exclude={"section_id"})
        if previous is None or previous.model_dump(exclude_unset=True) != current_request:
            raise ValueError("generation request differs from verified revision: " + segment.id)
        source = prior_workspace / "audio" / (segment.id + ".wav")
        prior_record = AudioRecord.model_validate_json(source.with_suffix(".json").read_text())
        if (
            sha256(source) != prior_record.audio_hash
            or audio_properties(source) != prior_record.properties
        ):
            raise ValueError("prior waveform changed after recorded-revision verification")
        target = directory / source.name
        temporary = target.with_suffix(".tmp.wav")
        shutil.copyfile(source, temporary)
        if sha256(temporary) != prior_record.audio_hash:
            raise ValueError("waveform bytes changed during verified import")
        temporary.replace(target)
        record = AudioRecord(
            generation_hash=generation_identity(plan, segment),
            audio_hash=sha256(target),
            properties=audio_properties(target),
        )
        atomic(target.with_suffix(".json"), record)
        imported.append({"segment_id": segment.id, "audio_hash": record.audio_hash})
    import_record = {
        "import_version": 1,
        "prior_plan_hash": identity(prior_plan),
        "verifier_git_revision": revision,
        "generation_implementation_fingerprint": current_fingerprint,
        "generation_parameters_fingerprint": current_parameters,
        "recorded_status": status_result.stdout.strip(),
        "segments": imported,
    }
    atomic(workspace / "verified-revision-import.json", import_record)
    manifest = RenderManifest.model_validate_json((workspace / "manifest.json").read_text())
    atomic(
        workspace / "manifest.json",
        {
            **manifest.model_dump(exclude_unset=True),
            "verified_revision_import_hash": identity(import_record),
        },
    )
    load_plan(workspace)
    typer.echo(
        f"{len(imported)} exact generation requests imported from verified revision {revision[:12]}"
    )


@app.command("generate")
def render(workspace: Path, segment_ids: str = "") -> None:
    """Generate a selected audition or all segments; reuse only verified saved audio."""
    workspace = work_path(workspace)
    import numpy as np

    # SoundFile 0.14 annotates this API but ships no py.typed marker (docs/typing-boundaries.md).
    import soundfile as sf  # pyright: ignore[reportMissingTypeStubs]
    import torch
    from chatterbox.tts import ChatterboxTTS

    plan = load_plan(workspace)
    selected = set(segment_ids.split(",")) if segment_ids else {s.id for s in plan.segments}
    if not selected <= {s.id for s in plan.segments}:
        raise ValueError("unknown generation segment")
    pending = [
        s
        for s in plan.segments
        if s.id in selected and verified_segment(workspace, plan, s) is None
    ]
    if not pending:
        typer.echo("all selected segments verified")
        return
    model = ChatterboxTTS.from_local(plan.model_path, device=plan.device)
    builtin = copy.deepcopy(model.conds)
    if builtin is None:
        raise ValueError("model snapshot has no builtin conditioning")
    directory = workspace / "audio"
    directory.mkdir(exist_ok=True)
    for segment in pending:
        random.seed(segment.seed)
        np.random.seed(segment.seed)
        # Upstream torch.random.manual_seed leaves its seed parameter unannotated; segment.seed is int.
        torch.manual_seed(segment.seed)  # pyright: ignore[reportUnknownMemberType]
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(segment.seed)
        binding = plan.voices[segment.voice]
        model.conds = copy.deepcopy(builtin)
        parameters = segment.parameters
        wav = model.generate(
            segment.text,
            audio_prompt_path=None if binding == "builtin" else binding,
            exaggeration=parameters.exaggeration,
            cfg_weight=parameters.cfg_weight,
            temperature=parameters.temperature,
            repetition_penalty=parameters.repetition_penalty,
            min_p=parameters.min_p,
            top_p=parameters.top_p,
        )
        audio = wav.detach().cpu().numpy().T
        target = directory / (segment.id + ".wav")
        temporary = target.with_suffix(".tmp.wav")
        sf.write(temporary, audio, model.sr, subtype="FLOAT")
        properties = audio_properties(temporary)
        if properties.sample_rate != model.sr or properties.channels != 1:
            raise ValueError("unexpected original Chatterbox audio shape/rate")
        temporary.replace(target)
        atomic(
            target.with_suffix(".json"),
            {
                "generation_hash": generation_identity(plan, segment),
                "audio_hash": sha256(target),
                "properties": properties,
            },
        )
        typer.echo(
            f"{segment.id} {segment.speech_id} {properties.duration_seconds:.2f}s verified saved audio",
            err=False,
        )


@app.command()
def status(workspace: Path) -> None:
    """Validate current inputs and every completed generation segment."""
    workspace = work_path(workspace)
    plan = load_plan(workspace)
    complete = [s.id for s in plan.segments if verified_segment(workspace, plan, s)]
    typer.echo(
        f"{len(complete)}/{len(plan.segments)} saved segments verified; audio quality unreviewed"
    )
