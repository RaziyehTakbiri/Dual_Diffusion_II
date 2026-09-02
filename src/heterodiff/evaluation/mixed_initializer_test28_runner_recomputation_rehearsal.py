"""Definition-only CP63 runner/recomputation rehearsal boundary.

This module binds an external seed-capsule *syntax*, the seed-major request
schedule, runner lifecycle/resource contracts, and sixteen fixed development
rehearsal cases.  It does not authorize production seed use, expose a campaign
loop, write an attempt, bind shards, or certify capacity.

Only the Python standard library is imported at module import time.  Numerical
and project execution dependencies are reserved for the private rehearsal
child path.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import struct
import sys
import threading
import time
from types import SimpleNamespace
from typing import Mapping, Optional, Tuple, cast


CP63_TEST28_SCHEMA_VERSION = "cp63-test28-runner-recomputation-rehearsal-v1"
CP63_TEST28_SCOPE = (
    "development-runner-recomputation-rehearsal;external-seed-capsule-syntax-"
    "only;seed-major-definition-only-request-binding;all-sixteen-fixed-row-"
    "rehearsals;no-production-seed-execution-no-arbitrary-seed-no-campaign-"
    "no-durable-writer-no-shards-no-capacity-receipt-no-blocker-closure"
)

_CP61_STABLE_DESIGN_SHA256 = (
    "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
)
_CP62_SOURCE_SHA256 = "44ef12b1a556d80944774ac9b698acf1359879fe44729120a04feb5e7a4a8a49"
_CP62_BUNDLE_SHA256 = "0f92f54ce8d451485019f6d697736fd5eb48d2b942e1d3a3f1bd373b50c3ec92"
_CP62_SEMANTIC_SHA256 = (
    "f3bd0b80c52a9d79a3b6a8e06aa2923c6303e891bf526c1869c5552e1413f3ff"
)
_REHEARSAL_SEED_HEX = "12a5228200019dae"
_REHEARSAL_ID = "cp63-all-row-rehearsal-v1"
_RUNTIME_LOCK_SHA256 = (
    "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
)
_ZERO_SHA256 = "0" * 64
_ALLOW_RECORD_CLASS_DEFINITION = True

_SEED_CAPSULE_KEYS = (
    "schema",
    "purpose",
    "cp61_stable_design_sha256",
    "seed_count",
    "seed_ordinals",
    "seed_encoding",
    "ordered_seed_values",
    "source_method_id",
    "source_receipt_sha256",
    "acquisition_session_sha256",
    "body_sha256",
)
_RAW_OUTER_KEYS = (
    "schema",
    "purpose",
    "rehearsal_id",
    "repetition",
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

_ROW_INVENTORY = (
    (
        1,
        "row-01/T28-M1-Q/bounded-rejection/budget-1",
        "T28-M1-Q",
        "bounded-rejection",
        1,
        "a99bafb93499e89d054dd8e0df8c9a04acff29142620a7da374aa88dae53215a",
    ),
    (
        2,
        "row-02/T28-M1-Q/bounded-rejection/budget-4",
        "T28-M1-Q",
        "bounded-rejection",
        4,
        "f9f2d4f1d8aad14bbe5075b4febd763af4652fb4dda337e7a8d295b3a6045ec2",
    ),
    (
        3,
        "row-03/T28-M1-Q/bounded-rejection/budget-16",
        "T28-M1-Q",
        "bounded-rejection",
        16,
        "4413d707c0165dbf18e88df043edd760a75d4eed44d039a611402e06de9c4eb8",
    ),
    (
        4,
        "row-04/T28-M1-Q/bounded-rejection/budget-64",
        "T28-M1-Q",
        "bounded-rejection",
        64,
        "29f1f28fb222d258746cb7956a9ca0d65a6e97d398eddb1612720a9339eed338",
    ),
    (
        5,
        "row-05/T28-M1-Q/fixed-budget-sir/budget-8",
        "T28-M1-Q",
        "fixed-budget-sir",
        8,
        "71701768f889fee219b854217de255f3d034202a3a66875ceade1cd55955896a",
    ),
    (
        6,
        "row-06/T28-M1-Q/fixed-budget-sir/budget-32",
        "T28-M1-Q",
        "fixed-budget-sir",
        32,
        "bd7c4fd661bda70f29b8582c0db52d91d68fc703ae8838295a21cf9e6e55f23a",
    ),
    (
        7,
        "row-07/T28-M1-Q/fixed-budget-sir/budget-128",
        "T28-M1-Q",
        "fixed-budget-sir",
        128,
        "801f600536240a2f6f3de0dcac8d4092c2121fd17dc14fb0ca0bfc3b0260acb8",
    ),
    (
        8,
        "row-08/T28-M1-Q/fixed-budget-sir/budget-512",
        "T28-M1-Q",
        "fixed-budget-sir",
        512,
        "8e5458a8dfca1e49875cad53deff7447274ce3055960a0031cc07c4ec4de33e0",
    ),
    (
        9,
        "row-09/T28-M2-Q/bounded-rejection/budget-1",
        "T28-M2-Q",
        "bounded-rejection",
        1,
        "7d32b4e85d39504864268b7ba39189f17c3171d11079638e37a6614b97a543bf",
    ),
    (
        10,
        "row-10/T28-M2-Q/bounded-rejection/budget-4",
        "T28-M2-Q",
        "bounded-rejection",
        4,
        "17f11b448585709ef35a172e86665c83b2ea50a907caacdd400dbd8ce625771b",
    ),
    (
        11,
        "row-11/T28-M2-Q/bounded-rejection/budget-16",
        "T28-M2-Q",
        "bounded-rejection",
        16,
        "57937405e7302fcd9b9935050050a74e4b2c2818e17d720cde1ee2a56352bcf3",
    ),
    (
        12,
        "row-12/T28-M2-Q/bounded-rejection/budget-64",
        "T28-M2-Q",
        "bounded-rejection",
        64,
        "878797b61ec628ae5db0e882d6f3c34531468fbbc35fd92325063a3b017c1bd8",
    ),
    (
        13,
        "row-13/T28-M2-Q/fixed-budget-sir/budget-8",
        "T28-M2-Q",
        "fixed-budget-sir",
        8,
        "bc7b374f072aa402264634bcf520834a71609af5f6705b9b8ac3079884cd0376",
    ),
    (
        14,
        "row-14/T28-M2-Q/fixed-budget-sir/budget-32",
        "T28-M2-Q",
        "fixed-budget-sir",
        32,
        "1b60b917c4fba30085678101276fe2a210aaa82f34deb6ad4f9440a38cc3b074",
    ),
    (
        15,
        "row-15/T28-M2-Q/fixed-budget-sir/budget-128",
        "T28-M2-Q",
        "fixed-budget-sir",
        128,
        "a88491906e47ec4f5483b638ce411b8afd4ce7b5d73f19e372ab68a405f6d81c",
    ),
    (
        16,
        "row-16/T28-M2-Q/fixed-budget-sir/budget-512",
        "T28-M2-Q",
        "fixed-budget-sir",
        512,
        "0667c6c19a9b54db91f2167f685abdcaafcab73cbc4bcfaebcb420511ecc89c8",
    ),
)

_REHEARSAL_LAUNCH_COUNT = 0
_REHEARSAL_CASE_LAUNCH_COUNTS = {
    f"rehearsal-row-{row_ordinal:02d}": 0 for row_ordinal in range(1, 17)
}
_REHEARSAL_RUNNING = False
_REHEARSAL_STATE_LOCK = threading.Lock()
_CHILD_AUTH_DOMAIN = b"cp63-test28-rehearsal-child-auth-v1\0"
_CHILD_NONCE_DOMAIN = b"cp63-test28-rehearsal-child-nonce-v1\0"
_PIPE_EOF_GRACE_NS = 1_000_000_000
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


class CP63RunnerRehearsalError(RuntimeError):
    """Fail-closed CP63 boundary error carrying a stable machine code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class _SealedRecord:
    __slots__ = ()

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("CP63 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("CP63 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP63 records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP63SeedCapsuleContractV1(_SealedRecord):
    schema_version: str
    purpose: str
    cp61_stable_design_sha256: str
    seed_count: int
    seed_ordinals: Tuple[int, ...]
    seed_encoding: str
    exact_json_keys: Tuple[str, ...]
    maximum_capsule_bytes: int
    duplicate_values_retained: bool
    order_is_semantic: bool
    no_retry_drop_replacement_or_topup: bool
    source_method_required: bool
    source_receipt_required: bool
    acquisition_session_required: bool
    body_digest_required: bool
    parser_can_verify_iid_uniform: bool
    production_values_present: bool
    record_sha256: str


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP63SeedCapsuleObservationV1(_SealedRecord):
    schema: str
    purpose: str
    cp61_stable_design_sha256: str
    seed_count: int
    seed_ordinals: Tuple[int, ...]
    seed_encoding: str
    ordered_seed_values: Tuple[str, ...]
    source_method_id: str
    source_receipt_sha256: str
    acquisition_session_sha256: str
    body_sha256: str
    canonical_byte_count: int
    syntactically_valid: bool
    source_custody_digest_bound: bool
    iid_uniform_with_replacement_verified: bool
    production_execution_authorized: bool
    record_sha256: str


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP63ScheduleContractV1(_SealedRecord):
    schema_version: str
    seed_count: int
    row_count: int
    row_ordinals: Tuple[int, ...]
    total_request_count: int
    logical_request_ordinal_min: int
    logical_request_ordinal_max: int
    logical_request_order: str
    plan_seed_assignment: str
    fixture_strategy_budget_or_shard_hashing_before_plan_seed_assignment: bool
    duplicate_seed_values_distinguished_by_ordinal: bool
    schedule_digest_formula: str
    shard_mapping_bound: bool
    production_schedule_instantiated: bool
    record_sha256: str


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP63BoundRequestV1(_SealedRecord):
    schema_version: str
    seed_capsule_body_sha256: str
    seed_ordinal: int
    row_ordinal: int
    logical_request_ordinal: int
    row_key: str
    fixture_id: str
    strategy: str
    budget: int
    plan_seed_hex: str
    seed_free_request_sha256: str
    runtime_lock_sha256: str
    request_instance_sha256: str
    definition_only: bool
    production_execution_authorized: bool
    record_sha256: str


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP63LifecycleContractV1(_SealedRecord):
    schema_version: str
    lifecycle_id: str
    allowed_states: Tuple[str, ...]
    initial_state: str
    terminal_states: Tuple[str, ...]
    no_retry_drop_replacement_or_topup: bool
    infrastructure_failure_invalidates_entire_attempt: bool
    timeout_is_semantic_nonreturn: bool
    attempt_spent_after_durable_stochastic_output: bool
    confirmatory_states_enterable: bool
    filesystem_mutation_permitted: bool
    production_lifecycle_instantiated: bool
    record_sha256: str


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP63RawRecordSchemaV1(_SealedRecord):
    schema_version: str
    purpose: str
    exact_outer_keys: Tuple[str, ...]
    child_frame_encoding: str
    public_raw_record_encoding: str
    uint64_encoding: str
    float64_encoding: str
    fraction_encoding: str
    bytes_encoding: str
    four_closed_outcome_arms: Tuple[str, ...]
    preexecution_refusal_codes: Tuple[str, ...]
    execution_failure_codes: Tuple[str, ...]
    complete_kernel_trace_required_for_validated_returns: bool
    volatile_supervisor_custody_retained: bool
    recompute_owned_semantic_leaf_hashes: bool
    future_production_shape_predeclared: bool
    infrastructure_failure_has_raw_record: bool
    raw_trace_retained_separately: bool
    production_schema_frozen: bool
    production_records_observed: bool
    raw_frame_max_bytes: int
    record_sha256: str


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP63RunnerResourceContractV1(_SealedRecord):
    schema_version: str
    seed_capsule_max_bytes: int
    request_frame_max_bytes: int
    raw_frame_max_bytes: int
    stable_trace_max_bytes: int
    stderr_max_bytes: int
    deadline_seconds: int
    termination_grace_seconds: int
    reap_ceiling_seconds: int
    rehearsal_concurrency: int
    rehearsal_launch_limit: int
    external_seed_count: int
    row_count: int
    total_request_count: int
    rejection_proposal_slot_count: int
    sir_proposal_slot_count: int
    total_proposal_slot_count: int
    sir_resampling_draw_count: int
    maximum_event_occurrence_count: int
    maximum_coordinate_count: int
    maximum_future_raw_aggregate_bytes: int
    maximum_future_stable_aggregate_bytes: int
    capacity_receipt_present: bool
    production_resources_allocated: bool
    record_sha256: str


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP63RehearsalCaseV1(_SealedRecord):
    schema_version: str
    case_id: str
    row_ordinal: int
    row_key: str
    fixture_id: str
    strategy: str
    budget: int
    seed_hex: str
    seed_derivation: str
    seed_is_external_source_draw: bool
    seed_is_future_capsule_member: bool
    requested_repetitions: int
    maximum_child_launches: int
    production_observation: bool
    record_sha256: str


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP63RunnerRecomputationRehearsalBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    cp62_source_sha256: str
    cp62_bundle_sha256: str
    cp62_semantic_sha256: str
    seed_capsule_contract: CP63SeedCapsuleContractV1
    schedule_contract: CP63ScheduleContractV1
    lifecycle_contract: CP63LifecycleContractV1
    raw_record_schema: CP63RawRecordSchemaV1
    resource_contract: CP63RunnerResourceContractV1
    rehearsal_cases: Tuple[CP63RehearsalCaseV1, ...]
    seed_capsule_parser_exposed: bool
    seed_capsule_syntax_only: bool
    production_seed_ingest_for_execution: bool
    arbitrary_seed_execution: bool
    campaign_loop_exposed: bool
    durable_attempt_writer: bool
    shard_mapping_bound: bool
    capacity_receipt_present: bool
    rehearsal_all_rows_executed: bool
    closed_refusal_failure_classification_implemented: bool
    full_32768_recomputation_exposed: bool
    estimates_computed: bool
    intervals_computed: bool
    decision_made: bool
    production_schema_frozen: bool
    production_runner_bound: bool
    runner_and_recomputation_blocker_closed: bool
    formal_test_28_closed: bool
    record_sha256: str


_ALLOW_RECORD_CLASS_DEFINITION = False


def _seal(cls: type, values: dict[str, object]) -> object:
    if set(values) != {item.name for item in fields(cls)}:
        raise TypeError("CP63 sealed record field set differs")
    result = object.__new__(cls)
    for item in fields(cls):
        object.__setattr__(result, item.name, values[item.name])
    return result


def _plain_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _canonical_record_value(value: object) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is tuple:
        return {"$tuple": [_canonical_record_value(item) for item in value]}
    if isinstance(value, _SealedRecord):
        return {
            "$record": type(value).__name__,
            "fields": {
                item.name: _canonical_record_value(getattr(value, item.name))
                for item in fields(type(value))
            },
        }
    raise TypeError("value has no CP63 canonical record representation")


def _canonical_record_bytes(value: object) -> bytes:
    return _plain_json_bytes(_canonical_record_value(value))


def _record(cls: type, domain: bytes, values: dict[str, object]) -> object:
    payload = dict(values)
    payload["record_sha256"] = _ZERO_SHA256
    provisional = _seal(cls, payload)
    payload["record_sha256"] = hashlib.sha256(
        domain + b"\0" + _canonical_record_bytes(provisional)
    ).hexdigest()
    return _seal(cls, payload)


def _validate_record(value: object, cls: type, domain: bytes, name: str) -> object:
    if type(value) is not cls:
        raise TypeError(name + " must be the exact sealed record type")
    supplied = getattr(value, "record_sha256", None)
    if not _is_sha256(supplied):
        raise TypeError(name + " record digest is invalid")
    values = {item.name: getattr(value, item.name) for item in fields(cls)}
    values["record_sha256"] = _ZERO_SHA256
    provisional = _seal(cls, values)
    expected = hashlib.sha256(
        domain + b"\0" + _canonical_record_bytes(provisional)
    ).hexdigest()
    if supplied != expected:
        raise ValueError(name + " record digest differs")
    return value


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_sha256(value: object, name: str) -> str:
    if not _is_sha256(value):
        raise TypeError(name + " must be exact lowercase SHA-256 text")
    return cast(str, value)


def _require_uint64_hex(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 16
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TypeError(name + " must be 16 lowercase hexadecimal digits")
    return value


def _require_integer(value: object, name: str, *, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value < minimum or value > maximum:
        raise ValueError(name + " lies outside the frozen range")
    return value


def _reject_duplicate_pairs(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("CP63 JSON contains duplicate keys")
        result[key] = value
    return result


def _validate_plain_json(value: object, *, depth: int = 0, budget: list = None) -> None:
    if budget is None:
        budget = [0]
    budget[0] += 1
    if depth > 64 or budget[0] > 262_144:
        raise ValueError("CP63 JSON exceeds the structural resource bound")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if value.bit_length() > 16_384:
            raise ValueError("CP63 JSON contains an oversized integer")
        return
    if type(value) is float:
        raise TypeError("CP63 JSON must not contain floating-point numbers")
    if type(value) is str:
        if len(value.encode("utf-8")) > 2_097_152:
            raise ValueError("CP63 JSON contains oversized text")
        return
    if type(value) is list:
        for item in value:
            _validate_plain_json(item, depth=depth + 1, budget=budget)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or not key or len(key.encode("utf-8")) > 4_096:
                raise TypeError("CP63 JSON contains an invalid object key")
            _validate_plain_json(item, depth=depth + 1, budget=budget)
        return
    raise TypeError("CP63 JSON contains a non-JSON value")


def _decode_canonical_json(payload: object, *, maximum: int, name: str) -> dict:
    if type(payload) is not bytes or not payload or len(payload) > maximum:
        raise ValueError(name + " has invalid byte length")
    if payload.startswith(b"\xef\xbb\xbf") or payload.rstrip() != payload:
        raise ValueError(name + " is not exact canonical JSON bytes")
    try:
        decoded = json.loads(
            payload.decode("ascii"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError("nonfinite JSON constant " + token)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError(name + " is not canonical JSON") from error
    if type(decoded) is not dict:
        raise TypeError(name + " must decode to an exact object")
    _validate_plain_json(decoded)
    try:
        encoded = _plain_json_bytes(decoded)
    except (TypeError, ValueError) as error:
        raise ValueError(name + " is not encodable canonical JSON") from error
    if encoded != payload:
        raise ValueError(name + " is not in canonical byte form")
    return decoded


def _seed_contract() -> CP63SeedCapsuleContractV1:
    return cast(
        CP63SeedCapsuleContractV1,
        _record(
            CP63SeedCapsuleContractV1,
            b"cp63-seed-capsule-contract-v1",
            {
                "schema_version": CP63_TEST28_SCHEMA_VERSION,
                "purpose": "future-production-external-iid-uniform-uint64-with-replacement",
                "cp61_stable_design_sha256": _CP61_STABLE_DESIGN_SHA256,
                "seed_count": 2_048,
                "seed_ordinals": tuple(range(1, 2_049)),
                "seed_encoding": "uint64-16-lowercase-hex-big-endian",
                "exact_json_keys": _SEED_CAPSULE_KEYS,
                "maximum_capsule_bytes": 131_072,
                "duplicate_values_retained": True,
                "order_is_semantic": True,
                "no_retry_drop_replacement_or_topup": True,
                "source_method_required": True,
                "source_receipt_required": True,
                "acquisition_session_required": True,
                "body_digest_required": True,
                "parser_can_verify_iid_uniform": False,
                "production_values_present": False,
            },
        ),
    )


def cp63_schedule_contract() -> CP63ScheduleContractV1:
    """Return the shard-neutral seed-major logical schedule."""

    return cast(
        CP63ScheduleContractV1,
        _record(
            CP63ScheduleContractV1,
            b"cp63-schedule-contract-v1",
            {
                "schema_version": CP63_TEST28_SCHEMA_VERSION,
                "seed_count": 2_048,
                "row_count": 16,
                "row_ordinals": tuple(range(1, 17)),
                "total_request_count": 32_768,
                "logical_request_ordinal_min": 1,
                "logical_request_ordinal_max": 32_768,
                "logical_request_order": "(seed_ordinal-1)*16+row_ordinal",
                "plan_seed_assignment": "external-seed-value-unchanged",
                "fixture_strategy_budget_or_shard_hashing_before_plan_seed_assignment": False,
                "duplicate_seed_values_distinguished_by_ordinal": True,
                "schedule_digest_formula": (
                    "SHA256(cp63-test28-logical-schedule-v1\\0+canonical(seed-"
                    "capsule-body-sha256,seed-count,row-count,logical-order))"
                ),
                "shard_mapping_bound": False,
                "production_schedule_instantiated": False,
            },
        ),
    )


def _rehearsal_cases() -> Tuple[CP63RehearsalCaseV1, ...]:
    return tuple(
        cast(
            CP63RehearsalCaseV1,
            _record(
                CP63RehearsalCaseV1,
                b"cp63-rehearsal-case-v1",
                {
                    "schema_version": CP63_TEST28_SCHEMA_VERSION,
                    "case_id": f"rehearsal-row-{row_ordinal:02d}",
                    "row_ordinal": row_ordinal,
                    "row_key": row_key,
                    "fixture_id": fixture_id,
                    "strategy": strategy,
                    "budget": budget,
                    "seed_hex": _REHEARSAL_SEED_HEX,
                    "seed_derivation": (
                        "first-eight-bytes-big-endian-of-sha256(cp63-test28-all-"
                        "row-rehearsal-seed-v1\\0)"
                    ),
                    "seed_is_external_source_draw": False,
                    "seed_is_future_capsule_member": False,
                    "requested_repetitions": 2,
                    "maximum_child_launches": 2,
                    "production_observation": False,
                },
            ),
        )
        for row_ordinal, row_key, fixture_id, strategy, budget, _seed_free in _ROW_INVENTORY
    )


def _lifecycle_contract() -> CP63LifecycleContractV1:
    return cast(
        CP63LifecycleContractV1,
        _record(
            CP63LifecycleContractV1,
            b"cp63-lifecycle-contract-v1",
            {
                "schema_version": CP63_TEST28_SCHEMA_VERSION,
                "lifecycle_id": "cp63-development-rehearsal-lifecycle-v1",
                "allowed_states": (
                    "DEFINED",
                    "REHEARSAL_STARTED",
                    "REHEARSAL_PASS",
                    "REHEARSAL_FAIL",
                    "REHEARSAL_INVALID_INFRA",
                ),
                "initial_state": "DEFINED",
                "terminal_states": (
                    "REHEARSAL_PASS",
                    "REHEARSAL_FAIL",
                    "REHEARSAL_INVALID_INFRA",
                ),
                "no_retry_drop_replacement_or_topup": True,
                "infrastructure_failure_invalidates_entire_attempt": True,
                "timeout_is_semantic_nonreturn": False,
                "attempt_spent_after_durable_stochastic_output": True,
                "confirmatory_states_enterable": False,
                "filesystem_mutation_permitted": False,
                "production_lifecycle_instantiated": False,
            },
        ),
    )


def _raw_record_schema() -> CP63RawRecordSchemaV1:
    return cast(
        CP63RawRecordSchemaV1,
        _record(
            CP63RawRecordSchemaV1,
            b"cp63-raw-record-schema-v1",
            {
                "schema_version": CP63_TEST28_SCHEMA_VERSION,
                "purpose": "development-runner-rehearsal-only",
                "exact_outer_keys": _RAW_OUTER_KEYS,
                "child_frame_encoding": (
                    "one-uint64-big-endian-length-prefixed-canonical-json-frame"
                ),
                "public_raw_record_encoding": "unframed-canonical-json-object-bytes",
                "uint64_encoding": "16-lowercase-hex-big-endian",
                "float64_encoding": "tagged-8-byte-big-endian-hex",
                "fraction_encoding": (
                    "tagged-canonical-signed-numerator-positive-denominator-decimal"
                ),
                "bytes_encoding": "bounded-lowercase-hex",
                "four_closed_outcome_arms": _PHASE_ARMS,
                "preexecution_refusal_codes": _PREEXECUTION_REFUSAL_CODES,
                "execution_failure_codes": _EXECUTION_FAILURE_CODES,
                "complete_kernel_trace_required_for_validated_returns": True,
                "volatile_supervisor_custody_retained": True,
                "recompute_owned_semantic_leaf_hashes": True,
                "future_production_shape_predeclared": True,
                "infrastructure_failure_has_raw_record": False,
                "raw_trace_retained_separately": True,
                "production_schema_frozen": False,
                "production_records_observed": False,
                "raw_frame_max_bytes": 16_777_216,
            },
        ),
    )


def _resource_contract() -> CP63RunnerResourceContractV1:
    return cast(
        CP63RunnerResourceContractV1,
        _record(
            CP63RunnerResourceContractV1,
            b"cp63-runner-resource-contract-v1",
            {
                "schema_version": CP63_TEST28_SCHEMA_VERSION,
                "seed_capsule_max_bytes": 131_072,
                "request_frame_max_bytes": 65_536,
                "raw_frame_max_bytes": 16_777_216,
                "stable_trace_max_bytes": 8_388_608,
                "stderr_max_bytes": 1_048_576,
                "deadline_seconds": 300,
                "termination_grace_seconds": 2,
                "reap_ceiling_seconds": 5,
                "rehearsal_concurrency": 1,
                "rehearsal_launch_limit": 32,
                "external_seed_count": 2_048,
                "row_count": 16,
                "total_request_count": 32_768,
                "rejection_proposal_slot_count": 348_160,
                "sir_proposal_slot_count": 2_785_280,
                "total_proposal_slot_count": 3_133_440,
                "sir_resampling_draw_count": 16_384,
                "maximum_event_occurrence_count": 4_700_160,
                "maximum_coordinate_count": 7_833_600,
                "maximum_future_raw_aggregate_bytes": 549_755_813_888,
                "maximum_future_stable_aggregate_bytes": 274_877_906_944,
                "capacity_receipt_present": False,
                "production_resources_allocated": False,
            },
        ),
    )


def cp63_runner_recomputation_rehearsal_bundle() -> CP63RunnerRecomputationRehearsalBundleV1:
    """Return the zero-execution CP63 runner rehearsal definition."""

    return cast(
        CP63RunnerRecomputationRehearsalBundleV1,
        _record(
            CP63RunnerRecomputationRehearsalBundleV1,
            b"cp63-runner-recomputation-rehearsal-bundle-v1",
            {
                "schema_version": CP63_TEST28_SCHEMA_VERSION,
                "scope": CP63_TEST28_SCOPE,
                "cp62_source_sha256": _CP62_SOURCE_SHA256,
                "cp62_bundle_sha256": _CP62_BUNDLE_SHA256,
                "cp62_semantic_sha256": _CP62_SEMANTIC_SHA256,
                "seed_capsule_contract": _seed_contract(),
                "schedule_contract": cp63_schedule_contract(),
                "lifecycle_contract": _lifecycle_contract(),
                "raw_record_schema": _raw_record_schema(),
                "resource_contract": _resource_contract(),
                "rehearsal_cases": _rehearsal_cases(),
                "seed_capsule_parser_exposed": True,
                "seed_capsule_syntax_only": True,
                "production_seed_ingest_for_execution": False,
                "arbitrary_seed_execution": False,
                "campaign_loop_exposed": False,
                "durable_attempt_writer": False,
                "shard_mapping_bound": False,
                "capacity_receipt_present": False,
                "rehearsal_all_rows_executed": False,
                "closed_refusal_failure_classification_implemented": False,
                "full_32768_recomputation_exposed": False,
                "estimates_computed": False,
                "intervals_computed": False,
                "decision_made": False,
                "production_schema_frozen": False,
                "production_runner_bound": False,
                "runner_and_recomputation_blocker_closed": False,
                "formal_test_28_closed": False,
            },
        ),
    )


def cp63_validate_seed_capsule_bytes(payload: object) -> CP63SeedCapsuleObservationV1:
    """Validate one bounded capsule without authenticating its source law."""

    checked = _decode_canonical_json(payload, maximum=131_072, name="CP63 seed capsule")
    if tuple(checked) != tuple(sorted(checked)):
        # Canonical bytes already prove sorted serialization.  This branch is
        # retained as an explicit object-order custody assertion.
        raise ValueError("CP63 seed capsule object order differs")
    if set(checked) != set(_SEED_CAPSULE_KEYS) or len(checked) != len(
        _SEED_CAPSULE_KEYS
    ):
        raise ValueError("CP63 seed capsule field set differs")
    exact = {
        "schema": CP63_TEST28_SCHEMA_VERSION,
        "purpose": "future-production-external-iid-uniform-uint64-with-replacement",
        "cp61_stable_design_sha256": _CP61_STABLE_DESIGN_SHA256,
        "seed_count": 2_048,
        "seed_encoding": "uint64-16-lowercase-hex-big-endian",
    }
    for key, expected in exact.items():
        if type(checked[key]) is not type(expected) or checked[key] != expected:
            raise ValueError("CP63 seed capsule " + key + " differs")
    ordinals = checked["seed_ordinals"]
    values = checked["ordered_seed_values"]
    if (
        type(ordinals) is not list
        or len(ordinals) != 2_048
        or any(type(value) is not int for value in ordinals)
        or ordinals != list(range(1, 2_049))
    ):
        raise ValueError("CP63 seed ordinals differ from the exact range")
    if type(values) is not list or len(values) != 2_048:
        raise ValueError("CP63 ordered seed values differ in length")
    seed_values = tuple(
        _require_uint64_hex(value, "CP63 seed value") for value in values
    )
    source_method_id = checked["source_method_id"]
    if (
        type(source_method_id) is not str
        or not source_method_id
        or len(source_method_id.encode("utf-8")) > 4_096
    ):
        raise TypeError("CP63 source method id must be bounded nonempty text")
    source_receipt = _require_sha256(
        checked["source_receipt_sha256"], "CP63 source receipt"
    )
    acquisition = _require_sha256(
        checked["acquisition_session_sha256"], "CP63 acquisition session"
    )
    supplied_body_sha256 = _require_sha256(
        checked["body_sha256"], "CP63 seed capsule body"
    )
    digest_body = dict(checked)
    digest_body["body_sha256"] = _ZERO_SHA256
    expected_body_sha256 = hashlib.sha256(
        b"cp63-test28-seed-capsule-v1\0" + _plain_json_bytes(digest_body)
    ).hexdigest()
    if supplied_body_sha256 != expected_body_sha256:
        raise ValueError("CP63 seed capsule body digest differs")
    return cast(
        CP63SeedCapsuleObservationV1,
        _record(
            CP63SeedCapsuleObservationV1,
            b"cp63-seed-capsule-observation-v1",
            {
                "schema": CP63_TEST28_SCHEMA_VERSION,
                "purpose": exact["purpose"],
                "cp61_stable_design_sha256": _CP61_STABLE_DESIGN_SHA256,
                "seed_count": 2_048,
                "seed_ordinals": tuple(range(1, 2_049)),
                "seed_encoding": exact["seed_encoding"],
                "ordered_seed_values": seed_values,
                "source_method_id": source_method_id,
                "source_receipt_sha256": source_receipt,
                "acquisition_session_sha256": acquisition,
                "body_sha256": supplied_body_sha256,
                "canonical_byte_count": len(cast(bytes, payload)),
                "syntactically_valid": True,
                "source_custody_digest_bound": True,
                "iid_uniform_with_replacement_verified": False,
                "production_execution_authorized": False,
            },
        ),
    )


def cp63_seed_capsule_canonical_json_bytes(record: object) -> bytes:
    observed = cast(
        CP63SeedCapsuleObservationV1,
        _validate_record(
            record,
            CP63SeedCapsuleObservationV1,
            b"cp63-seed-capsule-observation-v1",
            "seed capsule observation",
        ),
    )
    if (
        observed.schema != CP63_TEST28_SCHEMA_VERSION
        or observed.purpose
        != "future-production-external-iid-uniform-uint64-with-replacement"
        or observed.cp61_stable_design_sha256 != _CP61_STABLE_DESIGN_SHA256
        or observed.seed_count != 2_048
        or observed.seed_ordinals != tuple(range(1, 2_049))
        or observed.seed_encoding != "uint64-16-lowercase-hex-big-endian"
        or len(observed.ordered_seed_values) != 2_048
        or not observed.syntactically_valid
        or not observed.source_custody_digest_bound
        or observed.iid_uniform_with_replacement_verified
        or observed.production_execution_authorized
    ):
        raise ValueError("seed capsule observation differs from the frozen contract")
    values = {
        "schema": observed.schema,
        "purpose": observed.purpose,
        "cp61_stable_design_sha256": observed.cp61_stable_design_sha256,
        "seed_count": observed.seed_count,
        "seed_ordinals": list(observed.seed_ordinals),
        "seed_encoding": observed.seed_encoding,
        "ordered_seed_values": list(observed.ordered_seed_values),
        "source_method_id": observed.source_method_id,
        "source_receipt_sha256": observed.source_receipt_sha256,
        "acquisition_session_sha256": observed.acquisition_session_sha256,
        "body_sha256": observed.body_sha256,
    }
    encoded = _plain_json_bytes(values)
    if len(encoded) != observed.canonical_byte_count:
        raise ValueError("seed capsule canonical byte count differs")
    reparsed = cp63_validate_seed_capsule_bytes(encoded)
    if reparsed.record_sha256 != observed.record_sha256:
        raise ValueError("seed capsule observation does not replay")
    return encoded


def cp63_bound_request(
    seed_capsule: object, logical_request_ordinal: object
) -> CP63BoundRequestV1:
    observed = cast(
        CP63SeedCapsuleObservationV1,
        _validate_record(
            seed_capsule,
            CP63SeedCapsuleObservationV1,
            b"cp63-seed-capsule-observation-v1",
            "seed capsule observation",
        ),
    )
    cp63_seed_capsule_canonical_json_bytes(observed)
    logical = _require_integer(
        logical_request_ordinal,
        "logical request ordinal",
        minimum=1,
        maximum=32_768,
    )
    seed_ordinal = (logical - 1) // 16 + 1
    row_ordinal = (logical - 1) % 16 + 1
    row = _ROW_INVENTORY[row_ordinal - 1]
    (_ordinal, row_key, fixture_id, strategy, budget, seed_free_sha256) = row
    if _ordinal != row_ordinal:
        raise RuntimeError("CP63 row inventory is noncanonical")
    identity = {
        "schema_version": CP63_TEST28_SCHEMA_VERSION,
        "seed_capsule_body_sha256": observed.body_sha256,
        "seed_ordinal": seed_ordinal,
        "row_ordinal": row_ordinal,
        "logical_request_ordinal": logical,
        "row_key": row_key,
        "fixture_id": fixture_id,
        "strategy": strategy,
        "budget": budget,
        "plan_seed_hex": observed.ordered_seed_values[seed_ordinal - 1],
        "seed_free_request_sha256": seed_free_sha256,
        "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
    }
    identity["request_instance_sha256"] = hashlib.sha256(
        b"cp63-test28-bound-request-v1\0" + _plain_json_bytes(identity)
    ).hexdigest()
    identity["definition_only"] = True
    identity["production_execution_authorized"] = False
    return cast(
        CP63BoundRequestV1,
        _record(
            CP63BoundRequestV1,
            b"cp63-bound-request-record-v1",
            identity,
        ),
    )


def _cp62_module() -> object:
    from heterodiff.evaluation import (
        mixed_initializer_test28_execution_capsule as cp62,
    )

    path = Path(cast(str, cp62.__file__))
    if hashlib.sha256(path.read_bytes()).hexdigest() != _CP62_SOURCE_SHA256:
        raise CP63RunnerRehearsalError(
            "CP62_SOURCE_CUSTODY_MISMATCH", "the bound CP62 source bytes differ"
        )
    bundle = cp62.cp62_execution_capsule_bundle()
    if (
        bundle.record_sha256 != _CP62_BUNDLE_SHA256
        or bundle.semantic_sha256 != _CP62_SEMANTIC_SHA256
        or bundle.runtime_source_abi_lock.record_sha256 != _RUNTIME_LOCK_SHA256
    ):
        raise CP63RunnerRehearsalError(
            "CP62_BUNDLE_CUSTODY_MISMATCH", "the bound CP62 bundle differs"
        )
    return cp62


def _case_by_id(case_id: object) -> CP63RehearsalCaseV1:
    if type(case_id) is not str or not case_id:
        raise TypeError("rehearsal case id must be exact nonempty text")
    for case in _rehearsal_cases():
        if case.case_id == case_id:
            return case
    raise ValueError("only the sixteen frozen CP63 rehearsal cases are executable")


def _case_and_row(case_id: object) -> Tuple[CP63RehearsalCaseV1, object]:
    case = _case_by_id(case_id)
    cp62 = _cp62_module()
    row = cp62.cp62_execution_capsule_bundle().request_bindings[case.row_ordinal - 1]
    expected = _ROW_INVENTORY[case.row_ordinal - 1]
    if (
        row.row_ordinal,
        row.row_key,
        row.fixture_id,
        row.strategy,
        row.budget,
        row.seed_free_request_sha256,
    ) != expected:
        raise CP63RunnerRehearsalError(
            "CP62_ROW_CUSTODY_MISMATCH", "the bound CP62 request row differs"
        )
    return case, row


def _case_view(case: CP63RehearsalCaseV1) -> object:
    return SimpleNamespace(
        case_id=case.case_id,
        row_ordinal=case.row_ordinal,
        fixture_id=case.fixture_id,
        strategy=case.strategy,
        budget=case.budget,
        seed_uint64=int(case.seed_hex, 16),
        seed_hex=case.seed_hex,
    )


def _rehearsal_request_instance_sha256(case: CP63RehearsalCaseV1, row: object) -> str:
    identity = {
        "schema": CP63_TEST28_SCHEMA_VERSION,
        "rehearsal_id": _REHEARSAL_ID,
        "seed_ordinal": 1,
        "row_ordinal": case.row_ordinal,
        "logical_request_ordinal": case.row_ordinal,
        "row_key": case.row_key,
        "fixture_id": case.fixture_id,
        "strategy": case.strategy,
        "budget": case.budget,
        "plan_seed_hex": case.seed_hex,
        "seed_free_request_sha256": getattr(row, "seed_free_request_sha256"),
        "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
    }
    return hashlib.sha256(
        b"cp63-test28-rehearsal-request-instance-v1\0" + _plain_json_bytes(identity)
    ).hexdigest()


def _validate_exact_outer_identity(
    value: Mapping[str, object], case: CP63RehearsalCaseV1, row: object
) -> None:
    expected = {
        "schema": CP63_TEST28_SCHEMA_VERSION,
        "purpose": "development-runner-rehearsal-only",
        "rehearsal_id": _REHEARSAL_ID,
        "seed_ordinal": 1,
        "row_ordinal": case.row_ordinal,
        "logical_request_ordinal": case.row_ordinal,
        "row_key": case.row_key,
        "fixture_id": case.fixture_id,
        "strategy": case.strategy,
        "budget": case.budget,
        "plan_seed_hex": case.seed_hex,
        "seed_free_request_sha256": getattr(row, "seed_free_request_sha256"),
        "request_instance_sha256": _rehearsal_request_instance_sha256(case, row),
        "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
    }
    for field_name, wanted in expected.items():
        actual = value.get(field_name)
        if type(actual) is not type(wanted) or actual != wanted:
            raise ValueError("CP63 record " + field_name + " differs")


def _validate_clean_child_completion(raw: dict, supervisor: dict) -> None:
    if (
        supervisor["process_group"] != supervisor["pid"]
        or supervisor["exit_code"] != 0
        or supervisor["term_signal"] is not None
        or not supervisor["completion_strictly_before_deadline"]
        or not supervisor["exact_one_frame"]
        or supervisor["termination_attempted"]
        or supervisor["termination_signal_delivered"]
        or supervisor["kill_attempted"]
        or not supervisor["reaped"]
        or int(supervisor["terminal_monotonic_ns"])
        >= int(supervisor["deadline_monotonic_ns"])
    ):
        raise ValueError("CP63 supervisor custody is not a clean timely completion")
    child_payload = {
        key: raw[key]
        for key in _RAW_OUTER_KEYS
        if key not in ("supervisor_custody", "raw_sha256")
    }
    encoded = _plain_json_bytes(child_payload)
    frame = len(encoded).to_bytes(8, "big") + encoded
    if (
        supervisor["frame_bytes"] != len(frame)
        or supervisor["child_frame_sha256"] != hashlib.sha256(frame).hexdigest()
    ):
        raise ValueError("CP63 child frame custody differs")


def _execute_rehearsal_case_locally(case_id: str, repetition: int) -> dict:
    case, row = _case_and_row(case_id)
    _require_integer(repetition, "rehearsal repetition", minimum=1, maximum=2)
    cp62 = _cp62_module()

    from heterodiff.evaluation import exact_rational_quadratic_initial_tilt as exact
    from heterodiff.processes import certified_initial_score_provider_v1 as facade
    from heterodiff.processes import (
        plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 as kernel_v2,
    )

    observation = cp62._runtime_observation()
    source_factory = (
        exact.build_t28_m1_q_exact_score_provider
        if case.fixture_id == "T28-M1-Q"
        else exact.build_t28_m2_q_exact_score_provider
    )
    source = source_factory()
    if (
        source.certificate.fixture_id != row.fixture_id
        or source.certificate.certificate_sha256 != row.source_certificate_sha256
    ):
        raise CP63RunnerRehearsalError(
            "SOURCE_BINDING_MISMATCH", "the exact score source differs"
        )
    provider = facade.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
        source, adapter_role_sha256=row.adapter_role_sha256
    )
    provider_certificate = provider.certificate
    expected_provider = {
        "adapter_role_sha256": row.adapter_role_sha256,
        "source_certificate_sha256": row.source_certificate_sha256,
        "source_parameter_sha256": row.source_parameter_sha256,
        "reference_parameter_sha256": row.reference_parameter_sha256,
        "certificate_sha256": row.facade_certificate_sha256,
    }
    if any(
        getattr(provider_certificate, name) != wanted
        for name, wanted in expected_provider.items()
    ):
        raise CP63RunnerRehearsalError(
            "FACADE_BINDING_MISMATCH", "the certified facade differs"
        )
    seed = int(case.seed_hex, 16)
    plan = kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy=row.strategy,
        residual_context=row.residual_context,
        initializer_role_sha256=row.initializer_role_sha256,
        seed=seed,
        budget=row.budget,
        ess_warning_fraction=(0.25 if row.strategy == "fixed-budget-sir" else None),
    )
    if (
        plan.residual_context_sha256 != row.residual_context_sha256
        or plan.initializer_role_sha256 != row.initializer_role_sha256
        or plan.strategy != row.strategy
        or plan.seed != seed
        or plan.budget != row.budget
        or plan.adaptive_fallback_permitted
        or (
            row.strategy == "fixed-budget-sir"
            and struct.pack(">d", plan.ess_warning_fraction).hex()
            != row.sir_ess_warning_fraction_float64_be
        )
        or (
            row.strategy == "bounded-rejection"
            and plan.ess_warning_fraction is not None
        )
    ):
        raise CP63RunnerRehearsalError(
            "PLAN_BINDING_MISMATCH", "the rehearsal plan differs"
        )
    owner = kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        provider, plan=plan
    )
    result = owner.execute()
    if owner.validate_result(result) is not result:
        raise CP63RunnerRehearsalError(
            "RESULT_VALIDATION_IDENTITY_MISMATCH",
            "kernel validation returned another object",
        )
    if row.strategy == "bounded-rejection":
        if result.status == "selected":
            closed_status = "returned-rejection-selected-before-deadline"
        elif result.status == "exhausted":
            closed_status = "returned-rejection-exhausted-before-deadline"
        else:
            raise CP63RunnerRehearsalError(
                "UNKNOWN_REJECTION_STATUS", "the rejection status is unknown"
            )
    else:
        if result.status != "selected":
            raise CP63RunnerRehearsalError(
                "UNKNOWN_SIR_STATUS", "the SIR status is unknown"
            )
        closed_status = "returned-sir-selected-before-deadline"
    case_view = _case_view(case)
    semantic = cp62._kernel_semantic_trace(case_view, row, owner, result)
    if semantic["runtime_observation"] != observation:
        raise CP63RunnerRehearsalError(
            "RUNTIME_OBSERVATION_CHANGED",
            "the runtime observation changed during execution",
        )
    payload = {
        "schema": CP63_TEST28_SCHEMA_VERSION,
        "purpose": "development-runner-rehearsal-only",
        "rehearsal_id": _REHEARSAL_ID,
        "repetition": repetition,
        "seed_ordinal": 1,
        "row_ordinal": case.row_ordinal,
        "logical_request_ordinal": case.row_ordinal,
        "row_key": case.row_key,
        "fixture_id": case.fixture_id,
        "strategy": case.strategy,
        "budget": case.budget,
        "plan_seed_hex": case.seed_hex,
        "seed_free_request_sha256": row.seed_free_request_sha256,
        "request_instance_sha256": _rehearsal_request_instance_sha256(case, row),
        "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
        "phase": "returned-before-deadline",
        "closed_status": closed_status,
        "failure_code": None,
        "kernel_trace": {
            "semantic": semantic,
            "volatile_custody": cp62._kernel_volatile_custody(owner, result),
        },
    }
    _validate_child_payload(payload)
    return payload


_CHILD_PAYLOAD_KEYS = tuple(
    key for key in _RAW_OUTER_KEYS if key not in ("supervisor_custody", "raw_sha256")
)


def _validate_returned_volatile_pattern(
    volatile: dict, *, strategy: str, budget: int, name: str
) -> None:
    nested = volatile["nested_record_custody"]
    expected_kind = (
        "rejection-attempt" if strategy == "bounded-rejection" else "sir-particle"
    )
    if len(nested) != budget or any(
        item["slot_kind"] != expected_kind for item in nested
    ):
        raise ValueError(name + " nested volatile custody differs")
    if any(
        item[field] is None
        for item in nested
        for field in (
            "configuration_sha256",
            "source_evaluation_sha256",
            "facade_evaluation_sha256",
            "scored_sha256",
        )
    ):
        raise ValueError(name + " common nested volatile custody is incomplete")
    if strategy == "bounded-rejection":
        if any(
            item["quota_sha256"] is None
            or item["attempt_sha256"] is None
            or item["particle_sha256"] is not None
            for item in nested
        ):
            raise ValueError(name + " rejection nested volatile custody differs")
    elif any(
        item["quota_sha256"] is not None
        or item["attempt_sha256"] is not None
        or item["particle_sha256"] is None
        for item in nested
    ):
        raise ValueError(name + " SIR nested volatile custody differs")


def _validate_child_payload(value: object) -> dict:
    if (
        type(value) is not dict
        or set(value) != set(_CHILD_PAYLOAD_KEYS)
        or len(value) != len(_CHILD_PAYLOAD_KEYS)
    ):
        raise ValueError("CP63 child payload field set differs")
    row_ordinal = _require_integer(
        value["row_ordinal"], "child row ordinal", minimum=1, maximum=16
    )
    case, row = _case_and_row(f"rehearsal-row-{row_ordinal:02d}")
    _validate_exact_outer_identity(value, case, row)
    _require_integer(value["repetition"], "child repetition", minimum=1, maximum=2)
    cp62 = _cp62_module()
    kernel_trace = cp62._exact_keys(
        value["kernel_trace"], cp62._KERNEL_TRACE_KEYS, "CP63 child kernel trace"
    )
    phase = value["phase"]
    case_view = _case_view(case)
    if phase == "returned-before-deadline":
        if (
            type(value["closed_status"]) is not str
            or value["closed_status"]
            not in cp62._RETURNED_STATUS_BY_STRATEGY[case.strategy]
            or value["failure_code"] is not None
        ):
            raise ValueError("CP63 child returned status differs")
        cp62._validate_semantic_trace(
            kernel_trace["semantic"],
            case=case_view,
            row=row,
            closed_status=value["closed_status"],
        )
        volatile = cp62._validate_volatile_custody(kernel_trace["volatile_custody"])
        _validate_returned_volatile_pattern(
            volatile,
            strategy=case.strategy,
            budget=case.budget,
            name="CP63 child",
        )
    elif phase in (
        "preexecution-refusal-before-deadline",
        "execution-failure-before-deadline",
    ):
        refusal = phase == "preexecution-refusal-before-deadline"
        codes = _PREEXECUTION_REFUSAL_CODES if refusal else _EXECUTION_FAILURE_CODES
        if (
            value["closed_status"] != phase
            or value["failure_code"] not in codes
            or kernel_trace["volatile_custody"] is not None
        ):
            raise ValueError("CP63 child closed outcome differs")
        cp62._validate_closed_semantic_trace(
            kernel_trace["semantic"],
            case=case_view,
            row=row,
            outcome_kind="preexecution-refusal" if refusal else "execution-failure",
            failure_code=value["failure_code"],
        )
    else:
        raise ValueError("CP63 child payload phase differs")
    return value


def cp63_validate_raw_record_bytes(payload: object) -> dict:
    value = _decode_canonical_json(payload, maximum=16_777_216, name="CP63 raw record")
    if set(value) != set(_RAW_OUTER_KEYS) or len(value) != len(_RAW_OUTER_KEYS):
        raise ValueError("CP63 raw record field set differs")
    supplied = _require_sha256(value["raw_sha256"], "CP63 raw record")
    body = dict(value)
    body["raw_sha256"] = _ZERO_SHA256
    expected_digest = hashlib.sha256(
        b"cp63-test28-raw-record-v1\0" + _plain_json_bytes(body)
    ).hexdigest()
    if supplied != expected_digest:
        raise ValueError("CP63 raw record digest differs")
    row_ordinal = _require_integer(
        value["row_ordinal"], "CP63 row ordinal", minimum=1, maximum=16
    )
    case, row = _case_and_row(f"rehearsal-row-{row_ordinal:02d}")
    _validate_exact_outer_identity(value, case, row)
    _require_integer(value["repetition"], "CP63 repetition", minimum=1, maximum=2)
    cp62 = _cp62_module()
    kernel_trace = cp62._exact_keys(
        value["kernel_trace"], cp62._KERNEL_TRACE_KEYS, "CP63 raw kernel trace"
    )
    supervisor = cp62._validate_supervisor_custody(value["supervisor_custody"])
    phase = value["phase"]
    closed_status = value["closed_status"]
    failure_code = value["failure_code"]
    case_view = _case_view(case)
    if phase == "returned-before-deadline":
        allowed = cp62._RETURNED_STATUS_BY_STRATEGY[case.strategy]
        if (
            type(closed_status) is not str
            or closed_status not in allowed
            or failure_code is not None
        ):
            raise ValueError("CP63 returned status differs from strategy")
        semantic = cp62._validate_semantic_trace(
            kernel_trace["semantic"],
            case=case_view,
            row=row,
            closed_status=closed_status,
        )
        volatile = cp62._validate_volatile_custody(kernel_trace["volatile_custody"])
        _validate_returned_volatile_pattern(
            volatile,
            strategy=case.strategy,
            budget=case.budget,
            name="CP63 raw",
        )
        if semantic["strategy"] != case.strategy:
            raise ValueError("CP63 semantic strategy differs")
        _validate_clean_child_completion(value, supervisor)
    elif phase in (
        "preexecution-refusal-before-deadline",
        "execution-failure-before-deadline",
    ):
        refusal = phase == "preexecution-refusal-before-deadline"
        codes = _PREEXECUTION_REFUSAL_CODES if refusal else _EXECUTION_FAILURE_CODES
        outcome_kind = "preexecution-refusal" if refusal else "execution-failure"
        if (
            closed_status != phase
            or type(failure_code) is not str
            or failure_code not in codes
            or kernel_trace["volatile_custody"] is not None
        ):
            raise ValueError("CP63 closed refusal/failure record differs")
        cp62._validate_closed_semantic_trace(
            kernel_trace["semantic"],
            case=case_view,
            row=row,
            outcome_kind=outcome_kind,
            failure_code=failure_code,
        )
        _validate_clean_child_completion(value, supervisor)
    elif phase == "timeout-at-deadline":
        if (
            closed_status != "timeout-censored-at-deadline"
            or failure_code is not None
            or kernel_trace["volatile_custody"] is not None
        ):
            raise ValueError("CP63 timeout record differs")
        cp62._validate_closed_semantic_trace(
            kernel_trace["semantic"],
            case=case_view,
            row=row,
            outcome_kind="timeout-censored",
            failure_code=None,
        )
        if (
            supervisor["process_group"] != supervisor["pid"]
            or supervisor["completion_strictly_before_deadline"]
            or supervisor["exact_one_frame"]
            or not supervisor["reaped"]
            or int(supervisor["terminal_monotonic_ns"])
            < int(supervisor["deadline_monotonic_ns"])
        ):
            raise ValueError("CP63 timeout supervisor custody differs")
        cp62._require_timeout_terminal_fields(
            supervisor["exit_code"], supervisor["term_signal"]
        )
        if (
            supervisor["termination_signal_delivered"]
            and not supervisor["termination_attempted"]
        ):
            raise ValueError("CP63 termination delivery lacks an attempt")
        if (
            supervisor["term_signal"] == signal.SIGTERM
            and not supervisor["termination_signal_delivered"]
        ):
            raise ValueError("CP63 SIGTERM timeout lacks delivery custody")
        if (
            supervisor["term_signal"] == signal.SIGKILL
            and not supervisor["kill_attempted"]
        ):
            raise ValueError("CP63 SIGKILL timeout lacks kill custody")
        if supervisor["kill_attempted"] and not supervisor["termination_attempted"]:
            raise ValueError("CP63 kill custody lacks a termination attempt")
    else:
        raise ValueError("CP63 raw record phase is not a frozen arm")
    return value


def cp63_project_stable_trace(raw_record: object) -> dict:
    if type(raw_record) is bytes:
        raw = cp63_validate_raw_record_bytes(raw_record)
    elif type(raw_record) is dict:
        raw = cp63_validate_raw_record_bytes(_plain_json_bytes(raw_record))
    else:
        raise TypeError("CP63 stable projection requires raw bytes or an exact object")
    stable = {
        key: raw[key]
        for key in _RAW_OUTER_KEYS
        if key not in ("repetition", "supervisor_custody", "raw_sha256")
    }
    stable["kernel_trace"] = raw["kernel_trace"]["semantic"]
    _validate_stable_trace(stable)
    return stable


_STABLE_KEYS = tuple(
    key
    for key in _RAW_OUTER_KEYS
    if key not in ("repetition", "supervisor_custody", "raw_sha256")
)


def _validate_stable_trace(trace: object) -> dict:
    if (
        type(trace) is not dict
        or set(trace) != set(_STABLE_KEYS)
        or len(trace) != len(_STABLE_KEYS)
    ):
        raise ValueError("CP63 stable trace field set differs")
    row_ordinal = _require_integer(
        trace["row_ordinal"], "CP63 stable row ordinal", minimum=1, maximum=16
    )
    case, row = _case_and_row(f"rehearsal-row-{row_ordinal:02d}")
    _validate_exact_outer_identity(trace, case, row)
    cp62 = _cp62_module()
    case_view = _case_view(case)
    phase = trace["phase"]
    closed_status = trace["closed_status"]
    failure_code = trace["failure_code"]
    if phase == "returned-before-deadline":
        if (
            type(closed_status) is not str
            or closed_status not in cp62._RETURNED_STATUS_BY_STRATEGY[case.strategy]
            or failure_code is not None
        ):
            raise ValueError("CP63 stable returned outcome differs")
        cp62._validate_semantic_trace(
            trace["kernel_trace"],
            case=case_view,
            row=row,
            closed_status=closed_status,
        )
    elif phase in (
        "preexecution-refusal-before-deadline",
        "execution-failure-before-deadline",
    ):
        refusal = phase == "preexecution-refusal-before-deadline"
        codes = _PREEXECUTION_REFUSAL_CODES if refusal else _EXECUTION_FAILURE_CODES
        if (
            closed_status != phase
            or type(failure_code) is not str
            or failure_code not in codes
        ):
            raise ValueError("CP63 stable refusal/failure outcome differs")
        cp62._validate_closed_semantic_trace(
            trace["kernel_trace"],
            case=case_view,
            row=row,
            outcome_kind="preexecution-refusal" if refusal else "execution-failure",
            failure_code=failure_code,
        )
    elif phase == "timeout-at-deadline":
        if closed_status != "timeout-censored-at-deadline" or failure_code is not None:
            raise ValueError("CP63 stable timeout outcome differs")
        cp62._validate_closed_semantic_trace(
            trace["kernel_trace"],
            case=case_view,
            row=row,
            outcome_kind="timeout-censored",
            failure_code=None,
        )
    else:
        raise ValueError("CP63 stable phase is not a frozen arm")
    encoded = _plain_json_bytes(trace)
    if len(encoded) > 8_388_608:
        raise ValueError("CP63 stable trace exceeds its byte ceiling")
    return trace


def cp63_stable_trace_canonical_json_bytes(trace: object) -> bytes:
    checked = _validate_stable_trace(trace)
    encoded = _plain_json_bytes(checked)
    if len(encoded) > 8_388_608:
        raise ValueError("CP63 stable trace exceeds its byte ceiling")
    return encoded


def cp63_stable_trace_sha256(trace: object) -> str:
    return hashlib.sha256(
        b"cp63-test28-stable-trace-v1\0" + cp63_stable_trace_canonical_json_bytes(trace)
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                return digest.hexdigest()
            digest.update(block)


def _write_all(file_descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    offset = 0
    while offset < len(view):
        written = os.write(file_descriptor, view[offset:])
        if written <= 0:
            raise CP63RunnerRehearsalError(
                "CHILD_FRAME_WRITE_FAILURE", "child frame write made no progress"
            )
        offset += written


def _child_nonce(case_id: str, repetition: int, start_ns: int, launch: int) -> str:
    return hashlib.sha256(
        _CHILD_NONCE_DOMAIN
        + case_id.encode("ascii")
        + b"\0"
        + repetition.to_bytes(1, "big")
        + start_ns.to_bytes(8, "big")
        + os.getpid().to_bytes(8, "big")
        + launch.to_bytes(8, "big")
    ).hexdigest()


def _child_auth(case_id: str, repetition: int, nonce: str, source_sha256: str) -> str:
    return hashlib.sha256(
        _CHILD_AUTH_DOMAIN
        + case_id.encode("ascii")
        + b"\0"
        + repetition.to_bytes(1, "big")
        + bytes.fromhex(nonce)
        + bytes.fromhex(source_sha256)
    ).hexdigest()


def _rehearsal_child_main(arguments: Tuple[str, ...]) -> int:
    if len(arguments) != 6 or arguments[0] != "--cp63-rehearsal-child":
        return 64
    case_id, repetition_text, nonce, source_sha256, supplied_auth = arguments[1:]
    try:
        case = _case_by_id(case_id)
        if repetition_text not in ("1", "2"):
            raise ValueError("rehearsal repetition is noncanonical")
        repetition = int(repetition_text)
        _require_sha256(nonce, "child nonce")
        _require_sha256(source_sha256, "child source digest")
        _require_sha256(supplied_auth, "child authorization")
        if supplied_auth != _child_auth(case.case_id, repetition, nonce, source_sha256):
            raise ValueError("child authorization differs")
        if _file_sha256(Path(__file__).resolve()) != source_sha256:
            raise CP63RunnerRehearsalError(
                "CHILD_SOURCE_CUSTODY_MISMATCH", "CP63 child source bytes differ"
            )
        if tuple(sorted(os.environ.items())) != tuple(
            sorted(_SANITIZED_CHILD_ENVIRONMENT)
        ):
            raise CP63RunnerRehearsalError(
                "CHILD_ENVIRONMENT_MISMATCH", "child environment differs"
            )
        source_root = Path(__file__).resolve().parents[2]
        workspace_root = source_root.parent
        venv_root = Path(sys.executable).parent.parent
        pyvenv_path = venv_root / "pyvenv.cfg"
        dependency_lock_path = (
            workspace_root / "requirements" / "m1-reference-macos-arm64-py311.lock"
        )
        if (
            not pyvenv_path.is_file()
            or pyvenv_path.stat().st_size != 343
            or _file_sha256(pyvenv_path)
            != "27b7b9074cde30bc28e757484a301498e391d2abe48e7b75ba822480acecebfa"
            or not dependency_lock_path.is_file()
            or _file_sha256(dependency_lock_path)
            != "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d"
        ):
            raise CP63RunnerRehearsalError(
                "PREIMPORT_RUNTIME_INPUT_MISMATCH",
                "pre-import environment bytes differ",
            )
        site_packages = (
            venv_root
            / "lib"
            / ("python%d.%d" % (sys.version_info.major, sys.version_info.minor))
            / "site-packages"
        )
        if not site_packages.is_dir():
            raise CP63RunnerRehearsalError(
                "PREIMPORT_SITE_PACKAGES_MISSING", "site-packages is absent"
            )
        os.chdir(workspace_root)
        source_root_text = str(source_root)
        if source_root_text not in sys.path:
            sys.path.insert(0, source_root_text)
        site_packages_text = str(site_packages)
        if site_packages_text not in sys.path:
            sys.path.append(site_packages_text)
        payload = _execute_rehearsal_case_locally(case.case_id, repetition)
        encoded = _plain_json_bytes(payload)
        if len(encoded) + 8 > 16_777_216:
            raise CP63RunnerRehearsalError(
                "CHILD_FRAME_OVERSIZED", "child frame is oversized"
            )
        _write_all(1, len(encoded).to_bytes(8, "big") + encoded)
        return 0
    except BaseException as error:
        code = (
            error.code
            if isinstance(error, CP63RunnerRehearsalError)
            else type(error).__name__.upper()
        )
        try:
            _write_all(2, ("CP63_CHILD_ERROR:" + code + "\n").encode("ascii")[:4096])
        except BaseException:
            pass
        return 70


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
    import fcntl

    duplicated = int(fcntl.fcntl(file_descriptor, fcntl.F_DUPFD_CLOEXEC, 3))
    _safe_close(file_descriptor)
    return duplicated


def _spawn_rehearsal_child(
    case_id: str, repetition: int, start_ns: int, launch_ordinal: int
) -> Tuple[int, int, int]:
    stdout_read = stdout_write = None
    stderr_read = stderr_write = None
    devnull = None
    pid = None
    try:
        stdout_read, stdout_write = os.pipe()
        stderr_read, stderr_write = os.pipe()
        devnull = os.open(os.devnull, os.O_RDONLY)
        stdout_read = _staging_file_descriptor(stdout_read)
        stdout_write = _staging_file_descriptor(stdout_write)
        stderr_read = _staging_file_descriptor(stderr_read)
        stderr_write = _staging_file_descriptor(stderr_write)
        devnull = _staging_file_descriptor(devnull)
        source_sha256 = _file_sha256(Path(__file__).resolve())
        nonce = _child_nonce(case_id, repetition, start_ns, launch_ordinal)
        auth = _child_auth(case_id, repetition, nonce, source_sha256)
        executable = os.path.abspath(sys.executable)
        arguments = (
            executable,
            "-S",
            "-s",
            "-P",
            "-u",
            str(Path(__file__).resolve()),
            "--cp63-rehearsal-child",
            case_id,
            str(repetition),
            nonce,
            source_sha256,
            auth,
        )
        file_actions = (
            (os.POSIX_SPAWN_DUP2, devnull, 0),
            (os.POSIX_SPAWN_DUP2, stdout_write, 1),
            (os.POSIX_SPAWN_DUP2, stderr_write, 2),
            (os.POSIX_SPAWN_CLOSE, stdout_read),
            (os.POSIX_SPAWN_CLOSE, stderr_read),
            (os.POSIX_SPAWN_CLOSE, devnull),
            (os.POSIX_SPAWN_CLOSE, stdout_write),
            (os.POSIX_SPAWN_CLOSE, stderr_write),
        )
        pid = os.posix_spawn(
            executable,
            arguments,
            dict(_SANITIZED_CHILD_ENVIRONMENT),
            file_actions=file_actions,
            setsid=True,
            setsigmask=(),
            setsigdef=(signal.SIGINT, signal.SIGPIPE, signal.SIGTERM),
        )
        _safe_close(devnull)
        devnull = None
        _safe_close(stdout_write)
        stdout_write = None
        _safe_close(stderr_write)
        stderr_write = None
        os.set_blocking(stdout_read, False)
        os.set_blocking(stderr_read, False)
    except BaseException as error:
        _safe_close(stdout_read)
        _safe_close(stderr_read)
        _safe_close(stdout_write)
        _safe_close(stderr_write)
        _safe_close(devnull)
        if pid is not None:
            try:
                _cp62_module()._terminate_and_reap(pid, None, allow_grace=False)
            except BaseException:
                pass
        raise CP63RunnerRehearsalError(
            "CHILD_SPAWN_FAILURE", "failed to spawn the rehearsal child"
        ) from error
    return cast(int, pid), cast(int, stdout_read), cast(int, stderr_read)


def _returned_raw_record(
    child_payload: dict,
    *,
    pid: int,
    start_ns: int,
    deadline_ns: int,
    terminal_ns: int,
    status: int,
    child_frame: bytes,
    stderr: bytes,
) -> bytes:
    cp62 = _cp62_module()
    exit_code, term_signal = cp62._exit_and_signal(status)
    record = dict(child_payload)
    record["supervisor_custody"] = {
        "pid": pid,
        "process_group": pid,
        "start_monotonic_ns": str(start_ns),
        "deadline_monotonic_ns": str(deadline_ns),
        "terminal_monotonic_ns": str(terminal_ns),
        "exit_code": exit_code,
        "term_signal": term_signal,
        "frame_bytes": len(child_frame),
        "child_frame_sha256": hashlib.sha256(child_frame).hexdigest(),
        "stderr_bytes": len(stderr),
        "stderr_hex": stderr.hex(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "completion_strictly_before_deadline": True,
        "exact_one_frame": True,
        "termination_attempted": False,
        "termination_signal_delivered": False,
        "kill_attempted": False,
        "reaped": True,
    }
    record["raw_sha256"] = _ZERO_SHA256
    record["raw_sha256"] = hashlib.sha256(
        b"cp63-test28-raw-record-v1\0" + _plain_json_bytes(record)
    ).hexdigest()
    encoded = _plain_json_bytes(record)
    cp63_validate_raw_record_bytes(encoded)
    return encoded


def _timeout_raw_record(
    case: CP63RehearsalCaseV1,
    row: object,
    repetition: int,
    *,
    pid: int,
    start_ns: int,
    deadline_ns: int,
    terminal_ns: int,
    status: int,
    kill_attempted: bool,
    termination_attempted: bool,
    termination_signal_delivered: bool,
    observed_stdout: bytes,
    stderr: bytes,
) -> bytes:
    cp62 = _cp62_module()
    exit_code, term_signal = cp62._exit_and_signal(status)
    record = {
        "schema": CP63_TEST28_SCHEMA_VERSION,
        "purpose": "development-runner-rehearsal-only",
        "rehearsal_id": _REHEARSAL_ID,
        "repetition": repetition,
        "seed_ordinal": 1,
        "row_ordinal": case.row_ordinal,
        "logical_request_ordinal": case.row_ordinal,
        "row_key": case.row_key,
        "fixture_id": case.fixture_id,
        "strategy": case.strategy,
        "budget": case.budget,
        "plan_seed_hex": case.seed_hex,
        "seed_free_request_sha256": row.seed_free_request_sha256,
        "request_instance_sha256": _rehearsal_request_instance_sha256(case, row),
        "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
        "phase": "timeout-at-deadline",
        "closed_status": "timeout-censored-at-deadline",
        "failure_code": None,
        "kernel_trace": {
            "semantic": cp62._closed_semantic_trace(
                _case_view(case),
                row,
                outcome_kind="timeout-censored",
                failure_code=None,
                runtime_observation=None,
            ),
            "volatile_custody": None,
        },
        "supervisor_custody": {
            "pid": pid,
            "process_group": pid,
            "start_monotonic_ns": str(start_ns),
            "deadline_monotonic_ns": str(deadline_ns),
            "terminal_monotonic_ns": str(max(terminal_ns, deadline_ns)),
            "exit_code": exit_code,
            "term_signal": term_signal,
            "frame_bytes": len(observed_stdout),
            "child_frame_sha256": hashlib.sha256(observed_stdout).hexdigest(),
            "stderr_bytes": len(stderr),
            "stderr_hex": stderr.hex(),
            "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
            "completion_strictly_before_deadline": False,
            "exact_one_frame": False,
            "termination_attempted": termination_attempted,
            "termination_signal_delivered": termination_signal_delivered,
            "kill_attempted": kill_attempted,
            "reaped": True,
        },
        "raw_sha256": _ZERO_SHA256,
    }
    record["raw_sha256"] = hashlib.sha256(
        b"cp63-test28-raw-record-v1\0" + _plain_json_bytes(record)
    ).hexdigest()
    encoded = _plain_json_bytes(record)
    cp63_validate_raw_record_bytes(encoded)
    return encoded


def _supervise_rehearsal_case(
    case: CP63RehearsalCaseV1,
    row: object,
    repetition: int,
    launch_ordinal: int,
) -> bytes:
    cp62 = _cp62_module()
    start_ns = time.monotonic_ns()
    deadline_ns = start_ns + 300 * 1_000_000_000
    pid = stdout_fd = stderr_fd = status = reaped_ns = selector = None
    stdout = bytearray()
    stderr = bytearray()
    process_group_absence_observed = False
    try:
        pid, stdout_fd, stderr_fd = _spawn_rehearsal_child(
            case.case_id, repetition, start_ns, launch_ordinal
        )
        selector = selectors.DefaultSelector()
        selector.register(stdout_fd, selectors.EVENT_READ, "stdout")
        selector.register(stderr_fd, selectors.EVENT_READ, "stderr")
        while True:
            previous_status = status
            status = cp62._poll_child(pid, status)
            if previous_status is None and status is not None:
                reaped_ns = time.monotonic_ns()
            now = time.monotonic_ns()
            if now >= deadline_ns:
                exit_code, term_signal = cp62._exit_and_signal(status)
                if status is not None and (exit_code != 0 or term_signal is not None):
                    raise CP63RunnerRehearsalError(
                        "CHILD_ABNORMAL_EXIT",
                        "child terminated abnormally before observation",
                    )
                for key in tuple(selector.get_map().values()):
                    selector.unregister(key.fd)
                (
                    status,
                    kill_attempted,
                    termination_attempted,
                    termination_delivered,
                ) = cp62._terminate_and_reap(pid, status, allow_grace=True)
                process_group_absence_observed = True
                _safe_close(stdout_fd)
                stdout_fd = None
                _safe_close(stderr_fd)
                stderr_fd = None
                cp62._require_timeout_terminal_status(status)
                return _timeout_raw_record(
                    case,
                    row,
                    repetition,
                    pid=pid,
                    start_ns=start_ns,
                    deadline_ns=deadline_ns,
                    terminal_ns=time.monotonic_ns(),
                    status=status,
                    kill_attempted=kill_attempted,
                    termination_attempted=termination_attempted,
                    termination_signal_delivered=termination_delivered,
                    observed_stdout=bytes(stdout),
                    stderr=bytes(stderr),
                )
            wait_seconds = min(0.05, max(0.0, (deadline_ns - now) / 1e9))
            cp62._read_child_streams(selector, stdout, stderr, timeout=wait_seconds)
            if status is not None and not selector.get_map():
                break
            if (
                status is not None
                and reaped_ns is not None
                and time.monotonic_ns() - reaped_ns > _PIPE_EOF_GRACE_NS
            ):
                raise CP63RunnerRehearsalError(
                    "CHILD_PIPE_EOF_FAILURE", "child pipes did not reach EOF"
                )
        exit_code, term_signal = cp62._exit_and_signal(status)
        if cp62._process_group_exists(pid):
            raise CP63RunnerRehearsalError(
                "CHILD_PROCESS_GROUP_LEAK", "child left a process-group member"
            )
        process_group_absence_observed = True
        if exit_code != 0 or term_signal is not None:
            raise CP63RunnerRehearsalError(
                "CHILD_ABNORMAL_EXIT", "child did not exit cleanly"
            )
        if len(stdout) < 8:
            raise CP63RunnerRehearsalError(
                "CHILD_FRAME_MISSING", "child frame is missing"
            )
        announced = int.from_bytes(stdout[:8], "big")
        if announced + 8 != len(stdout):
            raise CP63RunnerRehearsalError(
                "CHILD_FRAME_LENGTH_MISMATCH", "child frame length differs"
            )
        child_payload = _decode_canonical_json(
            bytes(stdout[8:]), maximum=16_777_208, name="CP63 child frame"
        )
        _validate_child_payload(child_payload)
        terminal_ns = time.monotonic_ns()
        if terminal_ns >= deadline_ns:
            cp62._require_timeout_terminal_status(status)
            return _timeout_raw_record(
                case,
                row,
                repetition,
                pid=pid,
                start_ns=start_ns,
                deadline_ns=deadline_ns,
                terminal_ns=terminal_ns,
                status=status,
                kill_attempted=False,
                termination_attempted=False,
                termination_signal_delivered=False,
                observed_stdout=bytes(stdout),
                stderr=bytes(stderr),
            )
        return _returned_raw_record(
            child_payload,
            pid=pid,
            start_ns=start_ns,
            deadline_ns=deadline_ns,
            terminal_ns=terminal_ns,
            status=cast(int, status),
            child_frame=bytes(stdout),
            stderr=bytes(stderr),
        )
    except BaseException as error:
        if selector is not None:
            for key in tuple(selector.get_map().values()):
                selector.unregister(key.fd)
                _safe_close(cast(int, key.fd))
        _safe_close(cast(Optional[int], stdout_fd))
        _safe_close(cast(Optional[int], stderr_fd))
        if (
            pid is not None
            and not process_group_absence_observed
            and (status is None or cp62._process_group_exists(pid))
        ):
            cp62._terminate_and_reap(pid, status, allow_grace=False)
        if isinstance(error, CP63RunnerRehearsalError):
            raise
        raise CP63RunnerRehearsalError(
            "CHILD_SUPERVISOR_INFRASTRUCTURE_FAILURE",
            "the rehearsal supervisor encountered an infrastructure failure",
        ) from error
    finally:
        if selector is not None:
            selector.close()


def cp63_run_rehearsal_case(case_id: object) -> bytes:
    """Run one frozen all-row development rehearsal in a fresh child."""

    global _REHEARSAL_LAUNCH_COUNT, _REHEARSAL_RUNNING

    case, row = _case_and_row(case_id)
    entered = False
    try:
        with _REHEARSAL_STATE_LOCK:
            if _REHEARSAL_RUNNING:
                raise CP63RunnerRehearsalError(
                    "REHEARSAL_CONCURRENCY_REFUSED",
                    "only one CP63 rehearsal child may run at a time",
                )
            if _REHEARSAL_LAUNCH_COUNT >= 32:
                raise CP63RunnerRehearsalError(
                    "REHEARSAL_LAUNCH_LIMIT_REACHED",
                    "the frozen CP63 launch limit is exhausted",
                )
            prior = _REHEARSAL_CASE_LAUNCH_COUNTS[case.case_id]
            if prior >= case.maximum_child_launches:
                raise CP63RunnerRehearsalError(
                    "REHEARSAL_CASE_LAUNCH_LIMIT_REACHED",
                    "the frozen per-case launch limit is exhausted",
                )
            repetition = prior + 1
            _REHEARSAL_LAUNCH_COUNT += 1
            _REHEARSAL_CASE_LAUNCH_COUNTS[case.case_id] = repetition
            _REHEARSAL_RUNNING = True
            entered = True
            launch_ordinal = _REHEARSAL_LAUNCH_COUNT
        return _supervise_rehearsal_case(case, row, repetition, launch_ordinal)
    finally:
        if entered:
            with _REHEARSAL_STATE_LOCK:
                _REHEARSAL_RUNNING = False


if __name__ == "__main__":
    raise SystemExit(_rehearsal_child_main(tuple(sys.argv[1:])))


__all__ = (
    "CP63RunnerRehearsalError",
    "CP63SeedCapsuleContractV1",
    "CP63SeedCapsuleObservationV1",
    "CP63ScheduleContractV1",
    "CP63BoundRequestV1",
    "CP63LifecycleContractV1",
    "CP63RawRecordSchemaV1",
    "CP63RunnerResourceContractV1",
    "CP63RehearsalCaseV1",
    "CP63RunnerRecomputationRehearsalBundleV1",
    "CP63_TEST28_SCHEMA_VERSION",
    "CP63_TEST28_SCOPE",
    "cp63_runner_recomputation_rehearsal_bundle",
    "cp63_validate_seed_capsule_bytes",
    "cp63_seed_capsule_canonical_json_bytes",
    "cp63_schedule_contract",
    "cp63_bound_request",
    "cp63_validate_raw_record_bytes",
    "cp63_project_stable_trace",
    "cp63_stable_trace_canonical_json_bytes",
    "cp63_stable_trace_sha256",
    "cp63_run_rehearsal_case",
)
