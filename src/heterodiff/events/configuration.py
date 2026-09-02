"""Immutable finite configurations of typed marked events.

These objects are validated runtime representations, not the persistence or
hash-key boundary.  Use :meth:`EventConfiguration.state_key` for an ID-free
model-state key and :class:`heterodiff.data.ReferenceTensor` for validated
serialization with provenance sidecars.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from numbers import Integral, Real
from types import MappingProxyType
from typing import Hashable, Iterable, Iterator, Mapping, Optional, Sequence, Tuple

from .observations import EventObservation, ObservationPattern
from .schema import FeatureSchema, MultiplicityMode, TimeMeasureKind


MarkVector = Tuple[float, ...]


def _freeze_mark(value: object, *, name: str) -> MarkVector:
    if isinstance(value, bool):
        raise TypeError("mark {!r} must contain real numbers".format(name))
    if isinstance(value, Real):
        converted_value = float(value)
        values = (0.0 if converted_value == 0.0 else converted_value,)
    else:
        if isinstance(value, (str, bytes)):
            raise TypeError("mark {!r} must be numeric".format(name))
        try:
            raw_values = tuple(value)  # type: ignore[arg-type]
        except TypeError as exc:
            raise TypeError("mark {!r} must be numeric".format(name)) from exc
        converted = []
        for item in raw_values:
            if isinstance(item, bool) or not isinstance(item, Real):
                raise TypeError("mark {!r} must contain real numbers".format(name))
            converted_value = float(item)
            converted.append(0.0 if converted_value == 0.0 else converted_value)
        values = tuple(converted)
    if any(not math.isfinite(item) for item in values):
        raise ValueError("mark {!r} must contain finite values".format(name))
    return values


@dataclass(frozen=True)
class Event:
    """One typed event in native coordinates.

    Marks are stored as immutable float tuples, including scalar marks. The
    optional ``event_id`` is simulator or dataset bookkeeping; it is excluded
    from equality, canonical ordering, and the probabilistic model state.
    """

    event_time: float
    event_type: int
    marks: Mapping[str, MarkVector] = field(default_factory=dict)
    event_id: Optional[Hashable] = field(default=None, compare=False, hash=False)

    def __post_init__(self) -> None:
        if isinstance(self.event_time, bool) or not isinstance(self.event_time, Real):
            raise TypeError("event_time must be a real number")
        event_time = float(self.event_time)
        if not math.isfinite(event_time):
            raise ValueError("event_time must be finite")
        if event_time == 0.0:
            event_time = 0.0
        object.__setattr__(self, "event_time", event_time)

        if isinstance(self.event_type, bool) or not isinstance(self.event_type, Integral):
            raise TypeError("event_type must be an integer")
        object.__setattr__(self, "event_type", int(self.event_type))

        if not isinstance(self.marks, Mapping):
            raise TypeError("marks must be a mapping from field names to values")
        frozen_marks = {}
        for name, value in self.marks.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("mark names must be non-empty strings")
            frozen_marks[name] = _freeze_mark(value, name=name)
        object.__setattr__(
            self, "marks", MappingProxyType(dict(sorted(frozen_marks.items())))
        )

        if self.event_id is not None:
            try:
                hash(self.event_id)
            except TypeError as exc:
                raise TypeError("event_id must be hashable") from exc

    def model_key(self) -> Tuple[object, ...]:
        """Canonical key containing model state but no bookkeeping id."""

        return (
            self.event_time,
            self.event_type,
            tuple((name, self.marks[name]) for name in sorted(self.marks)),
        )


def canonical_sort(events: Iterable[Event]) -> Tuple[Event, ...]:
    """Sort an event representation using only permutation-invariant state.

    Unlike a stable time-only sort, the result does not depend on the input
    enumeration when simultaneous events are permitted. Exact duplicate model
    states are left adjacent; their admissibility is selected by the schema's
    multiplicity mode.
    """

    events_tuple = tuple(events)
    if any(type(event) is not Event for event in events_tuple):
        raise TypeError("events must contain only exact Event instances")
    return tuple(sorted(events_tuple, key=Event.model_key))


@dataclass(frozen=True)
class CountedEvent:
    """One distinct model atom and its positive finite multiplicity.

    ``event`` is always stripped of its optional provenance identifier.  The
    count summary therefore exposes only probabilistic model state even when
    the occurrence-expanded configuration retains dataset sidecars.  This is
    a runtime summary; use :meth:`state_key` rather than relying on hashing or
    pickling the mapping-backed ``Event`` object.
    """

    event: Event
    multiplicity: int

    def __post_init__(self) -> None:
        if type(self.event) is not Event:
            raise TypeError("event must be an exact Event instance")
        if isinstance(self.multiplicity, bool) or not isinstance(
            self.multiplicity, Integral
        ):
            raise TypeError("multiplicity must be an integer")
        multiplicity = int(self.multiplicity)
        if multiplicity <= 0:
            raise ValueError("multiplicity must be positive")
        object.__setattr__(self, "multiplicity", multiplicity)
        # Always rebuild the public base type.  Besides dropping ``event_id``,
        # this prevents an Event subclass from smuggling extra comparison or
        # provenance state through the count-summary boundary.
        object.__setattr__(
            self,
            "event",
            Event(
                event_time=self.event.event_time,
                event_type=self.event.event_type,
                marks=self.event.marks,
            ),
        )

    def state_key(self) -> Tuple[object, ...]:
        """Canonical model-state key with no occurrence provenance."""

        return (self.event.model_key(), self.multiplicity)


def _canonical_occurrence_key(
    event: Event, observation: EventObservation
) -> Tuple[object, ...]:
    """Joint canonical key for an occurrence and its aligned supervision."""

    return (event.model_key(), observation.signature_key())


@dataclass(frozen=True)
class EventConfiguration:
    """A validated finite configuration on a typed event space.

    Construction canonicalizes event order and the aligned observation pattern.
    Thus two enumerations of the same unlabelled configuration compare equal,
    regardless of dataset identifiers.  For repeated atoms, supervision masks
    participate in canonical ordering so their aligned occurrence expansion is
    also independent of input enumeration.
    """

    schema: FeatureSchema
    events: Tuple[Event, ...] = ()
    observed: Optional[ObservationPattern] = field(
        default=None, compare=False, hash=False
    )
    sample_id: str = field(default="", compare=False, hash=False)
    group_id: str = field(default="", compare=False, hash=False)

    def __post_init__(self) -> None:
        if not isinstance(self.schema, FeatureSchema):
            raise TypeError("schema must be a FeatureSchema")
        events = tuple(self.events)
        if any(type(event) is not Event for event in events):
            raise TypeError("events must contain only exact Event instances")
        object.__setattr__(self, "events", events)

        if not isinstance(self.sample_id, str):
            raise TypeError("sample_id must be a string")
        if not isinstance(self.group_id, str):
            raise TypeError("group_id must be a string")

        observed = self.observed
        if observed is None:
            observed = ObservationPattern.from_present_values(self)
        elif type(observed) is not ObservationPattern:
            raise TypeError(
                "observed must be an exact ObservationPattern instance or None"
            )
        object.__setattr__(self, "observed", observed)

        self._validate_events()
        observed.validate(self)

        order = tuple(
            sorted(
                range(len(events)),
                key=lambda index: _canonical_occurrence_key(
                    events[index], observed.events[index]
                ),
            )
        )
        if order != tuple(range(len(events))):
            object.__setattr__(self, "events", tuple(events[index] for index in order))
            observed = observed.permuted(order)
            object.__setattr__(self, "observed", observed)

        self._validate_multiplicity_contract()
        observed.validate(self)

    def _validate_events(self) -> None:
        seen_ids = set()
        for index, event in enumerate(self.events):
            try:
                event_type = self.schema.event_type(event.event_type)
            except KeyError as exc:
                raise ValueError(
                    "event {} uses unknown type id {}".format(index, event.event_type)
                ) from exc

            if event.event_time < 0.0:
                raise ValueError("event {} occurs before time zero".format(index))
            if self.schema.horizon is not None and event.event_time > self.schema.horizon:
                raise ValueError(
                    "event {} occurs after horizon {}".format(index, self.schema.horizon)
                )
            if self.schema.time_measure is TimeMeasureKind.ATOMIC:
                assert self.schema.time_reference is not None
                if event.event_time not in self.schema.time_reference.atoms:
                    raise ValueError(
                        "event {} time {} is outside the declared atomic grid".format(
                            index, event.event_time
                        )
                    )

            applicable = set(event_type.field_names)
            invalid = set(event.marks) - applicable
            if invalid:
                raise ValueError(
                    "event {} stores inapplicable marks: {}".format(
                        index, ", ".join(sorted(invalid))
                    )
                )
            for name, value in event.marks.items():
                event_type.field(name).coerce_value(value)

            if event.event_id is not None:
                if event.event_id in seen_ids:
                    raise ValueError("event_id values must be unique within a configuration")
                seen_ids.add(event.event_id)

    def _validate_multiplicity_contract(self) -> None:
        for previous, current in zip(self.events, self.events[1:]):
            duplicate = previous.model_key() == current.model_key()
            if duplicate:
                if self.schema.multiplicity_mode is MultiplicityMode.SIMPLE:
                    raise ValueError(
                        "a simple event configuration cannot contain duplicates"
                    )
                # Repeated occurrences are precisely the extra states admitted
                # by finite-counting mode, even when unrelated simultaneous
                # atoms remain disallowed by ``allow_simultaneous``.
                continue
            if (
                not self.schema.allow_simultaneous
                and previous.event_time == current.event_time
            ):
                raise ValueError(
                    "simultaneous events require an explicit schema representation"
                )

    def validate(self, *, require_complete: bool = False) -> None:
        """Re-run invariants and optionally require every applicable value."""

        self._validate_events()
        self._validate_multiplicity_contract()
        assert self.observed is not None
        self.observed.validate(self)
        if require_complete:
            for index, event in enumerate(self.events):
                expected = set(self.schema.event_type(event.event_type).field_names)
                absent = expected - set(event.marks)
                if absent:
                    raise ValueError(
                        "event {} is missing applicable values: {}".format(
                            index, ", ".join(sorted(absent))
                        )
                    )

    @property
    def is_complete(self) -> bool:
        try:
            self.validate(require_complete=True)
        except ValueError:
            return False
        return True

    @property
    def is_canonical(self) -> bool:
        assert self.observed is not None
        keys = tuple(
            _canonical_occurrence_key(event, observation)
            for event, observation in zip(self.events, self.observed.events)
        )
        return keys == tuple(sorted(keys))

    @property
    def cardinality(self) -> int:
        """Total occurrence count, including repeated model atoms."""

        return len(self.events)

    @property
    def distinct_atom_count(self) -> int:
        """Number of distinct model atoms after forgetting provenance ids."""

        return len(self.count_items())

    @property
    def is_simple(self) -> bool:
        """Whether every distinct model atom has multiplicity one."""

        return self.cardinality == self.distinct_atom_count

    def count_items(self) -> Tuple[CountedEvent, ...]:
        """Return canonical distinct atoms with positive counts.

        Observation metadata is not model state and provenance identifiers are
        stripped from each representative atom.
        """

        items = []
        index = 0
        while index < len(self.events):
            event = self.events[index]
            model_key = event.model_key()
            stop = index + 1
            while (
                stop < len(self.events)
                and self.events[stop].model_key() == model_key
            ):
                stop += 1
            items.append(CountedEvent(event=event, multiplicity=stop - index))
            index = stop
        return tuple(items)

    def multiplicity_of(self, event: Event) -> int:
        """Return the count of ``event``'s model atom, ignoring its id."""

        if type(event) is not Event:
            raise TypeError("event must be an exact Event instance")
        key = event.model_key()
        return sum(1 for occurrence in self.events if occurrence.model_key() == key)

    def state_key(self) -> Tuple[Tuple[object, ...], ...]:
        """Canonical finite-counting state with all provenance excluded."""

        return tuple(item.state_key() for item in self.count_items())

    def permuted(self, order: Sequence[int]) -> "EventConfiguration":
        """Re-enumerate events, then return the same canonical configuration."""

        order_tuple = tuple(order)
        if sorted(order_tuple) != list(range(len(self.events))):
            raise ValueError("order must be a permutation of event indices")
        assert self.observed is not None
        return EventConfiguration(
            schema=self.schema,
            events=tuple(self.events[index] for index in order_tuple),
            observed=self.observed.permuted(order_tuple),
            sample_id=self.sample_id,
            group_id=self.group_id,
        )

    def with_observation(self, observed: ObservationPattern) -> "EventConfiguration":
        return EventConfiguration(
            schema=self.schema,
            events=self.events,
            observed=observed,
            sample_id=self.sample_id,
            group_id=self.group_id,
        )

    def __len__(self) -> int:
        return len(self.events)

    def __iter__(self) -> Iterator[Event]:
        return iter(self.events)
