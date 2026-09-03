"""Domain-neutral native-event adapter contract.

This module is the minimal, model-independent seam between a source adapter
and HeteroDiff's native :class:`~heterodiff.events.EventConfiguration`.  It
contains no parser, training, tensor-capacity, padding, task, or model policy.

The contract deliberately treats an adapter's objects as untrusted.  The
shared validator snapshots exact base event/schema/observation types, removes
all occurrence and sample identifiers, and independently rebuilds every
Phase-B-recomputable core commitment before returning a native configuration.
Static-context, label, coverage, fit, provenance, and semantic-reconstruction
leaf semantics remain opaque digest commitments until Phase C.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from types import MappingProxyType
import unicodedata
from typing import Optional, Protocol, Tuple, runtime_checkable

from heterodiff.events import (
    ContinuousField,
    Event,
    EventConfiguration,
    EventObservation,
    EventTypeSchema,
    FeatureSchema,
    MultiplicityMode,
    ObservationPattern,
    SupportKind,
    TimeMeasureKind,
    TimeReference,
)


ADAPTER_CONTRACT_VERSION = "heterodiff-native-event-adapter-v1"
UNICODE_PROFILE = "ucd-3.2.0"
ATOMIC_COUNTING_GRID_REPRESENTATION_ID = "heterodiff.atomic-counting-grid.v1"

DESCRIPTOR_DIGEST_DOMAIN = "heterodiff.adapter.descriptor.v1"
SCHEMA_DIGEST_DOMAIN = "heterodiff.adapter.schema.v1"
NATIVE_OBSERVATION_DIGEST_DOMAIN = (
    "heterodiff.adapter.native-observation.v1"
)
SPLIT_MANIFEST_DIGEST_DOMAIN = "heterodiff.adapter.split-manifest.v1"
STATIC_CONTEXT_DIGEST_DOMAIN = "heterodiff.adapter.static-context.v1"
EVALUATION_LABELS_DIGEST_DOMAIN = "heterodiff.adapter.evaluation-labels.v1"
COVERAGE_LEDGER_DIGEST_DOMAIN = "heterodiff.adapter.coverage-ledger.v1"
FITTED_STATE_DIGEST_DOMAIN = "heterodiff.adapter.fitted-state.v1"
PRIVATE_PROVENANCE_DIGEST_DOMAIN = "heterodiff.adapter.private-provenance.v1"
SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN = (
    "heterodiff.adapter.semantic-reconstruction.v1"
)
SAMPLE_MANIFEST_DIGEST_DOMAIN = "heterodiff.adapter.sample-manifest.v1"

_PUBLIC_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_VERSION_RE = re.compile(r"^[1-9][0-9]{0,9}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SPLITS = frozenset(("train", "validation", "test"))
_MAX_PUBLIC_ID_BYTES = 128
_MAX_PRIVATE_ID_CODEPOINTS = 256
_MAX_SAFE_JSON_INTEGER = 2**53 - 1
_UCD = unicodedata.ucd_3_2_0


class AdapterContractError(ValueError):
    """A content or capability commitment violates the adapter contract."""


def _canonical_json_bytes(value: object) -> bytes:
    """Encode an internal payload using the contract's exact JSON profile."""

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


def _domain_digest(domain: str, payload: object) -> str:
    if type(domain) is not str:
        raise TypeError("digest domain must be an exact string")
    try:
        domain_bytes = domain.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("digest domain must contain only ASCII") from exc
    payload_bytes = _canonical_json_bytes(payload)
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload_bytes).to_bytes(8, "big"))
    digest.update(payload_bytes)
    return digest.hexdigest()


def _validated_sha256(value: object, *, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(
            "{} must be a lowercase 64-character SHA-256 digest".format(name)
        )
    return value


def _validated_public_id(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("{} must be an exact string".format(name))
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("{} must contain only ASCII".format(name)) from exc
    if len(encoded) > _MAX_PUBLIC_ID_BYTES or _PUBLIC_ID_RE.fullmatch(value) is None:
        raise ValueError("{} is not a canonical public identifier".format(name))
    return value


def _validated_private_text(value: object, *, name: str) -> str:
    if type(value) is not str:
        raise TypeError("{} must be an exact string".format(name))
    if not value or len(value) > _MAX_PRIVATE_ID_CODEPOINTS:
        raise ValueError("{} must contain 1--256 code points".format(name))
    if _UCD.normalize("NFC", value) != value:
        raise ValueError("{} must be Unicode NFC".format(name))
    forbidden = {"Cc", "Cs", "Co", "Cn", "Zl", "Zp"}
    categories = tuple(_UCD.category(character) for character in value)
    if any(category in forbidden for category in categories):
        raise ValueError("{} contains a forbidden Unicode code point".format(name))
    if categories[0] == "Zs" or categories[-1] == "Zs":
        raise ValueError("{} must equal its whitespace-trimmed form".format(name))
    return value


def _validated_nonnegative_size(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise TypeError("{} must be an exact integer".format(name))
    result = value
    if result < 0 or result > _MAX_SAFE_JSON_INTEGER:
        raise ValueError("{} is outside the canonical size range".format(name))
    return result


def _float_hex(value: object, *, name: str) -> str:
    if type(value) is not float:
        raise TypeError("{} must be a canonical binary64 float".format(name))
    if not math.isfinite(value):
        raise ValueError("{} must be finite".format(name))
    return (0.0 if value == 0.0 else value).hex().lower()


def _sentinel(domain: str, kind: str) -> str:
    return _domain_digest(domain, {"kind": kind})


EMPTY_STATIC_CONTEXT_SHA256 = _sentinel(STATIC_CONTEXT_DIGEST_DOMAIN, "empty")
EMPTY_EVALUATION_LABELS_SHA256 = _sentinel(
    EVALUATION_LABELS_DIGEST_DOMAIN, "empty"
)
EMPTY_COVERAGE_LEDGER_SHA256 = _sentinel(COVERAGE_LEDGER_DIGEST_DOMAIN, "empty")
NO_FITTED_STATE_SHA256 = _sentinel(FITTED_STATE_DIGEST_DOMAIN, "no_fit")
EMPTY_PRIVATE_PROVENANCE_SHA256 = _sentinel(
    PRIVATE_PROVENANCE_DIGEST_DOMAIN, "empty"
)
EMPTY_SEMANTIC_RECONSTRUCTION_SHA256 = _sentinel(
    SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN, "empty"
)


@dataclass(frozen=True)
class AdapterIdentity:
    """Content-bound public identity of one semantic adapter policy."""

    adapter_id: str
    adapter_version: str
    policy_sha256: str
    contract_version: str = ADAPTER_CONTRACT_VERSION

    def __post_init__(self) -> None:
        _validated_public_id(self.adapter_id, name="adapter_id")
        if type(self.adapter_version) is not str or _VERSION_RE.fullmatch(
            self.adapter_version
        ) is None:
            raise ValueError("adapter_version must be a canonical positive decimal")
        if type(self.contract_version) is not str:
            raise TypeError("contract_version must be an exact string")
        if self.contract_version != ADAPTER_CONTRACT_VERSION:
            raise ValueError("unsupported adapter contract version")
        _validated_sha256(self.policy_sha256, name="policy_sha256")


@dataclass(frozen=True)
class AdapterCapabilities:
    """Identity-free declarations that control shared conformance checks."""

    time_measure: TimeMeasureKind
    multiplicity_mode: MultiplicityMode
    semantic_reconstruction: bool = True
    raw_byte_reconstruction: bool = False
    fitted_state: bool = False
    supported_representation_ids: Tuple[str, ...] = ()
    static_context: bool = False
    evaluation_labels: bool = False
    private_provenance: bool = False

    def __post_init__(self) -> None:
        if type(self.time_measure) is not TimeMeasureKind:
            raise TypeError("time_measure must be an exact TimeMeasureKind")
        if type(self.multiplicity_mode) is not MultiplicityMode:
            raise TypeError("multiplicity_mode must be an exact MultiplicityMode")
        for name in (
            "semantic_reconstruction",
            "raw_byte_reconstruction",
            "fitted_state",
            "static_context",
            "evaluation_labels",
            "private_provenance",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError("{} must be an exact boolean".format(name))
        if not self.semantic_reconstruction:
            raise ValueError("semantic reconstruction support is mandatory")
        if type(self.supported_representation_ids) is not tuple:
            raise TypeError("supported_representation_ids must be an exact tuple")
        identifiers = tuple(
            _validated_public_id(value, name="representation_id")
            for value in self.supported_representation_ids
        )
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("representation identifiers must be unique")
        if identifiers != tuple(sorted(identifiers)):
            raise ValueError("representation identifiers must use canonical order")
        if (
            ATOMIC_COUNTING_GRID_REPRESENTATION_ID in identifiers
            and self.time_measure is not TimeMeasureKind.ATOMIC
        ):
            raise ValueError(
                "atomic-counting-grid representation requires atomic time"
            )


@dataclass(frozen=True)
class AdapterDescriptor:
    """Exact adapter identity and its identity-independent capabilities."""

    identity: AdapterIdentity
    capabilities: AdapterCapabilities

    def __post_init__(self) -> None:
        if type(self.identity) is not AdapterIdentity:
            raise TypeError("identity must be an exact AdapterIdentity")
        if type(self.capabilities) is not AdapterCapabilities:
            raise TypeError("capabilities must be exact AdapterCapabilities")
        object.__setattr__(
            self,
            "identity",
            AdapterIdentity(
                adapter_id=self.identity.adapter_id,
                adapter_version=self.identity.adapter_version,
                policy_sha256=self.identity.policy_sha256,
                contract_version=self.identity.contract_version,
            ),
        )
        object.__setattr__(
            self,
            "capabilities",
            AdapterCapabilities(
                time_measure=self.capabilities.time_measure,
                multiplicity_mode=self.capabilities.multiplicity_mode,
                semantic_reconstruction=self.capabilities.semantic_reconstruction,
                raw_byte_reconstruction=self.capabilities.raw_byte_reconstruction,
                fitted_state=self.capabilities.fitted_state,
                supported_representation_ids=(
                    self.capabilities.supported_representation_ids
                ),
                static_context=self.capabilities.static_context,
                evaluation_labels=self.capabilities.evaluation_labels,
                private_provenance=self.capabilities.private_provenance,
            ),
        )

    @property
    def descriptor_sha256(self) -> str:
        return adapter_descriptor_digest(self)


@dataclass(frozen=True)
class SamplePartition:
    """Private sample/group identity and one closed-vocabulary split."""

    sample_id: str
    group_id: str
    split: str

    def __post_init__(self) -> None:
        _validated_private_text(self.sample_id, name="sample_id")
        _validated_private_text(self.group_id, name="group_id")
        if type(self.split) is not str or self.split not in _SPLITS:
            raise ValueError("split must be exactly train, validation, or test")


@dataclass(frozen=True)
class SplitManifest:
    """Content commitment for a complete, group-disjoint corpus split."""

    entries: Tuple[SamplePartition, ...]

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple:
            raise TypeError("split entries must be an exact tuple")
        if not self.entries:
            raise ValueError("a split manifest requires at least one sample")
        if any(type(entry) is not SamplePartition for entry in self.entries):
            raise TypeError("split entries must be exact SamplePartition instances")
        entries = tuple(
            SamplePartition(entry.sample_id, entry.group_id, entry.split)
            for entry in self.entries
        )
        sample_ids = tuple(entry.sample_id for entry in entries)
        if len(set(sample_ids)) != len(sample_ids):
            raise ValueError("sample_id values must be unique across the corpus")
        group_splits = {}
        for entry in entries:
            prior = group_splits.setdefault(entry.group_id, entry.split)
            if prior != entry.split:
                raise ValueError("one group cannot occur in multiple splits")
        ordered = tuple(
            sorted(
                entries,
                key=lambda entry: (entry.group_id, entry.sample_id, entry.split),
            )
        )
        object.__setattr__(self, "entries", ordered)

    @property
    def split_manifest_sha256(self) -> str:
        return split_manifest_digest(self)

    def partition_for(self, sample_id: str) -> SamplePartition:
        _validated_private_text(sample_id, name="sample_id")
        for entry in self.entries:
            if entry.sample_id == sample_id:
                return entry
        raise KeyError("sample_id is absent from the split manifest")

    def contains_exactly(self, partition: SamplePartition) -> bool:
        if type(partition) is not SamplePartition:
            raise TypeError("partition must be an exact SamplePartition")
        return any(entry == partition for entry in self.entries)


def _identity_payload(identity: AdapterIdentity) -> object:
    return {
        "adapter_id": identity.adapter_id,
        "adapter_version": identity.adapter_version,
        "contract_version": identity.contract_version,
        "policy_sha256": identity.policy_sha256,
    }


def _capabilities_payload(capabilities: AdapterCapabilities) -> object:
    return {
        "evaluation_labels": capabilities.evaluation_labels,
        "fitted_state": capabilities.fitted_state,
        "multiplicity_mode": capabilities.multiplicity_mode.value,
        "private_provenance": capabilities.private_provenance,
        "raw_byte_reconstruction": capabilities.raw_byte_reconstruction,
        "semantic_reconstruction": capabilities.semantic_reconstruction,
        "static_context": capabilities.static_context,
        "supported_representation_ids": list(
            capabilities.supported_representation_ids
        ),
        "time_measure": capabilities.time_measure.value,
    }


def adapter_descriptor_digest(descriptor: AdapterDescriptor) -> str:
    """Return the descriptor's domain-separated canonical digest."""

    if type(descriptor) is not AdapterDescriptor:
        raise TypeError("descriptor must be an exact AdapterDescriptor")
    if type(descriptor.identity) is not AdapterIdentity:
        raise TypeError("identity must be an exact AdapterIdentity")
    if type(descriptor.capabilities) is not AdapterCapabilities:
        raise TypeError("capabilities must be exact AdapterCapabilities")
    identity = AdapterIdentity(
        adapter_id=descriptor.identity.adapter_id,
        adapter_version=descriptor.identity.adapter_version,
        policy_sha256=descriptor.identity.policy_sha256,
        contract_version=descriptor.identity.contract_version,
    )
    capabilities = AdapterCapabilities(
        time_measure=descriptor.capabilities.time_measure,
        multiplicity_mode=descriptor.capabilities.multiplicity_mode,
        semantic_reconstruction=descriptor.capabilities.semantic_reconstruction,
        raw_byte_reconstruction=descriptor.capabilities.raw_byte_reconstruction,
        fitted_state=descriptor.capabilities.fitted_state,
        supported_representation_ids=(
            descriptor.capabilities.supported_representation_ids
        ),
        static_context=descriptor.capabilities.static_context,
        evaluation_labels=descriptor.capabilities.evaluation_labels,
        private_provenance=descriptor.capabilities.private_provenance,
    )
    return _domain_digest(
        DESCRIPTOR_DIGEST_DOMAIN,
        {
            "capabilities": _capabilities_payload(capabilities),
            "identity": _identity_payload(identity),
            "unicode_profile": UNICODE_PROFILE,
        },
    )


def _validate_exact_schema_tree(schema: object) -> FeatureSchema:
    if type(schema) is not FeatureSchema:
        raise TypeError("schema must be an exact FeatureSchema")
    if type(schema.event_types) is not tuple:
        raise TypeError("schema event_types must be an exact tuple")
    if type(schema.time_measure) is not TimeMeasureKind:
        raise TypeError("schema time_measure must be an exact TimeMeasureKind")
    if type(schema.multiplicity_mode) is not MultiplicityMode:
        raise TypeError("schema multiplicity_mode must be an exact MultiplicityMode")
    if type(schema.allow_simultaneous) is not bool:
        raise TypeError("schema allow_simultaneous must be an exact boolean")
    _validated_private_text(schema.version, name="schema version")
    if schema.horizon is not None:
        _float_hex(schema.horizon, name="schema horizon")
    if type(schema.time_reference) is not TimeReference:
        raise TypeError("time_reference must be an exact TimeReference")
    reference = schema.time_reference
    if type(reference.kind) is not TimeMeasureKind:
        raise TypeError("time-reference kind must be an exact TimeMeasureKind")
    if type(reference.atoms) is not tuple or any(
        type(value) is not float for value in reference.atoms
    ):
        raise TypeError("time-reference atoms must be canonical floats")
    if type(reference.atom_weights) is not tuple or any(
        type(value) is not float for value in reference.atom_weights
    ):
        raise TypeError("time-reference weights must be canonical floats")
    _float_hex(reference.continuous_weight, name="continuous time weight")
    for event_type in schema.event_types:
        if type(event_type) is not EventTypeSchema:
            raise TypeError("event types must be exact EventTypeSchema instances")
        if type(event_type.type_id) is not int:
            raise TypeError("event type ids must be canonical integers")
        if event_type.type_id > _MAX_SAFE_JSON_INTEGER:
            raise ValueError("event type id exceeds the canonical JSON range")
        _validated_private_text(event_type.name, name="event type name")
        if type(event_type.fields) is not tuple:
            raise TypeError("event-type fields must be an exact tuple")
        for field in event_type.fields:
            if type(field) is not ContinuousField:
                raise TypeError("fields must be exact ContinuousField instances")
            _validated_private_text(field.name, name="field name")
            if type(field.dimension) is not int:
                raise TypeError("field dimensions must be canonical integers")
            if field.dimension > _MAX_SAFE_JSON_INTEGER:
                raise ValueError("field dimension exceeds the canonical JSON range")
            if type(field.support) is not SupportKind:
                raise TypeError("field support must be an exact SupportKind")
            if field.lower is not None:
                _float_hex(field.lower, name="field lower bound")
            if field.upper is not None:
                _float_hex(field.upper, name="field upper bound")
            if field.unit is not None:
                _validated_private_text(field.unit, name="field unit")
    return schema


def rebuild_exact_schema(schema: FeatureSchema) -> FeatureSchema:
    """Return a canonical exact-type schema detached from adapter objects."""

    source = _validate_exact_schema_tree(schema)
    assert source.time_reference is not None
    reference = TimeReference(
        kind=source.time_reference.kind,
        atoms=tuple(
            0.0 if value == 0.0 else value for value in source.time_reference.atoms
        ),
        atom_weights=tuple(
            0.0 if value == 0.0 else value
            for value in source.time_reference.atom_weights
        ),
        continuous_weight=(
            0.0
            if source.time_reference.continuous_weight == 0.0
            else source.time_reference.continuous_weight
        ),
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
                    lower=(
                        None
                        if field.lower is None
                        else 0.0 if field.lower == 0.0 else field.lower
                    ),
                    upper=(
                        None
                        if field.upper is None
                        else 0.0 if field.upper == 0.0 else field.upper
                    ),
                    unit=field.unit,
                )
                for field in sorted(event_type.fields, key=lambda item: item.name)
            ),
        )
        for event_type in sorted(source.event_types, key=lambda item: item.type_id)
    )
    return FeatureSchema(
        event_types=event_types,
        horizon=(
            None
            if source.horizon is None
            else 0.0 if source.horizon == 0.0 else source.horizon
        ),
        time_measure=source.time_measure,
        time_reference=reference,
        allow_simultaneous=source.allow_simultaneous,
        version=source.version,
        multiplicity_mode=source.multiplicity_mode,
    )


def _schema_payload(schema: FeatureSchema) -> object:
    canonical = rebuild_exact_schema(schema)
    assert canonical.time_reference is not None
    return {
        "allow_simultaneous": canonical.allow_simultaneous,
        "event_types": [
            {
                "fields": [
                    {
                        "dimension": field.dimension,
                        "lower": (
                            None
                            if field.lower is None
                            else _float_hex(field.lower, name="field lower bound")
                        ),
                        "name": field.name,
                        "support": field.support.value,
                        "unit": field.unit,
                        "upper": (
                            None
                            if field.upper is None
                            else _float_hex(field.upper, name="field upper bound")
                        ),
                    }
                    for field in event_type.fields
                ],
                "name": event_type.name,
                "type_id": event_type.type_id,
            }
            for event_type in canonical.event_types
        ],
        "horizon": (
            None
            if canonical.horizon is None
            else _float_hex(canonical.horizon, name="schema horizon")
        ),
        "multiplicity_mode": canonical.multiplicity_mode.value,
        "time_measure": canonical.time_measure.value,
        "time_reference": {
            "atom_weights": [
                _float_hex(value, name="time atom weight")
                for value in canonical.time_reference.atom_weights
            ],
            "atoms": [
                _float_hex(value, name="time atom")
                for value in canonical.time_reference.atoms
            ],
            "continuous_weight": _float_hex(
                canonical.time_reference.continuous_weight,
                name="continuous time weight",
            ),
            "kind": canonical.time_reference.kind.value,
        },
        "version": canonical.version,
    }


def feature_schema_digest(schema: FeatureSchema) -> str:
    """Commit to one canonical exact native feature schema."""

    return _domain_digest(SCHEMA_DIGEST_DOMAIN, _schema_payload(schema))


def _validate_exact_configuration_tree(
    configuration: object,
) -> EventConfiguration:
    if type(configuration) is not EventConfiguration:
        raise TypeError("configuration must be an exact EventConfiguration")
    _validate_exact_schema_tree(configuration.schema)
    if type(configuration.events) is not tuple:
        raise TypeError("configuration events must be an exact tuple")
    if (
        type(configuration.sample_id) is not str
        or type(configuration.group_id) is not str
    ):
        raise TypeError("configuration identifiers must be exact strings")
    if type(configuration.observed) is not ObservationPattern:
        raise TypeError("observed must be an exact ObservationPattern")
    if type(configuration.observed.events) is not tuple:
        raise TypeError("observation events must be an exact tuple")
    if type(configuration.observed.cardinality_observed) is not bool:
        raise TypeError("cardinality_observed must be an exact boolean")
    for event in configuration.events:
        if type(event) is not Event:
            raise TypeError("events must contain exact Event instances")
        if type(event.event_time) is not float or type(event.event_type) is not int:
            raise TypeError("event coordinates must use canonical base types")
        _float_hex(event.event_time, name="event time")
        if type(event.marks) is not MappingProxyType:
            raise TypeError("event marks must use the immutable base mapping")
        for name, vector in event.marks.items():
            _validated_private_text(name, name="mark name")
            if type(vector) is not tuple or any(
                type(value) is not float for value in vector
            ):
                raise TypeError("mark values must be exact tuples of floats")
            for value in vector:
                _float_hex(value, name="mark value")
    for observation in configuration.observed.events:
        if type(observation) is not EventObservation:
            raise TypeError("observations must be exact EventObservation instances")
        if type(observation.time_observed) is not bool or type(
            observation.type_observed
        ) is not bool:
            raise TypeError("observation flags must be exact booleans")
        if type(observation.observed_marks) is not frozenset:
            raise TypeError("observed marks must be an exact frozenset")
        for name in observation.observed_marks:
            _validated_private_text(name, name="observed mark name")
    configuration.validate()
    return configuration


def rebuild_detached_native_configuration(
    configuration: EventConfiguration,
    *,
    schema: Optional[FeatureSchema] = None,
) -> EventConfiguration:
    """Rebuild exact native objects while dropping every bookkeeping ID."""

    if type(configuration) is not EventConfiguration:
        raise TypeError("configuration must be an exact EventConfiguration")
    canonical_schema = rebuild_exact_schema(
        configuration.schema if schema is None else schema
    )
    if feature_schema_digest(configuration.schema) != feature_schema_digest(
        canonical_schema
    ):
        raise AdapterContractError("configuration schema disagrees with adapter schema")
    source = _validate_exact_configuration_tree(configuration)
    assert source.observed is not None
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
        schema=canonical_schema,
        events=tuple(
            Event(
                event_time=event.event_time,
                event_type=event.event_type,
                marks={name: tuple(values) for name, values in event.marks.items()},
                event_id=None,
            )
            for event in source.events
        ),
        observed=observations,
        sample_id="",
        group_id="",
    )


def _native_observation_payload(configuration: EventConfiguration) -> object:
    detached = rebuild_detached_native_configuration(configuration)
    assert detached.observed is not None
    return {
        "occurrences": [
            {
                "event": {
                    "event_time": _float_hex(event.event_time, name="event time"),
                    "event_type": event.event_type,
                    "marks": {
                        name: [
                            _float_hex(value, name="mark value") for value in vector
                        ]
                        for name, vector in event.marks.items()
                    },
                },
                "observation": {
                    "observed_marks": sorted(observation.observed_marks),
                    "time_observed": observation.time_observed,
                    "type_observed": observation.type_observed,
                },
            }
            for event, observation in zip(
                detached.events, detached.observed.events
            )
        ],
        "observation_pattern": {
            "cardinality_observed": detached.observed.cardinality_observed,
        },
        "schema": _schema_payload(detached.schema),
    }


def native_observation_digest(configuration: EventConfiguration) -> str:
    """Commit to schema, ID-free occurrences, and source observation masks."""

    return _domain_digest(
        NATIVE_OBSERVATION_DIGEST_DOMAIN,
        _native_observation_payload(configuration),
    )


def split_manifest_digest(manifest: SplitManifest) -> str:
    """Commit to a complete canonical group-disjoint corpus partition."""

    if type(manifest) is not SplitManifest:
        raise TypeError("split manifest must be an exact SplitManifest")
    snapshot = SplitManifest(manifest.entries)
    return _domain_digest(
        SPLIT_MANIFEST_DIGEST_DOMAIN,
        {
            "entries": [
                {
                    "group_id": entry.group_id,
                    "sample_id": entry.sample_id,
                    "split": entry.split,
                }
                for entry in snapshot.entries
            ],
            "unicode_profile": UNICODE_PROFILE,
        },
    )


def _sample_manifest_payload(manifest: "AdapterManifest") -> object:
    return {
        "coverage_ledger_sha256": manifest.coverage_ledger_sha256,
        "descriptor_sha256": manifest.descriptor_sha256,
        "evaluation_labels_sha256": manifest.evaluation_labels_sha256,
        "fitted_state_sha256": manifest.fitted_state_sha256,
        "native_observation_sha256": manifest.native_observation_sha256,
        "partition": {
            "group_id": manifest.partition.group_id,
            "sample_id": manifest.partition.sample_id,
            "split": manifest.partition.split,
        },
        "private_provenance_sha256": manifest.private_provenance_sha256,
        "schema_sha256": manifest.schema_sha256,
        "schema_version": manifest.schema_version,
        "semantic_reconstruction_sha256": (
            manifest.semantic_reconstruction_sha256
        ),
        "source_sha256": manifest.source_sha256,
        "source_size_bytes": manifest.source_size_bytes,
        "split_manifest_sha256": manifest.split_manifest_sha256,
        "static_context_sha256": manifest.static_context_sha256,
    }


@dataclass(frozen=True)
class AdapterManifest:
    """Acyclic content commitments for one adapted source sample."""

    descriptor_sha256: str
    partition: SamplePartition
    source_sha256: str
    source_size_bytes: int
    schema_sha256: str
    schema_version: str
    split_manifest_sha256: str
    native_observation_sha256: str
    static_context_sha256: str
    evaluation_labels_sha256: str
    coverage_ledger_sha256: str
    fitted_state_sha256: str
    private_provenance_sha256: str
    semantic_reconstruction_sha256: str
    sample_root_sha256: str

    def __post_init__(self) -> None:
        if type(self.partition) is not SamplePartition:
            raise TypeError("partition must be an exact SamplePartition")
        object.__setattr__(
            self,
            "partition",
            SamplePartition(
                self.partition.sample_id,
                self.partition.group_id,
                self.partition.split,
            ),
        )
        for name in (
            "descriptor_sha256",
            "source_sha256",
            "schema_sha256",
            "split_manifest_sha256",
            "native_observation_sha256",
            "static_context_sha256",
            "evaluation_labels_sha256",
            "coverage_ledger_sha256",
            "fitted_state_sha256",
            "private_provenance_sha256",
            "semantic_reconstruction_sha256",
            "sample_root_sha256",
        ):
            _validated_sha256(getattr(self, name), name=name)
        object.__setattr__(
            self,
            "source_size_bytes",
            _validated_nonnegative_size(
                self.source_size_bytes, name="source_size_bytes"
            ),
        )
        _validated_private_text(self.schema_version, name="schema_version")
        expected_root = _domain_digest(
            SAMPLE_MANIFEST_DIGEST_DOMAIN, _sample_manifest_payload(self)
        )
        if self.sample_root_sha256 != expected_root:
            raise AdapterContractError("sample-root digest mismatch")


def build_adapter_manifest(
    *,
    descriptor: AdapterDescriptor,
    partition: SamplePartition,
    source_bytes: bytes,
    split_manifest: SplitManifest,
    configuration: EventConfiguration,
    static_context_sha256: str = EMPTY_STATIC_CONTEXT_SHA256,
    evaluation_labels_sha256: str = EMPTY_EVALUATION_LABELS_SHA256,
    coverage_ledger_sha256: str = EMPTY_COVERAGE_LEDGER_SHA256,
    fitted_state_sha256: str = NO_FITTED_STATE_SHA256,
    private_provenance_sha256: str = EMPTY_PRIVATE_PROVENANCE_SHA256,
    semantic_reconstruction_sha256: str = EMPTY_SEMANTIC_RECONSTRUCTION_SHA256,
) -> AdapterManifest:
    """Build a manifest from core recomputations and opaque leaf digests.

    Descriptor, source, split, schema, and native-observation leaves are
    recomputed here.  Static context, labels, coverage, fit, provenance, and
    semantic reconstruction remain caller-supplied digest commitments until
    their Phase-C object contracts exist.
    """

    if type(descriptor) is not AdapterDescriptor:
        raise TypeError("descriptor must be an exact AdapterDescriptor")
    if type(partition) is not SamplePartition:
        raise TypeError("partition must be an exact SamplePartition")
    if type(source_bytes) is not bytes:
        raise TypeError("source_bytes must be exact immutable bytes")
    if type(split_manifest) is not SplitManifest:
        raise TypeError("split_manifest must be an exact SplitManifest")
    split_manifest = SplitManifest(split_manifest.entries)
    if not split_manifest.contains_exactly(partition):
        raise AdapterContractError("partition is absent from the split manifest")
    schema = rebuild_exact_schema(configuration.schema)
    values = {
        "descriptor_sha256": descriptor.descriptor_sha256,
        "partition": partition,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_size_bytes": len(source_bytes),
        "schema_sha256": feature_schema_digest(schema),
        "schema_version": schema.version,
        "split_manifest_sha256": split_manifest.split_manifest_sha256,
        "native_observation_sha256": native_observation_digest(configuration),
        "static_context_sha256": _validated_sha256(
            static_context_sha256, name="static_context_sha256"
        ),
        "evaluation_labels_sha256": _validated_sha256(
            evaluation_labels_sha256, name="evaluation_labels_sha256"
        ),
        "coverage_ledger_sha256": _validated_sha256(
            coverage_ledger_sha256, name="coverage_ledger_sha256"
        ),
        "fitted_state_sha256": _validated_sha256(
            fitted_state_sha256, name="fitted_state_sha256"
        ),
        "private_provenance_sha256": _validated_sha256(
            private_provenance_sha256, name="private_provenance_sha256"
        ),
        "semantic_reconstruction_sha256": _validated_sha256(
            semantic_reconstruction_sha256,
            name="semantic_reconstruction_sha256",
        ),
    }
    provisional = object.__new__(AdapterManifest)
    for name, value in values.items():
        object.__setattr__(provisional, name, value)
    root = _domain_digest(
        SAMPLE_MANIFEST_DIGEST_DOMAIN, _sample_manifest_payload(provisional)
    )
    return AdapterManifest(sample_root_sha256=root, **values)


@dataclass(frozen=True)
class AdaptedEventSample:
    """The minimal Phase-B output of a domain adapter."""

    configuration: EventConfiguration
    manifest: AdapterManifest

    def __post_init__(self) -> None:
        if type(self.configuration) is not EventConfiguration:
            raise TypeError("configuration must be an exact EventConfiguration")
        if type(self.manifest) is not AdapterManifest:
            raise TypeError("manifest must be an exact AdapterManifest")
        _validate_exact_configuration_tree(self.configuration)
        manifest = _validate_manifest_shape(self.manifest)
        expected_root = _domain_digest(
            SAMPLE_MANIFEST_DIGEST_DOMAIN,
            _sample_manifest_payload(manifest),
        )
        if manifest.sample_root_sha256 != expected_root:
            raise AdapterContractError("sample-root digest mismatch")
        object.__setattr__(self, "manifest", manifest)

    def validate(
        self,
        adapter: "NativeEventAdapter",
        *,
        source_bytes: bytes,
        split_manifest: SplitManifest,
    ) -> EventConfiguration:
        return validate_adapted_event_sample(
            adapter,
            self,
            source_bytes=source_bytes,
            split_manifest=split_manifest,
        )


@runtime_checkable
class AdapterDescriptorProvider(Protocol):
    """Structural identity/schema surface needed by the shared validator."""

    def descriptor(self) -> AdapterDescriptor:
        ...

    def schema(self) -> FeatureSchema:
        ...


@runtime_checkable
class NativeEventAdapter(AdapterDescriptorProvider, Protocol):
    """Minimal Phase-B structural adapter protocol.

    Source inventory, fitted preprocessing, coverage, reconstruction, tasks,
    and representation encoders are intentionally separate later contracts.
    """

    def adapt(
        self,
        source_bytes: bytes,
        partition: SamplePartition,
        split_manifest: SplitManifest,
    ) -> AdaptedEventSample:
        ...

    def validate_domain_sample(self, sample: AdaptedEventSample) -> None:
        ...


def _validate_capability_commitments(
    capabilities: AdapterCapabilities, manifest: AdapterManifest
) -> None:
    checks = (
        (
            capabilities.static_context,
            manifest.static_context_sha256,
            EMPTY_STATIC_CONTEXT_SHA256,
            "static context",
        ),
        (
            capabilities.evaluation_labels,
            manifest.evaluation_labels_sha256,
            EMPTY_EVALUATION_LABELS_SHA256,
            "evaluation labels",
        ),
        (
            capabilities.private_provenance,
            manifest.private_provenance_sha256,
            EMPTY_PRIVATE_PROVENANCE_SHA256,
            "private provenance",
        ),
        (
            capabilities.fitted_state,
            manifest.fitted_state_sha256,
            NO_FITTED_STATE_SHA256,
            "fitted state",
        ),
    )
    for occurs, digest, empty_digest, label in checks:
        if occurs and digest == empty_digest:
            raise AdapterContractError(
                "{} capability uses its empty sentinel".format(label)
            )
        if not occurs and digest != empty_digest:
            raise AdapterContractError(
                "{} digest contradicts its capability".format(label)
            )


def _snapshot_descriptor(descriptor: object) -> AdapterDescriptor:
    """Re-run all identity/capability checks after crossing trust boundary."""

    if type(descriptor) is not AdapterDescriptor:
        raise TypeError("adapter descriptor must be an exact AdapterDescriptor")
    identity = descriptor.identity
    capabilities = descriptor.capabilities
    if type(identity) is not AdapterIdentity:
        raise TypeError("descriptor identity must be an exact AdapterIdentity")
    if type(capabilities) is not AdapterCapabilities:
        raise TypeError(
            "descriptor capabilities must be exact AdapterCapabilities"
        )
    return AdapterDescriptor(
        AdapterIdentity(
            adapter_id=identity.adapter_id,
            adapter_version=identity.adapter_version,
            policy_sha256=identity.policy_sha256,
            contract_version=identity.contract_version,
        ),
        AdapterCapabilities(
            time_measure=capabilities.time_measure,
            multiplicity_mode=capabilities.multiplicity_mode,
            semantic_reconstruction=capabilities.semantic_reconstruction,
            raw_byte_reconstruction=capabilities.raw_byte_reconstruction,
            fitted_state=capabilities.fitted_state,
            supported_representation_ids=capabilities.supported_representation_ids,
            static_context=capabilities.static_context,
            evaluation_labels=capabilities.evaluation_labels,
            private_provenance=capabilities.private_provenance,
        ),
    )


def _validate_manifest_shape(manifest: object) -> AdapterManifest:
    """Snapshot exact fields without checking cross-field commitments."""

    if type(manifest) is not AdapterManifest:
        raise TypeError("manifest must be an exact AdapterManifest")
    if type(manifest.partition) is not SamplePartition:
        raise TypeError("manifest partition must be an exact SamplePartition")
    partition = SamplePartition(
        manifest.partition.sample_id,
        manifest.partition.group_id,
        manifest.partition.split,
    )
    digest_names = (
        "descriptor_sha256",
        "source_sha256",
        "schema_sha256",
        "split_manifest_sha256",
        "native_observation_sha256",
        "static_context_sha256",
        "evaluation_labels_sha256",
        "coverage_ledger_sha256",
        "fitted_state_sha256",
        "private_provenance_sha256",
        "semantic_reconstruction_sha256",
        "sample_root_sha256",
    )
    values = {
        name: _validated_sha256(getattr(manifest, name), name=name)
        for name in digest_names
    }
    values["source_size_bytes"] = _validated_nonnegative_size(
        manifest.source_size_bytes,
        name="source_size_bytes",
    )
    values["schema_version"] = _validated_private_text(
        manifest.schema_version,
        name="schema_version",
    )
    values["partition"] = partition
    snapshot = object.__new__(AdapterManifest)
    for name, value in values.items():
        object.__setattr__(snapshot, name, value)
    return snapshot


def validate_adapted_event_sample(
    adapter: NativeEventAdapter,
    sample: AdaptedEventSample,
    *,
    source_bytes: bytes,
    split_manifest: SplitManifest,
) -> EventConfiguration:
    """Validate all Phase-B commitments and return the detached native state."""

    if not isinstance(adapter, NativeEventAdapter):
        raise TypeError("adapter does not satisfy NativeEventAdapter")
    if type(sample) is not AdaptedEventSample:
        raise TypeError("sample must be an exact AdaptedEventSample")
    if type(source_bytes) is not bytes:
        raise TypeError("source_bytes must be exact immutable bytes")
    if type(split_manifest) is not SplitManifest:
        raise TypeError("split_manifest must be an exact SplitManifest")
    split_manifest = SplitManifest(split_manifest.entries)

    descriptor = _snapshot_descriptor(adapter.descriptor())
    adapter_schema = adapter.schema()
    canonical_schema = rebuild_exact_schema(adapter_schema)
    capabilities = descriptor.capabilities
    if capabilities.time_measure is not canonical_schema.time_measure:
        raise AdapterContractError("declared time measure disagrees with schema")
    if capabilities.multiplicity_mode is not canonical_schema.multiplicity_mode:
        raise AdapterContractError("declared multiplicity mode disagrees with schema")

    domain_result = adapter.validate_domain_sample(sample)
    if domain_result is not None:
        raise TypeError("validate_domain_sample must return None")

    manifest = _validate_manifest_shape(sample.manifest)
    if manifest.descriptor_sha256 != descriptor.descriptor_sha256:
        raise AdapterContractError("descriptor digest mismatch")
    if sample.configuration.sample_id != manifest.partition.sample_id:
        raise AdapterContractError("configuration sample_id disagrees with partition")
    if sample.configuration.group_id != manifest.partition.group_id:
        raise AdapterContractError("configuration group_id disagrees with partition")
    if not split_manifest.contains_exactly(manifest.partition):
        raise AdapterContractError("partition is absent from the split manifest")
    if manifest.split_manifest_sha256 != split_manifest.split_manifest_sha256:
        raise AdapterContractError("split-manifest digest mismatch")
    if manifest.source_size_bytes != len(source_bytes):
        raise AdapterContractError("source byte-count mismatch")
    if manifest.source_sha256 != hashlib.sha256(source_bytes).hexdigest():
        raise AdapterContractError("source digest mismatch")
    expected_schema_digest = feature_schema_digest(canonical_schema)
    if manifest.schema_sha256 != expected_schema_digest:
        raise AdapterContractError("schema digest mismatch")
    if manifest.schema_version != canonical_schema.version:
        raise AdapterContractError("schema version mismatch")

    detached = rebuild_detached_native_configuration(
        sample.configuration, schema=canonical_schema
    )
    expected_native_digest = native_observation_digest(detached)
    if manifest.native_observation_sha256 != expected_native_digest:
        raise AdapterContractError("native-observation digest mismatch")
    _validate_capability_commitments(capabilities, manifest)
    if (
        manifest.semantic_reconstruction_sha256
        == EMPTY_SEMANTIC_RECONSTRUCTION_SHA256
    ):
        raise AdapterContractError(
            "mandatory semantic reconstruction uses its empty sentinel"
        )
    if capabilities.raw_byte_reconstruction:
        raise AdapterContractError(
            "raw-byte reconstruction is not committed by the Phase-B manifest"
        )

    expected_root = _domain_digest(
        SAMPLE_MANIFEST_DIGEST_DOMAIN, _sample_manifest_payload(manifest)
    )
    if manifest.sample_root_sha256 != expected_root:
        raise AdapterContractError("sample-root digest mismatch")
    return detached


__all__ = [
    "ADAPTER_CONTRACT_VERSION",
    "ATOMIC_COUNTING_GRID_REPRESENTATION_ID",
    "AdapterCapabilities",
    "AdapterContractError",
    "AdapterDescriptor",
    "AdapterDescriptorProvider",
    "AdapterIdentity",
    "AdapterManifest",
    "AdaptedEventSample",
    "COVERAGE_LEDGER_DIGEST_DOMAIN",
    "DESCRIPTOR_DIGEST_DOMAIN",
    "EMPTY_COVERAGE_LEDGER_SHA256",
    "EMPTY_EVALUATION_LABELS_SHA256",
    "EMPTY_PRIVATE_PROVENANCE_SHA256",
    "EMPTY_SEMANTIC_RECONSTRUCTION_SHA256",
    "EMPTY_STATIC_CONTEXT_SHA256",
    "EVALUATION_LABELS_DIGEST_DOMAIN",
    "FITTED_STATE_DIGEST_DOMAIN",
    "NATIVE_OBSERVATION_DIGEST_DOMAIN",
    "NO_FITTED_STATE_SHA256",
    "NativeEventAdapter",
    "PRIVATE_PROVENANCE_DIGEST_DOMAIN",
    "SAMPLE_MANIFEST_DIGEST_DOMAIN",
    "SCHEMA_DIGEST_DOMAIN",
    "SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN",
    "SPLIT_MANIFEST_DIGEST_DOMAIN",
    "STATIC_CONTEXT_DIGEST_DOMAIN",
    "SamplePartition",
    "SplitManifest",
    "UNICODE_PROFILE",
    "adapter_descriptor_digest",
    "build_adapter_manifest",
    "feature_schema_digest",
    "native_observation_digest",
    "rebuild_detached_native_configuration",
    "rebuild_exact_schema",
    "split_manifest_digest",
    "validate_adapted_event_sample",
]
