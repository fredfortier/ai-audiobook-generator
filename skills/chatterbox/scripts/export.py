"""Export a verified M4B using the configured library naming convention."""

from pathlib import Path

import typer

from audiobooks.delivery import export_m4b


def main(delivery: Path, variant: str | None = None, replace_hash: str | None = None) -> None:
    typer.echo(export_m4b(delivery, variant=variant, replace_hash=replace_hash))


if __name__ == "__main__":
    typer.run(main)
