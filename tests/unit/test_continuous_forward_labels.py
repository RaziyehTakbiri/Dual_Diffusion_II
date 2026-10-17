"""Independent deterministic forward-law tests, not a learning experiment."""

from copy import deepcopy
import ast
import math
from pathlib import Path

import numpy as np
import pytest

from heterodiff.experiments import continuous_forward_labels as forward


class _Tape:
    """Deterministic random tape; zero-size calls consume no tape item."""
    def __init__(self, *, normal=(), poisson=(), random=()):
        self.items = {key: list(values) for key, values in
            [('normal', normal), ('poisson', poisson), ('random', random)]}
        self.calls = []

    def _take(self, kind, size):
        self.calls.append((kind, size))
        if size == 0:
            return np.empty(0, dtype=int if kind == 'poisson' else float)
        assert self.items[kind], (kind, size, 'unexpected RNG consumption')
        result = np.asarray(self.items[kind].pop(0))
        assert result.shape == (size,), (kind, size, result.shape)
        return result.copy()

    def normal(self, size):
        return self._take('normal', size)

    def poisson(self, rate, size):
        assert rate > 0
        return self._take('poisson', size)

    def random(self, size):
        return self._take('random', size)


def _manual_density(spec, state, z):
    c = spec.contamination*math.exp(-1)*spec.selected_probability*math.exp(-spec.observation_value**2/2)/math.sqrt(2*math.pi)
    return c+(0. if state != 2 else (1-spec.contamination)*.5
        *math.exp(-.5*((spec.observation_value-z)/spec.observation_sd)**2)
        /(spec.observation_sd*math.sqrt(2*math.pi)))


def _half_coefficients(spec):
    clock = spec.continuous_rate/16
    return 1-clock/2+clock*clock/8, math.sqrt(clock)*(1-clock/4)


@pytest.mark.parametrize('probability', [.2, .8])
def test_terminal_label_is_whole_observation_density_without_double_key_probability(probability):
    spec = forward.ForwardSpec(2.5, .7, selected_probability=probability)
    states, coordinates = np.array([0, 1, 2, 2]), np.array([0., 0., .7, -1.])
    labels = forward.observation_density(spec, states, coordinates)
    expected = [_manual_density(spec, state, z) for state, z in zip(states, coordinates)]
    np.testing.assert_allclose(labels, expected, rtol=2e-15, atol=0.)
    assert labels[0] == labels[1] == spec.contamination_density
    assert labels[2] == spec.maximum_label
    assert labels.min() > 0 and labels.max() <= spec.maximum_label


def test_surviving_coordinate_receives_two_independent_heun_half_steps(monkeypatch):
    spec = forward.ForwardSpec(2.5, .7)
    tape = _Tape(normal=([.3], [-.4]), poisson=([0],))
    monkeypatch.setattr(forward.np.random, 'Generator', _Tape)
    states, coordinates = np.array([2]), np.array([2.])
    original = deepcopy((states, coordinates))
    labels, record = forward.rollout_labels(spec, .875, states, coordinates, tape)
    a, noise = _half_coefficients(spec)
    final_z = a*(a*2.+noise*.3)+noise*(-.4)
    assert labels[0] == pytest.approx(_manual_density(spec, 2, final_z), abs=1e-15)
    assert record['potential_uniformization_events'] == record['accepted_birth_death_events'] == 0
    assert record['continuous_half_step_updates'] == 2
    assert record['terminal_state_counts'] == {'EMPTY': 0, 'OTHER': 0, 'CONTINUOUS': 1}
    for observed, before in zip((states, coordinates), original):
        np.testing.assert_array_equal(observed, before)
    assert all(not values for values in tape.items.values())


def test_middle_phase_birth_gets_fresh_mark_and_only_right_heun_step(monkeypatch):
    spec = forward.ForwardSpec(2.5, .7)
    tape = _Tape(normal=([1.2], [-.4]), poisson=([1],), random=([0.], [0.]))
    monkeypatch.setattr(forward.np.random, 'Generator', _Tape)
    labels, record = forward.rollout_labels(spec, .875, np.array([0]), np.array([0.]), tape)
    a, noise = _half_coefficients(spec)
    assert labels[0] == pytest.approx(_manual_density(spec, 2, a*1.2-noise*.4), abs=1e-15)
    assert record['accepted_birth_death_events'] == 1
    assert record['continuous_half_step_updates'] == 1


@pytest.mark.parametrize('initial_coordinate', [-3., 2.])
def test_death_and_rebirth_in_same_macro_erase_ancestor_not_just_change_category(monkeypatch, initial_coordinate):
    spec = forward.ForwardSpec(2.5, .7)
    tape = _Tape(normal=([.3], [1.2], [-.4]), poisson=([2],), random=([0.], [0.], [0.]))
    monkeypatch.setattr(forward.np.random, 'Generator', _Tape)
    labels, record = forward.rollout_labels(spec, .875, np.array([2]), np.array([initial_coordinate]), tape)
    a, noise = _half_coefficients(spec)
    assert labels[0] == pytest.approx(_manual_density(spec, 2, a*1.2-noise*.4), abs=1e-15)
    assert record['accepted_birth_death_events'] == 2
    assert record['potential_uniformization_events'] == 2
    assert record['continuous_half_step_updates'] == 2


def test_uniformization_self_transitions_do_not_reset_the_coordinate(monkeypatch):
    spec = forward.ForwardSpec(2.5, .7)
    tape = _Tape(normal=([.3], [-.4]), poisson=([2],), random=([.9], [.9]))
    monkeypatch.setattr(forward.np.random, 'Generator', _Tape)
    labels, record = forward.rollout_labels(spec, .875, np.array([2]), np.array([2.]), tape)
    a, noise = _half_coefficients(spec)
    assert labels[0] == pytest.approx(_manual_density(spec, 2, a*(a*2.+noise*.3)-noise*.4), abs=1e-15)
    assert record['accepted_birth_death_events'] == 0
    assert record['potential_uniformization_events'] == 2


def test_watchdog_refuses_whole_call_instead_of_returning_truncated_labels(monkeypatch):
    spec = forward.ForwardSpec(2.5, .7)
    tape = _Tape(normal=([.3],), poisson=([65],))
    monkeypatch.setattr(forward.np.random, 'Generator', _Tape)
    def forbidden(*args):
        raise AssertionError('no terminal labels may be returned after truncation')
    monkeypatch.setattr(forward, 'observation_density', forbidden)
    with pytest.raises(RuntimeError, match='no truncated labels'):
        forward.rollout_labels(spec, .875, np.array([2]), np.array([2.]), tape)


def test_terminal_queries_use_no_randomness_and_preserve_all_input_rows():
    spec = forward.ForwardSpec(.8, .7)
    rng = np.random.default_rng(51)
    before = deepcopy(rng.bit_generator.state)
    states, coordinates = np.array([0, 1, 2]), np.array([0., 0., -.3])
    labels, record = forward.rollout_labels(spec, 1., states, coordinates, rng)
    assert rng.bit_generator.state == before
    np.testing.assert_array_equal(labels, forward.observation_density(spec, states, coordinates))
    assert record['macro_intervals_per_suffix'] == 0
    assert record['forward_suffix_count'] == 3
    assert record['continuous_half_step_updates'] == 0
    assert record['backward_likelihood_or_score_queried'] is False
    assert record['conditional_endpoint_sampler_used'] is False


def test_zero_rates_leave_states_and_coordinates_unchanged_in_distribution():
    spec = forward.ForwardSpec(.8, .7, death_rate=0., continuous_rate=0.)
    states, coordinates = np.array([0, 1, 2, 2]), np.array([0., 0., -1., .8])
    labels, record = forward.rollout_labels(spec, 0., states, coordinates, np.random.default_rng(10))
    np.testing.assert_array_equal(labels, forward.observation_density(spec, states, coordinates))
    assert record['accepted_birth_death_events'] == record['potential_uniformization_events'] == 0
    assert record['terminal_state_counts'] == {'EMPTY': 1, 'OTHER': 1, 'CONTINUOUS': 2}


def test_balanced_input_design_is_nested_under_identical_rng_seed():
    small = forward.design_states(1024, np.random.default_rng(11))
    large = forward.design_states(8192, np.random.default_rng(11))
    for short, long in zip(small, large):
        np.testing.assert_array_equal(short, long[:1024])
    np.testing.assert_array_equal(large[0], np.tile([0, 1, 2, 2], 2048))
    assert np.all(large[1][large[0] != 2] == 0)
    assert np.all(abs(large[1][large[0] == 2]) < 4.5)


@pytest.mark.parametrize('case', ['masked_state', 'masked_coordinate', 'boolean_state',
    'float_state', 'unknown_state', 'atom_coordinate', 'complex_coordinate', 'nan', 'shape'])
def test_invalid_projected_states_are_refused(case):
    states, coordinate = np.array([0, 1, 2]), np.array([0., 0., 1.])
    if case == 'masked_state': states = np.ma.array(states, mask=[False, False, True])
    elif case == 'masked_coordinate': coordinate = np.ma.array(coordinate, mask=[False, False, True])
    elif case == 'boolean_state': states = states > 0
    elif case == 'float_state': states = states.astype(float)
    elif case == 'unknown_state': states[-1] = 3
    elif case == 'atom_coordinate': coordinate[1] = 1.
    elif case == 'complex_coordinate': coordinate = coordinate.astype(complex)
    elif case == 'nan': coordinate[-1] = math.nan
    else: coordinate = coordinate[:, None]
    with pytest.raises(ValueError):
        forward.validate_states(states, coordinate)


@pytest.mark.parametrize('time', [True, .2, -1., 1.1, math.nan])
def test_nonmacro_times_are_refused(time):
    with pytest.raises(ValueError):
        forward.rollout_labels(forward.ForwardSpec(.8, .7), time, np.array([0]),
            np.array([0.]), np.random.default_rng(1))


def test_forward_module_has_no_backward_oracle_or_sampler_import():
    tree = ast.parse(Path(forward.__file__).read_text())
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    imports += [name.name for node in ast.walk(tree) if isinstance(node, ast.Import) for name in node.names]
    assert not any('heterodiff' in name or 'scipy' in name or 'torch' in name for name in imports if name)


@pytest.mark.parametrize('theta,y', [(.8, .7), (2.5, 1.4)])
@pytest.mark.parametrize('method', ['association-aware-guide-plus-residual', 'unified-direct-conditioner'])
def test_vectorized_known_baseline_matches_prior_independent_guide_formula(theta, y, method):
    # The old helper is imported only in this test, never by the forward module.
    from heterodiff.evaluation.continuous_fiber_conditional_benchmark import ContinuousFiberSpec
    from heterodiff.evaluation.continuous_fiber_initialization_diagnostic import ContinuousFiberInitializationDiagnostic
    spec = forward.ForwardSpec(theta, y)
    previous_spec = ContinuousFiberSpec(theta=theta, observation_value=y,
        type_probabilities=(1-spec.selected_probability, spec.selected_probability))
    guide = ContinuousFiberInitializationDiagnostic(previous_spec)
    states = np.array([0, 1, 2, 2, 2, 2, 2])
    coordinates = np.array([0., 0., -4.5, -2., 0., 1.5, 4.5])
    original = deepcopy((states, coordinates))
    for u in forward.GRID:
        result = forward.baseline_rows(spec, u, states, coordinates, method)
        clock = u if method == 'association-aware-guide-plus-residual' else 1.
        expected = [guide.uncapped_log_likelihood_derivatives(clock,
            ('EMPTY', 'OTHER', 'CONTINUOUS')[state], float(z) if state == 2 else None)
            for state, z in zip(states, coordinates)]
        for name, source in [('value', 'log_likelihood'), ('gradient', 'gradient'), ('hessian', 'hessian')]:
            np.testing.assert_allclose(result[name], [row[source] for row in expected],
                atol=2e-13, rtol=2e-13)
        assert np.all(np.exp(result['value']) >= spec.contamination_density*(1-2e-14))
        assert np.all(np.exp(result['value']) <= spec.maximum_label*(1+2e-14))
        np.testing.assert_array_equal(result['gradient'][:2], [0., 0.])
        np.testing.assert_array_equal(result['hessian'][:2], [0., 0.])
        if u == 1. or method == 'unified-direct-conditioner':
            np.testing.assert_allclose(np.exp(result['value']),
                forward.observation_density(spec, states, coordinates), atol=2e-16, rtol=2e-14)
    for actual, before in zip((states, coordinates), original):
        np.testing.assert_array_equal(actual, before)


@pytest.mark.parametrize('method,time', [('unknown', 0.), ('association-aware-guide-plus-residual', .2),
    ('unified-direct-conditioner', True), ('unified-direct-conditioner', math.nan)])
def test_known_offset_refuses_undeclared_method_or_macro_time(method, time):
    with pytest.raises(ValueError):
        forward.baseline_rows(forward.ForwardSpec(.8, .7), time, np.array([0]), np.array([0.]), method)
