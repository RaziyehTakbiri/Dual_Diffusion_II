"""Local normalized association sampling and overflow-aware training proposal.

All kernel/task/context parameters are supplied; no real-domain noise, outlier,
schema or scientific policy is selected here. The analytic guide is the
uncapped auxiliary restriction, NOT an exact capped information function.
Finite NumPy random sampling and first-coordinate derivatives are numerical
interfaces, not new operational or second-derivative certificates.

This is an ALTERNATIVE observation-law proposal, not the frozen real-domain
half-thinning identity kernel. Contamination cannot remove the singular
identity-emission mass of that existing kernel. No real-domain rule is changed.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.autograd.function import once_differentiable

from heterodiff.events.observations import ObservationView, ObservedAnchor
from heterodiff.experiments.hybrid_conditional_training import (
    ObservedConditionalTrainingModel, configuration_batch,
)
from heterodiff.models.two_domain_conditional_training_loss import (
    BASELINE_KIND_BY_METHOD, ConditionalLogitBatch, SamplingLawWeights,
)
from heterodiff.models.two_domain_observation_training_design import (
    ObservationTrainingBatch, ObservationConditionEncoderV1,
    VisibleObservationSchema, tensorize_observations, MAX_BATCH_SIZE, MAX_VISIBLE_ANCHORS,
)
from heterodiff.theory.association_preconditioner import AnalyticAssociationPreconditioner
from heterodiff.theory.configuration_reference import (
    MIN_REFERENCE_CATEGORICAL_PROBABILITY, TransformedEvent,
)
from heterodiff.theory.finite_atomic_overflow_observation import OVERFLOW_OBSERVATION
from heterodiff.processes.learned_hybrid_training_sampler import HybridSamplingContext


class AssociationTrainingError(ValueError):
    pass


def _digest(value):
    def encode_extra(item):
        if type(item) is bytes:
            return {'bytes_hex': item.hex()}
        raise TypeError('unsupported identity value')
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False, default=encode_extra).encode()).hexdigest()


def _valid_sha(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _probabilities(values):
    values = tuple(float(v) for v in values)
    if (not values or any(not math.isfinite(v) or v < 0 for v in values)
            or not math.isclose(math.fsum(values), 1.0, rel_tol=0, abs_tol=5e-12)):
        raise AssociationTrainingError('invalid categorical probabilities')
    if any(0 < v < MIN_REFERENCE_CATEGORICAL_PROBABILITY for v in values):
        raise AssociationTrainingError('categorical probability below supported floor')
    return values


def _bernoulli_probability(value):
    value = float(value)
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise AssociationTrainingError('invalid Bernoulli probability')
    if any(0 < v < MIN_REFERENCE_CATEGORICAL_PROBABILITY for v in (value, 1-value)):
        raise AssociationTrainingError('Bernoulli branch below supported floor')
    return value


@dataclass(frozen=True)
class AssociationSample:
    outcome: object
    kernel_sha256: str
    diagnostics: dict


@dataclass(frozen=True, init=False)
class NormalizedAssociationTrainingKernel:
    """Numerical sampler for the SAME declared likelihood/preconditioner family.

    Outlier is one whole-observation mixture draw, not per-event contamination.
    Counts above M collapse to overflow; they are never truncated/resampled.
    Hidden signal/clutter labels remain diagnostics only, never model inputs.
    """
    guide: AnalyticAssociationPreconditioner
    declaration_id: str
    kernel_sha256: str
    max_retained_coordinates: int
    declared_context: HybridSamplingContext
    static_context: tuple

    def __init__(self, guide, *, declaration_id, declared_context, static_context, max_retained_coordinates=100_000):
        if type(guide) is not AnalyticAssociationPreconditioner:
            raise AssociationTrainingError('exact declared analytic family required')
        if type(declaration_id) is not str or not 1 <= len(declaration_id) <= 256:
            raise AssociationTrainingError('explicit bounded kernel declaration required')
        if type(declared_context) is not HybridSamplingContext:
            raise AssociationTrainingError('exact declared sampling context required')
        if (type(static_context) is not tuple or len(static_context) > 512
                or any(type(v) is not float or not math.isfinite(v) for v in static_context)):
            raise AssociationTrainingError('explicit finite static-context tuple required')
        if type(max_retained_coordinates) is not int or not 1 <= max_retained_coordinates <= 4_000_000:
            raise AssociationTrainingError('retained coordinate bound outside implementation range')
        reference = guide.observation_reference
        if reference.retained_cap * max(reference.type_dimensions.values()) > max_retained_coordinates:
            raise AssociationTrainingError('complete retained support exceeds coordinate bound')
        _bernoulli_probability(guide.contamination_probability)
        for p in guide.detection_probability: _bernoulli_probability(p)
        _probabilities(reference.type_weights.values())
        _probabilities(guide.terminal_clutter.stratum_probability)
        for row in guide.terminal_channel.stratum_probability: _probabilities(row)
        object.__setattr__(self, 'guide', guide)
        object.__setattr__(self, 'declaration_id', declaration_id)
        object.__setattr__(self, 'max_retained_coordinates', max_retained_coordinates)
        object.__setattr__(self, 'declared_context', declared_context)
        object.__setattr__(self, 'static_context', static_context)
        object.__setattr__(self, 'kernel_sha256', _digest({
            'schema': 'normalized-association-training-kernel-v1',
            'declaration': declaration_id, 'guide': guide.parameter_key(),
            'sampling': 'NUMPY_PCG64_NUMERICAL_UNCONDITIONAL_POISSON_THEN_COLLAPSE',
            'coordinate_limit': max_retained_coordinates,
            'context': (declared_context.domain_id, declared_context.task_id, declared_context.context_id),
            'static_context_hex': tuple(v.hex() for v in static_context)}))

    def _atom(self, rng, probabilities, *, source=None, clutter=False, reference=False):
        obs_reference = self.guide.observation_reference
        index = int(rng.choice(len(obs_reference.type_ids), p=np.asarray(probabilities)))
        kind = obs_reference.type_ids[index]
        width = obs_reference.type_dimensions[kind]
        if width == 0:
            return TransformedEvent(kind, ())
        noise = rng.standard_normal(width)
        if reference:
            coordinates = noise
        else:
            fiber = (self.guide.terminal_clutter.fiber_channels[kind] if clutter
                     else self.guide.terminal_channel.fiber_channels[(source.event_type, kind)])
            values = np.empty(0) if clutter else np.asarray(source.coordinates)
            with np.errstate(over='raise', invalid='raise'):
                coordinates = fiber.matrix @ values + fiber.bias + fiber._cholesky @ noise
        if not np.isfinite(coordinates).all():
            raise AssociationTrainingError('Gaussian coordinates not representable; no redraw')
        return TransformedEvent(kind, tuple(float(v) for v in coordinates))

    def sample(self, state, *, rng):
        if type(rng) is not np.random.Generator or type(rng.bit_generator) is not np.random.PCG64:
            raise AssociationTrainingError('explicit NumPy PCG64 generator required')
        row = self.guide.terminal_row(state)
        reference = self.guide.observation_reference
        outlier = float(rng.random()) < self.guide.contamination_probability
        if outlier:
            # NOT reference._base.sample_configuration: that would condition on n<=M.
            count = int(rng.poisson(1.0))
            detected = ()
            clutter_count = None
        else:
            detected = tuple(source for source, p in zip(row.sources, row.detection_probability)
                             if float(rng.random()) < float(p))
            clutter_count = int(rng.poisson(self.guide.terminal_clutter.total_intensity))
            count = len(detected) + clutter_count
        if count > reference.retained_cap:
            outcome = OVERFLOW_OBSERVATION
        else:
            if outlier:
                atoms = [self._atom(rng, tuple(reference.type_weights[k] for k in reference.type_ids),
                                    reference=True) for _ in range(count)]
            else:
                positions = {kind: i for i, kind in enumerate(self.guide.terminal_channel.source_type_ids)}
                atoms = [self._atom(rng, self.guide.terminal_channel.stratum_probability[positions[source.event_type]],
                                    source=source) for source in detected]
                atoms.extend(self._atom(rng, self.guide.terminal_clutter.stratum_probability, clutter=True)
                             for _ in range(clutter_count))
            outcome = reference.canonicalize_retained(atoms)
        return AssociationSample(outcome, self.kernel_sha256, {
            'whole_observation_outlier_branch': outlier,
            'sampled_total_count': count,
            'signal_count': None if outlier else len(detected),
            'clutter_count': clutter_count,
            'overflow': outcome is OVERFLOW_OBSERVATION,
            'coordinate_generation_skipped_by_exact_overflow_collapse': count > reference.retained_cap,
            'observation_truncated_or_redrawn': False,
            'hidden_labels_are_model_inputs': False,
            'real_domain_kernel_adopted': False})

    def sample_outcome(self, state, context, rng):
        """Trajectory callback bound to one explicitly declared m/z context."""
        if type(context) is not HybridSamplingContext or context != self.declared_context:
            raise AssociationTrainingError('sampling context differs from kernel declaration')
        return self.sample(state, rng=rng).outcome

    def log_value_and_gradient(self, reverse_time, state, observation, *, propagated):
        if type(propagated) is not bool:
            raise AssociationTrainingError('explicit guide-versus-terminal role required')
        if (type(reverse_time) is not float or not math.isfinite(reverse_time)
                or not 0 <= reverse_time <= self.guide.process.schedule.horizon):
            raise AssociationTrainingError('reverse time outside the process interval')
        if type(state) is not tuple or any(type(e) is not TransformedEvent for e in state):
            raise AssociationTrainingError('exact source occurrence tuple required')
        # Stable indices preserve multiplicities, including FP32-induced reordering.
        permutation = sorted(range(len(state)), key=lambda i: state[i].model_key())
        row = self.guide.terminal_row(state)
        outcome = self.guide.observation_reference.collapse(observation)
        if propagated:
            value = self.guide.evaluate(reverse_time, row.sources, outcome).log_density
        else:
            value = row.evaluate(outcome).log_density
        if outcome is OVERFLOW_OBSERVATION:
            # Type-only detection and count/Poisson overflow: no coordinate dependence.
            gradient = tuple((0.0,)*len(event.coordinates) for event in row.sources)
        else:
            result = (self.guide.coordinate_gradients(reverse_time, row.sources, outcome)
                      if propagated else row.coordinate_gradients(outcome))
            if not math.isclose(value, result.log_density, rel_tol=0, abs_tol=1e-10):
                raise AssociationTrainingError('value and gradient likelihoods disagree')
            gradient = tuple(tuple(float(v) for v in result.gradients[start:stop])
                             for start, stop in zip(result.coordinate_offsets, result.coordinate_offsets[1:]))
        if not math.isfinite(value) or any(not math.isfinite(v) for g in gradient for v in g):
            raise AssociationTrainingError('nonfinite association value or gradient')
        original_order = [None] * len(state)
        for canonical_index, original_index in enumerate(permutation):
            original_order[original_index] = gradient[canonical_index]
        return value, tuple(original_order)

    def torch_baseline(self, observation, *, propagated):
        """First-coordinate autograd adapter, not a second-order certificate.

        Oracle evaluates the same FP32-represented coordinates passed by the
        neural bridge. Its separate binary64 value/gradient are rounded to
        FP32. No derivative of the rounding map itself is asserted.
        """
        if type(propagated) is not bool:
            raise AssociationTrainingError('explicit guide-versus-terminal role required')
        outcome = self.guide.observation_reference.collapse(observation)
        type_ids = self.guide.process.reference.type_ids
        def baseline(u, state, coordinate_tensors):
            if len(coordinate_tensors) != len(type_ids):
                raise AssociationTrainingError('one coordinate tensor per process type required')
            by_type = {}
            for kind, values in zip(type_ids, coordinate_tensors):
                expected = (sum(e.event_type == kind for e in state),
                            self.guide.process.reference.type_dimensions[kind])
                if (type(values) is not torch.Tensor or values.dtype != torch.float32
                        or values.device.type != 'cpu' or tuple(values.shape) != expected
                        or not bool(torch.isfinite(values).all())):
                    raise AssociationTrainingError('exact finite CPU FP32 coordinate tensors required')
                by_type[kind] = iter(values.detach().tolist())
            represented = tuple(TransformedEvent(e.event_type, tuple(next(by_type[e.event_type]))) for e in state)
            value, gradient = self.log_value_and_gradient(u, represented, outcome, propagated=propagated)
            grouped = tuple(torch.tensor([g for e, g in zip(represented, gradient) if e.event_type == kind],
                                         dtype=torch.float32).reshape(t.shape)
                            for kind, t in zip(type_ids, coordinate_tensors))
            rounded_value = torch.tensor(value, dtype=torch.float32)
            if not bool(torch.isfinite(rounded_value)) or any(not bool(torch.isfinite(g).all()) for g in grouped):
                raise AssociationTrainingError('oracle value or gradient not representable in FP32')
            return _FirstCoordinateOracle.apply(rounded_value, grouped, *coordinate_tensors)
        baseline.kernel_sha256 = self.kernel_sha256
        baseline.propagated = propagated
        return baseline


class _FirstCoordinateOracle(torch.autograd.Function):
    @staticmethod
    def forward(ctx, value, gradients, *coordinates):
        ctx.save_for_backward(*gradients)
        return value.clone()

    @staticmethod
    @once_differentiable
    def backward(ctx, grad_output):
        return (None, None, *(grad_output*g for g in ctx.saved_tensors))


@dataclass(frozen=True)
class AssociationObservationBatch:
    retained: ObservationTrainingBatch
    overflow: torch.Tensor
    kernel_sha256: str

    def to(self, device):
        return AssociationObservationBatch(self.retained.to(device), self.overflow.to(device).clone(), self.kernel_sha256)

    def validate(self, schema, *, forbidden_tensors=()):
        if type(self.retained) is not ObservationTrainingBatch:
            raise AssociationTrainingError('exact retained observation batch required')
        size = self.retained.validate(schema, forbidden_tensors=forbidden_tensors)
        flag = self.overflow
        if (type(flag) is not torch.Tensor or flag.dtype != torch.bool or flag.shape != (size,)
                or flag.device != self.retained.anchor_features.device or flag.layout != torch.strided):
            raise AssociationTrainingError('one explicit Boolean overflow flag per row required')
        forbidden = {t.untyped_storage().data_ptr() for t in forbidden_tensors
                     if type(t) is torch.Tensor and t.numel()}
        if flag.numel() and flag.untyped_storage().data_ptr() in forbidden:
            raise AssociationTrainingError('overflow flag aliases latent/time state')
        if not _valid_sha(self.kernel_sha256):
            raise AssociationTrainingError('kernel identity required')
        if bool((self.retained.global_features[:,1:3] != 0).any()):
            raise AssociationTrainingError('association anchor count is not latent cardinality')
        for index in torch.nonzero(flag).flatten().tolist():
            if (bool((self.retained.batch_indices == index).any())
                    or bool((self.retained.global_features[index,:3] != 0).any())):
                raise AssociationTrainingError('overflow requires an empty unknown-count placeholder')
        return size


def tensorize_association_observations(kernel, outcomes, *, schema, task_ids, static_contexts, device='cpu'):
    """Chart coordinates stay marks, not fabricated nonnegative physical times."""
    if type(kernel) is not NormalizedAssociationTrainingKernel or type(schema) is not VisibleObservationSchema:
        raise AssociationTrainingError('exact declared kernel and visible schema required')
    if (type(outcomes) is not tuple or not 1 <= len(outcomes) <= MAX_BATCH_SIZE
            or type(task_ids) is not tuple or type(static_contexts) is not tuple
            or len(task_ids) != len(outcomes) or len(static_contexts) != len(outcomes)):
        raise AssociationTrainingError('bounded aligned tuples of outcomes/task/context required')
    reference = kernel.guide.observation_reference
    if (schema.domain_id != kernel.declared_context.domain_id
            or any(type(task) is not str or task.encode('utf-8') != kernel.declared_context.task_id for task in task_ids)):
        raise AssociationTrainingError('visible domain/task differs from declared sampling context')
    for context in static_contexts:
        if (type(context) is not tuple or any(type(v) is not float or not math.isfinite(v) for v in context)
                or tuple(v.hex() for v in context) != tuple(v.hex() for v in kernel.static_context)):
            raise AssociationTrainingError('visible static context differs from kernel declaration')
    if schema.event_type_ids != reference.type_ids:
        raise AssociationTrainingError('visible observation types differ from the kernel')
    expected_marks = {f'chart_{kind}': width for kind, width in reference.type_dimensions.items() if width}
    if {name: len(scales) for name, scales in schema.mark_fields} != expected_marks:
        raise AssociationTrainingError('visible chart mark widths differ from the kernel')
    collapsed = tuple(reference.collapse(observation) for observation in outcomes)
    if sum(len(a) for a in collapsed if a is not OVERFLOW_OBSERVATION) > MAX_VISIBLE_ANCHORS:
        raise AssociationTrainingError('visible anchors exceed implementation bound; no truncation')
    views, flags = [], []
    for outcome in collapsed:
        flag = outcome is OVERFLOW_OBSERVATION
        anchors = () if flag else tuple(ObservedAnchor(event_type=e.event_type,
            marks={f'chart_{e.event_type}': e.coordinates} if e.coordinates else {}) for e in outcome)
        views.append(ObservationView(anchors, cardinality=None))
        flags.append(flag)
    raw = tensorize_observations(tuple(views), task_ids, static_contexts, schema, device=device)
    result = AssociationObservationBatch(raw, torch.tensor(flags, dtype=torch.bool, device=device), kernel.kernel_sha256)
    result.validate(schema)
    return result


class OverflowObservationEncoder(nn.Module):
    """Explicit retained64+overflow1 ->64 proposal, with task/context retained."""
    def __init__(self, retained_encoder, *, initialization_seed):
        super().__init__()
        if type(retained_encoder) is not ObservationConditionEncoderV1:
            raise AssociationTrainingError('exact retained encoder required')
        if type(initialization_seed) is not int or not 0 <= initialization_seed < 2**64:
            raise AssociationTrainingError('explicit uint64 wrapper seed required')
        self.retained_encoder = deepcopy(retained_encoder)
        self.schema = retained_encoder.schema
        generator = torch.Generator().manual_seed(initialization_seed)
        self.weight = nn.Parameter(torch.empty(64,65,dtype=torch.float32))
        self.bias = nn.Parameter(torch.zeros(64,dtype=torch.float32))
        with torch.no_grad():
            self.weight.uniform_(-1/math.sqrt(65), 1/math.sqrt(65), generator=generator)
        self.to(retained_encoder.anchor1.weight.device)

    def forward(self, batch):
        if type(batch) is not AssociationObservationBatch:
            raise AssociationTrainingError('overflow-aware batch required')
        batch.validate(self.schema)
        retained = self.retained_encoder(batch.retained)
        # Overflow placeholders have no anchors or count, but m/z remain valid inputs.
        value = torch.cat((retained, batch.overflow.to(dtype=torch.float32)[:,None]), 1)
        result = torch.tanh(F.linear(value, self.weight, self.bias))
        if not bool(torch.isfinite(result).all()):
            raise AssociationTrainingError('nonfinite overflow-aware encoding')
        return result

    @property
    def parameter_count(self):
        return sum(p.numel() for p in self.parameters())


@dataclass(frozen=True)
class AssociationLogitBatch:
    states: tuple
    reverse_times: tuple
    observation: AssociationObservationBatch
    baseline_log_values: torch.Tensor
    baseline_kind: str


class AssociationConditionalTrainingModel(nn.Module):
    """Separate additive wrapper; original retained-only contracts stay intact."""
    def __init__(self, retained_model, *, wrapper_seed, kernel_sha256):
        super().__init__()
        if type(retained_model) is not ObservedConditionalTrainingModel:
            raise AssociationTrainingError('exact retained-only model proposal required')
        if type(wrapper_seed) is not int or not 0 <= wrapper_seed < 2**64-1:
            raise AssociationTrainingError('wrapper seed must allow one distinct nuisance seed')
        if not _valid_sha(kernel_sha256):
            raise AssociationTrainingError('model requires an explicit kernel identity')
        self.conditioner = deepcopy(retained_model.conditioner)
        self.encoder = OverflowObservationEncoder(retained_model.encoder, initialization_seed=wrapper_seed)
        self.nuisance = deepcopy(retained_model.nuisance)
        self.nuisance.encoder = OverflowObservationEncoder(retained_model.nuisance.encoder,
                                                            initialization_seed=wrapper_seed+1)
        self.method_id = retained_model.method_id
        self.kernel_sha256 = kernel_sha256

    @property
    def execution_device(self):
        return self.conditioner.execution_device

    def residual(self, states, reverse_times, observation):
        if type(observation) is not AssociationObservationBatch or observation.kernel_sha256 != self.kernel_sha256:
            raise AssociationTrainingError('observation kernel differs from model declaration')
        encoded = self.encoder(observation)
        batch = configuration_batch(self.conditioner.backbone, states, reverse_times, encoded)
        observation.validate(self.encoder.schema, forbidden_tensors=(batch.forward_time,*batch.coordinates))
        zero = torch.zeros(len(states),dtype=torch.float32,device=self.execution_device)
        return self.conditioner.gated_residual(ConditionalLogitBatch(
            batch,None,zero,BASELINE_KIND_BY_METHOD[self.method_id]))

    def forward(self, batch):
        if type(batch) is not AssociationLogitBatch:
            raise AssociationTrainingError('exact association logit batch required')
        baseline = batch.baseline_log_values
        if (batch.baseline_kind != BASELINE_KIND_BY_METHOD[self.method_id]
                or type(baseline) is not torch.Tensor or baseline.requires_grad
                or baseline.shape != (len(batch.states),) or baseline.dtype != torch.float32
                or baseline.device != self.execution_device or not bool(torch.isfinite(baseline).all())):
            raise AssociationTrainingError('fixed finite method-bound baseline required')
        value = baseline + self.residual(batch.states,batch.reverse_times,batch.observation) + self.nuisance(batch.observation)
        if not bool(torch.isfinite(value).all()):
            raise AssociationTrainingError('nonfinite association logits')
        return value

    def parameter_summary(self):
        return {'design_id': 'ASSOCIATION_OVERFLOW_WRAPPER_PROPOSAL_V1',
                'additional_parameters_over_retained_model': 8448,
                'all_unique_parameters': sum(p.numel() for p in self.parameters()),
                'nuisance_excluded_from_physical_potential': True,
                'production_configuration_adopted': False}


def association_joint_product_loss(model, joint, product, weights):
    if type(model) is not AssociationConditionalTrainingModel or type(weights) is not SamplingLawWeights:
        raise AssociationTrainingError('exact association model and explicit sampling weights required')
    if type(joint) is not AssociationLogitBatch or type(product) is not AssociationLogitBatch:
        raise AssociationTrainingError('exact association paired batches required')
    if joint.states != product.states or joint.reverse_times != product.reverse_times:
        raise AssociationTrainingError('paired latent and time must match')
    if (joint.observation.kernel_sha256 != product.observation.kernel_sha256
            or joint.observation.retained.task_context_sha256s != product.observation.retained.task_context_sha256s):
        raise AssociationTrainingError('paired kernel/task/context must match')
    for field in ('task_features','static_context_features'):
        if not torch.equal(getattr(joint.observation.retained,field),getattr(product.observation.retained,field)):
            raise AssociationTrainingError('paired task/context projections differ')
    j,p = model(joint),model(product)
    if j.shape != p.shape:
        raise AssociationTrainingError('paired class sizes differ')
    wj,wp = weights.tensors(size=j.numel(),device=model.execution_device)
    result = 0.5*((wj*F.softplus(-j)).mean()+(wp*F.softplus(p)).mean())
    if not bool(torch.isfinite(result)):
        raise AssociationTrainingError('nonfinite paired risk')
    return result
