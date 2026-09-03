"""Publisher-side private payload projections for Phase-D development.

This module is deliberately write-free.  It accepts only exact Phase-C
contract objects (or exact immutable byte strings), takes fresh bounded
snapshots, and emits immutable canonical-payload handles.  It does not accept
caller dictionaries, caller-selected leaf domains, representation-codec
payloads, filesystem paths, or a gate decision.

The projection handles and wrapper helpers are serializer-internal values,
never accepted publication inputs or preparation provenance.  The projections
are the publisher implementation only.  A publication
verifier must implement the schemas and digest computations independently.
Nothing in this module establishes ``ADAPTER-CONFORMANCE-GO``.
"""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Optional, Union

from heterodiff.events import EventConfiguration, FeatureSchema

from . import adapter_contract as _contract
from . import adapter_evidence as _evidence
from .adapter_conformance_runner import ConformanceRun
from .adapter_conformance_execution_guard import (
    ExecutionReceipt,
    validate_execution_receipt,
)
from .adapter_contract import (
    AdapterDescriptor,
    AdapterManifest,
    SamplePartition,
    SplitManifest,
)
from .adapter_evidence import (
    CompleteAdaptedEventSample,
    EvaluationLabels,
    ExpectedAdapterEvidence,
    FittedAdapterState,
    PrivateProvenance,
    SemanticReconstruction,
    SourceCoverageLedger,
    SourceInventory,
    StaticContext,
)
from .adapter_publication_types import (
    EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE,
    ExecutionGuardRunManifestV1,
    HostileControlInputV1,
    MAXIMUM_GOLDEN_DEFINITION_BYTES,
    MAXIMUM_REGISTRY_VALUES_PER_CATEGORY,
    PublicAdapterIdentityV1,
    PublicIdentifierRegistryV1,
)


PUBLICATION_PAYLOAD_IMPLEMENTATION_STATUS = "DEVELOPMENT_ONLY"

PRIVATE_PARTITION_DIGEST_DOMAIN = "heterodiff.adapter.private-partition.v1"
COMPLETE_SAMPLE_DIGEST_DOMAIN = (
    "heterodiff.adapter.complete-sample-publication.v1"
)
RAW_RECONSTRUCTION_ABSENCE_DIGEST_DOMAIN = (
    "heterodiff.adapter.raw-reconstruction-absence.v1"
)
RAW_RECONSTRUCTION_BYTES_DIGEST_DOMAIN = (
    "heterodiff.adapter.raw-reconstruction-bytes.v1"
)
CONFORMANCE_RUN_DIGEST_DOMAIN = (
    "heterodiff.adapter.conformance-run-receipt.v1"
)
EXECUTION_GUARD_RUN_MANIFEST_DIGEST_DOMAIN = (
    EXECUTION_GUARD_RUN_MANIFEST_ARTIFACT_TYPE
)
EXECUTION_GUARD_RECEIPT_DIGEST_DOMAIN = (
    "heterodiff.adapter.development-execution-guard-receipt.v1"
)
INDEPENDENT_GOLDEN_CASE_DIGEST_DOMAIN = (
    "heterodiff.adapter.development-independent-golden-case.v1"
)
HOSTILE_CONTROL_RECEIPT_DIGEST_DOMAIN = (
    "heterodiff.adapter.hostile-control-receipt.v1"
)
HOSTILE_CONTROL_INPUT_DIGEST_DOMAIN = (
    "heterodiff.adapter.hostile-control-input.v1"
)
HOSTILE_CONTROL_TEST_NODE_DIGEST_DOMAIN = (
    "heterodiff.adapter.hostile-test-node.v1"
)
PUBLIC_ID_REGISTRY_DIGEST_DOMAIN = (
    "heterodiff.adapter.public-id-registry.v1"
)
PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-native-configuration.v1"
)
PRIVATE_SOURCE_INVENTORY_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-source-inventory.v1"
)
PRIVATE_COVERAGE_LEDGER_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-coverage-ledger.v1"
)
PRIVATE_STATIC_CONTEXT_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-static-context.v1"
)
PRIVATE_EVALUATION_LABELS_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-evaluation-labels.v1"
)
PRIVATE_PROVENANCE_PAYLOAD_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-provenance-payload.v1"
)
PRIVATE_FITTED_STATE_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-fitted-state.v1"
)
PRIVATE_SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-semantic-reconstruction.v1"
)

MAXIMUM_PRIVATE_ARTIFACT_BYTES = 16 * 1024 * 1024
MAXIMUM_CANONICAL_LEAF_BYTES = MAXIMUM_PRIVATE_ARTIFACT_BYTES
MAXIMUM_CANONICAL_DEPTH = 32
MAXIMUM_CANONICAL_NODES = 200_000
MAXIMUM_CANONICAL_STRING_BYTES = 512 * 1024
_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1

_CANONICAL_PAYLOAD_DIGEST_DOMAINS = frozenset(
    (
        _contract.DESCRIPTOR_DIGEST_DOMAIN,
        _contract.NATIVE_OBSERVATION_DIGEST_DOMAIN,
        _contract.SAMPLE_MANIFEST_DIGEST_DOMAIN,
        _contract.SPLIT_MANIFEST_DIGEST_DOMAIN,
        _evidence.EXPECTED_EVIDENCE_DIGEST_DOMAIN,
        COMPLETE_SAMPLE_DIGEST_DOMAIN,
        CONFORMANCE_RUN_DIGEST_DOMAIN,
        EXECUTION_GUARD_RECEIPT_DIGEST_DOMAIN,
        EXECUTION_GUARD_RUN_MANIFEST_DIGEST_DOMAIN,
        HOSTILE_CONTROL_RECEIPT_DIGEST_DOMAIN,
        INDEPENDENT_GOLDEN_CASE_DIGEST_DOMAIN,
        PRIVATE_COVERAGE_LEDGER_DIGEST_DOMAIN,
        PRIVATE_EVALUATION_LABELS_DIGEST_DOMAIN,
        PRIVATE_FITTED_STATE_DIGEST_DOMAIN,
        PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN,
        PRIVATE_PARTITION_DIGEST_DOMAIN,
        PRIVATE_PROVENANCE_PAYLOAD_DIGEST_DOMAIN,
        PRIVATE_SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN,
        PRIVATE_SOURCE_INVENTORY_DIGEST_DOMAIN,
        PRIVATE_STATIC_CONTEXT_DIGEST_DOMAIN,
        PUBLIC_ID_REGISTRY_DIGEST_DOMAIN,
        RAW_RECONSTRUCTION_ABSENCE_DIGEST_DOMAIN,
    )
)


class PublicationPayloadError(ValueError):
    """A typed projection cannot be represented by the Phase-D profile."""


def _encoded_base64_length(decoded_length: int) -> int:
    if type(decoded_length) is not int:
        raise TypeError("decoded length must be an exact integer")
    if decoded_length < 0:
        raise PublicationPayloadError("decoded length must be nonnegative")
    return 4 * ((decoded_length + 2) // 3)


def _canonical_base64(value: bytes, *, maximum_encoded_bytes: int) -> str:
    if type(value) is not bytes:
        raise TypeError("base64 input must be exact immutable bytes")
    encoded_length = _encoded_base64_length(len(value))
    if encoded_length > maximum_encoded_bytes:
        raise PublicationPayloadError("base64 output exceeds its byte ceiling")
    encoded = base64.b64encode(value)
    if len(encoded) != encoded_length:  # pragma: no cover - stdlib invariant
        raise RuntimeError("base64 length invariant failed")
    return encoded.decode("ascii")


def _canonical_string_encoded_size(value: str) -> tuple:
    """Return exact ensure-ASCII JSON and UTF-8 sizes without encoding."""

    if type(value) is not str:
        raise TypeError("canonical string must be exact")
    json_size = 2
    utf8_size = 0
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise PublicationPayloadError(
                "canonical string is not valid Unicode"
            )
        if codepoint <= 0x7F:
            utf8_size += 1
        elif codepoint <= 0x7FF:
            utf8_size += 2
        elif codepoint <= 0xFFFF:
            utf8_size += 3
        else:
            utf8_size += 4
        if character in ('"', "\\", "\b", "\f", "\n", "\r", "\t"):
            json_size += 2
        elif 0x20 <= codepoint <= 0x7E:
            json_size += 1
        elif codepoint <= 0xFFFF:
            json_size += 6
        else:
            json_size += 12
    return json_size, utf8_size


def _preflight_canonical_tree(
    value: object,
    *,
    maximum_encoded_bytes: int,
) -> int:
    """Reject invalid or oversized values before calling the JSON encoder."""

    if type(maximum_encoded_bytes) is not int or maximum_encoded_bytes < 0:
        raise TypeError("canonical byte ceiling must be a nonnegative integer")

    nodes = 0
    encoded_size = 0
    stack = [(value, 0)]

    def add_size(amount: int) -> None:
        nonlocal encoded_size
        encoded_size += amount
        if encoded_size > maximum_encoded_bytes:
            raise PublicationPayloadError(
                "canonical payload exceeds its byte ceiling before encoding"
            )

    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAXIMUM_CANONICAL_NODES:
            raise PublicationPayloadError("canonical payload has too many nodes")
        if depth > MAXIMUM_CANONICAL_DEPTH:
            raise PublicationPayloadError("canonical payload is too deeply nested")
        if current is None:
            add_size(4)
            continue
        if type(current) is bool:
            add_size(4 if current else 5)
            continue
        if type(current) is int:
            if abs(current) > _MAXIMUM_SAFE_INTEGER:
                raise PublicationPayloadError(
                    "canonical integer is outside the exact range"
                )
            add_size(len(str(current)))
            continue
        if type(current) is str:
            json_size, utf8_size = _canonical_string_encoded_size(current)
            if utf8_size > MAXIMUM_CANONICAL_STRING_BYTES:
                raise PublicationPayloadError(
                    "canonical string exceeds its byte ceiling"
                )
            add_size(json_size)
            continue
        if type(current) is list:
            add_size(2 + max(0, len(current) - 1))
            stack.extend((item, depth + 1) for item in reversed(current))
            continue
        if type(current) is dict:
            add_size(2 + max(0, len(current) - 1) + len(current))
            for key, item in current.items():
                if type(key) is not str:
                    raise TypeError("canonical object keys must be exact strings")
                key_size, key_utf8_size = _canonical_string_encoded_size(key)
                if key_utf8_size > MAXIMUM_CANONICAL_STRING_BYTES:
                    raise PublicationPayloadError(
                        "canonical object key exceeds its byte ceiling"
                    )
                add_size(key_size)
                stack.append((item, depth + 1))
            continue
        # In particular, reject every float (including NaN/infinity), tuple,
        # enum instance, mapping proxy, bytes, and user mapping subclass.
        raise TypeError("value is outside the exact canonical JSON profile")
    return encoded_size


def _canonical_tree_bytes(
    value: object,
    *,
    maximum_encoded_bytes: int = MAXIMUM_PRIVATE_ARTIFACT_BYTES,
) -> bytes:
    expected_size = _preflight_canonical_tree(
        value,
        maximum_encoded_bytes=maximum_encoded_bytes,
    )
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as exc:  # pragma: no cover
        raise TypeError("value is not canonical-JSON serializable") from exc
    if len(encoded) != expected_size:  # pragma: no cover - stdlib invariant
        raise RuntimeError("canonical JSON size preflight disagrees with encoder")
    return encoded


def _canonical_tree_from_bytes(value: bytes) -> object:
    """Strict-parse publisher-produced canonical bytes for direct embedding."""

    if type(value) is not bytes:
        raise TypeError("canonical payload bytes must be exact")
    if len(value) > MAXIMUM_CANONICAL_LEAF_BYTES:
        raise PublicationPayloadError("canonical payload exceeds its byte ceiling")
    try:
        text = value.decode("ascii", "strict")
    except UnicodeError:
        raise PublicationPayloadError("canonical payload must be ASCII") from None

    def object_pairs(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise PublicationPayloadError(
                    "canonical payload has a duplicate key"
                )
            result[key] = item
        return result

    def parse_integer(token):
        digits = token[1:] if token.startswith("-") else token
        if len(digits) > 16:
            raise PublicationPayloadError(
                "canonical integer token exceeds its ceiling"
            )
        result = int(token, 10)
        if abs(result) > _MAXIMUM_SAFE_INTEGER:
            raise PublicationPayloadError(
                "canonical integer is outside the exact range"
            )
        return result

    def reject_number(_token):
        raise PublicationPayloadError(
            "canonical payload contains a non-integer number"
        )

    try:
        tree = json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_int=parse_integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
    except PublicationPayloadError:
        raise
    except (TypeError, ValueError, UnicodeError):
        raise PublicationPayloadError(
            "canonical payload is not strict JSON"
        ) from None
    if _canonical_tree_bytes(
        tree,
        maximum_encoded_bytes=MAXIMUM_CANONICAL_LEAF_BYTES,
    ) != value:
        raise PublicationPayloadError("canonical payload bytes are not canonical")
    return tree


def domain_separated_sha256(domain: str, payload_bytes: bytes) -> str:
    """Apply the Phase-D length-framed digest rule to exact bytes."""

    if type(domain) is not str:
        raise TypeError("digest domain must be an exact string")
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except UnicodeError:
        raise PublicationPayloadError(
            "digest domain must contain only ASCII"
        ) from None
    if not domain_bytes or len(domain_bytes) > 256 or b"\x00" in domain_bytes:
        raise PublicationPayloadError("digest domain is outside its bound")
    if type(payload_bytes) is not bytes:
        raise TypeError("digest payload must be exact immutable bytes")
    if len(payload_bytes) > MAXIMUM_PRIVATE_ARTIFACT_BYTES:
        raise PublicationPayloadError("digest payload exceeds its byte ceiling")
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload_bytes).to_bytes(8, "big"))
    digest.update(payload_bytes)
    return digest.hexdigest()


class CanonicalPayloadV1(tuple):
    """Slotless immutable result from one exact typed projection."""

    __slots__ = ()

    def __new__(cls, *args: object, **kwargs: object) -> "CanonicalPayloadV1":
        del cls, args, kwargs
        raise TypeError("canonical payloads are created only by typed projections")

    @property
    def canonical_json_bytes(self) -> bytes:
        return self[0]

    @property
    def digest_domain(self) -> str:
        return self[1]

    @property
    def payload_sha256(self) -> str:
        return self[2]

    @property
    def payload_byte_count(self) -> int:
        return len(self.canonical_json_bytes)


class RawByteObjectV1(tuple):
    """Slotless immutable result for an exact raw-byte object."""

    __slots__ = ()

    def __new__(cls, *args: object, **kwargs: object) -> "RawByteObjectV1":
        del cls, args, kwargs
        raise TypeError("raw-byte objects are created only by typed projections")

    @property
    def bytes_value(self) -> bytes:
        return self[0]

    @property
    def byte_count(self) -> int:
        return self[1]

    @property
    def sha256(self) -> str:
        return self[2]

    @property
    def bytes_b64(self) -> str:
        return self[3]


def _validated_canonical_payload_domain(value: object) -> str:
    if type(value) is not str:
        raise TypeError("canonical payload domain must be an exact string")
    if value not in _CANONICAL_PAYLOAD_DIGEST_DOMAINS:
        raise PublicationPayloadError(
            "canonical payload domain is not frozen for this profile"
        )
    return value


def _new_canonical_payload(
    tree: object,
    *,
    domain: str,
    expected_phase_c_sha256: Optional[str] = None,
) -> CanonicalPayloadV1:
    domain = _validated_canonical_payload_domain(domain)
    payload_bytes = _canonical_tree_bytes(
        tree,
        maximum_encoded_bytes=MAXIMUM_CANONICAL_LEAF_BYTES,
    )
    digest = domain_separated_sha256(domain, payload_bytes)
    if expected_phase_c_sha256 is not None:
        _contract._validated_sha256(
            expected_phase_c_sha256,
            name="expected_phase_c_sha256",
        )
        if digest != expected_phase_c_sha256:
            raise PublicationPayloadError(
                "publisher payload disagrees with its Phase-C commitment"
            )
    return tuple.__new__(
        CanonicalPayloadV1,
        (payload_bytes, domain, digest),
    )


def _new_raw_byte_object(value: bytes, *, maximum_bytes: int) -> RawByteObjectV1:
    if type(value) is not bytes:
        raise TypeError("raw payload must be exact immutable bytes")
    if type(maximum_bytes) is not int or maximum_bytes < 0:
        raise TypeError("raw payload ceiling must be a nonnegative integer")
    if len(value) > maximum_bytes:
        raise PublicationPayloadError("raw payload exceeds its byte ceiling")
    encoded = _canonical_base64(
        value,
        maximum_encoded_bytes=MAXIMUM_PRIVATE_ARTIFACT_BYTES,
    )
    return tuple.__new__(
        RawByteObjectV1,
        (
            value,
            len(value),
            hashlib.sha256(value).hexdigest(),
            encoded,
        ),
    )


def canonical_payload_wrapper(
    value: CanonicalPayloadV1,
    *,
    expected_domain: str,
) -> dict:
    """Return the exact Section-6 wrapper for a typed projection result."""

    if type(value) is not CanonicalPayloadV1:
        raise TypeError("value must be an exact CanonicalPayloadV1")
    expected_domain = _validated_canonical_payload_domain(expected_domain)
    if len(value) != 3:
        raise PublicationPayloadError("canonical payload handle has invalid arity")
    if type(value.canonical_json_bytes) is not bytes:
        raise TypeError("canonical payload bytes must be exact immutable bytes")
    actual_domain = _validated_canonical_payload_domain(value.digest_domain)
    if actual_domain != expected_domain:
        raise PublicationPayloadError(
            "canonical payload domain disagrees with its containing field"
        )
    _contract._validated_sha256(
        value.payload_sha256,
        name="canonical payload digest",
    )
    if len(value.canonical_json_bytes) > MAXIMUM_CANONICAL_LEAF_BYTES:
        raise PublicationPayloadError("canonical payload exceeds its byte ceiling")
    expected = domain_separated_sha256(
        actual_domain, value.canonical_json_bytes
    )
    if value.payload_sha256 != expected:
        raise PublicationPayloadError("canonical payload handle is inconsistent")
    return {
        "payload": _canonical_tree_from_bytes(value.canonical_json_bytes),
        "payload_byte_count": len(value.canonical_json_bytes),
        "payload_sha256": value.payload_sha256,
    }


def raw_byte_object(value: RawByteObjectV1) -> dict:
    """Return the exact Section-6 raw-byte object for a typed byte result."""

    if type(value) is not RawByteObjectV1:
        raise TypeError("value must be an exact RawByteObjectV1")
    if len(value) != 4:
        raise PublicationPayloadError("raw-byte handle has invalid arity")
    if type(value.bytes_value) is not bytes:
        raise TypeError("raw-byte handle bytes must be exact immutable bytes")
    if type(value.byte_count) is not int:
        raise TypeError("raw-byte handle length must be an exact integer")
    _contract._validated_sha256(value.sha256, name="raw-byte handle digest")
    if type(value.bytes_b64) is not str:
        raise TypeError("raw-byte handle base64 must be an exact string")
    if value.byte_count != len(value.bytes_value):
        raise PublicationPayloadError("raw-byte handle has an invalid length")
    if value.sha256 != hashlib.sha256(value.bytes_value).hexdigest():
        raise PublicationPayloadError("raw-byte handle has an invalid digest")
    if value.bytes_b64 != _canonical_base64(
        value.bytes_value,
        maximum_encoded_bytes=MAXIMUM_PRIVATE_ARTIFACT_BYTES,
    ):
        raise PublicationPayloadError("raw-byte handle has invalid base64")
    return {
        "byte_count": value.byte_count,
        "bytes_b64": value.bytes_b64,
        "sha256": value.sha256,
    }


def source_bytes_payload(value: bytes) -> RawByteObjectV1:
    """Project exact source bytes without accepting a path or mutable buffer."""

    return _new_raw_byte_object(value, maximum_bytes=_evidence.MAXIMUM_SOURCE_BYTES)


def _schema_tree(value: FeatureSchema) -> dict:
    canonical = _evidence.snapshot_bounded_schema(value)
    reference = canonical.time_reference
    if reference is None:  # pragma: no cover - FeatureSchema invariant
        raise PublicationPayloadError("schema has no time reference")
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
                            else _contract._float_hex(
                                field.lower, name="field lower bound"
                            )
                        ),
                        "name": field.name,
                        "support": field.support.value,
                        "unit": field.unit,
                        "upper": (
                            None
                            if field.upper is None
                            else _contract._float_hex(
                                field.upper, name="field upper bound"
                            )
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
            else _contract._float_hex(canonical.horizon, name="schema horizon")
        ),
        "multiplicity_mode": canonical.multiplicity_mode.value,
        "time_measure": canonical.time_measure.value,
        "time_reference": {
            "atom_weights": [
                _contract._float_hex(item, name="time atom weight")
                for item in reference.atom_weights
            ],
            "atoms": [
                _contract._float_hex(item, name="time atom")
                for item in reference.atoms
            ],
            "continuous_weight": _contract._float_hex(
                reference.continuous_weight,
                name="continuous time weight",
            ),
            "kind": reference.kind.value,
        },
        "version": canonical.version,
    }


def adapter_descriptor_payload(value: AdapterDescriptor) -> CanonicalPayloadV1:
    if type(value) is not AdapterDescriptor:
        raise TypeError("descriptor must be an exact AdapterDescriptor")
    snapshot = _contract._snapshot_descriptor(value)
    capabilities = snapshot.capabilities
    identity = snapshot.identity
    tree = {
        "capabilities": {
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
        },
        "identity": {
            "adapter_id": identity.adapter_id,
            "adapter_version": identity.adapter_version,
            "contract_version": identity.contract_version,
            "policy_sha256": identity.policy_sha256,
        },
        "unicode_profile": _contract.UNICODE_PROFILE,
    }
    return _new_canonical_payload(
        tree,
        domain=_contract.DESCRIPTOR_DIGEST_DOMAIN,
        expected_phase_c_sha256=_contract.adapter_descriptor_digest(snapshot),
    )


def partition_payload(value: SamplePartition) -> CanonicalPayloadV1:
    if type(value) is not SamplePartition:
        raise TypeError("partition must be an exact SamplePartition")
    snapshot = SamplePartition(value.sample_id, value.group_id, value.split)
    return _new_canonical_payload(
        {
            "group_id": snapshot.group_id,
            "sample_id": snapshot.sample_id,
            "split": snapshot.split,
            "unicode_profile": _contract.UNICODE_PROFILE,
        },
        domain=PRIVATE_PARTITION_DIGEST_DOMAIN,
    )


def split_manifest_payload(value: SplitManifest) -> CanonicalPayloadV1:
    if type(value) is not SplitManifest:
        raise TypeError("split manifest must be an exact SplitManifest")
    snapshot = _evidence.snapshot_bounded_split_manifest(value)
    return _new_canonical_payload(
        {
            "entries": [
                {
                    "group_id": item.group_id,
                    "sample_id": item.sample_id,
                    "split": item.split,
                }
                for item in snapshot.entries
            ],
            "unicode_profile": _contract.UNICODE_PROFILE,
        },
        domain=_contract.SPLIT_MANIFEST_DIGEST_DOMAIN,
        expected_phase_c_sha256=_contract.split_manifest_digest(snapshot),
    )


def adapter_manifest_payload(value: AdapterManifest) -> CanonicalPayloadV1:
    if type(value) is not AdapterManifest:
        raise TypeError("manifest must be an exact AdapterManifest")
    snapshot = _contract._validate_manifest_shape(value)
    tree = {
        "coverage_ledger_sha256": snapshot.coverage_ledger_sha256,
        "descriptor_sha256": snapshot.descriptor_sha256,
        "evaluation_labels_sha256": snapshot.evaluation_labels_sha256,
        "fitted_state_sha256": snapshot.fitted_state_sha256,
        "native_observation_sha256": snapshot.native_observation_sha256,
        "partition": {
            "group_id": snapshot.partition.group_id,
            "sample_id": snapshot.partition.sample_id,
            "split": snapshot.partition.split,
        },
        "private_provenance_sha256": snapshot.private_provenance_sha256,
        "schema_sha256": snapshot.schema_sha256,
        "schema_version": snapshot.schema_version,
        "semantic_reconstruction_sha256": (
            snapshot.semantic_reconstruction_sha256
        ),
        "source_sha256": snapshot.source_sha256,
        "source_size_bytes": snapshot.source_size_bytes,
        "split_manifest_sha256": snapshot.split_manifest_sha256,
        "static_context_sha256": snapshot.static_context_sha256,
    }
    return _new_canonical_payload(
        tree,
        domain=_contract.SAMPLE_MANIFEST_DIGEST_DOMAIN,
        expected_phase_c_sha256=snapshot.sample_root_sha256,
    )


def _detached_configuration_tree(value: EventConfiguration) -> dict:
    snapshot = _evidence.snapshot_bounded_native_configuration(value)
    detached = _contract.rebuild_detached_native_configuration(snapshot)
    observed = detached.observed
    if observed is None:  # pragma: no cover - EventConfiguration invariant
        raise PublicationPayloadError("native configuration has no observation")
    return {
        "occurrences": [
            {
                "event": {
                    "event_time": _contract._float_hex(
                        event.event_time, name="event time"
                    ),
                    "event_type": event.event_type,
                    "marks": {
                        name: [
                            _contract._float_hex(item, name="mark value")
                            for item in vector
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
            for event, observation in zip(detached.events, observed.events)
        ],
        "observation_pattern": {
            "cardinality_observed": observed.cardinality_observed,
        },
        "schema": _schema_tree(detached.schema),
    }


def detached_native_observation_payload(
    value: EventConfiguration,
) -> CanonicalPayloadV1:
    if type(value) is not EventConfiguration:
        raise TypeError("configuration must be an exact EventConfiguration")
    return _new_canonical_payload(
        _detached_configuration_tree(value),
        domain=_contract.NATIVE_OBSERVATION_DIGEST_DOMAIN,
        expected_phase_c_sha256=_contract.native_observation_digest(value),
    )


def _event_id_tree(value: object) -> dict:
    if value is None:
        return {"kind": "none"}
    if type(value) is str:
        _contract._validated_private_text(value, name="event_id")
        return {"kind": "text", "value": value}
    if type(value) is not tuple:
        raise TypeError("event_id must be None, an exact string, or an exact tuple")
    if not value or len(value) > _evidence.MAXIMUM_EVENT_ID_TUPLE_ARITY:
        raise PublicationPayloadError("event_id tuple is outside its arity bound")
    components = []
    for item in value:
        if type(item) is str:
            _contract._validated_private_text(item, name="event_id component")
            components.append({"kind": "text", "value": item})
        elif type(item) is int:
            if abs(item) > _evidence.MAXIMUM_EVENT_ID_INTEGER_ABSOLUTE_VALUE:
                raise PublicationPayloadError(
                    "event_id integer component exceeds its bound"
                )
            components.append({"kind": "integer", "value": item})
        else:
            raise TypeError(
                "event_id tuple components must be exact strings or integers"
            )
    return {"components": components, "kind": "tuple"}


def _event_id_sort_key(value: object) -> tuple:
    """Return a total private ordering key without stringifying an ID."""

    if value is None:
        return (0,)
    if type(value) is str:
        _contract._validated_private_text(value, name="event_id")
        return (1, value)
    if type(value) is not tuple:
        raise TypeError("event_id must be None, an exact string, or an exact tuple")
    if not value or len(value) > _evidence.MAXIMUM_EVENT_ID_TUPLE_ARITY:
        raise PublicationPayloadError("event_id tuple is outside its arity bound")
    components = []
    for item in value:
        if type(item) is int:
            if abs(item) > _evidence.MAXIMUM_EVENT_ID_INTEGER_ABSOLUTE_VALUE:
                raise PublicationPayloadError(
                    "event_id integer component exceeds its bound"
                )
            components.append((0, item))
        elif type(item) is str:
            _contract._validated_private_text(item, name="event_id component")
            components.append((1, item))
        else:
            raise TypeError(
                "event_id tuple components must be exact strings or integers"
            )
    return (2, tuple(components))


def identity_bearing_native_configuration_payload(
    value: EventConfiguration,
) -> CanonicalPayloadV1:
    """Project the private full configuration with explicitly tagged IDs."""

    if type(value) is not EventConfiguration:
        raise TypeError("configuration must be an exact EventConfiguration")
    snapshot = _evidence.snapshot_bounded_native_configuration(value)
    observed = snapshot.observed
    if observed is None:  # pragma: no cover - EventConfiguration invariant
        raise PublicationPayloadError("native configuration has no observation")
    occurrences = tuple(
        sorted(
            zip(snapshot.events, observed.events),
            key=lambda pair: (
                pair[0].model_key(),
                pair[1].signature_key(),
                _event_id_sort_key(pair[0].event_id),
            ),
        )
    )
    tree = {
        "group_id": snapshot.group_id,
        "occurrences": [
            {
                "event": {
                    "event_id": _event_id_tree(event.event_id),
                    "event_time": _contract._float_hex(
                        event.event_time, name="event time"
                    ),
                    "event_type": event.event_type,
                    "marks": {
                        name: [
                            _contract._float_hex(item, name="mark value")
                            for item in vector
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
            for event, observation in occurrences
        ],
        "observation_pattern": {
            "cardinality_observed": observed.cardinality_observed,
        },
        "sample_id": snapshot.sample_id,
        "schema": _schema_tree(snapshot.schema),
    }
    return _new_canonical_payload(
        tree,
        domain=PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN,
    )


class _Base64Budget:
    def __init__(self, values: tuple) -> None:
        if type(values) is not tuple:
            raise TypeError("base64 preflight values must be an exact tuple")
        encoded_bytes = 0
        for value in values:
            if type(value) is not bytes:
                raise TypeError(
                    "embedded raw payload must be exact immutable bytes"
                )
            if len(value) > _evidence.MAXIMUM_SINGLE_PAYLOAD_BYTES:
                raise PublicationPayloadError(
                    "embedded raw payload exceeds its ceiling"
                )
            encoded_bytes += _encoded_base64_length(len(value))
            if encoded_bytes > MAXIMUM_PRIVATE_ARTIFACT_BYTES:
                raise PublicationPayloadError(
                    "base64 expansion exceeds the private-artifact ceiling"
                )
        self.encoded_bytes = 0

    def raw(self, value: bytes) -> dict:
        if type(value) is not bytes:
            raise TypeError("embedded raw payload must be exact immutable bytes")
        if len(value) > _evidence.MAXIMUM_SINGLE_PAYLOAD_BYTES:
            raise PublicationPayloadError("embedded raw payload exceeds its ceiling")
        self.encoded_bytes += _encoded_base64_length(len(value))
        if self.encoded_bytes > MAXIMUM_PRIVATE_ARTIFACT_BYTES:
            raise PublicationPayloadError(
                "base64 expansion exceeds the private-artifact ceiling"
            )
        return raw_byte_object(
            _new_raw_byte_object(
                value,
                maximum_bytes=_evidence.MAXIMUM_SINGLE_PAYLOAD_BYTES,
            )
        )


def source_inventory_payload(value: SourceInventory) -> CanonicalPayloadV1:
    if type(value) is not SourceInventory:
        raise TypeError("inventory must be an exact SourceInventory")
    snapshot = _evidence._snapshot_inventory(value)
    budget = _Base64Budget(
        tuple(item.canonical_item_bytes for item in snapshot.items)
    )
    tree = {
        "item_format_id": snapshot.item_format_id,
        "items": [
            {
                "canonical_item": budget.raw(item.canonical_item_bytes),
                "item_key": item.item_key,
                "source_item_sha256": _evidence.source_inventory_item_digest(
                    item, item_format_id=snapshot.item_format_id
                ),
            }
            for item in snapshot.items
        ],
        "policy_sha256": snapshot.policy_sha256,
        "source_sha256": snapshot.source_sha256,
        "source_size_bytes": snapshot.source_size_bytes,
    }
    return _new_canonical_payload(
        tree,
        domain=PRIVATE_SOURCE_INVENTORY_DIGEST_DOMAIN,
    )


def coverage_ledger_payload(value: SourceCoverageLedger) -> CanonicalPayloadV1:
    if type(value) is not SourceCoverageLedger:
        raise TypeError("coverage must be an exact SourceCoverageLedger")
    snapshot = _evidence._snapshot_coverage(value)
    tree = {
        "entries": [
            {
                "disposition": item.disposition.value,
                "exclusion_reason_code": item.exclusion_reason_code,
                "item_key": item.item_key,
                "secondary_tags": list(item.secondary_tags),
                "target_key": item.target_key,
            }
            for item in snapshot.entries
        ],
        "policy_sha256": snapshot.policy_sha256,
        "source_inventory_sha256": snapshot.source_inventory_sha256,
        "source_sha256": snapshot.source_sha256,
        "source_size_bytes": snapshot.source_size_bytes,
    }
    result = _new_canonical_payload(
        tree,
        domain=PRIVATE_COVERAGE_LEDGER_DIGEST_DOMAIN,
    )
    phase_c_digest = domain_separated_sha256(
        _contract.COVERAGE_LEDGER_DIGEST_DOMAIN,
        result.canonical_json_bytes,
    )
    expected = _evidence.source_coverage_ledger_digest(snapshot)
    if snapshot.entries and phase_c_digest != expected:
        raise PublicationPayloadError(
            "coverage projection disagrees with its Phase-C commitment"
        )
    return result


def static_context_payload(value: StaticContext) -> CanonicalPayloadV1:
    if type(value) is not StaticContext:
        raise TypeError("static context must be an exact StaticContext")
    snapshot = _evidence._snapshot_static_context(value)
    budget = _Base64Budget(
        tuple(item.canonical_payload_bytes for item in snapshot.entries)
    )
    return _new_canonical_payload(
        {
            "entries": [
                {
                    "canonical_payload": budget.raw(
                        item.canonical_payload_bytes
                    ),
                    "entry_key": item.entry_key,
                }
                for item in snapshot.entries
            ],
            "format_id": snapshot.format_id,
            "policy_sha256": snapshot.policy_sha256,
            "source_sha256": snapshot.source_sha256,
        },
        domain=PRIVATE_STATIC_CONTEXT_DIGEST_DOMAIN,
    )


def evaluation_labels_payload(value: EvaluationLabels) -> CanonicalPayloadV1:
    if type(value) is not EvaluationLabels:
        raise TypeError("evaluation labels must be exact EvaluationLabels")
    snapshot = _evidence._snapshot_evaluation_labels(value)
    budget = _Base64Budget(
        tuple(item.canonical_payload_bytes for item in snapshot.entries)
    )
    return _new_canonical_payload(
        {
            "entries": [
                {
                    "canonical_payload": budget.raw(
                        item.canonical_payload_bytes
                    ),
                    "entry_key": item.entry_key,
                }
                for item in snapshot.entries
            ],
            "format_id": snapshot.format_id,
            "policy_sha256": snapshot.policy_sha256,
            "source_sha256": snapshot.source_sha256,
        },
        domain=PRIVATE_EVALUATION_LABELS_DIGEST_DOMAIN,
    )


def private_provenance_payload(value: PrivateProvenance) -> CanonicalPayloadV1:
    if type(value) is not PrivateProvenance:
        raise TypeError("provenance must be an exact PrivateProvenance")
    snapshot = _evidence._snapshot_private_provenance(value)
    budget = _Base64Budget(
        tuple(item.private_payload_bytes for item in snapshot.entries)
    )
    return _new_canonical_payload(
        {
            "entries": [
                {
                    "field_statuses": [
                        {
                            "field_name": status.field_name,
                            "reason_code": status.reason_code,
                            "status": status.status.value,
                        }
                        for status in item.field_statuses
                    ],
                    "native_occurrence_sha256": item.native_occurrence_sha256,
                    "private_format_id": item.private_format_id,
                    "private_payload": budget.raw(item.private_payload_bytes),
                    "provenance_key": item.provenance_key,
                    "source_item_keys": list(item.source_item_keys),
                }
                for item in snapshot.entries
            ],
            "native_observation_sha256": snapshot.native_observation_sha256,
            "policy_sha256": snapshot.policy_sha256,
            "source_sha256": snapshot.source_sha256,
        },
        domain=PRIVATE_PROVENANCE_PAYLOAD_DIGEST_DOMAIN,
    )


def fitted_state_payload(
    value: Optional[FittedAdapterState],
) -> CanonicalPayloadV1:
    if value is None:
        result = _new_canonical_payload(
            {"kind": "no_fit"},
            domain=PRIVATE_FITTED_STATE_DIGEST_DOMAIN,
        )
        phase_c = domain_separated_sha256(
            _contract.FITTED_STATE_DIGEST_DOMAIN,
            result.canonical_json_bytes,
        )
        if phase_c != _contract.NO_FITTED_STATE_SHA256:
            raise PublicationPayloadError("no-fit sentinel projection mismatch")
        return result
    if type(value) is not FittedAdapterState:
        raise TypeError("fitted state must be None or an exact FittedAdapterState")
    snapshot = _evidence._snapshot_fitted_state(value)
    budget = _Base64Budget(
        (snapshot.fit_configuration_bytes, snapshot.parameter_bytes)
    )
    return _new_canonical_payload(
        {
            "adapter_id": snapshot.adapter_id,
            "adapter_version": snapshot.adapter_version,
            "contract_version": snapshot.contract_version,
            "descriptor_sha256": snapshot.descriptor_sha256,
            "fit_configuration": {
                "format_id": snapshot.fit_configuration_format_id,
                "payload": budget.raw(snapshot.fit_configuration_bytes),
            },
            "fitted_parameters": {
                "format_id": snapshot.parameter_format_id,
                "payload": budget.raw(snapshot.parameter_bytes),
            },
            "policy_sha256": snapshot.policy_sha256,
            "schema_sha256": snapshot.schema_sha256,
            "split_manifest_sha256": snapshot.split_manifest_sha256,
            "training_group_set_sha256": snapshot.training_group_set_sha256,
            "unseen_value_policy_id": snapshot.unseen_value_policy_id,
        },
        domain=PRIVATE_FITTED_STATE_DIGEST_DOMAIN,
    )


def semantic_reconstruction_payload(
    value: SemanticReconstruction,
) -> CanonicalPayloadV1:
    if type(value) is not SemanticReconstruction:
        raise TypeError("reconstruction must be an exact SemanticReconstruction")
    snapshot = _evidence._snapshot_reconstruction(value)
    budget = _Base64Budget((snapshot.canonical_payload_bytes,))
    return _new_canonical_payload(
        {
            "canonical_payload": budget.raw(snapshot.canonical_payload_bytes),
            "policy_sha256": snapshot.policy_sha256,
            "record_count": snapshot.record_count,
            "schema_sha256": snapshot.schema_sha256,
            "semantic_format_id": snapshot.semantic_format_id,
            "source_sha256": snapshot.source_sha256,
        },
        domain=PRIVATE_SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN,
    )


RawReconstructionPayloadV1 = Union[CanonicalPayloadV1, RawByteObjectV1]


def raw_reconstruction_payload(
    descriptor: AdapterDescriptor,
    complete: CompleteAdaptedEventSample,
) -> RawReconstructionPayloadV1:
    """Project raw reconstruction solely from its typed capability contract."""

    if type(descriptor) is not AdapterDescriptor:
        raise TypeError("descriptor must be an exact AdapterDescriptor")
    if type(complete) is not CompleteAdaptedEventSample:
        raise TypeError("complete must be an exact CompleteAdaptedEventSample")
    descriptor_snapshot = _contract._snapshot_descriptor(descriptor)
    complete_snapshot = _evidence._snapshot_complete(complete)
    advertised = descriptor_snapshot.capabilities.raw_byte_reconstruction
    raw = complete_snapshot.raw_reconstruction_bytes
    if advertised:
        if raw is None:
            raise PublicationPayloadError(
                "advertised raw reconstruction is absent"
            )
        return _new_raw_byte_object(
            raw,
            maximum_bytes=_evidence.MAXIMUM_SOURCE_BYTES,
        )
    if raw is not None:
        raise PublicationPayloadError(
            "unadvertised raw reconstruction carries bytes"
        )
    return _new_canonical_payload(
        {"kind": "NOT_ADVERTISED"},
        domain=RAW_RECONSTRUCTION_ABSENCE_DIGEST_DOMAIN,
    )


def raw_reconstruction_commitment_sha256(
    descriptor: AdapterDescriptor,
    complete: CompleteAdaptedEventSample,
) -> str:
    payload = raw_reconstruction_payload(descriptor, complete)
    if type(payload) is CanonicalPayloadV1:
        return payload.payload_sha256
    return domain_separated_sha256(
        RAW_RECONSTRUCTION_BYTES_DIGEST_DOMAIN,
        payload.bytes_value,
    )


def complete_sample_commitment_payload(
    descriptor: AdapterDescriptor,
    complete: CompleteAdaptedEventSample,
) -> CanonicalPayloadV1:
    if type(descriptor) is not AdapterDescriptor:
        raise TypeError("descriptor must be an exact AdapterDescriptor")
    if type(complete) is not CompleteAdaptedEventSample:
        raise TypeError("complete must be an exact CompleteAdaptedEventSample")
    descriptor_snapshot = _contract._snapshot_descriptor(descriptor)
    snapshot = _evidence._snapshot_complete(complete)
    manifest = snapshot.sample.manifest
    if descriptor_snapshot.descriptor_sha256 != manifest.descriptor_sha256:
        raise PublicationPayloadError("descriptor and manifest disagree")
    return _new_canonical_payload(
        {
            "adapter_manifest_sha256": manifest.sample_root_sha256,
            "coverage_ledger_sha256": _evidence.source_coverage_ledger_digest(
                snapshot.coverage
            ),
            "evaluation_labels_sha256": _evidence.evaluation_labels_digest(
                snapshot.evaluation_labels
            ),
            "fitted_state_sha256": (
                _contract.NO_FITTED_STATE_SHA256
                if snapshot.fitted_state is None
                else _evidence.fitted_adapter_state_digest(
                    snapshot.fitted_state
                )
            ),
            "native_observation_sha256": _contract.native_observation_digest(
                snapshot.sample.configuration
            ),
            "private_provenance_sha256": _evidence.private_provenance_digest(
                snapshot.provenance
            ),
            "raw_reconstruction_sha256": (
                raw_reconstruction_commitment_sha256(
                    descriptor_snapshot, snapshot
                )
            ),
            "semantic_reconstruction_sha256": (
                _evidence.semantic_reconstruction_digest(snapshot.reconstruction)
            ),
            "source_inventory_sha256": _evidence.source_inventory_digest(
                snapshot.inventory
            ),
            "static_context_sha256": _evidence.static_context_digest(
                snapshot.static_context
            ),
        },
        domain=COMPLETE_SAMPLE_DIGEST_DOMAIN,
    )


def expected_evidence_payload(
    value: ExpectedAdapterEvidence,
) -> CanonicalPayloadV1:
    if type(value) is not ExpectedAdapterEvidence:
        raise TypeError("expected evidence must be exact ExpectedAdapterEvidence")
    snapshot = _evidence._snapshot_expected_evidence(value)
    tree = {
        "coverage": {
            "coverage_ledger_sha256": _evidence.source_coverage_ledger_digest(
                snapshot.coverage
            ),
            "policy_sha256": snapshot.coverage.policy_sha256,
            "source_inventory_sha256": snapshot.coverage.source_inventory_sha256,
            "source_sha256": snapshot.coverage.source_sha256,
            "source_size_bytes": snapshot.coverage.source_size_bytes,
        },
        "evaluation_labels": {
            "evaluation_labels_sha256": _evidence.evaluation_labels_digest(
                snapshot.evaluation_labels
            ),
            "format_id": snapshot.evaluation_labels.format_id,
            "policy_sha256": snapshot.evaluation_labels.policy_sha256,
            "source_sha256": snapshot.evaluation_labels.source_sha256,
        },
        "fitted_state_sha256": (
            _contract.NO_FITTED_STATE_SHA256
            if snapshot.fitted_state is None
            else _evidence.fitted_adapter_state_digest(snapshot.fitted_state)
        ),
        "native_observation_sha256": snapshot.native_observation_sha256,
        "private_provenance": {
            "native_observation_sha256": (
                snapshot.provenance.native_observation_sha256
            ),
            "policy_sha256": snapshot.provenance.policy_sha256,
            "private_provenance_sha256": _evidence.private_provenance_digest(
                snapshot.provenance
            ),
            "source_sha256": snapshot.provenance.source_sha256,
        },
        "semantic_reconstruction_sha256": (
            _evidence.semantic_reconstruction_digest(snapshot.reconstruction)
        ),
        "source_inventory_sha256": _evidence.source_inventory_digest(
            snapshot.inventory
        ),
        "static_context": {
            "format_id": snapshot.static_context.format_id,
            "policy_sha256": snapshot.static_context.policy_sha256,
            "source_sha256": snapshot.static_context.source_sha256,
            "static_context_sha256": _evidence.static_context_digest(
                snapshot.static_context
            ),
        },
    }
    return _new_canonical_payload(
        tree,
        domain=_evidence.EXPECTED_EVIDENCE_DIGEST_DOMAIN,
        expected_phase_c_sha256=_evidence.expected_adapter_evidence_digest(
            snapshot
        ),
    )


def independent_golden_case_payload(value: bytes) -> CanonicalPayloadV1:
    if type(value) is not bytes:
        raise TypeError("golden definition must be exact immutable bytes")
    if not value:
        raise PublicationPayloadError("golden definition must not be empty")
    return _new_canonical_payload(
        {
            "definition": raw_byte_object(
                _new_raw_byte_object(
                    value,
                    maximum_bytes=MAXIMUM_GOLDEN_DEFINITION_BYTES,
                )
            )
        },
        domain=INDEPENDENT_GOLDEN_CASE_DIGEST_DOMAIN,
    )


def hostile_control_receipt_payload(
    value: HostileControlInputV1,
) -> CanonicalPayloadV1:
    if type(value) is not HostileControlInputV1:
        raise TypeError("hostile control must be exact")
    snapshot = HostileControlInputV1(
        control_id=value.control_id,
        status_id=value.status_id,
        error_code=value.error_code,
        input_bytes=value.input_bytes,
        test_node_bytes=value.test_node_bytes,
    )
    return _new_canonical_payload(
        {
            "control_id": snapshot.control_id,
            "error_code": snapshot.error_code,
            "input_sha256": domain_separated_sha256(
                HOSTILE_CONTROL_INPUT_DIGEST_DOMAIN,
                snapshot.input_bytes,
            ),
            "status_id": snapshot.status_id,
            "test_node_sha256": domain_separated_sha256(
                HOSTILE_CONTROL_TEST_NODE_DIGEST_DOMAIN,
                snapshot.test_node_bytes,
            ),
        },
        domain=HOSTILE_CONTROL_RECEIPT_DIGEST_DOMAIN,
    )


def public_identifier_registry_payload(
    value: PublicIdentifierRegistryV1,
) -> CanonicalPayloadV1:
    if type(value) is not PublicIdentifierRegistryV1:
        raise TypeError("public identifier registry must be exact")
    if (
        type(value.adapter_identities) is not tuple
        or not value.adapter_identities
        or len(value.adapter_identities)
        > MAXIMUM_REGISTRY_VALUES_PER_CATEGORY
    ):
        raise PublicationPayloadError(
            "adapter identities are outside their shallow bound"
        )
    constructor_values = {}
    for name in PublicIdentifierRegistryV1.__dataclass_fields__:
        if name == "adapter_identities":
            constructor_values[name] = tuple(
                PublicAdapterIdentityV1(
                    item.adapter_id,
                    item.adapter_version,
                )
                for item in value.adapter_identities
            )
        else:
            constructor_values[name] = getattr(value, name)
    snapshot = PublicIdentifierRegistryV1(**constructor_values)
    tree = {
        name: (
            [
                {
                    "adapter_id": item.adapter_id,
                    "adapter_version": item.adapter_version,
                }
                for item in snapshot.adapter_identities
            ]
            if name == "adapter_identities"
            else list(getattr(snapshot, name))
        )
        for name in PublicIdentifierRegistryV1.__dataclass_fields__
    }
    return _new_canonical_payload(
        tree,
        domain=PUBLIC_ID_REGISTRY_DIGEST_DOMAIN,
    )


def execution_guard_run_manifest_payload(
    value: ExecutionGuardRunManifestV1,
) -> CanonicalPayloadV1:
    if type(value) is not ExecutionGuardRunManifestV1:
        raise TypeError(
            "run manifest must be an exact ExecutionGuardRunManifestV1"
        )
    snapshot = ExecutionGuardRunManifestV1(
        **{
            name: getattr(value, name)
            for name, definition in (
                ExecutionGuardRunManifestV1.__dataclass_fields__.items()
            )
            if definition.init
        }
    )
    return _new_canonical_payload(
        {
            "address_space_limit_bytes": snapshot.address_space_limit_bytes,
            "address_space_limit_method_id": (
                snapshot.address_space_limit_method_id
            ),
            "allowed_execution_status_ids": list(
                snapshot.allowed_execution_status_ids
            ),
            "argv_sha256": snapshot.argv_sha256,
            "artifact_type": snapshot.artifact_type,
            "clock_method_id": snapshot.clock_method_id,
            "cwd_launch_method_id": snapshot.cwd_launch_method_id,
            "decision_eligible_required": (
                snapshot.decision_eligible_required
            ),
            "dependency_lock_sha256": snapshot.dependency_lock_sha256,
            "environment_manifest_sha256": (
                snapshot.environment_manifest_sha256
            ),
            "environment_sha256": snapshot.environment_sha256,
            "execution_backend_id": snapshot.execution_backend_id,
            "execution_guard_source_sha256": (
                snapshot.execution_guard_source_sha256
            ),
            "filesystem_confinement_id": (
                snapshot.filesystem_confinement_id
            ),
            "format_version": snapshot.format_version,
            "guard_implementation_status_id": (
                snapshot.guard_implementation_status_id
            ),
            "interpreter_executable_sha256": (
                snapshot.interpreter_executable_sha256
            ),
            "managed_process_group_quiescence_required": (
                snapshot.managed_process_group_quiescence_required
            ),
            "output_capture_method_id": snapshot.output_capture_method_id,
            "output_complete_required": snapshot.output_complete_required,
            "output_limit_bytes": snapshot.output_limit_bytes,
            "peak_rss_limit_bytes": snapshot.peak_rss_limit_bytes,
            "peak_rss_method_id": snapshot.peak_rss_method_id,
            "process_containment_id": snapshot.process_containment_id,
            "publication_invocation_input_sha256": (
                snapshot.publication_invocation_input_sha256
            ),
            "publication_profile_input_sha256": (
                snapshot.publication_profile_input_sha256
            ),
            "source_binding_format_id": snapshot.source_binding_format_id,
            "source_tree_manifest_sha256": (
                snapshot.source_tree_manifest_sha256
            ),
            "test_inventory_sha256": snapshot.test_inventory_sha256,
            "wall_time_limit_nanoseconds": (
                snapshot.wall_time_limit_nanoseconds
            ),
            "working_directory_sha256": snapshot.working_directory_sha256,
        },
        domain=EXECUTION_GUARD_RUN_MANIFEST_DIGEST_DOMAIN,
    )


def execution_guard_receipt_payload(
    value: ExecutionReceipt,
) -> CanonicalPayloadV1:
    receipt = validate_execution_receipt(value)
    return _new_canonical_payload(
        {
            "address_space_limit_bytes": receipt.address_space_limit_bytes,
            "address_space_limit_method_id": (
                receipt.address_space_limit_method.value
            ),
            "argv_sha256": receipt.argv_sha256,
            "artifact_type": EXECUTION_GUARD_RECEIPT_DIGEST_DOMAIN,
            "clock_method_id": receipt.clock_method.value,
            "cwd_launch_method_id": receipt.cwd_launch_method.value,
            "decision_eligible": receipt.decision_eligible,
            "elapsed_monotonic_nanoseconds": (
                receipt.elapsed_monotonic_nanoseconds
            ),
            "environment_sha256": receipt.environment_sha256,
            "execution_backend_id": receipt.execution_backend.value,
            "filesystem_confinement_id": (
                receipt.filesystem_confinement_method.value
            ),
            "implementation_status_id": receipt.implementation_status,
            "managed_process_group_quiescent": (
                receipt.managed_process_group_quiescent
            ),
            "measured_peak_rss_bytes": receipt.measured_peak_rss_bytes,
            "output_capture_method_id": receipt.output_capture_method.value,
            "output_limit_bytes": receipt.output_limit_bytes,
            "peak_rss_enforcement_exact": (
                receipt.peak_rss_enforcement_exact
            ),
            "peak_rss_limit_bytes": receipt.peak_rss_limit_bytes,
            "peak_rss_method_id": receipt.peak_rss_method.value,
            "peak_rss_observation_finalized": (
                receipt.peak_rss_observation_finalized
            ),
            "peak_rss_limit_triggered": receipt.peak_rss_limit_triggered,
            "peak_rss_units_id": receipt.peak_rss_units.value,
            "process_containment_id": (
                receipt.process_containment_method.value
            ),
            "source_binding_format_id": receipt.source_binding_format.value,
            "source_sha256": receipt.source_sha256,
            "status_id": receipt.status.value,
            "stderr_complete": receipt.stderr_complete,
            "stderr_sha256": receipt.stderr_sha256,
            "stderr_size_bytes": receipt.stderr_size_bytes,
            "stdout_complete": receipt.stdout_complete,
            "stdout_sha256": receipt.stdout_sha256,
            "stdout_size_bytes": receipt.stdout_size_bytes,
            "terminating_signal": receipt.terminating_signal,
            "wall_time_limit_nanoseconds": (
                receipt.wall_time_limit_nanoseconds
            ),
            "wall_limit_triggered": receipt.wall_limit_triggered,
            "working_directory_sha256": receipt.working_directory_sha256,
            "exit_status": receipt.exit_status,
        },
        domain=EXECUTION_GUARD_RECEIPT_DIGEST_DOMAIN,
    )


def conformance_run_payload(value: ConformanceRun) -> CanonicalPayloadV1:
    if type(value) is not ConformanceRun:
        raise TypeError("run must be an exact ConformanceRun")
    snapshot = ConformanceRun(
        adapter_id=value.adapter_id,
        adapter_version=value.adapter_version,
        descriptor_sha256=value.descriptor_sha256,
        source_sha256=value.source_sha256,
        split_manifest_sha256=value.split_manifest_sha256,
        native_observation_sha256=value.native_observation_sha256,
        sample_root_sha256=value.sample_root_sha256,
        expected_evidence_sha256=value.expected_evidence_sha256,
        plan=value.plan,
        records=value.records,
        capability_control_trace=value.capability_control_trace,
    )
    plan = snapshot.plan
    tree = {
        "adapter_id": snapshot.adapter_id,
        "adapter_version": snapshot.adapter_version,
        "capability_control_trace": list(snapshot.capability_control_trace),
        "descriptor_sha256": snapshot.descriptor_sha256,
        "expected_evidence_sha256": snapshot.expected_evidence_sha256,
        "native_observation_sha256": snapshot.native_observation_sha256,
        "plan": {
            "atomic_grid": plan.atomic_grid.value,
            "coverage": plan.coverage.value,
            "evaluation_labels": plan.evaluation_labels.value,
            "fitted_state": plan.fitted_state.value,
            "multiplicity_mode": plan.multiplicity_mode.value,
            "native": plan.native.value,
            "provenance": plan.provenance.value,
            "raw_reconstruction": plan.raw_reconstruction.value,
            "representation_ids": list(plan.representation_ids),
            "semantic_reconstruction": plan.semantic_reconstruction.value,
            "static_context": plan.static_context.value,
            "time_measure": plan.time_measure.value,
        },
        "records": [
            {
                "check_id": item.check_id,
                "plan_mode": item.plan_mode.value,
                "reason": item.reason,
                "representation_id": item.representation_id,
                "status": item.status.value,
            }
            for item in snapshot.records
        ],
        "sample_root_sha256": snapshot.sample_root_sha256,
        "source_sha256": snapshot.source_sha256,
        "split_manifest_sha256": snapshot.split_manifest_sha256,
    }
    return _new_canonical_payload(
        tree,
        domain=CONFORMANCE_RUN_DIGEST_DOMAIN,
    )


__all__ = [
    "COMPLETE_SAMPLE_DIGEST_DOMAIN",
    "CONFORMANCE_RUN_DIGEST_DOMAIN",
    "EXECUTION_GUARD_RECEIPT_DIGEST_DOMAIN",
    "EXECUTION_GUARD_RUN_MANIFEST_DIGEST_DOMAIN",
    "HOSTILE_CONTROL_INPUT_DIGEST_DOMAIN",
    "HOSTILE_CONTROL_RECEIPT_DIGEST_DOMAIN",
    "HOSTILE_CONTROL_TEST_NODE_DIGEST_DOMAIN",
    "INDEPENDENT_GOLDEN_CASE_DIGEST_DOMAIN",
    "MAXIMUM_CANONICAL_LEAF_BYTES",
    "PRIVATE_COVERAGE_LEDGER_DIGEST_DOMAIN",
    "PRIVATE_EVALUATION_LABELS_DIGEST_DOMAIN",
    "PRIVATE_FITTED_STATE_DIGEST_DOMAIN",
    "PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN",
    "PRIVATE_PARTITION_DIGEST_DOMAIN",
    "PRIVATE_PROVENANCE_PAYLOAD_DIGEST_DOMAIN",
    "PRIVATE_SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN",
    "PRIVATE_SOURCE_INVENTORY_DIGEST_DOMAIN",
    "PRIVATE_STATIC_CONTEXT_DIGEST_DOMAIN",
    "PUBLICATION_PAYLOAD_IMPLEMENTATION_STATUS",
    "PUBLIC_ID_REGISTRY_DIGEST_DOMAIN",
    "PublicationPayloadError",
    "RAW_RECONSTRUCTION_ABSENCE_DIGEST_DOMAIN",
    "RAW_RECONSTRUCTION_BYTES_DIGEST_DOMAIN",
    "adapter_descriptor_payload",
    "adapter_manifest_payload",
    "complete_sample_commitment_payload",
    "conformance_run_payload",
    "coverage_ledger_payload",
    "detached_native_observation_payload",
    "evaluation_labels_payload",
    "expected_evidence_payload",
    "execution_guard_receipt_payload",
    "execution_guard_run_manifest_payload",
    "fitted_state_payload",
    "hostile_control_receipt_payload",
    "identity_bearing_native_configuration_payload",
    "independent_golden_case_payload",
    "partition_payload",
    "private_provenance_payload",
    "public_identifier_registry_payload",
    "raw_reconstruction_commitment_sha256",
    "raw_reconstruction_payload",
    "semantic_reconstruction_payload",
    "source_bytes_payload",
    "source_inventory_payload",
    "split_manifest_payload",
    "static_context_payload",
]
