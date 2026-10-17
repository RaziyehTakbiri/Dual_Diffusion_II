"""Immutable, bounded coordinate residual for one declared macro-grid node.

For a finite coefficient tuple and remaining time tau, this component represents
    r(z) = tau * sum_k c_k T_k(tanh(z / scale)).
The exact discrete fiber and grid node are selected by the caller: this class
does not encode metadata, fit coefficients, interpolate time, or integrate a
sampler.  A degree-zero instance supplies an atomic-fiber constant.  A terminal
instance (tau=0) returns exact floating-point zeros for value and derivatives.

Since |T_k(s)| <= 1 on [-1,1], the real-arithmetic bound is
    |r(z)| <= tau * sum_k |c_k|.
The reported floating-point evaluation of that expression is NOT rounded
outward and is NOT a sampler-safe rejection envelope or a floating-point error
certificate.  Analytic derivatives below are coordinate derivatives, not time
derivatives.  A caller cannot infer continuous-time regularity from independent
fits at different macro nodes.

This new NumPy-only diagnostic component neither changes the existing bounded
neural conditioners nor grants scientific/model/sampler admission.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real

import numpy as np
from numpy.polynomial.chebyshev import chebvander


MAXIMUM_DEGREE = 128


def _finite(value, name):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
        raise ValueError(f'{name} must be a finite real number')
    return float(value)


def _settings(remaining_time, coordinate_scale):
    remaining_time = _finite(remaining_time, 'remaining_time')
    coordinate_scale = _finite(coordinate_scale, 'coordinate_scale')
    if remaining_time < 0:
        raise ValueError('remaining_time must be nonnegative')
    if coordinate_scale <= 0:
        raise ValueError('coordinate_scale must be positive')
    return remaining_time, coordinate_scale


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


def design(z, degree, remaining_time=1., coordinate_scale=2.):
    """Return (value, gradient, Hessian) basis matrices with a final basis axis.

    For coordinates of shape S, each returned array has shape S+(degree+1,).
    Thus scalar input returns three vectors; an n-vector returns n-by-(d+1)
    matrices.  Multiplying each matrix by the same coefficient vector gives
    the residual and its first/second coordinate derivatives.  Degree is a
    declared diagnostic resource limit, not a silent truncation of a series.

    Values use chebvander.  Derivatives use differentiated three-term
    recurrences, followed by ds/dz=(1-s*s)/scale and
    d2s/dz2=-2*s*(1-s*s)/scale**2.  The latter is evaluated as
    -2*s*(ds/dz)/scale to avoid prematurely squaring a very small scale.
    """
    if type(degree) is not int or not 0 <= degree <= MAXIMUM_DEGREE:
        raise ValueError(f'degree must be an integer in [0,{MAXIMUM_DEGREE}]')
    remaining_time, coordinate_scale = _settings(remaining_time, coordinate_scale)
    coordinates = _coordinates(z)
    shape = coordinates.shape + (degree + 1,)
    if remaining_time == 0:
        return tuple(np.zeros(shape, dtype=np.float64) for _ in range(3))
    if degree == 0:
        return (np.full(shape, remaining_time, dtype=np.float64),
                np.zeros(shape, dtype=np.float64), np.zeros(shape, dtype=np.float64))
    # A finite z/scale can overflow in floating point even though tanh has a
    # finite limiting value.  Saturation to +/-1 is allowed; it is not a claim
    # that the floating-point result equals the mathematical derivative.
    with np.errstate(over='ignore', invalid='raise', divide='raise'):
        compact = np.tanh(coordinates / coordinate_scale)
    values = chebvander(compact, degree).reshape(shape)
    first = np.zeros_like(values)
    second = np.zeros_like(values)
    first[..., 1] = 1.
    for k in range(1, degree):
        first[..., k + 1] = 2 * values[..., k] + 2 * compact * first[..., k] - first[..., k - 1]
        second[..., k + 1] = 4 * first[..., k] + 2 * compact * second[..., k] - second[..., k - 1]
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        ds = (1 - compact * compact) / coordinate_scale
        d2s = -2 * compact * ds / coordinate_scale
        value_matrix = remaining_time * values
        gradient_matrix = remaining_time * first * ds[..., None]
        hessian_matrix = remaining_time * (second * ds[..., None] ** 2 + first * d2s[..., None])
    outputs = value_matrix, gradient_matrix, hessian_matrix
    if not all(np.all(np.isfinite(array)) for array in outputs):
        raise ArithmeticError('residual basis or coordinate derivatives are not representable')
    return outputs


@dataclass(frozen=True)
class CompactFiberResidual:
    """One frozen coefficient vector and terminal gate for one declared fiber/node."""

    coefficients: tuple[float, ...]
    remaining_time: float
    coordinate_scale: float = 2.

    def __post_init__(self):
        if type(self.coefficients) is not tuple or not 1 <= len(self.coefficients) <= MAXIMUM_DEGREE + 1:
            raise ValueError(f'coefficients must be a nonempty tuple of at most {MAXIMUM_DEGREE + 1} values')
        coefficients = tuple(_finite(value, 'coefficient') for value in self.coefficients)
        remaining_time, coordinate_scale = _settings(self.remaining_time, self.coordinate_scale)
        object.__setattr__(self, 'coefficients', coefficients)
        object.__setattr__(self, 'remaining_time', remaining_time)
        object.__setattr__(self, 'coordinate_scale', coordinate_scale)
        self.real_arithmetic_bound  # Refuse an unrepresentable declared bound.

    @property
    def degree(self):
        return len(self.coefficients) - 1

    @property
    def real_arithmetic_bound(self):
        """Evaluation of tau*||c||_1, NOT an FP-safe or outward-rounded bound."""
        if self.remaining_time == 0:
            return 0.
        try:
            result = math.fsum(self.remaining_time * abs(value) for value in self.coefficients)
        except OverflowError as exc:
            raise ArithmeticError('real-arithmetic bound is not representable') from exc
        if not math.isfinite(result):
            raise ArithmeticError('real-arithmetic bound is not representable')
        return result

    def evaluate(self, z):
        """Return fresh value/gradient/Hessian arrays with the input coordinate shape."""
        matrices = design(z, self.degree, self.remaining_time, self.coordinate_scale)
        if self.remaining_time == 0:
            # Do not multiply terminal zeros by huge coefficients or rely on
            # cancellation.  They remain exact zeros on every finite input.
            return {name: np.zeros(matrix.shape[:-1], dtype=np.float64)
                    for name, matrix in zip(('value', 'gradient', 'hessian'), matrices)}
        with np.errstate(over='ignore', invalid='ignore'):
            result = {name: np.asarray(matrix @ np.asarray(self.coefficients, dtype=np.float64))
                      for name, matrix in zip(('value', 'gradient', 'hessian'), matrices)}
        if not all(np.all(np.isfinite(array)) for array in result.values()):
            raise ArithmeticError('residual evaluation is not representable')
        return result
