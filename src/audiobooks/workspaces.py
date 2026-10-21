"""Canonical locations for generated book work."""

from __future__ import annotations

import os
from pathlib import Path

REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[2]
    if (Path(__file__).resolve().parents[2] / "pyproject.toml").is_file()
    else Path(__file__).resolve().parent / "data"
)


def workspace_dir() -> Path:
    """Return a persistent work directory outside installed plugin and tool caches."""
    configured = os.environ.get("WORKSPACE_DIR", "").strip()
    directory = Path(configured).expanduser() if configured else Path.home() / "Audiobooks" / "work"
    return directory.resolve()


def work_path(path: Path) -> Path:
    """Resolve a relative work path below the shared work root."""
    if path.is_absolute():
        return path.expanduser().resolve()
    directory = workspace_dir()
    resolved = (directory / path).resolve()
    try:
        resolved.relative_to(directory)
    except ValueError:
        raise ValueError("relative work path escapes WORKSPACE_DIR") from None
    return resolved
