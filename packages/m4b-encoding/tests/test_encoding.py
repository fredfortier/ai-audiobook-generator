"""Real AAC encoding must fail closed when metadata or timing diverges from the plan."""

import wave
from pathlib import Path

import pytest
from m4b_encoding import Chapter, encode_m4b


@pytest.mark.parametrize(
    ("title", "chapter_title", "end_frame", "reason"),
    [
        ("Different", "Opening", 24000, "encoded title"),
        ("Probe", "Invented", 24000, "chapter title"),
        ("Probe", "Opening", 12000, "chapter time"),
    ],
)
def test_encoding_rejects_actual_metadata_or_timing_mismatch(
    tmp_path: Path,
    title: str,
    chapter_title: str,
    end_frame: int,
    reason: str,
) -> None:
    audio = tmp_path / "source.wav"
    with wave.open(str(audio), "wb") as stream:
        stream.setparams((1, 2, 24000, 24000, "NONE", "not compressed"))
        stream.writeframes(b"\0\0" * 24000)
    metadata = tmp_path / "chapters.ffmetadata"
    metadata.write_text(
        ";FFMETADATA1\ntitle=Probe\n[CHAPTER]\nTIMEBASE=1/24000\nSTART=0\nEND=24000\ntitle=Opening\n"
    )
    output = tmp_path / "book.m4b"
    with pytest.raises(ValueError, match=reason):
        encode_m4b(
            audio,
            metadata,
            output,
            sample_rate=24000,
            title=title,
            chapters=[
                Chapter(section_id="one", title=chapter_title, start_frame=0, end_frame=end_frame)
            ],
        )
    assert not output.exists()
    assert not (tmp_path / ".book.partial.m4b").exists()
