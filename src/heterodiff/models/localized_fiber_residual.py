"""Frozen, localized C2 residual for one externally declared fiber/grid node.

The caller supplies value/score/Hessian jets of the quotient q=d/tau at raw
coordinate knots.  Each core interval is the unique quintic Hermite polynomial,
stored as six Bernstein (Bezier) controls.  One explicit collar on each side
joins the endpoint jet to the *same endpoint value* with zero first and second
derivatives at the outer edge.  Beyond those collars the function is constant.
The collars can overshoot the endpoint value; their controls are included in
the bound.  No coordinate is silently clamped to the fitted core interval.

The returned residual is r=tau*q.  Its real-arithmetic value bound follows from
the convex hull of every interval's Bernstein controls (including collars):
    |r(z)| <= tau * max_{interval,k} |b[interval,k]|.
The floating-point evaluation of this expression is NOT outward rounded and
is NOT a sampler-safe envelope or floating-point error certificate.  C2 joins
and fourth-order finite differences are mathematical statements whose finite
precision evaluations are tested, not certified exact arithmetic.

This module fits no targets, owns no metadata vocabulary, interpolates no time,
and changes no prior model, sampler or acceptance tolerance.  Each instance
belongs to one caller-selected discrete fiber and common-grid node.  A terminal
instance returns exact floating-point zeros after validating its input.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real

import numpy as np


MAXIMUM_CORE_CELLS = 1024


def _finite(value, name):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
        raise ValueError(f'{name} must be a finite real number')
    return float(value)


def _tuple(values, name, length=None):
    if type(values) is not tuple or (length is not None and len(values) != length):
        raise ValueError(f'{name} must be a tuple' + (f' of length {length}' if length is not None else ''))
    return tuple(_finite(value, name) for value in values)


def _knots(values, minimum=2):
    knots = _tuple(values, 'knots')
    if not minimum <= len(knots) <= MAXIMUM_CORE_CELLS + 1:
        raise ValueError(f'knots require {minimum} to {MAXIMUM_CORE_CELLS + 1} entries')
    gaps = tuple(right - left for left, right in zip(knots, knots[1:]))
    if any(not math.isfinite(gap) or gap <= 0 for gap in gaps):
        raise ValueError('knots must increase strictly with finite positive interval widths')
    return knots, gaps


def _coordinates(z):
    if np.ma.isMaskedArray(z):
        raise ValueError('masked coordinates are not supported')
    raw = np.asarray(z)
    if raw.dtype.kind not in 'fiu':
        raise ValueError('coordinates must be real numeric values, not booleans or complex values')
    with np.errstate(over='ignore', invalid='ignore'):
        result = np.asarray(raw, dtype=np.float64)
    if not np.all(np.isfinite(result)):
        raise ValueError('coordinates must be finite and representable as float64')
    return result


def _controls(left, right, value_left, value_right, gradient_left, gradient_right, hessian_left, hessian_right):
    width = right - left
    # Ordered products avoid forming width**2 prematurely when Hessian=0.
    first_left, first_right = (width / 5) * gradient_left, (width / 5) * gradient_right
    second_left = (width / 20) * (width * hessian_left)
    second_right = (width / 20) * (width * hessian_right)
    result = (value_left, value_left + first_left, value_left + 2 * first_left + second_left,
              value_right - 2 * first_right + second_right, value_right - first_right, value_right)
    if not all(math.isfinite(value) for value in result):
        raise ArithmeticError('quintic Bernstein controls are not representable')
    return result


def _derivative_controls(controls, width):
    first = tuple(5 * ((right - left) / width) for left, right in zip(controls, controls[1:]))
    # This is 20*(b[k+2]-2*b[k+1]+b[k])/width**2, factored as
    # the derivative of the degree-four first-derivative Bezier polynomial.
    second = tuple(4 * ((right - left) / width) for left, right in zip(first, first[1:]))
    if not all(math.isfinite(value) for value in first + second):
        raise ArithmeticError('Bernstein derivative controls are not representable')
    return first, second


def _de_casteljau(controls, parameters):
    """Row-wise de Casteljau, one interval and t in [0,1] per row."""
    work = np.array(controls, dtype=np.float64, copy=True)
    left, right = (1 - parameters)[:, None], parameters[:, None]
    for length in range(work.shape[1] - 1, 0, -1):
        work[:, :length] = left * work[:, :length] + right * work[:, 1:length + 1]
    return work[:, 0]


@dataclass(frozen=True, init=False)
class LocalizedFiberResidual:
    """Immutable complete piecewise controls; construct through from_jets only."""

    knots: tuple[float, ...]
    controls: tuple[tuple[float, ...], ...]
    core_knots: tuple[float, ...]
    remaining_time: float
    collar_width: float
    _first_controls: tuple[tuple[float, ...], ...]
    _second_controls: tuple[tuple[float, ...], ...]

    def __init__(self, *args, **kwargs):
        raise TypeError('use LocalizedFiberResidual.from_jets for validated C2 construction')

    @classmethod
    def from_jets(cls, knots, values, gradients, hessians, remaining_time, collar_width=1.):
        """Build quotient-q interpolation and apply remaining time only at evaluation.

        All four data inputs must be tuples.  Values, gradients and Hessians
        are coordinate jets of q, NOT of the gated residual tau*q.  The two
        added collars have the requested raw-coordinate width; the constructor
        refuses widths that cannot advance their endpoint in floating point.
        """
        core, _ = _knots(knots)
        values = _tuple(values, 'values', len(core))
        gradients = _tuple(gradients, 'gradients', len(core))
        hessians = _tuple(hessians, 'hessians', len(core))
        remaining_time = _finite(remaining_time, 'remaining_time')
        collar_width = _finite(collar_width, 'collar_width')
        if remaining_time < 0 or collar_width <= 0:
            raise ValueError('remaining_time must be nonnegative and collar_width positive')
        outer_left, outer_right = core[0] - collar_width, core[-1] + collar_width
        if (not math.isfinite(outer_left) or not math.isfinite(outer_right)
                or not outer_left < core[0] or not core[-1] < outer_right):
            raise ValueError('collar endpoints are not representable beyond the core')
        full_knots = (outer_left,) + core + (outer_right,)
        full_values = (values[0],) + values + (values[-1],)
        full_gradients = (0.,) + gradients + (0.,)
        full_hessians = (0.,) + hessians + (0.,)
        controls, first_controls, second_controls = [], [], []
        for index, (left, right) in enumerate(zip(full_knots, full_knots[1:])):
            if not math.isfinite(right - left) or right - left <= 0:
                raise ArithmeticError('complete interval width is not representable')
            control = _controls(left, right, full_values[index], full_values[index + 1],
                full_gradients[index], full_gradients[index + 1], full_hessians[index], full_hessians[index + 1])
            first, second = _derivative_controls(control, right - left)
            controls.append(control)
            first_controls.append(first)
            second_controls.append(second)
        result = object.__new__(cls)
        for name, value in (
                ('knots', full_knots), ('controls', tuple(controls)), ('core_knots', core),
                ('remaining_time', remaining_time), ('collar_width', collar_width),
                ('_first_controls', tuple(first_controls)), ('_second_controls', tuple(second_controls))):
            object.__setattr__(result, name, value)
        result.real_arithmetic_bound  # Refuse an unrepresentable declared value bound.
        return result

    @property
    def real_arithmetic_bound(self):
        """tau*maximum absolute control, NOT an FP-safe or outward-rounded bound."""
        if self.remaining_time == 0:
            return 0.
        result = self.remaining_time * max(abs(value) for row in self.controls for value in row)
        if not math.isfinite(result):
            raise ArithmeticError('real-arithmetic residual bound is not representable')
        return result

    def evaluate(self, z):
        """Evaluate gated residual value/gradient/Hessian with constant outer tails.

        At an interior knot the right-hand cell is selected deterministically.
        The shared input jets make either cell agree through the second
        derivative in real arithmetic.  Beyond the complete knot interval,
        the same endpoint value is retained and derivatives are exactly zero.
        """
        coordinates = _coordinates(z)
        result = {name: np.zeros(coordinates.shape, dtype=np.float64)
                  for name in ('value', 'gradient', 'hessian')}
        if self.remaining_time == 0 or coordinates.size == 0:
            return result
        flat = coordinates.reshape(-1)
        left_tail, right_tail = flat <= self.knots[0], flat >= self.knots[-1]
        interior = ~(left_tail | right_tail)
        value = result['value'].reshape(-1)
        value[left_tail] = self.remaining_time * self.controls[0][0]
        value[right_tail] = self.remaining_time * self.controls[-1][-1]
        if np.any(interior):
            points = flat[interior]
            knots = np.asarray(self.knots, dtype=np.float64)
            indices = np.searchsorted(knots, points, side='right') - 1
            widths = knots[indices + 1] - knots[indices]
            parameters = (points - knots[indices]) / widths
            if not np.all((parameters >= 0) & (parameters <= 1)):
                raise ArithmeticError('interior Bezier parameter is outside its interval')
            with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
                for name, controls in (('value', self.controls), ('gradient', self._first_controls),
                                       ('hessian', self._second_controls)):
                    result[name].reshape(-1)[interior] = self.remaining_time * _de_casteljau(
                        np.asarray(controls, dtype=np.float64)[indices], parameters)
        if not all(np.all(np.isfinite(array)) for array in result.values()):
            raise ArithmeticError('localized residual evaluation is not representable')
        return result


def estimate_hessians_from_scores(knots, gradients):
    """Estimate q'' from q' on a uniform grid with fourth-order five-point rules.

    This uses scores only, not target Hessian queries.  Five-point one-sided
    stencils are used at the first two and last two nodes.  On the interior,
    the centered weights are (1,-8,0,8,-1)/(12*h).  Smoothness, noise and finite
    precision govern the actual error; no error certificate is supplied.
    """
    knots, widths = _knots(knots, minimum=5)
    gradients = _tuple(gradients, 'gradients', len(knots))
    width = (knots[-1] - knots[0]) / (len(knots) - 1)
    if not math.isfinite(width) or width <= 0 or not np.allclose(widths, width, rtol=1e-12, atol=0.):
        raise ValueError('score-derived Hessians require a representable uniform knot grid')
    data = np.asarray(gradients, dtype=np.float64)
    result = np.empty_like(data)
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        # Divide successively: 12*width can overflow even when the desired
        # derivative is representable (large but finite raw-coordinate grids).
        result[0] = np.dot((-25., 48., -36., 16., -3.), data[:5]) / width / 12
        result[1] = np.dot((-3., -10., 18., -6., 1.), data[:5]) / width / 12
        result[-1] = -np.dot((-25., 48., -36., 16., -3.), data[-5:][::-1]) / width / 12
        result[-2] = -np.dot((-3., -10., 18., -6., 1.), data[-5:][::-1]) / width / 12
        result[2:-2] = (data[:-4] - 8 * data[1:-3] + 8 * data[3:-1] - data[4:]) / width / 12
    if not np.all(np.isfinite(result)):
        raise ArithmeticError('score-derived Hessians are not representable')
    return tuple(float(value) for value in result)
