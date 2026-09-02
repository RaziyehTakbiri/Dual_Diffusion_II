"""Calibration-only execution capsule for Formal Test 28.

CP62 binds the seed-free request grid, one runtime/source/ABI candidate, the
future seed-capsule schema, a bounded fresh-process supervisor contract, and
raw/stable trace schemas.  It deliberately does *not* accept production seed
values or expose a campaign loop.  The only executable entry point admits four
module-owned deterministic calibration cases.

Importing the module uses only the Python standard library.  Numerical and
project execution dependencies are imported only by the private calibration
child after its fixed case identifier has been validated.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import selectors
import signal
import struct
import sys
import sysconfig
import threading
import time
from typing import Mapping, Optional, Tuple, cast


CP62_TEST28_SCHEMA_VERSION = "cp62-test28-execution-capsule-v1"
CP62_TEST28_SCOPE = (
    "calibration-only-executable-whole-seed-capsule;exact-sixteen-seed-free-"
    "requests;runtime-source-abi-candidate;future-seed-capsule-schema-with-no-"
    "values;fresh-process-supervisor-and-timeout-censor-contract;raw-record-"
    "and-stable-trace-projection;four-fixed-domain-separated-calibration-cases;"
    "no-arbitrary-seed-no-production-ingest-no-campaign-no-estimates-no-"
    "intervals-no-operational-power-confirmatory-manuscript-or-test28-closure"
)
CP62_TEST28_FORMAL_TEST_28_STATUS = "OPEN"
CP62_TEST28_CP61_SOURCE_SHA256 = (
    "8ea06f5cfc5cd79842e2984d5f91918463cf887c0efc2fd026490f51e66129cb"
)
CP62_TEST28_CP61_STABLE_DESIGN_SHA256 = (
    "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
)
CP62_TEST28_CP60_SOURCE_SHA256 = (
    "493c4ad27a7b07aa6ad9f2894656a0dd37616f8cf54f010cd2050871783294a6"
)
CP62_TEST28_CP60_BUNDLE_SHA256 = (
    "ae105e4f9689dc6ee06fbaf1f2c697b08db2b1256225e5d348a5b82afcbd7d4a"
)
CP62_TEST28_KERNEL_SOURCE_SHA256 = (
    "a8164e10239bab6d43a8d8f068cf035d9a4c8b0b29ee233bf5b0af8d75a0684c"
)
CP62_TEST28_REFERENCE_SOURCE_SHA256 = (
    "725ddc4011e2c6cf15f1810be6fabc404c50bd53333e34ad22bedcdf4d6497da"
)
CP62_TEST28_FACADE_SOURCE_SHA256 = (
    "8aecb4ed75d4f88b7d6b0355f2d2c5ddad685d761fe4fbe63359bda672973234"
)
CP62_TEST28_EXACT_SCORE_SOURCE_SHA256 = (
    "87e197085ecee91ddbd78e1dfde3d0eb84797740946f76f1ee26f837d4149313"
)
CP62_TEST28_QUOTA_SOURCE_SHA256 = (
    "3985d23337f854e43a6ee766d4d9a0afeed0a60fd9e37855c064c88e7477dde1"
)

CP62_TEST28_EXTERNAL_SEED_COUNT = 2_048
CP62_TEST28_ROW_COUNT = 16
CP62_TEST28_TOTAL_REQUEST_COUNT = 32_768
CP62_TEST28_DEADLINE_SECONDS = 300
CP62_TEST28_TERMINATION_GRACE_SECONDS = 2
CP62_TEST28_REAP_CEILING_SECONDS = 5
CP62_TEST28_REQUEST_FRAME_MAX_BYTES = 65_536
CP62_TEST28_RAW_FRAME_MAX_BYTES = 16_777_216
CP62_TEST28_STABLE_TRACE_MAX_BYTES = 8_388_608
CP62_TEST28_STDERR_MAX_BYTES = 1_048_576
CP62_TEST28_SEED_CAPSULE_MAX_BYTES = 131_072
CP62_TEST28_CALIBRATION_LAUNCH_LIMIT = 8

CP62_TEST28_SANITIZED_CHILD_ENVIRONMENT = (
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

_ZERO_SHA256 = "0" * 64
_MAX_CANONICAL_DEPTH = 64
_MAX_CANONICAL_NODES = 262_144
_MAX_TEXT_BYTES = 4_096
_MAX_INTEGER_BITS = 16_384
_ALLOW_RECORD_CLASS_DEFINITION = True
_CALIBRATION_LAUNCH_COUNT = 0
_CALIBRATION_CASE_LAUNCH_COUNTS = {
    "m1-rejection-a64": 0,
    "m1-sir-j512": 0,
    "m2-rejection-a64": 0,
    "m2-sir-j512": 0,
}
_CALIBRATION_RUNNING = False
_CALIBRATION_STATE_LOCK = threading.Lock()
_PIPE_EOF_GRACE_NS = 1_000_000_000
_CHILD_AUTH_DOMAIN = b"cp62-test28-calibration-child-auth-v1\0"
_CHILD_NONCE_DOMAIN = b"cp62-test28-calibration-child-nonce-v1\0"
_EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


class CP62ExecutionCapsuleError(RuntimeError):
    """Fail-closed CP62 boundary error with a stable machine code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class _SealedRecord:
    __slots__ = ()

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("CP62 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("CP62 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("CP62 records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP62RuntimeSourceABILockV1(_SealedRecord):
    schema_version: str
    runtime_profile_id: str
    python_version: str
    python_implementation: str
    python_soabi: str
    python_executable_realpath_role: str
    python_executable_bytes: int
    python_executable_sha256: str
    python_framework_bytes: int
    python_framework_sha256: str
    pyvenv_cfg_bytes: int
    pyvenv_cfg_sha256: str
    stdlib_file_count: int
    stdlib_symlink_count: int
    stdlib_total_bytes: int
    stdlib_closure_sha256: str
    dependency_lock_sha256: str
    numpy_version: str
    numpy_record_sha256: str
    numpy_payload_closure_sha256: str
    scipy_version: str
    scipy_record_sha256: str
    scipy_payload_closure_sha256: str
    threadpoolctl_version: str
    threadpoolctl_record_sha256: str
    numpy_multiarray_sha256: str
    numpy_philox_sha256: str
    numpy_generator_sha256: str
    scipy_special_ufuncs_sha256: str
    decimal_module_version: str
    libmpdec_version: str
    decimal_extension_sha256: str
    math_extension_sha256: str
    platform_system: str
    platform_release: str
    platform_version: str
    machine: str
    cpu_model: str
    byteorder: str
    floating_rounding_mode: str
    sanitized_child_environment: Tuple[Tuple[str, str], ...]
    base_local_source_module_count: int
    base_local_source_capsule_sha256: str
    cp62_source_self_hash_bound_externally: bool
    source_file_observation_is_executed_bytecode_attestation: bool
    concurrent_workspace_mutation_in_threat_model: bool
    candidate_observed_in_two_clean_children: bool
    runtime_path_is_semantic: bool
    runtime_portable: bool
    production_runtime_match_verified: bool
    transform_law_theorem_proved: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP62RuntimeSourceABILockV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP62SeedCapsuleContractV1(_SealedRecord):
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
    digest_and_frequency_checks_imply_iid_uniform: bool
    seed_capsule_instantiated: bool
    seed_values_present: bool
    external_source_bound: bool
    iid_uniform_with_replacement_verified: bool
    source_method_id: Optional[str]
    source_receipt_sha256: Optional[str]
    acquisition_session_sha256: Optional[str]
    body_sha256: Optional[str]
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP62SeedCapsuleContractV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP62RequestBindingV1(_SealedRecord):
    schema_version: str
    row_ordinal: int
    row_key: str
    fixture_id: str
    strategy: str
    budget: int
    cp60_request_template_sha256: str
    cp60_definition_record_sha256: str
    source_factory: str
    facade_factory: str
    kernel_factory: str
    residual_context: Tuple[float, ...]
    residual_context_sha256: str
    adapter_role_sha256: str
    initializer_role_sha256: str
    source_certificate_sha256: str
    source_parameter_sha256: str
    reference_parameter_sha256: str
    facade_certificate_sha256: str
    sir_ess_warning_fraction_float64_be: Optional[str]
    adaptive_fallback_permitted: bool
    seed_free_request_sha256: str
    seed_value_present: bool
    request_instance_fully_bound: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP62RequestBindingV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP62SupervisorContractV1(_SealedRecord):
    schema_version: str
    child_start_mode: str
    one_new_process_group_per_request: bool
    deadline_clock: str
    deadline_seconds: int
    completion_strictly_before_deadline_required: bool
    equality_at_deadline_is_timeout: bool
    termination_grace_seconds: int
    reap_ceiling_seconds: int
    timeout_status: str
    timeout_is_semantic_nonreturn: bool
    exact_one_frame_required: bool
    request_frame_max_bytes: int
    raw_frame_max_bytes: int
    stderr_max_bytes: int
    no_retry: bool
    infrastructure_failure_invalidates_entire_attempt: bool
    infrastructure_failure_folded_into_execution_failure: bool
    infrastructure_failure_folded_into_timeout: bool
    calibration_concurrency: int
    calibration_launch_limit: int
    production_entry_point_enabled: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP62SupervisorContractV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP62RawRecordSchemaV1(_SealedRecord):
    schema_version: str
    child_frame_encoding: str
    public_raw_record_encoding: str
    uint64_encoding: str
    float64_encoding: str
    fraction_encoding: str
    bytes_encoding: str
    configuration_values_retained_not_digest_only: bool
    complete_kernel_trace_required_for_validated_returns: bool
    volatile_supervisor_custody_retained: bool
    plan_certificate_nested_and_result_hashes_raw_only: bool
    future_production_shape_predeclared: bool
    closed_refusal_failure_shapes_predeclared: bool
    calibration_runner_closed_refusal_failure_classification_implemented: bool
    production_schema_frozen: bool
    production_records_observed: bool
    raw_frame_max_bytes: int
    maximum_future_raw_aggregate_bytes: int
    capacity_receipt_present: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP62RawRecordSchemaV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP62StableTraceProjectionContractV1(_SealedRecord):
    schema_version: str
    included_semantics: Tuple[str, ...]
    excluded_volatile_custody: Tuple[str, ...]
    recompute_owned_leaf_hashes: bool
    inherited_kernel_hashes_semantically_authoritative: bool
    raw_trace_retained_separately: bool
    stable_trace_max_bytes: int
    calibration_cross_process_parity_required: bool
    calibration_cross_process_parity_observed: bool
    production_cross_process_parity_observed: bool
    full_trace_law_estimated: bool
    total_variation_estimated: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP62StableTraceProjectionContractV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP62CalibrationCaseV1(_SealedRecord):
    schema_version: str
    case_id: str
    fixture_id: str
    strategy: str
    budget: int
    row_ordinal: int
    seed_uint64: int
    seed_hex: str
    seed_derivation: str
    seed_is_external_source_draw: bool
    seed_is_future_capsule_member: bool
    requested_repetitions: int
    maximum_child_launches: int
    production_observation: bool
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP62CalibrationCaseV1 cannot be subclassed")


@dataclass(frozen=True, eq=False, init=False, slots=True)
class CP62ExecutionCapsuleBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    cp60_source_sha256: str
    cp60_bundle_sha256: str
    cp61_source_sha256: str
    cp61_stable_design_sha256: str
    runtime_source_abi_lock: CP62RuntimeSourceABILockV1
    seed_capsule_contract: CP62SeedCapsuleContractV1
    request_bindings: Tuple[CP62RequestBindingV1, ...]
    supervisor_contract: CP62SupervisorContractV1
    raw_record_schema: CP62RawRecordSchemaV1
    stable_trace_projection_contract: CP62StableTraceProjectionContractV1
    calibration_cases: Tuple[CP62CalibrationCaseV1, ...]
    seed_free_request_count: int
    logical_request_order: str
    production_seed_ingest_api_exposed: bool
    arbitrary_seed_execution_api_exposed: bool
    production_campaign_loop_exposed: bool
    calibration_only: bool
    source_runtime_abi_candidate_bound: bool
    seed_capsule_instantiated: bool
    external_source_bound: bool
    iid_uniform_with_replacement_verified: bool
    request_instances_fully_bound: bool
    production_runtime_match_verified: bool
    infrastructure_fidelity_verified: bool
    production_supervisor_bound: bool
    production_runner_bound: bool
    shard_mapping_bound: bool
    production_requests_executed: bool
    estimates_computed: bool
    intervals_computed: bool
    operational_predictions_derived: bool
    runner_and_recomputation_blocker_closed: bool
    unconditional_operational_predictions_blocker_closed: bool
    power_guarantee_claimed: bool
    confirmatory_evidence: bool
    manuscript_claim_promoted: bool
    formal_test_28_status: str
    formal_test_28_closed: bool
    semantic_sha256: str
    record_sha256: str

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError("CP62ExecutionCapsuleBundleV1 cannot be subclassed")


_ALLOW_RECORD_CLASS_DEFINITION = False


def _sha256(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TypeError(name + " must be a lowercase SHA-256 digest")
    return value


def _text(value: object, name: str, *, maximum: int = _MAX_TEXT_BYTES) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if not value or len(value.encode("utf-8")) > maximum:
        raise ValueError(name + " has invalid length")
    return value


def _integer(value: object, name: str, *, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(name + " must be an exact integer")
    if value < minimum or value > maximum or value.bit_length() > _MAX_INTEGER_BITS:
        raise ValueError(name + " lies outside the frozen bound")
    return value


def _seal(cls: type, values: Mapping[str, object]) -> object:
    if set(values) != {item.name for item in fields(cls)}:
        raise TypeError("CP62 sealed record field set differs")
    result = object.__new__(cls)
    for item in fields(cls):
        object.__setattr__(result, item.name, values[item.name])
    return result


def _canonical_value(value: object, *, depth: int = 0, budget: list = None) -> object:
    if budget is None:
        budget = [0]
    budget[0] += 1
    if budget[0] > _MAX_CANONICAL_NODES or depth > _MAX_CANONICAL_DEPTH:
        raise ValueError("CP62 canonical resource bound exceeded")
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        if value.bit_length() > _MAX_INTEGER_BITS:
            raise ValueError("CP62 canonical integer is oversized")
        return {"$int": str(value)}
    if type(value) is str:
        if len(value.encode("utf-8")) > _MAX_TEXT_BYTES:
            raise ValueError("CP62 canonical text is oversized")
        return value
    if type(value) is bytes:
        if len(value) > CP62_TEST28_RAW_FRAME_MAX_BYTES:
            raise ValueError("CP62 canonical bytes are oversized")
        return {"$bytes": value.hex()}
    if type(value) is float:
        if not math.isfinite(value) or (value == 0.0 and math.copysign(1.0, value) < 0):
            raise ValueError(
                "CP62 canonical float must be finite positive-zero binary64"
            )
        return {"$float64_be": struct.pack(">d", value).hex()}
    if type(value) is Fraction:
        if (
            value.numerator.bit_length() > _MAX_INTEGER_BITS
            or value.denominator.bit_length() > _MAX_INTEGER_BITS
        ):
            raise ValueError("CP62 canonical fraction is oversized")
        return {"$fraction": [str(value.numerator), str(value.denominator)]}
    if type(value) is tuple:
        return {
            "$tuple": [
                _canonical_value(item, depth=depth + 1, budget=budget) for item in value
            ]
        }
    if type(value) is dict:
        keys = tuple(value.keys())
        if any(
            type(key) is not str or len(key.encode("utf-8")) > _MAX_TEXT_BYTES
            for key in keys
        ):
            raise TypeError("CP62 canonical mapping keys must be bounded exact text")
        result = {}
        for key in sorted(keys):
            result[key] = _canonical_value(value[key], depth=depth + 1, budget=budget)
        return result
    if isinstance(value, _SealedRecord):
        return {
            "$record": type(value).__name__,
            "fields": {
                item.name: _canonical_value(
                    getattr(value, item.name), depth=depth + 1, budget=budget
                )
                for item in fields(type(value))
            },
        }
    raise TypeError("value has no CP62 canonical representation")


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        _canonical_value(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _digest(domain: str, value: object) -> str:
    return hashlib.sha256(
        domain.encode("ascii") + b"\0" + _canonical_bytes(value)
    ).hexdigest()


def _make_record(cls: type, domain: str, values: Mapping[str, object]) -> object:
    payload = dict(values)
    payload["record_sha256"] = _ZERO_SHA256
    provisional = _seal(cls, payload)
    payload["record_sha256"] = _digest(domain, provisional)
    return _seal(cls, payload)


_ROW_INVENTORY = (
    (
        "T28-M1-Q",
        "bounded-rejection",
        1,
        "d76e7f25460b8a38d00f32542422d864fcef9c7740b9af6d4c7d62b9fdfcee7a",
        "d4d930b46ab39a0f8a0f9cb2e65a896d3361876969fb783456ceee6e2f4d9160",
    ),
    (
        "T28-M1-Q",
        "bounded-rejection",
        4,
        "00659ec7b82ffee45bd0d0acf68c60329f427a2ec2e7904694d5ef5a5e386080",
        "8366db2154dd8e56577653a8c7bf27067bd190bd76d205daab422c55396bb6f8",
    ),
    (
        "T28-M1-Q",
        "bounded-rejection",
        16,
        "3b511499c530c8f2b9cee6886a28fb9f4db3d40d43d348b7c12c9a002a713fae",
        "deff18f198aacc3e70711d6b0f747be62686f181030b47e87beec301554ff782",
    ),
    (
        "T28-M1-Q",
        "bounded-rejection",
        64,
        "03bd3438cb844ae19416431f39a6ed61b3cfd22c2593dee80acdaf42f55cac21",
        "ce302962eda91df8d8af1b775de48b8fc83ed06b390fd4061e23e309fa553f38",
    ),
    (
        "T28-M1-Q",
        "fixed-budget-sir",
        8,
        "221d4dd57aba464cce571de0005794094105bc928742745f25fc8371a9bbfeaa",
        "dfbc72991541d23f3cdeeecb3ddba460c839967676ffdc1d3cc92e3a8a57ebc5",
    ),
    (
        "T28-M1-Q",
        "fixed-budget-sir",
        32,
        "43a4ab7b219a2e1f313e7c8d04133fbace6ca9e7b85298d94dc9d2a725114276",
        "7fd96a443a40de0631f785a7b0d2c00611fbe5359185f81164af8e0530b758a3",
    ),
    (
        "T28-M1-Q",
        "fixed-budget-sir",
        128,
        "2880c960e3cb04378b0e841011e642772c11770fd20e9f59adadd3e69fc04545",
        "164690f7b8693f50892be435fd2b7e8c28ba8927209da5c39429469f2e9261f0",
    ),
    (
        "T28-M1-Q",
        "fixed-budget-sir",
        512,
        "2471f1816d0f976cdc1d267d58794a07dd6279192fa911e4d2ad265b9b2a4abf",
        "b840599e28a1cb4a3197e503e4fe694860eb783ee66a6440d81fa6a1571c6c8b",
    ),
    (
        "T28-M2-Q",
        "bounded-rejection",
        1,
        "4b4f42597f351c3e1f90ee9c333a84d3c1a489e9b3d478223cec50a43e9cb947",
        "2ed1233312fde9a35d4dfa88e8bcd7ba654fec4a06e78b7e7222312a372a8a79",
    ),
    (
        "T28-M2-Q",
        "bounded-rejection",
        4,
        "399f23bb850b1b450780b74a1101713fab31d3d8add9476b473f8c201da110e3",
        "fbc8ec85b991e495e8666c3d0a54a60e33195493d7b2365be3f58c627239f775",
    ),
    (
        "T28-M2-Q",
        "bounded-rejection",
        16,
        "0dfff79a87e0f5598f3cadc434df5cad08c8cc05272b9704daae53ea2d614b06",
        "8696cfe0a24c82af274f98adc3a6fe8ca270123f7f50f0d9595beea1cf3e0cc4",
    ),
    (
        "T28-M2-Q",
        "bounded-rejection",
        64,
        "108d3e94ae4007708687b810a2719b52f64d0048ba95c3448d64a89132d6ace8",
        "6cacbb2fddcc91ddd24a0a3eac3e5a1173fabc017e1d100babe82bf6a0efa14d",
    ),
    (
        "T28-M2-Q",
        "fixed-budget-sir",
        8,
        "2bace4f2262efd5f1e93d974fc0d1f884d9f62a4ac4343ce98f4c9ece15028e7",
        "1eb5454bbcfde0274deec91030e22ddecb4ab7eeda164a10eac4547a8259a407",
    ),
    (
        "T28-M2-Q",
        "fixed-budget-sir",
        32,
        "52fc434f07d1b3e1547d4564522328bfa414b23bb2ce34723c6174d6eca458ba",
        "4e1e978e901ef11d644c70a337990f556d0bc7f1251a8ddd27d0069438ff1dc5",
    ),
    (
        "T28-M2-Q",
        "fixed-budget-sir",
        128,
        "68b96d706e0f6cfa54358481a8633fa60910eee3d74b4327def13a5bddd1ab8c",
        "0d699f76655f5558788872324adff18ca347a7392428f7a342396176c16ceec2",
    ),
    (
        "T28-M2-Q",
        "fixed-budget-sir",
        512,
        "366a20c37e4ed8394eaa5699d2942168a7ff2f01d385933d50785fbf33e76960",
        "22027ae08c0a673cba4866656d868102eafc6b336d57225028dfe96bf65fa71b",
    ),
)

_FIXTURE_BINDINGS = {
    "T28-M1-Q": {
        "adapter_role": "e93c2bd1bb9181ed21538d15e5618753a92048f7f3b5647250db2c570df0b2fc",
        "initializer_role": "a4ccf3fd3c63ac740e723d1bf6e30bcdb155089ce0901c0c5e0dee53936f6b38",
        "source_certificate": "3b29d26b3f50d63e6a52ca5033264e2346d7b4175342ac86c20254b98b745cc3",
        "source_parameter": "7cdd3f34b36d71fdd094c8db03dd34f1bc4aa8790c76c3f3d0409ad83e5b4dff",
        "reference_parameter": "8a07e6ee27a31bbfacc7f23531ca62a02e940838dca8f7bb39d660ed5c41aefd",
        "facade_certificate": "252d79a82b71951a28b5107d40f86d4a655d86242428fdae3fed8298fa35dda6",
    },
    "T28-M2-Q": {
        "adapter_role": "334d63f46dc53483717ab5017373622a7626e194e33f0de0b2d13b938abf793d",
        "initializer_role": "7c1e6a032b3da0e83756a00dc2fb6b4c28fad88bed9dcb3b548a3a79a8013677",
        "source_certificate": "d6f6b25794d3e1759f5a169a9a3c55e94af37d498117cce6dcb0644342edb8de",
        "source_parameter": "2031ac8bc0f9cc338d7784e9aba9264d369b96b6bf87482440c673a273882044",
        "reference_parameter": "3a2a7d39b64318b7e37b760fc48b11b9421869cb3f292b590af02ac22fcbc926",
        "facade_certificate": "be672223c1806ad3fe54f251d8d4b8822ad76d2a93c2c6f9c1f01ab75314da2d",
    },
}

_EMPTY_CONTEXT_SHA256 = (
    "8176a4298d195a7c4f82c579db2b23dd9fdaed9b7ffc1f687b7e980a99f1720f"
)

_CALIBRATION_INVENTORY = (
    ("m1-rejection-a64", "T28-M1-Q", "bounded-rejection", 64, 4, 0x50F4E257C447B1A5),
    ("m1-sir-j512", "T28-M1-Q", "fixed-budget-sir", 512, 8, 0xBF9166D11A411920),
    ("m2-rejection-a64", "T28-M2-Q", "bounded-rejection", 64, 12, 0x5A17988A783E381E),
    ("m2-sir-j512", "T28-M2-Q", "fixed-budget-sir", 512, 16, 0xC89B2562891B7701),
)


def _runtime_lock() -> CP62RuntimeSourceABILockV1:
    return cast(
        CP62RuntimeSourceABILockV1,
        _make_record(
            CP62RuntimeSourceABILockV1,
            "cp62-runtime-lock",
            {
                "schema_version": CP62_TEST28_SCHEMA_VERSION,
                "runtime_profile_id": "cp62-darwin-arm64-cpython3115-numpy246-scipy1171-calibration",
                "python_version": "3.11.5",
                "python_implementation": "CPython",
                "python_soabi": "cpython-311-darwin",
                "python_executable_realpath_role": "Library-Frameworks-Python-3.11-python3.11",
                "python_executable_bytes": 152_624,
                "python_executable_sha256": "ff2d7180d4aa2dcc03193194c1999509239e00101ade54fcdd736d9fc25bd0c6",
                "python_framework_bytes": 14_204_096,
                "python_framework_sha256": "0d05199d9881aaf901bcba66ce734e9563962a3d745c136d5d056a5f7b4be877",
                "pyvenv_cfg_bytes": 343,
                "pyvenv_cfg_sha256": "27b7b9074cde30bc28e757484a301498e391d2abe48e7b75ba822480acecebfa",
                "stdlib_file_count": 2_434,
                "stdlib_symlink_count": 2,
                "stdlib_total_bytes": 63_614_440,
                "stdlib_closure_sha256": "085941fc71c7e7d70f0b483d5ce763b10504edde09b77a0e8f00439c544af914",
                "dependency_lock_sha256": "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d",
                "numpy_version": "2.4.6",
                "numpy_record_sha256": "309c7993f01d68786221ef82fa233ca1a4fae7e88f34d24a033277f7ed680afb",
                "numpy_payload_closure_sha256": "5e015638adcd22cdc32e835eb48f1c82d1f1ec617a5af9f71ca89ad3f8179b30",
                "scipy_version": "1.17.1",
                "scipy_record_sha256": "e354befae57c8db19038d4b603e25160c143d71841c99072b2eeb3298c031ebb",
                "scipy_payload_closure_sha256": "ac4fc6789e36558a2cc48eaab89214faf8b3bccfb889029115e048acf6d8488e",
                "threadpoolctl_version": "3.6.0",
                "threadpoolctl_record_sha256": "45ec1ffcec4eabed9558f14385fc6f6122ac97461acce1bdbc962631b7f0efc4",
                "numpy_multiarray_sha256": "2a5f2e415c5e582109b015eafd0da1ce887b3e3006969369fe2e5e5b27720acd",
                "numpy_philox_sha256": "995b0916b06a8df18dfc2085df33d7c80ea0e27b1ce84a5ebe0bab71d9e0b8a0",
                "numpy_generator_sha256": "b492b97c917d15e0c7d17f2243b0c71ff4198e1fc193d4485e0136610677ec0a",
                "scipy_special_ufuncs_sha256": "edc1aa109be752f742d2cec328f2fcdcb29f947f24e91a41326ba92bf770dbd6",
                "decimal_module_version": "1.70",
                "libmpdec_version": "2.5.1",
                "decimal_extension_sha256": "4bca4ab8d399c2e4e105823e9857917b8d7daad0b3cd76110cfe2b552def8520",
                "math_extension_sha256": "b477f5570d9d57894c9146bc2ae2aad890b7ef06d2ba4d31753de22bbc1e4fb5",
                "platform_system": "Darwin",
                "platform_release": "25.3.0",
                "platform_version": "macOS-26.3.1-build-25D2128",
                "machine": "arm64",
                "cpu_model": "Apple-M1-Pro",
                "byteorder": "little",
                "floating_rounding_mode": "FE_TONEAREST-0",
                "sanitized_child_environment": CP62_TEST28_SANITIZED_CHILD_ENVIRONMENT,
                "base_local_source_module_count": 29,
                "base_local_source_capsule_sha256": "fbe8188acd893d98b7e362a3440f6ecc00035448ed40785f4852507642755daf",
                "cp62_source_self_hash_bound_externally": True,
                "source_file_observation_is_executed_bytecode_attestation": False,
                "concurrent_workspace_mutation_in_threat_model": False,
                "candidate_observed_in_two_clean_children": True,
                "runtime_path_is_semantic": False,
                "runtime_portable": False,
                "production_runtime_match_verified": False,
                "transform_law_theorem_proved": False,
            },
        ),
    )


def _seed_contract() -> CP62SeedCapsuleContractV1:
    return cast(
        CP62SeedCapsuleContractV1,
        _make_record(
            CP62SeedCapsuleContractV1,
            "cp62-seed-contract",
            {
                "schema_version": CP62_TEST28_SCHEMA_VERSION,
                "purpose": "future-production-external-iid-uniform-uint64-with-replacement",
                "cp61_stable_design_sha256": CP62_TEST28_CP61_STABLE_DESIGN_SHA256,
                "seed_count": CP62_TEST28_EXTERNAL_SEED_COUNT,
                "seed_ordinals": tuple(range(1, CP62_TEST28_EXTERNAL_SEED_COUNT + 1)),
                "seed_encoding": "uint64-16-lowercase-hex-big-endian",
                "exact_json_keys": (
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
                ),
                "maximum_capsule_bytes": CP62_TEST28_SEED_CAPSULE_MAX_BYTES,
                "duplicate_values_retained": True,
                "order_is_semantic": True,
                "no_retry_drop_replacement_or_topup": True,
                "digest_and_frequency_checks_imply_iid_uniform": False,
                "seed_capsule_instantiated": False,
                "seed_values_present": False,
                "external_source_bound": False,
                "iid_uniform_with_replacement_verified": False,
                "source_method_id": None,
                "source_receipt_sha256": None,
                "acquisition_session_sha256": None,
                "body_sha256": None,
            },
        ),
    )


def _seed_free_digest(values: Mapping[str, object]) -> str:
    return hashlib.sha256(
        b"cp62-test28-seed-free-request-v1\0" + _canonical_bytes(dict(values))
    ).hexdigest()


def _request_bindings() -> Tuple[CP62RequestBindingV1, ...]:
    result = []
    for ordinal, (fixture, strategy, budget, template_sha, definition_sha) in enumerate(
        _ROW_INVENTORY, 1
    ):
        fixed = _FIXTURE_BINDINGS[fixture]
        values = {
            "schema_version": CP62_TEST28_SCHEMA_VERSION,
            "row_ordinal": ordinal,
            "row_key": "row-%02d/%s/%s/budget-%d"
            % (ordinal, fixture, strategy, budget),
            "fixture_id": fixture,
            "strategy": strategy,
            "budget": budget,
            "cp60_request_template_sha256": template_sha,
            "cp60_definition_record_sha256": definition_sha,
            "source_factory": "build_t28_m1_q_exact_score_provider"
            if fixture == "T28-M1-Q"
            else "build_t28_m2_q_exact_score_provider",
            "facade_factory": "adapt_exact_rational_quadratic_initial_tilt_score_provider_v1",
            "kernel_factory": "certify_mixed_support_initial_tilt_initializer_kernel_v2",
            "residual_context": (),
            "residual_context_sha256": _EMPTY_CONTEXT_SHA256,
            "adapter_role_sha256": fixed["adapter_role"],
            "initializer_role_sha256": fixed["initializer_role"],
            "source_certificate_sha256": fixed["source_certificate"],
            "source_parameter_sha256": fixed["source_parameter"],
            "reference_parameter_sha256": fixed["reference_parameter"],
            "facade_certificate_sha256": fixed["facade_certificate"],
            "sir_ess_warning_fraction_float64_be": "3fd0000000000000"
            if strategy == "fixed-budget-sir"
            else None,
            "adaptive_fallback_permitted": False,
        }
        values["seed_free_request_sha256"] = _seed_free_digest(values)
        values["seed_value_present"] = False
        values["request_instance_fully_bound"] = False
        result.append(
            cast(
                CP62RequestBindingV1,
                _make_record(CP62RequestBindingV1, "cp62-request-binding", values),
            )
        )
    return tuple(result)


def _supervisor_contract() -> CP62SupervisorContractV1:
    return cast(
        CP62SupervisorContractV1,
        _make_record(
            CP62SupervisorContractV1,
            "cp62-supervisor-contract",
            {
                "schema_version": CP62_TEST28_SCHEMA_VERSION,
                "child_start_mode": "fresh-posix-spawn-exec-new-session-no-application-fork",
                "one_new_process_group_per_request": True,
                "deadline_clock": "parent-monotonic-ns",
                "deadline_seconds": CP62_TEST28_DEADLINE_SECONDS,
                "completion_strictly_before_deadline_required": True,
                "equality_at_deadline_is_timeout": True,
                "termination_grace_seconds": CP62_TEST28_TERMINATION_GRACE_SECONDS,
                "reap_ceiling_seconds": CP62_TEST28_REAP_CEILING_SECONDS,
                "timeout_status": "timeout-censored-at-deadline",
                "timeout_is_semantic_nonreturn": False,
                "exact_one_frame_required": True,
                "request_frame_max_bytes": CP62_TEST28_REQUEST_FRAME_MAX_BYTES,
                "raw_frame_max_bytes": CP62_TEST28_RAW_FRAME_MAX_BYTES,
                "stderr_max_bytes": CP62_TEST28_STDERR_MAX_BYTES,
                "no_retry": True,
                "infrastructure_failure_invalidates_entire_attempt": True,
                "infrastructure_failure_folded_into_execution_failure": False,
                "infrastructure_failure_folded_into_timeout": False,
                "calibration_concurrency": 1,
                "calibration_launch_limit": CP62_TEST28_CALIBRATION_LAUNCH_LIMIT,
                "production_entry_point_enabled": False,
            },
        ),
    )


def _raw_schema() -> CP62RawRecordSchemaV1:
    return cast(
        CP62RawRecordSchemaV1,
        _make_record(
            CP62RawRecordSchemaV1,
            "cp62-raw-schema",
            {
                "schema_version": CP62_TEST28_SCHEMA_VERSION,
                "child_frame_encoding": "one-uint64-big-endian-length-prefixed-canonical-json-frame",
                "public_raw_record_encoding": "unframed-canonical-json-object-bytes",
                "uint64_encoding": "16-lowercase-hex-big-endian",
                "float64_encoding": "tagged-8-byte-big-endian-hex",
                "fraction_encoding": "tagged-canonical-signed-numerator-positive-denominator-decimal",
                "bytes_encoding": "bounded-lowercase-hex",
                "configuration_values_retained_not_digest_only": True,
                "complete_kernel_trace_required_for_validated_returns": True,
                "volatile_supervisor_custody_retained": True,
                "plan_certificate_nested_and_result_hashes_raw_only": True,
                "future_production_shape_predeclared": True,
                "closed_refusal_failure_shapes_predeclared": True,
                "calibration_runner_closed_refusal_failure_classification_implemented": False,
                "production_schema_frozen": False,
                "production_records_observed": False,
                "raw_frame_max_bytes": CP62_TEST28_RAW_FRAME_MAX_BYTES,
                "maximum_future_raw_aggregate_bytes": CP62_TEST28_TOTAL_REQUEST_COUNT
                * CP62_TEST28_RAW_FRAME_MAX_BYTES,
                "capacity_receipt_present": False,
            },
        ),
    )


def _projection_contract() -> CP62StableTraceProjectionContractV1:
    return cast(
        CP62StableTraceProjectionContractV1,
        _make_record(
            CP62StableTraceProjectionContractV1,
            "cp62-projection-contract",
            {
                "schema_version": CP62_TEST28_SCHEMA_VERSION,
                "included_semantics": (
                    "request-fixture-strategy-budget-plan-seed",
                    "source-facade-reference-parameter-and-role-certificates",
                    "stable-runtime-source-abi-record",
                    "derived-role-seeds-and-initial-final-rng-state-hashes",
                    "canonical-configuration-values-and-coordinate-binary64-bytes",
                    "source-facade-evaluations-and-exact-q",
                    "all-rejection-delta-quota-decision-and-acceptance-slots",
                    "complete-sir-cloud-weight-ess-resampling-and-selection",
                    "closed-return-status-or-failure-code",
                ),
                "excluded_volatile_custody": (
                    "pid-process-group-path-time-stderr-repr-and-object-identities",
                    "plan-kernel-certificate-nested-evaluation-attempt-particle-and-result-sha256",
                    "raw-record-sha256",
                ),
                "recompute_owned_leaf_hashes": True,
                "inherited_kernel_hashes_semantically_authoritative": False,
                "raw_trace_retained_separately": True,
                "stable_trace_max_bytes": CP62_TEST28_STABLE_TRACE_MAX_BYTES,
                "calibration_cross_process_parity_required": True,
                "calibration_cross_process_parity_observed": True,
                "production_cross_process_parity_observed": False,
                "full_trace_law_estimated": False,
                "total_variation_estimated": False,
            },
        ),
    )


def _calibration_cases() -> Tuple[CP62CalibrationCaseV1, ...]:
    return tuple(
        cast(
            CP62CalibrationCaseV1,
            _make_record(
                CP62CalibrationCaseV1,
                "cp62-calibration-case",
                {
                    "schema_version": CP62_TEST28_SCHEMA_VERSION,
                    "case_id": case_id,
                    "fixture_id": fixture,
                    "strategy": strategy,
                    "budget": budget,
                    "row_ordinal": row,
                    "seed_uint64": seed,
                    "seed_hex": seed.to_bytes(8, "big").hex(),
                    "seed_derivation": "first-eight-bytes-big-endian-of-sha256(cp62-test28-calibration-seed-v1\\0+fixture+\\0+strategy)",
                    "seed_is_external_source_draw": False,
                    "seed_is_future_capsule_member": False,
                    "requested_repetitions": 2,
                    "maximum_child_launches": 2,
                    "production_observation": False,
                },
            ),
        )
        for case_id, fixture, strategy, budget, row, seed in _CALIBRATION_INVENTORY
    )


def _bundle_values() -> dict:
    return {
        "schema_version": CP62_TEST28_SCHEMA_VERSION,
        "scope": CP62_TEST28_SCOPE,
        "cp60_source_sha256": CP62_TEST28_CP60_SOURCE_SHA256,
        "cp60_bundle_sha256": CP62_TEST28_CP60_BUNDLE_SHA256,
        "cp61_source_sha256": CP62_TEST28_CP61_SOURCE_SHA256,
        "cp61_stable_design_sha256": CP62_TEST28_CP61_STABLE_DESIGN_SHA256,
        "runtime_source_abi_lock": _runtime_lock(),
        "seed_capsule_contract": _seed_contract(),
        "request_bindings": _request_bindings(),
        "supervisor_contract": _supervisor_contract(),
        "raw_record_schema": _raw_schema(),
        "stable_trace_projection_contract": _projection_contract(),
        "calibration_cases": _calibration_cases(),
        "seed_free_request_count": 16,
        "logical_request_order": "seed-major:(seed_ordinal-1)*16+row_ordinal",
        "production_seed_ingest_api_exposed": False,
        "arbitrary_seed_execution_api_exposed": False,
        "production_campaign_loop_exposed": False,
        "calibration_only": True,
        "source_runtime_abi_candidate_bound": True,
        "seed_capsule_instantiated": False,
        "external_source_bound": False,
        "iid_uniform_with_replacement_verified": False,
        "request_instances_fully_bound": False,
        "production_runtime_match_verified": False,
        "infrastructure_fidelity_verified": False,
        "production_supervisor_bound": False,
        "production_runner_bound": False,
        "shard_mapping_bound": False,
        "production_requests_executed": False,
        "estimates_computed": False,
        "intervals_computed": False,
        "operational_predictions_derived": False,
        "runner_and_recomputation_blocker_closed": False,
        "unconditional_operational_predictions_blocker_closed": False,
        "power_guarantee_claimed": False,
        "confirmatory_evidence": False,
        "manuscript_claim_promoted": False,
        "formal_test_28_status": CP62_TEST28_FORMAL_TEST_28_STATUS,
        "formal_test_28_closed": False,
        "semantic_sha256": _ZERO_SHA256,
    }


def _build_bundle() -> CP62ExecutionCapsuleBundleV1:
    values = _bundle_values()
    semantic = {key: value for key, value in values.items() if key != "semantic_sha256"}
    values["semantic_sha256"] = _digest("cp62-execution-capsule-semantic", semantic)
    return cast(
        CP62ExecutionCapsuleBundleV1,
        _make_record(
            CP62ExecutionCapsuleBundleV1, "cp62-execution-capsule-bundle", values
        ),
    )


def cp62_execution_capsule_bundle() -> CP62ExecutionCapsuleBundleV1:
    """Return the zero-import, zero-file-read CP62 calibration capsule."""

    return validate_cp62_execution_capsule_bundle(_build_bundle())


def _validate_exact_replay(
    value: object, expected: object, cls: type, name: str
) -> object:
    if type(value) is not cls:
        raise TypeError(name + " has the wrong exact CP62 type")
    if _canonical_bytes(value) != _canonical_bytes(expected):
        raise ValueError(name + " differs from frozen replay")
    return value


def validate_cp62_runtime_source_abi_lock(value: object) -> CP62RuntimeSourceABILockV1:
    return cast(
        CP62RuntimeSourceABILockV1,
        _validate_exact_replay(
            value, _runtime_lock(), CP62RuntimeSourceABILockV1, "runtime lock"
        ),
    )


def validate_cp62_seed_capsule_contract(value: object) -> CP62SeedCapsuleContractV1:
    return cast(
        CP62SeedCapsuleContractV1,
        _validate_exact_replay(
            value, _seed_contract(), CP62SeedCapsuleContractV1, "seed capsule contract"
        ),
    )


def validate_cp62_request_binding(value: object) -> CP62RequestBindingV1:
    if type(value) is not CP62RequestBindingV1:
        raise TypeError("request binding has the wrong exact CP62 type")
    ordinal = _integer(value.row_ordinal, "request row ordinal", minimum=1, maximum=16)
    return cast(
        CP62RequestBindingV1,
        _validate_exact_replay(
            value,
            _request_bindings()[ordinal - 1],
            CP62RequestBindingV1,
            "request binding",
        ),
    )


def validate_cp62_supervisor_contract(value: object) -> CP62SupervisorContractV1:
    return cast(
        CP62SupervisorContractV1,
        _validate_exact_replay(
            value,
            _supervisor_contract(),
            CP62SupervisorContractV1,
            "supervisor contract",
        ),
    )


def validate_cp62_raw_record_schema(value: object) -> CP62RawRecordSchemaV1:
    return cast(
        CP62RawRecordSchemaV1,
        _validate_exact_replay(
            value, _raw_schema(), CP62RawRecordSchemaV1, "raw schema"
        ),
    )


def validate_cp62_stable_trace_projection_contract(
    value: object,
) -> CP62StableTraceProjectionContractV1:
    return cast(
        CP62StableTraceProjectionContractV1,
        _validate_exact_replay(
            value,
            _projection_contract(),
            CP62StableTraceProjectionContractV1,
            "stable projection contract",
        ),
    )


def validate_cp62_calibration_case(value: object) -> CP62CalibrationCaseV1:
    if type(value) is not CP62CalibrationCaseV1:
        raise TypeError("calibration case has the wrong exact CP62 type")
    case_id = _text(value.case_id, "calibration case id")
    for expected in _calibration_cases():
        if expected.case_id == case_id:
            return cast(
                CP62CalibrationCaseV1,
                _validate_exact_replay(
                    value, expected, CP62CalibrationCaseV1, "calibration case"
                ),
            )
    raise ValueError("calibration case id is not frozen")


def validate_cp62_execution_capsule_bundle(
    value: object,
) -> CP62ExecutionCapsuleBundleV1:
    return cast(
        CP62ExecutionCapsuleBundleV1,
        _validate_exact_replay(
            value,
            _build_bundle_without_validation(),
            CP62ExecutionCapsuleBundleV1,
            "execution capsule bundle",
        ),
    )


def _build_bundle_without_validation() -> CP62ExecutionCapsuleBundleV1:
    values = _bundle_values()
    semantic = {key: item for key, item in values.items() if key != "semantic_sha256"}
    values["semantic_sha256"] = _digest("cp62-execution-capsule-semantic", semantic)
    return cast(
        CP62ExecutionCapsuleBundleV1,
        _make_record(
            CP62ExecutionCapsuleBundleV1, "cp62-execution-capsule-bundle", values
        ),
    )


def cp62_canonical_json_bytes(record: object) -> bytes:
    if type(record) is CP62ExecutionCapsuleBundleV1:
        validate_cp62_execution_capsule_bundle(record)
    elif type(record) is CP62RuntimeSourceABILockV1:
        validate_cp62_runtime_source_abi_lock(record)
    elif type(record) is CP62SeedCapsuleContractV1:
        validate_cp62_seed_capsule_contract(record)
    elif type(record) is CP62RequestBindingV1:
        validate_cp62_request_binding(record)
    elif type(record) is CP62SupervisorContractV1:
        validate_cp62_supervisor_contract(record)
    elif type(record) is CP62RawRecordSchemaV1:
        validate_cp62_raw_record_schema(record)
    elif type(record) is CP62StableTraceProjectionContractV1:
        validate_cp62_stable_trace_projection_contract(record)
    elif type(record) is CP62CalibrationCaseV1:
        validate_cp62_calibration_case(record)
    else:
        raise TypeError("canonical CP62 JSON accepts exact public records only")
    return _canonical_bytes(record)


def cp62_execution_capsule_semantic_sha256(bundle: object) -> str:
    return validate_cp62_execution_capsule_bundle(bundle).semantic_sha256


def cp62_logical_request_ordinal(seed_ordinal: object, row_ordinal: object) -> int:
    seed = _integer(
        seed_ordinal, "seed ordinal", minimum=1, maximum=CP62_TEST28_EXTERNAL_SEED_COUNT
    )
    row = _integer(row_ordinal, "row ordinal", minimum=1, maximum=CP62_TEST28_ROW_COUNT)
    return (seed - 1) * CP62_TEST28_ROW_COUNT + row


def cp62_inverse_logical_request_ordinal(logical_ordinal: object) -> Tuple[int, int]:
    logical = _integer(
        logical_ordinal,
        "logical request ordinal",
        minimum=1,
        maximum=CP62_TEST28_TOTAL_REQUEST_COUNT,
    )
    return (
        (logical - 1) // CP62_TEST28_ROW_COUNT + 1,
        (logical - 1) % CP62_TEST28_ROW_COUNT + 1,
    )


def _reject_duplicate_pairs(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("CP62 JSON contains duplicate keys")
        result[key] = value
    return result


def _decode_canonical_json(payload: bytes, *, maximum: int, name: str) -> dict:
    if type(payload) is not bytes or not payload or len(payload) > maximum:
        raise ValueError(name + " has invalid byte length")
    if payload.startswith(b"\xef\xbb\xbf") or payload.rstrip() != payload:
        raise ValueError(name + " is not exact canonical JSON bytes")
    try:
        value = json.loads(
            payload.decode("ascii"), object_pairs_hook=_reject_duplicate_pairs
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError(name + " is not canonical JSON") from error
    if type(value) is not dict:
        raise TypeError(name + " must decode to an exact object")
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")
    if encoded != payload:
        raise ValueError(name + " is not in canonical byte form")
    _validate_plain_json_resources(value, name=name)
    return value


def _validate_plain_json_resources(
    value: object,
    *,
    name: str,
    depth: int = 0,
    budget: Optional[list] = None,
    key_name: Optional[str] = None,
) -> None:
    if budget is None:
        budget = [0]
    budget[0] += 1
    if depth > _MAX_CANONICAL_DEPTH or budget[0] > _MAX_CANONICAL_NODES:
        raise ValueError(name + " exceeds the frozen structural resource bound")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if value.bit_length() > _MAX_INTEGER_BITS:
            raise ValueError(name + " contains an oversized integer")
        return
    if type(value) is float:
        raise TypeError(name + " must not contain JSON floating-point numbers")
    if type(value) is str:
        maximum = (
            2 * CP62_TEST28_STDERR_MAX_BYTES
            if key_name == "stderr_hex"
            else _MAX_TEXT_BYTES
        )
        if len(value.encode("utf-8")) > maximum:
            raise ValueError(name + " contains oversized text")
        return
    if type(value) is list:
        for item in value:
            _validate_plain_json_resources(
                item,
                name=name,
                depth=depth + 1,
                budget=budget,
            )
        return
    if type(value) is dict:
        for key, item in value.items():
            if (
                type(key) is not str
                or not key
                or len(key.encode("utf-8")) > _MAX_TEXT_BYTES
            ):
                raise TypeError(name + " has an invalid mapping key")
            _validate_plain_json_resources(
                item,
                name=name,
                depth=depth + 1,
                budget=budget,
                key_name=key,
            )
        return
    raise TypeError(name + " contains a non-JSON value")


def _plain_json_bytes(value: object) -> bytes:
    _validate_plain_json_resources(value, name="CP62 plain JSON")
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _plain_digest(domain: bytes, value: object) -> str:
    return hashlib.sha256(domain + b"\0" + _plain_json_bytes(value)).hexdigest()


def _exact_keys(value: object, expected: Tuple[str, ...], name: str) -> dict:
    if type(value) is not dict:
        raise TypeError(name + " must be an exact object")
    keys = tuple(value.keys())
    if any(
        type(key) is not str or not key or len(key.encode("utf-8")) > _MAX_TEXT_BYTES
        for key in keys
    ):
        raise TypeError(name + " keys must be bounded exact text")
    if len(keys) != len(expected) or set(keys) != set(expected):
        raise ValueError(name + " field set differs")
    return value


def _json_integer(value: object, name: str, *, minimum: int, maximum: int) -> int:
    return _integer(value, name, minimum=minimum, maximum=maximum)


def _json_optional_integer(
    value: object, name: str, *, minimum: int, maximum: int
) -> Optional[int]:
    if value is None:
        return None
    return _json_integer(value, name, minimum=minimum, maximum=maximum)


def _json_boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(name + " must be an exact boolean")
    return value


def _json_optional_sha256(value: object, name: str) -> Optional[str]:
    if value is None:
        return None
    return _sha256(value, name)


def _uint64_hex(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 16
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TypeError(name + " must be exact lowercase uint64 big-endian hex")
    return value


def _optional_uint64_hex(value: object, name: str) -> Optional[str]:
    if value is None:
        return None
    return _uint64_hex(value, name)


def _decimal_integer_text(
    value: object, name: str, *, minimum: Optional[int] = None
) -> int:
    if type(value) is not str or not value:
        raise TypeError(name + " must be a canonical decimal integer string")
    try:
        parsed = int(value, 10)
    except ValueError as error:
        raise ValueError(name + " is not a decimal integer") from error
    if str(parsed) != value or parsed.bit_length() > _MAX_INTEGER_BITS:
        raise ValueError(name + " is not canonical or is oversized")
    if minimum is not None and parsed < minimum:
        raise ValueError(name + " lies below the frozen minimum")
    return parsed


def _fraction_tag(value: Fraction) -> dict:
    if type(value) is not Fraction:
        raise TypeError("fraction tag requires an exact Fraction")
    if (
        value.numerator.bit_length() > _MAX_INTEGER_BITS
        or value.denominator.bit_length() > _MAX_INTEGER_BITS
    ):
        raise ValueError("fraction tag is oversized")
    return {"$fraction": [str(value.numerator), str(value.denominator)]}


def _validate_fraction_tag(value: object, name: str) -> Fraction:
    checked = _exact_keys(value, ("$fraction",), name)
    parts = checked["$fraction"]
    if type(parts) is not list or len(parts) != 2:
        raise TypeError(name + " fraction payload must be an exact pair")
    numerator = _decimal_integer_text(parts[0], name + " numerator")
    denominator = _decimal_integer_text(parts[1], name + " denominator", minimum=1)
    result = Fraction(numerator, denominator)
    if result.numerator != numerator or result.denominator != denominator:
        raise ValueError(name + " fraction is not reduced")
    return result


def _float64_tag(value: object) -> dict:
    if type(value) not in (float,):
        value = float(value)
    checked = float(value)
    if not math.isfinite(checked) or (
        checked == 0.0 and math.copysign(1.0, checked) < 0.0
    ):
        raise ValueError("binary64 trace value must be finite with canonical zero")
    return {"$float64_be": struct.pack(">d", checked).hex()}


def _validate_float64_tag(value: object, name: str) -> float:
    checked = _exact_keys(value, ("$float64_be",), name)
    raw = checked["$float64_be"]
    if (
        type(raw) is not str
        or len(raw) != 16
        or any(character not in "0123456789abcdef" for character in raw)
    ):
        raise TypeError(name + " must be exact binary64 big-endian hex")
    result = struct.unpack(">d", bytes.fromhex(raw))[0]
    if not math.isfinite(result) or (
        result == 0.0 and math.copysign(1.0, result) < 0.0
    ):
        raise ValueError(name + " is nonfinite or negative zero")
    return result


def _validate_optional_float64_tag(value: object, name: str) -> Optional[float]:
    if value is None:
        return None
    return _validate_float64_tag(value, name)


def _verify_owned_leaf(value: dict, *, field: str, domain: bytes, name: str) -> None:
    supplied = _sha256(value[field], name + " digest")
    body = dict(value)
    body.pop(field)
    expected = _plain_digest(domain, body)
    if supplied != expected:
        raise ValueError(name + " digest differs")


def _owned_leaf(domain: bytes, body: Mapping[str, object], field: str) -> dict:
    result = dict(body)
    result[field] = _plain_digest(domain, result)
    return result


def _case_and_row(
    case_id: object,
) -> Tuple[CP62CalibrationCaseV1, CP62RequestBindingV1]:
    checked = _text(case_id, "calibration case id")
    cases = _calibration_cases()
    for case in cases:
        if case.case_id == checked:
            return case, _request_bindings()[case.row_ordinal - 1]
    raise ValueError("only the four frozen CP62 calibration cases are executable")


def _current_source_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


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
_QUOTA_TEXT_FIELDS = (
    "schema_version",
    "certificate_scope",
    "proof_policy",
    "proof_contract",
    "branch",
)
_QUOTA_INTEGER_FIELDS = (
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
)
_QUOTA_BOOLEAN_FIELDS = (
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
)
_QUOTA_KEYS = (
    *_QUOTA_TEXT_FIELDS,
    *_QUOTA_INTEGER_FIELDS,
    *_QUOTA_BOOLEAN_FIELDS,
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
_SEMANTIC_TRACE_KEYS = (
    "trace_schema",
    "stable_request_sha256",
    "calibration_instance_sha256",
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
    "cp62_semantic_trace_sha256",
)
_CLOSED_SEMANTIC_TRACE_KEYS = (
    "trace_schema",
    "stable_request_sha256",
    "calibration_instance_sha256",
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
    "cp62_closed_trace_sha256",
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


def _configuration_trace(configuration: object) -> dict:
    if type(configuration) is not tuple:
        raise TypeError("kernel configuration must be an exact tuple")
    events = []
    prior = None
    for event in configuration:
        event_type = _integer(
            getattr(event, "event_type", None),
            "configuration event type",
            minimum=0,
            maximum=2**31 - 1,
        )
        coordinates = getattr(event, "coordinates", None)
        if type(coordinates) is not tuple:
            raise TypeError("configuration coordinates must be an exact tuple")
        encoded_coordinates = [_float64_tag(value) for value in coordinates]
        ordering_key = (event_type, tuple(float(value) for value in coordinates))
        if prior is not None and ordering_key < prior:
            raise ValueError("configuration events are noncanonical")
        prior = ordering_key
        events.append(
            {"event_type": event_type, "coordinates_float64_be": encoded_coordinates}
        )
    return _owned_leaf(
        b"cp62-test28-configuration-v1",
        {"events": events},
        "cp62_configuration_sha256",
    )


def _source_evaluation_trace(evaluation: object) -> dict:
    body = {
        "fixture_id": getattr(evaluation, "fixture_id"),
        "residual_context_float64_be": [
            _float64_tag(value) for value in getattr(evaluation, "residual_context")
        ],
        "cardinality": getattr(evaluation, "cardinality"),
        "count_penalty": _fraction_tag(getattr(evaluation, "count_penalty")),
        "exact_log_weight": _fraction_tag(getattr(evaluation, "exact_log_weight")),
        "rounded_exact_log_weight_float64_be": (
            None
            if getattr(evaluation, "rounded_exact_log_weight") is None
            else _float64_tag(getattr(evaluation, "rounded_exact_log_weight"))
        ),
        "direct_binary64_log_weight_float64_be": (
            None
            if getattr(evaluation, "direct_binary64_log_weight") is None
            else _float64_tag(getattr(evaluation, "direct_binary64_log_weight"))
        ),
        "exact_upper_bound_respected": getattr(
            evaluation, "exact_upper_bound_respected"
        ),
        "represented_restriction_identity_verified": getattr(
            evaluation, "represented_restriction_identity_verified"
        ),
    }
    return _owned_leaf(
        b"cp62-test28-source-evaluation-v1",
        body,
        "cp62_source_evaluation_sha256",
    )


def _facade_evaluation_trace(evaluation: object) -> dict:
    rounded = getattr(evaluation, "rounded_log_weight")
    body = {
        "backend_kind": getattr(evaluation, "backend_kind"),
        "residual_context_float64_be": [
            _float64_tag(value) for value in getattr(evaluation, "residual_context")
        ],
        "exact_log_weight": _fraction_tag(getattr(evaluation, "exact_log_weight")),
        "rounded_log_weight_float64_be": (
            None if rounded is None else _float64_tag(rounded)
        ),
        "exact_upper_bound_respected": getattr(
            evaluation, "exact_upper_bound_respected"
        ),
        "exact_lower_bound_respected": getattr(
            evaluation, "exact_lower_bound_respected"
        ),
        "structural_validation_replayed_learned_model": getattr(
            evaluation, "structural_validation_replayed_learned_model"
        ),
        "structural_validation_replayed_rng": getattr(
            evaluation, "structural_validation_replayed_rng"
        ),
        "source_evaluation": _source_evaluation_trace(
            getattr(evaluation, "source_evaluation")
        ),
    }
    return _owned_leaf(
        b"cp62-test28-facade-evaluation-v1",
        body,
        "cp62_facade_evaluation_sha256",
    )


def _scored_trace(scored: object) -> dict:
    rounded = getattr(scored, "rounded_log_weight")
    body = {
        "index": getattr(scored, "index"),
        "configuration": _configuration_trace(getattr(scored, "configuration")),
        "facade_evaluation": _facade_evaluation_trace(getattr(scored, "evaluation")),
        "exact_log_weight": _fraction_tag(getattr(scored, "exact_log_weight")),
        "rounded_log_weight_float64_be": (
            None if rounded is None else _float64_tag(rounded)
        ),
    }
    return _owned_leaf(b"cp62-test28-scored-slot-v1", body, "cp62_scored_sha256")


def _quota_trace(certificate: object) -> dict:
    body = {name: getattr(certificate, name) for name in _QUOTA_TEXT_FIELDS}
    body.update(
        {name: str(getattr(certificate, name)) for name in _QUOTA_INTEGER_FIELDS}
    )
    body.update({name: getattr(certificate, name) for name in _QUOTA_BOOLEAN_FIELDS})
    return _owned_leaf(b"cp62-test28-quota-certificate-v1", body, "cp62_quota_sha256")


def _attempt_trace(attempt: object, index: int) -> dict:
    body = {
        "attempt_index": index,
        "scored": _scored_trace(getattr(attempt, "scored")),
        "exact_delta": _fraction_tag(getattr(attempt, "exact_delta")),
        "quota": _quota_trace(getattr(attempt, "quota_certificate")),
        "decision_word_hex": _integer(
            getattr(attempt, "decision_word"),
            "rejection decision word",
            minimum=0,
            maximum=2**64 - 1,
        )
        .to_bytes(8, "big")
        .hex(),
        "accepted": getattr(attempt, "accepted"),
    }
    return _owned_leaf(b"cp62-test28-rejection-attempt-v1", body, "cp62_attempt_sha256")


def _particle_trace(particle: object, index: int) -> dict:
    body = {
        "particle_index": index,
        "scored": _scored_trace(getattr(particle, "scored")),
        "normalized_weight_float64_be": _float64_tag(
            getattr(particle, "normalized_weight")
        ),
    }
    return _owned_leaf(b"cp62-test28-sir-particle-v1", body, "cp62_particle_sha256")


def _calibration_instance_sha256(row: CP62RequestBindingV1, seed: int) -> str:
    return hashlib.sha256(
        b"cp62-test28-calibration-request-instance-v1\0"
        + bytes.fromhex(row.seed_free_request_sha256)
        + seed.to_bytes(8, "big")
    ).hexdigest()


def _runtime_observation() -> dict:
    import ctypes
    import decimal

    import numpy
    import scipy
    import threadpoolctl

    _verify_runtime_critical_bytes()
    _verify_base_local_source_capsule()
    rounding = int(ctypes.CDLL(None).fegetround())
    observation = {
        "runtime_profile_id": _runtime_lock().runtime_profile_id,
        "runtime_lock_sha256": _runtime_lock().record_sha256,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_soabi": sysconfig.get_config_var("SOABI"),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "machine": platform.machine(),
        "byteorder": sys.byteorder,
        "floating_rounding_mode": "FE_TONEAREST-%d" % rounding,
        "numpy_version": numpy.__version__,
        "scipy_version": scipy.__version__,
        "threadpoolctl_version": threadpoolctl.__version__,
        "decimal_module_version": decimal.__version__,
        "libmpdec_version": decimal.__libmpdec_version__,
        "cp62_source_sha256": _current_source_sha256(),
        "kernel_source_sha256": _loaded_module_sha256(
            "heterodiff.processes.plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2"
        ),
        "reference_source_sha256": _loaded_module_sha256(
            "heterodiff.theory.configuration_reference"
        ),
        "facade_source_sha256": _loaded_module_sha256(
            "heterodiff.processes.certified_initial_score_provider_v1"
        ),
        "exact_score_source_sha256": _loaded_module_sha256(
            "heterodiff.evaluation.exact_rational_quadratic_initial_tilt"
        ),
        "quota_source_sha256": _loaded_module_sha256(
            "heterodiff.processes.arbitrary_rational_uint64_exp_quota"
        ),
        "full_runtime_lock_recomputed": False,
    }
    _validate_runtime_observation(observation)
    return observation


def _loaded_module_sha256(module_name: str) -> str:
    module = sys.modules.get(module_name)
    path = None if module is None else getattr(module, "__file__", None)
    if type(path) is not str:
        raise CP62ExecutionCapsuleError(
            "RUNTIME_SOURCE_MODULE_MISSING",
            "required runtime source module is not loaded",
        )
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _verify_base_local_source_capsule() -> None:
    source_root = Path(__file__).resolve().parents[2]
    current_source = Path(__file__).resolve()
    rows = []
    for module_name, module in tuple(sys.modules.items()):
        if module_name != "heterodiff" and not module_name.startswith("heterodiff."):
            continue
        raw_path = getattr(module, "__file__", None)
        if type(raw_path) is not str:
            continue
        unresolved_path = Path(raw_path)
        if unresolved_path.is_symlink():
            raise CP62ExecutionCapsuleError(
                "LOCAL_SOURCE_FILE_KIND_MISMATCH",
                "a loaded heterodiff source is a symbolic link",
            )
        path = unresolved_path.resolve()
        if path == current_source or path.suffix != ".py":
            continue
        try:
            relative = path.relative_to(source_root)
        except ValueError as error:
            raise CP62ExecutionCapsuleError(
                "LOCAL_SOURCE_PATH_ESCAPE",
                "a loaded heterodiff module lies outside the source capsule",
            ) from error
        if not path.is_file():
            raise CP62ExecutionCapsuleError(
                "LOCAL_SOURCE_FILE_KIND_MISMATCH",
                "a loaded heterodiff source is not a regular file",
            )
        rows.append(
            {
                "module": module_name,
                "path": relative.as_posix(),
                "size": path.stat().st_size,
                "sha256": _file_sha256(path),
            }
        )
    rows.sort(key=lambda row: cast(str, row["module"]))
    payload = json.dumps(
        rows,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    digest = hashlib.sha256(b"cp62-local-source-capsule-v1\0" + payload).hexdigest()
    lock = _runtime_lock()
    if (
        len(rows) != lock.base_local_source_module_count
        or digest != lock.base_local_source_capsule_sha256
    ):
        raise CP62ExecutionCapsuleError(
            "LOCAL_SOURCE_CAPSULE_MISMATCH",
            "loaded local source capsule differs from the frozen candidate",
        )


def _verify_runtime_critical_bytes() -> None:
    import _decimal
    import importlib

    lock = _runtime_lock()
    real_executable = Path(sys.executable).resolve()
    if (
        real_executable.stat().st_size != lock.python_executable_bytes
        or _file_sha256(real_executable) != lock.python_executable_sha256
    ):
        raise CP62ExecutionCapsuleError(
            "RUNTIME_EXECUTABLE_MISMATCH", "Python executable bytes differ"
        )
    framework = real_executable.parent.parent / "Python"
    if (
        framework.stat().st_size != lock.python_framework_bytes
        or _file_sha256(framework) != lock.python_framework_sha256
    ):
        raise CP62ExecutionCapsuleError(
            "RUNTIME_FRAMEWORK_MISMATCH", "Python framework bytes differ"
        )
    native = {
        "_decimal": lock.decimal_extension_sha256,
        "math": lock.math_extension_sha256,
        "numpy._core._multiarray_umath": lock.numpy_multiarray_sha256,
        "numpy.random._philox": lock.numpy_philox_sha256,
        "numpy.random._generator": lock.numpy_generator_sha256,
        "scipy.special._special_ufuncs": lock.scipy_special_ufuncs_sha256,
    }
    del _decimal
    for module_name, expected in native.items():
        module = importlib.import_module(module_name)
        path = getattr(module, "__file__", None)
        if type(path) is not str or _file_sha256(Path(path)) != expected:
            raise CP62ExecutionCapsuleError(
                "RUNTIME_NATIVE_IMAGE_MISMATCH",
                "loaded native image differs: " + module_name,
            )


def _runtime_expected_values() -> Mapping[str, object]:
    lock = _runtime_lock()
    return {
        "runtime_profile_id": lock.runtime_profile_id,
        "runtime_lock_sha256": lock.record_sha256,
        "python_version": lock.python_version,
        "python_implementation": lock.python_implementation,
        "python_soabi": lock.python_soabi,
        "platform_system": lock.platform_system,
        "platform_release": lock.platform_release,
        "machine": lock.machine,
        "byteorder": lock.byteorder,
        "floating_rounding_mode": lock.floating_rounding_mode,
        "numpy_version": lock.numpy_version,
        "scipy_version": lock.scipy_version,
        "threadpoolctl_version": lock.threadpoolctl_version,
        "decimal_module_version": lock.decimal_module_version,
        "libmpdec_version": lock.libmpdec_version,
        "kernel_source_sha256": CP62_TEST28_KERNEL_SOURCE_SHA256,
        "reference_source_sha256": CP62_TEST28_REFERENCE_SOURCE_SHA256,
        "facade_source_sha256": CP62_TEST28_FACADE_SOURCE_SHA256,
        "exact_score_source_sha256": CP62_TEST28_EXACT_SCORE_SOURCE_SHA256,
        "quota_source_sha256": CP62_TEST28_QUOTA_SOURCE_SHA256,
        "full_runtime_lock_recomputed": False,
    }


def _validate_runtime_observation(value: object) -> dict:
    checked = _exact_keys(value, _RUNTIME_OBSERVATION_KEYS, "runtime observation")
    for name, expected in _runtime_expected_values().items():
        supplied = checked[name]
        if type(supplied) is not type(expected) or supplied != expected:
            raise ValueError("runtime observation %s differs" % name)
    _sha256(checked["cp62_source_sha256"], "CP62 source observation")
    if checked["cp62_source_sha256"] != _current_source_sha256():
        raise ValueError("runtime observation CP62 source bytes differ")
    return checked


def _kernel_semantic_trace(
    case: CP62CalibrationCaseV1,
    row: CP62RequestBindingV1,
    kernel: object,
    result: object,
) -> dict:
    certificate = getattr(kernel, "certificate")
    result_status = getattr(result, "status")
    attempts = []
    particles = []
    normalized_weights = []
    decision_initial = None
    decision_final = None
    resampling_initial = None
    resampling_final = None
    resampling_word = None
    resampling_uniform = None
    effective_sample_size = None
    maximum_weight = None
    ess_warning = None
    if row.strategy == "bounded-rejection":
        attempts = [
            _attempt_trace(attempt, index)
            for index, attempt in enumerate(getattr(result, "attempts"))
        ]
        decision_initial = getattr(result, "decision_stream_initial_state_sha256")
        decision_final = getattr(result, "decision_stream_final_state_sha256")
    else:
        particles = [
            _particle_trace(particle, index)
            for index, particle in enumerate(getattr(result, "particles"))
        ]
        normalized_weights = [
            _float64_tag(value) for value in getattr(result, "normalized_weights")
        ]
        resampling_initial = getattr(result, "resampling_stream_initial_state_sha256")
        resampling_final = getattr(result, "resampling_stream_final_state_sha256")
        resampling_word = (
            _integer(
                getattr(result, "resampling_word"),
                "resampling word",
                minimum=0,
                maximum=2**64 - 1,
            )
            .to_bytes(8, "big")
            .hex()
        )
        resampling_uniform = getattr(result, "resampling_uniform_53")
        effective_sample_size = _float64_tag(getattr(result, "effective_sample_size"))
        maximum_weight = _float64_tag(getattr(result, "maximum_normalized_weight"))
        ess_warning = getattr(result, "ess_warning")
    selected_configuration = getattr(result, "selected_configuration")
    lower_bound = getattr(certificate, "exact_log_weight_lower_bound")
    body = {
        "trace_schema": "cp62-test28-stable-kernel-trace-v1",
        "stable_request_sha256": row.seed_free_request_sha256,
        "calibration_instance_sha256": _calibration_instance_sha256(
            row, case.seed_uint64
        ),
        "plan_seed_hex": case.seed_hex,
        "fixture_id": row.fixture_id,
        "strategy": row.strategy,
        "budget": row.budget,
        "source_certificate_sha256": row.source_certificate_sha256,
        "source_parameter_sha256": row.source_parameter_sha256,
        "reference_parameter_sha256": row.reference_parameter_sha256,
        "facade_certificate_sha256": row.facade_certificate_sha256,
        "adapter_role_sha256": row.adapter_role_sha256,
        "initializer_role_sha256": row.initializer_role_sha256,
        "residual_context_sha256": row.residual_context_sha256,
        "runtime_observation": _runtime_observation(),
        "exact_log_weight_upper_bound": _fraction_tag(
            getattr(certificate, "exact_log_weight_upper_bound")
        ),
        "exact_log_weight_lower_bound": (
            None if lower_bound is None else _fraction_tag(lower_bound)
        ),
        "proposal_seed_hex": getattr(certificate, "proposal_seed")
        .to_bytes(8, "big")
        .hex(),
        "rejection_decision_seed_hex": (
            None
            if getattr(certificate, "rejection_decision_seed") is None
            else getattr(certificate, "rejection_decision_seed")
            .to_bytes(8, "big")
            .hex()
        ),
        "sir_resampling_seed_hex": (
            None
            if getattr(certificate, "sir_resampling_seed") is None
            else getattr(certificate, "sir_resampling_seed").to_bytes(8, "big").hex()
        ),
        "resource_preflight": {
            "mode": getattr(certificate, "resource_preflight_mode"),
            "reference_occurrence_limit": getattr(
                certificate, "reference_occurrence_limit"
            ),
            "reference_coordinate_limit": getattr(
                certificate, "reference_coordinate_limit"
            ),
            "worst_case_occurrences": getattr(certificate, "worst_case_occurrences"),
            "worst_case_coordinates": getattr(certificate, "worst_case_coordinates"),
            "fixed_budget_work_certified": getattr(
                certificate, "fixed_budget_work_certified"
            ),
            "arbitrary_rational_quota_required": getattr(
                certificate, "arbitrary_rational_quota_required"
            ),
        },
        "explicit_rejection_exhaustion": getattr(
            certificate, "explicit_rejection_exhaustion"
        ),
        "structural_result_validation_replays_provider_evaluate": getattr(
            certificate, "structural_result_validation_replays_provider_evaluate"
        ),
        "structural_result_validation_replays_provider_evaluate_or_source_public_validate_evaluation": getattr(
            certificate,
            "structural_result_validation_replays_provider_evaluate_or_source_public_validate_evaluation",
        ),
        "structural_result_validation_replays_reference_sampler": getattr(
            certificate, "structural_result_validation_replays_reference_sampler"
        ),
        "structural_result_validation_replays_rng": getattr(
            certificate, "structural_result_validation_replays_rng"
        ),
        "operational_reference_sampling_law_verified": getattr(
            certificate, "operational_reference_sampling_law_verified"
        ),
        "philox_uniformity_verified": getattr(
            certificate, "philox_uniformity_verified"
        ),
        "stream_independence_verified": getattr(
            certificate, "stream_independence_verified"
        ),
        "iid_proposals_verified": getattr(certificate, "iid_proposals_verified"),
        "analytic_target_equality_verified": getattr(
            certificate, "analytic_target_equality_verified"
        ),
        "exact_operational_rejection_bernoulli_verified": getattr(
            certificate, "exact_operational_rejection_bernoulli_verified"
        ),
        "finite_j_sir_exact_target_verified": getattr(
            certificate, "finite_j_sir_exact_target_verified"
        ),
        "source_or_model_quality_evidence": getattr(
            certificate, "source_or_model_quality_evidence"
        ),
        "path_or_sampler_admitted": getattr(certificate, "path_or_sampler_admitted"),
        "formal_test_28_closed": getattr(certificate, "formal_test_28_closed"),
        "result_status": result_status,
        "proposal_stream_initial_state_sha256": getattr(
            result, "proposal_stream_initial_state_sha256"
        ),
        "proposal_stream_final_state_sha256": getattr(
            result, "proposal_stream_final_state_sha256"
        ),
        "decision_stream_initial_state_sha256": decision_initial,
        "decision_stream_final_state_sha256": decision_final,
        "resampling_stream_initial_state_sha256": resampling_initial,
        "resampling_stream_final_state_sha256": resampling_final,
        "resampling_word_hex": resampling_word,
        "resampling_uniform_53": resampling_uniform,
        "effective_sample_size_float64_be": effective_sample_size,
        "maximum_normalized_weight_float64_be": maximum_weight,
        "ess_warning": ess_warning,
        "attempts": attempts,
        "particles": particles,
        "normalized_weights_float64_be": normalized_weights,
        "selected_index": getattr(result, "selected_index"),
        "selected_configuration": (
            None
            if selected_configuration is None
            else _configuration_trace(selected_configuration)
        ),
    }
    return _owned_leaf(
        b"cp62-test28-semantic-kernel-trace-v1",
        body,
        "cp62_semantic_trace_sha256",
    )


def _kernel_volatile_custody(kernel: object, result: object) -> dict:
    nested = []
    if hasattr(result, "attempts"):
        for index, attempt in enumerate(getattr(result, "attempts")):
            nested.append(
                {
                    "slot_index": index,
                    "slot_kind": "rejection-attempt",
                    "configuration_sha256": getattr(
                        attempt.scored, "configuration_sha256"
                    ),
                    "source_evaluation_sha256": getattr(
                        attempt.scored.evaluation, "source_evaluation_sha256"
                    ),
                    "facade_evaluation_sha256": getattr(
                        attempt.scored, "evaluation_sha256"
                    ),
                    "scored_sha256": getattr(
                        attempt.scored, "scored_configuration_sha256"
                    ),
                    "quota_sha256": getattr(
                        attempt.quota_certificate, "certificate_sha256"
                    ),
                    "attempt_sha256": getattr(attempt, "attempt_sha256"),
                    "particle_sha256": None,
                }
            )
    if hasattr(result, "particles"):
        for index, particle in enumerate(getattr(result, "particles")):
            nested.append(
                {
                    "slot_index": index,
                    "slot_kind": "sir-particle",
                    "configuration_sha256": getattr(
                        particle.scored, "configuration_sha256"
                    ),
                    "source_evaluation_sha256": getattr(
                        particle.scored.evaluation, "source_evaluation_sha256"
                    ),
                    "facade_evaluation_sha256": getattr(
                        particle.scored, "evaluation_sha256"
                    ),
                    "scored_sha256": getattr(
                        particle.scored, "scored_configuration_sha256"
                    ),
                    "quota_sha256": None,
                    "attempt_sha256": None,
                    "particle_sha256": getattr(particle, "particle_sha256"),
                }
            )
    certificate = getattr(kernel, "certificate")
    plan = getattr(kernel, "plan")
    return {
        "plan_sha256": getattr(plan, "plan_sha256"),
        "kernel_certificate_sha256": getattr(certificate, "certificate_sha256"),
        "result_sha256": getattr(result, "result_sha256"),
        "provider_runtime_identity": getattr(plan, "provider_runtime_identity"),
        "reference_runtime_identity": getattr(
            certificate, "reference_runtime_identity"
        ),
        "nested_record_custody": nested,
    }


def _recompute_fixture_score(
    row: CP62RequestBindingV1, configuration: dict
) -> Tuple[Fraction, float, float, Fraction]:
    events = configuration["events"]
    cap = 1 if row.fixture_id == "T28-M1-Q" else 2
    if len(events) > cap:
        raise ValueError("configuration exceeds fixture cap")
    count_penalty = (
        Fraction(-1, 4)
        if row.fixture_id == "T28-M2-Q" and len(events) == 2
        else Fraction(0, 1)
    )
    exact = count_penalty
    direct = float(count_penalty)
    prior = None
    for event in events:
        event_type = event["event_type"]
        coordinates = [
            _validate_float64_tag(item, "configuration coordinate")
            for item in event["coordinates_float64_be"]
        ]
        expected_dimension = (
            0
            if row.fixture_id == "T28-M1-Q" and event_type == 0
            else 1
            if row.fixture_id == "T28-M1-Q" and event_type == 1
            else 1
            if row.fixture_id == "T28-M2-Q" and event_type == 0
            else 2
            if row.fixture_id == "T28-M2-Q" and event_type == 1
            else -1
        )
        if expected_dimension < 0 or len(coordinates) != expected_dimension:
            raise ValueError("configuration type/dimension differs from fixture")
        ordering_key = (event_type, tuple(coordinates))
        if prior is not None and ordering_key < prior:
            raise ValueError(
                "configuration ordering differs from fixture canonical form"
            )
        prior = ordering_key
        coefficients = (
            ()
            if expected_dimension == 0
            else (Fraction(1, 4),)
            if row.fixture_id == "T28-M1-Q" or event_type == 0
            else (Fraction(1, 8), Fraction(1, 6))
        )
        for coefficient, coordinate in zip(coefficients, coordinates):
            exact -= coefficient * Fraction.from_float(coordinate) ** 2
            direct -= float(coefficient) * (coordinate * coordinate)
    if direct == 0.0:
        direct = 0.0
    rounded = float(exact)
    if rounded == 0.0:
        rounded = 0.0
    return exact, rounded, direct, count_penalty


def _validate_configuration_trace(value: object, name: str) -> dict:
    checked = _exact_keys(value, _CONFIGURATION_KEYS, name)
    events = checked["events"]
    if type(events) is not list or len(events) > 4_096:
        raise TypeError(name + " events must be a bounded exact list")
    prior = None
    for event_index, event in enumerate(events):
        item = _exact_keys(
            event,
            ("event_type", "coordinates_float64_be"),
            "%s event %d" % (name, event_index),
        )
        event_type = _json_integer(
            item["event_type"],
            "%s event type" % name,
            minimum=0,
            maximum=2**31 - 1,
        )
        coordinates = item["coordinates_float64_be"]
        if type(coordinates) is not list or len(coordinates) > 4_096:
            raise TypeError(name + " coordinates must be a bounded exact list")
        coordinate_values = []
        for coordinate_index, coordinate in enumerate(coordinates):
            coordinate_values.append(
                _validate_float64_tag(
                    coordinate,
                    "%s coordinate %d" % (name, coordinate_index),
                )
            )
        ordering_key = (event_type, tuple(coordinate_values))
        if prior is not None and ordering_key < prior:
            raise ValueError(name + " events are noncanonical")
        prior = ordering_key
    _verify_owned_leaf(
        checked,
        field="cp62_configuration_sha256",
        domain=b"cp62-test28-configuration-v1",
        name=name,
    )
    return checked


def _validate_source_evaluation_trace(
    value: object,
    name: str,
    *,
    row: CP62RequestBindingV1,
    configuration: dict,
) -> dict:
    checked = _exact_keys(value, _SOURCE_EVALUATION_KEYS, name)
    if checked["fixture_id"] != row.fixture_id:
        raise ValueError(name + " fixture differs")
    context = checked["residual_context_float64_be"]
    if type(context) is not list or len(context) > 4_096:
        raise TypeError(name + " context must be a bounded exact list")
    for index, item in enumerate(context):
        _validate_float64_tag(item, "%s context %d" % (name, index))
    if context:
        raise ValueError(name + " residual context is not empty")
    _json_integer(
        checked["cardinality"], name + " cardinality", minimum=0, maximum=4_096
    )
    exact, rounded, direct, penalty = _recompute_fixture_score(row, configuration)
    if checked["cardinality"] != len(configuration["events"]):
        raise ValueError(name + " cardinality differs from configuration")
    if (
        _validate_fraction_tag(checked["count_penalty"], name + " count penalty")
        != penalty
    ):
        raise ValueError(name + " count penalty differs")
    if (
        _validate_fraction_tag(checked["exact_log_weight"], name + " exact score")
        != exact
    ):
        raise ValueError(name + " exact score differs from independent formula")
    rounded_supplied = _validate_optional_float64_tag(
        checked["rounded_exact_log_weight_float64_be"], name + " rounded score"
    )
    direct_supplied = _validate_optional_float64_tag(
        checked["direct_binary64_log_weight_float64_be"], name + " direct score"
    )
    if rounded_supplied != rounded or direct_supplied != direct:
        raise ValueError(name + " binary64 score layer differs")
    if (
        _json_boolean(
            checked["exact_upper_bound_respected"], name + " upper-bound flag"
        )
        is not True
    ):
        raise ValueError(name + " upper-bound flag differs")
    if (
        _json_boolean(
            checked["represented_restriction_identity_verified"],
            name + " restriction flag",
        )
        is not True
    ):
        raise ValueError(name + " restriction flag differs")
    _verify_owned_leaf(
        checked,
        field="cp62_source_evaluation_sha256",
        domain=b"cp62-test28-source-evaluation-v1",
        name=name,
    )
    return checked


def _validate_facade_evaluation_trace(
    value: object,
    name: str,
    *,
    row: CP62RequestBindingV1,
    configuration: dict,
) -> dict:
    checked = _exact_keys(value, _FACADE_EVALUATION_KEYS, name)
    if checked["backend_kind"] != "exact-rational-quadratic-initial-tilt-v1":
        raise ValueError(name + " backend kind differs")
    context = checked["residual_context_float64_be"]
    if type(context) is not list or len(context) > 4_096:
        raise TypeError(name + " context must be a bounded exact list")
    for index, item in enumerate(context):
        _validate_float64_tag(item, "%s context %d" % (name, index))
    if context:
        raise ValueError(name + " residual context is not empty")
    exact = _validate_fraction_tag(checked["exact_log_weight"], name + " exact score")
    _validate_optional_float64_tag(
        checked["rounded_log_weight_float64_be"], name + " rounded score"
    )
    if (
        _json_boolean(
            checked["exact_upper_bound_respected"], name + " upper-bound flag"
        )
        is not True
    ):
        raise ValueError(name + " upper-bound flag differs")
    if checked["exact_lower_bound_respected"] is not None:
        raise ValueError(name + " lower-bound flag must be absent")
    for field in (
        "structural_validation_replayed_learned_model",
        "structural_validation_replayed_rng",
    ):
        if _json_boolean(checked[field], name + " " + field):
            raise ValueError(name + " structural replay nonclaim differs")
    source = _validate_source_evaluation_trace(
        checked["source_evaluation"],
        name + " source evaluation",
        row=row,
        configuration=configuration,
    )
    if (
        _validate_fraction_tag(source["exact_log_weight"], name + " source exact score")
        != exact
    ):
        raise ValueError(name + " facade/source exact scores differ")
    source_rounded = _validate_optional_float64_tag(
        source["rounded_exact_log_weight_float64_be"],
        name + " source rounded score",
    )
    if (
        _validate_optional_float64_tag(
            checked["rounded_log_weight_float64_be"], name + " rounded score replay"
        )
        != source_rounded
    ):
        raise ValueError(name + " facade/source rounded scores differ")
    _verify_owned_leaf(
        checked,
        field="cp62_facade_evaluation_sha256",
        domain=b"cp62-test28-facade-evaluation-v1",
        name=name,
    )
    return checked


def _validate_scored_trace(
    value: object,
    *,
    index: int,
    name: str,
    row: CP62RequestBindingV1,
) -> dict:
    checked = _exact_keys(value, _SCORED_KEYS, name)
    if (
        _json_integer(checked["index"], name + " index", minimum=0, maximum=4_096)
        != index
    ):
        raise ValueError(name + " index differs from position")
    configuration = _validate_configuration_trace(
        checked["configuration"], name + " configuration"
    )
    evaluation = _validate_facade_evaluation_trace(
        checked["facade_evaluation"],
        name + " facade evaluation",
        row=row,
        configuration=configuration,
    )
    exact = _validate_fraction_tag(checked["exact_log_weight"], name + " exact score")
    if (
        _validate_fraction_tag(
            evaluation["exact_log_weight"], name + " facade exact score"
        )
        != exact
    ):
        raise ValueError(name + " scored/facade exact scores differ")
    rounded = _validate_optional_float64_tag(
        checked["rounded_log_weight_float64_be"], name + " rounded score"
    )
    facade_rounded = _validate_optional_float64_tag(
        evaluation["rounded_log_weight_float64_be"],
        name + " facade rounded score",
    )
    if rounded != facade_rounded:
        raise ValueError(name + " scored/facade rounded scores differ")
    _verify_owned_leaf(
        checked,
        field="cp62_scored_sha256",
        domain=b"cp62-test28-scored-slot-v1",
        name=name,
    )
    return checked


def _validate_quota_trace(value: object, name: str) -> dict:
    checked = _exact_keys(value, _QUOTA_KEYS, name)
    for field in _QUOTA_TEXT_FIELDS:
        _text(checked[field], name + " " + field)
    integers = {}
    for field in _QUOTA_INTEGER_FIELDS:
        minimum = 1 if field.endswith("denominator") else None
        integers[field] = _decimal_integer_text(
            checked[field], name + " " + field, minimum=minimum
        )
    if integers["decision_denominator"] != 2**64:
        raise ValueError(name + " decision denominator differs")
    if integers["quota"] < 0 or integers["quota"] > 2**64:
        raise ValueError(name + " quota lies outside [0,2^64]")
    delta = Fraction(integers["delta_numerator"], integers["delta_denominator"])
    if (
        delta.numerator != integers["delta_numerator"]
        or delta.denominator != integers["delta_denominator"]
    ):
        raise ValueError(name + " delta parts are noncanonical")
    for field in _QUOTA_BOOLEAN_FIELDS:
        _json_boolean(checked[field], name + " " + field)
    _verify_owned_leaf(
        checked,
        field="cp62_quota_sha256",
        domain=b"cp62-test28-quota-certificate-v1",
        name=name,
    )
    return checked


def _validate_attempt_trace(
    value: object,
    *,
    index: int,
    name: str,
    row: CP62RequestBindingV1,
) -> dict:
    checked = _exact_keys(value, _ATTEMPT_KEYS, name)
    if (
        _json_integer(
            checked["attempt_index"], name + " index", minimum=0, maximum=4_096
        )
        != index
    ):
        raise ValueError(name + " index differs from position")
    scored = _validate_scored_trace(
        checked["scored"], index=index, name=name + " scored slot", row=row
    )
    delta = _validate_fraction_tag(checked["exact_delta"], name + " delta")
    quota = _validate_quota_trace(checked["quota"], name + " quota")
    quota_delta = Fraction(
        _decimal_integer_text(quota["delta_numerator"], name + " quota numerator"),
        _decimal_integer_text(
            quota["delta_denominator"], name + " quota denominator", minimum=1
        ),
    )
    if delta != quota_delta:
        raise ValueError(name + " delta and quota input differ")
    word_hex = _uint64_hex(checked["decision_word_hex"], name + " decision word")
    accepted = _json_boolean(checked["accepted"], name + " accepted")
    quota_value = _decimal_integer_text(
        quota["quota"], name + " quota value", minimum=0
    )
    if accepted != (int(word_hex, 16) < quota_value):
        raise ValueError(name + " acceptance differs from word/quota comparison")
    scored_exact = _validate_fraction_tag(
        scored["exact_log_weight"], name + " scored exact score"
    )
    if scored_exact != delta:
        raise ValueError(name + " delta differs from q-U for frozen U=0")
    from heterodiff.processes.arbitrary_rational_uint64_exp_quota import (
        certify_arbitrary_rational_uint64_exp_quota,
    )

    if _quota_trace(certify_arbitrary_rational_uint64_exp_quota(delta)) != quota:
        raise ValueError(name + " quota differs from exact clean replay")
    _verify_owned_leaf(
        checked,
        field="cp62_attempt_sha256",
        domain=b"cp62-test28-rejection-attempt-v1",
        name=name,
    )
    return checked


def _validate_particle_trace(
    value: object,
    *,
    index: int,
    name: str,
    row: CP62RequestBindingV1,
) -> dict:
    checked = _exact_keys(value, _PARTICLE_KEYS, name)
    if (
        _json_integer(
            checked["particle_index"], name + " index", minimum=0, maximum=4_096
        )
        != index
    ):
        raise ValueError(name + " index differs from position")
    _validate_scored_trace(
        checked["scored"], index=index, name=name + " scored slot", row=row
    )
    weight = _validate_float64_tag(
        checked["normalized_weight_float64_be"], name + " normalized weight"
    )
    if not 0.0 < weight <= 1.0:
        raise ValueError(name + " normalized weight lies outside (0,1]")
    _verify_owned_leaf(
        checked,
        field="cp62_particle_sha256",
        domain=b"cp62-test28-sir-particle-v1",
        name=name,
    )
    return checked


def _validate_resource_preflight(value: object, *, row: CP62RequestBindingV1) -> dict:
    checked = _exact_keys(value, _RESOURCE_PREFLIGHT_KEYS, "resource preflight")
    if checked["mode"] != "stochastic-worst-case":
        raise ValueError("resource preflight mode differs")
    for field in (
        "reference_occurrence_limit",
        "reference_coordinate_limit",
        "worst_case_occurrences",
        "worst_case_coordinates",
    ):
        _json_integer(
            checked[field], "resource preflight " + field, minimum=0, maximum=2**31
        )
    if (
        checked["reference_occurrence_limit"] != 500_000
        or checked["reference_coordinate_limit"] != 4_000_000
    ):
        raise ValueError("resource preflight global limits differ")
    if checked["worst_case_occurrences"] != row.budget * (
        1 if row.fixture_id == "T28-M1-Q" else 2
    ):
        raise ValueError("resource preflight occurrence work differs")
    if checked["worst_case_coordinates"] != row.budget * (
        1 if row.fixture_id == "T28-M1-Q" else 4
    ):
        raise ValueError("resource preflight coordinate work differs")
    if (
        _json_boolean(
            checked["fixed_budget_work_certified"],
            "fixed-budget work certification",
        )
        is not True
    ):
        raise ValueError("fixed-budget work is not certified")
    quota_required = _json_boolean(
        checked["arbitrary_rational_quota_required"],
        "quota requirement",
    )
    if quota_required != (row.strategy == "bounded-rejection"):
        raise ValueError("quota requirement differs from strategy")
    return checked


def _derive_stream_seed(
    case: CP62CalibrationCaseV1,
    row: CP62RequestBindingV1,
    stream_role: str,
) -> int:
    digest = hashlib.sha256(
        b"heterodiff-mixed-support-initializer-derived-stream-v2\x00"
    )
    digest.update(row.strategy.encode("ascii") + b"\x00")
    digest.update(stream_role.encode("ascii") + b"\x00")
    digest.update(case.seed_uint64.to_bytes(8, "big"))
    digest.update(bytes.fromhex(row.initializer_role_sha256))
    digest.update(bytes.fromhex(row.residual_context_sha256))
    digest.update(bytes.fromhex(row.facade_certificate_sha256))
    if stream_role == "sir-resampling":
        digest.update(b"sir-particle-budget\x00")
        digest.update(row.budget.to_bytes(8, "big"))
    else:
        digest.update(b"no-particle-budget\x00")
    result = int.from_bytes(digest.digest()[:8], "big")
    return result ^ (1 << 63) if result == case.seed_uint64 else result


def _expected_stream_seeds(
    case: CP62CalibrationCaseV1, row: CP62RequestBindingV1
) -> Tuple[int, Optional[int], Optional[int]]:
    proposal = _derive_stream_seed(case, row, "proposal")
    used = {case.seed_uint64, proposal}

    def unique(candidate: int) -> int:
        while candidate in used:
            candidate = (candidate + 1) % (1 << 64)
        used.add(candidate)
        return candidate

    if row.strategy == "bounded-rejection":
        return (
            proposal,
            unique(_derive_stream_seed(case, row, "rejection-decision")),
            None,
        )
    return proposal, None, unique(_derive_stream_seed(case, row, "sir-resampling"))


def _closed_semantic_trace(
    case: CP62CalibrationCaseV1,
    row: CP62RequestBindingV1,
    *,
    outcome_kind: str,
    failure_code: Optional[str],
    runtime_observation: Optional[dict],
) -> dict:
    body = {
        "trace_schema": "cp62-test28-closed-kernel-outcome-v1",
        "stable_request_sha256": row.seed_free_request_sha256,
        "calibration_instance_sha256": _calibration_instance_sha256(
            row, case.seed_uint64
        ),
        "plan_seed_hex": case.seed_hex,
        "fixture_id": row.fixture_id,
        "strategy": row.strategy,
        "budget": row.budget,
        "source_certificate_sha256": row.source_certificate_sha256,
        "source_parameter_sha256": row.source_parameter_sha256,
        "reference_parameter_sha256": row.reference_parameter_sha256,
        "facade_certificate_sha256": row.facade_certificate_sha256,
        "adapter_role_sha256": row.adapter_role_sha256,
        "initializer_role_sha256": row.initializer_role_sha256,
        "residual_context_sha256": row.residual_context_sha256,
        "runtime_lock_sha256": _runtime_lock().record_sha256,
        "runtime_observation": runtime_observation,
        "outcome_kind": outcome_kind,
        "failure_code": failure_code,
        "completed_kernel_trace_present": False,
        "timeout_is_semantic_nonreturn": False,
    }
    return _owned_leaf(
        b"cp62-test28-closed-kernel-outcome-v1",
        body,
        "cp62_closed_trace_sha256",
    )


def _validate_closed_semantic_trace(
    value: object,
    *,
    case: CP62CalibrationCaseV1,
    row: CP62RequestBindingV1,
    outcome_kind: str,
    failure_code: Optional[str],
) -> dict:
    checked = _exact_keys(
        value, _CLOSED_SEMANTIC_TRACE_KEYS, "closed semantic kernel trace"
    )
    exact = _closed_semantic_trace(
        case,
        row,
        outcome_kind=outcome_kind,
        failure_code=failure_code,
        runtime_observation=checked["runtime_observation"],
    )
    observation = checked["runtime_observation"]
    if observation is not None:
        _validate_runtime_observation(observation)
    if _plain_json_bytes(checked) != _plain_json_bytes(exact):
        raise ValueError("closed semantic kernel trace differs from frozen replay")
    return checked


def _validate_semantic_trace(
    value: object,
    *,
    case: CP62CalibrationCaseV1,
    row: CP62RequestBindingV1,
    closed_status: str,
) -> dict:
    checked = _exact_keys(value, _SEMANTIC_TRACE_KEYS, "semantic kernel trace")
    exact_common = {
        "trace_schema": "cp62-test28-stable-kernel-trace-v1",
        "stable_request_sha256": row.seed_free_request_sha256,
        "calibration_instance_sha256": _calibration_instance_sha256(
            row, case.seed_uint64
        ),
        "plan_seed_hex": case.seed_hex,
        "fixture_id": row.fixture_id,
        "strategy": row.strategy,
        "budget": row.budget,
        "source_certificate_sha256": row.source_certificate_sha256,
        "source_parameter_sha256": row.source_parameter_sha256,
        "reference_parameter_sha256": row.reference_parameter_sha256,
        "facade_certificate_sha256": row.facade_certificate_sha256,
        "adapter_role_sha256": row.adapter_role_sha256,
        "initializer_role_sha256": row.initializer_role_sha256,
        "residual_context_sha256": row.residual_context_sha256,
    }
    for field, expected in exact_common.items():
        if type(checked[field]) is not type(expected) or checked[field] != expected:
            raise ValueError("semantic trace %s differs" % field)
    _validate_runtime_observation(checked["runtime_observation"])
    upper = _validate_fraction_tag(
        checked["exact_log_weight_upper_bound"], "exact log-weight upper bound"
    )
    if upper != 0:
        raise ValueError("frozen exact log-weight upper bound differs")
    lower_value = checked["exact_log_weight_lower_bound"]
    if lower_value is not None:
        raise ValueError("frozen exact log-weight lower bound must be absent")
    proposal_seed, decision_seed, resampling_seed = _expected_stream_seeds(case, row)
    expected_seed_fields = {
        "proposal_seed_hex": proposal_seed.to_bytes(8, "big").hex(),
        "rejection_decision_seed_hex": (
            None if decision_seed is None else decision_seed.to_bytes(8, "big").hex()
        ),
        "sir_resampling_seed_hex": (
            None
            if resampling_seed is None
            else resampling_seed.to_bytes(8, "big").hex()
        ),
    }
    for field, wanted in expected_seed_fields.items():
        actual = checked[field]
        if type(actual) is not type(wanted) or actual != wanted:
            raise ValueError("semantic derived stream seed differs")
    _validate_resource_preflight(checked["resource_preflight"], row=row)
    if _json_boolean(
        checked["explicit_rejection_exhaustion"],
        "explicit rejection exhaustion",
    ) != (row.strategy == "bounded-rejection"):
        raise ValueError("explicit rejection exhaustion flag differs")
    for field in (
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
    ):
        if _json_boolean(checked[field], "semantic trace " + field):
            raise ValueError("semantic nonclaim flag %s differs" % field)
    _sha256(
        checked["proposal_stream_initial_state_sha256"],
        "proposal initial state",
    )
    _sha256(
        checked["proposal_stream_final_state_sha256"],
        "proposal final state",
    )
    attempts = checked["attempts"]
    particles = checked["particles"]
    weights = checked["normalized_weights_float64_be"]
    if (
        type(attempts) is not list
        or type(particles) is not list
        or type(weights) is not list
    ):
        raise TypeError("semantic trace slot collections must be exact lists")
    selected_index = _json_optional_integer(
        checked["selected_index"],
        "selected index",
        minimum=0,
        maximum=row.budget - 1,
    )
    selected_configuration = checked["selected_configuration"]
    if row.strategy == "bounded-rejection":
        if checked["result_status"] not in ("selected", "exhausted"):
            raise ValueError("rejection result status differs")
        expected_closed = (
            "returned-rejection-selected-before-deadline"
            if checked["result_status"] == "selected"
            else "returned-rejection-exhausted-before-deadline"
        )
        if closed_status != expected_closed:
            raise ValueError("rejection outer/inner status differs")
        _uint64_hex(checked["rejection_decision_seed_hex"], "rejection decision seed")
        if checked["sir_resampling_seed_hex"] is not None:
            raise ValueError("rejection trace has a resampling seed")
        for field in (
            "resampling_stream_initial_state_sha256",
            "resampling_stream_final_state_sha256",
            "resampling_word_hex",
            "resampling_uniform_53",
            "effective_sample_size_float64_be",
            "maximum_normalized_weight_float64_be",
            "ess_warning",
        ):
            if checked[field] is not None:
                raise ValueError("rejection trace has an inapplicable SIR field")
        _sha256(
            checked["decision_stream_initial_state_sha256"],
            "decision initial state",
        )
        _sha256(
            checked["decision_stream_final_state_sha256"],
            "decision final state",
        )
        if len(attempts) != row.budget or particles or weights:
            raise ValueError("rejection slot collection length differs")
        validated_attempts = [
            _validate_attempt_trace(
                item, index=index, name="attempt %d" % index, row=row
            )
            for index, item in enumerate(attempts)
        ]
        if checked["result_status"] == "selected":
            if selected_index is None or selected_configuration is None:
                raise ValueError("selected rejection trace lacks selection")
            for index in range(selected_index):
                if validated_attempts[index]["accepted"]:
                    raise ValueError("selected rejection index is not first accepted")
            if not validated_attempts[selected_index]["accepted"]:
                raise ValueError("selected rejection attempt was not accepted")
            selected = _validate_configuration_trace(
                selected_configuration, "selected configuration"
            )
            if (
                selected
                != validated_attempts[selected_index]["scored"]["configuration"]
            ):
                raise ValueError("selected rejection configuration differs")
        else:
            if selected_index is not None or selected_configuration is not None:
                raise ValueError("exhausted rejection trace retains a selection")
            if any(item["accepted"] for item in validated_attempts):
                raise ValueError("exhausted rejection trace has an accepted attempt")
    else:
        if (
            checked["result_status"] != "selected"
            or closed_status != "returned-sir-selected-before-deadline"
        ):
            raise ValueError("SIR outer/inner result status differs")
        if checked["rejection_decision_seed_hex"] is not None:
            raise ValueError("SIR trace has a decision seed")
        _uint64_hex(checked["sir_resampling_seed_hex"], "SIR resampling seed")
        for field in (
            "decision_stream_initial_state_sha256",
            "decision_stream_final_state_sha256",
        ):
            if checked[field] is not None:
                raise ValueError("SIR trace has an inapplicable decision field")
        _sha256(
            checked["resampling_stream_initial_state_sha256"],
            "resampling initial state",
        )
        _sha256(
            checked["resampling_stream_final_state_sha256"],
            "resampling final state",
        )
        _uint64_hex(checked["resampling_word_hex"], "resampling word")
        uniform_53 = _json_integer(
            checked["resampling_uniform_53"],
            "resampling uniform53",
            minimum=0,
            maximum=2**53 - 1,
        )
        if uniform_53 != int(checked["resampling_word_hex"], 16) >> 11:
            raise ValueError("SIR uniform53 differs from resampling word")
        ess = _validate_float64_tag(
            checked["effective_sample_size_float64_be"], "effective sample size"
        )
        maximum_weight = _validate_float64_tag(
            checked["maximum_normalized_weight_float64_be"], "maximum weight"
        )
        if not 0.0 < ess <= row.budget or not 0.0 < maximum_weight <= 1.0:
            raise ValueError("SIR aggregate diagnostic lies outside bounds")
        _json_boolean(checked["ess_warning"], "ESS warning")
        if attempts or len(particles) != row.budget or len(weights) != row.budget:
            raise ValueError("SIR slot collection length differs")
        validated_particles = [
            _validate_particle_trace(
                item, index=index, name="particle %d" % index, row=row
            )
            for index, item in enumerate(particles)
        ]
        for index, weight in enumerate(weights):
            _validate_float64_tag(weight, "normalized weight %d" % index)
            if weight != validated_particles[index]["normalized_weight_float64_be"]:
                raise ValueError("SIR weight array and particle weight differ")
        from heterodiff.processes.plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 import (
            normalize_mixed_support_sir_exact_log_weights_v2,
            select_mixed_support_sir_index_v2,
        )

        exact_scores = tuple(
            _validate_fraction_tag(
                particle["scored"]["exact_log_weight"],
                "particle exact score",
            )
            for particle in validated_particles
        )
        expected_weights = normalize_mixed_support_sir_exact_log_weights_v2(
            exact_scores
        )
        expected_weight_tags = [_float64_tag(value) for value in expected_weights]
        if weights != expected_weight_tags:
            raise ValueError("SIR weights differ from frozen normalization replay")
        expected_ess = 1.0 / math.fsum(
            float(value * value) for value in expected_weights
        )
        expected_maximum_weight = max(float(value) for value in expected_weights)
        if ess != expected_ess or maximum_weight != expected_maximum_weight:
            raise ValueError("SIR aggregate diagnostics differ from weights")
        if checked["ess_warning"] != (expected_ess < 0.25 * row.budget):
            raise ValueError("SIR warning differs from frozen threshold")
        expected_selected = select_mixed_support_sir_index_v2(
            expected_weights, int(checked["resampling_word_hex"], 16)
        )
        if selected_index != expected_selected:
            raise ValueError("SIR selected index differs from right-sided selector")
        if selected_index is None or selected_configuration is None:
            raise ValueError("SIR trace lacks a selection")
        selected = _validate_configuration_trace(
            selected_configuration, "selected configuration"
        )
        if selected != validated_particles[selected_index]["scored"]["configuration"]:
            raise ValueError("selected SIR configuration differs")
    _verify_owned_leaf(
        checked,
        field="cp62_semantic_trace_sha256",
        domain=b"cp62-test28-semantic-kernel-trace-v1",
        name="semantic kernel trace",
    )
    return checked


def _validate_volatile_custody(value: object) -> dict:
    checked = _exact_keys(value, _VOLATILE_CUSTODY_KEYS, "volatile kernel custody")
    for field in ("plan_sha256", "kernel_certificate_sha256", "result_sha256"):
        _sha256(checked[field], "volatile " + field)
    _json_integer(
        checked["provider_runtime_identity"],
        "provider runtime identity",
        minimum=0,
        maximum=2**64 - 1,
    )
    _json_integer(
        checked["reference_runtime_identity"],
        "reference runtime identity",
        minimum=0,
        maximum=2**64 - 1,
    )
    nested = checked["nested_record_custody"]
    if type(nested) is not list or len(nested) > 4_096:
        raise TypeError("nested record custody must be a bounded exact list")
    for index, value in enumerate(nested):
        item = _exact_keys(
            value, _NESTED_CUSTODY_KEYS, "nested record custody %d" % index
        )
        if item["slot_index"] != index or item["slot_kind"] not in (
            "rejection-attempt",
            "sir-particle",
        ):
            raise ValueError("nested record custody slot differs")
        for field in (
            "configuration_sha256",
            "source_evaluation_sha256",
            "facade_evaluation_sha256",
            "scored_sha256",
            "quota_sha256",
            "attempt_sha256",
            "particle_sha256",
        ):
            _json_optional_sha256(item[field], "nested custody " + field)
    return checked


def _validate_supervisor_custody(value: object) -> dict:
    checked = _exact_keys(value, _SUPERVISOR_CUSTODY_KEYS, "supervisor custody")
    for field in ("pid", "process_group"):
        _json_integer(
            checked[field], "supervisor " + field, minimum=1, maximum=2**63 - 1
        )
    start = _decimal_integer_text(
        checked["start_monotonic_ns"], "supervisor start", minimum=0
    )
    deadline = _decimal_integer_text(
        checked["deadline_monotonic_ns"], "supervisor deadline", minimum=0
    )
    terminal = _decimal_integer_text(
        checked["terminal_monotonic_ns"], "supervisor terminal", minimum=0
    )
    if deadline != start + CP62_TEST28_DEADLINE_SECONDS * 1_000_000_000:
        raise ValueError("supervisor deadline arithmetic differs")
    if terminal < start:
        raise ValueError("supervisor terminal time precedes start")
    _json_optional_integer(
        checked["exit_code"], "supervisor exit code", minimum=0, maximum=255
    )
    _json_optional_integer(
        checked["term_signal"], "supervisor signal", minimum=1, maximum=255
    )
    frame_bytes = _json_integer(
        checked["frame_bytes"],
        "supervisor frame bytes",
        minimum=0,
        maximum=CP62_TEST28_RAW_FRAME_MAX_BYTES,
    )
    _sha256(checked["child_frame_sha256"], "supervisor child frame digest")
    stderr_bytes = _json_integer(
        checked["stderr_bytes"],
        "supervisor stderr bytes",
        minimum=0,
        maximum=CP62_TEST28_STDERR_MAX_BYTES,
    )
    stderr_hex = checked["stderr_hex"]
    if (
        type(stderr_hex) is not str
        or len(stderr_hex) != 2 * stderr_bytes
        or any(character not in "0123456789abcdef" for character in stderr_hex)
    ):
        raise TypeError("supervisor stderr hex differs from byte count")
    if hashlib.sha256(bytes.fromhex(stderr_hex)).hexdigest() != _sha256(
        checked["stderr_sha256"], "supervisor stderr digest"
    ):
        raise ValueError("supervisor stderr digest differs")
    for field in (
        "completion_strictly_before_deadline",
        "exact_one_frame",
        "termination_attempted",
        "termination_signal_delivered",
        "kill_attempted",
        "reaped",
    ):
        _json_boolean(checked[field], "supervisor " + field)
    if checked["reaped"] and (
        (checked["exit_code"] is None) == (checked["term_signal"] is None)
    ):
        raise ValueError("reaped supervisor custody needs one terminal wait status")
    if checked["exact_one_frame"] and frame_bytes < 8:
        raise ValueError("supervisor frame is shorter than its prefix")
    return checked


_RAW_REQUIRED_KEYS = (
    "schema",
    "purpose",
    "case_id",
    "row_ordinal",
    "row_key",
    "fixture_id",
    "strategy",
    "budget",
    "seed_hex",
    "seed_free_request_sha256",
    "runtime_lock_sha256",
    "phase",
    "closed_status",
    "failure_code",
    "kernel_trace",
    "supervisor_custody",
    "raw_sha256",
)

_STABLE_TRACE_KEYS = (
    "schema",
    "purpose",
    "case_id",
    "row_ordinal",
    "row_key",
    "fixture_id",
    "strategy",
    "budget",
    "seed_hex",
    "seed_free_request_sha256",
    "runtime_lock_sha256",
    "phase",
    "closed_status",
    "failure_code",
    "kernel_trace",
)

_RETURNED_STATUS_BY_STRATEGY = {
    "bounded-rejection": (
        "returned-rejection-selected-before-deadline",
        "returned-rejection-exhausted-before-deadline",
    ),
    "fixed-budget-sir": ("returned-sir-selected-before-deadline",),
}
_TIMEOUT_PHASE = "timeout-at-deadline"
_TIMEOUT_STATUS = "timeout-censored-at-deadline"
_PREEXECUTION_REFUSAL_PHASE = "preexecution-refusal-before-deadline"
_EXECUTION_FAILURE_PHASE = "execution-failure-before-deadline"
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


def _validate_clean_child_completion(raw_record: dict, supervisor: dict) -> None:
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
        raise ValueError("supervisor custody is not a clean timely completion")
    child_payload = {key: raw_record[key] for key in _CHILD_PAYLOAD_KEYS}
    child_payload_bytes = _plain_json_bytes(child_payload)
    child_frame = len(child_payload_bytes).to_bytes(8, "big") + child_payload_bytes
    if (
        supervisor["frame_bytes"] != len(child_frame)
        or supervisor["child_frame_sha256"] != hashlib.sha256(child_frame).hexdigest()
    ):
        raise ValueError("child frame custody differs")


def cp62_validate_raw_record_bytes(payload: object) -> dict:
    if type(payload) is not bytes:
        raise TypeError("raw record must be exact bytes")
    value = _decode_canonical_json(
        payload, maximum=CP62_TEST28_RAW_FRAME_MAX_BYTES, name="raw record"
    )
    if tuple(sorted(value)) != tuple(sorted(_RAW_REQUIRED_KEYS)):
        raise ValueError("raw record field set differs")
    if (
        value["schema"] != CP62_TEST28_SCHEMA_VERSION
        or value["purpose"] != "development-calibration-only"
    ):
        raise ValueError("raw record schema or purpose differs")
    supplied = value["raw_sha256"]
    _sha256(supplied, "raw record digest")
    body = dict(value)
    body["raw_sha256"] = _ZERO_SHA256
    expected = hashlib.sha256(
        b"cp62-test28-raw-record-v1\0" + _plain_json_bytes(body)
    ).hexdigest()
    if supplied != expected:
        raise ValueError("raw record digest differs")
    case, row = _case_and_row(value["case_id"])
    exact_outer = {
        "row_ordinal": case.row_ordinal,
        "row_key": row.row_key,
        "fixture_id": case.fixture_id,
        "strategy": case.strategy,
        "budget": case.budget,
        "seed_hex": case.seed_hex,
        "seed_free_request_sha256": row.seed_free_request_sha256,
        "runtime_lock_sha256": _runtime_lock().record_sha256,
    }
    for field, wanted in exact_outer.items():
        actual = value[field]
        if type(actual) is not type(wanted) or actual != wanted:
            raise ValueError("raw record %s differs from frozen case" % field)
    kernel_trace = _exact_keys(
        value["kernel_trace"], _KERNEL_TRACE_KEYS, "raw kernel trace"
    )
    supervisor = _validate_supervisor_custody(value["supervisor_custody"])
    if value["phase"] == "returned-before-deadline":
        allowed_statuses = _RETURNED_STATUS_BY_STRATEGY[row.strategy]
        if (
            type(value["closed_status"]) is not str
            or value["closed_status"] not in allowed_statuses
            or value["failure_code"] is not None
        ):
            raise ValueError("raw record returned status differs from strategy")
        semantic = _validate_semantic_trace(
            kernel_trace["semantic"],
            case=case,
            row=row,
            closed_status=value["closed_status"],
        )
        volatile = _validate_volatile_custody(kernel_trace["volatile_custody"])
        nested = volatile["nested_record_custody"]
        expected_kind = (
            "rejection-attempt"
            if row.strategy == "bounded-rejection"
            else "sir-particle"
        )
        if len(nested) != row.budget or any(
            item["slot_kind"] != expected_kind for item in nested
        ):
            raise ValueError("volatile nested custody differs from semantic slots")
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
            raise ValueError("common volatile nested custody is incomplete")
        if row.strategy == "bounded-rejection":
            for item in nested:
                if (
                    item["quota_sha256"] is None
                    or item["attempt_sha256"] is None
                    or item["particle_sha256"] is not None
                ):
                    raise ValueError("rejection volatile custody pattern differs")
        else:
            for item in nested:
                if (
                    item["quota_sha256"] is not None
                    or item["attempt_sha256"] is not None
                    or item["particle_sha256"] is None
                ):
                    raise ValueError("SIR volatile custody pattern differs")
        if semantic["strategy"] != row.strategy:
            raise ValueError("semantic/volatile strategy binding differs")
        _validate_clean_child_completion(value, supervisor)
    elif value["phase"] in (
        _PREEXECUTION_REFUSAL_PHASE,
        _EXECUTION_FAILURE_PHASE,
    ):
        is_refusal = value["phase"] == _PREEXECUTION_REFUSAL_PHASE
        codes = _PREEXECUTION_REFUSAL_CODES if is_refusal else _EXECUTION_FAILURE_CODES
        outcome_kind = "preexecution-refusal" if is_refusal else "execution-failure"
        if (
            value["closed_status"] != value["phase"]
            or type(value["failure_code"]) is not str
            or value["failure_code"] not in codes
            or kernel_trace["volatile_custody"] is not None
        ):
            raise ValueError("closed refusal/failure raw record differs")
        _validate_closed_semantic_trace(
            kernel_trace["semantic"],
            case=case,
            row=row,
            outcome_kind=outcome_kind,
            failure_code=value["failure_code"],
        )
        _validate_clean_child_completion(value, supervisor)
    elif value["phase"] == _TIMEOUT_PHASE:
        if (
            value["closed_status"] != _TIMEOUT_STATUS
            or value["failure_code"] is not None
            or kernel_trace["volatile_custody"] is not None
        ):
            raise ValueError("timeout raw record status/custody differs")
        _validate_closed_semantic_trace(
            kernel_trace["semantic"],
            case=case,
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
            raise ValueError("timeout supervisor custody differs")
        _require_timeout_terminal_fields(
            supervisor["exit_code"], supervisor["term_signal"]
        )
        if (
            supervisor["termination_signal_delivered"]
            and not supervisor["termination_attempted"]
        ):
            raise ValueError("timeout termination delivery lacks an attempt")
        if (
            supervisor["term_signal"] == signal.SIGTERM
            and not supervisor["termination_signal_delivered"]
        ):
            raise ValueError("SIGTERM timeout lacks delivery custody")
        if (
            supervisor["term_signal"] == signal.SIGKILL
            and not supervisor["kill_attempted"]
        ):
            raise ValueError("SIGKILL timeout lacks kill-attempt custody")
        if supervisor["kill_attempted"] and not supervisor["termination_attempted"]:
            raise ValueError("timeout kill attempt lacks a termination attempt")
    else:
        raise ValueError("raw record phase is not a frozen closed phase")
    return value


def cp62_project_stable_trace(raw_record: object) -> dict:
    if type(raw_record) is bytes:
        raw = cp62_validate_raw_record_bytes(raw_record)
    elif type(raw_record) is dict:
        encoded = json.dumps(
            raw_record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        raw = cp62_validate_raw_record_bytes(encoded)
    else:
        raise TypeError("stable projection requires raw bytes or an exact raw object")
    trace = {
        "schema": CP62_TEST28_SCHEMA_VERSION,
        "purpose": raw["purpose"],
        "case_id": raw["case_id"],
        "row_ordinal": raw["row_ordinal"],
        "row_key": raw["row_key"],
        "fixture_id": raw["fixture_id"],
        "strategy": raw["strategy"],
        "budget": raw["budget"],
        "seed_hex": raw["seed_hex"],
        "seed_free_request_sha256": raw["seed_free_request_sha256"],
        "runtime_lock_sha256": raw["runtime_lock_sha256"],
        "phase": raw["phase"],
        "closed_status": raw["closed_status"],
        "failure_code": raw["failure_code"],
        "kernel_trace": raw["kernel_trace"]["semantic"],
    }
    _validate_stable_trace(trace)
    return trace


def _validate_stable_trace(trace: object) -> dict:
    checked = _exact_keys(trace, _STABLE_TRACE_KEYS, "stable trace")
    if (
        checked["schema"] != CP62_TEST28_SCHEMA_VERSION
        or checked["purpose"] != "development-calibration-only"
    ):
        raise ValueError("stable trace schema or purpose differs")
    case, row = _case_and_row(checked["case_id"])
    exact_outer = {
        "row_ordinal": case.row_ordinal,
        "row_key": row.row_key,
        "fixture_id": case.fixture_id,
        "strategy": case.strategy,
        "budget": case.budget,
        "seed_hex": case.seed_hex,
        "seed_free_request_sha256": row.seed_free_request_sha256,
        "runtime_lock_sha256": _runtime_lock().record_sha256,
    }
    for field, wanted in exact_outer.items():
        actual = checked[field]
        if type(actual) is not type(wanted) or actual != wanted:
            raise ValueError("stable trace %s differs" % field)
    if checked["phase"] == "returned-before-deadline":
        allowed_statuses = _RETURNED_STATUS_BY_STRATEGY[row.strategy]
        if (
            type(checked["closed_status"]) is not str
            or checked["closed_status"] not in allowed_statuses
            or checked["failure_code"] is not None
        ):
            raise ValueError("stable trace returned outcome differs")
        _validate_semantic_trace(
            checked["kernel_trace"],
            case=case,
            row=row,
            closed_status=checked["closed_status"],
        )
    elif checked["phase"] in (
        _PREEXECUTION_REFUSAL_PHASE,
        _EXECUTION_FAILURE_PHASE,
    ):
        is_refusal = checked["phase"] == _PREEXECUTION_REFUSAL_PHASE
        codes = _PREEXECUTION_REFUSAL_CODES if is_refusal else _EXECUTION_FAILURE_CODES
        outcome_kind = "preexecution-refusal" if is_refusal else "execution-failure"
        if (
            checked["closed_status"] != checked["phase"]
            or type(checked["failure_code"]) is not str
            or checked["failure_code"] not in codes
        ):
            raise ValueError("stable refusal/failure outcome differs")
        _validate_closed_semantic_trace(
            checked["kernel_trace"],
            case=case,
            row=row,
            outcome_kind=outcome_kind,
            failure_code=checked["failure_code"],
        )
    elif checked["phase"] == _TIMEOUT_PHASE:
        if (
            checked["closed_status"] != _TIMEOUT_STATUS
            or checked["failure_code"] is not None
        ):
            raise ValueError("stable timeout outcome differs")
        _validate_closed_semantic_trace(
            checked["kernel_trace"],
            case=case,
            row=row,
            outcome_kind="timeout-censored",
            failure_code=None,
        )
    else:
        raise ValueError("stable trace phase differs")
    encoded = _plain_json_bytes(checked)
    if len(encoded) > CP62_TEST28_STABLE_TRACE_MAX_BYTES:
        raise ValueError("stable projection is oversized")
    return checked


def cp62_stable_trace_canonical_json_bytes(trace: object) -> bytes:
    checked = _validate_stable_trace(trace)
    encoded = _plain_json_bytes(checked)
    if len(encoded) > CP62_TEST28_STABLE_TRACE_MAX_BYTES:
        raise ValueError("stable trace is oversized")
    return encoded


def cp62_stable_trace_sha256(trace: object) -> str:
    encoded = cp62_stable_trace_canonical_json_bytes(trace)
    return hashlib.sha256(b"cp62-test28-stable-trace-v1\0" + encoded).hexdigest()


_CHILD_PAYLOAD_KEYS = tuple(
    key for key in _RAW_REQUIRED_KEYS if key not in ("supervisor_custody", "raw_sha256")
)


def _execute_calibration_case_locally(case_id: str) -> dict:
    case, row = _case_and_row(case_id)

    from heterodiff.evaluation import exact_rational_quadratic_initial_tilt as exact
    from heterodiff.processes import certified_initial_score_provider_v1 as facade
    from heterodiff.processes import (
        plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 as kernel_v2,
    )

    observation = _runtime_observation()
    source_factory = (
        exact.build_t28_m1_q_exact_score_provider
        if row.fixture_id == "T28-M1-Q"
        else exact.build_t28_m2_q_exact_score_provider
    )
    source = source_factory()
    source_certificate = source.certificate
    if (
        source_certificate.fixture_id != row.fixture_id
        or source_certificate.certificate_sha256 != row.source_certificate_sha256
    ):
        raise CP62ExecutionCapsuleError(
            "SOURCE_BINDING_MISMATCH", "exact score source differs from request binding"
        )
    provider = facade.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
        source, adapter_role_sha256=row.adapter_role_sha256
    )
    provider_certificate = provider.certificate
    provider_expected = {
        "adapter_role_sha256": row.adapter_role_sha256,
        "source_certificate_sha256": row.source_certificate_sha256,
        "source_parameter_sha256": row.source_parameter_sha256,
        "reference_parameter_sha256": row.reference_parameter_sha256,
        "certificate_sha256": row.facade_certificate_sha256,
    }
    for field, wanted in provider_expected.items():
        if getattr(provider_certificate, field) != wanted:
            raise CP62ExecutionCapsuleError(
                "FACADE_BINDING_MISMATCH",
                "certified facade differs from request binding",
            )
    plan = kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy=row.strategy,
        residual_context=row.residual_context,
        initializer_role_sha256=row.initializer_role_sha256,
        seed=case.seed_uint64,
        budget=row.budget,
        ess_warning_fraction=(0.25 if row.strategy == "fixed-budget-sir" else None),
    )
    if (
        plan.residual_context_sha256 != row.residual_context_sha256
        or plan.initializer_role_sha256 != row.initializer_role_sha256
        or plan.strategy != row.strategy
        or plan.seed != case.seed_uint64
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
        raise CP62ExecutionCapsuleError(
            "PLAN_BINDING_MISMATCH", "kernel plan differs from request binding"
        )
    owner = kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        provider, plan=plan
    )
    result = owner.execute()
    if owner.validate_result(result) is not result:
        raise CP62ExecutionCapsuleError(
            "RESULT_VALIDATION_IDENTITY_MISMATCH",
            "kernel validation returned another result object",
        )
    if row.strategy == "bounded-rejection":
        if result.status == "selected":
            closed_status = "returned-rejection-selected-before-deadline"
        elif result.status == "exhausted":
            closed_status = "returned-rejection-exhausted-before-deadline"
        else:
            raise CP62ExecutionCapsuleError(
                "UNKNOWN_REJECTION_STATUS",
                "kernel returned an unknown rejection status",
            )
    else:
        if result.status != "selected":
            raise CP62ExecutionCapsuleError(
                "UNKNOWN_SIR_STATUS", "kernel returned an unknown SIR status"
            )
        closed_status = "returned-sir-selected-before-deadline"
    semantic = _kernel_semantic_trace(case, row, owner, result)
    if semantic["runtime_observation"] != observation:
        raise CP62ExecutionCapsuleError(
            "RUNTIME_OBSERVATION_CHANGED",
            "runtime observation changed during calibration execution",
        )
    payload = {
        "schema": CP62_TEST28_SCHEMA_VERSION,
        "purpose": "development-calibration-only",
        "case_id": case.case_id,
        "row_ordinal": row.row_ordinal,
        "row_key": row.row_key,
        "fixture_id": row.fixture_id,
        "strategy": row.strategy,
        "budget": row.budget,
        "seed_hex": case.seed_hex,
        "seed_free_request_sha256": row.seed_free_request_sha256,
        "runtime_lock_sha256": _runtime_lock().record_sha256,
        "phase": "returned-before-deadline",
        "closed_status": closed_status,
        "failure_code": None,
        "kernel_trace": {
            "semantic": semantic,
            "volatile_custody": _kernel_volatile_custody(owner, result),
        },
    }
    _validate_child_payload(payload)
    return payload


def _validate_child_payload(value: object) -> dict:
    checked = _exact_keys(value, _CHILD_PAYLOAD_KEYS, "calibration child payload")
    case, row = _case_and_row(checked["case_id"])
    expected = {
        "schema": CP62_TEST28_SCHEMA_VERSION,
        "purpose": "development-calibration-only",
        "row_ordinal": row.row_ordinal,
        "row_key": row.row_key,
        "fixture_id": row.fixture_id,
        "strategy": row.strategy,
        "budget": row.budget,
        "seed_hex": case.seed_hex,
        "seed_free_request_sha256": row.seed_free_request_sha256,
        "runtime_lock_sha256": _runtime_lock().record_sha256,
    }
    for field, wanted in expected.items():
        if type(checked[field]) is not type(wanted) or checked[field] != wanted:
            raise ValueError("calibration child payload %s differs" % field)
    kernel_trace = _exact_keys(
        checked["kernel_trace"], _KERNEL_TRACE_KEYS, "child kernel trace"
    )
    if checked["phase"] == "returned-before-deadline":
        if (
            checked["closed_status"] not in _RETURNED_STATUS_BY_STRATEGY[row.strategy]
            or checked["failure_code"] is not None
        ):
            raise ValueError("calibration child returned an unknown status")
        _validate_semantic_trace(
            kernel_trace["semantic"],
            case=case,
            row=row,
            closed_status=checked["closed_status"],
        )
        volatile = _validate_volatile_custody(kernel_trace["volatile_custody"])
        if len(volatile["nested_record_custody"]) != row.budget:
            raise ValueError("child nested custody length differs")
    elif checked["phase"] in (
        _PREEXECUTION_REFUSAL_PHASE,
        _EXECUTION_FAILURE_PHASE,
    ):
        is_refusal = checked["phase"] == _PREEXECUTION_REFUSAL_PHASE
        codes = _PREEXECUTION_REFUSAL_CODES if is_refusal else _EXECUTION_FAILURE_CODES
        outcome_kind = "preexecution-refusal" if is_refusal else "execution-failure"
        if (
            checked["closed_status"] != checked["phase"]
            or type(checked["failure_code"]) is not str
            or checked["failure_code"] not in codes
            or kernel_trace["volatile_custody"] is not None
        ):
            raise ValueError("calibration child closed outcome differs")
        _validate_closed_semantic_trace(
            kernel_trace["semantic"],
            case=case,
            row=row,
            outcome_kind=outcome_kind,
            failure_code=checked["failure_code"],
        )
    else:
        raise ValueError("calibration child phase differs")
    return checked


def _child_auth_sha256(case_id: str, nonce_sha256: str) -> str:
    return hashlib.sha256(
        _CHILD_AUTH_DOMAIN
        + case_id.encode("ascii")
        + b"\0"
        + bytes.fromhex(nonce_sha256)
    ).hexdigest()


def _calibration_child_nonce(case_id: str, start_ns: int, launch_ordinal: int) -> str:
    return hashlib.sha256(
        _CHILD_NONCE_DOMAIN
        + case_id.encode("ascii")
        + b"\0"
        + start_ns.to_bytes(8, "big")
        + os.getpid().to_bytes(8, "big")
        + launch_ordinal.to_bytes(8, "big")
    ).hexdigest()


def _write_all(file_descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    offset = 0
    while offset < len(view):
        written = os.write(file_descriptor, view[offset:])
        if written <= 0:
            raise CP62ExecutionCapsuleError(
                "CHILD_FRAME_WRITE_FAILURE", "child frame write made no progress"
            )
        offset += written


def _calibration_child_main(arguments: Tuple[str, ...]) -> int:
    if len(arguments) != 4 or arguments[0] != "--cp62-calibration-child":
        return 64
    case_id, nonce_sha256, supplied_auth = arguments[1:]
    try:
        _case_and_row(case_id)
        _sha256(nonce_sha256, "calibration child nonce")
        _sha256(supplied_auth, "calibration child authorization")
        expected_auth = _child_auth_sha256(case_id, nonce_sha256)
        if supplied_auth != expected_auth:
            raise ValueError("calibration child authorization differs")
        if tuple(sorted(os.environ.items())) != tuple(
            sorted(CP62_TEST28_SANITIZED_CHILD_ENVIRONMENT)
        ):
            raise CP62ExecutionCapsuleError(
                "CHILD_ENVIRONMENT_MISMATCH",
                "calibration child environment differs from the frozen allowlist",
            )

        source_root = Path(__file__).resolve().parents[2]
        workspace_root = source_root.parent
        executable_path = Path(sys.executable)
        venv_root = executable_path.parent.parent
        pyvenv_path = venv_root / "pyvenv.cfg"
        dependency_lock_path = (
            workspace_root / "requirements" / "m1-reference-macos-arm64-py311.lock"
        )
        runtime_lock = _runtime_lock()
        if (
            not pyvenv_path.is_file()
            or pyvenv_path.stat().st_size != runtime_lock.pyvenv_cfg_bytes
            or _file_sha256(pyvenv_path) != runtime_lock.pyvenv_cfg_sha256
            or not dependency_lock_path.is_file()
            or _file_sha256(dependency_lock_path) != runtime_lock.dependency_lock_sha256
        ):
            raise CP62ExecutionCapsuleError(
                "PREIMPORT_RUNTIME_INPUT_MISMATCH",
                "pre-import virtual-environment or dependency-lock bytes differ",
            )
        site_packages = (
            venv_root
            / "lib"
            / ("python%d.%d" % (sys.version_info.major, sys.version_info.minor))
            / "site-packages"
        )
        if not site_packages.is_dir():
            raise CP62ExecutionCapsuleError(
                "PREIMPORT_SITE_PACKAGES_MISSING",
                "the frozen virtual-environment site-packages directory is absent",
            )
        os.chdir(workspace_root)
        source_root_text = str(source_root)
        if source_root_text not in sys.path:
            sys.path.insert(0, source_root_text)
        site_packages_text = str(site_packages)
        if site_packages_text not in sys.path:
            sys.path.append(site_packages_text)

        payload = _execute_calibration_case_locally(case_id)
        encoded = _plain_json_bytes(payload)
        if len(encoded) + 8 > CP62_TEST28_RAW_FRAME_MAX_BYTES:
            raise CP62ExecutionCapsuleError(
                "CHILD_FRAME_OVERSIZED", "calibration child frame is oversized"
            )
        _write_all(1, len(encoded).to_bytes(8, "big") + encoded)
        return 0
    except BaseException as error:
        code = (
            error.code
            if isinstance(error, CP62ExecutionCapsuleError)
            else type(error).__name__.upper()
        )
        message = ("CP62_CHILD_ERROR:" + code + "\n").encode("ascii", "replace")
        try:
            _write_all(2, message[:4_096])
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


def _poll_child(pid: int, status: Optional[int]) -> Optional[int]:
    if status is not None:
        return status
    try:
        waited_pid, waited_status = os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        raise CP62ExecutionCapsuleError(
            "CHILD_REAP_STATE_LOST", "calibration child reap state was lost"
        )
    return waited_status if waited_pid == pid else None


def _exit_and_signal(status: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
    if status is None:
        return None, None
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status), None
    if os.WIFSIGNALED(status):
        return None, os.WTERMSIG(status)
    return None, None


def _require_timeout_terminal_fields(
    exit_code: Optional[int], term_signal: Optional[int]
) -> None:
    if not (
        (exit_code == 0 and term_signal is None)
        or (exit_code is None and term_signal in (signal.SIGTERM, signal.SIGKILL))
    ):
        raise ValueError(
            "an abnormal child exit cannot be folded into timeout censoring"
        )


def _require_timeout_terminal_status(status: int) -> None:
    try:
        _require_timeout_terminal_fields(*_exit_and_signal(status))
    except ValueError as error:
        raise CP62ExecutionCapsuleError(
            "CHILD_ABNORMAL_EXIT_AT_DEADLINE",
            "an abnormal child exit cannot be folded into timeout censoring",
        ) from error


def _process_group_exists(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return False
    except OSError as error:
        raise CP62ExecutionCapsuleError(
            "PROCESS_GROUP_PROBE_FAILURE",
            "failed to probe the calibration process group",
        ) from error
    return True


def _terminate_and_reap(
    pid: int,
    status: Optional[int],
    *,
    allow_grace: bool,
) -> Tuple[int, bool, bool, bool]:
    group_absence_observed = False

    def group_exists() -> bool:
        nonlocal group_absence_observed
        if group_absence_observed:
            return False
        exists = _process_group_exists(pid)
        if not exists:
            group_absence_observed = True
        return exists

    kill_attempted = False
    termination_attempted = False
    termination_delivered = False
    if group_exists():
        termination_attempted = True
        try:
            os.killpg(pid, signal.SIGTERM)
            termination_delivered = True
        except ProcessLookupError:
            group_absence_observed = True
        except OSError as error:
            raise CP62ExecutionCapsuleError(
                "PROCESS_GROUP_TERMINATION_FAILURE",
                "failed to terminate calibration process group",
            ) from error
    grace_deadline = time.monotonic_ns() + (
        CP62_TEST28_TERMINATION_GRACE_SECONDS * 1_000_000_000 if allow_grace else 0
    )
    while time.monotonic_ns() < grace_deadline:
        if status is None:
            status = _poll_child(pid, status)
        if group_absence_observed or (status is not None and not group_exists()):
            break
        time.sleep(0.01)
    if not group_absence_observed and (status is None or group_exists()):
        kill_attempted = True
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            group_absence_observed = True
        except OSError as error:
            raise CP62ExecutionCapsuleError(
                "PROCESS_GROUP_KILL_FAILURE",
                "failed to kill calibration process group",
            ) from error
    reap_deadline = (
        time.monotonic_ns() + CP62_TEST28_REAP_CEILING_SECONDS * 1_000_000_000
    )
    while time.monotonic_ns() < reap_deadline:
        if status is None:
            status = _poll_child(pid, status)
        if status is not None and (group_absence_observed or not group_exists()):
            break
        time.sleep(0.01)
    if status is None:
        raise CP62ExecutionCapsuleError(
            "PROCESS_GROUP_REAP_FAILURE",
            "calibration process group could not be reaped within the ceiling",
        )
    if not group_absence_observed and group_exists():
        raise CP62ExecutionCapsuleError(
            "PROCESS_GROUP_CLEANUP_FAILURE",
            "calibration process group survived the cleanup ceiling",
        )
    return status, kill_attempted, termination_attempted, termination_delivered


def _spawn_calibration_child(
    case_id: str, start_ns: int, launch_ordinal: int
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
        nonce = _calibration_child_nonce(case_id, start_ns, launch_ordinal)
        auth = _child_auth_sha256(case_id, nonce)
        executable = os.path.abspath(sys.executable)
        source_path = str(Path(__file__).resolve())
        arguments = (
            executable,
            "-S",
            "-s",
            "-P",
            "-u",
            source_path,
            "--cp62-calibration-child",
            case_id,
            nonce,
            auth,
        )
        environment = dict(CP62_TEST28_SANITIZED_CHILD_ENVIRONMENT)
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
            environment,
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
            _terminate_and_reap(pid, None, allow_grace=False)
        raise CP62ExecutionCapsuleError(
            "CHILD_SPAWN_FAILURE", "failed to spawn calibration child"
        ) from error
    return cast(int, pid), cast(int, stdout_read), cast(int, stderr_read)


def _read_child_streams(
    selector: selectors.BaseSelector,
    stdout: bytearray,
    stderr: bytearray,
    *,
    timeout: float,
) -> None:
    for key, _mask in selector.select(timeout):
        file_descriptor = cast(int, key.fd)
        target = stdout if key.data == "stdout" else stderr
        while True:
            try:
                block = os.read(file_descriptor, 65_536)
            except BlockingIOError:
                break
            except OSError as error:
                raise CP62ExecutionCapsuleError(
                    "CHILD_PIPE_READ_FAILURE", "failed to read calibration child pipe"
                ) from error
            if not block:
                selector.unregister(file_descriptor)
                _safe_close(file_descriptor)
                break
            target.extend(block)
            maximum = (
                CP62_TEST28_RAW_FRAME_MAX_BYTES
                if key.data == "stdout"
                else CP62_TEST28_STDERR_MAX_BYTES
            )
            if len(target) > maximum:
                raise CP62ExecutionCapsuleError(
                    "CHILD_STDOUT_OVERSIZED"
                    if key.data == "stdout"
                    else "CHILD_STDERR_OVERSIZED",
                    "calibration child output exceeded its frozen cap",
                )
            if key.data == "stdout" and len(stdout) >= 8:
                announced = int.from_bytes(stdout[:8], "big")
                if announced + 8 > CP62_TEST28_RAW_FRAME_MAX_BYTES:
                    raise CP62ExecutionCapsuleError(
                        "CHILD_FRAME_LENGTH_OVERSIZED",
                        "calibration child announced an oversized frame",
                    )
                if len(stdout) > announced + 8:
                    raise CP62ExecutionCapsuleError(
                        "CHILD_MULTIPLE_OR_TRAILING_FRAMES",
                        "calibration child emitted trailing frame bytes",
                    )


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
    exit_code, term_signal = _exit_and_signal(status)
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
    record["raw_sha256"] = _plain_digest(b"cp62-test28-raw-record-v1", record)
    encoded = _plain_json_bytes(record)
    cp62_validate_raw_record_bytes(encoded)
    return encoded


def _timeout_raw_record(
    case: CP62CalibrationCaseV1,
    row: CP62RequestBindingV1,
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
    exit_code, term_signal = _exit_and_signal(status)
    record = {
        "schema": CP62_TEST28_SCHEMA_VERSION,
        "purpose": "development-calibration-only",
        "case_id": case.case_id,
        "row_ordinal": row.row_ordinal,
        "row_key": row.row_key,
        "fixture_id": row.fixture_id,
        "strategy": row.strategy,
        "budget": row.budget,
        "seed_hex": case.seed_hex,
        "seed_free_request_sha256": row.seed_free_request_sha256,
        "runtime_lock_sha256": _runtime_lock().record_sha256,
        "phase": _TIMEOUT_PHASE,
        "closed_status": _TIMEOUT_STATUS,
        "failure_code": None,
        "kernel_trace": {
            "semantic": _closed_semantic_trace(
                case,
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
    record["raw_sha256"] = _plain_digest(b"cp62-test28-raw-record-v1", record)
    encoded = _plain_json_bytes(record)
    cp62_validate_raw_record_bytes(encoded)
    return encoded


def _supervise_calibration_case(
    case: CP62CalibrationCaseV1,
    row: CP62RequestBindingV1,
    launch_ordinal: int,
) -> bytes:
    start_ns = time.monotonic_ns()
    deadline_ns = start_ns + CP62_TEST28_DEADLINE_SECONDS * 1_000_000_000
    pid = None
    stdout_fd = None
    stderr_fd = None
    stdout = bytearray()
    stderr = bytearray()
    status = None
    reaped_ns = None
    selector = None
    process_group_absence_observed = False
    try:
        pid, stdout_fd, stderr_fd = _spawn_calibration_child(
            case.case_id, start_ns, launch_ordinal
        )
        selector = selectors.DefaultSelector()
        selector.register(stdout_fd, selectors.EVENT_READ, "stdout")
        selector.register(stderr_fd, selectors.EVENT_READ, "stderr")
        while True:
            previous_status = status
            status = _poll_child(pid, status)
            if previous_status is None and status is not None:
                reaped_ns = time.monotonic_ns()
            now = time.monotonic_ns()
            if now >= deadline_ns:
                exit_code, term_signal = _exit_and_signal(status)
                if status is not None and (exit_code != 0 or term_signal is not None):
                    raise CP62ExecutionCapsuleError(
                        "CHILD_ABNORMAL_EXIT",
                        "calibration child terminated abnormally before observation",
                    )
                for key in tuple(selector.get_map().values()):
                    selector.unregister(key.fd)
                (
                    status,
                    kill_attempted,
                    termination_attempted,
                    termination_delivered,
                ) = _terminate_and_reap(pid, status, allow_grace=True)
                process_group_absence_observed = True
                _safe_close(stdout_fd)
                stdout_fd = None
                _safe_close(stderr_fd)
                stderr_fd = None
                _require_timeout_terminal_status(status)
                return _timeout_raw_record(
                    case,
                    row,
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
            _read_child_streams(selector, stdout, stderr, timeout=wait_seconds)
            if status is not None and not selector.get_map():
                break
            if (
                status is not None
                and reaped_ns is not None
                and time.monotonic_ns() - reaped_ns > _PIPE_EOF_GRACE_NS
            ):
                raise CP62ExecutionCapsuleError(
                    "CHILD_PIPE_EOF_FAILURE",
                    "calibration child pipes did not reach EOF after reap",
                )

        exit_code, term_signal = _exit_and_signal(status)
        if _process_group_exists(pid):
            raise CP62ExecutionCapsuleError(
                "CHILD_PROCESS_GROUP_LEAK",
                "calibration child left a live process-group member",
            )
        process_group_absence_observed = True
        if exit_code != 0 or term_signal is not None:
            raise CP62ExecutionCapsuleError(
                "CHILD_ABNORMAL_EXIT", "calibration child did not exit cleanly"
            )
        if len(stdout) < 8:
            raise CP62ExecutionCapsuleError(
                "CHILD_FRAME_MISSING", "calibration child frame is missing"
            )
        announced = int.from_bytes(stdout[:8], "big")
        if announced + 8 != len(stdout):
            raise CP62ExecutionCapsuleError(
                "CHILD_FRAME_LENGTH_MISMATCH",
                "calibration child frame length differs",
            )
        child_payload = _decode_canonical_json(
            bytes(stdout[8:]),
            maximum=CP62_TEST28_RAW_FRAME_MAX_BYTES - 8,
            name="calibration child frame",
        )
        _validate_child_payload(child_payload)
        terminal_ns = time.monotonic_ns()
        if terminal_ns >= deadline_ns:
            kill_attempted = False
            termination_attempted = False
            termination_delivered = False
            _require_timeout_terminal_status(status)
            return _timeout_raw_record(
                case,
                row,
                pid=pid,
                start_ns=start_ns,
                deadline_ns=deadline_ns,
                terminal_ns=terminal_ns,
                status=status,
                kill_attempted=kill_attempted,
                termination_attempted=termination_attempted,
                termination_signal_delivered=termination_delivered,
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
        _safe_close(stdout_fd)
        _safe_close(stderr_fd)
        if (
            pid is not None
            and not process_group_absence_observed
            and (status is None or _process_group_exists(pid))
        ):
            _terminate_and_reap(pid, status, allow_grace=False)
        if isinstance(error, CP62ExecutionCapsuleError):
            raise
        raise CP62ExecutionCapsuleError(
            "CHILD_SUPERVISOR_INFRASTRUCTURE_FAILURE",
            "calibration supervisor encountered an infrastructure failure",
        ) from error
    finally:
        if selector is not None:
            selector.close()


def cp62_run_calibration_case(case_id: object) -> bytes:
    """Run one of the four frozen calibration cases in a fresh child."""

    global _CALIBRATION_LAUNCH_COUNT, _CALIBRATION_RUNNING

    case, row = _case_and_row(case_id)
    entered = False
    try:
        with _CALIBRATION_STATE_LOCK:
            if _CALIBRATION_RUNNING:
                raise CP62ExecutionCapsuleError(
                    "CALIBRATION_CONCURRENCY_REFUSED",
                    "only one CP62 calibration child may run at a time",
                )
            if _CALIBRATION_LAUNCH_COUNT >= CP62_TEST28_CALIBRATION_LAUNCH_LIMIT:
                raise CP62ExecutionCapsuleError(
                    "CALIBRATION_LAUNCH_LIMIT_REACHED",
                    "the frozen CP62 calibration launch limit is exhausted",
                )
            if (
                _CALIBRATION_CASE_LAUNCH_COUNTS[case.case_id]
                >= case.maximum_child_launches
            ):
                raise CP62ExecutionCapsuleError(
                    "CALIBRATION_CASE_LAUNCH_LIMIT_REACHED",
                    "the frozen per-case calibration launch limit is exhausted",
                )
            entered = True
            _CALIBRATION_LAUNCH_COUNT += 1
            _CALIBRATION_CASE_LAUNCH_COUNTS[case.case_id] += 1
            _CALIBRATION_RUNNING = True
            launch_ordinal = _CALIBRATION_LAUNCH_COUNT
        return _supervise_calibration_case(case, row, launch_ordinal)
    finally:
        if entered:
            with _CALIBRATION_STATE_LOCK:
                _CALIBRATION_RUNNING = False


if __name__ == "__main__":
    raise SystemExit(_calibration_child_main(tuple(sys.argv[1:])))


__all__ = (
    "CP62ExecutionCapsuleError",
    "CP62RuntimeSourceABILockV1",
    "CP62SeedCapsuleContractV1",
    "CP62RequestBindingV1",
    "CP62SupervisorContractV1",
    "CP62RawRecordSchemaV1",
    "CP62StableTraceProjectionContractV1",
    "CP62CalibrationCaseV1",
    "CP62ExecutionCapsuleBundleV1",
    "CP62_TEST28_SCHEMA_VERSION",
    "CP62_TEST28_SCOPE",
    "cp62_execution_capsule_bundle",
    "cp62_execution_capsule_semantic_sha256",
    "cp62_canonical_json_bytes",
    "cp62_logical_request_ordinal",
    "cp62_inverse_logical_request_ordinal",
    "cp62_validate_raw_record_bytes",
    "cp62_project_stable_trace",
    "cp62_stable_trace_canonical_json_bytes",
    "cp62_stable_trace_sha256",
    "cp62_run_calibration_case",
    "validate_cp62_runtime_source_abi_lock",
    "validate_cp62_seed_capsule_contract",
    "validate_cp62_request_binding",
    "validate_cp62_supervisor_contract",
    "validate_cp62_raw_record_schema",
    "validate_cp62_stable_trace_projection_contract",
    "validate_cp62_calibration_case",
    "validate_cp62_execution_capsule_bundle",
)
