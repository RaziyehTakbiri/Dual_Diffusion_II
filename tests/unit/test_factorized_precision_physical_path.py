"""CPU-only tests of the candidate's actual physical input/gradient boundary.

The reference differentiates through CPU64 -> encoded FP32 -> graph FP64.
It does not confuse gradients at promoted batch coordinates with gradients at
the physical interface's original coordinates. No CUDA/data/job is requested.
"""
from copy import deepcopy
from dataclasses import replace

import pytest
import torch

from heterodiff.experiments import factorized_base_precision as precision
from heterodiff.experiments import factorized_device_training as training
from heterodiff.experiments.factorized_conditional_training import (
    FactorizedObservation, FactorizedTrainingBatch,
)
from heterodiff.models.factorized_device_energy_torch import (
    DeviceFactorizedEnergy, device_configuration_batch,
)
from tests.unit.test_factorized_device_training import fixture


DOMAINS = ('R3-PHYS', 'R4-RETAIL')
METHODS = ('association-aware-guide-plus-residual', 'unified-direct-conditioner')


@pytest.fixture(autouse=True)
def cpu_one_thread():
    before = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(before)


def setup(domain='R3-PHYS', method=METHODS[0], *, conditional=False, policy=None):
    source, reference, base, learner, context = fixture(domain, method)
    base = DeviceFactorizedEnergy.from_cpu(base, 'cpu')
    learner = training.DeviceFactorizedConditionalModel.from_cpu(learner, 'cpu')
    observation = FactorizedObservation((source[-1],), domain, context.task_id, context.context_bytes)
    kwargs = dict(base_context=context.base_context, clean_hold=reference.schedule.clean_hold)
    if conditional:
        kwargs.update(conditional_model=learner, observation=observation)
    if policy is not None:
        kwargs['precision_policy'] = policy
    physical = training.DeviceFactorizedPhysicalPotential(base, **kwargs)
    return source, base, learner, physical, kwargs, observation


def explicit_reference_chain(physical, u, state):
    roots = tuple(torch.tensor([] if not e.key.dimension else [e.coordinate],
        dtype=torch.float64, device='cpu', requires_grad=True) for e in state)
    clamped = min(u, physical.base.architecture.horizon - physical.clean_hold)
    encoded = device_configuration_batch((state,), (clamped,), physical.base_context,
        physical.base.architecture, device='cpu', coordinates=roots)
    # Build the promoted graph explicitly rather than calling the public helper.
    promoted = replace(encoded, coordinates=tuple(x.double() for x in encoded.coordinates),
        forward_time=encoded.forward_time.double(), context=encoded.context.double())
    parameters = {name: p.double() for name, p in physical.base.named_parameters()}
    value = precision._functional_energy(physical.base.architecture, promoted, parameters)[0]
    if roots and value.requires_grad:
        original_gradients = torch.autograd.grad(value, roots, retain_graph=True, allow_unused=True)
        promoted_gradients = torch.autograd.grad(value, promoted.coordinates, allow_unused=True)
    else:
        original_gradients = promoted_gradients = (None,) * len(roots)
    rows = tuple(tuple(float(x) for x in (torch.zeros_like(root) if g is None else g))
                 for root, g in zip(roots, original_gradients))
    return float(value.detach()), rows, encoded, original_gradients, promoted_gradients


@pytest.mark.parametrize('domain', DOMAINS)
def test_physical_value_gradient_matches_original_cpu64_root_reference_chain(domain):
    source, _, _, physical, _, _ = setup(domain, policy=precision.PRECISION_POLICY)
    reference_value, reference_rows, encoded, roots, promoted = explicit_reference_chain(physical, .5, source)
    value, rows = physical.value_grad(.5, source)
    assert value == reference_value == physical.value(.5, source)
    assert rows == reference_rows
    assert encoded.coordinates[-1].dtype == torch.float32
    assert encoded.coordinates[-1].item() == torch.tensor(source[-1].coordinate, dtype=torch.float32).item()
    assert encoded.coordinates[-1].item() != source[-1].coordinate
    cast_rounding_observed = False
    for root, high in zip(roots, promoted):
        if high is not None:
            assert root.dtype == high.dtype == torch.float64
            assert torch.equal(root, high.float().double())
            cast_rounding_observed |= not torch.equal(root, high)
    assert cast_rounding_observed, 'fixture must expose the physical FP32 input-gradient cast boundary'
    assert all(not p.requires_grad and p.grad is None and p.dtype == torch.float32
               for p in physical.base.parameters())


@pytest.mark.parametrize('domain', DOMAINS)
def test_fp32_input_quantization_is_preserved_not_silently_removed(domain):
    source, _, _, physical, _, _ = setup(domain, policy=precision.PRECISION_POLICY)
    shifted = (*source[:-1], replace(source[-1], coordinate=source[-1].coordinate + 2.**-45))
    assert shifted[-1].coordinate != source[-1].coordinate
    assert torch.tensor(shifted[-1].coordinate, dtype=torch.float32).item() == torch.tensor(
        source[-1].coordinate, dtype=torch.float32).item()
    assert physical.value_grad(.5, shifted) == physical.value_grad(.5, source)


@pytest.mark.parametrize('domain', DOMAINS)
@pytest.mark.parametrize('state_kind', ('empty', 'atomic', 'duplicates', 'permuted'))
def test_empty_atomic_and_duplicate_occurrence_gradient_alignment(domain, state_kind):
    source, _, _, physical, _, _ = setup(domain, policy=precision.PRECISION_POLICY)
    states = {'empty': (), 'atomic': (source[0],),
              'duplicates': (source[0], source[1], source[1]),
              'permuted': (replace(source[1], coordinate=-.3), source[0], source[1])}
    state = states[state_kind]
    value, rows, _, _, _ = explicit_reference_chain(physical, .5, state)
    assert physical.value_grad(.5, state) == (value, rows)
    assert tuple(len(row) for row in rows) == tuple(e.key.dimension for e in state)
    reverse_value, reverse_rows = physical.value_grad(.5, tuple(reversed(state)))
    assert value == reverse_value and rows == tuple(reversed(reverse_rows))


@pytest.mark.parametrize('domain', DOMAINS)
@pytest.mark.parametrize('method', METHODS)
def test_candidate_clean_hold_tilt_and_conditional_precision_boundaries(domain, method):
    source, base, learner, candidate, kwargs, observation = setup(
        domain, method, conditional=True, policy=precision.PRECISION_POLICY)
    legacy = training.DeviceFactorizedPhysicalPotential(base, **{**kwargs, 'precision_policy': 'LEGACY_FP32'})
    base_only = training.DeviceFactorizedPhysicalPotential(base, base_context=kwargs['base_context'],
        clean_hold=.25, precision_policy=precision.PRECISION_POLICY)
    seen = []
    def check_conditioner_fp32(_module, arguments):
        batch = arguments[0]
        assert batch.forward_time.dtype == batch.context.dtype == torch.float32
        assert all(x.dtype == torch.float32 for x in batch.coordinates)
        seen.append(True)
    hook = candidate.model.conditioner.register_forward_pre_hook(check_conditioner_fp32)
    try:
        for u in (0., .5, .75, .875, 1.):
            assert candidate.initialization_log_tilt(u, source) == legacy.initialization_log_tilt(u, source)
            coordinates = candidate._coordinates(source, False)
            tilt = candidate.model.baseline((source,), (u,), (observation,), coordinates=coordinates)
            tilt = tilt + candidate.model.residual((source,), (u,), (observation,), coordinates=coordinates)
            assert candidate.value(u, source) == base_only.value(u, source) + float(tilt[0].detach())
        assert candidate.value_grad(.75, source) == candidate.value_grad(.875, source) == candidate.value_grad(1., source)
    finally:
        hook.remove()
    assert seen
    assert candidate.initialization_residual_log_tilt(source) == legacy.initialization_residual_log_tilt(source)
    assert all(p.dtype == torch.float32 for p in candidate.model.parameters())
    # Nuisance changes classification logits but never the physical potential.
    row = FactorizedTrainingBatch((source,), (.5,), (observation,), 'LOCAL_PRECISION_TEST')
    logits_before = learner.logits(row).detach().clone()
    nuisance_before = learner.nuisance((observation,)).detach().double()
    with torch.no_grad():
        learner.nuisance.output.bias.add_(3.)
    nuisance_delta = learner.nuisance((observation,)).detach().double() - nuisance_before
    assert bool((nuisance_delta != 0).all())
    # Compare the actual FP32 nuisance change, not an invented exact +3 output:
    # the FP32 affine operation rounds before its unchanged FP64 logit addition.
    torch.testing.assert_close(learner.logits(row) - logits_before,
        nuisance_delta, atol=1e-14, rtol=0.)
    changed = training.DeviceFactorizedPhysicalPotential(base, **kwargs)
    assert changed.value_grad(.5, source) == candidate.value_grad(.5, source)
    assert changed.initialization_log_tilt(0., source) == candidate.initialization_log_tilt(0., source)
    with torch.no_grad():
        base.readout_output.bias.add_(1.)
    altered_base = training.DeviceFactorizedPhysicalPotential(base, **kwargs)
    assert altered_base.value(.5, source) != candidate.value(.5, source)
    assert altered_base.initialization_log_tilt(0., source) == candidate.initialization_log_tilt(0., source)
    assert altered_base.initialization_residual_log_tilt(source) == candidate.initialization_residual_log_tilt(source)


@pytest.mark.parametrize('domain', DOMAINS)
def test_legacy_default_exact_and_candidate_snapshot_and_initialization_exclude_base_changes(domain):
    source, base, _, default, kwargs, _ = setup(domain)
    explicit = training.DeviceFactorizedPhysicalPotential(base, **kwargs, precision_policy='LEGACY_FP32')
    candidate = training.DeviceFactorizedPhysicalPotential(base, **kwargs, precision_policy=precision.PRECISION_POLICY)
    before = candidate.value_grad(.5, source)
    for u in (0., .5, .75, 1.):
        assert default.value_grad(u, source) == explicit.value_grad(u, source)
    with torch.no_grad():
        base.readout_output.bias.add_(1.)
    after = training.DeviceFactorizedPhysicalPotential(base, **kwargs, precision_policy=precision.PRECISION_POLICY)
    assert before == candidate.value_grad(.5, source)
    assert after.value(.5, source) != before[0]
    assert candidate.initialization_log_tilt(0., source) == after.initialization_log_tilt(0., source) == 0.
    assert candidate.initialization_residual_log_tilt(source) == after.initialization_residual_log_tilt(source) == 0.
    assert candidate.precision_policy == precision.PRECISION_POLICY
    with pytest.raises(AttributeError):
        candidate.precision_policy = 'LEGACY_FP32'


def valid_energy_inputs():
    source, base, _, _, _, _ = setup()
    roots = tuple(torch.tensor([] if not e.key.dimension else [e.coordinate],
        dtype=torch.float64, device='cpu', requires_grad=True) for e in source)
    batch = device_configuration_batch((source,), (.5,), torch.zeros(1, 64, device='cpu'),
        base.architecture, device='cpu', coordinates=roots)
    return base, batch


def test_public_energy_is_fp64_preserves_parameters_rng_and_differentiable_inputs():
    base, batch = valid_energy_inputs()
    before = deepcopy(base.state_dict())
    rng = torch.random.get_rng_state().clone()
    values = precision.precision_stable_base_energy(base, batch)
    assert values.dtype == torch.float64 and values.device.type == 'cpu' and values.shape == (1,)
    values.sum().backward()
    assert all(p.grad is not None and p.grad.dtype == torch.float32 and p.grad.device.type == 'cpu'
               for p in base.parameters())
    assert all(torch.equal(value, base.state_dict()[name]) for name, value in before.items())
    assert torch.equal(rng, torch.random.get_rng_state())


@pytest.mark.parametrize('bad', ('binding', 'fp64_batch', 'owner', 'resource', 'nonfinite', 'time', 'model_dtype', 'model_device', 'extra_parameter', 'wrong_model'))
def test_public_energy_rejects_invalid_binding_resource_and_parameter_ownership_before_graph(monkeypatch, bad):
    base, batch = valid_energy_inputs()
    if bad == 'binding':
        batch = replace(batch, architecture_sha256='wrong')
    elif bad == 'fp64_batch':
        batch = replace(batch, forward_time=batch.forward_time.double())
    elif bad == 'owner':
        batch = replace(batch, owners=(1, 1))
    elif bad == 'resource':
        batch = replace(batch, metadata_keys=batch.metadata_keys * 9,
            coordinate_dimensions=batch.coordinate_dimensions * 9,
            coordinates=batch.coordinates * 9, owners=batch.owners * 9)
    elif bad == 'nonfinite':
        batch = replace(batch, context=torch.full_like(batch.context, float('nan')))
    elif bad == 'time':
        batch = replace(batch, forward_time=torch.tensor([2.], dtype=torch.float32, device='cpu'))
    elif bad == 'model_dtype':
        base.double()
    elif bad == 'model_device':
        base.device = torch.device('meta')
    elif bad == 'extra_parameter':
        base.register_parameter('extra', torch.nn.Parameter(torch.ones(1, device='cpu')))
    else:
        base = object()
    def forbidden(*_args, **_kwargs):
        pytest.fail('invalid public input reached the numerical graph')
    monkeypatch.setattr(precision, '_functional_energy', forbidden)
    with pytest.raises(ValueError):
        precision.precision_stable_base_energy(base, batch)


@pytest.mark.parametrize('policy', ('AUTO', '', None, 1, True, ['LEGACY_FP32']))
def test_unknown_policy_rejected_before_snapshot_copy(monkeypatch, policy):
    _, base, _, _, kwargs, _ = setup()
    def forbidden(*_args, **_kwargs):
        pytest.fail('invalid policy reached snapshot copy')
    monkeypatch.setattr(training, 'deepcopy', forbidden)
    with pytest.raises(ValueError):
        training.DeviceFactorizedPhysicalPotential(base, **kwargs, precision_policy=policy)


def test_public_energy_frozen_parameters_and_meta_default_keep_explicit_cpu_graph():
    base, batch = valid_energy_inputs()
    base.requires_grad_(False)
    with torch.device('meta'):
        value = precision.precision_stable_base_energy(base, batch)
        gradient = torch.autograd.grad(value.sum(), batch.coordinates[-1])[0]
    assert value.dtype == torch.float64 and value.device.type == 'cpu'
    assert gradient.dtype == torch.float32 and gradient.device.type == 'cpu'
    assert all(p.dtype == torch.float32 and p.grad is None for p in base.parameters())
