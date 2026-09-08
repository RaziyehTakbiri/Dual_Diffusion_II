"""Connect the amended BASE population, conditional risk and physical sampler.

These explicit local entrypoints never load datasets, launch jobs, select
scientific hyperparameters, or qualify an installed/GPU runtime. All choices
and supplied synthetic sources are caller-owned. Finite numerical path laws
are identified separately from ideal continuous-time laws.
"""
from dataclasses import dataclass
from copy import deepcopy
import hashlib
import json
import math

import torch

from heterodiff.experiments.factorized_conditional_training import (
    FactorizedConditionalModel, FactorizedObservation, FactorizedPhysicalPotential,
    FactorizedTrainingBatch,
)
from heterodiff.processes.factorized_hybrid_sampler import (
    ExactFactorizedReference, FactorizedSchedule, LearnedFactorizedSampler, conditional_initializer,
    _Streams,
)


class FactorizedPipelineError(RuntimeError):
    pass


def _need(condition, message):
    if not condition:
        raise FactorizedPipelineError(message)


@dataclass(frozen=True)
class FactorizedPopulationContext:
    domain_id: str
    task_id: str
    context_bytes: bytes
    base_context: tuple[float, ...]

    def __post_init__(self):
        FactorizedObservation((), self.domain_id, self.task_id, self.context_bytes)
        _need(type(self.base_context) is tuple and len(self.base_context) == 64 and
              all(type(x) is float and math.isfinite(x) for x in self.base_context),
              "explicit finite 64D BASE context required")

    def binding(self):
        return json.dumps([self.domain_id, self.task_id, self.context_bytes.hex(),
                           [x.hex() for x in self.base_context]], separators=(",", ":")).encode()


def _parameter_digest(model):
    digest = hashlib.sha256()
    for name, value in model.named_parameters():
        digest.update(name.encode()+b"\0")
        digest.update(value.detach().cpu().numpy().tobytes(order="C"))
    return digest.hexdigest()


def _reference_identity(reference):
    from heterodiff.theory.factorized_association_guide_torch import FactorizedAssociationGuide
    return FactorizedAssociationGuide(reference.oracle).identity_sha256


def _clock_binding(model, reference):
    _need(getattr(model.remaining_clocks, '__func__', None) is FactorizedSchedule.remaining_clocks
          and getattr(model.remaining_clocks, '__self__', None) == reference.schedule,
          'pipeline requires the exact reference-owned physical schedule callback')


class FactorizedBasePopulation:
    """Frozen learned BASE with two independently keyed whole-path branches.

    Only Pi_N initialization is allowed here. The product example retains the
    first path's interior state and replaces only its observation with one from
    the second terminal path. Replay reproducibility is not an IID proof.
    """
    def __init__(self, base, reference, reverse_grid, context):
        _need(type(reference) is ExactFactorizedReference and
              type(context) is FactorizedPopulationContext, "exact reference/context required")
        _need(reference.reference.domain_id == context.domain_id, "population domain mismatch")
        _need(base.architecture.total_cap == reference.parameters.reference_cap and
              base.architecture.horizon == reference.schedule.horizon, "BASE carrier/schedule mismatch")
        self.reference, self.context = deepcopy(reference), context
        self.physical = FactorizedPhysicalPotential(base, base_context=context.base_context,
                                                   clean_hold=reference.schedule.clean_hold)
        self.sampler = LearnedFactorizedSampler(self.reference, self.physical, reverse_grid)
        content = {'base_sha256': _parameter_digest(self.physical.base),
                   'architecture_sha256': base.architecture.architecture_sha256,
                   'grid': [float(u).hex() for u in reverse_grid],
                   'schedule': reference.schedule.__dict__,
                   'parameters': reference.parameters.__dict__,
                   'context': context.binding().hex(),
                   'reference_identity': self._reference_identity(),
                   'scope': 'QUERY_REFINED_NUMERICAL_BASE_PATH_AND_AMENDED_OBSERVATION',
                   'time_family': 'EXPLICIT_FIXED_U_OR_UNIFORM_STRICT_FULL_INTERVAL'}
        self.law_id = 'local-factorized-'+hashlib.sha256(json.dumps(content, sort_keys=True,
                                                                  separators=(',', ':')).encode()).hexdigest()

    def _reference_identity(self):
        return _reference_identity(self.reference)

    def sample_pair(self, *, reverse_time, run_seed, record_id):
        _need(type(reverse_time) is float and math.isfinite(reverse_time) and
              0 < reverse_time < self.reference.schedule.horizon, "pair time must be strictly interior")
        _need(type(record_id) is bytes and bool(record_id), "explicit pair record id required")
        record = hashlib.sha256(self.context.binding()+self.law_id.encode()+record_id).digest()
        grid = tuple(sorted(set(self.sampler.grid+(reverse_time,))))
        sampler = LearnedFactorizedSampler(self.reference, self.physical, grid)
        kernel_id = self.law_id+'-fixed-'+hashlib.sha256(reverse_time.hex().encode()).hexdigest()
        paths, observations = [], []
        for branch in (b"base-joint-one", b"base-product-two"):
            path = sampler.sample_path(run_seed=run_seed, record_id=record, branch_id=branch)
            path.diagnostics['query_refined_grid'] = grid != self.sampler.grid
            path.diagnostics['base_grid'] = self.sampler.grid
            path.diagnostics['same_unrefined_numerical_path_law_claimed'] = False
            rng = _Streams(run_seed, record, branch).rng("terminal-observation")
            visible = self.reference.oracle.sample_observation(path.terminal_state, rng)
            observations.append(FactorizedObservation(visible, self.context.domain_id,
                                                      self.context.task_id, self.context.context_bytes))
            paths.append(path)
        state = paths[0].at_time(reverse_time)
        joint = FactorizedTrainingBatch((state,), (reverse_time,), (observations[0],), kernel_id)
        product = FactorizedTrainingBatch((state,), (reverse_time,), (observations[1],), kernel_id)
        return joint, product, tuple(paths)


def train_conditional_step(model, population, *, optimizer, reverse_time, run_seed,
                           record_id, sample_count):
    """One paired update using complete independent paths and explicit time law.

    reverse_time=None selects uniform q on the entire open reverse interval;
    each continuous draw is inserted into the numerical grid before generating
    both paths. An explicit fixed time is a separate diagnostic objective.
    Refinement changes the numerical path law and its computational work.
    """
    _need(type(model) is FactorizedConditionalModel and type(population) is FactorizedBasePopulation,
          "exact model and learned BASE population required")
    _need(type(sample_count) is int and 0 < sample_count <= model.conditioner.architecture.limits.maximum_batch_size,
          "sample count exceeds declared learner batch limit")
    _need(type(record_id) is bytes and bool(record_id), "explicit conditional-step record id required")
    _need(reverse_time is None or (type(reverse_time) is float and math.isfinite(reverse_time)
          and 0 < reverse_time < population.reference.schedule.horizon), 'invalid time policy')
    _need(model.guide.identity_sha256 == population._reference_identity(),
          "conditional guide/reference law mismatch")
    _need(model.horizon == population.reference.schedule.horizon and
          model.clean_hold == population.reference.schedule.clean_hold,
          "conditional schedule/hold mismatch")
    _clock_binding(model, population.reference)
    supplied = [p for group in optimizer.param_groups for p in group['params']]
    expected = list(model.parameters())
    _need(len(supplied) == len(expected) and {id(p) for p in supplied} == {id(p) for p in expected},
          "optimizer must own exactly this conditional learner")
    joints, products, paths = [], [], []
    time_stream = _Streams(run_seed, population.context.binding()+record_id, b'conditional-time-policy')
    for i in range(sample_count):
        u = reverse_time
        if u is None:
            u = float(time_stream.rng('full-interval-time', i).random())*population.reference.schedule.horizon
            _need(0 < u < population.reference.schedule.horizon, 'time RNG endpoint: no redraw')
        j, p, pair = population.sample_pair(reverse_time=u, run_seed=run_seed,
                                          record_id=record_id+i.to_bytes(8, "big"))
        joints.append(j); products.append(p); paths.extend(pair)
    law_id = (population.law_id+'-uniform-full-reverse-interval' if reverse_time is None
              else joints[0].law_id)
    joint = FactorizedTrainingBatch(tuple(x.states[0] for x in joints),
              tuple(x.reverse_times[0] for x in joints), tuple(x.observations[0] for x in joints), law_id)
    product = FactorizedTrainingBatch(joint.states, joint.reverse_times,
              tuple(x.observations[0] for x in products), law_id)
    before = [p.detach().clone() for p in expected]
    optimizer.zero_grad(set_to_none=True)
    loss = model.paired_loss(joint, product)
    loss.backward()
    _need(all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in expected),
          "nonfinite conditional gradient: optimizer not run")
    optimizer.step()
    _need(all(bool(torch.isfinite(p).all()) for p in expected), "nonfinite conditional parameters")
    changed = sum(int(torch.count_nonzero(p.detach()-a)) for p, a in zip(expected, before))
    return {'decision': 'LOCAL_CONDITIONAL_OPTIMIZER_STEP_COMPLETE', 'loss': float(loss.detach()),
            'changed_parameter_elements': changed, 'paired_examples': sample_count,
            'base_paths_generated': 2*sample_count, 'law_id': law_id,
            'reverse_times': joint.reverse_times,
            'time_policy': 'UNIFORM_FULL_REVERSE_INTERVAL' if reverse_time is None else 'FIXED_TIME_DIAGNOSTIC',
            'query_refined_paths': sum(p.diagnostics['query_refined_grid'] for p in paths),
            'actual_macrosteps': sum(len(p.reverse_grid)-1 for p in paths),
            'accepted_births': sum(p.diagnostics['accepted_birth'] for p in paths),
            'accepted_deaths': sum(p.diagnostics['accepted_death'] for p in paths),
            'production_or_scientific_convergence_claimed': False}


def sample_conditional(base, model, reference, reverse_grid, context, observed, *, run_seed, record_id):
    """Fixed-model conditional path with cap-correct analytic initialization."""
    _need(type(model) is FactorizedConditionalModel and type(context) is FactorizedPopulationContext,
          "exact conditional model/context required")
    _need(type(reference) is ExactFactorizedReference, "exact conditional reference required")
    _need(context.domain_id == reference.reference.domain_id and
          model.guide.identity_sha256 == _reference_identity(reference), "conditional reference mismatch")
    _need(model.horizon == reference.schedule.horizon and model.clean_hold == reference.schedule.clean_hold,
          "conditional clock endpoints mismatch")
    _clock_binding(model, reference)
    observation = FactorizedObservation(observed, context.domain_id, context.task_id, context.context_bytes)
    physical = FactorizedPhysicalPotential(base, base_context=context.base_context,
        conditional_model=model, observation=observation, clean_hold=reference.schedule.clean_hold)
    initializer = conditional_initializer(physical.model.guide, physical, observed, reference.schedule,
        model.method_id, maximum_trials=reference.limits.maximum_initialization_trials)
    sampler = LearnedFactorizedSampler(reference, physical, reverse_grid, initializer=initializer)
    return sampler.sample_path(run_seed=run_seed, record_id=record_id, branch_id=b"conditional")
