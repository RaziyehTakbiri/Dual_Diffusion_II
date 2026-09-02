"""Immutable schemas for heterogeneous marked events.

Applicability is structural: an event type declares the continuous fields that
exist for that type. Whether an applicable value is observed is represented
separately by :mod:`heterodiff.events.observations`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Integral, Real
from typing import Optional, Sequence, Tuple, Union


class SupportKind(str, Enum):
    """Native support of one continuous mark field.

    All supports describe their open, continuously modelled stratum. Exact
    boundary atoms must be represented as separate discrete event types or
    fields; they must not be silently clipped into the interior.
    """

    REAL = "real"
    POSITIVE = "positive"
    BOUNDED = "bounded"
    SIMPLEX = "simplex"


class TimeMeasureKind(str, Enum):
    """Dominating observation-time measure declared by a dataset adapter."""

    CONTINUOUS = "continuous"
    ATOMIC = "atomic_grid"
    MIXED = "mixed"


class MultiplicityMode(str, Enum):
    """Whether identical model atoms may occur more than once.

    ``SIMPLE`` retains the original simple-configuration contract.  In
    ``FINITE_COUNTING`` mode the configuration is a finite counting measure:
    repeated occurrences are retained explicitly and their number is part of
    the model state.
    """

    SIMPLE = "simple"
    FINITE_COUNTING = "finite_counting"


@dataclass(frozen=True)
class TimeReference:
    """Concrete dominating measure for physical event time.

    The reference is the sum of an optional continuous component and explicit
    weighted atoms. Weights define a finite measure and therefore need not sum
    to one. A dataset adapter must choose the atoms before any atomic or mixed
    likelihood/reversal claim is made.
    """

    kind: TimeMeasureKind = TimeMeasureKind.CONTINUOUS
    atoms: Tuple[float, ...] = ()
    atom_weights: Tuple[float, ...] = ()
    continuous_weight: float = 1.0

    def __post_init__(self) -> None:
        try:
            kind = TimeMeasureKind(self.kind)
        except (TypeError, ValueError) as exc:
            valid = ", ".join(item.value for item in TimeMeasureKind)
            raise ValueError("time reference kind must be one of: {}".format(valid)) from exc
        object.__setattr__(self, "kind", kind)

        raw_atoms = tuple(self.atoms)
        raw_weights = tuple(self.atom_weights)
        if any(
            isinstance(value, bool) or not isinstance(value, Real)
            for value in raw_atoms
        ):
            raise TypeError("time atoms must contain real numbers")
        if any(
            isinstance(value, bool) or not isinstance(value, Real)
            for value in raw_weights
        ):
            raise TypeError("time atom weights must contain real numbers")
        atoms = tuple(float(value) for value in raw_atoms)
        weights = tuple(float(value) for value in raw_weights)
        if len(atoms) != len(weights):
            raise ValueError("every time atom requires exactly one weight")
        if any(not math.isfinite(value) or value < 0.0 for value in atoms):
            raise ValueError("time atoms must be finite and nonnegative")
        if len(set(atoms)) != len(atoms):
            raise ValueError("time atoms must be unique")
        if any(not math.isfinite(value) or value <= 0.0 for value in weights):
            raise ValueError("time atom weights must be finite and positive")

        if isinstance(self.continuous_weight, bool) or not isinstance(
            self.continuous_weight, Real
        ):
            raise TypeError("continuous time weight must be a real number")
        continuous_weight = float(self.continuous_weight)
        if not math.isfinite(continuous_weight) or continuous_weight < 0.0:
            raise ValueError("continuous time weight must be finite and nonnegative")

        if kind is TimeMeasureKind.CONTINUOUS:
            if atoms or weights:
                raise ValueError("a continuous time reference cannot contain atoms")
            if continuous_weight <= 0.0:
                raise ValueError("a continuous time reference needs positive weight")
        elif kind is TimeMeasureKind.ATOMIC:
            if not atoms:
                raise ValueError("an atomic time reference requires explicit atoms")
            if continuous_weight != 0.0:
                raise ValueError("an atomic time reference has zero continuous weight")
        else:
            if not atoms:
                raise ValueError("a mixed time reference requires explicit atoms")
            if continuous_weight <= 0.0:
                raise ValueError("a mixed time reference needs positive continuous weight")

        order = tuple(sorted(range(len(atoms)), key=atoms.__getitem__))
        object.__setattr__(self, "atoms", tuple(atoms[index] for index in order))
        object.__setattr__(
            self, "atom_weights", tuple(weights[index] for index in order)
        )
        object.__setattr__(self, "continuous_weight", continuous_weight)

    @classmethod
    def continuous(cls, weight: float = 1.0) -> "TimeReference":
        return cls(
            kind=TimeMeasureKind.CONTINUOUS,
            continuous_weight=weight,
        )

    @classmethod
    def atomic(
        cls,
        atoms: Sequence[Real],
        weights: Sequence[Real],
    ) -> "TimeReference":
        return cls(
            kind=TimeMeasureKind.ATOMIC,
            atoms=tuple(atoms),
            atom_weights=tuple(weights),
            continuous_weight=0.0,
        )

    @classmethod
    def mixed(
        cls,
        atoms: Sequence[Real],
        weights: Sequence[Real],
        *,
        continuous_weight: float = 1.0,
    ) -> "TimeReference":
        return cls(
            kind=TimeMeasureKind.MIXED,
            atoms=tuple(atoms),
            atom_weights=tuple(weights),
            continuous_weight=continuous_weight,
        )


NumericValue = Union[Real, Sequence[Real]]


def _positive_int(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("{} must be an integer".format(name))
    value = int(value)
    if value <= 0:
        raise ValueError("{} must be positive".format(name))
    return value


def _nonempty_name(value: object, *, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError("{} must be a string".format(name))
    if not value.strip():
        raise ValueError("{} must not be empty".format(name))
    return value


def _coerce_numeric_vector(value: NumericValue, *, name: str) -> Tuple[float, ...]:
    if isinstance(value, bool):
        raise TypeError("{} must contain real numbers, not booleans".format(name))
    if isinstance(value, Real):
        values = (float(value),)
    else:
        if isinstance(value, (str, bytes)):
            raise TypeError("{} must be a real number or a sequence of them".format(name))
        try:
            raw_values = tuple(value)
        except TypeError as exc:
            raise TypeError(
                "{} must be a real number or a sequence of them".format(name)
            ) from exc
        values_list = []
        for item in raw_values:
            if isinstance(item, bool) or not isinstance(item, Real):
                raise TypeError("{} must contain only real numbers".format(name))
            values_list.append(float(item))
        values = tuple(values_list)
    if any(not math.isfinite(item) for item in values):
        raise ValueError("{} must contain only finite values".format(name))
    return values


@dataclass(frozen=True)
class ContinuousField:
    """Schema for one native continuous mark.

    ``dimension`` is the native dimension. A simplex with ``dimension=K`` is
    transformed to ``K-1`` unconstrained coordinates.
    """

    name: str
    dimension: int = 1
    support: SupportKind = SupportKind.REAL
    lower: Optional[float] = None
    upper: Optional[float] = None
    unit: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _nonempty_name(self.name, name="field name"))
        object.__setattr__(
            self, "dimension", _positive_int(self.dimension, name="field dimension")
        )
        try:
            support = SupportKind(self.support)
        except (TypeError, ValueError) as exc:
            valid = ", ".join(item.value for item in SupportKind)
            raise ValueError("support must be one of: {}".format(valid)) from exc
        object.__setattr__(self, "support", support)

        if self.unit is not None:
            object.__setattr__(self, "unit", _nonempty_name(self.unit, name="field unit"))

        if support is SupportKind.BOUNDED:
            if self.lower is None or self.upper is None:
                raise ValueError("bounded fields require both lower and upper")
            if isinstance(self.lower, bool) or not isinstance(self.lower, Real):
                raise TypeError("lower must be a real number")
            if isinstance(self.upper, bool) or not isinstance(self.upper, Real):
                raise TypeError("upper must be a real number")
            lower, upper = float(self.lower), float(self.upper)
            if not math.isfinite(lower) or not math.isfinite(upper):
                raise ValueError("bounded endpoints must be finite")
            if lower >= upper:
                raise ValueError("bounded fields require lower < upper")
            width = upper - lower
            if not math.isfinite(width):
                raise ValueError("bounded field width must be finite")
            if math.nextafter(lower, upper) >= upper:
                raise ValueError(
                    "bounded field interval has no representable interior value"
                )
            object.__setattr__(self, "lower", lower)
            object.__setattr__(self, "upper", upper)
        elif self.lower is not None or self.upper is not None:
            raise ValueError("lower and upper are valid only for bounded fields")

        if support is SupportKind.SIMPLEX and self.dimension < 2:
            raise ValueError("a simplex field requires dimension >= 2")

    @property
    def transformed_dimension(self) -> int:
        """Number of unconstrained coordinates after the native transform."""

        if self.support is SupportKind.SIMPLEX:
            return self.dimension - 1
        return self.dimension

    def coerce_value(self, value: NumericValue) -> Tuple[float, ...]:
        """Validate and return a canonical tuple representation."""

        values = _coerce_numeric_vector(value, name="mark '{}'".format(self.name))
        if len(values) != self.dimension:
            raise ValueError(
                "mark '{}' has dimension {}; expected {}".format(
                    self.name, len(values), self.dimension
                )
            )

        if self.support is SupportKind.POSITIVE:
            if any(item <= 0.0 for item in values):
                raise ValueError("mark '{}' must be strictly positive".format(self.name))
        elif self.support is SupportKind.BOUNDED:
            assert self.lower is not None and self.upper is not None
            if any(not self.lower < item < self.upper for item in values):
                raise ValueError(
                    "mark '{}' must lie strictly inside ({}, {})".format(
                        self.name, self.lower, self.upper
                    )
                )
        elif self.support is SupportKind.SIMPLEX:
            if any(item <= 0.0 for item in values):
                raise ValueError(
                    "simplex mark '{}' must have strictly positive components".format(
                        self.name
                    )
                )
            tolerance = 32.0 * 2.220446049250313e-16 * self.dimension
            if not math.isclose(
                sum(values), 1.0, rel_tol=0.0, abs_tol=tolerance
            ):
                raise ValueError(
                    "simplex mark '{}' components must sum to one".format(self.name)
                )
        return values

    def contains(self, value: NumericValue) -> bool:
        """Return whether ``value`` belongs to the declared open support."""

        try:
            self.coerce_value(value)
        except (TypeError, ValueError):
            return False
        return True


@dataclass(frozen=True)
class EventTypeSchema:
    """The native continuous-mark schema for one categorical event type."""

    type_id: int
    name: str
    fields: Tuple[ContinuousField, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.type_id, bool) or not isinstance(self.type_id, Integral):
            raise TypeError("type_id must be an integer")
        type_id = int(self.type_id)
        if type_id < 0:
            raise ValueError("type_id must be non-negative")
        object.__setattr__(self, "type_id", type_id)
        object.__setattr__(self, "name", _nonempty_name(self.name, name="event type name"))
        fields = tuple(self.fields)
        if any(not isinstance(field, ContinuousField) for field in fields):
            raise TypeError("fields must contain only ContinuousField instances")
        names = tuple(field.name for field in fields)
        if len(set(names)) != len(names):
            raise ValueError("field names must be unique within an event type")
        object.__setattr__(self, "fields", fields)

    @property
    def field_names(self) -> Tuple[str, ...]:
        return tuple(field.name for field in self.fields)

    def has_field(self, name: str) -> bool:
        return any(field.name == name for field in self.fields)

    def field(self, name: str) -> ContinuousField:
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError("event type {!r} has no field {!r}".format(self.name, name))


@dataclass(frozen=True)
class FeatureSchema:
    """Complete event vocabulary and observation horizon for a dataset."""

    event_types: Tuple[EventTypeSchema, ...]
    horizon: Optional[float] = None
    time_measure: TimeMeasureKind = TimeMeasureKind.CONTINUOUS
    time_reference: Optional[TimeReference] = None
    allow_simultaneous: bool = False
    version: str = "1"
    multiplicity_mode: MultiplicityMode = MultiplicityMode.SIMPLE

    def __post_init__(self) -> None:
        event_types = tuple(self.event_types)
        if not event_types:
            raise ValueError("a feature schema requires at least one event type")
        if any(not isinstance(item, EventTypeSchema) for item in event_types):
            raise TypeError("event_types must contain only EventTypeSchema instances")
        ids = tuple(item.type_id for item in event_types)
        names = tuple(item.name for item in event_types)
        if len(set(ids)) != len(ids):
            raise ValueError("event type ids must be unique")
        if len(set(names)) != len(names):
            raise ValueError("event type names must be unique")
        object.__setattr__(self, "event_types", event_types)

        if self.horizon is not None:
            if isinstance(self.horizon, bool) or not isinstance(self.horizon, Real):
                raise TypeError("horizon must be a real number")
            horizon = float(self.horizon)
            if not math.isfinite(horizon) or horizon <= 0.0:
                raise ValueError("horizon must be finite and positive")
            object.__setattr__(self, "horizon", horizon)
        try:
            time_measure = TimeMeasureKind(self.time_measure)
        except (TypeError, ValueError) as exc:
            valid = ", ".join(item.value for item in TimeMeasureKind)
            raise ValueError("time_measure must be one of: {}".format(valid)) from exc
        object.__setattr__(self, "time_measure", time_measure)
        try:
            multiplicity_mode = MultiplicityMode(self.multiplicity_mode)
        except (TypeError, ValueError) as exc:
            valid = ", ".join(item.value for item in MultiplicityMode)
            raise ValueError(
                "multiplicity_mode must be one of: {}".format(valid)
            ) from exc
        object.__setattr__(self, "multiplicity_mode", multiplicity_mode)
        time_reference = self.time_reference
        if time_reference is None:
            if time_measure is not TimeMeasureKind.CONTINUOUS:
                raise ValueError(
                    "atomic or mixed time measures require an explicit TimeReference"
                )
            time_reference = TimeReference.continuous()
        elif not isinstance(time_reference, TimeReference):
            raise TypeError("time_reference must be a TimeReference or None")
        if time_reference.kind is not time_measure:
            raise ValueError("time_reference kind must match time_measure")
        if self.horizon is not None and any(
            atom > self.horizon for atom in time_reference.atoms
        ):
            raise ValueError("time atoms must lie inside the observation horizon")
        object.__setattr__(self, "time_reference", time_reference)
        if not isinstance(self.allow_simultaneous, bool):
            raise TypeError("allow_simultaneous must be a boolean")
        object.__setattr__(self, "version", _nonempty_name(self.version, name="schema version"))

    def event_type(self, type_id: int) -> EventTypeSchema:
        for event_type in self.event_types:
            if event_type.type_id == type_id:
                return event_type
        raise KeyError("unknown event type id {}".format(type_id))

    def is_applicable(self, type_id: int, field_name: str) -> bool:
        return self.event_type(type_id).has_field(field_name)

    def has_field(self, field_name: str) -> bool:
        return any(event_type.has_field(field_name) for event_type in self.event_types)

    @property
    def all_field_names(self) -> Tuple[str, ...]:
        return tuple(
            sorted(
                {
                    field.name
                    for event_type in self.event_types
                    for field in event_type.fields
                }
            )
        )
