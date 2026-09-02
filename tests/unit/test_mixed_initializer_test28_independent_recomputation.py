"""Hostile tests for the CP63 independent compact recomputation path."""

from __future__ import annotations

import ast
import copy
from dataclasses import fields
from fractions import Fraction
import gc
import hashlib
import inspect
import json
from pathlib import Path
import struct
import threading
from types import SimpleNamespace
import weakref

import pytest

from heterodiff.evaluation import (
    mixed_initializer_test28_independent_recomputation as oracle,
)


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = (
    _ROOT
    / "src"
    / "heterodiff"
    / "evaluation"
    / "mixed_initializer_test28_independent_recomputation.py"
)
_CP61_STABLE_DESIGN_SHA256 = (
    "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
)
_CP61_SOURCE_SHA256 = "8ea06f5cfc5cd79842e2984d5f91918463cf887c0efc2fd026490f51e66129cb"
_CP58_SOURCE_SHA256 = "24649278e40c49bb1c7eae0f3b00a3c5694020844b986aa836b98c02c3024822"
_M1_REGISTRY_SHA256 = "314a54638d17f8dcb4b4313a92594306643254ab4a958aeb9d81efd5786a0406"
_M2_REGISTRY_SHA256 = "e740e5927d2242aa0d945f4a252a638cae6aa4757f31ed24094c188b715929e8"
_CP63_RUNNER_SCHEMA = "cp63-test28-runner-recomputation-rehearsal-v1"
_REHEARSAL_PURPOSE = "development-runner-rehearsal-only"
_REHEARSAL_ID = "cp63-all-row-rehearsal-v1"
_REHEARSAL_SEED_HEX = "12a5228200019dae"
_RUNTIME_LOCK_SHA256 = (
    "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
)
_ROW1_SEED_FREE_SHA256 = (
    "a99bafb93499e89d054dd8e0df8c9a04acff29142620a7da374aa88dae53215a"
)


def test_cp63_independent_recomputation_surface_and_signatures_are_exact() -> None:
    classes = {
        "CP63CompactObservationV1",
        "CP63RehearsalRecomputationReceiptV1",
        "CP63IndependentRecomputationBundleV1",
    }
    functions = {
        "cp63_independent_recomputation_bundle": (),
        "cp63_independently_validate_stable_trace_bytes": ("payload",),
        "cp63_compact_observation": ("payload",),
        "cp63_recompute_rehearsal": ("stable_trace_payloads",),
        "cp63_recomputation_canonical_json_bytes": ("record",),
        "cp63_recomputation_sha256": ("record",),
    }
    expected = (
        classes
        | set(functions)
        | {
            "CP63IndependentRecomputationError",
            "CP63_INDEPENDENT_RECOMPUTATION_SCHEMA_VERSION",
            "CP63_INDEPENDENT_RECOMPUTATION_SCOPE",
        }
    )
    assert expected == set(oracle.__all__)
    for name in expected:
        assert hasattr(oracle, name), name
    for name, parameters in functions.items():
        assert tuple(inspect.signature(getattr(oracle, name)).parameters) == parameters


def test_cp63_independent_record_field_sets_are_exact() -> None:
    expected = {
        "CP63CompactObservationV1": (
            "schema_version",
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
            "stable_trace_sha256",
            "observable_cell_label",
            "observable_contribution_ordinal",
            "first_selected_attempt_one_based",
            "selected",
            "selected_feature_ids",
            "selected_feature_values",
            "record_sha256",
        ),
        "CP63RehearsalRecomputationReceiptV1": (
            "schema_version",
            "request_count",
            "row_ordinals",
            "logical_request_ordinals",
            "stable_trace_sha256s",
            "compact_observation_sha256s",
            "observable_contributions",
            "first_attempt_contributions",
            "selected_feature_present",
            "selected_feature_values",
            "missing_count",
            "duplicate_count",
            "invalid_count",
            "independent_parser",
            "runner_source_imported",
            "intervals_computed",
            "decision_made",
            "record_sha256",
        ),
        "CP63IndependentRecomputationBundleV1": (
            "schema_version",
            "scope",
            "cp61_source_sha256",
            "cp61_stable_design_sha256",
            "cp58_source_sha256",
            "m1_feature_registry_sha256",
            "m2_feature_registry_sha256",
            "row_count",
            "observable_estimand_ids",
            "rejection_first_attempt_estimand_ids",
            "selected_feature_estimand_ids",
            "observable_estimand_count",
            "rejection_first_attempt_estimand_count",
            "selected_feature_estimand_count",
            "estimand_count",
            "compact_projection_formula",
            "independent_parser",
            "runner_source_imported",
            "cp62_source_imported",
            "kernel_or_numerical_dependency_imported",
            "full_32768_recomputation_exposed",
            "n2048_intervals_computed",
            "decision_made",
            "runner_and_recomputation_blocker_closed",
            "confirmatory_evidence",
            "manuscript_claim",
            "formal_test_28_status",
            "formal_test_28_closed",
            "record_sha256",
        ),
    }
    for name, field_names in expected.items():
        assert tuple(item.name for item in fields(getattr(oracle, name))) == field_names


def test_cp63_independent_source_is_stdlib_only_and_import_independent() -> None:
    source = _SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_roots = {"heterodiff", "numpy", "scipy", "torch"}
    forbidden_modules = {
        "heterodiff.evaluation.mixed_initializer_test28_runner_recomputation_rehearsal",
        "heterodiff.evaluation.mixed_initializer_test28_execution_capsule",
        "heterodiff.evaluation.mixed_initializer_test28_whole_seed_mc_design",
        "heterodiff.processes.plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2",
        "heterodiff.processes.certified_initial_score_provider_v1",
        "heterodiff.evaluation.exact_rational_quadratic_initial_tilt",
    }
    imported_roots = set()
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".", 1)[0])
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
            imported_modules.add(node.module)
    assert not forbidden_roots & imported_roots
    assert not forbidden_modules & imported_modules
    for module_name in forbidden_modules:
        assert module_name not in source
    assert "__import__" not in source
    assert "import_module" not in source
    assert "sys.modules" not in source


def test_cp63_independent_bundle_freezes_554_inventory_and_no_claims() -> None:
    bundle = oracle.cp63_independent_recomputation_bundle()
    assert bundle.cp61_source_sha256 == _CP61_SOURCE_SHA256
    assert bundle.cp61_stable_design_sha256 == _CP61_STABLE_DESIGN_SHA256
    assert bundle.cp58_source_sha256 == _CP58_SOURCE_SHA256
    assert bundle.m1_feature_registry_sha256 == _M1_REGISTRY_SHA256
    assert bundle.m2_feature_registry_sha256 == _M2_REGISTRY_SHA256
    assert bundle.row_count == 16
    assert bundle.observable_estimand_count == 72
    assert bundle.rejection_first_attempt_estimand_count == 170
    assert bundle.selected_feature_estimand_count == 312
    assert bundle.estimand_count == 554
    assert bundle.runner_source_imported is False
    assert bundle.cp62_source_imported is False
    assert bundle.kernel_or_numerical_dependency_imported is False
    assert bundle.independent_parser is True
    assert bundle.full_32768_recomputation_exposed is False
    assert bundle.n2048_intervals_computed is False
    assert bundle.decision_made is False
    assert bundle.runner_and_recomputation_blocker_closed is False
    assert bundle.confirmatory_evidence is False
    assert bundle.manuscript_claim is False
    assert bundle.formal_test_28_status == "OPEN"
    assert bundle.formal_test_28_closed is False


def test_cp63_independent_estimand_inventory_is_complete_unique_and_ordered() -> None:
    bundle = oracle.cp63_independent_recomputation_bundle()
    assert len(bundle.observable_estimand_ids) == 72
    assert len(bundle.rejection_first_attempt_estimand_ids) == 170
    assert len(bundle.selected_feature_estimand_ids) == 312
    all_ids = (
        bundle.observable_estimand_ids
        + bundle.rejection_first_attempt_estimand_ids
        + bundle.selected_feature_estimand_ids
    )
    assert len(all_ids) == 554
    assert len(set(all_ids)) == 554
    assert bundle.observable_estimand_ids[0].startswith("cp61/observable/row-01/")
    assert bundle.observable_estimand_ids[-1].startswith("cp61/observable/row-16/")
    assert bundle.rejection_first_attempt_estimand_ids[0].endswith("/attempt-1")
    assert bundle.rejection_first_attempt_estimand_ids[-1].endswith("/attempt-64")


def test_cp63_all_554_estimand_ids_exactly_match_the_live_cp61_inventory() -> None:
    from heterodiff.evaluation import (
        mixed_initializer_test28_whole_seed_mc_design as cp61,
    )

    independent = oracle.cp63_independent_recomputation_bundle()
    predecessor = cp61.cp61_whole_seed_mc_design_bundle()
    assert hashlib.sha256(Path(cp61.__file__).read_bytes()).hexdigest() == (
        independent.cp61_source_sha256
    )
    assert independent.observable_estimand_ids == tuple(
        item.estimand_id for item in predecessor.observable_estimands
    )
    assert independent.rejection_first_attempt_estimand_ids == tuple(
        item.estimand_id for item in predecessor.rejection_first_attempt_estimands
    )
    assert independent.selected_feature_estimand_ids == tuple(
        item.estimand_id for item in predecessor.selected_conditional_feature_estimands
    )
    all_predecessor = (
        predecessor.observable_estimands
        + predecessor.rejection_first_attempt_estimands
        + predecessor.selected_conditional_feature_estimands
    )
    assert tuple(item.estimand_ordinal for item in all_predecessor) == tuple(
        range(1, 555)
    )
    assert independent.m1_feature_registry_sha256 == (
        predecessor.m1_feature_registry_sha256
    )
    assert independent.m2_feature_registry_sha256 == (
        predecessor.m2_feature_registry_sha256
    )


@pytest.mark.parametrize(
    "payload",
    (
        None,
        "not-bytes",
        b"",
        b"{}\n",
        b"\xef\xbb\xbf{}",
        b'{"schema":"one","schema":"two"}',
        b"x" * 8_388_609,
    ),
)
def test_cp63_independent_parser_rejects_noncanonical_or_oversized_input(
    payload,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        oracle.cp63_independently_validate_stable_trace_bytes(payload)


def test_cp63_independent_parser_enforces_depth_and_node_caps_before_schema() -> None:
    nested = None
    for _ in range(66):
        nested = [nested]
    with pytest.raises(
        oracle.CP63IndependentRecomputationError, match="depth exceeded"
    ):
        oracle.cp63_independently_validate_stable_trace_bytes(
            _plain_json_bytes({"x": nested})
        )

    with pytest.raises(
        oracle.CP63IndependentRecomputationError, match="node cap exceeded"
    ):
        oracle.cp63_independently_validate_stable_trace_bytes(
            _plain_json_bytes({"x": [None] * 262_145})
        )


@pytest.mark.parametrize(
    "payload,message",
    (
        (b'{"' + b"x" * 4_097 + b'":0}', "key is oversized"),
        (b'{"x":"' + b"y" * 4_097 + b'"}', "text is oversized"),
        (b'{"x":1' + b"0" * 5_001 + b"}", "integer is oversized"),
        (b'{"x":1.5}', "floats are forbidden"),
        (b'{"x":NaN}', "floats are forbidden"),
    ),
)
def test_cp63_independent_parser_enforces_scalar_resource_and_numeric_caps(
    payload,
    message,
) -> None:
    with pytest.raises(oracle.CP63IndependentRecomputationError, match=message):
        oracle.cp63_independently_validate_stable_trace_bytes(payload)


def _plain_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _owned_json_leaf(domain: bytes, body: dict, digest_field: str) -> dict:
    value = copy.deepcopy(body)
    value[digest_field] = hashlib.sha256(
        domain + b"\0" + _plain_json_bytes(value)
    ).hexdigest()
    return value


def _row1_request_instance_sha256() -> str:
    identity = {
        "schema": _CP63_RUNNER_SCHEMA,
        "rehearsal_id": _REHEARSAL_ID,
        "seed_ordinal": 1,
        "row_ordinal": 1,
        "logical_request_ordinal": 1,
        "row_key": "row-01/T28-M1-Q/bounded-rejection/budget-1",
        "fixture_id": "T28-M1-Q",
        "strategy": "bounded-rejection",
        "budget": 1,
        "plan_seed_hex": _REHEARSAL_SEED_HEX,
        "seed_free_request_sha256": _ROW1_SEED_FREE_SHA256,
        "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
    }
    return hashlib.sha256(
        b"cp63-test28-rehearsal-request-instance-v1\0" + _plain_json_bytes(identity)
    ).hexdigest()


def _row1_timeout_stable_trace() -> dict:
    calibration_instance_sha256 = hashlib.sha256(
        b"cp62-test28-calibration-request-instance-v1\0"
        + bytes.fromhex(_ROW1_SEED_FREE_SHA256)
        + int(_REHEARSAL_SEED_HEX, 16).to_bytes(8, "big")
    ).hexdigest()
    closed = _owned_json_leaf(
        b"cp62-test28-closed-kernel-outcome-v1",
        {
            "trace_schema": "cp62-test28-closed-kernel-outcome-v1",
            "stable_request_sha256": _ROW1_SEED_FREE_SHA256,
            "calibration_instance_sha256": calibration_instance_sha256,
            "plan_seed_hex": _REHEARSAL_SEED_HEX,
            "fixture_id": "T28-M1-Q",
            "strategy": "bounded-rejection",
            "budget": 1,
            "source_certificate_sha256": (
                "3b29d26b3f50d63e6a52ca5033264e2346d7b4175342ac86c20254b98b745cc3"
            ),
            "source_parameter_sha256": (
                "7cdd3f34b36d71fdd094c8db03dd34f1bc4aa8790c76c3f3d0409ad83e5b4dff"
            ),
            "reference_parameter_sha256": (
                "8a07e6ee27a31bbfacc7f23531ca62a02e940838dca8f7bb39d660ed5c41aefd"
            ),
            "facade_certificate_sha256": (
                "252d79a82b71951a28b5107d40f86d4a655d86242428fdae3fed8298fa35dda6"
            ),
            "adapter_role_sha256": (
                "e93c2bd1bb9181ed21538d15e5618753a92048f7f3b5647250db2c570df0b2fc"
            ),
            "initializer_role_sha256": (
                "a4ccf3fd3c63ac740e723d1bf6e30bcdb155089ce0901c0c5e0dee53936f6b38"
            ),
            "residual_context_sha256": (
                "8176a4298d195a7c4f82c579db2b23dd9fdaed9b7ffc1f687b7e980a99f1720f"
            ),
            "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
            "runtime_observation": None,
            "outcome_kind": "timeout-censored",
            "failure_code": None,
            "completed_kernel_trace_present": False,
            "timeout_is_semantic_nonreturn": False,
        },
        "cp62_closed_trace_sha256",
    )
    return {
        "schema": _CP63_RUNNER_SCHEMA,
        "purpose": _REHEARSAL_PURPOSE,
        "rehearsal_id": _REHEARSAL_ID,
        "seed_ordinal": 1,
        "row_ordinal": 1,
        "logical_request_ordinal": 1,
        "row_key": "row-01/T28-M1-Q/bounded-rejection/budget-1",
        "fixture_id": "T28-M1-Q",
        "strategy": "bounded-rejection",
        "budget": 1,
        "plan_seed_hex": _REHEARSAL_SEED_HEX,
        "seed_free_request_sha256": _ROW1_SEED_FREE_SHA256,
        "request_instance_sha256": _row1_request_instance_sha256(),
        "runtime_lock_sha256": _RUNTIME_LOCK_SHA256,
        "phase": "timeout-at-deadline",
        "closed_status": "timeout-censored-at-deadline",
        "failure_code": None,
        "kernel_trace": closed,
    }


def _row1_refusal_or_failure_stable_trace(phase: str, failure_code: str) -> dict:
    trace = _row1_timeout_stable_trace()
    outcome_kind = (
        "preexecution-refusal"
        if phase == "preexecution-refusal-before-deadline"
        else "execution-failure"
    )
    semantic = trace["kernel_trace"]
    semantic.pop("cp62_closed_trace_sha256")
    semantic["outcome_kind"] = outcome_kind
    semantic["failure_code"] = failure_code
    semantic["cp62_closed_trace_sha256"] = hashlib.sha256(
        b"cp62-test28-closed-kernel-outcome-v1\0" + _plain_json_bytes(semantic)
    ).hexdigest()
    trace["phase"] = phase
    trace["closed_status"] = phase
    trace["failure_code"] = failure_code
    return trace


def test_cp63_independent_parser_accepts_exact_closed_timeout_trace() -> None:
    expected = _row1_timeout_stable_trace()
    assert (
        oracle.cp63_independently_validate_stable_trace_bytes(
            _plain_json_bytes(expected)
        )
        == expected
    )


@pytest.mark.parametrize(
    "phase,failure_code",
    tuple(
        ("preexecution-refusal-before-deadline", code)
        for code in (
            "plan_validation_refusal",
            "provider_reference_binding_refusal",
            "resource_preflight_refusal",
            "runtime_binding_refusal",
            "other_preexecution_refusal",
        )
    )
    + tuple(
        ("execution-failure-before-deadline", code)
        for code in (
            "reference_sampling_failure",
            "score_evaluation_failure",
            "quota_certification_failure",
            "float64_normalization_failure",
            "categorical_selection_failure",
            "structural_result_validation_failure",
            "other_execution_failure",
        )
    ),
)
def test_cp63_independent_parser_accepts_every_exact_closed_failure_code(
    phase,
    failure_code,
) -> None:
    expected = _row1_refusal_or_failure_stable_trace(phase, failure_code)
    assert (
        oracle.cp63_independently_validate_stable_trace_bytes(
            _plain_json_bytes(expected)
        )
        == expected
    )


@pytest.mark.parametrize(
    "phase,failure_code",
    (
        ("preexecution-refusal-before-deadline", "reference_sampling_failure"),
        ("execution-failure-before-deadline", "plan_validation_refusal"),
        ("preexecution-refusal-before-deadline", "unknown"),
        ("execution-failure-before-deadline", None),
    ),
)
def test_cp63_independent_parser_rejects_cross_arm_or_open_failure_codes(
    phase,
    failure_code,
) -> None:
    trace = _row1_refusal_or_failure_stable_trace(
        phase,
        "other_preexecution_refusal"
        if phase == "preexecution-refusal-before-deadline"
        else "other_execution_failure",
    )
    trace["failure_code"] = failure_code
    semantic = trace["kernel_trace"]
    semantic["failure_code"] = failure_code
    semantic.pop("cp62_closed_trace_sha256")
    semantic["cp62_closed_trace_sha256"] = hashlib.sha256(
        b"cp62-test28-closed-kernel-outcome-v1\0" + _plain_json_bytes(semantic)
    ).hexdigest()
    with pytest.raises(oracle.CP63IndependentRecomputationError):
        oracle.cp63_independently_validate_stable_trace_bytes(_plain_json_bytes(trace))


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("schema", "cp63-test28-runner-recomputation-rehearsal-v0"),
        ("purpose", "production"),
        ("rehearsal_id", "cp63-other-rehearsal"),
        ("seed_ordinal", 2),
        ("row_ordinal", 2),
        ("logical_request_ordinal", 2),
        ("row_key", "row-01/wrong"),
        ("fixture_id", "T28-M2-Q"),
        ("strategy", "fixed-budget-sir"),
        ("budget", 4),
        ("plan_seed_hex", "0000000000000000"),
        ("seed_free_request_sha256", "0" * 64),
        ("request_instance_sha256", "0" * 64),
        ("runtime_lock_sha256", "0" * 64),
        ("phase", "returned-before-deadline"),
        ("closed_status", "preexecution-refusal-before-deadline"),
        ("failure_code", "plan_validation_refusal"),
    ),
)
def test_cp63_independent_parser_hard_binds_outer_rehearsal_identity(
    field,
    replacement,
) -> None:
    trace = _row1_timeout_stable_trace()
    trace[field] = replacement
    with pytest.raises(oracle.CP63IndependentRecomputationError):
        oracle.cp63_independently_validate_stable_trace_bytes(_plain_json_bytes(trace))


def test_cp63_independent_parser_recomputes_closed_semantic_digest() -> None:
    trace = _row1_timeout_stable_trace()
    trace["kernel_trace"]["runtime_lock_sha256"] = "0" * 64
    with pytest.raises(oracle.CP63IndependentRecomputationError):
        oracle.cp63_independently_validate_stable_trace_bytes(_plain_json_bytes(trace))


def _float64_tag(value: float) -> dict[str, str]:
    return {"$float64_be": struct.pack(">d", value).hex()}


def _fraction_tag(value: Fraction) -> dict[str, list[str]]:
    return {"$fraction": [str(value.numerator), str(value.denominator)]}


def _configuration(events: list[dict]) -> dict:
    body = {"events": events}
    body["cp62_configuration_sha256"] = hashlib.sha256(
        b"cp62-test28-configuration-v1\0" + _plain_json_bytes(body)
    ).hexdigest()
    return body


def test_cp63_source_evaluation_rejects_redigested_bool_cardinality() -> None:
    configuration = ((1, (Fraction(1, 2),)),)
    source_evaluation = _owned_json_leaf(
        b"cp62-test28-source-evaluation-v1",
        {
            "fixture_id": "T28-M1-Q",
            "residual_context_float64_be": [],
            "cardinality": True,
            "count_penalty": _fraction_tag(Fraction(0)),
            "exact_log_weight": _fraction_tag(Fraction(-1, 16)),
            "rounded_exact_log_weight_float64_be": _float64_tag(-1 / 16),
            "direct_binary64_log_weight_float64_be": _float64_tag(-1 / 16),
            "exact_upper_bound_respected": True,
            "represented_restriction_identity_verified": True,
        },
        "cp62_source_evaluation_sha256",
    )
    with pytest.raises(oracle.CP63IndependentRecomputationError):
        oracle._validate_source_evaluation(
            source_evaluation,
            fixture_id="T28-M1-Q",
            configuration=configuration,
            name="bool-cardinality-hostile",
        )


def _selected_trace(
    *,
    row_ordinal: int,
    fixture_id: str,
    strategy: str,
    budget: int,
    configuration: dict,
    selected_index: int,
) -> dict:
    return {
        "seed_ordinal": 1,
        "row_ordinal": row_ordinal,
        "logical_request_ordinal": row_ordinal,
        "row_key": (f"row-{row_ordinal:02d}/{fixture_id}/{strategy}/budget-{budget}"),
        "fixture_id": fixture_id,
        "strategy": strategy,
        "budget": budget,
        "plan_seed_hex": "12a5228200019dae",
        "seed_free_request_sha256": "1" * 64,
        "request_instance_sha256": "2" * 64,
        "runtime_lock_sha256": "3" * 64,
        "closed_status": (
            "returned-rejection-selected-before-deadline"
            if strategy == "bounded-rejection"
            else "returned-sir-selected-before-deadline"
        ),
        "kernel_trace": {
            "selected_index": selected_index,
            "selected_configuration": configuration,
        },
    }


@pytest.mark.parametrize("tamper", ("wrong-digest", "wrong-field", "stale-digest"))
def test_cp63_compact_observation_requires_exact_cp62_configuration_digest(
    monkeypatch,
    tamper,
) -> None:
    configuration = _configuration(
        [
            {
                "event_type": 1,
                "coordinates_float64_be": [_float64_tag(0.5)],
            }
        ]
    )
    if tamper == "wrong-digest":
        configuration["cp62_configuration_sha256"] = "0" * 64
    elif tamper == "wrong-field":
        digest = configuration.pop("cp62_configuration_sha256")
        configuration["cp63_configuration_sha256"] = digest
    else:
        configuration["events"][0]["coordinates_float64_be"] = [_float64_tag(0.25)]
    trace = _selected_trace(
        row_ordinal=1,
        fixture_id="T28-M1-Q",
        strategy="bounded-rejection",
        budget=1,
        configuration=configuration,
        selected_index=0,
    )
    monkeypatch.setattr(
        oracle,
        "cp63_independently_validate_stable_trace_bytes",
        lambda _payload: trace,
    )
    with pytest.raises(oracle.CP63IndependentRecomputationError):
        oracle.cp63_compact_observation(b"hostile-configuration")


def test_cp63_independent_m1_feature_toy_oracle(monkeypatch) -> None:
    configuration = _configuration(
        [
            {
                "event_type": 1,
                "coordinates_float64_be": [_float64_tag(0.5)],
            }
        ]
    )
    trace = _selected_trace(
        row_ordinal=1,
        fixture_id="T28-M1-Q",
        strategy="bounded-rejection",
        budget=1,
        configuration=configuration,
        selected_index=0,
    )
    monkeypatch.setattr(
        oracle,
        "cp63_independently_validate_stable_trace_bytes",
        lambda _payload: trace,
    )
    observation = oracle.cp63_compact_observation(b"toy-m1")
    assert observation.selected is True
    assert observation.first_selected_attempt_one_based == 1
    assert dict(
        zip(
            observation.selected_feature_ids,
            observation.selected_feature_values,
            strict=True,
        )
    ) == {
        "count/eq/0": Fraction(0),
        "count/eq/1": Fraction(1),
        "type/0/occupancy": Fraction(0),
        "type/1/occupancy": Fraction(1),
        "coordinate/1/axis0/odd": Fraction(1, 2),
        "coordinate/1/axis0/even": Fraction(1, 4),
    }


def test_cp63_independent_m2_feature_toy_oracle(monkeypatch) -> None:
    configuration = _configuration(
        [
            {
                "event_type": 0,
                "coordinates_float64_be": [_float64_tag(0.5)],
            },
            {
                "event_type": 1,
                "coordinates_float64_be": [
                    _float64_tag(0.25),
                    _float64_tag(-0.5),
                ],
            },
        ]
    )
    trace = _selected_trace(
        row_ordinal=16,
        fixture_id="T28-M2-Q",
        strategy="fixed-budget-sir",
        budget=512,
        configuration=configuration,
        selected_index=0,
    )
    monkeypatch.setattr(
        oracle,
        "cp63_independently_validate_stable_trace_bytes",
        lambda _payload: trace,
    )
    observation = oracle.cp63_compact_observation(b"toy-m2")
    values = dict(
        zip(
            observation.selected_feature_ids,
            observation.selected_feature_values,
            strict=True,
        )
    )
    assert len(values) == 33
    assert observation.first_selected_attempt_one_based is None
    assert values["count/eq/2"] == 1
    assert values["type/0/occupancy"] == Fraction(1, 2)
    assert values["type/1/occupancy"] == Fraction(1, 2)
    assert values["coordinate/0/axis0/odd"] == Fraction(1, 4)
    assert values["coordinate/1/axis1/odd"] == Fraction(-1, 4)
    assert values["coordinate/1/diag-plus-3-4/odd"] == Fraction(-1, 8)
    assert values["coordinate/1/diag-minus-3-4/even"] == Fraction(121, 800)
    assert values["pair-type/0/1"] == 1


@pytest.mark.parametrize(
    "fixture_id,configuration,expected_count",
    (
        ("T28-M1-Q", ((1, (2.0,)),), 6),
        (
            "T28-M2-Q",
            (
                (1, (-4.0, 0.5)),
                (1, (2.0, -3.0)),
            ),
            33,
        ),
    ),
)
def test_cp63_complete_feature_vector_matches_live_cp58_without_source_import(
    fixture_id,
    configuration,
    expected_count,
) -> None:
    from heterodiff.evaluation import (
        mixed_initializer_test28_bounded_sir_diagnostics as cp58,
    )

    exact_configuration = tuple(
        (
            event_type,
            tuple(Fraction.from_float(value) for value in coordinates),
        )
        for event_type, coordinates in configuration
    )
    actual = oracle._feature_vector(fixture_id, exact_configuration)
    registry = cp58.cp58_feature_registry(fixture_id)
    assert hashlib.sha256(Path(cp58.__file__).read_bytes()).hexdigest() == (
        oracle.cp63_independent_recomputation_bundle().cp58_source_sha256
    )
    assert tuple(feature_id for feature_id, _value in actual) == tuple(
        feature.feature_id for feature in registry.features
    )
    assert tuple(value for _feature_id, value in actual) == (
        cp58.cp58_bounded_feature_vector(fixture_id, configuration)
    )
    assert len(actual) == expected_count
    values = dict(actual)
    if fixture_id == "T28-M1-Q":
        assert values["coordinate/1/axis0/odd"] == 1
        assert values["coordinate/1/axis0/even"] == 1
    else:
        assert values["pair-projection/1/axis0/1/axis1"] == Fraction(3, 4)


def _object_new_clone_and_redigest(record, changes: dict, domain: bytes):
    clone = object.__new__(type(record))
    values = {item.name: getattr(record, item.name) for item in fields(type(record))}
    values.update(changes)
    values["record_sha256"] = "0" * 64
    values["record_sha256"] = hashlib.sha256(
        domain + b"\0" + oracle._canonical_json_bytes(values)
    ).hexdigest()
    for name, value in values.items():
        object.__setattr__(clone, name, value)
    return clone


def _mutate_module_created_and_redigest(record, changes: dict, domain: bytes) -> None:
    values = {item.name: getattr(record, item.name) for item in fields(type(record))}
    values.update(changes)
    values["record_sha256"] = "0" * 64
    values["record_sha256"] = hashlib.sha256(
        domain + b"\0" + oracle._canonical_json_bytes(values)
    ).hexdigest()
    for name, value in values.items():
        object.__setattr__(record, name, value)


def _module_created_record_trio(monkeypatch):
    configuration = _configuration(
        [
            {
                "event_type": 1,
                "coordinates_float64_be": [_float64_tag(0.5)],
            }
        ]
    )
    trace = _selected_trace(
        row_ordinal=1,
        fixture_id="T28-M1-Q",
        strategy="bounded-rejection",
        budget=1,
        configuration=configuration,
        selected_index=0,
    )
    trace["seed_free_request_sha256"] = _ROW1_SEED_FREE_SHA256
    trace["request_instance_sha256"] = _row1_request_instance_sha256()
    trace["runtime_lock_sha256"] = _RUNTIME_LOCK_SHA256
    monkeypatch.setattr(
        oracle,
        "cp63_independently_validate_stable_trace_bytes",
        lambda _payload: trace,
    )
    compact = oracle.cp63_compact_observation(b"compact-record-fixture")
    oracle.cp63_recomputation_canonical_json_bytes(compact)

    payloads = tuple(f"row-{row:02d}".encode("ascii") for row in range(1, 17))
    fake_observations = {}
    for row, payload in enumerate(payloads, 1):
        fixture, strategy, _budget = oracle._ROW_SHAPES[row - 1]
        cell = (
            "timeout-censored-at-deadline"
            if strategy == "bounded-rejection"
            else "timeout-censored-at-deadline"
        )
        observable, _first = oracle._contribution_ordinals(row, cell, None)
        fake_observations[payload] = SimpleNamespace(
            row_ordinal=row,
            logical_request_ordinal=row,
            fixture_id=fixture,
            plan_seed_hex=_REHEARSAL_SEED_HEX,
            stable_trace_sha256=f"{row:064x}",
            record_sha256=f"{row + 16:064x}",
            observable_contribution_ordinal=observable,
            observable_cell_label=cell,
            first_selected_attempt_one_based=None,
            selected_feature_ids=(),
            selected_feature_values=(),
        )
    monkeypatch.setattr(
        oracle,
        "cp63_compact_observation",
        lambda payload: fake_observations[payload],
    )
    receipt = oracle.cp63_recompute_rehearsal(payloads)
    oracle.cp63_recomputation_canonical_json_bytes(receipt)
    reordered = list(payloads)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    with pytest.raises(oracle.CP63IndependentRecomputationError):
        oracle.cp63_recompute_rehearsal(tuple(reordered))
    duplicated = list(payloads)
    duplicated[1] = duplicated[0]
    with pytest.raises(oracle.CP63IndependentRecomputationError):
        oracle.cp63_recompute_rehearsal(tuple(duplicated))
    bundle = oracle.cp63_independent_recomputation_bundle()
    oracle.cp63_recomputation_canonical_json_bytes(bundle)
    return compact, receipt, bundle


def test_cp63_all_public_record_types_reject_object_new_redigested_forgeries(
    monkeypatch,
) -> None:
    compact, receipt, bundle = _module_created_record_trio(monkeypatch)

    for record in (compact, receipt, bundle):
        with pytest.raises(TypeError):
            type(record)()
        with pytest.raises(TypeError):
            record.__reduce_ex__(5)

    for forged in (
        _object_new_clone_and_redigest(
            compact,
            {"selected": False},
            b"cp63-compact-observation-v1",
        ),
        _object_new_clone_and_redigest(
            compact,
            {"observable_contribution_ordinal": True},
            b"cp63-compact-observation-v1",
        ),
        _object_new_clone_and_redigest(
            receipt,
            {"observable_contributions": (0,) * 72},
            b"cp63-rehearsal-recomputation-receipt-v1",
        ),
        _object_new_clone_and_redigest(
            receipt,
            {"missing_count": False},
            b"cp63-rehearsal-recomputation-receipt-v1",
        ),
        _object_new_clone_and_redigest(
            receipt,
            {"row_ordinals": (True,) + tuple(range(2, 17))},
            b"cp63-rehearsal-recomputation-receipt-v1",
        ),
        _object_new_clone_and_redigest(
            bundle,
            {"decision_made": True},
            b"cp63-independent-recomputation-bundle-v1",
        ),
    ):
        with pytest.raises(TypeError, match="was not module-created"):
            oracle.cp63_recomputation_canonical_json_bytes(forged)


def test_cp63_exact_object_new_clones_are_not_module_created(monkeypatch) -> None:
    compact, receipt, bundle = _module_created_record_trio(monkeypatch)
    domains = (
        b"cp63-compact-observation-v1",
        b"cp63-rehearsal-recomputation-receipt-v1",
        b"cp63-independent-recomputation-bundle-v1",
    )
    for record, domain in zip((compact, receipt, bundle), domains, strict=True):
        forged = _object_new_clone_and_redigest(record, {}, domain)
        assert forged.record_sha256 == record.record_sha256
        with pytest.raises(TypeError, match="was not module-created"):
            oracle.cp63_recomputation_canonical_json_bytes(forged)
        with pytest.raises(TypeError, match="was not module-created"):
            oracle.cp63_recomputation_sha256(forged)


def test_cp63_unissued_in_range_compact_feature_forge_is_rejected(
    monkeypatch,
) -> None:
    compact, _receipt, _bundle = _module_created_record_trio(monkeypatch)
    values = list(compact.selected_feature_values)
    assert values
    values[0] = Fraction(1) if values[0] != Fraction(1) else Fraction(0)
    forged = _object_new_clone_and_redigest(
        compact,
        {"selected_feature_values": tuple(values)},
        b"cp63-compact-observation-v1",
    )
    with pytest.raises(TypeError, match="was not module-created"):
        oracle.cp63_recomputation_canonical_json_bytes(forged)


def test_cp63_unissued_distinct_receipt_stable_hash_forge_is_rejected(
    monkeypatch,
) -> None:
    _compact, receipt, _bundle = _module_created_record_trio(monkeypatch)
    hashes = list(receipt.stable_trace_sha256s)
    replacement = hashlib.sha256(b"cp63-hostile-distinct-stable-hash").hexdigest()
    assert replacement not in hashes
    hashes[0] = replacement
    forged = _object_new_clone_and_redigest(
        receipt,
        {"stable_trace_sha256s": tuple(hashes)},
        b"cp63-rehearsal-recomputation-receipt-v1",
    )
    with pytest.raises(TypeError, match="was not module-created"):
        oracle.cp63_recomputation_canonical_json_bytes(forged)


def test_cp63_registered_compact_mutation_cannot_replace_issued_snapshot(
    monkeypatch,
) -> None:
    compact, _receipt, _bundle = _module_created_record_trio(monkeypatch)
    values = list(compact.selected_feature_values)
    assert values
    values[0] = Fraction(1) if values[0] != Fraction(1) else Fraction(0)
    _mutate_module_created_and_redigest(
        compact,
        {"selected_feature_values": tuple(values)},
        b"cp63-compact-observation-v1",
    )
    with pytest.raises(ValueError, match="issued record was mutated"):
        oracle.cp63_recomputation_canonical_json_bytes(compact)
    with pytest.raises(ValueError, match="issued record was mutated"):
        oracle.cp63_recomputation_sha256(compact)


def test_cp63_registered_receipt_mutation_cannot_replace_issued_snapshot(
    monkeypatch,
) -> None:
    _compact, receipt, _bundle = _module_created_record_trio(monkeypatch)
    hashes = list(receipt.stable_trace_sha256s)
    replacement = hashlib.sha256(b"cp63-hostile-issued-stable-hash").hexdigest()
    assert replacement not in hashes
    hashes[0] = replacement
    _mutate_module_created_and_redigest(
        receipt,
        {"stable_trace_sha256s": tuple(hashes)},
        b"cp63-rehearsal-recomputation-receipt-v1",
    )
    with pytest.raises(ValueError, match="issued record was mutated"):
        oracle.cp63_recomputation_canonical_json_bytes(receipt)
    with pytest.raises(ValueError, match="issued record was mutated"):
        oracle.cp63_recomputation_sha256(receipt)


def test_cp63_issued_snapshot_registry_is_thread_safe_and_weak(monkeypatch) -> None:
    compact, _receipt, _bundle = _module_created_record_trio(monkeypatch)
    expected_payload = oracle.cp63_recomputation_canonical_json_bytes(compact)
    expected_sha256 = oracle.cp63_recomputation_sha256(compact)
    barrier = threading.Barrier(9)
    failures = []

    def worker() -> None:
        try:
            barrier.wait(timeout=5)
            for _ in range(50):
                assert (
                    oracle.cp63_recomputation_canonical_json_bytes(compact)
                    == expected_payload
                )
                assert oracle.cp63_recomputation_sha256(compact) == expected_sha256
        except BaseException as error:
            failures.append(error)

    threads = tuple(threading.Thread(target=worker) for _ in range(8))
    for thread in threads:
        thread.start()
    barrier.wait(timeout=5)
    for thread in threads:
        thread.join(timeout=10)
        assert not thread.is_alive()
    assert failures == []

    ephemeral = oracle.cp63_independent_recomputation_bundle()
    ephemeral_id = id(ephemeral)
    ephemeral_ref = weakref.ref(ephemeral)
    with oracle._ISSUED_RECORD_LOCK:
        assert ephemeral in oracle._ISSUED_RECORD_SNAPSHOTS
    del ephemeral
    gc.collect()
    assert ephemeral_ref() is None
    with oracle._ISSUED_RECORD_LOCK:
        assert all(
            id(record) != ephemeral_id for record in oracle._ISSUED_RECORD_SNAPSHOTS
        )


def test_cp63_independent_records_are_sealed_and_nonpickleable() -> None:
    bundle = oracle.cp63_independent_recomputation_bundle()
    for record in (bundle,):
        try:
            type(record)()
        except TypeError:
            pass
        else:
            raise AssertionError("CP63 independent records became constructible")
        try:
            record.__reduce_ex__(5)
        except TypeError:
            pass
        else:
            raise AssertionError("CP63 independent records became pickleable")


def test_cp63_independent_builder_is_deterministic() -> None:
    first = oracle.cp63_independent_recomputation_bundle()
    second = oracle.cp63_independent_recomputation_bundle()
    assert oracle.cp63_recomputation_canonical_json_bytes(
        first
    ) == oracle.cp63_recomputation_canonical_json_bytes(second)
    assert oracle.cp63_recomputation_sha256(first) == oracle.cp63_recomputation_sha256(
        second
    )
