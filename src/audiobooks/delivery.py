"""Encode and independently verify chaptered AAC/M4B delivery artifacts."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import unicodedata
from pathlib import Path

from m4b_encoding import Chapter, EncodingReport, Probe
from m4b_encoding import encode_m4b as encode_audio
from pydantic import ConfigDict
from static_ffmpeg.run import (
    get_or_fetch_platform_executables_else_raise,  # pyright: ignore[reportUnknownVariableType]
)

from audiobooks.assembly import AssemblyRecord
from audiobooks.files import Record, write_atomic
from audiobooks.source_units import sha256
from audiobooks.workspaces import work_path


class DeliveryIdentity(Record):
    model_config = ConfigDict(extra="allow", strict=True)
    delivery_version: int
    verification_passed: bool
    output_hash: str
    probe: Probe


class DeliveryManifest(EncodingReport):
    delivery_version: int
    assembly_record_hash: str
    audio_quality_verified: bool


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
    manifest = DeliveryIdentity.model_validate_json(manifest_path.read_text())
    if manifest.delivery_version != 1 or manifest.verification_passed is not True:
        raise ValueError("verified delivery manifest is required")
    if manifest.output_hash != sha256(delivery):
        raise ValueError("delivery differs from its verified manifest")
    tags = manifest.probe.format.tags
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
        if current_hash == manifest.output_hash:
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
        if sha256(temporary) != manifest.output_hash:
            raise ValueError("exported delivery hash differs")
        if replace_hash is not None:
            if not target.exists() or sha256(target) != replace_hash:
                raise ValueError(f"export target differs from expected existing hash: {target}")
            os.replace(temporary, target)
        else:
            try:
                os.link(temporary, target)
            except FileExistsError:
                if sha256(target) != manifest.output_hash:
                    raise ValueError(f"export target contains a different file: {target}") from None
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    temporary.unlink(missing_ok=True)
    return target


def encode_m4b(
    assembly_directory: Path,
    output: Path,
    *,
    bitrate: str = "96k",
    gain_db: float = 0.0,
    system_ffmpeg: bool = False,
) -> DeliveryManifest:
    """Admit a verified assembly, encode it, and bind its production provenance."""
    assembly_directory = work_path(assembly_directory)
    output = work_path(output)
    if output.exists() or output.with_suffix(".json").exists():
        raise ValueError("delivery output and manifest must be new")
    audio = assembly_directory / "assembly.wav"
    metadata = assembly_directory / "chapters.ffmetadata"
    record_path = assembly_directory / "assembly.json"
    record = AssemblyRecord.model_validate_json(record_path.read_text())
    if sha256(audio) != record.audio_hash or sha256(metadata) != record.metadata_hash:
        raise ValueError("assembly audio or chapter metadata changed")
    if not record.exact_samples_preserved or not record.chapters:
        raise ValueError("verified lossless assembly with explicit chapters required")
    if system_ffmpeg:
        ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
        if ffmpeg is None or ffprobe is None:
            raise ValueError("--system-ffmpeg requires both ffmpeg and ffprobe on PATH")
    else:
        ffmpeg, ffprobe = get_or_fetch_platform_executables_else_raise()
    report = encode_audio(
        audio,
        metadata,
        output,
        sample_rate=record.properties.sample_rate,
        chapters=[
            Chapter(section_id=c.section_id, title=c.title, start_frame=c.start, end_frame=c.end)
            for c in record.chapters
        ],
        title=record.book_metadata.title,
        author=record.book_metadata.author,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
        bitrate=bitrate,
        gain_db=gain_db,
    )
    manifest = DeliveryManifest(
        **report.model_dump(),
        delivery_version=1,
        assembly_record_hash=sha256(record_path),
        audio_quality_verified=False,
    )
    write_atomic(output.with_suffix(".json"), manifest)
    return manifest
