"""Custody and permit boundary for the frozen A1 exact-population lane.

Section 6 of the A1 preregistration now authoritatively fixes this lane: all
eight paired seeds, a full ``M_train`` batch, 3,000 AdamW updates for the two
matched primary learners, and 4,500 for the stronger direct diagnostic.  The
objective is exactly

``sum[J*softplus(-ell) + R*softplus(ell)] / (2*16)``.

This module prepares every result-independent object, defines strict result
schemas, and contains the method-local optimizer loop.  That loop remains
fail-closed unless the isolated, exactly-once runner supplies a ledger-bound,
single-use permit.  Importing this module, preparing custody, and running its
unit tests therefore take no optimizer steps.

The product-positive identification control is *not* a trained lane.  It is
the frozen oracle-only algebra check on the full ``33 x 20 x 21`` reporting
domain and cannot determine PASS or STOP.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import hashlib
import io
import json
import math
from numbers import Integral, Real
import os
from pathlib import Path
import resource
import sys
import time
from typing import Optional, Tuple

import numpy as np
import torch
from torch.nn import functional as torch_functional

from heterodiff.models.finite_association_residual_torch import (
    BASE_FEATURE_COUNT,
    PRIMARY_HIDDEN_WIDTH,
    STRONG_DIRECT_HIDDEN_WIDTH,
    ContinuousCorrectionCertificate,
    FiniteAssociationCorrectionNetwork,
    FiniteAssociationMLPSnapshot,
    certify_finite_association_continuous_correction,
    cosine_adamw_learning_rate,
    finite_association_adamw_update,
    finite_association_features,
    finite_association_logits,
    make_finite_association_adamw,
    require_matching_continuous_certificate,
    require_matching_snapshot_continuous_certificate,
    snapshot_finite_association_mlp,
)

from .finite_association_guided_residual_pilot import (
    FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS,
    FrozenAssociationResidualFixture,
    build_frozen_association_residual_fixture,
    frozen_association_fixture_content_digests,
    frozen_association_fixture_sha256,
    frozen_association_residual_splits,
    run_association_residual_prerequisite_gate,
)
from .finite_association_residual_data import (
    PAIRED_SEEDS,
    PRIMARY_UPDATES,
    STRONGER_UPDATES,
)
from .finite_association_residual_training_torch import (
    FrozenAssociationTrainingEnvironment,
    configure_frozen_association_training_environment,
    frozen_association_training_configuration_sha256,
    frozen_association_training_source_sha256,
)


EXACT_DIRECT_METHOD = "direct"
EXACT_GUIDED_METHOD = "guided"
EXACT_STRONG_DIRECT_METHOD = "strong_direct"
EXACT_PRIMARY_METHODS = (EXACT_DIRECT_METHOD, EXACT_GUIDED_METHOD)
EXACT_POPULATION_METHODS = EXACT_PRIMARY_METHODS + (EXACT_STRONG_DIRECT_METHOD,)
EXACT_SPLIT_NAMES = ("train", "validation", "test")
EXACT_TRAIN_TIME_COUNT = 16
EXACT_POPULATION_SUPPORT_SIZE = EXACT_TRAIN_TIME_COUNT * 61
EXACT_EXPECTED_TOTAL_OPTIMIZER_STEPS = len(PAIRED_SEEDS) * (
    2 * PRIMARY_UPDATES + STRONGER_UPDATES
)
EXACT_RESOURCE_SCOPE = (
    "isolated_process_prepare_guide_train_certificate_evaluate"
)
ORACLE_PRODUCT_POSITIVE_LOGIT_TOLERANCE = 1.0e-9

_SHA256_HEX = frozenset("0123456789abcdef")
_EXPECTED_SPLIT_SHAPES = {
    "train": (16, 61),
    "validation": (8, 19),
    "test": (8, 20),
}
_PERMIT_NOTE = (
    "exact contract is frozen; optimizer execution requires a ledger-bound "
    "isolated exactly-once runner permit; this is local custody enforcement, "
    "not cryptographic caller authentication"
)
_METHOD_RESULT_PAYLOAD_SCHEMA = (
    "heterodiff-a1-exact-population-method-result-payload-v4"
)
_METHOD_RESULT_PAYLOAD_MAXIMUM_BYTES = 32 * 1024 * 1024


class ExactPopulationExecutionPermitRequired(RuntimeError):
    """Raised before optimizer construction when runner authority is absent."""


_EXACT_EXECUTION_PERMIT_CONSTRUCTION_KEY = object()


class FrozenExactPopulationExecutionPermit:
    """Single-use authority for one exact-population seed/method worker.

    Construction is private to the isolated runner.  Validation reads the
    canonical on-disk PREPARED receipt, and consumption durably advances that
    receipt to RUNNING before the optimizer object can be constructed.
    """

    __slots__ = (
        "seed",
        "method",
        "run_key_sha256",
        "preflight_sha256",
        "prepared_ledger_sha256",
        "execution_runtime_sha256",
        "campaign_sha256",
        "worker_session_sha256",
        "launch_id_sha256",
        "launch_authorization_sha256",
        "child_process_identity_sha256",
        "production_session",
        "ledger_directory",
        "worker_process_id",
        "total_wall_start",
        "total_cpu_start",
        "preparation_wall_seconds",
        "preparation_cpu_seconds",
        "_worker_session_capability",
        "_running_ledger_sha256",
        "_consumed",
        "_locked",
    )

    def __init__(
        self,
        *,
        seed: object,
        method: object,
        run_key_sha256: object,
        preflight_sha256: object,
        prepared_ledger_sha256: object,
        execution_runtime_sha256: object,
        campaign_sha256: object,
        worker_session_sha256: object,
        launch_id_sha256: object,
        launch_authorization_sha256: object,
        child_process_identity_sha256: object,
        production_session: object,
        worker_session_capability: object,
        ledger_directory: object,
        worker_process_id: object,
        total_wall_start: object,
        total_cpu_start: object,
        preparation_wall_seconds: object,
        preparation_cpu_seconds: object,
        _construction_key: object,
    ) -> None:
        if _construction_key is not _EXACT_EXECUTION_PERMIT_CONSTRUCTION_KEY:
            raise TypeError(
                "exact execution permits are issued only by the isolated worker"
            )
        object.__setattr__(self, "seed", _require_seed(seed))
        object.__setattr__(self, "method", _require_method(method))
        for name, value in (
            ("run_key_sha256", run_key_sha256),
            ("preflight_sha256", preflight_sha256),
            ("prepared_ledger_sha256", prepared_ledger_sha256),
            ("execution_runtime_sha256", execution_runtime_sha256),
            ("campaign_sha256", campaign_sha256),
            ("worker_session_sha256", worker_session_sha256),
            ("launch_id_sha256", launch_id_sha256),
            ("launch_authorization_sha256", launch_authorization_sha256),
            (
                "child_process_identity_sha256",
                child_process_identity_sha256,
            ),
        ):
            object.__setattr__(self, name, _require_sha256(value, name=name))
        if type(production_session) is not bool:
            raise TypeError("production_session must be boolean")
        object.__setattr__(self, "production_session", production_session)
        object.__setattr__(self, "_worker_session_capability", worker_session_capability)
        object.__setattr__(self, "_running_ledger_sha256", None)
        object.__setattr__(self, "ledger_directory", str(Path(ledger_directory).resolve()))
        if (
            isinstance(worker_process_id, (bool, np.bool_))
            or not isinstance(worker_process_id, Integral)
            or int(worker_process_id) <= 0
        ):
            raise ValueError("worker_process_id must be a positive integer")
        object.__setattr__(self, "worker_process_id", int(worker_process_id))
        for name, value in (
            ("total_wall_start", total_wall_start),
            ("total_cpu_start", total_cpu_start),
        ):
            scalar = _finite_float(value, name=name, nonnegative=True)
            object.__setattr__(self, name, scalar)
        for name, value in (
            ("preparation_wall_seconds", preparation_wall_seconds),
            ("preparation_cpu_seconds", preparation_cpu_seconds),
        ):
            scalar = _finite_float(value, name=name, positive=True)
            object.__setattr__(self, name, scalar)
        object.__setattr__(self, "_consumed", False)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("exact execution permit is immutable")
        object.__setattr__(self, name, value)

    def validate_for(
        self,
        prepared: "PreparedAssociationExactPopulationDiagnostic",
        seed: object,
        method: object,
    ) -> None:
        if self._consumed:
            raise RuntimeError("exact execution permit was already consumed")
        if os.getpid() != self.worker_process_id:
            raise RuntimeError("exact execution permit belongs to another process")
        if type(prepared) is not PreparedAssociationExactPopulationDiagnostic:
            raise TypeError("prepared must be exact-population preparation")
        if (
            _require_seed(seed) != self.seed
            or _require_method(method) != self.method
            or prepared.preflight_sha256 != self.preflight_sha256
        ):
            raise RuntimeError("exact execution permit does not match this run")
        from heterodiff.experiments.finite_association_exact_population_isolated_runner import (
            _verify_prepared_exact_execution_permit,
        )

        _verify_prepared_exact_execution_permit(
            self, prepared, self.seed, self.method
        )

    def consume_for(
        self,
        prepared: "PreparedAssociationExactPopulationDiagnostic",
        seed: object,
        method: object,
    ) -> None:
        self.validate_for(prepared, seed, method)
        from heterodiff.experiments.finite_association_exact_population_isolated_runner import (
            _consume_prepared_exact_execution_permit,
        )

        running_sha256 = _consume_prepared_exact_execution_permit(
            self, prepared, self.seed, self.method
        )
        object.__setattr__(
            self,
            "_running_ledger_sha256",
            _require_sha256(
                running_sha256, name="running_ledger_sha256"
            ),
        )
        object.__setattr__(self, "_consumed", True)

    @property
    def running_ledger_sha256(self) -> str:
        if not self._consumed or self._running_ledger_sha256 is None:
            raise RuntimeError("exact permit has no consumed RUNNING receipt")
        return self._running_ledger_sha256


def _issue_frozen_exact_population_execution_permit(
    *,
    seed: object,
    method: object,
    run_key_sha256: object,
    preflight_sha256: object,
    prepared_ledger_sha256: object,
    execution_runtime_sha256: object,
    campaign_sha256: object,
    ledger_directory: object,
    total_wall_start: object,
    total_cpu_start: object,
    preparation_wall_seconds: object,
    preparation_cpu_seconds: object,
    worker_session_capability: object,
) -> FrozenExactPopulationExecutionPermit:
    """Private bridge called only after the worker persists PREPARED."""

    from heterodiff.experiments.finite_association_exact_population_isolated_runner import (
        _authorize_exact_execution_permit_session,
    )

    (
        worker_session_sha256,
        production_session,
        launch_id_sha256,
        launch_authorization_sha256,
        child_process_identity_sha256,
    ) = (
        _authorize_exact_execution_permit_session(
            worker_session_capability,
            ledger_directory=ledger_directory,
            run_key_sha256=run_key_sha256,
            prepared_ledger_sha256=prepared_ledger_sha256,
            execution_runtime_sha256=execution_runtime_sha256,
            campaign_sha256=campaign_sha256,
        )
    )

    return FrozenExactPopulationExecutionPermit(
        seed=seed,
        method=method,
        run_key_sha256=run_key_sha256,
        preflight_sha256=preflight_sha256,
        prepared_ledger_sha256=prepared_ledger_sha256,
        execution_runtime_sha256=execution_runtime_sha256,
        campaign_sha256=campaign_sha256,
        worker_session_sha256=worker_session_sha256,
        launch_id_sha256=launch_id_sha256,
        launch_authorization_sha256=launch_authorization_sha256,
        child_process_identity_sha256=child_process_identity_sha256,
        production_session=production_session,
        worker_session_capability=worker_session_capability,
        ledger_directory=ledger_directory,
        worker_process_id=os.getpid(),
        total_wall_start=total_wall_start,
        total_cpu_start=total_cpu_start,
        preparation_wall_seconds=preparation_wall_seconds,
        preparation_cpu_seconds=preparation_cpu_seconds,
        _construction_key=_EXACT_EXECUTION_PERMIT_CONSTRUCTION_KEY,
    )


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str or len(value) != 64 or any(
        character not in _SHA256_HEX for character in value
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _immutable_array(value: object, dtype: np.dtype) -> np.ndarray:
    array = np.asarray(value)
    if array.dtype != dtype:
        raise TypeError("array dtype must be exactly %s" % dtype)
    contiguous = np.array(array, dtype=dtype, copy=True, order="C")
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=dtype).reshape(
        contiguous.shape
    )


def _array_digest(label: bytes, *arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(label)
    digest.update(b"\0")
    for value in arrays:
        array = np.ascontiguousarray(value)
        descriptor = "%s|%s|" % (
            array.dtype.str,
            ",".join(str(int(size)) for size in array.shape),
        )
        digest.update(descriptor.encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _record_digest(label: bytes, *values: object) -> str:
    digest = hashlib.sha256()
    digest.update(label)
    digest.update(b"\0")
    for value in values:
        payload = str(value).encode("utf-8")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _finite_float(
    value: object,
    *,
    name: str,
    nonnegative: bool = False,
    positive: bool = False,
) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean value" % name)
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite" % name)
    if positive and result <= 0.0:
        raise ValueError("%s must be positive" % name)
    if nonnegative and result < 0.0:
        raise ValueError("%s must be nonnegative" % name)
    return result


def _require_seed(value: object) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("seed must be an integer non-boolean value")
    result = int(value)
    if result not in PAIRED_SEEDS:
        raise ValueError("seed must be one of the eight frozen paired seeds")
    return result


def _require_method(value: object) -> str:
    if type(value) is not str:
        raise TypeError("method must be a string")
    if value not in EXACT_POPULATION_METHODS:
        raise ValueError("method must be direct, guided, or strong_direct")
    return value


def _method_updates(method: str) -> int:
    return (
        STRONGER_UPDATES
        if _require_method(method) == EXACT_STRONG_DIRECT_METHOD
        else PRIMARY_UPDATES
    )


def _method_width(method: str) -> int:
    return (
        STRONG_DIRECT_HIDDEN_WIDTH
        if _require_method(method) == EXACT_STRONG_DIRECT_METHOD
        else PRIMARY_HIDDEN_WIDTH
    )


def _method_parameter_count(method: str) -> int:
    width = _method_width(method)
    return (
        BASE_FEATURE_COUNT * width
        + width
        + width * width
        + width
        + width
        + 1
    )


def _method_forward_macs(method: str) -> int:
    width = _method_width(method)
    return BASE_FEATURE_COUNT * width + width * width + width


def _torch_float64_vector(value: object, *, name: str) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError("%s must be a torch.Tensor" % name)
    if value.dtype != torch.float64 or value.device.type != "cpu":
        raise TypeError("%s must be a CPU float64 tensor" % name)
    if value.ndim != 1 or value.numel() == 0:
        raise ValueError("%s must be a nonempty vector" % name)
    if bool(torch.any(~torch.isfinite(value)).detach().item()):
        raise ValueError("%s must contain only finite values" % name)
    return value


@dataclass(frozen=True)
class FrozenExactPopulationExecutionContract:
    """Authoritative Section 6 exact-lane contract."""

    objective_label: str = "physical_sum_divided_by_2_times_16_train_times"
    train_time_count: int = EXACT_TRAIN_TIME_COUNT
    full_batch: bool = True
    paired_seeds: Tuple[int, ...] = PAIRED_SEEDS
    methods: Tuple[str, ...] = EXACT_POPULATION_METHODS
    primary_updates: int = PRIMARY_UPDATES
    stronger_direct_updates: int = STRONGER_UPDATES
    optimizer_name: str = "AdamW"
    learning_rate: float = 1.0e-3
    final_learning_rate: float = 1.0e-5
    endpoint_inclusive_cosine_schedule: bool = True
    beta1: float = 0.9
    beta2: float = 0.999
    epsilon: float = 1.0e-8
    weight_decay: float = 1.0e-6
    gradient_norm_clip: float = 1.0
    final_checkpoint_only: bool = True
    diagnostic_only: bool = True
    exact_trained_product_control: bool = False
    isolated_runner_permit_required: bool = True

    def __post_init__(self) -> None:
        if self.objective_label != (
            "physical_sum_divided_by_2_times_16_train_times"
        ):
            raise ValueError("the exact objective label changed")
        if self.train_time_count != 16 or self.full_batch is not True:
            raise ValueError("the exact lane must use all 16 train times full-batch")
        if self.paired_seeds != PAIRED_SEEDS or self.methods != EXACT_POPULATION_METHODS:
            raise ValueError("the exact seeds or methods changed")
        if self.primary_updates != 3000 or self.stronger_direct_updates != 4500:
            raise ValueError("the exact update counts changed")
        expected = (1.0e-3, 1.0e-5, 0.9, 0.999, 1.0e-8, 1.0e-6, 1.0)
        actual = (
            self.learning_rate,
            self.final_learning_rate,
            self.beta1,
            self.beta2,
            self.epsilon,
            self.weight_decay,
            self.gradient_norm_clip,
        )
        if self.optimizer_name != "AdamW" or actual != expected:
            raise ValueError("the exact optimizer constants changed")
        if not (
            self.endpoint_inclusive_cosine_schedule
            and self.final_checkpoint_only
            and self.diagnostic_only
            and self.isolated_runner_permit_required
        ):
            raise ValueError("the exact execution safeguards are mandatory")
        if self.exact_trained_product_control is not False:
            raise ValueError("Section 6 does not authorize an exact-trained product lane")

    @property
    def expected_total_optimizer_steps(self) -> int:
        return EXACT_EXPECTED_TOTAL_OPTIMIZER_STEPS

    @property
    def digest(self) -> str:
        return _record_digest(
            b"heterodiff-a1-exact-population-contract-v2",
            self.objective_label,
            self.train_time_count,
            self.full_batch,
            self.paired_seeds,
            self.methods,
            self.primary_updates,
            self.stronger_direct_updates,
            self.optimizer_name,
            self.learning_rate,
            self.final_learning_rate,
            self.endpoint_inclusive_cosine_schedule,
            self.beta1,
            self.beta2,
            self.epsilon,
            self.weight_decay,
            self.gradient_norm_clip,
            self.final_checkpoint_only,
            self.diagnostic_only,
            self.exact_trained_product_control,
            self.isolated_runner_permit_required,
        )


def frozen_exact_population_configuration_sha256(
    *, source_sha256: Optional[object] = None
) -> str:
    """Bind the exact lane to source, sampled optimizer/runtime, and Section 6."""

    source = (
        frozen_association_training_source_sha256()
        if source_sha256 is None
        else _require_sha256(source_sha256, name="source_sha256")
    )
    sampled = frozen_association_training_configuration_sha256(
        source_sha256=source
    )
    contract = FrozenExactPopulationExecutionContract()
    return _record_digest(
        b"heterodiff-a1-exact-population-configuration-v2",
        source,
        sampled,
        contract.digest,
        EXACT_SPLIT_NAMES,
        BASE_FEATURE_COUNT,
        PRIMARY_HIDDEN_WIDTH,
        STRONG_DIRECT_HIDDEN_WIDTH,
    )


@dataclass(frozen=True, eq=False)
class FrozenAssociationExactPopulationSplitCustody:
    """Immutable Cartesian population tensors for one frozen reporting split."""

    split_name: str
    fixture_sha256: str
    split_sha256: str
    time_partition_indices: np.ndarray
    pair_partition: np.ndarray
    time_indices: np.ndarray
    state_indices: np.ndarray
    observation_indices: np.ndarray
    direct_times: np.ndarray
    features: np.ndarray
    terminal_classifier_logits: np.ndarray
    guide_classifier_logits: np.ndarray
    exact_optimal_logits: np.ndarray
    joint_mass: np.ndarray
    product_mass: np.ndarray
    support_sha256: str
    tensor_sha256: str
    custody_sha256: str

    def __post_init__(self) -> None:
        if self.split_name not in EXACT_SPLIT_NAMES:
            raise ValueError("split_name must be train, validation, or test")
        _require_sha256(self.fixture_sha256, name="fixture_sha256")
        _require_sha256(self.split_sha256, name="split_sha256")
        n_times, n_pairs = _EXPECTED_SPLIT_SHAPES[self.split_name]
        size = n_times * n_pairs
        time_partition = _immutable_array(
            self.time_partition_indices, np.dtype(np.int64)
        )
        pairs = _immutable_array(self.pair_partition, np.dtype(np.int64))
        if time_partition.shape != (n_times,) or pairs.shape != (n_pairs, 2):
            raise ValueError("population partition has a non-frozen shape")
        object.__setattr__(self, "time_partition_indices", time_partition)
        object.__setattr__(self, "pair_partition", pairs)
        for name in ("time_indices", "state_indices", "observation_indices"):
            value = _immutable_array(getattr(self, name), np.dtype(np.int64))
            if value.shape != (size,):
                raise ValueError("%s has an invalid split-support shape" % name)
            object.__setattr__(self, name, value)
        if not np.array_equal(self.time_indices, np.repeat(time_partition, n_pairs)):
            raise ValueError("time support is not in frozen time-major order")
        tiled = np.tile(pairs, (n_times, 1))
        if not np.array_equal(self.state_indices, tiled[:, 0]) or not np.array_equal(
            self.observation_indices, tiled[:, 1]
        ):
            raise ValueError("pair support is not the frozen Cartesian product")
        if (
            np.any(self.time_indices < 0)
            or np.any(self.time_indices > 31)
            or np.any(self.state_indices < 0)
            or np.any(self.state_indices >= 20)
            or np.any(self.observation_indices < 0)
            or np.any(self.observation_indices >= 20)
        ):
            raise ValueError("exact split support contains an out-of-range index")
        for name in (
            "direct_times",
            "features",
            "terminal_classifier_logits",
            "guide_classifier_logits",
            "exact_optimal_logits",
            "joint_mass",
            "product_mass",
        ):
            value = _immutable_array(getattr(self, name), np.dtype(np.float64))
            expected = (size, BASE_FEATURE_COUNT) if name == "features" else (size,)
            if value.shape != expected or not np.all(np.isfinite(value)):
                raise ValueError("%s has an invalid exact-population value" % name)
            object.__setattr__(self, name, value)
        if np.any(self.joint_mass <= 0.0) or np.any(self.product_mass <= 0.0):
            raise ValueError("physical class masses must be strictly positive")
        if not np.allclose(
            self.exact_optimal_logits,
            np.log(self.joint_mass) - np.log(self.product_mass),
            atol=2.0e-13,
            rtol=2.0e-13,
        ):
            raise ValueError("exact logits do not equal the physical J/R log ratio")
        if not np.array_equal(self.features[:, -1], np.ones(size)):
            raise ValueError("the frozen feature constant changed")
        for name in ("support_sha256", "tensor_sha256", "custody_sha256"):
            _require_sha256(getattr(self, name), name=name)
        support = _array_digest(
            b"heterodiff-a1-exact-population-split-support-v2",
            self.time_partition_indices,
            self.pair_partition,
            self.time_indices,
            self.state_indices,
            self.observation_indices,
        )
        tensors = _array_digest(
            b"heterodiff-a1-exact-population-split-tensors-v2",
            self.direct_times,
            self.features,
            self.terminal_classifier_logits,
            self.guide_classifier_logits,
            self.exact_optimal_logits,
            self.joint_mass,
            self.product_mass,
        )
        custody = _record_digest(
            b"heterodiff-a1-exact-population-split-custody-v2",
            self.split_name,
            self.fixture_sha256,
            self.split_sha256,
            support,
            tensors,
        )
        if support != self.support_sha256 or tensors != self.tensor_sha256:
            raise ValueError("exact split arrays do not match their digests")
        if custody != self.custody_sha256:
            raise ValueError("exact split custody digest is inconsistent")

    @property
    def support_size(self) -> int:
        return int(self.direct_times.size)

    @property
    def physical_normalizer(self) -> float:
        return 0.5 * math.fsum(
            float(positive) + float(negative)
            for positive, negative in zip(self.joint_mass, self.product_mass)
        )


# Compatibility name for code that used the original train-only custody type.
FrozenAssociationExactPopulationCustody = FrozenAssociationExactPopulationSplitCustody


@dataclass(frozen=True, eq=False)
class FrozenOracleProductPositiveControlCustody:
    """Full-domain equal-law algebra custody; no optimizer is authorized."""

    fixture_sha256: str
    equal_class_mass: np.ndarray
    pointwise_optimal_logits: np.ndarray
    maximum_absolute_logit: float
    passed: bool
    oracle_only: bool
    optimizer_execution_authorized: bool
    tensor_sha256: str
    custody_sha256: str

    def __post_init__(self) -> None:
        _require_sha256(self.fixture_sha256, name="fixture_sha256")
        for name in ("equal_class_mass", "pointwise_optimal_logits"):
            value = _immutable_array(getattr(self, name), np.dtype(np.float64))
            if value.shape != (33, 20, 21) or not np.all(np.isfinite(value)):
                raise ValueError("%s has an invalid product-control value" % name)
            object.__setattr__(self, name, value)
        if np.any(self.equal_class_mass <= 0.0):
            raise ValueError("product-control masses must be positive")
        maximum = _finite_float(
            self.maximum_absolute_logit,
            name="maximum_absolute_logit",
            nonnegative=True,
        )
        observed_maximum = float(np.max(np.abs(self.pointwise_optimal_logits)))
        if maximum != observed_maximum:
            raise ValueError("product-positive maximum does not match its table")
        expected_pass = maximum <= ORACLE_PRODUCT_POSITIVE_LOGIT_TOLERANCE
        if self.passed is not expected_pass:
            raise ValueError("product-positive pass flag disagrees with the 1e-9 gate")
        if self.oracle_only is not True or self.optimizer_execution_authorized is not False:
            raise ValueError("the product-positive control must remain optimizer-free oracle algebra")
        object.__setattr__(self, "maximum_absolute_logit", maximum)
        _require_sha256(self.tensor_sha256, name="tensor_sha256")
        _require_sha256(self.custody_sha256, name="custody_sha256")
        tensor = _array_digest(
            b"heterodiff-a1-oracle-product-positive-tensors-v3",
            self.equal_class_mass,
            self.pointwise_optimal_logits,
        )
        custody = _record_digest(
            b"heterodiff-a1-oracle-product-positive-custody-v3",
            self.fixture_sha256,
            self.maximum_absolute_logit,
            self.passed,
            self.oracle_only,
            self.optimizer_execution_authorized,
            tensor,
        )
        if tensor != self.tensor_sha256 or custody != self.custody_sha256:
            raise ValueError("oracle product-control custody is inconsistent")


@dataclass(frozen=True)
class FrozenExactPopulationSeedCustody:
    seed: int
    torch_generator_seed: int
    primary_initial_parameter_sha256: str
    stronger_direct_initial_parameter_sha256: str
    custody_sha256: str

    def __post_init__(self) -> None:
        checked = _require_seed(self.seed)
        if checked != self.seed:
            raise ValueError("seed must be stored canonically")
        if (
            isinstance(self.torch_generator_seed, (bool, np.bool_))
            or not isinstance(self.torch_generator_seed, Integral)
            or not 0 <= int(self.torch_generator_seed) <= 2**64 - 1
        ):
            raise ValueError("torch_generator_seed must be a uint64-range integer")
        for name in (
            "primary_initial_parameter_sha256",
            "stronger_direct_initial_parameter_sha256",
            "custody_sha256",
        ):
            _require_sha256(getattr(self, name), name=name)
        observed = _record_digest(
            b"heterodiff-a1-exact-population-seed-custody-v2",
            checked,
            int(self.torch_generator_seed),
            self.primary_initial_parameter_sha256,
            self.stronger_direct_initial_parameter_sha256,
        )
        if observed != self.custody_sha256:
            raise ValueError("seed custody digest is inconsistent")


@dataclass(frozen=True, eq=False)
class PreparedAssociationExactPopulationDiagnostic:
    fixture: FrozenAssociationResidualFixture
    fixture_content_sha256: Tuple[str, str, str, str, str]
    populations: Tuple[
        FrozenAssociationExactPopulationSplitCustody,
        FrozenAssociationExactPopulationSplitCustody,
        FrozenAssociationExactPopulationSplitCustody,
    ]
    oracle_product_control: FrozenOracleProductPositiveControlCustody
    seed_custodies: Tuple[FrozenExactPopulationSeedCustody, ...]
    execution_contract: FrozenExactPopulationExecutionContract
    source_sha256: str
    sampled_configuration_sha256: str
    exact_configuration_sha256: str
    preflight_sha256: str

    def __post_init__(self) -> None:
        if type(self.fixture) is not FrozenAssociationResidualFixture:
            raise TypeError("fixture must be the exact frozen association fixture")
        if type(self.fixture_content_sha256) is not tuple or len(
            self.fixture_content_sha256
        ) != 5:
            raise TypeError("fixture_content_sha256 must contain five digests")
        for value in self.fixture_content_sha256:
            _require_sha256(value, name="fixture_content_sha256")
        actual = frozen_association_fixture_content_digests(self.fixture)
        if (
            actual != self.fixture_content_sha256
            or actual != FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS
        ):
            raise ValueError("prepared fixture contents are not frozen A1")
        if type(self.populations) is not tuple or len(self.populations) != 3:
            raise TypeError("populations must contain train/validation/test custody")
        if tuple(value.split_name for value in self.populations) != EXACT_SPLIT_NAMES:
            raise ValueError("population split custody is not canonical")
        fixture_token = frozen_association_fixture_sha256(actual)
        if any(value.fixture_sha256 != fixture_token for value in self.populations):
            raise ValueError("population custody is not bound to the actual fixture")
        if type(self.oracle_product_control) is not (
            FrozenOracleProductPositiveControlCustody
        ):
            raise TypeError("oracle_product_control has an invalid type")
        if self.oracle_product_control.fixture_sha256 != fixture_token:
            raise ValueError("oracle product control is not bound to the actual fixture")
        if type(self.seed_custodies) is not tuple or tuple(
            value.seed for value in self.seed_custodies
        ) != PAIRED_SEEDS:
            raise ValueError("seed custody must contain all eight seeds canonically")
        if not all(
            type(value) is FrozenExactPopulationSeedCustody
            for value in self.seed_custodies
        ):
            raise TypeError("seed custody contains an invalid record")
        if type(self.execution_contract) is not FrozenExactPopulationExecutionContract:
            raise TypeError("execution_contract must be the authoritative contract")
        for name in (
            "source_sha256",
            "sampled_configuration_sha256",
            "exact_configuration_sha256",
            "preflight_sha256",
        ):
            _require_sha256(getattr(self, name), name=name)
        expected_sampled = frozen_association_training_configuration_sha256(
            source_sha256=self.source_sha256
        )
        expected_exact = frozen_exact_population_configuration_sha256(
            source_sha256=self.source_sha256
        )
        if (
            expected_sampled != self.sampled_configuration_sha256
            or expected_exact != self.exact_configuration_sha256
        ):
            raise ValueError("prepared source/configuration custody is inconsistent")
        if _prepared_preflight_sha256(self) != self.preflight_sha256:
            raise ValueError("exact-population preflight digest is inconsistent")

    @property
    def train_population(self) -> FrozenAssociationExactPopulationSplitCustody:
        return self.populations[0]

    @property
    def validation_population(self) -> FrozenAssociationExactPopulationSplitCustody:
        return self.populations[1]

    @property
    def test_population(self) -> FrozenAssociationExactPopulationSplitCustody:
        return self.populations[2]

    @property
    def population(self) -> FrozenAssociationExactPopulationSplitCustody:
        """Compatibility property for the historical train-only name."""

        return self.train_population

    @property
    def custody_sha256(self) -> str:
        return self.preflight_sha256


def _exact_preflight_sha256_from_parts(
    *,
    fixture_content_sha256: Tuple[str, str, str, str, str],
    populations: Tuple[
        FrozenAssociationExactPopulationSplitCustody,
        FrozenAssociationExactPopulationSplitCustody,
        FrozenAssociationExactPopulationSplitCustody,
    ],
    oracle_product_control: FrozenOracleProductPositiveControlCustody,
    seed_custodies: Tuple[FrozenExactPopulationSeedCustody, ...],
    execution_contract: FrozenExactPopulationExecutionContract,
    source_sha256: str,
    sampled_configuration_sha256: str,
    exact_configuration_sha256: str,
) -> str:
    return _record_digest(
        b"heterodiff-a1-exact-population-preflight-v2",
        fixture_content_sha256,
        tuple(value.custody_sha256 for value in populations),
        oracle_product_control.custody_sha256,
        tuple(value.custody_sha256 for value in seed_custodies),
        execution_contract.digest,
        source_sha256,
        sampled_configuration_sha256,
        exact_configuration_sha256,
        tuple(
            (
                method,
                _method_width(method),
                _method_updates(method),
                _method_parameter_count(method),
                _method_forward_macs(method),
            )
            for method in EXACT_POPULATION_METHODS
        ),
    )


def _prepared_preflight_sha256(
    prepared: PreparedAssociationExactPopulationDiagnostic,
) -> str:
    return _exact_preflight_sha256_from_parts(
        fixture_content_sha256=prepared.fixture_content_sha256,
        populations=prepared.populations,
        oracle_product_control=prepared.oracle_product_control,
        seed_custodies=prepared.seed_custodies,
        execution_contract=prepared.execution_contract,
        source_sha256=prepared.source_sha256,
        sampled_configuration_sha256=prepared.sampled_configuration_sha256,
        exact_configuration_sha256=prepared.exact_configuration_sha256,
    )


def _snapshot_parameter_sha256(
    arrays: Tuple[Tuple[str, np.ndarray], ...]
) -> str:
    digest = hashlib.sha256()
    for name, value in arrays:
        array = np.ascontiguousarray(value, dtype=np.float64)
        digest.update(name.encode("utf-8"))
        digest.update(b"torch.float64")
        digest.update(repr(tuple(array.shape)).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


@dataclass(frozen=True, eq=False)
class FrozenExactPopulationMLPSnapshot:
    """Read-only NumPy custody for an immutable final MLP snapshot."""

    input_features: int
    hidden_width: int
    weight1: np.ndarray
    bias1: np.ndarray
    weight2: np.ndarray
    bias2: np.ndarray
    weight3: np.ndarray
    bias3: np.ndarray
    parameter_sha256: str

    def __post_init__(self) -> None:
        if self.input_features != BASE_FEATURE_COUNT or self.hidden_width not in (
            PRIMARY_HIDDEN_WIDTH,
            STRONG_DIRECT_HIDDEN_WIDTH,
        ):
            raise ValueError("snapshot architecture is not an exact-lane architecture")
        names = ("weight1", "bias1", "weight2", "bias2", "weight3", "bias3")
        expected = (
            (self.hidden_width, self.input_features),
            (self.hidden_width,),
            (self.hidden_width, self.hidden_width),
            (self.hidden_width,),
            (1, self.hidden_width),
            (1,),
        )
        values = []
        for name, shape in zip(names, expected):
            value = _immutable_array(getattr(self, name), np.dtype(np.float64))
            if value.shape != shape or not np.all(np.isfinite(value)):
                raise ValueError("snapshot %s has an invalid value" % name)
            object.__setattr__(self, name, value)
            values.append((name, value))
        _require_sha256(self.parameter_sha256, name="parameter_sha256")
        if _snapshot_parameter_sha256(tuple(values)) != self.parameter_sha256:
            raise ValueError("immutable snapshot tensors do not match their digest")

    @classmethod
    def from_torch_snapshot(
        cls, snapshot: FiniteAssociationMLPSnapshot
    ) -> "FrozenExactPopulationMLPSnapshot":
        if type(snapshot) is not FiniteAssociationMLPSnapshot:
            raise TypeError("snapshot must be an exact FiniteAssociationMLPSnapshot")
        return cls(
            input_features=snapshot.input_features,
            hidden_width=snapshot.hidden_width,
            weight1=snapshot.weight1.detach().numpy(),
            bias1=snapshot.bias1.detach().numpy(),
            weight2=snapshot.weight2.detach().numpy(),
            bias2=snapshot.bias2.detach().numpy(),
            weight3=snapshot.weight3.detach().numpy(),
            bias3=snapshot.bias3.detach().numpy(),
            parameter_sha256=snapshot.parameter_sha256,
        )

    def to_torch_snapshot(self) -> FiniteAssociationMLPSnapshot:
        return FiniteAssociationMLPSnapshot(
            input_features=self.input_features,
            hidden_width=self.hidden_width,
            weight1=torch.tensor(np.asarray(self.weight1), dtype=torch.float64),
            bias1=torch.tensor(np.asarray(self.bias1), dtype=torch.float64),
            weight2=torch.tensor(np.asarray(self.weight2), dtype=torch.float64),
            bias2=torch.tensor(np.asarray(self.bias2), dtype=torch.float64),
            weight3=torch.tensor(np.asarray(self.weight3), dtype=torch.float64),
            bias3=torch.tensor(np.asarray(self.bias3), dtype=torch.float64),
            parameter_sha256=self.parameter_sha256,
        )


def freeze_exact_population_mlp_snapshot(
    snapshot: FiniteAssociationMLPSnapshot,
) -> FrozenExactPopulationMLPSnapshot:
    """Copy a validated torch snapshot into read-only exact-lane custody."""

    return FrozenExactPopulationMLPSnapshot.from_torch_snapshot(snapshot)


@dataclass(frozen=True, eq=False)
class ExactPopulationOptimizationTrace:
    """Every-update objective, schedule, and unclipped gradient trace."""

    method: str
    update_indices: np.ndarray
    learning_rates: np.ndarray
    training_objectives: np.ndarray
    unclipped_gradient_norms: np.ndarray
    trace_sha256: str

    def __post_init__(self) -> None:
        method = _require_method(self.method)
        updates = _method_updates(method)
        indices = _immutable_array(self.update_indices, np.dtype(np.int64))
        if not np.array_equal(indices, np.arange(updates, dtype=np.int64)):
            raise ValueError("trace must contain every optimizer update canonically")
        object.__setattr__(self, "update_indices", indices)
        for name in (
            "learning_rates",
            "training_objectives",
            "unclipped_gradient_norms",
        ):
            value = _immutable_array(getattr(self, name), np.dtype(np.float64))
            if value.shape != (updates,) or not np.all(np.isfinite(value)):
                raise ValueError("%s has an invalid trace value" % name)
            if name != "learning_rates" and np.any(value < 0.0):
                raise ValueError("%s must be nonnegative" % name)
            object.__setattr__(self, name, value)
        expected_rates = np.asarray(
            [cosine_adamw_learning_rate(index, updates) for index in range(updates)],
            dtype=np.float64,
        )
        if not np.array_equal(self.learning_rates, expected_rates):
            raise ValueError("trace learning rates differ from the frozen schedule")
        _require_sha256(self.trace_sha256, name="trace_sha256")
        observed = _array_digest(
            b"heterodiff-a1-exact-population-optimization-trace-v2",
            self.update_indices,
            self.learning_rates,
            self.training_objectives,
            self.unclipped_gradient_norms,
        )
        if observed != self.trace_sha256:
            raise ValueError("optimization trace digest is inconsistent")

    @property
    def optimizer_updates(self) -> int:
        return int(self.update_indices.size)


def build_exact_population_optimization_trace(
    method: object,
    training_objectives: object,
    unclipped_gradient_norms: object,
) -> ExactPopulationOptimizationTrace:
    """Freeze the every-update values emitted by an isolated exact worker."""

    checked_method = _require_method(method)
    updates = _method_updates(checked_method)
    indices = np.arange(updates, dtype=np.int64)
    rates = np.asarray(
        [cosine_adamw_learning_rate(index, updates) for index in range(updates)],
        dtype=np.float64,
    )
    objectives = np.asarray(training_objectives, dtype=np.float64)
    gradients = np.asarray(unclipped_gradient_norms, dtype=np.float64)
    digest = _array_digest(
        b"heterodiff-a1-exact-population-optimization-trace-v2",
        indices,
        rates,
        objectives,
        gradients,
    )
    return ExactPopulationOptimizationTrace(
        method=checked_method,
        update_indices=indices,
        learning_rates=rates,
        training_objectives=objectives,
        unclipped_gradient_norms=gradients,
        trace_sha256=digest,
    )


@dataclass(frozen=True)
class ExactPopulationSplitDiagnostic:
    """Final-checkpoint exact diagnostic for one Cartesian reporting split."""

    split_name: str
    population_custody_sha256: str
    support_size: int
    raw_population_bce: float
    optimal_raw_population_bce: float
    physical_normalizer: float
    normalized_excess_bce: float

    def __post_init__(self) -> None:
        if self.split_name not in EXACT_SPLIT_NAMES:
            raise ValueError("split diagnostic name is not frozen")
        _require_sha256(
            self.population_custody_sha256,
            name="population_custody_sha256",
        )
        expected_size = math.prod(_EXPECTED_SPLIT_SHAPES[self.split_name])
        if (
            isinstance(self.support_size, (bool, np.bool_))
            or not isinstance(self.support_size, Integral)
            or int(self.support_size) != expected_size
        ):
            raise ValueError("split diagnostic support size changed")
        raw = _finite_float(
            self.raw_population_bce,
            name="raw_population_bce",
            nonnegative=True,
        )
        optimum = _finite_float(
            self.optimal_raw_population_bce,
            name="optimal_raw_population_bce",
            nonnegative=True,
        )
        normalizer = _finite_float(
            self.physical_normalizer,
            name="physical_normalizer",
            positive=True,
        )
        excess = _finite_float(
            self.normalized_excess_bce,
            name="normalized_excess_bce",
            nonnegative=True,
        )
        if raw + 1.0e-14 < optimum:
            raise ValueError("reported BCE is below the exact population optimum")
        expected_excess = max(0.0, (raw - optimum) / normalizer)
        if not math.isclose(excess, expected_excess, rel_tol=2.0e-12, abs_tol=2.0e-14):
            raise ValueError("normalized excess BCE is inconsistent")
        for name, value in (
            ("raw_population_bce", raw),
            ("optimal_raw_population_bce", optimum),
            ("physical_normalizer", normalizer),
            ("normalized_excess_bce", excess),
        ):
            object.__setattr__(self, name, value)

    @property
    def digest(self) -> str:
        return _record_digest(
            b"heterodiff-a1-exact-population-split-diagnostic-v2",
            self.split_name,
            self.population_custody_sha256,
            self.support_size,
            float(self.raw_population_bce).hex(),
            float(self.optimal_raw_population_bce).hex(),
            float(self.physical_normalizer).hex(),
            float(self.normalized_excess_bce).hex(),
        )


@dataclass(frozen=True)
class ExactPopulationResourceMeasurement:
    """Method-scoped measurement emitted by one fresh isolated worker."""

    measurement_scope: str
    isolated_process: bool
    elapsed_cpu_seconds: float
    elapsed_wall_seconds: float
    preparation_cpu_seconds: float
    preparation_wall_seconds: float
    optimizer_wall_seconds: float
    peak_rss_bytes: int
    peak_rss_method_id: str
    parameter_count: int
    forward_multiply_add_count: int
    preparation_included: bool
    guide_construction_included: bool
    training_included: bool
    certificate_included: bool
    evaluation_included: bool

    def __post_init__(self) -> None:
        if self.measurement_scope != EXACT_RESOURCE_SCOPE or self.isolated_process is not True:
            raise ValueError("resource measurement must cover one fresh isolated worker")
        cpu = _finite_float(
            self.elapsed_cpu_seconds, name="elapsed_cpu_seconds", positive=True
        )
        wall = _finite_float(
            self.elapsed_wall_seconds, name="elapsed_wall_seconds", positive=True
        )
        object.__setattr__(self, "elapsed_cpu_seconds", cpu)
        object.__setattr__(self, "elapsed_wall_seconds", wall)
        preparation_cpu = _finite_float(
            self.preparation_cpu_seconds,
            name="preparation_cpu_seconds",
            positive=True,
        )
        preparation_wall = _finite_float(
            self.preparation_wall_seconds,
            name="preparation_wall_seconds",
            positive=True,
        )
        optimizer_wall = _finite_float(
            self.optimizer_wall_seconds,
            name="optimizer_wall_seconds",
            positive=True,
        )
        if preparation_cpu > cpu + 1.0e-9:
            raise ValueError("preparation CPU time exceeds total process CPU time")
        if preparation_wall + optimizer_wall > wall + 1.0e-9:
            raise ValueError(
                "preparation plus optimizer wall time exceeds total wall time"
            )
        object.__setattr__(self, "preparation_cpu_seconds", preparation_cpu)
        object.__setattr__(self, "preparation_wall_seconds", preparation_wall)
        object.__setattr__(self, "optimizer_wall_seconds", optimizer_wall)
        if (
            isinstance(self.peak_rss_bytes, (bool, np.bool_))
            or not isinstance(self.peak_rss_bytes, Integral)
            or int(self.peak_rss_bytes) <= 0
        ):
            raise ValueError("peak_rss_bytes must be a positive integer byte count")
        if type(self.peak_rss_method_id) is not str or not self.peak_rss_method_id:
            raise TypeError("peak_rss_method_id must be a nonempty string")
        if any(
            isinstance(value, (bool, np.bool_))
            or not isinstance(value, Integral)
            or int(value) <= 0
            for value in (self.parameter_count, self.forward_multiply_add_count)
        ):
            raise ValueError("parameter and multiply-add counts must be positive integers")
        if not all(
            value is True
            for value in (
                self.preparation_included,
                self.guide_construction_included,
                self.training_included,
                self.certificate_included,
                self.evaluation_included,
            )
        ):
            raise ValueError("resource scope must include every method-stage cost")

    @property
    def digest(self) -> str:
        return _record_digest(
            b"heterodiff-a1-exact-population-resource-v3",
            self.measurement_scope,
            self.isolated_process,
            float(self.elapsed_cpu_seconds).hex(),
            float(self.elapsed_wall_seconds).hex(),
            float(self.preparation_cpu_seconds).hex(),
            float(self.preparation_wall_seconds).hex(),
            float(self.optimizer_wall_seconds).hex(),
            self.peak_rss_bytes,
            self.peak_rss_method_id,
            self.parameter_count,
            self.forward_multiply_add_count,
            self.preparation_included,
            self.guide_construction_included,
            self.training_included,
            self.certificate_included,
            self.evaluation_included,
        )


def _exact_classifier_sha256(
    *,
    method: str,
    fixture_sha256: str,
    exact_configuration_sha256: str,
    snapshot_sha256: str,
    certificate_sha256: str,
) -> str:
    return _record_digest(
        b"heterodiff-a1-exact-population-classifier-v2",
        _require_method(method),
        _require_sha256(fixture_sha256, name="fixture_sha256"),
        _require_sha256(
            exact_configuration_sha256,
            name="exact_configuration_sha256",
        ),
        _require_sha256(snapshot_sha256, name="snapshot_sha256"),
        _require_sha256(certificate_sha256, name="certificate_sha256"),
        "terminal-base" if method != EXACT_GUIDED_METHOD else "correct-guide-base",
        "2048*tanh(raw/2048)",
    )


def frozen_exact_population_classifier_sha256(
    *,
    method: object,
    fixture_sha256: object,
    exact_configuration_sha256: object,
    snapshot_sha256: object,
    certificate_sha256: object,
) -> str:
    """Return the full method/base/snapshot/certificate classifier identity."""

    return _exact_classifier_sha256(
        method=_require_method(method),
        fixture_sha256=_require_sha256(fixture_sha256, name="fixture_sha256"),
        exact_configuration_sha256=_require_sha256(
            exact_configuration_sha256,
            name="exact_configuration_sha256",
        ),
        snapshot_sha256=_require_sha256(snapshot_sha256, name="snapshot_sha256"),
        certificate_sha256=_require_sha256(
            certificate_sha256,
            name="certificate_sha256",
        ),
    )


@dataclass(frozen=True, eq=False)
class ExactPopulationMethodDiagnosticResult:
    """One seed/method exact fit; complete but never decision-bearing."""

    seed: int
    method: str
    run_key_sha256: str
    execution_runtime_sha256: str
    campaign_sha256: str
    preflight_sha256: str
    prepared_ledger_sha256: str
    running_ledger_sha256: str
    worker_session_sha256: str
    launch_id_sha256: str
    launch_authorization_sha256: str
    child_process_identity_sha256: str
    production_session: bool
    fixture_sha256: str
    exact_configuration_sha256: str
    initial_parameter_sha256: str
    final_snapshot: FrozenExactPopulationMLPSnapshot
    continuous_certificate: ContinuousCorrectionCertificate
    classifier_sha256: str
    optimization_trace: ExactPopulationOptimizationTrace
    split_diagnostics: Tuple[
        ExactPopulationSplitDiagnostic,
        ExactPopulationSplitDiagnostic,
        ExactPopulationSplitDiagnostic,
    ]
    resources: ExactPopulationResourceMeasurement
    final_checkpoint_only: bool
    numerical_integrity_passed: bool
    diagnostic_only: bool

    def __post_init__(self) -> None:
        _require_seed(self.seed)
        method = _require_method(self.method)
        for name in (
            "run_key_sha256",
            "execution_runtime_sha256",
            "campaign_sha256",
            "preflight_sha256",
            "prepared_ledger_sha256",
            "running_ledger_sha256",
            "worker_session_sha256",
            "launch_id_sha256",
            "launch_authorization_sha256",
            "child_process_identity_sha256",
            "fixture_sha256",
            "exact_configuration_sha256",
            "initial_parameter_sha256",
            "classifier_sha256",
        ):
            _require_sha256(getattr(self, name), name=name)
        if type(self.production_session) is not bool:
            raise TypeError("production_session must be boolean")
        if type(self.final_snapshot) is not FrozenExactPopulationMLPSnapshot:
            raise TypeError("final_snapshot must be immutable exact snapshot custody")
        if self.final_snapshot.hidden_width != _method_width(method):
            raise ValueError("final snapshot architecture differs from its method")
        require_matching_snapshot_continuous_certificate(
            self.final_snapshot.to_torch_snapshot(),
            self.continuous_certificate,
            frozen_fixture_sha256=self.fixture_sha256,
            guide_classifier_logit_grid=None,
        )
        expected_classifier = _exact_classifier_sha256(
            method=method,
            fixture_sha256=self.fixture_sha256,
            exact_configuration_sha256=self.exact_configuration_sha256,
            snapshot_sha256=self.final_snapshot.parameter_sha256,
            certificate_sha256=self.continuous_certificate.certificate_sha256,
        )
        if expected_classifier != self.classifier_sha256:
            raise ValueError("exact classifier digest is inconsistent")
        if (
            type(self.optimization_trace) is not ExactPopulationOptimizationTrace
            or self.optimization_trace.method != method
            or self.optimization_trace.optimizer_updates != _method_updates(method)
        ):
            raise ValueError("optimization trace does not match the exact method")
        if type(self.split_diagnostics) is not tuple or tuple(
            value.split_name for value in self.split_diagnostics
        ) != EXACT_SPLIT_NAMES:
            raise ValueError("split diagnostics must be train/validation/test")
        if not all(
            type(value) is ExactPopulationSplitDiagnostic
            for value in self.split_diagnostics
        ):
            raise TypeError("split diagnostics contain an invalid record")
        if type(self.resources) is not ExactPopulationResourceMeasurement:
            raise TypeError("resources must be an isolated-worker measurement")
        if (
            self.resources.parameter_count != _method_parameter_count(method)
            or self.resources.forward_multiply_add_count != _method_forward_macs(method)
        ):
            raise ValueError("resource model counts differ from the method")
        if not (
            self.final_checkpoint_only is True
            and self.numerical_integrity_passed is True
            and self.diagnostic_only is True
        ):
            raise ValueError("an exact result must be certified final-only diagnostic")

    @property
    def digest(self) -> str:
        return _record_digest(
            b"heterodiff-a1-exact-population-method-result-v5",
            self.seed,
            self.method,
            self.run_key_sha256,
            self.execution_runtime_sha256,
            self.campaign_sha256,
            self.preflight_sha256,
            self.prepared_ledger_sha256,
            self.running_ledger_sha256,
            self.worker_session_sha256,
            self.launch_id_sha256,
            self.launch_authorization_sha256,
            self.child_process_identity_sha256,
            self.production_session,
            self.fixture_sha256,
            self.exact_configuration_sha256,
            self.initial_parameter_sha256,
            self.final_snapshot.parameter_sha256,
            self.continuous_certificate.certificate_sha256,
            self.classifier_sha256,
            self.optimization_trace.trace_sha256,
            tuple(value.digest for value in self.split_diagnostics),
            self.resources.digest,
            self.final_checkpoint_only,
            self.numerical_integrity_passed,
            self.diagnostic_only,
        )


_OPTIMIZER_COMPLETION_CONSTRUCTION_KEY = object()
_OPTIMIZER_COMPLETION_FINALIZER_KEY = object()
_COMPLETED_EXECUTION_CONSTRUCTION_KEY = object()


class FrozenExactPopulationOptimizerCompletion:
    """Executor-minted single-use proof that the full method run completed."""

    __slots__ = (
        "_receipt_bytes",
        "optimizer_completion_sha256",
        "result_sha256",
        "worker_process_id",
        "_consumed",
        "_locked",
    )

    def __init__(
        self,
        *,
        result: ExactPopulationMethodDiagnosticResult,
        permit: FrozenExactPopulationExecutionPermit,
        expected_optimizer_steps: object,
        observed_optimizer_steps: object,
        rolling_optimizer_transcript_sha256: object,
        _construction_key: object,
    ) -> None:
        if _construction_key is not _OPTIMIZER_COMPLETION_CONSTRUCTION_KEY:
            raise TypeError("optimizer completion receipts are executor-minted")
        if type(result) is not ExactPopulationMethodDiagnosticResult:
            raise TypeError("optimizer completion requires an exact method result")
        if type(permit) is not FrozenExactPopulationExecutionPermit or not permit._consumed:
            raise RuntimeError("optimizer completion requires a consumed exact permit")
        expected = _method_updates(result.method)
        observed = (
            -1
            if isinstance(observed_optimizer_steps, (bool, np.bool_))
            or not isinstance(observed_optimizer_steps, Integral)
            else int(observed_optimizer_steps)
        )
        if (
            isinstance(expected_optimizer_steps, (bool, np.bool_))
            or not isinstance(expected_optimizer_steps, Integral)
            or int(expected_optimizer_steps) != expected
            or observed != expected
            or result.optimization_trace.optimizer_updates != expected
        ):
            raise ValueError("optimizer completion step count is inconsistent")
        rolling = _require_sha256(
            rolling_optimizer_transcript_sha256,
            name="rolling_optimizer_transcript_sha256",
        )
        if result.production_session is not True:
            raise RuntimeError("executor completion cannot certify an emulated session")
        if result.final_snapshot.parameter_sha256 == result.initial_parameter_sha256:
            raise RuntimeError("optimizer completion cannot certify unchanged parameters")
        permit_bindings = {
            "seed": permit.seed,
            "method": permit.method,
            "run_key_sha256": permit.run_key_sha256,
            "execution_runtime_sha256": permit.execution_runtime_sha256,
            "campaign_sha256": permit.campaign_sha256,
            "preflight_sha256": permit.preflight_sha256,
            "prepared_ledger_sha256": permit.prepared_ledger_sha256,
            "running_ledger_sha256": permit.running_ledger_sha256,
            "worker_session_sha256": permit.worker_session_sha256,
            "launch_id_sha256": permit.launch_id_sha256,
            "launch_authorization_sha256": permit.launch_authorization_sha256,
            "child_process_identity_sha256": (
                permit.child_process_identity_sha256
            ),
            "production_session": permit.production_session,
        }
        if any(
            getattr(result, name) != expected_value
            for name, expected_value in permit_bindings.items()
        ) or permit.worker_process_id != os.getpid():
            raise RuntimeError("optimizer completion result differs from its permit")
        receipt = {
            "schema": "heterodiff-a1-exact-optimizer-completion-v2",
            "production_eligible": True,
            "seed": result.seed,
            "method": result.method,
            "launch_id_sha256": result.launch_id_sha256,
            "launch_authorization_sha256": result.launch_authorization_sha256,
            "child_process_identity_sha256": result.child_process_identity_sha256,
            "worker_session_sha256": result.worker_session_sha256,
            "run_key_sha256": result.run_key_sha256,
            "campaign_sha256": result.campaign_sha256,
            "execution_runtime_sha256": result.execution_runtime_sha256,
            "preflight_sha256": result.preflight_sha256,
            "prepared_ledger_sha256": result.prepared_ledger_sha256,
            "running_ledger_sha256": result.running_ledger_sha256,
            "expected_optimizer_steps": expected,
            "observed_optimizer_steps": observed,
            "initial_parameter_sha256": result.initial_parameter_sha256,
            "final_parameter_sha256": result.final_snapshot.parameter_sha256,
            "rolling_optimizer_transcript_sha256": rolling,
            "trace_sha256": result.optimization_trace.trace_sha256,
            "certificate_sha256": result.continuous_certificate.certificate_sha256,
            "classifier_sha256": result.classifier_sha256,
            "split_diagnostic_sha256": [
                value.digest for value in result.split_diagnostics
            ],
            "resource_sha256": result.resources.digest,
            "result_sha256": result.digest,
            "worker_process_id": os.getpid(),
            "completed_unix_ns": time.time_ns(),
        }
        encoded = json.dumps(
            receipt,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        completion_sha256 = hashlib.sha256(encoded).hexdigest()
        receipt["optimizer_completion_sha256"] = completion_sha256
        object.__setattr__(
            self,
            "_receipt_bytes",
            json.dumps(
                receipt,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            ).encode("ascii"),
        )
        object.__setattr__(self, "optimizer_completion_sha256", completion_sha256)
        object.__setattr__(self, "result_sha256", result.digest)
        object.__setattr__(self, "worker_process_id", os.getpid())
        object.__setattr__(self, "_consumed", False)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("optimizer completion receipt is immutable")
        object.__setattr__(self, name, value)

    @property
    def receipt(self) -> dict:
        return json.loads(self._receipt_bytes.decode("ascii"))

    def _consume_for_finalization(
        self,
        reopened_result: ExactPopulationMethodDiagnosticResult,
        *,
        _finalizer_key: object,
    ) -> dict:
        if _finalizer_key is not _OPTIMIZER_COMPLETION_FINALIZER_KEY:
            raise TypeError("optimizer completion is consumed only by the finalizer")
        if self._consumed:
            raise RuntimeError("optimizer completion receipt was already consumed")
        if os.getpid() != self.worker_process_id:
            raise RuntimeError("optimizer completion belongs to another process")
        if (
            type(reopened_result) is not ExactPopulationMethodDiagnosticResult
            or reopened_result.digest != self.result_sha256
        ):
            raise RuntimeError("reopened result differs from optimizer completion")
        object.__setattr__(self, "_consumed", True)
        return self.receipt


class CompletedExactPopulationExecution:
    """Private executor return pairing a result with its completion proof."""

    __slots__ = ("result", "optimizer_completion", "_locked")

    def __init__(
        self,
        result: ExactPopulationMethodDiagnosticResult,
        optimizer_completion: FrozenExactPopulationOptimizerCompletion,
        *,
        _construction_key: object,
    ) -> None:
        if _construction_key is not _COMPLETED_EXECUTION_CONSTRUCTION_KEY:
            raise TypeError("completed exact executions are executor-minted")
        if (
            type(result) is not ExactPopulationMethodDiagnosticResult
            or type(optimizer_completion)
            is not FrozenExactPopulationOptimizerCompletion
            or optimizer_completion.result_sha256 != result.digest
        ):
            raise RuntimeError("completed execution result/receipt is inconsistent")
        object.__setattr__(self, "result", result)
        object.__setattr__(self, "optimizer_completion", optimizer_completion)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("completed exact execution is immutable")
        object.__setattr__(self, name, value)


def _exact_optimizer_transcript_seed_sha256(
    permit: FrozenExactPopulationExecutionPermit,
    *,
    initial_parameter_sha256: object,
    expected_optimizer_steps: object,
) -> str:
    """Bind an update transcript to its complete pre-update run custody."""

    if type(permit) is not FrozenExactPopulationExecutionPermit or not permit._consumed:
        raise RuntimeError("optimizer transcript requires a consumed exact permit")
    initial = _require_sha256(
        initial_parameter_sha256, name="initial_parameter_sha256"
    )
    expected = _method_updates(permit.method)
    if (
        isinstance(expected_optimizer_steps, (bool, np.bool_))
        or not isinstance(expected_optimizer_steps, Integral)
        or int(expected_optimizer_steps) != expected
    ):
        raise ValueError("optimizer transcript expected step count changed")
    return _record_digest(
        b"heterodiff-a1-exact-optimizer-update-transcript-seed-v2",
        permit.seed,
        permit.method,
        permit.run_key_sha256,
        permit.worker_session_sha256,
        permit.launch_id_sha256,
        permit.launch_authorization_sha256,
        permit.child_process_identity_sha256,
        permit.execution_runtime_sha256,
        permit.campaign_sha256,
        permit.preflight_sha256,
        permit.prepared_ledger_sha256,
        permit.running_ledger_sha256,
        initial,
        expected,
    )


def _require_exact_optimizer_transcript_final_parameter(
    last_post_update_parameter_sha256: object,
    final_parameter_sha256: object,
) -> str:
    last_update = _require_sha256(
        last_post_update_parameter_sha256,
        name="last_post_update_parameter_sha256",
    )
    final = _require_sha256(
        final_parameter_sha256, name="final_parameter_sha256"
    )
    if last_update != final:
        raise RuntimeError(
            "exact final snapshot differs from the last optimizer transcript update"
        )
    return final


def _exact_payload_keys(
    value: object, expected: Tuple[str, ...], *, name: str
) -> dict:
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError("%s has an invalid exact-result payload schema" % name)
    return value


def exact_population_method_result_payload(
    result: ExactPopulationMethodDiagnosticResult,
) -> dict:
    """Return a weights-only-safe payload with no live Python object graph."""

    if type(result) is not ExactPopulationMethodDiagnosticResult:
        raise TypeError("result must be an exact method diagnostic")
    result.__post_init__()
    snapshot = {
        field.name: (
            torch.tensor(
                np.asarray(getattr(result.final_snapshot, field.name)),
                dtype=torch.float64,
            )
            if field.name.startswith("weight") or field.name.startswith("bias")
            else getattr(result.final_snapshot, field.name)
        )
        for field in fields(FrozenExactPopulationMLPSnapshot)
    }
    trace = {
        field.name: (
            torch.tensor(
                np.asarray(getattr(result.optimization_trace, field.name)),
                dtype=(
                    torch.int64
                    if field.name == "update_indices"
                    else torch.float64
                ),
            )
            if field.name
            in (
                "update_indices",
                "learning_rates",
                "training_objectives",
                "unclipped_gradient_norms",
            )
            else getattr(result.optimization_trace, field.name)
        )
        for field in fields(ExactPopulationOptimizationTrace)
    }
    return {
        "schema": _METHOD_RESULT_PAYLOAD_SCHEMA,
        "seed": result.seed,
        "method": result.method,
        "run_key_sha256": result.run_key_sha256,
        "execution_runtime_sha256": result.execution_runtime_sha256,
        "campaign_sha256": result.campaign_sha256,
        "preflight_sha256": result.preflight_sha256,
        "prepared_ledger_sha256": result.prepared_ledger_sha256,
        "running_ledger_sha256": result.running_ledger_sha256,
        "worker_session_sha256": result.worker_session_sha256,
        "launch_id_sha256": result.launch_id_sha256,
        "launch_authorization_sha256": result.launch_authorization_sha256,
        "child_process_identity_sha256": result.child_process_identity_sha256,
        "production_session": result.production_session,
        "fixture_sha256": result.fixture_sha256,
        "exact_configuration_sha256": result.exact_configuration_sha256,
        "initial_parameter_sha256": result.initial_parameter_sha256,
        "final_snapshot": snapshot,
        "continuous_certificate": asdict(result.continuous_certificate),
        "classifier_sha256": result.classifier_sha256,
        "optimization_trace": trace,
        "split_diagnostics": tuple(
            asdict(value) for value in result.split_diagnostics
        ),
        "resources": asdict(result.resources),
        "final_checkpoint_only": result.final_checkpoint_only,
        "numerical_integrity_passed": result.numerical_integrity_passed,
        "diagnostic_only": result.diagnostic_only,
        "result_sha256": result.digest,
    }


def exact_population_method_result_from_payload(
    payload: object,
) -> ExactPopulationMethodDiagnosticResult:
    """Reconstruct and fully revalidate one plain method-result payload."""

    top_level = (
        "schema",
        "seed",
        "method",
        "run_key_sha256",
        "execution_runtime_sha256",
        "campaign_sha256",
        "preflight_sha256",
        "prepared_ledger_sha256",
        "running_ledger_sha256",
        "worker_session_sha256",
        "launch_id_sha256",
        "launch_authorization_sha256",
        "child_process_identity_sha256",
        "production_session",
        "fixture_sha256",
        "exact_configuration_sha256",
        "initial_parameter_sha256",
        "final_snapshot",
        "continuous_certificate",
        "classifier_sha256",
        "optimization_trace",
        "split_diagnostics",
        "resources",
        "final_checkpoint_only",
        "numerical_integrity_passed",
        "diagnostic_only",
        "result_sha256",
    )
    values = _exact_payload_keys(payload, top_level, name="payload")
    if values["schema"] != _METHOD_RESULT_PAYLOAD_SCHEMA:
        raise ValueError("exact method-result payload version is unsupported")
    snapshot_names = tuple(
        field.name for field in fields(FrozenExactPopulationMLPSnapshot)
    )
    snapshot_values = _exact_payload_keys(
        values["final_snapshot"], snapshot_names, name="final_snapshot"
    )
    for name in ("weight1", "bias1", "weight2", "bias2", "weight3", "bias3"):
        tensor = snapshot_values[name]
        if (
            not isinstance(tensor, torch.Tensor)
            or tensor.device.type != "cpu"
            or tensor.dtype != torch.float64
        ):
            raise TypeError("saved snapshot tensors must be CPU float64")
        snapshot_values[name] = tensor.detach().numpy()
    snapshot = FrozenExactPopulationMLPSnapshot(**snapshot_values)
    certificate_names = tuple(
        field.name for field in fields(ContinuousCorrectionCertificate)
    )
    certificate = ContinuousCorrectionCertificate(
        **_exact_payload_keys(
            values["continuous_certificate"],
            certificate_names,
            name="continuous_certificate",
        )
    )
    trace_names = tuple(field.name for field in fields(ExactPopulationOptimizationTrace))
    trace_values = _exact_payload_keys(
        values["optimization_trace"], trace_names, name="optimization_trace"
    )
    for name, dtype in (
        ("update_indices", torch.int64),
        ("learning_rates", torch.float64),
        ("training_objectives", torch.float64),
        ("unclipped_gradient_norms", torch.float64),
    ):
        tensor = trace_values[name]
        if (
            not isinstance(tensor, torch.Tensor)
            or tensor.device.type != "cpu"
            or tensor.dtype != dtype
        ):
            raise TypeError("saved optimization trace has an invalid tensor")
        trace_values[name] = tensor.detach().numpy()
    trace = ExactPopulationOptimizationTrace(**trace_values)
    split_values = values["split_diagnostics"]
    if type(split_values) not in (tuple, list) or len(split_values) != 3:
        raise ValueError("saved split diagnostics are incomplete")
    split_names = tuple(field.name for field in fields(ExactPopulationSplitDiagnostic))
    splits = tuple(
        ExactPopulationSplitDiagnostic(
            **_exact_payload_keys(value, split_names, name="split_diagnostic")
        )
        for value in split_values
    )
    resource_names = tuple(
        field.name for field in fields(ExactPopulationResourceMeasurement)
    )
    resources = ExactPopulationResourceMeasurement(
        **_exact_payload_keys(values["resources"], resource_names, name="resources")
    )
    result = ExactPopulationMethodDiagnosticResult(
        seed=values["seed"],
        method=values["method"],
        run_key_sha256=values["run_key_sha256"],
        execution_runtime_sha256=values["execution_runtime_sha256"],
        campaign_sha256=values["campaign_sha256"],
        preflight_sha256=values["preflight_sha256"],
        prepared_ledger_sha256=values["prepared_ledger_sha256"],
        running_ledger_sha256=values["running_ledger_sha256"],
        worker_session_sha256=values["worker_session_sha256"],
        launch_id_sha256=values["launch_id_sha256"],
        launch_authorization_sha256=values["launch_authorization_sha256"],
        child_process_identity_sha256=values[
            "child_process_identity_sha256"
        ],
        production_session=values["production_session"],
        fixture_sha256=values["fixture_sha256"],
        exact_configuration_sha256=values["exact_configuration_sha256"],
        initial_parameter_sha256=values["initial_parameter_sha256"],
        final_snapshot=snapshot,
        continuous_certificate=certificate,
        classifier_sha256=values["classifier_sha256"],
        optimization_trace=trace,
        split_diagnostics=splits,
        resources=resources,
        final_checkpoint_only=values["final_checkpoint_only"],
        numerical_integrity_passed=values["numerical_integrity_passed"],
        diagnostic_only=values["diagnostic_only"],
    )
    if values["result_sha256"] != result.digest:
        raise ValueError("saved exact method-result digest is inconsistent")
    return result


def load_exact_population_method_result(
    path: object, *, expected_sha256: object
) -> ExactPopulationMethodDiagnosticResult:
    """Digest-check and weights-only-load one non-aggregate method result."""

    result_path = Path(path)
    expected = _require_sha256(expected_sha256, name="expected_sha256")
    with result_path.open("rb") as handle:
        payload_bytes = handle.read(_METHOD_RESULT_PAYLOAD_MAXIMUM_BYTES + 1)
    if len(payload_bytes) > _METHOD_RESULT_PAYLOAD_MAXIMUM_BYTES:
        raise ValueError("exact method-result payload exceeds the byte limit")
    if hashlib.sha256(payload_bytes).hexdigest() != expected:
        raise ValueError("exact method-result file digest differs from its receipt")
    payload = torch.load(
        io.BytesIO(payload_bytes), map_location="cpu", weights_only=True
    )
    return exact_population_method_result_from_payload(payload)


@dataclass(frozen=True, eq=False)
class AssociationExactPopulationDiagnosticResult:
    """Complete or explicitly permit-blocked exact-lane record."""

    preflight_sha256: str
    execution_contract_sha256: str
    source_sha256: str
    exact_configuration_sha256: str
    fixture_sha256: str
    split_custody_sha256: Tuple[str, str, str]
    oracle_product_control_custody_sha256: str
    oracle_product_positive_maximum_absolute_logit: float
    oracle_product_control_passed: bool
    seed_custodies: Tuple[FrozenExactPopulationSeedCustody, ...]
    environment: Optional[FrozenAssociationTrainingEnvironment]
    executed: bool
    optimizer_steps_taken: int
    method_results: Tuple[ExactPopulationMethodDiagnosticResult, ...]
    status: str
    notes: Tuple[str, ...]
    scientific_decision_eligible: bool
    product_control_optimized: bool

    def __post_init__(self) -> None:
        for name in (
            "preflight_sha256",
            "execution_contract_sha256",
            "source_sha256",
            "exact_configuration_sha256",
            "fixture_sha256",
            "oracle_product_control_custody_sha256",
        ):
            _require_sha256(getattr(self, name), name=name)
        if (
            self.execution_contract_sha256
            != FrozenExactPopulationExecutionContract().digest
        ):
            raise ValueError(
                "result execution contract is not the ratified exact contract"
            )
        if self.exact_configuration_sha256 != (
            frozen_exact_population_configuration_sha256(
                source_sha256=self.source_sha256
            )
        ):
            raise ValueError(
                "result exact configuration is inconsistent with its source"
            )
        if type(self.split_custody_sha256) is not tuple or len(
            self.split_custody_sha256
        ) != 3:
            raise TypeError("split_custody_sha256 must contain three digests")
        for value in self.split_custody_sha256:
            _require_sha256(value, name="split_custody_sha256")
        if type(self.seed_custodies) is not tuple or tuple(
            value.seed for value in self.seed_custodies
        ) != PAIRED_SEEDS:
            raise ValueError("result seed custody is not canonical")
        if type(self.method_results) is not tuple:
            raise TypeError("method_results must be a tuple")
        if type(self.notes) is not tuple or not all(
            type(value) is str and value for value in self.notes
        ):
            raise TypeError("notes must be a tuple of nonempty strings")
        if not isinstance(self.executed, bool):
            raise TypeError("executed must be boolean")
        if (
            isinstance(self.optimizer_steps_taken, (bool, np.bool_))
            or not isinstance(self.optimizer_steps_taken, Integral)
            or int(self.optimizer_steps_taken) < 0
        ):
            raise ValueError("optimizer_steps_taken must be nonnegative integer")
        if self.scientific_decision_eligible is not False:
            raise ValueError("the exact lane is diagnostic and never decision-bearing")
        if self.product_control_optimized is not False:
            raise ValueError("an exact result cannot claim a trained product control")
        product_maximum = _finite_float(
            self.oracle_product_positive_maximum_absolute_logit,
            name="oracle_product_positive_maximum_absolute_logit",
            nonnegative=True,
        )
        expected_product_pass = (
            product_maximum <= ORACLE_PRODUCT_POSITIVE_LOGIT_TOLERANCE
        )
        if self.oracle_product_control_passed is not expected_product_pass:
            raise ValueError("oracle product-control pass flag disagrees with its gate")
        object.__setattr__(
            self,
            "oracle_product_positive_maximum_absolute_logit",
            product_maximum,
        )
        if not self.executed:
            if (
                self.environment is not None
                or self.optimizer_steps_taken != 0
                or self.method_results
                or self.status != "PERMIT_REQUIRED_UNEXECUTED"
            ):
                raise ValueError("an unexecuted exact result must be empty and permit-blocked")
            return
        if (
            type(self.environment) is not FrozenAssociationTrainingEnvironment
            or not self.environment.versions_match
            or not self.environment.execution_mode_matches
        ):
            raise ValueError("executed result environment is not the frozen runtime")
        if self.status != "DIAGNOSTIC_COMPLETE_NONDECISION":
            raise ValueError("an executed exact result has an invalid status")
        if self.oracle_product_control_passed is not True:
            raise ValueError("complete exact diagnostics require the oracle algebra gate")
        expected = tuple(
            (seed, method)
            for seed in PAIRED_SEEDS
            for method in EXACT_POPULATION_METHODS
        )
        observed = tuple((value.seed, value.method) for value in self.method_results)
        if observed != expected:
            raise ValueError("complete exact results are not canonical/all-seed")
        if self.optimizer_steps_taken != EXACT_EXPECTED_TOTAL_OPTIMIZER_STEPS:
            raise ValueError("complete exact result has the wrong total step count")
        custody_by_seed = {value.seed: value for value in self.seed_custodies}
        for result in self.method_results:
            expected_initial = (
                custody_by_seed[result.seed].stronger_direct_initial_parameter_sha256
                if result.method == EXACT_STRONG_DIRECT_METHOD
                else custody_by_seed[result.seed].primary_initial_parameter_sha256
            )
            if (
                result.preflight_sha256 != self.preflight_sha256
                or result.fixture_sha256 != self.fixture_sha256
                or result.exact_configuration_sha256
                != self.exact_configuration_sha256
                or result.initial_parameter_sha256 != expected_initial
                or tuple(
                    value.population_custody_sha256
                    for value in result.split_diagnostics
                )
                != self.split_custody_sha256
            ):
                raise ValueError("method result is not bound to top-level custody")

    @property
    def digest(self) -> str:
        environment = (
            "no-environment"
            if self.environment is None
            else (
                self.environment.python_version,
                self.environment.numpy_version,
                self.environment.scipy_version,
                self.environment.torch_version,
                self.environment.torch_cpu_only,
                self.environment.torch_threads,
                self.environment.torch_interop_threads,
                self.environment.deterministic_algorithms,
            )
        )
        return _record_digest(
            b"heterodiff-a1-exact-population-complete-result-v3",
            self.preflight_sha256,
            self.execution_contract_sha256,
            self.source_sha256,
            self.exact_configuration_sha256,
            self.fixture_sha256,
            self.split_custody_sha256,
            self.oracle_product_control_custody_sha256,
            float(self.oracle_product_positive_maximum_absolute_logit).hex(),
            self.oracle_product_control_passed,
            tuple(value.custody_sha256 for value in self.seed_custodies),
            environment,
            self.executed,
            self.optimizer_steps_taken,
            tuple(value.digest for value in self.method_results),
            self.status,
            self.notes,
            self.scientific_decision_eligible,
            self.product_control_optimized,
        )


def _population_support(
    time_partition: np.ndarray, pair_partition: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    times = np.repeat(time_partition, pair_partition.shape[0])
    pairs = np.tile(pair_partition, (time_partition.size, 1))
    return times, pairs[:, 0], pairs[:, 1]


def _build_split_population_custody(
    fixture: FrozenAssociationResidualFixture,
    fixture_sha256: str,
    split_name: str,
) -> FrozenAssociationExactPopulationSplitCustody:
    splits = frozen_association_residual_splits(fixture)
    time_partition = np.asarray(getattr(splits, "%s_times" % split_name))
    pair_partition = np.asarray(getattr(splits, "%s_pairs" % split_name))
    time_indices, state_indices, observation_indices = _population_support(
        time_partition, pair_partition
    )
    times = np.asarray(fixture.times)[time_indices]
    latent = torch.tensor(
        np.asarray(fixture.latent_space.states, dtype=np.int64)[state_indices],
        dtype=torch.int64,
    )
    retained = np.asarray(fixture.retained_observation_space.states, dtype=np.int64)
    anchors = torch.tensor(retained[observation_indices], dtype=torch.int64)
    overflow = torch.zeros(time_indices.size, dtype=torch.bool)
    features = finite_association_features(
        torch.tensor(times, dtype=torch.float64), latent, anchors, overflow
    ).detach().numpy()
    population = fixture.population
    terminal = population.optimal_log_density_ratio[
        -1, state_indices, observation_indices
    ]
    guide_grid = np.log(np.asarray(fixture.guide_density_grid)) - np.log(
        population.observation_marginal_density
    )[None, None, :]
    guide = guide_grid[time_indices, state_indices, observation_indices]
    optimal = population.optimal_log_density_ratio[
        time_indices, state_indices, observation_indices
    ]
    joint = population.joint_mass[time_indices, state_indices, observation_indices]
    product = population.product_mass[
        time_indices, state_indices, observation_indices
    ]
    support = _array_digest(
        b"heterodiff-a1-exact-population-split-support-v2",
        time_partition,
        pair_partition,
        time_indices,
        state_indices,
        observation_indices,
    )
    tensors = _array_digest(
        b"heterodiff-a1-exact-population-split-tensors-v2",
        times,
        features,
        terminal,
        guide,
        optimal,
        joint,
        product,
    )
    custody = _record_digest(
        b"heterodiff-a1-exact-population-split-custody-v2",
        split_name,
        fixture_sha256,
        splits.digest,
        support,
        tensors,
    )
    return FrozenAssociationExactPopulationSplitCustody(
        split_name=split_name,
        fixture_sha256=fixture_sha256,
        split_sha256=splits.digest,
        time_partition_indices=time_partition,
        pair_partition=pair_partition,
        time_indices=time_indices,
        state_indices=state_indices,
        observation_indices=observation_indices,
        direct_times=times,
        features=features,
        terminal_classifier_logits=terminal,
        guide_classifier_logits=guide,
        exact_optimal_logits=optimal,
        joint_mass=joint,
        product_mass=product,
        support_sha256=support,
        tensor_sha256=tensors,
        custody_sha256=custody,
    )


def _build_oracle_product_control(
    fixture: FrozenAssociationResidualFixture,
    fixture_sha256: str,
) -> FrozenOracleProductPositiveControlCustody:
    equal_mass = np.asarray(fixture.population.product_mass, dtype=np.float64)
    if equal_mass.shape != (33, 20, 21):
        raise ArithmeticError("oracle product-positive domain is not 33 x 20 x 21")
    optimal = np.log(equal_mass) - np.log(equal_mass)
    maximum = float(np.max(np.abs(optimal)))
    tensor = _array_digest(
        b"heterodiff-a1-oracle-product-positive-tensors-v3",
        equal_mass,
        optimal,
    )
    custody = _record_digest(
        b"heterodiff-a1-oracle-product-positive-custody-v3",
        fixture_sha256,
        maximum,
        maximum <= ORACLE_PRODUCT_POSITIVE_LOGIT_TOLERANCE,
        True,
        False,
        tensor,
    )
    return FrozenOracleProductPositiveControlCustody(
        fixture_sha256=fixture_sha256,
        equal_class_mass=equal_mass,
        pointwise_optimal_logits=optimal,
        maximum_absolute_logit=maximum,
        passed=maximum <= ORACLE_PRODUCT_POSITIVE_LOGIT_TOLERANCE,
        oracle_only=True,
        optimizer_execution_authorized=False,
        tensor_sha256=tensor,
        custody_sha256=custody,
    )


def _initial_parameter_sha256(torch_seed: int, hidden_width: int) -> str:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(torch_seed)
    model = FiniteAssociationCorrectionNetwork(
        generator=generator,
        input_features=BASE_FEATURE_COUNT,
        hidden_width=hidden_width,
    )
    return snapshot_finite_association_mlp(model).parameter_sha256


def _build_seed_custody(seed: int) -> FrozenExactPopulationSeedCustody:
    checked = _require_seed(seed)
    model_child = np.random.SeedSequence(checked).spawn(3)[1]
    state = model_child.generate_state(1, dtype=np.uint64)
    if state.shape != (1,):
        raise ArithmeticError("model seed child did not return one uint64 value")
    torch_seed = int(state[0])
    primary = _initial_parameter_sha256(torch_seed, PRIMARY_HIDDEN_WIDTH)
    stronger = _initial_parameter_sha256(torch_seed, STRONG_DIRECT_HIDDEN_WIDTH)
    custody = _record_digest(
        b"heterodiff-a1-exact-population-seed-custody-v2",
        checked,
        torch_seed,
        primary,
        stronger,
    )
    return FrozenExactPopulationSeedCustody(
        seed=checked,
        torch_generator_seed=torch_seed,
        primary_initial_parameter_sha256=primary,
        stronger_direct_initial_parameter_sha256=stronger,
        custody_sha256=custody,
    )


def prepare_frozen_association_exact_population_diagnostic(
) -> PreparedAssociationExactPopulationDiagnostic:
    """Prepare complete immutable custody without constructing an optimizer."""

    prerequisite = run_association_residual_prerequisite_gate()
    gate_digests = (
        prerequisite.generator_digest,
        prerequisite.observation_digest,
        prerequisite.population_digest,
        prerequisite.guide_digest,
        prerequisite.split_digest,
    )
    if not prerequisite.passed or gate_digests != FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS:
        raise RuntimeError("the frozen A1 prerequisite gate or digest changed")
    fixture = build_frozen_association_residual_fixture()
    actual_digests = frozen_association_fixture_content_digests(fixture)
    if actual_digests != FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS:
        raise RuntimeError("the constructed fixture contents changed after the gate")
    fixture_token = frozen_association_fixture_sha256(actual_digests)
    populations = tuple(
        _build_split_population_custody(fixture, fixture_token, split_name)
        for split_name in EXACT_SPLIT_NAMES
    )
    product = _build_oracle_product_control(fixture, fixture_token)
    seeds = tuple(_build_seed_custody(seed) for seed in PAIRED_SEEDS)
    contract = FrozenExactPopulationExecutionContract()
    source = frozen_association_training_source_sha256()
    sampled_configuration = frozen_association_training_configuration_sha256(
        source_sha256=source
    )
    exact_configuration = frozen_exact_population_configuration_sha256(
        source_sha256=source
    )
    preflight = _exact_preflight_sha256_from_parts(
        fixture_content_sha256=actual_digests,
        populations=populations,
        oracle_product_control=product,
        seed_custodies=seeds,
        execution_contract=contract,
        source_sha256=source,
        sampled_configuration_sha256=sampled_configuration,
        exact_configuration_sha256=exact_configuration,
    )
    return PreparedAssociationExactPopulationDiagnostic(
        fixture=fixture,
        fixture_content_sha256=actual_digests,
        populations=populations,
        oracle_product_control=product,
        seed_custodies=seeds,
        execution_contract=contract,
        source_sha256=source,
        sampled_configuration_sha256=sampled_configuration,
        exact_configuration_sha256=exact_configuration,
        preflight_sha256=preflight,
    )


def initialize_exact_population_model(
    prepared: PreparedAssociationExactPopulationDiagnostic,
    seed: object,
    method: object,
) -> FiniteAssociationCorrectionNetwork:
    """Return one fresh, digest-checked model without optimizer construction."""

    if type(prepared) is not PreparedAssociationExactPopulationDiagnostic:
        raise TypeError("prepared must be exact-population preparation")
    checked_seed = _require_seed(seed)
    checked_method = _require_method(method)
    custody = next(value for value in prepared.seed_custodies if value.seed == checked_seed)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(custody.torch_generator_seed)
    model = FiniteAssociationCorrectionNetwork(
        generator=generator,
        input_features=BASE_FEATURE_COUNT,
        hidden_width=_method_width(checked_method),
    )
    observed = snapshot_finite_association_mlp(model).parameter_sha256
    expected = (
        custody.stronger_direct_initial_parameter_sha256
        if checked_method == EXACT_STRONG_DIRECT_METHOD
        else custody.primary_initial_parameter_sha256
    )
    if observed != expected:
        raise RuntimeError("fresh exact-population model missed its custody digest")
    return model


def exact_masked_population_bce(
    logits: object,
    positive_mass: object,
    negative_mass: object,
    *,
    normalized: bool = False,
) -> torch.Tensor:
    """Return physical equal-prior BCE without classwise renormalization."""

    values = _torch_float64_vector(logits, name="logits")
    positive = _torch_float64_vector(positive_mass, name="positive_mass")
    negative = _torch_float64_vector(negative_mass, name="negative_mass")
    if positive.shape != values.shape or negative.shape != values.shape:
        raise ValueError("logits and physical masses must share one shape")
    if bool(torch.any(positive <= 0.0).detach().item()) or bool(
        torch.any(negative <= 0.0).detach().item()
    ):
        raise ValueError("physical class masses must be strictly positive")
    if type(normalized) is not bool:
        raise TypeError("normalized must be boolean")
    risk = 0.5 * torch.sum(
        positive * torch_functional.softplus(-values)
        + negative * torch_functional.softplus(values)
    )
    if normalized:
        risk = risk / (0.5 * torch.sum(positive + negative))
    if risk.dtype != torch.float64 or risk.ndim != 0 or not bool(
        torch.isfinite(risk).detach().item()
    ):
        raise ArithmeticError("exact masked-population BCE is invalid")
    return risk


def exact_population_training_bce(
    logits: object,
    positive_mass: object,
    negative_mass: object,
) -> torch.Tensor:
    """Return the authoritative Section 6 full-batch training objective."""

    values = _torch_float64_vector(logits, name="logits")
    if values.numel() != EXACT_POPULATION_SUPPORT_SIZE:
        raise ValueError("exact training objective requires all 16*61 train points")
    return exact_masked_population_bce(
        values, positive_mass, negative_mass, normalized=False
    ) / float(EXACT_TRAIN_TIME_COUNT)


def _population_for_split(
    prepared: PreparedAssociationExactPopulationDiagnostic, split_name: object
) -> FrozenAssociationExactPopulationSplitCustody:
    if type(split_name) is not str or split_name not in EXACT_SPLIT_NAMES:
        raise ValueError("split_name must be train, validation, or test")
    return prepared.populations[EXACT_SPLIT_NAMES.index(split_name)]


def exact_population_model_logits(
    model: FiniteAssociationCorrectionNetwork,
    prepared: PreparedAssociationExactPopulationDiagnostic,
    method: object,
    *,
    split_name: str = "train",
) -> torch.Tensor:
    """Compose one exact-lane learner on a frozen Cartesian split."""

    checked_method = _require_method(method)
    if type(prepared) is not PreparedAssociationExactPopulationDiagnostic:
        raise TypeError("prepared must be exact-population preparation")
    population = _population_for_split(prepared, split_name)
    if (
        type(model) is not FiniteAssociationCorrectionNetwork
        or model.input_features != BASE_FEATURE_COUNT
        or model.hidden_width != _method_width(checked_method)
    ):
        raise ValueError("model architecture does not match the exact method")
    features = torch.tensor(np.asarray(population.features), dtype=torch.float64)
    times = torch.tensor(np.asarray(population.direct_times), dtype=torch.float64)
    terminal = torch.tensor(
        np.asarray(population.terminal_classifier_logits), dtype=torch.float64
    )
    guide = (
        torch.tensor(np.asarray(population.guide_classifier_logits), dtype=torch.float64)
        if checked_method == EXACT_GUIDED_METHOD
        else None
    )
    mode = (
        EXACT_DIRECT_METHOD
        if checked_method == EXACT_STRONG_DIRECT_METHOD
        else checked_method
    )
    return finite_association_logits(
        model,
        features,
        times,
        terminal,
        mode=mode,
        guide_classifier_logit=guide,
    )


def exact_population_model_training_bce(
    model: FiniteAssociationCorrectionNetwork,
    prepared: PreparedAssociationExactPopulationDiagnostic,
    method: object,
) -> torch.Tensor:
    """Authoritative model-level exact objective on ``M_train``."""

    logits = exact_population_model_logits(model, prepared, method, split_name="train")
    positive = torch.tensor(
        np.asarray(prepared.train_population.joint_mass), dtype=torch.float64
    )
    negative = torch.tensor(
        np.asarray(prepared.train_population.product_mass), dtype=torch.float64
    )
    return exact_population_training_bce(logits, positive, negative)


def exact_population_model_diagnostic_bce(
    model: FiniteAssociationCorrectionNetwork,
    prepared: PreparedAssociationExactPopulationDiagnostic,
    method: object,
    *,
    split_name: str,
    normalized: bool = False,
) -> torch.Tensor:
    """Evaluate a final checkpoint on train, validation, or test custody."""

    population = _population_for_split(prepared, split_name)
    logits = exact_population_model_logits(
        model, prepared, method, split_name=split_name
    )
    return exact_masked_population_bce(
        logits,
        torch.tensor(np.asarray(population.joint_mass), dtype=torch.float64),
        torch.tensor(np.asarray(population.product_mass), dtype=torch.float64),
        normalized=normalized,
    )


def build_exact_population_split_diagnostic(
    population: FrozenAssociationExactPopulationSplitCustody,
    logits: object,
) -> ExactPopulationSplitDiagnostic:
    """Compute the exact final-checkpoint excess BCE record for one split."""

    if type(population) is not FrozenAssociationExactPopulationSplitCustody:
        raise TypeError("population must be exact split custody")
    values = _torch_float64_vector(logits, name="logits")
    if values.numel() != population.support_size:
        raise ValueError("logits do not cover the complete split custody")
    positive = torch.tensor(np.asarray(population.joint_mass), dtype=torch.float64)
    negative = torch.tensor(np.asarray(population.product_mass), dtype=torch.float64)
    optimum_logits = torch.tensor(
        np.asarray(population.exact_optimal_logits), dtype=torch.float64
    )
    raw = float(
        exact_masked_population_bce(values, positive, negative).detach().item()
    )
    optimum = float(
        exact_masked_population_bce(
            optimum_logits, positive, negative
        ).detach().item()
    )
    normalizer = population.physical_normalizer
    excess = max(0.0, (raw - optimum) / normalizer)
    return ExactPopulationSplitDiagnostic(
        split_name=population.split_name,
        population_custody_sha256=population.custody_sha256,
        support_size=population.support_size,
        raw_population_bce=raw,
        optimal_raw_population_bce=optimum,
        physical_normalizer=normalizer,
        normalized_excess_bce=excess,
    )


def unexecuted_exact_population_result(
    prepared: PreparedAssociationExactPopulationDiagnostic,
) -> AssociationExactPopulationDiagnosticResult:
    """Return an auditable zero-step record while runner authority is absent."""

    if type(prepared) is not PreparedAssociationExactPopulationDiagnostic:
        raise TypeError("prepared must be exact-population preparation")
    return AssociationExactPopulationDiagnosticResult(
        preflight_sha256=prepared.preflight_sha256,
        execution_contract_sha256=prepared.execution_contract.digest,
        source_sha256=prepared.source_sha256,
        exact_configuration_sha256=prepared.exact_configuration_sha256,
        fixture_sha256=prepared.train_population.fixture_sha256,
        split_custody_sha256=tuple(
            value.custody_sha256 for value in prepared.populations
        ),
        oracle_product_control_custody_sha256=(
            prepared.oracle_product_control.custody_sha256
        ),
        oracle_product_positive_maximum_absolute_logit=(
            prepared.oracle_product_control.maximum_absolute_logit
        ),
        oracle_product_control_passed=prepared.oracle_product_control.passed,
        seed_custodies=prepared.seed_custodies,
        environment=None,
        executed=False,
        optimizer_steps_taken=0,
        method_results=(),
        status="PERMIT_REQUIRED_UNEXECUTED",
        notes=(_PERMIT_NOTE,),
        scientific_decision_eligible=False,
        product_control_optimized=False,
    )


def execute_frozen_association_exact_population_diagnostic(
    prepared: PreparedAssociationExactPopulationDiagnostic,
    *,
    permit: Optional[object] = None,
) -> CompletedExactPopulationExecution:
    """Execute one permit-selected seed/method in its isolated worker.

    All validation that can be performed without constructing optimizer state
    occurs first.  The permit's durable PREPARED -> RUNNING transition is the
    final operation before optimizer construction.  The function therefore
    cannot silently reuse a run after an interruption at or after update zero.
    """

    if type(prepared) is not PreparedAssociationExactPopulationDiagnostic:
        raise TypeError("prepared must be exact-population preparation")
    if type(permit) is not FrozenExactPopulationExecutionPermit:
        qualifier = "missing" if permit is None else "unsupported"
        raise ExactPopulationExecutionPermitRequired(
            "exact-population optimizer execution is permit-gated (%s permit); %s"
            % (qualifier, _PERMIT_NOTE)
        )
    if permit.production_session is not True:
        raise ExactPopulationExecutionPermitRequired(
            "exact-population optimizer execution rejects an emulated worker session; %s"
            % _PERMIT_NOTE
        )
    # Revalidate actual mutable object graphs and all decision-bearing source
    # before consuming a permit.  No optimizer is constructed in this phase.
    prepared.__post_init__()
    source = frozen_association_training_source_sha256()
    configuration = frozen_exact_population_configuration_sha256(
        source_sha256=source
    )
    if source != prepared.source_sha256 or configuration != prepared.exact_configuration_sha256:
        raise RuntimeError("exact source/configuration custody changed after preflight")
    if _prepared_preflight_sha256(prepared) != prepared.preflight_sha256:
        raise RuntimeError("exact preflight custody changed before execution")
    seed = permit.seed
    method = permit.method
    seed_custody = next(
        value for value in prepared.seed_custodies if value.seed == seed
    )
    model = initialize_exact_population_model(prepared, seed, method)
    initial_snapshot = snapshot_finite_association_mlp(model)
    expected_initial = (
        seed_custody.stronger_direct_initial_parameter_sha256
        if method == EXACT_STRONG_DIRECT_METHOD
        else seed_custody.primary_initial_parameter_sha256
    )
    if initial_snapshot.parameter_sha256 != expected_initial:
        raise RuntimeError("exact initial parameters changed before execution")
    train = prepared.train_population
    if train.support_size != EXACT_POPULATION_SUPPORT_SIZE:
        raise RuntimeError("exact full-batch population support changed")
    environment = configure_frozen_association_training_environment()
    if not environment.versions_match or not environment.execution_mode_matches:
        raise RuntimeError("exact worker failed to enter the frozen runtime")
    permit.validate_for(prepared, seed, method)

    # This consumption performs and fsyncs PREPARED -> RUNNING.  It is kept
    # immediately adjacent to optimizer construction by design.
    permit.consume_for(prepared, seed, method)
    optimizer_wall_start = time.perf_counter()
    optimizer = make_finite_association_adamw(model)
    updates = _method_updates(method)
    objectives = np.empty(updates, dtype=np.float64)
    gradients = np.empty(updates, dtype=np.float64)
    transcript_seed_sha256 = _exact_optimizer_transcript_seed_sha256(
        permit,
        initial_parameter_sha256=expected_initial,
        expected_optimizer_steps=updates,
    )
    rolling_transcript = hashlib.sha256(
        b"heterodiff-a1-exact-optimizer-update-transcript-v2\0"
        + bytes.fromhex(transcript_seed_sha256)
    )
    observed_updates = 0
    last_post_update_parameter_sha256 = None
    for update_index in range(updates):
        loss = exact_population_model_training_bce(model, prepared, method)
        objective = float(loss.detach().item())
        if not math.isfinite(objective) or objective < 0.0:
            raise ArithmeticError("exact training objective became invalid")
        update = finite_association_adamw_update(
            model,
            optimizer,
            loss,
            update_index=update_index,
            total_updates=updates,
        )
        if update.update_index != update_index:
            raise RuntimeError("exact optimizer update index changed")
        if update.learning_rate != cosine_adamw_learning_rate(update_index, updates):
            raise RuntimeError("exact optimizer learning-rate schedule changed")
        objectives[update_index] = objective
        gradients[update_index] = update.unclipped_gradient_norm
        post_update_parameter_sha256 = snapshot_finite_association_mlp(
            model
        ).parameter_sha256
        last_post_update_parameter_sha256 = post_update_parameter_sha256
        update_receipt = _record_digest(
            b"heterodiff-a1-exact-optimizer-update-v1",
            update_index,
            float(update.learning_rate).hex(),
            float(objective).hex(),
            float(update.unclipped_gradient_norm).hex(),
            post_update_parameter_sha256,
        )
        rolling_transcript.update(bytes.fromhex(update_receipt))
        observed_updates += 1
    optimizer_wall_seconds = time.perf_counter() - optimizer_wall_start

    trace = build_exact_population_optimization_trace(
        method, objectives, gradients
    )
    certificate = certify_finite_association_continuous_correction(
        model,
        frozen_fixture_sha256=train.fixture_sha256,
        guide_classifier_logit_grid=None,
    )
    require_matching_continuous_certificate(
        model,
        certificate,
        frozen_fixture_sha256=train.fixture_sha256,
        guide_classifier_logit_grid=None,
    )
    snapshot = freeze_exact_population_mlp_snapshot(
        snapshot_finite_association_mlp(model)
    )
    if snapshot.parameter_sha256 != certificate.parameter_sha256:
        raise RuntimeError("exact certified parameters changed unexpectedly")
    _require_exact_optimizer_transcript_final_parameter(
        last_post_update_parameter_sha256,
        snapshot.parameter_sha256,
    )
    with torch.no_grad():
        split_diagnostics = tuple(
            build_exact_population_split_diagnostic(
                population,
                exact_population_model_logits(
                    model,
                    prepared,
                    method,
                    split_name=population.split_name,
                ),
            )
            for population in prepared.populations
        )
    classifier_sha256 = frozen_exact_population_classifier_sha256(
        method=method,
        fixture_sha256=train.fixture_sha256,
        exact_configuration_sha256=prepared.exact_configuration_sha256,
        snapshot_sha256=snapshot.parameter_sha256,
        certificate_sha256=certificate.certificate_sha256,
    )
    elapsed_cpu = time.process_time() - permit.total_cpu_start
    elapsed_wall = time.perf_counter() - permit.total_wall_start
    peak_native = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    peak_bytes = peak_native if sys.platform == "darwin" else peak_native * 1024
    resources = ExactPopulationResourceMeasurement(
        measurement_scope=EXACT_RESOURCE_SCOPE,
        isolated_process=True,
        elapsed_cpu_seconds=elapsed_cpu,
        elapsed_wall_seconds=elapsed_wall,
        preparation_cpu_seconds=permit.preparation_cpu_seconds,
        preparation_wall_seconds=permit.preparation_wall_seconds,
        optimizer_wall_seconds=optimizer_wall_seconds,
        peak_rss_bytes=peak_bytes,
        peak_rss_method_id=(
            "resource.getrusage.RUSAGE_SELF.ru_maxrss_"
            + ("bytes" if sys.platform == "darwin" else "kibibytes_times_1024")
        ),
        parameter_count=_method_parameter_count(method),
        forward_multiply_add_count=_method_forward_macs(method),
        preparation_included=True,
        guide_construction_included=True,
        training_included=True,
        certificate_included=True,
        evaluation_included=True,
    )
    result = ExactPopulationMethodDiagnosticResult(
        seed=seed,
        method=method,
        run_key_sha256=permit.run_key_sha256,
        execution_runtime_sha256=permit.execution_runtime_sha256,
        campaign_sha256=permit.campaign_sha256,
        preflight_sha256=prepared.preflight_sha256,
        prepared_ledger_sha256=permit.prepared_ledger_sha256,
        running_ledger_sha256=permit.running_ledger_sha256,
        worker_session_sha256=permit.worker_session_sha256,
        launch_id_sha256=permit.launch_id_sha256,
        launch_authorization_sha256=permit.launch_authorization_sha256,
        child_process_identity_sha256=permit.child_process_identity_sha256,
        production_session=permit.production_session,
        fixture_sha256=train.fixture_sha256,
        exact_configuration_sha256=prepared.exact_configuration_sha256,
        initial_parameter_sha256=expected_initial,
        final_snapshot=snapshot,
        continuous_certificate=certificate,
        classifier_sha256=classifier_sha256,
        optimization_trace=trace,
        split_diagnostics=split_diagnostics,
        resources=resources,
        final_checkpoint_only=True,
        numerical_integrity_passed=True,
        diagnostic_only=True,
    )
    optimizer_completion = FrozenExactPopulationOptimizerCompletion(
        result=result,
        permit=permit,
        expected_optimizer_steps=updates,
        observed_optimizer_steps=observed_updates,
        rolling_optimizer_transcript_sha256=rolling_transcript.hexdigest(),
        _construction_key=_OPTIMIZER_COMPLETION_CONSTRUCTION_KEY,
    )
    return CompletedExactPopulationExecution(
        result,
        optimizer_completion,
        _construction_key=_COMPLETED_EXECUTION_CONSTRUCTION_KEY,
    )


__all__ = [
    "AssociationExactPopulationDiagnosticResult",
    "CompletedExactPopulationExecution",
    "EXACT_DIRECT_METHOD",
    "EXACT_EXPECTED_TOTAL_OPTIMIZER_STEPS",
    "EXACT_GUIDED_METHOD",
    "EXACT_POPULATION_METHODS",
    "EXACT_POPULATION_SUPPORT_SIZE",
    "EXACT_PRIMARY_METHODS",
    "EXACT_RESOURCE_SCOPE",
    "EXACT_SPLIT_NAMES",
    "EXACT_STRONG_DIRECT_METHOD",
    "EXACT_TRAIN_TIME_COUNT",
    "ExactPopulationExecutionPermitRequired",
    "FrozenExactPopulationOptimizerCompletion",
    "ExactPopulationMethodDiagnosticResult",
    "ExactPopulationOptimizationTrace",
    "ExactPopulationResourceMeasurement",
    "ExactPopulationSplitDiagnostic",
    "FrozenAssociationExactPopulationCustody",
    "FrozenAssociationExactPopulationSplitCustody",
    "FrozenExactPopulationExecutionContract",
    "FrozenExactPopulationExecutionPermit",
    "FrozenExactPopulationMLPSnapshot",
    "FrozenExactPopulationSeedCustody",
    "FrozenOracleProductPositiveControlCustody",
    "PreparedAssociationExactPopulationDiagnostic",
    "ORACLE_PRODUCT_POSITIVE_LOGIT_TOLERANCE",
    "build_exact_population_optimization_trace",
    "build_exact_population_split_diagnostic",
    "exact_masked_population_bce",
    "exact_population_model_diagnostic_bce",
    "exact_population_model_logits",
    "exact_population_model_training_bce",
    "exact_population_method_result_from_payload",
    "exact_population_method_result_payload",
    "exact_population_training_bce",
    "execute_frozen_association_exact_population_diagnostic",
    "freeze_exact_population_mlp_snapshot",
    "frozen_exact_population_classifier_sha256",
    "frozen_exact_population_configuration_sha256",
    "initialize_exact_population_model",
    "load_exact_population_method_result",
    "prepare_frozen_association_exact_population_diagnostic",
    "unexecuted_exact_population_result",
]
