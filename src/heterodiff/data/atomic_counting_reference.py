"""Immutable padded layouts for lossless atomic counting-grid targets.

This module is a deterministic representation adapter.  It defines neither a
probability distribution nor a learning model, objective, or empirical claim.
Native time atoms occupy the leading positions of a fixed reference axis and
the remaining positions are canonical right padding.  Occurrence slots are
serialization capacity only; construction rejects overflow instead of
truncating or aggregating occurrences.

Native mark values are retained for exact reconstruction.  A separate array
contains the deterministic schema-declared support transform of every present
mark.  Applicability, physical presence, source observation, occurrence
activity, and padding remain distinct.  Dataset and event identifiers are
stored only in provenance sidecars and are excluded from every digest and
public manifest returned by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from numbers import Integral
from typing import Dict, Hashable, Mapping, Optional, Protocol, Tuple

import numpy as np

from heterodiff.data.atomic_counting_grid import AtomicCountingGridTensor
from heterodiff.events.configuration import EventConfiguration
from heterodiff.events.schema import (
    ContinuousField,
    EventTypeSchema,
    FeatureSchema,
    MultiplicityMode,
    SupportKind,
    TimeMeasureKind,
    TimeReference,
)
from heterodiff.events.transforms import TransformError, transform_for_field


CoordinateAxis = Tuple[Tuple[str, int], ...]
EventIdGrid = Tuple[Tuple[Tuple[Optional[Hashable], ...], ...], ...]
MultiplicityHistogram = Tuple[Tuple[int, int], ...]

_LAYOUT_SCHEMA_VERSION = "heterodiff-atomic-counting-reference-layout-v1"
_STATE_SCHEMA_VERSION = "heterodiff-atomic-counting-reference-state-v1"


def _exact_positive_integer(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("{} must be an integer".format(name))
    result = int(value)
    if result <= 0:
        raise ValueError("{} must be positive".format(name))
    return result


def _validate_exact_schema_tree(schema: object) -> FeatureSchema:
    """Reject stateful subclasses and noncanonical post-construction edits."""

    if type(schema) is not FeatureSchema:
        raise TypeError("schema must be an exact FeatureSchema instance")
    if type(schema.event_types) is not tuple:
        raise TypeError("schema event_types must be an exact tuple")
    if type(schema.time_measure) is not TimeMeasureKind:
        raise TypeError("schema time_measure must be a TimeMeasureKind")
    if type(schema.multiplicity_mode) is not MultiplicityMode:
        raise TypeError("schema multiplicity_mode must be a MultiplicityMode")
    if type(schema.allow_simultaneous) is not bool:
        raise TypeError("schema allow_simultaneous must be a boolean")
    if type(schema.version) is not str:
        raise TypeError("schema version must be an exact string")
    if schema.horizon is not None and type(schema.horizon) is not float:
        raise TypeError("schema horizon must be a canonical float or None")

    reference = schema.time_reference
    if type(reference) is not TimeReference:
        raise TypeError("time_reference must be an exact TimeReference instance")
    if type(reference.kind) is not TimeMeasureKind:
        raise TypeError("time_reference kind must be a TimeMeasureKind")
    if type(reference.atoms) is not tuple or any(
        type(value) is not float for value in reference.atoms
    ):
        raise TypeError("time-reference atoms must be canonical floats")
    if type(reference.atom_weights) is not tuple or any(
        type(value) is not float for value in reference.atom_weights
    ):
        raise TypeError("time-reference weights must be canonical floats")
    if type(reference.continuous_weight) is not float:
        raise TypeError("continuous time weight must be a canonical float")

    for event_type in schema.event_types:
        if type(event_type) is not EventTypeSchema:
            raise TypeError(
                "event_types must contain only exact EventTypeSchema instances"
            )
        if type(event_type.type_id) is not int:
            raise TypeError("event type ids must be canonical integers")
        if type(event_type.name) is not str:
            raise TypeError("event type names must be exact strings")
        if type(event_type.fields) is not tuple:
            raise TypeError("event-type fields must be an exact tuple")
        for field in event_type.fields:
            if type(field) is not ContinuousField:
                raise TypeError(
                    "event-type fields must contain only exact ContinuousField "
                    "instances"
                )
            if type(field.name) is not str:
                raise TypeError("field names must be exact strings")
            if type(field.dimension) is not int:
                raise TypeError("field dimensions must be canonical integers")
            if type(field.support) is not SupportKind:
                raise TypeError("field support must be a SupportKind")
            if field.lower is not None and type(field.lower) is not float:
                raise TypeError("field lower bounds must be canonical floats")
            if field.upper is not None and type(field.upper) is not float:
                raise TypeError("field upper bounds must be canonical floats")
            if field.unit is not None and type(field.unit) is not str:
                raise TypeError("field units must be exact strings or None")
    return schema


def _snapshot_schema(schema: object) -> FeatureSchema:
    """Return an exact detached schema after fail-closed tree validation."""

    source = _validate_exact_schema_tree(schema)
    assert source.time_reference is not None
    reference = TimeReference(
        kind=source.time_reference.kind,
        atoms=source.time_reference.atoms,
        atom_weights=source.time_reference.atom_weights,
        continuous_weight=source.time_reference.continuous_weight,
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
        for event_type in source.event_types
    )
    return FeatureSchema(
        event_types=event_types,
        horizon=source.horizon,
        time_measure=source.time_measure,
        time_reference=reference,
        allow_simultaneous=source.allow_simultaneous,
        version=source.version,
        multiplicity_mode=source.multiplicity_mode,
    )


def _canonical_json_bytes(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise TypeError("value is not canonical-JSON serializable") from exc
    return text.encode("utf-8")


def _domain_digest(domain: str, value: object) -> str:
    payload = _canonical_json_bytes(value)
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _schema_payload(schema: FeatureSchema) -> Mapping[str, object]:
    assert schema.time_reference is not None
    return {
        "allow_simultaneous": schema.allow_simultaneous,
        "event_types": [
            {
                "fields": [
                    {
                        "dimension": field.dimension,
                        "lower": field.lower,
                        "name": field.name,
                        "support": field.support.value,
                        "unit": field.unit,
                        "upper": field.upper,
                    }
                    for field in event_type.fields
                ],
                "name": event_type.name,
                "type_id": event_type.type_id,
            }
            for event_type in schema.event_types
        ],
        "horizon": schema.horizon,
        "multiplicity_mode": schema.multiplicity_mode.value,
        "time_measure": schema.time_measure.value,
        "time_reference": {
            "atom_weights": list(schema.time_reference.atom_weights),
            "atoms": list(schema.time_reference.atoms),
            "continuous_weight": schema.time_reference.continuous_weight,
            "kind": schema.time_reference.kind.value,
        },
        "version": schema.version,
    }


def _coordinate_axes(schema: FeatureSchema) -> Tuple[CoordinateAxis, CoordinateAxis]:
    native_dimensions: Dict[str, int] = {}
    transformed_dimensions: Dict[str, int] = {}
    for event_type in schema.event_types:
        for field in event_type.fields:
            native_dimensions[field.name] = max(
                native_dimensions.get(field.name, 0), field.dimension
            )
            transformed_dimensions[field.name] = max(
                transformed_dimensions.get(field.name, 0),
                field.transformed_dimension,
            )
    native = tuple(
        (name, coordinate)
        for name in sorted(native_dimensions)
        for coordinate in range(native_dimensions[name])
    )
    transformed = tuple(
        (name, coordinate)
        for name in sorted(transformed_dimensions)
        for coordinate in range(transformed_dimensions[name])
    )
    return native, transformed


def _immutable_array(
    value: object,
    *,
    name: str,
    dtype: np.dtype,
    shape: Tuple[int, ...],
) -> np.ndarray:
    if type(value) is not np.ndarray:
        raise TypeError("{} must be an exact NumPy array".format(name))
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
        if np.any(~np.isfinite(contiguous)):
            raise ValueError("{} must contain only finite values".format(name))
        contiguous[contiguous == 0.0] = 0.0
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=dtype).reshape(shape)


def _safe_sidecar(value: object, *, name: str) -> Optional[Hashable]:
    """Copy recursively immutable identifier values and reject opaque objects."""

    if value is None:
        return None
    if type(value) in (str, bytes, int, bool):
        return value  # type: ignore[return-value]
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("{} cannot contain nonfinite floats".format(name))
        return 0.0 if value == 0.0 else value
    if type(value) is tuple:
        return tuple(
            _safe_sidecar(item, name=name) for item in value
        )  # type: ignore[return-value]
    if type(value) is frozenset:
        return frozenset(
            _safe_sidecar(item, name=name) for item in value
        )  # type: ignore[return-value]
    raise TypeError(
        "{} must contain only recursively immutable built-in identifiers".format(name)
    )


def _freeze_event_ids(
    value: object,
    *,
    reference_length: int,
    number_of_types: int,
    slot_capacity: int,
) -> EventIdGrid:
    if type(value) is not tuple or len(value) != reference_length:
        raise ValueError(
            "event_ids must have one exact tuple row per reference position"
        )
    rows = []
    for row in value:
        if type(row) is not tuple or len(row) != number_of_types:
            raise ValueError("event_ids rows must match the event-type axis")
        type_rows = []
        for slots in row:
            if type(slots) is not tuple or len(slots) != slot_capacity:
                raise ValueError("event_ids cells must match the slot capacity")
            type_rows.append(
                tuple(_safe_sidecar(item, name="event_ids") for item in slots)
            )
        rows.append(tuple(type_rows))
    return tuple(rows)


def _positions(reference_length: int) -> np.ndarray:
    return np.asarray(
        [
            2.0 * float(position) / float(reference_length - 1) - 1.0
            for position in range(reference_length)
        ],
        dtype=np.float64,
    )


class _HashWriter(Protocol):
    def update(self, data: bytes) -> object:
        ...


def _array_digest_update(digest: _HashWriter, name: str, array: np.ndarray) -> None:
    metadata = {
        "dtype": array.dtype.str,
        "name": name,
        "shape": list(array.shape),
    }
    encoded = _canonical_json_bytes(metadata)
    digest.update(len(encoded).to_bytes(8, "big"))
    digest.update(encoded)
    raw = array.tobytes(order="C")
    digest.update(len(raw).to_bytes(8, "big"))
    digest.update(raw)


@dataclass(frozen=True, eq=False)
class CountingReferenceLayout:
    """Frozen schema, fixed reference length, and occurrence-slot capacity.

    This is layout metadata only.  It makes no probability, architecture,
    objective, or empirical assertion.
    """

    schema: FeatureSchema
    reference_length: int
    slot_capacity: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema", _snapshot_schema(self.schema))
        if self.schema.time_measure is not TimeMeasureKind.ATOMIC:
            raise ValueError("CountingReferenceLayout requires an atomic schema")
        reference_length = _exact_positive_integer(
            self.reference_length, name="reference_length"
        )
        if reference_length < 2:
            raise ValueError("reference_length must be at least two")
        slot_capacity = _exact_positive_integer(
            self.slot_capacity, name="slot_capacity"
        )
        if reference_length < self.native_atom_count:
            raise ValueError(
                "reference_length {} cannot fit {} native time atoms".format(
                    reference_length, self.native_atom_count
                )
            )
        object.__setattr__(self, "reference_length", reference_length)
        object.__setattr__(self, "slot_capacity", slot_capacity)

    @classmethod
    def from_tensor(
        cls,
        tensor: AtomicCountingGridTensor,
        *,
        reference_length: int,
        slot_capacity: Optional[int] = None,
    ) -> "CountingReferenceLayout":
        """Create a detached layout and reject any occurrence-capacity overflow."""

        if type(tensor) is not AtomicCountingGridTensor:
            raise TypeError("tensor must be an exact AtomicCountingGridTensor instance")
        _validate_exact_schema_tree(tensor.schema)
        capacity = tensor.slot_capacity if slot_capacity is None else slot_capacity
        layout = cls(tensor.schema, reference_length, capacity)
        if tensor.maximum_cell_multiplicity > layout.slot_capacity:
            raise ValueError(
                "tensor requires cell capacity {}; layout capacity {} would "
                "truncate occurrences".format(
                    tensor.maximum_cell_multiplicity, layout.slot_capacity
                )
            )
        return layout

    @property
    def native_atom_count(self) -> int:
        assert self.schema.time_reference is not None
        return len(self.schema.time_reference.atoms)

    @property
    def number_of_types(self) -> int:
        return len(self.schema.event_types)

    @property
    def type_ids(self) -> Tuple[int, ...]:
        return tuple(event_type.type_id for event_type in self.schema.event_types)

    @property
    def field_coordinates(self) -> CoordinateAxis:
        return _coordinate_axes(self.schema)[0]

    @property
    def transformed_coordinates(self) -> CoordinateAxis:
        return _coordinate_axes(self.schema)[1]

    @property
    def schema_digest(self) -> str:
        return _domain_digest(
            "heterodiff.atomic-counting-reference.schema.v1",
            _schema_payload(self.schema),
        )

    @property
    def layout_digest(self) -> str:
        return _domain_digest(
            "heterodiff.atomic-counting-reference.layout.v1",
            {
                "field_coordinates": [list(item) for item in self.field_coordinates],
                "native_atom_count": self.native_atom_count,
                "reference_length": self.reference_length,
                "schema_digest": self.schema_digest,
                "schema_version": _LAYOUT_SCHEMA_VERSION,
                "slot_capacity": self.slot_capacity,
                "transformed_coordinates": [
                    list(item) for item in self.transformed_coordinates
                ],
                "type_ids": list(self.type_ids),
            },
        )

    def encode(self, tensor: AtomicCountingGridTensor) -> "EncodedCountingReference":
        """Encode a matching grid with canonical right padding and no truncation."""

        if type(self) is not CountingReferenceLayout:
            raise TypeError("layout must be an exact CountingReferenceLayout instance")
        if type(tensor) is not AtomicCountingGridTensor:
            raise TypeError("tensor must be an exact AtomicCountingGridTensor instance")
        tensor_schema = _snapshot_schema(tensor.schema)
        if (
            _domain_digest(
                "heterodiff.atomic-counting-reference.schema.v1",
                _schema_payload(tensor_schema),
            )
            != self.schema_digest
        ):
            raise ValueError("tensor schema does not match the frozen layout")
        # Re-run the grid's complete public validation before reading arrays.
        tensor.to_configuration()
        if tensor.maximum_cell_multiplicity > self.slot_capacity:
            raise ValueError(
                "tensor requires cell capacity {}; layout capacity {} would "
                "truncate occurrences".format(
                    tensor.maximum_cell_multiplicity, self.slot_capacity
                )
            )

        r = self.reference_length
        a = self.native_atom_count
        k = self.number_of_types
        s = self.slot_capacity
        f = len(self.field_coordinates)
        d = len(self.transformed_coordinates)
        grid_shape = (r, k, s)
        field_shape = grid_shape + (f,)
        transformed_shape = grid_shape + (d,)

        exact_counts = np.zeros((r, k), dtype=np.int64)
        exact_counts[:a] = tensor.cell_counts
        occurrence_present = np.zeros(grid_shape, dtype=np.bool_)
        time_observed = np.zeros(grid_shape, dtype=np.bool_)
        type_observed = np.zeros(grid_shape, dtype=np.bool_)
        native_mark_values = np.zeros(field_shape, dtype=np.float64)
        clean_presence = np.zeros(field_shape, dtype=np.bool_)
        structural_applicability = np.zeros(field_shape, dtype=np.bool_)
        source_observed = np.zeros(field_shape, dtype=np.bool_)
        transformed_mark_values = np.zeros(transformed_shape, dtype=np.float64)
        transformed_clean_presence = np.zeros(transformed_shape, dtype=np.bool_)
        transformed_structural_applicability = np.zeros(
            transformed_shape, dtype=np.bool_
        )
        transformed_source_observed = np.zeros(transformed_shape, dtype=np.bool_)

        event_ids = [[[None for _ in range(s)] for _ in range(k)] for _ in range(r)]
        native_index = {
            coordinate: index for index, coordinate in enumerate(self.field_coordinates)
        }
        transformed_index = {
            coordinate: index
            for index, coordinate in enumerate(self.transformed_coordinates)
        }

        for atom_index in range(a):
            for type_index, event_type in enumerate(self.schema.event_types):
                count = int(exact_counts[atom_index, type_index])
                for slot in range(count):
                    occurrence_present[atom_index, type_index, slot] = True
                    time_observed[atom_index, type_index, slot] = bool(
                        tensor.time_observed[atom_index, type_index, slot]
                    )
                    type_observed[atom_index, type_index, slot] = bool(
                        tensor.type_observed[atom_index, type_index, slot]
                    )
                    event_ids[atom_index][type_index][slot] = tensor.event_ids[
                        atom_index
                    ][type_index][slot]
                    for field in event_type.fields:
                        native_indices = tuple(
                            native_index[(field.name, coordinate)]
                            for coordinate in range(field.dimension)
                        )
                        native_value = np.asarray(
                            [
                                tensor.mark_values[field.name][
                                    atom_index, type_index, slot, coordinate
                                ]
                                for coordinate in range(field.dimension)
                            ],
                            dtype=np.float64,
                        )
                        applicable = tensor.mark_applicable[field.name][
                            atom_index, type_index, slot, : field.dimension
                        ]
                        present = tensor.mark_present[field.name][
                            atom_index, type_index, slot, : field.dimension
                        ]
                        observed = tensor.mark_observed[field.name][
                            atom_index, type_index, slot, : field.dimension
                        ]
                        native_mark_values[
                            atom_index, type_index, slot, native_indices
                        ] = native_value
                        structural_applicability[
                            atom_index, type_index, slot, native_indices
                        ] = applicable
                        clean_presence[
                            atom_index, type_index, slot, native_indices
                        ] = present
                        source_observed[
                            atom_index, type_index, slot, native_indices
                        ] = observed

                        transformed_indices = tuple(
                            transformed_index[(field.name, coordinate)]
                            for coordinate in range(field.transformed_dimension)
                        )
                        transformed_structural_applicability[
                            atom_index, type_index, slot, transformed_indices
                        ] = True
                        if bool(np.all(present)):
                            transformed = transform_for_field(field).forward(
                                native_value.reshape(1, field.dimension)
                            )[0]
                            transformed_mark_values[
                                atom_index, type_index, slot, transformed_indices
                            ] = transformed
                            transformed_clean_presence[
                                atom_index, type_index, slot, transformed_indices
                            ] = True
                        if bool(np.all(observed)):
                            transformed_source_observed[
                                atom_index, type_index, slot, transformed_indices
                            ] = True

        valid_time_mask = np.zeros(r, dtype=np.bool_)
        valid_time_mask[:a] = True
        return EncodedCountingReference(
            layout=self,
            exact_counts=exact_counts,
            occurrence_present=occurrence_present,
            clean_presence=clean_presence,
            native_mark_values=native_mark_values,
            transformed_mark_values=transformed_mark_values,
            structural_applicability=structural_applicability,
            source_observed=source_observed,
            transformed_clean_presence=transformed_clean_presence,
            transformed_structural_applicability=(transformed_structural_applicability),
            transformed_source_observed=transformed_source_observed,
            time_observed=time_observed,
            type_observed=type_observed,
            cardinality_observed=tensor.cardinality_observed,
            valid_time_mask=valid_time_mask,
            position_coordinates=_positions(r),
            event_ids=tuple(tuple(tuple(slots) for slots in row) for row in event_ids),
            sample_id=tensor.sample_id,
            group_id=tensor.group_id,
        )

    def __reduce__(self) -> Tuple[object, Tuple[object, ...]]:
        return (
            CountingReferenceLayout,
            (self.schema, self.reference_length, self.slot_capacity),
        )


@dataclass(frozen=True, eq=False)
class EncodedCountingReference:
    """Validated padded arrays plus reconstruction-only provenance sidecars.

    The object is a serialization and support-transform boundary.  It makes no
    probability, architecture, objective, or empirical assertion.
    """

    layout: CountingReferenceLayout
    exact_counts: np.ndarray
    occurrence_present: np.ndarray
    clean_presence: np.ndarray
    native_mark_values: np.ndarray
    transformed_mark_values: np.ndarray
    structural_applicability: np.ndarray
    source_observed: np.ndarray
    transformed_clean_presence: np.ndarray
    transformed_structural_applicability: np.ndarray
    transformed_source_observed: np.ndarray
    time_observed: np.ndarray
    type_observed: np.ndarray
    cardinality_observed: bool
    valid_time_mask: np.ndarray
    position_coordinates: np.ndarray
    event_ids: EventIdGrid
    sample_id: str = ""
    group_id: str = ""

    def __post_init__(self) -> None:
        if type(self.layout) is not CountingReferenceLayout:
            raise TypeError("layout must be an exact CountingReferenceLayout instance")
        layout = CountingReferenceLayout(
            self.layout.schema,
            self.layout.reference_length,
            self.layout.slot_capacity,
        )
        object.__setattr__(self, "layout", layout)
        r = layout.reference_length
        k = layout.number_of_types
        s = layout.slot_capacity
        f = len(layout.field_coordinates)
        d = len(layout.transformed_coordinates)
        grid_shape = (r, k, s)
        field_shape = grid_shape + (f,)
        transformed_shape = grid_shape + (d,)
        int_dtype = np.dtype(np.int64)
        bool_dtype = np.dtype(np.bool_)
        float_dtype = np.dtype(np.float64)

        object.__setattr__(
            self,
            "exact_counts",
            _immutable_array(
                self.exact_counts,
                name="exact_counts",
                dtype=int_dtype,
                shape=(r, k),
            ),
        )
        for name, shape in (
            ("occurrence_present", grid_shape),
            ("clean_presence", field_shape),
            ("structural_applicability", field_shape),
            ("source_observed", field_shape),
            ("transformed_clean_presence", transformed_shape),
            ("transformed_structural_applicability", transformed_shape),
            ("transformed_source_observed", transformed_shape),
            ("time_observed", grid_shape),
            ("type_observed", grid_shape),
            ("valid_time_mask", (r,)),
        ):
            object.__setattr__(
                self,
                name,
                _immutable_array(
                    getattr(self, name), name=name, dtype=bool_dtype, shape=shape
                ),
            )
        for name, shape in (
            ("native_mark_values", field_shape),
            ("transformed_mark_values", transformed_shape),
            ("position_coordinates", (r,)),
        ):
            object.__setattr__(
                self,
                name,
                _immutable_array(
                    getattr(self, name), name=name, dtype=float_dtype, shape=shape
                ),
            )
        if type(self.cardinality_observed) is not bool:
            raise TypeError("cardinality_observed must be a boolean")
        if type(self.sample_id) is not str or type(self.group_id) is not str:
            raise TypeError("sample_id and group_id must be exact strings")
        object.__setattr__(
            self,
            "event_ids",
            _freeze_event_ids(
                self.event_ids,
                reference_length=r,
                number_of_types=k,
                slot_capacity=s,
            ),
        )
        self._validate_semantics()

    @property
    def schema(self) -> FeatureSchema:
        return self.layout.schema

    @property
    def schema_digest(self) -> str:
        return self.layout.schema_digest

    @property
    def layout_digest(self) -> str:
        return self.layout.layout_digest

    @property
    def cardinality(self) -> int:
        return sum(int(value) for value in self.exact_counts.flat)

    @property
    def occupied_cell_multiplicity_histogram(self) -> MultiplicityHistogram:
        native = self.exact_counts[: self.layout.native_atom_count]
        positive = native[native > 0]
        if not positive.size:
            return ()
        values, frequencies = np.unique(positive, return_counts=True)
        return tuple(
            (int(value), int(frequency))
            for value, frequency in zip(values, frequencies)
        )

    def _validate_semantics(self) -> None:
        layout = self.layout
        r = layout.reference_length
        a = layout.native_atom_count
        k = layout.number_of_types
        s = layout.slot_capacity
        expected_valid = np.zeros(r, dtype=np.bool_)
        expected_valid[:a] = True
        if not np.array_equal(self.valid_time_mask, expected_valid):
            raise ValueError(
                "valid_time_mask must be true exactly on the native leading prefix"
            )
        if not np.array_equal(self.position_coordinates, _positions(r)):
            raise ValueError("position_coordinates must equal 2*r/(R-1)-1 exactly")
        if np.any(self.exact_counts < 0):
            raise ValueError("exact_counts must be nonnegative")
        if np.any(self.exact_counts > s):
            raise ValueError("exact_counts cannot exceed slot capacity")
        if np.any(self.exact_counts[a:] != 0):
            raise ValueError("padded counts must be canonical zero")

        expected_occurrence = np.zeros((r, k, s), dtype=np.bool_)
        for atom_index in range(a):
            for type_index in range(k):
                expected_occurrence[
                    atom_index,
                    type_index,
                    : int(self.exact_counts[atom_index, type_index]),
                ] = True
        if not np.array_equal(self.occurrence_present, expected_occurrence):
            raise ValueError(
                "occurrence_present must be the active prefix determined by counts"
            )
        if np.any(self.time_observed & ~expected_occurrence):
            raise ValueError("inactive occurrences cannot have source-observed times")
        if np.any(self.type_observed & ~expected_occurrence):
            raise ValueError("inactive occurrences cannot have source-observed types")

        native_index = {
            coordinate: index
            for index, coordinate in enumerate(layout.field_coordinates)
        }
        transformed_index = {
            coordinate: index
            for index, coordinate in enumerate(layout.transformed_coordinates)
        }
        expected_native_applicable = np.zeros_like(self.structural_applicability)
        expected_transformed_applicable = np.zeros_like(
            self.transformed_structural_applicability
        )
        expected_transformed_values = np.zeros_like(self.transformed_mark_values)
        expected_transformed_presence = np.zeros_like(self.transformed_clean_presence)
        expected_transformed_observed = np.zeros_like(self.transformed_source_observed)

        for atom_index in range(a):
            for type_index, event_type in enumerate(layout.schema.event_types):
                for slot in range(s):
                    active = bool(expected_occurrence[atom_index, type_index, slot])
                    if not active:
                        continue
                    for field in event_type.fields:
                        native_indices = tuple(
                            native_index[(field.name, coordinate)]
                            for coordinate in range(field.dimension)
                        )
                        transformed_indices = tuple(
                            transformed_index[(field.name, coordinate)]
                            for coordinate in range(field.transformed_dimension)
                        )
                        expected_native_applicable[
                            atom_index, type_index, slot, native_indices
                        ] = True
                        expected_transformed_applicable[
                            atom_index, type_index, slot, transformed_indices
                        ] = True

                        present = self.clean_presence[
                            atom_index, type_index, slot, native_indices
                        ]
                        observed = self.source_observed[
                            atom_index, type_index, slot, native_indices
                        ]
                        if np.any(present) and not np.all(present):
                            raise ValueError(
                                "clean_presence must cover a complete native field"
                            )
                        if np.any(observed) and not np.all(observed):
                            raise ValueError(
                                "source_observed must cover a complete native field"
                            )
                        if np.any(observed & ~present):
                            raise ValueError(
                                "source-observed coordinates must be physically present"
                            )
                        if bool(np.all(present)):
                            native = self.native_mark_values[
                                atom_index, type_index, slot, native_indices
                            ]
                            canonical = np.asarray(
                                field.coerce_value(native), dtype=np.float64
                            )
                            if not np.array_equal(native, canonical):
                                raise ValueError(
                                    "native_mark_values are not canonical support values"
                                )
                            transform = transform_for_field(field)
                            transformed = transform.forward(
                                native.reshape(1, field.dimension)
                            )[0]
                            expected_transformed_values[
                                atom_index, type_index, slot, transformed_indices
                            ] = transformed
                            expected_transformed_presence[
                                atom_index, type_index, slot, transformed_indices
                            ] = True
                            try:
                                inverse = transform.inverse(
                                    transformed.reshape(1, field.transformed_dimension)
                                )[0]
                            except TransformError as exc:
                                raise ValueError(
                                    "support transform cannot invert a present value"
                                ) from exc
                            field.coerce_value(inverse)
                            tolerance = 128.0 * np.finfo(np.float64).eps
                            absolute_tolerance = 0.0
                            if field.support is SupportKind.BOUNDED:
                                assert (
                                    field.lower is not None and field.upper is not None
                                )
                                absolute_tolerance = tolerance * (
                                    field.upper - field.lower
                                )
                            elif field.support is SupportKind.SIMPLEX:
                                absolute_tolerance = tolerance
                            if not np.allclose(
                                inverse,
                                native,
                                rtol=tolerance,
                                atol=absolute_tolerance,
                            ):
                                raise ValueError(
                                    "support transform does not round-trip a present value"
                                )
                        if bool(np.all(observed)):
                            expected_transformed_observed[
                                atom_index, type_index, slot, transformed_indices
                            ] = True

        if not np.array_equal(
            self.structural_applicability, expected_native_applicable
        ):
            raise ValueError(
                "structural_applicability disagrees with schema and occurrence state"
            )
        if np.any(self.clean_presence & ~self.structural_applicability):
            raise ValueError("clean_presence includes inapplicable coordinates")
        if np.any(self.source_observed & ~self.clean_presence):
            raise ValueError("source_observed includes absent coordinates")
        if np.any(self.native_mark_values[~self.clean_presence] != 0.0):
            raise ValueError("native_mark_values must be zero outside clean presence")
        if not np.array_equal(
            self.transformed_structural_applicability,
            expected_transformed_applicable,
        ):
            raise ValueError(
                "transformed applicability disagrees with schema and occurrence state"
            )
        if not np.array_equal(
            self.transformed_clean_presence, expected_transformed_presence
        ):
            raise ValueError(
                "transformed clean presence disagrees with native clean presence"
            )
        if not np.array_equal(
            self.transformed_source_observed, expected_transformed_observed
        ):
            raise ValueError(
                "transformed source observation disagrees with native observation"
            )
        if not np.array_equal(
            self.transformed_mark_values, expected_transformed_values
        ):
            raise ValueError(
                "transformed_mark_values are not the declared support transforms"
            )

        seen_event_ids = set()
        for atom_index in range(r):
            for type_index in range(k):
                for slot in range(s):
                    event_id = self.event_ids[atom_index][type_index][slot]
                    if (
                        not expected_occurrence[atom_index, type_index, slot]
                        and event_id is not None
                    ):
                        raise ValueError(
                            "inactive occurrence slots cannot contain provenance ids"
                        )
                    if (
                        expected_occurrence[atom_index, type_index, slot]
                        and event_id is not None
                    ):
                        if event_id in seen_event_ids:
                            raise ValueError(
                                "non-null provenance event ids must be unique"
                            )
                        seen_event_ids.add(event_id)

    @property
    def state_digest(self) -> str:
        """Digest all identifier-free target and source-observation arrays."""

        digest = hashlib.sha256()
        digest.update(b"heterodiff.atomic-counting-reference.state.v1\x00")
        header = _canonical_json_bytes(
            {
                "cardinality_observed": self.cardinality_observed,
                "layout_digest": self.layout_digest,
                "schema_version": _STATE_SCHEMA_VERSION,
            }
        )
        digest.update(len(header).to_bytes(8, "big"))
        digest.update(header)
        for name in (
            "exact_counts",
            "occurrence_present",
            "clean_presence",
            "native_mark_values",
            "transformed_mark_values",
            "structural_applicability",
            "source_observed",
            "transformed_clean_presence",
            "transformed_structural_applicability",
            "transformed_source_observed",
            "time_observed",
            "type_observed",
            "valid_time_mask",
            "position_coordinates",
        ):
            _array_digest_update(digest, name, getattr(self, name))
        return digest.hexdigest()

    def public_manifest(self) -> Mapping[str, object]:
        """Return identifier-free shape, digest, and count metadata."""

        return {
            "cardinality": self.cardinality,
            "field_coordinate_count": len(self.layout.field_coordinates),
            "layout_digest": self.layout_digest,
            "multiplicity_histogram": [
                {"cell_count": count, "multiplicity": multiplicity}
                for multiplicity, count in self.occupied_cell_multiplicity_histogram
            ],
            "native_atom_count": self.layout.native_atom_count,
            "reference_length": self.layout.reference_length,
            "schema_digest": self.schema_digest,
            "schema_version": _STATE_SCHEMA_VERSION,
            "slot_capacity": self.layout.slot_capacity,
            "state_digest": self.state_digest,
            "transformed_coordinate_count": len(self.layout.transformed_coordinates),
            "type_count": self.layout.number_of_types,
        }

    def to_atomic_counting_grid_tensor(self) -> AtomicCountingGridTensor:
        """Remove right padding and reconstruct a validated native grid tensor."""

        if type(self) is not EncodedCountingReference:
            raise TypeError(
                "reference must be an exact EncodedCountingReference instance"
            )
        self._validate_semantics()
        a = self.layout.native_atom_count
        k = self.layout.number_of_types
        s = self.layout.slot_capacity
        grid_shape = (a, k, s)
        dimensions: Dict[str, int] = {}
        for event_type in self.schema.event_types:
            for field in event_type.fields:
                dimensions[field.name] = max(
                    dimensions.get(field.name, 0), field.dimension
                )
        native_index = {
            coordinate: index
            for index, coordinate in enumerate(self.layout.field_coordinates)
        }
        mark_values = {
            name: np.zeros(grid_shape + (dimension,), dtype=np.float64)
            for name, dimension in sorted(dimensions.items())
        }
        mark_applicable = {
            name: np.zeros(grid_shape + (dimension,), dtype=np.bool_)
            for name, dimension in sorted(dimensions.items())
        }
        mark_present = {
            name: np.zeros(grid_shape + (dimension,), dtype=np.bool_)
            for name, dimension in sorted(dimensions.items())
        }
        mark_observed = {
            name: np.zeros(grid_shape + (dimension,), dtype=np.bool_)
            for name, dimension in sorted(dimensions.items())
        }
        for name, dimension in sorted(dimensions.items()):
            indices = tuple(
                native_index[(name, coordinate)] for coordinate in range(dimension)
            )
            mark_values[name][...] = self.native_mark_values[:a, :, :, indices]
            mark_applicable[name][...] = self.structural_applicability[
                :a, :, :, indices
            ]
            mark_present[name][...] = self.clean_presence[:a, :, :, indices]
            mark_observed[name][...] = self.source_observed[:a, :, :, indices]
        return AtomicCountingGridTensor(
            schema=self.schema,
            cell_counts=self.exact_counts[:a].copy(),
            occurrence_present=self.occurrence_present[:a].copy(),
            time_observed=self.time_observed[:a].copy(),
            type_observed=self.type_observed[:a].copy(),
            mark_values=mark_values,
            mark_applicable=mark_applicable,
            mark_present=mark_present,
            mark_observed=mark_observed,
            cardinality_observed=self.cardinality_observed,
            event_ids=tuple(
                tuple(tuple(slots) for slots in row) for row in self.event_ids[:a]
            ),
            sample_id=self.sample_id,
            group_id=self.group_id,
        )

    def to_configuration(self) -> EventConfiguration:
        """Decode the native event configuration and aligned source observations."""

        return self.to_atomic_counting_grid_tensor().to_configuration()

    def __reduce__(self) -> Tuple[object, Tuple[object, ...]]:
        return (
            EncodedCountingReference,
            (
                self.layout,
                self.exact_counts,
                self.occurrence_present,
                self.clean_presence,
                self.native_mark_values,
                self.transformed_mark_values,
                self.structural_applicability,
                self.source_observed,
                self.transformed_clean_presence,
                self.transformed_structural_applicability,
                self.transformed_source_observed,
                self.time_observed,
                self.type_observed,
                self.cardinality_observed,
                self.valid_time_mask,
                self.position_coordinates,
                self.event_ids,
                self.sample_id,
                self.group_id,
            ),
        )


def encode_atomic_counting_reference(
    tensor: AtomicCountingGridTensor,
    *,
    reference_length: int,
    slot_capacity: Optional[int] = None,
) -> EncodedCountingReference:
    """Construct a layout and encode one exact atomic counting-grid tensor."""

    layout = CountingReferenceLayout.from_tensor(
        tensor,
        reference_length=reference_length,
        slot_capacity=slot_capacity,
    )
    return layout.encode(tensor)


__all__ = [
    "CoordinateAxis",
    "CountingReferenceLayout",
    "EncodedCountingReference",
    "EventIdGrid",
    "MultiplicityHistogram",
    "encode_atomic_counting_reference",
]
