# Directing original Chatterbox

Use this vocabulary consistently:

- A **director move** is a source-exact registered action accepted in `acting-score.json`.
- A **delivery beat** is a contiguous normalized span mapped to one or more accepted moves and one
  registered action vector. Every narrated character belongs to exactly one beat.
- The beat's resolved **Chatterbox parameters** are the generation request. Physical subdivisions
  inherit them unchanged.

For directed work, one action registry is authoritative:

| Action | Exaggeration | CFG | Temperature | Repetition | Min-p | Top-p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `CLARIFY` | .55 | .40 | .80 | 1.20 | .05 | 1.00 |
| `PROBE` | .78 | .30 | .80 | 1.20 | .05 | 1.00 |
| `CONVINCE` | .84 | .30 | .80 | 1.20 | .05 | 1.00 |
| `WARN` | .90 | .28 | .80 | 1.20 | .05 | 1.00 |
| `INVITE` | .76 | .30 | .80 | 1.20 | .05 | 1.00 |
| `EXALT` | 1.00 | .26 | .80 | 1.20 | .05 | 1.00 |
| `URGE` | .94 | .28 | .80 | 1.20 | .05 | 1.00 |
| `RESOLVE` | .72 | .34 | .80 | 1.20 | .05 | 1.00 |

The director selects the action from the source. The adapter preserves it and copies its complete
vector; it does not choose a second performance label or calculate modifiers. Undirected legacy
work may still use a brief's approved choices, but those choices never compete with an accepted
director action.

These vectors are experimentally accepted text-to-generation candidates for the over-acted
Plotinus diagnostic, not established acoustic meanings. Original Chatterbox exposes exaggeration as
an expressive scalar and CFG as conditioning guidance; the remaining four controls affect sampling
and stability. Do not infer emotions, tempo, pitch, emphasis, or Laban semantics from the numbers.

The renderer may replace a registered vector only through matched-text calibration evidence bound
to the exact action, score move IDs, proposed vector, and realized vector. Acoustic evidence may
change registry values; it does not rewrite action semantics or the accepted score. Stop tuning once
the intended contrast is audible without rushing, instability, or loss of fidelity.

Preserve the current expressive range when correcting overacting. Target only auditioned aggressive,
loud or high-register realizations and premature escalation, following the
[vocal restraint guidance](acting-direction.md#intensity-and-vocal-restraint). Exaggeration is not
an independent loudness control: no numeric threshold guarantees a calm or intense reading.
Compare affected moves in context with their lead-in and quieter neighbors; retain conviction and
emotional intensity while reducing excessive vocal force. Keep the registry unchanged without
matched audition evidence, and do not substitute global attenuation or flattened acting for this
localized performance correction.
