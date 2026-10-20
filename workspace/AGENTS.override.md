# Project instructions

## Work directories

Read the shared work directory from `WORKSPACE_DIR`. If it is unset or empty, use `.workspace`
in this repository.

Keep each book's generated and intermediate files under one directory:

```text
$WORKSPACE_DIR/<book-name>/
  prepared/
  adaptation/
  render/
  assembly/
  delivery/
```

Use the book's short, familiar name for `<book-name>`, such as `plotinus`. The five stage names
above are canonical. Add a descriptive child name only when multiple attempts at one stage must
coexist, for example `render/enoch/`. Do not use `books/`; it is ignored legacy data. Keep current
book inputs, intermediate files, records, and deliveries in the work directory.

Repository assets belong under `assets/`. The default narrator is Enoch at
`assets/voices/enoch.wav`; voice registries use that repository-relative path explicitly.

Commands may use absolute work paths. Relative work paths are resolved below `WORKSPACE_DIR` by
the project runtime.

Read the finished-library directory from `EXPORT_DIR`. Final export naming and verification belong
to [`skills/chatterbox/SKILL.md`](skills/chatterbox/SKILL.md).

## Project workpad

Every audiobook project must have `$WORKSPACE_DIR/<book-name>/WORKPAD.md`. Create and read it before
project work, and update it whenever a material fact or decision changes. Use a title followed by
exactly these two second-level sections:

- `Blueprint`: the stable project contract—source and edition, narration scope and exclusions,
  intended delivery and voice, and completion boundaries that later stages must preserve.
- `Material record`: dated source peculiarities or surprises, impactful decisions and reasons,
  material repairs, and user-requested changes or revisions with their consequences and evidence
  paths when available.

A fact is material when it can change source interpretation, narrated content, voice or
performance, regeneration, delivery, export, or a later decision. When an authorized change alters
the blueprint, update `Blueprint` and add a dated `Material record` entry instead of erasing the
change history.

Do not use `WORKPAD.md` for routine status, task lists, commands, logs, per-segment results, or
machine-owned hashes. A project must not advance to another stage or complete while its workpad is
missing or materially stale.
