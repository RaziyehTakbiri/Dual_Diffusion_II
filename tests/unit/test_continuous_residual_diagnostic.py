"""Independent diagnostic checks; no optimization or endpoint sampling."""

from copy import deepcopy
from types import SimpleNamespace
import json
import math

import pytest
import torch

from heterodiff.experiments import continuous_residual_diagnostic as diagnosis
from heterodiff.experiments import continuous_multiseed_benchmark as original
from heterodiff.data.two_domain_factorized_state import FactoredEvent, PhysioStateKey


@pytest.fixture(autouse=True)
def one_cpu_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


def test_capacity_is_gauge_invariant_and_reports_two_point_error_floor():
    actual = diagnosis.capacity_summary([1., 2., 4.], [1., 1.5, 2.], .25, .5)
    shifted = diagnosis.capacity_summary([8., 9., 11.], [-2., -1.5, -1.], .25, .5)
    assert actual == shifted
    assert actual['required_correction_diameter'] == 2.
    assert actual['available_residual_diameter'] == .25
    assert actual['excess_diameter'] == 1.75
    assert actual['uniform_log_potential_error_lower_bound_any_gauge'] == .875
    assert 'NOT_GLOBAL_ERROR_OR_SCORE_BOUND' in actual['scope']


def test_capacity_zero_gate_distinguishes_constant_gauge_from_state_error():
    assert diagnosis.capacity_summary([3., 4.], [1., 2.], .25, 0.)['excess_diameter'] == 0.
    assert diagnosis.capacity_summary([3., 5.], [1., 2.], .25, 0.)['excess_diameter'] == 1.
    assert diagnosis.capacity_summary([0., .5], [0., 0.], .25, 1.)['excess_diameter'] == 0.


@pytest.mark.parametrize('targets,baseline,bound,gate', [
    ([0.], [0.], .25, 1.), ([0., 1.], [0.], .25, 1.),
    ([0., math.nan], [0., 0.], .25, 1.), ([0., 1.], [0., math.inf], .25, 1.),
    ([0., 1.], [0., 0.], 0., 1.), ([0., 1.], [0., 0.], -.25, 1.),
    ([0., 1.], [0., 0.], .25, -1.), ([0., 1.], [0., 0.], .25, 1.01),
])
def test_capacity_rejects_invalid_input(targets, baseline, bound, gate):
    with pytest.raises(ValueError):
        diagnosis.capacity_summary(targets, baseline, bound, gate)


def test_coordinate_derivatives_constant_unused_and_polynomial_outputs():
    z = torch.tensor([2.], dtype=torch.float64, requires_grad=True)
    unused = torch.tensor([3.], dtype=torch.float64, requires_grad=True)
    atom = torch.tensor([], dtype=torch.float64, requires_grad=True)
    assert diagnosis._coordinate_derivatives(torch.tensor([2.]), (z, atom)) == {0: (0., 0.), 1: (0., 0.)}
    found = diagnosis._coordinate_derivatives(z**3, (z, unused, atom))
    assert found == {0: (12., 12.), 1: (0., 0.), 2: (0., 0.)}
    assert z.grad is None and unused.grad is None


def _summary_fixture():
    rows, targets = [], []
    for u in original.GRID:
        for label, z in [('EMPTY', None), ('OTHER_ATOM', None), ('CONTINUOUS', 0.), ('OTHER_CONTINUOUS', 0.)]:
            other_score = .125 if label == 'OTHER_CONTINUOUS' else 0.
            rows.append({'time': u, 'state': label, 'coordinate': z,
                'baseline_rn_log_likelihood': 2., 'physical_rn_log_likelihood': 5.,
                'classifier_logit': 9., 'residual': 3.,
                'baseline_gradient': 0., 'baseline_hessian': 0.,
                'physical_gradient': other_score, 'physical_hessian': 0.})
            target = {'rn_log_likelihood': 7., 'gradient': 0., 'hessian': 0., 'classifier_logit': 9.}
            targets.append({'time': u, 'state': label, 'coordinate': z,
                'continuous': dict(target), 'numerical_grid': dict(target)})
    return {'rows': rows}, {'rows': targets}


def test_summaries_remove_state_constant_gauges_and_detect_other_coordinate_score():
    inspection, targets = _summary_fixture()
    result = diagnosis.summarize_queries(inspection, targets, .25)
    assert len(result['per_time']) == 9
    for row in result['per_time']:
        for target in row['targets'].values():
            assert target['physical']['empty_centered_log_likelihood']['max_abs'] == 0.
            assert target['baseline']['empty_centered_log_likelihood']['max_abs'] == 0.
            assert target['classifier_logit']['max_abs'] == 0.
            assert target['physical']['other_continuous_spurious_score']['max_abs'] == .125
            assert target['capacity']['excess_diameter'] == 0.
    assert 'NOT_POSTERIOR_RISK_OR_ENDPOINT_BOUND' in result['scope']


@pytest.mark.parametrize('change', ['order', 'time', 'coordinate', 'length'])
def test_query_summary_refuses_roster_mismatch(change):
    inspection, targets = _summary_fixture()
    if change == 'order':
        targets['rows'][0], targets['rows'][1] = targets['rows'][1], targets['rows'][0]
    elif change == 'time':
        targets['rows'][0]['time'] = .0625
    elif change == 'coordinate':
        targets['rows'][2]['coordinate'] = .5
    else:
        targets['rows'].pop()
    with pytest.raises(ValueError, match='roster mismatch'):
        diagnosis.summarize_queries(inspection, targets, .25)


def test_observation_coverage_only_projects_existing_records_and_keeps_phases():
    key = PhysioStateKey(3, 'HR', 'POSITIVE')
    other = PhysioStateKey(4, 'HR', 'POSITIVE')
    states = ((), (), (FactoredEvent(key, .1),), (FactoredEvent(other, 3.),))
    observations = tuple(SimpleNamespace(observed=x) for x in (
        None, (), (FactoredEvent(key, 1.2),), (FactoredEvent(other, 5.),)))
    joint = SimpleNamespace(states=states, reverse_times=(0., .125, .5, .875), observations=observations)
    product = SimpleNamespace(states=states, reverse_times=joint.reverse_times,
        observations=tuple(reversed(observations)))
    before = deepcopy((joint, product))
    coverage = diagnosis.ObservationCoverage(key, .7)
    coverage.record(joint, product)
    coverage.phase = 'training'
    coverage.record(joint, product)
    assert (joint, product) == before
    report = coverage.report()
    assert report == coverage.report()
    assert report['record_count'] == 16
    assert all(row['count'] == 4 for row in report['groups'])
    for row in report['groups']:
        assert row['observation_kinds'] == {'EMPTY': 1, 'OTHER': 1, 'OVERFLOW': 1, 'SELECTED_CONTINUOUS': 1}
        assert row['selected_within_fixed_band_count'] == 1
        assert sum(row['time_counts'].values()) == 4
    assert report['record_sha256'] == diagnosis._digest(coverage.records)
    assert any(r['latent_category'] == 'OTHER' for r in report['records'])


def _replay_fixture():
    updates = ({'reverse_times': (.125, .5), 'loss': .6},)
    losses = [{'update': 0, 'held_out_paired_loss': .7}, {'update': 32, 'held_out_paired_loss': .6}]
    archived = {'initial_parameter_sha256': 'initial', 'final_parameter_sha256': 'final',
        'population_law_id': 'population', 'updates': json.loads(diagnosis._payload(updates)),
        'held_out_paired_loss_curve': deepcopy(losses)}
    return archived, ['initial', 'final', 'population', updates, losses]


def test_original_replay_accepts_exact_tuple_to_json_normalization():
    archived, arguments = _replay_fixture()
    checks = diagnosis.require_original_replay(archived, *arguments)
    assert len(checks) == 5 and all(checks.values())


@pytest.mark.parametrize('index', range(5))
def test_original_replay_rejects_each_changed_binding(index):
    archived, arguments = _replay_fixture()
    if index < 3:
        arguments[index] += '-changed'
    elif index == 3:
        arguments[index] = ({'reverse_times': (.125, .5), 'loss': .600001},)
    else:
        arguments[index][1]['held_out_paired_loss'] = .600001
    with pytest.raises(ValueError, match='original fit replay mismatch'):
        diagnosis.require_original_replay(archived, *arguments)


@pytest.mark.parametrize('method', original.METHODS)
def test_real_fixture_query_is_finite_nonmutating_and_zero_residual_at_endpoint(method, monkeypatch):
    from heterodiff.experiments.factorized_conditional_pipeline import _parameter_digest
    from heterodiff.processes.factorized_hybrid_sampler import LearnedFactorizedSampler
    def no_endpoint(*args, **kwargs):
        raise AssertionError('diagnostic must not draw endpoint paths')
    monkeypatch.setattr(LearnedFactorizedSampler, 'sample_path', no_endpoint)
    _, _, key, _, model, context, observed = original.fixture(original.SCENARIOS[0], 1201, method)
    before = _parameter_digest(model)
    modes = {name: child.training for name, child in model.named_modules()}
    result = diagnosis.inspect_model(model, context, observed, key)
    assert result['parameter_sha256'] == before == _parameter_digest(model)
    assert modes == {name: child.training for name, child in model.named_modules()}
    assert all(p.grad is None for p in model.parameters())
    assert len(result['rows']) == 108
    assert [(r['time'], r['state'], r['coordinate']) for r in result['rows']] == [
        (u, label, z) for u in original.GRID for label, z, _ in diagnosis.query_roster(key)]
    for row in result['rows']:
        assert all(math.isfinite(value) for value in row.values() if isinstance(value, (float, int)))
        assert row['classifier_logit'] == row['physical_rn_log_likelihood'] + result['nuisance']
        if row['state'].startswith('OTHER'):
            assert row['baseline_gradient'] == row['baseline_hessian'] == 0.
        if row['time'] == 1.:
            assert row['residual'] == row['residual_gradient'] == row['residual_hessian'] == 0.
    assert any(abs(r['physical_gradient']) > 0. for r in result['rows']
               if r['state'] == 'OTHER_CONTINUOUS' and r['time'] < 1.)
