"""Result-independent non-path evaluation for the frozen finite A1 fixture.

The evaluator in this module consumes a *certificate-bound* classifier-logit
callable and the exact finite population fixture.  It does not import PyTorch,
train a model, select a checkpoint, integrate a path law, or make an empirical
decision.  The only accepted classifier convention is

``logit(t, x, a) = log h(t, x; a) - log z_A(a)``.

All population averages use physical probability masses.  In particular,
observation-reference densities are converted back to physical information
only after restoring the frozen observation-marginal density ``z_A``.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Callable, Optional, Tuple

import numpy as np

from heterodiff.evaluation.finite_association_residual_metrics import (
    deterministic_weighted_median,
    normalized_masked_excess_bce,
)
from heterodiff.experiments.finite_association_guided_residual_pilot import (
    FrozenAssociationResidualFixture,
    FrozenAssociationResidualSplits,
    frozen_association_fixture_content_digests,
    frozen_association_fixture_sha256,
    frozen_association_residual_splits,
)


_FROZEN_TIME_COUNT = 33
_FROZEN_STATE_COUNT = 20
_FROZEN_OBSERVATION_COUNT = 21
_CERTIFICATE_GRID_INTERVALS = 4096
_CERTIFICATE_GRID_POINTS = 4097
_CERTIFICATE_TIME_CHUNK = 128
_CERTIFICATE_PAIR_COUNT = 20 * 21
_CERTIFICATE_OUTPUT_COUNT = _CERTIFICATE_GRID_POINTS * _CERTIFICATE_PAIR_COUNT
_CERTIFICATE_CORRECTION_LIMIT = 20.0
_PHYSICAL_LOG_INFORMATION_LIMIT = 24.0
_RELIABILITY_BIN_COUNT = 10
_FAMILY_ORDER = ("birth", "death", "replacement")


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    contiguous = np.array(array, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=np.float64
    ).reshape(contiguous.shape)


def _real_scalar(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite" % name)
    return result


def _nonnegative_scalar(value: object, *, name: str) -> float:
    result = _real_scalar(value, name=name)
    if result < 0.0:
        raise ValueError("%s must be nonnegative" % name)
    return result


def _integer_scalar(value: object, *, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    return int(value)


def _sha256(value: object, *, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("%s must be a 64-character SHA-256 digest" % name)
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("%s must be hexadecimal" % name) from error
    if value != value.lower():
        raise ValueError("%s must use lowercase hexadecimal" % name)
    return value


def _certificate_attribute(certificate: object, name: str) -> object:
    try:
        return getattr(certificate, name)
    except AttributeError as error:
        raise TypeError(
            "continuous certificate is missing %s" % name
        ) from error


@dataclass(frozen=True)
class FiniteAssociationLogitCertification:
    """Immutable NumPy-side custody record copied from the Torch certificate.

    This record validates the frozen coverage and bound fields.  The caller
    must create it only after the Torch-side
    ``require_matching_continuous_certificate`` check has bound that
    certificate to the fitted model.  Copying the two digests here prevents a
    later evaluator from silently dropping the checkpoint/feature identity.
    """

    parameter_sha256: str
    frozen_fixture_sha256: str
    feature_sha256: str
    input_features: int
    hidden_width: int
    grid_intervals: int
    grid_points: int
    time_chunk_size: int
    pair_count: int
    evaluated_output_count: int
    layer_outward_row_sums: Tuple[float, float, float]
    input_time_lipschitz: float
    network_time_lipschitz: float
    maximum_grid_absolute_correction: float
    outward_grid_maximum: float
    half_cell_allowance: float
    certified_maximum_absolute_correction: float
    correction_limit: float
    certificate_sha256: str

    def __post_init__(self) -> None:
        parameter = _sha256(self.parameter_sha256, name="parameter_sha256")
        fixture = _sha256(
            self.frozen_fixture_sha256, name="frozen_fixture_sha256"
        )
        feature = _sha256(self.feature_sha256, name="feature_sha256")
        certificate = _sha256(
            self.certificate_sha256, name="certificate_sha256"
        )
        inputs = _integer_scalar(self.input_features, name="input_features")
        width = _integer_scalar(self.hidden_width, name="hidden_width")
        intervals = _integer_scalar(self.grid_intervals, name="grid_intervals")
        points = _integer_scalar(self.grid_points, name="grid_points")
        chunk = _integer_scalar(
            self.time_chunk_size, name="time_chunk_size"
        )
        pairs = _integer_scalar(self.pair_count, name="pair_count")
        outputs = _integer_scalar(
            self.evaluated_output_count, name="evaluated_output_count"
        )
        bound = _real_scalar(
            self.certified_maximum_absolute_correction,
            name="certified_maximum_absolute_correction",
        )
        limit = _real_scalar(self.correction_limit, name="correction_limit")
        row_sums = tuple(
            _real_scalar(value, name="layer_outward_row_sums")
            for value in self.layer_outward_row_sums
        )
        input_lipschitz = _real_scalar(
            self.input_time_lipschitz, name="input_time_lipschitz"
        )
        network_lipschitz = _real_scalar(
            self.network_time_lipschitz, name="network_time_lipschitz"
        )
        grid_maximum = _real_scalar(
            self.maximum_grid_absolute_correction,
            name="maximum_grid_absolute_correction",
        )
        outward_maximum = _real_scalar(
            self.outward_grid_maximum, name="outward_grid_maximum"
        )
        half_cell = _real_scalar(
            self.half_cell_allowance, name="half_cell_allowance"
        )
        if (inputs, width) not in ((21, 32), (21, 40), (22, 32)):
            raise ValueError("certificate architecture is not a frozen A1 learner")
        if intervals != _CERTIFICATE_GRID_INTERVALS:
            raise ValueError("certificate must use 4096 time intervals")
        if points != _CERTIFICATE_GRID_POINTS:
            raise ValueError("certificate must use 4097 time points")
        if chunk != _CERTIFICATE_TIME_CHUNK:
            raise ValueError("certificate must use the frozen time chunk")
        if pairs != _CERTIFICATE_PAIR_COUNT:
            raise ValueError("certificate must cover all 20 x 21 pairs")
        if outputs != _CERTIFICATE_OUTPUT_COUNT:
            raise ValueError("certificate output coverage is incomplete")
        if limit != _CERTIFICATE_CORRECTION_LIMIT:
            raise ValueError("certificate correction limit must equal 20")
        if bound < 0.0 or bound > limit:
            raise ValueError("certified correction bound exceeds its limit")
        if len(row_sums) != 3 or any(value < 0.0 for value in row_sums):
            raise ValueError("certificate row-sum witness is invalid")
        if any(
            value < 0.0
            for value in (
                input_lipschitz,
                network_lipschitz,
                grid_maximum,
                outward_maximum,
                half_cell,
            )
        ):
            raise ValueError("certificate bound witness is invalid")
        if outward_maximum != math.nextafter(grid_maximum, math.inf):
            raise ValueError("certificate grid maximum is not outward rounded")
        object.__setattr__(self, "parameter_sha256", parameter)
        object.__setattr__(self, "frozen_fixture_sha256", fixture)
        object.__setattr__(self, "feature_sha256", feature)
        object.__setattr__(self, "certificate_sha256", certificate)
        object.__setattr__(self, "input_features", inputs)
        object.__setattr__(self, "hidden_width", width)
        object.__setattr__(self, "grid_intervals", intervals)
        object.__setattr__(self, "grid_points", points)
        object.__setattr__(self, "time_chunk_size", chunk)
        object.__setattr__(self, "pair_count", pairs)
        object.__setattr__(self, "evaluated_output_count", outputs)
        object.__setattr__(self, "layer_outward_row_sums", row_sums)
        object.__setattr__(self, "input_time_lipschitz", input_lipschitz)
        object.__setattr__(self, "network_time_lipschitz", network_lipschitz)
        object.__setattr__(
            self, "maximum_grid_absolute_correction", grid_maximum
        )
        object.__setattr__(self, "outward_grid_maximum", outward_maximum)
        object.__setattr__(self, "half_cell_allowance", half_cell)
        object.__setattr__(
            self, "certified_maximum_absolute_correction", bound
        )
        object.__setattr__(self, "correction_limit", limit)

    @classmethod
    def from_continuous_certificate(
        cls, certificate: object
    ) -> "FiniteAssociationLogitCertification":
        if _certificate_attribute(certificate, "passed") is not True:
            raise ValueError("continuous certificate must be an exact PASS")
        names = (
            "parameter_sha256",
            "frozen_fixture_sha256",
            "feature_sha256",
            "input_features",
            "hidden_width",
            "grid_intervals",
            "grid_points",
            "time_chunk_size",
            "pair_count",
            "evaluated_output_count",
            "layer_outward_row_sums",
            "input_time_lipschitz",
            "network_time_lipschitz",
            "maximum_grid_absolute_correction",
            "outward_grid_maximum",
            "half_cell_allowance",
            "certified_maximum_absolute_correction",
            "correction_limit",
            "certificate_sha256",
        )
        values = {
            name: _certificate_attribute(certificate, name) for name in names
        }
        return cls(**values)


_EVALUATOR_CONSTRUCTION_KEY = object()


class CertifiedFiniteAssociationLogitEvaluator:
    """Certificate-bound callable returning full finite classifier-logit grids.

    The wrapped callable receives one immutable increasing float64 time vector
    and must return an array of shape ``[time, 20, 21]`` in canonical fixture
    order.  Supporting arbitrary times, rather than only the 33 reporting
    knots, lets the same frozen checkpoint be adapted later to an independently
    refined path integrator without changing its evaluation convention.
    """

    __slots__ = (
        "_evaluate_logits",
        "_assert_integrity",
        "_certification",
        "_production_bound",
        "_classifier_sha256",
        "_execution_receipt_sha256",
        "_campaign_sha256",
        "_locked",
    )

    def __init__(
        self,
        evaluate_logits: Callable[[np.ndarray], np.ndarray],
        certification: FiniteAssociationLogitCertification,
        *,
        production_bound: bool,
        classifier_sha256: Optional[str],
        execution_receipt_sha256: Optional[str],
        campaign_sha256: Optional[str],
        assert_integrity: Optional[Callable[[], None]],
        _construction_key: object,
    ) -> None:
        if _construction_key is not _EVALUATOR_CONSTRUCTION_KEY:
            raise TypeError("use a declared evaluator binding function")
        if not callable(evaluate_logits):
            raise TypeError("evaluate_logits must be callable")
        if type(certification) is not FiniteAssociationLogitCertification:
            raise TypeError(
                "certification must be a FiniteAssociationLogitCertification"
            )
        if type(production_bound) is not bool:
            raise TypeError("production_bound must be boolean")
        if production_bound:
            classifier = _sha256(
                classifier_sha256, name="classifier_sha256"
            )
            receipt = _sha256(
                execution_receipt_sha256,
                name="execution_receipt_sha256",
            )
            campaign = _sha256(
                campaign_sha256,
                name="campaign_sha256",
            )
            if not callable(assert_integrity):
                raise TypeError(
                    "production evaluators require an integrity callback"
                )
        elif classifier_sha256 is not None:
            raise ValueError("test-only evaluators must not claim a classifier hash")
        elif execution_receipt_sha256 is not None:
            raise ValueError("test-only evaluators must not claim an execution receipt")
        elif campaign_sha256 is not None:
            raise ValueError("test-only evaluators must not claim campaign custody")
        elif assert_integrity is not None:
            raise ValueError("test-only evaluators must not claim integrity custody")
        else:
            classifier = None
            receipt = None
            campaign = None
        object.__setattr__(self, "_evaluate_logits", evaluate_logits)
        object.__setattr__(self, "_assert_integrity", assert_integrity)
        object.__setattr__(self, "_certification", certification)
        object.__setattr__(self, "_production_bound", production_bound)
        object.__setattr__(self, "_classifier_sha256", classifier)
        object.__setattr__(self, "_execution_receipt_sha256", receipt)
        object.__setattr__(self, "_campaign_sha256", campaign)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("certified evaluator binding is immutable")
        object.__setattr__(self, name, value)

    @property
    def certification(self) -> FiniteAssociationLogitCertification:
        return self._certification

    @property
    def production_bound(self) -> bool:
        return self._production_bound

    @property
    def classifier_sha256(self) -> Optional[str]:
        return self._classifier_sha256

    @property
    def execution_receipt_sha256(self) -> Optional[str]:
        return self._execution_receipt_sha256

    @property
    def campaign_sha256(self) -> Optional[str]:
        return self._campaign_sha256

    def assert_integrity(self) -> None:
        """Revalidate production custody once at an evaluation boundary."""

        if self._production_bound:
            result = self._assert_integrity()
            if result is not None:
                raise TypeError("integrity callback must return None")

    def __call__(self, direct_times: object) -> np.ndarray:
        try:
            raw = np.asarray(direct_times)
            objects = np.asarray(direct_times, dtype=object)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("direct_times must be a numeric vector") from error
        if any(isinstance(item, (bool, np.bool_)) for item in objects.flat):
            raise TypeError("direct_times must not contain booleans")
        if raw.dtype.kind not in "iuf" or raw.ndim != 1 or raw.size == 0:
            raise ValueError("direct_times must be a nonempty numeric vector")
        times = raw.astype(np.float64, copy=True)
        if not np.all(np.isfinite(times)):
            raise ValueError("direct_times must be finite")
        if np.any(times < 0.0) or np.any(times > 1.0):
            raise ValueError("direct_times must lie in [0, 1]")
        if times.size > 1 and np.any(times[1:] <= times[:-1]):
            raise ValueError("direct_times must be strictly increasing")
        immutable_times = _immutable_float_array(times)
        try:
            evaluated = self._evaluate_logits(immutable_times)
            values = np.asarray(evaluated)
            object_values = np.asarray(evaluated, dtype=object)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("logit callable returned a nonnumeric grid") from error
        if any(
            isinstance(item, (bool, np.bool_)) for item in object_values.flat
        ):
            raise TypeError("logit callable returned boolean values")
        if values.dtype.kind not in "iuf":
            raise TypeError("logit callable must return a real numeric grid")
        expected = (times.size, _FROZEN_STATE_COUNT, _FROZEN_OBSERVATION_COUNT)
        if values.shape != expected:
            raise ValueError("logit callable must return shape %r" % (expected,))
        result = values.astype(np.float64, copy=True)
        if not np.all(np.isfinite(result)):
            raise ValueError("logit callable returned non-finite values")
        return _immutable_float_array(result)


def bind_test_only_finite_association_logit_evaluator(
    evaluate_logits: Callable[[np.ndarray], np.ndarray],
    continuous_certificate: object,
) -> CertifiedFiniteAssociationLogitEvaluator:
    """Bind a synthetic/oracle callback that is ineligible for learned results."""

    certification = FiniteAssociationLogitCertification.from_continuous_certificate(
        continuous_certificate
    )
    return CertifiedFiniteAssociationLogitEvaluator(
        evaluate_logits,
        certification,
        production_bound=False,
        classifier_sha256=None,
        execution_receipt_sha256=None,
        campaign_sha256=None,
        assert_integrity=None,
        _construction_key=_EVALUATOR_CONSTRUCTION_KEY,
    )


def _bind_production_finite_association_logit_evaluator(
    verified_checkpoint: object,
) -> CertifiedFiniteAssociationLogitEvaluator:
    """Derive the entire production binding from canonical SUCCESS custody."""

    from heterodiff.experiments.finite_association_isolated_runner import (
        revalidate_successful_frozen_association_checkpoint,
    )
    from heterodiff.experiments.finite_association_residual_training_torch import (
        LedgerVerifiedFittedAssociationCheckpoint,
        _BoundFittedAssociationLogitGrid,
    )

    if type(verified_checkpoint) is not LedgerVerifiedFittedAssociationCheckpoint:
        raise TypeError("production binding requires a SUCCESS-ledger checkpoint")
    revalidate_successful_frozen_association_checkpoint(verified_checkpoint)
    checkpoint = verified_checkpoint.checkpoint
    bound = _BoundFittedAssociationLogitGrid(checkpoint)

    def assert_canonical_integrity() -> None:
        revalidate_successful_frozen_association_checkpoint(verified_checkpoint)
        bound.assert_integrity()

    certification = FiniteAssociationLogitCertification.from_continuous_certificate(
        checkpoint.certificate
    )
    return CertifiedFiniteAssociationLogitEvaluator(
        bound,
        certification,
        production_bound=True,
        classifier_sha256=checkpoint.classifier_sha256,
        execution_receipt_sha256=verified_checkpoint.success_receipt_sha256,
        campaign_sha256=verified_checkpoint.campaign_sha256,
        assert_integrity=assert_canonical_integrity,
        _construction_key=_EVALUATOR_CONSTRUCTION_KEY,
    )


@dataclass(frozen=True)
class MaskedExcessBCEDiagnostics:
    train: float
    validation: float
    joint_interpolation: float
    time_interpolation: float
    pair_interpolation: float
    latent_three: float
    anchor_three: float
    both_three: float
    overflow: float
    balanced_ood: float

    def __post_init__(self) -> None:
        values = {
            name: _nonnegative_scalar(getattr(self, name), name=name)
            for name in (
                "train",
                "validation",
                "joint_interpolation",
                "time_interpolation",
                "pair_interpolation",
                "latent_three",
                "anchor_three",
                "both_three",
                "overflow",
                "balanced_ood",
            )
        }
        expected = (
            values["latent_three"]
            + values["anchor_three"]
            + values["both_three"]
            + values["overflow"]
        ) / 4.0
        if not math.isclose(
            values["balanced_ood"], expected, rel_tol=2.0e-13, abs_tol=2.0e-14
        ):
            raise ValueError("balanced_ood is inconsistent with its four strata")
        for name, value in values.items():
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class CenteredLogInformationDiagnostics:
    physical_weighted_rmse: float
    maximum_absolute_error: float

    def __post_init__(self) -> None:
        for name in ("physical_weighted_rmse", "maximum_absolute_error"):
            object.__setattr__(
                self, name, _nonnegative_scalar(getattr(self, name), name=name)
            )


@dataclass(frozen=True)
class ResidualDiagnostics:
    physical_weighted_rmse: float
    maximum_absolute_error: float
    candidate_minimum: float
    candidate_maximum: float
    candidate_range: float
    oracle_minimum: float
    oracle_maximum: float
    oracle_range: float

    def __post_init__(self) -> None:
        for name in ("physical_weighted_rmse", "maximum_absolute_error"):
            object.__setattr__(
                self, name, _nonnegative_scalar(getattr(self, name), name=name)
            )
        for prefix in ("candidate", "oracle"):
            minimum = _real_scalar(getattr(self, prefix + "_minimum"), name=prefix + "_minimum")
            maximum = _real_scalar(getattr(self, prefix + "_maximum"), name=prefix + "_maximum")
            span = _nonnegative_scalar(getattr(self, prefix + "_range"), name=prefix + "_range")
            if maximum < minimum or not math.isclose(
                span, maximum - minimum, rel_tol=2.0e-13, abs_tol=2.0e-14
            ):
                raise ValueError("%s residual range is inconsistent" % prefix)
            object.__setattr__(self, prefix + "_minimum", minimum)
            object.__setattr__(self, prefix + "_maximum", maximum)
            object.__setattr__(self, prefix + "_range", span)


@dataclass(frozen=True)
class EdgeFamilyDiagnostics:
    family: str
    active_edge_count: int
    physical_weight: float
    physical_weighted_rmse: float
    maximum_absolute_error: float
    weighted_median_absolute_error: float

    def __post_init__(self) -> None:
        if type(self.family) is not str or self.family not in _FAMILY_ORDER:
            raise ValueError("edge family is not frozen")
        if (
            isinstance(self.active_edge_count, (bool, np.bool_))
            or not isinstance(self.active_edge_count, Integral)
            or int(self.active_edge_count) <= 0
        ):
            raise ValueError("active_edge_count must be a positive integer")
        object.__setattr__(self, "active_edge_count", int(self.active_edge_count))
        for name in (
            "physical_weight",
            "physical_weighted_rmse",
            "maximum_absolute_error",
            "weighted_median_absolute_error",
        ):
            value = _nonnegative_scalar(getattr(self, name), name=name)
            if name == "physical_weight" and value <= 0.0:
                raise ValueError("physical_weight must be positive")
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class EdgeLogRateDiagnostics:
    birth: EdgeFamilyDiagnostics
    death: EdgeFamilyDiagnostics
    replacement: EdgeFamilyDiagnostics

    def __post_init__(self) -> None:
        values = (self.birth, self.death, self.replacement)
        if any(type(value) is not EdgeFamilyDiagnostics for value in values):
            raise TypeError("edge diagnostics must contain exact family records")
        if tuple(value.family for value in values) != _FAMILY_ORDER:
            raise ValueError("edge diagnostics are not in frozen family order")


@dataclass(frozen=True, eq=False)
class ConditionalInitialTVDiagnostics:
    per_observation: np.ndarray
    observation_weighted_mean: float
    retained_observation_weighted_mean: float
    maximum: float
    overflow: float

    def __post_init__(self) -> None:
        values = np.asarray(self.per_observation, dtype=np.float64)
        if values.shape != (_FROZEN_OBSERVATION_COUNT,):
            raise ValueError("per_observation TV must have length 21")
        if not np.all(np.isfinite(values)) or np.any(values < 0.0):
            raise ValueError("per_observation TV values must be finite and nonnegative")
        for name in (
            "observation_weighted_mean",
            "retained_observation_weighted_mean",
            "maximum",
            "overflow",
        ):
            object.__setattr__(
                self, name, _nonnegative_scalar(getattr(self, name), name=name)
            )
        if not math.isclose(
            self.maximum,
            float(np.max(values)),
            rel_tol=2.0e-13,
            abs_tol=2.0e-14,
        ) or not math.isclose(
            self.overflow,
            float(values[-1]),
            rel_tol=2.0e-13,
            abs_tol=2.0e-14,
        ):
            raise ValueError("conditional initial TV summary is inconsistent")
        object.__setattr__(self, "per_observation", _immutable_float_array(values))


@dataclass(frozen=True, eq=False)
class CalibrationDiagnostics:
    brier: float
    optimal_brier: float
    excess_brier: float
    reliability_ece: float
    maximum_reliability_gap: float
    bin_mass: np.ndarray
    bin_mean_prediction: np.ndarray
    bin_positive_frequency: np.ndarray

    def __post_init__(self) -> None:
        for name in (
            "brier",
            "optimal_brier",
            "excess_brier",
            "reliability_ece",
            "maximum_reliability_gap",
        ):
            object.__setattr__(
                self, name, _nonnegative_scalar(getattr(self, name), name=name)
            )
        for name in (
            "bin_mass",
            "bin_mean_prediction",
            "bin_positive_frequency",
        ):
            value = np.asarray(getattr(self, name), dtype=np.float64)
            if value.shape != (_RELIABILITY_BIN_COUNT,):
                raise ValueError("%s must have ten entries" % name)
            if not np.all(np.isfinite(value)) or np.any(value < 0.0):
                raise ValueError("%s must be finite and nonnegative" % name)
            object.__setattr__(self, name, _immutable_float_array(value))
        if not math.isclose(
            self.excess_brier,
            self.brier - self.optimal_brier,
            rel_tol=2.0e-12,
            abs_tol=2.0e-14,
        ):
            raise ValueError("excess Brier score is inconsistent")
        if not math.isclose(
            math.fsum(float(value) for value in self.bin_mass),
            1.0,
            rel_tol=0.0,
            abs_tol=2.0e-12,
        ):
            raise ValueError("calibration bin masses must sum to one")
        occupied = self.bin_mass > 0.0
        if np.any(self.bin_mean_prediction[occupied] > 1.0) or np.any(
            self.bin_positive_frequency[occupied] > 1.0
        ):
            raise ValueError("occupied calibration-bin values must lie in [0, 1]")
        gaps = np.abs(self.bin_mean_prediction - self.bin_positive_frequency)
        expected_ece = float(self.bin_mass @ gaps)
        expected_maximum = float(np.max(gaps[occupied]))
        if not math.isclose(
            self.reliability_ece,
            expected_ece,
            rel_tol=2.0e-12,
            abs_tol=2.0e-14,
        ) or not math.isclose(
            self.maximum_reliability_gap,
            expected_maximum,
            rel_tol=2.0e-12,
            abs_tol=2.0e-14,
        ):
            raise ValueError("calibration reliability summary is inconsistent")


@dataclass(frozen=True)
class CoherenceDiagnostics:
    terminal_maximum_absolute_log_information_error: float
    terminal_maximum_absolute_residual: float
    generator_row_sum_maximum_absolute_residual: float
    normalization_physical_weighted_rmse: float
    normalization_maximum_absolute_residual: float
    semigroup_physical_weighted_rmse: float
    semigroup_maximum_absolute_residual: float
    edit_cycle_maximum_absolute_residual: float
    edit_cycle_count: int

    def __post_init__(self) -> None:
        for name in (
            "terminal_maximum_absolute_log_information_error",
            "terminal_maximum_absolute_residual",
            "generator_row_sum_maximum_absolute_residual",
            "normalization_physical_weighted_rmse",
            "normalization_maximum_absolute_residual",
            "semigroup_physical_weighted_rmse",
            "semigroup_maximum_absolute_residual",
            "edit_cycle_maximum_absolute_residual",
        ):
            object.__setattr__(
                self, name, _nonnegative_scalar(getattr(self, name), name=name)
            )
        if (
            isinstance(self.edit_cycle_count, (bool, np.bool_))
            or not isinstance(self.edit_cycle_count, Integral)
            or int(self.edit_cycle_count) <= 0
        ):
            raise ValueError("edit_cycle_count must be a positive integer")
        object.__setattr__(self, "edit_cycle_count", int(self.edit_cycle_count))


@dataclass(frozen=True, eq=False)
class FiniteAssociationNonPathEvaluation:
    """All mandatory 33-knot diagnostics that require no path integration."""

    parameter_sha256: str
    feature_sha256: str
    classifier_sha256: Optional[str]
    execution_receipt_sha256: Optional[str]
    campaign_sha256: Optional[str]
    production_bound: bool
    classifier_logit_grid: np.ndarray
    log_information_grid: np.ndarray
    residual_log_grid: np.ndarray
    masked_excess_bce: MaskedExcessBCEDiagnostics
    centered_log_information: CenteredLogInformationDiagnostics
    residual: ResidualDiagnostics
    edge_log_rates: EdgeLogRateDiagnostics
    conditional_initial_tv: ConditionalInitialTVDiagnostics
    calibration: CalibrationDiagnostics
    coherence: CoherenceDiagnostics

    def __post_init__(self) -> None:
        parameter = _sha256(self.parameter_sha256, name="parameter_sha256")
        feature = _sha256(self.feature_sha256, name="feature_sha256")
        if type(self.production_bound) is not bool:
            raise TypeError("production_bound must be boolean")
        if self.production_bound:
            classifier = _sha256(self.classifier_sha256, name="classifier_sha256")
            receipt = _sha256(
                self.execution_receipt_sha256,
                name="execution_receipt_sha256",
            )
            campaign = _sha256(self.campaign_sha256, name="campaign_sha256")
        elif self.classifier_sha256 is not None:
            raise ValueError("test-only evaluation cannot claim classifier custody")
        elif self.execution_receipt_sha256 is not None:
            raise ValueError("test-only evaluation cannot claim execution custody")
        elif self.campaign_sha256 is not None:
            raise ValueError("test-only evaluation cannot claim campaign custody")
        else:
            classifier = None
            receipt = None
            campaign = None
        nested_types = (
            ("masked_excess_bce", MaskedExcessBCEDiagnostics),
            ("centered_log_information", CenteredLogInformationDiagnostics),
            ("residual", ResidualDiagnostics),
            ("edge_log_rates", EdgeLogRateDiagnostics),
            ("conditional_initial_tv", ConditionalInitialTVDiagnostics),
            ("calibration", CalibrationDiagnostics),
            ("coherence", CoherenceDiagnostics),
        )
        for name, expected_type in nested_types:
            if type(getattr(self, name)) is not expected_type:
                raise TypeError("%s must be an exact diagnostic record" % name)
        expected = (
            _FROZEN_TIME_COUNT,
            _FROZEN_STATE_COUNT,
            _FROZEN_OBSERVATION_COUNT,
        )
        for name in (
            "classifier_logit_grid",
            "log_information_grid",
            "residual_log_grid",
        ):
            value = np.asarray(getattr(self, name), dtype=np.float64)
            if value.shape != expected or not np.all(np.isfinite(value)):
                raise ValueError("%s is not a finite frozen grid" % name)
            object.__setattr__(self, name, _immutable_float_array(value))
        object.__setattr__(self, "parameter_sha256", parameter)
        object.__setattr__(self, "feature_sha256", feature)
        object.__setattr__(self, "classifier_sha256", classifier)
        object.__setattr__(self, "execution_receipt_sha256", receipt)
        object.__setattr__(self, "campaign_sha256", campaign)


def _validate_fixture(
    fixture: FrozenAssociationResidualFixture,
) -> None:
    if type(fixture) is not FrozenAssociationResidualFixture:
        raise TypeError("fixture must be a FrozenAssociationResidualFixture")
    expected_times = np.arange(_FROZEN_TIME_COUNT, dtype=np.float64) / 32.0
    if not np.array_equal(fixture.times, expected_times):
        raise ValueError("fixture must use the exact 33 frozen dyadic knots")
    if (
        fixture.latent_space.n_states != _FROZEN_STATE_COUNT
        or fixture.observation.n_observations != _FROZEN_OBSERVATION_COUNT
        or fixture.observation.overflow_index != _FROZEN_OBSERVATION_COUNT - 1
    ):
        raise ValueError("fixture state/observation universe is not frozen A1")
    if fixture.oracle.active_transition_families != _FAMILY_ORDER:
        raise ValueError("fixture must contain all three frozen edit families")


def _masked_diagnostics(
    fixture: FrozenAssociationResidualFixture,
    splits: FrozenAssociationResidualSplits,
    logits: np.ndarray,
) -> MaskedExcessBCEDiagnostics:
    population = fixture.population

    def score(times: np.ndarray, pairs: np.ndarray) -> float:
        return normalized_masked_excess_bce(
            population.joint_mass,
            population.product_mass,
            logits,
            population.optimal_log_density_ratio,
            times,
            pairs,
        )

    latent = score(splits.test_times, splits.latent_three_pairs)
    anchor = score(splits.test_times, splits.anchor_three_pairs)
    both = score(splits.test_times, splits.both_three_pairs)
    overflow = score(splits.test_times, splits.overflow_pairs)
    return MaskedExcessBCEDiagnostics(
        train=score(splits.train_times, splits.train_pairs),
        validation=score(splits.validation_times, splits.validation_pairs),
        joint_interpolation=score(splits.test_times, splits.test_pairs),
        time_interpolation=score(splits.test_times, splits.train_pairs),
        pair_interpolation=score(splits.train_times, splits.test_pairs),
        latent_three=latent,
        anchor_three=anchor,
        both_three=both,
        overflow=overflow,
        balanced_ood=(latent + anchor + both + overflow) / 4.0,
    )


def _centered_information_diagnostics(
    error: np.ndarray, weights: np.ndarray
) -> CenteredLogInformationDiagnostics:
    centered = np.empty_like(error)
    for time_index in range(error.shape[0]):
        for observation_index in range(error.shape[2]):
            cell_weights = weights[time_index, :, observation_index]
            denominator = math.fsum(float(value) for value in cell_weights)
            if denominator <= 0.0:
                raise ArithmeticError("centered information cell has zero mass")
            mean = math.fsum(
                float(weight * value)
                for weight, value in zip(
                    cell_weights, error[time_index, :, observation_index]
                )
            ) / denominator
            centered[time_index, :, observation_index] = (
                error[time_index, :, observation_index] - mean
            )
    denominator = math.fsum(float(value) for value in weights.flat)
    square = math.fsum(
        float(weight * value * value)
        for weight, value in zip(weights.flat, centered.flat)
    )
    return CenteredLogInformationDiagnostics(
        physical_weighted_rmse=math.sqrt(square / denominator),
        maximum_absolute_error=float(np.max(np.abs(centered))),
    )


def _residual_diagnostics(
    candidate: np.ndarray,
    oracle: np.ndarray,
    weights: np.ndarray,
) -> ResidualDiagnostics:
    error = candidate - oracle
    denominator = math.fsum(float(value) for value in weights.flat)
    square = math.fsum(
        float(weight * value * value)
        for weight, value in zip(weights.flat, error.flat)
    )
    candidate_min = float(np.min(candidate))
    candidate_max = float(np.max(candidate))
    oracle_min = float(np.min(oracle))
    oracle_max = float(np.max(oracle))
    return ResidualDiagnostics(
        physical_weighted_rmse=math.sqrt(square / denominator),
        maximum_absolute_error=float(np.max(np.abs(error))),
        candidate_minimum=candidate_min,
        candidate_maximum=candidate_max,
        candidate_range=candidate_max - candidate_min,
        oracle_minimum=oracle_min,
        oracle_maximum=oracle_max,
        oracle_range=oracle_max - oracle_min,
    )


def _edge_diagnostics(
    fixture: FrozenAssociationResidualFixture,
    candidate_log_information: np.ndarray,
    exact_log_information: np.ndarray,
) -> EdgeLogRateDiagnostics:
    generator = fixture.oracle.generator
    state_values = fixture.latent_space.states
    family_values = {family: ([], []) for family in _FAMILY_ORDER}
    for source in range(_FROZEN_STATE_COUNT):
        for destination in range(_FROZEN_STATE_COUNT):
            base_rate = float(generator[source, destination])
            if source == destination or base_rate <= 0.0:
                continue
            family = fixture.oracle.transition_family(
                state_values[source], state_values[destination]
            )
            if family not in family_values:
                raise ArithmeticError("active generator edge has no frozen family")
            exact_tilt = (
                exact_log_information[:-1, destination, :]
                - exact_log_information[:-1, source, :]
            )
            candidate_tilt = (
                candidate_log_information[:-1, destination, :]
                - candidate_log_information[:-1, source, :]
            )
            errors = candidate_tilt - exact_tilt
            exact_rates = base_rate * np.exp(exact_tilt)
            weights = (
                fixture.population.joint_mass[:-1, source, :] * exact_rates
            ) / float(_FROZEN_TIME_COUNT - 1)
            family_values[family][0].append(errors.reshape(-1))
            family_values[family][1].append(weights.reshape(-1))

    results = {}
    for family in _FAMILY_ORDER:
        error_parts, weight_parts = family_values[family]
        if not error_parts:
            raise ArithmeticError("frozen edit family has no active edges")
        errors = np.concatenate(error_parts)
        weights = np.concatenate(weight_parts)
        total = math.fsum(float(value) for value in weights)
        if total <= 0.0 or not math.isfinite(total):
            raise ArithmeticError("edit-family physical weight is invalid")
        square = math.fsum(
            float(weight * error * error)
            for weight, error in zip(weights, errors)
        )
        results[family] = EdgeFamilyDiagnostics(
            family=family,
            active_edge_count=len(error_parts),
            physical_weight=total,
            physical_weighted_rmse=math.sqrt(square / total),
            maximum_absolute_error=float(np.max(np.abs(errors))),
            weighted_median_absolute_error=deterministic_weighted_median(
                np.abs(errors), weights
            ),
        )
    return EdgeLogRateDiagnostics(
        birth=results["birth"],
        death=results["death"],
        replacement=results["replacement"],
    )


def _conditional_initial_tv(
    fixture: FrozenAssociationResidualFixture,
    candidate_log_information: np.ndarray,
) -> ConditionalInitialTVDiagnostics:
    unnormalized = fixture.initial_marginal[:, None] * np.exp(
        candidate_log_information[0]
    )
    evidence = np.sum(unnormalized, axis=0)
    if np.any(evidence <= 0.0) or not np.all(np.isfinite(evidence)):
        raise ArithmeticError("candidate conditional-initial evidence is invalid")
    candidate = unnormalized / evidence[None, :]
    per_observation = 0.5 * np.sum(
        np.abs(candidate - fixture.population.conditional_initial), axis=0
    )
    mass = fixture.population.observation_marginal_mass
    overflow = fixture.observation.overflow_index
    retained_mass = float(np.sum(mass[:overflow]))
    if retained_mass <= 0.0:
        raise ArithmeticError("retained observation mass is zero")
    return ConditionalInitialTVDiagnostics(
        per_observation=per_observation,
        observation_weighted_mean=float(np.dot(mass, per_observation)),
        retained_observation_weighted_mean=float(
            np.dot(mass[:overflow], per_observation[:overflow]) / retained_mass
        ),
        maximum=float(np.max(per_observation)),
        overflow=float(per_observation[overflow]),
    )


def _sigmoid(values: np.ndarray) -> np.ndarray:
    result = np.empty_like(values)
    positive = values >= 0.0
    result[positive] = 1.0 / (1.0 + np.exp(-values[positive]))
    exponential = np.exp(values[~positive])
    result[~positive] = exponential / (1.0 + exponential)
    return result


def _calibration_diagnostics(
    fixture: FrozenAssociationResidualFixture, logits: np.ndarray
) -> CalibrationDiagnostics:
    joint = fixture.population.joint_mass
    product = fixture.population.product_mass
    candidate = _sigmoid(logits)
    truth = joint / (joint + product)
    mixture = 0.5 * (joint + product)
    denominator = math.fsum(float(value) for value in mixture.flat)
    brier = math.fsum(
        float(
            0.5
            * (
                positive * (1.0 - probability) ** 2
                + negative * probability**2
            )
        )
        for positive, negative, probability in zip(
            joint.flat, product.flat, candidate.flat
        )
    ) / denominator
    optimal = math.fsum(
        float(
            0.5
            * (
                positive * (1.0 - probability) ** 2
                + negative * probability**2
            )
        )
        for positive, negative, probability in zip(
            joint.flat, product.flat, truth.flat
        )
    ) / denominator

    indices = np.minimum(
        (candidate * _RELIABILITY_BIN_COUNT).astype(np.int64),
        _RELIABILITY_BIN_COUNT - 1,
    )
    bin_mass = np.zeros(_RELIABILITY_BIN_COUNT, dtype=np.float64)
    bin_prediction = np.zeros(_RELIABILITY_BIN_COUNT, dtype=np.float64)
    bin_truth = np.zeros(_RELIABILITY_BIN_COUNT, dtype=np.float64)
    for index in range(_RELIABILITY_BIN_COUNT):
        mask = indices == index
        mass = math.fsum(float(value) for value in mixture[mask])
        bin_mass[index] = mass
        if mass > 0.0:
            bin_prediction[index] = math.fsum(
                float(weight * probability)
                for weight, probability in zip(mixture[mask], candidate[mask])
            ) / mass
            bin_truth[index] = math.fsum(
                float(weight * probability)
                for weight, probability in zip(mixture[mask], truth[mask])
            ) / mass
    gaps = np.abs(bin_prediction - bin_truth)
    occupied = bin_mass > 0.0
    ece = math.fsum(
        float(bin_mass[index] * gaps[index])
        for index in range(_RELIABILITY_BIN_COUNT)
    ) / denominator
    maximum_gap = float(np.max(gaps[occupied])) if np.any(occupied) else 0.0
    excess = brier - optimal
    tolerance = 64.0 * np.finfo(np.float64).eps * max(1.0, brier, optimal)
    if excess < -tolerance:
        raise ArithmeticError("candidate Brier score is below its exact optimum")
    return CalibrationDiagnostics(
        brier=brier,
        optimal_brier=optimal,
        excess_brier=max(0.0, excess),
        reliability_ece=ece,
        maximum_reliability_gap=maximum_gap,
        bin_mass=bin_mass / denominator,
        bin_mean_prediction=bin_prediction,
        bin_positive_frequency=bin_truth,
    )


def _edit_cycle_residual(
    generator: np.ndarray, log_information: np.ndarray
) -> Tuple[float, int]:
    active = generator > 0.0
    maximum = 0.0
    count = 0
    for first in range(_FROZEN_STATE_COUNT):
        for second in range(first + 1, _FROZEN_STATE_COUNT):
            if active[first, second] and active[second, first]:
                forward = log_information[:, second, :] - log_information[:, first, :]
                backward = log_information[:, first, :] - log_information[:, second, :]
                maximum = max(maximum, float(np.max(np.abs(forward + backward))))
                count += log_information.shape[0] * log_information.shape[2]
            for third in range(second + 1, _FROZEN_STATE_COUNT):
                orientations = (
                    (first, second, third),
                    (first, third, second),
                )
                for source, middle, destination in orientations:
                    if not (
                        active[source, middle]
                        and active[middle, destination]
                        and active[destination, source]
                    ):
                        continue
                    circulation = (
                        log_information[:, middle, :]
                        - log_information[:, source, :]
                        + log_information[:, destination, :]
                        - log_information[:, middle, :]
                        + log_information[:, source, :]
                        - log_information[:, destination, :]
                    )
                    maximum = max(
                        maximum, float(np.max(np.abs(circulation)))
                    )
                    count += log_information.shape[0] * log_information.shape[2]
    if count == 0:
        raise ArithmeticError("no edit cycles were found in the frozen generator")
    return maximum, count


def _coherence_diagnostics(
    fixture: FrozenAssociationResidualFixture,
    log_information: np.ndarray,
) -> CoherenceDiagnostics:
    information = np.exp(log_information)
    reference = fixture.observation.reference_mass
    normalization = information @ reference - 1.0
    normalization_weights = fixture.population.time_marginal
    normalization_denominator = math.fsum(
        float(value) for value in normalization_weights.flat
    )
    normalization_square = math.fsum(
        float(weight * residual * residual)
        for weight, residual in zip(
            normalization_weights.flat, normalization.flat
        )
    )

    semigroup_errors = []
    semigroup_weights = []
    for index in range(_FROZEN_TIME_COUNT - 1):
        elapsed = float(fixture.times[index + 1] - fixture.times[index])
        propagated = fixture.oracle.forward_transition(elapsed) @ information[index + 1]
        residual = information[index] - propagated
        weights = (
            fixture.population.time_marginal[index, :, None]
            * reference[None, :]
        )
        semigroup_errors.append(residual.reshape(-1))
        semigroup_weights.append(weights.reshape(-1))
    semigroup_error = np.concatenate(semigroup_errors)
    semigroup_weight = np.concatenate(semigroup_weights)
    semigroup_denominator = math.fsum(float(value) for value in semigroup_weight)
    semigroup_square = math.fsum(
        float(weight * residual * residual)
        for weight, residual in zip(semigroup_weight, semigroup_error)
    )
    cycle_maximum, cycle_count = _edit_cycle_residual(
        fixture.oracle.generator, log_information
    )
    terminal_exact = np.log(fixture.observation.density_kernel)
    return CoherenceDiagnostics(
        terminal_maximum_absolute_log_information_error=float(
            np.max(np.abs(log_information[-1] - terminal_exact))
        ),
        terminal_maximum_absolute_residual=float(
            np.max(
                np.abs(
                    log_information[-1]
                    - np.log(fixture.guide_density_grid[-1])
                )
            )
        ),
        generator_row_sum_maximum_absolute_residual=float(
            np.max(np.abs(fixture.oracle.generator.sum(axis=1)))
        ),
        normalization_physical_weighted_rmse=math.sqrt(
            normalization_square / normalization_denominator
        ),
        normalization_maximum_absolute_residual=float(
            np.max(np.abs(normalization))
        ),
        semigroup_physical_weighted_rmse=math.sqrt(
            semigroup_square / semigroup_denominator
        ),
        semigroup_maximum_absolute_residual=float(
            np.max(np.abs(semigroup_error))
        ),
        edit_cycle_maximum_absolute_residual=cycle_maximum,
        edit_cycle_count=cycle_count,
    )


def evaluate_finite_association_nonpath(
    evaluator: CertifiedFiniteAssociationLogitEvaluator,
    fixture: FrozenAssociationResidualFixture,
    splits: Optional[FrozenAssociationResidualSplits] = None,
) -> FiniteAssociationNonPathEvaluation:
    """Compute the frozen 33-knot diagnostics without training or paths."""

    if type(evaluator) is not CertifiedFiniteAssociationLogitEvaluator:
        raise TypeError(
            "evaluator must be a CertifiedFiniteAssociationLogitEvaluator"
        )
    _validate_fixture(fixture)
    if splits is None:
        checked_splits = frozen_association_residual_splits(fixture)
    elif type(splits) is FrozenAssociationResidualSplits:
        expected = frozen_association_residual_splits(fixture)
        if splits.digest != expected.digest:
            raise ValueError("splits do not match the frozen A1 partition")
        checked_splits = splits
    else:
        raise TypeError("splits must be FrozenAssociationResidualSplits or None")
    actual_fixture_sha256 = frozen_association_fixture_sha256(
        frozen_association_fixture_content_digests(fixture, checked_splits)
    )
    if (
        evaluator.certification.frozen_fixture_sha256
        != actual_fixture_sha256
    ):
        raise ValueError(
            "continuous certificate is not bound to the supplied A1 fixture"
        )

    evaluator.assert_integrity()
    try:
        logits = evaluator(fixture.times)
    finally:
        # Production custody is re-opened from the canonical campaign even
        # when the classifier callback raises or returns an invalid grid.
        evaluator.assert_integrity()
    population = fixture.population
    log_information = logits + np.log(
        population.observation_marginal_density
    )[None, None, :]
    if float(np.max(np.abs(log_information))) >= _PHYSICAL_LOG_INFORMATION_LIMIT:
        raise ValueError("candidate physical log information must remain below 24")
    exact_log_information = np.log(population.backward_information_density)
    guide_log_information = np.log(fixture.guide_density_grid)
    residual = log_information - guide_log_information
    error = log_information - exact_log_information
    weights = population.joint_mass

    result = FiniteAssociationNonPathEvaluation(
        parameter_sha256=evaluator.certification.parameter_sha256,
        feature_sha256=evaluator.certification.feature_sha256,
        classifier_sha256=evaluator.classifier_sha256,
        execution_receipt_sha256=evaluator.execution_receipt_sha256,
        campaign_sha256=evaluator.campaign_sha256,
        production_bound=evaluator.production_bound,
        classifier_logit_grid=logits,
        log_information_grid=log_information,
        residual_log_grid=residual,
        masked_excess_bce=_masked_diagnostics(
            fixture, checked_splits, logits
        ),
        centered_log_information=_centered_information_diagnostics(
            error, weights
        ),
        residual=_residual_diagnostics(
            residual, fixture.exact_residual_grid, weights
        ),
        edge_log_rates=_edge_diagnostics(
            fixture, log_information, exact_log_information
        ),
        conditional_initial_tv=_conditional_initial_tv(
            fixture, log_information
        ),
        calibration=_calibration_diagnostics(fixture, logits),
        coherence=_coherence_diagnostics(fixture, log_information),
    )
    evaluator.assert_integrity()
    return result


class CertifiedFiniteAssociationPotentialAdapter:
    """Positive one-observation potential scaffold for later path integration.

    Constructing or calling this adapter performs no propagation and computes
    no path metric.  It only converts the certified classifier gauge back to
    one physical potential vector at an arbitrary direct time.
    """

    def __init__(
        self,
        evaluator: CertifiedFiniteAssociationLogitEvaluator,
        fixture: FrozenAssociationResidualFixture,
        observation_index: object,
    ) -> None:
        if type(evaluator) is not CertifiedFiniteAssociationLogitEvaluator:
            raise TypeError("evaluator must be certificate-bound")
        _validate_fixture(fixture)
        actual_fixture_sha256 = frozen_association_fixture_sha256(
            frozen_association_fixture_content_digests(fixture)
        )
        if (
            evaluator.certification.frozen_fixture_sha256
            != actual_fixture_sha256
        ):
            raise ValueError(
                "continuous certificate is not bound to the supplied A1 fixture"
            )
        index = _integer_scalar(observation_index, name="observation_index")
        if index < 0 or index >= _FROZEN_OBSERVATION_COUNT:
            raise IndexError("observation_index is out of range")
        self._evaluator = evaluator
        self._fixture = fixture
        self._observation_index = index
        terminal = self.log_potential_vector(1.0)
        exact_terminal = fixture.observation.log_density_kernel[:, index]
        if float(np.max(np.abs(terminal - exact_terminal))) > 1.0e-10:
            raise ValueError(
                "candidate potential fails the frozen terminal boundary"
            )

    @property
    def observation_index(self) -> int:
        return self._observation_index

    @property
    def parameter_sha256(self) -> str:
        return self._evaluator.certification.parameter_sha256

    def log_potential_vector(self, direct_time: object) -> np.ndarray:
        time = _real_scalar(direct_time, name="direct_time")
        if time < 0.0 or time > 1.0:
            raise ValueError("direct_time must lie in [0, 1]")
        logits = self._evaluator(np.asarray((time,), dtype=np.float64))[0]
        result = logits[:, self._observation_index] + math.log(
            float(
                self._fixture.population.observation_marginal_density[
                    self._observation_index
                ]
            )
        )
        if float(np.max(np.abs(result))) >= _PHYSICAL_LOG_INFORMATION_LIMIT:
            raise ValueError("candidate physical log information must remain below 24")
        return _immutable_float_array(result)

    def __call__(self, direct_time: object) -> np.ndarray:
        result = np.exp(self.log_potential_vector(direct_time))
        if np.any(result <= 0.0) or not np.all(np.isfinite(result)):
            raise ArithmeticError("candidate potential is not positive and finite")
        return _immutable_float_array(result)


__all__ = [
    "CalibrationDiagnostics",
    "CenteredLogInformationDiagnostics",
    "CertifiedFiniteAssociationLogitEvaluator",
    "CertifiedFiniteAssociationPotentialAdapter",
    "CoherenceDiagnostics",
    "ConditionalInitialTVDiagnostics",
    "EdgeFamilyDiagnostics",
    "EdgeLogRateDiagnostics",
    "FiniteAssociationLogitCertification",
    "FiniteAssociationNonPathEvaluation",
    "MaskedExcessBCEDiagnostics",
    "ResidualDiagnostics",
    "bind_test_only_finite_association_logit_evaluator",
    "evaluate_finite_association_nonpath",
]
