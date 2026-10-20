"""Small, explicit file persistence helpers shared by pipeline stages."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from pydantic import BaseModel, JsonValue, TypeAdapter


def read_json(path: Path) -> JsonValue:
    """Read a UTF-8 JSON document from ``path``."""
    return TypeAdapter[JsonValue](JsonValue).validate_json(path.read_text(encoding="utf-8"))


def write_atomic(path: Path, content: object) -> None:
    """Atomically replace ``path`` with text or pretty-printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        content
        if isinstance(content, str)
        else json.dumps(content, ensure_ascii=False, indent=2, default=json_default) + "\n"
    )
    descriptor, temporary_path = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def json_default(value: object) -> object:
    """Serialize declared records without inventing absent optional persisted fields."""
    if isinstance(value, BaseModel):
        return value.model_dump(exclude_unset=True)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")
