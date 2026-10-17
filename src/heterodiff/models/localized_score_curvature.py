"""Separate seven-point score differentiation; previous FD5 rules stay unchanged.

At every uniform-grid knot this differentiates the degree-six interpolant of
seven supplied scores.  Interior stencils are centered; the first/last three
use shifted one-sided stencils on the first/last seven knots.  Weights are
derived exactly as Fractions, then evaluated in floating point without solving
a numerical linear system.  Under a C7 score and exact input the truncation
error is O(h**6); noisy scores and floating point need separate error analysis.
This does not increase the underlying quintic Hermite interpolation order.
"""

from fractions import Fraction
from functools import lru_cache
import math
from numbers import Real

import numpy as np


MAXIMUM_KNOTS = 1025


@lru_cache(maxsize=7)
def fd7_weights(position):
    """Exact dimensionless derivative weights at position 0,...,6 on knots 0,...,6."""
    if type(position) is not int or not 0 <= position <= 6:
        raise ValueError('stencil position must be an integer in [0,6]')
    answer = []
    for j in range(7):
        if j == position:
            answer.append(sum((Fraction(1, position-m) for m in range(7) if m != position), Fraction(0)))
        else:
            numerator = math.prod(position-m for m in range(7) if m not in (j, position))
            denominator = math.prod(j-m for m in range(7) if m != j)
            answer.append(Fraction(numerator, denominator))
    return tuple(answer)


def _tuple(values, name):
    if type(values) is not tuple:
        raise ValueError(f'{name} must be an immutable tuple')
    answer = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
            raise ValueError(f'{name} must contain finite real values')
        answer.append(float(value))
    return tuple(answer)


def estimate_hessians_from_scores_fd7(knots, gradients):
    """Return score-derived curvature at the same knots; no Hessian-label argument."""
    knots, gradients = _tuple(knots, 'knots'), _tuple(gradients, 'gradients')
    if not 7 <= len(knots) <= MAXIMUM_KNOTS or len(gradients) != len(knots):
        raise ValueError('aligned knots and scores require 7 to 1025 entries')
    widths = tuple(b-a for a, b in zip(knots, knots[1:]))
    width = (knots[-1]-knots[0])/(len(knots)-1)
    if (not math.isfinite(width) or width <= 0
            or any(not math.isfinite(w) or w <= 0 for w in widths)
            or not np.allclose(widths, width, rtol=1e-12, atol=0.)):
        raise ValueError('a representable strictly increasing uniform knot grid is required')
    answer = []
    for i in range(len(knots)):
        start = min(max(i-3, 0), len(knots)-7)
        weights = fd7_weights(i-start)
        # Subtracting the score at the evaluation knot exploits the exact
        # zero sum of derivative weights and keeps constant scores exactly zero.
        try:
            value = math.fsum(float(w)*(gradients[start+j]-gradients[i]) for j, w in enumerate(weights))/width
        except (OverflowError, ValueError) as exc:
            raise ArithmeticError('FD7 score derivative is not representable') from exc
        if not math.isfinite(value):
            raise ArithmeticError('FD7 score derivative is not representable')
        answer.append(value)
    return tuple(answer)
