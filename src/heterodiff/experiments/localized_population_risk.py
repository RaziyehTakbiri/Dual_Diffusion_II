"""Weighted quasi-risk diagnostics on the unchanged 35-coefficient spline family.

There are no backward-oracle imports, scientific settings selection, or sampler
operations here. The optimizer is one predeclared strict L-BFGS-B phase. Local
Hessian eigenvalues are sensitivity diagnostics, not global distance bounds;
computed spectra and convex box gaps are not outward-rounded certificates.
"""
import math
from numbers import Real

import numpy as np
from scipy.optimize import minimize

from heterodiff.models.localized_likelihood_learner import training_design


COEFFICIENTS = 35
OPTIMIZER_OPTIONS = {'maxiter': 2000, 'maxls': 50, 'ftol': 1e-15, 'gtol': 1e-11}
WEIGHT_SUM_ATOL = 1e-12
PSD_ROUNDOFF_FACTOR = 64*np.finfo(np.float64).eps


def _scalar(value, name, *, positive=False):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real) or not math.isfinite(float(value)):
        raise ValueError(name+' must be a finite real scalar')
    value = float(value)
    if positive and value <= 0:
        raise ValueError(name+' must be positive')
    return value


def _array(source, name):
    raw = np.asarray(source)
    if np.ma.isMaskedArray(source) or raw.dtype.kind not in 'fiu':
        raise ValueError(name+' must contain unmasked real numbers')
    with np.errstate(over='ignore', invalid='ignore'):
        answer = np.array(raw, dtype=np.float64, copy=True)
    if not np.isfinite(answer).all():
        raise ValueError(name+' must be finite and representable as float64')
    return answer


def _prepare(features, labels, baseline, weights, maximum_label, penalty_matrix):
    X, Y, b, w, P = (_array(a, name) for a,name in ((features,'features'),(labels,'labels'),
        (baseline,'baseline'),(weights,'weights'),(penalty_matrix,'penalty_matrix')))
    M = _scalar(maximum_label, 'maximum_label', positive=True)
    if X.ndim != 2 or not len(X) or X.shape[1] != COEFFICIENTS:
        raise ValueError('features require nonempty rows and exactly 35 columns')
    if any(a.shape != (len(X),) for a in (Y,b,w)):
        raise ValueError('labels, baseline and weights must align with feature rows')
    if np.any(Y <= 0) or np.any(Y > M):
        raise ValueError('labels must lie in (0,maximum_label]')
    if np.any(w <= 0) or not math.isclose(math.fsum(w), 1., rel_tol=0., abs_tol=WEIGHT_SUM_ATOL):
        raise ValueError('strictly positive weights summing to one required; weights are not renormalized')
    if P.shape != (COEFFICIENTS,COEFFICIENTS):
        raise ValueError('penalty requires a 35 by 35 matrix')
    scale = max(1., float(np.max(abs(P))))
    symmetry_error = float(np.max(abs(P-P.T)))
    if symmetry_error > PSD_ROUNDOFF_FACTOR*scale:
        raise ValueError('penalty must be symmetric up to floating-point roundoff')
    # The symmetric part gives precisely the same real scalar quadratic. This
    # removes only an accepted roundoff-size antisymmetric component, not a
    # negative eigenvalue or an indefinite direction.
    P = .5*P+.5*P.T
    eig = np.linalg.eigvalsh(P)
    spectral_scale = max(1., float(np.max(abs(eig))))
    if eig[0] < -PSD_ROUNDOFF_FACTOR*spectral_scale:
        raise ValueError('penalty must be positive semidefinite up to spectral roundoff')
    return X,Y,b,w,M,P,{'penalty_symmetry_roundoff_max_abs':symmetry_error,
        'penalty_minimum_eigenvalue_computed':float(eig[0]),
        'penalty_spectral_roundoff_tolerance':PSD_ROUNDOFF_FACTOR*spectral_scale,
        'negative_roundoff_eigenvalue_projected_away':False}


def _terms(c, X, Y, b, w, M, P, *, hessian=True):
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            f = b+X@c
            predicted = np.exp(f)
            objective = float(w@(predicted-Y*f)/M+.5*(c@P@c))
            gradient = X.T@(w*(predicted-Y))/M+P@c
            matrix = X.T@((w*predicted/M)[:,None]*X)+P if hessian else None
    except FloatingPointError as exc:
        raise ArithmeticError('weighted quasi-risk is not representable') from exc
    if not math.isfinite(objective) or not np.isfinite(gradient).all() or (matrix is not None and not np.isfinite(matrix).all()):
        raise ArithmeticError('weighted quasi-risk is not representable')
    if matrix is not None:
        matrix = .5*matrix+.5*matrix.T
    return objective,gradient,matrix


def weighted_risk_terms(coefficients, features, labels, baseline, weights, maximum_label, penalty_matrix):
    """Return normalized penalized objective, analytic gradient and Hessian."""
    X,Y,b,w,M,P,_ = _prepare(features,labels,baseline,weights,maximum_label,penalty_matrix)
    c = _array(coefficients,'coefficients')
    if c.shape != (COEFFICIENTS,):
        raise ValueError('exactly 35 physical coefficients required')
    return _terms(c,X,Y,b,w,M,P)


def projected_gradient(coefficients, gradient, coefficient_bound):
    """Box normal-cone residual; only actual boundaries remove components."""
    c, g = _array(coefficients,'coefficients'),_array(gradient,'gradient')
    A = _scalar(coefficient_bound,'coefficient_bound',positive=True)
    if c.shape != g.shape or c.shape != (COEFFICIENTS,) or np.any(abs(c) > A):
        raise ValueError('aligned feasible 35-coefficient box point required')
    result = g.copy()
    result[(c == -A)&(g > 0)] = 0.
    result[(c == A)&(g < 0)] = 0.
    return result


def fit_weighted_risk(features, labels, baseline, weights, maximum_label,
                      coefficient_bound, penalty_matrix, minimum_label):
    """One zero-start strict L-BFGS-B fit; no Newton, retry, or warm start.

Returns (physical_coefficients ndarray, JSON-native diagnostics). The supplied
minimum label is checked, not inferred from fitted/evaluation outcomes. Gram,
penalty, row-L1 and baseline-floor diagnostics permit a separately justified
global strong-convexity calculation; the local Hessian alone does not.
"""
    X,Y,b,w,M,P,metadata = _prepare(features,labels,baseline,weights,maximum_label,penalty_matrix)
    A = _scalar(coefficient_bound,'coefficient_bound',positive=True)
    floor = _scalar(minimum_label,'minimum_label',positive=True)
    if floor > M or np.any(Y < floor):
        raise ValueError('labels must respect the supplied positive minimum')
    if np.any(b < math.log(floor)-1e-12) or np.any(b > math.log(M)+1e-12):
        raise ValueError('baseline must respect known observation bounds up to log roundoff')
    initial = np.zeros(COEFFICIENTS)
    initial_value = _terms(initial,X,Y,b,w,M,P,hessian=False)[0]
    calls = 0
    def objective(c):
        nonlocal calls
        calls += 1
        value,gradient,_ = _terms(c,X,Y,b,w,M,P,hessian=False)
        return value,gradient
    optimized = minimize(objective,initial,method='L-BFGS-B',jac=True,
        bounds=[(-A,A)]*COEFFICIENTS,options=dict(OPTIMIZER_OPTIONS))
    c = _array(optimized.x,'optimizer coefficients')
    if c.shape != (COEFFICIENTS,) or np.any(abs(c) > A):
        raise ArithmeticError('optimizer returned an infeasible point')
    value,gradient,hessian = _terms(c,X,Y,b,w,M,P)
    projected = projected_gradient(c,gradient,A)
    # Every summand is nonnegative for a feasible point. In real arithmetic
    # this equals g.c + A||g||_1, the convex first-order box suboptimality bound.
    gap = math.fsum(abs(float(g))*(A+(float(v) if g >= 0 else -float(v))) for v,g in zip(c,gradient))
    gram = X.T@(w[:,None]*X)
    gram = .5*gram+.5*gram.T
    gram_eig, local_eig = np.linalg.eigvalsh(gram),np.linalg.eigvalsh(hessian)
    row_l1 = np.sum(abs(X),axis=1)
    actual_floor = min(floor,math.exp(float(np.min(b))))
    diagnostics = {'solver':'SCIPY_L_BFGS_B','solver_success':bool(optimized.success),
        'solver_status':int(optimized.status),'solver_message':str(optimized.message),
        'iterations':int(optimized.nit),'function_evaluations':int(optimized.nfev),
        'gradient_evaluations':int(optimized.njev),'observed_optimizer_objective_calls':calls,
        'initial_and_final_diagnostic_objective_calls':2,'full_hessian_diagnostic_calls':1,
        'optimizer_options':dict(OPTIMIZER_OPTIONS),'initial_coefficients':'ALL_ZERO',
        'newton_polish_performed':False,'retries':0,
        'initial_objective':initial_value,'final_objective':value,
        'physical_coefficients':c.tolist(),'gradient':gradient.tolist(),
        'projected_gradient':projected.tolist(),'projected_gradient_max_abs':float(max(abs(projected))),
        'box_first_order_gap':gap,'box_gap_is_outward_rounded_certificate':False,
        'box_gap_requires_convexity_and_exact_arithmetic_for_rigorous_bound':True,
        'local_hessian_minimum_eigenvalue':float(local_eig[0]),
        'weighted_gram_minimum_eigenvalue':float(gram_eig[0]),
        'weighted_gram_maximum_eigenvalue':float(gram_eig[-1]),
        'weighted_gram_eigenvalues':gram_eig.tolist(),
        'local_hessian_is_global_strong_convexity_certificate':False,
        'computed_eigenvalues_are_interval_certified':False,
        'feature_maximum_row_l1_norm':float(max(row_l1)),
        'feature_minimum_entry':float(np.min(X)),
        'feature_partition_of_unity_max_abs_error':float(max(abs(X.sum(axis=1)-1))),
        'minimum_baseline':float(np.min(b)),'known_minimum_label':floor,
        'conservative_baseline_density_floor_from_supplied_floor_and_observed_offset':actual_floor,
        'maximum_label':M,'coefficient_bound':A,'weights_sum':math.fsum(w),
        'minimum_weight':float(min(w)),'row_count':len(Y),'coefficient_count':COEFFICIENTS,
        'exact_boundary_count':int(np.sum(abs(c) == A)),
        'near_boundary_count_descriptive_1e_minus_10':int(np.sum(abs(c) >= A-1e-10)),
        'near_boundary_rule_used_for_projected_gradient':False,**metadata}
    return c.copy(),diagnostics


def population_quadrature(points_per_cell=16):
    """Positive E/O atoms plus uniform-core Gaussian quadrature, q16 or q32.

The existing feature family is reused without modification. Polynomial Gram
integration is exact in real arithmetic for these orders; the nonlinear
exponential likelihood-risk integrand is not polynomial and requires its own
quadrature agreement check.
"""
    if type(points_per_cell) is not int or points_per_cell not in (16,32):
        raise ValueError('predeclared 16 or 32 points per cell required')
    roots, gauss_weights = np.polynomial.legendre.leggauss(points_per_cell)
    edges = np.linspace(-4.5,4.5,33)
    half = (edges[1]-edges[0])/2
    continuous = ((edges[:-1,None]+half)+half*roots).reshape(-1)
    states = np.r_[np.array((0,1),dtype=np.int64),np.full(len(continuous),2,dtype=np.int64)]
    coordinates = np.r_[0.,0.,continuous]
    weights = np.r_[.25,.25,np.tile(.5*half*gauss_weights/9,32)]
    return {'states':states,'coordinates':coordinates,'weights':weights,
        'features':training_design(states,coordinates),'points_per_cell':points_per_cell,
        'continuous_cell_count':32,'design_probabilities':{'EMPTY':.25,'OTHER':.25,'CONTINUOUS':.5}}


def global_bound_diagnostics(fit):
    """Pure post-fit real-formula estimates, never a validated certificate.

For the finite weighted objective, row-L1 bound L gives Xc >= -A*L throughout
the coefficient box. With a true baseline density floor c, a true Gram lower
eigenvalue and a true PSD penalty lower eigenvalue, the displayed formula is a
global strong-convexity lower bound. Here eigenvalues and the floor are ordinary
floating-point diagnostics, not validated lower enclosures. The resulting
distance value is therefore an unvalidated estimate, not a rigorous error bar.
No negative computed eigenvalue is clipped or silently declared positive.
"""
    if not isinstance(fit, dict):
        raise ValueError('fit diagnostics mapping required')
    required = ('conservative_baseline_density_floor_from_supplied_floor_and_observed_offset',
        'maximum_label','coefficient_bound','feature_maximum_row_l1_norm',
        'weighted_gram_minimum_eigenvalue','penalty_minimum_eigenvalue_computed','box_first_order_gap')
    if any(name not in fit for name in required):
        raise ValueError('required post-fit bound diagnostic is missing')
    floor,M,A,L,gram,penalty,gap = (_scalar(fit[name],name) for name in required)
    if floor <= 0 or M <= 0 or floor > M or A <= 0 or L < 0 or gap < 0:
        raise ValueError('positive likelihood bounds, positive box and nonnegative row bound/gap required')
    exponent = A*L
    factor = (floor/M)*math.exp(-exponent)
    mu = factor*gram+penalty
    finite_mu = math.isfinite(mu)
    positive = finite_mu and mu > 0
    distance = None
    if positive:
        try:
            distance = 0. if gap == 0 else math.exp(.5*(math.log(2.)+math.log(gap)-math.log(mu)))
        except OverflowError:
            distance = None
    representable_distance = distance is not None and math.isfinite(distance)
    if not representable_distance:
        distance = None
    reason = ('POSITIVE_FINITE_UNVALIDATED_ESTIMATE' if positive and representable_distance else
        'NONPOSITIVE_GLOBAL_CURVATURE_ESTIMATE' if finite_mu and mu <= 0 else
        'NONFINITE_GLOBAL_CURVATURE_ESTIMATE' if not finite_mu else
        'COEFFICIENT_DISTANCE_ESTIMATE_NOT_REPRESENTABLE')
    return {'global_strong_convexity_lower_bound_estimate':mu if finite_mu else None,
        'coefficient_distance_upper_bound_estimate':distance,
        'positive_finite_curvature_estimate':positive,
        'vacuous':not (positive and representable_distance),'reason':reason,
        'formula':'(baseline_floor/M)*exp(-A*max_row_L1)*lambda_min(Gram)+lambda_min(penalty)',
        'distance_formula':'sqrt(2*box_first_order_gap/global_curvature)',
        'baseline_density_floor':floor,'maximum_label':M,'coefficient_bound':A,
        'feature_maximum_row_l1_norm':L,'likelihood_curvature_factor':factor,
        'coefficient_exponent_representable':math.isfinite(exponent),
        'weighted_gram_minimum_eigenvalue_computed':gram,
        'penalty_minimum_eigenvalue_computed':penalty,'box_first_order_gap':gap,
        'negative_computed_eigenvalues_clipped':False,
        'eigenvalues_baseline_floor_and_gap_are_validated_enclosures':False,
        'floating_point_certificate':False,
        'distance_is_rigorous_only_with_true_global_bound_and_true_gap_bound':True,
        'local_hessian_eigenvalue_used_as_global_bound':False,
        'optimizer_or_oracle_called':False}
