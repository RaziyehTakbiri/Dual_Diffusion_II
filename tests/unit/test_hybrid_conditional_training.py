"""Actual continuous/jump paths, trainable visible encoders and F105; synthetic only."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
import math

import numpy as np
import pytest
import torch

from heterodiff.events.observations import ObservationView, ObservedAnchor
from heterodiff.experiments import hybrid_conditional_training as h
from heterodiff.experiments import two_domain_gpu_training as trainer
from heterodiff.experiments import two_domain_f105_checkpoint_validation as f105
from heterodiff.models.configuration_energy_torch import (
    BoundedConfigurationEnergy, ConfigurationEnergyArchitecture, SpectralNormCeilings,
)
from heterodiff.models.configuration_energy_training_torch import ConfigurationEnergyTrainingView
from heterodiff.models.two_domain_observation_training_design import (
    VisibleObservationSchema, tensorize_observations, ObservationConditionEncoderV1,
    ObservationOnlyNuisanceV1, SyntheticTrainingLawV1, training_design_parameter_counts,
)
from heterodiff.processes.learned_hybrid_training_sampler import (
    LearnedHybridTrainingSampler, HybridTrajectoryPlan, ReferenceConfigurationInitializer,
    HybridSamplingContext,
)
from heterodiff.processes.reversible_hybrid_reference import (
    PiecewiseConstantHybridSchedule, ReversibleHybridRates, ReversibleHybridReference,
)
from heterodiff.theory.configuration_reference import CappedPoissonConfigurationReference, TransformedEvent

DOMAINS=('physionet-challenge-2012','online-retail-ii')
METHODS=tuple(h.BASELINE_KIND_BY_METHOD)
VALIDATION_IDS=tuple(f'hybrid-validation-{i:03d}'.encode() for i in range(128))


def process():
    reference=CappedPoissonConfigurationReference({0:1},{0:1.0},activity=0.015,total_cap=1)
    schedule=PiecewiseConstantHybridSchedule((0.0,0.0625,0.25),(0.0,0.4),(0.0,0.2),clean_hold=0.0625)
    return ReversibleHybridReference(reference,schedule,ReversibleHybridRates(reference,per_particle_death_rate=0.3))


def energy(p,seed=65):
    arch=ConfigurationEnergyArchitecture.from_process(p,coordinate_scales_by_type={0:(1.0,)},
        context_dimension=64,context_scales=(1.0,)*64,context_schema_sha256='c'*64,
        event_hidden_width=4,event_embedding_width=4,context_hidden_width=4,
        context_embedding_width=4,readout_hidden_width=4,value_bound=0.1,
        spectral_ceilings=SpectralNormCeilings(*(100.0,)*7),bias_ceiling=100.0,
        first_derivative_ceiling=1e6,second_derivative_ceiling=1e6)
    return ConfigurationEnergyTrainingView.from_cpu_reference(
        BoundedConfigurationEnergy(arch,generator=torch.Generator().manual_seed(seed)))


def schema(domain):
    return VisibleObservationSchema(domain,(0,),(('angle',(1.0,)),),('sensor',),('static',),(1.0,))


def visible(s,angles,contexts=None):
    if contexts is None: contexts=((0.25,),)*len(angles)
    views=tuple(ObservationView((ObservedAnchor(marks={'angle':(a,)}),),cardinality=None) for a in angles)
    return tensorize_observations(views,('sensor',)*len(angles),contexts,s)


def model(p,domain,method):
    s=schema(domain)
    return h.ObservedConditionalTrainingModel(energy(p,79),
        ObservationConditionEncoderV1(s,initialization_seed=15),
        ObservationOnlyNuisanceV1(s,initialization_seed=29),method_id=method)


def test_encoder_parameter_count_and_real_loss_gradients():
    p=process(); current=model(p,DOMAINS[0],METHODS[0]); s=schema(DOMAINS[0])
    states=((TransformedEvent(0,(0.2,)),),())
    joint=h.ObservedTrainingBatch(states,(0.1,0.15),visible(s,[0.3,1.1]),
        torch.tensor([0.1,-0.2]),h.BASELINE_KIND_BY_METHOD[METHODS[0]])
    product=replace(joint,observation=visible(s,[1.9,2.2]))
    weights=h.SamplingLawWeights.declared(law_id='DECLARED_SYNTHETIC',size=2)
    loss=h.observed_joint_product_loss(current,joint,product,weights)
    expected=0.5*(torch.nn.functional.softplus(-current(joint)).mean()+
                  torch.nn.functional.softplus(current(product)).mean())
    assert torch.equal(loss,expected)
    loss.backward()
    for prefix in ('conditioner.backbone','encoder','nuisance.encoder','nuisance.hidden'):
        values=[v for name,v in current.named_parameters() if name.startswith(prefix)]
        assert any(v.grad is not None and bool((v.grad != 0).any()) for v in values),prefix
    counts=training_design_parameter_counts(s)
    assert current.encoder.parameter_count==counts['condition_encoder']
    assert current.nuisance.parameter_count==counts['nuisance_encoder']+counts['nuisance_head']
    assert current.parameter_summary()['all_unique_parameters']==sum(v.numel() for v in current.parameters())
    for raw in (joint.observation,product.observation):
        assert not raw.anchor_features.requires_grad


def test_raw_context_hash_and_process_state_cross_binding_rejected():
    p=process(); current=model(p,DOMAINS[0],METHODS[0]); s=schema(DOMAINS[0])
    j=h.ObservedTrainingBatch(((),),(0.1,),visible(s,[0.3],((1e100,),)),
        torch.zeros(1),h.BASELINE_KIND_BY_METHOD[METHODS[0]])
    other=visible(s,[0.3],((1e101,),))
    assert torch.equal(j.observation.static_context_features,other.static_context_features)
    weights=h.SamplingLawWeights.declared(law_id='DECLARED_SYNTHETIC',size=1)
    with pytest.raises(h.HybridTrainingError,match='identities differ'):
        h.observed_joint_product_loss(current,j,replace(j,observation=other),weights)
    with pytest.raises(h.HybridTrainingError,match='latent and time'):
        h.observed_joint_product_loss(current,j,replace(j,reverse_times=(0.2,)),weights)


@pytest.mark.parametrize('method',METHODS)
def test_total_neural_potential_gradient_nuisance_exclusion_and_initial_tilt(method):
    p=process(); base=energy(p); current=model(p,DOMAINS[0],method)
    obs=visible(schema(DOMAINS[0]),[0.7]); sensor=h.SyntheticAngularCountSensor(p)
    options=dict(conditional=current,observation=obs,baseline=sensor.baseline(0.7,propagated=method==METHODS[0]),
                 baseline_upper_bound=math.log(1.5))
    potential=h.TorchHybridPotential(base,torch.zeros(1,64),**options)
    state=(TransformedEvent(0,(0.25,)),)
    value,gradient=potential.value_grad(0.1,state)
    assert value==potential.value(0.1,state)
    delta=0.002
    numerical=(potential.value(0.1,(TransformedEvent(0,(0.25+delta,)),))-
               potential.value(0.1,(TransformedEvent(0,(0.25-delta,)),)))/(2*delta)
    assert math.isclose(gradient[0][0],numerical,rel_tol=0.03,abs_tol=3e-5)
    assert potential.value_grad(0.1,())[1]==()
    altered=deepcopy(current)
    with torch.no_grad():
        for parameter in altered.nuisance.parameters(): parameter.add_(0.5)
    same=h.TorchHybridPotential(base,torch.zeros(1,64),**dict(options,conditional=altered))
    assert same.value_grad(0.1,state)==potential.value_grad(0.1,state)
    init=h.TorchHybridPotential(base,torch.zeros(1,64),include_base=False,**options)
    base_only=h.TorchHybridPotential(base,torch.zeros(1,64))
    assert math.isclose(potential.value(0.0,state)-init.value(0.0,state),base_only.value(0.0,state),abs_tol=2e-7)
    with pytest.raises(h.HybridTrainingError,match='log h_hat only'):
        h.ConditionalRejectionInitializer(potential)
    initializer=h.ConditionalRejectionInitializer(init)
    assert initializer(p,np.random.default_rng(6))==initializer(p,np.random.default_rng(6))
    init.upper_value_bound = 100.0
    with pytest.raises(h.HybridTrainingError,match='below supported floor'):
        initializer(p,np.random.default_rng(6))
    assert all(parameter.grad is None for parameter in base.parameters())
    assert all(parameter.grad is None for parameter in current.parameters())


def test_angular_sensor_normalization_reference_propagation_and_clean_hold():
    p=process(); sensor=h.SyntheticAngularCountSensor(p)
    with pytest.raises(FrozenInstanceError): sensor.alpha=0.25
    with pytest.raises(ValueError): sensor.q[0,0]=0.0
    with pytest.raises(ValueError): sensor.f.setflags(write=True)
    states=((),(TransformedEvent(0,(0.2,)),))
    assert np.allclose(sensor.q.sum(1),0)
    angles=(np.arange(2048)+0.5)*(2*math.pi/2048)
    for state in states:
        mass=np.mean([math.exp(sensor.log_value(0.1,state,float(a),propagated=False)) for a in angles])
        assert math.isclose(mass,1.0,abs_tol=1e-13)
        assert sensor.log_value(0.2,state,0.7,propagated=True)==sensor.log_value(0.2,state,0.7,propagated=False)
    area=p.schedule.jump_integral(0.0,0.25-0.1)
    beta=p.rates.birth_rate; delta=p.rates.per_particle_death_rate
    # Analytic two-count CTMC E[(-1)^N] from the empty count state.
    expected=1-2*beta/(beta+delta)*(1-math.exp(-(beta+delta)*area))
    actual=(math.exp(sensor.log_value(0.1,(),0.0,propagated=True))-1)/sensor.alpha
    assert math.isclose(actual,expected,abs_tol=1e-14)


@pytest.mark.parametrize('domain',DOMAINS)
def test_synthetic_chart_preserves_occurrences_and_refuses_invalid_latents(domain):
    state=(TransformedEvent(0,(-0.3,)),TransformedEvent(0,(0.7,)))
    result=h.synthetic_positive_scalar_f105_configuration(domain,state)
    assert len(result.events)==2
    assert len(result.events[0].coordinates)==(112 if domain==DOMAINS[0] else 10)
    with pytest.raises(h.HybridTrainingError):
        h.synthetic_positive_scalar_f105_configuration(domain,(TransformedEvent(0,(0.0,0.0)),))
    with pytest.raises(h.HybridTrainingError):
        h.synthetic_positive_scalar_f105_configuration(domain,(TransformedEvent(0,(1000.0,)),))
    with pytest.raises(h.HybridTrainingError):
        h.synthetic_positive_scalar_f105_configuration(domain,(TransformedEvent(0,(-1000.0,)),))


def _run_hybrid_pipeline(domain,method):
    p=process(); base=energy(p); base.requires_grad_(False)
    current=model(p,domain,method); s=schema(domain)
    initial={name:v.detach().clone() for name,v in current.state_dict().items()}
    sensor=h.SyntheticAngularCountSensor(p)
    base_potential=h.TorchHybridPotential(base,torch.zeros(1,64))
    law=SyntheticTrainingLawV1(s,((0.25,),),Fraction(1,4),time_grid_bits=2)
    records=tuple(f'hybrid-training-{i:03d}'.encode() for i in range(16))
    diagnostics=dict(base_trajectory_count=0,conditional_trajectory_count=0,conditional_record_ids=[],
                     actual_macrosteps=0,initialization_excludes_base=True,law=law.description(),weights=[],
                     synthetic_chart_only=True,real_domain_sampler_admitted=False)
    def loss_adapter(live,fields,generator):
        draws=law.draw(16,generator=generator)
        pairs=[]
        for index,draw in zip(fields['index'].tolist(),draws):
            u=float(draw.reverse_time)
            plan=HybridTrajectoryPlan((0.0,0.1875,0.25)).refined_for_query(u)
            sampler=LearnedHybridTrainingSampler(p,base_potential,plan,ReferenceConfigurationInitializer())
            pairs.append(sampler.sample_pair(context=HybridSamplingContext(domain,b'sensor',b'static-025'),
                reverse_time=u,run_seed=811,record_id=records[index],observation_law=sensor.sample))
            diagnostics['base_trajectory_count']+=2
            diagnostics['actual_macrosteps']+=2*(len(plan.reverse_grid)-1)
        states=tuple(pair.branch_one.latent_at_u for pair in pairs)
        times=tuple(pair.reverse_time for pair in pairs)
        def batch(branch):
            angles=[getattr(pair,branch).observation for pair in pairs]
            values=[sensor.log_value(u,state,a,propagated=method==METHODS[0])
                    for state,u,a in zip(states,times,angles)]
            return h.ObservedTrainingBatch(states,times,visible(s,angles),torch.tensor(values,dtype=torch.float32),
                                            h.BASELINE_KIND_BY_METHOD[method])
        weights=law.equal_prior_weights(16)
        diagnostics['weights'].append(weights.description())
        return h.observed_joint_product_loss(live,batch('branch_one'),batch('branch_two'),weights)
    def validation(live,step,identity):
        groups=[]
        for group_index,group_id in enumerate(VALIDATION_IDS):
            # Fixed invented observed sensor and truth, different per group.
            angle=float(0.1+5.9*group_index/128)
            options=dict(conditional=live,observation=visible(s,[angle]),
                         baseline=sensor.baseline(angle,propagated=method==METHODS[0]),
                         baseline_upper_bound=math.log(1.5))
            potential=h.TorchHybridPotential(base,torch.zeros(1,64),**options)
            initializer=h.ConditionalRejectionInitializer(h.TorchHybridPotential(
                base,torch.zeros(1,64),include_base=False,**options))
            sampler=LearnedHybridTrainingSampler(p,potential,HybridTrajectoryPlan((0.0,0.1875,0.25)),initializer)
            samples=[]
            for draw in range(64):
                record_id=group_id+b':draw:'+str(draw).encode()
                path=sampler.sample_path(run_seed=991,record_id=record_id,branch_id=b'conditional-validation')
                samples.append(h.synthetic_positive_scalar_f105_configuration(domain,path.terminal_state))
                diagnostics['conditional_trajectory_count']+=1
                diagnostics['conditional_record_ids'].append(record_id)
                diagnostics['actual_macrosteps']+=len(path.reverse_times)-1
                assert path.diagnostics['initializer_is_reference_pi_n'] is False
            truth=() if group_index else (TransformedEvent(0,(0.15,)),)
            groups.append(f105.GroupConditionalConfigurations(group_id,tuple(samples),
                h.synthetic_positive_scalar_f105_configuration(domain,truth)))
        return f105.evaluate_checkpoint_validation(identity,step,live,VALIDATION_IDS,tuple(groups))
    result=trainer.run_training_qualification(current,
        trainer.TensorTrainingRoster(domain,records,{'index':torch.arange(16,dtype=torch.int64)}),
        trainer.RunIdentity(method,domain,0,811),device='cpu',loss_adapter=loss_adapter,
        validation_group_ids=VALIDATION_IDS,validation_adapter=validation,
        schedule=trainer.NonconfirmatorySchedule(1,1),
        configuration_id='LOCAL_CONTINUOUS_HYBRID_ANGULAR_SENSOR_POSITIVE_CHART_NOT_REAL_DOMAINS')
    assert all(torch.equal(v,current.state_dict()[name]) for name,v in initial.items())
    return result,diagnostics,initial


@pytest.mark.parametrize('domain,method',[(d,m) for d in DOMAINS for m in METHODS])
def test_actual_hybrid_training_and_complete_f105_checkpoint_pipeline(domain,method):
    result,diagnostics,initial=_run_hybrid_pipeline(domain,method)
    assert result.completed_updates==1 and math.isfinite(result.losses[0])
    checkpoint=result.checkpoints[0]
    for prefix in ('conditioner.backbone','encoder','nuisance.encoder','nuisance.hidden'):
        assert any(not torch.equal(initial[name],v) for name,v in checkpoint.model_state.items()
                   if name.startswith(prefix)),prefix
    assert diagnostics['base_trajectory_count']==32
    assert diagnostics['conditional_trajectory_count']==8192
    assert len(set(diagnostics['conditional_record_ids']))==8192
    assert diagnostics['actual_macrosteps']>=32*3+8192*2
    assert diagnostics['initialization_excludes_base']
    assert not diagnostics['real_domain_sampler_admitted']
    evidence=checkpoint.f105_validation
    assert evidence.validate_binding(result.identity,1,checkpoint.model_state,VALIDATION_IDS)
    assert len(evidence.group_records)==128
    assert not evidence.summary()['conditional_draw_generation_authenticated']
    assert all(item.factory_score.draw_count==64 for item in evidence.group_records)
    loaded=trainer.inspect_checkpoint_bytes(trainer.checkpoint_to_bytes(checkpoint))
    assert len(loaded['f105_validation_audit_projection']['group_records'])==128
