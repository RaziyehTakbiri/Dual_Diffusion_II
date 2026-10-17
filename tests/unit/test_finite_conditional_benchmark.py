"""Independent finite-law checks, including negative controls for false exactness."""

from dataclasses import replace
import itertools
import math

import numpy as np
import pytest
from scipy.linalg import expm

from heterodiff.evaluation.finite_conditional_benchmark import (
    FiniteBenchmarkSpec,
    FiniteConditionalBenchmark,
    enumerate_states,
)


@pytest.fixture
def oracle():
    reference = FiniteConditionalBenchmark()
    potential = [0.35 * n0 - 0.2 * n1 + 0.15 * n0 * n1
                 for n0, n1 in reference.states]
    return FiniteConditionalBenchmark(reference.spec, potential)


def test_enumeration_contains_all_unordered_duplicate_occupancies():
    states = enumerate_states(3)
    assert len(states) == 10
    assert states[:3] == ((0, 0), (0, 1), (1, 0))
    assert (3, 0) in states and (2, 1) in states
    assert len(set(states)) == len(states)
    assert all(sum(state) <= 3 for state in states)


@pytest.mark.parametrize("cap", [-1, 9, True, 1.5])
def test_invalid_enumeration_cap_rejected(cap):
    with pytest.raises(ValueError):
        enumerate_states(cap)


@pytest.mark.parametrize("updates", [
    {"theta": 0}, {"theta": float("nan")}, {"theta": True},
    {"death_rate": -1}, {"horizon": float("inf")},
    {"state_cap": 0}, {"state_cap": 1.5}, {"observation_cap": 4},
    {"observation_cap": True}, {"contamination": 0}, {"contamination": 1},
    {"type_probabilities": (0., 1.)}, {"type_probabilities": (.5, .6)},
    {"type_probabilities": [0.5, 0.5]},
])
def test_invalid_specs_rejected(updates):
    with pytest.raises(ValueError):
        FiniteBenchmarkSpec(**updates)


def test_prior_is_independently_conditioned_product_poisson(oracle):
    spec = oracle.spec
    total_cdf = sum(math.exp(-spec.theta) * spec.theta ** count / math.factorial(count)
                    for count in range(spec.state_cap + 1))
    expected = [
        math.exp(-spec.theta) * math.prod((spec.theta * rho) ** n / math.factorial(n)
                                         for n, rho in zip(state, spec.type_probabilities)) / total_cdf
        for state in oracle.states
    ]
    np.testing.assert_allclose(oracle.prior, expected, rtol=2e-15, atol=2e-16)
    assert oracle.prior.sum() == pytest.approx(1.)


@pytest.mark.parametrize("reference", [False, True])
def test_rates_detailed_balance_and_stationarity(oracle, reference):
    q = oracle.reference_generator if reference else oracle.generator
    law = oracle.prior if reference else oracle.stationary_law
    np.testing.assert_allclose(q.sum(axis=1), 0., rtol=0., atol=1e-15)
    assert np.all(np.diag(q) <= 0)
    assert np.all(q - np.diag(np.diag(q)) >= 0)
    flux = law[:, None] * q
    np.testing.assert_allclose(flux, flux.T, rtol=2e-15, atol=2e-16)
    np.testing.assert_allclose(law @ q, 0., rtol=0., atol=1e-15)
    np.testing.assert_allclose(law @ oracle.transition(.7, reference), law, rtol=2e-15, atol=2e-16)
    for index, state in enumerate(oracle.states):
        for other, target in enumerate(oracle.states):
            if sum(state) == oracle.spec.state_cap and sum(target) > sum(state):
                assert q[index, other] == 0.


def test_occurrence_death_and_capped_birth_rates_are_explicit(oracle):
    i = oracle.state_index[(2, 1)]
    q = oracle.reference_generator
    assert q[i, oracle.state_index[(1, 1)]] == pytest.approx(2 * oracle.spec.death_rate)
    assert q[i, oracle.state_index[(2, 0)]] == pytest.approx(oracle.spec.death_rate)
    i0 = oracle.state_index[(0, 0)]
    assert q[i0, oracle.state_index[(1, 0)]] == pytest.approx(
        oracle.spec.theta * oracle.spec.death_rate * oracle.spec.type_probabilities[0])


@pytest.mark.parametrize("reference", [False, True])
def test_matrix_exponential_stochasticity_and_semigroup(oracle, reference):
    identity = np.eye(len(oracle.states))
    np.testing.assert_array_equal(oracle.transition(0., reference), identity)
    for time in (0., .13, .37, 1.):
        p = oracle.transition(time, reference)
        assert np.min(p) >= 0
        np.testing.assert_allclose(p.sum(axis=1), 1., rtol=0., atol=1e-14)
    np.testing.assert_allclose(
        oracle.transition(.13, reference) @ oracle.transition(.37, reference),
        oracle.transition(.5, reference), rtol=2e-14, atol=2e-16,
    )


@pytest.mark.parametrize("reference", [False, True])
def test_matrix_exponential_matches_independent_uniformization(oracle, reference):
    # Poisson mixture of discrete jump-chain powers, implemented separately
    # from scipy.linalg.expm.  The omitted Poisson tail is below 1e-150 here.
    q = oracle.reference_generator if reference else oracle.generator
    rate = float(np.max(-np.diag(q)))
    duration = .73
    chain = np.eye(len(q)) + q / rate
    power = np.eye(len(q))
    weight = math.exp(-rate * duration)
    total_weight = weight
    probability = weight * power
    for count in range(1, 201):
        power = power @ chain
        weight *= rate * duration / count
        total_weight += weight
        probability += weight * power
    assert total_weight == pytest.approx(1., rel=0., abs=2e-15)
    np.testing.assert_allclose(probability, oracle.transition(duration, reference),
                               rtol=2e-14, atol=3e-16)


def test_backward_equation_has_correct_time_direction(oracle):
    time, epsilon = .4, 1e-5
    derivative = (oracle.backward_likelihood(time + epsilon, (1, 0))
                  - oracle.backward_likelihood(time - epsilon, (1, 0))) / (2 * epsilon)
    expected = -oracle.generator @ oracle.backward_likelihood(time, (1, 0))
    np.testing.assert_allclose(derivative, expected, rtol=2e-8, atol=2e-11)


def _brute_observation_probability(state, observation, spec):
    # Independently enumerate labelled occurrence retention patterns, and sum
    # labelled Poisson type strings rather than using the oracle's binomials.
    occurrence_types = [0] * state[0] + [1] * state[1]
    clean = 0.
    for kept in itertools.product((False, True), repeat=len(occurrence_types)):
        counts = tuple(sum(flag and event_type == j for flag, event_type in zip(kept, occurrence_types))
                       for j in range(2))
        result = counts if sum(counts) <= spec.observation_cap else None
        if result == observation:
            clean += 2. ** (-len(occurrence_types))
    reference = 0.
    # Only through cap need event-type strings.  Overflow total-count tails do
    # not depend on the type assignments and are summed directly up to 160.
    for count in range(161):
        count_mass = math.exp(-spec.observation_reference_rate) * spec.observation_reference_rate ** count / math.factorial(count)
        if count > spec.observation_cap:
            if observation is None:
                reference += count_mass
            continue
        for types in itertools.product((0, 1), repeat=count):
            counts = (types.count(0), types.count(1))
            if counts == observation:
                reference += count_mass * math.prod(spec.type_probabilities[i] for i in types)
    return (1. - spec.contamination) * clean + spec.contamination * reference


@pytest.mark.parametrize("observation_cap", [0, 1, 2, 3])
def test_observation_law_matches_independent_labelled_enumeration(observation_cap):
    oracle = FiniteConditionalBenchmark(FiniteBenchmarkSpec(observation_cap=observation_cap))
    for state in oracle.states:
        probabilities = []
        for observation in oracle.observations:
            observed = oracle.observation_probability(state, observation)
            expected = _brute_observation_probability(state, observation, oracle.spec)
            assert observed == pytest.approx(expected, rel=3e-15, abs=2e-16)
            assert observed > 0
            probabilities.append(observed)
        assert sum(probabilities) == pytest.approx(1., rel=0., abs=3e-16)


def test_duplicate_multiplicity_is_not_dropped():
    oracle = FiniteConditionalBenchmark(FiniteBenchmarkSpec(observation_cap=2))
    eps = oracle.spec.contamination
    p10 = oracle.observation_probability((2, 0), (1, 0))
    p00 = oracle.observation_probability((0, 0), (1, 0))
    assert p10 - p00 == pytest.approx((1. - eps) * 2 / 4)
    p20 = oracle.observation_probability((2, 0), (2, 0))
    p00 = oracle.observation_probability((0, 0), (2, 0))
    assert p20 - p00 == pytest.approx((1. - eps) / 4)


@pytest.mark.parametrize("observation", [(0, 0), (0, 1), (1, 0), None])
def test_posterior_and_backward_likelihood_match_joint_enumeration(oracle, observation):
    p = oracle.transition(oracle.spec.horizon)
    g = oracle.observation_likelihood(observation)
    joint = np.array([[oracle.prior[i] * p[i, j] * g[j]
                       for j in range(len(oracle.states))]
                      for i in range(len(oracle.states))])
    evidence = math.fsum(joint.flat)
    assert oracle.evidence(observation) == pytest.approx(evidence, rel=2e-15)
    np.testing.assert_allclose(oracle.terminal_posterior(observation), joint.sum(axis=0) / evidence,
                               rtol=3e-15, atol=2e-16)
    np.testing.assert_allclose(oracle.conditioned_initial(observation), joint.sum(axis=1) / evidence,
                               rtol=3e-15, atol=2e-16)
    np.testing.assert_array_equal(oracle.backward_likelihood(oracle.spec.horizon, observation), g)


@pytest.mark.parametrize("observation", [(0, 0), (0, 1), (1, 0), None])
def test_doob_rows_composition_initialization_and_terminal_marginal(oracle, observation):
    k01 = oracle.doob_transition(0., .37, observation)
    k12 = oracle.doob_transition(.37, 1., observation)
    k02 = oracle.doob_transition(0., 1., observation)
    for kernel in (k01, k12, k02):
        assert np.min(kernel) >= 0
        np.testing.assert_allclose(kernel.sum(axis=1), 1., rtol=0., atol=2e-14)
    np.testing.assert_allclose(k01 @ k12, k02, rtol=3e-14, atol=2e-16)
    np.testing.assert_allclose(oracle.conditioned_initial(observation) @ k01 @ k12,
                               oracle.terminal_posterior(observation), rtol=3e-14, atol=2e-16)
    # A correct transition does not make an unconditioned initializer correct.
    incorrect = oracle.prior @ k02
    assert np.sum(np.abs(incorrect - oracle.terminal_posterior(observation))) / 2 > 1e-3


def test_path_bayes_identity_exhaustively_on_three_time_skeleton(oracle):
    observation = (1, 0)
    times = (0., .4, 1.)
    p01, p12 = oracle.transition(.4), oracle.transition(.6)
    g = oracle.observation_likelihood(observation)
    z = oracle.evidence(observation)
    total = 0.
    for i, j, k in itertools.product(range(len(oracle.states)), repeat=3):
        expected = oracle.prior[i] * p01[i, j] * p12[j, k] * g[k] / z
        observed = oracle.conditioned_path_probability(
            (oracle.states[i], oracle.states[j], oracle.states[k]), times, observation)
        assert observed == pytest.approx(expected, rel=3e-14, abs=2e-17)
        total += observed
    assert total == pytest.approx(1., rel=2e-14)


def test_arbitrary_initial_law_is_conditioned_not_silently_replaced(oracle):
    initial = np.zeros(len(oracle.states))
    initial[oracle.state_index[(2, 1)]] = 1.
    posterior = oracle.terminal_posterior(None, initial)
    np.testing.assert_array_equal(oracle.conditioned_initial(None, initial), initial)
    expected = initial @ oracle.transition(1.) * oracle.observation_likelihood(None)
    np.testing.assert_allclose(posterior, expected / expected.sum(), rtol=2e-15)
    assert not np.allclose(posterior, oracle.terminal_posterior(None))


@pytest.mark.parametrize("observation_cap", [0, 1, 2, 3])
def test_uncapped_reference_convolution_is_normalized_and_terminal_exact(observation_cap):
    oracle = FiniteConditionalBenchmark(FiniteBenchmarkSpec(observation_cap=observation_cap))
    for state in oracle.states:
        for duration in (0., .2, .7, 1.):
            masses = [oracle.uncapped_reference_likelihood(state, duration, a) for a in oracle.observations]
            assert all(p > 0 for p in masses)
            assert sum(masses) == pytest.approx(1., rel=0., abs=5e-16)
        for observation in oracle.observations:
            assert oracle.uncapped_reference_likelihood(state, 0., observation) == pytest.approx(
                oracle.observation_probability(state, observation), rel=3e-15, abs=2e-16)


def test_uncapped_empty_formula_and_duplicate_convolution_by_hand():
    oracle = FiniteConditionalBenchmark(FiniteBenchmarkSpec(observation_cap=2))
    duration, state = .6, (3, 0)
    spec = oracle.spec
    keep = math.exp(-spec.death_rate * duration) / 2
    lam = spec.theta * (1 - math.exp(-spec.death_rate * duration)) / 2
    empty_clean = (1 - keep) ** 3 * math.exp(-lam)
    empty_ref = math.exp(-spec.observation_reference_rate)
    assert oracle.uncapped_reference_likelihood(state, duration, (0, 0)) == pytest.approx(
        (1 - spec.contamination) * empty_clean + spec.contamination * empty_ref, rel=2e-15)
    lam0 = lam * spec.type_probabilities[0]
    duplicate_clean = math.exp(-lam) * (
        (1 - keep) ** 3 * lam0 ** 2 / 2
        + 3 * keep * (1 - keep) ** 2 * lam0
        + 3 * keep ** 2 * (1 - keep)
    )
    duplicate_ref = math.exp(-spec.observation_reference_rate) * (spec.observation_reference_rate * spec.type_probabilities[0]) ** 2 / 2
    assert oracle.uncapped_reference_likelihood(state, duration, (2, 0)) == pytest.approx(
        (1 - spec.contamination) * duplicate_clean + spec.contamination * duplicate_ref, rel=2e-15)


def test_cap_and_base_law_approximations_have_measurable_nonzero_error(oracle):
    comparison = oracle.compare_reference_guides(.8, None)
    assert comparison["maximum_absolute_difference"] > .01
    assert comparison["uncapped_formula_is_capped_exact"] is False
    capped = oracle.capped_reference_likelihood(.8, (1, 0))
    learned_base = oracle.backward_likelihood(.2, (1, 0))
    assert np.max(np.abs(capped - learned_base)) > .01
    np.testing.assert_allclose(
        oracle.capped_reference_likelihood(0., None), oracle.observation_likelihood(None), rtol=0., atol=0.)


def test_freezing_conditional_rates_is_not_the_exact_grid_kernel(oracle):
    observation = (1, 0)
    h = oracle.backward_likelihood(0., observation)
    frozen_rates = oracle.generator * h[None, :] / h[:, None]
    np.fill_diagonal(frozen_rates, 0.)
    np.fill_diagonal(frozen_rates, -frozen_rates.sum(axis=1))
    approximate = expm(.5 * frozen_rates)
    exact = oracle.doob_transition(0., .5, observation)
    assert np.max(np.abs(approximate - exact)) > 1e-3
    # Both are stochastic; stochasticity alone does not establish the intended law.
    np.testing.assert_allclose(approximate.sum(axis=1), 1., atol=2e-15)


def test_mismatched_backward_guide_breaks_semigroup_rows(oracle):
    observation = (1, 0)
    ref_start = oracle.capped_reference_likelihood(1., observation)
    ref_end = oracle.capped_reference_likelihood(.5, observation)
    wrong = oracle.transition(.5) * ref_end[None, :] / ref_start[:, None]
    assert np.max(np.abs(wrong.sum(axis=1) - 1.)) > .01


@pytest.mark.parametrize("time", [-.1, 1.1, True, float("nan")])
def test_bad_times_rejected_even_after_cache_primed(oracle, time):
    oracle.transition(1.)
    with pytest.raises(ValueError):
        oracle.transition(time)
    with pytest.raises(ValueError):
        oracle.backward_likelihood(time, None)


@pytest.mark.parametrize("observation", [(2, 0), (-1, 0), (True, 0), [0, 0], (0,)])
def test_bad_observations_rejected(oracle, observation):
    with pytest.raises(ValueError):
        oracle.observation_likelihood(observation)


@pytest.mark.parametrize("potential", [[0.], [float("nan")] * 10, [5.] * 10, [True] * 10])
def test_bad_potentials_rejected(potential):
    with pytest.raises(ValueError):
        FiniteConditionalBenchmark(potential=potential)


def test_invalid_initial_and_path_inputs_rejected(oracle):
    for initial in ([1.], [0.] * 10, [float("nan")] * 10, [-.1, 1.1] + [0.] * 8):
        with pytest.raises(ValueError):
            oracle.terminal_posterior(None, initial)
    with pytest.raises(ValueError):
        oracle.doob_transition(.7, .2, None)
    for times in ((0.,), (.1, 1.), (0., .5), (0., .8, .7, 1.)):
        with pytest.raises(ValueError):
            oracle.conditioned_path_probability(((0, 0),) * len(times), times, None)
    with pytest.raises(ValueError):
        oracle.transition(.1, reference=1)
    assert FiniteConditionalBenchmark(replace(oracle.spec, state_cap=2)).spec.state_cap == 2


def test_oracle_arrays_are_read_only(oracle):
    for array in (oracle.prior, oracle.stationary_law, oracle.generator, oracle.reference_generator,
                  oracle.transition(.2), oracle.observation_likelihood(None), oracle.terminal_posterior(None)):
        assert not array.flags.writeable
