# Cue-seeded single-pass direction workpad

## Mandate and boundary

Design, experimentally validate, and implement one acting-direction protocol for audiobook text.
The protocol must let a reasoning-capable text director create one source-exact score from the
complete short work or coherent section packet, then let the processing agent adapt each paragraph
once in source order without interpreting the prose again.

The first proving case is the admitted Thomas Taylor Plotinus essay in
[`WORKPAD.md`](../.workspace/plotinus/WORKPAD.md). Its requested test treatment is deliberately
**over-acted**: local actions and transitions should be unmistakable so the experiment exposes
whether the directing grammar and Chatterbox mapping work. This is a diagnostic sibling, not an
assumption that maximal intensity is suitable for final publication.

This workpad authorizes research, isolated application-agent prompt experiments, canonical implementation
after its experiment gate passes, and the final bounded Plotinus test workflow. It does not authorize
replacing either existing verified Plotinus export. A new delivery must remain a separately named
variant and satisfy the ordinary source, render, assembly, delivery, and export contracts.

The governing user decisions are:

- the complete-work Sol direction pass derives the macro trajectory; no separate spine is retained;
- the Sol text director receives those cues and owns the source-exact rhetorical score;
- the Luna processing agent preserves that accepted score during one forward paragraph pass;
- one normative acting grammar chooses the stage direction once;
- each stage-direction category maps directly to one complete Chatterbox configuration;
- fresh isolated agent-context experiments must establish text-level effectiveness before the
  protocol is integrated into the canonical skill contract;
- the raw answer and direct disposition of every material probe belong in its workspace evidence
  directory; and
- the full audiobook workflow runs last, only after the revised skill has passed its soundness gate.

## Governing hypothesis

The Sol text director reads the complete short work or coherent section packet and creates one
source-exact rhetorical score. The main agent accepts that interpretation only after complete
semantic review. Luna then processes prepared paragraphs once in source order, preserving accepted
move fragments and deriving each action's registered Chatterbox vector mechanically.

The causal chain under test is:

```text
complete admitted text + frozen user cues -> Sol source-exact direction
                                           -> main-agent semantic acceptance
                                           -> Luna one-forward adaptation
                                           -> registered Chatterbox vector
```

A separate macro spine is not part of the candidate: P3 found that the complete-work Sol director
derived all declared transitions equally well without it. The protocol fails if Luna must reinterpret
prose, if two semantic readers can change the same action, if any accepted score omits or overlaps
source characters, if direction remains decorative without selecting a vector, or if the over-acted
cue becomes uniform force.

## Candidate runtime protocol

### Whole-work director context

The director receives the complete admitted short work, frozen addressee and production cues, and
the registered action meanings. It derives the throughline and macro trajectory while reading that
complete packet once for direction. No separate direction spine, anchor list, paragraph-level mood,
intensity tier, Laban field, or numeric control is supplied.

P3 compared the complete essay with and without the initial nine-anchor spine. Both variants made
the same four declared transition decisions and grounded them in adjacent source units. The
no-spine variant therefore won: zero anchors is the least detailed context that preserves the tested
macro continuity.

### Source-exact direction and one-forward adaptation

The Sol text director receives the frozen direction context and complete narrated short work or
coherent section packet. It reads that packet before setting boundaries, then covers every prepared
source character exactly once with ordered moves. Each move has only its exact span, one registered
action, one transitive listener-directed objective, and exact local evidence.
The director does not normalize, synthesize, choose another performance surface, or author numeric
controls.

The main agent reads every move for a short work against its exact words and neighbors. Mechanical
coverage is necessary but cannot accept interpretation. Only a reviewed score becomes the semantic
authority for processing.

Luna receives the accepted score with prepared units in source order and processes each paragraph
once. It preserves move identity, span, action, objective, and evidence; maps the action to the one
registered vector; and performs only the permitted normalization and delivery-beat work. Luna must
not classify the prose again, revise an accepted action, or introduce mood, Laban, intensity, tempo,
palette, or another independent direction field. A mismatch between prepared text and accepted score
is returned as a stale-identity defect.

Each move uses one normative acting sentence:

> **[ACTION] the listener to [observable response] by [textual tactic].**

The eight action meanings are:

- `CLARIFY`: make a relation, premise, qualification, or example intelligible.
- `PROBE`: recruit the listener into a genuinely unresolved question.
- `CONVINCE`: seek acceptance or rejection through owned reasons, counterexample, or inference.
- `WARN`: make an adverse consequence or moral danger matter.
- `INVITE`: make the listener receptive to a possibility, image, or inward prospect.
- `EXALT`: enlarge an earned vision, magnitude, wonder, or desire.
- `URGE`: move the listener to undertake a commanded act.
- `RESOLVE`: land and retain a concluding distinction or settled alternative.

Punctuation, elevated vocabulary, and the production cue are evidence, not automatic actions.
Boundaries follow genuine changes in listener task. The accepted score, not an ordered Luna
question tree, owns difficult rhetorical distinctions.

### Candidate action registry

These complete vectors are hypotheses for matched Enoch auditions. Until audio establishes a
replacement, temperature, repetition penalty, min-p, and top-p remain one stability policy. The
processing agent never edits or computes these values.

| Action | Intuitive stage direction | Exaggeration | CFG | Temperature | Repetition | Min-p | Top-p |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `CLARIFY` | Make the thought lucid and grounded. | .55 | .40 | .80 | 1.20 | .05 | 1.00 |
| `PROBE` | Recruit the listener into a live question. | .78 | .30 | .80 | 1.20 | .05 | 1.00 |
| `CONVINCE` | Apply firm argumentative pressure. | .84 | .30 | .80 | 1.20 | .05 | 1.00 |
| `WARN` | Make an adverse consequence matter. | .90 | .28 | .80 | 1.20 | .05 | 1.00 |
| `INVITE` | Draw the listener toward a possibility. | .76 | .30 | .80 | 1.20 | .05 | 1.00 |
| `EXALT` | Enlarge an earned vision, wonder, or desire. | 1.00 | .26 | .80 | 1.20 | .05 | 1.00 |
| `URGE` | Move the listener to undertake the commanded act. | .94 | .28 | .80 | 1.20 | .05 | 1.00 |
| `RESOLVE` | Land and preserve the final distinction. | .72 | .34 | .80 | 1.20 | .05 | 1.00 |

Calibration may replace an action's complete vector after matched-text auditions. It must retain a
one-to-one action/vector registry; it may not add hidden modifiers, profile arithmetic, or
paragraph-specific numeric invention.

## Probe-first development contract

Probe only one concrete uncertainty at a time. Before starting, write this one-sentence record under
`$WORKSPACE_DIR/plotinus/adaptation/direction-probes/<probe-id>/`:

> Objective: determine whether <one prompt rule or contrast> produces <one observable behavior> on
> <one exact source passage>.

Then give that exact passage and relevant prompt text directly to one fresh application agent.
Use `gpt-5.6-sol` for text-direction behavior and `gpt-5.6-luna` at `medium` for mechanical
processing behavior. Never use one role's output as behavioral validation of the other.

Keep the run observable. Require the agent to state the objective and passage before analysis and
to report its chosen offsets or comparison basis before its final answer. Read those messages while
the agent works. Interrupt a run that goes silent or works on something else; it supplies no
behavioral evidence.

Keep the record plain: preserve the agent's unedited final answer, then write a short direct verdict
against the objective. Do not use response schemas, parsers, launchers, persistent sessions,
aggregate quality scores, or repository/runtime integration for probing. A disagreement is a
failure of the tested rule, not something to average away.

Freeze a revision once it is coherent, source-faithful, role-correct, and satisfies the stated
objective. Do not reopen a defensible local choice merely to optimize among marginally plausible
labels or wording.

Use the smallest passage that can answer the objective. Only continuity probes may use the complete
essay, because whole-work continuity is their stated subject.

## Required prompt probes

The following probes are gates, not suggestions. Keep each raw answer and its direct disposition in
that probe's workspace evidence directory.

Each probe has exactly one governing decision:

| Probe | Decision it may inform |
| --- | --- |
| P0 | Establish the four named failure rates of the unchanged current contract. |
| P1 | Decide whether the Sol text-director protocol distinguishes listener responses at real rhetorical turns. |
| P2 | Decide whether the normative objective grammar excludes decorative or intransitive direction. |
| P3 | Decide whether a separate spine improves whole-work continuity over complete-work Sol direction alone. |
| P4 | Decide whether Sol owns direction once and Luna performs one forward non-semantic processing pass. |
| P5 | Select the least detailed direction context that preserves the required macro transitions. |
| P6 | Decide whether the over-acted cue strengthens supported actions without becoming uniform force. |
| P7 | Decide whether the selected prompt generalizes to untouched holdout rhetoric. |
| P8 | Decide whether a bad frozen context claim is surfaced precisely instead of forced into the score. |
| P9 | Confirm separate score ownership and mechanical Luna mapping across the complete candidate work. |

A probe cannot support a different decision. Before any invocation, its objective sentence must
name the exact passage, the one contrast being tested, and the observable pass or fail behavior.

### P0 — Current-contract baseline

Run the current acting-direction contract on Plotinus `u000027`, `u000028`, `u000038`, and
`u000042`. Establish the observed rates of free-form direction, category compression, unsupported
emotion, and action-to-vector ambiguity. This is comparison evidence, not authority for the repair.

### P1 — Text-director action discrimination

Use Sol text-director contexts on isolated passages containing:

- accumulated inquiry in `u000027`;
- received theory, counterexample, and renewed inquiry in `u000028`;
- warning imagery followed by its interpretation in `u000040`; and
- command, conditional preparation, ascent, and final distinction in `u000042`.

The director must distinguish actions because the listener task changes, not because punctuation or
elevated vocabulary changes. It must retain genuine `CLARIFY` inside an over-acted production and
cover each supplied passage source-exactly. Main-agent semantic review decides whether each move is
supported; another model does not validate the director by imitation. Luna replay tests only
preservation and vector derivation from an accepted score.

### P2 — Objective-grammar enforcement

Give the Sol director tempting invalid directions such as “be mystical,” “sound passionate,” “grave and
controlled,” and “Press.” The candidate must replace each with the registered transitive action and
the listener response established by the text. Test the nearest valid descriptive phrase inside
textual evidence so the rule does not erase source language.

### P3 — Spine versus no-spine control

P3 is accepted. Complete-essay Sol contexts with and without the initial nine-anchor spine selected
the same actions at `u000032`, `u000038`, `u000040`, and `u000042`. Both were coherent; the
no-spine context grounded every transition directly in adjacent units. No spine is retained.

### P4 — Role and pass compliance

The Sol director may read its complete assigned short work or coherent section before scoring; it
must not normalize or synthesize. The Luna processing task contains the accepted score followed by
each owned prepared unit exactly once in source order. Luna must not survey the work, classify prose,
revise earlier direction, or inspect later units before emitting the current normalized result. Any
need to reinterpret an action returns to the score owner instead of creating a second semantic pass.

### P5 — Context granularity disposition

P5 is satisfied by the P3 simplification. Once zero anchors preserved every declared transition,
there was no coarser spine to test and no disputed anchor with an earned benefit. Do not run
ceremonial anchor variants after the no-spine control has won.

### P6 — Over-acted cue pressure

Apply the production cue:

> Make every text-supported action and transition unmistakable, even beyond tasteful publication
> restraint, while preserving the argument, qualifications, and contrasts.

The output must heighten `PROBE`, `CONVINCE`, `WARN`, `EXALT`, and `URGE` where supported while
allowing genuine `CLARIFY` and `RESOLVE` spans. Uniform `EXALT`, uniform high force, invented
interlocutors, and loss of qualifications fail the probe.

### P7 — Holdouts

Do not use these passages while revising the prompt:

- the Bacchalian experiential sequence in `u000032`;
- Tartarus and mire in `u000035`;
- the Ulysses verse transition across `u000040`–`u000041`; and
- the last alternative formulation in `u000042`.

After selecting the candidate, test whether it distinguishes inquiry from enactment, warning from
horror performance, verse from a new character voice, and resolution from uninterrupted exaltation.

### P8 — Direction-context defect recovery

Supply one knowingly incorrect frozen direction-context claim for a working passage. The Sol
director must report the exact source contradiction instead of forcing the passage, silently
ignoring the defect, or rewriting completed moves. This tests recovery at the remaining direction
boundary without reintroducing a spine.

### P9 — Source and mapping preservation

Test the selected separate architecture: a reviewed source-offset score remains the sole semantic
artifact, and Luna maps its accepted moves mechanically during normalization. The result must
preserve exact narrated words, ordered span coverage, move identity, action, objective, evidence,
and the action's registered vector. It must neither introduce spoken directions nor select a second
performance choice. The bounded `u000027` fixed-score replay supports this ownership split; P9
passes only after the same preservation holds across the complete candidate work and stale-score
identity is rejected.

## Prompt acceptance gate

The candidate protocol may enter canonical skill authoring only when:

- P0 supplies a usable baseline;
- P1–P6 pass in fresh contexts without an unresolved disagreement;
- all P7 holdouts pass without prompt tuning against them;
- P8 returns a precise spine defect rather than producing an invalid score;
- P9 selects and supports one mapping architecture;
- every narrated Plotinus character is covered exactly once in the full candidate output;
- every move has one registered action, matching normative objective grammar, and local evidence;
- the over-acted cue produces strong local contrasts without erasing `CLARIFY` or `RESOLVE`; and
- no accepted behavior depends on Laban, free-form emotion, intensity tiers, or an independently
  selected performance choice.

If these conditions are not met, continue isolated experiments. Do not compensate by appending
qualifiers or parallel standards to the canonical skill.

## Canonical implementation plan

After the prompt gate passes, implement the smallest coherent replacement.

1. Update Plotinus's project `WORKPAD.md` with the accepted diagnostic intent, no-spine decision,
   action registry, evidence directory, and consequence for regeneration.
2. Keep complete-work direction context in the versioned brief. Validate admitted source identity,
   frozen user cues, registered actions, and the absence of redundant paragraph-level direction.
3. Replace the current director reasoning fields with exact span, action, objective, and evidence.
   Remove runtime Laban, free-form intensity/tempo, cue application,
   independent palette choice, and per-move trap fields when no independent consumer remains.
4. Encode the eight registered actions and their complete vectors in one authoritative registry.
   Direction results reference an action; adapters and exporters derive the vector from the frozen
   registry instead of accepting authored numeric values.
5. Change the Sol text-director and Luna/medium processing instructions to the accepted ownership
   split. Preserve context bounds, source identity, isolated drafts, and one-forward Luna behavior.
6. Implement separate accepted-score mapping. Do not retain two semantic readers of the same prose.
7. Update deterministic validation for exact coverage, ordering, registered actions, objective
   grammar, evidence containment, spine identity, vector derivation, stale hashes, and recovery.
   Deterministic checks must not claim the interpretation is good acting.
8. Replace the responsible rules in `skills/adapt-text/SKILL.md`,
   `references/acting-direction.md`, `references/performance.md`,
   `references/worker-procedure.md`, and `SPEC.md`. Delete superseded competing instructions rather
   than preserving them as alternatives.
9. Reconcile `skills/chatterbox/SKILL.md` so calibration may replace a registered vector only through
   matched-text evidence and cannot collapse distinct action families without evidence for each.
10. Add deterministic tests for the structure and identity properties plus durable behavioral fixtures
    only where the probe evidence shows a stable, discriminating case. Keep raw model transcripts and
    maintenance reasoning outside runtime skill references.

## Revised-skill soundness gate

After implementation, rerun P1–P9 through the assembled skill in fresh isolated, role-appropriate
Sol text-director and Luna processing contexts.
This is distinct from testing the isolated candidate prompt. Also run:

- the repository's structural and unit-test commands for every changed boundary;
- current-contract versus revised-skill comparisons under identical inputs;
- a no-guidance control to establish that the skill, not general model capability alone, causes the
  required procedure;
- a restrained direction cue and an uncued run to verify that the over-acted Plotinus test did not
  become the reusable skill's intrinsic style;
- a paratext exclusion and a sustained-exposition case that should remain `CLARIFY`; and
- exact script round-trip and stale-identity rejection.

The revised skill is sound only when its runtime instructions are retrieved and applied, all
structural checks pass, fresh behavioral results satisfy the prompt gate, preserved cases do not
regress, and remaining uncertainty is explicitly bounded. Author inspection or passing unit tests
alone do not satisfy this gate.

## Targeted acoustic experiments

Only after the revised-skill soundness gate passes, render matched-text Enoch auditions for all
eight actions. Hold text, voice, model snapshot, segmentation, seed, and the four sampler controls
fixed while comparing the current spirited vector with the candidate registry vector. Use Plotinus
spans selected by the accepted score, including transitions between adjacent actions.

Review whether the intended action is audible, whether adjacent actions are distinguishable, and
whether exaggeration or CFG causes rushing, omissions, repetitions, clipped endings, chant,
caricature, or lost qualifications. Record improved, unchanged, and regressed cases. Revise one
action's complete vector at a time and repeat its working and holdout samples. If `.95`–`1.00`
exaggeration remains indistinguishable from the current rendition, treat voice/model conditioning or
the evaluation method as the suspected bottleneck; do not add interpretive machinery to compensate.

Acoustic evidence changes only the registry vectors. It does not rewrite the director's action
semantics or whole-work interpretation
unless the text probes independently establish a semantic defect.

## Final Plotinus workflow

The complete processing workflow is forbidden until both the prompt acceptance gate and the
revised-skill soundness gate pass and the targeted acoustic experiments have selected viable
vectors.

Then:

1. Create distinct `over-acted` attempts under the canonical Plotinus `adaptation`, `render`,
   `assembly`, and `delivery` stages. Preserve both existing deliveries and exports.
2. Freeze the admitted prepared source, accepted no-spine direction context, action registry, over-acted cue,
   voice binding, and all hashes in a new adaptation identity.
3. Run the accepted single-forward processing workflow once over the complete narrated essay.
4. Validate and semantically review every move because Plotinus is a short work and the experiment
   depends on visible local action.
5. Export source-identical scripts and prove parsed narration equality with the admitted text.
6. Plan and render through the ordinary native-token, completion, and recovery contracts. Do not
   reuse approval from either prior delivery.
7. Review every rendered segment for completion and technical defects, and review representative
   transitions for acting effectiveness. The deliberately exaggerated treatment may be excessive;
   it must still be intelligible and source-faithful.
8. Assemble, encode, verify chapters and complete delivery, and export as an explicit `over-acted`
   sibling only if the delivery independently passes. Otherwise retain it as diagnostic evidence
   and record why it was not exported.

The experiment succeeds when the over-acted version makes the registered actions and their changes
plainly audible while preserving every word and qualification. It may still be rejected as a final
artistic preference. If the actions are not audibly distinct, diagnose the failed boundary—spine,
action classification, vector mapping, synthesis, or evaluation—before another full run.
