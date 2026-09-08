"""Independent small end-to-end qualification of the proposed mixed-key path.

Invented records only: three real BASE updates and three real conditional
updates are NOT the frozen scientific cadence or a convergence/quality result.
No GPU, source data, clinical admission, or installed-runtime claim is made.
"""

from copy import deepcopy
from fractions import Fraction
import math

import numpy as np
import pytest
import torch

from heterodiff.data.two_domain_factorized_state import (
    FactoredEvent, FactorizedMetadataReference, PhysioStateKey, RetailStateKey,
    TrainInformedMetadataReference, encode_metric_event,
)
from heterodiff.evaluation import two_domain_count_normalized_event_cks as cks
from heterodiff.evaluation.two_domain_count_normalized_event_cks_production import (
    evaluate_configuration_kernel_symbol, evaluate_formal_cks_score,
)
from heterodiff.experiments.factorized_base_training import train_base_step
from heterodiff.experiments.factorized_conditional_pipeline import (
    FactorizedBasePopulation, FactorizedPopulationContext, FactorizedPipelineError,
    sample_conditional, train_conditional_step,
)
from heterodiff.experiments.factorized_conditional_training import (
    FactorizedConditionalModel, FactorizedObservation, FactorizedPhysicalPotential,
    FactorizedTrainingBatch,
)
from heterodiff.experiments.two_domain_baseline_registry import PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID
from heterodiff.models.factorized_configuration_energy_torch import (
    BoundedFactorizedConfigurationEnergy, FactorizedEnergyArchitecture, FactorizedEnergyLimits,
)
from heterodiff.processes.factorized_hybrid_sampler import (
    ExactFactorizedReference, FactorizedSchedule, FactorizedSamplerLimits,
    LearnedFactorizedSampler, conditional_initializer, heun_step,
)
from heterodiff.theory.factorized_association_guide_torch import FactorizedAssociationGuide
from heterodiff.theory.factorized_smooth_amendment import AmendmentParameters, FactorizedSmoothOracle


GRID = (0.0, 0.25, 0.5, 0.75, 1.0)


def source_for(domain):
    if domain == cks.PHYSIONET_DOMAIN_ID:
        return (FactoredEvent(PhysioStateKey(8, "MechVent", "ATOMIC", Fraction(1))),
                FactoredEvent(PhysioStateKey(8, "HR", "POSITIVE"), 0.25))
    def key(branch):
        return RetailStateKey("C000008", "sku", "", -2,
                              (2010, 2, 3, 4, 5, 6, 7), None, branch)
    return (FactoredEvent(key("ZERO")), FactoredEvent(key("NEGATIVE"), 0.25))


def adam(module):
    return torch.optim.AdamW(module.parameters(), lr=.001, betas=(.9, .999), eps=1e-8,
                             weight_decay=0., amsgrad=False, maximize=False, foreach=False,
                             fused=False, capturable=False, differentiable=False)


def untouched_synthetic_raw_truth(domain):
    """Independent raw decimal fixtures: never lifted, corrupted, or projected."""
    if domain == cks.PHYSIONET_DOMAIN_ID:
        return cks.physionet_configuration(tuple(
            cks.physionet_event_from_decimal_token(
                elapsed_minutes=8, parameter=parameter, value_text=value)
            for parameter, value in (("MechVent", "1"), ("HR", "80"))))
    return cks.retail_configuration((cks.retail_event_from_decimal_token(
        invoice_no="C000008", stock_code="sku", description="", quantity=-2,
        invoice_calendar=(2010, 2, 3, 4, 5, 6, 7), unit_price_text="-2.50",
        country=None),))


@pytest.fixture(scope="module", params=[cks.PHYSIONET_DOMAIN_ID, cks.RETAIL_DOMAIN_ID])
def trained_base(request):
    domain = request.param
    source = source_for(domain)
    q = TrainInformedMetadataReference(FactorizedMetadataReference(domain), source, beta=Fraction(1, 4))
    parameters = AmendmentParameters(.5, 4, 4, .2, .1, .25, .25, 1.0)
    oracle = FactorizedSmoothOracle(q, parameters)
    schedule = FactorizedSchedule(1.0, .25, .5, 1.0)
    reference = ExactFactorizedReference(oracle, schedule,
        FactorizedSamplerLimits(maximum_jump_candidates=20000, maximum_initialization_trials=20000))
    specification = FactorizedEnergyArchitecture(
        "LOCAL_FACTORIZED_PIPELINE:" + domain, 4, 1.0, .25, 1.0, 1.0,
        FactorizedEnergyLimits(4, 16, 2048, 16384))
    base = BoundedFactorizedConfigurationEnergy(specification, initialization_seed=197)
    optimizer = adam(base)
    rng = np.random.default_rng(991)
    reports = [train_base_step(base, reference, (source,), context=torch.zeros(64), rng=rng,
                               optimizer=optimizer, sample_count=2, jump_weight=1.0) for _ in range(3)]
    assert all(report["changed_parameter_tensors"] > 0 for report in reports)
    context = FactorizedPopulationContext(domain, "SYNTHETIC_TASK", b"synthetic-static-context", (0.0,) * 64)
    return source, reference, base, context, reports


def conditioner_for(base, reference, method):
    energy = BoundedFactorizedConfigurationEnergy(base.architecture, initialization_seed=198)
    return FactorizedConditionalModel(energy, guide=FactorizedAssociationGuide(reference.oracle),
                                      method_id=method, clean_hold=reference.schedule.clean_hold,
                                      remaining_clocks=reference.schedule.remaining_clocks,
                                      observation_seed=199, nuisance_seed=200)


@pytest.mark.parametrize("method", [PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID])
def test_both_domains_methods_real_updates_paths_and_f105_decode(trained_base, method):
    source, reference, base, context, base_reports = trained_base
    learner = conditioner_for(base, reference, method)
    population = FactorizedBasePopulation(base, reference, GRID, context)
    base_before = {name: value.detach().clone() for name, value in base.named_parameters()}
    optimizer = adam(learner)
    reports = [train_conditional_step(learner, population, optimizer=optimizer, reverse_time=None,
                                      run_seed=501, record_id=f"step-{i}".encode(), sample_count=1)
               for i in range(3)]
    for report in reports:
        assert math.isfinite(report["loss"]) and report["changed_parameter_elements"] > 0
        assert report["time_policy"] == "UNIFORM_FULL_REVERSE_INTERVAL"
        assert len(report["reverse_times"]) == 1 and 0 < report["reverse_times"][0] < 1
        assert report["base_paths_generated"] == 2
        assert report["query_refined_paths"] == 2
        assert report["actual_macrosteps"] == 2 * len(GRID)
        assert report["production_or_scientific_convergence_claimed"] is False
    assert all(torch.equal(base_before[name], value) for name, value in base.named_parameters())
    # Conditional initialization includes guide and residual, not BASE/nuisance.
    path = sample_conditional(base, learner, reference, GRID, context, (source[-1],),
                               run_seed=502, record_id=b"conditional-retained")
    assert path.reverse_grid == GRID and path.states[-1] is path.states[-2]
    assert path.diagnostics["reference_pi_n_initializer"] is False
    assert path.diagnostics["exact_learned_path_or_finite_rng_law_claimed"] is False
    for event in (*source, *path.terminal_state):
        metric = event.to_metric_event()
        assert metric.domain_id == context.domain_id
        record = encode_metric_event(metric)
        assert record.event.key == event.key
        assert record.diagnostics()["discrete_metadata_rounded"] is False
        assert record.diagnostics()["raw_decimal_or_binary64_origin_proven"] is False
        if event.key.dimension == 0:
            assert record.event.coordinate is None and record.decoded_native_roundtrip_error in (None, Fraction(0))
        else:
            assert type(record.exact_binary64_conversion_error) is Fraction
            assert type(record.decoded_native_roundtrip_error) is Fraction
            assert math.isfinite(float(record.exact_binary64_conversion_error))
            assert math.isfinite(float(record.decoded_native_roundtrip_error))
            assert math.isfinite(record.event.coordinate - event.coordinate)
    second_path = sample_conditional(base, learner, reference, GRID, context, (source[-1],),
                                     run_seed=503, record_id=b"conditional-metric-second")
    generated = tuple(cks.ExactConfiguration(context.domain_id, tuple(
        event.to_metric_event() for event in result.terminal_state)) for result in (path, second_path))
    raw_truth = untouched_synthetic_raw_truth(context.domain_id)
    before_truth = raw_truth.events
    # This is a two-draw metric seam, not the 128-group x64 checkpoint contract.
    kernel = cks.configuration_kernel(generated[0], raw_truth)
    kernel_value = evaluate_configuration_kernel_symbol(kernel)
    assert 0 <= kernel_value <= 1 and math.isfinite(kernel_value)
    score = cks.conditional_cks_score(generated, raw_truth)
    score_value = evaluate_formal_cks_score(score)
    assert math.isfinite(score_value) and -2 <= score_value <= 1
    assert raw_truth.events == before_truth == untouched_synthetic_raw_truth(context.domain_id).events
    assert len(base_reports) == 3  # Real BASE training, not a frozen random initializer.


def test_independent_pairs_replay_refine_queries_and_keep_context(trained_base):
    _, reference, base, context, _ = trained_base
    population = FactorizedBasePopulation(base, reference, GRID, context)
    first = population.sample_pair(reverse_time=.37, run_seed=603, record_id=b"pair")
    repeated = population.sample_pair(reverse_time=.37, run_seed=603, record_id=b"pair")
    assert first == repeated
    joint, product, paths = first
    assert joint.states == product.states == (paths[0].at_time(.37),)
    assert joint.reverse_times == product.reverse_times == (.37,)
    assert joint.observations[0].context_identity == product.observations[0].context_identity
    assert paths[0].diagnostics["stream_binding_sha256"] != paths[1].diagnostics["stream_binding_sha256"]
    assert all(path.diagnostics["reference_pi_n_initializer"] for path in paths)
    assert all(path.diagnostics["query_refined_grid"] for path in paths)
    assert .37 in paths[0].reverse_grid
    different_time = population.sample_pair(reverse_time=.38, run_seed=603, record_id=b"pair")
    assert different_time[0].law_id != joint.law_id
    assert all(path.diagnostics["same_unrefined_numerical_path_law_claimed"] is False for path in paths)


@pytest.mark.parametrize("method", [PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID])
def test_nuisance_changes_logits_but_never_physical_gradient_or_initializer(trained_base, method):
    source, reference, base, context, _ = trained_base
    model = conditioner_for(base, reference, method)
    observation = FactorizedObservation((source[-1],), context.domain_id, context.task_id, context.context_bytes)
    batch = FactorizedTrainingBatch((source,), (.5,), (observation,), "synthetic-declared-law")
    initial_logit = model.logits(batch).detach().clone()
    before = FactorizedPhysicalPotential(base, base_context=context.base_context,
                                         conditional_model=model, observation=observation)
    with torch.no_grad():
        model.nuisance.output.bias.add_(3.)
    after = FactorizedPhysicalPotential(base, base_context=context.base_context,
                                        conditional_model=model, observation=observation)
    assert torch.allclose(model.logits(batch).detach() - initial_logit, torch.tensor([3.], dtype=torch.float64))
    assert before.value_grad(.5, source) == after.value_grad(.5, source)
    assert before.initialization_log_tilt(0., source) == after.initialization_log_tilt(0., source)
    assert before.initialization_residual_log_tilt(source) == after.initialization_residual_log_tilt(source)
    changed_base = deepcopy(base)
    with torch.no_grad():
        changed_base.readout_output.bias.add_(1.)
    base_altered = FactorizedPhysicalPotential(changed_base, base_context=context.base_context,
                                              conditional_model=model, observation=observation)
    assert before.initialization_log_tilt(0., source) == base_altered.initialization_log_tilt(0., source)
    assert before.value(.5, source) != base_altered.value(.5, source)
    for observed in ((source[-1],), None):
        row = FactorizedObservation(observed, context.domain_id, context.task_id, context.context_bytes)
        physical = FactorizedPhysicalPotential(base, base_context=context.base_context, conditional_model=model, observation=row)
        draw = conditional_initializer(physical.model.guide, physical, observed, reference.schedule, method)
        first, second = draw(np.random.default_rng(604)), draw(np.random.default_rng(604))
        assert first == second and len(first) <= reference.parameters.reference_cap


def test_clean_hold_is_exact_copy_and_reference_order_does_not_change_paths(trained_base):
    source, reference, base, context, _ = trained_base
    physical = FactorizedPhysicalPotential(base, base_context=context.base_context, clean_hold=.25)
    class Counted:
        upper_value_bound = physical.upper_value_bound
        def __init__(self):
            self.calls = []
        def value(self, u, state):
            self.calls.append(u)
            return physical.value(u, state)
        def value_grad(self, u, state):
            self.calls.append(u)
            return physical.value_grad(u, state)
    wrapper = Counted()
    refined_hold = (0., .25, .5, .75, .875, 1.)
    first = LearnedFactorizedSampler(reference, wrapper, refined_hold, initializer=lambda rng: source)
    path = first.sample_path(run_seed=701, record_id=b"ordered")
    other = LearnedFactorizedSampler(reference, physical, GRID,
                                      initializer=lambda rng: tuple(reversed(source))).sample_path(run_seed=701, record_id=b"ordered")
    assert path.terminal_state == other.terminal_state
    assert path.states[-1] is path.states[-2] is path.states[-3]
    assert all(u <= .75 for u in wrapper.calls)
    assert path.diagnostics["stream_requests"] == other.diagnostics["stream_requests"]
    assert physical.value(.75, source) == physical.value(.875, source) == physical.value(1., source)


class ZeroPotential:
    upper_value_bound = 0.0
    def value(self, u, state):
        return 0.0
    def value_grad(self, u, state):
        return 0.0, tuple((0.0,) if event.key.dimension else () for event in state)


def test_actual_birth_death_and_continuous_path_operations_are_not_one_jump_surrogates(trained_base):
    source, reference, _, _, _ = trained_base
    original = reference.parameters
    p = AmendmentParameters(1.5, 4, 4, 2.0, original.target_contamination,
                             original.target_log_value_sd, original.observation_contamination,
                             original.observation_log_value_sd)
    fast = ExactFactorizedReference(FactorizedSmoothOracle(reference.reference, p),
                                    FactorizedSchedule(1., .25, 2., 1.))
    births = deaths = 0
    changed_continuous = False
    for seed in range(10):
        path = LearnedFactorizedSampler(fast, ZeroPotential(), GRID, initializer=lambda rng: source).sample_path(
            run_seed=800 + seed, record_id=b"zero-potential-known-reference")
        births += path.diagnostics["accepted_birth"]
        deaths += path.diagnostics["accepted_death"]
        changed_continuous |= any(event.key.dimension and event.coordinate != source[-1].coordinate
                                   for state in path.states[1:] for event in state)
        assert all(len(state) <= 4 for state in path.states)
        assert path.states[-1] is path.states[-2]
    assert births > 0 and deaths > 0 and changed_continuous


def test_heun_h_over_two_improves_coupled_ou_rms_error_against_known_exact_law():
    # This is a small known-law numerical qualification, not a learned-model
    # convergence theorem. Exact OU increments are jointly Gaussian with the
    # same Brownian increments used by both step sizes, including bridge noise.
    key = PhysioStateKey(1, "HR", "POSITIVE")
    dt = 1 / 16
    decay = math.exp(-dt / 2)
    covariance = -2 * math.expm1(-dt / 2)
    exact_variance = -math.expm1(-dt)
    residual_variance = exact_variance - covariance**2 / dt
    coarse_errors, fine_errors = [], []
    rng = np.random.default_rng(889)
    for _ in range(128):
        increments = np.asarray(rng.normal(size=16), dtype=float) * math.sqrt(dt)
        bridges = np.asarray(rng.normal(size=16), dtype=float)
        exact = .7
        fine = coarse = (FactoredEvent(key, .7),)
        for i in range(16):
            exact = decay * exact + covariance / dt * increments[i] + math.sqrt(residual_variance) * bridges[i]
            fine = heun_step(fine, i * dt, dt, ZeroPotential(), 1., ((float(increments[i]),),))
        for i in range(8):
            increment = float(increments[2 * i] + increments[2 * i + 1])
            coarse = heun_step(coarse, i * 2 * dt, 2 * dt, ZeroPotential(), 1., ((increment,),))
        coarse_errors.append((coarse[0].coordinate - exact)**2)
        fine_errors.append((fine[0].coordinate - exact)**2)
    coarse_rms = math.sqrt(math.fsum(coarse_errors) / 128)
    fine_rms = math.sqrt(math.fsum(fine_errors) / 128)
    assert 0 < fine_rms < .8 * coarse_rms


def test_pipeline_rejects_unbound_clock_callback_before_updating(trained_base):
    _, reference, base, context, _ = trained_base
    model = conditioner_for(base, reference, PRIMARY_METHOD_ID)
    population = FactorizedBasePopulation(base, reference, GRID, context)
    model.remaining_clocks = lambda u: reference.schedule.remaining_clocks(u)
    with pytest.raises(FactorizedPipelineError, match="reference-owned"):
        train_conditional_step(model, population, optimizer=adam(model), reverse_time=None,
                               run_seed=900, record_id=b"invalid-clock", sample_count=1)
