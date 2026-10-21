# Canonical original Chatterbox scripts

Use the shared `audiobooks.script_contract` codec for both creation and parsing. Its dialect is `markdown_strict+fenced_divs+yaml_metadata_block`; formatting projects to words, never spoken syntax. Canonical text uses single spaces within lines and explicit verse line breaks.

Front matter contains `adapt_text_version: 1`, `title`, `engine: chatterbox-original`, `language: en`, `voices` and six numeric `defaults`. Every chapter repeats the same registry/defaults. Manifest order governs script order.

```markdown
---
adapt_text_version: 1
title: Example
engine: chatterbox-original
language: en
voices:
  narrator: assets/voices/enoch.wav
defaults:
  exaggeration: 0.5
  cfg_weight: 0.5
  temperature: 0.8
  repetition_penalty: 1.2
  min_p: 0.05
  top_p: 1.0
---

::: {#s000001 .speech voice="narrator"}
# A genuine heading
:::

::: {#s000002 .speech voice="narrator" exaggeration="0.60" temperature="0.66"}
A complete spoken paragraph.
:::
```

All audible content is inside flat `.speech` Divs with unique stable `sNNNNNN` IDs and explicit registered `voice`. Every block has an authoritative resolved vector containing all six Chatterbox controls because export accepts only delivery beats with complete approved vectors. Required front-matter defaults plus direct numeric block overrides are serialization factorization, not optional directing; together they resolve all six values before rendering. Named preset, emotion and rhetoric labels are never runtime authority. A block contains paragraphs or exactly one heading. Controls apply only to that block; nothing leaks forward. A voice change starts another block at an intelligible boundary. Provenance records map blocks to source IDs and normalized spans. Export may trim boundary whitespace from each beat; its words and punctuation must remain exactly those of the indexed span.

Reject duplicate keys, unknown controls, nonfinite values, unregistered voices and prose outside speech blocks. Do not place raw HTML, links, images, footnotes, code, nested scopes or attributed inline spans in speech. Literal punctuation is built as text nodes, allowing asterisks, brackets and hashes to round-trip without becoming markup.

Authoring bounds: exaggeration .3–1.1; CFG .3–.6; temperature .5–.9; repetition penalty 1–2; min-p 0–1; top-p greater than zero and at most one. These are narration policy, not a promise of stable audio for every combination. No `speed`, emotion/profile tags, deltas, timed pauses, seeds, phoneme tags or per-block raw reference paths. Put runtime-root-relative voice paths in the registry, and select their IDs. Use `assets/voices/enoch.wav` for the default narrator.
