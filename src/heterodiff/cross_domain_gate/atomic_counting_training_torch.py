"""Deterministic bounded trainer and checkpoints for the atomic-counting gate.

This module executes only the wiring control preregistered in
``research/32_cross_domain_atomic_counting_reference_gate.md``.  It does not
implement a likelihood, ELBO, native configuration process, official-data
experiment, clinical result, or evidence bundle.  Checkpoints are private
restart artifacts whose identity is supplied by the caller; saving one does
not mark any gate as passed.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, fields
import hashlib
import hmac
import importlib.metadata as importlib_metadata
import io
import json
import math
from numbers import Integral, Real
import os
from pathlib import Path
import random
import resource
import stat
import struct
import sys
import tempfile
import time
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple, Union
import zipfile

import numpy as np

try:
    import torch
except ModuleNotFoundError as error:  # pragma: no cover - optional boundary
    if error.name == "torch":
        raise ModuleNotFoundError(
            "heterodiff.cross_domain_gate.atomic_counting_training_torch "
            "requires the pinned Torch extra"
        ) from error
    raise

from heterodiff.cross_domain_gate.atomic_counting_reference_torch import (
    AtomicCountingReferenceConfig,
    AtomicCountingReferenceFFN,
    AtomicCountingReferenceTarget,
    atomic_counting_hybrid_loss,
    corrupt_atomic_counting_reference,
)
from heterodiff.cross_domain_gate.counting_windows import (
    CountingDomainTaskSet,
    CountingTaskId,
)
from heterodiff.data.cross_domain_counting_fixtures import CountingFixtureDomain
from heterodiff.models.reference_training import DeterministicPermutationSampler


PathLike = Union[str, os.PathLike]

_CHECKPOINT_MAGIC = b"HACGCP1\x00"
_CHECKPOINT_CONTAINER_VERSION = 1
_CHECKPOINT_PAYLOAD_VERSION = 1
_CHECKPOINT_HEADER_BYTES = 4
_CHECKPOINT_FORMAT = "heterodiff-atomic-counting-checkpoint-v1"
_TRAINING_CONFIG_FORMAT = "heterodiff-atomic-counting-training-v1"
_BINDINGS_FORMAT = "heterodiff-atomic-counting-bindings-v1"
_TASK_BUNDLE_FORMAT = "heterodiff-atomic-counting-training-tasks-v1"
_GENESIS = "genesis"
_SHA256_ALPHABET = frozenset("0123456789abcdef")
_HARD_MAX_CHECKPOINT_BYTES = 64 * 1024 * 1024
_HARD_MAX_LOG_BYTES = 2 * 1024 * 1024
_HARD_MAX_OUTPUT_BYTES = 256 * 1024 * 1024
_HARD_MAX_RSS_BYTES = 2 * 1024 * 1024 * 1024
_HARD_MAX_RUNTIME_SECONDS = 120.0
_HARD_MAX_TREE_NODES = 50_000
_HARD_MAX_TENSOR_ELEMENTS = 20_000_000
ATOMIC_COUNTING_GATE_ID = (
    "heterodiff-cross-domain-atomic-counting-reference-gate-v1"
)
M_ACG_1_TASK_SEQUENCE = (1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0)
P_ACG_1_TASK_SEQUENCE = (0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1)
_PINNED_PYTHON_MAJOR_MINOR = (3, 11)
_PINNED_PYTHON_VERSION = "3.11.5"
_PINNED_PYTHON_EXECUTABLE_SHA256 = (
    "ff2d7180d4aa2dcc03193194c1999509239e00101ade54fcdd736d9fc25bd0c6"
)
_PINNED_PYTHON_EXECUTABLE_SIZE_BYTES = 152_624
_PINNED_TORCH_VERSION = "2.12.1"
_PINNED_NUMPY_VERSION = "2.4.6"
_PINNED_PLATFORM = "darwin"
_PINNED_MACHINE = "arm64"
_BOOTSTRAP_SCHEMA = "heterodiff-atomic-counting-source-bootstrap-v1"
_BOOTSTRAP_RELATIVE_PATH = (
    "src/heterodiff/cross_domain_gate/atomic_counting_bootstrap.py"
)
_BOOTSTRAP_ENVIRONMENT_FIELDS = {
    "bootstrap_sha256": "HETERODIFF_BOOTSTRAP_SHA256",
    "executable_sha256": "HETERODIFF_PYTHON_EXECUTABLE_SHA256",
    "executable_size_bytes": "HETERODIFF_PYTHON_EXECUTABLE_SIZE",
    "python_implementation": "HETERODIFF_PYTHON_IMPLEMENTATION",
    "python_version": "HETERODIFF_PYTHON_VERSION",
    "schema": "HETERODIFF_BOOTSTRAP_SCHEMA",
}
_PINNED_ENVIRONMENT = {
    "MKL_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
}
_RUNTIME_MANIFEST_FORMAT = "heterodiff-atomic-counting-pinned-runtime-v1"
_TASK_SEQUENCES_BY_DOMAIN = {
    CountingFixtureDomain.MUSIC: M_ACG_1_TASK_SEQUENCE,
    CountingFixtureDomain.CLINICAL_STYLE: P_ACG_1_TASK_SEQUENCE,
}

_REQUIRED_BINDING_KEYS = frozenset(
    {
        "schema",
        "task",
        "corruption",
        "model",
        "loss",
        "training_config",
        "source_fixture",
        "converted_state",
        "tensor",
        "split_group_policy",
        "train_transform",
        "code_source",
        "dependency_lock",
        "environment_manifest",
        "gate_id",
        "gate_spec",
    }
)


class AtomicCountingTrainingError(RuntimeError):
    """Base class for fail-closed gate-training errors."""


class AtomicCountingCheckpointError(AtomicCountingTrainingError):
    """Base class for checkpoint rejection."""


class AtomicCountingCheckpointIntegrityError(AtomicCountingCheckpointError):
    """A checkpoint is malformed, truncated, appended, or internally invalid."""


class AtomicCountingCheckpointMismatchError(AtomicCountingCheckpointError):
    """A valid checkpoint belongs to a different declared run."""


class AtomicCountingCheckpointReplayError(AtomicCountingCheckpointError):
    """A checkpoint would repeat or roll back an externally accepted step."""


class AtomicCountingResourceError(AtomicCountingTrainingError):
    """A static or dynamic preregistered resource ceiling was exceeded."""


class AtomicCountingRuntimeError(AtomicCountingTrainingError):
    """The process does not match the frozen local execution environment."""


def _plain_int(
    value: object, *, name: str, minimum: int, maximum: int
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
    value: object, *, name: str, minimum: float, maximum: float
) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("{} must be a real number".format(name))
    result = float(value)
    if not math.isfinite(result) or result < minimum or result > maximum:
        raise ValueError(
            "{} must be finite and lie in [{}, {}]".format(
                name, minimum, maximum
            )
        )
    return result


def _require_sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _SHA256_ALPHABET for character in value)
    ):
        raise ValueError("{} must be a lowercase SHA-256 digest".format(name))
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise TypeError("value is not canonical-JSON serializable") from error
    return text.encode("utf-8")


def _domain_digest(domain: str, value: object) -> str:
    payload = _canonical_json_bytes(value)
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


@dataclass(frozen=True)
class AtomicCountingResourceLimits:
    """Injectable ceilings; defaults are the frozen production limits."""

    checkpoint_bytes: int = _HARD_MAX_CHECKPOINT_BYTES
    log_bytes: int = _HARD_MAX_LOG_BYTES
    output_bytes: int = _HARD_MAX_OUTPUT_BYTES
    peak_rss_bytes: int = _HARD_MAX_RSS_BYTES
    runtime_seconds: float = _HARD_MAX_RUNTIME_SECONDS

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "checkpoint_bytes",
            _plain_int(
                self.checkpoint_bytes,
                name="checkpoint_bytes",
                minimum=1,
                maximum=_HARD_MAX_CHECKPOINT_BYTES,
            ),
        )
        object.__setattr__(
            self,
            "log_bytes",
            _plain_int(
                self.log_bytes,
                name="log_bytes",
                minimum=1,
                maximum=_HARD_MAX_LOG_BYTES,
            ),
        )
        object.__setattr__(
            self,
            "output_bytes",
            _plain_int(
                self.output_bytes,
                name="output_bytes",
                minimum=1,
                maximum=_HARD_MAX_OUTPUT_BYTES,
            ),
        )
        object.__setattr__(
            self,
            "peak_rss_bytes",
            _plain_int(
                self.peak_rss_bytes,
                name="peak_rss_bytes",
                minimum=1,
                maximum=_HARD_MAX_RSS_BYTES,
            ),
        )
        object.__setattr__(
            self,
            "runtime_seconds",
            _finite_real(
                self.runtime_seconds,
                name="runtime_seconds",
                minimum=1e-9,
                maximum=_HARD_MAX_RUNTIME_SECONDS,
            ),
        )


def _default_peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Darwin reports bytes; Linux and the other supported Unix smoke hosts
    # report KiB.  This is a guard, not a benchmark.
    return value if sys.platform == "darwin" else value * 1024


class AtomicCountingResourceMonitor:
    """Monotonic runtime/RSS guard with deterministic injectable probes."""

    def __init__(
        self,
        limits: AtomicCountingResourceLimits = AtomicCountingResourceLimits(),
        *,
        clock: Callable[[], float] = time.monotonic,
        rss_reader: Callable[[], int] = _default_peak_rss_bytes,
    ) -> None:
        if type(limits) is not AtomicCountingResourceLimits:
            raise TypeError("limits must be exact AtomicCountingResourceLimits")
        if not callable(clock) or not callable(rss_reader):
            raise TypeError("clock and rss_reader must be callable")
        self.limits = limits
        self._clock = clock
        self._rss_reader = rss_reader
        self._start = float(clock())
        if not math.isfinite(self._start):
            raise ValueError("clock returned a nonfinite start time")
        self.maximum_elapsed_seconds = 0.0
        self.maximum_rss_bytes = 0
        self.stages: list[str] = []
        self._stage_observations: list[Tuple[int, str, float, int]] = []

    def check(self, stage: str) -> None:
        if type(stage) is not str or not stage or len(stage) > 128:
            raise TypeError("resource stage must be a bounded nonempty string")
        now = float(self._clock())
        rss = int(self._rss_reader())
        elapsed = now - self._start
        if (
            not math.isfinite(now)
            or elapsed < self.maximum_elapsed_seconds
            or rss < 0
        ):
            raise AtomicCountingResourceError("resource probe returned invalid state")
        self.maximum_elapsed_seconds = max(self.maximum_elapsed_seconds, elapsed)
        self.maximum_rss_bytes = max(self.maximum_rss_bytes, rss)
        self.stages.append(stage)
        self._stage_observations.append(
            (
                len(self._stage_observations) + 1,
                stage,
                self.maximum_elapsed_seconds,
                self.maximum_rss_bytes,
            )
        )
        if elapsed > self.limits.runtime_seconds:
            raise AtomicCountingResourceError(
                "runtime ceiling exceeded after {}".format(stage)
            )
        if rss > self.limits.peak_rss_bytes:
            raise AtomicCountingResourceError(
                "peak-RSS ceiling exceeded after {}".format(stage)
            )

    def stage_observation_manifest(self) -> Tuple[Mapping[str, object], ...]:
        """Return detached cumulative observations in their exact check order."""

        return tuple(
            {
                "elapsed_seconds": elapsed,
                "peak_rss_bytes": peak_rss,
                "stage": stage,
                "stage_index": stage_index,
            }
            for stage_index, stage, elapsed, peak_rss in self._stage_observations
        )

    def check_checkpoint_size(self, size: int) -> None:
        if _plain_int(
            size,
            name="checkpoint size",
            minimum=0,
            maximum=2**63 - 1,
        ) > self.limits.checkpoint_bytes:
            raise AtomicCountingResourceError("checkpoint byte ceiling exceeded")

    def check_log_size(self, size: int) -> None:
        if _plain_int(
            size,
            name="log size",
            minimum=0,
            maximum=2**63 - 1,
        ) > self.limits.log_bytes:
            raise AtomicCountingResourceError("log byte ceiling exceeded")

    def check_output_size(self, size: int) -> None:
        if _plain_int(
            size,
            name="output size",
            minimum=0,
            maximum=2**63 - 1,
        ) > self.limits.output_bytes:
            raise AtomicCountingResourceError("output byte ceiling exceeded")


@dataclass(frozen=True)
class AtomicCountingTrainingConfig:
    """The exact domain-specific 12-step smoke configuration."""

    domain: CountingFixtureDomain
    model_seed: int
    task_seed: int
    corruption_seed: int
    maximum_steps: int = 12
    checkpoint_step: int = 5
    batch_size: int = 1
    worker_processes: int = 0
    learning_rate: float = 0.001
    beta_one: float = 0.9
    beta_two: float = 0.999
    adam_epsilon: float = 1e-8
    weight_decay: float = 0.0
    scheduler_step_size: int = 4
    scheduler_gamma: float = 0.9
    parameter_budget: int = 250_000

    def __post_init__(self) -> None:
        if type(self.domain) is not CountingFixtureDomain:
            raise TypeError("domain must be an exact CountingFixtureDomain")
        for name in ("model_seed", "task_seed", "corruption_seed"):
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
        frozen_integers = {
            "maximum_steps": (12, 12),
            "checkpoint_step": (5, 5),
            "batch_size": (1, 1),
            "worker_processes": (0, 0),
            "scheduler_step_size": (4, 4),
            "parameter_budget": (250_000, 250_000),
        }
        for name, (minimum, maximum) in frozen_integers.items():
            object.__setattr__(
                self,
                name,
                _plain_int(
                    getattr(self, name),
                    name=name,
                    minimum=minimum,
                    maximum=maximum,
                ),
            )
        exact_floats = {
            "learning_rate": 0.001,
            "beta_one": 0.9,
            "beta_two": 0.999,
            "adam_epsilon": 1e-8,
            "weight_decay": 0.0,
            "scheduler_gamma": 0.9,
        }
        for name, expected in exact_floats.items():
            value = getattr(self, name)
            if type(value) is not float or value != expected:
                raise ValueError("{} must equal {!r}".format(name, expected))
        expected_seeds = {
            CountingFixtureDomain.MUSIC: (3201, 3203, 3209),
            CountingFixtureDomain.CLINICAL_STYLE: (3301, 3303, 3309),
        }[self.domain]
        if (self.model_seed, self.task_seed, self.corruption_seed) != expected_seeds:
            raise ValueError("domain seeds differ from the preregistered literals")
        direct_generator = torch.Generator(device="cpu")
        direct_generator.manual_seed(self.task_seed)
        direct_sequence = tuple(
            task_index
            for _epoch in range(6)
            for task_index in torch.randperm(
                2, generator=direct_generator, device="cpu"
            ).tolist()
        )
        if direct_sequence != _TASK_SEQUENCES_BY_DOMAIN[self.domain]:
            raise RuntimeError(
                "pinned Torch randperm differs from the frozen task sequence"
            )

    def public_mapping(self) -> Mapping[str, object]:
        return {
            "adam_epsilon": self.adam_epsilon,
            "batch_size": self.batch_size,
            "betas": [self.beta_one, self.beta_two],
            "checkpoint_step": self.checkpoint_step,
            "corruption_seed": self.corruption_seed,
            "domain": self.domain.value,
            "foreach": False,
            "format": _TRAINING_CONFIG_FORMAT,
            "fused": False,
            "learning_rate": self.learning_rate,
            "maximum_steps": self.maximum_steps,
            "model_seed": self.model_seed,
            "parameter_budget": self.parameter_budget,
            "scheduler_gamma": self.scheduler_gamma,
            "scheduler_step_size": self.scheduler_step_size,
            "task_sequence": list(_TASK_SEQUENCES_BY_DOMAIN[self.domain]),
            "task_seed": self.task_seed,
            "weight_decay": self.weight_decay,
            "worker_processes": self.worker_processes,
        }

    @property
    def config_digest(self) -> str:
        return _domain_digest(
            "heterodiff.atomic-counting-training-config.v1",
            self.public_mapping(),
        )


M_ACG_1_TRAINING_CONFIG = AtomicCountingTrainingConfig(
    CountingFixtureDomain.MUSIC, 3201, 3203, 3209
)
P_ACG_1_TRAINING_CONFIG = AtomicCountingTrainingConfig(
    CountingFixtureDomain.CLINICAL_STYLE, 3301, 3303, 3309
)


def _require_training_config(
    value: object,
) -> AtomicCountingTrainingConfig:
    if type(value) is not AtomicCountingTrainingConfig:
        raise TypeError("training_config must be exact AtomicCountingTrainingConfig")
    rebuilt = AtomicCountingTrainingConfig(
        **{field.name: getattr(value, field.name) for field in fields(value)}
    )
    if rebuilt != value:
        raise ValueError("training_config is not in canonical validated state")
    return value


@dataclass(frozen=True)
class AtomicCountingCheckpointBindings:
    """Exact external content digests required by every checkpoint."""

    values: Tuple[Tuple[str, str], ...]

    def __post_init__(self) -> None:
        if type(self.values) is not tuple or any(
            type(item) is not tuple or len(item) != 2 for item in self.values
        ):
            raise TypeError("binding values must be an exact tuple of pairs")
        mapping: Dict[str, str] = {}
        for key, value in self.values:
            if type(key) is not str:
                raise TypeError("binding names must be exact strings")
            if key in mapping:
                raise ValueError("binding names must be unique")
            if key == "gate_id":
                if value != ATOMIC_COUNTING_GATE_ID:
                    raise ValueError("checkpoint gate_id differs from the frozen gate")
                mapping[key] = value
            else:
                mapping[key] = _require_sha256(
                    value, name="binding {}".format(key)
                )
        if frozenset(mapping) != _REQUIRED_BINDING_KEYS:
            raise ValueError("checkpoint bindings have missing or unknown fields")
        if tuple(sorted(mapping.items())) != self.values:
            raise ValueError("checkpoint bindings must be sorted by name")

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, str]
    ) -> "AtomicCountingCheckpointBindings":
        if type(value) is not dict:
            raise TypeError("bindings must be a plain dictionary")
        return cls(tuple(sorted(value.items())))

    def as_dict(self) -> Dict[str, str]:
        return dict(self.values)

    @property
    def digest(self) -> str:
        return _domain_digest(
            "heterodiff.atomic-counting-checkpoint-bindings.v1",
            {"format": _BINDINGS_FORMAT, "values": self.as_dict()},
        )


@dataclass(frozen=True)
class AtomicCountingTrainingTasks:
    """The narrow ID-free handoff from redacted task construction to Torch."""

    domain: CountingFixtureDomain
    targets: Tuple[AtomicCountingReferenceTarget, AtomicCountingReferenceTarget]
    task_ids: Tuple[str, str]
    task_set_digest: str
    target_state_digest: str
    schema_digest: str
    source_fixture_digest: str
    split_group_policy_digest: str

    def __post_init__(self) -> None:
        if type(self.domain) is not CountingFixtureDomain:
            raise TypeError("domain must be an exact CountingFixtureDomain")
        if type(self.targets) is not tuple or len(self.targets) != 2 or any(
            type(value) is not AtomicCountingReferenceTarget
            for value in self.targets
        ):
            raise TypeError("targets must be the exact two reference targets")
        if self.task_ids != ("U", "A"):
            raise ValueError("task ids must be ordered exactly as (U, A)")
        _require_sha256(self.task_set_digest, name="task_set_digest")
        _require_sha256(self.target_state_digest, name="target_state_digest")
        _require_sha256(self.schema_digest, name="schema_digest")
        _require_sha256(self.source_fixture_digest, name="source_fixture_digest")
        _require_sha256(
            self.split_group_policy_digest,
            name="split_group_policy_digest",
        )
        if self.targets[0].config != self.targets[1].config:
            raise ValueError("U and A target configs differ")
        if any(target.batch_size != 1 for target in self.targets):
            raise ValueError("the frozen task targets require batch size one")
        for target in self.targets:
            target._validate()
        for name in (
            "clean_count",
            "clean_presence",
            "transformed_mark",
            "structural_applicable",
            "source_observed",
            "valid_time",
        ):
            if not torch.equal(
                getattr(self.targets[0], name),
                getattr(self.targets[1], name),
            ):
                raise ValueError("U and A clean target states differ")
        if bool(torch.any(self.targets[0].anchor_count_observed).item()):
            raise ValueError("task U cannot contain an anchor")
        if bool(torch.any(self.targets[0].anchor_count != 0).item()):
            raise ValueError("task U anchor counts must be canonical zero")
        if int(self.targets[1].anchor_count_observed.sum().item()) != 1:
            raise ValueError("task A must contain exactly one anchor")
        anchored = self.targets[1].anchor_count_observed
        if bool(torch.any(self.targets[1].clean_count[anchored] != 1).item()):
            raise ValueError("task A anchor must select a clean count-one cell")

    @property
    def config(self) -> AtomicCountingReferenceConfig:
        return self.targets[0].config

    @property
    def bundle_digest(self) -> str:
        return _domain_digest(
            "heterodiff.atomic-counting-training-tasks.v1",
            {
                "domain": self.domain.value,
                "format": _TASK_BUNDLE_FORMAT,
                "model_config": list(self.config.shape_signature),
                "schema_digest": self.schema_digest,
                "source_fixture_digest": self.source_fixture_digest,
                "split_group_policy_digest": self.split_group_policy_digest,
                "target_state_digest": self.target_state_digest,
                "task_ids": list(self.task_ids),
                "task_set_digest": self.task_set_digest,
            },
        )


def adapt_counting_task_set(
    task_set: CountingDomainTaskSet,
) -> AtomicCountingTrainingTasks:
    """Consume only the finalized redacted rasters; never recreate redaction."""

    if type(task_set) is not CountingDomainTaskSet:
        raise TypeError("task_set must be an exact CountingDomainTaskSet")
    # Reconstructing the exact immutable task set re-runs its full boundary
    # validation without inventing an alternate task or observation path.
    validated = CountingDomainTaskSet(
        task_set.domain,
        task_set.fixture_id,
        task_set.source_sha256,
        task_set.source_split,
        task_set.source_sample_id,
        task_set.source_group_id,
        task_set.target,
        task_set.tasks,
    )
    targets = []
    for task in validated.tasks:
        if task.task_id not in (
            CountingTaskId.UNCONDITIONAL,
            CountingTaskId.ANCHORED,
        ):
            raise ValueError("unsupported task id")
        raster = task.raster
        target = AtomicCountingReferenceTarget.from_encoded_reference(
            validated.target,
            anchor_count=torch.from_numpy(
                np.array(raster.anchor_count, copy=True, order="C")
            ),
            anchor_count_observed=torch.from_numpy(
                np.array(raster.anchor_count_observed, copy=True, order="C")
            ),
            parameter_budget=250_000,
        )
        targets.append(target)
    return AtomicCountingTrainingTasks(
        domain=validated.domain,
        targets=(targets[0], targets[1]),
        task_ids=("U", "A"),
        task_set_digest=validated.task_set_digest,
        target_state_digest=validated.target.state_digest,
        schema_digest=validated.target.schema_digest,
        source_fixture_digest=validated.source_sha256,
        split_group_policy_digest=validated.policy_digest,
    )


def _model_config_mapping(
    config: AtomicCountingReferenceConfig,
) -> Mapping[str, object]:
    return {
        "continuous_presence_indices": list(config.continuous_presence_indices),
        "input_width": config.input_width,
        "number_of_continuous_coordinates": (
            config.number_of_continuous_coordinates
        ),
        "number_of_event_types": config.number_of_event_types,
        "number_of_presence_coordinates": config.number_of_presence_coordinates,
        "parameter_budget": config.parameter_budget,
        "parameter_count": config.estimated_parameter_count,
        "reference_positions": config.reference_positions,
        "slot_capacity": config.slot_capacity,
        "type_embedding_width": 8,
        "trunk_widths": [64, 32],
    }


def atomic_counting_target_tensor_digest(
    tasks: AtomicCountingTrainingTasks,
) -> str:
    """Bind the actual Torch target bytes independently of converted state.

    ``target_state_digest`` authenticates the lossless NumPy/reference
    serialization.  This digest is recomputed from the tensors handed to the
    trainer, including task-specific anchors, so a checkpoint cannot satisfy
    both bindings by copying one digest into two differently named fields.
    """

    if type(tasks) is not AtomicCountingTrainingTasks:
        raise TypeError("tasks must be exact AtomicCountingTrainingTasks")
    tensor_names = (
        "clean_count",
        "clean_presence",
        "transformed_mark",
        "structural_applicable",
        "source_observed",
        "valid_time",
        "anchor_count",
        "anchor_count_observed",
    )
    task_records = []
    for task_id, target in zip(tasks.task_ids, tasks.targets):
        target._validate()
        tensors = []
        for name in tensor_names:
            value = getattr(target, name)
            if type(value) is not torch.Tensor:
                raise TypeError("target tensor payload must be exact torch.Tensor")
            if value.device.type != "cpu" or value.layout != torch.strided:
                raise ValueError("target tensor payload must be dense CPU storage")
            contiguous = value.detach().clone().contiguous()
            tensors.append(
                {
                    "data_sha256": _sha256_bytes(
                        contiguous.numpy().tobytes(order="C")
                    ),
                    "dtype": str(contiguous.dtype).removeprefix("torch."),
                    "name": name,
                    "shape": list(contiguous.shape),
                }
            )
        task_records.append({"task_id": task_id, "tensors": tensors})
    return _domain_digest(
        "heterodiff.atomic-counting-target-tensor-payload.v1",
        {
            "format": "heterodiff-atomic-counting-target-tensor-payload-v1",
            "model_shape": list(tasks.config.shape_signature),
            "tasks": task_records,
        },
    )


def _derived_binding_values(
    tasks: AtomicCountingTrainingTasks,
    config: AtomicCountingTrainingConfig,
) -> Dict[str, str]:
    model_mapping = _model_config_mapping(tasks.config)
    corruption_mapping = {
        "alpha_bar": 0.8,
        "count_mask_probability": 0.5,
        "draw_order": ["U_count", "U_presence", "Z"],
        "full_shape": True,
        "model_shape": model_mapping,
        "presence_mask_probability": 0.5,
        "step": 1,
    }
    loss_mapping = {
        "continuous": "enabled-branch-mean-epsilon-mse",
        "count": "0.5-occupied-plus-0.5-empty-cross-entropy",
        "presence": "0.5-positive-plus-0.5-zero-cross-entropy",
        "weights": [1.0, 1.0, 1.0],
    }
    transform_mapping = {
        "fitted": False,
        "positive": "natural-log",
        "real": "identity",
    }
    return {
        "schema": tasks.schema_digest,
        "task": tasks.task_set_digest,
        "corruption": _domain_digest(
            "heterodiff.atomic-counting-corruption.v1", corruption_mapping
        ),
        "model": _domain_digest(
            "heterodiff.atomic-counting-model.v1", model_mapping
        ),
        "loss": _domain_digest(
            "heterodiff.atomic-counting-loss.v1", loss_mapping
        ),
        "training_config": config.config_digest,
        "source_fixture": tasks.source_fixture_digest,
        "converted_state": tasks.target_state_digest,
        "tensor": atomic_counting_target_tensor_digest(tasks),
        "split_group_policy": tasks.split_group_policy_digest,
        "train_transform": _domain_digest(
            "heterodiff.atomic-counting-transform.v1", transform_mapping
        ),
        "gate_id": ATOMIC_COUNTING_GATE_ID,
    }


def build_checkpoint_bindings(
    tasks: AtomicCountingTrainingTasks,
    config: AtomicCountingTrainingConfig,
    *,
    external_digests: Mapping[str, str],
) -> AtomicCountingCheckpointBindings:
    """Bind exact internal state plus caller-audited code/environment content."""

    if type(tasks) is not AtomicCountingTrainingTasks:
        raise TypeError("tasks must be exact AtomicCountingTrainingTasks")
    _require_training_config(config)
    if config.domain is not tasks.domain:
        raise ValueError("training config and task domain differ")
    if type(external_digests) is not dict or set(external_digests) != {
        "code_source",
        "dependency_lock",
        "environment_manifest",
        "gate_spec",
    }:
        raise ValueError(
            "external_digests must contain exactly code, lock, environment, and "
            "gate-spec bindings"
        )
    external = {
        key: _require_sha256(value, name=key)
        for key, value in external_digests.items()
    }
    values = {
        **_derived_binding_values(tasks, config),
        **external,
    }
    if values["converted_state"] == values["tensor"]:
        raise AtomicCountingTrainingError(
            "converted-state and Torch tensor bindings must be independent"
        )
    return AtomicCountingCheckpointBindings.from_mapping(values)


def _numpy_rng_equal(left: tuple, right: tuple) -> bool:
    return (
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def _clone_tensor_mapping(value: Mapping[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    return {key: item.detach().clone() for key, item in value.items()}


def _make_optimizer(
    model: AtomicCountingReferenceFFN,
    config: AtomicCountingTrainingConfig,
) -> torch.optim.AdamW:
    return torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        betas=(config.beta_one, config.beta_two),
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
    optimizer: torch.optim.AdamW,
    config: AtomicCountingTrainingConfig,
) -> torch.optim.lr_scheduler.StepLR:
    return torch.optim.lr_scheduler.StepLR(
        optimizer,
        step_size=config.scheduler_step_size,
        gamma=config.scheduler_gamma,
    )


def _expected_learning_rate(
    config: AtomicCountingTrainingConfig, step: int
) -> float:
    value = config.learning_rate
    for _ in range(step // config.scheduler_step_size):
        value *= config.scheduler_gamma
    return value


@dataclass(frozen=True)
class AtomicCountingTrainingStep:
    """One exact completed-step record without gradients or provenance."""

    completed_step: int
    task_index: int
    task_id: str
    total_loss: torch.Tensor
    count_loss: torch.Tensor
    presence_loss: torch.Tensor
    continuous_loss: torch.Tensor
    occupied_count: int
    empty_count: int
    present_count: int
    absent_count: int
    continuous_count: int

    def __post_init__(self) -> None:
        _plain_int(
            self.completed_step,
            name="completed_step",
            minimum=1,
            maximum=12,
        )
        _plain_int(
            self.task_index, name="task_index", minimum=0, maximum=1
        )
        if self.task_id not in ("U", "A"):
            raise ValueError("task_id must be U or A")
        if self.task_id != ("U", "A")[self.task_index]:
            raise ValueError("task id and index disagree")
        for name in (
            "total_loss",
            "count_loss",
            "presence_loss",
            "continuous_loss",
        ):
            value = getattr(self, name)
            if (
                type(value) is not torch.Tensor
                or value.device.type != "cpu"
                or value.dtype != torch.float32
                or value.shape != torch.Size([])
                or value.requires_grad
                or not bool(torch.isfinite(value).item())
            ):
                raise ValueError("{} must be a finite detached CPU scalar".format(name))
        for name in (
            "occupied_count",
            "empty_count",
            "present_count",
            "absent_count",
            "continuous_count",
        ):
            _plain_int(
                getattr(self, name), name=name, minimum=0, maximum=20_000_000
            )


class AtomicCountingTrainer:
    """Transactional batch-one trainer for exactly the two tasks ``[U,A]``."""

    def __init__(
        self,
        tasks: AtomicCountingTrainingTasks,
        training_config: AtomicCountingTrainingConfig,
        bindings: AtomicCountingCheckpointBindings,
        model: AtomicCountingReferenceFFN,
        *,
        monitor: Optional[AtomicCountingResourceMonitor] = None,
    ) -> None:
        preflight_atomic_counting_pinned_runtime()
        if type(tasks) is not AtomicCountingTrainingTasks:
            raise TypeError("tasks must be exact AtomicCountingTrainingTasks")
        _require_training_config(training_config)
        if type(bindings) is not AtomicCountingCheckpointBindings:
            raise TypeError("bindings must be exact AtomicCountingCheckpointBindings")
        if type(model) is not AtomicCountingReferenceFFN:
            raise TypeError("model must be an exact AtomicCountingReferenceFFN")
        if tasks.domain is not training_config.domain:
            raise ValueError("task and trainer domains differ")
        if model.config != tasks.config:
            raise ValueError("task and model configs differ")
        if model.parameter_count != tasks.config.estimated_parameter_count:
            raise ValueError("model parameter count differs from static preflight")
        if model.parameter_count > training_config.parameter_budget:
            raise AtomicCountingResourceError("parameter ceiling exceeded")
        expected_bindings = bindings.as_dict()
        for name, value in _derived_binding_values(
            tasks, training_config
        ).items():
            if expected_bindings[name] != value:
                raise AtomicCountingCheckpointMismatchError(
                    "{} binding disagrees with trainer".format(name)
                )
        if monitor is None:
            monitor = AtomicCountingResourceMonitor()
        if type(monitor) is not AtomicCountingResourceMonitor:
            raise TypeError("monitor must be exact AtomicCountingResourceMonitor")

        self.tasks = tasks
        self.training_config = training_config
        self.bindings = bindings
        self.model = model
        self.monitor = monitor
        self.optimizer = _make_optimizer(model, training_config)
        self.scheduler = _make_scheduler(self.optimizer, training_config)
        self.sampler = DeterministicPermutationSampler(2, training_config.task_seed)
        self.corruption_generator = torch.Generator(device="cpu")
        self.corruption_generator.manual_seed(training_config.corruption_seed)
        self.completed_step = 0
        self.parent_checkpoint_sha256 = _GENESIS
        self.last_restored_checkpoint_sha256: Optional[str] = None
        self.monitor.check("trainer-initialization")
        self._validate_live_state()

    def _validate_optimizer_scheduler(self) -> None:
        if type(self.optimizer) is not torch.optim.AdamW:
            raise AtomicCountingTrainingError("optimizer must remain exact AdamW")
        if type(self.scheduler) is not torch.optim.lr_scheduler.StepLR:
            raise AtomicCountingTrainingError("scheduler must remain exact StepLR")
        if len(self.optimizer.param_groups) != 1:
            raise AtomicCountingTrainingError("optimizer must have one parameter group")
        group = self.optimizer.param_groups[0]
        expected = {
            "lr": _expected_learning_rate(
                self.training_config, self.completed_step
            ),
            "betas": (
                self.training_config.beta_one,
                self.training_config.beta_two,
            ),
            "eps": self.training_config.adam_epsilon,
            "weight_decay": 0.0,
            "amsgrad": False,
            "maximize": False,
            "foreach": False,
            "capturable": False,
            "differentiable": False,
            "fused": False,
        }
        for key, value in expected.items():
            if group.get(key) != value:
                raise AtomicCountingTrainingError(
                    "optimizer field {} differs from frozen contract".format(key)
                )
        if self.scheduler.step_size != 4 or self.scheduler.gamma != 0.9:
            raise AtomicCountingTrainingError("scheduler configuration changed")
        if self.scheduler.last_epoch != self.completed_step:
            raise AtomicCountingTrainingError("scheduler and completed step differ")

    def _validate_sampler_against_step(self) -> None:
        probe = DeterministicPermutationSampler(2, self.training_config.task_seed)
        for _ in range(self.completed_step):
            probe.next_indices(1)
        actual = self.sampler.state_dict()
        expected = probe.state_dict()
        for key in actual:
            left = actual[key]
            right = expected[key]
            if type(left) is torch.Tensor:
                equal = type(right) is torch.Tensor and torch.equal(left, right)
            else:
                equal = left == right
            if not equal:
                raise AtomicCountingTrainingError(
                    "sampler field {} disagrees with completed step".format(key)
                )

    def _validate_live_state(self) -> None:
        _require_training_config(self.training_config)
        self.bindings.__post_init__()
        _plain_int(
            self.completed_step,
            name="completed_step",
            minimum=0,
            maximum=self.training_config.maximum_steps,
        )
        self.tasks.__post_init__()
        if self.model.config != self.tasks.config:
            raise AtomicCountingTrainingError("model config changed")
        for name, parameter in self.model.named_parameters():
            if parameter.device.type != "cpu" or parameter.dtype != torch.float32:
                raise AtomicCountingTrainingError(
                    "parameter {} is not CPU float32".format(name)
                )
            if not bool(torch.all(torch.isfinite(parameter)).item()):
                raise AtomicCountingTrainingError(
                    "parameter {} is nonfinite".format(name)
                )
        self._validate_optimizer_scheduler()
        self._validate_sampler_against_step()
        state = self.corruption_generator.get_state()
        _validate_generator_state(state, name="live corruption generator")
        if self.parent_checkpoint_sha256 != _GENESIS:
            _require_sha256(
                self.parent_checkpoint_sha256,
                name="parent_checkpoint_sha256",
            )

    def _rollback(
        self,
        *,
        model_state: Mapping[str, torch.Tensor],
        optimizer_state: dict,
        scheduler_state: dict,
        sampler_state: dict,
        corruption_state: torch.Tensor,
        global_state: torch.Tensor,
        python_state: tuple,
        numpy_state: tuple,
        completed_step: int,
        training_mode: bool,
    ) -> None:
        self.model.load_state_dict(model_state, strict=True)
        self.optimizer.load_state_dict(optimizer_state)
        self.scheduler.load_state_dict(scheduler_state)
        self.sampler.load_state_dict(sampler_state)
        self.corruption_generator.set_state(corruption_state)
        torch.random.set_rng_state(global_state)
        random.setstate(python_state)
        np.random.set_state(numpy_state)
        self.completed_step = completed_step
        self.model.train(training_mode)

    def train_next(self) -> AtomicCountingTrainingStep:
        preflight_atomic_counting_pinned_runtime()
        if self.completed_step >= self.training_config.maximum_steps:
            raise AtomicCountingTrainingError("maximum training steps reached")
        self._validate_live_state()
        model_before = _clone_tensor_mapping(self.model.state_dict())
        optimizer_before = copy.deepcopy(self.optimizer.state_dict())
        scheduler_before = copy.deepcopy(self.scheduler.state_dict())
        sampler_before = self.sampler.state_dict()
        corruption_before = self.corruption_generator.get_state().clone()
        global_before = torch.random.get_rng_state().clone()
        python_before = random.getstate()
        numpy_before = np.random.get_state()
        step_before = self.completed_step
        mode_before = self.model.training
        try:
            task_index_tensor = self.sampler.next_indices(1)
            task_index = int(task_index_tensor.item())
            expected_task_index = _TASK_SEQUENCES_BY_DOMAIN[
                self.training_config.domain
            ][self.completed_step]
            if task_index != expected_task_index:
                raise AtomicCountingTrainingError(
                    "task sampler differs from the frozen 12-step sequence"
                )
            target = self.tasks.targets[task_index]
            corrupted = corrupt_atomic_counting_reference(
                target, generator=self.corruption_generator
            )
            self.monitor.check("corruption-and-conversion")
            self.model.train(True)
            self.optimizer.zero_grad(set_to_none=True)
            output = self.model(corrupted.model_input)
            loss = atomic_counting_hybrid_loss(output, corrupted.loss_target)
            if not bool(torch.isfinite(loss.total.detach()).item()):
                raise FloatingPointError("training loss is nonfinite")
            self.monitor.check("forward")
            loss.total.backward()
            gradients = [
                parameter.grad
                for parameter in self.model.parameters()
                if parameter.grad is not None
            ]
            if not gradients or any(
                bool(torch.any(~torch.isfinite(gradient)).item())
                for gradient in gradients
            ):
                raise FloatingPointError("training gradients are absent or nonfinite")
            self.monitor.check("backward")
            self.optimizer.step()
            self.scheduler.step()
            self.completed_step += 1
            self.monitor.check("optimizer-and-scheduler")
            if random.getstate() != python_before:
                raise AtomicCountingTrainingError("Python global RNG was consumed")
            if not _numpy_rng_equal(np.random.get_state(), numpy_before):
                raise AtomicCountingTrainingError("NumPy global RNG was consumed")
            if not torch.equal(torch.random.get_rng_state(), global_before):
                raise AtomicCountingTrainingError("Torch global RNG was consumed")
            self._validate_live_state()
            return AtomicCountingTrainingStep(
                completed_step=self.completed_step,
                task_index=task_index,
                task_id=self.tasks.task_ids[task_index],
                total_loss=loss.total.detach().clone(),
                count_loss=loss.count.detach().clone(),
                presence_loss=loss.presence.detach().clone(),
                continuous_loss=loss.continuous.detach().clone(),
                occupied_count=loss.occupied_count,
                empty_count=loss.empty_count,
                present_count=loss.present_count,
                absent_count=loss.absent_count,
                continuous_count=loss.continuous_count,
            )
        except BaseException:
            self._rollback(
                model_state=model_before,
                optimizer_state=optimizer_before,
                scheduler_state=scheduler_before,
                sampler_state=sampler_before,
                corruption_state=corruption_before,
                global_state=global_before,
                python_state=python_before,
                numpy_state=numpy_before,
                completed_step=step_before,
                training_mode=mode_before,
            )
            raise

    def train_until(self, completed_step: int) -> Tuple[AtomicCountingTrainingStep, ...]:
        stop = _plain_int(
            completed_step,
            name="completed_step",
            minimum=self.completed_step,
            maximum=self.training_config.maximum_steps,
        )
        return tuple(self.train_next() for _ in range(self.completed_step, stop))


def build_atomic_counting_trainer(
    tasks: AtomicCountingTrainingTasks,
    config: AtomicCountingTrainingConfig,
    bindings: AtomicCountingCheckpointBindings,
    *,
    monitor: Optional[AtomicCountingResourceMonitor] = None,
) -> AtomicCountingTrainer:
    """Seed declared globals, construct the exact model, then freeze RNG use."""

    preflight_atomic_counting_pinned_runtime()
    if type(tasks) is not AtomicCountingTrainingTasks:
        raise TypeError("tasks must be exact AtomicCountingTrainingTasks")
    _require_training_config(config)
    if type(bindings) is not AtomicCountingCheckpointBindings:
        raise TypeError("bindings must be exact AtomicCountingCheckpointBindings")
    if tasks.domain is not config.domain:
        raise ValueError("task and trainer domains differ")
    random.seed(config.model_seed)
    np.random.seed(config.model_seed)
    torch.manual_seed(config.model_seed)
    initialization_generator = torch.Generator(device="cpu")
    initialization_generator.manual_seed(config.model_seed)
    model = AtomicCountingReferenceFFN(
        tasks.config,
        initialization_generator=initialization_generator,
    )
    trainer = AtomicCountingTrainer(
        tasks, config, bindings, model, monitor=monitor
    )
    return trainer


def _validate_generator_state(value: object, *, name: str) -> torch.Tensor:
    if (
        type(value) is not torch.Tensor
        or value.device.type != "cpu"
        or value.dtype != torch.uint8
        or value.layout != torch.strided
        or value.ndim != 1
        or value.numel() == 0
        or value.numel() > 1_000_000
    ):
        raise AtomicCountingCheckpointIntegrityError(
            "{} must be a bounded dense CPU uint8 vector".format(name)
        )
    probe = torch.Generator(device="cpu")
    try:
        probe.set_state(value.detach().clone())
    except RuntimeError as error:
        raise AtomicCountingCheckpointIntegrityError(
            "{} is not a valid CPU generator state".format(name)
        ) from error
    return value.detach().clone()


@dataclass
class _TreeBudget:
    nodes: int = 0
    tensor_elements: int = 0
    tensor_bytes: int = 0


def _validate_safe_tree(
    value: object,
    *,
    budget: _TreeBudget,
    checkpoint_limit: int,
    path: str = "payload",
) -> None:
    budget.nodes += 1
    if budget.nodes > _HARD_MAX_TREE_NODES:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint object tree has too many nodes"
        )
    if value is None or type(value) in (bool, int, str):
        if type(value) is str and len(value.encode("utf-8")) > 1_000_000:
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint string is too large at {}".format(path)
            )
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint contains a nonfinite float at {}".format(path)
            )
        return
    if type(value) is torch.Tensor:
        if value.device.type != "cpu" or value.layout != torch.strided:
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint tensors must be dense CPU tensors"
            )
        if value.dtype not in (
            torch.bool,
            torch.uint8,
            torch.int64,
            torch.float32,
            torch.float64,
        ):
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint contains an unsupported tensor dtype"
            )
        if value.requires_grad:
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint tensors cannot require gradients"
            )
        elements = value.numel()
        tensor_bytes = elements * value.element_size()
        budget.tensor_elements += elements
        budget.tensor_bytes += tensor_bytes
        if elements > _HARD_MAX_TENSOR_ELEMENTS:
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint contains an individually oversized tensor"
            )
        if (
            budget.tensor_elements > 5 * _HARD_MAX_TENSOR_ELEMENTS
            or budget.tensor_bytes > checkpoint_limit
        ):
            raise AtomicCountingResourceError("checkpoint tensor budget exceeded")
        if value.is_floating_point() and bool(
            torch.any(~torch.isfinite(value)).item()
        ):
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint contains a nonfinite tensor"
            )
        return
    if type(value) in (list, tuple):
        if len(value) > _HARD_MAX_TREE_NODES:
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint sequence is too long"
            )
        for index, item in enumerate(value):
            _validate_safe_tree(
                item,
                budget=budget,
                checkpoint_limit=checkpoint_limit,
                path="{}[{}]".format(path, index),
            )
        return
    if type(value) is dict:
        if len(value) > _HARD_MAX_TREE_NODES:
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint mapping is too large"
            )
        for key, item in value.items():
            if type(key) not in (str, int):
                raise AtomicCountingCheckpointIntegrityError(
                    "checkpoint mapping keys must be exact strings or integers"
                )
            _validate_safe_tree(
                item,
                budget=budget,
                checkpoint_limit=checkpoint_limit,
                path="{}.{}".format(path, key),
            )
        return
    raise AtomicCountingCheckpointIntegrityError(
        "unsupported checkpoint object type at {}".format(path)
    )


def _checkpoint_payload(trainer: AtomicCountingTrainer) -> Dict[str, object]:
    model_mapping = _model_config_mapping(trainer.tasks.config)
    return {
        "format": _CHECKPOINT_FORMAT,
        "gate_id": ATOMIC_COUNTING_GATE_ID,
        "payload_version": _CHECKPOINT_PAYLOAD_VERSION,
        "completed_step": trainer.completed_step,
        "parent_checkpoint_sha256": trainer.parent_checkpoint_sha256,
        "bindings": trainer.bindings.as_dict(),
        "bindings_digest": trainer.bindings.digest,
        "training_config": dict(trainer.training_config.public_mapping()),
        "training_config_digest": trainer.training_config.config_digest,
        "model_config": dict(model_mapping),
        "model_config_digest": _domain_digest(
            "heterodiff.atomic-counting-model.v1", model_mapping
        ),
        "task_bundle_digest": trainer.tasks.bundle_digest,
        "model_state": {
            key: value.detach().clone()
            for key, value in trainer.model.state_dict().items()
        },
        "optimizer_state": copy.deepcopy(trainer.optimizer.state_dict()),
        "scheduler_state": copy.deepcopy(trainer.scheduler.state_dict()),
        "sampler_state": trainer.sampler.state_dict(),
        "corruption_generator_state": (
            trainer.corruption_generator.get_state().clone()
        ),
        "global_torch_rng_state": torch.random.get_rng_state().clone(),
    }


def _torch_payload_bytes(payload: Mapping[str, object]) -> bytes:
    stream = io.BytesIO()
    torch.save(dict(payload), stream)
    return stream.getvalue()


def _checkpoint_container(payload_bytes: bytes) -> bytes:
    header = {
        "container_version": _CHECKPOINT_CONTAINER_VERSION,
        "format": _CHECKPOINT_FORMAT,
        "payload_length": len(payload_bytes),
        "payload_sha256": _sha256_bytes(payload_bytes),
    }
    header_bytes = _canonical_json_bytes(header)
    if len(header_bytes) > 65_536:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint header exceeds its static ceiling"
        )
    return (
        _CHECKPOINT_MAGIC
        + struct.pack(">I", len(header_bytes))
        + header_bytes
        + payload_bytes
    )


def _atomic_publish_no_replace(path: PathLike, data: bytes) -> None:
    destination = Path(path)
    parent = destination.parent
    if not parent.exists() or not parent.is_dir() or parent.is_symlink():
        raise AtomicCountingCheckpointError(
            "checkpoint parent must be an existing non-symlink directory"
        )
    if os.path.lexists(destination):
        raise FileExistsError("checkpoint destination already exists")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".{}-".format(destination.name),
        suffix=".tmp",
        dir=str(parent),
    )
    temporary = Path(temporary_name)
    published = False
    try:
        os.fchmod(descriptor, 0o600)
        view = memoryview(data)
        offset = 0
        while offset < len(view):
            written = os.write(descriptor, view[offset:])
            if written <= 0:
                raise OSError("checkpoint temporary write made no progress")
            offset += written
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        # A same-filesystem hard link publishes a fully fsynced inode and fails
        # atomically if the destination appeared concurrently.
        os.link(temporary, destination)
        published = True
        directory_descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except BaseException:
        if published:
            try:
                temporary_stat = temporary.stat()
                destination_stat = destination.stat()
                if (
                    temporary_stat.st_dev == destination_stat.st_dev
                    and temporary_stat.st_ino == destination_stat.st_ino
                ):
                    destination.unlink()
            except FileNotFoundError:
                pass
        raise
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def save_atomic_counting_checkpoint(
    trainer: AtomicCountingTrainer,
    path: PathLike,
) -> str:
    """Atomically publish the unique step-five checkpoint without replacement."""

    preflight_atomic_counting_pinned_runtime()
    if type(trainer) is not AtomicCountingTrainer:
        raise TypeError("trainer must be an exact AtomicCountingTrainer")
    trainer._validate_live_state()
    if trainer.completed_step != trainer.training_config.checkpoint_step:
        raise AtomicCountingCheckpointError(
            "the frozen gate checkpoint is permitted only after step five"
        )
    if trainer.parent_checkpoint_sha256 != _GENESIS:
        raise AtomicCountingCheckpointReplayError(
            "the single gate checkpoint must have a genesis parent"
        )
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    global_before = torch.random.get_rng_state().clone()
    trainer.monitor.check("checkpoint-save-preflight")
    payload = _checkpoint_payload(trainer)
    _validate_safe_tree(
        payload,
        budget=_TreeBudget(),
        checkpoint_limit=trainer.monitor.limits.checkpoint_bytes,
    )
    container = _checkpoint_container(_torch_payload_bytes(payload))
    trainer.monitor.check_checkpoint_size(len(container))
    trainer.monitor.check("checkpoint-serialization")
    if random.getstate() != python_before:
        random.setstate(python_before)
        raise AtomicCountingTrainingError("checkpoint save consumed Python RNG")
    if not _numpy_rng_equal(np.random.get_state(), numpy_before):
        np.random.set_state(numpy_before)
        raise AtomicCountingTrainingError("checkpoint save consumed NumPy RNG")
    if not torch.equal(torch.random.get_rng_state(), global_before):
        torch.random.set_rng_state(global_before)
        raise AtomicCountingTrainingError("checkpoint save consumed global Torch RNG")
    _atomic_publish_no_replace(path, container)
    try:
        trainer.monitor.check("checkpoint-save")
        if random.getstate() != python_before:
            raise AtomicCountingTrainingError(
                "checkpoint publication consumed Python RNG"
            )
        if not _numpy_rng_equal(np.random.get_state(), numpy_before):
            raise AtomicCountingTrainingError(
                "checkpoint publication consumed NumPy RNG"
            )
        if not torch.equal(torch.random.get_rng_state(), global_before):
            raise AtomicCountingTrainingError(
                "checkpoint publication consumed global Torch RNG"
            )
    except BaseException:
        destination = Path(path)
        if destination.is_file() and _sha256_bytes(destination.read_bytes()) == _sha256_bytes(
            container
        ):
            destination.unlink()
        random.setstate(python_before)
        np.random.set_state(numpy_before)
        torch.random.set_rng_state(global_before)
        raise
    return _sha256_bytes(container)


def _read_bounded_regular_file(path: PathLike, maximum_bytes: int) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint cannot be opened as a regular file"
        ) from error
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint must be a regular file"
            )
        if metadata.st_size <= 0 or metadata.st_size > maximum_bytes:
            raise AtomicCountingResourceError("checkpoint byte ceiling exceeded")
        chunks = []
        remaining = metadata.st_size
        while remaining:
            chunk = os.read(descriptor, min(1_048_576, remaining))
            if not chunk:
                raise AtomicCountingCheckpointIntegrityError(
                    "checkpoint was truncated while reading"
                )
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint grew while reading"
            )
        result = b"".join(chunks)
        if len(result) != metadata.st_size:
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint length changed while reading"
            )
        return result
    finally:
        os.close(descriptor)


def _parse_checkpoint_container(data: bytes) -> bytes:
    prefix = len(_CHECKPOINT_MAGIC) + _CHECKPOINT_HEADER_BYTES
    if len(data) < prefix or data[: len(_CHECKPOINT_MAGIC)] != _CHECKPOINT_MAGIC:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint magic is missing or truncated"
        )
    header_length = struct.unpack(
        ">I", data[len(_CHECKPOINT_MAGIC) : prefix]
    )[0]
    if header_length <= 0 or header_length > 65_536:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint header length is invalid"
        )
    header_end = prefix + header_length
    if header_end > len(data):
        raise AtomicCountingCheckpointIntegrityError("checkpoint header is truncated")
    header_bytes = data[prefix:header_end]
    try:
        header = json.loads(header_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint header is not canonical JSON"
        ) from error
    if type(header) is not dict or set(header) != {
        "container_version",
        "format",
        "payload_length",
        "payload_sha256",
    }:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint header has missing or unknown fields"
        )
    if _canonical_json_bytes(header) != header_bytes:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint header is not canonical"
        )
    if (
        header["container_version"] != _CHECKPOINT_CONTAINER_VERSION
        or header["format"] != _CHECKPOINT_FORMAT
    ):
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint container version is unsupported"
        )
    payload_length = _plain_int(
        header["payload_length"],
        name="payload_length",
        minimum=1,
        maximum=_HARD_MAX_CHECKPOINT_BYTES,
    )
    if header_end + payload_length != len(data):
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint is truncated or has appended bytes"
        )
    expected_payload_digest = _require_sha256(
        header["payload_sha256"], name="payload_sha256"
    )
    payload = data[header_end:]
    if not hmac.compare_digest(_sha256_bytes(payload), expected_payload_digest):
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint payload digest mismatch"
        )
    return payload


def _preflight_torch_zip(payload: bytes, maximum_bytes: int) -> None:
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload), mode="r")
    except zipfile.BadZipFile as error:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint Torch payload is not a valid bounded archive"
        ) from error
    with archive:
        entries = archive.infolist()
        if not entries or len(entries) > 4096:
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint archive entry count is invalid"
            )
        total = 0
        for entry in entries:
            parts = Path(entry.filename).parts
            if (
                not parts
                or Path(entry.filename).is_absolute()
                or ".." in parts
                or entry.file_size < 0
                or entry.compress_size < 0
            ):
                raise AtomicCountingCheckpointIntegrityError(
                    "checkpoint archive contains an unsafe entry"
                )
            total += entry.file_size
            if entry.file_size > maximum_bytes or total > maximum_bytes:
                raise AtomicCountingResourceError(
                    "checkpoint expanded archive ceiling exceeded"
                )


def _decode_checkpoint_payload(payload: bytes, maximum_bytes: int) -> dict:
    _preflight_torch_zip(payload, maximum_bytes)
    try:
        value = torch.load(
            io.BytesIO(payload),
            map_location="cpu",
            weights_only=True,
        )
    except Exception as error:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint safe Torch payload could not be decoded"
        ) from error
    if type(value) is not dict:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint payload must be a plain dictionary"
        )
    _validate_safe_tree(
        value,
        budget=_TreeBudget(),
        checkpoint_limit=maximum_bytes,
    )
    return value


def _tree_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is torch.Tensor:
        return torch.equal(left, right)  # type: ignore[arg-type]
    if type(left) is dict:
        right_dict = right  # type: ignore[assignment]
        return list(left) == list(right_dict) and all(
            _tree_equal(left[key], right_dict[key]) for key in left
        )
    if type(left) in (list, tuple):
        return len(left) == len(right) and all(  # type: ignore[arg-type]
            _tree_equal(a, b) for a, b in zip(left, right)  # type: ignore[arg-type]
        )
    return left == right


def _expected_sampler_state(
    config: AtomicCountingTrainingConfig, step: int
) -> dict:
    sampler = DeterministicPermutationSampler(2, config.task_seed)
    for _ in range(step):
        sampler.next_indices(1)
    return sampler.state_dict()


def _expected_corruption_state(
    tasks: AtomicCountingTrainingTasks,
    config: AtomicCountingTrainingConfig,
    step: int,
) -> torch.Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(config.corruption_seed)
    model_config = tasks.config
    count_shape = (
        1,
        model_config.reference_positions,
        model_config.number_of_event_types,
    )
    presence_shape = count_shape + (
        model_config.slot_capacity,
        model_config.number_of_presence_coordinates,
    )
    continuous_shape = count_shape + (
        model_config.slot_capacity,
        model_config.number_of_continuous_coordinates,
    )
    for _ in range(step):
        torch.rand(
            count_shape,
            dtype=torch.float32,
            device="cpu",
            generator=generator,
        )
        torch.rand(
            presence_shape,
            dtype=torch.float32,
            device="cpu",
            generator=generator,
        )
        torch.randn(
            continuous_shape,
            dtype=torch.float32,
            device="cpu",
            generator=generator,
        )
    return generator.get_state().clone()


def _validate_probe_optimizer_scheduler(
    optimizer: torch.optim.AdamW,
    scheduler: torch.optim.lr_scheduler.StepLR,
    config: AtomicCountingTrainingConfig,
    step: int,
) -> None:
    if len(optimizer.param_groups) != 1:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint optimizer must contain one parameter group"
        )
    group = optimizer.param_groups[0]
    expected_lr = _expected_learning_rate(config, step)
    expected = {
        "lr": expected_lr,
        "betas": (config.beta_one, config.beta_two),
        "eps": config.adam_epsilon,
        "weight_decay": 0.0,
        "amsgrad": False,
        "maximize": False,
        "foreach": False,
        "capturable": False,
        "differentiable": False,
        "fused": False,
    }
    for key, value in expected.items():
        if group.get(key) != value:
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint optimizer field {} is incompatible".format(key)
            )
    if (
        scheduler.step_size != config.scheduler_step_size
        or scheduler.gamma != config.scheduler_gamma
        or scheduler.last_epoch != step
    ):
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint scheduler state is incompatible"
        )
    for state in optimizer.state.values():
        if type(state) is not dict:
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint optimizer parameter state is malformed"
            )
        if "step" in state:
            step_tensor = state["step"]
            if type(step_tensor) is not torch.Tensor or step_tensor.numel() != 1:
                raise AtomicCountingCheckpointIntegrityError(
                    "optimizer step counter is malformed"
                )
            value = float(step_tensor.item())
            if not value.is_integer() or value < 1 or value > step:
                raise AtomicCountingCheckpointIntegrityError(
                    "optimizer step counter exceeds completed step"
                )


def _validate_checkpoint_payload(
    payload: dict,
    trainer: AtomicCountingTrainer,
    *,
    minimum_step_exclusive: int,
    expected_parent_checkpoint_sha256: str,
) -> int:
    expected_keys = {
        "format",
        "gate_id",
        "payload_version",
        "completed_step",
        "parent_checkpoint_sha256",
        "bindings",
        "bindings_digest",
        "training_config",
        "training_config_digest",
        "model_config",
        "model_config_digest",
        "task_bundle_digest",
        "model_state",
        "optimizer_state",
        "scheduler_state",
        "sampler_state",
        "corruption_generator_state",
        "global_torch_rng_state",
    }
    if set(payload) != expected_keys:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint payload has missing or unknown fields"
        )
    if (
        payload["format"] != _CHECKPOINT_FORMAT
        or payload["payload_version"] != _CHECKPOINT_PAYLOAD_VERSION
    ):
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint payload version is unsupported"
        )
    if payload["gate_id"] != ATOMIC_COUNTING_GATE_ID:
        raise AtomicCountingCheckpointMismatchError(
            "checkpoint gate identifier differs"
        )
    step = _plain_int(
        payload["completed_step"],
        name="checkpoint completed_step",
        minimum=1,
        maximum=trainer.training_config.maximum_steps,
    )
    if step != trainer.training_config.checkpoint_step:
        raise AtomicCountingCheckpointMismatchError(
            "checkpoint is not the preregistered step-five artifact"
        )
    watermark = _plain_int(
        minimum_step_exclusive,
        name="minimum_step_exclusive",
        minimum=0,
        maximum=trainer.training_config.maximum_steps,
    )
    if step <= watermark:
        raise AtomicCountingCheckpointReplayError(
            "checkpoint is at or below the external step watermark"
        )
    if trainer.completed_step != 0 or trainer.last_restored_checkpoint_sha256 is not None:
        raise AtomicCountingCheckpointReplayError(
            "checkpoint restore requires a fresh zero-step trainer"
        )
    if expected_parent_checkpoint_sha256 != _GENESIS:
        _require_sha256(
            expected_parent_checkpoint_sha256,
            name="expected_parent_checkpoint_sha256",
        )
    if payload["parent_checkpoint_sha256"] != expected_parent_checkpoint_sha256:
        raise AtomicCountingCheckpointMismatchError(
            "checkpoint parent binding mismatch"
        )
    if type(payload["bindings"]) is not dict:
        raise AtomicCountingCheckpointIntegrityError("bindings must be a plain mapping")
    if (
        "gate_id" in payload["bindings"]
        and payload["bindings"]["gate_id"] != ATOMIC_COUNTING_GATE_ID
    ):
        raise AtomicCountingCheckpointMismatchError(
            "checkpoint binding gate identifier differs"
        )
    try:
        loaded_bindings = AtomicCountingCheckpointBindings.from_mapping(
            payload["bindings"]
        )
    except (TypeError, ValueError) as error:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint bindings are malformed"
        ) from error
    if (
        loaded_bindings != trainer.bindings
        or payload["bindings_digest"] != trainer.bindings.digest
    ):
        raise AtomicCountingCheckpointMismatchError(
            "checkpoint external content bindings differ"
        )
    if (
        payload["training_config"]
        != dict(trainer.training_config.public_mapping())
        or payload["training_config_digest"]
        != trainer.training_config.config_digest
    ):
        raise AtomicCountingCheckpointMismatchError(
            "checkpoint training configuration differs"
        )
    model_mapping = _model_config_mapping(trainer.tasks.config)
    if (
        payload["model_config"] != dict(model_mapping)
        or payload["model_config_digest"]
        != _domain_digest("heterodiff.atomic-counting-model.v1", model_mapping)
    ):
        raise AtomicCountingCheckpointMismatchError(
            "checkpoint model configuration differs"
        )
    if payload["task_bundle_digest"] != trainer.tasks.bundle_digest:
        raise AtomicCountingCheckpointMismatchError(
            "checkpoint task bundle differs"
        )

    model_state = payload["model_state"]
    if type(model_state) is not dict:
        raise AtomicCountingCheckpointIntegrityError(
            "model state must be a plain ordered mapping"
        )
    expected_model_state = trainer.model.state_dict()
    if list(model_state) != list(expected_model_state):
        raise AtomicCountingCheckpointMismatchError(
            "checkpoint ordered model parameter mapping differs"
        )
    for name, expected in expected_model_state.items():
        value = model_state[name]
        if (
            type(value) is not torch.Tensor
            or value.device.type != "cpu"
            or value.dtype != expected.dtype
            or tuple(value.shape) != tuple(expected.shape)
            or value.layout != torch.strided
        ):
            raise AtomicCountingCheckpointIntegrityError(
                "checkpoint model tensor {} is incompatible".format(name)
            )
    for key in ("optimizer_state", "scheduler_state", "sampler_state"):
        if type(payload[key]) is not dict:
            raise AtomicCountingCheckpointIntegrityError(
                "{} must be a plain mapping".format(key)
            )

    sampler_probe = DeterministicPermutationSampler(
        2, trainer.training_config.task_seed
    )
    try:
        sampler_probe.load_state_dict(payload["sampler_state"])
    except Exception as error:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint sampler state is incompatible"
        ) from error
    if not _tree_equal(
        sampler_probe.state_dict(),
        _expected_sampler_state(trainer.training_config, step),
    ):
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint sampler state disagrees with completed step"
        )

    corruption_state = _validate_generator_state(
        payload["corruption_generator_state"],
        name="checkpoint corruption generator",
    )
    if not torch.equal(
        corruption_state,
        _expected_corruption_state(trainer.tasks, trainer.training_config, step),
    ):
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint corruption generator disagrees with completed step"
        )
    global_state = _validate_generator_state(
        payload["global_torch_rng_state"], name="checkpoint global Torch RNG"
    )
    expected_global_generator = torch.Generator(device="cpu")
    expected_global_generator.manual_seed(trainer.training_config.model_seed)
    if not torch.equal(global_state, expected_global_generator.get_state()):
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint global Torch RNG differs from the declared model seed"
        )

    probe_model = copy.deepcopy(trainer.model)
    try:
        probe_model.load_state_dict(model_state, strict=True)
        probe_optimizer = _make_optimizer(probe_model, trainer.training_config)
        probe_scheduler = _make_scheduler(
            probe_optimizer, trainer.training_config
        )
        probe_optimizer.load_state_dict(payload["optimizer_state"])
        probe_scheduler.load_state_dict(payload["scheduler_state"])
    except (RuntimeError, ValueError, TypeError, KeyError) as error:
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint optimizer or scheduler state is incompatible"
        ) from error
    _validate_probe_optimizer_scheduler(
        probe_optimizer, probe_scheduler, trainer.training_config, step
    )
    return step


def load_atomic_counting_checkpoint(
    trainer: AtomicCountingTrainer,
    path: PathLike,
    *,
    expected_sha256: str,
    minimum_step_exclusive: int,
    expected_parent_checkpoint_sha256: str = _GENESIS,
) -> int:
    """Validate every byte and state binding before transactional restoration."""

    preflight_atomic_counting_pinned_runtime()
    if type(trainer) is not AtomicCountingTrainer:
        raise TypeError("trainer must be an exact AtomicCountingTrainer")
    expected_digest = _require_sha256(
        expected_sha256, name="expected checkpoint SHA-256"
    )
    trainer._validate_live_state()
    python_before = random.getstate()
    numpy_before = np.random.get_state()
    global_before = torch.random.get_rng_state().clone()
    trainer.monitor.check("checkpoint-load-preflight")
    data = _read_bounded_regular_file(
        path, trainer.monitor.limits.checkpoint_bytes
    )
    trainer.monitor.check_checkpoint_size(len(data))
    if not hmac.compare_digest(_sha256_bytes(data), expected_digest):
        raise AtomicCountingCheckpointIntegrityError(
            "checkpoint external SHA-256 mismatch"
        )
    payload_bytes = _parse_checkpoint_container(data)
    payload = _decode_checkpoint_payload(
        payload_bytes, trainer.monitor.limits.checkpoint_bytes
    )
    step = _validate_checkpoint_payload(
        payload,
        trainer,
        minimum_step_exclusive=minimum_step_exclusive,
        expected_parent_checkpoint_sha256=expected_parent_checkpoint_sha256,
    )
    trainer.monitor.check("checkpoint-validation")
    if random.getstate() != python_before:
        random.setstate(python_before)
        raise AtomicCountingTrainingError("checkpoint load consumed Python RNG")
    if not _numpy_rng_equal(np.random.get_state(), numpy_before):
        np.random.set_state(numpy_before)
        raise AtomicCountingTrainingError("checkpoint load consumed NumPy RNG")
    if not torch.equal(torch.random.get_rng_state(), global_before):
        torch.random.set_rng_state(global_before)
        raise AtomicCountingTrainingError(
            "checkpoint validation consumed global Torch RNG"
        )

    model_before = _clone_tensor_mapping(trainer.model.state_dict())
    optimizer_before = copy.deepcopy(trainer.optimizer.state_dict())
    scheduler_before = copy.deepcopy(trainer.scheduler.state_dict())
    sampler_before = trainer.sampler.state_dict()
    corruption_before = trainer.corruption_generator.get_state().clone()
    completed_before = trainer.completed_step
    parent_before = trainer.parent_checkpoint_sha256
    restored_before = trainer.last_restored_checkpoint_sha256
    mode_before = trainer.model.training
    try:
        trainer.model.load_state_dict(payload["model_state"], strict=True)
        trainer.optimizer.load_state_dict(payload["optimizer_state"])
        trainer.scheduler.load_state_dict(payload["scheduler_state"])
        trainer.sampler.load_state_dict(payload["sampler_state"])
        trainer.corruption_generator.set_state(
            payload["corruption_generator_state"]
        )
        trainer.completed_step = step
        trainer.parent_checkpoint_sha256 = expected_digest
        trainer.last_restored_checkpoint_sha256 = expected_digest
        trainer._validate_live_state()
        # The persisted global Torch state is installed only after all other
        # live validation has succeeded.
        torch.random.set_rng_state(payload["global_torch_rng_state"])
        trainer.monitor.check("checkpoint-restore")
        if random.getstate() != python_before:
            raise AtomicCountingTrainingError("checkpoint restore consumed Python RNG")
        if not _numpy_rng_equal(np.random.get_state(), numpy_before):
            raise AtomicCountingTrainingError("checkpoint restore consumed NumPy RNG")
    except BaseException:
        trainer.model.load_state_dict(model_before, strict=True)
        trainer.optimizer.load_state_dict(optimizer_before)
        trainer.scheduler.load_state_dict(scheduler_before)
        trainer.sampler.load_state_dict(sampler_before)
        trainer.corruption_generator.set_state(corruption_before)
        trainer.completed_step = completed_before
        trainer.parent_checkpoint_sha256 = parent_before
        trainer.last_restored_checkpoint_sha256 = restored_before
        trainer.model.train(mode_before)
        torch.random.set_rng_state(global_before)
        random.setstate(python_before)
        np.random.set_state(numpy_before)
        raise
    return step


def _tensor_manifest(value: torch.Tensor) -> Mapping[str, object]:
    tensor = value.detach().clone().contiguous().cpu()
    if tensor.dtype == torch.bool:
        numpy_value = tensor.numpy().astype(np.bool_, copy=False)
    else:
        numpy_value = tensor.numpy()
    return {
        "data_hex": numpy_value.tobytes(order="C").hex(),
        "dtype": str(tensor.dtype).removeprefix("torch."),
        "shape": list(tensor.shape),
    }


def _state_manifest(value: object) -> Mapping[str, object]:
    if value is None:
        return {"kind": "none"}
    if type(value) is bool:
        return {"kind": "bool", "value": value}
    if type(value) is int:
        return {"kind": "int", "value": value}
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("state manifest cannot contain nonfinite floats")
        return {"kind": "float", "value": value.hex()}
    if type(value) is str:
        return {"kind": "str", "value": value}
    if type(value) is torch.Tensor:
        return {"kind": "tensor", "value": _tensor_manifest(value)}
    if type(value) in (list, tuple):
        return {
            "kind": "tuple" if type(value) is tuple else "list",
            "items": [_state_manifest(item) for item in value],
        }
    if type(value) is dict:
        items = []
        for key, item in value.items():
            if type(key) is str:
                key_manifest: object = ["str", key]
            elif type(key) is int:
                key_manifest = ["int", key]
            else:
                raise TypeError("state manifest mapping key is unsupported")
            items.append([key_manifest, _state_manifest(item)])
        return {"kind": "dict", "items": items}
    raise TypeError("state manifest object type is unsupported")


def _step_manifest(value: AtomicCountingTrainingStep) -> Mapping[str, object]:
    if type(value) is not AtomicCountingTrainingStep:
        raise TypeError("step record must be exact AtomicCountingTrainingStep")
    value.__post_init__()
    return {
        "absent_count": value.absent_count,
        "completed_step": value.completed_step,
        "continuous_count": value.continuous_count,
        "continuous_loss": _tensor_manifest(value.continuous_loss),
        "count_loss": _tensor_manifest(value.count_loss),
        "empty_count": value.empty_count,
        "occupied_count": value.occupied_count,
        "presence_loss": _tensor_manifest(value.presence_loss),
        "present_count": value.present_count,
        "task_id": value.task_id,
        "task_index": value.task_index,
        "total_loss": _tensor_manifest(value.total_loss),
    }


def exact_training_state_manifest(
    trainer: AtomicCountingTrainer,
    records: Sequence[AtomicCountingTrainingStep],
) -> Mapping[str, object]:
    """Expose every compared scalar/tensor byte for restart falsification tests."""

    if type(trainer) is not AtomicCountingTrainer:
        raise TypeError("trainer must be exact AtomicCountingTrainer")
    if type(records) not in (tuple, list):
        raise TypeError("records must be a tuple or list")
    if len(records) != trainer.completed_step:
        raise ValueError("step-record count differs from completed step")
    for index, record in enumerate(records, start=1):
        if (
            type(record) is not AtomicCountingTrainingStep
            or record.completed_step != index
        ):
            raise ValueError("step records must be complete and consecutive")
    trainer._validate_live_state()
    return {
        "bindings_digest": trainer.bindings.digest,
        "completed_step": trainer.completed_step,
        "corruption_generator_state": _tensor_manifest(
            trainer.corruption_generator.get_state()
        ),
        "domain": trainer.training_config.domain.value,
        "format": "heterodiff-atomic-counting-restart-comparison-v1",
        "gate_id": ATOMIC_COUNTING_GATE_ID,
        "global_torch_rng_state": _tensor_manifest(torch.random.get_rng_state()),
        "model_state": _state_manifest(dict(trainer.model.state_dict())),
        "optimizer_state": _state_manifest(trainer.optimizer.state_dict()),
        "parameter_count": trainer.model.parameter_count,
        "sampler_state": _state_manifest(trainer.sampler.state_dict()),
        "scheduler_state": _state_manifest(trainer.scheduler.state_dict()),
        "step_records": [_step_manifest(record) for record in records],
        "task_bundle_digest": trainer.tasks.bundle_digest,
        "training_config_digest": trainer.training_config.config_digest,
    }


def training_manifest_bytes(
    trainer: AtomicCountingTrainer,
    records: Sequence[AtomicCountingTrainingStep],
) -> bytes:
    return _canonical_json_bytes(exact_training_state_manifest(trainer, records))


def write_training_manifest_no_replace(
    trainer: AtomicCountingTrainer,
    records: Sequence[AtomicCountingTrainingStep],
    path: PathLike,
) -> str:
    """Write a temporary test-comparison artifact, never an evidence bundle."""

    preflight_atomic_counting_pinned_runtime()
    payload = training_manifest_bytes(trainer, records)
    trainer.monitor.check_output_size(len(payload))
    trainer.monitor.check("comparison-output-preflight")
    _atomic_publish_no_replace(path, payload)
    try:
        trainer.monitor.check("comparison-output")
    except BaseException:
        destination = Path(path)
        if destination.is_file() and _sha256_bytes(destination.read_bytes()) == _sha256_bytes(
            payload
        ):
            destination.unlink()
        raise
    return _sha256_bytes(payload)


def _canonical_distribution_name(value: str) -> str:
    if type(value) is not str or not value:
        raise AtomicCountingRuntimeError("lock distribution name is invalid")
    result = value.lower().replace("_", "-").replace(".", "-")
    while "--" in result:
        result = result.replace("--", "-")
    if not result or result[0] == "-" or result[-1] == "-":
        raise AtomicCountingRuntimeError("lock distribution name is invalid")
    return result


def _pinned_runtime_lock_path() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "requirements"
        / "m1-reference-macos-arm64-py311.lock"
    )


def _pinned_lock_versions() -> Dict[str, str]:
    path = _pinned_runtime_lock_path()
    if not path.is_file() or path.is_symlink():
        raise AtomicCountingRuntimeError(
            "pinned runtime lock is missing or is not a regular project file"
        )
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as error:
        raise AtomicCountingRuntimeError("pinned runtime lock is not UTF-8") from error
    result: Dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.count("==") != 1:
            raise AtomicCountingRuntimeError(
                "pinned runtime lock line {} is not an exact version pin".format(
                    line_number
                )
            )
        declared_name, version = line.split("==")
        if (
            not declared_name
            or not version
            or declared_name != declared_name.strip()
            or version != version.strip()
        ):
            raise AtomicCountingRuntimeError(
                "pinned runtime lock line {} is not canonical".format(line_number)
            )
        name = _canonical_distribution_name(declared_name)
        if name in result:
            raise AtomicCountingRuntimeError(
                "pinned runtime lock repeats distribution {}".format(name)
            )
        result[name] = version
    if not result:
        raise AtomicCountingRuntimeError("pinned runtime lock has no distributions")
    return dict(sorted(result.items()))


def _capture_atomic_counting_pinned_runtime() -> Dict[str, object]:
    expected_distributions = _pinned_lock_versions()
    installed_distributions: Dict[str, str] = {}
    for name in expected_distributions:
        try:
            installed_distributions[name] = importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError as error:
            raise AtomicCountingRuntimeError(
                "pinned distribution {} is not installed".format(name)
            ) from error
    mps_available = False
    if hasattr(torch.backends, "mps"):
        mps_available = bool(torch.backends.mps.is_available())
    warn_only = False
    if hasattr(torch, "is_deterministic_algorithms_warn_only_enabled"):
        warn_only = bool(torch.is_deterministic_algorithms_warn_only_enabled())
    return {
        "bootstrap_attestation": _capture_bootstrap_attestation(),
        "default_device": str(torch.get_default_device()),
        "default_dtype": str(torch.get_default_dtype()),
        "environment": {
            key: os.environ.get(key) for key in sorted(_PINNED_ENVIRONMENT)
        },
        "format": _RUNTIME_MANIFEST_FORMAT,
        "locked_distributions": installed_distributions,
        "machine": os.uname().machine,
        "mps_available_but_unused": mps_available,
        "numpy_version": np.__version__,
        "os_name": os.name,
        "platform": sys.platform,
        "python_implementation": sys.implementation.name,
        "python_major_minor": [sys.version_info.major, sys.version_info.minor],
        "python_version": sys.version.split()[0],
        "torch_cuda_version": torch.version.cuda,
        "torch_flags": {
            "deterministic_algorithms": bool(
                torch.are_deterministic_algorithms_enabled()
            ),
            "deterministic_warn_only": warn_only,
            "mkldnn_enabled": bool(torch.backends.mkldnn.enabled),
            "num_interop_threads": torch.get_num_interop_threads(),
            "num_threads": torch.get_num_threads(),
        },
        "torch_version": torch.__version__,
    }


def _validate_atomic_counting_pinned_runtime(
    value: object,
    *,
    require_configured_torch_flags: bool = True,
) -> Mapping[str, object]:
    if type(require_configured_torch_flags) is not bool:
        raise TypeError("require_configured_torch_flags must be boolean")
    if type(value) is not dict:
        raise AtomicCountingRuntimeError("runtime manifest must be a plain mapping")
    expected_keys = {
        "bootstrap_attestation",
        "default_device",
        "default_dtype",
        "environment",
        "format",
        "locked_distributions",
        "machine",
        "mps_available_but_unused",
        "numpy_version",
        "os_name",
        "platform",
        "python_implementation",
        "python_major_minor",
        "python_version",
        "torch_cuda_version",
        "torch_flags",
        "torch_version",
    }
    if set(value) != expected_keys:
        raise AtomicCountingRuntimeError(
            "runtime manifest has missing or unknown fields"
        )
    exact = {
        "default_device": "cpu",
        "default_dtype": "torch.float32",
        "format": _RUNTIME_MANIFEST_FORMAT,
        "machine": _PINNED_MACHINE,
        "numpy_version": _PINNED_NUMPY_VERSION,
        "os_name": "posix",
        "platform": _PINNED_PLATFORM,
        "python_implementation": "cpython",
        "python_major_minor": list(_PINNED_PYTHON_MAJOR_MINOR),
        "python_version": _PINNED_PYTHON_VERSION,
        "torch_cuda_version": None,
        "torch_version": _PINNED_TORCH_VERSION,
    }
    for name, expected in exact.items():
        if value[name] != expected:
            raise AtomicCountingRuntimeError(
                "runtime field {} differs from the pinned value".format(name)
            )
    attestation = value["bootstrap_attestation"]
    expected_attestation = _expected_bootstrap_attestation()
    if (
        type(attestation) is not dict
        or set(attestation) != set(expected_attestation)
        or attestation != expected_attestation
    ):
        raise AtomicCountingRuntimeError(
            "runtime source-bootstrap attestation differs from the frozen values"
        )
    if type(value["mps_available_but_unused"]) is not bool:
        raise AtomicCountingRuntimeError("runtime MPS observation must be boolean")
    if value["environment"] != dict(sorted(_PINNED_ENVIRONMENT.items())):
        raise AtomicCountingRuntimeError(
            "runtime process environment differs from the pinned values"
        )
    expected_flags = {
        "deterministic_algorithms": True,
        "deterministic_warn_only": False,
        "mkldnn_enabled": False,
        "num_interop_threads": 1,
        "num_threads": 1,
    }
    if require_configured_torch_flags and value["torch_flags"] != expected_flags:
        raise AtomicCountingRuntimeError(
            "runtime Torch flags differ from the pinned values"
        )
    if not require_configured_torch_flags and (
        type(value["torch_flags"]) is not dict
        or set(value["torch_flags"]) != set(expected_flags)
    ):
        raise AtomicCountingRuntimeError("runtime Torch flag snapshot is malformed")
    expected_distributions = _pinned_lock_versions()
    if value["locked_distributions"] != expected_distributions:
        raise AtomicCountingRuntimeError(
            "installed distributions differ from the complete pinned lock"
        )
    # Ensure the manifest remains a deterministic, primitive-only binding.
    _canonical_json_bytes(value)
    return copy.deepcopy(value)


def preflight_atomic_counting_pinned_runtime() -> Mapping[str, object]:
    """Validate the complete local CPU runtime before any gate state change."""

    return _validate_atomic_counting_pinned_runtime(
        _capture_atomic_counting_pinned_runtime()
    )


def configure_atomic_counting_deterministic_runtime() -> Mapping[str, object]:
    """Apply and validate the frozen single-threaded deterministic CPU runtime."""

    # Environment variables and dependency versions must already be correct;
    # changing thread flags cannot turn a mislaunched interpreter into a valid
    # evidence process.
    _validate_atomic_counting_pinned_runtime(
        _capture_atomic_counting_pinned_runtime(),
        require_configured_torch_flags=False,
    )
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        if torch.get_num_interop_threads() != 1:
            raise
    torch.backends.mkldnn.enabled = False
    torch.use_deterministic_algorithms(True, warn_only=False)
    return preflight_atomic_counting_pinned_runtime()


def _stable_gate_file_bytes(path: Path, *, limit: int, name: str) -> bytes:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        try:
            component = current.lstat()
        except FileNotFoundError as error:
            raise AtomicCountingTrainingError("{} is missing".format(name)) from error
        if stat.S_ISLNK(component.st_mode):
            raise AtomicCountingTrainingError(
                "{} path must not contain symlinks".format(name)
            )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        named = path.lstat()
        identity = lambda value: (
            value.st_dev,
            value.st_ino,
            stat.S_IFMT(value.st_mode),
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(named.st_mode)
            or identity(before) != identity(named)
            or before.st_size > limit
        ):
            raise AtomicCountingTrainingError(
                "{} is not one bounded stable regular file".format(name)
            )
        chunks = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                raise AtomicCountingTrainingError(
                    "{} was truncated while reading".format(name)
                )
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise AtomicCountingTrainingError(
                "{} grew while reading".format(name)
            )
        if identity(os.fstat(descriptor)) != identity(before):
            raise AtomicCountingTrainingError(
                "{} changed while reading".format(name)
            )
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _expected_bootstrap_attestation() -> Dict[str, object]:
    root = Path(__file__).resolve().parents[3]
    try:
        bootstrap_raw = _stable_gate_file_bytes(
            root / _BOOTSTRAP_RELATIVE_PATH,
            limit=1024 * 1024,
            name="source bootstrap",
        )
    except AtomicCountingTrainingError as error:
        raise AtomicCountingRuntimeError(
            "source bootstrap could not be content-attested"
        ) from error
    return {
        "bootstrap_sha256": _sha256_bytes(bootstrap_raw),
        "executable_sha256": _PINNED_PYTHON_EXECUTABLE_SHA256,
        "executable_size_bytes": _PINNED_PYTHON_EXECUTABLE_SIZE_BYTES,
        "python_implementation": "cpython",
        "python_version": _PINNED_PYTHON_VERSION,
        "schema": _BOOTSTRAP_SCHEMA,
    }


def _capture_bootstrap_attestation() -> Dict[str, object]:
    expected = _expected_bootstrap_attestation()
    observed = {
        name: os.environ.get(environment_name)
        for name, environment_name in _BOOTSTRAP_ENVIRONMENT_FIELDS.items()
    }
    expected_environment = {
        **expected,
        "executable_size_bytes": str(expected["executable_size_bytes"]),
    }
    if observed != expected_environment:
        raise AtomicCountingRuntimeError(
            "runtime source-bootstrap environment attestation is missing or invalid"
        )
    return dict(expected)


def local_gate_external_digests() -> Mapping[str, str]:
    """Content-bind stable local source, specification, lock, and runtime bytes."""

    runtime = preflight_atomic_counting_pinned_runtime()
    root = Path(__file__).resolve().parents[3]
    source_root = root / "src" / "heterodiff"
    test_root = root / "tests"
    optional_relatives = (
        ".pytest.ini",
        "conftest.py",
        "pytest.ini",
        "setup.cfg",
        "sitecustomize.py",
        "src/conftest.py",
        "src/sitecustomize.py",
        "src/usercustomize.py",
        "tox.ini",
        "usercustomize.py",
    )
    required_paths = (
        *source_root.rglob("*.py"),
        *test_root.rglob("*.py"),
        root / "pyproject.toml",
    )
    if not required_paths:
        raise AtomicCountingTrainingError("local source tree is empty")

    def observation(path: Path) -> Tuple[int, ...]:
        value = path.lstat()
        return (
            value.st_dev,
            value.st_ino,
            stat.S_IFMT(value.st_mode),
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    optional_before = {}
    for relative in optional_relatives:
        path = root / relative
        absolute_parent = path.parent.absolute()
        current = Path(absolute_parent.anchor)
        for part in absolute_parent.parts[1:]:
            current = current / part
            try:
                component = current.lstat()
            except FileNotFoundError as error:
                raise AtomicCountingTrainingError(
                    "optional source/startup configuration parent is missing"
                ) from error
            if stat.S_ISLNK(component.st_mode):
                raise AtomicCountingTrainingError(
                    "optional source/startup configuration path must not contain symlinks"
                )
        try:
            optional_before[relative] = observation(path)
        except FileNotFoundError:
            optional_before[relative] = None
    entries = {
        path.relative_to(root).as_posix(): path for path in required_paths
    }
    entries.update(
        {relative: root / relative for relative in optional_relatives}
    )
    source_digest = hashlib.sha256()
    source_digest.update(
        b"heterodiff.atomic-counting-source-test-config-startup-tree.v3\x00"
    )
    for relative_text, path in sorted(entries.items()):
        relative = relative_text.encode("utf-8")
        source_digest.update(len(relative).to_bytes(8, "big"))
        source_digest.update(relative)
        if (
            relative_text in optional_before
            and optional_before[relative_text] is None
        ):
            source_digest.update(b"\x00")
            continue
        raw = _stable_gate_file_bytes(
            path, limit=8 * 1024 * 1024, name="implementation source"
        )
        source_digest.update(b"\x01")
        source_digest.update(len(raw).to_bytes(8, "big"))
        source_digest.update(raw)
    for relative, before in optional_before.items():
        path = root / relative
        try:
            after = observation(path)
        except FileNotFoundError:
            after = None
        if after != before:
            raise AtomicCountingTrainingError(
                "optional source/startup configuration changed while hashing"
            )
    lock_path = root / "requirements" / "m1-reference-macos-arm64-py311.lock"
    gate_path = root / "research" / "32_cross_domain_atomic_counting_reference_gate.md"
    lock_raw = _stable_gate_file_bytes(
        lock_path, limit=1024 * 1024, name="dependency lock"
    )
    gate_raw = _stable_gate_file_bytes(
        gate_path, limit=2 * 1024 * 1024, name="gate specification"
    )
    return {
        "code_source": source_digest.hexdigest(),
        "dependency_lock": _sha256_bytes(lock_raw),
        "environment_manifest": _domain_digest(
            "heterodiff.atomic-counting-local-environment.v1", runtime
        ),
        "gate_spec": _sha256_bytes(gate_raw),
    }


__all__ = [
    "ATOMIC_COUNTING_GATE_ID",
    "AtomicCountingCheckpointBindings",
    "AtomicCountingCheckpointError",
    "AtomicCountingCheckpointIntegrityError",
    "AtomicCountingCheckpointMismatchError",
    "AtomicCountingCheckpointReplayError",
    "AtomicCountingResourceError",
    "AtomicCountingResourceLimits",
    "AtomicCountingResourceMonitor",
    "AtomicCountingRuntimeError",
    "AtomicCountingTrainer",
    "AtomicCountingTrainingConfig",
    "AtomicCountingTrainingError",
    "AtomicCountingTrainingStep",
    "AtomicCountingTrainingTasks",
    "M_ACG_1_TRAINING_CONFIG",
    "M_ACG_1_TASK_SEQUENCE",
    "P_ACG_1_TRAINING_CONFIG",
    "P_ACG_1_TASK_SEQUENCE",
    "adapt_counting_task_set",
    "atomic_counting_target_tensor_digest",
    "build_atomic_counting_trainer",
    "build_checkpoint_bindings",
    "configure_atomic_counting_deterministic_runtime",
    "exact_training_state_manifest",
    "load_atomic_counting_checkpoint",
    "local_gate_external_digests",
    "preflight_atomic_counting_pinned_runtime",
    "save_atomic_counting_checkpoint",
    "training_manifest_bytes",
    "write_training_manifest_no_replace",
]
