# Directing original Chatterbox

Use this vocabulary consistently:

- A **director move** is a source-exact registered action accepted in `acting-score.json`.
- A **delivery beat** is a contiguous normalized span mapped to one or more accepted moves and one
  registered action vector. Every narrated character belongs to exactly one beat.
- The beat's resolved **Chatterbox parameters** are the generation request. Physical subdivisions
  inherit them unchanged.

## Source-backed direction and calibration

Use deliberate, educated address with differentiated action-specific starting settings. The
single runtime registry supplies this complete table:

| Action | Exaggeration | CFG | Temperature | Repetition | Min-p | Top-p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `CLARIFY` | .40 | .50 | .80 | 1.20 | .05 | 1.00 |
| `PROBE` | .50 | .40 | .80 | 1.20 | .05 | 1.00 |
| `CONVINCE` | .60 | .50 | .80 | 1.20 | .05 | 1.00 |
| `WARN` | .50 | .30 | .80 | 1.20 | .05 | 1.00 |
| `INVITE` | .40 | .40 | .80 | 1.20 | .05 | 1.00 |
| `EXALT` | .60 | .30 | .80 | 1.20 | .05 | 1.00 |
| `URGE` | .60 | .40 | .80 | 1.20 | .05 | 1.00 |
| `RESOLVE` | .40 | .30 | .80 | 1.20 | .05 | 1.00 |

Read the [acting specification](../SPEC.md#acting-direction-and-control-provenance) for the single
textbook authority, direct code, external-source conflicts, two-seed trials and explicit defense of
each numerical choice. These are bounded production starting choices, not eight native model
emotions or guaranteed pace/pitch shapes. The director derives the task from the source; the adapter
copies its registered vector without modifiers. The renderer auditions actual source and preserves
meaning while calibrating numbers. The agent owns the educated production judgment; do not impose
an external listener as a new approval gate. Report what the available evidence supports and any
perceptual limits; a failed critic supplies no approval. Never resume the withdrawn identical-vector
Of Happiness run or rewrite its frozen provenance.

## What the controls can realize

Read [original controls and quirks](chatterbox-original.md) before proposing calibration. The original
model projects `exaggeration` into a learned conditioning token. It does not take an action name,
emotion class, pitch target or volume target. CFG combines speech-token logits from text-conditioned
and text-ablated branches; both retain the speaker and emotion conditioning. Lower CFG is not a
separate calmness control. Temperature and probability filters govern sampling, not acting choices.
Keep the four sampling controls at baseline while diagnosing expressive scale or pacing.

When an audition overplays a passage, preserve its accepted action. Compare unchanged text, voice,
model and seed at baseline before trying a smaller expressive scalar. Change one control at a time
first. If baseline speech rushes, a lower CFG candidate around .3 is supported by upstream pacing
advice, but accept it only after checking completeness, pace and voice in that passage. Do not pair
every more serious thought with both higher exaggeration and lower CFG.

Treat `exaggeration >= .70` as an exceptional dramatic trial, never an action default. This is a
production-policy boundary informed by upstream dramatic-speech guidance, not an acoustic law.
For an intensified production candidate, require an explicit dramatic request or a source-supported
exceptional climax, explain
why a restrained realization is insufficient, and compare it with baseline and a less expressive
candidate before acceptance. `WARN`, `URGE`, `EXALT`, sacred vocabulary and punctuation alone do not
satisfy that condition. An explicit dramatic request permits the trial; it does not establish quality.
An overacting diagnostic may reproduce a prior vector on matched text; label and retain that audio
separately rather than treating reproduction as permission to use it in delivery.

Use the renderer's matched-text calibration record, bound to action, score move IDs, proposed and
realized vectors, and actual audition evidence. Keep any successful change scoped to the auditioned
material; a book-wide change needs representative evidence across its affected action families.
State the voice/text scope of any registry proposal; a single-voice result cannot prove transfer to other voices. Stop tuning when the intended
thought and contrast are clear at the requested scale without rushing, instability or lost words.

## Make material direction visible

Before accepting the score, tell the user the intended speaking scale and the material rhetorical
turns using the eight action names, a short source cue or unit IDs, and their listener objective.
Before the pilot, give the complete six-control baseline once. Report changed controls, affected
moves, the source reason and expected audible result when a material calibration is proposed or
accepted; label an unauditioned result as a hypothesis. Summarize the deciding audio evidence after
review. This is a concise decision explanation, not private deliberation or a per-move transcript.

For a material `CONVINCE` turn, name the counterexample and the assent it seeks, report the actual
six-value candidate and its evidence, and distinguish an observed acoustic difference from a heard
rhetorical effect. The objective states the direction; the parameters do not guarantee emphasis.
