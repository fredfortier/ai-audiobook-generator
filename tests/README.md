# Test admission and current retention audit

Probe uncertain behavior with disposable scripts before editing. Retain a durable test only when
its input distinguishes a concrete application regression beyond declared types. Nominal smoke
checks, configuration snapshots, implementation mirrors, and mocks are inadmissible.

The workspace migration removed the constant-only action-profile test, two nominal path checks,
and duplicate encoding coverage. Export/environment scenarios now use real subprocesses and files;
no mocks or monkeypatches remain. The retained path test uses a real escaping symlink.

Each row states the independent failure witness justifying retention. The isolated control passed;
all 28 injected domain faults were detected, and every retained test failed against at least one.
These are bounded regression witnesses, not exhaustive proof. Mutation artifacts and the Hypostasis
excerpt production stay outside the repository; they are development evidence, not test machinery.

| Test | Discriminating witness |
| --- | --- |
| `test_literal_markup_and_verse_survive_without_becoming_formatting` | Literal markup/verse must survive Pandoc; duplicate attributes, unscoped prose, and unknown controls must be rejected. |
| `test_encoding_rejects_actual_metadata_or_timing_mismatch` | Real FFmpeg output with conflicting title, chapter title, or timing must fail without leaving a partial delivery. |
| `test_verse_line_boundaries_cannot_be_flattened_during_normalization` | Flatten a verse newline while retaining its words; fidelity validation must reject it. |
| `test_removed_letter_calls_do_not_reject_authored_letters` | Remove indexed letter calls while retaining identical authored letters elsewhere. |
| `test_retained_letter_call_is_rejected_at_its_source_position` | Keep an indexed call while changing punctuation; it must still be detected. |
| `test_removed_numeric_call_does_not_match_brackets_or_spacing` | Distinguish removed numeric calls from retained words and surrounding brackets. |
| `test_removed_reference_punctuation_is_not_a_retained_call` | A surviving full stop is not the deleted bibliographic reference. |
| `test_score_rejects_source_gaps_and_evidence_outside_move` | Reject a missing source character and evidence taken from a different move. |
| `test_move_rejects_objective_without_listener_action` | A nonempty grammatical-looking string can still fail the owned listener-objective grammar. |
| `test_directed_beats_derive_vectors_from_actions_and_preserve_lineage` | Independently corrupt numeric vector, action, and move order; each must fail. |
| `test_directed_calibration_binds_action_moves_and_both_vectors` | A valid calibration record referencing a different accepted move must fail. |
| `test_score_rejects_interleaved_units` | Interleave otherwise complete unit moves; per-unit coverage must not admit reordered source. |
| `test_directed_fragment_preserves_accepted_move_lineage` | A real fragment draft with substituted action/move lineage must fail acceptance validation. |
| `test_directed_revision_does_not_freeze_old_score_moves` | Accept real directed work, revise it, and reject reuse of obsolete score identities. |
| `test_completion_binds_installed_command_and_resolves_nested_subcommands` | Real shell callbacks must filter nested commands when invoked from a Python parent. |
| `test_unsupported_completion_shell_fails_without_emitting_a_script` | An unknown shell must fail with exit two and no executable completion output. |
| `test_preprocess_cli_preserves_reports_and_propagates_blocked_admission` | The installed CLI must propagate broken-fragment refusal and preserve an existing report. |
| `test_runtime_resources_and_relative_preparation_paths_survive_external_callers` | Run from another directory; preparation/revision paths and bundled instruction resources must remain correct. |
| `test_chapter_title_case_distinguishes_sentence_starts_from_minor_words` | Contrast internal minor words with sentence starts; reject whitespace-only review evidence. |
| `test_export_keeps_base_and_replaces_only_expected_variant_bytes` | Use real files and subprocesses; preserve base bytes and reject a stale replacement hash. |
| `test_export_rejects_unverified_delivery_without_creating_library` | A hash-matching file with a false verification flag must not enter the library. |
| `test_assembly_preserves_samples_and_excludes_subheadings_from_navigation` | Four distinct recordings include only three delivery starts; compare exact PCM, chapters, and actual encode-to-export interoperability. |
| `test_agreeing_nav_ncx_many_fragments_and_navigation_projection` | Distinguish a retained content heading from a navigation-only title in the same resource. |
| `test_targetless_parent_path_and_stacked_hierarchy_are_preserved` | Preserve a label-only parent, co-located hierarchy, and a genuine separate parent boundary. |
| `test_material_source_or_content_label_disagreement_blocks` | Conflicting NCX/NAV labels and content headings must block automatic section admission. |
| `test_single_missing_fragment_degrades_but_multiple_missing_fragments_block` | Only one unambiguous missing fragment can degrade to resource start. |
| `test_structural_fallback_requires_semantics_or_section_plus_heading` | Decorative headings, filename conventions, and page markers must not become chapters. |
| `test_deficient_navigation_yields_to_stronger_repeated_structure_and_ignores_nonlinear` | Incomplete navigation must not discard a stronger second structural section or include nonlinear matter. |
| `test_calibre_candidate_requires_and_records_content_corroboration` | An uncorroborated structural guess blocks; a matching external candidate must retain its evidence. |
| `test_package_version_selects_primary_navigation_when_both_sources_exist` | The same two navigation sources have different authority in EPUB 2 and EPUB 3. |
| `test_one_boundary_per_linear_resource_preserves_reading_order` | Reverse navigation across two actual resources; selection must detect nonmonotonic order. |
| `test_inventory_preserves_both_navigation_sources_and_targetless_hierarchy` | An encoded target, targetless parent, and nonlinear spine item must retain separate evidence. |
| `test_multiple_missing_fragments_remain_distinct_fail_stop_evidence` | Two absent fragments in one existing resource must remain distinct unresolved targets. |
| `test_target_normalization_rejects_external_and_package_escape` | External URLs and parent traversal must not become ordinary package targets. |
| `test_render_input_rejects_speech_changed_after_export` | Change a script byte after export; rendering must reject its stale identity. |
| `test_unbound_script_inventory_requires_reviewed_reexport` | A script inventory without matching hashes cannot establish reviewed rendering inputs. |
| `test_export_preserves_narrated_span_ledger` | Export real accepted batches; reconcile every narrated beat with its provenance ledger. |
| `test_navigation_only_title_projection_and_existing_heading_are_exact` | Insert only the missing navigation title; preserve an existing heading and exact section membership. |
| `test_admission_rejects_unrecorded_prepared_file_change` | Mutate the retained Markdown without changing its manifest hash; admission must fail. |
| `test_section_start_must_match_first_unit_of_contiguous_membership` | Change a section start and recompute its file hash; semantic spine validation must still fail. |
| `test_new_adaptation_contract_rejects_unmigrated_version_one` | A readable legacy bundle still lacks the explicit section contract required for new adaptation. |
| `test_relative_work_paths_reject_parent_and_symlink_escapes` | Real subprocesses and a real symlink must not escape the configured work root. |
