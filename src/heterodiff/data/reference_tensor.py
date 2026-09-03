"""Lossless fixed-capacity *target* arrays for event configurations.

The representation is deliberately redundant.  Physical event time is stored
alongside its inter-event delta, and every continuous field has separate
applicability, physical-presence, and observation masks.  Consequently padding,
inapplicable coordinates, and missing applicable values are never identified
with an ordinary numeric value in a model objective.

Only arrays with an active mask may contribute to a probabilistic objective.
Inactive numeric entries are canonical zero sentinels and inactive event types
are ``-1``; these sentinels are validated but carry no probabilistic meaning.
The aligned arrays contain target identity, cardinality, and supervision.  They
are therefore not a conditioning input.  Use :meth:`ReferenceTensor.to_model_view`
to cross the explicit non-leaking boundary; the resulting unordered
``ObservationView`` contains only genuinely visible values.
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
from heterodiff.events.schema import FeatureSchema


FloatArrayMap = Mapping[str, np.ndarray]
BoolArrayMap = Mapping[str, np.ndarray]
_INT64_MAX = int(np.iinfo(np.int64).max)


def _capacity(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("max_events must be an integer")
    result = int(value)
    if result < 0:
        raise ValueError("max_events must be nonnegative")
    return result


def _field_dimensions(schema: FeatureSchema) -> Mapping[str, int]:
    """Return the widest native dimension of each schema field name."""

    dimensions = {}
    for event_type in schema.event_types:
        for field in event_type.fields:
            dimensions[field.name] = max(dimensions.get(field.name, 0), field.dimension)
    return MappingProxyType(dict(sorted(dimensions.items())))


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
        raise ValueError(
            "{} has shape {}; expected {}".format(name, value.shape, shape)
        )
    contiguous = np.array(value, dtype=dtype, copy=True, order="C")
    if dtype.kind == "f":
        # IEEE -0.0 and +0.0 compare equal but serialize differently.  Zero is
        # a canonical sentinel throughout this representation, so normalize
        # both active values and inactive/padded sentinels before freezing.
        contiguous[contiguous == 0.0] = 0.0
    # A bytes-backed array cannot have write access re-enabled by a caller,
    # unlike an owning ndarray whose WRITEABLE flag was merely cleared.
    result = np.frombuffer(contiguous.tobytes(order="C"), dtype=dtype).reshape(shape)
    return result


def _immutable_array_mapping(
    value: object,
    *,
    name: str,
    dtype: np.dtype,
    capacity: int,
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
            shape=(capacity, dimension),
        )
        for field_name, dimension in dimensions.items()
    }
    return MappingProxyType(arrays)


@dataclass(frozen=True, eq=False)
class ReferenceTensor:
    """Immutable, fixed-capacity representation of one configuration.

    ``mark_applicable`` is determined by the active event type.
    ``mark_present`` says whether the native value is physically stored, and
    ``mark_observed`` records the aligned supervision annotation.  These masks
    use the same shape as ``mark_values`` and are all-or-none over the native
    dimension of an applicable field.

    Dataset identifiers and event ids are retained as non-probabilistic
    sidecars, so conversion back to :class:`EventConfiguration` loses neither
    model state nor observation/provenance metadata.
    """

    schema: FeatureSchema
    length: int
    event_time: np.ndarray
    delta_time: np.ndarray
    event_type: np.ndarray
    event_present: np.ndarray
    time_observed: np.ndarray
    type_observed: np.ndarray
    mark_values: FloatArrayMap
    mark_applicable: BoolArrayMap
    mark_present: BoolArrayMap
    mark_observed: BoolArrayMap
    cardinality_observed: bool
    event_ids: Tuple[Optional[Hashable], ...]
    sample_id: str = ""
    group_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.schema, FeatureSchema):
            raise TypeError("schema must be a FeatureSchema")
        if isinstance(self.length, bool) or not isinstance(self.length, Integral):
            raise TypeError("length must be an integer")
        length = int(self.length)
        if length < 0:
            raise ValueError("length must be nonnegative")
        object.__setattr__(self, "length", length)

        if not isinstance(self.event_time, np.ndarray):
            raise TypeError("event_time must be a NumPy array")
        if self.event_time.ndim != 1:
            raise ValueError("event_time must be one-dimensional")
        capacity = self.event_time.shape[0]
        if length > capacity:
            raise ValueError(
                "length {} exceeds fixed capacity {}".format(length, capacity)
            )

        float_dtype = np.dtype(np.float64)
        int_dtype = np.dtype(np.int64)
        bool_dtype = np.dtype(np.bool_)
        object.__setattr__(
            self,
            "event_time",
            _immutable_array(
                self.event_time,
                name="event_time",
                dtype=float_dtype,
                shape=(capacity,),
            ),
        )
        object.__setattr__(
            self,
            "delta_time",
            _immutable_array(
                self.delta_time,
                name="delta_time",
                dtype=float_dtype,
                shape=(capacity,),
            ),
        )
        object.__setattr__(
            self,
            "event_type",
            _immutable_array(
                self.event_type,
                name="event_type",
                dtype=int_dtype,
                shape=(capacity,),
            ),
        )
        for attribute in ("event_present", "time_observed", "type_observed"):
            object.__setattr__(
                self,
                attribute,
                _immutable_array(
                    getattr(self, attribute),
                    name=attribute,
                    dtype=bool_dtype,
                    shape=(capacity,),
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
                capacity=capacity,
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
                    capacity=capacity,
                    dimensions=dimensions,
                ),
            )

        if not isinstance(self.cardinality_observed, bool):
            raise TypeError("cardinality_observed must be a boolean")
        if not isinstance(self.sample_id, str):
            raise TypeError("sample_id must be a string")
        if not isinstance(self.group_id, str):
            raise TypeError("group_id must be a string")

        event_ids = tuple(self.event_ids)
        if len(event_ids) != capacity:
            raise ValueError(
                "event_ids has length {}; expected {}".format(
                    len(event_ids), capacity
                )
            )
        for event_id in event_ids:
            if event_id is not None:
                try:
                    hash(event_id)
                except TypeError as exc:
                    raise TypeError("event_ids must contain only hashable values") from exc
        object.__setattr__(self, "event_ids", event_ids)

        self._validate_semantics(dimensions)

    @property
    def capacity(self) -> int:
        """Maximum number of events represented by these arrays."""

        return int(self.event_time.shape[0])

    @classmethod
    def from_configuration(
        cls,
        configuration: EventConfiguration,
        *,
        max_events: Optional[int] = None,
    ) -> "ReferenceTensor":
        """Encode a validated configuration without truncation or imputation."""

        if type(configuration) is not EventConfiguration:
            raise TypeError(
                "configuration must be an exact EventConfiguration instance"
            )
        configuration.validate()
        length = len(configuration)
        capacity = length if max_events is None else _capacity(max_events)
        if capacity < length:
            raise ValueError(
                "configuration has {} events and cannot fit capacity {}".format(
                    length, capacity
                )
            )

        event_time = np.zeros(capacity, dtype=np.float64)
        delta_time = np.zeros(capacity, dtype=np.float64)
        event_type = np.full(capacity, -1, dtype=np.int64)
        event_present = np.zeros(capacity, dtype=np.bool_)
        time_observed = np.zeros(capacity, dtype=np.bool_)
        type_observed = np.zeros(capacity, dtype=np.bool_)

        dimensions = _field_dimensions(configuration.schema)
        mark_values = {
            name: np.zeros((capacity, dimension), dtype=np.float64)
            for name, dimension in dimensions.items()
        }
        mark_applicable = {
            name: np.zeros((capacity, dimension), dtype=np.bool_)
            for name, dimension in dimensions.items()
        }
        mark_present = {
            name: np.zeros((capacity, dimension), dtype=np.bool_)
            for name, dimension in dimensions.items()
        }
        mark_observed = {
            name: np.zeros((capacity, dimension), dtype=np.bool_)
            for name, dimension in dimensions.items()
        }

        event_ids = [None] * capacity
        assert configuration.observed is not None
        for index, (event, observation) in enumerate(
            zip(configuration.events, configuration.observed.events)
        ):
            if event.event_type > _INT64_MAX:
                raise ValueError(
                    "ReferenceTensor requires active event type ids to fit "
                    "signed int64; use a declared dense vocabulary mapping"
                )
            event_time[index] = event.event_time
            event_type[index] = event.event_type
            event_present[index] = True
            time_observed[index] = observation.time_observed
            type_observed[index] = observation.type_observed
            event_ids[index] = event.event_id
            event_schema = configuration.schema.event_type(event.event_type)
            for field in event_schema.fields:
                native_slice = slice(0, field.dimension)
                mark_applicable[field.name][index, native_slice] = True
                if field.name in event.marks:
                    mark_values[field.name][index, native_slice] = event.marks[field.name]
                    mark_present[field.name][index, native_slice] = True
                if field.name in observation.observed_marks:
                    mark_observed[field.name][index, native_slice] = True

        if length:
            delta_time[0] = event_time[0]
            if length > 1:
                delta_time[1:length] = np.diff(event_time[:length])

        return cls(
            schema=configuration.schema,
            length=length,
            event_time=event_time,
            delta_time=delta_time,
            event_type=event_type,
            event_present=event_present,
            time_observed=time_observed,
            type_observed=type_observed,
            mark_values=mark_values,
            mark_applicable=mark_applicable,
            mark_present=mark_present,
            mark_observed=mark_observed,
            cardinality_observed=configuration.observed.cardinality_observed,
            event_ids=tuple(event_ids),
            sample_id=configuration.sample_id,
            group_id=configuration.group_id,
        )

    def _validate_semantics(self, dimensions: Mapping[str, int]) -> None:
        expected_event_present = np.arange(self.capacity) < self.length
        if not np.array_equal(self.event_present, expected_event_present):
            raise ValueError("event_present must be a contiguous prefix matching length")
        if np.any(~np.isfinite(self.event_time)):
            raise ValueError("event_time must contain only finite values")
        if np.any(~np.isfinite(self.delta_time)):
            raise ValueError("delta_time must contain only finite values")
        if np.any(self.event_time[self.length :] != 0.0):
            raise ValueError("padded event_time entries must be zero")
        if np.any(self.delta_time[self.length :] != 0.0):
            raise ValueError("padded delta_time entries must be zero")
        if np.any(self.event_type[self.length :] != -1):
            raise ValueError("padded event_type entries must be -1")
        if np.any(self.time_observed[self.length :]):
            raise ValueError("padded events cannot have observed times")
        if np.any(self.type_observed[self.length :]):
            raise ValueError("padded events cannot have observed types")
        if any(event_id is not None for event_id in self.event_ids[self.length :]):
            raise ValueError("padded events cannot have event ids")

        expected_delta = np.zeros(self.capacity, dtype=np.float64)
        if self.length:
            expected_delta[0] = self.event_time[0]
            if self.length > 1:
                expected_delta[1 : self.length] = np.diff(
                    self.event_time[: self.length]
                )
        if not np.array_equal(self.delta_time, expected_delta):
            raise ValueError("delta_time is inconsistent with event_time")

        expected_applicable = {
            name: np.zeros((self.capacity, dimension), dtype=np.bool_)
            for name, dimension in dimensions.items()
        }
        for index in range(self.length):
            type_id = int(self.event_type[index])
            try:
                event_schema = self.schema.event_type(type_id)
            except KeyError as exc:
                raise ValueError(
                    "active event {} uses unknown type id {}".format(index, type_id)
                ) from exc
            for field in event_schema.fields:
                expected_applicable[field.name][index, : field.dimension] = True

        events = []
        event_observations = []
        for field_name in dimensions:
            applicable = self.mark_applicable[field_name]
            present = self.mark_present[field_name]
            observed = self.mark_observed[field_name]
            values = self.mark_values[field_name]
            if not np.array_equal(applicable, expected_applicable[field_name]):
                raise ValueError(
                    "mark_applicable[{!r}] is inconsistent with event types".format(
                        field_name
                    )
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
            if np.any(~np.isfinite(values)):
                raise ValueError(
                    "mark_values[{!r}] must contain only finite values".format(
                        field_name
                    )
                )
            if np.any(values[~present] != 0.0):
                raise ValueError(
                    "mark_values[{!r}] must be zero where the mark is absent".format(
                        field_name
                    )
                )

        for index in range(self.length):
            event_schema = self.schema.event_type(int(self.event_type[index]))
            marks = {}
            observed_marks = set()
            for field in event_schema.fields:
                native_slice = slice(0, field.dimension)
                present = self.mark_present[field.name][index, native_slice]
                observed = self.mark_observed[field.name][index, native_slice]
                if np.any(present) and not np.all(present):
                    raise ValueError(
                        "mark_present[{!r}] must cover a complete native value".format(
                            field.name
                        )
                    )
                if np.any(observed) and not np.all(observed):
                    raise ValueError(
                        "mark_observed[{!r}] must cover a complete native value".format(
                            field.name
                        )
                    )
                if np.all(present):
                    marks[field.name] = tuple(
                        float(value)
                        for value in self.mark_values[field.name][index, native_slice]
                    )
                if np.all(observed):
                    observed_marks.add(field.name)
            events.append(
                Event(
                    event_time=float(self.event_time[index]),
                    event_type=int(self.event_type[index]),
                    marks=marks,
                    event_id=self.event_ids[index],
                )
            )
            event_observations.append(
                EventObservation(
                    time_observed=bool(self.time_observed[index]),
                    type_observed=bool(self.type_observed[index]),
                    observed_marks=frozenset(observed_marks),
                )
            )

        pattern = ObservationPattern(
            events=tuple(event_observations),
            cardinality_observed=self.cardinality_observed,
        )
        configuration = EventConfiguration(
            schema=self.schema,
            events=tuple(events),
            observed=pattern,
            sample_id=self.sample_id,
            group_id=self.group_id,
        )
        assert configuration.observed is not None
        input_keys = tuple(
            (event.model_key(), observation.signature_key())
            for event, observation in zip(events, event_observations)
        )
        output_keys = tuple(
            (event.model_key(), observation.signature_key())
            for event, observation in zip(
                configuration.events, configuration.observed.events
            )
        )
        if input_keys != output_keys:
            raise ValueError(
                "active event slots and aligned observations must be in "
                "canonical order"
            )

    def to_model_view(self) -> ObservationView:
        """Return the only supported model-conditioning view of this target.

        Hidden event slots, target alignment, applicability, padding, and
        unobserved cardinality are removed by ``ObservationPattern`` before
        this object leaves the data boundary.
        """

        configuration = self.to_configuration()
        assert configuration.observed is not None
        return configuration.observed.to_model_view(configuration)

    def to_configuration(self) -> EventConfiguration:
        """Decode the already validated active prefix into native events."""

        events = []
        observations = []
        for index in range(self.length):
            event_schema = self.schema.event_type(int(self.event_type[index]))
            marks = {}
            observed_marks = set()
            for field in event_schema.fields:
                native_slice = slice(0, field.dimension)
                if np.all(self.mark_present[field.name][index, native_slice]):
                    marks[field.name] = tuple(
                        float(value)
                        for value in self.mark_values[field.name][index, native_slice]
                    )
                if np.all(self.mark_observed[field.name][index, native_slice]):
                    observed_marks.add(field.name)
            events.append(
                Event(
                    event_time=float(self.event_time[index]),
                    event_type=int(self.event_type[index]),
                    marks=marks,
                    event_id=self.event_ids[index],
                )
            )
            observations.append(
                EventObservation(
                    time_observed=bool(self.time_observed[index]),
                    type_observed=bool(self.type_observed[index]),
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

    def __reduce__(self) -> Tuple[object, Tuple[object, ...]]:
        """Serialize through the validating constructor.

        ``MappingProxyType`` deliberately protects the field mappings at
        runtime but is not picklable.  The reducer emits ordinary mapping
        copies and reconstructs the tensor through ``__post_init__``, which
        restores both mapping proxies and bytes-backed read-only arrays.  This
        also prevents a pickle round trip from weakening immutability.  As
        with ordinary pickle, the schema and optional event-id sidecars must
        themselves be picklable.
        """

        return (
            ReferenceTensor,
            (
                self.schema,
                self.length,
                self.event_time,
                self.delta_time,
                self.event_type,
                self.event_present,
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


def configuration_to_reference_tensor(
    configuration: EventConfiguration,
    *,
    max_events: Optional[int] = None,
) -> ReferenceTensor:
    """Functional alias for :meth:`ReferenceTensor.from_configuration`."""

    return ReferenceTensor.from_configuration(
        configuration,
        max_events=max_events,
    )


def reference_tensor_to_configuration(tensor: ReferenceTensor) -> EventConfiguration:
    """Decode a validated :class:`ReferenceTensor`."""

    if not isinstance(tensor, ReferenceTensor):
        raise TypeError("tensor must be a ReferenceTensor")
    return tensor.to_configuration()


def reference_tensor_to_model_view(tensor: ReferenceTensor) -> ObservationView:
    """Return a non-aligned, non-leaking conditioning view of a target tensor."""

    if not isinstance(tensor, ReferenceTensor):
        raise TypeError("tensor must be a ReferenceTensor")
    return tensor.to_model_view()


__all__ = [
    "ReferenceTensor",
    "configuration_to_reference_tensor",
    "reference_tensor_to_configuration",
    "reference_tensor_to_model_view",
]
