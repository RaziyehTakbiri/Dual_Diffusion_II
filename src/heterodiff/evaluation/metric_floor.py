"""Group-disjoint real-versus-real metric-floor estimates.

Finite samples make a held-out real set differ from another held-out real set.
This module measures that descriptive *sampling floor* with repeated random
half-splits of whole groups.  A group can represent a subject, recording,
patient, composition, or any other leakage unit.  Every row from a group is
kept on one side of a split.

These values are neither statistical-significance tests nor model scores.  In
particular, they must not be subtracted from a real-versus-generated score or
presented as an uncertainty interval for that score.

Two explicit empirical distances are provided:

``wasserstein_distance_1d``
    The ordinary equally weighted empirical 1-Wasserstein distance on the real
    line.

``biased_energy_distance``
    The multivariate V-statistic

    ``2 mean_ij ||x_i-y_j|| - mean_ii' ||x_i-x_i'||
      - mean_jj' ||y_j-y_j'||``.

    Diagonal within-sample pairs are included.  Thus this is the nonnegative
    energy distance between the two empirical measures (sometimes called the
    *squared* energy distance under a square-root convention), not the
    unbiased U-statistic estimator of a population quantity.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
import unicodedata
from typing import Sequence, Tuple, Union

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import wasserstein_distance


WASSERSTEIN_1D = "wasserstein_1d"
BIASED_ENERGY = "biased_energy"
_METRICS = frozenset((WASSERSTEIN_1D, BIASED_ENERGY))
_MAX_SEED = 2**64 - 1

GroupId = Union[int, str]


def _finite_numeric_array(
    values: object,
    *,
    name: str,
    ndim: int,
) -> np.ndarray:
    """Validate without allowing booleans, strings, or object coercions."""

    try:
        raw = np.asarray(values)
    except (TypeError, ValueError) as error:
        raise TypeError("%s must be a rectangular numeric array" % name) from error
    if raw.dtype.kind not in "iuf":
        raise TypeError("%s must contain real non-boolean numbers" % name)
    if raw.ndim != ndim:
        raise ValueError("%s must have exactly %d dimension(s)" % (name, ndim))
    if raw.size == 0 or raw.shape[0] == 0:
        raise ValueError("%s must contain at least one observation" % name)
    if ndim == 2 and raw.shape[1] == 0:
        raise ValueError("%s must contain at least one feature" % name)
    try:
        with np.errstate(over="ignore", invalid="ignore"):
            converted = raw.astype(np.float64, copy=False)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s cannot be represented as finite float64 values" % name) from error
    if not np.all(np.isfinite(converted)):
        raise ValueError("%s must contain only finite values" % name)
    return np.ascontiguousarray(converted)


def wasserstein_distance_1d(left: object, right: object) -> float:
    """Return the equally weighted empirical 1-Wasserstein distance.

    Both inputs must be nonempty one-dimensional finite numeric arrays.
    Boolean, complex, string, object, and non-finite arrays are rejected rather
    than coerced.
    """

    left_array = _finite_numeric_array(left, name="left", ndim=1)
    right_array = _finite_numeric_array(right, name="right", ndim=1)
    result = float(wasserstein_distance(left_array, right_array))
    if not math.isfinite(result):
        raise FloatingPointError(
            "the Wasserstein distance is not representable as a finite float"
        )
    if result < 0.0:
        raise FloatingPointError("the Wasserstein implementation returned a negative value")
    return result


def biased_energy_distance(left: object, right: object) -> float:
    """Return the multivariate biased empirical energy-distance statistic.

    Inputs have shape ``(observations, features)`` and must have the same
    positive feature dimension.  Sample counts may differ.  The returned
    V-statistic includes diagonal within-sample pairs and is exactly zero for
    identical empirical samples, up to a transparent round-off correction.
    It is not a significance test.
    """

    left_array = _finite_numeric_array(left, name="left", ndim=2)
    right_array = _finite_numeric_array(right, name="right", ndim=2)
    if left_array.shape[1] != right_array.shape[1]:
        raise ValueError("left and right must have the same feature dimension")

    # Canonical row order makes the finite-precision reduction invariant to a
    # caller's row permutation, not merely mathematically equivalent within a
    # tolerance.  The last lexsort key is primary, hence the reversed columns.
    left_order = np.lexsort(
        tuple(left_array[:, column] for column in reversed(range(left_array.shape[1])))
    )
    right_order = np.lexsort(
        tuple(
            right_array[:, column]
            for column in reversed(range(right_array.shape[1]))
        )
    )
    left_array = left_array[left_order]
    right_array = right_array[right_order]

    cross = float(np.mean(cdist(left_array, right_array, metric="euclidean")))
    within_left = float(np.mean(cdist(left_array, left_array, metric="euclidean")))
    within_right = float(
        np.mean(cdist(right_array, right_array, metric="euclidean"))
    )
    components = np.array((cross, within_left, within_right), dtype=np.float64)
    if not np.all(np.isfinite(components)):
        raise FloatingPointError(
            "the energy-distance pairwise norms are not representable as finite floats"
        )

    result = 2.0 * cross - within_left - within_right
    if not math.isfinite(result):
        raise FloatingPointError(
            "the energy distance is not representable as a finite float"
        )
    if result < 0.0:
        # The V-statistic is mathematically nonnegative.  Permit only the
        # cancellation error associated with subtracting its three components;
        # a material negative value indicates a numerical or implementation bug.
        scale = max(2.0 * cross + within_left + within_right, 1.0)
        tolerance = 64.0 * np.finfo(np.float64).eps * scale
        if result < -tolerance:
            raise FloatingPointError(
                "the energy statistic is materially negative; numerical evaluation failed"
            )
        return 0.0
    return result


def _group_id_sequence(group_ids: object, expected_length: int) -> Tuple[GroupId, ...]:
    if isinstance(group_ids, (str, bytes)):
        raise TypeError("group_ids must be a one-dimensional sequence, not text")
    try:
        raw = np.asarray(group_ids, dtype=object)
    except (TypeError, ValueError) as error:
        raise TypeError("group_ids must be a one-dimensional sequence") from error
    if raw.ndim != 1:
        raise ValueError("group_ids must be one-dimensional")
    if raw.shape[0] != expected_length:
        raise ValueError("group_ids must align one-for-one with observations")

    ids = []
    category = None
    normalized_origins = {}
    for index, raw_id in enumerate(raw.tolist()):
        if isinstance(raw_id, (bool, np.bool_)):
            raise TypeError("group_ids[%d] must not be boolean" % index)
        if isinstance(raw_id, Integral):
            current_category = "integer"
            group_id: GroupId = int(raw_id)
        elif isinstance(raw_id, str):
            current_category = "text"
            if not raw_id or "\x00" in raw_id:
                raise ValueError("text group IDs must be nonempty and contain no NUL")
            group_id = unicodedata.normalize("NFC", raw_id)
            previous = normalized_origins.get(group_id)
            if previous is not None and previous != raw_id:
                raise ValueError(
                    "group_ids contain labels that collide after Unicode normalization"
                )
            normalized_origins[group_id] = raw_id
        elif isinstance(raw_id, Real):
            raise TypeError(
                "floating-point group IDs are ambiguous; use integers or text labels"
            )
        else:
            raise TypeError("group IDs must be homogeneous integers or text labels")

        if category is None:
            category = current_category
        elif category != current_category:
            raise TypeError("group IDs must not mix integer and text labels")
        ids.append(group_id)
    return tuple(ids)


def _canonical_unique_groups(group_ids: Tuple[GroupId, ...]) -> Tuple[GroupId, ...]:
    # Validation guarantees a homogeneous, totally orderable identifier type.
    return tuple(sorted(set(group_ids)))


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer" % name)
    converted = int(value)
    if converted <= 0:
        raise ValueError("%s must be positive" % name)
    return converted


def _seed(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("seed must be a non-negative integer")
    converted = int(value)
    if converted < 0 or converted > _MAX_SEED:
        raise ValueError("seed must lie in [0, 2**64 - 1]")
    return converted


def _quantile_levels(values: object) -> Tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("quantiles must be a sequence of real numbers")
    try:
        raw_values = tuple(values)  # type: ignore[arg-type]
    except TypeError as error:
        raise TypeError("quantiles must be a sequence of real numbers") from error
    if not raw_values:
        raise ValueError("quantiles must not be empty")

    result = []
    for value in raw_values:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError("quantile levels must be real non-boolean numbers")
        level = float(value)
        if not math.isfinite(level) or not 0.0 <= level <= 1.0:
            raise ValueError("quantile levels must be finite values in [0, 1]")
        result.append(level)
    if any(right <= left for left, right in zip(result, result[1:])):
        raise ValueError("quantile levels must be strictly increasing and unique")
    return tuple(result)


def _linear_quantile(sorted_values: np.ndarray, level: float) -> float:
    """NumPy's default linear empirical quantile, without version coupling."""

    position = level * (sorted_values.size - 1)
    lower_index = int(math.floor(position))
    upper_index = int(math.ceil(position))
    if lower_index == upper_index:
        return float(sorted_values[lower_index])
    weight = position - lower_index
    return float(
        (1.0 - weight) * sorted_values[lower_index]
        + weight * sorted_values[upper_index]
    )


@dataclass(frozen=True)
class GroupSplitDistance:
    """One auditable group-disjoint half-split and its descriptive distance."""

    repeat: int
    left_groups: Tuple[GroupId, ...]
    right_groups: Tuple[GroupId, ...]
    left_observations: int
    right_observations: int
    distance: float

    def __post_init__(self) -> None:
        if isinstance(self.repeat, bool) or not isinstance(self.repeat, Integral):
            raise TypeError("repeat must be an integer")
        repeat = int(self.repeat)
        if repeat < 0:
            raise ValueError("repeat must be non-negative")
        try:
            left_raw = tuple(self.left_groups)
            right_raw = tuple(self.right_groups)
        except TypeError as error:
            raise TypeError("group assignments must be iterable") from error
        left = _group_id_sequence(left_raw, len(left_raw))
        right = _group_id_sequence(right_raw, len(right_raw))
        if not left or not right:
            raise ValueError("both split sides must contain at least one group")
        if len(set(left)) != len(left) or len(set(right)) != len(right):
            raise ValueError("group assignments must not contain duplicate IDs")
        if set(left).intersection(right):
            raise ValueError("left and right group assignments must be disjoint")
        left_count = _positive_integer(self.left_observations, "left_observations")
        right_count = _positive_integer(self.right_observations, "right_observations")
        if isinstance(self.distance, bool) or not isinstance(self.distance, Real):
            raise TypeError("distance must be a real number")
        distance = float(self.distance)
        if not math.isfinite(distance) or distance < 0.0:
            raise ValueError("distance must be finite and non-negative")
        object.__setattr__(self, "repeat", repeat)
        object.__setattr__(self, "left_groups", left)
        object.__setattr__(self, "right_groups", right)
        object.__setattr__(self, "left_observations", left_count)
        object.__setattr__(self, "right_observations", right_count)
        object.__setattr__(self, "distance", distance)


@dataclass(frozen=True)
class GroupMetricFloor:
    """Repeated group-split distances and deterministic descriptive summaries."""

    metric: str
    seed: int
    splits: Tuple[GroupSplitDistance, ...]
    median: float
    quantile_levels: Tuple[float, ...]
    quantile_values: Tuple[float, ...]

    @property
    def distances(self) -> Tuple[float, ...]:
        """Return per-repeat distances in repeat order."""

        return tuple(split.distance for split in self.splits)

    def quantile(self, level: float) -> float:
        """Return a reported quantile, requiring an exactly requested level."""

        if isinstance(level, bool) or not isinstance(level, Real):
            raise TypeError("level must be a real non-boolean number")
        converted = float(level)
        for stored_level, value in zip(self.quantile_levels, self.quantile_values):
            if converted == stored_level:
                return value
        raise KeyError("quantile level was not requested")

    def __post_init__(self) -> None:
        if not isinstance(self.metric, str):
            raise TypeError("metric must be a string")
        if self.metric not in _METRICS:
            raise ValueError("metric must be one of %s" % sorted(_METRICS))
        seed = _seed(self.seed)
        splits = tuple(self.splits)
        if not splits:
            raise ValueError("splits must not be empty")
        if tuple(split.repeat for split in splits) != tuple(range(len(splits))):
            raise ValueError("split repeat indices must be consecutive from zero")
        levels = _quantile_levels(self.quantile_levels)
        quantile_values = tuple(self.quantile_values)
        if len(quantile_values) != len(levels):
            raise ValueError("quantile_values must align with quantile_levels")
        for value in (self.median,) + quantile_values:
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError("summary values must be real numbers")
            if not math.isfinite(float(value)) or float(value) < 0.0:
                raise ValueError("summary values must be finite and non-negative")
        sorted_distances = np.sort(
            np.fromiter((split.distance for split in splits), dtype=np.float64)
        )
        expected_median = _linear_quantile(sorted_distances, 0.5)
        expected_quantiles = tuple(
            _linear_quantile(sorted_distances, level) for level in levels
        )
        if float(self.median) != expected_median:
            raise ValueError("median is inconsistent with the split distances")
        if tuple(float(value) for value in quantile_values) != expected_quantiles:
            raise ValueError("quantile_values are inconsistent with the split distances")
        object.__setattr__(self, "seed", seed)
        object.__setattr__(self, "splits", splits)
        object.__setattr__(self, "median", float(self.median))
        object.__setattr__(self, "quantile_levels", levels)
        object.__setattr__(
            self, "quantile_values", tuple(float(value) for value in quantile_values)
        )


def estimate_group_metric_floor(
    values: object,
    group_ids: object,
    *,
    metric: str,
    repeats: int = 100,
    seed: int = 0,
    quantiles: Sequence[float] = (0.05, 0.25, 0.75, 0.95),
) -> GroupMetricFloor:
    """Estimate a descriptive real-versus-real sampling floor.

    For each repeat, the canonical sorted set of group IDs is permuted with a
    local ``numpy.random.Generator``.  ``floor(G/2)`` groups go left and all
    remaining groups go right.  The procedure supports unequal group sizes and
    never divides rows from one group between sides.  Row-order permutations
    therefore leave the seeded result unchanged.

    ``values`` must have shape ``(n,)`` for ``metric='wasserstein_1d'`` and
    ``(n, d)`` for ``metric='biased_energy'``.  Integer or Unicode text group
    IDs are accepted; floating, boolean, mixed-type, empty, and ambiguously
    Unicode-normalized IDs are rejected.
    """

    if not isinstance(metric, str):
        raise TypeError("metric must be a string")
    if metric not in _METRICS:
        raise ValueError("metric must be one of %s" % sorted(_METRICS))
    repeat_count = _positive_integer(repeats, "repeats")
    random_seed = _seed(seed)
    levels = _quantile_levels(quantiles)
    expected_ndim = 1 if metric == WASSERSTEIN_1D else 2
    value_array = _finite_numeric_array(values, name="values", ndim=expected_ndim)
    ids = _group_id_sequence(group_ids, value_array.shape[0])
    groups = _canonical_unique_groups(ids)
    if len(groups) < 2:
        raise ValueError("at least two distinct groups are required")

    rng = np.random.default_rng(random_seed)
    left_group_count = len(groups) // 2
    records = []
    for repeat in range(repeat_count):
        permutation = rng.permutation(len(groups))
        left_groups = tuple(sorted(groups[index] for index in permutation[:left_group_count]))
        right_groups = tuple(sorted(groups[index] for index in permutation[left_group_count:]))
        left_group_set = set(left_groups)
        left_mask = np.fromiter(
            (group_id in left_group_set for group_id in ids),
            dtype=np.bool_,
            count=len(ids),
        )
        right_mask = np.logical_not(left_mask)
        if not np.any(left_mask) or not np.any(right_mask):
            raise RuntimeError("internal group split unexpectedly produced an empty side")

        if metric == WASSERSTEIN_1D:
            distance = wasserstein_distance_1d(
                value_array[left_mask], value_array[right_mask]
            )
        else:
            distance = biased_energy_distance(
                value_array[left_mask], value_array[right_mask]
            )
        records.append(
            GroupSplitDistance(
                repeat=repeat,
                left_groups=left_groups,
                right_groups=right_groups,
                left_observations=int(np.sum(left_mask)),
                right_observations=int(np.sum(right_mask)),
                distance=distance,
            )
        )

    sorted_distances = np.sort(
        np.fromiter((record.distance for record in records), dtype=np.float64)
    )
    median = _linear_quantile(sorted_distances, 0.5)
    quantile_values = tuple(
        _linear_quantile(sorted_distances, level) for level in levels
    )
    return GroupMetricFloor(
        metric=metric,
        seed=random_seed,
        splits=tuple(records),
        median=median,
        quantile_levels=levels,
        quantile_values=quantile_values,
    )
