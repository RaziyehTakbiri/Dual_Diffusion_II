"""Tiny invented inputs only; no admitted data or scientific training."""
from dataclasses import replace
from fractions import Fraction
import math

import pytest
import torch

from heterodiff.data.two_domain_factorized_state import (
    FactoredEvent, PhysioStateKey, FactorizedMetadataReference,
)
from heterodiff.evaluation.two_domain_count_normalized_event_cks import PHYSIONET_DOMAIN_ID
from heterodiff.theory.factorized_smooth_amendment import FactorizedSmoothOracle, AmendmentParameters
from heterodiff.theory.factorized_association_guide_torch import FactorizedAssociationGuide
from heterodiff.models.factorized_configuration_energy_torch import (
    BoundedFactorizedConfigurationEnergy, FactorizedEnergyArchitecture, FactorizedEnergyLimits,
)
from heterodiff.experiments.factorized_conditional_training import (
    FactorizedObservation, FactorizedObservationEncoder, FactorizedTrainingBatch,
    FactorizedConditionalModel, FactorizedPhysicalPotential, FactorizedTrainingError,
    factorized_configuration_batch, factorized_joint_product_loss,
    PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID, SamplingLawWeights,
)


@pytest.fixture
def bundle():
    reference = FactorizedMetadataReference(PHYSIONET_DOMAIN_ID)
    params = AmendmentParameters(1.0, 4, 4, 1.0, .125, .25, .125, .5)
    guide = FactorizedAssociationGuide(FactorizedSmoothOracle(reference, params))
    architecture = FactorizedEnergyArchitecture('factorized-key-v1', 4, 2.0, 1.0, 1.0, 1.0,
                                               FactorizedEnergyLimits(8, 64, 1024, 32768))
    base = BoundedFactorizedConfigurationEnergy(architecture, initialization_seed=11)
    conditioner = BoundedFactorizedConfigurationEnergy(architecture, initialization_seed=12)
    continuous = FactoredEvent(PhysioStateKey(1, 'HR', 'POSITIVE'), .25)
    atomic = FactoredEvent(PhysioStateKey(1, 'GCS', 'ATOMIC', Fraction(3)))
    state = (continuous, atomic)
    observed = FactorizedObservation((continuous, atomic), PHYSIONET_DOMAIN_ID, 'tiny-task', b'context-a')
    return guide, base, conditioner, state, observed


def clocks(u):
    return max(0.0, 1.75-u), max(0.0, 1.75-u)


def model_for(bundle, method):
    guide, _, conditioner, _, _ = bundle
    return FactorizedConditionalModel(conditioner, guide=guide, method_id=method,
                                      clean_hold=.25, remaining_clocks=clocks,
                                      observation_seed=13, nuisance_seed=14)


def paired(bundle):
    _, _, _, state, observed = bundle
    empty = replace(observed, observed=())
    overflow = replace(observed, observed=None)
    return (FactorizedTrainingBatch((state, ()), (.25, .5), (observed, overflow), 'tiny-law'),
            FactorizedTrainingBatch((state, ()), (.25, .5), (empty, observed), 'tiny-law'))


@pytest.mark.parametrize('method', [PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID])
def test_real_analytic_paired_risk_and_one_adamw_update(bundle, method):
    model = model_for(bundle, method)
    joint, product = paired(bundle)
    before = tuple(p.detach().clone() for p in model.parameters())
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001)
    loss = model.paired_loss(joint, product)
    assert loss.dtype == torch.float64 and torch.isfinite(loss)
    loss.backward()
    for module in (model.conditioner, model.encoder, model.nuisance):
        gradients = [p.grad for p in module.parameters() if p.grad is not None]
        assert gradients and all(torch.isfinite(g).all() for g in gradients)
        assert any(bool((g != 0).any()) for g in gradients)
    optimizer.step()
    assert any(not torch.equal(a, b) for a,b in zip(before, model.parameters()))
    assert all(p.device.type == 'cpu' and p.dtype == torch.float32 for p in model.parameters())


def test_exact_parameter_counts_independent_encoders_and_workload(bundle):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    report = model.parameter_summary()
    assert report['conditioner'] == 96705
    assert report['observation_encoder'] == 51200
    assert report['independent_nuisance'] == 53313
    assert report['unique_trainable_model_parameters'] == 201218
    assert {p.data_ptr() for p in model.encoder.parameters()}.isdisjoint(
        p.data_ptr() for p in model.nuisance.encoder.parameters())
    joint, _ = paired(bundle)
    work = model.workload(joint)
    assert work['analytic_guide_calls'] == 2
    assert work['observation_encoder_batched_forward_calls'] == 2
    assert work['nuisance_head_affine_macs'] == 4160
    assert not work['production_budget_adopted']


def test_encoder_empty_overflow_context_and_permutation(bundle):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    row = bundle[-1]
    changed_context = replace(row, context_bytes=b'context-b')
    empty, overflow = replace(row, observed=()), replace(row, observed=None)
    enc = model.encoder((row, replace(row, observed=tuple(reversed(row.observed))),
                         changed_context, empty, overflow))
    assert torch.equal(enc[0], enc[1])
    assert not torch.equal(enc[0], enc[2])
    assert not torch.equal(enc[3], enc[4])
    duplicate = model.encoder((replace(row, observed=(row.observed[0],)),
                               replace(row, observed=(row.observed[0],)*2)))
    assert not torch.equal(duplicate[0], duplicate[1])


def test_encoder_consumes_every_key_and_context_byte(bundle, monkeypatch):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    row = bundle[-1]
    seen = []
    original = model.encoder.bytes.forward
    def capture(raw):
        seen.append(raw)
        return original(raw)
    monkeypatch.setattr(model.encoder.bytes, 'forward', capture)
    model.encoder((row,))
    assert seen == [e.key.canonical_bytes() for e in sorted(row.observed, key=lambda e:e.sort_key)]+[row.canonical_context_bytes]
    assert sum(map(len,seen)) == model.encoder.workload((row,))['metadata_bytes']


@pytest.mark.parametrize('method', [PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID])
def test_gate_is_single_cubic_and_exactly_zero_on_clean_hold(bundle, method):
    model = model_for(bundle, method)
    state, row = bundle[-2:]
    times = (0.0, .5, 1.75, 2.0)
    states, observations = (state,)*4, (row,)*4
    batch = factorized_configuration_batch(states, times, model.encoder(observations), model.conditioner.architecture)
    raw = model.conditioner(batch).double()
    expected_gate = torch.tensor([1.0, (1.25/1.75)**3, 0.0, 0.0], dtype=torch.float64)
    actual = model.residual(states, times, observations)
    assert torch.equal(actual, raw*expected_gate)
    assert actual[2:].tolist() == [0.0, 0.0]


@pytest.mark.parametrize('method', [PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID])
def test_physical_gradient_bound_nuisance_exclusion_snapshot_and_initializer(bundle, method):
    model = model_for(bundle, method)
    guide, base, _, state, row = bundle
    context = (0.0,)*64
    physical = FactorizedPhysicalPotential(base, base_context=context, conditional_model=model, observation=row)
    value, gradients = physical.value_grad(.25, state)
    assert physical.value(.25,state) == value
    assert len(gradients[0]) == 1 and gradients[1] == ()
    assert math.isfinite(gradients[0][0]) and value <= physical.upper_value_bound
    assert physical.initialization_residual_upper_bound == 1.0
    residual = float(model.residual((state,), (0.0,), (row,))[0].detach())
    assert physical.initialization_residual_log_tilt(state) == residual
    assert physical.initialization_log_tilt(0.0,state) == pytest.approx(
        residual+float(model.baseline((state,), (0.0,), (row,))[0]), abs=1e-12)
    with torch.no_grad():
        for p in model.nuisance.parameters(): p.add_(100)
    after_nuisance = FactorizedPhysicalPotential(base, base_context=context, conditional_model=model, observation=row)
    assert after_nuisance.value_grad(.25,state) == (value,gradients)
    with torch.no_grad():
        for p in base.parameters(): p.add_(.1)
        for p in model.conditioner.parameters(): p.add_(.1)
    assert physical.value_grad(.25,state) == (value,gradients)
    assert all(not p.requires_grad for p in physical.base.parameters())
    assert all(not p.requires_grad for p in physical.model.parameters())


def test_base_hold_extension_constant_and_second_coordinate_derivatives(bundle):
    _, base, _, state, _ = bundle
    physical = FactorizedPhysicalPotential(base, base_context=(0.0,)*64, clean_hold=.25)
    assert physical.value_grad(1.75,state) == physical.value_grad(2.0,state)
    assert physical.initialization_log_tilt(0.0,state) == 0.0
    assert physical.initialization_residual_log_tilt(state) == 0.0
    batch = factorized_configuration_batch((state,), (.25,), torch.zeros(1,64), base.architecture,
                                            coordinate_gradients=True)
    first = torch.autograd.grad(base(batch).sum(), batch.coordinates[0], create_graph=True)[0]
    second = torch.autograd.grad(first.sum(), batch.coordinates[0])[0]
    assert second.shape == (1,) and torch.isfinite(second).all()


@pytest.mark.parametrize('field,value', [('states', ((),())), ('reverse_times', (.75,.5)),
                                         ('law_id', 'wrong-law')])
def test_paired_population_and_law_mismatch_refused(bundle, field, value):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    joint, product = paired(bundle)
    with pytest.raises(FactorizedTrainingError):
        model.paired_loss(joint, replace(product, **{field:value}))


def test_exact_context_mismatch_and_negative_rn_refused(bundle):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    joint, product = paired(bundle)
    wrong = replace(product.observations[0], context_bytes=b'wrong')
    with pytest.raises(FactorizedTrainingError,match='context'):
        model.paired_loss(joint, replace(product,observations=(wrong,product.observations[1])))
    bad = SamplingLawWeights('target','tiny-law',(Fraction(-1),Fraction(1)),(Fraction(1),)*2,False)
    with pytest.raises(FactorizedTrainingError,match='nonnegative'):
        factorized_joint_product_loss(model,joint,product,bad)


def test_risk_is_fp64_and_rn_factors_are_not_self_normalized(bundle):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    joint, product = paired(bundle)
    unit = model.paired_loss(joint, product)
    weights = SamplingLawWeights('target','tiny-law',(Fraction(2),)*2,(Fraction(2),)*2,False)
    assert torch.equal(model.paired_loss(joint,product,weights),2*unit)
    assert model.logits(joint).dtype == torch.float64


@pytest.mark.parametrize('value', [Fraction(1,10**400),Fraction(10**400)])
def test_rn_representability_failure_refused(bundle, value):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    joint, product = paired(bundle)
    weights = SamplingLawWeights('target','tiny-law',(value,)*2,(Fraction(1),)*2,False)
    with pytest.raises(FactorizedTrainingError,match='RN weight'):
        model.paired_loss(joint,product,weights)


def test_finite_fp64_guide_not_narrowed_to_fp32(bundle, monkeypatch):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    joint, _ = paired(bundle)
    monkeypatch.setattr(model.guide, 'log_value', lambda *args,**kwargs:torch.tensor(1e100,dtype=torch.float64))
    logits = model.logits(joint)
    assert torch.isfinite(logits).all() and logits.dtype == torch.float64
    assert logits.tolist() == [1e100,1e100]


def test_visible_and_latent_fp32_overflow_refused(bundle):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    _,base,_,state,row = bundle
    bad = (FactoredEvent(state[0].key,1e100),)
    with pytest.raises(FactorizedTrainingError,match='FP32'):
        model.encoder((replace(row,observed=bad),))
    with pytest.raises(FactorizedTrainingError,match='FP32'):
        factorized_configuration_batch((bad,),(.25,),torch.zeros(1,64),base.architecture)


def test_context_resource_refusal_no_truncation(bundle):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    with pytest.raises(FactorizedTrainingError,match='byte limit'):
        model.encoder((replace(bundle[-1],context_bytes=b'a'*1024),))


def test_explicit_seed_and_cpu_initialization_preserve_global_rng(bundle):
    state = torch.random.get_rng_state().clone()
    first = model_for(bundle, PRIMARY_METHOD_ID)
    second = model_for(bundle, PRIMARY_METHOD_ID)
    assert torch.equal(state,torch.random.get_rng_state())
    assert all(torch.equal(a,b) for a,b in zip(first.parameters(),second.parameters()))
    encoder = FactorizedObservationEncoder(limits=first.encoder.limits,observation_cap=4,
                                           coordinate_scale=1.0,initialization_seed=2**64-1)
    assert sum(p.numel() for p in encoder.parameters()) == 51200


def test_bad_guide_or_hold_or_context_refused(bundle):
    guide,base,conditioner,_,row = bundle
    with pytest.raises(FactorizedTrainingError,match='analytic'):
        FactorizedConditionalModel(conditioner,guide=object(),method_id=PRIMARY_METHOD_ID,
            clean_hold=.25,remaining_clocks=clocks,observation_seed=1,nuisance_seed=2)
    with pytest.raises(FactorizedTrainingError,match='clean hold'):
        FactorizedPhysicalPotential(base,base_context=(0.0,)*64)
    with pytest.raises(FactorizedTrainingError,match='unused observation'):
        FactorizedPhysicalPotential(base,base_context=(0.0,)*64,observation=row,clean_hold=.25)


def test_nonzero_clock_on_hold_refused(bundle):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    model.remaining_clocks = lambda u:(.1,.1)
    with pytest.raises(FactorizedTrainingError,match='clean hold'):
        model.baseline((bundle[-2],),(2.0,),(bundle[-1],))


def test_large_roster_rejected_before_graph_and_wrong_physical_hold_refused(bundle):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    _,base,_,state,row = bundle
    with pytest.raises(FactorizedTrainingError,match='cap'):
        model.residual((state*3,),(.25,),(row,))
    with pytest.raises(FactorizedTrainingError,match='differs'):
        FactorizedPhysicalPotential(base,base_context=(0.0,)*64,conditional_model=model,
                                    observation=row,clean_hold=.5)
    physical = FactorizedPhysicalPotential(base,base_context=(0.0,)*64,clean_hold=.25)
    for u in (-1.0,3.0,float('nan')):
        with pytest.raises(FactorizedTrainingError,match='time'):
            physical.value(u,state)


def test_extra_analytic_coordinate_row_is_not_silently_ignored(bundle):
    model = model_for(bundle, PRIMARY_METHOD_ID)
    with pytest.raises(FactorizedTrainingError,match='align exactly'):
        model.baseline(((),),(.25,),(replace(bundle[-1],observed=()),),
                       coordinates=(torch.empty(0,dtype=torch.float64),))
