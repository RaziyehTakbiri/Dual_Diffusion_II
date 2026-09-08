"""Review-pending visible-only encoder, nuisance, and synthetic condition law.

The raw feature schema is explicit and rejects unknown fields. No target-aligned
ObservationPattern, latent configuration, or diffusion clock is an encoder input.
Architectures are concrete proposals, not adopted B06 successors. Finite-machine
synthetic time draws are not claimed to realize a continuous full-support law.
"""
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math

import torch
from torch import nn

from heterodiff.events.observations import ObservationView, ObservedAnchor
from heterodiff.experiments import two_domain_baseline_registry as b06
from heterodiff.models.two_domain_conditional_training_loss import SamplingLawWeights

DESIGN_ID = 'TWO_DOMAIN_VISIBLE_DEEPSETS_AND_NUISANCE_PROPOSAL_V1'
CONTINUOUS_TIME_LAW_ID = 'PROPOSED_UNIFORM_OPEN_REVERSE_INTERVAL_V1'
SYNTHETIC_LAW_ID = 'SYNTHETIC_UNIFORM_TASK_CONTEXT_MIDPOINT_TIME_GRID_V1'
MAX_BATCH_SIZE = 128
MAX_VISIBLE_ANCHORS = 16384


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _labels(values, name, maximum=512):
    if (type(values) is not tuple or len(values) > maximum
            or any(type(value) is not str or not value or len(value) > 128 for value in values)
            or len(set(values)) != len(values)):
        raise ValueError(name + ' requires an explicit unique bounded string tuple')


def _scales(values, name):
    if type(values) is not tuple or any(type(value) is not float or not math.isfinite(value) or value <= 0 for value in values):
        raise ValueError(name + ' requires exact positive finite float scales')


@dataclass(frozen=True)
class VisibleObservationSchema:
    domain_id: str
    event_type_ids: tuple
    mark_fields: tuple
    task_ids: tuple
    static_context_names: tuple
    static_context_scales: tuple
    physical_time_scale: float = 1.0

    def __post_init__(self):
        if type(self.domain_id) is not str or self.domain_id not in b06.DOMAIN_IDS:
            raise ValueError('domain must be an existing two-domain registry identity')
        if (type(self.event_type_ids) is not tuple or not 1 <= len(self.event_type_ids) <= 128
                or any(type(item) is not int or item < 0 for item in self.event_type_ids)
                or self.event_type_ids != tuple(sorted(set(self.event_type_ids)))):
            raise ValueError('event types must be explicitly sorted unique nonnegative integers')
        if type(self.mark_fields) is not tuple or any(type(row) is not tuple or len(row) != 2 for row in self.mark_fields):
            raise ValueError('mark_fields must be (name, scale_tuple) rows')
        _labels(tuple(row[0] for row in self.mark_fields), 'mark names')
        for name, scales in self.mark_fields:
            _scales(scales, name)
            if not scales:
                raise ValueError('each mark must have a positive declared width')
        if self.mark_dimension > 512:
            raise ValueError('declared visible mark width exceeds implementation bound')
        _labels(self.task_ids, 'task IDs', 32)
        if not self.task_ids:
            raise ValueError('at least one explicit task is required')
        _labels(self.static_context_names, 'static context names', 128)
        _scales(self.static_context_scales, 'static context')
        if len(self.static_context_names) != len(self.static_context_scales):
            raise ValueError('static context names/scales differ')
        forbidden = {'latent', 'latent_state', 'process_time', 'direct_time', 'reverse_time'}
        if any(name.lower() in forbidden for name in self.static_context_names):
            raise ValueError('static context cannot explicitly name a latent state or diffusion clock')
        _scales((self.physical_time_scale,), 'physical observation time')

    @property
    def mark_dimension(self):
        return sum(len(row[1]) for row in self.mark_fields)

    @property
    def anchor_dimension(self):
        return 3 + len(self.event_type_ids) + 2 * self.mark_dimension

    @property
    def global_dimension(self):
        return 3 + len(self.task_ids) + len(self.static_context_names)

    @property
    def schema_sha256(self):
        self.__post_init__()
        return _digest({'design_id': DESIGN_ID, **vars(self)})


def _tensor(value, name, *, device, ndim):
    if (type(value) is not torch.Tensor or value.dtype != torch.float32 or value.device != device
            or value.layout != torch.strided or value.ndim != ndim or value.requires_grad
            or not bool(torch.isfinite(value).all()) or not bool((value.abs() <= 1).all())):
        raise ValueError(name + ' must be detached bounded finite dense FP32 on one device')


@dataclass(frozen=True)
class ObservationTrainingBatch:
    schema_sha256: str
    anchor_features: torch.Tensor
    batch_indices: torch.Tensor
    global_features: torch.Tensor
    task_features: torch.Tensor
    static_context_features: torch.Tensor
    task_context_sha256s: tuple

    def validate(self, schema, *, forbidden_tensors=()):
        if type(schema) is not VisibleObservationSchema or self.schema_sha256 != schema.schema_sha256:
            raise ValueError('visible observation schema binding mismatch')
        if type(self.anchor_features) is not torch.Tensor:
            raise ValueError('visible anchor features must be an exact tensor')
        device = self.anchor_features.device
        for name in ('anchor_features', 'global_features', 'task_features', 'static_context_features'):
            _tensor(getattr(self, name), name, device=device, ndim=2)
        size = self.global_features.shape[0]
        if (type(self.task_context_sha256s) is not tuple or len(self.task_context_sha256s) != size
                or any(type(item) is not str or len(item) != 64
                       or any(char not in '0123456789abcdef' for char in item)
                       for item in self.task_context_sha256s)):
            raise ValueError('exact task/context identities required; float features are not identities')
        if not 1 <= size <= MAX_BATCH_SIZE or self.anchor_features.shape[0] > MAX_VISIBLE_ANCHORS:
            raise ValueError('observation batch exceeds implementation bound; no truncation')
        if (self.anchor_features.shape[1] != schema.anchor_dimension
                or self.global_features.shape[1] != schema.global_dimension
                or tuple(self.task_features.shape) != (size, len(schema.task_ids))
                or tuple(self.static_context_features.shape) != (size, len(schema.static_context_names))):
            raise ValueError('visible observation feature dimensions differ from schema')
        owners = self.batch_indices
        if (type(owners) is not torch.Tensor or owners.dtype != torch.int64 or owners.device != device
                or owners.layout != torch.strided or tuple(owners.shape) != (len(self.anchor_features),)
                or bool(((owners < 0) | (owners >= size)).any())):
            raise ValueError('visible anchor owners must index the observation batch')
        if not torch.equal(self.global_features[:, 3:], torch.cat((self.task_features, self.static_context_features), dim=1)):
            raise ValueError('task/static-context feature copies differ')
        if not bool(((self.task_features == 0) | (self.task_features == 1)).all()) or not bool((self.task_features.sum(1) == 1).all()):
            raise ValueError('task features must be exact one-hot rows')
        forbidden = {value.untyped_storage().data_ptr() for value in forbidden_tensors
                     if type(value) is torch.Tensor and value.numel()}
        if any(value.numel() and value.untyped_storage().data_ptr() in forbidden for value in
               (self.anchor_features, self.global_features, self.task_features, self.static_context_features)):
            raise ValueError('visible observation input aliases latent/time state')
        return size

    def to(self, device):
        return ObservationTrainingBatch(self.schema_sha256, *(
            getattr(self, name).to(device=device).clone()
            for name in ('anchor_features', 'batch_indices', 'global_features', 'task_features', 'static_context_features')),
            self.task_context_sha256s)


def _bounded(value, scale):
    return (2 / math.pi) * math.atan2(value, scale)


def tensorize_observations(views, task_ids, static_contexts, schema, *, device='cpu'):
    """Preserve visible occurrences/masks, never target alignment or hidden count."""
    if type(schema) is not VisibleObservationSchema:
        raise TypeError('exact VisibleObservationSchema required')
    schema.__post_init__()
    if (type(views) is not tuple or not 1 <= len(views) <= MAX_BATCH_SIZE
            or any(type(view) is not ObservationView for view in views)
            or type(task_ids) is not tuple or type(static_contexts) is not tuple
            or len(task_ids) != len(views) or len(static_contexts) != len(views)):
        raise ValueError('aligned explicit ObservationView/task/static-context tuples required')
    if sum(len(view.anchors) for view in views) > MAX_VISIBLE_ANCHORS:
        raise ValueError('visible anchors exceed implementation bound; no truncation')
    anchors, owners, globals_, tasks, contexts, condition_ids = [], [], [], [], [], []
    field_names = {name for name, _ in schema.mark_fields}
    for ordinal, (view, task, context) in enumerate(zip(views, task_ids, static_contexts)):
        if task not in schema.task_ids or type(task) is not str:
            raise ValueError('task is not in the explicitly declared law/schema')
        if (type(context) is not tuple or len(context) != len(schema.static_context_names)
                or any(type(value) is not float or not math.isfinite(value) for value in context)):
            raise ValueError('static context must contain declared finite exact floats')
        if view.cardinality is not None and view.cardinality > b06.MAXIMUM_EVENTS_BY_DOMAIN[schema.domain_id]:
            raise ValueError('observed cardinality exceeds domain cap')
        if any(type(anchor) is not ObservedAnchor for anchor in view.anchors):
            raise TypeError('exact model-visible anchors required')
        task_row = [float(task == item) for item in schema.task_ids]
        context_row = [_bounded(value, scale) for value, scale in zip(context, schema.static_context_scales)]
        condition_ids.append(_digest({'schema': schema.schema_sha256, 'task_id': task,
                                     'static_context_hex': [value.hex() for value in context]}))
        n = len(view.anchors)
        globals_.append([n / (1 + n), float(view.cardinality is not None),
                         0.0 if view.cardinality is None else view.cardinality / (1 + view.cardinality)]
                        + task_row + context_row)
        tasks.append(task_row)
        contexts.append(context_row)
        for anchor in view.anchors:
            if anchor.is_empty or set(anchor.marks) - field_names:
                raise ValueError('empty hidden anchor or undeclared visible mark')
            if anchor.event_type is not None and anchor.event_type not in schema.event_type_ids:
                raise ValueError('visible type is outside the declared vocabulary')
            row = [float(anchor.event_time is not None),
                   0.0 if anchor.event_time is None else _bounded(anchor.event_time, schema.physical_time_scale),
                   float(anchor.event_type is not None)]
            row.extend(float(anchor.event_type == item) for item in schema.event_type_ids)
            for name, scales in schema.mark_fields:
                observed = name in anchor.marks
                values = anchor.marks.get(name, (0.0,) * len(scales))
                if len(values) != len(scales):
                    raise ValueError('visible mark width differs from declared schema')
                row.extend([float(observed)] * len(scales))
                row.extend([_bounded(value, scale) if observed else 0.0 for value, scale in zip(values, scales)])
            anchors.append(row)
            owners.append(ordinal)
    result = ObservationTrainingBatch(
        schema.schema_sha256, torch.tensor(anchors, dtype=torch.float32, device=device).reshape(-1, schema.anchor_dimension),
        torch.tensor(owners, dtype=torch.int64, device=device),
        torch.tensor(globals_, dtype=torch.float32, device=device),
        torch.tensor(tasks, dtype=torch.float32, device=device),
        torch.tensor(contexts, dtype=torch.float32, device=device).reshape(len(views), -1),
        tuple(condition_ids))
    result.validate(schema)
    return result


class _Dense(nn.Module):
    def __init__(self, input_width, output_width, generator):
        super().__init__()
        self.weight = nn.Parameter(torch.empty((output_width, input_width), dtype=torch.float32))
        self.bias = nn.Parameter(torch.zeros(output_width, dtype=torch.float32))
        with torch.no_grad():
            self.weight.uniform_(-1 / math.sqrt(input_width), 1 / math.sqrt(input_width), generator=generator)

    def forward(self, value):
        return torch.nn.functional.linear(value, self.weight, self.bias)


def _generator(seed):
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError('initialization seed must be explicit nonnegative uint64 integer')
    return torch.Generator(device='cpu').manual_seed(seed)


class ObservationConditionEncoderV1(nn.Module):
    """Trainable bounded DeepSets; raw inputs detached, parameter gradients live."""
    def __init__(self, schema, *, initialization_seed=0, device='cpu'):
        super().__init__()
        if type(schema) is not VisibleObservationSchema:
            raise TypeError('exact VisibleObservationSchema required')
        schema.__post_init__()
        self.schema = schema
        generator = _generator(initialization_seed)
        self.anchor1 = _Dense(schema.anchor_dimension, 64, generator)
        self.anchor2 = _Dense(64, 64, generator)
        self.readout1 = _Dense(64 + schema.global_dimension, 64, generator)
        self.readout2 = _Dense(64, 64, generator)
        self.to(device=device)

    def forward(self, batch):
        if type(batch) is not ObservationTrainingBatch:
            raise TypeError('exact raw ObservationTrainingBatch required')
        size = batch.validate(self.schema)
        if batch.anchor_features.device != self.anchor1.weight.device:
            raise ValueError('encoder and observation batch devices differ')
        embeddings = torch.tanh(self.anchor2(torch.tanh(self.anchor1(batch.anchor_features))))
        rows = []
        for index in range(size):
            selected = embeddings[batch.batch_indices == index]
            rows.append(selected.sum(dim=0) / (1 + selected.shape[0]))
        pooled = torch.stack(rows)
        output = torch.tanh(self.readout2(torch.tanh(self.readout1(torch.cat((pooled, batch.global_features), 1)))))
        if not bool(torch.isfinite(output).all()) or not bool((output.abs() <= 1).all()):
            raise ArithmeticError('observation encoder is not finite and bounded')
        return output

    @property
    def parameter_count(self):
        return sum(value.numel() for value in self.parameters())


class ObservationOnlyNuisanceV1(nn.Module):
    """Independent trainable observation encoder +64→32→1; no clock/state API."""
    def __init__(self, schema, *, initialization_seed=1, device='cpu'):
        super().__init__()
        self.encoder = ObservationConditionEncoderV1(schema, initialization_seed=initialization_seed)
        generator = _generator(initialization_seed)
        self.hidden = _Dense(64, 32, generator)
        self.output = _Dense(32, 1, generator)
        self.to(device=device)

    def forward(self, batch):
        result = self.output(torch.tanh(self.hidden(self.encoder(batch)))).squeeze(-1)
        if not bool(torch.isfinite(result).all()):
            raise ArithmeticError('observation nuisance is nonfinite')
        return result

    @property
    def parameter_count(self):
        return sum(value.numel() for value in self.parameters())


def training_design_parameter_counts(schema):
    if type(schema) is not VisibleObservationSchema:
        raise TypeError('exact visible schema required')
    schema.__post_init__()
    encoder = 64 * (schema.anchor_dimension + 64 + schema.global_dimension) + 8448
    head = 64 * 32 + 32 + 32 + 1
    historical = b06.primary_parameter_count(schema.domain_id)
    return {'design_id': DESIGN_ID, 'schema_sha256': schema.schema_sha256,
            'condition_encoder': encoder, 'nuisance_encoder': encoder, 'nuisance_head': head,
            'additional_unique_trainable_parameters': 2 * encoder + head,
            'historical_base_and_conditioner': historical,
            'proposed_total_unique_parameters': historical['total'] + 2 * encoder + head,
            'proposed_trainable_parameters': historical['trainable_conditioner'] + 2 * encoder + head,
            'counts_require_exact_disjoint_graph_and_historical_backbone': True,
            'b06_successor_adopted': False, 'production_schema_admitted': False}


@dataclass(frozen=True)
class SyntheticConditionDraw:
    task_id: str
    static_context: tuple
    reverse_time: Fraction
    direct_time: Fraction


@dataclass(frozen=True, init=False)
class SyntheticTrainingLawV1:
    """Uniform finite task/context/midpoint law; separate proposed continuous q."""
    schema: VisibleObservationSchema
    static_context_roster: tuple
    horizon: Fraction
    time_grid_bits: int
    law_id: str
    def __init__(self, schema, static_context_roster, horizon, *, time_grid_bits=16):
        if type(schema) is not VisibleObservationSchema:
            raise TypeError('exact visible schema required')
        schema.__post_init__()
        if type(horizon) is not Fraction or horizon <= 0:
            raise ValueError('exact positive Fraction horizon required')
        if type(time_grid_bits) is not int or not 1 <= time_grid_bits <= 24:
            raise ValueError('time grid bits must be an integer in 1..24')
        if (type(static_context_roster) is not tuple or not 1 <= len(static_context_roster) <= 128
                or len(set(static_context_roster)) != len(static_context_roster)):
            raise ValueError('explicit unique synthetic static-context roster required')
        for context in static_context_roster:
            if (type(context) is not tuple or len(context) != len(schema.static_context_names)
                    or any(type(value) is not float or not math.isfinite(value) for value in context)):
                raise ValueError('synthetic contexts must agree with visible schema')
        object.__setattr__(self, 'schema', schema)
        object.__setattr__(self, 'static_context_roster', static_context_roster)
        object.__setattr__(self, 'horizon', horizon)
        object.__setattr__(self, 'time_grid_bits', time_grid_bits)
        object.__setattr__(self, 'law_id', SYNTHETIC_LAW_ID + ':' + _digest({
            'schema': schema.schema_sha256, 'contexts': static_context_roster,
            'horizon': str(horizon), 'grid_bits': time_grid_bits}))

    def proposed_continuous_time_density(self, reverse_time):
        if type(reverse_time) is not Fraction:
            raise TypeError('exact Fraction time required')
        return 1 / self.horizon if 0 < reverse_time < self.horizon else Fraction(0)

    def draw(self, size, *, generator):
        if type(size) is not int or not 1 <= size <= MAX_BATCH_SIZE:
            raise ValueError('bounded positive condition draw count required')
        if type(generator) is not torch.Generator or generator.device.type != 'cpu':
            raise ValueError('explicit CPU generator required for synthetic condition draws')
        tasks = torch.randint(len(self.schema.task_ids), (size,), generator=generator).tolist()
        contexts = torch.randint(len(self.static_context_roster), (size,), generator=generator).tolist()
        cells = torch.randint(2**self.time_grid_bits, (size,), generator=generator).tolist()
        result = []
        for task, context, cell in zip(tasks, contexts, cells):
            reverse_time = self.horizon * Fraction(2 * cell + 1, 2**(self.time_grid_bits + 1))
            result.append(SyntheticConditionDraw(self.schema.task_ids[task], self.static_context_roster[context],
                                                 reverse_time, self.horizon - reverse_time))
        return tuple(result)

    def equal_prior_weights(self, size):
        return SamplingLawWeights.declared(law_id=self.law_id, size=size)

    def description(self):
        return {'design_id': DESIGN_ID, 'synthetic_law_id': self.law_id,
                'task_context_law': 'DECLARED_SYNTHETIC_CARTESIAN_PRODUCT_ALL_PAIRS_SUPPLIED_AS_VALID',
                'task_probability': str(Fraction(1, len(self.schema.task_ids))),
                'context_probability': str(Fraction(1, len(self.static_context_roster))),
                'synthetic_time_grid_cell_probability': str(Fraction(1, 2**self.time_grid_bits)),
                'proposed_continuous_time_law_id': CONTINUOUS_TIME_LAW_ID,
                'proposed_q_density_on_entire_open_interval': str(1 / self.horizon),
                'proposed_q_has_full_open_interval_support': True,
                'finite_midpoint_draws_exactly_sample_continuous_q': False,
                'continuous_to_discrete_rn_correction_claimed': False,
                'synthetic_unit_weights_apply_only_to_declared_finite_law': True,
                'shared_task_context_and_time_required_for_both_classes': True,
                'two_independent_same_context_base_trajectories_required': True,
                'cross_context_batch_permutation_allowed': False,
                'proposed_initial_law': 'PROCESS_OWNED_PI_N_FOR_EACH_INDEPENDENT_BASE_BRANCH',
                'initial_law_or_base_trajectories_generated_by_this_component': False,
                'production_task_context_roster_selected': False,
                'production_law_or_design_adopted': False}
