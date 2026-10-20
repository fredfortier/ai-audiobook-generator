---
name: preprocess-text
description: Prepare HTML or EPUB sources as traceable, paragraph-preserving Markdown bundles for audiobook adaptation. Use before adapt-text or when a raw source has uncertain reading order or conversion quality. Does not rewrite prose for speech, assign voices, or synthesize audio.
---

# Preprocess text

Produce an admitted source bundle that `adapt-text` can process without scraping, EPUB parsing, or guessing reading order. Prefer **Pandoc Markdown**, with stable source-unit fences and a provenance index. Preserve wording at this stage; speech normalization and performance cues belong to adaptation.

Put generated work under `$WORKSPACE_DIR/<book-name>/prepared/`. If `WORKSPACE_DIR` is unset or empty, use this repository's `.workspace/`. The repository runtime resolves relative work paths below that directory.

Before preparation, create or read `$WORKSPACE_DIR/<book-name>/WORKPAD.md` under the repository contract. Establish its `Blueprint` from the admitted source and requested audiobook scope. Record material reading-order, encoding, structure, edition or provenance peculiarities and every consequential preparation decision; omit routine conversion notes.

## Tools and admission

Use the repository's locked **Pandoc + Panflute** for document conversion and writing, **EbookLib** for EPUB spine/resources, and **lxml** for HTML/XHTML structure and source locations. Dependencies are in [pyproject.toml](../../pyproject.toml). Run Python through `uv run --locked` from the repository root; discover the Pandoc executable with `pypandoc.get_pandoc_path()`. Do not install a second conversion stack. [Pandoc's reader/writer model](https://pandoc.org/MANUAL.html#description) fits these born-digital inputs; its conversion can be lossy, so successful conversion alone is not admission evidence.

Accept accessible, text-bearing HTML or EPUB in English, with an identifiable edition, readable paragraphs, and recoverable order. A chapter excerpt is sufficient when its start/end are explicit. Do not require complete-book metadata for an excerpt. Other languages need an explicit downstream engine decision because this workflow targets original English Chatterbox.

For scans/image-only books, broken encoding, unresolved columns, missing body sections, or essential tables/formulas/illustrations without a faithful textual representation, stop admission of the affected scope and report the concrete obstacle. Obtain an OCR or transcription upstream; do not guess or silently drop meaningful content. An independently complete unaffected chapter may be admitted as an explicitly scoped excerpt.

## Preparation procedure

1. **Freeze the witness.** Save the exact HTML response or EPUB bytes under `original/`. Record source URL/path, SHA-256, edition/title/language when available, retrieval time for URLs, requested scope, and tool versions. Follow only resources belonging to the requested work. Preserve the source even when it contains material excluded from narration.
2. **Establish reading order and section evidence.** For EPUB traverse [spine entries](https://www.w3.org/TR/epub-33/#sec-spine-elem), resolving item IDs with EbookLib; do not iterate ZIP filenames. Account for non-linear resources separately. Independently inventory EPUB 3 NAV and EPUB 2 NCX nodes, preserving hierarchy, raw targets, resolution failures and source position. Run `inspect_epub.py` for the lossless typed inventory and `select_epub_sections.py` for the conservative selection report. Standard navigation is primary; material order/hierarchy/label disagreement, unrelated boundaries at one position, or multiple broken fragments collapsing to one resource start blocks admission. When navigation is absent or demonstrably deficient, structural fallback selects only explicit section semantics or a sectioning element corroborated by an authored heading/accessibility name. Generic headings, page markers, stable names and Calibre candidates remain evidence unless independently corroborated. For HTML inspect the main reading stream with lxml, distinguishing navigation and print furniture. Inspect genuine section starts and ends against the original. Paragraph-styled titles can be real headings; heading-styled title-page credits are not chapters.
3. **Index before conversion.** Assign ordered IDs `u000001`, `u000002`, … to text-bearing units: headings, paragraphs, verse stanzas, and list items. Record resource href + DOM locator/fragment, original text, section ID, kind, and any original print-page labels. Include paratext in the inventory. Map every selected DOM boundary to its reviewed first unit. Retain an equivalent visible content heading once; if none exists, use `project_section_titles` with reviewed `SectionProjection` records to insert the authored navigation label as one provenance-backed heading unit at the boundary. Never infer this DOM-to-unit mapping from filenames. Keep embedded notes/citation calls distinguishable from body text; store note-call spans in the unit index when removing HTML would otherwise erase that distinction. Non-text furniture can be recorded as excluded resources without empty text units.
4. **Convert structurally.** Convert bounded DOM units through Pandoc's HTML reader; use Panflute to wrap each in a flat `.source` Div and write Markdown with `markdown_strict+fenced_divs+yaml_metadata_block`, ATX headings and `--wrap=none`. Put metadata in the bundle manifest, not spoken text. Preserve paragraph/stanza boundaries, quotations, meaningful emphasis, list labels and digits. Resolve HTML entities and formatting whitespace; join demonstrable soft wraps and page-continuation fragments. Record any join with all original locators. Do not modernize spelling, repair uncertain OCR, expand numbers, remove textual notes, or choose delivery.
5. **Classify source roles.** Mark units `body`, `paratext`, or `unknown` from source evidence. Title pages, contents, publisher matter, translator/editor introductions, notes, indexes, and platform notices are paratext even when substantial. `adapt-text` excludes them by default. Preserve embedded quotations/verse and genuine divisions of the work as body. Classification is a structural preparation decision, not permission to delete prose. Unknown roles remain explicit for adaptation to resolve; unknown reading order blocks admission.
6. **Compare and admit.** Parse the prepared Markdown back with Pandoc. Reconcile every inventoried unit once in order, compare its projected text with the original allowing only recorded structural/whitespace changes, and inspect section boundaries plus every conversion warning, join, unsupported construct, and uncertain location. Check that no sentence tail was lost when removing a link or note element. Record coverage counts, checks and unresolved issues. Mark the bundle admitted only when no issue prevents faithful adaptation of its declared scope.

Do not rely on an HTML-to-Markdown whole-document conversion to preserve source IDs, pages or EPUB order. The unit index provides those relationships. Do not add book-specific Plotinus rules or a mandatory second extractor; compare another source/tool only when a concrete extraction defect warrants it.

## Bundle contract: version two

```text
prepared/
  original/           # Retained raw witness
  prepared.md         # Canonical, unadapted source units
  units.jsonl         # Ordered provenance/index records
  sections.jsonl      # Explicit ordered section decisions and evidence
  manifest.json       # Version, hashes, source identity, scope, checks, admission
```

Each Markdown source unit has this shape:

```markdown
::: {#u000001 .source kind="paragraph" role="body" section="sec0001"}
The source paragraph, including its original 2 examples.
:::
```

Allow `kind="heading|paragraph|verse|list_item"` and `role="body|paratext|unknown"`; these denote alternatives, not literal combined values. A heading unit contains its Markdown heading. Paragraphs contain one paragraph; stanzas preserve line breaks; list items retain their printed label in text. Use explicit line-break nodes for verse so this dialect need not support a separate line-block extension. No nested source Divs, speech cues, invented chapter titles, or voice/engine parameters.

`units.jsonl` is a derived index, not a competing manuscript. Each record has `id`, `ordinal`, `section_id`, `kind`, `role`, `source_locators`, `source_text`, `prepared_text`, `print_pages` (possibly empty), `note_call_spans` (possibly empty), and `preparation_changes` (possibly empty). Offsets are half-open Unicode character offsets in `prepared_text`, the deterministic projection of that source Div. Keep note prose in separate indexed paratext units where structurally possible. Do not duplicate inline note text into both a body and a note unit.

Each `sections.jsonl` record has a contiguous ordinal, stable section ID, optional parent, level, role, navigation source, raw title, title-unit ID, raw target, exact start-unit ID, delivery-chapter decision, evidence and issues. Every evidence entry retains source kind/location, raw/resolved values, decision and reason. Records cover the unit spine contiguously in manifest order. Every delivery section starts at its authored or provenance-backed heading title unit; that unit participates in ordinary adaptation and normalization. Arbitrary headings and excluded paratext are not delivery chapters.

The manifest has `prepared_text_version: 2`, `admission: "ready"` or `"blocked"`, source identity/scope, ordered section IDs, original-file hashes, hashes of `prepared.md`, `units.jsonl` and `sections.jsonl`, tool versions, and a concise `checks`/`issues` record. Page labels are provenance, not claims that an ebook has print pagination. Role-unknown units can be admitted if their text and position are intact and the uncertainty is identified. Version one lacks the explicit section contract and new adaptation initialization rejects it with a migration diagnostic; use `upgrade_prepared.py` only with reviewed decisions, never inferred defaults.

Retain the frozen bundle for the adaptation run. Corrections produce new hashes and invalidate affected adaptation inputs; do not rewrite an admitted source underneath active workers. `adapt-text init` checks version two, admission, all three hashes, section/title/start invariants and index/Markdown agreement before dispatch. It accepts this bundle, not an arbitrary converted Markdown file.

## Handoff

Return the bundle path, admitted scope, section/unit counts, and any issues requiring interpretation. Report main-text versus paratext candidates separately without promising perfect automatic classification. Do not perform speech normalization or audio generation here. For the downstream contract and page/batch rules, read [adapt-text](../adapt-text/SKILL.md).

Use the installed libraries to prepare the bundle and verify its real extraction boundaries. Run `adapt-text` admission checks before handing it off.
