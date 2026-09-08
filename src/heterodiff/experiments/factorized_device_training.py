"""Explicit-device successor for the amended learner, not a scientific release.

Neural parameters/activations/derivatives/AdamW moments are FP32 on the selected
CPU or CUDA device. Exact keys, the analytic guide, RNG/path orchestration and
F105 remain CPU. Loss accumulation and physical outputs remain CPU FP64 using
differentiable device transfers. This hybrid boundary is intentional, measured,
and not a claim of a fully GPU-resident or faster end-to-end sampler.
"""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import hashlib
import json
import math

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from heterodiff.models.factorized_device_energy_torch import (
    DeviceFactorizedEnergy, DeviceFactorizedObservationEncoder,
    DeviceFactorizedObservationNuisance, device_configuration_batch,
)
from heterodiff.experiments.factorized_conditional_training import (
    FactorizedConditionalModel, FactorizedObservation, FactorizedTrainingBatch,
)
from heterodiff.experiments.factorized_base_training import BaseObjective
from heterodiff.models.two_domain_conditional_training_loss import SamplingLawWeights
from heterodiff.experiments.factorized_conditional_pipeline import (
    FactorizedBasePopulation, FactorizedPopulationContext, _parameter_digest, _reference_identity,
)
from heterodiff.processes.factorized_hybrid_sampler import (
    ExactFactorizedReference, FactorizedSchedule, LearnedFactorizedSampler, _Streams,
    conditional_initializer,
)


class DeviceFactorizedTrainingError(ValueError):
    pass


def _need(ok, message):
    if not ok:
        raise DeviceFactorizedTrainingError(message)


def _cpu64(value):
    return value.to(device='cpu', dtype=torch.float64)


def _finite(value, message):
    _need(isinstance(value, torch.Tensor) and bool(torch.isfinite(value).all()), message)


class DeviceFactorizedConditionalModel(nn.Module):
    @classmethod
    def from_cpu(cls, cpu_model, device):
        _need(type(cpu_model) is FactorizedConditionalModel, 'exact CPU conditional prototype required')
        self = cls()
        self.conditioner = DeviceFactorizedEnergy.from_cpu(cpu_model.conditioner, device)
        self.encoder = DeviceFactorizedObservationEncoder.from_cpu(cpu_model.encoder, device)
        self.nuisance = DeviceFactorizedObservationNuisance.from_cpu(cpu_model.nuisance, device)
        self.guide = deepcopy(cpu_model.guide)
        self.method_id, self.clean_hold = cpu_model.method_id, cpu_model.clean_hold
        self.remaining_clocks = deepcopy(cpu_model.remaining_clocks)
        self.device = self.conditioner.device
        # Preserve parent mode without overwriting individually copied submodule modes.
        self.training = cpu_model.training
        return self

    @property
    def horizon(self):
        return self.conditioner.architecture.horizon

    def _rows(self, states, reverse_times, observations):
        # This shared validation only inspects exact CPU metadata, not tensors.
        FactorizedConditionalModel._rows(self, states, reverse_times, observations)

    def baseline(self, states, reverse_times, observations, *, coordinates=None):
        # Unchanged analytic matching graph, including differentiable CPU64 rows.
        return FactorizedConditionalModel.baseline(self, states, reverse_times, observations,
                                                   coordinates=coordinates)

    def residual(self, states, reverse_times, observations, *, coordinates=None):
        self._rows(states, reverse_times, observations)
        context = self.encoder(observations)
        batch = device_configuration_batch(states, reverse_times, context, self.conditioner.architecture,
                                           device=self.device, coordinates=coordinates)
        direct = torch.tensor([self.horizon-u for u in reverse_times], dtype=torch.float64, device='cpu')
        gate = ((direct-self.clean_hold).clamp(min=0)/(self.horizon-self.clean_hold)).pow(3)
        return _cpu64(self.conditioner(batch))*gate

    def forward(self, batch):
        _need(type(batch) is FactorizedTrainingBatch, 'exact conditional batch required')
        _need(type(batch.law_id) is str and bool(batch.law_id) and batch.law_id.isascii(), 'explicit law identity required')
        result = (self.baseline(batch.states, batch.reverse_times, batch.observations)
                  + self.residual(batch.states, batch.reverse_times, batch.observations)
                  + _cpu64(self.nuisance(batch.observations)))
        _finite(result, 'nonfinite device conditional logits')
        return result

    def logits(self, batch):
        return self(batch)

    def paired_loss(self, joint, product, weights=None):
        _need(type(joint) is FactorizedTrainingBatch and type(product) is FactorizedTrainingBatch,
              'exact joint/product batches required')
        if weights is None:
            weights = SamplingLawWeights.declared(law_id=joint.law_id, size=len(joint.states))
        _need(joint.states == product.states and joint.reverse_times == product.reverse_times,
              'joint/product must share first state and time')
        _need(tuple(r.context_identity for r in joint.observations) ==
              tuple(r.context_identity for r in product.observations), 'joint/product context mismatch')
        _need(type(weights) is SamplingLawWeights and type(weights.uses_declared_law) is bool,
              'exact sampling weights required')
        _need(joint.law_id == product.law_id == weights.proposal_law_id, 'sampling law mismatch')
        n = len(joint.states)
        converted = []
        for row in (weights.joint, weights.product):
            _need(type(row) is tuple and len(row) == n and
                  all(type(x) is Fraction and x >= 0 for x in row), 'aligned rational weights required')
            try:
                values = torch.tensor([float(x) for x in row], device='cpu', dtype=torch.float64)
            except OverflowError as error:
                raise DeviceFactorizedTrainingError('weight overflow') from error
            _finite(values, 'nonfinite weights')
            _need(all(x == 0 or y > 0 for x,y in zip(row, values.tolist())), 'positive weight underflow')
            converted.append(values)
        if weights.uses_declared_law:
            _need(weights.target_law_id == weights.proposal_law_id and
                  all(x == 1 for x in weights.joint+weights.product), 'declared law needs unit weights')
        else:
            _need(weights.target_law_id != weights.proposal_law_id, 'distinct proposal law required')
        j,p = self(joint), self(product)
        _need(j.shape == p.shape and j.numel() > 0, 'balanced nonempty class sizes required')
        value = .5*((converted[0]*F.softplus(-j)).mean()+(converted[1]*F.softplus(p)).mean())
        _finite(value, 'nonfinite paired loss')
        return value


def device_base_objective_on_corrupted_states(model, states, destinations, forward_times,
                                             context, continuous_rates, jump_rates, *, jump_weight):
    _need(type(model) is DeviceFactorizedEnergy, 'exact device BASE energy required')
    _need(type(jump_weight) is float and math.isfinite(jump_weight) and jump_weight > 0, 'positive jump weight required')
    _need(type(states) is tuple and type(destinations) is tuple and type(forward_times) is tuple
          and len(states) == len(destinations) == len(forward_times) and bool(states), 'aligned source/proposal batches required')
    _need(type(context) is torch.Tensor and tuple(context.shape) == (64,) and context.dtype == torch.float32,
          'explicit FP32 64D context required')
    _finite(context, 'nonfinite context')
    _need(type(continuous_rates) is tuple and type(jump_rates) is tuple and
          len(continuous_rates) == len(jump_rates) == len(states) and
          all(type(r) is float and math.isfinite(r) and r >= 0 for r in continuous_rates+jump_rates),
          'aligned finite nonnegative rates required')
    _need(all(type(s) is float and math.isfinite(s) and 0 <= s <= model.architecture.horizon
              for s in forward_times), 'forward time out of range')
    reverse = tuple(model.architecture.horizon-s for s in forward_times)
    contexts = context.detach().clone().to(model.device).expand(len(states), 64)
    source = device_configuration_batch(states, reverse, contexts, model.architecture,
                                         device=model.device, coordinate_gradients=True)
    dest = device_configuration_batch(destinations, reverse, contexts, model.architecture, device=model.device)
    # Preserve direct physical-time conversion, avoiding a roundtrip through S-u.
    time = torch.tensor(forward_times, dtype=torch.float32, device=model.device)
    source, dest = replace(source, forward_time=time), replace(dest, forward_time=time)
    values, dest_values = model(source), model(dest)
    total = values.sum()
    terms = [_cpu64(v)*0 for v in values]
    for dimension, coordinate, owner in zip(source.coordinate_dimensions, source.coordinates, source.owners):
        if not dimension:
            continue
        gradient = torch.autograd.grad(total, coordinate, create_graph=True, retain_graph=True, allow_unused=True)[0]
        if gradient is None:
            continue
        second = (torch.autograd.grad(gradient.sum(), coordinate, create_graph=True,
                  retain_graph=True, allow_unused=True)[0] if gradient.requires_grad else None)
        g = _cpu64(gradient)
        h = g.sum()*0 if second is None else _cpu64(second).sum()
        terms[owner] = terms[owner]+.5*g.square().sum()+h-(_cpu64(coordinate.detach())*g).sum()
    continuous = (torch.stack(terms)*torch.tensor(continuous_rates, dtype=torch.float64, device='cpu')).mean()
    delta = _cpu64(dest_values)-_cpu64(values)
    jump = (torch.tensor(jump_rates, dtype=torch.float64, device='cpu')*(torch.exp(delta)+delta)).mean()
    objective = continuous+jump_weight*jump
    _finite(objective, 'nonfinite device BASE objective')
    return BaseObjective(objective, continuous, jump, source)


def _optimizer_parameters(model, optimizer):
    _need(type(optimizer) is torch.optim.AdamW and len(optimizer.param_groups) == 1, 'one AdamW group required')
    group = optimizer.param_groups[0]
    parameters = tuple(p for p in model.parameters() if p.requires_grad)
    supplied = tuple(group['params'])
    _need(parameters and len(parameters) == len(supplied) and
          {id(p) for p in parameters} == {id(p) for p in supplied}, 'optimizer ownership mismatch')
    _need(group['betas'] == (.9,.999) and group['eps'] == 1e-8 and group['weight_decay'] == 0. and
          all(group.get(k, False) is False for k in ('foreach','fused','amsgrad','maximize','capturable','differentiable')),
          'explicit nonfused AdamW settings required')
    _need(type(group['lr']) is float and math.isfinite(group['lr']) and group['lr'] > 0, 'positive learning rate required')
    return parameters


def _update(model, optimizer, loss):
    parameters = _optimizer_parameters(model, optimizer)
    before = [p.detach().clone() for p in parameters]
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    for p in parameters:
        if p.grad is not None:
            _finite(p.grad, 'nonfinite gradient: update not executed')
            _need(p.grad.device == model.device and p.grad.dtype == torch.float32, 'gradient placement mismatch')
    optimizer.step()
    changed = 0
    for p, old in zip(parameters, before):
        _finite(p, 'nonfinite parameter after update; no rollback-to-success')
        _need(p.device == model.device and p.dtype == torch.float32, 'parameter placement mismatch')
        changed += int(torch.count_nonzero(p.detach()-old).cpu())
        for key in ('exp_avg','exp_avg_sq'):
            moment = optimizer.state.get(p, {}).get(key)
            if moment is not None:
                _finite(moment, 'nonfinite optimizer moment')
                _need(moment.device == model.device and moment.dtype == torch.float32, 'moment placement mismatch')
    return changed


def device_train_base_step(model, reference, train_sources, *, context, rng, optimizer,
                           sample_count, jump_weight):
    _need(type(model) is DeviceFactorizedEnergy and type(reference) is ExactFactorizedReference,
          'exact device model/reference required')
    _need(type(rng) is np.random.Generator, 'explicit CPU reference RNG required')
    _need(type(sample_count) is int and 0 < sample_count <= min(64,model.architecture.limits.maximum_batch_size),
          'declared BASE batch limit exceeded')
    _need(type(train_sources) is tuple and bool(train_sources), 'explicit TRAIN source tuple required')
    _need(model.architecture.total_cap == reference.parameters.reference_cap and
          model.architecture.horizon == reference.schedule.horizon, 'BASE reference mismatch')
    _optimizer_parameters(model, optimizer)
    states,destinations,times,crates,jrates,kinds = [],[],[],[],[],[]
    for _ in range(sample_count):
        u = float(rng.random())
        _need(0 < u < 1, 'time RNG endpoint: no redraw')
        s = reference.schedule.clean_hold+(reference.schedule.horizon-reference.schedule.clean_hold)*u
        encoded = float(torch.tensor(s, dtype=torch.float32, device='cpu'))
        _need(reference.schedule.clean_hold < encoded < reference.schedule.horizon, 'FP32 active time endpoint')
        initial = reference.oracle.sample_training_target(train_sources,rng)
        state = reference.sample_forward(initial,s,rng)
        proposal = reference.proposal(state,rng)
        dest,rate,kind = (state,0.,'NO_EXIT') if proposal is None else proposal
        states.append(state); destinations.append(dest); times.append(s); kinds.append(kind)
        cr,jr = reference.schedule.continuous_rate,reference.schedule.jump_rate
        crates.append(float(cr)); jrates.append(float(jr*rate))
    objective = device_base_objective_on_corrupted_states(model,tuple(states),tuple(destinations),
        tuple(times),context,tuple(crates),tuple(jrates),jump_weight=jump_weight)
    changed = _update(model,optimizer,objective.total)
    return {'loss':float(objective.total.detach()), 'continuous_loss':float(objective.continuous.detach()),
            'jump_loss':float(objective.jump.detach()), 'changed_parameter_elements':changed,
            'forward_times':tuple(times), 'proposal_kinds':tuple(kinds), 'device':str(model.device),
            'reference_rng_and_corruption_device':'cpu', 'scientific_training_completed':False}


class DeviceFactorizedPhysicalPotential:
    """CPU physical interface backed by a frozen selected-device neural graph."""
    def __init__(self, base, *, base_context, conditional_model=None, observation=None, clean_hold=None):
        _need(type(base) is DeviceFactorizedEnergy, 'exact device BASE required')
        _need(type(base_context) is tuple and len(base_context) == 64 and
              all(type(x) is float and math.isfinite(x) for x in base_context), '64D explicit BASE context required')
        self.base = deepcopy(base).eval().requires_grad_(False)
        self.device = base.device
        self.base_context = torch.tensor([base_context], dtype=torch.float32, device=self.device)
        self.model, self.observation = None,observation
        if conditional_model is not None:
            _need(type(conditional_model) is DeviceFactorizedConditionalModel and type(observation) is FactorizedObservation,
                  'device conditional model and exact observation required')
            _need(conditional_model.device == base.device and
                  conditional_model.conditioner.architecture == base.architecture, 'BASE/conditional architecture or device mismatch')
            self.model = deepcopy(conditional_model).eval().requires_grad_(False)
            _need(clean_hold is None or clean_hold == self.model.clean_hold, 'clean hold mismatch')
            clean_hold = self.model.clean_hold
            self.model._rows(((),),(0.,),(observation,))
        else:
            _need(observation is None, 'BASE-only observation not used')
        _need(type(clean_hold) is float and math.isfinite(clean_hold) and
              0 <= clean_hold < base.architecture.horizon, 'explicit valid clean hold required')
        self.clean_hold = clean_hold
        extra = (0. if self.model is None else self.model.guide.upper_log_bound(observation.observed)
                 +self.model.conditioner.architecture.value_bound)
        self.initialization_upper_log_bound = extra
        self.initialization_residual_upper_bound = 0. if self.model is None else self.model.conditioner.architecture.value_bound
        self.upper_value_bound = base.architecture.value_bound+extra

    def _coordinates(self,state,gradient):
        return tuple(torch.tensor([] if not e.key.dimension else [e.coordinate],dtype=torch.float64,
                                  device='cpu',requires_grad=gradient) for e in state)

    def _base_batch(self,u,state,coordinates):
        _need(type(u) is float and math.isfinite(u) and 0 <= u <= self.base.architecture.horizon, 'physical time out of range')
        clamped = min(u,self.base.architecture.horizon-self.clean_hold)
        return device_configuration_batch((state,),(clamped,),self.base_context,self.base.architecture,
                                           device=self.device,coordinates=coordinates)

    def _tilt(self,u,state,coordinates):
        if self.model is None:
            return torch.tensor(0.,dtype=torch.float64,device='cpu')
        return (self.model.baseline((state,),(u,),(self.observation,),coordinates=coordinates)
                +self.model.residual((state,),(u,),(self.observation,),coordinates=coordinates))[0]

    def initialization_log_tilt(self,u,state):
        coordinates = self._coordinates(state,False)
        self._base_batch(u,state,coordinates)
        with torch.no_grad():
            value = self._tilt(u,state,coordinates)
        _finite(value,'nonfinite initial tilt')
        return float(value)

    def initialization_residual_log_tilt(self,state):
        coordinates = self._coordinates(state,False)
        self._base_batch(0.,state,coordinates)
        if self.model is None:
            return 0.
        with torch.no_grad():
            value = self.model.residual((state,),(0.,),(self.observation,),coordinates=coordinates)[0]
        _finite(value,'nonfinite initial residual')
        return float(value)

    def _value(self,u,state,coordinates):
        return _cpu64(self.base(self._base_batch(u,state,coordinates)))[0]+self._tilt(u,state,coordinates)

    def value(self,u,state):
        with torch.no_grad():
            value = self._value(u,state,self._coordinates(state,False))
        _finite(value,'nonfinite physical value')
        return float(value)

    def value_grad(self,u,state):
        coordinates = self._coordinates(state,True)
        with torch.enable_grad():
            value = self._value(u,state,coordinates)
            gradients = (torch.autograd.grad(value,coordinates,allow_unused=True)
                         if coordinates and value.requires_grad else (None,)*len(coordinates))
        _finite(value,'nonfinite physical value')
        rows=[]
        for x,g in zip(coordinates,gradients):
            g = torch.zeros_like(x) if g is None else g
            _finite(g,'nonfinite physical gradient')
            rows.append(tuple(float(v) for v in g))
        return float(value.detach()),tuple(rows)


class DeviceFactorizedBasePopulation(FactorizedBasePopulation):
    """Reuse CPU path/RNG semantics with selected-device physical evaluations."""
    def __init__(self, base, reference, reverse_grid, context):
        _need(type(base) is DeviceFactorizedEnergy and type(reference) is ExactFactorizedReference
              and type(context) is FactorizedPopulationContext, 'exact device population inputs required')
        _need(reference.reference.domain_id == context.domain_id and
              base.architecture.total_cap == reference.parameters.reference_cap and
              base.architecture.horizon == reference.schedule.horizon, 'population carrier mismatch')
        self.reference,self.context = deepcopy(reference),context
        self.physical = DeviceFactorizedPhysicalPotential(base,base_context=context.base_context,
                                                         clean_hold=reference.schedule.clean_hold)
        self.sampler = LearnedFactorizedSampler(self.reference,self.physical,reverse_grid)
        record = {'scope':'DEVICE_NEURAL_CPU_ORCHESTRATED_QUERY_REFINED_POPULATION',
                  'base':_parameter_digest(self.physical.base), 'architecture':base.architecture.architecture_sha256,
                  'device':str(base.device),'torch_version':torch.__version__,'cuda_build':torch.version.cuda,
                  'reference':_reference_identity(reference),'context':context.binding().hex(),
                  'grid':reverse_grid,'schedule':reference.schedule.__dict__}
        self.law_id = 'device-factorized-'+hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()


def device_train_conditional_step(model,population,*,optimizer,reverse_time,run_seed,record_id,sample_count):
    _need(type(model) is DeviceFactorizedConditionalModel and type(population) is DeviceFactorizedBasePopulation,
          'exact device conditional model/population required')
    _need(type(sample_count) is int and 0 < sample_count <= model.conditioner.architecture.limits.maximum_batch_size,
          'conditional sample count limit')
    _need(type(record_id) is bytes and bool(record_id),'explicit record id required')
    _need(model.guide.identity_sha256 == population._reference_identity() and
          model.device == population.physical.device, 'conditional reference/device mismatch')
    _need(model.horizon == population.reference.schedule.horizon and
          model.clean_hold == population.reference.schedule.clean_hold, 'conditional horizon/hold mismatch')
    _need(getattr(model.remaining_clocks,'__func__',None) is FactorizedSchedule.remaining_clocks and
          getattr(model.remaining_clocks,'__self__',None) == population.reference.schedule,
          'exact reference-owned schedule required')
    _optimizer_parameters(model,optimizer)
    stream = _Streams(run_seed,population.context.binding()+record_id,b'device-conditional-time')
    joints,products,paths=[],[],[]
    for i in range(sample_count):
        u = reverse_time if reverse_time is not None else float(stream.rng('time',i).random())*model.horizon
        j,p,pair = population.sample_pair(reverse_time=u,run_seed=run_seed,record_id=record_id+i.to_bytes(8,'big'))
        joints.append(j);products.append(p);paths.extend(pair)
    law = population.law_id+'-uniform-full' if reverse_time is None else joints[0].law_id
    joint = FactorizedTrainingBatch(tuple(x.states[0] for x in joints),tuple(x.reverse_times[0] for x in joints),
                                   tuple(x.observations[0] for x in joints),law)
    product = FactorizedTrainingBatch(joint.states,joint.reverse_times,tuple(x.observations[0] for x in products),law)
    loss = model.paired_loss(joint,product)
    changed = _update(model,optimizer,loss)
    return {'loss':float(loss.detach()),'changed_parameter_elements':changed,'device':str(model.device),
            'reverse_times':joint.reverse_times,'base_paths_generated':len(paths),
            'actual_macrosteps':sum(len(p.reverse_grid)-1 for p in paths),
            'time_policy':'UNIFORM_FULL_REVERSE_INTERVAL' if reverse_time is None else 'FIXED_TIME_DIAGNOSTIC',
            'law_id':law,'scientific_training_completed':False}


def device_sample_conditional(base,model,reference,reverse_grid,context,observed,*,run_seed,record_id):
    _need(type(reference) is ExactFactorizedReference and type(context) is FactorizedPopulationContext,
          'exact reference/context required')
    _need(type(model) is DeviceFactorizedConditionalModel and
          model.guide.identity_sha256 == _reference_identity(reference), 'conditional reference mismatch')
    _need(model.horizon == reference.schedule.horizon and model.clean_hold == reference.schedule.clean_hold,
          'conditional horizon/hold mismatch')
    _need(getattr(model.remaining_clocks,'__func__',None) is FactorizedSchedule.remaining_clocks and
          getattr(model.remaining_clocks,'__self__',None) == reference.schedule, 'conditional schedule mismatch')
    observation=FactorizedObservation(observed,context.domain_id,context.task_id,context.context_bytes)
    physical=DeviceFactorizedPhysicalPotential(base,base_context=context.base_context,conditional_model=model,
                                               observation=observation,clean_hold=reference.schedule.clean_hold)
    draw=conditional_initializer(physical.model.guide,physical,observed,reference.schedule,model.method_id,
                                 maximum_trials=reference.limits.maximum_initialization_trials)
    return LearnedFactorizedSampler(reference,physical,reverse_grid,initializer=draw).sample_path(
        run_seed=run_seed,record_id=record_id,branch_id=b'device-conditional')
