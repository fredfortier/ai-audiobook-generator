"""Exported script identities must survive until rendering freezes its inputs."""

from pathlib import Path

import pytest

from audiobooks.adaptation import verify_exported_scripts
from audiobooks.source_units import sha256


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
