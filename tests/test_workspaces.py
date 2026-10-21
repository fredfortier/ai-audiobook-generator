"""Work roots must not depend on the caller's directory or permit escapes."""

from pathlib import Path

import pytest

from audiobooks.workspaces import work_path, workspace_dir


@pytest.mark.parametrize("value", [None, "", "   "])
def test_unset_and_empty_environment_use_persistent_user_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("WORKSPACE_DIR", raising=False)
    if value is not None:
        monkeypatch.setenv("WORKSPACE_DIR", value)
    assert workspace_dir() == (Path.home() / "Audiobooks" / "work").resolve()


def test_relative_work_path_uses_configured_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "shared"
    monkeypatch.setenv("WORKSPACE_DIR", str(root))
    assert work_path(Path("plotinus/render/enoch")) == root / "plotinus" / "render" / "enoch"


def test_relative_work_path_cannot_escape_configured_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "work"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("WORKSPACE_DIR", str(root))
    for path in (Path("../outside"), Path("escape/book")):
        with pytest.raises(ValueError, match="escapes WORKSPACE_DIR"):
            work_path(path)
