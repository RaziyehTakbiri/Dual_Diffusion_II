"""Population density-ratio controls for the finite bridge pilot.

This module deliberately implements a saturated tabular control.  A count
vector already quotients out occurrence order, so the table is invariant to
permutations of indistinguishable occurrences, but it is neither scalable nor
a candidate novelty contribution.  Its purpose is stricter: if this model
cannot recover the complete finite population optimum, the training
orientation or downstream bridge plumbing is wrong before neural
approximation enters the experiment.

The saturated recovery model uses ``B * tanh(raw)`` for every direct-time,
latent-state, and observation cell.  A separate negative control uses the
unrestricted affine count logit ``c[t,a] + n @ w[t,:,a]``.  Both minimize the
exactly summed equal-prior joint-versus-product logistic risk.  At the
population optimum the saturated logit is
``log J_t(x,a) - log(pi_t(x) p_A(a))``, which differs from the bridge's
``log h`` only by an observation-dependent constant and therefore induces the
same edge ratios and normalized initial law.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Tuple

import numpy as np
from scipy.optimize import minimize


_MAX_POPULATION_CELLS = 2_000_000
_MAX_OPTIMIZER_ITERATIONS = 100_000
_MAX_AFFINE_DESIGN_CELLS = 2_000_000
_MAX_AFFINE_RANK_WORK = 20_000_000
_MIN_AFFINE_DESIGN_SINGULAR_RATIO = 1.0e-12


def _immutable_float_array(value: object) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    return np.frombuffer(array.tobytes(order="C"), dtype=np.float64).reshape(
        array.shape
    )


def _raw_numeric_array(value: object, *, name: str, allowed_kinds: str) -> np.ndarray:
    try:
        raw = np.asarray(value)
        object_view = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(
            "{} must be a rectangular numeric array".format(name)
        ) from error
    if any(isinstance(item, (bool, np.bool_)) for item in object_view.flat):
        raise TypeError("{} must not contain boolean entries".format(name))
    if raw.dtype.kind == "b":
        raise TypeError("{} must not have boolean dtype".format(name))
    if raw.dtype.kind not in allowed_kinds:
        raise TypeError("{} must have a real numeric dtype".format(name))
    return raw


def _positive_finite_real(
    value: object,
    *,
    name: str,
    maximum: float,
) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError("{} must be a real non-boolean number".format(name))
    result = float(value)
    if not math.isfinite(result) or result <= 0.0 or result > maximum:
        raise ValueError("{} must lie in (0, {}]".format(name, maximum))
    return result


def _bounded_integer(
    value: object,
    *,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TypeError("{} must be an integer non-boolean value".format(name))
    result = int(value)
    if result < minimum or result > maximum:
        raise ValueError(
            "{} must lie in [{}, {}]".format(name, minimum, maximum)
        )
    return result


def _validated_times(value: object) -> np.ndarray:
    raw = _raw_numeric_array(
        value, name="direct_times", allowed_kinds="iuf"
    )
    times = raw.astype(float, copy=True)
    if times.ndim != 1 or times.size == 0:
        raise ValueError("direct_times must be a nonempty one-dimensional array")
    if not np.all(np.isfinite(times)) or np.any(times < 0.0):
        raise ValueError("direct_times must be finite and nonnegative")
    if times.size > 1 and np.any(np.diff(times) <= 0.0):
        raise ValueError("direct_times must be strictly increasing")
    return times


def _validated_population_pair(
    joint_mass: object,
    product_mass: object,
    n_times: int,
) -> Tuple[np.ndarray, np.ndarray]:
    arrays = []
    for value, name in (
        (joint_mass, "joint_mass"),
        (product_mass, "product_mass"),
    ):
        raw = _raw_numeric_array(value, name=name, allowed_kinds="iuf")
        array = raw.astype(float, copy=True)
        if array.ndim != 3 or array.shape[0] != n_times:
            raise ValueError(
                "{} must have shape [n_times, n_states, n_observations]".format(
                    name
                )
            )
        if not np.all(np.isfinite(array)) or np.any(array <= 0.0):
            raise ValueError("{} entries must be finite and strictly positive".format(name))
        if not np.allclose(
            array.sum(axis=(1, 2)), 1.0, atol=2.0e-12, rtol=0.0
        ):
            raise ValueError("{} must be normalized at every time".format(name))
        arrays.append(array)
    joint, product = arrays
    if joint.shape != product.shape:
        raise ValueError("joint_mass and product_mass must have identical shapes")
    if joint.size > _MAX_POPULATION_CELLS:
        raise ValueError(
            "population table exceeds the work limit of {} cells".format(
                _MAX_POPULATION_CELLS
            )
        )
    return joint, product


def population_logistic_risk(
    joint_mass: object,
    product_mass: object,
    logits: object,
) -> float:
    """Return exact equal-prior BCE, averaged uniformly over time points."""

    joint = np.asarray(joint_mass, dtype=float)
    product = np.asarray(product_mass, dtype=float)
    score = np.asarray(logits, dtype=float)
    if joint.ndim != 3 or joint.shape != product.shape or score.shape != joint.shape:
        raise ValueError("joint_mass, product_mass, and logits must share one 3D shape")
    if not all(np.all(np.isfinite(value)) for value in (joint, product, score)):
        raise ValueError("risk inputs must be finite")
    if np.any(joint < 0.0) or np.any(product < 0.0):
        raise ValueError("risk masses must be nonnegative")
    if not np.allclose(joint.sum(axis=(1, 2)), 1.0, atol=2.0e-12, rtol=0.0):
        raise ValueError("joint_mass must be normalized at every time")
    if not np.allclose(product.sum(axis=(1, 2)), 1.0, atol=2.0e-12, rtol=0.0):
        raise ValueError("product_mass must be normalized at every time")
    per_time = 0.5 * (
        (joint * np.logaddexp(0.0, -score)).sum(axis=(1, 2))
        + (product * np.logaddexp(0.0, score)).sum(axis=(1, 2))
    )
    result = float(per_time.mean())
    if not math.isfinite(result):
        raise ArithmeticError("population logistic risk is not finite")
    return result


class PiecewiseLinearFinitePotential:
    """Positive bounded potential interpolated in direct process time."""

    def __init__(self, direct_times: object, log_potential_grid: object) -> None:
        times = _validated_times(direct_times)
        raw = _raw_numeric_array(
            log_potential_grid,
            name="log_potential_grid",
            allowed_kinds="iuf",
        )
        grid = raw.astype(float, copy=True)
        if grid.ndim != 3 or grid.shape[0] != times.size:
            raise ValueError(
                "log_potential_grid must have shape "
                "[n_times, n_states, n_observations]"
            )
        if grid.shape[1] == 0 or grid.shape[2] == 0:
            raise ValueError("potential state and observation axes must be nonempty")
        if not np.all(np.isfinite(grid)):
            raise ValueError("log_potential_grid entries must be finite")
        if np.max(np.abs(grid)) > 50.0:
            raise ValueError("absolute log-potential values must not exceed 50")
        self._direct_times = _immutable_float_array(times)
        self._log_potential_grid = _immutable_float_array(grid)

    @property
    def direct_times(self) -> np.ndarray:
        return self._direct_times

    @property
    def log_potential_grid(self) -> np.ndarray:
        return self._log_potential_grid

    @property
    def n_states(self) -> int:
        return int(self._log_potential_grid.shape[1])

    @property
    def n_observations(self) -> int:
        return int(self._log_potential_grid.shape[2])

    def _validated_direct_time(self, value: object) -> float:
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
            raise TypeError("direct_time must be a real non-boolean number")
        direct_time = float(value)
        if not math.isfinite(direct_time):
            raise ValueError("direct_time must be finite")
        lower = float(self._direct_times[0])
        upper = float(self._direct_times[-1])
        if direct_time < lower or direct_time > upper:
            raise ValueError(
                "direct_time must lie in the closed fitted interval [{}, {}]".format(
                    lower, upper
                )
            )
        return direct_time

    def _validated_observation_index(self, value: object) -> int:
        return _bounded_integer(
            value,
            name="observation_index",
            minimum=0,
            maximum=self.n_observations - 1,
        )

    def all_log_potentials(self, direct_time: object) -> np.ndarray:
        time = self._validated_direct_time(direct_time)
        exact = np.flatnonzero(self._direct_times == time)
        if exact.size:
            return _immutable_float_array(self._log_potential_grid[int(exact[0])])
        upper = int(np.searchsorted(self._direct_times, time, side="right"))
        lower = upper - 1
        fraction = (time - self._direct_times[lower]) / (
            self._direct_times[upper] - self._direct_times[lower]
        )
        interpolated = (
            (1.0 - fraction) * self._log_potential_grid[lower]
            + fraction * self._log_potential_grid[upper]
        )
        return _immutable_float_array(interpolated)

    def log_potential_vector(
        self, direct_time: object, observation_index: object
    ) -> np.ndarray:
        index = self._validated_observation_index(observation_index)
        return _immutable_float_array(self.all_log_potentials(direct_time)[:, index])

    def potential_vector(
        self, direct_time: object, observation_index: object
    ) -> np.ndarray:
        result = np.exp(self.log_potential_vector(direct_time, observation_index))
        if np.any(result <= 0.0) or not np.all(np.isfinite(result)):
            raise ArithmeticError("interpolated potential is not finite and positive")
        return _immutable_float_array(result)


@dataclass(frozen=True)
class BoundedPopulationPotentialFit:
    """Deterministic result of one complete-population tabular fit."""

    potential: PiecewiseLinearFinitePotential
    raw_parameter_grid: np.ndarray
    log_bound: float
    initial_risk: float
    final_risk: float
    oracle_risk: float
    excess_risk: float
    gradient_infinity_norm: float
    requested_gradient_tolerance: float
    iterations: int
    optimizer_converged: bool
    optimizer_message: str


@dataclass(frozen=True)
class AdditiveCountPotentialFit:
    """Unconstrained affine eventwise count-potential population fit."""

    potential: PiecewiseLinearFinitePotential
    intercept_grid: np.ndarray
    count_coefficient_grid: np.ndarray
    logit_safety_ceiling: float
    initial_risk: float
    final_risk: float
    oracle_risk: float
    excess_risk: float
    gradient_infinity_norm: float
    requested_gradient_tolerance: float
    minimum_hessian_eigenvalue: float
    maximum_hessian_condition_number: float
    summed_half_newton_decrement: float
    iterations: int
    optimizer_converged: bool
    optimizer_message: str


def _accept_finite_precision_polish(
    *,
    old_objective: float,
    proposed_objective: float,
    old_gradient_norm: float,
    proposed_gradient_norm: float,
    gradient_tolerance: float,
) -> bool:
    """Certify a sub-ULP polish step by an independent gradient reduction.

    Near a smooth optimum, recomputing the summed scalar loss can round a valid
    polish proposal one floating-point unit upward while the gradient remains
    accurately resolvable.  This narrow fallback never substitutes loss
    stagnation for convergence: the proposed loss may exceed the old loss by
    at most one binary64 ULP and its freshly evaluated gradient norm must
    strictly decrease.
    """

    values = (
        old_objective,
        proposed_objective,
        old_gradient_norm,
        proposed_gradient_norm,
        gradient_tolerance,
    )
    if not all(math.isfinite(value) for value in values):
        return False
    if min(old_gradient_norm, proposed_gradient_norm, gradient_tolerance) < 0.0:
        return False
    roundoff_slack = math.ulp(old_objective)
    return bool(
        old_gradient_norm <= 1.0e-8
        and proposed_objective <= old_objective + roundoff_slack
        and proposed_gradient_norm < old_gradient_norm
    )


def fit_bounded_tabular_potential(
    direct_times: object,
    joint_mass: object,
    product_mass: object,
    *,
    log_bound: object,
    max_iterations: object = 1_000,
    gradient_tolerance: object = 1.0e-11,
) -> BoundedPopulationPotentialFit:
    """Fit all bounded logits to the exactly summed population BCE.

    Optimization is intentionally deterministic and contains no minibatching,
    sampling, random initialization, or accelerator-dependent operation.
    """

    times = _validated_times(direct_times)
    joint, product = _validated_population_pair(
        joint_mass, product_mass, times.size
    )
    bound = _positive_finite_real(log_bound, name="log_bound", maximum=50.0)
    iterations = _bounded_integer(
        max_iterations,
        name="max_iterations",
        minimum=1,
        maximum=_MAX_OPTIMIZER_ITERATIONS,
    )
    tolerance = _positive_finite_real(
        gradient_tolerance, name="gradient_tolerance", maximum=1.0
    )
    oracle_logits = np.log(joint) - np.log(product)
    if np.max(np.abs(oracle_logits)) >= bound:
        raise ValueError(
            "log_bound must strictly exceed every exact population log ratio"
        )

    shape = joint.shape
    scale = float(joint.size)

    def objective(flat_raw: np.ndarray) -> Tuple[float, np.ndarray]:
        raw = flat_raw.reshape(shape)
        squashed = np.tanh(raw)
        logits = bound * squashed
        risk = population_logistic_risk(joint, product, logits)
        sigmoid = np.exp(-np.logaddexp(0.0, -logits))
        gradient_logits = 0.5 * (
            (joint + product) * sigmoid - joint
        ) / times.size
        gradient_raw = gradient_logits * bound * (1.0 - squashed * squashed)
        # A constant scale gives L-BFGS gradients a cell-size-independent
        # numerical magnitude without changing the minimizer.
        return risk * scale, (gradient_raw * scale).reshape(-1)

    initial_raw = np.zeros(joint.size, dtype=float)
    initial_risk = population_logistic_risk(
        joint, product, np.zeros(shape, dtype=float)
    )
    result = minimize(
        objective,
        initial_raw,
        method="L-BFGS-B",
        jac=True,
        options={
            "maxiter": iterations,
            "gtol": tolerance * scale,
            "ftol": 0.0,
            "maxls": 50,
        },
    )
    raw_grid = result.x.reshape(shape)
    polish_iterations = 0
    # L-BFGS-B may report objective-stagnation success before satisfying the
    # caller's requested gradient tolerance, particularly in rare population
    # cells.  The saturated problem is cellwise, so deterministic Newton steps
    # in logit coordinates finish the same declared BCE optimization without
    # changing its objective or using a model-selection metric.
    for polish_iterations in range(21):
        squashed = np.tanh(raw_grid)
        fitted_logits = bound * squashed
        sigmoid = np.exp(-np.logaddexp(0.0, -fitted_logits))
        gradient_logits = 0.5 * (
            (joint + product) * sigmoid - joint
        ) / times.size
        gradient_raw = gradient_logits * bound * (1.0 - squashed * squashed)
        if float(np.max(np.abs(gradient_raw))) <= tolerance:
            break
        hessian_logits = 0.5 * (
            (joint + product) * sigmoid * (1.0 - sigmoid)
        ) / times.size
        if np.any(hessian_logits <= 0.0) or not np.all(np.isfinite(hessian_logits)):
            raise ArithmeticError("population Newton curvature is invalid")
        updated_logits = fitted_logits - gradient_logits / hessian_logits
        margin = 16.0 * np.finfo(np.float64).eps
        updated_logits = np.clip(
            updated_logits,
            -bound * (1.0 - margin),
            bound * (1.0 - margin),
        )
        raw_grid = np.arctanh(updated_logits / bound)
    squashed = np.tanh(raw_grid)
    fitted_logits = bound * squashed
    final_risk = population_logistic_risk(joint, product, fitted_logits)
    oracle_risk = population_logistic_risk(joint, product, oracle_logits)
    polished_flat = raw_grid.reshape(-1)
    unscaled_gradient = objective(polished_flat)[1] / scale
    gradient_norm = float(np.max(np.abs(unscaled_gradient)))
    excess = final_risk - oracle_risk
    if excess < -2.0e-13:
        raise ArithmeticError("fitted risk is spuriously below the population optimum")
    if excess < 0.0:
        excess = 0.0

    return BoundedPopulationPotentialFit(
        potential=PiecewiseLinearFinitePotential(times, fitted_logits),
        raw_parameter_grid=_immutable_float_array(raw_grid),
        log_bound=bound,
        initial_risk=initial_risk,
        final_risk=final_risk,
        oracle_risk=oracle_risk,
        excess_risk=excess,
        gradient_infinity_norm=gradient_norm,
        requested_gradient_tolerance=tolerance,
        iterations=int(result.nit) + polish_iterations,
        optimizer_converged=bool(result.success and gradient_norm <= tolerance),
        optimizer_message=(
            "{}; {} cellwise Newton polish iterations".format(
                result.message, polish_iterations
            )
        ),
    )


def fit_additive_count_potential(
    direct_times: object,
    state_counts: object,
    joint_mass: object,
    product_mass: object,
    *,
    logit_safety_ceiling: object = 50.0,
    max_iterations: object = 2_000,
    gradient_tolerance: object = 1.0e-11,
) -> AdditiveCountPotentialFit:
    """Fit the restricted eventwise form ``c[t,a] + n @ w[t,:,a]``.

    Observation identity receives its own intercept and coefficient vector, so
    this is a strong control.  It cannot represent interactions between two
    latent occurrences and therefore exposes association-induced
    nonadditivity.  The affine parameters are not artificially box constrained;
    ``logit_safety_ceiling`` is a fail-closed post-fit numerical guard rather
    than part of the hypothesis class.
    """

    times = _validated_times(direct_times)
    joint, product = _validated_population_pair(
        joint_mass, product_mass, times.size
    )
    raw_counts = _raw_numeric_array(
        state_counts, name="state_counts", allowed_kinds="iu"
    )
    if raw_counts.size > _MAX_AFFINE_DESIGN_CELLS:
        raise ValueError(
            "affine count design exceeds the {}-cell work limit".format(
                _MAX_AFFINE_DESIGN_CELLS
            )
        )
    counts = raw_counts.astype(float, copy=True)
    if counts.ndim != 2 or counts.shape[0] != joint.shape[1] or counts.shape[1] == 0:
        raise ValueError("state_counts must have shape [n_states, n_atoms]")
    if np.any(counts < 0.0):
        raise ValueError("state_counts must be nonnegative")
    safety_ceiling = _positive_finite_real(
        logit_safety_ceiling,
        name="logit_safety_ceiling",
        maximum=50.0,
    )
    iterations = _bounded_integer(
        max_iterations,
        name="max_iterations",
        minimum=1,
        maximum=_MAX_OPTIMIZER_ITERATIONS,
    )
    tolerance = _positive_finite_real(
        gradient_tolerance, name="gradient_tolerance", maximum=1.0
    )

    n_times, _, n_observations = joint.shape
    n_atoms = counts.shape[1]
    intercept_size = n_times * n_observations
    coefficient_size = n_times * n_atoms * n_observations
    parameter_size = intercept_size + coefficient_size
    if parameter_size > _MAX_POPULATION_CELLS:
        raise ValueError(
            "additive parameter table exceeds the work limit of {} cells".format(
                _MAX_POPULATION_CELLS
            )
        )
    design = np.column_stack((np.ones(counts.shape[0]), counts))
    rank_dimension = min(design.shape)
    rank_work = rank_dimension * rank_dimension * max(design.shape)
    if design.size > _MAX_AFFINE_DESIGN_CELLS or rank_work > _MAX_AFFINE_RANK_WORK:
        raise ValueError("affine count design exceeds the rank-check work limit")
    singular_values = np.linalg.svd(design, compute_uv=False)
    singular_ratio = (
        0.0
        if singular_values.size < design.shape[1] or singular_values[0] == 0.0
        else float(singular_values[-1] / singular_values[0])
    )
    if singular_ratio < _MIN_AFFINE_DESIGN_SINGULAR_RATIO:
        raise ValueError(
            "the affine count design must have full column rank and a "
            "minimum singular-value ratio of {:.1e}".format(
                _MIN_AFFINE_DESIGN_SINGULAR_RATIO
            )
        )
    scale = float(joint.size)

    def unpack(flat: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        intercept = flat[:intercept_size].reshape(n_times, n_observations)
        coefficients = flat[intercept_size:].reshape(
            n_times, n_atoms, n_observations
        )
        return intercept, coefficients

    def objective(flat: np.ndarray) -> Tuple[float, np.ndarray]:
        intercept, coefficients = unpack(flat)
        linear = intercept[:, None, :] + np.einsum(
            "sk,tka->tsa", counts, coefficients
        )
        risk = population_logistic_risk(joint, product, linear)
        sigmoid = np.exp(-np.logaddexp(0.0, -linear))
        gradient_logits = 0.5 * (
            (joint + product) * sigmoid - joint
        ) / n_times
        gradient_intercept = gradient_logits.sum(axis=1)
        gradient_coefficients = np.einsum(
            "sk,tsa->tka", counts, gradient_logits
        )
        gradient = np.concatenate(
            (gradient_intercept.reshape(-1), gradient_coefficients.reshape(-1))
        )
        return risk * scale, gradient * scale

    initial = np.zeros(parameter_size, dtype=float)
    initial_risk = population_logistic_risk(
        joint, product, np.zeros_like(joint)
    )
    result = minimize(
        objective,
        initial,
        method="L-BFGS-B",
        jac=True,
        options={
            "maxiter": iterations,
            "gtol": tolerance * scale,
            "ftol": 0.0,
            "maxls": 50,
        },
    )
    intercept, coefficients = unpack(result.x.copy())
    newton_sweeps = 0
    # Each (time, observation) block is an independent strictly convex logistic
    # regression because the declared design is full rank and every population
    # cell is positive.  Small Newton sweeps enforce the requested raw-gradient
    # tolerance when L-BFGS-B stops on scalar-objective stagnation.
    for newton_sweeps in range(51):
        largest_gradient = 0.0
        changed = False
        for time_index in range(n_times):
            for observation_index in range(n_observations):
                theta = np.concatenate(
                    (
                        np.asarray([intercept[time_index, observation_index]]),
                        coefficients[time_index, :, observation_index],
                    )
                )
                logits = design @ theta
                sigmoid = np.exp(-np.logaddexp(0.0, -logits))
                joint_column = joint[time_index, :, observation_index]
                product_column = product[time_index, :, observation_index]
                gradient_logit = 0.5 * (
                    (joint_column + product_column) * sigmoid - joint_column
                ) / n_times
                gradient = design.T @ gradient_logit
                gradient_norm = float(np.max(np.abs(gradient)))
                largest_gradient = max(largest_gradient, gradient_norm)
                if gradient_norm <= tolerance:
                    continue
                curvature_weights = 0.5 * (
                    (joint_column + product_column)
                    * sigmoid
                    * (1.0 - sigmoid)
                ) / n_times
                hessian = design.T @ (curvature_weights[:, None] * design)
                try:
                    step = np.linalg.solve(hessian, -gradient)
                except np.linalg.LinAlgError:
                    step = np.linalg.lstsq(hessian, -gradient, rcond=None)[0]
                if float(gradient @ step) >= 0.0:
                    step = -gradient
                old_objective = 0.5 * float(
                    np.sum(
                        joint_column * np.logaddexp(0.0, -logits)
                        + product_column * np.logaddexp(0.0, logits)
                    )
                ) / n_times
                directional = float(gradient @ step)
                step_size = 1.0
                accepted = False
                for _ in range(60):
                    proposed = theta + step_size * step
                    proposed_logits = design @ proposed
                    proposed_objective = 0.5 * float(
                        np.sum(
                            joint_column * np.logaddexp(0.0, -proposed_logits)
                            + product_column * np.logaddexp(0.0, proposed_logits)
                        )
                    ) / n_times
                    armijo_bound = (
                        old_objective + 1.0e-4 * step_size * directional
                    )
                    # Once the KKT residual is near machine precision, the
                    # true Newton decrease can be smaller than the rounding
                    # error of the summed scalar loss even though its
                    # gradient remains resolvable.  In that narrow regime,
                    # accept a numerically non-increasing step only when an
                    # independently recomputed raw-gradient norm is strictly
                    # smaller.  This preserves the frozen stationarity
                    # threshold instead of treating objective stagnation as
                    # convergence.
                    proposed_sigmoid = np.exp(
                        -np.logaddexp(0.0, -proposed_logits)
                    )
                    proposed_gradient_logit = 0.5 * (
                        (joint_column + product_column) * proposed_sigmoid
                        - joint_column
                    ) / n_times
                    proposed_gradient = design.T @ proposed_gradient_logit
                    proposed_gradient_norm = float(
                        np.max(np.abs(proposed_gradient))
                    )
                    finite_precision_polish = _accept_finite_precision_polish(
                        old_objective=old_objective,
                        proposed_objective=proposed_objective,
                        old_gradient_norm=gradient_norm,
                        proposed_gradient_norm=proposed_gradient_norm,
                        gradient_tolerance=tolerance,
                    )
                    if (
                        proposed_objective <= armijo_bound
                        or finite_precision_polish
                    ):
                        theta = proposed
                        accepted = True
                        break
                    step_size *= 0.5
                if not accepted:
                    continue
                intercept[time_index, observation_index] = theta[0]
                coefficients[time_index, :, observation_index] = theta[1:]
                changed = True
        if largest_gradient <= tolerance:
            break
        if not changed:
            break
    linear = intercept[:, None, :] + np.einsum(
        "sk,tka->tsa", counts, coefficients
    )
    fitted_logits = linear
    if np.max(np.abs(fitted_logits)) > safety_ceiling:
        raise ArithmeticError(
            "additive fitted logit exceeded its numerical safety ceiling"
        )
    oracle_logits = np.log(joint) - np.log(product)
    final_risk = population_logistic_risk(joint, product, fitted_logits)
    oracle_risk = population_logistic_risk(joint, product, oracle_logits)
    polished_parameters = np.concatenate(
        (intercept.reshape(-1), coefficients.reshape(-1))
    )
    raw_gradient = objective(polished_parameters)[1] / scale
    gradient_norm = float(np.max(np.abs(raw_gradient)))
    minimum_hessian_eigenvalue = math.inf
    maximum_hessian_condition_number = 0.0
    summed_half_newton_decrement = 0.0
    for time_index in range(n_times):
        for observation_index in range(n_observations):
            theta = np.concatenate(
                (
                    np.asarray([intercept[time_index, observation_index]]),
                    coefficients[time_index, :, observation_index],
                )
            )
            logits = design @ theta
            sigmoid = np.exp(-np.logaddexp(0.0, -logits))
            joint_column = joint[time_index, :, observation_index]
            product_column = product[time_index, :, observation_index]
            gradient_logit = 0.5 * (
                (joint_column + product_column) * sigmoid - joint_column
            ) / n_times
            gradient = design.T @ gradient_logit
            curvature_weights = 0.5 * (
                (joint_column + product_column)
                * sigmoid
                * (1.0 - sigmoid)
            ) / n_times
            hessian = design.T @ (curvature_weights[:, None] * design)
            eigenvalues = np.linalg.eigvalsh(hessian)
            if eigenvalues[0] <= 0.0 or not np.all(np.isfinite(eigenvalues)):
                raise ArithmeticError("additive Hessian is not positive definite")
            minimum_hessian_eigenvalue = min(
                minimum_hessian_eigenvalue, float(eigenvalues[0])
            )
            maximum_hessian_condition_number = max(
                maximum_hessian_condition_number,
                float(eigenvalues[-1] / eigenvalues[0]),
            )
            newton_direction = np.linalg.solve(hessian, gradient)
            summed_half_newton_decrement += 0.5 * float(
                gradient @ newton_direction
            )
    excess = final_risk - oracle_risk
    if excess < -2.0e-13:
        raise ArithmeticError("restricted risk is spuriously below the optimum")
    if excess < 0.0:
        excess = 0.0
    return AdditiveCountPotentialFit(
        potential=PiecewiseLinearFinitePotential(times, fitted_logits),
        intercept_grid=_immutable_float_array(intercept),
        count_coefficient_grid=_immutable_float_array(coefficients),
        logit_safety_ceiling=safety_ceiling,
        initial_risk=initial_risk,
        final_risk=final_risk,
        oracle_risk=oracle_risk,
        excess_risk=excess,
        gradient_infinity_norm=gradient_norm,
        requested_gradient_tolerance=tolerance,
        minimum_hessian_eigenvalue=minimum_hessian_eigenvalue,
        maximum_hessian_condition_number=maximum_hessian_condition_number,
        summed_half_newton_decrement=summed_half_newton_decrement,
        iterations=int(result.nit) + newton_sweeps,
        optimizer_converged=bool(result.success and gradient_norm <= tolerance),
        optimizer_message=(
            "{}; {} block Newton sweeps".format(
                result.message, newton_sweeps
            )
        ),
    )


__all__ = [
    "AdditiveCountPotentialFit",
    "BoundedPopulationPotentialFit",
    "PiecewiseLinearFinitePotential",
    "fit_additive_count_potential",
    "fit_bounded_tabular_potential",
    "population_logistic_risk",
]
