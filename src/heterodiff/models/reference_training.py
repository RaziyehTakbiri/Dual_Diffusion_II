"""Deterministic CPU training and atomic checkpoints for the fixed-grid reference.

This module is an optional-PyTorch boundary.  It deliberately is not imported
from :mod:`heterodiff.models`, so the framework-free NumPy/theory package stays
importable when PyTorch is absent.

The checkpoint has two layers.  A small canonical-JSON header commits to the
length and SHA-256 of a Torch payload, while the caller must also supply the
SHA-256 of the complete checkpoint at load time.  The Torch payload contains
only plain primitive containers and dense CPU tensors and is loaded with
``weights_only=True``.  PyTorch's format still uses a restricted pickle
decoder internally; consequently the required expected digest must come from
a trusted run manifest, not from the checkpoint file itself.  This module
never opts into arbitrary-class unpickling.

Successful writes use a temporary regular file in the destination directory,
flush and ``fsync`` its contents, then publish it with ``os.replace``.  This
gives atomic old-or-new visibility on filesystems that implement same-directory
replace atomically.  Directory ``fsync`` is attempted for crash durability but
is not available on every supported platform; lack of directory-fsync support
does not weaken the old-or-new visibility claim, only the stronger claim that
the directory entry survives an abrupt power loss.

This is a bounded CPU smoke trainer, not a production data loader and not an
empirical result.  Its input pool already contains model-visible noisy state
and explicit clean/noise targets produced by the separately tested reference
corruption API.  The trainer never invents a second corruption law.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
import errno
import hashlib
import hmac
import io
import json
import math
from numbers import Integral, Real
import os
from pathlib import Path
import re
import stat
import struct
import tempfile
from typing import Any, Dict, Optional, Tuple, Union
import zipfile

try:
    import torch
except ModuleNotFoundError as error:  # pragma: no cover - no-Torch boundary test
    if error.name == "torch":
        raise ModuleNotFoundError(
            "heterodiff.models.reference_training requires the optional "
            "PyTorch dependency; install the 'reference' extra"
        ) from error
    raise

from heterodiff.artifacts.manifest import canonical_json_dumps, sha256_bytes

from .fixed_grid import (
    FixedGridReferenceDenoiser,
    hybrid_denoising_loss,
)
from .reference_config import FixedGridReferenceConfig


PathLike = Union[str, os.PathLike]

_CONTAINER_MAGIC = b"HDRCKP1\0"
_CONTAINER_VERSION = 1
_PAYLOAD_VERSION = 1
_SAMPLER_VERSION = 1
_CONFIG_FORMAT = "heterodiff-fixed-grid-training-v1"
_PAYLOAD_FORMAT = "torch-save-weights-only-v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PROVENANCE_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
_HEADER_LENGTH_BYTES = 4
_MAX_SAFE_INTEGER = 2**53 - 1
_HARD_MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024
_HARD_MAX_TENSOR_BYTES = 2 * 1024 * 1024 * 1024
_HARD_MAX_DATASET_SIZE = 10_000_000
_HARD_MAX_TRAINING_STEPS = 1_000_000_000
_BINARY64_EPSILON = float.fromhex("0x1.0000000000000p-52")
_BINARY64_MIN_NORMAL = float.fromhex("0x1.0000000000000p-1022")


class CheckpointError(ValueError):
    """Base class for fail-closed checkpoint errors."""


class CheckpointIntegrityError(CheckpointError):
    """The artifact is truncated, malformed, or fails a checksum."""


class CheckpointMismatchError(CheckpointError):
    """The artifact does not match the declared run identity."""


class CheckpointReplayError(CheckpointError):
    """The artifact would repeat or roll back an accepted training step."""


class CheckpointResourceError(CheckpointError):
    """The artifact exceeds an explicit bounded-work guard."""


def _plain_int(
    value: object,
    *,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("{} must be an integer".format(name))
    result = int(value)
    if result < minimum or result > maximum:
        raise ValueError(
            "{} must lie in [{}, {}]".format(name, minimum, maximum)
        )
    return result


def _finite_real(
    value: object,
    *,
    name: str,
    minimum: float,
    maximum: float,
    minimum_inclusive: bool = True,
) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{} must be a real number".format(name))
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("{} must be finite".format(name))
    below = result < minimum if minimum_inclusive else result <= minimum
    if below or result > maximum:
        left = "[" if minimum_inclusive else "("
        raise ValueError(
            "{} must lie in {}{}, {}]".format(name, left, minimum, maximum)
        )
    return result


def _sha256(value: object, *, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(
            "{} must be a lowercase 64-character SHA-256 digest".format(name)
        )
    return value


def _strict_json_loads(text: object, *, name: str) -> object:
    if not isinstance(text, str):
        raise CheckpointIntegrityError("{} must be UTF-8 JSON text".format(name))

    def reject_constant(value: str) -> None:
        raise CheckpointIntegrityError(
            "{} contains non-standard JSON constant {}".format(name, value)
        )

    def object_pairs(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise CheckpointIntegrityError(
                    "{} contains duplicate key {!r}".format(name, key)
                )
            result[key] = value
        return result

    try:
        return json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_constant=reject_constant,
        )
    except json.JSONDecodeError as error:
        raise CheckpointIntegrityError("{} is invalid JSON".format(name)) from error


def _validated_canonical_mapping(
    text: object,
    digest: object,
    *,
    name: str,
) -> Dict[str, Any]:
    expected = _sha256(digest, name="{} digest".format(name))
    value = _strict_json_loads(text, name=name)
    if not isinstance(value, dict):
        raise CheckpointIntegrityError("{} root must be a mapping".format(name))
    try:
        canonical = canonical_json_dumps(value)
    except (TypeError, ValueError) as error:
        raise CheckpointIntegrityError(
            "{} is outside the canonical JSON domain".format(name)
        ) from error
    if canonical != text:
        raise CheckpointIntegrityError("{} is not canonical JSON".format(name))
    actual = sha256_bytes(text.encode("utf-8"))
    if not hmac.compare_digest(actual, expected):
        raise CheckpointIntegrityError("{} digest mismatch".format(name))
    return value


@dataclass(frozen=True)
class CheckpointLimits:
    """Explicit denial-of-service guards for one checkpoint operation."""

    max_file_bytes: int = 1_073_741_824
    max_header_bytes: int = 65_536
    max_archive_entries: int = 100_000
    max_tensors: int = 100_000
    max_tensor_bytes: int = 1_073_741_824
    max_container_items: int = 500_000
    max_depth: int = 32
    max_string_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        specifications = (
            ("max_file_bytes", self.max_file_bytes, 1_024, _HARD_MAX_FILE_BYTES),
            ("max_header_bytes", self.max_header_bytes, 64, 1_048_576),
            ("max_archive_entries", self.max_archive_entries, 1, 1_000_000),
            ("max_tensors", self.max_tensors, 1, 1_000_000),
            ("max_tensor_bytes", self.max_tensor_bytes, 1, _HARD_MAX_TENSOR_BYTES),
            ("max_container_items", self.max_container_items, 1, 5_000_000),
            ("max_depth", self.max_depth, 1, 128),
            ("max_string_bytes", self.max_string_bytes, 1, 16_777_216),
        )
        for name, value, minimum, maximum in specifications:
            object.__setattr__(
                self,
                name,
                _plain_int(value, name=name, minimum=minimum, maximum=maximum),
            )


@dataclass(frozen=True)
class FixedGridTrainingConfig:
    """Frozen optimizer, scheduler, batching, and local-RNG configuration."""

    dataset_size: int
    batch_size: int
    sampler_seed: int
    local_generator_seed: int
    learning_rate: float = 1.0e-3
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999
    adam_epsilon: float = 1.0e-8
    weight_decay: float = 0.0
    scheduler_step_size: int = 1
    scheduler_gamma: float = 1.0
    categorical_weight: float = 1.0
    continuous_weight: float = 1.0
    gradient_clip_norm: Optional[float] = None
    max_training_steps: int = 1_000_000

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_size",
            _plain_int(
                self.dataset_size,
                name="dataset_size",
                minimum=1,
                maximum=_HARD_MAX_DATASET_SIZE,
            ),
        )
        object.__setattr__(
            self,
            "batch_size",
            _plain_int(
                self.batch_size,
                name="batch_size",
                minimum=1,
                maximum=_HARD_MAX_DATASET_SIZE,
            ),
        )
        if self.batch_size > self.dataset_size:
            raise ValueError("batch_size cannot exceed dataset_size")
        for name in ("sampler_seed", "local_generator_seed"):
            object.__setattr__(
                self,
                name,
                _plain_int(
                    getattr(self, name),
                    name=name,
                    minimum=0,
                    maximum=2**63 - 1,
                ),
            )
        object.__setattr__(
            self,
            "learning_rate",
            _finite_real(
                self.learning_rate,
                name="learning_rate",
                minimum=0.0,
                maximum=1.0e3,
                minimum_inclusive=False,
            ),
        )
        beta1 = _finite_real(
            self.adam_beta1,
            name="adam_beta1",
            minimum=0.0,
            maximum=1.0,
        )
        beta2 = _finite_real(
            self.adam_beta2,
            name="adam_beta2",
            minimum=0.0,
            maximum=1.0,
        )
        if beta1 >= 1.0 or beta2 >= 1.0:
            raise ValueError("Adam beta values must lie in [0, 1)")
        object.__setattr__(self, "adam_beta1", beta1)
        object.__setattr__(self, "adam_beta2", beta2)
        object.__setattr__(
            self,
            "adam_epsilon",
            _finite_real(
                self.adam_epsilon,
                name="adam_epsilon",
                minimum=0.0,
                maximum=1.0,
                minimum_inclusive=False,
            ),
        )
        object.__setattr__(
            self,
            "weight_decay",
            _finite_real(
                self.weight_decay,
                name="weight_decay",
                minimum=0.0,
                maximum=1.0e3,
            ),
        )
        object.__setattr__(
            self,
            "scheduler_step_size",
            _plain_int(
                self.scheduler_step_size,
                name="scheduler_step_size",
                minimum=1,
                maximum=_HARD_MAX_TRAINING_STEPS,
            ),
        )
        gamma = _finite_real(
            self.scheduler_gamma,
            name="scheduler_gamma",
            minimum=0.0,
            maximum=1.0,
            minimum_inclusive=False,
        )
        object.__setattr__(self, "scheduler_gamma", gamma)
        categorical = _finite_real(
            self.categorical_weight,
            name="categorical_weight",
            minimum=0.0,
            maximum=1.0e6,
        )
        continuous = _finite_real(
            self.continuous_weight,
            name="continuous_weight",
            minimum=0.0,
            maximum=1.0e6,
        )
        if categorical == 0.0 and continuous == 0.0:
            raise ValueError("at least one modality weight must be positive")
        object.__setattr__(self, "categorical_weight", categorical)
        object.__setattr__(self, "continuous_weight", continuous)
        if self.gradient_clip_norm is not None:
            object.__setattr__(
                self,
                "gradient_clip_norm",
                _finite_real(
                    self.gradient_clip_norm,
                    name="gradient_clip_norm",
                    minimum=0.0,
                    maximum=1.0e12,
                    minimum_inclusive=False,
                ),
            )
        maximum_steps = _plain_int(
            self.max_training_steps,
            name="max_training_steps",
            minimum=1,
            maximum=_HARD_MAX_TRAINING_STEPS,
        )
        object.__setattr__(self, "max_training_steps", maximum_steps)
        scheduled_updates = maximum_steps // self.scheduler_step_size
        terminal_learning_rate = self.learning_rate * (
            self.scheduler_gamma**scheduled_updates
        )
        if terminal_learning_rate < _BINARY64_MIN_NORMAL:
            raise ValueError(
                "the declared StepLR schedule underflows or enters the subnormal "
                "learning-rate range before max_training_steps"
            )


@dataclass(frozen=True)
class CheckpointIdentity:
    """Canonical schema plus declared code/data/environment digests."""

    schema_json: str
    schema_sha256: str
    provenance_json: str
    provenance_sha256: str

    def __post_init__(self) -> None:
        _validated_canonical_mapping(
            self.schema_json, self.schema_sha256, name="schema JSON"
        )
        provenance = _validated_canonical_mapping(
            self.provenance_json,
            self.provenance_sha256,
            name="provenance JSON",
        )
        if not provenance or len(provenance) > 32:
            raise ValueError("provenance must contain between 1 and 32 identifiers")
        for key, digest in provenance.items():
            if not isinstance(key, str) or _PROVENANCE_KEY_RE.fullmatch(key) is None:
                raise ValueError("provenance keys must be bounded canonical identifiers")
            _sha256(digest, name="provenance identifier {!r}".format(key))

    @classmethod
    def from_mappings(
        cls,
        *,
        schema: Mapping,
        provenance: Mapping,
    ) -> "CheckpointIdentity":
        if not isinstance(schema, Mapping):
            raise TypeError("schema must be a mapping")
        if not isinstance(provenance, Mapping):
            raise TypeError("provenance must be a mapping")
        schema_text = canonical_json_dumps(schema)
        provenance_text = canonical_json_dumps(provenance)
        return cls(
            schema_json=schema_text,
            schema_sha256=sha256_bytes(schema_text.encode("utf-8")),
            provenance_json=provenance_text,
            provenance_sha256=sha256_bytes(provenance_text.encode("utf-8")),
        )


class DeterministicPermutationSampler:
    """One explicit-generator permutation stream with checkpointable position."""

    def __init__(self, dataset_size: int, seed: int) -> None:
        self.dataset_size = _plain_int(
            dataset_size,
            name="dataset_size",
            minimum=1,
            maximum=_HARD_MAX_DATASET_SIZE,
        )
        self.seed = _plain_int(
            seed, name="seed", minimum=0, maximum=2**63 - 1
        )
        self._generator = torch.Generator(device="cpu")
        self._generator.manual_seed(self.seed)
        self._permutation = torch.randperm(
            self.dataset_size, generator=self._generator, device="cpu"
        )
        self.cursor = 0
        self.epoch = 0
        self.batches_emitted = 0

    @property
    def permutation(self) -> torch.Tensor:
        return self._permutation.clone()

    def next_indices(self, batch_size: int) -> torch.Tensor:
        size = _plain_int(
            batch_size,
            name="batch_size",
            minimum=1,
            maximum=self.dataset_size,
        )
        if self.cursor == self.dataset_size:
            self.epoch += 1
            self._permutation = torch.randperm(
                self.dataset_size, generator=self._generator, device="cpu"
            )
            self.cursor = 0
        stop = min(self.dataset_size, self.cursor + size)
        result = self._permutation[self.cursor : stop].clone()
        self.cursor = stop
        self.batches_emitted += 1
        return result

    def state_dict(self) -> Dict[str, object]:
        return {
            "version": _SAMPLER_VERSION,
            "dataset_size": self.dataset_size,
            "seed": self.seed,
            "epoch": self.epoch,
            "cursor": self.cursor,
            "batches_emitted": self.batches_emitted,
            "permutation": self._permutation.clone(),
            "generator_state": self._generator.get_state().clone(),
        }

    def load_state_dict(self, state: object) -> None:
        if type(state) is not dict:
            raise CheckpointIntegrityError("sampler state must be a plain mapping")
        expected_keys = {
            "version",
            "dataset_size",
            "seed",
            "epoch",
            "cursor",
            "batches_emitted",
            "permutation",
            "generator_state",
        }
        if set(state) != expected_keys:
            raise CheckpointIntegrityError("sampler state has missing or unknown fields")
        if state["version"] != _SAMPLER_VERSION:
            raise CheckpointIntegrityError("unsupported sampler-state version")
        if state["dataset_size"] != self.dataset_size or state["seed"] != self.seed:
            raise CheckpointMismatchError("sampler dataset size or seed mismatch")
        epoch = _plain_int(
            state["epoch"],
            name="sampler epoch",
            minimum=0,
            maximum=_HARD_MAX_TRAINING_STEPS,
        )
        cursor = _plain_int(
            state["cursor"],
            name="sampler cursor",
            minimum=0,
            maximum=self.dataset_size,
        )
        emitted = _plain_int(
            state["batches_emitted"],
            name="sampler batches_emitted",
            minimum=0,
            maximum=_HARD_MAX_TRAINING_STEPS,
        )
        permutation = state["permutation"]
        if type(permutation) is not torch.Tensor:
            raise CheckpointIntegrityError("sampler permutation must be a tensor")
        if (
            permutation.device.type != "cpu"
            or permutation.dtype != torch.int64
            or tuple(permutation.shape) != (self.dataset_size,)
            or permutation.layout != torch.strided
        ):
            raise CheckpointIntegrityError(
                "sampler permutation must be a dense CPU int64 vector"
            )
        expected = torch.arange(self.dataset_size, dtype=torch.int64)
        if not torch.equal(torch.sort(permutation).values, expected):
            raise CheckpointIntegrityError("sampler permutation is not a bijection")
        generator_state = _validated_generator_state(
            state["generator_state"], name="sampler generator state"
        )
        probe = torch.Generator(device="cpu")
        try:
            probe.set_state(generator_state)
        except RuntimeError as error:
            raise CheckpointIntegrityError(
                "sampler generator state is invalid"
            ) from error
        self._permutation = permutation.clone()
        self._generator.set_state(generator_state)
        self.cursor = cursor
        self.epoch = epoch
        self.batches_emitted = emitted


def _validated_generator_state(value: object, *, name: str) -> torch.Tensor:
    if type(value) is not torch.Tensor:
        raise CheckpointIntegrityError("{} must be a tensor".format(name))
    if (
        value.device.type != "cpu"
        or value.dtype != torch.uint8
        or value.ndim != 1
        or value.layout != torch.strided
        or value.numel() == 0
        or value.numel() > 1_000_000
    ):
        raise CheckpointIntegrityError(
            "{} must be a bounded dense CPU uint8 vector".format(name)
        )
    return value.clone()


@dataclass(frozen=True)
class FixedGridTrainingBatch:
    """Tensor-only pool compatible with the fixed-grid model and hybrid loss.

    The categorical targets are clean ``x0`` states and the continuous targets
    are the exact forward Gaussian ``epsilon`` values.  No target enters the
    model-visible argument list.
    """

    discrete_noisy_state: torch.Tensor
    continuous_noisy_state: torch.Tensor
    elapsed_time_input: torch.Tensor
    diffusion_progress: torch.Tensor
    sequence_mask: torch.Tensor
    discrete_observed_mask: torch.Tensor
    continuous_observed_mask: torch.Tensor
    elapsed_time_observed_mask: torch.Tensor
    discrete_target: torch.Tensor
    continuous_target: torch.Tensor
    discrete_loss_mask: torch.Tensor
    continuous_loss_mask: torch.Tensor

    def __post_init__(self) -> None:
        values = tuple(getattr(self, field.name) for field in fields(self))
        if any(type(value) is not torch.Tensor for value in values):
            raise TypeError("every training-batch field must be a torch.Tensor")
        if any(value.device.type != "cpu" for value in values):
            raise ValueError("the deterministic smoke trainer accepts CPU tensors only")
        if any(value.ndim == 0 for value in values):
            raise ValueError("every training-batch tensor must have a batch axis")
        sizes = {int(value.shape[0]) for value in values}
        if len(sizes) != 1 or next(iter(sizes)) == 0:
            raise ValueError("all training-batch tensors must share a non-empty batch axis")

    @property
    def num_samples(self) -> int:
        return int(self.discrete_noisy_state.shape[0])

    def select(self, indices: torch.Tensor) -> "FixedGridTrainingBatch":
        if (
            type(indices) is not torch.Tensor
            or indices.device.type != "cpu"
            or indices.dtype != torch.int64
            or indices.ndim != 1
            or indices.numel() == 0
        ):
            raise TypeError("indices must be a non-empty CPU int64 vector")
        if bool(torch.any((indices < 0) | (indices >= self.num_samples)).item()):
            raise IndexError("training-batch index is out of range")
        return FixedGridTrainingBatch(
            **{
                field.name: getattr(self, field.name).index_select(0, indices)
                for field in fields(self)
            }
        )


@dataclass(frozen=True)
class TrainingStepResult:
    """Detached exact result of one completed optimization step."""

    completed_step: int
    batch_indices: torch.Tensor
    total_loss: torch.Tensor
    categorical_loss: torch.Tensor
    continuous_loss: torch.Tensor


@dataclass
class _TreeBudget:
    tensors: int = 0
    tensor_bytes: int = 0
    items: int = 0


def _tensor_nbytes(tensor: torch.Tensor) -> int:
    return int(tensor.numel()) * int(tensor.element_size())


def _safe_tree_clone(
    value: object,
    *,
    limits: CheckpointLimits,
    budget: _TreeBudget,
    depth: int = 0,
    location: str = "$",
) -> object:
    if depth > limits.max_depth:
        raise CheckpointResourceError("checkpoint container nesting is too deep")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        if abs(value) > _MAX_SAFE_INTEGER:
            raise CheckpointResourceError(
                "{} integer exceeds the interoperable range".format(location)
            )
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CheckpointIntegrityError(
                "{} contains a non-finite float".format(location)
            )
        return value
    if isinstance(value, str):
        try:
            encoded = value.encode("utf-8", errors="strict")
        except UnicodeEncodeError as error:
            raise CheckpointIntegrityError(
                "{} contains invalid Unicode".format(location)
            ) from error
        if len(encoded) > limits.max_string_bytes:
            raise CheckpointResourceError("checkpoint string exceeds its byte guard")
        return value
    if type(value) is torch.Tensor:
        if (
            value.device.type != "cpu"
            or value.layout != torch.strided
            or value.is_quantized
            or value.is_complex()
        ):
            raise CheckpointIntegrityError(
                "{} must be a dense, non-quantized, non-complex CPU tensor".format(
                    location
                )
            )
        tensor_bytes = _tensor_nbytes(value)
        budget.tensors += 1
        budget.tensor_bytes += tensor_bytes
        if budget.tensors > limits.max_tensors:
            raise CheckpointResourceError("checkpoint tensor-count guard exceeded")
        if budget.tensor_bytes > limits.max_tensor_bytes:
            raise CheckpointResourceError("checkpoint tensor-byte guard exceeded")
        if value.is_floating_point() and bool(torch.any(~torch.isfinite(value)).item()):
            raise CheckpointIntegrityError(
                "{} contains a non-finite tensor".format(location)
            )
        return value.detach().clone().contiguous()
    if type(value) is dict:
        budget.items += len(value)
        if budget.items > limits.max_container_items:
            raise CheckpointResourceError("checkpoint container-item guard exceeded")
        result = {}
        for key, item in value.items():
            if not (
                (isinstance(key, str))
                or (isinstance(key, int) and not isinstance(key, bool))
            ):
                raise CheckpointIntegrityError(
                    "{} has a non-string/non-integer mapping key".format(location)
                )
            result[key] = _safe_tree_clone(
                item,
                limits=limits,
                budget=budget,
                depth=depth + 1,
                location="{}.{}".format(location, key),
            )
        return result
    if type(value) in (list, tuple):
        budget.items += len(value)
        if budget.items > limits.max_container_items:
            raise CheckpointResourceError("checkpoint container-item guard exceeded")
        converted = [
            _safe_tree_clone(
                item,
                limits=limits,
                budget=budget,
                depth=depth + 1,
                location="{}[{}]".format(location, index),
            )
            for index, item in enumerate(value)
        ]
        return tuple(converted) if type(value) is tuple else converted
    raise CheckpointIntegrityError(
        "{} has unsupported type {}; only primitives, plain containers, and "
        "dense CPU tensors are permitted".format(location, type(value).__name__)
    )


def _model_config_mapping(config: FixedGridReferenceConfig) -> Dict[str, object]:
    return {field.name: getattr(config, field.name) for field in fields(config)}


def _training_config_mapping(config: FixedGridTrainingConfig) -> Dict[str, object]:
    return {field.name: getattr(config, field.name) for field in fields(config)}


def _canonical_run_config(
    model_config: FixedGridReferenceConfig,
    training_config: FixedGridTrainingConfig,
) -> Tuple[str, str]:
    mapping = {
        "format": _CONFIG_FORMAT,
        "model": _model_config_mapping(model_config),
        "optimization": {
            "optimizer": "torch.optim.AdamW",
            "optimizer_options": {
                "amsgrad": False,
                "capturable": False,
                "decoupled_weight_decay": True,
                "differentiable": False,
                "foreach": False,
                "fused": False,
                "maximize": False,
            },
            "scheduler": "torch.optim.lr_scheduler.StepLR",
        },
        "training": _training_config_mapping(training_config),
    }
    text = canonical_json_dumps(mapping)
    return text, sha256_bytes(text.encode("utf-8"))


def _make_optimizer(
    model: FixedGridReferenceDenoiser,
    config: FixedGridTrainingConfig,
) -> torch.optim.Optimizer:
    return torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        betas=(config.adam_beta1, config.adam_beta2),
        eps=config.adam_epsilon,
        weight_decay=config.weight_decay,
        amsgrad=False,
        maximize=False,
        foreach=False,
        capturable=False,
        differentiable=False,
        fused=False,
    )


def _make_scheduler(
    optimizer: torch.optim.Optimizer,
    config: FixedGridTrainingConfig,
) -> torch.optim.lr_scheduler.StepLR:
    return torch.optim.lr_scheduler.StepLR(
        optimizer,
        step_size=config.scheduler_step_size,
        gamma=config.scheduler_gamma,
    )


def _validate_sampler_step_invariant(
    state: Mapping,
    *,
    config: FixedGridTrainingConfig,
    training_step: int,
) -> None:
    epoch = int(state["epoch"])
    cursor = int(state["cursor"])
    emitted = int(state["batches_emitted"])
    batches_per_epoch = (
        config.dataset_size + config.batch_size - 1
    ) // config.batch_size
    if cursor == 0:
        batches_in_epoch = 0
    else:
        if cursor != config.dataset_size and cursor % config.batch_size != 0:
            raise CheckpointIntegrityError(
                "sampler cursor is not reachable under the configured batch size"
            )
        batches_in_epoch = (cursor + config.batch_size - 1) // config.batch_size
    expected = epoch * batches_per_epoch + batches_in_epoch
    if emitted != expected or emitted != training_step:
        raise CheckpointIntegrityError(
            "sampler cursor/epoch/batch count does not match completed training step"
        )


def _validate_optimizer_scheduler_contract(
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.StepLR,
    *,
    config: FixedGridTrainingConfig,
    training_step: int,
) -> None:
    if len(optimizer.param_groups) != 1:
        raise CheckpointIntegrityError("checkpoint optimizer must have one parameter group")
    group = optimizer.param_groups[0]
    expected_group_keys = {
        "params",
        "lr",
        "betas",
        "eps",
        "weight_decay",
        "amsgrad",
        "maximize",
        "foreach",
        "capturable",
        "differentiable",
        "fused",
        "decoupled_weight_decay",
        "initial_lr",
    }
    if set(group) != expected_group_keys:
        raise CheckpointIntegrityError(
            "checkpoint optimizer group has missing or unknown fields"
        )
    expected_static = {
        "betas": (config.adam_beta1, config.adam_beta2),
        "eps": config.adam_epsilon,
        "weight_decay": config.weight_decay,
        "amsgrad": False,
        "maximize": False,
        "foreach": False,
        "capturable": False,
        "differentiable": False,
        "fused": False,
        "decoupled_weight_decay": True,
    }
    for name, expected in expected_static.items():
        if group.get(name) != expected:
            raise CheckpointMismatchError(
                "optimizer option {!r} does not match configuration".format(name)
            )
    if group.get("initial_lr") != config.learning_rate:
        raise CheckpointMismatchError("optimizer initial learning rate mismatch")
    expected_lr = config.learning_rate * (
        config.scheduler_gamma
        ** (training_step // config.scheduler_step_size)
    )
    scheduled_updates = training_step // config.scheduler_step_size
    # A valid chainable StepLR performs one rounded binary64 multiplication per
    # scheduled update, while the closed form above rounds through ``pow``.
    # Scale the comparison by a conservative forward-error bound.  The config
    # rejects the numerically unstable subnormal range, and the global step
    # guard keeps this tolerance below 2e-6.
    lr_relative_tolerance = max(
        32.0 * _BINARY64_EPSILON,
        8.0 * (scheduled_updates + 1) * _BINARY64_EPSILON,
    )
    actual_lr = group.get("lr")
    if (
        isinstance(actual_lr, bool)
        or not isinstance(actual_lr, Real)
        or not math.isfinite(float(actual_lr))
        or float(actual_lr) <= 0.0
        or not math.isclose(
            float(actual_lr),
            expected_lr,
            rel_tol=lr_relative_tolerance,
            abs_tol=0.0,
        )
    ):
        raise CheckpointIntegrityError("optimizer learning rate is inconsistent with step")
    if scheduler.step_size != config.scheduler_step_size:
        raise CheckpointMismatchError("scheduler step size mismatch")
    if scheduler.gamma != config.scheduler_gamma:
        raise CheckpointMismatchError("scheduler gamma mismatch")
    if scheduler.last_epoch != training_step:
        raise CheckpointIntegrityError("scheduler epoch does not match training step")
    if scheduler.base_lrs != [config.learning_rate]:
        raise CheckpointMismatchError("scheduler base learning rate mismatch")
    # StepLR's ordinary chainable update repeatedly multiplies the current
    # binary64 value.  That may differ by one ulp from the mathematically
    # equivalent closed form ``base_lr * gamma**k`` used above (for example,
    # 0.002 * 0.8 * 0.8).  The scheduler's serialized last value must therefore
    # agree *exactly* with the optimizer, while the closed form is only a tight
    # independent numerical consistency check.
    if scheduler.get_last_lr() != [actual_lr]:
        raise CheckpointIntegrityError("scheduler current learning rate is inconsistent")
    scheduler_state = scheduler.state_dict()
    expected_scheduler_keys = {
        "step_size",
        "gamma",
        "base_lrs",
        "last_epoch",
        "_step_count",
        "_is_initial",
        "_get_lr_called_within_step",
        "_last_lr",
    }
    if set(scheduler_state) != expected_scheduler_keys:
        raise CheckpointIntegrityError(
            "checkpoint scheduler has missing or unknown fields"
        )
    if (
        type(scheduler_state["last_epoch"]) is not int
        or type(scheduler_state["_step_count"]) is not int
        or scheduler_state["_step_count"] != training_step + 1
        or type(scheduler_state["_is_initial"]) is not bool
        or scheduler_state["_is_initial"]
        or type(scheduler_state["_get_lr_called_within_step"]) is not bool
        or scheduler_state["_get_lr_called_within_step"]
    ):
        raise CheckpointIntegrityError("checkpoint scheduler counters or flags are invalid")

    state = optimizer.state
    parameters = list(group["params"])
    if training_step == 0:
        if state:
            raise CheckpointIntegrityError("step-zero optimizer state must be empty")
    else:
        if len(state) != len(parameters) or any(parameter not in state for parameter in parameters):
            raise CheckpointIntegrityError(
                "optimizer state must cover every model parameter after a step"
            )
        for parameter in parameters:
            item = state[parameter]
            if type(item) is not dict or set(item) != {
                "step",
                "exp_avg",
                "exp_avg_sq",
            }:
                raise CheckpointIntegrityError(
                    "AdamW state has missing or unknown fields"
                )
            step_value = item.get("step")
            if (
                type(step_value) is not torch.Tensor
                or step_value.device.type != "cpu"
                or step_value.dtype != torch.float32
                or step_value.layout != torch.strided
                or step_value.ndim != 0
            ):
                raise CheckpointIntegrityError("AdamW state has an invalid step counter")
            if float(step_value.detach().item()) != float(training_step):
                raise CheckpointIntegrityError(
                    "optimizer step counter does not match training step"
                )
            for state_name in ("exp_avg", "exp_avg_sq"):
                moment = item[state_name]
                if (
                    type(moment) is not torch.Tensor
                    or moment.device != parameter.device
                    or moment.dtype != parameter.dtype
                    or moment.layout != torch.strided
                    or tuple(moment.shape) != tuple(parameter.shape)
                    or bool(torch.any(~torch.isfinite(moment)).item())
                ):
                    raise CheckpointIntegrityError(
                        "AdamW {} is incompatible with its parameter".format(
                            state_name
                        )
                    )
            if bool(torch.any(item["exp_avg_sq"] < 0.0).item()):
                raise CheckpointIntegrityError(
                    "AdamW second moment cannot contain a negative value"
                )


def _validate_serialized_optimizer_scheduler_state(
    optimizer_state: object,
    scheduler_state: object,
    *,
    model: FixedGridReferenceDenoiser,
    config: FixedGridTrainingConfig,
    training_step: int,
) -> None:
    """Validate locked-Torch state *before* ``load_state_dict`` can cast it."""

    if type(optimizer_state) is not dict or set(optimizer_state) != {
        "state",
        "param_groups",
    }:
        raise CheckpointIntegrityError(
            "serialized optimizer has missing or unknown fields"
        )
    groups = optimizer_state["param_groups"]
    states = optimizer_state["state"]
    if type(groups) is not list or len(groups) != 1 or type(groups[0]) is not dict:
        raise CheckpointIntegrityError(
            "serialized optimizer must contain one plain parameter group"
        )
    group = groups[0]
    expected_group_keys = {
        "params",
        "lr",
        "betas",
        "eps",
        "weight_decay",
        "amsgrad",
        "maximize",
        "foreach",
        "capturable",
        "differentiable",
        "fused",
        "decoupled_weight_decay",
        "initial_lr",
    }
    if set(group) != expected_group_keys:
        raise CheckpointIntegrityError(
            "serialized optimizer group has missing or unknown fields"
        )
    parameters = list(model.parameters())
    expected_indices = list(range(len(parameters)))
    if (
        type(group["params"]) is not list
        or any(type(index) is not int for index in group["params"])
        or group["params"] != expected_indices
    ):
        raise CheckpointIntegrityError(
            "serialized optimizer parameter order is incompatible"
        )
    numeric = ("lr", "eps", "weight_decay", "initial_lr")
    if any(type(group[name]) is not float for name in numeric):
        raise CheckpointIntegrityError(
            "serialized optimizer scalar options must be binary64 floats"
        )
    if (
        type(group["betas"]) is not tuple
        or len(group["betas"]) != 2
        or any(type(value) is not float for value in group["betas"])
    ):
        raise CheckpointIntegrityError(
            "serialized optimizer betas must be a pair of binary64 floats"
        )
    expected_boolean = {
        "amsgrad": False,
        "maximize": False,
        "foreach": False,
        "capturable": False,
        "differentiable": False,
        "fused": False,
        "decoupled_weight_decay": True,
    }
    if any(
        type(group[name]) is not bool or group[name] is not expected
        for name, expected in expected_boolean.items()
    ):
        raise CheckpointIntegrityError(
            "serialized optimizer boolean options are incompatible"
        )
    if type(states) is not dict:
        raise CheckpointIntegrityError("serialized optimizer state must be a mapping")
    expected_state_indices = set() if training_step == 0 else set(expected_indices)
    if set(states) != expected_state_indices or any(
        type(index) is not int for index in states
    ):
        raise CheckpointIntegrityError(
            "serialized optimizer state does not match the ordered parameters"
        )
    for index, parameter in enumerate(parameters):
        if training_step == 0:
            break
        item = states[index]
        if type(item) is not dict or set(item) != {
            "step",
            "exp_avg",
            "exp_avg_sq",
        }:
            raise CheckpointIntegrityError(
                "serialized AdamW state has missing or unknown fields"
            )
        step_value = item["step"]
        if (
            type(step_value) is not torch.Tensor
            or step_value.device.type != "cpu"
            or step_value.dtype != torch.float32
            or step_value.layout != torch.strided
            or step_value.ndim != 0
            or float(step_value.item()) != float(training_step)
        ):
            raise CheckpointIntegrityError(
                "serialized AdamW step counter is incompatible"
            )
        for state_name in ("exp_avg", "exp_avg_sq"):
            moment = item[state_name]
            if (
                type(moment) is not torch.Tensor
                or moment.device.type != "cpu"
                or moment.dtype != parameter.dtype
                or moment.layout != torch.strided
                or tuple(moment.shape) != tuple(parameter.shape)
                or bool(torch.any(~torch.isfinite(moment)).item())
            ):
                raise CheckpointIntegrityError(
                    "serialized AdamW {} is incompatible with parameter {!r}".format(
                        state_name, index
                    )
                )
        if bool(torch.any(item["exp_avg_sq"] < 0.0).item()):
            raise CheckpointIntegrityError(
                "serialized AdamW second moment cannot be negative"
            )

    expected_scheduler_keys = {
        "step_size",
        "gamma",
        "base_lrs",
        "last_epoch",
        "_step_count",
        "_is_initial",
        "_get_lr_called_within_step",
        "_last_lr",
    }
    if type(scheduler_state) is not dict or set(scheduler_state) != expected_scheduler_keys:
        raise CheckpointIntegrityError(
            "serialized scheduler has missing or unknown fields"
        )
    if (
        type(scheduler_state["step_size"]) is not int
        or scheduler_state["step_size"] != config.scheduler_step_size
        or type(scheduler_state["gamma"]) is not float
        or scheduler_state["gamma"] != config.scheduler_gamma
        or type(scheduler_state["base_lrs"]) is not list
        or scheduler_state["base_lrs"] != [config.learning_rate]
        or type(scheduler_state["last_epoch"]) is not int
        or scheduler_state["last_epoch"] != training_step
        or type(scheduler_state["_step_count"]) is not int
        or scheduler_state["_step_count"] != training_step + 1
        or type(scheduler_state["_is_initial"]) is not bool
        or scheduler_state["_is_initial"]
        or type(scheduler_state["_get_lr_called_within_step"]) is not bool
        or scheduler_state["_get_lr_called_within_step"]
        or type(scheduler_state["_last_lr"]) is not list
        or scheduler_state["_last_lr"] != [group["lr"]]
    ):
        raise CheckpointIntegrityError("serialized scheduler state is incompatible")


def _payload_from_trainer(
    trainer: "DeterministicFixedGridTrainer",
    *,
    limits: CheckpointLimits,
) -> Dict[str, object]:
    trainer._validate_live_invariants()
    payload = {
        "payload_version": _PAYLOAD_VERSION,
        "torch_version": str(torch.__version__),
        "training_step": trainer.training_step,
        "config_json": trainer.config_json,
        "config_sha256": trainer.config_sha256,
        "schema_json": trainer.identity.schema_json,
        "schema_sha256": trainer.identity.schema_sha256,
        "provenance_json": trainer.identity.provenance_json,
        "provenance_sha256": trainer.identity.provenance_sha256,
        "model_state": dict(trainer.model.state_dict()),
        "model_parameter_names": tuple(
            name for name, _ in trainer.model.named_parameters()
        ),
        "optimizer_state": trainer.optimizer.state_dict(),
        "scheduler_state": trainer.scheduler.state_dict(),
        "cpu_rng_state": torch.get_rng_state(),
        "local_generator_state": trainer.local_generator.get_state(),
        "sampler_state": trainer.sampler.state_dict(),
    }
    return _safe_tree_clone(
        payload,
        limits=limits,
        budget=_TreeBudget(),
    )


def _serialize_payload(payload: Dict[str, object], limits: CheckpointLimits) -> bytes:
    buffer = io.BytesIO()
    try:
        torch.save(payload, buffer, _use_new_zipfile_serialization=True)
    except Exception as error:
        raise CheckpointError("Torch checkpoint serialization failed") from error
    raw = buffer.getvalue()
    if len(raw) > limits.max_file_bytes:
        raise CheckpointResourceError("serialized checkpoint exceeds max_file_bytes")
    _preflight_torch_archive(raw, limits)
    return raw


def _preflight_torch_archive(raw: bytes, limits: CheckpointLimits) -> None:
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw), mode="r")
    except (zipfile.BadZipFile, OSError) as error:
        raise CheckpointIntegrityError("Torch payload is not a valid ZIP archive") from error
    with archive:
        entries = archive.infolist()
        if not entries or len(entries) > limits.max_archive_entries:
            raise CheckpointResourceError("Torch archive entry-count guard exceeded")
        names = set()
        total = 0
        for entry in entries:
            name = entry.filename
            if (
                not isinstance(name, str)
                or "\x00" in name
                or name.startswith(("/", "\\"))
                or any(component in ("", ".", "..") for component in name.split("/"))
                or name in names
            ):
                raise CheckpointIntegrityError("Torch archive has an unsafe entry name")
            names.add(name)
            if entry.compress_type != zipfile.ZIP_STORED:
                raise CheckpointIntegrityError(
                    "compressed Torch archive entries are not accepted"
                )
            if entry.file_size != entry.compress_size:
                raise CheckpointIntegrityError("Torch archive size metadata is inconsistent")
            total += int(entry.file_size)
            if total > limits.max_file_bytes:
                raise CheckpointResourceError(
                    "Torch archive expanded-size guard exceeded"
                )


def _container_bytes(payload: bytes, limits: CheckpointLimits) -> bytes:
    header = {
        "container_version": _CONTAINER_VERSION,
        "payload_format": _PAYLOAD_FORMAT,
        "payload_length": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
    }
    header_bytes = canonical_json_dumps(header).encode("utf-8")
    if len(header_bytes) > limits.max_header_bytes:
        raise CheckpointResourceError("checkpoint header exceeds max_header_bytes")
    result = (
        _CONTAINER_MAGIC
        + struct.pack(">I", len(header_bytes))
        + header_bytes
        + payload
    )
    if len(result) > limits.max_file_bytes:
        raise CheckpointResourceError("checkpoint exceeds max_file_bytes")
    return result


def _fsync_directory_best_effort(directory: Path) -> None:
    descriptor = None
    try:
        descriptor = os.open(str(directory), os.O_RDONLY)
        os.fsync(descriptor)
    except OSError as error:
        unsupported = {
            errno.EBADF,
            errno.EINVAL,
            getattr(errno, "ENOTSUP", errno.EINVAL),
            getattr(errno, "EOPNOTSUPP", errno.EINVAL),
        }
        if error.errno not in unsupported:
            # Replacement is already atomic and complete.  Raising here would
            # falsely tell the caller that the old file is still present.
            return
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _atomic_write(path: PathLike, data: bytes) -> None:
    target = Path(path)
    if not target.name:
        raise ValueError("checkpoint path must name a file")
    parent = target.parent if str(target.parent) else Path(".")
    try:
        parent_status = parent.lstat()
    except FileNotFoundError as error:
        raise FileNotFoundError("checkpoint parent directory does not exist") from error
    if stat.S_ISLNK(parent_status.st_mode) or not stat.S_ISDIR(parent_status.st_mode):
        raise ValueError("checkpoint parent must be a non-symlink directory")
    if target.exists() or target.is_symlink():
        target_status = target.lstat()
        if stat.S_ISLNK(target_status.st_mode) or not stat.S_ISREG(target_status.st_mode):
            raise ValueError("existing checkpoint target must be a regular file")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".{}-".format(target.name),
        suffix=".tmp",
        dir=str(parent),
    )
    temporary = Path(temporary_name)
    try:
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(str(temporary), str(target))
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        _fsync_directory_best_effort(parent)
    except Exception:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _stat_signature(status: os.stat_result) -> Tuple[int, int, int, int, int, int]:
    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _read_regular_file(path: PathLike, limits: CheckpointLimits) -> bytes:
    target = Path(path)
    try:
        before = target.lstat()
    except FileNotFoundError as error:
        raise FileNotFoundError("checkpoint does not exist: {}".format(target)) from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise CheckpointIntegrityError("checkpoint must be a non-symlink regular file")
    if before.st_size > limits.max_file_bytes:
        raise CheckpointResourceError("checkpoint exceeds max_file_bytes")
    with target.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        if _stat_signature(opened) != _stat_signature(before):
            raise CheckpointIntegrityError("checkpoint changed while opening")
        data = handle.read(limits.max_file_bytes + 1)
        after = os.fstat(handle.fileno())
    if len(data) > limits.max_file_bytes:
        raise CheckpointResourceError("checkpoint exceeds max_file_bytes")
    if _stat_signature(after) != _stat_signature(before) or len(data) != before.st_size:
        raise CheckpointIntegrityError("checkpoint changed while reading")
    try:
        path_after = target.lstat()
    except FileNotFoundError as error:
        raise CheckpointIntegrityError("checkpoint disappeared while reading") from error
    if _stat_signature(path_after) != _stat_signature(after):
        raise CheckpointIntegrityError("checkpoint changed after reading")
    return data


def _decode_container(
    data: bytes,
    *,
    expected_sha256: str,
    limits: CheckpointLimits,
) -> bytes:
    expected = _sha256(expected_sha256, name="expected checkpoint digest")
    actual = hashlib.sha256(data).hexdigest()
    if not hmac.compare_digest(actual, expected):
        raise CheckpointIntegrityError("checkpoint SHA-256 does not match expected digest")
    minimum = len(_CONTAINER_MAGIC) + _HEADER_LENGTH_BYTES
    if len(data) < minimum or data[: len(_CONTAINER_MAGIC)] != _CONTAINER_MAGIC:
        raise CheckpointIntegrityError("checkpoint magic is missing or truncated")
    header_length = struct.unpack(
        ">I", data[len(_CONTAINER_MAGIC) : minimum]
    )[0]
    if header_length == 0 or header_length > limits.max_header_bytes:
        raise CheckpointResourceError("checkpoint header length is outside its guard")
    header_end = minimum + header_length
    if header_end > len(data):
        raise CheckpointIntegrityError("checkpoint header is truncated")
    try:
        header_text = data[minimum:header_end].decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise CheckpointIntegrityError("checkpoint header is not UTF-8") from error
    header = _strict_json_loads(header_text, name="checkpoint header")
    if type(header) is not dict:
        raise CheckpointIntegrityError("checkpoint header root must be a mapping")
    expected_keys = {
        "container_version",
        "payload_format",
        "payload_length",
        "payload_sha256",
    }
    if set(header) != expected_keys:
        raise CheckpointIntegrityError("checkpoint header has missing or unknown fields")
    try:
        canonical_header = canonical_json_dumps(header)
    except (TypeError, ValueError) as error:
        raise CheckpointIntegrityError("checkpoint header is outside canonical JSON") from error
    if canonical_header != header_text:
        raise CheckpointIntegrityError("checkpoint header is not canonical JSON")
    if header["container_version"] != _CONTAINER_VERSION:
        raise CheckpointIntegrityError("unsupported checkpoint container version")
    if header["payload_format"] != _PAYLOAD_FORMAT:
        raise CheckpointIntegrityError("unsupported checkpoint payload format")
    payload_length = header["payload_length"]
    if isinstance(payload_length, bool) or not isinstance(payload_length, int):
        raise CheckpointIntegrityError("checkpoint payload length must be an integer")
    payload = data[header_end:]
    if payload_length != len(payload):
        raise CheckpointIntegrityError("checkpoint payload is truncated or has trailing data")
    payload_digest = _sha256(header["payload_sha256"], name="payload digest")
    if not hmac.compare_digest(hashlib.sha256(payload).hexdigest(), payload_digest):
        raise CheckpointIntegrityError("checkpoint payload checksum mismatch")
    _preflight_torch_archive(payload, limits)
    return payload


def _load_weights_only(payload: bytes, limits: CheckpointLimits) -> Dict[str, object]:
    try:
        value = torch.load(
            io.BytesIO(payload),
            map_location="cpu",
            weights_only=True,
        )
    except Exception as error:
        raise CheckpointIntegrityError(
            "restricted weights-only checkpoint decoding failed"
        ) from error
    safe_value = _safe_tree_clone(
        value,
        limits=limits,
        budget=_TreeBudget(),
    )
    if type(safe_value) is not dict:
        raise CheckpointIntegrityError("checkpoint payload root must be a plain mapping")
    return safe_value


def _validate_payload_metadata(
    payload: Dict[str, object],
    *,
    trainer: "DeterministicFixedGridTrainer",
) -> int:
    expected_keys = {
        "payload_version",
        "torch_version",
        "training_step",
        "config_json",
        "config_sha256",
        "schema_json",
        "schema_sha256",
        "provenance_json",
        "provenance_sha256",
        "model_state",
        "model_parameter_names",
        "optimizer_state",
        "scheduler_state",
        "cpu_rng_state",
        "local_generator_state",
        "sampler_state",
    }
    if set(payload) != expected_keys:
        raise CheckpointIntegrityError("checkpoint payload has missing or unknown fields")
    if payload["payload_version"] != _PAYLOAD_VERSION:
        raise CheckpointIntegrityError("unsupported checkpoint payload version")
    if payload["torch_version"] != str(torch.__version__):
        raise CheckpointMismatchError(
            "checkpoint PyTorch version does not match the running environment"
        )
    step = _plain_int(
        payload["training_step"],
        name="training_step",
        minimum=0,
        maximum=trainer.training_config.max_training_steps,
    )
    _validated_canonical_mapping(
        payload["config_json"], payload["config_sha256"], name="configuration JSON"
    )
    if (
        payload["config_json"] != trainer.config_json
        or payload["config_sha256"] != trainer.config_sha256
    ):
        raise CheckpointMismatchError("checkpoint configuration mismatch")
    _validated_canonical_mapping(
        payload["schema_json"], payload["schema_sha256"], name="schema JSON"
    )
    _validated_canonical_mapping(
        payload["provenance_json"],
        payload["provenance_sha256"],
        name="provenance JSON",
    )
    if (
        payload["schema_json"] != trainer.identity.schema_json
        or payload["schema_sha256"] != trainer.identity.schema_sha256
    ):
        raise CheckpointMismatchError("checkpoint schema mismatch")
    if (
        payload["provenance_json"] != trainer.identity.provenance_json
        or payload["provenance_sha256"] != trainer.identity.provenance_sha256
    ):
        raise CheckpointMismatchError("checkpoint provenance mismatch")
    if type(payload["model_state"]) is not dict:
        raise CheckpointIntegrityError("model state must be a plain mapping")
    expected_model_state = trainer.model.state_dict()
    if set(payload["model_state"]) != set(expected_model_state):
        raise CheckpointIntegrityError("model state has missing or unknown fields")
    for name, expected_tensor in expected_model_state.items():
        value = payload["model_state"][name]
        if (
            type(value) is not torch.Tensor
            or value.device.type != "cpu"
            or value.layout != torch.strided
            or value.dtype != expected_tensor.dtype
            or tuple(value.shape) != tuple(expected_tensor.shape)
        ):
            raise CheckpointIntegrityError(
                "model state tensor {!r} is incompatible".format(name)
            )
    expected_parameter_names = tuple(
        name for name, _ in trainer.model.named_parameters()
    )
    if (
        type(payload["model_parameter_names"]) is not tuple
        or payload["model_parameter_names"] != expected_parameter_names
    ):
        raise CheckpointMismatchError(
            "checkpoint ordered model-parameter mapping mismatch"
        )
    if type(payload["optimizer_state"]) is not dict:
        raise CheckpointIntegrityError("optimizer state must be a plain mapping")
    if type(payload["scheduler_state"]) is not dict:
        raise CheckpointIntegrityError("scheduler state must be a plain mapping")
    if type(payload["sampler_state"]) is not dict:
        raise CheckpointIntegrityError("sampler state must be a plain mapping")
    _validate_serialized_optimizer_scheduler_state(
        payload["optimizer_state"],
        payload["scheduler_state"],
        model=trainer.model,
        config=trainer.training_config,
        training_step=step,
    )
    _validated_generator_state(payload["cpu_rng_state"], name="CPU Torch RNG state")
    _validated_generator_state(
        payload["local_generator_state"], name="local generator state"
    )
    return step


class DeterministicFixedGridTrainer:
    """Bounded CPU float32 one-step trainer with exact resume state."""

    def __init__(
        self,
        model: FixedGridReferenceDenoiser,
        training_config: FixedGridTrainingConfig,
        identity: CheckpointIdentity,
    ) -> None:
        if not isinstance(model, FixedGridReferenceDenoiser):
            raise TypeError("model must be a FixedGridReferenceDenoiser")
        if not isinstance(training_config, FixedGridTrainingConfig):
            raise TypeError("training_config must be a FixedGridTrainingConfig")
        if not isinstance(identity, CheckpointIdentity):
            raise TypeError("identity must be a CheckpointIdentity")
        parameters = list(model.parameters())
        if not parameters:
            raise ValueError("model must contain parameters")
        if any(
            parameter.device.type != "cpu" or parameter.dtype != torch.float32
            for parameter in parameters
        ):
            raise ValueError("the deterministic trainer requires CPU float32 parameters")
        self.model = model
        self.training_config = training_config
        self.identity = identity
        self.optimizer = _make_optimizer(model, training_config)
        self.scheduler = _make_scheduler(self.optimizer, training_config)
        self.sampler = DeterministicPermutationSampler(
            training_config.dataset_size, training_config.sampler_seed
        )
        self.local_generator = torch.Generator(device="cpu")
        self.local_generator.manual_seed(training_config.local_generator_seed)
        self.training_step = 0
        self._has_restored_checkpoint = False
        self.config_json, self.config_sha256 = _canonical_run_config(
            model.config, training_config
        )
        self._validate_live_invariants()

    def _validate_live_invariants(self) -> None:
        step = _plain_int(
            self.training_step,
            name="training_step",
            minimum=0,
            maximum=self.training_config.max_training_steps,
        )
        sampler_state = self.sampler.state_dict()
        _validate_sampler_step_invariant(
            sampler_state, config=self.training_config, training_step=step
        )
        _validate_optimizer_scheduler_contract(
            self.optimizer,
            self.scheduler,
            config=self.training_config,
            training_step=step,
        )

    def train_next(self, pool: FixedGridTrainingBatch) -> TrainingStepResult:
        """Train on the next deterministic permutation slice.

        ``pool`` must have exactly ``training_config.dataset_size`` rows.  It is
        expected to have been created by the frozen Torch corruption bundle:
        categorical targets are clean x0 states and continuous targets are the
        sampled forward epsilon.  The model sees only the noisy-state fields.
        """

        if not isinstance(pool, FixedGridTrainingBatch):
            raise TypeError("pool must be a FixedGridTrainingBatch")
        if pool.num_samples != self.training_config.dataset_size:
            raise ValueError("training pool size does not match training configuration")
        if self.training_step >= self.training_config.max_training_steps:
            raise RuntimeError("max_training_steps reached")
        self._validate_live_invariants()

        # This bounded smoke path rolls all state back if validation, forward,
        # backward, optimizer, scheduler, or the postcondition fails.
        model_before = {
            key: value.detach().clone() for key, value in self.model.state_dict().items()
        }
        optimizer_before = _safe_tree_clone(
            self.optimizer.state_dict(), limits=CheckpointLimits(), budget=_TreeBudget()
        )
        scheduler_before = _safe_tree_clone(
            self.scheduler.state_dict(), limits=CheckpointLimits(), budget=_TreeBudget()
        )
        sampler_before = self.sampler.state_dict()
        cpu_rng_before = torch.get_rng_state().clone()
        local_rng_before = self.local_generator.get_state().clone()
        step_before = self.training_step
        training_mode_before = self.model.training
        try:
            indices = self.sampler.next_indices(self.training_config.batch_size)
            batch = pool.select(indices)
            self.model.train()
            self.optimizer.zero_grad(set_to_none=True)
            output = self.model(
                batch.discrete_noisy_state,
                batch.continuous_noisy_state,
                elapsed_time_input=batch.elapsed_time_input,
                diffusion_progress=batch.diffusion_progress,
                sequence_mask=batch.sequence_mask,
                discrete_observed_mask=batch.discrete_observed_mask,
                continuous_observed_mask=batch.continuous_observed_mask,
                elapsed_time_observed_mask=batch.elapsed_time_observed_mask,
            )
            loss = hybrid_denoising_loss(
                output,
                discrete_target=batch.discrete_target,
                continuous_target=batch.continuous_target,
                sequence_mask=batch.sequence_mask,
                discrete_loss_mask=batch.discrete_loss_mask,
                continuous_loss_mask=batch.continuous_loss_mask,
                categorical_weight=self.training_config.categorical_weight,
                continuous_weight=self.training_config.continuous_weight,
            )
            if not bool(torch.isfinite(loss.total.detach()).item()):
                raise FloatingPointError("training loss is non-finite")
            loss.total.backward()
            gradients = [parameter.grad for parameter in self.model.parameters()]
            if any(gradient is None for gradient in gradients):
                raise RuntimeError("a model parameter did not receive a gradient")
            if any(bool(torch.any(~torch.isfinite(gradient)).item()) for gradient in gradients):
                raise FloatingPointError("a model gradient is non-finite")
            if self.training_config.gradient_clip_norm is not None:
                norm = torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), self.training_config.gradient_clip_norm
                )
                if not bool(torch.isfinite(norm.detach()).item()):
                    raise FloatingPointError("gradient norm is non-finite")
            self.optimizer.step()
            self.scheduler.step()
            self.training_step += 1
            if any(
                bool(torch.any(~torch.isfinite(parameter.detach())).item())
                for parameter in self.model.parameters()
            ):
                raise FloatingPointError("optimizer produced a non-finite parameter")
            self._validate_live_invariants()
            return TrainingStepResult(
                completed_step=self.training_step,
                batch_indices=indices.clone(),
                total_loss=loss.total.detach().clone(),
                categorical_loss=loss.categorical.detach().clone(),
                continuous_loss=loss.continuous.detach().clone(),
            )
        except Exception:
            self.model.load_state_dict(model_before, strict=True)
            self.optimizer.load_state_dict(optimizer_before)
            self.scheduler.load_state_dict(scheduler_before)
            self.sampler.load_state_dict(sampler_before)
            self.local_generator.set_state(local_rng_before)
            torch.set_rng_state(cpu_rng_before)
            self.training_step = step_before
            self.model.train(training_mode_before)
            self.optimizer.zero_grad(set_to_none=True)
            raise

    def save_checkpoint(
        self,
        path: PathLike,
        *,
        limits: Optional[CheckpointLimits] = None,
    ) -> str:
        """Atomically publish a versioned checkpoint and return its SHA-256."""

        active_limits = CheckpointLimits() if limits is None else limits
        if not isinstance(active_limits, CheckpointLimits):
            raise TypeError("limits must be a CheckpointLimits")
        payload = _payload_from_trainer(self, limits=active_limits)
        serialized = _serialize_payload(payload, active_limits)
        container = _container_bytes(serialized, active_limits)
        digest = hashlib.sha256(container).hexdigest()
        _atomic_write(path, container)
        return digest

    def restore_checkpoint(
        self,
        path: PathLike,
        *,
        expected_sha256: str,
        limits: Optional[CheckpointLimits] = None,
        minimum_training_step: Optional[int] = None,
    ) -> int:
        """Validate completely, then restore state transactionally.

        ``minimum_training_step`` is an external monotonic watermark.  A
        checkpoint at or below it is treated as a replay.  Independently, a
        non-fresh trainer refuses to repeat or roll back its current step.
        """

        active_limits = CheckpointLimits() if limits is None else limits
        if not isinstance(active_limits, CheckpointLimits):
            raise TypeError("limits must be a CheckpointLimits")
        raw = _read_regular_file(path, active_limits)
        serialized = _decode_container(
            raw, expected_sha256=expected_sha256, limits=active_limits
        )
        payload = _load_weights_only(serialized, active_limits)
        step = _validate_payload_metadata(payload, trainer=self)
        if minimum_training_step is not None:
            watermark = _plain_int(
                minimum_training_step,
                name="minimum_training_step",
                minimum=0,
                maximum=self.training_config.max_training_steps,
            )
            if step <= watermark:
                raise CheckpointReplayError(
                    "checkpoint step does not exceed the external replay watermark"
                )
        if (
            self.training_step > 0 or self._has_restored_checkpoint
        ) and step <= self.training_step:
            raise CheckpointReplayError(
                "checkpoint would repeat or roll back the trainer's current step"
            )

        # Validate every state object against isolated probes before mutating
        # the live trainer.  fork_rng prevents probe construction from changing
        # global CPU RNG state.
        with torch.random.fork_rng(devices=[], enabled=True):
            probe_model = FixedGridReferenceDenoiser(self.model.config)
            try:
                probe_model.load_state_dict(payload["model_state"], strict=True)
            except (RuntimeError, ValueError, TypeError) as error:
                raise CheckpointIntegrityError("model state is incompatible") from error
            probe_optimizer = _make_optimizer(probe_model, self.training_config)
            try:
                probe_optimizer.load_state_dict(payload["optimizer_state"])
            except (RuntimeError, ValueError, TypeError, KeyError) as error:
                raise CheckpointIntegrityError("optimizer state is incompatible") from error
            probe_scheduler = _make_scheduler(probe_optimizer, self.training_config)
            try:
                probe_scheduler.load_state_dict(payload["scheduler_state"])
            except (RuntimeError, ValueError, TypeError, KeyError) as error:
                raise CheckpointIntegrityError("scheduler state is incompatible") from error
            _validate_optimizer_scheduler_contract(
                probe_optimizer,
                probe_scheduler,
                config=self.training_config,
                training_step=step,
            )
            probe_sampler = DeterministicPermutationSampler(
                self.training_config.dataset_size, self.training_config.sampler_seed
            )
            probe_sampler.load_state_dict(payload["sampler_state"])
            _validate_sampler_step_invariant(
                probe_sampler.state_dict(),
                config=self.training_config,
                training_step=step,
            )
            probe_generator = torch.Generator(device="cpu")
            try:
                probe_generator.set_state(
                    _validated_generator_state(
                        payload["local_generator_state"],
                        name="local generator state",
                    )
                )
                cpu_probe = torch.Generator(device="cpu")
                cpu_probe.set_state(
                    _validated_generator_state(
                        payload["cpu_rng_state"], name="CPU Torch RNG state"
                    )
                )
            except RuntimeError as error:
                raise CheckpointIntegrityError("checkpoint RNG state is invalid") from error

        # The probes make failure here highly unlikely; snapshots provide a
        # final transactional rollback if the live application still raises.
        model_before = {
            key: value.detach().clone() for key, value in self.model.state_dict().items()
        }
        optimizer_before = _safe_tree_clone(
            self.optimizer.state_dict(), limits=active_limits, budget=_TreeBudget()
        )
        scheduler_before = _safe_tree_clone(
            self.scheduler.state_dict(), limits=active_limits, budget=_TreeBudget()
        )
        sampler_before = self.sampler.state_dict()
        local_before = self.local_generator.get_state().clone()
        cpu_before = torch.get_rng_state().clone()
        step_before = self.training_step
        restored_before = self._has_restored_checkpoint
        try:
            self.model.load_state_dict(payload["model_state"], strict=True)
            self.optimizer.load_state_dict(payload["optimizer_state"])
            self.scheduler.load_state_dict(payload["scheduler_state"])
            self.sampler.load_state_dict(payload["sampler_state"])
            self.local_generator.set_state(payload["local_generator_state"])
            self.training_step = step
            self._validate_live_invariants()
            # Global state is installed last so validation cannot consume it.
            torch.set_rng_state(payload["cpu_rng_state"])
            self._has_restored_checkpoint = True
        except Exception:
            self.model.load_state_dict(model_before, strict=True)
            self.optimizer.load_state_dict(optimizer_before)
            self.scheduler.load_state_dict(scheduler_before)
            self.sampler.load_state_dict(sampler_before)
            self.local_generator.set_state(local_before)
            self.training_step = step_before
            self._has_restored_checkpoint = restored_before
            torch.set_rng_state(cpu_before)
            raise
        return step


__all__ = [
    "CheckpointError",
    "CheckpointIdentity",
    "CheckpointIntegrityError",
    "CheckpointLimits",
    "CheckpointMismatchError",
    "CheckpointReplayError",
    "CheckpointResourceError",
    "DeterministicFixedGridTrainer",
    "DeterministicPermutationSampler",
    "FixedGridTrainingBatch",
    "FixedGridTrainingConfig",
    "TrainingStepResult",
]
