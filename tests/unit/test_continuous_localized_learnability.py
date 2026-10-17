"""Runner-only tests with manufactured labels/fits; no scientific training runs."""
import builtins
from copy import deepcopy
import json
import math
import sys
from types import ModuleType

import numpy as np
import pytest

from heterodiff.experiments import continuous_localized_learnability as runner


def test_prospective_protocol_counts_pairing_and_unchanged_tolerances():
    spec = runner.specification()
    settings, seeds, nodes = len(runner.SCENARIOS), len(runner.SEEDS), len(runner.GRID)-1
    routes = settings*seeds*len(runner.METHODS)*len(runner.BUDGETS)
    assert spec['route_count'] == routes == 24
    assert spec['fit_count'] == routes*nodes == 192
    assert spec['unique_training_suffixes'] == settings*seeds*nodes*max(runner.BUDGETS) == 393216
    assert spec['unique_validation_suffixes'] == settings*seeds*nodes*runner.VALIDATION_SIZE == 196608
    assert spec['unique_forward_suffixes'] == 589824
    assert runner.BUDGETS == (1024, 8192) and runner.SEEDS == (11, 29, 47)
    assert runner.VALIDATION_SIZE == 4096 and runner.MAXIMUM_SECONDS == 1200
    assert spec['continuous_cells'] == 32
    assert spec['continuous_free_coefficients']+spec['atom_free_coefficients'] == 35
    assert spec['approximation_tolerances'] == {
        'value': (2e-6, 2e-5), 'gradient': (2e-5, 2e-4), 'hessian': (1e-4, 1e-3)}
    assert np.array_equal(spec['evaluation_coordinates'], np.linspace(-4., 4., 256))
    assert spec['paired_inputs_and_labels_across_methods'] is True
    assert spec['nested_samples_across_budgets'] is True
    assert spec['oracle_import_and_queries_after_all_fits_frozen'] is True
    assert spec['training_labels_include_backward_likelihood_or_derivatives'] is False
    assert spec['validation_or_oracle_selects_settings_or_stopping'] is False
    assert spec['sampler_integration'] is False and spec['old_BCE_model_replaced'] is False
    assert spec['retries'] == 0
    assert json.loads(runner.payload(spec))['fit_count'] == 192


def test_dataset_rng_namespaces_are_distinct_reproducible_and_forward_only(monkeypatch):
    monkeypatch.setattr(runner, 'BUDGETS', (8, 16))
    monkeypatch.setattr(runner, 'VALIDATION_SIZE', 8)
    calls = []
    def manufactured_labels(spec, u, states, coordinates, rng):
        calls.append((u, states.copy(), coordinates.copy()))
        labels = spec.contamination_density+(spec.maximum_label-spec.contamination_density)*rng.uniform(.1, .9, len(states))
        return labels, {'manufactured': True, 'forward_suffix_count': len(states)}
    monkeypatch.setattr(runner, 'rollout_labels', manufactured_labels)
    spec = runner.ForwardSpec(.8, .7)
    train = runner.make_dataset(spec, 0, 11, 0, 0)
    repeat = runner.make_dataset(spec, 0, 11, 0, 0)
    validation = runner.make_dataset(spec, 0, 11, 0, 1)
    other_seed = runner.make_dataset(spec, 0, 29, 0, 0)
    assert len(calls) == 4 and all(row[0] == 0 for row in calls)
    assert train['sha256'] == repeat['sha256']
    assert len({train['sha256'], validation['sha256'], other_seed['sha256']}) == 3
    assert train['rng_namespace'] == [20260913, 0, 11, 0, 0]
    assert validation['rng_namespace'] == [20260913, 0, 11, 0, 1]
    assert np.array_equal(train['states'], np.tile((0, 1, 2, 2), 4))
    assert runner.array_digest(train['states'], train['coordinates'], train['labels']) == train['sha256']


@pytest.fixture
def fake_training(monkeypatch):
    """Exercise all routes with tiny manufactured arrays and a nonoptimizing fit."""
    monkeypatch.setattr(runner, 'BUDGETS', (8, 16))
    monkeypatch.setattr(runner, 'VALIDATION_SIZE', 8)
    calls, data_calls = [], []
    def dataset(spec, scenario, seed, node, split):
        n = max(runner.BUDGETS) if split == 0 else runner.VALIDATION_SIZE
        states = np.tile(np.array((0, 1, 2, 2), dtype=np.int64), n//4)
        z = np.zeros(n)
        offset = (scenario*1000+seed*10+node*2+split)*1e-5
        z[states == 2] = np.linspace(-1., 1., n//2)+offset
        labels = np.full(n, spec.contamination_density+(spec.maximum_label-spec.contamination_density)*(.1+offset))
        data_calls.append((scenario, seed, node, split))
        return {'states': states, 'coordinates': z, 'labels': labels,
            'sha256': runner.array_digest(states, z, labels),
            'work': {'forward_suffix_count': n, 'manufactured_only': True},
            'rng_namespace': [20260913, scenario, seed, node, split]}
    def features(states, coordinates):
        result = np.zeros((len(states), 35))
        result[states == 2, 0] = 1.
        result[states == 0, 33] = 1.
        result[states == 1, 34] = 1.
        return result
    def baseline(spec, u, states, coordinates, method):
        assert method in runner.METHODS
        return {'value': np.full(len(states), -2.),
            'gradient': np.zeros(len(states)), 'hessian': np.zeros(len(states))}
    def fit(features, labels, baseline, tau, maximum, minimum, roughness):
        calls.append({'features': features.copy(), 'labels': labels.copy(),
            'baseline': baseline.copy(), 'tau': tau, 'maximum': maximum, 'minimum': minimum})
        assert features.shape == (len(labels), 35)
        assert baseline.shape == labels.shape
        model = runner.LearnedLocalizedResidual((0.,)*35, tau, 2./tau)
        return model, {'coefficients': [0.]*35, 'physical_coefficients': [0.]*35,
            'remaining_time': tau, 'quotient_coefficient_bound': 2./tau,
            'solver_success': len(calls) % 7 != 0, 'projected_gradient_max_abs': .125,
            'manufactured_no_optimizer_run': True}
    monkeypatch.setattr(runner, 'make_dataset', dataset)
    monkeypatch.setattr(runner, 'training_design', features)
    monkeypatch.setattr(runner, 'baseline_rows', baseline)
    monkeypatch.setattr(runner, 'roughness_matrix', lambda: np.zeros((35, 35)))
    monkeypatch.setattr(runner, 'fit_likelihood', fit)
    return calls, data_calls


def test_training_does_not_import_or_query_backward_oracle_and_exports_shared_prefixes(monkeypatch, fake_training):
    calls, data_calls = fake_training
    original_import = builtins.__import__
    forbidden = ('heterodiff.evaluation', 'heterodiff.experiments.continuous_residual_capacity')
    def guarded_import(name, *args, **kwargs):
        if any(name.startswith(prefix) for prefix in forbidden):
            raise AssertionError('backward oracle import during training')
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', guarded_import)
    raw_datasets, frozen_records = [], []
    routes, records = runner.train_all(on_dataset=lambda r: raw_datasets.append(deepcopy(r)),
        on_frozen=lambda r: frozen_records.append(deepcopy(r)))
    assert len(calls) == 192 and len(routes) == len(frozen_records) == 24
    assert len(raw_datasets) == len(records) == 48 and len(data_calls) == 96
    assert len(set(data_calls)) == 96  # Not regenerated for method or budget.
    route_map = {(r['scenario'], r['seed'], r['method'], r['train_budget']): r for r in routes}
    for scenario, _, _ in runner.SCENARIOS:
        for seed in runner.SEEDS:
            for budget in runner.BUDGETS:
                left, right = [route_map[(scenario, seed, method, budget)] for method in runner.METHODS]
                for ln, rn in zip(left['nodes'], right['nodes']):
                    for key in ('training_prefix_sha256', 'training_full_dataset_sha256', 'validation_dataset_sha256'):
                        assert ln[key] == rn[key]
            for method in runner.METHODS:
                small, large = [route_map[(scenario, seed, method, budget)] for budget in runner.BUDGETS]
                for sn, ln in zip(small['nodes'], large['nodes']):
                    assert sn['training_full_dataset_sha256'] == ln['training_full_dataset_sha256']
                    assert sn['validation_dataset_sha256'] == ln['validation_dataset_sha256']
                    assert sn['training_prefix_sha256'] != ln['training_prefix_sha256']
    for raw, record in zip(raw_datasets, records):
        assert runner.digest(raw) == record['record_sha256']
        assert json.loads(runner.payload(raw)) == raw
        for split in raw['splits']:
            states = np.asarray(split['states'], dtype=np.int64)
            z, labels = np.asarray(split['coordinates']), np.asarray(split['labels'])
            assert runner.array_digest(states, z, labels) == split['sha256']
        train = raw['splits'][0]
        for budget in runner.BUDGETS:
            expected = runner.array_digest(np.asarray(train['states'], dtype=np.int64)[:budget],
                np.asarray(train['coordinates'])[:budget], np.asarray(train['labels'])[:budget])
            for method in runner.METHODS:
                route = route_map[(raw['scenario'], raw['seed'], method, budget)]
                assert route['nodes'][runner.GRID.index(raw['u'])]['training_prefix_sha256'] == expected
    assert json.loads(runner.payload(frozen_records)) == frozen_records
    assert any(not node['fit']['solver_success'] for r in routes for node in r['nodes'])


def _manufactured_oracle_module(on_query):
    fake = ModuleType('heterodiff.experiments.continuous_residual_capacity')
    class Oracle:
        def log_likelihood_derivatives(self, u, state, coordinate=None):
            on_query()
            assert u in runner.GRID and state in ('EMPTY', 'OTHER', 'CONTINUOUS')
            assert (coordinate is None) == (state != 'CONTINUOUS')
            return {'log_likelihood': -2., 'gradient': 0., 'hessian': 0.}
    def bundle(scenario):
        on_query()
        assert scenario in runner.SCENARIOS
        return Oracle(), None, None
    def compare(approximation, target):
        result = {}
        for name, (atol, rtol) in runner.TOLERANCES.items():
            a, t = np.asarray(approximation[name]), np.asarray(target[name])
            assert a.shape == t.shape == (256,)
            error = a-t
            result[name] = {'count': len(t), 'max_abs': float(np.max(abs(error))),
                'rms': float(np.sqrt(np.mean(error**2))),
                'failure_count': int(np.sum(abs(error) > atol+rtol*abs(t))),
                'atol': atol, 'rtol': rtol}
        return result
    fake.target_bundle, fake.compare_arrays = bundle, compare
    return fake


def test_global_freeze_barrier_precedes_first_oracle_query_and_terminal_is_evaluated(monkeypatch, fake_training):
    calls, _ = fake_training
    frozen, barriers, outputs, queries = [], [], [], []
    def on_query():
        assert len(calls) == 192 and len(frozen) == 24 and len(barriers) == 1
        if not queries:
            assert barriers[0]['frozen_records_sha256'] == runner.digest(frozen)
        queries.append(True)
    monkeypatch.setitem(sys.modules, 'heterodiff.experiments.continuous_residual_capacity', _manufactured_oracle_module(on_query))
    report = runner.run_comparison(on_frozen=lambda r: frozen.append(deepcopy(r)),
        on_barrier=lambda r: barriers.append(deepcopy(r)), on_route=lambda r: outputs.append(deepcopy(r)))
    assert queries and len(outputs) == 24
    assert report['freeze_barrier']['frozen_models'] == 192
    assert report['freeze_barrier']['backward_target_queried_during_training'] is False
    assert report['completed_routes'] == 24 and report['completed_fits'] == 192
    assert runner.digest(frozen) == barriers[0]['frozen_records_sha256']
    for row in outputs:
        assert len(row['evaluation_nodes']) == 9
        terminal = row['evaluation_nodes'][-1]
        assert terminal['u'] == 1.
        for name in runner.TOLERANCES:
            assert terminal['residual'][name] == [0.]*258
            assert terminal['physical'][name] == terminal['target'][name]
            assert row['active_errors'][name]['continuous_errors']['probe_count'] == 2048
            assert row['active_errors'][name]['continuous_errors']['failure_count'] == 0
        assert terminal['atomic_log_value_errors'] == [0., 0.]
        assert terminal['model_real_absolute_bound'] == 0.
        assert row['maximum_projected_gradient'] == .125
        assert row['solver_success_count'] == sum(n['fit']['solver_success'] for n in row['nodes'])
        assert row['all_continuous_tolerances_passed'] is True
    assert json.loads(runner.payload(report))['completed_fits'] == 192


def test_failed_fit_prevents_barrier_and_oracle_evaluation(monkeypatch, fake_training):
    def fail(*args, **kwargs):
        raise RuntimeError('manufactured fit failure')
    monkeypatch.setattr(runner, 'fit_likelihood', fail)
    def forbidden(*args, **kwargs):
        raise AssertionError('must not evaluate or publish barrier after failed fit')
    monkeypatch.setattr(runner, 'evaluate_frozen', forbidden)
    with pytest.raises(RuntimeError, match='manufactured fit failure'):
        runner.run_comparison(on_barrier=forbidden)


def test_strict_json_rejects_nonfinite_before_creating_file_and_never_overwrites(tmp_path):
    path = tmp_path/'record.json'
    with pytest.raises(ValueError):
        runner.write_new(path, {'bad': math.nan})
    assert not path.exists()
    runner.write_new(path, {'finite': 1.})
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        runner.write_new(path, {'other': 2.})
    assert path.read_bytes() == before


def test_array_fingerprints_bind_shape_dtype_order_and_labels():
    base = np.arange(8, dtype=np.float64)
    assert runner.array_digest(base) == runner.array_digest(base.copy())
    assert len({runner.array_digest(base), runner.array_digest(base.astype(np.float32)),
        runner.array_digest(base.reshape(2, 4)), runner.array_digest(base[::-1])}) == 4
    assert runner.array_digest(base, base+1) != runner.array_digest(base+1, base)


def test_paired_risk_change_matches_independent_stratified_standard_error():
    states = np.array([0]*3+[1]*4+[2]*5)
    baseline = np.linspace(-2., -1., len(states))
    potential = baseline+np.linspace(-.2, .1, len(states))
    labels = np.linspace(.1, .4, len(states))
    maximum = .5
    changes = (np.exp(potential)-np.exp(baseline)-labels*(potential-baseline))/maximum
    expected_variance = 0.
    for s in (0, 1, 2):
        group = changes[states == s]
        centered_sum = sum(float(x-group.mean())**2 for x in group)
        expected_variance += (len(group)/len(states))**2*centered_sum/(len(group)-1)/len(group)
    result = runner.paired_risk_change(potential, baseline, labels, maximum, states)
    assert result['mean'] == pytest.approx(changes.mean(), abs=1e-15)
    assert result['stratified_standard_error_descriptive'] == pytest.approx(math.sqrt(expected_variance), abs=1e-15)
    assert result['negative_means_improved'] is True
    assert result['confidence_interval_or_multiple_testing_claim'] is False
    assert runner.unpenalized_risk(potential, labels, maximum) == pytest.approx(np.mean(np.exp(potential)-labels*potential)/maximum)


@pytest.mark.parametrize('problem', ['column', 'length', 'nan', 'complex', 'bool', 'zero_maximum', 'missing_stratum', 'one_in_stratum'])
def test_reporting_refuses_misaligned_nonfinite_or_undefined_stratified_statistics(problem):
    states = np.tile((0, 1, 2, 2), 2)
    potential, baseline, labels, maximum = np.zeros(8), np.zeros(8), np.full(8, .1), 1.
    if problem == 'column': potential = potential[:, None]
    elif problem == 'length': labels = labels[:-1]
    elif problem == 'nan': potential[0] = np.nan
    elif problem == 'complex': potential = potential.astype(complex)
    elif problem == 'bool': baseline = baseline == 0
    elif problem == 'zero_maximum': maximum = 0.
    elif problem == 'missing_stratum': states[states == 1] = 2
    else: states[1] = 2
    with pytest.raises(ValueError):
        runner.paired_risk_change(potential, baseline, labels, maximum, states)
