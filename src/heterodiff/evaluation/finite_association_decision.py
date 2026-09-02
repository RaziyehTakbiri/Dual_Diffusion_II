"""Fail-closed aggregation for the frozen finite A1 campaign.

This module implements the result-independent decision logic in Sections 7
and 8 of ``research/62_a1_association_guided_residual_falsification_spec.md``.
It never trains a learner.  Production admission accepts only the loader-only
120-member aggregate and never accepts caller-supplied sampled metric records.
The current aggregate is custody-only, so production returns ``HOLD`` until a
later execution-order authority explicitly makes it scientifically eligible.
The guarded future metric path starts from the aggregate's checkpoint wrappers,
recomputes every non-path/path metric, and reopens the aggregate after that work.

An incomplete campaign returns ``NOT_RUN``.  Custody or numerical failures
return ``HOLD``.  A complete, numerically valid campaign that misses any
frozen material criterion returns ``STOP``.  ``PASS`` is therefore reachable
only from all 120 canonical sampled coordinates plus the independently built
guide-alone, prerequisite, oracle-product, and rank-stress controls.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
import hashlib
import math
from numbers import Integral, Real
from types import SimpleNamespace
from typing import Callable, Optional, Tuple

import numpy as np

from heterodiff.evaluation.finite_association_path_evaluator import (
    FiniteAssociationPathEvaluation,
    FrozenAssociationPathReferenceSet,
    build_frozen_association_path_references,
    evaluate_finite_association_paths,
)
from heterodiff.evaluation.finite_association_residual_evaluator import (
    FiniteAssociationNonPathEvaluation,
    bind_test_only_finite_association_logit_evaluator,
    evaluate_finite_association_nonpath,
)
from heterodiff.evaluation.finite_association_residual_metrics import (
    paired_geometric_mean_ratio,
    paired_material_sign_test,
    ratio_equal_log_sample_aulc,
    shared_winning_seed_count,
)
from heterodiff.experiments.finite_association_guided_residual_pilot import (
    AssociationResidualPrerequisiteResult,
    FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS,
    FrozenAssociationResidualFixture,
    build_frozen_association_residual_fixture,
    frozen_association_fixture_content_digests,
    frozen_association_fixture_sha256,
    run_association_residual_prerequisite_gate,
)
from heterodiff.experiments.finite_association_residual_data import (
    PAIRED_SEEDS,
    SAMPLE_BUDGETS,
)


DIRECT_METHOD = "direct"
GUIDED_METHOD = "guided"
STRONG_DIRECT_METHOD = "strong_direct"
GUIDE_INPUT_METHOD = "guide_input"
MISMATCH_METHOD = "mismatch"
SAMPLED_METHODS = (
    DIRECT_METHOD,
    GUIDED_METHOD,
    STRONG_DIRECT_METHOD,
    GUIDE_INPUT_METHOD,
    MISMATCH_METHOD,
)
EXPECTED_SAMPLED_COORDINATES = tuple(
    (seed, budget, method)
    for seed in PAIRED_SEEDS
    for budget in SAMPLE_BUDGETS
    for method in SAMPLED_METHODS
)

_MAXIMUM_BUDGET = 32_768
_RATIO_FLOOR = 1.0e-12
_OVERFLOW_INDEX = 20
_AMBIGUOUS_INDICES = (8, 7, 5)
_SHA256_HEX = frozenset("0123456789abcdef")
_RUN_EVIDENCE_KEY = object()
_GUIDE_CONTROL_KEY = object()
_DECISION_STATUSES = ("NOT_RUN", "HOLD", "PASS", "STOP")


def _expected_decision_criterion_ids() -> Tuple[str, ...]:
    result = [
        "co_primary.bce.aulc.guided_vs_direct",
        "co_primary.path.aulc.guided_vs_direct",
        "co_primary.bce.sign_test",
        "co_primary.path.sign_test",
        "co_primary.shared_winning_seeds",
        "retained_path.guided_vs_direct.ratio",
        "retained_path.guided_vs_direct.absolute_reduction",
        "ood.balanced.guided_vs_direct",
    ]
    result.extend(
        "ood.%s.guided_vs_direct" % label
        for label in ("latent3", "anchor3", "both3", "overflow")
    )
    result.extend(
        "interpolation.%s.guided_vs_direct" % label
        for label in ("time", "pair")
    )
    result.extend(
        "edit_family.%s.guided_vs_direct" % label
        for label in ("birth", "death", "replacement")
    )
    result.append("edit_family.material_improvement_count")
    for label in ("bce", "path"):
        result.extend(
            (
                "strong_direct.%s.aulc" % label,
                "strong_direct.%s.maximum_budget" % label,
            )
        )
    result.append("guide_alone.retained_path")
    result.extend(
        "guide_alone.ambiguous_observation_%d" % index
        for index in _AMBIGUOUS_INDICES
    )
    result.append("guide_alone.ambiguous_strong_improvement_count")
    result.extend(
        "all_observations.path_%02d.guided_vs_direct" % index
        for index in range(21)
    )
    result.append("retained_observations.strict_improvement_count")
    for control in ("mismatch", "guide_input"):
        for label in ("bce", "path"):
            result.extend(
                (
                    "identification.%s.%s.aulc" % (control, label),
                    "identification.%s.%s.strict_seed_wins" % (control, label),
                )
            )
    result.extend(
        (
            "exact_residual.correction_scale",
            "rank_stress.operation_allocation",
        )
    )
    return tuple(result)


EXPECTED_DECISION_CRITERION_IDS = _expected_decision_criterion_ids()


def _sha256(value: object, *, name: str) -> str:
    if type(value) is not str or len(value) != 64 or any(
        character not in _SHA256_HEX for character in value
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _nonnegative(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError("%s must be finite and nonnegative" % name)
    return result


def _positive_integer(value: object, *, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result <= 0:
        raise ValueError("%s must be positive" % name)
    return result


def _immutable_float_array(value: object, *, shape: Tuple[int, ...]) -> np.ndarray:
    try:
        raw = np.asarray(value)
        objects = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("value must be a rectangular numeric array") from error
    if any(isinstance(item, (bool, np.bool_)) for item in objects.flat):
        raise TypeError("numeric arrays must not contain booleans")
    if raw.dtype.kind not in "iuf" or raw.shape != shape:
        raise ValueError("numeric array must have shape %r" % (shape,))
    result = np.asarray(raw, dtype=np.float64)
    if not np.all(np.isfinite(result)) or np.any(result < 0.0):
        raise ValueError("numeric array must be finite and nonnegative")
    contiguous = np.array(result, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=np.float64).reshape(
        contiguous.shape
    )


def _hash_array(digest: "hashlib._Hash", value: np.ndarray) -> None:
    array = np.ascontiguousarray(value)
    digest.update(array.dtype.str.encode("ascii"))
    digest.update(repr(tuple(array.shape)).encode("ascii"))
    payload = array.tobytes(order="C")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)


@dataclass(frozen=True)
class FrozenAssociationRunResources:
    """Resource values copied from one SUCCESS-ledger checkpoint/receipt."""

    preparation_cpu_seconds: float
    preparation_wall_seconds: float
    optimizer_wall_seconds: float
    total_cpu_seconds: float
    total_wall_seconds: float
    process_peak_rss_bytes: int

    def __post_init__(self) -> None:
        for name in (
            "preparation_cpu_seconds",
            "preparation_wall_seconds",
            "optimizer_wall_seconds",
            "total_cpu_seconds",
            "total_wall_seconds",
        ):
            object.__setattr__(self, name, _nonnegative(getattr(self, name), name=name))
        peak = _positive_integer(self.process_peak_rss_bytes, name="process_peak_rss_bytes")
        if self.preparation_cpu_seconds > self.total_cpu_seconds:
            raise ValueError("preparation CPU time exceeds total CPU time")
        if self.preparation_wall_seconds > self.total_wall_seconds:
            raise ValueError("preparation wall time exceeds total wall time")
        if self.optimizer_wall_seconds > self.total_wall_seconds:
            raise ValueError("optimizer wall time exceeds total wall time")
        object.__setattr__(self, "process_peak_rss_bytes", peak)


@dataclass(frozen=True, eq=False)
class FrozenAssociationSampledRunEvidence:
    """One coordinate bound to a canonical SUCCESS-ledger checkpoint.

    This is an internally derived metric DTO, not production admission input.
    The construction token is API hygiene only and is not provenance.  Future
    production use derives all instances from one complete aggregate load and
    matches every copied field to a second aggregate load after evaluation.
    """

    seed: int
    budget: int
    method: str
    run_key_sha256: str
    prepared_ledger_sha256: str
    running_ledger_sha256: str
    success_receipt_sha256: str
    campaign_sha256: str
    optimizer_completion_receipt_sha256: str
    worker_session_sha256: str
    launch_authorization_sha256: str
    launch_receipt_sha256: str
    worker_process_id: int
    worker_parent_process_id: int
    worker_process_identity_sha256: str
    preflight_sha256: str
    source_sha256: str
    configuration_sha256: str
    fixture_sha256: str
    execution_runtime_sha256: str
    custody_sha256: str
    all_dataset_sha256: Tuple[str, str, str]
    all_batch_schedule_sha256: Tuple[str, str, str, str, str, str]
    dataset_sha256: str
    batch_schedule_sha256: str
    initial_parameter_sha256: str
    parameter_count: int
    forward_multiply_add_count: int
    updates: int
    optimizer_steps_taken: int
    optimizer_transcript_sha256: str
    classifier_sha256: str
    parameter_sha256: str
    feature_sha256: str
    certificate_sha256: str
    certified_maximum_absolute_correction: float
    final_empirical_risk: float
    maximum_unclipped_gradient_norm: float
    nonpath: FiniteAssociationNonPathEvaluation
    path: FiniteAssociationPathEvaluation
    resources: FrozenAssociationRunResources
    _construction_key: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._construction_key is not _RUN_EVIDENCE_KEY:
            raise TypeError("use bind_frozen_association_sampled_run_evidence")
        if self.seed not in PAIRED_SEEDS or self.budget not in SAMPLE_BUDGETS:
            raise ValueError("run coordinate is not frozen")
        if self.method not in SAMPLED_METHODS:
            raise ValueError("sampled method is not frozen")
        for name in (
            "run_key_sha256",
            "prepared_ledger_sha256",
            "running_ledger_sha256",
            "success_receipt_sha256",
            "campaign_sha256",
            "optimizer_completion_receipt_sha256",
            "worker_session_sha256",
            "launch_authorization_sha256",
            "launch_receipt_sha256",
            "worker_process_identity_sha256",
            "preflight_sha256",
            "source_sha256",
            "configuration_sha256",
            "fixture_sha256",
            "execution_runtime_sha256",
            "custody_sha256",
            "dataset_sha256",
            "batch_schedule_sha256",
            "initial_parameter_sha256",
            "optimizer_transcript_sha256",
            "classifier_sha256",
            "parameter_sha256",
            "feature_sha256",
            "certificate_sha256",
        ):
            object.__setattr__(self, name, _sha256(getattr(self, name), name=name))
        for name in ("worker_process_id", "worker_parent_process_id"):
            object.__setattr__(
                self, name, _positive_integer(getattr(self, name), name=name)
            )
        if type(self.all_dataset_sha256) is not tuple or len(
            self.all_dataset_sha256
        ) != 3:
            raise TypeError("all_dataset_sha256 must contain three digests")
        if type(self.all_batch_schedule_sha256) is not tuple or len(
            self.all_batch_schedule_sha256
        ) != 6:
            raise TypeError("all_batch_schedule_sha256 must contain six digests")
        for value in self.all_dataset_sha256 + self.all_batch_schedule_sha256:
            _sha256(value, name="paired data/schedule digest")
        for name in (
            "parameter_count",
            "forward_multiply_add_count",
            "updates",
            "optimizer_steps_taken",
        ):
            object.__setattr__(self, name, _positive_integer(getattr(self, name), name=name))
        if self.optimizer_steps_taken != self.updates:
            raise ValueError("optimizer step count must equal the frozen update count")
        for name in (
            "certified_maximum_absolute_correction",
            "final_empirical_risk",
            "maximum_unclipped_gradient_norm",
        ):
            object.__setattr__(self, name, _nonnegative(getattr(self, name), name=name))
        if type(self.nonpath) is not FiniteAssociationNonPathEvaluation:
            raise TypeError("nonpath must be an exact non-path evaluation")
        if type(self.path) is not FiniteAssociationPathEvaluation:
            raise TypeError("path must be an exact all-21 path evaluation")
        if type(self.resources) is not FrozenAssociationRunResources:
            raise TypeError("resources must be a frozen resource record")

    @property
    def coordinate(self) -> Tuple[int, int, str]:
        return (self.seed, self.budget, self.method)


def bind_frozen_association_sampled_run_evidence(
    verified_checkpoint: object,
    nonpath: FiniteAssociationNonPathEvaluation,
    path: FiniteAssociationPathEvaluation,
) -> FrozenAssociationSampledRunEvidence:
    """Bind metrics for internal analysis/tests, never production admission.

    The checkpoint wrapper can only be produced by
    ``load_successful_frozen_association_checkpoint``.  Serialized evaluations
    alone are deliberately insufficient because they do not independently
    expose the seed/budget/method preimage of their SUCCESS receipt.  The
    returned record is not accepted by the production decision entry point.
    """

    from heterodiff.experiments.finite_association_residual_training_torch import (
        LedgerVerifiedFittedAssociationCheckpoint,
        _require_fitted_checkpoint_integrity,
    )
    from heterodiff.experiments.finite_association_isolated_runner import (
        revalidate_successful_frozen_association_checkpoint,
    )

    if type(verified_checkpoint) is not LedgerVerifiedFittedAssociationCheckpoint:
        raise TypeError("verified_checkpoint must come from the SUCCESS-ledger loader")
    if type(nonpath) is not FiniteAssociationNonPathEvaluation:
        raise TypeError("nonpath must be an exact non-path evaluation")
    if type(path) is not FiniteAssociationPathEvaluation:
        raise TypeError("path must be an exact all-21 path evaluation")
    revalidate_successful_frozen_association_checkpoint(verified_checkpoint)
    checkpoint = verified_checkpoint.checkpoint
    _require_fitted_checkpoint_integrity(checkpoint)
    preflight = checkpoint.preflight
    receipt = verified_checkpoint.success_receipt_sha256
    campaign = verified_checkpoint.campaign_sha256
    expected = (
        checkpoint.final_snapshot.parameter_sha256,
        checkpoint.classifier_sha256,
        receipt,
        campaign,
    )
    for name, evaluation in (("nonpath", nonpath), ("path", path)):
        observed = (
            evaluation.parameter_sha256,
            evaluation.classifier_sha256,
            evaluation.execution_receipt_sha256,
            evaluation.campaign_sha256,
        )
        if evaluation.production_bound is not True or observed != expected:
            raise ValueError(
                "%s evaluation is not bound to the supplied SUCCESS checkpoint" % name
            )
    if nonpath.feature_sha256 != checkpoint.certificate.feature_sha256:
        raise ValueError("non-path feature digest differs from the checkpoint")

    # Preparation times are read only from the immutable, validated SUCCESS
    # wrapper.  Older loaders that do not expose them cannot create evidence.
    try:
        preparation_cpu = verified_checkpoint.preparation_cpu_seconds
        preparation_wall = verified_checkpoint.preparation_wall_seconds
    except AttributeError as error:
        raise RuntimeError(
            "SUCCESS wrapper lacks ledger-bound preparation resource values"
        ) from error
    return FrozenAssociationSampledRunEvidence(
        seed=preflight.seed,
        budget=preflight.budget,
        method=preflight.method,
        run_key_sha256=checkpoint.run_key_sha256,
        prepared_ledger_sha256=checkpoint.prepared_ledger_sha256,
        running_ledger_sha256=verified_checkpoint.running_ledger_sha256,
        success_receipt_sha256=receipt,
        campaign_sha256=campaign,
        optimizer_completion_receipt_sha256=(
            verified_checkpoint.optimizer_completion_receipt_sha256
        ),
        worker_session_sha256=verified_checkpoint.worker_session_sha256,
        launch_authorization_sha256=(
            verified_checkpoint.launch_authorization_sha256
        ),
        launch_receipt_sha256=verified_checkpoint.launch_receipt_sha256,
        worker_process_id=verified_checkpoint.worker_process_id,
        worker_parent_process_id=verified_checkpoint.worker_parent_process_id,
        worker_process_identity_sha256=(
            verified_checkpoint.worker_process_identity_sha256
        ),
        preflight_sha256=preflight.preflight_sha256,
        source_sha256=preflight.source_sha256,
        configuration_sha256=preflight.configuration_sha256,
        fixture_sha256=preflight.fixture_sha256,
        execution_runtime_sha256=checkpoint.execution_runtime_sha256,
        custody_sha256=preflight.custody_sha256,
        all_dataset_sha256=preflight.all_dataset_sha256,
        all_batch_schedule_sha256=preflight.all_batch_schedule_sha256,
        dataset_sha256=preflight.dataset_sha256,
        batch_schedule_sha256=preflight.batch_schedule_sha256,
        initial_parameter_sha256=preflight.initial_parameter_sha256,
        parameter_count=preflight.parameter_count,
        forward_multiply_add_count=preflight.forward_multiply_add_count,
        updates=preflight.updates,
        optimizer_steps_taken=checkpoint.optimizer_steps_taken,
        optimizer_transcript_sha256=checkpoint.optimizer_transcript_sha256,
        classifier_sha256=checkpoint.classifier_sha256,
        parameter_sha256=checkpoint.final_snapshot.parameter_sha256,
        feature_sha256=checkpoint.certificate.feature_sha256,
        certificate_sha256=checkpoint.certificate.certificate_sha256,
        certified_maximum_absolute_correction=(
            checkpoint.certificate.certified_maximum_absolute_correction
        ),
        final_empirical_risk=checkpoint.final_empirical_risk,
        maximum_unclipped_gradient_norm=checkpoint.maximum_unclipped_gradient_norm,
        nonpath=nonpath,
        path=path,
        resources=FrozenAssociationRunResources(
            preparation_cpu_seconds=preparation_cpu,
            preparation_wall_seconds=preparation_wall,
            optimizer_wall_seconds=checkpoint.elapsed_training_seconds,
            total_cpu_seconds=checkpoint.total_cpu_seconds,
            total_wall_seconds=checkpoint.total_wall_seconds,
            process_peak_rss_bytes=checkpoint.process_peak_rss_bytes,
        ),
        _construction_key=_RUN_EVIDENCE_KEY,
    )


def _load_canonical_sampled_checkpoint(run_key_sha256: str) -> object:
    """Reload one canonical SUCCESS payload; factored for no-training tests."""

    from heterodiff.experiments.finite_association_isolated_runner import (
        load_successful_frozen_association_checkpoint,
    )

    return load_successful_frozen_association_checkpoint(run_key_sha256)


def _canonical_checkpoint_for_supplied_run(
    run: FrozenAssociationSampledRunEvidence,
) -> object:
    """Reopen a run and exhaustively match all copied custody metadata."""

    return _match_supplied_run_to_verified_checkpoint(
        run, _load_canonical_sampled_checkpoint(run.run_key_sha256)
    )


def _match_supplied_run_to_verified_checkpoint(
    run: FrozenAssociationSampledRunEvidence,
    verified: object,
) -> object:
    """Match one metric DTO to a wrapper from a canonical aggregate load."""

    from heterodiff.experiments.finite_association_residual_training_torch import (
        LedgerVerifiedFittedAssociationCheckpoint,
        _require_fitted_checkpoint_integrity,
    )

    if type(verified) is not LedgerVerifiedFittedAssociationCheckpoint:
        raise TypeError("canonical sampled loader returned the wrong wrapper type")
    checkpoint = verified.checkpoint
    _require_fitted_checkpoint_integrity(checkpoint)
    preflight = checkpoint.preflight
    observed = {
        "seed": run.seed,
        "budget": run.budget,
        "method": run.method,
        "run_key_sha256": run.run_key_sha256,
        "prepared_ledger_sha256": run.prepared_ledger_sha256,
        "running_ledger_sha256": run.running_ledger_sha256,
        "success_receipt_sha256": run.success_receipt_sha256,
        "campaign_sha256": run.campaign_sha256,
        "optimizer_completion_receipt_sha256": (
            run.optimizer_completion_receipt_sha256
        ),
        "worker_session_sha256": run.worker_session_sha256,
        "launch_authorization_sha256": run.launch_authorization_sha256,
        "launch_receipt_sha256": run.launch_receipt_sha256,
        "worker_process_id": run.worker_process_id,
        "worker_parent_process_id": run.worker_parent_process_id,
        "worker_process_identity_sha256": run.worker_process_identity_sha256,
        "preflight_sha256": run.preflight_sha256,
        "source_sha256": run.source_sha256,
        "configuration_sha256": run.configuration_sha256,
        "fixture_sha256": run.fixture_sha256,
        "execution_runtime_sha256": run.execution_runtime_sha256,
        "custody_sha256": run.custody_sha256,
        "all_dataset_sha256": run.all_dataset_sha256,
        "all_batch_schedule_sha256": run.all_batch_schedule_sha256,
        "dataset_sha256": run.dataset_sha256,
        "batch_schedule_sha256": run.batch_schedule_sha256,
        "initial_parameter_sha256": run.initial_parameter_sha256,
        "parameter_count": run.parameter_count,
        "forward_multiply_add_count": run.forward_multiply_add_count,
        "updates": run.updates,
        "optimizer_steps_taken": run.optimizer_steps_taken,
        "optimizer_transcript_sha256": run.optimizer_transcript_sha256,
        "classifier_sha256": run.classifier_sha256,
        "parameter_sha256": run.parameter_sha256,
        "feature_sha256": run.feature_sha256,
        "certificate_sha256": run.certificate_sha256,
        "certified_maximum_absolute_correction": (
            run.certified_maximum_absolute_correction
        ),
        "final_empirical_risk": run.final_empirical_risk,
        "maximum_unclipped_gradient_norm": run.maximum_unclipped_gradient_norm,
        "preparation_cpu_seconds": run.resources.preparation_cpu_seconds,
        "preparation_wall_seconds": run.resources.preparation_wall_seconds,
        "optimizer_wall_seconds": run.resources.optimizer_wall_seconds,
        "total_cpu_seconds": run.resources.total_cpu_seconds,
        "total_wall_seconds": run.resources.total_wall_seconds,
        "process_peak_rss_bytes": run.resources.process_peak_rss_bytes,
    }
    expected = {
        "seed": preflight.seed,
        "budget": preflight.budget,
        "method": preflight.method,
        "run_key_sha256": checkpoint.run_key_sha256,
        "prepared_ledger_sha256": checkpoint.prepared_ledger_sha256,
        "running_ledger_sha256": verified.running_ledger_sha256,
        "success_receipt_sha256": verified.success_receipt_sha256,
        "campaign_sha256": verified.campaign_sha256,
        "optimizer_completion_receipt_sha256": (
            verified.optimizer_completion_receipt_sha256
        ),
        "worker_session_sha256": verified.worker_session_sha256,
        "launch_authorization_sha256": verified.launch_authorization_sha256,
        "launch_receipt_sha256": verified.launch_receipt_sha256,
        "worker_process_id": verified.worker_process_id,
        "worker_parent_process_id": verified.worker_parent_process_id,
        "worker_process_identity_sha256": (
            verified.worker_process_identity_sha256
        ),
        "preflight_sha256": preflight.preflight_sha256,
        "source_sha256": preflight.source_sha256,
        "configuration_sha256": preflight.configuration_sha256,
        "fixture_sha256": preflight.fixture_sha256,
        "execution_runtime_sha256": checkpoint.execution_runtime_sha256,
        "custody_sha256": preflight.custody_sha256,
        "all_dataset_sha256": preflight.all_dataset_sha256,
        "all_batch_schedule_sha256": preflight.all_batch_schedule_sha256,
        "dataset_sha256": preflight.dataset_sha256,
        "batch_schedule_sha256": preflight.batch_schedule_sha256,
        "initial_parameter_sha256": preflight.initial_parameter_sha256,
        "parameter_count": preflight.parameter_count,
        "forward_multiply_add_count": preflight.forward_multiply_add_count,
        "updates": preflight.updates,
        "optimizer_steps_taken": checkpoint.optimizer_steps_taken,
        "optimizer_transcript_sha256": checkpoint.optimizer_transcript_sha256,
        "classifier_sha256": checkpoint.classifier_sha256,
        "parameter_sha256": checkpoint.final_snapshot.parameter_sha256,
        "feature_sha256": checkpoint.certificate.feature_sha256,
        "certificate_sha256": checkpoint.certificate.certificate_sha256,
        "certified_maximum_absolute_correction": (
            checkpoint.certificate.certified_maximum_absolute_correction
        ),
        "final_empirical_risk": checkpoint.final_empirical_risk,
        "maximum_unclipped_gradient_norm": checkpoint.maximum_unclipped_gradient_norm,
        "preparation_cpu_seconds": verified.preparation_cpu_seconds,
        "preparation_wall_seconds": verified.preparation_wall_seconds,
        "optimizer_wall_seconds": checkpoint.elapsed_training_seconds,
        "total_cpu_seconds": checkpoint.total_cpu_seconds,
        "total_wall_seconds": checkpoint.total_wall_seconds,
        "process_peak_rss_bytes": checkpoint.process_peak_rss_bytes,
    }
    mismatches = tuple(name for name in expected if observed[name] != expected[name])
    if mismatches:
        raise RuntimeError(
            "supplied run differs from canonical SUCCESS custody: %s"
            % ", ".join(mismatches)
        )
    result_identity = (
        checkpoint.final_snapshot.parameter_sha256,
        checkpoint.classifier_sha256,
        verified.success_receipt_sha256,
        verified.campaign_sha256,
    )
    for label, result in (("nonpath", run.nonpath), ("path", run.path)):
        supplied_identity = (
            result.parameter_sha256,
            result.classifier_sha256,
            result.execution_receipt_sha256,
            result.campaign_sha256,
        )
        if result.production_bound is not True or supplied_identity != result_identity:
            raise RuntimeError(
                "supplied %s metadata is not bound to canonical SUCCESS custody"
                % label
            )
    if run.nonpath.feature_sha256 != checkpoint.certificate.feature_sha256:
        raise RuntimeError("supplied non-path feature identity is not canonical")
    return verified


def _fresh_frozen_decision_context(
) -> Tuple[FrozenAssociationResidualFixture, FrozenAssociationPathReferenceSet]:
    """Build one fixture and one all-21 reference set for a decision call."""

    fixture = build_frozen_association_residual_fixture()
    references = build_frozen_association_path_references(fixture)
    references.require_preflight_pass()
    return fixture, references


def _evaluate_canonical_sampled_run_for_decision(
    verified_checkpoint: object,
    fixture: FrozenAssociationResidualFixture,
    reference_set: FrozenAssociationPathReferenceSet,
) -> FrozenAssociationSampledRunEvidence:
    """Regenerate all decision metrics from one canonical checkpoint."""

    from heterodiff.experiments.finite_association_residual_training_torch import (
        bind_fitted_association_checkpoint_evaluator,
    )

    evaluator = bind_fitted_association_checkpoint_evaluator(verified_checkpoint)
    nonpath = evaluate_finite_association_nonpath(evaluator, fixture)
    path = evaluate_finite_association_paths(
        evaluator,
        fixture,
        reference_set=reference_set,
    )
    return bind_frozen_association_sampled_run_evidence(
        verified_checkpoint,
        nonpath,
        path,
    )


def _guide_control_sha256(
    fixture_sha256: str,
    guide_sha256: str,
    reference_set_sha256: str,
    path: FiniteAssociationPathEvaluation,
) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-a1-guide-alone-path-control-v1\0")
    for value in (fixture_sha256, guide_sha256, reference_set_sha256):
        digest.update(value.encode("ascii"))
        digest.update(b"\0")
    for value in (
        path.path_kl_per_observation,
        path.unconditional_path_kl_per_observation,
        path.normalized_path_kl_per_observation,
        path.observation_mass,
    ):
        _hash_array(digest, value)
    digest.update(float(path.retained_normalized_path_score).hex().encode("ascii"))
    digest.update(float(path.ambiguous_normalized_path_score).hex().encode("ascii"))
    for failure in path.numerical_gate_failures:
        digest.update(failure.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


@dataclass(frozen=True, eq=False)
class FrozenAssociationGuideAlonePathControl:
    """Deterministically constructed ``r=0`` all-21 path control.

    Its construction token is API hygiene only.  A production decision
    rebuilds this control and compares its decision-bearing content digest.
    """

    fixture_sha256: str
    guide_sha256: str
    reference_set_sha256: str
    path: FiniteAssociationPathEvaluation
    control_sha256: str
    _construction_key: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._construction_key is not _GUIDE_CONTROL_KEY:
            raise TypeError("use build_frozen_association_guide_alone_path_control")
        fixture = _sha256(self.fixture_sha256, name="fixture_sha256")
        guide = _sha256(self.guide_sha256, name="guide_sha256")
        reference = _sha256(self.reference_set_sha256, name="reference_set_sha256")
        control = _sha256(self.control_sha256, name="control_sha256")
        if type(self.path) is not FiniteAssociationPathEvaluation:
            raise TypeError("guide-alone path must be an exact path evaluation")
        if self.path.production_bound is not False or any(
            value is not None
            for value in (
                self.path.classifier_sha256,
                self.path.execution_receipt_sha256,
                self.path.campaign_sha256,
            )
        ):
            raise ValueError("guide-alone control must remain deterministic/test-only")
        if self.path.reference_set_sha256 != reference:
            raise ValueError("guide-alone control uses a different path reference set")
        expected = _guide_control_sha256(fixture, guide, reference, self.path)
        if control != expected:
            raise ValueError("guide-alone control digest is inconsistent")
        object.__setattr__(self, "fixture_sha256", fixture)
        object.__setattr__(self, "guide_sha256", guide)
        object.__setattr__(self, "reference_set_sha256", reference)
        object.__setattr__(self, "control_sha256", control)


def build_frozen_association_guide_alone_path_control(
    fixture: FrozenAssociationResidualFixture,
    reference_set: FrozenAssociationPathReferenceSet,
) -> FrozenAssociationGuideAlonePathControl:
    """Evaluate the exact analytic guide with zero learned correction.

    This may perform path integration, but it never constructs an optimizer or
    takes a learner update.  The evaluator callback is created inside this
    function so an arbitrary test-only callback cannot be relabelled as the
    guide-alone control.
    """

    if type(fixture) is not FrozenAssociationResidualFixture:
        raise TypeError("fixture must be the exact frozen A1 fixture type")
    if type(reference_set) is not FrozenAssociationPathReferenceSet:
        raise TypeError("reference_set must be the exact all-21 reference set")
    content = frozen_association_fixture_content_digests(fixture)
    fixture_digest = frozen_association_fixture_sha256(content)
    if fixture_digest != frozen_association_fixture_sha256():
        raise ValueError("guide-alone fixture content is not frozen A1")
    guide_digest = content[3]
    if guide_digest != FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS[3]:
        raise ValueError("guide-alone control is not the frozen analytic guide")
    if (
        reference_set.frozen_fixture_sha256 != fixture_digest
        or not reference_set.preflight_passed
    ):
        raise ValueError("guide-alone control requires the passing all-21 preflight")

    parameter_digest = hashlib.sha256(
        b"heterodiff-a1-guide-alone-zero-correction"
    ).hexdigest()
    feature_digest = hashlib.sha256(
        b"heterodiff-a1-guide-alone-no-learned-features"
    ).hexdigest()
    certificate_digest = hashlib.sha256(
        (parameter_digest + fixture_digest + feature_digest).encode("ascii")
    ).hexdigest()
    outward_zero = math.nextafter(0.0, math.inf)
    certificate = SimpleNamespace(
        passed=True,
        parameter_sha256=parameter_digest,
        frozen_fixture_sha256=fixture_digest,
        feature_sha256=feature_digest,
        input_features=21,
        hidden_width=32,
        grid_intervals=4096,
        grid_points=4097,
        time_chunk_size=128,
        pair_count=20 * 21,
        evaluated_output_count=4097 * 20 * 21,
        layer_outward_row_sums=(0.0, 0.0, 0.0),
        input_time_lipschitz=0.0,
        network_time_lipschitz=0.0,
        maximum_grid_absolute_correction=0.0,
        outward_grid_maximum=outward_zero,
        half_cell_allowance=0.0,
        certified_maximum_absolute_correction=outward_zero,
        correction_limit=20.0,
        certificate_sha256=certificate_digest,
    )
    observation_density = np.asarray(
        fixture.population.observation_marginal_density, dtype=np.float64
    )

    def evaluate_guide_logits(direct_times: np.ndarray) -> np.ndarray:
        guide_density = np.stack(
            [fixture.guide.density_grid(float(value)) for value in direct_times],
            axis=0,
        )
        if np.any(guide_density <= 0.0) or not np.all(np.isfinite(guide_density)):
            raise ArithmeticError("analytic guide produced an invalid density")
        return np.log(guide_density) - np.log(observation_density)[None, None, :]

    evaluator = bind_test_only_finite_association_logit_evaluator(
        evaluate_guide_logits, certificate
    )
    path = evaluate_finite_association_paths(
        evaluator,
        fixture,
        reference_set=reference_set,
        test_only=True,
    )
    control_digest = _guide_control_sha256(
        fixture_digest, guide_digest, reference_set.reference_set_sha256, path
    )
    return FrozenAssociationGuideAlonePathControl(
        fixture_sha256=fixture_digest,
        guide_sha256=guide_digest,
        reference_set_sha256=reference_set.reference_set_sha256,
        path=path,
        control_sha256=control_digest,
        _construction_key=_GUIDE_CONTROL_KEY,
    )


def _fresh_and_compare_guide_control(
    supplied: FrozenAssociationGuideAlonePathControl,
    fixture: FrozenAssociationResidualFixture,
    reference_set: FrozenAssociationPathReferenceSet,
) -> FrozenAssociationGuideAlonePathControl:
    """Recompute the deterministic guide and reject a different supplied DTO."""

    if type(supplied) is not FrozenAssociationGuideAlonePathControl:
        raise TypeError("supplied guide-alone control has the wrong exact type")
    # Re-run all internal consistency checks in case a frozen dataclass was
    # altered through low-level Python mechanisms after construction.
    supplied.__post_init__()
    fresh = build_frozen_association_guide_alone_path_control(fixture, reference_set)
    observed = (
        supplied.fixture_sha256,
        supplied.guide_sha256,
        supplied.reference_set_sha256,
        supplied.control_sha256,
    )
    expected = (
        fresh.fixture_sha256,
        fresh.guide_sha256,
        fresh.reference_set_sha256,
        fresh.control_sha256,
    )
    if observed != expected:
        raise RuntimeError(
            "supplied guide-alone control differs from fresh deterministic recomputation"
        )
    return fresh


@dataclass(frozen=True)
class FrozenAssociationCampaignEvidence:
    """Internal/test-only reducer input; never production sampled admission."""

    campaign_sha256: Optional[str] = None
    sampled_runs: Tuple[FrozenAssociationSampledRunEvidence, ...] = ()
    guide_alone: Optional[FrozenAssociationGuideAlonePathControl] = None
    prerequisite: Optional[AssociationResidualPrerequisiteResult] = None
    exact_population_control: Optional[object] = None
    rank_stress_control: Optional[object] = None

    def __post_init__(self) -> None:
        if self.campaign_sha256 is not None:
            object.__setattr__(
                self,
                "campaign_sha256",
                _sha256(self.campaign_sha256, name="campaign_sha256"),
            )
        if type(self.sampled_runs) is not tuple or any(
            type(value) is not FrozenAssociationSampledRunEvidence
            for value in self.sampled_runs
        ):
            raise TypeError("sampled_runs must be an exact tuple of bound run evidence")
        if self.guide_alone is not None and type(
            self.guide_alone
        ) is not FrozenAssociationGuideAlonePathControl:
            raise TypeError("guide_alone has the wrong exact type")
        if self.prerequisite is not None and type(
            self.prerequisite
        ) is not AssociationResidualPrerequisiteResult:
            raise TypeError("prerequisite has the wrong exact type")


@dataclass(frozen=True)
class FrozenAssociationDecisionCriterion:
    criterion_id: str
    observed: Tuple[float, ...]
    requirement: str
    passed: bool

    def __post_init__(self) -> None:
        if type(self.criterion_id) is not str or not self.criterion_id:
            raise TypeError("criterion_id must be a nonempty string")
        if type(self.requirement) is not str or not self.requirement:
            raise TypeError("requirement must be a nonempty string")
        if type(self.observed) is not tuple or not self.observed or any(
            isinstance(value, (bool, np.bool_))
            or not isinstance(value, Real)
            or not math.isfinite(float(value))
            for value in self.observed
        ):
            raise ValueError("observed must be a nonempty finite numeric tuple")
        object.__setattr__(self, "observed", tuple(float(value) for value in self.observed))
        if type(self.passed) is not bool:
            raise TypeError("passed must be boolean")


@dataclass(frozen=True)
class FrozenAssociationCampaignDecision:
    """Non-authoritative decision DTO returned by the deterministic reducer.

    Even a ``PASS`` value is only a candidate decision until a later durable
    publication/audit receipt binds this DTO and its canonical evidence.  The
    Python constructor and private module symbols are not authentication.
    """

    status: str
    campaign_sha256: Optional[str]
    observed_sampled_coordinates: int
    expected_sampled_coordinates: int
    criteria: Tuple[FrozenAssociationDecisionCriterion, ...]
    reasons: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in _DECISION_STATUSES:
            raise ValueError("status must be NOT_RUN, HOLD, PASS, or STOP")
        if self.campaign_sha256 is not None:
            _sha256(self.campaign_sha256, name="campaign_sha256")
        for name in ("observed_sampled_coordinates", "expected_sampled_coordinates"):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
                raise TypeError("coordinate counts must be integers")
            if int(value) < 0:
                raise ValueError("coordinate counts must be nonnegative")
        if type(self.criteria) is not tuple or any(
            type(value) is not FrozenAssociationDecisionCriterion
            for value in self.criteria
        ):
            raise TypeError("criteria must be an exact criterion tuple")
        if type(self.reasons) is not tuple or any(
            type(value) is not str or not value for value in self.reasons
        ):
            raise TypeError("reasons must be a tuple of nonempty strings")
        if self.status == "PASS" and (
            self.reasons or not self.criteria or not all(value.passed for value in self.criteria)
        ):
            raise ValueError("PASS requires complete passing criteria and no reasons")
        if self.status != "PASS" and not self.reasons:
            raise ValueError("non-PASS decisions require at least one reason")
        criterion_ids = tuple(value.criterion_id for value in self.criteria)
        if self.status in ("PASS", "STOP"):
            if (
                self.campaign_sha256 is None
                or int(self.expected_sampled_coordinates)
                != len(EXPECTED_SAMPLED_COORDINATES)
                or int(self.observed_sampled_coordinates)
                != len(EXPECTED_SAMPLED_COORDINATES)
            ):
                raise ValueError(
                    "material decisions require one complete canonical campaign"
                )
            if criterion_ids != EXPECTED_DECISION_CRITERION_IDS:
                raise ValueError(
                    "material decisions require the exact frozen criterion set"
                )
        elif self.criteria:
            raise ValueError("NOT_RUN and HOLD decisions cannot carry criteria")

    @property
    def authoritative(self) -> bool:
        """Raw in-memory decision records never constitute publication proof."""

        return False


def _decision(
    status: str,
    evidence: Optional[FrozenAssociationCampaignEvidence],
    reasons: Tuple[str, ...],
    criteria: Tuple[FrozenAssociationDecisionCriterion, ...] = (),
) -> FrozenAssociationCampaignDecision:
    return FrozenAssociationCampaignDecision(
        status=status,
        campaign_sha256=None if evidence is None else evidence.campaign_sha256,
        observed_sampled_coordinates=(
            0 if evidence is None else len(evidence.sampled_runs)
        ),
        expected_sampled_coordinates=len(EXPECTED_SAMPLED_COORDINATES),
        criteria=criteria,
        reasons=reasons,
    )


def _run_metric_is_finite(run: FrozenAssociationSampledRunEvidence) -> bool:
    nonpath = run.nonpath
    masked = nonpath.masked_excess_bce
    nonnegative_values = (
        masked.train,
        masked.validation,
        masked.joint_interpolation,
        masked.time_interpolation,
        masked.pair_interpolation,
        masked.latent_three,
        masked.anchor_three,
        masked.both_three,
        masked.overflow,
        masked.balanced_ood,
        nonpath.centered_log_information.physical_weighted_rmse,
        nonpath.centered_log_information.maximum_absolute_error,
        nonpath.residual.physical_weighted_rmse,
        nonpath.residual.maximum_absolute_error,
        nonpath.residual.candidate_range,
        nonpath.residual.oracle_range,
        nonpath.conditional_initial_tv.observation_weighted_mean,
        nonpath.conditional_initial_tv.retained_observation_weighted_mean,
        nonpath.conditional_initial_tv.maximum,
        nonpath.conditional_initial_tv.overflow,
        nonpath.calibration.brier,
        nonpath.calibration.optimal_brier,
        nonpath.calibration.excess_brier,
        nonpath.calibration.reliability_ece,
        nonpath.calibration.maximum_reliability_gap,
        nonpath.coherence.terminal_maximum_absolute_log_information_error,
        nonpath.coherence.terminal_maximum_absolute_residual,
        nonpath.coherence.generator_row_sum_maximum_absolute_residual,
        nonpath.coherence.normalization_physical_weighted_rmse,
        nonpath.coherence.normalization_maximum_absolute_residual,
        nonpath.coherence.semigroup_physical_weighted_rmse,
        nonpath.coherence.semigroup_maximum_absolute_residual,
        nonpath.coherence.edit_cycle_maximum_absolute_residual,
    )
    signed_values = (
        nonpath.residual.candidate_minimum,
        nonpath.residual.candidate_maximum,
        nonpath.residual.oracle_minimum,
        nonpath.residual.oracle_maximum,
    )
    families = (
        nonpath.edge_log_rates.birth,
        nonpath.edge_log_rates.death,
        nonpath.edge_log_rates.replacement,
    )
    family_values = tuple(
        value
        for family in families
        for value in (
            family.physical_weight,
            family.physical_weighted_rmse,
            family.maximum_absolute_error,
            family.weighted_median_absolute_error,
        )
    )
    return (
        all(math.isfinite(float(value)) and float(value) >= 0.0 for value in nonnegative_values)
        and all(math.isfinite(float(value)) for value in signed_values)
        and all(math.isfinite(float(value)) and float(value) >= 0.0 for value in family_values)
        and all(family.active_edge_count > 0 for family in families)
        and nonpath.coherence.edit_cycle_count > 0
    )


def _custody_failures(
    evidence: FrozenAssociationCampaignEvidence,
    *,
    validate_metric_contents: bool,
) -> Tuple[str, ...]:
    failures = []
    runs = evidence.sampled_runs
    coordinates = tuple(value.coordinate for value in runs)
    if len(set(coordinates)) != len(coordinates):
        failures.append("a sampled seed/budget/method coordinate occurs more than once")
    if len(runs) == len(EXPECTED_SAMPLED_COORDINATES) and coordinates != (
        EXPECTED_SAMPLED_COORDINATES
    ):
        failures.append("complete sampled evidence is not in canonical campaign order")
    if runs and evidence.campaign_sha256 is None:
        failures.append("sampled evidence has no declared campaign SHA-256")
    receipts = []
    run_keys = []
    completion_receipts = []
    worker_sessions = []
    launch_authorizations = []
    launch_receipts = []
    worker_process_identities = []
    reference_sets = set()
    for run in runs:
        receipts.append(run.success_receipt_sha256)
        run_keys.append(run.run_key_sha256)
        completion_receipts.append(run.optimizer_completion_receipt_sha256)
        worker_sessions.append(run.worker_session_sha256)
        launch_authorizations.append(run.launch_authorization_sha256)
        launch_receipts.append(run.launch_receipt_sha256)
        worker_process_identities.append(run.worker_process_identity_sha256)
        reference_sets.add(run.path.reference_set_sha256)
        from heterodiff.experiments.finite_association_isolated_runner import (
            _worker_process_identity_sha256,
        )

        expected_process_identity = _worker_process_identity_sha256(
            {
                "worker_pid": run.worker_process_id,
                "worker_parent_pid": run.worker_parent_process_id,
                "session_sha256": run.worker_session_sha256,
                "launch_authorization_sha256": run.launch_authorization_sha256,
                "launch_receipt_sha256": run.launch_receipt_sha256,
            }
        )
        if expected_process_identity != run.worker_process_identity_sha256:
            failures.append(
                "%r worker process identity is inconsistent" % (run.coordinate,)
            )
        if run.campaign_sha256 != evidence.campaign_sha256:
            failures.append("%r carries a different campaign SHA-256" % (run.coordinate,))
        expected = (
            run.parameter_sha256,
            run.classifier_sha256,
            run.success_receipt_sha256,
            run.campaign_sha256,
        )
        for label, result in (("nonpath", run.nonpath), ("path", run.path)):
            observed = (
                result.parameter_sha256,
                result.classifier_sha256,
                result.execution_receipt_sha256,
                result.campaign_sha256,
            )
            if result.production_bound is not True or observed != expected:
                failures.append(
                    "%r %s result lost SUCCESS/classifier custody"
                    % (run.coordinate, label)
                )
        if run.nonpath.feature_sha256 != run.feature_sha256:
            failures.append("%r feature digest is inconsistent" % (run.coordinate,))
        if validate_metric_contents and not _run_metric_is_finite(run):
            failures.append("%r contains an invalid mandatory metric" % (run.coordinate,))
    if len(set(receipts)) != len(receipts):
        failures.append("SUCCESS receipts are not unique across sampled coordinates")
    if len(set(run_keys)) != len(run_keys):
        failures.append("run keys are not unique across sampled coordinates")
    for values, label in (
        (completion_receipts, "optimizer completion receipts"),
        (worker_sessions, "worker sessions"),
        (launch_authorizations, "launch authorizations"),
        (launch_receipts, "launch receipts"),
        (worker_process_identities, "worker process identities"),
    ):
        if len(set(values)) != len(values):
            failures.append("%s are not unique across sampled coordinates" % label)
    if len(reference_sets) > 1:
        failures.append("sampled paths do not share one all-21 reference set")

    for name in (
        "source_sha256",
        "configuration_sha256",
        "fixture_sha256",
        "execution_runtime_sha256",
    ):
        if len({getattr(value, name) for value in runs}) > 1:
            failures.append("sampled runs do not share one %s" % name)
    if runs:
        from heterodiff.experiments.finite_association_isolated_runner import (
            _campaign_record,
        )
        from heterodiff.experiments.finite_association_residual_training_torch import (
            frozen_association_training_configuration_sha256,
            frozen_association_training_source_sha256,
        )

        current_source = frozen_association_training_source_sha256()
        current_configuration = frozen_association_training_configuration_sha256(
            source_sha256=current_source
        )
        first = runs[0]
        if first.source_sha256 != current_source:
            failures.append("sampled campaign source custody is stale")
        if first.configuration_sha256 != current_configuration:
            failures.append("sampled campaign configuration custody is stale")
        if first.fixture_sha256 != frozen_association_fixture_sha256():
            failures.append("sampled campaign fixture custody is stale")
        expected_campaign = _campaign_record(
            fixture_sha256=first.fixture_sha256,
            source_sha256=first.source_sha256,
            configuration_sha256=first.configuration_sha256,
            execution_runtime_sha256=first.execution_runtime_sha256,
        )
        if expected_campaign["campaign_sha256"] != evidence.campaign_sha256:
            failures.append("declared campaign SHA-256 has the wrong canonical preimage")
    by_coordinate = {value.coordinate: value for value in runs}
    for seed in PAIRED_SEEDS:
        seed_runs = [value for value in runs if value.seed == seed]
        for name in (
            "custody_sha256",
            "all_dataset_sha256",
            "all_batch_schedule_sha256",
        ):
            if seed_runs and len({getattr(value, name) for value in seed_runs}) != 1:
                failures.append("seed %d does not share one %s" % (seed, name))
        for method in SAMPLED_METHODS:
            method_initials = {
                value.initial_parameter_sha256
                for value in seed_runs
                if value.method == method
            }
            if len(method_initials) > 1:
                failures.append(
                    "seed %d method %s changes initialization across budgets"
                    % (seed, method)
                )
        for budget in SAMPLE_BUDGETS:
            group = [
                by_coordinate.get((seed, budget, method))
                for method in SAMPLED_METHODS
            ]
            present = [value for value in group if value is not None]
            if len(present) < 2:
                continue
            for name in (
                "custody_sha256",
                "all_dataset_sha256",
                "all_batch_schedule_sha256",
                "dataset_sha256",
            ):
                if len({getattr(value, name) for value in present}) != 1:
                    failures.append(
                        "seed %d budget %d methods do not share %s"
                        % (seed, budget, name)
                    )
            primary = [
                by_coordinate.get((seed, budget, method))
                for method in (DIRECT_METHOD, GUIDED_METHOD, MISMATCH_METHOD)
            ]
            if all(value is not None for value in primary) and len(
                {value.initial_parameter_sha256 for value in primary}
            ) != 1:
                failures.append(
                    "seed %d budget %d matched 21-input initial tensors differ"
                    % (seed, budget)
                )
            primary_schedule = [
                by_coordinate.get((seed, budget, method))
                for method in (
                    DIRECT_METHOD,
                    GUIDED_METHOD,
                    GUIDE_INPUT_METHOD,
                    MISMATCH_METHOD,
                )
            ]
            if all(value is not None for value in primary_schedule) and len(
                {value.batch_schedule_sha256 for value in primary_schedule}
            ) != 1:
                failures.append(
                    "seed %d budget %d primary-update schedules differ"
                    % (seed, budget)
                )
    return tuple(dict.fromkeys(failures))


def _missing_reasons(evidence: FrozenAssociationCampaignEvidence) -> Tuple[str, ...]:
    reasons = []
    observed = {value.coordinate for value in evidence.sampled_runs}
    missing = [value for value in EXPECTED_SAMPLED_COORDINATES if value not in observed]
    if missing:
        reasons.append(
            "%d of 120 canonical sampled coordinates are absent" % len(missing)
        )
    if evidence.campaign_sha256 is None:
        reasons.append("canonical sampled campaign SHA-256 is absent")
    if evidence.guide_alone is None:
        reasons.append("deterministic guide-alone all-21 path control is absent")
    if evidence.prerequisite is None:
        reasons.append("frozen exact prerequisite control is absent")
    if evidence.exact_population_control is None:
        reasons.append(
            "executed all-seed exact-population diagnostic and its oracle-only "
            "product-positive control are absent"
        )
    else:
        # An explicitly unexecuted zero-step diagnostic is still NOT_RUN, but
        # it is never admitted as evidence.  Executed raw results fall through
        # to the custody check and are placed on HOLD without a ledger wrapper.
        from heterodiff.experiments.finite_association_exact_population_torch import (
            AssociationExactPopulationDiagnosticResult,
        )

        if (
            type(evidence.exact_population_control)
            is AssociationExactPopulationDiagnosticResult
            and evidence.exact_population_control.executed is False
        ):
            reasons.append("the all-seed exact-population diagnostic is unexecuted")
    if evidence.rank_stress_control is None:
        reasons.append("complete Section-9 rank-stress control is absent")
    return tuple(reasons)


def _control_hold_failures(
    evidence: FrozenAssociationCampaignEvidence,
) -> Tuple[Tuple[str, ...], bool]:
    """Validate every *supplied* control and return the rank hard-gate flag.

    Missing controls are handled later as ``NOT_RUN``.  A supplied malformed,
    stale, or numerically invalid control is a ``HOLD`` even when some other
    evidence remains absent.
    """

    from heterodiff.experiments.finite_association_exact_population_torch import (
        AssociationExactPopulationDiagnosticResult,
        EXACT_EXPECTED_TOTAL_OPTIMIZER_STEPS,
        EXACT_POPULATION_METHODS,
        ORACLE_PRODUCT_POSITIVE_LOGIT_TOLERANCE,
        frozen_exact_population_configuration_sha256,
    )
    from heterodiff.experiments.finite_association_exact_population_isolated_runner import (
        LedgerVerifiedExactPopulationDiagnostic,
        revalidate_completed_frozen_exact_population_diagnostic,
    )
    from heterodiff.experiments.finite_association_rank_stress import (
        LoaderVerifiedAssociationRankStressGateResult,
        RANK_STRESS_RANKS,
        _rank_stress_source_bundle_sha256,
        _rank_stress_specification_sha256,
    )
    from heterodiff.experiments.finite_association_residual_training_torch import (
        frozen_association_training_source_sha256,
    )

    failures = []
    prerequisite = evidence.prerequisite
    if prerequisite is not None:
        if type(prerequisite) is not AssociationResidualPrerequisiteResult:
            failures.append("prerequisite control has the wrong exact type")
        else:
            recomputed_prerequisite = run_association_residual_prerequisite_gate()
            prerequisite_matches = True
            for descriptor in fields(AssociationResidualPrerequisiteResult):
                observed_value = getattr(prerequisite, descriptor.name)
                expected_value = getattr(recomputed_prerequisite, descriptor.name)
                if isinstance(expected_value, np.ndarray):
                    matches = np.array_equal(observed_value, expected_value)
                else:
                    matches = observed_value == expected_value
                prerequisite_matches = prerequisite_matches and bool(matches)
            if not prerequisite_matches:
                failures.append(
                    "prerequisite control differs from fresh exact recomputation"
                )
            observed_prerequisite_digests = (
                prerequisite.generator_digest,
                prerequisite.observation_digest,
                prerequisite.population_digest,
                prerequisite.guide_digest,
                prerequisite.split_digest,
            )
            if observed_prerequisite_digests != FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS:
                failures.append(
                    "prerequisite controls do not use frozen-runtime digests"
                )
            non_correction_failures = tuple(
                value
                for value in prerequisite.failures
                if value != "residual correction scale"
            )
            failures.extend(
                "prerequisite: %s" % value for value in non_correction_failures
            )
            if prerequisite.terminal_guide_log_error > 1.0e-12:
                failures.append(
                    "terminal guide/target log-density error exceeds 1e-12"
                )
            if prerequisite.maximum_terminal_residual > 1.0e-10:
                failures.append("exact terminal residual exceeds 1e-10")
            if prerequisite.generator_row_sum_residual > 1.0e-10:
                failures.append("generator row-sum residual exceeds 1e-10")

    exact_wrapper = evidence.exact_population_control
    if exact_wrapper is None:
        pass
    elif type(exact_wrapper) is AssociationExactPopulationDiagnosticResult:
        try:
            exact_wrapper.__post_init__()
        except Exception as error:
            failures.append("raw exact-population control is malformed: %s" % error)
        else:
            if exact_wrapper.executed is not False:
                failures.append(
                    "executed exact-population control lacks aggregate SUCCESS custody"
                )
    elif type(exact_wrapper) is not LedgerVerifiedExactPopulationDiagnostic:
        failures.append(
            "exact-population control is not admitted by its aggregate SUCCESS ledger"
        )
    else:
        try:
            revalidated_exact_wrapper = (
                revalidate_completed_frozen_exact_population_diagnostic(
                    exact_wrapper
                )
            )
            exact = revalidated_exact_wrapper.result
        except Exception as error:
            failures.append("exact-population aggregate custody failed: %s" % error)
        else:
            current_source = frozen_association_training_source_sha256()
            current_configuration = frozen_exact_population_configuration_sha256(
                source_sha256=current_source
            )
            if (
                exact.source_sha256 != current_source
                or exact.exact_configuration_sha256 != current_configuration
                or exact.fixture_sha256 != frozen_association_fixture_sha256()
            ):
                failures.append("exact-population aggregate has stale custody")
            if (
                exact.product_control_optimized is not False
                or exact.oracle_product_control_passed is not True
                or exact.oracle_product_positive_maximum_absolute_logit
                > ORACLE_PRODUCT_POSITIVE_LOGIT_TOLERANCE
            ):
                failures.append("oracle product-positive logit exceeds 1e-9")
            expected_exact_coordinates = tuple(
                (seed, method)
                for seed in PAIRED_SEEDS
                for method in EXACT_POPULATION_METHODS
            )
            if (
                exact.executed is not True
                or exact.status != "DIAGNOSTIC_COMPLETE_NONDECISION"
                or exact.optimizer_steps_taken != EXACT_EXPECTED_TOTAL_OPTIMIZER_STEPS
                or tuple((value.seed, value.method) for value in exact.method_results)
                != expected_exact_coordinates
            ):
                failures.append(
                    "exact-population diagnostic is not the complete 8 x 3 / "
                    "%d-step nondecision record"
                    % EXACT_EXPECTED_TOTAL_OPTIMIZER_STEPS
                )

    guide = evidence.guide_alone
    if guide is not None:
        if type(guide) is not FrozenAssociationGuideAlonePathControl:
            failures.append("guide-alone control has the wrong exact type")
        else:
            if (
                guide.fixture_sha256 != frozen_association_fixture_sha256()
                or guide.guide_sha256 != FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS[3]
            ):
                failures.append("guide-alone control has stale fixture/guide custody")
            failures.extend(
                "guide-alone path: %s" % value
                for value in guide.path.numerical_gate_failures
            )

    rank = evidence.rank_stress_control
    rank_hard_gate_passed = False
    if rank is None:
        pass
    elif type(rank) is not LoaderVerifiedAssociationRankStressGateResult:
        failures.append(
            "rank-stress control is not loader-verified against prepared custody"
        )
    else:
        try:
            rank.revalidate_prepared_custody()
        except Exception as error:
            failures.append(
                "rank-stress prepared custody cannot be revalidated: %s" % error
            )
            return tuple(dict.fromkeys(failures)), False
        raw_rank = rank.raw_result
        if tuple(value.rank for value in raw_rank.rank_results) != RANK_STRESS_RANKS:
            failures.append("rank-stress control is not complete over all five ranks")
        if not raw_rank.runtime.fresh_process_marker_observed:
            failures.append("rank-stress fresh-process custody is absent")
        if not raw_rank.runtime.benchmark_metadata_complete:
            failures.append("rank-stress runtime metadata is incomplete")
        if raw_rank.source_sha256 != _rank_stress_source_bundle_sha256():
            failures.append("rank-stress source custody is stale")
        if raw_rank.specification_sha256 != _rank_stress_specification_sha256():
            failures.append("rank-stress specification custody is stale")
        for value in raw_rank.rank_results:
            if not value.full_oracle_agreement_verified:
                failures.append(
                    "rank %d analytic/exhaustive agreement exceeds 1e-10" % value.rank
                )
            if not value.benchmark_protocol_complete:
                failures.append("rank %d benchmark protocol is incomplete" % value.rank)
        try:
            current_suite_pass = rank.section_nine_gate_passed
        except Exception as error:
            failures.append("rank-stress source/spec custody cannot be revalidated: %s" % error)
            current_suite_pass = False
        rank_hard_gate_passed = all(
            value.hard_resource_gate_passed for value in raw_rank.rank_results
        )
        if current_suite_pass and not rank_hard_gate_passed:
            failures.append("rank suite PASS disagrees with its hard resource gates")
        if not current_suite_pass and rank_hard_gate_passed and not failures:
            failures.append("rank-stress source/specification custody is stale")
    return tuple(dict.fromkeys(failures)), rank_hard_gate_passed


def _learned_numerical_failures(
    evidence: FrozenAssociationCampaignEvidence,
) -> Tuple[str, ...]:
    failures = []
    reference_set = evidence.sampled_runs[0].path.reference_set_sha256
    if evidence.guide_alone.reference_set_sha256 != reference_set:
        failures.append("guide-alone and learned paths use different reference sets")
    for run in evidence.sampled_runs:
        prefix = "%d/%d/%s" % run.coordinate
        coherence = run.nonpath.coherence
        if coherence.terminal_maximum_absolute_log_information_error > 1.0e-12:
            failures.append(prefix + ": terminal log-information error exceeds 1e-12")
        if coherence.terminal_maximum_absolute_residual > 1.0e-10:
            failures.append(prefix + ": terminal residual exceeds 1e-10")
        if coherence.generator_row_sum_maximum_absolute_residual > 1.0e-10:
            failures.append(prefix + ": generator row-sum residual exceeds 1e-10")
        if coherence.edit_cycle_maximum_absolute_residual > 1.0e-10:
            failures.append(prefix + ": edit-cycle residual exceeds 1e-10")
        for message in run.path.numerical_gate_failures:
            failures.append(prefix + ": " + message)
        for item in run.path.observations:
            if (
                item.reference.unconditional_path_kl <= _RATIO_FLOOR
                or item.reference.refined_unconditional_path_kl <= _RATIO_FLOOR
            ):
                failures.append(prefix + ": unconditional path normalizer is <=1e-12")
    return tuple(dict.fromkeys(failures))


def _criterion(
    criterion_id: str,
    observed: object,
    requirement: str,
    passed: bool,
) -> FrozenAssociationDecisionCriterion:
    values = observed if type(observed) is tuple else (observed,)
    return FrozenAssociationDecisionCriterion(
        criterion_id=criterion_id,
        observed=tuple(float(value) for value in values),
        requirement=requirement,
        passed=bool(passed),
    )


def _material_criteria(
    evidence: FrozenAssociationCampaignEvidence,
    *,
    rank_hard_gate_passed: bool,
) -> Tuple[FrozenAssociationDecisionCriterion, ...]:
    runs = {value.coordinate: value for value in evidence.sampled_runs}

    def vector(
        method: str,
        budget: int,
        getter: Callable[[FrozenAssociationSampledRunEvidence], float],
    ) -> np.ndarray:
        result = np.asarray(
            [getter(runs[(seed, budget, method)]) for seed in PAIRED_SEEDS],
            dtype=np.float64,
        )
        if result.shape != (8,) or not np.all(np.isfinite(result)) or np.any(result < 0.0):
            raise ArithmeticError("a decision metric is not finite and nonnegative")
        return result

    bce = lambda run: run.nonpath.masked_excess_bce.joint_interpolation
    path = lambda run: run.path.ambiguous_normalized_path_score

    def aulc(method: str, getter: Callable[[FrozenAssociationSampledRunEvidence], float]) -> np.ndarray:
        return np.asarray(
            [
                ratio_equal_log_sample_aulc(
                    [getter(runs[(seed, budget, method)]) for budget in SAMPLE_BUDGETS]
                )
                for seed in PAIRED_SEEDS
            ],
            dtype=np.float64,
        )

    criteria = []
    guided_bce_aulc = aulc(GUIDED_METHOD, bce)
    direct_bce_aulc = aulc(DIRECT_METHOD, bce)
    guided_path_aulc = aulc(GUIDED_METHOD, path)
    direct_path_aulc = aulc(DIRECT_METHOD, path)
    for label, proposed, reference in (
        ("bce", guided_bce_aulc, direct_bce_aulc),
        ("path", guided_path_aulc, direct_path_aulc),
    ):
        ratio = paired_geometric_mean_ratio(proposed, reference)
        criteria.append(
            _criterion(
                "co_primary.%s.aulc.guided_vs_direct" % label,
                ratio,
                "paired geometric-mean ratio <= 0.75",
                ratio <= 0.75,
            )
        )
    bce_sign = paired_material_sign_test(guided_bce_aulc, direct_bce_aulc, margin=0.90)
    path_sign = paired_material_sign_test(guided_path_aulc, direct_path_aulc, margin=0.90)
    criteria.extend(
        (
            _criterion(
                "co_primary.bce.sign_test",
                (bce_sign.wins, bce_sign.p_value),
                "at least 7 strict wins at ratio 0.90",
                bce_sign.wins >= 7,
            ),
            _criterion(
                "co_primary.path.sign_test",
                (path_sign.wins, path_sign.p_value),
                "at least 7 strict wins at ratio 0.90",
                path_sign.wins >= 7,
            ),
        )
    )
    shared = shared_winning_seed_count(bce_sign, path_sign)
    criteria.append(
        _criterion(
            "co_primary.shared_winning_seeds",
            shared,
            "the same at least 7 seeds win both sign tests",
            shared >= 7,
        )
    )

    guided_retained = vector(
        GUIDED_METHOD, _MAXIMUM_BUDGET, lambda run: run.path.retained_normalized_path_score
    )
    direct_retained = vector(
        DIRECT_METHOD, _MAXIMUM_BUDGET, lambda run: run.path.retained_normalized_path_score
    )
    retained_ratio = paired_geometric_mean_ratio(guided_retained, direct_retained)
    retained_reduction = float(np.mean(direct_retained - guided_retained))
    criteria.extend(
        (
            _criterion(
                "retained_path.guided_vs_direct.ratio",
                retained_ratio,
                "paired geometric-mean ratio <= 0.80",
                retained_ratio <= 0.80,
            ),
            _criterion(
                "retained_path.guided_vs_direct.absolute_reduction",
                retained_reduction,
                "raw arithmetic-mean reduction >= 0.02",
                retained_reduction >= 0.02,
            ),
        )
    )

    ood_getters = (
        ("latent3", lambda run: run.nonpath.masked_excess_bce.latent_three),
        ("anchor3", lambda run: run.nonpath.masked_excess_bce.anchor_three),
        ("both3", lambda run: run.nonpath.masked_excess_bce.both_three),
        ("overflow", lambda run: run.nonpath.masked_excess_bce.overflow),
    )
    guided_ood = np.stack(
        [vector(GUIDED_METHOD, _MAXIMUM_BUDGET, getter) for _, getter in ood_getters],
        axis=1,
    )
    direct_ood = np.stack(
        [vector(DIRECT_METHOD, _MAXIMUM_BUDGET, getter) for _, getter in ood_getters],
        axis=1,
    )
    balanced_ratio = paired_geometric_mean_ratio(
        np.mean(guided_ood, axis=1), np.mean(direct_ood, axis=1)
    )
    criteria.append(
        _criterion(
            "ood.balanced.guided_vs_direct",
            balanced_ratio,
            "paired geometric-mean ratio <= 0.80",
            balanced_ratio <= 0.80,
        )
    )
    for index, (label, _) in enumerate(ood_getters):
        ratio = paired_geometric_mean_ratio(guided_ood[:, index], direct_ood[:, index])
        criteria.append(
            _criterion(
                "ood.%s.guided_vs_direct" % label,
                ratio,
                "paired geometric-mean ratio <= 1.05",
                ratio <= 1.05,
            )
        )

    for label, getter in (
        ("time", lambda run: run.nonpath.masked_excess_bce.time_interpolation),
        ("pair", lambda run: run.nonpath.masked_excess_bce.pair_interpolation),
    ):
        ratio = paired_geometric_mean_ratio(
            vector(GUIDED_METHOD, _MAXIMUM_BUDGET, getter),
            vector(DIRECT_METHOD, _MAXIMUM_BUDGET, getter),
        )
        criteria.append(
            _criterion(
                "interpolation.%s.guided_vs_direct" % label,
                ratio,
                "paired geometric-mean ratio <= 1.05",
                ratio <= 1.05,
            )
        )

    family_getters = (
        ("birth", lambda run: run.nonpath.edge_log_rates.birth.weighted_median_absolute_error),
        ("death", lambda run: run.nonpath.edge_log_rates.death.weighted_median_absolute_error),
        (
            "replacement",
            lambda run: run.nonpath.edge_log_rates.replacement.weighted_median_absolute_error,
        ),
    )
    family_ratios = []
    for label, getter in family_getters:
        ratio = paired_geometric_mean_ratio(
            vector(GUIDED_METHOD, _MAXIMUM_BUDGET, getter),
            vector(DIRECT_METHOD, _MAXIMUM_BUDGET, getter),
        )
        family_ratios.append(ratio)
        criteria.append(
            _criterion(
                "edit_family.%s.guided_vs_direct" % label,
                ratio,
                "paired geometric-mean weighted-median ratio <= 1.05",
                ratio <= 1.05,
            )
        )
    improved_families = sum(value <= 0.95 for value in family_ratios)
    criteria.append(
        _criterion(
            "edit_family.material_improvement_count",
            improved_families,
            "at least two family ratios <= 0.95",
            improved_families >= 2,
        )
    )

    strong_bce_aulc = aulc(STRONG_DIRECT_METHOD, bce)
    strong_path_aulc = aulc(STRONG_DIRECT_METHOD, path)
    for label, proposed_aulc, strong_aulc, getter in (
        ("bce", guided_bce_aulc, strong_bce_aulc, bce),
        ("path", guided_path_aulc, strong_path_aulc, path),
    ):
        curve_ratio = paired_geometric_mean_ratio(proposed_aulc, strong_aulc)
        maximum_ratio = paired_geometric_mean_ratio(
            vector(GUIDED_METHOD, _MAXIMUM_BUDGET, getter),
            vector(STRONG_DIRECT_METHOD, _MAXIMUM_BUDGET, getter),
        )
        criteria.extend(
            (
                _criterion(
                    "strong_direct.%s.aulc" % label,
                    curve_ratio,
                    "paired geometric-mean AULC ratio <= 0.90",
                    curve_ratio <= 0.90,
                ),
                _criterion(
                    "strong_direct.%s.maximum_budget" % label,
                    maximum_ratio,
                    "paired geometric-mean ratio <= 1.00",
                    maximum_ratio <= 1.00,
                ),
            )
        )

    guide_path = evidence.guide_alone.path
    guide_retained = np.full(8, guide_path.retained_normalized_path_score)
    guide_retained_ratio = paired_geometric_mean_ratio(guided_retained, guide_retained)
    criteria.append(
        _criterion(
            "guide_alone.retained_path",
            guide_retained_ratio,
            "paired geometric-mean ratio <= 0.90",
            guide_retained_ratio <= 0.90,
        )
    )
    ambiguous_ratios = []
    for observation_index in _AMBIGUOUS_INDICES:
        proposed = np.asarray(
            [
                runs[(seed, _MAXIMUM_BUDGET, GUIDED_METHOD)].path.normalized_path_kl_per_observation[
                    observation_index
                ]
                for seed in PAIRED_SEEDS
            ]
        )
        reference = np.full(
            8, guide_path.normalized_path_kl_per_observation[observation_index]
        )
        ratio = paired_geometric_mean_ratio(proposed, reference)
        ambiguous_ratios.append(ratio)
        criteria.append(
            _criterion(
                "guide_alone.ambiguous_observation_%d" % observation_index,
                ratio,
                "paired geometric-mean ratio <= 1.00",
                ratio <= 1.00,
            )
        )
    strong_ambiguous = sum(value <= 0.80 for value in ambiguous_ratios)
    criteria.append(
        _criterion(
            "guide_alone.ambiguous_strong_improvement_count",
            strong_ambiguous,
            "at least two ambiguous-observation ratios <= 0.80",
            strong_ambiguous >= 2,
        )
    )

    all_observation_ratios = []
    for observation_index in range(21):
        proposed = np.asarray(
            [
                runs[(seed, _MAXIMUM_BUDGET, GUIDED_METHOD)].path.normalized_path_kl_per_observation[
                    observation_index
                ]
                for seed in PAIRED_SEEDS
            ]
        )
        reference = np.asarray(
            [
                runs[(seed, _MAXIMUM_BUDGET, DIRECT_METHOD)].path.normalized_path_kl_per_observation[
                    observation_index
                ]
                for seed in PAIRED_SEEDS
            ]
        )
        ratio = paired_geometric_mean_ratio(proposed, reference)
        all_observation_ratios.append(ratio)
        criteria.append(
            _criterion(
                "all_observations.path_%02d.guided_vs_direct" % observation_index,
                ratio,
                "paired geometric-mean ratio <= 1.05",
                ratio <= 1.05,
            )
        )
    retained_strict_improvements = sum(
        ratio < 1.00
        for observation_index, ratio in enumerate(all_observation_ratios)
        if observation_index != _OVERFLOW_INDEX
    )
    criteria.append(
        _criterion(
            "retained_observations.strict_improvement_count",
            retained_strict_improvements,
            "at least two retained observations have strict paired-GM ratio < 1.00",
            retained_strict_improvements >= 2,
        )
    )

    for control, method, margin in (
        ("mismatch", MISMATCH_METHOD, 0.90),
        ("guide_input", GUIDE_INPUT_METHOD, 0.95),
    ):
        for label, guided_aulc, getter in (
            ("bce", guided_bce_aulc, bce),
            ("path", guided_path_aulc, path),
        ):
            control_aulc = aulc(method, getter)
            ratio = paired_geometric_mean_ratio(guided_aulc, control_aulc)
            sign = paired_material_sign_test(guided_aulc, control_aulc, margin=margin)
            criteria.extend(
                (
                    _criterion(
                        "identification.%s.%s.aulc" % (control, label),
                        ratio,
                        "paired geometric-mean AULC ratio <= %.2f" % margin,
                        ratio <= margin,
                    ),
                    _criterion(
                        "identification.%s.%s.strict_seed_wins" % (control, label),
                        (sign.wins, sign.p_value),
                        "at least 7 strict paired-seed ratios below %.2f" % margin,
                        sign.wins >= 7,
                    ),
                )
            )

    correction_ratio = evidence.prerequisite.correction_scale_ratio
    criteria.append(
        _criterion(
            "exact_residual.correction_scale",
            correction_ratio,
            "exact residual/direct correction-scale ratio <= 0.70",
            correction_ratio <= 0.70,
        )
    )
    criteria.append(
        _criterion(
            "rank_stress.operation_allocation",
            1.0 if rank_hard_gate_passed else 0.0,
            "all five hard operation/allocation gates pass",
            rank_hard_gate_passed,
        )
    )
    return tuple(criteria)


def _admit_supplied_sampled_runs(
    evidence: FrozenAssociationCampaignEvidence,
) -> Tuple[Tuple[object, ...], Tuple[str, ...]]:
    """Reopen every supplied run, accumulating fail-closed custody reasons."""

    admitted = []
    failures = []
    for run in evidence.sampled_runs:
        try:
            admitted.append(_canonical_checkpoint_for_supplied_run(run))
        except Exception as error:
            failures.append(
                "%r canonical SUCCESS admission failed: %s"
                % (run.coordinate, error)
            )
    return tuple(admitted), tuple(dict.fromkeys(failures))


def _refresh_complete_campaign_evidence(
    evidence: FrozenAssociationCampaignEvidence,
    admitted_checkpoints: Tuple[object, ...],
    fixture: FrozenAssociationResidualFixture,
    reference_set: FrozenAssociationPathReferenceSet,
    fresh_guide: FrozenAssociationGuideAlonePathControl,
) -> FrozenAssociationCampaignEvidence:
    """Discard caller metrics and rebuild all learned evidence canonically."""

    if len(admitted_checkpoints) != len(EXPECTED_SAMPLED_COORDINATES):
        raise RuntimeError("fresh metric evaluation requires all 120 checkpoints")
    fresh_runs = tuple(
        _evaluate_canonical_sampled_run_for_decision(
            verified,
            fixture,
            reference_set,
        )
        for verified in admitted_checkpoints
    )
    if tuple(value.coordinate for value in fresh_runs) != EXPECTED_SAMPLED_COORDINATES:
        raise RuntimeError("freshly evaluated checkpoints lost canonical ordering")
    return FrozenAssociationCampaignEvidence(
        campaign_sha256=evidence.campaign_sha256,
        sampled_runs=fresh_runs,
        guide_alone=fresh_guide,
        prerequisite=evidence.prerequisite,
        exact_population_control=evidence.exact_population_control,
        rank_stress_control=evidence.rank_stress_control,
    )


def _reduce_test_only_frozen_association_campaign_dtos(
    evidence: Optional[FrozenAssociationCampaignEvidence] = None,
) -> FrozenAssociationCampaignDecision:
    """Legacy DTO reducer retained only for focused unit tests.

    Production callers must use :func:`decide_frozen_association_campaign`,
    whose sampled input is the loader-only complete aggregate wrapper.  This
    helper is deliberately private and must never publish scientific evidence.
    """

    if evidence is None:
        return _decision(
            "NOT_RUN",
            None,
            ("no frozen A1 campaign evidence was supplied",),
        )
    if type(evidence) is not FrozenAssociationCampaignEvidence:
        return _decision(
            "HOLD",
            None,
            ("decision input has the wrong exact evidence type",),
        )
    try:
        evidence.__post_init__()
        for run in evidence.sampled_runs:
            run.__post_init__()
    except Exception as error:
        return _decision(
            "HOLD",
            None,
            ("decision evidence container is malformed: %s" % error,),
        )
    try:
        custody = _custody_failures(
            evidence,
            validate_metric_contents=False,
        )
    except Exception as error:
        return _decision(
            "HOLD",
            evidence,
            ("supplied sampled evidence is malformed: %s" % error,),
        )
    if custody:
        return _decision("HOLD", evidence, custody)
    admitted, admission_failures = _admit_supplied_sampled_runs(evidence)
    if admission_failures:
        return _decision("HOLD", evidence, admission_failures)
    try:
        control_failures, rank_hard_gate_passed = _control_hold_failures(evidence)
    except Exception as error:
        return _decision(
            "HOLD",
            evidence,
            ("supplied control evidence is malformed: %s" % error,),
        )
    if control_failures:
        return _decision("HOLD", evidence, control_failures)

    fixture = None
    reference_set = None
    fresh_guide = None
    if evidence.guide_alone is not None:
        try:
            fixture, reference_set = _fresh_frozen_decision_context()
            fresh_guide = _fresh_and_compare_guide_control(
                evidence.guide_alone,
                fixture,
                reference_set,
            )
        except Exception as error:
            return _decision(
                "HOLD",
                evidence,
                ("guide-alone canonical recomputation failed: %s" % error,),
            )

    missing = _missing_reasons(evidence)
    if missing:
        return _decision("NOT_RUN", evidence, missing)
    if fixture is None or reference_set is None or fresh_guide is None:
        return _decision(
            "HOLD",
            evidence,
            ("complete campaign lacks a fresh guide/reference decision context",),
        )
    try:
        refreshed = _refresh_complete_campaign_evidence(
            evidence,
            admitted,
            fixture,
            reference_set,
            fresh_guide,
        )
    except Exception as error:
        return _decision(
            "HOLD",
            evidence,
            ("canonical metric regeneration failed: %s" % error,),
        )

    # Close the evaluation-time TOCTOU window: after every expensive result is
    # formed, reopen all canonical SUCCESS records once more and compare them
    # with the freshly bound evidence.
    _, final_admission_failures = _admit_supplied_sampled_runs(refreshed)
    if final_admission_failures:
        return _decision("HOLD", refreshed, final_admission_failures)
    try:
        custody = _custody_failures(
            refreshed,
            validate_metric_contents=True,
        )
        control_failures, rank_hard_gate_passed = _control_hold_failures(
            refreshed
        )
    except Exception as error:
        return _decision(
            "HOLD",
            refreshed,
            ("final canonical evidence revalidation failed: %s" % error,),
        )
    if custody:
        return _decision("HOLD", refreshed, custody)
    if control_failures:
        return _decision("HOLD", refreshed, control_failures)
    numerical = _learned_numerical_failures(refreshed)
    if numerical:
        return _decision("HOLD", refreshed, numerical)
    try:
        criteria = _material_criteria(
            refreshed, rank_hard_gate_passed=rank_hard_gate_passed
        )
    except (ArithmeticError, FloatingPointError, OverflowError, ValueError) as error:
        return _decision(
            "HOLD",
            refreshed,
            ("material statistics could not be evaluated safely: %s" % error,),
        )
    failed = tuple(
        "%s failed: observed %r; required %s"
        % (value.criterion_id, value.observed, value.requirement)
        for value in criteria
        if not value.passed
    )
    if failed:
        return _decision("STOP", refreshed, failed, criteria)
    return _decision("PASS", refreshed, (), criteria)


def _aggregate_gate_decision(
    status: str,
    completed_sampled_campaign: Optional[object],
    reasons: Tuple[str, ...],
) -> FrozenAssociationCampaignDecision:
    """Return a fail-closed decision before any sampled metric DTO exists."""

    campaign_sha256 = None
    observed = 0
    if completed_sampled_campaign is not None:
        campaign_sha256 = getattr(
            completed_sampled_campaign, "campaign_sha256", None
        )
        if campaign_sha256 is not None:
            _sha256(campaign_sha256, name="campaign_sha256")
        try:
            observed = len(completed_sampled_campaign.checkpoints)
        except Exception:
            observed = 0
    return FrozenAssociationCampaignDecision(
        status=status,
        campaign_sha256=campaign_sha256,
        observed_sampled_coordinates=observed,
        expected_sampled_coordinates=len(EXPECTED_SAMPLED_COORDINATES),
        criteria=(),
        reasons=reasons,
    )


def _production_control_type_failures(
    exact_population_control: Optional[object],
    rank_stress_control: Optional[object],
) -> Tuple[str, ...]:
    """Require loader-only non-sampled controls before future metric work."""

    from heterodiff.experiments.finite_association_exact_population_isolated_runner import (
        LedgerVerifiedExactPopulationDiagnostic,
    )
    from heterodiff.experiments.finite_association_rank_stress import (
        LoaderVerifiedAssociationRankStressGateResult,
    )

    failures = []
    if (
        exact_population_control is not None
        and type(exact_population_control)
        is not LedgerVerifiedExactPopulationDiagnostic
    ):
        failures.append(
            "exact-population control must be its loader-verified aggregate wrapper"
        )
    if (
        rank_stress_control is not None
        and type(rank_stress_control)
        is not LoaderVerifiedAssociationRankStressGateResult
    ):
        failures.append(
            "rank-stress control must be its loader-verified custody wrapper"
        )
    return tuple(failures)


def _decide_scientifically_eligible_sampled_aggregate(
    completed_sampled_campaign: object,
    *,
    exact_population_control: Optional[object],
    rank_stress_control: Optional[object],
) -> FrozenAssociationCampaignDecision:
    """Future aggregate-only metric path, guarded by authority flags.

    The current custody aggregate deliberately cannot enter this function:
    execution-order attestation and scientific eligibility are both false.
    Keeping the metric path aggregate-native prevents any future migration
    from falling back to caller-supplied sampled metric DTOs.
    """

    if (
        completed_sampled_campaign.execution_order_attested is not True
        or completed_sampled_campaign.scientific_decision_eligible is not True
        or completed_sampled_campaign.fresh_metric_recomputation_required
        is not True
    ):
        raise RuntimeError(
            "sampled aggregate lacks scientific decision authorization"
        )
    control_type_failures = _production_control_type_failures(
        exact_population_control, rank_stress_control
    )
    if control_type_failures:
        return _aggregate_gate_decision(
            "HOLD", completed_sampled_campaign, control_type_failures
        )
    try:
        fixture, reference_set = _fresh_frozen_decision_context()
        fresh_guide = build_frozen_association_guide_alone_path_control(
            fixture, reference_set
        )
        prerequisite = run_association_residual_prerequisite_gate()
        shell = FrozenAssociationCampaignEvidence(
            campaign_sha256=completed_sampled_campaign.campaign_sha256,
            guide_alone=fresh_guide,
            prerequisite=prerequisite,
            exact_population_control=exact_population_control,
            rank_stress_control=rank_stress_control,
        )
        # This call freshly reloads the exact aggregate and rank-stress
        # prepared custody before any of the 120 expensive metric evaluations.
        control_failures, _ = _control_hold_failures(shell)
        if control_failures:
            return _aggregate_gate_decision(
                "HOLD", completed_sampled_campaign, control_failures
            )
        refreshed = _refresh_complete_campaign_evidence(
            shell,
            completed_sampled_campaign.checkpoints,
            fixture,
            reference_set,
            fresh_guide,
        )
    except Exception as error:
        return _aggregate_gate_decision(
            "HOLD",
            completed_sampled_campaign,
            ("canonical aggregate metric regeneration failed: %s" % error,),
        )

    missing = _missing_reasons(refreshed)
    if missing:
        return _decision("NOT_RUN", refreshed, missing)

    # Close the expensive evaluation window from one new aggregate load, then
    # match every freshly computed DTO to the 120 wrappers in that same load.
    try:
        from heterodiff.experiments.finite_association_isolated_runner import (
            revalidate_completed_frozen_association_sampled_campaign,
        )

        final_campaign = (
            revalidate_completed_frozen_association_sampled_campaign(
                completed_sampled_campaign
            )
        )
        if (
            final_campaign.aggregate_sha256
            != completed_sampled_campaign.aggregate_sha256
            or final_campaign.ordered_success_receipts_sha256
            != completed_sampled_campaign.ordered_success_receipts_sha256
            or final_campaign.ordered_checkpoint_sha256
            != completed_sampled_campaign.ordered_checkpoint_sha256
        ):
            raise RuntimeError("sampled aggregate changed during metric evaluation")
        if len(final_campaign.checkpoints) != len(refreshed.sampled_runs):
            raise RuntimeError("sampled aggregate lost a canonical checkpoint")
        for run, verified in zip(
            refreshed.sampled_runs, final_campaign.checkpoints
        ):
            _match_supplied_run_to_verified_checkpoint(run, verified)
    except Exception as error:
        return _decision(
            "HOLD",
            refreshed,
            ("final aggregate TOCTOU revalidation failed: %s" % error,),
        )

    try:
        custody = _custody_failures(
            refreshed, validate_metric_contents=True
        )
        control_failures, rank_hard_gate_passed = _control_hold_failures(
            refreshed
        )
    except Exception as error:
        return _decision(
            "HOLD",
            refreshed,
            ("final canonical evidence revalidation failed: %s" % error,),
        )
    if custody:
        return _decision("HOLD", refreshed, custody)
    if control_failures:
        return _decision("HOLD", refreshed, control_failures)
    numerical = _learned_numerical_failures(refreshed)
    if numerical:
        return _decision("HOLD", refreshed, numerical)
    try:
        criteria = _material_criteria(
            refreshed, rank_hard_gate_passed=rank_hard_gate_passed
        )
    except (ArithmeticError, FloatingPointError, OverflowError, ValueError) as error:
        return _decision(
            "HOLD",
            refreshed,
            ("material statistics could not be evaluated safely: %s" % error,),
        )
    failed = tuple(
        "%s failed: observed %r; required %s"
        % (value.criterion_id, value.observed, value.requirement)
        for value in criteria
        if not value.passed
    )
    if failed:
        return _decision("STOP", refreshed, failed, criteria)
    return _decision("PASS", refreshed, (), criteria)


def decide_frozen_association_campaign(
    completed_sampled_campaign: Optional[object] = None,
    *,
    exact_population_control: Optional[object] = None,
    rank_stress_control: Optional[object] = None,
) -> FrozenAssociationCampaignDecision:
    """Admit only the loader-verified complete sampled aggregate.

    No optimizer is invoked.  The current aggregate is intentionally custody
    only: until a later, separately authorized execution-order layer changes
    both authority flags, this entry point returns ``HOLD`` before metric
    recomputation.  Caller-supplied sampled metric DTOs are never production
    input.
    """

    if completed_sampled_campaign is None:
        return _aggregate_gate_decision(
            "NOT_RUN",
            None,
            ("no completed sampled aggregate was supplied",),
        )
    from heterodiff.experiments.finite_association_isolated_runner import (
        LedgerVerifiedFrozenAssociationSampledCampaign,
        revalidate_completed_frozen_association_sampled_campaign,
    )

    if type(completed_sampled_campaign) is not (
        LedgerVerifiedFrozenAssociationSampledCampaign
    ):
        return _aggregate_gate_decision(
            "HOLD",
            None,
            (
                "production decision input must be the loader-verified "
                "completed sampled aggregate",
            ),
        )
    try:
        canonical = revalidate_completed_frozen_association_sampled_campaign(
            completed_sampled_campaign
        )
    except Exception as error:
        return _aggregate_gate_decision(
            "HOLD",
            completed_sampled_campaign,
            ("completed sampled aggregate revalidation failed: %s" % error,),
        )
    authority_failures = []
    if canonical.fresh_metric_recomputation_required is not True:
        authority_failures.append(
            "sampled aggregate does not require fresh metric recomputation"
        )
    if canonical.execution_order_attested is not True:
        authority_failures.append(
            "sampled aggregate has no execution-order attestation"
        )
    if canonical.scientific_decision_eligible is not True:
        authority_failures.append(
            "sampled aggregate is custody-only and not scientific-decision eligible"
        )
    if authority_failures:
        return _aggregate_gate_decision(
            "HOLD", canonical, tuple(authority_failures)
        )
    return _decide_scientifically_eligible_sampled_aggregate(
        canonical,
        exact_population_control=exact_population_control,
        rank_stress_control=rank_stress_control,
    )


__all__ = [
    "DIRECT_METHOD",
    "EXPECTED_DECISION_CRITERION_IDS",
    "EXPECTED_SAMPLED_COORDINATES",
    "FrozenAssociationCampaignDecision",
    "FrozenAssociationDecisionCriterion",
    "FrozenAssociationGuideAlonePathControl",
    "GUIDED_METHOD",
    "GUIDE_INPUT_METHOD",
    "MISMATCH_METHOD",
    "SAMPLED_METHODS",
    "STRONG_DIRECT_METHOD",
    "build_frozen_association_guide_alone_path_control",
    "decide_frozen_association_campaign",
]
