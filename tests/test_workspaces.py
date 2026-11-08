"""Real subprocesses exercise environment and filesystem path boundaries."""

import os
import subprocess
import sys
from pathlib import Path


def test_relative_work_paths_reject_parent_and_symlink_escapes(tmp_path: Path) -> None:
    root = tmp_path / "work"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)
    for path in ("../outside", "escape/book"):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; from audiobooks.workspaces import work_path; work_path(Path(__import__('sys').argv[1]))",
                path,
            ],
            env={**os.environ, "WORKSPACE_DIR": str(root)},
            cwd=outside,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "escapes WORKSPACE_DIR" in result.stderr
