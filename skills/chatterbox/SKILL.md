---
name: chatterbox
description: Calibrate and render faithful English audiobook scripts with original Chatterbox, recover verified segments, assemble and inspect delivery, and export the verified M4B. Use after adapt-text; does not acquire voices or rewrite source prose.
---

# Chatterbox

Render complete reviewed scripts with original English Chatterbox. Keep semantic delivery beats intact: physical generation segments inherit the voice and all six numeric controls. Generation success is not audio-quality approval.

Resolve `<skill-root>` to the absolute directory containing this `SKILL.md`, following symlinks. In a plugin, `<skill-root>/../..` contains `pyproject.toml` and `src/audiobooks/`; run `uv run --project "<skill-root>/../.." --locked --no-dev audiobooks …` from any working directory. uv supplies Python and dependencies on first use. For separately installed skills, run the installed `audiobooks …` instead; if it is absent from `PATH`, resolve its directory with `uv tool dir --bin` and invoke that absolute executable. All command examples below use this shared CLI. Run its `runtime-root` command to locate bundled resources as `<runtime-root>`. When authorized credentials are needed, use uv’s `--env-file <local-file>`; do not print credentials. Model downloads use native Hugging Face cache/revision options and public `ChatterboxTTS.from_local`, without downloader patches.

Use `$WORKSPACE_DIR/<book-name>/render/`, `assembly/`, and `delivery/` for generated work. Set `WORKSPACE_DIR` to a persistent directory outside the plugin cache. If unset or empty, the fallback is `~/Audiobooks/work/`. Relative work paths are resolved below that directory. Add a child such as `render/enoch/` only when distinct attempts must coexist.

Read the project's `WORKPAD.md` before rendering and preserve its `Blueprint`. Update the `Material record` for acoustic or model surprises, consequential segmentation, seed, voice, assembly, mastering or export decisions, material repairs, and requested revisions. Keep ordinary segment progress and generated hashes in their existing machine records.

## Freeze the rendering plan

Require adapt-text's complete manifest, ordered scripts with matching exported `script_hashes`, disposition/span ledger and exported `sections.json`. Re-export reviewed adaptation work if those hashes are absent; a changed script must be restored or revised through adaptation before planning. For directed work also require its exact acting-score hash and score-move lineage on every speech span. Check the opening/closing main-text boundaries, explicit delivery title/start bindings, genuine headings and embedded verse. Resolve missing voice files and pronunciation questions; quotations alone do not introduce voices. Read [original controls and quirks](../adapt-text/references/chatterbox-original.md) when choosing settings.

Download the five original model files (`ve.safetensors`, `t3_cfg.safetensors`, `s3gen.safetensors`, `tokenizer.json`, `conds.pt`) at one explicit Hub commit. Keep the resolved snapshot path. Planning obtains missing English Punkt data through NLTK’s native downloader. Encoding obtains FFmpeg and ffprobe through `static-ffmpeg`; neither needs path configuration.

Use a JSON list of reviewed clause cuts, or `[]` when none are needed; `audiobooks render schema clause-cuts` prints its strict schema. Each cut contains `speech_id`, zero-based `paragraph`, original Unicode `offset` at a word start after whitespace, and source-grounded `reason`. The helper packs supported sentence spans using `tokenizer.text_to_tokens(punc_norm(raw))`. A sentence exceeding the chosen budget stops planning. First establish through auditions whether the complete sentence fits a viable larger budget under the native input/output limits and selected delivery. Use a coherent reviewed clause cut when context, completion or pacing requires subdivision. Never use a GPT tokenizer, blanket bracket deletion, arbitrary word cuts or a regex fallback. Inspect attribution and verse boundaries even when a sentence detector accepts them.

Run `audiobooks render plan <adaptation-workspace> <model-snapshot> <new-render-workspace> <clause-cuts-json> --token-limit <budget> --seed <seed> --device <device>`. The provisional default of 220 input tokens is an operating budget, not an upstream maximum or completion guarantee. Original generation has a separate output ceiling. Review the frozen plan's native punctuation view: pass its raw approved text to generation, which applies native cleanup once.

## Audition, then render

Choose representative segment IDs covering heading, sustained exposition, question, elevation, warning/exhortation, verse, longest clauses and each difficult name. Include joins across subdivisions and delivery changes. Run `audiobooks render generate <workspace> --segment-ids <comma-separated-IDs>` and apply [quality review](references/quality-review.md). Calibrate acting, punctuation and structural pauses together; prefer restrained rhetorical contrast over alternating presets.

Preserve expressive intensity while checking that aggressive or loud registers do not arrive too
quickly. Audition the build into a climax and its return to ordinary speech against the
[acting limits](../adapt-text/references/acting-direction.md#intensity-and-vocal-restraint).
Reserve extreme vocal force for rare passages that earn it; repair affected moves through the
calibration workflow below rather than lowering the whole book's intensity.

Keep authored words. For numerical acting/pacing candidates, write complete canonical scripts in a separate directory using the shared codec. `audiobooks render schema calibration` prints the record schema: `source_script_hashes` and `candidate_script_hashes` use the exact manifest `script_files` keys (for example `script/0001.md`), and `reasons` keys name every changed speech ID. Each reason identifies the accepted directing choice and score moves, the proposed vector, the audition evidence, and the realized candidate vector. Run `audiobooks render plan … --calibrated-script-dir <directory> --calibration-record <record-json>` in a fresh workspace. The helper permits only the six per-speech numeric controls to change and checks exact text, voice, heading, order and coverage. Review candidates before choosing the final scripts; this changes acting without repeating editorial normalization. Do not collapse distinct move families into one global override unless matched auditions support every affected family.

Any pronunciation spelling or punctuation exception must be source-scoped, explained and reviewed in the adaptation contract. Resolve these editorial changes upstream and export again; create a new rendering plan. Do not silently alter frozen segments or inject nonexistent pause/emotion tags. Compare candidates in separate render workspaces with explicit seeds/settings.

Apply the [whole-word name guidance](../adapt-text/references/source-and-normalization.md#pronouncing-names-as-whole-words):
try natural reading first, use a conservative joined English respelling only where warranted, and
never feed syllable-separated coaching into speech. Audition the name in its full phrase and
check consistency across occurrences; ASR spelling alone cannot establish pronunciation.

After the auditions pass, run `audiobooks render generate <workspace>` for all remaining segments. Keep the actual process handle and inspect compact live progress; attach to it after observation timeouts. Restart only after confirmed termination and a diagnosed corrective action. A stopped run resumes the same frozen plan and verifies saved audio before reuse. Changed source, code, model, reference, device or plan requires a new identity. Missing or corrupted audio/records prevent reuse; do not bless them from filename counts. For completed audio from a recorded code revision, verify it in an isolated checkout of that revision with its locked project. Never edit recorded hashes or bypass current-runtime guards to attach an old waveform to changed code.

When a new plan changes only non-generative section metadata, `audiobooks render import-verified-revision <new-workspace> <prior-workspace> <isolated-checkout>` may reuse prior waveforms. It first runs the prior checkout's own full status verification, requires every generation request, model byte, lockfile, device, voice, seed, text, span and control to match, and compares the waveform-producing implementation and control schema structurally. Any difference stops import. Retain its hash-bound import record; this is not a general stale-runtime bypass.

Review while rendering: inspect the first few minutes before committing to bulk generation, then
review reproducible random passages from newly rendered audio at regular checkpoints. Apply the
[progressive sampling and escalation rules](references/quality-review.md) so problems are caught
before they spread. Keep review throughput practical; do not build an exhaustive ASR, phoneme or
audio-model review backlog for the end of the book.

For a diagnosed stochastic speech error, preserve the failed audio and retry the complete unchanged span with an explicit alternative seed. `audiobooks render schema seed-overrides` describes a list of `segment_id`, unsigned 32-bit `seed` and scoped `reason`; pass its file to a fresh `audiobooks render plan … --seed-overrides <file>`. Do not loop through seeds without reviewing the failure. `--reuse-from <prior-workspace>` validates the prior frozen plan and copies only verified audio with an identical segment generation request: exact span/text, controls, seed, model, reference, device and runtime. Book coverage remains checked independently; changed requests need generation and review. Transfer quality observations only when actual audio hashes match.

Built-in conditioning is restored explicitly before generation; custom references use the public conditioning path. A missing reference, conditioning failure or resource failure stops generation. Preserve failed attempts separately; choose a targeted reviewed correction rather than a fallback cascade.

## Assemble and deliver

For a literary anthology, read [anthology identification and transitions](../adapt-text/references/literary-anthologies.md) before reviewing chapter titles and opening joins. Preserve the exported title/author/work identification, and realize its heading/introduction pause targets through reviewed assembly gaps after inspecting existing quiet.

Require verified audio for every planned segment. Assemble in plan order at native sample rate/channels, retaining lossless generation samples. Derive cumulative sample positions from decoded audio and declared structural gaps, not source length or estimated reading speed. Audition joins before choosing gaps; retain consonants, breath and decay. Do not apply automatic trims, fades, padding, resampling or dynamics processing without evidence that it improves the selected delivery.

Before assembly, review every delivery chapter title against its exact start and surrounding text. Confirm that it coherently and plausibly names the section, preserve the authored wording, and normalize reader-facing metadata to consistent English title case without changing the spoken heading. Record one ordered entry per delivery section in a chapter-title JSON object with `style: "English title case"`; each entry contains exact `section_id` and `source_title`, approved `title`, and concise `coherence` and `plausibility` evidence. The helper rejects incomplete, reordered, lexically changed, all-caps, or inconsistently cased reviews.

Run `audiobooks delivery assemble <render-workspace> <new-output-directory> <gaps-json> <chapter-titles-json>`. Supply `[]` for no added silence, or reviewed entries with `after_segment_id`, native integer `frames` and scoped `reason`; unknown, duplicate and terminal positions are rejected. The helper preserves and verifies every source sample, derives chapters only from the frozen explicit delivery-section starts, requires chapter coverage from the first frame, records both source and display titles plus realized positions, and writes `chapters.ffmetadata`. A heading without a delivery-section record never becomes a chapter. For large PCM use `--container RF64`. Assembly remains unapproved until delivery review.

Encode with `audiobooks delivery encode <assembly-directory> <new-output.m4b> --bitrate <rate> --gain-db <gain>`. The helper maps FFmetadata and chapters, maps source-derived title/author, writes AAC in an MP4-family container, then reopens it with ffprobe and compares every complete normalized title and contiguous start/end time to the source-frame plan under its recorded tolerance. Its manifest binds commands, versions, input/metadata/output hashes and codec parameters. Measure the unprocessed assembly before choosing any common gain or mastering, and remeasure the encoded delivery. Use a supported large-file container if PCM outgrows classic RIFF.

Complete automated integrity and ordered-coverage checks for all segments, progressive sampled
audio review, targeted follow-up of credible defects, and brief checks of the actual delivery
file. Full perceptual review of every segment is not a completion requirement. Report the actual
sample coverage and any unresolved limitations; synthesis success or a transcript alone does not
establish audio quality.

Export the verified delivery by default after completing its quality review. Skip export only when the user or governing context explicitly says the delivery must remain in the work directory. Read the finished-library directory from `EXPORT_DIR`; it has no fallback. Run `audiobooks delivery export <delivery.m4b>`. For an explicitly named sibling performance that shares the same admitted author and title, pass `--variant <variant>` so both deliveries coexist without changing source metadata. The helper requires the passing delivery manifest and matching M4B hash, then copies atomically without replacing different content. When an authorized correction supersedes an existing export, pass its exact observed SHA-256 as `--replace-hash`; replacement stops if the target changed or disappeared.

The base export path is `$EXPORT_DIR/<author-slug>.<full-title-slug>/<short-title-slug>.m4b`; an explicit sibling variant is `<short-title-slug>-<variant-slug>.m4b` in the same book directory. Slugs use lowercase ASCII kebab-case; the short title drops an English leading article and subtitle, while the directory retains the full source-derived author and title. Do not report the Chatterbox task complete until export succeeds or the explicit no-export decision is recorded. Return the exported path or recorded no-export decision, source coverage, model/render identities, duration, navigation and concise quality findings, including unresolved pronunciation or perceptual limitations.
