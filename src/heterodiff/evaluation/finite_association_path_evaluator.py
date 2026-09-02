"""Frozen time-inhomogeneous path evaluation for the finite A1 fixture.

This module is an evaluator, not a learner or an experiment runner.  A
certificate-bound classifier is converted to one positive physical potential
per observation with :class:`CertifiedFiniteAssociationPotentialAdapter`.
The existing finite-state path-control routines then propagate the exact and
candidate path laws under their *own* time-varying tilted generators.

The unconditional path divergences and oracle-self controls are kept in
separate reusable reference records.  They therefore need not be recomputed
for every seed and budget, while every candidate's primary and refined path
and occupancy integrations remain genuinely separate numerical calls.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from numbers import Integral, Real
import platform
import time as time_module
from typing import Optional, Sequence, Tuple

import numpy as np
import scipy

from heterodiff.evaluation.finite_association_residual_evaluator import (
    CertifiedFiniteAssociationLogitEvaluator,
    CertifiedFiniteAssociationPotentialAdapter,
)
from heterodiff.experiments.finite_association_guided_residual_pilot import (
    FrozenAssociationResidualFixture,
    frozen_association_fixture_sha256,
)
from heterodiff.theory.finite_bridge_path_control import (
    integrate_tilted_occupancy,
    potential_tilted_generator,
    tilted_path_kl,
)


_TERMINAL_TIME = 1.0
_FROZEN_TIME_COUNT = 33
_FROZEN_STATE_COUNT = 20
_FROZEN_OBSERVATION_COUNT = 21
_UNCONDITIONAL_NORMALIZER_FLOOR = 1.0e-12
_ORACLE_SELF_PATH_KL_LIMIT = 1.0e-10
_PATH_REFINEMENT_LIMIT = 1.0e-8
_ENDPOINT_REFINEMENT_LIMIT = 1.0e-8
_AMBIGUOUS_OBSERVATIONS = ((1, 1, 0), (1, 0, 1), (0, 1, 1))
_AMBIGUOUS_OBSERVATION_INDICES = (8, 7, 5)
_OVERFLOW_INDEX = 20
_UNCONDITIONAL_REFINEMENT_LIMIT = 1.0e-8
_TARGET_OCCUPANCY_ERROR_LIMIT = 1.0e-8
_FROZEN_PYTHON_VERSION = "3.11.5"
_FROZEN_NUMPY_VERSION = "2.4.6"
_FROZEN_SCIPY_VERSION = "1.17.1"
_ODE_METHOD = "scipy.integrate.solve_ivp:DOP853"
_QUADRATURE_METHOD = "scipy.integrate.quad_vec"


@dataclass(frozen=True)
class FiniteAssociationPathSolverSettings:
    """Recorded adaptive ODE/quadrature controls for one integration lane."""

    label: str
    rtol: float
    atol: float
    max_step: float
    quadrature_epsabs: float
    quadrature_epsrel: float
    quadrature_limit: int
    max_potential_evaluations: int

    def __post_init__(self) -> None:
        if self.label not in ("primary", "refined"):
            raise ValueError("solver label must be primary or refined")
        for name in (
            "rtol",
            "atol",
            "max_step",
            "quadrature_epsabs",
            "quadrature_epsrel",
        ):
            value = _nonnegative(getattr(self, name), name=name)
            if value <= 0.0:
                raise ValueError("%s must be strictly positive" % name)
            object.__setattr__(self, name, value)
        if self.rtol >= 1.0 or self.quadrature_epsrel >= 1.0:
            raise ValueError("relative tolerances must be below one")
        for name in ("quadrature_limit", "max_potential_evaluations"):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
                raise TypeError("%s must be an integer" % name)
            if int(value) <= 0:
                raise ValueError("%s must be positive" % name)
            object.__setattr__(self, name, int(value))


@dataclass(frozen=True)
class FiniteAssociationPathRuntime:
    """Versioned numerical backend included in path-reference custody."""

    python_version: str
    numpy_version: str
    scipy_version: str
    ode_method: str
    quadrature_method: str

    def __post_init__(self) -> None:
        for name in (
            "python_version",
            "numpy_version",
            "scipy_version",
            "ode_method",
            "quadrature_method",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise TypeError("%s must be a nonempty string" % name)

    @classmethod
    def current(cls) -> "FiniteAssociationPathRuntime":
        return cls(
            python_version=platform.python_version(),
            numpy_version=np.__version__,
            scipy_version=scipy.__version__,
            ode_method=_ODE_METHOD,
            quadrature_method=_QUADRATURE_METHOD,
        )

    @property
    def sha256(self) -> str:
        digest = hashlib.sha256()
        digest.update(b"heterodiff-a1-path-runtime-v1\0")
        for value in (
            self.python_version,
            self.numpy_version,
            self.scipy_version,
            self.ode_method,
            self.quadrature_method,
        ):
            digest.update(value.encode("utf-8"))
            digest.update(b"\0")
        return digest.hexdigest()

    @property
    def is_frozen_execution_runtime(self) -> bool:
        return (
            self.python_version == _FROZEN_PYTHON_VERSION
            and self.numpy_version == _FROZEN_NUMPY_VERSION
            and self.scipy_version == _FROZEN_SCIPY_VERSION
            and self.ode_method == _ODE_METHOD
            and self.quadrature_method == _QUADRATURE_METHOD
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


def _numeric_array(
    value: object, *, name: str, shape: Tuple[int, ...]
) -> np.ndarray:
    try:
        raw = np.asarray(value)
        objects = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("%s must be a rectangular numeric array" % name) from error
    if any(isinstance(item, (bool, np.bool_)) for item in objects.flat):
        raise TypeError("%s must not contain booleans" % name)
    if raw.dtype.kind not in "iuf" or raw.shape != shape:
        raise ValueError("%s must have shape %r" % (name, shape))
    result = raw.astype(np.float64, copy=True)
    if not np.all(np.isfinite(result)):
        raise ValueError("%s must contain only finite values" % name)
    return result


def _nonnegative(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError("%s must be finite and nonnegative" % name)
    return result


def _positive_integer(value: object, *, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result <= 0:
        raise ValueError("%s must be strictly positive" % name)
    return result


PRIMARY_PATH_SOLVER_SETTINGS = FiniteAssociationPathSolverSettings(
    label="primary",
    rtol=2.0e-10,
    atol=2.0e-12,
    max_step=1.0 / 128.0,
    quadrature_epsabs=1.0e-11,
    quadrature_epsrel=1.0e-10,
    quadrature_limit=2_000,
    max_potential_evaluations=300_000,
)
REFINED_PATH_SOLVER_SETTINGS = FiniteAssociationPathSolverSettings(
    label="refined",
    rtol=2.0e-11,
    atol=2.0e-13,
    max_step=1.0 / 256.0,
    quadrature_epsabs=1.0e-12,
    quadrature_epsrel=1.0e-11,
    quadrature_limit=2_000,
    max_potential_evaluations=300_000,
)


def _observation_index(value: object) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("observation_index must be an integer non-boolean value")
    result = int(value)
    if result < 0 or result >= _FROZEN_OBSERVATION_COUNT:
        raise IndexError("observation_index is out of range")
    return result


def _sha256(value: object, *, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError("%s must be a 64-character SHA-256 digest" % name)
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("%s must be hexadecimal" % name) from error
    if value != value.lower():
        raise ValueError("%s must use lowercase hexadecimal" % name)
    return value


def _digest_text(digest: "hashlib._Hash", value: str) -> None:
    encoded = value.encode("utf-8")
    digest.update(len(encoded).to_bytes(8, byteorder="little", signed=False))
    digest.update(encoded)


def _digest_array(digest: "hashlib._Hash", value: object) -> None:
    array = np.ascontiguousarray(value)
    _digest_text(digest, array.dtype.str)
    _digest_text(digest, ",".join(str(int(size)) for size in array.shape))
    payload = array.tobytes(order="C")
    digest.update(len(payload).to_bytes(8, byteorder="little", signed=False))
    digest.update(payload)


def _solver_settings_sha256(
    settings: FiniteAssociationPathSolverSettings,
) -> str:
    if not isinstance(settings, FiniteAssociationPathSolverSettings):
        raise TypeError("settings must be FiniteAssociationPathSolverSettings")
    digest = hashlib.sha256()
    digest.update(b"heterodiff-a1-path-solver-settings-v1\0")
    _digest_text(digest, settings.label)
    _digest_array(
        digest,
        np.asarray(
            (
                settings.rtol,
                settings.atol,
                settings.max_step,
                settings.quadrature_epsabs,
                settings.quadrature_epsrel,
            ),
            dtype=np.float64,
        ),
    )
    _digest_array(
        digest,
        np.asarray(
            (
                settings.quadrature_limit,
                settings.max_potential_evaluations,
            ),
            dtype=np.int64,
        ),
    )
    return digest.hexdigest()


def _validate_fixture(fixture: object) -> FrozenAssociationResidualFixture:
    if not isinstance(fixture, FrozenAssociationResidualFixture):
        raise TypeError("fixture must be a FrozenAssociationResidualFixture")
    expected = (
        _FROZEN_TIME_COUNT,
        _FROZEN_STATE_COUNT,
        _FROZEN_OBSERVATION_COUNT,
    )
    if fixture.population.joint_mass.shape != expected:
        raise ValueError("fixture is not the frozen 33 x 20 x 21 A1 population")
    if fixture.times[0] != 0.0 or fixture.times[-1] != _TERMINAL_TIME:
        raise ValueError("fixture must use the direct-time interval [0, 1]")
    return fixture


def finite_association_path_fixture_content_sha256(
    fixture: FrozenAssociationResidualFixture,
) -> str:
    """Hash the actual ordered finite objects consumed by path evaluation."""

    checked = _validate_fixture(fixture)
    digest = hashlib.sha256()
    digest.update(b"heterodiff-a1-path-fixture-content-v1\0")
    _digest_text(digest, frozen_association_fixture_sha256())
    for value in (
        np.asarray(checked.latent_space.states, dtype=np.int64),
        np.asarray(checked.retained_observation_space.states, dtype=np.int64),
        checked.oracle.generator,
        checked.initial_marginal,
        checked.times,
        checked.observation.reference_mass,
        checked.observation.kernel_mass,
        checked.observation.density_kernel,
        checked.population.observation_marginal_mass,
        checked.population.observation_marginal_density,
        checked.population.conditional_initial,
        checked.population.conditional_time,
        checked.population.conditional_terminal,
    ):
        _digest_array(digest, value)
    _digest_array(
        digest,
        np.asarray(
            (
                checked.population.terminal_time,
                checked.observation.overflow_index,
            ),
            dtype=np.float64,
        ),
    )
    return digest.hexdigest()


def _total_variation(first: np.ndarray, second: np.ndarray) -> float:
    result = 0.5 * math.fsum(
        abs(float(left) - float(right)) for left, right in zip(first, second)
    )
    if not math.isfinite(result) or result < 0.0:
        raise ArithmeticError("total variation is not representable")
    return result


def _validate_generator_grid(value: np.ndarray, *, name: str) -> None:
    if float(np.max(np.abs(np.sum(value, axis=2)))) > 1.0e-10:
        raise ValueError("%s is not conservative" % name)
    diagonal = np.diagonal(value, axis1=1, axis2=2)
    off_diagonal = np.array(value, copy=True)
    positions = np.arange(_FROZEN_STATE_COUNT)
    off_diagonal[:, positions, positions] = 0.0
    if np.any(diagonal > 0.0) or np.any(off_diagonal < 0.0):
        raise ValueError("%s has invalid CTMC rate signs" % name)


def _path_call(initial, generator, reference, candidate, times, *, refined):
    settings = (
        REFINED_PATH_SOLVER_SETTINGS
        if refined
        else PRIMARY_PATH_SOLVER_SETTINGS
    )
    return tilted_path_kl(
        initial,
        generator,
        reference,
        candidate,
        _TERMINAL_TIME,
        evaluation_times=times,
        rtol=settings.rtol,
        atol=settings.atol,
        max_step=settings.max_step,
        quadrature_epsabs=settings.quadrature_epsabs,
        quadrature_epsrel=settings.quadrature_epsrel,
        quadrature_limit=settings.quadrature_limit,
        max_potential_evaluations=settings.max_potential_evaluations,
    )


def _occupancy_call(initial, generator, potential, times, *, refined):
    settings = (
        REFINED_PATH_SOLVER_SETTINGS
        if refined
        else PRIMARY_PATH_SOLVER_SETTINGS
    )
    return integrate_tilted_occupancy(
        initial,
        generator,
        potential,
        _TERMINAL_TIME,
        evaluation_times=times,
        rtol=settings.rtol,
        atol=settings.atol,
        max_step=settings.max_step,
        quadrature_epsabs=settings.quadrature_epsabs,
        quadrature_epsrel=settings.quadrature_epsrel,
        quadrature_limit=settings.quadrature_limit,
        max_potential_evaluations=settings.max_potential_evaluations,
    )


class _ExactObservationPotential:
    def __init__(
        self, fixture: FrozenAssociationResidualFixture, observation_index: int
    ) -> None:
        self._oracle = fixture.oracle
        self._observation = fixture.observation.observation_at(observation_index)

    def __call__(self, direct_time: object) -> np.ndarray:
        if isinstance(direct_time, (bool, np.bool_)) or not isinstance(
            direct_time, Real
        ):
            raise TypeError("direct_time must be a real non-boolean number")
        time = float(direct_time)
        if not math.isfinite(time) or time < 0.0 or time > _TERMINAL_TIME:
            raise ValueError("direct_time must lie in [0, 1]")
        remaining = _TERMINAL_TIME - time
        tolerance = 32.0 * np.finfo(np.float64).eps
        if remaining < 0.0 and remaining >= -tolerance:
            remaining = 0.0
        return self._oracle.backward_information(remaining, self._observation)


class _UnitPotential:
    def __call__(self, direct_time: object) -> np.ndarray:
        if isinstance(direct_time, (bool, np.bool_)) or not isinstance(
            direct_time, Real
        ):
            raise TypeError("direct_time must be a real non-boolean number")
        time = float(direct_time)
        if not math.isfinite(time) or time < 0.0 or time > _TERMINAL_TIME:
            raise ValueError("direct_time must lie in [0, 1]")
        return _immutable_float_array(np.ones(_FROZEN_STATE_COUNT))


def _generator_grid(generator: np.ndarray, potential, times: np.ndarray) -> np.ndarray:
    return _immutable_float_array(
        np.stack(
            [
                potential_tilted_generator(generator, potential, float(time))
                for time in times
            ],
            axis=0,
        )
    )


def _reference_content_sha256(
    *,
    frozen_fixture_digest: str,
    fixture_content_digest: str,
    runtime: FiniteAssociationPathRuntime,
    observation_index: int,
    observation_mass: float,
    unconditional_path_kl: float,
    refined_unconditional_path_kl: float,
    unconditional_refinement_change: float,
    oracle_self_path_kl: float,
    target_marginal_maximum_absolute_error: float,
    target_initial_normalizer: float,
    target_initial_law: np.ndarray,
    target_generator_grid: np.ndarray,
    oracle_self_potential_evaluations: int,
    unconditional_potential_evaluations: int,
    refined_unconditional_potential_evaluations: int,
) -> str:
    # Elapsed CPU/wall measurements are deliberately excluded: they are
    # descriptive runner metadata and nondeterministic, whereas every value
    # capable of changing a path law or normalized score is content-bound.
    digest = hashlib.sha256()
    digest.update(b"heterodiff-a1-path-reference-v2\0")
    for value in (
        frozen_fixture_digest,
        fixture_content_digest,
        runtime.sha256,
        _solver_settings_sha256(PRIMARY_PATH_SOLVER_SETTINGS),
        _solver_settings_sha256(REFINED_PATH_SOLVER_SETTINGS),
        "reported-denominator:primary",
    ):
        _digest_text(digest, value)
    _digest_array(
        digest,
        np.asarray(
            (
                observation_mass,
                unconditional_path_kl,
                refined_unconditional_path_kl,
                unconditional_refinement_change,
                oracle_self_path_kl,
                target_marginal_maximum_absolute_error,
                target_initial_normalizer,
            ),
            dtype=np.float64,
        ),
    )
    _digest_array(
        digest,
        np.asarray(
            (
                observation_index,
                oracle_self_potential_evaluations,
                unconditional_potential_evaluations,
                refined_unconditional_potential_evaluations,
            ),
            dtype=np.int64,
        ),
    )
    _digest_array(digest, target_initial_law)
    _digest_array(digest, target_generator_grid)
    return digest.hexdigest()


@dataclass(frozen=True, eq=False)
class FrozenAssociationPathReference:
    """Reusable exact controls for one frozen observation."""

    frozen_fixture_sha256: str
    fixture_content_sha256: str
    runtime: FiniteAssociationPathRuntime
    reference_sha256: str
    observation_index: int
    observation_mass: float
    unconditional_path_kl: float
    refined_unconditional_path_kl: float
    primary_refined_unconditional_path_kl_change: float
    oracle_self_path_kl: float
    target_marginal_maximum_absolute_error: float
    target_initial_normalizer: float
    target_initial_law: np.ndarray
    target_generator_grid: np.ndarray
    primary_solver_settings: FiniteAssociationPathSolverSettings
    refined_solver_settings: FiniteAssociationPathSolverSettings
    oracle_self_potential_evaluations: int
    unconditional_potential_evaluations: int
    refined_unconditional_potential_evaluations: int
    elapsed_process_time_seconds: float
    elapsed_wall_time_seconds: float

    def __post_init__(self) -> None:
        fixture_digest = _sha256(
            self.frozen_fixture_sha256, name="frozen_fixture_sha256"
        )
        content_digest = _sha256(
            self.fixture_content_sha256, name="fixture_content_sha256"
        )
        reference_digest = _sha256(
            self.reference_sha256, name="reference_sha256"
        )
        if type(self.runtime) is not FiniteAssociationPathRuntime:
            raise TypeError("runtime must be a FiniteAssociationPathRuntime")
        index = _observation_index(self.observation_index)
        mass = _nonnegative(self.observation_mass, name="observation_mass")
        baseline = _nonnegative(
            self.unconditional_path_kl, name="unconditional_path_kl"
        )
        refined_baseline = _nonnegative(
            self.refined_unconditional_path_kl,
            name="refined_unconditional_path_kl",
        )
        baseline_change = _nonnegative(
            self.primary_refined_unconditional_path_kl_change,
            name="primary_refined_unconditional_path_kl_change",
        )
        oracle_self = _nonnegative(
            self.oracle_self_path_kl, name="oracle_self_path_kl"
        )
        target_error = _nonnegative(
            self.target_marginal_maximum_absolute_error,
            name="target_marginal_maximum_absolute_error",
        )
        normalizer = _nonnegative(
            self.target_initial_normalizer, name="target_initial_normalizer"
        )
        initial = _numeric_array(
            self.target_initial_law,
            name="target_initial_law",
            shape=(_FROZEN_STATE_COUNT,),
        )
        generators = _numeric_array(
            self.target_generator_grid,
            name="target_generator_grid",
            shape=(
                _FROZEN_TIME_COUNT,
                _FROZEN_STATE_COUNT,
                _FROZEN_STATE_COUNT,
            ),
        )
        if self.primary_solver_settings != PRIMARY_PATH_SOLVER_SETTINGS:
            raise ValueError("reference must record the frozen primary settings")
        if self.refined_solver_settings != REFINED_PATH_SOLVER_SETTINGS:
            raise ValueError("reference must record the frozen refined settings")
        self_evaluations = _positive_integer(
            self.oracle_self_potential_evaluations,
            name="oracle_self_potential_evaluations",
        )
        unconditional_evaluations = _positive_integer(
            self.unconditional_potential_evaluations,
            name="unconditional_potential_evaluations",
        )
        refined_unconditional_evaluations = _positive_integer(
            self.refined_unconditional_potential_evaluations,
            name="refined_unconditional_potential_evaluations",
        )
        process_time = _nonnegative(
            self.elapsed_process_time_seconds,
            name="elapsed_process_time_seconds",
        )
        wall_time = _nonnegative(
            self.elapsed_wall_time_seconds, name="elapsed_wall_time_seconds"
        )
        if mass <= 0.0:
            raise ValueError("observation_mass must be strictly positive")
        if baseline <= _UNCONDITIONAL_NORMALIZER_FLOOR:
            raise ArithmeticError(
                "unconditional path normalizer must exceed 1e-12; gate is HOLD"
            )
        if refined_baseline <= _UNCONDITIONAL_NORMALIZER_FLOOR:
            raise ArithmeticError(
                "refined unconditional path normalizer must exceed 1e-12; "
                "gate is HOLD"
            )
        expected_change = abs(baseline - refined_baseline)
        if not math.isclose(
            baseline_change,
            expected_change,
            rel_tol=2.0e-13,
            abs_tol=2.0e-14,
        ):
            raise ValueError("unconditional refinement change is inconsistent")
        if normalizer <= 0.0:
            raise ValueError("target_initial_normalizer must be strictly positive")
        if not math.isclose(
            math.fsum(float(value) for value in initial),
            1.0,
            rel_tol=0.0,
            abs_tol=2.0e-12,
        ) or np.any(initial < 0.0):
            raise ValueError("target_initial_law must be a probability vector")
        _validate_generator_grid(generators, name="target_generator_grid")
        expected_reference_digest = _reference_content_sha256(
            frozen_fixture_digest=fixture_digest,
            fixture_content_digest=content_digest,
            runtime=self.runtime,
            observation_index=index,
            observation_mass=mass,
            unconditional_path_kl=baseline,
            refined_unconditional_path_kl=refined_baseline,
            unconditional_refinement_change=baseline_change,
            oracle_self_path_kl=oracle_self,
            target_marginal_maximum_absolute_error=target_error,
            target_initial_normalizer=normalizer,
            target_initial_law=initial,
            target_generator_grid=generators,
            oracle_self_potential_evaluations=self_evaluations,
            unconditional_potential_evaluations=unconditional_evaluations,
            refined_unconditional_potential_evaluations=(
                refined_unconditional_evaluations
            ),
        )
        if reference_digest != expected_reference_digest:
            raise ValueError("reference SHA-256 does not match its content")
        object.__setattr__(self, "frozen_fixture_sha256", fixture_digest)
        object.__setattr__(self, "fixture_content_sha256", content_digest)
        object.__setattr__(self, "reference_sha256", reference_digest)
        object.__setattr__(self, "observation_index", index)
        object.__setattr__(self, "observation_mass", mass)
        object.__setattr__(self, "unconditional_path_kl", baseline)
        object.__setattr__(
            self, "refined_unconditional_path_kl", refined_baseline
        )
        object.__setattr__(
            self,
            "primary_refined_unconditional_path_kl_change",
            baseline_change,
        )
        object.__setattr__(self, "oracle_self_path_kl", oracle_self)
        object.__setattr__(
            self, "target_marginal_maximum_absolute_error", target_error
        )
        object.__setattr__(self, "target_initial_normalizer", normalizer)
        object.__setattr__(self, "target_initial_law", _immutable_float_array(initial))
        object.__setattr__(
            self, "target_generator_grid", _immutable_float_array(generators)
        )
        object.__setattr__(self, "elapsed_process_time_seconds", process_time)
        object.__setattr__(self, "elapsed_wall_time_seconds", wall_time)
        object.__setattr__(
            self, "oracle_self_potential_evaluations", self_evaluations
        )
        object.__setattr__(
            self,
            "unconditional_potential_evaluations",
            unconditional_evaluations,
        )
        object.__setattr__(
            self,
            "refined_unconditional_potential_evaluations",
            refined_unconditional_evaluations,
        )

    @property
    def numerical_gate_failures(self) -> Tuple[str, ...]:
        failures = []
        if self.oracle_self_path_kl > _ORACLE_SELF_PATH_KL_LIMIT:
            failures.append("oracle self path KL exceeds 1e-10 nat")
        if (
            self.primary_refined_unconditional_path_kl_change
            > _UNCONDITIONAL_REFINEMENT_LIMIT
        ):
            failures.append(
                "primary/refined unconditional path-KL change exceeds 1e-8 nat"
            )
        if (
            self.target_marginal_maximum_absolute_error
            > _TARGET_OCCUPANCY_ERROR_LIMIT
        ):
            failures.append("target occupancy error exceeds 1e-8")
        return tuple(failures)

    @property
    def numerical_gate_passed(self) -> bool:
        return len(self.numerical_gate_failures) == 0

    @property
    def oracle_self_gate_passed(self) -> bool:
        return self.oracle_self_path_kl <= _ORACLE_SELF_PATH_KL_LIMIT


def _reference_set_content_sha256(
    *,
    frozen_fixture_digest: str,
    fixture_content_digest: str,
    runtime: FiniteAssociationPathRuntime,
    references: Tuple[FrozenAssociationPathReference, ...],
) -> str:
    digest = hashlib.sha256()
    digest.update(b"heterodiff-a1-path-reference-set-v1\0")
    for value in (
        frozen_fixture_digest,
        fixture_content_digest,
        runtime.sha256,
        _solver_settings_sha256(PRIMARY_PATH_SOLVER_SETTINGS),
        _solver_settings_sha256(REFINED_PATH_SOLVER_SETTINGS),
        "reported-denominator:primary",
    ):
        _digest_text(digest, value)
    for reference in references:
        _digest_text(digest, reference.reference_sha256)
    return digest.hexdigest()


@dataclass(frozen=True, eq=False)
class FrozenAssociationPathReferenceSet:
    """Content-bound all-observation preflight required before candidate paths."""

    frozen_fixture_sha256: str
    fixture_content_sha256: str
    runtime: FiniteAssociationPathRuntime
    primary_solver_settings: FiniteAssociationPathSolverSettings
    refined_solver_settings: FiniteAssociationPathSolverSettings
    references: Tuple[FrozenAssociationPathReference, ...]
    reference_set_sha256: str

    def __post_init__(self) -> None:
        fixture_digest = _sha256(
            self.frozen_fixture_sha256, name="frozen_fixture_sha256"
        )
        content_digest = _sha256(
            self.fixture_content_sha256, name="fixture_content_sha256"
        )
        set_digest = _sha256(
            self.reference_set_sha256, name="reference_set_sha256"
        )
        if type(self.runtime) is not FiniteAssociationPathRuntime:
            raise TypeError("runtime must be a FiniteAssociationPathRuntime")
        if self.primary_solver_settings != PRIMARY_PATH_SOLVER_SETTINGS:
            raise ValueError("reference set has non-frozen primary settings")
        if self.refined_solver_settings != REFINED_PATH_SOLVER_SETTINGS:
            raise ValueError("reference set has non-frozen refined settings")
        if type(self.references) is not tuple or len(self.references) != 21:
            raise ValueError("reference set must contain all 21 observations")
        if not all(
            type(item) is FrozenAssociationPathReference
            for item in self.references
        ):
            raise TypeError("reference set contains an invalid record")
        if tuple(item.observation_index for item in self.references) != tuple(
            range(_FROZEN_OBSERVATION_COUNT)
        ):
            raise ValueError("reference set must use canonical observation order")
        for item in self.references:
            if (
                item.frozen_fixture_sha256 != fixture_digest
                or item.fixture_content_sha256 != content_digest
                or item.runtime != self.runtime
            ):
                raise ValueError("reference set mixes incompatible custody records")
        expected_digest = _reference_set_content_sha256(
            frozen_fixture_digest=fixture_digest,
            fixture_content_digest=content_digest,
            runtime=self.runtime,
            references=self.references,
        )
        if set_digest != expected_digest:
            raise ValueError("reference-set SHA-256 does not match its content")
        object.__setattr__(self, "frozen_fixture_sha256", fixture_digest)
        object.__setattr__(self, "fixture_content_sha256", content_digest)
        object.__setattr__(self, "reference_set_sha256", set_digest)

    @property
    def preflight_failures(self) -> Tuple[str, ...]:
        failures = []
        if not self.runtime.is_frozen_execution_runtime:
            failures.append(
                "path runtime does not match Python 3.11.5 / NumPy 2.4.6 / "
                "SciPy 1.17.1"
            )
        for reference in self.references:
            failures.extend(
                "observation %d: %s" % (reference.observation_index, message)
                for message in reference.numerical_gate_failures
            )
        return tuple(failures)

    @property
    def preflight_passed(self) -> bool:
        return len(self.preflight_failures) == 0

    def require_preflight_pass(self) -> None:
        if not self.preflight_passed:
            raise RuntimeError(
                "all-21 path reference preflight is HOLD: %s"
                % "; ".join(self.preflight_failures)
            )


@dataclass(frozen=True, eq=False)
class FiniteAssociationObservationPathEvaluation:
    """Path, occupancy, endpoint, and refinement diagnostics for one anchor."""

    parameter_sha256: str
    classifier_sha256: Optional[str]
    execution_receipt_sha256: Optional[str]
    campaign_sha256: Optional[str]
    production_bound: bool
    reference: FrozenAssociationPathReference
    candidate_initial_normalizer: float
    candidate_initial_law: np.ndarray
    candidate_generator_grid: np.ndarray
    target_marginals: np.ndarray
    candidate_marginals: np.ndarray
    target_integrated_occupation: np.ndarray
    candidate_integrated_occupation: np.ndarray
    marginal_total_variation: np.ndarray
    path_kl_initial: float
    path_kl_dynamic: float
    path_kl_total: float
    normalized_path_kl: float
    maximum_intermediate_total_variation: float
    endpoint_total_variation: float
    primary_refined_path_kl_change: float
    primary_refined_endpoint_total_variation: float
    primary_path_quadrature_error: float
    refined_path_quadrature_error: float
    primary_target_marginal_maximum_absolute_error: float
    primary_solver_settings: FiniteAssociationPathSolverSettings
    refined_solver_settings: FiniteAssociationPathSolverSettings
    primary_path_potential_evaluations: int
    refined_path_potential_evaluations: int
    primary_candidate_occupancy_potential_evaluations: int
    refined_candidate_occupancy_potential_evaluations: int
    elapsed_process_time_seconds: float
    elapsed_wall_time_seconds: float

    def __post_init__(self) -> None:
        parameter = _sha256(self.parameter_sha256, name="parameter_sha256")
        if type(self.production_bound) is not bool:
            raise TypeError("production_bound must be boolean")
        if self.production_bound:
            classifier = _sha256(
                self.classifier_sha256, name="classifier_sha256"
            )
            receipt = _sha256(
                self.execution_receipt_sha256,
                name="execution_receipt_sha256",
            )
            campaign = _sha256(self.campaign_sha256, name="campaign_sha256")
        elif self.classifier_sha256 is not None:
            raise ValueError("test-only path records cannot claim a classifier hash")
        elif self.execution_receipt_sha256 is not None:
            raise ValueError("test-only path records cannot claim execution custody")
        elif self.campaign_sha256 is not None:
            raise ValueError("test-only path records cannot claim campaign custody")
        else:
            classifier = None
            receipt = None
            campaign = None
        if type(self.reference) is not FrozenAssociationPathReference:
            raise TypeError("reference must be a FrozenAssociationPathReference")
        scalar_names = (
            "candidate_initial_normalizer",
            "path_kl_initial",
            "path_kl_dynamic",
            "path_kl_total",
            "normalized_path_kl",
            "maximum_intermediate_total_variation",
            "endpoint_total_variation",
            "primary_refined_path_kl_change",
            "primary_refined_endpoint_total_variation",
            "primary_path_quadrature_error",
            "refined_path_quadrature_error",
            "primary_target_marginal_maximum_absolute_error",
            "elapsed_process_time_seconds",
            "elapsed_wall_time_seconds",
        )
        scalars = {
            name: _nonnegative(getattr(self, name), name=name)
            for name in scalar_names
        }
        if scalars["candidate_initial_normalizer"] <= 0.0:
            raise ValueError("candidate_initial_normalizer must be positive")
        if self.primary_solver_settings != PRIMARY_PATH_SOLVER_SETTINGS:
            raise ValueError("primary solver settings are not frozen")
        if self.refined_solver_settings != REFINED_PATH_SOLVER_SETTINGS:
            raise ValueError("refined solver settings are not frozen")
        if not math.isclose(
            scalars["primary_target_marginal_maximum_absolute_error"],
            self.reference.target_marginal_maximum_absolute_error,
            rel_tol=2.0e-12,
            abs_tol=2.0e-14,
        ):
            raise ValueError("candidate call used an inconsistent target occupancy")
        integer_names = (
            "primary_path_potential_evaluations",
            "refined_path_potential_evaluations",
            "primary_candidate_occupancy_potential_evaluations",
            "refined_candidate_occupancy_potential_evaluations",
        )
        integers = {
            name: _positive_integer(getattr(self, name), name=name)
            for name in integer_names
        }
        if not math.isclose(
            scalars["path_kl_total"],
            scalars["path_kl_initial"] + scalars["path_kl_dynamic"],
            rel_tol=2.0e-12,
            abs_tol=2.0e-14,
        ):
            raise ValueError("path_kl_total is inconsistent with its components")
        expected_normalized = (
            scalars["path_kl_total"] / self.reference.unconditional_path_kl
        )
        if not math.isclose(
            scalars["normalized_path_kl"],
            expected_normalized,
            rel_tol=2.0e-12,
            abs_tol=2.0e-14,
        ):
            raise ValueError("normalized_path_kl uses the wrong normalizer")
        arrays = {
            "candidate_initial_law": _numeric_array(
                self.candidate_initial_law,
                name="candidate_initial_law",
                shape=(_FROZEN_STATE_COUNT,),
            ),
            "candidate_generator_grid": _numeric_array(
                self.candidate_generator_grid,
                name="candidate_generator_grid",
                shape=(
                    _FROZEN_TIME_COUNT,
                    _FROZEN_STATE_COUNT,
                    _FROZEN_STATE_COUNT,
                ),
            ),
            "target_marginals": _numeric_array(
                self.target_marginals,
                name="target_marginals",
                shape=(_FROZEN_TIME_COUNT, _FROZEN_STATE_COUNT),
            ),
            "candidate_marginals": _numeric_array(
                self.candidate_marginals,
                name="candidate_marginals",
                shape=(_FROZEN_TIME_COUNT, _FROZEN_STATE_COUNT),
            ),
            "target_integrated_occupation": _numeric_array(
                self.target_integrated_occupation,
                name="target_integrated_occupation",
                shape=(_FROZEN_STATE_COUNT,),
            ),
            "candidate_integrated_occupation": _numeric_array(
                self.candidate_integrated_occupation,
                name="candidate_integrated_occupation",
                shape=(_FROZEN_STATE_COUNT,),
            ),
            "marginal_total_variation": _numeric_array(
                self.marginal_total_variation,
                name="marginal_total_variation",
                shape=(_FROZEN_TIME_COUNT,),
            ),
        }
        for name in (
            "candidate_initial_law",
            "target_marginals",
            "candidate_marginals",
            "target_integrated_occupation",
            "candidate_integrated_occupation",
            "marginal_total_variation",
        ):
            if np.any(arrays[name] < 0.0):
                raise ValueError("%s must be nonnegative" % name)
        for name in ("target_marginals", "candidate_marginals"):
            if not np.allclose(
                np.sum(arrays[name], axis=1),
                1.0,
                atol=2.0e-10,
                rtol=0.0,
            ):
                raise ValueError("%s rows must be probability vectors" % name)
        if not math.isclose(
            math.fsum(float(value) for value in arrays["candidate_initial_law"]),
            1.0,
            rel_tol=0.0,
            abs_tol=2.0e-12,
        ):
            raise ValueError("candidate_initial_law must sum to one")
        _validate_generator_grid(
            arrays["candidate_generator_grid"], name="candidate_generator_grid"
        )
        if not np.allclose(
            arrays["candidate_marginals"][0],
            arrays["candidate_initial_law"],
            atol=2.0e-12,
            rtol=2.0e-12,
        ):
            raise ValueError("candidate occupancy does not start at its tilted law")
        if not np.allclose(
            arrays["target_marginals"][0],
            self.reference.target_initial_law,
            atol=2.0e-12,
            rtol=2.0e-12,
        ):
            raise ValueError("target occupancy does not start at its tilted law")
        for name in (
            "target_integrated_occupation",
            "candidate_integrated_occupation",
        ):
            if not math.isclose(
                math.fsum(float(value) for value in arrays[name]),
                _TERMINAL_TIME,
                rel_tol=0.0,
                abs_tol=2.0e-9,
            ):
                raise ValueError("%s does not sum to the horizon" % name)
        if not np.allclose(
            arrays["candidate_generator_grid"][-1],
            self.reference.target_generator_grid[-1],
            atol=2.0e-10,
            rtol=2.0e-10,
        ):
            raise ValueError("candidate generator fails the terminal boundary")
        expected_tv = np.asarray(
            [
                _total_variation(target, candidate)
                for target, candidate in zip(
                    arrays["target_marginals"], arrays["candidate_marginals"]
                )
            ],
            dtype=np.float64,
        )
        if not np.allclose(
            arrays["marginal_total_variation"],
            expected_tv,
            atol=2.0e-14,
            rtol=2.0e-13,
        ):
            raise ValueError("marginal_total_variation is inconsistent")
        if not math.isclose(
            scalars["maximum_intermediate_total_variation"],
            float(np.max(expected_tv[1:-1])),
            rel_tol=2.0e-13,
            abs_tol=2.0e-14,
        ):
            raise ValueError("maximum intermediate TV is inconsistent")
        if not math.isclose(
            scalars["endpoint_total_variation"],
            float(expected_tv[-1]),
            rel_tol=2.0e-13,
            abs_tol=2.0e-14,
        ):
            raise ValueError("endpoint TV is inconsistent")
        object.__setattr__(self, "parameter_sha256", parameter)
        object.__setattr__(self, "classifier_sha256", classifier)
        object.__setattr__(self, "execution_receipt_sha256", receipt)
        object.__setattr__(self, "campaign_sha256", campaign)
        for name, value in scalars.items():
            object.__setattr__(self, name, value)
        for name, value in integers.items():
            object.__setattr__(self, name, value)
        for name, value in arrays.items():
            object.__setattr__(self, name, _immutable_float_array(value))

    @property
    def observation_index(self) -> int:
        return self.reference.observation_index

    @property
    def unconditional_path_kl(self) -> float:
        return self.reference.unconditional_path_kl

    @property
    def oracle_self_path_kl(self) -> float:
        return self.reference.oracle_self_path_kl

    @property
    def target_endpoint(self) -> np.ndarray:
        return self.target_marginals[-1]

    @property
    def candidate_endpoint(self) -> np.ndarray:
        return self.candidate_marginals[-1]

    @property
    def initial_total_variation(self) -> float:
        return float(self.marginal_total_variation[0])

    @property
    def numerical_gate_failures(self) -> Tuple[str, ...]:
        failures = list(self.reference.numerical_gate_failures)
        if self.primary_refined_path_kl_change > _PATH_REFINEMENT_LIMIT:
            failures.append("primary/refined path-KL change exceeds 1e-8 nat")
        if (
            self.primary_refined_endpoint_total_variation
            > _ENDPOINT_REFINEMENT_LIMIT
        ):
            failures.append("primary/refined endpoint TV exceeds 1e-8")
        if (
            self.primary_target_marginal_maximum_absolute_error
            > _TARGET_OCCUPANCY_ERROR_LIMIT
            and "target occupancy error exceeds 1e-8" not in failures
        ):
            failures.append("target occupancy error exceeds 1e-8")
        return tuple(failures)

    @property
    def numerical_gate_passed(self) -> bool:
        return len(self.numerical_gate_failures) == 0


@dataclass(frozen=True, eq=False)
class FiniteAssociationPathEvaluation:
    """Complete canonical 21-observation A1 path evaluation and summaries."""

    parameter_sha256: str
    classifier_sha256: Optional[str]
    execution_receipt_sha256: Optional[str]
    campaign_sha256: Optional[str]
    production_bound: bool
    reference_set_sha256: str
    observations: Tuple[FiniteAssociationObservationPathEvaluation, ...]
    observation_mass: np.ndarray
    path_kl_per_observation: np.ndarray
    unconditional_path_kl_per_observation: np.ndarray
    normalized_path_kl_per_observation: np.ndarray
    endpoint_total_variation_per_observation: np.ndarray
    maximum_intermediate_total_variation_per_observation: np.ndarray
    observation_weighted_path_kl: float
    retained_path_kl_mean: float
    retained_normalized_path_score: float
    overflow_path_kl: float
    overflow_normalized_path_score: float
    observation_weighted_endpoint_total_variation: float
    retained_endpoint_total_variation_mean: float
    overflow_endpoint_total_variation: float
    ambiguous_observation_indices: np.ndarray
    ambiguous_normalized_path_kl: np.ndarray
    ambiguous_normalized_path_score: float
    reference_elapsed_process_time_seconds: float
    reference_elapsed_wall_time_seconds: float
    candidate_elapsed_process_time_seconds: float
    candidate_elapsed_wall_time_seconds: float
    numerical_gate_failures: Tuple[str, ...]

    def __post_init__(self) -> None:
        parameter = _sha256(self.parameter_sha256, name="parameter_sha256")
        if type(self.production_bound) is not bool:
            raise TypeError("production_bound must be boolean")
        if self.production_bound:
            classifier = _sha256(
                self.classifier_sha256, name="classifier_sha256"
            )
            receipt = _sha256(
                self.execution_receipt_sha256,
                name="execution_receipt_sha256",
            )
            campaign = _sha256(self.campaign_sha256, name="campaign_sha256")
        elif self.classifier_sha256 is not None:
            raise ValueError("test-only path summaries cannot claim a classifier hash")
        elif self.execution_receipt_sha256 is not None:
            raise ValueError("test-only path summaries cannot claim execution custody")
        elif self.campaign_sha256 is not None:
            raise ValueError("test-only path summaries cannot claim campaign custody")
        else:
            classifier = None
            receipt = None
            campaign = None
        reference_set_digest = _sha256(
            self.reference_set_sha256, name="reference_set_sha256"
        )
        if type(self.observations) is not tuple or len(self.observations) != 21:
            raise ValueError("observations must contain all 21 canonical records")
        if not all(
            type(item) is FiniteAssociationObservationPathEvaluation
            for item in self.observations
        ):
            raise TypeError("observations contains an invalid record")
        if tuple(item.observation_index for item in self.observations) != tuple(
            range(_FROZEN_OBSERVATION_COUNT)
        ):
            raise ValueError("observations must use canonical observation order")
        if any(item.parameter_sha256 != parameter for item in self.observations):
            raise ValueError("all observation records must use one checkpoint")
        if any(
            item.production_bound != self.production_bound
            or item.classifier_sha256 != classifier
            or item.execution_receipt_sha256 != receipt
            or item.campaign_sha256 != campaign
            for item in self.observations
        ):
            raise ValueError("observation records have inconsistent classifier custody")
        array_specs = (
            ("observation_mass", (_FROZEN_OBSERVATION_COUNT,)),
            ("path_kl_per_observation", (_FROZEN_OBSERVATION_COUNT,)),
            (
                "unconditional_path_kl_per_observation",
                (_FROZEN_OBSERVATION_COUNT,),
            ),
            ("normalized_path_kl_per_observation", (_FROZEN_OBSERVATION_COUNT,)),
            (
                "endpoint_total_variation_per_observation",
                (_FROZEN_OBSERVATION_COUNT,),
            ),
            (
                "maximum_intermediate_total_variation_per_observation",
                (_FROZEN_OBSERVATION_COUNT,),
            ),
            ("ambiguous_normalized_path_kl", (3,)),
        )
        arrays = {}
        for name, shape in array_specs:
            arrays[name] = _numeric_array(
                getattr(self, name), name=name, shape=shape
            )
            if np.any(arrays[name] < 0.0):
                raise ValueError("%s must be nonnegative" % name)
        try:
            ambiguous_raw = np.asarray(self.ambiguous_observation_indices)
            ambiguous_objects = np.asarray(
                self.ambiguous_observation_indices, dtype=object
            )
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(
                "ambiguous_observation_indices must be an integer vector"
            ) from error
        if any(
            isinstance(item, (bool, np.bool_)) for item in ambiguous_objects.flat
        ) or ambiguous_raw.dtype.kind not in "iu":
            raise TypeError("ambiguous_observation_indices must be integer")
        ambiguous_indices = ambiguous_raw.astype(np.int64, copy=True)
        if ambiguous_indices.shape != (3,) or np.any(ambiguous_indices < 0) or np.any(
            ambiguous_indices >= _FROZEN_OBSERVATION_COUNT
        ) or len(set(int(value) for value in ambiguous_indices)) != 3:
            raise ValueError("ambiguous_observation_indices is invalid")
        if not math.isclose(
            math.fsum(float(value) for value in arrays["observation_mass"]),
            1.0,
            rel_tol=0.0,
            abs_tol=2.0e-12,
        ) or np.any(arrays["observation_mass"] <= 0.0):
            raise ValueError("observation_mass must be a positive probability law")
        scalar_names = (
            "observation_weighted_path_kl",
            "retained_path_kl_mean",
            "retained_normalized_path_score",
            "overflow_path_kl",
            "overflow_normalized_path_score",
            "observation_weighted_endpoint_total_variation",
            "retained_endpoint_total_variation_mean",
            "overflow_endpoint_total_variation",
            "ambiguous_normalized_path_score",
            "reference_elapsed_process_time_seconds",
            "reference_elapsed_wall_time_seconds",
            "candidate_elapsed_process_time_seconds",
            "candidate_elapsed_wall_time_seconds",
        )
        scalars = {
            name: _nonnegative(getattr(self, name), name=name)
            for name in scalar_names
        }
        if type(self.numerical_gate_failures) is not tuple or not all(
            isinstance(item, str) and item for item in self.numerical_gate_failures
        ):
            raise TypeError("numerical_gate_failures must be a tuple of strings")
        if any(
            item.reference.frozen_fixture_sha256
            != frozen_association_fixture_sha256()
            for item in self.observations
        ):
            raise ValueError("an observation reference is not fixture-bound")
        first_reference = self.observations[0].reference
        if any(
            item.reference.fixture_content_sha256
            != first_reference.fixture_content_sha256
            or item.reference.runtime != first_reference.runtime
            for item in self.observations
        ):
            raise ValueError("result mixes incompatible path references")
        expected_set_digest = _reference_set_content_sha256(
            frozen_fixture_digest=first_reference.frozen_fixture_sha256,
            fixture_content_digest=first_reference.fixture_content_sha256,
            runtime=first_reference.runtime,
            references=tuple(item.reference for item in self.observations),
        )
        if reference_set_digest != expected_set_digest:
            raise ValueError("result has the wrong reference-set digest")
        expected_arrays = {
            "observation_mass": np.asarray(
                [item.reference.observation_mass for item in self.observations]
            ),
            "path_kl_per_observation": np.asarray(
                [item.path_kl_total for item in self.observations]
            ),
            "unconditional_path_kl_per_observation": np.asarray(
                [item.unconditional_path_kl for item in self.observations]
            ),
            "normalized_path_kl_per_observation": np.asarray(
                [item.normalized_path_kl for item in self.observations]
            ),
            "endpoint_total_variation_per_observation": np.asarray(
                [item.endpoint_total_variation for item in self.observations]
            ),
            "maximum_intermediate_total_variation_per_observation": np.asarray(
                [
                    item.maximum_intermediate_total_variation
                    for item in self.observations
                ]
            ),
        }
        for name, expected in expected_arrays.items():
            if not np.array_equal(arrays[name], expected):
                raise ValueError("%s is inconsistent with observation records" % name)
        if (
            tuple(int(value) for value in ambiguous_indices)
            != _AMBIGUOUS_OBSERVATION_INDICES
        ):
            raise ValueError("ambiguous observation indices are not frozen")
        if not np.array_equal(
            arrays["ambiguous_normalized_path_kl"],
            arrays["normalized_path_kl_per_observation"][ambiguous_indices],
        ):
            raise ValueError("ambiguous normalized path KL is inconsistent")

        mass = arrays["observation_mass"]
        path = arrays["path_kl_per_observation"]
        baseline = arrays["unconditional_path_kl_per_observation"]
        normalized = arrays["normalized_path_kl_per_observation"]
        endpoint = arrays["endpoint_total_variation_per_observation"]
        retained = np.ones(_FROZEN_OBSERVATION_COUNT, dtype=bool)
        retained[_OVERFLOW_INDEX] = False
        retained_mass = float(np.sum(mass[retained]))
        retained_path = float(mass[retained] @ path[retained])
        retained_baseline = float(mass[retained] @ baseline[retained])
        expected_scalars = {
            "observation_weighted_path_kl": float(mass @ path),
            "retained_path_kl_mean": retained_path / retained_mass,
            "retained_normalized_path_score": (
                retained_path / retained_baseline
            ),
            "overflow_path_kl": float(path[_OVERFLOW_INDEX]),
            "overflow_normalized_path_score": float(
                normalized[_OVERFLOW_INDEX]
            ),
            "observation_weighted_endpoint_total_variation": float(
                mass @ endpoint
            ),
            "retained_endpoint_total_variation_mean": float(
                mass[retained] @ endpoint[retained]
            )
            / retained_mass,
            "overflow_endpoint_total_variation": float(
                endpoint[_OVERFLOW_INDEX]
            ),
            "ambiguous_normalized_path_score": float(
                np.mean(normalized[ambiguous_indices])
            ),
            "reference_elapsed_process_time_seconds": math.fsum(
                item.reference.elapsed_process_time_seconds
                for item in self.observations
            ),
            "reference_elapsed_wall_time_seconds": math.fsum(
                item.reference.elapsed_wall_time_seconds
                for item in self.observations
            ),
            "candidate_elapsed_process_time_seconds": math.fsum(
                item.elapsed_process_time_seconds for item in self.observations
            ),
            "candidate_elapsed_wall_time_seconds": math.fsum(
                item.elapsed_wall_time_seconds for item in self.observations
            ),
        }
        for name, expected in expected_scalars.items():
            if not math.isclose(
                scalars[name], expected, rel_tol=2.0e-13, abs_tol=2.0e-14
            ):
                raise ValueError("%s is inconsistent with observation records" % name)
        expected_failures = []
        for item in self.observations:
            expected_failures.extend(
                "observation %d: %s" % (item.observation_index, message)
                for message in item.numerical_gate_failures
            )
        if self.numerical_gate_failures != tuple(expected_failures):
            raise ValueError("numerical gate failures are incomplete or inconsistent")
        object.__setattr__(self, "parameter_sha256", parameter)
        object.__setattr__(self, "classifier_sha256", classifier)
        object.__setattr__(self, "execution_receipt_sha256", receipt)
        object.__setattr__(self, "campaign_sha256", campaign)
        object.__setattr__(self, "reference_set_sha256", reference_set_digest)
        for name, value in arrays.items():
            object.__setattr__(self, name, _immutable_float_array(value))
        object.__setattr__(
            self,
            "ambiguous_observation_indices",
            _immutable_int_array(ambiguous_indices),
        )
        for name, value in scalars.items():
            object.__setattr__(self, name, value)

    @property
    def numerical_gate_passed(self) -> bool:
        return len(self.numerical_gate_failures) == 0


def build_frozen_association_path_reference(
    fixture: FrozenAssociationResidualFixture,
    observation_index: object,
) -> FrozenAssociationPathReference:
    """Compute reusable unconditional and oracle-self controls for one anchor."""

    checked_fixture = _validate_fixture(fixture)
    index = _observation_index(observation_index)
    initial = checked_fixture.initial_marginal
    generator = checked_fixture.oracle.generator
    times = checked_fixture.times
    process_start = time_module.process_time()
    wall_start = time_module.perf_counter()

    # These are intentionally distinct numerical calls.  The self path is a
    # numerical null diagnostic; the unit potential is the ordinary,
    # unconditional base path and supplies the frozen normalization.
    self_path = _path_call(
        initial,
        generator,
        _ExactObservationPotential(checked_fixture, index),
        _ExactObservationPotential(checked_fixture, index),
        times,
        refined=False,
    )
    unconditional = _path_call(
        initial,
        generator,
        _ExactObservationPotential(checked_fixture, index),
        _UnitPotential(),
        times,
        refined=False,
    )
    refined_unconditional = _path_call(
        initial,
        generator,
        _ExactObservationPotential(checked_fixture, index),
        _UnitPotential(),
        times,
        refined=True,
    )
    exact_for_grid = _ExactObservationPotential(checked_fixture, index)
    target_generator_grid = _generator_grid(generator, exact_for_grid, times)
    target_error = float(
        np.max(
            np.abs(
                self_path.occupancy.marginals
                - checked_fixture.population.conditional_time[:, :, index]
            )
        )
    )
    fixture_digest = frozen_association_fixture_sha256()
    content_digest = finite_association_path_fixture_content_sha256(
        checked_fixture
    )
    runtime = FiniteAssociationPathRuntime.current()
    baseline_change = abs(unconditional.total - refined_unconditional.total)
    observation_mass = float(
        checked_fixture.population.observation_marginal_mass[index]
    )
    reference_digest = _reference_content_sha256(
        frozen_fixture_digest=fixture_digest,
        fixture_content_digest=content_digest,
        runtime=runtime,
        observation_index=index,
        observation_mass=observation_mass,
        unconditional_path_kl=unconditional.total,
        refined_unconditional_path_kl=refined_unconditional.total,
        unconditional_refinement_change=baseline_change,
        oracle_self_path_kl=self_path.total,
        target_marginal_maximum_absolute_error=target_error,
        target_initial_normalizer=self_path.reference_initial.normalizer,
        target_initial_law=self_path.reference_initial.probabilities,
        target_generator_grid=target_generator_grid,
        oracle_self_potential_evaluations=self_path.potential_evaluations,
        unconditional_potential_evaluations=(
            unconditional.potential_evaluations
        ),
        refined_unconditional_potential_evaluations=(
            refined_unconditional.potential_evaluations
        ),
    )
    elapsed_process = time_module.process_time() - process_start
    elapsed_wall = time_module.perf_counter() - wall_start
    return FrozenAssociationPathReference(
        frozen_fixture_sha256=fixture_digest,
        fixture_content_sha256=content_digest,
        runtime=runtime,
        reference_sha256=reference_digest,
        observation_index=index,
        observation_mass=observation_mass,
        unconditional_path_kl=unconditional.total,
        refined_unconditional_path_kl=refined_unconditional.total,
        primary_refined_unconditional_path_kl_change=baseline_change,
        oracle_self_path_kl=self_path.total,
        target_marginal_maximum_absolute_error=target_error,
        target_initial_normalizer=self_path.reference_initial.normalizer,
        target_initial_law=self_path.reference_initial.probabilities,
        target_generator_grid=target_generator_grid,
        primary_solver_settings=PRIMARY_PATH_SOLVER_SETTINGS,
        refined_solver_settings=REFINED_PATH_SOLVER_SETTINGS,
        oracle_self_potential_evaluations=self_path.potential_evaluations,
        unconditional_potential_evaluations=(
            unconditional.potential_evaluations
        ),
        refined_unconditional_potential_evaluations=(
            refined_unconditional.potential_evaluations
        ),
        elapsed_process_time_seconds=elapsed_process,
        elapsed_wall_time_seconds=elapsed_wall,
    )


def build_frozen_association_path_references(
    fixture: FrozenAssociationResidualFixture,
) -> FrozenAssociationPathReferenceSet:
    """Build and content-bind the all-21 canonical reference preflight."""

    checked_fixture = _validate_fixture(fixture)
    references = tuple(
        build_frozen_association_path_reference(checked_fixture, index)
        for index in range(_FROZEN_OBSERVATION_COUNT)
    )
    fixture_digest = frozen_association_fixture_sha256()
    content_digest = finite_association_path_fixture_content_sha256(
        checked_fixture
    )
    runtime = FiniteAssociationPathRuntime.current()
    set_digest = _reference_set_content_sha256(
        frozen_fixture_digest=fixture_digest,
        fixture_content_digest=content_digest,
        runtime=runtime,
        references=references,
    )
    return FrozenAssociationPathReferenceSet(
        frozen_fixture_sha256=fixture_digest,
        fixture_content_sha256=content_digest,
        runtime=runtime,
        primary_solver_settings=PRIMARY_PATH_SOLVER_SETTINGS,
        refined_solver_settings=REFINED_PATH_SOLVER_SETTINGS,
        references=references,
        reference_set_sha256=set_digest,
    )


def _evaluate_finite_association_observation_path(
    evaluator: CertifiedFiniteAssociationLogitEvaluator,
    fixture: FrozenAssociationResidualFixture,
    observation_index: object,
    *,
    reference_set: FrozenAssociationPathReferenceSet,
) -> FiniteAssociationObservationPathEvaluation:
    """Internal evaluator entered only after all-21 preflight and integrity."""

    if type(evaluator) is not CertifiedFiniteAssociationLogitEvaluator:
        raise TypeError("evaluator must be certificate-bound")
    checked_fixture = _validate_fixture(fixture)
    if (
        evaluator.certification.frozen_fixture_sha256
        != frozen_association_fixture_sha256()
    ):
        raise ValueError("evaluator is not bound to the frozen A1 fixture")
    index = _observation_index(observation_index)
    if type(reference_set) is not FrozenAssociationPathReferenceSet:
        raise TypeError("reference_set must be all-21 content-bound preflight")
    checked_reference = reference_set.references[index]

    initial = checked_fixture.initial_marginal
    generator = checked_fixture.oracle.generator
    times = checked_fixture.times
    process_start = time_module.process_time()
    wall_start = time_module.perf_counter()

    # Constructing each adapter also enforces the exact terminal boundary.  No
    # primary solve, refined solve, or occupancy propagation is reused.
    primary_path = _path_call(
        initial,
        generator,
        _ExactObservationPotential(checked_fixture, index),
        CertifiedFiniteAssociationPotentialAdapter(
            evaluator, checked_fixture, index
        ),
        times,
        refined=False,
    )
    primary_candidate_occupancy = _occupancy_call(
        initial,
        generator,
        CertifiedFiniteAssociationPotentialAdapter(
            evaluator, checked_fixture, index
        ),
        times,
        refined=False,
    )
    refined_path = _path_call(
        initial,
        generator,
        _ExactObservationPotential(checked_fixture, index),
        CertifiedFiniteAssociationPotentialAdapter(
            evaluator, checked_fixture, index
        ),
        times,
        refined=True,
    )
    refined_candidate_occupancy = _occupancy_call(
        initial,
        generator,
        CertifiedFiniteAssociationPotentialAdapter(
            evaluator, checked_fixture, index
        ),
        times,
        refined=True,
    )
    candidate_for_grid = CertifiedFiniteAssociationPotentialAdapter(
        evaluator, checked_fixture, index
    )

    if not np.allclose(
        primary_path.candidate_initial.probabilities,
        primary_candidate_occupancy.initial_law.probabilities,
        atol=2.0e-13,
        rtol=2.0e-13,
    ):
        raise ArithmeticError(
            "independent candidate integrations disagree on the tilted initial law"
        )
    propagated_target_marginals = primary_path.occupancy.marginals
    target_marginals = np.asarray(
        checked_fixture.population.conditional_time[:, :, index],
        dtype=np.float64,
    )
    candidate_marginals = primary_candidate_occupancy.marginals
    total_variation = np.asarray(
        [
            _total_variation(target, candidate)
            for target, candidate in zip(target_marginals, candidate_marginals)
        ],
        dtype=np.float64,
    )
    path_change = abs(primary_path.total - refined_path.total)
    endpoint_change = _total_variation(
        primary_candidate_occupancy.marginals[-1],
        refined_candidate_occupancy.marginals[-1],
    )
    normalized = primary_path.total / checked_reference.unconditional_path_kl
    candidate_generator_grid = _generator_grid(
        generator, candidate_for_grid, times
    )
    elapsed_process = time_module.process_time() - process_start
    elapsed_wall = time_module.perf_counter() - wall_start

    return FiniteAssociationObservationPathEvaluation(
        parameter_sha256=evaluator.certification.parameter_sha256,
        classifier_sha256=evaluator.classifier_sha256,
        execution_receipt_sha256=evaluator.execution_receipt_sha256,
        campaign_sha256=evaluator.campaign_sha256,
        production_bound=evaluator.production_bound,
        reference=checked_reference,
        candidate_initial_normalizer=primary_path.candidate_initial.normalizer,
        candidate_initial_law=primary_path.candidate_initial.probabilities,
        candidate_generator_grid=candidate_generator_grid,
        target_marginals=target_marginals,
        candidate_marginals=candidate_marginals,
        target_integrated_occupation=(
            primary_path.occupancy.integrated_occupation
        ),
        candidate_integrated_occupation=(
            primary_candidate_occupancy.integrated_occupation
        ),
        marginal_total_variation=total_variation,
        path_kl_initial=primary_path.initial,
        path_kl_dynamic=primary_path.dynamic,
        path_kl_total=primary_path.total,
        normalized_path_kl=normalized,
        maximum_intermediate_total_variation=float(
            np.max(total_variation[1:-1])
        ),
        endpoint_total_variation=float(total_variation[-1]),
        primary_refined_path_kl_change=path_change,
        primary_refined_endpoint_total_variation=endpoint_change,
        primary_path_quadrature_error=primary_path.quadrature_error,
        refined_path_quadrature_error=refined_path.quadrature_error,
        primary_target_marginal_maximum_absolute_error=float(
            np.max(np.abs(propagated_target_marginals - target_marginals))
        ),
        primary_solver_settings=PRIMARY_PATH_SOLVER_SETTINGS,
        refined_solver_settings=REFINED_PATH_SOLVER_SETTINGS,
        primary_path_potential_evaluations=(
            primary_path.potential_evaluations
        ),
        refined_path_potential_evaluations=(
            refined_path.potential_evaluations
        ),
        primary_candidate_occupancy_potential_evaluations=(
            primary_candidate_occupancy.potential_evaluations
        ),
        refined_candidate_occupancy_potential_evaluations=(
            refined_candidate_occupancy.potential_evaluations
        ),
        elapsed_process_time_seconds=elapsed_process,
        elapsed_wall_time_seconds=elapsed_wall,
    )


def _require_matching_reference_set(
    fixture: FrozenAssociationResidualFixture,
    reference_set: object,
) -> FrozenAssociationPathReferenceSet:
    if type(reference_set) is not FrozenAssociationPathReferenceSet:
        raise TypeError("reference_set must be all-21 content-bound preflight")
    if reference_set.frozen_fixture_sha256 != frozen_association_fixture_sha256():
        raise ValueError("reference set has the wrong frozen fixture token")
    actual_content = finite_association_path_fixture_content_sha256(fixture)
    if reference_set.fixture_content_sha256 != actual_content:
        raise ValueError("reference set does not match actual fixture content")
    if reference_set.runtime != FiniteAssociationPathRuntime.current():
        raise ValueError("reference set was built under a different runtime")
    reference_set.require_preflight_pass()
    return reference_set


def evaluate_finite_association_observation_path(
    evaluator: CertifiedFiniteAssociationLogitEvaluator,
    fixture: FrozenAssociationResidualFixture,
    observation_index: object,
    *,
    reference_set: FrozenAssociationPathReferenceSet,
    test_only: bool = False,
) -> FiniteAssociationObservationPathEvaluation:
    """Evaluate one anchor after the complete reference preflight passes.

    ``test_only=True`` is accepted only for an explicitly test-bound evaluator
    and prevents synthetic/oracle callbacks from masquerading as learned
    results.  Production checkpoint integrity is checked exactly once before
    and once after this top-level evaluation, never inside adaptive callbacks.
    """

    if type(evaluator) is not CertifiedFiniteAssociationLogitEvaluator:
        raise TypeError("evaluator must be certificate-bound")
    if type(test_only) is not bool:
        raise TypeError("test_only must be boolean")
    if evaluator.production_bound == test_only:
        raise ValueError(
            "production evaluators require test_only=False and test-only "
            "evaluators require test_only=True"
        )
    checked_fixture = _validate_fixture(fixture)
    checked_set = _require_matching_reference_set(
        checked_fixture, reference_set
    )
    evaluator.assert_integrity()
    try:
        result = _evaluate_finite_association_observation_path(
            evaluator,
            checked_fixture,
            observation_index,
            reference_set=checked_set,
        )
    finally:
        evaluator.assert_integrity()
    return result


def summarize_finite_association_paths(
    observations: Sequence[FiniteAssociationObservationPathEvaluation],
    fixture: FrozenAssociationResidualFixture,
) -> FiniteAssociationPathEvaluation:
    """Aggregate all canonical records using physical observation masses."""

    checked_fixture = _validate_fixture(fixture)
    records = tuple(observations)
    if len(records) != _FROZEN_OBSERVATION_COUNT:
        raise ValueError("all 21 observation records are required")
    if not all(
        type(item) is FiniteAssociationObservationPathEvaluation
        for item in records
    ):
        raise TypeError("observations contains an invalid record")
    if tuple(item.observation_index for item in records) != tuple(
        range(_FROZEN_OBSERVATION_COUNT)
    ):
        raise ValueError("observation records must be in canonical order")
    parameter = records[0].parameter_sha256
    if any(item.parameter_sha256 != parameter for item in records):
        raise ValueError("observation records come from different checkpoints")

    mass = np.asarray(
        checked_fixture.population.observation_marginal_mass, dtype=np.float64
    )
    path = np.asarray([item.path_kl_total for item in records], dtype=np.float64)
    baseline = np.asarray(
        [item.unconditional_path_kl for item in records], dtype=np.float64
    )
    normalized = path / baseline
    endpoint = np.asarray(
        [item.endpoint_total_variation for item in records], dtype=np.float64
    )
    intermediate = np.asarray(
        [
            item.maximum_intermediate_total_variation
            for item in records
        ],
        dtype=np.float64,
    )
    overflow = checked_fixture.observation.overflow_index
    retained = np.ones(_FROZEN_OBSERVATION_COUNT, dtype=bool)
    retained[overflow] = False
    retained_mass = math.fsum(float(value) for value in mass[retained])
    retained_path_numerator = float(mass[retained] @ path[retained])
    retained_baseline = float(mass[retained] @ baseline[retained])
    if retained_baseline <= _UNCONDITIONAL_NORMALIZER_FLOOR:
        raise ArithmeticError(
            "retained unconditional path normalizer must exceed 1e-12; "
            "gate is HOLD"
        )
    ambiguous = np.asarray(
        [
            checked_fixture.observation.index_of_observation(observation)
            for observation in _AMBIGUOUS_OBSERVATIONS
        ],
        dtype=np.int64,
    )
    failures = []
    for item in records:
        failures.extend(
            "observation %d: %s" % (item.observation_index, message)
            for message in item.numerical_gate_failures
        )

    return FiniteAssociationPathEvaluation(
        parameter_sha256=parameter,
        classifier_sha256=records[0].classifier_sha256,
        execution_receipt_sha256=records[0].execution_receipt_sha256,
        campaign_sha256=records[0].campaign_sha256,
        production_bound=records[0].production_bound,
        reference_set_sha256=_reference_set_content_sha256(
            frozen_fixture_digest=records[0].reference.frozen_fixture_sha256,
            fixture_content_digest=records[0].reference.fixture_content_sha256,
            runtime=records[0].reference.runtime,
            references=tuple(item.reference for item in records),
        ),
        observations=records,
        observation_mass=mass,
        path_kl_per_observation=path,
        unconditional_path_kl_per_observation=baseline,
        normalized_path_kl_per_observation=normalized,
        endpoint_total_variation_per_observation=endpoint,
        maximum_intermediate_total_variation_per_observation=intermediate,
        observation_weighted_path_kl=float(mass @ path),
        retained_path_kl_mean=retained_path_numerator / retained_mass,
        retained_normalized_path_score=(
            retained_path_numerator / retained_baseline
        ),
        overflow_path_kl=float(path[overflow]),
        overflow_normalized_path_score=float(normalized[overflow]),
        observation_weighted_endpoint_total_variation=float(mass @ endpoint),
        retained_endpoint_total_variation_mean=(
            float(mass[retained] @ endpoint[retained]) / retained_mass
        ),
        overflow_endpoint_total_variation=float(endpoint[overflow]),
        ambiguous_observation_indices=ambiguous,
        ambiguous_normalized_path_kl=normalized[ambiguous],
        ambiguous_normalized_path_score=float(np.mean(normalized[ambiguous])),
        reference_elapsed_process_time_seconds=math.fsum(
            item.reference.elapsed_process_time_seconds for item in records
        ),
        reference_elapsed_wall_time_seconds=math.fsum(
            item.reference.elapsed_wall_time_seconds for item in records
        ),
        candidate_elapsed_process_time_seconds=math.fsum(
            item.elapsed_process_time_seconds for item in records
        ),
        candidate_elapsed_wall_time_seconds=math.fsum(
            item.elapsed_wall_time_seconds for item in records
        ),
        numerical_gate_failures=tuple(failures),
    )


def evaluate_finite_association_paths(
    evaluator: CertifiedFiniteAssociationLogitEvaluator,
    fixture: FrozenAssociationResidualFixture,
    *,
    reference_set: Optional[FrozenAssociationPathReferenceSet] = None,
    test_only: bool = False,
) -> FiniteAssociationPathEvaluation:
    """Run and summarize the complete frozen 21-observation path evaluator."""

    if type(evaluator) is not CertifiedFiniteAssociationLogitEvaluator:
        raise TypeError("evaluator must be certificate-bound")
    if type(test_only) is not bool:
        raise TypeError("test_only must be boolean")
    if evaluator.production_bound == test_only:
        raise ValueError(
            "production evaluators require test_only=False and test-only "
            "evaluators require test_only=True"
        )
    checked_fixture = _validate_fixture(fixture)
    if reference_set is None:
        built_set = build_frozen_association_path_references(
            checked_fixture
        )
    else:
        built_set = reference_set
    checked_set = _require_matching_reference_set(checked_fixture, built_set)
    evaluator.assert_integrity()
    try:
        records = tuple(
            _evaluate_finite_association_observation_path(
                evaluator,
                checked_fixture,
                index,
                reference_set=checked_set,
            )
            for index in range(_FROZEN_OBSERVATION_COUNT)
        )
        result = summarize_finite_association_paths(records, checked_fixture)
    finally:
        evaluator.assert_integrity()
    return result


__all__ = [
    "FiniteAssociationObservationPathEvaluation",
    "FiniteAssociationPathEvaluation",
    "FiniteAssociationPathRuntime",
    "FiniteAssociationPathSolverSettings",
    "FrozenAssociationPathReference",
    "FrozenAssociationPathReferenceSet",
    "PRIMARY_PATH_SOLVER_SETTINGS",
    "REFINED_PATH_SOLVER_SETTINGS",
    "build_frozen_association_path_reference",
    "build_frozen_association_path_references",
    "evaluate_finite_association_observation_path",
    "evaluate_finite_association_paths",
    "finite_association_path_fixture_content_sha256",
    "summarize_finite_association_paths",
]
