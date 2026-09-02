"""Source-independent CP65 production receipt-schema validator.

This module intentionally imports neither the authoritative CP65 catalog nor
CP64 (nor any other project module).  It independently reconstructs the frozen
schema semantics and validates only caller-supplied bytes.  It performs no
filesystem, host, clock, entropy, network, process, authorization, or execution
operation.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import hmac
import json
import math
import re
import threading
from typing import Mapping, Tuple, cast
import weakref


CP65_TEST28_SCHEMA_VERSION = "cp65-test28-production-schema-preimage-validator-v1"
CP65_TEST28_SCOPE = (
    "zero-execution-production-schema-preimage-and-syntax-validation-only;"
    "no-external-receipts;no-seeds;no-host-probes;no-filesystem-write;"
    "no-trust-root;no-authority-verification;no-gate-evidence;no-authorization;"
    "no-launch;no-execution;no-blocker-closure"
)

_ZERO_SHA256 = "0" * 64
_CANONICAL_PROFILE_ID = "cp65-ascii-canonical-json-v1"
_MAX_SUPPLIED_ARTIFACT_SET_ITEMS = 312
_MAX_SUPPLIED_ARTIFACT_SET_BYTES = 536_870_912
_MAX_SUPPLIED_ARTIFACT_SET_NODES = 1_048_576
_MAX_SUPPLIED_ARTIFACT_SET_DECODED_STRING_CHARACTERS = 268_435_456
_MAX_SOURCE_MANIFEST_ENTRIES = 4_096
_MAX_TERMINAL_PUBLICATION_ENTRIES = 312
_FROZEN_PROTOCOL_BYTES = 125_063
_FROZEN_PROTOCOL_SHA256 = (
    "79074586ce77d5a57ad49193098b0ba7c8e07e7446c002b42277572e10193df8"
)
_FROZEN_MACHINE_MANIFEST_BYTES = 2_038_189
_FROZEN_MACHINE_MANIFEST_SHA256 = (
    "e9cd67841d12325e06cdd645e79d40737937b36d6052275ffb9e5185d8978376"
)
_FROZEN_DEPENDENCY_LOCK_BYTES = 736
_FROZEN_DEPENDENCY_LOCK_SHA256 = (
    "ba373a4f7ef687e55d6f0a5cbc1f14eaf9db03ab1cf001cc8d6009e85adbbc5d"
)
_SHARD_ID_RE = re.compile(r"shard-00(?:0[1-9]|[12][0-9]|3[0-2])\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_HEX16_RE = re.compile(r"[0-9a-f]{16}\Z")
_HEX768_RE = re.compile(r"[0-9a-f]{768}\Z")
_UTC_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\." r"[0-9]{6}Z\Z"
)
_ATTEMPT_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_OPAQUE_METHOD_SESSION_AUTHORITY_ID_RE = re.compile(r"[a-z0-9][a-z0-9._:/-]{0,127}\Z")
_ALLOW_RECORD_CLASS_DEFINITION = True


class _SealedRecord:
    __slots__ = ("__weakref__",)

    def __new__(cls, *args: object, **kwargs: object) -> object:
        del args, kwargs
        raise TypeError("independent CP65 records are module-created only")

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        if not _ALLOW_RECORD_CLASS_DEFINITION:
            raise TypeError("independent CP65 records cannot be subclassed")

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise TypeError("independent CP65 records are not pickle objects")


@dataclass(frozen=True, eq=False, init=False)
class CP65IndependentSuppliedValidationV1(_SealedRecord):
    schema_version: str
    validation_scope: str
    caller_supplied_bytes_only: bool
    input_artifact_ids: Tuple[str, ...]
    input_relative_paths: Tuple[str, ...]
    input_sha256s: Tuple[str, ...]
    input_byte_lengths: Tuple[int, ...]
    validated_artifact_ids: Tuple[str, ...]
    validated_relative_paths: Tuple[str, ...]
    validated_body_sha256s: Tuple[str, ...]
    syntax_valid: bool
    intrinsic_digest_preimages_valid: bool
    all_required_digest_preimage_sources_supplied: bool
    validated_digest_preimage_count: int
    unresolved_digest_preimage_count: int
    digest_preimages_valid: bool
    all_required_cross_binding_targets_supplied: bool
    validated_cross_binding_count: int
    unresolved_cross_binding_count: int
    cross_bindings_valid: bool
    signature_verification_applicable: bool
    signature_mathematically_valid_under_supplied_key: bool
    parser_input_resource_limits_satisfied: bool
    external_production_receipts_observed: bool
    external_provenance_verified: bool
    filesystem_observed: bool
    source_authority_verified: bool
    authorization_trust_root_bound: bool
    authority_verified: bool
    production_evidence_accepted: bool
    gate_transition_permitted: bool
    launch_authorized: bool
    execution_permitted: bool
    definition_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


@dataclass(frozen=True, eq=False, init=False)
class CP65IndependentProductionSchemaPreimageValidatorBundleV1(_SealedRecord):
    schema_version: str
    scope: str
    canonical_profile_id: str
    artifact_ids: Tuple[str, ...]
    transient_path_ids: Tuple[str, ...]
    field_rule_ids: Tuple[str, ...]
    digest_contract_ids: Tuple[str, ...]
    sha256_pointer_classification_ids: Tuple[str, ...]
    predicate_ids: Tuple[str, ...]
    gate_ids: Tuple[str, ...]
    auxiliary_bound_ids: Tuple[str, ...]
    schema_semantic_sha256: str
    sha256_pointer_contract_count: int
    sha256_pointer_contracts_cover_every_sha256_field_rule: bool
    registry_required_targets_all_durable_by_gate15: bool
    later_artifacts_have_no_registry_dependency: bool
    all_schema_references_resolve_exactly_once: bool
    no_orphan_or_unused_rule_predicate_digest_or_artifact_ids: bool
    all_referenced_rules_have_executable_validator_semantics: bool
    global_path_count: int
    per_shard_path_template_count: int
    conditional_path_count: int
    expanded_final_path_count: int
    reserved_destination_partial_path_count: int
    prepared_authorization_partial_path_count: int
    auxiliary_reserved_partial_or_existing_final_slot_count: int
    auxiliary_reservation_hold_path_count: int
    ordinary_auxiliary_partial_candidate_path_count: int
    expanded_transient_path_count: int
    expanded_final_and_transient_path_count: int
    generic_writer_partial_paths_are_state_aliases: bool
    expanded_final_and_transient_paths_collision_free: bool
    complete_final_path_template_roster_frozen: bool
    complete_production_roster_frozen: bool
    gate_count: int
    evidence_present_count: int
    digest_dag_node_count: int
    digest_dag_edge_count: int
    digest_dag_node_ids: Tuple[str, ...]
    digest_dag_edges: Tuple[Tuple[str, str], ...]
    digest_dag_edge_target_pointers: Tuple[str, ...]
    digest_dag_edge_source_contract_ids: Tuple[str, ...]
    digest_dag_edge_digest_kinds: Tuple[str, ...]
    digest_dag_is_gate_evidence_only: bool
    artifact_preimage_dependency_node_ids: Tuple[str, ...]
    artifact_preimage_dependency_edges: Tuple[Tuple[str, str], ...]
    artifact_preimage_edge_target_pointers: Tuple[str, ...]
    artifact_preimage_edge_source_contract_ids: Tuple[str, ...]
    artifact_preimage_edge_digest_kinds: Tuple[str, ...]
    artifact_preimage_topological_order: Tuple[str, ...]
    artifact_preimage_node_count: int
    artifact_preimage_edge_count: int
    artifact_preimage_dag_acyclic: bool
    artifact_preimage_dag_complete: bool
    artifact_body_domain_separators_unique: bool
    receipt_envelope_artifact_ids: Tuple[str, ...]
    referenced_execution_output_artifact_ids: Tuple[str, ...]
    frozen_or_binary_custody_artifact_ids: Tuple[str, ...]
    receipt_envelope_schema_count: int
    referenced_execution_output_schema_count: int
    frozen_or_binary_custody_schema_count: int
    artifact_kind_partitions_disjoint_and_exhaustive: bool
    schema_completeness_claim_scope: str
    all_required_production_receipt_keysets_predeclared: bool
    complete_receipt_type_range_size_and_domain_schemas_frozen: bool
    complete_auxiliary_artifact_size_schema_frozen: bool
    bounded_auxiliary_artifact_size_proof_present: bool
    generic_prestart_terminal_record_schema_frozen: bool
    all_required_production_receipt_digest_preimages_frozen: bool
    complete_production_digest_instance_validation_interface_frozen: bool
    authorization_signature_preimage_and_verifier_frozen: bool
    requirement_schemas_frozen: bool
    artifact_occurrence_and_branch_schema_frozen: bool
    production_receipt_schema_frozen: bool
    production_execution_and_output_schema_frozen: bool
    production_schema_frozen: bool
    external_production_receipts_observed: bool
    authority_verified: bool
    production_evidence_accepted: bool
    launch_authorized: bool
    execution_permitted: bool
    authoritative_module_imported: bool
    project_modules_imported: bool
    filesystem_path_api_exposed: bool
    definition_only: bool
    record_sha256: str

    __slots__ = tuple(__annotations__)


_ALLOW_RECORD_CLASS_DEFINITION = False

_RECORD_DOMAINS = {
    CP65IndependentSuppliedValidationV1: (b"cp65-independent-supplied-validation-v1"),
    CP65IndependentProductionSchemaPreimageValidatorBundleV1: (
        b"cp65-independent-production-schema-preimage-validator-bundle-v1"
    ),
}

_ISSUED_RECORD_LOCK = threading.RLock()
_ISSUED_RECORD_SNAPSHOTS: weakref.WeakKeyDictionary[
    _SealedRecord, bytes
] = weakref.WeakKeyDictionary()


def _canonical_value(value: object, *, require_issued: bool) -> object:
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is tuple:
        return tuple(
            _canonical_value(item, require_issued=require_issued) for item in value
        )
    if isinstance(value, _SealedRecord):
        if type(value) not in _RECORD_DOMAINS:
            raise TypeError("unsupported independent CP65 record type")
        if require_issued:
            with _ISSUED_RECORD_LOCK:
                if _ISSUED_RECORD_SNAPSHOTS.get(value) is None:
                    raise TypeError("independent CP65 record was not module-created")
        return {
            item.name: _canonical_value(
                getattr(value, item.name), require_issued=require_issued
            )
            for item in fields(type(value))
        }
    raise TypeError("value has no independent CP65 canonical representation")


def _canonical_bytes(value: object, *, require_issued: bool) -> bytes:
    return json.dumps(
        _canonical_value(value, require_issued=require_issued),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _plain_json_value(value: object) -> object:
    """Copy an exact JSON value without admitting implicit Python coercions."""

    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) in (tuple, list):
        return [_plain_json_value(item) for item in value]
    if type(value) is dict:
        result = {}
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("independent CP65 plain JSON keys must be strings")
            result[key] = _plain_json_value(item)
        return result
    raise TypeError("value has no independent CP65 plain JSON representation")


def _plain_json_bytes(value: object) -> bytes:
    """Encode independently generated catalog data as canonical ASCII JSON."""

    return json.dumps(
        _plain_json_value(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _seal_plain_record(domain: bytes, values: Mapping[str, object]) -> dict:
    """Seal one independently restated plain record under its own domain."""

    if type(domain) is not bytes or not domain or b"\0" in domain:
        raise TypeError("plain-record domain must be nonempty exact bytes")
    if type(values) is not dict or "record_sha256" in values:
        raise TypeError("plain-record values must omit record_sha256")
    complete = dict(values)
    complete["record_sha256"] = _ZERO_SHA256
    complete["record_sha256"] = hashlib.sha256(
        domain + b"\0" + _plain_json_bytes(complete)
    ).hexdigest()
    return complete


def _record(cls: type, values: Mapping[str, object]) -> object:
    names = tuple(item.name for item in fields(cls))
    if set(values) != set(names) - {"record_sha256"}:
        raise TypeError("independent CP65 sealed record field set differs")
    complete = dict(values)
    complete["record_sha256"] = _ZERO_SHA256
    provisional = object.__new__(cls)
    for name in names:
        object.__setattr__(provisional, name, complete[name])
    complete["record_sha256"] = hashlib.sha256(
        _RECORD_DOMAINS[cls]
        + b"\0"
        + _canonical_bytes(provisional, require_issued=False)
    ).hexdigest()
    result = object.__new__(cls)
    for name in names:
        object.__setattr__(result, name, complete[name])
    snapshot = _canonical_bytes(result, require_issued=False)
    with _ISSUED_RECORD_LOCK:
        _ISSUED_RECORD_SNAPSHOTS[cast(_SealedRecord, result)] = snapshot
    return result


def _require_relative_path(value: object, name: str) -> str:
    if type(value) is not str:
        raise ValueError(name + " must be a relative path string")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(name + " must be ASCII") from exc
    if (
        not value
        or value.startswith("/")
        or "\\" in value
        or "\0" in value
        or any(part in ("", ".", "..") for part in value.split("/"))
    ):
        raise ValueError(name + " is not a normalized POSIX relative path")
    return value


def _require_shard_id(value: object, name: str) -> str:
    if type(value) is not str or _SHARD_ID_RE.fullmatch(value) is None:
        raise ValueError(name + " must identify candidate shard 0001..0032")
    return value


def _relative_path_matches_template(
    path_template: object, relative_path: object
) -> bool:
    """Match one normalized final path, including the closed shard expansion."""

    path = _require_relative_path(relative_path, "relative_path")
    if type(path_template) is not str:
        raise ValueError("path_template must be a relative path string")
    if path_template.count("{shard_id}") > 1:
        raise ValueError("path_template contains repeated shard placeholders")
    normalized_template = path_template.replace("{shard_id}", "shard-0001")
    _require_relative_path(normalized_template, "path_template")
    if "{shard_id}" not in path_template:
        return path == path_template
    prefix, suffix = path_template.split("{shard_id}")
    if not path.startswith(prefix) or not path.endswith(suffix):
        return False
    shard_id = path[len(prefix) : len(path) - len(suffix) if suffix else None]
    return _SHARD_ID_RE.fullmatch(shard_id) is not None


def _expand_shard_path_template(path_template: object, shard_id: object) -> str:
    """Expand exactly one per-shard path template."""

    shard = _require_shard_id(shard_id, "shard_id")
    if type(path_template) is not str or path_template.count("{shard_id}") != 1:
        raise ValueError("path_template must contain one shard placeholder")
    expanded = path_template.replace("{shard_id}", shard)
    _require_relative_path(expanded, "expanded relative path")
    return expanded


def _reject_float(_text: str) -> object:
    raise ValueError("independent CP65 canonical JSON forbids floats")


def _reject_constant(_text: str) -> object:
    raise ValueError("independent CP65 canonical JSON forbids nonfinite constants")


def _bounded_parse_int(text: str) -> int:
    unsigned = text[1:] if text.startswith("-") else text
    if len(unsigned) > 20:
        raise ValueError("independent CP65 integer token is too long")
    value = int(text, 10)
    if not -(2**63) <= value <= 2**64 - 1:
        raise ValueError("independent CP65 integer is outside parser bounds")
    return value


def _unique_object(pairs: list) -> dict:
    if len(pairs) > 128:
        raise ValueError("independent CP65 object has too many members")
    result = {}
    for key, value in pairs:
        try:
            key_bytes = key.encode("ascii")
        except (AttributeError, UnicodeEncodeError) as exc:
            raise ValueError(
                "independent CP65 object key is not bounded ASCII"
            ) from exc
        if len(key_bytes) > 128:
            raise ValueError("independent CP65 object key is too long")
        if key in result:
            raise ValueError("independent CP65 object contains a duplicate key")
        result[key] = value
    return result


def _validate_lexical_nesting(payload: bytes) -> None:
    depth = 0
    structural_node_lower_bound = 1
    in_string = False
    escaped = False
    for byte in payload:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x5B, 0x7B):
            depth += 1
            structural_node_lower_bound += 1
            if structural_node_lower_bound > _MAX_SUPPLIED_ARTIFACT_SET_NODES:
                raise ValueError("independent CP65 JSON has too many nodes")
            if depth > 16:
                raise ValueError("independent CP65 JSON nesting is too deep")
        elif byte in (0x5D, 0x7D):
            depth -= 1
            if depth < 0:
                raise ValueError("independent CP65 JSON nesting is malformed")
        elif byte == 0x2C:
            structural_node_lower_bound += 1
            if structural_node_lower_bound > _MAX_SUPPLIED_ARTIFACT_SET_NODES:
                raise ValueError("independent CP65 JSON has too many nodes")


def _validate_json_resources(value: object) -> Tuple[int, int]:
    stack = [(value, 1)]
    node_count = 0
    decoded_string_characters = 0
    while stack:
        current, depth = stack.pop()
        node_count += 1
        if node_count > _MAX_SUPPLIED_ARTIFACT_SET_NODES:
            raise ValueError("independent CP65 JSON has too many nodes")
        if depth > 16:
            raise ValueError("independent CP65 JSON nesting is too deep")
        if current is None:
            raise ValueError("CP65 independent canonical JSON forbids null")
        if type(current) in (bool, int):
            continue
        if type(current) is str:
            try:
                length = len(current.encode("ascii"))
            except UnicodeEncodeError as exc:
                raise ValueError("independent CP65 JSON string is not ASCII") from exc
            if length > 1_048_576:
                raise ValueError("independent CP65 JSON string is too long")
            decoded_string_characters += len(current)
            if (
                decoded_string_characters
                > _MAX_SUPPLIED_ARTIFACT_SET_DECODED_STRING_CHARACTERS
            ):
                raise ValueError(
                    "independent CP65 JSON decoded strings exceed their cap"
                )
            continue
        if type(current) is list:
            if len(current) > 32_768:
                raise ValueError("independent CP65 JSON array is too long")
            stack.extend((item, depth + 1) for item in reversed(current))
            continue
        if type(current) is dict:
            decoded_string_characters += sum(len(key) for key in current)
            if (
                decoded_string_characters
                > _MAX_SUPPLIED_ARTIFACT_SET_DECODED_STRING_CHARACTERS
            ):
                raise ValueError(
                    "independent CP65 JSON decoded strings exceed their cap"
                )
            stack.extend((item, depth + 1) for item in current.values())
            continue
        raise ValueError("independent CP65 JSON contains an unsupported value")
    return node_count, decoded_string_characters


def _parse_canonical_json_object_impl(payload: object, maximum_bytes: int) -> dict:
    if type(payload) is not bytes:
        raise TypeError("payload must be exact bytes")
    if type(maximum_bytes) is not int or maximum_bytes < 2:
        raise TypeError("maximum_bytes must be a positive exact integer")
    if not 2 <= len(payload) <= maximum_bytes:
        raise ValueError("payload byte length is outside the frozen bound")
    _validate_lexical_nesting(payload)
    try:
        text = payload.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("payload must be ASCII") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_int=_bounded_parse_int,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except (
        json.JSONDecodeError,
        UnicodeError,
        RecursionError,
        OverflowError,
        MemoryError,
    ) as exc:
        raise ValueError("payload is not bounded independent CP65 JSON") from exc
    if type(value) is not dict:
        raise ValueError("payload must contain one top-level object")
    _validate_json_resources(value)
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    if canonical != payload:
        raise ValueError("payload differs from exact independent CP65 JSON")
    return value


def _parse_canonical_json_object(payload: object, maximum_bytes: int) -> dict:
    try:
        return _parse_canonical_json_object_impl(payload, maximum_bytes)
    except MemoryError as exc:
        raise ValueError("payload is not bounded independent CP65 JSON") from exc


def _aggregate_json_resource_counts(
    documents: Tuple[object, ...],
) -> Tuple[int, int]:
    """Enforce the resource caps across a complete supplied artifact set."""

    if type(documents) is not tuple:
        raise TypeError("documents must be an exact tuple")
    aggregate_nodes = 0
    aggregate_decoded_characters = 0
    try:
        for document in documents:
            if type(document) is not dict:
                continue
            nodes, decoded_characters = _validate_json_resources(document)
            aggregate_nodes += nodes
            aggregate_decoded_characters += decoded_characters
            if aggregate_nodes > _MAX_SUPPLIED_ARTIFACT_SET_NODES:
                raise ValueError("supplied artifact set contains too many parsed nodes")
            if (
                aggregate_decoded_characters
                > _MAX_SUPPLIED_ARTIFACT_SET_DECODED_STRING_CHARACTERS
            ):
                raise ValueError(
                    "supplied artifact set contains too many decoded string characters"
                )
    except MemoryError as exc:
        raise ValueError("supplied artifact set exceeded parser limits") from exc
    return aggregate_nodes, aggregate_decoded_characters


def _decode_json_pointer_part(encoded: str) -> str:
    decoded = []
    position = 0
    while position < len(encoded):
        character = encoded[position]
        if character != "~":
            decoded.append(character)
            position += 1
            continue
        if position + 1 >= len(encoded) or encoded[position + 1] not in ("0", "1"):
            raise ValueError("JSON pointer contains a noncanonical escape")
        decoded.append("~" if encoded[position + 1] == "0" else "/")
        position += 2
    return "".join(decoded)


def _json_pointer_parts(pointer: object, *, allow_wildcard: bool) -> Tuple[str, ...]:
    if type(pointer) is not str or not pointer.startswith("/"):
        raise ValueError("JSON pointer differs")
    parts = tuple(_decode_json_pointer_part(part) for part in pointer[1:].split("/"))
    if not allow_wildcard and "*" in pointer:
        raise ValueError("closed JSON pointer differs")
    if allow_wildcard and any("*" in part and part != "*" for part in parts):
        raise ValueError("wildcard JSON pointer differs")
    return parts


def _resolve_closed_json_pointer(document: object, pointer: object) -> object:
    current = document
    for part in _json_pointer_parts(pointer, allow_wildcard=False):
        if type(current) is not dict or part not in current:
            raise ValueError("closed JSON pointer does not resolve")
        current = current[part]
    return current


def _resolve_selected_json_pointer(
    document: object,
    pointer: object,
    wildcard_indices: object,
) -> object:
    """Resolve a wildcard pointer under one exact array-index selector."""

    if type(wildcard_indices) is not tuple or any(
        type(index) is not int or index < 0 for index in wildcard_indices
    ):
        raise ValueError("JSON pointer selector differs")
    current = document
    wildcard_ordinal = 0
    for part in _json_pointer_parts(pointer, allow_wildcard=True):
        if part == "*":
            if type(current) is not list or wildcard_ordinal >= len(wildcard_indices):
                raise ValueError("wildcard JSON pointer does not resolve")
            selected = wildcard_indices[wildcard_ordinal]
            wildcard_ordinal += 1
            if selected >= len(current):
                raise ValueError("JSON pointer selector is out of range")
            current = current[selected]
            continue
        if type(current) is not dict or part not in current:
            raise ValueError("wildcard JSON pointer does not resolve")
        current = current[part]
    if wildcard_ordinal != len(wildcard_indices):
        raise ValueError("JSON pointer selector cardinality differs")
    return current


def _enumerate_wildcard_json_pointer(
    document: object, pointer: object
) -> Tuple[Tuple[Tuple[int, ...], object], ...]:
    """Enumerate all array selections for a closed-or-wildcard pointer."""

    rows = (((), document),)
    for part in _json_pointer_parts(pointer, allow_wildcard=True):
        expanded = []
        for indices, current in rows:
            if part == "*":
                if type(current) is not list:
                    raise ValueError("wildcard JSON pointer does not resolve")
                expanded.extend(
                    (indices + (index,), item) for index, item in enumerate(current)
                )
            else:
                if type(current) is not dict or part not in current:
                    raise ValueError("wildcard JSON pointer does not resolve")
                expanded.append((indices, current[part]))
        rows = tuple(expanded)
    return rows


def _resolve_registry_target_pointer(
    document: object,
    pointer: object,
    wildcard_indices: object,
) -> object:
    return _resolve_selected_json_pointer(document, pointer, wildcard_indices)


def _normalize_supplied_artifact(
    artifact_id: object, relative_path: object, payload: object
) -> Tuple[str, str, bytes]:
    if type(artifact_id) is not str or type(relative_path) is not str:
        raise TypeError("supplied artifact id/path must be exact strings")
    if type(payload) is not bytes:
        raise TypeError("supplied artifact payload must be exact bytes")
    return artifact_id, _require_relative_path(relative_path, "relative_path"), payload


def _normalize_supplied_artifact_set(
    items: object,
) -> Tuple[Tuple[str, str, bytes], ...]:
    """Normalize only exact immutable triples and enforce whole-set caps."""

    if type(items) is not tuple:
        raise TypeError("items must be an exact tuple")
    if not 1 <= len(items) <= _MAX_SUPPLIED_ARTIFACT_SET_ITEMS:
        raise ValueError("supplied artifact set cardinality is outside 1..312")
    normalized = []
    paths = set()
    total_bytes = 0
    for item in items:
        if type(item) is not tuple or len(item) != 3:
            raise TypeError("each supplied item must be an exact three-tuple")
        normalized_item = _normalize_supplied_artifact(*item)
        if normalized_item[1] in paths:
            raise ValueError("supplied artifact paths must be unique")
        paths.add(normalized_item[1])
        total_bytes += len(normalized_item[2])
        if total_bytes > _MAX_SUPPLIED_ARTIFACT_SET_BYTES:
            raise ValueError("supplied artifact set exceeds 512 MiB")
        normalized.append(normalized_item)
    return tuple(normalized)


def _supplied_validation(
    artifact_ids: Tuple[str, ...],
    relative_paths: Tuple[str, ...],
    payloads: Tuple[bytes, ...],
    body_sha256s: Tuple[str, ...],
    *,
    signature_applicable: bool = False,
    signature_valid: bool = False,
    validated_digest_preimage_count: int = 1,
    unresolved_digest_preimage_count: int = 1,
    validated_cross_binding_count: int = 0,
    unresolved_cross_binding_count: int = 0,
) -> CP65IndependentSuppliedValidationV1:
    sequences = (artifact_ids, relative_paths, payloads, body_sha256s)
    if any(type(sequence) is not tuple for sequence in sequences):
        raise TypeError("independent validation inputs must be exact tuples")
    if not artifact_ids or len({len(sequence) for sequence in sequences}) != 1:
        raise ValueError("independent validation input cardinalities differ")
    if len(artifact_ids) > _MAX_SUPPLIED_ARTIFACT_SET_ITEMS:
        raise ValueError("independent validation input cardinality exceeds its cap")
    if any(type(item) is not str for item in artifact_ids):
        raise TypeError("validated artifact ids must be exact strings")
    if any(type(item) is not str for item in relative_paths):
        raise TypeError("validated relative paths must be exact strings")
    for path in relative_paths:
        _require_relative_path(path, "validated relative path")
    if any(type(item) is not bytes for item in payloads):
        raise TypeError("validated payloads must be exact bytes")
    if any(
        type(item) is not str or _SHA256_RE.fullmatch(item) is None
        for item in body_sha256s
    ):
        raise ValueError("validated body digests must be lowercase SHA256 hex")
    if type(signature_applicable) is not bool or type(signature_valid) is not bool:
        raise TypeError("signature result flags must be exact booleans")
    if signature_valid and not signature_applicable:
        raise ValueError(
            "a signature cannot be valid when verification is inapplicable"
        )
    counts = (
        validated_digest_preimage_count,
        unresolved_digest_preimage_count,
        validated_cross_binding_count,
        unresolved_cross_binding_count,
    )
    if any(type(count) is not int or count < 0 for count in counts):
        raise ValueError("validation counts must be exact nonnegative integers")
    return cast(
        CP65IndependentSuppliedValidationV1,
        _record(
            CP65IndependentSuppliedValidationV1,
            {
                "schema_version": CP65_TEST28_SCHEMA_VERSION,
                "validation_scope": "caller-supplied-development-bytes-only",
                "caller_supplied_bytes_only": True,
                "input_artifact_ids": artifact_ids,
                "input_relative_paths": relative_paths,
                "input_sha256s": tuple(
                    hashlib.sha256(item).hexdigest() for item in payloads
                ),
                "input_byte_lengths": tuple(len(item) for item in payloads),
                "validated_artifact_ids": artifact_ids,
                "validated_relative_paths": relative_paths,
                "validated_body_sha256s": body_sha256s,
                "syntax_valid": True,
                "intrinsic_digest_preimages_valid": True,
                "all_required_digest_preimage_sources_supplied": (
                    unresolved_digest_preimage_count == 0
                ),
                "validated_digest_preimage_count": validated_digest_preimage_count,
                "unresolved_digest_preimage_count": unresolved_digest_preimage_count,
                "digest_preimages_valid": unresolved_digest_preimage_count == 0,
                "all_required_cross_binding_targets_supplied": (
                    unresolved_cross_binding_count == 0
                ),
                "validated_cross_binding_count": validated_cross_binding_count,
                "unresolved_cross_binding_count": unresolved_cross_binding_count,
                "cross_bindings_valid": unresolved_cross_binding_count == 0,
                "signature_verification_applicable": signature_applicable,
                "signature_mathematically_valid_under_supplied_key": signature_valid,
                "parser_input_resource_limits_satisfied": True,
                "external_production_receipts_observed": False,
                "external_provenance_verified": False,
                "filesystem_observed": False,
                "source_authority_verified": False,
                "authorization_trust_root_bound": False,
                "authority_verified": False,
                "production_evidence_accepted": False,
                "gate_transition_permitted": False,
                "launch_authorized": False,
                "execution_permitted": False,
                "definition_only": True,
            },
        ),
    )


_I_ARTIFACT_DECLARATIONS = (
    (
        "frozen-protocol",
        "frozen_inputs/protocol.md",
        "global",
        "frozen-input-opaque",
        (),
        (),
        "",
        False,
    ),
    (
        "frozen-protocol-sha256",
        "frozen_inputs/protocol.sha256",
        "global",
        "sha256-text",
        (),
        (),
        "",
        False,
    ),
    (
        "frozen-machine-manifest",
        "frozen_inputs/machine_manifest.json",
        "global",
        "frozen-input-canonical-json",
        (),
        (),
        "",
        False,
    ),
    (
        "source-manifest",
        "frozen_inputs/bound_files.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "protocol_sha256",
            "machine_manifest_sha256",
            "entry_count",
            "total_bytes",
            "entries",
            "ordered_entries_sha256",
            "body_sha256",
        ),
        (
            (
                "entries",
                ("ordinal", "role", "relative_path", "bytes", "lines", "sha256"),
            ),
        ),
        "cp65-test28-source-manifest-v1",
        False,
    ),
    (
        "dependency-lock",
        "frozen_inputs/dependency_lock.txt",
        "global",
        "receipt-envelope-opaque-bytes",
        (),
        (),
        "",
        False,
    ),
    (
        "freeze-receipt",
        "freeze_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "from_state",
            "to_state",
            "protocol_sha256",
            "machine_manifest_sha256",
            "bound_files_sha256",
            "frozen_source_fixture_materialization_sha256",
            "dependency_lock_sha256",
            "power_threshold_receipt_sha256",
            "launch_authority_public_key_sha256",
            "independent_reviewer_public_key_set_sha256",
            "seed_source_authority_public_key_sha256",
            "production_receipt_schema_bundle_sha256",
            "frozen_at_utc",
            "freezer_identity_sha256",
            "body_sha256",
        ),
        (),
        "cp65-test28-freeze-receipt-v2",
        False,
    ),
    (
        "power-threshold-receipt",
        "power_threshold_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "protocol_sha256",
            "machine_manifest_sha256",
            "power_review_ascii",
            "power_review_sha256",
            "selected_count_justification_ascii",
            "selected_count_justification_sha256",
            "primary_slot_count",
            "ordered_slot_thresholds",
            "ordered_slot_threshold_row_sha256s",
            "ordered_slot_thresholds_sha256",
            "reviewer_signoff_sha256",
            "completed_at_utc",
            "body_sha256",
        ),
        (
            (
                "ordered_slot_thresholds",
                (
                    "slot_ordinal",
                    "gate_id",
                    "estimand_id",
                    "threshold_encoding",
                    "threshold_value",
                    "design_minimum_selected_count",
                    "justification_ascii",
                    "justification_sha256",
                    "row_sha256",
                ),
            ),
        ),
        "cp65-test28-power-threshold-receipt-v2",
        False,
    ),
    (
        "preflight-gate-summary",
        "preflight_gate_summary.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "covered_gate_ids",
            "covered_gate_states",
            "covered_evidence_node_ids",
            "ordered_evidence_receipt_sha256s",
            "external_digest_preimage_registry_sha256",
            "body_sha256",
        ),
        (),
        "cp65-test28-preflight-gate-summary-v2",
        False,
    ),
    (
        "independent-signoff-set",
        "independent_signoff.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "preflight_gate_summary_sha256",
            "reviewer_public_key_set_sha256",
            "required_reviewer_roles",
            "ordered_signoffs",
            "signoff_count",
            "all_required_roles_present",
            "all_decisions_approve",
            "all_signatures_mathematically_valid_under_declared_keys",
            "body_sha256",
        ),
        (
            (
                "ordered_signoffs",
                (
                    "reviewer_role",
                    "reviewer_identity_sha256",
                    "reviewer_public_key_identity_sha256",
                    "reviewed_artifact_sha256s",
                    "decision",
                    "signed_at_utc",
                    "signature_scheme_id",
                    "reviewer_signature_sha256",
                    "reviewer_signature_hex",
                    "signoff_sha256",
                ),
            ),
        ),
        "cp65-test28-independent-signoff-set-v1",
        False,
    ),
    (
        "capacity-receipt",
        "capacity_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "destination_reservation_required_bytes",
            "auxiliary_metadata_reservation_required_bytes",
            "combined_available_and_quota_required_before_reservation_bytes",
            "available_and_quota_required_after_destination_before_auxiliary_reservation_bytes",
            "schedule_sha256",
            "capacity_schema_sha256",
            "storage_root_identity_sha256",
            "filesystem_identity_sha256",
            "measurement_session_sha256",
            "measured_at_utc",
            "measurement_method_id",
            "quota_method_id",
            "reservation_method_id",
            "auxiliary_metadata_reservation_method_id",
            "allocation_unit_bytes",
            "auxiliary_metadata_reservation_artifact_sha256",
            "available_bytes_before_reservation",
            "quota_headroom_bytes_before_reservation",
            "physically_allocated_reservation_bytes",
            "physically_allocated_auxiliary_metadata_bytes",
            "auxiliary_metadata_reserved_quota_bytes",
            "usable_reserved_bytes_after_allocation",
            "available_bytes_after_reservation",
            "quota_headroom_bytes_after_reservation",
            "available_inodes_after_reservation",
            "non_sparse_allocation_verified",
            "reservation_same_filesystem_verified",
            "reservation_exclusive_verified",
            "reservation_durable_verified",
            "auxiliary_metadata_reservation_exclusive_verified",
            "auxiliary_metadata_non_sparse_allocation_verified",
            "auxiliary_metadata_reserved_quota_verified",
            "auxiliary_metadata_reservation_durable_verified",
            "auxiliary_metadata_reservation_same_storage_root_verified",
            "destination_and_auxiliary_reservation_no_double_count_verified",
            "shard_count",
            "atomic_rename_supported",
            "file_fsync_supported",
            "directory_fsync_supported",
            "auxiliary_artifact_size_proof_sha256",
            "maximum_auxiliary_artifact_logical_bytes",
            "maximum_auxiliary_reserved_bytes",
            "allocation_and_directory_charge_policy_slot_bytes",
            "observed_allocation_and_directory_charge_bytes",
            "allocation_and_directory_charge_within_policy",
            "reservation_manifest_sha256",
            "body_sha256",
        ),
        (),
        "cp65-test28-capacity-receipt-v2",
        False,
    ),
    (
        "auxiliary-metadata-reservation",
        "auxiliary_metadata_reservation.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "schedule_sha256",
            "capacity_schema_sha256",
            "measurement_session_sha256",
            "exclusive_root_charge_measurement_sha256",
            "storage_root_identity_sha256",
            "filesystem_identity_sha256",
            "reservation_method_id",
            "allocation_unit_bytes",
            "artifact_entry_count",
            "artifact_entries",
            "artifact_slot_reserved_bytes",
            "allocated_existing_final_bytes",
            "allocated_future_partial_bytes",
            "unique_nonhold_artifact_allocated_bytes",
            "exclusive_root_charge_baseline_bytes",
            "exclusive_root_charge_current_bytes",
            "disjoint_allocation_and_directory_charge_bytes",
            "hold_relative_path",
            "hold_device_identity_sha256",
            "hold_inode",
            "hold_extent_map_sha256",
            "hold_allocated_bytes",
            "allocation_and_directory_charge_policy_slot_bytes",
            "exclusive_reserved_headroom_bytes",
            "physical_reservation_sum_bytes",
            "enforced_quota_bytes",
            "exclusive_verified",
            "non_sparse_verified",
            "durable_verified",
            "same_root_verified",
            "created_at_utc",
            "body_sha256",
        ),
        (
            (
                "artifact_entries",
                (
                    "ordinal",
                    "artifact_id",
                    "final_relative_path",
                    "alternate_final_relative_path",
                    "reservation_state",
                    "partial_relative_path",
                    "primary_publication_arm_id",
                    "alternate_publication_arm_id",
                    "device_identity_sha256",
                    "inode",
                    "extent_map_sha256",
                    "maximum_logical_bytes",
                    "reserved_bytes",
                    "non_sparse_verified",
                    "exclusive_verified",
                    "file_fsync_completed_at_utc",
                    "directory_fsync_completed_at_utc",
                    "entry_sha256",
                ),
            ),
        ),
        "cp65-test28-auxiliary-metadata-reservation-v3",
        False,
    ),
    (
        "reservation-manifest",
        "reservation_manifest.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "schedule_sha256",
            "capacity_schema_sha256",
            "measurement_session_sha256",
            "storage_root_identity_sha256",
            "filesystem_identity_sha256",
            "allocation_unit_bytes",
            "entry_count",
            "entries",
            "total_logical_reserved_bytes",
            "total_allocated_reserved_bytes",
            "created_at_utc",
            "body_sha256",
        ),
        (
            (
                "entries",
                (
                    "ordinal",
                    "final_relative_path",
                    "partial_relative_path",
                    "device_identity_sha256",
                    "inode",
                    "extent_map_sha256",
                    "logical_reserved_bytes",
                    "allocated_reserved_bytes",
                    "non_sparse_verified",
                    "exclusive_verified",
                    "file_fsync_completed_at_utc",
                    "directory_fsync_completed_at_utc",
                    "entry_sha256",
                ),
            ),
        ),
        "cp65-test28-reservation-manifest-v2",
        False,
    ),
    (
        "production-runtime-receipt",
        "production_runtime_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "observation_session_sha256",
            "observed_at_utc",
            "source_manifest_sha256",
            "dependency_lock_sha256",
            "runtime_profile_id",
            "python_executable_sha256",
            "python_framework_sha256",
            "stdlib_closure_sha256",
            "numpy_record_sha256",
            "numpy_payload_closure_sha256",
            "scipy_record_sha256",
            "scipy_payload_closure_sha256",
            "loaded_local_source_closure_sha256",
            "abi_map_sha256",
            "environment_sha256",
            "body_sha256",
        ),
        (),
        "cp64-test28-production-runtime-receipt-v1",
        True,
    ),
    (
        "external-seed-acquisition-start-receipt",
        "seed_acquisition_start_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "source_method_id",
            "acquisition_journal_relative_path",
            "acquisition_journal_device_identity_sha256",
            "acquisition_journal_inode",
            "acquisition_journal_preallocated_bytes",
            "acquisition_journal_allocation_method_id",
            "acquisition_journal_extent_map_sha256",
            "acquisition_journal_file_fsync_completed_at_utc",
            "acquisition_journal_directory_fsync_completed_at_utc",
            "acquisition_journal_inode_recheck_sha256",
            "acquisition_session_id",
            "started_at_utc",
            "body_sha256",
        ),
        (),
        "cp64-test28-external-seed-acquisition-start-receipt-v1",
        True,
    ),
    (
        "external-seed-acquisition-journal",
        "seed_acquisition_journal.bin",
        "global",
        "binary-journal",
        (),
        (),
        "cp64-external-seed-acquisition-journal-entry-v1",
        True,
    ),
    (
        "external-seed-source-receipt",
        "seed_source_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "cp61_stable_design_sha256",
            "seed_count",
            "seed_encoding",
            "source_method_id",
            "acquisition_start_receipt_sha256",
            "acquisition_session_sha256",
            "acquisition_journal_sha256",
            "acquisition_journal_head_sha256",
            "acquisition_journal_entry_count",
            "ordered_seed_values_commitment_sha256",
            "custody_artifact_sha256",
            "source_authority_attestation_sha256",
            "body_sha256",
        ),
        (),
        "cp65-test28-external-seed-source-receipt-v2",
        False,
    ),
    (
        "seed-capsule-body",
        "seed_capsule.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "cp61_stable_design_sha256",
            "seed_count",
            "seed_ordinals",
            "seed_encoding",
            "ordered_seed_values",
            "source_method_id",
            "source_receipt_sha256",
            "acquisition_session_sha256",
            "body_sha256",
        ),
        (),
        "cp63-test28-seed-capsule-v1",
        True,
    ),
    (
        "production-shard-map-receipt",
        "shard_map.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "seed_capsule_body_sha256",
            "schedule_sha256",
            "capacity_receipt_sha256",
            "durability_receipt_sha256",
            "candidate_shard_policy_sha256",
            "reservation_manifest_sha256",
            "shard_count",
            "shards",
            "body_sha256",
        ),
        (
            (
                "shards",
                (
                    "shard_ordinal",
                    "shard_id",
                    "seed_ordinal_min",
                    "seed_ordinal_max",
                    "logical_request_ordinal_min",
                    "logical_request_ordinal_max",
                    "logical_request_count",
                    "relative_directory",
                    "capacity_partition_bytes",
                    "per_file_reservation_manifest_entry_sha256s",
                    "shard_record_sha256",
                ),
            ),
        ),
        "cp64-test28-production-shard-map-receipt-v1",
        True,
    ),
    (
        "durability-receipt",
        "durability_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "capacity_receipt_sha256",
            "layout_contract_sha256",
            "writer_source_manifest_sha256",
            "qualification_session_sha256",
            "filesystem_identity_sha256",
            "atomic_rename_verified",
            "file_fsync_verified",
            "directory_fsync_verified",
            "exclusive_create_verified",
            "no_symlink_verified",
            "no_hardlink_verified",
            "no_overwrite_verified",
            "body_sha256",
        ),
        (),
        "cp64-test28-durability-receipt-v1",
        True,
    ),
    (
        "preauthorization-outcome",
        "preauthorization_outcome.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "outcome_arm",
            "prepared_launch_authorization_sha256",
            "terminal_state",
            "selected_at_utc",
            "body_sha256",
        ),
        (),
        "cp64-test28-preauthorization-outcome-v1",
        True,
    ),
    (
        "launch-authorization",
        "launch_authorization.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "attempt_state",
            "protocol_sha256",
            "machine_manifest_sha256",
            "source_manifest_sha256",
            "dependency_lock_sha256",
            "seed_source_receipt_sha256",
            "seed_capsule_body_sha256",
            "schedule_sha256",
            "production_runtime_receipt_sha256",
            "capacity_receipt_sha256",
            "durability_receipt_sha256",
            "production_shard_map_receipt_sha256",
            "preflight_gate_summary_sha256",
            "power_threshold_receipt_sha256",
            "freeze_receipt_sha256",
            "independent_signoff_sha256",
            "authorized_attempt_number",
            "authorization_issued_at_utc",
            "authorization_expires_at_utc",
            "authority_scheme_id",
            "authority_identity_sha256",
            "authority_signature_hex",
            "authority_signature_sha256",
            "body_sha256",
        ),
        (),
        "cp65-test28-launch-authorization-receipt-v2",
        False,
    ),
    (
        "postauthorization-outcome",
        "postauthorization_outcome.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "launch_authorization_sha256",
            "outcome_arm",
            "terminal_state",
            "selected_at_utc",
            "body_sha256",
        ),
        (),
        "cp64-test28-postauthorization-outcome-v1",
        True,
    ),
    (
        "started-receipt",
        "STARTED.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "launch_authorization_sha256",
            "postauthorization_outcome_sha256",
            "started_at_utc",
            "production_runner_rng_or_child_started_before_receipt",
            "body_sha256",
        ),
        (),
        "cp65-test28-started-receipt-v1",
        False,
    ),
    (
        "environment",
        "environment.json",
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "launch-receipt",
        "launch_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "launch_authorization_sha256",
            "postauthorization_outcome_sha256",
            "started_receipt_sha256",
            "production_schedule_sha256",
            "runner_source_manifest_sha256",
            "runtime_receipt_sha256",
            "shard_map_receipt_sha256",
            "launched_at_utc",
            "body_sha256",
        ),
        (),
        "cp65-test28-launch-receipt-v1",
        False,
    ),
    (
        "primary-metrics",
        "metrics/primary_metrics.json",
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "secondary-diagnostics",
        "metrics/secondary_diagnostics.json",
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "postexecution-independent-recomputation",
        "independent_recomputation.json",
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "decisions",
        "decisions.json",
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "deviations",
        "deviations.json",
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "failures",
        "failures.json",
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "exclusions",
        "exclusions.json",
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "reruns",
        "reruns.json",
        "global",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "terminal-state",
        "terminal_state.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "terminal_arm",
            "previous_lifecycle_state",
            "terminal_state",
            "freeze_receipt_sha256",
            "preauthorization_outcome_sha256",
            "launch_authorization_sha256",
            "postauthorization_outcome_sha256",
            "started_receipt_sha256",
            "durable_artifact_inventory_sha256",
            "auxiliary_transition_journal_after_inventory_entry_count",
            "auxiliary_transition_journal_after_inventory_head_sha256",
            "reason_code",
            "terminalized_at_utc",
            "body_sha256",
        ),
        (),
        "cp65-test28-terminal-state-v1",
        False,
    ),
    (
        "sha256-manifest",
        "sha256_manifest.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "terminal_state_sha256",
            "auxiliary_transition_journal_after_terminal_entry_count",
            "auxiliary_transition_journal_after_terminal_head_sha256",
            "entry_count",
            "entries",
            "ordered_entries_sha256",
            "created_at_utc",
            "body_sha256",
        ),
        (("entries", ("path", "bytes", "sha256")),),
        "cp65-test28-sha256-manifest-v1",
        False,
    ),
    (
        "committed-marker",
        "COMMITTED.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "terminal_state_sha256",
            "sha256_manifest_sha256",
            "auxiliary_metadata_reservation_sha256",
            "auxiliary_reservation_transition_journal_sha256",
            "auxiliary_reservation_transition_journal_final_head_sha256",
            "auxiliary_reservation_transition_journal_final_entry_count",
            "auxiliary_reservation_transition_journal_file_fsync_completed_at_utc",
            "auxiliary_reservation_transition_journal_directory_fsync_completed_at_utc",
            "hold_relative_path",
            "hold_device_identity_sha256",
            "hold_inode",
            "hold_extent_map_sha256",
            "hold_removed_at_utc",
            "hold_removal_directory_fsync_completed_at_utc",
            "hold_absence_verified",
            "committed_at_utc",
            "body_sha256",
        ),
        (),
        "cp65-test28-committed-marker-v3",
        False,
    ),
    (
        "launch-authority-public-key",
        "frozen_inputs/launch_authority_public_key.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "authority_scheme_id",
            "authority_id",
            "modulus_hex",
            "public_exponent",
            "valid_from_utc",
            "valid_until_utc",
            "body_sha256",
        ),
        (),
        "cp65-test28-launch-authority-public-key-v1",
        False,
    ),
    (
        "dependency-lock-match-receipt",
        "dependency_lock_match_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "dependency_lock_relative_path",
            "expected_sha256",
            "observed_sha256",
            "observed_bytes",
            "match_verified",
            "verified_at_utc",
            "body_sha256",
        ),
        (),
        "cp65-test28-dependency-lock-match-receipt-v2",
        False,
    ),
    (
        "seed-source-custody-artifact",
        "seed_source_custody_artifact.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "source_method_id",
            "acquisition_session_sha256",
            "custody_media_type",
            "custody_encoding",
            "custody_bytes",
            "custody_payload_sha256",
            "retention_location_identity_sha256",
            "created_at_utc",
            "body_sha256",
        ),
        (),
        "cp65-test28-seed-source-custody-artifact-v1",
        False,
    ),
    (
        "seed-capsule-sequence-crosscheck-receipt",
        "seed_capsule_sequence_crosscheck_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "source_receipt_sha256",
            "seed_capsule_body_sha256",
            "source_sequence_commitment_sha256",
            "capsule_sequence_commitment_sha256",
            "seed_count",
            "seed_encoding",
            "sequence_equal",
            "checked_at_utc",
            "body_sha256",
        ),
        (),
        "cp65-test28-seed-capsule-sequence-crosscheck-receipt-v1",
        False,
    ),
    (
        "production-schedule",
        "production_schedule.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "seed_capsule_body_sha256",
            "schedule_contract_sha256",
            "request_count",
            "requests",
            "ordered_request_record_sha256s",
            "ordered_requests_sha256",
            "body_sha256",
        ),
        (
            (
                "requests",
                (
                    "schema_version",
                    "seed_capsule_body_sha256",
                    "seed_ordinal",
                    "row_ordinal",
                    "logical_request_ordinal",
                    "row_key",
                    "fixture_id",
                    "strategy",
                    "budget",
                    "plan_seed_hex",
                    "seed_free_request_sha256",
                    "runtime_lock_sha256",
                    "request_instance_sha256",
                    "request_row_sha256",
                ),
            ),
        ),
        "cp65-test28-production-schedule-v1",
        False,
    ),
    (
        "production-runner-supervisor-qualification-receipt",
        "production_runner_supervisor_qualification_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "source_manifest_sha256",
            "runtime_receipt_sha256",
            "supervisor_contract_sha256",
            "qualification_fixture_set_sha256",
            "qualification_test_count",
            "timeout_case_count",
            "process_group_cleanup_case_count",
            "fd_leak_case_count",
            "environment_drift_case_count",
            "all_cases_passed",
            "qualified_at_utc",
            "body_sha256",
        ),
        (),
        "cp65-test28-production-runner-supervisor-qualification-receipt-v1",
        False,
    ),
    (
        "closed-refusal-failure-classifier-qualification-receipt",
        "closed_refusal_failure_classifier_qualification_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "classifier_source_manifest_sha256",
            "supervisor_contract_sha256",
            "closed_refusal_codes",
            "closed_failure_codes",
            "reachability_case_count",
            "all_closed_arms_reachable",
            "unknown_codes_rejected",
            "qualified_at_utc",
            "body_sha256",
        ),
        (),
        "cp65-test28-closed-refusal-failure-classifier-qualification-receipt-v1",
        False,
    ),
    (
        "independent-554-estimate-interval-decision-path-qualification-receipt",
        "independent_554_estimate_interval_decision_path_qualification_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "qualification_fixture_set_sha256",
            "estimand_contract_sha256",
            "independent_source_manifest_sha256",
            "expected_estimand_count_supported",
            "estimate_path_qualification_case_count",
            "interval_path_qualification_case_count",
            "decision_path_qualification_case_count",
            "repetition_blind_recomputation_verified",
            "all_554_estimands_supported",
            "all_cases_passed",
            "qualified_at_utc",
            "body_sha256",
        ),
        (),
        "cp65-test28-independent-554-estimate-interval-decision-path-qualification-receipt-v1",
        False,
    ),
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "independent_full_32768_recomputation_qualification_receipt.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "qualification_fixture_set_sha256",
            "production_schedule_contract_sha256",
            "raw_record_schema_sha256",
            "stable_projection_schema_sha256",
            "independent_recomputation_source_manifest_sha256",
            "qualification_case_count",
            "expected_request_count_supported",
            "expected_estimand_count_supported",
            "repetition_blind_recomputation_verified",
            "all_cases_passed",
            "qualified_at_utc",
            "body_sha256",
        ),
        (),
        "cp65-test28-independent-full-32768-recomputation-qualification-receipt-v1",
        False,
    ),
    (
        "independent-reviewer-public-key-set",
        "frozen_inputs/independent_reviewer_public_keys.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "protocol_sha256",
            "machine_manifest_sha256",
            "required_reviewer_roles",
            "key_count",
            "ordered_keys",
            "ordered_public_key_identity_sha256s",
            "body_sha256",
        ),
        (
            (
                "ordered_keys",
                (
                    "reviewer_role",
                    "reviewer_identity_sha256",
                    "signature_scheme_id",
                    "authority_id",
                    "public_key_identity_sha256",
                    "modulus_hex",
                    "public_exponent",
                    "valid_from_utc",
                    "valid_until_utc",
                    "row_sha256",
                ),
            ),
        ),
        "cp65-test28-independent-reviewer-public-key-set-v1",
        False,
    ),
    (
        "seed-source-authority-public-key",
        "frozen_inputs/seed_source_authority_public_key.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "source_authority_scheme_id",
            "source_authority_id",
            "modulus_hex",
            "public_exponent",
            "valid_from_utc",
            "valid_until_utc",
            "body_sha256",
        ),
        (),
        "cp65-test28-seed-source-authority-public-key-v1",
        False,
    ),
    (
        "seed-source-authority-attestation",
        "seed_source_authority_attestation.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "acquisition_start_receipt_sha256",
            "acquisition_journal_sha256",
            "acquisition_journal_head_sha256",
            "acquisition_journal_entry_count",
            "ordered_seed_values_commitment_sha256",
            "seed_source_custody_artifact_sha256",
            "source_method_id",
            "source_authority_scheme_id",
            "source_authority_identity_sha256",
            "attested_at_utc",
            "attestation_expires_at_utc",
            "source_authority_signature_hex",
            "source_authority_signature_sha256",
            "body_sha256",
        ),
        (),
        "cp65-test28-seed-source-authority-attestation-v1",
        False,
    ),
    (
        "frozen-source-fixture-materialization",
        "frozen_inputs/source_fixture_materialization.bin",
        "global",
        "frozen-input-binary-archive",
        (),
        (),
        "cp65-test28-frozen-source-fixture-materialization-v1",
        False,
    ),
    (
        "production-schema-preimage-validator-bundle",
        "frozen_inputs/production_schema_preimage_validator_bundle.json",
        "global",
        "frozen-input-canonical-json",
        (),
        (),
        "",
        False,
    ),
    (
        "power-review-signoff",
        "power_review_signoff.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "protocol_sha256",
            "machine_manifest_sha256",
            "power_review_sha256",
            "selected_count_justification_sha256",
            "primary_slot_count",
            "ordered_slot_threshold_row_sha256s",
            "ordered_slot_thresholds_sha256",
            "reviewer_role",
            "reviewer_identity_sha256",
            "reviewer_public_key_identity_sha256",
            "decision",
            "signed_at_utc",
            "signature_scheme_id",
            "reviewer_signature_sha256",
            "reviewer_signature_hex",
            "body_sha256",
        ),
        (),
        "cp65-test28-power-review-signoff-v1",
        False,
    ),
    (
        "preterminal-durable-artifact-inventory",
        "preterminal_durable_artifact_inventory.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "terminal_arm",
            "auxiliary_transition_journal_prefix_entry_count",
            "auxiliary_transition_journal_prefix_head_sha256",
            "entry_count",
            "entries",
            "ordered_entries_sha256",
            "created_at_utc",
            "body_sha256",
        ),
        (("entries", ("ordinal", "path", "bytes", "sha256", "entry_sha256")),),
        "cp65-test28-preterminal-durable-artifact-inventory-v1",
        False,
    ),
    (
        "external-digest-preimage-registry",
        "external_digest_preimage_registry.json",
        "global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "protocol_sha256",
            "machine_manifest_sha256",
            "schema_semantic_sha256",
            "entry_count",
            "entries",
            "ordered_entry_sha256s",
            "ordered_entries_sha256",
            "finalized_at_utc",
            "body_sha256",
        ),
        (
            (
                "entries",
                (
                    "ordinal",
                    "classification_id",
                    "target_artifact_id",
                    "target_relative_path",
                    "target_json_pointer",
                    "target_instance_selector_json_ascii",
                    "target_artifact_raw_sha256",
                    "digest_kind",
                    "domain_separator",
                    "preimage_encoding",
                    "preimage_bytes",
                    "preimage_ascii",
                    "digest_sha256",
                    "entry_sha256",
                ),
            ),
        ),
        "cp65-test28-external-digest-preimage-registry-v1",
        False,
    ),
    (
        "auxiliary-reservation-transition-journal",
        "auxiliary_reservation_transition_journal.bin",
        "global",
        "binary-transition-journal",
        (),
        (),
        "cp65-test28-auxiliary-reservation-transition-entry-v1",
        False,
    ),
    (
        "shard-requests",
        "shards/{shard_id}/requests.jsonl",
        "per-shard",
        "referenced-predecessor-jsonl",
        (),
        (),
        "",
        True,
    ),
    (
        "shard-raw-records",
        "shards/{shard_id}/raw_records.jsonl",
        "per-shard",
        "referenced-predecessor-jsonl",
        (),
        (),
        "",
        True,
    ),
    (
        "shard-stable-traces",
        "shards/{shard_id}/stable_traces.jsonl",
        "per-shard",
        "referenced-predecessor-jsonl",
        (),
        (),
        "",
        True,
    ),
    (
        "shard-stderr-records",
        "shards/{shard_id}/stderr_records.bin",
        "per-shard",
        "referenced-predecessor-binary-frames",
        (),
        (),
        "",
        True,
    ),
    (
        "shard-rng-initial-states",
        "shards/{shard_id}/rng_initial_states.json",
        "per-shard",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "shard-rng-final-states",
        "shards/{shard_id}/rng_final_states.json",
        "per-shard",
        "referenced-production-output-canonical-json",
        (),
        (),
        "",
        True,
    ),
    (
        "shard-index",
        "shards/{shard_id}/shard_index.json",
        "per-shard",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "shard_id",
            "shard_record_sha256",
            "request_count",
            "ordered_request_entries",
            "raw_file_sha256",
            "stable_file_sha256",
            "stderr_file_sha256",
            "rng_initial_file_sha256",
            "rng_final_file_sha256",
            "created_at_utc",
            "body_sha256",
        ),
        (
            (
                "ordered_request_entries",
                (
                    "logical_request_ordinal",
                    "request_offset",
                    "request_length",
                    "request_sha256",
                    "raw_offset",
                    "raw_length",
                    "raw_sha256",
                    "stable_offset",
                    "stable_length",
                    "stable_sha256",
                    "stderr_offset",
                    "stderr_frame_length",
                    "stderr_payload_length",
                    "stderr_sha256",
                    "rng_initial_sha256",
                    "rng_final_sha256",
                    "row_sha256",
                ),
            ),
        ),
        "cp65-test28-shard-index-v1",
        False,
    ),
    (
        "shard-receipt",
        "shards/{shard_id}/shard_receipt.json",
        "per-shard",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "shard_id",
            "production_shard_map_receipt_sha256",
            "shard_index_sha256",
            "requests_file_sha256",
            "raw_file_sha256",
            "stable_file_sha256",
            "stderr_file_sha256",
            "rng_initial_file_sha256",
            "rng_final_file_sha256",
            "request_count",
            "terminal_counts",
            "committed_at_utc",
            "body_sha256",
        ),
        (
            (
                "terminal_counts",
                (
                    "returned_rejection_selected_before_deadline",
                    "returned_rejection_exhausted_before_deadline",
                    "returned_sir_selected_before_deadline",
                    "preexecution_refusal_before_deadline",
                    "execution_failure_before_deadline",
                    "timeout_censored_at_deadline",
                ),
            ),
        ),
        "cp65-test28-shard-receipt-v1",
        False,
    ),
    (
        "partial-seed-acquisition-terminal-receipt",
        "seed_partial_acquisition_terminal_receipt.json",
        "conditional-global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "freeze_receipt_sha256",
            "acquisition_start_receipt_sha256",
            "source_method_id",
            "expected_seed_count",
            "acquired_seed_count",
            "acquisition_journal_sha256",
            "acquisition_journal_head_sha256",
            "acquisition_journal_entry_count",
            "acquisition_journal_raw_bytes",
            "seed_encoding",
            "ordered_partial_seed_values",
            "ordered_partial_seed_values_commitment_sha256",
            "terminal_state",
            "topup_redraw_reselection_permitted",
            "body_sha256",
        ),
        (),
        "cp64-test28-partial-acquisition-terminal-receipt-v1",
        True,
    ),
    (
        "rejected-launch-authorization-candidate",
        "rejected_launch_authorization_candidate.json",
        "conditional-global",
        "receipt-envelope-canonical-json",
        (
            "schema",
            "purpose",
            "attempt_id",
            "attempt_state",
            "protocol_sha256",
            "machine_manifest_sha256",
            "source_manifest_sha256",
            "dependency_lock_sha256",
            "seed_source_receipt_sha256",
            "seed_capsule_body_sha256",
            "schedule_sha256",
            "production_runtime_receipt_sha256",
            "capacity_receipt_sha256",
            "durability_receipt_sha256",
            "production_shard_map_receipt_sha256",
            "preflight_gate_summary_sha256",
            "power_threshold_receipt_sha256",
            "freeze_receipt_sha256",
            "independent_signoff_sha256",
            "authorized_attempt_number",
            "authorization_issued_at_utc",
            "authorization_expires_at_utc",
            "authority_scheme_id",
            "authority_identity_sha256",
            "authority_signature_hex",
            "authority_signature_sha256",
            "body_sha256",
        ),
        (),
        "cp65-test28-launch-authorization-receipt-v2",
        False,
    ),
)

_I_BOOLEAN_KEYS = frozenset(
    {
        "all_554_estimands_supported",
        "all_cases_passed",
        "all_closed_arms_reachable",
        "all_decisions_approve",
        "all_required_roles_present",
        "all_signatures_mathematically_valid_under_declared_keys",
        "allocation_and_directory_charge_within_policy",
        "atomic_rename_supported",
        "atomic_rename_verified",
        "auxiliary_metadata_non_sparse_allocation_verified",
        "auxiliary_metadata_reservation_durable_verified",
        "auxiliary_metadata_reservation_exclusive_verified",
        "auxiliary_metadata_reservation_same_storage_root_verified",
        "auxiliary_metadata_reserved_quota_verified",
        "definition_only",
        "destination_and_auxiliary_reservation_no_double_count_verified",
        "directory_fsync_supported",
        "directory_fsync_verified",
        "durable_verified",
        "exclusive_create_verified",
        "exclusive_verified",
        "file_fsync_supported",
        "file_fsync_verified",
        "hold_absence_verified",
        "match_verified",
        "no_hardlink_verified",
        "no_overwrite_verified",
        "no_symlink_verified",
        "non_sparse_allocation_verified",
        "non_sparse_verified",
        "production_execution_authorized",
        "production_runner_rng_or_child_started_before_receipt",
        "repetition_blind_recomputation_verified",
        "reservation_durable_verified",
        "reservation_exclusive_verified",
        "reservation_same_filesystem_verified",
        "same_root_verified",
        "sequence_equal",
        "topup_redraw_reselection_permitted",
        "unknown_codes_rejected",
    }
)

_I_ARRAY_KEYS = frozenset(
    {
        "artifact_entries",
        "closed_failure_codes",
        "closed_refusal_codes",
        "covered_evidence_node_ids",
        "covered_gate_ids",
        "covered_gate_states",
        "entries",
        "ordered_entry_sha256s",
        "ordered_evidence_receipt_sha256s",
        "ordered_keys",
        "ordered_partial_seed_values",
        "ordered_public_key_identity_sha256s",
        "ordered_request_entries",
        "ordered_request_record_sha256s",
        "ordered_seed_values",
        "ordered_signoffs",
        "ordered_slot_threshold_row_sha256s",
        "ordered_slot_thresholds",
        "per_file_reservation_manifest_entry_sha256s",
        "requests",
        "required_reviewer_roles",
        "reviewed_artifact_sha256s",
        "seed_ordinals",
        "shards",
    }
)

_I_INTEGER_EXACT = {
    ("seed-capsule-body", "seed_count"): 2048,
    ("external-seed-source-receipt", "seed_count"): 2048,
    ("external-seed-source-receipt", "acquisition_journal_entry_count"): 2048,
    ("partial-seed-acquisition-terminal-receipt", "expected_seed_count"): 2048,
    ("seed-source-authority-attestation", "acquisition_journal_entry_count"): 2048,
    ("seed-capsule-sequence-crosscheck-receipt", "seed_count"): 2048,
    ("production-schedule", "request_count"): 32768,
    ("production-shard-map-receipt", "shard_count"): 32,
    ("production-shard-map-receipt", "logical_request_count"): 1024,
    ("shard-index", "request_count"): 1024,
    ("shard-receipt", "request_count"): 1024,
    ("power-threshold-receipt", "primary_slot_count"): 32,
    ("power-review-signoff", "primary_slot_count"): 32,
    ("power-threshold-receipt", "design_minimum_selected_count"): 1040,
    ("capacity-receipt", "shard_count"): 32,
    ("reservation-manifest", "entry_count"): 128,
    ("independent-signoff-set", "signoff_count"): 4,
    ("independent-reviewer-public-key-set", "key_count"): 4,
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "expected_request_count_supported",
    ): 32768,
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "expected_estimand_count_supported",
    ): 554,
    (
        "independent-554-estimate-interval-decision-path-qualification-receipt",
        "expected_estimand_count_supported",
    ): 554,
    ("launch-authority-public-key", "public_exponent"): 65537,
    ("seed-source-authority-public-key", "public_exponent"): 65537,
    ("independent-reviewer-public-key-set", "public_exponent"): 65537,
    ("auxiliary-metadata-reservation", "required_bytes"): 34359738368,
    ("capacity-receipt", "destination_reservation_required_bytes"): 1099511627776,
    ("capacity-receipt", "auxiliary_metadata_reservation_required_bytes"): 34359738368,
    (
        "capacity-receipt",
        "combined_available_and_quota_required_before_reservation_bytes",
    ): 1133871366144,
    (
        "capacity-receipt",
        "available_and_quota_required_after_destination_before_auxiliary_reservation_bytes",
    ): 34359738368,
    ("capacity-receipt", "maximum_auxiliary_artifact_logical_bytes"): 21845344321,
    ("capacity-receipt", "maximum_auxiliary_reserved_bytes"): 23286841344,
    (
        "capacity-receipt",
        "allocation_and_directory_charge_policy_slot_bytes",
    ): 1073741824,
    ("auxiliary-metadata-reservation", "artifact_entry_count"): 183,
    ("auxiliary-metadata-reservation", "artifact_slot_reserved_bytes"): 22213099520,
    (
        "auxiliary-metadata-reservation",
        "allocation_and_directory_charge_policy_slot_bytes",
    ): 1073741824,
    (
        "auxiliary-metadata-reservation",
        "exclusive_reserved_headroom_bytes",
    ): 11072897024,
}

_I_INTEGER_INTERVALS = {
    (
        "preterminal-durable-artifact-inventory",
        "/auxiliary_transition_journal_prefix_entry_count",
    ): (0, 251),
    ("terminal-state", "/auxiliary_transition_journal_after_inventory_entry_count"): (
        1,
        252,
    ),
    ("sha256-manifest", "/auxiliary_transition_journal_after_terminal_entry_count"): (
        2,
        253,
    ),
    (
        "committed-marker",
        "/auxiliary_reservation_transition_journal_final_entry_count",
    ): (4, 255),
    ("preterminal-durable-artifact-inventory", "/entry_count"): (1, 312),
    ("sha256-manifest", "/entry_count"): (1, 312),
    ("external-digest-preimage-registry", "/entry_count"): (0, 4096),
}

_I_ARRAY_LENGTH_EXACT = {
    ("seed-capsule-body", "seed_ordinals"): 2048,
    ("seed-capsule-body", "ordered_seed_values"): 2048,
    ("production-schedule", "requests"): 32768,
    ("production-schedule", "ordered_request_record_sha256s"): 32768,
    ("production-shard-map-receipt", "shards"): 32,
    ("power-threshold-receipt", "ordered_slot_thresholds"): 32,
    ("power-threshold-receipt", "ordered_slot_threshold_row_sha256s"): 32,
    ("preflight-gate-summary", "covered_gate_ids"): 15,
    ("preflight-gate-summary", "covered_gate_states"): 15,
    ("preflight-gate-summary", "covered_evidence_node_ids"): 15,
    ("preflight-gate-summary", "ordered_evidence_receipt_sha256s"): 15,
    ("independent-signoff-set", "required_reviewer_roles"): 4,
    ("independent-signoff-set", "ordered_signoffs"): 4,
    ("independent-reviewer-public-key-set", "required_reviewer_roles"): 4,
    (
        "closed-refusal-failure-classifier-qualification-receipt",
        "closed_refusal_codes",
    ): 5,
    (
        "closed-refusal-failure-classifier-qualification-receipt",
        "closed_failure_codes",
    ): 7,
    ("shard-index", "ordered_request_entries"): 1024,
    ("auxiliary-metadata-reservation", "artifact_entries"): 183,
    ("reservation-manifest", "entries"): 128,
    ("production-shard-map-receipt", "per_file_reservation_manifest_entry_sha256s"): 4,
    ("independent-reviewer-public-key-set", "ordered_keys"): 4,
    ("independent-reviewer-public-key-set", "ordered_public_key_identity_sha256s"): 4,
    ("power-review-signoff", "ordered_slot_threshold_row_sha256s"): 32,
}

_I_PURPOSE_BY_ARTIFACT = {
    "source-manifest": "frozen-source-fixture-materialization-custody",
    "freeze-receipt": "attempt-frozen-input-closure",
    "power-threshold-receipt": "production-power-review-and-primary-threshold-freeze",
    "preflight-gate-summary": "preauthorization-gates-1-through-15-summary",
    "independent-signoff-set": "independent-preauthorization-signoff-set",
    "capacity-receipt": "production-capacity-and-exclusive-reservation-observation",
    "auxiliary-metadata-reservation": "exclusive-dynamic-auxiliary-reservation",
    "reservation-manifest": "destination-and-auxiliary-reservation-manifest",
    "production-runtime-receipt": "production-runtime-lock-observation",
    "external-seed-acquisition-start-receipt": "durable-start-before-external-source-contact",
    "external-seed-source-receipt": "completed-external-seed-source-custody",
    "seed-capsule-body": "future-production-external-iid-uniform-uint64-with-replacement",
    "production-shard-map-receipt": "candidate-production-shard-map-custody",
    "durability-receipt": "production-writer-durability-qualification",
    "preauthorization-outcome": "preauthorization-atomic-outcome",
    "launch-authorization": "explicit-production-launch-authorization",
    "postauthorization-outcome": "postauthorization-prestart-atomic-outcome",
    "started-receipt": "production-started-custody",
    "launch-receipt": "production-launch-custody",
    "terminal-state": "attempt-terminal-state-publication",
    "sha256-manifest": "terminal-corpus-sha256-manifest",
    "committed-marker": "final-corpus-publication-after-sealed-transition-journal-and-hold-release",
    "launch-authority-public-key": "launch-authority-public-key-custody",
    "dependency-lock-match-receipt": "dependency-lock-match-observation",
    "seed-source-custody-artifact": "external-seed-source-custody-preimage",
    "seed-capsule-sequence-crosscheck-receipt": "seed-capsule-sequence-crosscheck",
    "production-schedule": "production-request-schedule-custody",
    "production-runner-supervisor-qualification-receipt": "production-runner-supervisor-qualification",
    "closed-refusal-failure-classifier-qualification-receipt": "closed-refusal-failure-classifier-qualification",
    "independent-554-estimate-interval-decision-path-qualification-receipt": "independent-554-estimate-interval-decision-path-qualification",
    "independent-full-32768-recomputation-qualification-receipt": "independent-full-32768-recomputation-qualification",
    "independent-reviewer-public-key-set": "independent-reviewer-public-key-set-custody",
    "seed-source-authority-public-key": "seed-source-authority-public-key-custody",
    "seed-source-authority-attestation": "external-seed-source-authority-attestation",
    "power-review-signoff": "signed-power-review-custody",
    "preterminal-durable-artifact-inventory": "preterminal-durable-artifact-inventory",
    "external-digest-preimage-registry": "post-gate15-pre-summary-bounded-external-digest-preimage-custody",
    "shard-index": "production-shard-index-custody",
    "shard-receipt": "production-shard-terminal-custody",
    "partial-seed-acquisition-terminal-receipt": "terminal-custody-of-recovered-prefix",
    "rejected-launch-authorization-candidate": "rejected-launch-authorization-candidate-custody",
}

_I_STRING_DOMAINS = {
    ("source-manifest", "purpose"): ("frozen-source-fixture-materialization-custody",),
    ("freeze-receipt", "purpose"): ("attempt-frozen-input-closure",),
    ("power-threshold-receipt", "purpose"): (
        "production-power-review-and-primary-threshold-freeze",
    ),
    ("preflight-gate-summary", "purpose"): (
        "preauthorization-gates-1-through-15-summary",
    ),
    ("independent-signoff-set", "purpose"): (
        "independent-preauthorization-signoff-set",
    ),
    ("capacity-receipt", "purpose"): (
        "production-capacity-and-exclusive-reservation-observation",
    ),
    ("auxiliary-metadata-reservation", "purpose"): (
        "exclusive-dynamic-auxiliary-reservation",
    ),
    ("reservation-manifest", "purpose"): (
        "destination-and-auxiliary-reservation-manifest",
    ),
    ("production-runtime-receipt", "purpose"): ("production-runtime-lock-observation",),
    ("external-seed-acquisition-start-receipt", "purpose"): (
        "durable-start-before-external-source-contact",
    ),
    ("external-seed-source-receipt", "purpose"): (
        "completed-external-seed-source-custody",
    ),
    ("seed-capsule-body", "purpose"): (
        "future-production-external-iid-uniform-uint64-with-replacement",
    ),
    ("production-shard-map-receipt", "purpose"): (
        "candidate-production-shard-map-custody",
    ),
    ("durability-receipt", "purpose"): ("production-writer-durability-qualification",),
    ("preauthorization-outcome", "purpose"): ("preauthorization-atomic-outcome",),
    ("launch-authorization", "purpose"): ("explicit-production-launch-authorization",),
    ("postauthorization-outcome", "purpose"): (
        "postauthorization-prestart-atomic-outcome",
    ),
    ("started-receipt", "purpose"): ("production-started-custody",),
    ("launch-receipt", "purpose"): ("production-launch-custody",),
    ("terminal-state", "purpose"): ("attempt-terminal-state-publication",),
    ("sha256-manifest", "purpose"): ("terminal-corpus-sha256-manifest",),
    ("committed-marker", "purpose"): (
        "final-corpus-publication-after-sealed-transition-journal-and-hold-release",
    ),
    ("launch-authority-public-key", "purpose"): (
        "launch-authority-public-key-custody",
    ),
    ("dependency-lock-match-receipt", "purpose"): (
        "dependency-lock-match-observation",
    ),
    ("seed-source-custody-artifact", "purpose"): (
        "external-seed-source-custody-preimage",
    ),
    ("seed-capsule-sequence-crosscheck-receipt", "purpose"): (
        "seed-capsule-sequence-crosscheck",
    ),
    ("production-schedule", "purpose"): ("production-request-schedule-custody",),
    ("production-runner-supervisor-qualification-receipt", "purpose"): (
        "production-runner-supervisor-qualification",
    ),
    ("closed-refusal-failure-classifier-qualification-receipt", "purpose"): (
        "closed-refusal-failure-classifier-qualification",
    ),
    (
        "independent-554-estimate-interval-decision-path-qualification-receipt",
        "purpose",
    ): ("independent-554-estimate-interval-decision-path-qualification",),
    ("independent-full-32768-recomputation-qualification-receipt", "purpose"): (
        "independent-full-32768-recomputation-qualification",
    ),
    ("independent-reviewer-public-key-set", "purpose"): (
        "independent-reviewer-public-key-set-custody",
    ),
    ("seed-source-authority-public-key", "purpose"): (
        "seed-source-authority-public-key-custody",
    ),
    ("seed-source-authority-attestation", "purpose"): (
        "external-seed-source-authority-attestation",
    ),
    ("power-review-signoff", "purpose"): ("signed-power-review-custody",),
    ("preterminal-durable-artifact-inventory", "purpose"): (
        "preterminal-durable-artifact-inventory",
    ),
    ("external-digest-preimage-registry", "purpose"): (
        "post-gate15-pre-summary-bounded-external-digest-preimage-custody",
    ),
    ("shard-index", "purpose"): ("production-shard-index-custody",),
    ("shard-receipt", "purpose"): ("production-shard-terminal-custody",),
    ("partial-seed-acquisition-terminal-receipt", "purpose"): (
        "terminal-custody-of-recovered-prefix",
    ),
    ("rejected-launch-authorization-candidate", "purpose"): (
        "rejected-launch-authorization-candidate-custody",
    ),
    ("freeze-receipt", "from_state"): ("DRAFT_PRE_FREEZE",),
    ("freeze-receipt", "to_state"): ("FROZEN",),
    ("launch-authorization", "attempt_state"): ("FROZEN",),
    ("rejected-launch-authorization-candidate", "attempt_state"): ("FROZEN",),
    ("seed-capsule-body", "seed_encoding"): ("uint64-16-lowercase-hex-big-endian",),
    ("external-seed-source-receipt", "seed_encoding"): (
        "uint64-16-lowercase-hex-big-endian",
    ),
    ("partial-seed-acquisition-terminal-receipt", "seed_encoding"): (
        "uint64-16-lowercase-hex-big-endian",
    ),
    ("partial-seed-acquisition-terminal-receipt", "terminal_state"): ("INCOMPLETE",),
    ("launch-authority-public-key", "authority_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("launch-authorization", "authority_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("rejected-launch-authorization-candidate", "authority_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("seed-source-authority-public-key", "source_authority_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("seed-source-authority-attestation", "source_authority_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("independent-reviewer-public-key-set", "signature_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("independent-signoff-set", "signature_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("power-review-signoff", "signature_scheme_id"): (
        "rsa-pss-sha256-3072-e65537-salt32-v1",
    ),
    ("independent-reviewer-public-key-set", "reviewer_role"): (
        "protocol-and-provenance-reviewer",
        "runtime-and-durability-reviewer",
        "statistical-power-and-decision-reviewer",
        "independent-recomputation-reviewer",
    ),
    ("independent-signoff-set", "reviewer_role"): (
        "protocol-and-provenance-reviewer",
        "runtime-and-durability-reviewer",
        "statistical-power-and-decision-reviewer",
        "independent-recomputation-reviewer",
    ),
    ("power-review-signoff", "reviewer_role"): (
        "statistical-power-and-decision-reviewer",
    ),
    ("independent-signoff-set", "decision"): ("APPROVE",),
    ("power-review-signoff", "decision"): ("APPROVE",),
    ("auxiliary-metadata-reservation", "hold_relative_path"): (
        ".cp65_auxiliary_reservation_hold.partial",
    ),
    ("auxiliary-metadata-reservation", "reservation_state"): (
        "existing-final-in-place",
        "preallocated-partial-in-place",
        "preallocated-live-journal-in-place",
        "future-o-excl-covered-by-hold",
    ),
    ("preauthorization-outcome", "outcome_arm"): (
        "AUTHORIZATION",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    ),
    ("postauthorization-outcome", "outcome_arm"): (
        "STARTED",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    ),
    ("terminal-state", "terminal_arm"): (
        "PREAUTHORIZATION",
        "POSTAUTHORIZATION_PRESTART",
        "STARTED",
    ),
    ("preterminal-durable-artifact-inventory", "terminal_arm"): (
        "PREAUTHORIZATION",
        "POSTAUTHORIZATION_PRESTART",
        "STARTED",
    ),
    ("terminal-state", "previous_lifecycle_state"): ("FROZEN", "STARTED"),
    ("terminal-state", "terminal_state"): (
        "PASS",
        "FAIL",
        "INVALID_PROTOCOL",
        "ABORTED_INFRA",
        "INCOMPLETE",
    ),
    ("terminal-state", "reason_code"): (
        "completed-as-preregistered",
        "primary-or-structural-failure",
        "frozen-input-or-protocol-invalid",
        "infrastructure-abort",
        "attempt-incomplete",
    ),
    ("external-digest-preimage-registry", "digest_kind"): (
        "plain-sha256",
        "domain-separated-sha256",
    ),
    ("external-digest-preimage-registry", "preimage_encoding"): (
        "ascii",
        "lowercase-hex",
    ),
    ("seed-source-custody-artifact", "custody_media_type"): (
        "application/octet-stream",
    ),
    ("seed-source-custody-artifact", "custody_encoding"): ("identity",),
    ("seed-capsule-sequence-crosscheck-receipt", "seed_encoding"): (
        "uint64-16-lowercase-hex-big-endian",
    ),
    ("production-runtime-receipt", "runtime_profile_id"): (
        "cp62-darwin-arm64-cpython3115-numpy246-scipy1171-calibration",
    ),
}

_I_ROW_INVENTORY = (
    (
        1,
        "row-01/T28-M1-Q/bounded-rejection/budget-1",
        "T28-M1-Q",
        "bounded-rejection",
        1,
        "a99bafb93499e89d054dd8e0df8c9a04acff29142620a7da374aa88dae53215a",
    ),
    (
        2,
        "row-02/T28-M1-Q/bounded-rejection/budget-4",
        "T28-M1-Q",
        "bounded-rejection",
        4,
        "f9f2d4f1d8aad14bbe5075b4febd763af4652fb4dda337e7a8d295b3a6045ec2",
    ),
    (
        3,
        "row-03/T28-M1-Q/bounded-rejection/budget-16",
        "T28-M1-Q",
        "bounded-rejection",
        16,
        "4413d707c0165dbf18e88df043edd760a75d4eed44d039a611402e06de9c4eb8",
    ),
    (
        4,
        "row-04/T28-M1-Q/bounded-rejection/budget-64",
        "T28-M1-Q",
        "bounded-rejection",
        64,
        "29f1f28fb222d258746cb7956a9ca0d65a6e97d398eddb1612720a9339eed338",
    ),
    (
        5,
        "row-05/T28-M1-Q/fixed-budget-sir/budget-8",
        "T28-M1-Q",
        "fixed-budget-sir",
        8,
        "71701768f889fee219b854217de255f3d034202a3a66875ceade1cd55955896a",
    ),
    (
        6,
        "row-06/T28-M1-Q/fixed-budget-sir/budget-32",
        "T28-M1-Q",
        "fixed-budget-sir",
        32,
        "bd7c4fd661bda70f29b8582c0db52d91d68fc703ae8838295a21cf9e6e55f23a",
    ),
    (
        7,
        "row-07/T28-M1-Q/fixed-budget-sir/budget-128",
        "T28-M1-Q",
        "fixed-budget-sir",
        128,
        "801f600536240a2f6f3de0dcac8d4092c2121fd17dc14fb0ca0bfc3b0260acb8",
    ),
    (
        8,
        "row-08/T28-M1-Q/fixed-budget-sir/budget-512",
        "T28-M1-Q",
        "fixed-budget-sir",
        512,
        "8e5458a8dfca1e49875cad53deff7447274ce3055960a0031cc07c4ec4de33e0",
    ),
    (
        9,
        "row-09/T28-M2-Q/bounded-rejection/budget-1",
        "T28-M2-Q",
        "bounded-rejection",
        1,
        "7d32b4e85d39504864268b7ba39189f17c3171d11079638e37a6614b97a543bf",
    ),
    (
        10,
        "row-10/T28-M2-Q/bounded-rejection/budget-4",
        "T28-M2-Q",
        "bounded-rejection",
        4,
        "17f11b448585709ef35a172e86665c83b2ea50a907caacdd400dbd8ce625771b",
    ),
    (
        11,
        "row-11/T28-M2-Q/bounded-rejection/budget-16",
        "T28-M2-Q",
        "bounded-rejection",
        16,
        "57937405e7302fcd9b9935050050a74e4b2c2818e17d720cde1ee2a56352bcf3",
    ),
    (
        12,
        "row-12/T28-M2-Q/bounded-rejection/budget-64",
        "T28-M2-Q",
        "bounded-rejection",
        64,
        "878797b61ec628ae5db0e882d6f3c34531468fbbc35fd92325063a3b017c1bd8",
    ),
    (
        13,
        "row-13/T28-M2-Q/fixed-budget-sir/budget-8",
        "T28-M2-Q",
        "fixed-budget-sir",
        8,
        "bc7b374f072aa402264634bcf520834a71609af5f6705b9b8ac3079884cd0376",
    ),
    (
        14,
        "row-14/T28-M2-Q/fixed-budget-sir/budget-32",
        "T28-M2-Q",
        "fixed-budget-sir",
        32,
        "1b60b917c4fba30085678101276fe2a210aaa82f34deb6ad4f9440a38cc3b074",
    ),
    (
        15,
        "row-15/T28-M2-Q/fixed-budget-sir/budget-128",
        "T28-M2-Q",
        "fixed-budget-sir",
        128,
        "a88491906e47ec4f5483b638ce411b8afd4ce7b5d73f19e372ab68a405f6d81c",
    ),
    (
        16,
        "row-16/T28-M2-Q/fixed-budget-sir/budget-512",
        "T28-M2-Q",
        "fixed-budget-sir",
        512,
        "0667c6c19a9b54db91f2167f685abdcaafcab73cbc4bcfaebcb420511ecc89c8",
    ),
)

_I_NESTED_DIGESTS = {
    ("external-digest-preimage-registry", "entries"): (
        "entry_sha256",
        "cp65-test28-external-digest-preimage-registry-entry-v1",
    ),
    ("auxiliary-metadata-reservation", "artifact_entries"): (
        "entry_sha256",
        "cp65-test28-auxiliary-metadata-reservation-entry-v3",
    ),
    ("power-threshold-receipt", "ordered_slot_thresholds"): (
        "row_sha256",
        "cp65-test28-power-threshold-row-v1",
    ),
    ("independent-signoff-set", "ordered_signoffs"): (
        "signoff_sha256",
        "cp65-test28-independent-signoff-row-v1",
    ),
    ("reservation-manifest", "entries"): (
        "entry_sha256",
        "cp65-test28-reservation-manifest-entry-v1",
    ),
    ("production-shard-map-receipt", "shards"): (
        "shard_record_sha256",
        "cp64-test28-production-shard-map-shard-record-v1",
    ),
    ("production-schedule", "requests"): (
        "request_row_sha256",
        "cp65-test28-production-schedule-request-row-v1",
    ),
    ("independent-reviewer-public-key-set", "ordered_keys"): (
        "row_sha256",
        "cp65-test28-independent-reviewer-public-key-row-v1",
    ),
    ("shard-index", "ordered_request_entries"): (
        "row_sha256",
        "cp65-test28-shard-index-request-entry-v1",
    ),
    ("preterminal-durable-artifact-inventory", "entries"): (
        "entry_sha256",
        "cp65-test28-preterminal-durable-artifact-inventory-entry-v1",
    ),
}

_I_INTERNAL_DIGEST_DECLARATIONS = (
    (
        "seed-capsule-body:ordered-seed-sequence",
        "seed-capsule-body",
        "/ordered_seed_values",
        "cp64-test28-ordered-seed-sequence-v1",
        (),
        (),
    ),
    (
        "power-threshold-receipt:power-review-text",
        "power-threshold-receipt",
        "/power_review_sha256",
        "cp65-test28-power-review-text-v1",
        (),
        (),
        "exact-ascii-bytes-v1",
    ),
    (
        "power-threshold-receipt:selected-count-justification-text",
        "power-threshold-receipt",
        "/selected_count_justification_sha256",
        "cp65-test28-selected-count-justification-v1",
        (),
        (),
        "exact-ascii-bytes-v1",
    ),
    (
        "power-threshold-receipt:threshold-row-justification-text",
        "power-threshold-receipt",
        "/ordered_slot_thresholds/*/justification_sha256",
        "cp65-test28-threshold-row-justification-v1",
        (),
        (),
        "exact-ascii-bytes-v1",
    ),
    (
        "power-threshold-receipt:ordered-threshold-rows",
        "power-threshold-receipt",
        "/ordered_slot_thresholds_sha256",
        "cp65-test28-power-threshold-rows-v1",
        (),
        ("power-threshold-receipt:ordered_slot_thresholds-row-digest",),
    ),
    (
        "production-schedule:ordered-request-records",
        "production-schedule",
        "/ordered_requests_sha256",
        "cp65-test28-production-schedule-ordered-requests-v1",
        (),
        ("production-schedule:requests-row-digest",),
    ),
    (
        "source-manifest:ordered-entries",
        "source-manifest",
        "/ordered_entries_sha256",
        "cp65-test28-source-manifest-ordered-entries-v1",
        (),
        (),
    ),
    (
        "external-digest-preimage-registry:ordered-entries",
        "external-digest-preimage-registry",
        "/ordered_entries_sha256",
        "cp65-test28-external-digest-preimage-registry-ordered-entries-v1",
        (),
        ("external-digest-preimage-registry:entries-row-digest",),
    ),
    (
        "launch-authority-public-key:identity",
        "launch-authority-public-key",
        "$public_key_identity",
        "cp65-test28-launch-authority-public-key-identity-v1",
        (),
        (),
    ),
    (
        "seed-source-authority-public-key:identity",
        "seed-source-authority-public-key",
        "$public_key_identity",
        "cp65-test28-seed-source-authority-public-key-identity-v1",
        (),
        (),
    ),
    (
        "independent-reviewer-public-key-set:key-identity",
        "independent-reviewer-public-key-set",
        "/ordered_keys/*/public_key_identity_sha256",
        "cp65-test28-independent-reviewer-public-key-identity-v1",
        (),
        (),
    ),
    (
        "launch-authorization:unsigned-preimage",
        "launch-authorization",
        "$unsigned_preimage",
        "cp65-test28-launch-authorization-signature-preimage-v1",
        ("/authority_signature_hex", "/authority_signature_sha256", "/body_sha256"),
        (),
    ),
    (
        "launch-authorization:raw-signature",
        "launch-authorization",
        "/authority_signature_sha256",
        "",
        (),
        (),
    ),
    (
        "launch-authorization-candidate:prepared-raw-sha256",
        "launch-authorization",
        "$prepared_candidate_raw_sha256",
        "",
        (),
        ("launch-authorization:body-sha256",),
        "prepared-canonical-launch-authorization-bytes-v1",
    ),
    (
        "rejected-launch-authorization-candidate:raw-sha256",
        "rejected-launch-authorization-candidate",
        "$raw_sha256",
        "",
        (),
        ("launch-authorization-candidate:prepared-raw-sha256",),
        "byte-identical-prepared-candidate-published-to-rejected-path-v1",
    ),
    (
        "seed-source-authority-attestation:unsigned-preimage",
        "seed-source-authority-attestation",
        "$unsigned_preimage",
        "cp65-test28-seed-source-authority-attestation-signature-preimage-v1",
        (
            "/source_authority_signature_hex",
            "/source_authority_signature_sha256",
            "/body_sha256",
        ),
        (),
    ),
    (
        "seed-source-authority-attestation:raw-signature",
        "seed-source-authority-attestation",
        "/source_authority_signature_sha256",
        "",
        (),
        (),
    ),
    (
        "independent-signoff-set:row-unsigned-preimage",
        "independent-signoff-set",
        "/ordered_signoffs/*/$unsigned_preimage",
        "cp65-test28-independent-signoff-row-signature-preimage-v1",
        (
            "/ordered_signoffs/*/reviewer_signature_hex",
            "/ordered_signoffs/*/reviewer_signature_sha256",
            "/ordered_signoffs/*/signoff_sha256",
        ),
        (),
    ),
    (
        "independent-signoff-set:row-raw-signature",
        "independent-signoff-set",
        "/ordered_signoffs/*/reviewer_signature_sha256",
        "",
        (),
        (),
    ),
    (
        "power-review-signoff:unsigned-preimage",
        "power-review-signoff",
        "$unsigned_preimage",
        "cp65-test28-power-review-signoff-signature-preimage-v1",
        ("/reviewer_signature_hex", "/reviewer_signature_sha256", "/body_sha256"),
        (),
    ),
    (
        "power-review-signoff:raw-signature",
        "power-review-signoff",
        "/reviewer_signature_sha256",
        "",
        (),
        (),
    ),
    (
        "external-seed-acquisition-journal:entry",
        "external-seed-acquisition-journal",
        "$entry_sha256",
        "cp64-external-seed-acquisition-journal-entry-v1",
        (),
        (),
    ),
    (
        "external-seed-acquisition-journal:head",
        "external-seed-acquisition-journal",
        "$journal_head_sha256",
        "cp64-external-seed-acquisition-journal-head-v1",
        (),
        ("external-seed-acquisition-journal:entry",),
    ),
    (
        "sha256-manifest:ordered-entries",
        "sha256-manifest",
        "/ordered_entries_sha256",
        "cp65-test28-sha256-manifest-ordered-entries-v1",
        (),
        (),
    ),
    (
        "preterminal-durable-artifact-inventory:ordered-entries",
        "preterminal-durable-artifact-inventory",
        "/ordered_entries_sha256",
        "cp65-test28-preterminal-durable-artifact-inventory-ordered-entries-v1",
        (),
        ("preterminal-durable-artifact-inventory:entries-row-digest",),
    ),
    (
        "source-manifest:selected-entry-raw-sha256",
        "source-manifest",
        "/entries/*/sha256",
        "",
        (),
        (),
        "path-selected-retained-raw-file-v1",
    ),
    (
        "preterminal-durable-artifact-inventory:selected-entry-raw-sha256",
        "preterminal-durable-artifact-inventory",
        "/entries/*/sha256",
        "",
        (),
        (),
        "path-selected-retained-raw-file-v1",
    ),
    (
        "sha256-manifest:selected-entry-raw-sha256",
        "sha256-manifest",
        "/entries/*/sha256",
        "",
        (),
        (),
        "path-selected-retained-raw-file-v1",
    ),
    (
        "external-digest-preimage-registry:selected-target-raw-sha256",
        "external-digest-preimage-registry",
        "/entries/*/target_artifact_raw_sha256",
        "",
        (),
        (),
        "registry-selected-target-raw-file-v1",
    ),
    (
        "external-digest-preimage-registry:declared-preimage-sha256",
        "external-digest-preimage-registry",
        "/entries/*/digest_sha256",
        "",
        (),
        (),
        "registry-row-declared-preimage-v1",
    ),
    (
        "production-schema-preimage-validator-bundle:schema-semantic-sha256",
        "production-schema-preimage-validator-bundle",
        "$schema_semantic_sha256",
        "cp65-test28-production-schema-semantic-v1",
        (),
        (),
    ),
    (
        "production-schema-preimage-validator-bundle:auxiliary-size-proof-record-sha256",
        "production-schema-preimage-validator-bundle",
        "$auxiliary_size_proof.record_sha256",
        "cp65-auxiliary-size-proof-v1",
        (),
        (),
    ),
    (
        "v15-machine-manifest:cp64-capacity-receipt-schema-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/bundle/capacity_receipt_schema/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp61-stable-design-semantic-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_validated_mc_design/bundle/stable_design_semantic_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp64-candidate-shard-policy-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/bundle/candidate_shard_policy/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp64-durability-receipt-schema-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_production_custody_preflight_scaffold/bundle/durability_receipt_schema/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp63-schedule-contract-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_runner_recomputation_rehearsal/runner_bundle/canonical_record/fields/schedule_contract/fields/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp62-supervisor-contract-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/supervisor_contract/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp63-raw-record-schema-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_runner_recomputation_rehearsal/runner_bundle/canonical_record/fields/raw_record_schema/fields/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp62-projection-contract-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/stable_trace_projection/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "v15-machine-manifest:cp62-runtime-lock-record-sha256",
        "frozen-machine-manifest",
        "/diagnostic_contracts/whole_seed_execution_capsule_and_calibration/runtime_source_abi_lock/record_sha256",
        "",
        (),
        (),
        "selected-stored-lowercase-sha256-reference-v1",
    ),
    (
        "source-manifest:independent-recomputation-submanifest",
        "source-manifest",
        "$independent_recomputation_source_submanifest_sha256",
        "cp65-test28-independent-recomputation-source-submanifest-v1",
        (),
        ("source-manifest:selected-entry-raw-sha256",),
        "role-filtered-ordered-source-manifest-submanifest-v1",
    ),
    (
        "independent-reviewer-public-key-set:selected-reviewer-identity-sha256",
        "independent-reviewer-public-key-set",
        "$selected_reviewer_identity_sha256",
        "",
        (),
        (
            "external-preimage:independent-reviewer-public-key-set:/ordered_keys/*/reviewer_identity_sha256",
        ),
        "role-selected-stored-digest-field-v1",
    ),
    (
        "production-schedule:cp62-seed-free-request-sha256",
        "production-schedule",
        "/requests/*/seed_free_request_sha256",
        "cp62-test28-seed-free-request-v1",
        (),
        (),
    ),
    (
        "production-schedule:request-instance-sha256",
        "production-schedule",
        "/requests/*/request_instance_sha256",
        "cp63-test28-bound-request-v1",
        (),
        (),
    ),
    (
        "shard-index:request-payload-segment-sha256",
        "shard-index",
        "/ordered_request_entries/*/request_sha256",
        "",
        (),
        (),
        "offset-length-selected-payload-bytes-v1",
    ),
    (
        "shard-index:raw-payload-segment-sha256",
        "shard-index",
        "/ordered_request_entries/*/raw_sha256",
        "",
        (),
        (),
        "offset-length-selected-payload-bytes-v1",
    ),
    (
        "shard-index:stable-payload-segment-sha256",
        "shard-index",
        "/ordered_request_entries/*/stable_sha256",
        "",
        (),
        (),
        "offset-length-selected-payload-bytes-v1",
    ),
    (
        "shard-index:stderr-payload-segment-sha256",
        "shard-index",
        "/ordered_request_entries/*/stderr_sha256",
        "",
        (),
        (),
        "length-frame-selected-payload-bytes-v1",
    ),
    (
        "shard-index:rng-initial-state-row-sha256",
        "shard-index",
        "/ordered_request_entries/*/rng_initial_sha256",
        "",
        (),
        (),
        "ordered-rng-container-state-row-v1",
    ),
    (
        "shard-index:rng-final-state-row-sha256",
        "shard-index",
        "/ordered_request_entries/*/rng_final_sha256",
        "",
        (),
        (),
        "ordered-rng-container-state-row-v1",
    ),
    (
        "preflight-gate-summary:selected-evidence-raw-sha256",
        "preflight-gate-summary",
        "/ordered_evidence_receipt_sha256s/*",
        "",
        (),
        (),
        "gate-ordinal-selected-retained-raw-file-v1",
    ),
    (
        "production-shard-map-receipt:selected-reservation-entry-sha256",
        "production-shard-map-receipt",
        "/shards/*/per_file_reservation_manifest_entry_sha256s/*",
        "cp65-test28-reservation-manifest-entry-v1",
        (),
        (),
    ),
    (
        "external-seed-acquisition-journal:ordered-seed-values-commitment",
        "external-seed-acquisition-journal",
        "$ordered_seed_values_commitment_sha256",
        "cp64-test28-ordered-seed-sequence-v1",
        (),
        ("external-seed-acquisition-journal:head",),
    ),
    (
        "auxiliary-reservation-transition-journal:head0",
        "auxiliary-reservation-transition-journal",
        "$header.head0_sha256",
        "cp65-test28-auxiliary-reservation-transition-head-v1",
        (),
        (),
    ),
    (
        "auxiliary-reservation-transition-journal:preinventory-prefix",
        "auxiliary-reservation-transition-journal",
        "$preinventory_prefix.head_sha256",
        "cp65-test28-auxiliary-reservation-transition-entry-v1",
        (),
        ("auxiliary-reservation-transition-journal:head0",),
    ),
    (
        "auxiliary-reservation-transition-journal:after-inventory",
        "auxiliary-reservation-transition-journal",
        "$after_inventory.head_sha256",
        "cp65-test28-auxiliary-reservation-transition-entry-v1",
        (),
        ("auxiliary-reservation-transition-journal:preinventory-prefix",),
    ),
    (
        "auxiliary-reservation-transition-journal:after-terminal",
        "auxiliary-reservation-transition-journal",
        "$after_terminal.head_sha256",
        "cp65-test28-auxiliary-reservation-transition-entry-v1",
        (),
        ("auxiliary-reservation-transition-journal:after-inventory",),
    ),
    (
        "auxiliary-reservation-transition-journal:final-head",
        "auxiliary-reservation-transition-journal",
        "$final.head_sha256",
        "cp65-test28-auxiliary-reservation-transition-entry-v1",
        (),
        ("auxiliary-reservation-transition-journal:after-terminal",),
    ),
)

_I_RAW_ARTIFACT_SHA256_FIELD_SOURCES = {
    "protocol_sha256": "frozen-protocol",
    "machine_manifest_sha256": "frozen-machine-manifest",
    "bound_files_sha256": "source-manifest",
    "source_manifest_sha256": "source-manifest",
    "writer_source_manifest_sha256": "source-manifest",
    "runner_source_manifest_sha256": "source-manifest",
    "classifier_source_manifest_sha256": "source-manifest",
    "frozen_source_fixture_materialization_sha256": "frozen-source-fixture-materialization",
    "dependency_lock_sha256": "dependency-lock",
    "expected_sha256": "dependency-lock",
    "observed_sha256": "dependency-lock",
    "power_threshold_receipt_sha256": "power-threshold-receipt",
    "launch_authority_public_key_sha256": "launch-authority-public-key",
    "independent_reviewer_public_key_set_sha256": "independent-reviewer-public-key-set",
    "seed_source_authority_public_key_sha256": "seed-source-authority-public-key",
    "production_receipt_schema_bundle_sha256": "production-schema-preimage-validator-bundle",
    "capacity_schema_sha256": "production-schema-preimage-validator-bundle",
    "freeze_receipt_sha256": "freeze-receipt",
    "seed_source_receipt_sha256": "external-seed-source-receipt",
    "source_receipt_sha256": "external-seed-source-receipt",
    "schedule_sha256": "production-schedule",
    "production_schedule_sha256": "production-schedule",
    "production_runtime_receipt_sha256": "production-runtime-receipt",
    "runtime_receipt_sha256": "production-runtime-receipt",
    "capacity_receipt_sha256": "capacity-receipt",
    "durability_receipt_sha256": "durability-receipt",
    "production_shard_map_receipt_sha256": "production-shard-map-receipt",
    "shard_map_receipt_sha256": "production-shard-map-receipt",
    "preflight_gate_summary_sha256": "preflight-gate-summary",
    "independent_signoff_sha256": "independent-signoff-set",
    "launch_authorization_sha256": "launch-authorization",
    "postauthorization_outcome_sha256": "postauthorization-outcome",
    "started_receipt_sha256": "started-receipt",
    "terminal_state_sha256": "terminal-state",
    "sha256_manifest_sha256": "sha256-manifest",
    "auxiliary_metadata_reservation_sha256": "auxiliary-metadata-reservation",
    "auxiliary_metadata_reservation_artifact_sha256": "auxiliary-metadata-reservation",
    "reservation_manifest_sha256": "reservation-manifest",
    "external_digest_preimage_registry_sha256": "external-digest-preimage-registry",
    "reviewer_public_key_set_sha256": "independent-reviewer-public-key-set",
    "source_authority_attestation_sha256": "seed-source-authority-attestation",
    "acquisition_journal_sha256": "external-seed-acquisition-journal",
    "custody_artifact_sha256": "seed-source-custody-artifact",
    "seed_source_custody_artifact_sha256": "seed-source-custody-artifact",
    "reviewer_signoff_sha256": "power-review-signoff",
    "preauthorization_outcome_sha256": "preauthorization-outcome",
    "durable_artifact_inventory_sha256": "preterminal-durable-artifact-inventory",
    "shard_index_sha256": "shard-index",
    "requests_file_sha256": "shard-requests",
    "raw_file_sha256": "shard-raw-records",
    "stable_file_sha256": "shard-stable-traces",
    "stderr_file_sha256": "shard-stderr-records",
    "rng_initial_file_sha256": "shard-rng-initial-states",
    "rng_final_file_sha256": "shard-rng-final-states",
}

_I_BODY_ARTIFACT_SHA256_FIELD_SOURCES = {
    "acquisition_start_receipt_sha256": "external-seed-acquisition-start-receipt",
    "acquisition_session_sha256": "external-seed-acquisition-start-receipt",
    "seed_capsule_body_sha256": "seed-capsule-body",
}

_I_SHA256_POINTER_SOURCE_CONTRACT_OVERRIDES = {
    (
        "capacity-receipt",
        "/capacity_schema_sha256",
    ): "v15-machine-manifest:cp64-capacity-receipt-schema-record-sha256",
    (
        "auxiliary-metadata-reservation",
        "/capacity_schema_sha256",
    ): "v15-machine-manifest:cp64-capacity-receipt-schema-record-sha256",
    (
        "reservation-manifest",
        "/capacity_schema_sha256",
    ): "v15-machine-manifest:cp64-capacity-receipt-schema-record-sha256",
    (
        "external-seed-source-receipt",
        "/cp61_stable_design_sha256",
    ): "v15-machine-manifest:cp61-stable-design-semantic-sha256",
    (
        "seed-capsule-body",
        "/cp61_stable_design_sha256",
    ): "v15-machine-manifest:cp61-stable-design-semantic-sha256",
    (
        "independent-554-estimate-interval-decision-path-qualification-receipt",
        "/estimand_contract_sha256",
    ): "v15-machine-manifest:cp61-stable-design-semantic-sha256",
    (
        "production-shard-map-receipt",
        "/candidate_shard_policy_sha256",
    ): "v15-machine-manifest:cp64-candidate-shard-policy-record-sha256",
    (
        "durability-receipt",
        "/layout_contract_sha256",
    ): "v15-machine-manifest:cp64-durability-receipt-schema-record-sha256",
    (
        "production-schedule",
        "/schedule_contract_sha256",
    ): "v15-machine-manifest:cp63-schedule-contract-record-sha256",
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "/production_schedule_contract_sha256",
    ): "v15-machine-manifest:cp63-schedule-contract-record-sha256",
    (
        "production-runner-supervisor-qualification-receipt",
        "/supervisor_contract_sha256",
    ): "v15-machine-manifest:cp62-supervisor-contract-record-sha256",
    (
        "closed-refusal-failure-classifier-qualification-receipt",
        "/supervisor_contract_sha256",
    ): "v15-machine-manifest:cp62-supervisor-contract-record-sha256",
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "/raw_record_schema_sha256",
    ): "v15-machine-manifest:cp63-raw-record-schema-record-sha256",
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "/stable_projection_schema_sha256",
    ): "v15-machine-manifest:cp62-projection-contract-record-sha256",
    (
        "independent-full-32768-recomputation-qualification-receipt",
        "/independent_recomputation_source_manifest_sha256",
    ): "source-manifest:independent-recomputation-submanifest",
    (
        "independent-554-estimate-interval-decision-path-qualification-receipt",
        "/independent_source_manifest_sha256",
    ): "source-manifest:independent-recomputation-submanifest",
    (
        "external-digest-preimage-registry",
        "/schema_semantic_sha256",
    ): "production-schema-preimage-validator-bundle:schema-semantic-sha256",
    (
        "external-digest-preimage-registry",
        "/ordered_entry_sha256s/*",
    ): "external-digest-preimage-registry:entries-row-digest",
    (
        "production-schedule",
        "/requests/*/seed_capsule_body_sha256",
    ): "seed-capsule-body:body-sha256",
    (
        "production-schedule",
        "/requests/*/runtime_lock_sha256",
    ): "v15-machine-manifest:cp62-runtime-lock-record-sha256",
    (
        "production-schedule",
        "/ordered_request_record_sha256s/*",
    ): "production-schedule:requests-row-digest",
    (
        "power-threshold-receipt",
        "/ordered_slot_threshold_row_sha256s/*",
    ): "power-threshold-receipt:ordered_slot_thresholds-row-digest",
    (
        "power-review-signoff",
        "/power_review_sha256",
    ): "power-threshold-receipt:power-review-text",
    (
        "power-review-signoff",
        "/selected_count_justification_sha256",
    ): "power-threshold-receipt:selected-count-justification-text",
    (
        "power-review-signoff",
        "/ordered_slot_thresholds_sha256",
    ): "power-threshold-receipt:ordered-threshold-rows",
    (
        "power-review-signoff",
        "/ordered_slot_threshold_row_sha256s/*",
    ): "power-threshold-receipt:ordered_slot_thresholds-row-digest",
    (
        "preflight-gate-summary",
        "/ordered_evidence_receipt_sha256s/*",
    ): "preflight-gate-summary:selected-evidence-raw-sha256",
    (
        "independent-reviewer-public-key-set",
        "/ordered_public_key_identity_sha256s/*",
    ): "independent-reviewer-public-key-set:key-identity",
    (
        "independent-signoff-set",
        "/ordered_signoffs/*/reviewed_artifact_sha256s/*",
    ): "preflight-gate-summary:raw-sha256",
    (
        "production-shard-map-receipt",
        "/shards/*/per_file_reservation_manifest_entry_sha256s/*",
    ): "reservation-manifest:entries-row-digest",
    (
        "shard-index",
        "/shard_record_sha256",
    ): "production-shard-map-receipt:shards-row-digest",
    (
        "launch-authorization",
        "/authority_identity_sha256",
    ): "launch-authority-public-key:identity",
    (
        "rejected-launch-authorization-candidate",
        "/authority_identity_sha256",
    ): "launch-authority-public-key:identity",
    (
        "seed-source-authority-attestation",
        "/source_authority_identity_sha256",
    ): "seed-source-authority-public-key:identity",
    (
        "power-review-signoff",
        "/reviewer_public_key_identity_sha256",
    ): "independent-reviewer-public-key-set:key-identity",
    (
        "power-review-signoff",
        "/reviewer_identity_sha256",
    ): "independent-reviewer-public-key-set:selected-reviewer-identity-sha256",
    (
        "independent-signoff-set",
        "/ordered_signoffs/*/reviewer_public_key_identity_sha256",
    ): "independent-reviewer-public-key-set:key-identity",
    (
        "independent-signoff-set",
        "/ordered_signoffs/*/reviewer_identity_sha256",
    ): "independent-reviewer-public-key-set:selected-reviewer-identity-sha256",
    (
        "external-seed-source-receipt",
        "/acquisition_journal_head_sha256",
    ): "external-seed-acquisition-journal:head",
    (
        "partial-seed-acquisition-terminal-receipt",
        "/acquisition_journal_head_sha256",
    ): "external-seed-acquisition-journal:head",
    (
        "seed-source-authority-attestation",
        "/acquisition_journal_head_sha256",
    ): "external-seed-acquisition-journal:head",
    (
        "seed-source-authority-attestation",
        "/ordered_seed_values_commitment_sha256",
    ): "external-seed-acquisition-journal:ordered-seed-values-commitment",
    (
        "external-seed-source-receipt",
        "/ordered_seed_values_commitment_sha256",
    ): "external-seed-acquisition-journal:ordered-seed-values-commitment",
    (
        "partial-seed-acquisition-terminal-receipt",
        "/ordered_partial_seed_values_commitment_sha256",
    ): "external-seed-acquisition-journal:ordered-seed-values-commitment",
    (
        "seed-capsule-sequence-crosscheck-receipt",
        "/source_sequence_commitment_sha256",
    ): "external-seed-acquisition-journal:ordered-seed-values-commitment",
    (
        "seed-capsule-sequence-crosscheck-receipt",
        "/capsule_sequence_commitment_sha256",
    ): "seed-capsule-body:ordered-seed-sequence",
    (
        "preterminal-durable-artifact-inventory",
        "/auxiliary_transition_journal_prefix_head_sha256",
    ): "auxiliary-reservation-transition-journal:preinventory-prefix",
    (
        "terminal-state",
        "/auxiliary_transition_journal_after_inventory_head_sha256",
    ): "auxiliary-reservation-transition-journal:after-inventory",
    (
        "sha256-manifest",
        "/auxiliary_transition_journal_after_terminal_head_sha256",
    ): "auxiliary-reservation-transition-journal:after-terminal",
    (
        "committed-marker",
        "/auxiliary_reservation_transition_journal_final_head_sha256",
    ): "auxiliary-reservation-transition-journal:final-head",
    (
        "committed-marker",
        "/auxiliary_reservation_transition_journal_sha256",
    ): "auxiliary-reservation-transition-journal:raw-sha256",
    (
        "committed-marker",
        "/hold_device_identity_sha256",
    ): "external-preimage:auxiliary-metadata-reservation:/hold_device_identity_sha256",
    (
        "committed-marker",
        "/hold_extent_map_sha256",
    ): "external-preimage:auxiliary-metadata-reservation:/hold_extent_map_sha256",
    (
        "capacity-receipt",
        "/auxiliary_artifact_size_proof_sha256",
    ): "production-schema-preimage-validator-bundle:auxiliary-size-proof-record-sha256",
    ("launch-receipt", "/runner_source_manifest_sha256"): "source-manifest:raw-sha256",
    (
        "preauthorization-outcome",
        "/prepared_launch_authorization_sha256",
    ): "launch-authorization-candidate:prepared-raw-sha256",
}

# Independently restated leaves selected from the immutable v15 predecessor.
# The frozen manifest's raw bytes remain a custody pin; runtime validation does
# not decode that predecessor as the semantic source for these relationships.
_I_V15_SELECTED_STORED_SHA256_BY_CONTRACT_ID = {
    "v15-machine-manifest:cp64-capacity-receipt-schema-record-sha256": (
        "968108bda050687408fe989186aff3137560b827d1c83622f685a597d208ecfe"
    ),
    "v15-machine-manifest:cp61-stable-design-semantic-sha256": (
        "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
    ),
    "v15-machine-manifest:cp64-candidate-shard-policy-record-sha256": (
        "8623c092772eaa0e40066d7e423967095e86491c01d869aa824c81fa9ee4b4ea"
    ),
    "v15-machine-manifest:cp64-durability-receipt-schema-record-sha256": (
        "aced3702d8f1cbb240de9c41c6f97581a5ce019045e3300cc485bcb6328e76c2"
    ),
    "v15-machine-manifest:cp63-schedule-contract-record-sha256": (
        "7ca5555de1aa852021c6b7fd181417a629dcec461455650ecafc495f5e6fb607"
    ),
    "v15-machine-manifest:cp62-supervisor-contract-record-sha256": (
        "6dfb5b8bbb7cecabed1c84349bc32ac130dd2fb698ba400e0ce74d3ef58434fb"
    ),
    "v15-machine-manifest:cp63-raw-record-schema-record-sha256": (
        "29f17aa7528971e7892b6ea4ccb37b5943190a0e592191341ae444e8ed63b3cb"
    ),
    "v15-machine-manifest:cp62-projection-contract-record-sha256": (
        "1d42337a0191822fb7d7fa81883bab08101dbf68cd88e1b835553bc96fb32733"
    ),
    "v15-machine-manifest:cp62-runtime-lock-record-sha256": (
        "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
    ),
}

_I_EXTERNAL_REGISTRY_SHA256_POINTERS = frozenset(
    {
        (
            "auxiliary-metadata-reservation",
            "/artifact_entries/*/device_identity_sha256",
        ),
        ("auxiliary-metadata-reservation", "/artifact_entries/*/extent_map_sha256"),
        ("auxiliary-metadata-reservation", "/exclusive_root_charge_measurement_sha256"),
        ("auxiliary-metadata-reservation", "/filesystem_identity_sha256"),
        ("auxiliary-metadata-reservation", "/hold_device_identity_sha256"),
        ("auxiliary-metadata-reservation", "/hold_extent_map_sha256"),
        ("auxiliary-metadata-reservation", "/measurement_session_sha256"),
        ("auxiliary-metadata-reservation", "/storage_root_identity_sha256"),
        ("capacity-receipt", "/filesystem_identity_sha256"),
        ("capacity-receipt", "/measurement_session_sha256"),
        ("capacity-receipt", "/storage_root_identity_sha256"),
        ("durability-receipt", "/filesystem_identity_sha256"),
        ("durability-receipt", "/qualification_session_sha256"),
        (
            "external-seed-acquisition-start-receipt",
            "/acquisition_journal_device_identity_sha256",
        ),
        (
            "external-seed-acquisition-start-receipt",
            "/acquisition_journal_extent_map_sha256",
        ),
        (
            "external-seed-acquisition-start-receipt",
            "/acquisition_journal_inode_recheck_sha256",
        ),
        ("freeze-receipt", "/freezer_identity_sha256"),
        (
            "independent-554-estimate-interval-decision-path-qualification-receipt",
            "/qualification_fixture_set_sha256",
        ),
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "/qualification_fixture_set_sha256",
        ),
        (
            "independent-reviewer-public-key-set",
            "/ordered_keys/*/reviewer_identity_sha256",
        ),
        (
            "production-runner-supervisor-qualification-receipt",
            "/qualification_fixture_set_sha256",
        ),
        ("production-runtime-receipt", "/abi_map_sha256"),
        ("production-runtime-receipt", "/environment_sha256"),
        ("production-runtime-receipt", "/loaded_local_source_closure_sha256"),
        ("production-runtime-receipt", "/numpy_payload_closure_sha256"),
        ("production-runtime-receipt", "/numpy_record_sha256"),
        ("production-runtime-receipt", "/observation_session_sha256"),
        ("production-runtime-receipt", "/python_executable_sha256"),
        ("production-runtime-receipt", "/python_framework_sha256"),
        ("production-runtime-receipt", "/scipy_payload_closure_sha256"),
        ("production-runtime-receipt", "/scipy_record_sha256"),
        ("production-runtime-receipt", "/stdlib_closure_sha256"),
        ("reservation-manifest", "/entries/*/device_identity_sha256"),
        ("reservation-manifest", "/entries/*/extent_map_sha256"),
        ("reservation-manifest", "/filesystem_identity_sha256"),
        ("reservation-manifest", "/measurement_session_sha256"),
        ("reservation-manifest", "/storage_root_identity_sha256"),
        ("seed-source-custody-artifact", "/custody_payload_sha256"),
        ("seed-source-custody-artifact", "/retention_location_identity_sha256"),
    }
)

_I_POINTER_WILDCARD_CARDINALITIES = {
    ("source-manifest", "entries"): 4096,
    ("power-threshold-receipt", "ordered_slot_thresholds"): 32,
    ("external-digest-preimage-registry", "entries"): 4096,
    ("external-digest-preimage-registry", "ordered_entry_sha256s"): 4096,
    ("auxiliary-metadata-reservation", "artifact_entries"): 183,
    ("reservation-manifest", "entries"): 128,
    ("production-schedule", "requests"): 32768,
    ("production-schedule", "ordered_request_record_sha256s"): 32768,
    ("production-shard-map-receipt", "shards"): 32,
    ("production-shard-map-receipt", "per_file_reservation_manifest_entry_sha256s"): 4,
    ("independent-signoff-set", "ordered_signoffs"): 4,
    ("independent-signoff-set", "reviewed_artifact_sha256s"): 1,
    ("independent-reviewer-public-key-set", "ordered_keys"): 4,
    ("independent-reviewer-public-key-set", "ordered_public_key_identity_sha256s"): 4,
    ("power-threshold-receipt", "ordered_slot_threshold_row_sha256s"): 32,
    ("power-review-signoff", "ordered_slot_threshold_row_sha256s"): 32,
    ("preflight-gate-summary", "ordered_evidence_receipt_sha256s"): 15,
    ("shard-index", "ordered_request_entries"): 1024,
    ("preterminal-durable-artifact-inventory", "entries"): 312,
    ("sha256-manifest", "entries"): 312,
}

_I_CROSS_PREDICATE_SPECS = (
    (
        "cross:preauthorization-outcome-discriminated-union",
        ("preauthorization-outcome",),
        "discriminated-union",
        ("/outcome_arm", "/prepared_launch_authorization_sha256", "/terminal_state"),
        {"arms": ["AUTHORIZATION", "INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE"]},
    ),
    (
        "cross:postauthorization-outcome-discriminated-union",
        ("postauthorization-outcome",),
        "discriminated-union",
        ("/outcome_arm", "/launch_authorization_sha256", "/terminal_state"),
        {"arms": ["STARTED", "INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE"]},
    ),
    (
        "cross:terminal-arm-member-of-closed-domain",
        ("terminal-state",),
        "member-of",
        ("/terminal_arm",),
        {"members": ["PREAUTHORIZATION", "POSTAUTHORIZATION_PRESTART", "STARTED"]},
    ),
    (
        "cross:source-start-and-session-digests-equal",
        ("external-seed-source-receipt",),
        "all-equal",
        ("/acquisition_start_receipt_sha256", "/acquisition_session_sha256"),
        {},
    ),
    (
        "cross:shard-map-ranges-contiguously-cover-production",
        ("production-shard-map-receipt",),
        "contiguous-cover",
        (
            "/shards/*/seed_ordinal_min",
            "/shards/*/seed_ordinal_max",
            "/shards/*/logical_request_ordinal_min",
            "/shards/*/logical_request_ordinal_max",
        ),
        {"seed_cover": [1, 2048], "logical_cover": [1, 32768]},
    ),
    (
        "cross:schedule-row-digest-sequence-equals-outer-sequence",
        ("production-schedule",),
        "digest-sequence-equal",
        ("/requests/*/request_row_sha256", "/ordered_request_record_sha256s"),
        {},
    ),
    (
        "cross:terminal-state-is-exact-discriminated-union",
        ("terminal-state",),
        "discriminated-union",
        (
            "/terminal_arm",
            "/previous_lifecycle_state",
            "/terminal_state",
            "/freeze_receipt_sha256",
            "/preauthorization_outcome_sha256",
            "/launch_authorization_sha256",
            "/postauthorization_outcome_sha256",
            "/started_receipt_sha256",
            "/durable_artifact_inventory_sha256",
            "/reason_code",
        ),
        {"arms": ["PREAUTHORIZATION", "POSTAUTHORIZATION_PRESTART", "STARTED"]},
    ),
    (
        "cross:partial-journal-valid-prefix-formula",
        ("partial-seed-acquisition-terminal-receipt",),
        "integer-formula-equal",
        (
            "/acquired_seed_count",
            "/acquisition_journal_entry_count",
            "/acquisition_journal_raw_bytes",
        ),
        {
            "formula": "entry-count=acquired-count;raw-file-bytes=163840;valid-prefix-bytes=80*entry-count"
        },
    ),
    (
        "cross:shard-terminal-counts-sum-to-request-count",
        ("shard-receipt",),
        "integer-sum-equal",
        ("/terminal_counts", "/request_count"),
        {},
    ),
    (
        "cross:seed-capsule-array-lengths-equal-count",
        ("seed-capsule-body",),
        "length-equal",
        ("/seed_ordinals", "/ordered_seed_values", "/seed_count"),
        {},
    ),
    (
        "cross:preauthorization-record-is-one-allowed-arm",
        ("preauthorization-outcome",),
        "logical-or",
        ("/outcome_arm", "/terminal_state"),
        {"arms": ["AUTHORIZATION", "INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE"]},
    ),
    (
        "cross:published-and-rejected-authorization-not-copresent",
        ("launch-authorization", "rejected-launch-authorization-candidate"),
        "logical-not",
        (
            "launch-authorization:$present",
            "rejected-launch-authorization-candidate:$present",
        ),
        {"forbidden": "both-present"},
    ),
    (
        "cross:authorization-arm-prepared-digest-nonzero",
        ("preauthorization-outcome",),
        "not-equal",
        ("/outcome_arm", "/prepared_launch_authorization_sha256"),
        {
            "value": "0000000000000000000000000000000000000000000000000000000000000000",
            "when": {"/outcome_arm": "AUTHORIZATION"},
        },
    ),
    (
        "cross:preflight-summary-vectors-ordered",
        ("preflight-gate-summary",),
        "ordered-equal",
        ("/covered_gate_ids", "/covered_gate_states", "/covered_evidence_node_ids"),
        {
            "expected_sequences": [
                [
                    "v15-protocol-sidecar-and-machine-manifest-frozen",
                    "complete-production-source-manifest",
                    "exact-dependency-lock-matched",
                    "full-production-runtime-lock-recomputed-and-matched",
                    "external-seed-source-receipt-and-authority",
                    "external-seed-capsule-sequence-crosscheck",
                    "production-request-schedule-materialized",
                    "capacity-receipt-meets-usable-and-quota-floor",
                    "durable-writer-qualified",
                    "production-shard-map-selected-and-materialized",
                    "production-runner-supervisor-qualified",
                    "closed-refusal-failure-classifier-qualified",
                    "independent-full-32768-recomputation-qualified",
                    "independent-554-estimate-interval-decision-path-qualified",
                    "power-review-and-32-primary-thresholds-frozen",
                ],
                [
                    "PASS",
                    "PASS",
                    "PASS",
                    "PASS",
                    "PASS",
                    "PASS",
                    "PASS",
                    "PASS",
                    "PASS",
                    "PASS",
                    "PASS",
                    "PASS",
                    "PASS",
                    "PASS",
                    "PASS",
                ],
                [
                    "freeze-receipt",
                    "source-manifest",
                    "dependency-lock-match-receipt",
                    "production-runtime-receipt",
                    "external-seed-source-receipt",
                    "seed-capsule-sequence-crosscheck-receipt",
                    "production-schedule",
                    "capacity-receipt",
                    "durability-receipt",
                    "production-shard-map-receipt",
                    "production-runner-supervisor-qualification-receipt",
                    "closed-refusal-failure-classifier-qualification-receipt",
                    "independent-full-32768-recomputation-receipt",
                    "independent-554-estimate-interval-decision-path-receipt",
                    "power-threshold-receipt",
                ],
            ]
        },
    ),
    (
        "cross:launch-authorization-rsa-pss-mathematics",
        ("launch-authorization", "launch-authority-public-key"),
        "rsa-pss-verify",
        (
            "launch-authorization:$signature-preimage-bytes",
            "launch-authority-public-key:$modulus-bytes",
            "launch-authorization:$signature-bytes",
        ),
        {"scheme": "rsa-pss-sha256-3072-e65537-salt32-v1"},
    ),
    (
        "cross:source-receipt-binds-start-body-digest",
        ("external-seed-source-receipt", "external-seed-acquisition-start-receipt"),
        "sha256-body-equal",
        (
            "external-seed-source-receipt:/acquisition_start_receipt_sha256",
            "external-seed-acquisition-start-receipt:/body_sha256",
        ),
        {"domain": "cp64-test28-external-seed-acquisition-start-receipt-v1"},
    ),
    (
        "cross:freeze-binds-source-manifest-raw-bytes",
        ("freeze-receipt", "source-manifest"),
        "sha256-raw-equal",
        ("freeze-receipt:/bound_files_sha256", "source-manifest:$raw_sha256"),
        {},
    ),
    (
        "cross:source-manifest-entry-ordinals-strictly-increase",
        ("source-manifest",),
        "strictly-increasing",
        ("/entries/*/ordinal",),
        {"first": 1, "step": 1},
    ),
    (
        "cross:launch-authorization-validity-contained-by-key",
        ("launch-authorization", "launch-authority-public-key"),
        "utc-interval-contained",
        (
            "launch-authority-public-key:/valid_from_utc",
            "launch-authorization:/authorization_issued_at_utc",
            "launch-authorization:/authorization_expires_at_utc",
            "launch-authority-public-key:/valid_until_utc",
        ),
        {"inequality": "valid-from<=issued<expires<=valid-until"},
    ),
)

_I_GATE_IDS = (
    "v15-protocol-sidecar-and-machine-manifest-frozen",
    "complete-production-source-manifest",
    "exact-dependency-lock-matched",
    "full-production-runtime-lock-recomputed-and-matched",
    "external-seed-source-receipt-and-authority",
    "external-seed-capsule-sequence-crosscheck",
    "production-request-schedule-materialized",
    "capacity-receipt-meets-usable-and-quota-floor",
    "durable-writer-qualified",
    "production-shard-map-selected-and-materialized",
    "production-runner-supervisor-qualified",
    "closed-refusal-failure-classifier-qualified",
    "independent-full-32768-recomputation-qualified",
    "independent-554-estimate-interval-decision-path-qualified",
    "power-review-and-32-primary-thresholds-frozen",
    "independent-review-signoffs-present",
    "explicit-launch-authorization-present",
)

_I_GATE_EVIDENCE_NODES = (
    "freeze-receipt",
    "source-manifest",
    "dependency-lock-match-receipt",
    "production-runtime-receipt",
    "external-seed-source-receipt",
    "seed-capsule-sequence-crosscheck-receipt",
    "production-schedule",
    "capacity-receipt",
    "durability-receipt",
    "production-shard-map-receipt",
    "production-runner-supervisor-qualification-receipt",
    "closed-refusal-failure-classifier-qualification-receipt",
    "independent-full-32768-recomputation-receipt",
    "independent-554-estimate-interval-decision-path-receipt",
    "power-threshold-receipt",
    "independent-signoff-set",
    "launch-authorization",
)

_I_GATE_DAG_NODES = (
    "source-manifest",
    "dependency-lock-match-receipt",
    "power-threshold-receipt",
    "freeze-receipt",
    "external-seed-acquisition-start-receipt",
    "external-seed-source-receipt",
    "seed-capsule-body",
    "seed-capsule-sequence-crosscheck-receipt",
    "production-schedule",
    "production-runtime-receipt",
    "capacity-receipt",
    "durability-receipt",
    "production-shard-map-receipt",
    "production-runner-supervisor-qualification-receipt",
    "closed-refusal-failure-classifier-qualification-receipt",
    "independent-full-32768-recomputation-receipt",
    "independent-554-estimate-interval-decision-path-receipt",
    "preflight-gate-summary",
    "independent-signoff-set",
    "launch-authorization",
)

_I_GATE_DAG_EDGES = (
    ("source-manifest", "freeze-receipt"),
    ("source-manifest", "production-runtime-receipt"),
    ("source-manifest", "launch-authorization"),
    ("power-threshold-receipt", "freeze-receipt"),
    ("power-threshold-receipt", "launch-authorization"),
    ("freeze-receipt", "external-seed-acquisition-start-receipt"),
    ("freeze-receipt", "external-seed-source-receipt"),
    ("freeze-receipt", "production-runtime-receipt"),
    ("freeze-receipt", "launch-authorization"),
    ("external-seed-acquisition-start-receipt", "external-seed-source-receipt"),
    ("external-seed-source-receipt", "seed-capsule-body"),
    ("external-seed-source-receipt", "seed-capsule-sequence-crosscheck-receipt"),
    ("external-seed-source-receipt", "launch-authorization"),
    ("seed-capsule-body", "production-schedule"),
    ("seed-capsule-body", "seed-capsule-sequence-crosscheck-receipt"),
    ("seed-capsule-body", "launch-authorization"),
    ("production-schedule", "capacity-receipt"),
    ("production-schedule", "production-shard-map-receipt"),
    ("production-schedule", "launch-authorization"),
    ("production-runtime-receipt", "launch-authorization"),
    ("capacity-receipt", "durability-receipt"),
    ("capacity-receipt", "production-shard-map-receipt"),
    ("capacity-receipt", "launch-authorization"),
    ("durability-receipt", "production-shard-map-receipt"),
    ("durability-receipt", "launch-authorization"),
    ("production-shard-map-receipt", "launch-authorization"),
    ("preflight-gate-summary", "independent-signoff-set"),
    ("preflight-gate-summary", "launch-authorization"),
    ("independent-signoff-set", "launch-authorization"),
    ("freeze-receipt", "preflight-gate-summary"),
    ("source-manifest", "preflight-gate-summary"),
    ("dependency-lock-match-receipt", "preflight-gate-summary"),
    ("production-runtime-receipt", "preflight-gate-summary"),
    ("external-seed-source-receipt", "preflight-gate-summary"),
    ("seed-capsule-sequence-crosscheck-receipt", "preflight-gate-summary"),
    ("production-schedule", "preflight-gate-summary"),
    ("capacity-receipt", "preflight-gate-summary"),
    ("durability-receipt", "preflight-gate-summary"),
    ("production-shard-map-receipt", "preflight-gate-summary"),
    ("production-runner-supervisor-qualification-receipt", "preflight-gate-summary"),
    (
        "closed-refusal-failure-classifier-qualification-receipt",
        "preflight-gate-summary",
    ),
    ("independent-full-32768-recomputation-receipt", "preflight-gate-summary"),
    (
        "independent-554-estimate-interval-decision-path-receipt",
        "preflight-gate-summary",
    ),
    ("power-threshold-receipt", "preflight-gate-summary"),
)

_I_GATE_DAG_EDGE_TARGET_POINTERS = (
    "/bound_files_sha256",
    "/source_manifest_sha256",
    "/source_manifest_sha256",
    "/power_threshold_receipt_sha256",
    "/power_threshold_receipt_sha256",
    "/freeze_receipt_sha256",
    "/freeze_receipt_sha256",
    "/freeze_receipt_sha256",
    "/freeze_receipt_sha256",
    "/acquisition_start_receipt_sha256",
    "/source_receipt_sha256",
    "/source_receipt_sha256",
    "/seed_source_receipt_sha256",
    "/seed_capsule_body_sha256",
    "/seed_capsule_body_sha256",
    "/seed_capsule_body_sha256",
    "/schedule_sha256",
    "/schedule_sha256",
    "/schedule_sha256",
    "/production_runtime_receipt_sha256",
    "/capacity_receipt_sha256",
    "/capacity_receipt_sha256",
    "/capacity_receipt_sha256",
    "/durability_receipt_sha256",
    "/durability_receipt_sha256",
    "/production_shard_map_receipt_sha256",
    "/preflight_gate_summary_sha256",
    "/preflight_gate_summary_sha256",
    "/independent_signoff_sha256",
    "/ordered_evidence_receipt_sha256s/0",
    "/ordered_evidence_receipt_sha256s/1",
    "/ordered_evidence_receipt_sha256s/2",
    "/ordered_evidence_receipt_sha256s/3",
    "/ordered_evidence_receipt_sha256s/4",
    "/ordered_evidence_receipt_sha256s/5",
    "/ordered_evidence_receipt_sha256s/6",
    "/ordered_evidence_receipt_sha256s/7",
    "/ordered_evidence_receipt_sha256s/8",
    "/ordered_evidence_receipt_sha256s/9",
    "/ordered_evidence_receipt_sha256s/10",
    "/ordered_evidence_receipt_sha256s/11",
    "/ordered_evidence_receipt_sha256s/12",
    "/ordered_evidence_receipt_sha256s/13",
    "/ordered_evidence_receipt_sha256s/14",
)

_I_GATE_DAG_EDGE_SOURCE_CONTRACT_IDS = (
    "source-manifest:raw-sha256",
    "source-manifest:raw-sha256",
    "source-manifest:raw-sha256",
    "power-threshold-receipt:raw-sha256",
    "power-threshold-receipt:raw-sha256",
    "freeze-receipt:raw-sha256",
    "freeze-receipt:raw-sha256",
    "freeze-receipt:raw-sha256",
    "freeze-receipt:raw-sha256",
    "external-seed-acquisition-start-receipt:body-sha256",
    "external-seed-source-receipt:raw-sha256",
    "external-seed-source-receipt:raw-sha256",
    "external-seed-source-receipt:raw-sha256",
    "seed-capsule-body:body-sha256",
    "seed-capsule-body:body-sha256",
    "seed-capsule-body:body-sha256",
    "production-schedule:raw-sha256",
    "production-schedule:raw-sha256",
    "production-schedule:raw-sha256",
    "production-runtime-receipt:raw-sha256",
    "capacity-receipt:raw-sha256",
    "capacity-receipt:raw-sha256",
    "capacity-receipt:raw-sha256",
    "durability-receipt:raw-sha256",
    "durability-receipt:raw-sha256",
    "production-shard-map-receipt:raw-sha256",
    "preflight-gate-summary:raw-sha256",
    "preflight-gate-summary:raw-sha256",
    "independent-signoff-set:raw-sha256",
    "freeze-receipt:raw-sha256",
    "source-manifest:raw-sha256",
    "dependency-lock-match-receipt:raw-sha256",
    "production-runtime-receipt:raw-sha256",
    "external-seed-source-receipt:raw-sha256",
    "seed-capsule-sequence-crosscheck-receipt:raw-sha256",
    "production-schedule:raw-sha256",
    "capacity-receipt:raw-sha256",
    "durability-receipt:raw-sha256",
    "production-shard-map-receipt:raw-sha256",
    "production-runner-supervisor-qualification-receipt:raw-sha256",
    "closed-refusal-failure-classifier-qualification-receipt:raw-sha256",
    "independent-full-32768-recomputation-qualification-receipt:raw-sha256",
    "independent-554-estimate-interval-decision-path-qualification-receipt:raw-sha256",
    "power-threshold-receipt:raw-sha256",
)

_I_GATE_DAG_EDGE_DIGEST_KINDS = (
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "body-domain-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "body-domain-sha256",
    "body-domain-sha256",
    "body-domain-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
    "plain-raw-file-sha256",
)

_I_GATE_REQUIRED_ARTIFACT_IDS = (
    (
        "frozen-protocol",
        "frozen-protocol-sha256",
        "frozen-machine-manifest",
        "production-schema-preimage-validator-bundle",
        "frozen-source-fixture-materialization",
        "source-manifest",
        "dependency-lock",
        "power-review-signoff",
        "power-threshold-receipt",
        "launch-authority-public-key",
        "independent-reviewer-public-key-set",
        "seed-source-authority-public-key",
        "freeze-receipt",
    ),
    (
        "frozen-protocol",
        "frozen-machine-manifest",
        "production-schema-preimage-validator-bundle",
        "frozen-source-fixture-materialization",
        "source-manifest",
    ),
    ("freeze-receipt", "dependency-lock", "dependency-lock-match-receipt"),
    (
        "freeze-receipt",
        "source-manifest",
        "dependency-lock",
        "dependency-lock-match-receipt",
        "production-runtime-receipt",
    ),
    (
        "freeze-receipt",
        "external-seed-acquisition-start-receipt",
        "external-seed-acquisition-journal",
        "seed-source-custody-artifact",
        "seed-source-authority-public-key",
        "seed-source-authority-attestation",
        "external-seed-source-receipt",
    ),
    (
        "freeze-receipt",
        "external-seed-acquisition-start-receipt",
        "external-seed-acquisition-journal",
        "seed-source-custody-artifact",
        "seed-source-authority-public-key",
        "seed-source-authority-attestation",
        "external-seed-source-receipt",
        "seed-capsule-body",
        "seed-capsule-sequence-crosscheck-receipt",
    ),
    (
        "freeze-receipt",
        "external-seed-source-receipt",
        "seed-capsule-body",
        "production-runtime-receipt",
        "production-schedule",
    ),
    (
        "freeze-receipt",
        "production-schema-preimage-validator-bundle",
        "production-schedule",
        "auxiliary-metadata-reservation",
        "reservation-manifest",
        "capacity-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "capacity-receipt",
        "auxiliary-metadata-reservation",
        "reservation-manifest",
        "durability-receipt",
    ),
    (
        "freeze-receipt",
        "seed-capsule-body",
        "production-schedule",
        "capacity-receipt",
        "durability-receipt",
        "reservation-manifest",
        "production-shard-map-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "production-runtime-receipt",
        "production-runner-supervisor-qualification-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "production-runner-supervisor-qualification-receipt",
        "closed-refusal-failure-classifier-qualification-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "production-schedule",
        "independent-full-32768-recomputation-qualification-receipt",
    ),
    (
        "freeze-receipt",
        "source-manifest",
        "production-schedule",
        "independent-554-estimate-interval-decision-path-qualification-receipt",
    ),
    (
        "frozen-protocol",
        "frozen-machine-manifest",
        "independent-reviewer-public-key-set",
        "power-review-signoff",
        "power-threshold-receipt",
    ),
    (
        "freeze-receipt",
        "preflight-gate-summary",
        "external-digest-preimage-registry",
        "independent-reviewer-public-key-set",
        "independent-signoff-set",
    ),
    (),
)

_I_REGISTRY_CUT_DURABLE_ARTIFACT_IDS = frozenset(
    {
        "auxiliary-metadata-reservation",
        "capacity-receipt",
        "closed-refusal-failure-classifier-qualification-receipt",
        "dependency-lock",
        "dependency-lock-match-receipt",
        "durability-receipt",
        "external-seed-acquisition-journal",
        "external-seed-acquisition-start-receipt",
        "external-seed-source-receipt",
        "freeze-receipt",
        "frozen-machine-manifest",
        "frozen-protocol",
        "frozen-protocol-sha256",
        "frozen-source-fixture-materialization",
        "independent-554-estimate-interval-decision-path-qualification-receipt",
        "independent-full-32768-recomputation-qualification-receipt",
        "independent-reviewer-public-key-set",
        "launch-authority-public-key",
        "power-review-signoff",
        "power-threshold-receipt",
        "production-runner-supervisor-qualification-receipt",
        "production-runtime-receipt",
        "production-schedule",
        "production-schema-preimage-validator-bundle",
        "production-shard-map-receipt",
        "reservation-manifest",
        "seed-capsule-body",
        "seed-capsule-sequence-crosscheck-receipt",
        "seed-source-authority-attestation",
        "seed-source-authority-public-key",
        "seed-source-custody-artifact",
        "source-manifest",
    }
)

_I_SHA256_POINTER_SEMANTIC_CLASSES = frozenset(
    {
        "binary-chain",
        "body-artifact",
        "conditional-zero-or-cross",
        "externally-retained-preimage",
        "key-identity",
        "nested-domain",
        "nested-domain-digest",
        "raw-artifact",
        "selected-stored-digest",
        "self-body",
        "signature",
    }
)

_I_SHA256_SOURCE_AVAILABILITY_CUT_IDS = frozenset(
    {
        "authorization-candidate-prepared-before-preauth-cas",
        "durable-by-gate15-before-registry-finalization",
        "final-journal-sealed-before-committed",
        "frozen-before-acquisition-start",
        "intrinsic-same-record",
        "manifest-before-final-journal-seal",
        "postauth-outcome-before-started-or-terminal",
        "preauth-outcome-before-postauth",
        "preterminal-inventory-before-terminal",
        "registry-finalized-before-summary",
        "shards-finalized-before-preterminal-inventory",
        "signoff-finalized-before-authorization",
        "started-before-launch-and-terminal",
        "summary-finalized-before-signoff",
        "terminal-before-manifest",
    }
)

_I_FROZEN_BEFORE_ACQUISITION_ARTIFACT_IDS = frozenset(
    {
        "dependency-lock",
        "freeze-receipt",
        "frozen-machine-manifest",
        "frozen-protocol",
        "frozen-protocol-sha256",
        "frozen-source-fixture-materialization",
        "independent-reviewer-public-key-set",
        "launch-authority-public-key",
        "power-review-signoff",
        "power-threshold-receipt",
        "production-schema-preimage-validator-bundle",
        "seed-source-authority-public-key",
        "source-manifest",
    }
)

_I_REFERENCED_OUTPUT_IDS = (
    "environment",
    "primary-metrics",
    "secondary-diagnostics",
    "postexecution-independent-recomputation",
    "decisions",
    "deviations",
    "failures",
    "exclusions",
    "reruns",
    "shard-requests",
    "shard-raw-records",
    "shard-stable-traces",
    "shard-stderr-records",
    "shard-rng-initial-states",
    "shard-rng-final-states",
)

_I_FROZEN_OR_BINARY_CUSTODY_IDS = (
    "frozen-protocol",
    "frozen-protocol-sha256",
    "frozen-machine-manifest",
    "dependency-lock",
    "external-seed-acquisition-journal",
    "frozen-source-fixture-materialization",
    "production-schema-preimage-validator-bundle",
    "auxiliary-reservation-transition-journal",
)

_I_AUTHORIZATION_REQUIRED_ARTIFACTS = (
    "frozen-protocol",
    "frozen-protocol-sha256",
    "frozen-machine-manifest",
    "production-schema-preimage-validator-bundle",
    "frozen-source-fixture-materialization",
    "source-manifest",
    "dependency-lock",
    "power-review-signoff",
    "power-threshold-receipt",
    "launch-authority-public-key",
    "independent-reviewer-public-key-set",
    "seed-source-authority-public-key",
    "freeze-receipt",
    "dependency-lock-match-receipt",
    "production-runtime-receipt",
    "external-seed-acquisition-start-receipt",
    "external-seed-acquisition-journal",
    "seed-source-custody-artifact",
    "seed-source-authority-attestation",
    "external-seed-source-receipt",
    "seed-capsule-body",
    "seed-capsule-sequence-crosscheck-receipt",
    "production-schedule",
    "auxiliary-metadata-reservation",
    "reservation-manifest",
    "capacity-receipt",
    "durability-receipt",
    "production-shard-map-receipt",
    "production-runner-supervisor-qualification-receipt",
    "closed-refusal-failure-classifier-qualification-receipt",
    "independent-full-32768-recomputation-qualification-receipt",
    "independent-554-estimate-interval-decision-path-qualification-receipt",
    "preflight-gate-summary",
    "external-digest-preimage-registry",
    "independent-signoff-set",
    "preauthorization-outcome",
    "launch-authorization",
)

_I_INTEGER_FIELD_NAMES = frozenset(
    {
        "acquired_seed_count",
        "acquisition_journal_entry_count",
        "acquisition_journal_inode",
        "acquisition_journal_preallocated_bytes",
        "acquisition_journal_raw_bytes",
        "allocated_existing_final_bytes",
        "allocated_future_partial_bytes",
        "allocated_reserved_bytes",
        "allocation_and_directory_charge_policy_slot_bytes",
        "allocation_unit_bytes",
        "artifact_entry_count",
        "artifact_slot_reserved_bytes",
        "authorized_attempt_number",
        "auxiliary_metadata_reservation_required_bytes",
        "auxiliary_metadata_reserved_quota_bytes",
        "auxiliary_reservation_transition_journal_final_entry_count",
        "auxiliary_transition_journal_after_inventory_entry_count",
        "auxiliary_transition_journal_after_terminal_entry_count",
        "auxiliary_transition_journal_prefix_entry_count",
        "available_and_quota_required_after_destination_before_auxiliary_reservation_bytes",
        "available_bytes_after_reservation",
        "available_bytes_before_reservation",
        "available_inodes_after_reservation",
        "budget",
        "bytes",
        "capacity_partition_bytes",
        "combined_available_and_quota_required_before_reservation_bytes",
        "custody_bytes",
        "decision_path_qualification_case_count",
        "design_minimum_selected_count",
        "destination_reservation_required_bytes",
        "disjoint_allocation_and_directory_charge_bytes",
        "enforced_quota_bytes",
        "entry_count",
        "environment_drift_case_count",
        "estimate_path_qualification_case_count",
        "exclusive_reserved_headroom_bytes",
        "exclusive_root_charge_baseline_bytes",
        "exclusive_root_charge_current_bytes",
        "execution_failure_before_deadline",
        "expected_estimand_count_supported",
        "expected_request_count_supported",
        "expected_seed_count",
        "fd_leak_case_count",
        "hold_allocated_bytes",
        "hold_inode",
        "inode",
        "interval_path_qualification_case_count",
        "key_count",
        "lines",
        "logical_request_count",
        "logical_request_ordinal",
        "logical_request_ordinal_max",
        "logical_request_ordinal_min",
        "logical_reserved_bytes",
        "maximum_auxiliary_artifact_logical_bytes",
        "maximum_auxiliary_reserved_bytes",
        "maximum_logical_bytes",
        "observed_allocation_and_directory_charge_bytes",
        "observed_bytes",
        "ordinal",
        "physical_reservation_sum_bytes",
        "physically_allocated_auxiliary_metadata_bytes",
        "physically_allocated_reservation_bytes",
        "preexecution_refusal_before_deadline",
        "preimage_bytes",
        "primary_slot_count",
        "process_group_cleanup_case_count",
        "public_exponent",
        "qualification_case_count",
        "qualification_test_count",
        "quota_headroom_bytes_after_reservation",
        "quota_headroom_bytes_before_reservation",
        "raw_length",
        "raw_offset",
        "reachability_case_count",
        "request_count",
        "request_length",
        "request_offset",
        "reserved_bytes",
        "returned_rejection_exhausted_before_deadline",
        "returned_rejection_selected_before_deadline",
        "returned_sir_selected_before_deadline",
        "row_ordinal",
        "seed_count",
        "seed_ordinal",
        "seed_ordinal_max",
        "seed_ordinal_min",
        "shard_count",
        "shard_ordinal",
        "signoff_count",
        "slot_ordinal",
        "stable_length",
        "stable_offset",
        "stderr_frame_length",
        "stderr_offset",
        "stderr_payload_length",
        "timeout_case_count",
        "timeout_censored_at_deadline",
        "total_allocated_reserved_bytes",
        "total_bytes",
        "total_logical_reserved_bytes",
        "unique_nonhold_artifact_allocated_bytes",
        "usable_reserved_bytes_after_allocation",
    }
)

_I_PREDICATE_OPERATION_IDS = frozenset(
    {
        "all-equal",
        "contiguous-cover",
        "cross-constraint-satisfied",
        "digest-sequence-equal",
        "discriminated-union",
        "exact-equal",
        "field-rule-satisfied",
        "integer-formula-equal",
        "integer-sum-equal",
        "length-equal",
        "logical-and",
        "logical-not",
        "logical-or",
        "member-of",
        "not-equal",
        "ordered-equal",
        "relative-path-template-match",
        "rsa-pss-verify",
        "sha256-body-equal",
        "sha256-raw-equal",
        "strictly-increasing",
        "utc-interval-contained",
    }
)

_I_RECORD_DOMAINS = {
    "predecessor": b"cp65-predecessor-custody-v1",
    "field": b"cp65-field-rule-v1",
    "artifact": b"cp65-artifact-schema-v1",
    "transient": b"cp65-transient-path-contract-v1",
    "digest": b"cp65-digest-preimage-contract-v1",
    "pointer": b"cp65-sha256-pointer-contract-v1",
    "predicate": b"cp65-predicate-contract-v1",
    "gate": b"cp65-gate-requirement-v1",
    "bound": b"cp65-auxiliary-artifact-bound-v1",
    "proof": b"cp65-auxiliary-size-proof-v1",
    "signature": b"cp65-authorization-signature-contract-v1",
    "bundle": b"cp65-production-schema-preimage-validator-bundle-v1",
}

_I_ARTIFACT_BY_ID = {row[0]: row for row in _I_ARTIFACT_DECLARATIONS}
_I_GLOBAL_PATHS = tuple(
    row[1] for row in _I_ARTIFACT_DECLARATIONS if row[2] == "global"
)
_I_PER_SHARD_PATHS = tuple(
    row[1] for row in _I_ARTIFACT_DECLARATIONS if row[2] == "per-shard"
)
_I_CONDITIONAL_PATHS = tuple(
    row[1] for row in _I_ARTIFACT_DECLARATIONS if row[2] == "conditional-global"
)
_I_DESTINATION_IDS = (
    "shard-requests",
    "shard-raw-records",
    "shard-stable-traces",
    "shard-stderr-records",
)
_I_CLOSED_REFUSAL_CODES = (
    "plan_validation_refusal",
    "provider_reference_binding_refusal",
    "resource_preflight_refusal",
    "runtime_binding_refusal",
    "other_preexecution_refusal",
)
_I_CLOSED_FAILURE_CODES = (
    "reference_sampling_failure",
    "score_evaluation_failure",
    "quota_certification_failure",
    "float64_normalization_failure",
    "categorical_selection_failure",
    "structural_result_validation_failure",
    "other_execution_failure",
)
_I_REQUIRED_REVIEWER_ROLES = (
    "protocol-and-provenance-reviewer",
    "runtime-and-durability-reviewer",
    "statistical-power-and-decision-reviewer",
    "independent-recomputation-reviewer",
)
_I_POWER_PRIMARY_SLOT_IDS = tuple(
    "cp65-power-primary-slot-%02d" % ordinal for ordinal in range(1, 33)
)
_I_CP63_SCHEMA_VERSION = "cp63-test28-runner-recomputation-rehearsal-v1"
_I_CP61_STABLE_DESIGN_SHA256 = (
    "b3ddc5f16c20ee3e2325cfa37f5b9c10e8c3f52bf66b747921c33bcb40eb41bb"
)
_I_CP63_RUNTIME_LOCK_SHA256 = (
    "5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460"
)

_I_M1_FEATURE_SUFFIXES = (
    "count/eq/0",
    "count/eq/1",
    "type/0/occupancy",
    "type/1/occupancy",
    "coordinate/1/axis0/odd",
    "coordinate/1/axis0/even",
)
_I_M2_FEATURE_SUFFIXES = (
    "count/eq/0",
    "count/eq/1",
    "count/eq/2",
    "type/0/occupancy",
    "type/1/occupancy",
    "coordinate/0/axis0/odd",
    "coordinate/0/axis0/even",
    "coordinate/1/axis0/odd",
    "coordinate/1/axis0/even",
    "coordinate/1/axis1/odd",
    "coordinate/1/axis1/even",
    "coordinate/1/diag-plus-3-4/odd",
    "coordinate/1/diag-plus-3-4/even",
    "coordinate/1/diag-minus-3-4/odd",
    "coordinate/1/diag-minus-3-4/even",
    "pair-type/0/0",
    "pair-type/0/1",
    "pair-type/1/1",
    "pair-projection/0/axis0/0/axis0",
    "pair-projection/0/axis0/1/axis0",
    "pair-projection/0/axis0/1/axis1",
    "pair-projection/0/axis0/1/diag-plus-3-4",
    "pair-projection/0/axis0/1/diag-minus-3-4",
    "pair-projection/1/axis0/1/axis0",
    "pair-projection/1/axis0/1/axis1",
    "pair-projection/1/axis0/1/diag-plus-3-4",
    "pair-projection/1/axis0/1/diag-minus-3-4",
    "pair-projection/1/axis1/1/axis1",
    "pair-projection/1/axis1/1/diag-plus-3-4",
    "pair-projection/1/axis1/1/diag-minus-3-4",
    "pair-projection/1/diag-plus-3-4/1/diag-plus-3-4",
    "pair-projection/1/diag-plus-3-4/1/diag-minus-3-4",
    "pair-projection/1/diag-minus-3-4/1/diag-minus-3-4",
)


def _i_record(kind: str, values: dict) -> dict:
    try:
        domain = _I_RECORD_DOMAINS[kind]
    except KeyError as exc:
        raise RuntimeError("unknown independent catalog record kind") from exc
    return _seal_plain_record(domain, values)


def _i_record_semantics(record: dict) -> dict:
    if type(record) is not dict or set(record).isdisjoint({"record_sha256"}):
        raise TypeError("catalog record differs")
    return {key: value for key, value in record.items() if key != "record_sha256"}


def _i_estimand_ids() -> Tuple[str, ...]:
    result = []
    rejection_observables = (
        "returned-rejection-selected-before-deadline",
        "returned-rejection-exhausted-before-deadline",
        "preexecution-refusal-before-deadline",
        "execution-failure-before-deadline",
        "timeout-censored-at-deadline",
    )
    sir_observables = (
        "returned-sir-selected-before-deadline",
        "preexecution-refusal-before-deadline",
        "execution-failure-before-deadline",
        "timeout-censored-at-deadline",
    )
    for _ordinal, row_key, _fixture, strategy, _budget, _digest in _I_ROW_INVENTORY:
        suffixes = (
            rejection_observables
            if strategy == "bounded-rejection"
            else sir_observables
        )
        result.extend("cp61/observable/" + row_key + "/" + item for item in suffixes)
    for _ordinal, row_key, _fixture, strategy, budget, _digest in _I_ROW_INVENTORY:
        if strategy == "bounded-rejection":
            result.extend(
                "cp61/rejection-first-attempt/" + row_key + "/attempt-%d" % attempt
                for attempt in range(1, budget + 1)
            )
    for _ordinal, row_key, fixture, _strategy, _budget, _digest in _I_ROW_INVENTORY:
        suffixes = (
            _I_M1_FEATURE_SUFFIXES if fixture == "T28-M1-Q" else _I_M2_FEATURE_SUFFIXES
        )
        result.extend(
            "cp61/selected-feature/" + row_key + "/" + item for item in suffixes
        )
    if len(result) != 554 or len(set(result)) != 554:
        raise RuntimeError("independent CP61 estimand grammar differs")
    return tuple(result)


_I_CP61_ESTIMAND_IDS = _i_estimand_ids()


def _i_artifact_maximum_bytes(artifact_id: str) -> int:
    overrides = {
        "frozen-protocol": 16_777_216,
        "frozen-protocol-sha256": 65,
        "frozen-machine-manifest": 16_777_216,
        "dependency-lock": 1_048_576,
        "external-seed-acquisition-journal": 163_840,
        "auxiliary-reservation-transition-journal": 65_536,
        "seed-capsule-body": 131_072,
        "reservation-manifest": 268_435_456,
        "primary-metrics": 268_435_456,
        "secondary-diagnostics": 536_870_912,
        "postexecution-independent-recomputation": 536_870_912,
        "frozen-source-fixture-materialization": 134_217_728,
        "shard-requests": 67_109_888,
        "shard-raw-records": 17_179_870_208,
        "shard-stable-traces": 8_589_935_616,
        "shard-stderr-records": 1_073_750_016,
        "shard-rng-initial-states": 134_217_728,
        "shard-rng-final-states": 134_217_728,
        "shard-index": 134_217_728,
        "shard-receipt": 134_217_728,
    }
    return overrides.get(artifact_id, 67_108_864)


def _i_artifact_minimum_bytes(artifact_id: str, has_json_keys: bool) -> int:
    fixed = {
        "frozen-protocol-sha256": 65,
        "external-seed-acquisition-journal": 163_840,
        "auxiliary-reservation-transition-journal": 65_536,
    }
    return fixed.get(artifact_id, 2 if has_json_keys else 0)


def _i_build_bounds() -> Tuple[dict, ...]:
    destination_reserved = {
        "shard-requests": 67_109_888,
        "shard-stable-traces": 8_589_935_616,
        "shard-stderr-records": 1_073_750_016,
        "shard-raw-records": 24_628_942_848,
    }
    reserved_overrides = {
        "reservation-manifest": 268_435_456,
        "primary-metrics": 268_435_456,
        "secondary-diagnostics": 536_870_912,
        "postexecution-independent-recomputation": 536_870_912,
        "external-digest-preimage-registry": 67_108_864,
        "frozen-source-fixture-materialization": 134_217_728,
        "auxiliary-reservation-transition-journal": 65_536,
        "shard-rng-initial-states": 134_217_728,
        "shard-rng-final-states": 134_217_728,
        "shard-index": 134_217_728,
        "shard-receipt": 134_217_728,
    }
    result = []
    authorization_aliases = (
        "launch-authorization",
        "rejected-launch-authorization-candidate",
    )
    for (
        artifact_id,
        _path,
        scope,
        _media,
        _keys,
        _nested,
        _domain,
        _old,
    ) in _I_ARTIFACT_DECLARATIONS:
        count = 32 if scope == "per-shard" else 1
        reserved = destination_reserved.get(
            artifact_id, reserved_overrides.get(artifact_id, 67_108_864)
        )
        aliased = artifact_id in authorization_aliases
        result.append(
            _i_record(
                "bound",
                {
                    "schema_version": CP65_TEST28_SCHEMA_VERSION,
                    "bound_id": "aux-bound:" + artifact_id,
                    "artifact_id": artifact_id,
                    "physical_slot_group_id": (
                        "auxiliary-slot:launch-authorization-candidate"
                        if aliased
                        else "auxiliary-slot:" + artifact_id
                    ),
                    "mutually_exclusive_artifact_ids": (
                        authorization_aliases if aliased else (artifact_id,)
                    ),
                    "maximum_instance_count": count,
                    "maximum_logical_bytes_per_instance": _i_artifact_maximum_bytes(
                        artifact_id
                    ),
                    "maximum_reserved_bytes_per_instance": reserved,
                    "maximum_total_reserved_bytes": count * reserved,
                    "simultaneous_presence_rule_id": (
                        "mutual-exclusion:launch-or-rejected-authorization"
                        if aliased
                        else "presence:" + artifact_id
                    ),
                    "reservation_partition_id": (
                        "destination-reservation"
                        if artifact_id in _I_DESTINATION_IDS
                        else "exclusive-auxiliary-metadata-reservation"
                    ),
                    "destination_reservation_excluded": artifact_id
                    not in _I_DESTINATION_IDS,
                },
            )
        )
    result.append(
        _i_record(
            "bound",
            {
                "schema_version": CP65_TEST28_SCHEMA_VERSION,
                "bound_id": "allocation-and-directory-charge-policy-slot",
                "artifact_id": "__allocation_and_directory_charge_policy_slot__",
                "physical_slot_group_id": "auxiliary-slot:allocation-and-directory-charge-policy",
                "mutually_exclusive_artifact_ids": (
                    "__allocation_and_directory_charge_policy_slot__",
                ),
                "maximum_instance_count": 1,
                "maximum_logical_bytes_per_instance": 0,
                "maximum_reserved_bytes_per_instance": 1_073_741_824,
                "maximum_total_reserved_bytes": 1_073_741_824,
                "simultaneous_presence_rule_id": "always-reserved-with-auxiliary-partition",
                "reservation_partition_id": "exclusive-auxiliary-metadata-reservation",
                "destination_reservation_excluded": False,
            },
        )
    )
    return tuple(result)


def _i_auxiliary_slots(bounds: Tuple[dict, ...]) -> Tuple[Tuple[object, ...], ...]:
    by_id = {
        row["artifact_id"]: row
        for row in bounds
        if not row["artifact_id"].startswith("__")
    }
    result = []
    for (
        artifact_id,
        path,
        scope,
        _media,
        _keys,
        _nested,
        _domain,
        _old,
    ) in _I_ARTIFACT_DECLARATIONS:
        if (
            artifact_id in _I_DESTINATION_IDS
            or artifact_id == "rejected-launch-authorization-candidate"
        ):
            continue
        if scope == "per-shard":
            for ordinal in range(1, 33):
                final_path = path.replace("{shard_id}", "shard-%04d" % ordinal)
                result.append(
                    (
                        artifact_id,
                        final_path,
                        "",
                        by_id[artifact_id]["maximum_logical_bytes_per_instance"],
                        by_id[artifact_id]["maximum_reserved_bytes_per_instance"],
                        "UNCONDITIONAL",
                        "",
                    )
                )
        else:
            alternate_path = (
                _I_ARTIFACT_BY_ID["rejected-launch-authorization-candidate"][1]
                if artifact_id == "launch-authorization"
                else ""
            )
            primary_arm, alternate_arm = "UNCONDITIONAL", ""
            if artifact_id == "launch-authorization":
                primary_arm, alternate_arm = (
                    "AUTHORIZATION",
                    "PREAUTHORIZATION_TERMINAL",
                )
            elif artifact_id == "committed-marker":
                primary_arm = "DIRECT_O_EXCL_AFTER_HOLD_RELEASE"
            elif artifact_id == "auxiliary-reservation-transition-journal":
                primary_arm = "IN_PLACE_TRANSITION_JOURNAL"
            result.append(
                (
                    artifact_id,
                    path,
                    alternate_path,
                    by_id[artifact_id]["maximum_logical_bytes_per_instance"],
                    by_id[artifact_id]["maximum_reserved_bytes_per_instance"],
                    primary_arm,
                    alternate_arm,
                )
            )
    result.sort(key=lambda row: row[1])
    if len(result) != 183 or len({row[1] for row in result}) != 183:
        raise RuntimeError("independent auxiliary slot expansion differs")
    return tuple(result)


def _i_string_domain(
    artifact_id: str, pointer: str, key: str, bounds: Tuple[dict, ...]
) -> Tuple[str, ...]:
    domain = _I_STRING_DOMAINS.get((artifact_id, key), ())
    if artifact_id == "production-schedule":
        if pointer == "/requests/*/schema_version":
            return (_I_CP63_SCHEMA_VERSION,)
        if pointer == "/requests/*/row_key":
            return tuple(row[1] for row in _I_ROW_INVENTORY)
        if pointer == "/requests/*/fixture_id":
            return tuple(dict.fromkeys(row[2] for row in _I_ROW_INVENTORY))
        if pointer == "/requests/*/strategy":
            return tuple(dict.fromkeys(row[3] for row in _I_ROW_INVENTORY))
    if artifact_id == "closed-refusal-failure-classifier-qualification-receipt":
        if pointer == "/closed_refusal_codes/*":
            return _I_CLOSED_REFUSAL_CODES
        if pointer == "/closed_failure_codes/*":
            return _I_CLOSED_FAILURE_CODES
    if artifact_id == "preflight-gate-summary":
        if pointer == "/covered_gate_ids/*":
            return _I_GATE_IDS[:15]
        if pointer == "/covered_gate_states/*":
            return ("PASS",)
        if pointer == "/covered_evidence_node_ids/*":
            return _I_GATE_EVIDENCE_NODES[:15]
    if pointer == "/required_reviewer_roles/*" and artifact_id in (
        "independent-signoff-set",
        "independent-reviewer-public-key-set",
    ):
        return _I_REQUIRED_REVIEWER_ROLES
    if artifact_id == "auxiliary-metadata-reservation" and pointer.startswith(
        "/artifact_entries/*/"
    ):
        slots = _i_auxiliary_slots(bounds)
        column = {
            "artifact_id": 0,
            "primary_publication_arm_id": 5,
            "alternate_publication_arm_id": 6,
        }.get(key)
        if column is not None:
            return tuple(dict.fromkeys(str(row[column]) for row in slots))
    return domain


def _i_field_kind(key: str, nested_keys: Tuple[str, ...] = ()) -> str:
    if key == "terminal_counts":
        return "object"
    if nested_keys or key in _I_ARRAY_KEYS:
        return "array"
    if key in _I_BOOLEAN_KEYS:
        return "boolean"
    return "integer" if key in _I_INTEGER_FIELD_NAMES else "string"


def _i_pattern_id(key: str) -> str:
    if key.endswith("_sha256") or key == "sha256":
        return "lowercase-sha256-hex"
    if key.endswith("_signature_hex") or key in ("signature_hex", "modulus_hex"):
        return "lowercase-hex-768"
    if key == "plan_seed_hex" or "seed_value" in key:
        return "lowercase-hex-16"
    if key.endswith("_utc"):
        return "utc-microseconds-z"
    if "path" in key or key == "relative_directory":
        return "posix-relative-path"
    if key == "shard_id":
        return "shard-id-0001-through-0032"
    if key == "attempt_id":
        return "attempt-id-v1"
    if (
        key.endswith("_method_id")
        or key.endswith("_session_id")
        or key.endswith("_authority_id")
        or key == "authority_id"
    ):
        return "opaque-method-session-authority-id-v1"
    if key == "threshold_value":
        return "canonical-rational-threshold-v1"
    return "bounded-nonempty-ascii"


def _i_field_rule(
    artifact_id: str,
    pointer: str,
    key: str,
    bounds: Tuple[dict, ...],
    nested_keys: Tuple[str, ...] = (),
) -> dict:
    exact_integer = _I_INTEGER_EXACT.get((artifact_id, key))
    kind = _i_field_kind(key, nested_keys)
    if (
        exact_integer is not None
        or "/terminal_counts/" in pointer
        or key in ("lines", "budget")
    ):
        kind = "integer"
    integer_interval = (
        (exact_integer, exact_integer)
        if exact_integer is not None
        else ((0, 2**64 - 1) if kind == "integer" else ())
    )
    integer_interval = _I_INTEGER_INTERVALS.get(
        (artifact_id, pointer), integer_interval
    )
    if artifact_id == "external-digest-preimage-registry" and key == "preimage_bytes":
        integer_interval = (0, 65_536)
    if artifact_id == "source-manifest" and pointer == "/entry_count":
        integer_interval = (1, 4_096)
    exact_length = _I_ARRAY_LENGTH_EXACT.get((artifact_id, key))
    if exact_length is not None:
        length_interval = (exact_length, exact_length)
    elif kind == "array":
        length_interval = (0, 32_768)
    elif kind == "string":
        length_interval = (1, 1_048_576)
    else:
        length_interval = ()
    domains = _i_string_domain(artifact_id, pointer, key, bounds)
    if artifact_id == "source-manifest" and pointer == "/entries/*/role":
        domains = ("production-runner-source", "independent-recomputation-source")
    if artifact_id == "power-threshold-receipt":
        if key == "gate_id":
            domains = _I_POWER_PRIMARY_SLOT_IDS
        elif key == "estimand_id":
            domains = _I_CP61_ESTIMAND_IDS
        elif key == "threshold_encoding":
            domains = (
                "canonical-rational-signed-numerator-positive-denominator-lowest-terms-v1",
            )
    if key == "terminal_state" and artifact_id in (
        "preauthorization-outcome",
        "postauthorization-outcome",
    ):
        domains, length_interval = (
            "",
            "INVALID_PROTOCOL",
            "ABORTED_INFRA",
            "INCOMPLETE",
        ), (0, 16)
    if artifact_id == "auxiliary-metadata-reservation" and key in (
        "alternate_final_relative_path",
        "alternate_publication_arm_id",
        "partial_relative_path",
        "file_fsync_completed_at_utc",
        "directory_fsync_completed_at_utc",
    ):
        length_interval = (0, 1_048_576)
    if artifact_id == "power-threshold-receipt":
        if pointer == "/power_review_ascii":
            length_interval = (1, 1_048_576)
        elif pointer in (
            "/selected_count_justification_ascii",
            "/ordered_slot_thresholds/*/justification_ascii",
        ):
            length_interval = (1, 16_384)
    if artifact_id == "external-digest-preimage-registry":
        if pointer in ("/entries", "/ordered_entry_sha256s"):
            length_interval = (0, 4_096)
        elif pointer.endswith("/preimage_ascii"):
            length_interval = (0, 131_072)
    if artifact_id == "source-manifest" and pointer == "/entries":
        length_interval = (1, 4_096)
    if (
        artifact_id
        in (
            "preterminal-durable-artifact-inventory",
            "sha256-manifest",
        )
        and pointer == "/entries"
    ):
        length_interval = (1, 312)
    if (
        artifact_id == "independent-signoff-set"
        and pointer == "/ordered_signoffs/*/reviewed_artifact_sha256s"
    ):
        length_interval = (1, 1)
    pattern_id = _i_pattern_id(key) if kind == "string" else ""
    if pattern_id == "lowercase-sha256-hex":
        length_interval = (64, 64)
    elif pattern_id == "lowercase-hex-16":
        length_interval = (16, 16)
    elif pattern_id == "lowercase-hex-768":
        length_interval = (768, 768)
    elif pattern_id == "utc-microseconds-z":
        length_interval = (27, 27)
    declaration = _I_ARTIFACT_BY_ID[artifact_id]
    if key == "schema" and declaration[6]:
        domains = (declaration[6],)
    if kind == "array" and nested_keys:
        item_rule_ids = tuple(
            "%s:/%s/*/%s" % (artifact_id, pointer.strip("/"), child)
            for child in nested_keys
        )
    elif kind == "array":
        item_rule_ids = ("%s:/%s/*" % (artifact_id, pointer.strip("/")),)
    else:
        item_rule_ids = ()
    cross_ids = tuple(
        "constraint:" + predicate_id
        for predicate_id, artifact_ids, _operation, pointers, _operand in _I_CROSS_PREDICATE_SPECS
        if artifact_id in artifact_ids and pointer in pointers
    )
    return _i_record(
        "field",
        {
            "schema_version": CP65_TEST28_SCHEMA_VERSION,
            "rule_id": "%s:%s" % (artifact_id, pointer),
            "artifact_id": artifact_id,
            "json_pointer": pointer,
            "value_kind": kind,
            "required": True,
            "integer_interval": integer_interval,
            "length_interval": length_interval,
            "boolean_domain": (
                (
                    (True,)
                    if artifact_id == "committed-marker"
                    and key == "hold_absence_verified"
                    else (
                        (False,)
                        if key
                        in (
                            "production_runner_rng_or_child_started_before_receipt",
                            "topup_redraw_reselection_permitted",
                        )
                        else (False, True)
                    )
                )
                if kind == "boolean"
                else ()
            ),
            "string_domain": domains,
            "string_pattern_id": pattern_id,
            "array_item_rule_ids": item_rule_ids,
            "exact_object_keys": nested_keys,
            "cross_constraint_ids": (
                ("field:%s:%s" % (artifact_id, pointer),)
                + (
                    ("independent-signoff-reviewed-summary-raw-binding",)
                    if artifact_id == "independent-signoff-set"
                    and pointer == "/ordered_signoffs/*/reviewed_artifact_sha256s"
                    else ()
                )
                + cross_ids
            ),
        },
    )


def _i_build_field_rules(bounds: Tuple[dict, ...]) -> Tuple[dict, ...]:
    result = []
    for (
        artifact_id,
        _path,
        _scope,
        _media,
        keys,
        nested,
        _domain,
        _old,
    ) in _I_ARTIFACT_DECLARATIONS:
        nested_by_key = dict(nested)
        for key in keys:
            children = nested_by_key.get(key, ())
            result.append(_i_field_rule(artifact_id, "/" + key, key, bounds, children))
            for child in children:
                child_pointer = (
                    "/%s/%s" % (key, child)
                    if key == "terminal_counts"
                    else "/%s/*/%s" % (key, child)
                )
                result.append(_i_field_rule(artifact_id, child_pointer, child, bounds))
                if _i_field_kind(child) == "array":
                    result.append(
                        _i_field_rule(
                            artifact_id,
                            child_pointer + "/*",
                            child[:-1] or "item",
                            bounds,
                        )
                    )
        for key in keys:
            if key not in nested_by_key and _i_field_kind(key) == "array":
                result.append(
                    _i_field_rule(
                        artifact_id,
                        "/%s/*" % key,
                        key[:-1] or "item",
                        bounds,
                    )
                )
    if len(result) != 801:
        raise RuntimeError("independent field-rule count differs")
    return tuple(result)


def _i_raw_node(artifact_id: str) -> str:
    return "digest:" + artifact_id + ":raw-sha256"


def _i_body_node(artifact_id: str) -> str:
    return "digest:" + artifact_id + ":body-sha256"


def _i_build_artifact_schemas(field_rules: Tuple[dict, ...]) -> Tuple[dict, ...]:
    by_artifact = {}
    for rule in field_rules:
        by_artifact.setdefault(rule["artifact_id"], []).append(rule["rule_id"])
    result = []
    for (
        artifact_id,
        path,
        scope,
        media,
        keys,
        _nested,
        _domain,
        preserved,
    ) in _I_ARTIFACT_DECLARATIONS:
        final_newline = "none"
        if media == "sha256-text":
            final_newline = "exactly-one-lf"
        elif media == "referenced-predecessor-jsonl":
            final_newline = "one-lf-per-record-including-final-record"
        elif media in (
            "binary-journal",
            "binary-transition-journal",
            "referenced-predecessor-binary-frames",
        ):
            final_newline = "not-applicable-no-trailing-bytes"
        has_body = "body_sha256" in keys
        digest_id = (
            "launch-authorization:body-sha256"
            if artifact_id == "rejected-launch-authorization-candidate"
            else artifact_id + (":body-sha256" if has_body else ":raw-sha256")
        )
        nodes = (
            (
                "digest:launch-authorization:body-sha256",
                _i_raw_node(artifact_id),
            )
            if artifact_id == "rejected-launch-authorization-candidate"
            else (
                (_i_body_node(artifact_id), _i_raw_node(artifact_id))
                if has_body
                else (_i_raw_node(artifact_id),)
            )
        )
        result.append(
            _i_record(
                "artifact",
                {
                    "schema_version": CP65_TEST28_SCHEMA_VERSION,
                    "artifact_id": artifact_id,
                    "path_template": path,
                    "path_scope": scope,
                    "presence_rule_id": "presence:" + artifact_id,
                    "encoding": "ascii-canonical-json"
                    if "canonical-json" in media
                    else "exact-bytes",
                    "media_kind": media,
                    "exact_keys": keys,
                    "field_rule_ids": tuple(by_artifact.get(artifact_id, ())),
                    "record_rule_id": "record:" + artifact_id,
                    "minimum_instances": 0,
                    "maximum_instances": 32 if scope == "per-shard" else 1,
                    "minimum_bytes_per_instance": _i_artifact_minimum_bytes(
                        artifact_id, bool(keys)
                    ),
                    "maximum_bytes_per_instance": _i_artifact_maximum_bytes(
                        artifact_id
                    ),
                    "final_newline_rule": final_newline,
                    "digest_preimage_contract_id": digest_id,
                    "dag_node_ids": nodes,
                    "auxiliary_reservation_class": (
                        "destination-reservation"
                        if artifact_id in _I_DESTINATION_IDS
                        else "exclusive-auxiliary-metadata-reservation"
                    ),
                    "cp64_contract_preserved": preserved,
                    "definition_only": True,
                },
            )
        )
    return tuple(result)


def _i_expanded_final_paths() -> Tuple[Tuple[str, str, int], ...]:
    rows = []
    for artifact_id, path, scope, *_rest in _I_ARTIFACT_DECLARATIONS:
        if scope == "per-shard":
            rows.extend(
                (
                    artifact_id,
                    path.replace("{shard_id}", "shard-%04d" % ordinal),
                    ordinal,
                )
                for ordinal in range(1, 33)
            )
        else:
            rows.append((artifact_id, path, 0))
    rows.sort(key=lambda row: row[1])
    if len(rows) != 312 or len({row[1] for row in rows}) != 312:
        raise RuntimeError("independent final path expansion differs")
    return tuple(rows)


def _i_build_transients(bounds: Tuple[dict, ...]) -> Tuple[dict, ...]:
    rows = []
    final_rows = _i_expanded_final_paths()
    shard_by_artifact_path = {(a, p): s for a, p, s in final_rows}
    for artifact_id in _I_DESTINATION_IDS:
        template = _I_ARTIFACT_BY_ID[artifact_id][1]
        for ordinal in range(1, 33):
            final_path = template.replace("{shard_id}", "shard-%04d" % ordinal)
            rows.append(
                (
                    artifact_id,
                    final_path,
                    "",
                    final_path + ".partial",
                    "per-shard",
                    ordinal,
                    "destination-reserved-partial",
                    False,
                    "UNCONDITIONAL",
                    "",
                )
            )
    for (
        artifact_id,
        final_path,
        alternate_path,
        _logical,
        _reserved,
        primary,
        alternate,
    ) in _i_auxiliary_slots(bounds):
        if artifact_id in (
            "committed-marker",
            "auxiliary-reservation-transition-journal",
        ):
            continue
        rows.append(
            (
                artifact_id,
                final_path,
                alternate_path,
                final_path + ".partial",
                _I_ARTIFACT_BY_ID[artifact_id][2],
                shard_by_artifact_path[(artifact_id, final_path)],
                "auxiliary-partial-candidate",
                artifact_id == "launch-authorization",
                primary,
                alternate,
            )
        )
    rows.append(
        (
            "__auxiliary_dynamic_hold__",
            "",
            "",
            ".cp65_auxiliary_reservation_hold.partial",
            "global",
            0,
            "dynamic-auxiliary-reservation-hold",
            False,
            "",
            "",
        )
    )
    rows.sort(key=lambda row: row[3])
    final_paths = {row[1] for row in final_rows}
    if len(rows) != 310 or len({row[3] for row in rows}) != 310:
        raise RuntimeError("independent transient path expansion differs")
    if final_paths.intersection(row[3] for row in rows):
        raise RuntimeError("independent final/transient path collision")
    result = []
    for ordinal, row in enumerate(rows, 1):
        (
            artifact_id,
            final_path,
            alternate_path,
            transient_path,
            scope,
            shard,
            kind,
            prepared,
            primary,
            alternate,
        ) = row
        result.append(
            _i_record(
                "transient",
                {
                    "schema_version": CP65_TEST28_SCHEMA_VERSION,
                    "transient_ordinal": ordinal,
                    "transient_path_id": "transient-path:%04d" % ordinal,
                    "owner_artifact_id": artifact_id,
                    "final_relative_path": final_path,
                    "alternate_final_relative_path": alternate_path,
                    "transient_relative_path": transient_path,
                    "primary_publication_arm_id": primary,
                    "alternate_publication_arm_id": alternate,
                    "path_scope": scope,
                    "shard_ordinal": shard,
                    "transient_kind": kind,
                    "aliases_final_inode_when_published": artifact_id
                    != "__auxiliary_dynamic_hold__",
                    "prepared_authorization_alias": prepared,
                    "retained_at_committed": False,
                    "sha256_manifest_included": False,
                    "collision_free": True,
                    "definition_only": True,
                },
            )
        )
    return tuple(result)


def _i_digest(
    contract_id: str,
    artifact_id: str,
    pointer: str,
    domain: str,
    zeroed: Tuple[str, ...],
    components: Tuple[str, ...],
    canonical_profile_id: str = "",
) -> dict:
    return _i_record(
        "digest",
        {
            "schema_version": CP65_TEST28_SCHEMA_VERSION,
            "contract_id": contract_id,
            "artifact_id": artifact_id,
            "digest_field_pointer": pointer,
            "algorithm_id": "sha256",
            "domain_separator": domain + ("\0" if domain else ""),
            "canonical_profile_id": canonical_profile_id
            or (_CANONICAL_PROFILE_ID if domain else "exact-raw-bytes-v1"),
            "zeroed_field_pointers": zeroed,
            "ordered_component_ids": components,
            "output_encoding": "64-lowercase-hex",
            "output_bytes": 32,
            "verifier_implemented": True,
            "definition_only": True,
        },
    )


def _i_is_sha256_rule(rule: dict) -> bool:
    parts = rule["json_pointer"].split("/")
    leaf = parts[-1]
    parent = parts[-2] if len(parts) > 1 else ""
    return (
        leaf == "sha256"
        or leaf.endswith("_sha256")
        or (leaf == "*" and parent.endswith("_sha256s"))
    )


def _i_intrinsic_owned_sha256_keys() -> frozenset:
    keys = {
        (artifact_id, "/%s/*/%s" % (array_key, digest_key))
        for (artifact_id, array_key), (digest_key, _domain) in _I_NESTED_DIGESTS.items()
    }
    keys.update(
        (artifact_id, pointer)
        for _contract, artifact_id, pointer, _domain, _zeroed, _components, *_rest in _I_INTERNAL_DIGEST_DECLARATIONS
        if pointer.startswith("/")
    )
    keys.update(
        (artifact_id, "/body_sha256")
        for artifact_id, _path, _scope, _media, artifact_keys, *_rest in _I_ARTIFACT_DECLARATIONS
        if "body_sha256" in artifact_keys
        and artifact_id != "rejected-launch-authorization-candidate"
    )
    return frozenset(keys)


_I_INTRINSIC_SHA256_KEYS = _i_intrinsic_owned_sha256_keys()


def _i_external_contract_id(artifact_id: str, pointer: str) -> str:
    if (artifact_id, pointer) == (
        "auxiliary-metadata-reservation",
        "/exclusive_root_charge_measurement_sha256",
    ):
        return "auxiliary-metadata-reservation:exclusive-root-charge-measurement-sha256"
    return "external-preimage:%s:%s" % (artifact_id, pointer)


def _i_source_contract_for_artifact(artifact_id: str, *, body: bool = False) -> str:
    return artifact_id + (":body-sha256" if body else ":raw-sha256")


def _i_pointer_source_contract_id(
    artifact_id: str, pointer: str, contracts_by_target: Mapping[Tuple[str, str], str]
) -> str:
    key = (artifact_id, pointer)
    override = _I_SHA256_POINTER_SOURCE_CONTRACT_OVERRIDES.get(key)
    if override is not None:
        return override
    if key in _I_EXTERNAL_REGISTRY_SHA256_POINTERS:
        return _i_external_contract_id(*key)
    own = contracts_by_target.get(key)
    if own is not None:
        return own
    if artifact_id == "rejected-launch-authorization-candidate":
        launch_key = ("launch-authorization", pointer)
        source = contracts_by_target.get(launch_key)
        if source is not None:
            return source
        return _i_pointer_source_contract_id(
            launch_key[0], launch_key[1], contracts_by_target
        )
    leaf = pointer.rsplit("/", 1)[-1]
    raw_artifact = _I_RAW_ARTIFACT_SHA256_FIELD_SOURCES.get(leaf)
    if raw_artifact is not None:
        return _i_source_contract_for_artifact(raw_artifact)
    body_artifact = _I_BODY_ARTIFACT_SHA256_FIELD_SOURCES.get(leaf)
    if body_artifact is not None:
        return _i_source_contract_for_artifact(body_artifact, body=True)
    raise RuntimeError(
        "unclassified independent SHA256 pointer: %s%s" % (artifact_id, pointer)
    )


def _i_build_digest_contracts(field_rules: Tuple[dict, ...]) -> Tuple[dict, ...]:
    if set(_I_SHA256_POINTER_SOURCE_CONTRACT_OVERRIDES).intersection(
        _I_EXTERNAL_REGISTRY_SHA256_POINTERS
    ):
        raise RuntimeError("independent SHA route also appears in registry")
    result = []
    nested_ids = {}
    for (artifact_id, key), (digest_key, domain) in _I_NESTED_DIGESTS.items():
        contract_id = "%s:%s-row-digest" % (artifact_id, key)
        nested_ids.setdefault(artifact_id, []).append(contract_id)
        components = (
            ("power-threshold-receipt:threshold-row-justification-text",)
            if (artifact_id, key)
            == ("power-threshold-receipt", "ordered_slot_thresholds")
            else ()
        )
        result.append(
            _i_digest(
                contract_id,
                artifact_id,
                "/%s/*/%s" % (key, digest_key),
                domain,
                ("/%s/*/%s" % (key, digest_key),),
                components,
            )
        )
    internal_by_artifact = {}
    for declaration in _I_INTERNAL_DIGEST_DECLARATIONS:
        internal_by_artifact.setdefault(declaration[1], []).append(declaration[0])
        result.append(_i_digest(*declaration))
    for (
        artifact_id,
        _path,
        _scope,
        _media,
        keys,
        _nested,
        domain,
        _old,
    ) in _I_ARTIFACT_DECLARATIONS:
        if artifact_id == "rejected-launch-authorization-candidate":
            continue
        has_body = "body_sha256" in keys
        internal = tuple(
            contract_id
            for contract_id in internal_by_artifact.get(artifact_id, ())
            if contract_id != "launch-authorization-candidate:prepared-raw-sha256"
        )
        components = tuple(nested_ids.get(artifact_id, ())) + internal
        result.append(
            _i_digest(
                artifact_id + (":body-sha256" if has_body else ":raw-sha256"),
                artifact_id,
                "/body_sha256" if has_body else "$raw_sha256",
                domain if has_body else "",
                ("/body_sha256",) if has_body else (),
                components,
            )
        )
        if has_body:
            result.append(
                _i_digest(
                    artifact_id + ":raw-sha256",
                    artifact_id,
                    "$raw_sha256",
                    "",
                    (),
                    (artifact_id + ":body-sha256",),
                )
            )
    owned = {(row["artifact_id"], row["digest_field_pointer"]) for row in result}
    sha_keys = tuple(
        (rule["artifact_id"], rule["json_pointer"])
        for rule in field_rules
        if _i_is_sha256_rule(rule)
    )
    if _I_EXTERNAL_REGISTRY_SHA256_POINTERS - set(sha_keys):
        raise RuntimeError("independent registry pointer is not a field rule")
    for artifact_id, pointer in sorted(_I_EXTERNAL_REGISTRY_SHA256_POINTERS):
        if (artifact_id, pointer) in owned:
            raise RuntimeError("independent intrinsic pointer uses registry")
        result.append(
            _i_digest(
                _i_external_contract_id(artifact_id, pointer),
                artifact_id,
                pointer,
                (
                    "cp65-test28-exclusive-root-charge-measurement-v1"
                    if (artifact_id, pointer)
                    == (
                        "auxiliary-metadata-reservation",
                        "/exclusive_root_charge_measurement_sha256",
                    )
                    else ""
                ),
                (),
                (),
                "external-registry-exact-preimage-v1",
            )
        )
        owned.add((artifact_id, pointer))
    by_target = {
        (row["artifact_id"], row["digest_field_pointer"]): row["contract_id"]
        for row in result
    }
    available = {row["contract_id"] for row in result}
    for artifact_id, pointer in sha_keys:
        if (artifact_id, pointer) in owned:
            continue
        if (
            _i_pointer_source_contract_id(artifact_id, pointer, by_target)
            not in available
        ):
            raise RuntimeError("independent SHA source contract is unresolved")
    if len(result) != 211:
        raise RuntimeError("independent digest-contract count differs")
    return tuple(result)


def _i_sha256_source_cut(
    target_artifact_id: str,
    semantic_class: str,
    source_artifact_id: str,
    source_contract_id: str,
) -> str:
    if semantic_class == "externally-retained-preimage" or (
        semantic_class == "conditional-zero-or-cross"
        and target_artifact_id == "auxiliary-metadata-reservation"
    ):
        return "durable-by-gate15-before-registry-finalization"
    if (
        source_contract_id.endswith(":body-sha256")
        and source_artifact_id == target_artifact_id
    ):
        return "intrinsic-same-record"
    if (
        semantic_class in ("nested-domain", "signature", "key-identity")
        and source_artifact_id == target_artifact_id
    ):
        return "intrinsic-same-record"
    if source_contract_id.startswith("auxiliary-reservation-transition-journal:"):
        if source_contract_id.endswith(":final-head") or (
            source_contract_id.endswith(":raw-sha256")
            and target_artifact_id == "committed-marker"
        ):
            return "final-journal-sealed-before-committed"
        if source_contract_id.endswith(":after-terminal"):
            return "terminal-before-manifest"
        if source_contract_id.endswith(":after-inventory"):
            return "preterminal-inventory-before-terminal"
        if source_contract_id.endswith(":preinventory-prefix"):
            return "shards-finalized-before-preterminal-inventory"
        return "durable-by-gate15-before-registry-finalization"
    if source_artifact_id in _I_FROZEN_BEFORE_ACQUISITION_ARTIFACT_IDS:
        return "frozen-before-acquisition-start"
    if source_artifact_id == "external-digest-preimage-registry":
        return "registry-finalized-before-summary"
    if source_artifact_id == "preflight-gate-summary":
        return "summary-finalized-before-signoff"
    if source_artifact_id == "independent-signoff-set":
        return "signoff-finalized-before-authorization"
    if source_artifact_id in (
        "launch-authorization",
        "rejected-launch-authorization-candidate",
    ):
        return "authorization-candidate-prepared-before-preauth-cas"
    if source_artifact_id == "preauthorization-outcome":
        return "preauth-outcome-before-postauth"
    if source_artifact_id == "postauthorization-outcome":
        return "postauth-outcome-before-started-or-terminal"
    if source_artifact_id in ("started-receipt", "launch-receipt"):
        return "started-before-launch-and-terminal"
    if source_artifact_id.startswith("shard-"):
        return "shards-finalized-before-preterminal-inventory"
    if source_artifact_id == "preterminal-durable-artifact-inventory":
        return "preterminal-inventory-before-terminal"
    if source_artifact_id == "terminal-state":
        return "terminal-before-manifest"
    if source_artifact_id == "sha256-manifest":
        return "manifest-before-final-journal-seal"
    return "durable-by-gate15-before-registry-finalization"


def _i_pointer_validator_implemented(
    target_artifact_id: str, pointer: str, source_artifact_id: str
) -> bool:
    if (
        target_artifact_id
        in (
            "preterminal-durable-artifact-inventory",
            "sha256-manifest",
        )
        and pointer == "/entries/*/sha256"
    ):
        return False
    if target_artifact_id == "shard-index" and pointer in {
        "/ordered_request_entries/*/request_sha256",
        "/ordered_request_entries/*/raw_sha256",
        "/ordered_request_entries/*/stable_sha256",
        "/ordered_request_entries/*/stderr_sha256",
        "/ordered_request_entries/*/rng_initial_sha256",
        "/ordered_request_entries/*/rng_final_sha256",
        "/raw_file_sha256",
        "/stable_file_sha256",
        "/stderr_file_sha256",
        "/rng_initial_file_sha256",
        "/rng_final_file_sha256",
    }:
        return False
    if target_artifact_id == "shard-receipt" and pointer in {
        "/requests_file_sha256",
        "/raw_file_sha256",
        "/stable_file_sha256",
        "/stderr_file_sha256",
        "/rng_initial_file_sha256",
        "/rng_final_file_sha256",
    }:
        return False
    return source_artifact_id not in _I_REFERENCED_OUTPUT_IDS


def _i_build_pointer_contracts(
    field_rules: Tuple[dict, ...], digest_contracts: Tuple[dict, ...]
) -> Tuple[dict, ...]:
    by_target = {
        (row["artifact_id"], row["digest_field_pointer"]): row
        for row in digest_contracts
    }
    by_id = {row["contract_id"]: row for row in digest_contracts}
    result, seen = [], set()
    contract_ids_by_target = {key: row["contract_id"] for key, row in by_target.items()}
    conditional_zero = {
        ("preauthorization-outcome", "/prepared_launch_authorization_sha256"): (
            "authorization-arm-nonzero-final-launch-raw;terminal-arm-zero-iff-no-prepared-candidate-else-nonzero-rejected-candidate-raw",
            "preauthorization-prepared-candidate-branch-binding",
        ),
        ("terminal-state", "/launch_authorization_sha256"): (
            "zero-iff-preauthorization-terminal-otherwise-exact-raw-cross",
            "terminal-launch-authorization-arm-binding",
        ),
        ("terminal-state", "/postauthorization_outcome_sha256"): (
            "zero-unless-postauthorization-arm-exact-raw-cross",
            "terminal-postauthorization-outcome-arm-binding",
        ),
        ("terminal-state", "/started_receipt_sha256"): (
            "zero-unless-started-arm-exact-raw-cross",
            "terminal-started-receipt-arm-binding",
        ),
        (
            "auxiliary-metadata-reservation",
            "/artifact_entries/*/device_identity_sha256",
        ): (
            "zero-iff-committed-marker-future-o-excl-covered-by-hold-otherwise-nonzero",
            "auxiliary-device-identity-committed-marker-zero-arm-binding",
        ),
        ("auxiliary-metadata-reservation", "/artifact_entries/*/extent_map_sha256"): (
            "zero-iff-committed-marker-future-o-excl-covered-by-hold-otherwise-nonzero",
            "auxiliary-extent-map-committed-marker-zero-arm-binding",
        ),
    }
    shard_segment_sources = {
        "/ordered_request_entries/*/request_sha256": "shard-requests",
        "/ordered_request_entries/*/raw_sha256": "shard-raw-records",
        "/ordered_request_entries/*/stable_sha256": "shard-stable-traces",
        "/ordered_request_entries/*/stderr_sha256": "shard-stderr-records",
        "/ordered_request_entries/*/rng_initial_sha256": "shard-rng-initial-states",
        "/ordered_request_entries/*/rng_final_sha256": "shard-rng-final-states",
    }
    for rule in field_rules:
        if not _i_is_sha256_rule(rule):
            continue
        target_artifact_id = rule["artifact_id"]
        target_pointer = rule["json_pointer"]
        key = (target_artifact_id, target_pointer, "pointer-wildcards-in-path-order")
        if key in seen:
            raise RuntimeError("duplicate independent SHA pointer classification")
        seen.add(key)
        source_contract_id = _i_pointer_source_contract_id(
            target_artifact_id, target_pointer, contract_ids_by_target
        )
        source_contract = by_id[source_contract_id]
        external = (
            target_artifact_id,
            target_pointer,
        ) in _I_EXTERNAL_REGISTRY_SHA256_POINTERS
        if external:
            semantic_class = "externally-retained-preimage"
            digest_kind = (
                "body-domain-sha256"
                if source_contract["domain_separator"]
                else "plain-raw-bytes-sha256"
            )
            source_artifact_id = "external-digest-preimage-registry"
            source_pointer = "/entries/*/digest_sha256"
        elif source_contract_id.startswith("v15-machine-manifest:"):
            semantic_class, digest_kind = (
                "selected-stored-digest",
                "selected-stored-sha256-cross-binding",
            )
            source_artifact_id = source_contract["artifact_id"]
            source_pointer = source_contract["digest_field_pointer"]
        elif (
            source_contract_id
            == "source-manifest:independent-recomputation-submanifest"
        ):
            semantic_class, digest_kind = (
                "nested-domain-digest",
                "domain-separated-canonical-json-sha256",
            )
            source_artifact_id = source_contract["artifact_id"]
            source_pointer = source_contract["digest_field_pointer"]
        elif source_contract_id.endswith(":body-sha256"):
            semantic_class = (
                "self-body"
                if source_contract["artifact_id"] == target_artifact_id
                and target_pointer == "/body_sha256"
                else "body-artifact"
            )
            digest_kind = "body-domain-sha256"
            source_artifact_id = source_contract["artifact_id"]
            source_pointer = source_contract["digest_field_pointer"]
        elif "raw-signature" in source_contract_id:
            semantic_class, digest_kind = "signature", "plain-raw-bytes-sha256"
            source_artifact_id = source_contract["artifact_id"]
            source_pointer = target_pointer.replace("_sha256", "_hex")
        elif "identity" in source_contract_id:
            semantic_class, digest_kind = "key-identity", "key-identity-domain-sha256"
            source_artifact_id = source_contract["artifact_id"]
            source_pointer = source_contract["digest_field_pointer"]
        elif "journal" in source_contract_id:
            semantic_class, digest_kind = "binary-chain", "ordered-domain-sha256"
            source_artifact_id = source_contract["artifact_id"]
            source_pointer = source_contract["digest_field_pointer"]
        elif any(
            token in source_contract_id
            for token in (
                "row-digest",
                "ordered",
                "segment",
                "selected-entry",
                "selected-target",
                "declared-preimage",
                "request-instance",
                "seed-free-request",
                "selected-evidence",
                "selected-reservation-entry",
            )
        ):
            semantic_class = "nested-domain"
            if (
                "row-digest" in source_contract_id
                or "request-instance" in source_contract_id
                or "seed-free-request" in source_contract_id
            ):
                digest_kind = "record-row-domain-sha256"
            elif any(
                token in source_contract_id
                for token in (
                    "segment",
                    "selected-entry",
                    "selected-target",
                    "declared-preimage",
                    "selected-evidence",
                )
            ):
                digest_kind = "plain-raw-bytes-sha256"
            else:
                digest_kind = "ordered-domain-sha256"
            source_artifact_id = source_contract["artifact_id"]
            source_pointer = source_contract["digest_field_pointer"]
        else:
            semantic_class, digest_kind = "raw-artifact", "plain-raw-file-sha256"
            source_artifact_id = source_contract["artifact_id"]
            source_pointer = source_contract["digest_field_pointer"]
        policy, binding_rule = conditional_zero.get(
            (target_artifact_id, target_pointer),
            ("nonzero-required", "unconditional-classified-digest-binding"),
        )
        if (target_artifact_id, target_pointer) in conditional_zero:
            semantic_class = "conditional-zero-or-cross"
        if (
            target_artifact_id == "shard-index"
            and target_pointer in shard_segment_sources
        ):
            source_artifact_id = shard_segment_sources[target_pointer]
        result.append(
            _i_record(
                "pointer",
                {
                    "schema_version": CP65_TEST28_SCHEMA_VERSION,
                    "classification_id": "sha256-pointer:%s:%s" % key[:2],
                    "target_artifact_id": target_artifact_id,
                    "target_json_pointer": target_pointer,
                    "semantic_class": semantic_class,
                    "digest_kind": digest_kind,
                    "source_artifact_id": source_artifact_id,
                    "source_json_pointer": source_pointer,
                    "source_contract_id": source_contract_id,
                    "source_availability_cut_id": _i_sha256_source_cut(
                        target_artifact_id,
                        semantic_class,
                        source_artifact_id,
                        source_contract_id,
                    ),
                    "instance_selector_id": key[2],
                    "cardinality_rule_id": "exactly-one-classification-per-expanded-pointer-instance",
                    "preimage_encoding": (
                        "registry-row-declared-ascii-or-lowercase-hex"
                        if external
                        else source_contract["canonical_profile_id"]
                    ),
                    "domain_separator": source_contract["domain_separator"],
                    "zero_policy_id": policy,
                    "conditional_binding_rule_id": binding_rule,
                    "externally_retained_preimage_required": external,
                    "preimage_registry_entry_required": external,
                    "validator_implemented": _i_pointer_validator_implemented(
                        target_artifact_id, target_pointer, source_artifact_id
                    ),
                    "definition_only": True,
                },
            )
        )
    if len(result) != 315 or len(result) != len(seen):
        raise RuntimeError("independent pointer classification count differs")
    return tuple(result)


_I_GATE_PASS_CONDITIONS = {
    1: (("freeze-receipt", "/to_state", "FROZEN"),),
    2: (("source-manifest", "/body_sha256", "$valid-body"),),
    3: (("dependency-lock-match-receipt", "/match_verified", True),),
    4: (("production-runtime-receipt", "/body_sha256", "$valid-body"),),
    5: (("external-seed-source-receipt", "$external_authority_verified", True),),
    6: (("seed-capsule-sequence-crosscheck-receipt", "/sequence_equal", True),),
    7: (("production-schedule", "/request_count", 32_768),),
    8: (
        (
            "capacity-receipt",
            "/destination_and_auxiliary_reservation_no_double_count_verified",
            True,
        ),
    ),
    9: (("durability-receipt", "/directory_fsync_verified", True),),
    10: (("production-shard-map-receipt", "/shard_count", 32),),
    11: (
        (
            "production-runner-supervisor-qualification-receipt",
            "/all_cases_passed",
            True,
        ),
    ),
    12: (
        (
            "closed-refusal-failure-classifier-qualification-receipt",
            "/all_closed_arms_reachable",
            True,
        ),
        (
            "closed-refusal-failure-classifier-qualification-receipt",
            "/unknown_codes_rejected",
            True,
        ),
    ),
    13: (
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "/repetition_blind_recomputation_verified",
            True,
        ),
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "/all_cases_passed",
            True,
        ),
    ),
    14: (
        (
            "independent-554-estimate-interval-decision-path-qualification-receipt",
            "/repetition_blind_recomputation_verified",
            True,
        ),
        (
            "independent-554-estimate-interval-decision-path-qualification-receipt",
            "/all_554_estimands_supported",
            True,
        ),
        (
            "independent-554-estimate-interval-decision-path-qualification-receipt",
            "/all_cases_passed",
            True,
        ),
    ),
    15: (("power-review-signoff", "/decision", "APPROVE"),),
    16: (
        ("independent-signoff-set", "/all_required_roles_present", True),
        ("independent-signoff-set", "/all_decisions_approve", True),
        (
            "independent-signoff-set",
            "/all_signatures_mathematically_valid_under_declared_keys",
            True,
        ),
        ("independent-signoff-set", "$external_reviewer_authority_verified", True),
    ),
    17: (("launch-authorization", "$external_launch_authority_verified", True),),
}


def _i_predicate(
    predicate_id: str,
    artifact_ids: Tuple[str, ...],
    operation_id: str,
    pointers: Tuple[str, ...],
    operand: object,
    child_predicate_ids: Tuple[str, ...] = (),
) -> dict:
    return _i_record(
        "predicate",
        {
            "schema_version": CP65_TEST28_SCHEMA_VERSION,
            "predicate_id": predicate_id,
            "applies_to_artifact_ids": artifact_ids,
            "input_json_pointers": pointers,
            "operation_id": operation_id,
            "operand_json_ascii": _plain_json_bytes(operand).decode("ascii"),
            "child_predicate_ids": child_predicate_ids,
            "evaluation_order": pointers,
            "failure_code": "cp65-predicate-failed:" + predicate_id,
            "validator_implemented": operation_id in _I_PREDICATE_OPERATION_IDS,
            "definition_only": True,
        },
    )


def _i_build_predicates(field_rules: Tuple[dict, ...]) -> Tuple[dict, ...]:
    result = []
    by_artifact, cross_by_artifact = {}, {}
    for rule in field_rules:
        predicate_id = "field:" + rule["rule_id"]
        by_artifact.setdefault(rule["artifact_id"], []).append(predicate_id)
        result.append(
            _i_predicate(
                predicate_id,
                (rule["artifact_id"],),
                "field-rule-satisfied",
                (rule["json_pointer"],),
                {"rule_id": rule["rule_id"]},
            )
        )
    for (
        predicate_id,
        artifact_ids,
        operation_id,
        pointers,
        operand,
    ) in _I_CROSS_PREDICATE_SPECS:
        wrapper_id = "constraint:" + predicate_id
        for artifact_id in artifact_ids:
            cross_by_artifact.setdefault(artifact_id, []).append(wrapper_id)
        if predicate_id == "cross:preauthorization-record-is-one-allowed-arm":
            children = (
                "field:preauthorization-outcome:/outcome_arm",
                "field:preauthorization-outcome:/terminal_state",
            )
        elif operation_id == "logical-not":
            children = ("cross:preauthorization-record-is-one-allowed-arm",)
        else:
            children = ()
        result.append(
            _i_predicate(
                predicate_id,
                artifact_ids,
                operation_id,
                pointers,
                operand,
                children,
            )
        )
        result.append(
            _i_predicate(
                wrapper_id,
                artifact_ids,
                "cross-constraint-satisfied",
                pointers,
                {"constraint_id": predicate_id},
                (predicate_id,),
            )
        )
    cross_by_artifact.setdefault("auxiliary-metadata-reservation", []).append(
        "always-reserved-with-auxiliary-partition"
    )
    result.append(
        _i_predicate(
            "auxiliary-exclusive-root-charge-disjoint-conservation",
            ("auxiliary-metadata-reservation",),
            "cross-constraint-satisfied",
            (
                "/exclusive_root_charge_baseline_bytes",
                "/exclusive_root_charge_current_bytes",
                "/unique_nonhold_artifact_allocated_bytes",
                "/hold_allocated_bytes",
                "/disjoint_allocation_and_directory_charge_bytes",
                "/physical_reservation_sum_bytes",
            ),
            {"constraint_id": "auxiliary-exclusive-root-charge-disjoint-conservation"},
        )
    )
    cross_by_artifact.setdefault("launch-authorization", []).append(
        "mutual-exclusion:launch-or-rejected-authorization"
    )
    cross_by_artifact.setdefault("auxiliary-metadata-reservation", []).append(
        "auxiliary-exclusive-root-charge-disjoint-conservation"
    )
    result.append(
        _i_predicate(
            "source-manifest-role-partitions-disjoint",
            ("source-manifest",),
            "cross-constraint-satisfied",
            ("/entries",),
            {"constraint_id": "source-manifest-role-partitions-disjoint"},
        )
    )
    cross_by_artifact.setdefault("source-manifest", []).append(
        "source-manifest-role-partitions-disjoint"
    )
    result.append(
        _i_predicate(
            "independent-signoff-reviewed-summary-raw-binding",
            ("independent-signoff-set", "preflight-gate-summary"),
            "cross-constraint-satisfied",
            (
                "/ordered_signoffs/*/reviewed_artifact_sha256s",
                "preflight-gate-summary:$raw_sha256",
            ),
            {"constraint_id": "independent-signoff-reviewed-summary-raw-binding"},
        )
    )
    cross_by_artifact.setdefault("independent-signoff-set", []).append(
        "independent-signoff-reviewed-summary-raw-binding"
    )
    for (
        artifact_id,
        path,
        _scope,
        _media,
        _keys,
        _nested,
        _domain,
        _old,
    ) in _I_ARTIFACT_DECLARATIONS:
        result.append(
            _i_predicate(
                "presence:" + artifact_id,
                (artifact_id,),
                "relative-path-template-match",
                ("$relative_path",),
                {"path_template": path},
            )
        )
        result.append(
            _i_predicate(
                "record:" + artifact_id,
                (artifact_id,),
                "logical-and",
                (),
                {},
                ("presence:" + artifact_id,)
                + tuple(by_artifact.get(artifact_id, ()))
                + tuple(cross_by_artifact.get(artifact_id, ())),
            )
        )
    result.append(
        _i_predicate(
            "always-reserved-with-auxiliary-partition",
            (),
            "exact-equal",
            ("$policy-reserved",),
            {"expected": True, "actual": True},
        )
    )
    result.append(
        _i_predicate(
            "co-presence:launch-and-rejected-authorization",
            ("launch-authorization", "rejected-launch-authorization-candidate"),
            "logical-and",
            (),
            {},
            (
                "presence:launch-authorization",
                "presence:rejected-launch-authorization-candidate",
            ),
        )
    )
    result.append(
        _i_predicate(
            "mutual-exclusion:launch-or-rejected-authorization",
            ("launch-authorization", "rejected-launch-authorization-candidate"),
            "logical-not",
            (),
            {},
            ("co-presence:launch-and-rejected-authorization",),
        )
    )
    evidence_aliases = {
        "independent-full-32768-recomputation-receipt": "independent-full-32768-recomputation-qualification-receipt",
        "independent-554-estimate-interval-decision-path-receipt": "independent-554-estimate-interval-decision-path-qualification-receipt",
    }
    for gate_ordinal, (gate_id, evidence_node) in enumerate(
        zip(_I_GATE_IDS, _I_GATE_EVIDENCE_NODES), 1
    ):
        evidence_artifact = evidence_aliases.get(evidence_node, evidence_node)
        pass_children = []
        for condition_ordinal, (condition_artifact, pointer, expected) in enumerate(
            _I_GATE_PASS_CONDITIONS[gate_ordinal], 1
        ):
            condition_id = "gate-pass-condition:%02d:%02d" % (
                gate_ordinal,
                condition_ordinal,
            )
            pass_children.append(condition_id)
            result.append(
                _i_predicate(
                    condition_id,
                    (condition_artifact,),
                    "exact-equal",
                    (pointer,),
                    {"expected": expected},
                )
            )
        gate_pass_id = "gate-pass:" + gate_id
        result.append(
            _i_predicate(
                gate_pass_id,
                (evidence_artifact,),
                "logical-and",
                (),
                {},
                tuple(pass_children),
            )
        )
        required = (
            _I_AUTHORIZATION_REQUIRED_ARTIFACTS
            if gate_ordinal == 17
            else _I_GATE_REQUIRED_ARTIFACT_IDS[gate_ordinal - 1]
        )
        result.append(
            _i_predicate(
                "gate:" + gate_id,
                (evidence_artifact,),
                "logical-and",
                (),
                {"required_gate_state": "PASS"},
                tuple("record:" + item for item in required) + (gate_pass_id,),
            )
        )
    if len(result) != 1_031:
        raise RuntimeError("independent predicate count differs")
    return tuple(result)


def _i_build_gates() -> Tuple[dict, ...]:
    aliases = {
        "independent-554-estimate-interval-decision-path-receipt": "independent-554-estimate-interval-decision-path-qualification-receipt",
        "independent-full-32768-recomputation-receipt": "independent-full-32768-recomputation-qualification-receipt",
    }
    result = []
    for ordinal, (gate_id, node_id) in enumerate(
        zip(_I_GATE_IDS, _I_GATE_EVIDENCE_NODES), 1
    ):
        artifact_id = aliases.get(node_id, node_id)
        required = (
            _I_AUTHORIZATION_REQUIRED_ARTIFACTS
            if ordinal == 17
            else _I_GATE_REQUIRED_ARTIFACT_IDS[ordinal - 1]
        )
        clauses = tuple("record:" + item for item in required) + (
            "gate-pass:" + gate_id,
        )
        result.append(
            _i_record(
                "gate",
                {
                    "schema_version": CP65_TEST28_SCHEMA_VERSION,
                    "gate_ordinal": ordinal,
                    "gate_id": gate_id,
                    "evidence_node_id": node_id,
                    "evidence_artifact_id": artifact_id,
                    "required_artifact_ids": required,
                    "predicate_id": "gate:" + gate_id,
                    "predicate_clause_ids": clauses,
                    "preflight_summary_covered": ordinal <= 15,
                    "requires_external_provenance": True,
                    "requires_independent_authority": ordinal in (5, 15, 16, 17),
                    "evidence_present": False,
                    "gate_state": "MISSING",
                    "definition_only": True,
                },
            )
        )
    return tuple(result)


_I_EXTRA_ARTIFACT_EDGES = (
    ("frozen-protocol", "source-manifest", "/entries/*/sha256"),
    ("frozen-machine-manifest", "source-manifest", "/entries/*/sha256"),
    ("dependency-lock", "source-manifest", "/entries/*/sha256"),
    ("frozen-source-fixture-materialization", "source-manifest", "/entries/*/sha256"),
    (
        "production-schema-preimage-validator-bundle",
        "source-manifest",
        "/entries/*/sha256",
    ),
    ("launch-authority-public-key", "source-manifest", "/entries/*/sha256"),
    ("independent-reviewer-public-key-set", "source-manifest", "/entries/*/sha256"),
    ("seed-source-authority-public-key", "source-manifest", "/entries/*/sha256"),
    (
        "frozen-source-fixture-materialization",
        "freeze-receipt",
        "/frozen_source_fixture_materialization_sha256",
    ),
    (
        "production-schema-preimage-validator-bundle",
        "freeze-receipt",
        "/production_receipt_schema_bundle_sha256",
    ),
    (
        "launch-authority-public-key",
        "freeze-receipt",
        "/launch_authority_public_key_sha256",
    ),
    (
        "independent-reviewer-public-key-set",
        "freeze-receipt",
        "/independent_reviewer_public_key_set_sha256",
    ),
    (
        "seed-source-authority-public-key",
        "freeze-receipt",
        "/seed_source_authority_public_key_sha256",
    ),
    ("dependency-lock", "freeze-receipt", "/dependency_lock_sha256"),
    ("frozen-protocol", "power-review-signoff", "/protocol_sha256"),
    ("frozen-machine-manifest", "power-review-signoff", "/machine_manifest_sha256"),
    ("power-review-signoff", "power-threshold-receipt", "/reviewer_signoff_sha256"),
    (
        "external-digest-preimage-registry",
        "preflight-gate-summary",
        "/external_digest_preimage_registry_sha256",
    ),
    (
        "independent-reviewer-public-key-set",
        "independent-signoff-set",
        "/reviewer_public_key_set_sha256",
    ),
    (
        "external-seed-acquisition-start-receipt",
        "seed-source-authority-attestation",
        "/acquisition_start_receipt_sha256",
    ),
    (
        "external-seed-acquisition-journal",
        "seed-source-authority-attestation",
        "/acquisition_journal_sha256",
    ),
    (
        "seed-source-custody-artifact",
        "seed-source-authority-attestation",
        "/seed_source_custody_artifact_sha256",
    ),
    (
        "seed-source-authority-attestation",
        "external-seed-source-receipt",
        "/source_authority_attestation_sha256",
    ),
    ("freeze-receipt", "auxiliary-metadata-reservation", "/freeze_receipt_sha256"),
    ("production-schedule", "auxiliary-metadata-reservation", "/schedule_sha256"),
    (
        "production-schema-preimage-validator-bundle",
        "auxiliary-metadata-reservation",
        "/capacity_schema_sha256",
    ),
    ("freeze-receipt", "reservation-manifest", "/freeze_receipt_sha256"),
    ("production-schedule", "reservation-manifest", "/schedule_sha256"),
    (
        "production-schema-preimage-validator-bundle",
        "reservation-manifest",
        "/capacity_schema_sha256",
    ),
    (
        "auxiliary-metadata-reservation",
        "capacity-receipt",
        "/auxiliary_metadata_reservation_artifact_sha256",
    ),
    ("reservation-manifest", "capacity-receipt", "/reservation_manifest_sha256"),
    (
        "preauthorization-outcome",
        "launch-authorization",
        "$publication-order-and-byte-identity",
    ),
    (
        "preterminal-durable-artifact-inventory",
        "terminal-state",
        "/durable_artifact_inventory_sha256",
    ),
    ("preterminal-durable-artifact-inventory", "sha256-manifest", "/entries/*/sha256"),
    ("terminal-state", "sha256-manifest", "/terminal_state_sha256"),
    ("sha256-manifest", "committed-marker", "/sha256_manifest_sha256"),
    ("terminal-state", "committed-marker", "/terminal_state_sha256"),
)


def _i_build_artifact_preimage_graph(
    contracts: Tuple[dict, ...], pointer_contracts: Tuple[dict, ...]
) -> Tuple[tuple, tuple, tuple, tuple, tuple, tuple]:
    nodes = ["digest:" + row["contract_id"] for row in contracts]
    edges, pointers = [], []
    state_source_contract_ids = {}
    edge_source_contract_overrides = {}
    edge_digest_kind_overrides = {}

    def add_node(node: str) -> None:
        if node not in nodes:
            nodes.append(node)

    def add_edge(
        source: str,
        target: str,
        pointer: str,
        source_contract_id: str = "",
        digest_kind: str = "",
    ) -> None:
        add_node(source)
        add_node(target)
        edge = (source, target)
        if edge in edges:
            if pointers[edges.index(edge)] == pointer:
                return
            raise RuntimeError("duplicate independent preimage edge")
        edges.append(edge)
        pointers.append(pointer)
        if source_contract_id:
            edge_source_contract_overrides[edge] = source_contract_id
        if digest_kind:
            edge_digest_kind_overrides[edge] = digest_kind

    by_id = {row["contract_id"]: row for row in contracts}
    contract_ids = set(by_id)
    for contract in contracts:
        target = "digest:" + contract["contract_id"]
        for component_id in contract["ordered_component_ids"]:
            if component_id not in contract_ids:
                raise RuntimeError("independent digest component is unresolved")
            add_edge(
                "digest:" + component_id,
                target,
                (
                    "$classified-source-contract"
                    if contract["contract_id"].startswith("classified-binding:")
                    else by_id[component_id]["digest_field_pointer"]
                ),
            )
    for pointer_contract in pointer_contracts:
        artifact_id = pointer_contract["target_artifact_id"]
        target = (
            "state:rejected-launch-authorization-candidate:validated-envelope"
            if artifact_id == "rejected-launch-authorization-candidate"
            else _i_body_node(artifact_id)
        )
        source = "digest:" + pointer_contract["source_contract_id"]
        intrinsic = (
            artifact_id,
            pointer_contract["target_json_pointer"],
        ) in _I_INTRINSIC_SHA256_KEYS
        if intrinsic:
            if source != target:
                add_edge(
                    source,
                    target,
                    pointer_contract["target_json_pointer"],
                    pointer_contract["source_contract_id"],
                    pointer_contract["digest_kind"],
                )
            continue
        binding_state = "binding:" + pointer_contract["classification_id"]
        state_source_contract_ids[binding_state] = pointer_contract[
            "source_contract_id"
        ]
        add_edge(
            source,
            binding_state,
            "$selected-source-digest",
            pointer_contract["source_contract_id"],
            pointer_contract["digest_kind"],
        )
        add_edge(
            binding_state,
            target,
            pointer_contract["target_json_pointer"],
            pointer_contract["source_contract_id"],
            "digest-value-equality",
        )
    for source_id, target_id, pointer in _I_EXTRA_ARTIFACT_EDGES:
        identity_contract = {
            (
                "launch-authority-public-key",
                "/authority_identity_sha256",
            ): "launch-authority-public-key:identity",
            (
                "seed-source-authority-public-key",
                "/source_authority_identity_sha256",
            ): "seed-source-authority-public-key:identity",
            (
                "independent-reviewer-public-key-set",
                "/reviewer_public_key_identity_sha256",
            ): "independent-reviewer-public-key-set:key-identity",
            (
                "independent-reviewer-public-key-set",
                "/ordered_signoffs/*/reviewer_public_key_identity_sha256",
            ): "independent-reviewer-public-key-set:key-identity",
        }.get((source_id, pointer))
        source = (
            "digest:" + identity_contract
            if identity_contract
            else _i_raw_node(source_id)
        )
        if (
            target_id == "launch-authorization"
            and pointer == "$publication-order-and-byte-identity"
        ):
            prepared_digest = (
                "digest:launch-authorization-candidate:prepared-raw-sha256"
            )
            prepared_state = "state:launch-authorization-candidate:prepared-raw"
            authorization_winner = "state:preauthorization-outcome:authorization-winner"
            terminal_winner = "state:preauthorization-outcome:terminal-winner"
            add_edge(prepared_digest, prepared_state, "$prepared_exact_bytes")
            add_edge(
                prepared_state,
                _i_body_node("preauthorization-outcome"),
                "/prepared_launch_authorization_sha256",
            )
            add_edge(
                _i_raw_node("preauthorization-outcome"),
                authorization_winner,
                "$authorization-arm",
            )
            add_edge(
                _i_raw_node("preauthorization-outcome"),
                terminal_winner,
                "$terminal-arm",
            )
            add_edge(
                authorization_winner,
                _i_raw_node("launch-authorization"),
                "$rename-no-replace-identical-bytes",
            )
            add_edge(
                prepared_state,
                _i_raw_node("launch-authorization"),
                "$authorization-candidate-byte-identity",
            )
            add_edge(
                terminal_winner,
                _i_raw_node("rejected-launch-authorization-candidate"),
                "$rename-no-replace-identical-bytes",
            )
            add_edge(
                prepared_state,
                _i_raw_node("rejected-launch-authorization-candidate"),
                "$rejected-candidate-byte-identity",
            )
            continue
        if target_id == "source-manifest" and pointer == "/entries/*/sha256":
            target = "digest:source-manifest:selected-entry-raw-sha256"
        elif target_id == "launch-authorization":
            target = "digest:launch-authorization:unsigned-preimage"
        else:
            target = _i_body_node(target_id)
        add_edge(source, target, pointer)
    journal_states = (
        "state:auxiliary-transition-journal:head0",
        "state:auxiliary-transition-journal:preinventory-prefix",
        "state:auxiliary-transition-journal:after-inventory",
        "state:auxiliary-transition-journal:after-terminal",
        "state:auxiliary-transition-journal:final",
    )
    for state in journal_states:
        add_node(state)
    add_edge(
        _i_raw_node("auxiliary-metadata-reservation"),
        journal_states[0],
        "$header.auxiliary_reservation_raw_sha256",
    )
    add_edge(
        journal_states[0], journal_states[1], "$valid_prefix.previous_entry_sha256"
    )
    add_edge(
        journal_states[1],
        _i_body_node("preterminal-durable-artifact-inventory"),
        "/auxiliary_transition_journal_prefix_head_sha256",
    )
    add_edge(
        _i_raw_node("preterminal-durable-artifact-inventory"),
        journal_states[2],
        "$transition-code-3.target_raw_sha256",
    )
    add_edge(
        journal_states[2],
        _i_body_node("terminal-state"),
        "/auxiliary_transition_journal_after_inventory_head_sha256",
    )
    add_edge(
        _i_raw_node("terminal-state"),
        journal_states[3],
        "$transition-code-4.target_raw_sha256",
    )
    add_edge(
        journal_states[3],
        _i_body_node("sha256-manifest"),
        "/auxiliary_transition_journal_after_terminal_head_sha256",
    )
    add_edge(
        _i_raw_node("sha256-manifest"),
        journal_states[4],
        "$transition-code-5.target_raw_sha256",
    )
    add_edge(
        journal_states[4],
        _i_body_node("committed-marker"),
        "/auxiliary_reservation_transition_journal_final_head_sha256",
    )
    add_edge(
        _i_raw_node("auxiliary-reservation-transition-journal"),
        _i_body_node("committed-marker"),
        "/auxiliary_reservation_transition_journal_sha256",
    )
    inventory_target = (
        "digest:preterminal-durable-artifact-inventory:selected-entry-raw-sha256"
    )
    excluded = {
        "auxiliary-reservation-transition-journal",
        "preterminal-durable-artifact-inventory",
        "terminal-state",
        "sha256-manifest",
        "committed-marker",
    }
    for artifact_id, *_rest in _I_ARTIFACT_DECLARATIONS:
        if artifact_id not in excluded:
            edge = (_i_raw_node(artifact_id), inventory_target)
            if edge not in edges:
                add_edge(edge[0], edge[1], "/entries/*/sha256")
    indegree = {node: 0 for node in nodes}
    children = {node: [] for node in nodes}
    for source, target in edges:
        indegree[target] += 1
        children[source].append(target)
    ready = [node for node in nodes if indegree[node] == 0]
    order = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for child in children[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if len(order) != len(nodes):
        raise RuntimeError("independent artifact-preimage graph is cyclic")
    source_contract_ids, digest_kinds = [], []
    state_contracts = {
        "state:launch-authorization-candidate:prepared-raw": "launch-authorization-candidate:prepared-raw-sha256",
        "state:preauthorization-outcome:authorization-winner": "preauthorization-outcome:raw-sha256",
        "state:preauthorization-outcome:terminal-winner": "preauthorization-outcome:raw-sha256",
        "state:auxiliary-transition-journal:head0": "auxiliary-reservation-transition-journal:head0",
        "state:auxiliary-transition-journal:preinventory-prefix": "auxiliary-reservation-transition-journal:preinventory-prefix",
        "state:auxiliary-transition-journal:after-inventory": "auxiliary-reservation-transition-journal:after-inventory",
        "state:auxiliary-transition-journal:after-terminal": "auxiliary-reservation-transition-journal:after-terminal",
        "state:auxiliary-transition-journal:final": "auxiliary-reservation-transition-journal:final-head",
    }
    for edge in edges:
        source = edge[0]
        if edge in edge_source_contract_overrides:
            contract_id = edge_source_contract_overrides[edge]
        elif source.startswith("digest:"):
            contract_id = source[len("digest:") :]
        elif source in state_contracts:
            contract_id = state_contracts[source]
        elif source in state_source_contract_ids:
            contract_id = state_source_contract_ids[source]
        else:
            raise RuntimeError("independent graph source lacks a digest contract")
        if contract_id not in by_id:
            raise RuntimeError("independent graph source contract is unresolved")
        source_contract_ids.append(contract_id)
        contract = by_id[contract_id]
        if edge in edge_digest_kind_overrides:
            kind = edge_digest_kind_overrides[edge]
        elif source.startswith(("state:", "binding:")):
            kind = "byte-identity"
        elif "unsigned-preimage" in contract_id:
            kind = "signature-preimage-sha256"
        elif "identity" in contract_id:
            kind = "key-identity-domain-sha256"
        elif "raw-signature" in contract_id:
            kind = "plain-raw-bytes-sha256"
        elif "row-digest" in contract_id or contract_id.endswith(":entry"):
            kind = "record-row-domain-sha256"
        elif "ordered" in contract_id or contract_id.endswith(":head"):
            kind = "ordered-domain-sha256"
        elif contract["domain_separator"]:
            kind = "body-domain-sha256"
        else:
            kind = "plain-raw-file-sha256"
        digest_kinds.append(kind)
    graph = (
        tuple(nodes),
        tuple(edges),
        tuple(pointers),
        tuple(source_contract_ids),
        tuple(digest_kinds),
        tuple(order),
    )
    if len(nodes) != 456 or len(edges) != 708:
        raise RuntimeError("independent artifact-preimage graph size differs")
    return graph


def _i_build_auxiliary_proof(bounds: Tuple[dict, ...]) -> dict:
    grouped = {}
    by_artifact = {row["artifact_id"]: row for row in bounds}
    for row in bounds:
        grouped.setdefault(row["physical_slot_group_id"], []).append(row)
    auxiliary_groups = tuple(
        rows
        for rows in grouped.values()
        if rows[0]["destination_reservation_excluded"]
        and not rows[0]["artifact_id"].startswith("__")
    )
    logical_maximum = sum(
        max(
            row["maximum_instance_count"] * row["maximum_logical_bytes_per_instance"]
            for row in rows
        )
        for rows in auxiliary_groups
    )
    slot_maximum = sum(
        max(row["maximum_total_reserved_bytes"] for row in rows)
        for rows in auxiliary_groups
    )
    policy = by_artifact["__allocation_and_directory_charge_policy_slot__"][
        "maximum_total_reserved_bytes"
    ]
    maximum = slot_maximum + policy
    if (logical_maximum, slot_maximum, maximum) != (
        21_845_344_321,
        22_213_099_520,
        23_286_841_344,
    ):
        raise RuntimeError("independent auxiliary arithmetic differs")
    return _i_record(
        "proof",
        {
            "schema_version": CP65_TEST28_SCHEMA_VERSION,
            "proof_id": "cp65-exclusive-auxiliary-reservation-size-proof-v1",
            "cp64_capacity_schema_record_sha256": "968108bda050687408fe989186aff3137560b827d1c83622f685a597d208ecfe",
            "auxiliary_reservation_floor_bytes": 34_359_738_368,
            "artifact_bound_ids": tuple(row["bound_id"] for row in bounds),
            "covered_complete_roster_artifact_ids": tuple(
                row[0] for row in _I_ARTIFACT_DECLARATIONS
            ),
            "destination_artifact_ids": _I_DESTINATION_IDS,
            "maximum_auxiliary_artifact_logical_bytes": logical_maximum,
            "maximum_auxiliary_artifact_slot_reserved_bytes": slot_maximum,
            "allocation_and_directory_charge_policy_slot_bytes": policy,
            "maximum_auxiliary_policy_required_bytes": maximum,
            "exclusive_reserved_policy_headroom_bytes": 11_072_897_024,
            "maximum_dynamic_hold_bytes": 34_359_738_368,
            "arithmetic_formula": "mutually-exclusive-launch-alias-counted-once+54-global+2-conditional+4*32-shard-auxiliary-slots+1073741824=23286841344",
            "every_auxiliary_artifact_covered_exactly_once": True,
            "simultaneous_branch_upper_bound_conservative": True,
            "integer_arithmetic_verified": True,
            "fits_exclusive_auxiliary_reservation": True,
            "definition_only": True,
            "production_reservation_observed": False,
        },
    )


def _i_signature_contract() -> dict:
    return _i_record(
        "signature",
        {
            "schema_version": CP65_TEST28_SCHEMA_VERSION,
            "scheme_id": "rsa-pss-sha256-3072-e65537-salt32-v1",
            "public_key_artifact_id": "launch-authority-public-key",
            "authorization_artifact_id": "launch-authorization",
            "hash_algorithm_id": "sha256",
            "mgf_algorithm_id": "mgf1-sha256",
            "modulus_bytes": 384,
            "modulus_bit_length": 3_072,
            "public_exponent": 65_537,
            "signature_bytes": 384,
            "signature_hex_characters": 768,
            "salt_bytes": 32,
            "em_bits": 3_071,
            "em_bytes": 384,
            "trailer_field": 188,
            "unused_high_bits": 1,
            "signing_preimage_domain": "cp65-test28-launch-authorization-signature-preimage-v1\0",
            "signing_preimage_zeroed_field_pointers": (
                "/authority_signature_hex",
                "/authority_signature_sha256",
                "/body_sha256",
            ),
            "signature_digest_formula": "SHA256(raw-384-byte-signature)",
            "public_key_identity_formula": "SHA256(cp65-test28-launch-authority-public-key-identity-v1\\0+canonical(authority_scheme_id,authority_id,modulus_hex,public_exponent))",
            "strict_pss_verification_steps": (
                "parse-exact-3072-bit-odd-modulus-and-e65537",
                "require-gcd-modulus-exponent-one-and-signature-less-than-modulus",
                "perform-one-modular-exponentiation",
                "require-emBits3071-emLen384-trailer-bc-unused-high-bit-zero",
                "mgf1-sha256-exactly-eleven-blocks",
                "require-318-zero-ps-bytes-01-delimiter-and-32-byte-salt",
                "constant-time-compare-recomputed-sha256-hash",
                "check-valid-from-less-equal-issued-less-than-expires-less-equal-valid-until",
            ),
            "signer_implemented": False,
            "key_generation_implemented": False,
            "public_key_present": False,
            "trust_root_bound": False,
            "signature_instance_present": False,
            "verifier_implemented": True,
            "authority_verified": False,
            "launch_authorized": False,
            "definition_only": True,
        },
    )


def _i_predecessor_custody() -> dict:
    return _i_record(
        "predecessor",
        {
            "schema_version": CP65_TEST28_SCHEMA_VERSION,
            "cp64_schema_version": "cp64-test28-production-custody-preflight-v1",
            "cp64_source_relative_path": "src/heterodiff/evaluation/mixed_initializer_test28_production_custody_preflight.py",
            "cp64_source_sha256": "d35cbacb84e3348ae10549e053a0bb1572569583cdd03e66119353af4148bec2",
            "cp64_source_bytes": 109_716,
            "cp64_source_lines": 2_409,
            "cp64_test_relative_path": "tests/unit/test_mixed_initializer_test28_production_custody_preflight.py",
            "cp64_test_sha256": "5e2d3a4ee4803556812983a01506e1f0b146c62ac2e2017c98914474a799fca4",
            "cp64_test_bytes": 125_001,
            "cp64_test_lines": 2_944,
            "v15_protocol_relative_path": "research/preregistrations/cp50_test28_mixed_initializer_v15.md",
            "v15_protocol_sha256": "79074586ce77d5a57ad49193098b0ba7c8e07e7446c002b42277572e10193df8",
            "v15_protocol_bytes": 125_063,
            "v15_protocol_lines": 2_265,
            "v15_manifest_relative_path": "research/fixtures/cp50_test28_mixed_initializer_v15.json",
            "v15_manifest_sha256": "e9cd67841d12325e06cdd645e79d40737937b36d6052275ffb9e5185d8978376",
            "v15_manifest_bytes": 2_038_189,
            "v15_manifest_lines": 39_046,
            "cp64_bundle_record_sha256": "32f7f0c62019d8ee906e6f74300f6c33fbe55984f69cfe4fe1061ffb92463f39",
            "cp64_bundle_public_sha256": "caecd8630def94f7ac6da721422e3d9d71c26c351e753369abf17b224a90de83",
            "cp64_bundle_canonical_json_sha256": "31c1ff133f9dc6c3f9a5810359bd313f5fe5f46cb5e2bd6801b8dac0e241ae23",
            "cp64_bundle_canonical_json_bytes": 77_595,
            "cp64_no_execution_gate_contract_record_sha256": "7ceb4f12ce712e7123509eb6380e134876855bb91e90c64a951f7e1bcbcb2633",
            "cp64_false_schema_definition_flags": (
                "all_required_production_receipt_keysets_predeclared",
                "complete_receipt_type_range_size_and_domain_schemas_frozen",
                "complete_auxiliary_artifact_size_schema_frozen",
                "bounded_auxiliary_artifact_size_proof_present",
                "generic_prestart_terminal_record_schema_frozen",
                "all_required_production_receipt_digest_preimages_frozen",
                "authorization_signature_preimage_and_verifier_frozen",
                "requirement_schemas_frozen",
            ),
            "cp64_gate_count": 17,
            "cp64_evidence_present_count": 0,
            "cp64_ledger_total_count": 19,
            "cp64_ledger_satisfied_count": 15,
            "cp64_ledger_missing_count": 4,
            "v15_protocol_state": "DRAFT",
            "v15_lifecycle_current_state": "DRAFT_PRE_FREEZE",
            "v15_complete_production_roster_frozen": False,
            "formal_test_28_status": "OPEN",
            "formal_test_28_closed": False,
            "cp65_source_hashes_external_binding_required": True,
            "predecessor_only": True,
        },
    )


def _i_semantic_sha256(
    field_rules: Tuple[dict, ...],
    artifact_schemas: Tuple[dict, ...],
    transients: Tuple[dict, ...],
    digest_contracts: Tuple[dict, ...],
    pointer_contracts: Tuple[dict, ...],
    predicates: Tuple[dict, ...],
    gates: Tuple[dict, ...],
    bounds: Tuple[dict, ...],
    proof: dict,
    signature: dict,
    graph: tuple,
) -> str:
    payload = {
        "artifact_preimage_dependency_edges": graph[1],
        "artifact_preimage_dependency_node_ids": graph[0],
        "artifact_preimage_edge_target_pointers": graph[2],
        "artifact_preimage_source_contract_ids": graph[3],
        "artifact_preimage_digest_kinds": graph[4],
        "artifact_preimage_topological_order": graph[5],
        "artifact_schemas": tuple(_i_record_semantics(row) for row in artifact_schemas),
        "transient_path_contracts": tuple(
            _i_record_semantics(row) for row in transients
        ),
        "authorization_signature_contract": _i_record_semantics(signature),
        "auxiliary_artifact_bounds": tuple(_i_record_semantics(row) for row in bounds),
        "auxiliary_size_proof": _i_record_semantics(proof),
        "canonical_profile_id": _CANONICAL_PROFILE_ID,
        "conditional_paths": _I_CONDITIONAL_PATHS,
        "digest_dag_edges": _I_GATE_DAG_EDGES,
        "digest_dag_nodes": _I_GATE_DAG_NODES,
        "digest_preimage_contracts": tuple(
            _i_record_semantics(row) for row in digest_contracts
        ),
        "sha256_pointer_contracts": tuple(
            _i_record_semantics(row) for row in pointer_contracts
        ),
        "field_rules": tuple(_i_record_semantics(row) for row in field_rules),
        "gate_requirements": tuple(_i_record_semantics(row) for row in gates),
        "global_paths": _I_GLOBAL_PATHS,
        "path_precision": (312, 128, 1, 183, 1, 181, 310, 622, True, True),
        "per_shard_path_templates": _I_PER_SHARD_PATHS,
        "predicate_contracts": tuple(_i_record_semantics(row) for row in predicates),
        "schema_version": CP65_TEST28_SCHEMA_VERSION,
    }
    return hashlib.sha256(
        b"cp65-test28-production-schema-semantic-v1\0" + _plain_json_bytes(payload)
    ).hexdigest()


_I_OUTER_DEFINITION_VALUES = {
    "schema_version": CP65_TEST28_SCHEMA_VERSION,
    "scope": CP65_TEST28_SCOPE,
    "canonical_profile_id": _CANONICAL_PROFILE_ID,
    "sha256_pointer_contracts_cover_every_sha256_field_rule": True,
    "registry_required_targets_all_durable_by_gate15": True,
    "later_artifacts_have_no_registry_dependency": True,
    "all_schema_references_resolve_exactly_once": True,
    "no_orphan_or_unused_rule_predicate_digest_or_artifact_ids": True,
    "all_referenced_rules_have_executable_validator_semantics": True,
    "expanded_final_path_count": 312,
    "reserved_destination_partial_path_count": 128,
    "prepared_authorization_partial_path_count": 1,
    "auxiliary_reserved_partial_or_existing_final_slot_count": 183,
    "auxiliary_reservation_hold_path_count": 1,
    "ordinary_auxiliary_partial_candidate_path_count": 181,
    "expanded_final_and_transient_path_count": 622,
    "generic_writer_partial_paths_are_state_aliases": True,
    "expanded_final_and_transient_paths_collision_free": True,
    "candidate_shard_count": 32,
    "evidence_present_count": 0,
    "digest_dag_is_gate_evidence_only": True,
    "artifact_preimage_dag_acyclic": True,
    "artifact_preimage_dag_complete": True,
    "artifact_body_domain_separators_unique": True,
    "artifact_kind_partitions_disjoint_and_exhaustive": True,
    "schema_completeness_claim_scope": (
        "supplied-receipt-envelope-instance-canonical-fields-digests-and-pure-"
        "gate-predicates-only;excludes-lifecycle-occurrence-branch-presence-"
        "provenance-trust-evidence-and-execution-output-semantics"
    ),
    "all_required_production_receipt_keysets_predeclared": True,
    "complete_receipt_type_range_size_and_domain_schemas_frozen": True,
    "complete_auxiliary_artifact_size_schema_frozen": True,
    "bounded_auxiliary_artifact_size_proof_present": True,
    "generic_prestart_terminal_record_schema_frozen": True,
    "all_required_production_receipt_digest_preimages_frozen": True,
    "complete_production_digest_instance_validation_interface_frozen": False,
    "authorization_signature_preimage_and_verifier_frozen": True,
    "requirement_schemas_frozen": True,
    "complete_final_path_template_roster_frozen": True,
    "complete_production_roster_frozen": False,
    "artifact_occurrence_and_branch_schema_frozen": False,
    "production_receipt_schema_frozen": False,
    "production_execution_and_output_schema_frozen": False,
    "production_schema_frozen": False,
    "source_receipt_binds_capsule_body": False,
    "capacity_receipt_binds_shard_map": False,
    "external_production_receipts_observed": False,
    "external_seed_values_present": False,
    "source_authority_verified": False,
    "production_runtime_observed": False,
    "capacity_observed": False,
    "durability_observed": False,
    "candidate_shard_policy_selected": False,
    "production_shard_map_instantiated": False,
    "runner_supervisor_qualified": False,
    "closed_classifier_qualified": False,
    "power_thresholds_frozen": False,
    "freeze_receipt_present": False,
    "independent_signoffs_present": False,
    "launch_authorization_present": False,
    "started": False,
    "production_requests_materialized": False,
    "production_campaign_exposed": False,
    "production_execution_authorized": False,
    "production_execution_observed": False,
    "estimates_computed": False,
    "intervals_computed": False,
    "decision_made": False,
    "runner_and_recomputation_blocker_closed": False,
    "unconditional_operational_predictions_blocker_closed": False,
    "power_and_thresholds_blocker_closed": False,
    "confirmatory_custody_blocker_closed": False,
    "confirmatory_evidence": False,
    "manuscript_claim": False,
    "formal_test_28_status": "OPEN",
    "formal_test_28_closed": False,
    "ledger_prerequisite_id": "whole_seed_production_schema_preimage_and_validator_definition",
    "ledger_total_count": 20,
    "ledger_satisfied_count": 16,
    "ledger_missing_count": 4,
    "zero_argument_builder": True,
    "stdlib_only_import": True,
    "project_modules_imported": False,
    "host_filesystem_probed": False,
    "clock_read": False,
    "rng_used": False,
    "network_used": False,
    "subprocess_api_exposed": False,
    "filesystem_path_api_exposed": False,
    "definition_only": True,
}

_I_AUTHORITATIVE_BUNDLE_CANONICAL_BYTES = 2_488_135
_I_AUTHORITATIVE_BUNDLE_CANONICAL_SHA256 = (
    "fd755453f7359f8db7c1dbbeea63748fd74551707ff8f5fd7e5d80a6982aa576"
)
_I_SCHEMA_SEMANTIC_SHA256 = (
    "8855d84a573344723bc6c4c32036b7aeb878d6c66a04d5423d5f591ed40316c0"
)


def _i_catalog_parts() -> dict:
    bounds = _i_build_bounds()
    field_rules = _i_build_field_rules(bounds)
    artifacts = _i_build_artifact_schemas(field_rules)
    transients = _i_build_transients(bounds)
    digests = _i_build_digest_contracts(field_rules)
    pointers = _i_build_pointer_contracts(field_rules, digests)
    predicates = _i_build_predicates(field_rules)
    gates = _i_build_gates()
    proof = _i_build_auxiliary_proof(bounds)
    signature = _i_signature_contract()
    graph = _i_build_artifact_preimage_graph(digests, pointers)
    semantic_sha256 = _i_semantic_sha256(
        field_rules,
        artifacts,
        transients,
        digests,
        pointers,
        predicates,
        gates,
        bounds,
        proof,
        signature,
        graph,
    )
    if semantic_sha256 != _I_SCHEMA_SEMANTIC_SHA256:
        raise RuntimeError("independent schema semantic reconstruction differs")
    return {
        "predecessor": _i_predecessor_custody(),
        "field_rules": field_rules,
        "artifacts": artifacts,
        "transients": transients,
        "digests": digests,
        "pointers": pointers,
        "predicates": predicates,
        "gates": gates,
        "bounds": bounds,
        "proof": proof,
        "signature": signature,
        "graph": graph,
        "semantic_sha256": semantic_sha256,
    }


def _independent_schema_semantic_sha256() -> str:
    """Return the digest derived from independently restated catalog semantics."""

    return cast(str, _i_catalog_parts()["semantic_sha256"])


def _i_authoritative_bundle_record() -> dict:
    """Assemble the tuple-valued record used for independent canonicalization."""

    parts = _i_catalog_parts()
    artifacts = cast(Tuple[dict, ...], parts["artifacts"])
    transients = cast(Tuple[dict, ...], parts["transients"])
    digests = cast(Tuple[dict, ...], parts["digests"])
    pointers = cast(Tuple[dict, ...], parts["pointers"])
    predicates = cast(Tuple[dict, ...], parts["predicates"])
    gates = cast(Tuple[dict, ...], parts["gates"])
    bounds = cast(Tuple[dict, ...], parts["bounds"])
    graph = cast(tuple, parts["graph"])
    receipt_ids = tuple(
        row["artifact_id"]
        for row in artifacts
        if row["artifact_id"] not in _I_REFERENCED_OUTPUT_IDS
        and row["artifact_id"] not in _I_FROZEN_OR_BINARY_CUSTODY_IDS
    )
    if (
        len(receipt_ids),
        len(_I_REFERENCED_OUTPUT_IDS),
        len(_I_FROZEN_OR_BINARY_CUSTODY_IDS),
    ) != (41, 15, 8):
        raise RuntimeError("independent artifact partitions differ")
    values = dict(_I_OUTER_DEFINITION_VALUES)
    values.update(
        {
            "predecessor_custody": parts["predecessor"],
            "field_rules": parts["field_rules"],
            "artifact_schemas": artifacts,
            "transient_path_contracts": transients,
            "digest_preimage_contracts": digests,
            "sha256_pointer_contracts": pointers,
            "predicate_contracts": predicates,
            "gate_requirements": gates,
            "auxiliary_artifact_bounds": bounds,
            "auxiliary_size_proof": parts["proof"],
            "authorization_signature_contract": parts["signature"],
            "schema_semantic_sha256": parts["semantic_sha256"],
            "sha256_pointer_contract_count": len(pointers),
            "global_path_count": len(_I_GLOBAL_PATHS),
            "per_shard_path_template_count": len(_I_PER_SHARD_PATHS),
            "conditional_path_count": len(_I_CONDITIONAL_PATHS),
            "expanded_transient_path_count": len(transients),
            "gate_count": len(gates),
            "digest_dag_node_count": len(_I_GATE_DAG_NODES),
            "digest_dag_edge_count": len(_I_GATE_DAG_EDGES),
            "digest_dag_node_ids": _I_GATE_DAG_NODES,
            "digest_dag_edges": _I_GATE_DAG_EDGES,
            "digest_dag_edge_target_pointers": _I_GATE_DAG_EDGE_TARGET_POINTERS,
            "digest_dag_edge_source_contract_ids": _I_GATE_DAG_EDGE_SOURCE_CONTRACT_IDS,
            "digest_dag_edge_digest_kinds": _I_GATE_DAG_EDGE_DIGEST_KINDS,
            "artifact_preimage_dependency_node_ids": graph[0],
            "artifact_preimage_dependency_edges": graph[1],
            "artifact_preimage_edge_target_pointers": graph[2],
            "artifact_preimage_edge_source_contract_ids": graph[3],
            "artifact_preimage_edge_digest_kinds": graph[4],
            "artifact_preimage_topological_order": graph[5],
            "artifact_preimage_node_count": len(graph[0]),
            "artifact_preimage_edge_count": len(graph[1]),
            "receipt_envelope_artifact_ids": receipt_ids,
            "referenced_execution_output_artifact_ids": _I_REFERENCED_OUTPUT_IDS,
            "frozen_or_binary_custody_artifact_ids": _I_FROZEN_OR_BINARY_CUSTODY_IDS,
            "receipt_envelope_schema_count": len(receipt_ids),
            "referenced_execution_output_schema_count": len(_I_REFERENCED_OUTPUT_IDS),
            "frozen_or_binary_custody_schema_count": len(
                _I_FROZEN_OR_BINARY_CUSTODY_IDS
            ),
        }
    )
    return _i_record("bundle", values)


def _independent_authoritative_bundle_primitive() -> dict:
    """Return a fresh JSON-native full authoritative-shaped catalog tree."""

    return cast(dict, _plain_json_value(_i_authoritative_bundle_record()))


def _independent_authoritative_bundle_canonical_bytes() -> bytes:
    """Generate and pin-check the full independent authoritative catalog bytes."""

    payload = _plain_json_bytes(_i_authoritative_bundle_record())
    if (
        len(payload) != _I_AUTHORITATIVE_BUNDLE_CANONICAL_BYTES
        or hashlib.sha256(payload).hexdigest()
        != _I_AUTHORITATIVE_BUNDLE_CANONICAL_SHA256
    ):
        raise RuntimeError("independent authoritative bundle reconstruction differs")
    return payload


def _mgf1_sha256(seed: bytes, output_length: int) -> bytes:
    if type(seed) is not bytes or type(output_length) is not int:
        raise TypeError("independent MGF1 inputs have the wrong exact type")
    if not 0 <= output_length <= 351:
        raise ValueError("independent MGF1 output is outside the profile")
    result = bytearray()
    for counter in range(11):
        if len(result) >= output_length:
            break
        result.extend(hashlib.sha256(seed + counter.to_bytes(4, "big")).digest())
    return bytes(result[:output_length])


def _verify_rsa_pss_sha256_3072(
    message: bytes, modulus: bytes, signature: bytes
) -> bool:
    """Independently verify the fixed profile; never sign or generate a key."""

    if type(message) is not bytes or type(modulus) is not bytes:
        raise TypeError("independent RSA-PSS inputs must be exact bytes")
    if type(signature) is not bytes:
        raise TypeError("independent RSA-PSS signature must be exact bytes")
    if len(modulus) != 384 or len(signature) != 384:
        return False
    modulus_integer = int.from_bytes(modulus, "big")
    if (
        modulus_integer.bit_length() != 3_072
        or modulus_integer % 2 == 0
        or math.gcd(modulus_integer, 65_537) != 1
    ):
        return False
    signature_integer = int.from_bytes(signature, "big")
    if signature_integer >= modulus_integer:
        return False
    encoded = pow(signature_integer, 65_537, modulus_integer).to_bytes(384, "big")
    if encoded[-1] != 0xBC:
        return False
    masked_db = encoded[:351]
    encoded_hash = encoded[351:383]
    if masked_db[0] & 0x80:
        return False
    mask = _mgf1_sha256(encoded_hash, 351)
    data_block = bytearray(left ^ right for left, right in zip(masked_db, mask))
    data_block[0] &= 0x7F
    if data_block[:318] != b"\0" * 318 or data_block[318] != 0x01:
        return False
    salt = bytes(data_block[319:351])
    message_hash = hashlib.sha256(message).digest()
    expected_hash = hashlib.sha256(b"\0" * 8 + message_hash + salt).digest()
    return hmac.compare_digest(encoded_hash, expected_hash)


def _validate_public_record(record: object) -> Tuple[_SealedRecord, bytes]:
    if type(record) not in _RECORD_DOMAINS:
        raise TypeError("unsupported independent CP65 record type")
    sealed = cast(_SealedRecord, record)
    with _ISSUED_RECORD_LOCK:
        snapshot = _ISSUED_RECORD_SNAPSHOTS.get(sealed)
        if snapshot is None:
            raise TypeError("independent CP65 record was not module-created")
        current = _canonical_bytes(sealed, require_issued=True)
    if current != snapshot:
        raise ValueError("independent CP65 issued record was mutated")
    names = tuple(item.name for item in fields(type(sealed)))
    provisional = object.__new__(type(sealed))
    for name in names:
        object.__setattr__(
            provisional,
            name,
            _ZERO_SHA256 if name == "record_sha256" else getattr(sealed, name),
        )
    expected = hashlib.sha256(
        _RECORD_DOMAINS[type(sealed)]
        + b"\0"
        + _canonical_bytes(provisional, require_issued=False)
    ).hexdigest()
    if sealed.record_sha256 != expected:
        raise ValueError("independent CP65 record digest differs")
    return sealed, snapshot


def cp65_independent_validator_bundle() -> CP65IndependentProductionSchemaPreimageValidatorBundleV1:
    """Return the independently reconstructed definition-only bundle."""

    full = _i_authoritative_bundle_record()
    values = {
        name: full[name]
        for name in (
            "schema_version",
            "scope",
            "canonical_profile_id",
            "schema_semantic_sha256",
            "sha256_pointer_contract_count",
            "sha256_pointer_contracts_cover_every_sha256_field_rule",
            "registry_required_targets_all_durable_by_gate15",
            "later_artifacts_have_no_registry_dependency",
            "all_schema_references_resolve_exactly_once",
            "no_orphan_or_unused_rule_predicate_digest_or_artifact_ids",
            "all_referenced_rules_have_executable_validator_semantics",
            "global_path_count",
            "per_shard_path_template_count",
            "conditional_path_count",
            "expanded_final_path_count",
            "reserved_destination_partial_path_count",
            "prepared_authorization_partial_path_count",
            "auxiliary_reserved_partial_or_existing_final_slot_count",
            "auxiliary_reservation_hold_path_count",
            "ordinary_auxiliary_partial_candidate_path_count",
            "expanded_transient_path_count",
            "expanded_final_and_transient_path_count",
            "generic_writer_partial_paths_are_state_aliases",
            "expanded_final_and_transient_paths_collision_free",
            "complete_final_path_template_roster_frozen",
            "complete_production_roster_frozen",
            "gate_count",
            "evidence_present_count",
            "digest_dag_node_count",
            "digest_dag_edge_count",
            "digest_dag_node_ids",
            "digest_dag_edges",
            "digest_dag_edge_target_pointers",
            "digest_dag_edge_source_contract_ids",
            "digest_dag_edge_digest_kinds",
            "digest_dag_is_gate_evidence_only",
            "artifact_preimage_dependency_node_ids",
            "artifact_preimage_dependency_edges",
            "artifact_preimage_edge_target_pointers",
            "artifact_preimage_edge_source_contract_ids",
            "artifact_preimage_edge_digest_kinds",
            "artifact_preimage_topological_order",
            "artifact_preimage_node_count",
            "artifact_preimage_edge_count",
            "artifact_preimage_dag_acyclic",
            "artifact_preimage_dag_complete",
            "artifact_body_domain_separators_unique",
            "receipt_envelope_artifact_ids",
            "referenced_execution_output_artifact_ids",
            "frozen_or_binary_custody_artifact_ids",
            "receipt_envelope_schema_count",
            "referenced_execution_output_schema_count",
            "frozen_or_binary_custody_schema_count",
            "artifact_kind_partitions_disjoint_and_exhaustive",
            "schema_completeness_claim_scope",
            "all_required_production_receipt_keysets_predeclared",
            "complete_receipt_type_range_size_and_domain_schemas_frozen",
            "complete_auxiliary_artifact_size_schema_frozen",
            "bounded_auxiliary_artifact_size_proof_present",
            "generic_prestart_terminal_record_schema_frozen",
            "all_required_production_receipt_digest_preimages_frozen",
            "complete_production_digest_instance_validation_interface_frozen",
            "authorization_signature_preimage_and_verifier_frozen",
            "requirement_schemas_frozen",
            "artifact_occurrence_and_branch_schema_frozen",
            "production_receipt_schema_frozen",
            "production_execution_and_output_schema_frozen",
            "production_schema_frozen",
            "external_production_receipts_observed",
            "filesystem_path_api_exposed",
            "definition_only",
        )
    }
    values.update(
        {
            "artifact_ids": tuple(
                row["artifact_id"] for row in full["artifact_schemas"]
            ),
            "transient_path_ids": tuple(
                row["transient_path_id"] for row in full["transient_path_contracts"]
            ),
            "field_rule_ids": tuple(row["rule_id"] for row in full["field_rules"]),
            "digest_contract_ids": tuple(
                row["contract_id"] for row in full["digest_preimage_contracts"]
            ),
            "sha256_pointer_classification_ids": tuple(
                row["classification_id"] for row in full["sha256_pointer_contracts"]
            ),
            "predicate_ids": tuple(
                row["predicate_id"] for row in full["predicate_contracts"]
            ),
            "gate_ids": tuple(row["gate_id"] for row in full["gate_requirements"]),
            "auxiliary_bound_ids": tuple(
                row["bound_id"] for row in full["auxiliary_artifact_bounds"]
            ),
            "authoritative_module_imported": False,
            "project_modules_imported": False,
            "authority_verified": False,
            "production_evidence_accepted": False,
            "launch_authorized": False,
            "execution_permitted": False,
        }
    )
    return cast(
        CP65IndependentProductionSchemaPreimageValidatorBundleV1,
        _record(CP65IndependentProductionSchemaPreimageValidatorBundleV1, values),
    )


def _require_sha256(value: object, name: str, *, nonzero: bool = False) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(name + " must be exact lowercase SHA256 hex")
    if nonzero and value == _ZERO_SHA256:
        raise ValueError(name + " must be nonzero")
    return value


def _require_utc(value: object, name: str) -> str:
    if type(value) is not str or _UTC_RE.fullmatch(value) is None:
        raise ValueError(name + " must be exact UTC microsecond text")
    year = int(value[0:4])
    month = int(value[5:7])
    day = int(value[8:10])
    hour = int(value[11:13])
    minute = int(value[14:16])
    second = int(value[17:19])
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    month_days = (0, 31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if (
        year == 0
        or not 1 <= month <= 12
        or not 1 <= day <= month_days[month]
        or not 0 <= hour <= 23
        or not 0 <= minute <= 59
        or not 0 <= second <= 59
    ):
        raise ValueError(name + " calendar value differs")
    return value


def _parse_canonical_threshold_rational(value: str, name: str) -> Tuple[int, int]:
    match = re.fullmatch(r"(-?(?:0|[1-9][0-9]*))/([1-9][0-9]*)", value)
    if match is None or value.startswith("-0"):
        raise ValueError(name + " must be a canonical rational threshold")
    numerator_text, denominator_text = match.groups()
    if len(numerator_text.lstrip("-")) > 39 or len(denominator_text) > 39:
        raise ValueError(name + " rational integer is outside its lexical bound")
    numerator = int(numerator_text)
    denominator = int(denominator_text)
    if not -(2**127) + 1 <= numerator <= 2**127 - 1:
        raise ValueError(name + " numerator is outside signed-127 bounds")
    if not 1 <= denominator <= 2**127 - 1:
        raise ValueError(name + " denominator is outside positive-127 bounds")
    if math.gcd(abs(numerator), denominator) != 1:
        raise ValueError(name + " rational is not in lowest terms")
    if numerator == 0 and denominator != 1:
        raise ValueError(name + " zero rational must be 0/1")
    return numerator, denominator


def _validation_string_domain(
    artifact_id: str, pointer: str, key: str
) -> Tuple[str, ...]:
    domain = _I_STRING_DOMAINS.get((artifact_id, key), ())
    if artifact_id == "production-schedule":
        if pointer == "/requests/*/schema_version":
            return (_I_CP63_SCHEMA_VERSION,)
        if pointer == "/requests/*/row_key":
            return tuple(row[1] for row in _I_ROW_INVENTORY)
        if pointer == "/requests/*/fixture_id":
            return tuple(dict.fromkeys(row[2] for row in _I_ROW_INVENTORY))
        if pointer == "/requests/*/strategy":
            return tuple(dict.fromkeys(row[3] for row in _I_ROW_INVENTORY))
    if artifact_id == "closed-refusal-failure-classifier-qualification-receipt":
        if pointer == "/closed_refusal_codes/*":
            return _I_CLOSED_REFUSAL_CODES
        if pointer == "/closed_failure_codes/*":
            return _I_CLOSED_FAILURE_CODES
    if artifact_id == "preflight-gate-summary":
        if pointer == "/covered_gate_ids/*":
            return _I_GATE_IDS[:15]
        if pointer == "/covered_gate_states/*":
            return ("PASS",)
        if pointer == "/covered_evidence_node_ids/*":
            return _I_GATE_EVIDENCE_NODES[:15]
    if pointer == "/required_reviewer_roles/*" and artifact_id in (
        "independent-signoff-set",
        "independent-reviewer-public-key-set",
    ):
        return _I_REQUIRED_REVIEWER_ROLES
    if artifact_id == "source-manifest" and pointer == "/entries/*/role":
        return ("production-runner-source", "independent-recomputation-source")
    if artifact_id == "power-threshold-receipt":
        if key == "gate_id":
            return _I_POWER_PRIMARY_SLOT_IDS
        if key == "estimand_id":
            return _I_CP61_ESTIMAND_IDS
        if key == "threshold_encoding":
            return (
                "canonical-rational-signed-numerator-positive-denominator-lowest-terms-v1",
            )
    if artifact_id == "auxiliary-metadata-reservation" and pointer.startswith(
        "/artifact_entries/*/"
    ):
        column = {
            "artifact_id": 0,
            "primary_publication_arm_id": 5,
            "alternate_publication_arm_id": 6,
        }.get(key)
        if column is not None:
            return tuple(
                dict.fromkeys(
                    str(row[column]) for row in _i_auxiliary_slots(_i_build_bounds())
                )
            )
    return domain


def _validate_scalar_field(
    artifact_id: str, pointer: str, key: str, value: object
) -> None:
    exact_integer = _I_INTEGER_EXACT.get((artifact_id, key))
    if exact_integer is not None:
        if type(value) is not int or value != exact_integer:
            raise ValueError(pointer + " differs from its exact integer")
        return
    integer_interval = _I_INTEGER_INTERVALS.get((artifact_id, pointer))
    if integer_interval is not None:
        if (
            type(value) is not int
            or not integer_interval[0] <= value <= integer_interval[1]
        ):
            raise ValueError(pointer + " differs from its exact integer interval")
        return
    if "/terminal_counts/" in pointer or key in ("lines", "budget"):
        if type(value) is not int or not 0 <= value <= 2**63 - 1:
            raise ValueError(pointer + " must be a bounded nonnegative integer")
        return
    kind = _i_field_kind(key)
    if kind == "boolean":
        if type(value) is not bool:
            raise ValueError(pointer + " must be an exact boolean")
        if (
            key
            in (
                "production_runner_rng_or_child_started_before_receipt",
                "topup_redraw_reselection_permitted",
            )
            and value is not False
        ):
            raise ValueError(pointer + " must be the exact false sentinel")
        return
    if kind == "integer":
        if type(value) is not int or not 0 <= value <= 2**64 - 1:
            raise ValueError(pointer + " must be a bounded nonnegative integer")
        return
    if kind == "object":
        if type(value) is not dict:
            raise ValueError(pointer + " must be an exact object")
        return
    if type(value) is not str:
        raise ValueError(pointer + " must be an exact string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(pointer + " must be ASCII") from exc
    maximum = 1_048_576
    if artifact_id == "power-threshold-receipt" and key in (
        "selected_count_justification_ascii",
        "justification_ascii",
    ):
        maximum = 16_384
    elif artifact_id == "external-digest-preimage-registry" and key == "preimage_ascii":
        maximum = 131_072
    if len(encoded) > maximum:
        raise ValueError(pointer + " string is too long")
    if (
        artifact_id == "auxiliary-metadata-reservation"
        and key
        in (
            "alternate_final_relative_path",
            "alternate_publication_arm_id",
            "partial_relative_path",
            "file_fsync_completed_at_utc",
            "directory_fsync_completed_at_utc",
        )
        and value == ""
    ):
        return
    if (
        artifact_id == "external-digest-preimage-registry"
        and key
        in (
            "domain_separator",
            "preimage_ascii",
        )
        and value == ""
    ):
        return
    domain = _validation_string_domain(artifact_id, pointer, key)
    if key == "schema":
        domain = (
            _I_CP63_SCHEMA_VERSION
            if artifact_id == "seed-capsule-body"
            else _I_ARTIFACT_BY_ID[artifact_id][6],
        )
    if key == "schema_version" and artifact_id == "production-schedule":
        domain = (_I_CP63_SCHEMA_VERSION,)
    if key == "terminal_state" and artifact_id in (
        "preauthorization-outcome",
        "postauthorization-outcome",
    ):
        domain = ("", "INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE")
    if domain and value not in domain:
        raise ValueError(pointer + " differs from its closed string domain")
    pattern = _i_pattern_id(key)
    if pattern == "lowercase-sha256-hex":
        _require_sha256(value, pointer)
    elif pattern == "lowercase-hex-16" and _HEX16_RE.fullmatch(value) is None:
        raise ValueError(pointer + " must be 16 lowercase hex characters")
    elif pattern == "lowercase-hex-768" and _HEX768_RE.fullmatch(value) is None:
        raise ValueError(pointer + " must be 768 lowercase hex characters")
    elif pattern == "utc-microseconds-z":
        _require_utc(value, pointer)
    elif pattern == "posix-relative-path":
        _require_relative_path(value, pointer)
    elif (
        pattern == "shard-id-0001-through-0032"
        and _SHARD_ID_RE.fullmatch(value) is None
    ):
        raise ValueError(pointer + " must be a canonical shard id")
    elif pattern == "attempt-id-v1" and _ATTEMPT_ID_RE.fullmatch(value) is None:
        raise ValueError(pointer + " must be a canonical attempt id")
    elif pattern == "opaque-method-session-authority-id-v1" and (
        _OPAQUE_METHOD_SESSION_AUTHORITY_ID_RE.fullmatch(value) is None
    ):
        raise ValueError(pointer + " must be a canonical opaque identifier")
    elif pattern == "canonical-rational-threshold-v1":
        _parse_canonical_threshold_rational(value, pointer)
    elif (
        pattern == "bounded-nonempty-ascii"
        and not encoded
        and not (
            key == "terminal_state"
            and artifact_id in ("preauthorization-outcome", "postauthorization-outcome")
        )
    ):
        raise ValueError(pointer + " must be nonempty")


def _validate_primitive_array(artifact_id: str, key: str, value: object) -> list:
    if type(value) is not list:
        raise ValueError("/%s must be an exact array" % key)
    exact_length = _I_ARRAY_LENGTH_EXACT.get((artifact_id, key))
    if exact_length is not None and len(value) != exact_length:
        raise ValueError("/%s array length differs" % key)
    if len(value) > 32_768:
        raise ValueError("/%s array exceeds the frozen bound" % key)
    if key == "seed_ordinals":
        if value != list(range(1, 2_049)):
            raise ValueError("seed ordinals differ from 1..2048")
    elif key in ("ordered_seed_values", "ordered_partial_seed_values"):
        if any(
            type(item) is not str or _HEX16_RE.fullmatch(item) is None for item in value
        ):
            raise ValueError("seed value array is not exact uint64 hex")
    elif key in (
        "ordered_slot_threshold_row_sha256s",
        "ordered_entry_sha256s",
        "ordered_public_key_identity_sha256s",
        "ordered_request_record_sha256s",
        "per_file_reservation_manifest_entry_sha256s",
        "ordered_evidence_receipt_sha256s",
        "reviewed_artifact_sha256s",
    ):
        for item in value:
            _require_sha256(item, "/%s/*" % key)
    elif key == "closed_refusal_codes" and tuple(value) != _I_CLOSED_REFUSAL_CODES:
        raise ValueError("closed refusal code tuple differs")
    elif key == "closed_failure_codes" and tuple(value) != _I_CLOSED_FAILURE_CODES:
        raise ValueError("closed failure code tuple differs")
    elif key == "covered_gate_ids" and tuple(value) != _I_GATE_IDS[:15]:
        raise ValueError("preflight covered gate order differs")
    elif key == "covered_gate_states" and tuple(value) != ("PASS",) * 15:
        raise ValueError("preflight covered gate states differ")
    elif (
        key == "covered_evidence_node_ids"
        and tuple(value) != _I_GATE_EVIDENCE_NODES[:15]
    ):
        raise ValueError("preflight evidence node order differs")
    elif (
        key == "required_reviewer_roles" and tuple(value) != _I_REQUIRED_REVIEWER_ROLES
    ):
        raise ValueError("required reviewer roles differ")
    return value


def _validate_nested_rows(
    artifact_id: str,
    document: dict,
    nested: Tuple[Tuple[str, Tuple[str, ...]], ...],
) -> None:
    for container_key, exact_keys in nested:
        container = document[container_key]
        if container_key == "terminal_counts":
            if (
                type(container) is not dict
                or set(container) != set(exact_keys)
                or len(container) != len(exact_keys)
            ):
                raise ValueError("terminal_counts field set differs")
            for key in exact_keys:
                _validate_scalar_field(
                    artifact_id, "/terminal_counts/" + key, key, container[key]
                )
            continue
        if type(container) is not list:
            raise ValueError("/%s must be an exact array" % container_key)
        exact_length = _I_ARRAY_LENGTH_EXACT.get((artifact_id, container_key))
        if exact_length is not None and len(container) != exact_length:
            raise ValueError("/%s array length differs" % container_key)
        for index, row in enumerate(container):
            if (
                type(row) is not dict
                or set(row) != set(exact_keys)
                or len(row) != len(exact_keys)
            ):
                raise ValueError("/%s/%d field set differs" % (container_key, index))
            for key in exact_keys:
                if _i_field_kind(key) == "array":
                    _validate_primitive_array(artifact_id, key, row[key])
                else:
                    _validate_scalar_field(
                        artifact_id,
                        "/%s/%d/%s" % (container_key, index, key),
                        key,
                        row[key],
                    )
            digest_info = _I_NESTED_DIGESTS.get((artifact_id, container_key))
            if digest_info is not None:
                digest_key, domain = digest_info
                supplied = _require_sha256(row[digest_key], digest_key)
                zeroed = dict(row)
                zeroed[digest_key] = _ZERO_SHA256
                expected = hashlib.sha256(
                    domain.encode("ascii") + b"\0" + _plain_json_bytes(zeroed)
                ).hexdigest()
                if supplied != expected:
                    raise ValueError(
                        "/%s/%d nested digest differs" % (container_key, index)
                    )


def _validate_body_digest(artifact_id: str, document: dict) -> str:
    domain = _I_ARTIFACT_BY_ID[artifact_id][6]
    supplied = _require_sha256(document["body_sha256"], "/body_sha256")
    zeroed = dict(document)
    zeroed["body_sha256"] = _ZERO_SHA256
    expected = hashlib.sha256(
        domain.encode("ascii") + b"\0" + _plain_json_bytes(zeroed)
    ).hexdigest()
    if supplied != expected:
        raise ValueError("artifact body digest differs")
    return supplied


def _independent_recomputation_source_submanifest_sha256(document: object) -> str:
    declaration = _I_ARTIFACT_BY_ID["source-manifest"]
    exact_keys = declaration[4]
    nested_keys = declaration[5][0][1]
    if type(document) is not dict or set(document) != set(exact_keys):
        raise ValueError("source manifest keyset differs")
    entries = document.get("entries")
    entry_count = document.get("entry_count")
    if (
        type(entries) is not list
        or type(entry_count) is not int
        or entry_count != len(entries)
    ):
        raise ValueError("source manifest entry count differs")
    selected = []
    production_paths = set()
    independent_paths = set()
    previous_path = ""
    for ordinal, entry in enumerate(entries, 1):
        if type(entry) is not dict or set(entry) != set(nested_keys):
            raise ValueError("source manifest entry keyset differs")
        if entry["ordinal"] != ordinal:
            raise ValueError("source manifest entry ordinals differ")
        role = entry["role"]
        path = entry["relative_path"]
        if role not in ("production-runner-source", "independent-recomputation-source"):
            raise ValueError("source manifest role differs")
        if (
            type(path) is not str
            or not path
            or (previous_path and path <= previous_path)
        ):
            raise ValueError("source manifest path order differs")
        previous_path = path
        if role == "independent-recomputation-source":
            selected.append(entry)
            independent_paths.add(path)
        else:
            production_paths.add(path)
    if not selected or independent_paths.intersection(production_paths):
        raise ValueError("source manifest role partition differs")
    return hashlib.sha256(
        b"cp65-test28-independent-recomputation-source-submanifest-v1\0"
        + _plain_json_bytes({"entry_count": len(selected), "entries": selected})
    ).hexdigest()


def _reviewer_key_identity(key: dict) -> str:
    identity = {
        "reviewer_role": key["reviewer_role"],
        "reviewer_identity_sha256": key["reviewer_identity_sha256"],
        "signature_scheme_id": key["signature_scheme_id"],
        "authority_id": key["authority_id"],
        "modulus_hex": key["modulus_hex"],
        "public_exponent": key["public_exponent"],
    }
    return hashlib.sha256(
        b"cp65-test28-independent-reviewer-public-key-identity-v1\0"
        + _plain_json_bytes(identity)
    ).hexdigest()


def _validate_terminal_union(document: dict) -> None:
    arm = document["terminal_arm"]
    state = document["terminal_state"]
    zero_fields = ()
    nonzero_fields = ("freeze_receipt_sha256", "durable_artifact_inventory_sha256")
    if arm == "PREAUTHORIZATION":
        if document["previous_lifecycle_state"] != "FROZEN" or state not in (
            "INVALID_PROTOCOL",
            "ABORTED_INFRA",
            "INCOMPLETE",
        ):
            raise ValueError("PREAUTHORIZATION terminal discriminator differs")
        nonzero_fields += ("preauthorization_outcome_sha256",)
        zero_fields = (
            "launch_authorization_sha256",
            "postauthorization_outcome_sha256",
            "started_receipt_sha256",
        )
    elif arm == "POSTAUTHORIZATION_PRESTART":
        if document["previous_lifecycle_state"] != "FROZEN" or state not in (
            "INVALID_PROTOCOL",
            "ABORTED_INFRA",
            "INCOMPLETE",
        ):
            raise ValueError("POSTAUTHORIZATION_PRESTART discriminator differs")
        nonzero_fields += (
            "preauthorization_outcome_sha256",
            "launch_authorization_sha256",
            "postauthorization_outcome_sha256",
        )
        zero_fields = ("started_receipt_sha256",)
    elif arm == "STARTED":
        if document["previous_lifecycle_state"] != "STARTED" or state not in (
            "PASS",
            "FAIL",
            "INVALID_PROTOCOL",
            "ABORTED_INFRA",
            "INCOMPLETE",
        ):
            raise ValueError("STARTED terminal discriminator differs")
        nonzero_fields += (
            "preauthorization_outcome_sha256",
            "launch_authorization_sha256",
            "postauthorization_outcome_sha256",
            "started_receipt_sha256",
        )
    else:
        raise ValueError("terminal arm differs")
    for key in nonzero_fields:
        _require_sha256(document[key], key, nonzero=True)
    for key in zero_fields:
        if document[key] != _ZERO_SHA256:
            raise ValueError(key + " must use the zero digest sentinel")
    reasons = {
        "PASS": "completed-as-preregistered",
        "FAIL": "primary-or-structural-failure",
        "INVALID_PROTOCOL": "frozen-input-or-protocol-invalid",
        "ABORTED_INFRA": "infrastructure-abort",
        "INCOMPLETE": "attempt-incomplete",
    }
    if document["reason_code"] != reasons[state]:
        raise ValueError("terminal reason code differs")


def _validate_preterminal_inventory_intrinsic(document: dict) -> None:
    entries = document["entries"]
    if (
        document["entry_count"] != len(entries)
        or not 1 <= len(entries) <= _MAX_TERMINAL_PUBLICATION_ENTRIES
    ):
        raise ValueError("preterminal inventory entry count differs")
    if [row["ordinal"] for row in entries] != list(range(1, len(entries) + 1)):
        raise ValueError("preterminal inventory ordinals differ")
    paths = [row["path"] for row in entries]
    if paths != sorted(set(paths)):
        raise ValueError("preterminal inventory paths are not sorted and unique")
    forbidden = {
        "preterminal_durable_artifact_inventory.json",
        "terminal_state.json",
        "sha256_manifest.json",
        "COMMITTED.json",
        "auxiliary_reservation_transition_journal.bin",
    }
    for row in entries:
        _require_relative_path(row["path"], "preterminal inventory path")
        if row["path"] in forbidden:
            raise ValueError("preterminal inventory contains a forbidden artifact")
        zeroed = dict(row)
        zeroed["entry_sha256"] = _ZERO_SHA256
        expected = hashlib.sha256(
            b"cp65-test28-preterminal-durable-artifact-inventory-entry-v1\0"
            + _plain_json_bytes(zeroed)
        ).hexdigest()
        if row["entry_sha256"] != expected:
            raise ValueError("preterminal inventory entry digest differs")
    ordered = hashlib.sha256(
        b"cp65-test28-preterminal-durable-artifact-inventory-ordered-entries-v1\0"
        + b"".join(bytes.fromhex(row["entry_sha256"]) for row in entries)
    ).hexdigest()
    if document["ordered_entries_sha256"] != ordered:
        raise ValueError("preterminal inventory ordered digest differs")


def _validate_sha256_manifest_intrinsic(document: dict) -> None:
    entries = document["entries"]
    if (
        document["entry_count"] != len(entries)
        or not 1 <= len(entries) <= _MAX_TERMINAL_PUBLICATION_ENTRIES
    ):
        raise ValueError("SHA256 manifest entry count differs")
    paths = [row["path"] for row in entries]
    if paths != sorted(set(paths)):
        raise ValueError("SHA256 manifest paths are not sorted and unique")
    forbidden = {
        "sha256_manifest.json",
        "COMMITTED.json",
        "auxiliary_reservation_transition_journal.bin",
    }
    for row in entries:
        _require_relative_path(row["path"], "SHA256 manifest path")
        if row["path"] in forbidden:
            raise ValueError("SHA256 manifest contains a forbidden artifact")
    ordered = hashlib.sha256(
        b"cp65-test28-sha256-manifest-ordered-entries-v1\0" + _plain_json_bytes(entries)
    ).hexdigest()
    if document["ordered_entries_sha256"] != ordered:
        raise ValueError("SHA256 manifest ordered digest differs")


def _validate_receipt_specific(artifact_id: str, document: dict) -> None:
    if artifact_id == "external-digest-preimage-registry":
        entries = document["entries"]
        count = document["entry_count"]
        if type(count) is not int or not 0 <= count <= 4_096 or len(entries) != count:
            raise ValueError("external digest registry entry count differs")
        pointer_contracts = {
            row["classification_id"]: row
            for row in cast(Tuple[dict, ...], _i_catalog_parts()["pointers"])
            if row["preimage_registry_entry_required"]
        }
        encoded_total = 0
        ordered = []
        sort_keys = []
        slots = _i_auxiliary_slots(_i_build_bounds())
        for ordinal, row in enumerate(entries, 1):
            if row["ordinal"] != ordinal:
                raise ValueError("external digest registry ordinals differ")
            pointer_contract = pointer_contracts.get(row["classification_id"])
            if pointer_contract is None or (
                row["target_artifact_id"],
                row["target_json_pointer"],
            ) != (
                pointer_contract["target_artifact_id"],
                pointer_contract["target_json_pointer"],
            ):
                raise ValueError("external digest registry classification differs")
            target_id = row["target_artifact_id"]
            if (
                target_id not in _I_ARTIFACT_BY_ID
                or not _relative_path_matches_template(
                    _I_ARTIFACT_BY_ID[target_id][1], row["target_relative_path"]
                )
            ):
                raise ValueError(
                    "external digest registry target artifact/path differs"
                )
            selector_ascii = row["target_instance_selector_json_ascii"]
            if not 1 <= len(selector_ascii.encode("ascii")) <= 4_096:
                raise ValueError("external digest registry selector size differs")
            selector = _parse_canonical_json_object(
                selector_ascii.encode("ascii"), 4_096
            )
            if tuple(selector) != (
                "artifact_instance_ordinal",
                "shard_ordinal",
                "wildcard_indices",
            ):
                raise ValueError("external digest registry selector keys differ")
            instance_ordinal = selector["artifact_instance_ordinal"]
            shard_ordinal = selector["shard_ordinal"]
            wildcard_indices = selector["wildcard_indices"]
            if type(instance_ordinal) is not int or not 1 <= instance_ordinal <= 312:
                raise ValueError("registry artifact instance ordinal differs")
            if type(shard_ordinal) is not int or not (
                shard_ordinal == 0 or 1 <= shard_ordinal <= 32
            ):
                raise ValueError("registry shard ordinal differs")
            if (
                type(wildcard_indices) is not list
                or len(wildcard_indices) > 8
                or any(
                    type(index) is not int or not 0 <= index <= 32_767
                    for index in wildcard_indices
                )
            ):
                raise ValueError("registry wildcard selector differs")
            pointer = pointer_contract["target_json_pointer"]
            if len(wildcard_indices) != pointer.count("*"):
                raise ValueError("registry wildcard selector cardinality differs")
            pointer_parts = tuple(part for part in pointer.split("/") if part)
            wildcard_ordinal = 0
            for part_index, part in enumerate(pointer_parts):
                if part != "*":
                    continue
                container_key = pointer_parts[part_index - 1]
                maximum = _I_POINTER_WILDCARD_CARDINALITIES.get(
                    (pointer_contract["target_artifact_id"], container_key)
                )
                selected_index = wildcard_indices[wildcard_ordinal]
                wildcard_ordinal += 1
                if maximum is None or selected_index >= maximum:
                    raise ValueError("registry wildcard selector is out of range")
                if (
                    pointer_contract["target_artifact_id"]
                    == "auxiliary-metadata-reservation"
                    and container_key == "artifact_entries"
                    and slots[selected_index][0] == "committed-marker"
                ):
                    raise ValueError("registry selector targets a conditional zero arm")
            scope = _I_ARTIFACT_BY_ID[target_id][2]
            if scope == "per-shard":
                if shard_ordinal == 0 or instance_ordinal != shard_ordinal:
                    raise ValueError("registry shard instance selector differs")
            elif shard_ordinal != 0 or instance_ordinal != 1:
                raise ValueError("registry global instance selector differs")
            _require_sha256(
                row["target_artifact_raw_sha256"],
                "registry target raw digest",
                nonzero=True,
            )
            encoding = row["preimage_encoding"]
            preimage_ascii = row["preimage_ascii"]
            if encoding == "ascii":
                decoded = preimage_ascii.encode("ascii")
            elif encoding == "lowercase-hex":
                if (
                    len(preimage_ascii) % 2
                    or re.fullmatch(r"[0-9a-f]*", preimage_ascii) is None
                ):
                    raise ValueError("registry lowercase-hex preimage differs")
                decoded = bytes.fromhex(preimage_ascii)
            else:
                raise ValueError("registry preimage encoding differs")
            if len(decoded) != row["preimage_bytes"] or len(decoded) > 65_536:
                raise ValueError("registry decoded preimage size differs")
            encoded_total += len(preimage_ascii)
            digest_kind = row["digest_kind"]
            domain = row["domain_separator"]
            expected_kind = (
                "domain-separated-sha256"
                if pointer_contract["domain_separator"]
                else "plain-sha256"
            )
            if (
                digest_kind != expected_kind
                or domain != pointer_contract["domain_separator"]
            ):
                raise ValueError(
                    "registry digest profile differs from pointer contract"
                )
            if digest_kind == "plain-sha256":
                if domain != "":
                    raise ValueError("plain registry digest has a domain")
                expected_digest = hashlib.sha256(decoded).hexdigest()
            else:
                domain_bytes = domain.encode("ascii")
                if not 1 <= len(domain_bytes) <= 256 or not domain.endswith("\0"):
                    raise ValueError("registry digest domain differs")
                expected_digest = hashlib.sha256(domain_bytes + decoded).hexdigest()
            if row["digest_sha256"] != expected_digest:
                raise ValueError("registry supplied preimage digest differs")
            ordered.append(row["entry_sha256"])
            sort_keys.append(
                (
                    target_id,
                    row["target_relative_path"],
                    row["target_json_pointer"],
                    selector_ascii,
                    row["classification_id"],
                )
            )
        if encoded_total > 62_914_560:
            raise ValueError("registry encoded preimage aggregate exceeds its cap")
        if sort_keys != sorted(sort_keys) or len(set(sort_keys)) != len(sort_keys):
            raise ValueError("registry targets are not canonical and unique")
        if tuple(document["ordered_entry_sha256s"]) != tuple(ordered):
            raise ValueError("registry entry digest vector differs")
        expected_ordered = hashlib.sha256(
            b"cp65-test28-external-digest-preimage-registry-ordered-entries-v1\0"
            + b"".join(bytes.fromhex(item) for item in ordered)
        ).hexdigest()
        if document["ordered_entries_sha256"] != expected_ordered:
            raise ValueError("registry ordered-entry digest differs")
    elif artifact_id == "power-threshold-receipt":
        review = document["power_review_ascii"].encode("ascii")
        selected = document["selected_count_justification_ascii"].encode("ascii")
        if not review or not selected:
            raise ValueError("power-review preimage text must be nonempty")
        if (
            document["power_review_sha256"]
            != hashlib.sha256(
                b"cp65-test28-power-review-text-v1\0" + review
            ).hexdigest()
        ):
            raise ValueError("power-review text digest differs")
        if (
            document["selected_count_justification_sha256"]
            != hashlib.sha256(
                b"cp65-test28-selected-count-justification-v1\0" + selected
            ).hexdigest()
        ):
            raise ValueError("selected-count justification digest differs")
        row_digests = []
        estimand_positions = []
        estimand_index = {
            estimand_id: index for index, estimand_id in enumerate(_I_CP61_ESTIMAND_IDS)
        }
        for ordinal, row in enumerate(document["ordered_slot_thresholds"], 1):
            if (
                row["slot_ordinal"] != ordinal
                or row["gate_id"] != _I_POWER_PRIMARY_SLOT_IDS[ordinal - 1]
                or row["threshold_encoding"]
                != "canonical-rational-signed-numerator-positive-denominator-lowest-terms-v1"
                or row["design_minimum_selected_count"] != 1_040
            ):
                raise ValueError("power threshold row design identity differs")
            if row["estimand_id"] not in estimand_index:
                raise ValueError("power threshold estimand is outside CP61 inventory")
            estimand_positions.append(estimand_index[row["estimand_id"]])
            _parse_canonical_threshold_rational(
                row["threshold_value"], "threshold_value"
            )
            justification = row["justification_ascii"].encode("ascii")
            if not justification:
                raise ValueError("threshold-row justification must be nonempty")
            if (
                row["justification_sha256"]
                != hashlib.sha256(
                    b"cp65-test28-threshold-row-justification-v1\0" + justification
                ).hexdigest()
            ):
                raise ValueError("threshold-row justification digest differs")
            row_digests.append(row["row_sha256"])
        if estimand_positions != sorted(set(estimand_positions)):
            raise ValueError("power threshold estimands are not unique and ordered")
        if tuple(document["ordered_slot_threshold_row_sha256s"]) != tuple(row_digests):
            raise ValueError("power threshold row-digest vector differs")
        if (
            document["ordered_slot_thresholds_sha256"]
            != hashlib.sha256(
                b"cp65-test28-power-threshold-rows-v1\0"
                + _plain_json_bytes(row_digests)
            ).hexdigest()
        ):
            raise ValueError("ordered power-threshold digest differs")
    elif artifact_id == "seed-capsule-body":
        if document["cp61_stable_design_sha256"] != _I_CP61_STABLE_DESIGN_SHA256:
            raise ValueError("seed capsule design custody differs")
        if document["seed_count"] != 2_048:
            raise ValueError("seed capsule count differs")
        if (
            type(document["source_method_id"]) is not str
            or not 1 <= len(document["source_method_id"].encode("ascii")) <= 4_096
        ):
            raise ValueError("seed capsule source method differs")
    elif artifact_id == "external-seed-source-receipt":
        if document["seed_count"] != 2_048:
            raise ValueError("completed source receipt seed count differs")
        if document["acquisition_journal_entry_count"] != 2_048:
            raise ValueError("completed source journal count differs")
        if (
            document["acquisition_start_receipt_sha256"]
            != document["acquisition_session_sha256"]
        ):
            raise ValueError("completed source start-receipt aliases differ")
    elif artifact_id == "partial-seed-acquisition-terminal-receipt":
        count = document["acquired_seed_count"]
        if type(count) is not int or not 0 <= count <= 2_048:
            raise ValueError("partial acquisition count differs")
        if document["acquisition_journal_entry_count"] != count:
            raise ValueError("partial journal count differs")
        if document["acquisition_journal_raw_bytes"] != 163_840:
            raise ValueError("partial journal full preallocation bytes differs")
        if len(document["ordered_partial_seed_values"]) != count:
            raise ValueError("partial seed list length differs")
        if document["topup_redraw_reselection_permitted"] is not False:
            raise ValueError("partial source topup/redraw must be false")
    elif artifact_id == "production-schedule":
        requests = document["requests"]
        digests = document["ordered_request_record_sha256s"]
        if len(requests) != 32_768 or len(digests) != 32_768:
            raise ValueError("production schedule row count differs")
        request_keys = _I_ARTIFACT_BY_ID["production-schedule"][5][0][1]
        for index, row in enumerate(requests, 1):
            seed_ordinal = (index - 1) // 16 + 1
            row_ordinal = (index - 1) % 16 + 1
            inventory = _I_ROW_INVENTORY[row_ordinal - 1]
            exact = {
                "schema_version": _I_CP63_SCHEMA_VERSION,
                "seed_ordinal": seed_ordinal,
                "row_ordinal": row_ordinal,
                "logical_request_ordinal": index,
                "row_key": inventory[1],
                "fixture_id": inventory[2],
                "strategy": inventory[3],
                "budget": inventory[4],
                "seed_free_request_sha256": inventory[5],
                "runtime_lock_sha256": _I_CP63_RUNTIME_LOCK_SHA256,
            }
            if any(
                type(row[key]) is not type(expected) or row[key] != expected
                for key, expected in exact.items()
            ):
                raise ValueError("production schedule request identity differs")
            identity = {key: row[key] for key in request_keys[:12]}
            expected_instance = hashlib.sha256(
                b"cp63-test28-bound-request-v1\0" + _plain_json_bytes(identity)
            ).hexdigest()
            if row["request_instance_sha256"] != expected_instance:
                raise ValueError("production schedule request instance digest differs")
            if digests[index - 1] != row["request_row_sha256"]:
                raise ValueError("production schedule digest vector differs")
        expected_ordered = hashlib.sha256(
            b"cp65-test28-production-schedule-ordered-requests-v1\0"
            + _plain_json_bytes(digests)
        ).hexdigest()
        if document["ordered_requests_sha256"] != expected_ordered:
            raise ValueError("production schedule ordered digest differs")
    elif artifact_id == "source-manifest":
        entries = document["entries"]
        if not 1 <= len(entries) <= _MAX_SOURCE_MANIFEST_ENTRIES or document[
            "entry_count"
        ] != len(entries):
            raise ValueError("source manifest entry count differs")
        ordinals = [row["ordinal"] for row in entries]
        paths = [row["relative_path"] for row in entries]
        if ordinals != list(range(1, len(entries) + 1)) or paths != sorted(set(paths)):
            raise ValueError("source manifest entries are not ordered and unique")
        if document["total_bytes"] != sum(row["bytes"] for row in entries):
            raise ValueError("source manifest total bytes differs")
        expected = hashlib.sha256(
            b"cp65-test28-source-manifest-ordered-entries-v1\0"
            + _plain_json_bytes(entries)
        ).hexdigest()
        if document["ordered_entries_sha256"] != expected:
            raise ValueError("source manifest ordered-entry digest differs")
        _independent_recomputation_source_submanifest_sha256(document)
    elif artifact_id == "preflight-gate-summary":
        if tuple(document["covered_gate_ids"]) != _I_GATE_IDS[:15]:
            raise ValueError("preflight covered gate IDs differ")
        if tuple(document["covered_gate_states"]) != ("PASS",) * 15:
            raise ValueError("preflight covered gate states differ")
        if tuple(document["covered_evidence_node_ids"]) != _I_GATE_EVIDENCE_NODES[:15]:
            raise ValueError("preflight evidence node IDs differ")
        for digest in document["ordered_evidence_receipt_sha256s"]:
            _require_sha256(digest, "preflight evidence digest", nonzero=True)
    elif artifact_id == "closed-refusal-failure-classifier-qualification-receipt":
        pass
    elif artifact_id == "started-receipt":
        if (
            document["production_runner_rng_or_child_started_before_receipt"]
            is not False
        ):
            raise ValueError("STARTED receipt ordering boolean differs")
    elif artifact_id == "shard-receipt":
        if sum(document["terminal_counts"].values()) != document["request_count"]:
            raise ValueError("shard terminal counts do not sum to request count")
        if document["request_count"] != 1_024:
            raise ValueError("shard receipt request count differs")
    elif artifact_id == "preauthorization-outcome":
        arm = document["outcome_arm"]
        if arm not in (
            "AUTHORIZATION",
            "INVALID_PROTOCOL",
            "ABORTED_INFRA",
            "INCOMPLETE",
        ):
            raise ValueError("preauthorization outcome arm differs")
        if arm == "AUTHORIZATION":
            _require_sha256(
                document["prepared_launch_authorization_sha256"],
                "prepared authorization",
                nonzero=True,
            )
            if document["terminal_state"] != "":
                raise ValueError("authorization arm terminal state must be empty")
        elif document["terminal_state"] != arm:
            raise ValueError("preauthorization terminal arm differs")
    elif artifact_id == "postauthorization-outcome":
        arm = document["outcome_arm"]
        if arm not in ("STARTED", "INVALID_PROTOCOL", "ABORTED_INFRA", "INCOMPLETE"):
            raise ValueError("postauthorization outcome arm differs")
        _require_sha256(
            document["launch_authorization_sha256"],
            "launch authorization",
            nonzero=True,
        )
        if (arm == "STARTED" and document["terminal_state"] != "") or (
            arm != "STARTED" and document["terminal_state"] != arm
        ):
            raise ValueError("postauthorization terminal state differs")
    elif artifact_id == "terminal-state":
        _validate_terminal_union(document)
    elif artifact_id == "preterminal-durable-artifact-inventory":
        _validate_preterminal_inventory_intrinsic(document)
    elif artifact_id == "sha256-manifest":
        _validate_sha256_manifest_intrinsic(document)
    elif artifact_id == "auxiliary-metadata-reservation":
        expected_slots = _i_auxiliary_slots(_i_build_bounds())
        rows = document["artifact_entries"]
        if document["artifact_entry_count"] != 183 or len(rows) != 183:
            raise ValueError("auxiliary reservation entry count differs")
        existing_bytes = 0
        future_bytes = 0
        identities = set()
        extent_maps = set()
        for ordinal, (row, expected) in enumerate(zip(rows, expected_slots), 1):
            (
                expected_artifact,
                final_path,
                alternate_final_path,
                logical_cap,
                reserved_cap,
                primary_arm,
                alternate_arm,
            ) = expected
            if (
                row["ordinal"] != ordinal
                or row["artifact_id"] != expected_artifact
                or row["final_relative_path"] != final_path
                or row["alternate_final_relative_path"] != alternate_final_path
                or row["primary_publication_arm_id"] != primary_arm
                or row["alternate_publication_arm_id"] != alternate_arm
                or row["maximum_logical_bytes"] != logical_cap
                or not 0 <= row["reserved_bytes"] <= reserved_cap
            ):
                raise ValueError("auxiliary reservation canonical row differs")
            state = row["reservation_state"]
            if expected_artifact == "committed-marker":
                if (
                    state != "future-o-excl-covered-by-hold"
                    or row["partial_relative_path"] != ""
                    or row["device_identity_sha256"] != _ZERO_SHA256
                    or row["inode"] != 0
                    or row["extent_map_sha256"] != _ZERO_SHA256
                    or row["reserved_bytes"] != reserved_cap
                    or row["non_sparse_verified"] is not False
                    or row["exclusive_verified"] is not False
                    or row["file_fsync_completed_at_utc"] != ""
                    or row["directory_fsync_completed_at_utc"] != ""
                ):
                    raise ValueError("COMMITTED auxiliary row sentinel differs")
                continue
            is_live_journal = (
                expected_artifact == "auxiliary-reservation-transition-journal"
            )
            if state not in (
                "existing-final-in-place",
                "preallocated-partial-in-place",
                "preallocated-live-journal-in-place",
            ):
                raise ValueError("auxiliary reservation row state differs")
            if is_live_journal:
                if state != "preallocated-live-journal-in-place":
                    raise ValueError("auxiliary transition journal row state differs")
                expected_partial = final_path
            else:
                if state == "preallocated-live-journal-in-place":
                    raise ValueError("live-journal state used by another artifact")
                expected_partial = (
                    ""
                    if state == "existing-final-in-place"
                    else final_path + ".partial"
                )
            if row["partial_relative_path"] != expected_partial:
                raise ValueError("auxiliary reservation row partial path differs")
            _require_sha256(
                row["device_identity_sha256"],
                "auxiliary row device",
                nonzero=True,
            )
            _require_sha256(
                row["extent_map_sha256"],
                "auxiliary row extents",
                nonzero=True,
            )
            if row["inode"] <= 0:
                raise ValueError("auxiliary reservation row inode differs")
            if (
                row["non_sparse_verified"] is not True
                or row["exclusive_verified"] is not True
            ):
                raise ValueError("auxiliary reservation row qualification differs")
            _require_utc(row["file_fsync_completed_at_utc"], "auxiliary row file fsync")
            _require_utc(
                row["directory_fsync_completed_at_utc"],
                "auxiliary row directory fsync",
            )
            identity = (row["device_identity_sha256"], row["inode"])
            if identity in identities or row["extent_map_sha256"] in extent_maps:
                raise ValueError("auxiliary reservation inode/extent alias differs")
            identities.add(identity)
            extent_maps.add(row["extent_map_sha256"])
            if state == "existing-final-in-place":
                existing_bytes += row["reserved_bytes"]
            else:
                if row["reserved_bytes"] != reserved_cap:
                    raise ValueError("future auxiliary partial is not fully reserved")
                future_bytes += row["reserved_bytes"]
        if document["allocated_existing_final_bytes"] != existing_bytes:
            raise ValueError("auxiliary existing-final total differs")
        if document["allocated_future_partial_bytes"] != future_bytes:
            raise ValueError("auxiliary future-partial total differs")
        unique_nonhold = existing_bytes + future_bytes
        if document["unique_nonhold_artifact_allocated_bytes"] != unique_nonhold:
            raise ValueError("auxiliary unique nonhold allocation differs")
        if document["artifact_slot_reserved_bytes"] != 22_213_099_520:
            raise ValueError("auxiliary static slot total differs")
        if document["hold_relative_path"] != ".cp65_auxiliary_reservation_hold.partial":
            raise ValueError("auxiliary reservation hold path differs")
        if not 11_140_005_888 <= document["hold_allocated_bytes"] <= 34_359_738_368:
            raise ValueError("auxiliary dynamic hold is outside its bound")
        _require_sha256(
            document["hold_device_identity_sha256"],
            "auxiliary hold device identity",
            nonzero=True,
        )
        _require_sha256(
            document["hold_extent_map_sha256"],
            "auxiliary hold extent map",
            nonzero=True,
        )
        if document["hold_inode"] <= 0:
            raise ValueError("auxiliary hold inode differs")
        if (
            not 0
            <= document["disjoint_allocation_and_directory_charge_bytes"]
            <= 1_073_741_824
        ):
            raise ValueError("observed allocation/directory charge exceeds policy")
        baseline = document["exclusive_root_charge_baseline_bytes"]
        current = document["exclusive_root_charge_current_bytes"]
        if baseline < 0 or current < baseline:
            raise ValueError("exclusive-root charge measurements differ")
        disjoint_charge = document["disjoint_allocation_and_directory_charge_bytes"]
        physical = unique_nonhold + disjoint_charge + document["hold_allocated_bytes"]
        if (
            document["physical_reservation_sum_bytes"] != physical
            or physical < 34_359_738_368
        ):
            raise ValueError("auxiliary physical reservation floor differs")
        if current - baseline != physical:
            raise ValueError("exclusive-root charge conservation differs")
        measurement_preimage = {
            "schema": "cp65-test28-exclusive-root-charge-measurement-v1",
            "attempt_id": document["attempt_id"],
            "measurement_session_sha256": document["measurement_session_sha256"],
            "storage_root_identity_sha256": document["storage_root_identity_sha256"],
            "filesystem_identity_sha256": document["filesystem_identity_sha256"],
            "exclusive_root_charge_baseline_bytes": baseline,
            "exclusive_root_charge_current_bytes": current,
            "unique_nonhold_artifact_allocated_bytes": unique_nonhold,
            "hold_allocated_bytes": document["hold_allocated_bytes"],
            "disjoint_allocation_and_directory_charge_bytes": disjoint_charge,
        }
        expected_measurement = hashlib.sha256(
            b"cp65-test28-exclusive-root-charge-measurement-v1\0"
            + _plain_json_bytes(measurement_preimage)
        ).hexdigest()
        if document["exclusive_root_charge_measurement_sha256"] != expected_measurement:
            raise ValueError("exclusive-root charge measurement digest differs")
        if document["enforced_quota_bytes"] < 34_359_738_368:
            raise ValueError("auxiliary quota reservation floor differs")
        allocation_unit = document["allocation_unit_bytes"]
        if (
            allocation_unit <= 0
            or (allocation_unit & (allocation_unit - 1))
            or allocation_unit > 1_073_741_824
            or 34_359_738_368 % allocation_unit
        ):
            raise ValueError("auxiliary allocation unit differs")
        required_hold = max(0, 34_359_738_368 - unique_nonhold - disjoint_charge)
        expected_hold = (
            (required_hold + allocation_unit - 1) // allocation_unit
        ) * allocation_unit
        if document["hold_allocated_bytes"] != expected_hold:
            raise ValueError("auxiliary dynamic hold complement differs")
        hold_identity = (
            document["hold_device_identity_sha256"],
            document["hold_inode"],
        )
        if (
            hold_identity in identities
            or document["hold_extent_map_sha256"] in extent_maps
        ):
            raise ValueError("auxiliary hold aliases an artifact reservation")
        for key in (
            "exclusive_verified",
            "non_sparse_verified",
            "durable_verified",
            "same_root_verified",
        ):
            if document[key] is not True:
                raise ValueError("auxiliary reservation qualification differs: " + key)
    elif artifact_id == "independent-reviewer-public-key-set":
        if (
            document["key_count"] != 4
            or tuple(document["required_reviewer_roles"]) != _I_REQUIRED_REVIEWER_ROLES
        ):
            raise ValueError("reviewer key set role count differs")
        roles = tuple(row["reviewer_role"] for row in document["ordered_keys"])
        if roles != _I_REQUIRED_REVIEWER_ROLES:
            raise ValueError("reviewer key order differs")
        identities = []
        reviewers = set()
        for row in document["ordered_keys"]:
            identity = _reviewer_key_identity(row)
            if row["public_key_identity_sha256"] != identity:
                raise ValueError("reviewer public-key identity differs")
            if row["reviewer_identity_sha256"] in reviewers:
                raise ValueError("reviewer identities must be unique")
            reviewers.add(row["reviewer_identity_sha256"])
            if not row["valid_from_utc"] < row["valid_until_utc"]:
                raise ValueError("reviewer key validity interval differs")
            identities.append(identity)
        if tuple(document["ordered_public_key_identity_sha256s"]) != tuple(identities):
            raise ValueError("reviewer key identity vector differs")
    elif artifact_id == "independent-signoff-set":
        if (
            document["signoff_count"] != 4
            or tuple(document["required_reviewer_roles"]) != _I_REQUIRED_REVIEWER_ROLES
        ):
            raise ValueError("independent signoff count differs")
    elif artifact_id == "power-review-signoff":
        if (
            document["reviewer_role"] != "statistical-power-and-decision-reviewer"
            or document["decision"] != "APPROVE"
        ):
            raise ValueError("power reviewer role/decision differs")
    elif artifact_id == "committed-marker":
        if (
            document["hold_relative_path"] != ".cp65_auxiliary_reservation_hold.partial"
            or document["hold_absence_verified"] is not True
        ):
            raise ValueError("COMMITTED hold publication differs")
        if (
            not document["hold_removed_at_utc"]
            < document["hold_removal_directory_fsync_completed_at_utc"]
            < document["committed_at_utc"]
        ):
            raise ValueError("COMMITTED hold-removal publication order differs")


def _validate_source_materialization(
    payload: bytes,
) -> Tuple[Tuple[str, int, int, str], ...]:
    if len(payload) < 44 or len(payload) > 134_217_728 or payload[:8] != b"CP65SRC1":
        raise ValueError("source materialization framing differs")
    expected_archive = hashlib.sha256(
        b"cp65-test28-frozen-source-fixture-materialization-v1\0" + payload[:-32]
    ).digest()
    if not hmac.compare_digest(payload[-32:], expected_archive):
        raise ValueError("source materialization archive digest differs")
    view = memoryview(payload)
    limit = len(payload) - 32
    offset = 8
    count = int.from_bytes(view[offset : offset + 4], "big")
    offset += 4
    if not 1 <= count <= 4_096:
        raise ValueError("source materialization entry count differs")
    result = []
    aggregate = 12
    previous_path = ""
    for _ordinal in range(1, count + 1):
        if offset + 4 > limit:
            raise ValueError("source materialization path length is truncated")
        path_length = int.from_bytes(view[offset : offset + 4], "big")
        offset += 4
        if not 1 <= path_length <= 4_096 or offset + path_length + 40 > limit:
            raise ValueError("source materialization path frame differs")
        try:
            path = bytes(view[offset : offset + path_length]).decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError("source materialization path is not ASCII") from exc
        offset += path_length
        _require_relative_path(path, "source materialization path")
        if path <= previous_path or path in (
            "frozen_inputs/bound_files.json",
            "freeze_receipt.json",
            "frozen_inputs/source_fixture_materialization.bin",
        ):
            raise ValueError("source materialization path order/exclusion differs")
        previous_path = path
        content_length = int.from_bytes(view[offset : offset + 8], "big")
        offset += 8
        if content_length > 16_777_216 or offset + 32 + content_length > limit:
            raise ValueError("source materialization content length differs")
        content_sha = bytes(view[offset : offset + 32])
        offset += 32
        content = view[offset : offset + content_length]
        offset += content_length
        if not hmac.compare_digest(hashlib.sha256(content).digest(), content_sha):
            raise ValueError("source materialization content SHA differs")
        content_bytes = bytes(content)
        lines = (
            0
            if not content_bytes
            else content_bytes.count(b"\n") + int(not content_bytes.endswith(b"\n"))
        )
        aggregate += 44 + path_length + content_length
        if aggregate > 134_217_728:
            raise ValueError("source materialization aggregate exceeds bound")
        result.append((path, content_length, lines, content_sha.hex()))
    if offset != limit:
        raise ValueError("source materialization contains trailing bytes")
    return tuple(result)


def _auxiliary_transition_journal_prefix(
    payload: bytes,
    *,
    expected_auxiliary_reservation_raw_sha256: str = "",
    expected_schema_semantic_sha256: str = "",
) -> Tuple[int, str, Tuple[Tuple[int, ...], ...]]:
    if type(payload) is not bytes or len(payload) != 65_536:
        raise ValueError("auxiliary transition journal must be exactly 65536 bytes")
    header = payload[:256]
    if header[:8] != b"CP65AUX1" or int.from_bytes(header[8:16], "big") != 1:
        raise ValueError("auxiliary transition journal header differs")
    auxiliary_raw = header[16:48]
    semantic_raw = header[48:80]
    supplied_head0 = header[80:112]
    if (
        int.from_bytes(header[112:120], "big") != 255
        or int.from_bytes(header[120:128], "big") != 256
        or header[128:] != b"\0" * 128
    ):
        raise ValueError("auxiliary transition journal header framing differs")
    expected_head0 = hashlib.sha256(
        b"cp65-test28-auxiliary-reservation-transition-head-v1\0"
        + auxiliary_raw
        + semantic_raw
    ).digest()
    if not hmac.compare_digest(supplied_head0, expected_head0):
        raise ValueError("auxiliary transition journal initial head differs")
    if expected_auxiliary_reservation_raw_sha256:
        _require_sha256(
            expected_auxiliary_reservation_raw_sha256,
            "auxiliary reservation raw digest",
            nonzero=True,
        )
        if auxiliary_raw.hex() != expected_auxiliary_reservation_raw_sha256:
            raise ValueError("auxiliary transition journal reservation digest differs")
    if expected_schema_semantic_sha256:
        _require_sha256(
            expected_schema_semantic_sha256,
            "schema semantic digest",
            nonzero=True,
        )
        if semantic_raw.hex() != expected_schema_semantic_sha256:
            raise ValueError("auxiliary transition journal schema digest differs")
    head = supplied_head0
    parsed = []
    seen_code1_slots = set()
    checkpoint_codes = []
    slots = _i_auxiliary_slots(_i_build_bounds())
    checkpoint_slots = {
        3: next(
            index
            for index, row in enumerate(slots, 1)
            if row[0] == "preterminal-durable-artifact-inventory"
        ),
        4: next(
            index for index, row in enumerate(slots, 1) if row[0] == "terminal-state"
        ),
        5: next(
            index for index, row in enumerate(slots, 1) if row[0] == "sha256-manifest"
        ),
    }
    zero_slot = b"\0" * 256
    ended = False
    for index in range(255):
        slot = payload[256 + index * 256 : 512 + index * 256]
        if slot == zero_slot:
            ended = True
            continue
        if ended or slot[184:] != b"\0" * 72:
            raise ValueError("auxiliary transition journal suffix is torn")
        ordinal = int.from_bytes(slot[0:8], "big")
        artifact_slot = int.from_bytes(slot[8:16], "big")
        transition_code = int.from_bytes(slot[16:24], "big")
        allocated_before = int.from_bytes(slot[24:32], "big")
        allocated_after = int.from_bytes(slot[32:40], "big")
        hold_before = int.from_bytes(slot[40:48], "big")
        hold_after = int.from_bytes(slot[48:56], "big")
        target_path_sha256 = slot[56:88]
        target_raw_sha256 = slot[88:120]
        previous_head = slot[120:152]
        entry_sha256 = slot[152:184]
        if ordinal != index + 1 or transition_code not in range(1, 7):
            raise ValueError("auxiliary transition journal ordinal/code differs")
        if not (
            1 <= artifact_slot <= 183 or (transition_code == 6 and artifact_slot == 0)
        ):
            raise ValueError("auxiliary transition journal artifact slot differs")
        if (
            allocated_before + hold_before != 34_359_738_368
            or allocated_after + hold_after != 34_359_738_368
        ):
            raise ValueError("auxiliary transition journal hold complement differs")
        if parsed and (
            allocated_before != parsed[-1][4] or hold_before != parsed[-1][6]
        ):
            raise ValueError("auxiliary transition journal totals are discontinuous")
        zero_digest = b"\0" * 32
        if transition_code == 6:
            if (
                artifact_slot != 0
                or target_path_sha256 != zero_digest
                or target_raw_sha256 != zero_digest
                or allocated_before != allocated_after
                or hold_before != hold_after
            ):
                raise ValueError("auxiliary transition journal final seal differs")
        elif target_path_sha256 == zero_digest or target_raw_sha256 == zero_digest:
            raise ValueError("auxiliary transition journal target digest is zero")
        if transition_code in (1, 2) and checkpoint_codes:
            raise ValueError("auxiliary transition follows a terminal checkpoint")
        if transition_code == 1:
            if artifact_slot in seen_code1_slots:
                raise ValueError("auxiliary transition artifact slot repeats")
            seen_code1_slots.add(artifact_slot)
        elif transition_code == 2:
            if allocated_after != allocated_before or hold_after != hold_before:
                raise ValueError("auxiliary recovery recheck changes accounting")
        elif transition_code in (3, 4, 5):
            if artifact_slot != checkpoint_slots[transition_code]:
                raise ValueError("auxiliary checkpoint artifact slot differs")
            checkpoint_codes.append(transition_code)
            if checkpoint_codes != list(range(3, 3 + len(checkpoint_codes))):
                raise ValueError("auxiliary checkpoint code order differs")
        elif transition_code == 6 and checkpoint_codes != [3, 4, 5]:
            raise ValueError("auxiliary final seal precedes required checkpoints")
        if not hmac.compare_digest(previous_head, head):
            raise ValueError("auxiliary transition journal previous head differs")
        expected_entry = hashlib.sha256(
            b"cp65-test28-auxiliary-reservation-transition-entry-v1\0"
            + auxiliary_raw
            + slot[:152]
        ).digest()
        if not hmac.compare_digest(entry_sha256, expected_entry):
            raise ValueError("auxiliary transition journal entry digest differs")
        parsed.append(
            (
                ordinal,
                artifact_slot,
                transition_code,
                allocated_before,
                allocated_after,
                hold_before,
                hold_after,
                target_path_sha256.hex(),
                target_raw_sha256.hex(),
            )
        )
        head = entry_sha256
    if (
        parsed
        and parsed[-1][2] == 6
        and tuple(row[2] for row in parsed[-4:]) != (3, 4, 5, 6)
    ):
        raise ValueError("auxiliary sealed journal suffix differs")
    return len(parsed), head.hex(), tuple(parsed)


def _validate_auxiliary_transition_journal_against_reservation(
    reservation_document: dict,
    reservation_raw_bytes: bytes,
    journal_bytes: bytes,
    schema_semantic_sha256: str,
    supplied_by_path: Mapping[str, bytes],
) -> Tuple[int, int]:
    count, _head, parsed = _auxiliary_transition_journal_prefix(
        journal_bytes,
        expected_auxiliary_reservation_raw_sha256=hashlib.sha256(
            reservation_raw_bytes
        ).hexdigest(),
        expected_schema_semantic_sha256=schema_semantic_sha256,
    )
    rows = reservation_document.get("artifact_entries")
    if type(rows) is not list or len(rows) != 183:
        raise ValueError("auxiliary transition journal reservation rows differ")
    rows_by_ordinal = {
        row["ordinal"]: row
        for row in rows
        if type(row) is dict and type(row.get("ordinal")) is int
    }
    if set(rows_by_ordinal) != set(range(1, 184)):
        raise ValueError("auxiliary transition journal reservation slots differ")
    expected_allocated = (
        reservation_document["unique_nonhold_artifact_allocated_bytes"]
        + reservation_document["disjoint_allocation_and_directory_charge_bytes"]
    )
    expected_hold = reservation_document["hold_allocated_bytes"]
    if parsed and (parsed[0][3], parsed[0][5]) != (expected_allocated, expected_hold):
        raise ValueError("auxiliary transition journal initial totals differ")
    transitioned_slots = set()
    validated = 2
    unresolved = 0
    for entry in parsed:
        artifact_slot = entry[1]
        code = entry[2]
        if code == 6:
            continue
        row = rows_by_ordinal[artifact_slot]
        initial_state = row["reservation_state"]
        if code == 1:
            if (
                initial_state != "preallocated-partial-in-place"
                or row["artifact_id"]
                in (
                    "auxiliary-reservation-transition-journal",
                    "committed-marker",
                )
                or artifact_slot in transitioned_slots
            ):
                raise ValueError("auxiliary code1 initial slot state differs")
            transitioned_slots.add(artifact_slot)
        elif code == 2:
            if not (
                initial_state == "existing-final-in-place"
                or artifact_slot in transitioned_slots
            ):
                raise ValueError("auxiliary code2 target is not an existing final")
        primary_path = row["final_relative_path"]
        alternate_path = row["alternate_final_relative_path"]
        selected_path = ""
        for candidate in (primary_path, alternate_path):
            if (
                candidate
                and hashlib.sha256(candidate.encode("ascii")).hexdigest() == entry[7]
            ):
                selected_path = candidate
                break
        if not selected_path:
            raise ValueError("auxiliary transition target path differs")
        if selected_path not in supplied_by_path:
            unresolved += 1
        else:
            if hashlib.sha256(supplied_by_path[selected_path]).hexdigest() != entry[8]:
                raise ValueError("auxiliary transition target raw bytes differ")
            validated += 1
    return validated + count, unresolved


def _journal_prefix(
    payload: bytes, acquisition_start_body_sha256: str
) -> Tuple[int, str, Tuple[str, ...]]:
    if type(payload) is not bytes or len(payload) != 163_840:
        raise ValueError("acquisition journal must be the full preallocated file")
    _require_sha256(
        acquisition_start_body_sha256,
        "acquisition start receipt body digest",
        nonzero=True,
    )
    start_digest = bytes.fromhex(acquisition_start_body_sha256)
    head = hashlib.sha256(
        b"cp64-external-seed-acquisition-journal-head-v1\0" + start_digest
    ).digest()
    values = []
    zero_slot = b"\0" * 80
    for index in range(2_048):
        slot = payload[index * 80 : (index + 1) * 80]
        if slot == zero_slot:
            break
        ordinal_bytes = slot[:8]
        value_bytes = slot[8:16]
        previous = slot[16:48]
        supplied_entry = slot[48:80]
        ordinal = int.from_bytes(ordinal_bytes, "big")
        expected_entry = hashlib.sha256(
            b"cp64-external-seed-acquisition-journal-entry-v1\0"
            + start_digest
            + ordinal_bytes
            + value_bytes
            + previous
        ).digest()
        if (
            ordinal != index + 1
            or not hmac.compare_digest(previous, head)
            or not hmac.compare_digest(supplied_entry, expected_entry)
        ):
            break
        values.append(value_bytes.hex())
        head = supplied_entry
    return len(values), head.hex(), tuple(values)


def _ordered_seed_values_commitment(values: Tuple[str, ...]) -> str:
    return hashlib.sha256(
        b"cp64-test28-ordered-seed-sequence-v1\0"
        + _plain_json_bytes(
            {
                "seed_count": len(values),
                "seed_encoding": "uint64-16-lowercase-hex-big-endian",
                "ordered_seed_values": list(values),
            }
        )
    ).hexdigest()


def _validate_artifact_payload(
    artifact_id: str, relative_path: str, payload: bytes
) -> Tuple[str, object]:
    if artifact_id not in _I_ARTIFACT_BY_ID:
        raise ValueError("unknown CP65 artifact id")
    _require_relative_path(relative_path, "relative_path")
    if not _relative_path_matches_template(
        _I_ARTIFACT_BY_ID[artifact_id][1], relative_path
    ):
        raise ValueError("relative_path does not expand the artifact template")
    declaration = _I_ARTIFACT_BY_ID[artifact_id]
    if len(payload) > _i_artifact_maximum_bytes(artifact_id):
        raise ValueError("artifact payload exceeds its schema-specific byte cap")
    if artifact_id in _I_REFERENCED_OUTPUT_IDS:
        raise ValueError(
            "referenced execution/output containers are not semantic validator inputs"
        )
    if artifact_id == "frozen-protocol-sha256":
        expected = _FROZEN_PROTOCOL_SHA256.encode("ascii") + b"\n"
        if payload != expected:
            raise ValueError("frozen protocol SHA sidecar framing differs")
        return hashlib.sha256(payload).hexdigest(), payload[:-1].decode("ascii")
    if artifact_id == "frozen-protocol":
        if (
            len(payload) != _FROZEN_PROTOCOL_BYTES
            or hashlib.sha256(payload).hexdigest() != _FROZEN_PROTOCOL_SHA256
        ):
            raise ValueError("frozen protocol immutable bytes differ")
        return hashlib.sha256(payload).hexdigest(), payload
    if artifact_id == "dependency-lock":
        if (
            len(payload) != _FROZEN_DEPENDENCY_LOCK_BYTES
            or hashlib.sha256(payload).hexdigest() != _FROZEN_DEPENDENCY_LOCK_SHA256
        ):
            raise ValueError("frozen dependency-lock immutable bytes differ")
        return hashlib.sha256(payload).hexdigest(), payload
    if artifact_id == "external-seed-acquisition-journal":
        if len(payload) != 163_840:
            raise ValueError("acquisition journal must be the full preallocated file")
        return hashlib.sha256(payload).hexdigest(), payload
    if artifact_id == "frozen-source-fixture-materialization":
        return hashlib.sha256(payload).hexdigest(), _validate_source_materialization(
            payload
        )
    if artifact_id == "production-schema-preimage-validator-bundle":
        if payload != _independent_authoritative_bundle_canonical_bytes():
            raise ValueError("retained CP65 schema bundle bytes differ")
        return hashlib.sha256(payload).hexdigest(), payload
    if artifact_id == "frozen-machine-manifest":
        if (
            len(payload) != _FROZEN_MACHINE_MANIFEST_BYTES
            or hashlib.sha256(payload).hexdigest() != _FROZEN_MACHINE_MANIFEST_SHA256
        ):
            raise ValueError("frozen machine-manifest immutable bytes differ")
        return hashlib.sha256(payload).hexdigest(), payload
    if artifact_id == "auxiliary-reservation-transition-journal":
        parsed = _auxiliary_transition_journal_prefix(payload)
        return hashlib.sha256(payload).hexdigest(), parsed
    if not declaration[4]:
        raise ValueError("artifact has no CP65 semantic bytes validator")
    document = _parse_canonical_json_object(
        payload, _i_artifact_maximum_bytes(artifact_id)
    )
    exact_keys = declaration[4]
    if set(document) != set(exact_keys) or len(document) != len(exact_keys):
        raise ValueError("artifact exact top-level key set differs")
    nested = declaration[5]
    nested_by_key = dict(nested)
    for key in exact_keys:
        if key in nested_by_key:
            continue
        if _i_field_kind(key) == "array":
            _validate_primitive_array(artifact_id, key, document[key])
        else:
            _validate_scalar_field(artifact_id, "/" + key, key, document[key])
    _validate_nested_rows(artifact_id, document, nested)
    body_sha256 = _validate_body_digest(artifact_id, document)
    _validate_receipt_specific(artifact_id, document)
    return body_sha256, document


def _intrinsic_digest_instance_counts(
    artifact_id: str, document: object
) -> Tuple[int, int]:
    if artifact_id == "preflight-gate-summary":
        if type(document) is not dict:
            raise ValueError("preflight gate summary document differs")
        return 1, len(document["ordered_evidence_receipt_sha256s"]) + 2
    if artifact_id == "production-schedule":
        if type(document) is not dict or type(document.get("requests")) is not list:
            raise ValueError("production schedule document differs")
        count = len(document["requests"])
        return 3 * count + 3, 2 * count + 3
    if artifact_id == "power-threshold-receipt":
        if (
            type(document) is not dict
            or type(document.get("ordered_slot_thresholds")) is not list
        ):
            raise ValueError("power threshold receipt document differs")
        count = len(document["ordered_slot_thresholds"])
        return count + 3, count + 5
    if artifact_id == "capacity-receipt":
        return 1, 8
    if artifact_id == "external-digest-preimage-registry":
        if type(document) is not dict or type(document.get("entries")) is not list:
            raise ValueError("external digest registry document differs")
        count = len(document["entries"])
        return 2 * count + 2, count + 3
    if artifact_id == "preterminal-durable-artifact-inventory":
        if type(document) is not dict:
            raise ValueError("preterminal inventory document differs")
        count = len(document["entries"])
        return count + 2, count + 1
    if artifact_id == "terminal-state":
        return 1, 4
    if artifact_id == "sha256-manifest":
        if type(document) is not dict:
            raise ValueError("SHA256 manifest document differs")
        return 2, len(document["entries"]) + 2
    return 1, 1


def _public_key_identity(
    key: dict, *, scheme_field: str, identity_domain: bytes
) -> str:
    identity = {
        scheme_field: key[scheme_field],
        "authority_id": key.get("authority_id", key.get("source_authority_id")),
        "modulus_hex": key["modulus_hex"],
        "public_exponent": key["public_exponent"],
    }
    if scheme_field == "source_authority_scheme_id":
        identity["source_authority_id"] = identity.pop("authority_id")
    return hashlib.sha256(identity_domain + _plain_json_bytes(identity)).hexdigest()


def _verify_signed_document(
    document: dict,
    key: dict,
    *,
    scheme_field: str,
    identity_field: str,
    signature_hex_field: str,
    signature_sha_field: str,
    issued_field: str,
    expires_field: str,
    key_scheme_field: str,
    key_identity_domain: bytes,
    signing_domain: bytes,
) -> bool:
    if (
        document[scheme_field] != key[key_scheme_field]
        or key["public_exponent"] != 65_537
    ):
        return False
    expected_identity = _public_key_identity(
        key, scheme_field=key_scheme_field, identity_domain=key_identity_domain
    )
    if document[identity_field] != expected_identity:
        return False
    issued = _require_utc(document[issued_field], issued_field)
    expires = _require_utc(document[expires_field], expires_field)
    valid_from = _require_utc(key["valid_from_utc"], "valid_from_utc")
    valid_until = _require_utc(key["valid_until_utc"], "valid_until_utc")
    if not valid_from <= issued < expires <= valid_until:
        return False
    signature_hex = document[signature_hex_field]
    if type(signature_hex) is not str or _HEX768_RE.fullmatch(signature_hex) is None:
        return False
    signature = bytes.fromhex(signature_hex)
    if document[signature_sha_field] != hashlib.sha256(signature).hexdigest():
        return False
    unsigned = dict(document)
    unsigned[signature_hex_field] = ""
    unsigned[signature_sha_field] = _ZERO_SHA256
    unsigned["body_sha256"] = _ZERO_SHA256
    return _verify_rsa_pss_sha256_3072(
        signing_domain + _plain_json_bytes(unsigned),
        bytes.fromhex(key["modulus_hex"]),
        signature,
    )


def _validate_registry_target_bindings(
    by_id: dict,
) -> Tuple[int, Tuple[Tuple[str, str], ...]]:
    if "external-digest-preimage-registry" not in by_id:
        return 0, ()
    registry = by_id["external-digest-preimage-registry"][0][3]
    if type(registry) is not dict:
        raise ValueError("external digest registry document differs")
    validated = 0
    resolved = []
    for entry in registry["entries"]:
        selector = _parse_canonical_json_object(
            entry["target_instance_selector_json_ascii"].encode("ascii"), 4_096
        )
        wildcard_indices = tuple(selector["wildcard_indices"])
        candidates = tuple(
            row
            for row in by_id.get(entry["target_artifact_id"], ())
            if row[0] == entry["target_relative_path"]
        )
        if not candidates:
            continue
        if len(candidates) != 1:
            raise ValueError("registry target artifact instance is ambiguous")
        target_path, target_raw, _target_body, target_document = candidates[0]
        if (
            hashlib.sha256(target_raw).hexdigest()
            != entry["target_artifact_raw_sha256"]
        ):
            raise ValueError("registry target raw digest differs")
        try:
            selected = _resolve_registry_target_pointer(
                target_document, entry["target_json_pointer"], wildcard_indices
            )
        except ValueError as exc:
            raise ValueError("registry target pointer does not resolve") from exc
        if selected != entry["digest_sha256"]:
            raise ValueError("registry target pointer digest differs")
        validated += 1
        resolved.append((entry["target_artifact_id"], target_path))
    return validated, tuple(resolved)


def _validate_independent_signoff_aggregation(
    by_id: dict,
) -> Tuple[bool, bool, int]:
    if "independent-signoff-set" not in by_id:
        return False, False, 0
    if (
        "independent-reviewer-public-key-set" not in by_id
        or "preflight-gate-summary" not in by_id
    ):
        return False, False, 0
    document = by_id["independent-signoff-set"][0][3]
    key_set = by_id["independent-reviewer-public-key-set"][0][3]
    summary_raw = hashlib.sha256(by_id["preflight-gate-summary"][0][1]).hexdigest()
    key_set_raw = hashlib.sha256(
        by_id["independent-reviewer-public-key-set"][0][1]
    ).hexdigest()
    if (
        document["preflight_gate_summary_sha256"] != summary_raw
        or document["reviewer_public_key_set_sha256"] != key_set_raw
    ):
        raise ValueError("independent signoff outer raw binding differs")
    rows = document["ordered_signoffs"]
    keys = key_set["ordered_keys"]
    roles = tuple(row["reviewer_role"] for row in rows)
    if (
        len(rows) != 4
        or len(keys) != 4
        or roles != _I_REQUIRED_REVIEWER_ROLES
        or len(set(roles)) != 4
    ):
        raise ValueError("independent signoff reviewer role coverage differs")
    validities = []
    for row, key, expected_role in zip(rows, keys, _I_REQUIRED_REVIEWER_ROLES):
        if (
            key["reviewer_role"] != expected_role
            or row["reviewer_role"] != expected_role
            or row["reviewed_artifact_sha256s"] != [summary_raw]
            or row["decision"] != "APPROVE"
            or row["reviewer_identity_sha256"] != key["reviewer_identity_sha256"]
            or row["reviewer_public_key_identity_sha256"] != _reviewer_key_identity(key)
            or row["signature_scheme_id"] != key["signature_scheme_id"]
            or row["signature_scheme_id"] != "rsa-pss-sha256-3072-e65537-salt32-v1"
            or key["public_exponent"] != 65_537
        ):
            raise ValueError("independent signoff row/key binding differs")
        signed_at = _require_utc(row["signed_at_utc"], "signed_at_utc")
        valid_from = _require_utc(key["valid_from_utc"], "valid_from_utc")
        valid_until = _require_utc(key["valid_until_utc"], "valid_until_utc")
        signature = bytes.fromhex(row["reviewer_signature_hex"])
        unsigned = dict(row)
        unsigned["reviewer_signature_hex"] = ""
        unsigned["reviewer_signature_sha256"] = _ZERO_SHA256
        unsigned["signoff_sha256"] = _ZERO_SHA256
        validities.append(
            valid_from <= signed_at < valid_until
            and row["reviewer_signature_sha256"]
            == hashlib.sha256(signature).hexdigest()
            and _verify_rsa_pss_sha256_3072(
                b"cp65-test28-independent-signoff-row-signature-preimage-v1\0"
                + _plain_json_bytes(unsigned),
                bytes.fromhex(key["modulus_hex"]),
                signature,
            )
        )
    derived = (
        roles == _I_REQUIRED_REVIEWER_ROLES,
        all(row["decision"] == "APPROVE" for row in rows),
        all(validities),
    )
    declared = (
        document["all_required_roles_present"],
        document["all_decisions_approve"],
        document["all_signatures_mathematically_valid_under_declared_keys"],
    )
    if derived != (True, True, True) or declared != derived:
        raise ValueError("independent signoff derived aggregate differs")
    return True, True, 12


def _validate_supplied_signature_aggregation(
    by_id: dict,
) -> Tuple[bool, bool, int, int]:
    applicable = False
    validities = []
    validated = 0
    unresolved = 0
    for signed_id in (
        "launch-authorization",
        "rejected-launch-authorization-candidate",
    ):
        if signed_id not in by_id:
            continue
        applicable = True
        if "launch-authority-public-key" not in by_id:
            unresolved += 1
            validities.append(False)
            continue
        validities.append(
            _verify_signed_document(
                by_id[signed_id][0][3],
                by_id["launch-authority-public-key"][0][3],
                scheme_field="authority_scheme_id",
                identity_field="authority_identity_sha256",
                signature_hex_field="authority_signature_hex",
                signature_sha_field="authority_signature_sha256",
                issued_field="authorization_issued_at_utc",
                expires_field="authorization_expires_at_utc",
                key_scheme_field="authority_scheme_id",
                key_identity_domain=b"cp65-test28-launch-authority-public-key-identity-v1\0",
                signing_domain=b"cp65-test28-launch-authorization-signature-preimage-v1\0",
            )
        )
        validated += 1
    if "seed-source-authority-attestation" in by_id:
        applicable = True
        if "seed-source-authority-public-key" not in by_id:
            unresolved += 1
            validities.append(False)
        else:
            validities.append(
                _verify_signed_document(
                    by_id["seed-source-authority-attestation"][0][3],
                    by_id["seed-source-authority-public-key"][0][3],
                    scheme_field="source_authority_scheme_id",
                    identity_field="source_authority_identity_sha256",
                    signature_hex_field="source_authority_signature_hex",
                    signature_sha_field="source_authority_signature_sha256",
                    issued_field="attested_at_utc",
                    expires_field="attestation_expires_at_utc",
                    key_scheme_field="source_authority_scheme_id",
                    key_identity_domain=b"cp65-test28-seed-source-authority-public-key-identity-v1\0",
                    signing_domain=b"cp65-test28-seed-source-authority-attestation-signature-preimage-v1\0",
                )
            )
            validated += 1
    if "power-review-signoff" in by_id:
        applicable = True
        if "independent-reviewer-public-key-set" not in by_id:
            unresolved += 1
            validities.append(False)
        else:
            document = by_id["power-review-signoff"][0][3]
            keys = tuple(
                key
                for key in by_id["independent-reviewer-public-key-set"][0][3][
                    "ordered_keys"
                ]
                if key["reviewer_role"] == "statistical-power-and-decision-reviewer"
            )
            if len(keys) != 1:
                raise ValueError("power reviewer role does not select one key")
            key = keys[0]
            signature = bytes.fromhex(document["reviewer_signature_hex"])
            unsigned = dict(document)
            unsigned["reviewer_signature_hex"] = ""
            unsigned["reviewer_signature_sha256"] = _ZERO_SHA256
            unsigned["body_sha256"] = _ZERO_SHA256
            validities.append(
                document["reviewer_role"] == key["reviewer_role"]
                and document["reviewer_identity_sha256"]
                == key["reviewer_identity_sha256"]
                and document["reviewer_public_key_identity_sha256"]
                == _reviewer_key_identity(key)
                and document["decision"] == "APPROVE"
                and document["signature_scheme_id"] == key["signature_scheme_id"]
                and document["signature_scheme_id"]
                == "rsa-pss-sha256-3072-e65537-salt32-v1"
                and key["public_exponent"] == 65_537
                and key["valid_from_utc"]
                <= document["signed_at_utc"]
                < key["valid_until_utc"]
                and document["reviewer_signature_sha256"]
                == hashlib.sha256(signature).hexdigest()
                and _verify_rsa_pss_sha256_3072(
                    b"cp65-test28-power-review-signoff-signature-preimage-v1\0"
                    + _plain_json_bytes(unsigned),
                    bytes.fromhex(key["modulus_hex"]),
                    signature,
                )
            )
            validated += 1
    if "independent-signoff-set" in by_id:
        applicable = True
        missing = tuple(
            artifact_id
            for artifact_id in (
                "independent-reviewer-public-key-set",
                "preflight-gate-summary",
            )
            if artifact_id not in by_id
        )
        if missing:
            unresolved += len(missing)
            validities.append(False)
        else:
            _applies, valid, count = _validate_independent_signoff_aggregation(by_id)
            validities.append(valid)
            validated += count
    return (
        applicable,
        bool(applicable and unresolved == 0 and all(validities)),
        validated,
        unresolved,
    )


def _validate_terminal_publication_cross_bindings(by_id: dict) -> Tuple[int, int]:
    validated = 0
    unresolved = 0
    by_path = {row[0]: row for rows in by_id.values() for row in rows}

    def require_raw_entry(entry: dict) -> None:
        nonlocal validated, unresolved
        source = by_path.get(entry["path"])
        if source is None:
            unresolved += 1
            return
        raw_bytes = source[1]
        if (
            entry["bytes"] != len(raw_bytes)
            or entry["sha256"] != hashlib.sha256(raw_bytes).hexdigest()
        ):
            raise ValueError("terminal publication member raw bytes differ")
        validated += 1

    inventory = None
    if "preterminal-durable-artifact-inventory" in by_id:
        candidate = by_id["preterminal-durable-artifact-inventory"][0][3]
        inventory = (
            candidate if type(candidate) is dict and "entries" in candidate else None
        )
    if inventory is not None:
        for entry in inventory["entries"]:
            require_raw_entry(entry)
        excluded = {
            "preterminal_durable_artifact_inventory.json",
            "terminal_state.json",
            "sha256_manifest.json",
            "COMMITTED.json",
            "auxiliary_reservation_transition_journal.bin",
        }
        eligible = {path for path in by_path if path not in excluded}
        inventoried = {entry["path"] for entry in inventory["entries"]}
        if not eligible.issubset(inventoried):
            raise ValueError("preterminal inventory omits a supplied durable artifact")
        unresolved += 1
    terminal = None
    if "terminal-state" in by_id:
        terminal = by_id["terminal-state"][0][3]
        if "preterminal-durable-artifact-inventory" not in by_id:
            unresolved += 1
        else:
            expected = hashlib.sha256(
                by_id["preterminal-durable-artifact-inventory"][0][1]
            ).hexdigest()
            if terminal["durable_artifact_inventory_sha256"] != expected:
                raise ValueError(
                    "cross-artifact digest binding differs: "
                    "durable_artifact_inventory_sha256"
                )
            if (
                inventory is not None
                and inventory["terminal_arm"] != terminal["terminal_arm"]
            ):
                raise ValueError("inventory and terminal arms differ")
            validated += 1
        branch_sources = [
            ("freeze-receipt", "freeze_receipt_sha256"),
            ("preauthorization-outcome", "preauthorization_outcome_sha256"),
        ]
        if terminal["terminal_arm"] in ("POSTAUTHORIZATION_PRESTART", "STARTED"):
            branch_sources.extend(
                (
                    ("launch-authorization", "launch_authorization_sha256"),
                    ("postauthorization-outcome", "postauthorization_outcome_sha256"),
                )
            )
        if terminal["terminal_arm"] == "STARTED":
            branch_sources.append(("started-receipt", "started_receipt_sha256"))
        for source_id, pointer in branch_sources:
            if source_id not in by_id:
                unresolved += 1
            else:
                expected = hashlib.sha256(by_id[source_id][0][1]).hexdigest()
                if terminal[pointer] != expected:
                    raise ValueError(
                        "cross-artifact digest binding differs: " + pointer
                    )
                validated += 1
        unresolved += 1
    if "sha256-manifest" in by_id:
        manifest = by_id["sha256-manifest"][0][3]
        if "terminal-state" not in by_id:
            unresolved += 1
        else:
            expected = hashlib.sha256(by_id["terminal-state"][0][1]).hexdigest()
            if manifest["terminal_state_sha256"] != expected:
                raise ValueError("SHA256 manifest terminal raw binding differs")
            validated += 1
        for entry in manifest["entries"]:
            require_raw_entry(entry)
        unresolved += 1
        if inventory is not None and terminal is not None:
            expected_entries = [
                {"path": row["path"], "bytes": row["bytes"], "sha256": row["sha256"]}
                for row in inventory["entries"]
            ]
            inventory_payload = by_id["preterminal-durable-artifact-inventory"][0][1]
            terminal_payload = by_id["terminal-state"][0][1]
            expected_entries.extend(
                (
                    {
                        "path": "preterminal_durable_artifact_inventory.json",
                        "bytes": len(inventory_payload),
                        "sha256": hashlib.sha256(inventory_payload).hexdigest(),
                    },
                    {
                        "path": "terminal_state.json",
                        "bytes": len(terminal_payload),
                        "sha256": hashlib.sha256(terminal_payload).hexdigest(),
                    },
                )
            )
            expected_entries.sort(key=lambda row: row["path"])
            if manifest["entries"] != expected_entries:
                raise ValueError("SHA256 manifest branch membership differs")
            if (
                not inventory["created_at_utc"]
                < terminal["terminalized_at_utc"]
                < manifest["created_at_utc"]
            ):
                raise ValueError("terminal publication chronology differs")
    return validated, unresolved


_I_VALIDATION_CROSS_LINKS = (
    (
        "external-seed-acquisition-start-receipt",
        "freeze-receipt",
        "freeze_receipt_sha256",
        "raw",
    ),
    ("freeze-receipt", "frozen-protocol", "protocol_sha256", "raw"),
    ("freeze-receipt", "frozen-machine-manifest", "machine_manifest_sha256", "raw"),
    ("freeze-receipt", "source-manifest", "bound_files_sha256", "raw"),
    ("freeze-receipt", "dependency-lock", "dependency_lock_sha256", "raw"),
    (
        "freeze-receipt",
        "frozen-source-fixture-materialization",
        "frozen_source_fixture_materialization_sha256",
        "raw",
    ),
    (
        "freeze-receipt",
        "production-schema-preimage-validator-bundle",
        "production_receipt_schema_bundle_sha256",
        "raw",
    ),
    (
        "freeze-receipt",
        "power-threshold-receipt",
        "power_threshold_receipt_sha256",
        "raw",
    ),
    (
        "freeze-receipt",
        "launch-authority-public-key",
        "launch_authority_public_key_sha256",
        "raw",
    ),
    (
        "freeze-receipt",
        "independent-reviewer-public-key-set",
        "independent_reviewer_public_key_set_sha256",
        "raw",
    ),
    (
        "freeze-receipt",
        "seed-source-authority-public-key",
        "seed_source_authority_public_key_sha256",
        "raw",
    ),
    (
        "external-seed-source-receipt",
        "external-seed-acquisition-start-receipt",
        "acquisition_start_receipt_sha256",
        "body",
    ),
    (
        "external-seed-source-receipt",
        "seed-source-authority-attestation",
        "source_authority_attestation_sha256",
        "raw",
    ),
    (
        "seed-capsule-body",
        "external-seed-source-receipt",
        "source_receipt_sha256",
        "raw",
    ),
    ("production-schedule", "seed-capsule-body", "seed_capsule_body_sha256", "body"),
    ("capacity-receipt", "production-schedule", "schedule_sha256", "raw"),
    (
        "capacity-receipt",
        "auxiliary-metadata-reservation",
        "auxiliary_metadata_reservation_artifact_sha256",
        "raw",
    ),
    ("capacity-receipt", "reservation-manifest", "reservation_manifest_sha256", "raw"),
    ("durability-receipt", "capacity-receipt", "capacity_receipt_sha256", "raw"),
    (
        "production-shard-map-receipt",
        "capacity-receipt",
        "capacity_receipt_sha256",
        "raw",
    ),
    (
        "production-shard-map-receipt",
        "durability-receipt",
        "durability_receipt_sha256",
        "raw",
    ),
    (
        "independent-signoff-set",
        "preflight-gate-summary",
        "preflight_gate_summary_sha256",
        "raw",
    ),
    (
        "independent-signoff-set",
        "independent-reviewer-public-key-set",
        "reviewer_public_key_set_sha256",
        "raw",
    ),
    (
        "preflight-gate-summary",
        "external-digest-preimage-registry",
        "external_digest_preimage_registry_sha256",
        "raw",
    ),
    ("preflight-gate-summary", "freeze-receipt", "freeze_receipt_sha256", "raw"),
    ("launch-authorization", "frozen-protocol", "protocol_sha256", "raw"),
    (
        "launch-authorization",
        "frozen-machine-manifest",
        "machine_manifest_sha256",
        "raw",
    ),
    ("launch-authorization", "source-manifest", "source_manifest_sha256", "raw"),
    ("launch-authorization", "dependency-lock", "dependency_lock_sha256", "raw"),
    (
        "launch-authorization",
        "external-seed-source-receipt",
        "seed_source_receipt_sha256",
        "raw",
    ),
    ("launch-authorization", "seed-capsule-body", "seed_capsule_body_sha256", "body"),
    ("launch-authorization", "production-schedule", "schedule_sha256", "raw"),
    (
        "launch-authorization",
        "production-runtime-receipt",
        "production_runtime_receipt_sha256",
        "raw",
    ),
    ("launch-authorization", "capacity-receipt", "capacity_receipt_sha256", "raw"),
    ("launch-authorization", "durability-receipt", "durability_receipt_sha256", "raw"),
    (
        "launch-authorization",
        "production-shard-map-receipt",
        "production_shard_map_receipt_sha256",
        "raw",
    ),
    (
        "launch-authorization",
        "preflight-gate-summary",
        "preflight_gate_summary_sha256",
        "raw",
    ),
    (
        "launch-authorization",
        "power-threshold-receipt",
        "power_threshold_receipt_sha256",
        "raw",
    ),
    ("launch-authorization", "freeze-receipt", "freeze_receipt_sha256", "raw"),
    (
        "launch-authorization",
        "independent-signoff-set",
        "independent_signoff_sha256",
        "raw",
    ),
    ("committed-marker", "terminal-state", "terminal_state_sha256", "raw"),
    ("committed-marker", "sha256-manifest", "sha256_manifest_sha256", "raw"),
    (
        "committed-marker",
        "auxiliary-metadata-reservation",
        "auxiliary_metadata_reservation_sha256",
        "raw",
    ),
)


def _validate_supplied_cross_bindings(by_id: dict) -> Tuple[int, int]:
    documents = [
        document
        for rows in by_id.values()
        for _path, _payload, _body, document in rows
        if type(document) is dict
    ]
    attempt_ids = {
        document["attempt_id"] for document in documents if "attempt_id" in document
    }
    if len(attempt_ids) > 1:
        raise ValueError("supplied artifacts cross different attempt ids")
    validated, unresolved = _validate_terminal_publication_cross_bindings(by_id)

    def raw(artifact_id: str) -> str:
        return hashlib.sha256(by_id[artifact_id][0][1]).hexdigest()

    def body(artifact_id: str) -> str:
        return by_id[artifact_id][0][2]

    auxiliary_present = "auxiliary-metadata-reservation" in by_id
    transition_journal_present = "auxiliary-reservation-transition-journal" in by_id
    if auxiliary_present or transition_journal_present:
        if not (auxiliary_present and transition_journal_present):
            unresolved += 1
        else:
            supplied_by_path = {
                path: payload
                for rows in by_id.values()
                for path, payload, _body_digest, _document in rows
            }
            (
                journal_validated,
                journal_unresolved,
            ) = _validate_auxiliary_transition_journal_against_reservation(
                by_id["auxiliary-metadata-reservation"][0][3],
                by_id["auxiliary-metadata-reservation"][0][1],
                by_id["auxiliary-reservation-transition-journal"][0][1],
                _I_SCHEMA_SEMANTIC_SHA256,
                supplied_by_path,
            )
            validated += journal_validated
            unresolved += journal_unresolved
    if "committed-marker" in by_id:
        if "auxiliary-reservation-transition-journal" not in by_id:
            unresolved += 3
        else:
            committed = by_id["committed-marker"][0][3]
            journal_payload = by_id["auxiliary-reservation-transition-journal"][0][1]
            (
                final_count,
                final_head,
                final_entries,
            ) = _auxiliary_transition_journal_prefix(journal_payload)
            if (
                final_count < 4
                or not final_entries
                or tuple(row[2] for row in final_entries[-4:]) != (3, 4, 5, 6)
            ):
                raise ValueError("COMMITTED transition journal is not finally sealed")
            if (
                committed["auxiliary_reservation_transition_journal_sha256"]
                != hashlib.sha256(journal_payload).hexdigest()
            ):
                raise ValueError("COMMITTED transition journal raw digest differs")
            if (
                committed["auxiliary_reservation_transition_journal_final_head_sha256"]
                != final_head
            ):
                raise ValueError("COMMITTED transition journal final head differs")
            if (
                committed["auxiliary_reservation_transition_journal_final_entry_count"]
                != final_count
            ):
                raise ValueError("COMMITTED transition journal final count differs")
            journal_file_fsync = committed[
                "auxiliary_reservation_transition_journal_file_fsync_completed_at_utc"
            ]
            journal_directory_fsync = committed[
                "auxiliary_reservation_transition_journal_directory_fsync_completed_at_utc"
            ]
            if not (
                journal_file_fsync
                < journal_directory_fsync
                < committed["hold_removed_at_utc"]
                < committed["hold_removal_directory_fsync_completed_at_utc"]
                < committed["committed_at_utc"]
            ):
                raise ValueError("COMMITTED transition journal chronology differs")
            if (
                "preterminal-durable-artifact-inventory" in by_id
                and "terminal-state" in by_id
                and "sha256-manifest" in by_id
                and not (
                    by_id["preterminal-durable-artifact-inventory"][0][3][
                        "created_at_utc"
                    ]
                    < by_id["terminal-state"][0][3]["terminalized_at_utc"]
                    < by_id["sha256-manifest"][0][3]["created_at_utc"]
                    < journal_file_fsync
                )
            ):
                raise ValueError("COMMITTED terminal publication chronology differs")
            validated += 3

    for target_id, source_id, pointer, digest_kind in _I_VALIDATION_CROSS_LINKS:
        if target_id not in by_id:
            continue
        target = by_id[target_id][0][3]
        if type(target) is not dict or pointer not in target:
            continue
        if source_id not in by_id:
            unresolved += 1
            continue
        expected = body(source_id) if digest_kind == "body" else raw(source_id)
        if target[pointer] != expected:
            raise ValueError("cross-artifact digest binding differs: " + pointer)
        validated += 1
    if "committed-marker" in by_id and "auxiliary-metadata-reservation" in by_id:
        committed = by_id["committed-marker"][0][3]
        reservation = by_id["auxiliary-metadata-reservation"][0][3]
        for key in (
            "hold_relative_path",
            "hold_device_identity_sha256",
            "hold_inode",
            "hold_extent_map_sha256",
        ):
            if committed[key] != reservation[key]:
                raise ValueError("COMMITTED hold identity differs: " + key)
        validated += 4
    if "frozen-protocol-sha256" in by_id:
        if "frozen-protocol" not in by_id:
            unresolved += 1
        else:
            if by_id["frozen-protocol-sha256"][0][3] != raw("frozen-protocol"):
                raise ValueError("cross-artifact frozen protocol sidecar differs")
            validated += 1
    for (
        (target_id, target_pointer),
        source_contract_id,
    ) in _I_SHA256_POINTER_SOURCE_CONTRACT_OVERRIDES.items():
        selected_value = _I_V15_SELECTED_STORED_SHA256_BY_CONTRACT_ID.get(
            source_contract_id
        )
        if selected_value is None:
            continue
        if target_id not in by_id:
            continue
        if "frozen-machine-manifest" not in by_id:
            unresolved += 1
            continue
        _require_sha256(
            selected_value, "selected predecessor stored digest", nonzero=True
        )
        target_document = by_id[target_id][0][3]
        if target_pointer == "/requests/*/runtime_lock_sha256":
            target_values = tuple(
                row["runtime_lock_sha256"] for row in target_document["requests"]
            )
            if not target_values or any(
                value != selected_value for value in target_values
            ):
                raise ValueError("selected predecessor stored digest binding differs")
            validated += len(target_values)
        else:
            target_value = _resolve_closed_json_pointer(target_document, target_pointer)
            if target_value != selected_value:
                raise ValueError("selected predecessor stored digest binding differs")
            validated += 1
    if "source-manifest" in by_id and type(by_id["source-manifest"][0][3]) is dict:
        if "frozen-source-fixture-materialization" not in by_id:
            unresolved += 1
        else:
            manifest_rows = by_id["source-manifest"][0][3]["entries"]
            archive_rows = by_id["frozen-source-fixture-materialization"][0][3]
            projection = tuple(
                (row["relative_path"], row["bytes"], row["lines"], row["sha256"])
                for row in manifest_rows
            )
            if projection != archive_rows:
                raise ValueError(
                    "source materialization rows differ from source manifest"
                )
            validated += len(archive_rows)
    for qualification_id, pointer in (
        (
            "independent-full-32768-recomputation-qualification-receipt",
            "independent_recomputation_source_manifest_sha256",
        ),
        (
            "independent-554-estimate-interval-decision-path-qualification-receipt",
            "independent_source_manifest_sha256",
        ),
    ):
        if qualification_id not in by_id:
            continue
        if "source-manifest" not in by_id:
            unresolved += 1
            continue
        expected_submanifest = _independent_recomputation_source_submanifest_sha256(
            by_id["source-manifest"][0][3]
        )
        if by_id[qualification_id][0][3][pointer] != expected_submanifest:
            raise ValueError(
                "independent qualification source submanifest digest differs"
            )
        validated += 1
    if "power-review-signoff" in by_id:
        if "power-threshold-receipt" not in by_id:
            unresolved += 1
        else:
            signoff = by_id["power-review-signoff"][0][3]
            receipt = by_id["power-threshold-receipt"][0][3]
            for key in (
                "protocol_sha256",
                "machine_manifest_sha256",
                "power_review_sha256",
                "selected_count_justification_sha256",
                "primary_slot_count",
                "ordered_slot_threshold_row_sha256s",
                "ordered_slot_thresholds_sha256",
            ):
                if signoff[key] != receipt[key]:
                    raise ValueError("power-review signoff binding differs: " + key)
                validated += 1
    journal_dependents = tuple(
        artifact_id
        for artifact_id in (
            "partial-seed-acquisition-terminal-receipt",
            "external-seed-source-receipt",
            "seed-source-authority-attestation",
        )
        if artifact_id in by_id
    )
    if journal_dependents:
        missing = tuple(
            artifact_id
            for artifact_id in (
                "external-seed-acquisition-start-receipt",
                "external-seed-acquisition-journal",
            )
            if artifact_id not in by_id
        )
        if missing:
            unresolved += len(missing) * len(journal_dependents)
        else:
            start_body = body("external-seed-acquisition-start-receipt")
            journal_payload = by_id["external-seed-acquisition-journal"][0][1]
            prefix_count, prefix_head, prefix_values = _journal_prefix(
                journal_payload, start_body
            )
            journal_sha = hashlib.sha256(journal_payload).hexdigest()
            commitment = _ordered_seed_values_commitment(prefix_values)
            for artifact_id in journal_dependents:
                document = by_id[artifact_id][0][3]
                if document["acquisition_start_receipt_sha256"] != start_body:
                    raise ValueError("journal dependent start digest differs")
                if document["acquisition_journal_sha256"] != journal_sha:
                    raise ValueError("journal dependent full-file digest differs")
                if document["acquisition_journal_head_sha256"] != prefix_head:
                    raise ValueError("journal dependent recovered head differs")
                if document["acquisition_journal_entry_count"] != prefix_count:
                    raise ValueError("journal dependent recovered count differs")
                commitment_key = (
                    "ordered_partial_seed_values_commitment_sha256"
                    if artifact_id == "partial-seed-acquisition-terminal-receipt"
                    else "ordered_seed_values_commitment_sha256"
                )
                if document[commitment_key] != commitment:
                    raise ValueError("journal dependent sequence commitment differs")
                if artifact_id == "partial-seed-acquisition-terminal-receipt":
                    if document["acquisition_journal_raw_bytes"] != 163_840:
                        raise ValueError("partial journal raw-byte count differs")
                    if tuple(document["ordered_partial_seed_values"]) != prefix_values:
                        raise ValueError("partial journal values differ")
                elif prefix_count != 2_048:
                    raise ValueError(
                        "completed journal does not contain 2048 valid entries"
                    )
                validated += 5
    if (
        "partial-seed-acquisition-terminal-receipt" in by_id
        and "external-seed-source-receipt" in by_id
    ):
        raise ValueError("partial and completed source receipt arms cannot coexist")
    if (
        "preauthorization-outcome" in by_id
        and type(by_id["preauthorization-outcome"][0][3]) is dict
        and "prepared_launch_authorization_sha256"
        in by_id["preauthorization-outcome"][0][3]
    ):
        outcome = by_id["preauthorization-outcome"][0][3]
        prepared = outcome["prepared_launch_authorization_sha256"]
        if outcome["outcome_arm"] == "AUTHORIZATION":
            if "launch-authorization" not in by_id or prepared != raw(
                "launch-authorization"
            ):
                raise ValueError(
                    "authorization outcome does not bind published identical bytes"
                )
            if "rejected-launch-authorization-candidate" in by_id:
                raise ValueError(
                    "authorization winner cannot retain rejected candidate"
                )
        elif prepared != _ZERO_SHA256:
            if "rejected-launch-authorization-candidate" not in by_id:
                raise ValueError(
                    "losing prepared authorization candidate is not retained"
                )
            if prepared != raw("rejected-launch-authorization-candidate"):
                raise ValueError("rejected authorization candidate bytes differ")
            if "launch-authorization" in by_id:
                raise ValueError(
                    "terminal preauthorization arm published final authorization"
                )
    if "production-schedule" in by_id and "seed-capsule-body" in by_id:
        schedule = by_id["production-schedule"][0][3]
        capsule = by_id["seed-capsule-body"][0][3]
        for row in schedule["requests"]:
            if (
                row["plan_seed_hex"]
                != capsule["ordered_seed_values"][row["seed_ordinal"] - 1]
            ):
                raise ValueError("schedule plan seed differs from capsule ordinal")
        validated += 1
    return validated, unresolved


def _validate_supplied_artifact_bytes_impl(
    artifact_id: object, relative_path: object, payload: object
) -> CP65IndependentSuppliedValidationV1:
    normalized_id, normalized_path, normalized_payload = _normalize_supplied_artifact(
        artifact_id, relative_path, payload
    )
    body_sha256, document = _validate_artifact_payload(
        normalized_id, normalized_path, normalized_payload
    )
    validated_cross, unresolved_cross = _validate_supplied_cross_bindings(
        {normalized_id: [(normalized_path, normalized_payload, body_sha256, document)]}
    )
    validated_digest, unresolved_digest = _intrinsic_digest_instance_counts(
        normalized_id, document
    )
    return _supplied_validation(
        (normalized_id,),
        (normalized_path,),
        (normalized_payload,),
        (body_sha256,),
        validated_digest_preimage_count=validated_digest,
        unresolved_digest_preimage_count=unresolved_digest,
        validated_cross_binding_count=validated_cross,
        unresolved_cross_binding_count=unresolved_cross,
    )


def _validate_supplied_artifact_set_impl(
    items: object,
) -> CP65IndependentSuppliedValidationV1:
    normalized = _normalize_supplied_artifact_set(items)
    by_id = {}
    body_sha256s = []
    aggregate_nodes = 0
    aggregate_decoded_characters = 0
    for artifact_id, relative_path, payload in normalized:
        body_sha256, document = _validate_artifact_payload(
            artifact_id, relative_path, payload
        )
        if artifact_id == "frozen-machine-manifest":
            # The hash-pinned predecessor contains JSON null sentinels.  The
            # ordinary multi-artifact resource profile forbids null, so the
            # authoritative set pipeline also rejects this otherwise valid
            # immutable leaf before cross-binding work.
            raise ValueError(
                "frozen predecessor manifest is outside the artifact-set JSON profile"
            )
        if type(document) is dict:
            nodes, decoded_characters = _validate_json_resources(document)
            aggregate_nodes += nodes
            aggregate_decoded_characters += decoded_characters
            if aggregate_nodes > _MAX_SUPPLIED_ARTIFACT_SET_NODES:
                raise ValueError("supplied artifact set contains too many parsed nodes")
            if (
                aggregate_decoded_characters
                > _MAX_SUPPLIED_ARTIFACT_SET_DECODED_STRING_CHARACTERS
            ):
                raise ValueError(
                    "supplied artifact set contains too many decoded string characters"
                )
        body_sha256s.append(body_sha256)
        by_id.setdefault(artifact_id, []).append(
            (relative_path, payload, body_sha256, document)
        )
    for artifact_id, rows in by_id.items():
        maximum = 32 if _I_ARTIFACT_BY_ID[artifact_id][2] == "per-shard" else 1
        if len(rows) > maximum:
            raise ValueError("artifact multiplicity exceeds its schema bound")
    if (
        "launch-authorization" in by_id
        and "rejected-launch-authorization-candidate" in by_id
    ):
        raise ValueError(
            "final and rejected launch authorization aliases cannot coexist"
        )
    validated_cross, unresolved_cross = _validate_supplied_cross_bindings(by_id)
    (
        signature_applicable,
        signature_valid,
        signature_validated,
        signature_unresolved,
    ) = _validate_supplied_signature_aggregation(by_id)
    validated_cross += signature_validated
    unresolved_cross += signature_unresolved
    digest_counts = tuple(
        (
            artifact_id,
            path,
            *_intrinsic_digest_instance_counts(artifact_id, document),
        )
        for artifact_id, rows in by_id.items()
        for path, _payload, _body, document in rows
    )
    validated_digest = sum(row[2] for row in digest_counts)
    unresolved_digest = sum(row[3] for row in digest_counts)
    registry_count, resolved_targets = _validate_registry_target_bindings(by_id)
    validated_digest += registry_count
    if registry_count:
        unresolved_digest = max(0, unresolved_digest - registry_count)
        for target in set(resolved_targets):
            matching = tuple(row for row in digest_counts if (row[0], row[1]) == target)
            if len(matching) != 1:
                raise ValueError("registry resolved target worklist is ambiguous")
            unresolved_digest = max(0, unresolved_digest - matching[0][3])
    return _supplied_validation(
        tuple(row[0] for row in normalized),
        tuple(row[1] for row in normalized),
        tuple(row[2] for row in normalized),
        tuple(body_sha256s),
        signature_applicable=signature_applicable,
        signature_valid=signature_valid,
        validated_digest_preimage_count=validated_digest,
        unresolved_digest_preimage_count=unresolved_digest,
        validated_cross_binding_count=validated_cross,
        unresolved_cross_binding_count=unresolved_cross,
    )


def _verify_launch_authorization_signature_impl(
    receipt_payload: object, public_key_payload: object
) -> CP65IndependentSuppliedValidationV1:
    if type(receipt_payload) is not bytes or type(public_key_payload) is not bytes:
        raise TypeError("signature verifier inputs must be exact bytes")
    return _validate_supplied_artifact_set_impl(
        (
            ("launch-authorization", "launch_authorization.json", receipt_payload),
            (
                "launch-authority-public-key",
                "frozen_inputs/launch_authority_public_key.json",
                public_key_payload,
            ),
        )
    )


def cp65_independently_validate_supplied_artifact_bytes(
    artifact_id: object, relative_path: object, payload: object
) -> CP65IndependentSuppliedValidationV1:
    """Validate caller-supplied bytes without accepting production evidence."""

    try:
        return _validate_supplied_artifact_bytes_impl(
            artifact_id, relative_path, payload
        )
    except MemoryError as exc:
        raise ValueError(
            "caller-supplied artifact exceeded independent parser limits"
        ) from exc


def cp65_independently_validate_supplied_artifact_set(
    items: object,
) -> CP65IndependentSuppliedValidationV1:
    """Validate exact (artifact-id, relative-path, bytes) tuples."""

    try:
        return _validate_supplied_artifact_set_impl(items)
    except MemoryError as exc:
        raise ValueError(
            "caller-supplied artifact set exceeded independent parser limits"
        ) from exc


def cp65_independently_verify_launch_authorization_signature(
    receipt_payload: object, public_key_payload: object
) -> CP65IndependentSuppliedValidationV1:
    """Verify PSS mathematics without asserting authority or trust."""

    try:
        return _verify_launch_authorization_signature_impl(
            receipt_payload, public_key_payload
        )
    except MemoryError as exc:
        raise ValueError(
            "signature verifier exceeded independent parser limits"
        ) from exc


def cp65_independent_canonical_json_bytes(record: object) -> bytes:
    """Encode one exact, unchanged, independent CP65 record."""

    _validated, snapshot = _validate_public_record(record)
    return snapshot


def cp65_independent_sha256(record: object) -> str:
    """Hash one independent record with its exact public type tag."""

    validated, snapshot = _validate_public_record(record)
    return hashlib.sha256(
        b"cp65-independent-public-record-v1\0"
        + type(validated).__name__.encode("ascii")
        + b"\0"
        + snapshot
    ).hexdigest()


__all__ = (
    "CP65_TEST28_SCHEMA_VERSION",
    "CP65_TEST28_SCOPE",
    "CP65IndependentSuppliedValidationV1",
    "CP65IndependentProductionSchemaPreimageValidatorBundleV1",
    "cp65_independent_validator_bundle",
    "cp65_independently_validate_supplied_artifact_bytes",
    "cp65_independently_validate_supplied_artifact_set",
    "cp65_independently_verify_launch_authorization_signature",
    "cp65_independent_canonical_json_bytes",
    "cp65_independent_sha256",
)
