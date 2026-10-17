"""Bounded C2 localized log-likelihood residual learned without derivative labels.

Quintic B-spline controls at each end are tied in groups of three, making
constant extensions C2. This is a statistical subfamily of local quintics,
not the previous oracle-jet interpolant or a general amortized BCE learner.
"""
from dataclasses import dataclass
import math

import numpy as np
from scipy.interpolate import BSpline
from scipy.optimize import minimize

CORE = (-4.5, 4.5)
CELLS = 32
SMOOTHNESS = 1e-4
RIDGE = 1e-6
MAXIMUM_ITERATIONS = 200
CONTINUOUS_COEFFICIENTS = 33
COEFFICIENTS = 35


def _basis():
    knots = np.linspace(*CORE, CELLS+1)
    vector = np.r_[np.repeat(knots[0], 5), knots, np.repeat(knots[-1], 5)]
    # 37 raw controls -> 33 free ones, with two endpoint equalities per side.
    mapping = np.zeros((37, 33))
    mapping[:3, 0] = 1
    for i in range(3, 34):
        mapping[i, i-2] = 1
    mapping[34:, -1] = 1
    return BSpline(vector, mapping, 5, extrapolate=False)


def spline_features(z, derivative=0):
    raw = np.asarray(z)
    if (raw.ndim != 1 or raw.dtype.kind not in 'fiu' or np.ma.isMaskedArray(z)
            or not np.isfinite(raw).all() or type(derivative) is not int or derivative not in (0, 1, 2)):
        raise ValueError('finite one-dimensional coordinates and derivative 0,1,2 required')
    with np.errstate(over='ignore', invalid='ignore'):
        z = raw.astype(np.float64)
    if not np.isfinite(z).all():
        raise ValueError('coordinates must be representable as float64')
    result = _basis()(np.clip(z, *CORE), nu=derivative)
    if derivative:
        result[(z <= CORE[0]) | (z >= CORE[1])] = 0.
    if not np.isfinite(result).all():
        raise ArithmeticError('invalid spline features')
    return result


def training_design(states, coordinates, derivative=0):
    if type(derivative) is not int or derivative not in (0, 1, 2):
        raise ValueError('derivative must be 0,1,2')
    from heterodiff.experiments.continuous_forward_labels import validate_states
    states, coordinates = validate_states(states, coordinates)
    result = np.zeros((len(states), COEFFICIENTS))
    result[states == 2, :CONTINUOUS_COEFFICIENTS] = spline_features(coordinates[states == 2], derivative)
    if derivative == 0:
        result[states == 0, -2], result[states == 1, -1] = 1., 1.
    return result


def roughness_matrix():
    """Exact real-arithmetic Gaussian integration of mean squared core curvature."""
    roots, weights = np.polynomial.legendre.leggauss(4)
    knots = np.linspace(*CORE, CELLS+1)
    half = (knots[1]-knots[0])/2
    z = (knots[:-1, None]+half+half*roots).reshape(-1)
    weighted = np.tile(weights*half/(CORE[1]-CORE[0]), CELLS)
    features = spline_features(z, 2)
    matrix = np.zeros((COEFFICIENTS, COEFFICIENTS))
    matrix[:CONTINUOUS_COEFFICIENTS, :CONTINUOUS_COEFFICIENTS] = features.T@(weighted[:, None]*features)
    return matrix


def risk_value_gradient(coefficients, features, labels, baseline, tau, maximum_label, roughness):
    potential = baseline+tau*(features@coefficients)
    predicted = np.exp(potential)
    value = float(np.mean(predicted-labels*potential)/maximum_label
        + .5*SMOOTHNESS*tau*tau*(coefficients@roughness@coefficients)
        + .5*RIDGE*tau*tau*(coefficients@coefficients))
    gradient = (tau*(features.T@(predicted-labels))/(len(labels)*maximum_label)
        + SMOOTHNESS*tau*tau*(roughness@coefficients)+RIDGE*tau*tau*coefficients)
    if not math.isfinite(value) or not np.isfinite(gradient).all():
        raise ArithmeticError('nonfinite convex objective')
    return value, gradient


@dataclass(frozen=True)
class LearnedLocalizedResidual:
    coefficients: tuple[float, ...]
    remaining_time: float
    coefficient_bound: float

    def __post_init__(self):
        if (isinstance(self.coefficient_bound, bool) or not isinstance(self.coefficient_bound, (int, float))
                or not math.isfinite(self.coefficient_bound) or self.coefficient_bound <= 0
                or type(self.coefficients) is not tuple or len(self.coefficients) != COEFFICIENTS
                or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                    or abs(v) > self.coefficient_bound for v in self.coefficients)
                or isinstance(self.remaining_time, bool) or not isinstance(self.remaining_time, (int, float))
                or not math.isfinite(self.remaining_time) or not 0 <= self.remaining_time <= 1):
            raise ValueError('bounded finite coefficient tuple and time gate required')

    def evaluate(self, states, coordinates):
        return {name: self.remaining_time*(training_design(states, coordinates, order)@self.coefficients)
            for order, name in enumerate(('value', 'gradient', 'hessian'))}

    @property
    def real_absolute_bound(self):
        return self.remaining_time*max(abs(v) for v in self.coefficients)


def fit_likelihood(features, labels, baseline, tau, maximum_label, minimum_label, roughness=None):
    for a in (features, labels, baseline):
        if np.ma.isMaskedArray(a) or np.asarray(a).dtype.kind not in 'fiu':
            raise ValueError('real unmasked arrays required')
    with np.errstate(over='ignore', invalid='ignore'):
        features, labels, baseline = (np.asarray(a, dtype=np.float64) for a in (features, labels, baseline))
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
           for v in (tau, maximum_label, minimum_label)):
        raise ValueError('finite real time and label bounds required')
    if (features.ndim != 2 or features.shape[1] != COEFFICIENTS or len(features) == 0
            or labels.shape != (len(features),) or baseline.shape != labels.shape
            or not all(np.isfinite(a).all() for a in (features, labels, baseline))
            or isinstance(tau, bool) or not 0 < tau <= 1 or not math.isfinite(maximum_label)
            or not math.isfinite(minimum_label) or not 0 < minimum_label < maximum_label
            or np.any(labels < minimum_label) or np.any(labels > maximum_label)):
        raise ValueError('aligned finite positive likelihood labels and active time required')
    if roughness is not None and (np.ma.isMaskedArray(roughness) or np.asarray(roughness).dtype.kind not in 'fiu'):
        raise ValueError('real unmasked roughness required')
    roughness = roughness_matrix() if roughness is None else np.asarray(roughness, dtype=np.float64)
    if roughness.shape != (COEFFICIENTS, COEFFICIENTS) or not np.isfinite(roughness).all():
        raise ValueError('finite aligned roughness matrix required')
    if not np.allclose(roughness, roughness.T, rtol=0, atol=1e-10) or np.linalg.eigvalsh(roughness).min() < -1e-8:
        raise ValueError('positive semidefinite symmetric roughness matrix required')
    initial = np.zeros(COEFFICIENTS)
    # Optimize physical coefficients a=tau*q, so conditioning and regularization
    # do not change merely because a macro node is close to the terminal.
    physical_bound = 2*math.log(maximum_label/minimum_label)
    objective = lambda c: risk_value_gradient(c, features, labels, baseline, 1., maximum_label, roughness)
    initial_value, _ = objective(initial)
    result = minimize(objective, initial, method='L-BFGS-B', jac=True,
        bounds=[(-physical_bound, physical_bound)]*COEFFICIENTS,
        options={'maxiter': MAXIMUM_ITERATIONS, 'maxls': 30, 'ftol': 1e-12, 'gtol': 1e-7})
    model = LearnedLocalizedResidual(tuple(float(c/tau) for c in result.x), float(tau), physical_bound/tau)
    final_value, gradient = objective(result.x)
    projected = gradient.copy()
    projected[(result.x <= -physical_bound) & (gradient > 0)] = 0
    projected[(result.x >= physical_bound) & (gradient < 0)] = 0
    return model, {'solver_success': bool(result.success), 'solver_status': int(result.status),
        'solver_message': str(result.message), 'iterations': int(result.nit), 'function_evaluations': int(result.nfev),
        'initial_penalized_risk': initial_value, 'final_penalized_risk': final_value,
        'projected_gradient_max_abs': float(np.max(abs(projected))),
        'coefficient_boundary_count': int(np.sum(abs(result.x) >= physical_bound-1e-10)),
        'coefficients': list(model.coefficients), 'remaining_time': tau,
        'physical_coefficients': result.x.tolist(), 'physical_coefficient_bound': physical_bound,
        'quotient_coefficient_bound': physical_bound/tau,
        'box_basis': 'TWICE_LOG_KNOWN_OBSERVATION_MAXIMUM_OVER_CONTAMINATION_FLOOR',
        'real_arithmetic_absolute_bound': model.real_absolute_bound,
        'hessian_score_or_exact_likelihood_labels_consumed': False,
        'regularization_selected_from_validation_or_oracle': False}
