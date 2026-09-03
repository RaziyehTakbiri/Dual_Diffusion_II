"""Additive Phase-C evidence contracts for native-event adapters.

The Phase-B contract in :mod:`heterodiff.data.adapter_contract` intentionally
treats coverage, provenance, fitted state, and reconstruction as opaque digest
leaves.  This module gives those leaves exact, domain-neutral structures while
leaving every Phase-B public object and validation path unchanged.

The complete validator treats adapter output as untrusted.  It validates the
shared source, split, schema, native-state, and manifest commitments before it
invokes an adapter-owned domain hook.  It returns only a newly detached native
``EventConfiguration``.  No parser, domain, Torch, task, padding, or model
module is imported here.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
import hashlib
import re
from types import MappingProxyType
from typing import Optional, Tuple

from heterodiff.data import adapter_contract as _contract
from heterodiff.data.adapter_contract import (
    AdapterCapabilities,
    AdapterContractError,
    AdapterDescriptor,
    AdapterManifest,
    AdaptedEventSample,
    NativeEventAdapter,
    SamplePartition,
    SplitManifest,
)
from heterodiff.events import (
    ContinuousField,
    Event,
    EventConfiguration,
    EventObservation,
    EventTypeSchema,
    FeatureSchema,
    ObservationPattern,
    TimeReference,
)


SOURCE_ITEM_DIGEST_DOMAIN = "heterodiff.adapter.source-item.v1"
SOURCE_INVENTORY_DIGEST_DOMAIN = "heterodiff.adapter.source-inventory.v1"
NATIVE_OCCURRENCE_DIGEST_DOMAIN = "heterodiff.adapter.native-occurrence.v1"
TRAINING_GROUP_SET_DIGEST_DOMAIN = (
    "heterodiff.adapter.training-group-set.v1"
)
EXPECTED_EVIDENCE_DIGEST_DOMAIN = "heterodiff.adapter.expected-evidence.v1"

# Development defaults implement the generated-v1 ceilings in research/34.
# A9.1 must freeze these exact values before decision-bearing execution.
MAXIMUM_SOURCE_BYTES = 64 * 1024
MAXIMUM_INVENTORY_ITEMS = 4096
MAXIMUM_SEMANTIC_OCCURRENCES = 2048
MAXIMUM_SPLIT_ENTRIES = 4096
MAXIMUM_SPLIT_GROUPS = 128
MAXIMUM_DECLARED_EVENT_TYPES = 1024
MAXIMUM_FIELDS_PER_EVENT_TYPE = 16
MAXIMUM_SCALAR_COORDINATES_PER_EVENT_TYPE = 16
MAXIMUM_SCALAR_COORDINATES_PER_OCCURRENCE = 16
MAXIMUM_TIME_ATOMS = 4096
MAXIMUM_EVENT_ID_TUPLE_ARITY = 8
MAXIMUM_EVENT_ID_COMPONENT_BYTES = 256
MAXIMUM_EVENT_ID_METADATA_BYTES = 2 * 1024 * 1024
MAXIMUM_EVENT_ID_INTEGER_ABSOLUTE_VALUE = (1 << 53) - 1
MAXIMUM_KEYED_LEAF_ENTRIES = 4096
MAXIMUM_FIELD_STATUSES_PER_OCCURRENCE = 16
MAXIMUM_SOURCE_LINKS_PER_OCCURRENCE = 4096
MAXIMUM_TOTAL_PROVENANCE_SOURCE_LINKS = MAXIMUM_INVENTORY_ITEMS
MAXIMUM_SECONDARY_TAGS_PER_ITEM = 64
MAXIMUM_TOTAL_SECONDARY_TAGS = MAXIMUM_INVENTORY_ITEMS
MAXIMUM_REASON_CODES = 1024
MAXIMUM_SINGLE_PAYLOAD_BYTES = 256 * 1024
# This bounds the sum of private payload byte strings, not the encoded size of
# a persisted evidence artifact.  A9.1/publication must separately freeze and
# enforce the exact serialized-artifact byte ceiling.
MAXIMUM_PRIVATE_PAYLOAD_BYTES = 16 * 1024 * 1024

_ERROR_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,95}$")


class AdapterConformanceCode(str, Enum):
    """Stable machine-readable failures emitted by the complete validator."""

    CORE_ADAPTER_PROTOCOL = "CORE_ADAPTER_PROTOCOL"
    CORE_INPUT_SHAPE_INVALID = "CORE_INPUT_SHAPE_INVALID"
    CORE_DESCRIPTOR_SCHEMA_MISMATCH = "CORE_DESCRIPTOR_SCHEMA_MISMATCH"
    CORE_DESCRIPTOR_DIGEST_MISMATCH = "CORE_DESCRIPTOR_DIGEST_MISMATCH"
    CORE_PARTITION_MISMATCH = "CORE_PARTITION_MISMATCH"
    CORE_SPLIT_MISMATCH = "CORE_SPLIT_MISMATCH"
    CORE_SOURCE_MISMATCH = "CORE_SOURCE_MISMATCH"
    CORE_SCHEMA_MISMATCH = "CORE_SCHEMA_MISMATCH"
    CORE_NATIVE_MISMATCH = "CORE_NATIVE_MISMATCH"
    CORE_MANIFEST_ROOT_MISMATCH = "CORE_MANIFEST_ROOT_MISMATCH"
    NATIVE_EXPECTATION_MISMATCH = "NATIVE_EXPECTATION_MISMATCH"
    INVENTORY_BINDING_MISMATCH = "INVENTORY_BINDING_MISMATCH"
    INVENTORY_EXPECTATION_MISMATCH = "INVENTORY_EXPECTATION_MISMATCH"
    COVERAGE_BINDING_MISMATCH = "COVERAGE_BINDING_MISMATCH"
    COVERAGE_EXPECTATION_MISMATCH = "COVERAGE_EXPECTATION_MISMATCH"
    COVERAGE_ITEM_SET_MISMATCH = "COVERAGE_ITEM_SET_MISMATCH"
    COVERAGE_TARGET_MISMATCH = "COVERAGE_TARGET_MISMATCH"
    COVERAGE_EXCLUSION_REASON_INVALID = (
        "COVERAGE_EXCLUSION_REASON_INVALID"
    )
    STATIC_CONTEXT_CAPABILITY_MISMATCH = (
        "STATIC_CONTEXT_CAPABILITY_MISMATCH"
    )
    STATIC_CONTEXT_BINDING_MISMATCH = "STATIC_CONTEXT_BINDING_MISMATCH"
    STATIC_CONTEXT_EXPECTATION_MISMATCH = (
        "STATIC_CONTEXT_EXPECTATION_MISMATCH"
    )
    EVALUATION_LABELS_CAPABILITY_MISMATCH = (
        "EVALUATION_LABELS_CAPABILITY_MISMATCH"
    )
    EVALUATION_LABELS_BINDING_MISMATCH = (
        "EVALUATION_LABELS_BINDING_MISMATCH"
    )
    EVALUATION_LABELS_EXPECTATION_MISMATCH = (
        "EVALUATION_LABELS_EXPECTATION_MISMATCH"
    )
    PROVENANCE_CAPABILITY_MISMATCH = "PROVENANCE_CAPABILITY_MISMATCH"
    PROVENANCE_BINDING_MISMATCH = "PROVENANCE_BINDING_MISMATCH"
    PROVENANCE_EXPECTATION_MISMATCH = "PROVENANCE_EXPECTATION_MISMATCH"
    PROVENANCE_OCCURRENCE_MULTISET_MISMATCH = (
        "PROVENANCE_OCCURRENCE_MULTISET_MISMATCH"
    )
    PROVENANCE_SOURCE_ITEM_MISMATCH = (
        "PROVENANCE_SOURCE_ITEM_MISMATCH"
    )
    PROVENANCE_FIELD_STATUS_MISMATCH = (
        "PROVENANCE_FIELD_STATUS_MISMATCH"
    )
    PROVENANCE_CENSOR_REASON_INVALID = (
        "PROVENANCE_CENSOR_REASON_INVALID"
    )
    FITTED_STATE_REQUIRED = "FITTED_STATE_REQUIRED"
    FITTED_STATE_FORBIDDEN = "FITTED_STATE_FORBIDDEN"
    FITTED_STATE_BINDING_MISMATCH = "FITTED_STATE_BINDING_MISMATCH"
    FITTED_STATE_EXPECTATION_MISMATCH = "FITTED_STATE_EXPECTATION_MISMATCH"
    RECONSTRUCTION_BINDING_MISMATCH = (
        "RECONSTRUCTION_BINDING_MISMATCH"
    )
    RECONSTRUCTION_EXPECTATION_MISMATCH = (
        "RECONSTRUCTION_EXPECTATION_MISMATCH"
    )
    ORACLE_SHAPE_INVALID = "ORACLE_SHAPE_INVALID"
    ORACLE_BINDING_INVALID = "ORACLE_BINDING_INVALID"
    REASON_REGISTRY_INVALID = "REASON_REGISTRY_INVALID"
    LEAF_SHAPE_INVALID = "LEAF_SHAPE_INVALID"
    LEAF_MANIFEST_DIGEST_MISMATCH = "LEAF_MANIFEST_DIGEST_MISMATCH"
    RAW_RECONSTRUCTION_CAPABILITY_MISMATCH = (
        "RAW_RECONSTRUCTION_CAPABILITY_MISMATCH"
    )
    RAW_RECONSTRUCTION_MISMATCH = "RAW_RECONSTRUCTION_MISMATCH"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    DOMAIN_VALIDATION_FAILED = "DOMAIN_VALIDATION_FAILED"
    DOMAIN_VALIDATION_RETURNED_VALUE = "DOMAIN_VALIDATION_RETURNED_VALUE"


class AdapterConformanceError(AdapterContractError):
    """One stable coded failure from complete adapter validation."""

    def __init__(
        self, message: str, *, code: AdapterConformanceCode
    ) -> None:
        if type(message) is not str:
            raise TypeError("conformance error message must be an exact string")
        if type(code) is not AdapterConformanceCode:
            raise TypeError("conformance error code must be exact")
        if _ERROR_CODE_RE.fullmatch(code.value) is None:  # pragma: no cover
            raise ValueError("invalid internal conformance error code")
        super().__init__(message)
        self.code = code.value


class AdapterEvidenceResourceError(ValueError):
    """A Phase-C evidence object exceeds a fixed development ceiling."""


def _bounded_length(value: object, *, maximum: int, name: str) -> int:
    try:
        length = len(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError("{} must have a bounded length".format(name)) from exc
    if length > maximum:
        raise AdapterEvidenceResourceError(
            "{} exceeds its resource ceiling".format(name)
        )
    return length


def _bounded_payload(payload: object, *, name: str) -> bytes:
    if type(payload) is not bytes:
        raise TypeError("{} must be exact immutable bytes".format(name))
    _bounded_length(
        payload, maximum=MAXIMUM_SINGLE_PAYLOAD_BYTES, name=name
    )
    return payload


def _fail(code: AdapterConformanceCode, message: str) -> None:
    raise AdapterConformanceError(message, code=code)


def _blob_payload(payload: bytes) -> object:
    payload = _bounded_payload(payload, name="canonical payload")
    return {
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "payload_size_bytes": len(payload),
    }


def _validate_reason_codes(
    values: Tuple[str, ...], *, name: str
) -> Tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError("{} must be an exact tuple".format(name))
    _bounded_length(values, maximum=MAXIMUM_REASON_CODES, name=name)
    result = tuple(
        _contract._validated_public_id(value, name=name) for value in values
    )
    if len(set(result)) != len(result):
        raise ValueError("{} values must be unique".format(name))
    if result != tuple(sorted(result)):
        raise ValueError("{} values must use canonical order".format(name))
    return result


@dataclass(frozen=True)
class SourceInventoryItem:
    """One private parsed-item identity and its canonical semantic bytes."""

    item_key: str
    canonical_item_bytes: bytes

    def __post_init__(self) -> None:
        _bounded_payload(
            self.canonical_item_bytes, name="canonical_item_bytes"
        )
        _contract._validated_private_text(self.item_key, name="item_key")


def _snapshot_inventory_item(item: object) -> SourceInventoryItem:
    if type(item) is not SourceInventoryItem:
        raise TypeError("inventory items must be exact SourceInventoryItem instances")
    return SourceInventoryItem(item.item_key, item.canonical_item_bytes)


def _preflight_inventory_payloads(
    items: Tuple[object, ...],
) -> int:
    if any(type(item) is not SourceInventoryItem for item in items):
        raise TypeError(
            "inventory items must be exact SourceInventoryItem instances"
        )
    total = 0
    for item in items:
        payload = _bounded_payload(
            item.canonical_item_bytes, name="canonical_item_bytes"
        )
        total += len(payload)
        if total > MAXIMUM_PRIVATE_PAYLOAD_BYTES:
            raise AdapterEvidenceResourceError(
                "inventory payload bytes exceed the private payload ceiling"
            )
    return total


def source_inventory_item_digest(
    item: SourceInventoryItem, *, item_format_id: str
) -> str:
    snapshot = _snapshot_inventory_item(item)
    format_id = _contract._validated_public_id(
        item_format_id, name="item_format_id"
    )
    return _contract._domain_digest(
        SOURCE_ITEM_DIGEST_DOMAIN,
        {
            "canonical_item": _blob_payload(snapshot.canonical_item_bytes),
            "item_key": snapshot.item_key,
            "item_format_id": format_id,
        },
    )


@dataclass(frozen=True)
class SourceInventory:
    """Content-bound parsed-item inventory for one exact source object."""

    source_sha256: str
    source_size_bytes: int
    policy_sha256: str
    item_format_id: str
    items: Tuple[SourceInventoryItem, ...]

    def __post_init__(self) -> None:
        _contract._validated_sha256(self.source_sha256, name="source_sha256")
        _contract._validated_nonnegative_size(
            self.source_size_bytes, name="source_size_bytes"
        )
        if self.source_size_bytes > MAXIMUM_SOURCE_BYTES:
            raise AdapterEvidenceResourceError(
                "source_size_bytes exceeds its resource ceiling"
            )
        _contract._validated_sha256(self.policy_sha256, name="policy_sha256")
        _contract._validated_public_id(
            self.item_format_id, name="item_format_id"
        )
        if type(self.items) is not tuple:
            raise TypeError("inventory items must be an exact tuple")
        _bounded_length(
            self.items,
            maximum=MAXIMUM_INVENTORY_ITEMS,
            name="inventory items",
        )
        _preflight_inventory_payloads(self.items)
        items = tuple(_snapshot_inventory_item(item) for item in self.items)
        if sum(len(item.canonical_item_bytes) for item in items) > (
            MAXIMUM_PRIVATE_PAYLOAD_BYTES
        ):
            raise AdapterEvidenceResourceError(
                "inventory payload bytes exceed the private payload ceiling"
            )
        keys = tuple(item.item_key for item in items)
        if len(set(keys)) != len(keys):
            raise ValueError("inventory item_key values must be unique")
        object.__setattr__(
            self, "items", tuple(sorted(items, key=lambda item: item.item_key))
        )

    @property
    def source_inventory_sha256(self) -> str:
        return source_inventory_digest(self)


def _snapshot_inventory(inventory: object) -> SourceInventory:
    if type(inventory) is not SourceInventory:
        raise TypeError("inventory must be an exact SourceInventory")
    return SourceInventory(
        source_sha256=inventory.source_sha256,
        source_size_bytes=inventory.source_size_bytes,
        policy_sha256=inventory.policy_sha256,
        item_format_id=inventory.item_format_id,
        items=inventory.items,
    )


def source_inventory_digest(inventory: SourceInventory) -> str:
    snapshot = _snapshot_inventory(inventory)
    return _contract._domain_digest(
        SOURCE_INVENTORY_DIGEST_DOMAIN,
        {
            "item_format_id": snapshot.item_format_id,
            "items": [
                {
                    "item_key": item.item_key,
                    "source_item_sha256": source_inventory_item_digest(
                        item, item_format_id=snapshot.item_format_id
                    ),
                }
                for item in snapshot.items
            ],
            "policy_sha256": snapshot.policy_sha256,
            "source_sha256": snapshot.source_sha256,
            "source_size_bytes": snapshot.source_size_bytes,
        },
    )


class CoverageDisposition(str, Enum):
    EVENT_OCCURRENCE = "event_occurrence"
    STATIC_CONTEXT = "static_context"
    EVALUATION_ONLY_LABEL = "evaluation_only_label"
    EXCLUDED_WITH_REASON = "excluded_with_reason"


@dataclass(frozen=True)
class CoverageEntry:
    """Exactly one primary disposition for one inventoried source item."""

    item_key: str
    disposition: CoverageDisposition
    target_key: Optional[str] = None
    exclusion_reason_code: Optional[str] = None
    secondary_tags: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.secondary_tags) is not tuple:
            raise TypeError("secondary_tags must be an exact tuple")
        _bounded_length(
            self.secondary_tags,
            maximum=MAXIMUM_SECONDARY_TAGS_PER_ITEM,
            name="secondary_tags",
        )
        _contract._validated_private_text(self.item_key, name="item_key")
        if type(self.disposition) is not CoverageDisposition:
            raise TypeError("coverage disposition must be exact")
        tags = tuple(
            _contract._validated_public_id(tag, name="secondary_tag")
            for tag in self.secondary_tags
        )
        if len(set(tags)) != len(tags) or tags != tuple(sorted(tags)):
            raise ValueError("secondary_tags must be unique and canonically ordered")
        object.__setattr__(self, "secondary_tags", tags)
        excluded = self.disposition is CoverageDisposition.EXCLUDED_WITH_REASON
        if excluded:
            if self.target_key is not None:
                raise ValueError("an excluded item cannot have a target_key")
            _contract._validated_public_id(
                self.exclusion_reason_code, name="exclusion_reason_code"
            )
        else:
            _contract._validated_private_text(
                self.target_key, name="coverage target_key"
            )
            if self.exclusion_reason_code is not None:
                raise ValueError("a materialized item cannot have an exclusion reason")


def _snapshot_coverage_entry(entry: object) -> CoverageEntry:
    if type(entry) is not CoverageEntry:
        raise TypeError("coverage entries must be exact CoverageEntry instances")
    return CoverageEntry(
        item_key=entry.item_key,
        disposition=entry.disposition,
        target_key=entry.target_key,
        exclusion_reason_code=entry.exclusion_reason_code,
        secondary_tags=entry.secondary_tags,
    )


def _preflight_coverage_entry_tuples(
    entries: Tuple[object, ...],
) -> int:
    total_secondary_tags = 0
    for entry in entries:
        if type(entry) is not CoverageEntry:
            raise TypeError(
                "coverage entries must be exact CoverageEntry instances"
            )
        if type(entry.secondary_tags) is not tuple:
            raise TypeError("secondary_tags must be an exact tuple")
        _bounded_length(
            entry.secondary_tags,
            maximum=MAXIMUM_SECONDARY_TAGS_PER_ITEM,
            name="secondary tags per item",
        )
        total_secondary_tags += len(entry.secondary_tags)
        if total_secondary_tags > MAXIMUM_TOTAL_SECONDARY_TAGS:
            raise AdapterEvidenceResourceError(
                "aggregate secondary tags exceed their resource ceiling"
            )
    return total_secondary_tags


@dataclass(frozen=True)
class SourceCoverageLedger:
    """Exhaustive primary dispositions for one independently inventoried source."""

    source_sha256: str
    source_size_bytes: int
    policy_sha256: str
    source_inventory_sha256: str
    entries: Tuple[CoverageEntry, ...]

    def __post_init__(self) -> None:
        _contract._validated_sha256(self.source_sha256, name="source_sha256")
        _contract._validated_nonnegative_size(
            self.source_size_bytes, name="source_size_bytes"
        )
        if self.source_size_bytes > MAXIMUM_SOURCE_BYTES:
            raise AdapterEvidenceResourceError(
                "source_size_bytes exceeds its resource ceiling"
            )
        _contract._validated_sha256(self.policy_sha256, name="policy_sha256")
        _contract._validated_sha256(
            self.source_inventory_sha256, name="source_inventory_sha256"
        )
        if type(self.entries) is not tuple:
            raise TypeError("coverage entries must be an exact tuple")
        _bounded_length(
            self.entries,
            maximum=MAXIMUM_INVENTORY_ITEMS,
            name="coverage entries",
        )
        _preflight_coverage_entry_tuples(self.entries)
        entries = tuple(_snapshot_coverage_entry(entry) for entry in self.entries)
        if sum(len(entry.secondary_tags) for entry in entries) > (
            MAXIMUM_TOTAL_SECONDARY_TAGS
        ):
            raise AdapterEvidenceResourceError(
                "aggregate secondary tags exceed their resource ceiling"
            )
        keys = tuple(entry.item_key for entry in entries)
        if len(set(keys)) != len(keys):
            raise ValueError("coverage item_key values must be unique")
        object.__setattr__(
            self, "entries", tuple(sorted(entries, key=lambda entry: entry.item_key))
        )

    @property
    def coverage_ledger_sha256(self) -> str:
        return source_coverage_ledger_digest(self)


def _snapshot_coverage(ledger: object) -> SourceCoverageLedger:
    if type(ledger) is not SourceCoverageLedger:
        raise TypeError("coverage must be an exact SourceCoverageLedger")
    return SourceCoverageLedger(
        source_sha256=ledger.source_sha256,
        source_size_bytes=ledger.source_size_bytes,
        policy_sha256=ledger.policy_sha256,
        source_inventory_sha256=ledger.source_inventory_sha256,
        entries=ledger.entries,
    )


def source_coverage_ledger_digest(ledger: SourceCoverageLedger) -> str:
    snapshot = _snapshot_coverage(ledger)
    if not snapshot.entries:
        return _contract.EMPTY_COVERAGE_LEDGER_SHA256
    return _contract._domain_digest(
        _contract.COVERAGE_LEDGER_DIGEST_DOMAIN,
        {
            "entries": [
                {
                    "disposition": entry.disposition.value,
                    "exclusion_reason_code": entry.exclusion_reason_code,
                    "item_key": entry.item_key,
                    "secondary_tags": list(entry.secondary_tags),
                    "target_key": entry.target_key,
                }
                for entry in snapshot.entries
            ],
            "policy_sha256": snapshot.policy_sha256,
            "source_inventory_sha256": snapshot.source_inventory_sha256,
            "source_sha256": snapshot.source_sha256,
            "source_size_bytes": snapshot.source_size_bytes,
        },
    )


@dataclass(frozen=True)
class StaticContextEntry:
    entry_key: str
    canonical_payload_bytes: bytes

    def __post_init__(self) -> None:
        _bounded_payload(
            self.canonical_payload_bytes, name="static context payload"
        )
        _contract._validated_private_text(self.entry_key, name="static entry_key")


@dataclass(frozen=True)
class EvaluationLabelEntry:
    entry_key: str
    canonical_payload_bytes: bytes

    def __post_init__(self) -> None:
        _bounded_payload(
            self.canonical_payload_bytes, name="evaluation label payload"
        )
        _contract._validated_private_text(self.entry_key, name="label entry_key")


def _snapshot_static_entry(entry: object) -> StaticContextEntry:
    if type(entry) is not StaticContextEntry:
        raise TypeError("static entries must be exact StaticContextEntry instances")
    return StaticContextEntry(entry.entry_key, entry.canonical_payload_bytes)


def _snapshot_label_entry(entry: object) -> EvaluationLabelEntry:
    if type(entry) is not EvaluationLabelEntry:
        raise TypeError("label entries must be exact EvaluationLabelEntry instances")
    return EvaluationLabelEntry(entry.entry_key, entry.canonical_payload_bytes)


def _preflight_keyed_payloads(
    entries: Tuple[object, ...],
    *,
    expected_type: object,
    payload_name: str,
    entry_label: str,
) -> int:
    if any(type(entry) is not expected_type for entry in entries):
        raise TypeError(
            "{} entries have an invalid exact type".format(entry_label)
        )
    total = 0
    for entry in entries:
        payload = _bounded_payload(
            entry.canonical_payload_bytes,  # type: ignore[attr-defined]
            name=payload_name,
        )
        total += len(payload)
        if total > MAXIMUM_PRIVATE_PAYLOAD_BYTES:
            raise AdapterEvidenceResourceError(
                "{} payload bytes exceed the private payload ceiling".format(
                    entry_label
                )
            )
    return total


@dataclass(frozen=True)
class StaticContext:
    source_sha256: str
    policy_sha256: str
    format_id: str
    entries: Tuple[StaticContextEntry, ...] = ()

    def __post_init__(self) -> None:
        _contract._validated_sha256(self.source_sha256, name="source_sha256")
        _contract._validated_sha256(self.policy_sha256, name="policy_sha256")
        _contract._validated_public_id(self.format_id, name="static format_id")
        if type(self.entries) is not tuple:
            raise TypeError("static entries must be an exact tuple")
        _bounded_length(
            self.entries,
            maximum=MAXIMUM_KEYED_LEAF_ENTRIES,
            name="static entries",
        )
        _preflight_keyed_payloads(
            self.entries,
            expected_type=StaticContextEntry,
            payload_name="static context payload",
            entry_label="static",
        )
        entries = tuple(_snapshot_static_entry(entry) for entry in self.entries)
        if sum(len(entry.canonical_payload_bytes) for entry in entries) > (
            MAXIMUM_PRIVATE_PAYLOAD_BYTES
        ):
            raise AdapterEvidenceResourceError(
                "static payload bytes exceed the private payload ceiling"
            )
        keys = tuple(entry.entry_key for entry in entries)
        if len(set(keys)) != len(keys):
            raise ValueError("static entry_key values must be unique")
        object.__setattr__(
            self, "entries", tuple(sorted(entries, key=lambda entry: entry.entry_key))
        )

    @property
    def static_context_sha256(self) -> str:
        return static_context_digest(self)


@dataclass(frozen=True)
class EvaluationLabels:
    source_sha256: str
    policy_sha256: str
    format_id: str
    entries: Tuple[EvaluationLabelEntry, ...] = ()

    def __post_init__(self) -> None:
        _contract._validated_sha256(self.source_sha256, name="source_sha256")
        _contract._validated_sha256(self.policy_sha256, name="policy_sha256")
        _contract._validated_public_id(self.format_id, name="label format_id")
        if type(self.entries) is not tuple:
            raise TypeError("label entries must be an exact tuple")
        _bounded_length(
            self.entries,
            maximum=MAXIMUM_KEYED_LEAF_ENTRIES,
            name="label entries",
        )
        _preflight_keyed_payloads(
            self.entries,
            expected_type=EvaluationLabelEntry,
            payload_name="evaluation label payload",
            entry_label="label",
        )
        entries = tuple(_snapshot_label_entry(entry) for entry in self.entries)
        if sum(len(entry.canonical_payload_bytes) for entry in entries) > (
            MAXIMUM_PRIVATE_PAYLOAD_BYTES
        ):
            raise AdapterEvidenceResourceError(
                "label payload bytes exceed the private payload ceiling"
            )
        keys = tuple(entry.entry_key for entry in entries)
        if len(set(keys)) != len(keys):
            raise ValueError("label entry_key values must be unique")
        object.__setattr__(
            self, "entries", tuple(sorted(entries, key=lambda entry: entry.entry_key))
        )

    @property
    def evaluation_labels_sha256(self) -> str:
        return evaluation_labels_digest(self)


def _snapshot_static_context(value: object) -> StaticContext:
    if type(value) is not StaticContext:
        raise TypeError("static_context must be an exact StaticContext")
    return StaticContext(
        value.source_sha256, value.policy_sha256, value.format_id, value.entries
    )


def _snapshot_evaluation_labels(value: object) -> EvaluationLabels:
    if type(value) is not EvaluationLabels:
        raise TypeError("evaluation_labels must be exact EvaluationLabels")
    return EvaluationLabels(
        value.source_sha256, value.policy_sha256, value.format_id, value.entries
    )


def static_context_digest(context: StaticContext) -> str:
    snapshot = _snapshot_static_context(context)
    if not snapshot.entries:
        return _contract.EMPTY_STATIC_CONTEXT_SHA256
    return _contract._domain_digest(
        _contract.STATIC_CONTEXT_DIGEST_DOMAIN,
        {
            "entries": [
                {
                    "canonical_payload": _blob_payload(
                        entry.canonical_payload_bytes
                    ),
                    "entry_key": entry.entry_key,
                }
                for entry in snapshot.entries
            ],
            "format_id": snapshot.format_id,
            "policy_sha256": snapshot.policy_sha256,
            "source_sha256": snapshot.source_sha256,
        },
    )


def evaluation_labels_digest(labels: EvaluationLabels) -> str:
    snapshot = _snapshot_evaluation_labels(labels)
    if not snapshot.entries:
        return _contract.EMPTY_EVALUATION_LABELS_SHA256
    return _contract._domain_digest(
        _contract.EVALUATION_LABELS_DIGEST_DOMAIN,
        {
            "entries": [
                {
                    "canonical_payload": _blob_payload(
                        entry.canonical_payload_bytes
                    ),
                    "entry_key": entry.entry_key,
                }
                for entry in snapshot.entries
            ],
            "format_id": snapshot.format_id,
            "policy_sha256": snapshot.policy_sha256,
            "source_sha256": snapshot.source_sha256,
        },
    )


class SourceValueStatus(str, Enum):
    PRESENT = "present"
    SOURCE_MISSING = "source_missing"
    CENSORED = "censored"


@dataclass(frozen=True)
class SourceFieldStatus:
    field_name: str
    status: SourceValueStatus
    reason_code: Optional[str] = None

    def __post_init__(self) -> None:
        _contract._validated_private_text(self.field_name, name="field_name")
        if type(self.status) is not SourceValueStatus:
            raise TypeError("source value status must be exact")
        if self.status is SourceValueStatus.CENSORED:
            if self.reason_code is None:
                raise ValueError("a censored field requires a reason_code")
            _contract._validated_public_id(
                self.reason_code, name="censor reason_code"
            )
        elif self.reason_code is not None:
            raise ValueError("only a censored field may have a reason_code")


def _snapshot_field_status(value: object) -> SourceFieldStatus:
    if type(value) is not SourceFieldStatus:
        raise TypeError("field statuses must be exact SourceFieldStatus instances")
    return SourceFieldStatus(value.field_name, value.status, value.reason_code)


@dataclass(frozen=True)
class OccurrenceProvenance:
    provenance_key: str
    native_occurrence_sha256: str
    source_item_keys: Tuple[str, ...]
    field_statuses: Tuple[SourceFieldStatus, ...]
    private_format_id: str
    private_payload_bytes: bytes

    def __post_init__(self) -> None:
        if type(self.source_item_keys) is not tuple:
            raise TypeError("source_item_keys must be an exact tuple")
        _bounded_length(
            self.source_item_keys,
            maximum=MAXIMUM_SOURCE_LINKS_PER_OCCURRENCE,
            name="source_item_keys",
        )
        if type(self.field_statuses) is not tuple:
            raise TypeError("field_statuses must be an exact tuple")
        _bounded_length(
            self.field_statuses,
            maximum=MAXIMUM_FIELD_STATUSES_PER_OCCURRENCE,
            name="field_statuses",
        )
        _bounded_payload(
            self.private_payload_bytes, name="private provenance payload"
        )
        _contract._validated_private_text(
            self.provenance_key, name="provenance_key"
        )
        _contract._validated_sha256(
            self.native_occurrence_sha256, name="native_occurrence_sha256"
        )
        source_keys = tuple(
            _contract._validated_private_text(key, name="source item key")
            for key in self.source_item_keys
        )
        if not source_keys:
            raise ValueError("occurrence provenance requires a source item")
        if len(set(source_keys)) != len(source_keys) or source_keys != tuple(
            sorted(source_keys)
        ):
            raise ValueError(
                "source_item_keys must be unique and canonically ordered"
            )
        object.__setattr__(self, "source_item_keys", source_keys)
        statuses = tuple(
            _snapshot_field_status(status) for status in self.field_statuses
        )
        names = tuple(status.field_name for status in statuses)
        if len(set(names)) != len(names):
            raise ValueError("field status names must be unique")
        object.__setattr__(
            self,
            "field_statuses",
            tuple(sorted(statuses, key=lambda status: status.field_name)),
        )
        _contract._validated_public_id(
            self.private_format_id, name="private_format_id"
        )


def _snapshot_occurrence_provenance(value: object) -> OccurrenceProvenance:
    if type(value) is not OccurrenceProvenance:
        raise TypeError(
            "provenance entries must be exact OccurrenceProvenance instances"
        )
    return OccurrenceProvenance(
        provenance_key=value.provenance_key,
        native_occurrence_sha256=value.native_occurrence_sha256,
        source_item_keys=value.source_item_keys,
        field_statuses=value.field_statuses,
        private_format_id=value.private_format_id,
        private_payload_bytes=value.private_payload_bytes,
    )


def _preflight_provenance_entry_tuples_and_payloads(
    entries: Tuple[object, ...],
) -> Tuple[int, int]:
    total_source_links = 0
    total_payload_bytes = 0
    for entry in entries:
        if type(entry) is not OccurrenceProvenance:
            raise TypeError(
                "provenance entries must be exact OccurrenceProvenance instances"
            )
        if type(entry.source_item_keys) is not tuple:
            raise TypeError("source_item_keys must be an exact tuple")
        _bounded_length(
            entry.source_item_keys,
            maximum=MAXIMUM_SOURCE_LINKS_PER_OCCURRENCE,
            name="provenance source links per occurrence",
        )
        if type(entry.field_statuses) is not tuple:
            raise TypeError("field_statuses must be an exact tuple")
        _bounded_length(
            entry.field_statuses,
            maximum=MAXIMUM_FIELD_STATUSES_PER_OCCURRENCE,
            name="field statuses per occurrence",
        )
        payload = _bounded_payload(
            entry.private_payload_bytes,
            name="private provenance payload",
        )
        total_source_links += len(entry.source_item_keys)
        if total_source_links > MAXIMUM_TOTAL_PROVENANCE_SOURCE_LINKS:
            raise AdapterEvidenceResourceError(
                "aggregate provenance source links exceed their resource ceiling"
            )
        total_payload_bytes += len(payload)
        if total_payload_bytes > MAXIMUM_PRIVATE_PAYLOAD_BYTES:
            raise AdapterEvidenceResourceError(
                "provenance payload bytes exceed the private payload ceiling"
            )
    return total_source_links, total_payload_bytes


@dataclass(frozen=True)
class PrivateProvenance:
    source_sha256: str
    native_observation_sha256: str
    policy_sha256: str
    entries: Tuple[OccurrenceProvenance, ...]

    def __post_init__(self) -> None:
        _contract._validated_sha256(self.source_sha256, name="source_sha256")
        _contract._validated_sha256(
            self.native_observation_sha256, name="native_observation_sha256"
        )
        _contract._validated_sha256(self.policy_sha256, name="policy_sha256")
        if type(self.entries) is not tuple:
            raise TypeError("provenance entries must be an exact tuple")
        _bounded_length(
            self.entries,
            maximum=MAXIMUM_SEMANTIC_OCCURRENCES,
            name="provenance entries",
        )
        _preflight_provenance_entry_tuples_and_payloads(self.entries)
        entries = tuple(
            _snapshot_occurrence_provenance(entry) for entry in self.entries
        )
        if sum(len(entry.source_item_keys) for entry in entries) > (
            MAXIMUM_TOTAL_PROVENANCE_SOURCE_LINKS
        ):
            raise AdapterEvidenceResourceError(
                "aggregate provenance source links exceed their resource ceiling"
            )
        if sum(len(entry.private_payload_bytes) for entry in entries) > (
            MAXIMUM_PRIVATE_PAYLOAD_BYTES
        ):
            raise AdapterEvidenceResourceError(
                "provenance payload bytes exceed the private payload ceiling"
            )
        keys = tuple(entry.provenance_key for entry in entries)
        if len(set(keys)) != len(keys):
            raise ValueError("provenance_key values must be unique")
        object.__setattr__(
            self,
            "entries",
            tuple(sorted(entries, key=lambda entry: entry.provenance_key)),
        )

    @property
    def private_provenance_sha256(self) -> str:
        return private_provenance_digest(self)


def _snapshot_private_provenance(value: object) -> PrivateProvenance:
    if type(value) is not PrivateProvenance:
        raise TypeError("provenance must be exact PrivateProvenance")
    return PrivateProvenance(
        value.source_sha256,
        value.native_observation_sha256,
        value.policy_sha256,
        value.entries,
    )


def private_provenance_digest(provenance: PrivateProvenance) -> str:
    snapshot = _snapshot_private_provenance(provenance)
    if not snapshot.entries:
        return _contract.EMPTY_PRIVATE_PROVENANCE_SHA256
    return _contract._domain_digest(
        _contract.PRIVATE_PROVENANCE_DIGEST_DOMAIN,
        {
            "entries": [
                {
                    "field_statuses": [
                        {
                            "field_name": status.field_name,
                            "reason_code": status.reason_code,
                            "status": status.status.value,
                        }
                        for status in entry.field_statuses
                    ],
                    "native_occurrence_sha256": (
                        entry.native_occurrence_sha256
                    ),
                    "private_format_id": entry.private_format_id,
                    "private_payload": _blob_payload(
                        entry.private_payload_bytes
                    ),
                    "provenance_key": entry.provenance_key,
                    "source_item_keys": list(entry.source_item_keys),
                }
                for entry in snapshot.entries
            ],
            "native_observation_sha256": snapshot.native_observation_sha256,
            "policy_sha256": snapshot.policy_sha256,
            "source_sha256": snapshot.source_sha256,
        },
    )


def _native_occurrence_payload_from_detached(
    detached: EventConfiguration, index: int
) -> object:
    if type(index) is not int:
        raise TypeError("occurrence index must be an exact integer")
    if index < 0 or index >= len(detached.events):
        raise IndexError("occurrence index is outside the configuration")
    assert detached.observed is not None
    event = detached.events[index]
    observation = detached.observed.events[index]
    return {
        "event": {
            "event_time": _contract._float_hex(
                event.event_time, name="event time"
            ),
            "event_type": event.event_type,
            "marks": {
                name: [
                    _contract._float_hex(value, name="mark value")
                    for value in vector
                ]
                for name, vector in event.marks.items()
            },
        },
        "observation": {
            "observed_marks": sorted(observation.observed_marks),
            "time_observed": observation.time_observed,
            "type_observed": observation.type_observed,
        },
        "schema_sha256": _contract.feature_schema_digest(detached.schema),
    }


def _native_occurrence_payload(
    configuration: EventConfiguration, index: int
) -> object:
    snapshot = snapshot_bounded_native_configuration(configuration)
    detached = _contract.rebuild_detached_native_configuration(snapshot)
    return _native_occurrence_payload_from_detached(detached, index)


def native_occurrence_digest(
    configuration: EventConfiguration, index: int
) -> str:
    return _contract._domain_digest(
        NATIVE_OCCURRENCE_DIGEST_DOMAIN,
        _native_occurrence_payload(configuration, index),
    )


def native_occurrence_digests(
    configuration: EventConfiguration,
) -> Tuple[str, ...]:
    snapshot = snapshot_bounded_native_configuration(configuration)
    detached = _contract.rebuild_detached_native_configuration(snapshot)
    return tuple(
        _contract._domain_digest(
            NATIVE_OCCURRENCE_DIGEST_DOMAIN,
            _native_occurrence_payload_from_detached(detached, index),
        )
        for index in range(len(detached.events))
    )


def training_group_set_digest(split_manifest: SplitManifest) -> str:
    snapshot = snapshot_bounded_split_manifest(split_manifest)
    groups = tuple(
        sorted(
            {
                entry.group_id
                for entry in snapshot.entries
                if entry.split == "train"
            }
        )
    )
    return _contract._domain_digest(
        TRAINING_GROUP_SET_DIGEST_DOMAIN,
        {"group_ids": list(groups), "unicode_profile": _contract.UNICODE_PROFILE},
    )


@dataclass(frozen=True)
class FittedAdapterState:
    """Canonical private bytes and all bindings for fitted preprocessing."""

    descriptor_sha256: str
    adapter_id: str
    adapter_version: str
    contract_version: str
    policy_sha256: str
    schema_sha256: str
    split_manifest_sha256: str
    training_group_set_sha256: str
    fit_configuration_format_id: str
    fit_configuration_bytes: bytes
    parameter_format_id: str
    parameter_bytes: bytes
    unseen_value_policy_id: str

    def __post_init__(self) -> None:
        _bounded_payload(
            self.fit_configuration_bytes, name="fit configuration"
        )
        _bounded_payload(self.parameter_bytes, name="fitted parameters")
        if len(self.fit_configuration_bytes) + len(self.parameter_bytes) > (
            MAXIMUM_PRIVATE_PAYLOAD_BYTES
        ):
            raise AdapterEvidenceResourceError(
                "fitted-state bytes exceed the private payload ceiling"
            )
        for name in (
            "descriptor_sha256",
            "policy_sha256",
            "schema_sha256",
            "split_manifest_sha256",
            "training_group_set_sha256",
        ):
            _contract._validated_sha256(getattr(self, name), name=name)
        _contract._validated_public_id(self.adapter_id, name="adapter_id")
        if type(self.adapter_version) is not str or _contract._VERSION_RE.fullmatch(
            self.adapter_version
        ) is None:
            raise ValueError("adapter_version must be a canonical positive decimal")
        if type(self.contract_version) is not str:
            raise TypeError("contract_version must be an exact string")
        if self.contract_version != _contract.ADAPTER_CONTRACT_VERSION:
            raise ValueError("unsupported adapter contract version")
        for name in (
            "fit_configuration_format_id",
            "parameter_format_id",
            "unseen_value_policy_id",
        ):
            _contract._validated_public_id(getattr(self, name), name=name)

    @property
    def fitted_state_sha256(self) -> str:
        return fitted_adapter_state_digest(self)


def _snapshot_fitted_state(value: object) -> FittedAdapterState:
    if type(value) is not FittedAdapterState:
        raise TypeError("fitted_state must be an exact FittedAdapterState")
    return FittedAdapterState(
        descriptor_sha256=value.descriptor_sha256,
        adapter_id=value.adapter_id,
        adapter_version=value.adapter_version,
        contract_version=value.contract_version,
        policy_sha256=value.policy_sha256,
        schema_sha256=value.schema_sha256,
        split_manifest_sha256=value.split_manifest_sha256,
        training_group_set_sha256=value.training_group_set_sha256,
        fit_configuration_format_id=value.fit_configuration_format_id,
        fit_configuration_bytes=value.fit_configuration_bytes,
        parameter_format_id=value.parameter_format_id,
        parameter_bytes=value.parameter_bytes,
        unseen_value_policy_id=value.unseen_value_policy_id,
    )


def fitted_adapter_state_digest(state: FittedAdapterState) -> str:
    snapshot = _snapshot_fitted_state(state)
    return _contract._domain_digest(
        _contract.FITTED_STATE_DIGEST_DOMAIN,
        {
            "adapter_id": snapshot.adapter_id,
            "adapter_version": snapshot.adapter_version,
            "contract_version": snapshot.contract_version,
            "descriptor_sha256": snapshot.descriptor_sha256,
            "fit_configuration": {
                "format_id": snapshot.fit_configuration_format_id,
                **_blob_payload(snapshot.fit_configuration_bytes),
            },
            "fitted_parameters": {
                "format_id": snapshot.parameter_format_id,
                **_blob_payload(snapshot.parameter_bytes),
            },
            "policy_sha256": snapshot.policy_sha256,
            "schema_sha256": snapshot.schema_sha256,
            "split_manifest_sha256": snapshot.split_manifest_sha256,
            "training_group_set_sha256": snapshot.training_group_set_sha256,
            "unseen_value_policy_id": snapshot.unseen_value_policy_id,
        },
    )


@dataclass(frozen=True)
class SemanticReconstruction:
    """Adapter-policy canonical semantic source reconstruction bytes."""

    source_sha256: str
    schema_sha256: str
    policy_sha256: str
    semantic_format_id: str
    record_count: int
    canonical_payload_bytes: bytes

    def __post_init__(self) -> None:
        _bounded_payload(
            self.canonical_payload_bytes, name="semantic payload"
        )
        _contract._validated_sha256(self.source_sha256, name="source_sha256")
        _contract._validated_sha256(self.schema_sha256, name="schema_sha256")
        _contract._validated_sha256(self.policy_sha256, name="policy_sha256")
        _contract._validated_public_id(
            self.semantic_format_id, name="semantic_format_id"
        )
        _contract._validated_nonnegative_size(
            self.record_count, name="record_count"
        )
        if self.record_count > MAXIMUM_INVENTORY_ITEMS:
            raise AdapterEvidenceResourceError(
                "record_count exceeds its resource ceiling"
            )

    @property
    def semantic_reconstruction_sha256(self) -> str:
        return semantic_reconstruction_digest(self)


def _snapshot_reconstruction(value: object) -> SemanticReconstruction:
    if type(value) is not SemanticReconstruction:
        raise TypeError("reconstruction must be an exact SemanticReconstruction")
    return SemanticReconstruction(
        source_sha256=value.source_sha256,
        schema_sha256=value.schema_sha256,
        policy_sha256=value.policy_sha256,
        semantic_format_id=value.semantic_format_id,
        record_count=value.record_count,
        canonical_payload_bytes=value.canonical_payload_bytes,
    )


def semantic_reconstruction_digest(value: SemanticReconstruction) -> str:
    snapshot = _snapshot_reconstruction(value)
    return _contract._domain_digest(
        _contract.SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN,
        {
            "canonical_payload": _blob_payload(
                snapshot.canonical_payload_bytes
            ),
            "policy_sha256": snapshot.policy_sha256,
            "record_count": snapshot.record_count,
            "schema_sha256": snapshot.schema_sha256,
            "semantic_format_id": snapshot.semantic_format_id,
            "source_sha256": snapshot.source_sha256,
        },
    )


def _preflight_exact_tuple(
    value: object, *, maximum: int, name: str
) -> Tuple[object, ...]:
    """Check tuple identity and size without inspecting an element."""

    if type(value) is not tuple:
        raise TypeError("{} must be an exact tuple".format(name))
    _bounded_length(value, maximum=maximum, name=name)
    return value


def _preflight_schema(schema: object) -> FeatureSchema:
    """Bound an exact schema before validation, sorting, copying, or hashing."""

    if type(schema) is not FeatureSchema:
        raise TypeError("schema must be an exact FeatureSchema")
    event_types = _preflight_exact_tuple(
        schema.event_types,
        maximum=MAXIMUM_DECLARED_EVENT_TYPES,
        name="declared event types",
    )
    if not event_types:
        raise ValueError("schema requires at least one declared event type")
    if type(schema.time_reference) is not TimeReference:
        raise TypeError("time_reference must be an exact TimeReference")
    atoms = _preflight_exact_tuple(
        schema.time_reference.atoms,
        maximum=MAXIMUM_TIME_ATOMS,
        name="time-reference atoms",
    )
    weights = _preflight_exact_tuple(
        schema.time_reference.atom_weights,
        maximum=MAXIMUM_TIME_ATOMS,
        name="time-reference atom weights",
    )
    if len(atoms) != len(weights):
        raise ValueError("time-reference atoms and weights must align")

    field_groups = []
    for event_type in event_types:
        if type(event_type) is not EventTypeSchema:
            raise TypeError(
                "declared event types must be exact EventTypeSchema instances"
            )
        fields = _preflight_exact_tuple(
            event_type.fields,
            maximum=MAXIMUM_FIELDS_PER_EVENT_TYPE,
            name="declared fields per event type",
        )
        field_groups.append(fields)
    for fields in field_groups:
        scalar_coordinates = 0
        for field in fields:
            if type(field) is not ContinuousField:
                raise TypeError(
                    "declared fields must be exact ContinuousField instances"
                )
            if type(field.dimension) is not int:
                raise TypeError("field dimensions must be exact integers")
            if field.dimension <= 0:
                raise ValueError("field dimensions must be positive")
            if field.dimension > MAXIMUM_SCALAR_COORDINATES_PER_EVENT_TYPE:
                raise AdapterEvidenceResourceError(
                    "one field dimension exceeds the scalar-coordinate ceiling"
                )
            scalar_coordinates += field.dimension
            if (
                scalar_coordinates
                > MAXIMUM_SCALAR_COORDINATES_PER_EVENT_TYPE
            ):
                raise AdapterEvidenceResourceError(
                    "one event type exceeds the scalar-coordinate ceiling"
                )
    return schema


def _snapshot_bounded_event_marks(
    marks: object,
) -> Tuple[Tuple[str, Tuple[float, ...]], ...]:
    """Copy one possibly proxy-backed map through a bounded trusted iterator."""

    if type(marks) is not MappingProxyType:
        raise TypeError("event marks must use the exact immutable mapping")
    try:
        reported_size = len(marks)
    except Exception:
        raise TypeError("event marks have an invalid immutable mapping") from None
    if reported_size > MAXIMUM_FIELDS_PER_EVENT_TYPE:
        raise AdapterEvidenceResourceError(
            "marks per occurrence exceed their resource ceiling"
        )
    try:
        iterator = iter(marks.items())
        raw_items = []
        for _ in range(MAXIMUM_FIELDS_PER_EVENT_TYPE + 1):
            try:
                raw_items.append(next(iterator))
            except StopIteration:
                break
    except Exception:
        raise TypeError("event marks have an invalid immutable mapping") from None
    if len(raw_items) > MAXIMUM_FIELDS_PER_EVENT_TYPE:
        raise AdapterEvidenceResourceError(
            "marks per occurrence exceed their resource ceiling"
        )
    if len(raw_items) != reported_size:
        raise TypeError("event mark mapping length is inconsistent")

    result = []
    seen_names = set()
    scalar_coordinates = 0
    for item in raw_items:
        if type(item) is not tuple or len(item) != 2:
            raise TypeError("event mark items must be exact key-value tuples")
        name, vector = item
        validated_name = _contract._validated_private_text(
            name, name="mark name"
        )
        if validated_name in seen_names:
            raise ValueError("event mark names must be unique")
        seen_names.add(validated_name)
        if type(vector) is not tuple:
            raise TypeError("mark vectors must be exact tuples")
        vector_size = _bounded_length(
            vector,
            maximum=MAXIMUM_SCALAR_COORDINATES_PER_OCCURRENCE,
            name="one mark vector",
        )
        scalar_coordinates += vector_size
        if scalar_coordinates > MAXIMUM_SCALAR_COORDINATES_PER_OCCURRENCE:
            raise AdapterEvidenceResourceError(
                "one occurrence exceeds the scalar-coordinate ceiling"
            )
        canonical_vector = []
        for value in vector:
            if type(value) is not float:
                raise TypeError("mark coordinates must be exact floats")
            _contract._float_hex(value, name="mark value")
            canonical_vector.append(value)
        result.append((validated_name, tuple(canonical_vector)))
    return tuple(result)


def _event_id_metadata_size(
    value: object, *, allow_integer: bool = False
) -> int:
    """Validate the Phase-C sidecar grammar without invoking arbitrary hash."""

    if value is None:
        return 0
    if type(value) is str:
        validated = _contract._validated_private_text(value, name="event_id")
        encoded_size = len(validated.encode("utf-8"))
        if encoded_size > MAXIMUM_EVENT_ID_COMPONENT_BYTES:
            raise AdapterEvidenceResourceError(
                "event_id text exceeds its byte ceiling"
            )
        return 1 + encoded_size
    if type(value) is int:
        if not allow_integer:
            raise TypeError(
                "event_id must be None, exact text, or a shallow exact tuple"
            )
        if abs(value) > MAXIMUM_EVENT_ID_INTEGER_ABSOLUTE_VALUE:
            raise AdapterEvidenceResourceError(
                "event_id integer exceeds its canonical range"
            )
        return 9
    if type(value) is tuple:
        _bounded_length(
            value,
            maximum=MAXIMUM_EVENT_ID_TUPLE_ARITY,
            name="event_id tuple",
        )
        if not value:
            raise ValueError("event_id tuples must not be empty")
        total = 1
        for component in value:
            if type(component) not in (str, int):
                raise TypeError(
                    "event_id tuple components must be exact strings or integers"
                )
            total += _event_id_metadata_size(
                component, allow_integer=True
            )
        return total
    raise TypeError(
        "event_id must be None, an exact string, or a shallow exact tuple"
    )


def _preflight_native_configuration(
    configuration: object,
) -> EventConfiguration:
    """Bound native tuples and mark vectors before rebuilding their tree."""

    if type(configuration) is not EventConfiguration:
        raise TypeError("configuration must be an exact EventConfiguration")
    events = _preflight_exact_tuple(
        configuration.events,
        maximum=MAXIMUM_SEMANTIC_OCCURRENCES,
        name="native occurrences",
    )
    if type(configuration.observed) is not ObservationPattern:
        raise TypeError("observed must be an exact ObservationPattern")
    observations = _preflight_exact_tuple(
        configuration.observed.events,
        maximum=MAXIMUM_SEMANTIC_OCCURRENCES,
        name="native observations",
    )
    if len(events) != len(observations):
        raise ValueError("native occurrences and observations must align")
    _preflight_schema(configuration.schema)

    event_id_metadata_bytes = 0
    for event in events:
        if type(event) is not Event:
            raise TypeError("native occurrences must be exact Event instances")
        if type(event.event_time) is not float or type(event.event_type) is not int:
            raise TypeError("event coordinates must use exact scalar types")
        _contract._float_hex(event.event_time, name="event time")
        event_id_metadata_bytes += _event_id_metadata_size(event.event_id)
        if event_id_metadata_bytes > MAXIMUM_EVENT_ID_METADATA_BYTES:
            raise AdapterEvidenceResourceError(
                "aggregate event_id metadata exceeds its byte ceiling"
            )
    # Resource-only event-ID accounting is a separate first pass.  Otherwise a
    # hostile mark mapping on the event that crosses the aggregate byte ceiling
    # could turn a deterministic resource rejection into a shape failure.
    for event in events:
        _snapshot_bounded_event_marks(event.marks)
    for observation in observations:
        if type(observation) is not EventObservation:
            raise TypeError(
                "native observations must be exact EventObservation instances"
            )
        if type(observation.observed_marks) is not frozenset:
            raise TypeError("observed marks must be an exact frozenset")
        _bounded_length(
            observation.observed_marks,
            maximum=MAXIMUM_FIELDS_PER_EVENT_TYPE,
            name="observed marks per occurrence",
        )
        if type(observation.time_observed) is not bool or type(
            observation.type_observed
        ) is not bool:
            raise TypeError("observation flags must be exact booleans")
        for name in observation.observed_marks:
            _contract._validated_private_text(name, name="observed mark name")
    return configuration


def _preflight_split_manifest(value: object) -> SplitManifest:
    """Bound a split before its constructor builds maps, sets, and sort keys."""

    if type(value) is not SplitManifest:
        raise TypeError("split_manifest must be an exact SplitManifest")
    entries = _preflight_exact_tuple(
        value.entries,
        maximum=MAXIMUM_SPLIT_ENTRIES,
        name="split entries",
    )
    if not entries:
        raise ValueError("a split manifest requires at least one entry")
    groups = set()
    for entry in entries:
        if type(entry) is not SamplePartition:
            raise TypeError(
                "split entries must be exact SamplePartition instances"
            )
        group_id = _contract._validated_private_text(
            entry.group_id, name="split group_id"
        )
        groups.add(group_id)
        if len(groups) > MAXIMUM_SPLIT_GROUPS:
            raise AdapterEvidenceResourceError(
                "split groups exceed their resource ceiling"
            )
    return value


def snapshot_bounded_schema(schema: FeatureSchema) -> FeatureSchema:
    """Return an exact schema only after generated-v1 structural preflight."""

    _preflight_schema(schema)
    return _contract.rebuild_exact_schema(schema)


def snapshot_bounded_split_manifest(value: SplitManifest) -> SplitManifest:
    """Return an exact split only after entry and natural-group preflight."""

    _preflight_split_manifest(value)
    return SplitManifest(value.entries)


def snapshot_bounded_native_configuration(
    configuration: EventConfiguration,
) -> EventConfiguration:
    """Rebuild native state from bounded copies of every untrusted container."""

    source = _preflight_native_configuration(configuration)
    if type(source.sample_id) is not str or type(source.group_id) is not str:
        raise TypeError("configuration identifiers must be exact strings")
    if source.sample_id:
        _contract._validated_private_text(
            source.sample_id, name="configuration sample_id"
        )
    if source.group_id:
        _contract._validated_private_text(
            source.group_id, name="configuration group_id"
        )
    assert source.observed is not None
    try:
        events = tuple(
            Event(
                event_time=event.event_time,
                event_type=event.event_type,
                marks=dict(_snapshot_bounded_event_marks(event.marks)),
                event_id=event.event_id,
            )
            for event in source.events
        )
        observations = ObservationPattern(
            events=tuple(
                EventObservation(
                    time_observed=observation.time_observed,
                    type_observed=observation.type_observed,
                    observed_marks=frozenset(observation.observed_marks),
                )
                for observation in source.observed.events
            ),
            cardinality_observed=source.observed.cardinality_observed,
        )
        return EventConfiguration(
            schema=snapshot_bounded_schema(source.schema),
            events=events,
            observed=observations,
            sample_id=source.sample_id,
            group_id=source.group_id,
        )
    except AdapterEvidenceResourceError:
        raise
    except Exception:
        raise TypeError(
            "native configuration cannot be rebuilt from bounded exact values"
        ) from None


def _preflight_evidence_leaves(value: object) -> None:
    """Bound every leaf tuple before inspecting, copying, sorting, or hashing."""

    try:
        inventory = value.inventory  # type: ignore[attr-defined]
        coverage = value.coverage  # type: ignore[attr-defined]
        static_context = value.static_context  # type: ignore[attr-defined]
        evaluation_labels = value.evaluation_labels  # type: ignore[attr-defined]
        provenance = value.provenance  # type: ignore[attr-defined]
        fitted_state = value.fitted_state  # type: ignore[attr-defined]
        reconstruction = value.reconstruction  # type: ignore[attr-defined]
    except AttributeError as exc:
        raise TypeError("evidence bundle is missing a required leaf") from exc
    if type(inventory) is not SourceInventory:
        raise TypeError("inventory must be an exact SourceInventory")
    if type(coverage) is not SourceCoverageLedger:
        raise TypeError("coverage must be an exact SourceCoverageLedger")
    if type(static_context) is not StaticContext:
        raise TypeError("static_context must be an exact StaticContext")
    if type(evaluation_labels) is not EvaluationLabels:
        raise TypeError("evaluation_labels must be exact EvaluationLabels")
    if type(provenance) is not PrivateProvenance:
        raise TypeError("provenance must be exact PrivateProvenance")
    if fitted_state is not None and type(fitted_state) is not FittedAdapterState:
        raise TypeError("fitted_state must be an exact FittedAdapterState")
    if type(reconstruction) is not SemanticReconstruction:
        raise TypeError("reconstruction must be an exact SemanticReconstruction")

    inventory_items = _preflight_exact_tuple(
        inventory.items,
        maximum=MAXIMUM_INVENTORY_ITEMS,
        name="inventory items",
    )
    coverage_entries = _preflight_exact_tuple(
        coverage.entries,
        maximum=MAXIMUM_INVENTORY_ITEMS,
        name="coverage entries",
    )
    static_entries = _preflight_exact_tuple(
        static_context.entries,
        maximum=MAXIMUM_KEYED_LEAF_ENTRIES,
        name="static entries",
    )
    label_entries = _preflight_exact_tuple(
        evaluation_labels.entries,
        maximum=MAXIMUM_KEYED_LEAF_ENTRIES,
        name="evaluation-label entries",
    )
    provenance_entries = _preflight_exact_tuple(
        provenance.entries,
        maximum=MAXIMUM_SEMANTIC_OCCURRENCES,
        name="provenance entries",
    )

    _preflight_coverage_entry_tuples(coverage_entries)
    total_source_links, provenance_payload_bytes = (
        _preflight_provenance_entry_tuples_and_payloads(provenance_entries)
    )
    if total_source_links > len(inventory_items):
        raise AdapterEvidenceResourceError(
            "provenance source links exceed inventoried source items"
        )

    inventory_payload_bytes = _preflight_inventory_payloads(inventory_items)
    static_payload_bytes = _preflight_keyed_payloads(
        static_entries,
        expected_type=StaticContextEntry,
        payload_name="static context payload",
        entry_label="static",
    )
    label_payload_bytes = _preflight_keyed_payloads(
        label_entries,
        expected_type=EvaluationLabelEntry,
        payload_name="evaluation label payload",
        entry_label="label",
    )
    fitted_payload_bytes = 0
    if fitted_state is not None:
        fitted_payload_bytes += len(
            _bounded_payload(
                fitted_state.fit_configuration_bytes,
                name="fit configuration",
            )
        )
        fitted_payload_bytes += len(
            _bounded_payload(
                fitted_state.parameter_bytes,
                name="fitted parameters",
            )
        )
    reconstruction_payload_bytes = len(
        _bounded_payload(
            reconstruction.canonical_payload_bytes,
            name="semantic payload",
        )
    )
    raw_payload_bytes = 0
    raw_reconstruction = getattr(value, "raw_reconstruction_bytes", None)
    if raw_reconstruction is not None:
        if type(raw_reconstruction) is not bytes:
            raise TypeError("raw reconstruction must be exact immutable bytes")
        _bounded_length(
            raw_reconstruction,
            maximum=MAXIMUM_SOURCE_BYTES,
            name="raw reconstruction",
        )
        raw_payload_bytes = len(raw_reconstruction)
    total_payload_bytes = (
        inventory_payload_bytes
        + static_payload_bytes
        + label_payload_bytes
        + provenance_payload_bytes
        + fitted_payload_bytes
        + reconstruction_payload_bytes
        + raw_payload_bytes
    )
    if total_payload_bytes > MAXIMUM_PRIVATE_PAYLOAD_BYTES:
        raise AdapterEvidenceResourceError(
            "aggregate private payload bytes exceed their aggregate ceiling"
        )

    for entry in provenance_entries:
        field_statuses = entry.field_statuses
        if any(type(status) is not SourceFieldStatus for status in field_statuses):
            raise TypeError(
                "field statuses must be exact SourceFieldStatus instances"
            )


def _aggregate_private_payload_size(
    *,
    inventory: SourceInventory,
    static_context: StaticContext,
    evaluation_labels: EvaluationLabels,
    provenance: PrivateProvenance,
    fitted_state: Optional[FittedAdapterState],
    reconstruction: SemanticReconstruction,
    raw_reconstruction_bytes: Optional[bytes] = None,
) -> int:
    """Return payload bytes only; serialized artifact size is a separate gate."""

    total = sum(
        len(item.canonical_item_bytes) for item in inventory.items
    )
    total += sum(
        len(entry.canonical_payload_bytes)
        for entry in static_context.entries
    )
    total += sum(
        len(entry.canonical_payload_bytes)
        for entry in evaluation_labels.entries
    )
    total += sum(
        len(entry.private_payload_bytes) for entry in provenance.entries
    )
    if fitted_state is not None:
        total += len(fitted_state.fit_configuration_bytes)
        total += len(fitted_state.parameter_bytes)
    total += len(reconstruction.canonical_payload_bytes)
    if raw_reconstruction_bytes is not None:
        total += len(raw_reconstruction_bytes)
    return total


@dataclass(frozen=True)
class ExpectedAdapterEvidence:
    """Independent full oracle for one decision-capable validation.

    This object must be built through a source-bound implementation independent
    of the adapter under test.  It binds the expected detached native state and
    every Phase-C leaf; comparing only inventory and reconstruction is a
    development diagnostic and cannot establish semantic conformance.
    """

    native_observation_sha256: str
    inventory: SourceInventory
    coverage: SourceCoverageLedger
    static_context: StaticContext
    evaluation_labels: EvaluationLabels
    provenance: PrivateProvenance
    fitted_state: Optional[FittedAdapterState]
    reconstruction: SemanticReconstruction

    def __post_init__(self) -> None:
        _preflight_evidence_leaves(self)
        _contract._validated_sha256(
            self.native_observation_sha256,
            name="expected native_observation_sha256",
        )
        object.__setattr__(self, "inventory", _snapshot_inventory(self.inventory))
        object.__setattr__(self, "coverage", _snapshot_coverage(self.coverage))
        object.__setattr__(
            self, "static_context", _snapshot_static_context(self.static_context)
        )
        object.__setattr__(
            self,
            "evaluation_labels",
            _snapshot_evaluation_labels(self.evaluation_labels),
        )
        object.__setattr__(
            self, "provenance", _snapshot_private_provenance(self.provenance)
        )
        if self.fitted_state is not None:
            object.__setattr__(
                self, "fitted_state", _snapshot_fitted_state(self.fitted_state)
            )
        object.__setattr__(
            self, "reconstruction", _snapshot_reconstruction(self.reconstruction)
        )
        if _aggregate_private_payload_size(
            inventory=self.inventory,
            static_context=self.static_context,
            evaluation_labels=self.evaluation_labels,
            provenance=self.provenance,
            fitted_state=self.fitted_state,
            reconstruction=self.reconstruction,
        ) > MAXIMUM_PRIVATE_PAYLOAD_BYTES:
            raise AdapterEvidenceResourceError(
                "expected private payload bytes exceed their aggregate ceiling"
            )

    @property
    def expected_evidence_sha256(self) -> str:
        return expected_adapter_evidence_digest(self)


def _snapshot_expected_evidence(value: object) -> ExpectedAdapterEvidence:
    if type(value) is not ExpectedAdapterEvidence:
        raise TypeError(
            "expected_evidence must be an exact ExpectedAdapterEvidence"
        )
    return ExpectedAdapterEvidence(
        native_observation_sha256=value.native_observation_sha256,
        inventory=value.inventory,
        coverage=value.coverage,
        static_context=value.static_context,
        evaluation_labels=value.evaluation_labels,
        provenance=value.provenance,
        fitted_state=value.fitted_state,
        reconstruction=value.reconstruction,
    )


def expected_adapter_evidence_digest(value: ExpectedAdapterEvidence) -> str:
    snapshot = _snapshot_expected_evidence(value)
    return _contract._domain_digest(
        EXPECTED_EVIDENCE_DIGEST_DOMAIN,
        {
            "coverage": {
                "coverage_ledger_sha256": source_coverage_ledger_digest(
                    snapshot.coverage
                ),
                "policy_sha256": snapshot.coverage.policy_sha256,
                "source_inventory_sha256": (
                    snapshot.coverage.source_inventory_sha256
                ),
                "source_sha256": snapshot.coverage.source_sha256,
                "source_size_bytes": snapshot.coverage.source_size_bytes,
            },
            "evaluation_labels": {
                "evaluation_labels_sha256": evaluation_labels_digest(
                    snapshot.evaluation_labels
                ),
                "format_id": snapshot.evaluation_labels.format_id,
                "policy_sha256": snapshot.evaluation_labels.policy_sha256,
                "source_sha256": snapshot.evaluation_labels.source_sha256,
            },
            "fitted_state_sha256": (
                _contract.NO_FITTED_STATE_SHA256
                if snapshot.fitted_state is None
                else fitted_adapter_state_digest(snapshot.fitted_state)
            ),
            "native_observation_sha256": snapshot.native_observation_sha256,
            "private_provenance": {
                "native_observation_sha256": (
                    snapshot.provenance.native_observation_sha256
                ),
                "policy_sha256": snapshot.provenance.policy_sha256,
                "private_provenance_sha256": private_provenance_digest(
                    snapshot.provenance
                ),
                "source_sha256": snapshot.provenance.source_sha256,
            },
            "semantic_reconstruction_sha256": semantic_reconstruction_digest(
                snapshot.reconstruction
            ),
            "source_inventory_sha256": source_inventory_digest(
                snapshot.inventory
            ),
            "static_context": {
                "format_id": snapshot.static_context.format_id,
                "policy_sha256": snapshot.static_context.policy_sha256,
                "source_sha256": snapshot.static_context.source_sha256,
                "static_context_sha256": static_context_digest(
                    snapshot.static_context
                ),
            },
        },
    )


@dataclass(frozen=True)
class CompleteAdaptedEventSample:
    """One Phase-B sample plus exact Phase-C private evidence leaves."""

    sample: AdaptedEventSample
    inventory: SourceInventory
    coverage: SourceCoverageLedger
    static_context: StaticContext
    evaluation_labels: EvaluationLabels
    provenance: PrivateProvenance
    fitted_state: Optional[FittedAdapterState]
    reconstruction: SemanticReconstruction
    raw_reconstruction_bytes: Optional[bytes] = None

    def __post_init__(self) -> None:
        if type(self.sample) is not AdaptedEventSample:
            raise TypeError("sample must be an exact AdaptedEventSample")
        _preflight_native_configuration(self.sample.configuration)
        _preflight_evidence_leaves(self)
        object.__setattr__(self, "inventory", _snapshot_inventory(self.inventory))
        object.__setattr__(self, "coverage", _snapshot_coverage(self.coverage))
        object.__setattr__(
            self, "static_context", _snapshot_static_context(self.static_context)
        )
        object.__setattr__(
            self,
            "evaluation_labels",
            _snapshot_evaluation_labels(self.evaluation_labels),
        )
        object.__setattr__(
            self, "provenance", _snapshot_private_provenance(self.provenance)
        )
        if self.fitted_state is not None:
            object.__setattr__(
                self, "fitted_state", _snapshot_fitted_state(self.fitted_state)
            )
        object.__setattr__(
            self, "reconstruction", _snapshot_reconstruction(self.reconstruction)
        )
        if self.raw_reconstruction_bytes is not None and type(
            self.raw_reconstruction_bytes
        ) is not bytes:
            raise TypeError("raw reconstruction must be exact immutable bytes")
        if self.raw_reconstruction_bytes is not None:
            _bounded_length(
                self.raw_reconstruction_bytes,
                maximum=MAXIMUM_SOURCE_BYTES,
                name="raw reconstruction",
            )
        if _complete_private_payload_size(self) > MAXIMUM_PRIVATE_PAYLOAD_BYTES:
            raise AdapterEvidenceResourceError(
                "complete private payload bytes exceed their aggregate ceiling"
            )


def _complete_private_payload_size(value: CompleteAdaptedEventSample) -> int:
    return _aggregate_private_payload_size(
        inventory=value.inventory,
        static_context=value.static_context,
        evaluation_labels=value.evaluation_labels,
        provenance=value.provenance,
        fitted_state=value.fitted_state,
        reconstruction=value.reconstruction,
        raw_reconstruction_bytes=value.raw_reconstruction_bytes,
    )


def _snapshot_complete(value: object) -> CompleteAdaptedEventSample:
    if type(value) is not CompleteAdaptedEventSample:
        raise TypeError("complete must be an exact CompleteAdaptedEventSample")
    if type(value.sample) is not AdaptedEventSample:
        raise TypeError("sample must be an exact AdaptedEventSample")
    configuration = value.sample.configuration
    if type(configuration) is not EventConfiguration:
        raise TypeError("configuration must be an exact EventConfiguration")
    _preflight_evidence_leaves(value)
    _preflight_native_configuration(configuration)
    _contract._validated_private_text(
        configuration.sample_id,
        name="configuration sample_id",
    )
    _contract._validated_private_text(
        configuration.group_id,
        name="configuration group_id",
    )
    configuration_snapshot = snapshot_bounded_native_configuration(
        configuration
    )
    sample = AdaptedEventSample(configuration_snapshot, value.sample.manifest)
    return CompleteAdaptedEventSample(
        sample=sample,
        inventory=value.inventory,
        coverage=value.coverage,
        static_context=value.static_context,
        evaluation_labels=value.evaluation_labels,
        provenance=value.provenance,
        fitted_state=value.fitted_state,
        reconstruction=value.reconstruction,
        raw_reconstruction_bytes=value.raw_reconstruction_bytes,
    )


def _validate_leaf_binding(
    actual: str,
    expected: str,
    *,
    label: str,
) -> None:
    if actual != expected:
        _fail(
            AdapterConformanceCode.LEAF_MANIFEST_DIGEST_MISMATCH,
            "{} digest disagrees with the sample manifest".format(label),
        )


def _validate_core_before_domain_hook(
    adapter: NativeEventAdapter,
    complete: CompleteAdaptedEventSample,
    *,
    source_bytes: bytes,
    split_manifest: SplitManifest,
) -> Tuple[AdapterDescriptor, EventConfiguration, AdapterManifest]:
    try:
        satisfies_protocol = isinstance(adapter, NativeEventAdapter)
    except Exception:
        _fail(
            AdapterConformanceCode.CORE_ADAPTER_PROTOCOL,
            "adapter protocol inspection failed",
        )
    if not satisfies_protocol:
        _fail(
            AdapterConformanceCode.CORE_ADAPTER_PROTOCOL,
            "adapter does not satisfy NativeEventAdapter",
        )
    try:
        core = complete.sample
    except AttributeError:
        _fail(
            AdapterConformanceCode.CORE_INPUT_SHAPE_INVALID,
            "complete sample is missing its Phase-B core",
        )
    if type(core) is not AdaptedEventSample:
        _fail(
            AdapterConformanceCode.CORE_INPUT_SHAPE_INVALID,
            "complete sample core must be an exact AdaptedEventSample",
        )
    try:
        adapter_descriptor = adapter.descriptor()
    except Exception:
        _fail(
            AdapterConformanceCode.CORE_DESCRIPTOR_SCHEMA_MISMATCH,
            "adapter descriptor operation failed",
        )
    try:
        descriptor = _contract._snapshot_descriptor(adapter_descriptor)
    except (AttributeError, TypeError, ValueError, AdapterContractError):
        _fail(
            AdapterConformanceCode.CORE_DESCRIPTOR_SCHEMA_MISMATCH,
            "adapter descriptor has an invalid exact shape",
        )
    try:
        adapter_schema = adapter.schema()
    except Exception:
        _fail(
            AdapterConformanceCode.CORE_DESCRIPTOR_SCHEMA_MISMATCH,
            "adapter schema operation failed",
        )
    try:
        canonical_schema = snapshot_bounded_schema(adapter_schema)
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "adapter schema exceeds a generated-v1 resource ceiling",
        )
    except (AttributeError, TypeError, ValueError, AdapterContractError):
        _fail(
            AdapterConformanceCode.CORE_DESCRIPTOR_SCHEMA_MISMATCH,
            "adapter schema has an invalid exact shape",
        )
    try:
        manifest = _contract._validate_manifest_shape(core.manifest)
    except (AttributeError, TypeError, ValueError, AdapterContractError):
        _fail(
            AdapterConformanceCode.CORE_INPUT_SHAPE_INVALID,
            "sample manifest has an invalid exact shape",
        )
    capabilities = descriptor.capabilities
    if (
        capabilities.time_measure is not canonical_schema.time_measure
        or capabilities.multiplicity_mode is not canonical_schema.multiplicity_mode
    ):
        _fail(
            AdapterConformanceCode.CORE_DESCRIPTOR_SCHEMA_MISMATCH,
            "declared capabilities disagree with the native schema",
        )
    if manifest.descriptor_sha256 != descriptor.descriptor_sha256:
        _fail(
            AdapterConformanceCode.CORE_DESCRIPTOR_DIGEST_MISMATCH,
            "descriptor digest mismatch",
        )
    if not split_manifest.contains_exactly(manifest.partition):
        _fail(
            AdapterConformanceCode.CORE_PARTITION_MISMATCH,
            "sample partition is absent from the corpus split",
        )
    if manifest.split_manifest_sha256 != split_manifest.split_manifest_sha256:
        _fail(
            AdapterConformanceCode.CORE_SPLIT_MISMATCH,
            "split-manifest digest mismatch",
        )
    if (
        manifest.source_size_bytes != len(source_bytes)
        or manifest.source_sha256 != hashlib.sha256(source_bytes).hexdigest()
    ):
        _fail(
            AdapterConformanceCode.CORE_SOURCE_MISMATCH,
            "source bytes disagree with the sample manifest",
        )
    schema_digest = _contract.feature_schema_digest(canonical_schema)
    if (
        manifest.schema_sha256 != schema_digest
        or manifest.schema_version != canonical_schema.version
    ):
        _fail(
            AdapterConformanceCode.CORE_SCHEMA_MISMATCH,
            "schema commitment mismatch",
        )
    try:
        configuration = core.configuration
        if type(configuration) is not EventConfiguration:
            raise TypeError("configuration must be exact")
        bounded_configuration = snapshot_bounded_native_configuration(
            configuration
        )
        detached = _contract.rebuild_detached_native_configuration(
            bounded_configuration, schema=canonical_schema
        )
        sample_id = bounded_configuration.sample_id
        group_id = bounded_configuration.group_id
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "native occurrence count exceeds its resource ceiling",
        )
    except (AttributeError, TypeError, ValueError, AdapterContractError):
        _fail(
            AdapterConformanceCode.CORE_NATIVE_MISMATCH,
            "native configuration has an invalid exact shape",
        )
    if (
        sample_id != manifest.partition.sample_id
        or group_id != manifest.partition.group_id
    ):
        _fail(
            AdapterConformanceCode.CORE_PARTITION_MISMATCH,
            "configuration identifiers disagree with the sample partition",
        )
    if manifest.native_observation_sha256 != _contract.native_observation_digest(
        detached
    ):
        _fail(
            AdapterConformanceCode.CORE_NATIVE_MISMATCH,
            "native-observation digest mismatch",
        )
    expected_root = _contract._domain_digest(
        _contract.SAMPLE_MANIFEST_DIGEST_DOMAIN,
        _contract._sample_manifest_payload(manifest),
    )
    if manifest.sample_root_sha256 != expected_root:
        _fail(
            AdapterConformanceCode.CORE_MANIFEST_ROOT_MISMATCH,
            "sample-root digest mismatch",
        )
    return descriptor, detached, manifest


def _validate_leaf_source_bindings(
    complete: CompleteAdaptedEventSample,
    *,
    source_sha256: str,
    source_size_bytes: int,
    policy_sha256: str,
    schema_sha256: str,
    native_sha256: str,
) -> None:
    inventory = complete.inventory
    coverage = complete.coverage
    if (
        inventory.source_sha256 != source_sha256
        or inventory.source_size_bytes != source_size_bytes
        or inventory.policy_sha256 != policy_sha256
    ):
        _fail(
            AdapterConformanceCode.INVENTORY_BINDING_MISMATCH,
            "inventory source or policy binding mismatch",
        )
    if (
        coverage.source_sha256 != source_sha256
        or coverage.source_size_bytes != source_size_bytes
        or coverage.policy_sha256 != policy_sha256
        or coverage.source_inventory_sha256
        != source_inventory_digest(inventory)
    ):
        _fail(
            AdapterConformanceCode.COVERAGE_BINDING_MISMATCH,
            "coverage source, policy, or inventory binding mismatch",
        )
    static_context = complete.static_context
    if (
        static_context.source_sha256 != source_sha256
        or static_context.policy_sha256 != policy_sha256
    ):
        _fail(
            AdapterConformanceCode.STATIC_CONTEXT_BINDING_MISMATCH,
            "static-context source or policy binding mismatch",
        )
    labels = complete.evaluation_labels
    if (
        labels.source_sha256 != source_sha256
        or labels.policy_sha256 != policy_sha256
    ):
        _fail(
            AdapterConformanceCode.EVALUATION_LABELS_BINDING_MISMATCH,
            "evaluation-label source or policy binding mismatch",
        )
    provenance = complete.provenance
    if (
        provenance.source_sha256 != source_sha256
        or provenance.policy_sha256 != policy_sha256
        or provenance.native_observation_sha256 != native_sha256
    ):
        _fail(
            AdapterConformanceCode.PROVENANCE_BINDING_MISMATCH,
            "provenance source, policy, or native binding mismatch",
        )
    reconstruction = complete.reconstruction
    if (
        reconstruction.source_sha256 != source_sha256
        or reconstruction.policy_sha256 != policy_sha256
        or reconstruction.schema_sha256 != schema_sha256
    ):
        _fail(
            AdapterConformanceCode.RECONSTRUCTION_BINDING_MISMATCH,
            "semantic reconstruction source, schema, or policy mismatch",
        )


def _validate_coverage_and_provenance(
    complete: CompleteAdaptedEventSample,
    detached: EventConfiguration,
    *,
    allowed_exclusion_reason_codes: Tuple[str, ...],
    allowed_censor_reason_codes: Tuple[str, ...],
) -> None:
    inventory_keys = tuple(item.item_key for item in complete.inventory.items)
    coverage_keys = tuple(entry.item_key for entry in complete.coverage.entries)
    if inventory_keys != coverage_keys:
        _fail(
            AdapterConformanceCode.COVERAGE_ITEM_SET_MISMATCH,
            "coverage item keys do not equal the independent inventory",
        )
    allowed_exclusions = set(allowed_exclusion_reason_codes)
    for entry in complete.coverage.entries:
        if (
            entry.disposition is CoverageDisposition.EXCLUDED_WITH_REASON
            and entry.exclusion_reason_code not in allowed_exclusions
        ):
            _fail(
                AdapterConformanceCode.COVERAGE_EXCLUSION_REASON_INVALID,
                "coverage uses an unfrozen exclusion reason",
            )

    provenance_by_key = {
        entry.provenance_key: entry for entry in complete.provenance.entries
    }
    event_targets = {
        entry.target_key
        for entry in complete.coverage.entries
        if entry.disposition is CoverageDisposition.EVENT_OCCURRENCE
    }
    static_targets = {
        entry.target_key
        for entry in complete.coverage.entries
        if entry.disposition is CoverageDisposition.STATIC_CONTEXT
    }
    label_targets = {
        entry.target_key
        for entry in complete.coverage.entries
        if entry.disposition is CoverageDisposition.EVALUATION_ONLY_LABEL
    }
    if event_targets != set(provenance_by_key):
        _fail(
            AdapterConformanceCode.COVERAGE_TARGET_MISMATCH,
            "event coverage targets do not equal provenance keys",
        )
    if static_targets != {
        entry.entry_key for entry in complete.static_context.entries
    }:
        _fail(
            AdapterConformanceCode.COVERAGE_TARGET_MISMATCH,
            "static coverage targets do not equal static-context keys",
        )
    if label_targets != {
        entry.entry_key for entry in complete.evaluation_labels.entries
    }:
        _fail(
            AdapterConformanceCode.COVERAGE_TARGET_MISMATCH,
            "label coverage targets do not equal evaluation-label keys",
        )

    expected_occurrences = native_occurrence_digests(detached)
    actual_occurrences = tuple(
        entry.native_occurrence_sha256 for entry in complete.provenance.entries
    )
    if Counter(expected_occurrences) != Counter(actual_occurrences):
        _fail(
            AdapterConformanceCode.PROVENANCE_OCCURRENCE_MULTISET_MISMATCH,
            "provenance does not cover the native occurrence multiset exactly",
        )
    event_items_by_target = {}
    for entry in complete.coverage.entries:
        if entry.disposition is CoverageDisposition.EVENT_OCCURRENCE:
            event_items_by_target.setdefault(entry.target_key, []).append(
                entry.item_key
            )
    for key, provenance in provenance_by_key.items():
        expected_source_keys = tuple(sorted(event_items_by_target.get(key, ())))
        if provenance.source_item_keys != expected_source_keys:
            _fail(
                AdapterConformanceCode.PROVENANCE_SOURCE_ITEM_MISMATCH,
                "provenance source-item links disagree with coverage",
            )

    occurrence_by_digest = {}
    assert detached.observed is not None
    for digest, event in zip(expected_occurrences, detached.events):
        occurrence_by_digest[digest] = event
    allowed_censors = set(allowed_censor_reason_codes)
    for provenance in complete.provenance.entries:
        event = occurrence_by_digest[provenance.native_occurrence_sha256]
        applicable = tuple(
            sorted(detached.schema.event_type(event.event_type).field_names)
        )
        statuses = {
            status.field_name: status for status in provenance.field_statuses
        }
        if tuple(sorted(statuses)) != applicable:
            _fail(
                AdapterConformanceCode.PROVENANCE_FIELD_STATUS_MISMATCH,
                "field-status keys do not equal schema-applicable fields",
            )
        for field_name in applicable:
            status = statuses[field_name]
            present = field_name in event.marks
            if present != (status.status is SourceValueStatus.PRESENT):
                _fail(
                    AdapterConformanceCode.PROVENANCE_FIELD_STATUS_MISMATCH,
                    "source field status disagrees with native mark presence",
                )
            if (
                status.status is SourceValueStatus.CENSORED
                and status.reason_code not in allowed_censors
            ):
                _fail(
                    AdapterConformanceCode.PROVENANCE_CENSOR_REASON_INVALID,
                    "provenance uses an unfrozen censor reason",
                )


def _validate_capabilities_and_fitted_state(
    capabilities: AdapterCapabilities,
    complete: CompleteAdaptedEventSample,
    descriptor: AdapterDescriptor,
    manifest: AdapterManifest,
    split_manifest: SplitManifest,
) -> None:
    static_nonempty = bool(complete.static_context.entries)
    if capabilities.static_context != static_nonempty:
        _fail(
            AdapterConformanceCode.STATIC_CONTEXT_CAPABILITY_MISMATCH,
            "static-context capability disagrees with its leaf",
        )
    labels_nonempty = bool(complete.evaluation_labels.entries)
    if capabilities.evaluation_labels != labels_nonempty:
        _fail(
            AdapterConformanceCode.EVALUATION_LABELS_CAPABILITY_MISMATCH,
            "evaluation-label capability disagrees with its leaf",
        )
    provenance_nonempty = bool(complete.provenance.entries)
    if capabilities.private_provenance != provenance_nonempty:
        _fail(
            AdapterConformanceCode.PROVENANCE_CAPABILITY_MISMATCH,
            "private-provenance capability disagrees with its leaf",
        )
    if complete.sample.configuration.events and not provenance_nonempty:
        _fail(
            AdapterConformanceCode.PROVENANCE_CAPABILITY_MISMATCH,
            "every admitted occurrence requires private provenance",
        )

    state = complete.fitted_state
    if capabilities.fitted_state and state is None:
        _fail(
            AdapterConformanceCode.FITTED_STATE_REQUIRED,
            "fitted-state capability cannot use the no-fit sentinel",
        )
    if not capabilities.fitted_state and state is not None:
        _fail(
            AdapterConformanceCode.FITTED_STATE_FORBIDDEN,
            "a no-fit adapter cannot emit fitted state",
        )
    if state is None:
        if manifest.fitted_state_sha256 != _contract.NO_FITTED_STATE_SHA256:
            _fail(
                AdapterConformanceCode.FITTED_STATE_FORBIDDEN,
                "no-fit adapter manifest does not use the exact sentinel",
            )
        return
    identity = descriptor.identity
    schema_sha256 = manifest.schema_sha256
    expected_training_groups = training_group_set_digest(split_manifest)
    if (
        state.descriptor_sha256 != descriptor.descriptor_sha256
        or state.adapter_id != identity.adapter_id
        or state.adapter_version != identity.adapter_version
        or state.contract_version != identity.contract_version
        or state.policy_sha256 != identity.policy_sha256
        or state.schema_sha256 != schema_sha256
        or state.split_manifest_sha256 != manifest.split_manifest_sha256
        or state.training_group_set_sha256 != expected_training_groups
    ):
        _fail(
            AdapterConformanceCode.FITTED_STATE_BINDING_MISMATCH,
            "fitted state is not bound to this adapter/schema/train split",
        )


def validate_complete_adapted_event_sample(
    adapter: NativeEventAdapter,
    complete: CompleteAdaptedEventSample,
    *,
    source_bytes: bytes,
    split_manifest: SplitManifest,
    expected_evidence: ExpectedAdapterEvidence,
    allowed_exclusion_reason_codes: Tuple[str, ...] = (),
    allowed_censor_reason_codes: Tuple[str, ...] = (),
) -> EventConfiguration:
    """Decision-capable validation against one independent full oracle.

    ``expected_evidence`` must be built by a source-bound implementation that
    is independent of the adapter under test.  It binds expected detached
    native state and every Phase-C leaf.  The function returns only a newly
    detached exact base ``EventConfiguration``.
    """

    if type(complete) is not CompleteAdaptedEventSample:
        raise TypeError("complete must be an exact CompleteAdaptedEventSample")
    if type(source_bytes) is not bytes:
        raise TypeError("source_bytes must be exact immutable bytes")
    if type(split_manifest) is not SplitManifest:
        raise TypeError("split_manifest must be an exact SplitManifest")
    if type(expected_evidence) is not ExpectedAdapterEvidence:
        _fail(
            AdapterConformanceCode.ORACLE_SHAPE_INVALID,
            "independent oracle must be an exact ExpectedAdapterEvidence",
        )
    if len(source_bytes) > MAXIMUM_SOURCE_BYTES:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "source bytes exceed the generated-v1 resource ceiling",
        )
    try:
        _preflight_evidence_leaves(complete)
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "complete evidence exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            AdapterConformanceCode.LEAF_SHAPE_INVALID,
            "complete evidence has an invalid or mutated exact shape",
        )
    if type(complete.sample) is not AdaptedEventSample:
        _fail(
            AdapterConformanceCode.CORE_INPUT_SHAPE_INVALID,
            "complete sample core must be an exact AdaptedEventSample",
        )
    try:
        _preflight_native_configuration(complete.sample.configuration)
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "native configuration exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            AdapterConformanceCode.CORE_NATIVE_MISMATCH,
            "native configuration has an invalid or mutated exact shape",
        )
    try:
        _preflight_split_manifest(split_manifest)
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "split manifest exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            AdapterConformanceCode.CORE_INPUT_SHAPE_INVALID,
            "split-manifest input has an invalid exact shape",
        )
    try:
        _preflight_evidence_leaves(expected_evidence)
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "independent oracle exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            AdapterConformanceCode.ORACLE_SHAPE_INVALID,
            "independent oracle has an invalid or mutated exact shape",
        )
    try:
        _preflight_exact_tuple(
            allowed_exclusion_reason_codes,
            maximum=MAXIMUM_REASON_CODES,
            name="allowed exclusion reasons",
        )
        _preflight_exact_tuple(
            allowed_censor_reason_codes,
            maximum=MAXIMUM_REASON_CODES,
            name="allowed censor reasons",
        )
        if len(allowed_exclusion_reason_codes) + len(
            allowed_censor_reason_codes
        ) > MAXIMUM_REASON_CODES:
            raise AdapterEvidenceResourceError(
                "combined reason registry exceeds its resource ceiling"
            )
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "frozen reason registry exceeds its resource ceiling",
        )
    except Exception:
        _fail(
            AdapterConformanceCode.REASON_REGISTRY_INVALID,
            "frozen reason registry has an invalid exact shape",
        )
    try:
        complete_snapshot = _snapshot_complete(complete)
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "complete evidence exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            AdapterConformanceCode.LEAF_SHAPE_INVALID,
            "complete evidence has an invalid or mutated exact shape",
        )
    try:
        split_snapshot = snapshot_bounded_split_manifest(split_manifest)
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "split manifest exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            AdapterConformanceCode.CORE_INPUT_SHAPE_INVALID,
            "split-manifest input has an invalid exact shape",
        )
    try:
        expected_snapshot = _snapshot_expected_evidence(expected_evidence)
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "independent oracle exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            AdapterConformanceCode.ORACLE_SHAPE_INVALID,
            "independent oracle has an invalid or mutated exact shape",
        )
    try:
        exclusions = _validate_reason_codes(
            allowed_exclusion_reason_codes, name="allowed exclusion reason"
        )
        censors = _validate_reason_codes(
            allowed_censor_reason_codes, name="allowed censor reason"
        )
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "frozen reason registry exceeds its resource ceiling",
        )
    except Exception:
        _fail(
            AdapterConformanceCode.REASON_REGISTRY_INVALID,
            "frozen reason registry has an invalid exact shape",
        )

    descriptor, detached, manifest = _validate_core_before_domain_hook(
        adapter,
        complete_snapshot,
        source_bytes=source_bytes,
        split_manifest=split_snapshot,
    )
    if manifest.native_observation_sha256 != (
        expected_snapshot.native_observation_sha256
    ):
        _fail(
            AdapterConformanceCode.NATIVE_EXPECTATION_MISMATCH,
            "detached native state differs from the independent oracle",
        )
    try:
        source_sha256 = hashlib.sha256(source_bytes).hexdigest()
        _validate_leaf_source_bindings(
            complete_snapshot,
            source_sha256=source_sha256,
            source_size_bytes=len(source_bytes),
            policy_sha256=descriptor.identity.policy_sha256,
            schema_sha256=manifest.schema_sha256,
            native_sha256=manifest.native_observation_sha256,
        )
        _validate_leaf_binding(
            manifest.static_context_sha256,
            static_context_digest(complete_snapshot.static_context),
            label="static context",
        )
        _validate_leaf_binding(
            manifest.evaluation_labels_sha256,
            evaluation_labels_digest(complete_snapshot.evaluation_labels),
            label="evaluation labels",
        )
        _validate_leaf_binding(
            manifest.coverage_ledger_sha256,
            source_coverage_ledger_digest(complete_snapshot.coverage),
            label="coverage ledger",
        )
        _validate_leaf_binding(
            manifest.private_provenance_sha256,
            private_provenance_digest(complete_snapshot.provenance),
            label="private provenance",
        )
        _validate_leaf_binding(
            manifest.semantic_reconstruction_sha256,
            semantic_reconstruction_digest(complete_snapshot.reconstruction),
            label="semantic reconstruction",
        )
        expected_fitted_digest = (
            _contract.NO_FITTED_STATE_SHA256
            if complete_snapshot.fitted_state is None
            else fitted_adapter_state_digest(complete_snapshot.fitted_state)
        )
        _validate_leaf_binding(
            manifest.fitted_state_sha256,
            expected_fitted_digest,
            label="fitted state",
        )
        _validate_capabilities_and_fitted_state(
            descriptor.capabilities,
            complete_snapshot,
            descriptor,
            manifest,
            split_snapshot,
        )
        _validate_coverage_and_provenance(
            complete_snapshot,
            detached,
            allowed_exclusion_reason_codes=exclusions,
            allowed_censor_reason_codes=censors,
        )

        try:
            _validate_leaf_source_bindings(
                expected_snapshot,  # type: ignore[arg-type]
                source_sha256=source_sha256,
                source_size_bytes=len(source_bytes),
                policy_sha256=descriptor.identity.policy_sha256,
                schema_sha256=manifest.schema_sha256,
                native_sha256=manifest.native_observation_sha256,
            )
            _validate_coverage_and_provenance(
                expected_snapshot,  # type: ignore[arg-type]
                detached,
                allowed_exclusion_reason_codes=exclusions,
                allowed_censor_reason_codes=censors,
            )
        except AdapterConformanceError:
            _fail(
                AdapterConformanceCode.ORACLE_BINDING_INVALID,
                "independent oracle has inconsistent cross-leaf bindings",
            )

        if complete_snapshot.inventory != expected_snapshot.inventory:
            _fail(
                AdapterConformanceCode.INVENTORY_EXPECTATION_MISMATCH,
                "adapter inventory differs from the independent inventory oracle",
            )
        if complete_snapshot.coverage != expected_snapshot.coverage:
            _fail(
                AdapterConformanceCode.COVERAGE_EXPECTATION_MISMATCH,
                "adapter coverage differs from the independent oracle",
            )
        if complete_snapshot.static_context != expected_snapshot.static_context:
            _fail(
                AdapterConformanceCode.STATIC_CONTEXT_EXPECTATION_MISMATCH,
                "adapter static context differs from the independent oracle",
            )
        if (
            complete_snapshot.evaluation_labels
            != expected_snapshot.evaluation_labels
        ):
            _fail(
                AdapterConformanceCode.EVALUATION_LABELS_EXPECTATION_MISMATCH,
                "adapter evaluation labels differ from the independent oracle",
            )
        if complete_snapshot.provenance != expected_snapshot.provenance:
            _fail(
                AdapterConformanceCode.PROVENANCE_EXPECTATION_MISMATCH,
                "adapter provenance differs from the independent oracle",
            )
        if complete_snapshot.fitted_state != expected_snapshot.fitted_state:
            _fail(
                AdapterConformanceCode.FITTED_STATE_EXPECTATION_MISMATCH,
                "adapter fitted state differs from the independent oracle",
            )
        if complete_snapshot.reconstruction != expected_snapshot.reconstruction:
            _fail(
                AdapterConformanceCode.RECONSTRUCTION_EXPECTATION_MISMATCH,
                "semantic reconstruction differs from the independent oracle",
            )

        if descriptor.capabilities.raw_byte_reconstruction:
            if complete_snapshot.raw_reconstruction_bytes is None:
                _fail(
                    AdapterConformanceCode.RAW_RECONSTRUCTION_CAPABILITY_MISMATCH,
                    "raw-byte capability requires an exact reconstruction",
                )
            if complete_snapshot.raw_reconstruction_bytes != source_bytes:
                _fail(
                    AdapterConformanceCode.RAW_RECONSTRUCTION_MISMATCH,
                    "raw-byte reconstruction differs from the exact source bytes",
                )
        elif complete_snapshot.raw_reconstruction_bytes is not None:
            _fail(
                AdapterConformanceCode.RAW_RECONSTRUCTION_CAPABILITY_MISMATCH,
                "raw reconstruction contradicts the adapter capability",
            )
    except AdapterConformanceError:
        raise
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "evidence validation exceeded a generated-v1 resource ceiling",
        )
    except (AttributeError, KeyError, IndexError, TypeError, ValueError):
        _fail(
            AdapterConformanceCode.LEAF_SHAPE_INVALID,
            "evidence leaf has an invalid or mutated exact shape",
        )

    # This adapter-owned hook is deliberately last.  The detached result was
    # already rebuilt into independent exact base objects before the hook runs.
    try:
        domain_result = adapter.validate_domain_sample(complete_snapshot.sample)
    except Exception:
        _fail(
            AdapterConformanceCode.DOMAIN_VALIDATION_FAILED,
            "adapter domain validation failed",
        )
    if domain_result is not None:
        _fail(
            AdapterConformanceCode.DOMAIN_VALIDATION_RETURNED_VALUE,
            "validate_domain_sample must return None",
        )
    return detached


def validate_complete_adapted_event_sample_development_only(
    adapter: NativeEventAdapter,
    complete: CompleteAdaptedEventSample,
    *,
    source_bytes: bytes,
    split_manifest: SplitManifest,
    expected_inventory: SourceInventory,
    expected_semantic_reconstruction: SemanticReconstruction,
    allowed_exclusion_reason_codes: Tuple[str, ...] = (),
    allowed_censor_reason_codes: Tuple[str, ...] = (),
) -> EventConfiguration:
    """Compatibility diagnostic; never sufficient for a gate decision.

    Coverage, keyed leaves, provenance, fitted state, and native state are
    copied from the adapter object itself.  Use
    :func:`validate_complete_adapted_event_sample` with an independently built
    :class:`ExpectedAdapterEvidence` for all decision-bearing validation.
    """

    if type(complete) is not CompleteAdaptedEventSample:
        raise TypeError("complete must be an exact CompleteAdaptedEventSample")
    try:
        if type(expected_inventory) is not SourceInventory:
            raise TypeError("expected_inventory must be exact")
        if type(expected_semantic_reconstruction) is not SemanticReconstruction:
            raise TypeError("expected reconstruction must be exact")
        complete_snapshot = _snapshot_complete(complete)
        inventory_snapshot = _snapshot_inventory(expected_inventory)
        reconstruction_snapshot = _snapshot_reconstruction(
            expected_semantic_reconstruction
        )
        expected = ExpectedAdapterEvidence(
            native_observation_sha256=(
                complete_snapshot.sample.manifest.native_observation_sha256
            ),
            inventory=inventory_snapshot,
            coverage=complete_snapshot.coverage,
            static_context=complete_snapshot.static_context,
            evaluation_labels=complete_snapshot.evaluation_labels,
            provenance=complete_snapshot.provenance,
            fitted_state=complete_snapshot.fitted_state,
            reconstruction=reconstruction_snapshot,
        )
    except AdapterEvidenceResourceError:
        _fail(
            AdapterConformanceCode.RESOURCE_LIMIT_EXCEEDED,
            "development oracle exceeds a generated-v1 resource ceiling",
        )
    except Exception:
        _fail(
            AdapterConformanceCode.ORACLE_SHAPE_INVALID,
            "development oracle has an invalid exact shape",
        )
    return validate_complete_adapted_event_sample(
        adapter,
        complete_snapshot,
        source_bytes=source_bytes,
        split_manifest=split_manifest,
        expected_evidence=expected,
        allowed_exclusion_reason_codes=allowed_exclusion_reason_codes,
        allowed_censor_reason_codes=allowed_censor_reason_codes,
    )


__all__ = [
    "AdapterConformanceCode",
    "AdapterConformanceError",
    "AdapterEvidenceResourceError",
    "CompleteAdaptedEventSample",
    "CoverageDisposition",
    "CoverageEntry",
    "EvaluationLabelEntry",
    "EvaluationLabels",
    "EXPECTED_EVIDENCE_DIGEST_DOMAIN",
    "ExpectedAdapterEvidence",
    "FittedAdapterState",
    "MAXIMUM_DECLARED_EVENT_TYPES",
    "MAXIMUM_EVENT_ID_COMPONENT_BYTES",
    "MAXIMUM_EVENT_ID_INTEGER_ABSOLUTE_VALUE",
    "MAXIMUM_EVENT_ID_METADATA_BYTES",
    "MAXIMUM_EVENT_ID_TUPLE_ARITY",
    "MAXIMUM_FIELD_STATUSES_PER_OCCURRENCE",
    "MAXIMUM_FIELDS_PER_EVENT_TYPE",
    "MAXIMUM_INVENTORY_ITEMS",
    "MAXIMUM_KEYED_LEAF_ENTRIES",
    "MAXIMUM_PRIVATE_PAYLOAD_BYTES",
    "MAXIMUM_REASON_CODES",
    "MAXIMUM_SCALAR_COORDINATES_PER_EVENT_TYPE",
    "MAXIMUM_SCALAR_COORDINATES_PER_OCCURRENCE",
    "MAXIMUM_SECONDARY_TAGS_PER_ITEM",
    "MAXIMUM_SEMANTIC_OCCURRENCES",
    "MAXIMUM_SINGLE_PAYLOAD_BYTES",
    "MAXIMUM_SOURCE_BYTES",
    "MAXIMUM_SOURCE_LINKS_PER_OCCURRENCE",
    "MAXIMUM_SPLIT_ENTRIES",
    "MAXIMUM_SPLIT_GROUPS",
    "MAXIMUM_TIME_ATOMS",
    "MAXIMUM_TOTAL_PROVENANCE_SOURCE_LINKS",
    "MAXIMUM_TOTAL_SECONDARY_TAGS",
    "NATIVE_OCCURRENCE_DIGEST_DOMAIN",
    "NativeEventAdapter",
    "OccurrenceProvenance",
    "PrivateProvenance",
    "SOURCE_INVENTORY_DIGEST_DOMAIN",
    "SOURCE_ITEM_DIGEST_DOMAIN",
    "SemanticReconstruction",
    "SourceCoverageLedger",
    "SourceFieldStatus",
    "SourceInventory",
    "SourceInventoryItem",
    "SourceValueStatus",
    "StaticContext",
    "StaticContextEntry",
    "TRAINING_GROUP_SET_DIGEST_DOMAIN",
    "evaluation_labels_digest",
    "expected_adapter_evidence_digest",
    "fitted_adapter_state_digest",
    "native_occurrence_digest",
    "native_occurrence_digests",
    "private_provenance_digest",
    "semantic_reconstruction_digest",
    "snapshot_bounded_native_configuration",
    "snapshot_bounded_schema",
    "snapshot_bounded_split_manifest",
    "source_coverage_ledger_digest",
    "source_inventory_digest",
    "source_inventory_item_digest",
    "static_context_digest",
    "training_group_set_digest",
    "validate_complete_adapted_event_sample",
    "validate_complete_adapted_event_sample_development_only",
]
