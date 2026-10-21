"""Shared command line for the AI Audiobook Generator plugin."""

from pathlib import Path

import typer
from typer._completion_shared import get_completion_script

from audiobooks import adaptation, preprocessing, rendering
from audiobooks.assembly import assemble
from audiobooks.corpus import audit_corpus
from audiobooks.delivery import encode_m4b, export_m4b
from audiobooks.workspaces import REPOSITORY_ROOT

app = typer.Typer(
    name="audiobooks",
    help="Prepare, adapt, render, and deliver reviewed AI audiobooks.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
delivery = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)
app.add_typer(preprocessing.app, name="preprocess", help="Inspect and admit source editions.")
app.add_typer(adaptation.app, name="adapt", help="Direct and accept faithful speech adaptations.")
app.add_typer(rendering.app, name="render", help="Plan, synthesize, and verify Chatterbox audio.")
app.add_typer(delivery, name="delivery", help="Assemble, encode, and export chaptered audiobooks.")
preprocessing.app.command("audit-corpus")(audit_corpus)
delivery.command("assemble")(assemble)


@app.command("runtime-root")
def runtime_root() -> None:
    """Print the absolute root of bundled voices, workspace contract, and agent roles."""
    typer.echo(REPOSITORY_ROOT)


@delivery.command()
def encode(
    assembly_directory: Path, output: Path, bitrate: str = "96k", gain_db: float = 0.0
) -> None:
    """Encode and verify a chaptered AAC/MP4 M4B from lossless assembly."""
    manifest = encode_m4b(assembly_directory, output, bitrate=bitrate, gain_db=gain_db)
    typer.echo(f"verified {len(manifest.chapters)} chapters; {manifest.output_hash}")


@delivery.command("export")
def export(delivery: Path, variant: str | None = None, replace_hash: str | None = None) -> None:
    """Copy a verified M4B into the configured finished library."""
    typer.echo(export_m4b(delivery, variant=variant, replace_hash=replace_hash))


@app.command()
def completion(shell: str = typer.Argument(help="Shell type: bash, zsh, or fish.")) -> None:
    """Print shell completion without relying on parent-shell detection."""
    if shell not in {"bash", "zsh", "fish"}:
        typer.echo(f"Shell '{shell}' is not supported. Choose bash, zsh, or fish.", err=True)
        raise typer.Exit(code=2)
    typer.echo(
        get_completion_script(
            prog_name="audiobooks",
            complete_var="_AUDIOBOOKS_COMPLETE",
            shell=shell,
        )
    )
