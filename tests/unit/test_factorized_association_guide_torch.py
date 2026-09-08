"""Local synthetic guide/sampler tests, not full-domain qualification."""
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import math

import numpy as np
import pytest
import torch

from heterodiff.data.two_domain_factorized_state import (
    FactoredEvent, FactorizedMetadataReference, PhysioStateKey,
    TrainInformedMetadataReference,
)
from heterodiff.theory.factorized_smooth_amendment import (
    AmendmentParameters, FactorizedSmoothOracle, OracleLimits,
)
from heterodiff.theory.factorized_association_guide_torch import (
    FactorizedAssociationGuide, FactorizedGuideError, _sample_log_weights,
)


X = PhysioStateKey(2, "HR", "POSITIVE")
Y = PhysioStateKey(3, "HR", "POSITIVE")
A = FactoredEvent(PhysioStateKey(0, "GCS", "ATOMIC", Fraction(3)))
B = FactoredEvent(PhysioStateKey(1, "MechVent", "ATOMIC", Fraction(0)))


def event(value, key=X):
    return FactoredEvent(key, float(value))


def oracle(**overrides):
    params = AmendmentParameters(1.2, 4, 3, 0.7, 0.04, 0.2, 0.15, 0.3)
    return FactorizedSmoothOracle(FactorizedMetadataReference("R3-PHYS"), replace(params, **overrides))


def coords(state):
    return tuple(torch.tensor([] if x.coordinate is None else [x.coordinate],
                              dtype=torch.float64, device="cpu", requires_grad=True) for x in state)


@pytest.mark.parametrize("state", [(), (A,), (A, A, B), (event(0.4),),
                                   (event(0.5), event(-0.2), A)])
@pytest.mark.parametrize("observed", [(), (A,), (event(0.1),), (event(0.2), event(-0.4)), None])
@pytest.mark.parametrize("clocks", [(0.0, 0.0), (0.4, 0.8)])
def test_values_match_real_factorized_oracle_and_bounds(state, observed, clocks):
    raw = oracle()
    guide = FactorizedAssociationGuide(raw)
    actual = guide.log_value(state, observed, jump_clock=clocks[0], continuous_clock=clocks[1])
    expected = raw.observation_log_density(state, observed, jump_clock=clocks[0], continuous_clock=clocks[1])
    assert actual.dtype == torch.float64 and actual.shape == () and actual.device.type == "cpu"
    assert float(actual) == pytest.approx(expected, abs=2e-12)
    assert float(actual) <= guide.upper_log_bound(observed) + 2e-12


@pytest.mark.parametrize("clocks", [(0.0, 0.0), (0.3, 0.7)])
def test_actual_matching_coordinate_gradients_and_hessians(clocks):
    guide = FactorizedAssociationGuide(oracle())
    state, observed = (event(0.5), A, event(-0.2)), (event(0.2), event(-0.4))
    variables = coords(state)
    value = guide.log_value(state, observed, variables, jump_clock=clocks[0], continuous_clock=clocks[1])
    gradients = torch.autograd.grad(value, variables, create_graph=True)
    assert gradients[1].shape == (0,)
    h = 1e-5
    for index in (0, 2):
        plus, minus = list(state), list(state)
        plus[index] = event(state[index].coordinate + h)
        minus[index] = event(state[index].coordinate - h)
        vp = float(guide.log_value(tuple(plus), observed, jump_clock=clocks[0], continuous_clock=clocks[1]))
        vm = float(guide.log_value(tuple(minus), observed, jump_clock=clocks[0], continuous_clock=clocks[1]))
        assert float(gradients[index][0].detach()) == pytest.approx((vp-vm)/(2*h), rel=2e-7, abs=2e-7)
        diagonal = torch.autograd.grad(gradients[index][0], variables[index], retain_graph=True)[0][0]
        assert float(diagonal.detach()) == pytest.approx((vp-2*float(value.detach())+vm)/h**2, abs=1e-4)


@pytest.mark.parametrize("observed", [(event(0.2, Y),), None, ()])
def test_impossible_overflow_and_empty_observations_have_finite_zero_gradients(observed):
    guide = FactorizedAssociationGuide(oracle())
    state = (event(0.4), A)
    variables = coords(state)
    value = guide.log_value(state, observed, variables)
    derivatives = torch.autograd.grad(value, variables)
    assert all(bool(torch.isfinite(x).all()) and bool((x == 0).all()) for x in derivatives)


def test_supplied_coordinates_override_values_and_keep_occurrence_order():
    guide = FactorizedAssociationGuide(oracle())
    original = (event(90), event(-80))
    actual = (event(0.5), event(-0.2))
    variables = coords(actual)
    value = guide.log_value(original, (event(0.1),), variables)
    assert float(value.detach()) == pytest.approx(float(guide.log_value(actual, (event(0.1),))))
    gradient = torch.autograd.grad(value, variables)
    flipped = tuple(reversed(variables))
    reverse_value = guide.log_value(tuple(reversed(original)), (event(0.1),), flipped)
    reverse_gradient = torch.autograd.grad(reverse_value, flipped)
    assert torch.equal(gradient[0], reverse_gradient[1])


def test_coordinate_type_and_resource_refusals_before_rng():
    guide = FactorizedAssociationGuide(oracle(), maximum_dp_work=1)
    with pytest.raises(FactorizedGuideError, match="CPU_FLOAT64"):
        guide.log_value((event(0),), (), (torch.tensor([0.0]),))
    with pytest.raises(FactorizedGuideError, match="DP_RESOURCE"):
        guide.log_value((event(0),), (event(0), event(1)))
    guide = FactorizedAssociationGuide(oracle(observation_cap=1), maximum_posterior_work=5)
    rng = np.random.default_rng(4)
    before = deepcopy(rng.bit_generator.state)
    with pytest.raises(FactorizedGuideError, match="OVERFLOW_POSTERIOR_RESOURCE"):
        guide.sample_reference_posterior(None, rng, jump_clock=0.4)
    assert rng.bit_generator.state == before


def test_snapshot_and_train_mixture_identity():
    raw = oracle()
    guide = FactorizedAssociationGuide(raw)
    previous = float(guide.log_value((A,), (A,)))
    raw.parameters = replace(raw.parameters, observation_contamination=0.9)
    assert float(guide.log_value((A,), (A,))) == previous
    assert guide.identity_sha256 != FactorizedAssociationGuide(raw).identity_sha256
    one = TrainInformedMetadataReference(raw.reference, (A, B), beta=Fraction(1, 5))
    two = TrainInformedMetadataReference(raw.reference, (A, A, B), beta=Fraction(1, 5))
    ids = [FactorizedAssociationGuide(FactorizedSmoothOracle(ref, raw.parameters)).identity_sha256 for ref in (one, two)]
    assert ids[0] != ids[1]


def test_log_race_does_not_exponentiate_tiny_masses():
    rng = np.random.default_rng(8)
    assert {_sample_log_weights((-10000.0, -10001.0), rng) for _ in range(100)} == {0, 1}
    class Endpoint:
        def exponential(self):
            return 0.0
    with pytest.raises(FactorizedGuideError, match="NO_REDRAW"):
        _sample_log_weights((0.0,), Endpoint())


def test_retained_capped_count_distribution_and_rare_anchor_keys():
    raw = oracle(reference_cap=2)
    guide = FactorizedAssociationGuide(raw)
    observed, J = (A, B), 0.4
    p, theta, survival = raw.parameters, 1.2, math.exp(-0.7*J)
    prior_cap = sum(math.exp(-theta)*theta**n/math.factorial(n) for n in range(3))
    clean_evidence = math.exp(1-theta/2)*(theta/2)**2
    mean = theta*(1-survival/2)
    weights = []
    for n in range(3):
        hcount = sum(math.comb(2,b)*survival**b*(1-survival)**(2-b)*
                     math.exp(-mean)*mean**(n-b)/math.factorial(n-b)
                     for b in range(min(2,n)+1))
        weights.append(p.observation_contamination*math.exp(raw.count_log_prob(n))+
                       (1-p.observation_contamination)*clean_evidence*hcount/prior_cap)
    expected = np.array(weights)/sum(weights)
    rng, samples = np.random.default_rng(5), []
    for _ in range(1200):
        result = guide.sample_reference_posterior(observed, rng, jump_clock=J)
        assert result == tuple(sorted(result, key=lambda x:x.sort_key)) and len(result) <= 2
        samples.append(result)
    counts = Counter(map(len,samples))
    assert np.array([counts[i]/1200 for i in range(3)]) == pytest.approx(expected, abs=0.055)
    assert sum(any(x.key in (A.key,B.key) for x in sample) for sample in samples) > 300


@pytest.mark.parametrize("J", [0.0, 0.4])
def test_overflow_count_posterior_matches_oracle_without_coordinate_bias(J):
    raw = oracle(observation_cap=1)
    guide = FactorizedAssociationGuide(raw)
    weights = np.array([math.exp(raw.count_log_prob(n) + raw.observation_log_density((A,)*n, None, jump_clock=J))
                        for n in range(5)])
    weights /= sum(weights)
    actual_logs = guide._overflow_count_logs(*raw._clocks(J, 0.0)[:2])
    normalized = np.exp(np.array(actual_logs)-np.logaddexp.reduce(actual_logs))
    assert normalized == pytest.approx(weights, abs=2e-14)
    rng = np.random.default_rng(44)
    counts = Counter(len(guide.sample_reference_posterior(None, rng, jump_clock=J)) for _ in range(800))
    assert np.array([counts[n]/800 for n in range(5)]) == pytest.approx(weights, abs=0.065)


def test_continuous_ancestor_mean_variance_and_seed_repeatability():
    guide = FactorizedAssociationGuide(oracle(reference_cap=1, observation_contamination=1e-8))
    observed = (event(0.7),)
    def run(seed):
        rng = np.random.default_rng(seed)
        return [guide.sample_reference_posterior(observed, rng) for _ in range(400)]
    result = run(8)
    assert result == run(8)
    assert all(len(x)==1 and x[0].key == X for x in result)
    values = np.array([x[0].coordinate for x in result])
    assert values.mean() == pytest.approx(0.7/1.09, abs=0.045)
    assert values.var() == pytest.approx(0.09/1.09, abs=0.025)


def test_local_event_limit_is_refusal_not_extra_count_conditioning(monkeypatch):
    import heterodiff.theory.factorized_association_guide_torch as module
    raw = FactorizedSmoothOracle(oracle().reference, oracle().parameters, limits=OracleLimits(maximum_events=1))
    guide = FactorizedAssociationGuide(raw)
    calls = []
    def force(weights, rng):
        calls.append(tuple(weights))
        return 0 if len(calls)==1 else len(weights)-1
    monkeypatch.setattr(module,"_sample_log_weights",force)
    with pytest.raises(FactorizedGuideError, match="NO_DROPPING"):
        guide.sample_reference_posterior((), np.random.default_rng(2))
