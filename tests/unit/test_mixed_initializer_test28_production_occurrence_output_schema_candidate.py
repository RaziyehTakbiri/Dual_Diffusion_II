"""Independent hostile tests for the CP74 authoritative candidate descriptor."""

from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, is_dataclass
import gc
import hashlib
import inspect
import json
import pickle
from pathlib import Path
import subprocess
from typing import Dict, List, Tuple
import weakref

import heterodiff.evaluation.mixed_initializer_test28_production_occurrence_output_schema_candidate as cp74
import pytest


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_production_occurrence_output_schema_candidate.py"
)
_PYTHON39 = Path("/Users/mahtab/opt/anaconda3/bin/python3.9")

_SCHEMA = "cp74-test28-production-occurrence-output-schema-candidate-v1"
_PREREQUISITE_ID = (
    "whole_seed_candidate_production_artifact_occurrence_branch_and_execution_"
    "output_schema_definition"
)
_ALL = (
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
_OUTPUT_ARTIFACT_IDS = (
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
_STOCHASTIC_OR_POSTEXECUTION_OUTPUT_ARTIFACT_IDS = _OUTPUT_ARTIFACT_IDS[1:]
_CROSS_BINDING_IDS = (
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
_STABLE_TO_CP69_TO_CP71_FORMULA = (
    "independently-reproject-every-hashed-raw-record-using-the-candidate-"
    "projection-and-rebuild-every-stable-file-before-setting-the-flag-true;"
    "for-each-exact-CP74-stable-record-in-logical-request-ordinal-order-1-"
    "through-32768-apply-the-frozen-CP63-compact-semantic-projection-field-by-"
    "field-without-calling-or-claiming-the-CP63-rehearsal-only-parser;the-"
    "transient-semantic-view-replaces-the-CP74-returned-or-closed-trace_schema-"
    "with-the-corresponding-CP62-trace_schema-renames-request_instance_sha256-"
    "to-calibration_instance_sha256-renames-cp74_semantic_trace_sha256-or-"
    "cp74_closed_trace_sha256-to-the-corresponding-CP62-carrier-and-recomputes-"
    "that-omitted-carrier-CP62-terminal-digest-solely-to-replay-the-frozen-CP63-"
    "semantic-projection-while-the-CP74-attempt-and-request-custody-values-"
    "remain-unchanged;derive-selected_configuration-first_selected_attempt_one_"
    "based-observable_cell_label-observable_contribution_ordinal-selected_"
    "feature_ids-and-exact-Fraction-selected_feature_values-by-the-frozen-CP63-"
    "selected-configuration-contribution-ordinal-and-feature-vector-formulas;"
    "construct-one-exact-21-key-CP69-record;set-schema_version=cp69-test28-"
    "compact-projection-interchange-qualification-v1;set-source_semantic_schema_"
    "version=cp63-test28-independent-compact-recomputation-v1;copy-(seed_"
    "ordinal,row_ordinal,logical_request_ordinal,row_key,fixture_id,strategy,"
    "budget,plan_seed_hex,seed_free_request_sha256,request_instance_sha256,"
    "runtime_lock_sha256)-from-the-validated-CP74-stable-record;set-CP69-stable_"
    "trace_sha256-to-plain-SHA256-of-the-exact-canonical-CP74-stable-record-"
    "bytes-before-LF-not-the-old-CP63-rehearsal-domain-digest;set-observable_"
    "cell_label=closed_status;set-selected=true-only-for-returned-rejection-"
    "selected-before-deadline-or-returned-sir-selected-before-deadline-and-"
    "false-otherwise;set-first_selected_attempt_one_based=selected_index+1-"
    "only-for-selected-bounded-rejection-and-null-otherwise;set-(selected_"
    "feature_ids,selected_feature_values)=the-exact-CP63-feature-projection-for-"
    "selected_configuration-or-two-empty-vectors-otherwise;set-record_sha256-"
    "to-SHA256(cp69-test28-compact-interchange-observation-v1\\0||ASCII-"
    "canonical-JSON-of-the-exact-21-key-record-with-record_sha256-set-to-64-"
    "zero-hex-characters);canonicalize-each-CP69-record-with-zero-trailing-"
    "bytes-and-reduce-the-exact-32768-record-byte-stream-once-through-the-"
    "development-structural-CP71-reducer-in-logical-request-ordinal-order;cp71_"
    "output_canonical_json_sha256-equals-plain-SHA256-of-the-exact-rebuilt-CP71-"
    "output-bytes;CP72-and-CP73-public-summary-fields-equal-their-exact-class-"
    "name-domain-separated-public-digests-for-that-output-and-stream-but-"
    "remain-noncustodial-development-structural-references"
)
_OCCURRENCE_EXPRESSIONS = (
    "ABSENT",
    "EXACT_GLOBAL_ONE",
    "EXACT_ALL_32_SHARDS",
    "DURABLE_PREFIX_DEPENDENCY_CLOSED",
    "IFF_PARTIAL_ACQUISITION_TERMINAL",
    "IFF_REJECTED_AUTHORIZATION_CANDIDATE",
)
_OUTPUT_SCHEMA_IDS = (
    "cp74-test28-production-environment-candidate-v1",
    "cp74-test28-production-primary-metrics-candidate-v1",
    "cp74-test28-production-secondary-diagnostics-candidate-v1",
    "cp74-test28-production-independent-recomputation-candidate-v1",
    "cp74-test28-production-decisions-candidate-v1",
    "cp74-test28-production-deviations-candidate-v1",
    "cp74-test28-production-failures-candidate-v1",
    "cp74-test28-production-exclusions-candidate-v1",
    "cp74-test28-production-reruns-candidate-v1",
    "cp74-test28-production-shard-request-jsonl-candidate-v1",
    "cp74-test28-production-raw-record-jsonl-candidate-v1",
    "cp74-test28-production-stable-trace-jsonl-candidate-v1",
    "cp74-test28-production-stderr-frame-stream-candidate-v1",
    "cp74-test28-production-rng-initial-state-container-candidate-v1",
    "cp74-test28-production-rng-final-state-container-candidate-v1",
)
_LEDGER_ROOT_KEYS = (
    "schema",
    "purpose",
    "attempt_id",
    "entry_count",
    "entries",
    "ordered_entries_sha256",
    "body_sha256",
)
_OUTPUT_TOP_LEVEL_KEYS = (
    (
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
    (
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
    (
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
    (
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
    (
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
    _LEDGER_ROOT_KEYS,
    _LEDGER_ROOT_KEYS,
    _LEDGER_ROOT_KEYS,
    _LEDGER_ROOT_KEYS,
    (
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
    ),
    (
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
    ),
    (
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
    ),
    (),
    (
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
    ),
    (
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
    ),
)
_CONDITIONAL_RULE_IDS = (
    "partial-acquisition-terminal-receipt-required-iff-acquisition-start-committed-and-complete-source-receipt-absent",
    "rejected-launch-authorization-candidate-required-iff-preauthorization-terminal-arm-wins-after-durable-prepared-authorization-candidate-exists",
)
_CP65_GATE_EVIDENCE_DAG_NODES = (
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
    "independent-full-32768-recomputation-qualification-receipt",
    "independent-554-estimate-interval-decision-path-qualification-receipt",
    "preflight-gate-summary",
    "independent-signoff-set",
    "launch-authorization",
)
_CP65_GATE_EVIDENCE_DAG_EDGES = (
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
_FROZEN_BEFORE_ACQUISITION_ARTIFACT_SET = frozenset(
    (
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
)
_GATE17_REQUIRED_ARTIFACT_SET = _FROZEN_BEFORE_ACQUISITION_ARTIFACT_SET | {
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
}


def _inventory_ordered(artifact_set: set) -> tuple:
    assert artifact_set <= set(_ARTIFACT_IDS)
    return tuple(
        artifact_id for artifact_id in _ARTIFACT_IDS if artifact_id in artifact_set
    )


_FROZEN_BEFORE_ACQUISITION_ARTIFACT_IDS = _inventory_ordered(
    set(_FROZEN_BEFORE_ACQUISITION_ARTIFACT_SET)
)
_GATE17_REQUIRED_ARTIFACT_IDS = _inventory_ordered(set(_GATE17_REQUIRED_ARTIFACT_SET))
_CUT1_AND_CUT2_REQUIRED_ARTIFACT_IDS = _inventory_ordered(
    set(_FROZEN_BEFORE_ACQUISITION_ARTIFACT_SET)
    | {
        "dependency-lock-match-receipt",
        "production-runtime-receipt",
        "external-seed-acquisition-start-receipt",
        "external-seed-acquisition-journal",
        "seed-source-custody-artifact",
        "seed-source-authority-attestation",
        "environment",
    }
)
_CUT3_REQUIRED_ARTIFACT_IDS = _inventory_ordered(
    set(_CUT1_AND_CUT2_REQUIRED_ARTIFACT_IDS)
    | {"external-seed-source-receipt", "seed-capsule-body"}
)
_CUT4_REQUIRED_ARTIFACT_IDS = _inventory_ordered(
    set(_CUT3_REQUIRED_ARTIFACT_IDS)
    | {
        "seed-capsule-sequence-crosscheck-receipt",
        "production-schedule",
        "auxiliary-metadata-reservation",
        "reservation-manifest",
        "capacity-receipt",
        "durability-receipt",
        "production-shard-map-receipt",
    }
)
_CUT5_REQUIRED_ARTIFACT_IDS = _inventory_ordered(
    set(_GATE17_REQUIRED_ARTIFACT_SET) | {"environment"}
)
_CUT6_REQUIRED_ARTIFACT_IDS = _inventory_ordered(
    set(_CUT5_REQUIRED_ARTIFACT_IDS) | {"postauthorization-outcome"}
)
_PREAUTHORIZATION_PREFIX_IDS = frozenset(
    (
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
        "external-seed-source-receipt",
        "seed-capsule-body",
        "seed-capsule-sequence-crosscheck-receipt",
        "production-schedule",
        "production-shard-map-receipt",
        "durability-receipt",
    )
)
_SHARD_CLOSURE_IDS = ("shard-index", "shard-receipt")
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


def _key_rule(label: str, keys: tuple) -> str:
    return "%s=(%s)" % (label, ",".join(keys))


_RAW_NESTED_KEY_RULES = (
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


def _expected_branch_expression(artifact_id: str, branch_id: str) -> str:
    preauthorization = branch_id.startswith("preauthorization-")
    prestart = branch_id.startswith("postauthorization-prestart-")
    started = not preauthorization and not prestart
    complete = branch_id in ("started-pass", "started-fail")
    if artifact_id == "environment":
        return (
            "DURABLE_PREFIX_DEPENDENCY_CLOSED"
            if preauthorization
            else "EXACT_GLOBAL_ONE"
        )
    if artifact_id in _OUTPUT_ARTIFACT_IDS:
        if not started:
            return "ABSENT"
        if complete:
            return (
                "EXACT_ALL_32_SHARDS"
                if artifact_id.startswith("shard-")
                else "EXACT_GLOBAL_ONE"
            )
        return "DURABLE_PREFIX_DEPENDENCY_CLOSED"
    if artifact_id in _SHARD_CLOSURE_IDS:
        if not started:
            return "ABSENT"
        return "EXACT_ALL_32_SHARDS" if complete else "DURABLE_PREFIX_DEPENDENCY_CLOSED"
    if artifact_id == "partial-seed-acquisition-terminal-receipt":
        return "IFF_PARTIAL_ACQUISITION_TERMINAL" if preauthorization else "ABSENT"
    if artifact_id == "rejected-launch-authorization-candidate":
        return "IFF_REJECTED_AUTHORIZATION_CANDIDATE" if preauthorization else "ABSENT"
    if artifact_id in _PREAUTHORIZATION_PREFIX_IDS:
        return (
            "DURABLE_PREFIX_DEPENDENCY_CLOSED"
            if preauthorization
            else "EXACT_GLOBAL_ONE"
        )
    if artifact_id in ("launch-authorization", "postauthorization-outcome"):
        return "ABSENT" if preauthorization else "EXACT_GLOBAL_ONE"
    if artifact_id in ("started-receipt", "launch-receipt"):
        return "EXACT_GLOBAL_ONE" if started else "ABSENT"
    return "EXACT_GLOBAL_ONE"


def _plain(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {item.name: _plain(getattr(value, item.name)) for item in fields(value)}
    if type(value) in (tuple, list):
        return [_plain(item) for item in value]
    if type(value) is dict:
        return {key: _plain(item) for key, item in value.items()}
    if value is None or type(value) in (bool, int, str):
        return value
    raise AssertionError("unsupported independent CP74 value: %r" % (type(value),))


def _canonical(value: object) -> bytes:
    return json.dumps(
        _plain(value),
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _record_digest(record: object, domain: bytes) -> str:
    body = _plain(record)
    assert type(body) is dict
    body["record_sha256"] = "0" * 64
    return hashlib.sha256(domain + _canonical(body)).hexdigest()


def _unissued_copy(record: object) -> object:
    clone = object.__new__(type(record))
    for item in fields(record):
        object.__setattr__(clone, item.name, getattr(record, item.name))
    return clone


_RECORD_DOMAINS = {
    cp74.CP74PredecessorCustodyV1: b"cp74-test28-predecessor-custody-v1\0",
    cp74.CP74LifecycleBranchRuleV1: b"cp74-test28-lifecycle-branch-rule-v1\0",
    cp74.CP74CrashCutRuleV1: b"cp74-test28-crash-cut-rule-v1\0",
    cp74.CP74ArtifactOccurrenceRuleV1: b"cp74-test28-artifact-occurrence-rule-v1\0",
    cp74.CP74ExecutionOutputSemanticRuleV1: (
        b"cp74-test28-execution-output-semantic-rule-v1\0"
    ),
    cp74.CP74OutputCrossBindingRuleV1: (b"cp74-test28-output-cross-binding-rule-v1\0"),
    cp74.CP74CandidateSchemaContractV1: (b"cp74-test28-candidate-schema-contract-v1\0"),
    cp74.CP74ProductionOccurrenceOutputSchemaCandidateBundleV1: (
        b"cp74-test28-production-occurrence-output-schema-candidate-bundle-v1\0"
    ),
}
_ORDERED_DOMAINS = {
    cp74.CP74LifecycleBranchRuleV1: (
        b"cp74-test28-ordered-lifecycle-branch-rule-digests-v1\0"
    ),
    cp74.CP74CrashCutRuleV1: (b"cp74-test28-ordered-crash-cut-rule-digests-v1\0"),
    cp74.CP74ArtifactOccurrenceRuleV1: (
        b"cp74-test28-ordered-artifact-occurrence-rule-digests-v1\0"
    ),
    cp74.CP74ExecutionOutputSemanticRuleV1: (
        b"cp74-test28-ordered-execution-output-semantic-rule-digests-v1\0"
    ),
    cp74.CP74OutputCrossBindingRuleV1: (
        b"cp74-test28-ordered-output-cross-binding-rule-digests-v1\0"
    ),
}


_PREDECESSOR_FIELDS = (
    "schema_version",
    "v24_protocol_markdown_path",
    "v24_protocol_markdown_sha256",
    "v24_protocol_markdown_bytes",
    "v24_protocol_markdown_lf_count",
    "v24_machine_manifest_path",
    "v24_machine_manifest_sha256",
    "v24_machine_manifest_bytes",
    "v24_machine_manifest_lf_count",
    "predecessor_component_ids",
    "predecessor_source_paths",
    "predecessor_source_sha256s",
    "predecessor_bundle_record_sha256s",
    "predecessor_bundle_public_sha256s",
    "cp65_artifact_id_order_sha256",
    "cp65_artifact_schema_record_order_sha256",
    "cp65_referenced_output_id_order_sha256",
    "cp65_schema_semantic_sha256",
    "cp65_gate_evidence_dag_node_count",
    "cp65_gate_evidence_dag_edge_count",
    "cp65_gate_evidence_dag_semantic_sha256",
    "cp65_gate_evidence_dag_is_not_full_typed_graph",
    "cp65_gate_evidence_artifact_id_aliases",
    "cp65_typed_artifact_preimage_graph_vector_lengths",
    "cp65_typed_artifact_preimage_graph_semantic_sha256",
    "cp65_typed_digest_graph_inherited_by_hash_reference_only",
    "cp65_typed_digest_graph_revalidated_by_cp74",
    "custody_is_hash_reference_only",
    "predecessor_runtime_imports_performed",
    "production_artifacts_observed",
    "record_sha256",
)
_LIFECYCLE_FIELDS = (
    "schema_version",
    "branch_ordinal",
    "branch_id",
    "branch_phase",
    "terminal_state",
    "preauthorization_outcome_arm",
    "postauthorization_outcome_arm",
    "always_required_artifact_ids",
    "always_forbidden_artifact_ids",
    "durable_prefix_artifact_ids",
    "allowed_crash_cut_ids",
    "started_arm_crash_recovery_rule",
    "terminal_arm_crash_recovery_rule",
    "production_rng_or_child_permitted",
    "retry_redraw_topup_or_reselection_permitted",
    "terminal_state_record_required",
    "sha256_manifest_required",
    "committed_marker_required",
    "candidate_only",
    "record_sha256",
)
_CRASH_FIELDS = (
    "schema_version",
    "crash_cut_ordinal",
    "crash_cut_id",
    "crash_cut_phase",
    "applicable_branch_ids",
    "required_durable_artifact_ids",
    "forbidden_artifact_ids",
    "conditional_artifact_ids",
    "recovery_rule",
    "terminal_state_rule",
    "production_rng_or_child_permitted",
    "retry_redraw_topup_or_reselection_permitted",
    "candidate_only",
    "record_sha256",
)
_OCCURRENCE_FIELDS = (
    "schema_version",
    "artifact_ordinal",
    "artifact_id",
    "cp65_schema_version",
    "cp65_artifact_schema_record_sha256",
    "path_template",
    "path_scope",
    "presence_rule_id",
    "encoding",
    "media_kind",
    "exact_keys",
    "field_rule_ids",
    "record_rule_id",
    "cp65_minimum_instances",
    "cp65_maximum_instances",
    "minimum_bytes_per_instance",
    "maximum_bytes_per_instance",
    "final_newline_rule",
    "digest_preimage_contract_id",
    "dag_node_ids",
    "auxiliary_reservation_class",
    "cp64_contract_preserved",
    "cp65_definition_only",
    "branch_occurrence_expressions",
    "conditional_occurrence_rule_ids",
    "dependency_predecessor_artifact_ids",
    "retained_if_durable",
    "manifest_bound_if_present",
    "committed_marker_transitively_binds_if_present",
    "conditional_rules_closed",
    "candidate_only",
    "record_sha256",
)
_OUTPUT_FIELDS = (
    "schema_version",
    "output_ordinal",
    "artifact_id",
    "cp65_artifact_schema_record_sha256",
    "path_template",
    "path_scope",
    "media_kind",
    "output_schema_id",
    "canonical_encoding",
    "framing_rule",
    "final_terminator_rule",
    "complete_attempt_instance_count",
    "complete_attempt_units_per_instance",
    "complete_attempt_total_unit_count",
    "ordering_rule",
    "exact_top_level_keys",
    "nested_schema_rules",
    "field_semantic_rules",
    "record_identity_fields",
    "closed_outcome_arms",
    "record_digest_domain",
    "ordered_record_digest_domain",
    "body_digest_domain",
    "source_contract_ids",
    "cross_binding_rule_ids",
    "production_values_present",
    "candidate_only",
    "record_sha256",
)
_CROSS_BINDING_FIELDS = (
    "schema_version",
    "rule_ordinal",
    "rule_id",
    "source_artifact_ids",
    "source_pointer_or_components",
    "target_artifact_ids",
    "target_pointer_or_components",
    "digest_or_equality_kind",
    "preimage_or_equality_formula",
    "cardinality_rule",
    "ordering_rule",
    "required_in_complete_attempt",
    "candidate_only",
    "record_sha256",
)
_CONTRACT_FIELDS = (
    "schema_version",
    "scope",
    "canonical_profile_id",
    "artifact_count",
    "receipt_envelope_artifact_count",
    "referenced_output_artifact_count",
    "frozen_or_binary_custody_artifact_count",
    "lifecycle_branch_count",
    "crash_cut_count",
    "output_cross_binding_count",
    "shard_count",
    "seed_count",
    "row_count",
    "request_count",
    "estimand_count",
    "primary_gate_slot_count",
    "artifact_ids",
    "lifecycle_branch_ids",
    "crash_cut_ids",
    "referenced_output_artifact_ids",
    "output_cross_binding_rule_ids",
    "branch_occurrence_expression_enum",
    "conditional_occurrence_rule_ids",
    "all_cp65_artifact_descriptors_preserved",
    "all_artifact_occurrences_closed",
    "all_branch_arms_mutually_exclusive_and_exhaustive",
    "all_conditional_occurrence_rules_closed",
    "all_output_envelope_framing_and_cross_binding_descriptors_candidate_complete",
    "all_cross_bindings_candidate_complete",
    "descriptor_bodies_only",
    "production_output_bodies_accepted",
    "public_caller_data_api_exposed",
    "project_modules_imported",
    "stdlib_only",
    "module_direct_filesystem_io",
    "module_direct_clock",
    "module_direct_rng",
    "module_direct_network",
    "module_direct_subprocess",
    "candidate_schema_inventory_complete",
    "candidate_descriptor_definition_complete",
    "primary_decision_semantics_resolved",
    "primary_decision_semantics_deferred_to_external_power_review",
    "independent_structural_validator_required",
    "schema_acceptance_independent",
    "authoritative_for_production",
    "production_schema_frozen",
    "production_execution_and_output_schema_frozen",
    "production_receipt_schema_frozen",
    "production_artifacts_observed",
    "production_evidence_accepted",
    "gate_ids",
    "gate_states",
    "blocker_ids",
    "blocker_states",
    "blocker_ledger_total_count",
    "blocker_ledger_satisfied_count",
    "blocker_ledger_missing_count",
    "formal_test_28_status",
    "formal_test_28_closed",
    "record_sha256",
)
_BUNDLE_FIELDS = (
    "schema_version",
    "scope",
    "predecessor_custody",
    "contract",
    "lifecycle_branch_rules",
    "crash_cut_rules",
    "artifact_occurrence_rules",
    "execution_output_semantic_rules",
    "output_cross_binding_rules",
    "lifecycle_branch_count",
    "crash_cut_count",
    "artifact_occurrence_rule_count",
    "execution_output_semantic_rule_count",
    "output_cross_binding_rule_count",
    "ordered_lifecycle_branch_record_sha256",
    "ordered_crash_cut_record_sha256",
    "ordered_artifact_occurrence_record_sha256",
    "ordered_execution_output_semantic_record_sha256",
    "ordered_output_cross_binding_record_sha256",
    "candidate_schema_semantic_sha256",
    "all_record_digests_valid",
    "all_inventories_complete",
    "all_occurrence_expressions_closed",
    "all_cross_bindings_resolve",
    "authoritative_builder_validates_internal_definition",
    "authoritative_builder_accepts_production_data",
    "candidate_descriptor_packet_internally_consistent",
    "candidate_descriptor_definition_complete",
    "candidate_schema_executable",
    "primary_decision_semantics_resolved",
    "primary_decision_semantics_deferred_to_external_power_review",
    "schema_acceptance_independent",
    "authoritative_for_production",
    "production_schema_frozen",
    "production_execution_and_output_schema_frozen",
    "production_receipt_schema_frozen",
    "production_evidence_accepted",
    "production_gate_states",
    "draft_blocker_states",
    "formal_test_28_status",
    "formal_test_28_closed",
    "record_sha256",
)

_RECORD_LAYOUTS = (
    (cp74.CP74PredecessorCustodyV1, _PREDECESSOR_FIELDS),
    (cp74.CP74LifecycleBranchRuleV1, _LIFECYCLE_FIELDS),
    (cp74.CP74CrashCutRuleV1, _CRASH_FIELDS),
    (cp74.CP74ArtifactOccurrenceRuleV1, _OCCURRENCE_FIELDS),
    (cp74.CP74ExecutionOutputSemanticRuleV1, _OUTPUT_FIELDS),
    (cp74.CP74OutputCrossBindingRuleV1, _CROSS_BINDING_FIELDS),
    (cp74.CP74CandidateSchemaContractV1, _CONTRACT_FIELDS),
    (
        cp74.CP74ProductionOccurrenceOutputSchemaCandidateBundleV1,
        _BUNDLE_FIELDS,
    ),
)


def _import_roots(tree: ast.AST) -> Tuple[str, ...]:
    roots = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.append(node.module.split(".")[0])
    return tuple(roots)


def test_public_surface_and_fixed_counts_are_exact() -> None:
    assert cp74.__all__ == _ALL
    assert len(cp74.__all__) == len(set(cp74.__all__)) == 29
    assert cp74.CP74_TEST28_SCHEMA_VERSION == _SCHEMA
    assert cp74.CP74_TEST28_FORMAL_TEST_28_STATUS == "OPEN"
    assert cp74.CP74_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID == _PREREQUISITE_ID
    assert (
        cp74.CP74_TEST28_ARTIFACT_COUNT,
        cp74.CP74_TEST28_REFERENCED_OUTPUT_COUNT,
        cp74.CP74_TEST28_LIFECYCLE_BRANCH_COUNT,
        cp74.CP74_TEST28_CRASH_CUT_COUNT,
        cp74.CP74_TEST28_OUTPUT_CROSS_BINDING_COUNT,
    ) == (64, 15, 11, 6, 24)
    assert (
        cp74.CP74_TEST28_SHARD_COUNT,
        cp74.CP74_TEST28_SEED_COUNT,
        cp74.CP74_TEST28_ROW_COUNT,
        cp74.CP74_TEST28_REQUEST_COUNT,
        cp74.CP74_TEST28_ESTIMAND_COUNT,
    ) == (32, 2_048, 16, 32_768, 554)
    assert cp74.CP74_TEST28_PRODUCTION_GATE_COUNT == 17
    assert (
        cp74.CP74_TEST28_BLOCKER_LEDGER_TOTAL_COUNT,
        cp74.CP74_TEST28_BLOCKER_LEDGER_SATISFIED_COUNT,
        cp74.CP74_TEST28_BLOCKER_LEDGER_MISSING_COUNT,
    ) == (29, 25, 4)


@pytest.mark.parametrize(("record_type", "expected_fields"), _RECORD_LAYOUTS)
def test_record_layouts_are_exact(record_type: type, expected_fields: tuple) -> None:
    assert is_dataclass(record_type)
    assert tuple(item.name for item in fields(record_type)) == expected_fields
    assert record_type.__slots__ == expected_fields
    with pytest.raises(TypeError, match="module-created only"):
        record_type()
    with pytest.raises(TypeError, match="cannot be subclassed"):
        type("HostileSubclass", (record_type,), {})


def test_public_signatures_are_narrow() -> None:
    builder_signature = inspect.signature(
        cp74.cp74_production_occurrence_output_schema_candidate_bundle
    )
    assert tuple(builder_signature.parameters) == ()
    assert (
        builder_signature.return_annotation
        == "CP74ProductionOccurrenceOutputSchemaCandidateBundleV1"
    )
    for function in (cp74.cp74_canonical_json_bytes, cp74.cp74_sha256):
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == ("value",)
        assert signature.parameters["value"].annotation == "object"


def test_scope_pins_candidate_only_nonclaims() -> None:
    scope = cp74.CP74_TEST28_SCOPE
    required_phrases = (
        "development-only-definition-of-a-production-occurrence-output-schema-candidate",
        "descriptor-bodies-only",
        "primary-decision-semantics-unresolved-and-deferred-to-external-power-review",
        "no-independent-schema-acceptance",
        "no-production-schema-freeze",
        "no-production-artifact-observation",
        "no-caller-data-parser-path-writer-runner-or-io-api",
        "project-modules-not-imported",
    )
    assert all(phrase in scope for phrase in required_phrases)
    assert "production-schema-frozen" not in scope
    assert "production-evidence-accepted" not in scope


def test_source_imports_only_the_declared_standard_library_surface() -> None:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"), filename=str(_SOURCE))
    assert set(_import_roots(tree)) == {
        "__future__",
        "base64",
        "dataclasses",
        "hashlib",
        "json",
        "threading",
        "typing",
        "weakref",
        "zlib",
    }
    forbidden_names = {
        "open",
        "Path",
        "socket",
        "subprocess",
        "time",
        "datetime",
        "random",
        "secrets",
        "urandom",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert forbidden_names.isdisjoint(called_names)


@pytest.mark.parametrize("value", ({}, [], (), b"", "", 0, False, None))
def test_canonical_and_digest_apis_reject_unissued_values(value: object) -> None:
    with pytest.raises(TypeError, match="issued records only"):
        cp74.cp74_canonical_json_bytes(value)
    with pytest.raises(TypeError, match="issued records only"):
        cp74.cp74_sha256(value)


def test_bundle_inventories_counts_and_builder_determinism_are_exact() -> None:
    first = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    second = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    assert first is not second
    assert first.record_sha256 == second.record_sha256
    assert cp74.cp74_sha256(first) == cp74.cp74_sha256(second)
    assert first.schema_version == first.contract.schema_version == _SCHEMA
    assert first.scope == first.contract.scope == cp74.CP74_TEST28_SCOPE
    assert first.contract.artifact_ids == _ARTIFACT_IDS
    assert first.contract.lifecycle_branch_ids == _LIFECYCLE_BRANCH_IDS
    assert first.contract.crash_cut_ids == _CRASH_CUT_IDS
    assert first.contract.referenced_output_artifact_ids == _OUTPUT_ARTIFACT_IDS
    assert first.contract.output_cross_binding_rule_ids == _CROSS_BINDING_IDS
    assert first.contract.branch_occurrence_expression_enum == _OCCURRENCE_EXPRESSIONS
    assert first.contract.conditional_occurrence_rule_ids == _CONDITIONAL_RULE_IDS
    assert (
        first.lifecycle_branch_count,
        first.crash_cut_count,
        first.artifact_occurrence_rule_count,
        first.execution_output_semantic_rule_count,
        first.output_cross_binding_rule_count,
    ) == (11, 6, 64, 15, 24)
    assert tuple(row.branch_id for row in first.lifecycle_branch_rules) == (
        _LIFECYCLE_BRANCH_IDS
    )
    assert tuple(row.crash_cut_id for row in first.crash_cut_rules) == _CRASH_CUT_IDS
    assert tuple(row.artifact_id for row in first.artifact_occurrence_rules) == (
        _ARTIFACT_IDS
    )
    assert tuple(row.artifact_id for row in first.execution_output_semantic_rules) == (
        _OUTPUT_ARTIFACT_IDS
    )
    assert tuple(row.rule_id for row in first.output_cross_binding_rules) == (
        _CROSS_BINDING_IDS
    )


def test_all_cp65_artifact_descriptors_are_independently_reconstructed() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    projection = []
    cp65_digests = []
    for ordinal, row in enumerate(bundle.artifact_occurrence_rules, 1):
        assert row.artifact_ordinal == ordinal
        body = {
            "schema_version": row.cp65_schema_version,
            "artifact_id": row.artifact_id,
            "path_template": row.path_template,
            "path_scope": row.path_scope,
            "presence_rule_id": row.presence_rule_id,
            "encoding": row.encoding,
            "media_kind": row.media_kind,
            "exact_keys": row.exact_keys,
            "field_rule_ids": row.field_rule_ids,
            "record_rule_id": row.record_rule_id,
            "minimum_instances": row.cp65_minimum_instances,
            "maximum_instances": row.cp65_maximum_instances,
            "minimum_bytes_per_instance": row.minimum_bytes_per_instance,
            "maximum_bytes_per_instance": row.maximum_bytes_per_instance,
            "final_newline_rule": row.final_newline_rule,
            "digest_preimage_contract_id": row.digest_preimage_contract_id,
            "dag_node_ids": row.dag_node_ids,
            "auxiliary_reservation_class": row.auxiliary_reservation_class,
            "cp64_contract_preserved": row.cp64_contract_preserved,
            "definition_only": row.cp65_definition_only,
            "record_sha256": "0" * 64,
        }
        digest = hashlib.sha256(
            b"cp65-artifact-schema-v1\0" + _canonical(body)
        ).hexdigest()
        assert digest == row.cp65_artifact_schema_record_sha256
        body["record_sha256"] = digest
        projection.append(body)
        cp65_digests.append(digest)
    assert len(_canonical(projection)) == 118_909
    assert hashlib.sha256(_canonical(projection)).hexdigest() == (
        "ce5c83103123e9c312c2fe566bea524997f7e6287fe9329d5d0f875aedadfa7f"
    )
    custody = bundle.predecessor_custody
    assert (
        hashlib.sha256(
            b"cp74-test28-cp65-ids-order-v1\0"
            + b"".join(item.encode("ascii") for item in _ARTIFACT_IDS)
        ).hexdigest()
        == custody.cp65_artifact_id_order_sha256
    )
    assert (
        hashlib.sha256(
            b"cp74-test28-cp65-records-order-v1\0"
            + b"".join(bytes.fromhex(item) for item in cp65_digests)
        ).hexdigest()
        == custody.cp65_artifact_schema_record_order_sha256
    )
    assert (
        hashlib.sha256(
            b"cp74-test28-cp65-outs-order-v1\0"
            + b"".join(item.encode("ascii") for item in _OUTPUT_ARTIFACT_IDS)
        ).hexdigest()
        == custody.cp65_referenced_output_id_order_sha256
    )


def test_every_record_order_digest_semantic_digest_and_public_digest_recomputes() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    vectors = (
        bundle.lifecycle_branch_rules,
        bundle.crash_cut_rules,
        bundle.artifact_occurrence_rules,
        bundle.execution_output_semantic_rules,
        bundle.output_cross_binding_rules,
    )
    ordered = []
    for vector in vectors:
        domain = _ORDERED_DOMAINS[type(vector[0])]
        for record in vector:
            assert record.record_sha256 == _record_digest(
                record, _RECORD_DOMAINS[type(record)]
            )
            assert cp74.cp74_canonical_json_bytes(record) == _canonical(record)
        ordered.append(
            hashlib.sha256(
                domain
                + b"".join(bytes.fromhex(record.record_sha256) for record in vector)
            ).hexdigest()
        )
    assert tuple(ordered) == (
        bundle.ordered_lifecycle_branch_record_sha256,
        bundle.ordered_crash_cut_record_sha256,
        bundle.ordered_artifact_occurrence_record_sha256,
        bundle.ordered_execution_output_semantic_record_sha256,
        bundle.ordered_output_cross_binding_record_sha256,
    )
    assert (
        bundle.candidate_schema_semantic_sha256
        == hashlib.sha256(
            b"cp74-test28-candidate-schema-semantic-v1\0"
            + b"".join(bytes.fromhex(item) for item in ordered)
            + (64).to_bytes(2, "big")
            + (15).to_bytes(2, "big")
            + (11).to_bytes(2, "big")
            + (6).to_bytes(2, "big")
            + (24).to_bytes(2, "big")
        ).hexdigest()
    )
    graph_records = (
        bundle.predecessor_custody,
        bundle.contract,
        *tuple(item for vector in vectors for item in vector),
        bundle,
    )
    for record in graph_records:
        assert record.record_sha256 == _record_digest(
            record, _RECORD_DOMAINS[type(record)]
        )
        canonical = cp74.cp74_canonical_json_bytes(record)
        assert canonical == _canonical(record)
        assert (
            cp74.cp74_sha256(record)
            == hashlib.sha256(
                b"cp74-authoritative-public-record-v1\0"
                + type(record).__name__.encode("ascii")
                + b"\0"
                + canonical
            ).hexdigest()
        )


def test_all_64_by_11_occurrence_expressions_are_independently_closed() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    artifact_set = set(_ARTIFACT_IDS)
    manifest_excluded = {
        "sha256-manifest",
        "committed-marker",
        "auxiliary-reservation-transition-journal",
    }
    committed_transitive_excluded = {"committed-marker"}
    for ordinal, row in enumerate(bundle.artifact_occurrence_rules, 1):
        assert row.artifact_ordinal == ordinal
        expected = tuple(
            (branch_id, _expected_branch_expression(row.artifact_id, branch_id))
            for branch_id in _LIFECYCLE_BRANCH_IDS
        )
        assert row.branch_occurrence_expressions == expected
        assert len(row.branch_occurrence_expressions) == 11
        assert len(set(row.branch_occurrence_expressions)) == 11
        if row.artifact_id == "partial-seed-acquisition-terminal-receipt":
            assert row.conditional_occurrence_rule_ids == (_CONDITIONAL_RULE_IDS[0],)
        elif row.artifact_id == "rejected-launch-authorization-candidate":
            assert row.conditional_occurrence_rule_ids == (_CONDITIONAL_RULE_IDS[1],)
        else:
            assert row.conditional_occurrence_rule_ids == ()
        assert len(row.dependency_predecessor_artifact_ids) == len(
            set(row.dependency_predecessor_artifact_ids)
        )
        assert set(row.dependency_predecessor_artifact_ids) <= artifact_set
        assert row.artifact_id not in row.dependency_predecessor_artifact_ids
        assert row.retained_if_durable is True
        assert row.manifest_bound_if_present is (
            row.artifact_id not in manifest_excluded
        )
        assert row.committed_marker_transitively_binds_if_present is (
            row.artifact_id not in committed_transitive_excluded
        )
        assert row.conditional_rules_closed is True
        assert row.candidate_only is True
        assert row.cp65_definition_only is True
    assert tuple(
        row.artifact_id
        for row in bundle.artifact_occurrence_rules
        if not row.manifest_bound_if_present
    ) == tuple(
        artifact_id for artifact_id in _ARTIFACT_IDS if artifact_id in manifest_excluded
    )
    assert tuple(
        row.artifact_id
        for row in bundle.artifact_occurrence_rules
        if not row.committed_marker_transitively_binds_if_present
    ) == ("committed-marker",)


def test_occurrence_dependency_graph_is_acyclic() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    graph = {
        row.artifact_id: row.dependency_predecessor_artifact_ids
        for row in bundle.artifact_occurrence_rules
    }
    visiting = set()
    visited = set()

    def visit(artifact_id: str) -> None:
        assert artifact_id not in visiting, "dependency cycle at %s" % artifact_id
        if artifact_id in visited:
            return
        visiting.add(artifact_id)
        for predecessor in graph[artifact_id]:
            visit(predecessor)
        visiting.remove(artifact_id)
        visited.add(artifact_id)

    for artifact_id in _ARTIFACT_IDS:
        visit(artifact_id)
    assert visited == set(_ARTIFACT_IDS)


def test_cp65_gate_evidence_dag_is_exact_and_every_branch_is_downward_closed() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    assert len(_CP65_GATE_EVIDENCE_DAG_NODES) == 20
    assert len(set(_CP65_GATE_EVIDENCE_DAG_NODES)) == 20
    assert len(_CP65_GATE_EVIDENCE_DAG_EDGES) == 44
    assert len(set(_CP65_GATE_EVIDENCE_DAG_EDGES)) == 44
    assert {
        artifact_id for edge in _CP65_GATE_EVIDENCE_DAG_EDGES for artifact_id in edge
    } == set(_CP65_GATE_EVIDENCE_DAG_NODES)
    predecessors = {
        row.artifact_id: row.dependency_predecessor_artifact_ids
        for row in bundle.artifact_occurrence_rules
    }
    for source, target in _CP65_GATE_EVIDENCE_DAG_EDGES:
        assert source in predecessors[target]

    def transitive(artifact_id: str) -> set:
        result = set()
        frontier = list(predecessors[artifact_id])
        while frontier:
            predecessor = frontier.pop()
            if predecessor in result:
                continue
            result.add(predecessor)
            frontier.extend(predecessors[predecessor])
        return result

    occurrence = {
        row.artifact_id: dict(row.branch_occurrence_expressions)
        for row in bundle.artifact_occurrence_rules
    }
    for branch_id in _LIFECYCLE_BRANCH_IDS:
        for artifact_id in _ARTIFACT_IDS:
            if occurrence[artifact_id][branch_id] == "ABSENT":
                continue
            assert all(
                occurrence[predecessor][branch_id] != "ABSENT"
                for predecessor in transitive(artifact_id)
            )


def test_lifecycle_rows_are_exact_partitions_of_the_64_row_truth_table() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    expected_phases = (
        "PREAUTHORIZATION",
        "PREAUTHORIZATION",
        "PREAUTHORIZATION",
        "POSTAUTHORIZATION_PRESTART",
        "POSTAUTHORIZATION_PRESTART",
        "POSTAUTHORIZATION_PRESTART",
        "STARTED",
        "STARTED",
        "STARTED",
        "STARTED",
        "STARTED",
    )
    expected_terminal = (
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
        "PASS",
        "FAIL",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    )
    expected_cuts = (
        _CRASH_CUT_IDS[:4],
        _CRASH_CUT_IDS[:4],
        _CRASH_CUT_IDS[:4],
        (_CRASH_CUT_IDS[4],),
        (_CRASH_CUT_IDS[4],),
        (_CRASH_CUT_IDS[4],),
        (),
        (),
        (),
        (),
        (_CRASH_CUT_IDS[5],),
    )
    for ordinal, row in enumerate(bundle.lifecycle_branch_rules, 1):
        assert row.branch_ordinal == ordinal
        assert row.branch_id == _LIFECYCLE_BRANCH_IDS[ordinal - 1]
        assert row.branch_phase == expected_phases[ordinal - 1]
        assert row.terminal_state == expected_terminal[ordinal - 1]
        assert row.preauthorization_outcome_arm == (
            row.terminal_state if ordinal <= 3 else "AUTHORIZATION"
        )
        assert row.postauthorization_outcome_arm == (
            "ABSENT"
            if ordinal <= 3
            else (row.terminal_state if ordinal <= 6 else "STARTED")
        )
        expressions = {
            artifact_id: _expected_branch_expression(artifact_id, row.branch_id)
            for artifact_id in _ARTIFACT_IDS
        }
        assert row.always_required_artifact_ids == tuple(
            artifact_id
            for artifact_id in _ARTIFACT_IDS
            if expressions[artifact_id] in ("EXACT_GLOBAL_ONE", "EXACT_ALL_32_SHARDS")
        )
        assert row.always_forbidden_artifact_ids == tuple(
            artifact_id
            for artifact_id in _ARTIFACT_IDS
            if expressions[artifact_id] == "ABSENT"
        )
        assert row.durable_prefix_artifact_ids == tuple(
            artifact_id
            for artifact_id in _ARTIFACT_IDS
            if expressions[artifact_id] == "DURABLE_PREFIX_DEPENDENCY_CLOSED"
        )
        classified = set(row.always_required_artifact_ids)
        classified.update(row.always_forbidden_artifact_ids)
        classified.update(row.durable_prefix_artifact_ids)
        conditional = {
            artifact_id
            for artifact_id, expression in expressions.items()
            if expression.startswith("IFF_")
        }
        assert classified.isdisjoint(conditional)
        assert classified | conditional == set(_ARTIFACT_IDS)
        assert row.allowed_crash_cut_ids == expected_cuts[ordinal - 1]
        assert row.production_rng_or_child_permitted is (ordinal >= 7)
        assert row.retry_redraw_topup_or_reselection_permitted is False
        assert row.terminal_state_record_required is True
        assert row.sha256_manifest_required is True
        assert row.committed_marker_required is True
        assert row.candidate_only is True


def test_complete_and_abnormal_started_output_occurrences_are_not_blurred() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    rows = {row.artifact_id: row for row in bundle.artifact_occurrence_rules}
    for artifact_id in _OUTPUT_ARTIFACT_IDS:
        expression = dict(rows[artifact_id].branch_occurrence_expressions)
        if artifact_id == "environment":
            for branch_id in _LIFECYCLE_BRANCH_IDS[:3]:
                assert expression[branch_id] == "DURABLE_PREFIX_DEPENDENCY_CLOSED"
            for branch_id in _LIFECYCLE_BRANCH_IDS[3:]:
                assert expression[branch_id] == "EXACT_GLOBAL_ONE"
            continue
        complete_expected = (
            "EXACT_ALL_32_SHARDS"
            if artifact_id.startswith("shard-")
            else "EXACT_GLOBAL_ONE"
        )
        assert expression["started-pass"] == complete_expected
        assert expression["started-fail"] == complete_expected
        for branch_id in _LIFECYCLE_BRANCH_IDS[8:]:
            assert expression[branch_id] == "DURABLE_PREFIX_DEPENDENCY_CLOSED"
        for branch_id in _LIFECYCLE_BRANCH_IDS[:6]:
            assert expression[branch_id] == "ABSENT"


def test_six_crash_cuts_pin_at_cut_not_post_recovery_artifacts() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    outputs_and_closure = (
        _STOCHASTIC_OR_POSTEXECUTION_OUTPUT_ARTIFACT_IDS + _SHARD_CLOSURE_IDS
    )
    preauth_branches = _LIFECYCLE_BRANCH_IDS[:3]
    postauth_branches = _LIFECYCLE_BRANCH_IDS[3:6]
    expected = (
        (
            "PREAUTHORIZATION",
            preauth_branches,
            _CUT1_AND_CUT2_REQUIRED_ARTIFACT_IDS,
            (
                "external-seed-source-receipt",
                "seed-capsule-body",
                "seed-capsule-sequence-crosscheck-receipt",
                "production-schedule",
                "production-shard-map-receipt",
                "durability-receipt",
            )
            + outputs_and_closure,
            ("partial-seed-acquisition-terminal-receipt",),
        ),
        (
            "PREAUTHORIZATION",
            preauth_branches,
            _CUT1_AND_CUT2_REQUIRED_ARTIFACT_IDS,
            (
                "external-seed-source-receipt",
                "seed-capsule-body",
                "seed-capsule-sequence-crosscheck-receipt",
                "production-schedule",
                "production-shard-map-receipt",
                "durability-receipt",
            )
            + outputs_and_closure,
            ("partial-seed-acquisition-terminal-receipt",),
        ),
        (
            "PREAUTHORIZATION",
            preauth_branches,
            _CUT3_REQUIRED_ARTIFACT_IDS,
            (
                "partial-seed-acquisition-terminal-receipt",
                "production-shard-map-receipt",
                "durability-receipt",
                "seed-capsule-sequence-crosscheck-receipt",
                "production-schedule",
            )
            + outputs_and_closure,
            (),
        ),
        (
            "PREAUTHORIZATION",
            preauth_branches,
            _CUT4_REQUIRED_ARTIFACT_IDS,
            ("partial-seed-acquisition-terminal-receipt",) + outputs_and_closure,
            ("rejected-launch-authorization-candidate",),
        ),
        (
            "POSTAUTHORIZATION_PRESTART",
            postauth_branches,
            _CUT5_REQUIRED_ARTIFACT_IDS,
            ("started-receipt", "launch-receipt") + outputs_and_closure,
            (),
        ),
        (
            "STARTED",
            ("started-incomplete",),
            _CUT6_REQUIRED_ARTIFACT_IDS,
            ("started-receipt", "launch-receipt") + outputs_and_closure,
            (),
        ),
    )
    expected = tuple(
        (
            phase,
            branches,
            required,
            _inventory_ordered(set(forbidden)),
            _inventory_ordered(set(conditional)),
        )
        for phase, branches, required, forbidden, conditional in expected
    )
    assert tuple(len(item[2]) for item in expected) == (20, 20, 22, 29, 38, 39)
    forbidden_postcut = {
        "preterminal-durable-artifact-inventory",
        "terminal-state",
        "sha256-manifest",
        "committed-marker",
    }
    for ordinal, row in enumerate(bundle.crash_cut_rules, 1):
        phase, branches, required, forbidden, conditional = expected[ordinal - 1]
        assert row.crash_cut_ordinal == ordinal
        assert row.crash_cut_id == _CRASH_CUT_IDS[ordinal - 1]
        assert row.crash_cut_phase == phase
        assert row.applicable_branch_ids == branches
        assert row.required_durable_artifact_ids == required
        assert set(_FROZEN_BEFORE_ACQUISITION_ARTIFACT_IDS) <= set(required)
        assert row.forbidden_artifact_ids == forbidden
        assert row.conditional_artifact_ids == conditional
        assert set(required).isdisjoint(forbidden)
        assert forbidden_postcut.isdisjoint(required)
        assert row.production_rng_or_child_permitted is False
        assert row.retry_redraw_topup_or_reselection_permitted is False
        assert row.candidate_only is True
    final = bundle.crash_cut_rules[-1]
    assert "recovers-STARTED" in final.recovery_rule
    assert "INCOMPLETE" in final.terminal_state_rule
    assert "zero-output-occurrences" in final.terminal_state_rule


def test_all_15_output_envelopes_have_exact_schema_keys_and_cardinalities() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    occurrence = {row.artifact_id: row for row in bundle.artifact_occurrence_rules}
    for ordinal, row in enumerate(bundle.execution_output_semantic_rules, 1):
        artifact_id = _OUTPUT_ARTIFACT_IDS[ordinal - 1]
        source = occurrence[artifact_id]
        assert row.output_ordinal == ordinal
        assert row.artifact_id == artifact_id
        assert row.output_schema_id == _OUTPUT_SCHEMA_IDS[ordinal - 1]
        assert row.exact_top_level_keys == _OUTPUT_TOP_LEVEL_KEYS[ordinal - 1]
        assert row.cp65_artifact_schema_record_sha256 == (
            source.cp65_artifact_schema_record_sha256
        )
        assert (row.path_template, row.path_scope, row.media_kind) == (
            source.path_template,
            source.path_scope,
            source.media_kind,
        )
        if ordinal <= 9:
            assert (
                row.complete_attempt_instance_count,
                row.complete_attempt_units_per_instance,
                row.complete_attempt_total_unit_count,
                row.canonical_encoding,
                row.framing_rule,
                row.final_terminator_rule,
                row.ordering_rule,
            ) == (
                1,
                1,
                1,
                "ASCII-canonical-JSON",
                "one-canonical-JSON-document",
                "zero-trailing-bytes",
                "single-global-instance",
            )
        else:
            assert (
                row.complete_attempt_instance_count,
                row.complete_attempt_units_per_instance,
                row.complete_attempt_total_unit_count,
            ) == (32, 1_024, 32_768)
            assert "shard-ordinal-1-through-32" in row.ordering_rule
            assert "whole-finalized-shard-files" in row.ordering_rule
            assert "never-transient-partial-files" in row.ordering_rule
        assert row.production_values_present is False
        assert row.candidate_only is True
        assert "production-values-absent" in row.field_semantic_rules[-1]
        assert any(
            "total-final-artifact-instances=201" in rule
            for rule in row.field_semantic_rules
        )
        assert any(
            "total-framed-units-or-rows=196617" in rule
            for rule in row.field_semantic_rules
        )
    assert (
        sum(
            row.complete_attempt_instance_count
            for row in bundle.execution_output_semantic_rules
        )
        == 201
    )
    assert (
        sum(
            row.complete_attempt_total_unit_count
            for row in bundle.execution_output_semantic_rules
        )
        == 196_617
    )


def test_all_15_output_nested_keysets_are_independently_frozen() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    expected = {
        "environment": (
            "environment-entry-exact-keys=(name,value_text,entry_sha256)",
            "ordered-environment-entries-sorted-by-unique-name",
            "sanitized-child-environment-exact17=" + repr(_SANITIZED_CHILD_ENVIRONMENT),
        ),
        "primary-metrics": (
            "primary-slot-exact-keys=(slot_ordinal,slot_id,estimand_id,estimand_record_sha256,estimate,interval_lower,interval_upper,gate_id,threshold_value,threshold_row_sha256,slot_record_sha256)",
            "exactly-32-slots-in-slot-ordinal-order",
            "gate_id-exactly-cp65-power-primary-slot-%02d-and-equals-referenced-threshold-row-gate_id",
        ),
        "secondary-diagnostics": (
            "terminal-count-exact-keys=(returned_rejection_selected_before_deadline,returned_rejection_exhausted_before_deadline,returned_sir_selected_before_deadline,preexecution_refusal_before_deadline,execution_failure_before_deadline,timeout_censored_at_deadline)",
            "diagnostic-exact-keys=(diagnostic_ordinal,diagnostic_id,value_kind,value_text,source_artifact_ids,source_sha256s,diagnostic_record_sha256)",
        ),
        "postexecution-independent-recomputation": (
            _key_rule("estimand-record-exact-keys", _CP71_ESTIMAND_KEYS),
            "ordered-shard-vectors-exactly-32-in-shard-ordinal-order",
            "estimand-inventory-exactly-554-in-estimand-ordinal-order",
            "embedded-CP71-estimand-record-domain=cp71-test28-supplied-estimand-estimate-interval-v1-NUL",
            "embedded-CP71-ordered-estimand-domain=cp71-test28-ordered-estimand-record-digests-v1-NUL",
            "embedded-CP71-output-body-domain=cp71-test28-supplied-interchange-estimate-interval-output-body-v1-NUL",
            "cp72-validation-summary-public-digest-domain=cp72-public-record-v1-NUL",
            "cp73-relation-summary-public-digest-domain=cp73-public-record-v1-NUL",
        ),
        "decisions": (
            "slot-decision-exact-keys=(slot_ordinal,slot_id,primary_metric_record_sha256,threshold_row_sha256,decision_semantics_resolved,decision,slot_decision_record_sha256)",
            "exactly-32-slot-envelopes-in-slot-ordinal-order",
        ),
        "deviations": (
            "deviation-entry-exact-keys=(ordinal,scope_kind,logical_request_ordinal,code,stage,description_sha256,source_artifact_id,source_record_sha256,disposition,entry_sha256)",
        ),
        "failures": (
            "failure-entry-exact-keys=(ordinal,logical_request_ordinal,shard_id,phase,closed_status,failure_code,raw_record_sha256,stable_trace_sha256,entry_sha256)",
        ),
        "exclusions": (
            "exclusion-entry-exact-keys=(ordinal,logical_request_ordinal,reason_code,source_artifact_id,source_record_sha256,estimand_population_effect,disposition,entry_sha256)",
        ),
        "reruns": (
            "rerun-entry-exact-keys=(ordinal,prior_attempt_id,new_attempt_id,independent_adjudication_sha256,frozen_inputs_sha256,abort_before_acquisition_start_durable,identical_frozen_inputs,no_same_attempt_retry,entry_sha256)",
        ),
        "shard-requests": (),
        "shard-raw-records": _RAW_NESTED_KEY_RULES,
        "shard-stable-traces": (
            _key_rule("returned-semantic-exact-keys", _RETURNED_SEMANTIC_KEYS),
            _key_rule("closed-semantic-exact-keys", _CLOSED_SEMANTIC_KEYS),
        ),
        "shard-stderr-records": (),
        "shard-rng-initial-states": (
            _key_rule("state-row-exact-keys", _RNG_ROW_KEYS),
            _key_rule("normalized-state-exact-keys", _RNG_STATE_KEYS),
            "present-Philox-state-has-bit_generator=Philox-counter_u64_hex-length4-key_u64_hex-length2-buffer_u64_hex-length4",
            "absent-state-uses-present=false-bit_generator=null-empty-counter-key-buffer-buffer_pos=0-has_uint32=0-uinteger_u64_hex=0000000000000000",
            "returned-rejection-requires-proposal-and-decision-streams-and-absent-resampling;returned-SIR-requires-proposal-and-resampling-and-absent-decision",
            "closed-refusal-failure-and-timeout-arms-have-no-RNG-state-hashes-in-the-exact21-semantic-and-require-explicit-absent-unobserved-state-sentinels-with-no-invented-custody",
            "reconstruct-exact-NumPy-Philox-state-dict-with-native-frozen-<u8-arrays-counter-shape4-key-shape2-buffer-shape4",
            "hash-reconstructed-state-with-domain-heterodiff-mixed-support-initializer-v2-philox-state-NUL-and-CP62-recursive-sorted-dict-type-tags",
            "compare-state-hash-to-arm-appropriate-raw-semantic-initial-or-final-stream-state-sha256",
        ),
    }
    expected["shard-rng-final-states"] = expected["shard-rng-initial-states"]
    assert tuple(expected) == _OUTPUT_ARTIFACT_IDS
    for row in bundle.execution_output_semantic_rules:
        assert row.nested_schema_rules == expected[row.artifact_id]


def _child_paths(prefix: str, keys: tuple) -> set:
    return {prefix + "/" + key for key in keys}


def _expected_field_grammar_paths(artifact_id: str, top_level: tuple) -> set:
    paths = {"/" + key for key in top_level}
    if artifact_id == "environment":
        paths |= _child_paths(
            "/ordered_environment_entries/*", ("name", "value_text", "entry_sha256")
        )
    elif artifact_id == "primary-metrics":
        paths |= _child_paths(
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
        )
    elif artifact_id == "secondary-diagnostics":
        paths |= _child_paths(
            "/terminal_counts",
            (
                "returned_rejection_selected_before_deadline",
                "returned_rejection_exhausted_before_deadline",
                "returned_sir_selected_before_deadline",
                "preexecution_refusal_before_deadline",
                "execution_failure_before_deadline",
                "timeout_censored_at_deadline",
            ),
        )
        paths |= _child_paths(
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
        )
    elif artifact_id == "postexecution-independent-recomputation":
        paths |= _child_paths("/estimand_estimate_intervals/*", _CP71_ESTIMAND_KEYS)
    elif artifact_id == "decisions":
        paths |= _child_paths(
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
        )
    elif artifact_id in ("deviations", "failures", "exclusions", "reruns"):
        keys = {
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
        paths |= _child_paths("/entries/*", keys)
    elif artifact_id in ("shard-raw-records", "shard-stable-traces"):
        semantic = (
            "/kernel_trace/semantic"
            if artifact_id == "shard-raw-records"
            else "/kernel_trace"
        )
        returned = semantic + "@returned"
        closed = semantic + "@closed"
        paths |= _child_paths(returned, _RETURNED_SEMANTIC_KEYS)
        paths |= _child_paths(closed, _CLOSED_SEMANTIC_KEYS)
        paths |= _child_paths(
            returned + "/runtime_observation", _RUNTIME_OBSERVATION_KEYS
        )
        paths |= _child_paths(
            closed + "/runtime_observation", _RUNTIME_OBSERVATION_KEYS
        )
        paths |= _child_paths(
            returned + "/resource_preflight", _RESOURCE_PREFLIGHT_KEYS
        )
        for collection, item_keys in (
            ("attempts", _ATTEMPT_KEYS),
            ("particles", _PARTICLE_KEYS),
        ):
            item = returned + "/" + collection + "/*"
            scored = item + "/scored"
            configuration = scored + "/configuration"
            facade = scored + "/facade_evaluation"
            paths |= _child_paths(item, item_keys)
            paths |= _child_paths(scored, _SCORED_KEYS)
            paths |= _child_paths(configuration, _CONFIGURATION_KEYS)
            paths |= _child_paths(
                configuration + "/events/*",
                ("event_type", "coordinates_float64_be"),
            )
            paths |= _child_paths(facade, _FACADE_EVALUATION_KEYS)
            paths |= _child_paths(
                facade + "/source_evaluation", _SOURCE_EVALUATION_KEYS
            )
            if collection == "attempts":
                paths |= _child_paths(item + "/quota", _QUOTA_KEYS)
        paths |= _child_paths(returned + "/selected_configuration", _CONFIGURATION_KEYS)
        paths |= _child_paths(
            returned + "/selected_configuration/events/*",
            ("event_type", "coordinates_float64_be"),
        )
        if artifact_id == "shard-raw-records":
            paths |= _child_paths("/kernel_trace", _KERNEL_TRACE_KEYS)
            paths |= _child_paths(
                "/kernel_trace/volatile_custody", _VOLATILE_CUSTODY_KEYS
            )
            paths |= _child_paths(
                "/kernel_trace/volatile_custody/nested_record_custody/*",
                _NESTED_CUSTODY_KEYS,
            )
            paths |= _child_paths("/supervisor_custody", _SUPERVISOR_CUSTODY_KEYS)
    elif artifact_id == "shard-stderr-records":
        paths |= {"/frames/*/length_prefix", "/frames/*/payload"}
    elif artifact_id in (
        "shard-rng-initial-states",
        "shard-rng-final-states",
    ):
        paths |= _child_paths("/ordered_state_rows/*", _RNG_ROW_KEYS)
        for stream in (
            "proposal_stream_state",
            "decision_stream_state",
            "resampling_stream_state",
        ):
            paths |= _child_paths("/ordered_state_rows/*/" + stream, _RNG_STATE_KEYS)
    return paths


def test_all_15_field_grammars_have_exact_duplicate_free_path_coverage() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    expected_counts = (23, 23, 27, 46, 22, 17, 16, 15, 16, 14, 296, 259, 2, 40, 40)
    for row, expected_count in zip(
        bundle.execution_output_semantic_rules, expected_counts
    ):
        grammar = tuple(
            rule
            for rule in row.field_semantic_rules
            if rule.startswith("field-grammar|")
        )
        assert len(grammar) == expected_count
        split = tuple(rule.split("|", 3) for rule in grammar)
        assert all(
            len(parts) == 4
            and parts[0] == "field-grammar"
            and parts[1].startswith("path=/")
            and parts[2].startswith("json-type=")
            and parts[3].startswith("constraint=")
            for parts in split
        )
        paths = tuple(parts[1][5:] for parts in split)
        assert len(paths) == len(set(paths))
        assert set(paths) == _expected_field_grammar_paths(
            row.artifact_id, row.exact_top_level_keys
        )


def test_jsonl_stderr_rng_and_digest_domain_exceptions_are_exact() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    outputs = {row.artifact_id: row for row in bundle.execution_output_semantic_rules}
    for artifact_id in (
        "shard-requests",
        "shard-raw-records",
        "shard-stable-traces",
    ):
        row = outputs[artifact_id]
        assert row.canonical_encoding == "ASCII-canonical-JSON"
        assert row.framing_rule == (
            "1024-canonical-JSON-records-each-followed-by-one-LF"
        )
        assert row.final_terminator_rule == "one-LF-after-every-record-including-last"
        assert row.body_digest_domain == "plain-sha256-of-exact-file-bytes"
    request = outputs["shard-requests"]
    assert request.record_digest_domain == (
        "cp65-test28-production-schedule-request-row-v1\0"
    )
    assert "candidate" in request.ordered_record_digest_domain
    stable = outputs["shard-stable-traces"]
    assert stable.record_digest_domain == (
        "plain-sha256-of-exact-canonical-stable-record-bytes-before-LF"
    )
    assert stable.ordered_record_digest_domain == (
        "cp74-test28-production-shard-stable-candidate-ordered-record-digests-v1\0"
    )
    assert stable.body_digest_domain == "plain-sha256-of-exact-file-bytes"
    stderr = outputs["shard-stderr-records"]
    assert stderr.canonical_encoding == (
        "binary-uint64-big-endian-length-prefixed-frames"
    )
    assert stderr.framing_rule == (
        "1024-uint64-big-endian-length-prefixed-payload-frames"
    )
    assert stderr.final_terminator_rule == "zero-trailing-bytes"
    assert stderr.record_digest_domain == "plain-sha256-of-frame-payload-bytes"
    assert stderr.ordered_record_digest_domain == "not-applicable-framed-binary-stream"
    assert stderr.body_digest_domain == "plain-sha256-of-exact-file-bytes"
    for artifact_id in ("shard-rng-initial-states", "shard-rng-final-states"):
        row = outputs[artifact_id]
        assert row.framing_rule == (
            "one-canonical-JSON-container-with-1024-ordered-state-rows"
        )
        assert row.final_terminator_rule == "zero-trailing-bytes"
        assert all(
            "candidate" in domain and domain.endswith("\0")
            for domain in (
                row.record_digest_domain,
                row.ordered_record_digest_domain,
                row.body_digest_domain,
            )
        )
    candidate_domains = []
    for row in bundle.execution_output_semantic_rules:
        for domain in (
            row.record_digest_domain,
            row.ordered_record_digest_domain,
            row.body_digest_domain,
        ):
            if domain.startswith("cp74-"):
                assert "candidate" in domain
                assert domain.endswith("\0")
                candidate_domains.append(domain)
    assert len(candidate_domains) == len(set(candidate_domains))


def test_all_output_digest_descriptors_have_executable_preimages_not_domains_only() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    for row in bundle.execution_output_semantic_rules:
        formulas = tuple(
            rule
            for rule in row.field_semantic_rules
            if rule.startswith(("digest-formula=", "ordered-record-digest="))
        )
        assert len(formulas) == 3
        joined = "\n".join(formulas)
        assert "carrier=" in joined
        assert "preimage=" in joined
        assert "digest=" in joined
        assert "field-omitted" not in joined
        for domain in (
            row.record_digest_domain,
            row.ordered_record_digest_domain,
            row.body_digest_domain,
        ):
            if domain.startswith(("cp65-", "cp71-", "cp74-")):
                assert domain.replace("\0", "\\0") in joined
    outputs = {row.artifact_id: row for row in bundle.execution_output_semantic_rules}
    stable = "\n".join(outputs["shard-stable-traces"].field_semantic_rules)
    assert "no-stable-self-digest-field-exists" in stable
    assert "exact-ASCII-canonical-JSON-stable-record-bytes-before-LF" in stable
    assert "domain=none;digest=plain-SHA256(preimage)" in stable
    assert "1024-raw-32-byte-plain-stable-record-digests" in stable
    assert "exact-1024-row-JSONL-file-bytes" in stable
    request = "\n".join(outputs["shard-requests"].field_semantic_rules)
    raw = "\n".join(outputs["shard-raw-records"].field_semantic_rules)
    assert "request_row_sha256-set-to-64-lowercase-zero-hex-characters" in request
    assert "raw_sha256-set-to-64-lowercase-zero-hex-characters" in raw
    omission_rules = {
        rule
        for row in bundle.execution_output_semantic_rules
        for rule in row.field_semantic_rules
        if "field-omitted" in rule
    }
    assert omission_rules == {
        "returned-terminal-digest-formula=SHA256(cp74-test28-production-returned-kernel-trace-candidate-v1\\0||ASCII-canonical-JSON-of-exact-returned-semantic-object-with-cp74_semantic_trace_sha256-field-omitted)",
        "closed-terminal-digest-formula=SHA256(cp74-test28-production-closed-kernel-outcome-candidate-v1\\0||ASCII-canonical-JSON-of-exact-closed-semantic-object-with-cp74_closed_trace_sha256-field-omitted)",
        "cp62-configuration-leaf-digest-formula=SHA256(cp62-test28-configuration-v1\\0||ASCII-canonical-JSON-of-exact-configuration-object-with-cp62_configuration_sha256-field-omitted)",
        "cp62-source-evaluation-leaf-digest-formula=SHA256(cp62-test28-source-evaluation-v1\\0||ASCII-canonical-JSON-of-exact-source-evaluation-object-with-cp62_source_evaluation_sha256-field-omitted)",
        "cp62-facade-evaluation-leaf-digest-formula=SHA256(cp62-test28-facade-evaluation-v1\\0||ASCII-canonical-JSON-of-exact-facade-evaluation-object-with-cp62_facade_evaluation_sha256-field-omitted)",
        "cp62-scored-slot-leaf-digest-formula=SHA256(cp62-test28-scored-slot-v1\\0||ASCII-canonical-JSON-of-exact-scored-object-with-cp62_scored_sha256-field-omitted)",
        "cp62-quota-certificate-leaf-digest-formula=SHA256(cp62-test28-quota-certificate-v1\\0||ASCII-canonical-JSON-of-exact-quota-object-with-cp62_quota_sha256-field-omitted)",
        "cp62-rejection-attempt-leaf-digest-formula=SHA256(cp62-test28-rejection-attempt-v1\\0||ASCII-canonical-JSON-of-exact-attempt-object-with-cp62_attempt_sha256-field-omitted)",
        "cp62-SIR-particle-leaf-digest-formula=SHA256(cp62-test28-sir-particle-v1\\0||ASCII-canonical-JSON-of-exact-particle-object-with-cp62_particle_sha256-field-omitted)",
    }


def test_explicit_child_digest_vectors_are_bound_before_ordered_digesting() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    expected_vectors = {
        "primary-metrics": "/ordered_primary_slot_record_sha256s",
        "secondary-diagnostics": "/ordered_diagnostic_record_sha256s",
        "decisions": "/ordered_slot_decision_record_sha256s",
        "shard-rng-initial-states": "/ordered_state_row_sha256s",
        "shard-rng-final-states": "/ordered_state_row_sha256s",
    }
    nested_outputs = set(_OUTPUT_ARTIFACT_IDS[:9]) | {
        "shard-rng-initial-states",
        "shard-rng-final-states",
    }
    for row in bundle.execution_output_semantic_rules:
        ordered = tuple(
            rule
            for rule in row.field_semantic_rules
            if rule.startswith("digest-formula=ordered-nested-records;")
        )
        if row.artifact_id not in nested_outputs:
            assert ordered == ()
            continue
        assert len(ordered) == 1
        formula = ordered[0]
        if row.artifact_id in expected_vectors:
            assert (
                "explicit-vector=%s-must-equal-the-child-carrier-values-in-the-"
                "same-frozen-order-and-cardinality-before-the-ordered-digest-is-"
                "computed" % expected_vectors[row.artifact_id]
            ) in formula
        else:
            assert (
                "explicit-vector=not-present-the-frozen-child-carrier-order-is-"
                "the-ordered-digest-input"
            ) in formula


def test_raw_stable_semantics_close_exact_phase_status_code_and_projection_rules() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    outputs = {row.artifact_id: row for row in bundle.execution_output_semantic_rules}
    raw = outputs["shard-raw-records"]
    stable = outputs["shard-stable-traces"]
    assert len(raw.exact_top_level_keys) == 20
    assert "rehearsal_id" not in raw.exact_top_level_keys
    assert "repetition" not in raw.exact_top_level_keys
    assert len(stable.exact_top_level_keys) == 18
    assert "supervisor_custody" not in stable.exact_top_level_keys
    assert "raw_sha256" not in stable.exact_top_level_keys
    raw_rules = "\n".join(raw.nested_schema_rules + raw.field_semantic_rules)
    stable_rules = "\n".join(stable.nested_schema_rules + stable.field_semantic_rules)
    required = (
        "phase-arms-exact=('returned-before-deadline', 'preexecution-refusal-before-deadline', 'execution-failure-before-deadline', 'timeout-at-deadline')",
        "plan_validation_refusal",
        "provider_reference_binding_refusal",
        "resource_preflight_refusal",
        "runtime_binding_refusal",
        "other_preexecution_refusal",
        "reference_sampling_failure",
        "score_evaluation_failure",
        "quota_certification_failure",
        "float64_normalization_failure",
        "categorical_selection_failure",
        "structural_result_validation_failure",
        "other_execution_failure",
        "returned-trace_schema=cp74-test28-production-returned-kernel-trace-candidate-v1",
        "closed-trace_schema=cp74-test28-production-closed-kernel-outcome-candidate-v1",
    )
    assert all(item in raw_rules for item in required)
    assert all(item in stable_rules for item in required[-2:])
    assert "supervisor-custody-exact-keys=" in raw_rules
    assert "stderr_sha256" in raw_rules
    assert "exactly-1024" in raw_rules
    assert "removing-supervisor_custody-and-raw_sha256" in stable_rules
    projection = {row.rule_id: row for row in bundle.output_cross_binding_rules}[
        "shard-raw-records-to-shard-stable-traces"
    ]
    assert "copy-phase-closed_status-failure_code-byte-for-byte" in (
        projection.preimage_or_equality_formula
    )
    assert "exact-four-phase-six-closed-status-five-refusal-code-seven-execution" in (
        projection.preimage_or_equality_formula
    )
    assert "rehearsal_id" not in stable.exact_top_level_keys
    assert raw.closed_outcome_arms == stable.closed_outcome_arms
    assert len(raw.closed_outcome_arms) == 6


def _field_grammar_map(row: object) -> Dict[str, str]:
    result = {}
    for rule in row.field_semantic_rules:
        if not rule.startswith("field-grammar|"):
            continue
        _tag, path, json_type, constraint = rule.split("|", 3)
        result[path[5:]] = json_type + "|" + constraint
    return result


def test_raw_and_stable_arm_grammars_are_exact_and_semantically_identical() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    outputs = {row.artifact_id: row for row in bundle.execution_output_semantic_rules}
    raw = outputs["shard-raw-records"]
    stable = outputs["shard-stable-traces"]
    raw_grammar = _field_grammar_map(raw)
    stable_grammar = _field_grammar_map(stable)
    exact_raw = {
        "/phase": "json-type=string|constraint=one-of=('returned-before-deadline', 'preexecution-refusal-before-deadline', 'execution-failure-before-deadline', 'timeout-at-deadline')",
        "/closed_status": "json-type=string|constraint=one-of=('returned-rejection-selected-before-deadline', 'returned-rejection-exhausted-before-deadline', 'returned-sir-selected-before-deadline', 'preexecution-refusal-before-deadline', 'execution-failure-before-deadline', 'timeout-censored-at-deadline')",
        "/failure_code": "json-type=string-or-null|constraint=null-or-one-of-refusal5-or-execution-failure7;phase-compatible",
        "/kernel_trace/semantic": "json-type=object|constraint=exact-returned54-or-closed21-discriminated-by-outer-phase",
        "/kernel_trace/volatile_custody": "json-type=object-or-null|constraint=exact-object-on-returned-before-deadline;exact=null-on-refusal-failure-timeout",
        "/kernel_trace/semantic@returned/result_status": "json-type=string|constraint=bounded-rejection-one-of=(selected,exhausted)-and-matches-outer-closed_status;fixed-budget-sir-exact=selected-and-outer-closed_status=returned-sir-selected-before-deadline",
        "/kernel_trace/semantic@returned/attempts": "json-type=array|constraint=strategy-discriminated;rejection-length=budget;SIR-exact-empty",
        "/kernel_trace/semantic@returned/particles": "json-type=array|constraint=strategy-discriminated;SIR-length=budget;rejection-exact-empty",
        "/kernel_trace/semantic@returned/selected_index": "json-type=integer-or-null-bool-forbidden|constraint=bounded-rejection-selected=first-accepted-attempt-index;bounded-rejection-exhausted=null;fixed-budget-sir=right-sided-selection-from-normalized-weights-and-resampling-word;non-null-range-0-through-budget-minus-1",
        "/kernel_trace/semantic@returned/selected_configuration": "json-type=object-or-null|constraint=bounded-rejection-selected=exact-configuration-of-first-accepted-attempt;bounded-rejection-exhausted=null;fixed-budget-sir=exact-configuration-of-right-sided-selected-particle",
        "/kernel_trace/semantic@closed/outcome_kind": "json-type=string|constraint=one-of=(preexecution-refusal,execution-failure,timeout-censored);equals-outer-phase-arm",
        "/kernel_trace/semantic@closed/failure_code": "json-type=string-or-null|constraint=exact-refusal5-for-preexecution-refusal;exact-execution-failure7-for-execution-failure;exact=null-for-timeout-censored",
        "/kernel_trace/semantic@returned/attempts/*/scored/configuration/events/*/event_type": "json-type=integer-bool-forbidden|constraint=one-of=(0,1);coordinate-dimension:T28-M1-Q/type0=0,T28-M1-Q/type1=1,T28-M2-Q/type0=1,T28-M2-Q/type1=2",
        "/kernel_trace/semantic@returned/attempts/*/scored/configuration/events/*/coordinates_float64_be": "json-type=array|constraint=fixture-and-event-type-exact-length:T28-M1-Q/type0=0,T28-M1-Q/type1=1,T28-M2-Q/type0=1,T28-M2-Q/type1=2;each-item-exact-one-key-object-$float64_be-with-16-lowercase-hex-IEEE754-binary64-big-endian;finite;no-negative-zero",
        "/kernel_trace/semantic@returned/attempts/*/quota/schema_version": "json-type=string|constraint=exact-literal=arbitrary-rational-uint64-exp-quota-v1",
    }
    assert {path: raw_grammar[path] for path in exact_raw} == exact_raw
    semantic_prefix = "/kernel_trace/semantic@"
    raw_semantic = {
        path: grammar
        for path, grammar in raw_grammar.items()
        if path.startswith(semantic_prefix)
    }
    assert raw_semantic
    for path, grammar in raw_semantic.items():
        stable_path = "/kernel_trace@" + path[len(semantic_prefix) :]
        assert stable_grammar[stable_path] == grammar

    exact_projection_rules = (
        "nested-leaf-parent-relations=recompute-configuration-before-source-and-facade;source-evaluation-is-the-exact-facade-child;configuration-and-facade-digests-and-exact-log-weight-fields-bind-the-scored-slot;attempt.exact_delta-equals-attempt.scored.exact_log_weight;the-entire-attempt.quota-object-including-all-text-integer-boolean-and-cp62_quota_sha256-fields-equals-a-fresh-certify_arbitrary_rational_uint64_exp_quota(attempt.exact_delta)-projection-under-schema-arbitrary-rational-uint64-exp-quota-v1;accepted-equals-int(decision_word_hex,16)<int(quota.quota,10);scored-binds-each-attempt-or-particle;selected-configuration-equals-the-selected-scored-configuration",
        "bounded-rejection-rule=decision-stream-initial-and-final-digests-present;resampling-seed-state-word-uniform-ESS-maximum-weight-and-ess_warning-null;attempts-length=budget;particles-and-normalized-weights-empty;explicit-rejection-exhaustion=true;quota-required=true;selected-status-uses-first-accepted-attempt-and-exhausted-status-has-no-accepted-attempt-or-selection",
        "fixed-budget-SIR-rule=decision-seed-and-state-digests-null;resampling-seed-state-digests-word-uniform-ESS-maximum-weight-and-ess_warning-present;attempts-empty;particles-and-normalized-weights-length=budget;explicit-rejection-exhaustion=false;quota-required=false;weights-exactly-recomputed-from-particle-exact-scores-and-sum-to-one;selected-index-is-the-frozen-right-sided-selection-from-weights-and-word",
        "closed-rule=runtime_observation-null-or-exact-runtime-object;completed_kernel_trace_present=false;timeout_is_semantic_nonreturn=false;no-RNG-state-custody;outcome_kind-and-failure_code-exactly-match-the-outer-phase",
    )
    for rule in exact_projection_rules:
        assert rule in raw.field_semantic_rules
        assert rule in stable.field_semantic_rules
    raw_source_constraints = tuple(
        rule
        for rule in stable.field_semantic_rules
        if rule.startswith(
            "corresponding-raw-source-before-stable-projection-constraint="
        )
    )
    assert raw_source_constraints == (
        "corresponding-raw-source-before-stable-projection-constraint=returned-volatile-nested-custody-exactly-matches-each-semantic-slot-configuration-source-facade-scored-and-strategy-specific-quota-attempt-or-particle-child-digests-in-index-order;closed-arms-have-volatile_custody=null",
        "corresponding-raw-source-before-stable-projection-constraint=supervisor-monotonic-runtime-process-and-stderr-custody-values-are-unauthenticated-candidate-fields",
    )
    assert not any(
        rule.startswith(
            (
                "returned-refusal-and-execution-failure-supervisor-rule=",
                "timeout-supervisor-rule=",
                "all-supervisor-arms-require=",
                "returned-volatile-nested-custody-exactly-matches=",
                "supervisor-monotonic-runtime-process-and-stderr-custody-values=",
            )
        )
        for rule in stable.field_semantic_rules
    )


def test_decision_and_recomputation_descriptors_cannot_be_read_as_production_claims() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    outputs = {row.artifact_id: row for row in bundle.execution_output_semantic_rules}
    primary = "\n".join(
        outputs["primary-metrics"].nested_schema_rules
        + outputs["primary-metrics"].field_semantic_rules
    )
    decisions = "\n".join(
        outputs["decisions"].nested_schema_rules
        + outputs["decisions"].field_semantic_rules
    )
    recomputation = "\n".join(
        outputs["postexecution-independent-recomputation"].nested_schema_rules
        + outputs["postexecution-independent-recomputation"].field_semantic_rules
    )
    assert "exactly-32-slots" in primary
    assert (
        "comparison-operator-direction-and-executable-decision-function-not-defined"
        in primary
    )
    assert "decision_semantics_resolved=false" in decisions
    assert "all_primary_thresholds_passed=null" in decisions
    assert "decision=null" in decisions
    assert "no-currently-executable-production-decision-schema" in decisions
    assert "exactly-554" in recomputation
    assert _field_grammar_map(outputs["postexecution-independent-recomputation"])[
        "/source_interchange_schema_version"
    ] == (
        "json-type=string|constraint=exact-literal=cp69-test28-compact-"
        "projection-interchange-qualification-v1"
    )
    assert "development-structural-references-only" in recomputation
    assert "not-production-custody-or-gate13-or-gate14-evidence" in recomputation
    assert "production_recomputation_performed-remains-false" in recomputation


def test_all_24_cross_bindings_are_ordered_resolved_and_reciprocal() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    artifact_set = set(_ARTIFACT_IDS)
    cross_by_id = {row.rule_id: row for row in bundle.output_cross_binding_rules}
    assert tuple(cross_by_id) == _CROSS_BINDING_IDS
    for ordinal, row in enumerate(bundle.output_cross_binding_rules, 1):
        assert row.rule_ordinal == ordinal
        assert row.rule_id == _CROSS_BINDING_IDS[ordinal - 1]
        assert row.source_artifact_ids
        assert row.target_artifact_ids
        assert len(row.source_artifact_ids) == len(set(row.source_artifact_ids))
        assert len(row.target_artifact_ids) == len(set(row.target_artifact_ids))
        assert set(row.source_artifact_ids + row.target_artifact_ids) <= artifact_set
        assert row.digest_or_equality_kind
        assert row.preimage_or_equality_formula
        assert row.cardinality_rule
        assert row.ordering_rule
        assert row.required_in_complete_attempt is True
        assert row.candidate_only is True
    covered = set()
    for output in bundle.execution_output_semantic_rules:
        assert len(output.cross_binding_rule_ids) == len(
            set(output.cross_binding_rule_ids)
        )
        for rule_id in output.cross_binding_rule_ids:
            assert rule_id in cross_by_id
            cross = cross_by_id[rule_id]
            assert output.artifact_id in (
                cross.source_artifact_ids + cross.target_artifact_ids
            )
            covered.add(rule_id)
    assert covered == set(_CROSS_BINDING_IDS[:-1])
    assert _CROSS_BINDING_IDS[-1] not in covered
    inventory = cross_by_id[
        "referenced-outputs-to-preterminal-inventory-and-sha256-manifest"
    ]
    assert inventory.source_artifact_ids == _OUTPUT_ARTIFACT_IDS
    assert inventory.target_artifact_ids == (
        "preterminal-durable-artifact-inventory",
        "sha256-manifest",
    )
    assert "all-and-only-present" in inventory.digest_or_equality_kind
    assert "partial-writer-files-never-occur" in inventory.preimage_or_equality_formula
    committed = cross_by_id["terminal-state-and-sha256-manifest-to-committed-marker"]
    assert committed.source_artifact_ids == ("terminal-state", "sha256-manifest")
    assert committed.target_artifact_ids == ("committed-marker",)
    assert "transitively-binds" in committed.preimage_or_equality_formula


def test_runtime_recomputation_threshold_and_terminal_crossbindings_are_exact() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    cross = {row.rule_id: row for row in bundle.output_cross_binding_rules}
    runtime = cross[
        "frozen-runtime-lock-and-production-runtime-receipt-to-shard-raw-records"
    ]
    assert runtime.source_artifact_ids == (
        "frozen-machine-manifest",
        "production-runtime-receipt",
    )
    assert runtime.source_pointer_or_components == (
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
    )
    assert runtime.target_artifact_ids == ("shard-raw-records",)
    assert "production-runtime-receipt-has-no-runtime_lock_sha256-field" in (
        runtime.preimage_or_equality_formula
    )
    assert "CP74-authenticates-neither" in runtime.preimage_or_equality_formula

    reprojection = cross[
        "independent-raw-to-stable-reprojection-to-postexecution-independent-recomputation"
    ]
    assert reprojection.source_artifact_ids == ("shard-raw-records",)
    assert reprojection.target_artifact_ids == (
        "shard-stable-traces",
        "postexecution-independent-recomputation",
    )
    assert reprojection.target_pointer_or_components == (
        "all-32768-stable-records-and-32-stable-file-SHA256s",
        "/raw_to_stable_projection_recomputed",
        "/cp71_output_canonical_json_sha256",
        "/cp72_validation_summary_public_sha256",
        "/cp73_relation_summary_public_sha256",
    )
    assert reprojection.preimage_or_equality_formula == _STABLE_TO_CP69_TO_CP71_FORMULA

    primary = cross["postexecution-independent-recomputation-to-primary-metrics"]
    assert primary.source_artifact_ids == (
        "postexecution-independent-recomputation",
        "power-threshold-receipt",
        "power-review-signoff",
    )
    assert primary.target_artifact_ids == ("primary-metrics",)
    assert primary.target_pointer_or_components == (
        "/recomputation_artifact_sha256",
        "/power_threshold_receipt_sha256",
        "/power_review_signoff_sha256",
        "/ordered_primary_slots/*/(estimand_id,estimand_record_sha256,estimate,interval_lower,interval_upper)",
        "/ordered_primary_slots/*/(slot_ordinal,slot_id,gate_id,threshold_row_sha256)",
    )
    assert "exact-retained-predecessor-raw-file-digests" in (
        primary.preimage_or_equality_formula
    )
    assert "threshold-value/operator/decision-law-remain-unresolved" in (
        primary.preimage_or_equality_formula
    )

    diagnostics = cross[
        "shard-request-raw-stable-and-receipt-facts-to-secondary-diagnostics-and-auxiliary-ledgers"
    ]
    assert diagnostics.target_pointer_or_components[:3] == (
        "secondary-/ordered_shard_receipt_sha256s",
        "secondary-/ordered_raw_file_sha256s",
        "secondary-/ordered_stable_file_sha256s",
    )
    assert "same-32-final-shard-files-and-receipts" in (
        diagnostics.preimage_or_equality_formula
    )

    decisions = cross["primary-metrics-and-power-thresholds-to-decisions"]
    assert decisions.source_artifact_ids == (
        "primary-metrics",
        "power-threshold-receipt",
        "power-review-signoff",
    )
    assert decisions.target_artifact_ids == ("decisions",)
    assert decisions.target_pointer_or_components == (
        "/primary_metrics_sha256",
        "/power_threshold_receipt_sha256",
        "/power_review_signoff_sha256",
        "/ordered_slot_decisions/*/(slot_ordinal,slot_id,primary_metric_record_sha256,threshold_row_sha256)",
    )
    assert "therefore-equal-the-primary-root-fields" in (
        decisions.preimage_or_equality_formula
    )
    assert "no-operator-or-PASS-FAIL-law" in decisions.preimage_or_equality_formula

    terminal = cross["decisions-and-auxiliary-ledgers-to-terminal-state"]
    assert "claims-no-direct-digest-binding" in terminal.preimage_or_equality_formula
    assert "rule23-preterminal-inventory-and-manifest" in (
        terminal.preimage_or_equality_formula
    )
    assert "cannot-produce-PASS-or-FAIL" in terminal.preimage_or_equality_formula


def test_environment_binding_is_one_way_and_crossbinding_graph_is_acyclic() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    environment = bundle.execution_output_semantic_rules[0]
    assert environment.artifact_id == "environment"
    assert (
        "sanitized-child-environment-exact17=" + repr(_SANITIZED_CHILD_ENVIRONMENT)
        in environment.nested_schema_rules
    )
    assert len(_SANITIZED_CHILD_ENVIRONMENT) == 17
    names = tuple(name for name, _ in _SANITIZED_CHILD_ENVIRONMENT)
    assert names == tuple(sorted(names))
    assert len(set(names)) == 17
    assert "production_runtime_receipt_sha256" not in environment.exact_top_level_keys
    assert environment.exact_top_level_keys == _OUTPUT_TOP_LEVEL_KEYS[0]
    occurrence = {row.artifact_id: row for row in bundle.artifact_occurrence_rules}
    assert occurrence["environment"].dependency_predecessor_artifact_ids == (
        "source-manifest",
        "dependency-lock",
        "freeze-receipt",
        "dependency-lock-match-receipt",
    )
    assert (
        "environment"
        in occurrence["production-runtime-receipt"].dependency_predecessor_artifact_ids
    )
    assert (
        "production-runtime-receipt"
        in occurrence[
            "external-seed-acquisition-start-receipt"
        ].dependency_predecessor_artifact_ids
    )
    cross = {row.rule_id: row for row in bundle.output_cross_binding_rules}[
        "environment-to-production-runtime-receipt"
    ]
    assert cross.source_artifact_ids == (
        "freeze-receipt",
        "source-manifest",
        "dependency-lock",
        "environment",
    )
    assert cross.source_pointer_or_components == (
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
    )
    assert cross.target_artifact_ids == ("production-runtime-receipt",)
    assert cross.target_pointer_or_components == (
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
    )
    assert "SHA256(exact-environment-file-bytes)" in (
        cross.preimage_or_equality_formula
    )
    graph: Dict[str, set] = {artifact_id: set() for artifact_id in _ARTIFACT_IDS}
    for row in bundle.output_cross_binding_rules:
        for source in row.source_artifact_ids:
            for target in row.target_artifact_ids:
                graph[source].add(target)
    visiting = set()
    visited = set()

    def visit(artifact_id: str) -> None:
        assert artifact_id not in visiting, "crossbinding cycle at %s" % artifact_id
        if artifact_id in visited:
            return
        visiting.add(artifact_id)
        for target in graph[artifact_id]:
            visit(target)
        visiting.remove(artifact_id)
        visited.add(artifact_id)

    for artifact_id in _ARTIFACT_IDS:
        visit(artifact_id)


def test_contract_bundle_and_every_rule_keep_candidate_only_nonclaims() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    contract = bundle.contract
    true_contract_fields = (
        "all_cp65_artifact_descriptors_preserved",
        "all_artifact_occurrences_closed",
        "all_branch_arms_mutually_exclusive_and_exhaustive",
        "all_conditional_occurrence_rules_closed",
        "all_output_envelope_framing_and_cross_binding_descriptors_candidate_complete",
        "all_cross_bindings_candidate_complete",
        "descriptor_bodies_only",
        "stdlib_only",
        "candidate_schema_inventory_complete",
        "candidate_descriptor_definition_complete",
        "primary_decision_semantics_deferred_to_external_power_review",
        "independent_structural_validator_required",
    )
    false_contract_fields = (
        "production_output_bodies_accepted",
        "public_caller_data_api_exposed",
        "project_modules_imported",
        "module_direct_filesystem_io",
        "module_direct_clock",
        "module_direct_rng",
        "module_direct_network",
        "module_direct_subprocess",
        "primary_decision_semantics_resolved",
        "schema_acceptance_independent",
        "authoritative_for_production",
        "production_schema_frozen",
        "production_execution_and_output_schema_frozen",
        "production_receipt_schema_frozen",
        "production_artifacts_observed",
        "production_evidence_accepted",
        "formal_test_28_closed",
    )
    assert all(getattr(contract, name) is True for name in true_contract_fields)
    assert all(getattr(contract, name) is False for name in false_contract_fields)
    assert contract.gate_states == ("MISSING",) * 17
    assert contract.blocker_states == ("MISSING",) * 4
    assert len(contract.gate_ids) == 17
    assert contract.blocker_ids == (
        "confirmatory_custody",
        "power_and_thresholds",
        "runner_and_recomputation",
        "unconditional_operational_predictions",
    )
    assert (
        contract.blocker_ledger_total_count,
        contract.blocker_ledger_satisfied_count,
        contract.blocker_ledger_missing_count,
    ) == (29, 25, 4)
    assert contract.formal_test_28_status == "OPEN"
    assert bundle.authoritative_builder_validates_internal_definition is True
    assert bundle.authoritative_builder_accepts_production_data is False
    assert bundle.candidate_descriptor_packet_internally_consistent is True
    assert bundle.candidate_descriptor_definition_complete is True
    assert bundle.candidate_schema_executable is False
    assert bundle.primary_decision_semantics_resolved is False
    assert bundle.primary_decision_semantics_deferred_to_external_power_review is True
    assert bundle.schema_acceptance_independent is False
    assert bundle.authoritative_for_production is False
    assert bundle.production_schema_frozen is False
    assert bundle.production_execution_and_output_schema_frozen is False
    assert bundle.production_receipt_schema_frozen is False
    assert bundle.production_evidence_accepted is False
    assert bundle.production_gate_states == ("MISSING",) * 17
    assert bundle.draft_blocker_states == ("MISSING",) * 4
    assert bundle.formal_test_28_status == "OPEN"
    assert bundle.formal_test_28_closed is False
    assert all(row.candidate_only is True for row in bundle.lifecycle_branch_rules)
    assert all(row.candidate_only is True for row in bundle.crash_cut_rules)
    assert all(row.candidate_only is True for row in bundle.artifact_occurrence_rules)
    assert all(
        row.candidate_only is True for row in bundle.execution_output_semantic_rules
    )
    assert all(row.candidate_only is True for row in bundle.output_cross_binding_rules)


def test_predecessor_custody_is_hash_reference_only_and_observes_nothing() -> None:
    custody = (
        cp74.cp74_production_occurrence_output_schema_candidate_bundle().predecessor_custody
    )
    assert custody.v24_protocol_markdown_sha256 == (
        "0609ac037cce6d5ef22cbf1ca7ccbc11aa46b3c9a192a8b08d12de9e8a6cf135"
    )
    assert custody.v24_protocol_markdown_bytes == 263_275
    assert custody.v24_protocol_markdown_lf_count == 4_278
    assert custody.v24_machine_manifest_sha256 == (
        "b271d19cd0a5f7f5912a1f324e88b565c7fe712111bb444d117c6ab650b6aadb"
    )
    assert custody.v24_machine_manifest_bytes == 6_249_780
    assert custody.v24_machine_manifest_lf_count == 121_879
    assert custody.predecessor_component_ids == (
        "cp64-production-custody-preflight",
        "cp65-production-schema-preimage-validator",
    )
    assert len(custody.predecessor_source_sha256s) == 2
    assert len(custody.predecessor_bundle_record_sha256s) == 2
    assert len(custody.predecessor_bundle_public_sha256s) == 2
    assert custody.cp65_schema_semantic_sha256 == (
        "8855d84a573344723bc6c4c32036b7aeb878d6c66a04d5423d5f591ed40316c0"
    )
    assert custody.cp65_gate_evidence_dag_node_count == 20
    assert custody.cp65_gate_evidence_dag_edge_count == 44
    assert custody.cp65_gate_evidence_dag_semantic_sha256 == (
        "eb9a83e70b243882e3579c7361bc3b0dbfed31be90344c5b1f536ac5ef4b9bc2"
    )
    assert custody.cp65_gate_evidence_dag_is_not_full_typed_graph is True
    assert custody.cp65_gate_evidence_artifact_id_aliases == (
        (
            "independent-full-32768-recomputation-receipt",
            "independent-full-32768-recomputation-qualification-receipt",
        ),
        (
            "independent-554-estimate-interval-decision-path-receipt",
            "independent-554-estimate-interval-decision-path-qualification-receipt",
        ),
    )
    assert custody.cp65_typed_artifact_preimage_graph_vector_lengths == (
        456,
        708,
        708,
        708,
        708,
        456,
    )
    assert custody.cp65_typed_artifact_preimage_graph_semantic_sha256 == (
        "a3b5b1511a7fd5abfb99f9c3ce0a413540541ef6899cfc534e8ab93bed8ef185"
    )
    assert custody.cp65_typed_digest_graph_inherited_by_hash_reference_only is True
    assert custody.cp65_typed_digest_graph_revalidated_by_cp74 is False
    assert custody.custody_is_hash_reference_only is True
    assert custody.predecessor_runtime_imports_performed is False
    assert custody.production_artifacts_observed is False


def test_canonical_graph_is_ascii_duplicate_free_float_free_and_bounded() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    records = (
        bundle.predecessor_custody,
        bundle.contract,
        *bundle.lifecycle_branch_rules,
        *bundle.crash_cut_rules,
        *bundle.artifact_occurrence_rules,
        *bundle.execution_output_semantic_rules,
        *bundle.output_cross_binding_rules,
        bundle,
    )
    duplicate_keys: List[str] = []

    def hook(pairs: List[Tuple[str, object]]) -> dict:
        keys = [key for key, _value in pairs]
        if len(keys) != len(set(keys)):
            duplicate_keys.extend(keys)
        return dict(pairs)

    def reject_float(value: str) -> object:
        raise AssertionError("float in CP74 canonical record: %s" % value)

    for record in records:
        payload = cp74.cp74_canonical_json_bytes(record)
        assert payload == _canonical(record)
        assert payload.isascii()
        assert len(payload) <= 1_048_576
        assert json.loads(
            payload.decode("ascii"),
            object_pairs_hook=hook,
            parse_float=reject_float,
            parse_constant=reject_float,
        ) == _plain(record)
    assert duplicate_keys == []
    assert len(cp74.cp74_canonical_json_bytes(bundle)) < 1_048_576


def test_record_apis_reject_unissued_tampered_and_pickle_attempts() -> None:
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    unissued = _unissued_copy(bundle.contract)
    for function in (cp74.cp74_canonical_json_bytes, cp74.cp74_sha256):
        with pytest.raises(ValueError, match="not issued"):
            function(unissued)
    with pytest.raises(TypeError, match="not pickle"):
        pickle.dumps(bundle)
    assert bundle != _unissued_copy(bundle)
    original = bundle.contract.scope
    object.__setattr__(bundle.contract, "scope", "tampered")
    try:
        for function in (cp74.cp74_canonical_json_bytes, cp74.cp74_sha256):
            with pytest.raises(ValueError, match="tampered"):
                function(bundle.contract)
    finally:
        object.__setattr__(bundle.contract, "scope", original)
    assert cp74.cp74_canonical_json_bytes(bundle.contract) == _canonical(
        bundle.contract
    )


def test_weak_registry_releases_complete_bundle_graph_without_a_cache() -> None:
    baseline = len(cp74._ISSUED_RECORD_SNAPSHOTS)
    bundle = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
    bundle_ref = weakref.ref(bundle)
    contract_ref = weakref.ref(bundle.contract)
    occurrence_ref = weakref.ref(bundle.artifact_occurrence_rules[0])
    assert len(cp74._ISSUED_RECORD_SNAPSHOTS) >= baseline + 123
    del bundle
    gc.collect()
    assert bundle_ref() is None
    assert contract_ref() is None
    assert occurrence_ref() is None
    assert len(cp74._ISSUED_RECORD_SNAPSHOTS) == baseline


def test_builder_and_issued_record_registry_are_thread_safe() -> None:
    with ThreadPoolExecutor(max_workers=8) as executor:
        bundles = list(
            executor.map(
                lambda _ordinal: cp74.cp74_production_occurrence_output_schema_candidate_bundle(),
                range(24),
            )
        )
        public_digests = list(executor.map(cp74.cp74_sha256, bundles))
        canonical = list(executor.map(cp74.cp74_canonical_json_bytes, bundles))
    assert len({id(bundle) for bundle in bundles}) == 24
    assert len({bundle.record_sha256 for bundle in bundles}) == 1
    assert len(set(public_digests)) == 1
    assert len(set(canonical)) == 1


def test_source_record_construction_literals_have_no_duplicate_string_keys() -> None:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"), filename=str(_SOURCE))
    duplicates = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        names = [
            key.value
            for key in node.keys
            if isinstance(key, ast.Constant) and type(key.value) is str
        ]
        if len(names) != len(set(names)):
            duplicates.append(names)
    assert duplicates == []


def test_locked_python39_import_and_bundle_build() -> None:
    if not _PYTHON39.is_file():
        pytest.skip("locked Python 3.9 executable is unavailable")
    script = r"""
import heterodiff.evaluation.mixed_initializer_test28_production_occurrence_output_schema_candidate as cp74
b = cp74.cp74_production_occurrence_output_schema_candidate_bundle()
assert len(cp74.__all__) == 29
assert len(b.artifact_occurrence_rules) == 64
assert len(b.execution_output_semantic_rules) == 15
assert len(b.lifecycle_branch_rules) == 11
assert len(b.crash_cut_rules) == 6
assert len(b.output_cross_binding_rules) == 24
assert b.production_schema_frozen is False
assert b.formal_test_28_status == "OPEN"
print("cp74-authoritative-python39-ok")
"""
    result = subprocess.run(
        [str(_PYTHON39), "-c", script],
        cwd=str(_ROOT),
        env={"PYTHONPATH": str(_ROOT / "src")},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "cp74-authoritative-python39-ok"
