# External typing boundaries

`uv run basedpyright src tests` must report zero errors and warnings in strict mode. The checker
configuration disables no diagnostics, excludes no application modules, and rejects unnecessary
ignore comments. Application records use Pydantic models; persisted input is validated before its
fields enter domain logic. `Any`, casts, dynamic attribute access, and application-code exclusions
are not used to clear the checker.

## Inline exceptions

Each exception names one diagnostic on one external import or call. Removing it from the locked
environment reproduces that diagnostic; it does not justify suppressing errors in surrounding code.

| Boundary | Diagnostic | Evidence and justification |
| --- | --- | --- |
| `_Element` imports in `epub_structure.py` and `epub_sections.py` | `reportPrivateUsage` | lxml's [documented concrete element class](https://lxml.de/api/lxml.etree._Element-class.html) is named `_Element`. The installed `types-lxml==2026.2.16` signatures use that class for element factories and traversal. Importing it once as `Element` preserves those maintained types; only the underscore-name diagnostic is suppressed. |
| SoundFile imports in `assembly.py`, `rendering.py`, and `test_delivery.py` | `reportMissingTypeStubs` | The installed `soundfile==0.14.0` module annotates `read`, `write`, and `SoundFile`, including NumPy return types, but its distribution contains no `py.typed` marker. Package-file inspection reproduces the missing marker. Only the import diagnostic is suppressed; source annotations still check all audio calls and returned values. The real FFmpeg assembly test verifies sample preservation and M4B chapters. |
| `torch.manual_seed(segment.seed)` in `rendering.py` | `reportUnknownMemberType` | The locked Python 3.13 environment installs `torch==2.6.0`. Its `torch/random.py` defines `manual_seed(seed) -> torch._C.Generator`: the **seed parameter** lacks an annotation. Its implementation converts that argument with `int(seed)`. The [documented argument is an integer](https://docs.pytorch.org/docs/2.6/generated/torch.manual_seed.html); the caller supplies the Pydantic-validated integer `RenderSegment.seed`, with the generation plan enforcing the unsigned 32-bit seed range. The exclusion applies only to this member lookup, and the return value is unused. |

These are seven inline locations: two lxml imports, four SoundFile imports, and one PyTorch call.
No `# type: ignore`, file-wide directive, or general `Unknown` suppression is present.

An isolated-copy audit removed each exception class in turn: the checker produced exactly two
private-name errors, four missing-stub errors, and one unknown-member error, with no unrelated
diagnostics. A second static probe deliberately passed invalid arguments to seven external calls;
all seven remained errors, including an invalid SoundFile sample rate. These probes were not added
as redundant permanent tests of the type checker.

## Dependency interfaces

The packages below ship no usable typing metadata for the API this project uses in the locked distributions.
The narrow `.pyi` files under [typings](../typings/) describe those external interfaces; they do not
replace application implementations or claim to cover the entire upstream packages. Every declared
method, constructor, property, and return path was inspected in the installed locked source.
`uv run basedpyright typings` checks the declarations themselves.

| Package | Source inspected | Declared interface and evidence |
| --- | --- | --- |
| Panflute 2.3.1 | `panflute/base.py`, `elements.py`, `tools.py`, `io.py` | Element hierarchy, child sequences, attributes, document metadata, and conversion/load functions. `convert_text` explicitly branches between text, document, and element-list results; the application checks for text before using its result. `Doc.get_metadata()` with no arguments returns built-in metadata. Real admitted-source and script-codec tests exercise this interface. |
| EbookLib 0.20 | `ebooklib/__init__.py`, `epub.py` | Read-package spine, item and navigation classes, metadata, and item iteration. `get_content` can return its default (`None`); the declaration preserves that possibility, and callers provide empty bytes to the XML parser when content is absent. Metadata values remain `object` until converted by the existing string projection. EPUB 2/3, missing-target, hierarchy, and source-disagreement tests exercise these paths. |
| pypandoc-binary 1.17 | `pypandoc/__init__.py` | Only `get_pandoc_path()` and `get_pandoc_version()`, both returning strings. The installed source annotations and a direct runtime version query confirm these returns. |
| NLTK 3.10.3 | `nltk/tokenize/punkt.py` and tokenizer exports | `PunktTokenizer` construction and `span_tokenize`, whose implementation yields integer start/end pairs. The import remains lazy, so CLI help does not initialize the tokenizer. |
| Chatterbox 0.1.7 | Commit [`5de7a54`](https://github.com/resemble-ai/chatterbox/tree/5de7a54aa4e5e2baadb0182dde554908b48b85c2), recorded in `uv.lock` | `EnTokenizer.text_to_tokens` constructs an `IntTensor`; `T3Config.max_text_tokens` is an integer; `punc_norm` accepts and returns strings; `ChatterboxTTS.from_local` returns the model; `conds` can be absent; `generate` returns the synthesized tensor. The six control parameters are declared individually, and the call supplies their typed Pydantic fields explicitly. No model download or synthesis run is claimed by this typing audit. |

The lxml interface comes from the maintained `types-lxml` development dependency rather than a
local replacement. SoundFile source annotations and PyTorch's own types remain in use.
Recheck the local declarations and inline exceptions against installed source when updating the
corresponding locked dependencies.

## Serialization and existing artifacts

Typed records preserve supplied fields during JSON serialization with `exclude_unset=True`; absent
optional fields are not invented when computing hashes. Edition-specific provenance and ffprobe
metadata retain their extra fields. Those extras are serialized, never used as untyped application
state. Accepted records, source identities, frozen plans, and audio hashes retain their validation
guards. Runtime and dependency changes still require new render plans under the existing rules.
Read-only validation of 65 existing local production documents preserved their exact JSON hashes,
including historical choice and calibration provenance; it did not modify those artifacts or waive
their runtime-identity guards.
