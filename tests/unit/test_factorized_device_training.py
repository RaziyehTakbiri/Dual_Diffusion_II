"""CPU execution of explicit-device routes; no CUDA qualification implied."""
from fractions import Fraction
from copy import deepcopy

import numpy as np
import pytest
import torch

from heterodiff.data.two_domain_factorized_state import (
    FactoredEvent, PhysioStateKey, RetailStateKey, FactorizedMetadataReference,
    TrainInformedMetadataReference,
)
from heterodiff.models.factorized_configuration_energy_torch import (
    FactorizedEnergyArchitecture,FactorizedEnergyLimits,BoundedFactorizedConfigurationEnergy,
)
from heterodiff.models.factorized_device_energy_torch import DeviceFactorizedEnergy
from heterodiff.theory.factorized_smooth_amendment import AmendmentParameters,FactorizedSmoothOracle
from heterodiff.theory.factorized_association_guide_torch import FactorizedAssociationGuide
from heterodiff.processes.factorized_hybrid_sampler import FactorizedSchedule,ExactFactorizedReference
from heterodiff.experiments.two_domain_baseline_registry import PRIMARY_METHOD_ID,PRIMARY_COMPARATOR_ID
from heterodiff.experiments.factorized_conditional_training import (
    FactorizedConditionalModel,FactorizedTrainingBatch,FactorizedObservation,FactorizedPhysicalPotential,
)
from heterodiff.experiments.factorized_conditional_pipeline import FactorizedPopulationContext
from heterodiff.experiments.factorized_base_training import base_objective_on_corrupted_states,train_base_step
from heterodiff.experiments.factorized_device_training import (
    DeviceFactorizedConditionalModel,DeviceFactorizedPhysicalPotential,DeviceFactorizedTrainingError,
    device_base_objective_on_corrupted_states,device_train_base_step,DeviceFactorizedBasePopulation,
    device_train_conditional_step,device_sample_conditional,
)


def fixture(domain,method=PRIMARY_METHOD_ID):
    if domain=='R3-PHYS':
        source=(FactoredEvent(PhysioStateKey(3,'MechVent','ATOMIC',Fraction(1))),
                FactoredEvent(PhysioStateKey(3,'HR','POSITIVE'),.2))
    else:
        def key(branch):
            return RetailStateKey('C123456','sku','name',-1,(2010,1,2,3,4,5,6),'UK',branch)
        source=(FactoredEvent(key('ZERO')),FactoredEvent(key('NEGATIVE'),.2))
    q=TrainInformedMetadataReference(FactorizedMetadataReference(domain),source,beta=Fraction(1,4))
    oracle=FactorizedSmoothOracle(q,AmendmentParameters(.5,4,4,.2,.1,.25,.25,1.))
    schedule=FactorizedSchedule(1.,.25,.5,1.)
    reference=ExactFactorizedReference(oracle,schedule)
    arch=FactorizedEnergyArchitecture('DEVICE_TEST_'+domain,4,1.,.25,1.,1.,
        FactorizedEnergyLimits(4,16,2048,16384))
    base=BoundedFactorizedConfigurationEnergy(arch,initialization_seed=41)
    energy=BoundedFactorizedConfigurationEnergy(arch,initialization_seed=42)
    cond=FactorizedConditionalModel(energy,guide=FactorizedAssociationGuide(oracle),method_id=method,
        clean_hold=.25,remaining_clocks=schedule.remaining_clocks,observation_seed=43,nuisance_seed=44)
    context=FactorizedPopulationContext(domain,'TEST',b'static',(0.,)*64)
    return source,reference,base,cond,context


def adam(model):
    return torch.optim.AdamW(model.parameters(),lr=.001,betas=(.9,.999),eps=1e-8,weight_decay=0.,
        foreach=False,fused=False,amsgrad=False,maximize=False,capturable=False,differentiable=False)


def compare_gradients(cpu,device):
    a,b=dict(cpu.named_parameters()),dict(device.named_parameters())
    assert a.keys()==b.keys()
    for key in a:
        assert (a[key].grad is None)==(b[key].grad is None)
        if a[key].grad is not None:
            torch.testing.assert_close(a[key].grad,b[key].grad,atol=1e-7,rtol=1e-6)


@pytest.mark.parametrize('domain',['R3-PHYS','R4-RETAIL'])
def test_base_value_hessian_loss_and_parameter_gradients_match_cpu(domain):
    source,_,base,_,_=fixture(domain)
    device=DeviceFactorizedEnergy.from_cpu(base,'cpu')
    kwargs=dict(states=(source,),destinations=((source[0],),),forward_times=(.5,),
                context=torch.zeros(64),continuous_rates=(1.,),jump_rates=(.3,),jump_weight=1.)
    a=base_objective_on_corrupted_states(base,**kwargs)
    b=device_base_objective_on_corrupted_states(device,**kwargs)
    for key in ('total','continuous','jump'):
        torch.testing.assert_close(getattr(a,key),getattr(b,key),atol=1e-8,rtol=1e-7)
        assert getattr(b,key).device.type=='cpu' and getattr(b,key).dtype==torch.float64
    a.total.backward();b.total.backward()
    compare_gradients(base,device)


@pytest.mark.parametrize('domain',['R3-PHYS','R4-RETAIL'])
@pytest.mark.parametrize('method',[PRIMARY_METHOD_ID,PRIMARY_COMPARATOR_ID])
def test_conditional_loss_gradients_nuisance_and_physical_parity(domain,method):
    source,_,base,cpu,context=fixture(domain,method)
    device=DeviceFactorizedConditionalModel.from_cpu(cpu,'cpu')
    dbase=DeviceFactorizedEnergy.from_cpu(base,'cpu')
    observation=FactorizedObservation((source[-1],),domain,'TEST',b'static')
    overflow=FactorizedObservation(None,domain,'TEST',b'static')
    joint=FactorizedTrainingBatch((source,source),(.5,.875),(observation,overflow),'FIXED_TEST_LAW')
    product=FactorizedTrainingBatch(joint.states,joint.reverse_times,(overflow,observation),'FIXED_TEST_LAW')
    a,b=cpu.paired_loss(joint,product),device.paired_loss(joint,product)
    torch.testing.assert_close(a,b,atol=1e-8,rtol=1e-7)
    a.backward();b.backward();compare_gradients(cpu,device)
    cp=FactorizedPhysicalPotential(base,base_context=context.base_context,conditional_model=cpu,observation=observation)
    dp=DeviceFactorizedPhysicalPotential(dbase,base_context=context.base_context,conditional_model=device,observation=observation)
    for u in (0.,.5,.75,.875,1.):
        av,ag=cp.value_grad(u,source);bv,bg=dp.value_grad(u,source)
        assert bv==pytest.approx(av,rel=1e-6,abs=1e-7)
        for left,right in zip(ag,bg):
            assert right==pytest.approx(left,rel=1e-6,abs=1e-7)
        assert cp.initialization_log_tilt(u,source)==pytest.approx(dp.initialization_log_tilt(u,source),abs=1e-7)
    assert dp.value(.75,source)==dp.value(.875,source)==dp.value(1.,source)
    with torch.no_grad():
        device.nuisance.output.bias.add_(5.)
    changed=DeviceFactorizedPhysicalPotential(dbase,base_context=context.base_context,conditional_model=device,observation=observation)
    assert changed.value_grad(.5,source)==dp.value_grad(.5,source)
    assert changed.initialization_residual_log_tilt(source)==dp.initialization_residual_log_tilt(source)


@pytest.mark.parametrize('domain',['R3-PHYS','R4-RETAIL'])
def test_actual_base_update_matches_cpu_from_shared_random_inputs(domain):
    source,reference,base,_,_=fixture(domain)
    device=DeviceFactorizedEnergy.from_cpu(base,'cpu')
    before=torch.random.get_rng_state().clone()
    a=train_base_step(base,reference,(source,),context=torch.zeros(64),rng=np.random.default_rng(7),
        optimizer=adam(base),sample_count=2,jump_weight=1.)
    b=device_train_base_step(device,reference,(source,),context=torch.zeros(64),rng=np.random.default_rng(7),
        optimizer=adam(device),sample_count=2,jump_weight=1.)
    assert b['loss']==pytest.approx(a['loss'],rel=1e-6,abs=1e-7)
    assert b['changed_parameter_elements']>0
    for key,value in base.state_dict().items():
        torch.testing.assert_close(value,device.state_dict()[key],atol=1e-7,rtol=1e-6)
    assert torch.equal(torch.random.get_rng_state(),before)


@pytest.mark.parametrize('domain',['R3-PHYS','R4-RETAIL'])
@pytest.mark.parametrize('method',[PRIMARY_METHOD_ID,PRIMARY_COMPARATOR_ID])
def test_device_population_conditional_update_and_sampler_run_on_cpu(domain,method):
    source,reference,base,cpu,context=fixture(domain,method)
    dbase=DeviceFactorizedEnergy.from_cpu(base,'cpu')
    device=DeviceFactorizedConditionalModel.from_cpu(cpu,'cpu')
    grid=(0.,.25,.5,.75,1.)
    population=DeviceFactorizedBasePopulation(dbase,reference,grid,context)
    report=device_train_conditional_step(device,population,optimizer=adam(device),reverse_time=None,
                                        run_seed=501,record_id=b'step',sample_count=1)
    assert report['changed_parameter_elements']>0 and report['base_paths_generated']==2
    assert report['time_policy']=='UNIFORM_FULL_REVERSE_INTERVAL' and report['device']=='cpu'
    path=device_sample_conditional(dbase,device,reference,grid,context,(source[-1],),run_seed=502,record_id=b'draw')
    assert path.terminal_state is path.states[-2]
    assert all(len(state)<=4 for state in path.states)
    for event in path.terminal_state:
        assert event.to_metric_event().domain_id==domain


def test_selected_device_objective_keeps_cpu64_accumulation_under_meta_default():
    source,_,base,_,_=fixture('R3-PHYS')
    device=DeviceFactorizedEnergy.from_cpu(base,'cpu')
    context=torch.zeros(64,device='cpu')
    with torch.device('meta'):
        objective=device_base_objective_on_corrupted_states(device,(source,),((source[0],),),(.5,),
            context,(1.,),(.2,),jump_weight=1.)
        assert objective.total.device.type=='cpu'
        objective.total.backward()
    assert all(p.grad is None or p.grad.device.type=='cpu' for p in device.parameters())


def test_sampler_snapshot_not_changed_by_later_optimizer_or_parameter_changes():
    source,_,base,cpu,context=fixture('R3-PHYS')
    device=DeviceFactorizedConditionalModel.from_cpu(cpu,'cpu')
    dbase=DeviceFactorizedEnergy.from_cpu(base,'cpu')
    observation=FactorizedObservation((source[-1],),'R3-PHYS','TEST',b'static')
    physical=DeviceFactorizedPhysicalPotential(dbase,base_context=context.base_context,conditional_model=device,observation=observation)
    before=physical.value_grad(.5,source)
    with torch.no_grad():
        device.conditioner.readout_output.bias.add_(1.)
        dbase.readout_output.bias.add_(1.)
    assert physical.value_grad(.5,source)==before


def test_invalid_device_training_inputs_do_not_change_parameters():
    source,reference,base,_,_=fixture('R3-PHYS')
    device=DeviceFactorizedEnergy.from_cpu(base,'cpu')
    before=deepcopy(device.state_dict())
    with pytest.raises(DeviceFactorizedTrainingError,match='batch limit'):
        device_train_base_step(device,reference,(source,),context=torch.zeros(64),rng=np.random.default_rng(7),
                               optimizer=adam(device),sample_count=100,jump_weight=1.)
    assert all(torch.equal(v,device.state_dict()[k]) for k,v in before.items())


def test_conditional_copy_preserves_parent_and_mixed_submodule_modes():
    _,_,_,cpu,_=fixture('R3-PHYS')
    cpu.eval()
    cpu.nuisance.train()
    device=DeviceFactorizedConditionalModel.from_cpu(cpu,'cpu')
    assert not device.training and not device.conditioner.training
    assert not device.encoder.training and device.nuisance.training


@pytest.mark.parametrize('field,value',[('clean_hold',.125),('horizon',2.)])
def test_schedule_mismatch_rejected_before_optimizer_or_sampling(field,value):
    source,reference,base,cpu,context=fixture('R3-PHYS')
    device=DeviceFactorizedConditionalModel.from_cpu(cpu,'cpu')
    dbase=DeviceFactorizedEnergy.from_cpu(base,'cpu')
    grid=(0.,.25,.5,.75,1.)
    population=DeviceFactorizedBasePopulation(dbase,reference,grid,context)
    if field=='clean_hold':
        device.clean_hold=value
    else:
        from dataclasses import replace
        device.conditioner.architecture=replace(device.conditioner.architecture,horizon=value)
    before=deepcopy(device.state_dict())
    with pytest.raises(DeviceFactorizedTrainingError,match='horizon/hold'):
        device_train_conditional_step(device,population,optimizer=adam(device),reverse_time=.5,
            run_seed=1,record_id=b'bad',sample_count=1)
    with pytest.raises(DeviceFactorizedTrainingError,match='horizon/hold'):
        device_sample_conditional(dbase,device,reference,grid,context,(source[-1],),
            run_seed=1,record_id=b'bad')
    assert all(torch.equal(v,device.state_dict()[k]) for k,v in before.items())
