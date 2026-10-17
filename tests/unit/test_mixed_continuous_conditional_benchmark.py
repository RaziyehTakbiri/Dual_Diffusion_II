from fractions import Fraction
from dataclasses import replace
import math

import numpy as np
import pytest
import torch

from heterodiff.data.two_domain_factorized_state import FactoredEvent, PhysioStateKey
from heterodiff.evaluation.continuous_fiber_conditional_benchmark import (
    ContinuousFiberConditionalBenchmark, MixedGaussianLaw,
)
from heterodiff.experiments.mixed_continuous_conditional_benchmark import (
    BenchmarkBudget, IndependentHPotential, METHODS, _fixture,
    category, discrepancy, materialize, run_benchmark,
)
from heterodiff.processes.factorized_hybrid_sampler import LearnedFactorizedSampler


@pytest.fixture(autouse=True)
def one_thread():
    old = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(old)


@pytest.mark.parametrize('field,value', [
    ('oracle_draws', 0), ('neural_draws', True), ('conditional_steps', 33),
    ('pairs_per_step', 5), ('maximum_seconds', 1201), ('oracle_draws', 1.5),
])
def test_invalid_budgets(field, value):
    with pytest.raises(ValueError):
        BenchmarkBudget(**{field: value})


def test_actual_fixture_and_independent_parameters_agree():
    ref, oracle, key, base, model, _, obs = _fixture()
    assert ref.parameters.reference_cap == 1
    assert ref.parameters.observation_cap == 1
    assert float(ref.reference.mass(key).as_fraction()) == oracle.spec.type_probabilities[1]
    assert ref.parameters.reference_count_mean == oracle.spec.theta
    assert ref.parameters.death_rate == oracle.spec.death_rate
    assert ref.parameters.observation_contamination == oracle.spec.contamination
    assert ref.parameters.observation_log_value_sd == oracle.spec.observation_sd
    assert ref.schedule.clean_hold == 0.
    assert obs[0].coordinate == oracle.spec.observation_value
    assert model.residual_gate_policy == 'LINEAR_ACTIVE_TIME_V1'
    assert all(torch.count_nonzero(p) == 0 for p in base.parameters())


@pytest.mark.parametrize('state_kind', ['empty', 'selected', 'other-continuous', 'atomic'])
def test_exact_h_obeys_real_sampler_fiber_interface(state_kind):
    _, oracle, key, _, _, _, _ = _fixture()
    states = {'empty': (), 'selected': (FactoredEvent(key, .4),),
              'other-continuous': (FactoredEvent(PhysioStateKey(4, 'HR', 'POSITIVE'), .9),),
              'atomic': (FactoredEvent(PhysioStateKey(3, 'MechVent', 'ATOMIC', Fraction(1))),)}
    state = states[state_kind]
    potential = IndependentHPotential(oracle, key)
    value, rows = potential.value_grad(.3, state)
    assert math.isfinite(value) and value <= potential.upper_value_bound
    assert value == pytest.approx(potential.value(.3, state), abs=1e-14)
    assert tuple(map(len, rows)) == tuple(event.key.dimension for event in state)
    if state_kind == 'other-continuous':
        assert rows == ((0.,),)
    if state_kind == 'selected':
        h = 1e-5
        slope = (potential.value(.3, (FactoredEvent(key, .4+h),)) -
                 potential.value(.3, (FactoredEvent(key, .4-h),)))/(2*h)
        assert rows[0][0] == pytest.approx(slope, abs=1e-9)


def test_other_materialization_preserves_actual_key_and_fiber():
    ref, _, key, _, _, _, _ = _fixture()
    law = MixedGaussianLaw(0., 1., ())
    rng = np.random.default_rng(51)
    for _ in range(64):
        state = materialize(law, rng, ref, key)
        assert len(state) == 1 and state[0].key != key
        assert category(state, key) == 'OTHER'
        assert state[0].key.domain_id == 'R3-PHYS'
        assert (state[0].coordinate is not None) == bool(state[0].key.dimension)


def test_h_control_runs_actual_sampler_and_replays():
    ref, oracle, key, _, _, _, _ = _fixture()
    sampler = LearnedFactorizedSampler(ref, IndependentHPotential(oracle, key), (0., .5, 1.),
        initializer=lambda rng: materialize(oracle.conditioned_initial(), rng, ref, key))
    a = sampler.sample_path(run_seed=91, record_id=b'independent-control')
    b = sampler.sample_path(run_seed=91, record_id=b'independent-control')
    assert a == b
    assert all(len(state) <= 1 for state in a.states)


def test_h_only_control_rejects_nonzero_base():
    _, oracle, key, _, _, _, _ = _fixture()
    tilted = ContinuousFiberConditionalBenchmark(replace(oracle.spec, potential=(0., .2, .3)))
    with pytest.raises(ValueError, match='zero BASE'):
        IndependentHPotential(tilted, key)


def test_h_upper_bound_at_terminal_density_maximum():
    _, oracle, key, _, _, _, _ = _fixture()
    potential = IndependentHPotential(oracle, key)
    value, gradient = potential.value_grad(1., (FactoredEvent(key, .7),))
    assert value <= potential.upper_value_bound
    assert gradient == ((0.,),)


def test_statistics_are_joint_indicators_not_empirical_tv():
    _, oracle, key, _, _, _, _ = _fixture()
    states = [(), (FactoredEvent(key, 0.),)]
    report = discrepancy(states, key, oracle.terminal_posterior())
    assert report['category_probabilities'] == [.5, 0., .5]
    assert report['joint_cdf_empirical'][-1] == .5
    assert report['continuous_TV_or_KL_estimated'] is False
    assert report['posterior_accuracy_proved'] is False
    with pytest.raises(ValueError):
        discrepancy([], key, oracle.terminal_posterior())
    with pytest.raises(ValueError):
        category((FactoredEvent(key, 0.),)*2, key)


def test_small_end_to_end_all_five_routes_no_quality_claim():
    result = run_benchmark(BenchmarkBudget(oracle_draws=2, neural_draws=1,
        conditional_steps=1, pairs_per_step=1, maximum_seconds=60))
    assert len(result['routes']) == 5
    neural = result['routes'][-2:]
    assert [r['method'] for r in neural] == list(METHODS)
    assert neural[0]['sampler_initializer'].startswith('UNCAPPED_FUTURE_REFERENCE')
    assert neural[1]['sampler_initializer'].startswith('ZERO_CLOCK_OBSERVATION')
    for route in neural:
        assert route['updates'][0]['changed_parameter_elements'] > 0
        assert route['population']['required_residual_gate_policy'] == 'LINEAR_ACTIVE_TIME_V1'
        assert route['metrics']['draw_count'] == 1
        assert route['base_model_trained_in_this_comparison'] is False
    assert result['scope']['actual_mixed_neural_models_used']
    assert result['scope']['actual_hybrid_sampler_used']
    assert not result['scope']['full_posterior_or_statistical_superiority_claimed']
    assert result['scope']['discarded_failed_samples'] == 0
