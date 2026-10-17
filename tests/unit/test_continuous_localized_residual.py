"""Independent construction-layer tests; no scientific-target experiment."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, dataclass
import json
import math

import numpy as np
import pytest

from heterodiff.experiments import continuous_localized_residual as localized


def _polynomial(z, tau=1.):
    """Quintic raw-coordinate polynomial and its hand-derived jets."""
    z = np.asarray(z, dtype=np.float64)
    return {
        'value': tau*(.2-.3*z+.07*z**2-.011*z**3+.002*z**4-.0003*z**5),
        'gradient': tau*(-.3+.14*z-.033*z**2+.008*z**3-.0015*z**4),
        'hessian': tau*(.14-.066*z+.024*z**2-.006*z**3),
    }


def test_fixed_rosters_preserve_old_evaluation_without_overlap_or_mutation():
    knots, evaluation = localized.construction_rosters()
    np.testing.assert_array_equal(evaluation, np.linspace(-4., 4., 256))
    assert tuple(knots) == (64, 128, 256)
    for cells, z in knots.items():
        np.testing.assert_array_equal(z, np.linspace(-4.5, 4.5, cells+1))
        assert np.min(np.abs(z[:, None]-evaluation)) > 1e-12
        assert z.dtype == np.float64
    knots[64][:] = 100.
    evaluation[:] = 100.
    again, probes = localized.construction_rosters()
    np.testing.assert_array_equal(again[64], np.linspace(-4.5, 4.5, 65))
    np.testing.assert_array_equal(probes, np.linspace(-4., 4., 256))


def test_roster_collision_is_rejected_before_construction(monkeypatch):
    monkeypatch.setattr(localized.previous, 'collocation_rosters',
        lambda: (np.arange(3), np.array([0.])))
    with pytest.raises(ArithmeticError, match='overlap'):
        localized.construction_rosters()


def test_prospective_specification_keeps_all_arms_and_nonpromotion_scope():
    spec = localized.specification()
    assert spec['route_count'] == 24
    assert spec['continuous_profile_count'] == 192
    assert spec['terminal_zero_profiles'] == 24
    assert spec['primary_arm'] == 'VS_FINITE_DIFFERENCE'
    assert tuple(spec['arms']) == ('VS_FINITE_DIFFERENCE', 'ORACLE_JET_VSH')
    assert spec['approximation_tolerances'] == localized.previous.TOLERANCES
    for key in ('tolerances_changed', 'collars_and_tails_oracle_accuracy_claimed',
            'sampler_integration', 'time_interpolation', 'evaluation_selected_resolution',
            'basis_only_causal_comparison_claimed', 'matched_label_or_compute_budget_claimed'):
        assert spec[key] is False
    assert spec['atomic_corrections'] == 'EXACT_ORACLE_CONSTANTS_NOT_LEARNED'
    assert json.loads(localized.payload(spec))['route_count'] == 24


@pytest.mark.parametrize('tau', [1., .125])
@pytest.mark.parametrize('arm', localized.ARMS)
def test_quintic_reproduction_includes_curvature_and_exactly_one_time_gate(tau, arm):
    z = np.linspace(-4.5, 4.5, 17)
    labels = _polynomial(z, tau)
    before = deepcopy((z, labels))
    kwargs = {'oracle_hessians': labels['hessian']} if arm == 'ORACLE_JET_VSH' else {}
    model, record = localized.build_profile(z, labels['value'], labels['gradient'], tau,
        arm=arm, **kwargs)
    probes = np.linspace(-4.5, 4.5, 119)
    expected = _polynomial(probes, tau)
    for name, values in model.evaluate(probes).items():
        np.testing.assert_allclose(values, expected[name], atol=2e-11, rtol=2e-11)
    np.testing.assert_allclose(record['residual_curvatures_used'], labels['hessian'],
        atol=2e-12, rtol=2e-12)
    np.testing.assert_array_equal(z, before[0])
    for key in labels:
        np.testing.assert_array_equal(labels[key], before[1][key])
    assert record['remaining_time'] == tau
    assert record['oracle_hessian_labels_consumed'] is (arm == 'ORACLE_JET_VSH')
    assert record['coefficient_sha256'] == localized.digest([list(row) for row in model.controls])
    assert json.loads(localized.payload(record)) == record
    with pytest.raises(FrozenInstanceError):
        model.remaining_time = .25


def test_primary_curvature_is_independent_score_difference_not_hessian_labels(monkeypatch):
    z = np.linspace(-1., 1., 9)
    labels = _polynomial(z, .5)
    calls = []
    original = localized.estimate_hessians_from_scores
    def record_call(knots, scores):
        calls.append((knots, scores))
        return original(knots, scores)
    monkeypatch.setattr(localized, 'estimate_hessians_from_scores', record_call)
    _, report = localized.build_profile(z, labels['value'], labels['gradient'], .5,
        arm='VS_FINITE_DIFFERENCE')
    assert calls == [(tuple(z), tuple(labels['gradient']))]
    assert report['oracle_hessian_labels_consumed'] is False
    with pytest.raises(ValueError, match='must not consume'):
        localized.build_profile(z, labels['value'], labels['gradient'], .5,
            arm='VS_FINITE_DIFFERENCE', oracle_hessians=labels['hessian'])
    def forbidden(*args):
        raise AssertionError('VSH control must consume its explicit jet instead')
    monkeypatch.setattr(localized, 'estimate_hessians_from_scores', forbidden)
    _, vsh = localized.build_profile(z, labels['value'], labels['gradient'], .5,
        arm='ORACLE_JET_VSH', oracle_hessians=labels['hessian']+3.)
    np.testing.assert_array_equal(vsh['residual_curvatures_used'], labels['hessian']+3.)


@pytest.mark.parametrize('case', ['unknown_arm', 'zero_time', 'large_time', 'bool_time',
    'nan_time', 'few_knots', 'nonuniform_primary', 'shape', 'boolean_values',
    'complex_gradient', 'masked', 'nan_value', 'missing_hessian', 'bad_hessian_shape',
    'nan_hessian'])
def test_invalid_construction_inputs_are_rejected(case):
    z = np.linspace(-1., 1., 9)
    labels = _polynomial(z)
    value, gradient = labels['value'], labels['gradient']
    tau, arm, kwargs = 1., 'VS_FINITE_DIFFERENCE', {}
    if case == 'unknown_arm': arm = 'VALUE_ONLY'
    elif case == 'zero_time': tau = 0.
    elif case == 'large_time': tau = 1.1
    elif case == 'bool_time': tau = True
    elif case == 'nan_time': tau = math.nan
    elif case == 'few_knots': z, value, gradient = z[:4], value[:4], gradient[:4]
    elif case == 'nonuniform_primary': z[3] += .01
    elif case == 'shape': value = value[:, None]
    elif case == 'boolean_values': value = value > 0
    elif case == 'complex_gradient': gradient = gradient.astype(complex)
    elif case == 'masked': value = np.ma.array(value, mask=False)
    elif case == 'nan_value': value[3] = math.nan
    elif case == 'missing_hessian': arm = 'ORACLE_JET_VSH'
    elif case == 'bad_hessian_shape':
        arm, kwargs = 'ORACLE_JET_VSH', {'oracle_hessians': np.zeros((9, 1))}
    else:
        arm, kwargs = 'ORACLE_JET_VSH', {'oracle_hessians': np.full(9, math.nan)}
    with pytest.raises(ValueError):
        localized.build_profile(z, value, gradient, tau, arm=arm, **kwargs)


def test_whole_roster_bound_includes_both_collars_tails_and_atomic_constants():
    z = np.linspace(-1., 1., 9)
    values = np.zeros_like(z)
    scores = np.full_like(z, 12.)
    model, _ = localized.build_profile(z, values, scores, .25, arm='VS_FINITE_DIFFERENCE')
    bounds = localized.profile_bounds(model, {'EMPTY': -70., 'OTHER': 80.})
    controls = .25*np.asarray(model.controls)
    assert bounds['continuous_real_range'] == [float(controls.min()), float(controls.max())]
    assert max(abs(controls[0]).max(), abs(controls[-1]).max()) > abs(controls[1:-1]).max()
    assert bounds['mixed_real_range'] == [-70., 80.]
    assert bounds['whole_projection_real_absolute_bound'] == 80.
    assert bounds['whole_projection_real_oscillation_bound'] == 150.
    probes = np.r_[[-1e100], np.linspace(-2., 2., 513), [1e100]]
    actual = model.evaluate(probes)
    for key, bound_key in [('value', 'continuous_real_absolute_bound'),
            ('gradient', 'continuous_real_score_absolute_bound'),
            ('hessian', 'continuous_real_hessian_absolute_bound')]:
        assert np.max(np.abs(actual[key])) <= bounds[bound_key]*(1.+1e-12)
    for key in actual:
        np.testing.assert_array_equal(actual[key][[0, -1]], np.zeros(2))
    assert bounds['includes_core_collars_tails_and_atomic_values'] is True
    assert bounds['floating_point_outward_certificate'] is False
    assert bounds['used_by_sampler'] is False
    with pytest.raises(ArithmeticError, match='nonfinite'):
        localized.profile_bounds(model, {'EMPTY': math.nan})


@dataclass(frozen=True)
class _ManufacturedSpec:
    description: str = 'polynomial_harness_only_not_a_scientific_oracle'


class _ManufacturedOracle:
    spec = _ManufacturedSpec()
    def evidence(self):
        return .5

    @staticmethod
    def _row(u, state, coordinate, scale):
        tau = 1.-u
        if state == 'CONTINUOUS':
            p = _polynomial(float(coordinate), tau*scale)
            return {'log_likelihood': float(-2.-.2*coordinate**2+p['value']),
                'gradient': float(-.4*coordinate+p['gradient']), 'hessian': float(-.4+p['hessian'])}
        base = {'EMPTY': -3., 'OTHER': -5.}[state]
        correction = {'EMPTY': .8, 'OTHER': -.4}[state]
        return {'log_likelihood': base+tau*scale*correction, 'gradient': 0., 'hessian': 0.}

    def log_likelihood_derivatives(self, u, state, coordinate=None):
        return self._row(u, state, coordinate, 1.)

    def uncapped_log_likelihood_derivatives(self, u, state, coordinate=None):
        return self._row(u, state, coordinate, .4)


def test_reduced_fake_oracle_harness_checks_all_metrics_arms_and_terminal(monkeypatch, tmp_path):
    monkeypatch.setattr(localized, 'SCENARIOS', (('manufactured', 0., 0.),))
    monkeypatch.setattr(localized, 'CELLS', (8,))
    oracle = _ManufacturedOracle()
    monkeypatch.setattr(localized.previous, 'target_bundle', lambda scenario: (oracle, oracle, oracle))
    callbacks, routes = [], []
    def check():
        callbacks.append(True)
    def save(route):
        routes.append(route)
        localized.previous._write_new(tmp_path/f"route-{route['ordinal']}.json", route)
    report = localized.run_comparison(check, save)
    assert report['completed_routes'] == 4
    assert report['completed_active_profiles'] == 32
    assert report['completed_terminal_zero_profiles'] == 4
    assert len(callbacks) == 4*9+1
    assert report['routes'] == routes
    assert {(r['method'], r['arm']) for r in routes} == {
        (method, arm) for method in localized.METHODS for arm in localized.ARMS}
    target_rows = report['references'][0]['target_rows']
    for route in routes:
        assert route['all_active_value_score_hessian_checks_passed'] is True
        for key, error in route['active_probe_errors'].items():
            nodes = [node['candidate_errors'][key] for node in route['nodes'][:-1]]
            assert error['probe_count'] == 2048 and error['failure_count'] == 0
            assert error['max_abs'] == max(node['max_abs'] for node in nodes)
            assert error['rms'] == math.sqrt(sum(node['rms']**2 for node in nodes)/8)
        for node, target in zip(route['nodes'], target_rows):
            for key in localized.TOLERANCES:
                np.testing.assert_array_equal(node['physical'][key],
                    np.asarray(node['baseline'][key])+np.asarray(node['residual'][key]))
            actual = np.asarray(node['physical']['value'])
            truth = np.asarray(target['evaluation']['value'])
            contrast = (actual-node['baseline_atoms']['EMPTY']
                -node['atomic_residuals_exact_oracle_not_learned']['EMPTY'])-(truth-target['atoms']['EMPTY'])
            assert node['E_to_C_log_rate_ratio_error_max_abs'] == float(np.max(abs(contrast)))
            assert node['E_to_C_relative_rate_ratio_error_max_abs'] == float(np.max(abs(np.expm1(contrast))))
            for atom in ('EMPTY', 'OTHER'):
                assert node['baseline_atoms'][atom]+node['atomic_residuals_exact_oracle_not_learned'][atom] == pytest.approx(target['atoms'][atom])
        terminal = route['nodes'][-1]
        assert terminal['construction']['terminal_zero_no_oracle_labels_consumed'] is True
        for array in terminal['residual'].values():
            np.testing.assert_array_equal(array, np.zeros(256))
    scope = report['scope']
    assert scope['primary_consumed_oracle_hessian_labels'] is False
    assert scope['control_consumed_oracle_hessian_labels'] is True
    for key in ('native_BCE_learner_repaired_or_qualified', 'sampler_or_endpoint_law_qualified',
            'time_interpolation_selected', 'sampling_envelope_FP_certified'):
        assert scope[key] is False
    encoded = localized.payload(report)
    assert json.loads(encoded)['completed_routes'] == 4
    assert len(list(tmp_path.glob('route-*.json'))) == 4


@pytest.mark.parametrize('bad_payload', [{'bad': np.bool_(True)}, {'bad': math.nan}])
def test_export_validation_occurs_before_exclusive_file_creation(tmp_path, bad_payload):
    path = tmp_path/'invalid.json'
    with pytest.raises((ValueError, TypeError)):
        localized.previous._write_new(path, bad_payload)
    assert not path.exists()
    valid = {'complete': True, 'value': .5}
    localized.previous._write_new(path, valid)
    assert json.loads(path.read_bytes()) == valid
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        localized.previous._write_new(path, {'replacement': True})
    assert path.read_bytes() == before
