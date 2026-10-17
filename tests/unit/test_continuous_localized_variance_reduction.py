"""Independent runner tests: manufactured paired labels and no optimizer runs."""
import builtins
from copy import deepcopy
import json
import math
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from heterodiff.experiments import continuous_localized_variance_reduction as runner


def test_fixed_roster_and_matched_work_claims():
    spec = runner.specification()
    assert spec['route_count'] == 2*3*2*2*2 == 48
    assert spec['fit_count'] == spec['route_count']*8 == 384
    assert spec['dataset_pair_count'] == 2*3*8 == 48
    assert spec['unique_training_skeletons'] == 48*8192 == 393216
    assert spec['unique_validation_skeletons'] == 48*4096 == 196608
    assert spec['unique_total_skeletons'] == 589824
    assert spec['nested_budgets'] == (1024, 8192) and spec['seeds'] == (11, 29, 47)
    assert spec['fit'] == {'family_cells': 32, 'coefficients': 35, 'smoothness': 1e-4,
        'ridge': 1e-6, 'physical_box': '2*log(M/c)', 'initial': 'ZERO',
        'optimizer': 'UNCHANGED_fit_likelihood_L_BFGS_B', 'maxiter': 200,
        'maxls': 30, 'ftol': 1e-12, 'gtol': 1e-7}
    assert spec['raw_arm_is_new_paired_control_not_old_archive'] is True
    assert spec['paired_generation_cost_reported_once_not_standalone_arm_timings'] is True
    assert spec['equal_flops_random_draws_wall_time_or_actual_optimizer_evaluations_claimed'] is False
    assert spec['primary_validation_labels'] == 'SHARED_INDEPENDENT_RAO_BLACKWELL'
    assert spec['secondary_validation_labels'] == 'SHARED_INDEPENDENT_RAW'
    assert spec['oracle_or_validation_selects_settings_or_stopping'] is False
    assert spec['tolerances'] == {'value': (2e-6, 2e-5), 'gradient': (2e-5, 2e-4), 'hessian': (1e-4, 1e-3)}
    assert runner.UNIQUE_NOISE_COMPARISONS*len(runner.ARMS) == 192
    assert json.loads(runner.payload(spec))['fit_count'] == 384


def test_hoeffding_union_algebra_and_operator_readback():
    x = np.zeros((8, 35))
    x[np.arange(8), np.arange(8)] = 1.
    d = {'value': x[:3].copy(), 'gradient': 2*x[:3], 'hessian': -3*x[:3]}
    report = runner.derivative_noise_bound(x, 2., 1., d)
    log_union = math.log(2*35*96*2/.05)
    gradient = .5/8*math.sqrt(.5*8*log_union)
    box = 2*math.log(2.)
    radius = min(gradient/1e-6, 2*box*math.sqrt(35))
    assert report['gradient_noise_l2_bound'] == pytest.approx(gradient)
    assert report['coefficient_distance_bound_with_box_cap'] == pytest.approx(radius)
    for key, scale in (('value', 1.), ('gradient', 2.), ('hessian', 3.)):
        assert report['derivative_responses'][key]['maximum_probe_error_bound'] == pytest.approx(scale*radius)
        assert report['derivative_responses'][key]['rms_probe_error_bound'] == pytest.approx(scale*radius/math.sqrt(3))
    repeated = runner.derivative_noise_bound(np.tile(x, (2, 1)), 2., 1., d)
    assert repeated['gradient_noise_l2_bound'] == pytest.approx(gradient/math.sqrt(2))
    assert report['optimizer_error_bias_and_floating_point_not_included'] is True
    assert report['raw_and_rb_share_conservative_bound'] is True
    assert report['floating_point_interval_certificate'] is False


@pytest.mark.parametrize('kind', ('mask', 'nan', 'complex', 'width', 'empty', 'bool_bound',
    'string_bound', 'unordered', 'missing_derivative', 'derivative_mask', 'derivative_nan', 'derivative_width'))
def test_noise_bound_rejects_ambiguous_or_invalid_inputs(kind):
    x = np.ones((4, 35))/35
    d = {k: x.copy() for k in runner.TOLERANCES}
    maximum, minimum = 2., 1.
    if kind == 'mask': x = np.ma.array(x)
    elif kind == 'nan': x[0, 0] = np.nan
    elif kind == 'complex': x = x.astype(complex)
    elif kind == 'width': x = np.zeros((4, 34))
    elif kind == 'empty': x = np.zeros((0, 35))
    elif kind == 'bool_bound': maximum = True
    elif kind == 'string_bound': maximum = '2'
    elif kind == 'unordered': minimum = 2.
    elif kind == 'missing_derivative': del d['gradient']
    elif kind == 'derivative_mask': d['gradient'] = np.ma.array(x)
    elif kind == 'derivative_nan': d['gradient'][0, 0] = np.nan
    elif kind == 'derivative_width': d['gradient'] = np.zeros((4, 34))
    with pytest.raises(ValueError):
        runner.derivative_noise_bound(x, maximum, minimum, d)


def test_make_dataset_separates_rng_streams_preserves_design_and_binds_joint_payload(monkeypatch):
    monkeypatch.setattr(runner, 'BUDGETS', (8, 16))
    monkeypatch.setattr(runner, 'VALIDATION_SIZE', 8)
    calls = []
    def paired(spec, u, states, z, skeleton_rng, noise_rng):
        assert skeleton_rng is not noise_rng
        raw = skeleton_rng.uniform(.1, .2, len(states))
        rb = noise_rng.uniform(.1, .2, len(states))
        calls.append((u, states.copy(), z.copy(), raw.copy(), rb.copy()))
        return raw, rb, {'conditional_raw_label_variance': [.001]*len(states),
            'per_suffix_counts': {'events': list(range(len(states)))},
            'terminal_gaussian_state': {'states': states.tolist(), 'means': z.tolist(), 'variances': [0.]*len(states)},
            'same_jump_skeleton': True, 'forward_suffix_count': len(states)}
    monkeypatch.setattr(runner, 'paired_rollout_labels', paired)
    spec = runner.ForwardSpec(.8, .7)
    first = runner.make_dataset(spec, 0, 11, 0, 0)
    again = runner.make_dataset(spec, 0, 11, 0, 0)
    valid = runner.make_dataset(spec, 0, 11, 0, 1)
    assert first['payload_sha256'] == again['payload_sha256'] != valid['payload_sha256']
    expected = runner.design_states(16, np.random.default_rng(np.random.SeedSequence([20260913, 0, 11, 0, 0, 0])))
    assert np.array_equal(first['states'], expected[0]) and np.array_equal(first['coordinates'], expected[1])
    assert first['rng_namespace'] == [20260913, 731, 0, 11, 0, 0]
    assert first['payload_sha256'] == runner.array_digest(expected[0], expected[1],
        np.array(first['RAW']), np.array(first['RAO_BLACKWELL']), np.array(first['conditional_raw_label_variance']))
    assert not np.array_equal(first['RAW'], first['RAO_BLACKWELL'])
    assert first['work']['forward_suffix_count'] == 16
    assert 'conditional_raw_label_variance' not in first['work']
    assert first['per_suffix_counts']['events'] == list(range(16))
    assert json.loads(runner.payload(first)) == first


@pytest.fixture
def manufactured_training(monkeypatch):
    monkeypatch.setattr(runner, 'BUDGETS', (8, 16))
    monkeypatch.setattr(runner, 'VALIDATION_SIZE', 8)
    fit_calls, data_calls = [], []
    def data(spec, scenario, seed, node, split):
        n = 16 if split == 0 else 8
        s = np.tile(np.array((0, 1, 2, 2), dtype=np.int64), n//4)
        z = np.zeros(n)
        z[s == 2] = np.linspace(-1., 1., n//2)+(scenario+seed+node+split)*1e-5
        raw = np.full(n, .125+(seed+node+split)*1e-5)
        rb = raw+.01
        v = np.full(n, .001)
        data_calls.append((scenario, seed, node, split))
        return {'states': s.tolist(), 'coordinates': z.tolist(), 'RAW': raw.tolist(), 'RAO_BLACKWELL': rb.tolist(),
            'conditional_raw_label_variance': v.tolist(), 'per_suffix_counts': {'proposals': list(range(n)), 'normal_draws': [2]*n},
            'work': {'forward_suffix_count': n, 'manufactured': True}, 'paired_generation_seconds': 0.,
            'rng_namespace': [scenario, seed, node, split], 'design_sha256': runner.array_digest(s, z),
            'payload_sha256': runner.array_digest(s, z, raw, rb, v)}
    def baseline(spec, u, states, z, method):
        return {'value': np.full(len(states), -2.)}
    def fit(x, labels, b, tau, maximum, minimum, roughness):
        fit_calls.append({'x': x.copy(), 'labels': labels.copy(), 'b': b.copy(), 'tau': tau,
            'maximum': maximum, 'minimum': minimum, 'roughness': roughness.copy()})
        bound = 2*math.log(maximum/minimum)
        a = np.full(35, float(np.mean(labels))/10)
        return SimpleNamespace(real_absolute_bound=max(abs(a))), {
            'physical_coefficients': a.tolist(), 'physical_coefficient_bound': bound,
            'coefficients': (a/tau).tolist(), 'quotient_coefficient_bound': bound/tau,
            'solver_success': len(fit_calls) % 5 != 0, 'projected_gradient_max_abs': .001,
            'manufactured_no_optimizer_run': True}
    monkeypatch.setattr(runner, 'make_dataset', data)
    monkeypatch.setattr(runner, 'baseline_rows', baseline)
    monkeypatch.setattr(runner, 'fit_likelihood', fit)
    return fit_calls, data_calls


def test_training_pairing_common_validation_and_all_failure_flags_retained(monkeypatch, manufactured_training):
    calls, data_calls = manufactured_training
    original_import = builtins.__import__
    def forbid_oracle(name, *args, **kwargs):
        if name.startswith('heterodiff.evaluation') or name == 'heterodiff.experiments.continuous_residual_capacity':
            raise AssertionError('backward target imported before all fits freeze')
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', forbid_oracle)
    datasets, frozen = [], []
    routes, records = runner.train_all(on_dataset=lambda r: datasets.append(deepcopy(r)),
        on_frozen=lambda r: frozen.append(deepcopy(r)))
    assert len(calls) == 384 and len(routes) == len(frozen) == 48
    assert len(records) == len(datasets) == 48 and len(data_calls) == len(set(data_calls)) == 96
    index = {(r['scenario'], r['seed'], r['method'], r['train_budget'], r['arm']): r for r in routes}
    for row in routes:
        paired = index[row['scenario'], row['seed'], row['method'], row['train_budget'], 'RAW' if row['arm'] == 'RAO_BLACKWELL' else 'RAO_BLACKWELL']
        for node, other in zip(row['nodes'], paired['nodes']):
            for key in ('design_prefix_sha256', 'paired_dataset_payload_sha256', 'matched_skeleton_prefix_work'):
                assert node[key] == other[key]
            assert node['training_labels_sha256'] != other['training_labels_sha256']
            assert node['matched_skeleton_prefix_work']['proposals'] == sum(range(row['train_budget']))
    # Identical method inputs and normalization for each matching arm/budget/node.
    for (name, _, _) in runner.SCENARIOS:
        for seed in runner.SEEDS:
            for arm in runner.ARMS:
                for budget in runner.BUDGETS:
                    a, b = [index[name, seed, method, budget, arm] for method in runner.METHODS]
                    assert [n['training_labels_sha256'] for n in a['nodes']] == [n['training_labels_sha256'] for n in b['nodes']]
    for node in routes[0]['nodes']:
        valid = records[runner.GRID.index(node['u'])]['splits'][1]
        x = runner.training_design(valid['states'], valid['coordinates'])
        predicted = -2.+x@node['fit']['physical_coefficients']
        spec = runner.ForwardSpec(**routes[0]['process'])
        rb_risk = runner.unpenalized_risk(predicted, np.asarray(valid['RAO_BLACKWELL']), spec.maximum_label)
        assert node['validation_risk'] == pytest.approx(rb_risk)
    assert any(not n['fit']['solver_success'] for r in routes for n in r['nodes'])
    assert frozen == routes and json.loads(runner.payload(records)) == records


def _fake_evaluated(routes):
    answer = deepcopy(routes)
    for r in answer:
        rms = .4 if r['arm'] == 'RAW' else .2
        r['active_errors'] = {k: {'continuous_errors': {'rms': rms}} for k in runner.TOLERANCES}
    return answer


def test_global_freeze_barrier_before_both_evaluation_and_label_audit(monkeypatch, manufactured_training):
    calls, _ = manufactured_training
    datasets, frozen, barriers, phases = [], [], [], []
    def evaluate(rows, check, on_route):
        assert len(calls) == 384 and len(frozen) == 48 and len(barriers) == 1
        assert barriers[0]['frozen_records_sha256'] == runner.digest(frozen)
        phases.append('evaluate')
        answer = _fake_evaluated(rows)
        for row in answer: on_route(row)
        return answer
    def postfit(records, check):
        assert len(calls) == 384 and len(barriers) == 1 and phases == ['evaluate']
        phases.append('label_audit')
        return [{'manufactured_postfit_only': True}]
    monkeypatch.setattr(runner, 'evaluate_frozen', evaluate)
    monkeypatch.setattr(runner, 'postfit_label_diagnostics', postfit)
    report = runner.run_comparison(on_dataset=lambda r: datasets.append(deepcopy(r)),
        on_frozen=lambda r: frozen.append(deepcopy(r)), on_barrier=lambda r: barriers.append(deepcopy(r)))
    assert report['completed_routes'] == 48 and report['completed_fits'] == 384
    assert len(report['paired_comparisons']) == 24
    assert all(p['exact_shared_design_and_skeleton'] for p in report['paired_comparisons'])
    assert all(p['errors']['hessian']['rb_over_raw_rms'] == .5 for p in report['paired_comparisons'])
    assert report['freeze_barrier']['backward_target_queried_during_training'] is False
    assert report['scope']['same_skeleton_not_equal_flop_or_walltime'] is True
    assert runner.payload(json.loads(runner.payload(report))) == runner.payload(report)


def test_pair_summary_refuses_duplicate_or_missing_routes_and_handles_zero_raw_error():
    nodes = [{'validation_risk': 1., 'design_prefix_sha256': 'x', 'paired_dataset_payload_sha256': 'p',
              'matched_skeleton_prefix_work': {'proposals': 3}}]
    raw = {'scenario': 'toy', 'method': 'method', 'seed': 1, 'train_budget': 8, 'arm': 'RAW', 'nodes': nodes,
        'active_errors': {k: {'continuous_errors': {'rms': 0.}} for k in runner.TOLERANCES}}
    rb = {**deepcopy(raw), 'arm': 'RAO_BLACKWELL'}
    result = runner.summarize_pairs([raw, rb])
    assert all(x['rb_over_raw_rms'] is None for x in result[0]['errors'].values())
    for rows in ([raw], [rb], [raw, raw, rb]):
        with pytest.raises(ValueError):
            runner.summarize_pairs(rows)


def test_postfit_covariance_gradient_noise_and_label_mse_use_same_design_and_raw_density(monkeypatch):
    monkeypatch.setattr(runner, 'BUDGETS', (4, 8))
    monkeypatch.setattr(runner, 'SCENARIOS', (runner.SCENARIOS[0],))
    queried = []
    class Oracle:
        def log_likelihood_derivatives(self, u, state, coordinate=None):
            queried.append((u, state, coordinate))
            return {'log_likelihood': math.log(.125), 'gradient': 0., 'hessian': 0.}
    module = ModuleType('heterodiff.experiments.continuous_residual_capacity')
    module.target_bundle = lambda scenario: (Oracle(), None, None)
    monkeypatch.setitem(sys.modules, module.__name__, module)
    states = np.array((0, 1, 2, 2)*2, dtype=np.int64)
    z = np.array((0., 0., -1., -.5, 0., 0., .5, 1.))
    raw = np.array((.14, .11, .09, .17, .12, .13, .1, .15))
    rb = np.array((.13, .12, .12, .14, .125, .127, .121, .128))
    variance = np.linspace(.001, .002, 8)
    record = {'scenario': runner.SCENARIOS[0][0], 'seed': 11, 'u': .5,
        'splits': [{'states': states.tolist(), 'coordinates': z.tolist(), 'RAW': raw.tolist(),
                    'RAO_BLACKWELL': rb.tolist(), 'conditional_raw_label_variance': variance.tolist()},
                   {'validation': 'unused by postfit training-label audit'}]}
    original = deepcopy(record)
    result = runner.postfit_label_diagnostics([record])
    assert len(queried) == 8 and len(result) == 2 and record == original
    x = runner.training_design(states, z)
    spec = runner.ForwardSpec(*runner.SCENARIOS[0][1:])
    for row, n in zip(result, (4, 8)):
        direct = sum((variance[j]*np.outer(x[j], x[j]) for j in range(n)), np.zeros((35, 35)))/(n*spec.maximum_label)**2
        assert np.allclose(row['removed_gradient_covariance_estimate'], direct, atol=1e-20, rtol=1e-14)
        assert row['removed_gradient_covariance_trace'] == pytest.approx(np.trace(direct))
        assert np.linalg.eigvalsh(direct).min() >= -1e-18
        for name, labels in (('RAW', raw), ('RAO_BLACKWELL', rb)):
            error = labels[:n]-.125
            metrics = row['arms'][name]
            expected_noise = sum((x[j]*error[j] for j in range(n)), np.zeros(35))/(n*spec.maximum_label)
            assert np.allclose(metrics['empirical_gradient_noise'], expected_noise, atol=2e-17, rtol=1e-14)
            assert metrics['label_mse_against_independent_mean'] == pytest.approx(np.mean(error**2))
        assert row['noise_bound']['raw_and_rb_share_conservative_bound'] is True
        assert row['covariance_estimate_not_confidence_certificate'] is True
