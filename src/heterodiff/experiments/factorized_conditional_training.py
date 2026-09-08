"""Local mixed-key conditional learner; not a production/scientific certificate.

CPU FP32 learned graphs and CPU FP64 analytic guide/risk arithmetic. Raw visible
keys/context are consumed in full. Nuisance accepts observation only and never
enters the physical potential or initializer. No old finite-type API is widened.
"""
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
import json
import math

import torch
from torch import nn
from torch.nn import functional as F

from heterodiff.data.two_domain_factorized_state import FactoredEvent
from heterodiff.models.factorized_configuration_energy_torch import (
    BoundedFactorizedConfigurationEnergy, FactorizedConfigurationBatch,
    FactorizedEnergyLimits, FactorizedEnergyArchitecture,
    _Linear, _SharedByteEncoder, _bounded_coordinates, _validate_batch,
)
from heterodiff.models.two_domain_conditional_training_loss import SamplingLawWeights
from heterodiff.experiments.two_domain_baseline_registry import (
    PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID,
)

OBSERVATION_ENCODER_PARAMETERS = 51_200
NUISANCE_PARAMETERS = 53_313


class FactorizedTrainingError(ValueError):
    pass


def _need(value, message):
    if not value:
        raise FactorizedTrainingError(message)


def _label(value):
    _need(type(value) is str and bool(value) and len(value) <= 256
          and value.isascii(), 'bounded nonempty ASCII identity required')


def _seed(value):
    _need(type(value) is int and 0 <= value < 2**64, 'explicit uint64 seed required')


def _events(state):
    _need(type(state) is tuple and all(type(e) is FactoredEvent for e in state),
          'exact immutable factored event tuple required')
    _need(len({e.key.domain_id for e in state}) <= 1, 'mixed domains forbidden')


@dataclass(frozen=True)
class FactorizedObservation:
    observed: tuple[FactoredEvent, ...] | None
    domain_id: str
    task_id: str
    context_bytes: bytes

    def __post_init__(self):
        _label(self.domain_id)
        _label(self.task_id)
        _need(type(self.context_bytes) is bytes and bool(self.context_bytes),
              'explicit nonempty exact static-context bytes required')
        if self.observed is not None:
            _events(self.observed)
            _need(all(e.key.domain_id == self.domain_id for e in self.observed),
                  'observation domain differs from declared context')

    @property
    def context_identity(self):
        return self.domain_id, self.task_id, self.context_bytes

    @property
    def canonical_context_bytes(self):
        return json.dumps([self.domain_id, self.task_id, self.context_bytes.hex()],
                          separators=(',', ':'), ensure_ascii=True).encode('ascii')


def _observation_roster(values, limits, cap):
    _need(type(values) is tuple and 1 <= len(values) <= limits.maximum_batch_size,
          'bounded nonempty observation tuple required')
    events = total_bytes = 0
    for row in values:
        _need(type(row) is FactorizedObservation, 'exact visible observation required')
        row.__post_init__()
        retained = () if row.observed is None else row.observed
        _need(len(retained) <= cap, 'observation cap exceeded; no truncation')
        events += len(retained)
        _need(events <= limits.maximum_batch_events, 'visible event resource limit exceeded')
        _need(len(row.context_bytes) <= limits.maximum_metadata_bytes_per_event,
              'visible raw context byte limit exceeded; no truncation')
        for raw in (row.canonical_context_bytes, *(e.key.canonical_bytes() for e in retained)):
            _need(len(raw) <= limits.maximum_metadata_bytes_per_event,
                  'visible key/context byte limit exceeded; no truncation')
            total_bytes += len(raw)
    _need(events <= limits.maximum_batch_events, 'visible event resource limit exceeded')
    _need(total_bytes <= limits.maximum_total_metadata_bytes,
          'visible total-byte resource limit exceeded; no truncation')
    return events, total_bytes


class FactorizedObservationEncoder(nn.Module):
    """Shared complete-byte/DeepSets encoder; compression is not injective.

    The input has no latent state/time fields. 0D atoms, retained-empty and
    collapsed overflow remain distinct. Context gets an independent recurrence
    through the same byte parameters; every supplied byte is processed.
    """
    def __init__(self, *, limits, observation_cap, coordinate_scale, initialization_seed):
        super().__init__()
        _need(type(limits) is FactorizedEnergyLimits, 'explicit exact energy limits required')
        _need(type(observation_cap) is int and observation_cap >= 0, 'nonnegative observation cap required')
        _need(type(coordinate_scale) is float and math.isfinite(coordinate_scale)
              and coordinate_scale > 0, 'positive coordinate scale required')
        _need(float(torch.tensor(coordinate_scale, dtype=torch.float32, device='cpu'))
              == coordinate_scale, 'coordinate scale must be exactly FP32')
        _seed(initialization_seed)
        self.limits, self.observation_cap, self.coordinate_scale = limits, observation_cap, coordinate_scale
        rng = torch.Generator(device='cpu').manual_seed(initialization_seed)
        self.bytes = _SharedByteEncoder(rng)
        self.event_hidden = _Linear(34, 128, rng)
        self.event_output = _Linear(128, 128, rng)
        self.readout_hidden = _Linear(162, 128, rng)
        self.readout_output = _Linear(128, 64, rng)

    def forward(self, observations):
        _observation_roster(observations, self.limits, self.observation_cap)
        _finite_parameters(self)
        results = []
        for row in observations:
            retained = () if row.observed is None else row.observed
            embeddings = []
            for event in sorted(retained, key=lambda e: e.sort_key):
                active = event.key.dimension
                raw = torch.tensor([event.coordinate if active else 0.0], dtype=torch.float32, device='cpu')
                _need(bool(torch.isfinite(raw).all()), 'visible coordinate is not representable in FP32')
                scalar = _bounded_coordinates(raw, self.coordinate_scale)
                features = torch.cat((self.bytes(event.key.canonical_bytes()),
                                      torch.tensor([float(active)], dtype=torch.float32, device='cpu'), scalar))
                embeddings.append(torch.tanh(self.event_output(torch.tanh(self.event_hidden(features)))))
            pooled = (torch.stack(embeddings).sum(0)/(1+len(retained)) if embeddings
                      else torch.zeros(128, dtype=torch.float32, device='cpu'))
            flags = torch.tensor([float(row.observed is None), len(retained)/max(1, self.observation_cap)],
                                 dtype=torch.float32, device='cpu')
            merged = torch.cat((pooled, self.bytes(row.canonical_context_bytes), flags))
            results.append(torch.tanh(self.readout_output(torch.tanh(self.readout_hidden(merged)))))
        answer = torch.stack(results)
        _need(bool(torch.isfinite(answer).all()), 'nonfinite observation encoding')
        return answer

    def workload(self, observations):
        events, count = _observation_roster(observations, self.limits, self.observation_cap)
        return {'scope': 'GRAPH_COUNTS_NOT_F104_COST_WEIGHTS', 'metadata_bytes': count,
                'byte_recurrence_steps': count, 'byte_recurrence_matrix_macs': count*1024,
                'byte_scalar_multiplications': count*32,
                'event_affine_macs': events*(34*128+128*128),
                'readout_affine_macs': len(observations)*(162*128+128*64),
                'bias_tanh_pool_sort_and_autograd_included': False}


def _finite_parameters(module):
    for p in module.parameters():
        _need(p.dtype == torch.float32 and p.device.type == 'cpu'
              and p.layout == torch.strided and bool(torch.isfinite(p).all()),
              'learned parameters must remain finite dense CPU FP32')


class FactorizedObservationNuisance(nn.Module):
    def __init__(self, encoder, *, initialization_seed):
        super().__init__()
        _need(type(encoder) is FactorizedObservationEncoder, 'exact independent observation encoder required')
        _seed(initialization_seed)
        self.encoder = deepcopy(encoder)
        rng = torch.Generator(device='cpu').manual_seed(initialization_seed)
        self.hidden, self.output = _Linear(64, 32, rng), _Linear(32, 1, rng)

    def forward(self, observations):
        _finite_parameters(self)
        result = self.output(torch.tanh(self.hidden(self.encoder(observations)))).squeeze(1)
        _need(bool(torch.isfinite(result).all()), 'nonfinite nuisance')
        return result


def factorized_configuration_batch(states, reverse_times, contexts, architecture, *,
                                   coordinates=None, coordinate_gradients=False):
    """Build differentiable CPU FP32 rows, including higher coordinate derivatives.

    Optional supplied CPU FP64 coordinates retain their autograd connection
    through the FP32 cast. With coordinate_gradients=True new rows are leaves
    before conversion. No parameter or context gradient is detached.
    """
    _need(type(architecture) is FactorizedEnergyArchitecture, 'exact shared architecture required')
    _need(type(coordinate_gradients) is bool, 'exact coordinate-gradient flag required')
    _need(type(states) is tuple and bool(states), 'nonempty state roster required')
    _need(len(states) <= architecture.limits.maximum_batch_size, 'state batch resource limit exceeded')
    _need(type(reverse_times) is tuple and len(reverse_times) == len(states), 'aligned reverse times required')
    count = 0
    for state in states:
        _need(type(state) is tuple and len(state) <= architecture.total_cap, 'latent state cap exceeded; no truncation')
        count += len(state)
        _need(count <= architecture.limits.maximum_batch_events, 'latent event resource limit exceeded')
        _events(state)
    _need(all(type(u) is float and math.isfinite(u) and 0 <= u <= architecture.horizon for u in reverse_times),
          'reverse times outside declared horizon')
    flat = tuple(e for state in states for e in state)
    if coordinates is None:
        coordinates = tuple(torch.tensor([] if not e.key.dimension else [e.coordinate],
                                         dtype=torch.float64, device='cpu', requires_grad=coordinate_gradients) for e in flat)
    _need(type(coordinates) is tuple and len(coordinates) == len(flat), 'aligned coordinate tensors required')
    converted = []
    for event, value in zip(flat, coordinates):
        _need(type(value) is torch.Tensor and value.device.type == 'cpu' and value.dtype == torch.float64
              and tuple(value.shape) == (event.key.dimension,) and bool(torch.isfinite(value).all()),
              'coordinates require aligned finite CPU FP64 tensors')
        item = value.to(torch.float32)
        _need(bool(torch.isfinite(item).all()), 'latent coordinate FP32 overflow; no clipping')
        converted.append(item)
    batch = FactorizedConfigurationBatch(
        architecture.architecture_sha256, tuple(e.key.canonical_bytes() for e in flat),
        tuple(e.key.dimension for e in flat), tuple(converted),
        tuple(i for i, state in enumerate(states) for _ in state),
        torch.tensor([architecture.horizon-u for u in reverse_times], dtype=torch.float32, device='cpu'), contexts)
    _validate_batch(architecture, batch)
    return batch


def configuration_batch(backbone, states, reverse_times, context, *, coordinates=None):
    _need(type(backbone) is BoundedFactorizedConfigurationEnergy, 'exact shared energy required')
    return factorized_configuration_batch(states, reverse_times, context, backbone.architecture,
                                          coordinates=coordinates)


@dataclass(frozen=True)
class FactorizedTrainingBatch:
    states: tuple
    reverse_times: tuple[float, ...]
    observations: tuple[FactorizedObservation, ...]
    law_id: str


class FactorizedConditionalModel(nn.Module):
    def __init__(self, conditioner, *, guide, method_id, clean_hold, remaining_clocks,
                 observation_seed, nuisance_seed):
        super().__init__()
        _need(type(conditioner) is BoundedFactorizedConfigurationEnergy, 'exact shared conditioner energy required')
        _need(method_id in (PRIMARY_METHOD_ID, PRIMARY_COMPARATOR_ID), 'unknown conditional method')
        _need(type(clean_hold) is float and math.isfinite(clean_hold)
              and 0 <= clean_hold < conditioner.architecture.horizon, 'valid clean-hold boundary required')
        _need(callable(remaining_clocks), 'explicit remaining physical-clock callback required')
        _guide_type(guide)
        _need(conditioner.architecture.total_cap == guide.oracle.parameters.reference_cap,
              'conditioner cap must match declared reference cap')
        self.conditioner, self.guide = deepcopy(conditioner), deepcopy(guide)
        self.method_id, self.clean_hold, self.remaining_clocks = method_id, clean_hold, remaining_clocks
        self.encoder = FactorizedObservationEncoder(limits=conditioner.architecture.limits,
            observation_cap=guide.oracle.parameters.observation_cap,
            coordinate_scale=conditioner.architecture.coordinate_scale, initialization_seed=observation_seed)
        independent = FactorizedObservationEncoder(limits=conditioner.architecture.limits,
            observation_cap=guide.oracle.parameters.observation_cap,
            coordinate_scale=conditioner.architecture.coordinate_scale, initialization_seed=nuisance_seed)
        self.nuisance = FactorizedObservationNuisance(independent, initialization_seed=nuisance_seed)

    @property
    def horizon(self):
        return self.conditioner.architecture.horizon

    def _rows(self, states, reverse_times, observations):
        _observation_roster(observations, self.encoder.limits, self.encoder.observation_cap)
        _need(type(states) is tuple and len(states) == len(observations)
              and type(reverse_times) is tuple and len(reverse_times) == len(states), 'aligned conditional rows required')
        domain = self.guide.oracle.reference.domain_id
        for state, u, row in zip(states, reverse_times, observations):
            _need(type(state) is tuple and len(state) <= self.conditioner.architecture.total_cap,
                  'latent state cap exceeded; no truncation')
            _events(state)
            _need(type(u) is float and math.isfinite(u) and 0 <= u <= self.horizon, 'reverse time outside horizon')
            _need(row.domain_id == domain and all(e.key.domain_id == domain for e in state), 'conditional domain mismatch')

    def residual(self, states, reverse_times, observations, *, coordinates=None):
        self._rows(states, reverse_times, observations)
        context = self.encoder(observations)
        batch = configuration_batch(self.conditioner, states, reverse_times, context, coordinates=coordinates)
        direct = torch.tensor([self.horizon-u for u in reverse_times], dtype=torch.float64, device='cpu')
        gate = ((direct-self.clean_hold).clamp(min=0)/(self.horizon-self.clean_hold)).pow(3)
        # Exactly one gate, based on the declared binary64 clock, not a second FP32 clock.
        return self.conditioner(batch).to(torch.float64)*gate

    def baseline(self, states, reverse_times, observations, *, coordinates=None):
        self._rows(states, reverse_times, observations)
        _need(coordinates is None or (type(coordinates) is tuple
              and len(coordinates) == sum(map(len, states))), 'analytic coordinate roster must align exactly')
        results, offset = [], 0
        for state, u, row in zip(states, reverse_times, observations):
            clocks = self.remaining_clocks(u) if self.method_id == PRIMARY_METHOD_ID else (0.0, 0.0)
            _need(type(clocks) is tuple and len(clocks) == 2 and all(type(x) is float and math.isfinite(x) and x >= 0 for x in clocks),
                  'finite nonnegative remaining clock pair required')
            _need(u < self.horizon-self.clean_hold or clocks == (0.0, 0.0), 'nonzero remaining clock during clean hold')
            values = None if coordinates is None else coordinates[offset:offset+len(state)]
            result = self.guide.log_value(state, row.observed, coordinates=values,
                                          jump_clock=clocks[0], continuous_clock=clocks[1])
            _need(type(result) is torch.Tensor and result.device.type == 'cpu' and result.dtype == torch.float64
                  and result.ndim == 0 and bool(torch.isfinite(result)), 'guide must produce finite scalar CPU FP64')
            results.append(result)
            offset += len(state)
        return torch.stack(results)

    def forward(self, batch):
        _need(type(batch) is FactorizedTrainingBatch, 'exact factorized training batch required')
        _label(batch.law_id)
        result = (self.baseline(batch.states, batch.reverse_times, batch.observations)
                  + self.residual(batch.states, batch.reverse_times, batch.observations)
                  + self.nuisance(batch.observations).to(torch.float64))
        _need(bool(torch.isfinite(result).all()), 'nonfinite conditional classifier logit')
        return result

    def logits(self, batch):
        return self(batch)

    def paired_loss(self, joint, product, weights=None):
        if weights is None:
            weights = SamplingLawWeights.declared(law_id=joint.law_id, size=len(joint.states))
        return factorized_joint_product_loss(self, joint, product, weights)

    def parameter_summary(self):
        return {'conditioner': self.conditioner.parameter_count,
                'observation_encoder': sum(p.numel() for p in self.encoder.parameters()),
                'independent_nuisance': sum(p.numel() for p in self.nuisance.parameters()),
                'unique_trainable_model_parameters': sum(p.numel() for p in self.parameters()),
                'base_parameters_included': False, 'production_parameter_freeze_adopted': False}

    def workload(self, batch):
        _need(type(batch) is FactorizedTrainingBatch, 'exact factorized training batch required')
        self._rows(batch.states, batch.reverse_times, batch.observations)
        n = len(batch.states)
        zero = torch.zeros(n, 64, dtype=torch.float32, device='cpu')
        configuration = configuration_batch(self.conditioner, batch.states, batch.reverse_times, zero)
        return {'scope': 'ONE_CLASS_FORWARD_GRAPH_NOT_F104_WEIGHTED_COST',
                'classifier_examples': n, 'analytic_guide_calls': n,
                'conditioner_batched_forward_calls': 1,
                'observation_encoder_batched_forward_calls': 2,
                'nuisance_head_affine_macs': n*(64*32+32),
                'conditioner': self.conditioner.workload(configuration),
                'each_observation_encoder': self.encoder.workload(batch.observations),
                'joint_product_requires_two_class_forwards': True,
                'guide_matching_and_backprop_work_included': False,
                'production_budget_adopted': False}


def _guide_type(guide):
    # Imported lazily to keep model and guide modules acyclic.
    from heterodiff.theory.factorized_association_guide_torch import FactorizedAssociationGuide
    _need(type(guide) is FactorizedAssociationGuide, 'exact mixed-key analytic association guide required')


def factorized_joint_product_loss(model, joint, product, weights):
    _need(type(model) is FactorizedConditionalModel, 'exact mixed conditional model required')
    _need(type(joint) is FactorizedTrainingBatch and type(product) is FactorizedTrainingBatch,
          'exact joint/product batches required')
    _need(joint.states == product.states and joint.reverse_times == product.reverse_times,
          'joint/product must share first state and reverse time')
    _need(tuple(r.context_identity for r in joint.observations) == tuple(r.context_identity for r in product.observations),
          'joint/product must share exact task and static context')
    _need(type(weights) is SamplingLawWeights, 'exact declared RN weight record required')
    _label(weights.target_law_id); _label(weights.proposal_law_id)
    _need(joint.law_id == product.law_id == weights.proposal_law_id, 'sampling law identity mismatch')
    _need(type(weights.uses_declared_law) is bool, 'exact declared-law flag required')
    n = len(joint.states)
    converted = []
    for row in (weights.joint, weights.product):
        _need(type(row) is tuple and len(row) == n and all(type(x) is Fraction and x >= 0 for x in row),
              'aligned exact nonnegative class-conditional RN weights required')
        try:
            values = torch.tensor([float(x) for x in row], dtype=torch.float64, device='cpu')
        except OverflowError as error:
            raise FactorizedTrainingError('RN weight FP64 overflow') from error
        _need(bool(torch.isfinite(values).all()) and all(x == 0 or y > 0 for x,y in zip(row, values.tolist())),
              'RN weight FP64 overflow/positive underflow')
        converted.append(values)
    if weights.uses_declared_law:
        _need(weights.target_law_id == weights.proposal_law_id and all(x == 1 for x in weights.joint+weights.product),
              'declared law requires exact unit weights')
    else:
        _need(weights.target_law_id != weights.proposal_law_id, 'alternative law needs distinct target/proposal identities')
    j, p = model(joint), model(product)
    _need(j.shape == p.shape and j.numel() > 0, 'equal positive class sizes required')
    result = .5*((converted[0]*F.softplus(-j)).mean()+(converted[1]*F.softplus(p)).mean())
    _need(bool(torch.isfinite(result)), 'nonfinite paired FP64 risk')
    return result


class FactorizedPhysicalPotential:
    """Frozen CPU snapshot: V+baseline+gated residual, never nuisance.

    Coordinates enter the learned graph through an explicit FP64→FP32 cast;
    returned derivatives are local autograd derivatives of that numeric graph,
    not old certified derivatives or interval bounds.
    """
    def __init__(self, base, *, base_context, conditional_model=None, observation=None, clean_hold=None):
        _need(type(base) is BoundedFactorizedConfigurationEnergy, 'exact base energy required')
        _need(type(base_context) is tuple and len(base_context) == 64
              and all(type(x) is float and math.isfinite(x) for x in base_context), 'explicit finite64D base context required')
        self.base_context = torch.tensor([base_context], dtype=torch.float32, device='cpu')
        _need(bool(torch.isfinite(self.base_context).all()), 'base context FP32 overflow')
        self.base = deepcopy(base).eval().requires_grad_(False)
        self.model = None
        self.observation = observation
        if conditional_model is not None:
            _need(type(conditional_model) is FactorizedConditionalModel and type(observation) is FactorizedObservation,
                  'matching conditional model and observation required')
            _need(base.architecture.horizon == conditional_model.horizon
                  and base.architecture.metadata_schema_id == conditional_model.conditioner.architecture.metadata_schema_id
                  and base.architecture.total_cap == conditional_model.conditioner.architecture.total_cap,
                  'base/conditioner carrier or horizon mismatch')
            self.model = deepcopy(conditional_model).eval().requires_grad_(False)
            self.model._rows(((),), (0.0,), (observation,))
        else:
            _need(observation is None, 'base-only potential cannot accept an unused observation')
        if self.model is not None:
            _need(clean_hold is None or (type(clean_hold) is float and clean_hold.hex() == self.model.clean_hold.hex()),
                  'physical clean hold differs from conditional model')
            clean_hold = self.model.clean_hold
        _need(type(clean_hold) is float and math.isfinite(clean_hold)
              and 0 <= clean_hold < self.base.architecture.horizon,
              'explicit valid clean hold required for physical BASE extension')
        self.clean_hold = clean_hold
        tilt = 0.0 if self.model is None else (
            self.model.guide.upper_log_bound(observation.observed) + self.model.conditioner.architecture.value_bound)
        self.initialization_upper_log_bound = tilt
        self.initialization_residual_upper_bound = (0.0 if self.model is None else
                                                    self.model.conditioner.architecture.value_bound)
        self.upper_value_bound = self.base.architecture.value_bound + tilt
        _need(math.isfinite(tilt) and math.isfinite(self.upper_value_bound), 'nonfinite analytic upper bound')

    def _coordinates(self, state, requires_grad):
        _events(state)
        return tuple(torch.tensor([] if not e.key.dimension else [e.coordinate],
                                  dtype=torch.float64, device='cpu', requires_grad=requires_grad) for e in state)

    def _tilt(self, u, state, coordinates):
        if self.model is None:
            return torch.tensor(0.0, dtype=torch.float64, device='cpu')
        rows = (self.observation,)
        return (self.model.baseline((state,), (u,), rows, coordinates=coordinates)
                + self.model.residual((state,), (u,), rows, coordinates=coordinates))[0]

    def initialization_log_tilt(self, u, state):
        coordinates = self._coordinates(state, False)
        # Validate carrier/time even for base-only initialization.
        batch = configuration_batch(self.base, (state,), (u,), self.base_context, coordinates=coordinates)
        self.base.workload(batch)
        with torch.no_grad():
            value = self._tilt(u, state, coordinates)
        _need(bool(torch.isfinite(value)), 'nonfinite initializer tilt')
        return float(value)

    def initialization_residual_log_tilt(self, state):
        """Residual only, at reverse time zero, after analytic guide-posterior sampling."""
        coordinates = self._coordinates(state, False)
        batch = configuration_batch(self.base, (state,), (0.0,), self.base_context, coordinates=coordinates)
        self.base.workload(batch)
        if self.model is None:
            return 0.0
        with torch.no_grad():
            value = self.model.residual((state,), (0.0,), (self.observation,), coordinates=coordinates)[0]
        _need(bool(torch.isfinite(value)), 'nonfinite initializer residual')
        return float(value)

    def _value(self, u, state, coordinates):
        _need(type(u) is float and math.isfinite(u) and 0 <= u <= self.base.architecture.horizon,
              'physical reverse time outside horizon')
        # Adapter-owned hold extension, not an intrinsic backbone certificate:
        # BASE direct time is max(S-u,hold); the conditional gate uses original u.
        base_u = min(u, self.base.architecture.horizon-self.clean_hold)
        batch = configuration_batch(self.base, (state,), (base_u,), self.base_context, coordinates=coordinates)
        return self.base(batch)[0].to(torch.float64) + self._tilt(u, state, coordinates)

    def value(self, u, state):
        coordinates = self._coordinates(state, False)
        with torch.no_grad():
            value = self._value(u, state, coordinates)
        _need(bool(torch.isfinite(value)), 'nonfinite physical potential')
        return float(value)

    def value_grad(self, u, state):
        coordinates = self._coordinates(state, True)
        with torch.enable_grad():
            value = self._value(u, state, coordinates)
            gradients = (torch.autograd.grad(value, coordinates, allow_unused=True)
                         if coordinates and value.requires_grad else (None,)*len(coordinates))
        _need(bool(torch.isfinite(value)), 'nonfinite physical potential')
        rows = []
        for coordinate, gradient in zip(coordinates, gradients):
            if gradient is None:
                gradient = torch.zeros_like(coordinate)
            _need(bool(torch.isfinite(gradient).all()), 'nonfinite physical gradient')
            rows.append(tuple(float(x) for x in gradient))
        return float(value.detach()), tuple(rows)
