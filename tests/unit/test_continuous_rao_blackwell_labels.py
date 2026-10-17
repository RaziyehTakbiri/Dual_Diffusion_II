"""Manufactured forward-label identities; no learner or scientific fits."""

from copy import deepcopy
import ast
import json
import math
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import quad

from heterodiff.experiments import continuous_rao_blackwell_labels as paired
from heterodiff.experiments.continuous_forward_labels import (
    ForwardSpec, observation_density, rollout_labels,
)


class _Tape:
    def __init__(self, *, normal=(), poisson=(), random=()):
        self.items = {'normal': list(normal), 'poisson': list(poisson), 'random': list(random)}

    def _take(self, kind, size):
        if size == 0:
            return np.empty(0, dtype=int if kind == 'poisson' else float)
        assert self.items[kind], (kind, size)
        answer = np.asarray(self.items[kind].pop(0))
        assert answer.shape == (size,)
        return answer

    def normal(self, size):
        return self._take('normal', size)

    def poisson(self, rate, size):
        assert rate > 0
        return self._take('poisson', size)

    def random(self, size):
        return self._take('random', size)


def _phi(delta, variance):
    return math.exp(-delta*delta/(2*variance))/math.sqrt(2*math.pi*variance)


def _expected(spec, mean, variance):
    return spec.contamination_density+(1-spec.contamination)*.5*_phi(
        spec.observation_value-mean, variance+spec.observation_sd**2)


def _half(spec):
    clock = spec.continuous_rate/16
    return 1-clock/2+clock*clock/8, clock*(1-clock/4)**2


def _call(spec, u, states, z, skeleton_seed=81, noise_seed=29):
    return paired.paired_rollout_labels(spec, u, np.asarray(states, dtype=int),
        np.asarray(z, dtype=float), np.random.default_rng(skeleton_seed),
        np.random.default_rng(noise_seed))


def _assert_counts(work):
    for name, rows in work['per_suffix_counts'].items():
        assert len(rows) == work['forward_suffix_count']
        assert all(type(item) is int and item >= 0 for item in rows)
        assert sum(rows) == work[name]
    c = work['per_suffix_counts']
    np.testing.assert_array_equal(c['accepted_birth_death_events'],
        np.add(c['accepted_births'], c['accepted_deaths']))
    np.testing.assert_array_equal(c['raw_normal_draws_total'],
        np.add(c['raw_half_step_normal_draws'], c['raw_birth_normal_draws']))
    np.testing.assert_array_equal(c['potential_uniformization_events'],
        c['skeleton_acceptance_uniform_draws'])
    np.testing.assert_array_equal(c['raw_birth_normal_draws'], c['selected_births'])
    np.testing.assert_array_equal(c['conditional_gaussian_affine_updates'],
        c['continuous_half_step_updates'])
    assert work['backward_likelihood_or_score_queried'] is False
    assert work['conditional_endpoint_sampler_used'] is False
    assert work['same_jump_skeleton'] is True
    json.dumps(work, allow_nan=False)


def test_terminal_identity_zero_variance_and_no_random_draws():
    spec = ForwardSpec(.8, .7)
    states, z = np.array([0, 1, 2, 2]), np.array([0., 0., .7, -2.])
    skeleton, noise = np.random.default_rng(7), np.random.default_rng(9)
    before = deepcopy((skeleton.bit_generator.state, noise.bit_generator.state))
    raw, rb, work = paired.paired_rollout_labels(spec, 1., states, z, skeleton, noise)
    np.testing.assert_array_equal(raw, observation_density(spec, states, z))
    np.testing.assert_array_equal(raw, rb)
    assert work['conditional_raw_label_variance'] == [0., 0., 0., 0.]
    assert (skeleton.bit_generator.state, noise.bit_generator.state) == before
    assert all(work[name] == 0 for name in work['per_suffix_counts'] if 'evaluations' not in name)
    assert work['raw_observation_density_evaluations'] == 4
    assert work['rb_initial_raw_formula_evaluations'] == 4
    assert work['rb_gaussian_convolution_evaluations'] == 0
    _assert_counts(work)


def test_same_skeleton_different_noise_preserves_rb_labels_and_counts():
    spec = ForwardSpec(2.5, 1.4)
    states = np.tile([0, 1, 2, 2], 256)
    z = np.where(states == 2, .3, 0.)
    first = _call(spec, 0., states, z, noise_seed=17)
    second = _call(spec, 0., states, z, noise_seed=41)
    assert not np.array_equal(first[0], second[0])
    np.testing.assert_array_equal(first[1], second[1])
    for key in first[2]:
        if key != 'terminal_gaussian_state':
            assert first[2][key] == second[2][key]
    for key in ('states', 'means', 'variances'):
        assert first[2]['terminal_gaussian_state'][key] == second[2]['terminal_gaussian_state'][key]
    _assert_counts(first[2])


@pytest.mark.parametrize('u', [0., .375, .875])
def test_no_jump_gaussian_convolution_is_known_numerical_heun_law(u):
    spec = ForwardSpec(.8, .7, death_rate=0.)
    z = np.array([-2., .7, 2.])
    raw, rb, work = _call(spec, u, [2, 2, 2], z)
    a, q = _half(spec)
    steps = 2*(8-paired.GRID.index(u))
    variance = sum(q*a**(2*j) for j in range(steps))
    np.testing.assert_allclose(rb, [_expected(spec, a**steps*x, variance) for x in z],
        rtol=2e-15, atol=2e-16)
    assert work['continuous_half_step_updates'] == len(z)*steps
    assert work['raw_normal_draws_total'] == len(z)*steps
    assert work['potential_uniformization_events'] == 0
    assert np.all(raw >= spec.contamination_density)
    assert np.all(raw <= spec.maximum_label)
    _assert_counts(work)


def test_birth_has_unit_gaussian_reset_and_only_right_half(monkeypatch):
    spec = ForwardSpec(2.5, .7)
    skeleton = _Tape(poisson=([1],), random=([0.], [0.]))
    noise = _Tape(normal=([1.2], [-.4]))
    monkeypatch.setattr(paired.np.random, 'Generator', _Tape)
    raw, rb, work = paired.paired_rollout_labels(spec, .875,
        np.array([0]), np.array([0.]), skeleton, noise)
    a, q = _half(spec)
    assert raw[0] == pytest.approx(_expected(spec, a*1.2-math.sqrt(q)*.4, 0), abs=1e-15)
    assert rb[0] == pytest.approx(_expected(spec, 0, a*a+q), abs=1e-15)
    assert work['selected_births'] == work['accepted_births'] == 1
    assert work['continuous_half_step_updates'] == 1
    assert work['raw_birth_normal_draws'] == work['raw_half_step_normal_draws'] == 1
    assert all(not values for values in skeleton.items.values())
    assert all(not values for values in noise.items.values())
    _assert_counts(work)


@pytest.mark.parametrize('initial', [-3., 2.])
def test_death_rebirth_erases_ancestor_conditional_mean_and_variance(monkeypatch, initial):
    spec = ForwardSpec(2.5, .7)
    skeleton = _Tape(poisson=([2],), random=([0.], [0.], [0.]))
    noise = _Tape(normal=([.3], [1.2], [-.4]))
    monkeypatch.setattr(paired.np.random, 'Generator', _Tape)
    raw, rb, work = paired.paired_rollout_labels(spec, .875,
        np.array([2]), np.array([initial]), skeleton, noise)
    a, q = _half(spec)
    assert raw[0] == pytest.approx(_expected(spec, a*1.2-math.sqrt(q)*.4, 0), abs=1e-15)
    assert rb[0] == pytest.approx(_expected(spec, 0, a*a+q), abs=1e-15)
    assert work['accepted_deaths'] == work['conditional_gaussian_death_resets'] == 1
    assert work['accepted_birth_death_events'] == 2
    assert work['continuous_half_step_updates'] == 2
    _assert_counts(work)


def test_rejected_uniformization_proposals_preserve_gaussian_ancestor(monkeypatch):
    spec = ForwardSpec(2.5, .7)
    skeleton = _Tape(poisson=([2],), random=([.9], [.9]))
    noise = _Tape(normal=([.3], [-.4]))
    monkeypatch.setattr(paired.np.random, 'Generator', _Tape)
    raw, rb, work = paired.paired_rollout_labels(spec, .875,
        np.array([2]), np.array([2.]), skeleton, noise)
    a, q = _half(spec)
    assert rb[0] == pytest.approx(_expected(spec, a*a*2, q*(1+a*a)), abs=1e-15)
    assert raw[0] == pytest.approx(_expected(spec,
        a*(a*2+math.sqrt(q)*.3)-math.sqrt(q)*.4, 0), abs=1e-15)
    assert work['accepted_birth_death_events'] == 0
    assert work['potential_uniformization_events'] == 2
    _assert_counts(work)


def test_other_birth_retains_no_projected_coordinate_or_gaussian_variance(monkeypatch):
    spec = ForwardSpec(2.5, .7)
    skeleton = _Tape(poisson=([1],), random=([0.], [1.]))
    noise = _Tape()
    monkeypatch.setattr(paired.np.random, 'Generator', _Tape)
    raw, rb, work = paired.paired_rollout_labels(spec, .875,
        np.array([0]), np.array([0.]), skeleton, noise)
    assert raw[0] == rb[0] == spec.contamination_density
    assert work['conditional_raw_label_variance'] == [0.]
    assert work['raw_normal_draws_total'] == 0
    assert work['terminal_state_counts'] == {'EMPTY': 0, 'OTHER': 1, 'CONTINUOUS': 0}
    _assert_counts(work)


def test_watchdog_aborts_without_terminal_moments_or_truncation(monkeypatch):
    spec = ForwardSpec(2.5, .7)
    skeleton, noise = _Tape(poisson=([65],)), _Tape(normal=([.3],))
    monkeypatch.setattr(paired.np.random, 'Generator', _Tape)
    def forbidden(*args):
        raise AssertionError('terminal moments after watchdog')
    monkeypatch.setattr(paired, 'observation_density', forbidden)
    with pytest.raises(RuntimeError, match='no truncated labels'):
        paired.paired_rollout_labels(spec, .875, np.array([2]), np.array([2.]), skeleton, noise)


def test_zero_rates_preserve_raw_and_rb_but_count_original_zero_noise_draws():
    spec = ForwardSpec(.8, .7, death_rate=0., continuous_rate=0.)
    states, z = np.array([0, 1, 2, 2]), np.array([0., 0., -1., .8])
    raw, rb, work = _call(spec, 0., states, z)
    np.testing.assert_array_equal(raw, observation_density(spec, states, z))
    np.testing.assert_array_equal(raw, rb)
    assert work['raw_half_step_normal_draws'] == 32
    assert work['conditional_raw_label_variance'] == [0., 0., 0., 0.]
    assert work['potential_uniformization_events'] == 0
    _assert_counts(work)


@pytest.mark.parametrize('mean,variance', [(-1.3, .8), (.7, 1.), (2.1, .01), (0., 3.)])
def test_gaussian_first_and_second_moments_against_independent_quadrature(mean, variance):
    spec = ForwardSpec(.8, .7)
    expected, var = paired.conditional_observation_moments(spec, [2], [mean], [variance])
    def label(z):
        return spec.contamination_density+(1-spec.contamination)*.5*_phi(
            spec.observation_value-z, spec.observation_sd**2)
    numerical_mean = quad(lambda z: label(z)*_phi(z-mean, variance), -math.inf, math.inf,
                          epsabs=1e-12)[0]
    numerical_variance = quad(lambda z: (label(z)-numerical_mean)**2*_phi(z-mean, variance),
                              -math.inf, math.inf, epsabs=1e-12)[0]
    assert expected[0] == pytest.approx(numerical_mean, rel=2e-10, abs=1e-12)
    assert var[0] == pytest.approx(numerical_variance, rel=2e-9, abs=1e-12)


def test_tiny_gaussian_variance_is_nonnegative_without_moment_subtraction():
    spec = ForwardSpec(.8, .7)
    variances = np.array([0., 1e-20, 1e-16, 1e-12])
    mean, var = paired.conditional_observation_moments(spec, [2]*4, [.3]*4, variances)
    assert var[0] == 0
    assert np.all(var[1:] > 0)
    slope = ((1-spec.contamination)*.5*_phi(.4, .25)*(.4/.25))
    np.testing.assert_allclose(var[1:]/variances[1:], slope*slope, rtol=1e-10)
    assert np.isfinite(mean).all()


def test_bounded_gaussian_monte_carlo_matches_rb_mean_and_removed_variance():
    # A manufactured no-jump Gaussian law, not a learner/target comparison.
    spec, n = ForwardSpec(.8, .7, death_rate=0.), 20000
    raw, rb, work = _call(spec, .5, np.full(n, 2), np.full(n, -.3))
    var = np.asarray(work['conditional_raw_label_variance'])
    np.testing.assert_array_equal(rb, np.full(n, rb[0]))
    assert abs(raw.mean()-rb[0]) <= 7*math.sqrt(var[0]/n)
    assert raw.var() == pytest.approx(var[0], rel=.08)
    assert raw.var() > rb.var()


def test_paired_raw_marginal_matches_original_forward_simulator_with_jumps():
    spec, n = ForwardSpec(2.5, 1.4), 16000
    state, z = np.full(n, 2), np.full(n, -.4)
    raw, rb, work = _call(spec, .5, state, z)
    old, _ = rollout_labels(spec, .5, state, z, np.random.default_rng(430))
    # Independent bounded samples: seven empirical-standard-error allowance;
    # shared-skeleton pair uses its conditional variance, not independent SE.
    assert abs(raw.mean()-old.mean()) <= 7*math.sqrt((raw.var()+old.var())/n)
    removed = np.asarray(work['conditional_raw_label_variance'])
    assert abs((raw-rb).mean()) <= 7*math.sqrt(removed.sum())/n
    assert np.all(rb >= spec.contamination_density) and np.all(rb <= spec.maximum_label)
    _assert_counts(work)


@pytest.mark.parametrize('states,z', [([0], [1.]), ([3], [0.]), ([True], [0.]),
    ([2.], [0.]), ([2], [complex(1)]), ([2], [math.inf]), ([2], [math.nan]),
    ([[2]], [[0.]]), ([2, 2], [0.]), (np.ma.array([2], mask=[False]), [0.])])
def test_invalid_states_are_rejected(states, z):
    with pytest.raises(ValueError):
        paired.paired_rollout_labels(ForwardSpec(.8, .7), 0., states, z,
            np.random.default_rng(1), np.random.default_rng(2))


@pytest.mark.parametrize('u', [-.1, .1, 1.1, True, np.bool_(False), 0j, math.nan, math.inf])
def test_only_existing_macro_nodes_are_accepted(u):
    with pytest.raises(ValueError):
        _call(ForwardSpec(.8, .7), u, [0], [0.])


def test_rng_identity_and_type_rejected():
    rng = np.random.default_rng(1)
    for skeleton, noise in [(rng, rng), (None, rng), (rng, np.random.RandomState(1))]:
        with pytest.raises(ValueError, match='distinct NumPy generators'):
            paired.paired_rollout_labels(ForwardSpec(.8, .7), 0., [0], [0.], skeleton, noise)


@pytest.mark.parametrize('variances', [[-1.], [math.nan], [math.inf], [1j], [True],
    [0., 0.], np.ma.array([0.], mask=[False])])
def test_moment_variance_validation(variances):
    with pytest.raises(ValueError):
        paired.conditional_observation_moments(ForwardSpec(.8, .7), [2], [0.], variances)


def test_atomic_placeholder_variance_must_be_zero():
    with pytest.raises(ValueError):
        paired.conditional_observation_moments(ForwardSpec(.8, .7), [1], [0.], [.1])


def test_input_arrays_remain_unchanged_and_empty_inputs_are_supported():
    state, z = np.array([0, 1, 2, 2]), np.array([0., 0., -.4, .8])
    before = state.copy(), z.copy()
    _call(ForwardSpec(.8, .7), 0., state, z)
    np.testing.assert_array_equal(state, before[0])
    np.testing.assert_array_equal(z, before[1])
    raw, rb, work = _call(ForwardSpec(.8, .7), 0., [], [])
    assert raw.size == rb.size == 0
    _assert_counts(work)


def test_source_has_no_backward_oracle_guide_learner_or_sampler_imports():
    source = Path(paired.__file__).read_text()
    imports = [node.module for node in ast.walk(ast.parse(source)) if isinstance(node, ast.ImportFrom)]
    assert imports == ['heterodiff.experiments.continuous_forward_labels']
    imported = [item.name for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Import)
                for item in node.names]
    assert set(imported) == {'math', 'numpy'}


def test_saved_terminal_moments_reconstruct_labels_variance_and_prefix_counts():
    spec = ForwardSpec(2.5, 1.4)
    state = np.tile([0, 1, 2, 2], 128)
    z = np.where(state == 2, -.3, 0.)
    raw, rb, work = _call(spec, 0., state, z)
    terminal = work['terminal_gaussian_state']
    expected_raw = observation_density(spec, terminal['states'], terminal['raw_coordinates'])
    expected_rb, expected_var = paired.conditional_observation_moments(
        spec, terminal['states'], terminal['means'], terminal['variances'])
    np.testing.assert_array_equal(raw, expected_raw)
    np.testing.assert_array_equal(rb, expected_rb)
    np.testing.assert_array_equal(work['conditional_raw_label_variance'], expected_var)
    assert work['raw_observation_density_evaluations'] == len(state)
    assert work['rb_observation_mean_evaluations'] == len(state)
    assert work['conditional_variance_evaluations'] == len(state)
    active = sum(s == 2 and v > 0 for s, v in zip(terminal['states'], terminal['variances']))
    assert work['rb_gaussian_convolution_evaluations'] == active
    assert work['conditional_gaussian_second_moment_evaluations'] == active
    for name, rows in work['per_suffix_counts'].items():
        assert sum(rows[:17])+sum(rows[17:]) == work[name]
    _assert_counts(work)
