"""Exact path-space relative entropy for bounded finite-state CTMCs.

This module is a classical finite-state oracle.  It checks the jump part of the
path-space approximation identity targeted by the research specification; it
does not prove that identity on continuous marked-configuration space.

For two time-homogeneous row-convention generators ``Q`` (reference) and
``R`` (candidate), with initial laws ``p`` and ``r``, the finite-horizon path
relative entropy is

``KL(P_Q || P_R) = KL(p || r) + integral p_t[i] d_i dt``,

where ``p_t = p exp(t Q)`` and

``d_i = sum_{j != i} [Q_ij log(Q_ij / R_ij) - Q_ij + R_ij]``.

The value is infinite when the candidate removes a jump edge used with
positive occupation under the reference law.  Candidate-only edges contribute
their waiting-time penalty ``R_ij``.  Occupation times are evaluated by one
augmented matrix exponential rather than time discretisation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Tuple
import warnings

import numpy as np
from scipy.linalg import expm

from .finite_state import validate_generator, validate_probability_vector


_MAX_STATES = 256
_MAX_SCALED_EXIT_RATE = 1.0e7
_LOG_MAX_FLOAT = math.log(float(np.finfo(np.float64).max))
_LOG_MIN_SUBNORMAL = math.log(float(np.nextafter(0.0, 1.0)))


def _immutable_vector(value: object, *, name: str) -> np.ndarray:
    try:
        raw = np.asarray(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s must be a finite numeric vector" % name) from error
    if raw.dtype.kind == "b":
        raise TypeError("%s must not have boolean dtype" % name)
    if raw.dtype.kind not in "iuf":
        raise TypeError("%s must have a real numeric dtype" % name)
    try:
        array = raw.astype(np.float64, copy=False)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s must be representable as floats" % name) from error
    if array.ndim != 1:
        raise ValueError("%s must be one-dimensional" % name)
    if not np.all(np.isfinite(array)):
        raise ValueError("%s must be finite" % name)
    contiguous = np.array(array, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=np.float64)


def _validated_horizon(value: float) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("horizon must be a real non-boolean number")
    horizon = float(value)
    if not math.isfinite(horizon) or horizon < 0.0:
        raise ValueError("horizon must be finite and nonnegative")
    return horizon


def _validate_state_limit(state_count: int) -> None:
    if isinstance(state_count, bool) or not isinstance(state_count, Integral):
        raise TypeError("state_count must be an integer")
    if state_count <= 0 or state_count > _MAX_STATES:
        raise ValueError(
            "finite path-KL oracle supports between one and %d states"
            % _MAX_STATES
        )


@dataclass(frozen=True, eq=False)
class CTMCPathKLDivergence:
    """Decomposition of finite-horizon CTMC path relative entropy.

    ``occupation_time[i]`` is the expected amount of time spent in state ``i``
    under the reference law. ``state_rate_divergence[i]`` is the instantaneous
    relative-entropy rate conditional on that state and may be ``+inf``.
    Arrays are stored as defensive bytes-backed read-only copies.
    """

    initial: float
    dynamic: float
    total: float
    occupation_time: np.ndarray
    state_rate_divergence: np.ndarray

    def __post_init__(self) -> None:
        scalars = {}
        for name in ("initial", "dynamic", "total"):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
                raise TypeError("%s divergence must be a real number" % name)
            result = float(value)
            if math.isnan(result) or result < 0.0:
                raise ValueError("%s divergence must be nonnegative or +inf" % name)
            scalars[name] = result

        occupation = _immutable_vector(self.occupation_time, name="occupation_time")
        if np.any(occupation < 0.0):
            raise ValueError("occupation_time must be nonnegative")
        try:
            rates = np.asarray(self.state_rate_divergence, dtype=np.float64)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                "state_rate_divergence must be a numeric vector"
            ) from error
        if rates.ndim != 1 or rates.shape != occupation.shape:
            raise ValueError(
                "state_rate_divergence must match occupation_time shape"
            )
        if np.any(np.isnan(rates)) or np.any(rates < 0.0):
            raise ValueError(
                "state_rate_divergence must be nonnegative or +inf"
            )
        contiguous_rates = np.array(rates, dtype=np.float64, copy=True, order="C")
        immutable_rates = np.frombuffer(
            contiguous_rates.tobytes(order="C"), dtype=np.float64
        )

        expected_total = scalars["initial"] + scalars["dynamic"]
        if math.isinf(expected_total):
            if not math.isinf(scalars["total"]):
                raise ValueError("total divergence is inconsistent with components")
        elif not math.isclose(
            scalars["total"], expected_total, rel_tol=1.0e-13, abs_tol=1.0e-15
        ):
            raise ValueError("total divergence is inconsistent with components")

        for name, value in scalars.items():
            object.__setattr__(self, name, value)
        object.__setattr__(self, "occupation_time", occupation)
        object.__setattr__(self, "state_rate_divergence", immutable_rates)


def _initial_kl(reference: np.ndarray, candidate: np.ndarray) -> float:
    terms = []
    for reference_mass, candidate_mass in zip(reference, candidate):
        p = float(reference_mass)
        r = float(candidate_mass)
        if p == 0.0:
            continue
        if r == 0.0:
            return math.inf
        terms.append(p * (math.log(p) - math.log(r)))
    result = math.fsum(terms)
    if result < 0.0 and result >= -1.0e-14:
        result = 0.0
    if not math.isfinite(result) or result < 0.0:
        raise ArithmeticError("initial relative entropy is not representable")
    return result


def _poisson_rate_divergence(reference_rate: float, candidate_rate: float) -> float:
    if reference_rate == 0.0:
        return candidate_rate
    if candidate_rate == 0.0:
        return math.inf
    if reference_rate == candidate_rate:
        return 0.0

    difference = reference_rate - candidate_rate
    if abs(difference) <= 0.5 * candidate_rate:
        relative_difference = difference / candidate_rate
        value = candidate_rate * (
            (1.0 + relative_difference) * math.log1p(relative_difference)
            - relative_difference
        )
    else:
        value = (
            reference_rate
            * (math.log(reference_rate) - math.log(candidate_rate))
            - reference_rate
            + candidate_rate
        )
    tolerance = 64.0 * np.finfo(np.float64).eps * max(
        reference_rate, candidate_rate
    )
    if value < 0.0 and value >= -tolerance:
        return 0.0
    if not math.isfinite(value) or value < 0.0:
        raise ArithmeticError("jump-rate divergence is not representable")
    return value


def _state_rate_divergences(
    reference_generator: np.ndarray, candidate_generator: np.ndarray
) -> np.ndarray:
    state_count = reference_generator.shape[0]
    result = np.zeros(state_count, dtype=np.float64)
    for source in range(state_count):
        terms = []
        for destination in range(state_count):
            if source == destination:
                continue
            value = _poisson_rate_divergence(
                float(reference_generator[source, destination]),
                float(candidate_generator[source, destination]),
            )
            if math.isinf(value):
                terms = [math.inf]
                break
            terms.append(value)
        result[source] = math.fsum(terms)
    return result


def _reachable_states(initial: np.ndarray, generator: np.ndarray) -> Tuple[int, ...]:
    frontier = [int(index) for index in np.flatnonzero(initial > 0.0)]
    reached = set(frontier)
    while frontier:
        source = frontier.pop()
        destinations = np.flatnonzero(generator[source] > 0.0)
        for raw_destination in destinations:
            destination = int(raw_destination)
            if destination == source or destination in reached:
                continue
            reached.add(destination)
            frontier.append(destination)
    return tuple(sorted(reached))


def _occupation_times(
    initial: np.ndarray, generator: np.ndarray, horizon: float
) -> np.ndarray:
    state_count = generator.shape[0]
    if horizon == 0.0:
        return np.zeros(state_count, dtype=np.float64)

    maximum_exit_rate = float(np.max(-np.diag(generator)))
    scaled_rate = maximum_exit_rate * horizon
    if not math.isfinite(scaled_rate) or scaled_rate > _MAX_SCALED_EXIT_RATE:
        raise ValueError(
            "generator exit rates times horizon exceed the finite oracle limit"
        )

    augmented = np.zeros((2 * state_count, 2 * state_count), dtype=np.float64)
    augmented[:state_count, :state_count] = generator
    augmented[:state_count, state_count:] = np.eye(state_count, dtype=np.float64)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            exponential = expm(augmented * horizon)
    except (ArithmeticError, ValueError, Warning) as error:
        raise ArithmeticError("occupation-time matrix exponential failed") from error
    integral = exponential[:state_count, state_count:]
    occupation = initial @ integral
    if not np.all(np.isfinite(occupation)):
        raise ArithmeticError("occupation times are not finite")
    tolerance = 512.0 * np.finfo(np.float64).eps * max(horizon, 1.0)
    if np.any(occupation < -tolerance):
        raise ArithmeticError("occupation times became materially negative")
    occupation = np.where(occupation < 0.0, 0.0, occupation)
    total = float(math.fsum(float(value) for value in occupation))
    if not math.isclose(total, horizon, rel_tol=1.0e-11, abs_tol=tolerance):
        raise ArithmeticError("occupation times do not sum to the horizon")
    return occupation


def ctmc_path_kl(
    reference_initial: np.ndarray,
    reference_generator: np.ndarray,
    candidate_initial: np.ndarray,
    candidate_generator: np.ndarray,
    horizon: float,
) -> CTMCPathKLDivergence:
    """Return ``KL(reference path law || candidate path law)`` exactly.

    The two processes must be time-homogeneous finite-state CTMCs over the same
    ordered state space.  Infinite values are returned for genuine support
    mismatch; invalid matrices, numerical overflow, and resource excess raise.
    """

    reference_q = validate_generator(reference_generator)
    candidate_q = validate_generator(candidate_generator)
    if reference_q.shape != candidate_q.shape:
        raise ValueError("reference and candidate generators must have equal shape")
    state_count = reference_q.shape[0]
    _validate_state_limit(state_count)
    reference_p = validate_probability_vector(reference_initial, state_count)
    candidate_p = validate_probability_vector(candidate_initial, state_count)
    duration = _validated_horizon(horizon)

    initial_divergence = _initial_kl(reference_p, candidate_p)
    rate_divergences = _state_rate_divergences(reference_q, candidate_q)
    occupation = _occupation_times(reference_p, reference_q, duration)

    dynamic_divergence = 0.0
    if duration > 0.0:
        reachable = set(_reachable_states(reference_p, reference_q))
        if any(
            math.isinf(float(rate_divergences[index])) for index in reachable
        ):
            dynamic_divergence = math.inf
        else:
            dynamic_divergence = math.fsum(
                float(occupation[index]) * float(rate_divergences[index])
                for index in reachable
            )
            if dynamic_divergence < 0.0 and dynamic_divergence >= -1.0e-14:
                dynamic_divergence = 0.0
            if not math.isfinite(dynamic_divergence) or dynamic_divergence < 0.0:
                raise ArithmeticError("dynamic relative entropy is not representable")

    total = initial_divergence + dynamic_divergence
    if math.isnan(total):
        raise ArithmeticError("path relative entropy is not representable")
    return CTMCPathKLDivergence(
        initial=initial_divergence,
        dynamic=dynamic_divergence,
        total=total,
        occupation_time=occupation,
        state_rate_divergence=rate_divergences,
    )


def information_tilt_generator(
    base_generator: np.ndarray, log_information: np.ndarray
) -> np.ndarray:
    """Tilt finite CTMC jump rates by a strictly positive information vector.

    Off-diagonal rates are ``Q[i,j] * exp(log_h[j] - log_h[i])``.  The
    diagonal is reset to conserve rows.  This instantaneous construction is
    invariant to a common additive shift of ``log_h``.  It deliberately
    rejects ``-inf`` and zero information: unreachable/singular observations
    require a separately declared support branch.
    """

    generator = validate_generator(base_generator)
    state_count = generator.shape[0]
    _validate_state_limit(state_count)
    logs = _immutable_vector(log_information, name="log_information")
    if logs.shape != (state_count,):
        raise ValueError(
            "log_information must have shape (%d,)" % state_count
        )

    off_diagonal = np.zeros_like(generator)
    for source in range(state_count):
        for destination in range(state_count):
            if source == destination:
                continue
            rate = float(generator[source, destination])
            if rate == 0.0:
                continue
            log_rate = math.log(rate) + float(logs[destination] - logs[source])
            if log_rate > _LOG_MAX_FLOAT or log_rate < _LOG_MIN_SUBNORMAL:
                raise ArithmeticError(
                    "tilted rate is outside the positive floating-point range"
                )
            tilted_rate = math.exp(log_rate)
            if not math.isfinite(tilted_rate) or tilted_rate <= 0.0:
                raise ArithmeticError("tilted rate is not representable")
            off_diagonal[source, destination] = tilted_rate
    for source in range(state_count):
        try:
            exit_rate = math.fsum(
                float(off_diagonal[source, destination])
                for destination in range(state_count)
                if destination != source
            )
        except OverflowError as error:
            raise ArithmeticError("total tilted exit rate is not representable") from error
        if not math.isfinite(exit_rate):
            raise ArithmeticError("total tilted exit rate is not representable")
        off_diagonal[source, source] = -exit_rate
    return validate_generator(off_diagonal)


__all__ = [
    "CTMCPathKLDivergence",
    "ctmc_path_kl",
    "information_tilt_generator",
]
