"""Create a version-two prepared bundle from reviewed section decisions."""
from __future__ import annotations

import json
from pathlib import Path
import shutil

from pydantic import TypeAdapter
import typer

from audiobooks.source_units import Section, admit, sha256


def main(version_one: Path, decisions: Path, output: Path) -> None:
    """Freeze explicit section decisions without guessing them from version one."""
    manifest, _ = admit(version_one, required_version=1)
    if output.exists():
        raise ValueError("output bundle already exists")
    section_records = TypeAdapter(list[Section]).validate_json(decisions.read_text())
    if [record.section_id for record in section_records] != manifest["section_ids"]:
        raise ValueError("decision records must cover the version-one section spine in order")
    shutil.copytree(version_one, output)
    section_path = output / "sections.jsonl"
    section_path.write_text("".join(record.model_dump_json() + "\n" for record in section_records))
    revised = {
        **manifest,
        "prepared_text_version": 2,
        "hashes": {**manifest["hashes"], "sections.jsonl": sha256(section_path)},
        "checks": [*manifest.get("checks", []),
                   "Reviewed explicit sections cover every prepared unit contiguously and bind delivery titles."],
    }
    (output / "manifest.json").write_text(json.dumps(revised, ensure_ascii=False, indent=2) + "\n")
    admit(output, required_version=2)
    typer.echo(f"{len(section_records)} reviewed sections frozen as prepared version two")


if __name__ == "__main__":
    typer.run(main)
