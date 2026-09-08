"""Only invented keys/coordinates; no domain or parameter-budget adoption."""
from dataclasses import FrozenInstanceError, replace

import pytest
import torch

from heterodiff.models import factorized_configuration_energy_torch as f


def architecture(**changes):
    fields = dict(metadata_schema_id='EXPLICIT_SYNTHETIC_KEYS_ONLY', total_cap=8,
                  horizon=1.0, value_bound=2.0, coordinate_scale=1.0, context_scale=1.0,
                  limits=f.FactorizedEnergyLimits(4, 16, 128, 512))
    fields.update(changes)
    return f.FactorizedEnergyArchitecture(**fields)


def make_batch(spec, keys=(b'alpha', b'beta'), dimensions=(1, 0), *, owners=None, size=1):
    return f.FactorizedConfigurationBatch(spec.architecture_sha256, keys, dimensions,
        tuple(torch.tensor([0.25], requires_grad=True) if d else torch.empty(0, requires_grad=True)
              for d in dimensions), (0,)*len(keys) if owners is None else owners,
        torch.full((size,), 0.5), torch.zeros(size, 64))


def model_and_batch(**changes):
    spec = architecture(**changes)
    return f.BoundedFactorizedConfigurationEnergy(spec, initialization_seed=91), make_batch(spec)


def test_exact_parameter_formula_no_per_type_heads_and_no_global_rng_mutation():
    spec = architecture()
    before = torch.random.get_rng_state().clone()
    model = f.BoundedFactorizedConfigurationEnergy(spec, initialization_seed=2**64-1)
    assert torch.equal(before, torch.random.get_rng_state())
    assert model.parameter_count == 128*34+91265+(32*32+2*32) == 96705
    assert sum(p.numel() for p in model.metadata_encoder.parameters()) == 1088
    desc = model.description()
    assert desc['internal_context_parameters_already_included'] == 24960
    for name in ('type_roster_or_per_type_heads_used', 'learned_features_injective_claimed',
                 'metadata_coordinate_diffusion_used', 'old_certified_energy_interface_accepted',
                 'global_derivative_certificate_claimed', 'production_domain_schema_or_rates_adopted',
                 'gpu_qualification_claimed'):
        assert desc[name] is False


def test_same_seed_and_declaration_reproduce_parameters_while_changed_seed_does_not():
    spec = architecture()
    first = f.BoundedFactorizedConfigurationEnergy(spec, initialization_seed=28)
    second = f.BoundedFactorizedConfigurationEnergy(spec, initialization_seed=28)
    other = f.BoundedFactorizedConfigurationEnergy(spec, initialization_seed=29)
    assert all(torch.equal(x, y) for x, y in zip(first.parameters(), second.parameters()))
    assert any(not torch.equal(x, y) for x, y in zip(first.parameters(), other.parameters()))
    assert spec.architecture_sha256 == architecture().architecture_sha256
    assert spec.architecture_sha256 != architecture(metadata_schema_id='OTHER').architecture_sha256
    with pytest.raises(FrozenInstanceError):
        spec.total_cap = 9


def test_cpu_placement_is_explicit_even_with_an_ambient_non_cpu_default():
    spec = architecture()
    batch = make_batch(spec)
    empty = make_batch(spec, (), ())
    with torch.device('meta'):
        model = f.BoundedFactorizedConfigurationEnergy(spec, initialization_seed=31)
        assert all(p.device.type == 'cpu' for p in model.parameters())
        assert model(batch).device.type == 'cpu'
        assert model(empty).device.type == 'cpu'


def test_metadata_changes_energy_instead_of_travelling_as_ignored_annotation():
    model, batch = model_and_batch()
    values = []
    for key in (b'alpha', b'alphb', b'alpha\x00', b'alpha\x01', b'\xff'):
        values.append(model(make_batch(model.architecture, (key,), (0,))))
    assert len({float(value.detach()) for value in values}) == len(values)
    assert batch.metadata_keys == (b'alpha', b'beta')


def test_every_byte_is_consumed_no_hashing_vocabulary_or_truncation(monkeypatch):
    model, _ = model_and_batch(limits=f.FactorizedEnergyLimits(4, 16, 256, 512))
    key = bytes(range(256))
    batch = make_batch(model.architecture, (key,), (0,))
    seen = []
    recurrence_calls = []
    original_linear = f.F.linear
    def tracked_linear(values, weight, bias=None):
        if weight is model.metadata_encoder.recurrent_weight:
            recurrence_calls.append(True)
        return original_linear(values, weight, bias)
    monkeypatch.setattr(f.F, 'linear', tracked_linear)
    handle = model.metadata_encoder.register_forward_pre_hook(lambda module, inputs: seen.append(inputs[0]))
    model(batch)
    handle.remove()
    assert seen == [key]
    assert len(recurrence_calls) == len(key)
    work = model.workload(batch)
    assert work['metadata_bytes_consumed'] == work['metadata_recurrence_steps'] == 256
    assert work['metadata_recurrence_matrix_macs'] == 256*32*32
    assert work['metadata_byte_scalar_multiplications'] == 256*32
    assert work['event_affine_macs'] == 34*128+128*128
    assert work['context_affine_macs'] == 65*128+128*128
    assert work['readout_affine_macs'] == 257*128+128*128+128
    assert work['production_budget_adopted'] is False


def test_input_validation_has_no_4096_key_roster_ceiling_or_per_key_parameters():
    spec = architecture(total_cap=5000, limits=f.FactorizedEnergyLimits(1, 5000, 2, 10000))
    model = f.BoundedFactorizedConfigurationEnergy(spec, initialization_seed=17)
    keys = tuple(i.to_bytes(2, 'big') for i in range(5000))
    batch = make_batch(spec, keys, (0,)*len(keys))
    assert model.workload(batch)['events'] == 5000
    assert model.workload(batch)['metadata_bytes_consumed'] == 10000
    assert model.parameter_count == 96705
    # This validates the larger input interface; it does not claim a full-size
    # forward/backward or domain-scale runtime qualification.


def test_permutation_invariance_preserves_duplicate_occurrences_and_gradient_owners():
    model, _ = model_and_batch()
    batch = make_batch(model.architecture, (b'z', b'a', b'z'), (1, 0, 1))
    batch = replace(batch, coordinates=(torch.tensor([-0.4], requires_grad=True),
                                      torch.empty(0, requires_grad=True),
                                      torch.tensor([0.25], requires_grad=True)))
    permutation = (2, 0, 1)
    reordered = replace(batch, **{field: tuple(getattr(batch, field)[i] for i in permutation)
                                  for field in ('metadata_keys', 'coordinate_dimensions', 'coordinates', 'owners')})
    first = model(batch)
    second = model(reordered)
    assert torch.equal(first, second)
    gradients = torch.autograd.grad(first.sum(), (batch.coordinates[0], batch.coordinates[2]))
    repeated_gradients = torch.autograd.grad(second.sum(), (batch.coordinates[0], batch.coordinates[2]))
    assert all(torch.equal(x, y) for x, y in zip(gradients, repeated_gradients))
    one = make_batch(model.architecture, (b'duplicate',), (0,))
    two = make_batch(model.architecture, (b'duplicate', b'duplicate'), (0, 0))
    assert model.workload(two)['cardinalities'] == (2,)
    assert not torch.equal(model(one), model(two))


def test_zero_dimensional_atoms_are_empty_not_diffused_scalar_padding():
    model, _ = model_and_batch()
    atom = make_batch(model.architecture, (b'atomic',), (0,))
    assert model(atom).shape == (1,)
    assert atom.coordinates[0].shape == (0,)
    with pytest.raises(f.FactorizedEnergyError, match='declared shape'):
        model(replace(atom, coordinates=(torch.tensor([0.0]),)))
    with pytest.raises(f.FactorizedEnergyError, match='inconsistent fiber'):
        model(make_batch(model.architecture, (b'same-key', b'same-key'), (0, 1)))


def test_explicit_context_and_time_affect_energy_empty_configurations_are_valid():
    model, _ = model_and_batch()
    batch = make_batch(model.architecture, (), (), size=2)
    baseline = model(batch)
    changed_context = batch.context.clone()
    changed_context[1, 0] = 0.75
    context_result = model(replace(batch, context=changed_context))
    assert torch.equal(baseline[0], baseline[1])
    assert context_result[0] != context_result[1]
    time_result = model(replace(batch, forward_time=torch.tensor([0.0, 1.0])))
    assert time_result[0] != time_result[1]
    assert model.workload(batch)['events'] == 0


def test_cpu_forward_backward_and_one_optimizer_update_has_shared_parameter_gradients():
    model, batch = model_and_batch()
    batch = replace(batch, context=torch.full((1, 64), 0.25))
    before = {name: p.detach().clone() for name, p in model.named_parameters()}
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0)
    optimizer.zero_grad(set_to_none=True)
    loss = (model(batch)-torch.tensor([1.0])).square().mean()
    loss.backward()
    for name in ('metadata_encoder.recurrent_weight', 'metadata_encoder.byte_weight',
                 'event_hidden.weight', 'context_hidden.weight', 'readout_output.weight'):
        parameter = dict(model.named_parameters())[name]
        assert parameter.grad is not None and bool(torch.isfinite(parameter.grad).all())
        assert bool((parameter.grad != 0).any()), name
    assert batch.coordinates[0].grad is not None
    assert bool(torch.isfinite(batch.coordinates[0].grad).all())
    assert batch.coordinates[1].grad is None
    optimizer.step()
    for name in ('metadata_encoder.recurrent_weight', 'event_hidden.weight', 'readout_output.weight'):
        assert not torch.equal(before[name], dict(model.named_parameters())[name].detach())
    assert bool((model(batch).detach().abs() <= model.architecture.value_bound).all())


def test_coordinate_autograd_matches_local_finite_difference():
    model, batch = model_and_batch()
    gradient = torch.autograd.grad(model(batch).sum(), batch.coordinates[0])[0]
    delta = 0.005
    upper = replace(batch, coordinates=(batch.coordinates[0].detach()+delta, batch.coordinates[1]))
    lower = replace(batch, coordinates=(batch.coordinates[0].detach()-delta, batch.coordinates[1]))
    numerical = (model(upper)-model(lower))/(2*delta)
    assert torch.allclose(gradient, numerical, atol=3e-6, rtol=0.03)


@pytest.mark.parametrize('side', [-1, 1])
def test_declared_scalar_value_bound_holds_under_large_finite_parameters(side):
    model, batch = model_and_batch()
    with torch.no_grad():
        model.readout_output.bias.fill_(side*1000)
    result = model(batch)
    assert float(result.detach()) == side*model.architecture.value_bound


@pytest.mark.parametrize('alter', [
    lambda b: replace(b, metadata_keys=(b'', b'beta')),
    lambda b: replace(b, metadata_keys=(bytearray(b'alpha'), b'beta')),
    lambda b: replace(b, metadata_keys=[b'alpha', b'beta']),
    lambda b: replace(b, owners=(True, 0)),
    lambda b: replace(b, owners=(1, 0)),
    lambda b: replace(b, coordinate_dimensions=(True, 0)),
    lambda b: replace(b, coordinate_dimensions=(2, 0)),
    lambda b: replace(b, architecture_sha256='0'*64),
    lambda b: replace(b, coordinates=(torch.tensor([float('nan')]), b.coordinates[1])),
    lambda b: replace(b, coordinates=(torch.tensor([0.25], dtype=torch.float64), b.coordinates[1])),
    lambda b: replace(b, context=torch.zeros(1, 63)),
    lambda b: replace(b, forward_time=torch.tensor([1.01])),
    lambda b: replace(b, coordinates=(b.coordinates[0],)),
])
def test_malformed_or_cross_bound_batch_is_rejected(alter):
    model, batch = model_and_batch()
    with pytest.raises(f.FactorizedEnergyError):
        model(alter(batch))


@pytest.mark.parametrize('limits, keys, dimensions, size', [
    (f.FactorizedEnergyLimits(1, 16, 128, 512), (), (), 2),
    (f.FactorizedEnergyLimits(4, 1, 128, 512), (b'a', b'b'), (0, 0), 1),
    (f.FactorizedEnergyLimits(4, 16, 1, 512), (b'long',), (0,), 1),
    (f.FactorizedEnergyLimits(4, 16, 128, 2), (b'aa', b'bb'), (0, 0), 1),
])
def test_resource_exhaustion_refuses_before_any_metadata_encoder_execution(limits, keys, dimensions, size):
    model = f.BoundedFactorizedConfigurationEnergy(architecture(limits=limits), initialization_seed=0)
    seen = []
    handle = model.metadata_encoder.register_forward_pre_hook(lambda *args: seen.append(True))
    try:
        with pytest.raises(f.FactorizedEnergyResourceError):
            model(make_batch(model.architecture, keys, dimensions, size=size))
    finally:
        handle.remove()
    assert seen == []


def test_total_cap_refuses_instead_of_top_coding_and_parameters_remain_cpu_fp32():
    model, batch = model_and_batch(total_cap=1)
    with pytest.raises(f.FactorizedEnergyResourceError, match='total_cap'):
        model(batch)
    model, batch = model_and_batch()
    model.double()
    with pytest.raises(f.FactorizedEnergyError, match='CPU FP32'):
        model(batch)


@pytest.mark.parametrize('changes', [
    {'total_cap': True}, {'horizon': 0.0}, {'value_bound': float('inf')},
    {'coordinate_scale': 0.1}, {'context_scale': 1e-100}, {'limits': None},
    {'metadata_schema_id': ''},
])
def test_invalid_architecture_refuses(changes):
    with pytest.raises(f.FactorizedEnergyError):
        architecture(**changes)
