"""Exact association likelihood for unordered, partially detected anchors.

This module is a small oracle for one classical finite-set calculation.  It is
not a methodological novelty claim.

Fix ``n`` terminal events.  The events are temporarily indexed only to
evaluate their likelihoods.  Event ``i`` is detected independently with
probability ``d[i]``.  Conditional on detection, ``L[j, i]`` is the density of
observed anchor ``j`` under event ``i``.  The anchors themselves form an
unordered multiset of cardinality ``r``.  Their density is taken relative to
the unnormalised finite-set (Lebesgue--Poisson) reference

``(1 / r!) product_j mu(d anchor_j)``.

Under that convention the exact density is

``sum_phi product_j d[phi(j)] L[j, phi(j)]
         product_{i not in image(phi)} (1 - d[i])``,

where the sum ranges over injective anchor-to-event maps.  No additional
factorial belongs in the formula: the injection sum is precisely the
symmetrisation required by the ``1 / r!`` reference.

The implementation scans terminal events while retaining a bit mask of the
anchors already assigned.  Its time complexity is ``O(n r 2**r)`` and its
memory complexity is ``O(2**r)`` in the worst case.  This is intended as an
exact test oracle for small anchor sets, not as a production assignment
solver.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np


def _as_real_numeric_array(value: np.ndarray, name: str) -> np.ndarray:
    """Convert a numeric input to float while rejecting coercive edge cases."""

    array = np.asarray(value)
    if array.dtype.kind == "b":
        raise TypeError("%s must not have boolean dtype" % name)
    if array.dtype.kind not in "iuf":
        raise TypeError("%s must have a real numeric dtype" % name)
    converted = array.astype(float, copy=True)
    if not np.all(np.isfinite(converted)):
        raise ValueError("%s entries must be finite" % name)
    return converted


def validate_unordered_association_inputs(
    pair_likelihood: np.ndarray,
    detection_probability: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Validate and copy an ``(r, n)`` likelihood matrix and ``(n,)`` rates.

    Likelihood values are densities, so they may exceed one.  Both likelihoods
    and detection probabilities are checked before any logarithm is taken;
    exact zeros remain exact zeros.
    """

    likelihood = _as_real_numeric_array(pair_likelihood, "pair_likelihood")
    detection = _as_real_numeric_array(
        detection_probability, "detection_probability"
    )

    if likelihood.ndim != 2:
        raise ValueError("pair_likelihood must be a two-dimensional matrix")
    if detection.ndim != 1:
        raise ValueError("detection_probability must be a one-dimensional vector")
    if likelihood.shape[1] != detection.shape[0]:
        raise ValueError(
            "pair_likelihood has %d event columns but detection_probability "
            "has length %d" % (likelihood.shape[1], detection.shape[0])
        )
    if np.any(likelihood < 0.0):
        raise ValueError("pair_likelihood entries must be nonnegative")
    if np.any(detection < 0.0) or np.any(detection > 1.0):
        raise ValueError("detection probabilities must lie in [0, 1]")
    return likelihood, detection


def _log_nonnegative(values: np.ndarray) -> np.ndarray:
    """Return exact log values, mapping only exact zeros to ``-inf``."""

    result = np.full(values.shape, -np.inf, dtype=float)
    positive = values > 0.0
    result[positive] = np.log(values[positive])
    return result


def _log_miss_probability(detection: np.ndarray) -> np.ndarray:
    """Return ``log(1 - d)`` without first rounding ``1 - d`` to one.

    In particular, ``log1p`` preserves the log probability of missing an event
    whose positive detection probability is smaller than machine epsilon.
    Exact unit detection remains an exact impossible miss rather than emitting
    a divide-by-zero warning.
    """

    result = np.full(detection.shape, -np.inf, dtype=float)
    can_miss = detection < 1.0
    result[can_miss] = np.log1p(-detection[can_miss])
    return result


def _accumulate_log_weight(
    destination: Dict[int, float],
    mask: int,
    log_weight: float,
) -> None:
    """Add a nonnegative path weight to a sparse log-domain table."""

    if log_weight == -np.inf:
        return
    previous = destination.get(mask)
    if previous is None:
        destination[mask] = log_weight
    else:
        destination[mask] = float(np.logaddexp(previous, log_weight))


def log_unordered_anchor_density(
    pair_likelihood: np.ndarray,
    detection_probability: np.ndarray,
) -> float:
    """Return the exact unordered-anchor log density by bit-mask dynamic programming.

    The return value is ``-inf`` exactly when the observation has zero density,
    including when there are more anchors than terminal events.  Very small
    positive densities remain finite in log space; no epsilon or probability
    floor is introduced.
    """

    likelihood, detection = validate_unordered_association_inputs(
        pair_likelihood, detection_probability
    )
    n_anchors, n_events = likelihood.shape
    if n_anchors > n_events:
        return -math.inf

    log_likelihood = _log_nonnegative(likelihood)
    log_detection = _log_nonnegative(detection)
    log_miss = _log_miss_probability(detection)

    # The dictionary maps a mask of already assigned anchors to the log of the
    # total weight of all assignments producing that mask after the processed
    # event prefix.  Each event is either missed or assigned to exactly one
    # previously unassigned anchor.
    dynamic: Dict[int, float] = {0: 0.0}
    for event_index in range(n_events):
        updated: Dict[int, float] = {}
        for mask, log_prefix_weight in dynamic.items():
            _accumulate_log_weight(
                updated,
                mask,
                log_prefix_weight + log_miss[event_index],
            )
            for anchor_index in range(n_anchors):
                anchor_bit = 1 << anchor_index
                if mask & anchor_bit:
                    continue
                _accumulate_log_weight(
                    updated,
                    mask | anchor_bit,
                    log_prefix_weight
                    + log_detection[event_index]
                    + log_likelihood[anchor_index, event_index],
                )
        dynamic = updated

    full_mask = (1 << n_anchors) - 1
    return dynamic.get(full_mask, -math.inf)


def unordered_anchor_density(
    pair_likelihood: np.ndarray,
    detection_probability: np.ndarray,
) -> float:
    """Return the unordered-anchor density in ordinary floating-point space.

    Computation is performed in log space first.  If the mathematically
    positive result is below the smallest representable float, IEEE exponent
    underflow may return zero; use :func:`log_unordered_anchor_density` when
    rare-event distinctions matter.  A non-representably large density raises
    ``OverflowError`` instead of silently returning infinity.
    """

    log_density = log_unordered_anchor_density(
        pair_likelihood, detection_probability
    )
    if log_density == -math.inf:
        return 0.0
    try:
        density = math.exp(log_density)
    except OverflowError as error:
        raise OverflowError(
            "unordered-anchor density exceeds floating-point range; use "
            "log_unordered_anchor_density"
        ) from error
    if not math.isfinite(density):
        raise OverflowError(
            "unordered-anchor density exceeds floating-point range; use "
            "log_unordered_anchor_density"
        )
    return density


__all__ = [
    "log_unordered_anchor_density",
    "unordered_anchor_density",
    "validate_unordered_association_inputs",
]
