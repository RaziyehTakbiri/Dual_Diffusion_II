from __future__ import annotations

import ast
import math
from pathlib import Path

import numpy as np
import pytest

from heterodiff.evaluation.mixed_ctmc_ou_path_kl_diagnostic import (
    DIAGNOSTIC_SCOPE,
    FORWARD_ORIENTATION,
    NUMERICAL_QUALIFICATION,
    REVERSE_ORIENTATION,
    TerminalMatchedResidual,
    build_mixed_ctmc_ou_path_kl_diagnostic,
    residual_jump_increment,
    residual_spatial_gradient,
    residual_value,
)
from heterodiff.evaluation.mixed_ctmc_ou_known_law_oracle import (
    build_mixed_ctmc_ou_known_law_oracle,
)
from heterodiff.theory.finite_bridge_path_control import tilted_path_kl
from heterodiff.theory.finite_state import transition_matrix


@pytest.fixture(scope="module")
def diagnostic():
    return build_mixed_ctmc_ou_path_kl_diagnostic()


def test_scope_is_explicitly_fixture_only_and_non_promotional(diagnostic) -> None:
    assert diagnostic.scope == DIAGNOSTIC_SCOPE
    assert diagnostic.orientation == FORWARD_ORIENTATION
    assert diagnostic.numerical_qualification == NUMERICAL_QUALIFICATION
    boundary = diagnostic.boundary
    assert boundary.mathematical_path_kl_identity_exact is True
    assert boundary.float_quadrature_interval_certified is False
    assert boundary.adaptive_error_estimate_is_rigorous_bound is False
    assert boundary.fixture_direct_gradient_quantity_exercised is True
    assert boundary.fixture_direct_jump_edge_quantities_exercised is True
    assert boundary.learned_estimator_exercised is False
    assert boundary.association_marginalization_exercised is False
    assert boundary.state_dependent_mark_dimension_exercised is False
    assert boundary.cap_defect_cancellation_exercised is False
    assert boundary.general_c17_theorem_proved is False
    assert boundary.r2_hybrid_completed is False
    assert boundary.claim_promotion_authorized is False
    assert boundary.confirmatory_execution_authorized is False
    assert boundary.production_execution_authorized is False
    assert diagnostic.state_vectors == (
        (0, 0),
        (0, 1),
        (1, 0),
        (0, 2),
        (1, 1),
        (2, 0),
    )
    controls = diagnostic.numerical_controls
    assert controls.adaptive_absolute_tolerance == 1.0e-11
    assert controls.adaptive_relative_tolerance == 1.0e-11
    assert controls.adaptive_maximum_subdivisions == 200
    assert controls.gauss_legendre_order == 96
    assert controls.reverse_ode_relative_tolerance == 2.0e-11
    assert controls.reverse_ode_absolute_tolerance == 2.0e-13


def test_source_does_not_reuse_public_path_kl_oracle() -> None:
    source_path = (
        Path(__file__).resolve().parents[2]
        / "src/heterodiff/evaluation/mixed_ctmc_ou_path_kl_diagnostic.py"
    )
    tree = ast.parse(source_path.read_text("utf-8"))
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "heterodiff.theory.finite_bridge_path_control" not in imported_names
    assert "tilted_path_kl" not in imported_names
    assert "tilted_path_kl" not in called_names


def test_default_residual_is_nonzero_but_terminal_matched(diagnostic) -> None:
    residual = diagnostic.residual
    horizon = 0.8
    assert residual.non_gauge_perturbation_nonzero is True
    assert diagnostic.terminal_residual_exactly_zero is True
    assert (
        residual_value(
            residual,
            time=0.0,
            state_index=2,
            coordinate=0.7,
            horizon=horizon,
        )
        != 0.0
    )
    for state_index in range(6):
        assert (
            residual_value(
                residual,
                time=horizon,
                state_index=state_index,
                coordinate=-3.1,
                horizon=horizon,
            )
            == 0.0
        )
        assert (
            residual_jump_increment(
                residual,
                time=horizon,
                source=0,
                destination=state_index,
                horizon=horizon,
            )
            == 0.0
        )
    assert residual_spatial_gradient(residual, time=horizon, horizon=horizon) == 0.0


def test_exact_to_plugin_decomposition_is_positive_and_additive(diagnostic) -> None:
    decomposition = diagnostic.decomposition
    initializer = decomposition.initializer
    jumps = decomposition.jumps

    assert initializer.discrete_exact_to_plugin > 0.0
    assert initializer.ou_exact_to_plugin > 0.0
    assert initializer.total_exact_to_plugin == pytest.approx(
        initializer.discrete_exact_to_plugin + initializer.ou_exact_to_plugin,
        rel=0.0,
        abs=2.0e-15,
    )
    assert decomposition.ou_continuous_gradient > 0.0
    assert jumps.birth > 0.0
    assert jumps.death > 0.0
    assert jumps.replacement > 0.0
    assert (jumps.birth, jumps.death, jumps.replacement) == pytest.approx(
        (
            0.029135431076622087,
            0.016340611640645607,
            0.04403186747022539,
        ),
        rel=0.0,
        abs=2.0e-14,
    )
    assert jumps.total == pytest.approx(
        jumps.birth + jumps.death + jumps.replacement,
        rel=0.0,
        abs=2.0e-15,
    )
    assert decomposition.dynamic == pytest.approx(
        decomposition.ou_continuous_gradient + jumps.total,
        rel=0.0,
        abs=2.0e-15,
    )
    assert decomposition.total == pytest.approx(
        initializer.total_exact_to_plugin + decomposition.dynamic,
        rel=0.0,
        abs=2.0e-15,
    )
    assert jumps.total_quadrature_error_estimate == pytest.approx(
        jumps.birth_quadrature_error_estimate
        + jumps.death_quadrature_error_estimate
        + jumps.replacement_quadrature_error_estimate,
        rel=0.0,
        abs=2.0e-30,
    )


def test_initializer_and_ou_gradient_terms_have_direct_closed_forms(
    diagnostic,
) -> None:
    initializer = diagnostic.decomposition.initializer
    exact = initializer.exact_discrete_probabilities
    plugin = initializer.plugin_discrete_probabilities
    direct_discrete = math.fsum(
        float(probability) * (math.log(float(probability)) - math.log(float(candidate)))
        for probability, candidate in zip(exact, plugin)
    )
    assert initializer.discrete_exact_to_plugin == pytest.approx(
        direct_discrete, rel=0.0, abs=2.0e-15
    )
    expected_ou_initializer = (
        0.5 * initializer.shared_ou_variance * diagnostic.residual.continuous_slope**2
    )
    assert initializer.ou_exact_to_plugin == pytest.approx(
        expected_ou_initializer, rel=0.0, abs=2.0e-15
    )
    assert initializer.plugin_ou_mean == pytest.approx(
        initializer.exact_ou_mean
        + initializer.shared_ou_variance * diagnostic.residual.continuous_slope,
        rel=0.0,
        abs=2.0e-15,
    )
    expected_gradient = 0.7**2 * diagnostic.residual.continuous_slope**2 * 0.8 / 6.0
    assert diagnostic.decomposition.ou_continuous_gradient == pytest.approx(
        expected_gradient, rel=0.0, abs=2.0e-15
    )


def test_zero_perturbation_has_zero_path_kl_and_same_initializer() -> None:
    zero = build_mixed_ctmc_ou_path_kl_diagnostic(
        residual=TerminalMatchedResidual(
            discrete_scale=0.0,
            continuous_slope=0.0,
            gauge_scale=0.0,
        )
    )
    components = zero.decomposition
    assert zero.residual.non_gauge_perturbation_nonzero is False
    assert components.initializer.discrete_exact_to_plugin == pytest.approx(
        0.0, rel=0.0, abs=2.0e-16
    )
    assert components.initializer.ou_exact_to_plugin == 0.0
    assert components.ou_continuous_gradient == 0.0
    assert components.jumps.birth == 0.0
    assert components.jumps.death == 0.0
    assert components.jumps.replacement == 0.0
    assert components.total == pytest.approx(0.0, rel=0.0, abs=2.0e-16)
    assert zero.reverse_orientation.total == pytest.approx(0.0, rel=0.0, abs=2.0e-16)
    assert zero.orientation_totals_distinct is False
    np.testing.assert_allclose(
        components.initializer.exact_discrete_probabilities,
        components.initializer.plugin_discrete_probabilities,
        rtol=0.0,
        atol=2.0e-16,
    )


def test_state_independent_gauge_changes_raw_e_but_not_any_kl_component() -> None:
    first = build_mixed_ctmc_ou_path_kl_diagnostic(
        residual=TerminalMatchedResidual(gauge_scale=-3.5)
    )
    second = build_mixed_ctmc_ou_path_kl_diagnostic(
        residual=TerminalMatchedResidual(gauge_scale=9.25)
    )
    first_value = residual_value(
        first.residual,
        time=0.25,
        state_index=3,
        coordinate=0.4,
        horizon=0.8,
    )
    second_value = residual_value(
        second.residual,
        time=0.25,
        state_index=3,
        coordinate=0.4,
        horizon=0.8,
    )
    assert first_value != second_value
    assert first.decomposition.ou_continuous_gradient == (
        second.decomposition.ou_continuous_gradient
    )
    assert first.decomposition.jumps == second.decomposition.jumps
    assert first.decomposition.total == second.decomposition.total
    assert first.reverse_orientation.total == second.reverse_orientation.total
    assert first.crosscheck.total == second.crosscheck.total
    np.testing.assert_array_equal(
        first.decomposition.initializer.plugin_discrete_probabilities,
        second.decomposition.initializer.plugin_discrete_probabilities,
    )


def test_reverse_orientation_is_computed_separately_and_is_not_substitutable(
    diagnostic,
) -> None:
    reverse = diagnostic.reverse_orientation
    forward = diagnostic.decomposition
    assert reverse.orientation == REVERSE_ORIENTATION
    assert reverse.plugin_final_probability_mass_residual < 1.0e-10
    assert reverse.initializer == pytest.approx(
        forward.initializer.total_plugin_to_exact, rel=0.0, abs=0.0
    )
    assert reverse.dynamic == pytest.approx(
        reverse.ou_continuous_gradient
        + reverse.birth
        + reverse.death
        + reverse.replacement,
        rel=0.0,
        abs=2.0e-15,
    )
    assert reverse.total == pytest.approx(
        reverse.initializer + reverse.dynamic, rel=0.0, abs=2.0e-15
    )
    assert diagnostic.orientation_totals_distinct is True
    assert reverse.total != pytest.approx(forward.total, rel=1.0e-6, abs=1.0e-8)
    assert reverse.birth > 0.0
    assert reverse.death > 0.0
    assert reverse.replacement > 0.0


def test_independent_fixed_quadrature_crosscheck_agrees_without_certifying(
    diagnostic,
) -> None:
    crosscheck = diagnostic.crosscheck
    jumps = diagnostic.decomposition.jumps
    assert crosscheck.method == (
        "FIXED_GAUSS_LEGENDRE_WITH_DIRECT_POISSON_RATE_KL_AND_DIRECT_INITIAL_KL"
    )
    assert crosscheck.applied_to_any_gate_or_claim_decision is False
    assert crosscheck.initializer_direct_kl == pytest.approx(
        diagnostic.decomposition.initializer.total_exact_to_plugin,
        rel=0.0,
        abs=2.0e-15,
    )
    assert crosscheck.birth_direct_poisson == pytest.approx(
        jumps.birth, rel=0.0, abs=2.0e-12
    )
    assert crosscheck.death_direct_poisson == pytest.approx(
        jumps.death, rel=0.0, abs=2.0e-12
    )
    assert crosscheck.replacement_direct_poisson == pytest.approx(
        jumps.replacement, rel=0.0, abs=2.0e-12
    )
    assert crosscheck.total == pytest.approx(
        diagnostic.decomposition.total, rel=0.0, abs=5.0e-12
    )
    assert crosscheck.absolute_difference_from_adaptive_total < 5.0e-12
    assert diagnostic.boundary.float_quadrature_interval_certified is False


def test_independent_public_finite_bridge_oracle_matches_discrete_components(
    diagnostic,
) -> None:
    oracle = build_mixed_ctmc_ou_known_law_oracle()
    discrete = oracle.discrete
    horizon = oracle.continuous.parameters.horizon
    residual = diagnostic.residual
    potentials = np.asarray(residual.state_potentials, dtype=np.float64)

    def exact_information(time: float) -> np.ndarray:
        return transition_matrix(discrete.generator, horizon - time) @ (
            discrete.terminal_likelihood
        )

    def plugin_information(time: float) -> np.ndarray:
        envelope = 1.0 - time / horizon
        return exact_information(time) * np.exp(
            envelope * residual.discrete_scale * potentials
        )

    public = tilted_path_kl(
        discrete.initial_probabilities,
        discrete.generator,
        exact_information,
        plugin_information,
        horizon,
        rtol=2.0e-11,
        atol=2.0e-13,
        max_step=horizon / 128.0,
        quadrature_epsabs=2.0e-11,
        quadrature_epsrel=2.0e-11,
        quadrature_limit=2_000,
    )
    expected_initial = diagnostic.decomposition.initializer.discrete_exact_to_plugin
    expected_dynamic = diagnostic.decomposition.jumps.total
    assert public.initial == pytest.approx(expected_initial, rel=0.0, abs=3.0e-12)
    assert public.dynamic == pytest.approx(expected_dynamic, rel=0.0, abs=3.0e-11)
    assert public.total == pytest.approx(
        expected_initial + expected_dynamic, rel=0.0, abs=3.0e-11
    )


def test_public_probability_arrays_are_read_only(diagnostic) -> None:
    initializer = diagnostic.decomposition.initializer
    for probabilities in (
        initializer.exact_discrete_probabilities,
        initializer.plugin_discrete_probabilities,
    ):
        assert probabilities.flags.writeable is False
        assert float(np.sum(probabilities)) == pytest.approx(1.0, rel=0.0, abs=2.0e-15)
        with pytest.raises(ValueError):
            probabilities[0] = 0.0


def test_inputs_fail_closed() -> None:
    with pytest.raises(TypeError, match="non-boolean"):
        TerminalMatchedResidual(discrete_scale=True)
    with pytest.raises(TypeError, match="tuple"):
        TerminalMatchedResidual(state_potentials=[0.0] * 6)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="six"):
        TerminalMatchedResidual(state_potentials=(0.0,))
    with pytest.raises(ValueError, match="finite"):
        TerminalMatchedResidual(continuous_slope=math.nan)
    with pytest.raises(TypeError, match="TerminalMatchedResidual"):
        build_mixed_ctmc_ou_path_kl_diagnostic(residual=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="non-boolean"):
        build_mixed_ctmc_ou_path_kl_diagnostic(quadrature_absolute_tolerance=True)
    with pytest.raises(ValueError, match="greater than"):
        build_mixed_ctmc_ou_path_kl_diagnostic(quadrature_relative_tolerance=0.0)
    with pytest.raises(TypeError, match="integer non-boolean"):
        build_mixed_ctmc_ou_path_kl_diagnostic(quadrature_subdivisions=False)
    with pytest.raises(ValueError, match="between"):
        build_mixed_ctmc_ou_path_kl_diagnostic(gauss_legendre_order=7)
    with pytest.raises(ValueError, match="finite diagnostic limit"):
        build_mixed_ctmc_ou_path_kl_diagnostic(
            residual=TerminalMatchedResidual(discrete_scale=1.0e6)
        )

    residual = TerminalMatchedResidual()
    with pytest.raises(ValueError, match="closed diagnostic horizon"):
        residual_value(
            residual,
            time=0.9,
            state_index=0,
            coordinate=0.0,
            horizon=0.8,
        )
    with pytest.raises(ValueError, match="between"):
        residual_jump_increment(
            residual,
            time=0.0,
            source=0,
            destination=6,
            horizon=0.8,
        )
    with pytest.raises(ValueError, match="finite"):
        residual_value(
            residual,
            time=0.0,
            state_index=0,
            coordinate=math.inf,
            horizon=0.8,
        )
    with pytest.raises(TypeError, match="TerminalMatchedResidual"):
        residual_spatial_gradient(object(), time=0.0, horizon=0.8)  # type: ignore[arg-type]
