from __future__ import annotations

import math

import numpy as np
import pytest

from heterodiff.evaluation.mixed_ctmc_ou_known_law_oracle import (
    CLAIM_PROMOTION_EFFECT,
    DIAGNOSTIC_TOLERANCE_ROLE,
    ORACLE_SCOPE,
    OUParameters,
    build_mixed_ctmc_ou_known_law_oracle,
    ou_backward_information,
    ou_conditioned_drift,
    ou_log_backward_information,
    ou_log_information_gradient,
    uniformization_transition,
)
from heterodiff.theory.finite_state import transition_matrix


@pytest.fixture(scope="module")
def oracle():
    return build_mixed_ctmc_ou_known_law_oracle()


def _positive_edges(matrix: np.ndarray):
    for source in range(matrix.shape[0]):
        for destination in range(matrix.shape[1]):
            if source != destination and matrix[source, destination] > 0.0:
                yield source, destination


def test_fixture_is_small_mixed_and_fail_closed(oracle) -> None:
    assert oracle.scope == ORACLE_SCOPE
    assert oracle.factorized_reference_process is True
    assert oracle.factorized_terminal_likelihood is True
    assert oracle.discrete.state_vectors == (
        (0, 0),
        (0, 1),
        (1, 0),
        (0, 2),
        (1, 1),
        (2, 0),
    )
    assert oracle.mixed_evidence == pytest.approx(
        oracle.discrete.evidence * oracle.continuous.evidence,
        rel=0.0,
        abs=0.0,
    )

    diagnostics = oracle.diagnostics
    assert diagnostics.tolerance_role == DIAGNOSTIC_TOLERANCE_ROLE
    assert diagnostics.absolute_tolerance_applied_to_any_decision is False
    assert diagnostics.uniformization_certificate_scope == (
        "ANALYTIC_POISSON_TRUNCATION_TAIL_WITH_SEPARATE_FLOATING_ROUNDOFF"
    )
    assert diagnostics.claim_promotion_effect == CLAIM_PROMOTION_EFFECT == "NONE"
    assert diagnostics.claim_promotion_authorized is False
    assert diagnostics.production_execution_authorized is False
    assert diagnostics.closes_mixed_known_law_gate is False
    assert diagnostics.candidate_residual_exercised is False
    assert diagnostics.path_kl_decomposition_exercised is False
    assert diagnostics.cap_defect_cancellation_exercised is False
    assert diagnostics.association_marginalization_exercised is False
    assert diagnostics.continuous_marks_attached_to_occurrences is False
    assert diagnostics.c17_exercised is False


def test_all_three_jump_families_are_nonempty_and_have_exact_count_changes(
    oracle,
) -> None:
    states = oracle.discrete.state_vectors
    components = (
        (oracle.discrete.birth_generator, 1, oracle.discrete.birth_edge_count),
        (oracle.discrete.death_generator, -1, oracle.discrete.death_edge_count),
        (
            oracle.discrete.replacement_generator,
            0,
            oracle.discrete.replacement_edge_count,
        ),
    )
    for component, total_change, declared_count in components:
        edges = tuple(_positive_edges(component))
        assert len(edges) == declared_count == 6
        for source, destination in edges:
            difference = tuple(
                target - origin
                for origin, target in zip(states[source], states[destination])
            )
            assert sum(difference) == total_change
            if total_change == 1:
                assert sorted(difference) == [0, 1]
            elif total_change == -1:
                assert sorted(difference) == [-1, 0]
            else:
                assert sorted(difference) == [-1, 1]

    combined = (
        oracle.discrete.birth_generator
        + oracle.discrete.death_generator
        + oracle.discrete.replacement_generator
    )
    np.testing.assert_array_equal(oracle.discrete.generator, combined)
    np.testing.assert_allclose(
        oracle.discrete.generator.sum(axis=1), 0.0, rtol=0.0, atol=1.0e-15
    )


def test_uniformization_has_an_explicit_tail_envelope(oracle) -> None:
    certificate = oracle.discrete.uniformization
    exact = transition_matrix(
        oracle.discrete.generator, oracle.continuous.parameters.horizon
    )
    lower = certificate.transition_lower
    allowance = certificate.roundoff_allowance
    assert certificate.poisson_tail_bound <= (
        oracle.diagnostics.uniformization_tail_tolerance
    )
    assert certificate.term_count == certificate.final_poisson_index + 1
    assert np.all(exact >= lower - allowance)
    assert np.all(exact <= lower + certificate.poisson_tail_bound + allowance)
    np.testing.assert_allclose(
        certificate.row_mass_deficit,
        certificate.poisson_tail_bound,
        rtol=0.0,
        atol=allowance,
    )


def test_uniformization_fails_closed_before_poisson_seed_underflow() -> None:
    fast_generator = np.asarray(
        [[-1000.0, 1000.0], [1000.0, -1000.0]], dtype=np.float64
    )
    with pytest.raises(ArithmeticError, match="Poisson weight"):
        uniformization_transition(
            fast_generator,
            1.0,
            tail_tolerance=1.0e-12,
        )


def test_discrete_h_tilted_initializer_endpoints_and_paths_agree(oracle) -> None:
    discrete = oracle.discrete
    np.testing.assert_allclose(
        discrete.initial_probabilities.sum(), 1.0, rtol=0.0, atol=1.0e-15
    )
    np.testing.assert_allclose(
        discrete.tilted_initial_probabilities.sum(),
        1.0,
        rtol=0.0,
        atol=1.0e-15,
    )
    np.testing.assert_allclose(
        discrete.conditional_terminal_probabilities.sum(),
        1.0,
        rtol=0.0,
        atol=1.0e-15,
    )
    expected_initial = (
        discrete.initial_probabilities
        * discrete.backward_information_at_zero
        / discrete.evidence
    )
    np.testing.assert_allclose(
        discrete.tilted_initial_probabilities,
        expected_initial,
        rtol=2.0e-15,
        atol=2.0e-15,
    )
    assert discrete.enumerated_path_count == 84
    assert discrete.maximum_path_log_ratio_residual < 1.0e-12
    assert discrete.backward_equation_residual < 1.0e-8
    assert discrete.endpoint_ode_l1_residual < 1.0e-9


def test_ou_h_gradient_and_doob_drift_are_analytic(oracle) -> None:
    parameters = oracle.continuous.parameters
    time = 0.31 * parameters.horizon
    coordinate = 0.27
    step = 1.0e-6
    finite_difference = (
        math.log(ou_backward_information(parameters, time, coordinate + step))
        - math.log(ou_backward_information(parameters, time, coordinate - step))
    ) / (2.0 * step)
    gradient = ou_log_information_gradient(parameters, time, coordinate)
    assert gradient == pytest.approx(finite_difference, rel=0.0, abs=2.0e-10)
    base_drift = -parameters.mean_reversion * (coordinate - parameters.long_run_mean)
    expected = base_drift + parameters.diffusion**2 * gradient
    assert ou_conditioned_drift(parameters, time, coordinate) == pytest.approx(
        expected, rel=0.0, abs=2.0e-15
    )
    assert expected != pytest.approx(base_drift, rel=0.0, abs=1.0e-6)


def test_ou_log_information_preserves_positive_tail_semantics(oracle) -> None:
    parameters = oracle.continuous.parameters
    direct_time = 0.2
    coordinate = 50.0
    log_information = ou_log_backward_information(parameters, direct_time, coordinate)
    assert math.isfinite(log_information)
    assert log_information < math.log(float(np.finfo(np.float64).tiny))
    with pytest.raises(ArithmeticError, match="not representable"):
        ou_backward_information(parameters, direct_time, coordinate)


def test_ou_tilted_initializer_endpoint_and_path_moments_agree(oracle) -> None:
    continuous = oracle.continuous
    parameters = continuous.parameters
    decay = math.exp(-parameters.mean_reversion * parameters.horizon)
    transition_variance = (
        parameters.diffusion**2
        * -math.expm1(-2.0 * parameters.mean_reversion * parameters.horizon)
        / (2.0 * parameters.mean_reversion)
    )
    base_terminal_mean = parameters.long_run_mean + decay * (
        parameters.initial_mean - parameters.long_run_mean
    )
    base_terminal_variance = (
        decay**2 * parameters.initial_variance + transition_variance
    )
    observation_total_variance = (
        base_terminal_variance + parameters.observation_variance
    )
    expected_terminal_mean = base_terminal_mean + (
        base_terminal_variance
        / observation_total_variance
        * (parameters.observation_value - base_terminal_mean)
    )
    expected_terminal_variance = (
        base_terminal_variance
        - base_terminal_variance**2 / observation_total_variance
    )
    expected_initial_mean = parameters.initial_mean + (
        parameters.initial_variance
        * decay
        / observation_total_variance
        * (parameters.observation_value - base_terminal_mean)
    )
    expected_initial_variance = (
        parameters.initial_variance
        - (parameters.initial_variance * decay) ** 2 / observation_total_variance
    )

    assert continuous.evidence > 0.0
    assert continuous.tilted_initial_mean == pytest.approx(
        expected_initial_mean, rel=0.0, abs=2.0e-15
    )
    assert continuous.tilted_initial_variance == pytest.approx(
        expected_initial_variance, rel=0.0, abs=2.0e-15
    )
    assert continuous.conditional_terminal_mean == pytest.approx(
        expected_terminal_mean, rel=0.0, abs=2.0e-15
    )
    assert continuous.conditional_terminal_variance == pytest.approx(
        expected_terminal_variance, rel=0.0, abs=2.0e-15
    )
    assert continuous.endpoint_ode_mean_residual < 1.0e-9
    assert continuous.endpoint_ode_variance_residual < 1.0e-9
    assert continuous.maximum_moment_dynamics_residual < 1.0e-12
    assert continuous.maximum_backward_pde_residual < 1.0e-8


def test_diagnostic_tolerance_does_not_change_the_known_law() -> None:
    tight = build_mixed_ctmc_ou_known_law_oracle(diagnostic_absolute_tolerance=1.0e-12)
    loose = build_mixed_ctmc_ou_known_law_oracle(diagnostic_absolute_tolerance=1.0e-3)
    assert tight.diagnostics.absolute_tolerance == 1.0e-12
    assert loose.diagnostics.absolute_tolerance == 1.0e-3
    np.testing.assert_array_equal(tight.discrete.generator, loose.discrete.generator)
    np.testing.assert_array_equal(
        tight.discrete.conditional_terminal_probabilities,
        loose.discrete.conditional_terminal_probabilities,
    )
    assert tight.continuous.parameters == loose.continuous.parameters
    assert tight.continuous.evidence == loose.continuous.evidence
    assert (
        tight.continuous.maximum_moment_dynamics_residual
        == loose.continuous.maximum_moment_dynamics_residual
    )


def test_public_arrays_are_read_only_and_inputs_fail_closed(oracle) -> None:
    for array in (
        oracle.discrete.generator,
        oracle.discrete.initial_probabilities,
        oracle.discrete.tilted_initial_probabilities,
        oracle.discrete.conditional_terminal_probabilities,
        oracle.discrete.uniformization.transition_lower,
    ):
        assert array.flags.writeable is False
        with pytest.raises(ValueError):
            array.flat[0] = 0.0

    with pytest.raises(TypeError, match="non-boolean"):
        build_mixed_ctmc_ou_known_law_oracle(diagnostic_absolute_tolerance=True)
    with pytest.raises(ValueError, match="smaller than one"):
        build_mixed_ctmc_ou_known_law_oracle(uniformization_tail_tolerance=1.0)
    with pytest.raises(RuntimeError, match="maximum_terms"):
        uniformization_transition(
            oracle.discrete.generator,
            oracle.continuous.parameters.horizon,
            tail_tolerance=1.0e-30,
            maximum_terms=1,
        )
    with pytest.raises(ValueError, match="time must not exceed"):
        ou_backward_information(
            oracle.continuous.parameters,
            oracle.continuous.parameters.horizon + 0.1,
            0.0,
        )
    with pytest.raises(TypeError, match="OUParameters"):
        ou_conditioned_drift(object(), 0.0, 0.0)
    with pytest.raises(ValueError, match="greater than"):
        OUParameters(
            mean_reversion=0.0,
            long_run_mean=0.0,
            diffusion=1.0,
            initial_mean=0.0,
            initial_variance=1.0,
            observation_value=0.0,
            observation_variance=1.0,
            horizon=1.0,
        )
