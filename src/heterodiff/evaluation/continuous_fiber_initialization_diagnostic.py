"""Independent capped-versus-uncapped guide initializer diagnostic.

This module considers the existing N=1, zero-BASE reference submodel and one
selected continuous observation.  It does not call FactorizedAssociationGuide
or its initializer.  The uncapped likelihood is derived directly from retained
ancestor Bernoulli events and retained-immigrant Poisson probabilities.

Both initial posteriors have the SAME capped initial prior Pi_N.  Their only
difference is the future transition law used to propagate the likelihood:
cap-respecting birth/death versus uncapped immigration/death.  Consequently
the returned mixed-law TV is an initializer discrepancy, not terminal sampler
error, learned-model error, or an empirical TV estimate from Monte Carlo.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import quad

from heterodiff.evaluation.continuous_fiber_conditional_benchmark import (
    STATES,
    ContinuousFiberSpec,
    ContinuousFiberConditionalBenchmark,
    GaussianComponent,
    MixedGaussianLaw,
)


def _normal_log_density(y, mean, variance):
    return -.5 * (math.log(2. * math.pi) + math.log(variance) + (y - mean) ** 2 / variance)


class ContinuousFiberInitializationDiagnostic:
    """Closed-form propagated likelihood and cap-conditioned initial mixtures."""

    def __init__(self, spec=None):
        spec = ContinuousFiberSpec() if spec is None else spec
        if type(spec) is not ContinuousFiberSpec:
            raise ValueError('spec must be a ContinuousFiberSpec')
        if spec.potential != (0., 0., 0.):
            raise ValueError('this diagnostic requires the zero-BASE reference process')
        self.oracle = ContinuousFiberConditionalBenchmark(spec)
        if not np.allclose(self.oracle.initial_state_probabilities, self.oracle.reference_state_prior, rtol=0., atol=1e-14):
            raise ValueError('both initializers must use the capped stationary reference state prior')
        if any(mean != 0. or variance != 1. for mean, variance in zip(spec.initial_fiber_means, spec.initial_fiber_variances)):
            raise ValueError('the capped reference prior requires standard-normal initial fibers')
        self.spec = spec

    def _parts(self, time, state):
        time = self.oracle._time(time)
        if state not in STATES:
            raise ValueError('unknown projected state')
        p = self.spec
        remaining = p.horizon - time
        survival = math.exp(-p.death_rate * remaining)
        retained_ancestor_probability = .5 * survival
        immigrant_mean = .5 * p.theta * (-math.expm1(-p.death_rate * remaining))
        contraction = math.exp(-p.continuous_rate * remaining / 2.)
        variance = p.observation_sd ** 2 - math.expm1(-p.continuous_rate * remaining)
        stationary_observation_density = math.exp(_normal_log_density(p.observation_value, 0., 1. + p.observation_sd ** 2))
        replacement = p.contamination * self.oracle.observation_reference_density
        factor = (1. - p.contamination) * math.exp(-immigrant_mean)
        # Exactly one selected immigrant, with every retained extra occurrence
        # excluded.  For an occupied initial state, its ancestor must not also
        # contribute an observation in this branch.
        immigrant = immigrant_mean * p.type_probabilities[1] * stationary_observation_density
        if state == 'EMPTY':
            return replacement + factor * immigrant, 0., contraction, variance
        constant = replacement + factor * (1. - retained_ancestor_probability) * immigrant
        signal = factor * retained_ancestor_probability if state == 'CONTINUOUS' else 0.
        if state == 'CONTINUOUS' and signal <= 0:
            raise ArithmeticError('uncapped surviving-coordinate likelihood weight is not representable')
        return constant, signal, contraction, variance

    def uncapped_log_likelihood_derivatives(self, time, state, coordinate=None):
        """Absolute observation log density and coordinate score/Hessian."""
        _, coordinate = self.oracle._state(state, coordinate)
        constant, signal, contraction, variance = self._parts(time, state)
        if state != 'CONTINUOUS':
            return {'log_likelihood': math.log(constant), 'gradient': 0., 'hessian': 0.}
        log_signal = math.log(signal) + _normal_log_density(self.spec.observation_value, contraction * coordinate, variance)
        log_likelihood = float(np.logaddexp(math.log(constant), log_signal))
        responsibility = math.exp(log_signal - log_likelihood)
        first = contraction * (self.spec.observation_value - contraction * coordinate) / variance
        second = -contraction ** 2 / variance
        return {'log_likelihood': log_likelihood,
                'gradient': responsibility * first,
                'hessian': responsibility * second + responsibility * (1. - responsibility) * first ** 2}

    def uncapped_backward_likelihood(self, time, state, coordinate=None):
        return math.exp(self.uncapped_log_likelihood_derivatives(time, state, coordinate)['log_likelihood'])

    def uncapped_evidence(self):
        prior = self.oracle.prior
        constant, signal, contraction, variance = self._parts(0., 'CONTINUOUS')
        continuous = math.fsum(c.weight * (constant + signal * math.exp(_normal_log_density(
            self.spec.observation_value, contraction * c.mean, variance + contraction ** 2 * c.variance)))
                              for c in prior.components)
        return (prior.empty_probability * self.uncapped_backward_likelihood(0., 'EMPTY')
                + prior.other_probability * self.uncapped_backward_likelihood(0., 'OTHER') + continuous)

    def uncapped_conditioned_initial(self):
        prior = self.oracle.prior
        constant, signal, contraction, noise = self._parts(0., 'CONTINUOUS')
        evidence = self.uncapped_evidence()
        components = []
        for c in prior.components:
            components.append(GaussianComponent(c.weight * constant / evidence, c.mean, c.variance))
            observed_variance = noise + contraction ** 2 * c.variance
            likelihood = math.exp(_normal_log_density(self.spec.observation_value, contraction * c.mean, observed_variance))
            mean = c.mean + c.variance * contraction / observed_variance * (self.spec.observation_value - contraction * c.mean)
            variance = c.variance * noise / observed_variance
            components.append(GaussianComponent(c.weight * signal * likelihood / evidence, mean, variance))
        return MixedGaussianLaw(
            prior.empty_probability * self.uncapped_backward_likelihood(0., 'EMPTY') / evidence,
            prior.other_probability * self.uncapped_backward_likelihood(0., 'OTHER') / evidence,
            tuple(components))

    def initializer_comparison(self):
        """Mixed-law TV from atom differences plus 1D absolute-density quadrature.

        QUADPACK's returned integration error is an estimate, not a certified
        mathematical interval.  No samples are used to estimate this TV.
        """
        exact = self.oracle.conditioned_initial()
        guide = self.uncapped_conditioned_initial()
        atom_l1 = abs(exact.empty_probability - guide.empty_probability) + abs(exact.other_probability - guide.other_probability)
        continuous_l1, error = quad(lambda x: abs(exact.continuous_density(x) - guide.continuous_density(x)),
                                    -np.inf, np.inf, epsabs=1e-11, epsrel=1e-11, limit=300)
        tv = .5 * (atom_l1 + continuous_l1)
        if not math.isfinite(tv) or not 0 <= tv <= 1. + 1e-10:
            raise ArithmeticError('mixed-law initialization discrepancy is invalid')
        return {'exact_capped_initial': exact.to_dict(), 'uncapped_guide_initial': guide.to_dict(),
                'exact_capped_conditional_coordinate_moments': dict(zip(('mean', 'variance'), exact.continuous_moments())),
                'uncapped_guide_conditional_coordinate_moments': dict(zip(('mean', 'variance'), guide.continuous_moments())),
                'exact_capped_evidence': self.oracle.evidence(), 'uncapped_guide_evidence': self.uncapped_evidence(),
                'atom_l1_difference': atom_l1, 'continuous_l1_difference': continuous_l1,
                'initial_total_variation': tv, 'total_variation_quadrature_error_estimate': .5 * error,
                'quadrature_error_is_certified_bound': False, 'monte_carlo_used': False}

    def score_comparison(self, times=(0., .25, .5, .75, 1.), coordinates=None):
        """Compare two analytic likelihoods on a declared finite query grid."""
        if coordinates is None:
            coordinates = tuple(float(v) for v in np.linspace(-3., 3., 21))
        if not isinstance(times, (tuple, list)) or not 1 <= len(times) <= 32:
            raise ValueError('one to 32 query times are required')
        if not isinstance(coordinates, (tuple, list)) or not 1 <= len(coordinates) <= 201:
            raise ValueError('one to 201 coordinate queries are required')
        rows = []
        for time in times:
            for state, coordinate in [('EMPTY', None), ('OTHER', None), *(('CONTINUOUS', x) for x in coordinates)]:
                capped = self.oracle.log_likelihood_derivatives(time, state, coordinate)
                uncapped = self.uncapped_log_likelihood_derivatives(time, state, coordinate)
                rows.append({'time': float(time), 'state': state, 'coordinate': coordinate,
                             'absolute_likelihood_difference': abs(math.exp(capped['log_likelihood']) - math.exp(uncapped['log_likelihood'])),
                             'absolute_log_likelihood_difference': abs(capped['log_likelihood'] - uncapped['log_likelihood']),
                             'absolute_score_difference': abs(capped['gradient'] - uncapped['gradient']),
                             'absolute_hessian_difference': abs(capped['hessian'] - uncapped['hessian'])})
        names = ('absolute_likelihood_difference', 'absolute_log_likelihood_difference',
                 'absolute_score_difference', 'absolute_hessian_difference')
        return {'times': list(times), 'coordinates': list(coordinates), 'query_count': len(rows),
                'maximum_observed_differences': {name: max(row[name] for row in rows) for name in names},
                'rows': rows, 'global_uniform_bound_claimed': False}

    def report(self):
        p = self.spec
        return {'schema_version': 'heterodiff-continuous-fiber-initialization-diagnostic-v1',
                'scope': 'ZERO_BASE_CAP_ONE_SAME_CAPPED_INITIAL_PRIOR_ANALYTIC_COMPARISON',
                'specification': {'theta': p.theta, 'type_probabilities': list(p.type_probabilities),
                                  'death_rate': p.death_rate, 'continuous_rate': p.continuous_rate,
                                  'horizon': p.horizon, 'observation_sd': p.observation_sd,
                                  'contamination': p.contamination, 'observation_value': p.observation_value},
                'initialization': self.initializer_comparison(),
                'likelihood_grid': self.score_comparison(times=tuple(p.horizon * u for u in (0., .25, .5, .75, 1.))),
                'learned_guide_or_sampler_imported': False, 'real_data_or_gpu_used': False}
