"""Independent Bernoulli/Poisson and native-guide checks of the initializer law."""

from dataclasses import replace
from fractions import Fraction
import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm, poisson

from heterodiff.evaluation.continuous_fiber_conditional_benchmark import ContinuousFiberSpec
from heterodiff.evaluation.continuous_fiber_initialization_diagnostic import ContinuousFiberInitializationDiagnostic


@pytest.fixture(params=[(.8, .7), (2.5, 1.4)])
def diagnostic(request):
    theta, y = request.param
    return ContinuousFiberInitializationDiagnostic(ContinuousFiberSpec(theta=theta, observation_value=y))


def _enumerated_clean_density(diagnostic, time, state, coordinate):
    """Enumerate retained-ancestor count and immigrant count separately."""
    p = diagnostic.spec
    remaining = p.horizon - time
    ancestor_retention = .5 * math.exp(-p.death_rate * remaining)
    immigration = .5 * p.theta * (1 - math.exp(-p.death_rate * remaining))
    a = math.exp(-p.continuous_rate * remaining / 2)
    signal_sd = math.sqrt(p.observation_sd ** 2 + 1 - a ** 2)
    immigrant_sd = math.sqrt(1 + p.observation_sd ** 2)
    total = 0.
    ancestor_outcomes = [(False, 1.)] if state == 'EMPTY' else [(False, 1 - ancestor_retention), (True, ancestor_retention)]
    for retained, mass in ancestor_outcomes:
        # More than one total retained occurrence is not this observation.
        for immigrant_count in range(4):
            if int(retained) + immigrant_count != 1:
                continue
            probability = mass * poisson.pmf(immigrant_count, immigration)
            if retained and state == 'CONTINUOUS':
                total += probability * norm.pdf(p.observation_value, a * coordinate, signal_sd)
            elif not retained:
                total += probability * p.type_probabilities[1] * norm.pdf(p.observation_value, 0., immigrant_sd)
    return total


@pytest.mark.parametrize('time', [0., .4, 1.])
@pytest.mark.parametrize('state,coordinate', [('EMPTY', None), ('OTHER', None), ('CONTINUOUS', -.5), ('CONTINUOUS', 1.2)])
def test_likelihood_matches_separate_ancestor_and_immigrant_enumeration(diagnostic, time, state, coordinate):
    p = diagnostic.spec
    expected = p.contamination * diagnostic.oracle.observation_reference_density + (1 - p.contamination) * _enumerated_clean_density(
        diagnostic, time, state, coordinate)
    assert diagnostic.uncapped_backward_likelihood(time, state, coordinate) == pytest.approx(expected, rel=3e-14, abs=2e-16)


def test_extra_retained_ancestor_factor_is_required_for_other_category(diagnostic):
    # OTHER cannot itself produce the selected-key observation.  It must fail
    # to survive-and-be-retained, even when a matching immigrant is observed.
    p = diagnostic.spec
    c0 = p.contamination * diagnostic.oracle.observation_reference_density
    empty_clean = diagnostic.uncapped_backward_likelihood(0., 'EMPTY') - c0
    other_clean = diagnostic.uncapped_backward_likelihood(0., 'OTHER') - c0
    retention = .5 * math.exp(-p.death_rate * p.horizon)
    assert other_clean / empty_clean == pytest.approx(1 - retention, rel=3e-15)


def test_uncapped_evidence_and_initializer_equal_direct_bayes_quadrature(diagnostic):
    prior = diagnostic.oracle.prior
    guide = diagnostic.uncapped_conditioned_initial()
    continuous, error = quad(lambda x: prior.continuous_density(x) * diagnostic.uncapped_backward_likelihood(0., 'CONTINUOUS', x),
                              -np.inf, np.inf, epsabs=1e-12, epsrel=1e-12)
    evidence = (prior.empty_probability * diagnostic.uncapped_backward_likelihood(0., 'EMPTY')
                + prior.other_probability * diagnostic.uncapped_backward_likelihood(0., 'OTHER') + continuous)
    assert error < 1e-11
    assert evidence == pytest.approx(diagnostic.uncapped_evidence(), rel=1e-12)
    assert guide.state_probabilities[2] == pytest.approx(continuous / evidence, rel=1e-12)
    for coordinate in (-3., -.5, .7, 2.):
        expected = prior.continuous_density(coordinate) * diagnostic.uncapped_backward_likelihood(0., 'CONTINUOUS', coordinate) / evidence
        assert guide.continuous_density(coordinate) == pytest.approx(expected, rel=2e-12)
    assert sum(guide.state_probabilities) == pytest.approx(1., abs=2e-15)


def test_initializer_components_have_correct_square_completion_parameters(diagnostic):
    law = diagnostic.uncapped_conditioned_initial()
    p = diagnostic.spec
    a = math.exp(-p.continuous_rate * p.horizon / 2)
    assert len(law.components) == 2
    assert law.components[0].mean == 0.
    assert law.components[0].variance == 1.
    assert law.components[1].mean == pytest.approx(a * p.observation_value / (1 + p.observation_sd ** 2), rel=2e-15)
    assert law.components[1].variance == pytest.approx(1 - a ** 2 / (1 + p.observation_sd ** 2), rel=2e-15)


def test_initial_tv_matches_fine_partition_lower_bound_and_quad_error(diagnostic):
    comparison = diagnostic.initializer_comparison()
    exact = diagnostic.oracle.conditioned_initial()
    guide = diagnostic.uncapped_conditioned_initial()
    grid = np.linspace(-12., 12., 2401)
    cdf_difference = np.array([exact.continuous_cdf(float(x)) - guide.continuous_cdf(float(x)) for x in grid])
    binned_continuous_l1 = np.abs(np.diff(cdf_difference)).sum()
    binned_tv = .5 * (comparison['atom_l1_difference'] + binned_continuous_l1)
    assert binned_tv <= comparison['initial_total_variation'] + 3e-11
    assert comparison['initial_total_variation'] - binned_tv < 2e-6
    assert comparison['initial_total_variation'] > .001
    assert comparison['total_variation_quadrature_error_estimate'] < 1e-10
    assert comparison['monte_carlo_used'] is False
    assert comparison['quadrature_error_is_certified_bound'] is False


@pytest.mark.parametrize('time, coordinate', [(0., -.5), (.3, .2), (1., 1.2)])
def test_uncapped_analytic_score_and_hessian_match_finite_differences(diagnostic, time, coordinate):
    result = diagnostic.uncapped_log_likelihood_derivatives(time, 'CONTINUOUS', coordinate)
    step = 1e-4
    f = lambda x: math.log(diagnostic.uncapped_backward_likelihood(time, 'CONTINUOUS', x))
    gradient = (f(coordinate + step) - f(coordinate - step)) / (2 * step)
    hessian = (f(coordinate + step) - 2 * f(coordinate) + f(coordinate - step)) / step ** 2
    assert result['gradient'] == pytest.approx(gradient, abs=2e-8, rel=2e-7)
    assert result['hessian'] == pytest.approx(hessian, abs=3e-7, rel=3e-6)


def test_terminal_likelihood_is_not_approximated(diagnostic):
    for state, coordinate in [('EMPTY', None), ('OTHER', None), ('CONTINUOUS', -.5), ('CONTINUOUS', 1.2)]:
        actual = diagnostic.uncapped_log_likelihood_derivatives(diagnostic.spec.horizon, state, coordinate)
        exact = diagnostic.oracle.log_likelihood_derivatives(diagnostic.spec.horizon, state, coordinate)
        assert actual == pytest.approx(exact, rel=3e-14, abs=2e-15)


def test_no_jump_process_has_no_cap_likelihood_or_initializer_discrepancy():
    diagnostic = ContinuousFiberInitializationDiagnostic(ContinuousFiberSpec(death_rate=0.))
    report = diagnostic.report()
    assert report['initialization']['initial_total_variation'] < 2e-15
    assert max(report['likelihood_grid']['maximum_observed_differences'].values()) < 2e-14


def test_fixed_report_is_bounded_and_scope_is_explicit(diagnostic):
    report = diagnostic.report()
    assert report['likelihood_grid']['query_count'] == 115
    assert report['likelihood_grid']['global_uniform_bound_claimed'] is False
    assert report['learned_guide_or_sampler_imported'] is False
    assert report['real_data_or_gpu_used'] is False
    assert report['initialization']['initial_total_variation'] > 0.
    assert report['likelihood_grid']['maximum_observed_differences']['absolute_score_difference'] > .01


@pytest.mark.parametrize('updates', [
    {'potential': (0., 0., .1)}, {'initial_state_probabilities': (.2, .2, .6)},
    {'initial_fiber_means': (.2,)}, {'initial_fiber_variances': (.5,)},
])
def test_mismatched_base_or_prior_is_not_silently_compared(updates):
    with pytest.raises(ValueError):
        ContinuousFiberInitializationDiagnostic(replace(ContinuousFiberSpec(), **updates))


@pytest.mark.parametrize('times,coordinates', [([], [0.]), ([0.] * 33, [0.]), ([0.], []), ([0.], [0.] * 202)])
def test_unbounded_or_empty_query_grids_rejected(times, coordinates):
    with pytest.raises(ValueError):
        ContinuousFiberInitializationDiagnostic().score_comparison(times, coordinates)


@pytest.mark.parametrize('theta,y', [(.8, .7), (2.5, 1.4)])
def test_native_association_guide_matches_independent_absolute_likelihood_and_derivatives(theta, y):
    # The independent module never imports this implementation.  This separate
    # cross-check exercises the real full-support metadata law, not two fake
    # replacement keys; OTHER includes both atomic and continuous examples.
    import torch
    from heterodiff.data.two_domain_factorized_state import (
        FactoredEvent, FactorizedMetadataReference, PhysioStateKey, TrainInformedMetadataReference,
    )
    from heterodiff.theory.factorized_association_guide_torch import FactorizedAssociationGuide
    from heterodiff.theory.factorized_smooth_amendment import AmendmentParameters, FactorizedSmoothOracle
    key = PhysioStateKey(3, 'HR', 'POSITIVE')
    reference = TrainInformedMetadataReference(FactorizedMetadataReference('R3-PHYS'),
        (FactoredEvent(key, .2),), beta=Fraction(1, 4))
    rho = float(reference.mass(key).as_fraction())
    diagnostic = ContinuousFiberInitializationDiagnostic(ContinuousFiberSpec(
        theta=theta, observation_value=y, type_probabilities=(1 - rho, rho)))
    smooth = FactorizedSmoothOracle(reference, AmendmentParameters(
        reference_count_mean=theta, reference_cap=1, observation_cap=1, death_rate=1.,
        target_contamination=.1, target_log_value_sd=.25,
        observation_contamination=.1, observation_log_value_sd=.5))
    guide = FactorizedAssociationGuide(smooth)
    observed = (FactoredEvent(key, y),)
    cases = [('EMPTY', ()), ('OTHER', (FactoredEvent(PhysioStateKey(3, 'MechVent', 'ATOMIC', Fraction(1))),)),
             ('OTHER', (FactoredEvent(PhysioStateKey(4, 'HR', 'POSITIVE'), .2),))]
    cases += [('CONTINUOUS', (FactoredEvent(key, z),)) for z in (-1., .2, 1.5)]
    for time in (0., .5, 1.):
        for label, state in cases:
            coordinates = tuple(torch.tensor([] if e.coordinate is None else [e.coordinate],
                                            dtype=torch.float64, requires_grad=True) for e in state)
            actual = guide.log_value(state, observed, coordinates, jump_clock=1. - time, continuous_clock=1. - time)
            z = state[0].coordinate if label == 'CONTINUOUS' else None
            independent = diagnostic.uncapped_log_likelihood_derivatives(time, label, z)
            expected_log_rn = independent['log_likelihood'] - math.log(diagnostic.oracle.observation_reference_density)
            assert float(actual.detach()) == pytest.approx(expected_log_rn, rel=2e-13, abs=2e-13)
            if state and state[0].key.dimension:
                grad, = torch.autograd.grad(actual, coordinates[0], create_graph=True)
                assert float(grad[0].detach()) == pytest.approx(independent['gradient'], rel=2e-12, abs=2e-13)
                if grad.requires_grad:
                    hessian, = torch.autograd.grad(grad[0], coordinates[0])
                    assert float(hessian[0]) == pytest.approx(independent['hessian'], rel=2e-12, abs=2e-13)
