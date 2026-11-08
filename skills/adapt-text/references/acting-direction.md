# Source-exact acting direction

Use this reference when creating or semantically reviewing an acting score. Score language is
metadata and never enters spoken text.

The [acting specification](../SPEC.md#acting-direction-and-control-provenance) owns this revision’s
single textbook basis and the explicit transfer from theatrical objectives to narration. The eight
actions below are local operational definitions, not a textbook taxonomy or native model grammar.

## Complete-work direction

Read the complete assigned short work or coherent section packet before setting boundaries. Derive
its throughline and macro trajectory from the frozen direction context and source itself. Do not
create a separate direction spine or ask the adapter to rediscover the trajectory.

For each thought ask what the narrator must cause the listener to do. Select exactly one registered
action:

| Action | Listener task |
| --- | --- |
| `CLARIFY` | Make a relation, premise, qualification, or example intelligible. |
| `PROBE` | Recruit the listener into a genuinely unresolved question. |
| `CONVINCE` | Seek acceptance or rejection through reasons, counterexample, or inference. |
| `WARN` | Make an adverse consequence or moral danger matter. |
| `INVITE` | Make the listener receptive to a possibility, image, or inward prospect. |
| `EXALT` | Enlarge an earned vision, magnitude, wonder, or desire. |
| `URGE` | Move the listener to undertake a commanded act. |
| `RESOLVE` | Land and retain a concluding distinction or settled alternative. |

Question marks, elevated vocabulary, imperatives, and paragraph endings are evidence rather than
automatic classifications. `CLARIFY` is the fallback when the span establishes no other listener
task. These actions are not an intensity ladder. A broad cue may qualify a supported action but
never supplies one by itself. A rhetorical question that advances a stated argument may be
`CONVINCE`; reporting a threat as an example may remain `CLARIFY`. Neither requires alarm.

## Intensity and vocal restraint

Default to deliberate, educated address to one attentive listener. Keep ideas active and contrasts
legible; let the listener follow each qualification and inference. Select the words carrying the
contrast rather than stressing every important-looking word. Preserve natural movement and warmth;
deliberate does not mean uniformly slow, solemn, detached or flat. Direct the action that produces
understanding rather than displaying an emotion as an end in itself. Build any escalation from the
passage and its preceding trajectory.

`WARN`, `URGE` and `EXALT` describe listener tasks, not instructions to shout. Warnings can be grave,
exhortations firm and visions spacious within a controlled speaking register. Catastrophe, sacred
subject matter or an imperative does not by itself authorize heightened vocal force. Reserve an
exceptional dramatic trial for an explicit production request or a climax whose source and build
support it, subject to the audition requirements in [performance.md](performance.md).

Interpret conventional directions in context: “deliberate” asks for clear thought and unhurried
transitions; “grave” for the weight of a consequence; “urgent” for a compelling listener task;
“intimate” for a specific addressee; “with wonder” for discovery. None is automatically slow,
low-pitched, loud, whispered or `EXALT`. Express the supported listener task with the existing eight
actions, and put speaking-scale limits in the brief. A direction to persuade need not sound angry;
an inward invitation need not become breathy. These are acting intentions, not extra model syntax.

Freeze this restraint in the brief's performance limits and review the build into each climax.
Keep the source-supported action; do not relabel an intense passage as `CLARIFY` merely to reduce
its loudness. If realized audio escalates too quickly, route the affected moves to rendering
calibration while preserving their dramatic intent. These limits do not add fields to score moves.

## Exact moves

A move begins only when the required listener response changes. Punctuation and sentence boundaries
are evidence, not automatic cuts. Cover every character of each narrated prepared unit exactly once
with ordered half-open Unicode spans, including connective language and boundary whitespace.
Paratext has no moves.

Each move contains only:

- its unique ID, unit ID, and exact source span;
- one registered action;
- one sentence in the form `[ACTION] the listener to [observable response] by [textual tactic].`;
- exact textual evidence contained in that span.

Do not add mood, emotion, Laban factors, intensity, tempo, palette choice, trap, or numeric controls.
Do not invent psychology, characters, doctrinal certainty, or subtext beyond the source. Return a
precise direction-context defect when a frozen claim contradicts the passage.

## Review

Mechanical checks verify exact offsets, ordered complete coverage, registered actions, objective
grammar, evidence containment, source identity, and later vector derivation. They cannot approve an
interpretation. The main agent reads every move of a short work and every move in the first section
of a long work against its words and neighbors, expanding review after any failed sample.

Challenge unsupported boundaries, cue leakage, action labels chosen from punctuation alone, and
uniform force. Freeze a coherent, source-faithful, role-correct score once it satisfies its objective;
do not reopen defensible local choices for marginal relabeling.

Give the main agent concise notes on material turns and restraint choices. The main agent reports
those choices to the user under [performance.md](performance.md#make-material-direction-visible),
then verifies their realization in audio; source-exact metadata alone cannot establish delivery.
