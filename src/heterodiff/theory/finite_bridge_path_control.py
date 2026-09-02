"""Finite-state path control for positive time-dependent bridge potentials.

This module is a bounded numerical diagnostic, not a scalable model and not a
configuration-space theorem.  A row-convention finite CTMC with generator
``Q`` is tilted by a strictly positive potential ``v(t, i)`` according to

``Q^v_t[i, j] = Q[i, j] v(t, j) / v(t, i)``,  ``i != j``.

The diagonal is always rebuilt as the negative off-diagonal row sum.  The
initial law is tilted and normalized as ``rho[i] v(0, i) / Z_v``.  For two
potentials ``h`` and ``v``, :func:`tilted_path_kl` numerically propagates the
``h``-tilted marginal and evaluates the finite-state path relative entropy

``KL(Q^h || Q^v) = KL(rho^h_0 || rho^v_0)``
``                    + integral sum_i rho^h_t[i] D_i(t) dt``,

where ``D_i`` is the sum of Poisson-rate divergences over outgoing edges.
The dynamic term and state occupation times are computed by adaptive numerical
quadrature over a dense adaptive ODE solution.  They are numerical controls,
not exact certificates.

Arbitrary potential callables are supported by the diagnostic functions and
are assumed to be deterministic and sufficiently regular for the requested
numerical tolerances.  Exact simulation needs more: an arbitrary callable has
no certifiable between-call rate envelope.  The sampler is therefore restricted
to :class:`TabulatedPositivePotential`, whose logarithm is linearly
interpolated.  Every tilted edge rate is then exponential-affine on each knot
interval, so each state exit rate is convex and its maximum occurs at an
interval endpoint.  This gives a certified finite thinning bound.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Callable, Optional, Tuple
import warnings

import numpy as np
from scipy.integrate import quad_vec, solve_ivp

from .finite_state import validate_generator, validate_probability_vector


PositivePotential = Callable[[float], object]

_MAX_STATES = 256
_MAX_TABLE_ENTRIES = 2_000_000
_MAX_EVALUATION_TIMES = 10_001
_MAX_POTENTIAL_EVALUATIONS = 1_000_000
_MAX_QUADRATURE_LIMIT = 100_000
_MAX_SAMPLER_PROPOSALS = 1_000_000
_MAX_SAMPLER_JUMPS = 1_000_000
_MAX_SCALED_EXIT_RATE = 10_000_000.0
_MAX_SEED = int(np.iinfo(np.uint64).max)
_LOG_MAX_FLOAT = math.log(float(np.finfo(np.float64).max))
_LOG_MIN_SUBNORMAL = math.log(float(np.nextafter(0.0, 1.0)))


def _immutable_array(value: object, *, dtype: np.dtype = np.dtype(float)) -> np.ndarray:
    array = np.asarray(value, dtype=dtype)
    contiguous = np.array(array, dtype=dtype, copy=True, order="C")
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=dtype).reshape(
        contiguous.shape
    )


def _numeric_array(value: object, *, name: str, ndim: int) -> np.ndarray:
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
        raise ValueError("%s cannot be represented as floats" % name) from error
    if array.ndim != ndim:
        raise ValueError("%s must be %d-dimensional" % (name, ndim))
    if not np.all(np.isfinite(array)):
        raise ValueError("%s entries must be finite" % name)
    return array


def _real_number(value: object, *, name: str, minimum: float) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise ValueError("%s must be finite and at least %g" % (name, minimum))
    return result


def _positive_integer(value: object, *, name: str, maximum: int) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result <= 0 or result > maximum:
        raise ValueError("%s must lie between 1 and %d" % (name, maximum))
    return result


def _nonnegative_integer(value: object, *, name: str, maximum: int) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result < 0 or result > maximum:
        raise ValueError("%s must lie between 0 and %d" % (name, maximum))
    return result


def _state_limited_generator(base_generator: object) -> np.ndarray:
    generator = validate_generator(np.asarray(base_generator))
    state_count = generator.shape[0]
    if state_count <= 0 or state_count > _MAX_STATES:
        raise ValueError(
            "finite bridge path control supports between one and %d states"
            % _MAX_STATES
        )
    return generator


def _positive_vector(value: object, *, state_count: int, name: str) -> np.ndarray:
    vector = _numeric_array(value, name=name, ndim=1)
    if vector.shape != (state_count,):
        raise ValueError("%s must have shape (%d,)" % (name, state_count))
    if np.any(vector <= 0.0):
        raise ValueError("%s must be strictly positive" % name)
    return vector


@dataclass(frozen=True, eq=False, init=False)
class TabulatedPositivePotential:
    """Strictly positive values with linear interpolation in log space.

    The public time argument is the direct process time.  In particular, an
    exact terminal-observation information function should be tabulated as
    ``h_t = P_{t,T} g`` rather than as a function of an undocumented reverse
    clock.
    """

    times: np.ndarray
    values: np.ndarray
    _log_values: np.ndarray

    def __init__(self, times: object, values: object) -> None:
        checked_times = _numeric_array(times, name="times", ndim=1)
        checked_values = _numeric_array(values, name="values", ndim=2)
        if checked_times.size < 2:
            raise ValueError("times must contain at least two knots")
        if checked_values.shape[0] != checked_times.size:
            raise ValueError("values rows must match the number of time knots")
        if checked_values.shape[1] <= 0:
            raise ValueError("values must contain at least one state")
        if checked_values.size > _MAX_TABLE_ENTRIES:
            raise ValueError(
                "potential table exceeds the limit of %d entries"
                % _MAX_TABLE_ENTRIES
            )
        if np.any(np.diff(checked_times) <= 0.0):
            raise ValueError("times must be strictly increasing")
        if checked_times[0] < 0.0:
            raise ValueError("times must be nonnegative")
        if np.any(checked_values <= 0.0):
            raise ValueError("values must be strictly positive")
        log_values = np.log(checked_values)
        if not np.all(np.isfinite(log_values)):
            raise ArithmeticError("log potential values are not representable")
        object.__setattr__(self, "times", _immutable_array(checked_times))
        object.__setattr__(self, "values", _immutable_array(checked_values))
        object.__setattr__(self, "_log_values", _immutable_array(log_values))

    @property
    def state_count(self) -> int:
        return int(self.values.shape[1])

    @property
    def start_time(self) -> float:
        return float(self.times[0])

    @property
    def end_time(self) -> float:
        return float(self.times[-1])

    def __call__(self, time: float) -> np.ndarray:
        direct_time = _real_number(time, name="time", minimum=0.0)
        if direct_time < self.start_time or direct_time > self.end_time:
            raise ValueError(
                "time must lie within the tabulated interval [%g, %g]"
                % (self.start_time, self.end_time)
            )
        if direct_time == self.end_time:
            return _immutable_array(self.values[-1])
        right = int(np.searchsorted(self.times, direct_time, side="right"))
        if right == 0:
            return _immutable_array(self.values[0])
        left = right - 1
        width = float(self.times[right] - self.times[left])
        fraction = (direct_time - float(self.times[left])) / width
        log_value = (
            (1.0 - fraction) * self._log_values[left]
            + fraction * self._log_values[right]
        )
        value = np.exp(log_value)
        if np.any(value <= 0.0) or not np.all(np.isfinite(value)):
            raise ArithmeticError("interpolated potential is not representable")
        return _immutable_array(value)


class _EvaluationBudget:
    def __init__(self, maximum: int) -> None:
        self.maximum = _positive_integer(
            maximum,
            name="max_potential_evaluations",
            maximum=_MAX_POTENTIAL_EVALUATIONS,
        )
        self.count = 0

    def consume(self) -> None:
        self.count += 1
        if self.count > self.maximum:
            raise RuntimeError(
                "potential evaluation count exceeded the declared limit of %d"
                % self.maximum
            )


def _potential_values(
    potential: PositivePotential,
    time: float,
    state_count: int,
    budget: Optional[_EvaluationBudget],
) -> np.ndarray:
    if not callable(potential):
        raise TypeError(
            "potential must be callable; use TabulatedPositivePotential for tables"
        )
    direct_time = _real_number(time, name="time", minimum=0.0)
    if budget is not None:
        budget.consume()
    return _positive_vector(
        potential(direct_time), state_count=state_count, name="potential(time)"
    )


class _TiltEngine:
    def __init__(self, generator: np.ndarray) -> None:
        self.generator = _state_limited_generator(generator)
        self.state_count = self.generator.shape[0]
        off_diagonal = self.generator.copy()
        np.fill_diagonal(off_diagonal, 0.0)
        self.sources, self.destinations = np.nonzero(off_diagonal > 0.0)
        self.base_rates = off_diagonal[self.sources, self.destinations]
        self.log_base_rates = np.log(self.base_rates)

    def tilt(self, values: np.ndarray) -> np.ndarray:
        checked = _positive_vector(
            values, state_count=self.state_count, name="potential values"
        )
        logs = np.log(checked)
        log_rates = (
            self.log_base_rates
            + logs[self.destinations]
            - logs[self.sources]
        )
        if np.any(log_rates > _LOG_MAX_FLOAT) or np.any(
            log_rates < _LOG_MIN_SUBNORMAL
        ):
            raise ArithmeticError(
                "a tilted rate is outside the positive floating-point range"
            )
        rates = np.exp(log_rates)
        if np.any(rates <= 0.0) or not np.all(np.isfinite(rates)):
            raise ArithmeticError("a tilted rate is not representable")
        result = np.zeros_like(self.generator)
        result[self.sources, self.destinations] = rates
        for source in range(self.state_count):
            try:
                exit_rate = math.fsum(
                    float(result[source, destination])
                    for destination in range(self.state_count)
                    if destination != source
                )
            except OverflowError as error:
                raise ArithmeticError(
                    "a tilted total exit rate is not representable"
                ) from error
            if not math.isfinite(exit_rate):
                raise ArithmeticError(
                    "a tilted total exit rate is not representable"
                )
            result[source, source] = -exit_rate
        return result


def potential_tilted_generator(
    base_generator: object,
    potential: PositivePotential,
    time: object,
) -> np.ndarray:
    """Return the conservative generator tilted at direct process time ``time``."""

    engine = _TiltEngine(np.asarray(base_generator))
    values = _potential_values(
        potential,
        _real_number(time, name="time", minimum=0.0),
        engine.state_count,
        None,
    )
    return _immutable_array(engine.tilt(values))


@dataclass(frozen=True, eq=False)
class TiltedInitialLaw:
    """Normalized initial tilt and its potential normalizer."""

    time: float
    normalizer: float
    probabilities: np.ndarray

    def __post_init__(self) -> None:
        direct_time = _real_number(self.time, name="time", minimum=0.0)
        normalizer = _real_number(
            self.normalizer, name="normalizer", minimum=0.0
        )
        if normalizer == 0.0:
            raise ValueError("normalizer must be strictly positive")
        probabilities = validate_probability_vector(self.probabilities)
        object.__setattr__(self, "time", direct_time)
        object.__setattr__(self, "normalizer", normalizer)
        object.__setattr__(
            self, "probabilities", _immutable_array(probabilities)
        )


def _initial_from_values(
    base_initial: np.ndarray,
    values: np.ndarray,
    time: float,
) -> TiltedInitialLaw:
    initial = validate_probability_vector(base_initial, values.size)
    support = initial > 0.0
    if not np.any(support):
        raise ArithmeticError("base initial law has no positive support")
    scale = float(np.max(values[support]))
    scaled = np.zeros_like(initial)
    scaled[support] = initial[support] * values[support] / scale
    scaled_total = math.fsum(float(value) for value in scaled)
    normalizer = scale * scaled_total
    if (
        not math.isfinite(scaled_total)
        or scaled_total <= 0.0
        or not math.isfinite(normalizer)
        or normalizer <= 0.0
    ):
        raise ArithmeticError("initial potential normalizer is not representable")
    probabilities = scaled / scaled_total
    if np.any(support & (probabilities == 0.0)):
        raise ArithmeticError("a positive tilted initial mass underflowed to zero")
    probabilities = validate_probability_vector(
        probabilities, initial.size, atol=2.0e-14
    )
    return TiltedInitialLaw(
        time=time, normalizer=normalizer, probabilities=probabilities
    )


def conditional_initial_law(
    base_initial: object,
    potential: PositivePotential,
    time: object = 0.0,
) -> TiltedInitialLaw:
    """Return ``rho_i v(time,i) / sum_j rho_j v(time,j)``."""

    raw_initial = validate_probability_vector(np.asarray(base_initial))
    if raw_initial.size > _MAX_STATES:
        raise ValueError(
            "finite bridge path control supports at most %d states" % _MAX_STATES
        )
    direct_time = _real_number(time, name="time", minimum=0.0)
    values = _potential_values(
        potential, direct_time, raw_initial.size, None
    )
    return _initial_from_values(raw_initial, values, direct_time)


def _evaluation_grid(horizon: float, evaluation_times: object) -> np.ndarray:
    if evaluation_times is None:
        if horizon == 0.0:
            return np.asarray([0.0])
        return np.linspace(0.0, horizon, 17, dtype=float)
    times = _numeric_array(evaluation_times, name="evaluation_times", ndim=1)
    if times.size <= 0 or times.size > _MAX_EVALUATION_TIMES:
        raise ValueError(
            "evaluation_times must contain between 1 and %d values"
            % _MAX_EVALUATION_TIMES
        )
    if horizon == 0.0:
        if times.size != 1 or times[0] != 0.0:
            raise ValueError("zero horizon requires evaluation_times=[0]")
        return times
    if times.size < 2 or np.any(np.diff(times) <= 0.0):
        raise ValueError("evaluation_times must be strictly increasing")
    tolerance = 32.0 * np.finfo(np.float64).eps * max(horizon, 1.0)
    if abs(float(times[0])) > tolerance or abs(float(times[-1]) - horizon) > tolerance:
        raise ValueError("evaluation_times must begin at 0 and end at horizon")
    times[0] = 0.0
    times[-1] = horizon
    return times


def _numerical_controls(
    horizon: object,
    rtol: object,
    atol: object,
    max_step: object,
    quadrature_epsabs: object,
    quadrature_epsrel: object,
    quadrature_limit: object,
) -> Tuple[float, float, float, float, float, float, int]:
    duration = _real_number(horizon, name="horizon", minimum=0.0)
    relative = _real_number(rtol, name="rtol", minimum=0.0)
    absolute = _real_number(atol, name="atol", minimum=0.0)
    quad_absolute = _real_number(
        quadrature_epsabs, name="quadrature_epsabs", minimum=0.0
    )
    quad_relative = _real_number(
        quadrature_epsrel, name="quadrature_epsrel", minimum=0.0
    )
    if relative == 0.0 or relative >= 1.0:
        raise ValueError("rtol must lie strictly between zero and one")
    if absolute == 0.0:
        raise ValueError("atol must be strictly positive")
    if quad_absolute == 0.0 or quad_relative == 0.0 or quad_relative >= 1.0:
        raise ValueError(
            "quadrature tolerances must be positive and epsrel must be below one"
        )
    if max_step is None:
        step = duration / 64.0 if duration > 0.0 else 1.0
    else:
        step = _real_number(max_step, name="max_step", minimum=0.0)
        if step == 0.0:
            raise ValueError("max_step must be strictly positive")
    limit = _positive_integer(
        quadrature_limit,
        name="quadrature_limit",
        maximum=_MAX_QUADRATURE_LIMIT,
    )
    return (
        duration,
        relative,
        absolute,
        step,
        quad_absolute,
        quad_relative,
        limit,
    )


def _validated_marginal(
    value: object,
    *,
    state_count: int,
    numerical_atol: float,
) -> np.ndarray:
    marginal = _numeric_array(value, name="numerical marginal", ndim=1)
    if marginal.shape != (state_count,):
        raise ArithmeticError("numerical marginal has the wrong shape")
    tolerance = max(2.0e-10, 128.0 * numerical_atol)
    if np.any(marginal < -tolerance):
        raise ArithmeticError("numerical marginal became materially negative")
    total = math.fsum(float(value) for value in marginal)
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=tolerance):
        raise ArithmeticError("numerical marginal does not conserve probability")
    marginal[marginal < 0.0] = 0.0
    marginal /= marginal.sum()
    return marginal


def _solve_marginal(
    initial: np.ndarray,
    engine: _TiltEngine,
    potential: PositivePotential,
    horizon: float,
    evaluation_times: np.ndarray,
    rtol: float,
    atol: float,
    max_step: float,
    budget: _EvaluationBudget,
):
    if horizon == 0.0:
        return None, initial[None, :], 0

    def right_hand_side(time: float, marginal: np.ndarray) -> np.ndarray:
        values = _potential_values(
            potential, time, engine.state_count, budget
        )
        return marginal @ engine.tilt(values)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            solution = solve_ivp(
                right_hand_side,
                (0.0, horizon),
                initial,
                method="DOP853",
                t_eval=evaluation_times,
                dense_output=True,
                rtol=rtol,
                atol=atol,
                max_step=max_step,
            )
    except (ArithmeticError, RuntimeError, ValueError, Warning) as error:
        raise ArithmeticError("time-inhomogeneous marginal integration failed") from error
    if not solution.success or solution.sol is None:
        raise ArithmeticError(
            "time-inhomogeneous marginal integration failed: %s"
            % solution.message
        )
    marginals = np.vstack(
        [
            _validated_marginal(
                solution.y[:, index],
                state_count=engine.state_count,
                numerical_atol=atol,
            )
            for index in range(solution.y.shape[1])
        ]
    )
    return solution, marginals, int(solution.nfev)


def _dense_marginal(solution, time: float, state_count: int, atol: float) -> np.ndarray:
    return _validated_marginal(
        solution.sol(time), state_count=state_count, numerical_atol=atol
    )


def _quadrature(
    integrand,
    horizon: float,
    epsabs: float,
    epsrel: float,
    limit: int,
):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            integral, error = quad_vec(
                integrand,
                0.0,
                horizon,
                epsabs=epsabs,
                epsrel=epsrel,
                limit=limit,
            )
    except (ArithmeticError, RuntimeError, ValueError, Warning) as caught:
        raise ArithmeticError("adaptive numerical quadrature failed") from caught
    error_value = float(error)
    if not math.isfinite(error_value) or error_value < 0.0:
        raise ArithmeticError("quadrature returned an invalid error estimate")
    return np.asarray(integral, dtype=float), error_value


@dataclass(frozen=True, eq=False)
class TimeIndexedOccupancy:
    """Tilted marginals at requested times and integrated state occupancy."""

    initial_law: TiltedInitialLaw
    times: np.ndarray
    marginals: np.ndarray
    integrated_occupation: np.ndarray
    quadrature_error: float
    ode_evaluations: int
    potential_evaluations: int

    def __post_init__(self) -> None:
        if not isinstance(self.initial_law, TiltedInitialLaw):
            raise TypeError("initial_law must be a TiltedInitialLaw")
        times = _numeric_array(self.times, name="times", ndim=1)
        marginals = _numeric_array(self.marginals, name="marginals", ndim=2)
        occupation = _numeric_array(
            self.integrated_occupation, name="integrated_occupation", ndim=1
        )
        if marginals.shape != (times.size, occupation.size):
            raise ValueError("marginals shape must match times and state count")
        if times.size == 0 or times[0] != 0.0 or np.any(np.diff(times) <= 0.0):
            raise ValueError("times must begin at zero and be strictly increasing")
        if occupation.size != self.initial_law.probabilities.size:
            raise ValueError("occupancy state count must match the initial law")
        if np.any(marginals < 0.0) or np.any(occupation < 0.0):
            raise ValueError("marginals and occupation must be nonnegative")
        if not np.allclose(
            marginals.sum(axis=1), 1.0, atol=3.0e-10, rtol=0.0
        ):
            raise ValueError("every time-indexed marginal must sum to one")
        horizon = float(times[-1])
        if not math.isclose(
            math.fsum(float(value) for value in occupation),
            horizon,
            rel_tol=0.0,
            abs_tol=3.0e-9 * max(horizon, 1.0),
        ):
            raise ValueError("integrated occupation must sum to the horizon")
        quadrature_error = _real_number(
            self.quadrature_error, name="quadrature_error", minimum=0.0
        )
        ode_evaluations = _nonnegative_integer(
            self.ode_evaluations,
            name="ode_evaluations",
            maximum=_MAX_POTENTIAL_EVALUATIONS,
        )
        potential_evaluations = _nonnegative_integer(
            self.potential_evaluations,
            name="potential_evaluations",
            maximum=_MAX_POTENTIAL_EVALUATIONS,
        )
        object.__setattr__(self, "times", _immutable_array(times))
        object.__setattr__(self, "marginals", _immutable_array(marginals))
        object.__setattr__(
            self, "integrated_occupation", _immutable_array(occupation)
        )
        object.__setattr__(self, "quadrature_error", quadrature_error)
        object.__setattr__(self, "ode_evaluations", ode_evaluations)
        object.__setattr__(
            self, "potential_evaluations", potential_evaluations
        )


def _occupation_record(
    initial_law: TiltedInitialLaw,
    engine: _TiltEngine,
    potential: PositivePotential,
    horizon: float,
    times: np.ndarray,
    rtol: float,
    atol: float,
    max_step: float,
    quad_epsabs: float,
    quad_epsrel: float,
    quad_limit: int,
    budget: _EvaluationBudget,
) -> Tuple[TimeIndexedOccupancy, object]:
    solution, marginals, ode_evaluations = _solve_marginal(
        initial_law.probabilities,
        engine,
        potential,
        horizon,
        times,
        rtol,
        atol,
        max_step,
        budget,
    )
    if horizon == 0.0:
        occupation = np.zeros(engine.state_count, dtype=float)
        quadrature_error = 0.0
    else:
        occupation, quadrature_error = _quadrature(
            lambda time: _dense_marginal(
                solution, time, engine.state_count, atol
            ),
            horizon,
            quad_epsabs,
            quad_epsrel,
            quad_limit,
        )
        tolerance = max(
            2.0e-9 * max(horizon, 1.0),
            8.0 * quadrature_error,
            128.0 * atol,
        )
        if np.any(occupation < -tolerance):
            raise ArithmeticError("integrated occupation became negative")
        occupation[occupation < 0.0] = 0.0
        if not math.isclose(
            math.fsum(float(value) for value in occupation),
            horizon,
            rel_tol=0.0,
            abs_tol=tolerance,
        ):
            raise ArithmeticError("integrated occupation does not sum to horizon")
    record = TimeIndexedOccupancy(
        initial_law=initial_law,
        times=times,
        marginals=marginals,
        integrated_occupation=occupation,
        quadrature_error=quadrature_error,
        ode_evaluations=ode_evaluations,
        potential_evaluations=budget.count,
    )
    return record, solution


def integrate_tilted_occupancy(
    base_initial: object,
    base_generator: object,
    potential: PositivePotential,
    horizon: object,
    *,
    evaluation_times: object = None,
    rtol: object = 2.0e-10,
    atol: object = 2.0e-12,
    max_step: object = None,
    quadrature_epsabs: object = 1.0e-10,
    quadrature_epsrel: object = 1.0e-9,
    quadrature_limit: object = 1_000,
    max_potential_evaluations: object = 200_000,
) -> TimeIndexedOccupancy:
    """Propagate the tilted initial law and return time-indexed occupancy."""

    engine = _TiltEngine(np.asarray(base_generator))
    initial = validate_probability_vector(
        np.asarray(base_initial), engine.state_count
    )
    (
        duration,
        relative,
        absolute,
        step,
        quad_absolute,
        quad_relative,
        quad_limit,
    ) = _numerical_controls(
        horizon,
        rtol,
        atol,
        max_step,
        quadrature_epsabs,
        quadrature_epsrel,
        quadrature_limit,
    )
    times = _evaluation_grid(duration, evaluation_times)
    budget = _EvaluationBudget(max_potential_evaluations)  # type: ignore[arg-type]
    initial_values = _potential_values(
        potential, 0.0, engine.state_count, budget
    )
    initial_law = _initial_from_values(initial, initial_values, 0.0)
    record, _ = _occupation_record(
        initial_law,
        engine,
        potential,
        duration,
        times,
        relative,
        absolute,
        step,
        quad_absolute,
        quad_relative,
        quad_limit,
        budget,
    )
    return record


def _categorical_kl(reference: np.ndarray, candidate: np.ndarray) -> float:
    terms = []
    for reference_mass, candidate_mass in zip(reference, candidate):
        p = float(reference_mass)
        q = float(candidate_mass)
        if p == 0.0:
            continue
        if q == 0.0:
            return math.inf
        terms.append(p * (math.log(p) - math.log(q)))
    result = math.fsum(terms)
    if result < 0.0 and result >= -2.0e-14:
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
        relative = difference / candidate_rate
        value = candidate_rate * (
            (1.0 + relative) * math.log1p(relative) - relative
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
        value = 0.0
    if not math.isfinite(value) or value < 0.0:
        raise ArithmeticError("jump-rate divergence is not representable")
    return value


def _state_rate_divergence(
    reference_generator: np.ndarray,
    candidate_generator: np.ndarray,
) -> np.ndarray:
    state_count = reference_generator.shape[0]
    result = np.zeros(state_count, dtype=float)
    for source in range(state_count):
        terms = []
        for destination in range(state_count):
            if source == destination:
                continue
            divergence = _poisson_rate_divergence(
                float(reference_generator[source, destination]),
                float(candidate_generator[source, destination]),
            )
            if math.isinf(divergence):
                terms = [math.inf]
                break
            terms.append(divergence)
        result[source] = math.fsum(terms)
    return result


@dataclass(frozen=True, eq=False)
class FiniteBridgePathKL:
    """Numerical decomposition of a time-inhomogeneous tilted path KL."""

    initial: float
    dynamic: float
    total: float
    reference_initial: TiltedInitialLaw
    candidate_initial: TiltedInitialLaw
    occupancy: TimeIndexedOccupancy
    state_rate_divergence: np.ndarray
    quadrature_error: float
    potential_evaluations: int

    def __post_init__(self) -> None:
        checked = {}
        for name in ("initial", "dynamic", "total", "quadrature_error"):
            value = _real_number(getattr(self, name), name=name, minimum=0.0)
            checked[name] = value
        expected = checked["initial"] + checked["dynamic"]
        if not math.isclose(
            checked["total"], expected, rel_tol=2.0e-12, abs_tol=2.0e-14
        ):
            raise ValueError("total path KL is inconsistent with its components")
        if not isinstance(self.reference_initial, TiltedInitialLaw) or not isinstance(
            self.candidate_initial, TiltedInitialLaw
        ):
            raise TypeError("initial records must be TiltedInitialLaw instances")
        if not isinstance(self.occupancy, TimeIndexedOccupancy):
            raise TypeError("occupancy must be a TimeIndexedOccupancy")
        rates = _numeric_array(
            self.state_rate_divergence,
            name="state_rate_divergence",
            ndim=2,
        )
        expected_shape = self.occupancy.marginals.shape
        if rates.shape != expected_shape or np.any(rates < 0.0):
            raise ValueError(
                "state_rate_divergence must be nonnegative and match marginals"
            )
        evaluations = _nonnegative_integer(
            self.potential_evaluations,
            name="potential_evaluations",
            maximum=_MAX_POTENTIAL_EVALUATIONS,
        )
        for name, value in checked.items():
            object.__setattr__(self, name, value)
        object.__setattr__(
            self, "state_rate_divergence", _immutable_array(rates)
        )
        object.__setattr__(self, "potential_evaluations", evaluations)


def tilted_path_kl(
    base_initial: object,
    base_generator: object,
    reference_potential: PositivePotential,
    candidate_potential: PositivePotential,
    horizon: object,
    *,
    evaluation_times: object = None,
    rtol: object = 2.0e-10,
    atol: object = 2.0e-12,
    max_step: object = None,
    quadrature_epsabs: object = 1.0e-10,
    quadrature_epsrel: object = 1.0e-9,
    quadrature_limit: object = 1_000,
    max_potential_evaluations: object = 200_000,
) -> FiniteBridgePathKL:
    """Numerically return ``KL(reference tilted path || candidate path)``.

    Both paths use the same base generator and therefore have identical edge
    support.  The returned error is the adaptive quadrature estimate; it does
    not include ODE discretization error and is not an empirical certificate.
    """

    engine = _TiltEngine(np.asarray(base_generator))
    base_p = validate_probability_vector(np.asarray(base_initial), engine.state_count)
    (
        duration,
        relative,
        absolute,
        step,
        quad_absolute,
        quad_relative,
        quad_limit,
    ) = _numerical_controls(
        horizon,
        rtol,
        atol,
        max_step,
        quadrature_epsabs,
        quadrature_epsrel,
        quadrature_limit,
    )
    times = _evaluation_grid(duration, evaluation_times)
    budget = _EvaluationBudget(max_potential_evaluations)  # type: ignore[arg-type]
    reference_values = _potential_values(
        reference_potential, 0.0, engine.state_count, budget
    )
    candidate_values = _potential_values(
        candidate_potential, 0.0, engine.state_count, budget
    )
    reference_initial = _initial_from_values(base_p, reference_values, 0.0)
    candidate_initial = _initial_from_values(base_p, candidate_values, 0.0)
    initial_kl = _categorical_kl(
        reference_initial.probabilities, candidate_initial.probabilities
    )

    solution, marginals, ode_evaluations = _solve_marginal(
        reference_initial.probabilities,
        engine,
        reference_potential,
        duration,
        times,
        relative,
        absolute,
        step,
        budget,
    )

    if duration == 0.0:
        occupation = np.zeros(engine.state_count, dtype=float)
        dynamic = 0.0
        quadrature_error = 0.0
    else:
        def path_integrand(time: float) -> np.ndarray:
            marginal = _dense_marginal(
                solution, time, engine.state_count, absolute
            )
            exact_values = _potential_values(
                reference_potential, time, engine.state_count, budget
            )
            approximate_values = _potential_values(
                candidate_potential, time, engine.state_count, budget
            )
            exact_generator = engine.tilt(exact_values)
            approximate_generator = engine.tilt(approximate_values)
            rate_divergence = _state_rate_divergence(
                exact_generator, approximate_generator
            )
            dynamic_rate = float(marginal @ rate_divergence)
            if not math.isfinite(dynamic_rate) or dynamic_rate < 0.0:
                raise ArithmeticError("instantaneous path KL is invalid")
            return np.concatenate((marginal, np.asarray([dynamic_rate])))

        combined, quadrature_error = _quadrature(
            path_integrand,
            duration,
            quad_absolute,
            quad_relative,
            quad_limit,
        )
        occupation = combined[:-1]
        dynamic = float(combined[-1])
        tolerance = max(
            2.0e-9 * max(duration, 1.0),
            8.0 * quadrature_error,
            128.0 * absolute,
        )
        if np.any(occupation < -tolerance):
            raise ArithmeticError("integrated occupation became negative")
        occupation[occupation < 0.0] = 0.0
        if not math.isclose(
            math.fsum(float(value) for value in occupation),
            duration,
            rel_tol=0.0,
            abs_tol=tolerance,
        ):
            raise ArithmeticError("integrated occupation does not sum to horizon")
        if dynamic < 0.0 and dynamic >= -tolerance:
            dynamic = 0.0
        if not math.isfinite(dynamic) or dynamic < 0.0:
            raise ArithmeticError("dynamic path KL is not representable")

    occupancy = TimeIndexedOccupancy(
        initial_law=reference_initial,
        times=times,
        marginals=marginals,
        integrated_occupation=occupation,
        quadrature_error=quadrature_error,
        ode_evaluations=ode_evaluations,
        potential_evaluations=budget.count,
    )
    time_rates = []
    for direct_time in times:
        exact_values = _potential_values(
            reference_potential, float(direct_time), engine.state_count, budget
        )
        approximate_values = _potential_values(
            candidate_potential, float(direct_time), engine.state_count, budget
        )
        time_rates.append(
            _state_rate_divergence(
                engine.tilt(exact_values), engine.tilt(approximate_values)
            )
        )
    total = initial_kl + dynamic
    if not math.isfinite(total) or total < 0.0:
        raise ArithmeticError("total path KL is not representable")
    return FiniteBridgePathKL(
        initial=initial_kl,
        dynamic=dynamic,
        total=total,
        reference_initial=reference_initial,
        candidate_initial=candidate_initial,
        occupancy=occupancy,
        state_rate_divergence=np.vstack(time_rates),
        quadrature_error=quadrature_error,
        potential_evaluations=budget.count,
    )


@dataclass(frozen=True, eq=False)
class FiniteCTMCPathSample:
    """One exact thinning sample for a log-linearly tabulated tilt."""

    horizon: float
    initial_state: int
    jump_times: np.ndarray
    states: np.ndarray
    proposal_count: int
    rejected_count: int
    certified_rate_bound: float

    def __post_init__(self) -> None:
        horizon = _real_number(self.horizon, name="horizon", minimum=0.0)
        if isinstance(self.initial_state, (bool, np.bool_)) or not isinstance(
            self.initial_state, Integral
        ):
            raise TypeError("initial_state must be an integer")
        jump_times = _numeric_array(self.jump_times, name="jump_times", ndim=1)
        states_raw = np.asarray(self.states)
        if states_raw.dtype.kind == "b" or states_raw.dtype.kind not in "iu":
            raise TypeError("states must have an integer non-boolean dtype")
        states = np.asarray(states_raw, dtype=np.int64)
        if states.ndim != 1 or states.size != jump_times.size + 1:
            raise ValueError("states must contain the initial and every post-jump state")
        if states.size == 0 or int(states[0]) != int(self.initial_state):
            raise ValueError("states must begin with initial_state")
        if np.any(states < 0):
            raise ValueError("states must be nonnegative")
        if jump_times.size > 0 and (
            np.any(np.diff(jump_times) <= 0.0)
            or jump_times[0] <= 0.0
            or jump_times[-1] > horizon
        ):
            raise ValueError("jump_times must be strictly increasing within the horizon")
        proposals = _nonnegative_integer(
            self.proposal_count,
            name="proposal_count",
            maximum=_MAX_SAMPLER_PROPOSALS,
        )
        rejected = _nonnegative_integer(
            self.rejected_count,
            name="rejected_count",
            maximum=_MAX_SAMPLER_PROPOSALS,
        )
        if rejected > proposals or jump_times.size != proposals - rejected:
            raise ValueError("proposal, rejection, and jump counts are inconsistent")
        bound = _real_number(
            self.certified_rate_bound,
            name="certified_rate_bound",
            minimum=0.0,
        )
        object.__setattr__(self, "horizon", horizon)
        object.__setattr__(self, "initial_state", int(self.initial_state))
        object.__setattr__(self, "jump_times", _immutable_array(jump_times))
        object.__setattr__(
            self, "states", _immutable_array(states, dtype=np.dtype(np.int64))
        )
        object.__setattr__(self, "proposal_count", proposals)
        object.__setattr__(self, "rejected_count", rejected)
        object.__setattr__(self, "certified_rate_bound", bound)


def _tabulated_exit_rate_bound(
    engine: _TiltEngine, potential: TabulatedPositivePotential
) -> float:
    if potential.state_count != engine.state_count:
        raise ValueError("tabulated potential state count does not match generator")
    maximum = 0.0
    for values in potential.values:
        generator = engine.tilt(values)
        maximum = max(maximum, float(np.max(-np.diag(generator))))
    if maximum == 0.0:
        return 0.0
    bound = math.nextafter(maximum, math.inf)
    if not math.isfinite(bound):
        raise ArithmeticError("certified sampler rate bound is not finite")
    return bound


def _validated_seed(seed: object) -> Optional[int]:
    if seed is None:
        return None
    if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, Integral):
        raise TypeError("seed must be an integer non-boolean value or None")
    result = int(seed)
    if result < 0 or result > _MAX_SEED:
        raise ValueError("seed is outside the supported uint64 range")
    return result


def sample_tabulated_tilted_path(
    base_initial: object,
    base_generator: object,
    potential: TabulatedPositivePotential,
    *,
    seed: object = None,
    max_proposals: object = 100_000,
    max_jumps: object = 100_000,
) -> FiniteCTMCPathSample:
    """Exactly sample the log-linearly interpolated tilted CTMC by thinning.

    Only :class:`TabulatedPositivePotential` is accepted.  For an arbitrary
    callable, values at finitely many checked times cannot certify a bound on
    unobserved rate peaks, so this function fails closed rather than accepting
    a user-asserted envelope.
    """

    if not isinstance(potential, TabulatedPositivePotential):
        raise TypeError(
            "exact bounded sampling requires a TabulatedPositivePotential"
        )
    if potential.start_time != 0.0:
        raise ValueError("tabulated sampler potential must begin at direct time 0")
    engine = _TiltEngine(np.asarray(base_generator))
    initial = validate_probability_vector(
        np.asarray(base_initial), engine.state_count
    )
    proposal_limit = _positive_integer(
        max_proposals,
        name="max_proposals",
        maximum=_MAX_SAMPLER_PROPOSALS,
    )
    jump_limit = _positive_integer(
        max_jumps, name="max_jumps", maximum=_MAX_SAMPLER_JUMPS
    )
    horizon = potential.end_time
    bound = _tabulated_exit_rate_bound(engine, potential)
    scaled_rate = bound * horizon
    if not math.isfinite(scaled_rate) or scaled_rate > _MAX_SCALED_EXIT_RATE:
        raise ValueError("certified exit-rate bound times horizon is too large")
    initial_law = conditional_initial_law(initial, potential, 0.0)
    generator = np.random.default_rng(_validated_seed(seed))
    state = int(generator.choice(engine.state_count, p=initial_law.probabilities))
    initial_state = state
    direct_time = 0.0
    proposals = 0
    rejected = 0
    jump_times = []
    states = [state]
    if bound > 0.0:
        while True:
            direct_time += float(generator.exponential(1.0 / bound))
            if direct_time > horizon:
                break
            proposals += 1
            if proposals > proposal_limit:
                raise RuntimeError("sampler exceeded max_proposals")
            tilted = engine.tilt(potential(direct_time))
            exit_rate = float(-tilted[state, state])
            tolerance = 64.0 * np.finfo(np.float64).eps * max(bound, 1.0)
            if exit_rate > bound + tolerance:
                raise ArithmeticError(
                    "runtime exit rate exceeded the certified tabulated bound"
                )
            if exit_rate == 0.0 or float(generator.random()) * bound >= exit_rate:
                rejected += 1
                continue
            rates = tilted[state].copy()
            rates[state] = 0.0
            probabilities = rates / exit_rate
            destination = int(generator.choice(engine.state_count, p=probabilities))
            if destination == state or tilted[state, destination] <= 0.0:
                raise ArithmeticError("sampler selected an invalid destination")
            state = destination
            jump_times.append(direct_time)
            states.append(state)
            if len(jump_times) > jump_limit:
                raise RuntimeError("sampler exceeded max_jumps")
    return FiniteCTMCPathSample(
        horizon=horizon,
        initial_state=initial_state,
        jump_times=np.asarray(jump_times, dtype=float),
        states=np.asarray(states, dtype=np.int64),
        proposal_count=proposals,
        rejected_count=rejected,
        certified_rate_bound=bound,
    )


__all__ = [
    "FiniteBridgePathKL",
    "FiniteCTMCPathSample",
    "PositivePotential",
    "TabulatedPositivePotential",
    "TiltedInitialLaw",
    "TimeIndexedOccupancy",
    "conditional_initial_law",
    "integrate_tilted_occupancy",
    "potential_tilted_generator",
    "sample_tabulated_tilted_path",
    "tilted_path_kl",
]
