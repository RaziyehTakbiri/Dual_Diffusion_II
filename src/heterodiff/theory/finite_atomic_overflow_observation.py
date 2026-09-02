"""Positive unordered observations with one explicit overflow outcome.

This module supplies the finite observation boundary for the frozen A1
association-guide experiment.  Ordinary outcomes are unlabelled anchor-count
vectors in a :class:`FiniteAtomicCountingSpace`; one distinct final outcome
collects every larger count vector.  Retained probabilities are coefficients
of the *unconditioned* source-detection plus Poisson-clutter probability
generating function.  In particular, they are never divided by the probability
of remaining below the observation cap.

The clean association law may contain structural zeros.  Strict positivity is
introduced only by a whole-observation mixture with a declared positive finite
reference law.  This is a bounded exact oracle, not a scalable association
algorithm.
"""

from __future__ import annotations

from enum import Enum
import math
from numbers import Integral, Real
from typing import Mapping, Optional, Tuple, Union

import numpy as np

from .finite_atomic_counting import AtomicCountVector, FiniteAtomicCountingSpace


_MAX_KERNEL_WORK = 20_000_000
_MAX_TOTAL_CLUTTER_RATE = 10_000.0
_NORMALIZATION_ATOL = 5.0e-13


class OverflowObservation(Enum):
    """Singleton type for the observation tail beyond the retained cap."""

    OVERFLOW = "overflow"


OVERFLOW_OBSERVATION = OverflowObservation.OVERFLOW
FiniteAtomicObservationValue = Union[AtomicCountVector, OverflowObservation]


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    contiguous = np.array(array, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=np.float64
    ).reshape(contiguous.shape)


def _as_float_array(
    value: object,
    *,
    name: str,
    shape: Tuple[int, ...],
) -> np.ndarray:
    try:
        raw = np.asarray(value)
        object_view = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s must be a rectangular numeric array" % name) from error
    if any(isinstance(item, (bool, np.bool_)) for item in object_view.flat):
        raise TypeError("%s must not contain boolean entries" % name)
    if raw.dtype.kind == "b":
        raise TypeError("%s must not have boolean dtype" % name)
    if raw.dtype.kind not in "iuf":
        raise TypeError("%s must have a real numeric dtype" % name)
    try:
        array = raw.astype(np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s cannot be represented as float64" % name) from error
    if array.shape != shape:
        raise ValueError("%s must have shape %r" % (name, shape))
    if not np.all(np.isfinite(array)):
        raise ValueError("%s entries must be finite" % name)
    return array


def _open_probability(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result) or not 0.0 < result < 1.0:
        raise ValueError("%s must lie strictly between zero and one" % name)
    return result


def _logaddexp(first: float, second: float) -> float:
    if first == -math.inf:
        return second
    if second == -math.inf:
        return first
    maximum = max(first, second)
    return maximum + math.log1p(math.exp(-abs(first - second)))


def _logsumexp(values: Tuple[float, ...]) -> float:
    if not values:
        return -math.inf
    maximum = max(values)
    if maximum == -math.inf:
        return -math.inf
    total = math.fsum(math.exp(value - maximum) for value in values)
    result = maximum + math.log(total)
    if not math.isfinite(result):
        raise ArithmeticError("association log-sum-exp is not representable")
    return result


def _log_nonnegative(value: float) -> float:
    return -math.inf if value == 0.0 else math.log(value)


def _poisson_log_mass(count: int, mean: float) -> float:
    if mean == 0.0:
        return 0.0 if count == 0 else -math.inf
    return count * math.log(mean) - mean - math.lgamma(count + 1.0)


class PositiveFiniteAtomicOverflowObservation:
    """Finite positive observation kernel with an explicit overflow column.

    Parameters
    ----------
    latent_space:
        Capped source-count space indexing rows.
    retained_observation_space:
        Capped anchor-count space indexing the ordinary columns.  Overflow is
        appended as the final column and is not a count vector in this space.
    detection_probability:
        Per-source probability of emitting one anchor.  Values in ``[0, 1]``
        are allowed; clean structural zeros remain exact.
    confusion_matrix:
        Row-source, column-anchor conditional emission probabilities.
    observation_clutter_rates:
        Independent Poisson rates for anchor clutter.  The resulting
        unbounded cardinality is collapsed into the explicit overflow column.
    contamination_probability:
        Probability of replacing the complete clean observation by one draw
        from ``reference_mass``.
    reference_mass:
        Strictly positive normalized mass on ordinary outcomes followed by
        overflow.  ``None`` selects the uniform law.
    """

    def __init__(
        self,
        latent_space: FiniteAtomicCountingSpace,
        retained_observation_space: FiniteAtomicCountingSpace,
        detection_probability: object,
        confusion_matrix: object,
        observation_clutter_rates: object,
        contamination_probability: object,
        *,
        reference_mass: Optional[object] = None,
    ) -> None:
        if not isinstance(latent_space, FiniteAtomicCountingSpace):
            raise TypeError("latent_space must be a FiniteAtomicCountingSpace")
        if not isinstance(retained_observation_space, FiniteAtomicCountingSpace):
            raise TypeError(
                "retained_observation_space must be a FiniteAtomicCountingSpace"
            )

        source_count = latent_space.atom_count
        anchor_count = retained_observation_space.atom_count
        detection = _as_float_array(
            detection_probability,
            name="detection_probability",
            shape=(source_count,),
        )
        if np.any(detection < 0.0) or np.any(detection > 1.0):
            raise ValueError("detection probabilities must lie in [0, 1]")
        confusion = _as_float_array(
            confusion_matrix,
            name="confusion_matrix",
            shape=(source_count, anchor_count),
        )
        if np.any(confusion < 0.0):
            raise ValueError("confusion probabilities must be nonnegative")
        if not np.allclose(
            confusion.sum(axis=1), 1.0, atol=1.0e-12, rtol=0.0
        ):
            raise ValueError("confusion_matrix rows must sum to one")
        confusion /= confusion.sum(axis=1, keepdims=True)

        clutter = _as_float_array(
            observation_clutter_rates,
            name="observation_clutter_rates",
            shape=(anchor_count,),
        )
        if np.any(clutter < 0.0):
            raise ValueError("observation clutter rates must be nonnegative")
        try:
            clutter_total = math.fsum(float(value) for value in clutter)
        except OverflowError as error:
            raise ValueError(
                "total observation clutter rate is not representable"
            ) from error
        if (
            not math.isfinite(clutter_total)
            or clutter_total > _MAX_TOTAL_CLUTTER_RATE
        ):
            raise ValueError(
                "total observation clutter rate must not exceed %g"
                % _MAX_TOTAL_CLUTTER_RATE
            )
        epsilon = _open_probability(
            contamination_probability, name="contamination_probability"
        )

        ordinary_count = retained_observation_space.n_states
        observation_count = ordinary_count + 1
        if reference_mass is None:
            reference = np.full(
                observation_count, 1.0 / observation_count, dtype=np.float64
            )
        else:
            reference = _as_float_array(
                reference_mass,
                name="reference_mass",
                shape=(observation_count,),
            )
            if np.any(reference <= 0.0):
                raise ValueError("reference_mass entries must be strictly positive")
            try:
                total = math.fsum(float(value) for value in reference)
            except OverflowError as error:
                raise ValueError("reference_mass sum is not representable") from error
            if not math.isclose(
                total, 1.0, rel_tol=0.0, abs_tol=_NORMALIZATION_ATOL
            ):
                raise ValueError("reference_mass must sum to one")
            reference /= total

        work = (
            latent_space.n_states
            * max(1, latent_space.total_cap)
            * ordinary_count
            * (anchor_count + 1)
            + latent_space.n_states
            * ordinary_count
            * ordinary_count
            * max(1, anchor_count)
        )
        if work > _MAX_KERNEL_WORK:
            raise ValueError(
                "observation kernel exceeds the enumerable work limit of %d"
                % _MAX_KERNEL_WORK
            )

        self._latent_space = latent_space
        self._retained_observation_space = retained_observation_space
        self._observations = tuple(retained_observation_space.states) + (
            OVERFLOW_OBSERVATION,
        )
        self._detection_probability = _immutable_float_array(detection)
        self._confusion_matrix = _immutable_float_array(confusion)
        self._observation_clutter_rates = _immutable_float_array(clutter)
        self._reference_mass = _immutable_float_array(reference)
        self._contamination_probability = epsilon
        self._clutter_total = clutter_total

        clean = np.empty(
            (latent_space.n_states, observation_count), dtype=np.float64
        )
        for latent_index, latent_counts in enumerate(latent_space.states):
            clean[latent_index] = self._clean_mass_row(latent_counts)
        if np.any(clean < 0.0) or not np.all(np.isfinite(clean)):
            raise ArithmeticError("clean observation kernel is not finite and nonnegative")
        if not np.allclose(
            clean.sum(axis=1), 1.0, atol=_NORMALIZATION_ATOL, rtol=0.0
        ):
            raise ArithmeticError("clean observation rows are not normalized")

        kernel = (1.0 - epsilon) * clean + epsilon * reference[None, :]
        density = kernel / reference[None, :]
        if np.any(kernel <= 0.0) or not np.all(np.isfinite(kernel)):
            raise ArithmeticError("contaminated observation mass is not positive")
        if not np.allclose(
            kernel.sum(axis=1), 1.0, atol=_NORMALIZATION_ATOL, rtol=0.0
        ):
            raise ArithmeticError("contaminated observation rows are not normalized")
        if np.any(density < epsilon - _NORMALIZATION_ATOL) or not np.all(
            np.isfinite(density)
        ):
            raise ArithmeticError("observation density violates its positive bound")
        if not np.allclose(
            np.sum(density * reference[None, :], axis=1),
            1.0,
            atol=_NORMALIZATION_ATOL,
            rtol=0.0,
        ):
            raise ArithmeticError(
                "observation density does not normalize under reference_mass"
            )

        self._clean_kernel_mass = _immutable_float_array(clean)
        self._kernel_mass = _immutable_float_array(kernel)
        self._density_kernel = _immutable_float_array(density)
        self._log_density_kernel = _immutable_float_array(np.log(density))

    @property
    def latent_space(self) -> FiniteAtomicCountingSpace:
        return self._latent_space

    @property
    def retained_observation_space(self) -> FiniteAtomicCountingSpace:
        return self._retained_observation_space

    @property
    def observations(self) -> Tuple[FiniteAtomicObservationValue, ...]:
        return self._observations

    @property
    def n_observations(self) -> int:
        return len(self._observations)

    @property
    def overflow_index(self) -> int:
        return self.n_observations - 1

    @property
    def detection_probability(self) -> np.ndarray:
        return self._detection_probability

    @property
    def confusion_matrix(self) -> np.ndarray:
        return self._confusion_matrix

    @property
    def observation_clutter_rates(self) -> np.ndarray:
        return self._observation_clutter_rates

    @property
    def reference_mass(self) -> np.ndarray:
        return self._reference_mass

    @property
    def contamination_probability(self) -> float:
        return self._contamination_probability

    @property
    def clean_kernel_mass(self) -> np.ndarray:
        return self._clean_kernel_mass

    @property
    def kernel_mass(self) -> np.ndarray:
        return self._kernel_mass

    @property
    def density_kernel(self) -> np.ndarray:
        return self._density_kernel

    @property
    def log_density_kernel(self) -> np.ndarray:
        return self._log_density_kernel

    @property
    def lower_bound(self) -> float:
        return float(np.min(self._density_kernel))

    @property
    def upper_bound(self) -> float:
        return float(np.max(self._density_kernel))

    def _source_log_distribution(
        self, latent_counts: AtomicCountVector
    ) -> Mapping[AtomicCountVector, float]:
        anchor_count = self._retained_observation_space.atom_count
        cap = self._retained_observation_space.total_cap
        zero = (0,) * anchor_count
        dynamic = {zero: 0.0}
        emission = (
            self._detection_probability[:, None] * self._confusion_matrix
        )
        miss = 1.0 - self._detection_probability
        for source, multiplicity in enumerate(latent_counts):
            log_miss = _log_nonnegative(float(miss[source]))
            log_emission = tuple(
                _log_nonnegative(float(value)) for value in emission[source]
            )
            for _ in range(multiplicity):
                updated = {}
                for partial, log_prefix in dynamic.items():
                    if log_miss != -math.inf:
                        updated[partial] = _logaddexp(
                            updated.get(partial, -math.inf),
                            log_prefix + log_miss,
                        )
                    if sum(partial) >= cap:
                        continue
                    for anchor, log_probability in enumerate(log_emission):
                        if log_probability == -math.inf:
                            continue
                        destination = list(partial)
                        destination[anchor] += 1
                        target = tuple(destination)
                        updated[target] = _logaddexp(
                            updated.get(target, -math.inf),
                            log_prefix + log_probability,
                        )
                dynamic = updated
        return dynamic

    def _clutter_log_mass(
        self, source_counts: AtomicCountVector, observed_counts: AtomicCountVector
    ) -> float:
        terms = [-self._clutter_total]
        for anchor, observed in enumerate(observed_counts):
            residual = observed - source_counts[anchor]
            if residual < 0:
                return -math.inf
            log_mass = _poisson_log_mass(
                residual, float(self._observation_clutter_rates[anchor])
            )
            if log_mass == -math.inf:
                return -math.inf
            # ``_poisson_log_mass`` already includes ``-mean``.  Replace the
            # shared total exponential by the count-dependent terms only.
            terms.append(log_mass + float(self._observation_clutter_rates[anchor]))
        return math.fsum(terms)

    def _clean_mass_row(self, latent_counts: AtomicCountVector) -> np.ndarray:
        source_distribution = self._source_log_distribution(latent_counts)
        ordinary_logs = []
        ordinary_mass = np.zeros(
            self._retained_observation_space.n_states, dtype=np.float64
        )
        for observed_index, observed_counts in enumerate(
            self._retained_observation_space.states
        ):
            terms = []
            for source_counts, source_log_mass in source_distribution.items():
                clutter_log_mass = self._clutter_log_mass(
                    source_counts, observed_counts
                )
                if clutter_log_mass != -math.inf:
                    terms.append(source_log_mass + clutter_log_mass)
            log_mass = _logsumexp(tuple(terms))
            ordinary_logs.append(log_mass)
            if log_mass != -math.inf:
                ordinary_mass[observed_index] = math.exp(log_mass)

        log_retained = _logsumexp(tuple(ordinary_logs))
        if log_retained == -math.inf:
            overflow = 1.0
        else:
            if log_retained > _NORMALIZATION_ATOL:
                raise ArithmeticError("retained clean observation mass exceeds one")
            overflow = -math.expm1(min(log_retained, 0.0))
        row_total = math.fsum(float(value) for value in ordinary_mass) + overflow
        if not math.isclose(
            row_total, 1.0, rel_tol=0.0, abs_tol=_NORMALIZATION_ATOL
        ):
            raise ArithmeticError("clean retained mass and overflow do not normalize")
        overflow += 1.0 - row_total
        if overflow < -_NORMALIZATION_ATOL or overflow > 1.0 + _NORMALIZATION_ATOL:
            raise ArithmeticError("clean overflow probability lies outside [0, 1]")
        if abs(overflow) <= _NORMALIZATION_ATOL:
            overflow = 0.0
        result = np.empty(self.n_observations, dtype=np.float64)
        result[:-1] = ordinary_mass
        result[-1] = overflow
        return result

    def index_of_observation(self, observation: object) -> int:
        if observation is OVERFLOW_OBSERVATION:
            return self.overflow_index
        if isinstance(observation, OverflowObservation):
            raise ValueError("unknown overflow observation value")
        return self._retained_observation_space.index_of(observation)  # type: ignore[arg-type]

    def observation_at(self, index: object) -> FiniteAtomicObservationValue:
        if isinstance(index, (bool, np.bool_)) or not isinstance(index, Integral):
            raise TypeError("observation index must be an integer non-boolean value")
        position = int(index)
        if position < 0 or position >= self.n_observations:
            raise IndexError("observation index is out of range")
        return self._observations[position]

    def mass_row(self, latent_counts: object) -> np.ndarray:
        index = self._latent_space.index_of(latent_counts)  # type: ignore[arg-type]
        return _immutable_float_array(self._kernel_mass[index])

    def density_row(self, latent_counts: object) -> np.ndarray:
        index = self._latent_space.index_of(latent_counts)  # type: ignore[arg-type]
        return _immutable_float_array(self._density_kernel[index])

    def likelihood(self, observation: object) -> np.ndarray:
        index = self.index_of_observation(observation)
        return _immutable_float_array(self._density_kernel[:, index])

    def probability(self, latent_counts: object, observation: object) -> float:
        latent_index = self._latent_space.index_of(latent_counts)  # type: ignore[arg-type]
        observed_index = self.index_of_observation(observation)
        return float(self._kernel_mass[latent_index, observed_index])

    def density(self, latent_counts: object, observation: object) -> float:
        latent_index = self._latent_space.index_of(latent_counts)  # type: ignore[arg-type]
        observed_index = self.index_of_observation(observation)
        return float(self._density_kernel[latent_index, observed_index])


__all__ = [
    "FiniteAtomicObservationValue",
    "OVERFLOW_OBSERVATION",
    "OverflowObservation",
    "PositiveFiniteAtomicOverflowObservation",
]
