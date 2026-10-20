"""Encode and independently verify chaptered AAC/M4B delivery artifacts."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

from audiobooks.files import write_atomic
from audiobooks.source_units import sha256
from audiobooks.workspaces import work_path


def _slug(value: str, limit: int = 80) -> str:
    value = value.replace("'", "").replace("’", "")
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")
    if not slug:
        raise ValueError("author and title metadata must form portable names")
    if len(slug) > limit:
        digest = hashlib.sha256(value.encode()).hexdigest()[:8]
        slug = slug[: limit - len(digest) - 1].rstrip("-") + "-" + digest
    return slug


def _short_title(title: str) -> str:
    title = re.split(r":|\s+[—–-]\s+", title, maxsplit=1)[0].strip()
    words = title.split()
    if len(words) > 1 and words[0].casefold() in {"a", "an", "the"}:
        title = " ".join(words[1:])
    return title


def export_m4b(
    delivery: Path, *, variant: str | None = None, replace_hash: str | None = None
) -> Path:
    """Copy a hash-verified delivery to its deterministic EXPORT_DIR path."""
    configured = os.environ.get("EXPORT_DIR", "").strip()
    if not configured:
        raise ValueError("EXPORT_DIR is required unless export was explicitly waived")
    delivery = work_path(delivery)
    if delivery.suffix.lower() != ".m4b" or not delivery.is_file():
        raise ValueError("an existing .m4b delivery is required")
    manifest_path = delivery.with_suffix(".json")
    if not manifest_path.is_file():
        raise ValueError("verified delivery manifest is required")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("delivery_version") != 1 or manifest.get("verification_passed") is not True:
        raise ValueError("verified delivery manifest is required")
    if manifest.get("output_hash") != sha256(delivery):
        raise ValueError("delivery differs from its verified manifest")
    tags = manifest.get("probe", {}).get("format", {}).get("tags", {})
    author = tags.get("artist", "").strip()
    title = tags.get("title", "").strip()
    if not author or not title:
        raise ValueError("verified delivery requires author and title metadata")
    if variant is not None and not variant.strip():
        raise ValueError("export variant must be nonblank when supplied")

    export_directory = Path(configured).expanduser().resolve()
    book_directory = export_directory / f"{_slug(author)}.{_slug(title)}"
    export_title = _short_title(title)
    if variant is not None:
        export_title += " " + variant.strip()
    target = book_directory / f"{_slug(export_title)}.m4b"
    if target.exists():
        current_hash = sha256(target)
        if current_hash == manifest["output_hash"]:
            return target
        if replace_hash is None:
            raise ValueError(f"export target contains a different file: {target}")
        if not re.fullmatch(r"[0-9a-f]{64}", replace_hash) or current_hash != replace_hash:
            raise ValueError(f"export target differs from expected existing hash: {target}")
    elif replace_hash is not None:
        raise ValueError(f"expected existing export target is absent: {target}")

    book_directory.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name("." + target.name + ".partial")
    if temporary.exists():
        raise ValueError(f"stale partial export exists: {temporary}")
    try:
        shutil.copyfile(delivery, temporary)
        if sha256(temporary) != manifest["output_hash"]:
            raise ValueError("exported delivery hash differs")
        if replace_hash is not None:
            if not target.exists() or sha256(target) != replace_hash:
                raise ValueError(f"export target differs from expected existing hash: {target}")
            os.replace(temporary, target)
        else:
            try:
                os.link(temporary, target)
            except FileExistsError:
                if sha256(target) != manifest["output_hash"]:
                    raise ValueError(f"export target contains a different file: {target}") from None
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    temporary.unlink(missing_ok=True)
    return target


def _version(command: str) -> str:
    result = subprocess.run([command, "-version"], capture_output=True, text=True, check=True)
    return result.stdout.splitlines()[0]


def _probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
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
    return json.loads(result.stdout)


def encode_m4b(
    assembly_directory: Path, output: Path, *, bitrate: str = "96k", gain_db: float = 0.0
) -> dict:
    """Encode one verified assembly and compare ffprobe chapters to its frame plan."""
    assembly_directory = work_path(assembly_directory)
    output = work_path(output)
    if output.exists() or output.with_suffix(".json").exists():
        raise ValueError("delivery output and manifest must be new")
    if output.suffix.lower() != ".m4b" or not math.isfinite(gain_db):
        raise ValueError("finite gain and an .m4b output are required")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise ValueError("FFmpeg and ffprobe are required")
    assembly_path = assembly_directory / "assembly.wav"
    metadata_path = assembly_directory / "chapters.ffmetadata"
    record_path = assembly_directory / "assembly.json"
    record = json.loads(record_path.read_text())
    if (
        sha256(assembly_path) != record["audio_hash"]
        or sha256(metadata_path) != record["metadata_hash"]
    ):
        raise ValueError("assembly audio or chapter metadata changed")
    if not record.get("exact_samples_preserved") or not record.get("chapters"):
        raise ValueError("verified lossless assembly with explicit chapters required")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name("." + output.stem + ".partial.m4b")
    if temporary.exists():
        raise ValueError("stale partial delivery exists")
    arguments = [
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-v",
        "error",
        "-i",
        str(assembly_path),
        "-f",
        "ffmetadata",
        "-i",
        str(metadata_path),
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
        probe = _probe(temporary)
        audio_streams = [
            stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"
        ]
        if len(audio_streams) != 1 or audio_streams[0].get("codec_name") != "aac":
            raise ValueError("delivery must contain exactly one AAC audio stream")
        if "mp4" not in probe.get("format", {}).get("format_name", ""):
            raise ValueError("delivery is not an MP4-family container")
        tags = probe.get("format", {}).get("tags", {})
        metadata = record.get("book_metadata", {})
        if tags.get("title") != metadata.get("title"):
            raise ValueError("delivery title metadata differs from the admitted source")
        if metadata.get("author") and tags.get("artist") != metadata["author"]:
            raise ValueError("delivery author metadata differs from the admitted source")
        expected = record["chapters"]
        actual = probe.get("chapters", [])
        if len(actual) != len(expected):
            raise ValueError("ffprobe chapter count differs from the frame plan")
        rate = record["properties"]["sample_rate"]
        tolerance_seconds = max(0.001, 2 / rate)
        verified_chapters = []
        for planned, observed in zip(expected, actual, strict=True):
            planned_start = planned["start"] / rate
            planned_end = planned["end"] / rate
            observed_start = float(observed["start_time"])
            observed_end = float(observed["end_time"])
            title = observed.get("tags", {}).get("title")
            if title != planned["title"]:
                raise ValueError("ffprobe chapter title differs from normalized section title")
            if (
                abs(observed_start - planned_start) > tolerance_seconds
                or abs(observed_end - planned_end) > tolerance_seconds
            ):
                raise ValueError("ffprobe chapter time differs from the frame plan")
            verified_chapters.append(
                {
                    "section_id": planned.get("section_id"),
                    "title": title,
                    "planned_start_frame": planned["start"],
                    "planned_end_frame": planned["end"],
                    "observed_start_seconds": observed_start,
                    "observed_end_seconds": observed_end,
                }
            )
        if any(
            abs(float(actual[index]["end_time"]) - float(actual[index + 1]["start_time"]))
            > tolerance_seconds
            for index in range(len(actual) - 1)
        ):
            raise ValueError("ffprobe chapters are not contiguous")
        temporary.replace(output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    manifest = {
        "delivery_version": 1,
        "ffmpeg_version": _version("ffmpeg"),
        "ffprobe_version": _version("ffprobe"),
        "ffmpeg_arguments": arguments[:-1] + [str(output)],
        "input_audio_hash": record["audio_hash"],
        "ffmetadata_hash": record["metadata_hash"],
        "assembly_record_hash": sha256(record_path),
        "output_hash": sha256(output),
        "codec": "aac",
        "bitrate": bitrate,
        "gain_db": gain_db,
        "timestamp_tolerance_seconds": tolerance_seconds,
        "chapters": verified_chapters,
        "probe": probe,
        "verification_passed": True,
        "audio_quality_verified": False,
    }
    write_atomic(output.with_suffix(".json"), manifest)
    return manifest
