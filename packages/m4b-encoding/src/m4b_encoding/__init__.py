"""AAC/M4B encoding with independently probed chapter and metadata verification."""

import hashlib
import math
import subprocess
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Chapter(Record):
    section_id: str
    title: str
    start_frame: int = Field(ge=0)
    end_frame: int = Field(gt=0)


class ProbeStream(Record):
    model_config = ConfigDict(extra="allow", strict=True)
    codec_type: str = ""
    codec_name: str = ""


class ProbeFormat(Record):
    model_config = ConfigDict(extra="allow", strict=True)
    format_name: str = ""
    tags: dict[str, str] = Field(default_factory=dict)


class ProbeChapter(Record):
    model_config = ConfigDict(extra="allow", strict=True)
    start_time: str
    end_time: str
    tags: dict[str, str] = Field(default_factory=dict)


class Probe(Record):
    model_config = ConfigDict(extra="allow", strict=True)
    streams: list[ProbeStream] = Field(default_factory=list)
    format: ProbeFormat = Field(default_factory=ProbeFormat)
    chapters: list[ProbeChapter] = Field(default_factory=list)


class VerifiedChapter(Record):
    section_id: str
    title: str
    planned_start_frame: int
    planned_end_frame: int
    observed_start_seconds: float
    observed_end_seconds: float


class EncodingReport(Record):
    output_hash: str
    probe: Probe
    verification_passed: bool
    ffmpeg_version: str
    ffprobe_version: str
    ffmpeg_arguments: list[str]
    input_audio_hash: str
    ffmetadata_hash: str
    codec: str
    bitrate: str
    gain_db: float
    timestamp_tolerance_seconds: float
    chapters: list[VerifiedChapter]


def _version(command: str) -> str:
    result = subprocess.run([command, "-version"], capture_output=True, text=True, check=True)
    return result.stdout.splitlines()[0]


def _probe(path: Path, ffprobe: str) -> Probe:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-show_chapters",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return Probe.model_validate_json(result.stdout)


def encode_m4b(
    audio: Path,
    metadata: Path,
    output: Path,
    *,
    sample_rate: int,
    chapters: list[Chapter],
    title: str,
    author: str | None = None,
    ffmpeg: str = "ffmpeg",
    ffprobe: str = "ffprobe",
    bitrate: str = "96k",
    gain_db: float = 0.0,
) -> EncodingReport:
    """Encode audio and verify its metadata and chapters against an explicit frame plan."""
    if output.exists():
        raise ValueError("encoding output must be new")
    if output.suffix.lower() != ".m4b" or not math.isfinite(gain_db):
        raise ValueError("finite gain and an .m4b output are required")
    if sample_rate <= 0 or not chapters or chapters[0].start_frame != 0:
        raise ValueError(
            "positive sample rate and explicit chapters starting at frame zero required"
        )
    if any(left.end_frame != right.start_frame for left, right in zip(chapters, chapters[1:])):
        raise ValueError("planned chapters must be contiguous")
    if any(chapter.end_frame <= chapter.start_frame for chapter in chapters):
        raise ValueError("planned chapters must have positive frame spans")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name("." + output.stem + ".partial.m4b")
    if temporary.exists():
        raise ValueError("stale partial delivery exists")
    arguments = [
        ffmpeg,
        "-hide_banner",
        "-nostdin",
        "-v",
        "error",
        "-i",
        str(audio),
        "-f",
        "ffmetadata",
        "-i",
        str(metadata),
        "-map",
        "0:a:0",
        "-map_metadata",
        "1",
        "-map_chapters",
        "1",
        "-vn",
        "-af",
        f"volume={gain_db:g}dB",
        "-c:a",
        "aac",
        "-b:a",
        bitrate,
        "-movflags",
        "+faststart",
        str(temporary),
    ]
    try:
        subprocess.run(arguments, capture_output=True, text=True, check=True)
        probe = _probe(temporary, ffprobe)
        audio_streams = [stream for stream in probe.streams if stream.codec_type == "audio"]
        if len(audio_streams) != 1 or audio_streams[0].codec_name != "aac":
            raise ValueError("delivery must contain exactly one AAC audio stream")
        if "mp4" not in probe.format.format_name:
            raise ValueError("delivery is not an MP4-family container")
        tags = probe.format.tags
        if tags.get("title") != title:
            raise ValueError("encoded title differs from the requested metadata")
        if author and tags.get("artist") != author:
            raise ValueError("encoded author differs from the requested metadata")
        expected = chapters
        actual = probe.chapters
        if len(actual) != len(expected):
            raise ValueError("ffprobe chapter count differs from the frame plan")
        rate = sample_rate
        tolerance_seconds = max(0.001, 2 / rate)
        verified_chapters: list[VerifiedChapter] = []
        for planned, observed in zip(expected, actual, strict=True):
            planned_start = planned.start_frame / rate
            planned_end = planned.end_frame / rate
            observed_start = float(observed.start_time)
            observed_end = float(observed.end_time)
            if observed.tags.get("title") != planned.title:
                raise ValueError("ffprobe chapter title differs from normalized section title")
            if (
                abs(observed_start - planned_start) > tolerance_seconds
                or abs(observed_end - planned_end) > tolerance_seconds
            ):
                raise ValueError("ffprobe chapter time differs from the frame plan")
            verified_chapters.append(
                VerifiedChapter(
                    section_id=planned.section_id,
                    title=planned.title,
                    planned_start_frame=planned.start_frame,
                    planned_end_frame=planned.end_frame,
                    observed_start_seconds=observed_start,
                    observed_end_seconds=observed_end,
                )
            )
        if any(
            abs(float(actual[index].end_time) - float(actual[index + 1].start_time))
            > tolerance_seconds
            for index in range(len(actual) - 1)
        ):
            raise ValueError("ffprobe chapters are not contiguous")
        temporary.replace(output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    hashes: list[str] = []
    for path in (audio, metadata, output):
        with path.open("rb") as stream:
            hashes.append(hashlib.file_digest(stream, "sha256").hexdigest())
    return EncodingReport(
        ffmpeg_version=_version(ffmpeg),
        ffprobe_version=_version(ffprobe),
        ffmpeg_arguments=arguments[:-1] + [str(output)],
        input_audio_hash=hashes[0],
        ffmetadata_hash=hashes[1],
        output_hash=hashes[2],
        codec="aac",
        bitrate=bitrate,
        gain_db=gain_db,
        timestamp_tolerance_seconds=tolerance_seconds,
        chapters=verified_chapters,
        probe=probe,
        verification_passed=True,
    )
