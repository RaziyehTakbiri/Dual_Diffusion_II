"""CPU-only graph-copy tests; no CUDA availability or execution is implied."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction

import pytest
import torch

from heterodiff.data.two_domain_factorized_state import FactoredEvent, PhysioStateKey
from heterodiff.models.factorized_configuration_energy_torch import (
    BoundedFactorizedConfigurationEnergy, FactorizedEnergyArchitecture, FactorizedEnergyLimits,
    FactorizedConfigurationBatch, FactorizedEnergyError,
)
from heterodiff.experiments.factorized_conditional_training import (
    FactorizedObservation, FactorizedObservationEncoder, FactorizedObservationNuisance,
    factorized_configuration_batch,
)
from heterodiff.models.factorized_device_energy_torch import (
    DeviceFactorizedEnergy, DeviceFactorizedObservationEncoder, DeviceFactorizedObservationNuisance,
    DeviceFactorizedConfigurationBatch, FactorizedDeviceError, device_configuration_batch, explicit_device,
)


def architecture():
    return FactorizedEnergyArchitecture("factorized-key-v1", 4, 2.0, 1.0, 1.0, 1.0,
                                       FactorizedEnergyLimits(8, 32, 1024, 16384))


def models():
    spec = architecture()
    energy = BoundedFactorizedConfigurationEnergy(spec, initialization_seed=2**64-1)
    encoder = FactorizedObservationEncoder(limits=spec.limits, observation_cap=4,
                                           coordinate_scale=1.0, initialization_seed=73)
    nuisance = FactorizedObservationNuisance(encoder, initialization_seed=14)
    return energy, encoder, nuisance


X = PhysioStateKey(1, "HR", "POSITIVE")
A = FactoredEvent(PhysioStateKey(2, "GCS", "ATOMIC", Fraction(3)))


def states():
    return ((FactoredEvent(X, 0.25), A, FactoredEvent(X, -0.4), FactoredEvent(X, 0.25)), ())


def observations():
    return tuple(FactorizedObservation(s, "R3-PHYS", "full-context-task", b"all\x00raw\xffbytes")
                 for s in (states()[0], (), None))


def variables(roster):
    return tuple(torch.tensor([] if not event.key.dimension else [event.coordinate],
                              dtype=torch.float64, device="cpu", requires_grad=True)
                 for state in roster for event in state)


@pytest.mark.parametrize("index,wrapper", [(0, DeviceFactorizedEnergy),
                                          (1, DeviceFactorizedObservationEncoder),
                                          (2, DeviceFactorizedObservationNuisance)])
def test_copy_preserves_exact_names_values_flags_and_independent_storage_without_rng(index, wrapper):
    source = models()[index].eval()
    list(source.modules())[1].train(True)  # Mixed per-submodule modes are retained too.
    next(source.parameters()).requires_grad_(False)
    before = torch.random.get_rng_state().clone()
    copied = wrapper.from_cpu(source, "cpu")
    assert torch.equal(before, torch.random.get_rng_state())
    assert copied.device == torch.device("cpu") and not copied.training
    assert [(name, m.training) for name, m in source.named_modules()] == [
        (name, m.training) for name, m in copied.named_modules()]
    assert tuple(source.state_dict()) == tuple(copied.state_dict())
    assert tuple(dict(source.named_parameters())) == tuple(dict(copied.named_parameters()))
    for original, other in zip(source.parameters(), copied.parameters()):
        assert torch.equal(original, other) and original.data_ptr() != other.data_ptr()
        assert original.requires_grad == other.requires_grad
    assert copied.parameter_count == sum(p.numel() for p in source.parameters())
    restored = deepcopy(copied)
    assert tuple(restored.state_dict()) == tuple(copied.state_dict())


def test_energy_forward_coordinate_hessian_context_and_parameter_gradient_bitwise_cpu_parity():
    source = models()[0]
    target = DeviceFactorizedEnergy.from_cpu(source, "cpu")
    roster, times = states(), (0.25, 1.4)
    source_x, target_x = variables(roster), variables(roster)
    source_z = torch.full((2, 64), 0.1, dtype=torch.float32, device="cpu", requires_grad=True)
    target_z = source_z.detach().clone().requires_grad_()
    source_batch = factorized_configuration_batch(roster, times, source_z, source.architecture, coordinates=source_x)
    target_batch = device_configuration_batch(roster, times, target_z, target.architecture,
                                               device="cpu", coordinates=target_x)
    a, b = source(source_batch), target(target_batch)
    assert torch.equal(a, b)
    ga = torch.autograd.grad(a.sum(), (*source_x, source_z, *source.parameters()), create_graph=True, allow_unused=True)
    gb = torch.autograd.grad(b.sum(), (*target_x, target_z, *target.parameters()), create_graph=True, allow_unused=True)
    assert ga[1] is gb[1] is None  # A 0D atom has no coordinate in either graph.
    assert all((x is None and y is None) or (x is not None and y is not None and torch.equal(x, y))
               for x, y in zip(ga, gb))
    ha = torch.autograd.grad(ga[0].sum(), source_x[0])[0]
    hb = torch.autograd.grad(gb[0].sum(), target_x[0])[0]
    assert torch.equal(ha, hb) and bool(torch.isfinite(hb).all())
    assert target.workload(target_batch)["metadata_bytes_consumed"] == source.workload(source_batch)["metadata_bytes_consumed"]


@pytest.mark.parametrize("index,wrapper", [(1, DeviceFactorizedObservationEncoder),
                                          (2, DeviceFactorizedObservationNuisance)])
def test_observation_and_nuisance_forward_and_parameter_gradient_bitwise_cpu_parity(index, wrapper):
    source = models()[index]
    target = wrapper.from_cpu(source, "cpu")
    a, b = source(observations()), target(observations())
    assert torch.equal(a, b)
    ga = torch.autograd.grad(a.sum(), tuple(source.parameters()))
    gb = torch.autograd.grad(b.sum(), tuple(target.parameters()))
    assert all(torch.equal(x, y) for x, y in zip(ga, gb))
    assert not torch.equal(b[1], b[2])  # retained empty != overflow


def test_actual_adamw_step_and_moments_match_cpu_reference():
    cpu = models()[0]
    target = DeviceFactorizedEnergy.from_cpu(cpu, "cpu")
    opts = [torch.optim.AdamW(model.parameters(), lr=0.001, betas=(.9, .999), eps=1e-8,
                             weight_decay=0., foreach=False, fused=False) for model in (cpu, target)]
    z = torch.zeros(2, 64, dtype=torch.float32, device="cpu")
    batches = (factorized_configuration_batch(states(), (.1, .8), z, cpu.architecture),
               device_configuration_batch(states(), (.1, .8), z, target.architecture, device="cpu"))
    for model, opt, batch in zip((cpu, target), opts, batches):
        opt.zero_grad(set_to_none=True)
        model(batch).square().mean().backward()
        opt.step()
    for a, b in zip(cpu.parameters(), target.parameters()):
        assert torch.equal(a, b)
        for name in ("step", "exp_avg", "exp_avg_sq"):
            assert torch.equal(opts[0].state[a][name], opts[1].state[b][name])


def test_builder_makes_actual_device_fp32_leaf_rows_and_keeps_supplied_graph():
    spec = architecture()
    z = torch.zeros(2, 64, dtype=torch.float64, device="cpu", requires_grad=True)
    batch = device_configuration_batch(states(), (.2, .4), z, spec, device="cpu", coordinate_gradients=True)
    assert all(x.device.type == "cpu" and x.dtype == torch.float32 and x.is_leaf and x.requires_grad
               for x in batch.coordinates)
    assert batch.coordinates[1].shape == (0,)
    model = DeviceFactorizedEnergy.from_cpu(models()[0], "cpu")
    value = model(batch).sum()
    gradients = torch.autograd.grad(value, (*batch.coordinates, z), create_graph=True, allow_unused=True)
    assert gradients[1] is None
    assert all(g is None or bool(torch.isfinite(g).all()) for g in gradients)
    other = device_configuration_batch(states(), (.2, .4), z, spec, device="cpu", coordinates=batch.coordinates)
    assert all(a is b for a, b in zip(batch.coordinates, other.coordinates))


def test_canonical_pooling_preserves_duplicate_and_permutation_order():
    model = DeviceFactorizedEnergy.from_cpu(models()[0], "cpu")
    roster, z = states(), torch.zeros(2, 64, dtype=torch.float32, device="cpu")
    a = device_configuration_batch(roster, (.25, .5), z, model.architecture, device="cpu")
    b = device_configuration_batch((tuple(reversed(roster[0])), ()), (.25, .5), z, model.architecture, device="cpu")
    assert torch.equal(model(a), model(b))
    assert model.workload(a)["events"] == 4 and model.workload(a)["cardinalities"] == (4, 0)


def test_full_byte_input_and_context_are_consumed_without_alias_or_truncation(monkeypatch):
    encoder = DeviceFactorizedObservationEncoder.from_cpu(models()[1], "cpu")
    consumed, original = [], encoder.bytes.forward
    def record(key):
        consumed.append(key)
        return original(key)
    monkeypatch.setattr(encoder.bytes, "forward", record)
    rows = observations()
    encoder(rows)
    expected = [e.key.canonical_bytes() for e in sorted(rows[0].observed, key=lambda e: e.sort_key)]
    expected += [rows[0].canonical_context_bytes, rows[1].canonical_context_bytes, rows[2].canonical_context_bytes]
    assert consumed == expected
    assert all(b"ff" in raw for raw in (r.canonical_context_bytes for r in rows))


def test_explicit_cpu_allocations_ignore_meta_default_device():
    cpu, encoder, nuisance = models()
    roster, rows = states(), observations()
    z = torch.zeros(2, 64, dtype=torch.float32, device="cpu")
    expected = cpu(factorized_configuration_batch(roster, (.2, .5), z, cpu.architecture))
    before = torch.random.get_rng_state().clone()
    with torch.device("meta"):
        model = DeviceFactorizedEnergy.from_cpu(cpu, "cpu")
        batch = device_configuration_batch(roster, (.2, .5), z, model.architecture, device="cpu", coordinate_gradients=True)
        assert torch.equal(model(batch), expected)
        assert torch.equal(DeviceFactorizedObservationEncoder.from_cpu(encoder, "cpu")(rows), encoder(rows))
        assert torch.equal(DeviceFactorizedObservationNuisance.from_cpu(nuisance, "cpu")(rows), nuisance(rows))
    assert torch.equal(before, torch.random.get_rng_state())


@pytest.mark.parametrize("device", ["mps", "meta", "cpu:2", "invalid-device", 0, None])
def test_unsupported_devices_refuse_without_cuda_execution(device):
    with pytest.raises(FactorizedDeviceError):
        explicit_device(device)


def test_cuda_names_are_parsed_only_not_executed_or_qualified():
    assert explicit_device("cuda") == torch.device("cuda:0")
    assert explicit_device("cuda:3") == torch.device("cuda:3")


@pytest.mark.parametrize("change", [
    lambda b: replace(b, architecture_sha256="0"*64),
    lambda b: replace(b, owners=(False, 0, 0, 0)),
    lambda b: replace(b, coordinate_dimensions=(1, 1, 1, 1)),
    lambda b: replace(b, metadata_keys=(b"", *b.metadata_keys[1:])),
    lambda b: replace(b, context=b.context.double()),
    lambda b: replace(b, forward_time=torch.tensor([3.0, 0.0], device="cpu")),
])
def test_invalid_device_batch_rejected_before_byte_recurrence(change, monkeypatch):
    model = DeviceFactorizedEnergy.from_cpu(models()[0], "cpu")
    batch = device_configuration_batch(states(), (.2, .4), torch.zeros(2, 64, device="cpu"), model.architecture, device="cpu")
    def forbidden(_):
        raise AssertionError("byte graph must not run")
    monkeypatch.setattr(model.metadata_encoder, "forward", forbidden)
    with pytest.raises(FactorizedEnergyError):
        model(change(batch))


def test_cpu_batch_not_silently_accepted_and_device_batch_identity_explicit():
    source = models()[0]
    model = DeviceFactorizedEnergy.from_cpu(source, "cpu")
    cpu_batch = factorized_configuration_batch(states(), (.2, .4), torch.zeros(2, 64, device="cpu"), source.architecture)
    assert type(cpu_batch) is FactorizedConfigurationBatch
    with pytest.raises(FactorizedDeviceError, match="exact device"):
        model(cpu_batch)
    batch = device_configuration_batch(states(), (.2, .4), torch.zeros(2, 64, device="cpu"), model.architecture, device="cpu")
    assert type(batch) is DeviceFactorizedConfigurationBatch


def test_coordinate_and_visible_fp32_overflow_and_resource_excess_refuse():
    spec = architecture()
    big = ((FactoredEvent(X, 1e100),),)
    with pytest.raises(FactorizedDeviceError, match="nonfinite"):
        device_configuration_batch(big, (.2,), torch.zeros(1, 64, device="cpu"), spec, device="cpu")
    encoder = DeviceFactorizedObservationEncoder.from_cpu(models()[1], "cpu")
    with pytest.raises(FactorizedDeviceError, match="overflow"):
        encoder((FactorizedObservation(big[0], "R3-PHYS", "test", b"z"),))
    with pytest.raises(FactorizedDeviceError, match="state tuple"):
        device_configuration_batch((states()[0]+(A,),), (.2,), torch.zeros(1, 64, device="cpu"), spec, device="cpu")


def test_nonfinite_device_parameter_refused_and_source_unchanged():
    source = models()[0]
    model = DeviceFactorizedEnergy.from_cpu(source, "cpu")
    with torch.no_grad():
        next(model.parameters())[0, 0] = float("nan")
    batch = device_configuration_batch(states(), (.2, .4), torch.zeros(2, 64, device="cpu"), model.architecture, device="cpu")
    with pytest.raises(FactorizedDeviceError, match="nonfinite device parameters"):
        model(batch)
    assert all(bool(torch.isfinite(p).all()) for p in source.parameters())
