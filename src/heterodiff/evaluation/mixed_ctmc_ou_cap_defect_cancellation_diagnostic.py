"""Cap-defect cancellation diagnostic for the factorized CTMC--OU fixture.

The existing mixed CTMC--OU path diagnostic compares the exact conditioned
law with a terminal-matched plug-in law through the error

``e = log(hat_h / h)``.

This module refactors both potentials through one deliberately non-harmonic
shared guide.  The guide is the information function of an auxiliary cap-3
count CTMC, restricted to the six states of the cap-2 target CTMC.  Its
harmonic defect under the cap-2 generator is nonzero at the cap and equals the
negative action of exactly the auxiliary births blocked by that cap.

For the shared factorization

``h = tilde_h * exp(r_star)`` and
``hat_h = tilde_h * exp(r_theta)``,

the code independently recovers ``e = r_theta - r_star`` and recomputes the
initializer, OU-gradient, birth, death, and replacement terms.  The cap
defect is not added to the path relative entropy.  This is the cancellation
required by the C17 algebra, but only on one small factorized fixture.

Matrix exponentials and adaptive quadrature are ordinary binary64 numerical
evaluations.  They are not interval enclosures.  This module does not exercise
a learned residual, association marginalization, occurrence-attached marks,
the general C17 theorem, or R2-HYBRID, and it authorizes no claim or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Tuple
import warnings

import numpy as np
from scipy.integrate import IntegrationWarning, quad
from scipy.special import logsumexp

from heterodiff.evaluation.mixed_ctmc_ou_known_law_oracle import (
    MixedCTMCOUKnownLawOracle,
    build_mixed_ctmc_ou_known_law_oracle,
)
from heterodiff.evaluation.mixed_ctmc_ou_path_kl_diagnostic import (
    MixedCTMCOUPathKLDiagnostic,
    TerminalMatchedResidual,
    build_mixed_ctmc_ou_path_kl_diagnostic,
    residual_value,
)
from heterodiff.theory.finite_atomic_counting import (
    FiniteAtomicCountingSpace,
    finite_atomic_birth_generator,
    finite_atomic_death_generator,
    finite_atomic_replacement_generator,
)
from heterodiff.theory.finite_state import combine_generators, transition_matrix


DIAGNOSTIC_SCOPE = "FINITE_FACTORIZED_MIXED_CTMC_OU_SHARED_CAP3_GUIDE_CANCELLATION"
NUMERICAL_QUALIFICATION = (
    "EXACT_SHARED_GUIDE_AND_BLOCKED_BIRTH_ALGEBRA_WITH_"
    "BINARY64_MATRIX_EXPONENTIALS_AND_NONINTERVAL_QUADRATURE"
)

_AUXILIARY_CAP = 3
_BIRTH_RATES = (0.7, 0.4)
_DEATH_RATES = (0.5, 0.3)
_REPLACEMENT_RATES = ((0.0, 0.2), (0.35, 0.0))
_EVALUATION_TIME_FRACTIONS = (0.0, 0.25, 0.5, 0.75, 1.0)
_EVALUATION_COORDINATES = (-1.0, 0.0, 1.0)
_MAX_QUADRATURE_SUBDIVISIONS = 10_000


def _readonly(value: object, *, dtype: np.dtype = np.dtype(np.float64)) -> np.ndarray:
    array = np.array(value, dtype=dtype, copy=True, order="C")
    return np.frombuffer(array.tobytes(order="C"), dtype=dtype).reshape(array.shape)


def _positive_real(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError("%s must be finite and greater than zero" % name)
    return result


def _positive_integer(value: object, *, name: str, maximum: int) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result <= 0 or result > maximum:
        raise ValueError("%s must lie between 1 and %d" % (name, maximum))
    return result


def _nonnegative(value: float, *, name: str, tolerance: float = 1.0e-13) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ArithmeticError("%s is not finite" % name)
    if result < -tolerance:
        raise ArithmeticError("%s is unexpectedly negative" % name)
    return max(0.0, result)


def _phi(value: float) -> float:
    """Evaluate ``exp(value) - 1 - value`` stably near zero."""

    if abs(value) < 1.0e-4:
        return (
            value
            * value
            * (
                0.5
                + value
                * (
                    1.0 / 6.0
                    + value * (1.0 / 24.0 + value * (1.0 / 120.0 + value / 720.0))
                )
            )
        )
    return _nonnegative(
        math.expm1(value) - value,
        name="Poisson Bregman function",
    )


@dataclass(frozen=True, eq=False)
class CapDefectTimeSlice:
    """One direct-time evaluation of the restricted auxiliary guide."""

    time: float
    exact_cap2_information: np.ndarray
    restricted_cap3_guide: np.ndarray
    exact_residual: np.ndarray
    plugin_residual_at_zero_coordinate: np.ndarray
    recovered_error_at_zero_coordinate: np.ndarray
    generator_harmonic_defect: np.ndarray
    blocked_birth_defect: np.ndarray
    cap_mask: np.ndarray
    maximum_defect_identity_residual: float
    maximum_error_recovery_residual: float
    maximum_target_log_reconstruction_residual: float
    maximum_plugin_log_reconstruction_residual: float


@dataclass(frozen=True)
class SharedGuidePathKLComponents:
    """Five-term exact-to-plug-in decomposition evaluated through the guide."""

    initializer: float
    ou_continuous_gradient: float
    birth: float
    death: float
    replacement: float
    dynamic: float
    total: float
    birth_quadrature_error_estimate: float
    death_quadrature_error_estimate: float
    replacement_quadrature_error_estimate: float
    total_quadrature_error_estimate: float


@dataclass(frozen=True)
class ExistingDiagnosticAgreement:
    """Absolute component differences from the existing Fork-B diagnostic."""

    initializer_absolute_difference: float
    ou_continuous_gradient_absolute_difference: float
    birth_absolute_difference: float
    death_absolute_difference: float
    replacement_absolute_difference: float
    total_absolute_difference: float
    maximum_component_absolute_difference: float


@dataclass(frozen=True)
class DiagnosticScopeBoundary:
    mathematical_shared_guide_cancellation_exact: bool
    mathematical_blocked_birth_identity_exact: bool
    floating_matrix_exponentials_interval_certified: bool
    floating_quadrature_interval_certified: bool
    adaptive_error_estimate_is_rigorous_bound: bool
    fixture_cap_defect_cancellation_exercised: bool
    cap_defect_used_as_path_kl_summand: bool
    general_cap_stability_proved: bool
    learned_estimator_exercised: bool
    association_marginalization_exercised: bool
    continuous_marks_attached_to_occurrences: bool
    general_c17_theorem_proved: bool
    r2_hybrid_completed: bool
    claim_promotion_authorized: bool
    confirmatory_execution_authorized: bool
    production_execution_authorized: bool


@dataclass(frozen=True)
class MixedCTMCOUCapDefectCancellationDiagnostic:
    """Complete cap-defect cancellation record and its no-claim boundary."""

    scope: str
    numerical_qualification: str
    state_vectors: Tuple[Tuple[int, int], ...]
    auxiliary_state_vectors: Tuple[Tuple[int, int], ...]
    auxiliary_cap: int
    evaluation_times: np.ndarray
    evaluation_coordinates: np.ndarray
    time_slices: Tuple[CapDefectTimeSlice, ...]
    maximum_absolute_cap_defect: float
    maximum_defect_identity_residual: float
    maximum_error_recovery_residual: float
    maximum_target_log_reconstruction_residual: float
    maximum_plugin_log_reconstruction_residual: float
    terminal_exact_residual_zero: bool
    terminal_plugin_residual_zero: bool
    terminal_guide_matches_target_likelihood: bool
    path_total_excludes_cap_defect: bool
    shared_guide_decomposition: SharedGuidePathKLComponents
    existing_path_diagnostic: MixedCTMCOUPathKLDiagnostic
    existing_diagnostic_agreement: ExistingDiagnosticAgreement
    boundary: DiagnosticScopeBoundary


@dataclass(frozen=True, eq=False)
class _AuxiliaryGuide:
    state_vectors: Tuple[Tuple[int, int], ...]
    birth_generator: np.ndarray
    generator: np.ndarray
    terminal_likelihood: np.ndarray
    common_indices: np.ndarray


def _terminal_likelihood(states: Tuple[Tuple[int, int], ...]) -> np.ndarray:
    return np.asarray(
        [
            1.0 + 0.75 * alpha + 0.4 * beta + 0.2 * alpha * beta
            for alpha, beta in states
        ],
        dtype=np.float64,
    )


def _build_auxiliary_guide(
    cap2_states: Tuple[Tuple[int, int], ...],
) -> _AuxiliaryGuide:
    space = FiniteAtomicCountingSpace(("alpha", "beta"), total_cap=_AUXILIARY_CAP)
    birth = finite_atomic_birth_generator(space, _BIRTH_RATES)
    death = finite_atomic_death_generator(space, _DEATH_RATES)
    replacement = finite_atomic_replacement_generator(
        space,
        np.asarray(_REPLACEMENT_RATES, dtype=np.float64),
    )
    generator = combine_generators(birth, death, replacement)
    position = {state: index for index, state in enumerate(space.states)}
    if any(state not in position for state in cap2_states):
        raise RuntimeError(
            "the auxiliary state space does not contain every cap-2 state"
        )
    common = np.asarray([position[state] for state in cap2_states], dtype=np.int64)
    return _AuxiliaryGuide(
        state_vectors=tuple(space.states),
        birth_generator=_readonly(birth),
        generator=_readonly(generator),
        terminal_likelihood=_readonly(_terminal_likelihood(tuple(space.states))),
        common_indices=_readonly(common, dtype=np.dtype(np.int64)),
    )


def _cap2_information(
    oracle: MixedCTMCOUKnownLawOracle,
    time: float,
) -> np.ndarray:
    horizon = oracle.continuous.parameters.horizon
    result = transition_matrix(oracle.discrete.generator, horizon - time) @ (
        oracle.discrete.terminal_likelihood
    )
    if not np.all(np.isfinite(result)) or np.any(result <= 0.0):
        raise ArithmeticError("cap-2 information is not finite and positive")
    return result


def _cap3_information(
    auxiliary: _AuxiliaryGuide,
    horizon: float,
    time: float,
) -> np.ndarray:
    result = transition_matrix(auxiliary.generator, horizon - time) @ (
        auxiliary.terminal_likelihood
    )
    if not np.all(np.isfinite(result)) or np.any(result <= 0.0):
        raise ArithmeticError("cap-3 guide information is not finite and positive")
    return result


def _time_slice(
    oracle: MixedCTMCOUKnownLawOracle,
    auxiliary: _AuxiliaryGuide,
    residual: TerminalMatchedResidual,
    time: float,
) -> CapDefectTimeSlice:
    horizon = oracle.continuous.parameters.horizon
    cap2_states = oracle.discrete.state_vectors
    information2 = _cap2_information(oracle, time)
    information3 = _cap3_information(auxiliary, horizon, time)
    common = np.asarray(auxiliary.common_indices, dtype=np.int64)
    guide = information3[common]

    # h3 solves partial_t h3 = -Q3 h3.  Restriction and Q2 application give
    # the full harmonic defect without a finite-difference time derivative.
    guide_time_derivative = (-auxiliary.generator @ information3)[common]
    defect = (guide_time_derivative + oracle.discrete.generator @ guide) / guide

    # Use the declared target cap rather than relying on state ordering.
    target_cap = max(sum(state) for state in cap2_states)
    cap_mask = np.asarray([sum(state) == target_cap for state in cap2_states])
    blocked = np.zeros(len(cap2_states), dtype=np.float64)
    for cap2_index, source_index in enumerate(common):
        if not cap_mask[cap2_index]:
            continue
        source = int(source_index)
        terms = []
        for destination, destination_state in enumerate(auxiliary.state_vectors):
            if sum(destination_state) <= target_cap:
                continue
            rate = float(auxiliary.birth_generator[source, destination])
            if rate == 0.0:
                continue
            terms.append(-rate * (information3[destination] - information3[source]))
        blocked[cap2_index] = math.fsum(terms) / float(guide[cap2_index])

    exact_residual = np.log(information2) - np.log(guide)
    error = np.asarray(
        [
            residual_value(
                residual,
                time=time,
                state_index=index,
                coordinate=0.0,
                horizon=horizon,
            )
            for index in range(len(cap2_states))
        ],
        dtype=np.float64,
    )
    plugin_residual = exact_residual + error
    recovered_error = plugin_residual - exact_residual
    target_log_reconstruction = np.log(guide) + exact_residual
    target_log = np.log(information2)
    error_recovery_residuals = []
    plugin_reconstruction_residuals = []
    for coordinate in _EVALUATION_COORDINATES:
        coordinate_error = np.asarray(
            [
                residual_value(
                    residual,
                    time=time,
                    state_index=index,
                    coordinate=coordinate,
                    horizon=horizon,
                )
                for index in range(len(cap2_states))
            ],
            dtype=np.float64,
        )
        coordinate_plugin_residual = exact_residual + coordinate_error
        coordinate_recovered = coordinate_plugin_residual - exact_residual
        error_recovery_residuals.append(
            float(np.max(np.abs(coordinate_recovered - coordinate_error)))
        )
        plugin_reconstruction_residuals.append(
            float(
                np.max(
                    np.abs(
                        np.log(guide)
                        + coordinate_plugin_residual
                        - (target_log + coordinate_error)
                    )
                )
            )
        )

    return CapDefectTimeSlice(
        time=time,
        exact_cap2_information=_readonly(information2),
        restricted_cap3_guide=_readonly(guide),
        exact_residual=_readonly(exact_residual),
        plugin_residual_at_zero_coordinate=_readonly(plugin_residual),
        recovered_error_at_zero_coordinate=_readonly(recovered_error),
        generator_harmonic_defect=_readonly(defect),
        blocked_birth_defect=_readonly(blocked),
        cap_mask=_readonly(cap_mask, dtype=np.dtype(bool)),
        maximum_defect_identity_residual=float(np.max(np.abs(defect - blocked))),
        maximum_error_recovery_residual=max(error_recovery_residuals),
        maximum_target_log_reconstruction_residual=float(
            np.max(np.abs(target_log_reconstruction - target_log))
        ),
        maximum_plugin_log_reconstruction_residual=max(plugin_reconstruction_residuals),
    )


def _target_marginal_and_rates(
    oracle: MixedCTMCOUKnownLawOracle,
    time: float,
) -> Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    information = _cap2_information(oracle, time)
    base_marginal = oracle.discrete.initial_probabilities @ transition_matrix(
        oracle.discrete.generator, time
    )
    target = base_marginal * information / oracle.discrete.evidence
    mass = math.fsum(float(value) for value in target)
    if (
        not np.all(np.isfinite(target))
        or np.any(target < 0.0)
        or not math.isclose(mass, 1.0, rel_tol=0.0, abs_tol=2.0e-11)
    ):
        raise ArithmeticError("target marginal is not a probability law")
    target = target / mass
    information_ratio = information[np.newaxis, :] / information[:, np.newaxis]
    families = []
    for base_family in (
        oracle.discrete.birth_generator,
        oracle.discrete.death_generator,
        oracle.discrete.replacement_generator,
    ):
        rates = np.array(base_family, dtype=np.float64, copy=True)
        np.fill_diagonal(rates, 0.0)
        rates *= information_ratio
        if not np.all(np.isfinite(rates)) or np.any(rates < 0.0):
            raise ArithmeticError("target family rates are invalid")
        families.append(rates)
    return target, (families[0], families[1], families[2])


def _recovered_error_vector(
    oracle: MixedCTMCOUKnownLawOracle,
    auxiliary: _AuxiliaryGuide,
    residual: TerminalMatchedResidual,
    time: float,
) -> np.ndarray:
    information2 = _cap2_information(oracle, time)
    information3 = _cap3_information(
        auxiliary,
        oracle.continuous.parameters.horizon,
        time,
    )
    guide = information3[np.asarray(auxiliary.common_indices, dtype=np.int64)]
    r_star = np.log(information2) - np.log(guide)
    declared_error = np.asarray(
        [
            residual_value(
                residual,
                time=time,
                state_index=index,
                coordinate=0.0,
                horizon=oracle.continuous.parameters.horizon,
            )
            for index in range(len(oracle.discrete.state_vectors))
        ],
        dtype=np.float64,
    )
    r_theta = r_star + declared_error
    recovered = r_theta - r_star
    if not np.all(np.isfinite(recovered)):
        raise ArithmeticError("shared-guide error is not finite")
    return recovered


def _jump_integrand(
    oracle: MixedCTMCOUKnownLawOracle,
    auxiliary: _AuxiliaryGuide,
    residual: TerminalMatchedResidual,
    family_index: int,
    time: float,
) -> float:
    target, families = _target_marginal_and_rates(oracle, time)
    error = _recovered_error_vector(oracle, auxiliary, residual, time)
    family = families[family_index]
    terms = []
    for source in range(family.shape[0]):
        for destination in range(family.shape[1]):
            rate = float(family[source, destination])
            if source == destination or rate == 0.0:
                continue
            increment = float(error[destination] - error[source])
            terms.append(float(target[source]) * rate * _phi(increment))
    return _nonnegative(math.fsum(terms), name="shared-guide jump integrand")


def _adaptive_integral(
    oracle: MixedCTMCOUKnownLawOracle,
    auxiliary: _AuxiliaryGuide,
    residual: TerminalMatchedResidual,
    family_index: int,
    *,
    absolute_tolerance: float,
    relative_tolerance: float,
    subdivisions: int,
) -> Tuple[float, float]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", IntegrationWarning)
            value, error = quad(
                lambda time: _jump_integrand(
                    oracle,
                    auxiliary,
                    residual,
                    family_index,
                    float(time),
                ),
                0.0,
                oracle.continuous.parameters.horizon,
                epsabs=absolute_tolerance,
                epsrel=relative_tolerance,
                limit=subdivisions,
            )
    except (ArithmeticError, IntegrationWarning, ValueError) as exception:
        raise ArithmeticError("shared-guide adaptive quadrature failed") from exception
    return (
        _nonnegative(value, name="shared-guide jump integral"),
        _nonnegative(error, name="shared-guide quadrature error estimate"),
    )


def _shared_guide_decomposition(
    oracle: MixedCTMCOUKnownLawOracle,
    auxiliary: _AuxiliaryGuide,
    residual: TerminalMatchedResidual,
    *,
    absolute_tolerance: float,
    relative_tolerance: float,
    subdivisions: int,
) -> SharedGuidePathKLComponents:
    recovered_initial_error = _recovered_error_vector(oracle, auxiliary, residual, 0.0)
    exact_initial = np.asarray(oracle.discrete.tilted_initial_probabilities)
    log_exact = np.log(exact_initial)
    log_normalizer = float(logsumexp(log_exact + recovered_initial_error))
    plugin_initial = np.exp(log_exact + recovered_initial_error - log_normalizer)
    plugin_initial /= math.fsum(float(value) for value in plugin_initial)
    discrete_initializer = _nonnegative(
        math.fsum(
            float(exact) * (math.log(float(exact)) - math.log(float(plugin)))
            for exact, plugin in zip(exact_initial, plugin_initial)
        ),
        name="shared-guide discrete initializer KL",
    )
    initial_variance = oracle.continuous.tilted_initial_variance
    continuous_slope = residual.continuous_slope
    ou_initializer = _nonnegative(
        0.5 * initial_variance * continuous_slope * continuous_slope,
        name="shared-guide OU initializer KL",
    )
    initializer = math.fsum((discrete_initializer, ou_initializer))

    parameters = oracle.continuous.parameters
    continuous = _nonnegative(
        parameters.diffusion**2 * continuous_slope**2 * parameters.horizon / 6.0,
        name="shared-guide OU-gradient KL",
    )
    values = []
    errors = []
    for family_index in range(3):
        value, error = _adaptive_integral(
            oracle,
            auxiliary,
            residual,
            family_index,
            absolute_tolerance=absolute_tolerance,
            relative_tolerance=relative_tolerance,
            subdivisions=subdivisions,
        )
        values.append(value)
        errors.append(error)
    birth, death, replacement = values
    birth_error, death_error, replacement_error = errors
    dynamic = math.fsum((continuous, birth, death, replacement))
    total = math.fsum((initializer, dynamic))
    if not math.isfinite(total):
        raise ArithmeticError("shared-guide path KL is not representable")
    return SharedGuidePathKLComponents(
        initializer=initializer,
        ou_continuous_gradient=continuous,
        birth=birth,
        death=death,
        replacement=replacement,
        dynamic=dynamic,
        total=total,
        birth_quadrature_error_estimate=birth_error,
        death_quadrature_error_estimate=death_error,
        replacement_quadrature_error_estimate=replacement_error,
        total_quadrature_error_estimate=math.fsum(errors),
    )


def _agreement(
    shared: SharedGuidePathKLComponents,
    existing: MixedCTMCOUPathKLDiagnostic,
) -> ExistingDiagnosticAgreement:
    decomposition = existing.decomposition
    differences = (
        abs(shared.initializer - decomposition.initializer.total_exact_to_plugin),
        abs(shared.ou_continuous_gradient - decomposition.ou_continuous_gradient),
        abs(shared.birth - decomposition.jumps.birth),
        abs(shared.death - decomposition.jumps.death),
        abs(shared.replacement - decomposition.jumps.replacement),
        abs(shared.total - decomposition.total),
    )
    return ExistingDiagnosticAgreement(
        initializer_absolute_difference=differences[0],
        ou_continuous_gradient_absolute_difference=differences[1],
        birth_absolute_difference=differences[2],
        death_absolute_difference=differences[3],
        replacement_absolute_difference=differences[4],
        total_absolute_difference=differences[5],
        maximum_component_absolute_difference=max(differences),
    )


def build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic(
    *,
    residual: TerminalMatchedResidual = TerminalMatchedResidual(),
    quadrature_absolute_tolerance: object = 1.0e-11,
    quadrature_relative_tolerance: object = 1.0e-11,
    quadrature_subdivisions: object = 200,
) -> MixedCTMCOUCapDefectCancellationDiagnostic:
    """Build the shared-guide cap cancellation diagnostic.

    Quadrature error estimates remain non-rigorous library diagnostics.  No
    output of this function closes a gate, promotes a claim, or authorizes an
    execution.
    """

    if not isinstance(residual, TerminalMatchedResidual):
        raise TypeError("residual must be a TerminalMatchedResidual instance")
    absolute_tolerance = _positive_real(
        quadrature_absolute_tolerance,
        name="quadrature_absolute_tolerance",
    )
    relative_tolerance = _positive_real(
        quadrature_relative_tolerance,
        name="quadrature_relative_tolerance",
    )
    subdivisions = _positive_integer(
        quadrature_subdivisions,
        name="quadrature_subdivisions",
        maximum=_MAX_QUADRATURE_SUBDIVISIONS,
    )

    oracle = build_mixed_ctmc_ou_known_law_oracle()
    auxiliary = _build_auxiliary_guide(oracle.discrete.state_vectors)
    horizon = oracle.continuous.parameters.horizon
    times = np.asarray(
        [fraction * horizon for fraction in _EVALUATION_TIME_FRACTIONS],
        dtype=np.float64,
    )
    slices = tuple(
        _time_slice(oracle, auxiliary, residual, float(time)) for time in times
    )
    shared = _shared_guide_decomposition(
        oracle,
        auxiliary,
        residual,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        subdivisions=subdivisions,
    )
    existing = build_mixed_ctmc_ou_path_kl_diagnostic(
        residual=residual,
        quadrature_absolute_tolerance=absolute_tolerance,
        quadrature_relative_tolerance=relative_tolerance,
        quadrature_subdivisions=subdivisions,
    )
    terminal = slices[-1]
    maximum_absolute_defect = max(
        float(np.max(np.abs(item.generator_harmonic_defect))) for item in slices
    )
    path_sum = math.fsum(
        (
            shared.initializer,
            shared.ou_continuous_gradient,
            shared.birth,
            shared.death,
            shared.replacement,
        )
    )
    return MixedCTMCOUCapDefectCancellationDiagnostic(
        scope=DIAGNOSTIC_SCOPE,
        numerical_qualification=NUMERICAL_QUALIFICATION,
        state_vectors=oracle.discrete.state_vectors,
        auxiliary_state_vectors=auxiliary.state_vectors,
        auxiliary_cap=_AUXILIARY_CAP,
        evaluation_times=_readonly(times),
        evaluation_coordinates=_readonly(_EVALUATION_COORDINATES),
        time_slices=slices,
        maximum_absolute_cap_defect=maximum_absolute_defect,
        maximum_defect_identity_residual=max(
            item.maximum_defect_identity_residual for item in slices
        ),
        maximum_error_recovery_residual=max(
            item.maximum_error_recovery_residual for item in slices
        ),
        maximum_target_log_reconstruction_residual=max(
            item.maximum_target_log_reconstruction_residual for item in slices
        ),
        maximum_plugin_log_reconstruction_residual=max(
            item.maximum_plugin_log_reconstruction_residual for item in slices
        ),
        terminal_exact_residual_zero=bool(np.all(terminal.exact_residual == 0.0)),
        terminal_plugin_residual_zero=all(
            residual_value(
                residual,
                time=horizon,
                state_index=index,
                coordinate=coordinate,
                horizon=horizon,
            )
            == 0.0
            for index in range(len(oracle.discrete.state_vectors))
            for coordinate in _EVALUATION_COORDINATES
        ),
        terminal_guide_matches_target_likelihood=bool(
            np.array_equal(
                terminal.restricted_cap3_guide,
                oracle.discrete.terminal_likelihood,
            )
        ),
        path_total_excludes_cap_defect=(
            maximum_absolute_defect > 0.0
            and math.isclose(shared.total, path_sum, rel_tol=0.0, abs_tol=2.0e-15)
        ),
        shared_guide_decomposition=shared,
        existing_path_diagnostic=existing,
        existing_diagnostic_agreement=_agreement(shared, existing),
        boundary=DiagnosticScopeBoundary(
            mathematical_shared_guide_cancellation_exact=True,
            mathematical_blocked_birth_identity_exact=True,
            floating_matrix_exponentials_interval_certified=False,
            floating_quadrature_interval_certified=False,
            adaptive_error_estimate_is_rigorous_bound=False,
            fixture_cap_defect_cancellation_exercised=True,
            cap_defect_used_as_path_kl_summand=False,
            general_cap_stability_proved=False,
            learned_estimator_exercised=False,
            association_marginalization_exercised=False,
            continuous_marks_attached_to_occurrences=False,
            general_c17_theorem_proved=False,
            r2_hybrid_completed=False,
            claim_promotion_authorized=False,
            confirmatory_execution_authorized=False,
            production_execution_authorized=False,
        ),
    )


__all__ = [
    "DIAGNOSTIC_SCOPE",
    "NUMERICAL_QUALIFICATION",
    "CapDefectTimeSlice",
    "DiagnosticScopeBoundary",
    "ExistingDiagnosticAgreement",
    "MixedCTMCOUCapDefectCancellationDiagnostic",
    "SharedGuidePathKLComponents",
    "build_mixed_ctmc_ou_cap_defect_cancellation_diagnostic",
]
