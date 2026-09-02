"""Optional-PyTorch execution boundary for the frozen finite A1 learners.

This module separates preparation from execution.  :func:`prepare` constructs
and hashes one immutable data/model plan without taking an optimizer step;
:func:`execute` consumes exactly that plan under the frozen environment and
schedule.  Unit tests exercise preparation and objectives only.  Importing or
testing this module therefore does not execute the decision experiment.

Every fitted checkpoint is continuously certified before it can expose a
classifier-logit callback.  In particular, path/rate code cannot obtain an
evaluator from an uncertified or subsequently mutated model.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import hashlib
import io
import math
from numbers import Integral
import os
from pathlib import Path
import platform
import resource
import stat
import sys
import time
from typing import Optional, Tuple

import numpy as np
import scipy
import torch
from torch.nn import functional as torch_functional

from heterodiff.models.finite_association_residual_torch import (
    BASE_FEATURE_COUNT,
    CERTIFICATE_CORRECTION_LIMIT,
    CERTIFICATE_GRID_INTERVALS,
    CERTIFICATE_TIME_CHUNK,
    CORRECTION_BOUND,
    ContinuousCorrectionCertificate,
    FiniteAssociationCorrectionNetwork,
    FiniteAssociationMLPSnapshot,
    GUIDE_INPUT_FEATURE_COUNT,
    PRIMARY_HIDDEN_WIDTH,
    STRONG_DIRECT_HIDDEN_WIDTH,
    certify_finite_association_continuous_correction,
    finite_association_adamw_update,
    finite_association_features,
    finite_association_logits,
    _finite_association_validated_snapshot_logits,
    make_finite_association_adamw,
    require_matching_continuous_certificate,
    require_matching_snapshot_continuous_certificate,
    snapshot_finite_association_mlp,
)
from heterodiff.theory import IndependentFiniteAtomicReferenceGuide

from .finite_association_guided_residual_pilot import (
    FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS,
    FrozenAssociationResidualFixture,
    build_frozen_association_residual_fixture,
    frozen_association_fixture_content_digests,
    frozen_association_fixture_sha256,
    run_association_residual_prerequisite_gate,
)
from .finite_association_residual_data import (
    PAIRED_SEEDS,
    PRIMARY_UPDATES,
    SAMPLE_BUDGETS,
    STRONGER_UPDATES,
    FrozenAssociationResidualSampleCustody,
    FrozenAssociationResidualSampleDataset,
    build_frozen_association_residual_sample_custody,
)
from .finite_association_production_order import (
    DEFAULT_SOURCE_PATHS as _PRODUCTION_SOURCE_RELATIVE_PATHS,
    frozen_production_source_manifest,
)


DIRECT_METHOD = "direct"
GUIDED_METHOD = "guided"
STRONG_DIRECT_METHOD = "strong_direct"
GUIDE_INPUT_METHOD = "guide_input"
MISMATCH_METHOD = "mismatch"
LEARNER_METHODS = (
    DIRECT_METHOD,
    GUIDED_METHOD,
    STRONG_DIRECT_METHOD,
    GUIDE_INPUT_METHOD,
    MISMATCH_METHOD,
)

_EXPECTED_PYTHON = "3.11.5"
_EXPECTED_NUMPY = "2.4.6"
_EXPECTED_SCIPY = "1.17.1"
_EXPECTED_TORCH = "2.12.1"
_TERMINAL_TIME = 1.0
_PAIR_COUNT = 20 * 21
_SHA256_HEX = frozenset("0123456789abcdef")
_CHECKPOINT_PAYLOAD_SCHEMA = "heterodiff-a1-fitted-checkpoint-payload-v4"
_OPTIMIZER_TRANSCRIPT_SCHEMA = (
    "heterodiff-a1-sampled-optimizer-update-transcript-v3"
)
_BATCH_SIZE = 128
_ADAMW_INITIAL_LEARNING_RATE = 1.0e-3
_ADAMW_FINAL_LEARNING_RATE = 1.0e-5
_ADAMW_BETAS = (0.9, 0.999)
_ADAMW_EPSILON = 1.0e-8
_ADAMW_WEIGHT_DECAY = 1.0e-6
_GRADIENT_NORM_LIMIT = 1.0
_TRAINING_SOURCE_RELATIVE_PATHS = tuple(_PRODUCTION_SOURCE_RELATIVE_PATHS)


def _require_sha256(value: object, *, name: str) -> str:
    if type(value) is not str or len(value) != 64 or any(
        character not in _SHA256_HEX for character in value
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _require_method(value: object) -> str:
    if type(value) is not str:
        raise TypeError("method must be a string")
    if value not in LEARNER_METHODS:
        raise ValueError("method must be one of %r" % (LEARNER_METHODS,))
    return value


def _require_seed(value: object) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("seed must be an integer non-boolean value")
    result = int(value)
    if result not in PAIRED_SEEDS:
        raise ValueError("seed is not one of the eight frozen paired seeds")
    return result


def _require_budget(value: object) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("budget must be an integer non-boolean value")
    result = int(value)
    if result not in SAMPLE_BUDGETS:
        raise ValueError("budget is not one of the three frozen sample budgets")
    return result


def _method_contract(method: str) -> Tuple[str, int, int, int]:
    """Return composition mode, inputs, width, and update count."""

    if method == STRONG_DIRECT_METHOD:
        return "direct", BASE_FEATURE_COUNT, STRONG_DIRECT_HIDDEN_WIDTH, STRONGER_UPDATES
    if method == GUIDE_INPUT_METHOD:
        return "input", GUIDE_INPUT_FEATURE_COUNT, PRIMARY_HIDDEN_WIDTH, PRIMARY_UPDATES
    if method == MISMATCH_METHOD:
        return "mismatch", BASE_FEATURE_COUNT, PRIMARY_HIDDEN_WIDTH, PRIMARY_UPDATES
    if method == GUIDED_METHOD:
        return "guided", BASE_FEATURE_COUNT, PRIMARY_HIDDEN_WIDTH, PRIMARY_UPDATES
    if method == DIRECT_METHOD:
        return "direct", BASE_FEATURE_COUNT, PRIMARY_HIDDEN_WIDTH, PRIMARY_UPDATES
    raise AssertionError("validated learner method is unhandled")


def _digest_parts(label: bytes, *parts: object) -> str:
    digest = hashlib.sha256()
    digest.update(label)
    digest.update(b"\0")
    for value in parts:
        if isinstance(value, str):
            payload = value.encode("utf-8")
        elif isinstance(value, Integral) and not isinstance(value, (bool, np.bool_)):
            payload = str(int(value)).encode("ascii")
        elif isinstance(value, torch.Tensor):
            tensor = value.detach().to(device="cpu").contiguous()
            payload = (
                str(tensor.dtype).encode("ascii")
                + repr(tuple(tensor.shape)).encode("ascii")
                + tensor.numpy().tobytes(order="C")
            )
        else:
            array = np.ascontiguousarray(value)
            payload = (
                array.dtype.str.encode("ascii")
                + repr(tuple(array.shape)).encode("ascii")
                + array.tobytes(order="C")
            )
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def frozen_association_training_source_sha256() -> str:
    """Bind training to the complete production executable-source manifest."""

    project_root = Path(__file__).resolve().parents[3]
    manifest = frozen_production_source_manifest(project_root)
    if tuple(item["path"] for item in manifest["files"]) != (
        _TRAINING_SOURCE_RELATIVE_PATHS
    ):
        raise RuntimeError("training source closure changed during hashing")
    return manifest["source_manifest_sha256"]


def frozen_association_training_configuration_sha256(
    *, source_sha256: Optional[object] = None
) -> str:
    """Return the canonical optimizer/runtime/model contract identity."""

    source = (
        frozen_association_training_source_sha256()
        if source_sha256 is None
        else _require_sha256(source_sha256, name="source_sha256")
    )
    return _digest_parts(
        b"heterodiff-a1-association-training-configuration-v4",
        source,
        frozen_association_fixture_sha256(),
        _EXPECTED_PYTHON,
        _EXPECTED_NUMPY,
        _EXPECTED_SCIPY,
        _EXPECTED_TORCH,
        "cpu-float64-single-thread-deterministic",
        _BATCH_SIZE,
        _ADAMW_INITIAL_LEARNING_RATE,
        _ADAMW_FINAL_LEARNING_RATE,
        np.asarray(_ADAMW_BETAS, dtype=np.float64),
        _ADAMW_EPSILON,
        _ADAMW_WEIGHT_DECAY,
        _GRADIENT_NORM_LIMIT,
        PRIMARY_UPDATES,
        STRONGER_UPDATES,
        BASE_FEATURE_COUNT,
        GUIDE_INPUT_FEATURE_COUNT,
        PRIMARY_HIDDEN_WIDTH,
        STRONG_DIRECT_HIDDEN_WIDTH,
        CORRECTION_BOUND,
        CERTIFICATE_GRID_INTERVALS,
        CERTIFICATE_TIME_CHUNK,
        CERTIFICATE_CORRECTION_LIMIT,
        np.asarray(PAIRED_SEEDS, dtype=np.int64),
        np.asarray(SAMPLE_BUDGETS, dtype=np.int64),
        *LEARNER_METHODS,
    )


@dataclass(frozen=True)
class FrozenAssociationTrainingEnvironment:
    python_version: str
    numpy_version: str
    scipy_version: str
    torch_version: str
    torch_cpu_only: bool
    torch_threads: int
    torch_interop_threads: int
    deterministic_algorithms: bool

    @property
    def versions_match(self) -> bool:
        return (
            self.python_version == _EXPECTED_PYTHON
            and self.numpy_version == _EXPECTED_NUMPY
            and self.scipy_version == _EXPECTED_SCIPY
            and self.torch_version == _EXPECTED_TORCH
            and self.torch_cpu_only
        )

    @property
    def execution_mode_matches(self) -> bool:
        return (
            self.torch_threads == 1
            and self.torch_interop_threads == 1
            and self.deterministic_algorithms
        )


def inspect_frozen_association_training_environment(
) -> FrozenAssociationTrainingEnvironment:
    """Return the exact version/thread/determinism custody record."""

    return FrozenAssociationTrainingEnvironment(
        python_version=platform.python_version(),
        numpy_version=np.__version__,
        scipy_version=scipy.__version__,
        torch_version=str(torch.__version__),
        torch_cpu_only=torch.version.cuda is None,
        torch_threads=int(torch.get_num_threads()),
        torch_interop_threads=int(torch.get_num_interop_threads()),
        deterministic_algorithms=bool(
            torch.are_deterministic_algorithms_enabled()
        ),
    )


def configure_frozen_association_training_environment(
) -> FrozenAssociationTrainingEnvironment:
    """Fail closed unless the exact frozen runtime can be configured."""

    before = inspect_frozen_association_training_environment()
    if not before.versions_match:
        raise RuntimeError(
            "frozen learner execution requires Python %s, NumPy %s, SciPy %s, "
            "and CPU PyTorch %s" % (
                _EXPECTED_PYTHON,
                _EXPECTED_NUMPY,
                _EXPECTED_SCIPY,
                _EXPECTED_TORCH,
            )
        )
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError as error:
            raise RuntimeError(
                "PyTorch interop threads could not be frozen at one; run the "
                "decision in a fresh process"
            ) from error
    torch.use_deterministic_algorithms(True)
    after = inspect_frozen_association_training_environment()
    if not after.versions_match or not after.execution_mode_matches:
        raise RuntimeError("frozen single-thread deterministic mode was not established")
    return after


def _process_peak_rss_bytes() -> int:
    native = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if native < 0:
        raise ArithmeticError("process peak RSS is negative")
    # Darwin reports bytes; Linux and the supported Unix CI runtimes report KiB.
    return native if sys.platform == "darwin" else native * 1024


def _mismatched_guide(
    fixture: FrozenAssociationResidualFixture,
) -> IndependentFiniteAtomicReferenceGuide:
    correct = fixture.guide
    beta = tuple(float(value) for value in correct.immigration_rates)
    if beta != (0.38, 0.30, 0.24):
        raise ArithmeticError("the frozen correct-guide immigration vector changed")
    return IndependentFiniteAtomicReferenceGuide(
        fixture.latent_space,
        fixture.observation,
        terminal_time=_TERMINAL_TIME,
        immigration_rates=(beta[1], beta[2], beta[0]),
        per_particle_death_rates=correct.per_particle_death_rates,
        replacement_rates=correct.replacement_rates,
    )


def _classifier_guide_grid(
    fixture: FrozenAssociationResidualFixture,
    direct_times: np.ndarray,
    *,
    mismatch: bool,
) -> np.ndarray:
    times = np.asarray(direct_times, dtype=np.float64)
    if times.ndim != 1 or times.size == 0 or not np.all(np.isfinite(times)):
        raise ValueError("direct_times must be a nonempty finite vector")
    if np.any(times < 0.0) or np.any(times > _TERMINAL_TIME):
        raise ValueError("direct_times must lie in [0, 1]")
    guide = _mismatched_guide(fixture) if mismatch else fixture.guide
    density = np.stack(
        [guide.density_grid(float(value)) for value in times], axis=0
    )
    z = np.asarray(fixture.population.observation_marginal_density)
    if density.shape != (times.size, 20, 21) or np.any(density <= 0.0):
        raise ArithmeticError("analytic guide returned an invalid density grid")
    result = np.log(density) - np.log(z)[None, None, :]
    if not np.all(np.isfinite(result)):
        raise ArithmeticError("classifier guide grid is non-finite")
    return np.asarray(result, dtype=np.float64)


def _torch_model_seed(custody: FrozenAssociationResidualSampleCustody) -> int:
    state = custody.model_seed_child.generate_state(1, dtype=np.uint64)
    if state.shape != (1,):
        raise ArithmeticError("model seed child did not return one uint64 value")
    result = int(state[0])
    if result < 0 or result > 2**64 - 1:
        raise ArithmeticError("model generator seed is outside uint64")
    return result


def _pair_count_tensors(
    fixture: FrozenAssociationResidualFixture,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    latent = torch.tensor(fixture.latent_space.states, dtype=torch.int64)
    anchors = torch.tensor(
        fixture.retained_observation_space.states + ((0, 0, 0),),
        dtype=torch.int64,
    )
    overflow = torch.zeros(21, dtype=torch.bool)
    overflow[-1] = True
    return latent, anchors, overflow


@dataclass(frozen=True)
class FrozenAssociationResidualTrainingPreflight:
    seed: int
    budget: int
    method: str
    composition_mode: str
    input_features: int
    hidden_width: int
    updates: int
    torch_generator_seed: int
    source_sha256: str
    configuration_sha256: str
    fixture_sha256: str
    custody_sha256: str
    all_dataset_sha256: Tuple[str, str, str]
    all_batch_schedule_sha256: Tuple[str, str, str, str, str, str]
    dataset_sha256: str
    batch_schedule_sha256: str
    training_tensor_sha256: str
    initial_parameter_sha256: str
    preflight_sha256: str
    parameter_count: int
    forward_multiply_add_count: int

    def __post_init__(self) -> None:
        _require_seed(self.seed)
        _require_budget(self.budget)
        method = _require_method(self.method)
        mode, inputs, width, updates = _method_contract(method)
        if (
            self.composition_mode != mode
            or self.input_features != inputs
            or self.hidden_width != width
            or self.updates != updates
        ):
            raise ValueError("preflight architecture/schedule differs from contract")
        for name in (
            "source_sha256",
            "configuration_sha256",
            "fixture_sha256",
            "custody_sha256",
            "dataset_sha256",
            "batch_schedule_sha256",
            "training_tensor_sha256",
            "initial_parameter_sha256",
            "preflight_sha256",
        ):
            _require_sha256(getattr(self, name), name=name)
        if type(self.all_dataset_sha256) is not tuple or len(
            self.all_dataset_sha256
        ) != 3:
            raise TypeError("all_dataset_sha256 must contain three digests")
        if type(self.all_batch_schedule_sha256) is not tuple or len(
            self.all_batch_schedule_sha256
        ) != 6:
            raise TypeError(
                "all_batch_schedule_sha256 must contain six digests"
            )
        for name, values in (
            ("all_dataset_sha256", self.all_dataset_sha256),
            ("all_batch_schedule_sha256", self.all_batch_schedule_sha256),
        ):
            for value in values:
                _require_sha256(value, name=name)
        if isinstance(self.torch_generator_seed, (bool, np.bool_)) or not isinstance(
            self.torch_generator_seed, Integral
        ) or not 0 <= int(self.torch_generator_seed) <= 2**64 - 1:
            raise ValueError("torch_generator_seed must be a uint64-valued integer")
        if any(
            isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral)
            for value in (self.parameter_count, self.forward_multiply_add_count)
        ):
            raise TypeError("model counts must be integers")
        if self.parameter_count <= 0 or self.forward_multiply_add_count <= 0:
            raise ValueError("model counts must be positive")
        if _frozen_training_preflight_sha256(self) != self.preflight_sha256:
            raise ValueError("preflight digest is inconsistent with its full record")


def _frozen_training_preflight_sha256(
    preflight: FrozenAssociationResidualTrainingPreflight,
) -> str:
    return _digest_parts(
        b"heterodiff-a1-association-training-preflight-v1",
        preflight.seed,
        preflight.budget,
        preflight.method,
        preflight.composition_mode,
        preflight.input_features,
        preflight.hidden_width,
        preflight.updates,
        preflight.torch_generator_seed,
        preflight.source_sha256,
        preflight.configuration_sha256,
        preflight.fixture_sha256,
        preflight.custody_sha256,
        *preflight.all_dataset_sha256,
        *preflight.all_batch_schedule_sha256,
        preflight.dataset_sha256,
        preflight.batch_schedule_sha256,
        preflight.training_tensor_sha256,
        preflight.initial_parameter_sha256,
        preflight.parameter_count,
        preflight.forward_multiply_add_count,
    )


_EXECUTION_PERMIT_CONSTRUCTION_KEY = object()


class FrozenAssociationExecutionPermit:
    """Single-use authorization emitted only by the isolated ledger worker."""

    __slots__ = (
        "run_key_sha256",
        "preflight_sha256",
        "prepared_ledger_sha256",
        "campaign_sha256",
        "execution_runtime_sha256",
        "worker_session_sha256",
        "ledger_directory",
        "worker_process_id",
        "worker_parent_process_id",
        "total_wall_start",
        "total_cpu_start",
        "_worker_session",
        "_running_ledger_sha256",
        "_consumed",
        "_locked",
    )

    def __init__(
        self,
        *,
        run_key_sha256: object,
        preflight_sha256: object,
        prepared_ledger_sha256: object,
        campaign_sha256: object,
        execution_runtime_sha256: object,
        worker_session: object,
        ledger_directory: object,
        worker_process_id: object,
        total_wall_start: object,
        total_cpu_start: object,
        _construction_key: object,
    ) -> None:
        if _construction_key is not _EXECUTION_PERMIT_CONSTRUCTION_KEY:
            raise TypeError("execution permits are issued only by the isolated worker")
        object.__setattr__(self, "run_key_sha256", _require_sha256(
            run_key_sha256, name="run_key_sha256"
        ))
        object.__setattr__(self, "preflight_sha256", _require_sha256(
            preflight_sha256, name="preflight_sha256"
        ))
        object.__setattr__(self, "prepared_ledger_sha256", _require_sha256(
            prepared_ledger_sha256, name="prepared_ledger_sha256"
        ))
        object.__setattr__(self, "campaign_sha256", _require_sha256(
            campaign_sha256, name="campaign_sha256"
        ))
        object.__setattr__(self, "execution_runtime_sha256", _require_sha256(
            execution_runtime_sha256, name="execution_runtime_sha256"
        ))
        from heterodiff.experiments.finite_association_isolated_runner import (
            _FrozenAssociationWorkerSession,
        )

        if type(worker_session) is not _FrozenAssociationWorkerSession:
            raise TypeError("execution permit requires a parent-handshaken session")
        worker_session.validate_run(self.run_key_sha256)
        object.__setattr__(self, "_worker_session", worker_session)
        object.__setattr__(
            self, "worker_session_sha256", worker_session.session_sha256
        )
        ledger_path = Path(ledger_directory).resolve()
        object.__setattr__(self, "ledger_directory", str(ledger_path))
        if isinstance(worker_process_id, (bool, np.bool_)) or not isinstance(
            worker_process_id, Integral
        ) or int(worker_process_id) <= 0:
            raise ValueError("worker_process_id must be a positive integer")
        object.__setattr__(self, "worker_process_id", int(worker_process_id))
        object.__setattr__(self, "worker_parent_process_id", os.getppid())
        for name, value in (
            ("total_wall_start", total_wall_start),
            ("total_cpu_start", total_cpu_start),
        ):
            scalar = float(value)
            if not math.isfinite(scalar) or scalar < 0.0:
                raise ValueError("%s must be finite and nonnegative" % name)
            object.__setattr__(self, name, scalar)
        object.__setattr__(self, "_consumed", False)
        object.__setattr__(self, "_running_ledger_sha256", None)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("execution permit is immutable")
        object.__setattr__(self, name, value)

    def validate_for(
        self, preflight: FrozenAssociationResidualTrainingPreflight
    ) -> None:
        if self._consumed:
            raise RuntimeError("execution permit was already consumed")
        if os.getpid() != self.worker_process_id:
            raise RuntimeError("execution permit belongs to another process")
        if preflight.preflight_sha256 != self.preflight_sha256:
            raise RuntimeError("execution permit does not match this preflight")
        from heterodiff.experiments.finite_association_isolated_runner import (
            _verify_prepared_execution_permit,
        )

        _verify_prepared_execution_permit(self, preflight)

    def consume_for(
        self, preflight: FrozenAssociationResidualTrainingPreflight
    ) -> None:
        self.validate_for(preflight)
        from heterodiff.experiments.finite_association_isolated_runner import (
            _consume_prepared_execution_permit,
        )

        running_ledger_sha256 = _consume_prepared_execution_permit(
            self, preflight
        )
        object.__setattr__(
            self,
            "_running_ledger_sha256",
            _require_sha256(
                running_ledger_sha256, name="running_ledger_sha256"
            ),
        )
        object.__setattr__(self, "_consumed", True)

    @property
    def running_ledger_sha256(self) -> str:
        if not self._consumed or self._running_ledger_sha256 is None:
            raise RuntimeError("execution permit has not entered RUNNING")
        return self._running_ledger_sha256


def _issue_frozen_association_execution_permit(
    *,
    run_key_sha256: object,
    preflight_sha256: object,
    prepared_ledger_sha256: object,
    campaign_sha256: object,
    execution_runtime_sha256: object,
    ledger_directory: object,
    total_wall_start: object,
    total_cpu_start: object,
    worker_session: object = None,
) -> FrozenAssociationExecutionPermit:
    """Private bridge used after the worker atomically records PREPARED."""

    return FrozenAssociationExecutionPermit(
        run_key_sha256=run_key_sha256,
        preflight_sha256=preflight_sha256,
        prepared_ledger_sha256=prepared_ledger_sha256,
        campaign_sha256=campaign_sha256,
        execution_runtime_sha256=execution_runtime_sha256,
        worker_session=worker_session,
        ledger_directory=ledger_directory,
        worker_process_id=os.getpid(),
        total_wall_start=total_wall_start,
        total_cpu_start=total_cpu_start,
        _construction_key=_EXECUTION_PERMIT_CONSTRUCTION_KEY,
    )


@dataclass(frozen=True, eq=False)
class PreparedAssociationResidualTraining:
    preflight: FrozenAssociationResidualTrainingPreflight
    fixture: FrozenAssociationResidualFixture
    custody: FrozenAssociationResidualSampleCustody
    dataset: FrozenAssociationResidualSampleDataset
    model: FiniteAssociationCorrectionNetwork
    features: torch.Tensor
    direct_times: torch.Tensor
    terminal_classifier_logits: torch.Tensor
    guide_classifier_logits: Optional[torch.Tensor]
    class_labels: torch.Tensor
    importance_weights: torch.Tensor


def _prepared_training_tensor_sha256(
    prepared: PreparedAssociationResidualTraining,
) -> str:
    return _digest_parts(
        b"heterodiff-a1-association-training-tensors-v1",
        prepared.features,
        prepared.direct_times,
        prepared.terminal_classifier_logits,
        prepared.guide_classifier_logits
        if prepared.guide_classifier_logits is not None
        else "no-guide",
        prepared.class_labels,
        prepared.importance_weights,
    )


@dataclass(frozen=True)
class FrozenAssociationOptimizerCompletionReceipt:
    """Serialized proof that the sampled executor reached its completion edge.

    The self-digest is not local-user authentication.  Production admission
    additionally requires the live, single-use capability returned by the
    executor and the canonical RUNNING-to-SUCCESS ledger transition.
    """

    schema: str
    seed: int
    budget: int
    method: str
    run_key_sha256: str
    campaign_sha256: str
    preflight_sha256: str
    prepared_ledger_sha256: str
    running_ledger_sha256: str
    execution_runtime_sha256: str
    worker_session_sha256: str
    expected_optimizer_steps: int
    observed_optimizer_steps: int
    optimizer_transcript_sha256: str
    initial_parameter_sha256: str
    last_post_update_parameter_sha256: str
    final_parameter_sha256: str
    certificate_sha256: str
    classifier_sha256: str
    resource_sha256: str
    checkpoint_identity_sha256: str
    completion_receipt_sha256: str

    def __post_init__(self) -> None:
        from heterodiff.experiments.finite_association_isolated_runner import (
            _validated_optimizer_completion_receipt_record,
        )

        _validated_optimizer_completion_receipt_record(asdict(self))


def _optimizer_completion_resource_sha256(
    *,
    elapsed_training_seconds: float,
    total_cpu_seconds: float,
    total_wall_seconds: float,
    process_peak_rss_bytes: int,
) -> str:
    return _digest_parts(
        b"heterodiff-a1-sampled-completion-resources-v1",
        float(elapsed_training_seconds).hex(),
        float(total_cpu_seconds).hex(),
        float(total_wall_seconds).hex(),
        int(process_peak_rss_bytes),
    )


def _optimizer_completion_checkpoint_identity_sha256(
    *,
    preflight_sha256: str,
    run_key_sha256: str,
    prepared_ledger_sha256: str,
    running_ledger_sha256: str,
    execution_runtime_sha256: str,
    classifier_sha256: str,
    parameter_sha256: str,
    certificate_sha256: str,
    final_empirical_risk: float,
    maximum_unclipped_gradient_norm: float,
    optimizer_steps_taken: int,
    optimizer_transcript_sha256: str,
    resource_sha256: str,
) -> str:
    return _digest_parts(
        b"heterodiff-a1-sampled-completed-checkpoint-identity-v1",
        preflight_sha256,
        run_key_sha256,
        prepared_ledger_sha256,
        running_ledger_sha256,
        execution_runtime_sha256,
        classifier_sha256,
        parameter_sha256,
        certificate_sha256,
        float(final_empirical_risk).hex(),
        float(maximum_unclipped_gradient_norm).hex(),
        int(optimizer_steps_taken),
        optimizer_transcript_sha256,
        resource_sha256,
    )


def _build_optimizer_completion_receipt(
    *,
    preflight: FrozenAssociationResidualTrainingPreflight,
    execution_permit: FrozenAssociationExecutionPermit,
    optimizer_steps_taken: int,
    optimizer_transcript_sha256: str,
    last_post_update_parameter_sha256: str,
    final_parameter_sha256: str,
    certificate_sha256: str,
    classifier_sha256: str,
    resource_sha256: str,
    checkpoint_identity_sha256: str,
) -> FrozenAssociationOptimizerCompletionReceipt:
    from heterodiff.experiments.finite_association_isolated_runner import (
        _OPTIMIZER_COMPLETION_SCHEMA,
        _sha256_json,
    )

    _require_last_post_update_matches_final(
        last_post_update_parameter_sha256, final_parameter_sha256
    )
    body = {
        "schema": _OPTIMIZER_COMPLETION_SCHEMA,
        "seed": preflight.seed,
        "budget": preflight.budget,
        "method": preflight.method,
        "run_key_sha256": execution_permit.run_key_sha256,
        "campaign_sha256": execution_permit.campaign_sha256,
        "preflight_sha256": preflight.preflight_sha256,
        "prepared_ledger_sha256": execution_permit.prepared_ledger_sha256,
        "running_ledger_sha256": execution_permit.running_ledger_sha256,
        "execution_runtime_sha256": execution_permit.execution_runtime_sha256,
        "worker_session_sha256": execution_permit.worker_session_sha256,
        "expected_optimizer_steps": preflight.updates,
        "observed_optimizer_steps": int(optimizer_steps_taken),
        "optimizer_transcript_sha256": optimizer_transcript_sha256,
        "initial_parameter_sha256": preflight.initial_parameter_sha256,
        "last_post_update_parameter_sha256": (
            last_post_update_parameter_sha256
        ),
        "final_parameter_sha256": final_parameter_sha256,
        "certificate_sha256": certificate_sha256,
        "classifier_sha256": classifier_sha256,
        "resource_sha256": resource_sha256,
        "checkpoint_identity_sha256": checkpoint_identity_sha256,
    }
    body["completion_receipt_sha256"] = _sha256_json(body)
    return FrozenAssociationOptimizerCompletionReceipt(**body)


@dataclass(frozen=True, eq=False)
class FittedAssociationResidualCheckpoint:
    preflight: FrozenAssociationResidualTrainingPreflight
    environment: FrozenAssociationTrainingEnvironment
    fixture: FrozenAssociationResidualFixture
    mismatched_guide: Optional[IndependentFiniteAtomicReferenceGuide]
    final_snapshot: FiniteAssociationMLPSnapshot
    certificate: ContinuousCorrectionCertificate
    certificate_guide_grid: Optional[torch.Tensor]
    run_key_sha256: str
    prepared_ledger_sha256: str
    execution_runtime_sha256: str
    classifier_sha256: str
    final_empirical_risk: float
    maximum_unclipped_gradient_norm: float
    optimizer_steps_taken: int
    optimizer_transcript_sha256: str
    optimizer_completion_receipt: FrozenAssociationOptimizerCompletionReceipt
    elapsed_training_seconds: float
    total_cpu_seconds: float
    total_wall_seconds: float
    process_peak_rss_bytes: int

    def __post_init__(self) -> None:
        if type(self.preflight) is not FrozenAssociationResidualTrainingPreflight:
            raise TypeError("checkpoint preflight must be the exact frozen record")
        if not self.environment.versions_match or not self.environment.execution_mode_matches:
            raise ValueError("checkpoint environment does not match the frozen runtime")
        if type(self.fixture) is not FrozenAssociationResidualFixture:
            raise TypeError("checkpoint fixture must be the frozen A1 fixture")
        if self.preflight.method == MISMATCH_METHOD:
            if not isinstance(
                self.mismatched_guide, IndependentFiniteAtomicReferenceGuide
            ):
                raise TypeError("mismatch checkpoint must retain its cyclic guide")
        elif self.mismatched_guide is not None:
            raise ValueError("only mismatch checkpoints may retain a cyclic guide")
        for name in (
            "run_key_sha256",
            "prepared_ledger_sha256",
            "execution_runtime_sha256",
            "classifier_sha256",
            "optimizer_transcript_sha256",
        ):
            _require_sha256(getattr(self, name), name=name)
        require_matching_snapshot_continuous_certificate(
            self.final_snapshot,
            self.certificate,
            frozen_fixture_sha256=self.preflight.fixture_sha256,
            guide_classifier_logit_grid=self.certificate_guide_grid,
        )
        actual_fixture_digests = frozen_association_fixture_content_digests(
            self.fixture
        )
        if (
            actual_fixture_digests != FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS
            or frozen_association_fixture_sha256(actual_fixture_digests)
            != self.preflight.fixture_sha256
        ):
            raise ValueError("checkpoint fixture contents are not frozen A1")
        if self.preflight.method == MISMATCH_METHOD and (
            _independent_guide_sha256(self.mismatched_guide)
            != _independent_guide_sha256(_mismatched_guide(self.fixture))
        ):
            raise ValueError("checkpoint cyclic guide differs from the frozen control")
        expected_classifier = _fitted_classifier_sha256(
            self.preflight,
            self.environment,
            self.fixture,
            self.final_snapshot,
            self.certificate,
            self.certificate_guide_grid,
            self.execution_runtime_sha256,
        )
        if expected_classifier != self.classifier_sha256:
            raise ValueError("checkpoint classifier digest is inconsistent")
        if (
            isinstance(self.optimizer_steps_taken, (bool, np.bool_))
            or not isinstance(self.optimizer_steps_taken, Integral)
            or int(self.optimizer_steps_taken) != self.preflight.updates
        ):
            raise ValueError("checkpoint optimizer step count is inconsistent")
        object.__setattr__(
            self, "optimizer_steps_taken", int(self.optimizer_steps_taken)
        )
        for name in (
            "final_empirical_risk",
            "maximum_unclipped_gradient_norm",
            "elapsed_training_seconds",
            "total_cpu_seconds",
            "total_wall_seconds",
        ):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value < 0.0:
                raise ValueError("%s must be finite and nonnegative" % name)
            object.__setattr__(self, name, value)
        if isinstance(self.process_peak_rss_bytes, (bool, np.bool_)) or not isinstance(
            self.process_peak_rss_bytes, Integral
        ) or int(self.process_peak_rss_bytes) < 0:
            raise ValueError("process peak RSS bytes must be a nonnegative integer")
        _require_optimizer_completion_matches_checkpoint(self)


def _require_optimizer_completion_matches_checkpoint(
    checkpoint: FittedAssociationResidualCheckpoint,
) -> None:
    receipt = checkpoint.optimizer_completion_receipt
    if type(receipt) is not FrozenAssociationOptimizerCompletionReceipt:
        raise TypeError(
            "checkpoint requires an exact optimizer completion receipt"
        )
    receipt.__post_init__()
    resource_sha256 = _optimizer_completion_resource_sha256(
        elapsed_training_seconds=checkpoint.elapsed_training_seconds,
        total_cpu_seconds=checkpoint.total_cpu_seconds,
        total_wall_seconds=checkpoint.total_wall_seconds,
        process_peak_rss_bytes=checkpoint.process_peak_rss_bytes,
    )
    checkpoint_identity_sha256 = (
        _optimizer_completion_checkpoint_identity_sha256(
            preflight_sha256=checkpoint.preflight.preflight_sha256,
            run_key_sha256=checkpoint.run_key_sha256,
            prepared_ledger_sha256=checkpoint.prepared_ledger_sha256,
            running_ledger_sha256=receipt.running_ledger_sha256,
            execution_runtime_sha256=checkpoint.execution_runtime_sha256,
            classifier_sha256=checkpoint.classifier_sha256,
            parameter_sha256=checkpoint.final_snapshot.parameter_sha256,
            certificate_sha256=checkpoint.certificate.certificate_sha256,
            final_empirical_risk=checkpoint.final_empirical_risk,
            maximum_unclipped_gradient_norm=(
                checkpoint.maximum_unclipped_gradient_norm
            ),
            optimizer_steps_taken=checkpoint.optimizer_steps_taken,
            optimizer_transcript_sha256=(
                checkpoint.optimizer_transcript_sha256
            ),
            resource_sha256=resource_sha256,
        )
    )
    observed = (
        receipt.seed,
        receipt.budget,
        receipt.method,
        receipt.run_key_sha256,
        receipt.preflight_sha256,
        receipt.prepared_ledger_sha256,
        receipt.execution_runtime_sha256,
        receipt.expected_optimizer_steps,
        receipt.observed_optimizer_steps,
        receipt.optimizer_transcript_sha256,
        receipt.initial_parameter_sha256,
        receipt.last_post_update_parameter_sha256,
        receipt.final_parameter_sha256,
        receipt.certificate_sha256,
        receipt.classifier_sha256,
        receipt.resource_sha256,
        receipt.checkpoint_identity_sha256,
    )
    expected = (
        checkpoint.preflight.seed,
        checkpoint.preflight.budget,
        checkpoint.preflight.method,
        checkpoint.run_key_sha256,
        checkpoint.preflight.preflight_sha256,
        checkpoint.prepared_ledger_sha256,
        checkpoint.execution_runtime_sha256,
        checkpoint.preflight.updates,
        checkpoint.optimizer_steps_taken,
        checkpoint.optimizer_transcript_sha256,
        checkpoint.preflight.initial_parameter_sha256,
        checkpoint.final_snapshot.parameter_sha256,
        checkpoint.final_snapshot.parameter_sha256,
        checkpoint.certificate.certificate_sha256,
        checkpoint.classifier_sha256,
        resource_sha256,
        checkpoint_identity_sha256,
    )
    if observed != expected:
        raise ValueError(
            "optimizer completion receipt differs from checkpoint custody"
        )


_OPTIMIZER_COMPLETION_CAPABILITY_KEY = object()


class _FrozenAssociationOptimizerCompletionCapability:
    """Live, process-bound, single-use edge from executor to SUCCESS writer."""

    __slots__ = ("_receipt", "_execution_permit", "_consumed", "_locked")

    def __init__(
        self,
        receipt: FrozenAssociationOptimizerCompletionReceipt,
        execution_permit: FrozenAssociationExecutionPermit,
        *,
        _construction_key: object,
    ) -> None:
        if _construction_key is not _OPTIMIZER_COMPLETION_CAPABILITY_KEY:
            raise TypeError(
                "optimizer completion capabilities come only from execution"
            )
        if type(receipt) is not FrozenAssociationOptimizerCompletionReceipt:
            raise TypeError("completion capability requires the exact receipt")
        if type(execution_permit) is not FrozenAssociationExecutionPermit:
            raise TypeError("completion capability requires the consumed permit")
        if not execution_permit._consumed:
            raise RuntimeError("optimizer completion requires a consumed permit")
        object.__setattr__(self, "_receipt", receipt)
        object.__setattr__(self, "_execution_permit", execution_permit)
        object.__setattr__(self, "_consumed", False)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("optimizer completion capability is immutable")
        object.__setattr__(self, name, value)

    @property
    def receipt(self) -> FrozenAssociationOptimizerCompletionReceipt:
        return self._receipt

    def consume_for_success(
        self,
        checkpoint: FittedAssociationResidualCheckpoint,
        running_record: object,
        worker_session: object,
    ) -> None:
        if self._consumed:
            raise RuntimeError("optimizer completion capability was already consumed")
        if os.getpid() != self._execution_permit.worker_process_id:
            raise RuntimeError("optimizer completion belongs to another process")
        if worker_session is not self._execution_permit._worker_session:
            raise RuntimeError("optimizer completion worker session changed")
        _require_optimizer_completion_matches_checkpoint(checkpoint)
        if checkpoint.optimizer_completion_receipt != self._receipt:
            raise RuntimeError("optimizer completion receipt changed")
        if type(running_record) is not dict:
            raise TypeError("optimizer completion requires the RUNNING record")
        if (
            running_record.get("state") != "RUNNING"
            or running_record.get("run_key_sha256")
            != self._receipt.run_key_sha256
            or running_record.get("prepared_ledger_sha256")
            != self._receipt.prepared_ledger_sha256
            or running_record.get("running_ledger_sha256")
            != self._receipt.running_ledger_sha256
            or running_record.get("campaign_sha256", self._receipt.campaign_sha256)
            != self._receipt.campaign_sha256
            or running_record.get("runtime", {}).get("sha256")
            != self._receipt.execution_runtime_sha256
            or running_record.get("worker_session", {}).get("session_sha256")
            != self._receipt.worker_session_sha256
            or running_record.get("preflight", {}).get("preflight_sha256")
            != self._receipt.preflight_sha256
        ):
            raise RuntimeError(
                "optimizer completion differs from canonical RUNNING custody"
            )
        object.__setattr__(self, "_consumed", True)


_COMPLETED_TRAINING_CONSTRUCTION_KEY = object()


class OptimizerCompletedAssociationResidualTraining:
    """Checkpoint plus the live capability required by the SUCCESS edge."""

    __slots__ = ("_checkpoint", "_completion_capability", "_locked")

    def __init__(
        self,
        checkpoint: FittedAssociationResidualCheckpoint,
        completion_capability: _FrozenAssociationOptimizerCompletionCapability,
        *,
        _construction_key: object,
    ) -> None:
        if _construction_key is not _COMPLETED_TRAINING_CONSTRUCTION_KEY:
            raise TypeError("completed training is returned only by the executor")
        if type(checkpoint) is not FittedAssociationResidualCheckpoint:
            raise TypeError("completed training requires an exact checkpoint")
        if type(completion_capability) is not _FrozenAssociationOptimizerCompletionCapability:
            raise TypeError("completed training requires the live completion capability")
        _require_optimizer_completion_matches_checkpoint(checkpoint)
        if completion_capability.receipt != checkpoint.optimizer_completion_receipt:
            raise RuntimeError("completion capability/checkpoint receipt mismatch")
        object.__setattr__(self, "_checkpoint", checkpoint)
        object.__setattr__(self, "_completion_capability", completion_capability)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("completed training is immutable")
        object.__setattr__(self, name, value)

    @property
    def checkpoint(self) -> FittedAssociationResidualCheckpoint:
        _require_optimizer_completion_matches_checkpoint(self._checkpoint)
        return self._checkpoint

    def _consume_for_success(
        self, running_record: object, worker_session: object
    ) -> None:
        self._completion_capability.consume_for_success(
            self._checkpoint, running_record, worker_session
        )


_LEDGER_VERIFIED_CONSTRUCTION_KEY = object()


class LedgerVerifiedFittedAssociationCheckpoint:
    """A fitted payload admitted by the canonical campaign SUCCESS ledger."""

    __slots__ = (
        "_checkpoint",
        "_success_receipt_sha256",
        "_campaign_sha256",
        "_running_ledger_sha256",
        "_optimizer_completion_receipt_sha256",
        "_worker_session_sha256",
        "_launch_authorization_sha256",
        "_launch_receipt_sha256",
        "_worker_process_id",
        "_worker_parent_process_id",
        "_worker_process_identity_sha256",
        "_preparation_cpu_seconds",
        "_preparation_wall_seconds",
        "_locked",
    )

    def __init__(
        self,
        checkpoint: FittedAssociationResidualCheckpoint,
        *,
        success_receipt_sha256: object,
        campaign_sha256: object,
        running_ledger_sha256: object,
        optimizer_completion_receipt_sha256: object,
        worker_session_sha256: object,
        launch_authorization_sha256: object,
        launch_receipt_sha256: object,
        worker_process_id: object,
        worker_parent_process_id: object,
        worker_process_identity_sha256: object,
        preparation_cpu_seconds: object,
        preparation_wall_seconds: object,
        _construction_key: object,
    ) -> None:
        if _construction_key is not _LEDGER_VERIFIED_CONSTRUCTION_KEY:
            raise TypeError("use the canonical SUCCESS-ledger loader")
        if type(checkpoint) is not FittedAssociationResidualCheckpoint:
            raise TypeError("checkpoint must be an exact fitted payload")
        _require_fitted_checkpoint_integrity(checkpoint)
        object.__setattr__(self, "_checkpoint", checkpoint)
        object.__setattr__(
            self,
            "_success_receipt_sha256",
            _require_sha256(
                success_receipt_sha256, name="success_receipt_sha256"
            ),
        )
        object.__setattr__(
            self,
            "_campaign_sha256",
            _require_sha256(campaign_sha256, name="campaign_sha256"),
        )
        for name, raw in (
            ("_running_ledger_sha256", running_ledger_sha256),
            (
                "_optimizer_completion_receipt_sha256",
                optimizer_completion_receipt_sha256,
            ),
            ("_worker_session_sha256", worker_session_sha256),
            ("_launch_authorization_sha256", launch_authorization_sha256),
            ("_launch_receipt_sha256", launch_receipt_sha256),
            ("_worker_process_identity_sha256", worker_process_identity_sha256),
        ):
            object.__setattr__(self, name, _require_sha256(raw, name=name[1:]))
        if (
            self._optimizer_completion_receipt_sha256
            != checkpoint.optimizer_completion_receipt.completion_receipt_sha256
            or self._running_ledger_sha256
            != checkpoint.optimizer_completion_receipt.running_ledger_sha256
        ):
            raise RuntimeError(
                "SUCCESS wrapper completion custody differs from checkpoint"
            )
        for name, raw in (
            ("_worker_process_id", worker_process_id),
            ("_worker_parent_process_id", worker_parent_process_id),
        ):
            if isinstance(raw, (bool, np.bool_)) or not isinstance(raw, Integral):
                raise TypeError("worker process identifiers must be integers")
            value = int(raw)
            if value <= 0:
                raise ValueError("worker process identifiers must be positive")
            object.__setattr__(self, name, value)
        from heterodiff.experiments.finite_association_isolated_runner import (
            _worker_process_identity_sha256,
        )

        expected_process_identity = _worker_process_identity_sha256(
            {
                "worker_pid": self._worker_process_id,
                "worker_parent_pid": self._worker_parent_process_id,
                "session_sha256": self._worker_session_sha256,
                "launch_authorization_sha256": (
                    self._launch_authorization_sha256
                ),
                "launch_receipt_sha256": self._launch_receipt_sha256,
            }
        )
        if expected_process_identity != self._worker_process_identity_sha256:
            raise RuntimeError("SUCCESS wrapper worker process binding changed")
        for name, raw in (
            ("_preparation_cpu_seconds", preparation_cpu_seconds),
            ("_preparation_wall_seconds", preparation_wall_seconds),
        ):
            if isinstance(raw, (bool, np.bool_)):
                raise TypeError("preparation durations must be non-boolean")
            value = float(raw)
            if not math.isfinite(value) or value < 0.0:
                raise ValueError("preparation durations must be finite and nonnegative")
            object.__setattr__(self, name, value)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("ledger-verified checkpoint is immutable")
        object.__setattr__(self, name, value)

    @property
    def checkpoint(self) -> FittedAssociationResidualCheckpoint:
        return self._checkpoint

    @property
    def success_receipt_sha256(self) -> str:
        return self._success_receipt_sha256

    @property
    def campaign_sha256(self) -> str:
        return self._campaign_sha256

    @property
    def running_ledger_sha256(self) -> str:
        return self._running_ledger_sha256

    @property
    def optimizer_completion_receipt_sha256(self) -> str:
        return self._optimizer_completion_receipt_sha256

    @property
    def worker_session_sha256(self) -> str:
        return self._worker_session_sha256

    @property
    def launch_authorization_sha256(self) -> str:
        return self._launch_authorization_sha256

    @property
    def launch_receipt_sha256(self) -> str:
        return self._launch_receipt_sha256

    @property
    def worker_process_id(self) -> int:
        return self._worker_process_id

    @property
    def worker_parent_process_id(self) -> int:
        return self._worker_parent_process_id

    @property
    def worker_process_identity_sha256(self) -> str:
        return self._worker_process_identity_sha256

    @property
    def preparation_cpu_seconds(self) -> float:
        return self._preparation_cpu_seconds

    @property
    def preparation_wall_seconds(self) -> float:
        return self._preparation_wall_seconds


def _ledger_verified_fitted_association_checkpoint(
    checkpoint: FittedAssociationResidualCheckpoint,
    *,
    success_receipt_sha256: object,
    campaign_sha256: object,
    running_ledger_sha256: object,
    optimizer_completion_receipt_sha256: object,
    worker_session_sha256: object,
    launch_authorization_sha256: object,
    launch_receipt_sha256: object,
    worker_process_id: object,
    worker_parent_process_id: object,
    worker_process_identity_sha256: object,
    preparation_cpu_seconds: object,
    preparation_wall_seconds: object,
) -> LedgerVerifiedFittedAssociationCheckpoint:
    return LedgerVerifiedFittedAssociationCheckpoint(
        checkpoint,
        success_receipt_sha256=success_receipt_sha256,
        campaign_sha256=campaign_sha256,
        running_ledger_sha256=running_ledger_sha256,
        optimizer_completion_receipt_sha256=(
            optimizer_completion_receipt_sha256
        ),
        worker_session_sha256=worker_session_sha256,
        launch_authorization_sha256=launch_authorization_sha256,
        launch_receipt_sha256=launch_receipt_sha256,
        worker_process_id=worker_process_id,
        worker_parent_process_id=worker_parent_process_id,
        worker_process_identity_sha256=worker_process_identity_sha256,
        preparation_cpu_seconds=preparation_cpu_seconds,
        preparation_wall_seconds=preparation_wall_seconds,
        _construction_key=_LEDGER_VERIFIED_CONSTRUCTION_KEY,
    )


def _dataclass_field_payload(value: object, expected_type: type) -> dict:
    if type(value) is not expected_type:
        raise TypeError("checkpoint component has the wrong exact type")
    return {field.name: getattr(value, field.name) for field in fields(expected_type)}


def fitted_association_checkpoint_payload(
    checkpoint: FittedAssociationResidualCheckpoint,
) -> dict:
    """Return a mappingproxy-free tensor/primitive checkpoint payload."""

    _require_fitted_checkpoint_integrity(checkpoint)
    snapshot = checkpoint.final_snapshot
    return {
        "schema": _CHECKPOINT_PAYLOAD_SCHEMA,
        "preflight": _dataclass_field_payload(
            checkpoint.preflight, FrozenAssociationResidualTrainingPreflight
        ),
        "environment": _dataclass_field_payload(
            checkpoint.environment, FrozenAssociationTrainingEnvironment
        ),
        "snapshot": {
            "input_features": snapshot.input_features,
            "hidden_width": snapshot.hidden_width,
            "weight1": snapshot.weight1.detach().clone(),
            "bias1": snapshot.bias1.detach().clone(),
            "weight2": snapshot.weight2.detach().clone(),
            "bias2": snapshot.bias2.detach().clone(),
            "weight3": snapshot.weight3.detach().clone(),
            "bias3": snapshot.bias3.detach().clone(),
            "parameter_sha256": snapshot.parameter_sha256,
        },
        "certificate": _dataclass_field_payload(
            checkpoint.certificate, ContinuousCorrectionCertificate
        ),
        "certificate_guide_grid": (
            None
            if checkpoint.certificate_guide_grid is None
            else checkpoint.certificate_guide_grid.detach().clone()
        ),
        "run_key_sha256": checkpoint.run_key_sha256,
        "prepared_ledger_sha256": checkpoint.prepared_ledger_sha256,
        "execution_runtime_sha256": checkpoint.execution_runtime_sha256,
        "classifier_sha256": checkpoint.classifier_sha256,
        "final_empirical_risk": checkpoint.final_empirical_risk,
        "maximum_unclipped_gradient_norm": (
            checkpoint.maximum_unclipped_gradient_norm
        ),
        "optimizer_steps_taken": checkpoint.optimizer_steps_taken,
        "optimizer_transcript_sha256": checkpoint.optimizer_transcript_sha256,
        "optimizer_completion_receipt": asdict(
            checkpoint.optimizer_completion_receipt
        ),
        "elapsed_training_seconds": checkpoint.elapsed_training_seconds,
        "total_cpu_seconds": checkpoint.total_cpu_seconds,
        "total_wall_seconds": checkpoint.total_wall_seconds,
        "process_peak_rss_bytes": checkpoint.process_peak_rss_bytes,
    }


def _exact_payload_keys(value: object, expected: Tuple[str, ...], *, name: str) -> dict:
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError("%s has an invalid checkpoint schema" % name)
    return value


def fitted_association_checkpoint_from_payload(
    payload: object,
) -> FittedAssociationResidualCheckpoint:
    """Reconstruct and fully revalidate a plain saved checkpoint payload."""

    top_level = (
        "schema",
        "preflight",
        "environment",
        "snapshot",
        "certificate",
        "certificate_guide_grid",
        "run_key_sha256",
        "prepared_ledger_sha256",
        "execution_runtime_sha256",
        "classifier_sha256",
        "final_empirical_risk",
        "maximum_unclipped_gradient_norm",
        "optimizer_steps_taken",
        "optimizer_transcript_sha256",
        "optimizer_completion_receipt",
        "elapsed_training_seconds",
        "total_cpu_seconds",
        "total_wall_seconds",
        "process_peak_rss_bytes",
    )
    values = _exact_payload_keys(payload, top_level, name="payload")
    if values["schema"] != _CHECKPOINT_PAYLOAD_SCHEMA:
        raise ValueError("checkpoint payload version is unsupported")
    preflight_names = tuple(
        field.name for field in fields(FrozenAssociationResidualTrainingPreflight)
    )
    environment_names = tuple(
        field.name for field in fields(FrozenAssociationTrainingEnvironment)
    )
    certificate_names = tuple(
        field.name for field in fields(ContinuousCorrectionCertificate)
    )
    snapshot_names = tuple(
        field.name for field in fields(FiniteAssociationMLPSnapshot)
    )
    preflight = FrozenAssociationResidualTrainingPreflight(
        **_exact_payload_keys(
            values["preflight"], preflight_names, name="preflight"
        )
    )
    environment = FrozenAssociationTrainingEnvironment(
        **_exact_payload_keys(
            values["environment"], environment_names, name="environment"
        )
    )
    snapshot = FiniteAssociationMLPSnapshot(
        **_exact_payload_keys(
            values["snapshot"], snapshot_names, name="snapshot"
        )
    )
    certificate = ContinuousCorrectionCertificate(
        **_exact_payload_keys(
            values["certificate"], certificate_names, name="certificate"
        )
    )
    completion_receipt_names = tuple(
        field.name for field in fields(FrozenAssociationOptimizerCompletionReceipt)
    )
    completion_receipt = FrozenAssociationOptimizerCompletionReceipt(
        **_exact_payload_keys(
            values["optimizer_completion_receipt"],
            completion_receipt_names,
            name="optimizer_completion_receipt",
        )
    )
    guide_grid = values["certificate_guide_grid"]
    if guide_grid is not None and not isinstance(guide_grid, torch.Tensor):
        raise TypeError("certificate_guide_grid must be a tensor or None")
    fixture = build_frozen_association_residual_fixture()
    mismatch = (
        _mismatched_guide(fixture)
        if preflight.method == MISMATCH_METHOD
        else None
    )
    return FittedAssociationResidualCheckpoint(
        preflight=preflight,
        environment=environment,
        fixture=fixture,
        mismatched_guide=mismatch,
        final_snapshot=snapshot,
        certificate=certificate,
        certificate_guide_grid=guide_grid,
        run_key_sha256=values["run_key_sha256"],
        prepared_ledger_sha256=values["prepared_ledger_sha256"],
        execution_runtime_sha256=values["execution_runtime_sha256"],
        classifier_sha256=values["classifier_sha256"],
        final_empirical_risk=values["final_empirical_risk"],
        maximum_unclipped_gradient_norm=values[
            "maximum_unclipped_gradient_norm"
        ],
        optimizer_steps_taken=values["optimizer_steps_taken"],
        optimizer_transcript_sha256=values["optimizer_transcript_sha256"],
        optimizer_completion_receipt=completion_receipt,
        elapsed_training_seconds=values["elapsed_training_seconds"],
        total_cpu_seconds=values["total_cpu_seconds"],
        total_wall_seconds=values["total_wall_seconds"],
        process_peak_rss_bytes=values["process_peak_rss_bytes"],
    )


def load_fitted_association_checkpoint(
    path: object,
    *,
    expected_sha256: object,
) -> FittedAssociationResidualCheckpoint:
    """Check payload bytes and reconstruct a non-production fitted record.

    This boundary verifies only the supplied file digest and internal model
    custody.  Production evaluation additionally requires the canonical
    SUCCESS-ledger loader, which returns a ledger-verified wrapper.
    """

    checkpoint_path = Path(path)
    expected = _require_sha256(expected_sha256, name="expected_sha256")
    maximum_bytes = 128 * 1024 * 1024
    try:
        metadata = os.lstat(checkpoint_path)
    except FileNotFoundError as error:
        raise ValueError("checkpoint path is absent") from error
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("checkpoint path is not a regular file")
    if metadata.st_size <= 0 or metadata.st_size > maximum_bytes:
        raise ValueError("checkpoint payload has an invalid byte length")
    descriptor = os.open(
        os.fspath(checkpoint_path),
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
        ) != (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
        ):
            raise RuntimeError("checkpoint identity changed while opening")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            payload_bytes = handle.read(maximum_bytes + 1)
    finally:
        os.close(descriptor)
    if len(payload_bytes) > maximum_bytes:
        raise ValueError("checkpoint payload exceeds the frozen byte limit")
    after = os.lstat(checkpoint_path)
    if (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ) != (
        opened.st_dev,
        opened.st_ino,
        opened.st_size,
        opened.st_mtime_ns,
    ):
        raise RuntimeError("checkpoint identity changed while reading")
    if hashlib.sha256(payload_bytes).hexdigest() != expected:
        raise ValueError("checkpoint file digest does not match the supplied receipt")
    payload = torch.load(
        io.BytesIO(payload_bytes),
        map_location="cpu",
        weights_only=True,
    )
    return fitted_association_checkpoint_from_payload(payload)


def _training_environment_sha256(
    environment: FrozenAssociationTrainingEnvironment,
) -> str:
    if type(environment) is not FrozenAssociationTrainingEnvironment:
        raise TypeError("environment must be the exact frozen record")
    return _digest_parts(
        b"heterodiff-a1-association-training-environment-v1",
        environment.python_version,
        environment.numpy_version,
        environment.scipy_version,
        environment.torch_version,
        "cpu-only" if environment.torch_cpu_only else "accelerator-present",
        environment.torch_threads,
        environment.torch_interop_threads,
        "deterministic"
        if environment.deterministic_algorithms
        else "nondeterministic",
    )


def _independent_guide_sha256(
    guide: IndependentFiniteAtomicReferenceGuide,
) -> str:
    if not isinstance(guide, IndependentFiniteAtomicReferenceGuide):
        raise TypeError("guide must be an IndependentFiniteAtomicReferenceGuide")
    return _digest_parts(
        b"heterodiff-a1-association-independent-guide-v1",
        np.asarray(guide.immigration_rates),
        np.asarray(guide.per_particle_death_rates),
        np.asarray(guide.replacement_rates),
        np.asarray(guide.one_particle_subgenerator),
        np.asarray(guide.terminal_emission_mass),
    )


def _require_exact_certificate_guide_grid(
    preflight: FrozenAssociationResidualTrainingPreflight,
    fixture: FrozenAssociationResidualFixture,
    certificate_guide_grid: Optional[torch.Tensor],
) -> None:
    """Bind the 22-input certificate to the analytic guide actually evaluated."""

    if preflight.method != GUIDE_INPUT_METHOD:
        if certificate_guide_grid is not None:
            raise ValueError("only guide-input checkpoints may carry a guide grid")
        return
    if not isinstance(certificate_guide_grid, torch.Tensor):
        raise TypeError("guide-input checkpoint must carry its certificate guide grid")
    direct_times = np.arange(
        CERTIFICATE_GRID_INTERVALS + 1, dtype=np.float64
    ) / float(CERTIFICATE_GRID_INTERVALS)
    expected = torch.tensor(
        _classifier_guide_grid(fixture, direct_times, mismatch=False),
        dtype=torch.float64,
    )
    if not torch.equal(certificate_guide_grid, expected):
        raise ValueError(
            "certificate guide grid differs from the frozen analytic guide"
        )


def _fitted_classifier_sha256(
    preflight: FrozenAssociationResidualTrainingPreflight,
    environment: FrozenAssociationTrainingEnvironment,
    fixture: FrozenAssociationResidualFixture,
    snapshot: FiniteAssociationMLPSnapshot,
    certificate: ContinuousCorrectionCertificate,
    certificate_guide_grid: Optional[torch.Tensor],
    execution_runtime_sha256: object,
) -> str:
    """Bind the complete executable classifier, not only its MLP tensors."""

    if type(preflight) is not FrozenAssociationResidualTrainingPreflight:
        raise TypeError("preflight must be the exact frozen record")
    runtime_digest = _require_sha256(
        execution_runtime_sha256, name="execution_runtime_sha256"
    )
    actual_digests = frozen_association_fixture_content_digests(fixture)
    fixture_token = frozen_association_fixture_sha256(actual_digests)
    if fixture_token != preflight.fixture_sha256:
        raise ValueError("classifier fixture differs from its preflight")
    _require_exact_certificate_guide_grid(
        preflight, fixture, certificate_guide_grid
    )
    require_matching_snapshot_continuous_certificate(
        snapshot,
        certificate,
        frozen_fixture_sha256=fixture_token,
        guide_classifier_logit_grid=certificate_guide_grid,
    )
    if preflight.method in (DIRECT_METHOD, STRONG_DIRECT_METHOD):
        guide_identity = "no-guide"
    elif preflight.method in (GUIDED_METHOD, GUIDE_INPUT_METHOD):
        guide_identity = _independent_guide_sha256(fixture.guide)
    elif preflight.method == MISMATCH_METHOD:
        guide_identity = _independent_guide_sha256(_mismatched_guide(fixture))
    else:  # pragma: no cover - preflight validates this already
        raise AssertionError("unhandled learner method")
    certificate_guide_identity = (
        "no-certificate-guide-grid"
        if certificate_guide_grid is None
        else _digest_parts(
            b"heterodiff-a1-association-certificate-guide-grid-v1",
            certificate_guide_grid,
        )
    )
    return _digest_parts(
        b"heterodiff-a1-association-full-classifier-v1",
        preflight.preflight_sha256,
        preflight.source_sha256,
        preflight.configuration_sha256,
        _training_environment_sha256(environment),
        runtime_digest,
        preflight.method,
        preflight.composition_mode,
        preflight.input_features,
        preflight.hidden_width,
        fixture_token,
        *actual_digests,
        guide_identity,
        snapshot.parameter_sha256,
        certificate.parameter_sha256,
        certificate.feature_sha256,
        certificate.certificate_sha256,
        certificate_guide_identity,
    )


def _training_tensors(
    fixture: FrozenAssociationResidualFixture,
    dataset: FrozenAssociationResidualSampleDataset,
    method: str,
) -> Tuple[
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    Optional[torch.Tensor],
    torch.Tensor,
    torch.Tensor,
]:
    times = torch.tensor(np.asarray(dataset.direct_times), dtype=torch.float64)
    latent_states, anchor_states, overflow_base = _pair_count_tensors(fixture)
    latent = latent_states[torch.tensor(dataset.state_indices, dtype=torch.int64)]
    anchors = anchor_states[
        torch.tensor(dataset.observation_indices, dtype=torch.int64)
    ]
    overflow = overflow_base[
        torch.tensor(dataset.observation_indices, dtype=torch.int64)
    ]

    correct_guide = None
    selected_guide = None
    if method in (GUIDED_METHOD, GUIDE_INPUT_METHOD):
        grid = (
            np.log(np.asarray(fixture.guide_density_grid))
            - np.log(fixture.population.observation_marginal_density)[None, None, :]
        )
        selected = grid[
            dataset.time_indices,
            dataset.state_indices,
            dataset.observation_indices,
        ]
        correct_guide = torch.tensor(selected, dtype=torch.float64)
        selected_guide = correct_guide
    elif method == MISMATCH_METHOD:
        mismatch_grid = _classifier_guide_grid(
            fixture, np.asarray(fixture.times), mismatch=True
        )
        selected = mismatch_grid[
            dataset.time_indices,
            dataset.state_indices,
            dataset.observation_indices,
        ]
        selected_guide = torch.tensor(selected, dtype=torch.float64)

    features = finite_association_features(
        times,
        latent,
        anchors,
        overflow,
        guide_classifier_logit=correct_guide
        if method == GUIDE_INPUT_METHOD
        else None,
    )
    terminal = torch.tensor(
        fixture.population.optimal_log_density_ratio[
            -1, dataset.state_indices, dataset.observation_indices
        ],
        dtype=torch.float64,
    )
    labels = torch.tensor(dataset.class_labels, dtype=torch.int64)
    importance = torch.tensor(dataset.importance_weights, dtype=torch.float64)
    return features, times, terminal, selected_guide, labels, importance


def prepare_frozen_association_residual_training(
    seed: object,
    budget: object,
    method: object,
) -> PreparedAssociationResidualTraining:
    """Prepare and hash one run without executing an optimizer update."""

    checked_seed = _require_seed(seed)
    checked_budget = _require_budget(budget)
    checked_method = _require_method(method)
    mode, inputs, width, updates = _method_contract(checked_method)

    if not inspect_frozen_association_training_environment().versions_match:
        raise RuntimeError(
            "training preparation must use the preregistered Python/NumPy/"
            "SciPy/CPU-PyTorch runtime"
        )

    prerequisite = run_association_residual_prerequisite_gate()
    observed_digests = (
        prerequisite.generator_digest,
        prerequisite.observation_digest,
        prerequisite.population_digest,
        prerequisite.guide_digest,
        prerequisite.split_digest,
    )
    if not prerequisite.passed or observed_digests != FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS:
        raise RuntimeError("the frozen prerequisite gate or its digests changed")
    fixture = build_frozen_association_residual_fixture()
    actual_digests = frozen_association_fixture_content_digests(fixture)
    if actual_digests != observed_digests:
        raise RuntimeError(
            "the supplied fixture contents do not match the prerequisite gate"
        )
    fixture_token = frozen_association_fixture_sha256(actual_digests)
    source_digest = frozen_association_training_source_sha256()
    configuration_digest = frozen_association_training_configuration_sha256(
        source_sha256=source_digest
    )
    custody = build_frozen_association_residual_sample_custody(checked_seed)
    dataset = custody.dataset(checked_budget)
    schedule = custody.batch_schedule(checked_budget, updates)

    torch_seed = _torch_model_seed(custody)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(torch_seed)
    model = FiniteAssociationCorrectionNetwork(
        generator=generator,
        input_features=inputs,
        hidden_width=width,
    )
    initial_snapshot = snapshot_finite_association_mlp(model)
    features, times, terminal, guide, labels, importance = _training_tensors(
        fixture, dataset, checked_method
    )
    tensor_digest = _digest_parts(
        b"heterodiff-a1-association-training-tensors-v1",
        features,
        times,
        terminal,
        guide if guide is not None else "no-guide",
        labels,
        importance,
    )
    parameter_count = model.parameter_count
    multiply_add_count = inputs * width + width * width + width
    preflight_digest = _digest_parts(
        b"heterodiff-a1-association-training-preflight-v1",
        checked_seed,
        checked_budget,
        checked_method,
        mode,
        inputs,
        width,
        updates,
        torch_seed,
        source_digest,
        configuration_digest,
        fixture_token,
        custody.digest,
        *custody.dataset_digests,
        *custody.batch_schedule_digests,
        dataset.digest,
        schedule.digest,
        tensor_digest,
        initial_snapshot.parameter_sha256,
        parameter_count,
        multiply_add_count,
    )
    preflight = FrozenAssociationResidualTrainingPreflight(
        seed=checked_seed,
        budget=checked_budget,
        method=checked_method,
        composition_mode=mode,
        input_features=inputs,
        hidden_width=width,
        updates=updates,
        torch_generator_seed=torch_seed,
        source_sha256=source_digest,
        configuration_sha256=configuration_digest,
        fixture_sha256=fixture_token,
        custody_sha256=custody.digest,
        all_dataset_sha256=custody.dataset_digests,
        all_batch_schedule_sha256=custody.batch_schedule_digests,
        dataset_sha256=dataset.digest,
        batch_schedule_sha256=schedule.digest,
        training_tensor_sha256=tensor_digest,
        initial_parameter_sha256=initial_snapshot.parameter_sha256,
        preflight_sha256=preflight_digest,
        parameter_count=parameter_count,
        forward_multiply_add_count=multiply_add_count,
    )
    return PreparedAssociationResidualTraining(
        preflight=preflight,
        fixture=fixture,
        custody=custody,
        dataset=dataset,
        model=model,
        features=features,
        direct_times=times,
        terminal_classifier_logits=terminal,
        guide_classifier_logits=guide,
        class_labels=labels,
        importance_weights=importance,
    )


def frozen_association_sampled_bce(
    model: FiniteAssociationCorrectionNetwork,
    features: torch.Tensor,
    direct_times: torch.Tensor,
    terminal_classifier_logits: torch.Tensor,
    class_labels: torch.Tensor,
    importance_weights: torch.Tensor,
    *,
    composition_mode: str,
    guide_classifier_logits: Optional[torch.Tensor],
) -> torch.Tensor:
    """Return the unnormalized-class weighted empirical BCE objective."""

    if composition_mode not in ("direct", "guided", "mismatch", "input"):
        raise ValueError("composition_mode is not frozen")
    if class_labels.dtype != torch.int64 or class_labels.device.type != "cpu":
        raise TypeError("class_labels must be a CPU int64 tensor")
    if class_labels.ndim != 1 or class_labels.numel() == 0 or not torch.all(
        (class_labels == 0) | (class_labels == 1)
    ):
        raise ValueError("class_labels must be a nonempty binary vector")
    if tuple(importance_weights.shape) != tuple(class_labels.shape):
        raise ValueError("importance weights and labels must have one shape")
    if importance_weights.dtype != torch.float64 or torch.any(
        ~torch.isfinite(importance_weights)
    ) or torch.any(importance_weights <= 0.0):
        raise ValueError("importance_weights must be positive finite float64")
    logits = finite_association_logits(
        model,
        features,
        direct_times,
        terminal_classifier_logits,
        mode=composition_mode,
        guide_classifier_logit=guide_classifier_logits,
    )
    if tuple(logits.shape) != tuple(class_labels.shape):
        raise ValueError("logits and labels must have one shape")
    per_example = torch.where(
        class_labels == 1,
        torch_functional.softplus(-logits),
        torch_functional.softplus(logits),
    )
    result = torch.mean(importance_weights * per_example)
    if result.dtype != torch.float64 or result.ndim != 0 or not torch.isfinite(result):
        raise ArithmeticError("sampled BCE objective is invalid")
    return result


def _certificate_guide_grid(
    prepared: PreparedAssociationResidualTraining,
) -> Optional[torch.Tensor]:
    if prepared.preflight.method != GUIDE_INPUT_METHOD:
        return None
    times = np.arange(
        CERTIFICATE_GRID_INTERVALS + 1, dtype=np.float64
    ) / float(CERTIFICATE_GRID_INTERVALS)
    values = _classifier_guide_grid(prepared.fixture, times, mismatch=False)
    return torch.tensor(values, dtype=torch.float64)


def _sampled_optimizer_transcript_seed_sha256(
    preflight: FrozenAssociationResidualTrainingPreflight,
    execution_permit: FrozenAssociationExecutionPermit,
) -> str:
    """Bind the rolling transcript to the complete consumed permit custody."""

    if type(preflight) is not FrozenAssociationResidualTrainingPreflight:
        raise TypeError("optimizer transcript seed requires the exact preflight")
    if type(execution_permit) is not FrozenAssociationExecutionPermit:
        raise TypeError("optimizer transcript seed requires the exact permit")
    if not execution_permit._consumed:
        raise RuntimeError("optimizer transcript seed requires a consumed permit")
    if (
        preflight.preflight_sha256 != execution_permit.preflight_sha256
        or _frozen_training_preflight_sha256(preflight)
        != preflight.preflight_sha256
    ):
        raise RuntimeError(
            "optimizer transcript preflight differs from consumed permit custody"
        )
    session = execution_permit._worker_session.record
    return _digest_parts(
        b"heterodiff-a1-sampled-optimizer-transcript-seed-v3",
        _OPTIMIZER_TRANSCRIPT_SCHEMA,
        preflight.seed,
        preflight.budget,
        preflight.method,
        execution_permit.run_key_sha256,
        execution_permit.campaign_sha256,
        execution_permit.ledger_directory,
        execution_permit.worker_process_id,
        execution_permit.worker_parent_process_id,
        execution_permit.worker_session_sha256,
        session["launch_authorization_sha256"],
        session["launch_receipt_sha256"],
        execution_permit.execution_runtime_sha256,
        execution_permit.prepared_ledger_sha256,
        execution_permit.running_ledger_sha256,
        preflight.preflight_sha256,
        preflight.initial_parameter_sha256,
        preflight.updates,
        preflight.batch_schedule_sha256,
        preflight.training_tensor_sha256,
    )


def _new_sampled_optimizer_transcript(seed_sha256: object):
    seed = _require_sha256(seed_sha256, name="optimizer_transcript_seed_sha256")
    transcript = hashlib.sha256()
    transcript.update(_OPTIMIZER_TRANSCRIPT_SCHEMA.encode("ascii"))
    transcript.update(b"\0")
    transcript.update(seed.encode("ascii"))
    transcript.update(b"\0")
    return transcript


def _append_sampled_optimizer_transcript_update(
    transcript: object,
    *,
    update_index: object,
    learning_rate: object,
    objective: object,
    unclipped_gradient_norm: object,
    post_update_parameter_sha256: object,
) -> None:
    """Append one update and its resulting full-parameter identity."""

    if not hasattr(transcript, "update"):
        raise TypeError("optimizer transcript must be a live hash state")
    if (
        isinstance(update_index, (bool, np.bool_))
        or not isinstance(update_index, Integral)
        or int(update_index) < 0
    ):
        raise ValueError("optimizer transcript update index is invalid")
    numeric = (
        float(learning_rate),
        float(objective),
        float(unclipped_gradient_norm),
    )
    if any(not math.isfinite(value) for value in numeric):
        raise ValueError("optimizer transcript update scalar is non-finite")
    parameter_sha256 = _require_sha256(
        post_update_parameter_sha256,
        name="post_update_parameter_sha256",
    )
    for value in (
        str(int(update_index)),
        numeric[0].hex(),
        numeric[1].hex(),
        numeric[2].hex(),
        parameter_sha256,
    ):
        transcript.update(value.encode("ascii"))
        transcript.update(b"\0")


def _require_last_post_update_matches_final(
    last_post_update_parameter_sha256: object,
    final_parameter_sha256: object,
) -> None:
    last = _require_sha256(
        last_post_update_parameter_sha256,
        name="last_post_update_parameter_sha256",
    )
    final = _require_sha256(
        final_parameter_sha256, name="final_parameter_sha256"
    )
    if last != final:
        raise RuntimeError(
            "last post-update parameters differ from the certified snapshot"
        )


def execute_frozen_association_residual_training(
    prepared: PreparedAssociationResidualTraining,
    *,
    execution_permit: object = None,
) -> OptimizerCompletedAssociationResidualTraining:
    """Execute exactly one previously emitted frozen training preflight."""

    if type(prepared) is not PreparedAssociationResidualTraining:
        raise TypeError("prepared must be an exact PreparedAssociationResidualTraining")
    if type(execution_permit) is not FrozenAssociationExecutionPermit:
        raise TypeError(
            "learner execution requires a single-use isolated-worker permit"
        )
    execution_permit.validate_for(prepared.preflight)
    environment = configure_frozen_association_training_environment()
    source_digest = frozen_association_training_source_sha256()
    configuration_digest = frozen_association_training_configuration_sha256(
        source_sha256=source_digest
    )
    if (
        source_digest != prepared.preflight.source_sha256
        or configuration_digest != prepared.preflight.configuration_sha256
        or _frozen_training_preflight_sha256(prepared.preflight)
        != prepared.preflight.preflight_sha256
    ):
        raise RuntimeError("source/configuration/preflight custody changed")
    fixture_digests = frozen_association_fixture_content_digests(prepared.fixture)
    if (
        fixture_digests != FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS
        or frozen_association_fixture_sha256(fixture_digests)
        != prepared.preflight.fixture_sha256
    ):
        raise RuntimeError("prepared fixture contents changed after preflight")
    mode, inputs, width, updates = _method_contract(prepared.preflight.method)
    expected_multiply_adds = inputs * width + width * width + width
    if (
        prepared.preflight.composition_mode != mode
        or prepared.preflight.input_features != inputs
        or prepared.preflight.hidden_width != width
        or prepared.preflight.updates != updates
        or prepared.preflight.torch_generator_seed != _torch_model_seed(prepared.custody)
        or prepared.model.input_features != inputs
        or prepared.model.hidden_width != width
        or prepared.model.parameter_count != prepared.preflight.parameter_count
        or expected_multiply_adds != prepared.preflight.forward_multiply_add_count
    ):
        raise RuntimeError("model/RNG/count contract changed after preflight")
    initial = snapshot_finite_association_mlp(prepared.model)
    if initial.parameter_sha256 != prepared.preflight.initial_parameter_sha256:
        raise RuntimeError("prepared model changed after its preflight was emitted")
    if (
        _prepared_training_tensor_sha256(prepared)
        != prepared.preflight.training_tensor_sha256
    ):
        raise RuntimeError("prepared training tensors changed after preflight")
    if (
        prepared.custody.digest != prepared.preflight.custody_sha256
        or prepared.dataset.digest != prepared.preflight.dataset_sha256
        or prepared.custody.dataset_digests
        != prepared.preflight.all_dataset_sha256
        or prepared.custody.batch_schedule_digests
        != prepared.preflight.all_batch_schedule_sha256
    ):
        raise RuntimeError("sample custody changed after preflight")
    schedule = prepared.custody.batch_schedule(
        prepared.preflight.budget, prepared.preflight.updates
    )
    if schedule.digest != prepared.preflight.batch_schedule_sha256:
        raise RuntimeError("batch schedule changed after preflight")

    # PREPARED is already durable in the exactly-once ledger.  Consumption is
    # the final operation before constructing the optimizer/update-zero state.
    execution_permit.consume_for(prepared.preflight)
    optimizer = make_finite_association_adamw(prepared.model)
    maximum_gradient_norm = 0.0
    optimizer_steps_taken = 0
    transcript = _new_sampled_optimizer_transcript(
        _sampled_optimizer_transcript_seed_sha256(
            prepared.preflight, execution_permit
        )
    )
    last_post_update_parameter_sha256 = None
    start = time.perf_counter()
    for update_index, batch_array in enumerate(schedule.batch_indices):
        batch = torch.tensor(batch_array, dtype=torch.int64)
        guide = (
            None
            if prepared.guide_classifier_logits is None
            else prepared.guide_classifier_logits[batch]
        )
        loss = frozen_association_sampled_bce(
            prepared.model,
            prepared.features[batch],
            prepared.direct_times[batch],
            prepared.terminal_classifier_logits[batch],
            prepared.class_labels[batch],
            prepared.importance_weights[batch],
            composition_mode=prepared.preflight.composition_mode,
            guide_classifier_logits=guide,
        )
        update = finite_association_adamw_update(
            prepared.model,
            optimizer,
            loss,
            update_index=update_index,
            total_updates=prepared.preflight.updates,
        )
        maximum_gradient_norm = max(
            maximum_gradient_norm, update.unclipped_gradient_norm
        )
        optimizer_steps_taken += 1
        last_post_update_parameter_sha256 = (
            snapshot_finite_association_mlp(prepared.model).parameter_sha256
        )
        _append_sampled_optimizer_transcript_update(
            transcript,
            update_index=update.update_index,
            learning_rate=update.learning_rate,
            objective=loss.detach().item(),
            unclipped_gradient_norm=update.unclipped_gradient_norm,
            post_update_parameter_sha256=(
                last_post_update_parameter_sha256
            ),
        )
    if optimizer_steps_taken != prepared.preflight.updates:
        raise RuntimeError("optimizer loop did not execute the frozen update count")
    optimizer_transcript_sha256 = transcript.hexdigest()
    elapsed = time.perf_counter() - start
    with torch.no_grad():
        final_risk = float(
            frozen_association_sampled_bce(
                prepared.model,
                prepared.features,
                prepared.direct_times,
                prepared.terminal_classifier_logits,
                prepared.class_labels,
                prepared.importance_weights,
                composition_mode=prepared.preflight.composition_mode,
                guide_classifier_logits=prepared.guide_classifier_logits,
            ).item()
        )

    certificate_guide = _certificate_guide_grid(prepared)
    certificate = certify_finite_association_continuous_correction(
        prepared.model,
        frozen_fixture_sha256=prepared.preflight.fixture_sha256,
        guide_classifier_logit_grid=certificate_guide,
    )
    require_matching_continuous_certificate(
        prepared.model,
        certificate,
        frozen_fixture_sha256=prepared.preflight.fixture_sha256,
        guide_classifier_logit_grid=certificate_guide,
    )
    final_snapshot = snapshot_finite_association_mlp(prepared.model)
    _require_last_post_update_matches_final(
        last_post_update_parameter_sha256,
        final_snapshot.parameter_sha256,
    )
    if final_snapshot.parameter_sha256 != certificate.parameter_sha256:
        raise RuntimeError("certified checkpoint digest changed unexpectedly")
    classifier_digest = _fitted_classifier_sha256(
        prepared.preflight,
        environment,
        prepared.fixture,
        final_snapshot,
        certificate,
        certificate_guide,
        execution_permit.execution_runtime_sha256,
    )
    total_cpu = time.process_time() - execution_permit.total_cpu_start
    total_wall = time.perf_counter() - execution_permit.total_wall_start
    peak_rss_bytes = _process_peak_rss_bytes()
    resource_sha256 = _optimizer_completion_resource_sha256(
        elapsed_training_seconds=elapsed,
        total_cpu_seconds=total_cpu,
        total_wall_seconds=total_wall,
        process_peak_rss_bytes=peak_rss_bytes,
    )
    checkpoint_identity_sha256 = (
        _optimizer_completion_checkpoint_identity_sha256(
            preflight_sha256=prepared.preflight.preflight_sha256,
            run_key_sha256=execution_permit.run_key_sha256,
            prepared_ledger_sha256=execution_permit.prepared_ledger_sha256,
            running_ledger_sha256=execution_permit.running_ledger_sha256,
            execution_runtime_sha256=execution_permit.execution_runtime_sha256,
            classifier_sha256=classifier_digest,
            parameter_sha256=final_snapshot.parameter_sha256,
            certificate_sha256=certificate.certificate_sha256,
            final_empirical_risk=final_risk,
            maximum_unclipped_gradient_norm=maximum_gradient_norm,
            optimizer_steps_taken=optimizer_steps_taken,
            optimizer_transcript_sha256=optimizer_transcript_sha256,
            resource_sha256=resource_sha256,
        )
    )
    completion_receipt = _build_optimizer_completion_receipt(
        preflight=prepared.preflight,
        execution_permit=execution_permit,
        optimizer_steps_taken=optimizer_steps_taken,
        optimizer_transcript_sha256=optimizer_transcript_sha256,
        last_post_update_parameter_sha256=(
            last_post_update_parameter_sha256
        ),
        final_parameter_sha256=final_snapshot.parameter_sha256,
        certificate_sha256=certificate.certificate_sha256,
        classifier_sha256=classifier_digest,
        resource_sha256=resource_sha256,
        checkpoint_identity_sha256=checkpoint_identity_sha256,
    )
    checkpoint = FittedAssociationResidualCheckpoint(
        preflight=prepared.preflight,
        environment=environment,
        fixture=prepared.fixture,
        mismatched_guide=(
            _mismatched_guide(prepared.fixture)
            if prepared.preflight.method == MISMATCH_METHOD
            else None
        ),
        final_snapshot=final_snapshot,
        certificate=certificate,
        certificate_guide_grid=certificate_guide,
        run_key_sha256=execution_permit.run_key_sha256,
        prepared_ledger_sha256=execution_permit.prepared_ledger_sha256,
        execution_runtime_sha256=execution_permit.execution_runtime_sha256,
        classifier_sha256=classifier_digest,
        final_empirical_risk=final_risk,
        maximum_unclipped_gradient_norm=maximum_gradient_norm,
        optimizer_steps_taken=optimizer_steps_taken,
        optimizer_transcript_sha256=optimizer_transcript_sha256,
        optimizer_completion_receipt=completion_receipt,
        elapsed_training_seconds=elapsed,
        total_cpu_seconds=total_cpu,
        total_wall_seconds=total_wall,
        process_peak_rss_bytes=peak_rss_bytes,
    )
    capability = _FrozenAssociationOptimizerCompletionCapability(
        completion_receipt,
        execution_permit,
        _construction_key=_OPTIMIZER_COMPLETION_CAPABILITY_KEY,
    )
    return OptimizerCompletedAssociationResidualTraining(
        checkpoint,
        capability,
        _construction_key=_COMPLETED_TRAINING_CONSTRUCTION_KEY,
    )


def _clone_finite_association_snapshot(
    snapshot: FiniteAssociationMLPSnapshot,
) -> FiniteAssociationMLPSnapshot:
    return FiniteAssociationMLPSnapshot(
        input_features=snapshot.input_features,
        hidden_width=snapshot.hidden_width,
        weight1=snapshot.weight1.detach().clone(),
        bias1=snapshot.bias1.detach().clone(),
        weight2=snapshot.weight2.detach().clone(),
        bias2=snapshot.bias2.detach().clone(),
        weight3=snapshot.weight3.detach().clone(),
        bias3=snapshot.bias3.detach().clone(),
        parameter_sha256=snapshot.parameter_sha256,
    )


def _require_fitted_checkpoint_integrity(
    checkpoint: FittedAssociationResidualCheckpoint,
) -> None:
    if type(checkpoint) is not FittedAssociationResidualCheckpoint:
        raise TypeError("checkpoint must be an exact fitted checkpoint")
    if (
        isinstance(checkpoint.optimizer_steps_taken, (bool, np.bool_))
        or not isinstance(checkpoint.optimizer_steps_taken, Integral)
        or int(checkpoint.optimizer_steps_taken) != checkpoint.preflight.updates
    ):
        raise RuntimeError("checkpoint optimizer step count changed")
    _require_sha256(
        checkpoint.optimizer_transcript_sha256,
        name="optimizer_transcript_sha256",
    )
    source = frozen_association_training_source_sha256()
    configuration = frozen_association_training_configuration_sha256(
        source_sha256=source
    )
    if (
        source != checkpoint.preflight.source_sha256
        or configuration != checkpoint.preflight.configuration_sha256
        or _frozen_training_preflight_sha256(checkpoint.preflight)
        != checkpoint.preflight.preflight_sha256
    ):
        raise RuntimeError("checkpoint source/configuration/preflight changed")
    require_matching_snapshot_continuous_certificate(
        checkpoint.final_snapshot,
        checkpoint.certificate,
        frozen_fixture_sha256=checkpoint.preflight.fixture_sha256,
        guide_classifier_logit_grid=checkpoint.certificate_guide_grid,
    )
    actual = _fitted_classifier_sha256(
        checkpoint.preflight,
        checkpoint.environment,
        checkpoint.fixture,
        checkpoint.final_snapshot,
        checkpoint.certificate,
        checkpoint.certificate_guide_grid,
        checkpoint.execution_runtime_sha256,
    )
    if actual != checkpoint.classifier_sha256:
        raise RuntimeError("checkpoint full-classifier digest changed")
    _require_optimizer_completion_matches_checkpoint(checkpoint)


class _BoundFittedAssociationLogitGrid:
    """Owned fitted classifier validated at result, not scalar-call, boundaries."""

    __slots__ = (
        "_preflight",
        "_environment",
        "_fixture",
        "_snapshot",
        "_certificate",
        "_certificate_guide_grid",
        "_guide",
        "_classifier_sha256",
        "_execution_runtime_sha256",
        "_latent_base",
        "_anchor_base",
        "_overflow_base",
        "_locked",
    )

    def __init__(self, checkpoint: FittedAssociationResidualCheckpoint) -> None:
        _require_fitted_checkpoint_integrity(checkpoint)
        fixture = build_frozen_association_residual_fixture()
        if (
            frozen_association_fixture_sha256(
                frozen_association_fixture_content_digests(fixture)
            )
            != checkpoint.preflight.fixture_sha256
        ):
            raise RuntimeError("fresh evaluator fixture failed custody")
        snapshot = _clone_finite_association_snapshot(checkpoint.final_snapshot)
        certificate_guide = (
            None
            if checkpoint.certificate_guide_grid is None
            else checkpoint.certificate_guide_grid.detach().clone()
        )
        guide = (
            _mismatched_guide(fixture)
            if checkpoint.preflight.method == MISMATCH_METHOD
            else fixture.guide
            if checkpoint.preflight.method in (GUIDED_METHOD, GUIDE_INPUT_METHOD)
            else None
        )
        latent, anchors, overflow = _pair_count_tensors(fixture)
        object.__setattr__(self, "_preflight", checkpoint.preflight)
        object.__setattr__(self, "_environment", checkpoint.environment)
        object.__setattr__(self, "_fixture", fixture)
        object.__setattr__(self, "_snapshot", snapshot)
        object.__setattr__(self, "_certificate", checkpoint.certificate)
        object.__setattr__(self, "_certificate_guide_grid", certificate_guide)
        object.__setattr__(self, "_guide", guide)
        object.__setattr__(self, "_classifier_sha256", checkpoint.classifier_sha256)
        object.__setattr__(
            self,
            "_execution_runtime_sha256",
            checkpoint.execution_runtime_sha256,
        )
        object.__setattr__(self, "_latent_base", latent)
        object.__setattr__(self, "_anchor_base", anchors)
        object.__setattr__(self, "_overflow_base", overflow)
        object.__setattr__(self, "_locked", True)
        self.assert_integrity()

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("bound fitted classifier is immutable")
        object.__setattr__(self, name, value)

    def assert_integrity(self) -> None:
        current_environment = inspect_frozen_association_training_environment()
        if current_environment != self._environment:
            raise RuntimeError("bound classifier execution environment changed")
        source = frozen_association_training_source_sha256()
        configuration = frozen_association_training_configuration_sha256(
            source_sha256=source
        )
        if (
            source != self._preflight.source_sha256
            or configuration != self._preflight.configuration_sha256
        ):
            raise RuntimeError("bound classifier source/configuration changed")
        actual = _fitted_classifier_sha256(
            self._preflight,
            self._environment,
            self._fixture,
            self._snapshot,
            self._certificate,
            self._certificate_guide_grid,
            self._execution_runtime_sha256,
        )
        if actual != self._classifier_sha256:
            raise RuntimeError("bound full-classifier digest changed")

    def __call__(self, direct_times: object) -> np.ndarray:
        times_array = np.asarray(direct_times, dtype=np.float64)
        if times_array.ndim != 1 or times_array.size == 0:
            raise ValueError("direct_times must be a nonempty vector")
        if not np.all(np.isfinite(times_array)) or np.any(
            (times_array < 0.0) | (times_array > 1.0)
        ):
            raise ValueError("direct_times must be finite and lie in [0, 1]")
        shape = (times_array.size, 20, 21)
        times = torch.tensor(times_array, dtype=torch.float64)[
            :, None, None
        ].expand(shape)
        latent = self._latent_base[None, :, None, :].expand(shape + (3,))
        anchors = self._anchor_base[None, None, :, :].expand(shape + (3,))
        overflow = self._overflow_base[None, None, :].expand(shape)
        guide_array = None
        if self._guide is not None:
            density = np.stack(
                [
                    self._guide.density_grid(float(value))
                    for value in times_array
                ],
                axis=0,
            )
            guide_array = np.log(density) - np.log(
                self._fixture.population.observation_marginal_density
            )[None, None, :]
        guide = (
            None
            if guide_array is None
            else torch.tensor(guide_array, dtype=torch.float64)
        )
        features = finite_association_features(
            times,
            latent,
            anchors,
            overflow,
            guide_classifier_logit=(
                guide if self._preflight.method == GUIDE_INPUT_METHOD else None
            ),
        )
        terminal = torch.tensor(
            self._fixture.population.optimal_log_density_ratio[-1],
            dtype=torch.float64,
        )[None, :, :].expand(shape)
        with torch.no_grad():
            logits = _finite_association_validated_snapshot_logits(
                self._snapshot,
                features,
                times,
                terminal,
                mode=self._preflight.composition_mode,
                guide_classifier_logit=guide,
            )
        result = logits.detach().numpy().copy()
        if result.shape != shape or not np.all(np.isfinite(result)):
            raise ArithmeticError("certified checkpoint returned an invalid grid")
        return result


def certified_association_checkpoint_logit_grid(
    verified_checkpoint: LedgerVerifiedFittedAssociationCheckpoint,
    direct_times: object,
) -> np.ndarray:
    """Evaluate a checkpoint with integrity checks around this whole result."""

    if type(verified_checkpoint) is not LedgerVerifiedFittedAssociationCheckpoint:
        raise TypeError("production evaluation requires a SUCCESS-ledger checkpoint")
    from heterodiff.experiments.finite_association_isolated_runner import (
        revalidate_successful_frozen_association_checkpoint,
    )

    revalidate_successful_frozen_association_checkpoint(verified_checkpoint)
    checkpoint = verified_checkpoint.checkpoint
    bound = _BoundFittedAssociationLogitGrid(checkpoint)
    try:
        result = bound(direct_times)
    finally:
        bound.assert_integrity()
        revalidate_successful_frozen_association_checkpoint(verified_checkpoint)
    return result


def bind_fitted_association_checkpoint_evaluator(
    verified_checkpoint: LedgerVerifiedFittedAssociationCheckpoint,
):
    """Bind an owned snapshot and complete production classifier identity."""

    if type(verified_checkpoint) is not LedgerVerifiedFittedAssociationCheckpoint:
        raise TypeError("production binding requires a SUCCESS-ledger checkpoint")
    from heterodiff.experiments.finite_association_isolated_runner import (
        revalidate_successful_frozen_association_checkpoint,
    )

    revalidate_successful_frozen_association_checkpoint(verified_checkpoint)
    from heterodiff.evaluation.finite_association_residual_evaluator import (
        _bind_production_finite_association_logit_evaluator,
    )

    return _bind_production_finite_association_logit_evaluator(
        verified_checkpoint
    )


__all__ = [
    "DIRECT_METHOD",
    "FittedAssociationResidualCheckpoint",
    "FrozenAssociationResidualTrainingPreflight",
    "FrozenAssociationTrainingEnvironment",
    "GUIDED_METHOD",
    "GUIDE_INPUT_METHOD",
    "LedgerVerifiedFittedAssociationCheckpoint",
    "LEARNER_METHODS",
    "MISMATCH_METHOD",
    "PreparedAssociationResidualTraining",
    "STRONG_DIRECT_METHOD",
    "bind_fitted_association_checkpoint_evaluator",
    "certified_association_checkpoint_logit_grid",
    "configure_frozen_association_training_environment",
    "execute_frozen_association_residual_training",
    "fitted_association_checkpoint_from_payload",
    "fitted_association_checkpoint_payload",
    "frozen_association_sampled_bce",
    "frozen_association_training_configuration_sha256",
    "frozen_association_training_source_sha256",
    "inspect_frozen_association_training_environment",
    "load_fitted_association_checkpoint",
    "prepare_frozen_association_residual_training",
]
