"""Lossless atomic-time counting-grid arrays for event configurations.

This module is a representation bridge.  It does not define a probability
law, a diffusion process, a neural architecture, an objective, or an
empirical result.  The grid axes are the atoms of an atomic ``TimeReference``
and the event types of a ``FeatureSchema``.  A third, dynamically sized axis
contains occurrence *serialization slots* inside each time/type cell.

``cell_counts`` is the semantic cell cardinality.  No binary projection is
performed: every occurrence is retained, including repeated identical atoms
in ``FINITE_COUNTING`` schemas.  Slots are canonicalized from event state and
observation masks when the object is constructed, so an aligned permutation
of input slots cannot change the represented model state.  Optional event
identifiers and dataset identifiers remain non-probabilistic provenance
sidecars.

The aligned target arrays contain hidden target identity and cardinality.  Do
not pass them directly to a conditioning network.  Use :meth:`to_model_view`
to remove unobserved targets and unobserved cardinality.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from types import MappingProxyType
from typing import Hashable, Mapping, Optional, Tuple

import numpy as np

from heterodiff.events.configuration import Event, EventConfiguration
from heterodiff.events.observations import (
    EventObservation,
    ObservationPattern,
    ObservationView,
)
from heterodiff.events.schema import (
    ContinuousField,
    EventTypeSchema,
    FeatureSchema,
    TimeMeasureKind,
    TimeReference,
)


FloatArrayMap = Mapping[str, np.ndarray]
BoolArrayMap = Mapping[str, np.ndarray]
EventIdGrid = Tuple[Tuple[Tuple[Optional[Hashable], ...], ...], ...]


def _snapshot_schema(value: object) -> FeatureSchema:
    """Validate exact schema node types and return a detached immutable copy.

    Frozen dataclasses prevent ordinary assignment but do not make an accepted
    subclass trustworthy: a subclass can expose stateful attributes or retain
    a mutable interpretation behind an inherited interface.  The tensor is a
    persistence/model-state boundary, so it rejects every subclass in the
    schema tree and reconstructs exact base instances.  Later mutation of the
    source configuration's object graph therefore cannot reinterpret frozen
    arrays.
    """

    if type(value) is not FeatureSchema:
        raise TypeError("schema must be an exact FeatureSchema instance")
    schema = value
    if type(schema.time_reference) is not TimeReference:
        raise TypeError("time_reference must be an exact TimeReference instance")
    for event_type in schema.event_types:
        if type(event_type) is not EventTypeSchema:
            raise TypeError(
                "event_types must contain only exact EventTypeSchema instances"
            )
        for field in event_type.fields:
            if type(field) is not ContinuousField:
                raise TypeError(
                    "event-type fields must contain only exact ContinuousField "
                    "instances"
                )

    assert schema.time_reference is not None
    time_reference = TimeReference(
        kind=schema.time_reference.kind,
        atoms=schema.time_reference.atoms,
        atom_weights=schema.time_reference.atom_weights,
        continuous_weight=schema.time_reference.continuous_weight,
    )
    event_types = tuple(
        EventTypeSchema(
            type_id=event_type.type_id,
            name=event_type.name,
            fields=tuple(
                ContinuousField(
                    name=field.name,
                    dimension=field.dimension,
                    support=field.support,
                    lower=field.lower,
                    upper=field.upper,
                    unit=field.unit,
                )
                for field in event_type.fields
            ),
        )
        for event_type in schema.event_types
    )
    return FeatureSchema(
        event_types=event_types,
        horizon=schema.horizon,
        time_measure=schema.time_measure,
        time_reference=time_reference,
        allow_simultaneous=schema.allow_simultaneous,
        version=schema.version,
        multiplicity_mode=schema.multiplicity_mode,
    )


def _field_dimensions(schema: FeatureSchema) -> Mapping[str, int]:
    dimensions = {}
    for event_type in schema.event_types:
        for field in event_type.fields:
            dimensions[field.name] = max(
                dimensions.get(field.name, 0), field.dimension
            )
    return MappingProxyType(dict(sorted(dimensions.items())))


def _slot_capacity(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("max_occurrences_per_cell must be an integer")
    result = int(value)
    if result < 0:
        raise ValueError("max_occurrences_per_cell must be nonnegative")
    return result


def _immutable_array(
    value: object,
    *,
    name: str,
    dtype: np.dtype,
    shape: Tuple[int, ...],
) -> np.ndarray:
    if not isinstance(value, np.ndarray):
        raise TypeError("{} must be a NumPy array".format(name))
    if value.dtype != dtype:
        raise TypeError(
            "{} must have dtype {}; got {}".format(name, dtype.name, value.dtype)
        )
    if value.shape != shape:
        raise ValueError("{} has shape {}; expected {}".format(name, value.shape, shape))
    contiguous = np.array(value, dtype=dtype, copy=True, order="C")
    if dtype.kind == "f":
        if np.any(~np.isfinite(contiguous)):
            raise ValueError("{} must contain only finite values".format(name))
        contiguous[contiguous == 0.0] = 0.0
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=dtype).reshape(shape)


def _immutable_array_mapping(
    value: object,
    *,
    name: str,
    dtype: np.dtype,
    grid_shape: Tuple[int, int, int],
    dimensions: Mapping[str, int],
) -> Mapping[str, np.ndarray]:
    if not isinstance(value, Mapping):
        raise TypeError("{} must be a mapping from field names to arrays".format(name))
    if any(not isinstance(field_name, str) for field_name in value):
        raise TypeError("{} field keys must be strings".format(name))
    expected_names = set(dimensions)
    actual_names = set(value)
    if actual_names != expected_names:
        missing = sorted(expected_names - actual_names)
        extra = sorted(actual_names - expected_names)
        details = []
        if missing:
            details.append("missing {}".format(", ".join(missing)))
        if extra:
            details.append("unexpected {}".format(", ".join(extra)))
        raise ValueError("{} field keys are invalid: {}".format(name, "; ".join(details)))
    arrays = {
        field_name: _immutable_array(
            value[field_name],
            name="{}[{!r}]".format(name, field_name),
            dtype=dtype,
            shape=grid_shape + (dimension,),
        )
        for field_name, dimension in dimensions.items()
    }
    return MappingProxyType(arrays)


def _freeze_event_ids(
    value: object,
    *,
    number_of_atoms: int,
    number_of_types: int,
    slot_capacity: int,
) -> EventIdGrid:
    if isinstance(value, (str, bytes)):
        raise TypeError("event_ids must be a three-dimensional sequence")
    try:
        atom_rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError("event_ids must be a three-dimensional sequence") from exc
    if len(atom_rows) != number_of_atoms:
        raise ValueError(
            "event_ids has {} time rows; expected {}".format(
                len(atom_rows), number_of_atoms
            )
        )
    frozen_rows = []
    for atom_index, row in enumerate(atom_rows):
        if isinstance(row, (str, bytes)):
            raise TypeError("event_ids rows must be sequences")
        try:
            type_rows = tuple(row)
        except TypeError as exc:
            raise TypeError("event_ids rows must be sequences") from exc
        if len(type_rows) != number_of_types:
            raise ValueError(
                "event_ids time row {} has {} type rows; expected {}".format(
                    atom_index, len(type_rows), number_of_types
                )
            )
        frozen_type_rows = []
        for type_index, slots in enumerate(type_rows):
            if isinstance(slots, (str, bytes)):
                raise TypeError("event_ids cell values must be sequences")
            try:
                slot_values = tuple(slots)
            except TypeError as exc:
                raise TypeError("event_ids cell values must be sequences") from exc
            if len(slot_values) != slot_capacity:
                raise ValueError(
                    "event_ids cell ({}, {}) has {} slots; expected {}".format(
                        atom_index, type_index, len(slot_values), slot_capacity
                    )
                )
            for event_id in slot_values:
                if event_id is not None:
                    try:
                        hash(event_id)
                    except TypeError as exc:
                        raise TypeError(
                            "event_ids must contain only hashable values or None"
                        ) from exc
            frozen_type_rows.append(slot_values)
        frozen_rows.append(tuple(frozen_type_rows))
    return tuple(frozen_rows)


@dataclass(frozen=True, eq=False)
class AtomicCountingGridTensor:
    """Immutable lossless target tensor on an atomic time/type grid.

    The shape of occurrence-level arrays is ``(A, K, S)`` where ``A`` is the
    number of declared time atoms, ``K`` is the number of event types, and
    ``S`` is a serialization capacity chosen per tensor.  Mark arrays append
    the widest native dimension of the named field.  ``S`` is not a model
    assumption: construction fails instead of truncating when it is too small.

    Occurrence slots are normalized to a canonical active prefix in each cell.
    Their order is never part of :meth:`state_key`; exact tied occurrences are
    exchangeable.  Event ids, ``sample_id``, and ``group_id`` are retained only
    as provenance sidecars and are excluded from model-state equality.
    """

    schema: FeatureSchema
    cell_counts: np.ndarray
    occurrence_present: np.ndarray
    time_observed: np.ndarray
    type_observed: np.ndarray
    mark_values: FloatArrayMap
    mark_applicable: BoolArrayMap
    mark_present: BoolArrayMap
    mark_observed: BoolArrayMap
    cardinality_observed: bool
    event_ids: EventIdGrid
    sample_id: str = ""
    group_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema", _snapshot_schema(self.schema))
        if self.schema.time_measure is not TimeMeasureKind.ATOMIC:
            raise ValueError(
                "AtomicCountingGridTensor requires an atomic time-measure schema"
            )
        assert self.schema.time_reference is not None
        number_of_atoms = len(self.schema.time_reference.atoms)
        number_of_types = len(self.schema.event_types)

        if not isinstance(self.occurrence_present, np.ndarray):
            raise TypeError("occurrence_present must be a NumPy array")
        if self.occurrence_present.ndim != 3:
            raise ValueError("occurrence_present must be three-dimensional")
        if self.occurrence_present.shape[:2] != (number_of_atoms, number_of_types):
            raise ValueError(
                "occurrence_present grid axes are inconsistent with the schema"
            )
        slot_capacity = self.occurrence_present.shape[2]
        grid_shape = (number_of_atoms, number_of_types, slot_capacity)
        int_dtype = np.dtype(np.int64)
        float_dtype = np.dtype(np.float64)
        bool_dtype = np.dtype(np.bool_)

        object.__setattr__(
            self,
            "cell_counts",
            _immutable_array(
                self.cell_counts,
                name="cell_counts",
                dtype=int_dtype,
                shape=(number_of_atoms, number_of_types),
            ),
        )
        for attribute in ("occurrence_present", "time_observed", "type_observed"):
            object.__setattr__(
                self,
                attribute,
                _immutable_array(
                    getattr(self, attribute),
                    name=attribute,
                    dtype=bool_dtype,
                    shape=grid_shape,
                ),
            )

        dimensions = _field_dimensions(self.schema)
        object.__setattr__(
            self,
            "mark_values",
            _immutable_array_mapping(
                self.mark_values,
                name="mark_values",
                dtype=float_dtype,
                grid_shape=grid_shape,
                dimensions=dimensions,
            ),
        )
        for attribute in ("mark_applicable", "mark_present", "mark_observed"):
            object.__setattr__(
                self,
                attribute,
                _immutable_array_mapping(
                    getattr(self, attribute),
                    name=attribute,
                    dtype=bool_dtype,
                    grid_shape=grid_shape,
                    dimensions=dimensions,
                ),
            )

        if not isinstance(self.cardinality_observed, bool):
            raise TypeError("cardinality_observed must be a boolean")
        if not isinstance(self.sample_id, str):
            raise TypeError("sample_id must be a string")
        if not isinstance(self.group_id, str):
            raise TypeError("group_id must be a string")
        object.__setattr__(
            self,
            "event_ids",
            _freeze_event_ids(
                self.event_ids,
                number_of_atoms=number_of_atoms,
                number_of_types=number_of_types,
                slot_capacity=slot_capacity,
            ),
        )

        configuration = self._validate_and_decode(dimensions)
        self._canonicalize_slots(configuration, dimensions)

    @property
    def number_of_time_atoms(self) -> int:
        return int(self.cell_counts.shape[0])

    @property
    def number_of_event_types(self) -> int:
        return int(self.cell_counts.shape[1])

    @property
    def slot_capacity(self) -> int:
        return int(self.occurrence_present.shape[2])

    @property
    def cardinality(self) -> int:
        return sum(int(value) for value in self.cell_counts.flat)

    @property
    def maximum_cell_multiplicity(self) -> int:
        if not self.cell_counts.size:
            return 0
        return int(np.max(self.cell_counts))

    @property
    def time_atoms(self) -> Tuple[float, ...]:
        assert self.schema.time_reference is not None
        return self.schema.time_reference.atoms

    @property
    def type_ids(self) -> Tuple[int, ...]:
        return tuple(event_type.type_id for event_type in self.schema.event_types)

    @classmethod
    def from_configuration(
        cls,
        configuration: EventConfiguration,
        *,
        max_occurrences_per_cell: Optional[int] = None,
    ) -> "AtomicCountingGridTensor":
        """Encode a validated atomic-time configuration without truncation."""

        if type(configuration) is not EventConfiguration:
            raise TypeError(
                "configuration must be an exact EventConfiguration instance"
            )
        schema = _snapshot_schema(configuration.schema)
        configuration.validate()
        if schema.time_measure is not TimeMeasureKind.ATOMIC:
            raise ValueError(
                "AtomicCountingGridTensor requires an atomic time-measure schema"
            )
        assert schema.time_reference is not None
        atom_indices = {
            atom: index for index, atom in enumerate(schema.time_reference.atoms)
        }
        type_indices = {
            event_type.type_id: index
            for index, event_type in enumerate(schema.event_types)
        }
        number_of_atoms = len(atom_indices)
        number_of_types = len(type_indices)
        counts = np.zeros((number_of_atoms, number_of_types), dtype=np.int64)
        for event in configuration.events:
            counts[atom_indices[event.event_time], type_indices[event.event_type]] += 1
        required_capacity = int(np.max(counts)) if counts.size else 0
        capacity = (
            required_capacity
            if max_occurrences_per_cell is None
            else _slot_capacity(max_occurrences_per_cell)
        )
        if capacity < required_capacity:
            raise ValueError(
                "configuration requires {} occurrences in one cell and cannot fit "
                "per-cell capacity {}".format(required_capacity, capacity)
            )

        grid_shape = (number_of_atoms, number_of_types, capacity)
        occurrence_present = np.zeros(grid_shape, dtype=np.bool_)
        time_observed = np.zeros(grid_shape, dtype=np.bool_)
        type_observed = np.zeros(grid_shape, dtype=np.bool_)
        dimensions = _field_dimensions(schema)
        mark_values = {
            name: np.zeros(grid_shape + (dimension,), dtype=np.float64)
            for name, dimension in dimensions.items()
        }
        mark_applicable = {
            name: np.zeros(grid_shape + (dimension,), dtype=np.bool_)
            for name, dimension in dimensions.items()
        }
        mark_present = {
            name: np.zeros(grid_shape + (dimension,), dtype=np.bool_)
            for name, dimension in dimensions.items()
        }
        mark_observed = {
            name: np.zeros(grid_shape + (dimension,), dtype=np.bool_)
            for name, dimension in dimensions.items()
        }
        event_ids = [
            [[None for _ in range(capacity)] for _ in range(number_of_types)]
            for _ in range(number_of_atoms)
        ]
        next_slot = np.zeros((number_of_atoms, number_of_types), dtype=np.int64)
        assert configuration.observed is not None
        for event, observation in zip(
            configuration.events, configuration.observed.events
        ):
            atom_index = atom_indices[event.event_time]
            type_index = type_indices[event.event_type]
            slot = int(next_slot[atom_index, type_index])
            next_slot[atom_index, type_index] += 1
            occurrence_present[atom_index, type_index, slot] = True
            time_observed[atom_index, type_index, slot] = observation.time_observed
            type_observed[atom_index, type_index, slot] = observation.type_observed
            event_ids[atom_index][type_index][slot] = event.event_id
            event_schema = schema.event_type(event.event_type)
            for field in event_schema.fields:
                native = slice(0, field.dimension)
                mark_applicable[field.name][atom_index, type_index, slot, native] = True
                if field.name in event.marks:
                    mark_values[field.name][atom_index, type_index, slot, native] = (
                        event.marks[field.name]
                    )
                    mark_present[field.name][atom_index, type_index, slot, native] = True
                if field.name in observation.observed_marks:
                    mark_observed[field.name][atom_index, type_index, slot, native] = True

        return cls(
            schema=schema,
            cell_counts=counts,
            occurrence_present=occurrence_present,
            time_observed=time_observed,
            type_observed=type_observed,
            mark_values=mark_values,
            mark_applicable=mark_applicable,
            mark_present=mark_present,
            mark_observed=mark_observed,
            cardinality_observed=configuration.observed.cardinality_observed,
            event_ids=tuple(
                tuple(tuple(slots) for slots in row) for row in event_ids
            ),
            sample_id=configuration.sample_id,
            group_id=configuration.group_id,
        )

    def _validate_and_decode(
        self, dimensions: Mapping[str, int]
    ) -> EventConfiguration:
        if np.any(self.cell_counts < 0):
            raise ValueError("cell_counts must be nonnegative")
        if np.any(self.cell_counts > self.slot_capacity):
            raise ValueError("cell_counts cannot exceed the occurrence-slot capacity")
        counted_present = np.count_nonzero(self.occurrence_present, axis=2)
        if not np.array_equal(self.cell_counts, counted_present):
            raise ValueError("cell_counts is inconsistent with occurrence_present")

        inactive = ~self.occurrence_present
        if np.any(self.time_observed & inactive):
            raise ValueError("inactive occurrence slots cannot have observed times")
        if np.any(self.type_observed & inactive):
            raise ValueError("inactive occurrence slots cannot have observed types")
        for atom_index in range(self.number_of_time_atoms):
            for type_index in range(self.number_of_event_types):
                for slot in range(self.slot_capacity):
                    if inactive[atom_index, type_index, slot] and self.event_ids[
                        atom_index
                    ][type_index][slot] is not None:
                        raise ValueError("inactive occurrence slots cannot have event ids")

        expected_applicable = {
            name: np.zeros(
                (
                    self.number_of_time_atoms,
                    self.number_of_event_types,
                    self.slot_capacity,
                    dimension,
                ),
                dtype=np.bool_,
            )
            for name, dimension in dimensions.items()
        }
        for type_index, event_type in enumerate(self.schema.event_types):
            for field in event_type.fields:
                expected_applicable[field.name][
                    :, type_index, :, : field.dimension
                ] = self.occurrence_present[:, type_index, :, None]

        for field_name in dimensions:
            applicable = self.mark_applicable[field_name]
            present = self.mark_present[field_name]
            observed = self.mark_observed[field_name]
            values = self.mark_values[field_name]
            if not np.array_equal(applicable, expected_applicable[field_name]):
                raise ValueError(
                    "mark_applicable[{!r}] is inconsistent with cells and event "
                    "types".format(field_name)
                )
            if np.any(present & ~applicable):
                raise ValueError(
                    "mark_present[{!r}] includes inapplicable coordinates".format(
                        field_name
                    )
                )
            if np.any(observed & ~present):
                raise ValueError(
                    "mark_observed[{!r}] includes absent coordinates".format(
                        field_name
                    )
                )
            if np.any(values[~present] != 0.0):
                raise ValueError(
                    "mark_values[{!r}] must be zero where the mark is absent".format(
                        field_name
                    )
                )

        events = []
        observations = []
        for atom_index, event_time in enumerate(self.time_atoms):
            for type_index, event_type in enumerate(self.schema.event_types):
                for slot in range(self.slot_capacity):
                    if not self.occurrence_present[atom_index, type_index, slot]:
                        continue
                    marks = {}
                    observed_marks = set()
                    for field in event_type.fields:
                        native = slice(0, field.dimension)
                        present = self.mark_present[field.name][
                            atom_index, type_index, slot, native
                        ]
                        observed = self.mark_observed[field.name][
                            atom_index, type_index, slot, native
                        ]
                        if np.any(present) and not np.all(present):
                            raise ValueError(
                                "mark_present[{!r}] must cover a complete native "
                                "value".format(field.name)
                            )
                        if np.any(observed) and not np.all(observed):
                            raise ValueError(
                                "mark_observed[{!r}] must cover a complete native "
                                "value".format(field.name)
                            )
                        if np.all(present):
                            marks[field.name] = tuple(
                                float(value)
                                for value in self.mark_values[field.name][
                                    atom_index, type_index, slot, native
                                ]
                            )
                        if np.all(observed):
                            observed_marks.add(field.name)
                    events.append(
                        Event(
                            event_time=event_time,
                            event_type=event_type.type_id,
                            marks=marks,
                            event_id=self.event_ids[atom_index][type_index][slot],
                        )
                    )
                    observations.append(
                        EventObservation(
                            time_observed=bool(
                                self.time_observed[atom_index, type_index, slot]
                            ),
                            type_observed=bool(
                                self.type_observed[atom_index, type_index, slot]
                            ),
                            observed_marks=frozenset(observed_marks),
                        )
                    )

        return EventConfiguration(
            schema=self.schema,
            events=tuple(events),
            observed=ObservationPattern(
                events=tuple(observations),
                cardinality_observed=self.cardinality_observed,
            ),
            sample_id=self.sample_id,
            group_id=self.group_id,
        )

    def _canonicalize_slots(
        self,
        configuration: EventConfiguration,
        dimensions: Mapping[str, int],
    ) -> None:
        """Rebuild slots from canonical occurrences; slot order is serialization."""

        grid_shape = (
            self.number_of_time_atoms,
            self.number_of_event_types,
            self.slot_capacity,
        )
        occurrence_present = np.zeros(grid_shape, dtype=np.bool_)
        time_observed = np.zeros(grid_shape, dtype=np.bool_)
        type_observed = np.zeros(grid_shape, dtype=np.bool_)
        mark_values = {
            name: np.zeros(grid_shape + (dimension,), dtype=np.float64)
            for name, dimension in dimensions.items()
        }
        mark_applicable = {
            name: np.zeros(grid_shape + (dimension,), dtype=np.bool_)
            for name, dimension in dimensions.items()
        }
        mark_present = {
            name: np.zeros(grid_shape + (dimension,), dtype=np.bool_)
            for name, dimension in dimensions.items()
        }
        mark_observed = {
            name: np.zeros(grid_shape + (dimension,), dtype=np.bool_)
            for name, dimension in dimensions.items()
        }
        event_ids = [
            [
                [None for _ in range(self.slot_capacity)]
                for _ in range(self.number_of_event_types)
            ]
            for _ in range(self.number_of_time_atoms)
        ]
        atom_indices = {atom: index for index, atom in enumerate(self.time_atoms)}
        type_indices = {
            event_type.type_id: index
            for index, event_type in enumerate(self.schema.event_types)
        }
        next_slot = np.zeros(
            (self.number_of_time_atoms, self.number_of_event_types), dtype=np.int64
        )
        assert configuration.observed is not None
        for event, observation in zip(
            configuration.events, configuration.observed.events
        ):
            atom_index = atom_indices[event.event_time]
            type_index = type_indices[event.event_type]
            slot = int(next_slot[atom_index, type_index])
            next_slot[atom_index, type_index] += 1
            occurrence_present[atom_index, type_index, slot] = True
            time_observed[atom_index, type_index, slot] = observation.time_observed
            type_observed[atom_index, type_index, slot] = observation.type_observed
            event_ids[atom_index][type_index][slot] = event.event_id
            event_schema = self.schema.event_type(event.event_type)
            for field in event_schema.fields:
                native = slice(0, field.dimension)
                mark_applicable[field.name][atom_index, type_index, slot, native] = True
                if field.name in event.marks:
                    mark_values[field.name][atom_index, type_index, slot, native] = (
                        event.marks[field.name]
                    )
                    mark_present[field.name][atom_index, type_index, slot, native] = True
                if field.name in observation.observed_marks:
                    mark_observed[field.name][atom_index, type_index, slot, native] = True

        bool_dtype = np.dtype(np.bool_)
        float_dtype = np.dtype(np.float64)
        object.__setattr__(
            self,
            "occurrence_present",
            _immutable_array(
                occurrence_present,
                name="occurrence_present",
                dtype=bool_dtype,
                shape=grid_shape,
            ),
        )
        object.__setattr__(
            self,
            "time_observed",
            _immutable_array(
                time_observed,
                name="time_observed",
                dtype=bool_dtype,
                shape=grid_shape,
            ),
        )
        object.__setattr__(
            self,
            "type_observed",
            _immutable_array(
                type_observed,
                name="type_observed",
                dtype=bool_dtype,
                shape=grid_shape,
            ),
        )
        object.__setattr__(
            self,
            "mark_values",
            _immutable_array_mapping(
                mark_values,
                name="mark_values",
                dtype=float_dtype,
                grid_shape=grid_shape,
                dimensions=dimensions,
            ),
        )
        for attribute, values in (
            ("mark_applicable", mark_applicable),
            ("mark_present", mark_present),
            ("mark_observed", mark_observed),
        ):
            object.__setattr__(
                self,
                attribute,
                _immutable_array_mapping(
                    values,
                    name=attribute,
                    dtype=bool_dtype,
                    grid_shape=grid_shape,
                    dimensions=dimensions,
                ),
            )
        object.__setattr__(
            self,
            "event_ids",
            tuple(tuple(tuple(slots) for slots in row) for row in event_ids),
        )

    def to_configuration(self) -> EventConfiguration:
        """Decode all occurrences, observation masks, and provenance sidecars."""

        return self._validate_and_decode(_field_dimensions(self.schema))

    def state_key(self) -> Tuple[Tuple[object, ...], ...]:
        """Return the slot-permutation-invariant finite-counting model state."""

        return self.to_configuration().state_key()

    def to_model_view(self) -> ObservationView:
        """Return only genuinely observed anchors and optional cardinality."""

        configuration = self.to_configuration()
        assert configuration.observed is not None
        return configuration.observed.to_model_view(configuration)

    def __reduce__(self) -> Tuple[object, Tuple[object, ...]]:
        """Pickle through the validating constructor and restore immutability."""

        return (
            AtomicCountingGridTensor,
            (
                self.schema,
                self.cell_counts,
                self.occurrence_present,
                self.time_observed,
                self.type_observed,
                dict(self.mark_values),
                dict(self.mark_applicable),
                dict(self.mark_present),
                dict(self.mark_observed),
                self.cardinality_observed,
                self.event_ids,
                self.sample_id,
                self.group_id,
            ),
        )


def configuration_to_atomic_counting_grid_tensor(
    configuration: EventConfiguration,
    *,
    max_occurrences_per_cell: Optional[int] = None,
) -> AtomicCountingGridTensor:
    """Functional lossless encoder for an atomic-time configuration."""

    return AtomicCountingGridTensor.from_configuration(
        configuration,
        max_occurrences_per_cell=max_occurrences_per_cell,
    )


def atomic_counting_grid_tensor_to_configuration(
    tensor: AtomicCountingGridTensor,
) -> EventConfiguration:
    """Decode a validated counting-grid tensor."""

    if type(tensor) is not AtomicCountingGridTensor:
        raise TypeError("tensor must be an exact AtomicCountingGridTensor instance")
    return tensor.to_configuration()


def atomic_counting_grid_tensor_to_model_view(
    tensor: AtomicCountingGridTensor,
) -> ObservationView:
    """Remove hidden target alignment at the explicit conditioning boundary."""

    if type(tensor) is not AtomicCountingGridTensor:
        raise TypeError("tensor must be an exact AtomicCountingGridTensor instance")
    return tensor.to_model_view()


__all__ = [
    "AtomicCountingGridTensor",
    "atomic_counting_grid_tensor_to_configuration",
    "atomic_counting_grid_tensor_to_model_view",
    "configuration_to_atomic_counting_grid_tensor",
]
