# Audio quality review

Catch problems during rendering with a reproducible random sample and targeted follow-up. Keep
complete mechanical integrity and source-order checks, but do not require listening, ASR, phoneme
analysis or audio-model criticism of every segment. Do not defer a large review queue until the
whole book is rendered. Record what was actually checked; sampled acceptance is not an exhaustive
listening claim.

## Complete mechanical checks

Verify every saved segment's hash, readable finite nonempty samples, native rate/channel count and
frame count. Reconcile every planned segment exactly once and in order, with no missing source
spans. Use inexpensive automated duration, silence and peak measurements to locate outliers and
suspicious endpoints. Compare outliers with their source and delivery action before calling them
defects; a single peak or unusual duration does not establish an audible problem.

These checks establish file integrity and planned coverage, not that every spoken word is correct.
Use unprompted ASR on sampled passages and suspected omissions, repetitions or truncations. Compare
each selected passage with its complete expected wording, including negation and phrase endings.
Do not feed that wording to the recognizer. Full-book ASR is optional when it is inexpensive and
keeps up with rendering; full-book phoneme and audio-language-model passes are not default gates.

## Review during rendering

Before bulk generation, review representative auditions and the first few minutes of the chosen
performance. Cover the voices, delivery extremes, longest clauses, verse/dialogue and difficult
names that actually occur. Confirm restrained intensity, intact words and endings, and natural
joins before letting the same settings propagate.

During rendering, select a random complete passage from newly available audio roughly every
15–20 minutes of generated listening time. A useful default is 20–40 seconds of speech per
checkpoint, with at least one random passage from each chapter or short work. Spread selection
across the program rather than repeatedly sampling its beginning. Record the random seed, eligible
segments, actual selected IDs/intervals and audio hashes so selection is reproducible. Snap to
complete phrases and include neighboring onsets/decays; respect a tool's window limit by splitting
explicitly. Targeted checks supplement the random sample rather than replacing it.

Inspect newly introduced voices, source forms, delivery settings and pronunciation cues when they
first appear. Recheck representative difficult names and exceptional clause joins; do not turn
every repeated name, voice transition or subdivision into a separate mandatory model request.
Continue review alongside generation using an available playback or qualified analysis tool.
Choose a method that can keep up; model benchmarking and competing reviewer backends are not part
of ordinary book production.

Judge intelligibility, unintended repeated/garbled words, consonants, breath/decay, clicks, abrupt
timbre changes, syntactic pauses and sustained pace against the source. Check whether warning,
exhortation or exaltation becomes aggressive or shouted prematurely. Review its lead-in and
release; reserve extreme force for an earned climax without flattening the rest of the acting.
Names should flow as whole words, without coaching-induced syllabic attacks. Necessary wording or
pronunciation-cue changes return to adaptation; numerical acting repairs use calibration.

## Targeted escalation and stopping

When a sample reveals a credible defect, inspect the complete affected phrase, its neighbors and a
few additional examples from the same setting, batch or delivery category. Repair the demonstrated
cause early and recheck the repair and its joins. If the problem recurs, widen review within that
affected scope and hold further generation using the implicated settings until corrected. A local
failure does not require replaying the whole book or checking every unrelated segment.

Triage automated flags into likely shared causes. Resolve a cause with contextual evidence and
reviewed examples instead of sending every spelling variant or weak-sound boundary to multiple
models. ASR can hallucinate additions as well as miss words; authored repetition and crop edges
must not be mistaken for generation defects. Do not retry seeds or rewrite source words solely
because a critic gives an unsupported description.

Sampling is sufficient when the early pilot and distributed rolling sample pass, demonstrated
material defects and affected neighborhoods are resolved, and the final mechanical and encoded
checks pass. Extra random samples or an exhaustive final sweep are not required merely because
unreviewed segments remain. State the sample coverage and bounded pronunciation/perceptual limits.

## Audio-model evidence

If using an audio-language model, pin the checkpoint, precision, input handling and prompt. Check
that actual audio features reach it, that it recognizes a real speech clip without its prose, and
that the chosen perceptual prompt distinguishes a clean clip from known damaged speech. Record
actual analyzed intervals and respect the audio-window limit. Reuse qualification for an unchanged
setup; do not repeat controls for every batch.

Reject unsupported event times, contradictory claims and generic assurances. Expand a disputed crop
to complete source phrases before inferring shouting, repetition or a cut. Treat the model as
fallible supplementary evidence, reconciled with source, playback or independent measurements.
If a prompt or backend fails its controls, withdraw its assurances and replace the affected sampled
review using a working method. Keep valid integrity/source evidence; do not convert the failed
review's entire historical interval inventory into a new exhaustive certification requirement.

## Final assembly and encoded delivery

Verify native sample preservation, declared gaps, source order and all chapter titles/times by
machine. Measure native-channel loudness, range and true peak before choosing any mastering, then
remeasure the actual encoded file. Gain, limiting, trims, fades or resampling need an evidenced
delivery benefit; another book's settings are not defaults.

Decode the delivered file and verify codec, rate/channels, duration, errors and complete segment
coverage. Check its beginning/end, a small fresh random sample and representative chapter seams,
plus repaired or suspect joins. Earlier native reviews remain valid for unchanged performances
when encoded integrity is verified; do not replay every native review window after encoding.
Navigation must follow the realized source-frame plan, with contiguous boundaries and the final
end agreeing with the probed duration within container tolerance.

Finish and export when the complete mechanical checks, progressive random sample, targeted repairs
and bounded encoded spot checks pass. If a genuine material defect or required sample review is
unresolved, report that specific limitation honestly; lack of exhaustive segment-by-segment review
alone is not a reason to hold a finished delivery.
