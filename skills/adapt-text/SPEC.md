# Faithful audiobook adaptation and rendering

## Completion theorem and burden of proof

Given an admitted English source, the delivered script and audiobook must preserve the author's main text, quotations, genuine headings and paragraph lineage under justified speech-surface edits; exclude all paratext by default; account for every indexed source unit exactly once; and use explicit voices and six direct original Chatterbox controls. The Gutenberg essay must be completely rendered with calibrated acting, punctuation and pauses, and its completed audio must pass source-completion, technical and sampled perceptual review. A parsed script or a successful synthesis call cannot prove this theorem.

Proof is required at each boundary: retained witness → admitted source units → reviewed normalization and beats → canonical scripts → generated segments → assembled and reviewed audio. An unresolved reading, missing unit, stale input, unsupported control, unexplained omission, repetition, truncation, glitch or unsuitable pacing prevents completion. Specification reasoning and evidence belong here; runtime skills and references contain only operational guidance. Verification uses ephemeral real fixtures and benchmarks, without mocks; permanent tests require a separate logical justification. Git records large logical changes with multiline commit messages.

Current evidence proves the shared text contract, bounded batch/fragment workflow, revision/recovery boundaries, exercised HTML/EPUB admission, independent runtime forward use and complete delegated Gutenberg acceptance/export. Current book evidence belongs below `$WORKSPACE_DIR/<book-name>/`; the Plotinus delivery record is `$WORKSPACE_DIR/plotinus/delivery/enoch-delivery.json`. It binds the Enoch asset, source coverage, render plan, lossless assembly, encoded file, loudness, navigation, and the limits of automated checks.

## Architecture and responsibilities

`preprocess-text` owns raw HTML/EPUB reading order, provenance and admission. `adapt-text` owns source-exact acting direction followed by paragraph-preserving normalization and mapping, ending in scripts, complete coverage and a rendering handoff. `chatterbox` owns physical segmentation, voice conditioning, calibration, synthesis, assembly and audio-quality review. Audio publication, voice acquisition and training are outside this request.

Use the root [locked project](../../pyproject.toml) and standard src-layout `audiobooks` package. [script_contract](../../src/audiobooks/script_contract.py) owns script records and the single Pandoc/Panflute codec; [source_units](../../src/audiobooks/source_units.py) owns prepared admission and partitioning; [adaptation](../../src/audiobooks/adaptation.py) owns brief/result/review records, packets, acceptance, revisions and export; [sentences](../../src/audiobooks/sentences.py) owns supported English sentence spans. The shared [Typer CLI](../../src/audiobooks/cli.py) registers all command groups through the root project's `audiobooks` entry point. This gives adaptation and rendering one contract without copied codecs, import-path changes, separate adaptation/generation environments or a generic orchestration framework. Records compose ordinary typed values; no service layer or domain inheritance hierarchy is needed.

Run `uv run --locked audiobooks adapt …`; elsewhere use `uv run --project <repository> --locked audiobooks adapt …`. Dependencies and exact resolution belong in [uv.lock](../../uv.lock): Typer for commands, Pydantic for strict records, Pandoc/Panflute for conversion, pypandoc-binary for the executable, EbookLib/lxml for preparation and NLTK for supported English sentence spans. Text intake, codec and CLI help must not load Torch or a synthesis model. uv provisions the shared project; there are no script-local dependencies. Missing English Punkt data is obtained lazily with `nltk.download("punkt_tab", quiet=True, raise_on_error=True)` using NLTK’s native default location. Encoding resolves FFmpeg and ffprobe with `static-ffmpeg`’s executable resolver; users configure neither binary paths nor `NLTK_DATA`. Installed wheels retain the lockfile, narrator recording, workspace contract and optional role instructions. Generated work defaults to `~/Audiobooks/work/`, outside tool and plugin caches.

Domain boundaries reject bad data with informative failures. The agent owns source interpretation, faithful edits, meaningful beats and review; scripts own identity/order checks, spans, serialization, arithmetic and recovery. Passing deterministic checks does not certify meaning or audible quality.

## Literary anthology extension — 2026-10-24

The user requested reusable anthology identification, spoken chapter titles, and optional brief
introductions before production of Working Anthology. **Literary anthology** describes this
editorial selection of works and excerpts; “compilation” describes its assembly but does not
identify the literary form. This extension authorizes explicit editorial framing alongside the
faithful source text. It does not authorize changes to the selected authors' words or program.

Lineage: root commit `c15398f54f7d904e55fb21a202d39f535c2290f2` adds the curatorial scratchpad.
The separate `workspace/working-anthology` repository contains
`72010c2a56b87e52ab14b90f97e300bd950aab21` (settled selection, WORKPAD and production plan) and
`19a6d340a959d0171366c1b1eb8423cf4e1c9f97` (scratchpad). These distinguish editorial listening
labels from original titles and preserve source differences. Production remains subject to the
recorded approval boundary. This development change neither begins production nor requests
introductions for that project.

#### Published examples and adopted convention

Research on 2026-10-24 examined actual published audiobook contents, rather than invented model
titles. These are established commercial examples, not a measured bestseller ranking:

| Source and inspected evidence | Consequence |
| --- | --- |
| Naxos, [Classic Women's Short Stories, NA223812D, booklet pp. 2–3](https://d2fahduf2624mg.cloudfront.net/pre_purchase_docs/BK_NAXO_000265/2020-06-24-05-44-43/bk_naxo_000265.pdf). Entries pair selection titles with their authors; separate CD tracks use opening phrases. The [Audio Publishers Association's 2003 awards record](https://www.audiopub.org/2003-audies-1) identifies this release as the Short Stories/Collections winner. | Adopt selection-level title plus author. Reject CD subdivisions and incipits as the anthology's literary chapter scheme. Award recognition supplies evidence of an established example, not sales volume. |
| Naxos, [Classic Romance, NA443012D, booklet pp. 2–5](https://d2fahduf2624mg.cloudfront.net/pre_purchase_docs/BK_NAXO_000715/2020-06-23-11-04-52/bk_naxo_000715.pdf). Work/excerpt titles precede author credits. Unknown authorship is marked; conventional short literary names and initials occur. The cover credits an introducing narrator separately. | This mixed-form excerpt anthology is the closest structural precedent. Adopt title-first identification, containing-work identification for excerpts, and conventional author names; distinguish narrator from author. Do not copy its inconsistent abbreviations. |
| Naxos, [Favourite Essays: An Anthology, NA493712D, booklet pp. 2–4](https://d2fahduf2624mg.cloudfront.net/pre_purchase_docs/BK_NAXO_000512/2020-06-24-07-38-44/bk_naxo_000512.pdf). Author group headings organize separately titled essays; longer essays have additional incipit tracks. | Preserve author/work association while flattening navigation to independently identifiable delivery chapters. An author group heading alone cannot identify a later isolated chapter. |

The booklets were retrieved and text-extracted in full; their contents establish published
labeling, not the exact words spoken on every recording. The recurring convention is selection
title plus literary author, with source-work titles identifying extracts. Ordering and typography
vary across editions and retailer presentations. The runtime mandates `Title, by Author` as this
project's consistent realization of that convention; it does not claim a universal industry rule
for punctuation or author/title ordering. Requiring the author on **every** chapter and explicit
book/division identification where applicable implements this user's stronger requirement.
Bare thematic labels lose identity; a bare chapter number loses both identity and authorship.

#### Pauses and optional introductions

[Neil Gardner, Ladbroke Audio, “Let's Talk About Secs”](https://ladbrokeaudio.co.uk/lets-talk-about-secs/)
describes two seconds between a chapter heading and the body as usual UK production practice,
while explicitly allowing publisher variation. The primary producer's indexed page text was
available through search; direct retrieval returned 403. It distinguishes that interval from
opening-credit and file-edge silences. Its credit-to-heading interval does **not** describe a
short editorial introduction after a heading, so that different interval is not imported here.

The [2024 Sound Advice guidelines, §6.1.5](https://printdisability.org/wp-content/uploads/2024/10/Sound-Advice-Guidelines-2024-3rd-Edition-N18-PDF.pdf)
require intelligible, context-sensitive phrasing and appropriate pauses; they supply no special
fixed duration for anthology introductions. The [NLS narration specification, 2025, §§3.1.1–2](https://www.loc.gov/nls/who-we-are/guidelines-and-specifications/contract-specifications/narration/)
similarly treats timing as an interpretative skill. Neither establishes an anthology exemption
from ordinary source-responsive narration. Their accessibility-specific rules about including
apparatus do not replace this project's main-text-only default.

Decision: adopt a two-second heading transition as a documented professional default for
ordinary books and anthologies. When a user requests an introduction, apply that same structural
separation on both sides of it. **This extension is a local editorial policy by analogy, not an
externally standardized introduction duration.** One or two sentences is likewise a local
interpretation of the user's “brief,” not a publishing standard. Factual orientation and an
audible editorial voice keep the introduction distinguishable from the source. Listening may
justify a recorded timing departure; no fixed number alone proves a natural transition.

The pause target describes the complete audible interval from the preceding spoken ending to
the following spoken onset. Existing quiet contributes to it. Assembly adds only the missing
native frames after checking those boundaries and preserving breath/decay; adding two seconds
blindly can double the intended separation. Already-longer quiet requires listening and a
recorded departure or an independently justified repair under the rendering contract.

#### Implementation boundary and prose acceptance

Deterministic prior art already supplies the necessary protocol:
[Unit/Section evidence](../../src/audiobooks/source_units.py) retains locators and manual editorial
decisions; [adaptation export](../../src/audiobooks/adaptation.py) requires a delivery title to be
one narrated heading at its explicit start; [assembly](../../src/audiobooks/assembly.py) accepts
reviewed native-frame gaps and permits title-case changes without lexical relabeling.
[Section tests](../../tests/test_section_contract.py) cover title projection and source identity.
No schema, helper, pause tag, metadata bypass, or new deterministic policy is needed.

Editorial framing must therefore exist in a retained compilation witness **before** admission.
Original witnesses remain separate provenance. The new anthology heading is a genuine heading
of that editorial compilation; an introduction remains separately indexed paratext admitted for
speech only by the user's request and exact brief rule. The source text remains unchanged.
Post-export insertion would defeat coverage and title-word checks and is rejected. Existing
introductory paratext is still excluded unless explicitly selected. A redundant source opening
title can be excluded with a scoped record while preserving internal authored headings.

The skill-writer synthesis/authoring route applies because the user requested new behavior.
The minimum shape is the existing reference-backed skill with one flat conditional leaf and
direct entry routes from preparation, adaptation and rendering. No discovery description,
registration, execution shape, provider mechanism, or delegated workflow changes. This is not
donor adaptation, declared doctrine, or an iteration from measured model failures. Research
stopped after the examples and primary timing guidance resolved the decisions; no universal
intro-duration claim remains to justify. Source lineage belongs here, outside runtime.

Formulation record: the runtime agent owes title/author identification for each anthology
chapter, introduction inclusion only upon request, and audible boundary review. The title,
source work/division and author must correspond to that chapter in speech and navigation.
“Literary anthology” uses its ordinary meaning; explicit editorial provenance assigns no new
power to alter source text. Obligations, correspondence and provenance/permission routes all
apply. The positive compilation-unit rule replaces the blanket announcement ban only within
this scope; independent fidelity, default paratext exclusion and frozen-source safeguards stay.
Conditions attach to their acts: a request permits introductions but does not admit all paratext;
two seconds attaches to each complete transition, not to every synthesis block.

Inspection cases: a complete standalone selection has title and author without a spurious book;
a titled extract also identifies its containing work and applicable division; an untitled extract
uses the work/division rather than an invented original title; unknown or disputed authorship
retains its status rather than borrowing a speaker's name. A later chapter by a returning author
still includes that author. Without a request the source follows the heading directly, separated
by the heading pause. With a request, an indexed editorial introduction sits between them with
both joins reviewed. A metadata-only author, an unindexed introduction, a swapped author, or
blind added padding fails the assembled rule. A normal single work retains its authored headings
without per-chapter anthology attribution. These are prose review cases, not executed model
comparisons or acoustic evidence; the new reference has not yet been exercised in production.

Validation on this change: `uv run python -m pytest -q` passed (48 tests and 10 subtests);
`uv run basedpyright src tests` reported zero errors/warnings; `uv run ruff check .` and
`uv run black --check .` passed. The installed skill-creator `quick_validate.py` passed for all
three touched skills; it checks frontmatter, not runtime behavior. Local reference routing and
the assembled contract were inspected separately. No model/audio production was performed.

## Admitted prepared source

The version-two bundle contains retained bytes under `original/`, `prepared.md`, ordered `units.jsonl`, explicit `sections.jsonl` and `manifest.json`. The manifest declares `prepared_text_version: 2`, ready/blocked admission, source/edition/language/scope, ordered section IDs, original-file hashes, manuscript/index/section hashes, tool versions, checks and issues. Each section record retains boundary/title provenance, hierarchy, role, exact start/title units and the delivery-chapter decision. Admission requires accessible text, recoverable reading order, complete declared scope, exact contiguous unit coverage and an authored or provenance-backed normalized title unit for every delivery section. Version one is readable as archived evidence but cannot initialize new adaptation; migration requires reviewed section decisions. Scans, encoding damage, uncertain columns or essential unsupported material return to upstream transcription; do not guess. An independently complete excerpt can be admitted explicitly.

Every unit has stable `uNNNNNN` ID, contiguous ordinal, section, kind (`heading|paragraph|verse|list_item`), role (`body|paratext|unknown`), all original locators, original/projected text, print-page labels, indexed half-open note-call spans and preparation changes. Source Divs are flat `.source` blocks with the same ID/kind/role/section. A genuine heading's level is derived from and checked against its Markdown header; an optional indexed level must agree. Stanzas preserve line breaks; list labels remain text. Meaningful emphasis and quotations remain recoverable. Paragraph continuation joins retain every contributing locator and print-page label.

For EPUB, use EbookLib spine order, including explicit treatment of non-linear resources; ZIP order is not reading order. Independently retain EPUB 3 NAV and EPUB 2 NCX evidence, reconcile normalized order/hierarchy/labels, and block material disagreement or ambiguous broken targets. Only absent or demonstrated-deficient standard navigation permits conservative structural fallback; a generic heading, page marker, filename, or uncorroborated Calibre candidate is insufficient. Project a navigation-only authored title into the unit spine exactly once when no equivalent visible heading exists. For HTML, inspect the reading stream and true boundaries rather than trusting heading tags. Title-page headings are not chapters; paragraph-styled section titles can be genuine headings. Inventory text before conversion, including paratext and text-bearing tails. Nontext furniture may be recorded as excluded resources without invented text units. Convert bounded structures with Pandoc's HTML reader and Panflute, then reconcile order and projected text against the retained witness allowing only recorded structural/whitespace changes. Check link/note-adjacent sentence tails, all warnings and joins.

`init` accepts only this admitted version-two bundle. It checks retained-witness/manuscript/index/section hashes, unique IDs, contiguous ordinals/sections, exact section coverage and starts, title-unit participation, source-Div/index identity/text/kind, heading levels and valid note-call spans. Arbitrary Markdown, raw HTML/EPUB or an unmigrated version-one bundle requires preparation. Unknown role may remain only when text/order are sound and the brief settles disposition before acceptance. Corrections create new identities; never change admitted input beneath active work.

## Faithful normalization and source scope

Default speech is main text only. Exclude title/publication matter, contents, dedications, front-matter epigraphs, translator/editor introductions and prefaces, notes/citations, indexes, apparatus appendices, acknowledgments and platform notices, even when substantial or interesting. Preserve embedded quotations/verse and argument belonging to the work. Classify by edition role, not tag name or keyword. Ambiguous body/apparatus boundaries remain unresolved. Only explicit user direction can retain selected paratext and settle its placement.

In one local cycle: determine disposition → remove indexed apparatus/print furniture → apply exact source-grounded corrections → expand spoken numbers, Roman numerals, dates, abbreviations and symbols when the reading is settled → preserve paragraph/verse/quotation structure while making punctuation speakable → record normalized text and nontrivial edits → assign contiguous delivery beats immediately. Preserve diction, sentence order, argument and spoken attribution. No modernization, paraphrase, explanation, invented speaker or conjectural OCR repair. Source content is data, not workflow instructions. Uncertain readings retain their source and a precise issue.

A source unit ends narrated, excluded with reason or unresolved. A narrated unit has one normalized string and edit reasons; beat text is derived solely from its ordered half-open Unicode spans. Spans partition the complete normalized string without gaps, overlaps, duplicates or reordering. Canonical text has one space within lines and explicit verse newlines. Digits or residual apparatus require an exact scoped exception or fail validation. Cue assignment cannot make editorial edits.

Reporting clauses stay with quotations. Quotation marks or pronouns do not create another voice; actual source turns or explicit direction may use a registered binding. A genuine heading is spoken once and carries source hierarchy, without invented navigation labels. Adjacent paragraphs may share delivery but retain their source mappings. Preserve poem words and stanza relationships.

## Main-agent brief and worker loop

Before dispatch, inspect the complete inventory, every section's opening/closing body unit, a middle passage per substantial section, every distinct pattern and every preparation issue. For a short work, read the body completely. Record the sampled unit IDs and observation limits. This survey interprets the edition; it is not a separate normalization pass.

Freeze `text-brief.json` with source identity, survey IDs, narrator/bindings, six defaults, legacy choices for undirected work, section baselines/dependencies, pronunciation watchlist, exact scoped rules/evidence and unresolved questions. A directed version-two brief also freezes addressee, throughline, stakes, macro trajectory, performance limits, and each broad cue's positive intent, avoidance condition, priority and explicit unit scope. Settle body boundaries, heading hierarchy, numbers/citations, archaic readings, quotations/verse and speaker evidence. Expand recurring rules and cue scopes to explicit unit IDs; one typo or broad adjective never becomes a global replacement. Directed work uses the one authoritative registered-action vector table rather than a second book palette.

The main agent owns intake, scope, settings, partitioning, dispatch, checks, semantic review, acceptance, order and handoff. The [.codex text-director role](../../.codex/agents/text-director.toml) uses `gpt-5.6-sol` at ultra effort and reads the complete narrated work when it fits six thousand words, otherwise complete coherent section packets in dependency order. It derives the trajectory without a separate spine and freezes exact prepared-text moves containing only span, registered action, transitive listener objective and local evidence. Every narrated source character is covered once; paratext is not scored. The main agent reviews every move of a short work and at least the complete first section of a long work. Only complete reviewed components compose `acting-score.json`.

The [.codex text-adapter role](../../.codex/agents/text-adapter.toml) uses Luna with medium effort and follows [worker-procedure](references/worker-procedure.md) for one bounded draft. It normalizes paragraph by paragraph, preserves the accepted score without reclassification, and derives each complete vector from its exact registered action. Split beats may repeat a move ID; a beat may merge adjacent moves only when they share one action and no real turn is erased. Collapsing adjacent duplicate IDs must reproduce the exact source move sequence. The adapter cannot reinterpret actions, select a second performance surface, invent controls, accept, export, change shared input, synthesize or recursively delegate. If declared role selection is unavailable, explicitly supply the same role contract; never silently substitute a model.

| Work unit | Rule |
| --- | --- |
| Work page | Greedily pack whole consecutive units up to six hundred whitespace words; preserve sections; an oversized unit stands alone. |
| Batch | At most ten pages and six thousand owned words within a section; greedily use the largest section-preserving batch within that bound. |
| Oversized paragraph | Dedicated batch when it fits an explicitly established context/output budget; otherwise verified sentence fragments retain parent ID and original character coverage in one sequential worker chain. |
| Context | Previous/next paragraph capped at four hundred words each, section/brief/settings, and accepted continuity capped at three hundred words; mark truncation and never emit context as owned work. |

Freeze the plan and its hash. Repartitioning is an explicit revision, preserving source IDs. Default to one active batch per continuity-dependent section; at most two workers when sections are independently interpretable with shared frozen settings. Fresh packets bound context. Out-of-order independent completion cannot change book order or permit duplicate dispatch.

Packets contain batch/attempt IDs, prepared/plan/configuration/brief hashes, the accepted acting-score hash, applicable move fragments and registered vectors for directed work, section, ordered page/owned-unit IDs and full texts, context-only neighbors, predecessor identity or section start, applicable rules, voices, record version, references and a unique draft path. Results retain those identities and exactly one disposition per owned unit, normalized text/edits, spans, move lineage, actions, voices/vectors, exclusions/issues and concise continuity. Missing or stale input prevents acceptance; unmodeled patterns return precise issues.

The first ordinary batch and each new source form receive complete pilot review. Thereafter review all editorial changes/exclusions, batch entry/exit and a source-fidelity/performance sample; a failed sample expands review over the affected pattern. No unresolved meaning, disposition, ownership or coverage may be accepted. Validate directed vectors against registered actions and legacy vectors against approved choices, not just bounds. Give one targeted repair; after a second failure, resolve the actual issue rather than looping whole-batch rewrites. Only the main agent accepts with a review tied to the exact result.

## Persistence, revisions and complete export

A workspace has frozen `prepared/`, brief, plan, isolated direction tasks/drafts, reviewed score components and `acting-score.json` when directed, adapter `tasks/`/`drafts/`, atomic accepted `work/<batch>.json`, manifest, ordered `script/*.md` and disposition/span coverage. The manifest owns source/scope, exact score identity, script order, defaults and voice registry. Derive section cursors from contiguous accepted batches and overall completeness from full planned coverage; a gap is not authority to dispatch live work twice. Confirm a worker's actual handle before retiring an active attempt. Preserve accepted records during repairs.

Acceptance is interruption-safe and idempotent for the same reviewed result. Export relies on accepted records, not mutable isolated drafts. Frozen fragment boundaries exactly cover the original paragraph; each bounded packet depends on verified predecessor output. Combining requires all fragments in order and produces one normalized paragraph/coverage record, without invented headings. Accepted fragment snapshots retain the complete proof even when temporary drafts are removed.

`revise` creates a new frozen workspace. Reuse requires an unchanged unit contract: source/structure, applicable rules, configuration, baseline, pronunciation instructions and immediate source neighbors. Changed dependencies invalidate interpretation-dependent sections. Workers copy reused reviewed dispositions exactly; they cannot reinterpret them. A local edit reprocesses only affected interpretation and context, preserving unrelated reviewed output. Old global hashes never become current authority merely because output exists.

Export requires complete accepted coverage, rechecks records and emits source-ordered scripts. Split at genuine sections or bounded continuations, never invented chapters. Preserve stable IDs, source heading levels, registry/default consistency, exact score identity and move lineage, per-unit dispositions and normalized spans. Beat emission may trim boundary whitespace only; words and punctuation remain exactly those of its indexed span. Canonical codec round trips must agree. Large books never require the full book/audit in one adapter context.

## Canonical script contract

Use YAML metadata and flat Pandoc `.speech` Divs, not model tags. Pandoc fenced Divs/metadata supply a data-only Markdown contract without a custom directive or expression language. One Panflute codec constructs literal nodes and parses the same typed records. Resolve Pandoc through pypandoc-binary; dialect is `markdown_strict+fenced_divs+yaml_metadata_block`, ATX headers, no smart punctuation, writer `--wrap=none`. Writer-selected fences/quoting are acceptable only when semantics round-trip. No handwritten fence writer, Markdown regex parser or substitute text tokenizer. Native Pandoc `--fail-if-warnings` prevents duplicate YAML metadata from silently becoming an accepted map; real top-level and nested duplicate-key checks fail while current book/candidate round trips remain exact.

Metadata has version one, title, `engine: chatterbox-original`, `language: en`, voice registry and all six defaults. Each block has unique stable `sNNNNNN` ID and explicit voice, with optional numeric overrides; values resolve independently and never leak forward. All audible content is inside speech blocks. Bodies contain paragraphs or one genuine heading, with literal punctuation and formatting projected to words. Reject prose outside blocks, raw HTML, code, images, link destinations, footnotes, nested performance scopes, inline controls, duplicate keys, unknown fields, nonfinite controls and invalid bindings. `builtin` denotes pretrained conditionals; other bindings are repository-relative real audio paths. Repeat frozen registry/defaults in every chapter and order files by manifest.

No executable profile/emotion/rhetoric labels, deltas, speed, seed, raw per-block reference override, SSML, phonemes or timed pauses. A voice/parameter change begins a new block at an intelligible boundary. Structural pauses belong to rendering rather than unsupported adaptation fields.

## Original Chatterbox controls and limits

Target the pinned [original English public API](https://github.com/resemble-ai/chatterbox/blob/5de7a54aa4e5e2baadb0182dde554908b48b85c2/src/chatterbox/tts.py#L208), not Turbo, Nano, multilingual or hosted APIs.

| Control | Upstream default | Narration policy and meaning |
| --- | ---: | --- |
| exaggeration | .5 | .3–1.1; one learned intensity scalar, not separate emotions, pitch or emphasis. |
| cfg_weight | .5 | .25–.6; conditioning/pacing aid, not duration or words per minute. |
| temperature | .8 | .5–.9; sampling variability. |
| repetition_penalty | 1.2 | 1–2; reliability trim. |
| min_p | .05 | 0–1; relative probability filter. |
| top_p | 1 | greater than zero, at most one; nucleus filter. |

Bounds are local authoring policy, not acoustic guarantees; reject rather than clamp. [Upstream guidance](https://github.com/resemble-ai/chatterbox/blob/5de7a54aa4e5e2baadb0182dde554908b48b85c2/README.md#original-chatterbox-tips) starts near .5/.5 and suggests lower CFG near .3 for fast references or larger exaggeration. Higher exaggeration may accelerate speech. CFG zero is outside policy because the inspected original branch/sampling assumptions need a dedicated runtime proof.

`audio_prompt_path` comes only from the voice registry. No prompt after a custom voice can reuse that voice; explicitly restore conditionals, including return to builtin. Reference conditioning uses the first six seconds for speech tokens and first ten for decoder conditioning; these are internal windows, not an exact file-length requirement. Clean representative reference speech and verified bindings are required.

Public generation caps output at one thousand speech tokens. A text-token bound cannot guarantee completed speech. Count candidate segments with the original tokenizer after exact upstream `punc_norm`. Treat two hundred twenty as an initial operating heuristic; select a larger whole-sentence budget when real completion and delivery prove it viable, or reduce it when observed failures require subdivision. Missing tokenizer or voice files prevents a synthesis-ready handoff; no GPT tokenizer fallback. Preview punctuation rewrites: semicolons/colons and ellipses become commas, dashes/quotes change and whitespace collapses. Pass admitted segment text to public `generate` so normalization is applied exactly as upstream, without broad sanitization or private sampling reconstruction. Seed is runtime RNG state, not a generation keyword.

## Acting direction and control provenance

The accepted score uses exactly eight listener-directed actions: `CLARIFY`, `PROBE`, `CONVINCE`,
`WARN`, `INVITE`, `EXALT`, `URGE`, and `RESOLVE`. Rhetoric, punctuation, addressee, stakes, and
neighboring moves supply boundary evidence. Each move carries one action, a transitive listener
objective, and exact local evidence. It carries no parallel mood, Laban, intensity, tempo, palette,
or trap field.

Broad user cues are production constraints with explicit scopes and avoidance conditions. The
director considers them against the exact source; conflicts affecting meaning, fidelity,
intelligibility, or stability remain owner decisions. With no cue, textual action remains
authoritative. A repeated global action or vector does not satisfy a cue merely because its
adjective sounds compatible.

Original Chatterbox exposes exaggeration as one scalar expressive condition and CFG as conditional
guidance; temperature, repetition penalty, min-p, and top-p act on token sampling. The authoritative
registry maps each accepted action directly to one complete six-value candidate vector. The adapter
copies that vector without arithmetic, deltas, boosts, hidden floors, clamps, or a second choice.
The mapping remains an acoustic hypothesis until matched-text listening validates it.

The renderer may replace a proposed vector only through an exact-text calibration record. Final
evidence retains the accepted move IDs, registered action, proposed vector, audition reason, and
realized vector. A global calibration cannot erase distinct action families without matched evidence
for each affected family.

## Rendering and quality obligations

Semantic beats retain author wording and acting. Physical generation subdivisions inherit their complete voice/vector and preserve exact source spans. [NLTK Punkt sentence spans](https://www.nltk.org/api/nltk.tokenize.punkt.html#nltk.tokenize.punkt.PunktSentenceTokenizer.span_tokenize) provide supported English abbreviation/closing-punctuation handling; inspect their decisions for this edition. Pack complete sentences under the original-tokenizer limit. For an oversized sentence, first establish whether a viable larger budget preserves complete delivery; otherwise require a reviewed clause boundary tied to original offsets. Arbitrary word cuts, regex sentence guesses and another tokenizer are insufficient.

The inspected neighboring `laban-tts` implementation, tests and manual/acting runbooks are nonauthoritative failure-mode evidence. Applicable external contracts and the locked upstream implementation take priority. The minimal design keeps editorial normalization, semantic beats and physical generation distinct; one shared codec and one supported sentence detector suffice. Do not build a fallback ladder to conceal a failed boundary.

| Laban implementation evidence | Governing resolution |
| --- | --- |
| `cues.py` estimates with a GPT tokenizer; `synthesize.py` later applies a 220-token input guard and regex/clause/word fallbacks. | Count each exact candidate with original Chatterbox `tokenizer.text_to_tokens(punc_norm(raw))`. 220 is a provisional Laban operating heuristic, not an upstream input maximum; the locked original T3 config declares 2,048 text positions before start/stop padding. Calibrate a conservative budget. Pack supported sentence spans; review exceptional clause cuts as original offsets, preserving all words and punctuation. A detector boundary is a candidate, not permission to detach attribution or verse. |
| `_generate_phrase_audio` copies private T3/S3 generation to observe its 1,000-token sampling ceiling. | Use public `generate`; the locked implementation has a separate 1,000-output-token ceiling and returns only audio. Input-budget compliance cannot certify completion. Verify actual speech, and revise only the implicated segmentation/settings after a diagnosed failure. No private-generator copy or instrumentation patch. |
| `_sanitize_text_for_chatterbox` deletes references and arbitrary brackets; native punctuation cleanup also changes input. | Remove only indexed apparatus during reviewed normalization. Record the native normalized view for token planning and audit, but pass raw approved segment text to `generate`, which normalizes once. Do not globally sanitize content or apply native cleanup twice. |
| Prompt caching and permissive `_choose_voice` can leave the previous custom voice active; conditional setup failures are caught. | Validate every declared binding. Preserve the initial built-in conditioning and restore it explicitly on return to `builtin`; use supported preparation/generation for custom references. Missing references or failed conditioning stop that segment rather than substitute a voice. |
| A monkeypatched Hub downloader selects a workspace cache; model loading follows current repository files. | Use native [Hub cache/revision arguments](https://huggingface.co/docs/huggingface_hub/guides/download) to obtain a pinned snapshot and public `from_local`. Freeze code, model-file and reference hashes. No downloader replacement or implicit model/device changes. |
| OOM handling clears cache and repeats splitting; README claims CPU fallback although the inspected branch does not provide it. | Diagnose actual resource failure. Keep failed attempts separate; an explicit smaller reviewed plan or explicit device change has a new render identity. Do not silently migrate devices, repeatedly apply an unchanged splitter or infer implemented behavior from README prose. |
| `_resume_existing_chunk` trusts existing WAV/sidecar durations and repairs positions; finalization can discover filename order. | Reuse only when frozen segment identity, saved-byte hash and decoded properties agree. Derive ordered coverage and cumulative sample positions from the frozen plan and verified audio; file presence/count, glob order and mutable sidecars are insufficient. Publish a completed segment record atomically after its audio is saved and verified. |
| `audiodub.py` canonicalizes to 48 kHz/16-bit and finalization applies loudnorm, post-gain and a limiter; manual runbooks expose native-channel dynamics and large-RIFF risks. | Preserve native generation rate/channels and lossless samples through assembly; convert only for a declared delivery need. Measure with supported FFmpeg filters, select mastering from actual measurements, and remeasure the encoded delivery. Do not adopt Laban's targets, duplicate resampling, padding, fades or dynamics changes by default. Use a supported large-file container when needed. |
| Manual quality guidance checks ASR, clipped runs, silence, breaths, difficult names, seams and realized navigation times. | Quantitative flags route targeted review; ASR cannot certify classical pronunciation or perceptual polish. Derive navigation from genuine source structure and realized sample times, then independently inspect encoded chapters and audio. Do not invent headings or truncate source titles to a legacy filename limit. |

Repair failed segments rather than assuming every in-range vector works. RNG/seed, voice, parameters, exact source span, model, device and relevant generation configuration belong to each frozen render identity. Quality decisions and attempts belong beside the audio, not in the source script.

The book plan proves complete ordered source coverage; each audio record proves a particular segment generation request. That request binds the exact span/text, complete numeric vector, explicit seed, model/reference hashes, device and runtime. A changed book plan may reuse audio only when the prior plan and inputs remain valid, requests are identical and saved bytes/decoded properties verify. This separates a localized stochastic speech retry from unrelated generation without weakening source admission. Seed overrides require known segment IDs, unique entries, finite unsigned 32-bit integers and scoped reasons; they create a new immutable plan and retain the failed attempt. Quality observations transfer only by actual audio hash, not matching parameters or seeds. A completed artifact remains bound to its recorded generation revision. Verify it using that revision’s isolated locked checkout; independently validate its source with the current codec. A stricter admission check does not retroactively change correctly parsed source or generated samples, and must not be bypassed by rewriting stored runtime hashes. Real two-segment generation proved unchanged-request byte reuse while rejecting reuse of the changed-seed segment; ephemeral checks also rejected corrupt saved bytes, unknown/duplicate overrides, blank reasons and boolean/out-of-range seeds. A reviewed alternative seed restored the authored this after two independent ASR models had agreed on is, with both models then transcribing the full unchanged clause correctly. These proofs justify local retry/reuse without word edits or silent attempt substitution.

Establish the operating token budget from real completion and pacing of the largest complete sentences under the public output ceiling. Prefer whole supported sentence spans when those auditions pass; add coherent source-reviewed clause cuts only where native context, completion or delivery requires them. An advisory 220-token limit must not become a model restriction by assumption.

Create `skills/chatterbox/SKILL.md` with calibration and quality sampling, and only reusable helpers justified by deterministic reliability. Audition representative exposition, sustained questions, elevation, exhortation, heading, verse, difficult names and longest segments before rendering the whole. Calibrate acting and punctuation together with structural silence; preserve authored words and review any scoped pronunciation exception. No invented native pause/emotion tags.

Numerical calibration belongs to rendering and must not repeat editorial normalization. The shared codec writes complete candidate scripts; a frozen calibration record binds original/candidate script hashes and a reason for every changed speech vector. Planning permits only six per-speech numeric controls to differ: all text, voices, headings, order, metadata and coverage must equal the accepted script. Physical subdivisions inherit the selected candidate's complete explicit vector. There are no runtime preset deltas or hidden overrides. Editorial punctuation/pronunciation changes still return to adaptation and its source review. The final candidate is selected from actual auditions, not inferred from a numeric profile.

For every segment and assembled delivery, verify readable finite audio, duration/word pacing, active-speech/silence distribution, RMS/loudness, peak/clipped runs, DC offset and suspicious transitions. Reconcile actual speech against complete expected text using a supported safe ASR backend; inspect omissions, repetitions and hallucinations. ASR cannot certify preferred classical pronunciation. Sample playback across passage types, joins and every flagged anomaly; check intact consonants, breath/decay, clicks, pauses and pacing. Quantitative checks are evidence, not perceptual proof. Audio-language critics require unprompted recognition of a known real clip and consistency with its decoded intervals; positive features alone do not establish judgment quality. Impossible event times or unexplained prompt-dependent descriptions require independent review rather than audio changes made to satisfy the critic. Repair unexplained anomalies and repeat affected checks. Verify assembly order/coverage and the delivered encoded artifact itself, including duration and navigation from the genuine section spine. Lossless assembly requires every verified request in frozen order, explicit reviewed gaps in native frames, exact decoded-sample preservation and realized genuine-heading metadata. Its report binds source audio, assembly code, gap declarations, metadata and output hashes; assembly verification does not approve delivery quality.

## Gutenberg acceptance and current evidence

The [supplied edition](https://www.gutenberg.org/files/29510/29510-h/29510-h.htm) is Plotinus, translated by Thomas Taylor. Narrate the genuine `CONCERNING THE BEAUTIFUL` heading, main essay and embedded two-line verse; exclude title/publication matter, translator introduction, all twelve notes, transcriber matter and Gutenberg notices. Introduction/substantive notes remain provenance. No print-page labels were identified; work pages do not claim print pagination. One narrator is appropriate; poets/questions do not create speakers. Preserve archaic diction and uncertain apparent defects rather than conjecture. Contrast analysis with contemplative ascent and exhortation under restrained calibrated delivery.

The admitted witness inventory has sixty-nine units, seventeen body units and 4,708 projected body words. Bounded conversion compared every indexed unit's words/punctuation with retained HTML under declared layout whitespace; all twelve linked note calls retain exact spans. A nontext rule is furniture, and body italic styling covers only punctuation rather than omitted emphatic wording. Actual declared text-adapter execution and main-agent review accepted every unit: seventeen narrated, fifty-two excluded. Export produced one canonical script with thirty-four semantic beats, one genuine heading and the intact two-line verse. Independent reconstruction checked every narrated word against the source after removing exactly nine indexed body calls, every contiguous beat span, and all sixty-nine ledger entries in original order. These are text proofs; audible acceptance is separately bound to the delivered file and its quality evidence.

The shared [segmentation helper](../../src/audiobooks/segmentation.py) uses supported English sentence spans and the actual original tokenizer; real-library checks retained abbreviation/quotation punctuation, packed short sentences, rejected an oversized sentence without an approved cut, and preserved complete original text with explicit clause cuts while rejecting invalid offsets. The pinned model tokenizer snapshot `5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18` measured a maximum Gutenberg sentence of 390 tokens and nine sentences above the provisional 220-token budget. The current Plotinus render plan and clause cuts live below `$WORKSPACE_DIR/plotinus/render/enoch/`. Neither an input count nor a sentence-model prediction certifies audible completion or attribution placement.

The rendering contract is exercised with real original-model audio: strict calibration preserves source/voice/structure, frozen-input changes reject reuse, and saved-byte/decoded-property checks reject corruption. Independent real-plan checks preserve all thirty-four beats and complete spans. Request-scoped recovery changes only diagnosed requests: native planning reused an unchanged waveform while excluding a changed seed, and corruption of the copied waveform prevented reuse. CLI intake/schema imports remain independent of Torch. The assembly helper rejects incomplete real-book audio before creating delivery output; a native WAV-to-AAC/M4B smoke check preserves escaped FFmetadata chapter titles and realized end times through ffprobe. The complete sixty-one-wave assembly preserves every decoded native sample exactly and records realized genuine-heading times; real-book guards reject unknown, duplicate and terminal gaps before output, with strict boolean/negative-frame rejection.

The restrained candidate uses low CFG, reduced exaggeration and native repetition baseline 1.20. Matched-seed acting comparisons and expanded category/name auditions support further rendering, with unprompted full-wave ASR and measured pacing/silence/peaks. A no-clause-cut 400-token plan has sixty-one exact spans, a maximum request of 399 native tokens and 115 words. Twenty real auditions cover every formerly over-budget sentence, largest requests, delivery categories, genuine heading, verse and difficult names. All complete generation under the unchanged public output ceiling; full-wave large-v3 transcription flags localized word questions rather than truncated endings. Longer coherent context restores previously disputed stars and magic without editing words or changing seeds. A second independent recognizer adjudicates remaining lexical flags; agreement is evidence, not perceptual proof. The [Whisper model card](https://github.com/openai/whisper/blob/main/model-card.md) warns that transcripts can contain words absent from audio, so additions also require review.

Audio-language criticism uses Qwen2.5-Omni's vendor-supported reference environment, public full-model API with audio output disabled and trained bfloat16 precision. An unprompted known-clip transcript matches every source word, with observed encoder execution and nonzero audio tokens. The selected spoken-verse candidate preserves all wording and line breaks; a matched-seed lower-exaggeration comparison distinguishes measured spoken reading from chant-like delivery. Analysis environments remain separate from the frozen generation runtime. Impossible event times, prompt-dependent descriptions or an interval excluding the flagged occurrence cannot govern repairs; final observations bind actual audio hashes and covered intervals.

The complete sixty-one-request book retains whole-sentence context and both independent full-wave ASR reports. Source-confirmed errors receive reviewed complete-span seed retries, without editorial changes; unchanged requests retain byte-verified recordings. The current strict codec independently reconstructs all seventeen narrated units, nine removed indexed body calls and thirty-four semantic beats from the retained witness. Lossless assembly preserves every native sample in plan order with no added gaps and lasts 1,424.84 seconds. Review covers all sixty joins; unchanged observations transfer only after exact source-interval and reviewed-excerpt verification.

A common -2 dB gain preserves relative dynamics and native 24 kHz mono audio, without limiting, resampling, trims or fades. Measurement of the actual AAC/M4B gives -19.4 LUFS, 2.3 LU range and -1.1 dBTP; probing confirms the one normalized genuine heading from zero through the realized 1,424.84-second end. All sixty-one decoded sample intervals correspond to their lossless source intervals, with separately recorded codec padding. Complete unprompted encoded transcription reaches the final source sentence. Seventeen localized second-recognizer checks and three occurrence-covered independent audio-model transcripts reconcile all thirty-one flags as spelling/homophone variants, weak-vowel differences or whole-book transcription artifacts. The repaired endpoint retains in mire alone. Thirty actual encoded perceptual samples cover opening/closing, delivery categories, heading, verse, names and diagnosed passages; sixty actual decoded join measurements supplement the source-bound join observations. Historical evidence remains evidence of that delivery; current delivery records use the `$WORKSPACE_DIR/<book-name>/delivery/` stage.

Ephemeral real-library checks passed literal Markdown punctuation/verse/headings/voice round trips, duplicate-attribute and numeric-policy rejection, prepared/index/witness checks and source mutation rejection. Installed locked Pandoc is 3.9. A real CLI fixture passed frozen intake, exact ownership/spans/approved vectors, stale/extra-unit rejection, independent completion order, fresh-process resume and repeatable ordered export; the six-unit workflow takes roughly eight seconds, a fixture observation rather than book throughput. Revision checks invalidated one changed paragraph and immediate context while retaining unrelated reviewed dispositions and rejecting their reinterpretation. Fragment checks passed sequential coverage, missing/altered-span rejection, exact reassembly and committed recovery without drafts. Native English spans also preserved abbreviation and quotation closure.

A real EPUB fixture passed deliberately nonalphabetic spine order, a reviewed page-continuation join, both original locators and print labels, and Pandoc/index admission; this does not prove automatic semantic continuation detection. Independent five-unit runtime forward use passed heading hierarchy, scoped abbreviation/number edits, attributed narrator quotation, verse and substantive-note exclusion, including invocation outside the repository. Skills pass skill-creator validation. These proofs remain narrower than complete audiobook acceptance.

Completion requires all of the following at current state: admitted HTML/EPUB behavior and source lineage; frozen surveyed brief and exercised declared worker; exact source disposition and normalized/beat coverage; supported finite controls and valid voices; faithful canonical round trips; interruption/revision/order behavior; verified original-tokenizer rendering plan; complete Gutenberg script without paratext; polished chatterbox skill and calibrated complete audio; source-completion, technical and sampled perceptual checks of the delivered artifact. No missing or indirect evidence counts as achieved.
