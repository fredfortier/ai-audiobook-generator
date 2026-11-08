"""Exercise installed command routing and shell callbacks beyond Python's type boundary."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_epub_sections import navigation_entry, write_epub


def invoke(
    directory: Path, *arguments: str, environment: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(Path(sys.executable).with_name("audiobooks")), *arguments],
        cwd=directory,
        env={**os.environ, **(environment or {})},
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.parametrize(
    ("shell", "marker"),
    [("bash", "complete -o"), ("zsh", "compdef"), ("fish", "complete --command")],
)
def test_completion_binds_installed_command_and_resolves_nested_subcommands(
    tmp_path: Path, shell: str, marker: str
) -> None:
    generated = invoke(tmp_path, "completion", shell)
    assert generated.returncode == 0, generated.stderr
    assert marker in generated.stdout
    assert "_AUDIOBOOKS_COMPLETE=complete_" + shell in generated.stdout
    assert " audiobooks" in generated.stdout
    completed = invoke(
        tmp_path,
        environment={
            "_AUDIOBOOKS_COMPLETE": "complete_" + shell,
            "COMP_WORDS": "audiobooks preprocess sel",
            "COMP_CWORD": "2",
            "_TYPER_COMPLETE_ARGS": "audiobooks preprocess sel",
            "_TYPER_COMPLETE_FISH_ACTION": "get-args",
        },
    )
    assert completed.returncode == 0, completed.stderr
    assert "select-sections" in completed.stdout
    assert "inspect" not in completed.stdout


def test_unsupported_completion_shell_fails_without_emitting_a_script(tmp_path: Path) -> None:
    result = invoke(tmp_path, "completion", "tcsh")
    assert result.returncode == 2
    assert "not supported" in result.stderr
    assert not result.stdout


@pytest.mark.parametrize("missing_fragment", [False, True])
def test_preprocess_cli_preserves_reports_and_propagates_blocked_admission(
    tmp_path: Path, missing_fragment: bool
) -> None:
    book = tmp_path / "book.epub"
    write_epub(
        book,
        body='<section id="one"><h1>One</h1></section><section id="two"><h1>Two</h1></section>',
        nav_entries=navigation_entry("One", "absent-one" if missing_fragment else "one")
        + navigation_entry("Two", "absent-two" if missing_fragment else "two"),
    )
    inventory = invoke(tmp_path, "preprocess", "inspect", str(book))
    assert inventory.returncode == 0, inventory.stderr
    assert [node["raw_target"] for node in json.loads(inventory.stdout)["navigation"]] == [
        "book.xhtml#absent-one" if missing_fragment else "book.xhtml#one",
        "book.xhtml#absent-two" if missing_fragment else "book.xhtml#two",
    ]
    report = tmp_path / "selection.json"
    selected = invoke(tmp_path, "preprocess", "select-sections", str(book), "--output", str(report))
    assert selected.returncode == (2 if missing_fragment else 0), selected.stderr
    assert json.loads(report.read_text())["status"] == ("blocked" if missing_fragment else "ready")
    report.write_text("reviewed evidence must survive")
    overwrite = invoke(
        tmp_path, "preprocess", "select-sections", str(book), "--output", str(report)
    )
    assert overwrite.returncode != 0
    assert "refusing to replace" in overwrite.stderr
    assert report.read_text() == "reviewed evidence must survive"


def test_runtime_resources_and_relative_preparation_paths_survive_external_callers(
    tmp_path: Path,
) -> None:
    from audiobooks.files import write_atomic
    from audiobooks.source_units import admit, identity
    from tests.test_acting_score import acting_score_fixture
    from tests.test_section_contract import migrated_plotinus

    runtime = invoke(tmp_path, "runtime-root")
    assert runtime.returncode == 0, runtime.stderr
    resource_root = Path(runtime.stdout.strip())
    assert (resource_root / "assets/workspace-contract.md").is_file()
    assert (resource_root / "skills/adapt-text/references/worker-procedure.md").is_file()
    prepared = migrated_plotinus(tmp_path)
    manifest, units = admit(prepared)
    _, template, _ = acting_score_fixture()
    brief = template.model_copy(
        update={
            "prepared_source_hash": identity(manifest),
            "survey_unit_ids": [unit.id for unit in units],
            "section_baselines": {section: None for section in manifest.section_ids},
            "section_dependencies": {section: [] for section in manifest.section_ids},
        }
    )
    write_atomic(tmp_path / "brief.json", brief.model_dump())
    caller = tmp_path / "caller"
    caller.mkdir()
    result = invoke(
        caller,
        "adapt",
        "init",
        "prepared",
        "brief.json",
        "adaptation",
        environment={"WORKSPACE_DIR": str(tmp_path)},
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "adaptation/manifest.json").is_file()
    assert not (caller / "adaptation").exists()

    revision = invoke(
        caller,
        "adapt",
        "revise",
        "adaptation",
        "prepared",
        "brief.json",
        "revision",
        environment={"WORKSPACE_DIR": str(tmp_path)},
    )
    assert revision.returncode == 0, revision.stderr
    assert (tmp_path / "revision/manifest.json").is_file()
    assert not (caller / "revision").exists()
