"""Frozen finite A1 metrics and paired decision statistics.

The functions here are result-independent implementations of Sections 4, 7,
and 8 of the association-guided residual preregistration.  They deliberately
keep physical population masses separate from ratio-only numerical floors.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
import numpy as np


_RATIO_FLOOR = 1.0e-12


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    contiguous = np.array(array, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=np.float64
    ).reshape(contiguous.shape)


def _immutable_bool_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.bool_)
    contiguous = np.array(array, dtype=np.bool_, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=np.bool_
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
    result = raw.astype(np.float64, copy=True)
    if result.ndim != ndim or any(size <= 0 for size in result.shape):
        raise ValueError("%s must be a nonempty %dD array" % (name, ndim))
    if not np.all(np.isfinite(result)):
        raise ValueError("%s entries must be finite" % name)
    return result


def _index_array(value: object, *, name: str, ndim: int) -> np.ndarray:
    try:
        raw = np.asarray(value)
        object_view = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s must be a rectangular integer array" % name) from error
    if any(isinstance(item, (bool, np.bool_)) for item in object_view.flat):
        raise TypeError("%s must not contain boolean entries" % name)
    if raw.dtype.kind not in "iu" or raw.ndim != ndim or raw.size == 0:
        raise TypeError("%s must be a nonempty integer %dD array" % (name, ndim))
    result = raw.astype(np.int64, copy=True)
    return result


def normalized_masked_excess_bce(
    joint_mass: object,
    product_mass: object,
    logits: object,
    optimal_logits: object,
    time_indices: object,
    state_observation_pairs: object,
) -> float:
    """Return the physical-mass-normalized excess BCE on one Cartesian mask."""

    joint = _numeric_array(joint_mass, name="joint_mass", ndim=3)
    product = _numeric_array(product_mass, name="product_mass", ndim=3)
    score = _numeric_array(logits, name="logits", ndim=3)
    optimum = _numeric_array(optimal_logits, name="optimal_logits", ndim=3)
    if not (joint.shape == product.shape == score.shape == optimum.shape):
        raise ValueError("population masses and logit grids must have one shape")
    if np.any(joint <= 0.0) or np.any(product <= 0.0):
        raise ValueError("joint_mass and product_mass must be strictly positive")
    times = _index_array(time_indices, name="time_indices", ndim=1)
    pairs = _index_array(
        state_observation_pairs, name="state_observation_pairs", ndim=2
    )
    if pairs.shape[1] != 2:
        raise ValueError("state_observation_pairs must have two columns")
    if (
        np.any(times < 0)
        or np.any(times >= joint.shape[0])
        or np.any(pairs[:, 0] < 0)
        or np.any(pairs[:, 0] >= joint.shape[1])
        or np.any(pairs[:, 1] < 0)
        or np.any(pairs[:, 1] >= joint.shape[2])
    ):
        raise IndexError("a mask index is out of range")
    if len(set(int(value) for value in times)) != times.size:
        raise ValueError("time_indices must not contain duplicates")
    if len(set(map(tuple, pairs.tolist()))) != pairs.shape[0]:
        raise ValueError("state_observation_pairs must not contain duplicates")

    current_loss = 0.0
    optimal_loss = 0.0
    denominator = 0.0
    for time_index in times:
        states = pairs[:, 0]
        observations = pairs[:, 1]
        positive = joint[time_index, states, observations]
        negative = product[time_index, states, observations]
        value = score[time_index, states, observations]
        best = optimum[time_index, states, observations]
        current_loss += 0.5 * float(
            np.sum(
                positive * np.logaddexp(0.0, -value)
                + negative * np.logaddexp(0.0, value)
            )
        )
        optimal_loss += 0.5 * float(
            np.sum(
                positive * np.logaddexp(0.0, -best)
                + negative * np.logaddexp(0.0, best)
            )
        )
        denominator += 0.5 * float(np.sum(positive + negative))
    if denominator <= 0.0 or not math.isfinite(denominator):
        raise ArithmeticError("masked population denominator is invalid")
    excess = (current_loss - optimal_loss) / denominator
    tolerance = 64.0 * np.finfo(np.float64).eps * max(
        1.0, abs(current_loss), abs(optimal_loss)
    ) / denominator
    if excess < -tolerance:
        raise ArithmeticError("masked excess BCE is materially negative")
    return max(0.0, float(excess))


def equal_log_sample_aulc(values: object) -> float:
    """Return the raw ``(y_512 + 2 y_4096 + y_32768) / 4``.

    This raw aggregation is appropriate for absolute-reduction criteria.  Use
    :func:`ratio_equal_log_sample_aulc` when the resulting AULC will enter a
    ratio statistic; that routine applies the preregistered floor to each
    ordinate *before* aggregation.
    """

    array = _numeric_array(values, name="values", ndim=1)
    if array.shape != (3,) or np.any(array < 0.0):
        raise ValueError("values must contain three nonnegative ordinates")
    return float((array[0] + 2.0 * array[1] + array[2]) / 4.0)


def ratio_equal_log_sample_aulc(values: object) -> float:
    """Return the frozen equal-log-sample AULC for a ratio statistic.

    Each of the three nonnegative ordinates is first replaced by
    ``max(value, 1e-12)``.  The floor is intentionally fixed and is applied
    before the ``1, 2, 1`` aggregation, as required by the preregistration.
    Physical masses and raw absolute-reduction metrics are never modified.
    """

    array = _numeric_array(values, name="values", ndim=1)
    if array.shape != (3,) or np.any(array < 0.0):
        raise ValueError("values must contain three nonnegative ordinates")
    floored = np.maximum(array, _RATIO_FLOOR)
    return float((floored[0] + 2.0 * floored[1] + floored[2]) / 4.0)


def paired_geometric_mean_ratio(
    proposed: object,
    reference: object,
    *,
    floor: object = _RATIO_FLOOR,
) -> float:
    proposed_array = _numeric_array(proposed, name="proposed", ndim=1)
    reference_array = _numeric_array(reference, name="reference", ndim=1)
    if proposed_array.shape != reference_array.shape:
        raise ValueError("paired metric arrays must have one shape")
    if np.any(proposed_array < 0.0) or np.any(reference_array < 0.0):
        raise ValueError("paired metrics must be nonnegative")
    if isinstance(floor, (bool, np.bool_)) or not isinstance(floor, Real):
        raise TypeError("floor must be a real non-boolean number")
    ratio_floor = float(floor)
    if not math.isfinite(ratio_floor) or ratio_floor <= 0.0:
        raise ValueError("floor must be finite and strictly positive")
    logs = np.log(np.maximum(proposed_array, ratio_floor)) - np.log(
        np.maximum(reference_array, ratio_floor)
    )
    return float(math.exp(float(np.mean(logs))))


@dataclass(frozen=True, eq=False)
class PairedMaterialSignTest:
    margin: float
    wins: int
    p_value: float
    winning_seeds: np.ndarray

    def __post_init__(self) -> None:
        margin = float(self.margin)
        p_value = float(self.p_value)
        if not math.isfinite(margin) or margin <= 0.0:
            raise ValueError("margin must be finite and positive")
        if isinstance(self.wins, (bool, np.bool_)) or not isinstance(
            self.wins, Integral
        ):
            raise TypeError("wins must be an integer")
        if int(self.wins) < 0 or int(self.wins) > 8:
            raise ValueError("wins must lie in [0, 8]")
        if not math.isfinite(p_value) or not 0.0 <= p_value <= 1.0:
            raise ValueError("p_value must lie in [0, 1]")
        mask = np.asarray(self.winning_seeds)
        if mask.dtype.kind != "b" or mask.shape != (8,):
            raise ValueError("winning_seeds must be a boolean length-eight mask")
        if int(np.count_nonzero(mask)) != int(self.wins):
            raise ValueError("wins must match winning_seeds")
        object.__setattr__(self, "margin", margin)
        object.__setattr__(self, "wins", int(self.wins))
        object.__setattr__(self, "p_value", p_value)
        object.__setattr__(
            self, "winning_seeds", _immutable_bool_array(mask)
        )


def paired_material_sign_test(
    proposed: object,
    reference: object,
    *,
    margin: object = 0.90,
) -> PairedMaterialSignTest:
    proposed_array = _numeric_array(proposed, name="proposed", ndim=1)
    reference_array = _numeric_array(reference, name="reference", ndim=1)
    if proposed_array.shape != (8,) or reference_array.shape != (8,):
        raise ValueError("the frozen sign test requires eight paired seeds")
    if np.any(proposed_array < 0.0) or np.any(reference_array < 0.0):
        raise ValueError("paired metrics must be nonnegative")
    if isinstance(margin, (bool, np.bool_)) or not isinstance(margin, Real):
        raise TypeError("margin must be a real non-boolean number")
    threshold = float(margin)
    if not math.isfinite(threshold) or threshold <= 0.0:
        raise ValueError("margin must be finite and positive")
    ratios = np.maximum(proposed_array, _RATIO_FLOOR) / np.maximum(
        reference_array, _RATIO_FLOOR
    )
    mask = ratios < threshold
    wins = int(np.count_nonzero(mask))
    p_value = math.fsum(math.comb(8, value) for value in range(wins, 9)) / 256.0
    return PairedMaterialSignTest(
        margin=threshold,
        wins=wins,
        p_value=p_value,
        winning_seeds=mask,
    )


def shared_winning_seed_count(
    first: PairedMaterialSignTest,
    second: PairedMaterialSignTest,
) -> int:
    if not isinstance(first, PairedMaterialSignTest) or not isinstance(
        second, PairedMaterialSignTest
    ):
        raise TypeError("both inputs must be PairedMaterialSignTest records")
    return int(np.count_nonzero(first.winning_seeds & second.winning_seeds))


def balanced_ood_score(stratum_scores: object) -> np.ndarray:
    """Return the per-seed arithmetic mean across the four frozen OOD strata."""

    scores = _numeric_array(stratum_scores, name="stratum_scores", ndim=2)
    if scores.shape[1] != 4 or np.any(scores < 0.0):
        raise ValueError("stratum_scores must have four nonnegative columns")
    return _immutable_float_array(np.mean(scores, axis=1))


def retained_path_score(
    path_kl: object,
    unconditional_path_kl: object,
    observation_mass: object,
    overflow_index: object,
) -> np.ndarray:
    """Return the frozen physical-mass-weighted retained path score per seed."""

    values = _numeric_array(path_kl, name="path_kl", ndim=2)
    baseline = _numeric_array(
        unconditional_path_kl, name="unconditional_path_kl", ndim=1
    )
    mass = _numeric_array(observation_mass, name="observation_mass", ndim=1)
    if baseline.shape != mass.shape or values.shape[1] != mass.size:
        raise ValueError("path and observation axes are inconsistent")
    if np.any(values < 0.0) or np.any(baseline < 0.0) or np.any(mass <= 0.0):
        raise ValueError("path KLs must be nonnegative and masses positive")
    if not math.isclose(float(np.sum(mass)), 1.0, rel_tol=0.0, abs_tol=2.0e-12):
        raise ValueError("observation_mass must sum to one")
    if isinstance(overflow_index, (bool, np.bool_)) or not isinstance(
        overflow_index, Integral
    ):
        raise TypeError("overflow_index must be an integer")
    overflow = int(overflow_index)
    if overflow < 0 or overflow >= mass.size:
        raise IndexError("overflow_index is out of range")
    keep = np.ones(mass.size, dtype=bool)
    keep[overflow] = False
    denominator = float(np.dot(mass[keep], baseline[keep]))
    if denominator <= _RATIO_FLOOR:
        raise ArithmeticError("retained unconditional path normalizer is too small")
    result = (values[:, keep] @ mass[keep]) / denominator
    return _immutable_float_array(result)


def deterministic_weighted_median(values: object, weights: object) -> float:
    """Return the lowest stable-sorted value reaching half the total weight."""

    data = _numeric_array(values, name="values", ndim=1)
    mass = _numeric_array(weights, name="weights", ndim=1)
    if data.shape != mass.shape:
        raise ValueError("values and weights must have one shape")
    if np.any(mass < 0.0) or not np.any(mass > 0.0):
        raise ValueError("weights must be nonnegative with positive total")
    order = np.argsort(data, kind="mergesort")
    sorted_values = data[order]
    sorted_weights = mass[order]
    threshold = 0.5 * math.fsum(float(value) for value in sorted_weights)
    cumulative = 0.0
    for value, weight in zip(sorted_values, sorted_weights):
        cumulative += float(weight)
        if cumulative >= threshold:
            return float(value)
    raise ArithmeticError("weighted median accumulation failed")


__all__ = [
    "PairedMaterialSignTest",
    "balanced_ood_score",
    "deterministic_weighted_median",
    "equal_log_sample_aulc",
    "normalized_masked_excess_bce",
    "paired_geometric_mean_ratio",
    "paired_material_sign_test",
    "ratio_equal_log_sample_aulc",
    "retained_path_score",
    "shared_winning_seed_count",
]
