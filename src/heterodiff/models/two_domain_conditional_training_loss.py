"""Differentiable conditional joint/product risk, an additive training draft.

Implements manuscript v3 Section 7.1 and its matched direct comparator:
  G+R: log h_tilde + a_R * bounded_energy + nuisance(a,m,z)
  DIR: log g       + a_R * bounded_energy + nuisance(a,m,z)
and the equal-prior logistic risk. The supplied energy is already saturated;
a second tanh is never applied. The physical log-potential excludes nuisance.

This module neither samples trajectories nor authenticates their law. It does
not choose the still-unfrozen observation encoder, nuisance architecture, or
task/context/time law. Caller-supplied baseline values are fixed evaluations,
not a propagated-guide implementation or its coordinate derivatives. The
observation-only interface rejects live autograd/alias paths from latent/time
inputs, but cannot authenticate feature meaning or arbitrary module globals.
Old certified CPU64 models and B06 parameter counts remain unchanged.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
import re
import struct
from typing import Callable

import torch
from torch import nn
from torch.nn import functional as functional

from heterodiff.experiments import two_domain_baseline_registry as b06
from .configuration_energy_training_torch import (
    ConfigurationEnergyTrainingView,
    TrainingConfigurationBatch,
)

SCOPE = 'DRAFT_CONDITIONAL_JOINT_PRODUCT_TRAINING_EQUATIONS'
BASELINE_KIND_BY_METHOD = {
    b06.PRIMARY_METHOD_ID: 'ANALYTIC_PROPAGATED_GUIDE_LOG',
    b06.PRIMARY_COMPARATOR_ID: 'TERMINAL_LIKELIHOOD_LOG',
}


def _label(value, name):
    if type(value) is not str or re.fullmatch(r'[A-Za-z0-9_.:-]{1,256}', value) is None:
        raise ValueError(f'{name} must be an explicit bounded plain label')
    return value


def _float_tensor(value, name, *, device, shape=None, detached=False):
    if (type(value) is not torch.Tensor or value.layout != torch.strided
            or value.dtype != torch.float32 or value.device != device
            or not bool(torch.isfinite(value).all())):
        raise ValueError(f'{name} must be finite dense FP32 on the model device')
    if shape is not None and tuple(value.shape) != tuple(shape):
        raise ValueError(f'{name} shape differs from the paired batch')
    if detached and value.requires_grad:
        raise ValueError(f'{name} must be an externally supplied detached feature/value')


@dataclass(frozen=True)
class ObservationOnlyInputs:
    """Explicit finite feature vectors for (a,m,z); no latent or time member."""

    observation: torch.Tensor
    task: torch.Tensor
    context: torch.Tensor

    def validate(self, *, device, size, forbidden_tensors=()):
        pointers = {value.untyped_storage().data_ptr() for value in forbidden_tensors if value.numel()}
        for name in ('observation', 'task', 'context'):
            value = getattr(self, name)
            _float_tensor(value, f'observation-only {name}', device=device, detached=True)
            if value.ndim != 2 or value.shape[0] != size:
                raise ValueError('observation-only inputs must have one feature row per pair')
            if value.numel() and value.untyped_storage().data_ptr() in pointers:
                raise ValueError('nuisance input aliases a latent/time input')


@dataclass(frozen=True)
class ConditionalLogitBatch:
    configuration: TrainingConfigurationBatch
    observation_only: ObservationOnlyInputs
    baseline_log_values: torch.Tensor
    baseline_kind: str


@dataclass(frozen=True)
class ConditionalLogitComponents:
    physical_log_potential: torch.Tensor
    gated_residual: torch.Tensor
    nuisance: torch.Tensor
    logit: torch.Tensor


def _select_rows(batch, selected):
    """Retain all occurrences, reindexing owners for active gate rows only."""
    mapping = torch.full((batch.forward_time.numel(),), -1, dtype=torch.int64, device=selected.device)
    mapping[selected] = torch.arange(selected.numel(), dtype=torch.int64, device=selected.device)
    coordinates, owners = [], []
    for values, original_owners in zip(batch.coordinates, batch.batch_indices):
        new_owners = mapping[original_owners]
        mask = new_owners >= 0
        coordinates.append(values[mask])
        owners.append(new_owners[mask])
    return TrainingConfigurationBatch(
        batch.architecture_sha256, batch.forward_time[selected], batch.context[selected],
        tuple(coordinates), tuple(owners),
    )


class ConditionalClassifier(nn.Module):
    """Supplied energy+nuisance modules, with distinct physical/logit surfaces.

    The nuisance forward signature is exactly (observation, task, context).
    A detached feature codec must be supplied separately; this is not a claim
    that its architecture, capacity, or scientific feature origin is frozen.
    """

    def __init__(self, backbone: ConfigurationEnergyTrainingView, nuisance: nn.Module, *,
                 method_id: str, clean_hold: float, nuisance_architecture_id: str):
        super().__init__()
        if type(backbone) is not ConfigurationEnergyTrainingView:
            raise TypeError('an explicit FP32 ConfigurationEnergyTrainingView is required')
        if type(method_id) is not str or method_id not in BASELINE_KIND_BY_METHOD:
            raise ValueError('only the two frozen primary method roles are supported')
        if not isinstance(nuisance, nn.Module) or isinstance(nuisance, (nn.DataParallel, nn.parallel.DistributedDataParallel)):
            raise TypeError('an explicitly supplied ordinary observation-only nuisance module is required')
        if type(clean_hold) is not float or not 0 <= clean_hold < backbone.architecture.schedule_horizon:
            raise ValueError('clean_hold must be a finite direct-time boundary strictly before the horizon')
        if clean_hold.hex() != backbone.architecture.clean_hold.hex():
            raise ValueError('clean_hold must exactly match the process-owned architecture boundary')
        self.backbone = deepcopy(backbone)
        self.nuisance = deepcopy(nuisance).to(device=backbone.execution_device)
        self.method_id = method_id
        self.clean_hold = clean_hold
        self.nuisance_architecture_id = _label(nuisance_architecture_id, 'nuisance_architecture_id')
        for value in (*self.nuisance.parameters(), *self.nuisance.buffers()):
            _float_tensor(value.detach(), 'nuisance state', device=self.execution_device)

    @property
    def execution_device(self):
        return self.backbone.execution_device

    def _validated(self, batch):
        if type(batch) is not ConditionalLogitBatch:
            raise TypeError('an exact ConditionalLogitBatch is required')
        if batch.baseline_kind != BASELINE_KIND_BY_METHOD[self.method_id]:
            raise ValueError('baseline role does not match guide-plus-residual or direct method')
        size = self.backbone._validate_batch(batch.configuration)
        _float_tensor(batch.baseline_log_values, 'fixed baseline log-values',
                      device=self.execution_device, shape=(size,), detached=True)
        return size

    def gated_residual(self, batch: ConditionalLogitBatch):
        size = self._validated(batch)
        direct_time = batch.configuration.forward_time
        horizon = self.backbone.architecture.schedule_horizon
        # s=S-u: a_R(u)=(max(s-s_hold,0)/(S-s_hold))**3.
        active = torch.nonzero(direct_time > self.clean_hold, as_tuple=False).flatten()
        result = torch.zeros(size, dtype=torch.float32, device=self.execution_device)
        if not active.numel():
            return result  # Canonical +0 without evaluating the neural model.
        active_batch = _select_rows(batch.configuration, active)
        gate = ((active_batch.forward_time - self.clean_hold) / (horizon - self.clean_hold)).pow(3)
        if not bool(torch.isfinite(gate).all()) or bool(((gate <= 0) | (gate > 1)).any()):
            raise ArithmeticError('active residual gate is not finite in (0,1] in FP32')
        # The backbone already performs B*tanh(F/B): multiply by the gate ONCE.
        residual = gate * self.backbone(active_batch)
        return result.index_copy(0, active, residual)

    def physical_log_potential(self, batch: ConditionalLogitBatch):
        """log h_hat only; never evaluates nuisance or exponentiates a tilt.

        Baseline values have no autograd graph here. Consequently this API
        supplies log-potential values, not complete analytic-guide derivatives.
        """
        result = batch.baseline_log_values + self.gated_residual(batch)
        _float_tensor(result, 'physical log-potential', device=self.execution_device)
        return result

    def components(self, batch: ConditionalLogitBatch):
        size = self._validated(batch)
        if type(batch.observation_only) is not ObservationOnlyInputs:
            raise TypeError('an exact observation-only interface is required')
        batch.observation_only.validate(
            device=self.execution_device, size=size,
            forbidden_tensors=(batch.configuration.forward_time, *batch.configuration.coordinates),
        )
        residual = self.gated_residual(batch)
        physical = batch.baseline_log_values + residual
        observation = batch.observation_only
        nuisance = self.nuisance(observation.observation, observation.task, observation.context)
        _float_tensor(nuisance, 'nuisance output', device=self.execution_device, shape=(size,))
        logit = physical + nuisance
        _float_tensor(logit, 'classifier logit', device=self.execution_device, shape=(size,))
        return ConditionalLogitComponents(physical, residual, nuisance, logit)

    def forward(self, batch: ConditionalLogitBatch):
        return self.components(batch).logit

    def description(self):
        return {
            'scope': SCOPE, 'method_id': self.method_id,
            'baseline_kind': BASELINE_KIND_BY_METHOD[self.method_id],
            'nuisance_architecture_id': self.nuisance_architecture_id,
            'conditional_parameter_count': self.backbone.parameter_count,
            'additional_nuisance_parameter_count': sum(value.numel() for value in self.nuisance.parameters()),
            'nuisance_excluded_from_physical_potential': True,
            'nuisance_architecture_or_capacity_frozen': False,
            'observation_feature_origin_authenticated': False,
            'task_context_time_law_authenticated': False,
            'rn_weights_authenticated': False,
            'sampler_or_scientific_training_admitted': False,
            'b06_parameter_count_successor_adopted': False,
        }


def _round_nonnegative_fraction_fp32(value: Fraction) -> float:
    """One exact-ratio nearest/even conversion, including midpoint cases.

    Binary64 gives an initial FP32 candidate. Comparing its two neighbours
    with the exact Fraction removes the possible binary64 double-rounding.
    Overflow and positive underflow are rejected by this training surface.
    """
    maximum = struct.unpack('>f', bytes.fromhex('7f7fffff'))[0]
    if value > Fraction(maximum):
        raise ArithmeticError('RN factor is outside the finite FP32 range')
    initial = struct.unpack('>I', struct.pack('>f', float(value)))[0]
    candidates = range(max(0, initial - 1), min(0x7f7fffff, initial + 1) + 1)
    def candidate(bits):
        return struct.unpack('>f', struct.pack('>I', bits))[0]
    winner = min(candidates, key=lambda bits: (abs(Fraction(candidate(bits)) - value), bits & 1))
    result = candidate(winner)
    if value > 0 and result == 0:
        raise ArithmeticError('positive RN factor underflowed in FP32')
    return result


@dataclass(frozen=True)
class SamplingLawWeights:
    """Exact, unnormalized class-conditional RN factors, retained as Fractions.

    Each class has its own empirical average and weight 1/2. These factors
    therefore concern the target/proposal class-CONDITIONAL law (including
    task/context/time/trajectory/observation), not a differently sampled class
    prior. Unequal class sampling and self-normalized factors are unsupported.
    Stored exact factors are rounded once to FP32 for the training arithmetic;
    neither their external law provenance nor exact-real arithmetic is claimed.
    """

    target_law_id: str
    proposal_law_id: str
    joint: tuple[Fraction, ...]
    product: tuple[Fraction, ...]
    uses_declared_law: bool

    @classmethod
    def declared(cls, *, law_id: str, size: int):
        if type(size) is not int or size < 1:
            raise ValueError('positive exact pair count required')
        values = (Fraction(1),) * size
        return cls(law_id, law_id, values, values, True)

    def tensors(self, *, size, device):
        _label(self.target_law_id, 'target_law_id')
        _label(self.proposal_law_id, 'proposal_law_id')
        if type(self.uses_declared_law) is not bool:
            raise ValueError('uses_declared_law must be exact boolean')
        for values in (self.joint, self.product):
            if type(values) is not tuple or len(values) != size:
                raise ValueError('one exact RN factor is required per member of each class')
            if any(type(value) is not Fraction or value < 0 for value in values):
                raise ValueError('RN factors must be exact nonnegative Fractions, not normalized tensors')
        if self.uses_declared_law:
            if self.target_law_id != self.proposal_law_id or any(value != 1 for value in self.joint + self.product):
                raise ValueError('declared law requires unit weights and identical law labels')
        elif self.target_law_id == self.proposal_law_id:
            raise ValueError('an alternative proposal requires a distinct explicit law label')
        result = []
        for values in (self.joint, self.product):
            tensor = torch.tensor([_round_nonnegative_fraction_fp32(value) for value in values], dtype=torch.float32, device=device)
            if not bool(torch.isfinite(tensor).all()) or any(value > 0 and item == 0 for value, item in zip(values, tensor.tolist())):
                raise ArithmeticError('RN factor overflowed or a positive factor underflowed in FP32')
            result.append(tensor)
        return tuple(result)

    def description(self):
        return {
            'target_law_id': self.target_law_id, 'proposal_law_id': self.proposal_law_id,
            'joint_exact_factors': [str(value) for value in self.joint],
            'product_exact_factors': [str(value) for value in self.product],
            'uses_declared_law': self.uses_declared_law,
            'self_normalization_performed': False,
            'operational_arithmetic': 'FP32_WITH_RETAINED_EXACT_RATIONAL_RN_INPUTS',
            'external_law_provenance_authenticated': False,
        }


def _same_pair_population(joint, product):
    """Check shared u,y,m,z, not a claim of independent simulated trajectories."""
    left, right = joint.configuration, product.configuration
    if not torch.equal(left.forward_time, right.forward_time):
        raise ValueError('joint/product pairs must share the same time per pair')
    if (len(left.coordinates) != len(right.coordinates)
            or any(not torch.equal(a, b) for a, b in zip(left.coordinates, right.coordinates))
            or any(not torch.equal(a, b) for a, b in zip(left.batch_indices, right.batch_indices))):
        raise ValueError('joint/product pairs must use the same first-trajectory latent state')
    for name in ('task', 'context'):
        if not torch.equal(getattr(joint.observation_only, name), getattr(product.observation_only, name)):
            raise ValueError('joint/product pairs must share identical task/context, not cross-context permutation')


def equal_prior_joint_product_loss(model: ConditionalClassifier, joint: ConditionalLogitBatch,
                                  product: ConditionalLogitBatch, weights: SamplingLawWeights):
    """0.5*mean(w_joint*softplus(-l_joint))+0.5*mean(w_product*softplus(l_product))."""
    if type(model) is not ConditionalClassifier or type(weights) is not SamplingLawWeights:
        raise TypeError('exact conditional classifier and explicit sampling-law weights required')
    joint_logits, product_logits = model(joint), model(product)
    if joint_logits.shape != product_logits.shape:
        raise ValueError('equal-prior paired risk requires equal nonempty class sizes')
    _same_pair_population(joint, product)
    joint_weights, product_weights = weights.tensors(size=joint_logits.numel(), device=model.execution_device)
    loss = 0.5 * ((joint_weights * functional.softplus(-joint_logits)).mean()
                  + (product_weights * functional.softplus(product_logits)).mean())
    _float_tensor(loss, 'conditional logistic loss', device=model.execution_device, shape=())
    return loss


def make_joint_product_loss_adapter(pair_builder: Callable):
    """Connect an explicit supplied pairing/feature codec to the generic trainer.

    pair_builder(batch_fields, generator) returns (joint, product, weights).
    The codec, not this adapter, owns the base-simulation and observation law.
    """
    if not callable(pair_builder):
        raise TypeError('an explicit pair builder/feature codec is required')
    def adapter(model, batch_fields, generator):
        joint, product, weights = pair_builder(batch_fields, generator)
        return equal_prior_joint_product_loss(model, joint, product, weights)
    return adapter
