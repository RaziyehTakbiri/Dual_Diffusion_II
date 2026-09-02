"""Small exact/certified known-law oracle for a factorized mixed process.

The reference process is the independent product of

* a capped two-type finite counting CTMC with birth, death, and type-changing
  replacement edges; and
* a scalar Ornstein--Uhlenbeck diffusion.

The terminal likelihood is a strictly positive product of a count likelihood
and a noisy Gaussian observation of the OU coordinate.  This makes the
finite-horizon information function, initial tilt, endpoint law, jump-rate
tilt, and continuous drift correction available in closed form.  The finite
CTMC transition is additionally reconstructed by uniformization with an
explicit Poisson-tail remainder.

This module is intentionally a small falsification oracle.  Its factorized
observation does not exercise association marginalization, continuous marks
attached to individual occurrences, or a learned residual.  Numerical
tolerances and pass/fail checks are diagnostics only: they do not promote a
manuscript claim, close the mixed known-law gate, or authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Tuple

import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import gammainc

from heterodiff.theory.finite_atomic_counting import (
    FiniteAtomicCountingSpace,
    capped_counting_reference,
    finite_atomic_birth_generator,
    finite_atomic_death_generator,
    finite_atomic_replacement_generator,
)
from heterodiff.theory.finite_state import (
    combine_generators,
    transition_matrix,
    validate_generator,
    validate_probability_vector,
)
from heterodiff.theory.path_kl import information_tilt_generator


ORACLE_SCOPE = "FINITE_FACTORIZED_MIXED_CTMC_OU_DIAGNOSTIC"
DIAGNOSTIC_TOLERANCE_ROLE = "NUMERICAL_DIAGNOSTIC_ONLY"
CLAIM_PROMOTION_EFFECT = "NONE"

_MAX_UNIFORMIZATION_TERMS = 100_000
_DEFAULT_UNIFORMIZATION_TAIL_TOLERANCE = 1.0e-14
_DEFAULT_DIAGNOSTIC_ABSOLUTE_TOLERANCE = 2.0e-9


def _readonly(value: object) -> np.ndarray:
    array = np.array(value, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(array.tobytes(order="C"), dtype=np.float64).reshape(
        array.shape
    )


def _real(
    value: object,
    *,
    name: str,
    minimum: float,
    strict: bool = False,
) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite" % name)
    if result < minimum or (strict and result == minimum):
        qualifier = "greater than" if strict else "at least"
        raise ValueError("%s must be %s %g" % (name, qualifier, minimum))
    return result


def _positive_integer(value: object, *, name: str, maximum: int) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result <= 0 or result > maximum:
        raise ValueError("%s must lie between 1 and %d" % (name, maximum))
    return result


@dataclass(frozen=True, eq=False)
class UniformizationCertificate:
    """Finite uniformization sum and its omitted Poisson mass.

    ``transition_lower`` is the nonnegative partial sum.  In exact arithmetic
    every entry of the true transition lies between that partial sum and
    ``transition_lower + poisson_tail_bound``.  ``roundoff_allowance`` is
    reported separately rather than being hidden inside the analytic tail.
    """

    uniformization_rate: float
    poisson_mean: float
    term_count: int
    final_poisson_index: int
    poisson_tail_bound: float
    roundoff_allowance: float
    transition_lower: np.ndarray
    row_mass_deficit: np.ndarray

    def __post_init__(self) -> None:
        rate = _real(
            self.uniformization_rate,
            name="uniformization_rate",
            minimum=0.0,
        )
        poisson_mean = _real(self.poisson_mean, name="poisson_mean", minimum=0.0)
        term_count = _positive_integer(
            self.term_count,
            name="term_count",
            maximum=_MAX_UNIFORMIZATION_TERMS,
        )
        index = (
            _positive_integer(
                self.final_poisson_index + 1,
                name="final_poisson_index plus one",
                maximum=_MAX_UNIFORMIZATION_TERMS,
            )
            - 1
        )
        if term_count != index + 1:
            raise ValueError("term_count must equal final_poisson_index + 1")
        tail = _real(
            self.poisson_tail_bound,
            name="poisson_tail_bound",
            minimum=0.0,
        )
        if tail > 1.0:
            raise ValueError("poisson_tail_bound must not exceed one")
        roundoff = _real(
            self.roundoff_allowance,
            name="roundoff_allowance",
            minimum=0.0,
        )
        transition = np.asarray(self.transition_lower, dtype=np.float64)
        if (
            transition.ndim != 2
            or transition.shape[0] != transition.shape[1]
            or not np.all(np.isfinite(transition))
            or np.any(transition < 0.0)
        ):
            raise ValueError(
                "transition_lower must be a finite nonnegative square matrix"
            )
        deficits = np.asarray(self.row_mass_deficit, dtype=np.float64)
        if deficits.shape != (transition.shape[0],):
            raise ValueError("row_mass_deficit must match the transition row count")
        if not np.all(np.isfinite(deficits)) or np.any(deficits < 0.0):
            raise ValueError("row_mass_deficit must be finite and nonnegative")
        object.__setattr__(self, "uniformization_rate", rate)
        object.__setattr__(self, "poisson_mean", poisson_mean)
        object.__setattr__(self, "term_count", term_count)
        object.__setattr__(self, "final_poisson_index", index)
        object.__setattr__(self, "poisson_tail_bound", tail)
        object.__setattr__(self, "roundoff_allowance", roundoff)
        object.__setattr__(self, "transition_lower", _readonly(transition))
        object.__setattr__(self, "row_mass_deficit", _readonly(deficits))


def uniformization_transition(
    generator: object,
    horizon: object,
    *,
    tail_tolerance: object = _DEFAULT_UNIFORMIZATION_TAIL_TOLERANCE,
    maximum_terms: object = _MAX_UNIFORMIZATION_TERMS,
) -> UniformizationCertificate:
    """Reconstruct ``exp(horizon * Q)`` by a bounded uniformization series."""

    matrix = validate_generator(np.asarray(generator))
    duration = _real(horizon, name="horizon", minimum=0.0)
    tolerance = _real(
        tail_tolerance,
        name="tail_tolerance",
        minimum=0.0,
        strict=True,
    )
    if tolerance >= 1.0:
        raise ValueError("tail_tolerance must be smaller than one")
    term_limit = _positive_integer(
        maximum_terms,
        name="maximum_terms",
        maximum=_MAX_UNIFORMIZATION_TERMS,
    )
    state_count = matrix.shape[0]
    rate = float(np.max(-np.diag(matrix)))
    if rate == 0.0 or duration == 0.0:
        identity = np.eye(state_count, dtype=np.float64)
        return UniformizationCertificate(
            uniformization_rate=rate,
            poisson_mean=0.0,
            term_count=1,
            final_poisson_index=0,
            poisson_tail_bound=0.0,
            roundoff_allowance=0.0,
            transition_lower=identity,
            row_mass_deficit=np.zeros(state_count, dtype=np.float64),
        )

    embedded = np.eye(state_count, dtype=np.float64) + matrix / rate
    roundoff_scale = 256.0 * np.finfo(np.float64).eps
    if np.any(embedded < -roundoff_scale) or not np.allclose(
        embedded.sum(axis=1), 1.0, atol=roundoff_scale, rtol=0.0
    ):
        raise ArithmeticError("uniformization embedded chain is not stochastic")
    embedded = np.where(embedded < 0.0, 0.0, embedded)
    raw_embedded = embedded.copy()
    embedded /= embedded.sum(axis=1, keepdims=True)
    embedded_adjustment = float(np.max(np.abs(embedded - raw_embedded)))
    if embedded_adjustment > roundoff_scale * float(state_count + 1):
        raise ArithmeticError(
            "uniformization embedded-chain normalization exceeded the "
            "declared floating-point roundoff budget"
        )

    poisson_mean = rate * duration
    if not math.isfinite(poisson_mean):
        raise ValueError("uniformization rate times horizon is not finite")
    poisson_index = 0
    poisson_weight = math.exp(-poisson_mean)
    if poisson_weight < float(np.finfo(np.float64).tiny):
        raise ArithmeticError(
            "initial Poisson weight is subnormal or underflowed; no "
            "uniformization enclosure is returned"
        )
    power = np.eye(state_count, dtype=np.float64)
    partial = poisson_weight * power
    tail = float(gammainc(1, poisson_mean))
    while tail > tolerance:
        if poisson_index + 1 >= term_limit:
            raise RuntimeError(
                "uniformization did not reach the requested tail tolerance "
                "within maximum_terms"
            )
        poisson_index += 1
        poisson_weight *= poisson_mean / float(poisson_index)
        power = power @ embedded
        partial += poisson_weight * power
        tail = float(gammainc(poisson_index + 1, poisson_mean))

    if not np.all(np.isfinite(partial)) or np.any(partial < 0.0):
        raise ArithmeticError("uniformization partial sum is invalid")
    deficits = 1.0 - partial.sum(axis=1)
    allowance = roundoff_scale * float(poisson_index + 1) * float(state_count + 1)
    if np.any(deficits < -allowance):
        raise ArithmeticError("uniformization partial sum exceeded unit row mass")
    deficits = np.where(deficits < 0.0, 0.0, deficits)
    if np.any(deficits > tail + allowance):
        raise ArithmeticError(
            "uniformization lost row mass beyond the analytic tail and "
            "floating-point allowance"
        )
    return UniformizationCertificate(
        uniformization_rate=rate,
        poisson_mean=poisson_mean,
        term_count=poisson_index + 1,
        final_poisson_index=poisson_index,
        poisson_tail_bound=tail,
        roundoff_allowance=allowance,
        transition_lower=partial,
        row_mass_deficit=deficits,
    )


@dataclass(frozen=True)
class OUParameters:
    """Scalar OU reference and one noisy terminal observation."""

    mean_reversion: float
    long_run_mean: float
    diffusion: float
    initial_mean: float
    initial_variance: float
    observation_value: float
    observation_variance: float
    horizon: float

    def __post_init__(self) -> None:
        for name in (
            "mean_reversion",
            "diffusion",
            "initial_variance",
            "observation_variance",
            "horizon",
        ):
            object.__setattr__(
                self,
                name,
                _real(getattr(self, name), name=name, minimum=0.0, strict=True),
            )
        for name in ("long_run_mean", "initial_mean", "observation_value"):
            object.__setattr__(
                self,
                name,
                _real(getattr(self, name), name=name, minimum=-math.inf),
            )


def _ou_decay(parameters: OUParameters, elapsed_time: float) -> float:
    return math.exp(-parameters.mean_reversion * elapsed_time)


def _ou_transition_variance(parameters: OUParameters, elapsed_time: float) -> float:
    return (
        parameters.diffusion**2
        * -math.expm1(-2.0 * parameters.mean_reversion * elapsed_time)
        / (2.0 * parameters.mean_reversion)
    )


def _ou_base_marginal(parameters: OUParameters, time: float) -> Tuple[float, float]:
    decay = _ou_decay(parameters, time)
    mean = parameters.long_run_mean + decay * (
        parameters.initial_mean - parameters.long_run_mean
    )
    variance = decay * decay * parameters.initial_variance + _ou_transition_variance(
        parameters, time
    )
    return mean, variance


def _normal_log_density(value: float, mean: float, variance: float) -> float:
    result = -0.5 * (
        math.log(2.0 * math.pi * variance) + (value - mean) ** 2 / variance
    )
    if not math.isfinite(result):
        raise ArithmeticError("normal log density is not representable")
    return result


def _normal_density(value: float, mean: float, variance: float) -> float:
    result = math.exp(_normal_log_density(value, mean, variance))
    if result == 0.0 or not math.isfinite(result):
        raise ArithmeticError(
            "positive normal density is not representable; use its log form"
        )
    return result


def _ou_checked_time(parameters: OUParameters, time: object) -> float:
    if not isinstance(parameters, OUParameters):
        raise TypeError("parameters must be an OUParameters instance")
    checked = _real(time, name="time", minimum=0.0)
    if checked > parameters.horizon:
        raise ValueError("time must not exceed the OU horizon")
    return checked


def ou_backward_information(
    parameters: OUParameters, time: object, coordinate: object
) -> float:
    """Return ``E[g(X_T) | X_t=x]`` for the Gaussian terminal likelihood."""

    result = math.exp(ou_log_backward_information(parameters, time, coordinate))
    if result == 0.0 or not math.isfinite(result):
        raise ArithmeticError(
            "positive OU backward information is not representable; "
            "use ou_log_backward_information"
        )
    return result


def ou_log_backward_information(
    parameters: OUParameters, time: object, coordinate: object
) -> float:
    """Return the exact log information without positive-tail underflow."""

    if not isinstance(parameters, OUParameters):
        raise TypeError("parameters must be an OUParameters instance")
    checked_time = _ou_checked_time(parameters, time)
    x = _real(coordinate, name="coordinate", minimum=-math.inf)
    remaining = parameters.horizon - checked_time
    decay = _ou_decay(parameters, remaining)
    predicted_mean = parameters.long_run_mean + decay * (x - parameters.long_run_mean)
    variance = (
        _ou_transition_variance(parameters, remaining) + parameters.observation_variance
    )
    return _normal_log_density(parameters.observation_value, predicted_mean, variance)


def ou_log_information_gradient(
    parameters: OUParameters, time: object, coordinate: object
) -> float:
    """Return the exact spatial derivative ``d/dx log h(t,x)``."""

    if not isinstance(parameters, OUParameters):
        raise TypeError("parameters must be an OUParameters instance")
    checked_time = _ou_checked_time(parameters, time)
    x = _real(coordinate, name="coordinate", minimum=-math.inf)
    remaining = parameters.horizon - checked_time
    decay = _ou_decay(parameters, remaining)
    predicted_mean = parameters.long_run_mean + decay * (x - parameters.long_run_mean)
    variance = (
        _ou_transition_variance(parameters, remaining) + parameters.observation_variance
    )
    return decay * (parameters.observation_value - predicted_mean) / variance


def ou_conditioned_drift(
    parameters: OUParameters, time: object, coordinate: object
) -> float:
    """Return the exact noisy-endpoint Doob drift of the OU coordinate."""

    checked_time = _ou_checked_time(parameters, time)
    x = _real(coordinate, name="coordinate", minimum=-math.inf)
    base = -parameters.mean_reversion * (x - parameters.long_run_mean)
    correction = parameters.diffusion**2 * ou_log_information_gradient(
        parameters, checked_time, x
    )
    return base + correction


def _ou_conditioned_drift_coefficients(
    parameters: OUParameters, time: float
) -> Tuple[float, float]:
    remaining = parameters.horizon - time
    decay = _ou_decay(parameters, remaining)
    variance = (
        _ou_transition_variance(parameters, remaining) + parameters.observation_variance
    )
    slope = -parameters.mean_reversion - (
        parameters.diffusion**2 * decay * decay / variance
    )
    intercept = (
        parameters.mean_reversion * parameters.long_run_mean
        + parameters.diffusion**2
        * decay
        * (parameters.observation_value - parameters.long_run_mean * (1.0 - decay))
        / variance
    )
    return slope, intercept


def _ou_conditioned_marginal(
    parameters: OUParameters, time: float
) -> Tuple[float, float]:
    mean, variance = _ou_base_marginal(parameters, time)
    terminal_mean, terminal_variance = _ou_base_marginal(parameters, parameters.horizon)
    remaining_decay = _ou_decay(parameters, parameters.horizon - time)
    covariance = variance * remaining_decay
    evidence_variance = terminal_variance + parameters.observation_variance
    innovation = parameters.observation_value - terminal_mean
    conditional_mean = mean + covariance * innovation / evidence_variance
    conditional_variance = variance - covariance * covariance / evidence_variance
    if conditional_variance <= 0.0 or not math.isfinite(conditional_variance):
        raise ArithmeticError("conditioned OU variance is not positive")
    return conditional_mean, conditional_variance


@dataclass(frozen=True, eq=False)
class DiscreteKnownLaw:
    state_vectors: Tuple[Tuple[int, int], ...]
    birth_generator: np.ndarray
    death_generator: np.ndarray
    replacement_generator: np.ndarray
    generator: np.ndarray
    initial_probabilities: np.ndarray
    terminal_likelihood: np.ndarray
    evidence: float
    backward_information_at_zero: np.ndarray
    tilted_initial_probabilities: np.ndarray
    conditional_terminal_probabilities: np.ndarray
    uniformization: UniformizationCertificate
    birth_edge_count: int
    death_edge_count: int
    replacement_edge_count: int
    enumerated_path_count: int
    maximum_path_log_ratio_residual: float
    backward_equation_residual: float
    endpoint_ode_l1_residual: float


@dataclass(frozen=True, eq=False)
class OUKnownLaw:
    parameters: OUParameters
    evidence: float
    tilted_initial_mean: float
    tilted_initial_variance: float
    conditional_terminal_mean: float
    conditional_terminal_variance: float
    endpoint_ode_mean_residual: float
    endpoint_ode_variance_residual: float
    maximum_moment_dynamics_residual: float
    maximum_backward_pde_residual: float


@dataclass(frozen=True, eq=False)
class MixedKnownLawDiagnostics:
    tolerance_role: str
    absolute_tolerance: float
    absolute_tolerance_applied_to_any_decision: bool
    uniformization_tail_tolerance: float
    uniformization_certificate_scope: str
    claim_promotion_effect: str
    claim_promotion_authorized: bool
    production_execution_authorized: bool
    closes_mixed_known_law_gate: bool
    candidate_residual_exercised: bool
    path_kl_decomposition_exercised: bool
    cap_defect_cancellation_exercised: bool
    association_marginalization_exercised: bool
    continuous_marks_attached_to_occurrences: bool
    c17_exercised: bool


@dataclass(frozen=True, eq=False)
class MixedCTMCOUKnownLawOracle:
    """Complete finite diagnostic fixture and its no-claim boundary."""

    scope: str
    factorized_reference_process: bool
    factorized_terminal_likelihood: bool
    discrete: DiscreteKnownLaw
    continuous: OUKnownLaw
    mixed_evidence: float
    diagnostics: MixedKnownLawDiagnostics


def _discrete_information(
    generator: np.ndarray,
    likelihood: np.ndarray,
    horizon: float,
    time: float,
) -> np.ndarray:
    return transition_matrix(generator, horizon - time) @ likelihood


def _discrete_conditional_terminal(
    initial: np.ndarray,
    generator: np.ndarray,
    likelihood: np.ndarray,
    horizon: float,
    evidence: float,
) -> np.ndarray:
    terminal = initial @ transition_matrix(generator, horizon)
    return validate_probability_vector(
        terminal * likelihood / evidence,
        generator.shape[0],
        atol=1.0e-11,
    )


def _count_edges(component: np.ndarray) -> int:
    off_diagonal = np.array(component, copy=True)
    np.fill_diagonal(off_diagonal, 0.0)
    return int(np.count_nonzero(off_diagonal > 0.0))


def _enumerated_discrete_path_residual(
    initial: np.ndarray,
    tilted_initial: np.ndarray,
    generator: np.ndarray,
    likelihood: np.ndarray,
    horizon: float,
    evidence: float,
) -> Tuple[int, float]:
    state_count = generator.shape[0]
    outgoing = tuple(
        tuple(
            int(destination)
            for destination in np.flatnonzero(generator[source] > 0.0)
            if int(destination) != source
        )
        for source in range(state_count)
    )
    paths = []
    for state in range(state_count):
        paths.append(((state,), ()))
    for source in range(state_count):
        for destination in outgoing[source]:
            paths.append(((source, destination), (0.37 * horizon,)))
            for second_destination in outgoing[destination]:
                paths.append(
                    (
                        (source, destination, second_destination),
                        (0.29 * horizon, 0.71 * horizon),
                    )
                )

    maximum = 0.0
    for state_path, jump_times in paths:
        initial_state = state_path[0]
        log_ratio = math.log(
            float(tilted_initial[initial_state]) / float(initial[initial_state])
        )
        for jump_time, source, destination in zip(
            jump_times, state_path[:-1], state_path[1:]
        ):
            information = _discrete_information(
                generator, likelihood, horizon, jump_time
            )
            tilted = information_tilt_generator(generator, np.log(information))
            log_ratio += math.log(
                float(tilted[source, destination])
                / float(generator[source, destination])
            )

        interval_starts = (0.0,) + tuple(jump_times)
        interval_ends = tuple(jump_times) + (horizon,)
        compensator_difference = 0.0
        for state, start, end in zip(state_path, interval_starts, interval_ends):
            start_h = float(
                _discrete_information(generator, likelihood, horizon, start)[state]
            )
            end_h = float(
                _discrete_information(generator, likelihood, horizon, end)[state]
            )
            compensator_difference += math.log(start_h) - math.log(end_h)
        log_ratio -= compensator_difference
        expected = math.log(float(likelihood[state_path[-1]])) - math.log(evidence)
        maximum = max(maximum, abs(log_ratio - expected))
    return len(paths), maximum


def _discrete_backward_residual(
    generator: np.ndarray,
    likelihood: np.ndarray,
    horizon: float,
) -> float:
    maximum = 0.0
    step = 1.0e-5 * horizon
    for time in (0.2 * horizon, 0.5 * horizon, 0.8 * horizon):
        left = _discrete_information(generator, likelihood, horizon, time - step)
        right = _discrete_information(generator, likelihood, horizon, time + step)
        center = _discrete_information(generator, likelihood, horizon, time)
        derivative = (right - left) / (2.0 * step)
        residual = derivative + generator @ center
        maximum = max(maximum, float(np.max(np.abs(residual))))
    return maximum


def _discrete_endpoint_ode_residual(
    initial: np.ndarray,
    generator: np.ndarray,
    likelihood: np.ndarray,
    horizon: float,
    conditional_terminal: np.ndarray,
) -> float:
    information_at_zero = _discrete_information(generator, likelihood, horizon, 0.0)
    evidence = float(initial @ information_at_zero)
    tilted_initial = initial * information_at_zero / evidence

    def derivative(time: float, marginal: np.ndarray) -> np.ndarray:
        information = _discrete_information(generator, likelihood, horizon, float(time))
        tilted = information_tilt_generator(generator, np.log(information))
        return marginal @ tilted

    solution = solve_ivp(
        derivative,
        (0.0, horizon),
        tilted_initial,
        method="DOP853",
        rtol=2.0e-12,
        atol=2.0e-14,
    )
    if not solution.success:
        raise ArithmeticError("conditioned CTMC endpoint integration failed")
    endpoint = solution.y[:, -1]
    return float(np.sum(np.abs(endpoint - conditional_terminal)))


def _ou_known_law(parameters: OUParameters) -> OUKnownLaw:
    terminal_mean, terminal_variance = _ou_base_marginal(parameters, parameters.horizon)
    evidence_variance = terminal_variance + parameters.observation_variance
    evidence = _normal_density(
        parameters.observation_value, terminal_mean, evidence_variance
    )
    tilted_initial_mean, tilted_initial_variance = _ou_conditioned_marginal(
        parameters, 0.0
    )
    conditional_terminal_mean, conditional_terminal_variance = _ou_conditioned_marginal(
        parameters, parameters.horizon
    )

    def moment_derivative(time: float, moments: np.ndarray) -> np.ndarray:
        slope, intercept = _ou_conditioned_drift_coefficients(parameters, time)
        return np.asarray(
            [
                slope * moments[0] + intercept,
                2.0 * slope * moments[1] + parameters.diffusion**2,
            ],
            dtype=np.float64,
        )

    solution = solve_ivp(
        moment_derivative,
        (0.0, parameters.horizon),
        np.asarray([tilted_initial_mean, tilted_initial_variance]),
        method="DOP853",
        rtol=2.0e-12,
        atol=2.0e-14,
    )
    if not solution.success:
        raise ArithmeticError("conditioned OU moment integration failed")
    endpoint_mean_residual = abs(float(solution.y[0, -1]) - conditional_terminal_mean)
    endpoint_variance_residual = abs(
        float(solution.y[1, -1]) - conditional_terminal_variance
    )

    maximum_moment_residual = 0.0
    delta_y = parameters.observation_value - terminal_mean
    evidence_variance = terminal_variance + parameters.observation_variance
    for time in (0.15, 0.4, 0.75):
        direct_time = time * parameters.horizon
        mean, variance = _ou_base_marginal(parameters, direct_time)
        mean_derivative = -parameters.mean_reversion * (mean - parameters.long_run_mean)
        variance_derivative = (
            -2.0 * parameters.mean_reversion * variance + parameters.diffusion**2
        )
        remaining_decay = _ou_decay(parameters, parameters.horizon - direct_time)
        covariance = variance * remaining_decay
        covariance_derivative = remaining_decay * (
            variance_derivative + parameters.mean_reversion * variance
        )
        conditional_mean = mean + covariance * delta_y / evidence_variance
        conditional_variance = variance - covariance**2 / evidence_variance
        exact_mean_derivative = (
            mean_derivative + covariance_derivative * delta_y / evidence_variance
        )
        exact_variance_derivative = (
            variance_derivative
            - 2.0 * covariance * covariance_derivative / evidence_variance
        )
        slope, intercept = _ou_conditioned_drift_coefficients(parameters, direct_time)
        maximum_moment_residual = max(
            maximum_moment_residual,
            abs(exact_mean_derivative - (slope * conditional_mean + intercept)),
            abs(
                exact_variance_derivative
                - (2.0 * slope * conditional_variance + parameters.diffusion**2)
            ),
        )

    maximum_pde_residual = 0.0
    time_step = 1.0e-5 * parameters.horizon
    for direct_time in (0.2 * parameters.horizon, 0.6 * parameters.horizon):
        for coordinate in (-0.7, 0.15, 1.1):
            left = ou_backward_information(
                parameters, direct_time - time_step, coordinate
            )
            right = ou_backward_information(
                parameters, direct_time + time_step, coordinate
            )
            value = ou_backward_information(parameters, direct_time, coordinate)
            time_derivative = (right - left) / (2.0 * time_step)
            remaining = parameters.horizon - direct_time
            remaining_decay = _ou_decay(parameters, remaining)
            predicted_mean = parameters.long_run_mean + remaining_decay * (
                coordinate - parameters.long_run_mean
            )
            conditional_variance = (
                _ou_transition_variance(parameters, remaining)
                + parameters.observation_variance
            )
            innovation = parameters.observation_value - predicted_mean
            gradient_log = remaining_decay * innovation / conditional_variance
            second_over_value = remaining_decay**2 * (
                innovation**2 / conditional_variance**2 - 1.0 / conditional_variance
            )
            base_drift = -parameters.mean_reversion * (
                coordinate - parameters.long_run_mean
            )
            generator_value = value * (
                base_drift * gradient_log
                + 0.5 * parameters.diffusion**2 * second_over_value
            )
            maximum_pde_residual = max(
                maximum_pde_residual,
                abs(time_derivative + generator_value),
            )

    return OUKnownLaw(
        parameters=parameters,
        evidence=evidence,
        tilted_initial_mean=tilted_initial_mean,
        tilted_initial_variance=tilted_initial_variance,
        conditional_terminal_mean=conditional_terminal_mean,
        conditional_terminal_variance=conditional_terminal_variance,
        endpoint_ode_mean_residual=endpoint_mean_residual,
        endpoint_ode_variance_residual=endpoint_variance_residual,
        maximum_moment_dynamics_residual=maximum_moment_residual,
        maximum_backward_pde_residual=maximum_pde_residual,
    )


def build_mixed_ctmc_ou_known_law_oracle(
    *,
    uniformization_tail_tolerance: object = (_DEFAULT_UNIFORMIZATION_TAIL_TOLERANCE),
    diagnostic_absolute_tolerance: object = (_DEFAULT_DIAGNOSTIC_ABSOLUTE_TOLERANCE),
) -> MixedCTMCOUKnownLawOracle:
    """Build the fixed two-type CTMC and scalar-OU diagnostic fixture.

    ``diagnostic_absolute_tolerance`` is retained as caller-supplied metadata
    for a future comparison record.  This partial oracle makes no pass/fail
    decision from it, and changing it cannot close a gate or promote a claim.
    """

    tail_tolerance = _real(
        uniformization_tail_tolerance,
        name="uniformization_tail_tolerance",
        minimum=0.0,
        strict=True,
    )
    if tail_tolerance >= 1.0:
        raise ValueError("uniformization_tail_tolerance must be smaller than one")
    diagnostic_tolerance = _real(
        diagnostic_absolute_tolerance,
        name="diagnostic_absolute_tolerance",
        minimum=0.0,
        strict=True,
    )

    horizon = 0.8
    space = FiniteAtomicCountingSpace(("alpha", "beta"), total_cap=2)
    birth = finite_atomic_birth_generator(space, (0.7, 0.4))
    death = finite_atomic_death_generator(space, (0.5, 0.3))
    replacement = finite_atomic_replacement_generator(
        space,
        np.asarray([[0.0, 0.2], [0.35, 0.0]], dtype=np.float64),
    )
    generator = combine_generators(birth, death, replacement)
    initial = capped_counting_reference(space, (0.8, 1.1))
    likelihood = np.asarray(
        [
            1.0 + 0.75 * alpha + 0.4 * beta + 0.2 * alpha * beta
            for alpha, beta in space.states
        ],
        dtype=np.float64,
    )
    transition = transition_matrix(generator, horizon)
    information_at_zero = transition @ likelihood
    evidence = float(initial @ information_at_zero)
    tilted_initial = validate_probability_vector(
        initial * information_at_zero / evidence,
        space.n_states,
        atol=1.0e-12,
    )
    conditional_terminal = _discrete_conditional_terminal(
        initial, generator, likelihood, horizon, evidence
    )
    uniformization = uniformization_transition(
        generator,
        horizon,
        tail_tolerance=tail_tolerance,
    )
    path_count, path_residual = _enumerated_discrete_path_residual(
        initial,
        tilted_initial,
        generator,
        likelihood,
        horizon,
        evidence,
    )
    discrete = DiscreteKnownLaw(
        state_vectors=tuple(space.states),
        birth_generator=_readonly(birth),
        death_generator=_readonly(death),
        replacement_generator=_readonly(replacement),
        generator=_readonly(generator),
        initial_probabilities=_readonly(initial),
        terminal_likelihood=_readonly(likelihood),
        evidence=evidence,
        backward_information_at_zero=_readonly(information_at_zero),
        tilted_initial_probabilities=_readonly(tilted_initial),
        conditional_terminal_probabilities=_readonly(conditional_terminal),
        uniformization=uniformization,
        birth_edge_count=_count_edges(birth),
        death_edge_count=_count_edges(death),
        replacement_edge_count=_count_edges(replacement),
        enumerated_path_count=path_count,
        maximum_path_log_ratio_residual=path_residual,
        backward_equation_residual=_discrete_backward_residual(
            generator, likelihood, horizon
        ),
        endpoint_ode_l1_residual=_discrete_endpoint_ode_residual(
            initial,
            generator,
            likelihood,
            horizon,
            conditional_terminal,
        ),
    )

    ou_parameters = OUParameters(
        mean_reversion=0.9,
        long_run_mean=-0.2,
        diffusion=0.7,
        initial_mean=0.35,
        initial_variance=0.6,
        observation_value=0.8,
        observation_variance=0.25,
        horizon=horizon,
    )
    continuous = _ou_known_law(ou_parameters)
    diagnostics = MixedKnownLawDiagnostics(
        tolerance_role=DIAGNOSTIC_TOLERANCE_ROLE,
        absolute_tolerance=diagnostic_tolerance,
        absolute_tolerance_applied_to_any_decision=False,
        uniformization_tail_tolerance=tail_tolerance,
        uniformization_certificate_scope=(
            "ANALYTIC_POISSON_TRUNCATION_TAIL_WITH_SEPARATE_FLOATING_ROUNDOFF"
        ),
        claim_promotion_effect=CLAIM_PROMOTION_EFFECT,
        claim_promotion_authorized=False,
        production_execution_authorized=False,
        closes_mixed_known_law_gate=False,
        candidate_residual_exercised=False,
        path_kl_decomposition_exercised=False,
        cap_defect_cancellation_exercised=False,
        association_marginalization_exercised=False,
        continuous_marks_attached_to_occurrences=False,
        c17_exercised=False,
    )
    return MixedCTMCOUKnownLawOracle(
        scope=ORACLE_SCOPE,
        factorized_reference_process=True,
        factorized_terminal_likelihood=True,
        discrete=discrete,
        continuous=continuous,
        mixed_evidence=discrete.evidence * continuous.evidence,
        diagnostics=diagnostics,
    )


__all__ = [
    "CLAIM_PROMOTION_EFFECT",
    "DIAGNOSTIC_TOLERANCE_ROLE",
    "DiscreteKnownLaw",
    "MixedCTMCOUKnownLawOracle",
    "MixedKnownLawDiagnostics",
    "ORACLE_SCOPE",
    "OUKnownLaw",
    "OUParameters",
    "UniformizationCertificate",
    "build_mixed_ctmc_ou_known_law_oracle",
    "ou_backward_information",
    "ou_conditioned_drift",
    "ou_log_backward_information",
    "ou_log_information_gradient",
    "uniformization_transition",
]
