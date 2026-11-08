# Withdrawn shared-neutral proposal — 2026-11-08

**Historical record, superseded.** The user rejected the design below. Its adoption claims and
production recommendation are withdrawn. The source-backed replacement research is in
[acting-evidence-2026-11-08.md](acting-evidence-2026-11-08.md) and the current SPEC. RSC and Hamlet
below are historical reading only; they supply no theory for the current single-textbook revision.
The identical-vector code change has been removed. Historical values are retained, compactly,
without claiming that they satisfy the new restraint requirement.


User-owned change: retain effective source-exact direction, reduce overacting, make high expressive
settings exceptional, explain material decisions with the defined vocabulary and native controls,
and ground audio judgments in actual features. A later request authorizes a complete Of Happiness
audiobook as the production exercise and prioritizes behavior-preserving code economy.

## Evidence and decision

- Inspected locked Chatterbox commit `5de7a54aa4e5e2baadb0182dde554908b48b85c2`, matching
  `.third-party/chatterbox` and `uv.lock`. Read `tts.py` completely, `models/t3/modules/cond_enc.py`,
  `T3.prepare_conditioning`, `prepare_input_embeds` and the original inference sampling loop.
  `exaggeration` is projected by a bias-free linear layer into a conditioning token. CFG's second
  branch ablates text embeddings, not speaker/emotion conditioning. The loop uses conditional logits
  plus CFG times their difference from the ablated branch, then repetition penalty, temperature,
  min-p, top-p, softmax and sampling. No stage-action semantics are encoded in these controls.
  [Pinned source](https://github.com/resemble-ai/chatterbox/tree/5de7a54aa4e5e2baadb0182dde554908b48b85c2/src/chatterbox).
- [Pinned upstream tips](https://github.com/resemble-ai/chatterbox/blob/5de7a54aa4e5e2baadb0182dde554908b48b85c2/README.md#original-chatterbox-tips)
  distinguish ordinary .5/.5 use from dramatic exaggeration around .7+ with lower CFG. Higher
  exaggeration can accelerate speech. This supports an ordinary starting policy, not predictions
  of exact feelings, rate or volume. Former registry: .55–1.0 exaggeration, .26–.4 CFG; seven of
  eight actions exceeded .7 exaggeration. That registry came from the deliberately over-acted
  diagnostic documented in `.agent/DIRECTION.md`; it is not evidence for ordinary publication.
- Studied Stanislavski, *An Actor Prepares*, Hapgood translation, chapter VII, pp. 121–137,
  especially objectives and action rather than forced emotional results; chapter XV, pp. 293–300,
  on relating local tasks to the whole. This supports preserving objectives and continuity while
  changing realization. Listener-directed audiobook objectives adapt theatrical partner-address;
  they are not a claim that Stanislavski prescribed narration to an audience.
  [Primary text](https://www.craftfilmschool.com/userfiles/files/An%20Actor%20Prepares.pdf).
- Studied Lyn Darnley/RSC, *Voice and Text Preparation Resource Pack*, pp. 2–5: developing argument,
  selective emphasis, inflection, textual antithesis, and the risk that imposed emotion obscures
  words. Adapted these as interpretive instructions, not unsupported pitch/stress controls.
  [RSC/BBC pack](https://downloads.bbc.co.uk/schools/teachers/offbyheart/obhs_voice_text_preparation.pdf).
- Read Shakespeare's *Hamlet* III.2, opening advice to players: proportionate action and restraint
  coexist with commitment; blandness is not the alternative to excess. Literary corroboration,
  not scientific evidence for a numeric model mapping.
  [Folger primary text](https://www.folger.edu/explore/shakespeares-works/hamlet/read/3/2/).

Adopted: all eight semantic actions initially share the upstream six-control defaults. This avoids
inventing eight unmeasured emotion-to-number correspondences. Existing source-exact scoring,
meaning, normalization boundaries, worker responsibilities, calibration provenance and legacy
compatibility remain. The .70 exception boundary is production policy informed by upstream dramatic
guidance; it is not a measured universal threshold. A dramatic brief remains legitimate but permits
an audition, not automatic acoustic acceptance. No new performance tier, schema, reference file or
agent phase is introduced. Parameters remain distinct instances for each action.

Replaced the old vector registry and its preserve-current-range rule; narrowed extreme-force
permission; added concise material decision reporting and feature-supported review. Ordinary prompts
need no new approval. Acoustic properties still require auditions. No research source can establish
that a particular number will sound educated on an untested voice.

## Verification boundaries

Author-inspection cases: a philosophical rebuttal stays CONVINCE without .84 exaggeration; a quoted
catastrophe need not become WARN; a true exhortation remains URGE at ordinary scale; a user-requested
dramatic climax may trial higher values with baseline comparison. A plain text-only edit does not
invoke acting direction. Same-vector actions must still reject wrong score lineage; regression
coverage explicitly checks that case. Structural validation does not establish perceptual quality.
No fresh-context before/after model comparison is claimed. The subsequent Of Happiness production
records auditions and bounded audio review in its own book workspace; it is a production exercise,
not proof of general superiority across voices and genres.

Executed authoring checks: 51 tests and ten subtests passed; Basedpyright reported zero errors or
warnings; Ruff and Black passed. Both edited skill entrypoints passed the installed skill-creator
structural validator; all local Markdown reference targets and director TOML resolved. The runtime
change removes 53 production Python lines (seven added, sixty removed); test additions preserve
vector rejection and explicitly reject action substitution despite equal parameter values. Reviewed
the neighboring brief, score, calibration, segmentation, persistence and delivery boundaries; retained
coverage, error handling, historical compatibility and render identities rather than removing
working functionality to reduce a count. The registry comprehension is ordinary typed Python and
creates a separate Parameters record per action. No new runtime API or dependency was added.

The Of Happiness production adds two scoped empirical comparisons (same voice, text, model and
seed). The old URGE .94/.28 realization has median voiced F0 120.65 Hz versus 98.00 at .5/.5,
and RMS is 3.20 dB higher; the mild CONVINCE comparison changes little. These support a conservative
policy in one voice, not universal emotion mappings. Acoustic review also caught a pitch estimator
lock in near-silence; active-frame energy masks and known-sine checks prevent that artifact from
becoming an acting claim. Attempted audio critics failed broader controls, so their assurances are
withdrawn. Runtime review wording now distinguishes supported acoustic judgments from unverified
perceptual or emotional claims; it does not impose an unavailable critic as a new approval stage.
Diagnostic reproduction of a prior high vector remains permitted outside delivery acceptance.
