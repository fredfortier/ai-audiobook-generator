# Audiobook project workspace

Read the persistent work root from `WORKSPACE_DIR`. If unset or empty, the runtime uses
`~/Audiobooks/work/`. Keep generated work outside the plugin cache; reinstalling a plugin must
not remove or change a book project. Relative work paths resolve below that root.

Keep one short book directory with `prepared/`, `adaptation/`, `render/`, `assembly/`, and
`delivery/`. Use descriptive children only when distinct attempts must coexist.

Before source preparation, create and read `<book>/WORKPAD.md`. Use a title followed by exactly
these two second-level sections:

- `Blueprint`: source and edition, narration scope and exclusions, intended voice/performance,
  delivery, and completion boundaries.
- `Material record`: dated source peculiarities, consequential decisions and repairs, and
  requested changes with their consequences and evidence paths.

Update the blueprint and append a material entry when an authorized change alters the contract.
Keep routine progress, commands, hashes and per-segment results in stage records instead.
Do not advance with a missing or materially stale workpad.

Resolve bundled voices relative to `audiobooks runtime-root`. The default narrator binding is
`assets/voices/enoch.wav`. Read `EXPORT_DIR` for the finished-library root; it has no fallback.
The chatterbox skill owns export naming and verification. A project may explicitly retain its
verified delivery locally when its governing context requires another native delivery contract.
