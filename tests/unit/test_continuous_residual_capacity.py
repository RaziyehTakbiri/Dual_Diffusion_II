"""Independent fit-layer checks; no full comparison or endpoint experiment."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
import json
import math

import numpy as np
import pytest

from heterodiff.experiments import continuous_residual_capacity as capacity
from heterodiff.models.compact_fiber_residual import CompactFiberResidual, design


def _manufactured(z, tau):
    """Degree-two compact polynomial, differentiated independently by hand."""
    s = np.tanh(np.asarray(z, dtype=np.float64)/2.)
    ds = (1.-s*s)/2.
    d2s = -s*ds
    q = .5+2.*s-.7*(2.*s*s-1.)
    dq = 2.-2.8*s
    return {'value': tau*q, 'gradient': tau*dq*ds,
            'hessian': tau*(-2.8*ds*ds+dq*d2s)}


def test_prospective_collocation_and_probe_rosters_are_reproducible_and_disjoint():
    train, evaluation = capacity.collocation_rosters()
    assert train.shape == (129,) and evaluation.shape == (256,)
    assert train.dtype == evaluation.dtype == np.float64
    expected = 2.*np.arctanh(np.tanh(2.)*np.cos(np.pi*(np.arange(129)+.5)/129.))
    np.testing.assert_array_equal(train, expected)
    np.testing.assert_array_equal(evaluation, np.linspace(-4., 4., 256))
    assert np.min(np.abs(train[:, None]-evaluation)) > 1e-12
    assert np.max(np.abs(train)) < 4.
    assert evaluation[0] == -4. and evaluation[-1] == 4.
    train[:] = 100.
    np.testing.assert_array_equal(capacity.collocation_rosters()[0], expected)


def test_specification_keeps_all_routes_objectives_and_declared_scope():
    spec = capacity.specification()
    assert spec['route_count'] == 2*2*2*3 == 24
    assert spec['continuous_fit_count'] == 24*8
    assert tuple(spec['degrees']) == (16, 32, 64)
    assert spec['score_objective_weight'] == 1.
    assert spec['rcond'] == 1e-12 and spec['ridge_regularization'] == 0.
    assert spec['hessian_supervised'] is False
    assert spec['sampler_integration'] is False
    assert spec['degree_selection_from_evaluation'] is False
    assert spec['tolerances_are_not_parity_or_endpoint_acceptance'] is True
    assert spec['atomic_corrections'] == 'EXACT_ORACLE_CONSTANTS_NOT_LEARNED'


@pytest.mark.parametrize('tau', [1., .125])
@pytest.mark.parametrize('objective', capacity.OBJECTIVES)
def test_manufactured_fit_recovers_value_score_hessian_with_one_gate(tau, objective):
    train, evaluation = capacity.collocation_rosters()
    labels = _manufactured(train, tau)
    before = deepcopy((train, labels))
    model, record = capacity.fit_residual(train, labels['value'], labels['gradient'], tau, 16, objective)
    actual = model.evaluate(evaluation)
    expected = _manufactured(evaluation, tau)
    for name in expected:
        np.testing.assert_allclose(actual[name], expected[name], atol=2e-10, rtol=2e-10)
    np.testing.assert_allclose(model.coefficients[:3], [.5, 2., -.7], atol=2e-11, rtol=0)
    np.testing.assert_allclose(model.coefficients[3:], 0., atol=2e-11, rtol=0)
    np.testing.assert_array_equal(train, before[0])
    for name in labels:
        np.testing.assert_array_equal(labels[name], before[1][name])
    assert record['full_column_rank'] and record['rank'] == 17
    assert record['coefficient_sha256'] == capacity.digest(list(model.coefficients))
    assert record['real_arithmetic_residual_envelope'] == model.real_arithmetic_bound
    assert record['floating_point_sampling_envelope_certified'] is False
    assert len(record['equilibrated_singular_values']) == 17
    assert len(record['column_norms']) == 17
    assert math.isfinite(record['equilibrated_condition_number'])
    assert type(record['full_column_rank']) is bool
    assert json.loads(capacity.payload(record)) == record
    with pytest.raises(FrozenInstanceError):
        model.remaining_time = .5


def test_score_objective_really_uses_derivative_labels_with_declared_weight():
    z, _ = capacity.collocation_rosters()
    zero, one = np.zeros_like(z), np.ones_like(z)
    vfit, vrecord = capacity.fit_residual(z, zero, one, .5, 16, 'VALUE_ONLY')
    sfit, srecord = capacity.fit_residual(z, zero, one, .5, 16, 'VALUE_AND_SCORE')
    assert all(c == 0. for c in vfit.coefficients)
    assert any(abs(c) > 1e-3 for c in sfit.coefficients)
    assert vrecord['train_objective'] == vrecord['train_value_mse'] == 0.
    assert srecord['train_objective'] == srecord['train_value_mse']+srecord['train_score_mse']
    assert srecord['train_objective'] < 1.
    v, d, _ = design(z, 16, remaining_time=.5)
    direct, *_ = np.linalg.lstsq(np.vstack((v, d)), np.concatenate((zero, one)), rcond=1e-12)
    np.testing.assert_allclose(sfit.coefficients, direct, atol=2e-10, rtol=2e-10)


@pytest.mark.parametrize('case', ['objective', 'degree', 'zero_time', 'large_time',
    'nan_time', 'few_rows', 'shape', 'nan_value', 'inf_gradient'])
def test_invalid_fit_contract_is_rejected(case):
    z, _ = capacity.collocation_rosters()
    value, gradient = np.zeros_like(z), np.ones_like(z)
    tau, degree, objective = .5, 16, 'VALUE_ONLY'
    if case == 'objective': objective = 'VALUE_AND_HESSIAN'
    elif case == 'degree': degree = 17
    elif case == 'zero_time': tau = 0.
    elif case == 'large_time': tau = 1.01
    elif case == 'nan_time': tau = math.nan
    elif case == 'few_rows': z, value, gradient = z[:16], value[:16], gradient[:16]
    elif case == 'shape': value = value[:, None]
    elif case == 'nan_value': value[0] = math.nan
    else: gradient[0] = math.inf
    with pytest.raises(ValueError):
        capacity.fit_residual(z, value, gradient, tau, degree, objective)


def test_pointwise_comparison_uses_target_relative_tolerances_and_all_coordinates():
    target = {key: np.array([0., -2., 3.]) for key in capacity.TOLERANCES}
    approximation = {}
    for key, (atol, rtol) in capacity.TOLERANCES.items():
        threshold = atol+rtol*np.abs(target[key])
        approximation[key] = target[key]+np.array([0., .5, 2.])*threshold
    report = capacity.compare_arrays(approximation, target)
    for key, result in report.items():
        error = approximation[key]-target[key]
        assert result['count'] == 3 and result['failure_count'] == 1
        assert result['passed_pointwise_approximation_tolerance'] is False
        assert result['max_abs'] == float(np.max(np.abs(error)))
        assert result['rms'] == float(np.sqrt(np.mean(error**2)))
        assert result['maximum_error_over_threshold'] == pytest.approx(2.)
    equal = capacity.compare_arrays(target, target)
    assert all(r['failure_count'] == 0 and r['rms'] == 0. for r in equal.values())


@pytest.mark.parametrize('case', ['shape', 'empty', 'nan'])
def test_comparison_rejects_incomplete_or_nonfinite_arrays(case):
    target = {key: np.zeros(2) for key in capacity.TOLERANCES}
    actual = deepcopy(target)
    if case == 'shape': actual['value'] = np.zeros((2, 1))
    elif case == 'empty': target['value'] = actual['value'] = np.zeros(0)
    else: actual['gradient'][1] = math.nan
    with pytest.raises(ValueError):
        capacity.compare_arrays(actual, target)


@pytest.mark.parametrize('scenario', capacity.SCENARIOS)
def test_target_and_baseline_conventions_match_at_terminal_and_other_score_is_zero(scenario):
    grid, uncapped, continuous = capacity.target_bundle(scenario)
    assert grid.grid == capacity.GRID
    assert grid.spec == uncapped.spec == continuous.spec
    z = np.array([-4., 0., 4.])
    terminal = capacity._rows(grid, 1., z)
    direct = capacity._rows(uncapped, 1., z, baseline=True)
    for key in terminal:
        np.testing.assert_allclose(terminal[key], direct[key], atol=1e-13, rtol=1e-13)
    for u in capacity.GRID:
        for oracle, method in [(grid, 'log_likelihood_derivatives'), (uncapped, 'uncapped_log_likelihood_derivatives')]:
            row = getattr(oracle, method)(u, 'OTHER')
            assert row['gradient'] == row['hessian'] == 0.
    with pytest.raises(ValueError):
        capacity.target_bundle(('undeclared', .8, .7))


def test_capacity_floor_is_a_gauge_independent_lower_bound_not_an_old_network_fit():
    a = capacity._capacity_floor([1., 3., 4.], [0., 1., 0.], .5)
    b = capacity._capacity_floor([8., 10., 11.], [-2., -1., -2.], .5)
    assert a == b
    assert a['required_correction_diameter'] == 3.
    assert a['old_allowed_diameter'] == .25
    assert a['old_class_uniform_error_lower_bound_any_gauge'] == 1.375


def test_terminal_component_is_zero_even_for_large_finite_coefficients():
    model = CompactFiberResidual((1e300, -1e300), 0.)
    for value in model.evaluate(np.array([-1e300, 0., 1e300])).values():
        np.testing.assert_array_equal(value, np.zeros(3))
    assert model.real_arithmetic_bound == 0.


@pytest.mark.parametrize('invalid', [{'bad': np.bool_(True)}, {'bad': math.nan}])
def test_write_new_validates_complete_payload_before_creating_file(tmp_path, invalid):
    path = tmp_path/'new-result.json'
    with pytest.raises((TypeError, ValueError)):
        capacity._write_new(path, invalid)
    assert not path.exists()


def test_write_new_preserves_existing_record_and_serializes_valid_fit(tmp_path):
    z, _ = capacity.collocation_rosters()
    target = _manufactured(z, .5)
    _, record = capacity.fit_residual(z, target['value'], target['gradient'], .5, 16, 'VALUE_AND_SCORE')
    path = tmp_path/'fit.json'
    capacity._write_new(path, record)
    original = path.read_bytes()
    assert json.loads(original) == record
    with pytest.raises(FileExistsError):
        capacity._write_new(path, {'replacement': True})
    assert path.read_bytes() == original
