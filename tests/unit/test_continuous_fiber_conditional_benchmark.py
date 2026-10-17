"""Independent analytic, quadrature, and sampling checks for the N=1 oracle."""

from dataclasses import replace
import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm

from heterodiff.evaluation.continuous_fiber_conditional_benchmark import (
    STATES,
    ContinuousFiberSpec,
    ContinuousFiberConditionalBenchmark,
    GaussianComponent,
    MixedGaussianLaw,
)


@pytest.fixture
def oracle():
    return ContinuousFiberConditionalBenchmark()


@pytest.fixture
def nonstationary():
    return ContinuousFiberConditionalBenchmark(ContinuousFiberSpec(
        theta=1.3, potential=(.1, -.2, .35), initial_state_probabilities=(.15, .2, .65),
        initial_fiber_weights=(.4, .6), initial_fiber_means=(-1.1, 1.3), initial_fiber_variances=(.2, .4)))


@pytest.mark.parametrize('updates', [
    {'theta': 0}, {'horizon': True}, {'observation_sd': 0}, {'observation_sd': 1e-200},
    {'death_rate': -1}, {'continuous_rate': float('nan')}, {'contamination': 0},
    {'contamination': 1}, {'observation_value': float('inf')}, {'observation_value': 11},
    {'type_probabilities': (.5, .6)}, {'type_probabilities': (0., 1.)},
    {'type_probabilities': [.25, .75]}, {'potential': (0., 0.)}, {'potential': (0., 0., 5.)},
    {'initial_state_probabilities': (.2, .2, .2)}, {'initial_fiber_weights': ()},
    {'initial_fiber_weights': (.5, .5)}, {'initial_fiber_variances': (0.,)},
])
def test_invalid_specs_rejected(updates):
    with pytest.raises(ValueError):
        ContinuousFiberSpec(**updates)


def test_state_generator_rates_and_reference_stationarity(oracle):
    assert STATES == ('EMPTY', 'OTHER', 'CONTINUOUS')
    np.testing.assert_allclose(oracle.generator, [[-.8, .2, .6], [1., -1., 0.], [1., 0., -1.]],
                               rtol=0., atol=2e-16)
    np.testing.assert_allclose(oracle.reference_state_prior @ oracle.generator, 0., atol=2e-16)
    for time in (0., .1, .7, 1.):
        p = oracle.transition(time)
        assert np.min(p) >= 0
        np.testing.assert_allclose(p.sum(axis=1), 1., atol=2e-15)
        np.testing.assert_allclose(oracle.marginal(time).state_probabilities, oracle.prior.state_probabilities, atol=3e-16)
        for value in (-2., 0., .7, 2.):
            assert oracle.marginal(time).continuous_density(value) == pytest.approx(oracle.prior.continuous_density(value), rel=3e-15)


def test_nonzero_finite_state_tilt_has_expected_stationary_law(nonstationary):
    weights = nonstationary.reference_state_prior * np.exp(2 * np.array(nonstationary.spec.potential))
    law = weights / weights.sum()
    np.testing.assert_allclose(law @ nonstationary.generator, 0., atol=2e-16)
    flux = law[:, None] * nonstationary.generator
    np.testing.assert_allclose(flux, flux.T, atol=2e-16)


def test_augmented_memory_chain_matches_survival_plus_reset_identity(nonstationary):
    for time in (0., .001, .25, .9):
        memory = nonstationary._memory_transition(time)
        projected = nonstationary.transition(time)
        survival = math.exp(-nonstationary.generator[2, 0] * time)
        assert memory[3, 3] == pytest.approx(survival, rel=3e-15)
        np.testing.assert_allclose(memory[:3, :3], projected, atol=2e-16)
        np.testing.assert_array_equal(memory[:3, 3], 0.)
        assert memory[3, 2] >= 0
        assert memory[3, 2] + survival == pytest.approx(projected[2, 2], rel=3e-15)
        np.testing.assert_allclose(memory[3, :2], projected[2, :2], atol=2e-16)


def test_ou_rate_uses_actual_sampler_half_drift_convention(oracle):
    contraction, variance = oracle._ou(.4)
    assert contraction == pytest.approx(math.exp(-.2))
    assert variance == pytest.approx(1. - math.exp(-.4))
    assert contraction ** 2 + variance == pytest.approx(1.)


def test_nonstationary_marginal_density_matches_transition_quadrature(nonstationary):
    time = .6
    law = nonstationary.marginal(time)
    for value in (-2., -.3, .7, 2.):
        birth = sum(nonstationary.prior.state_probabilities[i] * nonstationary.transition_continuous_density(
            time, state, None, value) for i, state in enumerate(STATES[:2]))
        retained, error = quad(lambda x: nonstationary.prior.continuous_density(x)
                              * nonstationary.transition_continuous_density(time, 'CONTINUOUS', x, value),
                              -np.inf, np.inf, epsabs=2e-12, epsrel=2e-12)
        assert error < 2e-11
        assert law.continuous_density(value) == pytest.approx(birth + retained, rel=2e-11, abs=2e-13)
    assert sum(law.state_probabilities) == pytest.approx(1., abs=3e-15)


def test_observation_channel_keeps_clean_noise_and_unnoised_replacement_separate(oracle):
    p = oracle.spec
    replacement = math.exp(-1) * p.type_probabilities[1] * norm.pdf(p.observation_value)
    assert oracle.observation_reference_density == pytest.approx(replacement, rel=2e-15)
    assert oracle.observation_likelihood('EMPTY') == pytest.approx(p.contamination * replacement)
    assert oracle.observation_likelihood('OTHER') == pytest.approx(p.contamination * replacement)
    assert oracle.observation_likelihood('CONTINUOUS', .4) == pytest.approx(
        p.contamination * replacement + (1 - p.contamination) * .5 * norm.pdf(p.observation_value, .4, p.observation_sd), rel=2e-15)
    incorrectly_smoothed_reference = math.exp(-1) * p.type_probabilities[1] * norm.pdf(
        p.observation_value, 0, math.sqrt(1 + p.observation_sd ** 2))
    assert abs(replacement - incorrectly_smoothed_reference) > .001


@pytest.mark.parametrize('state, coordinate', [('EMPTY', None), ('OTHER', None), ('CONTINUOUS', -.8)])
def test_terminal_backward_likelihood_is_the_observation_channel(oracle, state, coordinate):
    assert oracle.backward_likelihood(1., state, coordinate) == pytest.approx(
        oracle.observation_likelihood(state, coordinate), rel=2e-15)


@pytest.mark.parametrize('state, coordinate', [('EMPTY', None), ('OTHER', None), ('CONTINUOUS', -.8)])
def test_backward_semigroup_identity_by_independent_quadrature(nonstationary, state, coordinate):
    start, end = .2, .75
    index = STATES.index(state)
    atoms = sum(nonstationary.transition(end - start)[index, j] * nonstationary.backward_likelihood(end, target)
                for j, target in enumerate(STATES[:2]))
    continuous, error = quad(lambda z: nonstationary.transition_continuous_density(
        end - start, state, coordinate, z) * nonstationary.backward_likelihood(end, 'CONTINUOUS', z),
        -np.inf, np.inf, epsabs=2e-12, epsrel=2e-12)
    assert error < 2e-11
    assert atoms + continuous == pytest.approx(nonstationary.backward_likelihood(start, state, coordinate), rel=2e-11, abs=2e-13)


@pytest.mark.parametrize('state, coordinate', [('EMPTY', None), ('OTHER', None), ('CONTINUOUS', .4)])
def test_doob_transition_atom_and_density_mass_is_one(nonstationary, state, coordinate):
    atoms = sum(nonstationary.doob_atom_probability(.1, .9, state, coordinate, target) for target in STATES[:2])
    continuous, error = quad(lambda z: nonstationary.doob_continuous_density(.1, .9, state, coordinate, z),
                             -np.inf, np.inf, epsabs=2e-11, epsrel=2e-11)
    assert error < 2e-10
    assert atoms + continuous == pytest.approx(1., rel=2e-11)


@pytest.mark.parametrize('time, coordinate', [(0., -1.), (.3, .2), (.7, 1.4), (1., -.3)])
def test_analytic_log_gradient_and_hessian_match_finite_differences(nonstationary, time, coordinate):
    result = nonstationary.log_likelihood_derivatives(time, 'CONTINUOUS', coordinate)
    step = 1e-4
    f = lambda x: math.log(nonstationary.backward_likelihood(time, 'CONTINUOUS', x))
    gradient = (f(coordinate + step) - f(coordinate - step)) / (2 * step)
    hessian = (f(coordinate + step) - 2 * f(coordinate) + f(coordinate - step)) / step ** 2
    assert result['gradient'] == pytest.approx(gradient, rel=2e-7, abs=2e-8)
    assert result['hessian'] == pytest.approx(hessian, rel=3e-6, abs=3e-7)
    assert result['log_likelihood'] == pytest.approx(f(coordinate))


def test_backward_pde_on_continuous_category_includes_killing_and_ou(nonstationary):
    time, coordinate, step = .4, -.2, 1e-5
    result = nonstationary.log_likelihood_derivatives(time, 'CONTINUOUS', coordinate)
    h = math.exp(result['log_likelihood'])
    time_derivative = (nonstationary.backward_likelihood(time + step, 'CONTINUOUS', coordinate)
                       - nonstationary.backward_likelihood(time - step, 'CONTINUOUS', coordinate)) / (2 * step)
    c = nonstationary.spec.continuous_rate
    continuous_generator = c / 2 * h * (-coordinate * result['gradient'] + result['hessian'] + result['gradient'] ** 2)
    jump_generator = nonstationary.generator[2, 0] * (nonstationary.backward_likelihood(time, 'EMPTY') - h)
    assert time_derivative + continuous_generator + jump_generator == pytest.approx(0., abs=2e-10)


@pytest.mark.parametrize('which', ['terminal', 'initial'])
def test_gaussian_mixture_posteriors_equal_independent_bayes_density_and_cdf(nonstationary, which):
    prior = nonstationary.marginal(1.) if which == 'terminal' else nonstationary.prior
    posterior = nonstationary.terminal_posterior() if which == 'terminal' else nonstationary.conditioned_initial()
    likelihood = (lambda state, x=None: nonstationary.observation_likelihood(state, x)) if which == 'terminal' else (
        lambda state, x=None: nonstationary.backward_likelihood(0., state, x))
    evidence = sum(prior.state_probabilities[i] * likelihood(state) for i, state in enumerate(STATES[:2]))
    continuous_mass, _ = quad(lambda x: prior.continuous_density(x) * likelihood('CONTINUOUS', x),
                              -np.inf, np.inf, epsabs=2e-12, epsrel=2e-12)
    evidence += continuous_mass
    assert evidence == pytest.approx(nonstationary.evidence(), rel=2e-11)
    for value in (-2., -.5, .7, 2.):
        expected_density = prior.continuous_density(value) * likelihood('CONTINUOUS', value) / evidence
        assert posterior.continuous_density(value) == pytest.approx(expected_density, rel=2e-11, abs=2e-13)
        expected_cdf, error = quad(lambda x: prior.continuous_density(x) * likelihood('CONTINUOUS', x) / evidence,
                                   -np.inf, value, epsabs=2e-11, epsrel=2e-11)
        assert error < 2e-10
        assert posterior.continuous_cdf(value) == pytest.approx(expected_cdf, rel=2e-11, abs=2e-13)
    assert posterior.state_probabilities[2] == pytest.approx(continuous_mass / evidence, rel=2e-11)


def test_conditional_initial_law_does_not_equal_unconditioned_stationary_prior(oracle):
    conditioned = oracle.conditioned_initial()
    assert max(abs(a - b) for a, b in zip(conditioned.state_probabilities, oracle.prior.state_probabilities)) > .05
    assert abs(conditioned.continuous_moments()[0] - oracle.prior.continuous_moments()[0]) > .1
    assert conditioned.state_probabilities != oracle.terminal_posterior().state_probabilities


def test_no_jump_continuous_control_preserves_positive_contamination_mixture():
    spec = ContinuousFiberSpec(death_rate=0., initial_state_probabilities=(0., 0., 1.))
    oracle = ContinuousFiberConditionalBenchmark(spec)
    np.testing.assert_array_equal(oracle.transition(.6), np.eye(3))
    assert oracle.terminal_posterior().state_probabilities[2] == pytest.approx(1.)
    assert oracle.conditioned_initial().state_probabilities[2] == pytest.approx(1.)
    post = oracle.terminal_posterior()
    positive_components = [c for c in post.components if c.weight > 0]
    assert len(positive_components) == 2
    assert sorted(c.variance for c in positive_components) == pytest.approx([.2, 1.])
    result = oracle.log_likelihood_derivatives(.4, 'CONTINUOUS', .2)
    a = math.exp(-.6 / 2)
    variance = 1 - math.exp(-.6) + .25
    absolute_h = oracle._contamination_density + .45 * norm.pdf(.7, a * .2, math.sqrt(variance))
    assert math.exp(result['log_likelihood']) == pytest.approx(absolute_h, rel=2e-15)


def test_gaussian_mixture_moments_and_seeded_sampler(nonstationary):
    law = nonstationary.conditioned_initial()
    mean, variance = law.continuous_moments()
    mass = law.state_probabilities[2]
    first, _ = quad(lambda x: x * law.continuous_density(x), -np.inf, np.inf)
    second, _ = quad(lambda x: (x - mean) ** 2 * law.continuous_density(x), -np.inf, np.inf)
    assert mean == pytest.approx(first / mass, rel=2e-11)
    assert variance == pytest.approx(second / mass, rel=2e-11)
    first_rng, second_rng = np.random.default_rng(23), np.random.default_rng(23)
    first_draws = [law.sample(first_rng) for _ in range(100)]
    assert first_draws == [law.sample(second_rng) for _ in range(100)]
    for state, coordinate in first_draws:
        assert state in STATES
        assert (coordinate is None) == (state != 'CONTINUOUS')


def test_mixed_law_validation_and_joint_cdf_semantics():
    law = MixedGaussianLaw(.2, .3, (GaussianComponent(.5, 1., 2.),))
    assert law.continuous_cdf(20.) == pytest.approx(.5)
    assert law.continuous_cdf(-20.) < 1e-40
    assert law.to_dict()['continuous_density_is_joint_not_conditional'] is True
    with pytest.raises(ValueError):
        MixedGaussianLaw(.2, .3, ())
    with pytest.raises(ValueError):
        GaussianComponent(.2, 0., 0.)
    with pytest.raises(ValueError):
        MixedGaussianLaw(1., 0., ()).continuous_moments()
    with pytest.raises(ValueError):
        law.sample(None)


@pytest.mark.parametrize('time', [-.1, 1.1, True, float('nan')])
def test_invalid_times_rejected_even_with_cached_numeric_neighbour(oracle, time):
    oracle.transition(1.)
    with pytest.raises(ValueError):
        oracle.transition(time)
    with pytest.raises(ValueError):
        oracle.backward_likelihood(time, 'CONTINUOUS', .2)


@pytest.mark.parametrize('state, coordinate', [('UNKNOWN', None), ('CONTINUOUS', None),
                                              ('EMPTY', .2), ('OTHER', .2), ('CONTINUOUS', float('nan'))])
def test_invalid_projected_states_rejected(oracle, state, coordinate):
    with pytest.raises(ValueError):
        oracle.backward_likelihood(.2, state, coordinate)


def test_zero_rate_point_mass_density_and_extreme_underflow_refuse_explicitly(oracle):
    zero = ContinuousFiberConditionalBenchmark(replace(oracle.spec, continuous_rate=0.))
    with pytest.raises(ValueError, match='point mass'):
        zero.transition_continuous_density(.5, 'CONTINUOUS', .2, .3)
    extreme = ContinuousFiberConditionalBenchmark(replace(oracle.spec, potential=(4., 0., -4.), death_rate=10.))
    with pytest.raises(ArithmeticError, match='not representable'):
        extreme.backward_likelihood(0., 'CONTINUOUS', .2)


def test_log_RN_and_absolute_observation_conventions_differ_by_constant_only(oracle):
    lam = oracle.observation_reference_density
    for state, coordinate in (('EMPTY', None), ('OTHER', None), ('CONTINUOUS', -.2)):
        absolute = oracle.log_likelihood_derivatives(1., state, coordinate)
        rn = math.exp(absolute['log_likelihood']) / lam
        if state != 'CONTINUOUS':
            assert rn == pytest.approx(oracle.spec.contamination)
            assert absolute['gradient'] == absolute['hessian'] == 0.
        else:
            expected = .1 + .45 * norm.pdf(.7, coordinate, .5) / lam
            assert rn == pytest.approx(expected, rel=3e-15)
