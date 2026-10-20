"""Encode and verify a chaptered AAC/MP4 M4B from lossless assembly."""

from pathlib import Path

import typer

from audiobooks.delivery import encode_m4b


def main(
    assembly_directory: Path, output: Path, bitrate: str = "96k", gain_db: float = 0.0
) -> None:
    manifest = encode_m4b(assembly_directory, output, bitrate=bitrate, gain_db=gain_db)
    typer.echo(f"verified {len(manifest['chapters'])} chapters; {manifest['output_hash']}")


if __name__ == "__main__":
    typer.run(main)
