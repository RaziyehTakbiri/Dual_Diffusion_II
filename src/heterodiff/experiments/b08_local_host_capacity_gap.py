"""Pure B08 local-host policy and synthetic-receipt validation.

This additive module freezes only the three B08 fields that are already
scientifically determined without a production capacity reservation:

* F153: a fail-closed deterministic execution policy;
* F158: zero empirical-pilot compute; and
* F161: zero failure reserve.

The local-host observations and synthetic calibration receipts are diagnostic
evidence.  They are deliberately insufficient to populate F150--F152,
F154--F157, F159--F160, or F162, and they are not a capacity reservation,
F104 calibration-weight receipt, domain-scale runtime, or B08 closure.

The module is standard-library-only and pure.  It reads no file or environment,
launches no process, draws no entropy, and performs no training or scientific
calculation.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple


SCHEMA_VERSION = "heterodiff-manuscript-v3-b08-local-host-capacity-gap-v1"
STATE = "B08_LOCAL_HOST_PARTIAL_POLICY_FREEZE_CAPACITY_NO_GO"
CONTROL_PREDICATE = "B08_THREE_LOCALLY_DEFENSIBLE_FIELDS_FROZEN_CAPACITY_HOLD"

FIELD_IDS = ("F153", "F158", "F161")
RESIDUAL_FIELD_IDS = (
    "F150",
    "F151",
    "F152",
    "F154",
    "F155",
    "F156",
    "F157",
    "F159",
    "F160",
    "F162",
)
B08_CAPACITY_REQUIREMENTS = (
    "HARDWARE_AND_RUNTIME_IDENTITY",
    "CALIBRATION_WEIGHTS",
    "SCALAR_AND_HARD_AXIS_CEILING_VALUES",
    "CAPACITY_RESERVATION_RECEIPT",
)

_HEX_DIGITS = frozenset("0123456789abcdef")
_CANONICAL_ENVIRONMENT = {
    "BLIS_NUM_THREADS": "1",
    "CUDA_VISIBLE_DEVICES": "",
    "LANG": "C",
    "LC_ALL": "C",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONSAFEPATH": "1",
    "PYTHONUTF8": "1",
    "TZ": "UTC",
    "VECLIB_MAXIMUM_THREADS": "1",
}


def canonical_json_bytes(value: object) -> bytes:
    """Return canonical duplicate-free ASCII JSON bytes without a line feed."""

    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ValueError("value is not finite canonical JSON") from error
    return encoded.encode("ascii")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _exact_keys(value: object, expected: Iterable[str], *, name: str) -> dict:
    if type(value) is not dict:
        raise ValueError(name + " must be an exact object")
    expected_keys = frozenset(expected)
    if frozenset(value) != expected_keys or any(type(key) is not str for key in value):
        raise ValueError(name + " has a non-exact schema")
    return value


def _exact_list(value: object, *, length: int, name: str) -> list:
    if type(value) is not list or len(value) != length:
        raise ValueError(name + " must be an exact list of length %d" % length)
    return value


def _exact_bool(value: object, *, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(name + " must be an exact boolean")
    return value


def _exact_nonnegative_int(value: object, *, name: str, maximum: int = 2**63 - 1) -> int:
    if type(value) is not int or value < 0 or value > maximum:
        raise ValueError(name + " must be a bounded exact nonnegative integer")
    return value


def _exact_positive_int(value: object, *, name: str, maximum: int = 2**63 - 1) -> int:
    result = _exact_nonnegative_int(value, name=name, maximum=maximum)
    if result == 0:
        raise ValueError(name + " must be positive")
    return result


def _exact_ascii(value: object, *, name: str, maximum: int = 4096) -> str:
    if type(value) is not str or not value or len(value) > maximum or "\x00" in value:
        raise ValueError(name + " must be bounded nonempty ASCII")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError(name + " must be ASCII") from error
    return value


def _sha256(value: object, *, name: str) -> str:
    digest = _exact_ascii(value, name=name, maximum=64)
    if len(digest) != 64 or any(character not in _HEX_DIGITS for character in digest):
        raise ValueError(name + " must be a lowercase SHA-256 digest")
    return digest


def _require_exact_json_types(value: object, *, name: str) -> None:
    value_type = type(value)
    if value is None or value_type in (str, int, bool):
        return
    if value_type is list:
        for ordinal, item in enumerate(value):
            _require_exact_json_types(item, name="%s[%d]" % (name, ordinal))
        return
    if value_type is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(name + " contains a non-string key")
            _require_exact_json_types(item, name=name + "." + key)
        return
    raise ValueError(name + " contains a non-exact JSON-native type")


def hardware_observation() -> Dict[str, object]:
    """Return the redacted, device-bound local-host observation."""

    public_profile: Dict[str, object] = {
        "architecture": "arm64",
        "cpu_chip": "Apple M1 Pro",
        "cpu_cores": {
            "efficiency": 2,
            "performance": 8,
            "total": 10,
        },
        "gpu": {
            "chip": "Apple M1 Pro",
            "cores": 16,
            "metal_supported": True,
        },
        "installed_memory_gib": 16,
        "memory_type": "LPDDR5",
        "model_identifier": "MacBookPro18,1",
        "model_name": "MacBook Pro",
    }
    result: Dict[str, object] = {
        "capture_kind": "READ_ONLY_LOCAL_HOST_OBSERVATION_NOT_RESERVATION",
        "hardware_public_profile": public_profile,
        "hardware_public_profile_sha256": sha256_json(public_profile),
        "private_device_binding_domain": "heterodiff-b08-private-device-binding-v1",
        "private_device_binding_sha256": (
            "5e1227315f8c2c82be651c4dad8087a69bb2ca98966a04484546da2e012fe85d"
        ),
        "private_identifiers_recorded_in_package": False,
        "production_hardware_selected": False,
        "production_hardware_reserved": False,
        "reported_date": "2026-09-01",
        "time_externally_attested": False,
    }
    return result


def software_environment_observation() -> Dict[str, object]:
    """Return the observed smoke-test environment, not a production freeze."""

    distributions = [
        ["Jinja2", "3.1.6"],
        ["MarkupSafe", "3.0.3"],
        ["Pygments", "2.20.0"],
        ["filelock", "3.32.0"],
        ["fsspec", "2026.6.0"],
        ["iniconfig", "2.3.0"],
        ["mpmath", "1.3.0"],
        ["networkx", "3.6.1"],
        ["numpy", "2.4.6"],
        ["packaging", "26.2"],
        ["pip", "23.2.1"],
        ["pluggy", "1.6.0"],
        ["pyflakes", "3.4.0"],
        ["pytest", "9.1.1"],
        ["scipy", "1.17.1"],
        ["setuptools", "65.5.0"],
        ["sympy", "1.14.0"],
        ["threadpoolctl", "3.6.0"],
        ["torch", "2.12.1"],
        ["typing_extensions", "4.16.0"],
    ]
    identity: Dict[str, object] = {
        "architecture": "arm64",
        "darwin_kernel_version": "25.3.0",
        "distributions": distributions,
        "lockfile_path": "requirements/m1-reference-macos-arm64-py311.lock",
        "lockfile_sha256": (
            "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d"
        ),
        "macos_build": "25D2128",
        "macos_version": "26.3.1",
        "project_pyproject_sha256": (
            "78d8cddc752e6d2d41c6e050132ea71e65fb374a02a6fb00c2cf12ec3ff89fa0"
        ),
        "python_abi": "cpython-311-darwin",
        "python_implementation": "CPython",
        "python_version": "3.11.5",
        "torch_runtime": {
            "default_dtype_observed": "torch.float32",
            "deterministic_algorithms_default_observed": False,
            "mps_available_to_capture_process": False,
            "mps_built": True,
            "version": "2.12.1",
        },
    }
    return {
        "capture_kind": "READ_ONLY_INSTALLED_SMOKE_ENVIRONMENT_OBSERVATION",
        "complete_b12_runtime_present": False,
        "external_baseline_runtime_dependencies_complete": False,
        "identity": identity,
        "lockfile_self_declares_not_future_linux_cuda_large_training_lock": True,
        "production_environment_selected": False,
        "software_environment_observation_sha256": sha256_json(identity),
    }


def storage_observation() -> Dict[str, object]:
    """Return the exact one-time capacity observation; no bytes were reserved."""

    return {
        "available_1024_byte_blocks": 39564700,
        "available_bytes": 40514252800,
        "capture_kind": "READ_ONLY_DF_SNAPSHOT",
        "filesystem_total_1024_byte_blocks": 971350180,
        "filesystem_used_1024_byte_blocks": 896205864,
        "persistent_bytes_reserved": 0,
        "production_capacity_receipt": False,
        "reported_capacity_percent": 96,
        "reservation_created": False,
        "snapshot_not_a_future_availability_guarantee": True,
    }


def deterministic_settings_value() -> Dict[str, object]:
    """Exact F153 value: a CPU-only, fail-closed determinism policy."""

    return {
        "accelerator_policy": "CPU_ONLY_CUDA_AND_MPS_DISABLED",
        "b12_operation_level_determinism_receipt_required": True,
        "environment": dict(_CANONICAL_ENVIRONMENT),
        "f141_precision_owned_separately": True,
        "nondeterministic_or_unsupported_operation_disposition": (
            "TERMINAL_PREEXECUTION_NO_GO_NO_FALLBACK"
        ),
        "policy_id": "B08_CPU_SINGLE_THREAD_FAIL_CLOSED_DETERMINISM_V1",
        "production_determinism_demonstrated_by_this_package": False,
        "seed_registry_owned_by_b07": True,
        "torch": {
            "cudnn_benchmark": False,
            "deterministic_algorithms": True,
            "interop_threads": 1,
            "threads": 1,
            "warn_only": False,
        },
    }


def pilot_compute_allocation_value() -> Dict[str, object]:
    """Exact F158 value implied by the accepted distribution-free B07 route."""

    return {
        "accelerator_hours": 0,
        "allocation_id": "B08_ZERO_EMPIRICAL_PILOT_DISTRIBUTION_FREE_B07_V1",
        "f104_phase": "PILOT",
        "f104_resource_event_counts_all_zero": True,
        "model_evaluations": 0,
        "persistent_bytes": 0,
        "scientific_or_empirical_pilot_runs": 0,
        "synthetic_environment_calibration_is_not_empirical_pilot": True,
        "transfer_or_topup_permitted": False,
        "wall_time_seconds": 0,
    }


def failure_reserve_value() -> Dict[str, object]:
    """Exact F161 value under no rerun, no replacement, and no top-up."""

    return {
        "accelerator_hours": 0,
        "allocation_id": "B08_ZERO_FAILURE_RESERVE_NO_RERUN_NO_REPLACEMENT_V1",
        "extra_attempt_count": 0,
        "failed_and_aborted_scheduled_attempts_charged_to_original_allocation": True,
        "infrastructure_rerun_predicate": "NEVER_TRUE_NO_INFRASTRUCTURE_RERUN",
        "model_evaluations": 0,
        "persistent_bytes": 0,
        "post_result_topup_permitted": False,
        "replacement_or_retry_permitted": False,
        "wall_time_seconds": 0,
    }


def field_closures() -> List[Dict[str, object]]:
    return [
        {
            "field_id": "F153",
            "json_pointer": "/compute_and_fairness_plan/deterministic_settings",
            "status": "PROPOSED_CLOSED_BY_ADDITIVE_PREOUTCOME_POLICY_FREEZE",
            "value": deterministic_settings_value(),
        },
        {
            "field_id": "F158",
            "json_pointer": "/compute_and_fairness_plan/pilot_compute_allocation",
            "status": "PROPOSED_CLOSED_BY_ADDITIVE_PREOUTCOME_POLICY_FREEZE",
            "value": pilot_compute_allocation_value(),
        },
        {
            "field_id": "F161",
            "json_pointer": "/compute_and_fairness_plan/failure_reserve",
            "status": "PROPOSED_CLOSED_BY_ADDITIVE_PREOUTCOME_POLICY_FREEZE",
            "value": failure_reserve_value(),
        },
    ]


def residual_gaps() -> List[Dict[str, object]]:
    reasons = {
        "F150": "OBSERVED_LOCAL_HOST_IS_NOT_SELECTED_OR_RESERVED_PRODUCTION_HARDWARE",
        "F151": "OBSERVED_SMOKE_ENVIRONMENT_IS_NOT_COMPLETE_B12_PRODUCTION_RUNTIME",
        "F152": "CURRENT_LOCK_SELF_DECLARES_NOT_FUTURE_LARGE_TRAINING_LOCK",
        "F154": "NO_DOMAIN_SCALE_RUN_UNIT_OR_CAPACITY_TIMING_RECEIPT",
        "F155": "MPS_UNAVAILABLE_AND_FINAL_ACCELERATOR_ROUTE_NOT_SELECTED",
        "F156": "NO_WHOLE_METHOD_PEAK_DEVICE_HOST_OR_PERSISTENT_MEMORY_RECEIPT",
        "F157": "NO_B12_RUN_UNIT_AND_F143_F147_REMAIN_OPEN",
        "F159": "NO_FINAL_F147_TRIAL_LIMIT_CALIBRATION_WEIGHTS_OR_CAPACITY",
        "F160": "NO_COMPLETE_RUN_SCHEDULE_CALIBRATION_WEIGHTS_OR_CAPACITY",
        "F162": "NO_F104_WEIGHTS_SCALAR_CEILING_HARD_AXES_OR_RESERVATION_RECEIPT",
    }
    pointers = {
        "F150": "/compute_and_fairness_plan/hardware",
        "F151": "/compute_and_fairness_plan/software_environment_sha256",
        "F152": "/compute_and_fairness_plan/container_or_lockfile_sha256",
        "F154": "/compute_and_fairness_plan/per_run_wall_time_ceiling",
        "F155": "/compute_and_fairness_plan/per_run_accelerator_hour_ceiling",
        "F156": "/compute_and_fairness_plan/per_run_peak_memory_ceiling",
        "F157": "/compute_and_fairness_plan/per_run_model_evaluation_ceiling",
        "F159": "/compute_and_fairness_plan/tuning_compute_allocation",
        "F160": "/compute_and_fairness_plan/final_compute_allocation",
        "F162": "/compute_and_fairness_plan/total_compute_ceiling",
    }
    return [
        {
            "field_id": field_id,
            "json_pointer": pointers[field_id],
            "reason_code": reasons[field_id],
            "status": "OPEN_NULL_NO_VALUE_PROPOSED",
        }
        for field_id in RESIDUAL_FIELD_IDS
    ]


def sha256_calibration_receipt() -> Dict[str, object]:
    rows = [
        [0, 33036208, 32946000],
        [1, 33081709, 32999000],
        [2, 33059500, 32943000],
        [3, 32996958, 32919000],
        [4, 33073084, 32964000],
    ]
    result: Dict[str, object] = {
        "input_construction": "ONE_MIBIBYTE_ALL_ZERO_BYTES_STREAMED_64_TIMES",
        "maximum_rss_bytes_on_darwin": 17235968,
        "production_capacity_or_f104_weight_claimed": False,
        "rows": [
            {
                "input_bytes": 67108864,
                "ordinal": ordinal,
                "process_time_ns": process_time_ns,
                "sha256": "3b6a07d0d404fab4e23b6d34bc6696a6a312dd92821332385e5af7c01c421351",
                "wall_time_ns": wall_time_ns,
            }
            for ordinal, wall_time_ns, process_time_ns in rows
        ],
        "schema": "heterodiff-b08-local-host-synthetic-sha256-calibration-v1",
        "synthetic_non_scientific": True,
    }
    result["receipt_sha256"] = sha256_json(result)
    return result


def torch_calibration_receipt() -> Dict[str, object]:
    rows = [
        [0, 3444750, 1371000],
        [1, 404917, 404000],
        [2, 423709, 422000],
    ]
    result: Dict[str, object] = {
        "default_dtype_observed": "torch.float32",
        "deterministic_algorithms_enabled_for_capture": True,
        "device": "cpu",
        "input_construction": "FIXED_ARANGE_MOD257_AND_TRANSPOSED_ARANGE_MOD263_512_SQUARE",
        "maximum_rss_bytes_on_darwin": 282542080,
        "mps_available": False,
        "mps_built": True,
        "num_interop_threads": 1,
        "num_threads": 1,
        "production_capacity_determinism_or_f104_weight_claimed": False,
        "rows": [
            {
                "ordinal": ordinal,
                "output_sha256": "94816432ec6b2c0dda21ed9420dfad8ea5cf0f6d987dd20fef54500d9825f43d",
                "process_time_ns": process_time_ns,
                "shape": [512, 512, 512],
                "wall_time_ns": wall_time_ns,
            }
            for ordinal, wall_time_ns, process_time_ns in rows
        ],
        "schema": "heterodiff-b08-local-host-synthetic-torch-cpu-calibration-v1",
        "synthetic_non_scientific": True,
        "torch_version": "2.12.1",
    }
    result["receipt_sha256"] = sha256_json(result)
    return result


def _validate_self_digest(value: dict, *, name: str) -> None:
    digest = _sha256(value.get("receipt_sha256"), name=name + ".receipt_sha256")
    body = dict(value)
    body.pop("receipt_sha256")
    if digest != sha256_json(body):
        raise ValueError(name + " self digest mismatch")


def validate_sha256_calibration_receipt(value: object) -> Dict[str, object]:
    _require_exact_json_types(value, name="sha256 calibration receipt")
    expected = sha256_calibration_receipt()
    row_keys = {"input_bytes", "ordinal", "process_time_ns", "sha256", "wall_time_ns"}
    record = _exact_keys(value, expected, name="sha256 calibration receipt")
    rows = _exact_list(record["rows"], length=5, name="sha256 calibration rows")
    for ordinal, row in enumerate(rows):
        exact_row = _exact_keys(row, row_keys, name="sha256 calibration row")
        if _exact_nonnegative_int(exact_row["ordinal"], name="ordinal") != ordinal:
            raise ValueError("sha256 calibration ordinal mismatch")
        _exact_positive_int(exact_row["input_bytes"], name="input_bytes")
        _exact_positive_int(exact_row["wall_time_ns"], name="wall_time_ns")
        _exact_positive_int(exact_row["process_time_ns"], name="process_time_ns")
        _sha256(exact_row["sha256"], name="sha256")
    _exact_positive_int(record["maximum_rss_bytes_on_darwin"], name="maximum_rss")
    _exact_bool(record["synthetic_non_scientific"], name="synthetic_non_scientific")
    _exact_bool(
        record["production_capacity_or_f104_weight_claimed"],
        name="production_capacity_or_f104_weight_claimed",
    )
    _validate_self_digest(record, name="sha256 calibration receipt")
    if record != expected:
        raise ValueError("sha256 calibration receipt differs from frozen observation")
    return deepcopy(record)


def validate_torch_calibration_receipt(value: object) -> Dict[str, object]:
    _require_exact_json_types(value, name="torch calibration receipt")
    expected = torch_calibration_receipt()
    row_keys = {"ordinal", "output_sha256", "process_time_ns", "shape", "wall_time_ns"}
    record = _exact_keys(value, expected, name="torch calibration receipt")
    rows = _exact_list(record["rows"], length=3, name="torch calibration rows")
    for ordinal, row in enumerate(rows):
        exact_row = _exact_keys(row, row_keys, name="torch calibration row")
        if _exact_nonnegative_int(exact_row["ordinal"], name="ordinal") != ordinal:
            raise ValueError("torch calibration ordinal mismatch")
        shape = _exact_list(exact_row["shape"], length=3, name="torch shape")
        if any(type(axis) is not int or axis != 512 for axis in shape):
            raise ValueError("torch calibration shape mismatch")
        _sha256(exact_row["output_sha256"], name="output_sha256")
        _exact_positive_int(exact_row["wall_time_ns"], name="wall_time_ns")
        _exact_positive_int(exact_row["process_time_ns"], name="process_time_ns")
    for name in (
        "deterministic_algorithms_enabled_for_capture",
        "mps_available",
        "mps_built",
        "production_capacity_determinism_or_f104_weight_claimed",
        "synthetic_non_scientific",
    ):
        _exact_bool(record[name], name=name)
    _exact_positive_int(record["maximum_rss_bytes_on_darwin"], name="maximum_rss")
    _exact_positive_int(record["num_threads"], name="num_threads")
    _exact_positive_int(record["num_interop_threads"], name="num_interop_threads")
    _validate_self_digest(record, name="torch calibration receipt")
    if record != expected:
        raise ValueError("torch calibration receipt differs from frozen observation")
    return deepcopy(record)


def validate_field_closures(value: object) -> List[Dict[str, object]]:
    rows = _exact_list(value, length=3, name="field closures")
    expected = field_closures()
    if rows != expected:
        raise ValueError("field closures differ from exact three-field proposal")
    for row in rows:
        _exact_keys(row, {"field_id", "json_pointer", "status", "value"}, name="field closure")
    return deepcopy(rows)


def validate_residual_gaps(value: object) -> List[Dict[str, object]]:
    rows = _exact_list(value, length=10, name="residual gaps")
    expected = residual_gaps()
    if rows != expected:
        raise ValueError("residual gaps differ from exact ten-field no-go roster")
    return deepcopy(rows)


def capacity_gate() -> Dict[str, object]:
    return {
        "B08_close_permitted": False,
        "requirements": [
            {"requirement_id": requirement, "satisfied": False}
            for requirement in B08_CAPACITY_REQUIREMENTS
        ],
        "terminal_disposition": "B08_REMAINS_OPEN_CAPACITY_NO_GO",
    }


def validate_capacity_gate(value: object) -> Dict[str, object]:
    expected = capacity_gate()
    gate = _exact_keys(
        value,
        {"B08_close_permitted", "requirements", "terminal_disposition"},
        name="capacity gate",
    )
    _exact_bool(gate["B08_close_permitted"], name="B08_close_permitted")
    rows = _exact_list(gate["requirements"], length=4, name="capacity requirements")
    for row in rows:
        _exact_keys(row, {"requirement_id", "satisfied"}, name="capacity requirement")
        _exact_bool(row["satisfied"], name="capacity requirement satisfied")
    if gate != expected:
        raise ValueError("capacity gate may not claim a satisfied requirement")
    return deepcopy(gate)


def supported_projection() -> Dict[str, object]:
    """Return the complete pure semantic projection used by the package."""

    return {
        "capacity_gate": capacity_gate(),
        "field_closures": field_closures(),
        "hardware_observation": hardware_observation(),
        "residual_gaps": residual_gaps(),
        "sha256_calibration_receipt": sha256_calibration_receipt(),
        "software_environment_observation": software_environment_observation(),
        "storage_observation": storage_observation(),
        "torch_calibration_receipt": torch_calibration_receipt(),
    }


def validate_supported_projection(value: object) -> Dict[str, object]:
    _require_exact_json_types(value, name="supported projection")
    expected = supported_projection()
    projection = _exact_keys(value, expected, name="supported projection")
    validate_capacity_gate(projection["capacity_gate"])
    validate_field_closures(projection["field_closures"])
    validate_residual_gaps(projection["residual_gaps"])
    validate_sha256_calibration_receipt(projection["sha256_calibration_receipt"])
    validate_torch_calibration_receipt(projection["torch_calibration_receipt"])
    if projection != expected:
        raise ValueError("supported projection differs from frozen exact values")
    return deepcopy(projection)


__all__ = [
    "B08_CAPACITY_REQUIREMENTS",
    "CONTROL_PREDICATE",
    "FIELD_IDS",
    "RESIDUAL_FIELD_IDS",
    "SCHEMA_VERSION",
    "STATE",
    "canonical_json_bytes",
    "capacity_gate",
    "deterministic_settings_value",
    "failure_reserve_value",
    "field_closures",
    "hardware_observation",
    "pilot_compute_allocation_value",
    "residual_gaps",
    "sha256_calibration_receipt",
    "sha256_json",
    "software_environment_observation",
    "storage_observation",
    "supported_projection",
    "torch_calibration_receipt",
    "validate_capacity_gate",
    "validate_field_closures",
    "validate_residual_gaps",
    "validate_sha256_calibration_receipt",
    "validate_supported_projection",
    "validate_torch_calibration_receipt",
]
