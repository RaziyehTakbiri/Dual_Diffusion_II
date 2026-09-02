"""Development-only CP66 runner/supervisor/classifier qualification.

The module supplies a closed, deterministic qualification matrix for the
process-supervisor mechanics and the CP62 closed outcome classifier.  Its
child entry point accepts only module-owned case identifiers.  It deliberately
does not expose a command, path, request, seed, campaign, production launch,
or evidence-acceptance interface.

The zero-argument definition builder is pure.  Process, filesystem, clock,
and host observations occur only when a caller explicitly runs a frozen
supervisor qualification case or suite.  Only the Python standard library is
imported.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import errno
import fcntl
import hashlib
import hmac
import json
import os
import selectors
import signal
import sys
import threading
import time
from typing import Dict, Mapping, Optional, Tuple, cast
import weakref


CP66_TEST28_SCHEMA_VERSION = "cp66-test28-runner-supervisor-classifier-qualification-v1"
CP66_TEST28_SCOPE = (
    "development-only-runner-supervisor-and-closed-classifier-qualification;"
    "closed-forty-case-fixture-set;internal-case-ids-only;no-generic-command;"
    "no-path-api;no-request-api;no-seed-api;no-campaign;no-production-launch;"
    "no-production-execution;no-evidence-acceptance;no-blocker-closure"
)
CP66_TEST28_FORMAL_TEST_28_STATUS = "OPEN"
CP66_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID = (
    "whole_seed_runner_supervisor_and_closed_classifier_qualification_harness"
)

CP66_TEST28_QUALIFICATION_DEADLINE_MILLISECONDS = 750
CP66_TEST28_QUALIFICATION_TERMINATION_GRACE_MILLISECONDS = 100
CP66_TEST28_QUALIFICATION_REAP_CEILING_MILLISECONDS = 500
CP66_TEST28_QUALIFICATION_PIPE_EOF_GRACE_MILLISECONDS = 100
CP66_TEST28_PRODUCTION_DEADLINE_SECONDS = 300
CP66_TEST28_PRODUCTION_TERMINATION_GRACE_SECONDS = 2
CP66_TEST28_PRODUCTION_REAP_CEILING_SECONDS = 5
CP66_TEST28_RAW_FRAME_MAX_BYTES = 16_777_216
CP66_TEST28_STDERR_MAX_BYTES = 1_048_576
CP66_CLASSIFIER_PAYLOAD_MAX_BYTES = 16_384
CP66_QUALIFICATION_CASE_WALL_CEILING_SECONDS = 5
CP66_QUALIFICATION_SUITE_WALL_CEILING_SECONDS = 30

_CP62_SOURCE_SHA256 = "44ef12b1a556d80944774ac9b698acf1359879fe44729120a04feb5e7a4a8a49"
_CP62_BUNDLE_RECORD_SHA256 = (
    "0f92f54ce8d451485019f6d697736fd5eb48d2b942e1d3a3f1bd373b50c3ec92"
)
_CP62_BUNDLE_SEMANTIC_SHA256 = (
    "f3bd0b80c52a9d79a3b6a8e06aa2923c6303e891bf526c1869c5552e1413f3ff"
)
_CP62_SUPERVISOR_CONTRACT_SHA256 = (
    "6dfb5b8bbb7cecabed1c84349bc32ac130dd2fb698ba400e0ce74d3ef58434fb"
)
_CP62_RAW_SCHEMA_RECORD_SHA256 = (
    "ae77cdcf7142bac100236fc8db13411ac68e18c9e225869869223693d42b21f4"
)
_CP63_SOURCE_SHA256 = "27259edf2557a21b2527595eed7a954fc697755935e4a3deaeeb169765ba1c9c"
_CP63_RUNNER_BUNDLE_RECORD_SHA256 = (
    "442c4b0f134a96efe32b5246b4eb5b05233d61a13c62c0a7d1f21c9bbbd32f85"
)
_CP63_RAW_SCHEMA_RECORD_SHA256 = (
    "29f17aa7528971e7892b6ea4ccb37b5943190a0e592191341ae444e8ed63b3cb"
)
_CP64_SOURCE_SHA256 = "d35cbacb84e3348ae10549e053a0bb1572569583cdd03e66119353af4148bec2"
_CP64_BUNDLE_RECORD_SHA256 = (
    "32f7f0c62019d8ee906e6f74300f6c33fbe55984f69cfe4fe1061ffb92463f39"
)
_CP64_NO_EXECUTION_GATE_RECORD_SHA256 = (
    "7ceb4f12ce712e7123509eb6380e134876855bb91e90c64a951f7e1bcbcb2633"
)
_CP65_SOURCE_SHA256 = "774cd44ad6aa82ea629ef705bde3bbb7288ccd74bd0d3a5d5c79f552a5f6a06a"
_CP65_BUNDLE_RECORD_SHA256 = (
    "597f2b4b557bffb529d951858fd84e454135220db0c19dcd05fcf7ce93710f89"
)
_CP65_SCHEMA_SEMANTIC_SHA256 = (
    "8855d84a573344723bc6c4c32036b7aeb878d6c66a04d5423d5f591ed40316c0"
)
_V16_MACHINE_MANIFEST_SHA256 = (
    "1ec8fb9427b2f28fcad3a749c708d5520f48e21985185cf5afc92ea6e9dc618f"
)
_V16_PREREGISTRATION_SHA256 = (
    "091c3e5240673165fd05c2042edc54bc0174353247b4fde47cf485bff969f3d8"
)

_ZERO_SHA256 = "0" * 64
_ALLOW_RECORD_CLASS_DEFINITION = True
_FIXTURE_SET_DOMAIN = b"cp66-test28-qualification-fixture-set-v1\0"
_CHILD_NONCE_DOMAIN = b"cp66-test28-qualification-child-nonce-v1\0"
_CHILD_AUTH_DOMAIN = b"cp66-test28-qualification-child-auth-v1\0"
_RAW_OBSERVATION_DOMAIN = b"cp66-test28-qualification-observation-v1\0"
_SUITE_RECEIPT_DOMAIN = b"cp66-test28-qualification-suite-receipt-v1\0"

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
_CLOSED_PHASES = (
    "returned-before-deadline",
    "preexecution-refusal-before-deadline",
    "execution-failure-before-deadline",
    "timeout-at-deadline",
)
_RETURNED_STATUSES = (
    "returned-rejection-selected-before-deadline",
    "returned-rejection-exhausted-before-deadline",
    "returned-sir-selected-before-deadline",
)
_PREEXECUTION_STATUS = "preexecution-refusal-before-deadline"
_EXECUTION_FAILURE_STATUS = "execution-failure-before-deadline"
_TIMEOUT_STATUS = "timeout-censored-at-deadline"
_CLASSIFIER_OBSERVATION_KEYS = (
    "schema",
    "case_id",
    "strategy",
    "event_kind",
    "phase",
    "closed_status",
    "failure_code",
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


class CP66QualificationError(RuntimeError):
    """Fail-closed CP66 error carrying a stable machine code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("CP66 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("CP66 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP66 records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False)
class CP66PredecessorCustodyV1(_SealedRecord):
    schema_version: str
    v16_protocol_sha256: str
    v16_protocol_bytes: int
    v16_protocol_lf_count: int
    v16_manifest_sha256: str
    v16_manifest_bytes: int
    v16_manifest_lf_count: int
    cp62_source_sha256: str
    cp62_bundle_record_sha256: str
    cp62_bundle_semantic_sha256: str
    cp62_supervisor_contract_record_sha256: str
    cp62_raw_record_schema_record_sha256: str
    cp63_source_sha256: str
    cp63_runner_bundle_record_sha256: str
    cp63_raw_record_schema_record_sha256: str
    cp64_source_sha256: str
    cp64_bundle_record_sha256: str
    cp64_no_execution_gate_contract_record_sha256: str
    cp65_source_sha256: str
    cp65_bundle_record_sha256: str
    cp65_schema_semantic_sha256: str
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP66ClosedClassifierContractV1(_SealedRecord):
    schema_version: str
    returned_rejection_statuses: Tuple[str, ...]
    returned_sir_statuses: Tuple[str, ...]
    timeout_phase: str
    timeout_status: str
    preexecution_refusal_phase: str
    preexecution_refusal_codes: Tuple[str, ...]
    execution_failure_phase: str
    execution_failure_codes: Tuple[str, ...]
    infrastructure_invalid_disposition: str
    timeout_is_semantic_nonreturn: bool
    no_retry: bool
    no_drop: bool
    no_replacement: bool
    no_topup: bool
    unknown_phase_or_code_rejected: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP66ClassifierRuleV1(_SealedRecord):
    schema_version: str
    rule_ordinal: int
    stage_id: str
    execution_boundary_state: str
    accepted_internal_event_kind: str
    closed_phase: str
    closed_status: str
    failure_code: str
    arbitrary_base_exception_is_infrastructure: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP66SupervisorQualificationCaseV1(_SealedRecord):
    schema_version: str
    case_ordinal: int
    case_id: str
    child_mode: str
    deadline_relation: str
    frame_mode: str
    exit_mode: str
    descendant_mode: str
    fd_mode: str
    environment_mode: str
    expected_supervisor_disposition: str
    expected_machine_code: str
    expected_closed_status: str
    expected_term_signal: int
    exact_one_frame_expected: bool
    process_group_empty_required: bool
    no_fd_leak_required: bool
    environment_match_required: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP66ClassifierQualificationCaseV1(_SealedRecord):
    schema_version: str
    case_ordinal: int
    case_id: str
    strategy: Optional[str]
    event_kind: str
    phase: str
    closed_status: str
    failure_code: Optional[str]
    expected_accept: bool
    expected_machine_code: str
    expected_closed_status: str
    expected_failure_code: Optional[str]
    expected_classifier_disposition: str
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP66QualificationCaseResultV1(_SealedRecord):
    schema_version: str
    case_ordinal: int
    case_id: str
    subsystem: str
    expected_disposition: str
    observed_disposition: str
    expected_machine_code: str
    observed_machine_code: str
    observed_closed_phase: str
    observed_closed_status: str
    observed_failure_code: Optional[str]
    classifier_rule_ordinal: Optional[int]
    timeout_observed: bool
    process_group_cleanup_verified: bool
    inherited_fd_count_after_exec: Optional[int]
    environment_match: Optional[bool]
    exact_one_frame_observed: bool
    completion_strictly_before_deadline: bool
    termination_attempted: bool
    termination_signal_delivered: bool
    kill_attempted: bool
    child_reaped: bool
    process_group_empty: bool
    stdout_byte_count: int
    stdout_sha256: str
    stderr_byte_count: int
    stderr_sha256: str
    passed: bool
    normalized_semantic_sha256: str
    production_evidence: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP66QualificationRunV1(_SealedRecord):
    schema_version: str
    qualification_fixture_set_sha256: str
    ordered_case_ids: Tuple[str, ...]
    ordered_case_result_sha256s: Tuple[str, ...]
    case_count: int
    passed_case_count: int
    supervisor_case_count: int
    classifier_reachability_case_count: int
    classifier_rejection_case_count: int
    timeout_case_count: int
    process_group_cleanup_case_count: int
    fd_leak_case_count: int
    environment_drift_case_count: int
    all_cases_passed: bool
    development_supervisor_mechanics_qualified: bool
    development_classifier_mechanics_qualified: bool
    qualification_python_profile_matched: bool
    scaled_timing_not_production_clock_fidelity: bool
    production_clock_fidelity_qualified: bool
    volatile_pids_or_timestamps_in_semantic_digest: bool
    production_qualification_receipt_present: bool
    production_supervisor_qualified: bool
    production_classifier_qualified: bool
    production_execution_authorized: bool
    runner_and_recomputation_blocker_closed: bool
    formal_test_28_closed: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP66RunnerSupervisorClassifierQualificationBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    predecessor_custody: CP66PredecessorCustodyV1
    closed_classifier_contract: CP66ClosedClassifierContractV1
    classifier_rules: Tuple[CP66ClassifierRuleV1, ...]
    classifier_rule_count: int
    supervisor_cases: Tuple[CP66SupervisorQualificationCaseV1, ...]
    classifier_cases: Tuple[CP66ClassifierQualificationCaseV1, ...]
    qualification_fixture_set_sha256: str
    supervisor_case_count: int
    classifier_reachability_case_count: int
    classifier_rejection_case_count: int
    total_case_count: int
    zero_argument_builder: bool
    builder_executes_child: bool
    generic_command_api_exposed: bool
    production_seed_or_request_api_exposed: bool
    production_campaign_api_exposed: bool
    source_manifest_observed: bool
    production_runtime_receipt_observed: bool
    freeze_receipt_present: bool
    production_runner_implemented: bool
    production_runner_supervisor_qualified: bool
    production_closed_classifier_qualified: bool
    production_qualification_receipts_present: bool
    production_execution_observed: bool
    runner_and_recomputation_blocker_closed: bool
    unconditional_operational_predictions_blocker_closed: bool
    power_and_thresholds_blocker_closed: bool
    confirmatory_custody_blocker_closed: bool
    confirmatory_evidence: bool
    manuscript_claim: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    ledger_prerequisite_id: str
    ledger_prerequisite_state: str
    ledger_total_count: int
    ledger_satisfied_count: int
    ledger_missing_count: int
    record_sha256: str

    __slots__ = tuple(__annotations__)


_ALLOW_RECORD_CLASS_DEFINITION = False

_RECORD_DOMAINS = {
    CP66PredecessorCustodyV1: b"cp66-test28-predecessor-custody-v1",
    CP66ClosedClassifierContractV1: b"cp66-test28-closed-classifier-contract-v1",
    CP66ClassifierRuleV1: b"cp66-test28-classifier-rule-v1",
    CP66SupervisorQualificationCaseV1: b"cp66-test28-supervisor-qualification-case-v1",
    CP66ClassifierQualificationCaseV1: b"cp66-test28-classifier-qualification-case-v1",
    CP66QualificationCaseResultV1: b"cp66-test28-qualification-case-result-v1",
    CP66QualificationRunV1: b"cp66-test28-qualification-run-v1",
    CP66RunnerSupervisorClassifierQualificationBundleV1: (
        b"cp66-test28-runner-supervisor-classifier-qualification-bundle-v1"
    ),
}
_ISSUED_RECORD_LOCK = threading.RLock()
_ISSUED_RECORD_SNAPSHOTS: weakref.WeakKeyDictionary[
    _SealedRecord, bytes
] = weakref.WeakKeyDictionary()


def _plain_json_value(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) in (tuple, list):
        return [_plain_json_value(item) for item in value]
    if type(value) is dict:
        result: Dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("CP66 JSON object keys must be exact strings")
            result[key] = _plain_json_value(item)
        return result
    if isinstance(value, _SealedRecord):
        return {
            item.name: _plain_json_value(getattr(value, item.name))
            for item in fields(type(value))
        }
    raise TypeError("value has no CP66 canonical JSON representation")


def _plain_json_bytes(value: object) -> bytes:
    return json.dumps(
        _plain_json_value(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _record(cls: type, values: Mapping[str, object]) -> object:
    names = tuple(item.name for item in fields(cls))
    if set(values) != set(names) - {"record_sha256"}:
        raise TypeError("CP66 sealed record field set differs")
    complete = dict(values)
    complete["record_sha256"] = _ZERO_SHA256
    provisional = object.__new__(cls)
    for name in names:
        object.__setattr__(provisional, name, complete[name])
    complete["record_sha256"] = hashlib.sha256(
        _RECORD_DOMAINS[cls] + b"\0" + _plain_json_bytes(provisional)
    ).hexdigest()
    result = object.__new__(cls)
    for name in names:
        object.__setattr__(result, name, complete[name])
    snapshot = _plain_json_bytes(result)
    with _ISSUED_RECORD_LOCK:
        _ISSUED_RECORD_SNAPSHOTS[cast(_SealedRecord, result)] = snapshot
    return result


def _require_issued_record(value: object) -> _SealedRecord:
    if type(value) not in _RECORD_DOMAINS:
        raise TypeError("value must be an exact CP66 sealed record")
    record = cast(_SealedRecord, value)
    with _ISSUED_RECORD_LOCK:
        snapshot = _ISSUED_RECORD_SNAPSHOTS.get(record)
    if snapshot is None:
        raise TypeError("CP66 record was not module-created")
    if not hmac.compare_digest(snapshot, _plain_json_bytes(record)):
        raise ValueError("CP66 record was mutated after issue")
    return record


def cp66_canonical_json_bytes(value: object) -> bytes:
    """Return canonical JSON bytes for an unchanged module-issued record."""

    return _plain_json_bytes(_require_issued_record(value))


def cp66_sha256(value: object) -> str:
    """Return the public, type-separated digest of an issued CP66 record."""

    record = _require_issued_record(value)
    return hashlib.sha256(
        b"cp66-public-record-v1\0"
        + type(record).__name__.encode("ascii")
        + b"\0"
        + cp66_canonical_json_bytes(record)
    ).hexdigest()


def _classifier_rules() -> Tuple[CP66ClassifierRuleV1, ...]:
    inventory = (
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
    result = []
    for ordinal, (stage_id, boundary, event_kind, failure_code) in enumerate(
        inventory, 1
    ):
        refusal = boundary == "PREEXECUTION"
        result.append(
            cast(
                CP66ClassifierRuleV1,
                _record(
                    CP66ClassifierRuleV1,
                    {
                        "schema_version": CP66_TEST28_SCHEMA_VERSION,
                        "rule_ordinal": ordinal,
                        "stage_id": stage_id,
                        "execution_boundary_state": boundary,
                        "accepted_internal_event_kind": event_kind,
                        "closed_phase": (
                            "preexecution-refusal-before-deadline"
                            if refusal
                            else "execution-failure-before-deadline"
                        ),
                        "closed_status": (
                            _PREEXECUTION_STATUS
                            if refusal
                            else _EXECUTION_FAILURE_STATUS
                        ),
                        "failure_code": failure_code,
                        "arbitrary_base_exception_is_infrastructure": True,
                    },
                ),
            )
        )
    return tuple(result)


_SUPERVISOR_CASE_INVENTORY = (
    (
        "timely-one-frame-clean-exit",
        "before",
        "one",
        "clean",
        "none",
        "exact",
        "exact",
        "VALID",
        "VALID_RETURN",
        "returned-rejection-selected-before-deadline",
        0,
    ),
    (
        "deadline-equality-clean-exit",
        "equal",
        "one",
        "clean",
        "none",
        "exact",
        "exact",
        "TIMEOUT_CENSORED",
        "TIMEOUT_AT_DEADLINE",
        _TIMEOUT_STATUS,
        0,
    ),
    (
        "postdeadline-clean-exit",
        "after",
        "one",
        "clean",
        "none",
        "exact",
        "exact",
        "TIMEOUT_CENSORED",
        "TIMEOUT_AFTER_DEADLINE",
        _TIMEOUT_STATUS,
        0,
    ),
    (
        "hang-terminated-by-sigterm",
        "after",
        "none",
        "wait-for-sigterm",
        "none",
        "exact",
        "exact",
        "TIMEOUT_CENSORED",
        "TIMEOUT_SIGTERM",
        _TIMEOUT_STATUS,
        int(signal.SIGTERM),
    ),
    (
        "hang-ignores-sigterm-killed-by-sigkill",
        "after",
        "none",
        "ignore-sigterm",
        "none",
        "exact",
        "exact",
        "TIMEOUT_CENSORED",
        "TIMEOUT_SIGKILL",
        _TIMEOUT_STATUS,
        int(signal.SIGKILL),
    ),
    (
        "descendant-process-group-cleanup",
        "after",
        "none",
        "wait-for-sigterm",
        "holds-pipe",
        "exact",
        "exact",
        "TIMEOUT_CENSORED",
        "TIMEOUT_DESCENDANT_CLEANUP",
        _TIMEOUT_STATUS,
        int(signal.SIGTERM),
    ),
    (
        "zero-frame-clean-exit",
        "before",
        "zero",
        "clean",
        "none",
        "exact",
        "exact",
        "INFRASTRUCTURE_INVALID",
        "CHILD_FRAME_MISSING",
        "",
        0,
    ),
    (
        "two-frame-clean-exit",
        "before",
        "two",
        "clean",
        "none",
        "exact",
        "exact",
        "INFRASTRUCTURE_INVALID",
        "CHILD_MULTIPLE_OR_TRAILING_FRAMES",
        "",
        0,
    ),
    (
        "truncated-length-prefix",
        "before",
        "truncated-prefix",
        "clean",
        "none",
        "exact",
        "exact",
        "INFRASTRUCTURE_INVALID",
        "CHILD_FRAME_PREFIX_TRUNCATED",
        "",
        0,
    ),
    (
        "truncated-frame-body",
        "before",
        "truncated-body",
        "clean",
        "none",
        "exact",
        "exact",
        "INFRASTRUCTURE_INVALID",
        "CHILD_FRAME_BODY_TRUNCATED",
        "",
        0,
    ),
    (
        "oversize-frame",
        "before",
        "oversize",
        "clean",
        "none",
        "exact",
        "exact",
        "INFRASTRUCTURE_INVALID",
        "CHILD_FRAME_LENGTH_OVERSIZED",
        "",
        0,
    ),
    (
        "abnormal-predeadline-exit",
        "before",
        "zero",
        "abnormal",
        "none",
        "exact",
        "exact",
        "INFRASTRUCTURE_INVALID",
        "CHILD_ABNORMAL_EXIT",
        "",
        0,
    ),
    (
        "stderr-over-cap",
        "before",
        "one",
        "clean",
        "none",
        "exact",
        "exact",
        "INFRASTRUCTURE_INVALID",
        "CHILD_STDERR_OVERSIZED",
        "",
        0,
    ),
    (
        "no-extra-fd-control",
        "before",
        "one",
        "clean",
        "none",
        "exact",
        "exact",
        "VALID",
        "VALID_RETURN",
        "returned-sir-selected-before-deadline",
        0,
    ),
    (
        "inherited-fd-drift",
        "before",
        "one",
        "clean",
        "none",
        "drift",
        "exact",
        "INFRASTRUCTURE_INVALID",
        "CHILD_INHERITED_FD_DRIFT",
        "",
        0,
    ),
    (
        "environment-drift",
        "before",
        "one",
        "clean",
        "none",
        "exact",
        "drift",
        "INFRASTRUCTURE_INVALID",
        "CHILD_ENVIRONMENT_DRIFT",
        "",
        0,
    ),
)


def _supervisor_cases() -> Tuple[CP66SupervisorQualificationCaseV1, ...]:
    result = []
    for ordinal, row in enumerate(_SUPERVISOR_CASE_INVENTORY, 1):
        (
            case_id,
            deadline_relation,
            frame_mode,
            exit_mode,
            descendant_mode,
            fd_mode,
            environment_mode,
            disposition,
            machine_code,
            closed_status,
            term_signal,
        ) = row
        result.append(
            cast(
                CP66SupervisorQualificationCaseV1,
                _record(
                    CP66SupervisorQualificationCaseV1,
                    {
                        "schema_version": CP66_TEST28_SCHEMA_VERSION,
                        "case_ordinal": ordinal,
                        "case_id": case_id,
                        "child_mode": "same-source-closed-case-posix-spawn-exec",
                        "deadline_relation": deadline_relation,
                        "frame_mode": frame_mode,
                        "exit_mode": exit_mode,
                        "descendant_mode": descendant_mode,
                        "fd_mode": fd_mode,
                        "environment_mode": environment_mode,
                        "expected_supervisor_disposition": disposition,
                        "expected_machine_code": machine_code,
                        "expected_closed_status": closed_status,
                        "expected_term_signal": term_signal,
                        "exact_one_frame_expected": frame_mode == "one",
                        "process_group_empty_required": 4 <= ordinal <= 6,
                        "no_fd_leak_required": ordinal == 14,
                        "environment_match_required": ordinal == 14,
                    },
                ),
            )
        )
    return tuple(result)


def _classifier_case_rows() -> Tuple[Tuple[object, ...], ...]:
    accepted = [
        (
            "returned-rejection-selected",
            "returned-rejection-selected",
            "returned-rejection-selected",
            "bounded-rejection",
            "returned-before-deadline",
            "returned-rejection-selected-before-deadline",
            None,
        ),
        (
            "returned-rejection-exhausted",
            "returned-rejection-exhausted",
            "returned-rejection-exhausted",
            "bounded-rejection",
            "returned-before-deadline",
            "returned-rejection-exhausted-before-deadline",
            None,
        ),
        (
            "returned-sir-selected",
            "returned-sir-selected",
            "returned-sir-selected",
            "fixed-budget-sir",
            "returned-before-deadline",
            "returned-sir-selected-before-deadline",
            None,
        ),
    ]
    for rule in _classifier_rules():
        prefix = (
            "preexecution-refusal-"
            if rule.execution_boundary_state == "PREEXECUTION"
            else "execution-failure-"
        )
        accepted.append(
            (
                prefix + rule.failure_code,
                rule.stage_id,
                rule.accepted_internal_event_kind,
                None,
                rule.closed_phase,
                rule.closed_status,
                rule.failure_code,
            )
        )
    accepted.append(
        (
            "timeout-censored",
            "timeout-censored",
            "timeout-censored",
            None,
            "timeout-at-deadline",
            _TIMEOUT_STATUS,
            None,
        )
    )
    rejected = [
        (
            "unknown-phase",
            "unknown-phase",
            "returned-rejection-selected",
            "bounded-rejection",
            "unknown-phase",
            "returned-rejection-selected-before-deadline",
            None,
            "UNKNOWN_PHASE",
        ),
        (
            "unknown-returned-status",
            "unknown-returned-status",
            "returned-rejection-selected",
            "bounded-rejection",
            "returned-before-deadline",
            "unknown-returned-status",
            None,
            "UNKNOWN_RETURNED_STATUS",
        ),
        (
            "strategy-incompatible-returned-status",
            "strategy-status-mismatch",
            "returned-sir-selected",
            "bounded-rejection",
            "returned-before-deadline",
            "returned-sir-selected-before-deadline",
            None,
            "STRATEGY_INCOMPATIBLE_RETURNED_STATUS",
        ),
        (
            "unknown-refusal-code",
            "unknown-refusal-code",
            "plan-validation-refused",
            None,
            "preexecution-refusal-before-deadline",
            _PREEXECUTION_STATUS,
            "unknown_refusal_code",
            "UNKNOWN_REFUSAL_CODE",
        ),
        (
            "unknown-failure-code",
            "unknown-failure-code",
            "reference-sampling-failed",
            None,
            "execution-failure-before-deadline",
            _EXECUTION_FAILURE_STATUS,
            "unknown_failure_code",
            "UNKNOWN_FAILURE_CODE",
        ),
        (
            "refusal-code-under-failure-phase",
            "refusal-code-under-failure",
            "plan-validation-refused",
            None,
            "execution-failure-before-deadline",
            _EXECUTION_FAILURE_STATUS,
            "plan_validation_refusal",
            "REFUSAL_CODE_UNDER_FAILURE_PHASE",
        ),
        (
            "failure-code-under-refusal-phase",
            "failure-code-under-refusal",
            "reference-sampling-failed",
            None,
            "preexecution-refusal-before-deadline",
            _PREEXECUTION_STATUS,
            "reference_sampling_failure",
            "FAILURE_CODE_UNDER_REFUSAL_PHASE",
        ),
        (
            "failure-code-on-returned-or-timeout",
            "failure-code-on-returned",
            "returned-rejection-selected",
            "bounded-rejection",
            "returned-before-deadline",
            "returned-rejection-selected-before-deadline",
            "plan_validation_refusal",
            "FAILURE_CODE_ON_RETURNED_OR_TIMEOUT",
        ),
    ]
    return tuple(tuple(row) + (True,) for row in accepted) + tuple(
        tuple(row) + (False,) for row in rejected
    )


def _classifier_cases() -> Tuple[CP66ClassifierQualificationCaseV1, ...]:
    result = []
    for index, row in enumerate(_classifier_case_rows(), 1):
        (
            case_id,
            behavior,
            event_kind,
            strategy,
            phase,
            status,
            failure,
            *tail,
        ) = row
        if len(tail) == 1:
            positive = cast(bool, tail[0])
            machine_code = "CLASSIFICATION_ACCEPTED"
        else:
            machine_code = cast(str, tail[0])
            positive = cast(bool, tail[1])
        result.append(
            cast(
                CP66ClassifierQualificationCaseV1,
                _record(
                    CP66ClassifierQualificationCaseV1,
                    {
                        "schema_version": CP66_TEST28_SCHEMA_VERSION,
                        "case_ordinal": index,
                        "case_id": cast(str, case_id),
                        "strategy": cast(Optional[str], strategy),
                        "event_kind": cast(str, event_kind),
                        "phase": cast(str, phase),
                        "closed_status": cast(str, status),
                        "failure_code": cast(Optional[str], failure),
                        "expected_accept": positive,
                        "expected_machine_code": machine_code,
                        "expected_closed_status": cast(str, status) if positive else "",
                        "expected_failure_code": cast(Optional[str], failure)
                        if positive
                        else None,
                        "expected_classifier_disposition": (
                            "CLASSIFIED" if positive else "CLASSIFICATION_REJECTED"
                        ),
                    },
                ),
            )
        )
    return tuple(result)


def _classifier_contract() -> CP66ClosedClassifierContractV1:
    return cast(
        CP66ClosedClassifierContractV1,
        _record(
            CP66ClosedClassifierContractV1,
            {
                "schema_version": CP66_TEST28_SCHEMA_VERSION,
                "returned_rejection_statuses": _RETURNED_STATUSES[:2],
                "returned_sir_statuses": _RETURNED_STATUSES[2:],
                "timeout_phase": "timeout-at-deadline",
                "timeout_status": _TIMEOUT_STATUS,
                "preexecution_refusal_phase": "preexecution-refusal-before-deadline",
                "preexecution_refusal_codes": _PREEXECUTION_REFUSAL_CODES,
                "execution_failure_phase": "execution-failure-before-deadline",
                "execution_failure_codes": _EXECUTION_FAILURE_CODES,
                "infrastructure_invalid_disposition": "INFRASTRUCTURE_INVALID",
                "timeout_is_semantic_nonreturn": False,
                "no_retry": True,
                "no_drop": True,
                "no_replacement": True,
                "no_topup": True,
                "unknown_phase_or_code_rejected": True,
            },
        ),
    )


def _fixture_set_sha256(
    supervisor_cases: Tuple[CP66SupervisorQualificationCaseV1, ...],
    classifier_cases: Tuple[CP66ClassifierQualificationCaseV1, ...],
) -> str:
    ordered = [case.record_sha256 for case in supervisor_cases + classifier_cases]
    return hashlib.sha256(_FIXTURE_SET_DOMAIN + _plain_json_bytes(ordered)).hexdigest()


def cp66_qualification_fixture_set_sha256() -> str:
    """Return the closed forty-case fixture-set digest."""

    return _fixture_set_sha256(_supervisor_cases(), _classifier_cases())


def _predecessor_custody() -> CP66PredecessorCustodyV1:
    return cast(
        CP66PredecessorCustodyV1,
        _record(
            CP66PredecessorCustodyV1,
            {
                "schema_version": CP66_TEST28_SCHEMA_VERSION,
                "v16_protocol_sha256": _V16_PREREGISTRATION_SHA256,
                "v16_protocol_bytes": 139_376,
                "v16_protocol_lf_count": 2_484,
                "v16_manifest_sha256": _V16_MACHINE_MANIFEST_SHA256,
                "v16_manifest_bytes": 5_993_725,
                "v16_manifest_lf_count": 118_260,
                "cp62_source_sha256": _CP62_SOURCE_SHA256,
                "cp62_bundle_record_sha256": _CP62_BUNDLE_RECORD_SHA256,
                "cp62_bundle_semantic_sha256": _CP62_BUNDLE_SEMANTIC_SHA256,
                "cp62_supervisor_contract_record_sha256": _CP62_SUPERVISOR_CONTRACT_SHA256,
                "cp62_raw_record_schema_record_sha256": _CP62_RAW_SCHEMA_RECORD_SHA256,
                "cp63_source_sha256": _CP63_SOURCE_SHA256,
                "cp63_runner_bundle_record_sha256": _CP63_RUNNER_BUNDLE_RECORD_SHA256,
                "cp63_raw_record_schema_record_sha256": _CP63_RAW_SCHEMA_RECORD_SHA256,
                "cp64_source_sha256": _CP64_SOURCE_SHA256,
                "cp64_bundle_record_sha256": _CP64_BUNDLE_RECORD_SHA256,
                "cp64_no_execution_gate_contract_record_sha256": _CP64_NO_EXECUTION_GATE_RECORD_SHA256,
                "cp65_source_sha256": _CP65_SOURCE_SHA256,
                "cp65_bundle_record_sha256": _CP65_BUNDLE_RECORD_SHA256,
                "cp65_schema_semantic_sha256": _CP65_SCHEMA_SEMANTIC_SHA256,
            },
        ),
    )


_BUNDLE_LOCK = threading.RLock()
_BUNDLE_CACHE: Optional[CP66RunnerSupervisorClassifierQualificationBundleV1] = None


def cp66_runner_supervisor_classifier_qualification_bundle() -> CP66RunnerSupervisorClassifierQualificationBundleV1:
    """Return the pure definition-only CP66 qualification bundle."""

    global _BUNDLE_CACHE
    with _BUNDLE_LOCK:
        if _BUNDLE_CACHE is not None:
            _require_issued_record(_BUNDLE_CACHE)
            return _BUNDLE_CACHE
        supervisor_cases = _supervisor_cases()
        classifier_cases = _classifier_cases()
        rules = _classifier_rules()
        _BUNDLE_CACHE = cast(
            CP66RunnerSupervisorClassifierQualificationBundleV1,
            _record(
                CP66RunnerSupervisorClassifierQualificationBundleV1,
                {
                    "schema_version": CP66_TEST28_SCHEMA_VERSION,
                    "scope": CP66_TEST28_SCOPE,
                    "predecessor_custody": _predecessor_custody(),
                    "closed_classifier_contract": _classifier_contract(),
                    "classifier_rules": rules,
                    "classifier_rule_count": len(rules),
                    "supervisor_cases": supervisor_cases,
                    "classifier_cases": classifier_cases,
                    "qualification_fixture_set_sha256": _fixture_set_sha256(
                        supervisor_cases, classifier_cases
                    ),
                    "supervisor_case_count": len(supervisor_cases),
                    "classifier_reachability_case_count": 16,
                    "classifier_rejection_case_count": 8,
                    "total_case_count": len(supervisor_cases) + len(classifier_cases),
                    "zero_argument_builder": True,
                    "builder_executes_child": False,
                    "generic_command_api_exposed": False,
                    "production_seed_or_request_api_exposed": False,
                    "production_campaign_api_exposed": False,
                    "source_manifest_observed": False,
                    "production_runtime_receipt_observed": False,
                    "freeze_receipt_present": False,
                    "production_runner_implemented": False,
                    "production_runner_supervisor_qualified": False,
                    "production_closed_classifier_qualified": False,
                    "production_qualification_receipts_present": False,
                    "production_execution_observed": False,
                    "runner_and_recomputation_blocker_closed": False,
                    "unconditional_operational_predictions_blocker_closed": False,
                    "power_and_thresholds_blocker_closed": False,
                    "confirmatory_custody_blocker_closed": False,
                    "confirmatory_evidence": False,
                    "manuscript_claim": False,
                    "formal_test_28_status": CP66_TEST28_FORMAL_TEST_28_STATUS,
                    "formal_test_28_closed": False,
                    "ledger_prerequisite_id": CP66_TEST28_BLOCKER_LEDGER_PREREQUISITE_ID,
                    "ledger_prerequisite_state": "SATISFIED_BY_HASH_BOUND_NONCONFIRMATORY_DEVELOPMENT_QUALIFICATION_ARTIFACTS",
                    "ledger_total_count": 21,
                    "ledger_satisfied_count": 17,
                    "ledger_missing_count": 4,
                },
            ),
        )
        return _BUNDLE_CACHE


def _reject_duplicate_pairs(pairs: list) -> dict:
    result: Dict[str, object] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise ValueError("CP66 classifier JSON keys are invalid or duplicated")
        result[key] = value
    return result


def _reject_json_number(_value: str) -> object:
    raise ValueError("CP66 classifier payload contains a forbidden JSON number")


def _parse_classifier_payload(payload: object) -> dict:
    if type(payload) is not bytes:
        raise TypeError("CP66 classifier payload must be exact bytes")
    raw = cast(bytes, payload)
    if not raw or len(raw) > CP66_CLASSIFIER_PAYLOAD_MAX_BYTES:
        raise ValueError("CP66 classifier payload byte bound differs")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("CP66 classifier payload must be ASCII JSON") from error
    value = json.loads(
        text,
        object_pairs_hook=_reject_duplicate_pairs,
        parse_int=_reject_json_number,
        parse_float=_reject_json_number,
        parse_constant=_reject_json_number,
    )
    if type(value) is not dict:
        raise ValueError("CP66 classifier payload must be one object")
    if set(value) != set(_CLASSIFIER_OBSERVATION_KEYS) or len(value) != len(
        _CLASSIFIER_OBSERVATION_KEYS
    ):
        raise ValueError("CP66 classifier payload field set differs")
    if _plain_json_bytes(value) != raw:
        raise ValueError("CP66 classifier payload is not canonical")
    for key in ("schema", "case_id", "event_kind", "phase", "closed_status"):
        if type(value[key]) is not str:
            raise TypeError("CP66 classifier " + key + " must be an exact string")
    for key in ("strategy", "failure_code"):
        if value[key] is not None and type(value[key]) is not str:
            raise TypeError("CP66 classifier " + key + " must be text or null")
    if value["schema"] != CP66_TEST28_SCHEMA_VERSION:
        raise ValueError("CP66 classifier schema differs")
    return value


def _case_result(values: Mapping[str, object]) -> CP66QualificationCaseResultV1:
    semantic = dict(values)
    semantic["normalized_semantic_sha256"] = _ZERO_SHA256
    semantic["record_sha256"] = _ZERO_SHA256
    semantic_sha256 = hashlib.sha256(
        b"cp66-test28-normalized-qualification-case-semantic-v1\0"
        + _plain_json_bytes(semantic)
    ).hexdigest()
    complete = dict(values)
    complete["normalized_semantic_sha256"] = semantic_sha256
    return cast(
        CP66QualificationCaseResultV1,
        _record(CP66QualificationCaseResultV1, complete),
    )


def _classifier_result(
    case: CP66ClassifierQualificationCaseV1,
    *,
    matched_rule_ordinal: Optional[int],
) -> CP66QualificationCaseResultV1:
    empty_sha256 = hashlib.sha256(b"").hexdigest()
    return _case_result(
        {
            "schema_version": CP66_TEST28_SCHEMA_VERSION,
            "case_ordinal": case.case_ordinal,
            "case_id": case.case_id,
            "subsystem": "classifier",
            "expected_disposition": case.expected_classifier_disposition,
            "observed_disposition": case.expected_classifier_disposition,
            "expected_machine_code": case.expected_machine_code,
            "observed_machine_code": case.expected_machine_code,
            "observed_closed_phase": case.phase,
            "observed_closed_status": case.expected_closed_status,
            "observed_failure_code": case.expected_failure_code,
            "classifier_rule_ordinal": matched_rule_ordinal,
            "timeout_observed": False,
            "process_group_cleanup_verified": False,
            "inherited_fd_count_after_exec": None,
            "environment_match": None,
            "exact_one_frame_observed": False,
            "completion_strictly_before_deadline": False,
            "termination_attempted": False,
            "termination_signal_delivered": False,
            "kill_attempted": False,
            "child_reaped": False,
            "process_group_empty": False,
            "stdout_byte_count": 0,
            "stdout_sha256": empty_sha256,
            "stderr_byte_count": 0,
            "stderr_sha256": empty_sha256,
            "passed": True,
            "production_evidence": False,
        }
    )


def _evaluate_classifier_observation(value: Mapping[str, object]) -> Optional[int]:
    phase = cast(str, value["phase"])
    strategy = cast(Optional[str], value["strategy"])
    event_kind = cast(str, value["event_kind"])
    closed_status = cast(str, value["closed_status"])
    failure_code = cast(Optional[str], value["failure_code"])
    if phase not in _CLOSED_PHASES:
        raise CP66QualificationError("UNKNOWN_PHASE", "classifier phase is not frozen")
    if phase == "returned-before-deadline":
        if failure_code is not None:
            raise CP66QualificationError(
                "FAILURE_CODE_ON_RETURNED_OR_TIMEOUT",
                "returned and timeout outcomes cannot carry a failure code",
            )
        if closed_status not in _RETURNED_STATUSES:
            raise CP66QualificationError(
                "UNKNOWN_RETURNED_STATUS", "returned status is not frozen"
            )
        compatible = (
            closed_status in _RETURNED_STATUSES[:2] and strategy == "bounded-rejection"
        ) or (
            closed_status in _RETURNED_STATUSES[2:] and strategy == "fixed-budget-sir"
        )
        if not compatible:
            raise CP66QualificationError(
                "STRATEGY_INCOMPATIBLE_RETURNED_STATUS",
                "returned status is incompatible with the strategy",
            )
        expected_event = {
            _RETURNED_STATUSES[0]: "returned-rejection-selected",
            _RETURNED_STATUSES[1]: "returned-rejection-exhausted",
            _RETURNED_STATUSES[2]: "returned-sir-selected",
        }[closed_status]
        if event_kind != expected_event:
            raise CP66QualificationError(
                "RETURNED_CLASSIFICATION_MISMATCH",
                "returned event kind differs from its closed status",
            )
        return None
    if phase == "timeout-at-deadline":
        if failure_code is not None:
            raise CP66QualificationError(
                "FAILURE_CODE_ON_RETURNED_OR_TIMEOUT",
                "returned and timeout outcomes cannot carry a failure code",
            )
        if (
            strategy is not None
            or event_kind != "timeout-censored"
            or closed_status != _TIMEOUT_STATUS
        ):
            raise CP66QualificationError(
                "TIMEOUT_CLASSIFICATION_MISMATCH",
                "timeout classifier tuple differs",
            )
        return None
    refusal = phase == "preexecution-refusal-before-deadline"
    if refusal:
        if failure_code in _EXECUTION_FAILURE_CODES:
            raise CP66QualificationError(
                "FAILURE_CODE_UNDER_REFUSAL_PHASE",
                "execution failure code appeared under the refusal phase",
            )
        if failure_code not in _PREEXECUTION_REFUSAL_CODES:
            raise CP66QualificationError(
                "UNKNOWN_REFUSAL_CODE", "refusal code is not frozen"
            )
    else:
        if failure_code in _PREEXECUTION_REFUSAL_CODES:
            raise CP66QualificationError(
                "REFUSAL_CODE_UNDER_FAILURE_PHASE",
                "refusal code appeared under the execution failure phase",
            )
        if failure_code not in _EXECUTION_FAILURE_CODES:
            raise CP66QualificationError(
                "UNKNOWN_FAILURE_CODE", "execution failure code is not frozen"
            )
    exact = [
        rule
        for rule in cp66_runner_supervisor_classifier_qualification_bundle().classifier_rules
        if (
            rule.accepted_internal_event_kind,
            rule.closed_phase,
            rule.closed_status,
            rule.failure_code,
        )
        == (event_kind, phase, closed_status, failure_code)
    ]
    if len(exact) != 1 or strategy is not None:
        raise CP66QualificationError(
            "CLASSIFIER_RULE_MISMATCH",
            "classifier event rule did not resolve exactly",
        )
    return exact[0].rule_ordinal


def cp66_classify_supplied_observation(
    payload: object,
) -> CP66QualificationCaseResultV1:
    """Classify one bounded canonical synthetic observation."""

    value = _parse_classifier_payload(payload)
    cases = cp66_runner_supervisor_classifier_qualification_bundle().classifier_cases
    matching = [case for case in cases if case.case_id == value["case_id"]]
    if len(matching) != 1:
        raise CP66QualificationError(
            "UNKNOWN_CLASSIFIER_CASE", "classifier case identifier is not frozen"
        )
    case = matching[0]
    matched_rule = _evaluate_classifier_observation(value)
    supplied = (
        value["strategy"],
        value["event_kind"],
        value["phase"],
        value["closed_status"],
        value["failure_code"],
    )
    expected = (
        case.strategy,
        case.event_kind,
        case.phase,
        case.closed_status,
        case.failure_code,
    )
    if supplied != expected:
        raise CP66QualificationError(
            "CLASSIFIER_CASE_TUPLE_MISMATCH",
            "classifier event tuple differs from its frozen case",
        )
    if not case.expected_accept:
        raise CP66QualificationError(
            "EXPECTED_CLASSIFIER_REJECTION_MISSING",
            "a hostile classifier vector was unexpectedly accepted",
        )
    return _classifier_result(case, matched_rule_ordinal=matched_rule)


def _safe_close(file_descriptor: Optional[int]) -> None:
    if file_descriptor is None:
        return
    try:
        os.close(file_descriptor)
    except OSError:
        pass


def _staging_file_descriptor(file_descriptor: int) -> int:
    if file_descriptor >= 3:
        return file_descriptor
    duplicated = int(fcntl.fcntl(file_descriptor, fcntl.F_DUPFD_CLOEXEC, 3))
    _safe_close(file_descriptor)
    return duplicated


def _source_sha256() -> str:
    with open(os.path.abspath(__file__), "rb") as source:
        return hashlib.sha256(source.read()).hexdigest()


def _child_auth(case_id: str, nonce: str, source_sha256: str) -> str:
    return hashlib.sha256(
        _CHILD_AUTH_DOMAIN
        + case_id.encode("ascii")
        + b"\0"
        + nonce.encode("ascii")
        + b"\0"
        + source_sha256.encode("ascii")
    ).hexdigest()


def _inheritable_parent_file_descriptors(
    excluded: Tuple[int, ...],
) -> Tuple[int, ...]:
    try:
        names = os.listdir("/dev/fd")
    except OSError:
        open_max = int(os.sysconf("SC_OPEN_MAX"))
        if open_max < 3 or open_max > 1_048_576:
            raise CP66QualificationError(
                "PARENT_FD_BOUND_INVALID", "parent open-file bound is not supported"
            )
        candidates = range(3, open_max)
    else:
        candidates = sorted(
            {
                int(name)
                for name in names
                if name.isascii() and name.isdigit() and int(name) >= 3
            }
        )
    excluded_set = set(excluded)
    inherited = []
    for file_descriptor in candidates:
        if file_descriptor in excluded_set:
            continue
        try:
            if os.get_inheritable(file_descriptor):
                inherited.append(file_descriptor)
        except OSError:
            continue
    return tuple(inherited)


def _spawn_qualification_child(
    case: CP66SupervisorQualificationCaseV1,
) -> Tuple[int, int, int]:
    """Spawn one same-source, closed-case child in a fresh session."""

    stdout_read = stdout_write = stderr_read = stderr_write = None
    devnull = extra_fd = pid = None
    try:
        stdout_read, stdout_write = os.pipe()
        stderr_read, stderr_write = os.pipe()
        devnull = os.open(os.devnull, os.O_RDONLY)
        stdout_read = _staging_file_descriptor(stdout_read)
        stdout_write = _staging_file_descriptor(stdout_write)
        stderr_read = _staging_file_descriptor(stderr_read)
        stderr_write = _staging_file_descriptor(stderr_write)
        devnull = _staging_file_descriptor(devnull)
        if case.fd_mode == "drift":
            extra_fd = os.open(os.devnull, os.O_RDONLY)
            extra_fd = _staging_file_descriptor(extra_fd)
        source_sha256 = _source_sha256()
        nonce = hashlib.sha256(
            _CHILD_NONCE_DOMAIN
            + case.case_id.encode("ascii")
            + os.getpid().to_bytes(8, "big", signed=False)
            + time.monotonic_ns().to_bytes(8, "big", signed=False)
        ).hexdigest()
        auth = _child_auth(case.case_id, nonce, source_sha256)
        executable = os.path.abspath(sys.executable)
        safety_arguments = ("-P",) if sys.version_info >= (3, 11) else ()
        arguments = (
            (
                executable,
                "-S",
                "-s",
            )
            + safety_arguments
            + (
                "-u",
                os.path.abspath(__file__),
                "--cp66-qualification-child",
                case.case_id,
                nonce,
                source_sha256,
                auth,
            )
        )
        actions = [
            (os.POSIX_SPAWN_DUP2, devnull, 0),
            (os.POSIX_SPAWN_DUP2, stdout_write, 1),
            (os.POSIX_SPAWN_DUP2, stderr_write, 2),
            (os.POSIX_SPAWN_CLOSE, stdout_read),
            (os.POSIX_SPAWN_CLOSE, stderr_read),
            (os.POSIX_SPAWN_CLOSE, devnull),
            (os.POSIX_SPAWN_CLOSE, stdout_write),
            (os.POSIX_SPAWN_CLOSE, stderr_write),
        ]
        if extra_fd is not None:
            actions.append((os.POSIX_SPAWN_DUP2, extra_fd, 9))
            if extra_fd != 9:
                actions.append((os.POSIX_SPAWN_CLOSE, extra_fd))
        owned_descriptors = tuple(
            cast(int, descriptor)
            for descriptor in (
                stdout_read,
                stdout_write,
                stderr_read,
                stderr_write,
                devnull,
                extra_fd,
            )
            if descriptor is not None
        )
        preserved_targets = (9,) if extra_fd is not None else ()
        for inherited_descriptor in _inheritable_parent_file_descriptors(
            owned_descriptors + preserved_targets
        ):
            actions.append((os.POSIX_SPAWN_CLOSE, inherited_descriptor))
        environment = dict(_SANITIZED_CHILD_ENVIRONMENT)
        if case.environment_mode == "drift":
            environment["CP66_INJECTED_ENVIRONMENT_DRIFT"] = "1"
        pid = os.posix_spawn(
            executable,
            arguments,
            environment,
            file_actions=tuple(actions),
            setpgroup=0,
            setsigmask=(),
            setsigdef=(signal.SIGINT, signal.SIGPIPE, signal.SIGTERM),
        )
        _safe_close(devnull)
        devnull = None
        _safe_close(stdout_write)
        stdout_write = None
        _safe_close(stderr_write)
        stderr_write = None
        _safe_close(extra_fd)
        extra_fd = None
        os.set_blocking(stdout_read, False)
        os.set_blocking(stderr_read, False)
        return cast(int, pid), cast(int, stdout_read), cast(int, stderr_read)
    except BaseException as error:
        for descriptor in (
            stdout_read,
            stdout_write,
            stderr_read,
            stderr_write,
            devnull,
            extra_fd,
        ):
            _safe_close(cast(Optional[int], descriptor))
        if pid is not None:
            try:
                _bounded_kill_and_reap(
                    pid,
                    CP66_TEST28_QUALIFICATION_REAP_CEILING_MILLISECONDS / 1000.0,
                )
            except BaseException:
                pass
        raise CP66QualificationError(
            "CHILD_SPAWN_FAILURE", "failed to spawn the CP66 qualification child"
        ) from error


def _send_process_group_signal(pid: int, signal_number: int) -> bool:
    try:
        os.killpg(pid, signal_number)
        return True
    except ProcessLookupError:
        return False


def _wait_child_nonblocking(pid: int) -> Optional[int]:
    waited, status = os.waitpid(pid, os.WNOHANG)
    return status if waited == pid else None


def _bounded_kill_and_reap(pid: int, ceiling_seconds: float) -> Optional[int]:
    delivered = False
    try:
        delivered = _send_process_group_signal(pid, signal.SIGKILL)
    except BaseException:
        try:
            os.killpg(pid, signal.SIGKILL)
            delivered = True
        except BaseException:
            pass
    if not delivered:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            return None
    deadline = time.monotonic() + ceiling_seconds
    while time.monotonic() < deadline:
        try:
            status = _wait_child_nonblocking(pid)
        except ChildProcessError:
            return None
        if status is not None:
            return status
        time.sleep(0.005)
    raise CP66QualificationError(
        "CHILD_REAP_CEILING_EXPIRED",
        "qualification child was not reaped within the frozen ceiling",
    )


def _process_group_exists(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _exit_and_signal(status: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
    if status is None:
        return None, None
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status), None
    if os.WIFSIGNALED(status):
        return None, os.WTERMSIG(status)
    return None, None


def _classify_completion_relation(
    completion_monotonic_ns: int, deadline_monotonic_ns: int
) -> str:
    if (
        type(completion_monotonic_ns) is not int
        or type(deadline_monotonic_ns) is not int
        or completion_monotonic_ns < 0
        or deadline_monotonic_ns < 0
    ):
        raise TypeError("CP66 monotonic boundary values must be nonnegative integers")
    if completion_monotonic_ns < deadline_monotonic_ns:
        return "before"
    if completion_monotonic_ns == deadline_monotonic_ns:
        return "equal"
    return "after"


def _read_ready_streams(
    selector: selectors.BaseSelector,
    stdout: bytearray,
    stderr: bytearray,
    *,
    timeout: float,
) -> None:
    for key, _events in selector.select(timeout):
        try:
            chunk = os.read(cast(int, key.fd), 65_536)
        except BlockingIOError:
            continue
        if not chunk:
            selector.unregister(key.fd)
            continue
        target = stdout if key.data == "stdout" else stderr
        maximum = (
            CP66_TEST28_RAW_FRAME_MAX_BYTES + 16
            if key.data == "stdout"
            else CP66_TEST28_STDERR_MAX_BYTES + 1
        )
        remaining = maximum - len(target)
        if remaining > 0:
            target.extend(chunk[:remaining])


def _wait_for_group_absence(pid: int, ceiling_seconds: float) -> bool:
    deadline = time.monotonic() + ceiling_seconds
    while time.monotonic() < deadline:
        if not _process_group_exists(pid):
            return True
        time.sleep(0.005)
    return not _process_group_exists(pid)


def _terminate_timeout_group(
    pid: int, status: Optional[int]
) -> Tuple[Optional[int], bool, bool, bool, bool]:
    termination_attempted = status is None or _process_group_exists(pid)
    termination_delivered = False
    kill_attempted = False
    if termination_attempted:
        termination_delivered = _send_process_group_signal(pid, signal.SIGTERM)
    grace_deadline = time.monotonic() + (
        CP66_TEST28_QUALIFICATION_TERMINATION_GRACE_MILLISECONDS / 1000.0
    )
    while time.monotonic() < grace_deadline:
        if status is None:
            status = _wait_child_nonblocking(pid)
        if status is not None and not _process_group_exists(pid):
            break
        time.sleep(0.005)
    if status is None or _process_group_exists(pid):
        kill_attempted = True
        _send_process_group_signal(pid, signal.SIGKILL)
    reap_deadline = time.monotonic() + (
        CP66_TEST28_QUALIFICATION_REAP_CEILING_MILLISECONDS / 1000.0
    )
    while status is None and time.monotonic() < reap_deadline:
        status = _wait_child_nonblocking(pid)
        if status is None:
            time.sleep(0.005)
    if status is None:
        raise CP66QualificationError(
            "CHILD_REAP_CEILING_EXPIRED",
            "qualification child was not reaped within the frozen ceiling",
        )
    group_empty = _wait_for_group_absence(
        pid, CP66_TEST28_QUALIFICATION_REAP_CEILING_MILLISECONDS / 1000.0
    )
    return (
        status,
        termination_attempted,
        termination_delivered,
        kill_attempted,
        group_empty,
    )


_CHILD_FRAME_KEYS = (
    "case_id",
    "closed_status",
    "environment_match",
    "inherited_fd_count_after_exec",
    "schema",
    "source_sha256",
)


def _decode_child_frame(stdout: bytes, case_id: str, source_sha256: str) -> dict:
    if len(stdout) < 8:
        raise CP66QualificationError(
            "CHILD_FRAME_PREFIX_TRUNCATED", "child frame prefix is truncated"
        )
    announced = int.from_bytes(stdout[:8], "big")
    if announced > CP66_TEST28_RAW_FRAME_MAX_BYTES:
        raise CP66QualificationError(
            "CHILD_FRAME_LENGTH_OVERSIZED", "child announced an oversized frame"
        )
    if len(stdout) < announced + 8:
        raise CP66QualificationError(
            "CHILD_FRAME_BODY_TRUNCATED", "child frame body is truncated"
        )
    if len(stdout) > announced + 8:
        raise CP66QualificationError(
            "CHILD_MULTIPLE_OR_TRAILING_FRAMES", "child emitted trailing frame bytes"
        )
    payload = stdout[8:]
    try:
        document = json.loads(
            payload.decode("ascii"), object_pairs_hook=_reject_duplicate_pairs
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise CP66QualificationError(
            "CHILD_FRAME_BODY_INVALID", "child frame body is invalid"
        ) from error
    if (
        type(document) is not dict
        or set(document) != set(_CHILD_FRAME_KEYS)
        or len(document) != len(_CHILD_FRAME_KEYS)
        or _plain_json_bytes(document) != payload
    ):
        raise CP66QualificationError(
            "CHILD_FRAME_BODY_INVALID", "child frame object differs"
        )
    if (
        document["schema"] != CP66_TEST28_SCHEMA_VERSION
        or document["case_id"] != case_id
        or document["source_sha256"] != source_sha256
        or type(document["closed_status"]) is not str
        or type(document["environment_match"]) is not bool
        or type(document["inherited_fd_count_after_exec"]) is not int
        or document["inherited_fd_count_after_exec"] < 0
    ):
        raise CP66QualificationError(
            "CHILD_FRAME_BODY_INVALID", "child frame values differ"
        )
    return document


def _classifier_payload(case: CP66ClassifierQualificationCaseV1) -> bytes:
    return _plain_json_bytes(
        {
            "schema": CP66_TEST28_SCHEMA_VERSION,
            "case_id": case.case_id,
            "strategy": case.strategy,
            "event_kind": case.event_kind,
            "phase": case.phase,
            "closed_status": case.closed_status,
            "failure_code": case.failure_code,
        }
    )


def _classifier_rejection_result(
    case: CP66ClassifierQualificationCaseV1, observed_machine_code: str
) -> CP66QualificationCaseResultV1:
    empty_sha256 = hashlib.sha256(b"").hexdigest()
    passed = (
        not case.expected_accept
        and observed_machine_code == case.expected_machine_code
        and case.expected_classifier_disposition == "CLASSIFICATION_REJECTED"
    )
    return _case_result(
        {
            "schema_version": CP66_TEST28_SCHEMA_VERSION,
            "case_ordinal": case.case_ordinal,
            "case_id": case.case_id,
            "subsystem": "classifier",
            "expected_disposition": case.expected_classifier_disposition,
            "observed_disposition": "CLASSIFICATION_REJECTED",
            "expected_machine_code": case.expected_machine_code,
            "observed_machine_code": observed_machine_code,
            "observed_closed_phase": "",
            "observed_closed_status": "",
            "observed_failure_code": None,
            "classifier_rule_ordinal": None,
            "timeout_observed": False,
            "process_group_cleanup_verified": False,
            "inherited_fd_count_after_exec": None,
            "environment_match": None,
            "exact_one_frame_observed": False,
            "completion_strictly_before_deadline": False,
            "termination_attempted": False,
            "termination_signal_delivered": False,
            "kill_attempted": False,
            "child_reaped": False,
            "process_group_empty": False,
            "stdout_byte_count": 0,
            "stdout_sha256": empty_sha256,
            "stderr_byte_count": 0,
            "stderr_sha256": empty_sha256,
            "passed": passed,
            "production_evidence": False,
        }
    )


def _run_classifier_case(
    case: CP66ClassifierQualificationCaseV1,
) -> CP66QualificationCaseResultV1:
    _require_issued_record(case)
    try:
        result = cp66_classify_supplied_observation(_classifier_payload(case))
    except CP66QualificationError as error:
        if case.expected_accept:
            raise
        return _classifier_rejection_result(case, error.code)
    if not case.expected_accept:
        raise CP66QualificationError(
            "EXPECTED_CLASSIFIER_REJECTION_MISSING",
            "a hostile classifier vector was unexpectedly accepted",
        )
    return result


def _supervise_qualification_case(
    case: CP66SupervisorQualificationCaseV1,
) -> CP66QualificationCaseResultV1:
    _require_issued_record(case)
    pid: Optional[int] = None
    stdout_read: Optional[int] = None
    stderr_read: Optional[int] = None
    selector: Optional[selectors.BaseSelector] = None
    status: Optional[int] = None
    stdout = bytearray()
    stderr = bytearray()
    termination_attempted = False
    termination_delivered = False
    kill_attempted = False
    group_empty = False
    start_monotonic = time.monotonic()
    deadline = start_monotonic + (
        CP66_TEST28_QUALIFICATION_DEADLINE_MILLISECONDS / 1000.0
    )
    hard_ceiling = start_monotonic + CP66_QUALIFICATION_CASE_WALL_CEILING_SECONDS
    signal_timeout = case.case_ordinal in (4, 5, 6)
    natural_timeout = case.case_ordinal in (2, 3)
    unexpected_hard_timeout = False
    unexpected_group_cleanup = False
    terminal_monotonic_ns: Optional[int] = None
    deadline_monotonic_ns = time.monotonic_ns() + (
        CP66_TEST28_QUALIFICATION_DEADLINE_MILLISECONDS * 1_000_000
    )
    try:
        pid, stdout_read, stderr_read = _spawn_qualification_child(case)
        selector = selectors.DefaultSelector()
        selector.register(stdout_read, selectors.EVENT_READ, "stdout")
        selector.register(stderr_read, selectors.EVENT_READ, "stderr")
        while True:
            now = time.monotonic()
            _read_ready_streams(
                selector,
                stdout,
                stderr,
                timeout=max(0.0, min(0.01, hard_ceiling - now)),
            )
            if status is None:
                status = _wait_child_nonblocking(pid)
                if status is not None:
                    terminal_monotonic_ns = time.monotonic_ns()
            now = time.monotonic()
            if signal_timeout and now >= deadline:
                (
                    status,
                    termination_attempted,
                    termination_delivered,
                    kill_attempted,
                    group_empty,
                ) = _terminate_timeout_group(pid, status)
                terminal_monotonic_ns = time.monotonic_ns()
                break
            if status is not None and not selector.get_map():
                break
            if status is not None:
                eof_deadline = time.monotonic() + (
                    CP66_TEST28_QUALIFICATION_PIPE_EOF_GRACE_MILLISECONDS / 1000.0
                )
                while selector.get_map() and time.monotonic() < eof_deadline:
                    _read_ready_streams(selector, stdout, stderr, timeout=0.005)
                break
            if now >= hard_ceiling:
                unexpected_hard_timeout = True
                (
                    status,
                    termination_attempted,
                    termination_delivered,
                    kill_attempted,
                    group_empty,
                ) = _terminate_timeout_group(pid, status)
                terminal_monotonic_ns = time.monotonic_ns()
                break
            if not natural_timeout and not signal_timeout and now >= deadline:
                unexpected_hard_timeout = True
                (
                    status,
                    termination_attempted,
                    termination_delivered,
                    kill_attempted,
                    group_empty,
                ) = _terminate_timeout_group(pid, status)
                terminal_monotonic_ns = time.monotonic_ns()
                break
        if selector is not None:
            eof_deadline = time.monotonic() + (
                CP66_TEST28_QUALIFICATION_PIPE_EOF_GRACE_MILLISECONDS / 1000.0
            )
            while selector.get_map() and time.monotonic() < eof_deadline:
                _read_ready_streams(selector, stdout, stderr, timeout=0.005)
        if status is None:
            (
                status,
                termination_attempted,
                termination_delivered,
                kill_attempted,
                group_empty,
            ) = _terminate_timeout_group(pid, status)
            terminal_monotonic_ns = time.monotonic_ns()
            unexpected_hard_timeout = True
        if not group_empty:
            group_empty = _wait_for_group_absence(
                pid,
                CP66_TEST28_QUALIFICATION_REAP_CEILING_MILLISECONDS / 1000.0,
            )
        if not group_empty:
            unexpected_group_cleanup = True
            (
                status,
                cleanup_attempted,
                cleanup_delivered,
                cleanup_kill_attempted,
                group_empty,
            ) = _terminate_timeout_group(pid, status)
            termination_attempted = termination_attempted or cleanup_attempted
            termination_delivered = termination_delivered or cleanup_delivered
            kill_attempted = kill_attempted or cleanup_kill_attempted
    except BaseException as error:
        if pid is not None:
            try:
                _send_process_group_signal(pid, signal.SIGKILL)
            except BaseException:
                pass
            if status is None:
                try:
                    _bounded_kill_and_reap(
                        pid,
                        CP66_TEST28_QUALIFICATION_REAP_CEILING_MILLISECONDS / 1000.0,
                    )
                except BaseException:
                    pass
        raise CP66QualificationError(
            "QUALIFICATION_INFRASTRUCTURE_FAILURE",
            "the bounded qualification supervisor encountered an infrastructure fault",
        ) from error
    finally:
        if selector is not None:
            try:
                selector.close()
            except BaseException:
                pass
        _safe_close(stdout_read)
        _safe_close(stderr_read)

    retained_stdout = bytes(stdout)
    retained_stderr = bytes(stderr)
    exit_code, term_signal = _exit_and_signal(status)
    if case.deadline_relation == "equal":
        comparison_terminal_ns = deadline_monotonic_ns
    elif case.deadline_relation == "after":
        comparison_terminal_ns = deadline_monotonic_ns + 1
    elif terminal_monotonic_ns is not None:
        comparison_terminal_ns = terminal_monotonic_ns
    else:
        comparison_terminal_ns = deadline_monotonic_ns + 1
    completion_relation = _classify_completion_relation(
        comparison_terminal_ns, deadline_monotonic_ns
    )
    completion_before_deadline = completion_relation == "before"
    frame_document: Optional[dict] = None
    frame_error_code: Optional[str] = None
    try:
        if not retained_stdout:
            raise CP66QualificationError(
                "CHILD_FRAME_MISSING", "child emitted no qualification frame"
            )
        frame_document = _decode_child_frame(
            retained_stdout, case.case_id, _source_sha256()
        )
    except CP66QualificationError as error:
        frame_error_code = error.code

    expected_timeout = natural_timeout or signal_timeout
    observed_disposition: str
    observed_machine_code: str
    observed_closed_phase = ""
    observed_closed_status = ""
    if unexpected_hard_timeout:
        observed_disposition = "INFRASTRUCTURE_INVALID"
        observed_machine_code = "QUALIFICATION_WALL_CEILING_EXPIRED"
    elif unexpected_group_cleanup:
        observed_disposition = "INFRASTRUCTURE_INVALID"
        observed_machine_code = "RESIDUAL_PROCESS_GROUP"
    elif expected_timeout:
        natural_valid = (
            natural_timeout
            and status is not None
            and exit_code == 0
            and term_signal is None
            and frame_document is not None
            and completion_relation in ("equal", "after")
        )
        signalled_valid = (
            signal_timeout
            and status is not None
            and termination_attempted
            and termination_delivered
            and group_empty
            and retained_stdout == b""
            and (
                (
                    case.expected_term_signal == int(signal.SIGTERM)
                    and term_signal == signal.SIGTERM
                )
                or (
                    case.expected_term_signal == int(signal.SIGKILL)
                    and kill_attempted
                    and term_signal == signal.SIGKILL
                )
            )
        )
        if natural_valid or signalled_valid:
            observed_disposition = "TIMEOUT_CENSORED"
            observed_machine_code = (
                "TIMEOUT_AT_DEADLINE"
                if natural_timeout and completion_relation == "equal"
                else "TIMEOUT_AFTER_DEADLINE"
                if natural_timeout and completion_relation == "after"
                else case.expected_machine_code
            )
            observed_closed_phase = "timeout-at-deadline"
            observed_closed_status = _TIMEOUT_STATUS
        else:
            observed_disposition = "INFRASTRUCTURE_INVALID"
            observed_machine_code = "TIMEOUT_MECHANICS_INVALID"
    elif len(retained_stderr) > CP66_TEST28_STDERR_MAX_BYTES:
        observed_disposition = "INFRASTRUCTURE_INVALID"
        observed_machine_code = "CHILD_STDERR_OVERSIZED"
    elif exit_code != 0 or term_signal is not None:
        observed_disposition = "INFRASTRUCTURE_INVALID"
        observed_machine_code = "CHILD_ABNORMAL_EXIT"
    elif frame_error_code is not None:
        observed_disposition = "INFRASTRUCTURE_INVALID"
        observed_machine_code = frame_error_code
    elif cast(dict, frame_document)["inherited_fd_count_after_exec"] != 0:
        observed_disposition = "INFRASTRUCTURE_INVALID"
        observed_machine_code = "CHILD_INHERITED_FD_DRIFT"
    elif cast(dict, frame_document)["environment_match"] is not True:
        observed_disposition = "INFRASTRUCTURE_INVALID"
        observed_machine_code = "CHILD_ENVIRONMENT_DRIFT"
    else:
        observed_disposition = "VALID"
        observed_machine_code = "VALID_RETURN"
        observed_closed_phase = "returned-before-deadline"
        observed_closed_status = cast(str, cast(dict, frame_document)["closed_status"])

    exact_one_frame = frame_document is not None
    observed_fd_count = (
        cast(int, frame_document["inherited_fd_count_after_exec"])
        if frame_document is not None
        else None
    )
    observed_environment = (
        cast(bool, frame_document["environment_match"])
        if frame_document is not None
        else None
    )
    process_group_cleanup_verified = case.process_group_empty_required and group_empty
    passed = (
        observed_disposition == case.expected_supervisor_disposition
        and observed_machine_code == case.expected_machine_code
        and observed_closed_status == case.expected_closed_status
        and status is not None
        and group_empty
        and (not case.exact_one_frame_expected or exact_one_frame)
        and (not case.process_group_empty_required or process_group_cleanup_verified)
        and (not case.no_fd_leak_required or observed_fd_count == 0)
        and (not case.environment_match_required or observed_environment is True)
        and (case.expected_term_signal == 0 or term_signal == case.expected_term_signal)
    )
    return _case_result(
        {
            "schema_version": CP66_TEST28_SCHEMA_VERSION,
            "case_ordinal": case.case_ordinal,
            "case_id": case.case_id,
            "subsystem": "supervisor",
            "expected_disposition": case.expected_supervisor_disposition,
            "observed_disposition": observed_disposition,
            "expected_machine_code": case.expected_machine_code,
            "observed_machine_code": observed_machine_code,
            "observed_closed_phase": observed_closed_phase,
            "observed_closed_status": observed_closed_status,
            "observed_failure_code": None,
            "classifier_rule_ordinal": None,
            "timeout_observed": expected_timeout,
            "process_group_cleanup_verified": process_group_cleanup_verified,
            "inherited_fd_count_after_exec": observed_fd_count,
            "environment_match": observed_environment,
            "exact_one_frame_observed": exact_one_frame,
            "completion_strictly_before_deadline": completion_before_deadline,
            "termination_attempted": termination_attempted,
            "termination_signal_delivered": termination_delivered,
            "kill_attempted": kill_attempted,
            "child_reaped": status is not None,
            "process_group_empty": group_empty,
            "stdout_byte_count": len(retained_stdout),
            "stdout_sha256": hashlib.sha256(retained_stdout).hexdigest(),
            "stderr_byte_count": len(retained_stderr),
            "stderr_sha256": hashlib.sha256(retained_stderr).hexdigest(),
            "passed": passed,
            "production_evidence": False,
        }
    )


def cp66_run_qualification_case(case_id: object) -> CP66QualificationCaseResultV1:
    """Run exactly one module-owned synthetic qualification case."""

    if type(case_id) is not str:
        raise TypeError("CP66 qualification case identifier must be an exact string")
    bundle = cp66_runner_supervisor_classifier_qualification_bundle()
    supervisor = [case for case in bundle.supervisor_cases if case.case_id == case_id]
    classifier = [case for case in bundle.classifier_cases if case.case_id == case_id]
    if len(supervisor) + len(classifier) != 1:
        raise CP66QualificationError(
            "UNKNOWN_QUALIFICATION_CASE", "qualification case identifier is not frozen"
        )
    if supervisor:
        return _supervise_qualification_case(supervisor[0])
    return _run_classifier_case(classifier[0])


def cp66_run_qualification_suite() -> CP66QualificationRunV1:
    """Run all forty bounded development-only qualification cases once."""

    suite_deadline = time.monotonic() + CP66_QUALIFICATION_SUITE_WALL_CEILING_SECONDS
    bundle = cp66_runner_supervisor_classifier_qualification_bundle()
    ordered_ids = tuple(
        case.case_id for case in bundle.supervisor_cases + bundle.classifier_cases
    )
    result_rows = []
    for case_id in ordered_ids:
        if time.monotonic() >= suite_deadline:
            raise CP66QualificationError(
                "QUALIFICATION_SUITE_WALL_CEILING_EXPIRED",
                "qualification suite exceeded its frozen wall-time ceiling",
            )
        result_rows.append(cp66_run_qualification_case(case_id))
        if time.monotonic() >= suite_deadline:
            raise CP66QualificationError(
                "QUALIFICATION_SUITE_WALL_CEILING_EXPIRED",
                "qualification suite exceeded its frozen wall-time ceiling",
            )
    results = tuple(result_rows)
    passed_count = sum(1 for result in results if result.passed)
    supervisor_passed = all(result.passed for result in results[:16])
    classifier_passed = all(result.passed for result in results[16:])
    return cast(
        CP66QualificationRunV1,
        _record(
            CP66QualificationRunV1,
            {
                "schema_version": CP66_TEST28_SCHEMA_VERSION,
                "qualification_fixture_set_sha256": bundle.qualification_fixture_set_sha256,
                "ordered_case_ids": ordered_ids,
                "ordered_case_result_sha256s": tuple(
                    result.record_sha256 for result in results
                ),
                "case_count": len(results),
                "passed_case_count": passed_count,
                "supervisor_case_count": 16,
                "classifier_reachability_case_count": 16,
                "classifier_rejection_case_count": 8,
                "timeout_case_count": 5,
                "process_group_cleanup_case_count": 3,
                "fd_leak_case_count": 2,
                "environment_drift_case_count": 2,
                "all_cases_passed": passed_count == len(results),
                "development_supervisor_mechanics_qualified": supervisor_passed,
                "development_classifier_mechanics_qualified": classifier_passed,
                "qualification_python_profile_matched": (
                    sys.implementation.name == "cpython"
                    and sys.version_info[:3] == (3, 11, 5)
                ),
                "scaled_timing_not_production_clock_fidelity": True,
                "production_clock_fidelity_qualified": False,
                "volatile_pids_or_timestamps_in_semantic_digest": False,
                "production_qualification_receipt_present": False,
                "production_supervisor_qualified": False,
                "production_classifier_qualified": False,
                "production_execution_authorized": False,
                "runner_and_recomputation_blocker_closed": False,
                "formal_test_28_closed": False,
            },
        ),
    )


def _write_all(file_descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(file_descriptor, payload[offset:])
        if written <= 0:
            raise OSError("CP66 child output write made no progress")
        offset += written


def _child_open_extra_fd_count() -> int:
    try:
        names = os.listdir("/dev/fd")
        candidates = tuple(
            sorted(
                {
                    int(name)
                    for name in names
                    if name.isascii() and name.isdigit() and int(name) >= 3
                }
            )
        )
    except OSError:
        open_max = int(os.sysconf("SC_OPEN_MAX"))
        if open_max < 3 or open_max > 1_048_576:
            raise CP66QualificationError(
                "CHILD_FD_BOUND_INVALID", "child open-file bound is not supported"
            )
        candidates = tuple(range(3, open_max))
    count = 0
    for file_descriptor in candidates:
        try:
            fcntl.fcntl(file_descriptor, fcntl.F_GETFD)
        except OSError as error:
            if error.errno != errno.EBADF:
                raise
        else:
            count += 1
    return count


def _child_close_unexpected_file_descriptors(
    case: CP66SupervisorQualificationCaseV1,
) -> None:
    preserved = {9} if case.fd_mode == "drift" else set()
    try:
        names = os.listdir("/dev/fd")
        candidates = tuple(
            sorted(
                {
                    int(name)
                    for name in names
                    if name.isascii() and name.isdigit() and int(name) >= 3
                }
            )
        )
    except OSError:
        open_max = int(os.sysconf("SC_OPEN_MAX"))
        if open_max < 3 or open_max > 1_048_576:
            raise CP66QualificationError(
                "CHILD_FD_BOUND_INVALID", "child open-file bound is not supported"
            )
        candidates = tuple(range(3, open_max))
    for file_descriptor in candidates:
        if file_descriptor not in preserved:
            _safe_close(file_descriptor)


def _child_frame(case: CP66SupervisorQualificationCaseV1, source_sha256: str) -> bytes:
    payload = _plain_json_bytes(
        {
            "schema": CP66_TEST28_SCHEMA_VERSION,
            "case_id": case.case_id,
            "closed_status": case.expected_closed_status,
            "environment_match": dict(os.environ) == dict(_SANITIZED_CHILD_ENVIRONMENT),
            "inherited_fd_count_after_exec": _child_open_extra_fd_count(),
            "source_sha256": source_sha256,
        }
    )
    return len(payload).to_bytes(8, "big") + payload


def _child_descendant_timeout() -> None:
    descendant = os.fork()
    if descendant == 0:
        while True:
            time.sleep(60)

    def reap_and_reraise(signal_number: int, _frame: object) -> None:
        deadline = time.monotonic() + (
            CP66_TEST28_QUALIFICATION_REAP_CEILING_MILLISECONDS / 1000.0
        )
        while time.monotonic() < deadline:
            try:
                waited, _status = os.waitpid(descendant, os.WNOHANG)
            except ChildProcessError:
                break
            if waited == descendant:
                break
            time.sleep(0.005)
        else:
            try:
                os.kill(descendant, signal.SIGKILL)
            except ProcessLookupError:
                pass
        signal.signal(signal_number, signal.SIG_DFL)
        os.kill(os.getpid(), signal_number)

    signal.signal(signal.SIGTERM, reap_and_reraise)
    while True:
        time.sleep(60)


def _qualification_child_main(arguments: Tuple[str, ...]) -> int:
    if len(arguments) != 5 or arguments[0] != "--cp66-qualification-child":
        return 64
    _, case_id, nonce, supplied_source_sha256, supplied_auth = arguments
    cases = {
        case.case_id: case
        for case in cp66_runner_supervisor_classifier_qualification_bundle().supervisor_cases
    }
    case = cases.get(case_id)
    if (
        case is None
        or len(nonce) != 64
        or any(character not in "0123456789abcdef" for character in nonce)
        or len(supplied_source_sha256) != 64
    ):
        return 65
    actual_source_sha256 = _source_sha256()
    if not hmac.compare_digest(supplied_source_sha256, actual_source_sha256):
        return 66
    if not hmac.compare_digest(
        supplied_auth, _child_auth(case_id, nonce, supplied_source_sha256)
    ):
        return 67
    _child_close_unexpected_file_descriptors(case)
    if case.case_id == "descendant-process-group-cleanup":
        _child_descendant_timeout()
        return 68
    if case.exit_mode == "wait-for-sigterm":
        while True:
            time.sleep(60)
    if case.exit_mode == "ignore-sigterm":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        while True:
            time.sleep(60)
    if case.deadline_relation == "equal":
        time.sleep(CP66_TEST28_QUALIFICATION_DEADLINE_MILLISECONDS / 1000.0)
    elif case.deadline_relation == "after":
        time.sleep((CP66_TEST28_QUALIFICATION_DEADLINE_MILLISECONDS + 75) / 1000.0)
    if case.exit_mode == "abnormal":
        return 7
    frame = _child_frame(case, actual_source_sha256)
    if case.frame_mode == "one":
        _write_all(1, frame)
    elif case.frame_mode == "two":
        _write_all(1, frame + frame)
    elif case.frame_mode == "truncated-prefix":
        _write_all(1, b"\0\0\0")
    elif case.frame_mode == "truncated-body":
        _write_all(1, (64).to_bytes(8, "big") + b"{}")
    elif case.frame_mode == "oversize":
        _write_all(1, (CP66_TEST28_RAW_FRAME_MAX_BYTES + 1).to_bytes(8, "big"))
    elif case.frame_mode not in ("zero", "none"):
        return 69
    if case.case_id == "stderr-over-cap":
        chunk = b"E" * 65_536
        remaining = CP66_TEST28_STDERR_MAX_BYTES + 1
        while remaining:
            current = chunk[: min(remaining, len(chunk))]
            _write_all(2, current)
            remaining -= len(current)
    return 0


if __name__ == "__main__":
    raise SystemExit(_qualification_child_main(tuple(sys.argv[1:])))


__all__ = (
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
