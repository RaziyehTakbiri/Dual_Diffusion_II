"""Child-safe codec for one supplied complete adapted-evidence sample.

This module contains only deterministic snapshots, neutral contract/evidence
relations, private payload projections, canonical JSON, and digest framing.
It accepts no adapter object and performs no callback, comparison, decision,
filesystem access, import loading, or process control.  The resulting private
bundle is byte-identical to the frozen ``adapted-evidence-bundle.v1`` format.

The codec proves neither execution isolation nor semantic correctness.  A
trusted parent must still validate arbitrary returned bytes independently.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Optional

from . import adapter_contract as _contract
from . import adapter_evidence as _evidence
from .adapter_output_blind_case_input import (
    ActualAdapterCaseInputV1,
    PreparedOutputBlindCaseInputV1,
    validate_prepared_output_blind_case_input_v1,
)


CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_ARTIFACT_TYPE = (
    "heterodiff.adapter.adapted-evidence-bundle.v1"
)
CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_DIGEST_DOMAIN = (
    CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_ARTIFACT_TYPE
)
MAXIMUM_CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_BYTES = 32 * 1024 * 1024
MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES = 16 * 1024 * 1024
MAXIMUM_CHILD_SAFE_CANONICAL_DEPTH = 32
MAXIMUM_CHILD_SAFE_CANONICAL_NODES = 200_000
MAXIMUM_CHILD_SAFE_CANONICAL_STRING_BYTES = 512 * 1024

_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1
_COMPLETE_SAMPLE_DIGEST_DOMAIN = (
    "heterodiff.adapter.complete-sample-publication.v1"
)
_RAW_RECONSTRUCTION_ABSENCE_DIGEST_DOMAIN = (
    "heterodiff.adapter.raw-reconstruction-absence.v1"
)
_RAW_RECONSTRUCTION_BYTES_DIGEST_DOMAIN = (
    "heterodiff.adapter.raw-reconstruction-bytes.v1"
)
_PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-native-configuration.v1"
)
_PRIVATE_SOURCE_INVENTORY_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-source-inventory.v1"
)
_PRIVATE_COVERAGE_LEDGER_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-coverage-ledger.v1"
)
_PRIVATE_STATIC_CONTEXT_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-static-context.v1"
)
_PRIVATE_EVALUATION_LABELS_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-evaluation-labels.v1"
)
_PRIVATE_PROVENANCE_PAYLOAD_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-provenance-payload.v1"
)
_PRIVATE_FITTED_STATE_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-fitted-state.v1"
)
_PRIVATE_SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-semantic-reconstruction.v1"
)


class ChildBundleCodecCode(str, Enum):
    """Closed, nonreflecting failures from the pure child codec."""

    INPUT_TYPE = "CHILD_BUNDLE_CODEC_INPUT_TYPE"
    INPUT_TRANSPORT = "CHILD_BUNDLE_CODEC_INPUT_TRANSPORT"
    BINDING = "CHILD_BUNDLE_CODEC_BINDING"
    PROJECTION = "CHILD_BUNDLE_CODEC_PROJECTION"
    RESOURCE_LIMIT = "CHILD_BUNDLE_CODEC_RESOURCE_LIMIT"
    INTERNAL = "CHILD_BUNDLE_CODEC_INTERNAL"


_ERROR_MESSAGES = MappingProxyType(
    {
        ChildBundleCodecCode.INPUT_TYPE: (
            "child bundle codec input has an invalid exact type"
        ),
        ChildBundleCodecCode.INPUT_TRANSPORT: (
            "child bundle codec case-input transport is inconsistent"
        ),
        ChildBundleCodecCode.BINDING: (
            "child bundle case, descriptor, manifest, or evidence disagree"
        ),
        ChildBundleCodecCode.PROJECTION: (
            "child bundle evidence projection did not complete"
        ),
        ChildBundleCodecCode.RESOURCE_LIMIT: (
            "child bundle exceeds a frozen resource ceiling"
        ),
        ChildBundleCodecCode.INTERNAL: (
            "child bundle codec failed internally"
        ),
    }
)


class ChildBundleCodecError(ValueError):
    """One coded child-codec failure with no reflected input text."""

    def __init__(self, code: ChildBundleCodecCode) -> None:
        if type(code) is not ChildBundleCodecCode:
            raise TypeError("child bundle codec code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: ChildBundleCodecCode) -> None:
    raise ChildBundleCodecError(code) from None


def _canonical_string_encoded_size(value: str) -> tuple:
    if type(value) is not str:
        raise TypeError("canonical string must be exact")
    json_size = 2
    utf8_size = 0
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise ValueError("canonical string is not valid Unicode")
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
    if (
        type(maximum_encoded_bytes) is not int
        or maximum_encoded_bytes < 0
    ):
        raise TypeError("canonical byte ceiling must be nonnegative")
    nodes = 0
    encoded_size = 0
    stack = [(value, 0)]

    def add_size(amount: int) -> None:
        nonlocal encoded_size
        encoded_size += amount
        if encoded_size > maximum_encoded_bytes:
            raise OverflowError("canonical bytes exceed their ceiling")

    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAXIMUM_CHILD_SAFE_CANONICAL_NODES:
            raise OverflowError("canonical tree has too many nodes")
        if depth > MAXIMUM_CHILD_SAFE_CANONICAL_DEPTH:
            raise OverflowError("canonical tree is too deep")
        if current is None:
            add_size(4)
        elif type(current) is bool:
            add_size(4 if current else 5)
        elif type(current) is int:
            if abs(current) > _MAXIMUM_SAFE_INTEGER:
                raise ValueError("canonical integer is outside its range")
            add_size(len(str(current)))
        elif type(current) is str:
            json_size, utf8_size = _canonical_string_encoded_size(current)
            if utf8_size > MAXIMUM_CHILD_SAFE_CANONICAL_STRING_BYTES:
                raise OverflowError("canonical string exceeds its ceiling")
            add_size(json_size)
        elif type(current) is list:
            add_size(2 + max(0, len(current) - 1))
            stack.extend(
                (item, depth + 1) for item in reversed(current)
            )
        elif type(current) is dict:
            add_size(2 + max(0, len(current) - 1) + len(current))
            for key, item in current.items():
                if type(key) is not str:
                    raise TypeError("canonical object keys must be exact text")
                key_size, key_utf8_size = _canonical_string_encoded_size(key)
                if (
                    key_utf8_size
                    > MAXIMUM_CHILD_SAFE_CANONICAL_STRING_BYTES
                ):
                    raise OverflowError(
                        "canonical object key exceeds its ceiling"
                    )
                add_size(key_size)
                stack.append((item, depth + 1))
        else:
            raise TypeError("value is outside the canonical JSON profile")
    return encoded_size


def _canonical_tree_bytes(
    value: object,
    *,
    maximum_encoded_bytes: int,
) -> bytes:
    expected_size = _preflight_canonical_tree(
        value,
        maximum_encoded_bytes=maximum_encoded_bytes,
    )
    try:
        result = json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        raise TypeError("value is not canonical JSON") from None
    if len(result) != expected_size:
        raise RuntimeError("canonical preflight and encoder disagree")
    return result


def _domain_sha256(
    domain: str,
    payload: bytes,
    *,
    maximum_bytes: int,
) -> str:
    if type(domain) is not str or type(payload) is not bytes:
        raise TypeError("digest inputs must have exact types")
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except UnicodeError:
        raise TypeError("digest domain must be ASCII") from None
    if not domain_bytes or len(domain_bytes) > 256 or b"\x00" in domain_bytes:
        raise ValueError("digest domain is outside its bound")
    if type(maximum_bytes) is not int or maximum_bytes < 0:
        raise TypeError("digest ceiling must be nonnegative")
    if len(payload) > maximum_bytes:
        raise OverflowError("digest payload exceeds its ceiling")
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def child_safe_adapted_evidence_bundle_sha256(bundle_bytes: bytes) -> str:
    """Return the frozen bundle-domain digest of exact bounded bytes."""

    if type(bundle_bytes) is not bytes:
        raise TypeError("bundle_bytes must be exact immutable bytes")
    if (
        not bundle_bytes
        or len(bundle_bytes)
        > MAXIMUM_CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_BYTES
    ):
        raise ValueError("bundle_bytes are outside the child bundle bound")
    return _domain_sha256(
        CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_DIGEST_DOMAIN,
        bundle_bytes,
        maximum_bytes=MAXIMUM_CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_BYTES,
    )


@dataclass(frozen=True)
class ChildSafeAdaptedEvidenceBundleV1:
    """Exact immutable private-bundle transport returned by the codec."""

    bundle_bytes: bytes
    bundle_byte_count: int
    bundle_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not ChildSafeAdaptedEvidenceBundleV1:
            raise TypeError("child-safe bundle result must be exact")
        if type(self.bundle_bytes) is not bytes or not self.bundle_bytes:
            raise TypeError("bundle_bytes must be nonempty exact bytes")
        if type(self.bundle_byte_count) is not int:
            raise TypeError("bundle_byte_count must be an exact integer")
        if (
            self.bundle_byte_count != len(self.bundle_bytes)
            or self.bundle_byte_count
            > MAXIMUM_CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_BYTES
        ):
            raise ValueError("bundle_byte_count does not match bounded bytes")
        if type(self.bundle_sha256) is not str:
            raise TypeError("bundle_sha256 must be exact text")
        if self.bundle_sha256 != child_safe_adapted_evidence_bundle_sha256(
            self.bundle_bytes
        ):
            raise ValueError("bundle_sha256 does not match exact bundle bytes")


def _canonical_wrapper(
    tree: dict,
    *,
    domain: str,
    expected_sha256: Optional[str] = None,
) -> dict:
    if type(tree) is not dict:
        raise TypeError("canonical wrapper tree must be an exact object")
    payload_bytes = _canonical_tree_bytes(
        tree,
        maximum_encoded_bytes=MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES,
    )
    payload_sha256 = _domain_sha256(
        domain,
        payload_bytes,
        maximum_bytes=MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES,
    )
    if expected_sha256 is not None:
        _contract._validated_sha256(
            expected_sha256,
            name="expected payload digest",
        )
        if payload_sha256 != expected_sha256:
            raise ValueError("projected payload disagrees with its commitment")
    return {
        "payload": tree,
        "payload_byte_count": len(payload_bytes),
        "payload_sha256": payload_sha256,
    }


def _raw_object(value: bytes, *, maximum_bytes: int) -> dict:
    if type(value) is not bytes:
        raise TypeError("raw payload must be exact immutable bytes")
    if type(maximum_bytes) is not int or maximum_bytes < 0:
        raise TypeError("raw payload ceiling must be nonnegative")
    if len(value) > maximum_bytes:
        raise OverflowError("raw payload exceeds its ceiling")
    encoded = base64.b64encode(value)
    if len(encoded) > MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES:
        raise OverflowError("base64 payload exceeds its ceiling")
    return {
        "byte_count": len(value),
        "bytes_b64": encoded.decode("ascii"),
        "sha256": hashlib.sha256(value).hexdigest(),
    }


class _Base64Budget:
    def __init__(self, values: tuple) -> None:
        if type(values) is not tuple:
            raise TypeError("base64 preflight values must be an exact tuple")
        total = 0
        for value in values:
            if type(value) is not bytes:
                raise TypeError("embedded raw payload must be exact bytes")
            if len(value) > _evidence.MAXIMUM_SINGLE_PAYLOAD_BYTES:
                raise OverflowError("embedded raw payload exceeds its ceiling")
            total += 4 * ((len(value) + 2) // 3)
            if total > MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES:
                raise OverflowError("base64 expansion exceeds its ceiling")
        self.encoded_bytes = 0

    def raw(self, value: bytes) -> dict:
        if type(value) is not bytes:
            raise TypeError("embedded raw payload must be exact bytes")
        if len(value) > _evidence.MAXIMUM_SINGLE_PAYLOAD_BYTES:
            raise OverflowError("embedded raw payload exceeds its ceiling")
        self.encoded_bytes += 4 * ((len(value) + 2) // 3)
        if self.encoded_bytes > MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES:
            raise OverflowError("base64 expansion exceeds its ceiling")
        return _raw_object(
            value,
            maximum_bytes=_evidence.MAXIMUM_SINGLE_PAYLOAD_BYTES,
        )


def _descriptor_wrapper(
    descriptor: _contract.AdapterDescriptor,
) -> dict:
    capabilities = descriptor.capabilities
    identity = descriptor.identity
    tree = {
        "capabilities": {
            "evaluation_labels": capabilities.evaluation_labels,
            "fitted_state": capabilities.fitted_state,
            "multiplicity_mode": capabilities.multiplicity_mode.value,
            "private_provenance": capabilities.private_provenance,
            "raw_byte_reconstruction": (
                capabilities.raw_byte_reconstruction
            ),
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
    return _canonical_wrapper(
        tree,
        domain=_contract.DESCRIPTOR_DIGEST_DOMAIN,
        expected_sha256=_contract.adapter_descriptor_digest(descriptor),
    )


def _manifest_wrapper(manifest: _contract.AdapterManifest) -> dict:
    tree = _contract._sample_manifest_payload(manifest)
    if type(tree) is not dict:
        raise TypeError("manifest projection must be an exact object")
    return _canonical_wrapper(
        tree,
        domain=_contract.SAMPLE_MANIFEST_DIGEST_DOMAIN,
        expected_sha256=manifest.sample_root_sha256,
    )


def _detached_native_wrapper(
    configuration: object,
) -> dict:
    tree = _contract._native_observation_payload(configuration)
    if type(tree) is not dict:
        raise TypeError("native projection must be an exact object")
    return _canonical_wrapper(
        tree,
        domain=_contract.NATIVE_OBSERVATION_DIGEST_DOMAIN,
        expected_sha256=_contract.native_observation_digest(configuration),
    )


def _event_id_tree(value: object) -> dict:
    if value is None:
        return {"kind": "none"}
    if type(value) is str:
        _contract._validated_private_text(value, name="event_id")
        return {"kind": "text", "value": value}
    if type(value) is not tuple:
        raise TypeError("event_id has an invalid exact type")
    if not value or len(value) > _evidence.MAXIMUM_EVENT_ID_TUPLE_ARITY:
        raise ValueError("event_id tuple is outside its arity bound")
    components = []
    for item in value:
        if type(item) is str:
            _contract._validated_private_text(
                item,
                name="event_id component",
            )
            components.append({"kind": "text", "value": item})
        elif type(item) is int:
            if abs(item) > _evidence.MAXIMUM_EVENT_ID_INTEGER_ABSOLUTE_VALUE:
                raise ValueError("event_id integer exceeds its bound")
            components.append({"kind": "integer", "value": item})
        else:
            raise TypeError("event_id component has an invalid exact type")
    return {"components": components, "kind": "tuple"}


def _event_id_sort_key(value: object) -> tuple:
    if value is None:
        return (0,)
    if type(value) is str:
        _contract._validated_private_text(value, name="event_id")
        return (1, value)
    if type(value) is not tuple:
        raise TypeError("event_id has an invalid exact type")
    if not value or len(value) > _evidence.MAXIMUM_EVENT_ID_TUPLE_ARITY:
        raise ValueError("event_id tuple is outside its arity bound")
    components = []
    for item in value:
        if type(item) is int:
            if abs(item) > _evidence.MAXIMUM_EVENT_ID_INTEGER_ABSOLUTE_VALUE:
                raise ValueError("event_id integer exceeds its bound")
            components.append((0, item))
        elif type(item) is str:
            _contract._validated_private_text(
                item,
                name="event_id component",
            )
            components.append((1, item))
        else:
            raise TypeError("event_id component has an invalid exact type")
    return (2, tuple(components))


def _identity_configuration_wrapper(configuration: object) -> dict:
    snapshot = _evidence.snapshot_bounded_native_configuration(
        configuration
    )
    observed = snapshot.observed
    if observed is None:
        raise ValueError("native configuration has no observation")
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
                        event.event_time,
                        name="event time",
                    ),
                    "event_type": event.event_type,
                    "marks": {
                        name: [
                            _contract._float_hex(
                                item,
                                name="mark value",
                            )
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
        "schema": _contract._schema_payload(snapshot.schema),
    }
    return _canonical_wrapper(
        tree,
        domain=_PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN,
    )


def _inventory_wrapper(value: _evidence.SourceInventory) -> dict:
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
                "source_item_sha256": (
                    _evidence.source_inventory_item_digest(
                        item,
                        item_format_id=snapshot.item_format_id,
                    )
                ),
            }
            for item in snapshot.items
        ],
        "policy_sha256": snapshot.policy_sha256,
        "source_sha256": snapshot.source_sha256,
        "source_size_bytes": snapshot.source_size_bytes,
    }
    return _canonical_wrapper(
        tree,
        domain=_PRIVATE_SOURCE_INVENTORY_DIGEST_DOMAIN,
    )


def _coverage_wrapper(value: _evidence.SourceCoverageLedger) -> dict:
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
    wrapper = _canonical_wrapper(
        tree,
        domain=_PRIVATE_COVERAGE_LEDGER_DIGEST_DOMAIN,
    )
    if snapshot.entries:
        payload_bytes = _canonical_tree_bytes(
            tree,
            maximum_encoded_bytes=MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES,
        )
        if _domain_sha256(
            _contract.COVERAGE_LEDGER_DIGEST_DOMAIN,
            payload_bytes,
            maximum_bytes=MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES,
        ) != _evidence.source_coverage_ledger_digest(snapshot):
            raise ValueError("coverage projection disagrees with commitment")
    return wrapper


def _static_context_wrapper(value: _evidence.StaticContext) -> dict:
    snapshot = _evidence._snapshot_static_context(value)
    budget = _Base64Budget(
        tuple(item.canonical_payload_bytes for item in snapshot.entries)
    )
    tree = {
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
    }
    return _canonical_wrapper(
        tree,
        domain=_PRIVATE_STATIC_CONTEXT_DIGEST_DOMAIN,
    )


def _evaluation_labels_wrapper(
    value: _evidence.EvaluationLabels,
) -> dict:
    snapshot = _evidence._snapshot_evaluation_labels(value)
    budget = _Base64Budget(
        tuple(item.canonical_payload_bytes for item in snapshot.entries)
    )
    tree = {
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
    }
    return _canonical_wrapper(
        tree,
        domain=_PRIVATE_EVALUATION_LABELS_DIGEST_DOMAIN,
    )


def _provenance_wrapper(value: _evidence.PrivateProvenance) -> dict:
    snapshot = _evidence._snapshot_private_provenance(value)
    budget = _Base64Budget(
        tuple(item.private_payload_bytes for item in snapshot.entries)
    )
    tree = {
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
    }
    return _canonical_wrapper(
        tree,
        domain=_PRIVATE_PROVENANCE_PAYLOAD_DIGEST_DOMAIN,
    )


def _fitted_state_wrapper(
    value: Optional[_evidence.FittedAdapterState],
) -> dict:
    if value is None:
        tree = {"kind": "no_fit"}
        payload_bytes = _canonical_tree_bytes(
            tree,
            maximum_encoded_bytes=MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES,
        )
        if _domain_sha256(
            _contract.FITTED_STATE_DIGEST_DOMAIN,
            payload_bytes,
            maximum_bytes=MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES,
        ) != _contract.NO_FITTED_STATE_SHA256:
            raise RuntimeError("no-fit sentinel projection mismatch")
        return _canonical_wrapper(
            tree,
            domain=_PRIVATE_FITTED_STATE_DIGEST_DOMAIN,
        )
    if type(value) is not _evidence.FittedAdapterState:
        raise TypeError("fitted state must be exact or absent")
    snapshot = _evidence._snapshot_fitted_state(value)
    budget = _Base64Budget(
        (snapshot.fit_configuration_bytes, snapshot.parameter_bytes)
    )
    tree = {
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
    }
    return _canonical_wrapper(
        tree,
        domain=_PRIVATE_FITTED_STATE_DIGEST_DOMAIN,
    )


def _semantic_reconstruction_wrapper(
    value: _evidence.SemanticReconstruction,
) -> dict:
    snapshot = _evidence._snapshot_reconstruction(value)
    budget = _Base64Budget((snapshot.canonical_payload_bytes,))
    tree = {
        "canonical_payload": budget.raw(snapshot.canonical_payload_bytes),
        "policy_sha256": snapshot.policy_sha256,
        "record_count": snapshot.record_count,
        "schema_sha256": snapshot.schema_sha256,
        "semantic_format_id": snapshot.semantic_format_id,
        "source_sha256": snapshot.source_sha256,
    }
    return _canonical_wrapper(
        tree,
        domain=_PRIVATE_SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN,
    )


def _raw_reconstruction_member(
    descriptor: _contract.AdapterDescriptor,
    complete: _evidence.CompleteAdaptedEventSample,
) -> dict:
    advertised = descriptor.capabilities.raw_byte_reconstruction
    raw = complete.raw_reconstruction_bytes
    if advertised:
        if raw is None:
            raise ValueError("advertised raw reconstruction is absent")
        return _raw_object(raw, maximum_bytes=_evidence.MAXIMUM_SOURCE_BYTES)
    if raw is not None:
        raise ValueError("unadvertised raw reconstruction carries bytes")
    return _canonical_wrapper(
        {"kind": "NOT_ADVERTISED"},
        domain=_RAW_RECONSTRUCTION_ABSENCE_DIGEST_DOMAIN,
    )


def _raw_reconstruction_commitment_sha256(
    descriptor: _contract.AdapterDescriptor,
    complete: _evidence.CompleteAdaptedEventSample,
) -> str:
    raw = complete.raw_reconstruction_bytes
    if descriptor.capabilities.raw_byte_reconstruction:
        if raw is None:
            raise ValueError("advertised raw reconstruction is absent")
        return _domain_sha256(
            _RAW_RECONSTRUCTION_BYTES_DIGEST_DOMAIN,
            raw,
            maximum_bytes=_evidence.MAXIMUM_SOURCE_BYTES,
        )
    if raw is not None:
        raise ValueError("unadvertised raw reconstruction carries bytes")
    sentinel = _canonical_tree_bytes(
        {"kind": "NOT_ADVERTISED"},
        maximum_encoded_bytes=MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES,
    )
    return _domain_sha256(
        _RAW_RECONSTRUCTION_ABSENCE_DIGEST_DOMAIN,
        sentinel,
        maximum_bytes=MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES,
    )


def _complete_sample_wrapper(
    descriptor: _contract.AdapterDescriptor,
    complete: _evidence.CompleteAdaptedEventSample,
) -> dict:
    manifest = complete.sample.manifest
    if descriptor.descriptor_sha256 != manifest.descriptor_sha256:
        raise ValueError("descriptor and manifest disagree")
    tree = {
        "adapter_manifest_sha256": manifest.sample_root_sha256,
        "coverage_ledger_sha256": (
            _evidence.source_coverage_ledger_digest(complete.coverage)
        ),
        "evaluation_labels_sha256": (
            _evidence.evaluation_labels_digest(complete.evaluation_labels)
        ),
        "fitted_state_sha256": (
            _contract.NO_FITTED_STATE_SHA256
            if complete.fitted_state is None
            else _evidence.fitted_adapter_state_digest(
                complete.fitted_state
            )
        ),
        "native_observation_sha256": (
            _contract.native_observation_digest(
                complete.sample.configuration
            )
        ),
        "private_provenance_sha256": (
            _evidence.private_provenance_digest(complete.provenance)
        ),
        "raw_reconstruction_sha256": (
            _raw_reconstruction_commitment_sha256(descriptor, complete)
        ),
        "semantic_reconstruction_sha256": (
            _evidence.semantic_reconstruction_digest(
                complete.reconstruction
            )
        ),
        "source_inventory_sha256": (
            _evidence.source_inventory_digest(complete.inventory)
        ),
        "static_context_sha256": (
            _evidence.static_context_digest(complete.static_context)
        ),
    }
    return _canonical_wrapper(
        tree,
        domain=_COMPLETE_SAMPLE_DIGEST_DOMAIN,
    )


def _validate_bindings(
    case_input: ActualAdapterCaseInputV1,
    descriptor: _contract.AdapterDescriptor,
    complete: _evidence.CompleteAdaptedEventSample,
) -> None:
    source_bytes = case_input.source_bytes
    partition = case_input.partition
    split_manifest = case_input.split_manifest
    split_snapshot = _evidence.snapshot_bounded_split_manifest(
        split_manifest
    )
    manifest = _contract._validate_manifest_shape(complete.sample.manifest)
    configuration = _evidence.snapshot_bounded_native_configuration(
        complete.sample.configuration
    )
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    descriptor_sha256 = _contract.adapter_descriptor_digest(descriptor)
    split_sha256 = _contract.split_manifest_digest(split_snapshot)
    schema_sha256 = _contract.feature_schema_digest(configuration.schema)
    native_sha256 = _contract.native_observation_digest(configuration)
    capabilities = descriptor.capabilities

    if (
        manifest.partition != partition
        or not split_snapshot.contains_exactly(partition)
        or configuration.sample_id != partition.sample_id
        or configuration.group_id != partition.group_id
    ):
        raise ValueError("partition binding mismatch")
    if (
        manifest.source_size_bytes != len(source_bytes)
        or manifest.source_sha256 != source_sha256
        or manifest.split_manifest_sha256 != split_sha256
        or manifest.descriptor_sha256 != descriptor_sha256
    ):
        raise ValueError("external binding mismatch")
    if (
        manifest.schema_sha256 != schema_sha256
        or manifest.schema_version != configuration.schema.version
        or manifest.native_observation_sha256 != native_sha256
        or capabilities.time_measure is not configuration.schema.time_measure
        or capabilities.multiplicity_mode
        is not configuration.schema.multiplicity_mode
    ):
        raise ValueError("native binding mismatch")

    _evidence._validate_leaf_source_bindings(
        complete,
        source_sha256=source_sha256,
        source_size_bytes=len(source_bytes),
        policy_sha256=descriptor.identity.policy_sha256,
        schema_sha256=schema_sha256,
        native_sha256=native_sha256,
    )
    leaf_bindings = (
        (
            manifest.static_context_sha256,
            _evidence.static_context_digest(complete.static_context),
        ),
        (
            manifest.evaluation_labels_sha256,
            _evidence.evaluation_labels_digest(complete.evaluation_labels),
        ),
        (
            manifest.coverage_ledger_sha256,
            _evidence.source_coverage_ledger_digest(complete.coverage),
        ),
        (
            manifest.private_provenance_sha256,
            _evidence.private_provenance_digest(complete.provenance),
        ),
        (
            manifest.semantic_reconstruction_sha256,
            _evidence.semantic_reconstruction_digest(
                complete.reconstruction
            ),
        ),
        (
            manifest.fitted_state_sha256,
            (
                _contract.NO_FITTED_STATE_SHA256
                if complete.fitted_state is None
                else _evidence.fitted_adapter_state_digest(
                    complete.fitted_state
                )
            ),
        ),
    )
    if any(actual != expected for actual, expected in leaf_bindings):
        raise ValueError("leaf binding mismatch")
    _evidence._validate_capabilities_and_fitted_state(
        capabilities,
        complete,
        descriptor,
        manifest,
        split_snapshot,
    )
    if capabilities.raw_byte_reconstruction:
        if complete.raw_reconstruction_bytes != source_bytes:
            raise ValueError("raw reconstruction mismatch")
    elif complete.raw_reconstruction_bytes is not None:
        raise ValueError("unadvertised raw reconstruction")


def _adapted_members(
    descriptor: _contract.AdapterDescriptor,
    complete: _evidence.CompleteAdaptedEventSample,
) -> dict:
    configuration = complete.sample.configuration
    return {
        "adapter_descriptor": _descriptor_wrapper(descriptor),
        "adapter_manifest": _manifest_wrapper(complete.sample.manifest),
        "complete_sample_commitment": _complete_sample_wrapper(
            descriptor,
            complete,
        ),
        "coverage_ledger": _coverage_wrapper(complete.coverage),
        "detached_native_observation": _detached_native_wrapper(
            configuration
        ),
        "evaluation_labels": _evaluation_labels_wrapper(
            complete.evaluation_labels
        ),
        "fitted_state": _fitted_state_wrapper(complete.fitted_state),
        "identity_bearing_native_configuration": (
            _identity_configuration_wrapper(configuration)
        ),
        "private_provenance": _provenance_wrapper(complete.provenance),
        "raw_byte_reconstruction": _raw_reconstruction_member(
            descriptor,
            complete,
        ),
        "semantic_reconstruction": _semantic_reconstruction_wrapper(
            complete.reconstruction
        ),
        "source_inventory": _inventory_wrapper(complete.inventory),
        "static_context": _static_context_wrapper(complete.static_context),
    }


def build_child_safe_adapted_evidence_bundle(
    prepared_case_input: PreparedOutputBlindCaseInputV1,
    descriptor: _contract.AdapterDescriptor,
    complete: _evidence.CompleteAdaptedEventSample,
) -> ChildSafeAdaptedEvidenceBundleV1:
    """Project one exact supplied complete sample into the private bundle."""

    if (
        type(prepared_case_input) is not PreparedOutputBlindCaseInputV1
        or type(descriptor) is not _contract.AdapterDescriptor
        or type(complete) is not _evidence.CompleteAdaptedEventSample
    ):
        _fail(ChildBundleCodecCode.INPUT_TYPE)
    try:
        prepared = validate_prepared_output_blind_case_input_v1(
            prepared_case_input
        )
    except Exception:
        _fail(ChildBundleCodecCode.INPUT_TRANSPORT)
    if (
        type(prepared) is not PreparedOutputBlindCaseInputV1
        or prepared != prepared_case_input
        or type(prepared.case_input) is not ActualAdapterCaseInputV1
    ):
        _fail(ChildBundleCodecCode.INPUT_TRANSPORT)
    try:
        descriptor_snapshot = _contract._snapshot_descriptor(descriptor)
        complete_snapshot = _evidence._snapshot_complete(complete)
    except _evidence.AdapterEvidenceResourceError:
        _fail(ChildBundleCodecCode.RESOURCE_LIMIT)
    except Exception:
        _fail(ChildBundleCodecCode.BINDING)
    try:
        _validate_bindings(
            prepared.case_input,
            descriptor_snapshot,
            complete_snapshot,
        )
    except _evidence.AdapterEvidenceResourceError:
        _fail(ChildBundleCodecCode.RESOURCE_LIMIT)
    except Exception:
        _fail(ChildBundleCodecCode.BINDING)
    try:
        case_input = prepared.case_input
        tree = {
            "adapted": _adapted_members(
                descriptor_snapshot,
                complete_snapshot,
            ),
            "artifact_type": (
                CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_ARTIFACT_TYPE
            ),
            "case_input_sha256": prepared.input_sha256,
            "format_version": "1",
            "source_byte_count": len(case_input.source_bytes),
            "source_sha256": hashlib.sha256(
                case_input.source_bytes
            ).hexdigest(),
            "split_manifest_sha256": _contract.split_manifest_digest(
                case_input.split_manifest
            ),
        }
        bundle_bytes = _canonical_tree_bytes(
            tree,
            maximum_encoded_bytes=(
                MAXIMUM_CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_BYTES
            ),
        )
        return ChildSafeAdaptedEvidenceBundleV1(
            bundle_bytes=bundle_bytes,
            bundle_byte_count=len(bundle_bytes),
            bundle_sha256=child_safe_adapted_evidence_bundle_sha256(
                bundle_bytes
            ),
        )
    except OverflowError:
        _fail(ChildBundleCodecCode.RESOURCE_LIMIT)
    except ChildBundleCodecError:
        raise
    except (AttributeError, KeyError, IndexError, TypeError, ValueError):
        _fail(ChildBundleCodecCode.PROJECTION)
    except Exception:
        _fail(ChildBundleCodecCode.INTERNAL)


__all__ = [
    "CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_ARTIFACT_TYPE",
    "CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_DIGEST_DOMAIN",
    "ChildBundleCodecCode",
    "ChildBundleCodecError",
    "ChildSafeAdaptedEvidenceBundleV1",
    "MAXIMUM_CHILD_SAFE_ADAPTED_EVIDENCE_BUNDLE_BYTES",
    "MAXIMUM_CHILD_SAFE_CANONICAL_DEPTH",
    "MAXIMUM_CHILD_SAFE_CANONICAL_LEAF_BYTES",
    "MAXIMUM_CHILD_SAFE_CANONICAL_NODES",
    "MAXIMUM_CHILD_SAFE_CANONICAL_STRING_BYTES",
    "build_child_safe_adapted_evidence_bundle",
    "child_safe_adapted_evidence_bundle_sha256",
]
