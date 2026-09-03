"""Capability-driven execution of complete adapter conformance checks.

The runner is deliberately domain neutral.  It snapshots one adapter
descriptor and schema, derives an immutable plan solely from the declared
capabilities, validates the complete evidence bundle, and executes only the
representation round trips advertised by that capability record.

This is Phase-C development infrastructure.  Its identifiers and result
schema are not decision-bearing until the mandatory A9.1 protocol freeze.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from collections import Counter
from types import MappingProxyType
from typing import Optional, Protocol, Tuple, runtime_checkable

import numpy as np

from heterodiff.events import EventConfiguration, FeatureSchema

from . import adapter_contract as _contract
from . import adapter_evidence as _evidence
from .adapter_conformance_plan import (
    CheckMode,
    ConformancePlan,
    MAXIMUM_REPRESENTATION_IDS,
    PlanCheck,
    plan_from_capabilities,
)
from .adapter_contract import (
    ATOMIC_COUNTING_GRID_REPRESENTATION_ID,
    AdapterCapabilities,
    AdapterContractError,
    AdapterDescriptor,
    AdaptedEventSample,
    NativeEventAdapter,
    SamplePartition,
    SplitManifest,
)
from .atomic_counting_grid import AtomicCountingGridTensor
from .adapter_evidence import (
    AdapterEvidenceResourceError,
    CompleteAdaptedEventSample,
    ExpectedAdapterEvidence,
    MAXIMUM_SOURCE_BYTES,
    expected_adapter_evidence_digest,
    snapshot_bounded_native_configuration,
    snapshot_bounded_schema,
    snapshot_bounded_split_manifest,
    validate_complete_adapted_event_sample,
)


MAXIMUM_ATOMIC_GRID_CELLS = 65536
MAXIMUM_ATOMIC_GRID_SERIALIZATION_SLOTS = 131072
MAXIMUM_ATOMIC_GRID_MARK_SCALARS = 2097152
MAXIMUM_OCCURRENCES_PER_ATOMIC_CELL = 64


class ConformanceStatus(str, Enum):
    """Terminal status of one planned check in a successful run."""

    PASS = "pass"
    HOOK_ROUNDTRIP = "hook_roundtrip_only"
    NOT_APPLICABLE = "not_applicable"


class RunnerConformanceCode(str, Enum):
    """Stable machine-readable failures owned by the shared runner."""

    ADAPTER_PROTOCOL_INVALID = "ADAPTER_PROTOCOL_INVALID"
    INPUT_SNAPSHOT_INVALID = "INPUT_SNAPSHOT_INVALID"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    ADAPTER_SNAPSHOT_INVALID = "ADAPTER_SNAPSHOT_INVALID"
    REPRESENTATION_PROTOCOL_MISSING = "REPRESENTATION_PROTOCOL_MISSING"
    REPRESENTATION_ENCODE_FAILED = "REPRESENTATION_ENCODE_FAILED"
    REPRESENTATION_DECODE_FAILED = "REPRESENTATION_DECODE_FAILED"
    REPRESENTATION_PAYLOAD_INVALID = "REPRESENTATION_PAYLOAD_INVALID"
    REPRESENTATION_ROUNDTRIP_MISMATCH = (
        "REPRESENTATION_ROUNDTRIP_MISMATCH"
    )


class RunnerConformanceError(AdapterContractError):
    """One coded failure from capability-plan execution."""

    def __init__(self, message: str, *, code: RunnerConformanceCode) -> None:
        if type(message) is not str:
            raise TypeError("runner error message must be an exact string")
        if type(code) is not RunnerConformanceCode:
            raise TypeError("runner error code must be exact")
        super().__init__(message)
        self.code = code.value


def _fail(code: RunnerConformanceCode, message: str) -> None:
    raise RunnerConformanceError(message, code=code)


@runtime_checkable
class RepresentationConformanceCodec(Protocol):
    """Generic representation round-trip surface used by the runner."""

    def encode_representation(
        self,
        representation_id: str,
        configuration: EventConfiguration,
    ) -> object:
        ...

    def decode_representation(
        self,
        representation_id: str,
        payload: object,
        *,
        schema: FeatureSchema,
    ) -> EventConfiguration:
        ...


@dataclass(frozen=True)
class ConformanceRecord:
    """One ordered terminal record copied from a capability plan check."""

    check_id: str
    plan_mode: CheckMode
    status: ConformanceStatus
    reason: Optional[str] = None
    representation_id: Optional[str] = None

    def __post_init__(self) -> None:
        check = PlanCheck(
            check_id=self.check_id,
            mode=self.plan_mode,
            reason=self.reason,
            representation_id=self.representation_id,
        )
        expected_status = _status_for_check(check)
        if type(self.status) is not ConformanceStatus:
            raise TypeError("status must be an exact ConformanceStatus")
        if self.status is not expected_status:
            raise ValueError("record status disagrees with its plan mode")


def _record_for_check(check: PlanCheck) -> ConformanceRecord:
    return ConformanceRecord(
        check_id=check.check_id,
        plan_mode=check.mode,
        status=_status_for_check(check),
        reason=check.reason,
        representation_id=check.representation_id,
    )


def _status_for_check(check: PlanCheck) -> ConformanceStatus:
    if check.mode is CheckMode.NOT_APPLICABLE:
        return ConformanceStatus.NOT_APPLICABLE
    if (
        check.representation_id is not None
        and check.representation_id
        != ATOMIC_COUNTING_GRID_REPRESENTATION_ID
    ):
        return ConformanceStatus.HOOK_ROUNDTRIP
    return ConformanceStatus.PASS


@dataclass(frozen=True)
class ConformanceRun:
    """Immutable result of one fully successful conformance execution."""

    adapter_id: str
    adapter_version: str
    descriptor_sha256: str
    source_sha256: str
    split_manifest_sha256: str
    native_observation_sha256: str
    sample_root_sha256: str
    expected_evidence_sha256: str
    plan: ConformancePlan
    records: Tuple[ConformanceRecord, ...]
    capability_control_trace: Tuple[str, ...]

    def __post_init__(self) -> None:
        # Reuse the exact contract validator without introducing any runner
        # control branch on either public identity label.
        _contract.AdapterIdentity(
            self.adapter_id,
            self.adapter_version,
            "0" * 64,
        )
        for name in (
            "descriptor_sha256",
            "source_sha256",
            "split_manifest_sha256",
            "native_observation_sha256",
            "sample_root_sha256",
            "expected_evidence_sha256",
        ):
            _contract._validated_sha256(getattr(self, name), name=name)
        if type(self.plan) is not ConformancePlan:
            raise TypeError("plan must be an exact ConformancePlan")
        plan = ConformancePlan(
            time_measure=self.plan.time_measure,
            multiplicity_mode=self.plan.multiplicity_mode,
            native=self.plan.native,
            semantic_reconstruction=self.plan.semantic_reconstruction,
            coverage=self.plan.coverage,
            atomic_grid=self.plan.atomic_grid,
            raw_reconstruction=self.plan.raw_reconstruction,
            static_context=self.plan.static_context,
            evaluation_labels=self.plan.evaluation_labels,
            provenance=self.plan.provenance,
            fitted_state=self.plan.fitted_state,
            representation_ids=self.plan.representation_ids,
        )
        object.__setattr__(self, "plan", plan)
        if type(self.records) is not tuple or any(
            type(record) is not ConformanceRecord for record in self.records
        ):
            raise TypeError("records must be an exact tuple of records")
        records = tuple(
            ConformanceRecord(
                check_id=record.check_id,
                plan_mode=record.plan_mode,
                status=record.status,
                reason=record.reason,
                representation_id=record.representation_id,
            )
            for record in self.records
        )
        object.__setattr__(self, "records", records)
        expected_records = tuple(
            _record_for_check(check) for check in plan.ordered_checks()
        )
        if records != expected_records:
            raise ValueError("records do not exactly realize the plan")
        if type(self.capability_control_trace) is not tuple or any(
            type(value) is not str for value in self.capability_control_trace
        ):
            raise TypeError("capability_control_trace must be a tuple of strings")
        trace = tuple(self.capability_control_trace)
        object.__setattr__(self, "capability_control_trace", trace)
        if trace != plan.capability_control_trace:
            raise ValueError("control trace disagrees with the capability plan")


class _SnapshotAdapter:
    """Stable descriptor/schema view used during one runner execution."""

    def __init__(
        self,
        adapter: NativeEventAdapter,
        descriptor: AdapterDescriptor,
        schema: FeatureSchema,
    ) -> None:
        self._adapter = adapter
        self._descriptor = descriptor
        self._schema = schema

    def descriptor(self) -> AdapterDescriptor:
        return self._descriptor

    def schema(self) -> FeatureSchema:
        return self._schema

    def adapt(
        self,
        source_bytes: bytes,
        partition: SamplePartition,
        split_manifest: SplitManifest,
    ) -> AdaptedEventSample:
        return self._adapter.adapt(source_bytes, partition, split_manifest)

    def validate_domain_sample(self, sample: AdaptedEventSample) -> None:
        return self._adapter.validate_domain_sample(sample)


def _snapshot_runner_evidence_inputs(
    complete: CompleteAdaptedEventSample,
    expected_evidence: ExpectedAdapterEvidence,
) -> Tuple[
    CompleteAdaptedEventSample,
    ExpectedAdapterEvidence,
    str,
    str,
]:
    complete_snapshot = _evidence._snapshot_complete(complete)
    expected_snapshot = _evidence._snapshot_expected_evidence(
        expected_evidence
    )
    return (
        complete_snapshot,
        expected_snapshot,
        complete_snapshot.sample.manifest.sample_root_sha256,
        expected_adapter_evidence_digest(expected_snapshot),
    )


def _native_roundtrip_key(
    configuration: EventConfiguration,
) -> Tuple[object, ...]:
    bounded = snapshot_bounded_native_configuration(configuration)
    detached = _contract.rebuild_detached_native_configuration(bounded)
    assert detached.observed is not None
    return (
        _contract.feature_schema_digest(detached.schema),
        tuple(event.model_key() for event in detached.events),
        tuple(item.signature_key() for item in detached.observed.events),
        detached.observed.cardinality_observed,
        _contract.native_observation_digest(detached),
    )


def _preflight_exact_atomic_array(
    value: object,
    *,
    name: str,
    dtype: np.dtype,
    shape: Tuple[int, ...],
) -> np.ndarray:
    """Accept one canonical array only after cheap exact metadata checks."""

    if type(value) is not np.ndarray:
        raise TypeError("atomic-grid arrays must use the exact ndarray type")
    if value.shape != shape:
        raise ValueError("atomic-grid array shape is not canonical")
    if value.dtype != dtype:
        raise TypeError("atomic-grid array dtype is not canonical")
    return value


def _collect_bounded_atomic_grid_map(
    value: object,
    *,
    maximum: int,
) -> Tuple[Tuple[object, ...], bool]:
    """Consume at most one more than a canonical mark map can contain."""

    if type(value) is not MappingProxyType:
        return (), True
    try:
        reported_size = len(value)
    except Exception:
        return (), True
    invalid = reported_size > maximum
    raw_items = []
    try:
        iterator = iter(value.items())
        for _ in range(maximum + 1):
            try:
                raw_items.append(next(iterator))
            except StopIteration:
                break
    except Exception:
        invalid = True
    if len(raw_items) > maximum:
        invalid = True
    if len(raw_items) != reported_size:
        invalid = True
    return tuple(raw_items), invalid


def _preflight_atomic_array_resources_if_exact(
    value: object,
    *,
    maximum_elements: int,
    axis_ceilings: Tuple[int, ...],
) -> None:
    """Bound safe ndarray metadata while deferring non-array shape errors."""

    if type(value) is not np.ndarray:
        return
    if value.size > maximum_elements:
        raise AdapterEvidenceResourceError(
            "atomic-grid array elements exceed ceiling"
        )
    for axis, ceiling in enumerate(axis_ceilings):
        if value.ndim > axis and value.shape[axis] > ceiling:
            raise AdapterEvidenceResourceError(
                "atomic-grid array axis exceeds ceiling"
            )


def _preflight_atomic_grid_map_resources(
    raw_maps: dict,
) -> None:
    """Inspect safe mark-array metadata across all maps before shape checks."""

    for raw_items, _ in raw_maps.values():
        total_elements = 0
        for item in raw_items:
            if type(item) is not tuple or len(item) != 2:
                continue
            array = item[1]
            _preflight_atomic_array_resources_if_exact(
                array,
                maximum_elements=MAXIMUM_ATOMIC_GRID_MARK_SCALARS,
                axis_ceilings=(
                    _evidence.MAXIMUM_TIME_ATOMS,
                    _evidence.MAXIMUM_DECLARED_EVENT_TYPES,
                    MAXIMUM_OCCURRENCES_PER_ATOMIC_CELL,
                    _evidence.MAXIMUM_SCALAR_COORDINATES_PER_EVENT_TYPE,
                ),
            )
            if type(array) is np.ndarray:
                total_elements += array.size
        if total_elements > MAXIMUM_ATOMIC_GRID_MARK_SCALARS:
            raise AdapterEvidenceResourceError(
                "atomic-grid aggregate mark-array elements exceed ceiling"
            )


def _preflight_atomic_grid_map(
    raw_items: Tuple[object, ...],
    invalid: bool,
    *,
    dtype: np.dtype,
    grid_shape: Tuple[int, int, int],
    dimensions: dict,
) -> Tuple[Tuple[str, np.ndarray], ...]:
    """Validate one resource-bounded map and its canonical array metadata."""

    if invalid:
        raise TypeError("atomic-grid mark mapping is invalid")

    arrays = {}
    for item in raw_items:
        if type(item) is not tuple or len(item) != 2:
            raise TypeError("atomic-grid mark items must be exact pairs")
        field_name, array = item
        if type(field_name) is not str:
            raise TypeError("atomic-grid mark names must be exact strings")
        if field_name not in dimensions or field_name in arrays:
            raise ValueError("atomic-grid mark names are not canonical")
        arrays[field_name] = _preflight_exact_atomic_array(
            array,
            name=field_name,
            dtype=dtype,
            shape=grid_shape + (dimensions[field_name],),
        )
    if len(arrays) != len(dimensions):
        raise ValueError("atomic-grid mark mapping is incomplete")
    return tuple((name, arrays[name]) for name in dimensions)


def _snapshot_none_event_ids(
    value: object,
    *,
    number_of_atoms: int,
    number_of_types: int,
    slot_capacity: int,
) -> Tuple[Tuple[Tuple[None, ...], ...], ...]:
    """Validate the public grid's identity-free exact tuple grammar."""

    if type(value) is not tuple:
        raise TypeError("atomic-grid event_ids must be an exact 3-D tuple")
    if len(value) > _evidence.MAXIMUM_TIME_ATOMS:
        raise AdapterEvidenceResourceError(
            "atomic-grid event_id time rows exceed ceiling"
        )
    if len(value) != number_of_atoms:
        raise TypeError("atomic-grid event_ids must be an exact 3-D tuple")
    result = []
    for row in value:
        if type(row) is not tuple:
            raise TypeError("atomic-grid event_ids must be an exact 3-D tuple")
        if len(row) > _evidence.MAXIMUM_DECLARED_EVENT_TYPES:
            raise AdapterEvidenceResourceError(
                "atomic-grid event_id type rows exceed ceiling"
            )
        if len(row) != number_of_types:
            raise TypeError("atomic-grid event_ids must be an exact 3-D tuple")
        result_row = []
        for slots in row:
            if type(slots) is not tuple:
                raise TypeError(
                    "atomic-grid event_ids must be an exact 3-D tuple"
                )
            if len(slots) > MAXIMUM_OCCURRENCES_PER_ATOMIC_CELL:
                raise AdapterEvidenceResourceError(
                    "atomic-grid event_id slots exceed ceiling"
                )
            if len(slots) != slot_capacity:
                raise TypeError(
                    "atomic-grid event_ids must be an exact 3-D tuple"
                )
            for event_id in slots:
                if event_id is not None:
                    raise ValueError(
                        "atomic-grid event_ids must contain only None"
                    )
            result_row.append((None,) * slot_capacity)
        result.append(tuple(result_row))
    return tuple(result)


def _preflight_atomic_grid_payload_resources(
    payload: AtomicCountingGridTensor,
    schema: FeatureSchema,
) -> Tuple[
    Tuple[int, int, int],
    dict,
    dict,
]:
    """Reject every payload-size ceiling before deep container traversal."""

    assert schema.time_reference is not None
    number_of_atoms = len(schema.time_reference.atoms)
    number_of_types = len(schema.event_types)
    cells = number_of_atoms * number_of_types
    if cells > MAXIMUM_ATOMIC_GRID_CELLS:
        raise AdapterEvidenceResourceError("atomic-grid cells exceed ceiling")

    raw_arrays = {
        "cell_counts": payload.cell_counts,
        "occurrence_present": payload.occurrence_present,
        "time_observed": payload.time_observed,
        "type_observed": payload.type_observed,
    }
    _preflight_atomic_array_resources_if_exact(
        raw_arrays["cell_counts"],
        maximum_elements=MAXIMUM_ATOMIC_GRID_CELLS,
        axis_ceilings=(
            _evidence.MAXIMUM_TIME_ATOMS,
            _evidence.MAXIMUM_DECLARED_EVENT_TYPES,
        ),
    )
    for name in ("occurrence_present", "time_observed", "type_observed"):
        _preflight_atomic_array_resources_if_exact(
            raw_arrays[name],
            maximum_elements=MAXIMUM_ATOMIC_GRID_SERIALIZATION_SLOTS,
            axis_ceilings=(
                _evidence.MAXIMUM_TIME_ATOMS,
                _evidence.MAXIMUM_DECLARED_EVENT_TYPES,
                MAXIMUM_OCCURRENCES_PER_ATOMIC_CELL,
            ),
        )

    occurrence_present = raw_arrays["occurrence_present"]
    if type(occurrence_present) is not np.ndarray:
        raise TypeError("occurrence_present must use the exact ndarray type")
    if occurrence_present.ndim != 3:
        raise ValueError("occurrence_present must be three-dimensional")
    slot_capacity = occurrence_present.shape[2]
    if slot_capacity > MAXIMUM_OCCURRENCES_PER_ATOMIC_CELL:
        raise AdapterEvidenceResourceError("atomic-grid slots exceed ceiling")
    total_slots = cells * slot_capacity
    if total_slots > MAXIMUM_ATOMIC_GRID_SERIALIZATION_SLOTS:
        raise AdapterEvidenceResourceError(
            "atomic-grid serialization slots exceed ceiling"
        )

    dimensions = {}
    for event_type in schema.event_types:
        for field in event_type.fields:
            dimensions[field.name] = max(
                dimensions.get(field.name, 0), field.dimension
            )
    if total_slots * sum(dimensions.values()) > (
        MAXIMUM_ATOMIC_GRID_MARK_SCALARS
    ):
        raise AdapterEvidenceResourceError(
            "atomic-grid mark scalars exceed ceiling"
        )
    return (
        (number_of_atoms, number_of_types, slot_capacity),
        dimensions,
        raw_arrays,
    )


def _snapshot_atomic_grid(payload: object) -> AtomicCountingGridTensor:
    if type(payload) is not AtomicCountingGridTensor:
        _fail(
            RunnerConformanceCode.REPRESENTATION_PAYLOAD_INVALID,
            "atomic-grid encoder did not return the exact canonical payload type",
        )

    try:
        schema = snapshot_bounded_schema(payload.schema)
        (
            grid_shape,
            dimensions,
            raw_arrays,
        ) = _preflight_atomic_grid_payload_resources(payload, schema)
        number_of_atoms, number_of_types, slot_capacity = grid_shape
        int_dtype = np.dtype(np.int64)
        float_dtype = np.dtype(np.float64)
        bool_dtype = np.dtype(np.bool_)

        arrays = {
            "cell_counts": _preflight_exact_atomic_array(
                raw_arrays["cell_counts"],
                name="cell_counts",
                dtype=int_dtype,
                shape=(number_of_atoms, number_of_types),
            ),
            "occurrence_present": _preflight_exact_atomic_array(
                raw_arrays["occurrence_present"],
                name="occurrence_present",
                dtype=bool_dtype,
                shape=grid_shape,
            ),
            "time_observed": _preflight_exact_atomic_array(
                raw_arrays["time_observed"],
                name="time_observed",
                dtype=bool_dtype,
                shape=grid_shape,
            ),
            "type_observed": _preflight_exact_atomic_array(
                raw_arrays["type_observed"],
                name="type_observed",
                dtype=bool_dtype,
                shape=grid_shape,
            ),
        }
        event_ids = _snapshot_none_event_ids(
            payload.event_ids,
            number_of_atoms=number_of_atoms,
            number_of_types=number_of_types,
            slot_capacity=slot_capacity,
        )
        if type(payload.cardinality_observed) is not bool:
            raise TypeError("cardinality_observed must be an exact boolean")
        if type(payload.sample_id) is not str or payload.sample_id != "":
            raise ValueError("atomic-grid sample_id must be the empty string")
        if type(payload.group_id) is not str or payload.group_id != "":
            raise ValueError("atomic-grid group_id must be the empty string")

        raw_mark_maps = {
            name: _collect_bounded_atomic_grid_map(
                getattr(payload, name), maximum=len(dimensions)
            )
            for name in (
                "mark_values",
                "mark_applicable",
                "mark_present",
                "mark_observed",
            )
        }
        _preflight_atomic_grid_map_resources(raw_mark_maps)
        mark_arrays = {
            "mark_values": _preflight_atomic_grid_map(
                *raw_mark_maps["mark_values"],
                dtype=float_dtype,
                grid_shape=grid_shape,
                dimensions=dimensions,
            ),
            "mark_applicable": _preflight_atomic_grid_map(
                *raw_mark_maps["mark_applicable"],
                dtype=bool_dtype,
                grid_shape=grid_shape,
                dimensions=dimensions,
            ),
            "mark_present": _preflight_atomic_grid_map(
                *raw_mark_maps["mark_present"],
                dtype=bool_dtype,
                grid_shape=grid_shape,
                dimensions=dimensions,
            ),
            "mark_observed": _preflight_atomic_grid_map(
                *raw_mark_maps["mark_observed"],
                dtype=bool_dtype,
                grid_shape=grid_shape,
                dimensions=dimensions,
            ),
        }

        # Copy only after every dimension and shape has been bounded.  The
        # constructor therefore sees trusted base containers and can perform
        # its semantic/canonical validation without adapter-controlled hooks.
        copied_arrays = {
            name: np.array(array, dtype=array.dtype, copy=True, order="C")
            for name, array in arrays.items()
        }
        copied_mark_arrays = {
            name: MappingProxyType(
                {
                    field_name: np.array(
                        array, dtype=array.dtype, copy=True, order="C"
                    )
                    for field_name, array in items
                }
            )
            for name, items in mark_arrays.items()
        }
        grid = AtomicCountingGridTensor(
            schema=schema,
            cell_counts=copied_arrays["cell_counts"],
            occurrence_present=copied_arrays["occurrence_present"],
            time_observed=copied_arrays["time_observed"],
            type_observed=copied_arrays["type_observed"],
            mark_values=copied_mark_arrays["mark_values"],
            mark_applicable=copied_mark_arrays["mark_applicable"],
            mark_present=copied_mark_arrays["mark_present"],
            mark_observed=copied_mark_arrays["mark_observed"],
            cardinality_observed=payload.cardinality_observed,
            event_ids=event_ids,
            sample_id="",
            group_id="",
        )
    except AdapterEvidenceResourceError:
        _fail(
            RunnerConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "atomic-grid payload exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            RunnerConformanceCode.REPRESENTATION_PAYLOAD_INVALID,
            "atomic-grid payload has an invalid or mutated exact shape",
        )
    return grid


def _preflight_atomic_grid_resources(
    configuration: EventConfiguration,
) -> None:
    schema = configuration.schema
    assert schema.time_reference is not None
    cells = len(schema.time_reference.atoms) * len(schema.event_types)
    if cells > MAXIMUM_ATOMIC_GRID_CELLS:
        _fail(
            RunnerConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "atomic-grid cell count exceeds the generated-v1 ceiling",
        )
    counts = Counter(
        (event.event_time, event.event_type)
        for event in configuration.events
    )
    capacity = max(counts.values(), default=0)
    if capacity > MAXIMUM_OCCURRENCES_PER_ATOMIC_CELL:
        _fail(
            RunnerConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "atomic-grid cell multiplicity exceeds the generated-v1 ceiling",
        )
    slots = cells * capacity
    if slots > MAXIMUM_ATOMIC_GRID_SERIALIZATION_SLOTS:
        _fail(
            RunnerConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "atomic-grid serialization slots exceed the generated-v1 ceiling",
        )
    dimensions = {}
    for event_type in schema.event_types:
        for field in event_type.fields:
            dimensions[field.name] = max(
                dimensions.get(field.name, 0), field.dimension
            )
    if slots * sum(dimensions.values()) > MAXIMUM_ATOMIC_GRID_MARK_SCALARS:
        _fail(
            RunnerConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "atomic-grid mark scalars exceed the generated-v1 ceiling",
        )


def _validate_atomic_grid_payload(
    payload: object,
    *,
    schema: FeatureSchema,
    expected_key: Tuple[object, ...],
) -> AtomicCountingGridTensor:
    grid = _snapshot_atomic_grid(payload)
    if _contract.feature_schema_digest(grid.schema) != (
        _contract.feature_schema_digest(schema)
    ):
        _fail(
            RunnerConformanceCode.REPRESENTATION_PAYLOAD_INVALID,
            "atomic-grid payload schema differs from the capability schema",
        )
    if grid.slot_capacity != grid.maximum_cell_multiplicity:
        _fail(
            RunnerConformanceCode.REPRESENTATION_PAYLOAD_INVALID,
            "atomic-grid payload does not use canonical minimal slot capacity",
        )
    if grid.sample_id != "" or grid.group_id != "" or any(
        event_id is not None
        for atom_row in grid.event_ids
        for type_row in atom_row
        for event_id in type_row
    ):
        _fail(
            RunnerConformanceCode.REPRESENTATION_PAYLOAD_INVALID,
            "atomic-grid payload contains private bookkeeping identity",
        )
    try:
        independently_decoded = grid.to_configuration()
        independent_key = _native_roundtrip_key(independently_decoded)
    except Exception:
        _fail(
            RunnerConformanceCode.REPRESENTATION_PAYLOAD_INVALID,
            "atomic-grid payload fails shared independent decoding",
        )
    if independent_key != expected_key:
        _fail(
            RunnerConformanceCode.REPRESENTATION_ROUNDTRIP_MISMATCH,
            "atomic-grid payload changed detached native state",
        )
    return grid


def _roundtrip_representation(
    codec: RepresentationConformanceCodec,
    check: PlanCheck,
    configuration: EventConfiguration,
    schema: FeatureSchema,
) -> None:
    representation_id = check.representation_id
    if representation_id is None:  # pragma: no cover - plan invariant
        raise AssertionError("a representation check lacks its identifier")
    # Commit the trusted target before adapter-owned code can run.  The codec
    # receives fresh detached objects, never the validator's returned object.
    expected_key = _native_roundtrip_key(configuration)
    if representation_id == ATOMIC_COUNTING_GRID_REPRESENTATION_ID:
        _preflight_atomic_grid_resources(configuration)
    codec_input = _contract.rebuild_detached_native_configuration(
        configuration
    )
    codec_schema = _contract.rebuild_exact_schema(schema)
    try:
        payload = codec.encode_representation(
            representation_id,
            codec_input,
        )
    except Exception:
        _fail(
            RunnerConformanceCode.REPRESENTATION_ENCODE_FAILED,
            "representation encoder raised an exception",
        )
    if representation_id == ATOMIC_COUNTING_GRID_REPRESENTATION_ID:
        grid = _validate_atomic_grid_payload(
            payload,
            schema=schema,
            expected_key=expected_key,
        )
        payload = _snapshot_atomic_grid(grid)
    try:
        decoded = codec.decode_representation(
            representation_id,
            payload,
            schema=codec_schema,
        )
    except Exception:
        _fail(
            RunnerConformanceCode.REPRESENTATION_DECODE_FAILED,
            "representation decoder raised an exception",
        )
    if type(decoded) is not EventConfiguration:
        _fail(
            RunnerConformanceCode.REPRESENTATION_DECODE_FAILED,
            "representation decoder did not return an exact EventConfiguration",
        )
    try:
        actual_key = _native_roundtrip_key(decoded)
    except AdapterEvidenceResourceError:
        _fail(
            RunnerConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "decoded representation exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            RunnerConformanceCode.REPRESENTATION_DECODE_FAILED,
            "decoded representation is not valid native state",
        )
    if actual_key != expected_key:
        _fail(
            RunnerConformanceCode.REPRESENTATION_ROUNDTRIP_MISMATCH,
            "representation round trip changed detached native state for {}".format(
                representation_id
            ),
        )


def run_complete_adapter_conformance(
    adapter: NativeEventAdapter,
    complete: CompleteAdaptedEventSample,
    *,
    source_bytes: bytes,
    split_manifest: SplitManifest,
    expected_evidence: ExpectedAdapterEvidence,
    allowed_exclusion_reason_codes: Tuple[str, ...] = (),
    allowed_censor_reason_codes: Tuple[str, ...] = (),
) -> ConformanceRun:
    """Validate one sample and execute its identity-free capability plan."""

    if type(source_bytes) is not bytes:
        _fail(
            RunnerConformanceCode.INPUT_SNAPSHOT_INVALID,
            "source bytes must be exact immutable bytes",
        )
    if len(source_bytes) > MAXIMUM_SOURCE_BYTES:
        _fail(
            RunnerConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "source bytes exceed the generated-v1 resource ceiling",
        )
    try:
        split_snapshot = snapshot_bounded_split_manifest(split_manifest)
        split_manifest_sha256 = split_snapshot.split_manifest_sha256
        source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    except AdapterEvidenceResourceError:
        _fail(
            RunnerConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "split manifest exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            RunnerConformanceCode.INPUT_SNAPSHOT_INVALID,
            "cannot snapshot conformance inputs",
        )
    try:
        (
            complete_snapshot,
            expected_snapshot,
            sample_root_sha256,
            expected_evidence_sha256,
        ) = _snapshot_runner_evidence_inputs(complete, expected_evidence)
    except AdapterEvidenceResourceError:
        _fail(
            RunnerConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "adapter evidence exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            RunnerConformanceCode.INPUT_SNAPSHOT_INVALID,
            "cannot snapshot adapter evidence inputs",
        )
    try:
        satisfies_protocol = isinstance(adapter, NativeEventAdapter)
    except Exception:
        satisfies_protocol = False
    if not satisfies_protocol:
        _fail(
            RunnerConformanceCode.ADAPTER_PROTOCOL_INVALID,
            "adapter does not satisfy NativeEventAdapter",
        )
    try:
        descriptor_input = adapter.descriptor()
        if type(descriptor_input) is not AdapterDescriptor:
            raise TypeError("descriptor must be exact")
        capabilities_input = descriptor_input.capabilities
        if type(capabilities_input) is not AdapterCapabilities:
            raise TypeError("capabilities must be exact")
        representation_ids = capabilities_input.supported_representation_ids
        if type(representation_ids) is not tuple:
            raise TypeError("representation_ids must be exact tuple")
        if len(representation_ids) > MAXIMUM_REPRESENTATION_IDS:
            raise ValueError("representation_ids exceed ceiling")
        descriptor = _contract._snapshot_descriptor(descriptor_input)
        schema = snapshot_bounded_schema(adapter.schema())
        plan = plan_from_capabilities(descriptor.capabilities)
    except AdapterEvidenceResourceError:
        _fail(
            RunnerConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "adapter schema exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            RunnerConformanceCode.ADAPTER_SNAPSHOT_INVALID,
            "cannot snapshot adapter descriptor/schema",
        )

    snapshot_adapter = _SnapshotAdapter(adapter, descriptor, schema)
    detached = validate_complete_adapted_event_sample(
        snapshot_adapter,
        complete_snapshot,
        source_bytes=source_bytes,
        split_manifest=split_snapshot,
        expected_evidence=expected_snapshot,
        allowed_exclusion_reason_codes=allowed_exclusion_reason_codes,
        allowed_censor_reason_codes=allowed_censor_reason_codes,
    )

    codec = None
    required_representations = tuple(
        check
        for check in plan.ordered_checks()
        if check.mode is CheckMode.REQUIRED
        and check.representation_id is not None
    )
    if required_representations:
        try:
            satisfies_codec = isinstance(
                adapter, RepresentationConformanceCodec
            )
        except Exception:
            satisfies_codec = False
        if not satisfies_codec:
            _fail(
                RunnerConformanceCode.REPRESENTATION_PROTOCOL_MISSING,
                "advertised representations require the shared codec protocol",
            )
        codec = adapter

    records = []
    for check in plan.ordered_checks():
        if (
            check.mode is CheckMode.REQUIRED
            and check.representation_id is not None
        ):
            assert codec is not None
            _roundtrip_representation(codec, check, detached, schema)
        records.append(_record_for_check(check))

    identity = descriptor.identity
    return ConformanceRun(
        adapter_id=identity.adapter_id,
        adapter_version=identity.adapter_version,
        descriptor_sha256=descriptor.descriptor_sha256,
        source_sha256=source_sha256,
        split_manifest_sha256=split_manifest_sha256,
        native_observation_sha256=_contract.native_observation_digest(detached),
        sample_root_sha256=sample_root_sha256,
        expected_evidence_sha256=expected_evidence_sha256,
        plan=plan,
        records=tuple(records),
        capability_control_trace=plan.capability_control_trace,
    )


__all__ = [
    "ConformanceRecord",
    "ConformanceRun",
    "ConformanceStatus",
    "MAXIMUM_ATOMIC_GRID_CELLS",
    "MAXIMUM_ATOMIC_GRID_MARK_SCALARS",
    "MAXIMUM_ATOMIC_GRID_SERIALIZATION_SLOTS",
    "MAXIMUM_OCCURRENCES_PER_ATOMIC_CELL",
    "RepresentationConformanceCodec",
    "RunnerConformanceCode",
    "RunnerConformanceError",
    "run_complete_adapter_conformance",
]
