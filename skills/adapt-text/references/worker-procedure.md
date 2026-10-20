# Text-adapter worker procedure

Use this procedure for one assigned batch. The main agent supplies the interpretation of the edition in a versioned text brief. Your job is to apply it faithfully in one paragraph-by-paragraph normalization-and-cue pass. Do not survey the whole book or redesign its performance.

## 1. Check the packet

Require batch/attempt IDs; prepared-source, plan, configuration and text-brief hashes; ordered owned units grouped into work pages; separately labeled context-only units; applicable scoped rules; registered voice IDs; accepted preceding continuity or explicit section start; result schema; and your draft path. Undirected legacy work also requires its approved choices. Directed work instead requires the accepted acting-score hash, every applicable source-exact move, and the complete registered action vectors. Read [acting-direction.md](acting-direction.md) to understand the fields, not to reinterpret the work.

If an input is missing, contradictory, stale, or too large to process completely, report the precise issue and stop before adapting. Do not fill a missing brief with assumptions. Existing helpers may be used for read-only checks; missing helpers are not an instruction to implement them.

A fragment packet owns only its supplied portion of one oversized source paragraph. The fragment result composes these fragment fields with a nested ordinary `result`. Preserve `fragment_id`, `fragment_plan_hash`, `fragment_predecessor_hash`, `source_start` and `source_end` in the result. Beat offsets refer to this fragment's normalized text; source offsets refer to the original prepared paragraph. Use preceding fragment continuity and context without emitting neighboring text. The main agent assembles the complete paragraph and performs its acceptance review; a fragment never advances the book cursor by itself.

## 2. Process owned units in order

For each work page, visit each owned unit exactly once. Never emit a context-only unit.

If the packet supplies a unit in `fixed_results`, copy that previously reviewed disposition exactly. Do not normalize or direct it again. It remains owned output for coverage; the helper rejects any reinterpretation. Process only the remaining units through A–C below.

### A. Decide disposition

1. Apply any exact unit-specific decision in the brief.
2. Otherwise exclude `role=paratext` with reason `paratext` and its observed category. This includes substantive notes and translator/editor introductions.
3. For `role=unknown`, apply a matching source-evidenced classification rule from the brief. If none resolves the role, return `unresolved`; do not guess body versus paratext.
4. For body text, continue to B. An extraction defect or unclear meaning also produces `unresolved` with the unit ID and exact source phrase. Continue with independent units; do not claim the batch ready for acceptance.

### B. Normalize one paragraph for speech

Apply only these operations, in order:

1. Remove identified citation calls, page furniture and other print-only apparatus. Preserve the surrounding words and punctuation needed to connect the sentence.
2. Apply the brief's exact, scoped transcription corrections, if any. Preserve uncertain spelling/OCR and flag it; do not modernize archaic wording.
   Apply only supplied pronunciation respellings, keeping each name word joined as specified in
   [source-and-normalization.md](source-and-normalization.md#pronouncing-names-as-whole-words).
   Never turn a phonetic hint into syllables separated by spaces or hyphens. Report a conflicting
   split-syllable rule to the main agent rather than inventing a replacement.
3. Expand spoken numbers, ordinals, dates, Roman numerals, abbreviations and symbols under the brief's conventions. If a form has more than one materially different reading and the rule/context does not settle it, mark it unresolved.
4. Remove list/formatting markers while retaining spoken item labels and content. Make punctuation speech-friendly without changing sentence order or argument. Preserve quotation words, reporting clauses, stanza relationships and paragraph identity.
5. Record the normalized text and nontrivial before/after edits with reasons. Check it against the source before selecting cues. No summarizing, paraphrasing, added explanation, or restored/invented speaker labels.

Keep the source kind: a real heading remains a heading; an ordinary paragraph does not become one because it sounds elevated. Use the source/brief's structural evidence.

### C. Map accepted direction immediately

1. Use the brief's scoped voice assignment; otherwise use its narrator voice. Only explicit source turns or a main-agent instruction permit a voice change. Quotation marks and pronouns alone do not establish a new speaker.
2. For directed work, map every accepted source move into normalized text in order. A beat lists its `score_move_ids` and their one shared action. A move may repeat across adjacent beats for a real delivery or voice split. Adjacent moves with the same action may provisionally share one acoustic beat while retaining both IDs; flag that merge for main-agent review of whether the semantic turn remains audible. Different actions or voices require separate beats. Never omit, reorder, reinterpret, or substitute a move. Report a source/normalization contradiction to the main agent.
3. For undirected legacy work, start with the section baseline and switch only when a supplied trigger applies. This compatibility path does not authorize a local worker to invent a whole-work dramatic trajectory.
4. Choose the largest contiguous beat that sustains one accepted action and voice without obscuring a mapped turn. Keep a quotation with its reporting clause; split at a change in action or voice and where a semantic turn needs an audible boundary despite unchanged controls. Do not split merely at a work-page edge. Never combine owned and context-only text.
5. Copy the accepted action's six registered Chatterbox values exactly. Do not compute modifiers, choose arbitrary numeric values, insert inline instructions, or select another performance surface. A missing registry action is an issue for the main agent.
6. Return ordered half-open character spans into this unit's normalized text; the helper derives each beat's words from those spans. Do not retype a second version of the spoken text. Adjacent paragraphs can use the same action but keep separate unit results; the exporter may group them without losing their boundaries.

The accepted score supplies the action and the authoritative registry supplies its complete vector. Voice IDs, actions, and all control names are metadata, never spoken content.

## 3. Check the draft

- Result unit IDs equal the owned IDs once, in order. Each is `narrated`, `excluded`, or `unresolved`; no additional units.
- A narrated unit contains its normalized text, edit reasons and beat spans. Excluded units contain a reason, not generated speech. Unresolved units contain a precise question/defect, not guessed final speech.
- Beat spans cover normalized text exactly once in order, including inter-beat whitespace according to the supplied schema. Derive offsets with a script rather than guessing character counts. Each voice is registered. Each directed vector matches its registered action; each undirected legacy vector matches its approved choice. For directed work, collapsing adjacent repeated IDs across beats yields every accepted move ID exactly once in source order, and each beat's action agrees with all of its moves.
- Narrated text has no residual raw digits, removed-apparatus markers, formatting instructions or unsupported model tags. If the brief explicitly permits a literal exception, report its rule ID for the validator.
- Unit-scoped rules were applied only to their targets. Check the beginning and end of the batch against context for broken attribution, unfinished syntax or duplicated text.

Write the result in the supplied JSON schema to the assigned draft path. Run the supplied read-only validator when available and repair concrete errors. Do not invent a command or report a validator pass without execution. Preserve unresolved units so the main agent can resolve them; a syntactically valid draft may still be incomplete.

## 4. Return control

Return the draft path, counts by disposition, unresolved unit IDs, and at most 300 words of continuity notes about actual speaker/rhetorical/normalization decisions. Do not append a transcript of your reasoning or the whole adapted text to the main chat.

Stop after this batch. Do not call `accept`, edit shared files, write final Markdown, fetch another witness, synthesize, or spawn agents. On a repair request, change only the units identified by the main agent and retain the packet's identities; a new brief/hash requires a new task packet.
