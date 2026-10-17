"""Independent Gaussian/CTMC checks of the actual common-grid BASE target."""

from dataclasses import replace
import ast
import inspect
import math

import numpy as np
from numpy.polynomial.hermite import hermgauss
import pytest
from scipy.integrate import quad
from scipy.stats import norm, poisson

from heterodiff.evaluation.continuous_fiber_conditional_benchmark import (
    ContinuousFiberConditionalBenchmark, ContinuousFiberSpec,
)
from heterodiff.evaluation.continuous_fiber_grid_target import ContinuousFiberGridTarget, GridTarget


def _grid(count):
    return tuple(i / count for i in range(count + 1))


@pytest.fixture(params=[(.8, .7), (2.5, 1.4)])
def target(request):
    theta, y = request.param
    return GridTarget(ContinuousFiberSpec(theta=theta, observation_value=y), _grid(8))


def _quadrature(function):
    result, error = quad(function, -np.inf, np.inf, epsabs=2e-12, epsrel=2e-12, limit=200)
    assert error < 2e-10
    return result


def _uniformization(spec, duration):
    # Construct rates separately from the oracle and sum the Poisson number
    # of potential transitions; this is independent of scipy.linalg.expm.
    theta, death = spec.theta, spec.death_rate
    other, selected = spec.type_probabilities
    q = np.array([[-theta * death, theta * death * other, theta * death * selected],
                  [death, -death, 0.], [death, 0., -death]])
    rate = max(theta * death, death)
    if rate == 0:
        return np.eye(3)
    chain = np.eye(3) + q / rate
    power, result = np.eye(3), np.zeros((3, 3))
    for count in range(160):
        result += poisson.pmf(count, rate * duration) * power
        power = power @ chain
    return result


def _heun_direct(x, noise, duration, rate):
    # Predictor/corrector equations themselves, not the implementation's
    # expanded affine-coefficient formula.
    drift = -.5 * rate * x
    predictor = x + duration * drift + math.sqrt(rate) * noise
    return x + .5 * duration * (drift - .5 * rate * predictor) + math.sqrt(rate) * noise


def test_short_name_alias_and_independence_of_production_implementation():
    assert GridTarget is ContinuousFiberGridTarget
    tree = ast.parse(inspect.getsource(inspect.getmodule(GridTarget)))
    imported = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert not any(module and any(token in module for token in ('sampler', 'training', 'association_guide')) for module in imported)


@pytest.mark.parametrize('state,coordinate', [('EMPTY', None), ('OTHER', None), ('CONTINUOUS', -2.), ('CONTINUOUS', .7)])
def test_terminal_likelihood_and_derivatives_are_actual_observation_channel(target, state, coordinate):
    exact = ContinuousFiberConditionalBenchmark(target.spec)
    assert target.log_likelihood_derivatives(1., state, coordinate) == pytest.approx(
        exact.log_likelihood_derivatives(1., state, coordinate), rel=3e-14, abs=2e-15)
    # Contamination draws raw N(0,1), never N(0,1+sigma^2).
    expected_reference = math.exp(-1) * target.spec.type_probabilities[1] * norm.pdf(target.spec.observation_value)
    assert target.observation_reference_density == pytest.approx(expected_reference, rel=2e-15)


def test_halfstep_gaussian_coefficients_match_direct_predictor_corrector():
    p = ContinuousFiberSpec(continuous_rate=1.7, death_rate=.4)
    target = GridTarget(p, (0., .15, .4, 1.))
    for time in target.grid[:-1]:
        step = target.step_parameters(time)
        for side, duration in [('left', step['midpoint'] - time), ('right', step['end'] - step['midpoint'])]:
            coefficient = _heun_direct(1., 0., duration, p.continuous_rate)
            noise_gain = _heun_direct(0., math.sqrt(duration), duration, p.continuous_rate)
            assert step[side + '_coefficient'] == pytest.approx(coefficient, abs=3e-16)
            assert step[side + '_variance'] == pytest.approx(noise_gain ** 2, abs=2e-16)
        assert step['reset_variance'] == pytest.approx(step['right_coefficient'] ** 2 + step['right_variance'])
        assert step['survivor_variance'] == pytest.approx(step['right_coefficient'] ** 2 * step['left_variance'] + step['right_variance'])


def test_native_heun_explicit_increment_matches_independent_affine_map():
    # A deterministic coefficient cross-check only: no sampled trajectories,
    # optimizer, endpoint draws or native target are used here.
    from heterodiff.data.two_domain_factorized_state import FactoredEvent, PhysioStateKey
    from heterodiff.processes.factorized_hybrid_sampler import heun_step

    class Zero:
        upper_value_bound = 0.

        def value_grad(self, u, state):
            return 0., tuple((0.,) if event.key.dimension else () for event in state)

    key = PhysioStateKey(3, 'HR', 'POSITIVE')
    p = ContinuousFiberSpec(continuous_rate=1.7)
    target = GridTarget(p, (0., .15, 1.))
    step = target.step_parameters(0.)
    duration = step['midpoint']
    state = (FactoredEvent(key, -.8),)
    brownian = .13
    actual = heun_step(state, 0., duration, Zero(), p.continuous_rate, ((brownian,),))
    expected = step['left_coefficient'] * -.8 + math.sqrt(step['left_variance'] / duration) * brownian
    assert actual[0].coordinate == pytest.approx(expected, abs=3e-16)


def test_category_kernel_and_ancestry_match_independent_uniformization(target):
    for time, end in zip(target.grid, target.grid[1:]):
        transition = target.step_transition(time)
        assert np.allclose(transition, _uniformization(target.spec, end - time), rtol=0., atol=4e-16)
        assert np.allclose(transition.sum(axis=1), 1., rtol=0., atol=4e-16)
        assert np.allclose(target.initial_state_probabilities @ transition, target.initial_state_probabilities, rtol=0., atol=2e-16)
        params = target.step_parameters(time)
        assert params['reset_probabilities'][2] + params['survival_probability'] == pytest.approx(transition[2, 2], abs=3e-16)


@pytest.mark.parametrize('state,coordinate', [('EMPTY', None), ('OTHER', None), ('CONTINUOUS', -.4)])
def test_macro_joint_continuous_density_normalizes(target, state, coordinate):
    mass = _quadrature(lambda x: target.step_continuous_density(0., state, coordinate, x))
    assert mass == pytest.approx(target.step_transition(0.)[target.states.index(state), 2], rel=2e-12)


@pytest.mark.parametrize('state,coordinate', [('EMPTY', None), ('OTHER', None), ('CONTINUOUS', -.4), ('CONTINUOUS', 1.2)])
def test_one_step_likelihood_matches_separate_gaussian_predictor_corrector_quadrature(state, coordinate):
    p = ContinuousFiberSpec(theta=2.5, observation_value=1.4, continuous_rate=1.3)
    target = GridTarget(p, (0., 1.))
    roots, weights = hermgauss(64)
    nodes, weights = np.sqrt(2) * roots, weights / math.sqrt(math.pi)
    z1, z2 = nodes[:, None], nodes[None, :]
    pair_weights = weights[:, None] * weights[None, :]
    transition = _uniformization(p, 1.)
    survival = math.exp(-p.death_rate)
    half = .5
    # A new mark drawn during jumps is untouched during that whole jump phase.
    reset_final = _heun_direct(z1, math.sqrt(half) * z2, half, p.continuous_rate)
    reset_density = np.sum(pair_weights * norm.pdf(p.observation_value, reset_final, p.observation_sd))
    index = target.states.index(state)
    clean = transition[index, 2] * reset_density
    if state == 'CONTINUOUS':
        first = _heun_direct(coordinate, math.sqrt(half) * z1, half, p.continuous_rate)
        final = _heun_direct(first, math.sqrt(half) * z2, half, p.continuous_rate)
        survivor_density = np.sum(pair_weights * norm.pdf(p.observation_value, final, p.observation_sd))
        clean += survival * (survivor_density - reset_density)
    expected = p.contamination * target.observation_reference_density + (1 - p.contamination) * .5 * clean
    assert target.backward_likelihood(0., state, coordinate) == pytest.approx(expected, rel=2e-11, abs=2e-13)


@pytest.mark.parametrize('time,state,coordinate', [(0., 'EMPTY', None), (.25, 'OTHER', None), (.5, 'CONTINUOUS', -.8), (.875, 'CONTINUOUS', 1.2)])
def test_backward_harmonic_recursion_and_discrete_doob_normalization(target, time, state, coordinate):
    next_time = target.grid[target.grid.index(time) + 1]
    row = target.step_transition(time)[target.states.index(state)]
    atom_part = row[0] * target.backward_likelihood(next_time, 'EMPTY') + row[1] * target.backward_likelihood(next_time, 'OTHER')
    fiber_part = _quadrature(lambda x: target.step_continuous_density(time, state, coordinate, x)
        * target.backward_likelihood(next_time, 'CONTINUOUS', x))
    h = target.backward_likelihood(time, state, coordinate)
    assert atom_part + fiber_part == pytest.approx(h, rel=2e-12, abs=3e-15)
    assert (atom_part + fiber_part) / h == pytest.approx(1., rel=2e-12)


@pytest.mark.parametrize('time,coordinate', [(0., -.5), (.375, .2), (.875, 1.2), (1., 1.2)])
def test_coordinate_score_and_hessian_match_finite_differences(target, time, coordinate):
    result = target.log_likelihood_derivatives(time, 'CONTINUOUS', coordinate)
    step = 1e-4
    f = lambda x: math.log(target.backward_likelihood(time, 'CONTINUOUS', x))
    assert result['gradient'] == pytest.approx((f(coordinate + step) - f(coordinate - step)) / (2 * step), abs=2e-8, rel=2e-7)
    assert result['hessian'] == pytest.approx((f(coordinate + step) - 2 * f(coordinate) + f(coordinate - step)) / step ** 2,
                                             abs=4e-7, rel=3e-6)


def test_evidence_bayes_initial_law_and_terminal_law_are_consistent(target):
    initial = target.conditioned_initial()
    final_prior = target.marginal(1.)
    final = target.terminal_posterior()
    initial_evidence = (target.prior.empty_probability * target.backward_likelihood(0., 'EMPTY')
                       + target.prior.other_probability * target.backward_likelihood(0., 'OTHER')
                       + _quadrature(lambda x: target.prior.continuous_density(x) * target.backward_likelihood(0., 'CONTINUOUS', x)))
    final_evidence = (final_prior.empty_probability * target.backward_likelihood(1., 'EMPTY')
                     + final_prior.other_probability * target.backward_likelihood(1., 'OTHER')
                     + _quadrature(lambda x: final_prior.continuous_density(x) * target.backward_likelihood(1., 'CONTINUOUS', x)))
    assert target.evidence() == pytest.approx(initial_evidence, rel=2e-12)
    assert target.evidence() == pytest.approx(final_evidence, rel=2e-12)
    for law in (target.prior, final_prior, initial, final):
        assert law.empty_probability + law.other_probability + _quadrature(law.continuous_density) == pytest.approx(1., abs=3e-12)
    for x in (-2., -.5, .7, 2.):
        assert initial.continuous_density(x) == pytest.approx(target.prior.continuous_density(x)
            * target.backward_likelihood(0., 'CONTINUOUS', x) / target.evidence(), rel=3e-14)
        assert final.continuous_density(x) == pytest.approx(final_prior.continuous_density(x)
            * target.backward_likelihood(1., 'CONTINUOUS', x) / target.evidence(), rel=3e-14)


def test_numerical_marginal_is_not_silently_assumed_stationary(target):
    exact = ContinuousFiberConditionalBenchmark(target.spec)
    assert target.marginal(1.).continuous_moments()[1] != pytest.approx(1., abs=1e-8)
    assert abs(target.evidence() - exact.evidence()) > 1e-8
    # Category masses remain stationary even though the fiber variance does not.
    assert target.marginal(1.).state_probabilities == pytest.approx(target.prior.state_probabilities, abs=2e-15)


def test_refinement_changes_the_grid_target_and_converges_to_continuous_target(target):
    exact = ContinuousFiberConditionalBenchmark(target.spec)
    errors = []
    for count in (4, 8, 16, 32, 64):
        current = GridTarget(target.spec, _grid(count))
        maximum = 0.
        for state, coordinate in [('EMPTY', None), ('OTHER', None), ('CONTINUOUS', -.7), ('CONTINUOUS', 1.4)]:
            actual = current.log_likelihood_derivatives(0., state, coordinate)
            wanted = exact.log_likelihood_derivatives(0., state, coordinate)
            maximum = max(maximum, max(abs(actual[key] - wanted[key]) for key in actual))
        errors.append(maximum)
    assert all(fine < coarse for coarse, fine in zip(errors, errors[1:]))
    assert errors[-1] < 2e-5
    assert errors[0] > 8 * errors[-1]


def test_no_continuous_clock_gives_exact_continuous_reference_likelihood():
    spec = ContinuousFiberSpec(continuous_rate=0.)
    target, exact = GridTarget(spec, (0., .2, .7, 1.)), ContinuousFiberConditionalBenchmark(spec)
    for time in target.grid:
        for state, coordinate in [('EMPTY', None), ('OTHER', None), ('CONTINUOUS', .4)]:
            assert target.log_likelihood_derivatives(time, state, coordinate) == pytest.approx(
                exact.log_likelihood_derivatives(time, state, coordinate), rel=3e-14, abs=2e-15)
    with pytest.raises(ValueError, match='point mass'):
        target.step_continuous_density(0., 'CONTINUOUS', .4, .4)


def test_no_jump_path_is_closed_form_composition_of_affine_heun_steps():
    spec = ContinuousFiberSpec(death_rate=0., continuous_rate=1.4)
    target = GridTarget(spec, (0., .15, .4, 1.))
    a, v = 1., 0.
    for start, end in zip(target.grid, target.grid[1:]):
        for duration in ((end - start) / 2,) * 2:
            coefficient = _heun_direct(1., 0., duration, spec.continuous_rate)
            variance = _heun_direct(0., math.sqrt(duration), duration, spec.continuous_rate) ** 2
            a, v = coefficient * a, coefficient ** 2 * v + variance
    expected = spec.contamination * target.observation_reference_density + .5 * (1 - spec.contamination) * norm.pdf(
        spec.observation_value, a * -.3, math.sqrt(v + spec.observation_sd ** 2))
    assert target.backward_likelihood(0., 'CONTINUOUS', -.3) == pytest.approx(expected, rel=2e-15)
    assert target.marginal(1.).continuous_moments()[1] == pytest.approx(a ** 2 + v, rel=3e-15)


@pytest.mark.parametrize('grid', [[], (0.,), (0., .5), (0., .7, .2, 1.), (0., .5, .5, 1.), (0., math.nan, 1.), (False, 1.)])
def test_invalid_grid_is_refused(grid):
    with pytest.raises(ValueError):
        GridTarget(ContinuousFiberSpec(), grid)


@pytest.mark.parametrize('updates', [{'potential': (0., 0., .1)}, {'initial_fiber_means': (.2,)},
                                    {'initial_fiber_variances': (.5,)}, {'initial_state_probabilities': (.2, .3, .5)}])
def test_unsupported_base_or_initial_law_is_refused(updates):
    with pytest.raises(ValueError):
        GridTarget(replace(ContinuousFiberSpec(), **updates), _grid(8))


@pytest.mark.parametrize('time', [.0625, .2, -1., 1.1, True, math.nan])
def test_non_node_time_including_halfstep_midpoint_is_refused(target, time):
    with pytest.raises(ValueError):
        target.backward_likelihood(time, 'EMPTY')


@pytest.mark.parametrize('state,coordinate', [('UNKNOWN', None), ('EMPTY', .2), ('OTHER', .2), ('CONTINUOUS', None), ('CONTINUOUS', math.nan)])
def test_invalid_projected_state_is_refused(target, state, coordinate):
    with pytest.raises(ValueError):
        target.backward_likelihood(0., state, coordinate)


def test_terminal_node_has_no_outgoing_macro_kernel(target):
    with pytest.raises(ValueError):
        target.step_parameters(1.)
    with pytest.raises(ValueError):
        target.step_transition(1.)
