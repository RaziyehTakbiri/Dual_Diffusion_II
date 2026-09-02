"""Hostile zero-execution tests for the CP64 production-custody preflight."""

from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass
import gc
import hashlib
import inspect
import json
from pathlib import Path, PurePosixPath
import pickle
import subprocess
import sys
import threading
import weakref

import pytest

from heterodiff.evaluation import (
    mixed_initializer_test28_production_custody_preflight as cp64,
)

if sys.version_info >= (3, 10):
    from heterodiff.evaluation import (
        mixed_initializer_test28_independent_recomputation as independent,
    )
    from heterodiff.evaluation import (
        mixed_initializer_test28_runner_recomputation_rehearsal as runner,
    )
else:  # CP63's historical dataclass(slots=True) declarations are not Py3.9 syntax.
    independent = None
    runner = None


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_production_custody_preflight.py"
)
_RUNNER_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_runner_recomputation_rehearsal.py"
)
_INDEPENDENT_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_independent_recomputation.py"
)
_V14_PROTOCOL = (
    _ROOT / "research" / "preregistrations" / "cp50_test28_mixed_initializer_v1.md"
)
_V14_MANIFEST = (
    _ROOT / "research" / "fixtures" / "cp50_test28_mixed_initializer_v1.json"
)
_PYTHON39 = Path("/Users/mahtab/opt/anaconda3/bin/python3.9")
_ZERO_SHA256 = "0" * 64

_EXPECTED_FIELDS = {
    cp64.CP64PredecessorCustodyV1: (
        "schema_version",
        "cp63_protocol_relative_path",
        "cp63_protocol_sha256",
        "cp63_protocol_bytes",
        "cp63_protocol_lines",
        "cp63_machine_manifest_relative_path",
        "cp63_machine_manifest_sha256",
        "cp63_machine_manifest_bytes",
        "cp63_machine_manifest_lines",
        "cp63_protocol_id",
        "cp63_protocol_state",
        "cp63_manifest_schema_version",
        "cp63_bound_artifact_count",
        "cp63_development_verification_record_count",
        "cp63_ledger_total_count",
        "cp63_ledger_satisfied_count",
        "cp63_ledger_missing_count",
        "cp63_aggregate_test_count",
        "cp63_lifecycle_current_state",
        "cp63_v14_allowed_attempt_states",
        "cp63_v14_transition_graph",
        "cp63_freeze_state",
        "cp63_confirmatory_execution_authorized",
        "cp63_formal_test_28_status",
        "cp63_formal_test_28_closed",
        "cp61_stable_design_sha256",
        "cp62_source_sha256",
        "cp62_bundle_sha256",
        "cp62_runtime_lock_record_sha256",
        "cp62_supervisor_contract_record_sha256",
        "cp62_projection_contract_record_sha256",
        "cp63_runner_source_sha256",
        "cp63_runner_bundle_record_sha256",
        "cp63_schedule_contract_record_sha256",
        "cp63_seed_capsule_contract_record_sha256",
        "cp63_lifecycle_contract_record_sha256",
        "cp63_raw_record_schema_record_sha256",
        "cp63_resource_contract_record_sha256",
        "cp63_independent_source_sha256",
        "cp63_independent_bundle_record_sha256",
        "cp63_independent_bundle_public_sha256",
        "cp63_acceptance_receipt_sha256",
        "cp63_semantic_pin_receipt_sha256",
        "dependency_lock_path",
        "dependency_lock_sha256",
        "cp64_source_hash_in_record",
        "cp64_source_hash_external_binding_required",
        "predecessor_custody_only",
        "complete_production_source_manifest_present",
        "production_runtime_match_verified",
        "record_sha256",
    ),
    cp64.CP64ExternalSeedSourceReceiptSchemaV1: (
        "schema_version",
        "receipt_schema",
        "purpose",
        "exact_keys",
        "acquisition_start_receipt_exact_keys",
        "partial_acquisition_terminal_receipt_exact_keys",
        "acquisition_start_receipt_relative_path",
        "partial_acquisition_terminal_receipt_relative_path",
        "acquisition_journal_relative_path",
        "acquisition_journal_encoding",
        "acquisition_journal_entry_bytes",
        "acquisition_journal_max_entries",
        "acquisition_journal_max_bytes",
        "acquisition_journal_initial_head_formula",
        "acquisition_journal_entry_digest_formula",
        "acquisition_journal_entry_field_order",
        "acquisition_journal_entry_ordinals_strictly_increasing_from_one",
        "acquisition_journal_exclusive_create_required",
        "acquisition_journal_nofollow_required",
        "acquisition_journal_non_sparse_physical_allocation_required",
        "acquisition_journal_file_fsync_before_acquisition_start_receipt_required",
        "acquisition_journal_directory_fsync_before_acquisition_start_receipt_required",
        "acquisition_journal_path_inode_recheck_before_acquisition_start_receipt_required",
        "acquisition_journal_path_inode_recheck_before_each_entry_append_required",
        "acquisition_journal_preallocated_before_source_contact",
        "acquisition_journal_entry_fsync_before_next_source_draw",
        "acquisition_journal_every_entry_including_final_entry_fsync_required",
        "acquisition_journal_final_fsync_before_completed_source_receipt_required",
        "acquisition_journal_no_resume_after_crash",
        "acquisition_journal_recovery_terminal_state",
        "acquisition_journal_topup_redraw_reselection_permitted",
        "acquisition_journal_recovery_accepts_only_longest_valid_fsynced_prefix",
        "acquisition_journal_torn_or_invalid_suffix_is_not_value_evidence",
        "attempt_binding_required",
        "freeze_receipt_binding_required",
        "seed_count",
        "seed_encoding",
        "sequence_commitment_formula",
        "receipt_digest_formula",
        "capsule_body_digest_bound_by_source_receipt",
        "source_receipt_digest_referenced_by_capsule",
        "capsule_sequence_commitment_crosscheck_required",
        "completed_source_receipt_binds_acquisition_journal_sha_head_and_count",
        "completed_journal_entry_count_must_equal_seed_count",
        "completed_journal_head_must_equal_entry_digest_at_seed_count",
        "completed_journal_ordinal_value_sequence_commitment_must_equal_source_receipt_ordered_seed_values_commitment",
        "capsule_ordered_seed_values_commitment_must_equal_completed_journal_sequence_commitment",
        "canonical_syntax_can_prove_iid",
        "digest_can_authenticate_source",
        "acquisition_start_receipt_required",
        "acquisition_start_receipt_exclusive_create_required",
        "acquisition_start_receipt_file_fsync_required",
        "acquisition_start_receipt_directory_fsync_required",
        "acquisition_start_must_be_durably_committed_before_source_contact",
        "acquisition_session_sha256_is_start_receipt_sha256",
        "committed_acquisition_start_receipt_spends_attempt",
        "any_durable_external_seed_value_spends_attempt",
        "source_return_without_journal_fsync_spends_attempt",
        "source_return_without_journal_fsync_terminal_state",
        "source_return_without_journal_fsync_value_is_claimed_retained",
        "source_return_without_journal_fsync_resume_topup_redraw_permitted",
        "durably_journaled_partial_acquisition_values_must_be_retained",
        "partial_acquisition_terminal_receipt_required",
        "partial_acquisition_terminal_state",
        "partial_acquisition_topup_redraw_reselection_permitted",
        "receipt_values_present",
        "source_authority_verified",
        "record_sha256",
    ),
    cp64.CP64ProductionRuntimeReceiptSchemaV1: (
        "schema_version",
        "receipt_schema",
        "purpose",
        "exact_keys",
        "cp62_candidate_runtime_lock_sha256",
        "dependency_lock_sha256",
        "complete_source_manifest_required",
        "cp64_source_external_binding_required",
        "preimport_environment_required",
        "loaded_local_source_closure_required",
        "compiled_abi_map_required",
        "receipt_attempt_binding_required",
        "receipt_freeze_binding_required",
        "observation_must_postdate_freeze",
        "receipt_present",
        "full_runtime_lock_recomputed",
        "production_runtime_match_verified",
        "record_sha256",
    ),
    cp64.CP64CapacityReceiptSchemaV1: (
        "schema_version",
        "receipt_schema",
        "purpose",
        "exact_keys",
        "cp63_resource_contract_record_sha256",
        "global_payload_ceiling_bytes",
        "global_destination_reservation_bytes",
        "global_auxiliary_metadata_conservative_policy_reservation_bytes",
        "global_combined_available_and_quota_required_before_reservation_bytes",
        "global_available_and_quota_required_after_destination_before_auxiliary_reservation_bytes",
        "auxiliary_metadata_reservation_is_conservative_policy_floor",
        "complete_auxiliary_artifact_size_schema_frozen",
        "bounded_auxiliary_artifact_size_proof_required_before_capacity_pass",
        "bounded_auxiliary_artifact_size_proof_present",
        "auxiliary_metadata_must_fit_exclusive_auxiliary_reservation",
        "acquisition_journal_maximum_bytes",
        "acquisition_journal_counted_within_auxiliary_metadata_reserve",
        "per_shard_payload_ceiling_bytes",
        "per_shard_destination_reservation_bytes",
        "candidate_shard_count",
        "minimum_available_inodes",
        "combined_available_and_quota_before_reservation_each_must_meet_floor",
        "before_reservation_available_and_quota_each_meet_combined_floor_required",
        "after_destination_before_auxiliary_available_and_quota_each_meet_auxiliary_floor_required",
        "destination_and_auxiliary_reservations_both_exclusive_required",
        "destination_and_auxiliary_reservations_no_double_count_required",
        "auxiliary_metadata_reservation_method_rule",
        "auxiliary_metadata_physical_and_quota_reservations_both_required",
        "quota_only_auxiliary_reservation_sufficient",
        "auxiliary_metadata_reservation_artifact_relative_path",
        "auxiliary_metadata_reservation_same_storage_root_required",
        "auxiliary_metadata_reservation_retained_until_committed",
        "auxiliary_metadata_reservation_consumed_in_place_and_enforced_quota_required",
        "post_destination_free_space_or_quota_snapshot_alone_sufficient",
        "same_filesystem_required",
        "measurement_must_postdate_freeze",
        "measurement_must_predate_authorization",
        "reservation_receipt_required",
        "non_sparse_reservation_required",
        "reservation_same_filesystem_required",
        "destination_effective_reservation_formula",
        "auxiliary_effective_reservation_formula",
        "combined_effective_reservation_formula",
        "capacity_pass_predicate",
        "snapshot_only_sufficient",
        "jsonl_record_encoding",
        "jsonl_record_kinds",
        "jsonl_newline_bytes_per_record",
        "stderr_record_encoding",
        "stderr_length_prefix_bytes",
        "stderr_payload_max_bytes",
        "stderr_records_per_shard",
        "stderr_trailing_bytes_permitted",
        "seed_capsule_encoding",
        "seed_capsule_final_newline_bytes",
        "payload_ceilings_include_storage_framing",
        "capacity_receipt_present",
        "capacity_measured",
        "minimum_capacity_satisfied",
        "production_resources_allocated",
        "record_sha256",
    ),
    cp64.CP64DurabilityReceiptSchemaV1: (
        "schema_version",
        "receipt_schema",
        "purpose",
        "exact_keys",
        "global_relative_paths",
        "per_shard_relative_paths",
        "global_relative_paths_scope",
        "conditional_relative_paths",
        "conditional_path_rules",
        "complete_source_receipt_and_partial_terminal_receipt_mutually_exclusive",
        "relative_path_rule",
        "temporary_suffix",
        "exclusive_create_required",
        "symlinks_permitted",
        "hardlinks_permitted",
        "overwrite_permitted",
        "append_after_commit_permitted",
        "same_directory_atomic_rename_required",
        "file_fsync_before_rename_required",
        "directory_fsync_after_rename_required",
        "canonical_jsonl_final_newline_required",
        "stderr_frame_offsets_lengths_and_sha256_bound_in_shard_index",
        "raw_retained_separately",
        "stable_projection_never_replaces_raw",
        "shard_receipt_committed_last",
        "terminal_order",
        "launch_authorization_prepared_partial_relative_path",
        "rejected_launch_authorization_candidate_relative_path",
        "preauthorization_outcome_relative_path",
        "preauthorization_outcome_exact_keys",
        "preauthorization_outcome_allowed_arms",
        "preauthorization_outcome_exclusive_create_and_nofollow_required",
        "preauthorization_outcome_file_and_directory_fsync_required",
        "authorization_candidate_must_be_o_excl_nofollow_written_and_fsynced_as_partial_before_authorization_arm",
        "authorization_arm_requires_nonzero_matching_prepared_authorization_sha256",
        "authorization_arm_recovery_publishes_verified_prepared_bytes_by_rename_no_replace_and_directory_fsync",
        "preauthorization_terminal_arm_requires_terminal_state_equal_arm",
        "preauthorization_terminal_arm_never_publishes_final_launch_authorization",
        "losing_prepared_authorization_candidate_is_retained_under_rejected_non_authorizing_path",
        "preauthorization_outcome_crash_recovery_completes_winner_without_reselection",
        "preauthorization_outcome_losers_refuse_without_side_effects",
        "postauthorization_outcome_relative_path",
        "postauthorization_outcome_exact_keys",
        "postauthorization_outcome_allowed_arms",
        "postauthorization_outcome_requires_durable_final_launch_authorization",
        "postauthorization_outcome_exclusive_create_and_nofollow_required",
        "postauthorization_outcome_file_and_directory_fsync_required",
        "postauthorization_started_and_terminal_arms_mutually_exclusive",
        "postauthorization_outcome_crash_recovery_completes_winner_without_reselection",
        "postauthorization_outcome_losers_refuse_without_side_effects",
        "started_arm_effects_frozen_to_started_transition",
        "crash_after_started_arm_before_started_receipt_recovers_started_then_incomplete_without_production_rng_or_child",
        "crash_after_terminal_arm_before_terminal_receipt_completes_same_terminal_without_reselection",
        "both_outcome_receipts_retained_and_manifest_bound_at_committed",
        "started_receipt_must_bind_postauthorization_started_outcome",
        "terminal_state_must_bind_winning_terminal_outcome",
        "proposed_v15_preauthorization_terminal_states",
        "proposed_v15_preauthorization_crash_cuts",
        "proposed_v15_preauthorization_terminal_order",
        "proposed_v15_preauthorization_forbidden_stages",
        "preauthorization_terminal_retains_all_durable_artifacts",
        "preauthorization_terminal_state_binds_durable_artifact_inventory",
        "preauthorization_sha256_manifest_binds_all_durable_prestart_artifacts",
        "preauthorization_committed_marker_transitively_binds_all_durable_prestart_artifacts",
        "proposed_v15_postauthorization_prestart_terminal_states",
        "proposed_v15_postauthorization_prestart_crash_cut",
        "proposed_v15_postauthorization_prestart_terminal_order",
        "proposed_v15_postauthorization_prestart_forbidden_stages",
        "postauthorization_prestart_terminal_retains_launch_authorization",
        "postauthorization_prestart_terminal_state_binds_launch_authorization",
        "postauthorization_prestart_sha256_manifest_binds_launch_authorization",
        "postauthorization_prestart_committed_marker_transitively_binds_launch_authorization",
        "auxiliary_metadata_reservation_relative_path",
        "auxiliary_metadata_reservation_retained_until_committed",
        "auxiliary_metadata_reservation_manifest_bound_at_committed",
        "reservation_destination_final_path_templates",
        "reservation_allocation_unit_rule",
        "reservation_partition_formula",
        "reservation_per_shard_total_bytes",
        "reservation_global_total_bytes",
        "reservation_manifest_binds_per_file_reserved_bytes",
        "reservation_partial_path_formula",
        "reservation_uses_actual_destination_partial_inodes",
        "reservation_manifest_binds_path_device_inode_extents_logical_and_allocated_bytes",
        "reservation_files_exclusive_non_sparse_preallocated",
        "writer_consumes_reserved_partial_inodes_in_place",
        "reservation_handoff_requires_inode_identity_match",
        "reservation_qualification_verifies_in_place_overwrite_without_copy_on_write_double_allocation",
        "reserved_partial_truncation_only_after_complete_write_and_followed_by_file_fsync",
        "reserved_partial_files_absent_at_committed",
        "reservation_manifest_retained_and_manifest_bound_at_committed",
        "reservation_manifest_required",
        "reserved_destination_commit_order",
        "rename_no_replace_required",
        "cow_no_double_allocation_qualification_required",
        "cow_no_double_allocation_qualified",
        "committed_marker_exact_keys",
        "committed_marker_relative_path",
        "sha256_manifest_excludes_itself_and_committed_marker",
        "committed_marker_binds_terminal_state_and_sha256_manifest",
        "committed_marker_exclusive_create_required",
        "committed_marker_file_fsync_required",
        "committed_marker_directory_fsync_required",
        "committed_marker_created_after_terminal_and_manifest",
        "committed_marker_is_only_publication_boundary",
        "receipt_present",
        "writer_implemented",
        "writer_qualified",
        "filesystem_observed",
        "durable_output_written",
        "record_sha256",
    ),
    cp64.CP64CandidateShardV1: (
        "schema_version",
        "shard_ordinal",
        "shard_id",
        "relative_directory",
        "seed_ordinal_min",
        "seed_ordinal_max",
        "seed_ordinal_count",
        "logical_request_ordinal_min",
        "logical_request_ordinal_max",
        "logical_request_count",
        "all_sixteen_rows_per_seed_collocated",
        "logical_requests_strictly_increasing",
        "rejection_proposal_slot_count",
        "sir_proposal_slot_count",
        "total_proposal_slot_count",
        "sir_resampling_draw_count",
        "maximum_event_occurrence_count",
        "maximum_coordinate_count",
        "raw_ceiling_bytes",
        "stable_ceiling_bytes",
        "request_ceiling_bytes",
        "stderr_ceiling_bytes",
        "payload_ceiling_bytes",
        "candidate_destination_reservation_bytes",
        "definition_only",
        "selected_for_production",
        "instantiated",
        "record_sha256",
    ),
    cp64.CP64CandidateShardPolicyV1: (
        "schema_version",
        "policy_id",
        "cp63_schedule_contract_record_sha256",
        "cp63_resource_contract_record_sha256",
        "capacity_receipt_schema_record_sha256",
        "durability_receipt_schema_record_sha256",
        "mapping_formula",
        "shard_count",
        "seed_count",
        "row_count",
        "total_request_count",
        "seed_ordinals_per_shard",
        "logical_requests_per_shard",
        "shard_ordinals",
        "shards",
        "same_seed_rows_collocated",
        "duplicate_seed_values_distinguished_by_ordinal",
        "historical_pre_cp61_eight_shard_plan_inherited",
        "candidate_policy_frozen",
        "candidate_policy_selected_for_production",
        "production_shard_map_bound",
        "production_shard_map_instantiated",
        "record_sha256",
    ),
    cp64.CP64ProductionShardMapReceiptSchemaV1: (
        "schema_version",
        "receipt_schema",
        "purpose",
        "exact_keys",
        "shard_record_exact_keys",
        "exactly_32_candidate_shard_records_required",
        "shard_ordinals_strictly_increasing_unique_1_through_32",
        "logical_ordinal_ranges_contiguous_nonoverlapping_cover_1_through_32768",
        "seed_ordinal_ranges_contiguous_nonoverlapping_cover_1_through_2048",
        "shard_record_candidate_equality_field_pairs",
        "shard_record_candidate_fields_must_equal_candidate_record",
        "relative_directory_must_equal_candidate_shard_relative_directory",
        "per_file_reservation_manifest_entry_sha256_required_for_each_reserved_partial",
        "shard_record_per_file_reservation_link_order",
        "shard_record_per_file_reservation_links_exactly_four",
        "shard_record_per_file_reservation_link_digests_exact_nonzero_sha256",
        "shard_record_per_file_paths_match_candidate_templates",
        "shard_record_per_file_reserved_bytes_sum_to_candidate_destination_reservation_bytes",
        "each_shard_capacity_partition_bytes",
        "all_shard_capacity_partition_sum_bytes",
        "all_shard_capacity_partition_sum_equals_global_destination_reservation",
        "shard_record_digest_formula",
        "candidate_shard_policy_sha256",
        "mapping_formula",
        "shard_count",
        "attempt_binding_required",
        "reservation_manifest_binding_required",
        "receipt_present",
        "candidate_policy_selected_for_production",
        "production_shard_map_bound",
        "production_shard_map_instantiated",
        "record_sha256",
    ),
    cp64.CP64LaunchAuthorizationReceiptSchemaV1: (
        "schema_version",
        "receipt_schema",
        "purpose",
        "exact_keys",
        "proposed_v15_lifecycle_states",
        "v14_allowed_attempt_states",
        "v14_transition_graph",
        "proposed_v15_transition_graph",
        "current_state",
        "v15_protocol_and_manifest_amendment_required",
        "proposed_v15_protocol_and_manifest_paths_available_to_builder",
        "proposed_v15_protocol_and_manifest_consumed_by_bundle",
        "proposed_v15_protocol_relative_path",
        "proposed_v15_machine_manifest_relative_path",
        "proposed_v15_transition_graph_authoritative_for_production",
        "preflight_and_authorization_are_artifact_stages_not_lifecycle_states",
        "frozen_prestart_terminal_states",
        "partial_external_seed_acquisition_terminal_state",
        "any_durable_external_seed_value_spends_attempt",
        "no_redraw_reselection_replacement_after_durable_seed_acquisition",
        "pre_durable_output_infrastructure_abort_new_attempt_requires_written_independent_adjudication_and_identical_frozen_inputs",
        "authorization_requires_frozen_attempt_state",
        "authorization_must_follow_preauthorization_outcome_authorization_arm",
        "authorization_is_artifact_stage_not_lifecycle_state",
        "authorization_must_precede_postauthorization_outcome",
        "authorization_does_not_equal_started",
        "postauthorization_started_outcome_and_binding_started_receipt_must_be_durable_before_production_runner_rng_or_child",
        "transition_api_exposed",
        "receipt_present",
        "authority_verified",
        "launch_authorized",
        "started",
        "record_sha256",
    ),
    cp64.CP64NoExecutionGateContractV1: (
        "schema_version",
        "production_gate_ids",
        "production_gate_states",
        "requirement_schemas_frozen",
        "cp64_scaffolded_receipt_keysets_and_cross_bindings_predeclared",
        "all_required_production_receipt_keysets_predeclared",
        "complete_receipt_type_range_size_and_domain_schemas_frozen",
        "complete_auxiliary_artifact_size_schema_frozen",
        "bounded_auxiliary_artifact_size_proof_present",
        "generic_prestart_terminal_record_schema_frozen",
        "all_required_production_receipt_digest_preimages_frozen",
        "authorization_signature_preimage_and_verifier_frozen",
        "production_evidence_required_count",
        "production_evidence_present_count",
        "preauthorization_gate_count",
        "preflight_gate_summary_covered_gate_count",
        "preflight_gate_summary_gate_ids",
        "preflight_gate_summary_evidence_node_ids",
        "preflight_gate_summary_ids_states_evidence_strictly_aligned",
        "preflight_gate_summary_requires_all_covered_states_pass",
        "preflight_gate_summary_requires_exact_nonzero_sha256_per_covered_gate",
        "preflight_gate_summary_exact_keys",
        "preflight_gate_summary_excludes_independent_signoff_and_launch_authorization",
        "future_digest_node_order",
        "future_digest_edges",
        "source_receipt_binds_capsule_body",
        "capacity_receipt_binds_shard_map",
        "launch_authorization_is_only_final_downstream_aggregator",
        "digest_dag_acyclic",
        "external_seed_values_present",
        "source_authority_verified",
        "full_runtime_lock_recomputed",
        "capacity_measured",
        "durability_verified",
        "production_shard_map_bound",
        "production_runner_supervisor_qualified",
        "preflight_gate_summary_present",
        "closed_refusal_failure_classifier_qualified",
        "freeze_receipt_present",
        "power_thresholds_frozen",
        "independent_signoffs_present",
        "launch_authorization_present",
        "started",
        "production_request_materialization_exposed",
        "production_campaign_exposed",
        "preflight_passed",
        "readiness_state",
        "execution_authorized",
        "record_sha256",
    ),
    cp64.CP64ProductionCustodyPreflightBundleV1: (
        "schema_version",
        "scope",
        "v15_protocol_and_manifest_amendment_required",
        "proposed_v15_protocol_and_manifest_paths_available_to_builder",
        "proposed_v15_protocol_and_manifest_consumed_by_bundle",
        "proposed_v15_protocol_relative_path",
        "proposed_v15_machine_manifest_relative_path",
        "predecessor_custody",
        "external_seed_source_receipt_schema",
        "production_runtime_receipt_schema",
        "capacity_receipt_schema",
        "durability_receipt_schema",
        "candidate_shard_policy",
        "production_shard_map_receipt_schema",
        "launch_authorization_receipt_schema",
        "no_execution_gate_contract",
        "zero_argument_builder",
        "stdlib_only_import",
        "project_modules_imported",
        "host_filesystem_probed",
        "cp64_scaffolded_receipt_keysets_and_cross_bindings_predeclared",
        "all_required_production_receipt_keysets_predeclared",
        "complete_receipt_type_range_size_and_domain_schemas_frozen",
        "complete_auxiliary_artifact_size_schema_frozen",
        "bounded_auxiliary_artifact_size_proof_present",
        "generic_prestart_terminal_record_schema_frozen",
        "all_required_production_receipt_digest_preimages_frozen",
        "authorization_signature_preimage_and_verifier_frozen",
        "candidate_shard_policy_frozen",
        "candidate_shard_policy_selected_for_production",
        "external_seed_values_present",
        "external_seed_source_bound",
        "external_seed_source_receipt_present",
        "production_seed_capsule_present",
        "production_runtime_receipt_present",
        "capacity_receipt_present",
        "capacity_reservation_present",
        "durability_receipt_present",
        "production_shard_map_receipt_present",
        "freeze_receipt_present",
        "power_threshold_receipt_present",
        "independent_signoffs_present",
        "launch_authorization_present",
        "started_receipt_present",
        "committed_marker_present",
        "durable_writer_implemented",
        "production_runner_supervisor_qualified",
        "closed_refusal_failure_classification_implemented",
        "preflight_gate_summary_present",
        "production_runner_bound",
        "production_schema_frozen",
        "production_requests_materialized",
        "production_campaign_exposed",
        "production_execution_authorized",
        "production_execution_observed",
        "estimates_computed",
        "intervals_computed",
        "decision_made",
        "cp64_scaffolded_custody_preflight_inventory_and_policy_scaffold_complete",
        "runner_and_recomputation_blocker_closed",
        "unconditional_operational_predictions_blocker_closed",
        "power_and_thresholds_blocker_closed",
        "confirmatory_custody_blocker_closed",
        "confirmatory_evidence",
        "manuscript_claim",
        "formal_test_28_status",
        "formal_test_28_closed",
        "record_sha256",
    ),
}

_RECORD_DOMAINS = {
    cp64.CP64PredecessorCustodyV1: b"cp64-predecessor-custody-v1",
    cp64.CP64ExternalSeedSourceReceiptSchemaV1: (
        b"cp64-external-seed-source-receipt-schema-v1"
    ),
    cp64.CP64ProductionRuntimeReceiptSchemaV1: (
        b"cp64-production-runtime-receipt-schema-v1"
    ),
    cp64.CP64CapacityReceiptSchemaV1: b"cp64-capacity-receipt-schema-v1",
    cp64.CP64DurabilityReceiptSchemaV1: b"cp64-durability-receipt-schema-v1",
    cp64.CP64CandidateShardV1: b"cp64-candidate-shard-v1",
    cp64.CP64CandidateShardPolicyV1: b"cp64-candidate-shard-policy-v1",
    cp64.CP64ProductionShardMapReceiptSchemaV1: (
        b"cp64-production-shard-map-receipt-schema-v1"
    ),
    cp64.CP64LaunchAuthorizationReceiptSchemaV1: (
        b"cp64-launch-authorization-receipt-schema-v1"
    ),
    cp64.CP64NoExecutionGateContractV1: b"cp64-no-execution-gate-contract-v1",
    cp64.CP64ProductionCustodyPreflightBundleV1: (
        b"cp64-production-custody-preflight-bundle-v1"
    ),
}

_COMPONENT_PINS = {
    cp64.CP64ProductionCustodyPreflightBundleV1: (
        77_595,
        "31c1ff133f9dc6c3f9a5810359bd313f5fe5f46cb5e2bd6801b8dac0e241ae23",
        "32f7f0c62019d8ee906e6f74300f6c33fbe55984f69cfe4fe1061ffb92463f39",
        "caecd8630def94f7ac6da721422e3d9d71c26c351e753369abf17b224a90de83",
    ),
    cp64.CP64PredecessorCustodyV1: (
        3_733,
        "436d668504f22a42d3341636c2dfbdb18fb4112e14d2e0550ec0534ff329cd8f",
        "b3a6f04387a93eff4a327c8b8d9bf6951e13ce9a2dc8c7924bea8bd213398c4d",
        "c305f82eafa6cb694336daa097511686ea32ec0a04557dce7923f3035878ef6b",
    ),
    cp64.CP64ExternalSeedSourceReceiptSchemaV1: (
        5_788,
        "a0ffd50fc323112eeaa545f67a7b445e1a398c76a97287b4e44b3969920742dd",
        "03d29e3d8514ef7d7c0930620e23b4e35f52a7dd5b0c77955e89e62bf438a0fa",
        "998a0fd678f4721d37f483d63c73812ae6a6f59e96d97d9ac22880a47e949d77",
    ),
    cp64.CP64ProductionRuntimeReceiptSchemaV1: (
        1_345,
        "64f29132403b9dc9acbbf086111cca5474a202d168b872a72f238e35e209d66b",
        "0a347ca445aa300cdfa67204d01e81194783fc625c47b3974c8055c6782f1c3c",
        "41a0441570e631009c8ad0255edbc74e503111262a6e3def21b8080882d51fd8",
    ),
    cp64.CP64CapacityReceiptSchemaV1: (
        5_665,
        "a479987a4c0579227562d78e71b0550e82539d65020865d27057608b94d2d49e",
        "968108bda050687408fe989186aff3137560b827d1c83622f685a597d208ecfe",
        "c29261f5fe16974dd84734425a5c1934e2577116f491e33b1359fb0ff6869d73",
    ),
    cp64.CP64DurabilityReceiptSchemaV1: (
        10_970,
        "71cbbd7970df49f77d7d9b72d2a87e2e8c9709a066f58ae4f5f04facabbad9a3",
        "aced3702d8f1cbb240de9c41c6f97581a5ce019045e3300cc485bcb6328e76c2",
        "e1aa89489aadd86dbaf49b294e6d237141eeec68cbde9e28bca0bdd9315f5e60",
    ),
    cp64.CP64CandidateShardPolicyV1: (
        33_251,
        "199eb18f2e043c692fce53cde441594289217959dec0e37370559d1f2c0b1bfd",
        "8623c092772eaa0e40066d7e423967095e86491c01d869aa824c81fa9ee4b4ea",
        "6995505ea9c197ddc026a82daa15130518d30365bc7ccdc0af180a475a8afb9b",
    ),
    cp64.CP64CandidateShardV1: (
        990,
        "4314ac31bf971e1523b57d0cc22255e0a472409b3835170e61b1adf9063b682d",
        "8e298aad172c3ad1c09c4f5790c224ee25cd4ae6394a7ecdedd19a7de6db8d93",
        "0f2b0b21a5d321b07ba12a72afdce69ce669aef3f06bdf78f9ec50d54523f2e5",
    ),
    cp64.CP64ProductionShardMapReceiptSchemaV1: (
        2_915,
        "8002220c0c854edd1f746a9f2c2a5e523fdcf225ef58e535c6ae5ab64105c380",
        "288bb8d9ff9970d7e6fedf8e78f50d91fbd83e0e2c700ae195b9615d03678196",
        "f310ebcc7edef4dc633dc8451b709296421e04b94b45b0ac63a1c03adfa53bb3",
    ),
    cp64.CP64LaunchAuthorizationReceiptSchemaV1: (
        3_146,
        "ae71a12c8c916f17b62888b3ed398bc286cfbc4cceac49480ab48af9b1a8e917",
        "0c60d5484e0efb50991a95fa7da4b191dae7c48f25568f24207e594132ac17b5",
        "e34a58e41ad1a79b23ab55feb3ec9658efbc4029c57ed912f4256918a57b6b8c",
    ),
    cp64.CP64NoExecutionGateContractV1: (
        7_513,
        "5770b6caa44155ff7a12973304a78a84d6a80299e5e4d57e8acdfcb1787babee",
        "7ceb4f12ce712e7123509eb6380e134876855bb91e90c64a951f7e1bcbcb2633",
        "e3d3e6772a12a12b17c8561d14e5d74fc555d8f72ff5f724802c5542f5bc53dc",
    ),
}


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _plain(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is tuple:
        return [_plain(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _plain(getattr(value, item.name)) for item in fields(value)}
    raise TypeError(type(value).__name__)


def _plain_json_bytes(value: object) -> bytes:
    return json.dumps(
        _plain(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _all_records(root: object) -> tuple[object, ...]:
    found: list[object] = []
    seen: set[int] = set()

    def visit(value: object) -> None:
        if type(value) is tuple:
            for item in value:
                visit(item)
        elif is_dataclass(value) and not isinstance(value, type):
            if id(value) in seen:
                return
            seen.add(id(value))
            found.append(value)
            for item in fields(value):
                visit(getattr(value, item.name))

    visit(root)
    return tuple(found)


def test_cp64_source_and_public_surface_are_exact() -> None:
    assert _file_sha256(_SOURCE) == (
        "d35cbacb84e3348ae10549e053a0bb1572569583cdd03e66119353af4148bec2"
    )
    assert cp64.__all__ == (
        "CP64_TEST28_SCHEMA_VERSION",
        "CP64_TEST28_SCOPE",
        "CP64PredecessorCustodyV1",
        "CP64ExternalSeedSourceReceiptSchemaV1",
        "CP64ProductionRuntimeReceiptSchemaV1",
        "CP64CapacityReceiptSchemaV1",
        "CP64DurabilityReceiptSchemaV1",
        "CP64CandidateShardV1",
        "CP64CandidateShardPolicyV1",
        "CP64ProductionShardMapReceiptSchemaV1",
        "CP64LaunchAuthorizationReceiptSchemaV1",
        "CP64NoExecutionGateContractV1",
        "CP64ProductionCustodyPreflightBundleV1",
        "cp64_production_custody_preflight_bundle",
        "cp64_candidate_shard_for_logical_ordinal",
        "cp64_candidate_shard_bounds",
        "cp64_canonical_json_bytes",
        "cp64_sha256",
    )
    assert (
        tuple(
            inspect.signature(cp64.cp64_production_custody_preflight_bundle).parameters
        )
        == ()
    )


def test_cp64_bundle_smoke_is_definition_only() -> None:
    bundle = cp64.cp64_production_custody_preflight_bundle()
    assert bundle.schema_version == cp64.CP64_TEST28_SCHEMA_VERSION
    assert bundle.scope == cp64.CP64_TEST28_SCOPE
    assert (
        bundle.cp64_scaffolded_custody_preflight_inventory_and_policy_scaffold_complete
        is True
    )
    assert bundle.formal_test_28_status == "OPEN"
    assert bundle.formal_test_28_closed is False
    assert cp64.cp64_sha256(bundle) == (
        "caecd8630def94f7ac6da721422e3d9d71c26c351e753369abf17b224a90de83"
    )


def test_cp64_ast_has_no_execution_or_host_surface() -> None:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module.split(".")[0])
    assert imported == {
        "__future__",
        "dataclasses",
        "hashlib",
        "json",
        "threading",
        "typing",
        "weakref",
    }

    forbidden_names = {
        "open",
        "exec",
        "eval",
        "compile",
        "__import__",
        "subprocess",
        "posix_spawn",
        "fork",
        "system",
        "popen",
        "socket",
        "urlopen",
        "numpy",
        "scipy",
        "random",
        "secrets",
    }
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attributes = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    assert forbidden_names.isdisjoint(names | attributes)
    assert not any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and any(
            isinstance(item, ast.Constant) and item.value == "__main__"
            for item in ast.walk(node.test)
        )
        for node in ast.walk(tree)
    )


@pytest.mark.parametrize("record_type, expected", tuple(_EXPECTED_FIELDS.items()))
def test_cp64_record_field_order_is_exact(
    record_type: type, expected: tuple[str, ...]
) -> None:
    assert tuple(item.name for item in fields(record_type)) == expected


def test_cp64_records_use_python39_compatible_manual_slots() -> None:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and (
            isinstance(node.func, ast.Name) and node.func.id == "dataclass"
        ):
            assert not any(keyword.arg == "slots" for keyword in node.keywords)

    records = _all_records(cp64.cp64_production_custody_preflight_bundle())
    for record_type, expected_fields in _EXPECTED_FIELDS.items():
        assert record_type.__slots__ == expected_fields
        assert "__weakref__" not in record_type.__slots__
        record = next(item for item in records if type(item) is record_type)
        assert not hasattr(record, "__dict__")
        assert weakref.ref(record)() is record
    assert cp64._SealedRecord.__slots__ == ("__weakref__",)


def test_cp64_python39_import_builder_canonical_and_sealing() -> None:
    assert _PYTHON39.is_file()
    script = "\n".join(
        (
            "import gc, sys, weakref",
            "from dataclasses import fields",
            f"sys.path.insert(0, {str(_ROOT / 'src')!r})",
            "from heterodiff.evaluation import mixed_initializer_test28_production_custody_preflight as c",
            "assert sys.version_info[:2] == (3, 9)",
            "b = c.cp64_production_custody_preflight_bundle()",
            "raw = c.cp64_canonical_json_bytes(b)",
            "assert len(raw) == 77595 and raw.isascii()",
            "assert c.cp64_sha256(b) == 'caecd8630def94f7ac6da721422e3d9d71c26c351e753369abf17b224a90de83'",
            "assert not hasattr(b, '__dict__')",
            "assert type(b).__slots__ == tuple(x.name for x in fields(type(b)))",
            "try:\n c.CP64ProductionCustodyPreflightBundleV1()\n raise AssertionError('construction accepted')\nexcept TypeError:\n pass",
            "try:\n b.scope = 'forged'\n raise AssertionError('mutation accepted')\nexcept (AttributeError, TypeError):\n pass",
            "s = c.cp64_candidate_shard_bounds(1)",
            "r = weakref.ref(s); del s; gc.collect(); assert r() is None",
            "f = object.__new__(c.CP64CandidateShardV1)",
            "try:\n c.cp64_canonical_json_bytes(f)\n raise AssertionError('forgery accepted')\nexcept TypeError:\n pass",
            "print('CP64_PY39_OK')",
        )
    )
    completed = subprocess.run(
        (str(_PYTHON39), "-I", "-c", script),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert completed.stdout.strip() == "CP64_PY39_OK"
    assert completed.stderr == ""


def test_cp64_builder_is_pure_and_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = cp64.cp64_production_custody_preflight_bundle()
    first_bytes = cp64.cp64_canonical_json_bytes(first)

    def forbidden_import(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("builder attempted an import")

    def forbidden_open(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("builder attempted filesystem access")

    with monkeypatch.context() as guarded:
        guarded.setattr("builtins.open", forbidden_open)
        guarded.setattr("builtins.__import__", forbidden_import)
        second = cp64.cp64_production_custody_preflight_bundle()
    assert cp64.cp64_canonical_json_bytes(second) == first_bytes
    assert second is not first
    assert second.predecessor_custody is not first.predecessor_custody
    assert (
        second.candidate_shard_policy.shards[0]
        is not first.candidate_shard_policy.shards[0]
    )


def test_cp64_predecessor_custody_matches_live_cp63() -> None:
    bundle = cp64.cp64_production_custody_preflight_bundle()
    custody = bundle.predecessor_custody

    # The unversioned v14 paths are immutable predecessor custody.  V15 uses
    # separate sidecar paths and must never overwrite these bytes.
    assert custody.cp63_protocol_relative_path == (
        "research/preregistrations/cp50_test28_mixed_initializer_v1.md"
    )
    assert custody.cp63_protocol_sha256 == (
        "39c9c7fe061d1a36d21c999eadb308cd26cb982871cbbbd1c3d6a3a35d3842e9"
    )
    assert (custody.cp63_protocol_bytes, custody.cp63_protocol_lines) == (
        105_542,
        1_950,
    )
    assert custody.cp63_machine_manifest_relative_path == (
        "research/fixtures/cp50_test28_mixed_initializer_v1.json"
    )
    assert custody.cp63_machine_manifest_sha256 == (
        "d0fc1f2845f4ed1316bcbb20f9f876ee3cd99a156af525eecc089194af3a26fe"
    )
    assert (
        custody.cp63_machine_manifest_bytes,
        custody.cp63_machine_manifest_lines,
    ) == (1_898_933, 36_239)
    protocol_bytes = _V14_PROTOCOL.read_bytes()
    manifest_bytes = _V14_MANIFEST.read_bytes()
    assert _V14_PROTOCOL.relative_to(_ROOT).as_posix() == (
        custody.cp63_protocol_relative_path
    )
    assert _V14_MANIFEST.relative_to(_ROOT).as_posix() == (
        custody.cp63_machine_manifest_relative_path
    )
    assert hashlib.sha256(protocol_bytes).hexdigest() == custody.cp63_protocol_sha256
    assert len(protocol_bytes) == custody.cp63_protocol_bytes
    assert len(protocol_bytes.splitlines()) == custody.cp63_protocol_lines
    assert hashlib.sha256(manifest_bytes).hexdigest() == (
        custody.cp63_machine_manifest_sha256
    )
    assert len(manifest_bytes) == custody.cp63_machine_manifest_bytes
    assert len(manifest_bytes.splitlines()) == custody.cp63_machine_manifest_lines
    assert custody.cp63_protocol_id == "cp50-test28-mixed-initializer-v1"
    assert custody.cp63_protocol_state == "DRAFT"
    assert custody.cp63_manifest_schema_version == (
        "cp50-test28-mixed-initializer-machine-manifest-v14"
    )
    assert custody.cp63_bound_artifact_count == 38
    assert custody.cp63_development_verification_record_count == 35
    assert (
        custody.cp63_ledger_total_count,
        custody.cp63_ledger_satisfied_count,
        custody.cp63_ledger_missing_count,
    ) == (18, 14, 4)
    assert custody.cp63_aggregate_test_count == 1_066
    assert custody.cp63_lifecycle_current_state == "DRAFT_PRE_FREEZE"
    assert custody.cp63_freeze_state == "ABSENT_DRAFT"
    assert custody.cp63_confirmatory_execution_authorized is False
    assert custody.cp63_formal_test_28_status == "OPEN"
    assert custody.cp63_formal_test_28_closed is False

    assert _file_sha256(_RUNNER_SOURCE) == custody.cp63_runner_source_sha256
    assert _file_sha256(_INDEPENDENT_SOURCE) == custody.cp63_independent_source_sha256
    dependency_lock = _ROOT / custody.dependency_lock_path
    assert custody.dependency_lock_path == (
        "requirements/m1-reference-macos-arm64-py311.lock"
    )
    assert dependency_lock.is_file()
    assert _file_sha256(dependency_lock) == custody.dependency_lock_sha256
    assert custody.cp64_source_hash_in_record is False
    assert custody.cp64_source_hash_external_binding_required is True
    assert custody.predecessor_custody_only is True
    assert custody.complete_production_source_manifest_present is False
    assert custody.production_runtime_match_verified is False


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="historical CP63 records use dataclass(slots=True)",
)
def test_cp64_predecessor_custody_matches_live_cp63_builders() -> None:
    assert runner is not None
    assert independent is not None
    custody = cp64.cp64_production_custody_preflight_bundle().predecessor_custody
    runner_bundle = runner.cp63_runner_recomputation_rehearsal_bundle()
    independent_bundle = independent.cp63_independent_recomputation_bundle()
    assert runner_bundle.record_sha256 == custody.cp63_runner_bundle_record_sha256
    assert (
        runner_bundle.schedule_contract.record_sha256
        == custody.cp63_schedule_contract_record_sha256
    )
    assert (
        runner_bundle.seed_capsule_contract.record_sha256
        == custody.cp63_seed_capsule_contract_record_sha256
    )
    assert (
        runner_bundle.lifecycle_contract.record_sha256
        == custody.cp63_lifecycle_contract_record_sha256
    )
    assert (
        runner_bundle.raw_record_schema.record_sha256
        == custody.cp63_raw_record_schema_record_sha256
    )
    assert (
        runner_bundle.resource_contract.record_sha256
        == custody.cp63_resource_contract_record_sha256
    )
    assert (
        independent_bundle.record_sha256
        == custody.cp63_independent_bundle_record_sha256
    )
    assert (
        independent.cp63_recomputation_sha256(independent_bundle)
        == custody.cp63_independent_bundle_public_sha256
    )


def test_cp64_seed_source_schema_is_acyclic_and_non_authenticating() -> None:
    schema = (
        cp64.cp64_production_custody_preflight_bundle().external_seed_source_receipt_schema
    )
    assert schema.seed_count == 2_048
    assert schema.seed_encoding == "uint64-16-lowercase-hex-big-endian"
    assert "ordered_seed_values" in schema.sequence_commitment_formula
    assert "capsule" not in schema.receipt_digest_formula
    assert schema.capsule_body_digest_bound_by_source_receipt is False
    assert schema.source_receipt_digest_referenced_by_capsule is True
    assert schema.capsule_sequence_commitment_crosscheck_required is True
    assert schema.canonical_syntax_can_prove_iid is False
    assert schema.digest_can_authenticate_source is False
    assert schema.receipt_values_present is False
    assert schema.source_authority_verified is False
    assert "seed_capsule_body_sha256" not in schema.exact_keys
    assert schema.exact_keys == (
        "schema",
        "purpose",
        "attempt_id",
        "freeze_receipt_sha256",
        "cp61_stable_design_sha256",
        "seed_count",
        "seed_encoding",
        "source_method_id",
        "acquisition_session_sha256",
        "acquisition_journal_sha256",
        "acquisition_journal_head_sha256",
        "acquisition_journal_entry_count",
        "ordered_seed_values_commitment_sha256",
        "custody_artifact_sha256",
        "body_sha256",
    )
    assert schema.acquisition_start_receipt_exact_keys == (
        "schema",
        "purpose",
        "attempt_id",
        "freeze_receipt_sha256",
        "source_method_id",
        "acquisition_journal_relative_path",
        "acquisition_journal_device_identity_sha256",
        "acquisition_journal_inode",
        "acquisition_journal_preallocated_bytes",
        "acquisition_journal_allocation_method_id",
        "acquisition_journal_extent_map_sha256",
        "acquisition_journal_file_fsync_completed_at_utc",
        "acquisition_journal_directory_fsync_completed_at_utc",
        "acquisition_journal_inode_recheck_sha256",
        "acquisition_session_id",
        "started_at_utc",
        "body_sha256",
    )
    assert schema.partial_acquisition_terminal_receipt_exact_keys == (
        "schema",
        "purpose",
        "attempt_id",
        "freeze_receipt_sha256",
        "acquisition_start_receipt_sha256",
        "source_method_id",
        "expected_seed_count",
        "acquired_seed_count",
        "acquisition_journal_sha256",
        "acquisition_journal_head_sha256",
        "acquisition_journal_entry_count",
        "acquisition_journal_raw_bytes",
        "seed_encoding",
        "ordered_partial_seed_values",
        "ordered_partial_seed_values_commitment_sha256",
        "terminal_state",
        "topup_redraw_reselection_permitted",
        "body_sha256",
    )
    assert schema.attempt_binding_required is True
    assert schema.freeze_receipt_binding_required is True
    assert schema.acquisition_start_receipt_required is True
    assert schema.acquisition_start_receipt_exclusive_create_required is True
    assert schema.acquisition_start_receipt_file_fsync_required is True
    assert schema.acquisition_start_receipt_directory_fsync_required is True
    assert (
        schema.acquisition_start_must_be_durably_committed_before_source_contact is True
    )
    assert schema.acquisition_session_sha256_is_start_receipt_sha256 is True
    assert schema.committed_acquisition_start_receipt_spends_attempt is True
    assert schema.any_durable_external_seed_value_spends_attempt is True
    assert schema.durably_journaled_partial_acquisition_values_must_be_retained is True
    assert schema.partial_acquisition_terminal_receipt_required is True
    assert schema.partial_acquisition_terminal_state == "INCOMPLETE"
    assert schema.partial_acquisition_topup_redraw_reselection_permitted is False


def test_cp64_seed_acquisition_journal_is_crash_durable_and_fail_closed() -> None:
    bundle = cp64.cp64_production_custody_preflight_bundle()
    schema = bundle.external_seed_source_receipt_schema
    assert schema.acquisition_start_receipt_relative_path == (
        "seed_acquisition_start_receipt.json"
    )
    assert schema.partial_acquisition_terminal_receipt_relative_path == (
        "seed_partial_acquisition_terminal_receipt.json"
    )
    assert schema.acquisition_journal_relative_path == "seed_acquisition_journal.bin"
    assert schema.acquisition_journal_encoding == (
        "2048-max-fixed-80-byte-chained-binary-entries"
    )
    assert schema.acquisition_journal_entry_field_order == (
        "ordinal-uint64-be",
        "value-uint64-be",
        "previous-entry-sha256",
        "entry-sha256",
    )
    assert schema.acquisition_journal_entry_bytes == 80
    assert schema.acquisition_journal_max_entries == 2_048
    assert schema.acquisition_journal_max_bytes == 163_840
    assert 80 * 2_048 == 163_840
    assert schema.acquisition_journal_initial_head_formula == (
        "SHA256(cp64-external-seed-acquisition-journal-head-v1\\0+"
        "acquisition-start-receipt-sha256)"
    )
    assert schema.acquisition_journal_entry_digest_formula == (
        "SHA256(cp64-external-seed-acquisition-journal-entry-v1\\0+"
        "start-receipt-sha256+ordinal-uint64-be+value-uint64-be+"
        "previous-entry-sha256)"
    )
    assert schema.acquisition_journal_max_bytes == (
        bundle.capacity_receipt_schema.acquisition_journal_maximum_bytes
    )
    assert (
        schema.acquisition_journal_relative_path
        in bundle.durability_receipt_schema.global_relative_paths
    )
    required_true = (
        "acquisition_journal_entry_ordinals_strictly_increasing_from_one",
        "acquisition_journal_exclusive_create_required",
        "acquisition_journal_nofollow_required",
        "acquisition_journal_non_sparse_physical_allocation_required",
        "acquisition_journal_file_fsync_before_acquisition_start_receipt_required",
        "acquisition_journal_directory_fsync_before_acquisition_start_receipt_required",
        "acquisition_journal_path_inode_recheck_before_acquisition_start_receipt_required",
        "acquisition_journal_path_inode_recheck_before_each_entry_append_required",
        "acquisition_journal_preallocated_before_source_contact",
        "acquisition_journal_entry_fsync_before_next_source_draw",
        "acquisition_journal_every_entry_including_final_entry_fsync_required",
        "acquisition_journal_final_fsync_before_completed_source_receipt_required",
        "acquisition_journal_no_resume_after_crash",
        "acquisition_journal_recovery_accepts_only_longest_valid_fsynced_prefix",
        "acquisition_journal_torn_or_invalid_suffix_is_not_value_evidence",
        "completed_source_receipt_binds_acquisition_journal_sha_head_and_count",
        "completed_journal_entry_count_must_equal_seed_count",
        "completed_journal_head_must_equal_entry_digest_at_seed_count",
        "completed_journal_ordinal_value_sequence_commitment_must_equal_source_receipt_ordered_seed_values_commitment",
        "capsule_ordered_seed_values_commitment_must_equal_completed_journal_sequence_commitment",
    )
    assert all(getattr(schema, name) is True for name in required_true)
    assert schema.acquisition_journal_recovery_terminal_state == "INCOMPLETE"
    assert schema.acquisition_journal_topup_redraw_reselection_permitted is False
    assert schema.source_return_without_journal_fsync_spends_attempt is True
    assert schema.source_return_without_journal_fsync_terminal_state == "INCOMPLETE"
    assert schema.source_return_without_journal_fsync_value_is_claimed_retained is False
    assert (
        schema.source_return_without_journal_fsync_resume_topup_redraw_permitted
        is False
    )


def test_cp64_runtime_schema_requires_fresh_complete_production_custody() -> None:
    schema = (
        cp64.cp64_production_custody_preflight_bundle().production_runtime_receipt_schema
    )
    assert schema.cp62_candidate_runtime_lock_sha256 == (
        "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
    )
    assert schema.dependency_lock_sha256 == (
        "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d"
    )
    assert schema.complete_source_manifest_required is True
    assert schema.cp64_source_external_binding_required is True
    assert schema.preimport_environment_required is True
    assert schema.loaded_local_source_closure_required is True
    assert schema.compiled_abi_map_required is True
    assert schema.receipt_present is False
    assert schema.full_runtime_lock_recomputed is False
    assert schema.production_runtime_match_verified is False


def test_cp64_capacity_policy_arithmetic_and_reservation_semantics() -> None:
    bundle = cp64.cp64_production_custody_preflight_bundle()
    capacity = bundle.capacity_receipt_schema
    assert capacity.cp63_resource_contract_record_sha256 == (
        "17259329bbca1029e989029594af67570f81731d9b21355a5151277ba7938d40"
    )
    total_requests = 32_768
    raw = 549_755_813_888
    stable = 274_877_906_944
    requests = total_requests * 65_536
    stderr = total_requests * 1_048_576
    capsule = 131_072
    assert (raw, stable, requests, stderr, capsule) == (
        549_755_813_888,
        274_877_906_944,
        2_147_483_648,
        34_359_738_368,
        131_072,
    )
    base_payload = raw + stable + requests + stderr + capsule
    newline_overhead = 3 * total_requests
    stderr_prefix_overhead = 8 * total_requests
    assert base_payload == 861_141_073_920
    assert newline_overhead == 98_304
    assert stderr_prefix_overhead == 262_144
    assert capacity.global_payload_ceiling_bytes == (
        base_payload + newline_overhead + stderr_prefix_overhead
    )
    assert capacity.global_payload_ceiling_bytes == 861_141_434_368

    destination = 2**40
    auxiliary = 32 * 2**30
    combined = destination + auxiliary
    assert capacity.global_destination_reservation_bytes == destination
    assert (
        capacity.global_auxiliary_metadata_conservative_policy_reservation_bytes
        == auxiliary
    )
    assert (
        capacity.global_combined_available_and_quota_required_before_reservation_bytes
        == combined
    )
    assert combined == 1_133_871_366_144
    assert (
        capacity.global_available_and_quota_required_after_destination_before_auxiliary_reservation_bytes
        == auxiliary
    )
    assert destination - capacity.global_payload_ceiling_bytes == 238_370_193_408
    assert capacity.per_shard_payload_ceiling_bytes == 26_910_665_728
    assert capacity.per_shard_destination_reservation_bytes == auxiliary
    assert capacity.candidate_shard_count == 32
    assert 32 * capacity.per_shard_destination_reservation_bytes == destination
    assert capacity.minimum_available_inodes == 4_096

    required_true = (
        "auxiliary_metadata_reservation_is_conservative_policy_floor",
        "bounded_auxiliary_artifact_size_proof_required_before_capacity_pass",
        "auxiliary_metadata_must_fit_exclusive_auxiliary_reservation",
        "acquisition_journal_counted_within_auxiliary_metadata_reserve",
        "combined_available_and_quota_before_reservation_each_must_meet_floor",
        "before_reservation_available_and_quota_each_meet_combined_floor_required",
        "after_destination_before_auxiliary_available_and_quota_each_meet_auxiliary_floor_required",
        "destination_and_auxiliary_reservations_both_exclusive_required",
        "destination_and_auxiliary_reservations_no_double_count_required",
        "auxiliary_metadata_physical_and_quota_reservations_both_required",
        "auxiliary_metadata_reservation_same_storage_root_required",
        "auxiliary_metadata_reservation_retained_until_committed",
        "auxiliary_metadata_reservation_consumed_in_place_and_enforced_quota_required",
        "same_filesystem_required",
        "measurement_must_postdate_freeze",
        "measurement_must_predate_authorization",
        "reservation_receipt_required",
        "non_sparse_reservation_required",
        "reservation_same_filesystem_required",
    )
    assert all(getattr(capacity, name) is True for name in required_true)
    assert capacity.complete_auxiliary_artifact_size_schema_frozen is False
    assert capacity.bounded_auxiliary_artifact_size_proof_present is False
    assert capacity.quota_only_auxiliary_reservation_sufficient is False
    assert (
        capacity.post_destination_free_space_or_quota_snapshot_alone_sufficient is False
    )
    assert capacity.snapshot_only_sufficient is False
    assert capacity.acquisition_journal_maximum_bytes == 163_840
    assert capacity.auxiliary_metadata_reservation_artifact_relative_path == (
        "auxiliary_metadata_reservation.json"
    )
    assert capacity.auxiliary_metadata_reservation_method_rule == (
        "o-excl-nonsparse-preallocated-auxiliary-destination-inodes-consumed-in-"
        "place-and-exclusive-enforced-quota-both-required"
    )
    assert capacity.destination_effective_reservation_formula == (
        "min(physically_allocated_reservation_bytes,"
        "usable_reserved_bytes_after_allocation)"
    )
    assert capacity.auxiliary_effective_reservation_formula == (
        "min(physically_allocated_auxiliary_metadata_bytes,"
        "auxiliary_metadata_reserved_quota_bytes)-if-exclusive-durable-same-"
        "storage-root-and-no-double-count-else-0"
    )
    assert capacity.combined_effective_reservation_formula == (
        "destination-effective-reservation-bytes+auxiliary-effective-reservation-"
        "bytes-with-disjoint-custody"
    )
    assert "bounded_auxiliary_artifact_size_proof_present" in (
        capacity.capacity_pass_predicate
    )
    assert ">=1099511627776" in capacity.capacity_pass_predicate
    assert ">=34359738368" in capacity.capacity_pass_predicate
    assert ">=1133871366144" in capacity.capacity_pass_predicate
    assert "available_inodes_after_reservation>=4096" in (
        capacity.capacity_pass_predicate
    )
    assert "all_required_reservation_and_filesystem_verifications_true" in (
        capacity.capacity_pass_predicate
    )

    assert capacity.jsonl_record_encoding == (
        "ascii-canonical-json-one-record-per-line"
    )
    assert capacity.jsonl_record_kinds == ("request", "raw", "stable")
    assert capacity.jsonl_newline_bytes_per_record == 1
    assert capacity.stderr_record_encoding == (
        "uint64-big-endian-length-prefixed-raw-bytes"
    )
    assert capacity.stderr_length_prefix_bytes == 8
    assert capacity.stderr_payload_max_bytes == 1_048_576
    assert capacity.stderr_records_per_shard == 1_024
    assert capacity.stderr_trailing_bytes_permitted is False
    assert capacity.seed_capsule_encoding == "exact-cp63-canonical-json-bytes"
    assert capacity.seed_capsule_final_newline_bytes == 0
    assert capacity.payload_ceilings_include_storage_framing is True
    assert capacity.capacity_receipt_present is False
    assert capacity.capacity_measured is False
    assert capacity.minimum_capacity_satisfied is False
    assert capacity.production_resources_allocated is False


def test_cp64_candidate_shards_exhaustively_partition_schedule() -> None:
    policy = cp64.cp64_production_custody_preflight_bundle().candidate_shard_policy
    assert policy.policy_id == "cp64-contiguous-64-seed-ordinal-candidate-v1"
    assert policy.mapping_formula == "floor((logical_request_ordinal-1)/1024)+1"
    assert (policy.shard_count, policy.seed_count, policy.row_count) == (32, 2_048, 16)
    assert policy.total_request_count == 32_768
    assert policy.seed_ordinals_per_shard == 64
    assert policy.logical_requests_per_shard == 1_024
    assert policy.shard_ordinals == tuple(range(1, 33))
    assert len(policy.shards) == 32

    observed_logical: list[int] = []
    observed_seeds: list[int] = []
    for shard_ordinal, shard in enumerate(policy.shards, start=1):
        assert shard.shard_ordinal == shard_ordinal
        assert shard.shard_id == f"shard-{shard_ordinal:04d}"
        assert shard.seed_ordinal_min == (shard_ordinal - 1) * 64 + 1
        assert shard.seed_ordinal_max == shard_ordinal * 64
        assert shard.seed_ordinal_count == 64
        assert shard.logical_request_ordinal_min == (shard_ordinal - 1) * 1_024 + 1
        assert shard.logical_request_ordinal_max == shard_ordinal * 1_024
        assert shard.logical_request_count == 1_024
        assert shard.all_sixteen_rows_per_seed_collocated is True
        assert shard.logical_requests_strictly_increasing is True
        observed_logical.extend(
            range(
                shard.logical_request_ordinal_min, shard.logical_request_ordinal_max + 1
            )
        )
        observed_seeds.extend(range(shard.seed_ordinal_min, shard.seed_ordinal_max + 1))
    assert observed_logical == list(range(1, 32_769))
    assert observed_seeds == list(range(1, 2_049))

    for logical_ordinal in range(1, 32_769):
        shard = cp64.cp64_candidate_shard_for_logical_ordinal(logical_ordinal)
        expected = policy.shards[(logical_ordinal - 1) // 1_024]
        assert cp64.cp64_canonical_json_bytes(shard) == cp64.cp64_canonical_json_bytes(
            expected
        )
        seed_ordinal = (logical_ordinal - 1) // 16 + 1
        first_for_seed = (seed_ordinal - 1) * 16 + 1
        last_for_seed = first_for_seed + 15
        assert shard.logical_request_ordinal_min <= first_for_seed
        assert last_for_seed <= shard.logical_request_ordinal_max


@pytest.mark.parametrize(
    "function,value,error",
    (
        (cp64.cp64_candidate_shard_for_logical_ordinal, True, TypeError),
        (cp64.cp64_candidate_shard_for_logical_ordinal, False, TypeError),
        (cp64.cp64_candidate_shard_for_logical_ordinal, 1.0, TypeError),
        (cp64.cp64_candidate_shard_for_logical_ordinal, "1", TypeError),
        (cp64.cp64_candidate_shard_for_logical_ordinal, 0, ValueError),
        (cp64.cp64_candidate_shard_for_logical_ordinal, -1, ValueError),
        (cp64.cp64_candidate_shard_for_logical_ordinal, 32_769, ValueError),
        (cp64.cp64_candidate_shard_bounds, True, TypeError),
        (cp64.cp64_candidate_shard_bounds, 1.0, TypeError),
        (cp64.cp64_candidate_shard_bounds, "1", TypeError),
        (cp64.cp64_candidate_shard_bounds, 0, ValueError),
        (cp64.cp64_candidate_shard_bounds, 33, ValueError),
    ),
)
def test_cp64_candidate_mapping_rejects_invalid_inputs(
    function: object, value: object, error: type[Exception]
) -> None:
    with pytest.raises(error):
        function(value)  # type: ignore[operator]


@pytest.mark.parametrize("shard_ordinal", range(1, 33))
def test_cp64_candidate_shard_bounds_return_whole_issued_record(
    shard_ordinal: int,
) -> None:
    by_shard = cp64.cp64_candidate_shard_bounds(shard_ordinal)
    by_logical = cp64.cp64_candidate_shard_for_logical_ordinal(
        (shard_ordinal - 1) * 1_024 + 1
    )
    assert isinstance(by_shard, cp64.CP64CandidateShardV1)
    assert by_shard is not by_logical
    assert cp64.cp64_canonical_json_bytes(by_shard) == cp64.cp64_canonical_json_bytes(
        by_logical
    )


def test_cp64_candidate_shard_resource_math_is_exact() -> None:
    policy = cp64.cp64_production_custody_preflight_bundle().candidate_shard_policy
    expected_per_shard = {
        "rejection_proposal_slot_count": 10_880,
        "sir_proposal_slot_count": 87_040,
        "total_proposal_slot_count": 97_920,
        "sir_resampling_draw_count": 512,
        "maximum_event_occurrence_count": 146_880,
        "maximum_coordinate_count": 244_800,
        "raw_ceiling_bytes": 17_179_870_208,
        "stable_ceiling_bytes": 8_589_935_616,
        "request_ceiling_bytes": 67_109_888,
        "stderr_ceiling_bytes": 1_073_750_016,
        "payload_ceiling_bytes": 26_910_665_728,
        "candidate_destination_reservation_bytes": 34_359_738_368,
    }
    for shard in policy.shards:
        assert shard.relative_directory == f"shards/{shard.shard_id}"
        for name, expected in expected_per_shard.items():
            assert getattr(shard, name) == expected
        assert shard.total_proposal_slot_count == (
            shard.rejection_proposal_slot_count + shard.sir_proposal_slot_count
        )
        assert shard.payload_ceiling_bytes == (
            shard.raw_ceiling_bytes
            + shard.stable_ceiling_bytes
            + shard.request_ceiling_bytes
            + shard.stderr_ceiling_bytes
        )
        assert shard.definition_only is True
        assert shard.selected_for_production is False
        assert shard.instantiated is False

    global_expected = {
        "rejection_proposal_slot_count": 348_160,
        "sir_proposal_slot_count": 2_785_280,
        "total_proposal_slot_count": 3_133_440,
        "sir_resampling_draw_count": 16_384,
        "maximum_event_occurrence_count": 4_700_160,
        "maximum_coordinate_count": 7_833_600,
        "raw_ceiling_bytes": 549_755_846_656,
        "stable_ceiling_bytes": 274_877_939_712,
        "request_ceiling_bytes": 2_147_516_416,
        "stderr_ceiling_bytes": 34_360_000_512,
    }
    for name, expected in global_expected.items():
        assert sum(getattr(shard, name) for shard in policy.shards) == expected


def test_cp64_candidate_policy_is_unselected_and_does_not_inherit_eight_shards() -> None:
    bundle = cp64.cp64_production_custody_preflight_bundle()
    policy = bundle.candidate_shard_policy
    shard_schema = bundle.production_shard_map_receipt_schema
    assert policy.same_seed_rows_collocated is True
    assert policy.duplicate_seed_values_distinguished_by_ordinal is True
    assert policy.historical_pre_cp61_eight_shard_plan_inherited is False
    assert policy.candidate_policy_frozen is True
    assert policy.candidate_policy_selected_for_production is False
    assert policy.production_shard_map_bound is False
    assert policy.production_shard_map_instantiated is False
    assert shard_schema.candidate_shard_policy_sha256 == policy.record_sha256
    assert shard_schema.shard_count == 32
    assert shard_schema.receipt_present is False
    assert shard_schema.attempt_binding_required is True
    assert shard_schema.reservation_manifest_binding_required is True
    assert shard_schema.candidate_policy_selected_for_production is False
    assert shard_schema.production_shard_map_bound is False
    assert shard_schema.production_shard_map_instantiated is False
    assert cp64.cp64_sha256(policy) == (
        "6995505ea9c197ddc026a82daa15130518d30365bc7ccdc0af180a475a8afb9b"
    )

    assert shard_schema.exactly_32_candidate_shard_records_required is True
    assert shard_schema.shard_ordinals_strictly_increasing_unique_1_through_32 is True
    assert (
        shard_schema.logical_ordinal_ranges_contiguous_nonoverlapping_cover_1_through_32768
        is True
    )
    assert (
        shard_schema.seed_ordinal_ranges_contiguous_nonoverlapping_cover_1_through_2048
        is True
    )
    assert shard_schema.shard_record_candidate_equality_field_pairs == (
        ("shard_ordinal", "shard_ordinal"),
        ("shard_id", "shard_id"),
        ("seed_ordinal_min", "seed_ordinal_min"),
        ("seed_ordinal_max", "seed_ordinal_max"),
        ("logical_request_ordinal_min", "logical_request_ordinal_min"),
        ("logical_request_ordinal_max", "logical_request_ordinal_max"),
        ("logical_request_count", "logical_request_count"),
        ("relative_directory", "relative_directory"),
        ("capacity_partition_bytes", "candidate_destination_reservation_bytes"),
    )
    assert (
        shard_schema.shard_record_candidate_fields_must_equal_candidate_record is True
    )
    assert (
        shard_schema.relative_directory_must_equal_candidate_shard_relative_directory
        is True
    )
    assert (
        shard_schema.per_file_reservation_manifest_entry_sha256_required_for_each_reserved_partial
        is True
    )
    assert shard_schema.shard_record_per_file_reservation_link_order == (
        "requests.jsonl",
        "raw_records.jsonl",
        "stable_traces.jsonl",
        "stderr_records.bin",
    )
    assert shard_schema.shard_record_per_file_reservation_links_exactly_four is True
    assert (
        shard_schema.shard_record_per_file_reservation_link_digests_exact_nonzero_sha256
        is True
    )
    assert shard_schema.shard_record_per_file_paths_match_candidate_templates is True
    assert (
        shard_schema.shard_record_per_file_reserved_bytes_sum_to_candidate_destination_reservation_bytes
        is True
    )
    assert shard_schema.each_shard_capacity_partition_bytes == 34_359_738_368
    assert shard_schema.all_shard_capacity_partition_sum_bytes == 2**40
    assert (
        shard_schema.all_shard_capacity_partition_sum_equals_global_destination_reservation
        is True
    )
    assert shard_schema.shard_record_digest_formula == (
        "SHA256(cp64-test28-production-shard-map-shard-record-v1\\0+"
        "canonical(shard-record-with-zero-shard-record-sha256))"
    )
    durability = bundle.durability_receipt_schema
    expected_templates = tuple(
        f"shards/{{shard_id}}/{filename}"
        for filename in shard_schema.shard_record_per_file_reservation_link_order
    )
    assert durability.reservation_destination_final_path_templates == (
        expected_templates
    )
    for shard in policy.shards:
        expanded_paths = tuple(
            template.replace("{shard_id}", shard.shard_id)
            for template in durability.reservation_destination_final_path_templates
        )
        assert expanded_paths == tuple(
            f"{shard.relative_directory}/{filename}"
            for filename in shard_schema.shard_record_per_file_reservation_link_order
        )


def test_cp64_capacity_receipt_exact_keys_require_reservation_not_snapshot() -> None:
    keys = (
        cp64.cp64_production_custody_preflight_bundle().capacity_receipt_schema.exact_keys
    )
    assert keys == (
        "schema",
        "purpose",
        "attempt_id",
        "destination_reservation_required_bytes",
        "auxiliary_metadata_reservation_required_bytes",
        "combined_available_and_quota_required_before_reservation_bytes",
        "available_and_quota_required_after_destination_before_auxiliary_reservation_bytes",
        "schedule_sha256",
        "capacity_schema_sha256",
        "storage_root_identity_sha256",
        "filesystem_identity_sha256",
        "measurement_session_sha256",
        "measured_at_utc",
        "measurement_method_id",
        "quota_method_id",
        "reservation_method_id",
        "auxiliary_metadata_reservation_method_id",
        "allocation_unit_bytes",
        "auxiliary_metadata_reservation_artifact_sha256",
        "available_bytes_before_reservation",
        "quota_headroom_bytes_before_reservation",
        "physically_allocated_reservation_bytes",
        "physically_allocated_auxiliary_metadata_bytes",
        "auxiliary_metadata_reserved_quota_bytes",
        "usable_reserved_bytes_after_allocation",
        "available_bytes_after_reservation",
        "quota_headroom_bytes_after_reservation",
        "available_inodes_after_reservation",
        "non_sparse_allocation_verified",
        "reservation_same_filesystem_verified",
        "reservation_exclusive_verified",
        "reservation_durable_verified",
        "auxiliary_metadata_reservation_exclusive_verified",
        "auxiliary_metadata_non_sparse_allocation_verified",
        "auxiliary_metadata_reserved_quota_verified",
        "auxiliary_metadata_reservation_durable_verified",
        "auxiliary_metadata_reservation_same_storage_root_verified",
        "destination_and_auxiliary_reservation_no_double_count_verified",
        "shard_count",
        "atomic_rename_supported",
        "file_fsync_supported",
        "directory_fsync_supported",
        "reservation_manifest_sha256",
        "body_sha256",
    )
    for stale in (
        "requested_reservation_bytes",
        "global_required_bytes",
        "per_shard_required_bytes",
        "physically_or_quota_reserved_auxiliary_metadata_bytes",
    ):
        assert stale not in keys


def test_cp64_durability_layout_is_relative_unique_and_non_destructive() -> None:
    durability = (
        cp64.cp64_production_custody_preflight_bundle().durability_receipt_schema
    )
    expected_global = (
        "frozen_inputs/protocol.md",
        "frozen_inputs/protocol.sha256",
        "frozen_inputs/machine_manifest.json",
        "frozen_inputs/bound_files.json",
        "frozen_inputs/dependency_lock.txt",
        "freeze_receipt.json",
        "power_threshold_receipt.json",
        "preflight_gate_summary.json",
        "independent_signoff.json",
        "capacity_receipt.json",
        "auxiliary_metadata_reservation.json",
        "reservation_manifest.json",
        "production_runtime_receipt.json",
        "seed_acquisition_start_receipt.json",
        "seed_acquisition_journal.bin",
        "seed_source_receipt.json",
        "seed_capsule.json",
        "shard_map.json",
        "durability_receipt.json",
        "preauthorization_outcome.json",
        "launch_authorization.json",
        "postauthorization_outcome.json",
        "STARTED.json",
        "environment.json",
        "launch_receipt.json",
        "metrics/primary_metrics.json",
        "metrics/secondary_diagnostics.json",
        "independent_recomputation.json",
        "decisions.json",
        "deviations.json",
        "failures.json",
        "exclusions.json",
        "reruns.json",
        "terminal_state.json",
        "sha256_manifest.json",
        "COMMITTED.json",
    )
    expected_per_shard = (
        "shards/{shard_id}/requests.jsonl",
        "shards/{shard_id}/raw_records.jsonl",
        "shards/{shard_id}/stable_traces.jsonl",
        "shards/{shard_id}/stderr_records.bin",
        "shards/{shard_id}/rng_initial_states.json",
        "shards/{shard_id}/rng_final_states.json",
        "shards/{shard_id}/shard_index.json",
        "shards/{shard_id}/shard_receipt.json",
    )
    expected_conditional = (
        "seed_partial_acquisition_terminal_receipt.json",
        "rejected_launch_authorization_candidate.json",
    )
    assert durability.global_relative_paths == expected_global
    assert durability.per_shard_relative_paths == expected_per_shard
    assert durability.conditional_relative_paths == expected_conditional
    assert durability.conditional_path_rules == (
        (
            "seed_partial_acquisition_terminal_receipt.json",
            "required-iff-acquisition-start-committed-and-complete-source-receipt-absent",
        ),
        (
            "rejected_launch_authorization_candidate.json",
            "required-iff-preauthorization-terminal-arm-wins-after-a-durable-prepared-authorization-candidate-exists",
        ),
    )

    concrete_global = set(expected_global) | set(expected_conditional)
    expanded_final: set[str] = set()
    expanded_partial: set[str] = set()
    for template in expected_per_shard:
        assert template.count("{shard_id}") == 1
        for shard_ordinal in range(1, 33):
            expanded_final.add(template.format(shard_id=f"shard-{shard_ordinal:04d}"))
    for template in durability.reservation_destination_final_path_templates:
        assert template in expected_per_shard
        for shard_ordinal in range(1, 33):
            final = template.format(shard_id=f"shard-{shard_ordinal:04d}")
            expanded_partial.add(final + durability.temporary_suffix)
    assert len(concrete_global) == 38
    assert len(expanded_final) == 32 * 8
    assert len(expanded_partial) == 32 * 4
    assert not (concrete_global & expanded_final)
    assert not (concrete_global & expanded_partial)
    assert not (expanded_final & expanded_partial)

    for path in concrete_global | expanded_final | expanded_partial:
        pure = PurePosixPath(path)
        assert not pure.is_absolute()
        assert "\\" not in path
        assert "" not in path.split("/")
        assert "." not in pure.parts
        assert ".." not in pure.parts

    assert durability.temporary_suffix == ".partial"
    assert durability.exclusive_create_required is True
    assert durability.symlinks_permitted is False
    assert durability.hardlinks_permitted is False
    assert durability.overwrite_permitted is False
    assert durability.append_after_commit_permitted is False
    assert durability.same_directory_atomic_rename_required is True
    assert durability.file_fsync_before_rename_required is True
    assert durability.directory_fsync_after_rename_required is True
    assert durability.canonical_jsonl_final_newline_required is True
    assert (
        durability.stderr_frame_offsets_lengths_and_sha256_bound_in_shard_index is True
    )
    assert durability.raw_retained_separately is True
    assert durability.stable_projection_never_replaces_raw is True
    assert durability.shard_receipt_committed_last is True
    assert durability.receipt_present is False
    assert durability.writer_implemented is False
    assert durability.writer_qualified is False
    assert durability.filesystem_observed is False
    assert durability.durable_output_written is False
    assert durability.global_relative_paths[-1] == "COMMITTED.json"
    assert durability.global_relative_paths_scope == (
        "cp64-scaffolded-complete-acquisition-path-inventory-not-full-production-roster"
    )
    assert (
        durability.complete_source_receipt_and_partial_terminal_receipt_mutually_exclusive
        is True
    )


def test_cp64_reservation_uses_exact_destination_inodes_without_double_count() -> None:
    durability = (
        cp64.cp64_production_custody_preflight_bundle().durability_receipt_schema
    )
    assert durability.reservation_destination_final_path_templates == (
        "shards/{shard_id}/requests.jsonl",
        "shards/{shard_id}/raw_records.jsonl",
        "shards/{shard_id}/stable_traces.jsonl",
        "shards/{shard_id}/stderr_records.bin",
    )
    assert durability.reservation_allocation_unit_rule == (
        "exact-positive-power-of-two-at-most-1073741824-and-divides-34359738368"
    )
    assert durability.reservation_partition_formula == (
        "non-raw=ceil(payload-ceiling/allocation-unit)*allocation-unit;"
        "raw=34359738368-sum(non-raw);"
        "raw>=ceil(raw-ceiling/allocation-unit)*allocation-unit"
    )
    assert durability.reservation_per_shard_total_bytes == 34_359_738_368
    assert durability.reservation_global_total_bytes == 1_099_511_627_776
    assert durability.reservation_manifest_binds_per_file_reserved_bytes is True
    assert durability.reservation_partial_path_formula == "final_relative_path+.partial"
    assert durability.reservation_uses_actual_destination_partial_inodes is True
    assert (
        durability.reservation_manifest_binds_path_device_inode_extents_logical_and_allocated_bytes
        is True
    )
    assert durability.reservation_files_exclusive_non_sparse_preallocated is True
    assert durability.writer_consumes_reserved_partial_inodes_in_place is True
    assert durability.reservation_handoff_requires_inode_identity_match is True
    assert (
        durability.reservation_qualification_verifies_in_place_overwrite_without_copy_on_write_double_allocation
        is True
    )
    assert (
        durability.reserved_partial_truncation_only_after_complete_write_and_followed_by_file_fsync
        is True
    )
    assert durability.reserved_partial_files_absent_at_committed is True
    assert (
        durability.reservation_manifest_retained_and_manifest_bound_at_committed is True
    )
    assert durability.reservation_manifest_required is True
    assert durability.cow_no_double_allocation_qualification_required is True
    assert durability.cow_no_double_allocation_qualified is False
    assert durability.auxiliary_metadata_reservation_relative_path == (
        "auxiliary_metadata_reservation.json"
    )
    assert durability.auxiliary_metadata_reservation_retained_until_committed is True
    assert durability.auxiliary_metadata_reservation_manifest_bound_at_committed is True

    ceilings = {
        "raw": 17_179_870_208,
        "stable": 8_589_935_616,
        "request": 67_109_888,
        "stderr": 1_073_750_016,
    }
    floor = 34_359_738_368
    for allocation_unit in (2**power for power in range(31)):
        rounded = {
            name: ((ceiling + allocation_unit - 1) // allocation_unit) * allocation_unit
            for name, ceiling in ceilings.items()
        }
        raw_reservation = floor - sum(
            rounded[name] for name in ("stable", "request", "stderr")
        )
        assert raw_reservation % allocation_unit == 0
        assert raw_reservation >= rounded["raw"]
        assert (
            raw_reservation
            + sum(rounded[name] for name in ("stable", "request", "stderr"))
            == floor
        )


def test_cp64_reserved_destination_commit_and_final_publication_order_are_exact() -> None:
    durability = (
        cp64.cp64_production_custody_preflight_bundle().durability_receipt_schema
    )
    assert durability.reserved_destination_commit_order == (
        "open-partial-o_excl-o_nofollow",
        "non-sparse-preallocate-and-verify-extents",
        "write-canonical-bytes-in-place",
        "ftruncate-to-actual-length",
        "file-fsync-after-truncate",
        "hash-and-verify-final-bytes",
        "rename-no-replace-same-directory",
        "directory-fsync",
    )
    assert durability.rename_no_replace_required is True
    assert durability.committed_marker_exact_keys == (
        "schema",
        "purpose",
        "attempt_id",
        "terminal_state_sha256",
        "sha256_manifest_sha256",
        "committed_at_utc",
        "body_sha256",
    )
    assert durability.committed_marker_relative_path == "COMMITTED.json"
    assert durability.sha256_manifest_excludes_itself_and_committed_marker is True
    assert durability.committed_marker_binds_terminal_state_and_sha256_manifest is True
    assert durability.committed_marker_exclusive_create_required is True
    assert durability.committed_marker_file_fsync_required is True
    assert durability.committed_marker_directory_fsync_required is True
    assert durability.committed_marker_created_after_terminal_and_manifest is True
    assert durability.committed_marker_is_only_publication_boundary is True


def test_cp64_proposed_v15_preauthorization_terminal_publication_is_separate() -> None:
    durability = (
        cp64.cp64_production_custody_preflight_bundle().durability_receipt_schema
    )
    assert durability.proposed_v15_preauthorization_terminal_states == (
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    )
    assert durability.proposed_v15_preauthorization_crash_cuts == (
        "zero-source-values-after-start",
        "partial-source-values",
        "complete-seed-capsule-before-authorization",
        "later-preauthorization",
    )
    assert durability.proposed_v15_preauthorization_terminal_order == (
        "frozen-inputs",
        "freeze-receipt",
        "all-durable-prestart-artifacts",
        "applicable-acquisition-terminal-receipt",
        "preauthorization-outcome-terminal-arm",
        "applicable-rejected-authorization-candidate",
        "terminal-state",
        "sha256-manifest",
        "COMMITTED",
    )
    assert durability.proposed_v15_preauthorization_forbidden_stages == (
        "launch-authorization",
        "postauthorization-outcome",
        "STARTED",
        "shard-data",
        "shard-receipts",
        "independent-recomputation",
        "metrics",
        "decisions",
    )
    assert durability.preauthorization_terminal_retains_all_durable_artifacts is True
    assert (
        durability.preauthorization_terminal_state_binds_durable_artifact_inventory
        is True
    )
    assert (
        durability.preauthorization_sha256_manifest_binds_all_durable_prestart_artifacts
        is True
    )
    assert (
        durability.preauthorization_committed_marker_transitively_binds_all_durable_prestart_artifacts
        is True
    )

    assert durability.proposed_v15_postauthorization_prestart_terminal_states == (
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    )
    assert durability.proposed_v15_postauthorization_prestart_crash_cut == (
        "launch-authorization-durable-before-STARTED"
    )
    assert durability.proposed_v15_postauthorization_prestart_terminal_order == (
        "frozen-inputs",
        "freeze-receipt",
        "all-durable-prestart-artifacts",
        "preauthorization-outcome-authorization-arm",
        "launch-authorization",
        "postauthorization-outcome-terminal-arm",
        "terminal-state",
        "sha256-manifest",
        "COMMITTED",
    )
    assert durability.proposed_v15_postauthorization_prestart_forbidden_stages == (
        "STARTED",
        "shard-data",
        "shard-receipts",
        "independent-recomputation",
        "metrics",
        "decisions",
    )
    assert (
        durability.postauthorization_prestart_terminal_retains_launch_authorization
        is True
    )
    assert (
        durability.postauthorization_prestart_terminal_state_binds_launch_authorization
        is True
    )
    assert (
        durability.postauthorization_prestart_sha256_manifest_binds_launch_authorization
        is True
    )
    assert (
        durability.postauthorization_prestart_committed_marker_transitively_binds_launch_authorization
        is True
    )


def test_cp64_two_stage_outcomes_close_authorization_and_started_races() -> None:
    durability = (
        cp64.cp64_production_custody_preflight_bundle().durability_receipt_schema
    )
    assert durability.launch_authorization_prepared_partial_relative_path == (
        "launch_authorization.json.partial"
    )
    assert durability.launch_authorization_prepared_partial_relative_path == (
        "launch_authorization.json" + durability.temporary_suffix
    )
    assert durability.rejected_launch_authorization_candidate_relative_path == (
        "rejected_launch_authorization_candidate.json"
    )
    assert durability.preauthorization_outcome_relative_path == (
        "preauthorization_outcome.json"
    )
    assert durability.preauthorization_outcome_exact_keys == (
        "schema",
        "purpose",
        "attempt_id",
        "freeze_receipt_sha256",
        "outcome_arm",
        "prepared_launch_authorization_sha256",
        "terminal_state",
        "selected_at_utc",
        "body_sha256",
    )
    assert durability.preauthorization_outcome_allowed_arms == (
        "AUTHORIZATION",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    )
    assert durability.postauthorization_outcome_relative_path == (
        "postauthorization_outcome.json"
    )
    assert durability.postauthorization_outcome_exact_keys == (
        "schema",
        "purpose",
        "attempt_id",
        "freeze_receipt_sha256",
        "launch_authorization_sha256",
        "outcome_arm",
        "terminal_state",
        "selected_at_utc",
        "body_sha256",
    )
    assert durability.postauthorization_outcome_allowed_arms == (
        "STARTED",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    )
    prepared = PurePosixPath(
        durability.launch_authorization_prepared_partial_relative_path
    )
    assert not prepared.is_absolute()
    assert ".." not in prepared.parts
    assert str(prepared) not in durability.global_relative_paths
    assert str(prepared) not in durability.conditional_relative_paths
    assert (
        durability.preauthorization_outcome_relative_path
        in durability.global_relative_paths
    )
    assert (
        durability.postauthorization_outcome_relative_path
        in durability.global_relative_paths
    )
    assert (
        durability.rejected_launch_authorization_candidate_relative_path
        in durability.conditional_relative_paths
    )
    required_true = (
        "preauthorization_outcome_exclusive_create_and_nofollow_required",
        "preauthorization_outcome_file_and_directory_fsync_required",
        "authorization_candidate_must_be_o_excl_nofollow_written_and_fsynced_as_partial_before_authorization_arm",
        "authorization_arm_requires_nonzero_matching_prepared_authorization_sha256",
        "authorization_arm_recovery_publishes_verified_prepared_bytes_by_rename_no_replace_and_directory_fsync",
        "preauthorization_terminal_arm_requires_terminal_state_equal_arm",
        "preauthorization_terminal_arm_never_publishes_final_launch_authorization",
        "losing_prepared_authorization_candidate_is_retained_under_rejected_non_authorizing_path",
        "preauthorization_outcome_crash_recovery_completes_winner_without_reselection",
        "preauthorization_outcome_losers_refuse_without_side_effects",
        "postauthorization_outcome_requires_durable_final_launch_authorization",
        "postauthorization_outcome_exclusive_create_and_nofollow_required",
        "postauthorization_outcome_file_and_directory_fsync_required",
        "postauthorization_started_and_terminal_arms_mutually_exclusive",
        "postauthorization_outcome_crash_recovery_completes_winner_without_reselection",
        "postauthorization_outcome_losers_refuse_without_side_effects",
        "started_arm_effects_frozen_to_started_transition",
        "crash_after_started_arm_before_started_receipt_recovers_started_then_incomplete_without_production_rng_or_child",
        "crash_after_terminal_arm_before_terminal_receipt_completes_same_terminal_without_reselection",
        "both_outcome_receipts_retained_and_manifest_bound_at_committed",
        "started_receipt_must_bind_postauthorization_started_outcome",
        "terminal_state_must_bind_winning_terminal_outcome",
    )
    assert all(getattr(durability, name) is True for name in required_true)


def test_cp64_terminal_order_never_promotes_incomplete_evidence() -> None:
    terminal_order = (
        cp64.cp64_production_custody_preflight_bundle().durability_receipt_schema.terminal_order
    )
    assert terminal_order == (
        "frozen-inputs",
        "preflight-receipts",
        "launch-authorization-prepared-partial-fsynced",
        "preauthorization-outcome-authorization-arm",
        "launch-authorization",
        "postauthorization-outcome-started-arm",
        "STARTED",
        "shard-data",
        "shard-receipts",
        "independent-recomputation",
        "metrics",
        "decisions",
        "terminal-state",
        "sha256-manifest",
        "COMMITTED",
    )
    assert terminal_order.index("preauthorization-outcome-authorization-arm") < (
        terminal_order.index("launch-authorization")
    )
    assert terminal_order.index("postauthorization-outcome-started-arm") < (
        terminal_order.index("STARTED")
    )
    assert terminal_order.index("shard-receipts") < terminal_order.index(
        "independent-recomputation"
    )
    assert terminal_order.index("terminal-state") < terminal_order.index(
        "sha256-manifest"
    )
    assert terminal_order[-1] == "COMMITTED"


def test_cp64_future_digest_graph_is_exact_acyclic_and_one_way() -> None:
    gate = cp64.cp64_production_custody_preflight_bundle().no_execution_gate_contract
    expected_nodes = (
        "source-manifest",
        "dependency-lock-match-receipt",
        "power-threshold-receipt",
        "freeze-receipt",
        "external-seed-acquisition-start-receipt",
        "external-seed-source-receipt",
        "seed-capsule-body",
        "seed-capsule-sequence-crosscheck-receipt",
        "production-schedule",
        "production-runtime-receipt",
        "capacity-receipt",
        "durability-receipt",
        "production-shard-map-receipt",
        "production-runner-supervisor-qualification-receipt",
        "closed-refusal-failure-classifier-qualification-receipt",
        "independent-full-32768-recomputation-receipt",
        "independent-554-estimate-interval-decision-path-receipt",
        "preflight-gate-summary",
        "independent-signoff-set",
        "launch-authorization",
    )
    expected_edges = (
        ("source-manifest", "freeze-receipt"),
        ("source-manifest", "production-runtime-receipt"),
        ("source-manifest", "launch-authorization"),
        ("power-threshold-receipt", "freeze-receipt"),
        ("power-threshold-receipt", "launch-authorization"),
        ("freeze-receipt", "external-seed-acquisition-start-receipt"),
        ("freeze-receipt", "external-seed-source-receipt"),
        ("freeze-receipt", "production-runtime-receipt"),
        ("freeze-receipt", "launch-authorization"),
        ("external-seed-acquisition-start-receipt", "external-seed-source-receipt"),
        ("external-seed-source-receipt", "seed-capsule-body"),
        (
            "external-seed-source-receipt",
            "seed-capsule-sequence-crosscheck-receipt",
        ),
        ("external-seed-source-receipt", "launch-authorization"),
        ("seed-capsule-body", "production-schedule"),
        ("seed-capsule-body", "seed-capsule-sequence-crosscheck-receipt"),
        ("seed-capsule-body", "launch-authorization"),
        ("production-schedule", "capacity-receipt"),
        ("production-schedule", "production-shard-map-receipt"),
        ("production-schedule", "launch-authorization"),
        ("production-runtime-receipt", "launch-authorization"),
        ("capacity-receipt", "durability-receipt"),
        ("capacity-receipt", "production-shard-map-receipt"),
        ("capacity-receipt", "launch-authorization"),
        ("durability-receipt", "production-shard-map-receipt"),
        ("durability-receipt", "launch-authorization"),
        ("production-shard-map-receipt", "launch-authorization"),
        ("preflight-gate-summary", "independent-signoff-set"),
        ("preflight-gate-summary", "launch-authorization"),
        ("independent-signoff-set", "launch-authorization"),
        ("freeze-receipt", "preflight-gate-summary"),
        ("source-manifest", "preflight-gate-summary"),
        ("dependency-lock-match-receipt", "preflight-gate-summary"),
        ("production-runtime-receipt", "preflight-gate-summary"),
        ("external-seed-source-receipt", "preflight-gate-summary"),
        ("seed-capsule-sequence-crosscheck-receipt", "preflight-gate-summary"),
        ("production-schedule", "preflight-gate-summary"),
        ("capacity-receipt", "preflight-gate-summary"),
        ("durability-receipt", "preflight-gate-summary"),
        ("production-shard-map-receipt", "preflight-gate-summary"),
        (
            "production-runner-supervisor-qualification-receipt",
            "preflight-gate-summary",
        ),
        (
            "closed-refusal-failure-classifier-qualification-receipt",
            "preflight-gate-summary",
        ),
        ("independent-full-32768-recomputation-receipt", "preflight-gate-summary"),
        (
            "independent-554-estimate-interval-decision-path-receipt",
            "preflight-gate-summary",
        ),
        ("power-threshold-receipt", "preflight-gate-summary"),
    )
    assert gate.future_digest_node_order == expected_nodes
    assert gate.future_digest_edges == expected_edges
    assert len(expected_nodes) == 20
    assert len(expected_edges) == 44
    assert len(set(expected_nodes)) == len(expected_nodes)
    assert len(set(expected_edges)) == len(expected_edges)

    incoming = {node: 0 for node in expected_nodes}
    outgoing = {node: [] for node in expected_nodes}
    for source, target in expected_edges:
        outgoing[source].append(target)
        incoming[target] += 1
    frontier = [node for node in expected_nodes if incoming[node] == 0]
    visited: list[str] = []
    while frontier:
        source = frontier.pop()
        visited.append(source)
        for target in outgoing[source]:
            incoming[target] -= 1
            if incoming[target] == 0:
                frontier.append(target)
    assert len(visited) == len(expected_nodes)
    assert (
        len([edge for edge in expected_edges if edge[1] == "preflight-gate-summary"])
        == 15
    )
    assert (
        len([edge for edge in expected_edges if edge[1] == "independent-signoff-set"])
        == 1
    )
    assert outgoing["launch-authorization"] == []
    assert all(outgoing[node] for node in expected_nodes[:-1])
    assert ("seed-capsule-body", "external-seed-source-receipt") not in expected_edges
    assert ("production-shard-map-receipt", "capacity-receipt") not in expected_edges
    assert gate.source_receipt_binds_capsule_body is False
    assert gate.capacity_receipt_binds_shard_map is False
    assert gate.launch_authorization_is_only_final_downstream_aggregator is True
    assert gate.digest_dag_acyclic is True

    expected_evidence = (
        "freeze-receipt",
        "source-manifest",
        "dependency-lock-match-receipt",
        "production-runtime-receipt",
        "external-seed-source-receipt",
        "seed-capsule-sequence-crosscheck-receipt",
        "production-schedule",
        "capacity-receipt",
        "durability-receipt",
        "production-shard-map-receipt",
        "production-runner-supervisor-qualification-receipt",
        "closed-refusal-failure-classifier-qualification-receipt",
        "independent-full-32768-recomputation-receipt",
        "independent-554-estimate-interval-decision-path-receipt",
        "power-threshold-receipt",
    )
    assert gate.preflight_gate_summary_gate_ids == gate.production_gate_ids[:15]
    assert gate.preflight_gate_summary_evidence_node_ids == expected_evidence
    assert gate.preflight_gate_summary_ids_states_evidence_strictly_aligned is True
    assert gate.preflight_gate_summary_requires_all_covered_states_pass is True
    assert (
        gate.preflight_gate_summary_requires_exact_nonzero_sha256_per_covered_gate
        is True
    )
    assert gate.preflight_gate_summary_exact_keys == (
        "schema",
        "purpose",
        "attempt_id",
        "freeze_receipt_sha256",
        "covered_gate_ids",
        "covered_gate_states",
        "covered_evidence_node_ids",
        "ordered_evidence_receipt_sha256s",
        "body_sha256",
    )


def test_cp64_lifecycle_is_closed_and_has_no_transition_api() -> None:
    authorization = (
        cp64.cp64_production_custody_preflight_bundle().launch_authorization_receipt_schema
    )
    assert authorization.proposed_v15_lifecycle_states == (
        "DRAFT_PRE_FREEZE",
        "FROZEN",
        "STARTED",
        "PASS",
        "FAIL",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    )
    assert authorization.v14_allowed_attempt_states == (
        "FROZEN",
        "STARTED",
        "PASS",
        "FAIL",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    )
    assert authorization.v14_transition_graph == (
        ("FROZEN", "STARTED"),
        ("STARTED", "PASS"),
        ("STARTED", "FAIL"),
        ("STARTED", "INVALID_PROTOCOL"),
        ("STARTED", "ABORTED_INFRA"),
        ("STARTED", "INCOMPLETE"),
    )
    predecessor = cp64.cp64_production_custody_preflight_bundle().predecessor_custody
    assert predecessor.cp63_v14_allowed_attempt_states == (
        authorization.v14_allowed_attempt_states
    )
    assert predecessor.cp63_v14_transition_graph == authorization.v14_transition_graph
    assert authorization.proposed_v15_transition_graph == (
        ("DRAFT_PRE_FREEZE", "FROZEN"),
        ("FROZEN", "STARTED"),
        ("FROZEN", "INVALID_PROTOCOL"),
        ("FROZEN", "ABORTED_INFRA"),
        ("FROZEN", "INCOMPLETE"),
        ("STARTED", "PASS"),
        ("STARTED", "FAIL"),
        ("STARTED", "INVALID_PROTOCOL"),
        ("STARTED", "ABORTED_INFRA"),
        ("STARTED", "INCOMPLETE"),
    )
    assert authorization.current_state == "DRAFT_PRE_FREEZE"
    assert authorization.v15_protocol_and_manifest_amendment_required is True
    assert (
        authorization.proposed_v15_protocol_and_manifest_paths_available_to_builder
        is False
    )
    assert authorization.proposed_v15_protocol_and_manifest_consumed_by_bundle is False
    assert authorization.proposed_v15_protocol_relative_path == (
        "research/preregistrations/cp50_test28_mixed_initializer_v15.md"
    )
    assert authorization.proposed_v15_machine_manifest_relative_path == (
        "research/fixtures/cp50_test28_mixed_initializer_v15.json"
    )
    assert (
        authorization.proposed_v15_transition_graph_authoritative_for_production
        is False
    )
    assert (
        authorization.proposed_v15_transition_graph
        != authorization.v14_transition_graph
    )
    assert (
        authorization.preflight_and_authorization_are_artifact_stages_not_lifecycle_states
        is True
    )
    assert authorization.frozen_prestart_terminal_states == (
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    )
    assert (
        authorization.partial_external_seed_acquisition_terminal_state == "INCOMPLETE"
    )
    assert authorization.any_durable_external_seed_value_spends_attempt is True
    assert (
        authorization.no_redraw_reselection_replacement_after_durable_seed_acquisition
        is True
    )
    assert (
        authorization.pre_durable_output_infrastructure_abort_new_attempt_requires_written_independent_adjudication_and_identical_frozen_inputs
        is True
    )
    assert authorization.authorization_requires_frozen_attempt_state is True
    assert (
        authorization.authorization_must_follow_preauthorization_outcome_authorization_arm
        is True
    )
    assert authorization.authorization_is_artifact_stage_not_lifecycle_state is True
    assert authorization.authorization_must_precede_postauthorization_outcome is True
    assert authorization.authorization_does_not_equal_started is True
    assert (
        authorization.postauthorization_started_outcome_and_binding_started_receipt_must_be_durable_before_production_runner_rng_or_child
        is True
    )
    assert authorization.transition_api_exposed is False
    assert authorization.receipt_present is False
    assert authorization.authority_verified is False
    assert authorization.launch_authorized is False
    assert authorization.started is False
    exported = set(cp64.__all__)
    assert not any("transition" in name.lower() for name in exported)
    assert not any("authorize" in name.lower() for name in exported)
    assert not any("start" in name.lower() for name in exported)


def test_cp64_launch_authorization_exactly_binds_frozen_upstream_receipts() -> None:
    authorization = (
        cp64.cp64_production_custody_preflight_bundle().launch_authorization_receipt_schema
    )
    assert authorization.exact_keys == (
        "schema",
        "purpose",
        "attempt_id",
        "attempt_state",
        "protocol_sha256",
        "machine_manifest_sha256",
        "source_manifest_sha256",
        "dependency_lock_sha256",
        "seed_source_receipt_sha256",
        "seed_capsule_body_sha256",
        "schedule_sha256",
        "production_runtime_receipt_sha256",
        "capacity_receipt_sha256",
        "durability_receipt_sha256",
        "production_shard_map_receipt_sha256",
        "preflight_gate_summary_sha256",
        "power_threshold_receipt_sha256",
        "freeze_receipt_sha256",
        "independent_signoff_sha256",
        "authorized_attempt_number",
        "authorization_issued_at_utc",
        "authorization_expires_at_utc",
        "authority_scheme_id",
        "authority_identity_sha256",
        "authority_signature_sha256",
        "body_sha256",
    )
    assert authorization.record_sha256 == (
        "0c60d5484e0efb50991a95fa7da4b191dae7c48f25568f24207e594132ac17b5"
    )
    assert len(cp64.cp64_canonical_json_bytes(authorization)) == 3_146
    assert cp64.cp64_sha256(authorization) == (
        "e34a58e41ad1a79b23ab55feb3ec9658efbc4029c57ed912f4256918a57b6b8c"
    )


def test_cp64_all_future_receipt_schemas_have_exact_closed_keys_and_purposes() -> None:
    bundle = cp64.cp64_production_custody_preflight_bundle()
    assert bundle.external_seed_source_receipt_schema.purpose == (
        "future-production-source-custody-only"
    )
    assert bundle.production_runtime_receipt_schema.purpose == (
        "future-production-runtime-source-abi-custody"
    )
    assert bundle.capacity_receipt_schema.purpose == (
        "future-production-capacity-preflight-only"
    )
    assert bundle.durability_receipt_schema.purpose == (
        "future-production-durable-writer-qualification-only"
    )
    assert bundle.production_shard_map_receipt_schema.purpose == (
        "future-production-shard-map-selection-only"
    )
    assert bundle.launch_authorization_receipt_schema.purpose == (
        "future-explicit-production-launch-authorization-only"
    )
    assert bundle.production_runtime_receipt_schema.exact_keys == (
        "schema",
        "purpose",
        "attempt_id",
        "freeze_receipt_sha256",
        "observation_session_sha256",
        "observed_at_utc",
        "source_manifest_sha256",
        "dependency_lock_sha256",
        "runtime_profile_id",
        "python_executable_sha256",
        "python_framework_sha256",
        "stdlib_closure_sha256",
        "numpy_record_sha256",
        "numpy_payload_closure_sha256",
        "scipy_record_sha256",
        "scipy_payload_closure_sha256",
        "loaded_local_source_closure_sha256",
        "abi_map_sha256",
        "environment_sha256",
        "body_sha256",
    )
    assert bundle.durability_receipt_schema.exact_keys == (
        "schema",
        "purpose",
        "attempt_id",
        "capacity_receipt_sha256",
        "layout_contract_sha256",
        "writer_source_manifest_sha256",
        "qualification_session_sha256",
        "filesystem_identity_sha256",
        "atomic_rename_verified",
        "file_fsync_verified",
        "directory_fsync_verified",
        "exclusive_create_verified",
        "no_symlink_verified",
        "no_hardlink_verified",
        "no_overwrite_verified",
        "body_sha256",
    )
    shard_map = bundle.production_shard_map_receipt_schema
    assert shard_map.exact_keys == (
        "schema",
        "purpose",
        "attempt_id",
        "seed_capsule_body_sha256",
        "schedule_sha256",
        "capacity_receipt_sha256",
        "durability_receipt_sha256",
        "candidate_shard_policy_sha256",
        "reservation_manifest_sha256",
        "shard_count",
        "shards",
        "body_sha256",
    )
    assert shard_map.shard_record_exact_keys == (
        "shard_ordinal",
        "shard_id",
        "seed_ordinal_min",
        "seed_ordinal_max",
        "logical_request_ordinal_min",
        "logical_request_ordinal_max",
        "logical_request_count",
        "relative_directory",
        "capacity_partition_bytes",
        "per_file_reservation_manifest_entry_sha256s",
        "shard_record_sha256",
    )


def test_cp64_bundle_receipt_is_exact_and_excludes_its_own_source_hash() -> None:
    bundle = cp64.cp64_production_custody_preflight_bundle()
    canonical = cp64.cp64_canonical_json_bytes(bundle)
    source_sha = _file_sha256(_SOURCE)
    assert len(canonical) == 77_595
    assert bundle.record_sha256 == (
        "32f7f0c62019d8ee906e6f74300f6c33fbe55984f69cfe4fe1061ffb92463f39"
    )
    assert cp64.cp64_sha256(bundle) == (
        "caecd8630def94f7ac6da721422e3d9d71c26c351e753369abf17b224a90de83"
    )
    assert source_sha.encode("ascii") not in canonical
    assert bundle.predecessor_custody.cp64_source_hash_in_record is False
    assert bundle.predecessor_custody.cp64_source_hash_external_binding_required is True


def test_cp64_all_seventeen_production_gates_are_missing() -> None:
    gate = cp64.cp64_production_custody_preflight_bundle().no_execution_gate_contract
    assert gate.production_gate_ids == (
        "v15-protocol-sidecar-and-machine-manifest-frozen",
        "complete-production-source-manifest",
        "exact-dependency-lock-matched",
        "full-production-runtime-lock-recomputed-and-matched",
        "external-seed-source-receipt-and-authority",
        "external-seed-capsule-sequence-crosscheck",
        "production-request-schedule-materialized",
        "capacity-receipt-meets-usable-and-quota-floor",
        "durable-writer-qualified",
        "production-shard-map-selected-and-materialized",
        "production-runner-supervisor-qualified",
        "closed-refusal-failure-classifier-qualified",
        "independent-full-32768-recomputation-qualified",
        "independent-554-estimate-interval-decision-path-qualified",
        "power-review-and-32-primary-thresholds-frozen",
        "independent-review-signoffs-present",
        "explicit-launch-authorization-present",
    )
    assert len(gate.production_gate_ids) == 17
    assert len(set(gate.production_gate_ids)) == 17
    assert gate.production_gate_states == ("MISSING",) * 17
    assert gate.requirement_schemas_frozen is False
    assert gate.cp64_scaffolded_receipt_keysets_and_cross_bindings_predeclared is True
    assert gate.all_required_production_receipt_keysets_predeclared is False
    assert gate.complete_receipt_type_range_size_and_domain_schemas_frozen is False
    assert gate.complete_auxiliary_artifact_size_schema_frozen is False
    assert gate.bounded_auxiliary_artifact_size_proof_present is False
    assert gate.generic_prestart_terminal_record_schema_frozen is False
    assert gate.all_required_production_receipt_digest_preimages_frozen is False
    assert gate.authorization_signature_preimage_and_verifier_frozen is False
    assert gate.production_evidence_required_count == 17
    assert gate.production_evidence_present_count == 0
    assert gate.preauthorization_gate_count == 16
    assert gate.preflight_gate_summary_covered_gate_count == 15
    assert gate.preflight_gate_summary_gate_ids == gate.production_gate_ids[:15]
    assert (
        gate.preflight_gate_summary_excludes_independent_signoff_and_launch_authorization
        is True
    )
    false_fields = (
        "external_seed_values_present",
        "source_authority_verified",
        "full_runtime_lock_recomputed",
        "capacity_measured",
        "durability_verified",
        "production_shard_map_bound",
        "production_runner_supervisor_qualified",
        "preflight_gate_summary_present",
        "closed_refusal_failure_classifier_qualified",
        "freeze_receipt_present",
        "power_thresholds_frozen",
        "independent_signoffs_present",
        "launch_authorization_present",
        "started",
        "production_request_materialization_exposed",
        "production_campaign_exposed",
        "preflight_passed",
        "execution_authorized",
    )
    assert all(getattr(gate, name) is False for name in false_fields)
    assert gate.readiness_state == "BLOCKED_MISSING_PRODUCTION_EVIDENCE"


def test_cp64_bundle_never_claims_production_or_blocker_closure() -> None:
    bundle = cp64.cp64_production_custody_preflight_bundle()
    true_fields = (
        "zero_argument_builder",
        "stdlib_only_import",
        "cp64_scaffolded_receipt_keysets_and_cross_bindings_predeclared",
        "candidate_shard_policy_frozen",
        "cp64_scaffolded_custody_preflight_inventory_and_policy_scaffold_complete",
    )
    false_fields = (
        "project_modules_imported",
        "host_filesystem_probed",
        "proposed_v15_protocol_and_manifest_paths_available_to_builder",
        "proposed_v15_protocol_and_manifest_consumed_by_bundle",
        "all_required_production_receipt_keysets_predeclared",
        "complete_receipt_type_range_size_and_domain_schemas_frozen",
        "complete_auxiliary_artifact_size_schema_frozen",
        "bounded_auxiliary_artifact_size_proof_present",
        "generic_prestart_terminal_record_schema_frozen",
        "all_required_production_receipt_digest_preimages_frozen",
        "authorization_signature_preimage_and_verifier_frozen",
        "candidate_shard_policy_selected_for_production",
        "external_seed_values_present",
        "external_seed_source_bound",
        "external_seed_source_receipt_present",
        "production_seed_capsule_present",
        "production_runtime_receipt_present",
        "capacity_receipt_present",
        "capacity_reservation_present",
        "durability_receipt_present",
        "production_shard_map_receipt_present",
        "freeze_receipt_present",
        "power_threshold_receipt_present",
        "independent_signoffs_present",
        "launch_authorization_present",
        "started_receipt_present",
        "committed_marker_present",
        "durable_writer_implemented",
        "production_runner_supervisor_qualified",
        "closed_refusal_failure_classification_implemented",
        "preflight_gate_summary_present",
        "production_runner_bound",
        "production_schema_frozen",
        "production_requests_materialized",
        "production_campaign_exposed",
        "production_execution_authorized",
        "production_execution_observed",
        "estimates_computed",
        "intervals_computed",
        "decision_made",
        "runner_and_recomputation_blocker_closed",
        "unconditional_operational_predictions_blocker_closed",
        "power_and_thresholds_blocker_closed",
        "confirmatory_custody_blocker_closed",
        "confirmatory_evidence",
        "manuscript_claim",
        "formal_test_28_closed",
    )
    assert all(getattr(bundle, name) is True for name in true_fields)
    assert all(getattr(bundle, name) is False for name in false_fields)
    assert bundle.v15_protocol_and_manifest_amendment_required is True
    assert bundle.proposed_v15_protocol_relative_path.endswith(
        "cp50_test28_mixed_initializer_v15.md"
    )
    assert bundle.proposed_v15_machine_manifest_relative_path.endswith(
        "cp50_test28_mixed_initializer_v15.json"
    )
    assert bundle.formal_test_28_status == "OPEN"
    assert bundle.scope == (
        "zero-execution-production-custody-preflight-scaffold;proposed-v15-"
        "lifecycle-amendment-required-not-consumed-by-bundle;no-external-seed-"
        "values;no-source-authority;no-runtime-match;no-capacity-observation;no-"
        "filesystem-write;no-production-request;no-campaign;no-authorization;no-"
        "execution;no-blocker-closure"
    )


def test_cp64_only_definition_api_is_exposed() -> None:
    exported_functions = {
        name for name in cp64.__all__ if inspect.isfunction(getattr(cp64, name))
    }
    assert exported_functions == {
        "cp64_production_custody_preflight_bundle",
        "cp64_candidate_shard_for_logical_ordinal",
        "cp64_candidate_shard_bounds",
        "cp64_canonical_json_bytes",
        "cp64_sha256",
    }
    prohibited_fragments = (
        "parse",
        "ingest",
        "seed_capsule",
        "bound_request",
        "materialize",
        "campaign",
        "execute",
        "run_",
        "write",
        "probe",
        "reserve",
        "allocate",
        "authorize",
        "transition",
        "classify",
    )
    assert not any(
        fragment in name.lower()
        for name in exported_functions
        for fragment in prohibited_fragments
    )


@pytest.mark.parametrize("record_type, expected", tuple(_COMPONENT_PINS.items()))
def test_cp64_component_semantic_receipts_are_exactly_pinned(
    record_type: type,
    expected: tuple[int, str, str, str],
) -> None:
    record = next(
        item
        for item in _all_records(cp64.cp64_production_custody_preflight_bundle())
        if type(item) is record_type
    )
    canonical = cp64.cp64_canonical_json_bytes(record)
    (
        expected_bytes,
        expected_plain_sha,
        expected_record_sha,
        expected_public_sha,
    ) = expected
    assert len(canonical) == expected_bytes
    assert hashlib.sha256(canonical).hexdigest() == expected_plain_sha
    assert record.record_sha256 == expected_record_sha
    assert cp64.cp64_sha256(record) == expected_public_sha


@pytest.mark.parametrize("record_type, domain", tuple(_RECORD_DOMAINS.items()))
def test_cp64_record_digest_and_public_digest_are_independently_recomputed(
    record_type: type, domain: bytes
) -> None:
    records = _all_records(cp64.cp64_production_custody_preflight_bundle())
    record = next(item for item in records if type(item) is record_type)
    body = _plain(record)
    assert isinstance(body, dict)
    body["record_sha256"] = _ZERO_SHA256
    expected_record = hashlib.sha256(
        domain
        + b"\0"
        + json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    assert record.record_sha256 == expected_record
    canonical = _plain_json_bytes(record)
    assert cp64.cp64_canonical_json_bytes(record) == canonical
    expected_public = hashlib.sha256(
        b"cp64-public-record-v1\0"
        + type(record).__name__.encode("ascii")
        + b"\0"
        + canonical
    ).hexdigest()
    assert cp64.cp64_sha256(record) == expected_public


def test_cp64_all_forty_two_issued_records_validate() -> None:
    records = _all_records(cp64.cp64_production_custody_preflight_bundle())
    assert len(records) == 42
    assert sum(type(item) is cp64.CP64CandidateShardV1 for item in records) == 32
    for record in records:
        assert len(record.record_sha256) == 64
        assert record.record_sha256 != _ZERO_SHA256
        assert cp64.cp64_canonical_json_bytes(record) == _plain_json_bytes(record)
        assert len(cp64.cp64_sha256(record)) == 64


@pytest.mark.parametrize("record_type", tuple(_EXPECTED_FIELDS))
def test_cp64_records_reject_direct_construction_and_subclassing(
    record_type: type,
) -> None:
    with pytest.raises(TypeError, match="module-created only"):
        record_type()
    with pytest.raises(TypeError, match="cannot be subclassed"):
        type("ForgedSubclass", (record_type,), {})


@pytest.mark.parametrize("record_type", tuple(_EXPECTED_FIELDS))
def test_cp64_object_new_forgery_and_redigest_are_rejected(record_type: type) -> None:
    issued = next(
        item
        for item in _all_records(cp64.cp64_production_custody_preflight_bundle())
        if type(item) is record_type
    )
    forged = object.__new__(record_type)
    for item in fields(record_type):
        object.__setattr__(forged, item.name, getattr(issued, item.name))
    body = _plain(forged)
    assert isinstance(body, dict)
    body["record_sha256"] = _ZERO_SHA256
    digest = hashlib.sha256(
        _RECORD_DOMAINS[record_type]
        + b"\0"
        + json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    object.__setattr__(forged, "record_sha256", digest)
    with pytest.raises(TypeError, match="not module-created"):
        cp64.cp64_canonical_json_bytes(forged)
    with pytest.raises(TypeError, match="not module-created"):
        cp64.cp64_sha256(forged)


def test_cp64_issued_record_mutation_is_detected_even_after_redigest() -> None:
    record = cp64.cp64_candidate_shard_bounds(1)
    original = record.shard_id
    object.__setattr__(record, "shard_id", "shard-9999")
    body = _plain(record)
    assert isinstance(body, dict)
    body["record_sha256"] = _ZERO_SHA256
    redigest = hashlib.sha256(
        _RECORD_DOMAINS[type(record)]
        + b"\0"
        + json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    object.__setattr__(record, "record_sha256", redigest)
    with pytest.raises(ValueError, match="mutated"):
        cp64.cp64_canonical_json_bytes(record)
    with pytest.raises(ValueError, match="mutated"):
        cp64.cp64_sha256(record)
    object.__setattr__(record, "shard_id", original)


def test_cp64_records_reject_pickle_and_ordinary_setattr() -> None:
    record = cp64.cp64_candidate_shard_bounds(1)
    with pytest.raises(TypeError):
        pickle.dumps(record)
    with pytest.raises((AttributeError, TypeError)):
        setattr(record, "shard_id", "shard-9999")
    with pytest.raises((AttributeError, TypeError)):
        setattr(record, "extra", True)


def test_cp64_issuance_registry_is_weak() -> None:
    gc.collect()
    baseline = len(cp64._ISSUED_RECORD_SNAPSHOTS)
    record = cp64.cp64_candidate_shard_bounds(1)
    reference = weakref.ref(record)
    assert len(cp64._ISSUED_RECORD_SNAPSHOTS) == baseline + 1
    del record
    gc.collect()
    assert reference() is None
    assert len(cp64._ISSUED_RECORD_SNAPSHOTS) == baseline


def test_cp64_issuance_and_validation_are_thread_safe() -> None:
    failures: list[BaseException] = []
    results: list[tuple[str, str]] = []
    lock = threading.Lock()

    def worker(index: int) -> None:
        try:
            record = cp64.cp64_candidate_shard_for_logical_ordinal(index % 32_768 + 1)
            result = (record.record_sha256, cp64.cp64_sha256(record))
            with lock:
                results.append(result)
        except BaseException as error:  # pragma: no cover - hostile collection
            with lock:
                failures.append(error)

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(128)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert failures == []
    assert len(results) == 128
    assert all(
        len(record_sha) == len(public_sha) == 64 for record_sha, public_sha in results
    )


@pytest.mark.parametrize(
    "value",
    (None, True, False, 0, "", (), {}, [], 1.0, float("nan"), object()),
)
def test_cp64_public_canonical_and_sha_reject_nonrecords(value: object) -> None:
    with pytest.raises(TypeError):
        cp64.cp64_canonical_json_bytes(value)
    with pytest.raises(TypeError):
        cp64.cp64_sha256(value)
