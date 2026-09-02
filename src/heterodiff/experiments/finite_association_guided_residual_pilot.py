"""Frozen A1 association-guide residual experiment.

This file currently implements the result-independent fixture and prerequisite
gate from ``research/62_a1_association_guided_residual_falsification_spec.md``.
It deliberately does not train a learner.  A candidate comparison may be
added only after the exact law, guide, residual, splits, and serialized-array
digests pass this prerequisite stage.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Dict, Tuple

import numpy as np

from heterodiff.models.finite_bridge_residual import exact_residual_log_grid
from heterodiff.theory import (
    FiniteAtomicAssociationBridgeOracle,
    FiniteAtomicCountingSpace,
    FiniteBridgePopulation,
    IndependentFiniteAtomicReferenceGuide,
    OVERFLOW_OBSERVATION,
    PositiveFiniteAtomicOverflowObservation,
    capped_counting_reference,
    finite_bridge_population,
)


_TERMINAL_TIME = 1.0
_TIME_POINT_COUNT = 33
_FAMILY_ORDER = ("birth", "death", "replacement")

FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS = (
    "69b4bbea518ab816bb1e96952c3ddda5295257f66f0f8c902ba38eec10b6c339",
    "2c9da1e2e4d98e14d91459983a3b8fcbbf4b5409574863f68cba96642a89f08b",
    "09273f6bcee7c1a09165392e6ecf0125157b747d242c1f993a982ce3b2833cc7",
    "d6326ffb38c4c3ccf5aed1002f8cbd75fe5411f60d07172d5511730a63daba45",
    "ff37337476c48fee1c01e812f78cd22c7f2ed69298329f79cd87ab2aab3de937",
)

# Retained only so the NumPy-only compatibility regression can fail closed on
# unexpected drift.  Learner execution never accepts this Python 3.9/SciPy
# 1.9 serialization; its runner requires the tuple above.
FROZEN_ASSOCIATION_COMPATIBILITY_DIGESTS = (
    "69b4bbea518ab816bb1e96952c3ddda5295257f66f0f8c902ba38eec10b6c339",
    "2c9da1e2e4d98e14d91459983a3b8fcbbf4b5409574863f68cba96642a89f08b",
    "3da1e11dd3a7c939e93d63932792367335a25a9c65d03a5e6c95caa3d1f325ce",
    "a960c8037ca0d445cbddadf3c368d8aaeee08dc93be150a1e0de90d3d212f1f5",
    "ff37337476c48fee1c01e812f78cd22c7f2ed69298329f79cd87ab2aab3de937",
)


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    contiguous = np.array(array, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=np.float64
    ).reshape(contiguous.shape)


def _immutable_int_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.int64)
    contiguous = np.array(array, dtype=np.int64, copy=True, order="C")
    return np.frombuffer(
        contiguous.tobytes(order="C"), dtype=np.int64
    ).reshape(contiguous.shape)


def _array_digest(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for value in arrays:
        array = np.ascontiguousarray(value)
        descriptor = "%s|%s|" % (
            array.dtype.str,
            ",".join(str(int(size)) for size in array.shape),
        )
        digest.update(descriptor.encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def frozen_association_fixture_sha256(
    digests: Tuple[str, ...] = FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS,
) -> str:
    """Return the versioned custody token for the five prerequisite hashes."""

    if type(digests) is not tuple or len(digests) != 5:
        raise TypeError("digests must be the five-item prerequisite tuple")
    payload = hashlib.sha256()
    payload.update(b"heterodiff-a1-association-fixture-v1\0")
    for value in digests:
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError("every prerequisite digest must be SHA-256 hexadecimal")
        try:
            int(value, 16)
        except ValueError as error:
            raise ValueError(
                "every prerequisite digest must be SHA-256 hexadecimal"
            ) from error
        if value != value.lower():
            raise ValueError("prerequisite digests must use lowercase hexadecimal")
        payload.update(value.encode("ascii"))
        payload.update(b"\0")
    return payload.hexdigest()


def frozen_association_fixture_content_digests(
    fixture: "FrozenAssociationResidualFixture",
    splits: "FrozenAssociationResidualSplits" = None,
) -> Tuple[str, ...]:
    """Recompute the five content identities from an actual supplied fixture."""

    if type(fixture) is not FrozenAssociationResidualFixture:
        raise TypeError("fixture must be a FrozenAssociationResidualFixture")
    if splits is None:
        checked_splits = frozen_association_residual_splits(fixture)
    elif type(splits) is FrozenAssociationResidualSplits:
        checked_splits = splits
    else:
        raise TypeError("splits must be FrozenAssociationResidualSplits or None")
    observation = fixture.observation
    population = fixture.population
    return (
        _array_digest(fixture.oracle.generator),
        _array_digest(
            observation.reference_mass,
            observation.clean_kernel_mass,
            observation.kernel_mass,
            observation.density_kernel,
        ),
        _array_digest(
            population.times,
            population.time_marginal,
            population.observation_marginal_mass,
            population.joint_mass,
            population.product_mass,
            population.backward_information_density,
            population.optimal_log_density_ratio,
        ),
        _array_digest(
            fixture.guide.one_particle_subgenerator,
            fixture.guide.terminal_emission_mass,
            fixture.guide_density_grid,
            fixture.exact_residual_grid,
        ),
        checked_splits.digest,
    )


@dataclass(frozen=True, eq=False)
class FrozenAssociationResidualFixture:
    latent_space: FiniteAtomicCountingSpace
    retained_observation_space: FiniteAtomicCountingSpace
    observation: PositiveFiniteAtomicOverflowObservation
    oracle: FiniteAtomicAssociationBridgeOracle
    guide: IndependentFiniteAtomicReferenceGuide
    initial_marginal: np.ndarray
    times: np.ndarray
    population: FiniteBridgePopulation
    guide_density_grid: np.ndarray
    exact_residual_grid: np.ndarray

    def __post_init__(self) -> None:
        state_count = self.latent_space.n_states
        observation_count = self.observation.n_observations
        expected = (self.times.size, state_count, observation_count)
        if self.guide_density_grid.shape != expected:
            raise ValueError("guide_density_grid has an inconsistent shape")
        if self.exact_residual_grid.shape != expected:
            raise ValueError("exact_residual_grid has an inconsistent shape")
        object.__setattr__(
            self, "initial_marginal", _immutable_float_array(self.initial_marginal)
        )
        object.__setattr__(self, "times", _immutable_float_array(self.times))
        object.__setattr__(
            self,
            "guide_density_grid",
            _immutable_float_array(self.guide_density_grid),
        )
        object.__setattr__(
            self,
            "exact_residual_grid",
            _immutable_float_array(self.exact_residual_grid),
        )


@dataclass(frozen=True, eq=False)
class FrozenAssociationResidualSplits:
    train_times: np.ndarray
    validation_times: np.ndarray
    test_times: np.ndarray
    train_pairs: np.ndarray
    validation_pairs: np.ndarray
    test_pairs: np.ndarray
    latent_three_pairs: np.ndarray
    anchor_three_pairs: np.ndarray
    both_three_pairs: np.ndarray
    overflow_pairs: np.ndarray

    def __post_init__(self) -> None:
        for name in (
            "train_times",
            "validation_times",
            "test_times",
            "train_pairs",
            "validation_pairs",
            "test_pairs",
            "latent_three_pairs",
            "anchor_three_pairs",
            "both_three_pairs",
            "overflow_pairs",
        ):
            value = np.asarray(getattr(self, name))
            expected_ndim = 1 if name.endswith("times") else 2
            if value.ndim != expected_ndim or value.size == 0:
                raise ValueError("%s has an invalid shape" % name)
            if expected_ndim == 2 and value.shape[1] != 2:
                raise ValueError("%s must contain state/observation pairs" % name)
            object.__setattr__(self, name, _immutable_int_array(value))

    @property
    def digest(self) -> str:
        return _array_digest(
            self.train_times,
            self.validation_times,
            self.test_times,
            self.train_pairs,
            self.validation_pairs,
            self.test_pairs,
            self.latent_three_pairs,
            self.anchor_three_pairs,
            self.both_three_pairs,
            self.overflow_pairs,
        )


@dataclass(frozen=True)
class AssociationResidualPrerequisiteResult:
    generator_digest: str
    observation_digest: str
    population_digest: str
    guide_digest: str
    split_digest: str
    generator_row_sum_residual: float
    association_determinant: float
    ambiguous_permanent: float
    clean_overflow_minimum: float
    clean_overflow_maximum: float
    density_minimum: float
    density_maximum: float
    terminal_guide_log_error: float
    maximum_terminal_residual: float
    maximum_retained_initial_residual: float
    maximum_overall_initial_residual: float
    joint_weighted_initial_absolute_residual: float
    initial_overflow_probability: float
    retained_weighted_residual_share: float
    immigrant_terminal_mean: np.ndarray
    immigrant_anchor_intensity: np.ndarray
    target_harmonicity_residual: float
    guide_rank_propagation_residual: float
    correction_scale_ratio: float
    pair_partition_sizes: np.ndarray
    passed: bool
    failures: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "generator_digest",
            "observation_digest",
            "population_digest",
            "guide_digest",
            "split_digest",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) != 64:
                raise ValueError("%s must be a SHA-256 hexadecimal digest" % name)
            try:
                int(value, 16)
            except ValueError as error:
                raise ValueError("%s must be hexadecimal" % name) from error
        scalar_names = (
            "generator_row_sum_residual",
            "association_determinant",
            "ambiguous_permanent",
            "clean_overflow_minimum",
            "clean_overflow_maximum",
            "density_minimum",
            "density_maximum",
            "terminal_guide_log_error",
            "maximum_terminal_residual",
            "maximum_retained_initial_residual",
            "maximum_overall_initial_residual",
            "joint_weighted_initial_absolute_residual",
            "initial_overflow_probability",
            "retained_weighted_residual_share",
            "target_harmonicity_residual",
            "guide_rank_propagation_residual",
            "correction_scale_ratio",
        )
        for name in scalar_names:
            value = float(getattr(self, name))
            if not math.isfinite(value):
                raise ValueError("%s must be finite" % name)
            object.__setattr__(self, name, value)
        for name, shape in (
            ("immigrant_terminal_mean", (3,)),
            ("immigrant_anchor_intensity", (3,)),
            ("pair_partition_sizes", (3,)),
        ):
            value = np.asarray(getattr(self, name))
            if value.shape != shape or not np.all(np.isfinite(value)):
                raise ValueError("%s has an invalid value" % name)
            immutable = (
                _immutable_int_array(value)
                if name == "pair_partition_sizes"
                else _immutable_float_array(value)
            )
            object.__setattr__(self, name, immutable)
        if not isinstance(self.passed, bool):
            raise TypeError("passed must be boolean")
        if type(self.failures) is not tuple or not all(
            isinstance(item, str) and item for item in self.failures
        ):
            raise TypeError("failures must be a tuple of nonempty strings")
        if self.passed != (len(self.failures) == 0):
            raise ValueError("passed must be equivalent to an empty failure list")


def build_frozen_association_residual_fixture() -> FrozenAssociationResidualFixture:
    latent_space = FiniteAtomicCountingSpace(("s1", "s2", "s3"), 3)
    retained_space = FiniteAtomicCountingSpace(("a1", "a2", "a3"), 3)
    observation = PositiveFiniteAtomicOverflowObservation(
        latent_space,
        retained_space,
        detection_probability=(0.72, 0.63, 0.68),
        confusion_matrix=(
            (0.62, 0.25, 0.13),
            (0.22, 0.58, 0.20),
            (0.18, 0.27, 0.55),
        ),
        observation_clutter_rates=(0.10, 0.08, 0.12),
        contamination_probability=0.08,
    )
    replacement = (
        (0.0, 0.16, 0.07),
        (0.11, 0.0, 0.15),
        (0.09, 0.13, 0.0),
    )
    oracle = FiniteAtomicAssociationBridgeOracle(
        latent_space,
        observation,
        birth_rates=(0.38, 0.30, 0.24),
        per_particle_death_rates=(0.28, 0.34, 0.25),
        replacement_rates=replacement,
    )
    guide = IndependentFiniteAtomicReferenceGuide(
        latent_space,
        observation,
        terminal_time=_TERMINAL_TIME,
        immigration_rates=(0.38, 0.30, 0.24),
        per_particle_death_rates=(0.28, 0.34, 0.25),
        replacement_rates=replacement,
    )
    initial = capped_counting_reference(latent_space, (0.65, 0.50, 0.40))
    times = np.linspace(
        0.0, _TERMINAL_TIME, _TIME_POINT_COUNT, dtype=np.float64
    )
    population = finite_bridge_population(
        oracle, initial, times, _TERMINAL_TIME
    )
    guide_grid = np.stack(
        [guide.density_grid(float(time)) for time in times], axis=0
    )
    residual = exact_residual_log_grid(
        population.backward_information_density, guide_grid
    )
    return FrozenAssociationResidualFixture(
        latent_space=latent_space,
        retained_observation_space=retained_space,
        observation=observation,
        oracle=oracle,
        guide=guide,
        initial_marginal=initial,
        times=times,
        population=population,
        guide_density_grid=guide_grid,
        exact_residual_grid=residual,
    )


def frozen_association_residual_splits(
    fixture: FrozenAssociationResidualFixture,
) -> FrozenAssociationResidualSplits:
    if not isinstance(fixture, FrozenAssociationResidualFixture):
        raise TypeError("fixture must be a FrozenAssociationResidualFixture")
    latent_states = fixture.latent_space.states
    observations = fixture.observation.observations
    low_states = tuple(
        index for index, counts in enumerate(latent_states) if sum(counts) <= 2
    )
    low_observations = tuple(
        index
        for index, counts in enumerate(observations[:-1])
        if sum(counts) <= 2
    )
    cardinality_three_states = tuple(
        index for index, counts in enumerate(latent_states) if sum(counts) == 3
    )
    cardinality_three_observations = tuple(
        index
        for index, counts in enumerate(observations[:-1])
        if sum(counts) == 3
    )

    partitions: Dict[int, list] = {value: [] for value in range(5)}
    for state_index in low_states:
        state = latent_states[state_index]
        for observation_index in low_observations:
            observed = observations[observation_index]
            if observed is OVERFLOW_OBSERVATION:
                raise AssertionError("overflow entered the retained pair split")
            hash_value = (
                3 * state[0]
                + 5 * state[1]
                + 7 * state[2]
                + 11 * observed[0]
                + 13 * observed[1]
                + 17 * observed[2]
                + 19 * sum(state) * sum(observed)
            ) % 5
            partitions[hash_value].append((state_index, observation_index))

    train_pairs = partitions[0] + partitions[1] + partitions[2]
    validation_pairs = partitions[3]
    test_pairs = partitions[4]
    if not all(
        any(pair[0] == state for pair in train_pairs) for state in low_states
    ):
        raise ArithmeticError("the train split omits a low-cardinality state")
    if not all(
        any(pair[1] == observed for pair in train_pairs)
        for observed in low_observations
    ):
        raise ArithmeticError("the train split omits a low-cardinality observation")

    latent_three_pairs = [
        (state, observed)
        for state in cardinality_three_states
        for observed in low_observations
    ]
    anchor_three_pairs = [
        (state, observed)
        for state in low_states
        for observed in cardinality_three_observations
    ]
    both_three_pairs = [
        (state, observed)
        for state in cardinality_three_states
        for observed in cardinality_three_observations
    ]
    overflow_pairs = [
        (state, fixture.observation.overflow_index)
        for state in range(fixture.latent_space.n_states)
    ]
    return FrozenAssociationResidualSplits(
        train_times=np.arange(0, 32, 2, dtype=np.int64),
        validation_times=np.arange(1, 32, 4, dtype=np.int64),
        test_times=np.arange(3, 32, 4, dtype=np.int64),
        train_pairs=np.asarray(train_pairs, dtype=np.int64),
        validation_pairs=np.asarray(validation_pairs, dtype=np.int64),
        test_pairs=np.asarray(test_pairs, dtype=np.int64),
        latent_three_pairs=np.asarray(latent_three_pairs, dtype=np.int64),
        anchor_three_pairs=np.asarray(anchor_three_pairs, dtype=np.int64),
        both_three_pairs=np.asarray(both_three_pairs, dtype=np.int64),
        overflow_pairs=np.asarray(overflow_pairs, dtype=np.int64),
    )


def _centered_correction_rms(
    correction: np.ndarray,
    weights: np.ndarray,
) -> float:
    centered = np.array(correction, dtype=np.float64, copy=True)
    for time_index in range(centered.shape[0]):
        for observation_index in range(centered.shape[2]):
            cell_weights = weights[time_index, :, observation_index]
            total = math.fsum(float(value) for value in cell_weights)
            if total <= 0.0:
                raise ArithmeticError("correction weights must be positive")
            mean = float(
                np.dot(cell_weights, centered[time_index, :, observation_index])
                / total
            )
            centered[time_index, :, observation_index] -= mean
    numerator = float(np.sum(weights * centered * centered))
    denominator = float(np.sum(weights))
    return math.sqrt(numerator / denominator)


def run_association_residual_prerequisite_gate(
) -> AssociationResidualPrerequisiteResult:
    fixture = build_frozen_association_residual_fixture()
    splits = frozen_association_residual_splits(fixture)
    population = fixture.population
    observation = fixture.observation
    residual = fixture.exact_residual_grid

    emission = (
        observation.detection_probability[:, None] * observation.confusion_matrix
    )
    anchor_by_source = emission.T
    determinant = float(np.linalg.det(anchor_by_source))
    permanent = math.fsum(
        float(anchor_by_source[0, first])
        * float(anchor_by_source[1, second])
        * float(anchor_by_source[2, third])
        for first, second, third in (
            (0, 1, 2),
            (0, 2, 1),
            (1, 0, 2),
            (1, 2, 0),
            (2, 0, 1),
            (2, 1, 0),
        )
    )

    terminal_log_error = float(
        np.max(
            np.abs(
                np.log(fixture.guide_density_grid[-1])
                - observation.log_density_kernel
            )
        )
    )
    maximum_terminal_residual = float(np.max(np.abs(residual[-1])))
    maximum_retained_initial = float(np.max(np.abs(residual[0, :, :-1])))
    maximum_overall_initial = float(np.max(np.abs(residual[0])))
    joint_initial_weights = population.joint_mass[0]
    weighted_absolute = joint_initial_weights * np.abs(residual[0])
    joint_weighted_absolute = float(np.sum(weighted_absolute))
    retained_weighted = float(np.sum(weighted_absolute[:, :-1]))
    retained_share = retained_weighted / joint_weighted_absolute

    harmonicity = 0.0
    for index in range(fixture.times.size - 1):
        elapsed = float(fixture.times[index + 1] - fixture.times[index])
        propagated = (
            fixture.oracle.forward_transition(elapsed)
            @ population.backward_information_density[index + 1]
        )
        harmonicity = max(
            harmonicity,
            float(
                np.max(
                    np.abs(
                        propagated - population.backward_information_density[index]
                    )
                )
            ),
        )

    rank_residual = 0.0
    for direct_time in (0.0, 0.25, 0.5, 0.75, 1.0):
        expected = (
            fixture.guide.survival_transition(direct_time)
            @ fixture.guide.terminal_emission_mass
        )
        rank_residual = max(
            rank_residual,
            float(
                np.max(
                    np.abs(
                        expected
                        - fixture.guide.effective_emission_mass(direct_time)
                    )
                )
            ),
        )

    terminal_classifier = (
        observation.log_density_kernel
        - np.log(population.observation_marginal_density)[None, :]
    )
    remaining = 1.0 - fixture.times[:-1]
    direct_correction = (
        population.optimal_log_density_ratio[:-1]
        - terminal_classifier[None, :, :]
    ) / remaining[:, None, None]
    residual_correction = residual[:-1] / remaining[:, None, None]
    weights = 0.5 * (
        population.joint_mass[:-1] + population.product_mass[:-1]
    )
    direct_scale = _centered_correction_rms(direct_correction, weights)
    residual_scale = _centered_correction_rms(residual_correction, weights)
    correction_ratio = residual_scale / direct_scale

    generator_digest = _array_digest(fixture.oracle.generator)
    observation_digest = _array_digest(
        observation.reference_mass,
        observation.clean_kernel_mass,
        observation.kernel_mass,
        observation.density_kernel,
    )
    population_digest = _array_digest(
        population.times,
        population.time_marginal,
        population.observation_marginal_mass,
        population.joint_mass,
        population.product_mass,
        population.backward_information_density,
        population.optimal_log_density_ratio,
    )
    guide_digest = _array_digest(
        fixture.guide.one_particle_subgenerator,
        fixture.guide.terminal_emission_mass,
        fixture.guide_density_grid,
        fixture.exact_residual_grid,
    )
    prerequisite_digests = (
        generator_digest,
        observation_digest,
        population_digest,
        guide_digest,
        splits.digest,
    )

    failures = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    row_residual = float(np.max(np.abs(fixture.oracle.generator.sum(axis=1))))
    require(row_residual <= 1.0e-12, "target generator row sums")
    require(
        fixture.oracle.active_transition_families == _FAMILY_ORDER,
        "all target edit families",
    )
    require(abs(determinant - 0.0423190656) <= 1.0e-8, "rank-three determinant")
    require(abs(permanent - 0.090006360192) <= 1.0e-8, "ambiguous permanent")
    require(
        abs(float(np.min(observation.clean_kernel_mass[:, -1]))
            - 0.0002658111900217808)
        <= 1.0e-8,
        "minimum overflow witness",
    )
    require(
        abs(float(np.max(observation.clean_kernel_mass[:, -1]))
            - 0.11343860759109892)
        <= 1.0e-8,
        "maximum overflow witness",
    )
    require(terminal_log_error <= 1.0e-12, "terminal guide identity")
    require(maximum_terminal_residual <= 1.0e-10, "terminal-zero residual")
    require(
        abs(maximum_retained_initial - 0.28651014165) <= 1.0e-8,
        "retained residual nontriviality",
    )
    require(
        abs(maximum_overall_initial - 0.99836959565) <= 1.0e-8,
        "overall residual nontriviality",
    )
    require(joint_weighted_absolute >= 0.05, "weighted residual nontriviality")
    require(
        float(population.observation_marginal_mass[-1]) <= 0.05,
        "overflow marginal ceiling",
    )
    require(retained_share >= 0.60, "retained residual contribution")
    require(harmonicity <= 2.0e-12, "target information harmonicity")
    require(rank_residual <= 1.0e-13, "guide rank propagation")
    require(correction_ratio <= 0.70, "residual correction scale")
    require(
        prerequisite_digests
        in (
            FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS,
            FROZEN_ASSOCIATION_COMPATIBILITY_DIGESTS,
        ),
        "frozen prerequisite digests",
    )
    require(
        tuple(len(value) for value in (
            splits.train_pairs, splits.validation_pairs, splits.test_pairs
        ))
        == (61, 19, 20),
        "frozen pair partition sizes",
    )

    return AssociationResidualPrerequisiteResult(
        generator_digest=generator_digest,
        observation_digest=observation_digest,
        population_digest=population_digest,
        guide_digest=guide_digest,
        split_digest=splits.digest,
        generator_row_sum_residual=row_residual,
        association_determinant=determinant,
        ambiguous_permanent=permanent,
        clean_overflow_minimum=float(
            np.min(observation.clean_kernel_mass[:, -1])
        ),
        clean_overflow_maximum=float(
            np.max(observation.clean_kernel_mass[:, -1])
        ),
        density_minimum=observation.lower_bound,
        density_maximum=observation.upper_bound,
        terminal_guide_log_error=terminal_log_error,
        maximum_terminal_residual=maximum_terminal_residual,
        maximum_retained_initial_residual=maximum_retained_initial,
        maximum_overall_initial_residual=maximum_overall_initial,
        joint_weighted_initial_absolute_residual=joint_weighted_absolute,
        initial_overflow_probability=float(
            population.observation_marginal_mass[-1]
        ),
        retained_weighted_residual_share=retained_share,
        immigrant_terminal_mean=fixture.guide.immigrant_terminal_mean(0.0),
        immigrant_anchor_intensity=fixture.guide.immigrant_anchor_intensity(0.0),
        target_harmonicity_residual=harmonicity,
        guide_rank_propagation_residual=rank_residual,
        correction_scale_ratio=correction_ratio,
        pair_partition_sizes=np.asarray(
            (
                len(splits.train_pairs),
                len(splits.validation_pairs),
                len(splits.test_pairs),
            ),
            dtype=np.int64,
        ),
        passed=len(failures) == 0,
        failures=tuple(failures),
    )


__all__ = [
    "AssociationResidualPrerequisiteResult",
    "FROZEN_ASSOCIATION_COMPATIBILITY_DIGESTS",
    "FROZEN_ASSOCIATION_PREREQUISITE_DIGESTS",
    "FrozenAssociationResidualFixture",
    "FrozenAssociationResidualSplits",
    "build_frozen_association_residual_fixture",
    "frozen_association_fixture_content_digests",
    "frozen_association_fixture_sha256",
    "frozen_association_residual_splits",
    "run_association_residual_prerequisite_gate",
]
