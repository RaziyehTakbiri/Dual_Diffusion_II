"""Nonconfirmatory FP32 execution view of the typed DeepSets energy graph.

This additive training implementation does NOT replace the certified CPU64
``BoundedConfigurationEnergy``. Parameters, buffers, and architecture are copied
from that reference; the source model is never converted or trained in place.
Segment reductions use device-local FP32 ``torch.sum``, not sorted ``math.fsum``.
Thus graph/parameter correspondence is claimed, not binary64 numerical identity,
permutation-bitwise invariance, an analytic certificate, or GPU qualification.

This module supplies no diffusion objective, corruption process, context encoder,
data admission, sampler, checkpoint certification, or paid-job launcher.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

import torch
from torch import nn

from . import configuration_energy_torch as reference


TRAINING_VIEW_SCHEMA = "configuration-energy-fp32-training-view-v1"


@dataclass(frozen=True)
class TrainingConfigurationBatch:
    """Uncertified ragged inputs; type order is the architecture's type order."""

    architecture_sha256: str
    forward_time: torch.Tensor
    context: torch.Tensor
    coordinates: tuple[torch.Tensor, ...]
    batch_indices: tuple[torch.Tensor, ...]


def _explicit_device(value: str) -> torch.device:
    if value == "cpu":
        return torch.device("cpu")
    if not isinstance(value, str) or not value.startswith("cuda:"):
        raise ValueError("device must be cpu or an explicit cuda:N; no fallback")
    suffix = value[5:]
    if not suffix.isdecimal() or str(int(suffix)) != suffix:
        raise ValueError("CUDA device ordinal must be a canonical nonnegative integer")
    ordinal = int(suffix)
    if not torch.cuda.is_available() or ordinal >= torch.cuda.device_count():
        raise ValueError("requested CUDA device is unavailable; no CPU fallback")
    return torch.device(value)


class ConfigurationEnergyTrainingView(nn.Module):
    """Separate, uncertified FP32 trainable copy, with the original parameter names."""

    def __init__(self, cpu_reference: reference.BoundedConfigurationEnergy, *, device: str):
        super().__init__()
        if type(cpu_reference) is not reference.BoundedConfigurationEnergy:
            raise TypeError("an exact CPU BoundedConfigurationEnergy reference is required")
        cpu_reference._validate_state()
        target = _explicit_device(device)
        self.architecture = cpu_reference.architecture
        self.event_encoders = copy.deepcopy(cpu_reference.event_encoders).to(
            device=target, dtype=torch.float32
        )
        self.context_encoder = copy.deepcopy(cpu_reference.context_encoder).to(
            device=target, dtype=torch.float32
        )
        self.readout = copy.deepcopy(cpu_reference.readout).to(device=target, dtype=torch.float32)
        self._validate_state()

    @classmethod
    def from_cpu_reference(cls, cpu_reference, *, device="cpu"):
        return cls(cpu_reference, device=device)

    @property
    def parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    @property
    def execution_device(self) -> torch.device:
        # nn.Module.to() is also used by the explicit-device qualification
        # runner. Derive placement rather than retaining a stale CPU label.
        return self.readout.linear1.weight.device

    def execution_description(self) -> dict:
        return {
            "schema_version": TRAINING_VIEW_SCHEMA,
            "architecture_sha256": self.architecture.architecture_sha256,
            "device": str(self.execution_device),
            "parameter_dtype": "torch.float32",
            "parameter_count": self.parameter_count,
            "pooling": "DEVICE_FP32_PER_SEGMENT_TORCH_SUM",
            "cpu_reference_pooling": "SORTED_CPYTHON_MATH_FSUM_BINARY64",
            "coordinate_transform": "REFERENCE_STABLE_ATAN2_SCALE",
            "certified_cpu_checkpoint": False,
            "cross_device_bitwise_equivalence_claimed": False,
            "gpu_execution_qualified": False,
            "scientific_training_ready": False,
        }

    def _float_tensor(self, tensor: torch.Tensor, name: str, *, finite: bool = True) -> None:
        if not isinstance(tensor, torch.Tensor):
            raise TypeError(f"{name} must be a tensor")
        if tensor.dtype != torch.float32 or tensor.device != self.execution_device:
            raise ValueError(f"{name} must be FP32 on the explicit execution device")
        if tensor.layout != torch.strided or (finite and not bool(torch.isfinite(tensor).all())):
            raise ValueError(f"{name} must be a finite dense tensor")

    def _validate_state(self) -> None:
        reference._validate_architecture(self.architecture)
        if self.execution_device.type not in ("cpu", "cuda"):
            raise ValueError("training view supports only CPU or explicit CUDA placement")
        if self.parameter_count != self.architecture.expected_parameter_count:
            raise ValueError("training view parameter count differs from the reference graph")
        for name, tensor in self.state_dict().items():
            self._float_tensor(tensor, f"state {name}")
        scale_pairs = [
            (encoder.coordinate_scales, scales)
            for encoder, scales in zip(self.event_encoders, self.architecture.coordinate_scales)
        ] + [(self.context_encoder.context_scales, self.architecture.context_scales)]
        for observed, values in scale_pairs:
            expected = torch.tensor(values, dtype=torch.float32, device=self.execution_device)
            if not torch.equal(observed, expected) or bool((observed <= 0).any()):
                raise ValueError("architecture scales changed or are not positive in FP32")
        for name in ("value_bound", "schedule_horizon"):
            scalar = torch.tensor(getattr(self.architecture, name), dtype=torch.float32)
            if not bool(torch.isfinite(scalar)) or scalar.item() <= 0:
                raise ValueError(f"architecture {name} is not positive finite in FP32")

    def from_cpu_batch(self, batch: reference.TypedConfigurationBatch) -> TrainingConfigurationBatch:
        """Copy validated CPU64 inputs; this is not a training-record admission API."""
        checked = reference._validate_batch(self.architecture, batch)
        def converted(tensor, dtype):
            return tensor.detach().to(device=self.execution_device, dtype=dtype).clone()
        return TrainingConfigurationBatch(
            self.architecture.architecture_sha256,
            converted(checked.forward_time, torch.float32),
            converted(checked.context, torch.float32),
            tuple(converted(value, torch.float32) for value in checked.coordinates),
            tuple(converted(value, torch.int64) for value in checked.batch_indices),
        )

    def _validate_batch(self, batch: TrainingConfigurationBatch) -> int:
        if type(batch) is not TrainingConfigurationBatch:
            raise TypeError("an exact TrainingConfigurationBatch is required")
        if batch.architecture_sha256 != self.architecture.architecture_sha256:
            raise ValueError("batch architecture does not match this training view")
        self._float_tensor(batch.forward_time, "forward_time", finite=False)
        self._float_tensor(batch.context, "context", finite=False)
        if batch.forward_time.ndim != 1:
            raise ValueError("forward_time must be a vector")
        size = batch.forward_time.numel()
        if not 1 <= size <= reference.MAX_CONFIGURATION_ENERGY_BATCH_SIZE:
            raise ValueError("batch size exceeds the retained implementation limit")
        if batch.context.shape != (size, self.architecture.context_dimension):
            raise ValueError("context dimensions do not match the architecture")
        if type(batch.coordinates) is not tuple or type(batch.batch_indices) is not tuple:
            raise TypeError("ragged fields must be tuples in architecture type order")
        if len(batch.coordinates) != len(self.architecture.type_ids) or len(batch.batch_indices) != len(batch.coordinates):
            raise ValueError("ragged type roster differs from the architecture")
        total_occurrences = total_coordinates = 0
        for coordinates, owners, dimension in zip(batch.coordinates, batch.batch_indices, self.architecture.type_dimensions):
            self._float_tensor(coordinates, "coordinates", finite=False)
            if coordinates.ndim != 2 or coordinates.shape[1] != dimension:
                raise ValueError("event coordinate dimension differs from the architecture")
            if not isinstance(owners, torch.Tensor) or owners.dtype != torch.int64 or owners.device != self.execution_device:
                raise ValueError("batch indices must be int64 on the explicit execution device")
            if owners.layout != torch.strided or owners.shape != (coordinates.shape[0],):
                raise ValueError("batch indices must align with occurrences")
            total_occurrences += owners.numel()
            total_coordinates += coordinates.numel()
        if total_occurrences > reference.MAX_CONFIGURATION_ENERGY_BATCH_OCCURRENCES or total_coordinates > reference.MAX_CONFIGURATION_ENERGY_BATCH_COORDINATES:
            raise ValueError("ragged batch exceeds the retained implementation limits")
        reference._preflight_forward_work(
            self.architecture, batch_size=size,
            occurrence_counts=tuple(value.shape[0] for value in batch.coordinates),
        )
        # Owner masks scan every occurrence for every group. Bound this draft
        # reduction's extra work as well as the original graph's affine work.
        if size * total_occurrences > reference.MAX_CONFIGURATION_ENERGY_POOL_WORK:
            raise ValueError("segment-owner scans exceed the draft work limit")
        self._float_tensor(batch.forward_time, "forward_time")
        self._float_tensor(batch.context, "context")
        if bool(((batch.forward_time < 0) | (batch.forward_time > self.architecture.schedule_horizon)).any()):
            raise ValueError("forward times must lie in the architecture horizon")
        counts = torch.zeros(size, dtype=torch.int64, device=self.execution_device)
        for coordinates, owners in zip(batch.coordinates, batch.batch_indices):
            self._float_tensor(coordinates, "coordinates")
            if bool(((owners < 0) | (owners >= size)).any()):
                raise ValueError("event owner is outside this batch")
            counts += torch.stack([(owners == row).sum() for row in range(size)])
        if bool((counts > self.architecture.total_cap).any()):
            raise ValueError("configuration cap exceeded; truncation is forbidden")
        return size

    def forward(self, batch: TrainingConfigurationBatch) -> torch.Tensor:
        if torch.is_autocast_enabled(self.execution_device.type):
            raise ValueError("autocast is not allowed for this FP32 training view")
        self._validate_state()
        size = self._validate_batch(batch)
        pooled = torch.zeros((size, self.architecture.event_embedding_width), dtype=torch.float32, device=self.execution_device)
        counts = torch.zeros(size, dtype=torch.float32, device=self.execution_device)
        for encoder, coordinates, owners in zip(self.event_encoders, batch.coordinates, batch.batch_indices):
            if not owners.numel():
                continue
            encoded = encoder(coordinates)
            # No scatter-add atomics. This is a draft FP32 reduction, not fsum.
            pooled = pooled + torch.stack([
                encoded[owners == row].sum(dim=0) for row in range(size)
            ])
            counts += torch.stack([(owners == row).sum() for row in range(size)])
        normalized_time = 2.0 * (batch.forward_time / self.architecture.schedule_horizon) - 1.0
        context = self.context_encoder(normalized_time, batch.context)
        inputs = torch.cat((pooled, context, (counts / max(1, self.architecture.total_cap)).unsqueeze(-1)), dim=-1)
        raw = self.readout(inputs)
        bound = self.architecture.value_bound
        result = bound * torch.tanh(raw / bound)
        if not bool(torch.isfinite(result).all()) or bool((result.abs() > bound).any()):
            raise ArithmeticError("training-view bounded energy is invalid")
        return result
