"""Fixed finite-indicator comparisons; never continuous empirical TV or KL.

Bounds are conditional-on-fitted-model Monte Carlo bounds under independent
record draws. Training-seed variation is descriptive, not an inferred population
confidence interval. Signed contrasts do not require common random numbers.
"""
import math
import numpy as np

INDICATOR_COUNT = 24
ROUTE_ALPHA = .005
MIXTURE_ALPHA = .0025
CONTRAST_ALPHA = .0025


def _vector(values):
    a = np.asarray(values, dtype=float)
    if a.shape != (24,) or not np.isfinite(a).all() or np.min(a) < 0 or np.max(a) > 1:
        raise ValueError('24 finite probability indicators required')
    if abs(a[:3].sum()-1.) > 1e-12 or np.min(np.diff(a[3:])) < -1e-12 or np.max(a[3:]) > a[2]+1e-12:
        raise ValueError('category / joint-CDF indicator constraints violated')
    return a


def _width(n, family_count, alpha, span=1.):
    if type(n) is not int or n < 1 or type(family_count) is not int or family_count < 1:
        raise ValueError('positive integer draw and family counts required')
    if not 0 < alpha < 1:
        raise ValueError('alpha must be in (0,1)')
    return span*math.sqrt(math.log(2.*family_count*INDICATOR_COUNT/alpha)/(2.*n))


def route_report(empirical, target, n, *, family_count=22):
    p, q = _vector(empirical), _vector(target)
    width = _width(n, family_count, ROUTE_ALPHA)
    error = np.abs(p-q)
    maximum = float(error.max())
    return {'empirical_indicators': p.tolist(), 'target_indicators': q.tolist(),
            'draw_count': n, 'maximum_indicator_error': maximum,
            'maximum_category_error': float(error[:3].max()),
            'maximum_joint_cdf_grid_error': float(error[3:].max()),
            'sampling_half_width': width, 'alpha_family': ROUTE_ALPHA,
            'finite_indicator_error_interval': [max(0., maximum-width), min(1., maximum+width)],
            'scope': 'FINITE_INDICATORS_CONDITIONAL_ON_FITTED_MODEL_NOT_TV_OR_KL'}


def seed_summary(seed_means, target, draws_per_seed, *, mixture_family_count=4):
    means = np.asarray([_vector(x) for x in seed_means])
    q = _vector(target)
    if len(means) < 1:
        raise ValueError('nonempty complete seed roster required')
    _width(draws_per_seed, 1, MIXTURE_ALPHA)
    width = _width(int(len(means)*draws_per_seed), mixture_family_count, MIXTURE_ALPHA)
    mean = means.mean(axis=0)
    error = float(np.abs(mean-q).max())
    per_seed = np.max(np.abs(means-q), axis=1)
    return {'seed_count': len(means), 'draws_per_seed': draws_per_seed,
            'mixture_empirical_indicators': mean.tolist(),
            'mixture_maximum_indicator_error': error,
            'mixture_maximum_category_error': float(np.abs(mean[:3]-q[:3]).max()),
            'mixture_maximum_joint_cdf_grid_error': float(np.abs(mean[3:]-q[3:]).max()),
            'mixture_sampling_half_width': width, 'alpha_family': MIXTURE_ALPHA,
            'mixture_error_interval': [max(0., error-width), min(1., error+width)],
            'per_seed_maximum_indicator_errors': per_seed.tolist(),
            'seed_error_mean_descriptive': float(per_seed.mean()),
            'seed_error_range_descriptive': [float(per_seed.min()), float(per_seed.max())],
            'seed_error_sd_descriptive': float(per_seed.std(ddof=1)) if len(means)>1 else None,
            'training_seed_population_confidence_claimed': False,
            'mixture_is_equal_weight_over_this_fitted_seed_roster_only': True}


def paired_error_summary(left_seed_means, right_seed_means, target, draws_per_seed, *, route_family_count=22):
    left = np.asarray([_vector(x) for x in left_seed_means])
    right = np.asarray([_vector(x) for x in right_seed_means])
    q = _vector(target)
    if left.shape != right.shape or len(left) < 1:
        raise ValueError('matching nonempty paired seed rosters required')
    differences = np.max(np.abs(left-q), axis=1)-np.max(np.abs(right-q), axis=1)
    width = 2.*_width(draws_per_seed, route_family_count, ROUTE_ALPHA)
    mean = float(differences.mean())
    return {'per_seed_error_difference_left_minus_right': differences.tolist(),
            'mean_error_difference_left_minus_right': mean,
            'difference_sd_descriptive': float(differences.std(ddof=1)) if len(left)>1 else None,
            'sampling_half_width': width,
            'per_seed_error_difference_intervals': [[max(-1.,float(x)-width),min(1.,float(x)+width)] for x in differences],
            'mean_error_difference_interval': [max(-1.,mean-width),min(1.,mean+width)],
            'covered_by_route_family_alpha': ROUTE_ALPHA,
            'training_seed_population_confidence_claimed': False,
            'scope': 'AVERAGE_OF_PAIRED_FINITE_INDICATOR_ERRORS_NOT_ERROR_OF_MIXTURE'}


def paired_contrast(left_seed_means, right_seed_means, draws_per_seed, *, family_count=2):
    left = np.asarray([_vector(x) for x in left_seed_means])
    right = np.asarray([_vector(x) for x in right_seed_means])
    if left.shape != right.shape or len(left) < 1:
        raise ValueError('matching nonempty paired seed rosters required')
    _width(draws_per_seed, 1, CONTRAST_ALPHA)
    difference = (left-right).mean(axis=0)
    width = _width(int(len(left)*draws_per_seed), family_count, CONTRAST_ALPHA, span=2.)
    return {'signed_indicator_difference_left_minus_right': difference.tolist(),
            'sampling_half_width': width, 'alpha_family': CONTRAST_ALPHA,
            'signed_indicator_intervals': [[max(-1., float(x)-width), min(1., float(x)+width)] for x in difference],
            'common_random_numbers_claimed': False,
            'paired_by_training_seed_and_evaluation_index': True,
            'training_seed_population_confidence_claimed': False,
            'scope': 'SIGNED_PROBABILITY_DIFFERENCE_NOT_ERROR_OR_SUPERIORITY_INTERVAL'}
