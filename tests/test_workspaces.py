from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from audiobooks.workspaces import REPOSITORY_ROOT, work_path, workspace_dir


class WorkspaceTest(unittest.TestCase):
    def test_unset_and_empty_environment_use_repository_default(self):
        for value in (None, ""):
            environment = {} if value is None else {"WORKSPACE_DIR": value}
            with self.subTest(value=value), patch.dict(os.environ, environment, clear=True):
                self.assertEqual(workspace_dir(), (REPOSITORY_ROOT / ".workspace").resolve())

    def test_relative_work_path_uses_configured_root(self):
        with (
            TemporaryDirectory() as directory,
            patch.dict(os.environ, {"WORKSPACE_DIR": directory}, clear=True),
        ):
            self.assertEqual(
                work_path(Path("plotinus/render/enoch")),
                Path(directory).resolve() / "plotinus" / "render" / "enoch",
            )

    def test_absolute_work_path_is_unchanged(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "plotinus" / "render" / "enoch"
            self.assertEqual(work_path(path), path.resolve())

    def test_relative_work_path_cannot_escape_configured_root(self):
        with (
            TemporaryDirectory() as directory,
            patch.dict(os.environ, {"WORKSPACE_DIR": directory}, clear=True),
        ):
            with self.assertRaisesRegex(ValueError, "escapes WORKSPACE_DIR"):
                work_path(Path("../outside"))


if __name__ == "__main__":
    unittest.main()
