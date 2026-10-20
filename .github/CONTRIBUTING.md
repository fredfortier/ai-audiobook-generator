# Contributing

Read [AGENTS.md](../AGENTS.md). Keep changes focused and preserve source wording, admitted
provenance, reviewed direction, generation identities, and delivery verification.

Run all four checks from the repository root:

```sh
uv sync --locked
uv run python -m pytest -q
uv run basedpyright src tests
uv run ruff check .
uv run black --check .
```

Every test must identify a concrete application failure it can detect beyond declared types.
Follow the [test audit and admission criteria](../tests/README.md); nominal smoke checks,
third-party library checks, and redundant model-type assertions are not accepted.

Strict typing must pass with zero errors. Keep strictness enabled and use concrete application
contracts. An inline exception is permitted only at an external-library boundary with the
diagnostic, installed-source evidence, and justification recorded in
[typing-boundaries.md](../docs/typing-boundaries.md).

For bugs, include the command, revision, OS/Python versions, failure output, and the smallest
input you have permission to share. For changes at a production boundary, include the relevant
source-coverage, recovery, or audio evidence. Passing structural tests does not establish
interpretive or listening quality.

Original code and skill prose are MIT-licensed. The bundled Enoch recording has its own
CC BY 4.0 terms under `assets/voices/`. Preserve third-party notices and source-edition terms.
