"""Frozen, result-independent A1 association rank-stress infrastructure.

This module implements the result-independent infrastructure for Section 9 of
``research/62_a1_association_guided_residual_falsification_spec.md``.  It
freezes the eight-source/eight-anchor law, its exact positive Vandermonde
factorization, canonical input serialization, and implementation-independent
operation/allocation accounting.  It exposes analytic and independent
coefficient-oracle evaluators, but importing or preparing a fixture never
executes the complete ``33 x 45 x 46`` decision grid.  The analytic evaluator
counts visible owners once, holds a conservative SciPy matrix-exponential
workspace reservation live across each call, and avoids other hidden numeric
kernel workspaces with preallocated scalar contractions.  Section 9 is still
fail-closed until its explicit fresh-process launcher executes all ranks,
all times, one warm-up, five timed repetitions, and the independent oracle.
Before the first timer starts, that worker durably writes every canonical
array payload and individual digest to an fsync-backed PREPARED companion.

The analytic lane uses only fixed-rank coefficient recurrences and final
coefficient contractions.  It does not enumerate occurrence-level matchings.
The exhaustive lane independently expands the ordinary anchor-count PGF and
is deliberately excluded from analytic counters.
"""

from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import asdict, dataclass
import base64
from fractions import Fraction
import hashlib
import io
import json
import math
from numbers import Integral
import os
from pathlib import Path
import platform
import resource
import secrets
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Sequence, Tuple

import numpy as np
import scipy
from scipy.linalg import expm

from heterodiff.theory import FiniteAtomicCountingSpace


RANK_STRESS_RANKS = (1, 2, 3, 4, 8)
RANK_STRESS_TIME_POINT_COUNT = 33
RANK_STRESS_MAXIMUM_COEFFICIENT_UPDATES = 50_000_000
RANK_STRESS_MAXIMUM_OWNED_NUMERIC_BYTES = 8 * 5_000_000
RANK_STRESS_RELATIVE_AGREEMENT_TOLERANCE = 1.0e-10
RANK_STRESS_BENCHMARK_WARMUP_COUNT = 1
RANK_STRESS_BENCHMARK_REPETITION_COUNT = 5
RANK_STRESS_ANALYTIC_ALGORITHM_ID = (
    "fixed-rank-coefficient-recurrence-and-contraction-v1"
)
RANK_STRESS_OCCURRENCE_MATCHING_ENUMERATION_USED = False
RANK_STRESS_SCIPY_EXPM_MATRIX_ORDER = 16
# scipy.linalg.expm documents worst-case workspace of order eight n-by-n
# arrays for a real double input.  We reserve all eight arrays *in addition*
# to the registered input and returned output.  This deliberate double count
# is conservative for the frozen 16-by-16 call.
RANK_STRESS_SCIPY_EXPM_WORKSPACE_FLOAT64_ENTRIES = (
    8 * RANK_STRESS_SCIPY_EXPM_MATRIX_ORDER**2
)
RANK_STRESS_SCIPY_EXPM_WORKSPACE_BOUND_BYTES = (
    8 * RANK_STRESS_SCIPY_EXPM_WORKSPACE_FLOAT64_ENTRIES
)
RANK_STRESS_NUMPY_KERNEL_WORKSPACE_BOUND_BYTES = 0
RANK_STRESS_FULL_OUTPUT_BYTES = 33 * 45 * 46 * 8
RANK_STRESS_DENSITY_SHAPE = (33, 45, 46)
RANK_STRESS_EXPECTED_FULL_GRID_UPDATES = MappingProxyType(
    {
        1: 188_793,
        2: 353_001,
        3: 564_729,
        4: 823_977,
        8: 2_336_169,
    }
)
RANK_STRESS_EXPECTED_MANIFEST_SHA256 = MappingProxyType(
    {
        1: "56a5ac75e53fca408140e96e96ed6cebdbaaaaa1e720085d44f3e6a282b0e714",
        2: "89295c072747342e6a0055fabb615bfd68223919a5199c5c58116fd015605023",
        3: "c33161cb46853abf1c60e7f53b15573c147850e18379734026133d86170f780f",
        4: "1c07b4421289459cc3506efd907466b93013767f6796426fc0595ebd90356723",
        8: "fc8d29892b09772506c996a3267d22a594901cb616e28a840068c68655684ba0",
    }
)
RANK_STRESS_RESULT_SCHEMA = "heterodiff-association-rank-stress-result-v2"
RANK_STRESS_RUNTIME_SCHEMA = "heterodiff-association-rank-stress-runtime-v1"
RANK_STRESS_SUITE_SCHEMA = "heterodiff-association-rank-stress-suite-v1"
RANK_STRESS_PREPARED_SCHEMA = "heterodiff-association-rank-stress-prepared-v1"
RANK_STRESS_LOADER_RECEIPT_SCHEMA = (
    "heterodiff-association-rank-stress-loader-receipt-v1"
)
RANK_STRESS_EXPECTED_PYTHON_VERSION = "3.11.5"
RANK_STRESS_EXPECTED_NUMPY_VERSION = "2.4.6"
RANK_STRESS_EXPECTED_SCIPY_VERSION = "1.17.1"
RANK_STRESS_EXPECTED_THREADPOOLCTL_VERSION = "3.6.0"
RANK_STRESS_FRESH_PROCESS_MARKER = "HETERODIFF_RANK_STRESS_FRESH_PROCESS"
RANK_STRESS_FRESH_PROCESS_NONCE = "HETERODIFF_RANK_STRESS_FRESH_NONCE"
RANK_STRESS_THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
)
_IMPORT_FRESH_MARKER = os.environ.get(RANK_STRESS_FRESH_PROCESS_MARKER)
_IMPORT_FRESH_NONCE = os.environ.get(RANK_STRESS_FRESH_PROCESS_NONCE)
_IMPORT_PROCESS_ID = os.getpid()
_FRESH_PROCESS_PERMIT_KEY = object()
_LOADER_VERIFIED_RESULT_KEY = object()
_CONSUMED_FRESH_NONCES = set()
RANK_STRESS_UNEXECUTED_REQUIREMENTS = (
    "execute exhaustive agreement at all 33 times for every frozen rank",
    "record one warm-up and median of five wall-time repetitions",
    "record Python/NumPy/SciPy, OS, CPU, BLAS, thread, and peak-RSS metadata",
    "report Python-object overhead separately from owned numeric buffers",
    "run the audited protocol in a launcher-created fresh process",
)

_TYPE_COUNT = 8
_CARDINALITY_CAP = 2
_OBSERVATION_COUNT = 46
_CONTAMINATION_PROBABILITY = 0.08
_NUMERICAL_TOLERANCE = 2.0e-12
_SERIALIZATION_DOMAIN = b"heterodiff-association-rank-stress-array-v1\n"


def _canonical_json(value: object) -> bytes:
    try:
        serialized = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise TypeError("value is not canonical-JSON serializable") from error
    return serialized.encode("ascii")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _lower_sha256(value: object, *, name: str) -> str:
    if type(value) is not str or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("%s must be a lowercase SHA-256 digest" % name)
    return value


def _numeric_array_sha256(value: object) -> str:
    array = np.asarray(value)
    if array.dtype.kind not in "biufc":
        raise TypeError("only numeric arrays can be hashed")
    if array.dtype.kind in "biu":
        canonical = np.ascontiguousarray(array, dtype=np.dtype("<i8"))
    elif array.dtype.kind == "c":
        canonical = np.ascontiguousarray(array, dtype=np.dtype("<c16"))
    else:
        canonical = np.ascontiguousarray(array, dtype=np.dtype("<f8"))
    descriptor = {
        "dtype": canonical.dtype.str,
        "shape": tuple(int(size) for size in canonical.shape),
        "bytes_sha256": hashlib.sha256(canonical.tobytes(order="C")).hexdigest(),
    }
    return _sha256_json(descriptor)


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


def _validated_rank(value: object) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("rank must be an integer non-boolean value")
    rank = int(value)
    if rank not in RANK_STRESS_RANKS:
        raise ValueError("rank must be one of %r" % (RANK_STRESS_RANKS,))
    return rank


def _validated_time_index(value: object) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("time_index must be an integer non-boolean value")
    index = int(value)
    if index < 0 or index >= RANK_STRESS_TIME_POINT_COUNT:
        raise IndexError("time_index must lie between zero and 32")
    return index


def _fraction_matrix_rank(matrix: Sequence[Sequence[Fraction]]) -> int:
    """Return exact ordinary rank by rational row reduction."""

    work = [list(row) for row in matrix]
    if not work:
        return 0
    width = len(work[0])
    if any(len(row) != width for row in work):
        raise ValueError("matrix must be rectangular")
    pivot_row = 0
    for column in range(width):
        selected = next(
            (
                row
                for row in range(pivot_row, len(work))
                if work[row][column] != 0
            ),
            None,
        )
        if selected is None:
            continue
        work[pivot_row], work[selected] = work[selected], work[pivot_row]
        pivot = work[pivot_row][column]
        work[pivot_row] = [entry / pivot for entry in work[pivot_row]]
        for row in range(len(work)):
            if row == pivot_row:
                continue
            multiplier = work[row][column]
            if multiplier == 0:
                continue
            work[row] = [
                entry - multiplier * pivot_entry
                for entry, pivot_entry in zip(work[row], work[pivot_row])
            ]
        pivot_row += 1
        if pivot_row == len(work):
            break
    return pivot_row


def exact_vandermonde_emission_rank(rank: object) -> int:
    """Validate the frozen emission matrix's ordinary rank over rationals."""

    selected_rank = _validated_rank(rank)
    matrix = []
    for source in range(_TYPE_COUNT):
        unnormalized = [
            sum(
                Fraction(((source + 1) * (anchor + 1)) ** power, 81**power)
                for power in range(selected_rank)
            )
            for anchor in range(_TYPE_COUNT)
        ]
        row_sum = sum(unnormalized, Fraction(0, 1))
        detection = Fraction(55 + source, 100)
        matrix.append(
            [detection * entry / row_sum for entry in unnormalized]
        )
    return _fraction_matrix_rank(matrix)


@dataclass(frozen=True, eq=False)
class FrozenAssociationRankStressFixture:
    """All frozen arrays for one declared Vandermonde rank."""

    rank: int
    latent_space: FiniteAtomicCountingSpace
    retained_observation_space: FiniteAtomicCountingSpace
    latent_states: np.ndarray
    retained_observations: np.ndarray
    times: np.ndarray
    immigration_rates: np.ndarray
    death_rates: np.ndarray
    replacement_rates: np.ndarray
    one_particle_subgenerator: np.ndarray
    detection_probability: np.ndarray
    vandermonde_mass: np.ndarray
    confusion_matrix: np.ndarray
    terminal_emission_mass: np.ndarray
    observation_clutter_rates: np.ndarray
    reference_mass: np.ndarray
    anchor_factor: np.ndarray
    source_factor: np.ndarray

    def __post_init__(self) -> None:
        selected_rank = _validated_rank(self.rank)
        object.__setattr__(self, "rank", selected_rank)
        if self.latent_space.atom_count != _TYPE_COUNT:
            raise ValueError("latent_space must have eight source types")
        if self.retained_observation_space.atom_count != _TYPE_COUNT:
            raise ValueError("retained_observation_space must have eight anchors")
        if self.latent_space.total_cap != _CARDINALITY_CAP:
            raise ValueError("latent_space must have cap two")
        if self.retained_observation_space.total_cap != _CARDINALITY_CAP:
            raise ValueError("retained_observation_space must have cap two")
        if self.latent_space.n_states != 45:
            raise ValueError("latent_space must contain 45 states")
        if self.retained_observation_space.n_states != 45:
            raise ValueError("retained_observation_space must contain 45 states")

        float_shapes = {
            "times": (RANK_STRESS_TIME_POINT_COUNT,),
            "immigration_rates": (_TYPE_COUNT,),
            "death_rates": (_TYPE_COUNT,),
            "replacement_rates": (_TYPE_COUNT, _TYPE_COUNT),
            "one_particle_subgenerator": (_TYPE_COUNT, _TYPE_COUNT),
            "detection_probability": (_TYPE_COUNT,),
            "vandermonde_mass": (_TYPE_COUNT, _TYPE_COUNT),
            "confusion_matrix": (_TYPE_COUNT, _TYPE_COUNT),
            "terminal_emission_mass": (_TYPE_COUNT, _TYPE_COUNT),
            "observation_clutter_rates": (_TYPE_COUNT,),
            "reference_mass": (_OBSERVATION_COUNT,),
            "anchor_factor": (_TYPE_COUNT, selected_rank),
            "source_factor": (_TYPE_COUNT, selected_rank),
        }
        int_shapes = {
            "latent_states": (45, _TYPE_COUNT),
            "retained_observations": (45, _TYPE_COUNT),
        }
        for name, shape in float_shapes.items():
            value = np.asarray(getattr(self, name), dtype=np.float64)
            if value.shape != shape or not np.all(np.isfinite(value)):
                raise ValueError("%s has an invalid value" % name)
            object.__setattr__(self, name, _immutable_float_array(value))
        for name, shape in int_shapes.items():
            value = np.asarray(getattr(self, name), dtype=np.int64)
            if value.shape != shape or np.any(value < 0):
                raise ValueError("%s has an invalid value" % name)
            object.__setattr__(self, name, _immutable_int_array(value))

        if exact_vandermonde_emission_rank(selected_rank) != selected_rank:
            raise ArithmeticError("frozen emission matrix has the wrong exact rank")
        if not np.allclose(
            self.confusion_matrix.sum(axis=1), 1.0, atol=2.0e-15, rtol=0.0
        ):
            raise ArithmeticError("confusion rows do not normalize")
        if not np.allclose(
            self.terminal_emission_mass,
            self.source_factor @ self.anchor_factor.T,
            atol=2.0e-15,
            rtol=2.0e-15,
        ):
            raise ArithmeticError("frozen low-rank factors do not reconstruct emission")
        if not np.allclose(
            self.terminal_emission_mass.sum(axis=1),
            self.detection_probability,
            atol=2.0e-15,
            rtol=0.0,
        ):
            raise ArithmeticError("terminal emission rows do not match detection")
        if not np.allclose(
            self.reference_mass,
            np.full(_OBSERVATION_COUNT, 1.0 / _OBSERVATION_COUNT),
            atol=0.0,
            rtol=0.0,
        ):
            raise ArithmeticError("reference mass must be exactly uniform in float64")


def build_frozen_association_rank_stress_fixture(
    rank: object,
) -> FrozenAssociationRankStressFixture:
    """Construct one Section 9 fixture without evaluating a density grid."""

    selected_rank = _validated_rank(rank)
    source_names = tuple("s%d" % source for source in range(_TYPE_COUNT))
    anchor_names = tuple("a%d" % anchor for anchor in range(_TYPE_COUNT))
    latent_space = FiniteAtomicCountingSpace(source_names, _CARDINALITY_CAP)
    retained_space = FiniteAtomicCountingSpace(anchor_names, _CARDINALITY_CAP)

    vandermonde = np.empty((_TYPE_COUNT, _TYPE_COUNT), dtype=np.float64)
    for source in range(_TYPE_COUNT):
        for anchor in range(_TYPE_COUNT):
            base = ((source + 1) * (anchor + 1)) / 81.0
            vandermonde[source, anchor] = math.fsum(
                base**power for power in range(selected_rank)
            )
    confusion = vandermonde / vandermonde.sum(axis=1, keepdims=True)
    detection = np.asarray(
        [(55 + source) / 100.0 for source in range(_TYPE_COUNT)], dtype=float
    )
    emission = detection[:, None] * confusion

    anchor_factor = np.empty((_TYPE_COUNT, selected_rank), dtype=float)
    source_factor = np.empty((_TYPE_COUNT, selected_rank), dtype=float)
    row_sums = vandermonde.sum(axis=1)
    for power in range(selected_rank):
        anchor_factor[:, power] = np.asarray(
            [((anchor + 1) / 9.0) ** power for anchor in range(_TYPE_COUNT)]
        )
        source_factor[:, power] = np.asarray(
            [
                detection[source]
                * ((source + 1) / 9.0) ** power
                / row_sums[source]
                for source in range(_TYPE_COUNT)
            ]
        )

    immigration = np.asarray(
        [(source + 1) / 100.0 for source in range(_TYPE_COUNT)], dtype=float
    )
    death = np.asarray(
        [(20 + source) / 100.0 for source in range(_TYPE_COUNT)], dtype=float
    )
    replacement = np.zeros((_TYPE_COUNT, _TYPE_COUNT), dtype=float)
    for source in range(_TYPE_COUNT):
        for destination in range(_TYPE_COUNT):
            if source != destination:
                replacement[source, destination] = (
                    ((source + destination) % 3) + 1
                ) / 1000.0
    subgenerator = replacement.copy()
    np.fill_diagonal(subgenerator, -(death + replacement.sum(axis=1)))

    return FrozenAssociationRankStressFixture(
        rank=selected_rank,
        latent_space=latent_space,
        retained_observation_space=retained_space,
        latent_states=np.asarray(latent_space.states, dtype=np.int64),
        retained_observations=np.asarray(retained_space.states, dtype=np.int64),
        times=np.arange(RANK_STRESS_TIME_POINT_COUNT, dtype=float) / 32.0,
        immigration_rates=immigration,
        death_rates=death,
        replacement_rates=replacement,
        one_particle_subgenerator=subgenerator,
        detection_probability=detection,
        vandermonde_mass=vandermonde,
        confusion_matrix=confusion,
        terminal_emission_mass=emission,
        observation_clutter_rates=np.asarray(
            [(anchor + 1) / 200.0 for anchor in range(_TYPE_COUNT)], dtype=float
        ),
        reference_mass=np.full(_OBSERVATION_COUNT, 1.0 / _OBSERVATION_COUNT),
        anchor_factor=anchor_factor,
        source_factor=source_factor,
    )


@dataclass(frozen=True)
class SerializedRankStressArray:
    name: str
    dtype: str
    shape: Tuple[int, ...]
    payload: bytes
    sha256: str

    def __post_init__(self) -> None:
        if not self.name or type(self.name) is not str:
            raise TypeError("serialized array name must be a nonempty string")
        if type(self.payload) is not bytes or not self.payload:
            raise TypeError("serialized array payload must be nonempty bytes")
        if hashlib.sha256(self.payload).hexdigest() != self.sha256:
            raise ValueError("serialized array digest does not match its payload")


@dataclass(frozen=True)
class RankStressArrayManifest:
    records: Tuple[SerializedRankStressArray, ...]
    aggregate_sha256: str

    def __post_init__(self) -> None:
        names = tuple(record.name for record in self.records)
        if not names or len(set(names)) != len(names):
            raise ValueError("manifest names must be nonempty and unique")
        digest = hashlib.sha256()
        digest.update(b"heterodiff-association-rank-stress-manifest-v1\n")
        for record in self.records:
            digest.update(len(record.payload).to_bytes(8, "big"))
            digest.update(record.payload)
        if digest.hexdigest() != self.aggregate_sha256:
            raise ValueError("aggregate manifest digest is inconsistent")

    @property
    def digests(self) -> Mapping[str, str]:
        return MappingProxyType(
            {record.name: record.sha256 for record in self.records}
        )

    def record(self, name: str) -> SerializedRankStressArray:
        for record in self.records:
            if record.name == name:
                return record
        raise KeyError(name)


def _serialize_array(name: str, value: np.ndarray) -> SerializedRankStressArray:
    array = np.asarray(value)
    if array.dtype.kind not in "biufc":
        raise TypeError("only numeric arrays can enter the frozen manifest")
    if array.dtype.kind in "iu":
        canonical = np.ascontiguousarray(array, dtype=np.dtype("<i8"))
    else:
        canonical = np.ascontiguousarray(array, dtype=np.dtype("<f8"))
    shape = tuple(int(size) for size in canonical.shape)
    descriptor = "%s\n%s\n%s\n" % (
        name,
        canonical.dtype.str,
        ",".join(str(size) for size in shape),
    )
    payload = _SERIALIZATION_DOMAIN + descriptor.encode("ascii") + canonical.tobytes(
        order="C"
    )
    return SerializedRankStressArray(
        name=name,
        dtype=canonical.dtype.str,
        shape=shape,
        payload=payload,
        sha256=hashlib.sha256(payload).hexdigest(),
    )


def build_rank_stress_array_manifest(
    fixture: FrozenAssociationRankStressFixture,
) -> RankStressArrayManifest:
    """Canonically serialize every formula-defining numeric input array."""

    if not isinstance(fixture, FrozenAssociationRankStressFixture):
        raise TypeError("fixture must be a FrozenAssociationRankStressFixture")
    arrays = (
        ("rank", np.asarray([fixture.rank], dtype=np.int64)),
        (
            "contamination_probability",
            np.asarray([_CONTAMINATION_PROBABILITY], dtype=np.float64),
        ),
        ("latent_states", fixture.latent_states),
        ("retained_observations", fixture.retained_observations),
        ("times", fixture.times),
        ("immigration_rates", fixture.immigration_rates),
        ("death_rates", fixture.death_rates),
        ("replacement_rates", fixture.replacement_rates),
        ("one_particle_subgenerator", fixture.one_particle_subgenerator),
        ("detection_probability", fixture.detection_probability),
        ("vandermonde_mass", fixture.vandermonde_mass),
        ("confusion_matrix", fixture.confusion_matrix),
        ("terminal_emission_mass", fixture.terminal_emission_mass),
        ("observation_clutter_rates", fixture.observation_clutter_rates),
        ("reference_mass", fixture.reference_mass),
        ("anchor_factor", fixture.anchor_factor),
        ("source_factor", fixture.source_factor),
    )
    records = tuple(_serialize_array(name, value) for name, value in arrays)
    digest = hashlib.sha256()
    digest.update(b"heterodiff-association-rank-stress-manifest-v1\n")
    for record in records:
        digest.update(len(record.payload).to_bytes(8, "big"))
        digest.update(record.payload)
    return RankStressArrayManifest(records, digest.hexdigest())


def _multiindices(rank: int) -> np.ndarray:
    space = FiniteAtomicCountingSpace(
        tuple("k%d" % index for index in range(rank)), _CARDINALITY_CAP
    )
    return _immutable_int_array(space.states)


def _coefficient_factorials(multiindices: np.ndarray) -> np.ndarray:
    return _immutable_float_array(
        [
            math.prod(math.factorial(int(entry)) for entry in multiindex)
            for multiindex in multiindices
        ]
    )


def _increment_indices(multiindices: np.ndarray) -> np.ndarray:
    lookup = {
        tuple(int(entry) for entry in row): index
        for index, row in enumerate(multiindices)
    }
    result = np.full(multiindices.shape, -1, dtype=np.int64)
    for index, row in enumerate(multiindices):
        if int(np.sum(row)) >= _CARDINALITY_CAP:
            continue
        for channel in range(multiindices.shape[1]):
            destination = list(int(entry) for entry in row)
            destination[channel] += 1
            result[index, channel] = lookup[tuple(destination)]
    return _immutable_int_array(result)


@dataclass(frozen=True)
class RankStressCoefficientUpdateCount:
    observation_recurrence_per_time: int
    source_recurrence_per_time: int
    contractions_per_time: int
    times: int

    def __post_init__(self) -> None:
        for name in (
            "observation_recurrence_per_time",
            "source_recurrence_per_time",
            "contractions_per_time",
            "times",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise TypeError("%s must be a nonnegative integer" % name)

    @property
    def recurrence_per_time(self) -> int:
        return self.observation_recurrence_per_time + self.source_recurrence_per_time

    @property
    def total_per_time(self) -> int:
        return self.recurrence_per_time + self.contractions_per_time

    @property
    def full_grid_total(self) -> int:
        return self.times * self.total_per_time


def direct_rank_stress_loop_bound_count(
    fixture: FrozenAssociationRankStressFixture,
) -> RankStressCoefficientUpdateCount:
    """Second count computed only from the frozen cardinality loop bounds."""

    if not isinstance(fixture, FrozenAssociationRankStressFixture):
        raise TypeError("fixture must be a FrozenAssociationRankStressFixture")
    rank = fixture.rank

    def recurrence_count(cardinalities: np.ndarray) -> int:
        count = 0
        for cardinality_value in cardinalities:
            cardinality = int(cardinality_value)
            for completed_factors in range(cardinality):
                old_coefficients = math.comb(completed_factors + rank, rank)
                count += old_coefficients * (rank + 1)
        return count

    latent_cardinality = fixture.latent_states.sum(axis=1)
    retained_cardinality = fixture.retained_observations.sum(axis=1)
    contractions = 0
    for source_total in latent_cardinality:
        for observation_total in retained_cardinality:
            maximum_degree = min(int(source_total), int(observation_total))
            contractions += math.comb(maximum_degree + rank, rank)
    return RankStressCoefficientUpdateCount(
        observation_recurrence_per_time=recurrence_count(retained_cardinality),
        source_recurrence_per_time=recurrence_count(latent_cardinality),
        contractions_per_time=contractions,
        times=RANK_STRESS_TIME_POINT_COUNT,
    )


@dataclass(frozen=True, eq=False)
class PreparedAssociationRankStressRun:
    """Result-independent custody object constructed before any timing."""

    fixture: FrozenAssociationRankStressFixture
    manifest: RankStressArrayManifest
    multiindices: np.ndarray
    coefficient_totals: np.ndarray
    coefficient_factorials: np.ndarray
    increment_indices: np.ndarray
    latent_cardinalities: np.ndarray
    retained_cardinalities: np.ndarray
    retained_factorials: np.ndarray
    contamination_reference_mass: np.ndarray
    expected_updates: RankStressCoefficientUpdateCount

    def __post_init__(self) -> None:
        if not isinstance(self.fixture, FrozenAssociationRankStressFixture):
            raise TypeError("fixture has the wrong type")
        expected_manifest = build_rank_stress_array_manifest(self.fixture)
        if self.manifest.aggregate_sha256 != expected_manifest.aggregate_sha256:
            raise ValueError("manifest is not bound to the supplied fixture")
        if self.manifest.digests != expected_manifest.digests:
            raise ValueError("manifest records are not bound to the supplied fixture")
        coefficient_count = math.comb(
            self.fixture.rank + _CARDINALITY_CAP, self.fixture.rank
        )
        if self.multiindices.shape != (coefficient_count, self.fixture.rank):
            raise ValueError("multiindices have the wrong shape")
        if self.coefficient_factorials.shape != (coefficient_count,):
            raise ValueError("coefficient_factorials have the wrong shape")
        if self.coefficient_totals.shape != (coefficient_count,):
            raise ValueError("coefficient_totals have the wrong shape")
        if self.increment_indices.shape != (
            coefficient_count,
            self.fixture.rank,
        ):
            raise ValueError("increment_indices have the wrong shape")
        for name in ("latent_cardinalities", "retained_cardinalities"):
            if np.asarray(getattr(self, name)).shape != (45,):
                raise ValueError("%s have the wrong shape" % name)
        if np.asarray(self.retained_factorials).shape != (45,):
            raise ValueError("retained_factorials have the wrong shape")
        if np.asarray(self.contamination_reference_mass).shape != (
            _OBSERVATION_COUNT,
        ):
            raise ValueError("contamination_reference_mass has the wrong shape")
        expected_totals = np.asarray(self.multiindices).sum(axis=1)
        if not np.array_equal(self.coefficient_totals, expected_totals):
            raise ValueError("coefficient_totals do not match multiindices")
        expected_factorials = _coefficient_factorials(self.multiindices)
        if not np.array_equal(self.coefficient_factorials, expected_factorials):
            raise ValueError("coefficient_factorials do not match multiindices")
        expected_increments = _increment_indices(self.multiindices)
        if not np.array_equal(self.increment_indices, expected_increments):
            raise ValueError("increment_indices do not match multiindices")
        if not np.array_equal(
            self.latent_cardinalities, self.fixture.latent_states.sum(axis=1)
        ):
            raise ValueError("latent_cardinalities do not match the fixture")
        if not np.array_equal(
            self.retained_cardinalities,
            self.fixture.retained_observations.sum(axis=1),
        ):
            raise ValueError("retained_cardinalities do not match the fixture")
        expected_retained_factorials = np.asarray(
            [
                math.prod(math.factorial(int(value)) for value in counts)
                for counts in self.fixture.retained_observations
            ],
            dtype=np.float64,
        )
        if not np.array_equal(
            self.retained_factorials, expected_retained_factorials
        ):
            raise ValueError("retained_factorials do not match the fixture")
        if not np.array_equal(
            self.contamination_reference_mass,
            _CONTAMINATION_PROBABILITY * self.fixture.reference_mass,
        ):
            raise ValueError("contamination_reference_mass does not match the fixture")
        object.__setattr__(self, "multiindices", _immutable_int_array(self.multiindices))
        object.__setattr__(
            self, "coefficient_totals", _immutable_int_array(self.coefficient_totals)
        )
        object.__setattr__(
            self,
            "coefficient_factorials",
            _immutable_float_array(self.coefficient_factorials),
        )
        object.__setattr__(
            self, "increment_indices", _immutable_int_array(self.increment_indices)
        )
        object.__setattr__(
            self,
            "latent_cardinalities",
            _immutable_int_array(self.latent_cardinalities),
        )
        object.__setattr__(
            self,
            "retained_cardinalities",
            _immutable_int_array(self.retained_cardinalities),
        )
        object.__setattr__(
            self,
            "retained_factorials",
            _immutable_float_array(self.retained_factorials),
        )
        object.__setattr__(
            self,
            "contamination_reference_mass",
            _immutable_float_array(self.contamination_reference_mass),
        )
        expected = direct_rank_stress_loop_bound_count(self.fixture)
        if self.expected_updates != expected:
            raise ValueError("expected_updates do not match direct loop bounds")


def prepare_association_rank_stress_run(
    rank: object,
) -> PreparedAssociationRankStressRun:
    """Freeze arrays, serialize them, and derive counters; execute no grid."""

    fixture = build_frozen_association_rank_stress_fixture(rank)
    multiindices = _multiindices(fixture.rank)
    retained_factorials = np.asarray(
        [
            math.prod(math.factorial(int(value)) for value in counts)
            for counts in fixture.retained_observations
        ],
        dtype=np.float64,
    )
    return PreparedAssociationRankStressRun(
        fixture=fixture,
        manifest=build_rank_stress_array_manifest(fixture),
        multiindices=multiindices,
        coefficient_totals=multiindices.sum(axis=1),
        coefficient_factorials=_coefficient_factorials(multiindices),
        increment_indices=_increment_indices(multiindices),
        latent_cardinalities=fixture.latent_states.sum(axis=1),
        retained_cardinalities=fixture.retained_observations.sum(axis=1),
        retained_factorials=retained_factorials,
        contamination_reference_mass=(
            _CONTAMINATION_PROBABILITY * fixture.reference_mass
        ),
        expected_updates=direct_rank_stress_loop_bound_count(fixture),
    )


class OwnedNumericAllocationRegistry:
    """Count live backing buffers and conservative external workspaces.

    Array views share one owner entry.  A workspace reservation represents a
    numerical-library buffer whose Python owner is not exposed.  It is live in
    the registry for the complete call that may allocate that buffer, and is
    counted in addition to visible inputs and outputs.
    """

    def __init__(self) -> None:
        self._labels: Dict[str, int] = {}
        self._owners: Dict[int, Tuple[np.ndarray, int, int]] = {}
        self._workspace_labels: Dict[str, int] = {}
        self._current_array_bytes = 0
        self._current_workspace_bytes = 0
        self._current_bytes = 0
        self._peak_bytes = 0
        self._peak_array_bytes = 0
        self._peak_workspace_bytes = 0

    def _update_peak(self) -> None:
        self._current_bytes = (
            self._current_array_bytes + self._current_workspace_bytes
        )
        self._peak_bytes = max(self._peak_bytes, self._current_bytes)
        self._peak_array_bytes = max(
            self._peak_array_bytes, self._current_array_bytes
        )
        self._peak_workspace_bytes = max(
            self._peak_workspace_bytes, self._current_workspace_bytes
        )

    @staticmethod
    def _root_array(array: np.ndarray) -> np.ndarray:
        root = array
        while isinstance(root.base, np.ndarray):
            root = root.base
        return root

    def register(self, label: str, value: np.ndarray) -> None:
        if type(label) is not str or not label:
            raise TypeError("allocation label must be a nonempty string")
        if label in self._labels or label in self._workspace_labels:
            raise ValueError("allocation label is already registered")
        array = np.asarray(value)
        if array.dtype.kind not in "biufc":
            raise TypeError("allocation registry accepts only numeric arrays")
        root = self._root_array(array)
        owner_id = id(root)
        existing = self._owners.get(owner_id)
        if existing is None:
            owned_bytes = int(root.nbytes)
            self._owners[owner_id] = (root, owned_bytes, 1)
            self._current_array_bytes += owned_bytes
            self._update_peak()
        else:
            owner, owned_bytes, references = existing
            self._owners[owner_id] = (owner, owned_bytes, references + 1)
        self._labels[label] = owner_id

    def release(self, label: str) -> None:
        try:
            owner_id = self._labels.pop(label)
        except KeyError as error:
            raise KeyError("allocation label is not registered: %s" % label) from error
        owner, owned_bytes, references = self._owners[owner_id]
        if references == 1:
            del self._owners[owner_id]
            self._current_array_bytes -= owned_bytes
            self._update_peak()
        else:
            self._owners[owner_id] = (owner, owned_bytes, references - 1)

    def reserve_workspace(self, label: str, byte_count: object) -> None:
        """Reserve a conservative bound for a hidden numerical workspace."""

        if type(label) is not str or not label:
            raise TypeError("workspace label must be a nonempty string")
        if label in self._labels or label in self._workspace_labels:
            raise ValueError("allocation label is already registered")
        if isinstance(byte_count, (bool, np.bool_)) or not isinstance(
            byte_count, Integral
        ):
            raise TypeError("workspace byte_count must be an integer")
        size = int(byte_count)
        if size < 0:
            raise ValueError("workspace byte_count must be nonnegative")
        self._workspace_labels[label] = size
        self._current_workspace_bytes += size
        self._update_peak()

    def release_workspace(self, label: str) -> None:
        try:
            size = self._workspace_labels.pop(label)
        except KeyError as error:
            raise KeyError(
                "workspace label is not registered: %s" % label
            ) from error
        self._current_workspace_bytes -= size
        self._update_peak()

    @property
    def current_owned_numeric_bytes(self) -> int:
        return self._current_bytes

    @property
    def peak_owned_numeric_bytes(self) -> int:
        return self._peak_bytes

    @property
    def peak_visible_array_bytes(self) -> int:
        return self._peak_array_bytes

    @property
    def peak_reserved_workspace_bytes(self) -> int:
        return self._peak_workspace_bytes

    @property
    def peak_float64_equivalent_entries(self) -> int:
        return (self._peak_bytes + 7) // 8

    @property
    def live_labels(self) -> Tuple[str, ...]:
        return tuple(sorted((*self._labels, *self._workspace_labels)))


class _CoefficientUpdateCounter:
    def __init__(self) -> None:
        self.observation_recurrence = 0
        self.source_recurrence = 0
        self.contractions = 0

    @property
    def total(self) -> int:
        return (
            self.observation_recurrence
            + self.source_recurrence
            + self.contractions
        )


def _coefficient_table(
    counts: np.ndarray,
    constant_factor: np.ndarray,
    rank_factor: np.ndarray,
    prepared: PreparedAssociationRankStressRun,
    scratch_old: np.ndarray,
    scratch_new: np.ndarray,
    counter: _CoefficientUpdateCounter,
    observation_lane: bool,
) -> np.ndarray:
    scratch_old.fill(0.0)
    scratch_new.fill(0.0)
    scratch_old[0] = 1.0
    old = scratch_old
    new = scratch_new
    completed = 0
    coefficient_totals = prepared.coefficient_totals
    for type_index, multiplicity_value in enumerate(counts):
        multiplicity = int(multiplicity_value)
        for _ in range(multiplicity):
            new.fill(0.0)
            for coefficient_index, degree_value in enumerate(coefficient_totals):
                if int(degree_value) > completed:
                    continue
                new[coefficient_index] += (
                    old[coefficient_index] * constant_factor[type_index]
                )
                if observation_lane:
                    counter.observation_recurrence += 1
                else:
                    counter.source_recurrence += 1
                for channel in range(prepared.fixture.rank):
                    destination = int(
                        prepared.increment_indices[coefficient_index, channel]
                    )
                    if destination < 0:
                        raise ArithmeticError("coefficient recurrence left cap-two table")
                    new[destination] += (
                        old[coefficient_index] * rank_factor[type_index, channel]
                    )
                    if observation_lane:
                        counter.observation_recurrence += 1
                    else:
                        counter.source_recurrence += 1
            old, new = new, old
            completed += 1
    return old


def _register_static_numeric_buffers(
    prepared: PreparedAssociationRankStressRun,
    registry: OwnedNumericAllocationRegistry,
) -> Tuple[str, ...]:
    fixture = prepared.fixture
    values = (
        ("static/times", fixture.times),
        ("static/latent_states", fixture.latent_states),
        ("static/retained_observations", fixture.retained_observations),
        ("static/immigration", fixture.immigration_rates),
        ("static/death", fixture.death_rates),
        ("static/replacement", fixture.replacement_rates),
        ("static/subgenerator", fixture.one_particle_subgenerator),
        ("static/detection", fixture.detection_probability),
        ("static/vandermonde-mass", fixture.vandermonde_mass),
        ("static/confusion", fixture.confusion_matrix),
        ("static/terminal_emission", fixture.terminal_emission_mass),
        ("static/observation_clutter", fixture.observation_clutter_rates),
        ("static/reference", fixture.reference_mass),
        ("static/U", fixture.anchor_factor),
        ("static/V", fixture.source_factor),
        ("static/multiindices", prepared.multiindices),
        ("static/coefficient_totals", prepared.coefficient_totals),
        ("static/coefficient_factorials", prepared.coefficient_factorials),
        ("static/increment_indices", prepared.increment_indices),
        ("static/latent_cardinalities", prepared.latent_cardinalities),
        ("static/retained_cardinalities", prepared.retained_cardinalities),
        ("static/retained_factorials", prepared.retained_factorials),
        (
            "static/contamination-reference",
            prepared.contamination_reference_mass,
        ),
    )
    manifest_values = tuple(
        (
            "static/serialized-manifest/%s" % record.name,
            np.frombuffer(record.payload, dtype=np.uint8),
        )
        for record in prepared.manifest.records
    )
    all_values = values + manifest_values
    for label, value in all_values:
        registry.register(label, value)
    return tuple(label for label, _ in all_values)


def _deep_python_object_overhead_bytes(value: object) -> int:
    """Conservatively count reachable Python headers, excluding numeric data."""

    seen = set()

    def visit(item: object) -> int:
        identity = id(item)
        if identity in seen:
            return 0
        seen.add(identity)
        size = sys.getsizeof(item)
        if isinstance(item, np.ndarray):
            if item.flags.owndata:
                size = max(0, size - int(item.nbytes))
            return size
        if isinstance(item, (bytes, bytearray, memoryview)):
            return max(0, size - len(item))
        if isinstance(item, Mapping):
            return size + sum(
                visit(key) + visit(entry) for key, entry in item.items()
            )
        if isinstance(item, (tuple, list, set, frozenset)):
            return size + sum(visit(entry) for entry in item)
        attributes = getattr(item, "__dict__", None)
        if isinstance(attributes, dict):
            return size + visit(attributes)
        return size

    return int(visit(value))


def _scalar_matmul_into(
    left: np.ndarray, right: np.ndarray, destination: np.ndarray
) -> None:
    """Small float64 matrix product with no hidden numeric workspace.

    The Section-9 propagation matrices have maximum order eight.  Explicit
    scalar loops are intentional: every numeric output is preallocated and
    registered by the caller, while the short Python-float term lists enter
    the separately reported Python-allocation upper bound.
    """

    left_array = np.asarray(left, dtype=np.float64)
    right_array = np.asarray(right, dtype=np.float64)
    output = np.asarray(destination, dtype=np.float64)
    left_was_vector = left_array.ndim == 1
    right_was_vector = right_array.ndim == 1
    left_matrix = left_array.reshape(1, -1) if left_was_vector else left_array
    right_matrix = (
        right_array.reshape(-1, 1) if right_was_vector else right_array
    )
    if (
        left_matrix.ndim != 2
        or right_matrix.ndim != 2
        or left_matrix.shape[1] != right_matrix.shape[0]
    ):
        raise ValueError("matmul operands have incompatible shapes")
    expected_shape = (left_matrix.shape[0], right_matrix.shape[1])
    if left_was_vector and right_was_vector:
        expected_output_shape: Tuple[int, ...] = ()
    elif left_was_vector:
        expected_output_shape = (expected_shape[1],)
    elif right_was_vector:
        expected_output_shape = (expected_shape[0],)
    else:
        expected_output_shape = expected_shape
    if output.shape != expected_output_shape:
        raise ValueError("matmul destination has the wrong shape")
    for row in range(expected_shape[0]):
        for column in range(expected_shape[1]):
            value = math.fsum(
                float(left_matrix[row, inner])
                * float(right_matrix[inner, column])
                for inner in range(left_matrix.shape[1])
            )
            if expected_output_shape == ():
                output[...] = value
            elif left_was_vector:
                output[column] = value
            elif right_was_vector:
                output[row] = value
            else:
                output[row, column] = value


def _analytic_time_into(
    prepared: PreparedAssociationRankStressRun,
    time_index: int,
    destination: np.ndarray,
    counter: _CoefficientUpdateCounter,
    registry: OwnedNumericAllocationRegistry,
) -> None:
    fixture = prepared.fixture
    prefix = "time-%02d/" % time_index
    duration = 1.0 - float(fixture.times[time_index])
    block_input = np.zeros((2 * _TYPE_COUNT, 2 * _TYPE_COUNT), dtype=np.float64)
    for row in range(_TYPE_COUNT):
        for column in range(_TYPE_COUNT):
            block_input[row, column] = (
                duration * float(fixture.one_particle_subgenerator[row, column])
            )
    for type_index in range(_TYPE_COUNT):
        block_input[type_index, _TYPE_COUNT + type_index] = duration
    registry.register(prefix + "block-exponential-input", block_input)
    workspace_label = prefix + "scipy-expm-workspace-upper-bound"
    registry.reserve_workspace(
        workspace_label, RANK_STRESS_SCIPY_EXPM_WORKSPACE_BOUND_BYTES
    )
    block_output = expm(block_input)
    registry.register(prefix + "block-exponential-output", block_output)
    registry.release_workspace(workspace_label)
    survival = np.array(block_output[:_TYPE_COUNT, :_TYPE_COUNT], copy=True)
    integral = np.array(block_output[:_TYPE_COUNT, _TYPE_COUNT:], copy=True)
    registry.register(prefix + "survival", survival)
    registry.register(prefix + "integral", integral)
    registry.release(prefix + "block-exponential-output")
    registry.release(prefix + "block-exponential-input")

    immigrant = np.empty(_TYPE_COUNT, dtype=np.float64)
    registry.register(prefix + "immigrant", immigrant)
    _scalar_matmul_into(fixture.immigration_rates, integral, immigrant)
    propagated_v = np.empty(
        (_TYPE_COUNT, fixture.rank), dtype=np.float64
    )
    registry.register(prefix + "propagated-V", propagated_v)
    _scalar_matmul_into(survival, fixture.source_factor, propagated_v)
    registry.release(prefix + "survival")
    registry.release(prefix + "integral")
    effective_emission = np.empty(
        (_TYPE_COUNT, _TYPE_COUNT), dtype=np.float64
    )
    registry.register(prefix + "effective-emission", effective_emission)
    _scalar_matmul_into(
        propagated_v, fixture.anchor_factor.T, effective_emission
    )
    immigrant_anchor = np.empty(_TYPE_COUNT, dtype=np.float64)
    registry.register(prefix + "immigrant-anchor", immigrant_anchor)
    _scalar_matmul_into(
        immigrant, fixture.terminal_emission_mass, immigrant_anchor
    )
    registry.release(prefix + "immigrant")
    effective_clutter = np.empty(_TYPE_COUNT, dtype=np.float64)
    registry.register(prefix + "effective-clutter", effective_clutter)
    for type_index in range(_TYPE_COUNT):
        effective_clutter[type_index] = (
            float(fixture.observation_clutter_rates[type_index])
            + float(immigrant_anchor[type_index])
        )
    registry.release(prefix + "immigrant-anchor")
    emission_row_sum = np.empty(_TYPE_COUNT, dtype=np.float64)
    registry.register(prefix + "emission-row-sum", emission_row_sum)
    for type_index in range(_TYPE_COUNT):
        emission_row_sum[type_index] = math.fsum(
            float(value) for value in effective_emission[type_index]
        )
    miss = np.empty(_TYPE_COUNT, dtype=np.float64)
    registry.register(prefix + "miss", miss)
    for type_index in range(_TYPE_COUNT):
        miss[type_index] = 1.0 - float(emission_row_sum[type_index])
    registry.release(prefix + "emission-row-sum")
    registry.release(prefix + "effective-emission")
    for type_index in range(_TYPE_COUNT):
        if (
            float(miss[type_index]) < -_NUMERICAL_TOLERANCE
            or float(effective_clutter[type_index]) < -_NUMERICAL_TOLERANCE
        ):
            raise ArithmeticError("propagated guide factors contain negative mass")
        miss[type_index] = max(0.0, float(miss[type_index]))
        effective_clutter[type_index] = max(
            0.0, float(effective_clutter[type_index])
        )

    coefficient_count = prepared.multiindices.shape[0]
    observation_cache = np.empty((45, coefficient_count), dtype=np.float64)
    source_cache = np.empty((45, coefficient_count), dtype=np.float64)
    scratch_old = np.empty(coefficient_count, dtype=np.float64)
    scratch_new = np.empty(coefficient_count, dtype=np.float64)
    registry.register(prefix + "A-cache", observation_cache)
    registry.register(prefix + "B-cache", source_cache)
    registry.register(prefix + "recurrence-scratch-old", scratch_old)
    registry.register(prefix + "recurrence-scratch-new", scratch_new)

    for index, counts in enumerate(fixture.retained_observations):
        table = _coefficient_table(
            counts,
            effective_clutter,
            fixture.anchor_factor,
            prepared,
            scratch_old,
            scratch_new,
            counter,
            True,
        )
        observation_cache[index, :] = table
    for index, counts in enumerate(fixture.latent_states):
        table = _coefficient_table(
            counts,
            miss,
            propagated_v,
            prepared,
            scratch_old,
            scratch_new,
            counter,
            False,
        )
        source_cache[index, :] = table
    registry.release(prefix + "recurrence-scratch-new")
    registry.release(prefix + "recurrence-scratch-old")

    clean = np.empty((45, _OBSERVATION_COUNT), dtype=np.float64)
    mixed = np.empty_like(clean)
    density = np.empty_like(clean)
    registry.register(prefix + "clean-grid", clean)
    registry.register(prefix + "mixed-grid", mixed)
    registry.register(prefix + "density-grid", density)
    coefficient_totals = prepared.coefficient_totals
    poisson_exponential = math.exp(
        -math.fsum(float(value) for value in effective_clutter)
    )
    latent_totals = prepared.latent_cardinalities
    retained_totals = prepared.retained_cardinalities
    for latent_index, latent_total_value in enumerate(latent_totals):
        for observation_index, observation_total_value in enumerate(
            retained_totals
        ):
            maximum_degree = min(
                int(latent_total_value), int(observation_total_value)
            )
            terms = []
            for coefficient_index, degree_value in enumerate(coefficient_totals):
                if int(degree_value) > maximum_degree:
                    continue
                terms.append(
                    observation_cache[observation_index, coefficient_index]
                    * source_cache[latent_index, coefficient_index]
                    * prepared.coefficient_factorials[coefficient_index]
                )
                counter.contractions += 1
            clean[latent_index, observation_index] = (
                poisson_exponential
                * math.fsum(float(term) for term in terms)
                / prepared.retained_factorials[observation_index]
            )
        retained_total = math.fsum(
            float(value) for value in clean[latent_index, :-1]
        )
        if retained_total < -_NUMERICAL_TOLERANCE or retained_total > (
            1.0 + _NUMERICAL_TOLERANCE
        ):
            raise ArithmeticError("retained analytic probability is outside [0, one]")
        clean[latent_index, -1] = max(0.0, 1.0 - retained_total)

    for latent_index in range(45):
        normalization = 0.0
        for observation_index in range(_OBSERVATION_COUNT):
            mixed[latent_index, observation_index] = (
                (1.0 - _CONTAMINATION_PROBABILITY)
                * float(clean[latent_index, observation_index])
                + float(
                    prepared.contamination_reference_mass[observation_index]
                )
            )
            density[latent_index, observation_index] = (
                float(mixed[latent_index, observation_index])
                / float(fixture.reference_mass[observation_index])
            )
            value = float(density[latent_index, observation_index])
            if (
                not math.isfinite(value)
                or value < _CONTAMINATION_PROBABILITY - 5.0e-12
            ):
                raise ArithmeticError("analytic density is invalid")
            normalization += value * float(fixture.reference_mass[observation_index])
        if not math.isclose(normalization, 1.0, rel_tol=0.0, abs_tol=5.0e-12):
            raise ArithmeticError("analytic density rows do not normalize")
    destination[:, :] = density

    registry.release(prefix + "density-grid")
    registry.release(prefix + "mixed-grid")
    registry.release(prefix + "clean-grid")
    registry.release(prefix + "B-cache")
    registry.release(prefix + "A-cache")
    registry.release(prefix + "miss")
    registry.release(prefix + "effective-clutter")
    registry.release(prefix + "propagated-V")


@dataclass(frozen=True, eq=False)
class RankStressAnalyticTimeResult:
    time_index: int
    density: np.ndarray
    coefficient_updates: int
    expected_coefficient_updates: int
    peak_owned_numeric_bytes: int
    occurrence_matching_enumeration_used: bool = False
    peak_visible_numeric_bytes: Optional[int] = None
    peak_reserved_workspace_bytes: Optional[int] = None

    @property
    def relative_operation_agreement(self) -> bool:
        return self.coefficient_updates == self.expected_coefficient_updates


@dataclass(frozen=True, eq=False)
class RankStressAnalyticGridResult:
    density_grid: np.ndarray
    coefficient_updates: int
    expected_coefficient_updates: int
    peak_owned_numeric_bytes: int
    python_object_overhead_bytes: Optional[int]
    peak_rss_bytes: Optional[int]
    allocation_accounting_complete: bool
    full_oracle_agreement_verified: bool
    benchmark_metadata_complete: bool
    occurrence_matching_enumeration_used: bool = False
    peak_visible_numeric_bytes: Optional[int] = None
    peak_reserved_workspace_bytes: Optional[int] = None

    @property
    def hard_resource_gate_passed(self) -> bool:
        return (
            self.allocation_accounting_complete
            and self.coefficient_updates == self.expected_coefficient_updates
            and self.coefficient_updates
            <= RANK_STRESS_MAXIMUM_COEFFICIENT_UPDATES
            and self.peak_owned_numeric_bytes
            <= RANK_STRESS_MAXIMUM_OWNED_NUMERIC_BYTES
            and self.peak_visible_numeric_bytes is not None
            and self.peak_visible_numeric_bytes
            >= 2 * RANK_STRESS_FULL_OUTPUT_BYTES
            and self.peak_reserved_workspace_bytes is not None
            and self.peak_reserved_workspace_bytes
            >= max(
                RANK_STRESS_SCIPY_EXPM_WORKSPACE_BOUND_BYTES,
                RANK_STRESS_FULL_OUTPUT_BYTES,
            )
            and self.peak_owned_numeric_bytes
            >= 3 * RANK_STRESS_FULL_OUTPUT_BYTES
            and not self.occurrence_matching_enumeration_used
        )

    @property
    def section_nine_gate_passed(self) -> bool:
        return (
            self.hard_resource_gate_passed
            and self.full_oracle_agreement_verified
            and self.benchmark_metadata_complete
            and self.python_object_overhead_bytes is not None
            and self.peak_rss_bytes is not None
        )


def evaluate_association_rank_stress_analytic_time(
    prepared: PreparedAssociationRankStressRun,
    time_index: object,
) -> RankStressAnalyticTimeResult:
    """Evaluate one cheap diagnostic slice with full logical instrumentation."""

    if not isinstance(prepared, PreparedAssociationRankStressRun):
        raise TypeError("prepared has the wrong type")
    selected_time = _validated_time_index(time_index)
    registry = OwnedNumericAllocationRegistry()
    static_labels = _register_static_numeric_buffers(prepared, registry)
    output = np.empty((45, _OBSERVATION_COUNT), dtype=np.float64)
    registry.register("diagnostic-output", output)
    counter = _CoefficientUpdateCounter()
    _analytic_time_into(prepared, selected_time, output, counter, registry)
    expected = prepared.expected_updates.total_per_time
    if counter.total != expected:
        raise ArithmeticError("instrumented count disagrees with direct loop count")
    registry.reserve_workspace(
        "immutable-diagnostic-copy-temporary", int(output.nbytes)
    )
    immutable_output = _immutable_float_array(output)
    registry.register("immutable-diagnostic-output", immutable_output)
    registry.release_workspace("immutable-diagnostic-copy-temporary")
    peak = registry.peak_owned_numeric_bytes
    registry.release("diagnostic-output")
    registry.release("immutable-diagnostic-output")
    for label in reversed(static_labels):
        registry.release(label)
    if registry.current_owned_numeric_bytes != 0 or registry.live_labels:
        raise ArithmeticError("allocation registry did not return to zero")
    return RankStressAnalyticTimeResult(
        time_index=selected_time,
        density=immutable_output,
        coefficient_updates=counter.total,
        expected_coefficient_updates=expected,
        peak_owned_numeric_bytes=peak,
        occurrence_matching_enumeration_used=(
            RANK_STRESS_OCCURRENCE_MATCHING_ENUMERATION_USED
        ),
        peak_visible_numeric_bytes=registry.peak_visible_array_bytes,
        peak_reserved_workspace_bytes=registry.peak_reserved_workspace_bytes,
    )


def evaluate_association_rank_stress_analytic_grid(
    prepared: PreparedAssociationRankStressRun,
) -> RankStressAnalyticGridResult:
    """Evaluate the complete analytic grid when the frozen gate is authorized.

    This function is intentionally never called by fixture construction or by
    the focused unit tests.  Its output alone is not a decision: the separately
    executed exhaustive grid, relative-error comparison, timing repetitions,
    peak RSS, and independent audit remain required by Section 9.
    """

    if not isinstance(prepared, PreparedAssociationRankStressRun):
        raise TypeError("prepared has the wrong type")
    registry = OwnedNumericAllocationRegistry()
    static_labels = _register_static_numeric_buffers(prepared, registry)
    output = np.empty(
        (RANK_STRESS_TIME_POINT_COUNT, 45, _OBSERVATION_COUNT),
        dtype=np.float64,
    )
    registry.register("full-density-output", output)
    counter = _CoefficientUpdateCounter()
    for time_index in range(RANK_STRESS_TIME_POINT_COUNT):
        _analytic_time_into(
            prepared,
            time_index,
            output[time_index],
            counter,
            registry,
        )
    expected = prepared.expected_updates.full_grid_total
    if counter.total != expected:
        raise ArithmeticError("instrumented count disagrees with direct loop count")
    registry.reserve_workspace(
        "immutable-full-output-copy-temporary", int(output.nbytes)
    )
    immutable_output = _immutable_float_array(output)
    registry.register("immutable-full-density-output", immutable_output)
    registry.release_workspace("immutable-full-output-copy-temporary")
    peak = registry.peak_owned_numeric_bytes
    registry.release("full-density-output")
    registry.release("immutable-full-density-output")
    for label in reversed(static_labels):
        registry.release(label)
    if registry.current_owned_numeric_bytes != 0 or registry.live_labels:
        raise ArithmeticError("allocation registry did not return to zero")
    return RankStressAnalyticGridResult(
        density_grid=immutable_output,
        coefficient_updates=counter.total,
        expected_coefficient_updates=expected,
        peak_owned_numeric_bytes=peak,
        python_object_overhead_bytes=None,
        peak_rss_bytes=None,
        # The registry covers every explicit backing buffer and holds the
        # conservative SciPy expm workspace reservation live across each
        # call.  All remaining timed matrix contractions use preallocated
        # outputs and scalar loops, so there is no unregistered BLAS/ufunc
        # workspace in the analytic lane.
        allocation_accounting_complete=True,
        full_oracle_agreement_verified=False,
        benchmark_metadata_complete=False,
        occurrence_matching_enumeration_used=(
            RANK_STRESS_OCCURRENCE_MATCHING_ENUMERATION_USED
        ),
        peak_visible_numeric_bytes=registry.peak_visible_array_bytes,
        peak_reserved_workspace_bytes=registry.peak_reserved_workspace_bytes,
    )


def _unregistered_propagation(
    fixture: FrozenAssociationRankStressFixture, time_index: int
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    duration = 1.0 - float(fixture.times[time_index])
    block = np.zeros((2 * _TYPE_COUNT, 2 * _TYPE_COUNT), dtype=float)
    block[:_TYPE_COUNT, :_TYPE_COUNT] = fixture.one_particle_subgenerator
    block[:_TYPE_COUNT, _TYPE_COUNT:] = np.eye(_TYPE_COUNT)
    propagated = expm(duration * block)
    survival = propagated[:_TYPE_COUNT, :_TYPE_COUNT]
    integral = propagated[:_TYPE_COUNT, _TYPE_COUNT:]
    immigrant = fixture.immigration_rates @ integral
    emission = survival @ fixture.terminal_emission_mass
    clutter = (
        fixture.observation_clutter_rates
        + immigrant @ fixture.terminal_emission_mass
    )
    miss = 1.0 - emission.sum(axis=1)
    return emission, miss, clutter


def evaluate_association_rank_stress_exhaustive_time(
    fixture: FrozenAssociationRankStressFixture,
    time_index: object,
) -> np.ndarray:
    """Independent ordinary-PGF coefficient oracle for one time slice.

    The oracle expands source emission factors in anchor-count coordinates and
    convolves them with exact retained Poisson coefficients.  It never calls
    the fixed-rank recurrence or contraction and is excluded from its counters.
    """

    if not isinstance(fixture, FrozenAssociationRankStressFixture):
        raise TypeError("fixture must be a FrozenAssociationRankStressFixture")
    selected_time = _validated_time_index(time_index)
    emission, miss, clutter = _unregistered_propagation(fixture, selected_time)
    states = fixture.retained_observation_space.states
    state_index = {state: index for index, state in enumerate(states)}
    totals = tuple(sum(state) for state in states)
    poisson = np.empty(45, dtype=float)
    clutter_total = math.fsum(float(value) for value in clutter)
    for index, counts in enumerate(states):
        probability = math.exp(-clutter_total)
        for count, rate in zip(counts, clutter):
            probability *= float(rate) ** count / math.factorial(count)
        poisson[index] = probability

    clean = np.empty((45, _OBSERVATION_COUNT), dtype=float)
    for latent_index, latent_counts in enumerate(fixture.latent_space.states):
        source_coefficients = np.zeros(45, dtype=float)
        source_coefficients[0] = 1.0
        completed = 0
        for source, multiplicity in enumerate(latent_counts):
            for _ in range(multiplicity):
                updated = np.zeros(45, dtype=float)
                for coefficient_index, partial in enumerate(states):
                    if totals[coefficient_index] > completed:
                        continue
                    prefix = source_coefficients[coefficient_index]
                    updated[coefficient_index] += prefix * miss[source]
                    if totals[coefficient_index] >= _CARDINALITY_CAP:
                        continue
                    for anchor in range(_TYPE_COUNT):
                        destination = list(partial)
                        destination[anchor] += 1
                        updated[state_index[tuple(destination)]] += (
                            prefix * emission[source, anchor]
                        )
                source_coefficients = updated
                completed += 1

        for observation_index, observed in enumerate(states):
            terms = []
            for source_index, source_counts in enumerate(states):
                if any(
                    source_count > observed_count
                    for source_count, observed_count in zip(
                        source_counts, observed
                    )
                ):
                    continue
                clutter_counts = tuple(
                    observed_count - source_count
                    for source_count, observed_count in zip(
                        source_counts, observed
                    )
                )
                terms.append(
                    source_coefficients[source_index]
                    * poisson[state_index[clutter_counts]]
                )
            clean[latent_index, observation_index] = math.fsum(
                float(term) for term in terms
            )
        clean[latent_index, -1] = max(
            0.0,
            1.0
            - math.fsum(float(value) for value in clean[latent_index, :-1]),
        )
    mixed = (
        (1.0 - _CONTAMINATION_PROBABILITY) * clean
        + _CONTAMINATION_PROBABILITY * fixture.reference_mass[None, :]
    )
    density = mixed / fixture.reference_mass[None, :]
    return _immutable_float_array(density)


def evaluate_association_rank_stress_exhaustive_grid(
    fixture: FrozenAssociationRankStressFixture,
) -> np.ndarray:
    """Evaluate the complete independent oracle grid when execution is authorized.

    This callable is intentionally not invoked by preparation or focused unit
    tests.  The exhaustive lane is separate from, and excluded from, analytic
    operation/allocation counters.
    """

    if not isinstance(fixture, FrozenAssociationRankStressFixture):
        raise TypeError("fixture must be a FrozenAssociationRankStressFixture")
    output = np.empty(
        (RANK_STRESS_TIME_POINT_COUNT, 45, _OBSERVATION_COUNT), dtype=np.float64
    )
    for time_index in range(RANK_STRESS_TIME_POINT_COUNT):
        output[time_index, :, :] = evaluate_association_rank_stress_exhaustive_time(
            fixture, time_index
        )
    output.setflags(write=False)
    return output


def maximum_elementwise_relative_error(
    candidate: object, reference: object
) -> float:
    """Return max elementwise relative error for strictly positive densities."""

    candidate_array = np.asarray(candidate, dtype=float)
    reference_array = np.asarray(reference, dtype=float)
    if candidate_array.shape != reference_array.shape or candidate_array.size == 0:
        raise ValueError("candidate and reference must have the same nonempty shape")
    if not np.all(np.isfinite(candidate_array)) or not np.all(
        np.isfinite(reference_array)
    ):
        raise ValueError("candidate and reference must be finite")
    if np.any(reference_array <= 0.0):
        raise ValueError("reference must be strictly positive")
    return float(np.max(np.abs(candidate_array - reference_array) / reference_array))


def _peak_rss_bytes() -> Tuple[int, str]:
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if not math.isfinite(float(raw)) or float(raw) < 0.0:
        raise RuntimeError("process peak RSS is unavailable")
    system = platform.system()
    if system == "Darwin":
        return int(raw), "getrusage-ru_maxrss-darwin-bytes"
    if system == "Linux":
        return int(raw) * 1024, "getrusage-ru_maxrss-linux-kib-to-bytes"
    raise RuntimeError("peak RSS unit normalization is unsupported on this OS")


def _cpu_model() -> str:
    if platform.system() == "Darwin":
        for name in ("machdep.cpu.brand_string", "hw.model"):
            try:
                completed = subprocess.run(
                    ("/usr/sbin/sysctl", "-n", name),
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5.0,
                )
            except (OSError, subprocess.SubprocessError):
                continue
            value = completed.stdout.strip()
            if completed.returncode == 0 and value:
                return value
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        try:
            for line in cpuinfo.read_text(encoding="utf-8").splitlines():
                if line.lower().startswith(("model name", "hardware")):
                    value = line.split(":", 1)[-1].strip()
                    if value:
                        return value
        except OSError:
            pass
    processor = platform.processor().strip()
    if processor:
        return processor
    return platform.machine() or "unavailable"


def _runtime_payload(value: "RankStressRuntimeMetadata") -> dict:
    payload = asdict(value)
    payload.pop("runtime_sha256", None)
    payload["schema"] = RANK_STRESS_RUNTIME_SCHEMA
    return payload


@dataclass(frozen=True)
class RankStressRuntimeMetadata:
    """Immutable environment report for the launcher-created worker."""

    python_version: str
    python_implementation: str
    numpy_version: str
    scipy_version: str
    threadpoolctl_version: str
    operating_system: str
    operating_system_release: str
    platform_string: str
    machine: str
    cpu_model: str
    numpy_configuration_text: str
    native_pools_json: str
    thread_environment: Tuple[Tuple[str, str], ...]
    configured_blas_thread_count: int
    fresh_process_marker_observed: bool
    benchmark_clock_id: str
    peak_rss_method_id: str
    runtime_sha256: str = ""

    def __post_init__(self) -> None:
        text_fields = (
            "python_version",
            "python_implementation",
            "numpy_version",
            "scipy_version",
            "threadpoolctl_version",
            "operating_system",
            "operating_system_release",
            "platform_string",
            "machine",
            "cpu_model",
            "numpy_configuration_text",
            "native_pools_json",
            "benchmark_clock_id",
            "peak_rss_method_id",
        )
        for name in text_fields:
            if type(getattr(self, name)) is not str or not getattr(self, name):
                raise TypeError("%s must be a nonempty string" % name)
        try:
            pools = json.loads(self.native_pools_json)
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("native_pools_json is invalid") from error
        if not isinstance(pools, list):
            raise ValueError("native_pools_json must encode a list")
        for pool in pools:
            if not isinstance(pool, dict):
                raise ValueError("every native pool record must be a mapping")
            if set(pool) != {
                "user_api",
                "internal_api",
                "prefix",
                "version",
                "num_threads",
            }:
                raise ValueError("a native pool record has the wrong fields")
        expected_names = tuple(RANK_STRESS_THREAD_ENVIRONMENT)
        if (
            type(self.thread_environment) is not tuple
            or tuple(name for name, _ in self.thread_environment) != expected_names
            or any(type(value) is not str for _, value in self.thread_environment)
        ):
            raise ValueError("thread_environment is incomplete or out of order")
        if self.configured_blas_thread_count != 1:
            raise ValueError("configured_blas_thread_count must equal one")
        if type(self.fresh_process_marker_observed) is not bool:
            raise TypeError("fresh_process_marker_observed must be boolean")
        expected = _sha256_json(_runtime_payload(self))
        if self.runtime_sha256:
            _lower_sha256(self.runtime_sha256, name="runtime_sha256")
            if self.runtime_sha256 != expected:
                raise ValueError("runtime metadata digest is inconsistent")
        else:
            object.__setattr__(self, "runtime_sha256", expected)

    @property
    def benchmark_metadata_complete(self) -> bool:
        pools = json.loads(self.native_pools_json)
        discovered_counts = tuple(pool.get("num_threads") for pool in pools)
        return (
            self.python_version == RANK_STRESS_EXPECTED_PYTHON_VERSION
            and self.python_implementation == "CPython"
            and self.numpy_version == RANK_STRESS_EXPECTED_NUMPY_VERSION
            and self.scipy_version == RANK_STRESS_EXPECTED_SCIPY_VERSION
            and self.threadpoolctl_version
            == RANK_STRESS_EXPECTED_THREADPOOLCTL_VERSION
            and all(value == "1" for _, value in self.thread_environment)
            and self.configured_blas_thread_count == 1
            and bool(discovered_counts)
            and all(
                isinstance(value, int)
                and not isinstance(value, bool)
                and value == 1
                for value in discovered_counts
            )
            and self.numpy_configuration_text.strip() != "unavailable"
            and self.cpu_model.strip() != "unavailable"
        )


def capture_rank_stress_runtime_metadata() -> RankStressRuntimeMetadata:
    """Capture runtime/BLAS metadata without executing any density grid."""

    stream = io.StringIO()
    with redirect_stdout(stream):
        np.show_config()
    numpy_configuration = stream.getvalue().strip() or "unavailable"
    try:
        import threadpoolctl
    except ImportError:
        threadpoolctl_version = "unavailable"
        pool_records = []
    else:
        threadpoolctl_version = str(threadpoolctl.__version__)
        pool_records = []
        for pool in threadpoolctl.threadpool_info():
            pool_records.append(
                {
                    "user_api": pool.get("user_api"),
                    "internal_api": pool.get("internal_api"),
                    "prefix": pool.get("prefix"),
                    "version": pool.get("version"),
                    "num_threads": pool.get("num_threads"),
                }
            )
        pool_records.sort(
            key=lambda value: (
                str(value["user_api"]),
                str(value["internal_api"]),
                str(value["prefix"]),
            )
        )
    _, rss_method = _peak_rss_bytes()
    thread_environment = tuple(
        (name, os.environ.get(name, "<unset>"))
        for name in RANK_STRESS_THREAD_ENVIRONMENT
    )
    return RankStressRuntimeMetadata(
        python_version=platform.python_version(),
        python_implementation=platform.python_implementation(),
        numpy_version=np.__version__,
        scipy_version=scipy.__version__,
        threadpoolctl_version=threadpoolctl_version,
        operating_system=platform.system() or "unavailable",
        operating_system_release=platform.release() or "unavailable",
        platform_string=platform.platform() or "unavailable",
        machine=platform.machine() or "unavailable",
        cpu_model=_cpu_model(),
        numpy_configuration_text=numpy_configuration,
        native_pools_json=_canonical_json(pool_records).decode("ascii"),
        thread_environment=thread_environment,
        configured_blas_thread_count=1,
        fresh_process_marker_observed=(
            os.environ.get(RANK_STRESS_FRESH_PROCESS_MARKER) == "1"
        ),
        benchmark_clock_id="time.perf_counter_ns",
        peak_rss_method_id=rss_method,
    )


def _rank_execution_payload(value: "RankStressRankExecutionResult") -> dict:
    payload = asdict(value)
    payload.pop("result_sha256", None)
    payload["schema"] = RANK_STRESS_RESULT_SCHEMA
    return payload


@dataclass(frozen=True)
class RankStressRankExecutionResult:
    """Self-digested, fail-closed record for one frozen rank."""

    rank: int
    fixture_manifest_sha256: str
    oracle_time_indices: Tuple[int, ...]
    density_shape: Tuple[int, ...]
    analytic_density_sha256: str
    exhaustive_density_sha256: str
    maximum_relative_error: float
    relative_error_by_time: Tuple[float, ...]
    coefficient_updates: int
    expected_coefficient_updates: int
    peak_owned_numeric_bytes: int
    peak_visible_numeric_bytes: int
    peak_reserved_workspace_bytes: int
    scipy_expm_workspace_bound_bytes: int
    numpy_kernel_workspace_bound_bytes: int
    allocation_accounting_complete: bool
    occurrence_matching_enumeration_used: bool
    python_allocation_upper_bound_bytes: int
    warmup_wall_seconds: float
    timed_wall_seconds: Tuple[float, ...]
    median_five_wall_seconds: float
    result_sha256: str = ""

    def __post_init__(self) -> None:
        _validated_rank(self.rank)
        for name in (
            "fixture_manifest_sha256",
            "analytic_density_sha256",
            "exhaustive_density_sha256",
        ):
            _lower_sha256(getattr(self, name), name=name)
        if type(self.oracle_time_indices) is not tuple or any(
            isinstance(value, bool) or type(value) is not int
            for value in self.oracle_time_indices
        ):
            raise TypeError("oracle_time_indices must be an integer tuple")
        if type(self.density_shape) is not tuple or any(
            isinstance(value, bool) or type(value) is not int or value < 0
            for value in self.density_shape
        ):
            raise TypeError("density_shape must be a nonnegative integer tuple")
        if not math.isfinite(self.maximum_relative_error) or (
            self.maximum_relative_error < 0.0
        ):
            raise ValueError("maximum_relative_error must be finite and nonnegative")
        if type(self.relative_error_by_time) is not tuple or any(
            not math.isfinite(value) or value < 0.0
            for value in self.relative_error_by_time
        ):
            raise ValueError("relative_error_by_time must be finite and nonnegative")
        expected_maximum = (
            max(self.relative_error_by_time) if self.relative_error_by_time else 0.0
        )
        if self.maximum_relative_error != expected_maximum:
            raise ValueError("maximum_relative_error is inconsistent")
        integer_fields = (
            "coefficient_updates",
            "expected_coefficient_updates",
            "peak_owned_numeric_bytes",
            "peak_visible_numeric_bytes",
            "peak_reserved_workspace_bytes",
            "scipy_expm_workspace_bound_bytes",
            "numpy_kernel_workspace_bound_bytes",
            "python_allocation_upper_bound_bytes",
        )
        for name in integer_fields:
            value = getattr(self, name)
            if isinstance(value, bool) or type(value) is not int or value < 0:
                raise TypeError("%s must be a nonnegative integer" % name)
        for name in (
            "allocation_accounting_complete",
            "occurrence_matching_enumeration_used",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError("%s must be boolean" % name)
        if self.peak_owned_numeric_bytes < max(
            self.peak_visible_numeric_bytes,
            self.peak_reserved_workspace_bytes,
        ):
            raise ValueError("owned peak cannot be below a component peak")
        if (
            not math.isfinite(self.warmup_wall_seconds)
            or self.warmup_wall_seconds < 0.0
        ):
            raise ValueError("warmup_wall_seconds must be finite and nonnegative")
        if type(self.timed_wall_seconds) is not tuple or any(
            not math.isfinite(value) or value < 0.0
            for value in self.timed_wall_seconds
        ):
            raise ValueError("timed_wall_seconds must be a nonnegative finite tuple")
        expected_median = (
            float(statistics.median(self.timed_wall_seconds))
            if self.timed_wall_seconds
            else 0.0
        )
        if self.timed_wall_seconds and self.median_five_wall_seconds != expected_median:
            raise ValueError("median_five_wall_seconds is inconsistent")
        if not self.timed_wall_seconds and self.median_five_wall_seconds != 0.0:
            raise ValueError("an empty timing tuple must have median zero")
        expected = _sha256_json(_rank_execution_payload(self))
        if self.result_sha256:
            _lower_sha256(self.result_sha256, name="result_sha256")
            if self.result_sha256 != expected:
                raise ValueError("rank execution result digest is inconsistent")
        else:
            object.__setattr__(self, "result_sha256", expected)

    @property
    def full_oracle_agreement_verified(self) -> bool:
        return (
            self.oracle_time_indices
            == tuple(range(RANK_STRESS_TIME_POINT_COUNT))
            and self.density_shape == RANK_STRESS_DENSITY_SHAPE
            and len(self.relative_error_by_time)
            == RANK_STRESS_TIME_POINT_COUNT
            and self.maximum_relative_error
            <= RANK_STRESS_RELATIVE_AGREEMENT_TOLERANCE
        )

    @property
    def hard_resource_gate_passed(self) -> bool:
        return (
            self.allocation_accounting_complete
            and self.fixture_manifest_sha256
            == RANK_STRESS_EXPECTED_MANIFEST_SHA256[self.rank]
            and self.coefficient_updates == self.expected_coefficient_updates
            and self.expected_coefficient_updates
            == RANK_STRESS_EXPECTED_FULL_GRID_UPDATES[self.rank]
            and self.coefficient_updates
            <= RANK_STRESS_MAXIMUM_COEFFICIENT_UPDATES
            and self.peak_owned_numeric_bytes
            <= RANK_STRESS_MAXIMUM_OWNED_NUMERIC_BYTES
            and self.peak_visible_numeric_bytes
            >= 2 * RANK_STRESS_FULL_OUTPUT_BYTES
            and self.peak_owned_numeric_bytes
            >= 3 * RANK_STRESS_FULL_OUTPUT_BYTES
            and self.scipy_expm_workspace_bound_bytes
            == RANK_STRESS_SCIPY_EXPM_WORKSPACE_BOUND_BYTES
            and self.numpy_kernel_workspace_bound_bytes
            == RANK_STRESS_NUMPY_KERNEL_WORKSPACE_BOUND_BYTES
            and self.peak_reserved_workspace_bytes
            >= max(
                self.scipy_expm_workspace_bound_bytes,
                RANK_STRESS_FULL_OUTPUT_BYTES,
            )
            and not self.occurrence_matching_enumeration_used
        )

    @property
    def benchmark_protocol_complete(self) -> bool:
        return (
            RANK_STRESS_BENCHMARK_WARMUP_COUNT == 1
            and len(self.timed_wall_seconds)
            == RANK_STRESS_BENCHMARK_REPETITION_COUNT
            and self.median_five_wall_seconds
            == float(statistics.median(self.timed_wall_seconds))
        )

    @property
    def rank_gate_passed(self) -> bool:
        return (
            self.full_oracle_agreement_verified
            and self.hard_resource_gate_passed
            and self.benchmark_protocol_complete
        )


def _suite_payload(value: "RankStressGateExecutionResult") -> dict:
    payload = asdict(value)
    payload.pop("result_sha256", None)
    payload["schema"] = RANK_STRESS_SUITE_SCHEMA
    return payload


def _rank_stress_source_bundle_sha256() -> str:
    rank_source = Path(__file__).resolve()
    theory_module = sys.modules.get(FiniteAtomicCountingSpace.__module__)
    theory_source_name = getattr(theory_module, "__file__", None)
    if not theory_source_name:
        raise RuntimeError("finite counting-space source path is unavailable")
    sources = (
        ("finite_association_rank_stress.py", rank_source),
        (
            "finite_atomic_counting_space.py",
            Path(theory_source_name).resolve(),
        ),
    )
    digest = hashlib.sha256()
    digest.update(b"heterodiff-association-rank-stress-source-bundle-v1\n")
    for label, path in sources:
        payload = path.read_bytes()
        digest.update(label.encode("ascii") + b"\n")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _rank_stress_specification_path() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "research"
        / "62_a1_association_guided_residual_falsification_spec.md"
    )


def _rank_stress_specification_sha256() -> str:
    path = _rank_stress_specification_path()
    if not path.is_file():
        raise RuntimeError("frozen rank-stress specification is unavailable")
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class _RankStressFreshProcessPermit:
    nonce: str
    destination: Path
    worker_pid: int
    parent_pid: int
    _key: object

    def __post_init__(self) -> None:
        if self._key is not _FRESH_PROCESS_PERMIT_KEY:
            raise TypeError("fresh-process permit was not issued by the CLI boundary")
        if (
            type(self.nonce) is not str
            or len(self.nonce) != 64
            or any(character not in "0123456789abcdef" for character in self.nonce)
        ):
            raise ValueError("fresh-process nonce must be 32 lowercase hex bytes")
        if not isinstance(self.destination, Path) or not self.destination.is_absolute():
            raise TypeError("fresh-process destination must be an absolute Path")
        if self.worker_pid != os.getpid() or self.worker_pid != _IMPORT_PROCESS_ID:
            raise RuntimeError("fresh-process permit PID is inconsistent")
        if self.parent_pid != os.getppid():
            raise RuntimeError("fresh-process permit parent PID is inconsistent")
        if _IMPORT_FRESH_MARKER != "1" or _IMPORT_FRESH_NONCE != self.nonce:
            raise RuntimeError("fresh-process evidence was absent at module import")


def _prepared_custody_record(
    prepared_runs: Tuple[PreparedAssociationRankStressRun, ...],
    *,
    runtime_sha256: str,
    source_sha256: str,
    specification_sha256: str,
    permit: _RankStressFreshProcessPermit,
) -> dict:
    rank_records = []
    for prepared in prepared_runs:
        manifest = prepared.manifest
        if (
            manifest.aggregate_sha256
            != RANK_STRESS_EXPECTED_MANIFEST_SHA256[prepared.fixture.rank]
        ):
            raise RuntimeError("prepared rank manifest is not frozen")
        rank_records.append(
            {
                "rank": prepared.fixture.rank,
                "aggregate_sha256": manifest.aggregate_sha256,
                "records": [
                    {
                        "name": record.name,
                        "dtype": record.dtype,
                        "shape": record.shape,
                        "sha256": record.sha256,
                        "payload_base64": base64.b64encode(record.payload).decode(
                            "ascii"
                        ),
                    }
                    for record in manifest.records
                ],
            }
        )
    value = {
        "schema": RANK_STRESS_PREPARED_SCHEMA,
        "runtime_sha256": _lower_sha256(
            runtime_sha256, name="runtime_sha256"
        ),
        "source_sha256": _lower_sha256(source_sha256, name="source_sha256"),
        "specification_sha256": _lower_sha256(
            specification_sha256, name="specification_sha256"
        ),
        "fresh_nonce_sha256": hashlib.sha256(
            permit.nonce.encode("ascii")
        ).hexdigest(),
        "worker_pid": permit.worker_pid,
        "parent_pid": permit.parent_pid,
        "prepared_unix_ns": time.time_ns(),
        "ranks": rank_records,
    }
    value["prepared_custody_sha256"] = _sha256_json(value)
    return value


def _prepared_custody_path(destination: Path) -> Path:
    return Path(os.fspath(destination) + ".prepared.json")


@dataclass(frozen=True)
class RankStressGateExecutionResult:
    """Raw complete all-rank record, not decision-admissible by itself."""

    runtime: RankStressRuntimeMetadata
    rank_results: Tuple[RankStressRankExecutionResult, ...]
    analytic_algorithm_id: str
    source_sha256: str
    specification_sha256: str
    prepared_custody_sha256: str
    initial_peak_rss_bytes: int
    final_peak_rss_bytes: int
    fresh_process_normalized_peak_rss_delta_bytes: int
    peak_rss_method_id: str
    result_sha256: str = ""

    def __post_init__(self) -> None:
        if type(self.runtime) is not RankStressRuntimeMetadata:
            raise TypeError("runtime has the wrong type")
        if self.analytic_algorithm_id != RANK_STRESS_ANALYTIC_ALGORITHM_ID:
            raise ValueError("analytic_algorithm_id is not frozen")
        _lower_sha256(self.source_sha256, name="source_sha256")
        _lower_sha256(
            self.specification_sha256, name="specification_sha256"
        )
        _lower_sha256(
            self.prepared_custody_sha256, name="prepared_custody_sha256"
        )
        if type(self.rank_results) is not tuple or any(
            type(value) is not RankStressRankExecutionResult
            for value in self.rank_results
        ):
            raise TypeError("rank_results has the wrong type")
        if tuple(value.rank for value in self.rank_results) != tuple(
            sorted(value.rank for value in self.rank_results)
        ):
            raise ValueError("rank_results must be strictly ordered")
        for name in (
            "initial_peak_rss_bytes",
            "final_peak_rss_bytes",
            "fresh_process_normalized_peak_rss_delta_bytes",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or type(value) is not int or value < 0:
                raise TypeError("%s must be a nonnegative integer" % name)
        if self.final_peak_rss_bytes < self.initial_peak_rss_bytes:
            raise ValueError("final peak RSS cannot be below initial peak RSS")
        expected_delta = self.final_peak_rss_bytes - self.initial_peak_rss_bytes
        if self.fresh_process_normalized_peak_rss_delta_bytes != expected_delta:
            raise ValueError("fresh-process RSS delta is inconsistent")
        if self.peak_rss_method_id != self.runtime.peak_rss_method_id:
            raise ValueError("peak RSS method disagrees with runtime metadata")
        expected = _sha256_json(_suite_payload(self))
        if self.result_sha256:
            _lower_sha256(self.result_sha256, name="result_sha256")
            if self.result_sha256 != expected:
                raise ValueError("suite result digest is inconsistent")
        else:
            object.__setattr__(self, "result_sha256", expected)

    @property
    def diagnostic_gate_conditions_satisfied(self) -> bool:
        """Recompute raw conditions without asserting loader-verified custody."""

        return (
            tuple(value.rank for value in self.rank_results)
            == RANK_STRESS_RANKS
            and self.source_sha256 == _rank_stress_source_bundle_sha256()
            and self.specification_sha256
            == _rank_stress_specification_sha256()
            and self.runtime.fresh_process_marker_observed
            and self.runtime.benchmark_metadata_complete
            and all(value.rank_gate_passed for value in self.rank_results)
        )


def _rank_stress_path_sha256(path: Path, *, role: str) -> str:
    if not isinstance(path, Path) or not path.is_absolute():
        raise TypeError("rank-stress receipt paths must be absolute Paths")
    return _sha256_json(
        {
            "schema": "heterodiff-association-rank-stress-path-v1",
            "role": role,
            "path": os.fspath(path),
        }
    )


def _rank_stress_loader_receipt_payload(
    *,
    raw_result_sha256: str,
    serialized_result_sha256: str,
    prepared_custody_sha256: str,
    serialized_prepared_custody_sha256: str,
    result_path_sha256: str,
    prepared_custody_path_sha256: str,
) -> dict:
    return {
        "schema": RANK_STRESS_LOADER_RECEIPT_SCHEMA,
        "raw_result_sha256": _lower_sha256(
            raw_result_sha256, name="raw_result_sha256"
        ),
        "serialized_result_sha256": _lower_sha256(
            serialized_result_sha256, name="serialized_result_sha256"
        ),
        "prepared_custody_sha256": _lower_sha256(
            prepared_custody_sha256, name="prepared_custody_sha256"
        ),
        "serialized_prepared_custody_sha256": _lower_sha256(
            serialized_prepared_custody_sha256,
            name="serialized_prepared_custody_sha256",
        ),
        "result_path_sha256": _lower_sha256(
            result_path_sha256, name="result_path_sha256"
        ),
        "prepared_custody_path_sha256": _lower_sha256(
            prepared_custody_path_sha256,
            name="prepared_custody_path_sha256",
        ),
    }


class LoaderVerifiedAssociationRankStressGateResult:
    """Decision-admissible result minted only after both files are reloaded."""

    __slots__ = (
        "_raw_result",
        "_raw_result_sha256",
        "_serialized_result_sha256",
        "_prepared_custody_sha256",
        "_serialized_prepared_custody_sha256",
        "_result_path_sha256",
        "_prepared_custody_path_sha256",
        "_loader_receipt_sha256",
        "_result_path",
        "_prepared_custody_path",
        "_locked",
    )

    def __init__(
        self,
        *,
        raw_result: RankStressGateExecutionResult,
        serialized_result_sha256: str,
        prepared_custody_sha256: str,
        serialized_prepared_custody_sha256: str,
        result_path_sha256: str,
        prepared_custody_path_sha256: str,
        loader_receipt_sha256: str,
        result_path: Path,
        prepared_custody_path: Path,
        _construction_key: object,
    ) -> None:
        if _construction_key is not _LOADER_VERIFIED_RESULT_KEY:
            raise TypeError(
                "use load_association_rank_stress_gate_result to obtain "
                "decision-admissible rank-stress evidence"
            )
        if type(raw_result) is not RankStressGateExecutionResult:
            raise TypeError("raw_result has the wrong exact type")
        if prepared_custody_sha256 != raw_result.prepared_custody_sha256:
            raise ValueError("verified custody receipt disagrees with the raw result")
        if (
            not isinstance(result_path, Path)
            or not result_path.is_absolute()
            or not isinstance(prepared_custody_path, Path)
            or not prepared_custody_path.is_absolute()
        ):
            raise TypeError("verified artifact paths must be absolute Paths")
        if _prepared_custody_path(result_path) != prepared_custody_path:
            raise ValueError("prepared-custody path is not the result companion")
        if _rank_stress_path_sha256(result_path, role="result") != result_path_sha256:
            raise ValueError("result path digest is inconsistent")
        if (
            _rank_stress_path_sha256(
                prepared_custody_path, role="prepared-custody"
            )
            != prepared_custody_path_sha256
        ):
            raise ValueError("prepared-custody path digest is inconsistent")
        payload = _rank_stress_loader_receipt_payload(
            raw_result_sha256=raw_result.result_sha256,
            serialized_result_sha256=serialized_result_sha256,
            prepared_custody_sha256=prepared_custody_sha256,
            serialized_prepared_custody_sha256=(
                serialized_prepared_custody_sha256
            ),
            result_path_sha256=result_path_sha256,
            prepared_custody_path_sha256=prepared_custody_path_sha256,
        )
        expected = _sha256_json(payload)
        _lower_sha256(loader_receipt_sha256, name="loader_receipt_sha256")
        if loader_receipt_sha256 != expected:
            raise ValueError("loader verification receipt is inconsistent")
        object.__setattr__(self, "_raw_result", raw_result)
        object.__setattr__(self, "_raw_result_sha256", raw_result.result_sha256)
        object.__setattr__(
            self,
            "_serialized_result_sha256",
            _lower_sha256(
                serialized_result_sha256, name="serialized_result_sha256"
            ),
        )
        object.__setattr__(
            self,
            "_prepared_custody_sha256",
            _lower_sha256(prepared_custody_sha256, name="prepared_custody_sha256"),
        )
        object.__setattr__(
            self,
            "_serialized_prepared_custody_sha256",
            _lower_sha256(
                serialized_prepared_custody_sha256,
                name="serialized_prepared_custody_sha256",
            ),
        )
        object.__setattr__(
            self,
            "_result_path_sha256",
            _lower_sha256(result_path_sha256, name="result_path_sha256"),
        )
        object.__setattr__(
            self,
            "_prepared_custody_path_sha256",
            _lower_sha256(
                prepared_custody_path_sha256,
                name="prepared_custody_path_sha256",
            ),
        )
        object.__setattr__(self, "_loader_receipt_sha256", loader_receipt_sha256)
        object.__setattr__(self, "_result_path", result_path)
        object.__setattr__(self, "_prepared_custody_path", prepared_custody_path)
        object.__setattr__(self, "_locked", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_locked", False):
            raise AttributeError("loader-verified rank-stress result is immutable")
        object.__setattr__(self, name, value)

    def assert_integrity(self) -> None:
        self._raw_result.runtime.__post_init__()
        for rank_result in self._raw_result.rank_results:
            rank_result.__post_init__()
        self._raw_result.__post_init__()
        if self._raw_result.result_sha256 != self._raw_result_sha256:
            raise RuntimeError("raw rank-stress result changed after loader admission")
        if self._prepared_custody_sha256 != self._raw_result.prepared_custody_sha256:
            raise RuntimeError("prepared-custody binding changed after loader admission")
        payload = _rank_stress_loader_receipt_payload(
            raw_result_sha256=self._raw_result_sha256,
            serialized_result_sha256=self._serialized_result_sha256,
            prepared_custody_sha256=self._prepared_custody_sha256,
            serialized_prepared_custody_sha256=(
                self._serialized_prepared_custody_sha256
            ),
            result_path_sha256=self._result_path_sha256,
            prepared_custody_path_sha256=self._prepared_custody_path_sha256,
        )
        if _sha256_json(payload) != self._loader_receipt_sha256:
            raise RuntimeError("loader receipt changed after admission")
        if _prepared_custody_path(self._result_path) != self._prepared_custody_path:
            raise RuntimeError("verified artifact path relationship changed")
        if (
            _rank_stress_path_sha256(self._result_path, role="result")
            != self._result_path_sha256
            or _rank_stress_path_sha256(
                self._prepared_custody_path, role="prepared-custody"
            )
            != self._prepared_custody_path_sha256
        ):
            raise RuntimeError("verified artifact path digest changed")

    def revalidate_prepared_custody(self) -> None:
        """Reopen both exact files and require the same loader receipt."""

        self.assert_integrity()
        reloaded = load_association_rank_stress_gate_result(self._result_path)
        reloaded.assert_integrity()
        observed = (
            reloaded.raw_result.result_sha256,
            reloaded.serialized_result_sha256,
            reloaded.prepared_custody_sha256,
            reloaded.serialized_prepared_custody_sha256,
            reloaded.result_path_sha256,
            reloaded.prepared_custody_path_sha256,
            reloaded.loader_receipt_sha256,
        )
        expected = (
            self._raw_result_sha256,
            self._serialized_result_sha256,
            self._prepared_custody_sha256,
            self._serialized_prepared_custody_sha256,
            self._result_path_sha256,
            self._prepared_custody_path_sha256,
            self._loader_receipt_sha256,
        )
        if observed != expected:
            raise RuntimeError("rank-stress files changed after loader admission")

    @property
    def raw_result(self) -> RankStressGateExecutionResult:
        self.assert_integrity()
        return self._raw_result

    @property
    def serialized_result_sha256(self) -> str:
        return self._serialized_result_sha256

    @property
    def prepared_custody_sha256(self) -> str:
        return self._prepared_custody_sha256

    @property
    def serialized_prepared_custody_sha256(self) -> str:
        return self._serialized_prepared_custody_sha256

    @property
    def result_path_sha256(self) -> str:
        return self._result_path_sha256

    @property
    def prepared_custody_path_sha256(self) -> str:
        return self._prepared_custody_path_sha256

    @property
    def loader_receipt_sha256(self) -> str:
        return self._loader_receipt_sha256

    @property
    def section_nine_gate_passed(self) -> bool:
        """Return the authoritative gate decision for reloaded evidence."""

        self.revalidate_prepared_custody()
        self.assert_integrity()
        return self._raw_result.diagnostic_gate_conditions_satisfied


def _execute_one_rank_stress_protocol(
    prepared: PreparedAssociationRankStressRun,
) -> RankStressRankExecutionResult:
    if type(prepared) is not PreparedAssociationRankStressRun:
        raise TypeError("prepared has the wrong type")
    rank = prepared.fixture.rank
    static_python_overhead = _deep_python_object_overhead_bytes(prepared)
    if tracemalloc.is_tracing():
        raise RuntimeError("rank-stress worker requires a fresh tracemalloc state")
    tracemalloc.start()
    try:
        warmup_start = time.perf_counter_ns()
        warmup = evaluate_association_rank_stress_analytic_grid(prepared)
        warmup_wall = (time.perf_counter_ns() - warmup_start) / 1.0e9
        if np.asarray(warmup.density_grid).shape != RANK_STRESS_DENSITY_SHAPE:
            raise ArithmeticError("analytic warm-up has the wrong density shape")
        _, python_peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    analytic_sha256 = _numeric_array_sha256(warmup.density_grid)
    exhaustive = evaluate_association_rank_stress_exhaustive_grid(
        prepared.fixture
    )
    if np.asarray(exhaustive).shape != RANK_STRESS_DENSITY_SHAPE:
        raise ArithmeticError("exhaustive oracle has the wrong density shape")
    exhaustive_sha256 = _numeric_array_sha256(exhaustive)
    relative_error_by_time = tuple(
        maximum_elementwise_relative_error(
            warmup.density_grid[time_index], exhaustive[time_index]
        )
        for time_index in range(RANK_STRESS_TIME_POINT_COUNT)
    )
    relative_error = max(relative_error_by_time)
    coefficient_updates = warmup.coefficient_updates
    expected_updates = warmup.expected_coefficient_updates
    peak_owned = warmup.peak_owned_numeric_bytes
    peak_visible = int(warmup.peak_visible_numeric_bytes or 0)
    peak_workspace = int(warmup.peak_reserved_workspace_bytes or 0)
    del exhaustive

    timings = []
    for _ in range(RANK_STRESS_BENCHMARK_REPETITION_COUNT):
        started = time.perf_counter_ns()
        repetition = evaluate_association_rank_stress_analytic_grid(prepared)
        elapsed = (time.perf_counter_ns() - started) / 1.0e9
        if np.asarray(repetition.density_grid).shape != RANK_STRESS_DENSITY_SHAPE:
            raise ArithmeticError("timed analytic repetition has the wrong shape")
        if _numeric_array_sha256(repetition.density_grid) != analytic_sha256:
            raise ArithmeticError("timed analytic repetition changed its density")
        if (
            repetition.coefficient_updates != coefficient_updates
            or repetition.expected_coefficient_updates != expected_updates
        ):
            raise ArithmeticError("timed analytic repetition changed its counter")
        if not repetition.allocation_accounting_complete:
            raise ArithmeticError("timed allocation accounting became incomplete")
        peak_owned = max(peak_owned, repetition.peak_owned_numeric_bytes)
        peak_visible = max(
            peak_visible, int(repetition.peak_visible_numeric_bytes or 0)
        )
        peak_workspace = max(
            peak_workspace,
            int(repetition.peak_reserved_workspace_bytes or 0),
        )
        timings.append(float(elapsed))
    return RankStressRankExecutionResult(
        rank=rank,
        fixture_manifest_sha256=prepared.manifest.aggregate_sha256,
        oracle_time_indices=tuple(range(RANK_STRESS_TIME_POINT_COUNT)),
        density_shape=RANK_STRESS_DENSITY_SHAPE,
        analytic_density_sha256=analytic_sha256,
        exhaustive_density_sha256=exhaustive_sha256,
        maximum_relative_error=relative_error,
        relative_error_by_time=relative_error_by_time,
        coefficient_updates=coefficient_updates,
        expected_coefficient_updates=expected_updates,
        peak_owned_numeric_bytes=peak_owned,
        peak_visible_numeric_bytes=peak_visible,
        peak_reserved_workspace_bytes=peak_workspace,
        scipy_expm_workspace_bound_bytes=(
            RANK_STRESS_SCIPY_EXPM_WORKSPACE_BOUND_BYTES
        ),
        numpy_kernel_workspace_bound_bytes=(
            RANK_STRESS_NUMPY_KERNEL_WORKSPACE_BOUND_BYTES
        ),
        allocation_accounting_complete=warmup.allocation_accounting_complete,
        occurrence_matching_enumeration_used=(
            warmup.occurrence_matching_enumeration_used
        ),
        python_allocation_upper_bound_bytes=(
            static_python_overhead + int(python_peak)
        ),
        warmup_wall_seconds=float(warmup_wall),
        timed_wall_seconds=tuple(timings),
        median_five_wall_seconds=float(statistics.median(timings)),
    )


def execute_association_rank_stress_gate_in_worker(
    permit: _RankStressFreshProcessPermit,
) -> RankStressGateExecutionResult:
    """Execute Section 9 only behind the launcher-created process boundary.

    This non-learning function performs the full all-rank protocol.  The
    launcher below is the supported entry point; direct in-process calls fail
    closed before evaluating a grid.  The nonce is process-custody evidence,
    not an authentication or adversarial-security mechanism.
    """

    if type(permit) is not _RankStressFreshProcessPermit:
        raise TypeError("rank-stress execution requires a CLI-issued permit")
    if permit.nonce in _CONSUMED_FRESH_NONCES:
        raise RuntimeError("fresh-process permit is single-use")
    _CONSUMED_FRESH_NONCES.add(permit.nonce)
    thread_environment = tuple(
        os.environ.get(name) for name in RANK_STRESS_THREAD_ENVIRONMENT
    )
    if any(value != "1" for value in thread_environment):
        raise RuntimeError("all native thread limits must equal one before import")
    runtime = capture_rank_stress_runtime_metadata()
    if not runtime.benchmark_metadata_complete:
        raise RuntimeError(
            "rank-stress runtime or native-thread metadata is not frozen"
        )
    source_sha256 = _rank_stress_source_bundle_sha256()
    specification_sha256 = _rank_stress_specification_sha256()
    prepared_runs = tuple(
        prepare_association_rank_stress_run(rank) for rank in RANK_STRESS_RANKS
    )
    custody = _prepared_custody_record(
        prepared_runs,
        runtime_sha256=runtime.runtime_sha256,
        source_sha256=source_sha256,
        specification_sha256=specification_sha256,
        permit=permit,
    )
    _atomic_write_canonical_json_exclusive(
        _prepared_custody_path(permit.destination), custody
    )
    prepared_custody_sha256 = custody["prepared_custody_sha256"]
    initial_peak, rss_method = _peak_rss_bytes()
    results = tuple(
        _execute_one_rank_stress_protocol(prepared) for prepared in prepared_runs
    )
    final_peak, final_method = _peak_rss_bytes()
    if _rank_stress_source_bundle_sha256() != source_sha256:
        raise RuntimeError("rank-stress decision source changed during execution")
    if (
        _rank_stress_specification_sha256()
        != specification_sha256
    ):
        raise RuntimeError("rank-stress specification changed during execution")
    if final_method != rss_method or final_method != runtime.peak_rss_method_id:
        raise RuntimeError("peak RSS measurement method changed within the worker")
    return RankStressGateExecutionResult(
        runtime=runtime,
        rank_results=results,
        analytic_algorithm_id=RANK_STRESS_ANALYTIC_ALGORITHM_ID,
        source_sha256=source_sha256,
        specification_sha256=specification_sha256,
        prepared_custody_sha256=prepared_custody_sha256,
        initial_peak_rss_bytes=initial_peak,
        final_peak_rss_bytes=final_peak,
        fresh_process_normalized_peak_rss_delta_bytes=(
            final_peak - initial_peak
        ),
        peak_rss_method_id=rss_method,
    )


def _atomic_write_canonical_json_exclusive(
    destination: Path, value: Mapping[str, object]
) -> None:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("rank-stress result destination already exists")
    payload = _canonical_json(value) + b"\n"
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=str(destination.parent),
            prefix=".rank-stress-",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary_name, destination)
        os.unlink(temporary_name)
        temporary_name = None
        directory_descriptor = os.open(os.fspath(destination.parent), os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def _atomic_write_rank_stress_result(
    destination: Path, result: RankStressGateExecutionResult
) -> None:
    if type(result) is not RankStressGateExecutionResult:
        raise TypeError("result has the wrong type")
    serialized = asdict(result)
    serialized["schema"] = RANK_STRESS_SUITE_SCHEMA
    _atomic_write_canonical_json_exclusive(destination, serialized)


def launch_association_rank_stress_gate(
    destination: object,
    *,
    python_executable: Optional[object] = None,
    timeout_seconds: Optional[float] = None,
) -> LoaderVerifiedAssociationRankStressGateResult:
    """Launch, require child success, and revalidate the resulting audit record."""

    output_path = Path(destination).resolve()
    if output_path.exists() or _prepared_custody_path(output_path).exists():
        raise FileExistsError("rank-stress result or custody destination exists")
    executable = sys.executable if python_executable is None else os.fspath(
        python_executable
    )
    environment = dict(os.environ)
    for name in RANK_STRESS_THREAD_ENVIRONMENT:
        environment[name] = "1"
    environment["PYTHONHASHSEED"] = "0"
    environment[RANK_STRESS_FRESH_PROCESS_MARKER] = "1"
    nonce = secrets.token_hex(32)
    environment[RANK_STRESS_FRESH_PROCESS_NONCE] = nonce
    source_root = os.fspath(Path(__file__).resolve().parents[2])
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_root
        if not existing_pythonpath
        else source_root + os.pathsep + existing_pythonpath
    )
    completed = subprocess.run(
        (
            executable,
            "-m",
            "heterodiff.experiments.finite_association_rank_stress",
            "--execute-frozen-rank-stress",
            os.fspath(output_path),
            nonce,
        ),
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(
            "fresh rank-stress worker failed%s"
            % ((": " + detail) if detail else "")
        )
    return load_association_rank_stress_gate_result(output_path)


def _runtime_from_mapping(value: Mapping[str, object]) -> RankStressRuntimeMetadata:
    payload = dict(value)
    payload.pop("schema", None)
    _lower_sha256(
        payload.get("runtime_sha256"), name="serialized runtime_sha256"
    )
    payload["thread_environment"] = tuple(
        tuple(item) for item in payload["thread_environment"]
    )
    return RankStressRuntimeMetadata(**payload)


def _rank_result_from_mapping(
    value: Mapping[str, object]
) -> RankStressRankExecutionResult:
    payload = dict(value)
    payload.pop("schema", None)
    _lower_sha256(
        payload.get("result_sha256"), name="serialized rank result_sha256"
    )
    payload["oracle_time_indices"] = tuple(payload["oracle_time_indices"])
    payload["density_shape"] = tuple(payload["density_shape"])
    payload["relative_error_by_time"] = tuple(
        payload["relative_error_by_time"]
    )
    payload["timed_wall_seconds"] = tuple(payload["timed_wall_seconds"])
    return RankStressRankExecutionResult(**payload)


def _load_prepared_custody_payload(payload: bytes) -> dict:
    if type(payload) is not bytes or not payload:
        raise TypeError("prepared-custody payload must be nonempty bytes")
    value = json.loads(payload.decode("ascii"))
    if not isinstance(value, dict) or value.get("schema") != RANK_STRESS_PREPARED_SCHEMA:
        raise ValueError("rank-stress prepared-custody schema is invalid")
    claimed = _lower_sha256(
        value.get("prepared_custody_sha256"),
        name="serialized prepared_custody_sha256",
    )
    unsealed = dict(value)
    unsealed.pop("prepared_custody_sha256")
    if _sha256_json(unsealed) != claimed:
        raise ValueError("prepared-custody digest is inconsistent")
    for name in ("runtime_sha256", "source_sha256", "specification_sha256"):
        _lower_sha256(value.get(name), name="prepared " + name)
    ranks = value.get("ranks")
    if not isinstance(ranks, list) or tuple(
        item.get("rank") if isinstance(item, dict) else None for item in ranks
    ) != RANK_STRESS_RANKS:
        raise ValueError("prepared custody does not contain every frozen rank")
    for item in ranks:
        rank = item["rank"]
        prepared = prepare_association_rank_stress_run(rank)
        if item.get("aggregate_sha256") != prepared.manifest.aggregate_sha256:
            raise ValueError("prepared manifest aggregate is not frozen")
        records = item.get("records")
        if not isinstance(records, list) or len(records) != len(
            prepared.manifest.records
        ):
            raise ValueError("prepared manifest records are incomplete")
        for serialized, expected in zip(records, prepared.manifest.records):
            if not isinstance(serialized, dict):
                raise ValueError("prepared manifest record is invalid")
            try:
                payload = base64.b64decode(
                    serialized.get("payload_base64", ""), validate=True
                )
            except (ValueError, TypeError) as error:
                raise ValueError("prepared manifest payload is invalid") from error
            if (
                serialized.get("name") != expected.name
                or serialized.get("dtype") != expected.dtype
                or tuple(serialized.get("shape", ())) != expected.shape
                or serialized.get("sha256") != expected.sha256
                or payload != expected.payload
            ):
                raise ValueError("prepared manifest record is not frozen")
    return value


def _load_prepared_custody(source: Path) -> dict:
    with source.open("rb") as handle:
        return _load_prepared_custody_payload(handle.read())


def load_association_rank_stress_gate_result(
    source: object,
) -> LoaderVerifiedAssociationRankStressGateResult:
    """Reload both durable files and mint decision-admissible evidence."""

    path = Path(source).resolve()
    with path.open("rb") as handle:
        serialized_result = handle.read()
    value = json.loads(serialized_result.decode("ascii"))
    if not isinstance(value, dict) or value.get("schema") != RANK_STRESS_SUITE_SCHEMA:
        raise ValueError("rank-stress suite schema is invalid")
    payload = dict(value)
    payload.pop("schema")
    _lower_sha256(
        payload.get("result_sha256"), name="serialized suite result_sha256"
    )
    payload["runtime"] = _runtime_from_mapping(payload["runtime"])
    payload["rank_results"] = tuple(
        _rank_result_from_mapping(item) for item in payload["rank_results"]
    )
    result = RankStressGateExecutionResult(**payload)
    if result.source_sha256 != _rank_stress_source_bundle_sha256():
        raise ValueError("suite source digest does not match current frozen source")
    if result.specification_sha256 != _rank_stress_specification_sha256():
        raise ValueError(
            "suite specification digest does not match current frozen specification"
        )
    custody_path = _prepared_custody_path(path)
    with custody_path.open("rb") as handle:
        serialized_custody = handle.read()
    custody = _load_prepared_custody_payload(serialized_custody)
    if (
        custody["prepared_custody_sha256"]
        != result.prepared_custody_sha256
        or custody["runtime_sha256"] != result.runtime.runtime_sha256
        or custody["source_sha256"] != result.source_sha256
        or custody["specification_sha256"] != result.specification_sha256
    ):
        raise ValueError("suite is not cross-bound to prepared custody")
    if tuple(
        item["aggregate_sha256"] for item in custody["ranks"]
    ) != tuple(item.fixture_manifest_sha256 for item in result.rank_results):
        raise ValueError("suite rank results disagree with prepared custody")
    serialized_result_sha256 = hashlib.sha256(serialized_result).hexdigest()
    serialized_custody_sha256 = hashlib.sha256(serialized_custody).hexdigest()
    result_path_sha256 = _rank_stress_path_sha256(path, role="result")
    custody_path_sha256 = _rank_stress_path_sha256(
        custody_path, role="prepared-custody"
    )
    receipt_payload = _rank_stress_loader_receipt_payload(
        raw_result_sha256=result.result_sha256,
        serialized_result_sha256=serialized_result_sha256,
        prepared_custody_sha256=custody["prepared_custody_sha256"],
        serialized_prepared_custody_sha256=serialized_custody_sha256,
        result_path_sha256=result_path_sha256,
        prepared_custody_path_sha256=custody_path_sha256,
    )
    return LoaderVerifiedAssociationRankStressGateResult(
        raw_result=result,
        serialized_result_sha256=serialized_result_sha256,
        prepared_custody_sha256=custody["prepared_custody_sha256"],
        serialized_prepared_custody_sha256=serialized_custody_sha256,
        result_path_sha256=result_path_sha256,
        prepared_custody_path_sha256=custody_path_sha256,
        loader_receipt_sha256=_sha256_json(receipt_payload),
        result_path=path,
        prepared_custody_path=custody_path,
        _construction_key=_LOADER_VERIFIED_RESULT_KEY,
    )


def _rank_stress_cli_exit_code(
    result: LoaderVerifiedAssociationRankStressGateResult,
) -> int:
    if type(result) is not LoaderVerifiedAssociationRankStressGateResult:
        raise TypeError("result must come from the rank-stress result loader")
    return 0 if result.section_nine_gate_passed else 2


def _main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 3 or arguments[0] != "--execute-frozen-rank-stress":
        raise SystemExit(
            "usage: python -m heterodiff.experiments.finite_association_rank_stress "
            "--execute-frozen-rank-stress OUTPUT.json LAUNCH_NONCE"
        )
    destination = Path(arguments[1]).resolve()
    permit = _RankStressFreshProcessPermit(
        nonce=arguments[2],
        destination=destination,
        worker_pid=os.getpid(),
        parent_pid=os.getppid(),
        _key=_FRESH_PROCESS_PERMIT_KEY,
    )
    raw_result = execute_association_rank_stress_gate_in_worker(permit)
    _atomic_write_rank_stress_result(destination, raw_result)
    verified_result = load_association_rank_stress_gate_result(destination)
    return _rank_stress_cli_exit_code(verified_result)


__all__ = [
    "RANK_STRESS_ANALYTIC_ALGORITHM_ID",
    "RANK_STRESS_BENCHMARK_REPETITION_COUNT",
    "RANK_STRESS_BENCHMARK_WARMUP_COUNT",
    "RANK_STRESS_DENSITY_SHAPE",
    "RANK_STRESS_FRESH_PROCESS_MARKER",
    "RANK_STRESS_FRESH_PROCESS_NONCE",
    "RANK_STRESS_FULL_OUTPUT_BYTES",
    "RANK_STRESS_EXPECTED_FULL_GRID_UPDATES",
    "RANK_STRESS_EXPECTED_MANIFEST_SHA256",
    "RANK_STRESS_EXPECTED_NUMPY_VERSION",
    "RANK_STRESS_EXPECTED_PYTHON_VERSION",
    "RANK_STRESS_EXPECTED_SCIPY_VERSION",
    "RANK_STRESS_EXPECTED_THREADPOOLCTL_VERSION",
    "RANK_STRESS_MAXIMUM_COEFFICIENT_UPDATES",
    "RANK_STRESS_MAXIMUM_OWNED_NUMERIC_BYTES",
    "RANK_STRESS_NUMPY_KERNEL_WORKSPACE_BOUND_BYTES",
    "RANK_STRESS_OCCURRENCE_MATCHING_ENUMERATION_USED",
    "RANK_STRESS_LOADER_RECEIPT_SCHEMA",
    "RANK_STRESS_PREPARED_SCHEMA",
    "RANK_STRESS_RANKS",
    "RANK_STRESS_RELATIVE_AGREEMENT_TOLERANCE",
    "RANK_STRESS_SCIPY_EXPM_WORKSPACE_BOUND_BYTES",
    "RANK_STRESS_THREAD_ENVIRONMENT",
    "RANK_STRESS_TIME_POINT_COUNT",
    "RANK_STRESS_UNEXECUTED_REQUIREMENTS",
    "FrozenAssociationRankStressFixture",
    "LoaderVerifiedAssociationRankStressGateResult",
    "OwnedNumericAllocationRegistry",
    "PreparedAssociationRankStressRun",
    "RankStressAnalyticGridResult",
    "RankStressAnalyticTimeResult",
    "RankStressArrayManifest",
    "RankStressCoefficientUpdateCount",
    "RankStressGateExecutionResult",
    "RankStressRankExecutionResult",
    "RankStressRuntimeMetadata",
    "SerializedRankStressArray",
    "build_frozen_association_rank_stress_fixture",
    "build_rank_stress_array_manifest",
    "capture_rank_stress_runtime_metadata",
    "direct_rank_stress_loop_bound_count",
    "evaluate_association_rank_stress_analytic_grid",
    "evaluate_association_rank_stress_analytic_time",
    "evaluate_association_rank_stress_exhaustive_time",
    "evaluate_association_rank_stress_exhaustive_grid",
    "exact_vandermonde_emission_rank",
    "launch_association_rank_stress_gate",
    "load_association_rank_stress_gate_result",
    "maximum_elementwise_relative_error",
    "prepare_association_rank_stress_run",
]


if __name__ == "__main__":  # pragma: no cover - exercised only by full gate
    raise SystemExit(_main())
