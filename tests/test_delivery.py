"""Regressions for title semantics, atomic export, and real sample/chapter boundaries."""

import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf  # pyright: ignore[reportMissingTypeStubs]

from audiobooks.assembly import (
    AssemblyRecord,
    ChapterTitleReview,
    ChapterTitleReviewSet,
    assemble,
    reviewed_chapter_titles,
)
from audiobooks.delivery import encode_m4b
from audiobooks.files import write_atomic
from audiobooks.rendering import (
    AudioRecord,
    ChapterSource,
    DeliverySection,
    RenderPlan,
    RenderSegment,
    audio_properties,
    generation_identity,
    runtime_hashes,
)
from audiobooks.source_units import identity, sha256
from tests.test_acting_score import DEFAULT_PARAMETERS
from tests.test_cli import invoke


def write_delivery(path: Path, contents: bytes, *, verified: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(contents)
    write_atomic(
        path.with_suffix(".json"),
        {
            "delivery_version": 1,
            "output_hash": sha256(path),
            "verification_passed": verified,
            "probe": {
                "format": {"tags": {"artist": "Plotinus", "title": "An Essay on the Beautiful"}}
            },
        },
    )


@pytest.mark.parametrize(
    ("source", "valid", "invalid"),
    [
        (
            "Man is spirit. The spirit of the lover is in the beloved",
            "Man Is Spirit. The Spirit of the Lover Is in the Beloved",
            "Man Is Spirit. the Spirit of the Lover Is in the Beloved",
        ),
        ("CONCERNING THE BEAUTIFUL", "Concerning the Beautiful", "Concerning The Beautiful"),
    ],
)
def test_chapter_title_case_distinguishes_sentence_starts_from_minor_words(
    tmp_path: Path,
    source: str,
    valid: str,
    invalid: str,
) -> None:
    path = tmp_path / "titles.json"
    chapter = ChapterSource(section_id="work", title=source)
    review = {
        "section_id": "work",
        "source_title": source,
        "title": valid,
        "coherence": "Names the exact authored section.",
        "plausibility": "Preserves the words.",
    }
    write_atomic(path, {"style": "English title case", "chapters": [review]})
    assert reviewed_chapter_titles([chapter], path)["work"].title == valid
    review["title"] = invalid
    write_atomic(path, {"style": "English title case", "chapters": [review]})
    with pytest.raises(ValueError, match="consistent English title case"):
        reviewed_chapter_titles([chapter], path)
    review.update(title=valid, coherence="   ")
    write_atomic(path, {"style": "English title case", "chapters": [review]})
    with pytest.raises(ValueError, match="contextual evidence"):
        reviewed_chapter_titles([chapter], path)


def test_export_keeps_base_and_replaces_only_expected_variant_bytes(tmp_path: Path) -> None:
    source = tmp_path / "delivery/spirited.m4b"
    write_delivery(source, b"verified spirited audiobook")
    environment = {"EXPORT_DIR": str(tmp_path / "exports")}
    base = tmp_path / "exports/plotinus.an-essay-on-the-beautiful/essay-on-the-beautiful.m4b"
    base.parent.mkdir(parents=True)
    base.write_bytes(b"restrained audiobook")
    exported = invoke(
        tmp_path,
        "delivery",
        "export",
        str(source),
        "--variant",
        "spirited",
        environment=environment,
    )
    assert exported.returncode == 0, exported.stderr
    target = Path(exported.stdout.strip())
    assert target.name == "essay-on-the-beautiful-spirited.m4b"
    assert target.read_bytes() == source.read_bytes()
    assert base.read_bytes() == b"restrained audiobook"
    prior_hash = sha256(target)
    write_delivery(source, b"corrected verified audiobook")
    rejected = invoke(
        tmp_path,
        "delivery",
        "export",
        str(source),
        "--variant",
        "spirited",
        "--replace-hash",
        "0" * 64,
        environment=environment,
    )
    assert rejected.returncode != 0
    assert "expected existing hash" in rejected.stderr
    assert sha256(target) == prior_hash
    replaced = invoke(
        tmp_path,
        "delivery",
        "export",
        str(source),
        "--variant",
        "spirited",
        "--replace-hash",
        prior_hash,
        environment=environment,
    )
    assert replaced.returncode == 0, replaced.stderr
    assert target.read_bytes() == source.read_bytes()
    assert base.read_bytes() == b"restrained audiobook"


def test_export_rejects_unverified_delivery_without_creating_library(tmp_path: Path) -> None:
    source = tmp_path / "unverified.m4b"
    write_delivery(source, b"unverified", verified=False)
    result = invoke(
        tmp_path,
        "delivery",
        "export",
        str(source),
        environment={"EXPORT_DIR": str(tmp_path / "exports")},
    )
    assert result.returncode != 0
    assert "verified delivery" in result.stderr
    assert not (tmp_path / "exports").exists()


def test_assembly_preserves_samples_and_excludes_subheadings_from_navigation(
    tmp_path: Path,
) -> None:
    root = tmp_path
    workspace = root / "render"
    audio_directory = workspace / "audio"
    audio_directory.mkdir(parents=True)
    sample_rate = 24000
    segment_definitions: list[tuple[str, str, str, int]] = [
        ("g000001", "s000001", "OPENING", 1),
        ("g000002", "s000002", "Subsection", 2),
        ("g000003", "s000003", "CHAPTER TWO", 1),
        ("g000004", "s000004", "CLOSING", 1),
    ]
    segments = [
        RenderSegment(
            id=segment_id,
            script="script/0001.md",
            speech_id=speech_id,
            paragraph=0,
            start=0,
            end=len(text),
            text=text,
            native_text=text,
            native_tokens=len(text),
            voice="narrator",
            parameters=DEFAULT_PARAMETERS,
            seed=index,
            heading_level=heading_level,
        )
        for index, (segment_id, speech_id, text, heading_level) in enumerate(segment_definitions)
    ]
    plan = RenderPlan(
        render_version=1,
        model_path=str(root / "model"),
        device="cpu",
        voices={"narrator": "builtin"},
        title="Synthetic Book",
        author="Fixture Author",
        runtime_hashes=runtime_hashes(),
        input_hashes={},
        segments=segments,
        delivery_sections=[
            DeliverySection(
                section_id=section,
                title=segments[index].text,
                title_speech_id=segments[index].speech_id,
                start_segment_id=segments[index].id,
            )
            for section, index in [("one", 0), ("two", 2), ("three", 3)]
        ],
    )
    write_atomic(workspace / "plan.json", plan)
    (workspace / "manifest.json").write_text(json.dumps({"plan_hash": identity(plan)}))
    source_samples: list[np.ndarray[tuple[int], np.dtype[np.float32]]] = []
    for index, segment in enumerate(segments, 1):
        frames = sample_rate // 4
        sample_times = np.arange(frames, dtype=np.float64) / sample_rate
        audio = (0.05 * np.sin(2 * np.pi * (200 + index * 20) * sample_times)).astype(np.float32)
        source_samples.append(audio)
        path = audio_directory / f"{segment.id}.wav"
        sf.write(path, audio, sample_rate, format="WAV", subtype="FLOAT")
        write_atomic(
            path.with_suffix(".json"),
            AudioRecord(
                generation_hash=generation_identity(plan, segment),
                audio_hash=sha256(path),
                properties=audio_properties(path),
            ),
        )
    gaps = root / "gaps.json"
    gaps.write_text("[]\n")
    chapter_titles = root / "chapter-titles.json"
    write_atomic(
        chapter_titles,
        ChapterTitleReviewSet(
            style="English title case",
            chapters=[
                ChapterTitleReview(
                    section_id=c.section_id,
                    source_title=c.title,
                    title=c.title.title(),
                    coherence="Names the section at its exact first speech.",
                    plausibility="Only display casing changes; all source words remain.",
                )
                for c in plan.delivery_sections
            ],
        ),
    )
    assembly = root / "assembly"
    assemble(workspace, assembly, gaps, chapter_titles)
    assembled, _ = sf.read(assembly / "assembly.wav", dtype="float32")
    assert np.array_equal(assembled, np.concatenate(source_samples))
    assembly_record = AssemblyRecord.model_validate_json((assembly / "assembly.json").read_text())
    assert [chapter.title for chapter in assembly_record.chapters] == [
        "Opening",
        "Chapter Two",
        "Closing",
    ]
    assert [chapter.source_title for chapter in assembly_record.chapters] == [
        "OPENING",
        "CHAPTER TWO",
        "CLOSING",
    ]
    assert "Subsection" not in (assembly / "chapters.ffmetadata").read_text()

    output = root / "synthetic.m4b"
    manifest = encode_m4b(assembly, output, bitrate="64k", gain_db=-1.0, system_ffmpeg=True)
    assert output.is_file()
    assert manifest.verification_passed
    assert [chapter.title for chapter in manifest.chapters] == ["Opening", "Chapter Two", "Closing"]
    assert manifest.probe.streams[0].codec_name == "aac"
    assert manifest.input_audio_hash == assembly_record.audio_hash
    exported = invoke(
        tmp_path,
        "delivery",
        "export",
        str(output),
        environment={"EXPORT_DIR": str(tmp_path / "finished")},
    )
    assert exported.returncode == 0, exported.stderr
    assert Path(exported.stdout.strip()).read_bytes() == output.read_bytes()
