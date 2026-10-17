"""Independent law tests for the finite-table learning mechanism benchmark."""

import itertools
import math

import numpy as np
import pytest

from heterodiff.evaluation.finite_conditional_benchmark import (
    FiniteBenchmarkSpec,
    FiniteConditionalBenchmark,
)
from heterodiff.experiments import finite_conditional_learning_benchmark as learning


def _oracle(cap=3):
    prototype = FiniteConditionalBenchmark(FiniteBenchmarkSpec(state_cap=cap))
    potential = [.35 * a - .2 * b + .15 * a * b for a, b in prototype.states]
    return FiniteConditionalBenchmark(prototype.spec, potential)


def _exact_likelihoods(oracle, observation):
    h = np.array([oracle.backward_likelihood(t, observation) for t in learning.GRID])
    h[-1] = oracle.observation_likelihood(observation)
    return h


def _perturbed_likelihoods(oracle, observation, magnitude=.015):
    h = _exact_likelihoods(oracle, observation)
    for i, time in enumerate(learning.GRID[:-1]):
        for j, (a, b) in enumerate(oracle.states):
            h[i, j] *= math.exp(magnitude * (1. - time) * (a - 2. * b + (i % 2)))
    return h


@pytest.mark.parametrize("observation", [(0, 0), (0, 1), (1, 0), None])
def test_exact_oracle_likelihoods_recover_independent_terminal_posterior(observation):
    oracle = _oracle()
    h = _exact_likelihoods(oracle, observation)
    terminal, detail = learning.conditional_distribution(oracle, observation, h)
    np.testing.assert_allclose(terminal, oracle.terminal_posterior(observation), rtol=3e-14, atol=3e-16)
    np.testing.assert_allclose(detail['initial'], oracle.conditioned_initial(observation), rtol=3e-15)
    assert detail['harmonic_defect_sum_sup'] < 1e-13
    assert detail['path_and_terminal_TV_upper_bound'] < 1e-12
    for i, kernel in enumerate(detail['transitions']):
        np.testing.assert_allclose(kernel, oracle.doob_transition(learning.GRID[i], learning.GRID[i+1], observation),
                                   rtol=3e-14, atol=3e-16)


@pytest.mark.parametrize("fault", ["shape", "zero", "negative", "nan", "infinity", "terminal"])
def test_likelihood_validation_rejects_invalid_or_non_boundary_values(fault):
    oracle = _oracle()
    h = _exact_likelihoods(oracle, None)
    if fault == "shape":
        h = h[:-1]
    elif fault == "terminal":
        h[-1, 0] = np.nextafter(h[-1, 0], np.inf)
    else:
        h[0, 0] = {"zero": 0., "negative": -1., "nan": np.nan, "infinity": np.inf}[fault]
    with pytest.raises(ValueError):
        learning.conditional_distribution(oracle, None, h)


@pytest.mark.parametrize("grid", [(0., .25, .51, .75, 1.), (0., .5, 1.), (0., .25, .25, .75, 1.)])
def test_query_refined_or_different_grid_is_not_silently_admitted(grid):
    oracle = _oracle()
    h = _exact_likelihoods(oracle, None)
    with pytest.raises(ValueError):
        learning.conditional_distribution(oracle, None, h, grid=grid)


@pytest.mark.parametrize("time_index, message", [(0, 'initial likelihood normalizer'),
                                                (1, 'transition likelihood normalizer')])
def test_positive_but_unrepresentable_subnormal_normalizers_fail_explicitly(time_index, message):
    oracle = _oracle()
    h = _exact_likelihoods(oracle, None)
    h[time_index] = np.nextafter(0., 1.)
    assert np.min(h) > 0
    with pytest.raises(ValueError, match=message):
        learning.conditional_distribution(oracle, None, h)


def _enumerate_path_laws(oracle, observation, h):
    terminal, detail = learning.conditional_distribution(oracle, observation, h)
    base = [oracle.transition(right - left) for left, right in zip(learning.GRID, learning.GRID[1:])]
    g = oracle.observation_likelihood(observation)
    z = oracle.evidence(observation)
    exact_law, approximate_law, ratios = [], [], []
    accumulated_terminal = np.zeros(len(oracle.states))
    for indices in itertools.product(range(len(oracle.states)), repeat=len(learning.GRID)):
        exact = oracle.prior[indices[0]] * g[indices[-1]] / z
        approximate = detail['initial'][indices[0]]
        for i, (start, end) in enumerate(zip(indices, indices[1:])):
            exact *= base[i][start, end]
            approximate *= detail['transitions'][i][start, end]
        log_ratio = math.log(z / detail['initial_normalizer']) - sum(
            detail['harmonic_defects'][i, state] for i, state in enumerate(indices[:-1]))
        assert approximate / exact == pytest.approx(math.exp(log_ratio), rel=4e-14, abs=2e-15)
        exact_law.append(exact)
        approximate_law.append(approximate)
        ratios.append(approximate / exact)
        accumulated_terminal[indices[-1]] += approximate
    np.testing.assert_allclose(accumulated_terminal, terminal, rtol=4e-14, atol=2e-16)
    return np.array(exact_law), np.array(approximate_law), np.array(ratios), terminal, detail


@pytest.mark.parametrize("observation", [(0, 0), (0, 1), (1, 0), None])
def test_path_density_identity_and_tv_bound_by_exhaustive_small_state_paths(observation):
    # Cap one gives exactly three states and 3**5 complete fixed-grid paths.
    oracle = _oracle(cap=1)
    h = _perturbed_likelihoods(oracle, observation)
    exact, approximate, ratio, terminal, detail = _enumerate_path_laws(oracle, observation, h)
    assert exact.sum() == pytest.approx(1., rel=3e-14)
    assert approximate.sum() == pytest.approx(1., rel=3e-14)
    path_tv = float(.5 * np.abs(approximate - exact).sum())
    terminal_tv = float(.5 * np.abs(terminal - oracle.terminal_posterior(observation)).sum())
    e = detail['harmonic_defect_sum_sup']
    assert ratio.min() >= math.exp(-2 * e) - 1e-13
    assert ratio.max() <= math.exp(2 * e) + 1e-13
    assert terminal_tv <= path_tv + 1e-14
    assert path_tv <= detail['path_and_terminal_TV_upper_bound'] + 1e-14
    assert 0 < path_tv < .02
    assert detail['path_and_terminal_TV_upper_bound'] < 1.


def test_time_only_likelihood_scales_cancel_from_actual_twisted_law():
    oracle = _oracle(cap=1)
    h = _perturbed_likelihoods(oracle, (1, 0))
    first, detail = learning.conditional_distribution(oracle, (1, 0), h)
    # A time-only offset changes the raw harmonic defect but not normalized
    # initial/transition laws.  Its bound can be looser without implying drift.
    h[:-1] *= np.array([.3, 4., .8, 2.])[:, None]
    second, rescaled = learning.conditional_distribution(oracle, (1, 0), h)
    np.testing.assert_allclose(first, second, rtol=2e-15, atol=2e-16)
    np.testing.assert_allclose(detail['initial'], rescaled['initial'], rtol=2e-15)
    for original, scaled in zip(detail['transitions'], rescaled['transitions']):
        np.testing.assert_allclose(original, scaled, rtol=2e-15)
    assert rescaled['harmonic_defect_sum_sup'] > detail['harmonic_defect_sum_sup']
    assert rescaled['path_and_terminal_TV_upper_bound'] == 1.


def test_changed_initializer_is_not_cancelled_by_later_row_normalization():
    oracle = _oracle(cap=1)
    exact = _exact_likelihoods(oracle, (1, 0))
    altered = exact.copy()
    altered[0] *= np.array([1., 1.4, .7])
    original, first = learning.conditional_distribution(oracle, (1, 0), exact)
    approximation, second = learning.conditional_distribution(oracle, (1, 0), altered)
    for original_kernel, altered_kernel in zip(first['transitions'], second['transitions']):
        np.testing.assert_array_equal(original_kernel, altered_kernel)
    assert .5 * np.abs(original - approximation).sum() > .005


def test_cubic_gate_counterexample_has_nonzero_first_order_limit_and_divergence():
    diagnostic = learning.gate_boundary_diagnostic()
    np.testing.assert_allclose(diagnostic['first_order_limit'], [3., 0.], rtol=0., atol=1e-15)
    rows = diagnostic['rows']
    last = rows[-1]
    assert last['remaining_time'] == 1e-5
    assert last['linear_scaled_correction'][0] == pytest.approx(3., abs=3e-4)
    assert abs(last['linear_scaled_correction'][1]) < 2e-5
    assert last['cubic_scaled_correction'][0] > 1e10
    assert last['cubic_scaled_correction'][0] / rows[-2]['cubic_scaled_correction'][0] == pytest.approx(100., rel=.002)
    assert diagnostic['legacy_gate_changed'] is False
    assert diagnostic['global_linear_gate_realizability_claimed'] is False


@pytest.mark.parametrize("steps", [0, 2049, True, 1.5])
def test_bad_steps_rejected_before_work(steps):
    with pytest.raises(ValueError):
        learning.run_benchmark(steps=steps)


@pytest.mark.parametrize("seconds", [0, 301, True, 1.5])
def test_bad_time_limits_rejected_before_work(seconds):
    with pytest.raises(ValueError):
        learning.run_benchmark(maximum_seconds=seconds)


@pytest.fixture(scope='module')
def small_run():
    return learning.run_benchmark(steps=1, maximum_seconds=120)


def test_one_update_smoke_completes_all_prespecified_cases_and_work(small_run):
    assert small_run['decision'] == 'FINITE_CONDITIONAL_BENCHMARK_COMPLETED_NOT_FULL_MODEL_QUALIFICATION'
    assert small_run['scenario_count'] == 3
    assert small_run['observation_case_count'] == 12
    assert small_run['grid'] == list(learning.GRID)
    assert small_run['steps_per_learned_route'] == 1
    updates = 0
    for scenario in small_run['results']:
        assert len(scenario['states']) == 10
        assert [case['observation'] for case in scenario['cases']] == [[0, 0], [0, 1], [1, 0], 'OVERFLOW']
        assert sum(scenario['initial_prior']) == pytest.approx(1.)
        for case in scenario['cases']:
            assert case['evidence'] > 0
            assert sum(case['target_terminal_distribution']) == pytest.approx(1.)
            assert case['exact_oracle_control']['terminal_TV'] < 2e-12
            assert len(case['curves']['guide-only']) == 1
            assert case['curves']['guide-only'][0]['step'] == 0
            for method in learning.METHODS[1:]:
                curve = case['curves'][method]
                assert [point['step'] for point in curve] == [0, 1]
                assert curve[-1]['population_logistic_loss'] <= curve[0]['population_logistic_loss'] + 1e-12
                work = case['work'][method]
                assert work['optimizer_updates'] == 1
                assert work['population_class_state_terms_per_update'] == 80
                assert work['optimizer_update_population_class_state_terms'] == 80
                assert work['objective_evaluations_including_final_diagnostic'] == 2
                assert work['all_objective_evaluation_population_class_state_terms'] == 160
                assert work['work_count_scope'] == 'LEARNED_OBJECTIVE_ONLY_ORACLE_PREPARATION_AND_LAW_EVALUATION_SEPARATE'
                assert work['trainable_scalars'] == 41
                updates += work['optimizer_updates']
                for point in curve:
                    assert point['population_logistic_excess'] >= 0
                    assert point['maximum_absolute_ungated_residual'] <= learning.RESIDUAL_BOUND
                    assert point['terminal_TV'] <= point['path_and_terminal_TV_upper_bound'] + 2e-12
                    assert point['terminal_KL_target_to_approximation'] >= 0
                    assert sum(point['predicted_terminal_distribution']) == pytest.approx(1.)
    assert updates == 24


def test_smoke_report_states_scientific_scope_without_claiming_neural_qualification(small_run):
    scope = small_run['scope']
    assert scope['cpu_only'] is True
    assert scope['synthetic_only'] is True
    assert scope['population_risk_not_sample_generalization'] is True
    assert scope['fixed_toy_BASE_not_trained_BASE'] is True
    assert scope['finite_matrix_reference_not_exact_arithmetic'] is True
    for key in ('two_domain_neural_learner_qualified', 'continuous_fiber_or_Heun_qualified',
                'legacy_gate_or_objective_changed', 'paid_or_gpu_jobs_launched',
                'F105_or_real_data_used', 'method_superiority_preasserted'):
        assert scope[key] is False


def test_cpu_numerical_policy_is_restored_even_on_error():
    import torch
    old_threads = torch.get_num_threads()
    old_deterministic = torch.are_deterministic_algorithms_enabled()
    old_warn = torch.is_deterministic_algorithms_warn_only_enabled()
    with pytest.raises(RuntimeError, match='deliberate'):
        with learning._cpu_policy(torch):
            assert torch.get_num_threads() == 1
            assert torch.are_deterministic_algorithms_enabled()
            raise RuntimeError('deliberate')
    assert torch.get_num_threads() == old_threads
    assert torch.are_deterministic_algorithms_enabled() == old_deterministic
    assert torch.is_deterministic_algorithms_warn_only_enabled() == old_warn
