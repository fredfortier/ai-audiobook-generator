# Development Contract

## 0) Precedence

* `NOTE:` comments are authoritative: obey them verbatim and do not remove them.
* `TODO:` comments are user-authored requirements: implement the gap, remove the line, and
  never create a replacement `TODO:`.

## 1) Audit And Design

Before editing, read the target, immediate callers, tests, and relevant `references/`. Use `tree`
to orient and `rg` plus the appropriate package-manager commands to find canonical prior art.

Follow this local discipline first:

* Identify deterministic logic before touching skill surface.
* Skills runtime surface (`SKILL.md`, `references/`) is for the agent AT RUNTIME. Not regular documentation. Use  `$skill-writer` valid still construction techniques. 
* Prefer deletion, reuse, or extraction from repeated code. Keep the write set and API surface
  minimal; every new line must improve correctness, clarity, or measurable performance.
* Use library facilities directly. Add a helper only to enforce a domain invariant or collapse a
  protocol repeated in at least two places.
* Do not add speculative configuration, factories, compatibility layers, or future-proofing.
* Keep a functional core and imperative shell; CLI parsing, domain logic, and I/O are separate.

## 2) Python Contract

Use `$python-development`.

* Python >= 3.12; strictly type every public function.
* Use Pydantic v2 models for runtime structures, not ad-hoc dictionaries or dataclasses.
* Use Typer for CLIs, Loguru configured once for logging, and `pathlib.Path` for paths.
* Prefer Unicode output. Black owns formatting at 100 columns; Pyright owns strict typing.

### Layout

Keep pytest configuration in `pyproject.toml` with the canonical layout, and add only documented uv fields.

Before finalizing, run:

* `uv run python -m pytest -q`
* `uv run basedpyright src tests`
* `uv run ruff check .`
* `uv run black --check .`

Do not claim completion without these guards or an explicit reason they could not run. Separate
environment/import failures from patch regressions, and do not substitute partial checks without
user approval.

### Hard Bans

Never use `cast(...)`, `getattr(...)`, `setattr(...)`, `hasattr(...)`, or `# type: ignore`.
Ruff rules `B009` and `B010` enforce the dynamic-attribute subset.

For library or typing errors: reproduce locally; inspect installed source, stubs, signatures, and
official docs; apply the canonical idiom; then request approval if a vendor defect still requires
the compatibility protocol. Do not bypass the API dynamically.
