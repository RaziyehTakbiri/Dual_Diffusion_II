"""FD7 construction and archive-comparison tests; no scientific target fits."""
from copy import deepcopy
import json
import math

import numpy as np
from numpy.polynomial import Polynomial
import pytest

from heterodiff.experiments import continuous_localized_curvature as fd7


def test_fixed_protocol_keeps_same_knots_probes_labels_and_tolerances():
    knots, probes = fd7.construction_rosters()
    old_knots, old_probes = fd7.localized.construction_rosters()
    assert np.array_equal(knots, old_knots[256])
    assert np.array_equal(probes, old_probes)
    assert np.min(np.abs(knots[:, None]-probes)) > 1e-12
    spec = fd7.specification()
    assert spec['route_count'] == 4 and spec['active_profile_count'] == 32
    assert spec['terminal_zero_profile_count'] == 4
    assert spec['core_cells'] == 256 and spec['maximum_seconds'] == 300
    assert spec['approximation_tolerances'] == fd7.previous.TOLERANCES
    assert spec['oracle_hessian_labels_consumed'] is False
    assert spec['archive']['refit'] is False
    assert spec['sampler_integration'] is False
    assert spec['resolution_selection'] is False and spec['retries'] == 0
    assert json.loads(fd7.payload(spec))['route_count'] == 4
    # Mutating returned arrays must not change later rosters or older modules.
    knots[:] = 0.
    assert np.array_equal(fd7.construction_rosters()[0], old_knots[256])
    assert fd7.localized.CELLS == (64, 128, 256)
    assert fd7.localized.ARMS == ('VS_FINITE_DIFFERENCE', 'ORACLE_JET_VSH')


@pytest.mark.parametrize('tau', [1., .125])
@pytest.mark.parametrize('degree', [0, 3, 5])
def test_manufactured_quintic_profiles_reproduce_jets_without_hessian_labels(tau, degree):
    knots = np.linspace(-4.5, 4.5, 33)
    polynomial = Polynomial(tuple((-1)**i*.1/(i+1) for i in range(degree+1)))
    values, scores = tau*polynomial(knots), tau*polynomial.deriv(1)(knots)
    model, record = fd7.build_profile(knots, values, scores, tau)
    probes = np.linspace(-4.5, 4.5, 201)
    for name, derivative in [('value', 0), ('gradient', 1), ('hessian', 2)]:
        assert np.allclose(model.evaluate(probes)[name], tau*polynomial.deriv(derivative)(probes), rtol=2e-10, atol=2e-10)
    assert record['oracle_hessian_labels_consumed'] is False
    assert record['arm'] == fd7.ARM
    assert np.allclose(record['residual_curvatures_used'], tau*polynomial.deriv(2)(knots), rtol=2e-11, atol=2e-11)
    assert record['coefficient_sha256'] == fd7.digest([list(row) for row in model.controls])
    assert json.loads(fd7.payload(record)) == record


def test_primary_rejects_hessian_labels_and_keeps_input_arrays_unchanged():
    knots = np.linspace(-1., 1., 9)
    values, scores = knots**2, 2*knots
    saved = deepcopy((knots, values, scores))
    with pytest.raises(ValueError, match='must not consume'):
        fd7.build_profile(knots, values, scores, 1., oracle_hessians=np.full_like(knots, 2.))
    model, _ = fd7.build_profile(knots, values, scores, 1.)
    for actual, expected in zip((knots, values, scores), saved):
        assert np.array_equal(actual, expected)
    assert model.knots[0] == -2. and model.knots[-1] == 2.
    for field in ('gradient', 'hessian'):
        assert np.array_equal(model.evaluate(np.array([-1e100, 1e100]))[field], np.zeros(2))


@pytest.mark.parametrize('case', ['time', 'booltime', 'shape', 'mask', 'bool', 'complex', 'short', 'nonuniform', 'nan'])
def test_invalid_construction_inputs_fail_before_building(case):
    knots = np.linspace(-1., 1., 9)
    values, scores, tau = knots**2, 2*knots, 1.
    if case == 'time': tau = 0.
    elif case == 'booltime': tau = True
    elif case == 'shape': values = values[:, None]
    elif case == 'mask': scores = np.ma.array(scores, mask=False)
    elif case == 'bool': values = values > 0
    elif case == 'complex': scores = scores.astype(complex)
    elif case == 'short': knots, values, scores = knots[:6], values[:6], scores[:6]
    elif case == 'nonuniform': knots[3] += .01
    else: values[0] = math.nan
    with pytest.raises(ValueError):
        fd7.build_profile(knots, values, scores, tau)


def _manufactured_archive_route():
    zeros = {name: [0., 0.] for name in fd7.TOLERANCES}
    targets = {u: {'evaluation': deepcopy(zeros), 'atoms': {'EMPTY': 0., 'OTHER': 0.}} for u in fd7.GRID}
    route = {'ordinal': 6, 'arm': 'ORACLE_JET_VSH', 'core_cells': 256,
        'largest_whole_projection_real_absolute_bound': 3.,
        'nodes': [{'u': u, 'physical': deepcopy(zeros), 'construction': {'coefficient_sha256': 'manufactured'}} for u in fd7.GRID]}
    return route, targets


def test_archival_comparison_uses_preserved_arrays_not_new_construction():
    route, targets = _manufactured_archive_route()
    original = deepcopy(route)
    route['nodes'][0]['physical']['gradient'][0] = .01
    expected_route = deepcopy(route)
    report = fd7.compare_archival_control(route, targets)
    assert report['refit_performed'] is False
    assert report['archived_control_used_extra_hessian_supervision'] is True
    assert report['oracle_hessians_consumed_by_current_construction'] is False
    assert report['active_probe_errors']['gradient']['failure_count'] == 1
    assert report['active_probe_errors']['gradient']['probe_count'] == 16
    assert report['source_route_sha256'] == fd7.digest(expected_route)
    assert route == expected_route and route != original


def test_archived_target_check_records_roundoff_and_refuses_other_target():
    _, targets = _manufactured_archive_route()
    reference = {'target_rows': [{'u': u, 'evaluation': deepcopy(targets[u]['evaluation']), 'atoms': deepcopy(targets[u]['atoms'])} for u in fd7.GRID]}
    result = fd7._check_archived_targets(reference, targets)
    assert result['all_continuous_target_arrays_bitwise_equal'] is True
    reference['target_rows'][0]['evaluation']['value'][0] = 1e-14
    result = fd7._check_archived_targets(reference, targets)
    assert result['all_continuous_target_arrays_bitwise_equal'] is False
    assert result['maximum_target_roundoff_difference'] == 1e-14
    reference['target_rows'][0]['evaluation']['value'][0] = .01
    with pytest.raises(ValueError, match='target differs'):
        fd7._check_archived_targets(reference, targets)


def test_wrong_archive_is_rejected_without_any_target_execution(tmp_path):
    archive = tmp_path/'other.json'
    archive.write_text('{}\n')
    with pytest.raises(ValueError, match='predeclared archive'):
        fd7.load_archive(archive)


def test_archive_node_roster_mismatch_is_refused():
    route, targets = _manufactured_archive_route()
    route['nodes'][0]['u'] = .0625
    with pytest.raises(ValueError, match='node roster'):
        fd7.compare_archival_control(route, targets)
