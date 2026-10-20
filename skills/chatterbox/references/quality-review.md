# Audio quality review

Use decoded audio and the exact expected text from the frozen plan. Preserve quantitative reports, transcripts, sample locations and review decisions beside the rendered audio. A passing metric is evidence for its measured property only.

## Every segment

Verify finite nonempty samples, native sample rate/channel count, decoded frame count and saved-byte hash. Measure duration per word, active-speech ratio, leading/trailing/internal silence, RMS, peak, clipped-sample count and longest run, and DC offset. Use supported FFmpeg `astats`, `silencedetect`, `ebur128` or equivalent established tools where suitable. State the silence threshold/window used. Flag relative outliers and suspicious endpoints; a single peak sample does not establish an audible glitch.

Reconcile the complete expected speech with a supported ASR transcript. Use a backend that loads safely; never disable checkpoint safeguards. Do not supply expected prose as an ASR prompt when testing omissions. Inspect actual missing/repeated/extra phrases, especially first/last words, negation and the end of long clauses. Archaic spelling and proper-name transcription variants need local adjudication; normalizing a transcript must not hide a dropped word. Token-budget compliance does not prove that generation finished before its output ceiling.

Route each unexplained anomaly to localized playback or a supported audio-analysis tool. Check intelligibility, absence of doubled words/breaths, terminal consonants, natural breath/decay, clicks, buzz, abrupt timbre changes, and whether pauses complete syntax. ASR cannot certify preferred classical pronunciation or acting. The [Whisper model card](https://github.com/openai/whisper/blob/main/model-card.md) explicitly warns that its predictions can include words absent from the recording; independently adjudicate apparent additions as well as omissions.

When using an audio-language model, pin its checkpoint and use the installed processor's supported audio input. Verify that actual audio features reach the model; ignored keyword arguments can otherwise yield a plausible response from text alone. Record analyzed intervals, sample rate, any analysis resampling and the model's audio-window limit. Divide longer samples explicitly rather than allowing silent truncation. Verify that the analyzed interval contains the flagged occurrence; hearing the same word elsewhere or reviewing a prefix that excludes its endpoint cannot settle the flag. Before trusting free-form criticism, confirm that it recognizes a known real speech clip without providing its prose, and check claimed times against decoded intervals. Positive input features alone do not establish critic competence. Reject contradictory or unsupported descriptions; do not alter audio solely to satisfy them. Treat its observations as fallible supplementary evidence and reconcile them with acoustic measurements and source completion.

## Perceptual sample selection

During calibration review every selected audition and its adjacent joins. For a completed book, inspect opening and closing audio, every voice transition, every delivery category, every distinct source form, all difficult-name occurrences, all exceptional clause cuts, and every quantitative/ASR flag. Also choose representative unflagged passages from the beginning, middle and end of each substantial section. Record actual playback intervals and observations; sample counts alone are not a quality proof.

Judge delivery against the passage's rhetorical action: lucid exposition, a coherent question, contemplative elevation or an earned warning. Check sustained pace and contrast, including whether repeated generation subdivisions introduce artificial full stops. If a sample fails, expand review to the affected category or neighborhood and repair the implicated settings/segmentation rather than flatten the whole work.

Check whether a warning, exhortation or exaltation jumps prematurely into aggression, shouting or a
high-pitched register. Intensity should remain convincing at the scale of acting a letter to a
listener; extreme vocal force needs an exceptional, earned climax. Review the lead-in and release,
not just the loud passage in isolation. A correction passes when excessive force is reduced while
the passage retains its emotional commitment and contrast with its neighbors.

For names, listen for each name word to flow as a single word, with no artificial pauses or separate
syllabic attacks introduced by pronunciation coaching. Preserve natural breaks
between words of a multiword name. Compare the actual reading with the scoped intended form and
check consistency; return necessary spelling repairs to adaptation rather than inserting phonetic
separators into a frozen render request.

## Assembly and encoded delivery

Reconcile every planned segment exactly once and in order. Check joins using the terminal speech and next complete onset, preserving consonants and tails; inspect unusual silence and unexpected boundary peaks. Quantify pacing and silence over the full assembly, distinguishing declared gaps from generated pauses.

Measure native-channel Integrated, Momentary, Short-term loudness, LRA and True Peak before mastering. Choose any gain/limiting from the actual target and measurements; do not adopt another project's numbers as a default. Verify the resulting dynamics and encoded-file peaks instead of relying on the filter input settings.

Decode and inspect the delivered file itself: codec, channels/rate, duration, speech completeness, beginning/end, seams and navigation. Chapter order/titles must follow genuine source structure, times must follow realized audio, and the last boundary must agree with probed duration within container tolerance. Re-run affected checks after repairs. If perceptual evidence is unavailable, report that limitation and leave polished-audio acceptance unresolved.
