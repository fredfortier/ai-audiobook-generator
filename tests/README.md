# Test audit and admission criteria

Every retained test needs an independently stated application failure and an input that exposes
it. A successful nominal call, repeated evaluation of the same input, a library round trip,
or an assertion already implied by declared types is insufficient. Tests of external parsing,
content identity, source relationships, filesystem state, and native audio behavior remain useful
when their result is not guaranteed by types.

Audit scope: every test function in this directory, the code it exercises, all source modules,
and bundled CLI commands. The original suite had 43 test functions. The initial audit at
`31f1794` retained 40 functions. The shared CLI adds three functions with six cases, bringing
the current suite to 43 functions (48 pytest cases, plus subtests).

The one-off mutation audit ran the suite against 38 domain faults in isolated source copies.
An unmodified isolated control passed. Every mutant was detected, and every retained test
function failed against at least one mutant. The table names a verified witness per test.
Mutations affected application code, never test assertions or third-party packages. These
witnesses establish discriminating cases, not exhaustive proof of correctness. The mutation
harness is an audit tool, not another permanent test framework or CI dependency.

## Retained tests

Each witness below was observed to fail the named test. All witnesses concern runtime content,
relationships, or external effects that the type system cannot establish.

### test_cli.py

The shared CLI's three additional fault variants were run in isolated source copies. Each was
detected by its corresponding test below. The subprocess tests invoke the installed entry point
from outside the repository, with Python as the parent process.

| Test | Application failure / required distinction | Detected fault |
| --- | --- | --- |
| `test_completion_binds_installed_command_and_resolves_nested_subcommands` | Bash, Zsh, and Fish scripts must bind the installed executable and its actual callback variable; callbacks must filter nested subcommands from a Python parent. | `broken-completion-binding`: change the generated script's callback variable. |
| `test_unsupported_completion_shell_fails_without_emitting_a_script` | An unsupported shell must produce an actionable error and nonzero process status, rather than a successful empty completion installation. | `unsupported-shell-success`: exit zero for an unsupported shell. |
| `test_preprocess_cli_preserves_reports_and_propagates_blocked_admission` | Installed command routing must preserve EPUB targets, propagate blocked admission as exit two, write its evidence, and refuse to overwrite an existing report. | `blocked-admission-success`: exit zero for blocked section selection. |

### test_acting_score.py

| Test | Application failure / required distinction | Detected fault |
| --- | --- | --- |
| `test_removed_letter_calls_do_not_reject_authored_letters` | Deleting an indexed letter call must preserve identical authored letters; reject an overaggressive call detector. | `retain-all-calls` in `adaptation.retained_note_call` |
| `test_retained_letter_call_is_rejected_at_its_source_position` | Retained indexed calls must block acceptance even after punctuation changes. | `drop-all-calls` in `adaptation.retained_note_call` |
| `test_removed_numeric_call_does_not_match_brackets_or_spacing` | Bracket removal and spacing changes must not make deleted numeric calls appear retained. | `retain-all-calls` in `adaptation.retained_note_call` |
| `test_removed_reference_punctuation_is_not_a_retained_call` | A surviving sentence period is not evidence that the deleted reference survived. | `retain-all-calls` in `adaptation.retained_note_call` |
| `test_score_rejects_source_gaps_and_evidence_outside_move` | A structurally typed move can omit a source character or cite evidence outside its span. | `allow-score-gaps` in `adaptation.check_score_moves` |
| `test_move_rejects_objective_without_listener_action` | A string objective must express the action on a listener; its Python type cannot enforce the grammar. | `allow-bad-objective` in `adaptation.validate_listener_objective` |
| `test_directed_beats_derive_vectors_from_actions_and_preserve_lineage` | Valid parameter objects can belong to the wrong action, or beats can omit a score move. | `allow-unregistered-vector` in `adaptation.check_disposition` |
| `test_directed_calibration_binds_action_moves_and_both_vectors` | A calibration record can carry valid fields but refer to another accepted move. | `ignore-calibration-lineage` in `rendering.validate_calibration_provenance` |

### test_adaptation_regressions.py

| Test | Application failure / required distinction | Detected fault |
| --- | --- | --- |
| `test_score_rejects_interleaved_units` | Per-unit coverage is insufficient when one unit's moves resume after another unit. | `allow-unit-interleaving` in `adaptation.check_score_moves` |
| `test_directed_fragment_preserves_accepted_move_lineage` | A real fragment file must be checked as directed work and reject an action/score-ID mismatch. | `drop-fragment-score` in `adaptation.checked_fragment` |
| `test_directed_revision_does_not_freeze_old_score_moves` | After real score and narration acceptance, a revision must not freeze previous score IDs before a new score exists. | `reuse-old-score-moves` in `adaptation.revise` |

### test_delivery.py

| Test | Application failure / required distinction | Detected fault |
| --- | --- | --- |
| `test_chapter_title_review_capitalizes_minor_word_after_full_stop` | A minor word after a full stop starts a new sentence and needs its capital preserved. | `ignore-title-sentence-start` in `assembly._is_title_case` |
| `test_chapter_title_review_rejects_inconsistent_minor_word_casing` | An internal minor word must not acquire inappropriate display capitalization. | `ignore-minor-title-casing` in `assembly._is_title_case` |
| `test_chapter_title_review_requires_contextual_evidence` | Whitespace-only strings satisfy a string type but do not attest a title review. | `allow-blank-title-evidence` in `assembly.reviewed_chapter_titles` |
| `test_export_requires_configured_directory` | Missing EXPORT_DIR must not silently select the process's working directory. | `ignore-export-root` in `delivery.export_m4b` |
| `test_verified_variant_exports_beside_existing_base_delivery` | Exporting a named performance must choose a sibling path and preserve the existing base book. | `collapse-performance-variants` in `delivery.export_m4b` |
| `test_verified_variant_replaces_only_the_expected_existing_export` | A wrong expected hash must leave existing bytes intact; the matching hash permits replacement. | `overwrite-unattested-export` in `delivery.export_m4b` |
| `test_export_rejects_unverified_delivery` | A hash-bound local file with a false verification flag must never enter the finished library. | `export-unverified-audio` in `delivery.export_m4b` |
| `test_explicit_three_chapter_assembly_and_aac_m4b_round_trip` | Real sample assembly and FFmpeg/ffprobe must preserve the three explicit chapters while excluding an ordinary subsection. | `drop-m4b-chapter-map` in `delivery.encode_m4b` |

### test_epub_sections.py

| Test | Application failure / required distinction | Detected fault |
| --- | --- | --- |
| `test_agreeing_nav_ncx_many_fragments_and_navigation_projection` | A NAV-only chapter label needs one authored title while a content heading retains its own title. | `lose-navigation-only-title` in `epub_sections._boundary_from_node` |
| `test_targetless_parent_path_and_stacked_hierarchy_are_preserved` | Targetless ancestry and stacked same-start chapter hierarchy must not become duplicate audio chapters. | `duplicate-stacked-chapters` in `epub_sections._coalesce_stacked_boundaries` |
| `test_material_source_or_content_label_disagreement_blocks` | Conflicting navigation labels and content labels must remain actionable blocking evidence. | `ignore-nav-ncx-disagreement` in `epub_sections._compare_sources` |
| `test_single_missing_fragment_degrades_but_multiple_missing_fragments_block` | One missing fragment can degrade to resource start; multiple missing fragments must not silently collapse there. | `collapse-missing-fragments` in `epub_sections._resolve_navigation_positions` |
| `test_structural_fallback_requires_semantics_or_section_plus_heading` | Generic headings and page breaks must not become chapters without corroborated structure. | `promote-generic-headings` in `epub_sections.structural_candidates` |
| `test_deficient_navigation_yields_to_stronger_repeated_structure_and_ignores_nonlinear` | A one-entry TOC must yield to repeated real chapter sections while excluding nonlinear notes. | `trust-deficient-navigation` in `epub_sections.select_sections` |
| `test_calibre_candidate_requires_and_records_content_corroboration` | A corroborated external candidate changes an otherwise blocked structural boundary decision. | `ignore-calibre-evidence` in `epub_sections.select_sections` |
| `test_package_version_selects_primary_navigation_when_both_sources_exist` | When both NAV and NCX exist, the EPUB package version determines their precedence. | `ignore-epub-version` in `epub_sections._select_primary_navigation` |
| `test_one_boundary_per_linear_resource_preserves_reading_order` | Valid ordered navigation is accepted; reversed navigation must block rather than silently reorder the book. | `ignore-navigation-order` in `epub_sections.select_sections` |

### test_epub_structure.py

| Test | Application failure / required distinction | Detected fault |
| --- | --- | --- |
| `test_inventory_preserves_both_navigation_sources_and_targetless_hierarchy` | Parsing must retain both navigation sources, a targetless parent, decoded fragments, and nonlinear spine evidence. | `discard-ncx-inventory` in `epub_structure.inventory_epub` |
| `test_multiple_missing_fragments_remain_distinct_fail_stop_evidence` | Unresolved fragment IDs must stay distinct and marked absent in the inventory. | `pretend-fragment-exists` in `epub_structure.resolve_target` |
| `test_target_normalization_rejects_external_and_package_escape` | URL-shaped strings must not resolve as trusted local package navigation. | `accept-external-nav` in `epub_structure.normalize_target` |

### test_exported_scripts.py

| Test | Application failure / required distinction | Detected fault |
| --- | --- | --- |
| `test_render_input_rejects_speech_changed_after_export` | Changing exported speech bytes invalidates its reviewed identity before rendering. | `ignore-script-hashes` in `adaptation.verify_exported_scripts` |
| `test_unbound_script_inventory_requires_reviewed_reexport` | A script inventory lacking export hashes must require re-export rather than enter rendering unbound. | `ignore-script-hashes` in `adaptation.verify_exported_scripts` |

### test_section_contract.py

| Test | Application failure / required distinction | Detected fault |
| --- | --- | --- |
| `test_navigation_only_title_projection_and_existing_heading_are_exact` | Projection must insert a missing navigation heading once, preserve an existing heading once, and retain prose order. | `duplicate-projected-heading` in `source_units.project_section_titles` |
| `test_admission_rejects_unrecorded_prepared_file_change` | Even a projection-preserving whitespace edit must invalidate frozen prepared-file identity. | `ignore-prepared-hash` in `source_units.admit` |
| `test_section_start_must_match_first_unit_of_contiguous_membership` | Rehashed section metadata must not move a section start past its first source unit. | `allow-shifted-section-start` in `source_units.sections` |
| `test_new_adaptation_contract_rejects_unmigrated_version_one` | An external version-one manifest must not satisfy an explicitly requested version-two admission. | `allow-legacy-admission` in `source_units.admit` |

### test_workspaces.py

| Test | Application failure / required distinction | Detected fault |
| --- | --- | --- |
| `test_unset_and_empty_environment_use_repository_default` | Unset, empty, and whitespace-only configuration must select the package root even from another current directory. | `use-caller-work-root` in `workspaces.workspace_dir` |
| `test_relative_work_path_uses_configured_root` | Relative book paths belong below WORKSPACE_DIR, which deliberately differs from the caller's directory. | `ignore-configured-work-root` in `workspaces.work_path` |
| `test_relative_work_path_cannot_escape_configured_root` | Both parent traversal and a symlink resolving outside the workspace must be rejected. | `allow-workspace-escape` in `workspaces.work_path` |

## Removed or replaced

| Previous check | Decision and evidence |
| --- | --- |
| `test_selection_identity_is_deterministic` | Removed: comparing two calls on the same parsed input neither identifies a domain failure nor provides an independent oracle. |
| `test_absolute_work_path_is_unchanged` | Removed: a nominal assertion of delegated `Path.resolve()` behavior. Configured-root and real traversal/symlink tests cover the application's path ownership. |
| `test_verified_delivery_exports_to_inferred_book_path` | Removed: its naming and byte-copy assertions duplicate the stronger sibling-export test, which also protects an existing base audiobook. |
| `test_plotinus_version_two_covers_units_and_binds_delivery_title` | Removed: successful admission and hard-coded fixture word/page totals were nominal snapshots. Replaced by frozen-file tamper rejection; chapter relationships remain tested in projection, admission, and real M4B delivery. |
| Invalid action literal and unknown `intensity` constructor assertions | Removed: these repeat the `Action` literal and strict model field definitions. Retained only the custom listener-objective grammar check. |
| Previous directed-revision fixture | Replaced: it stored excluded paratext and contained no narrated score IDs. The revised test accepts a real complete score and actual narration through the production APIs before checking that revision does not reuse their old lineage. |
| Six `unittest.main()` entrypoints | Removed: pytest is the repository's canonical runner. These alternate runners contributed no behavioral proof. |

Further discrimination repairs: EPUB 2/3 precedence now uses both NAV and NCX; resource-order
checking includes reversed navigation; workspace tests run from a different current directory
and include a real escaping symlink; fragment validation also rejects a wrong score ID. Source
gap evidence is otherwise valid, so removing the coverage guard really permits missing text.

## Dead-code audit

Reviewed all core modules and bundled CLI scripts with reference searches, an AST inventory,
Ruff's unused-binding rules, and Vulture at 60% and 100% confidence.

- Removed the `Parameters.finite` after-validator and its `math` import. All six fields already
  have finite lower and upper bounds. A direct probe of NaN and both infinities for every field
  produced 18 field-bound errors before the after-validator could run. No redundant permanent
  test of Pydantic's bounded-float behavior was added.
- Discarded eight unused unpacked results while preserving their calls and validation effects.
  Ruff `RUF059` now prevents unused unpacked bindings from accumulating again.
- No unreferenced production function was established. Apparent scanner findings are registered
  Typer commands, Pydantic validators, or serialized fields consumed by source/agent protocols.
  `project_section_titles` is an externally used preparation API documented by the skill.
  Deleting these based only on textual reference counts would break runtime entrypoints or data.

Removing the redundant validator changes the control-schema fingerprint. Old render plans remain
subject to their existing runtime-identity guards; verification imports do not bypass that change.

## CI

`.github/workflows/python-checks.yml` runs four independent, fail-fast-disabled matrix jobs using
uv, Python 3.13, and `uv sync --locked`: pytest, strict Basedpyright, Ruff, and Black. Only tests
install FFmpeg; no model download or GPU synthesis is required by this suite. Action references
are pinned to verified release commits. All four checks must pass. Strict typing covers both
application code and tests; the external typing boundaries and narrowly scoped exceptions are
documented in [typing-boundaries.md](../docs/typing-boundaries.md).
