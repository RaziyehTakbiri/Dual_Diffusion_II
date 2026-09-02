"""Hostile tests for the zero-production CP66 qualification harness."""

from __future__ import annotations

import ast
import builtins
import hashlib
import inspect
import json
import os
import pickle
import signal
import subprocess
import sys
import time
import weakref
from dataclasses import fields, is_dataclass
from pathlib import Path

import heterodiff.evaluation.mixed_initializer_test28_runner_supervisor_classifier_qualification as cp66
import pytest


class _SyntheticInfrastructureFault(BaseException):
    pass


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SOURCE_PATH = (
    _PROJECT_ROOT / "src/heterodiff/evaluation/"
    "mixed_initializer_test28_runner_supervisor_classifier_qualification.py"
)
_PROTOCOL_PATH = (
    _PROJECT_ROOT / "research/preregistrations/cp50_test28_mixed_initializer_v16.md"
)
_MANIFEST_PATH = (
    _PROJECT_ROOT / "research/fixtures/cp50_test28_mixed_initializer_v16.json"
)

_ZERO_SHA256 = "0" * 64
_V16_PROTOCOL_SHA256 = (
    "091c3e5240673165fd05c2042edc54bc0174353247b4fde47cf485bff969f3d8"
)
_V16_PROTOCOL_BYTES = 139_376
_V16_PROTOCOL_LF_COUNT = 2_484
_V16_MANIFEST_SHA256 = (
    "1ec8fb9427b2f28fcad3a749c708d5520f48e21985185cf5afc92ea6e9dc618f"
)
_V16_MANIFEST_BYTES = 5_993_725
_V16_MANIFEST_LF_COUNT = 118_260
_CP62_SOURCE_SHA256 = "44ef12b1a556d80944774ac9b698acf1359879fe44729120a04feb5e7a4a8a49"
_CP62_BUNDLE_SHA256 = "0f92f54ce8d451485019f6d697736fd5eb48d2b942e1d3a3f1bd373b50c3ec92"
_CP62_SEMANTIC_SHA256 = (
    "f3bd0b80c52a9d79a3b6a8e06aa2923c6303e891bf526c1869c5552e1413f3ff"
)
_CP62_SUPERVISOR_SHA256 = (
    "6dfb5b8bbb7cecabed1c84349bc32ac130dd2fb698ba400e0ce74d3ef58434fb"
)
_CP62_RAW_SCHEMA_SHA256 = (
    "ae77cdcf7142bac100236fc8db13411ac68e18c9e225869869223693d42b21f4"
)
_CP63_SOURCE_SHA256 = "27259edf2557a21b2527595eed7a954fc697755935e4a3deaeeb169765ba1c9c"
_CP63_RUNNER_BUNDLE_SHA256 = (
    "442c4b0f134a96efe32b5246b4eb5b05233d61a13c62c0a7d1f21c9bbbd32f85"
)
_CP63_RAW_SCHEMA_SHA256 = (
    "29f17aa7528971e7892b6ea4ccb37b5943190a0e592191341ae444e8ed63b3cb"
)
_CP64_SOURCE_SHA256 = "d35cbacb84e3348ae10549e053a0bb1572569583cdd03e66119353af4148bec2"
_CP64_BUNDLE_SHA256 = "32f7f0c62019d8ee906e6f74300f6c33fbe55984f69cfe4fe1061ffb92463f39"
_CP64_GATE_SHA256 = "7ceb4f12ce712e7123509eb6380e134876855bb91e90c64a951f7e1bcbcb2633"
_CP65_SOURCE_SHA256 = "774cd44ad6aa82ea629ef705bde3bbb7288ccd74bd0d3a5d5c79f552a5f6a06a"
_CP65_BUNDLE_SHA256 = "597f2b4b557bffb529d951858fd84e454135220db0c19dcd05fcf7ce93710f89"
_CP65_SEMANTIC_SHA256 = (
    "8855d84a573344723bc6c4c32036b7aeb878d6c66a04d5423d5f591ed40316c0"
)

_REFUSAL_CODES = (
    "plan_validation_refusal",
    "provider_reference_binding_refusal",
    "resource_preflight_refusal",
    "runtime_binding_refusal",
    "other_preexecution_refusal",
)
_FAILURE_CODES = (
    "reference_sampling_failure",
    "score_evaluation_failure",
    "quota_certification_failure",
    "float64_normalization_failure",
    "categorical_selection_failure",
    "structural_result_validation_failure",
    "other_execution_failure",
)
_RETURNED_REJECTION_STATUSES = (
    "returned-rejection-selected-before-deadline",
    "returned-rejection-exhausted-before-deadline",
)
_RETURNED_SIR_STATUSES = ("returned-sir-selected-before-deadline",)

_SUPERVISOR_CASE_IDS = (
    "timely-one-frame-clean-exit",
    "deadline-equality-clean-exit",
    "postdeadline-clean-exit",
    "hang-terminated-by-sigterm",
    "hang-ignores-sigterm-killed-by-sigkill",
    "descendant-process-group-cleanup",
    "zero-frame-clean-exit",
    "two-frame-clean-exit",
    "truncated-length-prefix",
    "truncated-frame-body",
    "oversize-frame",
    "abnormal-predeadline-exit",
    "stderr-over-cap",
    "no-extra-fd-control",
    "inherited-fd-drift",
    "environment-drift",
)
_SUPERVISOR_EXPECTED = (
    ("VALID", "VALID_RETURN"),
    ("TIMEOUT_CENSORED", "TIMEOUT_AT_DEADLINE"),
    ("TIMEOUT_CENSORED", "TIMEOUT_AFTER_DEADLINE"),
    ("TIMEOUT_CENSORED", "TIMEOUT_SIGTERM"),
    ("TIMEOUT_CENSORED", "TIMEOUT_SIGKILL"),
    ("TIMEOUT_CENSORED", "TIMEOUT_DESCENDANT_CLEANUP"),
    ("INFRASTRUCTURE_INVALID", "CHILD_FRAME_MISSING"),
    ("INFRASTRUCTURE_INVALID", "CHILD_MULTIPLE_OR_TRAILING_FRAMES"),
    ("INFRASTRUCTURE_INVALID", "CHILD_FRAME_PREFIX_TRUNCATED"),
    ("INFRASTRUCTURE_INVALID", "CHILD_FRAME_BODY_TRUNCATED"),
    ("INFRASTRUCTURE_INVALID", "CHILD_FRAME_LENGTH_OVERSIZED"),
    ("INFRASTRUCTURE_INVALID", "CHILD_ABNORMAL_EXIT"),
    ("INFRASTRUCTURE_INVALID", "CHILD_STDERR_OVERSIZED"),
    ("VALID", "VALID_RETURN"),
    ("INFRASTRUCTURE_INVALID", "CHILD_INHERITED_FD_DRIFT"),
    ("INFRASTRUCTURE_INVALID", "CHILD_ENVIRONMENT_DRIFT"),
)
_SUPERVISOR_ROWS = (
    (
        "before",
        "one",
        "clean",
        "none",
        "exact",
        "exact",
        _RETURNED_REJECTION_STATUSES[0],
        0,
    ),
    (
        "equal",
        "one",
        "clean",
        "none",
        "exact",
        "exact",
        "timeout-censored-at-deadline",
        0,
    ),
    (
        "after",
        "one",
        "clean",
        "none",
        "exact",
        "exact",
        "timeout-censored-at-deadline",
        0,
    ),
    (
        "after",
        "none",
        "wait-for-sigterm",
        "none",
        "exact",
        "exact",
        "timeout-censored-at-deadline",
        int(signal.SIGTERM),
    ),
    (
        "after",
        "none",
        "ignore-sigterm",
        "none",
        "exact",
        "exact",
        "timeout-censored-at-deadline",
        int(signal.SIGKILL),
    ),
    (
        "after",
        "none",
        "wait-for-sigterm",
        "holds-pipe",
        "exact",
        "exact",
        "timeout-censored-at-deadline",
        int(signal.SIGTERM),
    ),
    ("before", "zero", "clean", "none", "exact", "exact", "", 0),
    ("before", "two", "clean", "none", "exact", "exact", "", 0),
    ("before", "truncated-prefix", "clean", "none", "exact", "exact", "", 0),
    ("before", "truncated-body", "clean", "none", "exact", "exact", "", 0),
    ("before", "oversize", "clean", "none", "exact", "exact", "", 0),
    ("before", "zero", "abnormal", "none", "exact", "exact", "", 0),
    ("before", "one", "clean", "none", "exact", "exact", "", 0),
    ("before", "one", "clean", "none", "exact", "exact", _RETURNED_SIR_STATUSES[0], 0),
    ("before", "one", "clean", "none", "drift", "exact", "", 0),
    ("before", "one", "clean", "none", "exact", "drift", "", 0),
)
_CLASSIFIER_ACCEPTED_CASE_IDS = (
    "returned-rejection-selected",
    "returned-rejection-exhausted",
    "returned-sir-selected",
    "preexecution-refusal-plan_validation_refusal",
    "preexecution-refusal-provider_reference_binding_refusal",
    "preexecution-refusal-resource_preflight_refusal",
    "preexecution-refusal-runtime_binding_refusal",
    "preexecution-refusal-other_preexecution_refusal",
    "execution-failure-reference_sampling_failure",
    "execution-failure-score_evaluation_failure",
    "execution-failure-quota_certification_failure",
    "execution-failure-float64_normalization_failure",
    "execution-failure-categorical_selection_failure",
    "execution-failure-structural_result_validation_failure",
    "execution-failure-other_execution_failure",
    "timeout-censored",
)
_CLASSIFIER_REJECTED_CASE_IDS = (
    "unknown-phase",
    "unknown-returned-status",
    "strategy-incompatible-returned-status",
    "unknown-refusal-code",
    "unknown-failure-code",
    "refusal-code-under-failure-phase",
    "failure-code-under-refusal-phase",
    "failure-code-on-returned-or-timeout",
)

_RULE_ROWS = (
    (
        "plan-validation",
        "PREEXECUTION",
        "plan-validation-refused",
        "plan_validation_refusal",
    ),
    (
        "provider-reference-binding",
        "PREEXECUTION",
        "provider-reference-binding-refused",
        "provider_reference_binding_refusal",
    ),
    (
        "resource-preflight",
        "PREEXECUTION",
        "resource-preflight-refused",
        "resource_preflight_refusal",
    ),
    (
        "runtime-binding",
        "PREEXECUTION",
        "runtime-binding-refused",
        "runtime_binding_refusal",
    ),
    (
        "other-preexecution",
        "PREEXECUTION",
        "declared-other-preexecution-refused",
        "other_preexecution_refusal",
    ),
    (
        "reference-sampling",
        "EXECUTION",
        "reference-sampling-failed",
        "reference_sampling_failure",
    ),
    (
        "score-evaluation",
        "EXECUTION",
        "score-evaluation-failed",
        "score_evaluation_failure",
    ),
    (
        "quota-certification",
        "EXECUTION",
        "quota-certification-failed",
        "quota_certification_failure",
    ),
    (
        "float64-normalization",
        "EXECUTION",
        "float64-normalization-failed",
        "float64_normalization_failure",
    ),
    (
        "categorical-selection",
        "EXECUTION",
        "categorical-selection-failed",
        "categorical_selection_failure",
    ),
    (
        "structural-result-validation",
        "EXECUTION",
        "structural-result-validation-failed",
        "structural_result_validation_failure",
    ),
    (
        "other-execution",
        "EXECUTION",
        "declared-other-execution-failed",
        "other_execution_failure",
    ),
)

_CLASSIFIER_ROWS = (
    (
        (
            "returned-rejection-selected",
            "bounded-rejection",
            "returned-rejection-selected",
            "returned-before-deadline",
            _RETURNED_REJECTION_STATUSES[0],
            None,
            True,
            "CLASSIFICATION_ACCEPTED",
            _RETURNED_REJECTION_STATUSES[0],
            None,
            "CLASSIFIED",
        ),
        (
            "returned-rejection-exhausted",
            "bounded-rejection",
            "returned-rejection-exhausted",
            "returned-before-deadline",
            _RETURNED_REJECTION_STATUSES[1],
            None,
            True,
            "CLASSIFICATION_ACCEPTED",
            _RETURNED_REJECTION_STATUSES[1],
            None,
            "CLASSIFIED",
        ),
        (
            "returned-sir-selected",
            "fixed-budget-sir",
            "returned-sir-selected",
            "returned-before-deadline",
            _RETURNED_SIR_STATUSES[0],
            None,
            True,
            "CLASSIFICATION_ACCEPTED",
            _RETURNED_SIR_STATUSES[0],
            None,
            "CLASSIFIED",
        ),
    )
    + tuple(
        (
            (
                "preexecution-refusal-"
                if boundary == "PREEXECUTION"
                else "execution-failure-"
            )
            + failure_code,
            None,
            event_kind,
            (
                "preexecution-refusal-before-deadline"
                if boundary == "PREEXECUTION"
                else "execution-failure-before-deadline"
            ),
            (
                "preexecution-refusal-before-deadline"
                if boundary == "PREEXECUTION"
                else "execution-failure-before-deadline"
            ),
            failure_code,
            True,
            "CLASSIFICATION_ACCEPTED",
            (
                "preexecution-refusal-before-deadline"
                if boundary == "PREEXECUTION"
                else "execution-failure-before-deadline"
            ),
            failure_code,
            "CLASSIFIED",
        )
        for _, boundary, event_kind, failure_code in _RULE_ROWS
    )
    + (
        (
            "timeout-censored",
            None,
            "timeout-censored",
            "timeout-at-deadline",
            "timeout-censored-at-deadline",
            None,
            True,
            "CLASSIFICATION_ACCEPTED",
            "timeout-censored-at-deadline",
            None,
            "CLASSIFIED",
        ),
        (
            "unknown-phase",
            "bounded-rejection",
            "returned-rejection-selected",
            "unknown-phase",
            _RETURNED_REJECTION_STATUSES[0],
            None,
            False,
            "UNKNOWN_PHASE",
            "",
            None,
            "CLASSIFICATION_REJECTED",
        ),
        (
            "unknown-returned-status",
            "bounded-rejection",
            "returned-rejection-selected",
            "returned-before-deadline",
            "unknown-returned-status",
            None,
            False,
            "UNKNOWN_RETURNED_STATUS",
            "",
            None,
            "CLASSIFICATION_REJECTED",
        ),
        (
            "strategy-incompatible-returned-status",
            "bounded-rejection",
            "returned-sir-selected",
            "returned-before-deadline",
            _RETURNED_SIR_STATUSES[0],
            None,
            False,
            "STRATEGY_INCOMPATIBLE_RETURNED_STATUS",
            "",
            None,
            "CLASSIFICATION_REJECTED",
        ),
        (
            "unknown-refusal-code",
            None,
            "plan-validation-refused",
            "preexecution-refusal-before-deadline",
            "preexecution-refusal-before-deadline",
            "unknown_refusal_code",
            False,
            "UNKNOWN_REFUSAL_CODE",
            "",
            None,
            "CLASSIFICATION_REJECTED",
        ),
        (
            "unknown-failure-code",
            None,
            "reference-sampling-failed",
            "execution-failure-before-deadline",
            "execution-failure-before-deadline",
            "unknown_failure_code",
            False,
            "UNKNOWN_FAILURE_CODE",
            "",
            None,
            "CLASSIFICATION_REJECTED",
        ),
        (
            "refusal-code-under-failure-phase",
            None,
            "plan-validation-refused",
            "execution-failure-before-deadline",
            "execution-failure-before-deadline",
            "plan_validation_refusal",
            False,
            "REFUSAL_CODE_UNDER_FAILURE_PHASE",
            "",
            None,
            "CLASSIFICATION_REJECTED",
        ),
        (
            "failure-code-under-refusal-phase",
            None,
            "reference-sampling-failed",
            "preexecution-refusal-before-deadline",
            "preexecution-refusal-before-deadline",
            "reference_sampling_failure",
            False,
            "FAILURE_CODE_UNDER_REFUSAL_PHASE",
            "",
            None,
            "CLASSIFICATION_REJECTED",
        ),
        (
            "failure-code-on-returned-or-timeout",
            "bounded-rejection",
            "returned-rejection-selected",
            "returned-before-deadline",
            _RETURNED_REJECTION_STATUSES[0],
            "plan_validation_refusal",
            False,
            "FAILURE_CODE_ON_RETURNED_OR_TIMEOUT",
            "",
            None,
            "CLASSIFICATION_REJECTED",
        ),
    )
)

_PUBLIC_API = (
    "CP66_TEST28_SCHEMA_VERSION",
    "CP66_TEST28_SCOPE",
    "CP66QualificationError",
    "CP66_CLASSIFIER_PAYLOAD_MAX_BYTES",
    "CP66_QUALIFICATION_CASE_WALL_CEILING_SECONDS",
    "CP66_QUALIFICATION_SUITE_WALL_CEILING_SECONDS",
    "CP66PredecessorCustodyV1",
    "CP66ClosedClassifierContractV1",
    "CP66ClassifierRuleV1",
    "CP66SupervisorQualificationCaseV1",
    "CP66ClassifierQualificationCaseV1",
    "CP66QualificationCaseResultV1",
    "CP66QualificationRunV1",
    "CP66RunnerSupervisorClassifierQualificationBundleV1",
    "cp66_runner_supervisor_classifier_qualification_bundle",
    "cp66_qualification_fixture_set_sha256",
    "cp66_classify_supplied_observation",
    "cp66_run_qualification_case",
    "cp66_run_qualification_suite",
    "cp66_canonical_json_bytes",
    "cp66_sha256",
)

_FIELDS = {
    "CP66PredecessorCustodyV1": (
        "schema_version",
        "v16_protocol_sha256",
        "v16_protocol_bytes",
        "v16_protocol_lf_count",
        "v16_manifest_sha256",
        "v16_manifest_bytes",
        "v16_manifest_lf_count",
        "cp62_source_sha256",
        "cp62_bundle_record_sha256",
        "cp62_bundle_semantic_sha256",
        "cp62_supervisor_contract_record_sha256",
        "cp62_raw_record_schema_record_sha256",
        "cp63_source_sha256",
        "cp63_runner_bundle_record_sha256",
        "cp63_raw_record_schema_record_sha256",
        "cp64_source_sha256",
        "cp64_bundle_record_sha256",
        "cp64_no_execution_gate_contract_record_sha256",
        "cp65_source_sha256",
        "cp65_bundle_record_sha256",
        "cp65_schema_semantic_sha256",
        "record_sha256",
    ),
    "CP66ClosedClassifierContractV1": (
        "schema_version",
        "returned_rejection_statuses",
        "returned_sir_statuses",
        "timeout_phase",
        "timeout_status",
        "preexecution_refusal_phase",
        "preexecution_refusal_codes",
        "execution_failure_phase",
        "execution_failure_codes",
        "infrastructure_invalid_disposition",
        "timeout_is_semantic_nonreturn",
        "no_retry",
        "no_drop",
        "no_replacement",
        "no_topup",
        "unknown_phase_or_code_rejected",
        "record_sha256",
    ),
    "CP66ClassifierRuleV1": (
        "schema_version",
        "rule_ordinal",
        "stage_id",
        "execution_boundary_state",
        "accepted_internal_event_kind",
        "closed_phase",
        "closed_status",
        "failure_code",
        "arbitrary_base_exception_is_infrastructure",
        "record_sha256",
    ),
    "CP66SupervisorQualificationCaseV1": (
        "schema_version",
        "case_ordinal",
        "case_id",
        "child_mode",
        "deadline_relation",
        "frame_mode",
        "exit_mode",
        "descendant_mode",
        "fd_mode",
        "environment_mode",
        "expected_supervisor_disposition",
        "expected_machine_code",
        "expected_closed_status",
        "expected_term_signal",
        "exact_one_frame_expected",
        "process_group_empty_required",
        "no_fd_leak_required",
        "environment_match_required",
        "record_sha256",
    ),
    "CP66ClassifierQualificationCaseV1": (
        "schema_version",
        "case_ordinal",
        "case_id",
        "strategy",
        "event_kind",
        "phase",
        "closed_status",
        "failure_code",
        "expected_accept",
        "expected_machine_code",
        "expected_closed_status",
        "expected_failure_code",
        "expected_classifier_disposition",
        "record_sha256",
    ),
    "CP66QualificationCaseResultV1": (
        "schema_version",
        "case_ordinal",
        "case_id",
        "subsystem",
        "expected_disposition",
        "observed_disposition",
        "expected_machine_code",
        "observed_machine_code",
        "observed_closed_phase",
        "observed_closed_status",
        "observed_failure_code",
        "classifier_rule_ordinal",
        "timeout_observed",
        "process_group_cleanup_verified",
        "inherited_fd_count_after_exec",
        "environment_match",
        "exact_one_frame_observed",
        "completion_strictly_before_deadline",
        "termination_attempted",
        "termination_signal_delivered",
        "kill_attempted",
        "child_reaped",
        "process_group_empty",
        "stdout_byte_count",
        "stdout_sha256",
        "stderr_byte_count",
        "stderr_sha256",
        "passed",
        "normalized_semantic_sha256",
        "production_evidence",
        "record_sha256",
    ),
    "CP66QualificationRunV1": (
        "schema_version",
        "qualification_fixture_set_sha256",
        "ordered_case_ids",
        "ordered_case_result_sha256s",
        "case_count",
        "passed_case_count",
        "supervisor_case_count",
        "classifier_reachability_case_count",
        "classifier_rejection_case_count",
        "timeout_case_count",
        "process_group_cleanup_case_count",
        "fd_leak_case_count",
        "environment_drift_case_count",
        "all_cases_passed",
        "development_supervisor_mechanics_qualified",
        "development_classifier_mechanics_qualified",
        "qualification_python_profile_matched",
        "scaled_timing_not_production_clock_fidelity",
        "production_clock_fidelity_qualified",
        "volatile_pids_or_timestamps_in_semantic_digest",
        "production_qualification_receipt_present",
        "production_supervisor_qualified",
        "production_classifier_qualified",
        "production_execution_authorized",
        "runner_and_recomputation_blocker_closed",
        "formal_test_28_closed",
        "record_sha256",
    ),
    "CP66RunnerSupervisorClassifierQualificationBundleV1": (
        "schema_version",
        "scope",
        "predecessor_custody",
        "closed_classifier_contract",
        "classifier_rules",
        "classifier_rule_count",
        "supervisor_cases",
        "classifier_cases",
        "qualification_fixture_set_sha256",
        "supervisor_case_count",
        "classifier_reachability_case_count",
        "classifier_rejection_case_count",
        "total_case_count",
        "zero_argument_builder",
        "builder_executes_child",
        "generic_command_api_exposed",
        "production_seed_or_request_api_exposed",
        "production_campaign_api_exposed",
        "source_manifest_observed",
        "production_runtime_receipt_observed",
        "freeze_receipt_present",
        "production_runner_implemented",
        "production_runner_supervisor_qualified",
        "production_closed_classifier_qualified",
        "production_qualification_receipts_present",
        "production_execution_observed",
        "runner_and_recomputation_blocker_closed",
        "unconditional_operational_predictions_blocker_closed",
        "power_and_thresholds_blocker_closed",
        "confirmatory_custody_blocker_closed",
        "confirmatory_evidence",
        "manuscript_claim",
        "formal_test_28_status",
        "formal_test_28_closed",
        "ledger_prerequisite_id",
        "ledger_prerequisite_state",
        "ledger_total_count",
        "ledger_satisfied_count",
        "ledger_missing_count",
        "record_sha256",
    ),
}

_DOMAINS = {
    "CP66PredecessorCustodyV1": b"cp66-test28-predecessor-custody-v1",
    "CP66ClosedClassifierContractV1": (b"cp66-test28-closed-classifier-contract-v1"),
    "CP66ClassifierRuleV1": b"cp66-test28-classifier-rule-v1",
    "CP66SupervisorQualificationCaseV1": (
        b"cp66-test28-supervisor-qualification-case-v1"
    ),
    "CP66ClassifierQualificationCaseV1": (
        b"cp66-test28-classifier-qualification-case-v1"
    ),
    "CP66QualificationCaseResultV1": (b"cp66-test28-qualification-case-result-v1"),
    "CP66QualificationRunV1": b"cp66-test28-qualification-run-v1",
    "CP66RunnerSupervisorClassifierQualificationBundleV1": (
        b"cp66-test28-runner-supervisor-classifier-qualification-bundle-v1"
    ),
}


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _plain(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _plain(getattr(value, field.name)) for field in fields(value)
        }
    if type(value) is tuple:
        return [_plain(item) for item in value]
    if type(value) is list:
        return [_plain(item) for item in value]
    if type(value) is dict:
        return {key: _plain(item) for key, item in value.items()}
    return value


def _record_digest(record: object) -> str:
    primitive = _plain(record)
    assert type(primitive) is dict
    primitive["record_sha256"] = _ZERO_SHA256
    return hashlib.sha256(
        _DOMAINS[type(record).__name__] + b"\0" + _canonical(primitive)
    ).hexdigest()


def _case_semantic_digest(record: object) -> str:
    primitive = _plain(record)
    assert type(primitive) is dict
    primitive["normalized_semantic_sha256"] = _ZERO_SHA256
    primitive["record_sha256"] = _ZERO_SHA256
    return hashlib.sha256(
        b"cp66-test28-normalized-qualification-case-semantic-v1\0"
        + _canonical(primitive)
    ).hexdigest()


def _file_metrics(path: Path) -> tuple[str, int, int]:
    payload = path.read_bytes()
    return hashlib.sha256(payload).hexdigest(), len(payload), payload.count(b"\n")


def _bundle() -> object:
    return cp66.cp66_runner_supervisor_classifier_qualification_bundle()


def _classifier_payload(case: object) -> bytes:
    """Build one canonical event without trusting a source-side fixture helper."""

    return _canonical(
        {
            "schema": cp66.CP66_TEST28_SCHEMA_VERSION,
            "case_id": case.case_id,
            "strategy": case.strategy,
            "event_kind": case.event_kind,
            "phase": case.phase,
            "closed_status": case.closed_status,
            "failure_code": case.failure_code,
        }
    )


def _decode_raw_frame(payload: bytes, offset: int = 0) -> tuple[dict, int]:
    assert len(payload) - offset >= 8
    announced = int.from_bytes(payload[offset : offset + 8], "big")
    assert 0 < announced <= 16_777_216
    end = offset + 8 + announced
    assert end <= len(payload)
    body = payload[offset + 8 : end]
    document = json.loads(body)
    assert type(document) is dict
    assert _canonical(document) == body
    assert tuple(sorted(document)) == (
        "case_id",
        "closed_status",
        "environment_match",
        "inherited_fd_count_after_exec",
        "schema",
        "source_sha256",
    )
    return document, end


def test_cp66_live_predecessor_bytes_and_exact_custody_pins() -> None:
    assert _file_metrics(_PROTOCOL_PATH) == (
        _V16_PROTOCOL_SHA256,
        _V16_PROTOCOL_BYTES,
        _V16_PROTOCOL_LF_COUNT,
    )
    assert _file_metrics(_MANIFEST_PATH) == (
        _V16_MANIFEST_SHA256,
        _V16_MANIFEST_BYTES,
        _V16_MANIFEST_LF_COUNT,
    )
    source_paths = {
        "cp62_source_sha256": _PROJECT_ROOT
        / "src/heterodiff/evaluation/mixed_initializer_test28_execution_capsule.py",
        "cp63_source_sha256": _PROJECT_ROOT / "src/heterodiff/evaluation/"
        "mixed_initializer_test28_runner_recomputation_rehearsal.py",
        "cp64_source_sha256": _PROJECT_ROOT
        / "src/heterodiff/evaluation/mixed_initializer_test28_production_custody_preflight.py",
        "cp65_source_sha256": _PROJECT_ROOT
        / "src/heterodiff/evaluation/mixed_initializer_test28_production_schema_preimage_validator.py",
    }
    expected = {
        "cp62_source_sha256": _CP62_SOURCE_SHA256,
        "cp63_source_sha256": _CP63_SOURCE_SHA256,
        "cp64_source_sha256": _CP64_SOURCE_SHA256,
        "cp65_source_sha256": _CP65_SOURCE_SHA256,
    }
    bundle = _bundle()
    custody = bundle.predecessor_custody
    for field_name, path in source_paths.items():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == expected[field_name] == getattr(custody, field_name)
    assert (
        custody.v16_protocol_sha256,
        custody.v16_protocol_bytes,
        custody.v16_protocol_lf_count,
    ) == (_V16_PROTOCOL_SHA256, _V16_PROTOCOL_BYTES, _V16_PROTOCOL_LF_COUNT)
    assert (
        custody.v16_manifest_sha256,
        custody.v16_manifest_bytes,
        custody.v16_manifest_lf_count,
    ) == (_V16_MANIFEST_SHA256, _V16_MANIFEST_BYTES, _V16_MANIFEST_LF_COUNT)
    assert custody.cp62_bundle_record_sha256 == _CP62_BUNDLE_SHA256
    assert custody.cp62_bundle_semantic_sha256 == _CP62_SEMANTIC_SHA256
    assert custody.cp62_supervisor_contract_record_sha256 == _CP62_SUPERVISOR_SHA256
    assert custody.cp62_raw_record_schema_record_sha256 == _CP62_RAW_SCHEMA_SHA256
    assert custody.cp63_runner_bundle_record_sha256 == _CP63_RUNNER_BUNDLE_SHA256
    assert custody.cp63_raw_record_schema_record_sha256 == _CP63_RAW_SCHEMA_SHA256
    assert custody.cp64_bundle_record_sha256 == _CP64_BUNDLE_SHA256
    assert custody.cp64_no_execution_gate_contract_record_sha256 == _CP64_GATE_SHA256
    assert custody.cp65_bundle_record_sha256 == _CP65_BUNDLE_SHA256
    assert custody.cp65_schema_semantic_sha256 == _CP65_SEMANTIC_SHA256


def test_cp66_public_surface_is_exact_and_has_no_production_entry_point() -> None:
    assert cp66.CP66_TEST28_SCHEMA_VERSION == (
        "cp66-test28-runner-supervisor-classifier-qualification-v1"
    )
    assert cp66.CP66_TEST28_SCOPE == (
        "development-only-runner-supervisor-and-closed-classifier-qualification;"
        "closed-forty-case-fixture-set;internal-case-ids-only;no-generic-command;"
        "no-path-api;no-request-api;no-seed-api;no-campaign;no-production-launch;"
        "no-production-execution;no-evidence-acceptance;no-blocker-closure"
    )
    assert (
        type(cp66.CP66_CLASSIFIER_PAYLOAD_MAX_BYTES) is int
        and cp66.CP66_CLASSIFIER_PAYLOAD_MAX_BYTES == 16_384
    )
    assert (
        type(cp66.CP66_QUALIFICATION_CASE_WALL_CEILING_SECONDS) is int
        and cp66.CP66_QUALIFICATION_CASE_WALL_CEILING_SECONDS == 5
    )
    assert (
        type(cp66.CP66_QUALIFICATION_SUITE_WALL_CEILING_SECONDS) is int
        and cp66.CP66_QUALIFICATION_SUITE_WALL_CEILING_SECONDS == 30
    )
    assert tuple(cp66.__all__) == _PUBLIC_API
    forbidden_fragments = (
        "authorize",
        "materialize",
        "production_run",
        "run_campaign",
        "execute_request",
        "seed_ingest",
        "writer",
        "sign_",
        "approve",
        "freeze_",
    )
    for name in cp66.__all__:
        lowered = name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
    assert (
        inspect.signature(
            cp66.cp66_runner_supervisor_classifier_qualification_bundle
        ).parameters
        == {}
    )
    assert (
        inspect.signature(cp66.cp66_qualification_fixture_set_sha256).parameters == {}
    )
    assert tuple(
        inspect.signature(cp66.cp66_classify_supplied_observation).parameters
    ) == ("payload",)
    assert tuple(inspect.signature(cp66.cp66_run_qualification_case).parameters) == (
        "case_id",
    )
    assert inspect.signature(cp66.cp66_run_qualification_suite).parameters == {}


def test_cp66_source_is_independent_and_has_no_generic_execution_surface() -> None:
    source = _SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert "heterodiff" not in imported_roots
    assert "numpy" not in imported_roots
    assert "scipy" not in imported_roots
    public_functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    assert set(public_functions) == {
        name for name in _PUBLIC_API if name.startswith("cp66_")
    }
    assert "shell=True" not in source
    assert "os.system" not in source
    assert "random" not in imported_roots
    assert "socket" not in imported_roots


@pytest.mark.parametrize("class_name,expected", tuple(_FIELDS.items()))
def test_cp66_sealed_record_field_order_and_slots(
    class_name: str, expected: tuple[str, ...]
) -> None:
    record_type = getattr(cp66, class_name)
    assert tuple(field.name for field in fields(record_type)) == expected
    assert record_type.__slots__ == expected
    with pytest.raises(TypeError):
        type("ForbiddenSubclass", (record_type,), {})


def test_cp66_records_are_sealed_nonpickleable_and_independently_digested() -> None:
    bundle = _bundle()
    records = [
        bundle.predecessor_custody,
        bundle.closed_classifier_contract,
        *bundle.classifier_rules,
        *bundle.supervisor_cases,
        *bundle.classifier_cases,
        bundle,
    ]
    for record in records:
        assert not hasattr(record, "__dict__")
        assert weakref.ref(record)() is record
        with pytest.raises(TypeError):
            type(record)()
        with pytest.raises((AttributeError, TypeError)):
            setattr(record, "record_sha256", _ZERO_SHA256)
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(record)
        assert record.record_sha256 == _record_digest(record)
        assert cp66.cp66_canonical_json_bytes(record) == _canonical(_plain(record))
        assert (
            cp66.cp66_sha256(record)
            == hashlib.sha256(
                b"cp66-public-record-v1\0"
                + type(record).__name__.encode("ascii")
                + b"\0"
                + _canonical(_plain(record))
            ).hexdigest()
        )


def test_cp66_builder_is_deterministic_and_executes_no_children(monkeypatch) -> None:
    calls: list[tuple[object, ...]] = []

    def forbidden(*args: object, **kwargs: object) -> None:
        calls.append(args + (kwargs,))
        raise AssertionError("the zero-argument builder executed a child")

    for name in ("fork", "posix_spawn", "posix_spawnp", "system"):
        if hasattr(os, name):
            monkeypatch.setattr(os, name, forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(time, "time", forbidden)
    monkeypatch.setattr(time, "monotonic", forbidden)
    monkeypatch.setattr(time, "monotonic_ns", forbidden)
    first = _bundle()
    second = _bundle()
    assert calls == []
    assert cp66.cp66_canonical_json_bytes(first) == cp66.cp66_canonical_json_bytes(
        second
    )
    assert first.record_sha256 == second.record_sha256
    assert first.zero_argument_builder is True
    assert first.builder_executes_child is False


def test_cp66_classifier_contract_and_exact_rule_registry() -> None:
    bundle = _bundle()
    contract = bundle.closed_classifier_contract
    assert contract.returned_rejection_statuses == _RETURNED_REJECTION_STATUSES
    assert contract.returned_sir_statuses == _RETURNED_SIR_STATUSES
    assert contract.timeout_phase == "timeout-at-deadline"
    assert contract.timeout_status == "timeout-censored-at-deadline"
    assert contract.preexecution_refusal_phase == (
        "preexecution-refusal-before-deadline"
    )
    assert contract.preexecution_refusal_codes == _REFUSAL_CODES
    assert contract.execution_failure_phase == "execution-failure-before-deadline"
    assert contract.execution_failure_codes == _FAILURE_CODES
    assert contract.timeout_is_semantic_nonreturn is False
    assert contract.no_retry is True
    assert contract.no_drop is True
    assert contract.no_replacement is True
    assert contract.no_topup is True
    assert contract.unknown_phase_or_code_rejected is True
    assert bundle.classifier_rule_count == len(bundle.classifier_rules) == 12
    observed = []
    for ordinal, rule in enumerate(bundle.classifier_rules, 1):
        assert rule.rule_ordinal == ordinal
        assert rule.arbitrary_base_exception_is_infrastructure is True
        observed.append(
            (
                rule.stage_id,
                rule.execution_boundary_state,
                rule.accepted_internal_event_kind,
                rule.failure_code,
            )
        )
        expected_phase = (
            "preexecution-refusal-before-deadline"
            if ordinal <= 5
            else "execution-failure-before-deadline"
        )
        assert rule.closed_phase == expected_phase
        assert rule.closed_status == expected_phase
    assert tuple(observed) == _RULE_ROWS
    assert len({row[0] for row in observed}) == 12
    assert len({row[2] for row in observed}) == 12
    assert {row[3] for row in observed} == set(_REFUSAL_CODES + _FAILURE_CODES)


def test_cp66_case_rosters_counts_order_and_fixture_digest() -> None:
    bundle = _bundle()
    assert tuple(case.case_id for case in bundle.supervisor_cases) == (
        _SUPERVISOR_CASE_IDS
    )
    assert tuple(case.case_ordinal for case in bundle.supervisor_cases) == tuple(
        range(1, 17)
    )
    assert tuple(case.case_id for case in bundle.classifier_cases) == (
        _CLASSIFIER_ACCEPTED_CASE_IDS + _CLASSIFIER_REJECTED_CASE_IDS
    )
    assert tuple(case.case_ordinal for case in bundle.classifier_cases) == tuple(
        range(1, 25)
    )
    assert (
        tuple(
            (
                case.case_id,
                case.strategy,
                case.event_kind,
                case.phase,
                case.closed_status,
                case.failure_code,
                case.expected_accept,
                case.expected_machine_code,
                case.expected_closed_status,
                case.expected_failure_code,
                case.expected_classifier_disposition,
            )
            for case in bundle.classifier_cases
        )
        == _CLASSIFIER_ROWS
    )
    assert bundle.supervisor_case_count == 16
    assert bundle.classifier_reachability_case_count == 16
    assert bundle.classifier_rejection_case_count == 8
    assert bundle.total_case_count == 40
    assert (
        tuple(
            (
                case.expected_supervisor_disposition,
                case.expected_machine_code,
            )
            for case in bundle.supervisor_cases
        )
        == _SUPERVISOR_EXPECTED
    )
    digests = [case.record_sha256 for case in bundle.supervisor_cases]
    digests.extend(case.record_sha256 for case in bundle.classifier_cases)
    expected = hashlib.sha256(
        b"cp66-test28-qualification-fixture-set-v1\0" + _canonical(digests)
    ).hexdigest()
    assert bundle.qualification_fixture_set_sha256 == expected
    assert cp66.cp66_qualification_fixture_set_sha256() == expected
    assert (
        len(
            set(
                _SUPERVISOR_CASE_IDS
                + _CLASSIFIER_ACCEPTED_CASE_IDS
                + _CLASSIFIER_REJECTED_CASE_IDS
            )
        )
        == 40
    )


def test_cp66_supervisor_case_expectations_are_not_self_contradictory() -> None:
    cases = {case.case_id: case for case in _bundle().supervisor_cases}
    ordered = tuple(cases[case_id] for case_id in _SUPERVISOR_CASE_IDS)
    assert all(
        case.child_mode == "same-source-closed-case-posix-spawn-exec"
        for case in ordered
    )
    assert (
        tuple(
            (
                case.deadline_relation,
                case.frame_mode,
                case.exit_mode,
                case.descendant_mode,
                case.fd_mode,
                case.environment_mode,
                case.expected_closed_status,
                case.expected_term_signal,
            )
            for case in ordered
        )
        == _SUPERVISOR_ROWS
    )
    assert tuple(case.exact_one_frame_expected for case in ordered) == tuple(
        row[1] == "one" for row in _SUPERVISOR_ROWS
    )
    assert tuple(case.process_group_empty_required for case in ordered) == (
        False,
        False,
        False,
        True,
        True,
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    )
    assert tuple(case.no_fd_leak_required for case in ordered) == (
        (False,) * 13 + (True, False, False)
    )
    assert tuple(case.environment_match_required for case in ordered) == (
        (False,) * 13 + (True, False, False)
    )
    valid = {"timely-one-frame-clean-exit", "no-extra-fd-control"}
    timeout = {
        "deadline-equality-clean-exit",
        "postdeadline-clean-exit",
        "hang-terminated-by-sigterm",
        "hang-ignores-sigterm-killed-by-sigkill",
        "descendant-process-group-cleanup",
    }
    invalid = set(_SUPERVISOR_CASE_IDS) - valid - timeout
    assert len(invalid) == 9
    for case_id in valid:
        case = cases[case_id]
        assert case.exact_one_frame_expected is True
        assert (
            case.expected_closed_status
            in _RETURNED_REJECTION_STATUSES + _RETURNED_SIR_STATUSES
        )
    for case_id in timeout:
        case = cases[case_id]
        assert case.expected_closed_status == "timeout-censored-at-deadline"
    for case_id in invalid:
        assert cases[case_id].expected_supervisor_disposition == (
            "INFRASTRUCTURE_INVALID"
        )
        assert cases[case_id].expected_closed_status == ""
    assert (
        tuple(
            (
                cases[case_id].expected_supervisor_disposition,
                cases[case_id].expected_machine_code,
            )
            for case_id in _SUPERVISOR_CASE_IDS
        )
        == _SUPERVISOR_EXPECTED
    )
    for case_id in (
        "hang-terminated-by-sigterm",
        "hang-ignores-sigterm-killed-by-sigkill",
        "descendant-process-group-cleanup",
    ):
        assert cases[case_id].process_group_empty_required is True
    assert cases["hang-terminated-by-sigterm"].expected_term_signal == signal.SIGTERM
    assert (
        cases["hang-ignores-sigterm-killed-by-sigkill"].expected_term_signal
        == signal.SIGKILL
    )
    assert cases["no-extra-fd-control"].no_fd_leak_required is True
    assert cases["no-extra-fd-control"].environment_match_required is True
    assert cases["inherited-fd-drift"].no_fd_leak_required is False
    assert cases["environment-drift"].environment_match_required is False


@pytest.mark.parametrize("case_index", range(24))
def test_cp66_classifier_case_matrix_against_independent_oracle(
    case_index: int,
) -> None:
    case = _bundle().classifier_cases[case_index]
    accepted = case_index < 16
    assert case.expected_accept is accepted
    if accepted:
        result = cp66.cp66_classify_supplied_observation(_classifier_payload(case))
        assert result.case_id == case.case_id
        assert result.observed_closed_phase == case.phase
        assert result.observed_closed_status == case.expected_closed_status
        assert result.observed_failure_code == case.expected_failure_code
        expected_rule_ordinal = case_index - 2 if 3 <= case_index <= 14 else None
        assert result.classifier_rule_ordinal == expected_rule_ordinal
        assert result.production_evidence is False
    else:
        with pytest.raises(cp66.CP66QualificationError) as caught:
            cp66.cp66_classify_supplied_observation(_classifier_payload(case))
        assert caught.value.code == case.expected_machine_code


@pytest.mark.parametrize("case_index", range(24))
def test_cp66_classifier_run_case_records_expected_acceptance_or_rejection(
    case_index: int,
) -> None:
    case = _bundle().classifier_cases[case_index]
    result = cp66.cp66_run_qualification_case(case.case_id)
    assert result.case_id == case.case_id
    assert result.subsystem == "classifier"
    assert result.expected_disposition == case.expected_classifier_disposition
    assert result.observed_disposition == case.expected_classifier_disposition
    assert result.expected_machine_code == case.expected_machine_code
    assert result.observed_machine_code == case.expected_machine_code
    assert result.observed_closed_phase == (case.phase if case.expected_accept else "")
    assert result.observed_closed_status == case.expected_closed_status
    assert result.observed_failure_code == case.expected_failure_code
    expected_rule_ordinal = case_index - 2 if 3 <= case_index <= 14 else None
    assert result.classifier_rule_ordinal == expected_rule_ordinal
    assert result.timeout_observed is False
    assert result.process_group_cleanup_verified is False
    assert result.inherited_fd_count_after_exec is None
    assert result.environment_match is None
    assert result.exact_one_frame_observed is False
    assert result.completion_strictly_before_deadline is False
    assert result.termination_attempted is False
    assert result.termination_signal_delivered is False
    assert result.kill_attempted is False
    assert result.child_reaped is False
    assert result.process_group_empty is False
    assert result.passed is True
    assert result.production_evidence is False
    assert result.normalized_semantic_sha256 == _case_semantic_digest(result)
    assert result.record_sha256 == _record_digest(result)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda document: document.pop("phase"),
        lambda document: document.__setitem__("extra", False),
        lambda document: document.__setitem__("strategy", True),
        lambda document: document.__setitem__("phase", ""),
        lambda document: document.__setitem__("event_kind", "unknown"),
        lambda document: document.__setitem__("failure_code", 1),
    ),
)
def test_cp66_classifier_parser_rejects_hostile_mutations(mutation) -> None:
    case = _bundle().classifier_cases[0]
    document = json.loads(_classifier_payload(case))
    mutation(document)
    with pytest.raises((TypeError, ValueError, cp66.CP66QualificationError)):
        cp66.cp66_classify_supplied_observation(_canonical(document))


@pytest.mark.parametrize(
    "case_index,wrong_known_code",
    (
        (3, "runtime_binding_refusal"),
        (8, "score_evaluation_failure"),
    ),
)
def test_cp66_classifier_rejects_known_event_with_wrong_same_phase_code(
    case_index: int, wrong_known_code: str
) -> None:
    case = _bundle().classifier_cases[case_index]
    document = json.loads(_classifier_payload(case))
    document["failure_code"] = wrong_known_code
    with pytest.raises(cp66.CP66QualificationError):
        cp66.cp66_classify_supplied_observation(_canonical(document))


def test_cp66_classifier_parser_rejects_noncanonical_and_resource_attacks() -> None:
    case = _bundle().classifier_cases[0]
    document = json.loads(_classifier_payload(case))
    pretty = json.dumps(document, indent=2, sort_keys=True).encode("ascii")
    duplicate = _classifier_payload(case).replace(
        b'"case_id":"' + case.case_id.encode("ascii") + b'",',
        b'"case_id":"'
        + case.case_id.encode("ascii")
        + b'","case_id":"'
        + case.case_id.encode("ascii")
        + b'",',
        1,
    )
    attacks = (
        pretty,
        duplicate,
        _classifier_payload(case) + b"\n",
        b"\xff",
        b"[1]",
        b"{" + b'"x":' + b"[" * 64 + b"0" + b"]" * 64 + b"}",
        b" " * (cp66.CP66_CLASSIFIER_PAYLOAD_MAX_BYTES + 1),
    )
    for payload in attacks:
        with pytest.raises(
            (TypeError, ValueError, RecursionError, cp66.CP66QualificationError)
        ):
            cp66.cp66_classify_supplied_observation(payload)
    with pytest.raises(TypeError):
        cp66.cp66_classify_supplied_observation(bytearray(_classifier_payload(case)))


def test_cp66_arbitrary_base_exceptions_never_map_to_other_codes() -> None:
    classifier_source = inspect.getsource(cp66.cp66_classify_supplied_observation)
    assert "except BaseException" not in classifier_source
    for forbidden in (
        "MemoryError",
        "OSError",
        "BrokenPipeError",
        "ProcessLookupError",
    ):
        assert forbidden not in classifier_source
    rule_events = {
        rule.accepted_internal_event_kind for rule in _bundle().classifier_rules
    }
    assert "declared-other-preexecution-refused" in rule_events
    assert "declared-other-execution-failed" in rule_events
    assert all("exception" not in event for event in rule_events)


def test_cp66_run_case_refuses_nonexact_and_nonroster_identifiers() -> None:
    for case_id in ("", "unknown", _SUPERVISOR_CASE_IDS[0] + " ", "../escape"):
        with pytest.raises((TypeError, ValueError, cp66.CP66QualificationError)):
            cp66.cp66_run_qualification_case(case_id)
    for value in (None, 1, True, b"timely-one-frame-clean-exit"):
        with pytest.raises((TypeError, ValueError, cp66.CP66QualificationError)):
            cp66.cp66_run_qualification_case(value)


def test_cp66_duplicate_key_child_frame_has_stable_invalid_body_code() -> None:
    case_id = "timely-one-frame-clean-exit"
    body = (
        b'{"case_id":"'
        + case_id.encode("ascii")
        + b'","case_id":"'
        + case_id.encode("ascii")
        + b'"}'
    )
    frame = len(body).to_bytes(8, "big") + body
    with pytest.raises(cp66.CP66QualificationError) as caught:
        cp66._decode_child_frame(
            frame,
            case_id,
            hashlib.sha256(_SOURCE_PATH.read_bytes()).hexdigest(),
        )
    assert caught.value.code == "CHILD_FRAME_BODY_INVALID"


def test_cp66_continuous_full_chunk_stream_drain_is_hard_bounded() -> None:
    script = r"""
import heterodiff.evaluation.mixed_initializer_test28_runner_supervisor_classifier_qualification as cp66

class Key:
    fd = 123
    data = "stdout"

class Selector:
    def select(self, timeout):
        assert timeout == 0.0
        return ((Key(), 1),)

    def unregister(self, file_descriptor):
        raise AssertionError(file_descriptor)

read_count = 0

def endless_full_chunk(file_descriptor, maximum_bytes):
    global read_count
    assert file_descriptor == 123
    assert maximum_bytes == 65_536
    read_count += 1
    return b"X" * 65_536

cp66.os.read = endless_full_chunk
stdout = bytearray()
cp66._read_ready_streams(Selector(), stdout, bytearray(), timeout=0.0)
assert 1 <= read_count <= 257
assert 1 <= len(stdout) <= cp66.CP66_TEST28_RAW_FRAME_MAX_BYTES + 16
"""
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = "src:."
    completed = subprocess.run(
        [sys.executable, "-W", "error", "-c", script],
        cwd=_PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=2.0,
        check=False,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_cp66_no_progress_reap_never_falls_back_to_blocking_waitpid() -> None:
    source_tree = ast.parse(_SOURCE_PATH.read_text(encoding="utf-8"))
    blocking_waits = tuple(
        node
        for node in ast.walk(source_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
        and node.func.attr == "waitpid"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == 0
    )
    assert blocking_waits == ()

    script = r"""
import time
import heterodiff.evaluation.mixed_initializer_test28_runner_supervisor_classifier_qualification as cp66

cp66._process_group_exists = lambda pid: True
cp66._send_process_group_signal = lambda pid, signal_number: True
cp66._wait_child_nonblocking = lambda pid: None
cp66._wait_for_group_absence = lambda pid, ceiling_seconds: False

def forbidden_blocking_waitpid(pid, options):
    assert options == 0
    time.sleep(60)

cp66.os.waitpid = forbidden_blocking_waitpid
try:
    cp66._terminate_timeout_group(424_242, None)
except cp66.CP66QualificationError as error:
    assert error.code == "CHILD_REAP_CEILING_EXPIRED"
else:
    raise AssertionError("an unreaped child did not raise a bounded infrastructure error")
"""
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = "src:."
    completed = subprocess.run(
        [sys.executable, "-W", "error", "-c", script],
        cwd=_PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=2.0,
        check=False,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert completed.stdout == ""
    assert completed.stderr == ""


@pytest.mark.parametrize("case_id", _SUPERVISOR_CASE_IDS)
def test_cp66_each_supervisor_boundary_is_bounded_and_matches_contract(
    case_id: str, monkeypatch
) -> None:
    expected = next(
        case for case in _bundle().supervisor_cases if case.case_id == case_id
    )
    original_spawn = cp66._spawn_qualification_child
    original_read = cp66._read_ready_streams
    original_group_exists = cp66._process_group_exists
    spawned: list[tuple[str, int]] = []
    observed_streams = {"stdout": b"", "stderr": b""}

    def spawn_spy(case):
        result = original_spawn(case)
        spawned.append((case.case_id, result[0]))
        return result

    def read_spy(selector, stdout, stderr, *, timeout):
        original_read(selector, stdout, stderr, timeout=timeout)
        observed_streams["stdout"] = bytes(stdout)
        observed_streams["stderr"] = bytes(stderr)

    monkeypatch.setattr(cp66, "_spawn_qualification_child", spawn_spy)
    monkeypatch.setattr(cp66, "_read_ready_streams", read_spy)
    started = time.monotonic()
    result = cp66.cp66_run_qualification_case(case_id)
    elapsed = time.monotonic() - started
    assert elapsed < cp66.CP66_QUALIFICATION_CASE_WALL_CEILING_SECONDS
    assert len(spawned) == 1
    assert spawned[0][0] == case_id
    assert original_group_exists(spawned[0][1]) is False
    assert result.case_id == case_id
    assert result.subsystem == "supervisor"
    assert result.passed is True
    assert result.expected_disposition == expected.expected_supervisor_disposition
    assert result.observed_disposition == expected.expected_supervisor_disposition
    assert result.expected_machine_code == expected.expected_machine_code
    assert result.observed_machine_code == expected.expected_machine_code
    expected_phase = (
        "returned-before-deadline"
        if expected.expected_supervisor_disposition == "VALID"
        else "timeout-at-deadline"
        if expected.expected_supervisor_disposition == "TIMEOUT_CENSORED"
        else ""
    )
    assert result.observed_closed_phase == expected_phase
    assert result.observed_closed_status == expected.expected_closed_status
    assert result.observed_failure_code is None
    assert result.classifier_rule_ordinal is None
    assert result.production_evidence is False
    expected_timeout = case_id in _SUPERVISOR_CASE_IDS[1:6]
    expected_termination = case_id in _SUPERVISOR_CASE_IDS[3:6]
    assert result.timeout_observed is expected_timeout
    assert result.completion_strictly_before_deadline is (not expected_timeout)
    assert result.termination_attempted is expected_termination
    assert result.termination_signal_delivered is expected_termination
    assert result.kill_attempted is (
        case_id == "hang-ignores-sigterm-killed-by-sigkill"
    )
    assert result.child_reaped is True
    assert result.process_group_cleanup_verified is (
        expected.process_group_empty_required
    )
    assert result.process_group_empty is True
    assert result.exact_one_frame_observed is (expected.frame_mode == "one")
    assert result.normalized_semantic_sha256 == _case_semantic_digest(result)
    assert result.record_sha256 == _record_digest(result)
    assert result.stdout_byte_count == len(observed_streams["stdout"])
    assert (
        result.stdout_sha256 == hashlib.sha256(observed_streams["stdout"]).hexdigest()
    )
    assert result.stderr_byte_count == len(observed_streams["stderr"])
    assert (
        result.stderr_sha256 == hashlib.sha256(observed_streams["stderr"]).hexdigest()
    )
    if case_id == "stderr-over-cap":
        assert len(observed_streams["stderr"]) == 1_048_577
    else:
        assert observed_streams["stderr"] == b""
    stdout = observed_streams["stdout"]
    if expected.frame_mode == "one":
        document, end = _decode_raw_frame(stdout)
        assert end == len(stdout)
        assert document["case_id"] == case_id
        assert document["schema"] == cp66.CP66_TEST28_SCHEMA_VERSION
        assert (
            document["source_sha256"]
            == hashlib.sha256(_SOURCE_PATH.read_bytes()).hexdigest()
        )
        assert document["inherited_fd_count_after_exec"] == (
            1 if expected.fd_mode == "drift" else 0
        )
        assert document["environment_match"] is (expected.environment_mode != "drift")
        assert document["closed_status"] == expected.expected_closed_status
    elif expected.frame_mode == "two":
        first, first_end = _decode_raw_frame(stdout)
        second, second_end = _decode_raw_frame(stdout, first_end)
        assert second_end == len(stdout)
        assert first == second
    elif expected.frame_mode == "truncated-prefix":
        assert 0 < len(stdout) < 8
    elif expected.frame_mode == "truncated-body":
        assert len(stdout) >= 8
        announced = int.from_bytes(stdout[:8], "big")
        assert announced <= 16_777_216
        assert len(stdout) - 8 < announced
    elif expected.frame_mode == "oversize":
        assert len(stdout) == 8
        assert int.from_bytes(stdout, "big") > 16_777_216
    else:
        assert expected.frame_mode in ("none", "zero")
        assert stdout == b""
    if result.exact_one_frame_observed:
        assert result.inherited_fd_count_after_exec == (
            1 if expected.fd_mode == "drift" else 0
        )
        assert result.environment_match is (expected.environment_mode != "drift")
    else:
        assert result.inherited_fd_count_after_exec is None
        assert result.environment_match is None
    special_observations = {
        "no-extra-fd-control": (0, True),
        "inherited-fd-drift": (1, True),
        "environment-drift": (0, False),
    }
    if case_id in special_observations:
        assert (
            result.inherited_fd_count_after_exec,
            result.environment_match,
        ) == special_observations[case_id]


def test_cp66_repeated_process_runs_have_stable_semantic_not_volatile_digest() -> None:
    first = cp66.cp66_run_qualification_case("timely-one-frame-clean-exit")
    second = cp66.cp66_run_qualification_case("timely-one-frame-clean-exit")
    assert first.normalized_semantic_sha256 == second.normalized_semantic_sha256
    assert first.record_sha256 == second.record_sha256
    primitive = _plain(first)
    assert type(primitive) is dict
    assert not any(
        "pid" in key or "timestamp" in key or "monotonic" in key or "wall_clock" in key
        for key in primitive
    )


def test_cp66_control_closes_inheritable_parent_fd_above_scan_range(
    monkeypatch,
) -> None:
    injected_fd = 300
    try:
        original_inheritable = os.get_inheritable(injected_fd)
        backup_fd = os.dup(injected_fd)
    except OSError:
        original_inheritable = False
        backup_fd = None
    source_fd = os.open(os.devnull, os.O_RDONLY)
    decoded_documents: list[dict] = []
    spawned_file_actions: list[tuple[tuple[object, ...], ...]] = []
    original_decode = cp66._decode_child_frame
    original_posix_spawn = os.posix_spawn

    def decode_spy(stdout, case_id, source_sha256):
        document = original_decode(stdout, case_id, source_sha256)
        decoded_documents.append(dict(document))
        return document

    def posix_spawn_spy(path, argv, environment, **kwargs):
        spawned_file_actions.append(tuple(kwargs.get("file_actions", ())))
        return original_posix_spawn(path, argv, environment, **kwargs)

    try:
        os.dup2(source_fd, injected_fd, inheritable=True)
        assert os.get_inheritable(injected_fd) is True
        monkeypatch.setattr(cp66, "_decode_child_frame", decode_spy)
        monkeypatch.setattr(cp66.os, "posix_spawn", posix_spawn_spy)
        result = cp66.cp66_run_qualification_case("no-extra-fd-control")
        assert result.passed is True
        assert result.observed_disposition == "VALID"
        assert result.inherited_fd_count_after_exec == 0
        assert len(decoded_documents) == 1
        assert decoded_documents[0]["inherited_fd_count_after_exec"] == 0
        assert len(spawned_file_actions) == 1
        assert (os.POSIX_SPAWN_CLOSE, injected_fd) in spawned_file_actions[0]
    finally:
        os.close(source_fd)
        if backup_fd is None:
            try:
                os.close(injected_fd)
            except OSError:
                pass
        else:
            os.dup2(backup_fd, injected_fd, inheritable=original_inheritable)
            os.close(backup_fd)


def test_cp66_deadline_equality_uses_exact_deterministic_comparator(
    monkeypatch,
) -> None:
    assert cp66._classify_completion_relation(99, 100) == "before"
    assert cp66._classify_completion_relation(100, 100) == "equal"
    assert cp66._classify_completion_relation(101, 100) == "after"
    for invalid in ((True, 1), (1, False), (1.0, 1), (1, "1"), (-1, 1)):
        with pytest.raises((TypeError, ValueError)):
            cp66._classify_completion_relation(*invalid)

    original = cp66._classify_completion_relation
    observed: list[tuple[int, int]] = []

    def comparator_spy(completion_ns, deadline_ns):
        observed.append((completion_ns, deadline_ns))
        return original(completion_ns, deadline_ns)

    monkeypatch.setattr(cp66, "_classify_completion_relation", comparator_spy)
    equality = cp66.cp66_run_qualification_case("deadline-equality-clean-exit")
    assert equality.passed is True
    assert equality.observed_machine_code == "TIMEOUT_AT_DEADLINE"
    assert any(completion == deadline for completion, deadline in observed)

    monkeypatch.setattr(
        cp66,
        "_classify_completion_relation",
        lambda completion_ns, deadline_ns: "before",
    )
    rejected = cp66.cp66_run_qualification_case("deadline-equality-clean-exit")
    assert rejected.passed is False
    assert rejected.observed_machine_code == "TIMEOUT_MECHANICS_INVALID"


@pytest.mark.parametrize(
    "fault_type", (OSError, MemoryError, _SyntheticInfrastructureFault)
)
def test_cp66_supervisor_faults_are_normalized_and_child_is_reaped(
    monkeypatch, fault_type
) -> None:
    original_spawn = cp66._spawn_qualification_child
    original_group_exists = cp66._process_group_exists
    spawned_pids: list[int] = []

    def spawn_spy(case):
        result = original_spawn(case)
        spawned_pids.append(result[0])
        return result

    def fail_read(*args, **kwargs):
        del args, kwargs
        raise fault_type("synthetic infrastructure fault")

    monkeypatch.setattr(cp66, "_spawn_qualification_child", spawn_spy)
    monkeypatch.setattr(cp66, "_read_ready_streams", fail_read)
    with pytest.raises(cp66.CP66QualificationError) as caught:
        cp66.cp66_run_qualification_case("timely-one-frame-clean-exit")
    assert caught.value.code == "QUALIFICATION_INFRASTRUCTURE_FAILURE"
    assert isinstance(caught.value.__cause__, fault_type)
    assert len(spawned_pids) == 1
    assert original_group_exists(spawned_pids[0]) is False


def test_cp66_residual_process_group_forces_cleanup_and_invalidates_case(
    monkeypatch,
) -> None:
    original_spawn = cp66._spawn_qualification_child
    spawned_pids: list[int] = []
    signals: list[int] = []
    simulated_group_exists = [True]
    absence_checks = [0]

    def spawn_spy(case):
        result = original_spawn(case)
        spawned_pids.append(result[0])
        return result

    def wait_for_group_absence_spy(pid, ceiling_seconds):
        assert pid == spawned_pids[0]
        assert 0.0 < ceiling_seconds <= 1.0
        absence_checks[0] += 1
        return absence_checks[0] > 1

    def process_group_exists_spy(pid):
        assert pid == spawned_pids[0]
        return simulated_group_exists[0]

    def signal_spy(pid, signal_number):
        assert pid == spawned_pids[0]
        signals.append(int(signal_number))
        simulated_group_exists[0] = False
        return True

    monkeypatch.setattr(cp66, "_spawn_qualification_child", spawn_spy)
    monkeypatch.setattr(cp66, "_wait_for_group_absence", wait_for_group_absence_spy)
    monkeypatch.setattr(cp66, "_process_group_exists", process_group_exists_spy)
    monkeypatch.setattr(cp66, "_send_process_group_signal", signal_spy)
    result = cp66.cp66_run_qualification_case("timely-one-frame-clean-exit")
    assert len(spawned_pids) == 1
    assert absence_checks[0] == 2
    assert signals == [int(signal.SIGTERM)]
    assert result.passed is False
    assert result.expected_disposition == "VALID"
    assert result.observed_disposition == "INFRASTRUCTURE_INVALID"
    assert result.observed_machine_code == "RESIDUAL_PROCESS_GROUP"
    assert result.termination_attempted is True
    assert result.termination_signal_delivered is True
    assert result.kill_attempted is False
    assert result.child_reaped is True
    assert result.process_group_empty is True


def test_cp66_supervisor_owns_and_closes_each_pipe_read_fd_exactly_once(
    monkeypatch,
) -> None:
    original_spawn = cp66._spawn_qualification_child
    original_close = cp66._safe_close
    read_fds: list[int] = []
    close_calls: list[int] = []

    def spawn_spy(case):
        result = original_spawn(case)
        read_fds.extend(result[1:])
        return result

    def close_spy(file_descriptor):
        if file_descriptor in read_fds:
            close_calls.append(file_descriptor)
        return original_close(file_descriptor)

    monkeypatch.setattr(cp66, "_spawn_qualification_child", spawn_spy)
    monkeypatch.setattr(cp66, "_safe_close", close_spy)
    result = cp66.cp66_run_qualification_case("timely-one-frame-clean-exit")
    assert result.passed is True
    assert len(read_fds) == len(set(read_fds)) == 2
    assert close_calls == read_fds
    for file_descriptor in read_fds:
        with pytest.raises(OSError):
            os.fstat(file_descriptor)


def test_cp66_full_suite_counts_and_cleanup_are_exact() -> None:
    started = time.monotonic()
    result = cp66.cp66_run_qualification_suite()
    elapsed = time.monotonic() - started
    assert elapsed < cp66.CP66_QUALIFICATION_SUITE_WALL_CEILING_SECONDS
    assert result.qualification_fixture_set_sha256 == (
        cp66.cp66_qualification_fixture_set_sha256()
    )
    assert result.case_count == result.passed_case_count == 40
    assert result.supervisor_case_count == 16
    assert result.classifier_reachability_case_count == 16
    assert result.classifier_rejection_case_count == 8
    assert result.timeout_case_count == 5
    assert result.process_group_cleanup_case_count == 3
    assert result.fd_leak_case_count == 2
    assert result.environment_drift_case_count == 2
    assert result.all_cases_passed is True
    assert result.development_supervisor_mechanics_qualified is True
    assert result.development_classifier_mechanics_qualified is True
    assert result.qualification_python_profile_matched is (
        sys.implementation.name == "cpython" and sys.version_info[:3] == (3, 11, 5)
    )
    assert result.scaled_timing_not_production_clock_fidelity is True
    assert result.production_clock_fidelity_qualified is False
    assert result.volatile_pids_or_timestamps_in_semantic_digest is False
    assert result.production_qualification_receipt_present is False
    assert result.production_supervisor_qualified is False
    assert result.production_classifier_qualified is False
    assert result.production_execution_authorized is False
    assert result.runner_and_recomputation_blocker_closed is False
    assert result.formal_test_28_closed is False
    assert result.ordered_case_ids == (
        _SUPERVISOR_CASE_IDS
        + _CLASSIFIER_ACCEPTED_CASE_IDS
        + _CLASSIFIER_REJECTED_CASE_IDS
    )
    independently_rerun_hashes = tuple(
        cp66.cp66_run_qualification_case(case_id).record_sha256
        for case_id in result.ordered_case_ids
    )
    assert result.ordered_case_result_sha256s == independently_rerun_hashes
    assert len(result.ordered_case_result_sha256s) == 40
    assert len(set(result.ordered_case_result_sha256s)) == 40
    assert result.record_sha256 == _record_digest(result)


def test_cp66_suite_wall_ceiling_is_enforced_during_case_sequence(
    monkeypatch,
) -> None:
    result_template = cp66.cp66_run_qualification_case("returned-rejection-selected")
    clock_ns = [100_000_000_000]
    called_case_ids: list[str] = []

    def monotonic() -> float:
        return clock_ns[0] / 1_000_000_000

    def monotonic_ns() -> int:
        return clock_ns[0]

    def delayed_case(case_id):
        called_case_ids.append(case_id)
        clock_ns[0] += 31_000_000_000
        return result_template

    monkeypatch.setattr(cp66.time, "monotonic", monotonic)
    monkeypatch.setattr(cp66.time, "monotonic_ns", monotonic_ns)
    monkeypatch.setattr(cp66, "cp66_run_qualification_case", delayed_case)
    with pytest.raises(cp66.CP66QualificationError) as caught:
        cp66.cp66_run_qualification_suite()
    assert caught.value.code == "QUALIFICATION_SUITE_WALL_CEILING_EXPIRED"
    assert called_case_ids == [_SUPERVISOR_CASE_IDS[0]]


def test_cp66_term_kill_order_and_process_groups_are_gone_after_suite(
    monkeypatch,
) -> None:
    original_spawn = cp66._spawn_qualification_child
    original_signal = cp66._send_process_group_signal
    original_wait = cp66._wait_child_nonblocking
    original_group_exists = cp66._process_group_exists
    current_case = [""]
    pids: dict[str, int] = {}
    signal_events: dict[str, list[int]] = {}
    wait_events: dict[str, int] = {}

    def spawn_spy(case):
        result = original_spawn(case)
        current_case[0] = case.case_id
        pids[case.case_id] = result[0]
        return result

    def signal_spy(pid, signal_number):
        signal_events.setdefault(current_case[0], []).append(int(signal_number))
        return original_signal(pid, signal_number)

    def wait_spy(pid):
        wait_events[current_case[0]] = wait_events.get(current_case[0], 0) + 1
        return original_wait(pid)

    monkeypatch.setattr(cp66, "_spawn_qualification_child", spawn_spy)
    monkeypatch.setattr(cp66, "_send_process_group_signal", signal_spy)
    monkeypatch.setattr(cp66, "_wait_child_nonblocking", wait_spy)
    term = cp66.cp66_run_qualification_case("hang-terminated-by-sigterm")
    kill = cp66.cp66_run_qualification_case("hang-ignores-sigterm-killed-by-sigkill")
    descendant = cp66.cp66_run_qualification_case("descendant-process-group-cleanup")
    assert term.observed_closed_status == "timeout-censored-at-deadline"
    assert kill.observed_closed_status == "timeout-censored-at-deadline"
    assert descendant.observed_closed_status == "timeout-censored-at-deadline"
    assert term.process_group_empty is True
    assert kill.process_group_empty is True
    assert descendant.process_group_empty is True
    assert signal_events[term.case_id] == [int(signal.SIGTERM)]
    assert signal_events[kill.case_id] == [int(signal.SIGTERM), int(signal.SIGKILL)]
    assert signal_events[descendant.case_id] == [int(signal.SIGTERM)]
    assert term.termination_attempted is True
    assert term.termination_signal_delivered is True
    assert term.kill_attempted is False
    assert kill.termination_attempted is True
    assert kill.termination_signal_delivered is True
    assert kill.kill_attempted is True
    assert descendant.termination_attempted is True
    assert descendant.termination_signal_delivered is True
    assert descendant.kill_attempted is False
    for result in (term, kill, descendant):
        assert wait_events[result.case_id] >= 1
        assert result.child_reaped is True
        assert original_group_exists(pids[result.case_id]) is False


def test_cp66_no_claims_and_ledger_transition_are_fail_closed() -> None:
    bundle = _bundle()
    expected_false = (
        "generic_command_api_exposed",
        "production_seed_or_request_api_exposed",
        "production_campaign_api_exposed",
        "source_manifest_observed",
        "production_runtime_receipt_observed",
        "freeze_receipt_present",
        "production_runner_implemented",
        "production_runner_supervisor_qualified",
        "production_closed_classifier_qualified",
        "production_qualification_receipts_present",
        "production_execution_observed",
        "runner_and_recomputation_blocker_closed",
        "unconditional_operational_predictions_blocker_closed",
        "power_and_thresholds_blocker_closed",
        "confirmatory_custody_blocker_closed",
        "confirmatory_evidence",
        "manuscript_claim",
        "formal_test_28_closed",
    )
    assert all(getattr(bundle, name) is False for name in expected_false)
    assert bundle.formal_test_28_status == "OPEN"
    assert bundle.ledger_prerequisite_id == (
        "whole_seed_runner_supervisor_and_closed_classifier_qualification_harness"
    )
    assert bundle.ledger_prerequisite_state == (
        "SATISFIED_BY_HASH_BOUND_NONCONFIRMATORY_DEVELOPMENT_QUALIFICATION_ARTIFACTS"
    )
    assert (
        bundle.ledger_total_count,
        bundle.ledger_satisfied_count,
        bundle.ledger_missing_count,
    ) == (21, 17, 4)
    assert bundle.zero_argument_builder is True
    assert bundle.builder_executes_child is False


def test_cp66_mutating_any_case_breaks_record_and_fixture_custody() -> None:
    bundle = _bundle()
    case = bundle.supervisor_cases[0]
    mutated = object.__new__(type(case))
    for field in fields(type(case)):
        object.__setattr__(mutated, field.name, getattr(case, field.name))
    object.__setattr__(mutated, "case_id", case.case_id + "-forged")
    assert mutated.record_sha256 != _record_digest(mutated)
    original_digests = [item.record_sha256 for item in bundle.supervisor_cases]
    original_digests.extend(item.record_sha256 for item in bundle.classifier_cases)
    forged_digests = list(original_digests)
    forged_digests[0] = _record_digest(mutated)
    original = hashlib.sha256(
        b"cp66-test28-qualification-fixture-set-v1\0" + _canonical(original_digests)
    ).hexdigest()
    forged = hashlib.sha256(
        b"cp66-test28-qualification-fixture-set-v1\0" + _canonical(forged_digests)
    ).hexdigest()
    assert original == bundle.qualification_fixture_set_sha256
    assert forged != original
    with pytest.raises(TypeError):
        cp66.cp66_canonical_json_bytes(mutated)


def test_cp66_cached_case_tamper_cannot_drive_public_supervisor() -> None:
    script = r"""
import heterodiff.evaluation.mixed_initializer_test28_runner_supervisor_classifier_qualification as cp66

bundle = cp66.cp66_runner_supervisor_classifier_qualification_bundle()
case = bundle.supervisor_cases[13]
assert case.case_id == "no-extra-fd-control"
object.__setattr__(case, "environment_mode", "drift")
object.__setattr__(case, "expected_supervisor_disposition", "INFRASTRUCTURE_INVALID")
object.__setattr__(case, "expected_machine_code", "CHILD_ENVIRONMENT_DRIFT")
try:
    cp66.cp66_run_qualification_case(case.case_id)
except ValueError as error:
    assert "mutated" in str(error)
else:
    raise AssertionError("a mutated cached case reached the process supervisor")
"""
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = "src:."
    completed = subprocess.run(
        [sys.executable, "-W", "error", "-c", script],
        cwd=_PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10.0,
        check=False,
    )
    assert completed.returncode == 0, (completed.stdout, completed.stderr)
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_cp66_runtime_surface_remains_python39_compatible() -> None:
    source = _SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, feature_version=(3, 9))
    assert isinstance(tree, ast.Module)
    assert "dataclass(slots=True" not in source.replace(" ", "")
    match_node = getattr(ast, "Match", ())
    assert all(not isinstance(node, match_node) for node in ast.walk(tree))
    assert "except*" not in source
