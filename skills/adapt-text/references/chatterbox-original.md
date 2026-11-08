# Original English Chatterbox handoff

Target `ChatterboxTTS.generate`, not multilingual, Turbo, Nano or a hosted API. Its direct controls are `exaggeration`, `cfg_weight`, `temperature`, `repetition_penalty`, `min_p`, `top_p`, plus `audio_prompt_path` selected from the voice registry. [Original API](https://github.com/resemble-ai/chatterbox/blob/5de7a54aa4e5e2baadb0182dde554908b48b85c2/src/chatterbox/tts.py) and [original-model guidance](https://github.com/resemble-ai/chatterbox/blob/5de7a54aa4e5e2baadb0182dde554908b48b85c2/README.md#original-chatterbox-tips).

The upstream defaults are .5, .5, .8, 1.2, .05, 1.0. Exaggeration is one scalar intensity condition, not separate joy, grief, pitch or emphasis controls. Temperature and probability filters affect sampling; repetition penalty is a reliability trim. CFG affects conditioning and may affect pacing, but is not a duration control. Extreme settings require auditions. CFG zero is outside narration policy and must not be assumed safe.

In the pinned original code, `generate` supplies `exaggeration` as `T3Cond.emotion_adv`;
`T3CondEnc` applies a learned bias-free `Linear(1, n_channels)` projection and concatenates it
with the speaker and reference-prompt conditioning. The two CFG branches share that conditioning;
the second branch zeros the text embeddings before adding position embeddings. The sampling loop
uses `cond + cfg_weight * (cond - uncond)`, then repetition penalty, temperature division, min-p,
top-p, softmax and multinomial sampling. Thus lowering CFG does not remove emotion conditioning,
and lowering temperature does not select a calmer emotion. The implementation provides no equation
from an acting verb to a particular audible feeling, stress, pitch, rate or loudness.

Upstream recommends .5/.5 for ordinary use, with about .7 or higher exaggeration and lower CFG
for dramatic speech; it also reports that higher exaggeration tends to accelerate speech. These
are empirical tendencies, not timing guarantees. Use [performance.md](performance.md) for the
calibration status and exceptional-trial boundary; select settings from matched evidence.

Passing no reference after a custom voice can reuse the previous conditionals. A renderer must explicitly restore each voice, including returning to `builtin`. Original reference preparation uses the first six seconds for speech tokens and first ten for decoder conditioning; prefer clean representative speech, without claiming these windows mandate a precise file length.

The public generation path caps output at one thousand speech tokens. This does not guarantee completion of long input. Plan coherent sentence subdivisions using the original tokenizer after upstream `punc_norm`; start at no more than two hundred twenty text tokens per generation and verify actual completion in audio. A smaller calibrated target may be needed. Preserve the parent beat's voice and numeric values. An unavailable tokenizer leaves segmentation unverified; another model's tokenizer cannot certify readiness.

Preview upstream punctuation changes: semicolons and colons become commas, ellipses become commas, curly quotes become straight quotes, dashes are rewritten and whitespace is collapsed. Typographic punctuation cannot specify exact pause timing. Structural pauses need explicit silence insertion in the renderer, with listening checks at joins.

Original Chatterbox does not accept SSML, native laugh tags, `language_id`, phonemes, exact pitch/rate/gain or phrase-level pause milliseconds. Seed configures runtime RNG, not a generation keyword or script field. Text validation cannot establish pronunciation, completed speech, voice similarity, glitches or acceptable pacing.
