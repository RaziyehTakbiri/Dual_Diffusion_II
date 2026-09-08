"""Explicit-device copies of the factorized CPU neural graphs.

CPU/CUDA FP32 implementation, not CUDA execution or numerical qualification.
Source models are never moved or mutated. Exact metadata stays on the host;
full-byte recurrence and learned tensors run on the selected explicit device.
No new vocabulary, scientific architecture, or old certificate is introduced.
"""
from copy import deepcopy
from dataclasses import dataclass
import math

import torch
from torch import nn
from torch.nn import functional as F

from heterodiff.data.two_domain_factorized_state import FactoredEvent
from heterodiff.models.factorized_configuration_energy_torch import (
    BoundedFactorizedConfigurationEnergy, FactorizedEnergyArchitecture,
    FactorizedEnergyError, FactorizedEnergyResourceError, EXPECTED_PARAMETER_COUNT,
)
from heterodiff.experiments.factorized_conditional_training import (
    FactorizedObservationEncoder, FactorizedObservationNuisance,
    _observation_roster, _finite_parameters,
)


class FactorizedDeviceError(FactorizedEnergyError):
    pass


def _need(condition, message):
    if not condition:
        raise FactorizedDeviceError(message)


def explicit_device(value):
    _need(type(value) in (str, torch.device), "explicit CPU or CUDA device required")
    try:
        result = torch.device(value)
    except (RuntimeError, ValueError) as error:
        raise FactorizedDeviceError("invalid explicit device") from error
    _need(result.type in ("cpu", "cuda"), "only CPU/CUDA devices are supported")
    if result.type == "cpu":
        _need(result.index in (None, 0), "CPU index must be absent or zero")
        return torch.device("cpu")
    return torch.device("cuda", 0 if result.index is None else result.index)


def _shape(value, shape, device, name):
    _need(type(value) is torch.Tensor and value.layout == torch.strided
          and value.dtype == torch.float32 and value.device == device
          and tuple(value.shape) == shape, name + " requires aligned dense device FP32")


def _finite_all(values, message):
    # A single host scalar read, never one host read for every metadata byte.
    values = tuple(values)
    if values:
        _need(bool(torch.stack([torch.isfinite(v).all() for v in values]).all()), message)


def _parameters(module):
    values = tuple(module.parameters())
    for p in values:
        _need(p.device == module.device and p.dtype == torch.float32 and p.layout == torch.strided,
              "parameters must remain dense FP32 on the declared device")
    _finite_all(values, "nonfinite device parameters")


def _copy_parameter(source, device):
    return nn.Parameter(source.detach().to(device=device, dtype=torch.float32).clone(),
                        requires_grad=source.requires_grad)


def _copy_modes(source, destination):
    original, copied = dict(source.named_modules()), dict(destination.named_modules())
    _need(original.keys() == copied.keys(), "device module-name roster mismatch")
    for name, module in original.items():
        copied[name].training = module.training


class _DeviceLinear(nn.Module):
    def __init__(self, source, device):
        super().__init__()
        self.weight = _copy_parameter(source.weight, device)
        self.bias = _copy_parameter(source.bias, device)

    def forward(self, value):
        return F.linear(value, self.weight, self.bias)


class _DeviceByteEncoder(nn.Module):
    def __init__(self, source, device):
        super().__init__()
        self.device = device
        self.recurrent_weight = _copy_parameter(source.recurrent_weight, device)
        self.byte_weight = _copy_parameter(source.byte_weight, device)
        self.bias = _copy_parameter(source.bias, device)

    def forward(self, key):
        hidden = torch.zeros(32, dtype=torch.float32, device=self.device)
        for byte in key:
            hidden = torch.tanh(F.linear(hidden, self.recurrent_weight)
                                + self.byte_weight * (byte / 256.0) + self.bias)
        return hidden


def _bounded(value, scale):
    return torch.atan2(value, torch.full_like(value, scale, device=value.device)) * (2 / math.pi)


@dataclass(frozen=True)
class DeviceFactorizedConfigurationBatch:
    architecture_sha256: str
    metadata_keys: tuple[bytes, ...]
    coordinate_dimensions: tuple[int, ...]
    coordinates: tuple[torch.Tensor, ...]
    owners: tuple[int, ...]
    forward_time: torch.Tensor
    context: torch.Tensor


def _batch_structure(architecture, keys, dimensions, owners, size):
    limits = architecture.limits
    _need(type(size) is int and 1 <= size <= limits.maximum_batch_size, "bounded nonempty batch required")
    _need(type(keys) is tuple and type(dimensions) is tuple and type(owners) is tuple,
          "exact event roster tuples required")
    _need(len(keys) == len(dimensions) == len(owners), "unaligned event roster")
    if len(keys) > limits.maximum_batch_events:
        raise FactorizedEnergyResourceError("maximum_batch_events exceeded; no truncation")
    counts, key_dimensions, total = [0] * size, {}, 0
    for key, dimension, owner in zip(keys, dimensions, owners):
        _need(type(key) is bytes and bool(key), "nonempty exact metadata bytes required")
        if len(key) > limits.maximum_metadata_bytes_per_event:
            raise FactorizedEnergyResourceError("maximum_metadata_bytes_per_event exceeded; no truncation")
        total += len(key)
        if total > limits.maximum_total_metadata_bytes:
            raise FactorizedEnergyResourceError("maximum_total_metadata_bytes exceeded; no truncation")
        _need(type(dimension) is int and dimension in (0, 1), "exact 0/1 fiber dimension required")
        _need(key not in key_dimensions or key_dimensions[key] == dimension, "inconsistent metadata fiber dimension")
        key_dimensions[key] = dimension
        _need(type(owner) is int and 0 <= owner < size, "exact in-range occurrence owner required")
        counts[owner] += 1
        if counts[owner] > architecture.total_cap:
            raise FactorizedEnergyResourceError("declared total_cap exceeded; no truncation")
    return tuple(counts), total


def _validate_batch(architecture, batch, device):
    _need(type(batch) is DeviceFactorizedConfigurationBatch, "exact device configuration batch required")
    _need(batch.architecture_sha256 == architecture.architecture_sha256, "architecture binding mismatch")
    _need(type(batch.forward_time) is torch.Tensor and batch.forward_time.ndim == 1,
          "forward_time requires a vector")
    size = batch.forward_time.shape[0]
    counts, total = _batch_structure(architecture, batch.metadata_keys, batch.coordinate_dimensions,
                                    batch.owners, size)
    _need(type(batch.coordinates) is tuple and len(batch.coordinates) == len(batch.metadata_keys),
          "aligned coordinate tuple required")
    _shape(batch.forward_time, (size,), device, "forward_time")
    _shape(batch.context, (size, 64), device, "context")
    for dimension, coordinate in zip(batch.coordinate_dimensions, batch.coordinates):
        _shape(coordinate, (dimension,), device, "fiber coordinate")
    _finite_all((batch.forward_time, batch.context, *batch.coordinates), "nonfinite device batch; no clipping")
    _need(not bool(((batch.forward_time < 0) | (batch.forward_time > architecture.horizon)).any()),
          "forward_time outside declared horizon")
    return size, counts, total


def device_configuration_batch(states, reverse_times, contexts, architecture, *, device,
                               coordinates=None, coordinate_gradients=False):
    """Build device FP32 rows; transfers retain coordinate/context autograd.

New coordinate rows are target-device FP32 leaves. Supplied CPU/target FP32
or FP64 rows are converted without detachment. Metadata is never tensorized
into categories. Resource structure is checked before device allocation.
"""
    target = explicit_device(device)
    _need(type(architecture) is FactorizedEnergyArchitecture, "exact architecture required")
    architecture.__post_init__()
    _need(type(coordinate_gradients) is bool, "exact coordinate-gradient flag required")
    _need(type(states) is tuple and 1 <= len(states) <= architecture.limits.maximum_batch_size,
          "bounded nonempty state roster required")
    _need(type(reverse_times) is tuple and len(reverse_times) == len(states)
          and all(type(u) is float and math.isfinite(u) and 0 <= u <= architecture.horizon for u in reverse_times),
          "aligned closed-horizon reverse times required")
    count = 0
    for state in states:
        _need(type(state) is tuple and len(state) <= architecture.total_cap, "exact capped state tuple required")
        count += len(state)
        _need(count <= architecture.limits.maximum_batch_events, "state event resource limit exceeded")
        _need(all(type(event) is FactoredEvent for event in state), "exact factored events required")
        _need(len({event.key.domain_id for event in state}) <= 1, "mixed state domains forbidden")
    flat = tuple(event for state in states for event in state)
    keys = tuple(event.key.canonical_bytes() for event in flat)
    dimensions = tuple(event.key.dimension for event in flat)
    owners = tuple(i for i, state in enumerate(states) for _ in state)
    _batch_structure(architecture, keys, dimensions, owners, len(states))
    _need(type(contexts) is torch.Tensor and contexts.layout == torch.strided
          and contexts.dtype in (torch.float32, torch.float64)
          and contexts.device in (torch.device("cpu"), target)
          and tuple(contexts.shape) == (len(states), 64), "aligned CPU/target floating contexts required")
    if coordinates is None:
        converted = tuple(torch.tensor([] if not event.key.dimension else [event.coordinate],
                                       dtype=torch.float32, device=target,
                                       requires_grad=coordinate_gradients) for event in flat)
    else:
        _need(type(coordinates) is tuple and len(coordinates) == len(flat), "aligned coordinate inputs required")
        for dimension, value in zip(dimensions, coordinates):
            _need(type(value) is torch.Tensor and value.layout == torch.strided
                  and value.dtype in (torch.float32, torch.float64)
                  and value.device in (torch.device("cpu"), target)
                  and tuple(value.shape) == (dimension,), "CPU/target FP32/FP64 fiber tensor required")
        converted = tuple(value.to(device=target, dtype=torch.float32) for value in coordinates)
    batch = DeviceFactorizedConfigurationBatch(
        architecture.architecture_sha256, keys, dimensions, converted, owners,
        torch.tensor([architecture.horizon - u for u in reverse_times], dtype=torch.float32, device=target),
        contexts.to(device=target, dtype=torch.float32))
    _validate_batch(architecture, batch, target)
    return batch


class DeviceFactorizedEnergy(nn.Module):
    @classmethod
    def from_cpu(cls, cpu_model, device):
        _need(type(cpu_model) is BoundedFactorizedConfigurationEnergy, "exact CPU energy required")
        cpu_model._validate_parameters()
        target = explicit_device(device)
        result = cls()
        result.device, result.architecture = target, deepcopy(cpu_model.architecture)
        result.metadata_encoder = _DeviceByteEncoder(cpu_model.metadata_encoder, target)
        for name in ("event_hidden", "event_output", "context_hidden", "context_output",
                     "readout_hidden", "readout_middle", "readout_output"):
            setattr(result, name, _DeviceLinear(getattr(cpu_model, name), target))
        _copy_modes(cpu_model, result)
        _need(result.parameter_count == EXPECTED_PARAMETER_COUNT, "device parameter count mismatch")
        return result

    @property
    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())

    def workload(self, batch):
        size, counts, total = _validate_batch(self.architecture, batch, self.device)
        events = len(batch.metadata_keys)
        return {"scope": "LOGICAL_DEVICE_GRAPH_NOT_GPU_TIME_OR_F104_COST",
                "configurations": size, "events": events, "cardinalities": counts,
                "metadata_bytes_consumed": total, "metadata_recurrence_steps": total,
                "metadata_recurrence_matrix_macs": total * 1024,
                "metadata_byte_scalar_multiplications": total * 32,
                "event_affine_macs": events * (34 * 128 + 128 * 128),
                "context_affine_macs": size * (65 * 128 + 128 * 128),
                "readout_affine_macs": size * (257 * 128 + 128 * 128 + 128),
                "coordinate_dimensions_total": sum(batch.coordinate_dimensions),
                "device": str(self.device), "cuda_qualification_claimed": False}

    def forward(self, batch):
        size, counts, _ = _validate_batch(self.architecture, batch, self.device)
        _need(self.parameter_count == EXPECTED_PARAMETER_COUNT, "device parameter count changed")
        _parameters(self)
        # One bulk coordinate transfer for canonical ordering, no per-event or
        # per-byte device scalar reads. Sorting is intentionally nondifferentiable.
        scalar_values = (torch.cat([v.detach() for v in batch.coordinates]).to(device="cpu").tolist()
                         if any(batch.coordinate_dimensions) else [])
        position, coordinate_keys = 0, []
        for dimension in batch.coordinate_dimensions:
            coordinate_keys.append((float(scalar_values[position]).hex(),) if dimension else ())
            position += dimension
        order = sorted(range(len(batch.metadata_keys)), key=lambda i: (
            batch.owners[i], batch.metadata_keys[i], batch.coordinate_dimensions[i], coordinate_keys[i]))
        groups = [[] for _ in range(size)]
        for i in order:
            metadata = self.metadata_encoder(batch.metadata_keys[i])
            active, coordinate = batch.coordinate_dimensions[i], batch.coordinates[i]
            scalar = (_bounded(coordinate, self.architecture.coordinate_scale) if active
                      else torch.zeros(1, dtype=torch.float32, device=self.device))
            values = torch.cat((metadata, torch.tensor([float(active)], dtype=torch.float32, device=self.device), scalar))
            embedded = torch.tanh(self.event_output(torch.tanh(self.event_hidden(values))))
            groups[batch.owners[i]].append(embedded)
        pooled = torch.stack([torch.stack(group).sum(0) if group
                              else torch.zeros(128, dtype=torch.float32, device=self.device) for group in groups])
        time = 2.0 * (batch.forward_time / self.architecture.horizon) - 1.0
        context = _bounded(batch.context, self.architecture.context_scale)
        context = torch.tanh(self.context_output(torch.tanh(
            self.context_hidden(torch.cat((time[:, None], context), 1)))))
        count = torch.tensor([n / self.architecture.total_cap for n in counts], dtype=torch.float32, device=self.device)
        value = torch.cat((pooled, context, count[:, None]), 1)
        value = torch.tanh(self.readout_hidden(value))
        value = torch.tanh(self.readout_middle(value))
        raw = self.readout_output(value).squeeze(1)
        _finite_all((raw,), "nonfinite device raw energy")
        result = self.architecture.value_bound * torch.tanh(raw / self.architecture.value_bound)
        _finite_all((result,), "nonfinite bounded device energy")
        _need(not bool((result.abs() > self.architecture.value_bound).any()), "device energy bound violated")
        return result


class DeviceFactorizedObservationEncoder(nn.Module):
    @classmethod
    def from_cpu(cls, cpu_encoder, device):
        _need(type(cpu_encoder) is FactorizedObservationEncoder, "exact CPU observation encoder required")
        _finite_parameters(cpu_encoder)
        result, target = cls(), explicit_device(device)
        result.device = target
        for name in ("limits", "observation_cap", "coordinate_scale"):
            setattr(result, name, deepcopy(getattr(cpu_encoder, name)))
        result.bytes = _DeviceByteEncoder(cpu_encoder.bytes, target)
        for name in ("event_hidden", "event_output", "readout_hidden", "readout_output"):
            setattr(result, name, _DeviceLinear(getattr(cpu_encoder, name), target))
        _copy_modes(cpu_encoder, result)
        return result

    @property
    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())

    def forward(self, observations):
        _observation_roster(observations, self.limits, self.observation_cap)
        _parameters(self)
        # The source observations are host records; perform one batched finite
        # representability check before launching any recurrent device work.
        host_coordinates = torch.tensor([event.coordinate for row in observations
            for event in (() if row.observed is None else row.observed) if event.key.dimension],
            dtype=torch.float32, device="cpu")
        _finite_all((host_coordinates,), "visible coordinate FP32 overflow; no clipping")
        results = []
        for row in observations:
            retained = () if row.observed is None else row.observed
            embeddings = []
            for event in sorted(retained, key=lambda e: e.sort_key):
                active = event.key.dimension
                raw = torch.tensor([event.coordinate if active else 0.0], dtype=torch.float32, device=self.device)
                features = torch.cat((self.bytes(event.key.canonical_bytes()),
                    torch.tensor([float(active)], dtype=torch.float32, device=self.device),
                    _bounded(raw, self.coordinate_scale)))
                embeddings.append(torch.tanh(self.event_output(torch.tanh(self.event_hidden(features)))))
            pooled = (torch.stack(embeddings).sum(0) / (1 + len(retained)) if embeddings
                      else torch.zeros(128, dtype=torch.float32, device=self.device))
            flags = torch.tensor([float(row.observed is None), len(retained) / max(1, self.observation_cap)],
                                 dtype=torch.float32, device=self.device)
            merged = torch.cat((pooled, self.bytes(row.canonical_context_bytes), flags))
            results.append(torch.tanh(self.readout_output(torch.tanh(self.readout_hidden(merged)))))
        result = torch.stack(results)
        _finite_all((result,), "nonfinite device observation encoding")
        return result


class DeviceFactorizedObservationNuisance(nn.Module):
    @classmethod
    def from_cpu(cls, cpu_nuisance, device):
        _need(type(cpu_nuisance) is FactorizedObservationNuisance, "exact CPU nuisance required")
        _finite_parameters(cpu_nuisance)
        result, target = cls(), explicit_device(device)
        result.device = target
        result.encoder = DeviceFactorizedObservationEncoder.from_cpu(cpu_nuisance.encoder, target)
        result.hidden = _DeviceLinear(cpu_nuisance.hidden, target)
        result.output = _DeviceLinear(cpu_nuisance.output, target)
        _copy_modes(cpu_nuisance, result)
        return result

    @property
    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())

    def forward(self, observations):
        _parameters(self)
        result = self.output(torch.tanh(self.hidden(self.encoder(observations)))).squeeze(1)
        _finite_all((result,), "nonfinite device nuisance")
        return result


__all__ = ["FactorizedDeviceError", "explicit_device", "DeviceFactorizedConfigurationBatch",
           "device_configuration_batch", "DeviceFactorizedEnergy",
           "DeviceFactorizedObservationEncoder", "DeviceFactorizedObservationNuisance"]
