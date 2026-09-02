"""Observation semantics for typed event configurations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from numbers import Integral, Real
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    FrozenSet,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

if TYPE_CHECKING:  # pragma: no cover - imports are for static checking only
    from .configuration import EventConfiguration


class MarkStatus(str, Enum):
    """Semantic state of a mark at one event."""

    INAPPLICABLE = "inapplicable"
    MISSING = "applicable_unobserved"
    OBSERVED = "applicable_observed"


@dataclass(frozen=True)
class EventObservation:
    """Ground-truth-aligned annotation of which event coordinates are observed.

    This object is supervision metadata. Its tuple position must not be exposed
    directly to a model when event cardinality or identity is hidden. Use
    :meth:`ObservationPattern.to_model_view` for a non-leaking input view.
    """

    time_observed: bool = True
    type_observed: bool = True
    observed_marks: FrozenSet[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.time_observed, bool):
            raise TypeError("time_observed must be a boolean")
        if not isinstance(self.type_observed, bool):
            raise TypeError("type_observed must be a boolean")
        marks = frozenset(self.observed_marks)
        if any(not isinstance(name, str) or not name.strip() for name in marks):
            raise ValueError("observed mark names must be non-empty strings")
        object.__setattr__(self, "observed_marks", marks)

    def signature_key(self) -> Tuple[object, ...]:
        """Return the canonical supervision signature for one occurrence.

        The signature contains masks only.  It deliberately contains neither
        target values nor occurrence provenance, and is suitable for breaking
        canonical-order ties between identical model atoms.
        """

        return (
            self.time_observed,
            self.type_observed,
            tuple(sorted(self.observed_marks)),
        )


@dataclass(frozen=True)
class ObservedAnchor:
    """Only the values of one event that are genuinely visible to a model."""

    event_time: Optional[float] = None
    event_type: Optional[int] = None
    marks: Mapping[str, Tuple[float, ...]] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if self.event_time is not None:
            if isinstance(self.event_time, bool) or not isinstance(self.event_time, Real):
                raise TypeError("event_time must be a real number or None")
            event_time = float(self.event_time)
            if not math.isfinite(event_time) or event_time < 0.0:
                raise ValueError("event_time must be finite and nonnegative")
            object.__setattr__(self, "event_time", event_time)
        if self.event_type is not None:
            if isinstance(self.event_type, bool) or not isinstance(self.event_type, Integral):
                raise TypeError("event_type must be an integer or None")
            event_type = int(self.event_type)
            if event_type < 0:
                raise ValueError("event_type must be nonnegative")
            object.__setattr__(self, "event_type", event_type)
        if not isinstance(self.marks, Mapping):
            raise TypeError("marks must be a mapping")
        frozen = {}
        for name, values in self.marks.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("visible mark names must be non-empty strings")
            if isinstance(values, (str, bytes, Real)):
                raise TypeError(
                    "visible mark values must be a nonempty sequence of real numbers"
                )
            try:
                raw_vector = tuple(values)
            except TypeError as exc:
                raise TypeError(
                    "visible mark values must be a nonempty sequence of real numbers"
                ) from exc
            if not raw_vector:
                raise ValueError("visible mark value vectors must not be empty")
            if any(
                isinstance(value, bool) or not isinstance(value, Real)
                for value in raw_vector
            ):
                raise TypeError(
                    "visible mark values must contain real non-boolean numbers"
                )
            vector = tuple(float(value) for value in raw_vector)
            if any(not math.isfinite(value) for value in vector):
                raise ValueError("visible marks must be finite")
            frozen[name] = vector
        object.__setattr__(self, "marks", MappingProxyType(dict(sorted(frozen.items()))))

    @property
    def is_empty(self) -> bool:
        return self.event_time is None and self.event_type is None and not self.marks

    def visible_key(self) -> Tuple[object, ...]:
        return (
            self.event_time is None,
            0.0 if self.event_time is None else self.event_time,
            self.event_type is None,
            -1 if self.event_type is None else self.event_type,
            tuple(self.marks.items()),
        )


@dataclass(frozen=True)
class ObservationView:
    """Model-visible anchors and optional cardinality, with no target alignment."""

    anchors: Tuple[ObservedAnchor, ...] = ()
    cardinality: Optional[int] = None

    def __post_init__(self) -> None:
        anchors = tuple(self.anchors)
        if any(not isinstance(anchor, ObservedAnchor) for anchor in anchors):
            raise TypeError("anchors must contain only ObservedAnchor instances")
        if any(anchor.is_empty for anchor in anchors):
            raise ValueError("empty hidden events must not appear as model-visible anchors")
        object.__setattr__(self, "anchors", tuple(sorted(anchors, key=lambda x: x.visible_key())))
        if self.cardinality is not None:
            if isinstance(self.cardinality, bool) or not isinstance(
                self.cardinality, Integral
            ):
                raise TypeError("cardinality must be an integer or None")
            cardinality = int(self.cardinality)
            if cardinality < 0:
                raise ValueError("cardinality must be nonnegative")
            if cardinality < len(anchors):
                raise ValueError(
                    "cardinality cannot be smaller than the number of visible anchors"
                )
            object.__setattr__(self, "cardinality", cardinality)


@dataclass(frozen=True)
class ObservationPattern:
    """Observation mask aligned with a configuration's events.

    This is ground-truth-aligned supervision metadata, not directly a model
    input. Applicability is intentionally absent from this object. It is derived from
    the event's type in ``FeatureSchema``. Consequently an inapplicable mark can
    never be mislabeled as merely missing.
    """

    events: Tuple[EventObservation, ...] = ()
    cardinality_observed: bool = True

    def __post_init__(self) -> None:
        events = tuple(self.events)
        if any(type(item) is not EventObservation for item in events):
            raise TypeError(
                "events must contain only exact EventObservation instances"
            )
        if not isinstance(self.cardinality_observed, bool):
            raise TypeError("cardinality_observed must be a boolean")
        object.__setattr__(self, "events", events)

    @classmethod
    def from_present_values(cls, configuration: "EventConfiguration") -> "ObservationPattern":
        """Mark every value physically present in the record as observed."""

        return cls(
            events=tuple(
                EventObservation(observed_marks=frozenset(event.marks))
                for event in configuration.events
            )
        )

    @classmethod
    def fully_observed(cls, configuration: "EventConfiguration") -> "ObservationPattern":
        """Observe time, type, and every applicable mark.

        Validation fails if the record does not contain a value for an
        applicable mark, making accidental claims of complete observation
        visible at the data boundary.
        """

        pattern = cls(
            events=tuple(
                EventObservation(
                    observed_marks=frozenset(
                        configuration.schema.event_type(event.event_type).field_names
                    )
                )
                for event in configuration.events
            )
        )
        pattern.validate(configuration)
        return pattern

    @classmethod
    def fully_hidden(cls, configuration: "EventConfiguration") -> "ObservationPattern":
        return cls(
            events=tuple(
                EventObservation(
                    time_observed=False,
                    type_observed=False,
                    observed_marks=frozenset(),
                )
                for _ in configuration.events
            ),
            cardinality_observed=False,
        )

    def validate(self, configuration: "EventConfiguration") -> None:
        if len(self.events) != len(configuration.events):
            raise ValueError(
                "observation pattern has {} events; configuration has {}".format(
                    len(self.events), len(configuration.events)
                )
            )
        for index, (event, observation) in enumerate(
            zip(configuration.events, self.events)
        ):
            applicable = set(
                configuration.schema.event_type(event.event_type).field_names
            )
            invalid = observation.observed_marks - applicable
            if invalid:
                raise ValueError(
                    "event {} observes inapplicable marks: {}".format(
                        index, ", ".join(sorted(invalid))
                    )
                )
            absent = observation.observed_marks - set(event.marks)
            if absent:
                raise ValueError(
                    "event {} marks values as observed but stores no value for: {}".format(
                        index, ", ".join(sorted(absent))
                    )
                )

    def to_model_view(self, configuration: "EventConfiguration") -> ObservationView:
        """Remove hidden event slots and return only genuinely visible values.

        In particular, a fully hidden pattern yields no anchors and no
        cardinality. Type-derived applicability masks are not included because
        they could reveal an unobserved event type.
        """

        self.validate(configuration)
        anchors = []
        for event, observation in zip(configuration.events, self.events):
            anchor = ObservedAnchor(
                event_time=event.event_time if observation.time_observed else None,
                event_type=event.event_type if observation.type_observed else None,
                marks={name: event.marks[name] for name in observation.observed_marks},
            )
            if not anchor.is_empty:
                anchors.append(anchor)
        return ObservationView(
            anchors=tuple(anchors),
            cardinality=len(configuration) if self.cardinality_observed else None,
        )

    def mark_status(
        self, configuration: "EventConfiguration", event_index: int, field_name: str
    ) -> MarkStatus:
        if not configuration.schema.has_field(field_name):
            raise KeyError("unknown mark field {!r}".format(field_name))
        if event_index < 0:
            raise IndexError("event index out of range")
        try:
            event = configuration.events[event_index]
            observation = self.events[event_index]
        except IndexError as exc:
            raise IndexError("event index out of range") from exc
        if not configuration.schema.is_applicable(event.event_type, field_name):
            return MarkStatus.INAPPLICABLE
        if field_name in observation.observed_marks:
            return MarkStatus.OBSERVED
        return MarkStatus.MISSING

    def applicability_mask(
        self,
        configuration: "EventConfiguration",
        field_names: Optional[Sequence[str]] = None,
    ) -> Tuple[Tuple[bool, ...], ...]:
        """Return a supervision/evaluation mask; never expose it for hidden types."""

        names = self._validated_field_names(configuration, field_names)
        return tuple(
            tuple(
                configuration.schema.is_applicable(event.event_type, name)
                for name in names
            )
            for event in configuration.events
        )

    def observation_mask(
        self,
        configuration: "EventConfiguration",
        field_names: Optional[Sequence[str]] = None,
    ) -> Tuple[Tuple[bool, ...], ...]:
        names = self._validated_field_names(configuration, field_names)
        return tuple(
            tuple(name in observation.observed_marks for name in names)
            for observation in self.events
        )

    def permuted(self, order: Iterable[int]) -> "ObservationPattern":
        order_tuple = tuple(order)
        if sorted(order_tuple) != list(range(len(self.events))):
            raise ValueError("order must be a permutation of observation indices")
        return ObservationPattern(
            events=tuple(self.events[index] for index in order_tuple),
            cardinality_observed=self.cardinality_observed,
        )

    @staticmethod
    def _validated_field_names(
        configuration: "EventConfiguration", field_names: Optional[Sequence[str]]
    ) -> Tuple[str, ...]:
        names = (
            configuration.schema.all_field_names
            if field_names is None
            else tuple(field_names)
        )
        unknown = tuple(name for name in names if not configuration.schema.has_field(name))
        if unknown:
            raise KeyError("unknown mark fields: {}".format(", ".join(unknown)))
        return names
