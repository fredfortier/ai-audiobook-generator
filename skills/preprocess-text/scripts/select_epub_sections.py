"""Emit conservative EPUB section decisions for human review."""

from pathlib import Path

import typer

from audiobooks.epub_sections import select_sections
from audiobooks.epub_structure import inventory_epub


def main(epub: Path, output: Path | None = None) -> None:
    inventory = inventory_epub(epub)
    selection = select_sections(inventory, epub_path=epub)
    rendered = selection.model_dump_json(indent=2)
    if output is None:
        typer.echo(rendered)
    else:
        if output.exists():
            raise ValueError("refusing to replace existing section report")
        output.write_text(rendered + "\n")
        typer.echo(f"{selection.status}: {len(selection.boundaries)} section boundaries")
    if selection.status == "blocked":
        raise typer.Exit(code=2)


if __name__ == "__main__":
    typer.run(main)
