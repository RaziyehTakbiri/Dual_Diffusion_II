"""Deterministic sampled-data custody for the frozen A1 experiment.

This module materializes the decision-bearing sampled lane from
``research/62_a1_association_guided_residual_falsification_spec.md``.  It does
not import a learner or a tensor framework.  The complete random boundary is
NumPy ``SeedSequence(seed).spawn(3)``: child zero generates inverse-CDF data,
child one is reserved and reproducibly exposed for model initialization, and
child two generates epoch permutations.

Categorical support is always traversed in full state-major, then
observation-major order after applying the frozen training-pair mask.  Every
budget takes the same within-time/class group prefixes from one 1,024-sample
maximum stream.  The stored importance weight is the unnormalized masked mass
``alpha[y, j]``; it is never replaced by an independently normalized class
weight.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
from numbers import Integral
from typing import Tuple

import numpy as np

from heterodiff.theory.finite_atomic_counting import FiniteAtomicCountingSpace

from .finite_association_guided_residual_pilot import (
    FrozenAssociationResidualFixture,
    FrozenAssociationResidualSplits,
    build_frozen_association_residual_fixture,
    frozen_association_residual_splits,
)


SAMPLE_BUDGETS = (512, 4_096, 32_768)
PAIRED_SEEDS = (1_729, 3_253, 5_003, 7_411, 10_007, 13_007, 16_001, 20_011)
BATCH_SIZE = 128
PRIMARY_UPDATES = 3_000
STRONGER_UPDATES = 4_500

_UPDATE_COUNTS = (PRIMARY_UPDATES, STRONGER_UPDATES)
_TRAIN_TIME_INDICES = tuple(range(0, 32, 2))
_CLASS_LABELS = (1, 0)  # Joint-positive first, product-negative second.
_GROUP_COUNT = len(_TRAIN_TIME_INDICES) * len(_CLASS_LABELS)
_MAXIMUM_GROUP_SAMPLES = 1_024
_TRAIN_PAIR_COUNT = 61
_MAX_SCHEDULE_ENTRIES = STRONGER_UPDATES * BATCH_SIZE
_FLOAT_DTYPE = np.dtype("<f8")
_INT_DTYPE = np.dtype("<i8")


def _frozen_training_support() -> Tuple[Tuple[int, int], ...]:
    latent_space = FiniteAtomicCountingSpace(("s1", "s2", "s3"), 3)
    retained_space = FiniteAtomicCountingSpace(("a1", "a2", "a3"), 3)
    result = []
    for state_index, state in enumerate(latent_space.states):
        if sum(state) > 2:
            continue
        for observation_index, observed in enumerate(retained_space.states):
            if sum(observed) > 2:
                continue
            hash_value = (
                3 * state[0]
                + 5 * state[1]
                + 7 * state[2]
                + 11 * observed[0]
                + 13 * observed[1]
                + 17 * observed[2]
                + 19 * sum(state) * sum(observed)
            ) % 5
            if hash_value in (0, 1, 2):
                result.append((state_index, observation_index))
    if len(result) != _TRAIN_PAIR_COUNT:
        raise ArithmeticError("frozen training support has an invalid size")
    return tuple(result)


_FROZEN_TRAIN_SUPPORT = _frozen_training_support()


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=_FLOAT_DTYPE)
    contiguous = np.array(array, dtype=_FLOAT_DTYPE, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=_FLOAT_DTYPE
    ).reshape(contiguous.shape)


def _immutable_int_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=_INT_DTYPE)
    contiguous = np.array(array, dtype=_INT_DTYPE, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=_INT_DTYPE
    ).reshape(contiguous.shape)


def _validated_int_array(
    value: object,
    *,
    name: str,
    shape: Tuple[int, ...],
) -> np.ndarray:
    try:
        raw = np.asarray(value)
        object_view = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s must be a rectangular integer array" % name) from error
    if any(isinstance(item, (bool, np.bool_)) for item in object_view.flat):
        raise TypeError("%s must not contain boolean entries" % name)
    if raw.dtype.kind not in "iu" or raw.shape != shape:
        raise ValueError("%s must be an integer array with shape %r" % (name, shape))
    try:
        converted = raw.astype(_INT_DTYPE, copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s cannot be represented as int64" % name) from error
    return _immutable_int_array(converted)


def _validated_float_array(
    value: object,
    *,
    name: str,
    shape: Tuple[int, ...],
    strictly_positive: bool = False,
) -> np.ndarray:
    try:
        raw = np.asarray(value)
        object_view = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s must be a rectangular numeric array" % name) from error
    if any(isinstance(item, (bool, np.bool_)) for item in object_view.flat):
        raise TypeError("%s must not contain boolean entries" % name)
    if raw.dtype.kind not in "iuf" or raw.shape != shape:
        raise ValueError("%s must be numeric with shape %r" % (name, shape))
    try:
        converted = raw.astype(_FLOAT_DTYPE, copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s cannot be represented as float64" % name) from error
    if not np.all(np.isfinite(converted)):
        raise ValueError("%s entries must be finite" % name)
    if strictly_positive and np.any(converted <= 0.0):
        raise ValueError("%s entries must be strictly positive" % name)
    return _immutable_float_array(converted)


def _frozen_integer(value: object, *, name: str, allowed: Tuple[int, ...]) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result not in allowed:
        raise ValueError("%s must be one of %r" % (name, allowed))
    return result


def _array_digest(label: str, *arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-finite-association-residual-data-v1\0")
    digest.update(label.encode("ascii"))
    digest.update(b"\0")
    for value in arrays:
        array = np.ascontiguousarray(value)
        descriptor = "%s|%s|" % (
            array.dtype.str,
            ",".join(str(int(size)) for size in array.shape),
        )
        digest.update(descriptor.encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _digest_is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


@dataclass(frozen=True, eq=False)
class FrozenAssociationResidualSampleDataset:
    """One immutable balanced accepted-example budget.

    Rows are ordered by training time, then class ``(positive, negative)``,
    then the within-group stream position.  Thus reshaping any row array to
    ``(16, 2, samples_per_group)`` exposes the nested group-prefix contract.
    """

    seed: int
    budget: int
    samples_per_group: int
    time_indices: np.ndarray
    direct_times: np.ndarray
    class_labels: np.ndarray
    state_indices: np.ndarray
    observation_indices: np.ndarray
    importance_weights: np.ndarray
    group_alpha_weights: np.ndarray
    support_pairs: np.ndarray
    _digest: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        seed = _frozen_integer(self.seed, name="seed", allowed=PAIRED_SEEDS)
        budget = _frozen_integer(
            self.budget, name="budget", allowed=SAMPLE_BUDGETS
        )
        expected_group_samples = budget // _GROUP_COUNT
        group_samples = _frozen_integer(
            self.samples_per_group,
            name="samples_per_group",
            allowed=tuple(value // _GROUP_COUNT for value in SAMPLE_BUDGETS),
        )
        if group_samples != expected_group_samples:
            raise ValueError("samples_per_group is inconsistent with budget")

        row_shape = (budget,)
        time_indices = _validated_int_array(
            self.time_indices, name="time_indices", shape=row_shape
        )
        direct_times = _validated_float_array(
            self.direct_times, name="direct_times", shape=row_shape
        )
        labels = _validated_int_array(
            self.class_labels, name="class_labels", shape=row_shape
        )
        states = _validated_int_array(
            self.state_indices, name="state_indices", shape=row_shape
        )
        observations = _validated_int_array(
            self.observation_indices,
            name="observation_indices",
            shape=row_shape,
        )
        importance = _validated_float_array(
            self.importance_weights,
            name="importance_weights",
            shape=row_shape,
            strictly_positive=True,
        )
        alpha = _validated_float_array(
            self.group_alpha_weights,
            name="group_alpha_weights",
            shape=(len(_TRAIN_TIME_INDICES), len(_CLASS_LABELS)),
            strictly_positive=True,
        )
        support = _validated_int_array(
            self.support_pairs,
            name="support_pairs",
            shape=(_TRAIN_PAIR_COUNT, 2),
        )

        expected_times = np.repeat(
            np.asarray(_TRAIN_TIME_INDICES, dtype=_INT_DTYPE),
            len(_CLASS_LABELS) * group_samples,
        )
        expected_labels = np.tile(
            np.repeat(np.asarray(_CLASS_LABELS, dtype=_INT_DTYPE), group_samples),
            len(_TRAIN_TIME_INDICES),
        )
        if not np.array_equal(time_indices, expected_times):
            raise ValueError("time_indices violate frozen group ordering")
        if not np.array_equal(labels, expected_labels):
            raise ValueError("class_labels violate frozen positive/negative ordering")
        expected_direct_times = expected_times.astype(_FLOAT_DTYPE) / 32.0
        if not np.array_equal(direct_times, expected_direct_times):
            raise ValueError("direct_times are inconsistent with frozen time indices")

        if np.any(support < 0):
            raise ValueError("support_pairs entries must be nonnegative")
        support_tuples = tuple((int(row[0]), int(row[1])) for row in support)
        if support_tuples != _FROZEN_TRAIN_SUPPORT:
            raise ValueError(
                "support_pairs must equal the frozen state-major training mask"
            )
        support_set = set(support_tuples)
        if any(
            (int(state), int(observed)) not in support_set
            for state, observed in zip(states, observations)
        ):
            raise ValueError("a sampled pair lies outside the frozen training mask")

        expected_importance = np.broadcast_to(
            np.asarray(alpha)[:, :, None],
            (len(_TRAIN_TIME_INDICES), len(_CLASS_LABELS), group_samples),
        ).reshape(-1)
        if not np.array_equal(importance, expected_importance):
            raise ValueError(
                "importance_weights must equal the exact group alpha weights"
            )

        metadata = np.asarray(
            (seed, budget, group_samples), dtype=_INT_DTYPE
        )
        digest = _array_digest(
            "sample-dataset",
            metadata,
            time_indices,
            direct_times,
            labels,
            states,
            observations,
            importance,
            alpha,
            support,
        )
        object.__setattr__(self, "seed", seed)
        object.__setattr__(self, "budget", budget)
        object.__setattr__(self, "samples_per_group", group_samples)
        object.__setattr__(self, "time_indices", time_indices)
        object.__setattr__(self, "direct_times", direct_times)
        object.__setattr__(self, "class_labels", labels)
        object.__setattr__(self, "state_indices", states)
        object.__setattr__(self, "observation_indices", observations)
        object.__setattr__(self, "importance_weights", importance)
        object.__setattr__(self, "group_alpha_weights", alpha)
        object.__setattr__(self, "support_pairs", support)
        object.__setattr__(self, "_digest", digest)

    @property
    def digest(self) -> str:
        return self._digest


@dataclass(frozen=True, eq=False)
class FrozenAssociationResidualBatchSchedule:
    """Complete immutable epoch-permutation batch schedule."""

    seed: int
    budget: int
    updates: int
    batch_size: int
    batch_indices: np.ndarray
    _digest: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        seed = _frozen_integer(self.seed, name="seed", allowed=PAIRED_SEEDS)
        budget = _frozen_integer(
            self.budget, name="budget", allowed=SAMPLE_BUDGETS
        )
        updates = _frozen_integer(
            self.updates, name="updates", allowed=_UPDATE_COUNTS
        )
        batch_size = _frozen_integer(
            self.batch_size, name="batch_size", allowed=(BATCH_SIZE,)
        )
        entry_count = updates * batch_size
        if entry_count > _MAX_SCHEDULE_ENTRIES:
            raise ValueError("batch schedule exceeds the frozen work limit")
        indices = _validated_int_array(
            self.batch_indices,
            name="batch_indices",
            shape=(updates, batch_size),
        )
        if np.any(indices < 0) or np.any(indices >= budget):
            raise ValueError("batch_indices lie outside the selected dataset")

        flattened = np.asarray(indices).reshape(-1)
        full_epoch_count = flattened.size // budget
        full_size = full_epoch_count * budget
        if full_epoch_count:
            epochs = flattened[:full_size].reshape(full_epoch_count, budget)
            expected = np.arange(budget, dtype=_INT_DTYPE)
            if not np.all(np.sort(epochs, axis=1) == expected[None, :]):
                raise ValueError("every complete epoch must be a permutation")
        tail = flattened[full_size:]
        if tail.size and np.unique(tail).size != tail.size:
            raise ValueError("the final partial epoch must be a permutation prefix")

        metadata = np.asarray(
            (seed, budget, updates, batch_size), dtype=_INT_DTYPE
        )
        digest = _array_digest("batch-schedule", metadata, indices)
        object.__setattr__(self, "seed", seed)
        object.__setattr__(self, "budget", budget)
        object.__setattr__(self, "updates", updates)
        object.__setattr__(self, "batch_size", batch_size)
        object.__setattr__(self, "batch_indices", indices)
        object.__setattr__(self, "_digest", digest)

    @property
    def digest(self) -> str:
        return self._digest


@dataclass(frozen=True, eq=False)
class FrozenAssociationResidualSampleCustody:
    """All frozen datasets, RNG custody, and batch schedules for one seed."""

    seed: int
    datasets: Tuple[FrozenAssociationResidualSampleDataset, ...]
    batch_schedules: Tuple[FrozenAssociationResidualBatchSchedule, ...]
    model_seed_entropy: int
    model_seed_spawn_key: Tuple[int, ...]
    model_seed_pool_size: int
    model_seed_state: np.ndarray
    _digest: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        seed = _frozen_integer(self.seed, name="seed", allowed=PAIRED_SEEDS)
        if type(self.datasets) is not tuple or len(self.datasets) != len(
            SAMPLE_BUDGETS
        ):
            raise TypeError("datasets must be the frozen budget tuple")
        if not all(
            isinstance(value, FrozenAssociationResidualSampleDataset)
            for value in self.datasets
        ):
            raise TypeError("datasets contain an invalid value")
        if tuple(value.budget for value in self.datasets) != SAMPLE_BUDGETS:
            raise ValueError("datasets must follow SAMPLE_BUDGETS order")
        if any(value.seed != seed for value in self.datasets):
            raise ValueError("every dataset must use the custody seed")

        expected_schedule_keys = tuple(
            (budget, updates)
            for budget in SAMPLE_BUDGETS
            for updates in _UPDATE_COUNTS
        )
        if type(self.batch_schedules) is not tuple or len(
            self.batch_schedules
        ) != len(expected_schedule_keys):
            raise TypeError("batch_schedules must be the complete frozen tuple")
        if not all(
            isinstance(value, FrozenAssociationResidualBatchSchedule)
            for value in self.batch_schedules
        ):
            raise TypeError("batch_schedules contain an invalid value")
        if tuple(
            (value.budget, value.updates) for value in self.batch_schedules
        ) != expected_schedule_keys:
            raise ValueError("batch_schedules use an invalid order or key")
        if any(value.seed != seed for value in self.batch_schedules):
            raise ValueError("every batch schedule must use the custody seed")

        if (
            isinstance(self.model_seed_entropy, (bool, np.bool_))
            or not isinstance(self.model_seed_entropy, Integral)
            or int(self.model_seed_entropy) != seed
        ):
            raise ValueError("model_seed_entropy must equal the custody seed")
        if type(self.model_seed_spawn_key) is not tuple or not all(
            isinstance(value, Integral) and not isinstance(value, (bool, np.bool_))
            for value in self.model_seed_spawn_key
        ):
            raise TypeError("model_seed_spawn_key must be an integer tuple")
        spawn_key = tuple(int(value) for value in self.model_seed_spawn_key)
        if spawn_key != (1,):
            raise ValueError("model_seed_spawn_key must identify spawn child one")
        pool_size = _frozen_integer(
            self.model_seed_pool_size,
            name="model_seed_pool_size",
            allowed=(4,),
        )
        model_state = _validated_int_array(
            self.model_seed_state,
            name="model_seed_state",
            shape=(4,),
        )
        reconstructed = np.random.SeedSequence(
            seed, spawn_key=spawn_key, pool_size=pool_size
        )
        expected_state = reconstructed.generate_state(4, dtype=np.uint32).astype(
            _INT_DTYPE
        )
        if not np.array_equal(model_state, expected_state):
            raise ValueError("model_seed_state does not match spawn child one")

        maximum = self.datasets[-1]
        for dataset in self.datasets[:-1]:
            if not np.array_equal(
                dataset.group_alpha_weights, maximum.group_alpha_weights
            ) or not np.array_equal(dataset.support_pairs, maximum.support_pairs):
                raise ValueError("datasets disagree on frozen mask weights or support")
            prefix = dataset.samples_per_group
            for name in ("state_indices", "observation_indices"):
                actual = np.asarray(getattr(dataset, name)).reshape(
                    len(_TRAIN_TIME_INDICES), len(_CLASS_LABELS), prefix
                )
                expected = np.asarray(getattr(maximum, name)).reshape(
                    len(_TRAIN_TIME_INDICES),
                    len(_CLASS_LABELS),
                    _MAXIMUM_GROUP_SAMPLES,
                )[:, :, :prefix]
                if not np.array_equal(actual, expected):
                    raise ValueError("datasets violate nested group prefixes")
        for budget in SAMPLE_BUDGETS:
            primary = next(
                value
                for value in self.batch_schedules
                if value.budget == budget and value.updates == PRIMARY_UPDATES
            )
            stronger = next(
                value
                for value in self.batch_schedules
                if value.budget == budget and value.updates == STRONGER_UPDATES
            )
            if not np.array_equal(
                primary.batch_indices,
                stronger.batch_indices[:PRIMARY_UPDATES],
            ):
                raise ValueError("stronger schedules must extend primary schedules")

        digest_payload = hashlib.sha256()
        digest_payload.update(
            b"heterodiff-finite-association-residual-custody-v1\0"
        )
        digest_payload.update(str(seed).encode("ascii"))
        digest_payload.update(b"\0")
        for value in self.datasets + self.batch_schedules:
            if not _digest_is_sha256(value.digest):
                raise ArithmeticError("an internal custody digest is invalid")
            digest_payload.update(value.digest.encode("ascii"))
        digest_payload.update(np.ascontiguousarray(model_state).tobytes(order="C"))

        object.__setattr__(self, "seed", seed)
        object.__setattr__(self, "model_seed_entropy", seed)
        object.__setattr__(self, "model_seed_spawn_key", spawn_key)
        object.__setattr__(self, "model_seed_pool_size", pool_size)
        object.__setattr__(self, "model_seed_state", model_state)
        object.__setattr__(self, "_digest", digest_payload.hexdigest())

    @property
    def digest(self) -> str:
        return self._digest

    @property
    def maximum_dataset(self) -> FrozenAssociationResidualSampleDataset:
        return self.datasets[-1]

    @property
    def dataset_digests(self) -> Tuple[str, ...]:
        return tuple(value.digest for value in self.datasets)

    @property
    def batch_schedule_digests(self) -> Tuple[str, ...]:
        return tuple(value.digest for value in self.batch_schedules)

    @property
    def model_seed_child(self) -> np.random.SeedSequence:
        """Return a fresh exact reconstruction of reserved spawn child one."""

        return np.random.SeedSequence(
            self.model_seed_entropy,
            spawn_key=self.model_seed_spawn_key,
            pool_size=self.model_seed_pool_size,
        )

    def dataset(self, budget: object) -> FrozenAssociationResidualSampleDataset:
        selected = _frozen_integer(budget, name="budget", allowed=SAMPLE_BUDGETS)
        return next(value for value in self.datasets if value.budget == selected)

    def batch_schedule(
        self, budget: object, updates: object
    ) -> FrozenAssociationResidualBatchSchedule:
        selected_budget = _frozen_integer(
            budget, name="budget", allowed=SAMPLE_BUDGETS
        )
        selected_updates = _frozen_integer(
            updates, name="updates", allowed=_UPDATE_COUNTS
        )
        return next(
            value
            for value in self.batch_schedules
            if value.budget == selected_budget and value.updates == selected_updates
        )


def _state_major_training_support(
    fixture: FrozenAssociationResidualFixture,
    splits: FrozenAssociationResidualSplits,
) -> np.ndarray:
    if not isinstance(fixture, FrozenAssociationResidualFixture):
        raise TypeError("fixture must be a FrozenAssociationResidualFixture")
    if not isinstance(splits, FrozenAssociationResidualSplits):
        raise TypeError("splits must be FrozenAssociationResidualSplits")
    supplied = {
        (int(pair[0]), int(pair[1])) for pair in np.asarray(splits.train_pairs)
    }
    if supplied != set(_FROZEN_TRAIN_SUPPORT):
        raise ArithmeticError("the frozen training pair mask has changed")
    support = np.asarray(_FROZEN_TRAIN_SUPPORT, dtype=_INT_DTYPE)
    if support.shape != (_TRAIN_PAIR_COUNT, 2) or {
        (int(pair[0]), int(pair[1])) for pair in support
    } != supplied:
        raise ArithmeticError("failed to reconstruct the frozen training mask")
    return _immutable_int_array(support)


def _draw_maximum_streams(
    seed_child: np.random.SeedSequence,
    fixture: FrozenAssociationResidualFixture,
    splits: FrozenAssociationResidualSplits,
    support: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    if tuple(int(value) for value in splits.train_times) != _TRAIN_TIME_INDICES:
        raise ArithmeticError("the frozen training time split has changed")
    generator = np.random.Generator(np.random.PCG64(seed_child))
    states = np.empty(
        (len(_TRAIN_TIME_INDICES), len(_CLASS_LABELS), _MAXIMUM_GROUP_SAMPLES),
        dtype=_INT_DTYPE,
    )
    observations = np.empty_like(states)
    alpha = np.empty(
        (len(_TRAIN_TIME_INDICES), len(_CLASS_LABELS)), dtype=_FLOAT_DTYPE
    )
    tables = (fixture.population.joint_mass, fixture.population.product_mass)

    support_states = np.asarray(support[:, 0], dtype=np.int64)
    support_observations = np.asarray(support[:, 1], dtype=np.int64)
    for time_position, time_index in enumerate(_TRAIN_TIME_INDICES):
        for class_position, table in enumerate(tables):
            weights = np.asarray(
                table[time_index, support_states, support_observations],
                dtype=np.float64,
            )
            if weights.shape != (_TRAIN_PAIR_COUNT,) or np.any(weights <= 0.0):
                raise ArithmeticError("masked sampling weights must be positive")
            group_alpha = math.fsum(float(value) for value in weights)
            if not math.isfinite(group_alpha) or not 0.0 < group_alpha <= 1.0:
                raise ArithmeticError("masked class mass is invalid")
            alpha[time_position, class_position] = group_alpha

            conditional = weights / group_alpha
            cumulative = np.cumsum(conditional, dtype=np.float64)
            if np.any(cumulative[:-1] <= 0.0) or np.any(
                cumulative[1:] <= cumulative[:-1]
            ):
                raise ArithmeticError("masked inverse-CDF support is not increasing")
            cumulative[-1] = 1.0
            uniforms = generator.random(_MAXIMUM_GROUP_SAMPLES)
            selected = np.searchsorted(cumulative, uniforms, side="right")
            if np.any(selected < 0) or np.any(selected >= _TRAIN_PAIR_COUNT):
                raise ArithmeticError("inverse-CDF sampling left its support")
            states[time_position, class_position] = support_states[selected]
            observations[time_position, class_position] = support_observations[
                selected
            ]

    return (
        _immutable_int_array(states),
        _immutable_int_array(observations),
        _immutable_float_array(alpha),
    )


def _materialize_dataset(
    seed: int,
    budget: int,
    fixture: FrozenAssociationResidualFixture,
    support: np.ndarray,
    maximum_states: np.ndarray,
    maximum_observations: np.ndarray,
    alpha: np.ndarray,
) -> FrozenAssociationResidualSampleDataset:
    samples_per_group = budget // _GROUP_COUNT
    shape = (len(_TRAIN_TIME_INDICES), len(_CLASS_LABELS), samples_per_group)
    time_indices = np.broadcast_to(
        np.asarray(_TRAIN_TIME_INDICES, dtype=_INT_DTYPE)[:, None, None], shape
    ).reshape(-1)
    labels = np.broadcast_to(
        np.asarray(_CLASS_LABELS, dtype=_INT_DTYPE)[None, :, None], shape
    ).reshape(-1)
    states = np.asarray(maximum_states)[:, :, :samples_per_group].reshape(-1)
    observations = np.asarray(maximum_observations)[
        :, :, :samples_per_group
    ].reshape(-1)
    importance = np.broadcast_to(np.asarray(alpha)[:, :, None], shape).reshape(-1)
    direct_times = np.asarray(fixture.times)[time_indices]
    return FrozenAssociationResidualSampleDataset(
        seed=seed,
        budget=budget,
        samples_per_group=samples_per_group,
        time_indices=time_indices,
        direct_times=direct_times,
        class_labels=labels,
        state_indices=states,
        observation_indices=observations,
        importance_weights=importance,
        group_alpha_weights=alpha,
        support_pairs=support,
    )


def _materialize_batch_schedule(
    seed: int,
    seed_child: np.random.SeedSequence,
    budget: int,
    updates: int,
) -> FrozenAssociationResidualBatchSchedule:
    generator = np.random.Generator(np.random.PCG64(seed_child))
    batches_per_epoch = budget // BATCH_SIZE
    schedule = np.empty((updates, BATCH_SIZE), dtype=_INT_DTYPE)
    completed = 0
    while completed < updates:
        permutation = generator.permutation(budget).reshape(
            batches_per_epoch, BATCH_SIZE
        )
        take = min(batches_per_epoch, updates - completed)
        schedule[completed : completed + take] = permutation[:take]
        completed += take
    return FrozenAssociationResidualBatchSchedule(
        seed=seed,
        budget=budget,
        updates=updates,
        batch_size=BATCH_SIZE,
        batch_indices=schedule,
    )


def build_frozen_association_residual_sample_custody(
    seed: object,
) -> FrozenAssociationResidualSampleCustody:
    """Build all frozen nested data and batch schedules for one paired seed."""

    checked_seed = _frozen_integer(seed, name="seed", allowed=PAIRED_SEEDS)
    fixture = build_frozen_association_residual_fixture()
    splits = frozen_association_residual_splits(fixture)
    support = _state_major_training_support(fixture, splits)

    root = np.random.SeedSequence(checked_seed)
    data_child, model_child, batch_child = root.spawn(3)
    maximum_states, maximum_observations, alpha = _draw_maximum_streams(
        data_child, fixture, splits, support
    )
    datasets = tuple(
        _materialize_dataset(
            checked_seed,
            budget,
            fixture,
            support,
            maximum_states,
            maximum_observations,
            alpha,
        )
        for budget in SAMPLE_BUDGETS
    )
    schedules = tuple(
        _materialize_batch_schedule(
            checked_seed, batch_child, budget, updates
        )
        for budget in SAMPLE_BUDGETS
        for updates in _UPDATE_COUNTS
    )
    model_state = model_child.generate_state(4, dtype=np.uint32).astype(
        _INT_DTYPE
    )
    return FrozenAssociationResidualSampleCustody(
        seed=checked_seed,
        datasets=datasets,
        batch_schedules=schedules,
        model_seed_entropy=int(model_child.entropy),
        model_seed_spawn_key=tuple(model_child.spawn_key),
        model_seed_pool_size=int(model_child.pool_size),
        model_seed_state=model_state,
    )


__all__ = [
    "BATCH_SIZE",
    "PAIRED_SEEDS",
    "PRIMARY_UPDATES",
    "SAMPLE_BUDGETS",
    "STRONGER_UPDATES",
    "FrozenAssociationResidualBatchSchedule",
    "FrozenAssociationResidualSampleCustody",
    "FrozenAssociationResidualSampleDataset",
    "build_frozen_association_residual_sample_custody",
]
