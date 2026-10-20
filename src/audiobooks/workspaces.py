"""Canonical locations for generated book work."""

from __future__ import annotations

import os
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def workspace_dir() -> Path:
    """Return the configured shared work directory or this repository's local default."""
    configured = os.environ.get("WORKSPACE_DIR", "").strip()
    directory = Path(configured).expanduser() if configured else REPOSITORY_ROOT / ".workspace"
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
