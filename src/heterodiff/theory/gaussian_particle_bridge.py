"""Exact Brownian-particle bridge with noisy unordered terminal anchors.

This module is a classical small-state oracle, not a neural method or a
methodological novelty claim.  It is useful for checking association-aware
bridge code against a case in which every quantity can be evaluated exactly.

There are ``n`` temporarily indexed particles in ``R**d``.  From the current
time ``t`` they evolve independently according to

``d X_i(s) = sqrt(q) d W_i(s)``.

At terminal time ``T``, particle ``i`` is detected independently with
probability ``p[i]``.  A detected particle produces one anchor with isotropic
Gaussian variance ``r > 0``; an undetected particle produces none.  Anchors
are an unordered multiset and clutter is absent.  Consequently, an
observation with ``m`` anchors is marginalised over every injective map from
the anchors to the particles.

The unordered density is relative to the unnormalised finite-set
(Lebesgue--Poisson) reference ``(1 / m!) product_j dy_j``.  Under this
convention the injection sum has no additional factorial.

Exact enumeration is intentionally bounded.  Strictly positive measurement
noise is required.  Singular exact anchors and the ``r -> 0`` limit are out of
scope and must not be inferred from this implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
from numbers import Integral, Real
from typing import Iterator, Optional, Sequence, Tuple
import warnings

import numpy as np


_MAX_ASSIGNMENTS_HARD = 1_000_000
_DEFAULT_MAX_ASSIGNMENTS = 100_000
_MAX_PARTICLES = 128
_MAX_DIMENSION = 128
_MAX_FLAT_DIMENSION = 512
_MAX_COVARIANCE_WORK = 20_000_000
_MAX_SAMPLE_ENTRIES = 10_000_000
_MAX_SAMPLE_SIZE = 1_000_000
_MAX_SEED = int(np.iinfo(np.uint64).max)


class UnreachableParticleBridgeObservationError(ValueError):
    """Raised when the terminal anchor observation has exactly zero density."""

    def __init__(self) -> None:
        super().__init__(
            "the unordered terminal-anchor observation has zero density "
            "from the current particle state"
        )


@dataclass(frozen=True)
class AssociationHypothesis:
    """One normalised latent anchor-to-particle association hypothesis.

    ``assignment[j]`` is the particle index assigned to anchor ``j``.
    ``log_probability`` remains informative when ``probability`` underflows
    to zero in ordinary floating-point space.  No probability floor is used.
    """

    assignment: Tuple[int, ...]
    log_probability: float
    probability: float

    def __post_init__(self) -> None:
        if isinstance(self.assignment, (str, bytes)):
            raise TypeError("assignment must be a finite sequence of indices")
        try:
            assignment_length = len(self.assignment)
        except TypeError as error:
            raise TypeError("assignment must be a finite sequence of indices") from error
        if assignment_length > _MAX_PARTICLES:
            raise ValueError(
                "assignment exceeds the oracle particle limit of %d"
                % _MAX_PARTICLES
            )
        try:
            assignment = tuple(self.assignment)
        except TypeError as error:
            raise TypeError("assignment must be a finite sequence of indices") from error
        indices = []
        for value in assignment:
            if isinstance(value, (bool, np.bool_)) or not isinstance(
                value, Integral
            ):
                raise TypeError(
                    "assignment entries must be nonnegative integer indices"
                )
            index = int(value)
            if index < 0:
                raise ValueError("assignment indices must be nonnegative")
            indices.append(index)
        if len(set(indices)) != len(indices):
            raise ValueError("assignment indices must be unique")

        if isinstance(self.log_probability, (bool, np.bool_)) or not isinstance(
            self.log_probability, Real
        ):
            raise TypeError("log_probability must be a real non-boolean number")
        log_probability = float(self.log_probability)
        if math.isnan(log_probability) or log_probability == math.inf:
            raise ValueError("log_probability must be finite or -inf")
        if log_probability > 0.0:
            raise ValueError("log_probability must not be positive")

        if isinstance(self.probability, (bool, np.bool_)) or not isinstance(
            self.probability, Real
        ):
            raise TypeError("probability must be a real non-boolean number")
        probability = float(self.probability)
        if (
            not math.isfinite(probability)
            or probability < 0.0
            or probability > 1.0
        ):
            raise ValueError("probability must lie in [0, 1]")
        if log_probability == -math.inf:
            if probability != 0.0:
                raise ValueError("-inf log_probability requires zero probability")
        else:
            expected = math.exp(log_probability)
            if expected > 0.0 and not math.isclose(
                probability, expected, rel_tol=1.0e-12, abs_tol=0.0
            ):
                raise ValueError(
                    "probability is inconsistent with representable log_probability"
                )

        object.__setattr__(self, "assignment", tuple(indices))
        object.__setattr__(self, "log_probability", log_probability)
        object.__setattr__(self, "probability", probability)


@dataclass(frozen=True)
class GaussianMixtureMoments:
    """Full moments of a Gaussian mixture in flattened particle coordinates.

    The mean has shape ``(n*d,)`` and covariance has shape
    ``(n*d, n*d)``.  Defensive, bytes-backed read-only copies are stored so
    writeability cannot be re-enabled.  Covariances are symmetrised if their
    asymmetry is within a dimension-scaled floating-point tolerance and may
    have eigenvalues no smaller than the corresponding negative roundoff
    tolerance; materially asymmetric or indefinite inputs are rejected.
    """

    mean: np.ndarray
    covariance: np.ndarray

    def __post_init__(self) -> None:
        try:
            mean = np.array(self.mean, dtype=float, copy=True)
            covariance = np.array(self.covariance, dtype=float, copy=True)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("mixture moments must be rectangular numeric arrays") from error
        if mean.ndim != 1:
            raise ValueError("mean must be one-dimensional")
        if mean.size > _MAX_FLAT_DIMENSION:
            raise ValueError(
                "mean exceeds the oracle flattened-state limit of %d"
                % _MAX_FLAT_DIMENSION
            )
        if covariance.shape != (mean.size, mean.size):
            raise ValueError("covariance shape must match flattened mean size")
        if not np.all(np.isfinite(mean)) or not np.all(np.isfinite(covariance)):
            raise ValueError("mixture moments must be finite")
        if mean.size:
            scale = float(np.max(np.abs(covariance)))
            tolerance = (
                256.0
                * float(np.finfo(float).eps)
                * max(mean.size, 1)
                * scale
            )
            with np.errstate(over="ignore", invalid="ignore"):
                asymmetry = float(np.max(np.abs(covariance - covariance.T)))
            if asymmetry > tolerance:
                raise ValueError("covariance must be symmetric up to roundoff")
            covariance = 0.5 * covariance + 0.5 * covariance.T
            try:
                minimum_eigenvalue = float(np.linalg.eigvalsh(covariance)[0])
            except np.linalg.LinAlgError as error:
                raise ValueError("covariance eigendecomposition failed") from error
            if minimum_eigenvalue < -tolerance:
                raise ValueError("covariance must be positive semidefinite up to roundoff")
        mean_shape = mean.shape
        covariance_shape = covariance.shape
        immutable_mean = np.frombuffer(mean.tobytes(order="C"), dtype=np.float64)
        immutable_mean = immutable_mean.reshape(mean_shape)
        immutable_covariance = np.frombuffer(
            covariance.tobytes(order="C"), dtype=np.float64
        ).reshape(covariance_shape)
        object.__setattr__(self, "mean", immutable_mean)
        object.__setattr__(self, "covariance", immutable_covariance)


def _validate_positive_real(value: float, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError("%s must be finite and strictly positive" % name)
    return result


def _validate_nonnegative_time(value: float, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError("%s must be finite and nonnegative" % name)
    return result


def _validate_bound(value: int, name: str, hard_maximum: int) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result <= 0 or result > hard_maximum:
        raise ValueError(
            "%s must lie between one and %d" % (name, hard_maximum)
        )
    return result


def _validate_seed(seed: Optional[int]) -> Optional[int]:
    if seed is None:
        return None
    if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, Integral):
        raise TypeError("seed must be a nonnegative integer or None")
    result = int(seed)
    if result < 0 or result > _MAX_SEED:
        raise ValueError("seed must lie in the uint64 range")
    return result


def _validate_size(size: Optional[int]) -> Optional[int]:
    if size is None:
        return None
    if isinstance(size, (bool, np.bool_)) or not isinstance(size, Integral):
        raise TypeError("size must be a strictly positive integer or None")
    result = int(size)
    if result <= 0 or result > _MAX_SAMPLE_SIZE:
        raise ValueError(
            "size must lie between one and %d" % _MAX_SAMPLE_SIZE
        )
    return result


def _numeric_matrix(value: np.ndarray, name: str) -> np.ndarray:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            array = np.asarray(value)
    except (TypeError, ValueError, Warning) as error:
        raise ValueError("%s must be a rectangular numeric matrix" % name) from error
    if array.dtype.kind == "b":
        raise TypeError("%s must not have boolean dtype" % name)
    if array.dtype.kind not in "iuf":
        raise TypeError("%s must have a real numeric dtype" % name)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = array.astype(float, copy=True)
    except (TypeError, ValueError, OverflowError, Warning) as error:
        raise ValueError("%s could not be represented as a float matrix" % name) from error
    if result.ndim != 2:
        raise ValueError("%s must be a two-dimensional matrix" % name)
    if not np.all(np.isfinite(result)):
        raise ValueError("%s entries must be finite" % name)
    return result


def _detection_vector(value: np.ndarray, particle_count: int) -> np.ndarray:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            array = np.asarray(value)
    except (TypeError, ValueError, Warning) as error:
        raise ValueError(
            "detection_probability must be a rectangular numeric vector"
        ) from error
    if array.dtype.kind == "b":
        raise TypeError("detection_probability must not have boolean dtype")
    if array.dtype.kind not in "iuf":
        raise TypeError("detection_probability must have a real numeric dtype")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = array.astype(float, copy=True)
    except (TypeError, ValueError, OverflowError, Warning) as error:
        raise ValueError(
            "detection_probability could not be represented as floats"
        ) from error
    if result.ndim != 1 or result.shape[0] != particle_count:
        raise ValueError(
            "detection_probability must have shape (%d,)" % particle_count
        )
    if not np.all(np.isfinite(result)):
        raise ValueError("detection probabilities must be finite")
    if np.any(result < 0.0) or np.any(result > 1.0):
        raise ValueError("detection probabilities must lie in [0, 1]")
    return result


def _logsumexp(log_values: Sequence[float]) -> float:
    finite = [value for value in log_values if value != -math.inf]
    if not finite:
        return -math.inf
    maximum = max(finite)
    total = math.fsum(math.exp(value - maximum) for value in finite)
    result = maximum + math.log(total)
    if not math.isfinite(result):
        raise ArithmeticError("log information is outside floating-point range")
    return result


def _safe_positive_sum(first: float, second: float, name: str) -> float:
    """Add finite nonnegative scalars, rejecting unrepresentable overflow."""

    if first > float(np.finfo(float).max) - second:
        raise ArithmeticError("%s is outside floating-point range" % name)
    result = first + second
    if not math.isfinite(result) or result <= 0.0:
        raise ArithmeticError("%s is not representable" % name)
    return result


class BrownianParticleBridgeOracle:
    """Known-law bridge for independent Brownian particles and noisy anchors."""

    def __init__(
        self,
        diffusion_variance_rate: float,
        observation_variance: float,
        max_assignments: int = _DEFAULT_MAX_ASSIGNMENTS,
    ) -> None:
        self._diffusion_variance_rate = _validate_positive_real(
            diffusion_variance_rate, "diffusion_variance_rate"
        )
        self._observation_variance = _validate_positive_real(
            observation_variance, "observation_variance"
        )
        self._max_assignments = _validate_bound(
            max_assignments, "max_assignments", _MAX_ASSIGNMENTS_HARD
        )

    @property
    def diffusion_variance_rate(self) -> float:
        return self._diffusion_variance_rate

    @property
    def observation_variance(self) -> float:
        return self._observation_variance

    @property
    def max_assignments(self) -> int:
        return self._max_assignments

    @staticmethod
    def _validate_times(
        time: float,
        terminal_time: float,
        future_time: Optional[float] = None,
    ) -> Tuple[float, float, Optional[float]]:
        current = _validate_nonnegative_time(time, "time")
        terminal = _validate_nonnegative_time(terminal_time, "terminal_time")
        if current > terminal:
            raise ValueError("time must not exceed terminal_time")
        if future_time is None:
            return current, terminal, None
        future = _validate_nonnegative_time(future_time, "future_time")
        if future < current or future > terminal:
            raise ValueError(
                "future_time must lie between time and terminal_time"
            )
        return current, terminal, future

    @staticmethod
    def _validate_observation_inputs(
        current_positions: np.ndarray,
        anchors: np.ndarray,
        detection_probability: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        positions = _numeric_matrix(current_positions, "current_positions")
        observed = _numeric_matrix(anchors, "anchors")
        particle_count, dimension = positions.shape
        if dimension == 0:
            raise ValueError("particle dimension must be strictly positive")
        if observed.shape[1] != dimension:
            raise ValueError(
                "anchors must have the same coordinate dimension as particles"
            )
        if particle_count > _MAX_PARTICLES:
            raise ValueError(
                "particle count exceeds the oracle safety limit of %d"
                % _MAX_PARTICLES
            )
        if dimension > _MAX_DIMENSION:
            raise ValueError(
                "particle dimension exceeds the oracle safety limit of %d"
                % _MAX_DIMENSION
            )
        if particle_count * dimension > _MAX_FLAT_DIMENSION:
            raise ValueError(
                "flattened state exceeds the oracle safety limit of %d"
                % _MAX_FLAT_DIMENSION
            )
        detection = _detection_vector(detection_probability, particle_count)
        return positions, observed, detection

    def _variance_for_elapsed(self, elapsed: float) -> float:
        if elapsed == 0.0:
            return 0.0
        variance = self._diffusion_variance_rate * elapsed
        if not math.isfinite(variance) or variance == 0.0:
            raise ArithmeticError(
                "Brownian variance is not representable for the requested interval"
            )
        return variance

    def _predictive_variance(self, remaining_time: float) -> float:
        brownian_variance = self._variance_for_elapsed(remaining_time)
        return _safe_positive_sum(
            brownian_variance,
            self._observation_variance,
            "predictive variance",
        )

    def _assignment_count(self, particle_count: int, anchor_count: int) -> int:
        if anchor_count > particle_count:
            return 0
        count = 1
        for factor in range(particle_count - anchor_count + 1, particle_count + 1):
            count *= factor
            if count > self._max_assignments:
                raise ValueError(
                    "exact association count exceeds max_assignments=%d"
                    % self._max_assignments
                )
        return count

    def _assignments(
        self, particle_count: int, anchor_count: int
    ) -> Iterator[Tuple[int, ...]]:
        self._assignment_count(particle_count, anchor_count)
        return itertools.permutations(range(particle_count), anchor_count)

    @staticmethod
    def _gaussian_log_density(
        anchor: np.ndarray,
        position: np.ndarray,
        variance: float,
    ) -> float:
        with np.errstate(over="ignore", invalid="ignore"):
            residual = anchor - position
        if not np.all(np.isfinite(residual)):
            raise ArithmeticError("anchor residual is outside floating-point range")
        scale = math.sqrt(variance)
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            standardised = residual / scale
        if not np.all(np.isfinite(standardised)):
            raise ArithmeticError(
                "standardised anchor residual is outside floating-point range"
            )
        norm = math.hypot(*(float(value) for value in standardised))
        if not math.isfinite(norm) or norm > math.sqrt(float(np.finfo(float).max)):
            raise ArithmeticError(
                "Gaussian log likelihood is outside floating-point range"
            )
        quadratic = norm * norm
        log_density = (
            -0.5
            * anchor.size
            * (math.log(2.0 * math.pi) + math.log(variance))
            - 0.5 * quadratic
        )
        if not math.isfinite(log_density):
            raise ArithmeticError(
                "Gaussian log likelihood is outside floating-point range"
            )
        return log_density

    def _validated_log_weights(
        self,
        current_positions: np.ndarray,
        anchors: np.ndarray,
        detection_probability: np.ndarray,
        time: float,
        terminal_time: float,
    ) -> Tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        float,
        Tuple[Tuple[int, ...], ...],
        Tuple[float, ...],
    ]:
        positions, observed, detection = self._validate_observation_inputs(
            current_positions, anchors, detection_probability
        )
        current, terminal, _ = self._validate_times(time, terminal_time)
        anchor_count = observed.shape[0]
        particle_count = positions.shape[0]
        if anchor_count > particle_count:
            return positions, observed, detection, math.nan, tuple(), tuple()

        predictive_variance = (
            math.nan
            if anchor_count == 0
            else self._predictive_variance(terminal - current)
        )
        assignments = tuple(self._assignments(particle_count, anchor_count))
        log_weights = []
        for assignment in assignments:
            assigned = set(assignment)
            log_weight = 0.0
            possible = True
            for anchor_index, particle_index in enumerate(assignment):
                probability = detection[particle_index]
                if probability == 0.0:
                    possible = False
                    break
                log_weight += math.log(probability)
                log_weight += self._gaussian_log_density(
                    observed[anchor_index],
                    positions[particle_index],
                    predictive_variance,
                )
            if possible:
                for particle_index in range(particle_count):
                    if particle_index in assigned:
                        continue
                    probability = detection[particle_index]
                    if probability == 1.0:
                        possible = False
                        break
                    log_weight += math.log1p(-probability)
            log_weights.append(log_weight if possible else -math.inf)
        return (
            positions,
            observed,
            detection,
            predictive_variance,
            assignments,
            tuple(log_weights),
        )

    def log_information(
        self,
        current_positions: np.ndarray,
        anchors: np.ndarray,
        detection_probability: np.ndarray,
        time: float,
        terminal_time: float,
    ) -> float:
        """Return ``log h(t, x)`` for the unordered noisy-anchor evidence.

        Exact structural impossibility is returned as ``-inf``.  Positive
        Gaussian likelihoods are never converted through ordinary-space
        densities, so small evidence is retained in log space without an
        epsilon floor.
        """

        result = self._validated_log_weights(
            current_positions,
            anchors,
            detection_probability,
            time,
            terminal_time,
        )
        return _logsumexp(result[-1])

    def association_posterior(
        self,
        current_positions: np.ndarray,
        anchors: np.ndarray,
        detection_probability: np.ndarray,
        time: float,
        terminal_time: float,
    ) -> Tuple[AssociationHypothesis, ...]:
        """Return the exact normalised posterior over injective associations."""

        result = self._validated_log_weights(
            current_positions,
            anchors,
            detection_probability,
            time,
            terminal_time,
        )
        assignments, log_weights = result[-2], result[-1]
        log_information = _logsumexp(log_weights)
        if log_information == -math.inf:
            raise UnreachableParticleBridgeObservationError()

        log_probabilities = tuple(
            value - log_information if value != -math.inf else -math.inf
            for value in log_weights
        )
        probabilities = [
            math.exp(value) if value != -math.inf else 0.0
            for value in log_probabilities
        ]
        total = math.fsum(probabilities)
        if not math.isfinite(total) or total <= 0.0:
            raise ArithmeticError("association posterior could not be normalised")
        probabilities = [value / total for value in probabilities]
        return tuple(
            AssociationHypothesis(assignment, log_probability, probability)
            for assignment, log_probability, probability in zip(
                assignments, log_probabilities, probabilities
            )
        )

    def bridge_drift(
        self,
        current_positions: np.ndarray,
        anchors: np.ndarray,
        detection_probability: np.ndarray,
        time: float,
        terminal_time: float,
    ) -> np.ndarray:
        """Return the exact Doob drift ``q * grad_x log h(t, x)``.

        The result has the same ``(n, d)`` shape as ``current_positions``.
        """

        positions, observed, _, predictive_variance, _, _ = (
            self._validated_log_weights(
                current_positions,
                anchors,
                detection_probability,
                time,
                terminal_time,
            )
        )
        posterior = self.association_posterior(
            positions,
            observed,
            detection_probability,
            time,
            terminal_time,
        )
        gradient = np.zeros_like(positions)
        for hypothesis in posterior:
            if hypothesis.probability == 0.0:
                continue
            for anchor_index, particle_index in enumerate(hypothesis.assignment):
                with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                    contribution = hypothesis.probability * (
                        (observed[anchor_index] - positions[particle_index])
                        / predictive_variance
                    )
                    gradient[particle_index] += contribution
        with np.errstate(over="ignore", invalid="ignore"):
            drift = self._diffusion_variance_rate * gradient
        if not np.all(np.isfinite(drift)):
            raise ArithmeticError("bridge drift is outside floating-point range")
        return drift

    def _component_offset_and_variance(
        self,
        positions: np.ndarray,
        observed: np.ndarray,
        assignment: Tuple[int, ...],
        elapsed_to_future: float,
        remaining_to_terminal: float,
        predictive_variance: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        particle_count, dimension = positions.shape
        step_variance = self._variance_for_elapsed(elapsed_to_future)
        offset = np.zeros((particle_count, dimension), dtype=float)
        variance = np.full(
            particle_count * dimension, step_variance, dtype=float
        )
        if step_variance == 0.0 or not assignment:
            return offset.reshape(-1), variance

        remaining_variance = self._variance_for_elapsed(remaining_to_terminal)
        assigned_variance_numerator = _safe_positive_sum(
            remaining_variance,
            self._observation_variance,
            "conditional remaining variance",
        )
        assigned_variance = step_variance * (
            assigned_variance_numerator / predictive_variance
        )
        gain = step_variance / predictive_variance
        if (
            not math.isfinite(assigned_variance)
            or assigned_variance < 0.0
            or not math.isfinite(gain)
        ):
            raise ArithmeticError("conditional Gaussian moments are not representable")
        for anchor_index, particle_index in enumerate(assignment):
            with np.errstate(over="ignore", invalid="ignore"):
                offset[particle_index] = gain * (
                    observed[anchor_index] - positions[particle_index]
                )
            start = particle_index * dimension
            variance[start : start + dimension] = assigned_variance
        if not np.all(np.isfinite(offset)) or not np.all(np.isfinite(variance)):
            raise ArithmeticError("conditional Gaussian moments are not representable")
        return offset.reshape(-1), variance

    def finite_step_moments(
        self,
        current_positions: np.ndarray,
        anchors: np.ndarray,
        detection_probability: np.ndarray,
        time: float,
        future_time: float,
        terminal_time: float,
    ) -> GaussianMixtureMoments:
        """Return exact full moments at ``future_time`` under the bridge.

        Conditional on an association the step law is Gaussian.  This method
        applies the law of total covariance over the exact finite mixture,
        including cross-particle covariance induced by association ambiguity.
        """

        positions, observed, _, predictive_variance, _, _ = (
            self._validated_log_weights(
                current_positions,
                anchors,
                detection_probability,
                time,
                terminal_time,
            )
        )
        current, terminal, future = self._validate_times(
            time, terminal_time, future_time
        )
        assert future is not None
        posterior = self.association_posterior(
            positions,
            observed,
            detection_probability,
            current,
            terminal,
        )
        flat_dimension = positions.size
        if len(posterior) * max(flat_dimension * flat_dimension, 1) > (
            _MAX_COVARIANCE_WORK
        ):
            raise ValueError(
                "exact mixture covariance exceeds the oracle work limit"
            )

        elapsed = future - current
        remaining = terminal - future
        offsets = []
        variances = []
        weights = []
        for hypothesis in posterior:
            if hypothesis.probability == 0.0:
                continue
            offset, variance = self._component_offset_and_variance(
                positions,
                observed,
                hypothesis.assignment,
                elapsed,
                remaining,
                predictive_variance,
            )
            offsets.append(offset)
            variances.append(variance)
            weights.append(hypothesis.probability)

        weight_total = math.fsum(weights)
        if weight_total <= 0.0:
            raise ArithmeticError("positive mixture components were lost")
        weights = [weight / weight_total for weight in weights]
        with np.errstate(over="ignore", invalid="ignore"):
            mean_offset = np.zeros(flat_dimension, dtype=float)
            for weight, offset in zip(weights, offsets):
                mean_offset += weight * offset
            mean = positions.reshape(-1) + mean_offset
            covariance = np.zeros((flat_dimension, flat_dimension), dtype=float)
            diagonal_indices = np.diag_indices(flat_dimension)
            for weight, offset, variance in zip(weights, offsets, variances):
                difference = offset - mean_offset
                covariance += weight * np.outer(difference, difference)
                covariance[diagonal_indices] += weight * variance
            covariance = 0.5 * (covariance + covariance.T)
        if not np.all(np.isfinite(mean)) or not np.all(np.isfinite(covariance)):
            raise ArithmeticError("mixture moments are outside floating-point range")
        return GaussianMixtureMoments(mean, covariance)

    def terminal_moments(
        self,
        current_positions: np.ndarray,
        anchors: np.ndarray,
        detection_probability: np.ndarray,
        time: float,
        terminal_time: float,
    ) -> GaussianMixtureMoments:
        """Return exact flattened mean and covariance at terminal time."""

        return self.finite_step_moments(
            current_positions=current_positions,
            anchors=anchors,
            detection_probability=detection_probability,
            time=time,
            future_time=terminal_time,
            terminal_time=terminal_time,
        )

    def sample_conditional_step(
        self,
        current_positions: np.ndarray,
        anchors: np.ndarray,
        detection_probability: np.ndarray,
        time: float,
        future_time: float,
        terminal_time: float,
        seed: Optional[int] = None,
        size: Optional[int] = None,
    ) -> np.ndarray:
        """Sample the exact finite-step Gaussian mixture with a local RNG.

        With ``size=None`` the result has shape ``(n, d)``.  Otherwise it has
        shape ``(size, n, d)``.  The global NumPy random state is never used.
        """

        validated_seed = _validate_seed(seed)
        validated_size = _validate_size(size)
        positions, observed, _, predictive_variance, _, _ = (
            self._validated_log_weights(
                current_positions,
                anchors,
                detection_probability,
                time,
                terminal_time,
            )
        )
        current, terminal, future = self._validate_times(
            time, terminal_time, future_time
        )
        assert future is not None
        posterior = self.association_posterior(
            positions,
            observed,
            detection_probability,
            current,
            terminal,
        )
        draw_count = 1 if validated_size is None else validated_size
        flat_dimension = positions.size
        if draw_count * max(flat_dimension, 1) > _MAX_SAMPLE_ENTRIES:
            raise ValueError("requested samples exceed the oracle memory limit")

        probabilities = np.asarray(
            [hypothesis.probability for hypothesis in posterior], dtype=float
        )
        probabilities /= probabilities.sum()
        generator = np.random.default_rng(validated_seed)
        selected = generator.choice(
            len(posterior), size=draw_count, p=probabilities
        )
        base = positions.reshape(-1)
        samples = np.empty((draw_count, flat_dimension), dtype=float)
        elapsed = future - current
        remaining = terminal - future
        for component_index in np.unique(selected):
            offset, variance = self._component_offset_and_variance(
                positions,
                observed,
                posterior[int(component_index)].assignment,
                elapsed,
                remaining,
                predictive_variance,
            )
            rows = np.flatnonzero(selected == component_index)
            standard_normal = generator.standard_normal(
                (rows.size, flat_dimension)
            )
            with np.errstate(over="ignore", invalid="ignore"):
                samples[rows] = (
                    base
                    + offset
                    + standard_normal * np.sqrt(variance)
                )
        if not np.all(np.isfinite(samples)):
            raise ArithmeticError("conditional samples are outside floating-point range")
        result = samples.reshape((draw_count,) + positions.shape)
        if validated_size is None:
            return result[0]
        return result


__all__ = [
    "AssociationHypothesis",
    "BrownianParticleBridgeOracle",
    "GaussianMixtureMoments",
    "UnreachableParticleBridgeObservationError",
]
