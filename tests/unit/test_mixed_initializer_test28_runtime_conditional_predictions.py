"""Independent hostile tests for CP59 conditional runtime arithmetic."""

from __future__ import annotations

import ast
import bisect
from dataclasses import FrozenInstanceError, fields, make_dataclass
from fractions import Fraction
import hashlib
import math
from pathlib import Path
import pickle
import subprocess
import sys

import mpmath
import pytest

from heterodiff.evaluation import (
    mixed_initializer_test28_runtime_conditional_predictions as predictions,
)


_ZERO_SHA = "0" * 64
_D53 = 1 << 53
_D64 = 1 << 64


class _LenBomb:
    def __len__(self):
        raise AssertionError(
            "validator invoked hostile __len__ before exact-type check"
        )


class _ComparisonBomb:
    def __eq__(self, other):
        del other
        raise AssertionError("validator invoked hostile __eq__ before exact-type check")

    def __ne__(self, other):
        del other
        raise AssertionError("validator invoked hostile __ne__ before exact-type check")

    def __lt__(self, other):
        del other
        raise AssertionError("validator invoked hostile __lt__ before exact-type check")

    def __gt__(self, other):
        del other
        raise AssertionError("validator invoked hostile __gt__ before exact-type check")


def _hash(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _hashes(count: int) -> tuple[str, ...]:
    return tuple(_hash("cp59-hostile-slot-%d" % index) for index in range(count))


def _fraction_ceiling(value: Fraction) -> int:
    return -((-value.numerator) // value.denominator)


def _independent_grid_counts(cdf: tuple[Fraction, ...]) -> tuple[int, ...]:
    boundaries = (0,) + tuple(_fraction_ceiling(_D53 * value) for value in cdf)
    return tuple(right - left for left, right in zip(boundaries, boundaries[1:]))


def _half_l1(left: tuple[Fraction, ...], right: tuple[Fraction, ...]) -> Fraction:
    return sum((abs(a - b) for a, b in zip(left, right)), Fraction(0, 1)) / 2


def _interval_half_l1(lower, upper, vector, probability_vectors):
    minimum = Fraction(0, 1)
    maximum = Fraction(0, 1)
    for lo, hi, value in zip(lower, upper, vector):
        if value < lo:
            minimum += lo - value
        elif value > hi:
            minimum += value - hi
        maximum += max(abs(value - lo), abs(value - hi))
    result = minimum / 2, maximum / 2
    if probability_vectors:
        return min(Fraction(1, 1), result[0]), min(Fraction(1, 1), result[1])
    return result


def _forge(instance, **changes):
    forged = object.__new__(type(instance))
    for item in fields(type(instance)):
        object.__setattr__(
            forged,
            item.name,
            changes.get(item.name, getattr(instance, item.name)),
        )
    return forged


def _redigest(instance, kind: str, **changes):
    forged = _forge(instance, **changes, record_sha256=_ZERO_SHA)
    return _forge(
        forged,
        record_sha256=predictions._digest(
            kind,
            {item.name: getattr(forged, item.name) for item in fields(type(forged))},
        ),
    )


def _alien_sealed_clone(instance):
    try:
        alien_type = make_dataclass(
            "CP59HostileAlien" + type(instance).__name__,
            [(item.name, item.type) for item in fields(type(instance))],
            bases=(predictions._SealedRecord,),
            frozen=True,
            init=False,
            slots=True,
        )
    except TypeError:
        # Sealing the base against external subclasses is itself a valid fix.
        return None
    alien = object.__new__(alien_type)
    for item in fields(type(instance)):
        object.__setattr__(alien, item.name, getattr(instance, item.name))
    return alien


def _independent_current_kernel_weights(scores) -> tuple[float, ...]:
    """Reproduce only the documented float64 normalization arithmetic."""

    import numpy as np

    logs = np.asarray([float(value) for value in scores], dtype=np.float64)
    shifted = np.exp(logs - float(np.max(logs)))
    total = math.fsum(float(value) for value in shifted)
    return tuple(float(value) for value in shifted / total)


def _sir(scores, weights=None):
    scores = tuple(scores)
    if weights is None:
        weights = _independent_current_kernel_weights(scores)
    return predictions.predict_cp59_realized_sir_cloud(
        fixture_id="T28-M2-Q",
        exact_log_scores=scores,
        retained_float64_weights=tuple(weights),
        configuration_sha256s=_hashes(len(scores)),
        supplied_unverified_kernel_result_sha256=_hash("unverified-kernel-result"),
    )


def _rejection(scores, probabilities, attempt_cap=4, upper=Fraction(0)):
    scores = tuple(scores)
    return predictions.predict_cp59_conditional_rejection_finite_law(
        fixture_id="T28-M2-Q",
        exact_log_scores=scores,
        exact_upper_bound=upper,
        proposal_probabilities=tuple(probabilities),
        attempt_cap=attempt_cap,
        configuration_sha256s=_hashes(len(scores)),
        supplied_unverified_kernel_result_sha256=_hash("unverified-kernel-result"),
    )


def _independent_uint64_exp_quota(delta: Fraction) -> int:
    if delta == 0:
        return _D64
    mpmath.mp.dps = 200
    exact = _D64 * mpmath.exp(mpmath.mpf(delta.numerator) / delta.denominator)
    return int(mpmath.floor(exact))


def _assert_independent_rejection_math(result) -> None:
    quotas = tuple(
        _independent_uint64_exp_quota(score - result.exact_upper_bound)
        for score in result.exact_log_scores
    )
    p64 = tuple(Fraction(quota, _D64) for quota in quotas)
    joints = tuple(
        nu * probability for nu, probability in zip(result.proposal_probabilities, p64)
    )
    alpha = sum(joints, Fraction(0))
    first = tuple((1 - alpha) ** offset * alpha for offset in range(result.attempt_cap))
    exhausted = (1 - alpha) ** result.attempt_cap
    assert tuple(atom.quota for atom in result.atoms) == quotas
    assert tuple(atom.p64 for atom in result.atoms) == p64
    assert (
        tuple(atom.joint_proposal_and_acceptance_probability for atom in result.atoms)
        == joints
    )
    assert result.finite_calibration_acceptance_probability == alpha
    assert (
        tuple(attempt.first_accept_probability for attempt in result.attempt_masses)
        == first
    )
    assert result.selection_within_attempt_cap_probability == sum(first, Fraction(0))
    assert result.exhaustion_probability == exhausted
    assert result.total_probability == 1


def test_source_law_support_obstruction_toy_rederivation() -> None:
    # One uniform root in a four-point space can produce only four pairs, while
    # the product-uniform pair space has sixteen atoms.
    root_domain = tuple(range(4))
    deterministic_pairs = {(root, root) for root in root_domain}
    product_pairs = tuple(
        (left, right) for left in root_domain for right in root_domain
    )
    tv = Fraction(1, 2) * sum(
        (
            abs(
                (Fraction(1, 4) if pair in deterministic_pairs else Fraction(0, 1))
                - Fraction(1, 16)
            )
            for pair in product_pairs
        ),
        Fraction(0, 1),
    )
    assert tv == Fraction(3, 4) == 1 - Fraction(1, 4)

    fixed_pair = (0, 0)
    fixed_tv = Fraction(1, 2) * sum(
        (
            abs(Fraction(pair == fixed_pair, 1) - Fraction(1, 16))
            for pair in product_pairs
        ),
        Fraction(0, 1),
    )
    assert fixed_tv == Fraction(15, 16) == 1 - Fraction(1, 16)


def test_source_law_boundary_is_explicit_and_fail_closed() -> None:
    boundary = predictions.cp59_source_law_boundary()
    assert predictions.validate_cp59_source_law_boundary(boundary) is boundary
    assert boundary.fixed_seed_replay_is_point_mass is True
    assert boundary.deterministic_replay_establishes_source_law is False
    assert boundary.plan_seed_bits == 64
    assert boundary.maximum_seed_pushforward_joint_trace_support == 1 << 64
    assert boundary.comparison_raw_word_coordinate_count == 2
    assert boundary.product_uniform_comparison_support == 1 << 128
    assert boundary.uniform_seed_pushforward_product_uniform_tv_lower_bound == (
        1 - Fraction(1, 1 << 64)
    )
    assert boundary.fixed_seed_point_mass_product_uniform_tv == (
        1 - Fraction(1, 1 << 128)
    )
    assert boundary.source_to_output_tv_nonconverse == (
        predictions.CP59_TEST28_SOURCE_TO_OUTPUT_TV_NONCONVERSE
    )
    assert boundary.source_support_obstruction_implies_output_tv_lower_bound is False
    assert boundary.current_kernel_iid_product_uniform_model_permitted is False
    assert (
        boundary.richer_external_source_api_or_correlated_seed_pushforward_required
        is True
    )
    assert boundary.external_joint_source_declaration_required is True
    assert "declaration alone cannot change support" in (
        boundary.external_source_assumption_requirement
    )
    for name in (
        "mu_fp_identified",
        "numpy_transform_law_verified",
        "philox_word_law_verified",
        "runtime_dependency_source_map_frozen",
        "numpy_version_alone_sufficient",
        "standard_normal_variable_word_consumption_accounted",
        "standard_normal_variable_consumption_totality_verified",
        "proposal_iid_verified",
        "role_stream_independence_verified",
        "decision_uint64_uniformity_verified",
        "resampling_uniform53_verified",
        "operational_alpha64_derived",
        "operational_rho64_derived",
        "operational_refusal_probability_derived",
        "unconditional_finite_j_sir_law_derived",
        "confirmatory_evidence",
        "formal_test_28_closed",
    ):
        assert getattr(boundary, name) is False
    assert boundary.compiled_numpy_scipy_abi_libm_lock_required is True
    assert boundary.formal_test_28_status == "OPEN"


def test_source_law_boundary_rejects_even_redigested_tamper() -> None:
    boundary = predictions.cp59_source_law_boundary()
    for changes in (
        {"plan_seed_bits": True},
        {"maximum_seed_pushforward_joint_trace_support": 1 << 65},
        {"current_kernel_iid_product_uniform_model_permitted": True},
        {"source_support_obstruction_implies_output_tv_lower_bound": True},
        {"external_joint_source_declaration_required": False},
        {"formal_test_28_closed": True},
    ):
        forged = _redigest(boundary, "source-law-boundary", **changes)
        with pytest.raises((TypeError, ValueError)):
            predictions.validate_cp59_source_law_boundary(forged)


def test_exact_right_sided_53bit_boundary_cells() -> None:
    result = _sir((Fraction(0),) * 4)
    cdf = tuple(slot.cdf_exact for slot in result.slots)
    assert cdf == (
        Fraction(1, 4),
        Fraction(1, 2),
        Fraction(3, 4),
        Fraction(1, 1),
    )
    counts = tuple(slot.categorical_53bit_cell_count for slot in result.slots)
    assert counts == (_D53 // 4,) * 4
    assert counts == _independent_grid_counts(cdf)
    assert sum(counts) == _D53
    assert result.abstract_uniform_53bit_grid_assumed_for_formula is True
    assert result.resampling_uniform53_verified is False
    assert (
        tuple(slot.ideal_probability_lower for slot in result.slots)
        == (Fraction(1, 4),) * 4
    )
    assert (
        tuple(slot.ideal_probability_upper for slot in result.slots)
        == (Fraction(1, 4),) * 4
    )

    # Equality at an interior CDF endpoint moves to the right-hand cell.
    for index, endpoint in enumerate(cdf[:-1]):
        grid_index = int(endpoint * _D53)
        grid_value = Fraction(grid_index, _D53)
        assert bisect.bisect_right(cdf, grid_value) == index + 1
        assert grid_index == sum(counts[: index + 1])


def test_nonunit_retained_vector_is_not_mislabeled_tv() -> None:
    third = float.fromhex("0x1.5555555555555p-2")
    result = _sir((Fraction(0),) * 3, (third,) * 3)
    raw = tuple(Fraction.from_float(third) for _ in range(3))
    assert result.retained_float64_weight_sum_exact == sum(raw, Fraction(0, 1))
    assert result.retained_float64_weight_sum_residual != 0
    assert (
        tuple(slot.nonoperational_exact_renormalized_weight for slot in result.slots)
        == (Fraction(1, 3),) * 3
    )
    assert result.nonoperational_exact_renormalized_sum == 1
    assert "half_l1" in "ideal_to_retained_float_half_l1_lower"
    assert not hasattr(result, "ideal_to_retained_float_tv_lower")
    retained_discrepancy_fields = tuple(
        item.name
        for item in fields(type(result))
        if "retained_float" in item.name
        and ("half_l1" in item.name or "tv" in item.name)
    )
    assert retained_discrepancy_fields
    assert all(
        "half_l1" in name and "tv" not in name for name in retained_discrepancy_fields
    )


@pytest.mark.parametrize(
    "scores",
    (
        (Fraction(0),) * 4,
        (Fraction(0), Fraction(-1, 2), Fraction(1, 3)),
        (Fraction(0), Fraction(-1), Fraction(-2)),
        (Fraction(0), Fraction(-27), Fraction(-27)),
    ),
)
def test_sir_all_exact_component_arithmetic(scores) -> None:
    weights = _independent_current_kernel_weights(scores)
    result = _sir(scores)
    assert predictions.validate_cp59_realized_sir_cloud_prediction(result) is result
    raw = tuple(Fraction.from_float(value) for value in weights)
    raw_sum = sum(raw, Fraction(0, 1))
    renormalized = tuple(value / raw_sum for value in raw)
    cdf = tuple(slot.cdf_exact for slot in result.slots)
    increments = tuple(
        current - previous
        for previous, current in zip((Fraction(0, 1),) + cdf[:-1], cdf)
    )
    counts = _independent_grid_counts(cdf)
    grid = tuple(Fraction(value, _D53) for value in counts)
    assert result.retained_float64_weight_sum_exact == raw_sum
    assert result.retained_float64_weight_sum_residual == raw_sum - 1
    assert tuple(slot.retained_float64_weight_exact for slot in result.slots) == raw
    assert (
        tuple(slot.nonoperational_exact_renormalized_weight for slot in result.slots)
        == renormalized
    )
    assert tuple(slot.cdf_increment_probability for slot in result.slots) == increments
    assert tuple(slot.categorical_53bit_cell_count for slot in result.slots) == counts
    assert tuple(slot.categorical_53bit_probability for slot in result.slots) == grid
    assert sum(increments, Fraction(0, 1)) == 1
    assert sum(grid, Fraction(0, 1)) == 1
    assert result.retained_float_to_cdf_half_l1 == _half_l1(raw, increments)
    assert result.nonoperational_renormalized_to_cdf_tv == _half_l1(
        renormalized, increments
    )
    assert result.cdf_to_categorical_53bit_tv == _half_l1(increments, grid)


def test_independent_normalization_formula_matches_frozen_production_helper() -> None:
    from heterodiff.processes import (
        plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 as kernel,
    )

    bundle = predictions.cp59_arithmetic_calibration_bundle()
    score_tables = (
        bundle.m1_realized_sir_calibration.exact_log_scores,
        bundle.m2_realized_sir_calibration.exact_log_scores,
        (Fraction(0), Fraction(-1, 2), Fraction(1, 3)),
        (Fraction(0), Fraction(-27), Fraction(-27)),
        (Fraction(0),) * 64,
    )
    for scores in score_tables:
        independent = _independent_current_kernel_weights(scores)
        production = tuple(
            float(value)
            for value in kernel.normalize_mixed_support_sir_exact_log_weights_v2(scores)
        )
        assert tuple(value.hex() for value in independent) == tuple(
            value.hex() for value in production
        )


def test_exact_cells_match_production_selector_at_every_interior_boundary() -> None:
    from heterodiff.processes import (
        plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2 as kernel,
    )

    scores = (Fraction(0), Fraction(-1, 2), Fraction(1, 3), Fraction(-7, 11))
    result = _sir(scores)
    production_weights = kernel.normalize_mixed_support_sir_exact_log_weights_v2(scores)
    counts = tuple(slot.categorical_53bit_cell_count for slot in result.slots)
    cumulative = tuple(sum(counts[: index + 1]) for index in range(len(counts)))
    probes = {0, _D53 - 1}
    for boundary in cumulative[:-1]:
        probes.update(
            value
            for value in (boundary - 1, boundary, boundary + 1)
            if 0 <= value < _D53
        )
    for grid_index in sorted(probes):
        expected = next(
            index for index, boundary in enumerate(cumulative) if grid_index < boundary
        )
        for unused_low_bits in (0, (1 << 11) - 1):
            raw_word = (grid_index << 11) | unused_low_bits
            assert (
                kernel.select_mixed_support_sir_index_v2(production_weights, raw_word)
                == expected
            )


def test_builders_never_import_or_invoke_production_kernel_module(monkeypatch) -> None:
    imported = []
    original = predictions.importlib.import_module

    def recording_import(name, *args, **kwargs):
        imported.append(name)
        return original(name, *args, **kwargs)

    monkeypatch.setattr(predictions.importlib, "import_module", recording_import)
    _sir((Fraction(0), Fraction(-1, 3)))
    _rejection(
        (Fraction(0), Fraction(-1, 3)),
        (Fraction(1, 3), Fraction(2, 3)),
        attempt_cap=2,
    )
    assert "numpy" in imported
    assert "heterodiff.processes.arbitrary_rational_uint64_exp_quota" in imported
    assert not any("initializer_kernel" in name for name in imported)


def test_quota_dependency_source_custody_and_nonattestation_flags() -> None:
    from heterodiff.processes import arbitrary_rational_uint64_exp_quota as quota

    source_sha256 = hashlib.sha256(Path(quota.__file__).read_bytes()).hexdigest()
    assert source_sha256 == predictions.CP59_TEST28_QUOTA_DEPENDENCY_SOURCE_SHA256
    records = (
        _sir((Fraction(0), Fraction(-1, 3))),
        _rejection(
            (Fraction(0), Fraction(-1, 3)),
            (Fraction(1, 3), Fraction(2, 3)),
            attempt_cap=2,
        ),
    )
    for record in records:
        assert record.quota_dependency_source_sha256 == source_sha256
        assert record.quota_dependency_independently_reimplemented is False
        assert record.clean_process_dependency_binding_assumed is True
        assert record.in_memory_quota_callable_integrity_attested is False
        assert record.decimal_implementation_formally_verified is False


def test_ideal_exp_probability_intervals_independently_enclose_mpmath() -> None:
    scores = (Fraction(0), Fraction(-1, 2), Fraction(1, 3), Fraction(-7, 11))
    result = _sir(scores)
    mpmath.mp.dps = 200
    exponentials = tuple(
        mpmath.exp(mpmath.mpf(value.numerator) / value.denominator) for value in scores
    )
    total = sum(exponentials)
    ideal = tuple(value / total for value in exponentials)
    lower = tuple(slot.ideal_probability_lower for slot in result.slots)
    upper = tuple(slot.ideal_probability_upper for slot in result.slots)
    assert sum(lower, Fraction(0, 1)) <= 1 <= sum(upper, Fraction(0, 1))
    for lo, truth, hi in zip(lower, ideal, upper):
        assert mpmath.mpf(lo.numerator) / lo.denominator <= truth
        assert truth <= mpmath.mpf(hi.numerator) / hi.denominator
        assert hi - lo < Fraction(1, 1 << 100)

    raw = tuple(slot.retained_float64_weight_exact for slot in result.slots)
    normalized = tuple(
        slot.nonoperational_exact_renormalized_weight for slot in result.slots
    )
    increments = tuple(slot.cdf_increment_probability for slot in result.slots)
    grid = tuple(slot.categorical_53bit_probability for slot in result.slots)
    assert (
        result.ideal_to_retained_float_half_l1_lower,
        result.ideal_to_retained_float_half_l1_upper,
    ) == _interval_half_l1(lower, upper, raw, False)
    assert (
        result.ideal_to_nonoperational_renormalized_tv_lower,
        result.ideal_to_nonoperational_renormalized_tv_upper,
    ) == _interval_half_l1(lower, upper, normalized, True)
    assert (
        result.ideal_to_cdf_tv_lower,
        result.ideal_to_cdf_tv_upper,
    ) == _interval_half_l1(lower, upper, increments, True)
    assert (
        result.ideal_to_categorical_53bit_tv_lower,
        result.ideal_to_categorical_53bit_tv_upper,
    ) == _interval_half_l1(lower, upper, grid, True)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("fixture_id", object(), TypeError),
        ("fixture_id", "T28-AESS", ValueError),
        ("exact_log_scores", [Fraction(0)], TypeError),
        ("exact_log_scores", (True,), TypeError),
        ("retained_float64_weights", [1.0], TypeError),
        ("retained_float64_weights", (1,), TypeError),
        ("retained_float64_weights", (float("nan"),), ValueError),
        ("retained_float64_weights", (float("inf"),), ValueError),
        ("retained_float64_weights", (0.0,), ValueError),
        ("retained_float64_weights", (-0.0,), ValueError),
        ("configuration_sha256s", [_hash("a")], TypeError),
        ("configuration_sha256s", ("bad",), ValueError),
        ("supplied_unverified_kernel_result_sha256", "bad", ValueError),
    ),
)
def test_sir_hostile_input_types_fail_closed(field, value, error) -> None:
    inputs = {
        "fixture_id": "T28-M1-Q",
        "exact_log_scores": (Fraction(0),),
        "retained_float64_weights": (1.0,),
        "configuration_sha256s": (_hash("a"),),
    }
    inputs[field] = value
    with pytest.raises(error):
        predictions.predict_cp59_realized_sir_cloud(**inputs)


def test_sir_length_bit_and_resolution_guards() -> None:
    with pytest.raises(ValueError, match="length"):
        _sir((), ())
    with pytest.raises(ValueError, match="length"):
        _sir(
            (Fraction(0),) * (predictions.CP59_TEST28_MAX_SIR_PARTICLES + 1),
            (1.0,) * (predictions.CP59_TEST28_MAX_SIR_PARTICLES + 1),
        )
    with pytest.raises(ValueError, match="bit bound"):
        _sir((Fraction(1 << 20_000, 1),), (1.0,))
    with pytest.raises(ValueError, match="resolution floor"):
        _sir((Fraction(0), Fraction(-28)))
    with pytest.raises(ValueError, match="shifted weights"):
        _sir((Fraction(0), Fraction(-1_000)), (0.5, 0.5))


def test_sir_parallel_input_lengths_must_match_exactly() -> None:
    with pytest.raises(ValueError, match="length"):
        predictions.predict_cp59_realized_sir_cloud(
            fixture_id="T28-M1-Q",
            exact_log_scores=(Fraction(0), Fraction(0)),
            retained_float64_weights=(0.5,),
            configuration_sha256s=(_hash("a"), _hash("b")),
        )
    with pytest.raises(ValueError, match="length"):
        predictions.predict_cp59_realized_sir_cloud(
            fixture_id="T28-M1-Q",
            exact_log_scores=(Fraction(0), Fraction(0)),
            retained_float64_weights=(0.5, 0.5),
            configuration_sha256s=(_hash("a"),),
        )


def test_sir_rejects_weights_not_matching_independent_normalization_formula() -> None:
    with pytest.raises(ValueError, match="independent frozen normalization formula"):
        _sir((Fraction(0), Fraction(-1)), (0.75, 0.25))


def test_sir_declared_maximum_output_is_bounded_and_exact() -> None:
    count = predictions.CP59_TEST28_MAX_SIR_PARTICLES
    result = _sir((Fraction(0),) * count)
    assert result.particle_count == count
    assert result.retained_float64_weight_sum_exact == 1
    assert result.cdf_increment_sum == 1
    assert result.categorical_53bit_cell_count_sum == _D53
    assert (
        tuple(slot.categorical_53bit_cell_count for slot in result.slots)
        == (_D53 // count,) * count
    )
    encoded = predictions.cp59_canonical_json_bytes(result)
    assert len(encoded) <= predictions.CP59_TEST28_MAX_CANONICAL_JSON_BYTES


def test_sir_claim_flags_remain_false() -> None:
    result = _sir((Fraction(0), Fraction(-1)))
    assert result.supplied_kernel_result_digest_provenance_verified is False
    assert result.numpy_cumsum_executed_by_builder is True
    assert result.independent_normalization_formula_recomputed is True
    assert result.supplied_weights_byte_match_independent_formula is True
    assert result.current_kernel_normalization_helper_invoked is False
    assert result.full_initializer_kernel_executed is False
    assert result.rng_executed is False
    for name in (
        "numpy_transform_law_verified",
        "decimal_implementation_formally_verified",
        "source_law_verified",
        "proposal_iid_verified",
        "resampling_uniform53_verified",
        "unconditional_finite_j_sir_law_derived",
        "sampled_output_provenance_verified",
        "production_observation_authenticated",
        "confirmatory_evidence",
        "formal_test_28_closed",
    ):
        assert getattr(result, name) is False


def test_sir_validator_rejects_redigested_nested_and_summary_tamper() -> None:
    result = _sir((Fraction(0), Fraction(-1)))
    changed_slot = _redigest(
        result.slots[0],
        "realized-sir-slot",
        categorical_53bit_cell_count=result.slots[0].categorical_53bit_cell_count + 1,
    )
    for changes in (
        {"slots": (changed_slot,) + result.slots[1:]},
        {"categorical_53bit_cell_count_sum": True},
        {"retained_float64_weight_sum_exact": Fraction(1, 2)},
        {"numpy_transform_law_verified": True},
        {"supplied_kernel_result_digest_provenance_verified": True},
    ):
        forged = _redigest(result, "realized-sir-cloud", **changes)
        with pytest.raises((TypeError, ValueError)):
            predictions.validate_cp59_realized_sir_cloud_prediction(forged)


def test_sir_validator_rejects_canonically_identical_alien_slot_type() -> None:
    result = _sir((Fraction(0), Fraction(-1)))
    alien = _alien_sealed_clone(result.slots[0])
    if alien is None:
        return
    assert type(alien) is not predictions.RealizedSIRSlotPredictionV1
    assert predictions.cp59_canonical_json_bytes(alien) == (
        predictions.cp59_canonical_json_bytes(result.slots[0])
    )
    forged = _redigest(
        result,
        "realized-sir-cloud",
        slots=(alien,) + result.slots[1:],
    )
    with pytest.raises((TypeError, ValueError)):
        predictions.validate_cp59_realized_sir_cloud_prediction(forged)


def test_sir_validator_exact_type_precedes_hostile_len_protocol() -> None:
    result = _sir((Fraction(0), Fraction(-1)))
    forged = _forge(result, exact_log_scores=_LenBomb())
    with pytest.raises(TypeError, match="exact tuple"):
        predictions.validate_cp59_realized_sir_cloud_prediction(forged)


def test_rejection_quota_alpha_first_accept_exhaustion_and_selected_law() -> None:
    scores = (Fraction(0), Fraction(-1, 3), Fraction(-2, 3))
    probabilities = (Fraction(1, 2), Fraction(1, 3), Fraction(1, 6))
    cap = 4
    result = _rejection(scores, probabilities, cap)
    assert (
        predictions.validate_cp59_conditional_rejection_finite_law_prediction(result)
        is result
    )

    quotas = tuple(_independent_uint64_exp_quota(score) for score in scores)
    p64 = tuple(Fraction(quota, _D64) for quota in quotas)
    joints = tuple(nu * probability for nu, probability in zip(probabilities, p64))
    alpha = sum(joints, Fraction(0))
    selected = tuple(joint / alpha for joint in joints)
    first = tuple((1 - alpha) ** offset * alpha for offset in range(cap))
    exhausted = (1 - alpha) ** cap

    assert tuple(atom.quota for atom in result.atoms) == quotas
    assert tuple(atom.p64 for atom in result.atoms) == p64
    assert (
        tuple(atom.joint_proposal_and_acceptance_probability for atom in result.atoms)
        == joints
    )
    assert tuple(atom.selected_atom_probability for atom in result.atoms) == selected
    assert result.finite_calibration_acceptance_probability == alpha
    assert tuple(
        attempt.all_prior_rejected_probability for attempt in result.attempt_masses
    ) == tuple((1 - alpha) ** offset for offset in range(cap))
    assert (
        tuple(attempt.first_accept_probability for attempt in result.attempt_masses)
        == first
    )
    assert result.selection_within_attempt_cap_probability == sum(first, Fraction(0))
    assert result.exhaustion_probability == exhausted
    assert result.total_probability == sum(first, Fraction(0)) + exhausted == 1
    assert result.selected_atom_probability_sum == sum(selected, Fraction(0)) == 1


def test_rejection_always_accept_and_zero_quota_exhaustion_edges() -> None:
    always = _rejection(
        (Fraction(0), Fraction(0)),
        (Fraction(2, 5), Fraction(3, 5)),
        attempt_cap=3,
    )
    assert tuple(atom.quota for atom in always.atoms) == (_D64, _D64)
    assert always.finite_calibration_acceptance_probability == 1
    assert tuple(
        attempt.first_accept_probability for attempt in always.attempt_masses
    ) == (Fraction(1), Fraction(0), Fraction(0))
    assert always.selection_within_attempt_cap_probability == 1
    assert always.exhaustion_probability == 0
    assert tuple(atom.selected_atom_probability for atom in always.atoms) == (
        Fraction(2, 5),
        Fraction(3, 5),
    )

    never = _rejection((Fraction(-100),), (Fraction(1),), attempt_cap=3)
    assert never.atoms[0].quota == 0
    assert never.finite_calibration_acceptance_probability == 0
    assert never.atoms[0].selected_atom_probability is None
    assert never.selected_atom_probability_sum is None
    assert (
        tuple(attempt.first_accept_probability for attempt in never.attempt_masses)
        == (Fraction(0),) * 3
    )
    assert never.selection_within_attempt_cap_probability == 0
    assert never.exhaustion_probability == 1


def test_rejection_formula_premises_are_not_operational_law_claims() -> None:
    result = _rejection(
        (Fraction(0), Fraction(-1, 3)),
        (Fraction(1, 3), Fraction(2, 3)),
        attempt_cap=2,
    )
    assert result.finite_declared_proposal_law_is_synthetic_calibration is True
    assert result.iid_finite_law_proposals_assumed_for_formula is True
    assert (
        result.abstract_independent_uniform_uint64_decision_words_assumed_for_formula
        is True
    )
    assert result.proposal_decision_independence_assumed_for_formula is True
    assert result.p64_mapping_computed_for_finite_calibration_support is True
    for name in (
        "supplied_kernel_result_digest_provenance_verified",
        "supplied_scores_fixture_membership_verified",
        "configuration_digest_provenance_verified",
        "finite_declared_law_identified_with_mu_fp",
        "operational_decision_word_law_verified",
        "operational_proposal_law_verified",
        "finite_calibration_iid_premise_verified",
        "proposal_decision_independence_verified",
        "operational_alpha64_derived",
        "operational_rho64_derived",
        "operational_refusal_probability_derived",
        "sampled_output_provenance_verified",
        "production_observation_authenticated",
        "confirmatory_evidence",
        "formal_test_28_closed",
    ):
        assert getattr(result, name) is False


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("fixture_id", object(), TypeError),
        ("fixture_id", "T28-AESS", ValueError),
        ("exact_log_scores", [Fraction(0)], TypeError),
        ("exact_log_scores", (True,), TypeError),
        ("exact_upper_bound", 0, TypeError),
        ("proposal_probabilities", [Fraction(1)], TypeError),
        ("proposal_probabilities", (True,), TypeError),
        ("proposal_probabilities", (Fraction(0),), ValueError),
        ("proposal_probabilities", (Fraction(-1),), ValueError),
        ("proposal_probabilities", (Fraction(1, 2),), ValueError),
        ("attempt_cap", True, TypeError),
        ("attempt_cap", 0, ValueError),
        ("attempt_cap", predictions.CP59_TEST28_MAX_REJECTION_ATTEMPTS + 1, ValueError),
        ("configuration_sha256s", [_hash("a")], TypeError),
        ("configuration_sha256s", ("bad",), ValueError),
        ("supplied_unverified_kernel_result_sha256", "bad", ValueError),
    ),
)
def test_rejection_hostile_input_types_fail_closed(field, value, error) -> None:
    inputs = {
        "fixture_id": "T28-M1-Q",
        "exact_log_scores": (Fraction(0),),
        "exact_upper_bound": Fraction(0),
        "proposal_probabilities": (Fraction(1),),
        "attempt_cap": 1,
        "configuration_sha256s": (_hash("a"),),
    }
    inputs[field] = value
    with pytest.raises(error):
        predictions.predict_cp59_conditional_rejection_finite_law(**inputs)


def test_rejection_length_upper_bound_and_fraction_bit_guards() -> None:
    with pytest.raises(ValueError, match="length"):
        _rejection((), (), attempt_cap=1)
    with pytest.raises(ValueError, match="length"):
        _rejection(
            (Fraction(0),) * (predictions.CP59_TEST28_MAX_REJECTION_ATTEMPTS + 1),
            (Fraction(1, predictions.CP59_TEST28_MAX_REJECTION_ATTEMPTS + 1),)
            * (predictions.CP59_TEST28_MAX_REJECTION_ATTEMPTS + 1),
            attempt_cap=1,
        )
    with pytest.raises(ValueError, match="upper bound"):
        _rejection((Fraction(1),), (Fraction(1),), upper=Fraction(0))
    with pytest.raises(ValueError, match="bit bound"):
        _rejection(
            (Fraction(-(1 << 20_000)),),
            (Fraction(1),),
            upper=Fraction(0),
        )


def test_rejection_parallel_lengths_and_common_denominator_guard() -> None:
    with pytest.raises(ValueError, match="length"):
        predictions.predict_cp59_conditional_rejection_finite_law(
            fixture_id="T28-M1-Q",
            exact_log_scores=(Fraction(0), Fraction(0)),
            exact_upper_bound=Fraction(0),
            proposal_probabilities=(Fraction(1),),
            attempt_cap=1,
            configuration_sha256s=(_hash("a"), _hash("b")),
        )
    with pytest.raises(ValueError, match="length"):
        predictions.predict_cp59_conditional_rejection_finite_law(
            fixture_id="T28-M1-Q",
            exact_log_scores=(Fraction(0), Fraction(0)),
            exact_upper_bound=Fraction(0),
            proposal_probabilities=(Fraction(1, 2), Fraction(1, 2)),
            attempt_cap=1,
            configuration_sha256s=(_hash("a"),),
        )

    primes = (
        1009,
        1013,
        1019,
        1021,
        1031,
        1033,
        1039,
        1049,
        1051,
        1061,
        1063,
        1069,
        1087,
        1091,
        1093,
        1097,
        1103,
        1109,
        1117,
        1123,
        1129,
        1151,
        1153,
        1163,
        1171,
        1181,
        1187,
        1193,
        1201,
        1213,
        1217,
        1223,
    )
    probabilities = tuple(
        value
        for prime in primes
        for value in (
            Fraction(1, len(primes) * prime),
            Fraction(prime - 1, len(primes) * prime),
        )
    )
    assert sum(probabilities, Fraction(0)) == 1
    with pytest.raises(ValueError, match="common denominator"):
        _rejection((Fraction(0),) * len(probabilities), probabilities, attempt_cap=1)


def test_rejection_declared_maximum_output_stays_within_resource_bounds() -> None:
    count = predictions.CP59_TEST28_MAX_REJECTION_ATTEMPTS
    scores = tuple(Fraction(-index, count) for index in range(count))
    probabilities = (Fraction(1, count),) * count
    result = _rejection(scores, probabilities, attempt_cap=count)
    assert result.support_size == count
    assert len(result.atoms) == count
    assert len(result.attempt_masses) == count
    _assert_independent_rejection_math(result)
    assert (
        max(
            result.selection_within_attempt_cap_probability.numerator.bit_length(),
            result.selection_within_attempt_cap_probability.denominator.bit_length(),
            result.exhaustion_probability.numerator.bit_length(),
            result.exhaustion_probability.denominator.bit_length(),
        )
        <= predictions.CP59_TEST28_MAX_RESULT_FRACTION_BITS
    )
    encoded = predictions.cp59_canonical_json_bytes(result)
    assert len(encoded) <= predictions.CP59_TEST28_MAX_CANONICAL_JSON_BYTES


def test_rejection_validator_rejects_child_summary_and_claim_tamper() -> None:
    result = _rejection(
        (Fraction(0), Fraction(-1, 3)),
        (Fraction(1, 3), Fraction(2, 3)),
        attempt_cap=2,
    )
    changed_atom = _redigest(
        result.atoms[0],
        "conditional-rejection-atom",
        quota=result.atoms[0].quota - 1,
    )
    changed_attempt = _redigest(
        result.attempt_masses[0],
        "conditional-rejection-attempt-mass",
        first_accept_probability=Fraction(0),
    )
    for changes in (
        {"atoms": (changed_atom,) + result.atoms[1:]},
        {"attempt_masses": (changed_attempt,) + result.attempt_masses[1:]},
        {"support_size": True},
        {"attempt_cap": True},
        {"finite_calibration_acceptance_probability": Fraction(0)},
        {"operational_alpha64_derived": True},
        {"production_observation_authenticated": True},
    ):
        forged = _redigest(result, "conditional-rejection-finite-law", **changes)
        with pytest.raises((TypeError, ValueError)):
            predictions.validate_cp59_conditional_rejection_finite_law_prediction(
                forged
            )


@pytest.mark.parametrize("child_field", ("atoms", "attempt_masses"))
def test_rejection_validator_rejects_canonically_identical_alien_child_type(
    child_field,
) -> None:
    result = _rejection(
        (Fraction(0), Fraction(-1, 3)),
        (Fraction(1, 3), Fraction(2, 3)),
        attempt_cap=2,
    )
    children = getattr(result, child_field)
    alien = _alien_sealed_clone(children[0])
    if alien is None:
        return
    assert alien.__class__ is not children[0].__class__
    assert predictions.cp59_canonical_json_bytes(alien) == (
        predictions.cp59_canonical_json_bytes(children[0])
    )
    forged = _redigest(
        result,
        "conditional-rejection-finite-law",
        **{child_field: (alien,) + children[1:]},
    )
    with pytest.raises((TypeError, ValueError)):
        predictions.validate_cp59_conditional_rejection_finite_law_prediction(forged)


def test_rejection_validator_exact_type_precedes_hostile_protocols() -> None:
    result = _rejection(
        (Fraction(0), Fraction(-1, 3)),
        (Fraction(1, 3), Fraction(2, 3)),
        attempt_cap=2,
    )
    with pytest.raises(TypeError, match="exact tuple"):
        predictions.validate_cp59_conditional_rejection_finite_law_prediction(
            _forge(result, exact_log_scores=_LenBomb())
        )
    with pytest.raises(TypeError, match="exact integer"):
        predictions.validate_cp59_conditional_rejection_finite_law_prediction(
            _forge(result, attempt_cap=_ComparisonBomb())
        )


def test_zero_argument_bundle_binds_all_four_fixture_calibrations() -> None:
    bundle = predictions.cp59_arithmetic_calibration_bundle()
    assert predictions.validate_cp59_arithmetic_calibration_bundle(bundle) is bundle
    assert predictions.cp59_canonical_json_bytes(bundle) == (
        predictions.cp59_canonical_json_bytes(
            predictions.cp59_arithmetic_calibration_bundle()
        )
    )
    assert bundle.source_law_boundary.record_sha256 == (
        predictions.cp59_source_law_boundary().record_sha256
    )
    assert bundle.m1_realized_sir_calibration.fixture_id == "T28-M1-Q"
    assert bundle.m2_realized_sir_calibration.fixture_id == "T28-M2-Q"
    assert tuple(
        child.attempt_cap for child in bundle.m1_conditional_rejection_calibrations
    ) == (1, 4, 16, 64)
    assert tuple(
        child.attempt_cap for child in bundle.m2_conditional_rejection_calibrations
    ) == (1, 4, 16, 64)
    assert all(
        child.fixture_id == "T28-M1-Q"
        for child in bundle.m1_conditional_rejection_calibrations
    )
    assert all(
        child.fixture_id == "T28-M2-Q"
        for child in bundle.m2_conditional_rejection_calibrations
    )
    assert bundle.predeclared_fixture_labeled_calibration_tables_bound is True
    assert bundle.fixture_score_formula_membership_proved_by_record is False
    assert bundle.inputs_are_predeclared_arithmetic_only is True
    assert bundle.independent_normalization_formula_recomputed is True
    assert bundle.kernel_normalization_helper_invoked is False
    for child in (
        bundle.m1_realized_sir_calibration,
        bundle.m2_realized_sir_calibration,
    ):
        assert predictions.validate_cp59_realized_sir_cloud_prediction(child) is child
        assert child.retained_float64_weights == (
            _independent_current_kernel_weights(child.exact_log_scores)
        )
        cdf = tuple(slot.cdf_exact for slot in child.slots)
        assert tuple(slot.categorical_53bit_cell_count for slot in child.slots) == (
            _independent_grid_counts(cdf)
        )
        assert child.supplied_scores_fixture_membership_verified is False
        assert child.production_observation_authenticated is False
    for child in (
        bundle.m1_conditional_rejection_calibrations
        + bundle.m2_conditional_rejection_calibrations
    ):
        assert (
            predictions.validate_cp59_conditional_rejection_finite_law_prediction(child)
            is child
        )
        _assert_independent_rejection_math(child)
        assert child.supplied_scores_fixture_membership_verified is False
        assert child.production_observation_authenticated is False
    for name in (
        "sampler_executed",
        "kernel_owner_or_plan_executed",
        "rng_executed",
        "production_observed",
        "operational_prediction",
        "operational_predictions_blocker_closed",
        "confirmatory_evidence",
        "formal_test_28_closed",
    ):
        assert getattr(bundle, name) is False
    assert bundle.formal_test_28_status == "OPEN"


def test_bundle_validator_rejects_redigested_nested_and_flag_tamper() -> None:
    bundle = predictions.cp59_arithmetic_calibration_bundle()
    changed_child = _redigest(
        bundle.m1_conditional_rejection_calibrations[0],
        "conditional-rejection-finite-law",
        production_observation_authenticated=True,
    )
    for changes in (
        {
            "m1_conditional_rejection_calibrations": (changed_child,)
            + bundle.m1_conditional_rejection_calibrations[1:]
        },
        {"inputs_are_predeclared_arithmetic_only": False},
        {"production_observed": True},
        {"operational_predictions_blocker_closed": True},
    ):
        forged = _redigest(bundle, "arithmetic-calibration-bundle", **changes)
        with pytest.raises((TypeError, ValueError)):
            predictions.validate_cp59_arithmetic_calibration_bundle(forged)


def test_bundle_validator_rejects_canonically_identical_alien_child_type() -> None:
    bundle = predictions.cp59_arithmetic_calibration_bundle()
    alien = _alien_sealed_clone(bundle.m1_realized_sir_calibration)
    if alien is None:
        return
    assert predictions.cp59_canonical_json_bytes(alien) == (
        predictions.cp59_canonical_json_bytes(bundle.m1_realized_sir_calibration)
    )
    forged = _redigest(
        bundle,
        "arithmetic-calibration-bundle",
        m1_realized_sir_calibration=alien,
    )
    with pytest.raises((TypeError, ValueError)):
        predictions.validate_cp59_arithmetic_calibration_bundle(forged)


def test_public_export_names_resolve() -> None:
    assert len(predictions.__all__) == len(set(predictions.__all__))
    for name in predictions.__all__:
        assert hasattr(predictions, name), name


def test_canonical_encoding_binds_exact_scalar_types_and_binary64_bits() -> None:
    result = _sir((Fraction(0),) * 4)
    encoded = predictions.cp59_canonical_json_bytes(result)
    assert b'"cp59_record_type":"realized-sir-cloud-v1"' in encoded
    assert b'"cp59_record_type":"realized-sir-slot-v1"' in encoded
    assert b"cp59_exact_integer_hex" in encoded
    assert b"cp59_exact_fraction_v1" in encoded
    assert b"0x1.0000000000000p-2" in encoded
    for unsupported in (True, 1, Fraction(1), 0.5, -0.0, float("nan"), [1]):
        with pytest.raises(TypeError):
            predictions.cp59_canonical_json_bytes(unsupported)


def test_oversized_text_and_canonical_scalar_payloads_fail_closed() -> None:
    oversized_text = "x" * (predictions.CP59_TEST28_MAX_TEXT_BYTES + 1)
    with pytest.raises(ValueError, match="bounded nonempty text"):
        predictions.predict_cp59_realized_sir_cloud(
            fixture_id=oversized_text,
            exact_log_scores=(Fraction(0),),
            retained_float64_weights=(1.0,),
            configuration_sha256s=(_hash("a"),),
        )
    with pytest.raises(ValueError, match="bounded nonempty text"):
        predictions.predict_cp59_realized_sir_cloud(
            fixture_id="T28-M1-Q",
            exact_log_scores=(Fraction(0),),
            retained_float64_weights=(1.0,),
            configuration_sha256s=(_hash("a"),),
            supplied_unverified_kernel_result_sha256=oversized_text,
        )

    boundary = predictions.cp59_source_law_boundary()
    forged = _forge(
        boundary,
        scope="x" * (predictions.CP59_TEST28_MAX_CANONICAL_SCALAR_BYTES + 1),
    )
    with pytest.raises(ValueError, match="scalar payload"):
        predictions.cp59_canonical_json_bytes(forged)


def test_import_is_lazy_and_does_not_load_numpy_or_process_modules() -> None:
    code = """
import sys
assert 'numpy' not in sys.modules
assert not any(name.startswith('heterodiff.processes') for name in sys.modules)
from heterodiff.evaluation import (
    mixed_initializer_test28_runtime_conditional_predictions,
)
assert 'numpy' not in sys.modules
assert not any(name.startswith('heterodiff.processes') for name in sys.modules)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")},
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_source_ast_has_no_rng_sampler_provider_or_kernel_execution() -> None:
    source_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "heterodiff"
        / "evaluation"
        / "mixed_initializer_test28_runtime_conditional_predictions.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    assert roots <= {
        "__future__",
        "dataclasses",
        "fractions",
        "hashlib",
        "importlib",
        "json",
        "math",
        "platform",
        "sys",
        "typing",
    }
    for forbidden in (
        "default_rng",
        "random_raw(",
        "sample_configuration(",
        "provider.evaluate(",
        "MixedSupportInitialTiltInitializerKernelV2(",
    ):
        assert forbidden not in source
    assert "no-mu-fp-no-iid-no-independence" in source
    assert "no-unconditional" in predictions.CP59_TEST28_RUNTIME_CONDITIONAL_SCOPE


def test_all_public_records_are_sealed_slot_only_and_nonpickleable() -> None:
    boundary = predictions.cp59_source_law_boundary()
    sir = _sir((Fraction(0), Fraction(-1)))
    rejection = _rejection(
        (Fraction(0), Fraction(-1)),
        (Fraction(1, 3), Fraction(2, 3)),
        attempt_cap=2,
    )
    bundle = predictions.cp59_arithmetic_calibration_bundle()
    records = (
        (boundary, sir, rejection, bundle)
        + sir.slots
        + rejection.atoms
        + rejection.attempt_masses
        + (
            bundle.m1_realized_sir_calibration,
            bundle.m2_realized_sir_calibration,
        )
        + bundle.m1_conditional_rejection_calibrations
        + bundle.m2_conditional_rejection_calibrations
    )
    for record in records:
        assert not hasattr(record, "__dict__")
        with pytest.raises(TypeError, match="module-created"):
            type(record)()
        with pytest.raises((TypeError, pickle.PicklingError)):
            pickle.dumps(record)
        with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
            record.hostile_attribute = True
        with pytest.raises(TypeError, match="cannot be subclassed"):
            type("HostileSubclass", (type(record),), {})
