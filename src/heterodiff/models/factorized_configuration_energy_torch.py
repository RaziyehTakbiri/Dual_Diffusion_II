"""Additive metadata-aware energy prototype, not a frozen scientific model.

Exact caller-declared metadata bytes are consumed in full by a shared recurrent
encoder. They are never hashed, truncated, made continuous, or replaced by a
finite vocabulary. The learned finite-precision recurrent state is NOT an
injective representation. Only declared 1D fibers have a continuous coordinate;
0D atoms have an empty coordinate tensor. This CPU FP32 prototype supplies no
reference law, clinical schema, observation law, old certificate compatibility,
global derivative certificate, production qualification, or paid-job launcher.
"""
from dataclasses import dataclass
import hashlib
import json
import math

import torch
from torch import nn
from torch.nn import functional as F


DESIGN_ID = 'SHARED_FACTORISED_METADATA_ENERGY_PROTOTYPE_V1'
METADATA_WIDTH = 32
EVENT_INPUT_WIDTH = METADATA_WIDTH + 2
HIDDEN_WIDTH = 128
CONTEXT_WIDTH = 64
EXPECTED_PARAMETER_COUNT = 96_705


class FactorizedEnergyError(ValueError):
    """Invalid declaration, input, or unsupported runtime; no fallback."""


class FactorizedEnergyResourceError(FactorizedEnergyError):
    """Declared local processing limit exceeded; nothing is truncated."""


def _positive_int(value, name):
    if type(value) is not int or value <= 0:
        raise FactorizedEnergyError(name + ' must be an exact positive integer')


def _positive_float32(value, name):
    if type(value) is not float or not math.isfinite(value) or value <= 0:
        raise FactorizedEnergyError(name + ' must be an exact positive finite float')
    represented = torch.tensor(value, dtype=torch.float32, device='cpu')
    if not bool(torch.isfinite(represented)) or float(represented) != value:
        raise FactorizedEnergyError(name + ' must be exactly representable as positive FP32')


@dataclass(frozen=True)
class FactorizedEnergyLimits:
    """Explicit local resource refusals, not a truncated scientific support."""

    maximum_batch_size: int
    maximum_batch_events: int
    maximum_metadata_bytes_per_event: int
    maximum_total_metadata_bytes: int

    def __post_init__(self):
        for name, value in vars(self).items():
            _positive_int(value, name)


@dataclass(frozen=True)
class FactorizedEnergyArchitecture:
    metadata_schema_id: str
    total_cap: int
    horizon: float
    value_bound: float
    coordinate_scale: float
    context_scale: float
    limits: FactorizedEnergyLimits

    def __post_init__(self):
        if (type(self.metadata_schema_id) is not str or not self.metadata_schema_id
                or len(self.metadata_schema_id) > 256 or not self.metadata_schema_id.isascii()):
            raise FactorizedEnergyError('explicit bounded ASCII metadata schema ID required')
        _positive_int(self.total_cap, 'total_cap')
        for name in ('horizon', 'value_bound', 'coordinate_scale', 'context_scale'):
            _positive_float32(getattr(self, name), name)
        if type(self.limits) is not FactorizedEnergyLimits:
            raise FactorizedEnergyError('exact explicit FactorizedEnergyLimits required')
        self.limits.__post_init__()

    @property
    def architecture_sha256(self):
        self.__post_init__()
        record = {name: value.hex() if type(value) is float else value
                  for name, value in vars(self).items() if name != 'limits'}
        record.update(design_id=DESIGN_ID, limits=vars(self.limits),
                      metadata_width=32, event_input_width=34, hidden_width=128,
                      context_width=64, parameter_count=EXPECTED_PARAMETER_COUNT)
        return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':'),
                                         ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


@dataclass(frozen=True)
class FactorizedConfigurationBatch:
    architecture_sha256: str
    metadata_keys: tuple[bytes, ...]
    coordinate_dimensions: tuple[int, ...]
    coordinates: tuple[torch.Tensor, ...]
    owners: tuple[int, ...]
    forward_time: torch.Tensor
    context: torch.Tensor


def _tensor(value, name, shape):
    if (type(value) is not torch.Tensor or value.layout != torch.strided
            or value.dtype != torch.float32 or value.device.type != 'cpu'
            or tuple(value.shape) != shape or not bool(torch.isfinite(value).all())):
        raise FactorizedEnergyError(name + ' requires finite dense CPU FP32 with declared shape')


def _validate_batch(architecture, batch):
    if type(batch) is not FactorizedConfigurationBatch:
        raise FactorizedEnergyError('exact FactorizedConfigurationBatch required')
    if batch.architecture_sha256 != architecture.architecture_sha256:
        raise FactorizedEnergyError('architecture binding mismatch')
    limits = architecture.limits
    for name in ('metadata_keys', 'coordinate_dimensions', 'coordinates', 'owners'):
        if type(getattr(batch, name)) is not tuple:
            raise FactorizedEnergyError(name + ' must be an exact tuple')
    n = len(batch.metadata_keys)
    if n > limits.maximum_batch_events:
        raise FactorizedEnergyResourceError('maximum_batch_events exceeded; no truncation')
    if any(len(getattr(batch, name)) != n for name in ('coordinate_dimensions', 'coordinates', 'owners')):
        raise FactorizedEnergyError('event rows must be exactly aligned')
    if type(batch.forward_time) is not torch.Tensor or batch.forward_time.ndim != 1:
        raise FactorizedEnergyError('forward_time requires a batch vector')
    size = batch.forward_time.shape[0]
    if not 1 <= size <= limits.maximum_batch_size:
        raise FactorizedEnergyResourceError('maximum_batch_size exceeded or empty batch')
    _tensor(batch.forward_time, 'forward_time', (size,))
    _tensor(batch.context, 'context', (size, CONTEXT_WIDTH))
    if bool((batch.forward_time < 0).any()) or bool((batch.forward_time > architecture.horizon).any()):
        raise FactorizedEnergyError('forward_time outside declared closed horizon')
    total_bytes = 0
    counts = [0]*size
    key_dimensions = {}
    for key, dimension, coordinate, owner in zip(batch.metadata_keys, batch.coordinate_dimensions,
                                                 batch.coordinates, batch.owners):
        if type(key) is not bytes or not key:
            raise FactorizedEnergyError('metadata key must be nonempty exact bytes')
        if len(key) > limits.maximum_metadata_bytes_per_event:
            raise FactorizedEnergyResourceError('maximum_metadata_bytes_per_event exceeded; no truncation')
        total_bytes += len(key)
        if total_bytes > limits.maximum_total_metadata_bytes:
            raise FactorizedEnergyResourceError('maximum_total_metadata_bytes exceeded; no truncation')
        if type(dimension) is not int or dimension not in (0, 1):
            raise FactorizedEnergyError('exact declared coordinate dimension 0 or 1 required')
        if key in key_dimensions and key_dimensions[key] != dimension:
            raise FactorizedEnergyError('same metadata key has inconsistent fiber dimensions')
        key_dimensions[key] = dimension
        _tensor(coordinate, 'event coordinate', (dimension,))
        if type(owner) is not int or not 0 <= owner < size:
            raise FactorizedEnergyError('owner must be an exact in-range batch index')
        counts[owner] += 1
        if counts[owner] > architecture.total_cap:
            raise FactorizedEnergyResourceError('declared total_cap exceeded; no truncation')
    return size, tuple(counts), total_bytes


class _Linear(nn.Module):
    def __init__(self, inputs, outputs, generator):
        super().__init__()
        self.weight = nn.Parameter(torch.empty(outputs, inputs, dtype=torch.float32, device='cpu'))
        self.bias = nn.Parameter(torch.empty(outputs, dtype=torch.float32, device='cpu'))
        radius = 1/math.sqrt(inputs)
        nn.init.uniform_(self.weight, -radius, radius, generator=generator)
        nn.init.uniform_(self.bias, -radius, radius, generator=generator)

    def forward(self, values):
        return F.linear(values, self.weight, self.bias)


class _SharedByteEncoder(nn.Module):
    """Canonical bytes in, learned compression out; no injectivity theorem."""

    def __init__(self, generator):
        super().__init__()
        self.recurrent_weight = nn.Parameter(torch.empty(32, 32, dtype=torch.float32, device='cpu'))
        self.byte_weight = nn.Parameter(torch.empty(32, dtype=torch.float32, device='cpu'))
        self.bias = nn.Parameter(torch.empty(32, dtype=torch.float32, device='cpu'))
        for parameter in self.parameters():
            nn.init.uniform_(parameter, -1/math.sqrt(32), 1/math.sqrt(32), generator=generator)

    def forward(self, key):
        hidden = torch.zeros(32, dtype=torch.float32, device='cpu')
        for byte in key:
            # Integer bytes/256 are exact FP32 dyadics; no learned vocabulary.
            hidden = torch.tanh(F.linear(hidden, self.recurrent_weight)
                                + self.byte_weight*(byte/256.0) + self.bias)
        return hidden


def _bounded_coordinates(values, scale):
    return torch.atan2(values, torch.full_like(values, scale))*(2/math.pi)


class BoundedFactorizedConfigurationEnergy(nn.Module):
    """Countable-key-capable local graph; not an old certified energy type."""

    def __init__(self, architecture, *, initialization_seed):
        super().__init__()
        if type(architecture) is not FactorizedEnergyArchitecture:
            raise FactorizedEnergyError('exact FactorizedEnergyArchitecture required')
        architecture.__post_init__()
        if type(initialization_seed) is not int or not 0 <= initialization_seed < 2**64:
            raise FactorizedEnergyError('explicit uint64 initialization seed required')
        self.architecture = architecture
        generator = torch.Generator(device='cpu').manual_seed(initialization_seed)
        self.metadata_encoder = _SharedByteEncoder(generator)
        self.event_hidden = _Linear(34, 128, generator)
        self.event_output = _Linear(128, 128, generator)
        self.context_hidden = _Linear(65, 128, generator)
        self.context_output = _Linear(128, 128, generator)
        self.readout_hidden = _Linear(257, 128, generator)
        self.readout_middle = _Linear(128, 128, generator)
        self.readout_output = _Linear(128, 1, generator)
        if self.parameter_count != EXPECTED_PARAMETER_COUNT:
            raise FactorizedEnergyError('constructed parameter count differs')

    @property
    def parameter_count(self):
        return sum(parameter.numel() for parameter in self.parameters())

    def _validate_parameters(self):
        if self.parameter_count != EXPECTED_PARAMETER_COUNT:
            raise FactorizedEnergyError('parameter count changed')
        for parameter in self.parameters():
            if (parameter.device.type != 'cpu' or parameter.dtype != torch.float32
                    or parameter.layout != torch.strided or not bool(torch.isfinite(parameter).all())):
                raise FactorizedEnergyError('model parameters must remain finite CPU FP32')

    def workload(self, batch):
        size, counts, total_bytes = _validate_batch(self.architecture, batch)
        events = len(batch.metadata_keys)
        return {'scope': 'LOGICAL_GRAPH_COUNTS_NOT_F104_WEIGHTS_OR_GPU_TIME',
                'configurations': size, 'events': events, 'cardinalities': counts,
                'metadata_bytes_consumed': total_bytes,
                'metadata_recurrence_steps': total_bytes,
                'metadata_recurrence_matrix_macs': total_bytes*32*32,
                'metadata_byte_scalar_multiplications': total_bytes*32,
                'event_affine_macs': events*(34*128+128*128),
                'context_affine_macs': size*(65*128+128*128),
                'readout_affine_macs': size*(257*128+128*128+128),
                'coordinate_dimensions_total': sum(batch.coordinate_dimensions),
                'bias_activation_sorting_pooling_and_autograd_work_included': False,
                'production_budget_adopted': False}

    def forward(self, batch):
        size, counts, _ = _validate_batch(self.architecture, batch)
        self._validate_parameters()
        groups = [[] for _ in range(size)]
        # Canonical evaluation order gives permutation-bitwise repeatability on
        # this CPU graph, without claiming an exact-sum or cross-runtime proof.
        order = sorted(range(len(batch.metadata_keys)), key=lambda i: (
            batch.owners[i], batch.metadata_keys[i], batch.coordinate_dimensions[i],
            tuple(float(value).hex() for value in batch.coordinates[i].detach().tolist())))
        for i in order:
            metadata = self.metadata_encoder(batch.metadata_keys[i])
            coordinate = batch.coordinates[i]
            active = batch.coordinate_dimensions[i]
            scalar = (_bounded_coordinates(coordinate, self.architecture.coordinate_scale)
                      if active else torch.zeros(1, dtype=torch.float32, device='cpu'))
            values = torch.cat((metadata, torch.tensor([float(active)], dtype=torch.float32, device='cpu'), scalar))
            embedded = torch.tanh(self.event_output(torch.tanh(self.event_hidden(values))))
            groups[batch.owners[i]].append(embedded)
        pooled = torch.stack([torch.stack(group).sum(0) if group else torch.zeros(128, dtype=torch.float32, device='cpu')
                              for group in groups])
        time = 2.0*(batch.forward_time/self.architecture.horizon)-1.0
        context = _bounded_coordinates(batch.context, self.architecture.context_scale)
        context = torch.tanh(self.context_output(torch.tanh(
            self.context_hidden(torch.cat((time[:, None], context), 1)))))
        count = torch.tensor([n/self.architecture.total_cap for n in counts], dtype=torch.float32, device='cpu')
        value = torch.cat((pooled, context, count[:, None]), 1)
        value = torch.tanh(self.readout_hidden(value))
        value = torch.tanh(self.readout_middle(value))
        raw = self.readout_output(value).squeeze(1)
        if not bool(torch.isfinite(raw).all()):
            raise FactorizedEnergyError('nonfinite raw energy; no fallback')
        result = self.architecture.value_bound*torch.tanh(raw/self.architecture.value_bound)
        if not bool(torch.isfinite(result).all()) or bool((result.abs() > self.architecture.value_bound).any()):
            raise FactorizedEnergyError('bounded energy check failed')
        return result

    def description(self):
        return {'design_id': DESIGN_ID, 'architecture_sha256': self.architecture.architecture_sha256,
                'metadata_schema_id': self.architecture.metadata_schema_id,
                'parameter_count': self.parameter_count, 'metadata_encoder_parameters': 1088,
                'internal_context_parameters_already_included': 24960,
                'type_roster_or_per_type_heads_used': False,
                'exact_input_bytes_preserved': True, 'learned_features_injective_claimed': False,
                'metadata_coordinate_diffusion_used': False,
                'old_certified_energy_interface_accepted': False,
                'global_derivative_certificate_claimed': False,
                'production_domain_schema_or_rates_adopted': False,
                'gpu_qualification_claimed': False,
                'scope': 'ADDITIVE_LOCAL_SCIENTIFIC_AMENDMENT_PROTOTYPE_ONLY'}


__all__ = ['FactorizedEnergyError', 'FactorizedEnergyResourceError',
           'FactorizedEnergyLimits', 'FactorizedEnergyArchitecture',
           'FactorizedConfigurationBatch', 'BoundedFactorizedConfigurationEnergy']
