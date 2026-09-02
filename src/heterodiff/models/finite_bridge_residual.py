"""Finite association-guide residual utilities.

These helpers keep three quantities distinct:

* a physical information density ``h_t(x; a)`` relative to the declared
  observation reference;
* the classifier logit ``log h_t(x; a) - log p_A(a)``; and
* the physical residual ``log h_t - log bar_h_t``.

The module is NumPy-only and contains no learned performance claim.  It is
used to falsify gauge, terminal-boundary, and common-potential plumbing before
the optional neural comparison is run.
"""

from __future__ import annotations

import math
from numbers import Real
from typing import Callable

import numpy as np


_MAX_GRID_ENTRIES = 2_000_000
_MAX_ABSOLUTE_LOG_VALUE = 50.0


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    contiguous = np.array(array, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=np.float64
    ).reshape(contiguous.shape)


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
    array = raw.astype(float, copy=True)
    if array.ndim != ndim or any(size <= 0 for size in array.shape):
        raise ValueError("%s must be a nonempty %d-dimensional array" % (name, ndim))
    if array.size > _MAX_GRID_ENTRIES:
        raise ValueError(
            "%s exceeds the work limit of %d entries"
            % (name, _MAX_GRID_ENTRIES)
        )
    if not np.all(np.isfinite(array)):
        raise ValueError("%s entries must be finite" % name)
    return array


def _positive_array(value: object, *, name: str, ndim: int) -> np.ndarray:
    array = _numeric_array(value, name=name, ndim=ndim)
    if np.any(array <= 0.0):
        raise ValueError("%s entries must be strictly positive" % name)
    return array


def _positive_finite_real(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError("%s must be finite and strictly positive" % name)
    return result


def classifier_guide_log_grid(
    guide_information_density: object,
    observation_marginal_density: object,
) -> np.ndarray:
    """Return the guide in the exact joint-versus-product classifier gauge.

    ``guide_information_density`` has shape ``[time, state, observation]`` and
    is a density relative to the same finite observation reference as
    ``observation_marginal_density``.  Subtracting the latter is necessary:
    omitting it creates an observation-only gauge discrepancy even when the
    physical guide is exact.
    """

    guide = _positive_array(
        guide_information_density,
        name="guide_information_density",
        ndim=3,
    )
    marginal = _positive_array(
        observation_marginal_density,
        name="observation_marginal_density",
        ndim=1,
    )
    if marginal.shape != (guide.shape[2],):
        raise ValueError(
            "observation_marginal_density must match the observation axis"
        )
    result = np.log(guide) - np.log(marginal)[None, None, :]
    if not np.all(np.isfinite(result)):
        raise ArithmeticError("classifier guide logits are not representable")
    return _immutable_float_array(result)


def exact_residual_log_grid(
    exact_information_density: object,
    guide_information_density: object,
) -> np.ndarray:
    """Return the physical residual ``log h_star - log bar_h``."""

    exact = _positive_array(
        exact_information_density,
        name="exact_information_density",
        ndim=3,
    )
    guide = _positive_array(
        guide_information_density,
        name="guide_information_density",
        ndim=3,
    )
    if exact.shape != guide.shape:
        raise ValueError("exact and guide information grids must have one shape")
    result = np.log(exact) - np.log(guide)
    if not np.all(np.isfinite(result)):
        raise ArithmeticError("exact residual values are not representable")
    return _immutable_float_array(result)


def compose_guided_log_information(
    guide_log_information: object,
    residual_log_grid: object,
) -> np.ndarray:
    """Compose a guide and residual without changing their physical gauge."""

    guide = _numeric_array(
        guide_log_information, name="guide_log_information", ndim=3
    )
    residual = _numeric_array(
        residual_log_grid, name="residual_log_grid", ndim=3
    )
    if guide.shape != residual.shape:
        raise ValueError("guide and residual log grids must have one shape")
    result = guide + residual
    if np.max(np.abs(result)) > _MAX_ABSOLUTE_LOG_VALUE:
        raise ValueError("composed absolute log information must not exceed 50")
    return _immutable_float_array(result)


def terminal_zero_bounded_residual(
    raw_output: object,
    direct_times: object,
    terminal_time: object,
    log_bound: object,
) -> np.ndarray:
    """Apply the frozen terminal-zero residual parameterization.

    The first axis of ``raw_output`` is time.  The returned value is
    ``(T-t) * B * tanh(raw_output / B)`` and therefore has an exact zero
    terminal row whenever the supplied time grid contains ``T``.  Scaling the
    tanh argument makes the safety map have unit derivative at zero and avoids
    magnifying early optimization gradients when ``B`` is deliberately loose.
    """

    raw = _numeric_array(raw_output, name="raw_output", ndim=3)
    times = _numeric_array(direct_times, name="direct_times", ndim=1)
    if times.shape != (raw.shape[0],):
        raise ValueError("direct_times must match the raw_output time axis")
    if np.any(times < 0.0) or np.any(np.diff(times) <= 0.0):
        raise ValueError("direct_times must be nonnegative and strictly increasing")
    terminal = _positive_finite_real(terminal_time, name="terminal_time")
    bound = _positive_finite_real(log_bound, name="log_bound")
    if bound > 2048.0:
        raise ValueError("log_bound exceeds the frozen A1 ceiling of 2048")
    tolerance = 32.0 * np.finfo(np.float64).eps * max(1.0, terminal)
    if times[-1] > terminal + tolerance:
        raise ValueError("direct_times must not exceed terminal_time")
    remaining = terminal - times
    remaining[np.abs(remaining) <= tolerance] = 0.0
    if np.any(remaining < 0.0):
        raise ValueError("direct_times must not exceed terminal_time")
    result = remaining[:, None, None] * bound * np.tanh(raw / bound)
    return _immutable_float_array(result)


class GuidedResidualPotential:
    """Positive analytic guide multiplied by a tabulated log residual.

    The guide remains continuous in direct process time.  Only the residual is
    interpolated linearly in log space.  The terminal residual row must be zero
    within the declared tolerance, preventing an approximate boundary from
    being silently presented as the same-terminal-law estimator.
    """

    def __init__(
        self,
        guide_potential: Callable[[float], np.ndarray],
        direct_times: object,
        residual_log_grid: object,
        *,
        terminal_tolerance: object = 1.0e-10,
    ) -> None:
        if not callable(guide_potential):
            raise TypeError("guide_potential must be callable")
        times = _numeric_array(direct_times, name="direct_times", ndim=1)
        residual = _numeric_array(
            residual_log_grid, name="residual_log_grid", ndim=2
        )
        if times.size < 2 or np.any(times < 0.0) or np.any(np.diff(times) <= 0.0):
            raise ValueError(
                "direct_times must contain at least two increasing nonnegative knots"
            )
        if residual.shape[0] != times.size:
            raise ValueError("residual rows must match direct_times")
        if np.max(np.abs(residual)) > _MAX_ABSOLUTE_LOG_VALUE:
            raise ValueError("absolute residual log values must not exceed 50")
        tolerance = _positive_finite_real(
            terminal_tolerance, name="terminal_tolerance"
        )
        if np.max(np.abs(residual[-1])) > tolerance:
            raise ValueError("terminal residual must be zero within tolerance")

        first = _positive_array(
            guide_potential(float(times[0])), name="guide_potential(start)", ndim=1
        )
        last = _positive_array(
            guide_potential(float(times[-1])), name="guide_potential(end)", ndim=1
        )
        if first.shape != (residual.shape[1],) or last.shape != first.shape:
            raise ValueError("guide potential state dimension is inconsistent")

        self._guide_potential = guide_potential
        self._direct_times = _immutable_float_array(times)
        self._residual_log_grid = _immutable_float_array(residual)
        self._terminal_tolerance = tolerance

    @property
    def direct_times(self) -> np.ndarray:
        return self._direct_times

    @property
    def residual_log_grid(self) -> np.ndarray:
        return self._residual_log_grid

    @property
    def state_count(self) -> int:
        return int(self._residual_log_grid.shape[1])

    @property
    def terminal_tolerance(self) -> float:
        return self._terminal_tolerance

    def residual_log_vector(self, direct_time: object) -> np.ndarray:
        if isinstance(direct_time, (bool, np.bool_)) or not isinstance(
            direct_time, Real
        ):
            raise TypeError("direct_time must be a real non-boolean number")
        time = float(direct_time)
        if not math.isfinite(time):
            raise ValueError("direct_time must be finite")
        if time < self._direct_times[0] or time > self._direct_times[-1]:
            raise ValueError("direct_time lies outside the residual grid")
        if time == self._direct_times[-1]:
            return _immutable_float_array(self._residual_log_grid[-1])
        right = int(np.searchsorted(self._direct_times, time, side="right"))
        if right == 0:
            return _immutable_float_array(self._residual_log_grid[0])
        left = right - 1
        fraction = (time - self._direct_times[left]) / (
            self._direct_times[right] - self._direct_times[left]
        )
        result = (
            (1.0 - fraction) * self._residual_log_grid[left]
            + fraction * self._residual_log_grid[right]
        )
        return _immutable_float_array(result)

    def log_potential_vector(self, direct_time: object) -> np.ndarray:
        residual = self.residual_log_vector(direct_time)
        guide = _positive_array(
            self._guide_potential(float(direct_time)),
            name="guide_potential(time)",
            ndim=1,
        )
        if guide.shape != (self.state_count,):
            raise ValueError("guide potential changed its state dimension")
        result = np.log(guide) + residual
        if np.max(np.abs(result)) > _MAX_ABSOLUTE_LOG_VALUE:
            raise ArithmeticError("composite log potential exceeds 50")
        return _immutable_float_array(result)

    def __call__(self, direct_time: object) -> np.ndarray:
        result = np.exp(self.log_potential_vector(direct_time))
        if np.any(result <= 0.0) or not np.all(np.isfinite(result)):
            raise ArithmeticError("guided residual potential is not representable")
        return _immutable_float_array(result)


__all__ = [
    "GuidedResidualPotential",
    "classifier_guide_log_grid",
    "compose_guided_log_information",
    "exact_residual_log_grid",
    "terminal_zero_bounded_residual",
]
