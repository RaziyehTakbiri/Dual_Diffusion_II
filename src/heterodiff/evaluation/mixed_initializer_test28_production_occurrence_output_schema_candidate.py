"""Define the CP74 production occurrence/output *candidate* descriptor.

This standard-library-only module owns no production data and exposes no
caller-data, path, writer, runner, or validation API.  Its zero-argument
builder returns a sealed, deterministic descriptor bundle.  The bundle closes
the development candidate inventories, lifecycle occurrence expressions,
framing envelopes, and digest/cross-binding formulas that CP65 intentionally
left opaque.  It does not accept the candidate independently, freeze a
production schema, observe an artifact, supply evidence, satisfy a production
gate, close a draft blocker, authorize execution, or close Formal Test 28.

The separately implemented CP74 independent module can reconstruct this
canonical bundle from caller-supplied bytes without importing this or another
project module.  Structural agreement between the two implementations is not
independent scientific acceptance of the candidate.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, fields
import hashlib
import json
import threading
from typing import List, Mapping, Optional, Tuple, cast
import weakref
import zlib


CP74_TEST28_SCHEMA_VERSION = (
    "cp74-test28-production-occurrence-output-schema-candidate-v1"
)
CP74_TEST28_SCOPE = (
    "development-only-definition-of-a-production-occurrence-output-schema-"
    "candidate;all-64-cp65-artifact-descriptors-preserved;closed-11-branch-"
    "and-6-crash-cut-occurrence-overlay;15-referenced-output-envelope-"
    "framing-order-cardinality-digest-and-cross-binding-descriptors;24-"
    "cross-binding-formulas;descriptor-bodies-only;primary-decision-"
    "semantics-unresolved-and-deferred-to-external-power-review;no-production-"
    "body-input;no-independent-schema-acceptance;no-production-schema-freeze;"
    "no-production-artifact-observation-provenance-authentication-runtime-"
    "attempt-durability-recomputation-decision-evidence-gate-blocker-"
    "authorization-launch-or-test28-closure-claim;zero-argument-static-"
    "builder;no-caller-data-parser-path-writer-runner-or-io-api;stdlib-only;"
    "project-modules-not-imported"
)
CP74_TEST28_FORMAL_TEST_28_STATUS = "OPEN"
CP74_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID = (
    "whole_seed_candidate_production_artifact_occurrence_branch_and_execution_"
    "output_schema_definition"
)
CP74_TEST28_ARTIFACT_COUNT = 64
CP74_TEST28_REFERENCED_OUTPUT_COUNT = 15
CP74_TEST28_LIFECYCLE_BRANCH_COUNT = 11
CP74_TEST28_CRASH_CUT_COUNT = 6
CP74_TEST28_OUTPUT_CROSS_BINDING_COUNT = 24
CP74_TEST28_SHARD_COUNT = 32
CP74_TEST28_SEED_COUNT = 2_048
CP74_TEST28_ROW_COUNT = 16
CP74_TEST28_REQUEST_COUNT = 32_768
CP74_TEST28_ESTIMAND_COUNT = 554
CP74_TEST28_PRODUCTION_GATE_COUNT = 17
CP74_TEST28_BLOCKER_LEDGER_TOTAL_COUNT = 29
CP74_TEST28_BLOCKER_LEDGER_SATISFIED_COUNT = 25
CP74_TEST28_BLOCKER_LEDGER_MISSING_COUNT = 4


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del cls, args, kwargs
        raise TypeError("CP74 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("CP74 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP74 records are not pickle objects")


_ALLOW_RECORD_CLASS_DEFINITION = True


@dataclass(frozen=True, eq=False, init=False)
class CP74PredecessorCustodyV1(_SealedRecord):
    schema_version: str
    v24_protocol_markdown_path: str
    v24_protocol_markdown_sha256: str
    v24_protocol_markdown_bytes: int
    v24_protocol_markdown_lf_count: int
    v24_machine_manifest_path: str
    v24_machine_manifest_sha256: str
    v24_machine_manifest_bytes: int
    v24_machine_manifest_lf_count: int
    predecessor_component_ids: Tuple[str, ...]
    predecessor_source_paths: Tuple[str, ...]
    predecessor_source_sha256s: Tuple[str, ...]
    predecessor_bundle_record_sha256s: Tuple[str, ...]
    predecessor_bundle_public_sha256s: Tuple[str, ...]
    cp65_artifact_id_order_sha256: str
    cp65_artifact_schema_record_order_sha256: str
    cp65_referenced_output_id_order_sha256: str
    cp65_schema_semantic_sha256: str
    cp65_gate_evidence_dag_node_count: int
    cp65_gate_evidence_dag_edge_count: int
    cp65_gate_evidence_dag_semantic_sha256: str
    cp65_gate_evidence_dag_is_not_full_typed_graph: bool
    cp65_gate_evidence_artifact_id_aliases: Tuple[Tuple[str, str], ...]
    cp65_typed_artifact_preimage_graph_vector_lengths: Tuple[int, ...]
    cp65_typed_artifact_preimage_graph_semantic_sha256: str
    cp65_typed_digest_graph_inherited_by_hash_reference_only: bool
    cp65_typed_digest_graph_revalidated_by_cp74: bool
    custody_is_hash_reference_only: bool
    predecessor_runtime_imports_performed: bool
    production_artifacts_observed: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP74LifecycleBranchRuleV1(_SealedRecord):
    schema_version: str
    branch_ordinal: int
    branch_id: str
    branch_phase: str
    terminal_state: str
    preauthorization_outcome_arm: str
    postauthorization_outcome_arm: str
    always_required_artifact_ids: Tuple[str, ...]
    always_forbidden_artifact_ids: Tuple[str, ...]
    durable_prefix_artifact_ids: Tuple[str, ...]
    allowed_crash_cut_ids: Tuple[str, ...]
    started_arm_crash_recovery_rule: str
    terminal_arm_crash_recovery_rule: str
    production_rng_or_child_permitted: bool
    retry_redraw_topup_or_reselection_permitted: bool
    terminal_state_record_required: bool
    sha256_manifest_required: bool
    committed_marker_required: bool
    candidate_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP74CrashCutRuleV1(_SealedRecord):
    schema_version: str
    crash_cut_ordinal: int
    crash_cut_id: str
    crash_cut_phase: str
    applicable_branch_ids: Tuple[str, ...]
    required_durable_artifact_ids: Tuple[str, ...]
    forbidden_artifact_ids: Tuple[str, ...]
    conditional_artifact_ids: Tuple[str, ...]
    recovery_rule: str
    terminal_state_rule: str
    production_rng_or_child_permitted: bool
    retry_redraw_topup_or_reselection_permitted: bool
    candidate_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP74ArtifactOccurrenceRuleV1(_SealedRecord):
    schema_version: str
    artifact_ordinal: int
    artifact_id: str
    cp65_schema_version: str
    cp65_artifact_schema_record_sha256: str
    path_template: str
    path_scope: str
    presence_rule_id: str
    encoding: str
    media_kind: str
    exact_keys: Tuple[str, ...]
    field_rule_ids: Tuple[str, ...]
    record_rule_id: str
    cp65_minimum_instances: int
    cp65_maximum_instances: int
    minimum_bytes_per_instance: int
    maximum_bytes_per_instance: int
    final_newline_rule: str
    digest_preimage_contract_id: str
    dag_node_ids: Tuple[str, ...]
    auxiliary_reservation_class: str
    cp64_contract_preserved: bool
    cp65_definition_only: bool
    branch_occurrence_expressions: Tuple[Tuple[str, str], ...]
    conditional_occurrence_rule_ids: Tuple[str, ...]
    dependency_predecessor_artifact_ids: Tuple[str, ...]
    retained_if_durable: bool
    manifest_bound_if_present: bool
    committed_marker_transitively_binds_if_present: bool
    conditional_rules_closed: bool
    candidate_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP74ExecutionOutputSemanticRuleV1(_SealedRecord):
    schema_version: str
    output_ordinal: int
    artifact_id: str
    cp65_artifact_schema_record_sha256: str
    path_template: str
    path_scope: str
    media_kind: str
    output_schema_id: str
    canonical_encoding: str
    framing_rule: str
    final_terminator_rule: str
    complete_attempt_instance_count: int
    complete_attempt_units_per_instance: int
    complete_attempt_total_unit_count: int
    ordering_rule: str
    exact_top_level_keys: Tuple[str, ...]
    nested_schema_rules: Tuple[str, ...]
    field_semantic_rules: Tuple[str, ...]
    record_identity_fields: Tuple[str, ...]
    closed_outcome_arms: Tuple[str, ...]
    record_digest_domain: str
    ordered_record_digest_domain: str
    body_digest_domain: str
    source_contract_ids: Tuple[str, ...]
    cross_binding_rule_ids: Tuple[str, ...]
    production_values_present: bool
    candidate_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP74OutputCrossBindingRuleV1(_SealedRecord):
    schema_version: str
    rule_ordinal: int
    rule_id: str
    source_artifact_ids: Tuple[str, ...]
    source_pointer_or_components: Tuple[str, ...]
    target_artifact_ids: Tuple[str, ...]
    target_pointer_or_components: Tuple[str, ...]
    digest_or_equality_kind: str
    preimage_or_equality_formula: str
    cardinality_rule: str
    ordering_rule: str
    required_in_complete_attempt: bool
    candidate_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP74CandidateSchemaContractV1(_SealedRecord):
    schema_version: str
    scope: str
    canonical_profile_id: str
    artifact_count: int
    receipt_envelope_artifact_count: int
    referenced_output_artifact_count: int
    frozen_or_binary_custody_artifact_count: int
    lifecycle_branch_count: int
    crash_cut_count: int
    output_cross_binding_count: int
    shard_count: int
    seed_count: int
    row_count: int
    request_count: int
    estimand_count: int
    primary_gate_slot_count: int
    artifact_ids: Tuple[str, ...]
    lifecycle_branch_ids: Tuple[str, ...]
    crash_cut_ids: Tuple[str, ...]
    referenced_output_artifact_ids: Tuple[str, ...]
    output_cross_binding_rule_ids: Tuple[str, ...]
    branch_occurrence_expression_enum: Tuple[str, ...]
    conditional_occurrence_rule_ids: Tuple[str, ...]
    all_cp65_artifact_descriptors_preserved: bool
    all_artifact_occurrences_closed: bool
    all_branch_arms_mutually_exclusive_and_exhaustive: bool
    all_conditional_occurrence_rules_closed: bool
    all_output_envelope_framing_and_cross_binding_descriptors_candidate_complete: bool
    all_cross_bindings_candidate_complete: bool
    descriptor_bodies_only: bool
    production_output_bodies_accepted: bool
    public_caller_data_api_exposed: bool
    project_modules_imported: bool
    stdlib_only: bool
    module_direct_filesystem_io: bool
    module_direct_clock: bool
    module_direct_rng: bool
    module_direct_network: bool
    module_direct_subprocess: bool
    candidate_schema_inventory_complete: bool
    candidate_descriptor_definition_complete: bool
    primary_decision_semantics_resolved: bool
    primary_decision_semantics_deferred_to_external_power_review: bool
    independent_structural_validator_required: bool
    schema_acceptance_independent: bool
    authoritative_for_production: bool
    production_schema_frozen: bool
    production_execution_and_output_schema_frozen: bool
    production_receipt_schema_frozen: bool
    production_artifacts_observed: bool
    production_evidence_accepted: bool
    gate_ids: Tuple[str, ...]
    gate_states: Tuple[str, ...]
    blocker_ids: Tuple[str, ...]
    blocker_states: Tuple[str, ...]
    blocker_ledger_total_count: int
    blocker_ledger_satisfied_count: int
    blocker_ledger_missing_count: int
    formal_test_28_status: str
    formal_test_28_closed: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP74ProductionOccurrenceOutputSchemaCandidateBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    predecessor_custody: CP74PredecessorCustodyV1
    contract: CP74CandidateSchemaContractV1
    lifecycle_branch_rules: Tuple[CP74LifecycleBranchRuleV1, ...]
    crash_cut_rules: Tuple[CP74CrashCutRuleV1, ...]
    artifact_occurrence_rules: Tuple[CP74ArtifactOccurrenceRuleV1, ...]
    execution_output_semantic_rules: Tuple[CP74ExecutionOutputSemanticRuleV1, ...]
    output_cross_binding_rules: Tuple[CP74OutputCrossBindingRuleV1, ...]
    lifecycle_branch_count: int
    crash_cut_count: int
    artifact_occurrence_rule_count: int
    execution_output_semantic_rule_count: int
    output_cross_binding_rule_count: int
    ordered_lifecycle_branch_record_sha256: str
    ordered_crash_cut_record_sha256: str
    ordered_artifact_occurrence_record_sha256: str
    ordered_execution_output_semantic_record_sha256: str
    ordered_output_cross_binding_record_sha256: str
    candidate_schema_semantic_sha256: str
    all_record_digests_valid: bool
    all_inventories_complete: bool
    all_occurrence_expressions_closed: bool
    all_cross_bindings_resolve: bool
    authoritative_builder_validates_internal_definition: bool
    authoritative_builder_accepts_production_data: bool
    candidate_descriptor_packet_internally_consistent: bool
    candidate_descriptor_definition_complete: bool
    candidate_schema_executable: bool
    primary_decision_semantics_resolved: bool
    primary_decision_semantics_deferred_to_external_power_review: bool
    schema_acceptance_independent: bool
    authoritative_for_production: bool
    production_schema_frozen: bool
    production_execution_and_output_schema_frozen: bool
    production_receipt_schema_frozen: bool
    production_evidence_accepted: bool
    production_gate_states: Tuple[str, ...]
    draft_blocker_states: Tuple[str, ...]
    formal_test_28_status: str
    formal_test_28_closed: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


_ALLOW_RECORD_CLASS_DEFINITION = False

_CP65_ARTIFACT_ROWS_ZLIB_B64 = "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"

_CP65_SCHEMA_VERSION = "cp65-test28-production-schema-preimage-validator-v1"
_CANONICAL_PROFILE_ID = "cp74-ascii-canonical-json-v1"
_ZERO_SHA256 = "0" * 64
_V24_PROTOCOL_PATH = "research/preregistrations/cp50_test28_mixed_initializer_v24.md"
_V24_PROTOCOL_SHA256 = (
    "0609ac037cce6d5ef22cbf1ca7ccbc11aa46b3c9a192a8b08d12de9e8a6cf135"
)
_V24_PROTOCOL_BYTES = 263_275
_V24_PROTOCOL_LF_COUNT = 4_278
_V24_MANIFEST_PATH = "research/fixtures/cp50_test28_mixed_initializer_v24.json"
_V24_MANIFEST_SHA256 = (
    "b271d19cd0a5f7f5912a1f324e88b565c7fe712111bb444d117c6ab650b6aadb"
)
_V24_MANIFEST_BYTES = 6_249_780
_V24_MANIFEST_LF_COUNT = 121_879
_PREDECESSOR_COMPONENT_IDS = (
    "cp64-production-custody-preflight",
    "cp65-production-schema-preimage-validator",
)
_PREDECESSOR_SOURCE_PATHS = (
    "src/heterodiff/evaluation/mixed_initializer_test28_production_custody_preflight.py",
    "src/heterodiff/evaluation/mixed_initializer_test28_production_schema_preimage_validator.py",
)
_PREDECESSOR_SOURCE_SHA256S = (
    "d35cbacb84e3348ae10549e053a0bb1572569583cdd03e66119353af4148bec2",
    "774cd44ad6aa82ea629ef705bde3bbb7288ccd74bd0d3a5d5c79f552a5f6a06a",
)
_PREDECESSOR_BUNDLE_RECORD_SHA256S = (
    "32f7f0c62019d8ee906e6f74300f6c33fbe55984f69cfe4fe1061ffb92463f39",
    "597f2b4b557bffb529d951858fd84e454135220db0c19dcd05fcf7ce93710f89",
)
_PREDECESSOR_BUNDLE_PUBLIC_SHA256S = (
    "caecd8630def94f7ac6da721422e3d9d71c26c351e753369abf17b224a90de83",
    "48862957062f3f0c30b7e237c10323d28f666325ca07c0d4e9f0e10e980b3ec0",
)
_CP65_ARTIFACT_ID_ORDER_SHA256 = (
    "cc7cd223d18f59933b0888b1663e3f7de157c010d189c2d46b085fd42d0da808"
)
_CP65_ARTIFACT_SCHEMA_RECORD_ORDER_SHA256 = (
    "088b09ee42fbd527940032a4dc26b30eee902d6a8cc1334e44c7bbe1698bf2ff"
)
_CP65_REFERENCED_OUTPUT_ID_ORDER_SHA256 = (
    "3d73d68568b7dc14eef9d55571593ef7436b8ccfc362e81138cf3ae907830f1e"
)
_CP65_SCHEMA_SEMANTIC_SHA256 = (
    "8855d84a573344723bc6c4c32036b7aeb878d6c66a04d5423d5f591ed40316c0"
)
_CP65_GATE_EVIDENCE_DAG_SEMANTIC_SHA256 = (
    "eb9a83e70b243882e3579c7361bc3b0dbfed31be90344c5b1f536ac5ef4b9bc2"
)
_CP65_TYPED_ARTIFACT_PREIMAGE_GRAPH_VECTOR_LENGTHS = (
    456,
    708,
    708,
    708,
    708,
    456,
)
_CP65_TYPED_ARTIFACT_PREIMAGE_GRAPH_SEMANTIC_SHA256 = (
    "a3b5b1511a7fd5abfb99f9c3ce0a413540541ef6899cfc534e8ab93bed8ef185"
)
_CP65_GATE_EVIDENCE_ARTIFACT_ID_ALIASES = (
    (
        "independent-full-32768-recomputation-receipt",
        "independent-full-32768-recomputation-qualification-receipt",
    ),
    (
        "independent-554-estimate-interval-decision-path-receipt",
        "independent-554-estimate-interval-decision-path-qualification-receipt",
    ),
)

_LIFECYCLE_BRANCH_IDS = (
    "preauthorization-invalid-protocol",
    "preauthorization-aborted-infra",
    "preauthorization-incomplete",
    "postauthorization-prestart-invalid-protocol",
    "postauthorization-prestart-aborted-infra",
    "postauthorization-prestart-incomplete",
    "started-pass",
    "started-fail",
    "started-invalid-protocol",
    "started-aborted-infra",
    "started-incomplete",
)
_CRASH_CUT_IDS = (
    "zero-source-values-after-start",
    "partial-source-values",
    "complete-seed-capsule-before-authorization",
    "later-preauthorization",
    "launch-authorization-durable-before-STARTED",
    "postauthorization-started-arm-durable-before-STARTED-receipt",
)
_REFERENCED_OUTPUT_ARTIFACT_IDS = (
    "environment",
    "primary-metrics",
    "secondary-diagnostics",
    "postexecution-independent-recomputation",
    "decisions",
    "deviations",
    "failures",
    "exclusions",
    "reruns",
    "shard-requests",
    "shard-raw-records",
    "shard-stable-traces",
    "shard-stderr-records",
    "shard-rng-initial-states",
    "shard-rng-final-states",
)
_STOCHASTIC_OR_POSTEXECUTION_OUTPUT_ARTIFACT_IDS = tuple(
    artifact_id
    for artifact_id in _REFERENCED_OUTPUT_ARTIFACT_IDS
    if artifact_id != "environment"
)
_ARTIFACT_IDS = (
    "frozen-protocol",
    "frozen-protocol-sha256",
    "frozen-machine-manifest",
    "source-manifest",
    "dependency-lock",
    "freeze-receipt",
    "power-threshold-receipt",
    "preflight-gate-summary",
    "independent-signoff-set",
    "capacity-receipt",
    "auxiliary-metadata-reservation",
    "reservation-manifest",
    "production-runtime-receipt",
    "external-seed-acquisition-start-receipt",
    "external-seed-acquisition-journal",
    "external-seed-source-receipt",
    "seed-capsule-body",
    "production-shard-map-receipt",
    "durability-receipt",
    "preauthorization-outcome",
    "launch-authorization",
    "postauthorization-outcome",
    "started-receipt",
    "environment",
    "launch-receipt",
    "primary-metrics",
    "secondary-diagnostics",
    "postexecution-independent-recomputation",
    "decisions",
    "deviations",
    "failures",
    "exclusions",
    "reruns",
    "terminal-state",
    "sha256-manifest",
    "committed-marker",
    "launch-authority-public-key",
    "dependency-lock-match-receipt",
    "seed-source-custody-artifact",
    "seed-capsule-sequence-crosscheck-receipt",
    "production-schedule",
    "production-runner-supervisor-qualification-receipt",
    "closed-refusal-failure-classifier-qualification-receipt",
    "independent-554-estimate-interval-decision-path-qualification-receipt",
    "independent-full-32768-recomputation-qualification-receipt",
    "independent-reviewer-public-key-set",
    "seed-source-authority-public-key",
    "seed-source-authority-attestation",
    "frozen-source-fixture-materialization",
    "production-schema-preimage-validator-bundle",
    "power-review-signoff",
    "preterminal-durable-artifact-inventory",
    "external-digest-preimage-registry",
    "auxiliary-reservation-transition-journal",
    "shard-requests",
    "shard-raw-records",
    "shard-stable-traces",
    "shard-stderr-records",
    "shard-rng-initial-states",
    "shard-rng-final-states",
    "shard-index",
    "shard-receipt",
    "partial-seed-acquisition-terminal-receipt",
    "rejected-launch-authorization-candidate",
)
_OUTPUT_CROSS_BINDING_RULE_IDS = (
    "production-schedule-to-shard-requests",
    "production-shard-map-to-shard-requests-and-shard-index",
    "shard-requests-to-shard-raw-records",
    "environment-to-production-runtime-receipt",
    "frozen-runtime-lock-and-production-runtime-receipt-to-shard-raw-records",
    "shard-raw-records-to-shard-stable-traces",
    "shard-raw-records-to-shard-stderr-records",
    "shard-raw-records-to-shard-rng-initial-states",
    "shard-raw-records-to-shard-rng-final-states",
    "shard-requests-to-shard-index",
    "shard-raw-records-to-shard-index",
    "shard-stable-traces-to-shard-index",
    "shard-stderr-records-to-shard-index",
    "shard-rng-initial-states-to-shard-index",
    "shard-rng-final-states-to-shard-index",
    "production-shard-map-and-shard-index-and-shard-files-to-shard-receipt",
    "shard-raw-files-and-shard-receipts-to-postexecution-independent-recomputation",
    "independent-raw-to-stable-reprojection-to-postexecution-independent-recomputation",
    "postexecution-independent-recomputation-to-primary-metrics",
    "shard-request-raw-stable-and-receipt-facts-to-secondary-diagnostics-and-auxiliary-ledgers",
    "primary-metrics-and-power-thresholds-to-decisions",
    "decisions-and-auxiliary-ledgers-to-terminal-state",
    "referenced-outputs-to-preterminal-inventory-and-sha256-manifest",
    "terminal-state-and-sha256-manifest-to-committed-marker",
)
_MANIFEST_BINDING_EXCLUDED_ARTIFACT_IDS = (
    "sha256-manifest",
    "committed-marker",
    "auxiliary-reservation-transition-journal",
)
_COMMITTED_TRANSITIVE_BINDING_EXCLUDED_ARTIFACT_IDS = ("committed-marker",)
_STABLE_TO_CP69_TO_CP71_CANDIDATE_FORMULA = (
    "independently-reproject-every-hashed-raw-record-using-the-candidate-"
    "projection-and-rebuild-every-stable-file-before-setting-the-flag-true;"
    "for-each-exact-CP74-stable-record-in-logical-request-ordinal-order-1-"
    "through-32768-apply-the-frozen-CP63-compact-semantic-projection-field-"
    "by-field-without-calling-or-claiming-the-CP63-rehearsal-only-parser;"
    "the-transient-semantic-view-replaces-the-CP74-returned-or-closed-"
    "trace_schema-with-the-corresponding-CP62-trace_schema-renames-request_"
    "instance_sha256-to-calibration_instance_sha256-renames-cp74_semantic_"
    "trace_sha256-or-cp74_closed_trace_sha256-to-the-corresponding-CP62-"
    "carrier-and-recomputes-that-omitted-carrier-CP62-terminal-digest-solely-"
    "to-replay-the-frozen-CP63-semantic-projection-while-the-CP74-attempt-and-"
    "request-custody-values-remain-unchanged;derive-selected_configuration-"
    "first_selected_attempt_one_based-observable_cell_label-observable_"
    "contribution_ordinal-selected_feature_ids-and-exact-Fraction-selected_"
    "feature_values-by-the-frozen-CP63-selected-configuration-contribution-"
    "ordinal-and-feature-vector-formulas;construct-one-exact-21-key-CP69-"
    "record;set-schema_version=cp69-test28-compact-projection-interchange-"
    "qualification-v1;set-source_semantic_schema_version=cp63-test28-"
    "independent-compact-recomputation-v1;copy-(seed_ordinal,row_ordinal,"
    "logical_request_ordinal,row_key,fixture_id,strategy,budget,plan_seed_hex,"
    "seed_free_request_sha256,request_instance_sha256,runtime_lock_sha256)-"
    "from-the-"
    "validated-CP74-stable-record;set-CP69-stable_trace_sha256-to-plain-SHA256-"
    "of-the-exact-canonical-CP74-stable-record-bytes-before-LF-not-the-old-"
    "CP63-rehearsal-domain-digest;set-observable_cell_label=closed_status;set-"
    "selected=true-only-for-returned-rejection-selected-before-deadline-or-"
    "returned-sir-selected-before-deadline-and-false-otherwise;set-first_"
    "selected_attempt_one_based=selected_index+1-only-for-selected-bounded-"
    "rejection-and-null-otherwise;set-(selected_feature_ids,selected_feature_"
    "values)=the-exact-CP63-feature-projection-for-selected_configuration-or-"
    "two-empty-vectors-otherwise;set-record_"
    "sha256-to-SHA256(cp69-test28-compact-interchange-observation-v1\\0||"
    "ASCII-canonical-JSON-of-the-exact-21-key-record-with-record_sha256-set-to-"
    "64-zero-hex-characters);canonicalize-each-CP69-record-with-zero-trailing-"
    "bytes-and-reduce-the-exact-32768-record-byte-stream-once-through-the-"
    "development-structural-CP71-reducer-in-logical-request-ordinal-order;"
    "cp71_output_canonical_json_sha256-equals-plain-SHA256-of-the-exact-"
    "rebuilt-CP71-output-bytes;CP72-and-CP73-public-summary-fields-equal-their-"
    "exact-class-name-domain-separated-public-digests-for-that-output-and-"
    "stream-but-remain-noncustodial-development-structural-references"
)
_BRANCH_OCCURRENCE_EXPRESSION_ENUM = (
    "ABSENT",
    "EXACT_GLOBAL_ONE",
    "EXACT_ALL_32_SHARDS",
    "DURABLE_PREFIX_DEPENDENCY_CLOSED",
    "IFF_PARTIAL_ACQUISITION_TERMINAL",
    "IFF_REJECTED_AUTHORIZATION_CANDIDATE",
)
_CONDITIONAL_OCCURRENCE_RULE_IDS = (
    "partial-acquisition-terminal-receipt-required-iff-acquisition-start-committed-and-complete-source-receipt-absent",
    "rejected-launch-authorization-candidate-required-iff-preauthorization-terminal-arm-wins-after-durable-prepared-authorization-candidate-exists",
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
_DRAFT_BLOCKER_IDS = (
    "confirmatory_custody",
    "power_and_thresholds",
    "runner_and_recomputation",
    "unconditional_operational_predictions",
)
_MISSING_GATE_STATES = tuple("MISSING" for _ in _PRODUCTION_GATE_IDS)
_MISSING_BLOCKER_STATES = tuple("MISSING" for _ in _DRAFT_BLOCKER_IDS)

_RAW_TOP_LEVEL_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "seed_ordinal",
    "row_ordinal",
    "logical_request_ordinal",
    "row_key",
    "fixture_id",
    "strategy",
    "budget",
    "plan_seed_hex",
    "seed_free_request_sha256",
    "request_instance_sha256",
    "runtime_lock_sha256",
    "phase",
    "closed_status",
    "failure_code",
    "kernel_trace",
    "supervisor_custody",
    "raw_sha256",
)
_STABLE_TOP_LEVEL_KEYS = tuple(
    key
    for key in _RAW_TOP_LEVEL_KEYS
    if key not in ("supervisor_custody", "raw_sha256")
)
_KERNEL_TRACE_KEYS = ("semantic", "volatile_custody")
_SUPERVISOR_CUSTODY_KEYS = (
    "pid",
    "process_group",
    "start_monotonic_ns",
    "deadline_monotonic_ns",
    "terminal_monotonic_ns",
    "exit_code",
    "term_signal",
    "frame_bytes",
    "child_frame_sha256",
    "stderr_bytes",
    "stderr_hex",
    "stderr_sha256",
    "completion_strictly_before_deadline",
    "exact_one_frame",
    "termination_attempted",
    "termination_signal_delivered",
    "kill_attempted",
    "reaped",
)
_VOLATILE_CUSTODY_KEYS = (
    "plan_sha256",
    "kernel_certificate_sha256",
    "result_sha256",
    "provider_runtime_identity",
    "reference_runtime_identity",
    "nested_record_custody",
)
_NESTED_CUSTODY_KEYS = (
    "slot_index",
    "slot_kind",
    "configuration_sha256",
    "source_evaluation_sha256",
    "facade_evaluation_sha256",
    "scored_sha256",
    "quota_sha256",
    "attempt_sha256",
    "particle_sha256",
)
_RUNTIME_OBSERVATION_KEYS = (
    "runtime_profile_id",
    "runtime_lock_sha256",
    "python_version",
    "python_implementation",
    "python_soabi",
    "platform_system",
    "platform_release",
    "machine",
    "byteorder",
    "floating_rounding_mode",
    "numpy_version",
    "scipy_version",
    "threadpoolctl_version",
    "decimal_module_version",
    "libmpdec_version",
    "cp62_source_sha256",
    "kernel_source_sha256",
    "reference_source_sha256",
    "facade_source_sha256",
    "exact_score_source_sha256",
    "quota_source_sha256",
    "full_runtime_lock_recomputed",
)
_RESOURCE_PREFLIGHT_KEYS = (
    "mode",
    "reference_occurrence_limit",
    "reference_coordinate_limit",
    "worst_case_occurrences",
    "worst_case_coordinates",
    "fixed_budget_work_certified",
    "arbitrary_rational_quota_required",
)
_RETURNED_SEMANTIC_KEYS = (
    "trace_schema",
    "stable_request_sha256",
    "request_instance_sha256",
    "plan_seed_hex",
    "fixture_id",
    "strategy",
    "budget",
    "source_certificate_sha256",
    "source_parameter_sha256",
    "reference_parameter_sha256",
    "facade_certificate_sha256",
    "adapter_role_sha256",
    "initializer_role_sha256",
    "residual_context_sha256",
    "runtime_observation",
    "exact_log_weight_upper_bound",
    "exact_log_weight_lower_bound",
    "proposal_seed_hex",
    "rejection_decision_seed_hex",
    "sir_resampling_seed_hex",
    "resource_preflight",
    "explicit_rejection_exhaustion",
    "structural_result_validation_replays_provider_evaluate",
    "structural_result_validation_replays_provider_evaluate_or_source_public_validate_evaluation",
    "structural_result_validation_replays_reference_sampler",
    "structural_result_validation_replays_rng",
    "operational_reference_sampling_law_verified",
    "philox_uniformity_verified",
    "stream_independence_verified",
    "iid_proposals_verified",
    "analytic_target_equality_verified",
    "exact_operational_rejection_bernoulli_verified",
    "finite_j_sir_exact_target_verified",
    "source_or_model_quality_evidence",
    "path_or_sampler_admitted",
    "formal_test_28_closed",
    "result_status",
    "proposal_stream_initial_state_sha256",
    "proposal_stream_final_state_sha256",
    "decision_stream_initial_state_sha256",
    "decision_stream_final_state_sha256",
    "resampling_stream_initial_state_sha256",
    "resampling_stream_final_state_sha256",
    "resampling_word_hex",
    "resampling_uniform_53",
    "effective_sample_size_float64_be",
    "maximum_normalized_weight_float64_be",
    "ess_warning",
    "attempts",
    "particles",
    "normalized_weights_float64_be",
    "selected_index",
    "selected_configuration",
    "cp74_semantic_trace_sha256",
)
_CLOSED_SEMANTIC_KEYS = (
    "trace_schema",
    "stable_request_sha256",
    "request_instance_sha256",
    "plan_seed_hex",
    "fixture_id",
    "strategy",
    "budget",
    "source_certificate_sha256",
    "source_parameter_sha256",
    "reference_parameter_sha256",
    "facade_certificate_sha256",
    "adapter_role_sha256",
    "initializer_role_sha256",
    "residual_context_sha256",
    "runtime_lock_sha256",
    "runtime_observation",
    "outcome_kind",
    "failure_code",
    "completed_kernel_trace_present",
    "timeout_is_semantic_nonreturn",
    "cp74_closed_trace_sha256",
)
_CONFIGURATION_KEYS = ("events", "cp62_configuration_sha256")
_SOURCE_EVALUATION_KEYS = (
    "fixture_id",
    "residual_context_float64_be",
    "cardinality",
    "count_penalty",
    "exact_log_weight",
    "rounded_exact_log_weight_float64_be",
    "direct_binary64_log_weight_float64_be",
    "exact_upper_bound_respected",
    "represented_restriction_identity_verified",
    "cp62_source_evaluation_sha256",
)
_FACADE_EVALUATION_KEYS = (
    "backend_kind",
    "residual_context_float64_be",
    "exact_log_weight",
    "rounded_log_weight_float64_be",
    "exact_upper_bound_respected",
    "exact_lower_bound_respected",
    "structural_validation_replayed_learned_model",
    "structural_validation_replayed_rng",
    "source_evaluation",
    "cp62_facade_evaluation_sha256",
)
_SCORED_KEYS = (
    "index",
    "configuration",
    "facade_evaluation",
    "exact_log_weight",
    "rounded_log_weight_float64_be",
    "cp62_scored_sha256",
)
_QUOTA_KEYS = (
    "schema_version",
    "certificate_scope",
    "proof_policy",
    "proof_contract",
    "branch",
    "delta_numerator",
    "delta_denominator",
    "precision",
    "adaptive_rounds",
    "decision_denominator",
    "quota",
    "input_lower_numerator",
    "input_lower_denominator",
    "input_upper_numerator",
    "input_upper_denominator",
    "exp_lower_numerator",
    "exp_lower_denominator",
    "exp_upper_numerator",
    "exp_upper_denominator",
    "input_lower_strict",
    "input_upper_strict",
    "exp_lower_strict",
    "exp_upper_strict",
    "terminal_rational_inequality_certified",
    "exact_divmod_input_enclosure_certified",
    "exponential_monotonicity_transfer_certified",
    "adjacent_decimal_outward_padding_certified",
    "adaptive_nested_enclosures_certified",
    "unique_scaled_floor_certified",
    "exact_scaled_floor_under_stated_contract_certified",
    "decimal_correct_rounding_contract_required",
    "decimal_implementation_formally_verified",
    "independent_transcendental_backend_verified",
    "binary_float_exp_used",
    "external_numeric_dependency_used",
    "exact_exponential_bernoulli_certified",
    "rejection_kernel_integrated",
    "runtime_portable",
    "cryptographic_authentication",
    "cp62_quota_sha256",
)
_ATTEMPT_KEYS = (
    "attempt_index",
    "scored",
    "exact_delta",
    "quota",
    "decision_word_hex",
    "accepted",
    "cp62_attempt_sha256",
)
_PARTICLE_KEYS = (
    "particle_index",
    "scored",
    "normalized_weight_float64_be",
    "cp62_particle_sha256",
)
_SANITIZED_CHILD_ENVIRONMENT = (
    ("BLIS_NUM_THREADS", "1"),
    ("CUDA_VISIBLE_DEVICES", ""),
    ("LANG", "C"),
    ("LC_ALL", "C"),
    ("MKL_NUM_THREADS", "1"),
    ("NUMEXPR_NUM_THREADS", "1"),
    ("OMP_NUM_THREADS", "1"),
    ("OPENBLAS_NUM_THREADS", "1"),
    ("PYTHONDONTWRITEBYTECODE", "1"),
    ("PYTHONHASHSEED", "0"),
    ("PYTHONNOUSERSITE", "1"),
    ("PYTHONPYCACHEPREFIX", "/dev/null"),
    ("PYTHONSAFEPATH", "1"),
    ("PYTHONUTF8", "1"),
    ("TZ", "UTC"),
    ("VECLIB_MAXIMUM_THREADS", "1"),
    ("__CF_USER_TEXT_ENCODING", "0x1F5:0x0:0x0"),
)
_CP71_ESTIMAND_KEYS = (
    "schema_version",
    "estimand_ordinal",
    "estimand_id",
    "cp61_estimand_record_sha256",
    "estimand_family",
    "row_ordinal",
    "fixture_id",
    "strategy",
    "budget",
    "observable_cell_label",
    "first_attempt_one_based",
    "feature_id",
    "feature_lower_bound",
    "feature_upper_bound",
    "denominator_mode",
    "denominator_count",
    "success_count",
    "exact_feature_sum",
    "estimate",
    "interval_method",
    "interval_state",
    "interval_lower",
    "interval_upper",
    "development_supplied_input_only",
    "input_provenance_authenticated",
    "arithmetic_transform_only",
    "record_sha256",
)

_RECORD_DOMAINS = {
    CP74PredecessorCustodyV1: b"cp74-test28-predecessor-custody-v1\0",
    CP74LifecycleBranchRuleV1: b"cp74-test28-lifecycle-branch-rule-v1\0",
    CP74CrashCutRuleV1: b"cp74-test28-crash-cut-rule-v1\0",
    CP74ArtifactOccurrenceRuleV1: b"cp74-test28-artifact-occurrence-rule-v1\0",
    CP74ExecutionOutputSemanticRuleV1: (
        b"cp74-test28-execution-output-semantic-rule-v1\0"
    ),
    CP74OutputCrossBindingRuleV1: b"cp74-test28-output-cross-binding-rule-v1\0",
    CP74CandidateSchemaContractV1: b"cp74-test28-candidate-schema-contract-v1\0",
    CP74ProductionOccurrenceOutputSchemaCandidateBundleV1: (
        b"cp74-test28-production-occurrence-output-schema-candidate-bundle-v1\0"
    ),
}
_PUBLIC_RECORD_DOMAIN = b"cp74-authoritative-public-record-v1\0"
_MAXIMUM_CANONICAL_DEPTH = 32
_MAXIMUM_CANONICAL_NODES = 262_144
_MAXIMUM_TEXT_CHARACTERS = 262_144
_ISSUED_RECORD_SNAPSHOTS: "weakref.WeakKeyDictionary[object, bytes]" = (
    weakref.WeakKeyDictionary()
)
_ISSUED_RECORD_LOCK = threading.RLock()


def _primitive(
    value: object, *, depth: int = 0, nodes: Optional[List[int]] = None
) -> object:
    if nodes is None:
        nodes = [0]
    nodes[0] += 1
    if depth > _MAXIMUM_CANONICAL_DEPTH or nodes[0] > _MAXIMUM_CANONICAL_NODES:
        raise ValueError("CP74 canonical value exceeds its structural limit")
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is str:
        if len(cast(str, value)) > _MAXIMUM_TEXT_CHARACTERS:
            raise ValueError("CP74 canonical text exceeds its limit")
        return value
    if isinstance(value, _SealedRecord):
        return {
            item.name: _primitive(
                getattr(value, item.name), depth=depth + 1, nodes=nodes
            )
            for item in fields(value)
        }
    if type(value) is tuple:
        return [
            _primitive(item, depth=depth + 1, nodes=nodes)
            for item in cast(tuple, value)
        ]
    if type(value) is list:
        return [
            _primitive(item, depth=depth + 1, nodes=nodes) for item in cast(list, value)
        ]
    if type(value) is dict:
        checked = cast(dict, value)
        if any(type(key) is not str for key in checked):
            raise TypeError("CP74 canonical mapping keys must be exact text")
        return {
            key: _primitive(checked[key], depth=depth + 1, nodes=nodes)
            for key in checked
        }
    raise TypeError("unsupported CP74 canonical value")


def _plain_json_bytes(value: object) -> bytes:
    return json.dumps(
        _primitive(value),
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _record(cls: type, values: Mapping[str, object]) -> object:
    names = tuple(item.name for item in fields(cls))
    if tuple(values) != tuple(name for name in names if name != "record_sha256"):
        raise RuntimeError("CP74 record construction fields differ")
    instance = object.__new__(cls)
    for name in names:
        object.__setattr__(
            instance, name, "0" * 64 if name == "record_sha256" else values[name]
        )
    body = _plain_json_bytes(instance)
    digest = hashlib.sha256(_RECORD_DOMAINS[cls] + body).hexdigest()
    object.__setattr__(instance, "record_sha256", digest)
    snapshot = _plain_json_bytes(instance)
    with _ISSUED_RECORD_LOCK:
        _ISSUED_RECORD_SNAPSHOTS[instance] = snapshot
    return instance


def _cp65_artifact_rows() -> Tuple[dict, ...]:
    decoded = zlib.decompress(base64.b64decode(_CP65_ARTIFACT_ROWS_ZLIB_B64))
    value = json.loads(decoded.decode("ascii"))
    if type(value) is not list or len(value) != CP74_TEST28_ARTIFACT_COUNT:
        raise RuntimeError("embedded CP65 artifact inventory differs")
    result = []
    tuple_fields = ("exact_keys", "field_rule_ids", "dag_node_ids")
    expected_fields = {
        "artifact_id",
        "record_sha256",
        "path_template",
        "path_scope",
        "presence_rule_id",
        "encoding",
        "media_kind",
        "exact_keys",
        "field_rule_ids",
        "record_rule_id",
        "minimum_instances",
        "maximum_instances",
        "minimum_bytes_per_instance",
        "maximum_bytes_per_instance",
        "final_newline_rule",
        "digest_preimage_contract_id",
        "dag_node_ids",
        "auxiliary_reservation_class",
        "cp64_contract_preserved",
    }
    for item in value:
        if type(item) is not dict or set(item) != expected_fields:
            raise RuntimeError("embedded CP65 artifact row differs")
        row = dict(item)
        for field_name in tuple_fields:
            if type(row.get(field_name)) is not list:
                raise RuntimeError("embedded CP65 tuple field differs")
            row[field_name] = tuple(row[field_name])
        cp65_body = {
            "schema_version": _CP65_SCHEMA_VERSION,
            "artifact_id": row["artifact_id"],
            "path_template": row["path_template"],
            "path_scope": row["path_scope"],
            "presence_rule_id": row["presence_rule_id"],
            "encoding": row["encoding"],
            "media_kind": row["media_kind"],
            "exact_keys": list(row["exact_keys"]),
            "field_rule_ids": list(row["field_rule_ids"]),
            "record_rule_id": row["record_rule_id"],
            "minimum_instances": row["minimum_instances"],
            "maximum_instances": row["maximum_instances"],
            "minimum_bytes_per_instance": row["minimum_bytes_per_instance"],
            "maximum_bytes_per_instance": row["maximum_bytes_per_instance"],
            "final_newline_rule": row["final_newline_rule"],
            "digest_preimage_contract_id": row["digest_preimage_contract_id"],
            "dag_node_ids": list(row["dag_node_ids"]),
            "auxiliary_reservation_class": row["auxiliary_reservation_class"],
            "cp64_contract_preserved": row["cp64_contract_preserved"],
            "definition_only": True,
            "record_sha256": _ZERO_SHA256,
        }
        recomputed = hashlib.sha256(
            b"cp65-artifact-schema-v1\0"
            + json.dumps(
                cp65_body,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("ascii")
        ).hexdigest()
        if recomputed != row.get("record_sha256"):
            raise RuntimeError("embedded CP65 artifact record digest differs")
        result.append(row)
    result_tuple = tuple(result)
    ids = tuple(cast(str, row["artifact_id"]) for row in result_tuple)
    records = tuple(cast(str, row["record_sha256"]) for row in result_tuple)
    outputs = tuple(item for item in ids if item in _REFERENCED_OUTPUT_ARTIFACT_IDS)
    if ids != _ARTIFACT_IDS:
        raise RuntimeError("embedded CP65 artifact id order differs")
    if (
        hashlib.sha256(
            b"cp74-test28-cp65-ids-order-v1\0"
            + b"".join(item.encode("ascii") for item in ids)
        ).hexdigest()
        != _CP65_ARTIFACT_ID_ORDER_SHA256
    ):
        raise RuntimeError("embedded CP65 artifact id order digest differs")
    if (
        hashlib.sha256(
            b"cp74-test28-cp65-records-order-v1\0"
            + b"".join(bytes.fromhex(item) for item in records)
        ).hexdigest()
        != _CP65_ARTIFACT_SCHEMA_RECORD_ORDER_SHA256
    ):
        raise RuntimeError("embedded CP65 schema-record order digest differs")
    if outputs != _REFERENCED_OUTPUT_ARTIFACT_IDS or (
        hashlib.sha256(
            b"cp74-test28-cp65-outs-order-v1\0"
            + b"".join(item.encode("ascii") for item in outputs)
        ).hexdigest()
        != _CP65_REFERENCED_OUTPUT_ID_ORDER_SHA256
    ):
        raise RuntimeError("embedded CP65 referenced-output order differs")
    return result_tuple


def _branch_phase(branch_id: str) -> str:
    if branch_id.startswith("preauthorization-"):
        return "PREAUTHORIZATION"
    if branch_id.startswith("postauthorization-prestart-"):
        return "POSTAUTHORIZATION_PRESTART"
    return "STARTED"


def _branch_terminal(branch_id: str) -> str:
    if branch_id.endswith("invalid-protocol"):
        return "INVALID_PROTOCOL"
    if branch_id.endswith("aborted-infra"):
        return "ABORTED_INFRA"
    if branch_id.endswith("incomplete"):
        return "INCOMPLETE"
    if branch_id == "started-pass":
        return "PASS"
    if branch_id == "started-fail":
        return "FAIL"
    raise RuntimeError("unknown CP74 lifecycle branch")


_FOUNDATIONAL_ARTIFACT_IDS = (
    "frozen-protocol",
    "frozen-protocol-sha256",
    "frozen-machine-manifest",
    "frozen-source-fixture-materialization",
    "production-schema-preimage-validator-bundle",
    "source-manifest",
    "dependency-lock",
    "freeze-receipt",
    "power-review-signoff",
    "power-threshold-receipt",
    "launch-authority-public-key",
    "independent-reviewer-public-key-set",
    "seed-source-authority-public-key",
    "preauthorization-outcome",
)
_PREAUTHORIZATION_DURABLE_PREFIX_ARTIFACT_IDS = (
    "environment",
    "production-runtime-receipt",
    "external-seed-acquisition-start-receipt",
    "external-seed-acquisition-journal",
    "preflight-gate-summary",
    "independent-signoff-set",
    "capacity-receipt",
    "auxiliary-metadata-reservation",
    "reservation-manifest",
    "dependency-lock-match-receipt",
    "seed-source-custody-artifact",
    "production-runner-supervisor-qualification-receipt",
    "closed-refusal-failure-classifier-qualification-receipt",
    "independent-554-estimate-interval-decision-path-qualification-receipt",
    "independent-full-32768-recomputation-qualification-receipt",
    "seed-source-authority-attestation",
    "external-digest-preimage-registry",
    "auxiliary-reservation-transition-journal",
)
_POST_ACQUISITION_PREAUTHORIZATION_PREFIX_ARTIFACT_IDS = (
    "seed-capsule-sequence-crosscheck-receipt",
    "production-schedule",
)
_TERMINAL_CLOSURE_ARTIFACT_IDS = (
    "preterminal-durable-artifact-inventory",
    "terminal-state",
    "sha256-manifest",
    "committed-marker",
)
_SHARD_CLOSURE_ARTIFACT_IDS = ("shard-index", "shard-receipt")
_CP65_GATE1_REQUIRED_ARTIFACT_IDS = (
    "frozen-protocol",
    "frozen-protocol-sha256",
    "frozen-machine-manifest",
    "production-schema-preimage-validator-bundle",
    "frozen-source-fixture-materialization",
    "source-manifest",
    "dependency-lock",
    "power-review-signoff",
    "power-threshold-receipt",
    "launch-authority-public-key",
    "independent-reviewer-public-key-set",
    "seed-source-authority-public-key",
    "freeze-receipt",
)
_CP65_GATE2_REQUIRED_ARTIFACT_IDS = (
    "frozen-protocol",
    "frozen-machine-manifest",
    "production-schema-preimage-validator-bundle",
    "frozen-source-fixture-materialization",
    "source-manifest",
)
_CP65_GATE3_REQUIRED_ARTIFACT_IDS = (
    "freeze-receipt",
    "dependency-lock",
    "dependency-lock-match-receipt",
)
_CP65_GATE4_REQUIRED_ARTIFACT_IDS = (
    "freeze-receipt",
    "source-manifest",
    "dependency-lock",
    "dependency-lock-match-receipt",
    "production-runtime-receipt",
)
_CP65_GATE5_REQUIRED_ARTIFACT_IDS = (
    "freeze-receipt",
    "external-seed-acquisition-start-receipt",
    "external-seed-acquisition-journal",
    "seed-source-custody-artifact",
    "seed-source-authority-public-key",
    "seed-source-authority-attestation",
    "external-seed-source-receipt",
)
_CP65_GATE5_PRE_SOURCE_CUSTODY_ARTIFACT_IDS = (
    "external-seed-acquisition-start-receipt",
    "external-seed-acquisition-journal",
    "seed-source-custody-artifact",
    "seed-source-authority-public-key",
    "seed-source-authority-attestation",
)
_CP65_GATE6_REQUIRED_ARTIFACT_IDS = (
    "freeze-receipt",
    "external-seed-acquisition-start-receipt",
    "external-seed-acquisition-journal",
    "seed-source-custody-artifact",
    "seed-source-authority-public-key",
    "seed-source-authority-attestation",
    "external-seed-source-receipt",
    "seed-capsule-body",
    "seed-capsule-sequence-crosscheck-receipt",
)
_CP65_GATE7_REQUIRED_ARTIFACT_IDS = (
    "freeze-receipt",
    "external-seed-source-receipt",
    "seed-capsule-body",
    "production-runtime-receipt",
    "production-schedule",
)
_CP65_GATE8_REQUIRED_ARTIFACT_IDS = (
    "freeze-receipt",
    "production-schema-preimage-validator-bundle",
    "production-schedule",
    "auxiliary-metadata-reservation",
    "reservation-manifest",
    "capacity-receipt",
)
_CP65_GATE9_REQUIRED_ARTIFACT_IDS = (
    "freeze-receipt",
    "source-manifest",
    "capacity-receipt",
    "auxiliary-metadata-reservation",
    "reservation-manifest",
    "durability-receipt",
)
_CP65_GATE10_REQUIRED_ARTIFACT_IDS = (
    "freeze-receipt",
    "seed-capsule-body",
    "production-schedule",
    "capacity-receipt",
    "durability-receipt",
    "reservation-manifest",
    "production-shard-map-receipt",
)
_CP65_GATE17_REQUIRED_ARTIFACT_IDS = (
    "frozen-protocol",
    "frozen-protocol-sha256",
    "frozen-machine-manifest",
    "production-schema-preimage-validator-bundle",
    "frozen-source-fixture-materialization",
    "source-manifest",
    "dependency-lock",
    "power-review-signoff",
    "power-threshold-receipt",
    "launch-authority-public-key",
    "independent-reviewer-public-key-set",
    "seed-source-authority-public-key",
    "freeze-receipt",
    "dependency-lock-match-receipt",
    "production-runtime-receipt",
    "external-seed-acquisition-start-receipt",
    "external-seed-acquisition-journal",
    "seed-source-custody-artifact",
    "seed-source-authority-attestation",
    "external-seed-source-receipt",
    "seed-capsule-body",
    "seed-capsule-sequence-crosscheck-receipt",
    "production-schedule",
    "auxiliary-metadata-reservation",
    "reservation-manifest",
    "capacity-receipt",
    "durability-receipt",
    "production-shard-map-receipt",
    "production-runner-supervisor-qualification-receipt",
    "closed-refusal-failure-classifier-qualification-receipt",
    "independent-full-32768-recomputation-qualification-receipt",
    "independent-554-estimate-interval-decision-path-qualification-receipt",
    "preflight-gate-summary",
    "external-digest-preimage-registry",
    "independent-signoff-set",
    "preauthorization-outcome",
    "launch-authorization",
)


def _ordered_artifact_union(*groups: Tuple[str, ...]) -> Tuple[str, ...]:
    selected = {artifact_id for group in groups for artifact_id in group}
    if not selected <= set(_ARTIFACT_IDS):
        raise RuntimeError("CP74 gate-stage artifact union has an unknown artifact")
    return tuple(
        artifact_id for artifact_id in _ARTIFACT_IDS if artifact_id in selected
    )


_CUT1_AND_CUT2_REQUIRED_BASE = _ordered_artifact_union(
    _CP65_GATE1_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE2_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE3_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE4_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE5_PRE_SOURCE_CUSTODY_ARTIFACT_IDS,
    ("environment",),
)
_CUT3_REQUIRED_BASE = _ordered_artifact_union(
    _CP65_GATE1_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE2_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE3_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE4_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE5_REQUIRED_ARTIFACT_IDS,
    ("seed-capsule-body", "environment"),
)
_CUT4_REQUIRED_BASE = _ordered_artifact_union(
    _CP65_GATE1_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE2_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE3_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE4_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE5_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE6_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE7_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE8_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE9_REQUIRED_ARTIFACT_IDS,
    _CP65_GATE10_REQUIRED_ARTIFACT_IDS,
    ("environment",),
)
_CUT5_REQUIRED_BASE = _ordered_artifact_union(
    _CP65_GATE17_REQUIRED_ARTIFACT_IDS, ("environment",)
)
_CUT6_REQUIRED_BASE = _ordered_artifact_union(
    _CP65_GATE17_REQUIRED_ARTIFACT_IDS,
    ("environment", "postauthorization-outcome"),
)
_CP64_FUTURE_DIGEST_EDGES = (
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
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "preflight-gate-summary",
    ),
    (
        "independent-554-estimate-interval-decision-path-qualification-receipt",
        "preflight-gate-summary",
    ),
    ("power-threshold-receipt", "preflight-gate-summary"),
)


def _branch_expression(artifact_id: str, branch_id: str) -> str:
    phase = _branch_phase(branch_id)
    complete = branch_id in ("started-pass", "started-fail")
    started = phase == "STARTED"
    if artifact_id == "environment":
        return (
            "DURABLE_PREFIX_DEPENDENCY_CLOSED"
            if phase == "PREAUTHORIZATION"
            else "EXACT_GLOBAL_ONE"
        )
    if artifact_id in _REFERENCED_OUTPUT_ARTIFACT_IDS:
        if not started:
            return "ABSENT"
        if complete:
            return (
                "EXACT_ALL_32_SHARDS"
                if artifact_id.startswith("shard-")
                else "EXACT_GLOBAL_ONE"
            )
        return "DURABLE_PREFIX_DEPENDENCY_CLOSED"
    if artifact_id in _SHARD_CLOSURE_ARTIFACT_IDS:
        if not started:
            return "ABSENT"
        return "EXACT_ALL_32_SHARDS" if complete else "DURABLE_PREFIX_DEPENDENCY_CLOSED"
    if artifact_id == "partial-seed-acquisition-terminal-receipt":
        return (
            "IFF_PARTIAL_ACQUISITION_TERMINAL"
            if phase == "PREAUTHORIZATION"
            else "ABSENT"
        )
    if artifact_id == "rejected-launch-authorization-candidate":
        return (
            "IFF_REJECTED_AUTHORIZATION_CANDIDATE"
            if phase == "PREAUTHORIZATION"
            else "ABSENT"
        )
    if artifact_id in ("external-seed-source-receipt", "seed-capsule-body"):
        return (
            "DURABLE_PREFIX_DEPENDENCY_CLOSED"
            if phase == "PREAUTHORIZATION"
            else "EXACT_GLOBAL_ONE"
        )
    if artifact_id in _POST_ACQUISITION_PREAUTHORIZATION_PREFIX_ARTIFACT_IDS:
        return (
            "DURABLE_PREFIX_DEPENDENCY_CLOSED"
            if phase == "PREAUTHORIZATION"
            else "EXACT_GLOBAL_ONE"
        )
    if artifact_id in _PREAUTHORIZATION_DURABLE_PREFIX_ARTIFACT_IDS:
        return (
            "DURABLE_PREFIX_DEPENDENCY_CLOSED"
            if phase == "PREAUTHORIZATION"
            else "EXACT_GLOBAL_ONE"
        )
    if artifact_id in ("production-shard-map-receipt", "durability-receipt"):
        return (
            "DURABLE_PREFIX_DEPENDENCY_CLOSED"
            if phase == "PREAUTHORIZATION"
            else "EXACT_GLOBAL_ONE"
        )
    if artifact_id == "launch-authorization":
        return "ABSENT" if phase == "PREAUTHORIZATION" else "EXACT_GLOBAL_ONE"
    if artifact_id == "postauthorization-outcome":
        return "ABSENT" if phase == "PREAUTHORIZATION" else "EXACT_GLOBAL_ONE"
    if artifact_id in ("started-receipt", "launch-receipt"):
        return "EXACT_GLOBAL_ONE" if started else "ABSENT"
    if artifact_id in _FOUNDATIONAL_ARTIFACT_IDS + _TERMINAL_CLOSURE_ARTIFACT_IDS:
        return "EXACT_GLOBAL_ONE"
    raise RuntimeError("CP74 artifact lacks a closed branch occurrence expression")


def _artifact_dependencies(artifact_id: str) -> Tuple[str, ...]:
    mapping = {
        "production-runtime-receipt": ("environment",),
        "external-seed-acquisition-start-receipt": ("production-runtime-receipt",),
        "external-seed-acquisition-journal": (
            "external-seed-acquisition-start-receipt",
        ),
        "external-seed-source-receipt": (
            "external-seed-acquisition-start-receipt",
            "external-seed-acquisition-journal",
        ),
        "seed-capsule-body": ("external-seed-source-receipt",),
        "production-schedule": (
            "seed-capsule-body",
            "seed-capsule-sequence-crosscheck-receipt",
        ),
        "capacity-receipt": ("production-schedule",),
        "durability-receipt": ("capacity-receipt", "reservation-manifest"),
        "production-shard-map-receipt": (
            "production-schedule",
            "capacity-receipt",
            "durability-receipt",
        ),
        "preauthorization-outcome": (),
        "launch-authorization": ("preauthorization-outcome",),
        "postauthorization-outcome": ("launch-authorization",),
        "started-receipt": ("postauthorization-outcome",),
        "launch-receipt": ("started-receipt",),
        "shard-requests": ("production-schedule", "production-shard-map-receipt"),
        "shard-raw-records": (
            "shard-requests",
            "production-runtime-receipt",
        ),
        "shard-stable-traces": ("shard-raw-records",),
        "shard-stderr-records": ("shard-raw-records",),
        "shard-rng-initial-states": ("shard-raw-records",),
        "shard-rng-final-states": ("shard-raw-records",),
        "shard-index": (
            "production-shard-map-receipt",
            "shard-requests",
            "shard-raw-records",
            "shard-stable-traces",
            "shard-stderr-records",
            "shard-rng-initial-states",
            "shard-rng-final-states",
        ),
        "shard-receipt": ("shard-index",),
        "environment": (
            "source-manifest",
            "dependency-lock",
            "freeze-receipt",
            "dependency-lock-match-receipt",
        ),
        "postexecution-independent-recomputation": (
            "shard-raw-records",
            "shard-stable-traces",
            "shard-receipt",
        ),
        "primary-metrics": (
            "postexecution-independent-recomputation",
            "power-threshold-receipt",
            "power-review-signoff",
        ),
        "secondary-diagnostics": (
            "shard-requests",
            "shard-raw-records",
            "shard-stable-traces",
            "shard-receipt",
        ),
        "decisions": (
            "primary-metrics",
            "power-threshold-receipt",
            "power-review-signoff",
        ),
        "deviations": ("secondary-diagnostics",),
        "failures": ("secondary-diagnostics",),
        "exclusions": ("secondary-diagnostics",),
        "reruns": ("secondary-diagnostics",),
        "preterminal-durable-artifact-inventory": (),
        "terminal-state": ("preauthorization-outcome",),
        "sha256-manifest": (
            "preterminal-durable-artifact-inventory",
            "terminal-state",
        ),
        "committed-marker": ("terminal-state", "sha256-manifest"),
        "partial-seed-acquisition-terminal-receipt": (
            "external-seed-acquisition-start-receipt",
            "external-seed-acquisition-journal",
        ),
        "rejected-launch-authorization-candidate": ("preauthorization-outcome",),
    }
    inherited = tuple(
        source for source, target in _CP64_FUTURE_DIGEST_EDGES if target == artifact_id
    )
    selected = set(inherited + mapping.get(artifact_id, ()))
    return tuple(item for item in _ARTIFACT_IDS if item in selected)


def _transitive_artifact_dependencies(artifact_id: str) -> Tuple[str, ...]:
    """Return the frozen direct-DAG ancestor set in artifact-roster order."""

    discovered = set()
    frontier = list(_artifact_dependencies(artifact_id))
    while frontier:
        predecessor = frontier.pop()
        if predecessor in discovered:
            continue
        if predecessor not in _ARTIFACT_IDS:
            raise RuntimeError("CP74 dependency closure has an unknown artifact")
        discovered.add(predecessor)
        frontier.extend(_artifact_dependencies(predecessor))
    if artifact_id in discovered:
        raise RuntimeError("CP74 dependency graph is cyclic")
    return tuple(item for item in _ARTIFACT_IDS if item in discovered)


def _build_lifecycle_rules() -> Tuple[CP74LifecycleBranchRuleV1, ...]:
    rows = []
    for ordinal, branch_id in enumerate(_LIFECYCLE_BRANCH_IDS, 1):
        phase = _branch_phase(branch_id)
        terminal = _branch_terminal(branch_id)
        pre_arm = terminal if phase == "PREAUTHORIZATION" else "AUTHORIZATION"
        post_arm = (
            "ABSENT"
            if phase == "PREAUTHORIZATION"
            else (terminal if phase == "POSTAUTHORIZATION_PRESTART" else "STARTED")
        )
        started = phase == "STARTED"
        expressions = {
            artifact_id: _branch_expression(artifact_id, branch_id)
            for artifact_id in _ARTIFACT_IDS
        }
        required = tuple(
            artifact_id
            for artifact_id in _ARTIFACT_IDS
            if expressions[artifact_id] in ("EXACT_GLOBAL_ONE", "EXACT_ALL_32_SHARDS")
        )
        forbidden = tuple(
            artifact_id
            for artifact_id in _ARTIFACT_IDS
            if expressions[artifact_id] == "ABSENT"
        )
        durable = tuple(
            artifact_id
            for artifact_id in _ARTIFACT_IDS
            if expressions[artifact_id] == "DURABLE_PREFIX_DEPENDENCY_CLOSED"
        )
        allowed_cuts = (
            _CRASH_CUT_IDS[:4]
            if phase == "PREAUTHORIZATION"
            else (
                (_CRASH_CUT_IDS[4],)
                if phase == "POSTAUTHORIZATION_PRESTART"
                else ((_CRASH_CUT_IDS[5],) if branch_id == "started-incomplete" else ())
            )
        )
        rows.append(
            cast(
                CP74LifecycleBranchRuleV1,
                _record(
                    CP74LifecycleBranchRuleV1,
                    {
                        "schema_version": CP74_TEST28_SCHEMA_VERSION,
                        "branch_ordinal": ordinal,
                        "branch_id": branch_id,
                        "branch_phase": phase,
                        "terminal_state": terminal,
                        "preauthorization_outcome_arm": pre_arm,
                        "postauthorization_outcome_arm": post_arm,
                        "always_required_artifact_ids": required,
                        "always_forbidden_artifact_ids": forbidden,
                        "durable_prefix_artifact_ids": durable,
                        "allowed_crash_cut_ids": allowed_cuts,
                        "started_arm_crash_recovery_rule": (
                            "not-applicable"
                            if not started
                            else "durable-STARTED-arm-recovers-STARTED-then-terminalizes-without-reselection"
                        ),
                        "terminal_arm_crash_recovery_rule": "durable-terminal-arm-completes-terminal-state-manifest-and-COMMITTED-without-reselection",
                        "production_rng_or_child_permitted": started,
                        "retry_redraw_topup_or_reselection_permitted": False,
                        "terminal_state_record_required": True,
                        "sha256_manifest_required": True,
                        "committed_marker_required": True,
                        "candidate_only": True,
                    },
                ),
            )
        )
    for row in rows:
        required = set(row.always_required_artifact_ids)
        forbidden = set(row.always_forbidden_artifact_ids)
        durable = set(row.durable_prefix_artifact_ids)
        if required & forbidden or durable & forbidden:
            raise RuntimeError("CP74 lifecycle required/forbidden sets overlap")
        for artifact_id in required:
            if _branch_expression(artifact_id, row.branch_id) == "ABSENT":
                raise RuntimeError("CP74 required lifecycle artifact is absent")
        for artifact_id in forbidden:
            if _branch_expression(artifact_id, row.branch_id) != "ABSENT":
                raise RuntimeError("CP74 forbidden lifecycle artifact is present")
        for artifact_id in durable:
            if (
                _branch_expression(artifact_id, row.branch_id)
                != "DURABLE_PREFIX_DEPENDENCY_CLOSED"
            ):
                raise RuntimeError("CP74 durable-prefix lifecycle artifact differs")
    return tuple(rows)


def _build_crash_cut_rules() -> Tuple[CP74CrashCutRuleV1, ...]:
    preauth_branches = _LIFECYCLE_BRANCH_IDS[:3]
    postauth_branches = _LIFECYCLE_BRANCH_IDS[3:6]
    specs = (
        (
            "PREAUTHORIZATION",
            preauth_branches,
            _CUT1_AND_CUT2_REQUIRED_BASE,
            ("external-seed-source-receipt", "seed-capsule-body")
            + _POST_ACQUISITION_PREAUTHORIZATION_PREFIX_ARTIFACT_IDS
            + ("production-shard-map-receipt", "durability-receipt")
            + _STOCHASTIC_OR_POSTEXECUTION_OUTPUT_ARTIFACT_IDS
            + _SHARD_CLOSURE_ARTIFACT_IDS,
            ("partial-seed-acquisition-terminal-receipt",),
            "empty-acquisition-journal-file-is-preallocated-fsynced-directory-fsynced-and-inode-rechecked-before-acquisition-start-receipt;subsequent-chained-journal-entries-depend-on-the-acquisition-start-digest;zero-value-cut-has-a-durable-empty-journal-and-partial-terminal-receipt-acquired-count-and-valid-entry-count-exactly-0",
            "preauthorization-terminal-state-selected-without-production-RNG-or-child",
        ),
        (
            "PREAUTHORIZATION",
            preauth_branches,
            _CUT1_AND_CUT2_REQUIRED_BASE,
            ("external-seed-source-receipt", "seed-capsule-body")
            + _POST_ACQUISITION_PREAUTHORIZATION_PREFIX_ARTIFACT_IDS
            + ("production-shard-map-receipt", "durability-receipt")
            + _STOCHASTIC_OR_POSTEXECUTION_OUTPUT_ARTIFACT_IDS
            + _SHARD_CLOSURE_ARTIFACT_IDS,
            ("partial-seed-acquisition-terminal-receipt",),
            "partial-terminal-receipt-has-equal-acquired-and-journal-count-in-inclusive-range-1-through-2047",
            "preauthorization-terminal-state-selected-without-production-RNG-or-child",
        ),
        (
            "PREAUTHORIZATION",
            preauth_branches,
            _CUT3_REQUIRED_BASE,
            (
                "partial-seed-acquisition-terminal-receipt",
                "production-shard-map-receipt",
                "durability-receipt",
            )
            + _POST_ACQUISITION_PREAUTHORIZATION_PREFIX_ARTIFACT_IDS
            + _STOCHASTIC_OR_POSTEXECUTION_OUTPUT_ARTIFACT_IDS
            + _SHARD_CLOSURE_ARTIFACT_IDS,
            (),
            "complete-2048-value-source-receipt-and-seed-capsule-are-durable-before-authorization-selection",
            "preauthorization-terminal-state-selected-without-production-RNG-or-child",
        ),
        (
            "PREAUTHORIZATION",
            preauth_branches,
            _CUT4_REQUIRED_BASE,
            ("partial-seed-acquisition-terminal-receipt",)
            + _STOCHASTIC_OR_POSTEXECUTION_OUTPUT_ARTIFACT_IDS
            + _SHARD_CLOSURE_ARTIFACT_IDS,
            ("rejected-launch-authorization-candidate",),
            "later-preauthorization-durable-prefix-is-inventory-bound-and-complete-source-receipt-forbids-partial-receipt",
            "preauthorization-terminal-state-selected-without-production-RNG-or-child",
        ),
        (
            "POSTAUTHORIZATION_PRESTART",
            postauth_branches,
            _CUT5_REQUIRED_BASE,
            ("started-receipt", "launch-receipt")
            + _STOCHASTIC_OR_POSTEXECUTION_OUTPUT_ARTIFACT_IDS
            + _SHARD_CLOSURE_ARTIFACT_IDS,
            (),
            "durable-launch-authorization-recovers-authorization-before-postauthorization-terminalization",
            "postauthorization-prestart-terminal-state-selected-without-production-RNG-or-child",
        ),
        (
            "STARTED",
            ("started-incomplete",),
            _CUT6_REQUIRED_BASE,
            ("started-receipt", "launch-receipt")
            + _STOCHASTIC_OR_POSTEXECUTION_OUTPUT_ARTIFACT_IDS
            + _SHARD_CLOSURE_ARTIFACT_IDS,
            (),
            "durable-STARTED-outcome-arm-before-STARTED-receipt-recovers-STARTED;then-publishes-and-binds-STARTED-receipt-and-launch-receipt-before-INCOMPLETE-terminalization",
            "STARTED_INCOMPLETE-only;zero-output-occurrences;no-production-RNG-or-child",
        ),
    )
    rows = []
    for ordinal, (
        phase,
        branches,
        required,
        forbidden,
        conditional,
        recovery,
        terminal,
    ) in enumerate(specs, 1):
        required_set = set(required)
        for artifact_id in required:
            required_set.update(_transitive_artifact_dependencies(artifact_id))
        required = tuple(
            artifact_id for artifact_id in _ARTIFACT_IDS if artifact_id in required_set
        )
        forbidden_set = set(forbidden)
        conditional_set = set(conditional)
        if not forbidden_set | conditional_set <= set(_ARTIFACT_IDS):
            raise RuntimeError("CP74 crash-cut specification has an unknown artifact")
        forbidden = tuple(
            artifact_id for artifact_id in _ARTIFACT_IDS if artifact_id in forbidden_set
        )
        conditional = tuple(
            artifact_id
            for artifact_id in _ARTIFACT_IDS
            if artifact_id in conditional_set
        )
        if set(required) & set(forbidden):
            raise RuntimeError("CP74 crash-cut required/forbidden sets overlap")
        rows.append(
            cast(
                CP74CrashCutRuleV1,
                _record(
                    CP74CrashCutRuleV1,
                    {
                        "schema_version": CP74_TEST28_SCHEMA_VERSION,
                        "crash_cut_ordinal": ordinal,
                        "crash_cut_id": _CRASH_CUT_IDS[ordinal - 1],
                        "crash_cut_phase": phase,
                        "applicable_branch_ids": branches,
                        "required_durable_artifact_ids": required,
                        "forbidden_artifact_ids": forbidden,
                        "conditional_artifact_ids": conditional,
                        "recovery_rule": recovery
                        + ";required_durable_artifact_ids-is-the-complete-transitive-minimum-durable-predecessor-closure-at-the-cut;forbidden_artifact_ids-are-exactly-forbidden-at-the-cut;unlisted-durable-prefix-artifacts-remain-branch-and-cut-progress-dependent-and-must-obey-the-full-dependency-DAG",
                        "terminal_state_rule": terminal,
                        "production_rng_or_child_permitted": False,
                        "retry_redraw_topup_or_reselection_permitted": False,
                        "candidate_only": True,
                    },
                ),
            )
        )
    return tuple(rows)


def _build_artifact_occurrence_rules() -> Tuple[CP74ArtifactOccurrenceRuleV1, ...]:
    rows = []
    cp65_rows = _cp65_artifact_rows()
    for ordinal, source in enumerate(cp65_rows, 1):
        artifact_id = cast(str, source["artifact_id"])
        expressions = tuple(
            (branch_id, _branch_expression(artifact_id, branch_id))
            for branch_id in _LIFECYCLE_BRANCH_IDS
        )
        conditional = ()
        if artifact_id == "partial-seed-acquisition-terminal-receipt":
            conditional = (_CONDITIONAL_OCCURRENCE_RULE_IDS[0],)
        elif artifact_id == "rejected-launch-authorization-candidate":
            conditional = (_CONDITIONAL_OCCURRENCE_RULE_IDS[1],)
        rows.append(
            cast(
                CP74ArtifactOccurrenceRuleV1,
                _record(
                    CP74ArtifactOccurrenceRuleV1,
                    {
                        "schema_version": CP74_TEST28_SCHEMA_VERSION,
                        "artifact_ordinal": ordinal,
                        "artifact_id": artifact_id,
                        "cp65_schema_version": _CP65_SCHEMA_VERSION,
                        "cp65_artifact_schema_record_sha256": source["record_sha256"],
                        "path_template": source["path_template"],
                        "path_scope": source["path_scope"],
                        "presence_rule_id": source["presence_rule_id"],
                        "encoding": source["encoding"],
                        "media_kind": source["media_kind"],
                        "exact_keys": source["exact_keys"],
                        "field_rule_ids": source["field_rule_ids"],
                        "record_rule_id": source["record_rule_id"],
                        "cp65_minimum_instances": source["minimum_instances"],
                        "cp65_maximum_instances": source["maximum_instances"],
                        "minimum_bytes_per_instance": source[
                            "minimum_bytes_per_instance"
                        ],
                        "maximum_bytes_per_instance": source[
                            "maximum_bytes_per_instance"
                        ],
                        "final_newline_rule": source["final_newline_rule"],
                        "digest_preimage_contract_id": source[
                            "digest_preimage_contract_id"
                        ],
                        "dag_node_ids": source["dag_node_ids"],
                        "auxiliary_reservation_class": source[
                            "auxiliary_reservation_class"
                        ],
                        "cp64_contract_preserved": source["cp64_contract_preserved"],
                        "cp65_definition_only": True,
                        "branch_occurrence_expressions": expressions,
                        "conditional_occurrence_rule_ids": conditional,
                        "dependency_predecessor_artifact_ids": _artifact_dependencies(
                            artifact_id
                        ),
                        "retained_if_durable": True,
                        "manifest_bound_if_present": artifact_id
                        not in _MANIFEST_BINDING_EXCLUDED_ARTIFACT_IDS,
                        "committed_marker_transitively_binds_if_present": artifact_id
                        not in _COMMITTED_TRANSITIVE_BINDING_EXCLUDED_ARTIFACT_IDS,
                        "conditional_rules_closed": True,
                        "candidate_only": True,
                    },
                ),
            )
        )
    if tuple(row.artifact_id for row in rows) != tuple(
        source["artifact_id"] for source in cp65_rows
    ):
        raise RuntimeError("CP74 occurrence inventory differs from CP65 order")
    return tuple(rows)


def _key_rule(label: str, keys: Tuple[str, ...]) -> str:
    return label + "=(" + ",".join(keys) + ")"


_REQUEST_KEYS = (
    "schema_version",
    "seed_capsule_body_sha256",
    "seed_ordinal",
    "row_ordinal",
    "logical_request_ordinal",
    "row_key",
    "fixture_id",
    "strategy",
    "budget",
    "plan_seed_hex",
    "seed_free_request_sha256",
    "runtime_lock_sha256",
    "request_instance_sha256",
    "request_row_sha256",
)
_RNG_CONTAINER_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "shard_id",
    "request_count",
    "state_phase",
    "ordered_state_rows",
    "ordered_state_row_sha256s",
    "ordered_states_sha256",
    "body_sha256",
)
_RNG_ROW_KEYS = (
    "logical_request_ordinal",
    "strategy",
    "proposal_stream_state",
    "decision_stream_state",
    "resampling_stream_state",
    "row_sha256",
)
_RNG_STATE_KEYS = (
    "present",
    "bit_generator",
    "counter_u64_hex",
    "key_u64_hex",
    "buffer_u64_hex",
    "buffer_pos",
    "has_uint32",
    "uinteger_u64_hex",
)
_CLOSED_OUTCOME_ARMS = (
    "returned-rejection-selected-before-deadline",
    "returned-rejection-exhausted-before-deadline",
    "returned-sir-selected-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-censored-at-deadline",
)
_PHASE_ARMS = (
    "returned-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-at-deadline",
)
_PREEXECUTION_REFUSAL_CODES = (
    "plan_validation_refusal",
    "provider_reference_binding_refusal",
    "resource_preflight_refusal",
    "runtime_binding_refusal",
    "other_preexecution_refusal",
)
_EXECUTION_FAILURE_CODES = (
    "reference_sampling_failure",
    "score_evaluation_failure",
    "quota_certification_failure",
    "float64_normalization_failure",
    "categorical_selection_failure",
    "structural_result_validation_failure",
    "other_execution_failure",
)
_PUBLICATION_STAGE_IDS = (
    "preimport-environment",
    "per-shard-requests",
    "per-shard-raw-records",
    "per-shard-stable-traces",
    "per-shard-stderr-records",
    "per-shard-rng-initial-states",
    "per-shard-rng-final-states",
    "per-shard-index",
    "per-shard-receipt",
    "postexecution-independent-recomputation",
    "primary-metrics",
    "secondary-diagnostics",
    "decisions",
    "deviations",
    "failures",
    "exclusions",
    "reruns",
    "preterminal-durable-artifact-inventory",
    "terminal-state",
    "sha256-manifest",
    "committed-marker",
)


def _output_specifications() -> Tuple[dict, ...]:
    ledger_root = (
        "schema",
        "purpose",
        "attempt_id",
        "entry_count",
        "entries",
        "ordered_entries_sha256",
        "body_sha256",
    )
    specs = (
        {
            "artifact_id": "environment",
            "schema": "cp74-test28-production-environment-candidate-v1",
            "keys": (
                "schema",
                "purpose",
                "attempt_id",
                "freeze_receipt_sha256",
                "source_manifest_sha256",
                "dependency_lock_sha256",
                "captured_before_project_import",
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
                "ordered_environment_entries",
                "ordered_environment_entries_sha256",
                "body_sha256",
            ),
            "nested": (
                "environment-entry-exact-keys=(name,value_text,entry_sha256)",
                "ordered-environment-entries-sorted-by-unique-name",
                "sanitized-child-environment-exact17="
                + repr(_SANITIZED_CHILD_ENVIRONMENT),
            ),
            "rules": (
                "canonical-JSON-document-has-zero-trailing-bytes",
                "raw-file-SHA256-equals-production-runtime-receipt-/environment_sha256",
                "new-candidate-publication-order-environment-file-durable-before-production-runtime-receipt-and-both-durable-before-external-seed-acquisition-start",
                "runtime-values-and-digests-are-unauthenticated-candidate-fields",
            ),
            "identity": ("attempt_id",),
            "sources": ("cp62-execution-capsule", "cp65-production-runtime-receipt"),
            "cross": ("environment-to-production-runtime-receipt",),
        },
        {
            "artifact_id": "primary-metrics",
            "schema": "cp74-test28-production-primary-metrics-candidate-v1",
            "keys": (
                "schema",
                "purpose",
                "attempt_id",
                "recomputation_artifact_sha256",
                "power_threshold_receipt_sha256",
                "power_review_signoff_sha256",
                "estimand_count",
                "primary_slot_count",
                "ordered_primary_slots",
                "ordered_primary_slot_record_sha256s",
                "ordered_primary_slots_sha256",
                "body_sha256",
            ),
            "nested": (
                "primary-slot-exact-keys=(slot_ordinal,slot_id,estimand_id,estimand_record_sha256,estimate,interval_lower,interval_upper,gate_id,threshold_value,threshold_row_sha256,slot_record_sha256)",
                "exactly-32-slots-in-slot-ordinal-order",
                "gate_id-exactly-cp65-power-primary-slot-%02d-and-equals-referenced-threshold-row-gate_id",
            ),
            "rules": (
                "envelope-and-cross-binding-shape-only",
                "descriptor-does-not-select-threshold-values;future-production-body-requirements-await-external-power-review",
                "comparison-operator-direction-and-executable-decision-function-not-defined-by-this-candidate",
                "canonical-JSON-document-has-zero-trailing-bytes",
            ),
            "identity": ("attempt_id",),
            "sources": (
                "cp61-estimand-inventory-development-reference",
                "cp65-power-threshold-receipt",
            ),
            "cross": (
                "postexecution-independent-recomputation-to-primary-metrics",
                "primary-metrics-and-power-thresholds-to-decisions",
            ),
        },
        {
            "artifact_id": "secondary-diagnostics",
            "schema": "cp74-test28-production-secondary-diagnostics-candidate-v1",
            "keys": (
                "schema",
                "purpose",
                "attempt_id",
                "request_count",
                "shard_count",
                "ordered_shard_receipt_sha256s",
                "ordered_raw_file_sha256s",
                "ordered_stable_file_sha256s",
                "terminal_counts",
                "diagnostic_count",
                "ordered_diagnostics",
                "ordered_diagnostic_record_sha256s",
                "ordered_diagnostics_sha256",
                "body_sha256",
            ),
            "nested": (
                "terminal-count-exact-keys="
                "(returned_rejection_selected_before_deadline,returned_rejection_exhausted_before_deadline,returned_sir_selected_before_deadline,preexecution_refusal_before_deadline,execution_failure_before_deadline,timeout_censored_at_deadline)",
                "diagnostic-exact-keys=(diagnostic_ordinal,diagnostic_id,value_kind,value_text,source_artifact_ids,source_sha256s,diagnostic_record_sha256)",
            ),
            "rules": (
                "terminal-counts-are-exact-projections-of-32768-request-raw-stable-and-shard-receipt-facts",
                "diagnostic-id-value-kind-and-value-domain-registry-is-unresolved-and-this-row-defines-only-an-extensible-source-bound-envelope",
                "no-drop-no-retry-no-replacement-no-topup-within-one-attempt",
                "canonical-JSON-document-has-zero-trailing-bytes",
            ),
            "identity": ("attempt_id",),
            "sources": ("cp66-closed-classifier-development-reference",),
            "cross": (
                "shard-request-raw-stable-and-receipt-facts-to-secondary-diagnostics-and-auxiliary-ledgers",
            ),
        },
        {
            "artifact_id": "postexecution-independent-recomputation",
            "schema": "cp74-test28-production-independent-recomputation-candidate-v1",
            "keys": (
                "schema",
                "purpose",
                "attempt_id",
                "source_interchange_schema_version",
                "source_output_schema_version",
                "request_count",
                "estimand_count",
                "ordered_shard_receipt_sha256s",
                "ordered_raw_file_sha256s",
                "ordered_stable_file_sha256s",
                "raw_to_stable_projection_recomputed",
                "cp71_output_canonical_json_sha256",
                "cp72_validation_summary_public_sha256",
                "cp73_relation_summary_public_sha256",
                "estimand_estimate_intervals",
                "ordered_estimand_record_sha256s_sha256",
                "output_body_sha256",
                "production_recomputation_performed",
                "body_sha256",
            ),
            "nested": (
                _key_rule("estimand-record-exact-keys", _CP71_ESTIMAND_KEYS),
                "ordered-shard-vectors-exactly-32-in-shard-ordinal-order",
                "estimand-inventory-exactly-554-in-estimand-ordinal-order",
                "embedded-CP71-estimand-record-domain=cp71-test28-supplied-estimand-estimate-interval-v1-NUL",
                "embedded-CP71-ordered-estimand-domain=cp71-test28-ordered-estimand-record-digests-v1-NUL",
                "embedded-CP71-output-body-domain=cp71-test28-supplied-interchange-estimate-interval-output-body-v1-NUL",
                "cp72-validation-summary-public-digest-domain=cp72-public-record-v1-NUL",
                "cp73-relation-summary-public-digest-domain=cp73-public-record-v1-NUL",
            ),
            "rules": (
                "independently-reproject-all-32768-hashed-raw-records-to-stable-traces-and-compare-stable-files",
                "never-trust-caller-stable-traces-without-raw-reprojection",
                "cp71-cp72-cp73-digests-are-development-structural-references-only-not-production-custody-or-gate13-or-gate14-evidence",
                "production_recomputation_performed-remains-false-until-an-observed-production-body-is-independently-recomputed",
                "canonical-JSON-document-has-zero-trailing-bytes",
            ),
            "identity": ("attempt_id",),
            "sources": (
                "cp69-development-interchange-structure-reference",
                "cp71-development-arithmetic-structure-reference",
                "cp72-development-output-validator-structure-reference",
                "cp73-development-relation-structure-reference",
            ),
            "cross": (
                "shard-raw-files-and-shard-receipts-to-postexecution-independent-recomputation",
                "independent-raw-to-stable-reprojection-to-postexecution-independent-recomputation",
                "postexecution-independent-recomputation-to-primary-metrics",
            ),
        },
        {
            "artifact_id": "decisions",
            "schema": "cp74-test28-production-decisions-candidate-v1",
            "keys": (
                "schema",
                "purpose",
                "attempt_id",
                "primary_metrics_sha256",
                "power_threshold_receipt_sha256",
                "power_review_signoff_sha256",
                "primary_slot_count",
                "ordered_slot_decisions",
                "ordered_slot_decision_record_sha256s",
                "ordered_slot_decisions_sha256",
                "decision_semantics_resolved",
                "all_primary_thresholds_passed",
                "decision",
                "decision_made_at_utc",
                "body_sha256",
            ),
            "nested": (
                "slot-decision-exact-keys=(slot_ordinal,slot_id,primary_metric_record_sha256,threshold_row_sha256,decision_semantics_resolved,decision,slot_decision_record_sha256)",
                "exactly-32-slot-envelopes-in-slot-ordinal-order",
            ),
            "rules": (
                "candidate-v1-requires-decision_semantics_resolved=false",
                "candidate-v1-requires-each-slot-decision_semantics_resolved=false",
                "candidate-v1-requires-all_primary_thresholds_passed=null-decision=null-decision_made_at_utc=null-and-each-slot-decision=null",
                "comparison-operator-direction-threshold-value-law-and-PASS-FAIL-function-deferred-to-later-external-power-review-revision-and-acceptance",
                "no-currently-executable-production-decision-schema-and-no-gate14-or-gate15-qualification",
                "canonical-JSON-document-has-zero-trailing-bytes",
            ),
            "identity": ("attempt_id",),
            "sources": (
                "cp65-power-threshold-receipt-envelope",
                "future-external-power-review-revision",
            ),
            "cross": (
                "primary-metrics-and-power-thresholds-to-decisions",
                "decisions-and-auxiliary-ledgers-to-terminal-state",
            ),
        },
        {
            "artifact_id": "deviations",
            "schema": "cp74-test28-production-deviations-candidate-v1",
            "keys": ledger_root,
            "nested": (
                "deviation-entry-exact-keys=(ordinal,scope_kind,logical_request_ordinal,code,stage,description_sha256,source_artifact_id,source_record_sha256,disposition,entry_sha256)",
            ),
            "rules": (
                "PASS-or-FAIL-requires-entry_count=0-and-entries=[]",
                "entries-exactly-project-request-raw-stable-or-receipt-facts",
                "canonical-JSON-document-has-zero-trailing-bytes",
            ),
            "identity": ("attempt_id",),
            "sources": ("cp65-terminal-state",),
            "cross": (
                "shard-request-raw-stable-and-receipt-facts-to-secondary-diagnostics-and-auxiliary-ledgers",
                "decisions-and-auxiliary-ledgers-to-terminal-state",
            ),
        },
        {
            "artifact_id": "failures",
            "schema": "cp74-test28-production-failures-candidate-v1",
            "keys": ledger_root,
            "nested": (
                "failure-entry-exact-keys=(ordinal,logical_request_ordinal,shard_id,phase,closed_status,failure_code,raw_record_sha256,stable_trace_sha256,entry_sha256)",
            ),
            "rules": (
                "entries-exactly-project-every-preexecution-refusal-execution-failure-or-timeout-closed-arm-with-no-drop;returned-rejection-exhaustion-is-not-a-failure-entry",
                "canonical-JSON-document-has-zero-trailing-bytes",
            ),
            "identity": ("attempt_id",),
            "sources": ("cp66-closed-classifier-development-reference",),
            "cross": (
                "shard-request-raw-stable-and-receipt-facts-to-secondary-diagnostics-and-auxiliary-ledgers",
                "decisions-and-auxiliary-ledgers-to-terminal-state",
            ),
        },
        {
            "artifact_id": "exclusions",
            "schema": "cp74-test28-production-exclusions-candidate-v1",
            "keys": ledger_root,
            "nested": (
                "exclusion-entry-exact-keys=(ordinal,logical_request_ordinal,reason_code,source_artifact_id,source_record_sha256,estimand_population_effect,disposition,entry_sha256)",
            ),
            "rules": (
                "PASS-or-FAIL-requires-entry_count=0-and-entries=[]-and-all-32768-scheduled-requests-accounted",
                "any-exclusion-or-drop-affecting-estimand-population-forces-INVALID_PROTOCOL",
                "canonical-JSON-document-has-zero-trailing-bytes",
            ),
            "identity": ("attempt_id",),
            "sources": ("cp65-terminal-state",),
            "cross": (
                "shard-request-raw-stable-and-receipt-facts-to-secondary-diagnostics-and-auxiliary-ledgers",
                "decisions-and-auxiliary-ledgers-to-terminal-state",
            ),
        },
        {
            "artifact_id": "reruns",
            "schema": "cp74-test28-production-reruns-candidate-v1",
            "keys": ledger_root,
            "nested": (
                "rerun-entry-exact-keys=(ordinal,prior_attempt_id,new_attempt_id,independent_adjudication_sha256,frozen_inputs_sha256,abort_before_acquisition_start_durable,identical_frozen_inputs,no_same_attempt_retry,entry_sha256)",
            ),
            "rules": (
                "same-attempt-retry-redraw-replacement-or-topup-is-forbidden",
                "separate-new-attempt-rerun-requires-independent-adjudication-identical-frozen-inputs-and-prior-infrastructure-abort-before-acquisition-start-became-durable",
                "rerun-forbidden-once-the-acquisition-start-receipt-is-durable-even-when-acquired_count=0-and-forbidden-after-any-value-or-other-stochastic-output-is-durable",
                "canonical-JSON-document-has-zero-trailing-bytes",
            ),
            "identity": ("attempt_id",),
            "sources": ("cp64-acquisition-start-attempt-spend-contract",),
            "cross": (
                "shard-request-raw-stable-and-receipt-facts-to-secondary-diagnostics-and-auxiliary-ledgers",
                "decisions-and-auxiliary-ledgers-to-terminal-state",
            ),
        },
    )
    return specs + _per_shard_output_specifications()


def _per_shard_output_specifications() -> Tuple[dict, ...]:
    common_identity = (
        "attempt_id",
        "seed_ordinal",
        "row_ordinal",
        "logical_request_ordinal",
        "request_instance_sha256",
    )
    raw_nested = (
        _key_rule("kernel-trace-exact-keys", _KERNEL_TRACE_KEYS),
        _key_rule("supervisor-custody-exact-keys", _SUPERVISOR_CUSTODY_KEYS),
        _key_rule("returned-semantic-exact-keys", _RETURNED_SEMANTIC_KEYS),
        _key_rule("closed-semantic-exact-keys", _CLOSED_SEMANTIC_KEYS),
        _key_rule("volatile-custody-exact-keys", _VOLATILE_CUSTODY_KEYS),
        _key_rule("nested-record-custody-exact-keys", _NESTED_CUSTODY_KEYS),
        _key_rule("runtime-observation-exact-keys", _RUNTIME_OBSERVATION_KEYS),
        _key_rule("resource-preflight-exact-keys", _RESOURCE_PREFLIGHT_KEYS),
        _key_rule("configuration-exact-keys", _CONFIGURATION_KEYS),
        "configuration-event-exact-keys=(event_type,coordinates_float64_be)",
        _key_rule("source-evaluation-exact-keys", _SOURCE_EVALUATION_KEYS),
        _key_rule("facade-evaluation-exact-keys", _FACADE_EVALUATION_KEYS),
        _key_rule("scored-exact-keys", _SCORED_KEYS),
        _key_rule("quota-exact-keys", _QUOTA_KEYS),
        _key_rule("attempt-exact-keys", _ATTEMPT_KEYS),
        _key_rule("particle-exact-keys", _PARTICLE_KEYS),
    )
    trace_projection_rules = (
        "returned-trace_schema=cp74-test28-production-returned-kernel-trace-candidate-v1",
        "closed-trace_schema=cp74-test28-production-closed-kernel-outcome-candidate-v1",
        "returned-terminal-digest-domain=cp74-test28-production-returned-kernel-trace-candidate-v1-NUL",
        "closed-terminal-digest-domain=cp74-test28-production-closed-kernel-outcome-candidate-v1-NUL",
        "returned-terminal-digest-formula=SHA256(cp74-test28-production-returned-kernel-trace-candidate-v1\\0||ASCII-canonical-JSON-of-exact-returned-semantic-object-with-cp74_semantic_trace_sha256-field-omitted)",
        "closed-terminal-digest-formula=SHA256(cp74-test28-production-closed-kernel-outcome-candidate-v1\\0||ASCII-canonical-JSON-of-exact-closed-semantic-object-with-cp74_closed_trace_sha256-field-omitted)",
        "terminal-semantic-digest-omission-is-an-explicit-CP62-owned-leaf-projection-exception;request-row-raw-row-and-new-CP74-wrapper-carriers-use-64-zero-substitution-instead",
        "cp62-configuration-leaf-digest-formula=SHA256(cp62-test28-configuration-v1\\0||ASCII-canonical-JSON-of-exact-configuration-object-with-cp62_configuration_sha256-field-omitted)",
        "cp62-source-evaluation-leaf-digest-formula=SHA256(cp62-test28-source-evaluation-v1\\0||ASCII-canonical-JSON-of-exact-source-evaluation-object-with-cp62_source_evaluation_sha256-field-omitted)",
        "cp62-facade-evaluation-leaf-digest-formula=SHA256(cp62-test28-facade-evaluation-v1\\0||ASCII-canonical-JSON-of-exact-facade-evaluation-object-with-cp62_facade_evaluation_sha256-field-omitted)",
        "cp62-scored-slot-leaf-digest-formula=SHA256(cp62-test28-scored-slot-v1\\0||ASCII-canonical-JSON-of-exact-scored-object-with-cp62_scored_sha256-field-omitted)",
        "cp62-quota-certificate-leaf-digest-formula=SHA256(cp62-test28-quota-certificate-v1\\0||ASCII-canonical-JSON-of-exact-quota-object-with-cp62_quota_sha256-field-omitted)",
        "cp62-rejection-attempt-leaf-digest-formula=SHA256(cp62-test28-rejection-attempt-v1\\0||ASCII-canonical-JSON-of-exact-attempt-object-with-cp62_attempt_sha256-field-omitted)",
        "cp62-SIR-particle-leaf-digest-formula=SHA256(cp62-test28-sir-particle-v1\\0||ASCII-canonical-JSON-of-exact-particle-object-with-cp62_particle_sha256-field-omitted)",
        "configuration-fixture-union=T28-M1-Q-has-at-most-1-event-and-T28-M2-Q-has-at-most-2-events;event_type-is-exactly-0-or-1;coordinate-dimensions-are-M1/type0=0,M1/type1=1,M2/type0=1,M2/type1=2;events-are-canonical-nondecreasing-(event_type,decoded-coordinate-tuple)-order",
        "deterministic-fixture-score-replay=count_penalty-is--1/4-only-for-T28-M2-Q-with-two-events-and-0/1-otherwise;exact_log_weight=count_penalty-minus-sum(coefficient*Fraction.from_float(coordinate)^2)-with-coefficients-M1/type0=(),M1/type1=(1/4),M2/type0=(1/4),M2/type1=(1/8,1/6);source-cardinality-equals-event-count;source-facade-scored-exact-values-equal;rounded-value-equals-float(exact);direct-value-replays-binary64-operations-in-frozen-order;all-zero-results-are-positive-zero",
        "nested-leaf-parent-relations=recompute-configuration-before-source-and-facade;source-evaluation-is-the-exact-facade-child;configuration-and-facade-digests-and-exact-log-weight-fields-bind-the-scored-slot;attempt.exact_delta-equals-attempt.scored.exact_log_weight;the-entire-attempt.quota-object-including-all-text-integer-boolean-and-cp62_quota_sha256-fields-equals-a-fresh-certify_arbitrary_rational_uint64_exp_quota(attempt.exact_delta)-projection-under-schema-arbitrary-rational-uint64-exp-quota-v1;accepted-equals-int(decision_word_hex,16)<int(quota.quota,10);scored-binds-each-attempt-or-particle;selected-configuration-equals-the-selected-scored-configuration",
        "returned-volatile-nested-custody-exactly-matches-each-semantic-slot-configuration-source-facade-scored-and-strategy-specific-quota-attempt-or-particle-child-digests-in-index-order;closed-arms-have-volatile_custody=null",
        "returned-common-rule=proposal-stream-initial-and-final-state-digests-present;exact-upper-bound=0;exact-lower-bound=null;fixed-budget-work-certified=true;all-four-structural-result-replay-flags-and-all-ten-production-law-quality-closure-flags=false;full-runtime-lock-recomputed=false",
        "stream-seed-derivation=SHA256(heterodiff-mixed-support-initializer-derived-stream-v2\\0||strategy-ASCII||NUL||stream-role-ASCII||NUL||outer-plan-seed-uint64-big-endian||initializer_role_sha256-raw32||residual_context_sha256-raw32||facade_certificate_sha256-raw32||sir-particle-budget\\0||budget-uint64-big-endian-for-sir-resampling-else-no-particle-budget\\0);use-first-8-digest-bytes-big-endian;xor-bit63-if-equal-to-plan-seed;proposal-uses-that-value-directly;the-strategy-specific-decision-or-resampling-candidate-is-incremented-modulo-2^64-until-distinct-from-plan-seed-and-proposal;encode-as-16-lowercase-hex",
        "bounded-rejection-rule=decision-stream-initial-and-final-digests-present;resampling-seed-state-word-uniform-ESS-maximum-weight-and-ess_warning-null;attempts-length=budget;particles-and-normalized-weights-empty;explicit-rejection-exhaustion=true;quota-required=true;selected-status-uses-first-accepted-attempt-and-exhausted-status-has-no-accepted-attempt-or-selection",
        "fixed-budget-SIR-rule=decision-seed-and-state-digests-null;resampling-seed-state-digests-word-uniform-ESS-maximum-weight-and-ess_warning-present;attempts-empty;particles-and-normalized-weights-length=budget;explicit-rejection-exhaustion=false;quota-required=false;weights-exactly-recomputed-from-particle-exact-scores-and-sum-to-one;selected-index-is-the-frozen-right-sided-selection-from-weights-and-word",
        "closed-rule=runtime_observation-null-or-exact-runtime-object;completed_kernel_trace_present=false;timeout_is_semantic_nonreturn=false;no-RNG-state-custody;outcome_kind-and-failure_code-exactly-match-the-outer-phase",
        "deterministic-CP62-to-CP74-projection-replaces-trace_schema-renames-calibration_instance_sha256-to-request_instance_sha256-renames-terminal-digest-field-and-recomputes-terminal-domain-digest",
        "all-other-CP62-semantic-field-names-and-nested-keysets-remain-exact-ancestry-without-production-authentication",
        "stable_request_sha256-equals-scheduled-seed_free_request_sha256",
        "supervisor-monotonic-runtime-process-and-stderr-custody-values-are-unauthenticated-candidate-fields",
    )
    stable_trace_projection_rules = tuple(
        (
            "corresponding-raw-source-before-stable-projection-constraint=" + rule
            if rule.startswith("returned-volatile-nested-custody-")
            or rule.startswith("supervisor-monotonic-runtime-process-")
            else rule
        )
        for rule in trace_projection_rules
    )
    rng_rules = (
        _key_rule("state-row-exact-keys", _RNG_ROW_KEYS),
        _key_rule("normalized-state-exact-keys", _RNG_STATE_KEYS),
        "present-Philox-state-has-bit_generator=Philox-counter_u64_hex-length4-key_u64_hex-length2-buffer_u64_hex-length4",
        "absent-state-uses-present=false-bit_generator=null-empty-counter-key-buffer-buffer_pos=0-has_uint32=0-uinteger_u64_hex=0000000000000000",
        "returned-rejection-requires-proposal-and-decision-streams-and-absent-resampling;returned-SIR-requires-proposal-and-resampling-and-absent-decision",
        "closed-refusal-failure-and-timeout-arms-have-no-RNG-state-hashes-in-the-exact21-semantic-and-require-explicit-absent-unobserved-state-sentinels-with-no-invented-custody",
        "reconstruct-exact-NumPy-Philox-state-dict-with-native-frozen-<u8-arrays-counter-shape4-key-shape2-buffer-shape4",
        "hash-reconstructed-state-with-domain-heterodiff-mixed-support-initializer-v2-philox-state-NUL-and-CP62-recursive-sorted-dict-type-tags",
        "compare-state-hash-to-arm-appropriate-raw-semantic-initial-or-final-stream-state-sha256",
    )
    return (
        {
            "artifact_id": "shard-requests",
            "schema": "cp74-test28-production-shard-request-jsonl-candidate-v1",
            "keys": _REQUEST_KEYS,
            "nested": (),
            "rules": (
                "exactly-1024-ASCII-canonical-JSON-records-per-final-shard-file-with-one-LF-after-each-record-including-last",
                "logical-request-ordinals-are-the-production-shard-map-contiguous-range-in-order",
                "each-record-is-an-exact-production-schedule-row-slice",
                "record-domain=cp65-test28-production-schedule-request-row-v1-NUL",
            ),
            "identity": (
                "seed_ordinal",
                "row_ordinal",
                "logical_request_ordinal",
                "request_instance_sha256",
            ),
            "sources": (
                "cp65-production-schedule",
                "cp67-schedule-materializer-development-reference",
            ),
            "cross": (
                "production-schedule-to-shard-requests",
                "production-shard-map-to-shard-requests-and-shard-index",
                "shard-requests-to-shard-raw-records",
                "shard-requests-to-shard-index",
            ),
        },
        {
            "artifact_id": "shard-raw-records",
            "schema": "cp74-test28-production-raw-record-jsonl-candidate-v1",
            "keys": _RAW_TOP_LEVEL_KEYS,
            "nested": raw_nested,
            "rules": (
                "purpose=production-candidate-only-and-no-rehearsal_id-or-repetition-field",
                "exactly-1024-ASCII-canonical-JSON-records-per-final-shard-file-with-one-LF-after-each-record-including-last",
                "four-phase-arms-and-six-closed-status-arms-are-mutually-exclusive-and-exhaustive",
                "phase-arms-exact=" + repr(_PHASE_ARMS),
                "preexecution-refusal-codes-exact=" + repr(_PREEXECUTION_REFUSAL_CODES),
                "execution-failure-codes-exact=" + repr(_EXECUTION_FAILURE_CODES),
                "returned-before-deadline-requires-failure_code=null-and-status-in-strategy-specific-returned-arms",
                "preexecution-refusal-before-deadline-requires-closed_status=preexecution-refusal-before-deadline-and-failure_code-in-exact-refusal-codes",
                "execution-failure-before-deadline-requires-closed_status=execution-failure-before-deadline-and-failure_code-in-exact-execution-failure-codes",
                "timeout-at-deadline-requires-closed_status=timeout-censored-at-deadline-and-failure_code=null",
                "kernel_trace-semantic-is-returned54-or-closed21-discriminated-by-phase",
                "returned-refusal-and-execution-failure-supervisor-rule=process_group-equals-pid;exit_code=0;term_signal=null;completion_strictly_before_deadline=true;exact_one_frame=true;termination_attempted=false;termination_signal_delivered=false;kill_attempted=false;reaped=true;terminal_monotonic_ns-strictly-less-than-deadline_monotonic_ns;child-payload-is-the-exact-CP74-raw-top-level-object-with-supervisor_custody-and-raw_sha256-omitted;frame_bytes-equals-8-plus-the-ASCII-canonical-child-payload-length;child_frame_sha256-equals-plain-SHA256(uint64-BE-payload-length||exact-child-payload-bytes)",
                "timeout-supervisor-rule=process_group-equals-pid;completion_strictly_before_deadline=false;exact_one_frame=false;reaped=true;terminal_monotonic_ns-at-least-deadline_monotonic_ns;exactly-one-of-exit_code-or-term_signal-is-present;termination-delivery-implies-attempt;SIGTERM-implies-delivery;SIGKILL-implies-kill-attempt;kill-attempt-implies-termination-attempt",
                "all-supervisor-arms-require-deadline_monotonic_ns=start_monotonic_ns+300000000000;terminal_monotonic_ns-at-least-start_monotonic_ns;stderr_hex-decoded-length-and-plain-SHA256-equalities",
                "stderr-frame-payload-bytes-exactly-equal-bytes.fromhex(supervisor_custody.stderr_hex);payload-length-equals-stderr_bytes;payload-SHA256-equals-stderr_sha256",
                "raw_sha256-is-domain-separated-canonical-child-record-digest-with-raw_sha256-zeroed",
            )
            + trace_projection_rules,
            "identity": common_identity,
            "sources": (
                "cp62-execution-capsule-development-ancestry",
                "cp63-rehearsal-projection-development-ancestry",
                "cp66-closed-classifier-development-reference",
            ),
            "cross": (
                "shard-requests-to-shard-raw-records",
                "frozen-runtime-lock-and-production-runtime-receipt-to-shard-raw-records",
                "shard-raw-records-to-shard-stable-traces",
                "shard-raw-records-to-shard-stderr-records",
                "shard-raw-records-to-shard-rng-initial-states",
                "shard-raw-records-to-shard-rng-final-states",
                "shard-raw-records-to-shard-index",
            ),
        },
        {
            "artifact_id": "shard-stable-traces",
            "schema": "cp74-test28-production-stable-trace-jsonl-candidate-v1",
            "keys": _STABLE_TOP_LEVEL_KEYS,
            "nested": (
                _key_rule("returned-semantic-exact-keys", _RETURNED_SEMANTIC_KEYS),
                _key_rule("closed-semantic-exact-keys", _CLOSED_SEMANTIC_KEYS),
            ),
            "rules": (
                "exactly-1024-ASCII-canonical-JSON-records-per-final-shard-file-with-one-LF-after-each-record-including-last",
                "exact-projection-of-corresponding-raw-record-by-replacing-top-level-schema-with-cp74-test28-production-stable-trace-jsonl-candidate-v1-removing-supervisor_custody-and-raw_sha256-and-replacing-kernel_trace-with-kernel_trace.semantic-while-preserving-every-other-field-byte-semantically",
                "no-rehearsal_id-or-repetition-field",
            )
            + stable_trace_projection_rules,
            "identity": common_identity,
            "sources": (
                "cp63-stable-projection-development-ancestry",
                "cp68-cp69-compact-projection-development-reference",
            ),
            "cross": (
                "shard-raw-records-to-shard-stable-traces",
                "shard-stable-traces-to-shard-index",
            ),
        },
        {
            "artifact_id": "shard-stderr-records",
            "schema": "cp74-test28-production-stderr-frame-stream-candidate-v1",
            "keys": (),
            "nested": (),
            "rules": (
                "binary-stream-exactly-1024-frames-per-final-shard-file-with-no-trailing-bytes",
                "each-frame=uint64-big-endian-payload-length||payload",
                "payload-length-inclusive-range-0-through-1048576-and-frame-length=8+payload-length",
                "frame-ordinal-aligns-with-logical-request-ordinal-and-payload-SHA256-equals-raw-supervisor_custody.stderr_sha256",
            ),
            "identity": ("path-shard_id-context", "logical_request_ordinal"),
            "sources": ("cp62-cp63-supervisor-stderr-custody-ancestry",),
            "cross": (
                "shard-raw-records-to-shard-stderr-records",
                "shard-stderr-records-to-shard-index",
            ),
        },
        {
            "artifact_id": "shard-rng-initial-states",
            "schema": "cp74-test28-production-rng-initial-state-container-candidate-v1",
            "keys": _RNG_CONTAINER_KEYS,
            "nested": rng_rules,
            "rules": (
                "one-ASCII-canonical-JSON-container-per-final-shard-file-with-zero-trailing-bytes",
                "ordered_state_rows-has-exactly-1024-rows-in-logical-request-order-and-state_phase=initial",
            ),
            "identity": ("attempt_id", "shard_id", "logical_request_ordinal"),
            "sources": ("cp62-kernel-Philox-state-digest-ancestry",),
            "cross": (
                "shard-raw-records-to-shard-rng-initial-states",
                "shard-rng-initial-states-to-shard-index",
            ),
        },
        {
            "artifact_id": "shard-rng-final-states",
            "schema": "cp74-test28-production-rng-final-state-container-candidate-v1",
            "keys": _RNG_CONTAINER_KEYS,
            "nested": rng_rules,
            "rules": (
                "one-ASCII-canonical-JSON-container-per-final-shard-file-with-zero-trailing-bytes",
                "ordered_state_rows-has-exactly-1024-rows-in-logical-request-order-and-state_phase=final",
            ),
            "identity": ("attempt_id", "shard_id", "logical_request_ordinal"),
            "sources": ("cp62-kernel-Philox-state-digest-ancestry",),
            "cross": (
                "shard-raw-records-to-shard-rng-final-states",
                "shard-rng-final-states-to-shard-index",
            ),
        },
    )


def _field_grammar_rule(path: str, json_type: str, constraint: str) -> str:
    if not path.startswith("/") or "|" in path or "|" in json_type or "|" in constraint:
        raise RuntimeError("CP74 field grammar token is not closed")
    return (
        "field-grammar|path="
        + path
        + "|json-type="
        + json_type
        + "|constraint="
        + constraint
    )


def _top_level_field_grammar(
    artifact_id: str, output_schema_id: str, field: str
) -> str:
    path = "/" + field
    if field in ("schema", "schema_version"):
        literal = (
            "cp63-test28-runner-recomputation-rehearsal-v1"
            if artifact_id == "shard-requests"
            else output_schema_id
        )
        return _field_grammar_rule(path, "string", "exact-literal=" + literal)
    if field == "purpose":
        return _field_grammar_rule(
            path, "string", "exact-literal=production-candidate-only"
        )
    if field == "attempt_id":
        return _field_grammar_rule(
            path,
            "string",
            "ASCII-regex=[a-z0-9][a-z0-9._-]{0,127};no-path-separator",
        )
    if field.endswith("_sha256"):
        return _field_grammar_rule(
            path, "string", "exactly-64-lowercase-hex-characters"
        )
    exact_integers = {
        "request_count": (
            1_024
            if artifact_id in ("shard-rng-initial-states", "shard-rng-final-states")
            else CP74_TEST28_REQUEST_COUNT
        ),
        "shard_count": CP74_TEST28_SHARD_COUNT,
        "estimand_count": CP74_TEST28_ESTIMAND_COUNT,
        "primary_slot_count": 32,
    }
    if field in exact_integers:
        return _field_grammar_rule(
            path, "integer-bool-forbidden", "exact=" + str(exact_integers[field])
        )
    integer_ranges = {
        "seed_ordinal": "inclusive-1-through-2048",
        "row_ordinal": "inclusive-1-through-16",
        "logical_request_ordinal": "inclusive-1-through-32768",
        "budget": "one-of=(1,4,8,16,32,64,128,512);strategy-compatible",
        "diagnostic_count": "inclusive-0-through-32768;equals-/ordered_diagnostics-length",
        "entry_count": "inclusive-0-through-32768;equals-/entries-length",
    }
    if field in integer_ranges:
        return _field_grammar_rule(
            path, "integer-bool-forbidden", integer_ranges[field]
        )
    fixed_booleans = {
        "captured_before_project_import": "exact=true",
        "raw_to_stable_projection_recomputed": "exact=true",
        "production_recomputation_performed": "exact=false-in-unobserved-candidate;requires-later-observed-production-revision-to-be-true",
        "decision_semantics_resolved": "exact=false",
    }
    if field in fixed_booleans:
        return _field_grammar_rule(path, "boolean", fixed_booleans[field])
    fixed_nulls = {
        "all_primary_thresholds_passed",
        "decision",
        "decision_made_at_utc",
    }
    if field in fixed_nulls:
        return _field_grammar_rule(
            path, "null", "exact=null-while-decision-semantics-unresolved"
        )
    array_constraints = {
        "ordered_environment_entries": "array-length=17;unique-name-sorted-order",
        "ordered_primary_slots": "array-length=32;slot-ordinal-order",
        "ordered_primary_slot_record_sha256s": "array-length=32;each-item=64-lowercase-hex;equals-child-slot_record_sha256-vector",
        "ordered_shard_receipt_sha256s": "array-length=32;each-item=64-lowercase-hex;shard-order",
        "ordered_raw_file_sha256s": "array-length=32;each-item=64-lowercase-hex;shard-order",
        "ordered_stable_file_sha256s": "array-length=32;each-item=64-lowercase-hex;shard-order",
        "ordered_diagnostics": "array-length-equals-/diagnostic_count;diagnostic-ordinal-order",
        "ordered_diagnostic_record_sha256s": "array-length-equals-/diagnostic_count;each-item=64-lowercase-hex;equals-child-diagnostic_record_sha256-vector",
        "estimand_estimate_intervals": "array-length=554;estimand-ordinal-order;exact-CP71-record-grammar",
        "ordered_slot_decisions": "array-length=32;slot-ordinal-order",
        "ordered_slot_decision_record_sha256s": "array-length=32;each-item=64-lowercase-hex;equals-child-slot_decision_record_sha256-vector",
        "entries": "array-length-equals-/entry_count;ordinal-order",
        "ordered_state_rows": "array-length=1024;logical-request-ordinal-order",
        "ordered_state_row_sha256s": "array-length=1024;each-item=64-lowercase-hex;equals-child-row_sha256-vector",
    }
    if field in array_constraints:
        return _field_grammar_rule(path, "array", array_constraints[field])
    if field == "terminal_counts":
        return _field_grammar_rule(
            path, "object", "exact-six-terminal-count-keys;integer-values-sum=32768"
        )
    if field in ("kernel_trace", "supervisor_custody"):
        return _field_grammar_rule(
            path, "object", "exact-discriminated-nested-grammar-defined-below"
        )
    text_constraints = {
        "source_interchange_schema_version": "exact-literal=cp69-test28-compact-projection-interchange-qualification-v1",
        "source_output_schema_version": "exact-literal=cp71-test28-supplied-development-estimate-interval-output-v1",
        "runtime_profile_id": "nonempty-ASCII-maximum-256-characters",
        "row_key": "exact-frozen-CP61-row-key-for-/row_ordinal",
        "fixture_id": "one-of=(T28-M1-Q,T28-M2-Q);exact-row-compatible",
        "strategy": "one-of=(bounded-rejection,fixed-budget-sir);exact-row-compatible",
        "plan_seed_hex": "exactly-16-lowercase-hex-characters",
        "phase": "one-of=" + repr(_PHASE_ARMS),
        "closed_status": "one-of=" + repr(_CLOSED_OUTCOME_ARMS),
        "failure_code": "null-or-one-of-refusal5-or-execution-failure7;phase-compatible",
        "shard_id": "ASCII-regex=shard-(0001-through-0032);path-compatible",
        "state_phase": "exact-literal="
        + ("initial" if artifact_id == "shard-rng-initial-states" else "final"),
    }
    if field in text_constraints:
        return _field_grammar_rule(
            path,
            "string-or-null" if field == "failure_code" else "string",
            text_constraints[field],
        )
    raise RuntimeError("CP74 top-level field lacks a closed grammar: " + field)


def _nested_field_grammar(path: str, field: str, *, context: str) -> str:
    if field == "quota" and context == "attempt":
        return _field_grammar_rule(
            path,
            "object",
            "exact-nested-keyset-and-field-grammar-at-this-path",
        )
    if field == "schema_version" and context == "cp71-estimand":
        return _field_grammar_rule(
            path,
            "string",
            "exact-literal=cp71-test28-supplied-development-estimate-interval-output-v1",
        )
    if field == "schema_version" and context == "quota":
        return _field_grammar_rule(
            path,
            "string",
            "exact-literal=arbitrary-rational-uint64-exp-quota-v1",
        )
    if field == "trace_schema" and context in (
        "returned-semantic",
        "closed-semantic",
    ):
        literal = (
            "cp74-test28-production-returned-kernel-trace-candidate-v1"
            if context == "returned-semantic"
            else "cp74-test28-production-closed-kernel-outcome-candidate-v1"
        )
        return _field_grammar_rule(path, "string", "exact-literal=" + literal)
    if context in ("returned-semantic", "closed-semantic") and field in (
        "stable_request_sha256",
        "request_instance_sha256",
        "source_certificate_sha256",
        "source_parameter_sha256",
        "reference_parameter_sha256",
        "facade_certificate_sha256",
        "adapter_role_sha256",
        "initializer_role_sha256",
        "residual_context_sha256",
        "runtime_lock_sha256",
    ):
        relation = {
            "stable_request_sha256": "equals-outer-seed_free_request_sha256",
            "request_instance_sha256": "equals-outer-request_instance_sha256",
            "runtime_lock_sha256": "equals-outer-runtime_lock_sha256-and-v15-machine-manifest-cp62-runtime-lock-record-SHA256",
        }.get(
            field,
            "equals-the-exact-frozen-CP61/CP62-request-binding-value-for-outer-row_ordinal",
        )
        return _field_grammar_rule(
            path,
            "string",
            "exactly-64-lowercase-hex-characters;" + relation,
        )
    if context == "runtime-observation" and field == "runtime_lock_sha256":
        return _field_grammar_rule(
            path,
            "string",
            "exactly-64-lowercase-hex-characters;equals-outer-runtime_lock_sha256-and-v15-machine-manifest-cp62-runtime-lock-record-SHA256",
        )
    if (
        field
        in (
            "decision_stream_initial_state_sha256",
            "decision_stream_final_state_sha256",
            "resampling_stream_initial_state_sha256",
            "resampling_stream_final_state_sha256",
        )
        and context == "returned-semantic"
    ):
        present_strategy = (
            "bounded-rejection"
            if field.startswith("decision_stream_")
            else "fixed-budget-sir"
        )
        return _field_grammar_rule(
            path,
            "string-or-null",
            "exactly-64-lowercase-hex-if-strategy=%s;exact=null-otherwise"
            % present_strategy,
        )
    if field == "ess_warning" and context == "returned-semantic":
        return _field_grammar_rule(
            path,
            "boolean-or-null",
            "exact=null-if-bounded-rejection;for-fixed-budget-sir-equals-effective_sample_size<(0.25*budget)",
        )
    if field == "semantic" and context == "kernel-trace":
        return _field_grammar_rule(
            path,
            "object",
            "exact-returned54-or-closed21-discriminated-by-outer-phase",
        )
    if field == "volatile_custody" and context == "kernel-trace":
        return _field_grammar_rule(
            path,
            "object-or-null",
            "exact-object-on-returned-before-deadline;exact=null-on-refusal-failure-timeout",
        )
    if field == "exact_log_weight_upper_bound" and context == "returned-semantic":
        return _field_grammar_rule(
            path,
            "canonical-fraction-object",
            "exact-reduced-fraction-zero-over-one",
        )
    if field == "exact_log_weight_lower_bound" and context == "returned-semantic":
        return _field_grammar_rule(path, "null", "exact=null")
    if field == "selected_index" and context == "returned-semantic":
        return _field_grammar_rule(
            path,
            "integer-or-null-bool-forbidden",
            "bounded-rejection-selected=first-accepted-attempt-index;bounded-rejection-exhausted=null;fixed-budget-sir=right-sided-selection-from-normalized-weights-and-resampling-word;non-null-range-0-through-budget-minus-1",
        )
    if field == "result_status" and context == "returned-semantic":
        return _field_grammar_rule(
            path,
            "string",
            "bounded-rejection-one-of=(selected,exhausted)-and-matches-outer-closed_status;fixed-budget-sir-exact=selected-and-outer-closed_status=returned-sir-selected-before-deadline",
        )
    if (
        field
        in (
            "rejection_decision_seed_hex",
            "sir_resampling_seed_hex",
            "resampling_word_hex",
        )
        and context == "returned-semantic"
    ):
        if field == "rejection_decision_seed_hex":
            constraint = "exactly-16-lowercase-hex-if-bounded-rejection;exact=null-if-fixed-budget-sir"
        else:
            constraint = "exact=null-if-bounded-rejection;exactly-16-lowercase-hex-if-fixed-budget-sir"
        return _field_grammar_rule(path, "string-or-null", constraint)
    if field == "resampling_uniform_53" and context == "returned-semantic":
        return _field_grammar_rule(
            path,
            "integer-or-null-bool-forbidden",
            "exact=null-if-bounded-rejection;fixed-budget-sir-inclusive-0-through-9007199254740991-and-equals-int(resampling_word_hex,16)>>11",
        )
    if (
        field
        in (
            "effective_sample_size_float64_be",
            "maximum_normalized_weight_float64_be",
        )
        and context == "returned-semantic"
    ):
        constraint = (
            "exact=null-if-bounded-rejection;fixed-budget-sir-finite-positive-binary64-big-endian-and-at-most-budget;equals-1/math.fsum(weight*weight)"
            if field.startswith("effective_")
            else "exact=null-if-bounded-rejection;fixed-budget-sir-finite-positive-binary64-big-endian-at-most-one;equals-max(normalized-weights)"
        )
        return _field_grammar_rule(
            path, "canonical-float64-tag-object-or-null", constraint
        )
    if field == "normalized_weight_float64_be" and context == "particle":
        return _field_grammar_rule(
            path,
            "canonical-float64-tag-object",
            "exact-object-key=$float64_be-with-16-lowercase-hex-IEEE754-binary64-big-endian;finite;strictly-positive-at-most-one;equals-corresponding-root-normalized-weight",
        )
    if field == "events" and context == "configuration":
        return _field_grammar_rule(
            path,
            "array",
            "fixture-discriminated-length:T28-M1-Q=0-through-1;T28-M2-Q=0-through-2;items-have-exact-keys=(event_type,coordinates_float64_be);strictly-nondecreasing-lexicographic-order-by-(event_type,decoded-coordinate-tuple)",
        )
    if field == "event_type" and context == "configuration-event":
        return _field_grammar_rule(
            path,
            "integer-bool-forbidden",
            "one-of=(0,1);coordinate-dimension:T28-M1-Q/type0=0,T28-M1-Q/type1=1,T28-M2-Q/type0=1,T28-M2-Q/type1=2",
        )
    if field == "coordinates_float64_be" and context == "configuration-event":
        return _field_grammar_rule(
            path,
            "array",
            "fixture-and-event-type-exact-length:T28-M1-Q/type0=0,T28-M1-Q/type1=1,T28-M2-Q/type0=1,T28-M2-Q/type1=2;each-item-exact-one-key-object-$float64_be-with-16-lowercase-hex-IEEE754-binary64-big-endian;finite;no-negative-zero",
        )
    if field == "cardinality" and context == "source-evaluation":
        return _field_grammar_rule(
            path,
            "integer-bool-forbidden",
            "equals-corresponding-configuration-/events-length;T28-M1-Q-inclusive-0-through-1;T28-M2-Q-inclusive-0-through-2",
        )
    if field == "count_penalty" and context == "source-evaluation":
        return _field_grammar_rule(
            path,
            "canonical-fraction-object",
            "exact-reduced-fraction=-1/4-only-for-T28-M2-Q-with-exactly-two-events;exact=0/1-otherwise",
        )
    if field == "exact_log_weight" and context in (
        "source-evaluation",
        "facade-evaluation",
        "scored",
    ):
        return _field_grammar_rule(
            path,
            "canonical-fraction-object",
            "same-exact-deterministic-fixture-score:count-penalty-minus-sum(coefficient*Fraction.from_float(decoded-coordinate)^2);coefficients:T28-M1-Q/type0=(),T28-M1-Q/type1=(1/4),T28-M2-Q/type0=(1/4),T28-M2-Q/type1=(1/8,1/6);source-facade-scored-values-equal",
        )
    if (
        field == "rounded_exact_log_weight_float64_be"
        and context == "source-evaluation"
    ):
        return _field_grammar_rule(
            path,
            "canonical-float64-tag-object",
            "equals-float(exact-deterministic-fixture-score)-with-negative-zero-canonicalized-to-positive-zero",
        )
    if (
        field == "direct_binary64_log_weight_float64_be"
        and context == "source-evaluation"
    ):
        return _field_grammar_rule(
            path,
            "canonical-float64-tag-object",
            "equals-direct-binary64-replay-starting-from-float(count-penalty)-and-subtracting-float(coefficient)*(coordinate*coordinate)-in-event-and-coordinate-order-with-negative-zero-canonicalized-to-positive-zero",
        )
    if field == "rounded_log_weight_float64_be" and context in (
        "facade-evaluation",
        "scored",
    ):
        return _field_grammar_rule(
            path,
            "canonical-float64-tag-object",
            "equals-corresponding-source-evaluation-/rounded_exact_log_weight_float64_be-and-float(exact-deterministic-fixture-score)-with-canonical-positive-zero",
        )
    if field == "logical_request_ordinal" and context == "deviations-entry":
        return _field_grammar_rule(
            path,
            "integer-or-null-bool-forbidden",
            "inclusive-1-through-32768-exactly-when-scope_kind=request;exact=null-for-attempt-shard-or-artifact-scope",
        )
    sha_nullable = context == "nested-custody" and field.endswith("_sha256")
    if field.endswith("_sha256"):
        return _field_grammar_rule(
            path,
            "string-or-null" if sha_nullable else "string",
            "null-or-64-lowercase-hex"
            if sha_nullable
            else "exactly-64-lowercase-hex-characters",
        )
    boolean_fields = {
        "exact_upper_bound_respected",
        "represented_restriction_identity_verified",
        "structural_validation_replayed_learned_model",
        "structural_validation_replayed_rng",
        "accepted",
        "input_lower_strict",
        "input_upper_strict",
        "exp_lower_strict",
        "exp_upper_strict",
        "terminal_rational_inequality_certified",
        "exact_divmod_input_enclosure_certified",
        "exponential_monotonicity_transfer_certified",
        "adjacent_decimal_outward_padding_certified",
        "adaptive_nested_enclosures_certified",
        "unique_scaled_floor_certified",
        "exact_scaled_floor_under_stated_contract_certified",
        "decimal_correct_rounding_contract_required",
        "decimal_implementation_formally_verified",
        "independent_transcendental_backend_verified",
        "binary_float_exp_used",
        "external_numeric_dependency_used",
        "exact_exponential_bernoulli_certified",
        "rejection_kernel_integrated",
        "runtime_portable",
        "cryptographic_authentication",
        "full_runtime_lock_recomputed",
        "fixed_budget_work_certified",
        "arbitrary_rational_quota_required",
        "explicit_rejection_exhaustion",
        "structural_result_validation_replays_provider_evaluate",
        "structural_result_validation_replays_provider_evaluate_or_source_public_validate_evaluation",
        "structural_result_validation_replays_reference_sampler",
        "structural_result_validation_replays_rng",
        "operational_reference_sampling_law_verified",
        "philox_uniformity_verified",
        "stream_independence_verified",
        "iid_proposals_verified",
        "analytic_target_equality_verified",
        "exact_operational_rejection_bernoulli_verified",
        "finite_j_sir_exact_target_verified",
        "source_or_model_quality_evidence",
        "path_or_sampler_admitted",
        "formal_test_28_closed",
        "ess_warning",
        "completed_kernel_trace_present",
        "timeout_is_semantic_nonreturn",
        "completion_strictly_before_deadline",
        "exact_one_frame",
        "termination_attempted",
        "termination_signal_delivered",
        "kill_attempted",
        "reaped",
        "decision_semantics_resolved",
        "abort_before_acquisition_start_durable",
        "identical_frozen_inputs",
        "no_same_attempt_retry",
        "present",
        "development_supplied_input_only",
        "input_provenance_authenticated",
        "arithmetic_transform_only",
    }
    if field in boolean_fields:
        exact_true_fields = {
            "exact_upper_bound_respected",
            "represented_restriction_identity_verified",
            "fixed_budget_work_certified",
            "development_supplied_input_only",
            "arithmetic_transform_only",
            "abort_before_acquisition_start_durable",
            "identical_frozen_inputs",
            "no_same_attempt_retry",
        }
        exact_false = field in {
            "structural_validation_replayed_learned_model",
            "structural_validation_replayed_rng",
            "structural_result_validation_replays_provider_evaluate",
            "structural_result_validation_replays_provider_evaluate_or_source_public_validate_evaluation",
            "structural_result_validation_replays_reference_sampler",
            "structural_result_validation_replays_rng",
            "operational_reference_sampling_law_verified",
            "philox_uniformity_verified",
            "stream_independence_verified",
            "iid_proposals_verified",
            "analytic_target_equality_verified",
            "exact_operational_rejection_bernoulli_verified",
            "finite_j_sir_exact_target_verified",
            "source_or_model_quality_evidence",
            "path_or_sampler_admitted",
            "formal_test_28_closed",
            "decision_semantics_resolved",
            "input_provenance_authenticated",
            "full_runtime_lock_recomputed",
            "completed_kernel_trace_present",
            "timeout_is_semantic_nonreturn",
        }
        relational_constraints = {
            "arbitrary_rational_quota_required": "exact=true-if-strategy=bounded-rejection;exact=false-if-fixed-budget-sir",
            "explicit_rejection_exhaustion": "exact=true-if-strategy=bounded-rejection;exact=false-if-fixed-budget-sir",
            "accepted": "exactly-int(decision_word_hex,16)<canonical-base10-integer-quota-value",
        }
        return _field_grammar_rule(
            path,
            "boolean",
            (
                relational_constraints[field]
                if field in relational_constraints
                else "exact=false"
                if exact_false
                else "exact=true"
                if field in exact_true_fields
                else "exact-JSON-boolean-with-context-relations-below"
            ),
        )
    integer_ranges = {
        "slot_ordinal": "inclusive-1-through-32",
        "diagnostic_ordinal": "inclusive-1-through-/diagnostic_count",
        "ordinal": "inclusive-1-through-/entry_count",
        "logical_request_ordinal": "inclusive-1-through-32768",
        "estimand_ordinal": "inclusive-1-through-554",
        "row_ordinal": "inclusive-1-through-16",
        "budget": "one-of=(1,4,8,16,32,64,128,512);strategy-compatible",
        "denominator_count": "inclusive-0-through-2048",
        "success_count": "null-or-inclusive-0-through-2048;family-compatible",
        "first_attempt_one_based": "null-or-inclusive-1-through-64;family-compatible",
        "event_type": "inclusive-0-through-2147483647",
        "cardinality": "inclusive-0-through-4096",
        "index": "inclusive-0-through-4096",
        "attempt_index": "inclusive-0-through-4096;equals-array-position",
        "particle_index": "inclusive-0-through-4096;equals-array-position",
        "reference_occurrence_limit": "exact=500000",
        "reference_coordinate_limit": "exact=4000000",
        "worst_case_occurrences": "inclusive-0-through-2147483648;exactly-budget*(1-if-T28-M1-Q-else-2)",
        "worst_case_coordinates": "inclusive-0-through-2147483648;exactly-budget*(1-if-T28-M1-Q-else-4)",
        "selected_index": "null-or-inclusive-0-through-budget-minus-1",
        "resampling_uniform_53": "null-or-inclusive-0-through-9007199254740991",
        "slot_index": "inclusive-0-through-4096;equals-array-position",
        "provider_runtime_identity": "inclusive-0-through-18446744073709551615",
        "reference_runtime_identity": "inclusive-0-through-18446744073709551615",
        "pid": "inclusive-1-through-9223372036854775807",
        "process_group": "inclusive-1-through-9223372036854775807",
        "exit_code": "null-or-inclusive-0-through-255",
        "term_signal": "null-or-inclusive-1-through-255",
        "frame_bytes": "inclusive-0-through-16777216",
        "stderr_bytes": "inclusive-0-through-1048576",
        "buffer_pos": "inclusive-0-through-4-if-present;exact=0-if-absent",
        "has_uint32": "one-of=(0,1)-if-present;exact=0-if-absent",
    }
    if field in integer_ranges:
        nullable = integer_ranges[field].startswith("null-or")
        return _field_grammar_rule(
            path,
            "integer-or-null-bool-forbidden" if nullable else "integer-bool-forbidden",
            integer_ranges[field],
        )
    if context == "terminal-count":
        return _field_grammar_rule(
            path,
            "integer-bool-forbidden",
            "inclusive-0-through-32768;all-six-terminal-counts-sum=32768",
        )
    decimal_integer_text = {
        "delta_numerator",
        "delta_denominator",
        "precision",
        "adaptive_rounds",
        "decision_denominator",
        "quota",
        "input_lower_numerator",
        "input_lower_denominator",
        "input_upper_numerator",
        "input_upper_denominator",
        "exp_lower_numerator",
        "exp_lower_denominator",
        "exp_upper_numerator",
        "exp_upper_denominator",
        "start_monotonic_ns",
        "deadline_monotonic_ns",
        "terminal_monotonic_ns",
    }
    if field in decimal_integer_text:
        return _field_grammar_rule(
            path,
            "string",
            "canonical-base10-integer-text;denominators-positive;monotonic-values-nonnegative;CP62-arithmetic-relations-replayed",
        )
    array_fields = {
        "source_artifact_ids": "array-length=1-through-64;items-are-exact-CP65-artifact-ids;no-duplicates",
        "source_sha256s": "array-length-equals-source_artifact_ids;items-64-lowercase-hex",
        "events": "array-length=0-through-4096;canonical-event-order",
        "coordinates_float64_be": "array-length=0-through-4096;each-item-exact-one-key-object-$float64_be-with-16-lowercase-hex-IEEE754-binary64-big-endian;finite;no-negative-zero",
        "residual_context_float64_be": "exact-empty-array",
        "attempts": "strategy-discriminated;rejection-length=budget;SIR-exact-empty",
        "particles": "strategy-discriminated;SIR-length=budget;rejection-exact-empty",
        "normalized_weights_float64_be": "strategy-discriminated;SIR-length=budget;rejection-exact-empty;each-SIR-item-exact-one-key-object-$float64_be-with-16-lowercase-hex-IEEE754-binary64-big-endian;positive-finite-no-negative-zero;sum-to-one-under-frozen-replay",
        "nested_record_custody": "array-length=0-through-4096;slot-index-order",
        "counter_u64_hex": "present-length=4;absent-empty-array;items-exact-16-lowercase-hex",
        "key_u64_hex": "present-length=2;absent-empty-array;items-exact-16-lowercase-hex",
        "buffer_u64_hex": "present-length=4;absent-empty-array;items-exact-16-lowercase-hex",
    }
    if field in array_fields:
        return _field_grammar_rule(path, "array", array_fields[field])
    object_fields = {
        "configuration",
        "facade_evaluation",
        "source_evaluation",
        "scored",
        "quota",
        "runtime_observation",
        "resource_preflight",
        "proposal_stream_state",
        "decision_stream_state",
        "resampling_stream_state",
    }
    if field in object_fields:
        nullable = field == "runtime_observation" and context == "closed-semantic"
        return _field_grammar_rule(
            path,
            "object-or-null" if nullable else "object",
            "exact-nested-keyset-and-field-grammar-at-this-path",
        )
    nullable_object_fields = {"selected_configuration"}
    if field in nullable_object_fields:
        return _field_grammar_rule(
            path,
            "object-or-null",
            "bounded-rejection-selected=exact-configuration-of-first-accepted-attempt;bounded-rejection-exhausted=null;fixed-budget-sir=exact-configuration-of-right-sided-selected-particle",
        )
    fraction_fields = {
        "estimate",
        "interval_lower",
        "interval_upper",
        "feature_lower_bound",
        "feature_upper_bound",
        "exact_feature_sum",
        "exact_log_weight_upper_bound",
        "exact_log_weight_lower_bound",
        "count_penalty",
        "exact_log_weight",
        "exact_delta",
        "threshold_value",
    }
    if field in fraction_fields:
        always_null = field == "threshold_value"
        cp62_required = context in {
            "source-evaluation",
            "facade-evaluation",
            "scored",
            "attempt",
        } and field in {
            "count_penalty",
            "exact_log_weight",
            "exact_delta",
        }
        return _field_grammar_rule(
            path,
            (
                "null"
                if always_null
                else "canonical-fraction-object"
                if cp62_required
                else "canonical-fraction-object-or-null"
            ),
            (
                "exact=null-pending-external-power-review"
                if always_null
                else "object-exact-key=$fraction;value=array-of-two-canonical-base10-integer-strings;denominator-positive;reduced;non-null-CP62-field"
                if cp62_required
                else "object-exact-key=$fraction;value=array-of-two-canonical-base10-integer-strings;denominator-positive;reduced;nullability-family-or-arm-discriminated"
            ),
        )
    float_tag_fields = {
        "rounded_exact_log_weight_float64_be",
        "direct_binary64_log_weight_float64_be",
        "rounded_log_weight_float64_be",
        "normalized_weight_float64_be",
        "effective_sample_size_float64_be",
        "maximum_normalized_weight_float64_be",
    }
    if field in float_tag_fields:
        return _field_grammar_rule(
            path,
            "canonical-float64-tag-object-or-null",
            "null-or-exact-one-key-object-$float64_be-with-16-lowercase-hex-IEEE754-binary64-big-endian;finite;no-negative-zero;arm-compatible",
        )
    exact_null_fields = {
        "exact_lower_bound_respected",
        "decision",
    }
    if field in exact_null_fields:
        return _field_grammar_rule(path, "null", "exact=null")
    hex16_nullable = {
        "proposal_seed_hex": False,
        "rejection_decision_seed_hex": True,
        "sir_resampling_seed_hex": True,
        "resampling_word_hex": True,
        "decision_word_hex": False,
        "uinteger_u64_hex": False,
    }
    if field in hex16_nullable:
        return _field_grammar_rule(
            path,
            "string-or-null" if hex16_nullable[field] else "string",
            "exactly-16-lowercase-hex-or-null;strategy-and-arm-compatible"
            if hex16_nullable[field]
            else "exactly-16-lowercase-hex",
        )
    if field == "value_text":
        return _field_grammar_rule(
            path,
            "string",
            (
                "exact-value-associated-with-environment-name-in-frozen-17-entry-allowlist"
                if context == "environment-entry"
                else "canonical-ASCII-value-encoding-selected-by-value_kind;maximum-4096-characters"
            ),
        )
    text_domains = {
        "name": "one-of-exact-17-sanitized-environment-names;sorted-unique",
        "slot_id": "exact=cp65-power-primary-slot-%02d-for-slot_ordinal",
        "estimand_id": "exact-CP61-estimand-id-for-estimand_ordinal-or-selected-primary-slot",
        "gate_id": "exact=cp65-power-primary-slot-%02d-for-slot_ordinal",
        "diagnostic_id": "ASCII-regex=cp74-candidate-diagnostic-[a-z0-9-]{1,96}",
        "value_kind": "one-of=(integer,boolean,canonical-fraction,canonical-float64-be,text,sha256)",
        "scope_kind": "one-of=(attempt,shard,request,artifact)",
        "code": "nonempty-ASCII-token-maximum-128",
        "stage": "one-of=" + repr(_PUBLICATION_STAGE_IDS),
        "source_artifact_id": "one-of-exact-64-CP65-artifact-ids",
        "disposition": "one-of=(recorded,invalidates-attempt,requires-independent-review)",
        "shard_id": "ASCII-regex=shard-(0001-through-0032)",
        "phase": "one-of=" + repr(_PHASE_ARMS),
        "closed_status": "one-of=" + repr(_CLOSED_OUTCOME_ARMS),
        "failure_code": "null-or-one-of-refusal5-or-execution-failure7;phase-compatible",
        "reason_code": "nonempty-ASCII-token-maximum-128",
        "estimand_population_effect": "one-of=(none,invalidates-attempt);PASS-or-FAIL-requires-none-and-no-entry",
        "prior_attempt_id": "ASCII-attempt-id-distinct-from-new_attempt_id",
        "new_attempt_id": "ASCII-attempt-id-distinct-from-prior_attempt_id",
        "schema_version": "exact-inherited-schema-literal-for-context",
        "trace_schema": "exact-CP74-returned-or-closed-candidate-trace-literal-for-discriminator",
        "stable_request_sha256": "exactly-64-lowercase-hex;equals-seed_free_request_sha256",
        "request_instance_sha256": "exactly-64-lowercase-hex;equals-outer-request-instance",
        "plan_seed_hex": "exactly-16-lowercase-hex;equals-outer-plan-seed",
        "fixture_id": "one-of=(T28-M1-Q,T28-M2-Q);outer-compatible",
        "strategy": "one-of=(bounded-rejection,fixed-budget-sir);outer-compatible",
        "result_status": "one-of=(selected,exhausted);strategy-compatible",
        "estimand_family": "one-of=(observable-cell,rejection-first-attempt,selected-conditional-feature)",
        "observable_cell_label": "null-or-exact-frozen-observable-cell-label;family-compatible",
        "feature_id": "null-or-exact-frozen-CP61-feature-id;family-compatible",
        "denominator_mode": "exact-family-specific-denominator-mode-literal",
        "interval_method": "exact-family-specific-CP71-method-literal",
        "interval_state": "one-of=(computed,insufficient-selection);family-and-count-compatible",
        "outcome_kind": "one-of=(preexecution-refusal,execution-failure,timeout-censored)",
        "runtime_profile_id": "nonempty-ASCII-maximum-256",
        "mode": "exact-literal=stochastic-worst-case",
        "backend_kind": "exact-literal=exact-rational-quadratic-initial-tilt-v1",
        "certificate_scope": "nonempty-ASCII-maximum-4096",
        "proof_policy": "nonempty-ASCII-maximum-4096",
        "proof_contract": "nonempty-ASCII-maximum-4096",
        "branch": "nonempty-ASCII-maximum-4096",
        "slot_kind": "one-of=(rejection-attempt,sir-particle)",
        "stderr_hex": "lowercase-even-length-hex;decoded-byte-length-equals-stderr_bytes;maximum-1048576-bytes",
        "bit_generator": "exact-literal=Philox-if-present;exact=null-if-absent",
    }
    if context == "failures-entry" and field == "phase":
        return _field_grammar_rule(
            path,
            "string",
            "one-of=(preexecution-refusal-before-deadline,execution-failure-before-deadline,timeout-at-deadline)",
        )
    if context == "failures-entry" and field == "closed_status":
        return _field_grammar_rule(
            path,
            "string",
            "equals-phase-for-refusal-or-execution-failure;exact=timeout-censored-at-deadline-for-timeout",
        )
    if context == "failures-entry" and field == "failure_code":
        return _field_grammar_rule(
            path,
            "string-or-null",
            "exact-refusal5-for-refusal;exact-execution-failure7-for-execution-failure;exact=null-for-timeout",
        )
    if context == "closed-semantic" and field == "outcome_kind":
        return _field_grammar_rule(
            path,
            "string",
            "one-of=(preexecution-refusal,execution-failure,timeout-censored);equals-outer-phase-arm",
        )
    if context == "closed-semantic" and field == "failure_code":
        return _field_grammar_rule(
            path,
            "string-or-null",
            "exact-refusal5-for-preexecution-refusal;exact-execution-failure7-for-execution-failure;exact=null-for-timeout-censored",
        )
    if field in text_domains:
        nullable = field in (
            "failure_code",
            "bit_generator",
            "observable_cell_label",
            "feature_id",
        )
        return _field_grammar_rule(
            path,
            "string-or-null" if nullable else "string",
            text_domains[field],
        )
    if field in {
        "python_version",
        "python_implementation",
        "python_soabi",
        "platform_system",
        "platform_release",
        "machine",
        "byteorder",
        "floating_rounding_mode",
        "numpy_version",
        "scipy_version",
        "threadpoolctl_version",
        "decimal_module_version",
        "libmpdec_version",
        "schema_version",
    }:
        return _field_grammar_rule(
            path,
            "string",
            "nonempty-ASCII-maximum-4096;context-literal-or-runtime-snapshot",
        )
    raise RuntimeError(
        "CP74 nested field lacks a closed grammar: " + context + ":" + field
    )


def _nested_grammar_group(
    prefix: str, keys: Tuple[str, ...], context: str
) -> Tuple[str, ...]:
    return tuple(
        _nested_field_grammar(prefix + "/" + field, field, context=context)
        for field in keys
    )


_EXPECTED_OUTPUT_FIELD_GRAMMAR_RULE_COUNTS = {
    "environment": 23,
    "primary-metrics": 23,
    "secondary-diagnostics": 27,
    "postexecution-independent-recomputation": 46,
    "decisions": 22,
    "deviations": 17,
    "failures": 16,
    "exclusions": 15,
    "reruns": 16,
    "shard-requests": 14,
    "shard-raw-records": 296,
    "shard-stable-traces": 259,
    "shard-stderr-records": 2,
    "shard-rng-initial-states": 40,
    "shard-rng-final-states": 40,
}


def _output_field_grammar_rules(spec: Mapping[str, object]) -> Tuple[str, ...]:
    artifact_id = cast(str, spec["artifact_id"])
    output_schema_id = cast(str, spec["schema"])
    keys = cast(Tuple[str, ...], spec["keys"])
    rules = [
        _top_level_field_grammar(artifact_id, output_schema_id, field) for field in keys
    ]
    if artifact_id == "environment":
        rules.extend(
            _nested_grammar_group(
                "/ordered_environment_entries/*",
                ("name", "value_text", "entry_sha256"),
                "environment-entry",
            )
        )
    elif artifact_id == "primary-metrics":
        rules.extend(
            _nested_grammar_group(
                "/ordered_primary_slots/*",
                (
                    "slot_ordinal",
                    "slot_id",
                    "estimand_id",
                    "estimand_record_sha256",
                    "estimate",
                    "interval_lower",
                    "interval_upper",
                    "gate_id",
                    "threshold_value",
                    "threshold_row_sha256",
                    "slot_record_sha256",
                ),
                "primary-slot",
            )
        )
    elif artifact_id == "secondary-diagnostics":
        rules.extend(
            _nested_grammar_group(
                "/terminal_counts",
                (
                    "returned_rejection_selected_before_deadline",
                    "returned_rejection_exhausted_before_deadline",
                    "returned_sir_selected_before_deadline",
                    "preexecution_refusal_before_deadline",
                    "execution_failure_before_deadline",
                    "timeout_censored_at_deadline",
                ),
                "terminal-count",
            )
        )
        rules.extend(
            _nested_grammar_group(
                "/ordered_diagnostics/*",
                (
                    "diagnostic_ordinal",
                    "diagnostic_id",
                    "value_kind",
                    "value_text",
                    "source_artifact_ids",
                    "source_sha256s",
                    "diagnostic_record_sha256",
                ),
                "diagnostic",
            )
        )
    elif artifact_id == "postexecution-independent-recomputation":
        rules.extend(
            _nested_grammar_group(
                "/estimand_estimate_intervals/*",
                _CP71_ESTIMAND_KEYS,
                "cp71-estimand",
            )
        )
    elif artifact_id == "decisions":
        rules.extend(
            _nested_grammar_group(
                "/ordered_slot_decisions/*",
                (
                    "slot_ordinal",
                    "slot_id",
                    "primary_metric_record_sha256",
                    "threshold_row_sha256",
                    "decision_semantics_resolved",
                    "decision",
                    "slot_decision_record_sha256",
                ),
                "slot-decision",
            )
        )
    elif artifact_id in ("deviations", "failures", "exclusions", "reruns"):
        entry_keys = {
            "deviations": (
                "ordinal",
                "scope_kind",
                "logical_request_ordinal",
                "code",
                "stage",
                "description_sha256",
                "source_artifact_id",
                "source_record_sha256",
                "disposition",
                "entry_sha256",
            ),
            "failures": (
                "ordinal",
                "logical_request_ordinal",
                "shard_id",
                "phase",
                "closed_status",
                "failure_code",
                "raw_record_sha256",
                "stable_trace_sha256",
                "entry_sha256",
            ),
            "exclusions": (
                "ordinal",
                "logical_request_ordinal",
                "reason_code",
                "source_artifact_id",
                "source_record_sha256",
                "estimand_population_effect",
                "disposition",
                "entry_sha256",
            ),
            "reruns": (
                "ordinal",
                "prior_attempt_id",
                "new_attempt_id",
                "independent_adjudication_sha256",
                "frozen_inputs_sha256",
                "abort_before_acquisition_start_durable",
                "identical_frozen_inputs",
                "no_same_attempt_retry",
                "entry_sha256",
            ),
        }[artifact_id]
        rules.extend(
            _nested_grammar_group("/entries/*", entry_keys, artifact_id + "-entry")
        )
    elif artifact_id in ("shard-raw-records", "shard-stable-traces"):
        semantic_prefix = (
            "/kernel_trace/semantic"
            if artifact_id == "shard-raw-records"
            else "/kernel_trace"
        )
        if artifact_id == "shard-raw-records":
            rules.extend(
                _nested_grammar_group(
                    "/kernel_trace", _KERNEL_TRACE_KEYS, "kernel-trace"
                )
            )
        returned_prefix = semantic_prefix + "@returned"
        closed_prefix = semantic_prefix + "@closed"
        rules.extend(
            _nested_grammar_group(
                returned_prefix, _RETURNED_SEMANTIC_KEYS, "returned-semantic"
            )
        )
        rules.extend(
            _nested_grammar_group(
                closed_prefix, _CLOSED_SEMANTIC_KEYS, "closed-semantic"
            )
        )
        for prefix, context in (
            (returned_prefix + "/runtime_observation", "runtime-observation"),
            (closed_prefix + "/runtime_observation", "runtime-observation"),
        ):
            rules.extend(
                _nested_grammar_group(prefix, _RUNTIME_OBSERVATION_KEYS, context)
            )
        rules.extend(
            _nested_grammar_group(
                returned_prefix + "/resource_preflight",
                _RESOURCE_PREFLIGHT_KEYS,
                "resource-preflight",
            )
        )
        for collection, item_keys, item_context in (
            ("attempts", _ATTEMPT_KEYS, "attempt"),
            ("particles", _PARTICLE_KEYS, "particle"),
        ):
            item_prefix = returned_prefix + "/" + collection + "/*"
            rules.extend(_nested_grammar_group(item_prefix, item_keys, item_context))
            scored_prefix = item_prefix + "/scored"
            rules.extend(_nested_grammar_group(scored_prefix, _SCORED_KEYS, "scored"))
            configuration_prefix = scored_prefix + "/configuration"
            rules.extend(
                _nested_grammar_group(
                    configuration_prefix, _CONFIGURATION_KEYS, "configuration"
                )
            )
            rules.extend(
                _nested_grammar_group(
                    configuration_prefix + "/events/*",
                    ("event_type", "coordinates_float64_be"),
                    "configuration-event",
                )
            )
            facade_prefix = scored_prefix + "/facade_evaluation"
            rules.extend(
                _nested_grammar_group(
                    facade_prefix, _FACADE_EVALUATION_KEYS, "facade-evaluation"
                )
            )
            rules.extend(
                _nested_grammar_group(
                    facade_prefix + "/source_evaluation",
                    _SOURCE_EVALUATION_KEYS,
                    "source-evaluation",
                )
            )
            if collection == "attempts":
                rules.extend(
                    _nested_grammar_group(item_prefix + "/quota", _QUOTA_KEYS, "quota")
                )
        rules.extend(
            _nested_grammar_group(
                returned_prefix + "/selected_configuration",
                _CONFIGURATION_KEYS,
                "configuration",
            )
        )
        rules.extend(
            _nested_grammar_group(
                returned_prefix + "/selected_configuration/events/*",
                ("event_type", "coordinates_float64_be"),
                "configuration-event",
            )
        )
        if artifact_id == "shard-raw-records":
            rules.extend(
                _nested_grammar_group(
                    "/kernel_trace/volatile_custody",
                    _VOLATILE_CUSTODY_KEYS,
                    "volatile-custody",
                )
            )
            rules.extend(
                _nested_grammar_group(
                    "/kernel_trace/volatile_custody/nested_record_custody/*",
                    _NESTED_CUSTODY_KEYS,
                    "nested-custody",
                )
            )
            rules.extend(
                _nested_grammar_group(
                    "/supervisor_custody",
                    _SUPERVISOR_CUSTODY_KEYS,
                    "supervisor-custody",
                )
            )
    elif artifact_id in (
        "shard-rng-initial-states",
        "shard-rng-final-states",
    ):
        rules.extend(
            _nested_grammar_group(
                "/ordered_state_rows/*", _RNG_ROW_KEYS, "rng-state-row"
            )
        )
        for stream_field in (
            "proposal_stream_state",
            "decision_stream_state",
            "resampling_stream_state",
        ):
            rules.extend(
                _nested_grammar_group(
                    "/ordered_state_rows/*/" + stream_field,
                    _RNG_STATE_KEYS,
                    "rng-state",
                )
            )
    elif artifact_id == "shard-stderr-records":
        rules.extend(
            (
                _field_grammar_rule(
                    "/frames/*/length_prefix",
                    "8-byte-binary-unsigned-big-endian",
                    "inclusive-0-through-1048576;equals-payload-byte-length",
                ),
                _field_grammar_rule(
                    "/frames/*/payload",
                    "byte-string",
                    "byte-length-from-prefix;plain-SHA256-bound-to-same-ordinal-index-and-raw-stderr-custody",
                ),
            )
        )
    paths = tuple(rule.split("|", 2)[1][5:] for rule in rules)
    if len(paths) != len(set(paths)):
        raise RuntimeError("CP74 output field grammar path is duplicated")
    if {"/" + field for field in keys} - set(paths):
        raise RuntimeError("CP74 output top-level field grammar is incomplete")
    if len(rules) != _EXPECTED_OUTPUT_FIELD_GRAMMAR_RULE_COUNTS[artifact_id]:
        raise RuntimeError("CP74 output field grammar cardinality differs")
    grammar_by_path = dict(zip(paths, rules))
    if artifact_id == "environment" and (
        "exact-value-associated-with-environment-name-in-frozen-17-entry-allowlist"
        not in grammar_by_path["/ordered_environment_entries/*/value_text"]
    ):
        raise RuntimeError("CP74 environment value grammar context differs")
    if artifact_id == "secondary-diagnostics" and (
        "canonical-ASCII-value-encoding-selected-by-value_kind"
        not in grammar_by_path["/ordered_diagnostics/*/value_text"]
    ):
        raise RuntimeError("CP74 diagnostic value grammar context differs")
    if artifact_id in ("shard-raw-records", "shard-stable-traces"):
        for semantic_arm in ("@returned",):
            base = (
                "/kernel_trace/semantic"
                if artifact_id == "shard-raw-records"
                else "/kernel_trace"
            ) + semantic_arm
            if "json-type=object" not in grammar_by_path[base + "/attempts/*/quota"]:
                raise RuntimeError("CP74 attempt quota object grammar differs")
            if (
                "json-type=string"
                not in grammar_by_path[base + "/attempts/*/quota/quota"]
            ):
                raise RuntimeError("CP74 nested quota integer-text grammar differs")
            if (
                "json-type=boolean-or-null"
                not in grammar_by_path[base + "/ess_warning"]
            ):
                raise RuntimeError("CP74 ESS-warning strategy grammar differs")
    if artifact_id in (
        "shard-rng-initial-states",
        "shard-rng-final-states",
    ):
        if "exact=1024" not in grammar_by_path["/request_count"] or (
            "inclusive-0-through-4-if-present"
            not in grammar_by_path[
                "/ordered_state_rows/*/proposal_stream_state/buffer_pos"
            ]
        ):
            raise RuntimeError("CP74 RNG per-shard grammar differs")
    return tuple(rules)


def _build_execution_output_semantic_rules(
    occurrence_rules: Tuple[CP74ArtifactOccurrenceRuleV1, ...]
) -> Tuple[CP74ExecutionOutputSemanticRuleV1, ...]:
    occurrence = {row.artifact_id: row for row in occurrence_rules}
    result = []
    for ordinal, spec in enumerate(_output_specifications(), 1):
        artifact_id = cast(str, spec["artifact_id"])
        source = occurrence[artifact_id]
        per_shard = artifact_id.startswith("shard-")
        if per_shard:
            instances = CP74_TEST28_SHARD_COUNT
            units = 1_024
            total_units = CP74_TEST28_REQUEST_COUNT
            encoding = (
                "binary-uint64-big-endian-length-prefixed-frames"
                if artifact_id == "shard-stderr-records"
                else "ASCII-canonical-JSON"
            )
            framing = (
                "1024-uint64-big-endian-length-prefixed-payload-frames"
                if artifact_id == "shard-stderr-records"
                else (
                    "1024-canonical-JSON-records-each-followed-by-one-LF"
                    if artifact_id
                    in ("shard-requests", "shard-raw-records", "shard-stable-traces")
                    else "one-canonical-JSON-container-with-1024-ordered-state-rows"
                )
            )
            terminator = (
                "one-LF-after-every-record-including-last"
                if artifact_id
                in ("shard-requests", "shard-raw-records", "shard-stable-traces")
                else "zero-trailing-bytes"
            )
            ordering = "shard-ordinal-1-through-32;within-shard-contiguous-1024-logical-request-ordinals-in-increasing-order;abnormal-started-branches-admit-only-whole-finalized-shard-files-in-a-dependency-closed-prefix-and-never-transient-partial-files"
        else:
            instances = 1
            units = 1
            total_units = 1
            encoding = "ASCII-canonical-JSON"
            framing = "one-canonical-JSON-document"
            terminator = "zero-trailing-bytes"
            ordering = "single-global-instance"
        record_domain, ordered_domain, body_domain = _output_digest_domains(artifact_id)
        cross_binding_ids = tuple(spec["cross"])
        if per_shard:
            cross_binding_ids += (
                "production-shard-map-and-shard-index-and-shard-files-to-shard-receipt",
            )
        cross_binding_ids += (
            "referenced-outputs-to-preterminal-inventory-and-sha256-manifest",
        )
        cross_binding_ids = tuple(dict.fromkeys(cross_binding_ids))
        result.append(
            cast(
                CP74ExecutionOutputSemanticRuleV1,
                _record(
                    CP74ExecutionOutputSemanticRuleV1,
                    {
                        "schema_version": CP74_TEST28_SCHEMA_VERSION,
                        "output_ordinal": ordinal,
                        "artifact_id": artifact_id,
                        "cp65_artifact_schema_record_sha256": source.cp65_artifact_schema_record_sha256,
                        "path_template": source.path_template,
                        "path_scope": source.path_scope,
                        "media_kind": source.media_kind,
                        "output_schema_id": spec["schema"],
                        "canonical_encoding": encoding,
                        "framing_rule": framing,
                        "final_terminator_rule": terminator,
                        "complete_attempt_instance_count": instances,
                        "complete_attempt_units_per_instance": units,
                        "complete_attempt_total_unit_count": total_units,
                        "ordering_rule": ordering,
                        "exact_top_level_keys": spec["keys"],
                        "nested_schema_rules": spec["nested"],
                        "field_semantic_rules": spec["rules"]
                        + _output_field_grammar_rules(spec)
                        + _output_digest_preimage_rules(artifact_id)
                        + (
                            "complete-attempt-all-15-output-families-total-final-artifact-instances=201",
                            "complete-attempt-all-15-output-families-total-framed-units-or-rows=196617",
                            "aggregate-logical-byte-maxima-definition-only:globals=1744830464;all-six-per-shard-families=869731237888;total=871476068352;not-a-simultaneous-allocation-claim",
                            "production-values-absent-and-no-production-body-was-accepted-or-observed",
                        ),
                        "record_identity_fields": spec["identity"],
                        "closed_outcome_arms": (
                            _CLOSED_OUTCOME_ARMS
                            if artifact_id
                            in ("shard-raw-records", "shard-stable-traces")
                            else ()
                        ),
                        "record_digest_domain": record_domain,
                        "ordered_record_digest_domain": ordered_domain,
                        "body_digest_domain": body_domain,
                        "source_contract_ids": spec["sources"],
                        "cross_binding_rule_ids": cross_binding_ids,
                        "production_values_present": False,
                        "candidate_only": True,
                    },
                ),
            )
        )
    if tuple(row.artifact_id for row in result) != _REFERENCED_OUTPUT_ARTIFACT_IDS:
        raise RuntimeError("CP74 output semantic inventory differs")
    if sum(row.complete_attempt_instance_count for row in result) != 201:
        raise RuntimeError("CP74 complete output instance count differs")
    if sum(row.complete_attempt_total_unit_count for row in result) != 196_617:
        raise RuntimeError("CP74 complete output unit count differs")
    domains = tuple(
        domain
        for row in result
        for domain in (
            row.record_digest_domain,
            row.ordered_record_digest_domain,
            row.body_digest_domain,
        )
    )
    candidate_domains = tuple(
        domain for domain in domains if domain.startswith("cp74-")
    )
    if len(set(candidate_domains)) != len(candidate_domains) or any(
        "candidate" not in domain or not domain.endswith("\0")
        for domain in candidate_domains
    ):
        raise RuntimeError("CP74 candidate output digest domains differ")
    return tuple(result)


def _output_digest_domains(artifact_id: str) -> Tuple[str, str, str]:
    if artifact_id == "shard-requests":
        return (
            "cp65-test28-production-schedule-request-row-v1\0",
            "cp74-test28-production-shard-request-candidate-ordered-record-digests-v1\0",
            "plain-sha256-of-exact-file-bytes",
        )
    if artifact_id == "shard-raw-records":
        return (
            "cp74-test28-production-raw-record-candidate-v1\0",
            "cp74-test28-production-shard-raw-candidate-ordered-record-digests-v1\0",
            "plain-sha256-of-exact-file-bytes",
        )
    if artifact_id == "shard-stable-traces":
        return (
            "plain-sha256-of-exact-canonical-stable-record-bytes-before-LF",
            "cp74-test28-production-shard-stable-candidate-ordered-record-digests-v1\0",
            "plain-sha256-of-exact-file-bytes",
        )
    if artifact_id == "shard-stderr-records":
        return (
            "plain-sha256-of-frame-payload-bytes",
            "not-applicable-framed-binary-stream",
            "plain-sha256-of-exact-file-bytes",
        )
    if artifact_id == "postexecution-independent-recomputation":
        return (
            "cp71-test28-supplied-estimand-estimate-interval-v1\0",
            "cp71-test28-ordered-estimand-record-digests-v1\0",
            "cp74-test28-production-independent-recomputation-candidate-body-v1\0",
        )
    nested_stems = {
        "environment": "environment-entry",
        "primary-metrics": "primary-slot",
        "secondary-diagnostics": "diagnostic",
        "decisions": "slot-decision",
        "deviations": "deviation-entry",
        "failures": "failure-entry",
        "exclusions": "exclusion-entry",
        "reruns": "rerun-entry",
        "shard-rng-initial-states": "rng-initial-state-row",
        "shard-rng-final-states": "rng-final-state-row",
    }
    stem = nested_stems[artifact_id]
    body_stem = (
        artifact_id[len("shard-") :]
        if artifact_id.startswith("shard-")
        else artifact_id
    )
    return (
        "cp74-test28-production-%s-candidate-record-v1\0" % stem,
        "cp74-test28-production-%s-candidate-ordered-record-digests-v1\0" % stem,
        "cp74-test28-production-%s-candidate-body-v1\0" % body_stem,
    )


def _output_digest_preimage_rules(artifact_id: str) -> Tuple[str, ...]:
    record_domain, ordered_domain, body_domain = _output_digest_domains(artifact_id)
    if artifact_id == "shard-requests":
        return (
            "digest-formula=request-row-self;carrier=/request_row_sha256;preimage=ASCII-canonical-JSON-exact-row-with-request_row_sha256-set-to-64-lowercase-zero-hex-characters;domain=cp65-test28-production-schedule-request-row-v1\\0;digest=lowercase-hex-SHA256(domain-bytes||preimage-bytes)",
            "digest-formula=request-shard-ordered-derived;carrier=not-stored-derived-candidate-value;preimage=domain-bytes||concatenation-in-logical-order-of-1024-raw-32-byte-request_row_sha256-values;domain=cp74-test28-production-shard-request-candidate-ordered-record-digests-v1\\0",
            "digest-formula=request-payload-and-file;carrier=shard-index-/ordered_request_entries/*/request_sha256-and-shard-receipt-request-file-SHA256;record-payload=exact-canonical-row-bytes-before-LF;record-digest=plain-SHA256(record-payload);file-digest=plain-SHA256(exact-1024-row-JSONL-file-bytes)",
        )
    if artifact_id == "shard-raw-records":
        return (
            "digest-formula=raw-row-self;carrier=/raw_sha256;preimage=ASCII-canonical-JSON-exact-row-with-raw_sha256-set-to-64-lowercase-zero-hex-characters;domain=cp74-test28-production-raw-record-candidate-v1\\0;digest=lowercase-hex-SHA256(domain-bytes||preimage-bytes)",
            "digest-formula=raw-shard-ordered-derived;carrier=not-stored-derived-candidate-value;preimage=domain-bytes||concatenation-in-logical-order-of-1024-raw-32-byte-raw_sha256-values;domain=cp74-test28-production-shard-raw-candidate-ordered-record-digests-v1\\0",
            "digest-formula=raw-file;carrier=shard-index-/raw_file_sha256-and-shard-receipt-raw-file-SHA256;preimage=exact-1024-row-JSONL-file-bytes;domain=none;digest=plain-SHA256(preimage)",
        )
    if artifact_id == "shard-stable-traces":
        return (
            "digest-formula=stable-record-plain;carrier=shard-index-/ordered_request_entries/*/stable_sha256;preimage=exact-ASCII-canonical-JSON-stable-record-bytes-before-LF;domain=none;digest=plain-SHA256(preimage);no-stable-self-digest-field-exists",
            "digest-formula=stable-shard-ordered-derived;carrier=not-stored-derived-candidate-value;preimage=domain-bytes||concatenation-in-logical-order-of-1024-raw-32-byte-plain-stable-record-digests;domain=cp74-test28-production-shard-stable-candidate-ordered-record-digests-v1\\0",
            "digest-formula=stable-file;carrier=shard-index-/stable_file_sha256-and-shard-receipt-stable-file-SHA256;preimage=exact-1024-row-JSONL-file-bytes;domain=none;digest=plain-SHA256(preimage)",
        )
    if artifact_id == "shard-stderr-records":
        return (
            "digest-formula=stderr-frame-payload;carrier=shard-index-/ordered_request_entries/*/stderr_sha256;preimage=payload-bytes-after-8-byte-big-endian-length-prefix;domain=none;digest=plain-SHA256(preimage)",
            "digest-formula=stderr-file;carrier=shard-index-/stderr_file_sha256-and-shard-receipt-stderr-file-SHA256;preimage=exact-concatenation-of-1024-length-prefix-plus-payload-frames-with-no-trailing-byte;domain=none;digest=plain-SHA256(preimage)",
            "ordered-record-digest=not-applicable-binary-frame-stream",
        )
    carriers = {
        "environment": (
            "/ordered_environment_entries/*/entry_sha256",
            "/ordered_environment_entries_sha256",
            "/body_sha256",
        ),
        "primary-metrics": (
            "/ordered_primary_slots/*/slot_record_sha256",
            "/ordered_primary_slots_sha256",
            "/body_sha256",
        ),
        "secondary-diagnostics": (
            "/ordered_diagnostics/*/diagnostic_record_sha256",
            "/ordered_diagnostics_sha256",
            "/body_sha256",
        ),
        "postexecution-independent-recomputation": (
            "/estimand_estimate_intervals/*/record_sha256",
            "/ordered_estimand_record_sha256s_sha256",
            "/body_sha256",
        ),
        "decisions": (
            "/ordered_slot_decisions/*/slot_decision_record_sha256",
            "/ordered_slot_decisions_sha256",
            "/body_sha256",
        ),
        "deviations": (
            "/entries/*/entry_sha256",
            "/ordered_entries_sha256",
            "/body_sha256",
        ),
        "failures": (
            "/entries/*/entry_sha256",
            "/ordered_entries_sha256",
            "/body_sha256",
        ),
        "exclusions": (
            "/entries/*/entry_sha256",
            "/ordered_entries_sha256",
            "/body_sha256",
        ),
        "reruns": (
            "/entries/*/entry_sha256",
            "/ordered_entries_sha256",
            "/body_sha256",
        ),
        "shard-rng-initial-states": (
            "/ordered_state_rows/*/row_sha256",
            "/ordered_states_sha256",
            "/body_sha256",
        ),
        "shard-rng-final-states": (
            "/ordered_state_rows/*/row_sha256",
            "/ordered_states_sha256",
            "/body_sha256",
        ),
    }
    record_carrier, ordered_carrier, body_carrier = carriers[artifact_id]
    explicit_digest_vectors = {
        "primary-metrics": "/ordered_primary_slot_record_sha256s",
        "secondary-diagnostics": "/ordered_diagnostic_record_sha256s",
        "decisions": "/ordered_slot_decision_record_sha256s",
        "shard-rng-initial-states": "/ordered_state_row_sha256s",
        "shard-rng-final-states": "/ordered_state_row_sha256s",
    }
    explicit_vector_rule = (
        ";explicit-vector=%s-must-equal-the-child-carrier-values-in-the-same-frozen-order-and-cardinality-before-the-ordered-digest-is-computed"
        % explicit_digest_vectors[artifact_id]
        if artifact_id in explicit_digest_vectors
        else ";explicit-vector=not-present-the-frozen-child-carrier-order-is-the-ordered-digest-input"
    )
    nested_exception = (
        "embedded-CP71-output-body-digest-reference=/output_body_sha256;preimage=cp71-test28-supplied-interchange-estimate-interval-output-body-v1\\0||exact-canonical-CP71-output-bytes-which-have-no-output_body_sha256-carrier-field;embedded-/cp71_output_canonical_json_sha256=plain-SHA256(the-identical-exact-canonical-CP71-output-bytes-used-by-/output_body_sha256);embedded-CP71-estimand-record-carrier-is-record_sha256-set-to-64-zero-hex;CP72-public-summary-formula=SHA256(cp72-public-record-v1\\0||CP72SuppliedDevelopmentOutputValidationSummaryV1\\0||exact-canonical-summary-bytes);CP73-public-summary-formula=SHA256(cp73-public-record-v1\\0||CP73SuppliedStreamOutputRelationSummaryV1\\0||exact-canonical-summary-bytes);both-are-development-only-structural-references"
        if artifact_id == "postexecution-independent-recomputation"
        else "no-additional-nested-digest-exception"
    )
    return (
        "digest-formula=nested-record;carrier=%s;preimage=ASCII-canonical-JSON-of-exact-nested-object-with-carrier-set-to-64-lowercase-zero-hex-characters;domain=%s;digest=lowercase-hex-SHA256(domain-bytes||preimage-bytes)"
        % (record_carrier, record_domain.replace("\0", "\\0")),
        "digest-formula=ordered-nested-records;carrier=%s;preimage=domain-bytes||concatenation-in-frozen-order-of-raw-32-byte-record-digests;domain=%s;digest=lowercase-hex-SHA256(preimage);empty-array-preimage-is-domain-bytes-alone-and-is-permitted-only-where-the-row-cardinality-rule-permits-zero%s"
        % (
            ordered_carrier,
            ordered_domain.replace("\0", "\\0"),
            explicit_vector_rule,
        ),
        "digest-formula=body;carrier=%s;preimage=ASCII-canonical-JSON-of-exact-top-level-object-with-carrier-set-to-64-lowercase-zero-hex-characters;domain=%s;digest=lowercase-hex-SHA256(domain-bytes||preimage-bytes);final-file-digest=plain-SHA256(exact-canonical-document-bytes)"
        % (body_carrier, body_domain.replace("\0", "\\0")),
        nested_exception,
    )


def _cross_binding_specifications() -> Tuple[dict, ...]:
    return (
        {
            "sources": ("production-schedule",),
            "source": (
                "/attempt_id",
                "/requests",
                "/ordered_request_record_sha256s",
            ),
            "targets": (
                "shard-requests",
                "preterminal-durable-artifact-inventory",
                "sha256-manifest",
            ),
            "target": (
                "shard-requests/every-JSONL-record",
                "shard-requests/plain-file-SHA256",
                "preterminal-inventory-/attempt_id",
                "sha256-manifest-/attempt_id",
            ),
            "kind": "exact-canonical-row-slice-and-plain-file-sha256",
            "formula": "partition-the-exact-32768-production-schedule-rows-into-32-contiguous-1024-row-shard-map-ranges-with-no-drop-duplication-or-reorder;request-rows-deliberately-have-no-attempt_id-so-the-schedule-root-attempt_id-equals-the-preterminal-inventory-and-manifest-attempt_id-and-the-request-files-are-bound-to-that-attempt-by-final-path-length-and-plain-file-SHA256",
            "cardinality": "32768-source-rows-to-32-files-times-1024-rows",
            "ordering": "logical_request_ordinal-strictly-1-through-32768",
        },
        {
            "sources": ("production-shard-map-receipt",),
            "source": (
                "/shards/*/shard_id",
                "/shards/*/logical_request_ordinal_min",
                "/shards/*/logical_request_ordinal_max",
                "/shards/*/shard_record_sha256",
            ),
            "targets": ("shard-requests", "shard-index"),
            "target": (
                "same-shard-request-range",
                "same-shard-index-/shard_record_sha256",
            ),
            "kind": "exact-equality-and-contiguous-range",
            "formula": "each-shard-map-row-selects-one-exact-1024-row-request-file-and-its-shard_record_sha256-equals-the-same-shard-index-field",
            "cardinality": "32-map-rows-to-32-request-files-and-32-indexes",
            "ordering": "shard-0001-through-shard-0032",
        },
        {
            "sources": ("shard-requests",),
            "source": ("each-request-identity", "request_instance_sha256"),
            "targets": ("shard-raw-records",),
            "target": ("same-logical-ordinal-raw-identity",),
            "kind": "exact-field-equality",
            "formula": "seed-row-logical-row-key-fixture-strategy-budget-plan-seed-seed-free-request-request-instance-and-runtime-lock-fields-match-exactly",
            "cardinality": "one-to-one-32768",
            "ordering": "same-shard-and-logical-ordinal",
        },
        {
            "sources": (
                "freeze-receipt",
                "source-manifest",
                "dependency-lock",
                "environment",
            ),
            "source": (
                "plain-SHA256-of-exact-freeze-receipt-file-bytes",
                "plain-SHA256-of-exact-source-manifest-file-bytes",
                "plain-SHA256-of-exact-dependency-lock-file-bytes",
                "/attempt_id",
                "/freeze_receipt_sha256",
                "/source_manifest_sha256",
                "/dependency_lock_sha256",
                "/runtime_profile_id",
                "/python_executable_sha256",
                "/python_framework_sha256",
                "/stdlib_closure_sha256",
                "/numpy_record_sha256",
                "/numpy_payload_closure_sha256",
                "/scipy_record_sha256",
                "/scipy_payload_closure_sha256",
                "/loaded_local_source_closure_sha256",
                "/abi_map_sha256",
                "plain-file-SHA256",
            ),
            "targets": ("production-runtime-receipt",),
            "target": (
                "/attempt_id",
                "/freeze_receipt_sha256",
                "/source_manifest_sha256",
                "/dependency_lock_sha256",
                "/runtime_profile_id",
                "/python_executable_sha256",
                "/python_framework_sha256",
                "/stdlib_closure_sha256",
                "/numpy_record_sha256",
                "/numpy_payload_closure_sha256",
                "/scipy_record_sha256",
                "/scipy_payload_closure_sha256",
                "/loaded_local_source_closure_sha256",
                "/abi_map_sha256",
                "/environment_sha256",
            ),
            "kind": "exact-overlapping-field-and-plain-sha256-equality",
            "formula": "environment.freeze_receipt_sha256-source_manifest_sha256-and-dependency_lock_sha256-equal-the-plain-SHA256-of-the-three-exact-already-durable-predecessor-files;all-14-overlapping-attempt-freeze-source-dependency-runtime-profile-python-framework-stdlib-numpy-scipy-local-source-and-ABI-fields-are-byte-for-byte-equal-between-environment-and-runtime-receipt;SHA256(exact-environment-file-bytes)==production-runtime-receipt.environment_sha256;environment-is-captured-after-the-dependency-lock-match-receipt-and-durable-before-the-runtime-receipt-with-no-back-reference-in-the-environment-body",
            "cardinality": "one-to-one",
            "ordering": "environment-durable-before-production-runtime-receipt",
        },
        {
            "sources": (
                "frozen-machine-manifest",
                "production-runtime-receipt",
            ),
            "source": (
                "v15-machine-manifest:cp62-runtime-lock-record-sha256",
                "/runtime_profile_id",
                "/python_framework_sha256",
                "/stdlib_closure_sha256",
                "/numpy_record_sha256",
                "/numpy_payload_closure_sha256",
                "/scipy_record_sha256",
                "/scipy_payload_closure_sha256",
                "/loaded_local_source_closure_sha256",
                "/abi_map_sha256",
                "/environment_sha256",
            ),
            "targets": ("shard-raw-records",),
            "target": (
                "every-record-/runtime_lock_sha256",
                "every-returned-or-present-closed-/kernel_trace/semantic/runtime_observation/runtime_lock_sha256",
                "every-present-/kernel_trace/semantic/runtime_observation/runtime_profile_id",
                "every-present-/kernel_trace/semantic/runtime_observation/exact-CP62-source-and-runtime-fields",
            ),
            "kind": "exact-manifest-runtime-lock-and-receipt-observation-crosscheck",
            "formula": "every-raw-outer-runtime_lock_sha256-and-every-present-nested-runtime_observation.runtime_lock_sha256-equals-the-v15-frozen-machine-manifest-CP62-runtime-lock-record-SHA256;production-runtime-receipt-has-no-runtime_lock_sha256-field;every-present-nested-runtime_observation.runtime_profile_id-equals-production-runtime-receipt.runtime_profile_id;all-other-present-CP62-runtime-observation-version-source-and-runtime-fields-replay-the-exact-frozen-CP62-runtime-lock-record-while-the-production-runtime-receipt-independently-binds-observed-python-framework-stdlib-numpy-scipy-local-source-ABI-and-environment-custody;the-two-descriptor-families-must-be-mutually-consistent-under-the-frozen-runtime-profile-but-CP74-authenticates-neither-and-accepts-no-production-runtime-evidence",
            "cardinality": "one-to-32768",
            "ordering": "logical-request-order",
        },
        {
            "sources": ("shard-raw-records",),
            "source": ("every-raw-record",),
            "targets": ("shard-stable-traces",),
            "target": ("same-logical-ordinal-stable-record",),
            "kind": "deterministic-candidate-projection",
            "formula": "from-an-already-formed-CP74-raw-record-replace-top-level-schema-with-cp74-test28-production-stable-trace-jsonl-candidate-v1;remove-supervisor_custody-and-raw_sha256;replace-kernel_trace-by-kernel_trace.semantic;copy-phase-closed_status-failure_code-byte-for-byte-and-copy-every-other-retained-field-byte-semantically-at-the-same-logical-ordinal;therefore-the-stable-record-inherits-only-the-exact-four-phase-six-closed-status-five-refusal-code-seven-execution-failure-code-discriminated-union-already-closed-by-the-raw-rule;preserve-the-already-CP74-projected-terminal-semantic-and-its-digest;canonicalize",
            "cardinality": "one-to-one-32768",
            "ordering": "same-shard-and-logical-ordinal",
        },
        {
            "sources": ("shard-raw-records",),
            "source": (
                "every-record-/supervisor_custody/stderr_sha256",
                "every-record-/supervisor_custody/stderr_bytes",
                "every-record-/supervisor_custody/stderr_hex",
            ),
            "targets": ("shard-stderr-records",),
            "target": (
                "same-ordinal-frame-payload-SHA256",
                "payload-length",
                "payload-bytes",
            ),
            "kind": "exact-bytes-plain-sha256-and-byte-length-equality",
            "formula": "parse-exactly-1024-uint64-BE-frames;payload-bytes-equal-bytes.fromhex(stderr_hex);payload-length-equals-stderr_bytes;payload-SHA256-equals-stderr_sha256;no-trailing-bytes",
            "cardinality": "one-to-one-32768",
            "ordering": "same-shard-and-logical-ordinal",
        },
        {
            "sources": ("shard-raw-records",),
            "source": ("arm-appropriate-initial-Philox-state-SHA256-fields",),
            "targets": ("shard-rng-initial-states",),
            "target": ("same-ordinal-normalized-stream-state-rows",),
            "kind": "CP62-Philox-state-digest-reconstruction",
            "formula": "returned-arms-reconstruct-exact-NumPy-Philox-dict-with-sorted-string-keys-and-native-frozen-<u8-counter4-key2-buffer4-arrays;apply-domain-heterodiff-mixed-support-initializer-v2-philox-state-NUL-and-CP62-recursive-N/B/I/S/D/T/A-type-tags;compare-to-raw-initial-state-digests;closed-refusal-failure-timeout-arms-use-explicit-absent-unobserved-sentinels-because-exact21-semantic-has-no-RNG-state-hash",
            "cardinality": "three-stream-slots-per-32768-requests-with-strategy-specific-presence",
            "ordering": "same-shard-logical-ordinal-and-stream-role",
        },
        {
            "sources": ("shard-raw-records",),
            "source": ("arm-appropriate-final-Philox-state-SHA256-fields",),
            "targets": ("shard-rng-final-states",),
            "target": ("same-ordinal-normalized-stream-state-rows",),
            "kind": "CP62-Philox-state-digest-reconstruction",
            "formula": "returned-arms-reconstruct-exact-NumPy-Philox-dict-with-sorted-string-keys-and-native-frozen-<u8-counter4-key2-buffer4-arrays;apply-domain-heterodiff-mixed-support-initializer-v2-philox-state-NUL-and-CP62-recursive-N/B/I/S/D/T/A-type-tags;compare-to-raw-final-state-digests;closed-refusal-failure-timeout-arms-use-explicit-absent-unobserved-sentinels-because-exact21-semantic-has-no-RNG-state-hash",
            "cardinality": "three-stream-slots-per-32768-requests-with-strategy-specific-presence",
            "ordering": "same-shard-logical-ordinal-and-stream-role",
        },
        *_index_cross_binding_specs(),
        {
            "sources": (
                "production-shard-map-receipt",
                "shard-index",
                "shard-requests",
                "shard-raw-records",
                "shard-stable-traces",
                "shard-stderr-records",
                "shard-rng-initial-states",
                "shard-rng-final-states",
            ),
            "source": (
                "shard-map-raw-SHA256",
                "same-shard-index-SHA256",
                "all-six-same-shard-file-SHA256-values",
            ),
            "targets": ("shard-receipt",),
            "target": (
                "/production_shard_map_receipt_sha256",
                "/shard_index_sha256",
                "six-file-SHA256-fields",
            ),
            "kind": "exact-plain-sha256-cross-binding",
            "formula": "receipt-production_shard_map_receipt_sha256-equals-plain-SHA256-of-map-file;index-and-all-six-file-digests-equal-same-shard-final-file-bytes",
            "cardinality": "32-receipts-each-bind-one-map-one-index-and-six-files",
            "ordering": "shard-0001-through-shard-0032",
        },
        {
            "sources": (
                "shard-raw-records",
                "shard-stable-traces",
                "shard-receipt",
            ),
            "source": (
                "ordered-32-raw-file-SHA256s",
                "ordered-32-stable-file-SHA256s",
                "ordered-32-receipt-SHA256s",
            ),
            "targets": ("postexecution-independent-recomputation",),
            "target": (
                "/ordered_raw_file_sha256s",
                "/ordered_stable_file_sha256s",
                "/ordered_shard_receipt_sha256s",
            ),
            "kind": "exact-vector-equality",
            "formula": "all-three-32-element-root-vectors-equal-the-plain-file-or-receipt-SHA256-values-in-shard-ordinal-order;recomputation-is-anchored-in-ordered-hashed-raw-files-and-receipts-and-never-trusts-the-stable-vector-without-independent-raw-reprojection",
            "cardinality": "32-and-32-and-32",
            "ordering": "shard-ordinal-order",
        },
        {
            "sources": ("shard-raw-records",),
            "source": ("all-32768-hashed-raw-records",),
            "targets": (
                "shard-stable-traces",
                "postexecution-independent-recomputation",
            ),
            "target": (
                "all-32768-stable-records-and-32-stable-file-SHA256s",
                "/raw_to_stable_projection_recomputed",
                "/cp71_output_canonical_json_sha256",
                "/cp72_validation_summary_public_sha256",
                "/cp73_relation_summary_public_sha256",
            ),
            "kind": "independent-deterministic-reprojection",
            "formula": _STABLE_TO_CP69_TO_CP71_CANDIDATE_FORMULA,
            "cardinality": "32768-records-and-32-files",
            "ordering": "shard-major-logical-ordinal-minor",
        },
        {
            "sources": (
                "postexecution-independent-recomputation",
                "power-threshold-receipt",
                "power-review-signoff",
            ),
            "source": (
                "plain-SHA256-of-exact-final-recomputation-file-bytes",
                "/estimand_estimate_intervals/*/(estimand_id,record_sha256,estimate,interval_lower,interval_upper)",
                "/ordered_estimand_record_sha256s_sha256",
                "power-threshold-receipt-plain-file-SHA256-and-/ordered_slot_thresholds/*/(slot_ordinal,gate_id,estimand_id,row_sha256)-plus-/ordered_slot_threshold_row_sha256s",
                "power-review-signoff-plain-file-SHA256",
            ),
            "targets": ("primary-metrics",),
            "target": (
                "/recomputation_artifact_sha256",
                "/power_threshold_receipt_sha256",
                "/power_review_signoff_sha256",
                "/ordered_primary_slots/*/(estimand_id,estimand_record_sha256,estimate,interval_lower,interval_upper)",
                "/ordered_primary_slots/*/(slot_ordinal,slot_id,gate_id,threshold_row_sha256)",
            ),
            "kind": "exact-plain-file-sha256-and-estimand-field-projection",
            "formula": "primary.recomputation_artifact_sha256-equals-plain-SHA256-of-the-exact-final-recomputation-artifact-bytes;primary.power_threshold_receipt_sha256-and-power_review_signoff_sha256-equal-the-exact-retained-predecessor-raw-file-digests;each-primary-slot-estimand_id-estimand_record_sha256-estimate-interval_lower-and-interval_upper-equals-the-corresponding-selected-CP71-estimand-record-field-byte-for-byte;each-slot_ordinal-slot_id-gate_id-threshold_row_sha256-equals-the-corresponding-CP65-threshold-row-identity-and-digest;threshold-value/operator/decision-law-remain-unresolved",
            "cardinality": "554-inventory-to-32-references",
            "ordering": "primary-slot-ordinal-1-through-32",
        },
        {
            "sources": (
                "shard-requests",
                "shard-raw-records",
                "shard-stable-traces",
                "shard-receipt",
            ),
            "source": ("all-request-outcome-and-file-facts",),
            "targets": (
                "secondary-diagnostics",
                "deviations",
                "failures",
                "exclusions",
                "reruns",
            ),
            "target": (
                "secondary-/ordered_shard_receipt_sha256s",
                "secondary-/ordered_raw_file_sha256s",
                "secondary-/ordered_stable_file_sha256s",
                "source-bound-envelope-entries-and-terminal-counts",
            ),
            "kind": "exact-projection-and-closed-source-bound-diagnostic-envelope",
            "formula": "secondary-root-ordered-receipt-raw-and-stable-SHA256-vectors-equal-the-same-32-final-shard-files-and-receipts-in-shard-order;terminal-counts-failures-deviations-exclusions-and-reruns-crosscheck-exact-request-raw-stable-receipt-facts;no-drop-same-attempt-retry-replacement-or-topup;diagnostic-envelope-ID-kind-value-grammar-is-closed-but-realized-diagnostic-scientific-content-is-absent-and-not-production-accepted",
            "cardinality": "all-32768-requests-accounted",
            "ordering": "ordinal-order-with-deterministic-ledger-entry-order",
        },
        {
            "sources": (
                "primary-metrics",
                "power-threshold-receipt",
                "power-review-signoff",
            ),
            "source": (
                "primary-metrics-plain-final-file-SHA256",
                "primary-metrics-/power_threshold_receipt_sha256",
                "primary-metrics-/power_review_signoff_sha256",
                "/ordered_primary_slots/*/(slot_ordinal,slot_id,slot_record_sha256,gate_id,threshold_row_sha256)",
                "power-threshold-receipt-plain-file-SHA256-and-/ordered_slot_thresholds/*/(slot_ordinal,gate_id,row_sha256)-plus-/ordered_slot_threshold_row_sha256s",
                "power-review-signoff-plain-file-SHA256",
            ),
            "targets": ("decisions",),
            "target": (
                "/primary_metrics_sha256",
                "/power_threshold_receipt_sha256",
                "/power_review_signoff_sha256",
                "/ordered_slot_decisions/*/(slot_ordinal,slot_id,primary_metric_record_sha256,threshold_row_sha256)",
            ),
            "kind": "exact-plain-file-sha256-and-slot-reference-envelope",
            "formula": "primary-metrics.power_threshold_receipt_sha256-and-power_review_signoff_sha256-equal-the-exact-retained-CP65-threshold-receipt-and-power-review-signoff-raw-file-digests;decisions.primary_metrics_sha256-equals-plain-SHA256-of-exact-final-primary-metrics-file-bytes;decisions-power-threshold-receipt-and-power-review-signoff-SHA-fields-equal-the-same-two-exact-retained-predecessor-raw-file-digests-and-therefore-equal-the-primary-root-fields;each-decision-row-slot_ordinal-slot_id-primary_metric_record_sha256-and-threshold_row_sha256-equals-the-corresponding-primary-slot-and-CP65-threshold-row-fields;gate_id-equals-cp65-power-primary-slot-%02d;candidate-v1-sets-resolution-false-and-decision-values-null;no-operator-or-PASS-FAIL-law",
            "cardinality": "32-to-32",
            "ordering": "slot-ordinal-order",
        },
        {
            "sources": ("decisions", "deviations", "failures", "exclusions", "reruns"),
            "source": ("resolution-and-ledger-semantic-states",),
            "targets": ("terminal-state",),
            "target": ("branch-terminal-state-and-reason-code-semantics",),
            "kind": "branch-conditional-semantic-consistency-without-direct-terminal-digest-field",
            "formula": "terminal-state-and-reason-code-must-be-compatible-with-the-decision-resolution-and-ledger-contents;live-CP65-terminal-state-has-no-decisions-or-ledger-SHA-fields-so-this-rule-claims-no-direct-digest-binding;all-file-SHA-custody-is-exclusively-via-rule23-preterminal-inventory-and-manifest;current-unresolved-decision-envelope-cannot-produce-PASS-or-FAIL",
            "cardinality": "one-terminal-state-per-branch",
            "ordering": "terminal-publication-order",
        },
        {
            "sources": _REFERENCED_OUTPUT_ARTIFACT_IDS,
            "source": (
                "each-present-final-relative-path",
                "byte-length",
                "plain-file-SHA256",
                "every-present-global-or-RNG-root-and-raw-or-stable-record-/attempt_id",
            ),
            "targets": (
                "preterminal-durable-artifact-inventory",
                "sha256-manifest",
            ),
            "target": (
                "exact-present-entry-set-and-/attempt_id",
                "exact-present-entry-set-and-/attempt_id",
            ),
            "kind": "exact-all-and-only-present-artifact-binding",
            "formula": "every-present-referenced-output-final-file-occurs-exactly-once-with-exact-path-length-and-plain-SHA256-in-both-inventory-and-manifest;every-present-JSON-global-root-RNG-root-and-raw-or-stable-record-attempt_id-equals-the-surrounding-preterminal-inventory-and-manifest-attempt_id;shard-request-records-have-no-attempt_id-and-are-bound-to-the-production-schedule-top-level-attempt_id-by-rule1-plus-path-and-file-digest-custody;stderr-has-no-JSON-attempt-field-but-is-path-and-digest-bound-to-the-same-attempt;absent-output-has-no-entry;partial-writer-files-never-occur",
            "cardinality": "branch-dependent-0-through-201-final-output-instances",
            "ordering": "frozen-artifact-then-shard-order",
        },
        {
            "sources": ("terminal-state", "sha256-manifest"),
            "source": ("plain-file-SHA256", "plain-file-SHA256"),
            "targets": ("committed-marker",),
            "target": ("terminal-state-and-manifest-binding-fields",),
            "kind": "exact-plain-sha256-equality",
            "formula": "COMMITTED-transitively-binds-the-winning-terminal-state-and-complete-manifest-after-file-and-directory-durability",
            "cardinality": "two-to-one",
            "ordering": "terminal-state-then-manifest-then-COMMITTED",
        },
    )


def _index_cross_binding_specs() -> Tuple[dict, ...]:
    families = (
        ("shard-requests", "request", "LF-delimited-canonical-JSON"),
        ("shard-raw-records", "raw", "LF-delimited-canonical-JSON"),
        ("shard-stable-traces", "stable", "LF-delimited-canonical-JSON"),
        ("shard-stderr-records", "stderr", "uint64-BE-frames"),
        ("shard-rng-initial-states", "rng-initial", "canonical-JSON-container"),
        ("shard-rng-final-states", "rng-final", "canonical-JSON-container"),
    )
    result = []
    for artifact_id, stem, framing in families:
        if stem in ("request", "raw", "stable"):
            formula = "index-offset-starts-0;each-payload-length-excludes-LF;offset-advances-length+1;payload-SHA256-is-plain;last-offset+length+1-equals-file-bytes;exactly-1024-rows-no-trailing"
        elif stem == "stderr":
            formula = "index-offset-starts-0;frame_length=8+payload_length;8-byte-big-endian-prefix-equals-payload_length;payload-SHA256-plain;offset-advances-frame_length;final-coverage-equals-file-bytes;exactly-1024-frames-no-trailing"
        else:
            formula = "container-has-exactly-1024-ordered-state-rows;each-index-row-SHA256-equals-corresponding-container-row-SHA256;plain-file-SHA256-equals-index-field;zero-trailing-bytes"
        target_components = (
            ("request-segment-offset-length-and-record-SHA256-fields",)
            if stem == "request"
            else (
                "%s-segment-or-row-index-fields" % stem,
                "%s-file-SHA256-field" % stem,
            )
        )
        result.append(
            {
                "sources": (artifact_id,),
                "source": ("exact-final-file-bytes", "1024-logical-units"),
                "targets": ("shard-index",),
                "target": target_components,
                "kind": "exact-framing-offset-length-and-plain-sha256-coverage",
                "formula": framing + ";" + formula,
                "cardinality": "17-CP65-segment/file-bindings-grouped-across-six-families;1024-units-per-shard-times-32",
                "ordering": "same-shard-contiguous-logical-ordinal-order",
            }
        )
    return tuple(result)


def _build_cross_binding_rules() -> Tuple[CP74OutputCrossBindingRuleV1, ...]:
    specs = _cross_binding_specifications()
    if len(specs) != CP74_TEST28_OUTPUT_CROSS_BINDING_COUNT:
        raise RuntimeError("CP74 cross-binding specification count differs")
    rows = []
    for ordinal, spec in enumerate(specs, 1):
        rows.append(
            cast(
                CP74OutputCrossBindingRuleV1,
                _record(
                    CP74OutputCrossBindingRuleV1,
                    {
                        "schema_version": CP74_TEST28_SCHEMA_VERSION,
                        "rule_ordinal": ordinal,
                        "rule_id": _OUTPUT_CROSS_BINDING_RULE_IDS[ordinal - 1],
                        "source_artifact_ids": spec["sources"],
                        "source_pointer_or_components": spec["source"],
                        "target_artifact_ids": spec["targets"],
                        "target_pointer_or_components": spec["target"],
                        "digest_or_equality_kind": spec["kind"],
                        "preimage_or_equality_formula": spec["formula"],
                        "cardinality_rule": spec["cardinality"],
                        "ordering_rule": spec["ordering"],
                        "required_in_complete_attempt": True,
                        "candidate_only": True,
                    },
                ),
            )
        )
    return tuple(rows)


_ORDERED_RECORD_DOMAINS = {
    CP74LifecycleBranchRuleV1: b"cp74-test28-ordered-lifecycle-branch-rule-digests-v1\0",
    CP74CrashCutRuleV1: b"cp74-test28-ordered-crash-cut-rule-digests-v1\0",
    CP74ArtifactOccurrenceRuleV1: b"cp74-test28-ordered-artifact-occurrence-rule-digests-v1\0",
    CP74ExecutionOutputSemanticRuleV1: b"cp74-test28-ordered-execution-output-semantic-rule-digests-v1\0",
    CP74OutputCrossBindingRuleV1: b"cp74-test28-ordered-output-cross-binding-rule-digests-v1\0",
}
_CANDIDATE_SEMANTIC_DOMAIN = b"cp74-test28-candidate-schema-semantic-v1\0"


def _ordered_record_digest(records: tuple) -> str:
    if not records or type(records) is not tuple:
        raise RuntimeError("CP74 ordered digest requires a nonempty exact tuple")
    record_type = type(records[0])
    if record_type not in _ORDERED_RECORD_DOMAINS or any(
        type(item) is not record_type for item in records
    ):
        raise RuntimeError("CP74 ordered digest record type differs")
    return hashlib.sha256(
        _ORDERED_RECORD_DOMAINS[record_type]
        + b"".join(bytes.fromhex(item.record_sha256) for item in records)
    ).hexdigest()


def _predecessor_custody() -> CP74PredecessorCustodyV1:
    return cast(
        CP74PredecessorCustodyV1,
        _record(
            CP74PredecessorCustodyV1,
            {
                "schema_version": CP74_TEST28_SCHEMA_VERSION,
                "v24_protocol_markdown_path": _V24_PROTOCOL_PATH,
                "v24_protocol_markdown_sha256": _V24_PROTOCOL_SHA256,
                "v24_protocol_markdown_bytes": _V24_PROTOCOL_BYTES,
                "v24_protocol_markdown_lf_count": _V24_PROTOCOL_LF_COUNT,
                "v24_machine_manifest_path": _V24_MANIFEST_PATH,
                "v24_machine_manifest_sha256": _V24_MANIFEST_SHA256,
                "v24_machine_manifest_bytes": _V24_MANIFEST_BYTES,
                "v24_machine_manifest_lf_count": _V24_MANIFEST_LF_COUNT,
                "predecessor_component_ids": _PREDECESSOR_COMPONENT_IDS,
                "predecessor_source_paths": _PREDECESSOR_SOURCE_PATHS,
                "predecessor_source_sha256s": _PREDECESSOR_SOURCE_SHA256S,
                "predecessor_bundle_record_sha256s": _PREDECESSOR_BUNDLE_RECORD_SHA256S,
                "predecessor_bundle_public_sha256s": _PREDECESSOR_BUNDLE_PUBLIC_SHA256S,
                "cp65_artifact_id_order_sha256": _CP65_ARTIFACT_ID_ORDER_SHA256,
                "cp65_artifact_schema_record_order_sha256": _CP65_ARTIFACT_SCHEMA_RECORD_ORDER_SHA256,
                "cp65_referenced_output_id_order_sha256": _CP65_REFERENCED_OUTPUT_ID_ORDER_SHA256,
                "cp65_schema_semantic_sha256": _CP65_SCHEMA_SEMANTIC_SHA256,
                "cp65_gate_evidence_dag_node_count": 20,
                "cp65_gate_evidence_dag_edge_count": 44,
                "cp65_gate_evidence_dag_semantic_sha256": _CP65_GATE_EVIDENCE_DAG_SEMANTIC_SHA256,
                "cp65_gate_evidence_dag_is_not_full_typed_graph": True,
                "cp65_gate_evidence_artifact_id_aliases": _CP65_GATE_EVIDENCE_ARTIFACT_ID_ALIASES,
                "cp65_typed_artifact_preimage_graph_vector_lengths": _CP65_TYPED_ARTIFACT_PREIMAGE_GRAPH_VECTOR_LENGTHS,
                "cp65_typed_artifact_preimage_graph_semantic_sha256": _CP65_TYPED_ARTIFACT_PREIMAGE_GRAPH_SEMANTIC_SHA256,
                "cp65_typed_digest_graph_inherited_by_hash_reference_only": True,
                "cp65_typed_digest_graph_revalidated_by_cp74": False,
                "custody_is_hash_reference_only": True,
                "predecessor_runtime_imports_performed": False,
                "production_artifacts_observed": False,
            },
        ),
    )


def _candidate_contract() -> CP74CandidateSchemaContractV1:
    return cast(
        CP74CandidateSchemaContractV1,
        _record(
            CP74CandidateSchemaContractV1,
            {
                "schema_version": CP74_TEST28_SCHEMA_VERSION,
                "scope": CP74_TEST28_SCOPE,
                "canonical_profile_id": _CANONICAL_PROFILE_ID,
                "artifact_count": CP74_TEST28_ARTIFACT_COUNT,
                "receipt_envelope_artifact_count": 41,
                "referenced_output_artifact_count": CP74_TEST28_REFERENCED_OUTPUT_COUNT,
                "frozen_or_binary_custody_artifact_count": 8,
                "lifecycle_branch_count": CP74_TEST28_LIFECYCLE_BRANCH_COUNT,
                "crash_cut_count": CP74_TEST28_CRASH_CUT_COUNT,
                "output_cross_binding_count": CP74_TEST28_OUTPUT_CROSS_BINDING_COUNT,
                "shard_count": CP74_TEST28_SHARD_COUNT,
                "seed_count": CP74_TEST28_SEED_COUNT,
                "row_count": CP74_TEST28_ROW_COUNT,
                "request_count": CP74_TEST28_REQUEST_COUNT,
                "estimand_count": CP74_TEST28_ESTIMAND_COUNT,
                "primary_gate_slot_count": 32,
                "artifact_ids": _ARTIFACT_IDS,
                "lifecycle_branch_ids": _LIFECYCLE_BRANCH_IDS,
                "crash_cut_ids": _CRASH_CUT_IDS,
                "referenced_output_artifact_ids": _REFERENCED_OUTPUT_ARTIFACT_IDS,
                "output_cross_binding_rule_ids": _OUTPUT_CROSS_BINDING_RULE_IDS,
                "branch_occurrence_expression_enum": _BRANCH_OCCURRENCE_EXPRESSION_ENUM,
                "conditional_occurrence_rule_ids": _CONDITIONAL_OCCURRENCE_RULE_IDS,
                "all_cp65_artifact_descriptors_preserved": True,
                "all_artifact_occurrences_closed": True,
                "all_branch_arms_mutually_exclusive_and_exhaustive": True,
                "all_conditional_occurrence_rules_closed": True,
                "all_output_envelope_framing_and_cross_binding_descriptors_candidate_complete": True,
                "all_cross_bindings_candidate_complete": True,
                "descriptor_bodies_only": True,
                "production_output_bodies_accepted": False,
                "public_caller_data_api_exposed": False,
                "project_modules_imported": False,
                "stdlib_only": True,
                "module_direct_filesystem_io": False,
                "module_direct_clock": False,
                "module_direct_rng": False,
                "module_direct_network": False,
                "module_direct_subprocess": False,
                "candidate_schema_inventory_complete": True,
                "candidate_descriptor_definition_complete": True,
                "primary_decision_semantics_resolved": False,
                "primary_decision_semantics_deferred_to_external_power_review": True,
                "independent_structural_validator_required": True,
                "schema_acceptance_independent": False,
                "authoritative_for_production": False,
                "production_schema_frozen": False,
                "production_execution_and_output_schema_frozen": False,
                "production_receipt_schema_frozen": False,
                "production_artifacts_observed": False,
                "production_evidence_accepted": False,
                "gate_ids": _PRODUCTION_GATE_IDS,
                "gate_states": _MISSING_GATE_STATES,
                "blocker_ids": _DRAFT_BLOCKER_IDS,
                "blocker_states": _MISSING_BLOCKER_STATES,
                "blocker_ledger_total_count": CP74_TEST28_BLOCKER_LEDGER_TOTAL_COUNT,
                "blocker_ledger_satisfied_count": CP74_TEST28_BLOCKER_LEDGER_SATISFIED_COUNT,
                "blocker_ledger_missing_count": CP74_TEST28_BLOCKER_LEDGER_MISSING_COUNT,
                "formal_test_28_status": CP74_TEST28_FORMAL_TEST_28_STATUS,
                "formal_test_28_closed": False,
            },
        ),
    )


def _validate_internal_definition(
    lifecycle: Tuple[CP74LifecycleBranchRuleV1, ...],
    cuts: Tuple[CP74CrashCutRuleV1, ...],
    occurrences: Tuple[CP74ArtifactOccurrenceRuleV1, ...],
    outputs: Tuple[CP74ExecutionOutputSemanticRuleV1, ...],
    cross: Tuple[CP74OutputCrossBindingRuleV1, ...],
) -> None:
    if tuple(row.branch_id for row in lifecycle) != _LIFECYCLE_BRANCH_IDS:
        raise RuntimeError("CP74 lifecycle inventory differs")
    if tuple(row.crash_cut_id for row in cuts) != _CRASH_CUT_IDS:
        raise RuntimeError("CP74 crash-cut inventory differs")
    if tuple(row.artifact_id for row in occurrences) != _ARTIFACT_IDS:
        raise RuntimeError("CP74 occurrence inventory differs")
    if tuple(row.artifact_id for row in outputs) != _REFERENCED_OUTPUT_ARTIFACT_IDS:
        raise RuntimeError("CP74 output inventory differs")
    if tuple(row.rule_id for row in cross) != _OUTPUT_CROSS_BINDING_RULE_IDS:
        raise RuntimeError("CP74 cross-binding inventory differs")
    if (
        tuple(
            row.artifact_id for row in occurrences if not row.manifest_bound_if_present
        )
        != _MANIFEST_BINDING_EXCLUDED_ARTIFACT_IDS
    ):
        raise RuntimeError("CP74 SHA-manifest binding exception set differs")
    if (
        tuple(
            row.artifact_id
            for row in occurrences
            if not row.committed_marker_transitively_binds_if_present
        )
        != _COMMITTED_TRANSITIVE_BINDING_EXCLUDED_ARTIFACT_IDS
    ):
        raise RuntimeError("CP74 COMMITTED transitive binding exception set differs")
    artifact_set = set(_ARTIFACT_IDS)
    if (
        len(_CP64_FUTURE_DIGEST_EDGES) != 44
        or len(set(_CP64_FUTURE_DIGEST_EDGES)) != 44
        or any(
            source not in artifact_set or target not in artifact_set
            for source, target in _CP64_FUTURE_DIGEST_EDGES
        )
    ):
        raise RuntimeError("CP74 inherited CP64 direct digest edge set differs")
    occurrence_by_id = {row.artifact_id: row for row in occurrences}
    for row in occurrences:
        if (
            tuple(branch for branch, _ in row.branch_occurrence_expressions)
            != _LIFECYCLE_BRANCH_IDS
        ):
            raise RuntimeError("CP74 occurrence branch order differs")
        if any(
            expression not in _BRANCH_OCCURRENCE_EXPRESSION_ENUM
            for _, expression in row.branch_occurrence_expressions
        ):
            raise RuntimeError("CP74 occurrence expression is not closed")
        if not set(row.dependency_predecessor_artifact_ids) <= artifact_set:
            raise RuntimeError("CP74 occurrence dependency is unresolved")
        if (
            len(row.dependency_predecessor_artifact_ids)
            != len(set(row.dependency_predecessor_artifact_ids))
            or row.artifact_id in row.dependency_predecessor_artifact_ids
            or row.dependency_predecessor_artifact_ids
            != _artifact_dependencies(row.artifact_id)
        ):
            raise RuntimeError("CP74 direct artifact dependency projection differs")
    for source, target in _CP64_FUTURE_DIGEST_EDGES:
        if source not in occurrence_by_id[target].dependency_predecessor_artifact_ids:
            raise RuntimeError("CP74 omitted an inherited CP64 direct digest edge")

    indegree = {artifact_id: 0 for artifact_id in _ARTIFACT_IDS}
    outgoing = {artifact_id: [] for artifact_id in _ARTIFACT_IDS}
    for row in occurrences:
        for source in row.dependency_predecessor_artifact_ids:
            outgoing[source].append(row.artifact_id)
            indegree[row.artifact_id] += 1
    frontier = [
        artifact_id for artifact_id in _ARTIFACT_IDS if indegree[artifact_id] == 0
    ]
    visited = 0
    while frontier:
        source = frontier.pop()
        visited += 1
        for target in outgoing[source]:
            indegree[target] -= 1
            if indegree[target] == 0:
                frontier.append(target)
    if visited != len(_ARTIFACT_IDS):
        raise RuntimeError("CP74 complete artifact dependency graph is cyclic")

    lifecycle_by_id = {row.branch_id: row for row in lifecycle}
    for branch_id in _LIFECYCLE_BRANCH_IDS:
        expressions = {
            row.artifact_id: dict(row.branch_occurrence_expressions)[branch_id]
            for row in occurrences
        }
        lifecycle_row = lifecycle_by_id[branch_id]
        if lifecycle_row.always_required_artifact_ids != tuple(
            artifact_id
            for artifact_id in _ARTIFACT_IDS
            if expressions[artifact_id] in ("EXACT_GLOBAL_ONE", "EXACT_ALL_32_SHARDS")
        ):
            raise RuntimeError("CP74 lifecycle exact-occurrence projection differs")
        if lifecycle_row.always_forbidden_artifact_ids != tuple(
            artifact_id
            for artifact_id in _ARTIFACT_IDS
            if expressions[artifact_id] == "ABSENT"
        ):
            raise RuntimeError("CP74 lifecycle absent-occurrence projection differs")
        if lifecycle_row.durable_prefix_artifact_ids != tuple(
            artifact_id
            for artifact_id in _ARTIFACT_IDS
            if expressions[artifact_id] == "DURABLE_PREFIX_DEPENDENCY_CLOSED"
        ):
            raise RuntimeError("CP74 lifecycle durable-prefix projection differs")
        for artifact_id, expression in expressions.items():
            if expression == "ABSENT":
                continue
            if any(
                expressions[predecessor] == "ABSENT"
                for predecessor in _transitive_artifact_dependencies(artifact_id)
            ):
                raise RuntimeError(
                    "CP74 branch occurrence violates dependency downward closure"
                )

    if (
        _artifact_dependencies("production-runtime-receipt")[0] != "source-manifest"
        or "environment" not in _artifact_dependencies("production-runtime-receipt")
        or "production-runtime-receipt"
        not in _artifact_dependencies("external-seed-acquisition-start-receipt")
    ):
        raise RuntimeError(
            "CP74 environment/runtime/acquisition temporal order differs"
        )
    for cut in cuts:
        required = set(cut.required_durable_artifact_ids)
        forbidden = set(cut.forbidden_artifact_ids)
        conditional = set(cut.conditional_artifact_ids)
        if (
            not required <= artifact_set
            or not forbidden <= artifact_set
            or not conditional <= artifact_set
            or required & forbidden
            or conditional & forbidden
            or "environment" in forbidden
        ):
            raise RuntimeError("CP74 crash-cut artifact inventory differs")
        transitive_required = {
            predecessor
            for artifact_id in required
            for predecessor in _transitive_artifact_dependencies(artifact_id)
        }
        if transitive_required & forbidden:
            raise RuntimeError(
                "CP74 crash-cut required dependency closure intersects forbidden set"
            )
        for branch_id in cut.applicable_branch_ids:
            expressions = {
                row.artifact_id: dict(row.branch_occurrence_expressions)[branch_id]
                for row in occurrences
            }
            if any(expressions[artifact_id] == "ABSENT" for artifact_id in required):
                raise RuntimeError("CP74 crash-cut requires a branch-absent artifact")
    cut_bases = (
        _CUT1_AND_CUT2_REQUIRED_BASE,
        _CUT1_AND_CUT2_REQUIRED_BASE,
        _CUT3_REQUIRED_BASE,
        _CUT4_REQUIRED_BASE,
        _CUT5_REQUIRED_BASE,
        _CUT6_REQUIRED_BASE,
    )
    for cut, base in zip(cuts, cut_bases):
        expected = set(base)
        for artifact_id in base:
            expected.update(_transitive_artifact_dependencies(artifact_id))
        if cut.required_durable_artifact_ids != tuple(
            artifact_id for artifact_id in _ARTIFACT_IDS if artifact_id in expected
        ):
            raise RuntimeError("CP74 crash-cut gate-stage required closure differs")
    if (
        len(cuts[4].required_durable_artifact_ids) != 38
        or len(cuts[5].required_durable_artifact_ids) != 39
    ):
        raise RuntimeError("CP74 launch crash-cut required cardinality differs")
    output_set = set(_REFERENCED_OUTPUT_ARTIFACT_IDS)
    for row in cross:
        if not set(row.source_artifact_ids + row.target_artifact_ids) <= artifact_set:
            raise RuntimeError("CP74 cross-binding artifact is unresolved")
    covered = {rule_id for row in outputs for rule_id in row.cross_binding_rule_ids}
    expected_covered = set(_OUTPUT_CROSS_BINDING_RULE_IDS[:-1])
    if covered != expected_covered:
        raise RuntimeError("CP74 output cross-binding reference is unresolved")
    cross_by_id = {row.rule_id: row for row in cross}
    for output in outputs:
        for rule_id in output.cross_binding_rule_ids:
            row = cross_by_id[rule_id]
            if output.artifact_id not in (
                row.source_artifact_ids + row.target_artifact_ids
            ):
                raise RuntimeError("CP74 output cross-binding reciprocity differs")
    if not output_set <= {row.artifact_id for row in occurrences}:
        raise RuntimeError("CP74 output lacks an occurrence row")

    output_by_id = {row.artifact_id: row for row in outputs}
    for artifact_id in ("shard-raw-records", "shard-stable-traces"):
        rules = output_by_id[artifact_id].field_semantic_rules
        omission_digest_rules = tuple(
            rule
            for rule in rules
            if "digest-formula=SHA256(" in rule and "field-omitted" in rule
        )
        if len(omission_digest_rules) != 9 or not all(
            carrier in "\n".join(omission_digest_rules)
            for carrier in (
                "cp74_semantic_trace_sha256",
                "cp74_closed_trace_sha256",
                "cp62_configuration_sha256",
                "cp62_source_evaluation_sha256",
                "cp62_facade_evaluation_sha256",
                "cp62_scored_sha256",
                "cp62_quota_sha256",
                "cp62_attempt_sha256",
                "cp62_particle_sha256",
            )
        ):
            raise RuntimeError("CP74 inherited omission digest formula set differs")
        joined = "\n".join(rules)
        for required_fragment in (
            "configuration-fixture-union=T28-M1-Q-has-at-most-1-event-and-T28-M2-Q-has-at-most-2-events",
            "deterministic-fixture-score-replay=count_penalty-is--1/4-only-for-T28-M2-Q-with-two-events",
            "certify_arbitrary_rational_uint64_exp_quota(attempt.exact_delta)",
            "stream-seed-derivation=SHA256(heterodiff-mixed-support-initializer-derived-stream-v2\\0",
            "worst_case_occurrences",
            "worst_case_coordinates",
        ):
            if required_fragment not in joined:
                raise RuntimeError("CP74 CP62 nested semantic closure differs")
    if output_by_id["shard-stable-traces"].record_digest_domain != (
        "plain-sha256-of-exact-canonical-stable-record-bytes-before-LF"
    ):
        raise RuntimeError("CP74 stable record digest semantics differ")
    postrecompute_rules = "\n".join(
        output_by_id["postexecution-independent-recomputation"].field_semantic_rules
    )
    if (
        "/estimand_estimate_intervals/*/estimand_record_sha256" in postrecompute_rules
        or "exact-literal=cp69-test28-compact-projection-interchange-qualification-v1"
        not in postrecompute_rules
        or "embedded-/cp71_output_canonical_json_sha256=plain-SHA256(the-identical-exact-canonical-CP71-output-bytes-used-by-/output_body_sha256)"
        not in postrecompute_rules
    ):
        raise RuntimeError("CP74 CP71 embedded digest relation differs")

    stable_to_cp69_rule = cross_by_id[
        "independent-raw-to-stable-reprojection-to-postexecution-independent-recomputation"
    ]
    if (
        stable_to_cp69_rule.preimage_or_equality_formula
        != _STABLE_TO_CP69_TO_CP71_CANDIDATE_FORMULA
        or not all(
            fragment in stable_to_cp69_rule.preimage_or_equality_formula
            for fragment in (
                "cp69-test28-compact-projection-interchange-qualification-v1",
                "cp63-test28-independent-compact-recomputation-v1",
                "plain-SHA256-of-the-exact-canonical-CP74-stable-record-bytes-before-LF",
                "cp69-test28-compact-interchange-observation-v1\\0",
                "record_sha256-set-to-64-zero-hex-characters",
                "reduce-the-exact-32768-record-byte-stream-once",
            )
        )
    ):
        raise RuntimeError("CP74 stable-to-CP69-to-CP71 derivation differs")

    runtime_rule = cross_by_id[
        "frozen-runtime-lock-and-production-runtime-receipt-to-shard-raw-records"
    ]
    if (
        runtime_rule.source_artifact_ids
        != ("frozen-machine-manifest", "production-runtime-receipt")
        or "/runtime_lock_sha256" in runtime_rule.source_pointer_or_components
        or "production-runtime-receipt-has-no-runtime_lock_sha256-field"
        not in runtime_rule.preimage_or_equality_formula
    ):
        raise RuntimeError("CP74 runtime-lock source relation differs")
    primary_rule = cross_by_id[
        "postexecution-independent-recomputation-to-primary-metrics"
    ]
    decision_rule = cross_by_id["primary-metrics-and-power-thresholds-to-decisions"]
    if (
        not all(
            fragment in primary_rule.preimage_or_equality_formula
            for fragment in (
                "primary.power_threshold_receipt_sha256",
                "power_review_signoff_sha256",
            )
        )
        or not any(
            "/ordered_slot_thresholds" in component
            for component in primary_rule.source_pointer_or_components
        )
        or not all(
            fragment in decision_rule.preimage_or_equality_formula
            for fragment in (
                "primary-metrics.power_threshold_receipt_sha256",
                "decisions-power-threshold-receipt-and-power-review-signoff-SHA-fields",
                "therefore-equal-the-primary-root-fields",
            )
        )
    ):
        raise RuntimeError("CP74 power/primary/decision cross-binding differs")


def _build_bundle() -> CP74ProductionOccurrenceOutputSchemaCandidateBundleV1:
    custody = _predecessor_custody()
    contract = _candidate_contract()
    lifecycle = _build_lifecycle_rules()
    cuts = _build_crash_cut_rules()
    occurrences = _build_artifact_occurrence_rules()
    outputs = _build_execution_output_semantic_rules(occurrences)
    cross = _build_cross_binding_rules()
    _validate_internal_definition(lifecycle, cuts, occurrences, outputs, cross)
    ordered_lifecycle = _ordered_record_digest(lifecycle)
    ordered_cuts = _ordered_record_digest(cuts)
    ordered_occurrences = _ordered_record_digest(occurrences)
    ordered_outputs = _ordered_record_digest(outputs)
    ordered_cross = _ordered_record_digest(cross)
    semantic = hashlib.sha256(
        _CANDIDATE_SEMANTIC_DOMAIN
        + bytes.fromhex(ordered_lifecycle)
        + bytes.fromhex(ordered_cuts)
        + bytes.fromhex(ordered_occurrences)
        + bytes.fromhex(ordered_outputs)
        + bytes.fromhex(ordered_cross)
        + CP74_TEST28_ARTIFACT_COUNT.to_bytes(2, "big")
        + CP74_TEST28_REFERENCED_OUTPUT_COUNT.to_bytes(2, "big")
        + CP74_TEST28_LIFECYCLE_BRANCH_COUNT.to_bytes(2, "big")
        + CP74_TEST28_CRASH_CUT_COUNT.to_bytes(2, "big")
        + CP74_TEST28_OUTPUT_CROSS_BINDING_COUNT.to_bytes(2, "big")
    ).hexdigest()
    return cast(
        CP74ProductionOccurrenceOutputSchemaCandidateBundleV1,
        _record(
            CP74ProductionOccurrenceOutputSchemaCandidateBundleV1,
            {
                "schema_version": CP74_TEST28_SCHEMA_VERSION,
                "scope": CP74_TEST28_SCOPE,
                "predecessor_custody": custody,
                "contract": contract,
                "lifecycle_branch_rules": lifecycle,
                "crash_cut_rules": cuts,
                "artifact_occurrence_rules": occurrences,
                "execution_output_semantic_rules": outputs,
                "output_cross_binding_rules": cross,
                "lifecycle_branch_count": len(lifecycle),
                "crash_cut_count": len(cuts),
                "artifact_occurrence_rule_count": len(occurrences),
                "execution_output_semantic_rule_count": len(outputs),
                "output_cross_binding_rule_count": len(cross),
                "ordered_lifecycle_branch_record_sha256": ordered_lifecycle,
                "ordered_crash_cut_record_sha256": ordered_cuts,
                "ordered_artifact_occurrence_record_sha256": ordered_occurrences,
                "ordered_execution_output_semantic_record_sha256": ordered_outputs,
                "ordered_output_cross_binding_record_sha256": ordered_cross,
                "candidate_schema_semantic_sha256": semantic,
                "all_record_digests_valid": True,
                "all_inventories_complete": True,
                "all_occurrence_expressions_closed": True,
                "all_cross_bindings_resolve": True,
                "authoritative_builder_validates_internal_definition": True,
                "authoritative_builder_accepts_production_data": False,
                "candidate_descriptor_packet_internally_consistent": True,
                "candidate_descriptor_definition_complete": True,
                "candidate_schema_executable": False,
                "primary_decision_semantics_resolved": False,
                "primary_decision_semantics_deferred_to_external_power_review": True,
                "schema_acceptance_independent": False,
                "authoritative_for_production": False,
                "production_schema_frozen": False,
                "production_execution_and_output_schema_frozen": False,
                "production_receipt_schema_frozen": False,
                "production_evidence_accepted": False,
                "production_gate_states": _MISSING_GATE_STATES,
                "draft_blocker_states": _MISSING_BLOCKER_STATES,
                "formal_test_28_status": CP74_TEST28_FORMAL_TEST_28_STATUS,
                "formal_test_28_closed": False,
            },
        ),
    )


def cp74_canonical_json_bytes(value: object) -> bytes:
    """Serialize one live, issued CP74 record canonically."""

    if not isinstance(value, _SealedRecord):
        raise TypeError("CP74 canonical serialization accepts issued records only")
    with _ISSUED_RECORD_LOCK:
        snapshot = _ISSUED_RECORD_SNAPSHOTS.get(value)
    if snapshot is None:
        raise ValueError("CP74 record was not issued or is no longer registered")
    current = _plain_json_bytes(value)
    if current != snapshot:
        raise ValueError("CP74 issued record was tampered")
    return snapshot


def cp74_sha256(value: object) -> str:
    """Return the domain-separated public digest of one issued CP74 record."""

    canonical = cp74_canonical_json_bytes(value)
    return hashlib.sha256(
        _PUBLIC_RECORD_DOMAIN + type(value).__name__.encode("ascii") + b"\0" + canonical
    ).hexdigest()


def cp74_production_occurrence_output_schema_candidate_bundle() -> CP74ProductionOccurrenceOutputSchemaCandidateBundleV1:
    """Return the deterministic descriptor-only CP74 candidate bundle."""

    return _build_bundle()


__all__ = (
    "CP74_TEST28_SCHEMA_VERSION",
    "CP74_TEST28_SCOPE",
    "CP74_TEST28_FORMAL_TEST_28_STATUS",
    "CP74_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID",
    "CP74_TEST28_ARTIFACT_COUNT",
    "CP74_TEST28_REFERENCED_OUTPUT_COUNT",
    "CP74_TEST28_LIFECYCLE_BRANCH_COUNT",
    "CP74_TEST28_CRASH_CUT_COUNT",
    "CP74_TEST28_OUTPUT_CROSS_BINDING_COUNT",
    "CP74_TEST28_SHARD_COUNT",
    "CP74_TEST28_SEED_COUNT",
    "CP74_TEST28_ROW_COUNT",
    "CP74_TEST28_REQUEST_COUNT",
    "CP74_TEST28_ESTIMAND_COUNT",
    "CP74_TEST28_PRODUCTION_GATE_COUNT",
    "CP74_TEST28_BLOCKER_LEDGER_TOTAL_COUNT",
    "CP74_TEST28_BLOCKER_LEDGER_SATISFIED_COUNT",
    "CP74_TEST28_BLOCKER_LEDGER_MISSING_COUNT",
    "CP74PredecessorCustodyV1",
    "CP74LifecycleBranchRuleV1",
    "CP74CrashCutRuleV1",
    "CP74ArtifactOccurrenceRuleV1",
    "CP74ExecutionOutputSemanticRuleV1",
    "CP74OutputCrossBindingRuleV1",
    "CP74CandidateSchemaContractV1",
    "CP74ProductionOccurrenceOutputSchemaCandidateBundleV1",
    "cp74_production_occurrence_output_schema_candidate_bundle",
    "cp74_canonical_json_bytes",
    "cp74_sha256",
)
