"""Finite mixed CTMC--OU direct path-KL diagnostic.

This module adds a terminal-matched residual perturbation to the factorized
known-law fixture in :mod:`mixed_ctmc_ou_known_law_oracle`.  For that finite
fixture, the classical change-of-measure identity gives

``KL(P_exact || P_plugin)`` as the sum of

* the normalized-initializer relative entropy;
* the OU continuous-gradient energy; and
* separate birth, death, and replacement Poisson-Bregman integrals.

The identity is exact for the stated ideal path laws.  The reported jump
integrals are ordinary floating-point adaptive quadrature with non-rigorous
error estimates; they are not interval-certified values.  A fixed-order
Gauss--Legendre calculation using the direct Poisson-rate divergence provides
an independent numerical cross-check.

This is only a small factorized falsification fixture.  It does not prove the
general C17 theorem, complete R2-HYBRID, promote any claim, or authorize
confirmatory or production execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Callable, Tuple
import warnings

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.integrate import IntegrationWarning, quad, solve_ivp
from scipy.special import logsumexp

from heterodiff.evaluation.mixed_ctmc_ou_known_law_oracle import (
    MixedCTMCOUKnownLawOracle,
    build_mixed_ctmc_ou_known_law_oracle,
)
from heterodiff.theory.finite_state import transition_matrix


DIAGNOSTIC_SCOPE = "FINITE_FACTORIZED_MIXED_CTMC_OU_DIRECT_PATH_KL"
FORWARD_ORIENTATION = "KL(P_EXACT_H || P_PLUGIN_H_EXP_E)"
REVERSE_ORIENTATION = "KL(P_PLUGIN_H_EXP_E || P_EXACT_H)"
NUMERICAL_QUALIFICATION = (
    "EXACT_MATHEMATICAL_IDENTITY_WITH_FLOAT_QUADRATURE_NOT_INTERVAL_CERTIFIED"
)

_STATE_POTENTIALS = (0.0, -0.55, 0.8, 0.95, -0.3, 1.25)
_MAX_ABSOLUTE_JUMP_LOG_TILT = 100.0
_MAX_QUADRATURE_SUBDIVISIONS = 10_000
_MIN_GAUSS_LEGENDRE_ORDER = 8
_MAX_GAUSS_LEGENDRE_ORDER = 512


def _real(value: object, *, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("%s must be a real non-boolean number" % name)
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("%s must be finite" % name)
    return result


def _positive_real(value: object, *, name: str) -> float:
    result = _real(value, name=name)
    if result <= 0.0:
        raise ValueError("%s must be greater than zero" % name)
    return result


def _bounded_integer(value: object, *, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("%s must be an integer non-boolean value" % name)
    result = int(value)
    if result < minimum or result > maximum:
        raise ValueError("%s must lie between %d and %d" % (name, minimum, maximum))
    return result


def _readonly(value: object) -> np.ndarray:
    array = np.array(value, dtype=np.float64, copy=True, order="C")
    return np.frombuffer(array.tobytes(order="C"), dtype=np.float64).reshape(
        array.shape
    )


def _nonnegative(value: float, *, name: str, tolerance: float = 1.0e-13) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ArithmeticError("%s is not finite" % name)
    if result < -tolerance:
        raise ArithmeticError("%s is unexpectedly negative" % name)
    return max(0.0, result)


def _phi(value: float) -> float:
    """Return ``exp(value) - 1 - value`` without small-value cancellation."""

    magnitude = abs(value)
    if magnitude < 1.0e-4:
        # Six terms leave an error far below binary64 roundoff at this cutoff.
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
    result = math.expm1(value) - value
    return _nonnegative(result, name="Poisson Bregman function")


@dataclass(frozen=True)
class TerminalMatchedResidual:
    """Affine, terminal-vanishing log residual used by the finite fixture.

    At time ``t`` and discrete state ``i``,

    ``e(t, i, x) = (1 - t/T) * (s*c[i] + beta*x + gamma)``.

    ``gamma`` is a state-independent, coordinate-independent gauge.  It
    changes raw residual values but cancels from the normalized initializer,
    the spatial gradient, and every jump increment.
    """

    discrete_scale: float = 0.65
    continuous_slope: float = -0.4
    gauge_scale: float = 0.3
    state_potentials: Tuple[float, ...] = _STATE_POTENTIALS

    def __post_init__(self) -> None:
        for name in ("discrete_scale", "continuous_slope", "gauge_scale"):
            object.__setattr__(self, name, _real(getattr(self, name), name=name))
        if type(self.state_potentials) is not tuple:
            raise TypeError("state_potentials must be a tuple")
        if len(self.state_potentials) != len(_STATE_POTENTIALS):
            raise ValueError("state_potentials must contain exactly six values")
        checked = tuple(
            _real(value, name="state_potentials[%d]" % index)
            for index, value in enumerate(self.state_potentials)
        )
        if not all(math.isfinite(value) for value in checked):
            raise ValueError("state_potentials must be finite")
        object.__setattr__(self, "state_potentials", checked)

    @property
    def non_gauge_perturbation_nonzero(self) -> bool:
        discrete_nonzero = self.discrete_scale != 0.0 and any(
            value != self.state_potentials[0] for value in self.state_potentials[1:]
        )
        return discrete_nonzero or self.continuous_slope != 0.0


def _checked_time(time: object, horizon: float) -> float:
    result = _real(time, name="time")
    if result < 0.0 or result > horizon:
        raise ValueError("time must lie in the closed diagnostic horizon")
    return result


def _checked_state_index(state_index: object) -> int:
    return _bounded_integer(
        state_index,
        name="state_index",
        minimum=0,
        maximum=len(_STATE_POTENTIALS) - 1,
    )


def residual_value(
    residual: TerminalMatchedResidual,
    *,
    time: object,
    state_index: object,
    coordinate: object,
    horizon: object,
) -> float:
    """Evaluate the fixture residual with fail-closed domain checks."""

    if not isinstance(residual, TerminalMatchedResidual):
        raise TypeError("residual must be a TerminalMatchedResidual instance")
    checked_horizon = _positive_real(horizon, name="horizon")
    checked_time = _checked_time(time, checked_horizon)
    index = _checked_state_index(state_index)
    x = _real(coordinate, name="coordinate")
    envelope = 1.0 - checked_time / checked_horizon
    result = envelope * (
        residual.discrete_scale * residual.state_potentials[index]
        + residual.continuous_slope * x
        + residual.gauge_scale
    )
    if not math.isfinite(result):
        raise ArithmeticError("residual value is not representable")
    return result


def residual_spatial_gradient(
    residual: TerminalMatchedResidual, *, time: object, horizon: object
) -> float:
    """Return the exact OU-coordinate gradient of the residual."""

    if not isinstance(residual, TerminalMatchedResidual):
        raise TypeError("residual must be a TerminalMatchedResidual instance")
    checked_horizon = _positive_real(horizon, name="horizon")
    checked_time = _checked_time(time, checked_horizon)
    return (1.0 - checked_time / checked_horizon) * residual.continuous_slope


def residual_jump_increment(
    residual: TerminalMatchedResidual,
    *,
    time: object,
    source: object,
    destination: object,
    horizon: object,
) -> float:
    """Return ``e(t,destination,x)-e(t,source,x)``.

    The coordinate and gauge cancel analytically, so neither is an argument.
    """

    if not isinstance(residual, TerminalMatchedResidual):
        raise TypeError("residual must be a TerminalMatchedResidual instance")
    checked_horizon = _positive_real(horizon, name="horizon")
    checked_time = _checked_time(time, checked_horizon)
    source_index = _checked_state_index(source)
    destination_index = _checked_state_index(destination)
    result = (
        (1.0 - checked_time / checked_horizon)
        * residual.discrete_scale
        * (
            residual.state_potentials[destination_index]
            - residual.state_potentials[source_index]
        )
    )
    if not math.isfinite(result):
        raise ArithmeticError("jump residual increment is not representable")
    return result


@dataclass(frozen=True, eq=False)
class InitializerKLComponents:
    discrete_exact_to_plugin: float
    ou_exact_to_plugin: float
    total_exact_to_plugin: float
    discrete_plugin_to_exact: float
    ou_plugin_to_exact: float
    total_plugin_to_exact: float
    exact_discrete_probabilities: np.ndarray
    plugin_discrete_probabilities: np.ndarray
    exact_ou_mean: float
    plugin_ou_mean: float
    shared_ou_variance: float


@dataclass(frozen=True)
class JumpBregmanComponents:
    birth: float
    death: float
    replacement: float
    total: float
    birth_quadrature_error_estimate: float
    death_quadrature_error_estimate: float
    replacement_quadrature_error_estimate: float
    total_quadrature_error_estimate: float


@dataclass(frozen=True)
class PathKLComponents:
    initializer: InitializerKLComponents
    ou_continuous_gradient: float
    jumps: JumpBregmanComponents
    dynamic: float
    total: float


@dataclass(frozen=True)
class ReverseOrientationDiagnostic:
    orientation: str
    initializer: float
    ou_continuous_gradient: float
    birth: float
    death: float
    replacement: float
    dynamic: float
    total: float
    plugin_final_probability_mass_residual: float


@dataclass(frozen=True)
class IndependentNumericalCrossCheck:
    method: str
    initializer_direct_kl: float
    ou_closed_form: float
    birth_direct_poisson: float
    death_direct_poisson: float
    replacement_direct_poisson: float
    total: float
    absolute_difference_from_adaptive_total: float
    applied_to_any_gate_or_claim_decision: bool


@dataclass(frozen=True)
class NumericalControls:
    adaptive_absolute_tolerance: float
    adaptive_relative_tolerance: float
    adaptive_maximum_subdivisions: int
    gauss_legendre_order: int
    reverse_ode_relative_tolerance: float
    reverse_ode_absolute_tolerance: float


@dataclass(frozen=True)
class DiagnosticScopeBoundary:
    mathematical_path_kl_identity_exact: bool
    float_quadrature_interval_certified: bool
    adaptive_error_estimate_is_rigorous_bound: bool
    fixture_direct_gradient_quantity_exercised: bool
    fixture_direct_jump_edge_quantities_exercised: bool
    learned_estimator_exercised: bool
    association_marginalization_exercised: bool
    state_dependent_mark_dimension_exercised: bool
    cap_defect_cancellation_exercised: bool
    general_c17_theorem_proved: bool
    r2_hybrid_completed: bool
    claim_promotion_authorized: bool
    confirmatory_execution_authorized: bool
    production_execution_authorized: bool


@dataclass(frozen=True)
class MixedCTMCOUPathKLDiagnostic:
    scope: str
    numerical_qualification: str
    orientation: str
    state_vectors: Tuple[Tuple[int, int], ...]
    residual: TerminalMatchedResidual
    terminal_residual_exactly_zero: bool
    decomposition: PathKLComponents
    reverse_orientation: ReverseOrientationDiagnostic
    orientation_totals_distinct: bool
    crosscheck: IndependentNumericalCrossCheck
    numerical_controls: NumericalControls
    boundary: DiagnosticScopeBoundary


def _discrete_information(oracle: MixedCTMCOUKnownLawOracle, time: float) -> np.ndarray:
    discrete = oracle.discrete
    horizon = oracle.continuous.parameters.horizon
    result = transition_matrix(discrete.generator, horizon - time) @ (
        discrete.terminal_likelihood
    )
    if not np.all(np.isfinite(result)) or np.any(result <= 0.0):
        raise ArithmeticError("discrete backward information is not positive")
    return result


def _target_discrete_marginal_and_rates(
    oracle: MixedCTMCOUKnownLawOracle, time: float
) -> Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    discrete = oracle.discrete
    information = _discrete_information(oracle, time)
    base_marginal = discrete.initial_probabilities @ transition_matrix(
        discrete.generator, time
    )
    target_marginal = base_marginal * information / discrete.evidence
    mass = float(np.sum(target_marginal))
    if (
        not np.all(np.isfinite(target_marginal))
        or np.any(target_marginal < 0.0)
        or not math.isclose(mass, 1.0, rel_tol=0.0, abs_tol=2.0e-11)
    ):
        raise ArithmeticError("target discrete marginal is not a probability law")
    target_marginal = target_marginal / mass

    rates = []
    ratio = information[np.newaxis, :] / information[:, np.newaxis]
    for component in (
        discrete.birth_generator,
        discrete.death_generator,
        discrete.replacement_generator,
    ):
        off_diagonal = np.array(component, dtype=np.float64, copy=True)
        np.fill_diagonal(off_diagonal, 0.0)
        off_diagonal *= ratio
        if not np.all(np.isfinite(off_diagonal)) or np.any(off_diagonal < 0.0):
            raise ArithmeticError("target tilted jump rates are invalid")
        rates.append(off_diagonal)
    return target_marginal, (rates[0], rates[1], rates[2])


def _jump_integrand(
    oracle: MixedCTMCOUKnownLawOracle,
    residual: TerminalMatchedResidual,
    family_index: int,
    time: float,
    bregman: Callable[[float, float], float],
) -> float:
    marginal, rates = _target_discrete_marginal_and_rates(oracle, time)
    family = rates[family_index]
    horizon = oracle.continuous.parameters.horizon
    terms = []
    for source in range(family.shape[0]):
        for destination in range(family.shape[1]):
            rate = float(family[source, destination])
            if source == destination or rate == 0.0:
                continue
            increment = residual_jump_increment(
                residual,
                time=time,
                source=source,
                destination=destination,
                horizon=horizon,
            )
            terms.append(float(marginal[source]) * bregman(rate, increment))
    result = math.fsum(terms)
    return _nonnegative(result, name="jump KL integrand")


def _forward_bregman(rate: float, increment: float) -> float:
    return rate * _phi(increment)


def _direct_poisson_divergence(rate: float, increment: float) -> float:
    plugin_rate = rate * math.exp(increment)
    if not math.isfinite(plugin_rate) or plugin_rate <= 0.0:
        raise ArithmeticError("plugin jump rate is not representable")
    result = rate * math.log(rate / plugin_rate) - rate + plugin_rate
    tolerance = 128.0 * np.finfo(np.float64).eps * max(rate, plugin_rate)
    return _nonnegative(
        result, name="direct Poisson-rate divergence", tolerance=tolerance
    )


def _adaptive_integral(
    integrand: Callable[[float], float],
    horizon: float,
    *,
    absolute_tolerance: float,
    relative_tolerance: float,
    subdivisions: int,
) -> Tuple[float, float]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", IntegrationWarning)
            value, error = quad(
                integrand,
                0.0,
                horizon,
                epsabs=absolute_tolerance,
                epsrel=relative_tolerance,
                limit=subdivisions,
            )
    except (ArithmeticError, IntegrationWarning, ValueError) as exception:
        raise ArithmeticError("adaptive jump quadrature failed") from exception
    return (
        _nonnegative(value, name="adaptive jump integral"),
        _nonnegative(error, name="adaptive quadrature error estimate"),
    )


def _gauss_legendre_integral(
    integrand: Callable[[float], float], horizon: float, order: int
) -> float:
    nodes, weights = leggauss(order)
    scale = 0.5 * horizon
    values = [integrand(scale * (float(node) + 1.0)) for node in nodes]
    result = scale * math.fsum(
        float(weight) * value for weight, value in zip(weights, values)
    )
    return _nonnegative(result, name="Gauss-Legendre integral")


def _initializer_components(
    oracle: MixedCTMCOUKnownLawOracle,
    residual: TerminalMatchedResidual,
) -> InitializerKLComponents:
    exact = np.asarray(oracle.discrete.tilted_initial_probabilities)
    state_tilts = residual.discrete_scale * np.asarray(
        residual.state_potentials, dtype=np.float64
    )
    log_exact = np.log(exact)
    log_normalizer = float(logsumexp(log_exact + state_tilts))
    plugin = np.exp(log_exact + state_tilts - log_normalizer)
    plugin /= float(np.sum(plugin))
    if not np.all(np.isfinite(plugin)) or np.any(plugin <= 0.0):
        raise ArithmeticError("plugin discrete initializer is not positive")

    forward_discrete = math.fsum(
        float(probability) * (math.log(float(probability)) - math.log(float(candidate)))
        for probability, candidate in zip(exact, plugin)
    )
    reverse_discrete = math.fsum(
        float(candidate) * (math.log(float(candidate)) - math.log(float(probability)))
        for probability, candidate in zip(exact, plugin)
    )
    variance = oracle.continuous.tilted_initial_variance
    slope = residual.continuous_slope
    plugin_mean = oracle.continuous.tilted_initial_mean + variance * slope
    ou_kl = 0.5 * variance * slope * slope
    forward_discrete = _nonnegative(
        forward_discrete, name="forward discrete initializer KL"
    )
    reverse_discrete = _nonnegative(
        reverse_discrete, name="reverse discrete initializer KL"
    )
    ou_kl = _nonnegative(ou_kl, name="OU initializer KL")
    forward_total = math.fsum((forward_discrete, ou_kl))
    reverse_total = math.fsum((reverse_discrete, ou_kl))
    if not all(
        math.isfinite(value) for value in (plugin_mean, forward_total, reverse_total)
    ):
        raise ArithmeticError("initializer KL is not representable")
    return InitializerKLComponents(
        discrete_exact_to_plugin=forward_discrete,
        ou_exact_to_plugin=ou_kl,
        total_exact_to_plugin=forward_total,
        discrete_plugin_to_exact=reverse_discrete,
        ou_plugin_to_exact=ou_kl,
        total_plugin_to_exact=reverse_total,
        exact_discrete_probabilities=_readonly(exact),
        plugin_discrete_probabilities=_readonly(plugin),
        exact_ou_mean=oracle.continuous.tilted_initial_mean,
        plugin_ou_mean=plugin_mean,
        shared_ou_variance=variance,
    )


def _continuous_gradient_component(
    oracle: MixedCTMCOUKnownLawOracle,
    residual: TerminalMatchedResidual,
) -> float:
    parameters = oracle.continuous.parameters
    # 1/2 * sigma^2 * integral_0^T beta^2 (1-t/T)^2 dt.
    result = (
        parameters.diffusion**2
        * residual.continuous_slope**2
        * parameters.horizon
        / 6.0
    )
    return _nonnegative(result, name="OU continuous-gradient KL")


def _plugin_generator(
    oracle: MixedCTMCOUKnownLawOracle,
    residual: TerminalMatchedResidual,
    time: float,
) -> Tuple[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    _, target_families = _target_discrete_marginal_and_rates(oracle, time)
    plugin_families = []
    for target in target_families:
        plugin = np.zeros_like(target)
        for source in range(target.shape[0]):
            for destination in range(target.shape[1]):
                if source == destination or target[source, destination] == 0.0:
                    continue
                increment = residual_jump_increment(
                    residual,
                    time=time,
                    source=source,
                    destination=destination,
                    horizon=oracle.continuous.parameters.horizon,
                )
                plugin[source, destination] = target[source, destination] * math.exp(
                    increment
                )
        plugin_families.append(plugin)
    generator = sum(plugin_families, np.zeros_like(plugin_families[0]))
    np.fill_diagonal(generator, -np.sum(generator, axis=1))
    if not np.all(np.isfinite(generator)):
        raise ArithmeticError("plugin discrete generator is not finite")
    return generator, (
        plugin_families[0],
        plugin_families[1],
        plugin_families[2],
    )


def _reverse_orientation(
    oracle: MixedCTMCOUKnownLawOracle,
    residual: TerminalMatchedResidual,
    initializer: InitializerKLComponents,
    continuous: float,
) -> ReverseOrientationDiagnostic:
    state_count = len(oracle.discrete.state_vectors)
    initial = np.asarray(initializer.plugin_discrete_probabilities)

    def derivative(time: float, values: np.ndarray) -> np.ndarray:
        probabilities = values[:state_count]
        generator, plugin_families = _plugin_generator(oracle, residual, float(time))
        _, target_families = _target_discrete_marginal_and_rates(oracle, float(time))
        accumulators = []
        for target, plugin in zip(target_families, plugin_families):
            terms = []
            for source in range(state_count):
                for destination in range(state_count):
                    if source == destination or target[source, destination] == 0.0:
                        continue
                    target_rate = float(target[source, destination])
                    plugin_rate = float(plugin[source, destination])
                    value = (
                        plugin_rate * math.log(plugin_rate / target_rate)
                        - plugin_rate
                        + target_rate
                    )
                    terms.append(float(probabilities[source]) * value)
            accumulators.append(math.fsum(terms))
        return np.concatenate(
            (probabilities @ generator, np.asarray(accumulators, dtype=np.float64))
        )

    solution = solve_ivp(
        derivative,
        (0.0, oracle.continuous.parameters.horizon),
        np.concatenate((initial, np.zeros(3, dtype=np.float64))),
        method="DOP853",
        rtol=2.0e-11,
        atol=2.0e-13,
    )
    if not solution.success or not np.all(np.isfinite(solution.y[:, -1])):
        raise ArithmeticError("reverse-orientation diagnostic integration failed")
    endpoint = solution.y[:state_count, -1]
    mass_residual = abs(float(np.sum(endpoint)) - 1.0)
    if np.any(endpoint < -2.0e-10) or mass_residual > 2.0e-9:
        raise ArithmeticError("plugin occupancy integration left probability space")
    birth, death, replacement = (
        _nonnegative(float(value), name="reverse jump KL")
        for value in solution.y[state_count:, -1]
    )
    dynamic = math.fsum((continuous, birth, death, replacement))
    total = math.fsum((initializer.total_plugin_to_exact, dynamic))
    if not math.isfinite(total):
        raise ArithmeticError("reverse path KL is not representable")
    return ReverseOrientationDiagnostic(
        orientation=REVERSE_ORIENTATION,
        initializer=initializer.total_plugin_to_exact,
        ou_continuous_gradient=continuous,
        birth=birth,
        death=death,
        replacement=replacement,
        dynamic=dynamic,
        total=total,
        plugin_final_probability_mass_residual=mass_residual,
    )


def _validate_log_rate_tilts(residual: TerminalMatchedResidual) -> None:
    potentials = residual.state_potentials
    maximum_difference = max(
        abs(destination - source) for source in potentials for destination in potentials
    )
    maximum = abs(residual.discrete_scale) * maximum_difference
    if not math.isfinite(maximum) or maximum > _MAX_ABSOLUTE_JUMP_LOG_TILT:
        raise ValueError("residual jump log tilts exceed the finite diagnostic limit")


def build_mixed_ctmc_ou_path_kl_diagnostic(
    *,
    residual: TerminalMatchedResidual = TerminalMatchedResidual(),
    quadrature_absolute_tolerance: object = 1.0e-11,
    quadrature_relative_tolerance: object = 1.0e-11,
    quadrature_subdivisions: object = 200,
    gauss_legendre_order: object = 96,
) -> MixedCTMCOUPathKLDiagnostic:
    """Build the exact-to-plugin decomposition for the finite fixture.

    ``quad`` error estimates and the independent Gauss--Legendre comparison
    are numerical diagnostics only.  Neither is a rigorous interval proof or
    a gate/claim decision.
    """

    if not isinstance(residual, TerminalMatchedResidual):
        raise TypeError("residual must be a TerminalMatchedResidual instance")
    absolute_tolerance = _positive_real(
        quadrature_absolute_tolerance, name="quadrature_absolute_tolerance"
    )
    relative_tolerance = _positive_real(
        quadrature_relative_tolerance, name="quadrature_relative_tolerance"
    )
    subdivisions = _bounded_integer(
        quadrature_subdivisions,
        name="quadrature_subdivisions",
        minimum=1,
        maximum=_MAX_QUADRATURE_SUBDIVISIONS,
    )
    order = _bounded_integer(
        gauss_legendre_order,
        name="gauss_legendre_order",
        minimum=_MIN_GAUSS_LEGENDRE_ORDER,
        maximum=_MAX_GAUSS_LEGENDRE_ORDER,
    )
    _validate_log_rate_tilts(residual)

    oracle = build_mixed_ctmc_ou_known_law_oracle()
    horizon = oracle.continuous.parameters.horizon
    initializer = _initializer_components(oracle, residual)
    continuous = _continuous_gradient_component(oracle, residual)

    adaptive_values = []
    adaptive_errors = []
    fixed_values = []
    for family_index in range(3):
        forward = lambda time, family_index=family_index: _jump_integrand(
            oracle,
            residual,
            family_index,
            float(time),
            _forward_bregman,
        )
        value, error = _adaptive_integral(
            forward,
            horizon,
            absolute_tolerance=absolute_tolerance,
            relative_tolerance=relative_tolerance,
            subdivisions=subdivisions,
        )
        direct = lambda time, family_index=family_index: _jump_integrand(
            oracle,
            residual,
            family_index,
            float(time),
            _direct_poisson_divergence,
        )
        fixed = _gauss_legendre_integral(direct, horizon, order)
        adaptive_values.append(value)
        adaptive_errors.append(error)
        fixed_values.append(fixed)

    birth, death, replacement = adaptive_values
    birth_error, death_error, replacement_error = adaptive_errors
    jump_total = math.fsum(adaptive_values)
    jump_error = math.fsum(adaptive_errors)
    jumps = JumpBregmanComponents(
        birth=birth,
        death=death,
        replacement=replacement,
        total=jump_total,
        birth_quadrature_error_estimate=birth_error,
        death_quadrature_error_estimate=death_error,
        replacement_quadrature_error_estimate=replacement_error,
        total_quadrature_error_estimate=jump_error,
    )
    dynamic = math.fsum((continuous, jump_total))
    total = math.fsum((initializer.total_exact_to_plugin, dynamic))
    if not math.isfinite(total):
        raise ArithmeticError("forward path KL is not representable")
    decomposition = PathKLComponents(
        initializer=initializer,
        ou_continuous_gradient=continuous,
        jumps=jumps,
        dynamic=dynamic,
        total=total,
    )

    direct_initializer = (
        math.fsum(
            float(probability)
            * (math.log(float(probability)) - math.log(float(candidate)))
            for probability, candidate in zip(
                initializer.exact_discrete_probabilities,
                initializer.plugin_discrete_probabilities,
            )
        )
        + initializer.ou_exact_to_plugin
    )
    direct_total = math.fsum((direct_initializer, continuous, *fixed_values))
    crosscheck = IndependentNumericalCrossCheck(
        method=(
            "FIXED_GAUSS_LEGENDRE_WITH_DIRECT_POISSON_RATE_KL_AND_DIRECT_INITIAL_KL"
        ),
        initializer_direct_kl=_nonnegative(
            direct_initializer, name="cross-check initializer KL"
        ),
        ou_closed_form=continuous,
        birth_direct_poisson=fixed_values[0],
        death_direct_poisson=fixed_values[1],
        replacement_direct_poisson=fixed_values[2],
        total=direct_total,
        absolute_difference_from_adaptive_total=abs(direct_total - total),
        applied_to_any_gate_or_claim_decision=False,
    )
    reverse = _reverse_orientation(oracle, residual, initializer, continuous)

    terminal_zero = all(
        residual_value(
            residual,
            time=horizon,
            state_index=index,
            coordinate=coordinate,
            horizon=horizon,
        )
        == 0.0
        for index in range(len(_STATE_POTENTIALS))
        for coordinate in (-1.0, 0.0, 1.0)
    )
    return MixedCTMCOUPathKLDiagnostic(
        scope=DIAGNOSTIC_SCOPE,
        numerical_qualification=NUMERICAL_QUALIFICATION,
        orientation=FORWARD_ORIENTATION,
        state_vectors=oracle.discrete.state_vectors,
        residual=residual,
        terminal_residual_exactly_zero=terminal_zero,
        decomposition=decomposition,
        reverse_orientation=reverse,
        orientation_totals_distinct=not math.isclose(
            total, reverse.total, rel_tol=1.0e-10, abs_tol=1.0e-12
        ),
        crosscheck=crosscheck,
        numerical_controls=NumericalControls(
            adaptive_absolute_tolerance=absolute_tolerance,
            adaptive_relative_tolerance=relative_tolerance,
            adaptive_maximum_subdivisions=subdivisions,
            gauss_legendre_order=order,
            reverse_ode_relative_tolerance=2.0e-11,
            reverse_ode_absolute_tolerance=2.0e-13,
        ),
        boundary=DiagnosticScopeBoundary(
            mathematical_path_kl_identity_exact=True,
            float_quadrature_interval_certified=False,
            adaptive_error_estimate_is_rigorous_bound=False,
            fixture_direct_gradient_quantity_exercised=True,
            fixture_direct_jump_edge_quantities_exercised=True,
            learned_estimator_exercised=False,
            association_marginalization_exercised=False,
            state_dependent_mark_dimension_exercised=False,
            cap_defect_cancellation_exercised=False,
            general_c17_theorem_proved=False,
            r2_hybrid_completed=False,
            claim_promotion_authorized=False,
            confirmatory_execution_authorized=False,
            production_execution_authorized=False,
        ),
    )


__all__ = [
    "DIAGNOSTIC_SCOPE",
    "FORWARD_ORIENTATION",
    "NUMERICAL_QUALIFICATION",
    "REVERSE_ORIENTATION",
    "DiagnosticScopeBoundary",
    "IndependentNumericalCrossCheck",
    "InitializerKLComponents",
    "JumpBregmanComponents",
    "MixedCTMCOUPathKLDiagnostic",
    "NumericalControls",
    "PathKLComponents",
    "ReverseOrientationDiagnostic",
    "TerminalMatchedResidual",
    "build_mixed_ctmc_ou_path_kl_diagnostic",
    "residual_jump_increment",
    "residual_spatial_gradient",
    "residual_value",
]
