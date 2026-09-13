"""Opt-in BASE graph precision candidate, not a GPU qualification claim.

The mathematical energy and relative-score/jump-flux objective are unchanged.
Inputs retain the established FP32 encoding. One FP64 view per FP32 parameter
is shared across both energy evaluations and every derivative branch, so branch
contributions accumulate before ONE cast back to the trainable FP32 leaf.
AdamW parameters, moments, epsilon and all parity tolerances are unchanged.
The legacy FP32 route remains the default and an explicit diagnostic control.
"""
from dataclasses import replace
import math

import torch
from torch.nn import functional as F

from heterodiff.experiments.factorized_base_training import BaseObjective
from heterodiff.models.factorized_device_energy_torch import (
    DeviceFactorizedEnergy, _finite_all, _parameters, _validate_batch,
)
from heterodiff.models.factorized_configuration_energy_torch import EXPECTED_PARAMETER_COUNT


PRECISION_POLICY = 'BASE_GRAPH_FP64_SHARED_V1'


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _promote_batch(batch, dtype):
    return replace(batch, coordinates=tuple(x.to(dtype=dtype) for x in batch.coordinates),
                   forward_time=batch.forward_time.to(dtype=dtype),
                   context=batch.context.to(dtype=dtype))


def _functional_energy(architecture, batch, parameters, *, rowwise=False):
    """Same energy algebra; rowwise affine evaluation is a CPU stress control.

    Internal function: callers validate metadata/resources and supply one shared
    parameter map. No casts are made here, particularly not inside recurrence.
    """
    dtype, device = batch.forward_time.dtype, batch.forward_time.device
    def zeros(n):
        return torch.zeros(n, dtype=dtype, device=device)
    def linear(name, x):
        weight, bias = parameters[name + '.weight'], parameters[name + '.bias']
        if rowwise and x.ndim == 2:
            return torch.stack([F.linear(row, weight, bias) for row in x])
        return F.linear(x, weight, bias)
    def bounded(x, scale):
        return torch.atan2(x, torch.full_like(x, scale)) * (2 / math.pi)
    def metadata(key):
        h = zeros(32)
        for byte in key:
            h = torch.tanh(F.linear(h, parameters['metadata_encoder.recurrent_weight'])
                + parameters['metadata_encoder.byte_weight'] * (byte / 256.0)
                + parameters['metadata_encoder.bias'])
        return h
    size = len(batch.forward_time)
    # The input has already been FP32 encoded; canonical ordering is unchanged.
    scalar_values = (torch.cat([x.detach() for x in batch.coordinates]).cpu().tolist()
                     if any(batch.coordinate_dimensions) else [])
    position, coordinate_keys = 0, []
    for dimension in batch.coordinate_dimensions:
        coordinate_keys.append((float(scalar_values[position]).hex(),) if dimension else ())
        position += dimension
    order = sorted(range(len(batch.metadata_keys)), key=lambda i: (
        batch.owners[i], batch.metadata_keys[i], batch.coordinate_dimensions[i], coordinate_keys[i]))
    groups = [[] for _ in range(size)]
    for i in order:
        active, coordinate = batch.coordinate_dimensions[i], batch.coordinates[i]
        scalar = bounded(coordinate, architecture.coordinate_scale) if active else zeros(1)
        x = torch.cat((metadata(batch.metadata_keys[i]),
                       torch.tensor([float(active)], dtype=dtype, device=device), scalar))
        groups[batch.owners[i]].append(torch.tanh(linear('event_output',
            torch.tanh(linear('event_hidden', x)))))
    pooled = torch.stack([torch.stack(group).sum(0) if group else zeros(128) for group in groups])
    t = 2.0 * (batch.forward_time / architecture.horizon) - 1.0
    z = bounded(batch.context, architecture.context_scale)
    z = torch.tanh(linear('context_output', torch.tanh(linear('context_hidden',
                                                           torch.cat((t[:, None], z), 1)))))
    counts = torch.tensor([len(group) / architecture.total_cap for group in groups],
                          dtype=dtype, device=device)
    x = torch.cat((pooled, z, counts[:, None]), 1)
    x = torch.tanh(linear('readout_hidden', x))
    x = torch.tanh(linear('readout_middle', x))
    raw = linear('readout_output', x).squeeze(1)
    result = architecture.value_bound * torch.tanh(raw / architecture.value_bound)
    _finite_all((raw, result), 'nonfinite precision-candidate energy; no clipping')
    _need(not bool((result.abs() > architecture.value_bound).any()), 'energy bound violated')
    return result


def _objective_from_values(values, dest_values, source, continuous_rates, jump_rates, jump_weight):
    """Unchanged objective, including +delta (not -delta) and exact Hessian."""
    cpu64 = lambda x: x.to(device='cpu', dtype=torch.float64)
    total = values.sum()
    terms = [cpu64(v) * 0 for v in values]
    for dimension, coordinate, owner in zip(source.coordinate_dimensions, source.coordinates, source.owners):
        if not dimension:
            continue
        g = torch.autograd.grad(total, coordinate, create_graph=True, retain_graph=True, allow_unused=True)[0]
        if g is None:
            continue
        h = (torch.autograd.grad(g.sum(), coordinate, create_graph=True, retain_graph=True,
                                allow_unused=True)[0] if g.requires_grad else None)
        g = cpu64(g)
        trace = g.sum() * 0 if h is None else cpu64(h).sum()
        terms[owner] = terms[owner] + .5 * g.square().sum() + trace - (cpu64(coordinate.detach()) * g).sum()
    continuous = (torch.stack(terms) * torch.tensor(continuous_rates, dtype=torch.float64, device='cpu')).mean()
    delta = cpu64(dest_values) - cpu64(values)
    jump = (torch.tensor(jump_rates, dtype=torch.float64, device='cpu') * (torch.exp(delta) + delta)).mean()
    objective = continuous + jump_weight * jump
    _finite_all((objective,), 'nonfinite precision-candidate objective; no clipping')
    return BaseObjective(objective, continuous, jump, source)


def _precision_objective(model, source, destination, continuous_rates, jump_rates, jump_weight,
                         *, dtype=torch.float64, rowwise=False, shared_parameters=True):
    """Internal diagnostic seam: FP32 and separate-cast modes are controls only."""
    _need(type(model) is DeviceFactorizedEnergy, 'exact device BASE model required')
    _need(model.parameter_count == EXPECTED_PARAMETER_COUNT, 'device parameter count changed')
    _need(dtype in (torch.float32, torch.float64), 'FP32/FP64 only')
    _need(type(rowwise) is bool and type(shared_parameters) is bool, 'exact diagnostic flags required')
    _parameters(model)
    size, _, _ = _validate_batch(model.architecture, source, model.device)
    dest_size, _, _ = _validate_batch(model.architecture, destination, model.device)
    _need(size == dest_size, 'aligned source/destination batches required')
    _need(type(continuous_rates) is tuple and type(jump_rates) is tuple
          and len(continuous_rates) == len(jump_rates) == size
          and all(type(r) is float and math.isfinite(r) and r >= 0 for r in continuous_rates + jump_rates),
          'aligned finite nonnegative rates required')
    _need(type(jump_weight) is float and math.isfinite(jump_weight) and jump_weight > 0,
          'positive jump weight required')
    _need(all(not d or x.requires_grad for d, x in zip(source.coordinate_dimensions, source.coordinates)),
          'differentiable continuous source coordinates required')
    source, destination = _promote_batch(source, dtype), _promote_batch(destination, dtype)
    # CRITICAL: never move this cast into _functional_energy or individual layers.
    # That would cast each branch gradient to FP32 before the cancellation.
    promoted = {name: p.to(dtype=dtype) for name, p in model.named_parameters()}
    other = (promoted if shared_parameters else
             {name: p.to(dtype=dtype) for name, p in model.named_parameters()})
    values = _functional_energy(model.architecture, source, promoted, rowwise=rowwise)
    dest_values = _functional_energy(model.architecture, destination, other, rowwise=rowwise)
    return _objective_from_values(values, dest_values, source, continuous_rates, jump_rates, jump_weight)


def precision_stable_base_objective(model, source, destination, continuous_rates, jump_rates, jump_weight):
    """Candidate: FP64 graph/derivatives/shared accumulation, FP32 leaf gradients.

    This is opt-in numerical implementation work, not a new scientific loss,
    a replacement of the legacy CPU comparator, or a qualified CUDA release.
    """
    return _precision_objective(model, source, destination, continuous_rates, jump_rates, jump_weight)


def precision_stable_base_energy(model, batch):
    """Evaluate the same BASE energy using the validated opt-in FP64 graph.

    The caller supplies the original FP32-encoded device batch. Promotion is
    differentiable: CPU64 physical coordinates passed through the existing
    FP32 device encoding retain their graph, including the return gradient.
    Parameters remain FP32 leaves (or frozen FP32 snapshot parameters); no
    model, input, optimizer, or global precision policy is mutated.
    """
    _need(type(model) is DeviceFactorizedEnergy, 'exact device BASE model required')
    _need(model.parameter_count == EXPECTED_PARAMETER_COUNT, 'device parameter count changed')
    _parameters(model)
    _validate_batch(model.architecture, batch, model.device)
    promoted_batch = _promote_batch(batch, torch.float64)
    promoted_parameters = {name: p.to(dtype=torch.float64) for name, p in model.named_parameters()}
    return _functional_energy(model.architecture, promoted_batch, promoted_parameters)
