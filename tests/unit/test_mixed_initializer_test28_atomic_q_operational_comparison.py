"""Independent and hostile CP56 ``T28-A0-Q`` operational comparisons."""

from __future__ import annotations

import builtins
from dataclasses import FrozenInstanceError
from fractions import Fraction
from math import factorial
import os
from pathlib import Path
import pickle
import subprocess
import sys
from unittest import mock

import pytest

from heterodiff.evaluation import (
    mixed_initializer_test28_atomic_q_operational_comparison as comparison,
)
from heterodiff.evaluation import mixed_initializer_test28_atomic_q_oracle as oracle
from heterodiff.processes import certified_initial_score_provider_v1 as score_provider
from heterodiff.processes import (
    plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 as kernel_v2,
)
from heterodiff.theory.configuration_reference import (
    CappedPoissonConfigurationReference,
)


_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)
_HALF = Fraction(1, 2)
_PROTOCOL_COUNTS = ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1), (0, 2))
_RUNTIME_COUNTS = ((0, 0), (0, 1), (1, 0), (0, 2), (1, 1), (2, 0))
_RUNTIME_TO_PROTOCOL = (0, 2, 1, 5, 4, 3)
_PROTOCOL_SCORES = (
    Fraction(0),
    Fraction(1, 2),
    Fraction(-1, 2),
    Fraction(1),
    Fraction(1, 2),
    Fraction(-1),
)
_RUNTIME_SCORES = (
    Fraction(0),
    Fraction(-1, 2),
    Fraction(1, 2),
    Fraction(-1),
    Fraction(1, 2),
    Fraction(1),
)
_RUNTIME_OUTPUT_HEX = (
    "0x1.7ade79b3ae4fcp-2",
    "0x1.13c13c86fd12fp-3",
    "0x1.f3b835374e505p-3",
    "0x1.9168b59dc254ap-6",
    "0x1.2bd4ecbac896bp-3",
    "0x1.498f2ed7ae37fp-4",
)
_INDEPENDENT_WIDTH = Fraction(1, 1 << 384)


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


def _positive_exp_bracket(value: Fraction) -> tuple[Fraction, Fraction]:
    """Independent positive Taylor bracket with a geometric tail bound."""

    assert _ZERO < value <= _ONE
    term = _ONE
    partial = _ONE
    for index in range(1, 8193):
        term = term * value / index
        partial += term
        next_term = term * value / (index + 1)
        tail_ratio = value / (index + 2)
        upper = partial + next_term / (_ONE - tail_ratio)
        if upper - partial <= _INDEPENDENT_WIDTH:
            return partial, upper
    raise AssertionError("independent exponential enclosure exhausted")


def _exp_bracket(value: Fraction) -> tuple[Fraction, Fraction]:
    if value == _ZERO:
        return _ONE, _ONE
    if value > _ZERO:
        return _positive_exp_bracket(value)
    lower, upper = _positive_exp_bracket(-value)
    return _ONE / upper, _ONE / lower


def _independent_analytic_probabilities():
    weights = (Fraction.from_float(0.4), Fraction.from_float(0.6))
    raw = []
    for count_vector in _PROTOCOL_COUNTS:
        mass = _ONE
        for index in range(2):
            mass *= weights[index] ** count_vector[index]
            mass /= factorial(count_vector[index])
        raw.append(mass)
    normalizer = sum(raw, _ZERO)
    assert normalizer == Fraction(5, 2)
    base = tuple(value / normalizer for value in raw)
    weighted = []
    for index in range(6):
        exp_lower, exp_upper = _exp_bracket(_PROTOCOL_SCORES[index])
        weighted.append((base[index] * exp_lower, base[index] * exp_upper))
    z_lower = sum((value[0] for value in weighted), _ZERO)
    z_upper = sum((value[1] for value in weighted), _ZERO)
    return tuple((value[0] / z_upper, value[1] / z_lower) for value in weighted)


def _independent_half_l1(record):
    analytic = _independent_analytic_probabilities()
    absolute = []
    for index in range(6):
        point = Fraction.from_float(record.protocol_output_weights_binary64[index])
        lower = point - analytic[index][1]
        upper = point - analytic[index][0]
        if lower >= 0:
            absolute.append((lower, upper))
        elif upper <= 0:
            absolute.append((-upper, -lower))
        else:
            absolute.append((_ZERO, max(-lower, upper)))
    return (
        _HALF * sum((value[0] for value in absolute), _ZERO),
        _HALF * sum((value[1] for value in absolute), _ZERO),
    )


@pytest.fixture(scope="module")
def record():
    return comparison.t28_a0_q_operational_comparison_v1()


def test_import_is_torch_lazy_and_has_no_execution_side_effect() -> None:
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
import builtins
import sys
real_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == "torch" or name.startswith("torch."):
        raise AssertionError("torch crossed the CP56 comparison import boundary")
    return real_import(name, *args, **kwargs)
builtins.__import__ = guarded
import heterodiff.evaluation.mixed_initializer_test28_atomic_q_operational_comparison
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


def test_canonical_kernel_path_is_count_keyed_not_positional(record) -> None:
    assert record.fixture_id == "T28-A0-Q"
    assert record.kernel.provider.certificate.backend_kind == (
        "atomic-q-score-table-v1"
    )
    assert (
        record.kernel.provider.backend_adapter.source
        is record.oracle_pair.score_provider
    )
    assert record.kernel.plan.strategy == "finite-atomic-enumeration"
    assert record.kernel.plan.residual_context == ()
    assert record.adapter_role_sha256 == (
        comparison.CP56_TEST28_ATOMIC_Q_ADAPTER_ROLE_SHA256
    )
    assert record.initializer_role_sha256 == (
        comparison.CP56_TEST28_ATOMIC_Q_INITIALIZER_ROLE_SHA256
    )
    assert record.protocol_count_vectors == _PROTOCOL_COUNTS
    assert record.runtime_count_vectors == _RUNTIME_COUNTS
    assert record.runtime_to_protocol_permutation == _RUNTIME_TO_PROTOCOL
    assert record.runtime_exact_scores == _RUNTIME_SCORES
    assert record.runtime_exact_scores != _PROTOCOL_SCORES

    for atom in record.kernel_result.atoms:
        source_point = atom.scored.evaluation.source_evaluation
        assert source_point.count_vector == atom.count_state
        protocol_index = _PROTOCOL_COUNTS.index(atom.count_state)
        assert source_point.exact_score == _PROTOCOL_SCORES[protocol_index]
        assert atom.scored.exact_log_weight == source_point.exact_score


def test_operational_binary64_vectors_and_hashes_are_exact(record) -> None:
    assert tuple(value.hex() for value in record.runtime_output_weights_binary64) == (
        _RUNTIME_OUTPUT_HEX
    )
    assert record.represented_log_normalizer_float64.hex() == ("0x1.3f72ebf905c68p-4")
    assert record.protocol_output_weights_binary64 == tuple(
        record.runtime_output_weights_binary64[_RUNTIME_COUNTS.index(count)]
        for count in _PROTOCOL_COUNTS
    )
    assert record.protocol_base_masses_binary64 == tuple(
        record.runtime_base_masses_binary64[_RUNTIME_COUNTS.index(count)]
        for count in _PROTOCOL_COUNTS
    )
    assert record.runtime_base_masses_sha256 == comparison._float_vector_sha256(
        record.runtime_base_masses_binary64, law="runtime-base"
    )
    assert record.protocol_base_masses_sha256 == comparison._float_vector_sha256(
        record.protocol_base_masses_binary64, law="protocol-base"
    )
    assert record.runtime_output_weights_sha256 == comparison._float_vector_sha256(
        record.runtime_output_weights_binary64, law="runtime-output"
    )
    assert record.protocol_output_weights_sha256 == comparison._float_vector_sha256(
        record.protocol_output_weights_binary64, law="protocol-output"
    )
    assert record.kernel_result_sha256 == record.kernel_result.result_sha256
    assert (
        record.kernel_certificate_sha256 == record.kernel.certificate.certificate_sha256
    )


def test_exact_float_sums_are_preserved_and_half_l1_is_not_mislabeled(record) -> None:
    exact_base = sum(
        (Fraction.from_float(value) for value in record.protocol_base_masses_binary64),
        _ZERO,
    )
    exact_output = sum(
        (
            Fraction.from_float(value)
            for value in record.protocol_output_weights_binary64
        ),
        _ZERO,
    )
    assert record.exact_base_mass_sum == exact_base
    assert record.exact_base_mass_sum_residual == (
        comparison.CP56_TEST28_ATOMIC_Q_BASE_SUM_RESIDUAL
    )
    assert record.exact_output_weight_sum == exact_output
    assert record.exact_output_weight_sum_residual == (
        comparison.CP56_TEST28_ATOMIC_Q_OUTPUT_SUM_RESIDUAL
    )
    assert record.exact_output_probability_measure_verified is False
    assert record.half_l1_is_total_variation is False
    assert "half-L1" in record.nonclaims[2]


def test_rigorous_discrepancy_encloses_independent_384_bit_derivation(record) -> None:
    independent_probabilities = _independent_analytic_probabilities()
    for index in range(6):
        cp55 = record.oracle_pair.binary64_parameter.target_probability_intervals[index]
        independent = independent_probabilities[index]
        assert cp55.lower <= independent[0] <= independent[1] <= cp55.upper

        point = Fraction.from_float(record.protocol_output_weights_binary64[index])
        independent_signed = (point - independent[1], point - independent[0])
        recorded_signed = record.signed_output_weight_minus_analytic_intervals[index]
        assert recorded_signed.lower <= independent_signed[0]
        assert independent_signed[1] <= recorded_signed.upper
        assert not recorded_signed.lower <= 0 <= recorded_signed.upper

    independent_half_l1 = _independent_half_l1(record)
    recorded = record.half_l1_discrepancy_interval
    assert recorded.lower <= independent_half_l1[0]
    assert independent_half_l1[1] <= recorded.upper
    assert recorded.lower > 0
    assert recorded.width > 0
    assert float(recorded.lower) == pytest.approx(8.508157450884242e-17)
    assert float(recorded.upper) == pytest.approx(8.508157450884242e-17)


def test_base_oracle_and_analytic_parameter_laws_are_quantified_not_equal(
    record,
) -> None:
    analytic_base = record.oracle_pair.binary64_parameter.normalized_base_masses
    exact_points = tuple(
        Fraction.from_float(value) for value in record.protocol_base_masses_binary64
    )
    expected = tuple(exact_points[index] - analytic_base[index] for index in range(6))
    assert record.base_minus_analytic_exact_discrepancies == expected
    assert record.base_half_l1_discrepancy == _HALF * sum(
        (abs(value) for value in expected), _ZERO
    )
    assert record.base_half_l1_discrepancy > 0
    assert record.base_law == "P_ref^{oracle,b64}"
    assert record.output_record == "P_enum^{kernel,b64}"
    assert record.analytic_comparator == "Pi_A0Q^{b64}"
    assert record.operational_reference_source_law_verified is False
    assert record.analytic_target_equality_verified is False
    assert record.facade_adapter_integration_verified is True
    assert record.kernel_v2_enumeration_integration_verified is True
    assert record.cryptographic_authentication is False


def test_structural_validation_never_executes_or_replays_score_rng_or_sampler(
    record,
) -> None:
    provider = record.kernel.provider
    source = provider.backend_adapter.source
    reference = provider.reference
    with mock.patch.object(
        type(record.kernel),
        "execute",
        side_effect=AssertionError("kernel execution replayed"),
    ), mock.patch.object(
        type(provider),
        "evaluate",
        side_effect=AssertionError("provider evaluation replayed"),
    ), mock.patch.object(
        type(source),
        "evaluate",
        side_effect=AssertionError("score-table evaluation replayed"),
    ), mock.patch.object(
        type(reference),
        "sample_configuration",
        side_effect=AssertionError("reference sampler replayed"),
    ), mock.patch.object(
        comparison._kernel,
        "_new_philox",
        side_effect=AssertionError("RNG replayed"),
    ):
        assert comparison.validate_t28_a0_q_operational_comparison_v1(record) is record
        rebuilt = comparison.compare_t28_a0_q_kernel_enumeration_v1(
            record.oracle_pair, record.kernel, record.kernel_result
        )
        assert rebuilt.semantic_comparison_sha256 == record.semantic_comparison_sha256
        assert rebuilt.instance_custody_sha256 == record.instance_custody_sha256


def test_wrong_oracle_identity_and_non_enumeration_results_fail_closed(record) -> None:
    another_pair = oracle.t28_a0_q_oracle_pair()
    with pytest.raises(ValueError, match="source"):
        comparison.compare_t28_a0_q_kernel_enumeration_v1(
            another_pair, record.kernel, record.kernel_result
        )
    with pytest.raises(TypeError, match="enumeration"):
        comparison.compare_t28_a0_q_kernel_enumeration_v1(
            record.oracle_pair, record.kernel, object()
        )


@pytest.mark.parametrize(
    "adapter_role,initializer_role,match",
    (
        (
            "0" * 64,
            comparison.CP56_TEST28_ATOMIC_Q_INITIALIZER_ROLE_SHA256,
            "adapter role",
        ),
        (
            comparison.CP56_TEST28_ATOMIC_Q_ADAPTER_ROLE_SHA256,
            "1" * 64,
            "initializer role",
        ),
    ),
)
def test_noncanonical_role_custody_fails_closed(
    adapter_role, initializer_role, match
) -> None:
    pair = oracle.t28_a0_q_oracle_pair()
    reference = CappedPoissonConfigurationReference(
        {0: 0, 1: 0},
        {0: 0.4, 1: 0.6},
        activity=1.0,
        total_cap=2,
    )
    provider = score_provider.adapt_atomic_q_score_table_provider_v1(
        pair.score_provider,
        reference=reference,
        adapter_role_sha256=adapter_role,
    )
    plan = kernel_v2.make_mixed_support_initial_tilt_initializer_plan_v2(
        provider,
        strategy="finite-atomic-enumeration",
        residual_context=(),
        initializer_role_sha256=initializer_role,
    )
    owner = kernel_v2.certify_mixed_support_initial_tilt_initializer_kernel_v2(
        provider, plan=plan
    )
    result = owner.execute()
    with pytest.raises(ValueError, match=match):
        comparison.compare_t28_a0_q_kernel_enumeration_v1(pair, owner, result)


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("runtime_to_protocol_permutation", (0, 1, 2, 3, 4, 5)),
        ("exact_output_weight_sum_residual", Fraction(0)),
        ("analytic_target_equality_verified", True),
        ("half_l1_is_total_variation", True),
        ("categorical_draw_executed", True),
    ),
)
def test_fully_redigested_semantic_tampering_is_rejected(
    record, field, replacement
) -> None:
    forged = _forge(record, **{field: replacement})
    object.__setattr__(
        forged,
        "instance_custody_sha256",
        comparison._instance_custody_sha256(forged),
    )
    with pytest.raises(ValueError, match="field"):
        comparison.validate_t28_a0_q_operational_comparison_v1(forged)


@pytest.mark.parametrize(
    "field,replacement,error_type",
    (
        (
            "protocol_count_vectors",
            (_EqualityBomb(),) + _PROTOCOL_COUNTS[1:],
            TypeError,
        ),
        (
            "runtime_to_protocol_permutation",
            (False,) + _RUNTIME_TO_PROTOCOL[1:],
            TypeError,
        ),
        (
            "runtime_exact_scores",
            (_EqualityBomb(),) + _RUNTIME_SCORES[1:],
            TypeError,
        ),
        (
            "runtime_source_evaluation_sha256s",
            (_EqualityBomb(),) + ("0" * 64,) * 5,
            TypeError,
        ),
        (
            "runtime_output_weights_binary64",
            (_EqualityBomb(),) + (0.1,) * 5,
            TypeError,
        ),
        (
            "signed_output_weight_minus_analytic_intervals",
            (_EqualityBomb(),) + (oracle.ClosedRationalInterval(_ZERO, _ONE),) * 5,
            TypeError,
        ),
        ("exact_output_weight_sum", Fraction(1 << 40_000), ValueError),
        ("scope", "a" * (comparison.MAX_CP56_TEXT_LENGTH + 1), ValueError),
        ("formal_test_28_closed", 0, TypeError),
    ),
)
def test_hostile_types_and_resources_fail_before_semantic_equality(
    record, field, replacement, error_type
) -> None:
    forged = _forge(record, **{field: replacement})
    with pytest.raises(error_type):
        comparison.validate_t28_a0_q_operational_comparison_v1(forged)


def test_record_is_sealed_nonpickle_immutable_and_not_publicly_constructible(
    record,
) -> None:
    with pytest.raises(TypeError):
        comparison.AtomicQOperationalComparisonV1()
    with pytest.raises(TypeError, match="subclass"):
        builtins.__build_class__(
            lambda: None,
            "HostileComparison",
            comparison.AtomicQOperationalComparisonV1,
        )
    with pytest.raises(TypeError, match="pickle"):
        pickle.dumps(record)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        record.instance_custody_sha256 = "0" * 64


def test_semantic_record_is_deterministic_in_one_unchanged_runtime(record) -> None:
    same_instance = comparison.compare_t28_a0_q_kernel_enumeration_v1(
        record.oracle_pair, record.kernel, record.kernel_result
    )
    assert same_instance.semantic_comparison_sha256 == record.semantic_comparison_sha256
    assert same_instance.instance_custody_sha256 == record.instance_custody_sha256
    assert same_instance.parameter_key() == record.parameter_key()

    fresh_instance = comparison.t28_a0_q_operational_comparison_v1()
    assert fresh_instance.semantic_comparison_sha256 == (
        record.semantic_comparison_sha256
    )
    assert fresh_instance.parameter_key() == record.parameter_key()
    assert fresh_instance.runtime_instance_key() != record.runtime_instance_key()
    assert fresh_instance.kernel_certificate_sha256 != (
        record.kernel_certificate_sha256
    )
    assert fresh_instance.kernel_result_sha256 != record.kernel_result_sha256
    assert comparison.t28_a0_q_operational_semantic_sha256(record) == (
        record.semantic_comparison_sha256
    )
    assert comparison.t28_a0_q_operational_instance_custody_sha256(record) == (
        record.instance_custody_sha256
    )
    assert record.semantic_digest_excludes_runtime_instance_digests is True
    assert record.semantic_digest_fresh_construction_stable is True
    assert (
        record.semantic_digest_cross_process_stable_under_identical_runtime_and_float_outputs
        is True
    )
    assert record.semantic_digest_runtime_portable is False
    assert record.runtime_instance_digests_bound is True
    assert record.instance_custody_digest_cross_process_stable is False
    assert record.runtime_portable is False
    assert record.formal_test_28_closed is False
    assert record.confirmatory_evidence is False
    assert record.manuscript_claim is False
    assert record.categorical_draw_executed is False


def test_semantic_digest_is_stable_in_a_fresh_process(record) -> None:
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    code = r"""
from heterodiff.evaluation.mixed_initializer_test28_atomic_q_operational_comparison import t28_a0_q_operational_comparison_v1
print(t28_a0_q_operational_comparison_v1().semantic_comparison_sha256)
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
    assert completed.stdout.strip() == record.semantic_comparison_sha256


def test_source_contains_no_positional_zip_score_projection() -> None:
    source = Path(comparison.__file__).read_text(encoding="utf-8")
    assert "zip(" not in source
    assert "count_vectors.index(count_vector)" in source
    assert "runtime_atoms_by_count[count]" in source
