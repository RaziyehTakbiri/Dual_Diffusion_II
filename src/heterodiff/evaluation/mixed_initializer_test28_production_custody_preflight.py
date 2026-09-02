"""Definition-only CP64 production-custody preflight boundary.

This module describes the receipts, deterministic candidate shard policy, and
fail-closed launch gates that must exist before Test 28 production execution
can be authorized.  It does not parse or acquire a seed capsule, inspect a
runtime, probe or allocate storage, write an attempt, authorize a launch, or
execute numerical work.

Only the Python standard library is imported.  Exported builders have
deterministic canonical outputs and no host-filesystem, RNG, network, process,
or project-state side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
import threading
from typing import Mapping, Tuple, cast
import weakref


CP64_TEST28_SCHEMA_VERSION = "cp64-test28-production-custody-preflight-v1"
CP64_TEST28_SCOPE = (
    "zero-execution-production-custody-preflight-scaffold;proposed-v15-"
    "lifecycle-amendment-required-not-consumed-by-bundle;no-external-seed-"
    "values;no-source-authority;no-runtime-match;no-capacity-observation;no-"
    "filesystem-write;no-production-request;no-campaign;no-authorization;no-"
    "execution;no-blocker-closure"
)

_ZERO_SHA256 = "0" * 64
_ALLOW_RECORD_CLASS_DEFINITION = True

_CP61_STABLE_DESIGN_SHA256 = (
    "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
)
_CP62_SOURCE_SHA256 = "44ef12b1a556d80944774ac9b698acf1359879fe44729120a04feb5e7a4a8a49"
_CP62_BUNDLE_SHA256 = "0f92f54ce8d451485019f6d697736fd5eb48d2b942e1d3a3f1bd373b50c3ec92"
_CP62_RUNTIME_LOCK_RECORD_SHA256 = (
    "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
)
_CP62_SUPERVISOR_CONTRACT_RECORD_SHA256 = (
    "6dfb5b8bbb7cecabed1c84349bc32ac130dd2fb698ba400e0ce74d3ef58434fb"
)
_CP62_PROJECTION_CONTRACT_RECORD_SHA256 = (
    "1d42337a0191822fb7d7fa81883bab08101dbf68cd88e1b835553bc96fb32733"
)
_CP63_RUNNER_SOURCE_SHA256 = (
    "27259edf2557a21b2527595eed7a954fc697755935e4a3deaeeb169765ba1c9c"
)
_CP63_RUNNER_BUNDLE_RECORD_SHA256 = (
    "442c4b0f134a96efe32b5246b4eb5b05233d61a13c62c0a7d1f21c9bbbd32f85"
)
_CP63_SCHEDULE_CONTRACT_RECORD_SHA256 = (
    "7ca5555de1aa852021c6b7fd181417a629dcec461455650ecafc495f5e6fb607"
)
_CP63_SEED_CAPSULE_CONTRACT_RECORD_SHA256 = (
    "1765adf642962c73b61634dde767fe9d2c2fef5fd71c21305fe43c6d338cf80d"
)
_CP63_LIFECYCLE_CONTRACT_RECORD_SHA256 = (
    "e335fe95f81c69ebe632a00344248d48095ceffb5c8cc1b7e4c5770b4f5a951a"
)
_CP63_RAW_RECORD_SCHEMA_RECORD_SHA256 = (
    "29f17aa7528971e7892b6ea4ccb37b5943190a0e592191341ae444e8ed63b3cb"
)
_CP63_RESOURCE_CONTRACT_RECORD_SHA256 = (
    "17259329bbca1029e989029594af67570f81731d9b21355a5151277ba7938d40"
)
_CP63_INDEPENDENT_SOURCE_SHA256 = (
    "5df076a008d8fe6848dc72083e2563e622c136ce0159441dd69db04c3b1cb9dc"
)
_CP63_INDEPENDENT_BUNDLE_RECORD_SHA256 = (
    "b219de24a17af7c06b503af07110ed863c339bca19c7457c163412ae0e76ddb9"
)
_CP63_INDEPENDENT_BUNDLE_PUBLIC_SHA256 = (
    "473f7aa7fec510c92ea5f47c5bab79636fc84932986f6c5f420fb0e4c189594b"
)
_CP63_ACCEPTANCE_RECEIPT_SHA256 = (
    "2b2f41f14424ddb164b6db793991ece8b222a4e4295d7e0143c6b6496c50097b"
)
_CP63_SEMANTIC_PIN_RECEIPT_SHA256 = (
    "d7dfdae440b3b26b289279ccdda6e665fe43fee965c0836fe1d6dac91ce8d5e7"
)
_DEPENDENCY_LOCK_PATH = "requirements/m1-reference-macos-arm64-py311.lock"
_DEPENDENCY_LOCK_SHA256 = (
    "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d"
)


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("CP64 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("CP64 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP64 records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False)
class CP64PredecessorCustodyV1(_SealedRecord):
    schema_version: str
    cp63_protocol_relative_path: str
    cp63_protocol_sha256: str
    cp63_protocol_bytes: int
    cp63_protocol_lines: int
    cp63_machine_manifest_relative_path: str
    cp63_machine_manifest_sha256: str
    cp63_machine_manifest_bytes: int
    cp63_machine_manifest_lines: int
    cp63_protocol_id: str
    cp63_protocol_state: str
    cp63_manifest_schema_version: str
    cp63_bound_artifact_count: int
    cp63_development_verification_record_count: int
    cp63_ledger_total_count: int
    cp63_ledger_satisfied_count: int
    cp63_ledger_missing_count: int
    cp63_aggregate_test_count: int
    cp63_lifecycle_current_state: str
    cp63_v14_allowed_attempt_states: Tuple[str, ...]
    cp63_v14_transition_graph: Tuple[Tuple[str, str], ...]
    cp63_freeze_state: str
    cp63_confirmatory_execution_authorized: bool
    cp63_formal_test_28_status: str
    cp63_formal_test_28_closed: bool
    cp61_stable_design_sha256: str
    cp62_source_sha256: str
    cp62_bundle_sha256: str
    cp62_runtime_lock_record_sha256: str
    cp62_supervisor_contract_record_sha256: str
    cp62_projection_contract_record_sha256: str
    cp63_runner_source_sha256: str
    cp63_runner_bundle_record_sha256: str
    cp63_schedule_contract_record_sha256: str
    cp63_seed_capsule_contract_record_sha256: str
    cp63_lifecycle_contract_record_sha256: str
    cp63_raw_record_schema_record_sha256: str
    cp63_resource_contract_record_sha256: str
    cp63_independent_source_sha256: str
    cp63_independent_bundle_record_sha256: str
    cp63_independent_bundle_public_sha256: str
    cp63_acceptance_receipt_sha256: str
    cp63_semantic_pin_receipt_sha256: str
    dependency_lock_path: str
    dependency_lock_sha256: str
    cp64_source_hash_in_record: bool
    cp64_source_hash_external_binding_required: bool
    predecessor_custody_only: bool
    complete_production_source_manifest_present: bool
    production_runtime_match_verified: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP64ExternalSeedSourceReceiptSchemaV1(_SealedRecord):
    schema_version: str
    receipt_schema: str
    purpose: str
    exact_keys: Tuple[str, ...]
    acquisition_start_receipt_exact_keys: Tuple[str, ...]
    partial_acquisition_terminal_receipt_exact_keys: Tuple[str, ...]
    acquisition_start_receipt_relative_path: str
    partial_acquisition_terminal_receipt_relative_path: str
    acquisition_journal_relative_path: str
    acquisition_journal_encoding: str
    acquisition_journal_entry_bytes: int
    acquisition_journal_max_entries: int
    acquisition_journal_max_bytes: int
    acquisition_journal_initial_head_formula: str
    acquisition_journal_entry_digest_formula: str
    acquisition_journal_entry_field_order: Tuple[str, ...]
    acquisition_journal_entry_ordinals_strictly_increasing_from_one: bool
    acquisition_journal_exclusive_create_required: bool
    acquisition_journal_nofollow_required: bool
    acquisition_journal_non_sparse_physical_allocation_required: bool
    acquisition_journal_file_fsync_before_acquisition_start_receipt_required: bool
    acquisition_journal_directory_fsync_before_acquisition_start_receipt_required: bool
    acquisition_journal_path_inode_recheck_before_acquisition_start_receipt_required: bool
    acquisition_journal_path_inode_recheck_before_each_entry_append_required: bool
    acquisition_journal_preallocated_before_source_contact: bool
    acquisition_journal_entry_fsync_before_next_source_draw: bool
    acquisition_journal_every_entry_including_final_entry_fsync_required: bool
    acquisition_journal_final_fsync_before_completed_source_receipt_required: bool
    acquisition_journal_no_resume_after_crash: bool
    acquisition_journal_recovery_terminal_state: str
    acquisition_journal_topup_redraw_reselection_permitted: bool
    acquisition_journal_recovery_accepts_only_longest_valid_fsynced_prefix: bool
    acquisition_journal_torn_or_invalid_suffix_is_not_value_evidence: bool
    attempt_binding_required: bool
    freeze_receipt_binding_required: bool
    seed_count: int
    seed_encoding: str
    sequence_commitment_formula: str
    receipt_digest_formula: str
    capsule_body_digest_bound_by_source_receipt: bool
    source_receipt_digest_referenced_by_capsule: bool
    capsule_sequence_commitment_crosscheck_required: bool
    completed_source_receipt_binds_acquisition_journal_sha_head_and_count: bool
    completed_journal_entry_count_must_equal_seed_count: bool
    completed_journal_head_must_equal_entry_digest_at_seed_count: bool
    completed_journal_ordinal_value_sequence_commitment_must_equal_source_receipt_ordered_seed_values_commitment: bool
    capsule_ordered_seed_values_commitment_must_equal_completed_journal_sequence_commitment: bool
    canonical_syntax_can_prove_iid: bool
    digest_can_authenticate_source: bool
    acquisition_start_receipt_required: bool
    acquisition_start_receipt_exclusive_create_required: bool
    acquisition_start_receipt_file_fsync_required: bool
    acquisition_start_receipt_directory_fsync_required: bool
    acquisition_start_must_be_durably_committed_before_source_contact: bool
    acquisition_session_sha256_is_start_receipt_sha256: bool
    committed_acquisition_start_receipt_spends_attempt: bool
    any_durable_external_seed_value_spends_attempt: bool
    source_return_without_journal_fsync_spends_attempt: bool
    source_return_without_journal_fsync_terminal_state: str
    source_return_without_journal_fsync_value_is_claimed_retained: bool
    source_return_without_journal_fsync_resume_topup_redraw_permitted: bool
    durably_journaled_partial_acquisition_values_must_be_retained: bool
    partial_acquisition_terminal_receipt_required: bool
    partial_acquisition_terminal_state: str
    partial_acquisition_topup_redraw_reselection_permitted: bool
    receipt_values_present: bool
    source_authority_verified: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP64ProductionRuntimeReceiptSchemaV1(_SealedRecord):
    schema_version: str
    receipt_schema: str
    purpose: str
    exact_keys: Tuple[str, ...]
    cp62_candidate_runtime_lock_sha256: str
    dependency_lock_sha256: str
    complete_source_manifest_required: bool
    cp64_source_external_binding_required: bool
    preimport_environment_required: bool
    loaded_local_source_closure_required: bool
    compiled_abi_map_required: bool
    receipt_attempt_binding_required: bool
    receipt_freeze_binding_required: bool
    observation_must_postdate_freeze: bool
    receipt_present: bool
    full_runtime_lock_recomputed: bool
    production_runtime_match_verified: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP64CapacityReceiptSchemaV1(_SealedRecord):
    schema_version: str
    receipt_schema: str
    purpose: str
    exact_keys: Tuple[str, ...]
    cp63_resource_contract_record_sha256: str
    global_payload_ceiling_bytes: int
    global_destination_reservation_bytes: int
    global_auxiliary_metadata_conservative_policy_reservation_bytes: int
    global_combined_available_and_quota_required_before_reservation_bytes: int
    global_available_and_quota_required_after_destination_before_auxiliary_reservation_bytes: int
    auxiliary_metadata_reservation_is_conservative_policy_floor: bool
    complete_auxiliary_artifact_size_schema_frozen: bool
    bounded_auxiliary_artifact_size_proof_required_before_capacity_pass: bool
    bounded_auxiliary_artifact_size_proof_present: bool
    auxiliary_metadata_must_fit_exclusive_auxiliary_reservation: bool
    acquisition_journal_maximum_bytes: int
    acquisition_journal_counted_within_auxiliary_metadata_reserve: bool
    per_shard_payload_ceiling_bytes: int
    per_shard_destination_reservation_bytes: int
    candidate_shard_count: int
    minimum_available_inodes: int
    combined_available_and_quota_before_reservation_each_must_meet_floor: bool
    before_reservation_available_and_quota_each_meet_combined_floor_required: bool
    after_destination_before_auxiliary_available_and_quota_each_meet_auxiliary_floor_required: bool
    destination_and_auxiliary_reservations_both_exclusive_required: bool
    destination_and_auxiliary_reservations_no_double_count_required: bool
    auxiliary_metadata_reservation_method_rule: str
    auxiliary_metadata_physical_and_quota_reservations_both_required: bool
    quota_only_auxiliary_reservation_sufficient: bool
    auxiliary_metadata_reservation_artifact_relative_path: str
    auxiliary_metadata_reservation_same_storage_root_required: bool
    auxiliary_metadata_reservation_retained_until_committed: bool
    auxiliary_metadata_reservation_consumed_in_place_and_enforced_quota_required: bool
    post_destination_free_space_or_quota_snapshot_alone_sufficient: bool
    same_filesystem_required: bool
    measurement_must_postdate_freeze: bool
    measurement_must_predate_authorization: bool
    reservation_receipt_required: bool
    non_sparse_reservation_required: bool
    reservation_same_filesystem_required: bool
    destination_effective_reservation_formula: str
    auxiliary_effective_reservation_formula: str
    combined_effective_reservation_formula: str
    capacity_pass_predicate: str
    snapshot_only_sufficient: bool
    jsonl_record_encoding: str
    jsonl_record_kinds: Tuple[str, ...]
    jsonl_newline_bytes_per_record: int
    stderr_record_encoding: str
    stderr_length_prefix_bytes: int
    stderr_payload_max_bytes: int
    stderr_records_per_shard: int
    stderr_trailing_bytes_permitted: bool
    seed_capsule_encoding: str
    seed_capsule_final_newline_bytes: int
    payload_ceilings_include_storage_framing: bool
    capacity_receipt_present: bool
    capacity_measured: bool
    minimum_capacity_satisfied: bool
    production_resources_allocated: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP64DurabilityReceiptSchemaV1(_SealedRecord):
    schema_version: str
    receipt_schema: str
    purpose: str
    exact_keys: Tuple[str, ...]
    global_relative_paths: Tuple[str, ...]
    per_shard_relative_paths: Tuple[str, ...]
    global_relative_paths_scope: str
    conditional_relative_paths: Tuple[str, ...]
    conditional_path_rules: Tuple[Tuple[str, str], ...]
    complete_source_receipt_and_partial_terminal_receipt_mutually_exclusive: bool
    relative_path_rule: str
    temporary_suffix: str
    exclusive_create_required: bool
    symlinks_permitted: bool
    hardlinks_permitted: bool
    overwrite_permitted: bool
    append_after_commit_permitted: bool
    same_directory_atomic_rename_required: bool
    file_fsync_before_rename_required: bool
    directory_fsync_after_rename_required: bool
    canonical_jsonl_final_newline_required: bool
    stderr_frame_offsets_lengths_and_sha256_bound_in_shard_index: bool
    raw_retained_separately: bool
    stable_projection_never_replaces_raw: bool
    shard_receipt_committed_last: bool
    terminal_order: Tuple[str, ...]
    launch_authorization_prepared_partial_relative_path: str
    rejected_launch_authorization_candidate_relative_path: str
    preauthorization_outcome_relative_path: str
    preauthorization_outcome_exact_keys: Tuple[str, ...]
    preauthorization_outcome_allowed_arms: Tuple[str, ...]
    preauthorization_outcome_exclusive_create_and_nofollow_required: bool
    preauthorization_outcome_file_and_directory_fsync_required: bool
    authorization_candidate_must_be_o_excl_nofollow_written_and_fsynced_as_partial_before_authorization_arm: bool
    authorization_arm_requires_nonzero_matching_prepared_authorization_sha256: bool
    authorization_arm_recovery_publishes_verified_prepared_bytes_by_rename_no_replace_and_directory_fsync: bool
    preauthorization_terminal_arm_requires_terminal_state_equal_arm: bool
    preauthorization_terminal_arm_never_publishes_final_launch_authorization: bool
    losing_prepared_authorization_candidate_is_retained_under_rejected_non_authorizing_path: bool
    preauthorization_outcome_crash_recovery_completes_winner_without_reselection: bool
    preauthorization_outcome_losers_refuse_without_side_effects: bool
    postauthorization_outcome_relative_path: str
    postauthorization_outcome_exact_keys: Tuple[str, ...]
    postauthorization_outcome_allowed_arms: Tuple[str, ...]
    postauthorization_outcome_requires_durable_final_launch_authorization: bool
    postauthorization_outcome_exclusive_create_and_nofollow_required: bool
    postauthorization_outcome_file_and_directory_fsync_required: bool
    postauthorization_started_and_terminal_arms_mutually_exclusive: bool
    postauthorization_outcome_crash_recovery_completes_winner_without_reselection: bool
    postauthorization_outcome_losers_refuse_without_side_effects: bool
    started_arm_effects_frozen_to_started_transition: bool
    crash_after_started_arm_before_started_receipt_recovers_started_then_incomplete_without_production_rng_or_child: bool
    crash_after_terminal_arm_before_terminal_receipt_completes_same_terminal_without_reselection: bool
    both_outcome_receipts_retained_and_manifest_bound_at_committed: bool
    started_receipt_must_bind_postauthorization_started_outcome: bool
    terminal_state_must_bind_winning_terminal_outcome: bool
    proposed_v15_preauthorization_terminal_states: Tuple[str, ...]
    proposed_v15_preauthorization_crash_cuts: Tuple[str, ...]
    proposed_v15_preauthorization_terminal_order: Tuple[str, ...]
    proposed_v15_preauthorization_forbidden_stages: Tuple[str, ...]
    preauthorization_terminal_retains_all_durable_artifacts: bool
    preauthorization_terminal_state_binds_durable_artifact_inventory: bool
    preauthorization_sha256_manifest_binds_all_durable_prestart_artifacts: bool
    preauthorization_committed_marker_transitively_binds_all_durable_prestart_artifacts: bool
    proposed_v15_postauthorization_prestart_terminal_states: Tuple[str, ...]
    proposed_v15_postauthorization_prestart_crash_cut: str
    proposed_v15_postauthorization_prestart_terminal_order: Tuple[str, ...]
    proposed_v15_postauthorization_prestart_forbidden_stages: Tuple[str, ...]
    postauthorization_prestart_terminal_retains_launch_authorization: bool
    postauthorization_prestart_terminal_state_binds_launch_authorization: bool
    postauthorization_prestart_sha256_manifest_binds_launch_authorization: bool
    postauthorization_prestart_committed_marker_transitively_binds_launch_authorization: bool
    auxiliary_metadata_reservation_relative_path: str
    auxiliary_metadata_reservation_retained_until_committed: bool
    auxiliary_metadata_reservation_manifest_bound_at_committed: bool
    reservation_destination_final_path_templates: Tuple[str, ...]
    reservation_allocation_unit_rule: str
    reservation_partition_formula: str
    reservation_per_shard_total_bytes: int
    reservation_global_total_bytes: int
    reservation_manifest_binds_per_file_reserved_bytes: bool
    reservation_partial_path_formula: str
    reservation_uses_actual_destination_partial_inodes: bool
    reservation_manifest_binds_path_device_inode_extents_logical_and_allocated_bytes: bool
    reservation_files_exclusive_non_sparse_preallocated: bool
    writer_consumes_reserved_partial_inodes_in_place: bool
    reservation_handoff_requires_inode_identity_match: bool
    reservation_qualification_verifies_in_place_overwrite_without_copy_on_write_double_allocation: bool
    reserved_partial_truncation_only_after_complete_write_and_followed_by_file_fsync: bool
    reserved_partial_files_absent_at_committed: bool
    reservation_manifest_retained_and_manifest_bound_at_committed: bool
    reservation_manifest_required: bool
    reserved_destination_commit_order: Tuple[str, ...]
    rename_no_replace_required: bool
    cow_no_double_allocation_qualification_required: bool
    cow_no_double_allocation_qualified: bool
    committed_marker_exact_keys: Tuple[str, ...]
    committed_marker_relative_path: str
    sha256_manifest_excludes_itself_and_committed_marker: bool
    committed_marker_binds_terminal_state_and_sha256_manifest: bool
    committed_marker_exclusive_create_required: bool
    committed_marker_file_fsync_required: bool
    committed_marker_directory_fsync_required: bool
    committed_marker_created_after_terminal_and_manifest: bool
    committed_marker_is_only_publication_boundary: bool
    receipt_present: bool
    writer_implemented: bool
    writer_qualified: bool
    filesystem_observed: bool
    durable_output_written: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP64CandidateShardV1(_SealedRecord):
    schema_version: str
    shard_ordinal: int
    shard_id: str
    relative_directory: str
    seed_ordinal_min: int
    seed_ordinal_max: int
    seed_ordinal_count: int
    logical_request_ordinal_min: int
    logical_request_ordinal_max: int
    logical_request_count: int
    all_sixteen_rows_per_seed_collocated: bool
    logical_requests_strictly_increasing: bool
    rejection_proposal_slot_count: int
    sir_proposal_slot_count: int
    total_proposal_slot_count: int
    sir_resampling_draw_count: int
    maximum_event_occurrence_count: int
    maximum_coordinate_count: int
    raw_ceiling_bytes: int
    stable_ceiling_bytes: int
    request_ceiling_bytes: int
    stderr_ceiling_bytes: int
    payload_ceiling_bytes: int
    candidate_destination_reservation_bytes: int
    definition_only: bool
    selected_for_production: bool
    instantiated: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP64CandidateShardPolicyV1(_SealedRecord):
    schema_version: str
    policy_id: str
    cp63_schedule_contract_record_sha256: str
    cp63_resource_contract_record_sha256: str
    capacity_receipt_schema_record_sha256: str
    durability_receipt_schema_record_sha256: str
    mapping_formula: str
    shard_count: int
    seed_count: int
    row_count: int
    total_request_count: int
    seed_ordinals_per_shard: int
    logical_requests_per_shard: int
    shard_ordinals: Tuple[int, ...]
    shards: Tuple[CP64CandidateShardV1, ...]
    same_seed_rows_collocated: bool
    duplicate_seed_values_distinguished_by_ordinal: bool
    historical_pre_cp61_eight_shard_plan_inherited: bool
    candidate_policy_frozen: bool
    candidate_policy_selected_for_production: bool
    production_shard_map_bound: bool
    production_shard_map_instantiated: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP64ProductionShardMapReceiptSchemaV1(_SealedRecord):
    schema_version: str
    receipt_schema: str
    purpose: str
    exact_keys: Tuple[str, ...]
    shard_record_exact_keys: Tuple[str, ...]
    exactly_32_candidate_shard_records_required: bool
    shard_ordinals_strictly_increasing_unique_1_through_32: bool
    logical_ordinal_ranges_contiguous_nonoverlapping_cover_1_through_32768: bool
    seed_ordinal_ranges_contiguous_nonoverlapping_cover_1_through_2048: bool
    shard_record_candidate_equality_field_pairs: Tuple[Tuple[str, str], ...]
    shard_record_candidate_fields_must_equal_candidate_record: bool
    relative_directory_must_equal_candidate_shard_relative_directory: bool
    per_file_reservation_manifest_entry_sha256_required_for_each_reserved_partial: bool
    shard_record_per_file_reservation_link_order: Tuple[str, ...]
    shard_record_per_file_reservation_links_exactly_four: bool
    shard_record_per_file_reservation_link_digests_exact_nonzero_sha256: bool
    shard_record_per_file_paths_match_candidate_templates: bool
    shard_record_per_file_reserved_bytes_sum_to_candidate_destination_reservation_bytes: bool
    each_shard_capacity_partition_bytes: int
    all_shard_capacity_partition_sum_bytes: int
    all_shard_capacity_partition_sum_equals_global_destination_reservation: bool
    shard_record_digest_formula: str
    candidate_shard_policy_sha256: str
    mapping_formula: str
    shard_count: int
    attempt_binding_required: bool
    reservation_manifest_binding_required: bool
    receipt_present: bool
    candidate_policy_selected_for_production: bool
    production_shard_map_bound: bool
    production_shard_map_instantiated: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP64LaunchAuthorizationReceiptSchemaV1(_SealedRecord):
    schema_version: str
    receipt_schema: str
    purpose: str
    exact_keys: Tuple[str, ...]
    proposed_v15_lifecycle_states: Tuple[str, ...]
    v14_allowed_attempt_states: Tuple[str, ...]
    v14_transition_graph: Tuple[Tuple[str, str], ...]
    proposed_v15_transition_graph: Tuple[Tuple[str, str], ...]
    current_state: str
    v15_protocol_and_manifest_amendment_required: bool
    proposed_v15_protocol_and_manifest_paths_available_to_builder: bool
    proposed_v15_protocol_and_manifest_consumed_by_bundle: bool
    proposed_v15_protocol_relative_path: str
    proposed_v15_machine_manifest_relative_path: str
    proposed_v15_transition_graph_authoritative_for_production: bool
    preflight_and_authorization_are_artifact_stages_not_lifecycle_states: bool
    frozen_prestart_terminal_states: Tuple[str, ...]
    partial_external_seed_acquisition_terminal_state: str
    any_durable_external_seed_value_spends_attempt: bool
    no_redraw_reselection_replacement_after_durable_seed_acquisition: bool
    pre_durable_output_infrastructure_abort_new_attempt_requires_written_independent_adjudication_and_identical_frozen_inputs: bool
    authorization_requires_frozen_attempt_state: bool
    authorization_must_follow_preauthorization_outcome_authorization_arm: bool
    authorization_is_artifact_stage_not_lifecycle_state: bool
    authorization_must_precede_postauthorization_outcome: bool
    authorization_does_not_equal_started: bool
    postauthorization_started_outcome_and_binding_started_receipt_must_be_durable_before_production_runner_rng_or_child: bool
    transition_api_exposed: bool
    receipt_present: bool
    authority_verified: bool
    launch_authorized: bool
    started: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP64NoExecutionGateContractV1(_SealedRecord):
    schema_version: str
    production_gate_ids: Tuple[str, ...]
    production_gate_states: Tuple[str, ...]
    requirement_schemas_frozen: bool
    cp64_scaffolded_receipt_keysets_and_cross_bindings_predeclared: bool
    all_required_production_receipt_keysets_predeclared: bool
    complete_receipt_type_range_size_and_domain_schemas_frozen: bool
    complete_auxiliary_artifact_size_schema_frozen: bool
    bounded_auxiliary_artifact_size_proof_present: bool
    generic_prestart_terminal_record_schema_frozen: bool
    all_required_production_receipt_digest_preimages_frozen: bool
    authorization_signature_preimage_and_verifier_frozen: bool
    production_evidence_required_count: int
    production_evidence_present_count: int
    preauthorization_gate_count: int
    preflight_gate_summary_covered_gate_count: int
    preflight_gate_summary_gate_ids: Tuple[str, ...]
    preflight_gate_summary_evidence_node_ids: Tuple[str, ...]
    preflight_gate_summary_ids_states_evidence_strictly_aligned: bool
    preflight_gate_summary_requires_all_covered_states_pass: bool
    preflight_gate_summary_requires_exact_nonzero_sha256_per_covered_gate: bool
    preflight_gate_summary_exact_keys: Tuple[str, ...]
    preflight_gate_summary_excludes_independent_signoff_and_launch_authorization: bool
    future_digest_node_order: Tuple[str, ...]
    future_digest_edges: Tuple[Tuple[str, str], ...]
    source_receipt_binds_capsule_body: bool
    capacity_receipt_binds_shard_map: bool
    launch_authorization_is_only_final_downstream_aggregator: bool
    digest_dag_acyclic: bool
    external_seed_values_present: bool
    source_authority_verified: bool
    full_runtime_lock_recomputed: bool
    capacity_measured: bool
    durability_verified: bool
    production_shard_map_bound: bool
    production_runner_supervisor_qualified: bool
    preflight_gate_summary_present: bool
    closed_refusal_failure_classifier_qualified: bool
    freeze_receipt_present: bool
    power_thresholds_frozen: bool
    independent_signoffs_present: bool
    launch_authorization_present: bool
    started: bool
    production_request_materialization_exposed: bool
    production_campaign_exposed: bool
    preflight_passed: bool
    readiness_state: str
    execution_authorized: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP64ProductionCustodyPreflightBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    v15_protocol_and_manifest_amendment_required: bool
    proposed_v15_protocol_and_manifest_paths_available_to_builder: bool
    proposed_v15_protocol_and_manifest_consumed_by_bundle: bool
    proposed_v15_protocol_relative_path: str
    proposed_v15_machine_manifest_relative_path: str
    predecessor_custody: CP64PredecessorCustodyV1
    external_seed_source_receipt_schema: CP64ExternalSeedSourceReceiptSchemaV1
    production_runtime_receipt_schema: CP64ProductionRuntimeReceiptSchemaV1
    capacity_receipt_schema: CP64CapacityReceiptSchemaV1
    durability_receipt_schema: CP64DurabilityReceiptSchemaV1
    candidate_shard_policy: CP64CandidateShardPolicyV1
    production_shard_map_receipt_schema: CP64ProductionShardMapReceiptSchemaV1
    launch_authorization_receipt_schema: CP64LaunchAuthorizationReceiptSchemaV1
    no_execution_gate_contract: CP64NoExecutionGateContractV1
    zero_argument_builder: bool
    stdlib_only_import: bool
    project_modules_imported: bool
    host_filesystem_probed: bool
    cp64_scaffolded_receipt_keysets_and_cross_bindings_predeclared: bool
    all_required_production_receipt_keysets_predeclared: bool
    complete_receipt_type_range_size_and_domain_schemas_frozen: bool
    complete_auxiliary_artifact_size_schema_frozen: bool
    bounded_auxiliary_artifact_size_proof_present: bool
    generic_prestart_terminal_record_schema_frozen: bool
    all_required_production_receipt_digest_preimages_frozen: bool
    authorization_signature_preimage_and_verifier_frozen: bool
    candidate_shard_policy_frozen: bool
    candidate_shard_policy_selected_for_production: bool
    external_seed_values_present: bool
    external_seed_source_bound: bool
    external_seed_source_receipt_present: bool
    production_seed_capsule_present: bool
    production_runtime_receipt_present: bool
    capacity_receipt_present: bool
    capacity_reservation_present: bool
    durability_receipt_present: bool
    production_shard_map_receipt_present: bool
    freeze_receipt_present: bool
    power_threshold_receipt_present: bool
    independent_signoffs_present: bool
    launch_authorization_present: bool
    started_receipt_present: bool
    committed_marker_present: bool
    durable_writer_implemented: bool
    production_runner_supervisor_qualified: bool
    closed_refusal_failure_classification_implemented: bool
    preflight_gate_summary_present: bool
    production_runner_bound: bool
    production_schema_frozen: bool
    production_requests_materialized: bool
    production_campaign_exposed: bool
    production_execution_authorized: bool
    production_execution_observed: bool
    estimates_computed: bool
    intervals_computed: bool
    decision_made: bool
    cp64_scaffolded_custody_preflight_inventory_and_policy_scaffold_complete: bool
    runner_and_recomputation_blocker_closed: bool
    unconditional_operational_predictions_blocker_closed: bool
    power_and_thresholds_blocker_closed: bool
    confirmatory_custody_blocker_closed: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


_ALLOW_RECORD_CLASS_DEFINITION = False

_RECORD_DOMAINS = {
    CP64PredecessorCustodyV1: b"cp64-predecessor-custody-v1",
    CP64ExternalSeedSourceReceiptSchemaV1: (
        b"cp64-external-seed-source-receipt-schema-v1"
    ),
    CP64ProductionRuntimeReceiptSchemaV1: (
        b"cp64-production-runtime-receipt-schema-v1"
    ),
    CP64CapacityReceiptSchemaV1: b"cp64-capacity-receipt-schema-v1",
    CP64DurabilityReceiptSchemaV1: b"cp64-durability-receipt-schema-v1",
    CP64CandidateShardV1: b"cp64-candidate-shard-v1",
    CP64CandidateShardPolicyV1: b"cp64-candidate-shard-policy-v1",
    CP64ProductionShardMapReceiptSchemaV1: (
        b"cp64-production-shard-map-receipt-schema-v1"
    ),
    CP64LaunchAuthorizationReceiptSchemaV1: (
        b"cp64-launch-authorization-receipt-schema-v1"
    ),
    CP64NoExecutionGateContractV1: b"cp64-no-execution-gate-contract-v1",
    CP64ProductionCustodyPreflightBundleV1: (
        b"cp64-production-custody-preflight-bundle-v1"
    ),
}

_EXTERNAL_SEED_SOURCE_RECEIPT_KEYS = (
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
_ACQUISITION_START_RECEIPT_KEYS = (
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
_PARTIAL_ACQUISITION_TERMINAL_RECEIPT_KEYS = (
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
_PRODUCTION_RUNTIME_RECEIPT_KEYS = (
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
_CAPACITY_RECEIPT_KEYS = (
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
_DURABILITY_RECEIPT_KEYS = (
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
_GLOBAL_RELATIVE_PATHS = (
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
_PER_SHARD_RELATIVE_PATHS = (
    "shards/{shard_id}/requests.jsonl",
    "shards/{shard_id}/raw_records.jsonl",
    "shards/{shard_id}/stable_traces.jsonl",
    "shards/{shard_id}/stderr_records.bin",
    "shards/{shard_id}/rng_initial_states.json",
    "shards/{shard_id}/rng_final_states.json",
    "shards/{shard_id}/shard_index.json",
    "shards/{shard_id}/shard_receipt.json",
)
_RESERVATION_DESTINATION_FINAL_PATH_TEMPLATES = (
    "shards/{shard_id}/requests.jsonl",
    "shards/{shard_id}/raw_records.jsonl",
    "shards/{shard_id}/stable_traces.jsonl",
    "shards/{shard_id}/stderr_records.bin",
)
_RESERVED_DESTINATION_COMMIT_ORDER = (
    "open-partial-o_excl-o_nofollow",
    "non-sparse-preallocate-and-verify-extents",
    "write-canonical-bytes-in-place",
    "ftruncate-to-actual-length",
    "file-fsync-after-truncate",
    "hash-and-verify-final-bytes",
    "rename-no-replace-same-directory",
    "directory-fsync",
)
_TERMINAL_ORDER = (
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
_COMMITTED_MARKER_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "terminal_state_sha256",
    "sha256_manifest_sha256",
    "committed_at_utc",
    "body_sha256",
)
_PRODUCTION_SHARD_MAP_RECEIPT_KEYS = (
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
_SHARD_RECORD_KEYS = (
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
_LAUNCH_AUTHORIZATION_RECEIPT_KEYS = (
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
_PROPOSED_V15_LIFECYCLE_STATES = (
    "DRAFT_PRE_FREEZE",
    "FROZEN",
    "STARTED",
    "PASS",
    "FAIL",
    "INVALID_PROTOCOL",
    "ABORTED_INFRA",
    "INCOMPLETE",
)
_V14_ALLOWED_ATTEMPT_STATES = (
    "FROZEN",
    "STARTED",
    "PASS",
    "FAIL",
    "INVALID_PROTOCOL",
    "ABORTED_INFRA",
    "INCOMPLETE",
)
_V14_TRANSITION_GRAPH = (
    ("FROZEN", "STARTED"),
    ("STARTED", "PASS"),
    ("STARTED", "FAIL"),
    ("STARTED", "INVALID_PROTOCOL"),
    ("STARTED", "ABORTED_INFRA"),
    ("STARTED", "INCOMPLETE"),
)
_PROPOSED_V15_TRANSITION_GRAPH = (
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
_PRODUCTION_GATE_IDS = (
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
_PREFLIGHT_GATE_SUMMARY_KEYS = (
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
_FUTURE_DIGEST_NODE_ORDER = (
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
_FUTURE_DIGEST_EDGES = (
    ("source-manifest", "freeze-receipt"),
    ("source-manifest", "production-runtime-receipt"),
    ("source-manifest", "launch-authorization"),
    ("power-threshold-receipt", "freeze-receipt"),
    ("power-threshold-receipt", "launch-authorization"),
    ("freeze-receipt", "external-seed-acquisition-start-receipt"),
    ("freeze-receipt", "external-seed-source-receipt"),
    ("freeze-receipt", "production-runtime-receipt"),
    ("freeze-receipt", "launch-authorization"),
    (
        "external-seed-acquisition-start-receipt",
        "external-seed-source-receipt",
    ),
    ("external-seed-source-receipt", "seed-capsule-body"),
    (
        "external-seed-source-receipt",
        "seed-capsule-sequence-crosscheck-receipt",
    ),
    ("external-seed-source-receipt", "launch-authorization"),
    ("seed-capsule-body", "production-schedule"),
    (
        "seed-capsule-body",
        "seed-capsule-sequence-crosscheck-receipt",
    ),
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
    (
        "seed-capsule-sequence-crosscheck-receipt",
        "preflight-gate-summary",
    ),
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
    (
        "independent-full-32768-recomputation-receipt",
        "preflight-gate-summary",
    ),
    (
        "independent-554-estimate-interval-decision-path-receipt",
        "preflight-gate-summary",
    ),
    ("power-threshold-receipt", "preflight-gate-summary"),
)

_PREFLIGHT_GATE_SUMMARY_EVIDENCE_NODE_IDS = (
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


def _validate_relative_path_declaration(path: str) -> None:
    if (
        type(path) is not str
        or not path
        or path.startswith("/")
        or "\\" in path
        or any(part in ("", ".", "..") for part in path.split("/"))
    ):
        raise RuntimeError("invalid CP64 relative path declaration")


def _validate_declared_path_closure() -> None:
    conditional_paths = (
        "seed_partial_acquisition_terminal_receipt.json",
        "rejected_launch_authorization_candidate.json",
    )
    inventories = (
        _GLOBAL_RELATIVE_PATHS,
        conditional_paths,
        _PER_SHARD_RELATIVE_PATHS,
        _RESERVATION_DESTINATION_FINAL_PATH_TEMPLATES,
    )
    for inventory in inventories:
        if len(inventory) != len(set(inventory)):
            raise RuntimeError("duplicate CP64 path declaration")
        for path in inventory:
            _validate_relative_path_declaration(path)

    retained_global = set(_GLOBAL_RELATIVE_PATHS)
    retained_conditional = set(conditional_paths)
    if retained_global & retained_conditional:
        raise RuntimeError("CP64 global and conditional paths overlap")
    if _RESERVATION_DESTINATION_FINAL_PATH_TEMPLATES != (_PER_SHARD_RELATIVE_PATHS[:4]):
        raise RuntimeError("CP64 reservation-manifest path coverage differs")

    expanded_per_shard = set()
    expanded_reserved_partials = set()
    for shard_ordinal in range(1, 33):
        shard_id = f"shard-{shard_ordinal:04d}"
        shard_paths = tuple(
            template.format(shard_id=shard_id) for template in _PER_SHARD_RELATIVE_PATHS
        )
        reserved_partials = tuple(
            template.format(shard_id=shard_id) + ".partial"
            for template in _RESERVATION_DESTINATION_FINAL_PATH_TEMPLATES
        )
        for path in shard_paths + reserved_partials:
            _validate_relative_path_declaration(path)
        if len(shard_paths) != len(set(shard_paths)) or len(reserved_partials) != len(
            set(reserved_partials)
        ):
            raise RuntimeError("duplicate CP64 expanded shard path")
        if set(shard_paths) & set(reserved_partials):
            raise RuntimeError("CP64 final and reserved-partial paths overlap")
        expanded_per_shard.update(shard_paths)
        expanded_reserved_partials.update(reserved_partials)

    if len(expanded_per_shard) != 32 * len(_PER_SHARD_RELATIVE_PATHS):
        raise RuntimeError("CP64 expanded per-shard paths collide")
    if len(expanded_reserved_partials) != 32 * len(
        _RESERVATION_DESTINATION_FINAL_PATH_TEMPLATES
    ):
        raise RuntimeError("CP64 reservation-manifest entries collide")
    all_retained = retained_global | retained_conditional
    if all_retained & (expanded_per_shard | expanded_reserved_partials):
        raise RuntimeError("CP64 global and shard path scopes collide")


def _validate_future_digest_dag() -> None:
    nodes = _FUTURE_DIGEST_NODE_ORDER
    edges = _FUTURE_DIGEST_EDGES
    if len(nodes) != 20 or len(nodes) != len(set(nodes)):
        raise RuntimeError("CP64 future digest nodes differ")
    if len(edges) != 44 or len(edges) != len(set(edges)):
        raise RuntimeError("CP64 future digest edges differ")
    node_set = set(nodes)
    if any(
        source not in node_set or target not in node_set for source, target in edges
    ):
        raise RuntimeError("CP64 future digest edge has an unknown endpoint")

    indegree = {node: 0 for node in nodes}
    outgoing = {node: [] for node in nodes}
    for source, target in edges:
        outgoing[source].append(target)
        indegree[target] += 1
    frontier = [node for node in nodes if indegree[node] == 0]
    visited = 0
    while frontier:
        source = frontier.pop()
        visited += 1
        for target in outgoing[source]:
            indegree[target] -= 1
            if indegree[target] == 0:
                frontier.append(target)
    if visited != len(nodes):
        raise RuntimeError("CP64 future digest graph is cyclic")
    if sum(target == "preflight-gate-summary" for _, target in edges) != 15:
        raise RuntimeError("CP64 preflight summary evidence indegree differs")
    if sum(target == "independent-signoff-set" for _, target in edges) != 1:
        raise RuntimeError("CP64 independent signoff indegree differs")
    if outgoing["launch-authorization"]:
        raise RuntimeError("CP64 launch authorization is not the sole sink")
    if any(not outgoing[node] for node in nodes if node != "launch-authorization"):
        raise RuntimeError("CP64 future digest graph has another sink")

    if len(_PRODUCTION_GATE_IDS) != 17:
        raise RuntimeError("CP64 production gate inventory differs")
    if len(_PREFLIGHT_GATE_SUMMARY_EVIDENCE_NODE_IDS) != 15:
        raise RuntimeError("CP64 preflight evidence inventory differs")


_ISSUED_RECORD_LOCK = threading.RLock()
_ISSUED_RECORD_SNAPSHOTS: weakref.WeakKeyDictionary[
    _SealedRecord, bytes
] = weakref.WeakKeyDictionary()


def _canonical_value(value: object, *, require_issued: bool) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is tuple:
        return tuple(
            _canonical_value(item, require_issued=require_issued) for item in value
        )
    if isinstance(value, _SealedRecord):
        if type(value) not in _RECORD_DOMAINS:
            raise TypeError("unsupported CP64 sealed record type")
        if require_issued:
            with _ISSUED_RECORD_LOCK:
                snapshot = _ISSUED_RECORD_SNAPSHOTS.get(value)
            if snapshot is None:
                raise TypeError("CP64 record was not module-created")
        return {
            item.name: _canonical_value(
                getattr(value, item.name), require_issued=require_issued
            )
            for item in fields(type(value))
        }
    raise TypeError("value has no CP64 canonical representation")


def _canonical_bytes(value: object, *, require_issued: bool) -> bytes:
    return json.dumps(
        _canonical_value(value, require_issued=require_issued),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _record(cls: type, values: Mapping[str, object]) -> object:
    names = tuple(item.name for item in fields(cls))
    if set(values) != set(names) - {"record_sha256"}:
        raise TypeError("CP64 sealed record field set differs")
    complete = dict(values)
    complete["record_sha256"] = _ZERO_SHA256
    provisional = object.__new__(cls)
    for name in names:
        object.__setattr__(provisional, name, complete[name])
    complete["record_sha256"] = hashlib.sha256(
        _RECORD_DOMAINS[cls]
        + b"\0"
        + _canonical_bytes(provisional, require_issued=False)
    ).hexdigest()
    result = object.__new__(cls)
    for name in names:
        object.__setattr__(result, name, complete[name])
    snapshot = _canonical_bytes(result, require_issued=False)
    with _ISSUED_RECORD_LOCK:
        _ISSUED_RECORD_SNAPSHOTS[cast(_SealedRecord, result)] = snapshot
    return result


def _predecessor_custody() -> CP64PredecessorCustodyV1:
    return cast(
        CP64PredecessorCustodyV1,
        _record(
            CP64PredecessorCustodyV1,
            {
                "schema_version": CP64_TEST28_SCHEMA_VERSION,
                "cp63_protocol_relative_path": (
                    "research/preregistrations/" "cp50_test28_mixed_initializer_v1.md"
                ),
                "cp63_protocol_sha256": (
                    "39c9c7fe061d1a36d21c999eadb308cd26cb982871cbbbd1c3d6a3a35d3842e9"
                ),
                "cp63_protocol_bytes": 105_542,
                "cp63_protocol_lines": 1_950,
                "cp63_machine_manifest_relative_path": (
                    "research/fixtures/cp50_test28_mixed_initializer_v1.json"
                ),
                "cp63_machine_manifest_sha256": (
                    "d0fc1f2845f4ed1316bcbb20f9f876ee3cd99a156af525eecc089194af3a26fe"
                ),
                "cp63_machine_manifest_bytes": 1_898_933,
                "cp63_machine_manifest_lines": 36_239,
                "cp63_protocol_id": "cp50-test28-mixed-initializer-v1",
                "cp63_protocol_state": "DRAFT",
                "cp63_manifest_schema_version": (
                    "cp50-test28-mixed-initializer-machine-manifest-v14"
                ),
                "cp63_bound_artifact_count": 38,
                "cp63_development_verification_record_count": 35,
                "cp63_ledger_total_count": 18,
                "cp63_ledger_satisfied_count": 14,
                "cp63_ledger_missing_count": 4,
                "cp63_aggregate_test_count": 1_066,
                "cp63_lifecycle_current_state": "DRAFT_PRE_FREEZE",
                "cp63_v14_allowed_attempt_states": _V14_ALLOWED_ATTEMPT_STATES,
                "cp63_v14_transition_graph": _V14_TRANSITION_GRAPH,
                "cp63_freeze_state": "ABSENT_DRAFT",
                "cp63_confirmatory_execution_authorized": False,
                "cp63_formal_test_28_status": "OPEN",
                "cp63_formal_test_28_closed": False,
                "cp61_stable_design_sha256": _CP61_STABLE_DESIGN_SHA256,
                "cp62_source_sha256": _CP62_SOURCE_SHA256,
                "cp62_bundle_sha256": _CP62_BUNDLE_SHA256,
                "cp62_runtime_lock_record_sha256": (_CP62_RUNTIME_LOCK_RECORD_SHA256),
                "cp62_supervisor_contract_record_sha256": (
                    _CP62_SUPERVISOR_CONTRACT_RECORD_SHA256
                ),
                "cp62_projection_contract_record_sha256": (
                    _CP62_PROJECTION_CONTRACT_RECORD_SHA256
                ),
                "cp63_runner_source_sha256": _CP63_RUNNER_SOURCE_SHA256,
                "cp63_runner_bundle_record_sha256": (_CP63_RUNNER_BUNDLE_RECORD_SHA256),
                "cp63_schedule_contract_record_sha256": (
                    _CP63_SCHEDULE_CONTRACT_RECORD_SHA256
                ),
                "cp63_seed_capsule_contract_record_sha256": (
                    _CP63_SEED_CAPSULE_CONTRACT_RECORD_SHA256
                ),
                "cp63_lifecycle_contract_record_sha256": (
                    _CP63_LIFECYCLE_CONTRACT_RECORD_SHA256
                ),
                "cp63_raw_record_schema_record_sha256": (
                    _CP63_RAW_RECORD_SCHEMA_RECORD_SHA256
                ),
                "cp63_resource_contract_record_sha256": (
                    _CP63_RESOURCE_CONTRACT_RECORD_SHA256
                ),
                "cp63_independent_source_sha256": _CP63_INDEPENDENT_SOURCE_SHA256,
                "cp63_independent_bundle_record_sha256": (
                    _CP63_INDEPENDENT_BUNDLE_RECORD_SHA256
                ),
                "cp63_independent_bundle_public_sha256": (
                    _CP63_INDEPENDENT_BUNDLE_PUBLIC_SHA256
                ),
                "cp63_acceptance_receipt_sha256": _CP63_ACCEPTANCE_RECEIPT_SHA256,
                "cp63_semantic_pin_receipt_sha256": (_CP63_SEMANTIC_PIN_RECEIPT_SHA256),
                "dependency_lock_path": _DEPENDENCY_LOCK_PATH,
                "dependency_lock_sha256": _DEPENDENCY_LOCK_SHA256,
                "cp64_source_hash_in_record": False,
                "cp64_source_hash_external_binding_required": True,
                "predecessor_custody_only": True,
                "complete_production_source_manifest_present": False,
                "production_runtime_match_verified": False,
            },
        ),
    )


def _external_seed_source_receipt_schema() -> CP64ExternalSeedSourceReceiptSchemaV1:
    return cast(
        CP64ExternalSeedSourceReceiptSchemaV1,
        _record(
            CP64ExternalSeedSourceReceiptSchemaV1,
            {
                "schema_version": CP64_TEST28_SCHEMA_VERSION,
                "receipt_schema": "cp64-test28-external-seed-source-receipt-v1",
                "purpose": "future-production-source-custody-only",
                "exact_keys": _EXTERNAL_SEED_SOURCE_RECEIPT_KEYS,
                "acquisition_start_receipt_exact_keys": (
                    _ACQUISITION_START_RECEIPT_KEYS
                ),
                "partial_acquisition_terminal_receipt_exact_keys": (
                    _PARTIAL_ACQUISITION_TERMINAL_RECEIPT_KEYS
                ),
                "acquisition_start_receipt_relative_path": (
                    "seed_acquisition_start_receipt.json"
                ),
                "partial_acquisition_terminal_receipt_relative_path": (
                    "seed_partial_acquisition_terminal_receipt.json"
                ),
                "acquisition_journal_relative_path": ("seed_acquisition_journal.bin"),
                "acquisition_journal_encoding": (
                    "2048-max-fixed-80-byte-chained-binary-entries"
                ),
                "acquisition_journal_entry_bytes": 80,
                "acquisition_journal_max_entries": 2_048,
                "acquisition_journal_max_bytes": 163_840,
                "acquisition_journal_initial_head_formula": (
                    "SHA256(cp64-external-seed-acquisition-journal-head-v1\\0+"
                    "acquisition-start-receipt-sha256)"
                ),
                "acquisition_journal_entry_digest_formula": (
                    "SHA256(cp64-external-seed-acquisition-journal-entry-v1\\0+"
                    "start-receipt-sha256+ordinal-uint64-be+value-uint64-be+"
                    "previous-entry-sha256)"
                ),
                "acquisition_journal_entry_field_order": (
                    "ordinal-uint64-be",
                    "value-uint64-be",
                    "previous-entry-sha256",
                    "entry-sha256",
                ),
                "acquisition_journal_entry_ordinals_strictly_increasing_from_one": True,
                "acquisition_journal_exclusive_create_required": True,
                "acquisition_journal_nofollow_required": True,
                "acquisition_journal_non_sparse_physical_allocation_required": True,
                "acquisition_journal_file_fsync_before_acquisition_start_receipt_required": True,
                "acquisition_journal_directory_fsync_before_acquisition_start_receipt_required": True,
                "acquisition_journal_path_inode_recheck_before_acquisition_start_receipt_required": True,
                "acquisition_journal_path_inode_recheck_before_each_entry_append_required": True,
                "acquisition_journal_preallocated_before_source_contact": True,
                "acquisition_journal_entry_fsync_before_next_source_draw": True,
                "acquisition_journal_every_entry_including_final_entry_fsync_required": True,
                "acquisition_journal_final_fsync_before_completed_source_receipt_required": True,
                "acquisition_journal_no_resume_after_crash": True,
                "acquisition_journal_recovery_terminal_state": "INCOMPLETE",
                "acquisition_journal_topup_redraw_reselection_permitted": False,
                "acquisition_journal_recovery_accepts_only_longest_valid_fsynced_prefix": True,
                "acquisition_journal_torn_or_invalid_suffix_is_not_value_evidence": True,
                "attempt_binding_required": True,
                "freeze_receipt_binding_required": True,
                "seed_count": 2_048,
                "seed_encoding": "uint64-16-lowercase-hex-big-endian",
                "sequence_commitment_formula": (
                    "SHA256(cp64-test28-ordered-seed-sequence-v1\\0+canonical("
                    "seed_count,seed_encoding,ordered_seed_values))"
                ),
                "receipt_digest_formula": (
                    "SHA256(cp64-test28-external-seed-source-receipt-v1\\0+"
                    "canonical(receipt-with-zero-body-sha256))"
                ),
                "capsule_body_digest_bound_by_source_receipt": False,
                "source_receipt_digest_referenced_by_capsule": True,
                "capsule_sequence_commitment_crosscheck_required": True,
                "completed_source_receipt_binds_acquisition_journal_sha_head_and_count": True,
                "completed_journal_entry_count_must_equal_seed_count": True,
                "completed_journal_head_must_equal_entry_digest_at_seed_count": True,
                "completed_journal_ordinal_value_sequence_commitment_must_equal_source_receipt_ordered_seed_values_commitment": True,
                "capsule_ordered_seed_values_commitment_must_equal_completed_journal_sequence_commitment": True,
                "canonical_syntax_can_prove_iid": False,
                "digest_can_authenticate_source": False,
                "acquisition_start_receipt_required": True,
                "acquisition_start_receipt_exclusive_create_required": True,
                "acquisition_start_receipt_file_fsync_required": True,
                "acquisition_start_receipt_directory_fsync_required": True,
                "acquisition_start_must_be_durably_committed_before_source_contact": True,
                "acquisition_session_sha256_is_start_receipt_sha256": True,
                "committed_acquisition_start_receipt_spends_attempt": True,
                "any_durable_external_seed_value_spends_attempt": True,
                "source_return_without_journal_fsync_spends_attempt": True,
                "source_return_without_journal_fsync_terminal_state": "INCOMPLETE",
                "source_return_without_journal_fsync_value_is_claimed_retained": False,
                "source_return_without_journal_fsync_resume_topup_redraw_permitted": False,
                "durably_journaled_partial_acquisition_values_must_be_retained": True,
                "partial_acquisition_terminal_receipt_required": True,
                "partial_acquisition_terminal_state": "INCOMPLETE",
                "partial_acquisition_topup_redraw_reselection_permitted": False,
                "receipt_values_present": False,
                "source_authority_verified": False,
            },
        ),
    )


def _production_runtime_receipt_schema() -> CP64ProductionRuntimeReceiptSchemaV1:
    return cast(
        CP64ProductionRuntimeReceiptSchemaV1,
        _record(
            CP64ProductionRuntimeReceiptSchemaV1,
            {
                "schema_version": CP64_TEST28_SCHEMA_VERSION,
                "receipt_schema": "cp64-test28-production-runtime-receipt-v1",
                "purpose": "future-production-runtime-source-abi-custody",
                "exact_keys": _PRODUCTION_RUNTIME_RECEIPT_KEYS,
                "cp62_candidate_runtime_lock_sha256": (
                    _CP62_RUNTIME_LOCK_RECORD_SHA256
                ),
                "dependency_lock_sha256": _DEPENDENCY_LOCK_SHA256,
                "complete_source_manifest_required": True,
                "cp64_source_external_binding_required": True,
                "preimport_environment_required": True,
                "loaded_local_source_closure_required": True,
                "compiled_abi_map_required": True,
                "receipt_attempt_binding_required": True,
                "receipt_freeze_binding_required": True,
                "observation_must_postdate_freeze": True,
                "receipt_present": False,
                "full_runtime_lock_recomputed": False,
                "production_runtime_match_verified": False,
            },
        ),
    )


def _capacity_receipt_schema() -> CP64CapacityReceiptSchemaV1:
    return cast(
        CP64CapacityReceiptSchemaV1,
        _record(
            CP64CapacityReceiptSchemaV1,
            {
                "schema_version": CP64_TEST28_SCHEMA_VERSION,
                "receipt_schema": "cp64-test28-capacity-receipt-v1",
                "purpose": "future-production-capacity-preflight-only",
                "exact_keys": _CAPACITY_RECEIPT_KEYS,
                "cp63_resource_contract_record_sha256": (
                    _CP63_RESOURCE_CONTRACT_RECORD_SHA256
                ),
                "global_payload_ceiling_bytes": 861_141_434_368,
                "global_destination_reservation_bytes": 1_099_511_627_776,
                "global_auxiliary_metadata_conservative_policy_reservation_bytes": 34_359_738_368,
                "global_combined_available_and_quota_required_before_reservation_bytes": 1_133_871_366_144,
                "global_available_and_quota_required_after_destination_before_auxiliary_reservation_bytes": 34_359_738_368,
                "auxiliary_metadata_reservation_is_conservative_policy_floor": True,
                "complete_auxiliary_artifact_size_schema_frozen": False,
                "bounded_auxiliary_artifact_size_proof_required_before_capacity_pass": True,
                "bounded_auxiliary_artifact_size_proof_present": False,
                "auxiliary_metadata_must_fit_exclusive_auxiliary_reservation": True,
                "acquisition_journal_maximum_bytes": 163_840,
                "acquisition_journal_counted_within_auxiliary_metadata_reserve": True,
                "per_shard_payload_ceiling_bytes": 26_910_665_728,
                "per_shard_destination_reservation_bytes": 34_359_738_368,
                "candidate_shard_count": 32,
                "minimum_available_inodes": 4_096,
                "combined_available_and_quota_before_reservation_each_must_meet_floor": True,
                "before_reservation_available_and_quota_each_meet_combined_floor_required": True,
                "after_destination_before_auxiliary_available_and_quota_each_meet_auxiliary_floor_required": True,
                "destination_and_auxiliary_reservations_both_exclusive_required": True,
                "destination_and_auxiliary_reservations_no_double_count_required": True,
                "auxiliary_metadata_reservation_method_rule": (
                    "o-excl-nonsparse-preallocated-auxiliary-destination-inodes-"
                    "consumed-in-place-and-exclusive-enforced-quota-both-"
                    "required"
                ),
                "auxiliary_metadata_physical_and_quota_reservations_both_required": True,
                "quota_only_auxiliary_reservation_sufficient": False,
                "auxiliary_metadata_reservation_artifact_relative_path": (
                    "auxiliary_metadata_reservation.json"
                ),
                "auxiliary_metadata_reservation_same_storage_root_required": True,
                "auxiliary_metadata_reservation_retained_until_committed": True,
                "auxiliary_metadata_reservation_consumed_in_place_and_enforced_quota_required": True,
                "post_destination_free_space_or_quota_snapshot_alone_sufficient": False,
                "same_filesystem_required": True,
                "measurement_must_postdate_freeze": True,
                "measurement_must_predate_authorization": True,
                "reservation_receipt_required": True,
                "non_sparse_reservation_required": True,
                "reservation_same_filesystem_required": True,
                "destination_effective_reservation_formula": (
                    "min(physically_allocated_reservation_bytes,"
                    "usable_reserved_bytes_after_allocation)"
                ),
                "auxiliary_effective_reservation_formula": (
                    "min(physically_allocated_auxiliary_metadata_bytes,"
                    "auxiliary_metadata_reserved_quota_bytes)-if-exclusive-"
                    "durable-same-storage-root-and-no-double-count-else-0"
                ),
                "combined_effective_reservation_formula": (
                    "destination-effective-reservation-bytes+auxiliary-"
                    "effective-reservation-bytes-with-disjoint-custody"
                ),
                "capacity_pass_predicate": (
                    "destination_effective_reservation_bytes>=1099511627776&&"
                    "auxiliary_effective_reservation_bytes>=34359738368&&"
                    "combined_effective_reservation_bytes>=1133871366144&&"
                    "available_inodes_after_reservation>=4096&&"
                    "bounded_auxiliary_artifact_size_proof_present&&"
                    "all_required_reservation_and_filesystem_verifications_true"
                ),
                "snapshot_only_sufficient": False,
                "jsonl_record_encoding": ("ascii-canonical-json-one-record-per-line"),
                "jsonl_record_kinds": ("request", "raw", "stable"),
                "jsonl_newline_bytes_per_record": 1,
                "stderr_record_encoding": (
                    "uint64-big-endian-length-prefixed-raw-bytes"
                ),
                "stderr_length_prefix_bytes": 8,
                "stderr_payload_max_bytes": 1_048_576,
                "stderr_records_per_shard": 1_024,
                "stderr_trailing_bytes_permitted": False,
                "seed_capsule_encoding": "exact-cp63-canonical-json-bytes",
                "seed_capsule_final_newline_bytes": 0,
                "payload_ceilings_include_storage_framing": True,
                "capacity_receipt_present": False,
                "capacity_measured": False,
                "minimum_capacity_satisfied": False,
                "production_resources_allocated": False,
            },
        ),
    )


def _durability_receipt_schema() -> CP64DurabilityReceiptSchemaV1:
    _validate_declared_path_closure()
    return cast(
        CP64DurabilityReceiptSchemaV1,
        _record(
            CP64DurabilityReceiptSchemaV1,
            {
                "schema_version": CP64_TEST28_SCHEMA_VERSION,
                "receipt_schema": "cp64-test28-durability-receipt-v1",
                "purpose": "future-production-durable-writer-qualification-only",
                "exact_keys": _DURABILITY_RECEIPT_KEYS,
                "global_relative_paths": _GLOBAL_RELATIVE_PATHS,
                "per_shard_relative_paths": _PER_SHARD_RELATIVE_PATHS,
                "global_relative_paths_scope": (
                    "cp64-scaffolded-complete-acquisition-path-inventory-not-"
                    "full-production-roster"
                ),
                "conditional_relative_paths": (
                    "seed_partial_acquisition_terminal_receipt.json",
                    "rejected_launch_authorization_candidate.json",
                ),
                "conditional_path_rules": (
                    (
                        "seed_partial_acquisition_terminal_receipt.json",
                        "required-iff-acquisition-start-committed-and-complete-"
                        "source-receipt-absent",
                    ),
                    (
                        "rejected_launch_authorization_candidate.json",
                        "required-iff-preauthorization-terminal-arm-wins-after-a-"
                        "durable-prepared-authorization-candidate-exists",
                    ),
                ),
                "complete_source_receipt_and_partial_terminal_receipt_mutually_exclusive": True,
                "relative_path_rule": (
                    "posix-relative-no-empty-dot-dotdot-leading-slash-or-backslash"
                ),
                "temporary_suffix": ".partial",
                "exclusive_create_required": True,
                "symlinks_permitted": False,
                "hardlinks_permitted": False,
                "overwrite_permitted": False,
                "append_after_commit_permitted": False,
                "same_directory_atomic_rename_required": True,
                "file_fsync_before_rename_required": True,
                "directory_fsync_after_rename_required": True,
                "canonical_jsonl_final_newline_required": True,
                "stderr_frame_offsets_lengths_and_sha256_bound_in_shard_index": True,
                "raw_retained_separately": True,
                "stable_projection_never_replaces_raw": True,
                "shard_receipt_committed_last": True,
                "terminal_order": _TERMINAL_ORDER,
                "launch_authorization_prepared_partial_relative_path": (
                    "launch_authorization.json.partial"
                ),
                "rejected_launch_authorization_candidate_relative_path": (
                    "rejected_launch_authorization_candidate.json"
                ),
                "preauthorization_outcome_relative_path": (
                    "preauthorization_outcome.json"
                ),
                "preauthorization_outcome_exact_keys": (
                    "schema",
                    "purpose",
                    "attempt_id",
                    "freeze_receipt_sha256",
                    "outcome_arm",
                    "prepared_launch_authorization_sha256",
                    "terminal_state",
                    "selected_at_utc",
                    "body_sha256",
                ),
                "preauthorization_outcome_allowed_arms": (
                    "AUTHORIZATION",
                    "INVALID_PROTOCOL",
                    "ABORTED_INFRA",
                    "INCOMPLETE",
                ),
                "preauthorization_outcome_exclusive_create_and_nofollow_required": True,
                "preauthorization_outcome_file_and_directory_fsync_required": True,
                "authorization_candidate_must_be_o_excl_nofollow_written_and_fsynced_as_partial_before_authorization_arm": True,
                "authorization_arm_requires_nonzero_matching_prepared_authorization_sha256": True,
                "authorization_arm_recovery_publishes_verified_prepared_bytes_by_rename_no_replace_and_directory_fsync": True,
                "preauthorization_terminal_arm_requires_terminal_state_equal_arm": True,
                "preauthorization_terminal_arm_never_publishes_final_launch_authorization": True,
                "losing_prepared_authorization_candidate_is_retained_under_rejected_non_authorizing_path": True,
                "preauthorization_outcome_crash_recovery_completes_winner_without_reselection": True,
                "preauthorization_outcome_losers_refuse_without_side_effects": True,
                "postauthorization_outcome_relative_path": (
                    "postauthorization_outcome.json"
                ),
                "postauthorization_outcome_exact_keys": (
                    "schema",
                    "purpose",
                    "attempt_id",
                    "freeze_receipt_sha256",
                    "launch_authorization_sha256",
                    "outcome_arm",
                    "terminal_state",
                    "selected_at_utc",
                    "body_sha256",
                ),
                "postauthorization_outcome_allowed_arms": (
                    "STARTED",
                    "INVALID_PROTOCOL",
                    "ABORTED_INFRA",
                    "INCOMPLETE",
                ),
                "postauthorization_outcome_requires_durable_final_launch_authorization": True,
                "postauthorization_outcome_exclusive_create_and_nofollow_required": True,
                "postauthorization_outcome_file_and_directory_fsync_required": True,
                "postauthorization_started_and_terminal_arms_mutually_exclusive": True,
                "postauthorization_outcome_crash_recovery_completes_winner_without_reselection": True,
                "postauthorization_outcome_losers_refuse_without_side_effects": True,
                "started_arm_effects_frozen_to_started_transition": True,
                "crash_after_started_arm_before_started_receipt_recovers_started_then_incomplete_without_production_rng_or_child": True,
                "crash_after_terminal_arm_before_terminal_receipt_completes_same_terminal_without_reselection": True,
                "both_outcome_receipts_retained_and_manifest_bound_at_committed": True,
                "started_receipt_must_bind_postauthorization_started_outcome": True,
                "terminal_state_must_bind_winning_terminal_outcome": True,
                "proposed_v15_preauthorization_terminal_states": (
                    "INVALID_PROTOCOL",
                    "ABORTED_INFRA",
                    "INCOMPLETE",
                ),
                "proposed_v15_preauthorization_crash_cuts": (
                    "zero-source-values-after-start",
                    "partial-source-values",
                    "complete-seed-capsule-before-authorization",
                    "later-preauthorization",
                ),
                "proposed_v15_preauthorization_terminal_order": (
                    "frozen-inputs",
                    "freeze-receipt",
                    "all-durable-prestart-artifacts",
                    "applicable-acquisition-terminal-receipt",
                    "preauthorization-outcome-terminal-arm",
                    "applicable-rejected-authorization-candidate",
                    "terminal-state",
                    "sha256-manifest",
                    "COMMITTED",
                ),
                "proposed_v15_preauthorization_forbidden_stages": (
                    "launch-authorization",
                    "postauthorization-outcome",
                    "STARTED",
                    "shard-data",
                    "shard-receipts",
                    "independent-recomputation",
                    "metrics",
                    "decisions",
                ),
                "preauthorization_terminal_retains_all_durable_artifacts": True,
                "preauthorization_terminal_state_binds_durable_artifact_inventory": True,
                "preauthorization_sha256_manifest_binds_all_durable_prestart_artifacts": True,
                "preauthorization_committed_marker_transitively_binds_all_durable_prestart_artifacts": True,
                "proposed_v15_postauthorization_prestart_terminal_states": (
                    "INVALID_PROTOCOL",
                    "ABORTED_INFRA",
                    "INCOMPLETE",
                ),
                "proposed_v15_postauthorization_prestart_crash_cut": (
                    "launch-authorization-durable-before-STARTED"
                ),
                "proposed_v15_postauthorization_prestart_terminal_order": (
                    "frozen-inputs",
                    "freeze-receipt",
                    "all-durable-prestart-artifacts",
                    "preauthorization-outcome-authorization-arm",
                    "launch-authorization",
                    "postauthorization-outcome-terminal-arm",
                    "terminal-state",
                    "sha256-manifest",
                    "COMMITTED",
                ),
                "proposed_v15_postauthorization_prestart_forbidden_stages": (
                    "STARTED",
                    "shard-data",
                    "shard-receipts",
                    "independent-recomputation",
                    "metrics",
                    "decisions",
                ),
                "postauthorization_prestart_terminal_retains_launch_authorization": True,
                "postauthorization_prestart_terminal_state_binds_launch_authorization": True,
                "postauthorization_prestart_sha256_manifest_binds_launch_authorization": True,
                "postauthorization_prestart_committed_marker_transitively_binds_launch_authorization": True,
                "auxiliary_metadata_reservation_relative_path": (
                    "auxiliary_metadata_reservation.json"
                ),
                "auxiliary_metadata_reservation_retained_until_committed": True,
                "auxiliary_metadata_reservation_manifest_bound_at_committed": True,
                "reservation_destination_final_path_templates": (
                    _RESERVATION_DESTINATION_FINAL_PATH_TEMPLATES
                ),
                "reservation_allocation_unit_rule": (
                    "exact-positive-power-of-two-at-most-1073741824-and-"
                    "divides-34359738368"
                ),
                "reservation_partition_formula": (
                    "non-raw=ceil(payload-ceiling/allocation-unit)*allocation-"
                    "unit;raw=34359738368-sum(non-raw);raw>=ceil(raw-ceiling/"
                    "allocation-unit)*allocation-unit"
                ),
                "reservation_per_shard_total_bytes": 34_359_738_368,
                "reservation_global_total_bytes": 1_099_511_627_776,
                "reservation_manifest_binds_per_file_reserved_bytes": True,
                "reservation_partial_path_formula": "final_relative_path+.partial",
                "reservation_uses_actual_destination_partial_inodes": True,
                "reservation_manifest_binds_path_device_inode_extents_logical_and_allocated_bytes": True,
                "reservation_files_exclusive_non_sparse_preallocated": True,
                "writer_consumes_reserved_partial_inodes_in_place": True,
                "reservation_handoff_requires_inode_identity_match": True,
                "reservation_qualification_verifies_in_place_overwrite_without_copy_on_write_double_allocation": True,
                "reserved_partial_truncation_only_after_complete_write_and_followed_by_file_fsync": True,
                "reserved_partial_files_absent_at_committed": True,
                "reservation_manifest_retained_and_manifest_bound_at_committed": True,
                "reservation_manifest_required": True,
                "reserved_destination_commit_order": (
                    _RESERVED_DESTINATION_COMMIT_ORDER
                ),
                "rename_no_replace_required": True,
                "cow_no_double_allocation_qualification_required": True,
                "cow_no_double_allocation_qualified": False,
                "committed_marker_exact_keys": _COMMITTED_MARKER_KEYS,
                "committed_marker_relative_path": "COMMITTED.json",
                "sha256_manifest_excludes_itself_and_committed_marker": True,
                "committed_marker_binds_terminal_state_and_sha256_manifest": True,
                "committed_marker_exclusive_create_required": True,
                "committed_marker_file_fsync_required": True,
                "committed_marker_directory_fsync_required": True,
                "committed_marker_created_after_terminal_and_manifest": True,
                "committed_marker_is_only_publication_boundary": True,
                "receipt_present": False,
                "writer_implemented": False,
                "writer_qualified": False,
                "filesystem_observed": False,
                "durable_output_written": False,
            },
        ),
    )


def _candidate_shard(shard_ordinal: int) -> CP64CandidateShardV1:
    seed_ordinal_min = (shard_ordinal - 1) * 64 + 1
    logical_request_ordinal_min = (shard_ordinal - 1) * 1_024 + 1
    return cast(
        CP64CandidateShardV1,
        _record(
            CP64CandidateShardV1,
            {
                "schema_version": CP64_TEST28_SCHEMA_VERSION,
                "shard_ordinal": shard_ordinal,
                "shard_id": f"shard-{shard_ordinal:04d}",
                "relative_directory": f"shards/shard-{shard_ordinal:04d}",
                "seed_ordinal_min": seed_ordinal_min,
                "seed_ordinal_max": seed_ordinal_min + 63,
                "seed_ordinal_count": 64,
                "logical_request_ordinal_min": logical_request_ordinal_min,
                "logical_request_ordinal_max": logical_request_ordinal_min + 1_023,
                "logical_request_count": 1_024,
                "all_sixteen_rows_per_seed_collocated": True,
                "logical_requests_strictly_increasing": True,
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
                "definition_only": True,
                "selected_for_production": False,
                "instantiated": False,
            },
        ),
    )


def _candidate_shard_policy(
    capacity_receipt_schema: CP64CapacityReceiptSchemaV1,
    durability_receipt_schema: CP64DurabilityReceiptSchemaV1,
) -> CP64CandidateShardPolicyV1:
    return cast(
        CP64CandidateShardPolicyV1,
        _record(
            CP64CandidateShardPolicyV1,
            {
                "schema_version": CP64_TEST28_SCHEMA_VERSION,
                "policy_id": "cp64-contiguous-64-seed-ordinal-candidate-v1",
                "cp63_schedule_contract_record_sha256": (
                    _CP63_SCHEDULE_CONTRACT_RECORD_SHA256
                ),
                "cp63_resource_contract_record_sha256": (
                    _CP63_RESOURCE_CONTRACT_RECORD_SHA256
                ),
                "capacity_receipt_schema_record_sha256": (
                    capacity_receipt_schema.record_sha256
                ),
                "durability_receipt_schema_record_sha256": (
                    durability_receipt_schema.record_sha256
                ),
                "mapping_formula": ("floor((logical_request_ordinal-1)/1024)+1"),
                "shard_count": 32,
                "seed_count": 2_048,
                "row_count": 16,
                "total_request_count": 32_768,
                "seed_ordinals_per_shard": 64,
                "logical_requests_per_shard": 1_024,
                "shard_ordinals": tuple(range(1, 33)),
                "shards": tuple(_candidate_shard(index) for index in range(1, 33)),
                "same_seed_rows_collocated": True,
                "duplicate_seed_values_distinguished_by_ordinal": True,
                "historical_pre_cp61_eight_shard_plan_inherited": False,
                "candidate_policy_frozen": True,
                "candidate_policy_selected_for_production": False,
                "production_shard_map_bound": False,
                "production_shard_map_instantiated": False,
            },
        ),
    )


def _production_shard_map_receipt_schema(
    candidate_shard_policy: CP64CandidateShardPolicyV1,
) -> CP64ProductionShardMapReceiptSchemaV1:
    return cast(
        CP64ProductionShardMapReceiptSchemaV1,
        _record(
            CP64ProductionShardMapReceiptSchemaV1,
            {
                "schema_version": CP64_TEST28_SCHEMA_VERSION,
                "receipt_schema": ("cp64-test28-production-shard-map-receipt-v1"),
                "purpose": "future-production-shard-map-selection-only",
                "exact_keys": _PRODUCTION_SHARD_MAP_RECEIPT_KEYS,
                "shard_record_exact_keys": _SHARD_RECORD_KEYS,
                "exactly_32_candidate_shard_records_required": True,
                "shard_ordinals_strictly_increasing_unique_1_through_32": True,
                "logical_ordinal_ranges_contiguous_nonoverlapping_cover_1_through_32768": True,
                "seed_ordinal_ranges_contiguous_nonoverlapping_cover_1_through_2048": True,
                "shard_record_candidate_equality_field_pairs": (
                    ("shard_ordinal", "shard_ordinal"),
                    ("shard_id", "shard_id"),
                    ("seed_ordinal_min", "seed_ordinal_min"),
                    ("seed_ordinal_max", "seed_ordinal_max"),
                    (
                        "logical_request_ordinal_min",
                        "logical_request_ordinal_min",
                    ),
                    (
                        "logical_request_ordinal_max",
                        "logical_request_ordinal_max",
                    ),
                    ("logical_request_count", "logical_request_count"),
                    ("relative_directory", "relative_directory"),
                    (
                        "capacity_partition_bytes",
                        "candidate_destination_reservation_bytes",
                    ),
                ),
                "shard_record_candidate_fields_must_equal_candidate_record": True,
                "relative_directory_must_equal_candidate_shard_relative_directory": True,
                "per_file_reservation_manifest_entry_sha256_required_for_each_reserved_partial": True,
                "shard_record_per_file_reservation_link_order": (
                    "requests.jsonl",
                    "raw_records.jsonl",
                    "stable_traces.jsonl",
                    "stderr_records.bin",
                ),
                "shard_record_per_file_reservation_links_exactly_four": True,
                "shard_record_per_file_reservation_link_digests_exact_nonzero_sha256": True,
                "shard_record_per_file_paths_match_candidate_templates": True,
                "shard_record_per_file_reserved_bytes_sum_to_candidate_destination_reservation_bytes": True,
                "each_shard_capacity_partition_bytes": 34_359_738_368,
                "all_shard_capacity_partition_sum_bytes": 1_099_511_627_776,
                "all_shard_capacity_partition_sum_equals_global_destination_reservation": True,
                "shard_record_digest_formula": (
                    "SHA256(cp64-test28-production-shard-map-shard-record-v1\\0+"
                    "canonical(shard-record-with-zero-shard-record-sha256))"
                ),
                "candidate_shard_policy_sha256": (candidate_shard_policy.record_sha256),
                "mapping_formula": ("floor((logical_request_ordinal-1)/1024)+1"),
                "shard_count": 32,
                "attempt_binding_required": True,
                "reservation_manifest_binding_required": True,
                "receipt_present": False,
                "candidate_policy_selected_for_production": False,
                "production_shard_map_bound": False,
                "production_shard_map_instantiated": False,
            },
        ),
    )


def _launch_authorization_receipt_schema() -> CP64LaunchAuthorizationReceiptSchemaV1:
    return cast(
        CP64LaunchAuthorizationReceiptSchemaV1,
        _record(
            CP64LaunchAuthorizationReceiptSchemaV1,
            {
                "schema_version": CP64_TEST28_SCHEMA_VERSION,
                "receipt_schema": ("cp64-test28-launch-authorization-receipt-v1"),
                "purpose": "future-explicit-production-launch-authorization-only",
                "exact_keys": _LAUNCH_AUTHORIZATION_RECEIPT_KEYS,
                "proposed_v15_lifecycle_states": _PROPOSED_V15_LIFECYCLE_STATES,
                "v14_allowed_attempt_states": _V14_ALLOWED_ATTEMPT_STATES,
                "v14_transition_graph": _V14_TRANSITION_GRAPH,
                "proposed_v15_transition_graph": (_PROPOSED_V15_TRANSITION_GRAPH),
                "current_state": "DRAFT_PRE_FREEZE",
                "v15_protocol_and_manifest_amendment_required": True,
                "proposed_v15_protocol_and_manifest_paths_available_to_builder": False,
                "proposed_v15_protocol_and_manifest_consumed_by_bundle": False,
                "proposed_v15_protocol_relative_path": (
                    "research/preregistrations/" "cp50_test28_mixed_initializer_v15.md"
                ),
                "proposed_v15_machine_manifest_relative_path": (
                    "research/fixtures/cp50_test28_mixed_initializer_v15.json"
                ),
                "proposed_v15_transition_graph_authoritative_for_production": False,
                "preflight_and_authorization_are_artifact_stages_not_lifecycle_states": True,
                "frozen_prestart_terminal_states": (
                    "INVALID_PROTOCOL",
                    "ABORTED_INFRA",
                    "INCOMPLETE",
                ),
                "partial_external_seed_acquisition_terminal_state": "INCOMPLETE",
                "any_durable_external_seed_value_spends_attempt": True,
                "no_redraw_reselection_replacement_after_durable_seed_acquisition": True,
                "pre_durable_output_infrastructure_abort_new_attempt_requires_written_independent_adjudication_and_identical_frozen_inputs": True,
                "authorization_requires_frozen_attempt_state": True,
                "authorization_must_follow_preauthorization_outcome_authorization_arm": True,
                "authorization_is_artifact_stage_not_lifecycle_state": True,
                "authorization_must_precede_postauthorization_outcome": True,
                "authorization_does_not_equal_started": True,
                "postauthorization_started_outcome_and_binding_started_receipt_must_be_durable_before_production_runner_rng_or_child": True,
                "transition_api_exposed": False,
                "receipt_present": False,
                "authority_verified": False,
                "launch_authorized": False,
                "started": False,
            },
        ),
    )


def _no_execution_gate_contract() -> CP64NoExecutionGateContractV1:
    _validate_future_digest_dag()
    return cast(
        CP64NoExecutionGateContractV1,
        _record(
            CP64NoExecutionGateContractV1,
            {
                "schema_version": CP64_TEST28_SCHEMA_VERSION,
                "production_gate_ids": _PRODUCTION_GATE_IDS,
                "production_gate_states": ("MISSING",) * 17,
                "requirement_schemas_frozen": False,
                "cp64_scaffolded_receipt_keysets_and_cross_bindings_predeclared": True,
                "all_required_production_receipt_keysets_predeclared": False,
                "complete_receipt_type_range_size_and_domain_schemas_frozen": False,
                "complete_auxiliary_artifact_size_schema_frozen": False,
                "bounded_auxiliary_artifact_size_proof_present": False,
                "generic_prestart_terminal_record_schema_frozen": False,
                "all_required_production_receipt_digest_preimages_frozen": False,
                "authorization_signature_preimage_and_verifier_frozen": False,
                "production_evidence_required_count": 17,
                "production_evidence_present_count": 0,
                "preauthorization_gate_count": 16,
                "preflight_gate_summary_covered_gate_count": 15,
                "preflight_gate_summary_gate_ids": _PRODUCTION_GATE_IDS[:15],
                "preflight_gate_summary_evidence_node_ids": (
                    _PREFLIGHT_GATE_SUMMARY_EVIDENCE_NODE_IDS
                ),
                "preflight_gate_summary_ids_states_evidence_strictly_aligned": True,
                "preflight_gate_summary_requires_all_covered_states_pass": True,
                "preflight_gate_summary_requires_exact_nonzero_sha256_per_covered_gate": True,
                "preflight_gate_summary_exact_keys": _PREFLIGHT_GATE_SUMMARY_KEYS,
                "preflight_gate_summary_excludes_independent_signoff_and_launch_authorization": True,
                "future_digest_node_order": _FUTURE_DIGEST_NODE_ORDER,
                "future_digest_edges": _FUTURE_DIGEST_EDGES,
                "source_receipt_binds_capsule_body": False,
                "capacity_receipt_binds_shard_map": False,
                "launch_authorization_is_only_final_downstream_aggregator": True,
                "digest_dag_acyclic": True,
                "external_seed_values_present": False,
                "source_authority_verified": False,
                "full_runtime_lock_recomputed": False,
                "capacity_measured": False,
                "durability_verified": False,
                "production_shard_map_bound": False,
                "production_runner_supervisor_qualified": False,
                "preflight_gate_summary_present": False,
                "closed_refusal_failure_classifier_qualified": False,
                "freeze_receipt_present": False,
                "power_thresholds_frozen": False,
                "independent_signoffs_present": False,
                "launch_authorization_present": False,
                "started": False,
                "production_request_materialization_exposed": False,
                "production_campaign_exposed": False,
                "preflight_passed": False,
                "readiness_state": "BLOCKED_MISSING_PRODUCTION_EVIDENCE",
                "execution_authorized": False,
            },
        ),
    )


def cp64_candidate_shard_for_logical_ordinal(
    logical_request_ordinal: object,
) -> CP64CandidateShardV1:
    """Return the definition-only candidate shard containing one logical ordinal."""

    if type(logical_request_ordinal) is not int:
        raise TypeError("logical_request_ordinal must be an exact integer")
    if not 1 <= logical_request_ordinal <= 32_768:
        raise ValueError("logical_request_ordinal must lie in 1..32768")
    shard_ordinal = (logical_request_ordinal - 1) // 1_024 + 1
    return _candidate_shard(shard_ordinal)


def cp64_candidate_shard_bounds(shard_ordinal: object) -> CP64CandidateShardV1:
    """Return the whole definition-only candidate shard for an exact ordinal."""

    if type(shard_ordinal) is not int:
        raise TypeError("shard_ordinal must be an exact integer")
    if not 1 <= shard_ordinal <= 32:
        raise ValueError("shard_ordinal must lie in 1..32")
    return _candidate_shard(shard_ordinal)


def cp64_production_custody_preflight_bundle() -> CP64ProductionCustodyPreflightBundleV1:
    """Return the zero-execution CP64 custody/preflight definition."""

    capacity_receipt_schema = _capacity_receipt_schema()
    durability_receipt_schema = _durability_receipt_schema()
    candidate_shard_policy = _candidate_shard_policy(
        capacity_receipt_schema,
        durability_receipt_schema,
    )
    return cast(
        CP64ProductionCustodyPreflightBundleV1,
        _record(
            CP64ProductionCustodyPreflightBundleV1,
            {
                "schema_version": CP64_TEST28_SCHEMA_VERSION,
                "scope": CP64_TEST28_SCOPE,
                "v15_protocol_and_manifest_amendment_required": True,
                "proposed_v15_protocol_and_manifest_paths_available_to_builder": False,
                "proposed_v15_protocol_and_manifest_consumed_by_bundle": False,
                "proposed_v15_protocol_relative_path": (
                    "research/preregistrations/" "cp50_test28_mixed_initializer_v15.md"
                ),
                "proposed_v15_machine_manifest_relative_path": (
                    "research/fixtures/cp50_test28_mixed_initializer_v15.json"
                ),
                "predecessor_custody": _predecessor_custody(),
                "external_seed_source_receipt_schema": (
                    _external_seed_source_receipt_schema()
                ),
                "production_runtime_receipt_schema": (
                    _production_runtime_receipt_schema()
                ),
                "capacity_receipt_schema": capacity_receipt_schema,
                "durability_receipt_schema": durability_receipt_schema,
                "candidate_shard_policy": candidate_shard_policy,
                "production_shard_map_receipt_schema": (
                    _production_shard_map_receipt_schema(candidate_shard_policy)
                ),
                "launch_authorization_receipt_schema": (
                    _launch_authorization_receipt_schema()
                ),
                "no_execution_gate_contract": _no_execution_gate_contract(),
                "zero_argument_builder": True,
                "stdlib_only_import": True,
                "project_modules_imported": False,
                "host_filesystem_probed": False,
                "cp64_scaffolded_receipt_keysets_and_cross_bindings_predeclared": True,
                "all_required_production_receipt_keysets_predeclared": False,
                "complete_receipt_type_range_size_and_domain_schemas_frozen": False,
                "complete_auxiliary_artifact_size_schema_frozen": False,
                "bounded_auxiliary_artifact_size_proof_present": False,
                "generic_prestart_terminal_record_schema_frozen": False,
                "all_required_production_receipt_digest_preimages_frozen": False,
                "authorization_signature_preimage_and_verifier_frozen": False,
                "candidate_shard_policy_frozen": True,
                "candidate_shard_policy_selected_for_production": False,
                "external_seed_values_present": False,
                "external_seed_source_bound": False,
                "external_seed_source_receipt_present": False,
                "production_seed_capsule_present": False,
                "production_runtime_receipt_present": False,
                "capacity_receipt_present": False,
                "capacity_reservation_present": False,
                "durability_receipt_present": False,
                "production_shard_map_receipt_present": False,
                "freeze_receipt_present": False,
                "power_threshold_receipt_present": False,
                "independent_signoffs_present": False,
                "launch_authorization_present": False,
                "started_receipt_present": False,
                "committed_marker_present": False,
                "durable_writer_implemented": False,
                "production_runner_supervisor_qualified": False,
                "closed_refusal_failure_classification_implemented": False,
                "preflight_gate_summary_present": False,
                "production_runner_bound": False,
                "production_schema_frozen": False,
                "production_requests_materialized": False,
                "production_campaign_exposed": False,
                "production_execution_authorized": False,
                "production_execution_observed": False,
                "estimates_computed": False,
                "intervals_computed": False,
                "decision_made": False,
                "cp64_scaffolded_custody_preflight_inventory_and_policy_scaffold_complete": True,
                "runner_and_recomputation_blocker_closed": False,
                "unconditional_operational_predictions_blocker_closed": False,
                "power_and_thresholds_blocker_closed": False,
                "confirmatory_custody_blocker_closed": False,
                "confirmatory_evidence": False,
                "manuscript_claim": False,
                "formal_test_28_status": "OPEN",
                "formal_test_28_closed": False,
            },
        ),
    )


def _validate_public_record(record: object) -> Tuple[_SealedRecord, bytes]:
    if type(record) not in _RECORD_DOMAINS:
        raise TypeError("unsupported CP64 record type")
    sealed = cast(_SealedRecord, record)
    with _ISSUED_RECORD_LOCK:
        issued_snapshot = _ISSUED_RECORD_SNAPSHOTS.get(sealed)
        if issued_snapshot is None:
            raise TypeError("CP64 record was not module-created")
        current = _canonical_bytes(sealed, require_issued=True)
        if current != issued_snapshot:
            raise ValueError("CP64 issued record was mutated")
        supplied = getattr(sealed, "record_sha256")
        names = tuple(item.name for item in fields(type(sealed)))
        provisional = object.__new__(type(sealed))
        for name in names:
            object.__setattr__(
                provisional,
                name,
                _ZERO_SHA256 if name == "record_sha256" else getattr(sealed, name),
            )
        expected = hashlib.sha256(
            _RECORD_DOMAINS[type(sealed)]
            + b"\0"
            + _canonical_bytes(provisional, require_issued=False)
        ).hexdigest()
        if supplied != expected:
            raise ValueError("CP64 record digest differs")
        return sealed, issued_snapshot


def cp64_canonical_json_bytes(record: object) -> bytes:
    """Encode one exact, unchanged, module-issued CP64 record."""

    _validated, issued_snapshot = _validate_public_record(record)
    return issued_snapshot


def cp64_sha256(record: object) -> str:
    """Hash one validated CP64 record with its exact public type tag."""

    validated, issued_snapshot = _validate_public_record(record)
    return hashlib.sha256(
        b"cp64-public-record-v1\0"
        + type(validated).__name__.encode("ascii")
        + b"\0"
        + issued_snapshot
    ).hexdigest()


__all__ = (
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
