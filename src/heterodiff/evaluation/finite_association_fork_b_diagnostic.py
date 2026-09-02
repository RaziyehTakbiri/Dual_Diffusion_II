"""Finite-A1 family-resolved component diagnostic for C17 Fork B.

This evaluator deliberately stops at the largest component supported by the
live finite association fixture.  It evaluates all 21 observations under the
exact finite target semigroup, partitions the numerical target-first path KL
into initializer, birth, death, and replacement contributions, and repeats
the computation under the frozen primary/refined numerical controls.

There are no continuous coordinates or occurrence-attached marks in this
fixture.  Consequently ``K_C`` is explicitly not applicable, rather than
reported as a measured zero.  Adaptive arithmetic is not an interval proof,
and a coherent return remains a ``PARTIAL_COMPONENT_DIAGNOSTIC`` with no C17,
R2, execution, or claim-promotion effect.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from numbers import Integral, Real
from typing import Optional, Tuple

import numpy as np

from heterodiff.evaluation.finite_association_path_evaluator import (
    FiniteAssociationPathRuntime,
    FiniteAssociationPathSolverSettings,
    PRIMARY_PATH_SOLVER_SETTINGS,
    REFINED_PATH_SOLVER_SETTINGS,
    finite_association_path_fixture_content_sha256,
)
from heterodiff.evaluation.finite_association_residual_evaluator import (
    CertifiedFiniteAssociationLogitEvaluator,
)
from heterodiff.experiments.finite_association_guided_residual_pilot import (
    FrozenAssociationResidualFixture,
    frozen_association_fixture_content_digests,
    frozen_association_fixture_sha256,
)
from heterodiff.theory.finite_bridge_family_path_control import (
    FINITE_BRIDGE_JUMP_FAMILY_ORDER,
    FiniteBridgeFamilyPathKL,
    tilted_path_kl_by_edge_family,
)
from heterodiff.theory.finite_bridge_path_control import tilted_path_kl


FINITE_ASSOCIATION_FORK_B_SCOPE = "FINITE_A1_CAPPED_ASSOCIATION_PATH_COMPONENTS_ONLY"
FINITE_ASSOCIATION_FORK_B_STATUS = "PARTIAL_COMPONENT_DIAGNOSTIC"
FINITE_ASSOCIATION_FORK_B_ORIENTATION = "KL(P_EXACT_TARGET_H || P_CANDIDATE_H_HAT)"
FINITE_ASSOCIATION_FORK_B_CONTINUOUS_COMPONENT_DISPOSITION = (
    "NOT_APPLICABLE_NO_CONTINUOUS_COORDINATES"
)
_TERMINAL_TIME = 1.0
_STATE_COUNT = 20
_OBSERVATION_COUNT = 21
_TARGET_MARGINAL_TOLERANCE = 1.0e-8
_TERMINAL_TOLERANCE = 1.0e-10
_REFINEMENT_TOLERANCE = 1.0e-8
_AGGREGATE_CROSSCHECK_TOLERANCE = 1.0e-8
_PHYSICAL_LOG_INFORMATION_LIMIT = 24.0
_LOCAL_COMPATIBILITY_FIXTURE_SHA256 = (
    "b96901980055f5ecfda653373ed935010040698985e274e0ebd3f04822f3e75d"
)
_PREREGISTERED_PRODUCTION_FIXTURE_SHA256 = (
    "0121b487728b40356de6707a33ba4881100c3d1b587259b19723463a60cecdcc"
)
_LOCAL_COMPATIBILITY_PATH_CONTENT_SHA256 = (
    "d269e5849a5b820605bafbb33f36c3c666f6e08ffa92c557212a6874c2ba3831"
)
_CANONICAL_COUNT_ORDER = (
    (0, 0, 0),
    (0, 0, 1),
    (0, 1, 0),
    (1, 0, 0),
    (0, 0, 2),
    (0, 1, 1),
    (0, 2, 0),
    (1, 0, 1),
    (1, 1, 0),
    (2, 0, 0),
    (0, 0, 3),
    (0, 1, 2),
    (0, 2, 1),
    (0, 3, 0),
    (1, 0, 2),
    (1, 1, 1),
    (1, 2, 0),
    (2, 0, 1),
    (2, 1, 0),
    (3, 0, 0),
)
_COMPONENT_ORDER = (
    "K0_NORMALIZED_INITIALIZER",
    "KC_CONTINUOUS_COORDINATES",
    "K_PLUS_BIRTH",
    "K_MINUS_DEATH",
    "K_R_REPLACEMENT",
)
_TARGET_INITIAL_MEASURE = "EXACT_CONDITIONED_TARGET_INITIAL_LAW"
_TARGET_OCCUPATION_MEASURE = "EXACT_CONDITIONED_TARGET_OCCUPATION"


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    contiguous = np.array(array, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=np.float64).reshape(
        contiguous.shape
    )


def _immutable_int_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.int64)
    contiguous = np.array(array, dtype=np.int64, copy=True, order="C")
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=np.int64).reshape(
        contiguous.shape
    )


def _nonnegative(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError("%s must be finite and nonnegative" % name)
    return result


def _sha256(value: object, *, name: str) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError("%s must be a 64-character SHA-256 digest" % name)
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError("%s must be lowercase hexadecimal" % name) from error
    if value != value.lower():
        raise ValueError("%s must be lowercase hexadecimal" % name)
    return value


def _optional_sha256(value: object, *, name: str) -> Optional[str]:
    if value is None:
        return None
    return _sha256(value, name=name)


def _validate_fixture(fixture: object) -> FrozenAssociationResidualFixture:
    if type(fixture) is not FrozenAssociationResidualFixture:
        raise TypeError("fixture must be the exact frozen A1 fixture record")
    expected = (33, _STATE_COUNT, _OBSERVATION_COUNT)
    if fixture.population.conditional_time.shape != expected:
        raise ValueError("fixture must contain the frozen 33 x 20 x 21 population")
    if fixture.times[0] != 0.0 or fixture.times[-1] != _TERMINAL_TIME:
        raise ValueError("fixture must use direct time [0, 1]")
    if tuple(fixture.latent_space.states) != _CANONICAL_COUNT_ORDER:
        raise ValueError("fixture latent states are not in canonical order")
    if tuple(fixture.retained_observation_space.states) != _CANONICAL_COUNT_ORDER:
        raise ValueError("fixture retained observations are not in canonical order")
    if tuple(fixture.observation.observations[:-1]) != _CANONICAL_COUNT_ORDER:
        raise ValueError("fixture observations are not in canonical order")
    if fixture.observation.overflow_index != 20:
        raise ValueError("fixture overflow observation must remain index 20")
    if fixture.observation.contamination_probability != 0.08:
        raise ValueError("fixture contamination probability must remain 0.08")
    if np.array_equal(
        fixture.observation.kernel_mass,
        fixture.observation.clean_kernel_mass,
    ):
        raise ValueError("fixture must retain the contaminated observation law")
    actual_fixture = frozen_association_fixture_sha256(
        frozen_association_fixture_content_digests(fixture)
    )
    if actual_fixture != _LOCAL_COMPATIBILITY_FIXTURE_SHA256:
        raise ValueError("fixture content token is not the local compatibility token")
    actual_path_content = finite_association_path_fixture_content_sha256(fixture)
    if actual_path_content != _LOCAL_COMPATIBILITY_PATH_CONTENT_SHA256:
        raise ValueError("fixture path content is not the local compatibility content")
    return fixture


class _ExactObservationPotential:
    def __init__(
        self, fixture: FrozenAssociationResidualFixture, observation_index: int
    ) -> None:
        self._oracle = fixture.oracle
        self._observation = fixture.observation.observation_at(observation_index)
        self._cache = {}

    def __call__(self, direct_time: object) -> np.ndarray:
        if isinstance(direct_time, (bool, np.bool_)) or not isinstance(
            direct_time, Real
        ):
            raise TypeError("direct_time must be a real non-boolean number")
        time = float(direct_time)
        if not math.isfinite(time) or time < 0.0 or time > _TERMINAL_TIME:
            raise ValueError("direct_time must lie in [0, 1]")
        if time not in self._cache:
            remaining = _TERMINAL_TIME - time
            tolerance = 32.0 * np.finfo(np.float64).eps
            if remaining < 0.0 and remaining >= -tolerance:
                remaining = 0.0
            self._cache[time] = _immutable_float_array(
                self._oracle.backward_information(remaining, self._observation)
            )
        return self._cache[time]


class _ExactTargetMarginal:
    """Direct finite-semigroup target marginal, independent of an ODE solve."""

    def __init__(
        self,
        fixture: FrozenAssociationResidualFixture,
        potential: _ExactObservationPotential,
    ) -> None:
        self._fixture = fixture
        self._potential = potential
        self._cache = {}

    def __call__(self, direct_time: object) -> np.ndarray:
        if isinstance(direct_time, (bool, np.bool_)) or not isinstance(
            direct_time, Real
        ):
            raise TypeError("direct_time must be a real non-boolean number")
        time = float(direct_time)
        if not math.isfinite(time) or time < 0.0 or time > _TERMINAL_TIME:
            raise ValueError("direct_time must lie in [0, 1]")
        if time not in self._cache:
            unconditioned = (
                self._fixture.initial_marginal
                @ self._fixture.oracle.forward_transition(time)
            )
            unnormalized = unconditioned * self._potential(time)
            normalizer = math.fsum(float(value) for value in unnormalized)
            if not math.isfinite(normalizer) or normalizer <= 0.0:
                raise ArithmeticError("exact target marginal has invalid mass")
            marginal = unnormalized / normalizer
            if np.any(marginal < 0.0) or not np.all(np.isfinite(marginal)):
                raise ArithmeticError("exact target marginal is not representable")
            self._cache[time] = _immutable_float_array(marginal)
        return self._cache[time]


class _DeterministicEvaluatorGuard:
    """Double-evaluate and digest every exact time-vector request."""

    def __init__(self, evaluator: CertifiedFiniteAssociationLogitEvaluator) -> None:
        self._evaluator = evaluator
        self._digests = {}

    @property
    def unique_input_count(self) -> int:
        return len(self._digests)

    def __call__(self, direct_times: object) -> np.ndarray:
        times = np.asarray(direct_times, dtype=np.float64)
        first = self._evaluator(times)
        second = self._evaluator(times)
        first_bytes = np.ascontiguousarray(first).tobytes(order="C")
        second_bytes = np.ascontiguousarray(second).tobytes(order="C")
        if first_bytes != second_bytes:
            raise ValueError("test-only evaluator is not deterministic")
        key = (
            times.dtype.str,
            times.shape,
            np.ascontiguousarray(times).tobytes(order="C"),
        )
        digest = hashlib.sha256(first_bytes).digest()
        previous = self._digests.get(key)
        if previous is not None and previous != digest:
            raise ValueError("test-only evaluator changed for a repeated input")
        self._digests[key] = digest
        return _immutable_float_array(first)


class _DeterministicCandidatePotential:
    def __init__(
        self,
        guard: _DeterministicEvaluatorGuard,
        fixture: FrozenAssociationResidualFixture,
        observation_index: int,
    ) -> None:
        self._guard = guard
        self._fixture = fixture
        self._observation_index = observation_index
        terminal = self.log_potential_vector(_TERMINAL_TIME)
        exact_terminal = fixture.observation.log_density_kernel[:, observation_index]
        if float(np.max(np.abs(terminal - exact_terminal))) > _TERMINAL_TOLERANCE:
            raise ValueError("candidate potential fails the frozen terminal boundary")

    def log_potential_vector(self, direct_time: object) -> np.ndarray:
        if isinstance(direct_time, (bool, np.bool_)) or not isinstance(
            direct_time, Real
        ):
            raise TypeError("direct_time must be a real non-boolean number")
        time = float(direct_time)
        if not math.isfinite(time) or time < 0.0 or time > _TERMINAL_TIME:
            raise ValueError("direct_time must lie in [0, 1]")
        logits = self._guard(np.asarray((time,), dtype=np.float64))[0]
        result = logits[:, self._observation_index] + math.log(
            float(
                self._fixture.population.observation_marginal_density[
                    self._observation_index
                ]
            )
        )
        if float(np.max(np.abs(result))) >= _PHYSICAL_LOG_INFORMATION_LIMIT:
            raise ValueError("candidate physical log information must remain below 24")
        return _immutable_float_array(result)

    def __call__(self, direct_time: object) -> np.ndarray:
        result = np.exp(self.log_potential_vector(direct_time))
        if np.any(result <= 0.0) or not np.all(np.isfinite(result)):
            raise ArithmeticError("candidate potential is not positive and finite")
        return _immutable_float_array(result)


def _edge_family_partition(
    fixture: FrozenAssociationResidualFixture,
) -> Tuple[np.ndarray, Tuple[int, int, int], str]:
    generator = np.asarray(fixture.oracle.generator, dtype=np.float64)
    states = fixture.latent_space.states
    matrix = np.full(generator.shape, -1, dtype=np.int64)
    family_to_index = {
        family: index for index, family in enumerate(FINITE_BRIDGE_JUMP_FAMILY_ORDER)
    }
    for source in range(generator.shape[0]):
        for destination in range(generator.shape[1]):
            if source == destination or generator[source, destination] <= 0.0:
                continue
            family = fixture.oracle.transition_family(
                states[source], states[destination]
            )
            if family not in family_to_index:
                raise ArithmeticError(
                    "positive aggregate generator edge has no declared family"
                )
            matrix[source, destination] = family_to_index[family]
    counts = tuple(int(np.count_nonzero(matrix == index)) for index in range(3))
    if any(value <= 0 for value in counts):
        raise ArithmeticError("the frozen fixture must exercise all jump families")
    digest = hashlib.sha256()
    digest.update(b"heterodiff-finite-a1-aggregate-edge-family-partition-v1\0")
    digest.update(np.ascontiguousarray(matrix).tobytes(order="C"))
    return _immutable_int_array(matrix), counts, digest.hexdigest()


def _path_call(
    fixture: FrozenAssociationResidualFixture,
    reference: _ExactObservationPotential,
    target_marginal: _ExactTargetMarginal,
    candidate: _DeterministicCandidatePotential,
    families: np.ndarray,
    settings: FiniteAssociationPathSolverSettings,
) -> FiniteBridgeFamilyPathKL:
    return tilted_path_kl_by_edge_family(
        fixture.initial_marginal,
        fixture.oracle.generator,
        reference,
        candidate,
        _TERMINAL_TIME,
        families,
        evaluation_times=fixture.times,
        rtol=settings.rtol,
        atol=settings.atol,
        max_step=settings.max_step,
        quadrature_epsabs=settings.quadrature_epsabs,
        quadrature_epsrel=settings.quadrature_epsrel,
        quadrature_limit=settings.quadrature_limit,
        max_potential_evaluations=settings.max_potential_evaluations,
        reference_marginal=target_marginal,
    )


def _aggregate_path_call(
    fixture: FrozenAssociationResidualFixture,
    reference: _ExactObservationPotential,
    candidate: _DeterministicCandidatePotential,
) -> object:
    settings = PRIMARY_PATH_SOLVER_SETTINGS
    return tilted_path_kl(
        fixture.initial_marginal,
        fixture.oracle.generator,
        reference,
        candidate,
        _TERMINAL_TIME,
        evaluation_times=fixture.times,
        rtol=settings.rtol,
        atol=settings.atol,
        max_step=settings.max_step,
        quadrature_epsabs=settings.quadrature_epsabs,
        quadrature_epsrel=settings.quadrature_epsrel,
        quadrature_limit=settings.quadrature_limit,
        max_potential_evaluations=settings.max_potential_evaluations,
    )


@dataclass(frozen=True)
class FiniteAssociationForkBComponentDiagnostic:
    """One explicitly applicable or inapplicable C17 component record."""

    component_id: str
    applicability: str
    target_measure: str
    integration_method: str
    primary_solver_settings: FiniteAssociationPathSolverSettings
    refined_solver_settings: FiniteAssociationPathSolverSettings
    value: Optional[float]
    refined_value: Optional[float]
    primary_refined_absolute_difference: Optional[float]
    primary_numerical_error_estimate: Optional[float]
    refined_numerical_error_estimate: Optional[float]
    numerical_error_estimate_disposition: str
    interval_certified: bool
    active_aggregate_edge_count: int
    entered_issued_total: bool

    def __post_init__(self) -> None:
        if self.component_id not in _COMPONENT_ORDER:
            raise ValueError("component_id is not frozen")
        if self.primary_solver_settings != PRIMARY_PATH_SOLVER_SETTINGS:
            raise ValueError("component primary settings are not frozen")
        if self.refined_solver_settings != REFINED_PATH_SOLVER_SETTINGS:
            raise ValueError("component refined settings are not frozen")
        if self.interval_certified is not False:
            raise ValueError("component cannot claim interval certification")
        if isinstance(self.active_aggregate_edge_count, (bool, np.bool_)) or not (
            isinstance(self.active_aggregate_edge_count, Integral)
        ):
            raise TypeError("active_aggregate_edge_count must be an integer")
        edge_count = int(self.active_aggregate_edge_count)
        if edge_count < 0:
            raise ValueError("active_aggregate_edge_count must be nonnegative")
        if type(self.entered_issued_total) is not bool:
            raise TypeError("entered_issued_total must be boolean")
        continuous = self.component_id == "KC_CONTINUOUS_COORDINATES"
        initializer = self.component_id == "K0_NORMALIZED_INITIALIZER"
        numeric_names = (
            "value",
            "refined_value",
            "primary_refined_absolute_difference",
            "primary_numerical_error_estimate",
            "refined_numerical_error_estimate",
        )
        if continuous:
            if self.applicability != (
                FINITE_ASSOCIATION_FORK_B_CONTINUOUS_COMPONENT_DISPOSITION
            ):
                raise ValueError("continuous applicability is not frozen")
            if self.integration_method != "NOT_APPLICABLE":
                raise ValueError("continuous integration method must be N/A")
            if self.target_measure != (
                FINITE_ASSOCIATION_FORK_B_CONTINUOUS_COMPONENT_DISPOSITION
            ):
                raise ValueError("continuous target measure must be N/A")
            if any(getattr(self, name) is not None for name in numeric_names):
                raise ValueError("continuous component must not carry numeric zero")
            if self.numerical_error_estimate_disposition != "NOT_APPLICABLE":
                raise ValueError("continuous numerical error must be N/A")
            if edge_count != 0 or self.entered_issued_total is not False:
                raise ValueError("continuous component cannot enter the finite total")
        else:
            if self.applicability != "APPLICABLE":
                raise ValueError("finite component must be applicable")
            for name in (
                "value",
                "refined_value",
                "primary_refined_absolute_difference",
            ):
                checked = _nonnegative(getattr(self, name), name=name)
                object.__setattr__(self, name, checked)
            expected_difference = abs(self.value - self.refined_value)  # type: ignore[operator]
            if not math.isclose(
                self.primary_refined_absolute_difference,  # type: ignore[arg-type]
                expected_difference,
                rel_tol=2.0e-12,
                abs_tol=2.0e-14,
            ):
                raise ValueError("component refinement difference is inconsistent")
            if self.entered_issued_total is not True:
                raise ValueError("applicable component must enter the issued total")
            if initializer:
                if self.target_measure != _TARGET_INITIAL_MEASURE:
                    raise ValueError(
                        "initializer must bind the exact target initial law"
                    )
                if self.integration_method != "FINITE_CATEGORICAL_KL_FLOAT64":
                    raise ValueError("initializer integration method is not frozen")
                if edge_count != 0:
                    raise ValueError("initializer must not claim active jump edges")
                if (
                    self.primary_numerical_error_estimate is not None
                    or self.refined_numerical_error_estimate is not None
                    or self.numerical_error_estimate_disposition
                    != "NO_SEPARATE_FLOAT64_ERROR_ESTIMATE"
                ):
                    raise ValueError("initializer error-estimate metadata is invalid")
            else:
                if self.target_measure != _TARGET_OCCUPATION_MEASURE:
                    raise ValueError("jump term must bind exact target occupation")
                if self.integration_method != (
                    "SCIPY_QUAD_VEC_OVER_EXACT_FINITE_TARGET_SEMIGROUP"
                ):
                    raise ValueError("jump integration method is not frozen")
                if edge_count <= 0:
                    raise ValueError("jump component must bind active edges")
                for name in (
                    "primary_numerical_error_estimate",
                    "refined_numerical_error_estimate",
                ):
                    checked = _nonnegative(getattr(self, name), name=name)
                    object.__setattr__(self, name, checked)
                if self.numerical_error_estimate_disposition != (
                    "SHARED_VECTOR_ADAPTIVE_ESTIMATE_NOT_AN_ENCLOSURE"
                ):
                    raise ValueError("jump error-estimate disposition is invalid")
        object.__setattr__(self, "active_aggregate_edge_count", edge_count)


def _component_records(
    primary: FiniteBridgeFamilyPathKL,
    refined: FiniteBridgeFamilyPathKL,
    active_edge_counts: Tuple[int, int, int],
) -> Tuple[FiniteAssociationForkBComponentDiagnostic, ...]:
    shared = {
        "primary_solver_settings": PRIMARY_PATH_SOLVER_SETTINGS,
        "refined_solver_settings": REFINED_PATH_SOLVER_SETTINGS,
        "interval_certified": False,
    }
    initializer = FiniteAssociationForkBComponentDiagnostic(
        component_id="K0_NORMALIZED_INITIALIZER",
        applicability="APPLICABLE",
        target_measure=_TARGET_INITIAL_MEASURE,
        integration_method="FINITE_CATEGORICAL_KL_FLOAT64",
        value=primary.initial,
        refined_value=refined.initial,
        primary_refined_absolute_difference=abs(primary.initial - refined.initial),
        primary_numerical_error_estimate=None,
        refined_numerical_error_estimate=None,
        numerical_error_estimate_disposition=("NO_SEPARATE_FLOAT64_ERROR_ESTIMATE"),
        active_aggregate_edge_count=0,
        entered_issued_total=True,
        **shared,
    )
    continuous = FiniteAssociationForkBComponentDiagnostic(
        component_id="KC_CONTINUOUS_COORDINATES",
        applicability=(FINITE_ASSOCIATION_FORK_B_CONTINUOUS_COMPONENT_DISPOSITION),
        target_measure=(FINITE_ASSOCIATION_FORK_B_CONTINUOUS_COMPONENT_DISPOSITION),
        integration_method="NOT_APPLICABLE",
        value=None,
        refined_value=None,
        primary_refined_absolute_difference=None,
        primary_numerical_error_estimate=None,
        refined_numerical_error_estimate=None,
        numerical_error_estimate_disposition="NOT_APPLICABLE",
        active_aggregate_edge_count=0,
        entered_issued_total=False,
        **shared,
    )
    names = (
        ("K_PLUS_BIRTH", "birth_dynamic", active_edge_counts[0]),
        ("K_MINUS_DEATH", "death_dynamic", active_edge_counts[1]),
        (
            "K_R_REPLACEMENT",
            "replacement_dynamic",
            active_edge_counts[2],
        ),
    )
    jumps = tuple(
        FiniteAssociationForkBComponentDiagnostic(
            component_id=component_id,
            applicability="APPLICABLE",
            target_measure=_TARGET_OCCUPATION_MEASURE,
            integration_method=("SCIPY_QUAD_VEC_OVER_EXACT_FINITE_TARGET_SEMIGROUP"),
            value=getattr(primary, field),
            refined_value=getattr(refined, field),
            primary_refined_absolute_difference=abs(
                getattr(primary, field) - getattr(refined, field)
            ),
            primary_numerical_error_estimate=(primary.quadrature_error_estimate),
            refined_numerical_error_estimate=(refined.quadrature_error_estimate),
            numerical_error_estimate_disposition=(
                "SHARED_VECTOR_ADAPTIVE_ESTIMATE_NOT_AN_ENCLOSURE"
            ),
            active_aggregate_edge_count=edge_count,
            entered_issued_total=True,
            **shared,
        )
        for component_id, field, edge_count in names
    )
    return (initializer, continuous) + jumps


@dataclass(frozen=True)
class FiniteAssociationForkBObservationDiagnostic:
    observation_index: int
    observation_mass: float
    components: Tuple[FiniteAssociationForkBComponentDiagnostic, ...]
    primary_initial: float
    primary_birth: float
    primary_death: float
    primary_replacement: float
    primary_dynamic: float
    primary_total: float
    refined_initial: float
    refined_birth: float
    refined_death: float
    refined_replacement: float
    refined_dynamic: float
    refined_total: float
    separately_computed_aggregate_total: float
    family_aggregate_crosscheck_absolute_difference: float
    initial_refinement_change: float
    birth_refinement_change: float
    death_refinement_change: float
    replacement_refinement_change: float
    total_refinement_change: float
    target_marginal_maximum_absolute_error: float
    terminal_log_potential_maximum_absolute_error: float
    primary_quadrature_error_estimate: float
    refined_quadrature_error_estimate: float
    primary_potential_evaluations: int
    refined_potential_evaluations: int
    numerical_failures: Tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.observation_index, (bool, np.bool_)) or not isinstance(
            self.observation_index, Integral
        ):
            raise TypeError("observation_index must be an integer")
        index = int(self.observation_index)
        if index < 0 or index >= _OBSERVATION_COUNT:
            raise ValueError("observation_index is out of range")
        scalar_names = (
            "observation_mass",
            "primary_initial",
            "primary_birth",
            "primary_death",
            "primary_replacement",
            "primary_dynamic",
            "primary_total",
            "refined_initial",
            "refined_birth",
            "refined_death",
            "refined_replacement",
            "refined_dynamic",
            "refined_total",
            "separately_computed_aggregate_total",
            "family_aggregate_crosscheck_absolute_difference",
            "initial_refinement_change",
            "birth_refinement_change",
            "death_refinement_change",
            "replacement_refinement_change",
            "total_refinement_change",
            "target_marginal_maximum_absolute_error",
            "terminal_log_potential_maximum_absolute_error",
            "primary_quadrature_error_estimate",
            "refined_quadrature_error_estimate",
        )
        values = {
            name: _nonnegative(getattr(self, name), name=name) for name in scalar_names
        }
        if values["observation_mass"] <= 0.0:
            raise ValueError("observation_mass must be positive")
        if type(self.components) is not tuple or len(self.components) != 5:
            raise ValueError("components must contain the exact five-term order")
        if not all(
            type(item) is FiniteAssociationForkBComponentDiagnostic
            for item in self.components
        ):
            raise TypeError("components contains an invalid record")
        if tuple(item.component_id for item in self.components) != _COMPONENT_ORDER:
            raise ValueError("components are not in frozen K0/KC/K+/K-/KR order")
        component_values = (
            (self.components[0], "initial"),
            (self.components[2], "birth"),
            (self.components[3], "death"),
            (self.components[4], "replacement"),
        )
        for component, suffix in component_values:
            if not math.isclose(
                component.value,  # type: ignore[arg-type]
                values["primary_" + suffix],
                rel_tol=2.0e-12,
                abs_tol=2.0e-14,
            ) or not math.isclose(
                component.refined_value,  # type: ignore[arg-type]
                values["refined_" + suffix],
                rel_tol=2.0e-12,
                abs_tol=2.0e-14,
            ):
                raise ValueError("component records disagree with flattened values")
        for prefix in ("primary", "refined"):
            family_sum = math.fsum(
                values[prefix + "_" + family]
                for family in FINITE_BRIDGE_JUMP_FAMILY_ORDER
            )
            if not math.isclose(
                values[prefix + "_dynamic"],
                family_sum,
                rel_tol=2.0e-12,
                abs_tol=2.0e-14,
            ):
                raise ValueError("%s dynamic KL is inconsistent" % prefix)
            if not math.isclose(
                values[prefix + "_total"],
                values[prefix + "_initial"] + family_sum,
                rel_tol=2.0e-12,
                abs_tol=2.0e-14,
            ):
                raise ValueError("%s total KL is inconsistent" % prefix)
        expected_changes = {
            "initial_refinement_change": abs(
                values["primary_initial"] - values["refined_initial"]
            ),
            "birth_refinement_change": abs(
                values["primary_birth"] - values["refined_birth"]
            ),
            "death_refinement_change": abs(
                values["primary_death"] - values["refined_death"]
            ),
            "replacement_refinement_change": abs(
                values["primary_replacement"] - values["refined_replacement"]
            ),
            "total_refinement_change": abs(
                values["primary_total"] - values["refined_total"]
            ),
            "family_aggregate_crosscheck_absolute_difference": abs(
                values["primary_total"] - values["separately_computed_aggregate_total"]
            ),
        }
        for name, expected in expected_changes.items():
            if not math.isclose(
                values[name], expected, rel_tol=2.0e-12, abs_tol=2.0e-14
            ):
                raise ValueError("%s is inconsistent" % name)
        for name in (
            "primary_potential_evaluations",
            "refined_potential_evaluations",
        ):
            raw = getattr(self, name)
            if isinstance(raw, (bool, np.bool_)) or not isinstance(raw, Integral):
                raise TypeError("%s must be an integer" % name)
            if int(raw) <= 0:
                raise ValueError("%s must be positive" % name)
            object.__setattr__(self, name, int(raw))
        if type(self.numerical_failures) is not tuple or not all(
            type(item) is str and item for item in self.numerical_failures
        ):
            raise TypeError("numerical_failures must be a tuple of strings")
        expected_failures = []
        if values["target_marginal_maximum_absolute_error"] > (
            _TARGET_MARGINAL_TOLERANCE
        ):
            expected_failures.append("target marginal mismatch exceeds 1e-8")
        if values["terminal_log_potential_maximum_absolute_error"] > (
            _TERMINAL_TOLERANCE
        ):
            expected_failures.append("terminal log-potential mismatch exceeds 1e-10")
        for component in (
            "initial",
            "birth",
            "death",
            "replacement",
            "total",
        ):
            if values[component + "_refinement_change"] > _REFINEMENT_TOLERANCE:
                expected_failures.append(
                    "primary/refined %s change exceeds 1e-8 nat" % component
                )
        if values["family_aggregate_crosscheck_absolute_difference"] > (
            _AGGREGATE_CROSSCHECK_TOLERANCE
        ):
            expected_failures.append(
                "family/aggregate path-KL crosscheck exceeds 1e-8 nat"
            )
        if expected_failures:
            raise ValueError(
                "a failed observation record cannot issue component totals: %s"
                % "; ".join(expected_failures)
            )
        if self.numerical_failures != tuple():
            raise ValueError("numerical_failures is incomplete or inconsistent")
        object.__setattr__(self, "observation_index", index)
        for name, value in values.items():
            object.__setattr__(self, name, value)

    @property
    def numerical_coherence_passed(self) -> bool:
        return len(self.numerical_failures) == 0


@dataclass(frozen=True, eq=False)
class FiniteAssociationForkBDiagnostic:
    schema_version: str
    scope: str
    status: str
    orientation: str
    continuous_component_disposition: str
    local_compatibility_fixture_sha256: str
    preregistered_production_fixture_sha256: str
    fixture_content_sha256: str
    edge_family_partition_sha256: str
    evaluator_parameter_sha256: str
    evaluator_feature_sha256: str
    evaluator_certificate_sha256: str
    classifier_sha256: Optional[str]
    execution_receipt_sha256: Optional[str]
    campaign_sha256: Optional[str]
    evaluator_production_bound: bool
    test_only_evaluator_used: bool
    test_only_callback_determinism_checked: bool
    determinism_unique_input_count: int
    production_checkpoint_evaluation_supported: bool
    runtime: FiniteAssociationPathRuntime
    primary_solver_settings: FiniteAssociationPathSolverSettings
    refined_solver_settings: FiniteAssociationPathSolverSettings
    family_names: Tuple[str, str, str]
    active_edge_counts: Tuple[int, int, int]
    observations: Tuple[FiniteAssociationForkBObservationDiagnostic, ...]
    observation_mass: np.ndarray
    observation_weighted_initial: float
    observation_weighted_birth: float
    observation_weighted_death: float
    observation_weighted_replacement: float
    observation_weighted_dynamic: float
    observation_weighted_total: float
    maximum_primary_refined_total_change: float
    maximum_target_marginal_absolute_error: float
    maximum_terminal_log_potential_absolute_error: float
    maximum_family_aggregate_crosscheck_absolute_difference: float
    numerical_failures: Tuple[str, ...]
    all_21_observations_evaluated: bool
    exact_finite_target_semigroup_marginal_used: bool
    association_marginalized_likelihood_used: bool
    aggregate_transition_family_partition_used: bool
    occurrence_attached_mark_fibers_exercised: bool
    continuous_coordinate_energy_exercised: bool
    cap_reference_defect_cancellation_certified: bool
    interval_enclosure_provided: bool
    simultaneous_coverage_proved: bool
    rigorous_numerical_enclosure_present: bool
    ode_or_quadrature_error_rigorously_enclosed: bool
    full_fork_b_certificate_complete: bool
    c17_theorem_proved: bool
    r1_a1_status: str
    r1_a1_result_slot_qualified: bool
    r2_hybrid_status: str
    r2_result_slot_qualified: bool
    manuscript_claim_promoted: bool
    execution_authorized: bool

    def __post_init__(self) -> None:
        if self.schema_version != "finite-association-fork-b-diagnostic-v1":
            raise ValueError("schema_version is not frozen")
        if self.scope != FINITE_ASSOCIATION_FORK_B_SCOPE:
            raise ValueError("scope is not the finite-A1 component scope")
        if self.status != FINITE_ASSOCIATION_FORK_B_STATUS:
            raise ValueError("status must remain partial")
        if self.orientation != FINITE_ASSOCIATION_FORK_B_ORIENTATION:
            raise ValueError("orientation must remain exact-target first")
        if self.continuous_component_disposition != (
            FINITE_ASSOCIATION_FORK_B_CONTINUOUS_COMPONENT_DISPOSITION
        ):
            raise ValueError("continuous component disposition is not frozen")
        for name in (
            "local_compatibility_fixture_sha256",
            "preregistered_production_fixture_sha256",
            "fixture_content_sha256",
            "edge_family_partition_sha256",
            "evaluator_parameter_sha256",
            "evaluator_feature_sha256",
            "evaluator_certificate_sha256",
        ):
            object.__setattr__(self, name, _sha256(getattr(self, name), name=name))
        if (
            self.local_compatibility_fixture_sha256
            != _LOCAL_COMPATIBILITY_FIXTURE_SHA256
            or self.preregistered_production_fixture_sha256
            != _PREREGISTERED_PRODUCTION_FIXTURE_SHA256
            or self.local_compatibility_fixture_sha256
            == self.preregistered_production_fixture_sha256
        ):
            raise ValueError("local and preregistered fixture custody is invalid")
        for name in (
            "classifier_sha256",
            "execution_receipt_sha256",
            "campaign_sha256",
        ):
            object.__setattr__(
                self, name, _optional_sha256(getattr(self, name), name=name)
            )
        if type(self.evaluator_production_bound) is not bool:
            raise TypeError("evaluator_production_bound must be boolean")
        if type(self.test_only_evaluator_used) is not bool:
            raise TypeError("test_only_evaluator_used must be boolean")
        if self.test_only_callback_determinism_checked is not True:
            raise ValueError("test-only callback determinism must be checked")
        if isinstance(self.determinism_unique_input_count, (bool, np.bool_)) or not (
            isinstance(self.determinism_unique_input_count, Integral)
        ):
            raise TypeError("determinism_unique_input_count must be an integer")
        determinism_inputs = int(self.determinism_unique_input_count)
        if determinism_inputs < 4:
            raise ValueError("determinism checks must include grid and scalar probes")
        if self.test_only_evaluator_used == self.evaluator_production_bound:
            raise ValueError("test-only and production evaluator custody conflict")
        if self.production_checkpoint_evaluation_supported is not False:
            raise ValueError(
                "the local compatibility artifact cannot support production checkpoints"
            )
        if self.evaluator_production_bound is not False:
            raise ValueError("this artifact accepts test-only evaluators only")
        production_pins = (
            self.classifier_sha256,
            self.execution_receipt_sha256,
            self.campaign_sha256,
        )
        if self.evaluator_production_bound != all(
            value is not None for value in production_pins
        ):
            raise ValueError("production evaluator custody is incomplete")
        if type(self.runtime) is not FiniteAssociationPathRuntime:
            raise TypeError("runtime must be an exact path runtime record")
        if self.primary_solver_settings != PRIMARY_PATH_SOLVER_SETTINGS:
            raise ValueError("primary solver settings are not frozen")
        if self.refined_solver_settings != REFINED_PATH_SOLVER_SETTINGS:
            raise ValueError("refined solver settings are not frozen")
        if self.family_names != FINITE_BRIDGE_JUMP_FAMILY_ORDER:
            raise ValueError("family order is not frozen")
        if (
            type(self.active_edge_counts) is not tuple
            or len(self.active_edge_counts) != 3
            or any(
                isinstance(item, (bool, np.bool_))
                or not isinstance(item, Integral)
                or int(item) <= 0
                for item in self.active_edge_counts
            )
        ):
            raise ValueError("active_edge_counts must contain three positives")
        counts = tuple(int(value) for value in self.active_edge_counts)
        records = self.observations
        if type(records) is not tuple or len(records) != _OBSERVATION_COUNT:
            raise ValueError("observations must contain all 21 records")
        if not all(
            type(item) is FiniteAssociationForkBObservationDiagnostic
            for item in records
        ):
            raise TypeError("observations contains an invalid record")
        if tuple(item.observation_index for item in records) != tuple(
            range(_OBSERVATION_COUNT)
        ):
            raise ValueError("observations are not in canonical order")
        for item in records:
            if (
                tuple(
                    component.active_aggregate_edge_count
                    for component in item.components[2:]
                )
                != counts
            ):
                raise ValueError(
                    "observation component edge counts disagree with aggregate custody"
                )
        mass = np.asarray(self.observation_mass, dtype=np.float64)
        if mass.shape != (_OBSERVATION_COUNT,) or np.any(mass <= 0.0):
            raise ValueError("observation_mass must contain 21 positive masses")
        if not math.isclose(
            math.fsum(float(value) for value in mass),
            1.0,
            rel_tol=0.0,
            abs_tol=2.0e-12,
        ):
            raise ValueError("observation masses must sum to one")
        if not np.allclose(
            mass,
            np.asarray([item.observation_mass for item in records]),
            atol=2.0e-13,
            rtol=2.0e-13,
        ):
            raise ValueError("observation masses disagree with observation records")
        weighted_names = (
            ("observation_weighted_initial", "primary_initial"),
            ("observation_weighted_birth", "primary_birth"),
            ("observation_weighted_death", "primary_death"),
            ("observation_weighted_replacement", "primary_replacement"),
            ("observation_weighted_dynamic", "primary_dynamic"),
            ("observation_weighted_total", "primary_total"),
        )
        scalar_values = {}
        for output_name, record_name in weighted_names:
            value = _nonnegative(getattr(self, output_name), name=output_name)
            expected = float(
                mass
                @ np.asarray(
                    [getattr(item, record_name) for item in records],
                    dtype=np.float64,
                )
            )
            if not math.isclose(value, expected, rel_tol=2.0e-12, abs_tol=2.0e-14):
                raise ValueError("%s is inconsistent" % output_name)
            scalar_values[output_name] = value
        maxima = {
            "maximum_primary_refined_total_change": max(
                item.total_refinement_change for item in records
            ),
            "maximum_target_marginal_absolute_error": max(
                item.target_marginal_maximum_absolute_error for item in records
            ),
            "maximum_terminal_log_potential_absolute_error": max(
                item.terminal_log_potential_maximum_absolute_error for item in records
            ),
            "maximum_family_aggregate_crosscheck_absolute_difference": max(
                item.family_aggregate_crosscheck_absolute_difference for item in records
            ),
        }
        for name, expected in maxima.items():
            value = _nonnegative(getattr(self, name), name=name)
            if not math.isclose(value, expected, rel_tol=2.0e-12, abs_tol=2.0e-14):
                raise ValueError("%s is inconsistent" % name)
            scalar_values[name] = value
        expected_failures = tuple(
            "observation %d: %s" % (item.observation_index, failure)
            for item in records
            for failure in item.numerical_failures
        )
        if self.numerical_failures != expected_failures:
            raise ValueError("numerical_failures is incomplete or inconsistent")
        required_true = (
            "all_21_observations_evaluated",
            "exact_finite_target_semigroup_marginal_used",
            "association_marginalized_likelihood_used",
            "aggregate_transition_family_partition_used",
        )
        required_false = (
            "occurrence_attached_mark_fibers_exercised",
            "continuous_coordinate_energy_exercised",
            "cap_reference_defect_cancellation_certified",
            "interval_enclosure_provided",
            "simultaneous_coverage_proved",
            "rigorous_numerical_enclosure_present",
            "ode_or_quadrature_error_rigorously_enclosed",
            "full_fork_b_certificate_complete",
            "c17_theorem_proved",
            "r1_a1_result_slot_qualified",
            "r2_result_slot_qualified",
            "manuscript_claim_promoted",
            "execution_authorized",
        )
        if self.r1_a1_status != "NOT_RUN" or self.r2_hybrid_status != "NOT_RUN":
            raise ValueError("R1-A1 and R2-HYBRID must remain NOT_RUN")
        for name in required_true:
            if getattr(self, name) is not True:
                raise ValueError("%s must be true" % name)
        for name in required_false:
            if getattr(self, name) is not False:
                raise ValueError("%s must remain false" % name)
        object.__setattr__(self, "active_edge_counts", counts)
        object.__setattr__(self, "determinism_unique_input_count", determinism_inputs)
        object.__setattr__(self, "observation_mass", _immutable_float_array(mass))
        for name, value in scalar_values.items():
            object.__setattr__(self, name, value)

    @property
    def numerical_coherence_passed(self) -> bool:
        """Whether the bounded numerical checks passed, not a C17 result."""

        return len(self.numerical_failures) == 0


def _observation_record(
    guard: _DeterministicEvaluatorGuard,
    fixture: FrozenAssociationResidualFixture,
    observation_index: int,
    families: np.ndarray,
    active_edge_counts: Tuple[int, int, int],
) -> FiniteAssociationForkBObservationDiagnostic:
    reference = _ExactObservationPotential(fixture, observation_index)
    target = _ExactTargetMarginal(fixture, reference)
    candidate = _DeterministicCandidatePotential(guard, fixture, observation_index)
    primary = _path_call(
        fixture,
        reference,
        target,
        candidate,
        families,
        PRIMARY_PATH_SOLVER_SETTINGS,
    )
    refined = _path_call(
        fixture,
        reference,
        target,
        candidate,
        families,
        REFINED_PATH_SOLVER_SETTINGS,
    )
    aggregate = _aggregate_path_call(fixture, reference, candidate)
    target_grid = np.stack([target(float(time)) for time in fixture.times], axis=0)
    target_error = float(
        np.max(
            np.abs(
                target_grid
                - fixture.population.conditional_time[:, :, observation_index]
            )
        )
    )
    terminal_error = float(
        np.max(
            np.abs(
                candidate.log_potential_vector(_TERMINAL_TIME)
                - np.log(reference(_TERMINAL_TIME))
            )
        )
    )
    total_change = abs(primary.total - refined.total)
    failures = []
    if target_error > _TARGET_MARGINAL_TOLERANCE:
        failures.append("target marginal mismatch exceeds 1e-8")
    if terminal_error > _TERMINAL_TOLERANCE:
        failures.append("terminal log-potential mismatch exceeds 1e-10")
    component_changes = (
        ("initial", abs(primary.initial - refined.initial)),
        ("birth", abs(primary.birth_dynamic - refined.birth_dynamic)),
        ("death", abs(primary.death_dynamic - refined.death_dynamic)),
        (
            "replacement",
            abs(primary.replacement_dynamic - refined.replacement_dynamic),
        ),
        ("total", total_change),
    )
    for component, change in component_changes:
        if change > _REFINEMENT_TOLERANCE:
            failures.append("primary/refined %s change exceeds 1e-8 nat" % component)
    crosscheck_change = abs(primary.total - aggregate.total)
    if crosscheck_change > _AGGREGATE_CROSSCHECK_TOLERANCE:
        failures.append("family/aggregate path-KL crosscheck exceeds 1e-8 nat")
    if failures:
        raise ArithmeticError(
            "finite-A1 Fork-B diagnostic refused before issuing totals: %s"
            % "; ".join(failures)
        )
    return FiniteAssociationForkBObservationDiagnostic(
        observation_index=observation_index,
        observation_mass=float(
            fixture.population.observation_marginal_mass[observation_index]
        ),
        components=_component_records(primary, refined, active_edge_counts),
        primary_initial=primary.initial,
        primary_birth=primary.birth_dynamic,
        primary_death=primary.death_dynamic,
        primary_replacement=primary.replacement_dynamic,
        primary_dynamic=primary.dynamic,
        primary_total=primary.total,
        refined_initial=refined.initial,
        refined_birth=refined.birth_dynamic,
        refined_death=refined.death_dynamic,
        refined_replacement=refined.replacement_dynamic,
        refined_dynamic=refined.dynamic,
        refined_total=refined.total,
        separately_computed_aggregate_total=aggregate.total,
        family_aggregate_crosscheck_absolute_difference=crosscheck_change,
        initial_refinement_change=abs(primary.initial - refined.initial),
        birth_refinement_change=abs(primary.birth_dynamic - refined.birth_dynamic),
        death_refinement_change=abs(primary.death_dynamic - refined.death_dynamic),
        replacement_refinement_change=abs(
            primary.replacement_dynamic - refined.replacement_dynamic
        ),
        total_refinement_change=total_change,
        target_marginal_maximum_absolute_error=target_error,
        terminal_log_potential_maximum_absolute_error=terminal_error,
        primary_quadrature_error_estimate=primary.quadrature_error_estimate,
        refined_quadrature_error_estimate=refined.quadrature_error_estimate,
        primary_potential_evaluations=primary.potential_evaluations,
        refined_potential_evaluations=refined.potential_evaluations,
        numerical_failures=tuple(failures),
    )


def evaluate_finite_association_fork_b_diagnostic(
    evaluator: CertifiedFiniteAssociationLogitEvaluator,
    fixture: FrozenAssociationResidualFixture,
    *,
    test_only: bool = False,
) -> FiniteAssociationForkBDiagnostic:
    """Evaluate the all-21 finite jump-family component and nothing broader.

    Only a test-only evaluator with ``test_only=True`` is accepted.  The
    locally rebuilt compatibility fixture does not provide frozen-runtime
    production path-content bytes, so production-bound evaluators fail closed.
    This function never trains, selects, loads, or bypasses a production
    checkpoint; a future production lane requires a separate binding.
    """

    if type(evaluator) is not CertifiedFiniteAssociationLogitEvaluator:
        raise TypeError("evaluator must be certificate-bound")
    if type(test_only) is not bool:
        raise TypeError("test_only must be boolean")
    if evaluator.production_bound:
        raise ValueError("production checkpoint evaluation is not supported")
    if test_only is not True:
        raise ValueError("the local compatibility evaluator requires test_only=True")
    checked_fixture = _validate_fixture(fixture)
    actual_fixture = frozen_association_fixture_sha256(
        frozen_association_fixture_content_digests(checked_fixture)
    )
    if evaluator.certification.frozen_fixture_sha256 != actual_fixture:
        raise ValueError("evaluator certificate does not bind the frozen fixture")
    families, edge_counts, family_digest = _edge_family_partition(checked_fixture)
    guard = _DeterministicEvaluatorGuard(evaluator)
    determinism_probes = (
        checked_fixture.times,
        np.asarray((0.0,), dtype=np.float64),
        np.asarray((0.5,), dtype=np.float64),
        np.asarray((1.0,), dtype=np.float64),
    )
    evaluator.assert_integrity()
    try:
        for probe in determinism_probes:
            guard(probe)
        records = tuple(
            _observation_record(
                guard,
                checked_fixture,
                index,
                families,
                edge_counts,
            )
            for index in range(_OBSERVATION_COUNT)
        )
        for probe in determinism_probes:
            guard(probe)
    finally:
        evaluator.assert_integrity()
    mass = np.asarray(
        checked_fixture.population.observation_marginal_mass,
        dtype=np.float64,
    )

    def weighted(name: str) -> float:
        return float(
            mass
            @ np.asarray([getattr(item, name) for item in records], dtype=np.float64)
        )

    failures = tuple(
        "observation %d: %s" % (item.observation_index, failure)
        for item in records
        for failure in item.numerical_failures
    )
    return FiniteAssociationForkBDiagnostic(
        schema_version="finite-association-fork-b-diagnostic-v1",
        scope=FINITE_ASSOCIATION_FORK_B_SCOPE,
        status=FINITE_ASSOCIATION_FORK_B_STATUS,
        orientation=FINITE_ASSOCIATION_FORK_B_ORIENTATION,
        continuous_component_disposition=(
            FINITE_ASSOCIATION_FORK_B_CONTINUOUS_COMPONENT_DISPOSITION
        ),
        local_compatibility_fixture_sha256=actual_fixture,
        preregistered_production_fixture_sha256=(
            _PREREGISTERED_PRODUCTION_FIXTURE_SHA256
        ),
        fixture_content_sha256=finite_association_path_fixture_content_sha256(
            checked_fixture
        ),
        edge_family_partition_sha256=family_digest,
        evaluator_parameter_sha256=evaluator.certification.parameter_sha256,
        evaluator_feature_sha256=evaluator.certification.feature_sha256,
        evaluator_certificate_sha256=(evaluator.certification.certificate_sha256),
        classifier_sha256=evaluator.classifier_sha256,
        execution_receipt_sha256=evaluator.execution_receipt_sha256,
        campaign_sha256=evaluator.campaign_sha256,
        evaluator_production_bound=evaluator.production_bound,
        test_only_evaluator_used=not evaluator.production_bound,
        test_only_callback_determinism_checked=True,
        determinism_unique_input_count=guard.unique_input_count,
        production_checkpoint_evaluation_supported=False,
        runtime=FiniteAssociationPathRuntime.current(),
        primary_solver_settings=PRIMARY_PATH_SOLVER_SETTINGS,
        refined_solver_settings=REFINED_PATH_SOLVER_SETTINGS,
        family_names=FINITE_BRIDGE_JUMP_FAMILY_ORDER,
        active_edge_counts=edge_counts,
        observations=records,
        observation_mass=mass,
        observation_weighted_initial=weighted("primary_initial"),
        observation_weighted_birth=weighted("primary_birth"),
        observation_weighted_death=weighted("primary_death"),
        observation_weighted_replacement=weighted("primary_replacement"),
        observation_weighted_dynamic=weighted("primary_dynamic"),
        observation_weighted_total=weighted("primary_total"),
        maximum_primary_refined_total_change=max(
            item.total_refinement_change for item in records
        ),
        maximum_target_marginal_absolute_error=max(
            item.target_marginal_maximum_absolute_error for item in records
        ),
        maximum_terminal_log_potential_absolute_error=max(
            item.terminal_log_potential_maximum_absolute_error for item in records
        ),
        maximum_family_aggregate_crosscheck_absolute_difference=max(
            item.family_aggregate_crosscheck_absolute_difference for item in records
        ),
        numerical_failures=failures,
        all_21_observations_evaluated=True,
        exact_finite_target_semigroup_marginal_used=True,
        association_marginalized_likelihood_used=True,
        aggregate_transition_family_partition_used=True,
        occurrence_attached_mark_fibers_exercised=False,
        continuous_coordinate_energy_exercised=False,
        cap_reference_defect_cancellation_certified=False,
        interval_enclosure_provided=False,
        simultaneous_coverage_proved=False,
        rigorous_numerical_enclosure_present=False,
        ode_or_quadrature_error_rigorously_enclosed=False,
        full_fork_b_certificate_complete=False,
        c17_theorem_proved=False,
        r1_a1_status="NOT_RUN",
        r1_a1_result_slot_qualified=False,
        r2_hybrid_status="NOT_RUN",
        r2_result_slot_qualified=False,
        manuscript_claim_promoted=False,
        execution_authorized=False,
    )


__all__ = [
    "FINITE_ASSOCIATION_FORK_B_CONTINUOUS_COMPONENT_DISPOSITION",
    "FINITE_ASSOCIATION_FORK_B_ORIENTATION",
    "FINITE_ASSOCIATION_FORK_B_SCOPE",
    "FINITE_ASSOCIATION_FORK_B_STATUS",
    "FiniteAssociationForkBComponentDiagnostic",
    "FiniteAssociationForkBDiagnostic",
    "FiniteAssociationForkBObservationDiagnostic",
    "evaluate_finite_association_fork_b_diagnostic",
]
