"""Synthetic BASE-equation and few-update tests; not production qualification."""

from fractions import Fraction
import math

import numpy as np
import pytest
import torch

from heterodiff.data.two_domain_factorized_state import (
    FactoredEvent, FactorizedMetadataReference, PhysioStateKey, RetailStateKey,
    TrainInformedMetadataReference,
)
from heterodiff.evaluation import two_domain_count_normalized_event_cks as cks
from heterodiff.experiments.factorized_base_training import (
    FactorizedBaseTrainingError, base_objective_on_corrupted_states, jump_flux_terms,
    relative_continuous_score_terms, train_base_step,
)
from heterodiff.models.factorized_configuration_energy_torch import (
    BoundedFactorizedConfigurationEnergy, FactorizedConfigurationBatch,
    FactorizedEnergyArchitecture, FactorizedEnergyLimits,
)
from heterodiff.processes.factorized_hybrid_sampler import ExactFactorizedReference, FactorizedSchedule
from heterodiff.theory.factorized_smooth_amendment import AmendmentParameters, FactorizedSmoothOracle


def make_source(domain):
    if domain == cks.PHYSIONET_DOMAIN_ID:
        return (FactoredEvent(PhysioStateKey(7, "GCS", "ATOMIC", Fraction(4))),
                FactoredEvent(PhysioStateKey(7, "HR", "POSITIVE"), 0.25))
    def key(branch):
        return RetailStateKey("C000007", "code", "", -2, (2010, 1, 1, 0, 0, 0, 0), None, branch)
    return (FactoredEvent(key("ZERO")), FactoredEvent(key("NEGATIVE"), 0.25))


def setup(domain):
    source = make_source(domain)
    q = TrainInformedMetadataReference(FactorizedMetadataReference(domain), source, beta=Fraction(1, 4))
    p = AmendmentParameters(0.5, 4, 4, 0.25, 0.01, 0.25, 0.1, 0.25)
    oracle = FactorizedSmoothOracle(q, p)
    process = ExactFactorizedReference(oracle, FactorizedSchedule(1.0, 0.125, 1.0, 1.0))
    spec = FactorizedEnergyArchitecture("SYNTHETIC_BASE_TEST:" + domain, 4, 1.0, 2.0, 1.0, 1.0,
                                       FactorizedEnergyLimits(4, 16, 2048, 16384))
    model = BoundedFactorizedConfigurationEnergy(spec, initialization_seed=11)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001, betas=(.9, .999), eps=1e-8,
                                  weight_decay=0., amsgrad=False, maximize=False,
                                  foreach=False, fused=False, capturable=False, differentiable=False)
    return source, process, model, optimizer


def test_continuous_formula_and_parameter_gradient_match_exact_scalar_quadratic():
    x = torch.tensor([.4], requires_grad=True)
    a = torch.tensor(.3, requires_grad=True)
    b = torch.tensor(.2, requires_grad=True)
    values = .5 * a * x.square() + b * x
    batch = FactorizedConfigurationBatch("synthetic", (b"scalar",), (1,), (x,), (0,),
                                         torch.tensor([.5]), torch.zeros(1, 64))
    terms = relative_continuous_score_terms(values, batch)
    expected_gradient = .3 * .4 + .2
    assert float(terms.detach()) == pytest.approx(.5 * expected_gradient**2 + .3 - .4 * expected_gradient, abs=1e-7)
    terms.sum().backward()
    assert float(a.grad) == pytest.approx(expected_gradient * .4 + 1 - .4**2, abs=1e-7)
    assert float(b.grad) == pytest.approx(expected_gradient - .4, abs=1e-7)


def test_atomic_coordinates_have_no_score_or_hessian_term_and_no_padding():
    parameter = torch.tensor(2., requires_grad=True)
    coordinate = torch.empty(0, requires_grad=True)
    batch = FactorizedConfigurationBatch("synthetic", (b"atom",), (0,), (coordinate,), (0,),
                                         torch.tensor([.5]), torch.zeros(1, 64))
    result = relative_continuous_score_terms(parameter.reshape(1), batch)
    assert float(result.detach()) == 0.0
    result.sum().backward()
    assert coordinate.grad is None and float(parameter.grad) == 0.0


def test_jump_flux_has_positive_linear_term_and_unnormalized_rate_once():
    source = torch.tensor([.1, 0.], requires_grad=True)
    destination = torch.tensor([.6, -2.], requires_grad=True)
    rates = torch.tensor([2., 3.], dtype=torch.float64)
    result = jump_flux_terms(source, destination, rates)
    assert result.detach().tolist() == pytest.approx([2 * (math.exp(.5) + .5), 3 * (math.exp(-2) - 2)], rel=1e-7)
    result.sum().backward()
    assert destination.grad.tolist() == pytest.approx([2 * (math.exp(.5) + 1), 3 * (math.exp(-2) + 1)], rel=1e-7)
    assert torch.equal(source.grad, -destination.grad)


@pytest.mark.parametrize("domain", [cks.PHYSIONET_DOMAIN_ID, cks.RETAIL_DOMAIN_ID])
def test_actual_base_model_objective_backward_and_three_reproducible_updates(domain):
    source, process, model, optimizer = setup(domain)
    second_source, second_process, second_model, second_optimizer = setup(domain)
    rng, repeated_rng = np.random.default_rng(67), np.random.default_rng(67)
    global_state = torch.random.get_rng_state().clone()
    reports, repeats = [], []
    for _ in range(3):
        reports.append(train_base_step(model, process, (source,), context=torch.zeros(64),
                                       rng=rng, optimizer=optimizer, sample_count=2, jump_weight=1.0))
        repeats.append(train_base_step(second_model, second_process, (second_source,), context=torch.zeros(64),
                                       rng=repeated_rng, optimizer=second_optimizer, sample_count=2, jump_weight=1.0))
    assert reports == repeats
    assert all(torch.equal(left, right) for left, right in zip(model.parameters(), second_model.parameters()))
    assert torch.equal(global_state, torch.random.get_rng_state())
    for report in reports:
        assert math.isfinite(report["loss"])
        assert report["changed_parameter_tensors"] > 0
        assert report["loss"] == pytest.approx(report["continuous_loss"] + report["jump_loss"])
        assert all(.125 < time < 1. for time in report["forward_times"])
        assert report["one_proposal_unnormalized_jump_weight"] is True
        for field in ("atomic_coordinates_differentiated", "train_roster_admission_verified",
                      "production_cadence_completed", "exact_population_minimizer_representable_claimed", "gpu_execution"):
            assert report[field] is False
    assert all(value.dtype == torch.float32 and bool(torch.isfinite(value).all()) for value in model.parameters())


def test_objective_scales_unnormalized_rate_once_and_rejects_negative_weights():
    source, _, model, _ = setup(cks.PHYSIONET_DOMAIN_ID)
    kwargs = dict(model=model, states=(source,), destinations=((source[0],),), forward_times=(.5,),
                  context=torch.zeros(64), jump_weight=2.0)
    first = base_objective_on_corrupted_states(**kwargs, continuous_rates=(1.0,), jump_rates=(3.0,))
    doubled = base_objective_on_corrupted_states(**kwargs, continuous_rates=(2.0,), jump_rates=(6.0,))
    assert float(doubled.total.detach()) == pytest.approx(2 * float(first.total.detach()), abs=1e-7)
    assert float(first.total.detach()) == pytest.approx(float(first.continuous.detach()) + 2 * float(first.jump.detach()))
    with pytest.raises(FactorizedBaseTrainingError, match="NONNEGATIVE_RATES"):
        base_objective_on_corrupted_states(**kwargs, continuous_rates=(1.0,), jump_rates=(-1.0,))
    # The API reports supplied weights; it cannot authenticate an arbitrary
    # externally normalized vector as a genuine proposal RN factor.


def test_invalid_optimizer_or_context_rejects_before_parameter_update():
    source, process, model, optimizer = setup(cks.PHYSIONET_DOMAIN_ID)
    before = tuple(parameter.detach().clone() for parameter in model.parameters())
    optimizer.param_groups[0]["weight_decay"] = .1
    with pytest.raises(FactorizedBaseTrainingError, match="ADAMW_SETTINGS"):
        train_base_step(model, process, (source,), context=torch.zeros(64), rng=np.random.default_rng(1),
                        optimizer=optimizer, sample_count=1, jump_weight=1.0)
    optimizer.param_groups[0]["weight_decay"] = 0.
    with pytest.raises(FactorizedBaseTrainingError, match="CONTEXT_VECTOR"):
        train_base_step(model, process, (source,), context=torch.zeros(63), rng=np.random.default_rng(1),
                        optimizer=optimizer, sample_count=1, jump_weight=1.0)
    assert all(torch.equal(left, right) for left, right in zip(before, model.parameters()))


def test_cpu_objective_placement_survives_ambient_meta_default():
    source, _, model, _ = setup(cks.PHYSIONET_DOMAIN_ID)
    context = torch.zeros(64, device="cpu")
    with torch.device("meta"):
        objective = base_objective_on_corrupted_states(
            model, (source,), ((source[0],),), (.5,), context,
            (1.0,), (2.0,), jump_weight=1.0)
        assert all(value.device.type == "cpu" for value in (
            objective.total, objective.continuous, objective.jump))
        assert math.isfinite(float(objective.total.detach()))
        objective.total.backward()
        assert all(parameter.grad is None or parameter.grad.device.type == "cpu"
                   for parameter in model.parameters())
