"""Emit the lossless EPUB package/navigation inventory as JSON."""

from pathlib import Path

import typer

from audiobooks.epub_structure import inventory_epub


def main(epub: Path, output: Path | None = None) -> None:
    inventory = inventory_epub(epub)
    rendered = inventory.model_dump_json(indent=2)
    if output is None:
        typer.echo(rendered)
    else:
        if output.exists():
            raise ValueError("refusing to replace existing inventory")
        output.write_text(rendered + "\n")
        typer.echo(
            f"wrote {len(inventory.spine)} spine items and {len(inventory.navigation)} navigation nodes"
        )


if __name__ == "__main__":
    typer.run(main)
