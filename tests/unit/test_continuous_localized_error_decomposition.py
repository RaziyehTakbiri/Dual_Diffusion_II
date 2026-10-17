"""Independent manufactured runner checks; never fit the scientific controls."""
from copy import deepcopy
import hashlib
import json
import math
import sys
from types import ModuleType

import numpy as np
import pytest

from heterodiff.experiments import continuous_localized_error_decomposition as runner


def test_prospective_roster_and_no_new_label_or_model_claim():
    s = runner.specification()
    assert s['same_data_control_fits'] == 24*8*2 == 384
    assert s['population_control_fits'] == 2*2*8*2*2 == 128
    assert s['total_new_diagnostic_fits'] == 512
    assert s['quadrature_points_per_cell'] == (16, 32)
    assert s['primary_quadrature'] == 32
    assert s['quadrature_weights'] == {'EMPTY': .25, 'OTHER': .25, 'CONTINUOUS_UNIFORM_CORE': .5}
    assert s['optimizer'] == {'method': 'L-BFGS-B', 'start': 'ZERO', 'maxiter': 2000,
        'maxls': 50, 'ftol': 1e-15, 'gtol': 1e-11, 'Newton_polishing': False}
    assert s['penalty_P'] == {'roughness': 1e-4, 'ridge': 1e-6}
    assert s['penalty_U'] == {'roughness': 0., 'ridge': 0.}
    assert s['new_forward_simulations'] == 0 and s['retries'] == 0
    assert s['validation_labels_used_for_fitting_or_selection'] is False
    assert s['oracle_labels_are_diagnostic_not_learned_results'] is True
    assert np.array_equal(s['evaluation_coordinates'], np.linspace(-4., 4., 256))
    assert json.loads(runner.payload(s))['total_new_diagnostic_fits'] == 512


def test_exact_ordered_telescope_and_all_ten_nonzero_cross_terms():
    terms = np.array(((1., -2., 4.), (-3., 1., 2.), (2., 2., -1.),
                      (.5, -4., 3.), (5., -1., -.5)))
    t = np.array((-.25, .5, 1.5))
    stages = {'T': t}
    current = t.copy()
    for name, term in zip(reversed(runner.STAGES[:-1]), reversed(terms)):
        current = current+term
        stages[name] = current.copy()
    saved = deepcopy(stages)
    result = runner.contrast_summary(stages)
    gram = np.array([[math.fsum(float(a*b) for a, b in zip(x, y))/3
                      for y in terms] for x in terms])
    assert np.array_equal(result['gram_mean_inner_products'], gram)
    assert result['pointwise_identity_max_abs'] == 0.
    assert result['squared_error_identity_abs'] < 1e-14
    assert result['components_are_independent_variances'] is False
    assert len(result['cross_terms_twice_inner_product']) == 10
    for row, (i, j) in zip(result['cross_terms_twice_inner_product'],
                           ((i, j) for i in range(5) for j in range(i+1, 5))):
        assert row == {'left': runner.TERMS[i], 'right': runner.TERMS[j], 'value': 2*gram[i, j]}
    assert result['squared_error_sum_diagonal'] != pytest.approx(result['squared_error_sum_including_cross_terms'])
    assert all(np.array_equal(stages[k], saved[k]) for k in stages)


def test_cancelling_components_cannot_be_read_as_variance_percentages():
    stages = {name: np.zeros(4) for name in runner.STAGES}
    stages['N'] = np.ones(4)
    r = runner.contrast_summary(stages)
    assert r['total_error_rms'] == 0.
    assert r['squared_error_sum_diagonal'] == 2.
    assert r['squared_error_sum_including_cross_terms'] == 0.
    assert r['cross_terms_twice_inner_product'][0]['value'] == -2.


@pytest.mark.parametrize('change', ('missing', 'extra', 'empty', 'shape', 'nan', 'infinity', 'matrix'))
def test_contrast_rejects_invalid_roster_or_vectors(change):
    rows = {k: np.zeros(3) for k in runner.STAGES}
    if change == 'missing':
        del rows['T']
    elif change == 'extra':
        rows['other'] = np.zeros(3)
    else:
        rows['N'] = {'empty': np.zeros(0), 'shape': np.zeros(4),
            'nan': np.array((0., np.nan, 0.)), 'infinity': np.array((0., np.inf, 0.)),
            'matrix': np.zeros((3, 1))}[change]
    with pytest.raises(ValueError):
        runner.contrast_summary(rows)


def test_target_crosswalk_preserves_atoms_and_coordinate_derivative_identity():
    calls = []
    class Oracle:
        def log_likelihood_derivatives(self, u, key, coordinate=None):
            calls.append((u, key, coordinate))
            if key == 'CONTINUOUS':
                return {'log_likelihood': coordinate**2, 'gradient': 2*coordinate, 'hessian': 2.}
            assert coordinate is None
            return {'log_likelihood': -1. if key == 'EMPTY' else -2., 'gradient': 0., 'hessian': 0.}
    rows = runner.target_rows(Oracle(), .5, np.array((1, 2, 0, 2)), np.array((0., -3., 0., 2.)))
    assert np.array_equal(rows['value'], (-2., 9., -1., 4.))
    assert np.array_equal(rows['gradient'], (0., -6., 0., 4.))
    assert np.array_equal(rows['hessian'], (0., 2., 0., 2.))
    assert calls == [(.5, 'EMPTY', None), (.5, 'OTHER', None),
                     (.5, 'CONTINUOUS', -3.), (.5, 'CONTINUOUS', 2.)]


def test_accuracy_uses_existing_pointwise_rule_and_not_only_global_maximum():
    targets = {key: np.array((0., 100.)) for key in runner.TOLERANCES}
    values = {}
    for key, (atol, rtol) in runner.TOLERANCES.items():
        values[key] = targets[key]+np.array((1.01*atol, .5*(atol+100*rtol)))
    r = runner.accuracy(values, targets)
    assert all(v['failure_count'] == 1 and v['probe_count'] == 2 for v in r.values())


@pytest.fixture
def manufactured_controls(monkeypatch):
    """Small complete chain, using an algebraic substitute rather than an optimizer."""
    monkeypatch.setattr(runner, 'SCENARIOS', (('manufactured', .8, .7),))
    monkeypatch.setattr(runner, 'METHODS', ('association-aware-guide-plus-residual',))
    monkeypatch.setattr(runner, 'SEEDS', (11,))
    monkeypatch.setattr(runner, 'BUDGETS', (4, 8))
    monkeypatch.setattr(runner, 'GRID', (0., .5, 1.))
    calls, readbacks = [], []
    states = np.array((0, 1, 2, 2)*2, dtype=np.int64)
    z = np.array((0., 0., -1., -.2, 0., 0., .4, 1.2))
    labels = np.linspace(.08, .2, 8)
    datasets = [{'scenario': 'manufactured', 'seed': 11, 'u': u, 'ordinal': i+1}
                for i, u in enumerate(runner.GRID[:-1])]
    old = []
    for ordinal, budget in enumerate(runner.BUDGETS, 1):
        old.append({'ordinal': ordinal, 'scenario': 'manufactured', 'seed': 11,
            'method': runner.METHODS[0], 'train_budget': budget,
            'nodes': [{'u': u, 'training_prefix_sha256': runner.array_digest(states[:budget], z[:budget], labels[:budget]),
                'fit': {'physical_coefficients': np.linspace(0., .01, 35).tolist()}}
                for u in runner.GRID[:-1]]})
    archive = {'routes': old, 'datasets': datasets}
    def data(directory, record):
        readbacks.append(record['u'])
        return states.copy(), z.copy(), labels.copy()
    def baseline(spec, u, s, coordinates, method):
        return {'value': np.full(len(s), -2.), 'gradient': np.zeros(len(s)), 'hessian': np.zeros(len(s))}
    def fit(x, ys, b, w, maximum, bound, penalty, minimum):
        calls.append({'x': x.copy(), 'y': ys.copy(), 'b': b.copy(), 'w': w.copy(), 'P': penalty.copy()})
        c = np.linspace(0., .02, 35)+float(np.mean(ys))/100+float(penalty.trace())/100
        return c, {'physical_coefficients': c.tolist(), 'solver_success': len(calls) % 3 != 0,
            'manufactured_no_optimization': True,
            'conservative_baseline_density_floor_from_supplied_floor_and_observed_offset': minimum,
            'maximum_label': maximum, 'coefficient_bound': bound, 'feature_maximum_row_l1_norm': 1.,
            'weighted_gram_minimum_eigenvalue': .001, 'penalty_minimum_eigenvalue_computed': float(penalty.diagonal().min()),
            'box_first_order_gap': 1e-9}
    class Oracle:
        def log_likelihood_derivatives(self, u, state, coordinate=None):
            z = coordinate if state == 'CONTINUOUS' else 0.
            return {'log_likelihood': -2.+.02*(1-u)*z*z,
                    'gradient': .04*(1-u)*z, 'hessian': .04*(1-u) if state == 'CONTINUOUS' else 0.}
    monkeypatch.setattr(runner, 'archived_training', data)
    monkeypatch.setattr(runner, 'baseline_rows', baseline)
    monkeypatch.setattr(runner, 'fit_weighted_risk', fit)
    return archive, {'manufactured': Oracle()}, calls, readbacks, states, z, labels


def test_all_stage_fits_share_inputs_preserve_archived_A_and_never_retry(manufactured_controls):
    archive, oracles, calls, reads, s, z, labels = manufactured_controls
    frozen_pop, frozen_emp = [], []
    saved = deepcopy(archive)
    populations, empirical = runner.fit_controls('unused', archive, oracles,
        on_population=lambda r: frozen_pop.append(deepcopy(r)), on_empirical=lambda r: frozen_emp.append(deepcopy(r)))
    assert len(populations) == 8 and len(empirical) == 2 and len(calls) == 16
    assert reads == [0., .5]
    assert archive == saved
    assert len(frozen_pop) == 8 and frozen_emp == empirical
    for row in empirical:
        budget = row['train_budget']
        for i, node in enumerate(row['nodes']):
            n, m = node['controls']['N'], node['controls']['M']
            assert n['labels_sha256'] == runner.array_digest(labels[:budget])
            means = np.exp(runner.target_rows(oracles['manufactured'], node['u'], s, z)['value'])
            assert m['labels_sha256'] == runner.array_digest(means[:budget])
            assert node['A_coefficients'] == saved['routes'][row['ordinal']-1]['nodes'][i]['fit']['physical_coefficients']
    # Population fits precede empirical controls; each latter N/M pair has the same X/b/w/P.
    for n, m in zip(calls[8::2], calls[9::2]):
        for key in ('x', 'b', 'w', 'P'):
            assert np.array_equal(n[key], m[key])
        assert not np.array_equal(n['y'], m['y'])
    assert any(not r['fit']['solver_success'] for r in populations)
    assert json.loads(runner.payload(empirical)) == empirical


def test_evaluation_chains_terminal_risk_quadrature_and_population_sharing(manufactured_controls):
    archive, oracles, _, _, _, _, _ = manufactured_controls
    populations, empirical = runner.fit_controls('unused', archive, oracles)
    pops, routes, norms = runner.evaluate_controls(populations, empirical, oracles)
    assert len(routes) == 2 and all(len(r['evaluation_nodes']) == 3 for r in routes)
    assert set(norms) == set(runner.TOLERANCES)
    for route in routes:
        for level in ('16', '32'):
            for key in runner.TOLERANCES:
                result = route['active_decomposition'][level][key]
                assert result['probe_count'] == 512
                assert len(result['cross_terms_twice_inner_product']) == 10
                assert result['pointwise_identity_max_abs'] < 1e-14
                assert result['squared_error_identity_abs'] < 1e-14
        terminal = route['evaluation_nodes'][-1]
        assert 'common_primary_population_excess_risk' not in terminal
        for stage in ('A', 'N', 'M'):
            assert terminal['stages'][stage] == terminal['target']
        for level in ('16', '32'):
            for key in runner.TOLERANCES:
                assert terminal['chains'][level]['continuous'][key]['total_error_rms'] == 0.
                assert terminal['chains'][level]['continuous'][key]['term_rms'] == [0.]*5
        node = route['evaluation_nodes'][0]
        q = runner.population_quadrature(32)
        tq = runner.target_rows(oracles['manufactured'], 0., q['states'], q['coordinates'])['value']
        spec = runner.ForwardSpec(.8, .7)
        a = np.asarray(route['nodes'][0]['A_coefficients'])
        delta = -2.+q['features']@a-tq
        independently = math.fsum(float(w*math.exp(t)*(math.expm1(d)-d)/spec.maximum_label)
            for w, t, d in zip(q['weights'], tq, delta))
        assert node['common_primary_population_excess_risk']['A'] == pytest.approx(independently, abs=2e-17)
    for i in range(2):
        for level in ('16', '32'):
            assert routes[0]['evaluation_nodes'][i]['chains'][level]['population_profile_ordinals'] == routes[1]['evaluation_nodes'][i]['chains'][level]['population_profile_ordinals']
    assert all('evaluation' in r for r in pops)
    for p in pops:
        cross = p['cross_quadrature_control']
        other = next(r for r in pops if r['ordinal'] == cross['other_profile_ordinal'])
        assert other['quadrature'] != p['quadrature']
        assert other['regularized'] == p['regularized'] and other['u'] == p['u']
        assert cross['coefficient_difference_max_abs'] == pytest.approx(np.max(abs(np.asarray(p['coefficients'])-other['coefficients'])))
        assert cross['pure_quadrature_error_claimed'] is False
        assert all(not r['interval_certified'] for r in p['solve_readback_bounds'].values())


def test_full_freeze_barrier_precedes_any_comparison_of_evaluation_probes(monkeypatch, manufactured_controls):
    archive, oracles, _, _, _, _, _ = manufactured_controls
    monkeypatch.setattr(runner, 'load_archive', lambda directory: archive)
    module = ModuleType('heterodiff.experiments.continuous_residual_capacity')
    module.target_bundle = lambda scenario: (oracles[scenario[0]], None, None)
    monkeypatch.setitem(sys.modules, module.__name__, module)
    frozen_pop, frozen_emp, barriers = [], [], []
    original_evaluate = runner.evaluate_controls
    def evaluate(*args, **kwargs):
        assert len(frozen_pop) == 8 and len(frozen_emp) == 2 and len(barriers) == 1
        assert all('evaluation' not in row for row in frozen_pop)
        assert barriers[0]['frozen_record_sha256'] == runner.digest({'population': frozen_pop, 'empirical': frozen_emp})
        return original_evaluate(*args, **kwargs)
    monkeypatch.setattr(runner, 'evaluate_controls', evaluate)
    report = runner.run_comparison('unused', on_population=lambda r: frozen_pop.append(deepcopy(r)),
        on_empirical=lambda r: frozen_emp.append(deepcopy(r)), on_barrier=lambda r: barriers.append(deepcopy(r)))
    assert report['freeze_barrier']['new_fits'] == 16
    assert report['freeze_barrier']['oracle_likelihood_labels_used_for_controls'] is True
    assert report['scope']['new_forward_labels_simulated'] is False
    assert report['scope']['oracle_controls_are_learned_results'] is False
    assert report['scope']['variance_components_identified'] is False


def test_invalid_archive_stops_before_oracle_instantiation_or_fits(monkeypatch):
    module = ModuleType('heterodiff.experiments.continuous_residual_capacity')
    def forbidden(*args, **kwargs):
        raise AssertionError('scientific work before archive accepted')
    module.target_bundle = forbidden
    monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr(runner, 'fit_controls', forbidden)
    def refuse(directory):
        raise ValueError('invalid preserved archive')
    monkeypatch.setattr(runner, 'load_archive', refuse)
    with pytest.raises(ValueError, match='invalid preserved archive'):
        runner.run_comparison('unused')


@pytest.fixture
def paired_dataset(tmp_path):
    states = np.tile(np.array((0, 1, 2, 2), dtype=np.int64), 2048)
    z, y = np.zeros(8192), np.full(8192, .125)
    split = {'states': states.tolist(), 'coordinates': z.tolist(), 'labels': y.tolist(),
        'sha256': runner.array_digest(states, z, y)}
    row = {'splits': [split, {'validation': 'not consumed'}]}
    record = {'ordinal': 1, 'record_sha256': runner.digest(row), 'split_sha256': [split['sha256']]}
    runner.write_new(tmp_path/'dataset-01.json', row)
    return tmp_path, row, record, states, z, y


def test_archived_training_reads_exact_bound_arrays_and_no_validation_use(paired_dataset):
    directory, _, record, *expected = paired_dataset
    observed = runner.archived_training(directory, record)
    assert all(np.array_equal(x, y) for x, y in zip(observed, expected))


@pytest.mark.parametrize('kind', ('record', 'array', 'shape', 'split_binding'))
def test_archived_training_refuses_mutated_bindings(paired_dataset, kind):
    directory, row, record, *_ = paired_dataset
    if kind == 'record':
        record['record_sha256'] = '0'*64
    elif kind == 'split_binding':
        record['split_sha256'][0] = '0'*64
    else:
        if kind == 'array':
            row['splits'][0]['labels'][0] += .01
        else:
            row['splits'][0]['states'].pop()
        (directory/'dataset-01.json').write_bytes(runner.payload(row))
        record['record_sha256'] = runner.digest(row)
    with pytest.raises(ValueError):
        runner.archived_training(directory, record)


@pytest.fixture
def manufactured_archive(tmp_path, monkeypatch):
    """Bind a tiny synthetic report for testing read-only guard ordering."""
    protocol = {'manufactured': True}
    monkeypatch.setattr(runner, 'ARCHIVE_PROTOCOL_SHA256', runner.digest(protocol))
    s = np.tile(np.array((0, 1, 2, 2), dtype=np.int64), 2048)
    z, y = np.zeros(8192), np.full(8192, .125)
    arrays = (s, z, y)
    monkeypatch.setattr(runner, 'archived_training', lambda directory, record: tuple(a.copy() for a in arrays))
    monkeypatch.setattr(runner, 'weighted_risk_terms', lambda *args: (1., np.zeros(35), np.eye(35)))
    def baseline(spec, u, states, coordinates, method):
        return {'value': np.full(len(states), -2.), 'gradient': np.zeros(len(states)), 'hessian': np.zeros(len(states))}
    monkeypatch.setattr(runner, 'baseline_rows', baseline)
    node = {'u': 0., 'training_prefix_sha256': runner.array_digest(s[:1024], z[:1024], y[:1024]),
        'fit': {'physical_coefficients': [0.]*35, 'final_penalized_risk': 1.}}
    frozen = {'all_models_frozen_before_backward_oracle': True, 'method': runner.METHODS[0],
        'nodes': [node], 'ordinal': 1, 'process': {'theta': .8, 'observation_value': .7},
        'scenario': 'manufactured', 'seed': 0, 'train_budget': 1024}
    physical = {'value': [-2.]*258, 'gradient': [0.]*258, 'hessian': [0.]*258}
    row = {**deepcopy(frozen), 'evaluation_nodes': [{'physical': physical}, {'terminal': True}]}
    barrier = {'frozen_records_sha256': runner.digest([frozen])}
    report = {'protocol_sha256': runner.digest(protocol), 'completed_routes': 24, 'completed_fits': 192,
        'protocol': protocol, 'source_sha256': {}, 'routes': [row], 'freeze_barrier': barrier,
        'datasets': [{'scenario': 'manufactured', 'seed': i, 'u': 0.} for i in range(48)]}
    for name, value in (('protocol.json', protocol), ('frozen-01.json', frozen), ('freeze-barrier.json', barrier), ('report.json', report)):
        runner.write_new(tmp_path/name, value)
    monkeypatch.setattr(runner, 'ARCHIVE_SHA256', hashlib.sha256((tmp_path/'report.json').read_bytes()).hexdigest())
    return tmp_path, report, frozen, barrier, arrays


def test_load_archive_checks_bound_sources_freeze_arrays_and_A_reconstruction(manufactured_archive):
    directory, expected, *_ = manufactured_archive
    assert runner.load_archive(directory) == expected


@pytest.mark.parametrize('kind', ('protocol', 'empty_frozen', 'frozen_field', 'barrier', 'prefix', 'risk', 'physical', 'source'))
def test_load_archive_refuses_preflight_inconsistency(manufactured_archive, monkeypatch, kind):
    directory, report, frozen, barrier, arrays = manufactured_archive
    if kind == 'protocol':
        (directory/'protocol.json').write_bytes(runner.payload({'changed': True}))
    elif kind == 'empty_frozen':
        (directory/'frozen-01.json').write_bytes(b'{}')
    elif kind == 'frozen_field':
        frozen['seed'] = 99
        (directory/'frozen-01.json').write_bytes(runner.payload(frozen))
    elif kind == 'barrier':
        barrier['frozen_records_sha256'] = '0'*64
        (directory/'freeze-barrier.json').write_bytes(runner.payload(barrier))
    elif kind == 'prefix':
        s, z, y = arrays
        bad = y.copy()
        bad[0] += .1
        monkeypatch.setattr(runner, 'archived_training', lambda directory, record: (s.copy(), z.copy(), bad.copy()))
    elif kind == 'risk':
        monkeypatch.setattr(runner, 'weighted_risk_terms', lambda *args: (2., np.zeros(35), np.eye(35)))
    elif kind == 'physical':
        monkeypatch.setattr(runner, '_physical', lambda *args: {'value': np.zeros(258), 'gradient': np.zeros(258), 'hessian': np.zeros(258)})
    else:
        report['source_sha256'] = {'models/localized_likelihood_learner.py': '0'*64}
        (directory/'report.json').write_bytes(runner.payload(report))
        monkeypatch.setattr(runner, 'ARCHIVE_SHA256', hashlib.sha256((directory/'report.json').read_bytes()).hexdigest())
    with pytest.raises(ValueError):
        runner.load_archive(directory)
