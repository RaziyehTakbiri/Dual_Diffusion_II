"""Additive observation-trained neural potential and hybrid pipeline interfaces.

Local numerical/design proposal only. The angular count sensor and positive
one-dimensional output chart are explicit synthetic examples, NOT the real
domains' association observation kernel or an inverse of the F105 embedding.
Neither coordinate gradients nor sampled paths acquire CPU certification here.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
import math

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from heterodiff.models.configuration_energy_training_torch import (
    ConfigurationEnergyTrainingView, TrainingConfigurationBatch,
)
from heterodiff.models.two_domain_conditional_training_loss import (
    BASELINE_KIND_BY_METHOD, ConditionalClassifier, ConditionalLogitBatch,
    SamplingLawWeights,
)
from heterodiff.models.two_domain_observation_training_design import (
    ObservationTrainingBatch, ObservationConditionEncoderV1, ObservationOnlyNuisanceV1,
)
from heterodiff.theory.configuration_reference import (
    MIN_REFERENCE_CATEGORICAL_PROBABILITY, TransformedEvent,
)
from heterodiff.theory.finite_state import transition_matrix


class HybridTrainingError(ValueError):
    pass


class _UnusedNuisance(nn.Module):
    def forward(self, observation, task, context):
        raise HybridTrainingError('unused core nuisance must never be called')


def _states(architecture, values):
    if type(values) is not tuple or not values:
        raise HybridTrainingError('nonempty tuple of configurations required')
    dimensions = dict(zip(architecture.type_ids, architecture.type_dimensions))
    for state in values:
        if (type(state) is not tuple or len(state) > architecture.total_cap
                or any(type(event) is not TransformedEvent for event in state)):
            raise HybridTrainingError('exact bounded transformed configurations required')
        if state != tuple(sorted(state, key=TransformedEvent.model_key)):
            raise HybridTrainingError('configuration order must be canonical')
        if any(event.event_type not in dimensions
               or len(event.coordinates) != dimensions[event.event_type] for event in state):
            raise HybridTrainingError('configuration fiber differs from the model')


def configuration_batch(backbone, states, reverse_times, context, *, coordinate_gradients=False):
    """Preserve occurrences; model direct time is s=S-u, never a supplied second clock."""
    _states(backbone.architecture, states)
    horizon = backbone.architecture.schedule_horizon
    if (type(reverse_times) is not tuple or len(reverse_times) != len(states)
            or any(type(u) is not float or not math.isfinite(u) or not 0 <= u <= horizon
                   for u in reverse_times)):
        raise HybridTrainingError('one finite reverse time in [0,S] per state required')
    coordinates, indices = [], []
    for kind, width in zip(backbone.architecture.type_ids, backbone.architecture.type_dimensions):
        rows = [(owner, event) for owner, state in enumerate(states)
                for event in state if event.event_type == kind]
        values = torch.tensor([event.coordinates for _, event in rows], dtype=torch.float32,
                              device=backbone.execution_device).reshape(len(rows), width)
        values.requires_grad_(coordinate_gradients)
        coordinates.append(values)
        indices.append(torch.tensor([owner for owner, _ in rows], dtype=torch.int64,
                                    device=backbone.execution_device))
    batch = TrainingConfigurationBatch(
        backbone.architecture.architecture_sha256,
        torch.tensor([horizon-u for u in reverse_times], dtype=torch.float32,
                     device=backbone.execution_device), context, tuple(coordinates), tuple(indices))
    backbone._validate_batch(batch)
    return batch


@dataclass(frozen=True)
class ObservedTrainingBatch:
    states: tuple
    reverse_times: tuple[float, ...]
    observation: ObservationTrainingBatch
    baseline_log_values: torch.Tensor
    baseline_kind: str


class ObservedConditionalTrainingModel(nn.Module):
    """Trainable observation encoder and independent nuisance, no y/u nuisance input.

    Reuses the existing core's bounded residual and single cubic gate. Both
    observation encoders receive detached visible data; encoder parameters
    remain trainable. The nuisance's independent encoder is never physical.
    """
    def __init__(self, backbone, encoder, nuisance, *, method_id):
        super().__init__()
        if (type(backbone) is not ConfigurationEnergyTrainingView
                or type(encoder) is not ObservationConditionEncoderV1
                or type(nuisance) is not ObservationOnlyNuisanceV1):
            raise HybridTrainingError('explicit training view and proposed observation modules required')
        if backbone.architecture.context_dimension != 64:
            raise HybridTrainingError('the proposed observation interface has exactly64 channels')
        if encoder.schema.schema_sha256 != nuisance.encoder.schema.schema_sha256:
            raise HybridTrainingError('condition and nuisance observation schemas differ')
        self.conditioner = ConditionalClassifier(
            backbone, _UnusedNuisance(), method_id=method_id,
            clean_hold=backbone.architecture.clean_hold,
            nuisance_architecture_id='UNUSED_CORE_NUISANCE_REAL_BRANCH_IS_SEPARATE')
        self.encoder = deepcopy(encoder).to(backbone.execution_device)
        self.nuisance = deepcopy(nuisance).to(backbone.execution_device)
        self.method_id = method_id

    @property
    def execution_device(self):
        return self.conditioner.execution_device

    def residual(self, states, reverse_times, observation):
        if type(observation) is not ObservationTrainingBatch:
            raise HybridTrainingError('visible observation batch required')
        encoded = self.encoder(observation)
        batch = configuration_batch(self.conditioner.backbone, states, reverse_times, encoded)
        observation.validate(self.encoder.schema,
                             forbidden_tensors=(batch.forward_time, *batch.coordinates))
        zero = torch.zeros(len(states), dtype=torch.float32, device=self.execution_device)
        return self.conditioner.gated_residual(ConditionalLogitBatch(
            batch, None, zero, BASELINE_KIND_BY_METHOD[self.method_id]))

    def forward(self, batch):
        if type(batch) is not ObservedTrainingBatch:
            raise HybridTrainingError('exact observed training batch required')
        baseline = batch.baseline_log_values
        if (batch.baseline_kind != BASELINE_KIND_BY_METHOD[self.method_id]
                or type(baseline) is not torch.Tensor or baseline.requires_grad
                or baseline.shape != (len(batch.states),) or baseline.dtype != torch.float32
                or baseline.device != self.execution_device or not bool(torch.isfinite(baseline).all())):
            raise HybridTrainingError('fixed finite FP32 baseline with matching method role required')
        residual = self.residual(batch.states, batch.reverse_times, batch.observation)
        nuisance = self.nuisance(batch.observation)
        value = baseline + residual + nuisance
        if value.shape != baseline.shape or not bool(torch.isfinite(value).all()):
            raise HybridTrainingError('conditional logits are invalid')
        return value

    def parameter_summary(self):
        return dict(scope='REVIEW_PENDING_OBSERVED_CONDITIONAL_MODEL',
                    conditioner_parameters=sum(p.numel() for p in self.conditioner.parameters()),
                    observation_encoder_parameters=sum(p.numel() for p in self.encoder.parameters()),
                    nuisance_including_independent_encoder_parameters=sum(p.numel() for p in self.nuisance.parameters()),
                    all_unique_parameters=sum(p.numel() for p in self.parameters()),
                    production_configuration_adopted=False,
                    nuisance_excluded_from_physical_potential=True)


def observed_joint_product_loss(model, joint, product, weights):
    if type(model) is not ObservedConditionalTrainingModel or type(weights) is not SamplingLawWeights:
        raise HybridTrainingError('explicit proposed model and sampling law required')
    if type(joint) is not ObservedTrainingBatch or type(product) is not ObservedTrainingBatch:
        raise HybridTrainingError('exact joint and product batches required')
    if joint.states != product.states or joint.reverse_times != product.reverse_times:
        raise HybridTrainingError('joint/product must share first latent and time')
    if joint.observation.task_context_sha256s != product.observation.task_context_sha256s:
        raise HybridTrainingError('raw task/static context identities differ')
    for field in ('task_features', 'static_context_features'):
        if not torch.equal(getattr(joint.observation, field), getattr(product.observation, field)):
            raise HybridTrainingError('joint/product must share task/static context')
    j, p = model(joint), model(product)
    if j.shape != p.shape:
        raise HybridTrainingError('equal class sizes required')
    wj, wp = weights.tensors(size=j.numel(), device=model.execution_device)
    value = 0.5*((wj*F.softplus(-j)).mean()+(wp*F.softplus(p)).mean())
    if not bool(torch.isfinite(value)):
        raise HybridTrainingError('paired risk is not finite')
    return value


class TorchHybridPotential:
    """CPU numerical snapshot: same total scalar supplies drift and jump tilt.

    baseline(u,state,coordinate_tensors) returns a scalar differentiable Torch
    log potential; its finite upper bound is declared, not globally certified.
    For candidate-base simulation omit the conditional model. For conditional
    initialization set include_base=False: V must NOT enter that tilt.
    """
    def __init__(self, base, base_context, *, conditional=None, observation=None,
                 baseline=None, baseline_upper_bound=0.0, include_base=True):
        if type(base) is not ConfigurationEnergyTrainingView or base.execution_device.type != 'cpu':
            raise HybridTrainingError('this numerical potential adapter is CPU-only')
        if type(include_base) is not bool:
            raise HybridTrainingError('include_base must be explicit bool')
        if (type(base_context) is not torch.Tensor or base_context.dtype != torch.float32
                or base_context.device.type != 'cpu' or base_context.requires_grad
                or base_context.shape != (1, base.architecture.context_dimension)
                or not bool(torch.isfinite(base_context).all())):
            raise HybridTrainingError('separate detached base context required')
        if conditional is not None:
            retained_pair = (type(conditional) is ObservedConditionalTrainingModel
                             and type(observation) is ObservationTrainingBatch)
            association_pair = False
            if not retained_pair:
                # Additive alternative-law proposal; do not widen retained-only contracts.
                from heterodiff.experiments.association_observation_training_adapter import (
                    AssociationConditionalTrainingModel, AssociationObservationBatch,
                )
                association_pair = (type(conditional) is AssociationConditionalTrainingModel
                                    and type(observation) is AssociationObservationBatch)
                if association_pair:
                    if (conditional.kernel_sha256 != observation.kernel_sha256
                            or getattr(baseline, 'kernel_sha256', None) != conditional.kernel_sha256
                            or getattr(baseline, 'propagated', None) is not
                            (BASELINE_KIND_BY_METHOD[conditional.method_id] == 'ANALYTIC_PROPAGATED_GUIDE_LOG')):
                        raise HybridTrainingError('association kernel or baseline role differs')
            if (not (retained_pair or association_pair) or not callable(baseline)
                    or conditional.execution_device.type != 'cpu'):
                raise HybridTrainingError('conditional potential requires observed model and explicit baseline')
            architecture = conditional.conditioner.backbone.architecture
            if ((architecture.type_ids, architecture.type_dimensions, architecture.total_cap,
                 architecture.schedule_horizon, architecture.clean_hold) !=
                    (base.architecture.type_ids, base.architecture.type_dimensions, base.architecture.total_cap,
                     base.architecture.schedule_horizon, base.architecture.clean_hold)):
                raise HybridTrainingError('base/conditional process interfaces differ')
        elif observation is not None or baseline is not None or not include_base:
            raise HybridTrainingError('base-only adapter has no conditional inputs')
        if type(baseline_upper_bound) is not float or not math.isfinite(baseline_upper_bound):
            raise HybridTrainingError('finite baseline upper bound required')
        self.base = deepcopy(base)
        self.base_context = base_context.detach().clone()
        self.conditional = deepcopy(conditional)
        self.observation = deepcopy(observation)
        self.baseline = baseline
        self.include_base = include_base
        base_bound = base.architecture.value_bound if include_base else 0.0
        residual_bound = 0.0 if conditional is None else conditional.conditioner.backbone.architecture.value_bound
        # Conservative FP32 arithmetic guard, not a certified outward interval.
        # The baseline's global bound remains a caller premise.
        bound = base_bound + residual_bound + max(0.0,baseline_upper_bound)
        self.upper_value_bound = bound + 32*np.finfo(np.float32).eps*max(1.0,bound)
        self.baseline_upper_bound = baseline_upper_bound

    def _evaluate(self, u, state, gradients):
        with torch.enable_grad() if gradients else torch.no_grad():
            batch = configuration_batch(self.base, (state,), (u,), self.base_context,
                                        coordinate_gradients=gradients)
            total = self.base(batch)[0] if self.include_base else torch.zeros((), dtype=torch.float32)
            if self.conditional is not None:
                model = self.conditional
                guide = self.baseline(u, state, batch.coordinates)
                if (type(guide) is not torch.Tensor or guide.shape != () or guide.dtype != torch.float32
                        or guide.device.type != 'cpu' or not bool(torch.isfinite(guide))):
                    raise HybridTrainingError('baseline must return one finite CPU FP32 scalar')
                if float(guide.detach()) > self.baseline_upper_bound + 1e-6:
                    raise HybridTrainingError('baseline exceeds declared numerical upper bound')
                context = model.encoder(self.observation)
                conditioned = TrainingConfigurationBatch(
                    model.conditioner.backbone.architecture.architecture_sha256,
                    batch.forward_time, context, batch.coordinates, batch.batch_indices)
                residual = model.conditioner.gated_residual(ConditionalLogitBatch(
                    conditioned, None, torch.zeros(1,dtype=torch.float32),
                    BASELINE_KIND_BY_METHOD[model.method_id]))[0]
                total = total + guide + residual
            value = float(total.detach())
            if not math.isfinite(value) or value > self.upper_value_bound:
                raise HybridTrainingError('total potential exceeds its numerical bound')
            if not gradients:
                return value
            if total.requires_grad:
                derivative = torch.autograd.grad(total, batch.coordinates, allow_unused=True)
            else:
                derivative = (None,)*len(batch.coordinates)
            rows = {}
            for kind, values, gradient in zip(self.base.architecture.type_ids, batch.coordinates, derivative):
                grad = torch.zeros_like(values) if gradient is None else gradient
                if not bool(torch.isfinite(grad).all()):
                    raise HybridTrainingError('coordinate gradient is nonfinite')
                rows[kind] = iter(grad.detach().tolist())
            return value, tuple(tuple(next(rows[event.event_type])) for event in state)

    def value(self, u, state):
        return self._evaluate(u, state, False)

    def value_grad(self, u, state):
        return self._evaluate(u, state, True)


class ConditionalRejectionInitializer:
    """Local rejection from Pi_N using ONLY the time-zero log h_hat factor.

    No base V is included in the target tilt. Budget exhaustion fails; the
    implementation does not select SIR, truncate a proposal or return partial
    success. Numerical RNG/exp/global-envelope certification is not claimed.
    """
    def __init__(self, initial_factor, *, max_proposals=10000):
        if (type(initial_factor) is not TorchHybridPotential or initial_factor.include_base
                or initial_factor.conditional is None):
            raise HybridTrainingError('conditional initialization requires log h_hat only, not V')
        if type(max_proposals) is not int or not 1 <= max_proposals <= 100000:
            raise HybridTrainingError('bounded initializer proposal count required')
        self.factor=initial_factor
        self.max_proposals=max_proposals

    def __call__(self, process, rng):
        for _ in range(self.max_proposals):
            proposal=process.reference.sample_configuration(rng)
            log_accept=self.factor.value(0.0,proposal)-self.factor.upper_value_bound
            if not math.isfinite(log_accept) or log_accept > 0:
                raise HybridTrainingError('invalid conditional initializer envelope')
            probability=math.exp(log_accept)
            if probability < MIN_REFERENCE_CATEGORICAL_PROBABILITY:
                raise HybridTrainingError('conditional initializer probability below supported floor')
            if float(rng.random()) < probability:
                return proposal
        raise HybridTrainingError('conditional initializer proposal budget exhausted')


@dataclass(frozen=True, eq=False, init=False)
class SyntheticAngularCountSensor:
    """Continuous count sensor with exactly specified REFERENCE propagated guide.

    g(a|y)/eta(a)=1+alpha*(-1)^n*cos(a), eta uniform on[0,2pi).
    Count birth/death semigroup gives the reference h; learned-base h_phi is
    not asserted equal. Finite matrix-exponential arithmetic is inherited.
    """
    reference: object
    schedule: object
    alpha: float
    q: np.ndarray
    f: np.ndarray

    def __init__(self, process, *, alpha=0.5):
        if type(alpha) is not float or not 0 < alpha < 1:
            raise HybridTrainingError('alpha must be strictly between zero and one')
        if process.reference.total_cap > 64:
            raise HybridTrainingError('synthetic count oracle supports cap<=64')
        # Snapshot the immutable reference/schedule, not the mutable process wrapper.
        object.__setattr__(self, 'reference', process.reference)
        object.__setattr__(self, 'schedule', process.schedule)
        object.__setattr__(self, 'alpha', alpha)
        cap = process.reference.total_cap
        q = np.zeros((cap+1,cap+1),dtype=np.float64)
        for n in range(cap+1):
            if n < cap: q[n,n+1] = process.rates.birth_rate
            if n: q[n,n-1] = n*process.rates.per_particle_death_rate
            q[n,n] = -math.fsum(q[n])
        object.__setattr__(self, 'q', np.frombuffer(q.tobytes(), dtype=np.float64).reshape(q.shape))
        f = np.array([(-1.0)**n for n in range(cap+1)], dtype=np.float64)
        object.__setattr__(self, 'f', np.frombuffer(f.tobytes(), dtype=np.float64))

    @lru_cache(maxsize=128)
    def _propagated_count_factors(self, u):
        area = self.schedule.jump_integral(0.0, self.schedule.horizon-u)
        return tuple(float(value) for value in transition_matrix(self.q, area)@self.f)

    def sample(self, state, context, rng):
        self.reference.canonicalize(state)
        for _ in range(10000):
            angle = float(rng.uniform(0.0, 2.0*math.pi))
            ratio = 1.0+self.alpha*self.f[len(state)]*math.cos(angle)
            if float(rng.random()) < ratio/(1.0+self.alpha):
                return angle
        raise HybridTrainingError('synthetic sensor rejection budget exhausted')

    def log_value(self, u, state, angle, *, propagated):
        self.reference.canonicalize(state)
        if (type(angle) is not float or not math.isfinite(angle) or not 0 <= angle < 2*math.pi
                or type(u) is not float or not 0 <= u <= self.schedule.horizon
                or type(propagated) is not bool):
            raise HybridTrainingError('valid angular observation/reverse time required')
        factor = self.f[len(state)]
        if propagated:
            factor = self._propagated_count_factors(u)[len(state)]
        ratio = 1.0+self.alpha*factor*math.cos(angle)
        if not 1-self.alpha-1e-12 <= ratio <= 1+self.alpha+1e-12:
            raise HybridTrainingError('reference count guide outside analytic bounds')
        return math.log(ratio)

    def baseline(self, angle, *, propagated):
        def value(u, state, coordinate_tensors):
            return torch.tensor(self.log_value(u,state,angle,propagated=propagated),dtype=torch.float32)
        return value


def synthetic_positive_scalar_f105_configuration(domain_id, state):
    """Explicit synthetic chart, not projection/inversion of112/10 F105 vectors.

    Each1D transformed occurrence maps exp(x) to a binary64 positive value;
    exact binary64 F105 constructors preserve that represented value. All
    categorical/calendar/time fields below are fixed invented fixture values.
    """
    from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
        physionet_configuration, physionet_event_from_binary64,
        retail_configuration, retail_event_from_binary64,
    )
    if domain_id not in ('physionet-challenge-2012','online-retail-ii'):
        raise HybridTrainingError('unknown domain')
    if type(state) is not tuple or any(type(event) is not TransformedEvent
            or event.event_type != 0 or len(event.coordinates) != 1 for event in state):
        raise HybridTrainingError('synthetic chart requires type0, one-dimensional occurrences')
    result=[]
    for event in state:
        try:
            value=math.exp(event.coordinates[0])
        except OverflowError as error:
            raise HybridTrainingError('positive chart overflow; no clipping') from error
        if not math.isfinite(value) or value <= 0:
            raise HybridTrainingError('positive chart overflow/underflow; no clipping')
        if domain_id == 'physionet-challenge-2012':
            result.append(physionet_event_from_binary64(elapsed_minutes=0,parameter='HR',value=value))
        else:
            result.append(retail_event_from_binary64(invoice_no='100001',stock_code='SYNTHETIC',
                description='Invented hybrid trajectory',quantity=1,
                invoice_calendar=(2010,1,1,12,0,0,0),unit_price=value,country='Test'))
    return (physionet_configuration(tuple(result)) if domain_id == 'physionet-challenge-2012'
            else retail_configuration(tuple(result)))
