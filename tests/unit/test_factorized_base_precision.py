"""Local CPU precision controls. Never infer a CUDA pass from these tests."""
from copy import deepcopy
from dataclasses import replace

import pytest
import torch

from heterodiff.experiments.factorized_base_precision import (
    PRECISION_POLICY, _functional_energy, _objective_from_values, _precision_objective,
    _promote_batch,
)
from heterodiff.experiments.factorized_device_qualification import _fixture, _optimizer, TOLERANCES
from heterodiff.experiments.factorized_device_training import device_base_objective_on_corrupted_states
from heterodiff.models.factorized_device_energy_torch import DeviceFactorizedEnergy, device_configuration_batch


@pytest.fixture(autouse=True)
def one_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


def setup(domain='R3-PHYS', method='association-aware-guide-plus-residual'):
    base, _, joint, _, destinations, _ = _fixture(domain, method)
    model = DeviceFactorizedEnergy.from_cpu(base, 'cpu')
    times = (.625, .125, .0)
    source = device_configuration_batch(joint.states, joint.reverse_times,
        torch.zeros(3, 64, device='cpu'), model.architecture, device='cpu', coordinate_gradients=True)
    destination = device_configuration_batch(destinations, joint.reverse_times,
        torch.zeros(3, 64, device='cpu'), model.architecture, device='cpu')
    t = torch.tensor(times, dtype=torch.float32, device='cpu')
    source, destination = replace(source, forward_time=t), replace(destination, forward_time=t)
    kwargs = dict(states=joint.states, destinations=destinations, forward_times=times,
        context=torch.zeros(64, device='cpu'), continuous_rates=(1., 1., 0.),
        jump_rates=(2., 1., .5), jump_weight=1.)
    return model, source, destination, kwargs


def objective(model, source, destination, **kwargs):
    return _precision_objective(model, source, destination, (1., 1., 0.), (2., 1., .5), 1., **kwargs)


def snapshot(model, loss):
    optimizer = _optimizer(model)
    loss.backward()
    gradients = {name: None if p.grad is None else p.grad.clone() for name, p in model.named_parameters()}
    optimizer.step()
    updated = {name: p.detach().clone() for name, p in model.named_parameters()}
    return gradients, updated, optimizer


@pytest.mark.parametrize('domain', ['R3-PHYS', 'R4-RETAIL'])
def test_functional_fp32_is_exact_legacy_algebra_including_higher_derivatives(domain):
    a, source, destination, kwargs = setup(domain)
    b = deepcopy(a)
    old = device_base_objective_on_corrupted_states(a, **kwargs)
    control = objective(b, source, destination, dtype=torch.float32)
    for field in ('total', 'continuous', 'jump'):
        assert torch.equal(getattr(old, field), getattr(control, field))
    ga, pa, _ = snapshot(a, old.total)
    gb, pb, _ = snapshot(b, control.total)
    for name in ga:
        assert (ga[name] is None) == (gb[name] is None)
        if ga[name] is not None:
            assert torch.equal(ga[name], gb[name]), name
        assert torch.equal(pa[name], pb[name]), name


@pytest.mark.parametrize('domain', ['R3-PHYS', 'R4-RETAIL'])
@pytest.mark.parametrize('method', ['association-aware-guide-plus-residual', 'unified-direct-conditioner'])
def test_shared_fp64_batched_and_rowwise_evaluation_meet_unchanged_update_tolerance(domain, method):
    a, source, destination, _ = setup(domain, method)
    b = deepcopy(a)
    oa, ob = objective(a, source, destination), objective(b, source, destination, rowwise=True)
    torch.testing.assert_close(oa.total, ob.total, atol=1e-13, rtol=1e-13)
    ga, pa, optimizer = snapshot(a, oa.total)
    gb, pb, _ = snapshot(b, ob.total)
    for name in ga:
        if ga[name] is not None:
            assert ga[name].dtype == torch.float32
            torch.testing.assert_close(ga[name], gb[name], atol=1e-12, rtol=1e-5)
        atol, rtol = TOLERANCES['updated_parameter']
        torch.testing.assert_close(pa[name], pb[name], atol=atol, rtol=rtol)
    assert all(p.dtype == torch.float32 for p in a.parameters())
    for state in optimizer.state.values():
        assert state['exp_avg'].dtype == state['exp_avg_sq'].dtype == torch.float32
    assert optimizer.param_groups[0]['eps'] == 1e-8


@pytest.mark.parametrize('domain', ['R3-PHYS', 'R4-RETAIL'])
def test_opt_in_route_preserves_default_and_initial_parameters_and_rng(domain):
    model, source, destination, kwargs = setup(domain)
    before, rng = deepcopy(model.state_dict()), torch.random.get_rng_state().clone()
    default = device_base_objective_on_corrupted_states(model, **kwargs)
    legacy = device_base_objective_on_corrupted_states(model, **kwargs, precision_policy='LEGACY_FP32')
    assert torch.equal(default.total, legacy.total)
    candidate = device_base_objective_on_corrupted_states(model, **kwargs, precision_policy=PRECISION_POLICY)
    direct = objective(model, source, destination)
    assert torch.equal(candidate.total, direct.total)
    assert candidate.source_batch.forward_time.dtype == torch.float64
    assert all(x.dtype == torch.float64 for x in candidate.source_batch.coordinates)
    assert all(torch.equal(p, model.state_dict()[name]) for name, p in before.items())
    assert torch.equal(rng, torch.random.get_rng_state())


@pytest.mark.parametrize('domain', ['R3-PHYS', 'R4-RETAIL'])
def test_shared_parameter_cast_accumulates_before_one_fp32_rounding(domain):
    model, source, destination, _ = setup(domain)
    source64, destination64 = _promote_batch(source, torch.float64), _promote_batch(destination, torch.float64)
    independent = {name: p.detach().double().requires_grad_(p.requires_grad) for name, p in model.named_parameters()}
    loss = _objective_from_values(_functional_energy(model.architecture, source64, independent),
        _functional_energy(model.architecture, destination64, independent), source64, (1., 1., 0.), (2., 1., .5), 1.)
    loss.total.backward()
    expected = {name: p.grad.float() if p.grad is not None else None for name, p in independent.items()}
    objective(model, source, destination).total.backward()
    for name, p in model.named_parameters():
        assert (p.grad is None) == (expected[name] is None)
        if p.grad is not None:
            assert torch.equal(p.grad, expected[name]), name


def test_cast_boundary_regression_on_exact_algebraic_cancellation():
    # Shared FP64 accumulation must preserve a contribution that FP32 loses.
    a = torch.tensor(1., dtype=torch.float32, requires_grad=True, device='cpu')
    shared = a.double()
    (shared * (1. + 2.**-30) - shared).backward()
    assert a.grad.item() == 2.**-30
    b = torch.tensor(1., dtype=torch.float32, requires_grad=True, device='cpu')
    (b.double() * (1. + 2.**-30) - b.double()).backward()
    assert b.grad.item() == 0.


@pytest.mark.parametrize('domain,index', [('R3-PHYS', (93, 167)), ('R4-RETAIL', (5, 64))])
def test_fp64_objective_sensitive_parameter_gradient_finite_difference(domain, index):
    model, source, destination, _ = setup(domain)
    source, destination = _promote_batch(source, torch.float64), _promote_batch(destination, torch.float64)
    params = {name: p.detach().double().requires_grad_(True) for name, p in model.named_parameters()}
    def loss():
        return _objective_from_values(_functional_energy(model.architecture, source, params),
            _functional_energy(model.architecture, destination, params), source, (1., 1., 0.), (2., 1., .5), 1.).total
    parameter = params['readout_hidden.weight']
    analytic = torch.autograd.grad(loss(), parameter)[0][index].item()
    initial = parameter[index].item()
    estimates = []
    # Richardson removes the O(h^2) central-difference truncation term.
    # Keep the original strict derivative check, not a looser tolerance.
    for step in (.01, .005):
        with torch.no_grad():
            parameter[index] = initial + step
        plus = loss().item()
        with torch.no_grad():
            parameter[index] = initial - step
        minus = loss().item()
        estimates.append((plus - minus) / (2 * step))
    with torch.no_grad():
        parameter[index] = initial
    assert (4 * estimates[1] - estimates[0]) / 3 == pytest.approx(analytic, rel=5e-4, abs=2e-12)


@pytest.mark.parametrize('field,value', [('precision_policy', 'AUTO'), ('jump_weight', float('nan')),
    ('continuous_rates', (1., -1., 0.)), ('forward_times', (2., .125, 0.))])
def test_invalid_candidate_inputs_fail_without_parameter_mutation(field, value):
    model, _, _, kwargs = setup()
    kwargs['precision_policy'] = PRECISION_POLICY
    kwargs[field] = value
    before = deepcopy(model.state_dict())
    with pytest.raises(ValueError):
        device_base_objective_on_corrupted_states(model, **kwargs)
    assert all(torch.equal(p, model.state_dict()[name]) for name, p in before.items())


def test_candidate_respects_meta_default_and_frozen_parameters():
    model, _, _, kwargs = setup()
    model.event_hidden.bias.requires_grad_(False)
    with torch.device('meta'):
        loss = device_base_objective_on_corrupted_states(model, **kwargs, precision_policy=PRECISION_POLICY)
        loss.total.backward()
    assert model.event_hidden.bias.grad is None
    assert all(p.grad is None or (p.grad.device.type == 'cpu' and p.grad.dtype == torch.float32)
               for p in model.parameters())


def test_zero_rates_and_identical_destination_preserve_constant_objective_and_negligible_update():
    model, _, _, kwargs = setup()
    kwargs.update(destinations=kwargs['states'], continuous_rates=(0., 0., 0.))
    objective64 = device_base_objective_on_corrupted_states(model, **kwargs, precision_policy=PRECISION_POLICY)
    assert objective64.total.item() == sum(kwargs['jump_rates']) / 3
    before = deepcopy(model.state_dict())
    gradients, updated, _ = snapshot(model, objective64.total)
    # FP64 branch accumulation can retain roundoff, not a bitwise-zero promise.
    assert all(g is None or float(g.abs().max()) < 1e-14 for g in gradients.values())
    atol, rtol = TOLERANCES['updated_parameter']
    for name in before:
        torch.testing.assert_close(updated[name], before[name], atol=atol, rtol=rtol)


def test_extra_parameter_is_rejected_as_in_legacy_graph():
    model, _, _, kwargs = setup()
    model.register_parameter('unexpected', torch.nn.Parameter(torch.ones(1)))
    before = deepcopy(model.state_dict())
    for policy in ('LEGACY_FP32', PRECISION_POLICY):
        with pytest.raises(ValueError, match='parameter count changed'):
            device_base_objective_on_corrupted_states(model, **kwargs, precision_policy=policy)
    assert all(torch.equal(p, model.state_dict()[name]) for name, p in before.items())


@pytest.mark.parametrize('domain', ['R3-PHYS', 'R4-RETAIL'])
def test_precision_candidate_is_connected_to_actual_reference_corruption_update(domain):
    import numpy as np
    from tests.unit.test_factorized_device_training import fixture
    from heterodiff.experiments.factorized_device_training import device_train_base_step
    source, reference, base, _, _ = fixture(domain)
    model = DeviceFactorizedEnergy.from_cpu(base, 'cpu')
    optimizer = _optimizer(model)
    result = device_train_base_step(model, reference, (source,), context=torch.zeros(64),
        rng=np.random.default_rng(7), optimizer=optimizer, sample_count=2, jump_weight=1.,
        precision_policy=PRECISION_POLICY)
    assert result['base_precision_policy'] == PRECISION_POLICY
    assert result['changed_parameter_elements'] > 0
    assert not result['scientific_training_completed']
    assert all(p.dtype == torch.float32 for p in model.parameters())
