"""Hostile contract tests for the CP62 calibration-only execution capsule."""

from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import pickle
import subprocess
import sys

import pytest

from heterodiff.evaluation import mixed_initializer_test28_execution_capsule as capsule


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_execution_capsule.py"
)

_CP61_SOURCE_SHA256 = "8ea06f5cfc5cd79842e2984d5f91918463cf887c0efc2fd026490f51e66129cb"
_CP61_BUNDLE_SHA256 = "8c5e23661cc0ef459e700c2af5239d21ee8aafd4d9dca2ed3db6e3ce2e4a0ca0"
_CP61_STABLE_DESIGN_SHA256 = (
    "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
)

_CALIBRATION_CASES = (
    ("m1-rejection-a64", "T28-M1-Q", "bounded-rejection", 64, 4, 0x50F4E257C447B1A5),
    ("m1-sir-j512", "T28-M1-Q", "fixed-budget-sir", 512, 8, 0xBF9166D11A411920),
    ("m2-rejection-a64", "T28-M2-Q", "bounded-rejection", 64, 12, 0x5A17988A783E381E),
    ("m2-sir-j512", "T28-M2-Q", "fixed-budget-sir", 512, 16, 0xC89B2562891B7701),
)

_M1_ADAPTER_ROLE = "e93c2bd1bb9181ed21538d15e5618753a92048f7f3b5647250db2c570df0b2fc"
_M2_ADAPTER_ROLE = "334d63f46dc53483717ab5017373622a7626e194e33f0de0b2d13b938abf793d"
_M1_KERNEL_ROLE = "a4ccf3fd3c63ac740e723d1bf6e30bcdb155089ce0901c0c5e0dee53936f6b38"
_M2_KERNEL_ROLE = "7c1e6a032b3da0e83756a00dc2fb6b4c28fad88bed9dcb3b548a3a79a8013677"

_EXPECTED_CALIBRATION_OUTCOMES = {
    "m1-rejection-a64": ("selected", 0, 64),
    "m1-sir-j512": ("selected", 253, None),
    "m2-rejection-a64": ("selected", 0, 52),
    "m2-sir-j512": ("selected", 96, None),
}

_EXPECTED_STABLE_TRACE_RECEIPTS = {
    "m1-rejection-a64": (
        296473,
        "ad0fd60347f16adb6317d464d8708bd2b2f9277f2a5195b43441765a489f1d2a",
    ),
    "m1-sir-j512": (
        850656,
        "7685a2357efd06a8b7dc473759ec19ba799d6039fc3841486428ac17620202e9",
    ),
    "m2-rejection-a64": (
        342364,
        "146924d4a7c7504a4540b60249f46fb3ed71a7fc6b10195958b5b461f469d04f",
    ),
    "m2-sir-j512": (
        904281,
        "37a982bc3cc8744087f7b9d356fc8ff15c3bd371c81d5f9508095f27e3724ccb",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _independent_canonical_value(value: object) -> object:
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        return {"$int": str(value)}
    if type(value) is str:
        return value
    if type(value) is tuple:
        return {"$tuple": [_independent_canonical_value(item) for item in value]}
    if type(value) is dict:
        return {key: _independent_canonical_value(value[key]) for key in sorted(value)}
    raise TypeError("hostile helper received an unsupported canonical value")


def _independent_seed_free_digest(row: object) -> str:
    names = (
        "schema_version",
        "row_ordinal",
        "row_key",
        "fixture_id",
        "strategy",
        "budget",
        "cp60_request_template_sha256",
        "cp60_definition_record_sha256",
        "source_factory",
        "facade_factory",
        "kernel_factory",
        "residual_context",
        "residual_context_sha256",
        "adapter_role_sha256",
        "initializer_role_sha256",
        "source_certificate_sha256",
        "source_parameter_sha256",
        "reference_parameter_sha256",
        "facade_certificate_sha256",
        "sir_ess_warning_fraction_float64_be",
        "adaptive_fallback_permitted",
    )
    payload = {name: getattr(row, name) for name in names}
    encoded = json.dumps(
        _independent_canonical_value(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(b"cp62-test28-seed-free-request-v1\x00" + encoded).hexdigest()


def _raw_digest(record: dict) -> str:
    body = dict(record)
    body["raw_sha256"] = "0" * 64
    encoded = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(b"cp62-test28-raw-record-v1\x00" + encoded).hexdigest()


def _owned_json_leaf(domain: bytes, body: dict, digest_field: str) -> dict:
    value = dict(body)
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    value[digest_field] = hashlib.sha256(domain + b"\x00" + encoded).hexdigest()
    return value


def _timeout_raw_record(**changes: object) -> dict:
    bundle = capsule.cp62_execution_capsule_bundle()
    case = bundle.calibration_cases[0]
    row = bundle.request_bindings[case.row_ordinal - 1]
    instance_sha256 = hashlib.sha256(
        b"cp62-test28-calibration-request-instance-v1\x00"
        + bytes.fromhex(row.seed_free_request_sha256)
        + case.seed_uint64.to_bytes(8, "big")
    ).hexdigest()
    closed = _owned_json_leaf(
        b"cp62-test28-closed-kernel-outcome-v1",
        {
            "trace_schema": "cp62-test28-closed-kernel-outcome-v1",
            "stable_request_sha256": row.seed_free_request_sha256,
            "calibration_instance_sha256": instance_sha256,
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
            "runtime_lock_sha256": bundle.runtime_source_abi_lock.record_sha256,
            "runtime_observation": None,
            "outcome_kind": "timeout-censored",
            "failure_code": None,
            "completed_kernel_trace_present": False,
            "timeout_is_semantic_nonreturn": False,
        },
        "cp62_closed_trace_sha256",
    )
    value = {
        "schema": capsule.CP62_TEST28_SCHEMA_VERSION,
        "purpose": "development-calibration-only",
        "case_id": case.case_id,
        "row_ordinal": case.row_ordinal,
        "row_key": row.row_key,
        "fixture_id": case.fixture_id,
        "strategy": case.strategy,
        "budget": case.budget,
        "seed_hex": case.seed_hex,
        "seed_free_request_sha256": row.seed_free_request_sha256,
        "runtime_lock_sha256": bundle.runtime_source_abi_lock.record_sha256,
        "phase": "timeout-at-deadline",
        "closed_status": "timeout-censored-at-deadline",
        "failure_code": None,
        "kernel_trace": {"semantic": closed, "volatile_custody": None},
        "supervisor_custody": {
            "pid": 100,
            "process_group": 100,
            "start_monotonic_ns": "0",
            "deadline_monotonic_ns": "300000000000",
            "terminal_monotonic_ns": "300000000000",
            "exit_code": None,
            "term_signal": 15,
            "frame_bytes": 0,
            "child_frame_sha256": hashlib.sha256(b"").hexdigest(),
            "stderr_bytes": 0,
            "stderr_hex": "",
            "stderr_sha256": hashlib.sha256(b"").hexdigest(),
            "completion_strictly_before_deadline": False,
            "exact_one_frame": False,
            "termination_attempted": True,
            "termination_signal_delivered": True,
            "kill_attempted": False,
            "reaped": True,
        },
        "raw_sha256": "0" * 64,
    }
    value.update(changes)
    value["raw_sha256"] = _raw_digest(value)
    return value


def _closed_failure_raw_record(phase: str, failure_code: str) -> dict:
    value = _timeout_raw_record()
    outcome_kind = (
        "preexecution-refusal"
        if phase == "preexecution-refusal-before-deadline"
        else "execution-failure"
    )
    semantic = dict(value["kernel_trace"]["semantic"])
    semantic.pop("cp62_closed_trace_sha256")
    semantic.update(
        {
            "outcome_kind": outcome_kind,
            "failure_code": failure_code,
        }
    )
    value.update(
        {
            "phase": phase,
            "closed_status": phase,
            "failure_code": failure_code,
            "kernel_trace": {
                "semantic": _owned_json_leaf(
                    b"cp62-test28-closed-kernel-outcome-v1",
                    semantic,
                    "cp62_closed_trace_sha256",
                ),
                "volatile_custody": None,
            },
        }
    )
    child_payload = {
        key: value[key]
        for key in value
        if key not in ("supervisor_custody", "raw_sha256")
    }
    child_payload_bytes = json.dumps(
        child_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    child_frame = len(child_payload_bytes).to_bytes(8, "big") + child_payload_bytes
    value["supervisor_custody"] = {
        "pid": 100,
        "process_group": 100,
        "start_monotonic_ns": "0",
        "deadline_monotonic_ns": "300000000000",
        "terminal_monotonic_ns": "1",
        "exit_code": 0,
        "term_signal": None,
        "frame_bytes": len(child_frame),
        "child_frame_sha256": hashlib.sha256(child_frame).hexdigest(),
        "stderr_bytes": 0,
        "stderr_hex": "",
        "stderr_sha256": hashlib.sha256(b"").hexdigest(),
        "completion_strictly_before_deadline": True,
        "exact_one_frame": True,
        "termination_attempted": False,
        "termination_signal_delivered": False,
        "kill_attempted": False,
        "reaped": True,
    }
    value["raw_sha256"] = _raw_digest(value)
    return value


@pytest.fixture(scope="module")
def calibration_frames() -> dict:
    """Spend the frozen 2 x 4 launch allowance once for every hostile test."""

    frames = {}
    for case_id, *_rest in _CALIBRATION_CASES:
        repetitions = []
        for _ in range(2):
            payload = capsule.cp62_run_calibration_case(case_id)
            repetitions.append(
                (payload, capsule.cp62_validate_raw_record_bytes(payload))
            )
        frames[case_id] = tuple(repetitions)
    return frames


def _raw_record(calibration_frames: dict, **changes: object) -> dict:
    value = copy.deepcopy(calibration_frames["m1-rejection-a64"][0][1])
    value.update(changes)
    value["raw_sha256"] = _raw_digest(value)
    return value


def _raw_bytes(calibration_frames: dict, **changes: object) -> bytes:
    return json.dumps(
        _raw_record(calibration_frames, **changes),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")


def _redigest_returned_raw_record(value: dict) -> dict:
    """Redigest every CP62-owned envelope after a hostile semantic edit."""

    semantic = dict(value["kernel_trace"]["semantic"])
    semantic.pop("cp62_semantic_trace_sha256")
    value["kernel_trace"]["semantic"] = _owned_json_leaf(
        b"cp62-test28-semantic-kernel-trace-v1",
        semantic,
        "cp62_semantic_trace_sha256",
    )
    child_payload = {
        key: value[key]
        for key in value
        if key not in ("supervisor_custody", "raw_sha256")
    }
    child_payload_bytes = json.dumps(
        child_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    child_frame = len(child_payload_bytes).to_bytes(8, "big") + child_payload_bytes
    value["supervisor_custody"]["frame_bytes"] = len(child_frame)
    value["supervisor_custody"]["child_frame_sha256"] = hashlib.sha256(
        child_frame
    ).hexdigest()
    value["raw_sha256"] = _raw_digest(value)
    return value


def test_cp62_public_contract_surface_is_exact() -> None:
    expected_classes = {
        "CP62RuntimeSourceABILockV1",
        "CP62SeedCapsuleContractV1",
        "CP62RequestBindingV1",
        "CP62SupervisorContractV1",
        "CP62RawRecordSchemaV1",
        "CP62StableTraceProjectionContractV1",
        "CP62CalibrationCaseV1",
        "CP62ExecutionCapsuleBundleV1",
    }
    expected_functions = {
        "cp62_execution_capsule_bundle",
        "cp62_canonical_json_bytes",
        "cp62_execution_capsule_semantic_sha256",
        "cp62_logical_request_ordinal",
        "cp62_inverse_logical_request_ordinal",
        "cp62_validate_raw_record_bytes",
        "cp62_project_stable_trace",
        "cp62_stable_trace_canonical_json_bytes",
        "cp62_stable_trace_sha256",
        "cp62_run_calibration_case",
    }
    for name in expected_classes | expected_functions:
        assert hasattr(capsule, name), name
    assert expected_classes | expected_functions <= set(capsule.__all__)


def test_cp62_exported_surface_and_signatures_are_exactly_frozen() -> None:
    expected = (
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
    assert capsule.__all__ == expected
    expected_parameters = {
        "cp62_execution_capsule_bundle": (),
        "cp62_execution_capsule_semantic_sha256": ("bundle",),
        "cp62_canonical_json_bytes": ("record",),
        "cp62_logical_request_ordinal": ("seed_ordinal", "row_ordinal"),
        "cp62_inverse_logical_request_ordinal": ("logical_ordinal",),
        "cp62_validate_raw_record_bytes": ("payload",),
        "cp62_project_stable_trace": ("raw_record",),
        "cp62_stable_trace_canonical_json_bytes": ("trace",),
        "cp62_stable_trace_sha256": ("trace",),
        "cp62_run_calibration_case": ("case_id",),
    }
    for name, parameters in expected_parameters.items():
        assert tuple(inspect.signature(getattr(capsule, name)).parameters) == parameters


def test_cp62_predecessor_custody_matches_live_cp61() -> None:
    from heterodiff.evaluation import (
        mixed_initializer_test28_whole_seed_mc_design as cp61,
    )

    bundle = capsule.cp62_execution_capsule_bundle()
    predecessor = cp61.cp61_whole_seed_mc_design_bundle()
    assert _sha256(Path(cp61.__file__)) == _CP61_SOURCE_SHA256
    assert predecessor.record_sha256 == _CP61_BUNDLE_SHA256
    assert predecessor.stable_design_semantic_sha256 == _CP61_STABLE_DESIGN_SHA256
    assert bundle.cp61_source_sha256 == _CP61_SOURCE_SHA256
    assert bundle.cp61_stable_design_sha256 == _CP61_STABLE_DESIGN_SHA256
    assert tuple(
        (
            row.fixture_id,
            row.strategy,
            row.budget,
            row.cp60_request_template_sha256,
            row.cp60_definition_record_sha256,
        )
        for row in bundle.request_bindings
    ) == tuple(
        (
            row.fixture_id,
            row.strategy,
            row.budget,
            row.cp60_request_template_sha256,
            row.cp60_definition_record_sha256,
        )
        for row in predecessor.ordered_rows
    )


def test_cp62_kernel_reference_and_provider_source_custody_matches_live_files() -> None:
    expected = {
        "CP62_TEST28_KERNEL_SOURCE_SHA256": (
            "src/heterodiff/processes/"
            "plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2.py"
        ),
        "CP62_TEST28_REFERENCE_SOURCE_SHA256": (
            "src/heterodiff/theory/configuration_reference.py"
        ),
        "CP62_TEST28_FACADE_SOURCE_SHA256": (
            "src/heterodiff/processes/certified_initial_score_provider_v1.py"
        ),
        "CP62_TEST28_EXACT_SCORE_SOURCE_SHA256": (
            "src/heterodiff/evaluation/exact_rational_quadratic_initial_tilt.py"
        ),
        "CP62_TEST28_QUOTA_SOURCE_SHA256": (
            "src/heterodiff/processes/arbitrary_rational_uint64_exp_quota.py"
        ),
    }
    for constant, relative_path in expected.items():
        assert getattr(capsule, constant) == _sha256(_ROOT / relative_path)


def test_cp62_exact_calibration_cases_are_not_seed_source_draws() -> None:
    bundle = capsule.cp62_execution_capsule_bundle()
    actual = tuple(
        (
            case.case_id,
            case.fixture_id,
            case.strategy,
            case.budget,
            case.row_ordinal,
            case.seed_uint64,
        )
        for case in bundle.calibration_cases
    )
    assert actual == _CALIBRATION_CASES
    for case in bundle.calibration_cases:
        expected = hashlib.sha256(
            b"cp62-test28-calibration-seed-v1\x00"
            + case.fixture_id.encode("ascii")
            + b"\x00"
            + case.strategy.encode("ascii")
        ).digest()[:8]
        assert case.seed_uint64 == int.from_bytes(expected, "big")
        assert case.seed_is_external_source_draw is False
        assert case.production_observation is False


def test_cp62_binds_all_sixteen_seed_free_requests_in_cp61_order() -> None:
    bundle = capsule.cp62_execution_capsule_bundle()
    rows = bundle.request_bindings
    assert len(rows) == 16
    assert tuple(row.row_ordinal for row in rows) == tuple(range(1, 17))
    assert tuple((row.fixture_id, row.strategy, row.budget) for row in rows) == tuple(
        (fixture, strategy, budget)
        for fixture in ("T28-M1-Q", "T28-M2-Q")
        for strategy, budgets in (
            ("bounded-rejection", (1, 4, 16, 64)),
            ("fixed-budget-sir", (8, 32, 128, 512)),
        )
        for budget in budgets
    )
    assert {row.adapter_role_sha256 for row in rows[:8]} == {_M1_ADAPTER_ROLE}
    assert {row.adapter_role_sha256 for row in rows[8:]} == {_M2_ADAPTER_ROLE}
    assert {row.initializer_role_sha256 for row in rows[:8]} == {_M1_KERNEL_ROLE}
    assert {row.initializer_role_sha256 for row in rows[8:]} == {_M2_KERNEL_ROLE}
    assert all(len(row.seed_free_request_sha256) == 64 for row in rows)
    assert all(not row.seed_value_present for row in rows)
    assert all(not row.request_instance_fully_bound for row in rows)
    assert all(not row.adaptive_fallback_permitted for row in rows)
    assert tuple(_independent_seed_free_digest(row) for row in rows) == tuple(
        row.seed_free_request_sha256 for row in rows
    )


@pytest.mark.parametrize("seed_ordinal", (1, 2, 2048))
@pytest.mark.parametrize("row_ordinal", (1, 8, 9, 16))
def test_cp62_logical_request_ordinal_is_seed_major_and_bijective(
    seed_ordinal: int, row_ordinal: int
) -> None:
    ordinal = capsule.cp62_logical_request_ordinal(seed_ordinal, row_ordinal)
    assert ordinal == (seed_ordinal - 1) * 16 + row_ordinal
    assert capsule.cp62_inverse_logical_request_ordinal(ordinal) == (
        seed_ordinal,
        row_ordinal,
    )


@pytest.mark.parametrize(
    "function,args",
    (
        ("cp62_logical_request_ordinal", (False, 1)),
        ("cp62_logical_request_ordinal", (1, True)),
        ("cp62_logical_request_ordinal", (0, 1)),
        ("cp62_logical_request_ordinal", (2049, 1)),
        ("cp62_logical_request_ordinal", (1, 0)),
        ("cp62_logical_request_ordinal", (1, 17)),
        ("cp62_inverse_logical_request_ordinal", (False,)),
        ("cp62_inverse_logical_request_ordinal", (0,)),
        ("cp62_inverse_logical_request_ordinal", (32769,)),
    ),
)
def test_cp62_ordinal_helpers_reject_bool_and_out_of_range(function, args) -> None:
    with pytest.raises((TypeError, ValueError)):
        getattr(capsule, function)(*args)


def test_cp62_seed_capsule_is_schema_only_and_never_claims_iid() -> None:
    contract = capsule.cp62_execution_capsule_bundle().seed_capsule_contract
    assert contract.seed_count == 2048
    assert contract.seed_ordinals == tuple(range(1, 2049))
    assert contract.seed_encoding == "uint64-16-lowercase-hex-big-endian"
    assert contract.purpose == (
        "future-production-external-iid-uniform-uint64-with-replacement"
    )
    assert contract.duplicate_values_retained is True
    assert contract.order_is_semantic is True
    assert contract.no_retry_drop_replacement_or_topup is True
    assert contract.digest_and_frequency_checks_imply_iid_uniform is False
    assert contract.maximum_capsule_bytes == 128 * 1024
    assert contract.exact_json_keys == (
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
    assert contract.seed_values_present is False
    assert contract.seed_capsule_instantiated is False
    assert contract.external_source_bound is False
    assert contract.iid_uniform_with_replacement_verified is False
    assert contract.source_method_id is None
    assert contract.source_receipt_sha256 is None
    assert contract.acquisition_session_sha256 is None
    assert contract.body_sha256 is None


def test_cp62_bundle_leaves_every_production_and_claim_flag_false() -> None:
    bundle = capsule.cp62_execution_capsule_bundle()
    false_fields = (
        "production_seed_ingest_api_exposed",
        "arbitrary_seed_execution_api_exposed",
        "production_campaign_loop_exposed",
        "seed_capsule_instantiated",
        "external_source_bound",
        "iid_uniform_with_replacement_verified",
        "request_instances_fully_bound",
        "production_runtime_match_verified",
        "infrastructure_fidelity_verified",
        "production_supervisor_bound",
        "production_runner_bound",
        "shard_mapping_bound",
        "production_requests_executed",
        "estimates_computed",
        "intervals_computed",
        "operational_predictions_derived",
        "runner_and_recomputation_blocker_closed",
        "unconditional_operational_predictions_blocker_closed",
        "power_guarantee_claimed",
        "confirmatory_evidence",
        "manuscript_claim_promoted",
        "formal_test_28_closed",
    )
    for name in false_fields:
        assert getattr(bundle, name) is False, name
    assert bundle.calibration_only is True
    assert bundle.source_runtime_abi_candidate_bound is True
    assert bundle.formal_test_28_status == "OPEN"


def test_cp62_records_are_sealed_nonconstructible_nonpickleable_and_replayed() -> None:
    bundle = capsule.cp62_execution_capsule_bundle()
    records_and_validators = (
        (bundle.runtime_source_abi_lock, capsule.validate_cp62_runtime_source_abi_lock),
        (bundle.seed_capsule_contract, capsule.validate_cp62_seed_capsule_contract),
        (bundle.request_bindings[0], capsule.validate_cp62_request_binding),
        (bundle.supervisor_contract, capsule.validate_cp62_supervisor_contract),
        (bundle.raw_record_schema, capsule.validate_cp62_raw_record_schema),
        (
            bundle.stable_trace_projection_contract,
            capsule.validate_cp62_stable_trace_projection_contract,
        ),
        (bundle.calibration_cases[0], capsule.validate_cp62_calibration_case),
        (bundle, capsule.validate_cp62_execution_capsule_bundle),
    )
    for record, validator in records_and_validators:
        assert validator(record) is record
        assert not hasattr(record, "__dict__")
        with pytest.raises(TypeError):
            type(record)()
        with pytest.raises(TypeError):
            type("HostileCP62Subclass", (type(record),), {})
        with pytest.raises(TypeError):
            pickle.dumps(record)
        with pytest.raises((AttributeError, TypeError)):
            setattr(record, "record_sha256", "f" * 64)


def test_cp62_validation_rejects_object_level_tamper_even_after_redigest_is_not_possible() -> None:
    bundle = capsule.cp62_execution_capsule_bundle()
    row = bundle.request_bindings[0]
    object.__setattr__(row, "budget", row.budget + 1)
    with pytest.raises((TypeError, ValueError)):
        capsule.validate_cp62_request_binding(row)
    with pytest.raises((TypeError, ValueError)):
        capsule.cp62_canonical_json_bytes(row)

    forged_bundle = capsule.cp62_execution_capsule_bundle()
    object.__setattr__(forged_bundle, "formal_test_28_closed", True)
    object.__setattr__(forged_bundle, "record_sha256", "f" * 64)
    with pytest.raises((TypeError, ValueError)):
        capsule.validate_cp62_execution_capsule_bundle(forged_bundle)
    with pytest.raises((TypeError, ValueError)):
        capsule.cp62_execution_capsule_semantic_sha256(forged_bundle)


def test_record_validation_rejects_hostile_mapping_keys_without_comparison() -> None:
    calls = []

    class Bomb:
        def __lt__(self, other):
            del other
            calls.append("lt")
            raise AssertionError("hostile key comparison executed")

    runtime = capsule.cp62_execution_capsule_bundle().runtime_source_abi_lock
    object.__setattr__(
        runtime,
        "sanitized_child_environment",
        {Bomb(): "first", Bomb(): "second"},
    )
    with pytest.raises((TypeError, ValueError)):
        capsule.validate_cp62_runtime_source_abi_lock(runtime)
    assert calls == []


@pytest.mark.parametrize("hostile", ({}, (), [], True, 1, "record"))
def test_cp62_canonical_encoder_accepts_only_validated_public_records(hostile) -> None:
    with pytest.raises((TypeError, ValueError)):
        capsule.cp62_canonical_json_bytes(hostile)


def test_cp62_source_has_no_production_or_entropy_api() -> None:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    forbidden = {
        "sample_seed",
        "sample_seeds",
        "execute_request",
        "execute_campaign",
        "run_campaign",
        "run_production_request",
        "compute_intervals",
        "compute_metrics",
    }
    assert public_functions.isdisjoint(forbidden)
    source = _SOURCE.read_text(encoding="utf-8")
    for token in ("secrets.", "os.urandom", "random.SystemRandom", "np.random"):
        assert token not in source


def test_zero_argument_builder_has_no_production_inputs() -> None:
    signature = inspect.signature(capsule.cp62_execution_capsule_bundle)
    assert tuple(signature.parameters) == ()


def test_zero_argument_builder_performs_no_io_process_launch_or_entropy(
    monkeypatch,
) -> None:
    def bomb(*args, **kwargs):
        del args, kwargs
        raise AssertionError(
            "CP62 definition builder crossed the no-execution boundary"
        )

    monkeypatch.setattr(capsule.os, "posix_spawn", bomb)
    monkeypatch.setattr(capsule.os, "posix_spawnp", bomb)
    monkeypatch.setattr(capsule.os, "open", bomb)
    monkeypatch.setattr(capsule.os, "listdir", bomb)
    monkeypatch.setattr(capsule.os, "walk", bomb)
    monkeypatch.setattr(capsule.os, "urandom", bomb)
    bundle = capsule.cp62_execution_capsule_bundle()
    assert bundle.calibration_only is True
    assert bundle.production_requests_executed is False


def test_runtime_source_abi_candidate_is_exact_but_nonportable_and_nonoperational() -> None:
    runtime = capsule.cp62_execution_capsule_bundle().runtime_source_abi_lock
    assert runtime.runtime_profile_id == (
        "cp62-darwin-arm64-cpython3115-numpy246-scipy1171-calibration"
    )
    assert runtime.python_version == "3.11.5"
    assert runtime.python_implementation == "CPython"
    assert runtime.python_soabi == "cpython-311-darwin"
    assert runtime.python_executable_realpath_role == (
        "Library-Frameworks-Python-3.11-python3.11"
    )
    assert runtime.python_executable_bytes == 152_624
    assert runtime.python_executable_sha256 == (
        "ff2d7180d4aa2dcc03193194c1999509239e00101ade54fcdd736d9fc25bd0c6"
    )
    assert runtime.python_framework_bytes == 14_204_096
    assert runtime.python_framework_sha256 == (
        "0d05199d9881aaf901bcba66ce734e9563962a3d745c136d5d056a5f7b4be877"
    )
    assert runtime.pyvenv_cfg_bytes == 343
    assert runtime.pyvenv_cfg_sha256 == (
        "27b7b9074cde30bc28e757484a301498e391d2abe48e7b75ba822480acecebfa"
    )
    assert runtime.stdlib_file_count == 2434
    assert runtime.stdlib_symlink_count == 2
    assert runtime.stdlib_total_bytes == 63_614_440
    assert runtime.stdlib_closure_sha256 == (
        "085941fc71c7e7d70f0b483d5ce763b10504edde09b77a0e8f00439c544af914"
    )
    assert runtime.dependency_lock_sha256 == (
        "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d"
    )
    assert runtime.numpy_version == "2.4.6"
    assert runtime.numpy_record_sha256 == (
        "309c7993f01d68786221ef82fa233ca1a4fae7e88f34d24a033277f7ed680afb"
    )
    assert runtime.numpy_payload_closure_sha256 == (
        "5e015638adcd22cdc32e835eb48f1c82d1f1ec617a5af9f71ca89ad3f8179b30"
    )
    assert runtime.scipy_version == "1.17.1"
    assert runtime.scipy_record_sha256 == (
        "e354befae57c8db19038d4b603e25160c143d71841c99072b2eeb3298c031ebb"
    )
    assert runtime.scipy_payload_closure_sha256 == (
        "ac4fc6789e36558a2cc48eaab89214faf8b3bccfb889029115e048acf6d8488e"
    )
    assert runtime.threadpoolctl_version == "3.6.0"
    assert runtime.threadpoolctl_record_sha256 == (
        "45ec1ffcec4eabed9558f14385fc6f6122ac97461acce1bdbc962631b7f0efc4"
    )
    assert runtime.numpy_multiarray_sha256 == (
        "2a5f2e415c5e582109b015eafd0da1ce887b3e3006969369fe2e5e5b27720acd"
    )
    assert runtime.numpy_philox_sha256 == (
        "995b0916b06a8df18dfc2085df33d7c80ea0e27b1ce84a5ebe0bab71d9e0b8a0"
    )
    assert runtime.numpy_generator_sha256 == (
        "b492b97c917d15e0c7d17f2243b0c71ff4198e1fc193d4485e0136610677ec0a"
    )
    assert runtime.scipy_special_ufuncs_sha256 == (
        "edc1aa109be752f742d2cec328f2fcdcb29f947f24e91a41326ba92bf770dbd6"
    )
    assert runtime.decimal_module_version == "1.70"
    assert runtime.libmpdec_version == "2.5.1"
    assert runtime.decimal_extension_sha256 == (
        "4bca4ab8d399c2e4e105823e9857917b8d7daad0b3cd76110cfe2b552def8520"
    )
    assert runtime.math_extension_sha256 == (
        "b477f5570d9d57894c9146bc2ae2aad890b7ef06d2ba4d31753de22bbc1e4fb5"
    )
    assert runtime.platform_system == "Darwin"
    assert runtime.platform_release == "25.3.0"
    assert runtime.platform_version == "macOS-26.3.1-build-25D2128"
    assert runtime.machine == "arm64"
    assert runtime.cpu_model == "Apple-M1-Pro"
    assert runtime.byteorder == "little"
    assert runtime.floating_rounding_mode == "FE_TONEAREST-0"
    assert runtime.sanitized_child_environment == (
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
    assert runtime.base_local_source_module_count == 29
    assert runtime.base_local_source_capsule_sha256 == (
        "fbe8188acd893d98b7e362a3440f6ecc00035448ed40785f4852507642755daf"
    )
    assert runtime.cp62_source_self_hash_bound_externally is True
    assert runtime.source_file_observation_is_executed_bytecode_attestation is False
    assert runtime.concurrent_workspace_mutation_in_threat_model is False
    assert runtime.candidate_observed_in_two_clean_children is True
    assert runtime.runtime_path_is_semantic is False
    assert runtime.runtime_portable is False
    assert runtime.production_runtime_match_verified is False
    assert runtime.transform_law_theorem_proved is False


def test_pinned_interpreter_and_native_images_match_the_runtime_lock() -> None:
    import importlib

    runtime = capsule.cp62_execution_capsule_bundle().runtime_source_abi_lock
    executable = Path(sys.executable).resolve()
    assert executable.stat().st_size == runtime.python_executable_bytes
    assert _sha256(executable) == runtime.python_executable_sha256
    expected_images = {
        "numpy._core._multiarray_umath": runtime.numpy_multiarray_sha256,
        "numpy.random._philox": runtime.numpy_philox_sha256,
        "numpy.random._generator": runtime.numpy_generator_sha256,
        "scipy.special._special_ufuncs": runtime.scipy_special_ufuncs_sha256,
        "_decimal": runtime.decimal_extension_sha256,
        "math": runtime.math_extension_sha256,
    }
    for module_name, expected_sha256 in expected_images.items():
        loaded = importlib.import_module(module_name)
        assert _sha256(Path(loaded.__file__).resolve()) == expected_sha256


def test_supervisor_contract_keeps_timeout_and_infrastructure_disjoint() -> None:
    supervisor = capsule.cp62_execution_capsule_bundle().supervisor_contract
    assert supervisor.child_start_mode == (
        "fresh-posix-spawn-exec-new-session-no-application-fork"
    )
    assert supervisor.deadline_clock == "parent-monotonic-ns"
    assert supervisor.deadline_seconds == 300
    assert supervisor.completion_strictly_before_deadline_required is True
    assert supervisor.equality_at_deadline_is_timeout is True
    assert supervisor.termination_grace_seconds == 2
    assert supervisor.reap_ceiling_seconds == 5
    assert supervisor.timeout_status == "timeout-censored-at-deadline"
    assert supervisor.timeout_is_semantic_nonreturn is False
    assert supervisor.no_retry is True
    assert supervisor.infrastructure_failure_invalidates_entire_attempt is True
    assert supervisor.infrastructure_failure_folded_into_execution_failure is False
    assert supervisor.infrastructure_failure_folded_into_timeout is False
    assert supervisor.calibration_concurrency == 1
    assert supervisor.calibration_launch_limit == 8
    assert supervisor.production_entry_point_enabled is False


def test_stdio_collision_staging_duplicates_below_three_and_closes_original(
    monkeypatch,
) -> None:
    fcntl = __import__("fcntl")
    calls = []
    closed = []

    def fake_fcntl(file_descriptor, command, minimum):
        calls.append((file_descriptor, command, minimum))
        return 9

    monkeypatch.setattr(fcntl, "fcntl", fake_fcntl)
    monkeypatch.setattr(capsule.os, "close", closed.append)
    assert capsule._staging_file_descriptor(1) == 9
    assert calls == [(1, fcntl.F_DUPFD_CLOEXEC, 3)]
    assert closed == [1]
    assert capsule._staging_file_descriptor(3) == 3
    assert calls == [(1, fcntl.F_DUPFD_CLOEXEC, 3)]


def test_spawn_setup_failure_closes_every_fd_and_kills_spawned_group(
    monkeypatch,
) -> None:
    pipes = iter(((10, 11), (12, 13)))
    closed = []
    terminated = []
    spawn_call = {}

    monkeypatch.setattr(capsule.os, "pipe", lambda: next(pipes))
    monkeypatch.setattr(capsule.os, "open", lambda *_args: 14)
    monkeypatch.setattr(capsule, "_staging_file_descriptor", lambda value: value)
    monkeypatch.setattr(capsule.os, "close", closed.append)

    def fake_spawn(executable, arguments, environment, **kwargs):
        spawn_call.update(
            executable=executable,
            arguments=arguments,
            environment=environment,
            kwargs=kwargs,
        )
        return 321

    def fake_set_blocking(file_descriptor, blocking):
        assert blocking is False
        if file_descriptor == 12:
            raise OSError("hostile nonblocking setup failure")

    def fake_terminate(pid, status, *, allow_grace):
        terminated.append((pid, status, allow_grace))
        return 9, True, True, True

    monkeypatch.setattr(capsule.os, "posix_spawn", fake_spawn)
    monkeypatch.setattr(capsule.os, "set_blocking", fake_set_blocking)
    monkeypatch.setattr(capsule, "_terminate_and_reap", fake_terminate)
    with pytest.raises(capsule.CP62ExecutionCapsuleError) as caught:
        capsule._spawn_calibration_child("m1-rejection-a64", 1, 1)
    assert caught.value.code == "CHILD_SPAWN_FAILURE"
    assert set(closed) == {10, 11, 12, 13, 14}
    assert terminated == [(321, None, False)]
    assert spawn_call["kwargs"]["setsid"] is True
    assert spawn_call["arguments"][1:5] == ("-S", "-s", "-P", "-u")
    assert spawn_call["environment"] == dict(
        capsule.CP62_TEST28_SANITIZED_CHILD_ENVIRONMENT
    )
    for action in spawn_call["kwargs"]["file_actions"]:
        assert action[1] >= 3


def test_prespawn_partial_pipe_failure_closes_staged_descriptors(monkeypatch) -> None:
    calls = 0
    closed = []
    terminated = []

    def fake_pipe():
        nonlocal calls
        calls += 1
        if calls == 1:
            return 10, 11
        raise OSError("hostile second-pipe failure")

    monkeypatch.setattr(capsule.os, "pipe", fake_pipe)
    monkeypatch.setattr(capsule.os, "close", closed.append)
    monkeypatch.setattr(
        capsule,
        "_terminate_and_reap",
        lambda *args, **kwargs: terminated.append((args, kwargs)),
    )
    with pytest.raises(capsule.CP62ExecutionCapsuleError) as caught:
        capsule._spawn_calibration_child("m1-rejection-a64", 1, 1)
    assert caught.value.code == "CHILD_SPAWN_FAILURE"
    assert set(closed) == {10, 11}
    assert terminated == []


def test_partial_selector_registration_failure_closes_fds_and_group(
    monkeypatch,
) -> None:
    class Key:
        def __init__(self, file_descriptor):
            self.fd = file_descriptor

    class HostileSelector:
        def __init__(self):
            self.mapping = {}
            self.closed = False

        def register(self, file_descriptor, _events, _data):
            if file_descriptor == 12:
                raise OSError("hostile selector registration failure")
            self.mapping[file_descriptor] = Key(file_descriptor)

        def unregister(self, file_descriptor):
            self.mapping.pop(file_descriptor)

        def get_map(self):
            return self.mapping

        def close(self):
            self.closed = True

    selector = HostileSelector()
    closed = []
    terminated = []
    bundle = capsule.cp62_execution_capsule_bundle()
    case = bundle.calibration_cases[0]
    row = bundle.request_bindings[case.row_ordinal - 1]
    monkeypatch.setattr(
        capsule, "_spawn_calibration_child", lambda *_args: (321, 10, 12)
    )
    monkeypatch.setattr(capsule, "_poll_child", lambda _pid, status: status)
    monkeypatch.setattr(capsule.selectors, "DefaultSelector", lambda: selector)
    monkeypatch.setattr(capsule, "_safe_close", closed.append)

    def fake_terminate(pid, status, *, allow_grace):
        terminated.append((pid, status, allow_grace))
        return 9, True, True, True

    monkeypatch.setattr(capsule, "_terminate_and_reap", fake_terminate)
    with pytest.raises(capsule.CP62ExecutionCapsuleError) as caught:
        capsule._supervise_calibration_case(case, row, 1)
    assert caught.value.code == "CHILD_SUPERVISOR_INFRASTRUCTURE_FAILURE"
    assert set(closed) == {10, 12}
    assert terminated == [(321, None, False)]
    assert selector.closed is True


def test_cleanup_kills_surviving_group_even_after_leader_was_reaped(
    monkeypatch,
) -> None:
    signals = []
    group_states = iter((True, True, False, False))
    monkeypatch.setattr(
        capsule.os, "killpg", lambda pid, sent: signals.append((pid, sent))
    )
    monkeypatch.setattr(
        capsule, "_process_group_exists", lambda _pid: next(group_states)
    )
    monkeypatch.setattr(capsule.time, "monotonic_ns", lambda: 0)
    (
        status,
        kill_attempted,
        termination_attempted,
        termination_delivered,
    ) = capsule._terminate_and_reap(321, 0, allow_grace=False)
    assert status == 0
    assert kill_attempted is True
    assert termination_attempted is True
    assert termination_delivered is True
    assert signals == [
        (321, capsule.signal.SIGTERM),
        (321, capsule.signal.SIGKILL),
    ]


def test_cleanup_records_no_signal_attempt_for_already_absent_reaped_group(
    monkeypatch,
) -> None:
    monkeypatch.setattr(capsule, "_process_group_exists", lambda _pid: False)

    def bomb(*_args):
        raise AssertionError("an absent reaped process group was signalled")

    monkeypatch.setattr(capsule.os, "killpg", bomb)
    assert capsule._terminate_and_reap(321, 0, allow_grace=False) == (
        0,
        False,
        False,
        False,
    )


def test_cleanup_preprobe_latches_absence_and_never_signals_or_reprobes(
    monkeypatch,
) -> None:
    probes = []
    signals = []

    def probe_once(pid):
        probes.append(pid)
        if len(probes) != 1:
            raise AssertionError("cleanup reprobed an absent numeric PGID")
        return False

    monkeypatch.setattr(capsule, "_process_group_exists", probe_once)
    monkeypatch.setattr(capsule, "_poll_child", lambda _pid, _status: 0)
    monkeypatch.setattr(capsule.time, "monotonic_ns", lambda: 0)
    monkeypatch.setattr(capsule.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        capsule.os, "killpg", lambda pid, sent: signals.append((pid, sent))
    )
    assert capsule._terminate_and_reap(321, None, allow_grace=True) == (
        0,
        False,
        False,
        False,
    )
    assert probes == [321]
    assert signals == []


def test_cleanup_term_esrch_latches_absence_and_suppresses_kill_and_reprobe(
    monkeypatch,
) -> None:
    probes = []
    signals = []

    def probe_once(pid):
        probes.append(pid)
        if len(probes) != 1:
            raise AssertionError("TERM ESRCH did not latch group absence")
        return True

    def term_esrch(pid, sent):
        signals.append((pid, sent))
        if sent == capsule.signal.SIGTERM:
            raise ProcessLookupError
        raise AssertionError("SIGKILL followed TERM ESRCH")

    monkeypatch.setattr(capsule, "_process_group_exists", probe_once)
    monkeypatch.setattr(capsule.os, "killpg", term_esrch)
    monkeypatch.setattr(capsule, "_poll_child", lambda _pid, _status: 0)
    monkeypatch.setattr(capsule.time, "monotonic_ns", lambda: 0)
    assert capsule._terminate_and_reap(321, None, allow_grace=False) == (
        0,
        False,
        True,
        False,
    )
    assert probes == [321]
    assert signals == [(321, capsule.signal.SIGTERM)]


def test_cleanup_kill_esrch_latches_absence_and_suppresses_final_reprobe(
    monkeypatch,
) -> None:
    probes = []
    signals = []

    def probe_once(pid):
        probes.append(pid)
        if len(probes) != 1:
            raise AssertionError("SIGKILL ESRCH did not latch group absence")
        return True

    def kill_esrch(pid, sent):
        signals.append((pid, sent))
        if sent == capsule.signal.SIGKILL:
            raise ProcessLookupError

    monkeypatch.setattr(capsule, "_process_group_exists", probe_once)
    monkeypatch.setattr(capsule.os, "killpg", kill_esrch)
    monkeypatch.setattr(capsule, "_poll_child", lambda _pid, _status: 0)
    monkeypatch.setattr(capsule.time, "monotonic_ns", lambda: 0)
    assert capsule._terminate_and_reap(321, None, allow_grace=False) == (
        0,
        True,
        True,
        True,
    )
    assert probes == [321]
    assert signals == [
        (321, capsule.signal.SIGTERM),
        (321, capsule.signal.SIGKILL),
    ]


def test_late_validation_timeout_never_reprobes_an_absent_reaped_group(
    monkeypatch,
) -> None:
    class Key:
        def __init__(self, file_descriptor):
            self.fd = file_descriptor

    class DrainedSelector:
        def __init__(self):
            self.mapping = {}

        def register(self, file_descriptor, _events, _data):
            self.mapping[file_descriptor] = Key(file_descriptor)

        def unregister(self, file_descriptor):
            self.mapping.pop(file_descriptor)

        def get_map(self):
            return self.mapping

        def close(self):
            pass

    full = _closed_failure_raw_record(
        "execution-failure-before-deadline", "score_evaluation_failure"
    )
    child_payload = {
        key: full[key]
        for key in full
        if key not in ("supervisor_custody", "raw_sha256")
    }
    encoded = json.dumps(
        child_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    child_frame = len(encoded).to_bytes(8, "big") + encoded
    bundle = capsule.cp62_execution_capsule_bundle()
    case = bundle.calibration_cases[0]
    row = bundle.request_bindings[case.row_ordinal - 1]
    selector = DrainedSelector()
    clock = iter((0, 1, 2, 300_000_000_000))
    probes = []

    def fake_read(active_selector, stdout, stderr, *, timeout):
        del stderr, timeout
        stdout.extend(child_frame)
        for key in tuple(active_selector.get_map().values()):
            active_selector.unregister(key.fd)

    def probe_once(pid):
        probes.append(pid)
        if len(probes) != 1:
            raise AssertionError("an already-absent numeric PGID was reprobed")
        return False

    monkeypatch.setattr(capsule.time, "monotonic_ns", lambda: next(clock))
    monkeypatch.setattr(
        capsule, "_spawn_calibration_child", lambda *_args: (321, 10, 12)
    )
    monkeypatch.setattr(capsule, "_poll_child", lambda _pid, _status: 0)
    monkeypatch.setattr(capsule.selectors, "DefaultSelector", lambda: selector)
    monkeypatch.setattr(capsule, "_read_child_streams", fake_read)
    monkeypatch.setattr(capsule, "_process_group_exists", probe_once)

    def cleanup_bomb(*_args, **_kwargs):
        raise AssertionError("an absent reaped process group entered cleanup")

    monkeypatch.setattr(capsule, "_terminate_and_reap", cleanup_bomb)
    raw = capsule.cp62_validate_raw_record_bytes(
        capsule._supervise_calibration_case(case, row, 1)
    )
    assert raw["phase"] == "timeout-at-deadline"
    assert raw["supervisor_custody"]["exit_code"] == 0
    assert raw["supervisor_custody"]["term_signal"] is None
    assert raw["supervisor_custody"]["termination_attempted"] is False
    assert raw["supervisor_custody"]["termination_signal_delivered"] is False
    assert raw["supervisor_custody"]["kill_attempted"] is False
    assert probes == [321]


def test_supervisor_treats_exact_deadline_equality_as_closed_timeout(
    monkeypatch,
) -> None:
    class Key:
        def __init__(self, file_descriptor):
            self.fd = file_descriptor

    class EmptyableSelector:
        def __init__(self):
            self.mapping = {}
            self.closed = False

        def register(self, file_descriptor, _events, _data):
            self.mapping[file_descriptor] = Key(file_descriptor)

        def unregister(self, file_descriptor):
            self.mapping.pop(file_descriptor)

        def get_map(self):
            return self.mapping

        def close(self):
            self.closed = True

    bundle = capsule.cp62_execution_capsule_bundle()
    case = bundle.calibration_cases[0]
    row = bundle.request_bindings[case.row_ordinal - 1]
    selector = EmptyableSelector()
    clock = iter((0, 300_000_000_000, 300_000_000_000))
    closed = []
    terminated = []
    cleanup_events = []
    monkeypatch.setattr(capsule.time, "monotonic_ns", lambda: next(clock))
    monkeypatch.setattr(
        capsule, "_spawn_calibration_child", lambda *_args: (321, 10, 12)
    )
    monkeypatch.setattr(capsule, "_poll_child", lambda _pid, status: status)
    monkeypatch.setattr(capsule.selectors, "DefaultSelector", lambda: selector)

    def fake_close(file_descriptor):
        closed.append(file_descriptor)
        cleanup_events.append(("close", file_descriptor))

    monkeypatch.setattr(capsule, "_safe_close", fake_close)

    def fake_terminate(pid, status, *, allow_grace):
        terminated.append((pid, status, allow_grace))
        cleanup_events.append(("terminate", pid))
        return capsule.signal.SIGTERM, False, True, True

    monkeypatch.setattr(capsule, "_terminate_and_reap", fake_terminate)
    payload = capsule._supervise_calibration_case(case, row, 1)
    raw = capsule.cp62_validate_raw_record_bytes(payload)
    assert raw["phase"] == "timeout-at-deadline"
    assert raw["closed_status"] == "timeout-censored-at-deadline"
    assert raw["supervisor_custody"]["terminal_monotonic_ns"] == "300000000000"
    assert raw["supervisor_custody"]["term_signal"] == capsule.signal.SIGTERM
    assert raw["supervisor_custody"]["termination_attempted"] is True
    assert raw["supervisor_custody"]["termination_signal_delivered"] is True
    assert raw["supervisor_custody"]["kill_attempted"] is False
    assert set(closed) == {10, 12}
    assert terminated == [(321, None, True)]
    assert cleanup_events[0] == ("terminate", 321)
    assert selector.closed is True


@pytest.mark.parametrize(
    "wait_status",
    (0, capsule.signal.SIGTERM, capsule.signal.SIGKILL),
)
def test_timeout_accepts_only_natural_zero_or_supervisor_terminal_signal(
    wait_status,
) -> None:
    capsule._require_timeout_terminal_status(wait_status)


@pytest.mark.parametrize(
    "wait_status",
    (1 << 8, capsule.signal.SIGINT, 0x7F),
)
def test_timeout_refuses_abnormal_or_nonterminal_wait_status(wait_status) -> None:
    with pytest.raises(capsule.CP62ExecutionCapsuleError) as caught:
        capsule._require_timeout_terminal_status(wait_status)
    assert caught.value.code == "CHILD_ABNORMAL_EXIT_AT_DEADLINE"


def test_raw_and_stable_schema_caps_are_exact_and_unallocated() -> None:
    bundle = capsule.cp62_execution_capsule_bundle()
    raw = bundle.raw_record_schema
    stable = bundle.stable_trace_projection_contract
    assert raw.raw_frame_max_bytes == 16 * 1024 * 1024
    assert raw.maximum_future_raw_aggregate_bytes == 512 * 1024**3
    assert raw.capacity_receipt_present is False
    assert raw.child_frame_encoding == (
        "one-uint64-big-endian-length-prefixed-canonical-json-frame"
    )
    assert raw.public_raw_record_encoding == "unframed-canonical-json-object-bytes"
    assert raw.configuration_values_retained_not_digest_only is True
    assert raw.complete_kernel_trace_required_for_validated_returns is True
    assert raw.future_production_shape_predeclared is True
    assert raw.production_schema_frozen is False
    assert raw.production_records_observed is False
    assert stable.stable_trace_max_bytes == 8 * 1024 * 1024
    assert stable.recompute_owned_leaf_hashes is True
    assert stable.inherited_kernel_hashes_semantically_authoritative is False
    assert stable.raw_trace_retained_separately is True
    assert stable.calibration_cross_process_parity_required is True
    assert stable.calibration_cross_process_parity_observed is True
    assert stable.production_cross_process_parity_observed is False
    assert stable.full_trace_law_estimated is False
    assert stable.total_variation_estimated is False


def test_raw_validator_accepts_one_exact_bound_calibration_return(
    calibration_frames,
) -> None:
    raw = _raw_record(calibration_frames)
    encoded = _raw_bytes(calibration_frames)
    assert capsule.cp62_validate_raw_record_bytes(encoded) == raw


@pytest.mark.parametrize(
    "case_id,fixture_id,strategy,budget,row_ordinal,seed",
    _CALIBRATION_CASES,
)
def test_public_calibration_runner_has_exact_two_process_stable_parity(
    calibration_frames,
    case_id,
    fixture_id,
    strategy,
    budget,
    row_ordinal,
    seed,
) -> None:
    repetitions = calibration_frames[case_id]
    assert len(repetitions) == 2
    raw_records = []
    stable_records = []
    stable_bytes = []
    for payload, raw in repetitions:
        assert type(payload) is bytes
        assert len(payload) <= 16 * 1024 * 1024
        assert capsule.cp62_validate_raw_record_bytes(payload) == raw
        assert (
            raw["case_id"],
            raw["fixture_id"],
            raw["strategy"],
            raw["budget"],
            raw["row_ordinal"],
            raw["seed_hex"],
        ) == (
            case_id,
            fixture_id,
            strategy,
            budget,
            row_ordinal,
            f"{seed:016x}",
        )
        assert raw["phase"] == "returned-before-deadline"
        assert raw["failure_code"] is None

        supervisor = raw["supervisor_custody"]
        assert supervisor["pid"] == supervisor["process_group"]
        assert supervisor["exit_code"] == 0
        assert supervisor["term_signal"] is None
        assert supervisor["completion_strictly_before_deadline"] is True
        assert supervisor["exact_one_frame"] is True
        assert supervisor["termination_attempted"] is False
        assert supervisor["termination_signal_delivered"] is False
        assert supervisor["kill_attempted"] is False
        assert supervisor["reaped"] is True
        assert supervisor["stderr_bytes"] == 0
        assert supervisor["stderr_hex"] == ""
        assert supervisor["stderr_sha256"] == hashlib.sha256(b"").hexdigest()
        assert (
            int(supervisor["start_monotonic_ns"])
            < int(supervisor["terminal_monotonic_ns"])
            < int(supervisor["deadline_monotonic_ns"])
        )

        child_payload = {
            key: raw[key]
            for key in raw
            if key not in ("supervisor_custody", "raw_sha256")
        }
        child_payload_bytes = json.dumps(
            child_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
        child_frame = len(child_payload_bytes).to_bytes(8, "big") + child_payload_bytes
        assert supervisor["frame_bytes"] == len(child_frame)
        assert (
            supervisor["child_frame_sha256"] == hashlib.sha256(child_frame).hexdigest()
        )

        semantic = raw["kernel_trace"]["semantic"]
        volatile = raw["kernel_trace"]["volatile_custody"]
        (
            expected_status,
            expected_index,
            expected_acceptances,
        ) = _EXPECTED_CALIBRATION_OUTCOMES[case_id]
        assert semantic["strategy"] == strategy
        assert semantic["budget"] == budget
        assert semantic["result_status"] == expected_status
        assert semantic["selected_index"] == expected_index
        assert len(volatile["nested_record_custody"]) == budget
        if strategy == "bounded-rejection":
            assert len(semantic["attempts"]) == budget
            assert semantic["particles"] == []
            assert semantic["normalized_weights_float64_be"] == []
            assert sum(attempt["accepted"] for attempt in semantic["attempts"]) == (
                expected_acceptances
            )
            assert semantic["selected_configuration"] is not None
        else:
            assert semantic["attempts"] == []
            assert len(semantic["particles"]) == budget
            assert len(semantic["normalized_weights_float64_be"]) == budget
            assert type(semantic["selected_index"]) is int
            assert semantic["selected_configuration"] is not None

        stable = capsule.cp62_project_stable_trace(raw)
        encoded = capsule.cp62_stable_trace_canonical_json_bytes(stable)
        assert len(encoded) <= 8 * 1024 * 1024
        stable_records.append(stable)
        stable_bytes.append(encoded)
        raw_records.append(raw)

    assert raw_records[0]["raw_sha256"] != raw_records[1]["raw_sha256"]
    assert (
        raw_records[0]["supervisor_custody"]["pid"]
        != raw_records[1]["supervisor_custody"]["pid"]
    )
    assert stable_records[0] == stable_records[1]
    assert stable_bytes[0] == stable_bytes[1]
    stable_receipts = tuple(
        (len(encoded), capsule.cp62_stable_trace_sha256(stable))
        for encoded, stable in zip(stable_bytes, stable_records, strict=True)
    )
    assert stable_receipts == (_EXPECTED_STABLE_TRACE_RECEIPTS[case_id],) * 2


def test_frozen_calibration_launch_limit_closes_after_two_by_four_runs(
    calibration_frames,
) -> None:
    assert set(calibration_frames) == {row[0] for row in _CALIBRATION_CASES}
    with pytest.raises(capsule.CP62ExecutionCapsuleError) as caught:
        capsule.cp62_run_calibration_case("m1-rejection-a64")
    assert caught.value.code == "CALIBRATION_LAUNCH_LIMIT_REACHED"


@pytest.mark.parametrize(
    "change",
    (
        {"case_id": "m2-rejection-a64"},
        {"row_ordinal": 16},
        {"row_key": "wrong-row"},
        {"fixture_id": "T28-M2-Q"},
        {"strategy": "fixed-budget-sir"},
        {"budget": 1},
        {"seed_hex": "0000000000000000"},
        {"seed_free_request_sha256": "f" * 64},
        {"runtime_lock_sha256": "e" * 64},
    ),
)
def test_redigested_raw_record_cannot_break_case_request_runtime_binding(
    calibration_frames, change
) -> None:
    with pytest.raises((TypeError, ValueError)):
        capsule.cp62_validate_raw_record_bytes(_raw_bytes(calibration_frames, **change))


@pytest.mark.parametrize(
    "change",
    (
        {"phase": "made-up"},
        {"closed_status": "nonreturn"},
        {"failure_code": "arbitrary-unbounded-exception"},
        {"phase": 1},
        {"closed_status": None},
        {"kernel_trace": []},
        {"supervisor_custody": []},
    ),
)
def test_redigested_raw_record_requires_closed_phase_status_and_nested_schema(
    calibration_frames,
    change,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        capsule.cp62_validate_raw_record_bytes(_raw_bytes(calibration_frames, **change))


@pytest.mark.parametrize(
    "path,replacement",
    (
        (("stable_request_sha256",), "f" * 64),
        (("proposal_seed_hex",), "0000000000000000"),
        (("formal_test_28_closed",), True),
        (("operational_reference_sampling_law_verified",), True),
        (("path_or_sampler_admitted",), True),
        (("runtime_observation", "cp62_source_sha256"), "f" * 64),
        (("resource_preflight", "fixed_budget_work_certified"), False),
    ),
)
def test_fully_redigested_return_cannot_break_bindings_or_promote_nonclaims(
    calibration_frames, path, replacement
) -> None:
    raw = copy.deepcopy(calibration_frames["m1-rejection-a64"][0][1])
    target = raw["kernel_trace"]["semantic"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    _redigest_returned_raw_record(raw)
    encoded = json.dumps(
        raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    with pytest.raises((TypeError, ValueError)):
        capsule.cp62_validate_raw_record_bytes(encoded)


def test_fully_redigested_rejection_decision_must_match_exact_quota(
    calibration_frames,
) -> None:
    raw = copy.deepcopy(calibration_frames["m1-rejection-a64"][0][1])
    attempt = raw["kernel_trace"]["semantic"]["attempts"][0]
    attempt["accepted"] = not attempt["accepted"]
    attempt.pop("cp62_attempt_sha256")
    raw["kernel_trace"]["semantic"]["attempts"][0] = _owned_json_leaf(
        b"cp62-test28-rejection-attempt-v1",
        attempt,
        "cp62_attempt_sha256",
    )
    _redigest_returned_raw_record(raw)
    encoded = json.dumps(
        raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    with pytest.raises((TypeError, ValueError)):
        capsule.cp62_validate_raw_record_bytes(encoded)


def test_fully_redigested_sir_weights_and_selection_are_replayed(
    calibration_frames,
) -> None:
    original = calibration_frames["m1-sir-j512"][0][1]

    weight_tamper = copy.deepcopy(original)
    semantic = weight_tamper["kernel_trace"]["semantic"]
    particle = semantic["particles"][0]
    replacement = {"$float64_be": "3ff0000000000000"}
    particle["normalized_weight_float64_be"] = replacement
    particle.pop("cp62_particle_sha256")
    semantic["particles"][0] = _owned_json_leaf(
        b"cp62-test28-sir-particle-v1",
        particle,
        "cp62_particle_sha256",
    )
    semantic["normalized_weights_float64_be"][0] = replacement
    _redigest_returned_raw_record(weight_tamper)

    selection_tamper = copy.deepcopy(original)
    selection_semantic = selection_tamper["kernel_trace"]["semantic"]
    selection_semantic["selected_index"] = (
        selection_semantic["selected_index"] + 1
    ) % 512
    _redigest_returned_raw_record(selection_tamper)

    for raw in (weight_tamper, selection_tamper):
        encoded = json.dumps(
            raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
        with pytest.raises((TypeError, ValueError)):
            capsule.cp62_validate_raw_record_bytes(encoded)


@pytest.mark.parametrize(
    "case_id,field",
    (
        ("m1-rejection-a64", "configuration_sha256"),
        ("m1-rejection-a64", "source_evaluation_sha256"),
        ("m1-rejection-a64", "facade_evaluation_sha256"),
        ("m1-rejection-a64", "scored_sha256"),
        ("m1-rejection-a64", "quota_sha256"),
        ("m1-rejection-a64", "attempt_sha256"),
        ("m1-sir-j512", "particle_sha256"),
    ),
)
def test_redigested_validated_return_requires_all_common_and_strategy_custody(
    calibration_frames, case_id, field
) -> None:
    raw = copy.deepcopy(calibration_frames[case_id][0][1])
    raw["kernel_trace"]["volatile_custody"]["nested_record_custody"][0][field] = None
    _redigest_returned_raw_record(raw)
    encoded = json.dumps(
        raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    with pytest.raises((TypeError, ValueError)):
        capsule.cp62_validate_raw_record_bytes(encoded)


def test_raw_decoder_rejects_duplicate_keys_bom_trailing_bytes_and_noncanonical(
    calibration_frames,
) -> None:
    encoded = _raw_bytes(calibration_frames)
    duplicate = encoded[:-1] + b',"schema":"duplicate"}'
    for hostile in (
        duplicate,
        b"\xef\xbb\xbf" + encoded,
        encoded + b"\n",
        encoded.replace(b'"budget":64', b'"budget": 64'),
    ):
        with pytest.raises((TypeError, ValueError)):
            capsule.cp62_validate_raw_record_bytes(hostile)


def test_raw_decoder_enforces_plain_json_depth_float_and_frame_resource_caps() -> None:
    nested: object = 0
    for _ in range(66):
        nested = [nested]
    deep = json.dumps({"x": nested}, sort_keys=True, separators=(",", ":")).encode(
        "ascii"
    )
    for hostile in (
        deep,
        b'{"x":1.0}',
        b"x" * (16 * 1024 * 1024 + 1),
    ):
        with pytest.raises((TypeError, ValueError)):
            capsule.cp62_validate_raw_record_bytes(hostile)


def test_timeout_censor_is_a_closed_stable_outcome_not_semantic_nonreturn() -> None:
    raw = _timeout_raw_record()
    encoded = json.dumps(
        raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    assert capsule.cp62_validate_raw_record_bytes(encoded) == raw
    stable = capsule.cp62_project_stable_trace(raw)
    assert stable["phase"] == "timeout-at-deadline"
    assert stable["closed_status"] == "timeout-censored-at-deadline"
    assert stable["kernel_trace"]["outcome_kind"] == "timeout-censored"
    assert stable["kernel_trace"]["completed_kernel_trace_present"] is False
    assert stable["kernel_trace"]["timeout_is_semantic_nonreturn"] is False
    assert "supervisor_custody" not in stable
    stable_bytes = capsule.cp62_stable_trace_canonical_json_bytes(stable)
    assert (
        capsule.cp62_stable_trace_sha256(stable)
        == hashlib.sha256(b"cp62-test28-stable-trace-v1\x00" + stable_bytes).hexdigest()
    )


@pytest.mark.parametrize(
    "custody_change",
    (
        {
            "exit_code": 0,
            "term_signal": None,
            "termination_attempted": False,
            "termination_signal_delivered": False,
            "kill_attempted": False,
        },
        {
            "exit_code": None,
            "term_signal": capsule.signal.SIGKILL,
            "termination_attempted": True,
            "termination_signal_delivered": False,
            "kill_attempted": True,
        },
    ),
)
def test_timeout_closed_arm_accepts_exact_natural_zero_or_sigkill_custody(
    custody_change,
) -> None:
    raw = _timeout_raw_record()
    raw["supervisor_custody"].update(custody_change)
    raw["raw_sha256"] = _raw_digest(raw)
    encoded = json.dumps(
        raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    assert capsule.cp62_validate_raw_record_bytes(encoded) == raw


@pytest.mark.parametrize(
    "phase,failure_code",
    (
        (
            "preexecution-refusal-before-deadline",
            "plan_validation_refusal",
        ),
        (
            "preexecution-refusal-before-deadline",
            "provider_reference_binding_refusal",
        ),
        (
            "preexecution-refusal-before-deadline",
            "resource_preflight_refusal",
        ),
        (
            "preexecution-refusal-before-deadline",
            "runtime_binding_refusal",
        ),
        (
            "preexecution-refusal-before-deadline",
            "other_preexecution_refusal",
        ),
        (
            "execution-failure-before-deadline",
            "reference_sampling_failure",
        ),
        (
            "execution-failure-before-deadline",
            "score_evaluation_failure",
        ),
        (
            "execution-failure-before-deadline",
            "quota_certification_failure",
        ),
        (
            "execution-failure-before-deadline",
            "float64_normalization_failure",
        ),
        (
            "execution-failure-before-deadline",
            "categorical_selection_failure",
        ),
        (
            "execution-failure-before-deadline",
            "structural_result_validation_failure",
        ),
        (
            "execution-failure-before-deadline",
            "other_execution_failure",
        ),
    ),
)
def test_exact_closed_refusal_and_execution_failure_code_union_is_accepted(
    phase, failure_code
) -> None:
    raw = _closed_failure_raw_record(phase, failure_code)
    encoded = json.dumps(
        raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    assert capsule.cp62_validate_raw_record_bytes(encoded) == raw
    stable = capsule.cp62_project_stable_trace(encoded)
    assert stable["phase"] == phase
    assert stable["closed_status"] == phase
    assert stable["failure_code"] == failure_code
    assert stable["kernel_trace"]["completed_kernel_trace_present"] is False
    assert stable["kernel_trace"]["timeout_is_semantic_nonreturn"] is False
    assert "supervisor_custody" not in stable


@pytest.mark.parametrize(
    "phase,failure_code",
    (
        (
            "preexecution-refusal-before-deadline",
            "reference_sampling_failure",
        ),
        (
            "execution-failure-before-deadline",
            "runtime_binding_refusal",
        ),
        ("execution-failure-before-deadline", "arbitrary_failure"),
    ),
)
def test_redigested_closed_failure_cannot_cross_or_expand_code_union(
    phase, failure_code
) -> None:
    raw = _closed_failure_raw_record(phase, failure_code)
    encoded = json.dumps(
        raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    with pytest.raises((TypeError, ValueError)):
        capsule.cp62_validate_raw_record_bytes(encoded)


@pytest.mark.parametrize(
    "custody_change",
    (
        {"child_frame_sha256": "f" * 64},
        {"frame_bytes": 8},
        {"exit_code": 1},
        {"exact_one_frame": False},
        {"completion_strictly_before_deadline": False},
        {"reaped": False},
    ),
)
def test_redigested_closed_failure_requires_clean_exact_child_frame_custody(
    custody_change,
) -> None:
    raw = _closed_failure_raw_record(
        "execution-failure-before-deadline", "score_evaluation_failure"
    )
    raw["supervisor_custody"].update(custody_change)
    raw["raw_sha256"] = _raw_digest(raw)
    encoded = json.dumps(
        raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    with pytest.raises((TypeError, ValueError)):
        capsule.cp62_validate_raw_record_bytes(encoded)


@pytest.mark.parametrize(
    "custody_change",
    (
        {"completion_strictly_before_deadline": True},
        {"termination_attempted": False},
        {"reaped": False},
        {"terminal_monotonic_ns": "299999999999"},
        {"process_group": 101},
        {"exit_code": 1, "term_signal": None},
        {"exit_code": None, "term_signal": capsule.signal.SIGINT},
        {"exit_code": 0, "term_signal": capsule.signal.SIGTERM},
        {"termination_signal_delivered": False},
        {
            "term_signal": capsule.signal.SIGKILL,
            "termination_signal_delivered": True,
            "kill_attempted": False,
        },
    ),
)
def test_redigested_timeout_custody_cannot_claim_a_non_timeout(custody_change) -> None:
    raw = _timeout_raw_record()
    raw["supervisor_custody"].update(custody_change)
    raw["raw_sha256"] = _raw_digest(raw)
    encoded = json.dumps(
        raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    with pytest.raises((TypeError, ValueError)):
        capsule.cp62_validate_raw_record_bytes(encoded)


@pytest.mark.parametrize(
    "semantic_change",
    (
        {"timeout_is_semantic_nonreturn": True},
        {"completed_kernel_trace_present": True},
        {"outcome_kind": "semantic-nonreturn"},
        {"failure_code": "execution-failure"},
        {"runtime_lock_sha256": "f" * 64},
    ),
)
def test_fully_redigested_timeout_semantics_cannot_promote_a_claim(
    semantic_change,
) -> None:
    raw = _timeout_raw_record()
    semantic = dict(raw["kernel_trace"]["semantic"])
    semantic.pop("cp62_closed_trace_sha256")
    semantic.update(semantic_change)
    raw["kernel_trace"]["semantic"] = _owned_json_leaf(
        b"cp62-test28-closed-kernel-outcome-v1",
        semantic,
        "cp62_closed_trace_sha256",
    )
    raw["raw_sha256"] = _raw_digest(raw)
    encoded = json.dumps(
        raw, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    with pytest.raises((TypeError, ValueError)):
        capsule.cp62_validate_raw_record_bytes(encoded)


def test_stable_projection_excludes_all_volatile_custody(
    calibration_frames,
) -> None:
    first = calibration_frames["m1-rejection-a64"][0][1]
    second = calibration_frames["m1-rejection-a64"][1][1]
    assert first["raw_sha256"] != second["raw_sha256"]
    assert first["supervisor_custody"] != second["supervisor_custody"]
    assert (
        first["kernel_trace"]["volatile_custody"]
        != second["kernel_trace"]["volatile_custody"]
    )
    first_trace = capsule.cp62_project_stable_trace(first)
    second_trace = capsule.cp62_project_stable_trace(second)
    assert first_trace == second_trace
    assert capsule.cp62_stable_trace_sha256(
        first_trace
    ) == capsule.cp62_stable_trace_sha256(second_trace)
    encoded = capsule.cp62_stable_trace_canonical_json_bytes(first_trace)
    for forbidden in (
        b"plan_sha256",
        b"kernel_certificate_sha256",
        b"result_sha256",
        b"provider_runtime_identity",
        b"supervisor_custody",
    ):
        assert forbidden not in encoded


def test_stable_projection_retains_the_entire_validated_semantic_trace(
    calibration_frames,
) -> None:
    first = calibration_frames["m1-rejection-a64"][0][1]
    second = calibration_frames["m2-rejection-a64"][0][1]
    first_trace = capsule.cp62_project_stable_trace(first)
    second_trace = capsule.cp62_project_stable_trace(second)
    assert first_trace["kernel_trace"] == first["kernel_trace"]["semantic"]
    assert second_trace["kernel_trace"] == second["kernel_trace"]["semantic"]
    assert first_trace != second_trace
    assert capsule.cp62_stable_trace_sha256(
        first_trace
    ) != capsule.cp62_stable_trace_sha256(second_trace)


def test_stable_encoder_and_digest_reject_arbitrary_or_tampered_dicts(
    calibration_frames,
) -> None:
    trace = capsule.cp62_project_stable_trace(_raw_record(calibration_frames))
    encoded = capsule.cp62_stable_trace_canonical_json_bytes(trace)
    assert type(encoded) is bytes
    assert (
        capsule.cp62_stable_trace_sha256(trace)
        == hashlib.sha256(b"cp62-test28-stable-trace-v1\x00" + encoded).hexdigest()
    )
    for hostile in (
        {},
        {"schema": capsule.CP62_TEST28_SCHEMA_VERSION},
        {**trace, "x": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            capsule.cp62_stable_trace_canonical_json_bytes(hostile)
        with pytest.raises((TypeError, ValueError)):
            capsule.cp62_stable_trace_sha256(hostile)


def test_calibration_entry_rejects_arbitrary_cases_before_operational_imports() -> None:
    source_root = str(_ROOT / "src")
    code = r"""
import sys
from heterodiff.evaluation import mixed_initializer_test28_execution_capsule as c
for value in ("unknown", "m1-rejection-a64\x00", 1, None):
    try:
        c.cp62_run_calibration_case(value)
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("hostile calibration case was accepted")
for name in (
    "numpy", "scipy",
    "heterodiff.processes.plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2",
):
    assert name not in sys.modules, name
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = source_root
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_public_calibration_gate_enforces_concurrency_per_case_and_global_caps() -> None:
    source_root = str(_ROOT / "src")
    code = r"""
from heterodiff.evaluation import mixed_initializer_test28_execution_capsule as c
c._supervise_calibration_case = lambda case, row, ordinal: str(ordinal).encode("ascii")

assert c.cp62_run_calibration_case("m1-rejection-a64") == b"1"
assert c.cp62_run_calibration_case("m1-rejection-a64") == b"2"
try:
    c.cp62_run_calibration_case("m1-rejection-a64")
except c.CP62ExecutionCapsuleError as error:
    assert error.code == "CALIBRATION_CASE_LAUNCH_LIMIT_REACHED"
else:
    raise AssertionError("per-case launch cap was bypassed")

c._CALIBRATION_RUNNING = True
try:
    c.cp62_run_calibration_case("m2-rejection-a64")
except c.CP62ExecutionCapsuleError as error:
    assert error.code == "CALIBRATION_CONCURRENCY_REFUSED"
else:
    raise AssertionError("concurrent launch gate was bypassed")
finally:
    c._CALIBRATION_RUNNING = False

for case_id in ("m1-sir-j512", "m2-rejection-a64", "m2-sir-j512"):
    c.cp62_run_calibration_case(case_id)
    c.cp62_run_calibration_case(case_id)
assert c._CALIBRATION_LAUNCH_COUNT == 8
try:
    c.cp62_run_calibration_case("m2-sir-j512")
except c.CP62ExecutionCapsuleError as error:
    assert error.code == "CALIBRATION_LAUNCH_LIMIT_REACHED"
else:
    raise AssertionError("global launch cap was bypassed")
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = source_root
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_clean_import_and_bundle_replay_load_no_operational_dependency() -> None:
    source_root = str(_ROOT / "src")
    code = r"""
import sys
from heterodiff.evaluation import mixed_initializer_test28_execution_capsule as c
b = c.cp62_execution_capsule_bundle()
c.validate_cp62_execution_capsule_bundle(b)
for name in (
    "numpy", "scipy",
    "heterodiff.evaluation.mixed_initializer_test28_whole_seed_mc_design",
    "heterodiff.processes.plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2",
):
    assert name not in sys.modules, name
assert b.production_runner_bound is False
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = source_root
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_bundle_and_canonical_bytes_replay_identically_in_two_clean_children() -> None:
    source_root = str(_ROOT / "src")
    code = r"""
import hashlib
import json
from heterodiff.evaluation import mixed_initializer_test28_execution_capsule as c
b = c.cp62_execution_capsule_bundle()
print(json.dumps({
    "record": b.record_sha256,
    "semantic": c.cp62_execution_capsule_semantic_sha256(b),
    "canonical": hashlib.sha256(c.cp62_canonical_json_bytes(b)).hexdigest(),
}, sort_keys=True, separators=(",", ":")))
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = source_root
    outputs = []
    for _ in range(2):
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(_ROOT),
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        outputs.append(completed.stdout)
    assert outputs[0] == outputs[1]
    observed = json.loads(outputs[0])
    local = capsule.cp62_execution_capsule_bundle()
    assert observed == {
        "record": local.record_sha256,
        "semantic": local.semantic_sha256,
        "canonical": hashlib.sha256(
            capsule.cp62_canonical_json_bytes(local)
        ).hexdigest(),
    }
