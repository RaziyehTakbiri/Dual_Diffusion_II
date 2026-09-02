"""Independent hostile tests for the CP57 stress and refusal oracles."""

from __future__ import annotations

import ast
import builtins
import copy
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
import hashlib
from itertools import product
import math
import os
from pathlib import Path
import pickle
import subprocess
import sys
from unittest import mock

import numpy as np
import pytest

from heterodiff.evaluation import exact_rational_quadratic_initial_tilt as exact_source
from heterodiff.evaluation import mixed_initializer_test28_oracle as cp50_oracle
from heterodiff.evaluation import (
    mixed_initializer_test28_stress_refusal_oracle as oracle,
)
from heterodiff.processes import certified_initial_score_provider_v1 as score_provider
from heterodiff.processes import (
    plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 as kernel_v2,
)
from heterodiff.theory import configuration_reference as reference_module
from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
    TransformedEvent,
)


_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)
_ADAPTER_ROLE = hashlib.sha256(b"cp57-hostile-adapter-v1").hexdigest()
_KERNEL_ROLE = hashlib.sha256(b"cp57-hostile-kernel-v1").hexdigest()
_RNG_ROLES = ("proposal", "rejection-decision", "sir-resampling")
_SUPPORT = ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2))
_BASE = (
    Fraction(2, 5),
    Fraction(4, 25),
    Fraction(6, 25),
    Fraction(4, 125),
    Fraction(12, 125),
    Fraction(9, 125),
)
_FACTORS = (_ONE, _ONE, _ONE, _ONE, _ONE, Fraction(1024, 1))
_TARGET_NUMERATORS = (50, 20, 30, 4, 12, 9216)
_TARGET_DENOMINATOR = 9332
_CLOUD = (0, 1, 2, 3, 4, 5, 0, 1)

_EXPECTED_CASE_SPECS = (
    (
        "T28-INVALID-NEGATIVE-FACTOR",
        "NEGATIVE_FACTOR",
        "negative-factor",
        "weights=(0x1.0000000000000p+0,-0x1.0000000000000p+0)",
        "independent-ess-weight-preflight",
        ("fixed-budget-sir",),
        "builtins.ValueError",
        "weights[1] must be strictly positive",
        "oracle-model-only",
    ),
    (
        "T28-INVALID-NAN-FACTOR",
        "NAN_FACTOR",
        "nan-factor",
        "weights=(0x1.0000000000000p+0,nan)",
        "independent-ess-weight-preflight",
        ("fixed-budget-sir",),
        "builtins.ValueError",
        "weights[1] must not be NaN",
        "oracle-model-only",
    ),
    (
        "T28-INVALID-POSITIVE-INFINITE-FACTOR",
        "POSITIVE_INFINITE_FACTOR",
        "positive-infinite-factor",
        "weights=(0x1.0000000000000p+0,+inf)",
        "independent-ess-weight-preflight",
        ("fixed-budget-sir",),
        "builtins.ValueError",
        "weights[1] must be finite",
        "oracle-model-only",
    ),
    (
        "T28-INVALID-FALSE-ENVELOPE",
        "FALSE_ENVELOPE",
        "false-envelope",
        "fixture=T28-A0-H;factors=(1/1,2/1,1/2,3/1,3/2,1/4);"
        "declared_envelope=2/1;declared_acceptance=549/1000",
        "independent-atomic-envelope-preflight",
        ("bounded-rejection",),
        "builtins.ValueError",
        "A0 rejection envelope is invalid",
        "oracle-model-only",
    ),
    (
        "T28-INVALID-ALL-ZERO-SIR-WEIGHTS",
        "ALL_ZERO_SIR_WEIGHTS",
        "zero-categorical-mass",
        "weights=(0x0.0p+0,0x0.0p+0)",
        "independent-ess-weight-preflight",
        ("fixed-budget-sir",),
        "builtins.ValueError",
        "weights[0] must be strictly positive",
        "oracle-model-only",
    ),
    (
        "T28-INVALID-ZERO-CATEGORICAL-BIN",
        "ZERO_CATEGORICAL_BIN",
        "zero-categorical-mass",
        "normalized_weights=(0x1.0000000000000p+0,0x0.0p+0);raw_word=0",
        "kernel-v2-categorical-transform-preflight",
        ("fixed-budget-sir",),
        "builtins.ValueError",
        "normalized_weights must be strictly positive",
        "direct-helper-preflight",
    ),
    (
        "T28-INVALID-NONNORMALIZED-CATEGORICAL-MASS",
        "NONNORMALIZED_CATEGORICAL_MASS",
        "invalid-categorical-mass",
        "normalized_weights=(0x1.3333333333333p-1," "0x1.3333333333333p-1);raw_word=0",
        "kernel-v2-categorical-transform-preflight",
        ("fixed-budget-sir",),
        "builtins.ValueError",
        "normalized_weights must sum to one",
        "direct-helper-preflight",
    ),
    (
        "T28-INVALID-COUNT-CATEGORICAL-RESOLUTION",
        "COUNT_CATEGORICAL_RESOLUTION",
        "invalid-categorical-mass",
        "type_dimensions=(0);type_weights=(0x1.0000000000000p+0);"
        "activity=0x1.0000000000000p-41;total_cap=1",
        "kernel-v2-reference-sampling-resolution-preflight",
        ("bounded-rejection", "fixed-budget-sir"),
        "heterodiff.theory.configuration_reference."
        "UnsupportedReferenceSamplingError",
        "count categorical law fails the pre-RNG sampling-resolution preflight",
        "production-preflight",
    ),
    (
        "T28-INVALID-TYPE-CATEGORICAL-RESOLUTION",
        "TYPE_CATEGORICAL_RESOLUTION",
        "invalid-categorical-mass",
        "type_dimensions=(0,0);type_weights=(0x1.0000000000000p-41,"
        "0x1.ffffffffff000p-1);activity=0x1.0000000000000p+0;total_cap=1",
        "kernel-v2-reference-sampling-resolution-preflight",
        ("bounded-rejection", "fixed-budget-sir"),
        "heterodiff.theory.configuration_reference."
        "UnsupportedReferenceSamplingError",
        "type categorical law fails the pre-RNG sampling-resolution preflight",
        "production-preflight",
    ),
    (
        "T28-INVALID-WRONG-EVENT-DIMENSION",
        "WRONG_EVENT_DIMENSION",
        "wrong-dimension",
        "fixture=T28-M1-Q;event_type=1;coordinates=()",
        "certified-score-provider-v1-configuration-preflight",
        ("bounded-rejection", "fixed-budget-sir"),
        "builtins.ValueError",
        "event coordinates have the wrong dimension",
        "provider-preflight-only",
    ),
    (
        "T28-INVALID-NONCANONICAL-NEGATIVE-ZERO-STATE",
        "NONCANONICAL_STATE",
        "noncanonical-state",
        "fixture=T28-M1-Q;event_type=1;coordinates=(-0x0.0p+0)",
        "certified-score-provider-v1-configuration-preflight",
        ("bounded-rejection", "fixed-budget-sir"),
        "builtins.ValueError",
        "event coordinates must use canonical positive zero",
        "provider-preflight-only",
    ),
    (
        "T28-INVALID-OCCURRENCE-WORK-LIMIT",
        "OCCURRENCE_WORK_LIMIT",
        "resource-limit",
        "type_dimensions=(0);type_weights=(0x1.0000000000000p+0);"
        "activity=0x1.0000000000000p+0;total_cap=123;budget=4096;"
        "worst_occurrences=503808;occurrence_limit=500000",
        "kernel-v2-stochastic-resource-preflight",
        ("bounded-rejection", "fixed-budget-sir"),
        "builtins.ValueError",
        "planned stochastic work exceeds reference resource limits",
        "production-preflight",
    ),
    (
        "T28-INVALID-COORDINATE-WORK-LIMIT",
        "COORDINATE_WORK_LIMIT",
        "resource-limit",
        "type_dimensions=(1000);type_weights=(0x1.0000000000000p+0);"
        "activity=0x1.0000000000000p+0;total_cap=1;budget=4096;"
        "worst_coordinates=4096000;coordinate_limit=4000000",
        "kernel-v2-stochastic-resource-preflight",
        ("bounded-rejection", "fixed-budget-sir"),
        "builtins.ValueError",
        "planned stochastic work exceeds reference resource limits",
        "production-preflight",
    ),
    (
        "T28-INVALID-FINITE-ATOMIC-SUPPORT-LIMIT",
        "FINITE_ATOMIC_SUPPORT_LIMIT",
        "resource-limit",
        "type_dimensions=(0,0);type_weights=(0x1.0000000000000p-1,"
        "0x1.0000000000000p-1);activity=0x1.0000000000000p+0;"
        "total_cap=22;support_states=276;support_limit=256",
        "kernel-v2-finite-atomic-oracle-resource-preflight",
        ("finite-atomic-enumeration",),
        "builtins.ValueError",
        "counting space would have 276 states, exceeding the finite oracle limit of 256",
        "production-preflight",
    ),
)


class _EqualityBomb:
    def __eq__(self, other):
        del other
        raise AssertionError("hostile equality was touched")

    def __ne__(self, other):
        del other
        raise AssertionError("hostile inequality was touched")


def _forge(instance, **changes):
    forged = object.__new__(type(instance))
    for name in instance.__annotations__:
        object.__setattr__(
            forged,
            name,
            changes[name] if name in changes else getattr(instance, name),
        )
    return forged


def _redigest(kind, instance):
    object.__setattr__(instance, "record_sha256", oracle._digest(kind, instance))
    return instance


def _immutable_float64(values):
    return np.frombuffer(
        np.asarray(values, dtype=np.float64).tobytes(), dtype=np.float64
    )


def _m1_provider():
    source = exact_source.build_t28_m1_q_exact_score_provider()
    return score_provider.adapt_exact_rational_quadratic_initial_tilt_score_provider_v1(
        source,
        adapter_role_sha256=_ADAPTER_ROLE,
    )


def _state_sha256(state):
    return hashlib.sha256(pickle.dumps(state, protocol=5)).hexdigest()


def _owned_rng_state_tuple(rngs):
    return tuple(
        (role, _state_sha256(copy.deepcopy(rng.bit_generator.state)))
        for role, rng in zip(_RNG_ROLES, rngs)
    )


def _negative_zero_event():
    event = object.__new__(TransformedEvent)
    object.__setattr__(event, "event_type", 1)
    object.__setattr__(event, "coordinates", (-0.0,))
    return event


def _invoke_live_invalid_case(case_id, provider):
    if case_id == "T28-INVALID-NEGATIVE-FACTOR":
        return cp50_oracle.ess_summary((1.0, -1.0))
    if case_id == "T28-INVALID-NAN-FACTOR":
        return cp50_oracle.ess_summary((1.0, float("nan")))
    if case_id == "T28-INVALID-POSITIVE-INFINITE-FACTOR":
        return cp50_oracle.ess_summary((1.0, float("inf")))
    if case_id == "T28-INVALID-FALSE-ENVELOPE":
        return replace(
            cp50_oracle.atomic_a0_fixture(),
            rejection_envelope=Fraction(2, 1),
            rejection_acceptance_probability=Fraction(549, 1000),
        )
    if case_id == "T28-INVALID-ALL-ZERO-SIR-WEIGHTS":
        return cp50_oracle.ess_summary((0.0, 0.0))
    if case_id == "T28-INVALID-ZERO-CATEGORICAL-BIN":
        return kernel_v2.select_mixed_support_sir_index_v2(
            _immutable_float64((1.0, 0.0)), 0
        )
    if case_id == "T28-INVALID-NONNORMALIZED-CATEGORICAL-MASS":
        value = float.fromhex("0x1.3333333333333p-1")
        return kernel_v2.select_mixed_support_sir_index_v2(
            _immutable_float64((value, value)), 0
        )
    if case_id == "T28-INVALID-COUNT-CATEGORICAL-RESOLUTION":
        reference = CappedPoissonConfigurationReference(
            {0: 0},
            {0: 1.0},
            activity=float.fromhex("0x1.0000000000000p-41"),
            total_cap=1,
        )
        return kernel_v2._preflight_resources(
            reference, strategy="fixed-budget-sir", budget=1
        )
    if case_id == "T28-INVALID-TYPE-CATEGORICAL-RESOLUTION":
        reference = CappedPoissonConfigurationReference(
            {0: 0, 1: 0},
            {
                0: float.fromhex("0x1.0000000000000p-41"),
                1: float.fromhex("0x1.ffffffffff000p-1"),
            },
            activity=1.0,
            total_cap=1,
        )
        return kernel_v2._preflight_resources(
            reference, strategy="fixed-budget-sir", budget=1
        )
    if case_id == "T28-INVALID-WRONG-EVENT-DIMENSION":
        return provider.evaluate((TransformedEvent(1, ()),), residual_context=())
    if case_id == "T28-INVALID-NONCANONICAL-NEGATIVE-ZERO-STATE":
        return provider.evaluate((_negative_zero_event(),), residual_context=())
    if case_id == "T28-INVALID-OCCURRENCE-WORK-LIMIT":
        reference = CappedPoissonConfigurationReference(
            {0: 0}, {0: 1.0}, activity=1.0, total_cap=123
        )
        return kernel_v2._preflight_resources(
            reference, strategy="fixed-budget-sir", budget=4096
        )
    if case_id == "T28-INVALID-COORDINATE-WORK-LIMIT":
        reference = CappedPoissonConfigurationReference(
            {0: 1000}, {0: 1.0}, activity=1.0, total_cap=1
        )
        return kernel_v2._preflight_resources(
            reference, strategy="fixed-budget-sir", budget=4096
        )
    if case_id == "T28-INVALID-FINITE-ATOMIC-SUPPORT-LIMIT":
        reference = CappedPoissonConfigurationReference(
            {0: 0, 1: 0}, {0: 0.5, 1: 0.5}, activity=1.0, total_cap=22
        )
        return kernel_v2._preflight_resources(
            reference, strategy="finite-atomic-enumeration", budget=0
        )
    raise AssertionError("test does not implement frozen case " + case_id)


@pytest.fixture(scope="module")
def aess():
    return oracle.t28_aess_low_ess_oracle_v1()


@pytest.fixture(scope="module")
def refusal_table():
    return oracle.t28_invalid_refusal_table_v1()


def test_import_is_stdlib_only_and_has_no_execution_side_effect() -> None:
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
import builtins
import sys
real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == "numpy" or name.startswith("numpy."):
        raise AssertionError("NumPy crossed the CP57 oracle import boundary")
    if name == "scipy" or name.startswith("scipy."):
        raise AssertionError("SciPy crossed the CP57 oracle import boundary")
    if name == "torch" or name.startswith("torch."):
        raise AssertionError("torch crossed the CP57 oracle import boundary")
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
import heterodiff.evaluation.mixed_initializer_test28_stress_refusal_oracle
assert "numpy" not in sys.modules
assert "scipy" not in sys.modules
assert "torch" not in sys.modules
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = source_root
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_source_imports_only_the_declared_stdlib_surface() -> None:
    tree = ast.parse(Path(oracle.__file__).read_text(encoding="utf-8"))
    roots = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".")[0])
    assert roots <= {
        "__future__",
        "dataclasses",
        "fractions",
        "hashlib",
        "json",
        "math",
        "typing",
    }
    all_import_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not ({"numpy", "scipy", "torch"} & all_import_roots)


def test_aess_base_is_independently_reconstructed_by_factorials(aess) -> None:
    support = tuple(
        sorted(
            (counts for counts in product(range(3), repeat=2) if sum(counts) <= 2),
            key=lambda counts: (sum(counts), tuple(-value for value in counts)),
        )
    )
    weights = (Fraction(2, 5), Fraction(3, 5))
    raw = []
    for counts in support:
        mass = _ONE
        for weight, count in zip(weights, counts):
            mass *= weight**count / math.factorial(count)
        raw.append(mass)
    raw_normalizer = sum(raw, _ZERO)
    independently_derived = tuple(value / raw_normalizer for value in raw)

    assert support == _SUPPORT == aess.count_vectors
    assert raw_normalizer == Fraction(5, 2)
    assert independently_derived == _BASE == aess.base_probabilities
    assert sum(independently_derived, _ZERO) == _ONE


def test_aess_exact_target_is_derived_without_consuming_serialized_target(aess) -> None:
    masses = tuple(base * factor for base, factor in zip(_BASE, _FACTORS))
    normalizer = sum(masses, _ZERO)
    target = tuple(value / normalizer for value in masses)

    assert aess.multiplicative_factors == _FACTORS
    assert masses == (
        Fraction(2, 5),
        Fraction(4, 25),
        Fraction(6, 25),
        Fraction(4, 125),
        Fraction(12, 125),
        Fraction(9216, 125),
    )
    assert aess.unnormalized_target_masses == masses
    assert normalizer == aess.target_normalizer == Fraction(9332, 125)
    assert target == aess.target_probabilities
    assert tuple(value * _TARGET_DENOMINATOR for value in target) == tuple(
        Fraction(value, 1) for value in _TARGET_NUMERATORS
    )
    assert sum(target, _ZERO) == _ONE
    assert aess.heavy_state_index == 5
    assert aess.heavy_state_label == "bb"
    assert target[5] == Fraction(2304, 2333) > Fraction(49, 50)


def test_aess_cloud_ess_and_strict_warning_are_independently_derived(aess) -> None:
    diagnostic = aess.diagnostic
    raw_weights = tuple(_FACTORS[index] for index in _CLOUD)
    weight_sum = sum(raw_weights, _ZERO)
    squared_sum = sum((value * value for value in raw_weights), _ZERO)
    normalized = tuple(value / weight_sum for value in raw_weights)
    ess = weight_sum * weight_sum / squared_sum
    ess_fraction = ess / len(raw_weights)

    assert diagnostic.cloud_state_indices == _CLOUD
    assert raw_weights == (_ONE,) * 5 + (Fraction(1024),) + (_ONE,) * 2
    assert diagnostic.unnormalized_weights == raw_weights
    assert diagnostic.weight_sum == weight_sum == Fraction(1031, 1)
    assert diagnostic.squared_weight_sum == squared_sum == Fraction(1048583, 1)
    assert diagnostic.normalized_weights == normalized
    assert ess == diagnostic.effective_sample_size == Fraction(1062961, 1048583)
    assert (
        ess_fraction
        == diagnostic.effective_sample_size_fraction
        == Fraction(1062961, 8388664)
    )
    assert diagnostic.ess_warning_fraction == Fraction(1, 4)
    assert diagnostic.ess_warning_threshold == Fraction(2, 1)
    assert ess < diagnostic.ess_warning_threshold
    assert diagnostic.expected_ess_warning is True
    assert diagnostic.ess_warning_comparator == (
        "effective_sample_size < ess_warning_fraction * particle_count"
    )


def test_aess_warning_contract_is_report_only_and_nonadaptive(aess) -> None:
    diagnostic = aess.diagnostic
    assert diagnostic.warning_policy_is_report_only is True
    assert diagnostic.expected_reported_particle_count == 8
    assert diagnostic.expected_warning_triggered_extra_particles == 0
    assert diagnostic.expected_warning_triggered_extra_draws == 0
    assert diagnostic.expected_warning_triggered_fallback is False
    assert diagnostic.expected_warning_triggered_cloud_reuse is False
    assert diagnostic.precommitted_strategy == "fixed-budget-sir"
    assert diagnostic.expected_strategy_after_warning == "fixed-budget-sir"
    assert diagnostic.expected_resampling_draw_count == 1
    assert aess.exact_expected_ess_warning_decision is True
    assert aess.report_only_policy_bound is True
    assert aess.production_behavior_observed is False


def test_generic_kernel_low_ess_trace_has_no_adaptive_work_and_is_not_aess(
    aess,
) -> None:
    provider = _m1_provider()
    plan = kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy="fixed-budget-sir",
        residual_context=(),
        initializer_role_sha256=_KERNEL_ROLE,
        seed=57,
        budget=8,
        ess_warning_fraction=0.25,
    )
    owner = kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        provider, plan=plan
    )
    low_score_event = TransformedEvent(1, (8.0,))
    configurations = ((),) + ((low_score_event,),) * 7
    calls = {"sample": 0, "evaluate": 0}
    reference_type = type(provider.reference)
    provider_type = type(provider)
    original_evaluate = provider_type.evaluate

    def deterministic_sample(self, rng):
        del self, rng
        index = calls["sample"]
        calls["sample"] += 1
        return configurations[index]

    def counted_evaluate(self, configuration, *, residual_context):
        calls["evaluate"] += 1
        return original_evaluate(self, configuration, residual_context=residual_context)

    with mock.patch.object(
        reference_type, "sample_configuration", new=deterministic_sample
    ), mock.patch.object(
        provider_type, "evaluate", new=counted_evaluate
    ), mock.patch.object(
        type(owner),
        "_execute_rejection",
        side_effect=AssertionError("ESS warning triggered rejection fallback"),
    ), mock.patch.object(
        type(owner),
        "_execute_enumeration",
        side_effect=AssertionError("ESS warning triggered enumeration fallback"),
    ):
        result = owner.execute()

    expected_small = math.exp(-16.0)
    expected_total = math.fsum((1.0,) + (expected_small,) * 7)
    expected_weights = (1.0 / expected_total,) + (expected_small / expected_total,) * 7
    expected_ess = 1.0 / math.fsum(value * value for value in expected_weights)
    replay_rng = np.random.Generator(
        np.random.Philox(owner.certificate.sir_resampling_seed)
    )
    expected_before = kernel_v2._rng_state_sha256(replay_rng.bit_generator.state)
    expected_word = int(replay_rng.bit_generator.random_raw())
    expected_after = kernel_v2._rng_state_sha256(replay_rng.bit_generator.state)

    assert calls == {"sample": 8, "evaluate": 8}
    assert len(result.particles) == plan.budget == 8
    assert tuple(float(value) for value in result.normalized_weights) == (
        expected_weights
    )
    assert result.effective_sample_size.hex() == expected_ess.hex()
    assert result.ess_warning is True
    assert result.resampling_word == expected_word
    assert result.resampling_stream_initial_state_sha256 == expected_before
    assert result.resampling_stream_final_state_sha256 == expected_after
    assert plan.adaptive_fallback_permitted is False
    assert aess.initializer_kernel_integrated is False
    assert aess.diagnostic_cloud_sampled is False
    assert aess.multiplicative_factors != tuple(
        Fraction.from_float(value) for value in expected_weights[:6]
    )


def test_invalid_table_exactly_matches_the_independent_frozen_matrix(
    refusal_table,
) -> None:
    actual = tuple(
        (
            case.case_id,
            case.refusal_code,
            case.category,
            case.malformed_payload_encoding,
            case.validation_boundary,
            case.applicable_strategies,
            case.expected_exception_qualname,
            case.expected_exception_message,
            case.expectation_scope,
        )
        for case in refusal_table.cases
    )
    assert refusal_table.required_case_count == 14
    assert actual == _EXPECTED_CASE_SPECS
    assert len({case.case_id for case in refusal_table.cases}) == 14
    assert set(refusal_table.category_registry) == {
        case.category for case in refusal_table.cases
    }


def test_invalid_table_scopes_do_not_promote_direct_or_oracle_rows(
    refusal_table,
) -> None:
    by_scope = {}
    for case in refusal_table.cases:
        by_scope.setdefault(case.expectation_scope, set()).add(case.case_id)
        assert case.production_boundary_verified_by_this_record is False
        assert case.refusal_precedes_any_owned_rng_factory_call is True
        assert case.expected_owned_rng_roles_not_constructed == _RNG_ROLES
        assert case.expected_rng_factory_call_count == 0
        assert (
            case.expected_externally_supplied_sentinel_rng_state_byte_identity is True
        )
        assert case.expected_result_artifact_created is False
    assert by_scope["production-preflight"] == {
        "T28-INVALID-COUNT-CATEGORICAL-RESOLUTION",
        "T28-INVALID-TYPE-CATEGORICAL-RESOLUTION",
        "T28-INVALID-OCCURRENCE-WORK-LIMIT",
        "T28-INVALID-COORDINATE-WORK-LIMIT",
        "T28-INVALID-FINITE-ATOMIC-SUPPORT-LIMIT",
    }
    assert by_scope["direct-helper-preflight"] == {
        "T28-INVALID-ZERO-CATEGORICAL-BIN",
        "T28-INVALID-NONNORMALIZED-CATEGORICAL-MASS",
    }
    assert by_scope["provider-preflight-only"] == {
        "T28-INVALID-WRONG-EVENT-DIMENSION",
        "T28-INVALID-NONCANONICAL-NEGATIVE-ZERO-STATE",
    }
    assert len(by_scope["oracle-model-only"]) == 5
    assert refusal_table.production_boundaries_verified_by_table is False


@pytest.mark.parametrize("case_index", range(14))
def test_every_invalid_case_executes_before_owned_rng_and_preserves_external_sentinel(
    refusal_table, case_index
) -> None:
    case = refusal_table.cases[case_index]
    provider = _m1_provider()
    source_type = type(provider.backend_adapter.source)
    sentinel_rngs = tuple(
        np.random.Generator(np.random.Philox(seed)) for seed in (5701, 5702, 5703)
    )
    before = _owned_rng_state_tuple(sentinel_rngs)
    expected_type = (
        reference_module.UnsupportedReferenceSamplingError
        if case.expected_exception_qualname.endswith(
            ".UnsupportedReferenceSamplingError"
        )
        else ValueError
    )

    with mock.patch.object(
        kernel_v2,
        "_new_philox",
        side_effect=AssertionError("invalid input constructed an RNG"),
    ) as rng_factory, mock.patch.object(
        kernel_v2,
        "_runtime_sha256",
        side_effect=AssertionError("invalid input reached runtime probing"),
    ) as runtime_probe, mock.patch.object(
        CappedPoissonConfigurationReference,
        "sample_configuration",
        side_effect=AssertionError("invalid input reached reference sampling"),
    ) as sampler, mock.patch.object(
        source_type,
        "evaluate",
        side_effect=AssertionError("invalid provider input reached score dispatch"),
    ) as source_dispatch:
        with pytest.raises(expected_type) as caught:
            _invoke_live_invalid_case(case.case_id, provider)

    after = _owned_rng_state_tuple(sentinel_rngs)
    assert type(caught.value) is expected_type
    assert str(caught.value) == case.expected_exception_message
    assert before == after
    assert rng_factory.call_count == 0
    assert runtime_probe.call_count == 0
    assert sampler.call_count == 0
    assert source_dispatch.call_count == 0

    observation = oracle.verify_t28_invalid_refusal_observation_v1(
        refusal_table,
        case_id=case.case_id,
        observed_exception=caught.value,
        validation_boundary=case.validation_boundary,
        externally_supplied_sentinel_rng_state_sha256_before=before,
        externally_supplied_sentinel_rng_state_sha256_after=after,
        rng_factory_call_count=0,
        result_artifact_created=False,
    )
    assert observation.supplied_exception_matches_frozen_expectation is True
    assert (
        observation.externally_supplied_sentinel_rng_state_digests_byte_identical
        is True
    )
    assert observation.supplied_observation_matches_frozen_expectation is True
    assert observation.case_expectation_is_production_preflight is (
        case.expectation_scope == "production-preflight"
    )
    assert observation.exact_exception_class_identity_checked is True
    assert observation.builtin_value_error_identity_checked is (
        expected_type is ValueError
    )
    assert observation.production_unsupported_reference_error_identity_checked is (
        expected_type is reference_module.UnsupportedReferenceSamplingError
    )
    assert observation.boundary_invocation_provenance_verified is False
    assert observation.sentinel_rng_state_digest_provenance_verified is False
    assert observation.production_runner_evidence is False


@pytest.mark.parametrize(
    "sentinel,message",
    (
        (
            "count",
            "count categorical law fails the pre-RNG sampling-resolution preflight",
        ),
        (
            "type",
            "type categorical law fails the pre-RNG sampling-resolution preflight",
        ),
    ),
)
def test_certification_refuses_unavailable_cdf_sentinel_before_runtime_or_rng(
    sentinel, message
) -> None:
    provider = _m1_provider()
    plan = kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy="fixed-budget-sir",
        residual_context=(),
        initializer_role_sha256=_KERNEL_ROLE,
        seed=5704,
        budget=1,
    )
    reference = provider.reference
    attribute = "_count_sampling_cdf" if sentinel == "count" else "_type_sampling_cdf"
    original = getattr(reference, attribute)
    object.__setattr__(reference, attribute, None)
    owned_rng = np.random.Generator(np.random.Philox(5705))
    before = _state_sha256(copy.deepcopy(owned_rng.bit_generator.state))
    try:
        with mock.patch.object(
            kernel_v2,
            "_runtime_sha256",
            side_effect=AssertionError("runtime probed before categorical preflight"),
        ) as runtime_probe, mock.patch.object(
            kernel_v2,
            "_new_philox",
            side_effect=AssertionError("RNG constructed before categorical preflight"),
        ) as rng_factory, mock.patch.object(
            type(reference),
            "sample_configuration",
            side_effect=AssertionError("sampled before categorical preflight"),
        ) as sampler:
            with pytest.raises(
                reference_module.UnsupportedReferenceSamplingError,
                match=message,
            ):
                kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
                    provider, plan=plan
                )
        assert runtime_probe.call_count == 0
        assert rng_factory.call_count == 0
        assert sampler.call_count == 0
    finally:
        object.__setattr__(reference, attribute, original)
    after = _state_sha256(copy.deepcopy(owned_rng.bit_generator.state))
    assert before == after


def test_certification_rejects_coordinated_self_consistent_count_pmf_cdf_tamper() -> None:
    provider = _m1_provider()
    plan = kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy="fixed-budget-sir",
        residual_context=(),
        initializer_role_sha256=_KERNEL_ROLE,
        seed=5707,
        budget=1,
    )
    reference = provider.reference
    original_pmf = reference._count_probability_vector
    original_cdf = reference._count_sampling_cdf
    hostile_pmf = _immutable_float64((0.75, 0.25))
    hostile_cdf = _immutable_float64((0.75, 1.0))
    assert reference.total_cap == 1
    assert reference.count_probabilities.tobytes() != hostile_pmf.tobytes()
    object.__setattr__(reference, "_count_probability_vector", hostile_pmf)
    object.__setattr__(reference, "_count_sampling_cdf", hostile_cdf)
    try:
        with mock.patch.object(
            kernel_v2,
            "_runtime_sha256",
            side_effect=AssertionError("coordinated tamper reached runtime probing"),
        ) as runtime_probe, mock.patch.object(
            kernel_v2,
            "_new_philox",
            side_effect=AssertionError("coordinated tamper constructed an RNG"),
        ) as rng_factory, mock.patch.object(
            type(reference),
            "sample_configuration",
            side_effect=AssertionError("coordinated tamper reached sampling"),
        ) as sampler:
            with pytest.raises(
                reference_module.UnsupportedReferenceSamplingError,
                match=(
                    "count categorical law fails the pre-RNG "
                    "sampling-resolution preflight"
                ),
            ):
                kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
                    provider, plan=plan
                )
        assert runtime_probe.call_count == 0
        assert rng_factory.call_count == 0
        assert sampler.call_count == 0
    finally:
        object.__setattr__(reference, "_count_probability_vector", original_pmf)
        object.__setattr__(reference, "_count_sampling_cdf", original_cdf)


def test_valid_non_idempotent_retained_type_weights_pass_stochastic_preflight() -> None:
    supplied_weights = {
        0: 0.9071400004548366,
        1: 0.09285999954516357,
    }
    reference = CappedPoissonConfigurationReference(
        {0: 0, 1: 0}, supplied_weights, activity=1.0, total_cap=1
    )
    rebuilt_from_retained_weights = CappedPoissonConfigurationReference(
        dict(reference.type_dimensions),
        dict(reference.type_weights),
        activity=reference.activity,
        total_cap=reference.total_cap,
    )

    assert tuple(value.hex() for value in reference._type_weight_vector) == (
        "0x1.d074a775b1a31p-1",
        "0x1.7c5ac45272e70p-4",
    )
    assert (
        reference._type_weight_vector.tobytes()
        != rebuilt_from_retained_weights._type_weight_vector.tobytes()
    )
    assert (
        reference._type_sampling_cdf.tobytes()
        != rebuilt_from_retained_weights._type_sampling_cdf.tobytes()
    )

    with mock.patch.object(
        kernel_v2,
        "_new_philox",
        side_effect=AssertionError("valid preflight constructed an RNG"),
    ) as rng_factory:
        preflight = kernel_v2._preflight_resources(
            reference, strategy="fixed-budget-sir", budget=1
        )
    assert rng_factory.call_count == 0
    assert preflight == (
        "stochastic-worst-case",
        reference_module.MAX_REFERENCE_BATCH_OCCURRENCES,
        reference_module.MAX_REFERENCE_BATCH_COORDINATES,
        1,
        0,
        None,
        None,
    )


def test_work_limit_precedence_remains_exact_when_count_cdf_is_unavailable() -> None:
    reference = CappedPoissonConfigurationReference(
        {0: 0}, {0: 1.0}, activity=1.0, total_cap=123
    )
    assert reference._count_sampling_cdf is None
    with mock.patch.object(
        kernel_v2,
        "_new_philox",
        side_effect=AssertionError("work preflight constructed an RNG"),
    ), pytest.raises(
        ValueError,
        match="planned stochastic work exceeds reference resource limits",
    ):
        kernel_v2._preflight_resources(
            reference, strategy="fixed-budget-sir", budget=4096
        )


def test_cap_zero_exempts_irrelevant_type_resolution_gate() -> None:
    tiny = float.fromhex("0x1.0000000000000p-41")
    reference = CappedPoissonConfigurationReference(
        {0: 0, 1: 0},
        {0: tiny, 1: float.fromhex("0x1.ffffffffff000p-1")},
        activity=1.0,
        total_cap=0,
    )
    assert reference._type_sampling_cdf is None
    preflight = kernel_v2._preflight_resources(
        reference, strategy="fixed-budget-sir", budget=1
    )
    assert preflight[:5] == (
        "stochastic-worst-case",
        reference_module.MAX_REFERENCE_BATCH_OCCURRENCES,
        reference_module.MAX_REFERENCE_BATCH_COORDINATES,
        0,
        0,
    )


@pytest.mark.parametrize(
    "reference",
    (
        CappedPoissonConfigurationReference(
            {0: 0},
            {0: 1.0},
            activity=float.fromhex("0x1.0000000000000p-41"),
            total_cap=1,
        ),
        CappedPoissonConfigurationReference(
            {0: 0, 1: 0},
            {
                0: float.fromhex("0x1.0000000000000p-41"),
                1: float.fromhex("0x1.ffffffffff000p-1"),
            },
            activity=1.0,
            total_cap=1,
        ),
    ),
)
def test_finite_atomic_enumeration_is_exempt_from_sampling_resolution(
    reference,
) -> None:
    assert reference._count_sampling_cdf is None or reference._type_sampling_cdf is None
    with mock.patch.object(
        reference_module,
        "_resolution_safe_cdf",
        side_effect=AssertionError("enumeration consulted stochastic resolution"),
    ):
        preflight = kernel_v2._preflight_resources(
            reference, strategy="finite-atomic-enumeration", budget=0
        )
    assert preflight[0] == "finite-atomic-oracle"
    assert preflight[5] is not None
    assert preflight[6] is not None


def test_ordinary_frozen_m1_provider_still_certifies_and_executes() -> None:
    provider = _m1_provider()
    plan = kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy="fixed-budget-sir",
        residual_context=(),
        initializer_role_sha256=_KERNEL_ROLE,
        seed=5706,
        budget=2,
    )
    owner = kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        provider, plan=plan
    )
    result = owner.execute()
    assert len(result.particles) == 2
    assert owner.validate_result(result) is result


def test_structural_validators_do_not_invoke_live_boundaries(
    aess, refusal_table
) -> None:
    bundle = oracle.t28_stress_refusal_oracle_bundle_v1()
    with mock.patch.object(
        kernel_v2,
        "_preflight_resources",
        side_effect=AssertionError("kernel preflight replayed"),
    ), mock.patch.object(
        kernel_v2,
        "_new_philox",
        side_effect=AssertionError("RNG constructed"),
    ), mock.patch.object(
        CappedPoissonConfigurationReference,
        "sample_configuration",
        side_effect=AssertionError("reference sampled"),
    ), mock.patch.object(
        cp50_oracle,
        "ess_summary",
        side_effect=AssertionError("invalid boundary replayed"),
    ):
        assert oracle.validate_t28_aess_low_ess_oracle_v1(aess) is aess
        assert oracle.validate_t28_invalid_refusal_table_v1(refusal_table) is (
            refusal_table
        )
        assert oracle.validate_t28_stress_refusal_oracle_bundle_v1(bundle) is bundle


def test_fully_redigested_aess_and_table_semantic_tampering_is_rejected(
    aess, refusal_table
) -> None:
    forged_diagnostic = _redigest(
        "aess-diagnostic",
        _forge(aess.diagnostic, effective_sample_size=Fraction(1, 1)),
    )
    forged_aess = _redigest("aess-oracle", _forge(aess, diagnostic=forged_diagnostic))
    with pytest.raises(ValueError, match="effective sample size"):
        oracle.validate_t28_aess_low_ess_oracle_v1(forged_aess)

    first = _redigest(
        "invalid-case",
        _forge(refusal_table.cases[0], expectation_scope="production-preflight"),
    )
    forged_table = _redigest(
        "invalid-table",
        _forge(refusal_table, cases=(first,) + refusal_table.cases[1:]),
    )
    with pytest.raises(ValueError, match="frozen matrix"):
        oracle.validate_t28_invalid_refusal_table_v1(forged_table)


def test_hostile_types_and_resource_values_fail_before_semantic_equality(
    aess, refusal_table
) -> None:
    forged = _forge(
        aess,
        type_weights=(_EqualityBomb(), Fraction(3, 5)),
    )
    with pytest.raises(TypeError, match="Fraction"):
        oracle.validate_t28_aess_low_ess_oracle_v1(forged)

    forged = _forge(aess, target_normalizer=Fraction(1 << 40_000, 1))
    with pytest.raises(ValueError, match="exact-integer bit bound"):
        oracle.validate_t28_aess_low_ess_oracle_v1(forged)

    forged = _forge(aess, scope="x" * (oracle.MAX_CP57_TEXT_LENGTH + 1))
    with pytest.raises(ValueError, match="bounded length"):
        oracle.validate_t28_aess_low_ess_oracle_v1(forged)

    forged = _forge(
        refusal_table,
        cases=(_EqualityBomb(),) + refusal_table.cases[1:],
    )
    with pytest.raises(TypeError, match="wrong exact type"):
        oracle.validate_t28_invalid_refusal_table_v1(forged)

    forged = _forge(refusal_table, required_case_count=True)
    with pytest.raises(TypeError, match="non-boolean integer"):
        oracle.validate_t28_invalid_refusal_table_v1(forged)


def test_expected_reported_particle_count_rejects_hostile_ne_before_comparison(
    aess,
) -> None:
    forged_diagnostic = _forge(
        aess.diagnostic,
        expected_reported_particle_count=_EqualityBomb(),
    )
    forged_aess = _forge(aess, diagnostic=forged_diagnostic)

    with pytest.raises(TypeError, match="non-boolean integer"):
        oracle.validate_t28_aess_low_ess_oracle_v1(forged_aess)


def test_observation_verifier_rejects_spoofed_type_message_rng_and_result(
    refusal_table,
) -> None:
    case = refusal_table.cases[0]
    states = tuple((role, str(index) * 64) for index, role in enumerate(_RNG_ROLES, 1))
    kwargs = {
        "case_id": case.case_id,
        "observed_exception": ValueError(case.expected_exception_message),
        "validation_boundary": case.validation_boundary,
        "externally_supplied_sentinel_rng_state_sha256_before": states,
        "externally_supplied_sentinel_rng_state_sha256_after": states,
        "rng_factory_call_count": 0,
        "result_artifact_created": False,
    }
    with pytest.raises(ValueError, match="message differs"):
        oracle.verify_t28_invalid_refusal_observation_v1(
            refusal_table,
            **{**kwargs, "observed_exception": ValueError("near match")},
        )

    class ValueErrorSubclass(ValueError):
        pass

    with pytest.raises(TypeError, match="wrong exact type"):
        oracle.verify_t28_invalid_refusal_observation_v1(
            refusal_table,
            **{
                **kwargs,
                "observed_exception": ValueErrorSubclass(
                    case.expected_exception_message
                ),
            },
        )
    changed = states[:-1] + ((_RNG_ROLES[-1], "f" * 64),)
    with pytest.raises(ValueError, match="external sentinel RNG states differ"):
        oracle.verify_t28_invalid_refusal_observation_v1(
            refusal_table,
            **{
                **kwargs,
                "externally_supplied_sentinel_rng_state_sha256_after": changed,
            },
        )
    with pytest.raises(ValueError, match="factory call count"):
        oracle.verify_t28_invalid_refusal_observation_v1(
            refusal_table,
            **{**kwargs, "rng_factory_call_count": 1},
        )
    with pytest.raises(ValueError, match="result artifact"):
        oracle.verify_t28_invalid_refusal_observation_v1(
            refusal_table,
            **{**kwargs, "result_artifact_created": True},
        )


def test_observation_verifier_rejects_production_exception_qualname_spoof(
    refusal_table,
) -> None:
    case = next(
        case
        for case in refusal_table.cases
        if case.case_id == "T28-INVALID-COUNT-CATEGORICAL-RESOLUTION"
    )
    spoof_type = type(
        "UnsupportedReferenceSamplingError",
        (ValueError,),
        {"__module__": "heterodiff.theory.configuration_reference"},
    )
    spoof = spoof_type(case.expected_exception_message)
    assert type(spoof).__module__ + "." + type(spoof).__qualname__ == (
        case.expected_exception_qualname
    )
    states = tuple((role, "b" * 64) for role in _RNG_ROLES)

    with pytest.raises(TypeError, match="wrong exact type"):
        oracle.verify_t28_invalid_refusal_observation_v1(
            refusal_table,
            case_id=case.case_id,
            observed_exception=spoof,
            validation_boundary=case.validation_boundary,
            externally_supplied_sentinel_rng_state_sha256_before=states,
            externally_supplied_sentinel_rng_state_sha256_after=states,
            rng_factory_call_count=0,
            result_artifact_created=False,
        )


def test_records_are_sealed_immutable_and_nonpickleable(aess, refusal_table) -> None:
    states = tuple((role, "a" * 64) for role in _RNG_ROLES)
    case = refusal_table.cases[0]
    observation = oracle.verify_t28_invalid_refusal_observation_v1(
        refusal_table,
        case_id=case.case_id,
        observed_exception=ValueError(case.expected_exception_message),
        validation_boundary=case.validation_boundary,
        externally_supplied_sentinel_rng_state_sha256_before=states,
        externally_supplied_sentinel_rng_state_sha256_after=states,
        rng_factory_call_count=0,
        result_artifact_created=False,
    )
    bundle = oracle.t28_stress_refusal_oracle_bundle_v1()
    records = (
        aess.diagnostic,
        aess,
        refusal_table.cases[0],
        refusal_table,
        observation,
        bundle,
    )
    for record in records:
        with pytest.raises(TypeError, match="pickle"):
            pickle.dumps(record)
        with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
            record.record_sha256 = "0" * 64
        with pytest.raises(TypeError, match="module-created"):
            type(record)()
        with pytest.raises(TypeError, match="subclass"):
            builtins.__build_class__(lambda: None, "HostileSubclass", type(record))


def test_bundle_digests_are_deterministic_distinct_and_cross_process_stable() -> None:
    first = oracle.t28_stress_refusal_oracle_bundle_v1()
    second = oracle.t28_stress_refusal_oracle_bundle_v1()
    assert first.record_sha256 == second.record_sha256
    assert first.aess_record_sha256 == second.aess_record_sha256
    assert (
        first.invalid_refusal_table_record_sha256
        == second.invalid_refusal_table_record_sha256
    )
    assert first.aess_record_sha256 != first.invalid_refusal_table_record_sha256
    assert first.subrecord_digests_distinct is True

    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
from heterodiff.evaluation.mixed_initializer_test28_stress_refusal_oracle import t28_stress_refusal_oracle_bundle_v1
value = t28_stress_refusal_oracle_bundle_v1()
print(value.aess_record_sha256)
print(value.invalid_refusal_table_record_sha256)
print(value.record_sha256)
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = source_root
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert tuple(completed.stdout.splitlines()) == (
        first.aess_record_sha256,
        first.invalid_refusal_table_record_sha256,
        first.record_sha256,
    )


def test_all_claim_boundaries_remain_negative(aess, refusal_table) -> None:
    assert aess.factors_are_exp_of_exact_rational_q is False
    assert aess.score_provider_facade_integrated is False
    assert aess.initializer_kernel_integrated is False
    assert aess.runtime_source_or_rng_law_verified is False
    assert aess.operational_prediction is False
    assert refusal_table.operational_source_or_rng_law_verified is False
    assert refusal_table.confirmatory_evidence is False
    assert refusal_table.formal_test28_evidence is False
    assert refusal_table.manuscript_claim is False
    assert "not a sampled cloud" in aess.nonclaims[1]
    assert "table alone specifies expectations" in refusal_table.nonclaims[3]
    assert "live tests are separate evidence" in refusal_table.nonclaims[3]
