"""Independent verifier for portable predicate programs and formula cores.

This module implements the Checkpoint-56B verifier lane.  It deliberately
depends only on the verifier-side Checkpoint-56A envelope implementation and
the frozen verifier-side semantic core.  It validates static program
structure and exact formula projection; it does not resolve inputs or execute
constructors or predicates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Final, Optional

from heterodiff.data import (
    adapter_portable_predicate_language_core_verifier as _core,
)
from heterodiff.data import (
    adapter_portable_predicate_runtime_artifacts_verifier as _envelope,
)


__all__ = (
    "PortablePredicateProgramFormulaVerificationCode",
    "PortablePredicateProgramFormulaVerificationError",
    "VerifiedPortablePredicateProgramFormulaPairV1",
    "verify_portable_predicate_program_formula_pair_v1",
)


_VALIDATION_SCOPE_ID: Final = (
    "FULL_PROGRAM_FORMULA_STRUCTURE_AND_PROJECTION_ONLY_V1"
)
_DOMAIN_SEPARATED_SHA256: Final = "DOMAIN_SEPARATED_SHA256"
_PLAIN_SHA256: Final = "PLAIN_SHA256"
_STATIC_CONTRACT: Final = "STATIC_CONTRACT"
_INPUT_RESOLVED: Final = "INPUT_RESOLVED"
_PROGRAM_LITERAL: Final = "PROGRAM_LITERAL"
_DERIVED_TYPED_VALUE: Final = "DERIVED_TYPED_VALUE"
_APPLICABILITY_ID: Final = "ALWAYS"
_FAILURE_ORACLE_ID: Final = "FAIL_CLOSED_FOUR_DISPOSITION_V1"
_MAXIMUM_INTEGER_DIGITS: Final = 20
_MAXIMUM_PURPOSE_RELATION_COMPARISONS: Final = 1024 * 1024


class PortablePredicateProgramFormulaVerificationCode(str, Enum):
    """Closed Checkpoint-56B verifier failures."""

    INPUT_TYPE = "INPUT_TYPE"
    COMPILED_PROFILE_INVALID = "COMPILED_PROFILE_INVALID"
    PROGRAM_INPUT_RESOURCE = "PROGRAM_INPUT_RESOURCE"
    FORMULA_INPUT_RESOURCE = "FORMULA_INPUT_RESOURCE"
    ANCHOR_INPUT_RESOURCE = "ANCHOR_INPUT_RESOURCE"
    PROGRAM_JSON_INVALID = "PROGRAM_JSON_INVALID"
    PROGRAM_JSON_TREE_INVALID = "PROGRAM_JSON_TREE_INVALID"
    PROGRAM_CANONICAL_MISMATCH = "PROGRAM_CANONICAL_MISMATCH"
    FORMULA_JSON_INVALID = "FORMULA_JSON_INVALID"
    FORMULA_JSON_TREE_INVALID = "FORMULA_JSON_TREE_INVALID"
    FORMULA_CANONICAL_MISMATCH = "FORMULA_CANONICAL_MISMATCH"
    PROGRAM_ENVELOPE_INVALID = "PROGRAM_ENVELOPE_INVALID"
    PROGRAM_BINDING_MISMATCH = "PROGRAM_BINDING_MISMATCH"
    FORMULA_ENVELOPE_INVALID = "FORMULA_ENVELOPE_INVALID"
    FORMULA_BINDING_MISMATCH = "FORMULA_BINDING_MISMATCH"
    PURPOSE_BINDING_INVALID = "PURPOSE_BINDING_INVALID"
    ANCHOR_BUNDLE_INVALID = "ANCHOR_BUNDLE_INVALID"
    ANCHOR_JSON_INVALID = "ANCHOR_JSON_INVALID"
    ANCHOR_JSON_TREE_INVALID = "ANCHOR_JSON_TREE_INVALID"
    ANCHOR_CANONICAL_MISMATCH = "ANCHOR_CANONICAL_MISMATCH"
    ANCHOR_BINDING_MISMATCH = "ANCHOR_BINDING_MISMATCH"
    TYPE_REGISTRY_INVALID = "TYPE_REGISTRY_INVALID"
    OPERAND_REGISTRY_INVALID = "OPERAND_REGISTRY_INVALID"
    TYPED_PAYLOAD_INVALID = "TYPED_PAYLOAD_INVALID"
    LOCATOR_INVALID = "LOCATOR_INVALID"
    SHAPING_REGISTRY_INVALID = "SHAPING_REGISTRY_INVALID"
    PREDICATE_REGISTRY_INVALID = "PREDICATE_REGISTRY_INVALID"
    PROFILE_EXTENSION_INVALID = "PROFILE_EXTENSION_INVALID"
    TYPE_RELATION_INVALID = "TYPE_RELATION_INVALID"
    GRAPH_INVALID = "GRAPH_INVALID"
    PURPOSE_RELATION_UNSATISFIED = "PURPOSE_RELATION_UNSATISFIED"
    NONCLAIM_STATE_INVALID = "NONCLAIM_STATE_INVALID"
    FORMULA_PROJECTION_MISMATCH = "FORMULA_PROJECTION_MISMATCH"
    FORMULA_IDENTITY_MISMATCH = "FORMULA_IDENTITY_MISMATCH"
    INTERNAL = "INTERNAL"


_ERROR_MESSAGES: Final = {
    code: "portable predicate program verifier rejected the input: "
    + code.value.lower().replace("_", " ")
    for code in PortablePredicateProgramFormulaVerificationCode
}
_ERROR_MESSAGES[
    PortablePredicateProgramFormulaVerificationCode.INTERNAL
] = "portable predicate program verifier is internally inconsistent"


class PortablePredicateProgramFormulaVerificationError(ValueError):
    """One fixed-message verifier failure."""

    def __init__(
        self,
        code: PortablePredicateProgramFormulaVerificationCode,
    ):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


@dataclass(frozen=True)
class VerifiedPortablePredicateProgramFormulaPairV1:
    """Immutable result of complete static program/formula verification."""

    canonical_program_bytes: bytes = field(repr=False)
    canonical_formula_core_bytes: bytes = field(repr=False)
    canonical_purpose_binding_bytes: bytes = field(repr=False)
    program_identity_sha256: str
    formula_core_identity_sha256: str
    program_byte_count: int
    formula_core_byte_count: int
    program_artifact_type: str
    formula_core_artifact_type: str
    semantic_core_contract_sha256: str
    profile_contract_sha256: str
    profile_id: str
    program_id: str
    program_purpose_id: str
    ordered_type_ids: tuple
    ordered_operand_ids: tuple
    ordered_input_operand_ids: tuple
    ordered_derived_operand_ids: tuple
    ordered_shaping_node_ids: tuple
    ordered_predicate_node_ids: tuple
    root_node_id: str
    required_anchor_role_ids: tuple
    type_depth: int
    graph_depth: int
    node_reference_count: int
    validation_scope_id: str
    nested_program_semantics_validated: bool
    formula_projection_validated: bool
    evaluation_performed: bool


@dataclass(frozen=True)
class _TypeInfo:
    row: dict
    kind: str
    depth: int


@dataclass(frozen=True)
class _DecodedValue:
    kind: str
    value: object
    parts: tuple = ()


def _fail(code: PortablePredicateProgramFormulaVerificationCode) -> None:
    raise PortablePredicateProgramFormulaVerificationError(code) from None


def _identifier(value: object) -> bool:
    return _envelope._identifier(value)


def _sha256(value: object) -> bool:
    return _envelope._sha256(value)


def _exact_keys(value: object, keys: tuple) -> bool:
    return type(value) is dict and set(value) == set(keys)


def _unique_identifiers(
    value: object,
    *,
    nonempty: bool = True,
    maximum: Optional[int] = None,
) -> bool:
    return (
        type(value) is list
        and (bool(value) or not nonempty)
        and (maximum is None or len(value) <= maximum)
        and all(_identifier(item) for item in value)
        and len(value) == len(set(value))
    )


def _same_exact(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return set(left) == set(right) and all(
            _same_exact(left[key], right[key]) for key in left
        )
    if type(left) is list:
        return len(left) == len(right) and all(
            _same_exact(a, b) for a, b in zip(left, right)
        )
    return left == right


def _framed_digest(domain: str, payload: bytes) -> str:
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except (AttributeError, UnicodeError):
        _fail(PortablePredicateProgramFormulaVerificationCode.INTERNAL)
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _bounded_integer(value: str) -> int:
    if len(value.lstrip("-")) > _MAXIMUM_INTEGER_DIGITS:
        raise ValueError
    return int(value)


def _decode_canonical_json(
    raw: bytes,
    *,
    resource_code: PortablePredicateProgramFormulaVerificationCode,
    json_code: PortablePredicateProgramFormulaVerificationCode,
    tree_code: PortablePredicateProgramFormulaVerificationCode,
    canonical_code: PortablePredicateProgramFormulaVerificationCode,
) -> object:
    preflight = _envelope._preflight_json(raw)
    if preflight == "syntax-invalid":
        _fail(json_code)
    if preflight != "valid":
        _fail(resource_code)
    try:
        decoded = json.loads(
            raw.decode("ascii", "strict"),
            object_pairs_hook=_envelope._unique_object,
            parse_constant=_envelope._reject_constant,
            parse_float=_envelope._reject_float,
            parse_int=_bounded_integer,
        )
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _fail(json_code)
    status = _envelope._bounded_tree_status(decoded)
    if status == "resource-invalid":
        _fail(resource_code)
    if status != "valid":
        _fail(tree_code)
    try:
        canonical = _envelope._encode_canonical(decoded)
    except _envelope.PortablePredicateRuntimeEnvelopeVerificationError:
        _fail(PortablePredicateProgramFormulaVerificationCode.INTERNAL)
    if raw != canonical:
        _fail(canonical_code)
    return decoded


def _profile_tree(profile: object) -> dict:
    try:
        decoded = json.loads(
            profile.canonical_profile_bytes.decode("ascii", "strict")
        )
    except (AttributeError, UnicodeError, ValueError, TypeError):
        _fail(PortablePredicateProgramFormulaVerificationCode.INTERNAL)
    if type(decoded) is not dict:
        _fail(PortablePredicateProgramFormulaVerificationCode.INTERNAL)
    return decoded


def _binding_by_role(profile_tree: dict) -> dict:
    return {
        row["artifact_role_id"]: row
        for row in profile_tree["artifact_domain_rows"]
    }


def _profile_fields(profile_tree: dict) -> dict:
    return {
        row["field_id"]: row
        for row in profile_tree["profile_field_schema_rows"]
    }


def _field_value_schema_valid(
    schema_id: str,
    value: object,
    limits: dict,
) -> bool:
    if schema_id == "strict-identifier-string-v1":
        return _identifier(value)
    if schema_id == "lowercase-sha256-string-v1":
        return _sha256(value)
    if schema_id == "nonnegative-index-or-count-integer-v1":
        return (
            type(value) is int
            and 0 <= value <= limits["collection_items"]
        )
    if schema_id == "ordered-identifier-array-v1":
        return (
            type(value) is list
            and len(value) <= limits["collection_items"]
            and all(_identifier(item) for item in value)
        )
    if schema_id == "ordered-exact-object-row-array-v1":
        return (
            type(value) is list
            and len(value) <= limits["collection_items"]
            and all(type(item) is dict for item in value)
        )
    return False


def _ordered_required_anchor_roles(purpose: dict) -> tuple:
    ordered = []
    for relation in purpose["purpose_relation_rows"]:
        if relation["relation_primitive_id"] == (
            "exactly-one-pinned-anchor-row-canonical-equality-v1"
        ):
            role = relation["anchor_role_id"]
            if role not in ordered:
                ordered.append(role)
    return tuple(ordered)


def _validate_purpose_binding(
    program: dict,
    profile_tree: dict,
    limits: dict,
) -> tuple:
    matching = [
        row
        for row in profile_tree["program_purpose_rows"]
        if row["program_purpose_id"] == program["program_purpose_id"]
    ]
    if len(matching) != 1:
        _fail(
            PortablePredicateProgramFormulaVerificationCode.PURPOSE_BINDING_INVALID
        )
    purpose = matching[0]
    binding = program["purpose_binding"]
    if (
        type(binding) is not dict
        or set(binding) != set(purpose["exact_binding_field_ids"])
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode.PURPOSE_BINDING_INVALID
        )
    profile_fields = _profile_fields(profile_tree)
    domains = _binding_by_role(profile_tree)
    anchors = {
        row["anchor_role_id"]: row
        for row in profile_tree["anchor_contract_rows"]
    }
    for field_id in purpose["exact_binding_field_ids"]:
        schema = profile_fields.get(field_id)
        if (
            schema is None
            or not _field_value_schema_valid(
                schema["value_schema_id"],
                binding[field_id],
                limits,
            )
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .PURPOSE_BINDING_INVALID
            )
        value = binding[field_id]
        role = schema["semantic_role_id"]
        parameter = schema["role_parameter_id"]
        if role == "ordered-unique-identifiers":
            if len(value) != len(set(value)):
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .PURPOSE_BINDING_INVALID
                )
        elif role == "artifact-type-for-role":
            if parameter not in domains or value != domains[parameter][
                "artifact_type_id"
            ]:
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .PURPOSE_BINDING_INVALID
                )
        elif role == "artifact-identity-semantics-for-role":
            if parameter not in domains or value != domains[parameter][
                "identity_semantics_id"
            ]:
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .PURPOSE_BINDING_INVALID
                )
        elif role == "anchor-artifact-type-for-role":
            if parameter not in anchors or value != anchors[parameter][
                "artifact_type_id"
            ]:
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .PURPOSE_BINDING_INVALID
                )
        elif role == "anchor-contract-sha256-for-role":
            if parameter not in anchors or value != anchors[parameter][
                "contract_sha256"
            ]:
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .PURPOSE_BINDING_INVALID
                )
        elif role == "index-below-field":
            other = binding.get(parameter)
            if type(other) is not int or value >= other:
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .PURPOSE_BINDING_INVALID
                )
        elif role == "identifier-member-of-purpose-field":
            other = binding.get(parameter)
            if type(other) is not list or value not in other:
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .PURPOSE_BINDING_INVALID
                )
        elif role not in {
            "opaque-identifier",
            "artifact-identity-sha256-for-role",
            "nonnegative-count",
        }:
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .PURPOSE_BINDING_INVALID
            )
    try:
        canonical_binding = _envelope._encode_canonical(binding)
    except _envelope.PortablePredicateRuntimeEnvelopeVerificationError:
        _fail(PortablePredicateProgramFormulaVerificationCode.INTERNAL)
    return purpose, canonical_binding


def _validate_anchor_bundle(
    anchor_snapshot: tuple,
    required_roles: tuple,
    profile_tree: dict,
) -> dict:
    roles = tuple(row[0] for row in anchor_snapshot)
    if roles != required_roles or len(roles) != len(set(roles)):
        _fail(
            PortablePredicateProgramFormulaVerificationCode.ANCHOR_BUNDLE_INVALID
        )
    pinned = {
        row["anchor_role_id"]: row
        for row in profile_tree["anchor_contract_rows"]
    }
    decoded_by_role = {}
    for role, raw in anchor_snapshot:
        row = pinned.get(role)
        if row is None:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.ANCHOR_BUNDLE_INVALID
            )
        decoded = _decode_canonical_json(
            raw,
            resource_code=(
                PortablePredicateProgramFormulaVerificationCode.ANCHOR_INPUT_RESOURCE
            ),
            json_code=(
                PortablePredicateProgramFormulaVerificationCode.ANCHOR_JSON_INVALID
            ),
            tree_code=(
                PortablePredicateProgramFormulaVerificationCode.ANCHOR_JSON_TREE_INVALID
            ),
            canonical_code=(
                PortablePredicateProgramFormulaVerificationCode
                .ANCHOR_CANONICAL_MISMATCH
            ),
        )
        if (
            type(decoded) is not dict
            or not _identifier(decoded.get("artifact_type"))
            or decoded["artifact_type"] != row["artifact_type_id"]
            or _framed_digest(row["artifact_type_id"], raw)
            != row["contract_sha256"]
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode.ANCHOR_BINDING_MISMATCH
            )
        decoded_by_role[role] = decoded
    return decoded_by_role


def _type_row_primitive_valid(
    row: object,
    schemas: dict,
    limits: dict,
) -> bool:
    if type(row) is not dict:
        return False
    kind = row.get("type_kind_id")
    schema = schemas.get(kind) if _identifier(kind) else None
    if (
        schema is None
        or not _exact_keys(row, tuple(schema["exact_field_ids"]))
        or not _identifier(row.get("type_id"))
    ):
        return False
    if kind in {"boolean", "u64", "token", "octets"}:
        field_id = {
            "boolean": "proposition_domain_id",
            "u64": "unit_id",
            "token": "token_domain_id",
            "octets": "octet_domain_id",
        }[kind]
        return _identifier(row[field_id])
    if kind == "sha256":
        return (
            row["digest_semantics_id"] == _PLAIN_SHA256
            and type(row["digest_domain_id"]) is str
            and row["digest_domain_id"] == ""
        ) or (
            row["digest_semantics_id"] == _DOMAIN_SEPARATED_SHA256
            and _identifier(row["digest_domain_id"])
        )
    if kind in {"optional", "sequence"}:
        return _identifier(row["item_type_id"])
    if kind == "tuple":
        components = row["ordered_component_type_ids"]
        return (
            type(components) is list
            and 1 <= len(components) <= limits["tuple_components"]
            and all(_identifier(item) for item in components)
        )
    if kind == "keyed-table":
        indices = row["ordered_key_component_indices"]
        return (
            _identifier(row["row_tuple_type_id"])
            and _identifier(row["key_tuple_type_id"])
            and type(indices) is list
            and 1 <= len(indices) <= limits["selector_key_components"]
            and all(type(item) is int and item >= 0 for item in indices)
            and len(indices) == len(set(indices))
        )
    if kind == "u64-interval-sequence":
        return _identifier(row["endpoint_u64_type_id"])
    return False


def _validate_types(
    program: dict,
    core_tree: dict,
) -> tuple:
    limits = core_tree["resource_limits"]
    rows = program["ordered_type_rows"]
    schemas = {
        row["type_kind_id"]: row
        for row in core_tree["type_contract"]["type_kind_schema_rows"]
    }
    if (
        type(rows) is not list
        or len(rows) > limits["type_rows"]
        or any(type(row) is not dict for row in rows)
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode.TYPE_REGISTRY_INVALID
        )
    if any(
        not _type_row_primitive_valid(row, schemas, limits)
        for row in rows
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode.TYPE_REGISTRY_INVALID
        )
    declared_type_ids = [row["type_id"] for row in rows]
    if len(declared_type_ids) != len(set(declared_type_ids)):
        _fail(
            PortablePredicateProgramFormulaVerificationCode.TYPE_REGISTRY_INVALID
        )
    infos = {}
    ordered_ids = []
    maximum_depth = 0
    for row in rows:
        kind = row.get("type_kind_id")
        schema = schemas.get(kind) if type(kind) is str else None
        if (
            schema is None
            or not _exact_keys(row, tuple(schema["exact_field_ids"]))
            or not _identifier(row.get("type_id"))
            or not _identifier(kind)
            or row["type_id"] in infos
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode.TYPE_REGISTRY_INVALID
            )
        type_id = row["type_id"]
        if kind == "boolean":
            valid = _identifier(row["proposition_domain_id"])
            references = ()
        elif kind == "u64":
            valid = _identifier(row["unit_id"])
            references = ()
        elif kind == "token":
            valid = _identifier(row["token_domain_id"])
            references = ()
        elif kind == "octets":
            valid = _identifier(row["octet_domain_id"])
            references = ()
        elif kind == "sha256":
            semantics = row["digest_semantics_id"]
            domain = row["digest_domain_id"]
            valid = (
                semantics == _PLAIN_SHA256
                and type(domain) is str
                and domain == ""
            ) or (
                semantics == _DOMAIN_SEPARATED_SHA256
                and _identifier(domain)
            )
            references = ()
        elif kind in {"optional", "sequence"}:
            valid = _identifier(row["item_type_id"])
            references = (row["item_type_id"],)
        elif kind == "tuple":
            components = row["ordered_component_type_ids"]
            valid = (
                type(components) is list
                and 1 <= len(components) <= limits["tuple_components"]
                and all(_identifier(item) for item in components)
            )
            references = tuple(components) if valid else ()
        elif kind == "keyed-table":
            indices = row["ordered_key_component_indices"]
            valid = (
                _identifier(row["row_tuple_type_id"])
                and _identifier(row["key_tuple_type_id"])
                and type(indices) is list
                and 1 <= len(indices) <= limits["selector_key_components"]
                and all(type(item) is int and item >= 0 for item in indices)
                and len(indices) == len(set(indices))
            )
            references = (
                row["row_tuple_type_id"],
                row["key_tuple_type_id"],
            )
        elif kind == "u64-interval-sequence":
            valid = _identifier(row["endpoint_u64_type_id"])
            references = (row["endpoint_u64_type_id"],)
        else:
            valid = False
            references = ()
        if not valid or any(reference not in infos for reference in references):
            _fail(
                PortablePredicateProgramFormulaVerificationCode.TYPE_REGISTRY_INVALID
            )
        depth = 1 + max(
            (infos[reference].depth for reference in references),
            default=0,
        )
        if depth > limits["type_depth"]:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.TYPE_REGISTRY_INVALID
            )
        info = _TypeInfo(row=row, kind=kind, depth=depth)
        infos[type_id] = info
        ordered_ids.append(type_id)
        maximum_depth = max(maximum_depth, depth)
        if kind == "keyed-table":
            row_type = infos[row["row_tuple_type_id"]]
            key_type = infos[row["key_tuple_type_id"]]
            indices = row["ordered_key_component_indices"]
            if (
                row_type.kind != "tuple"
                or key_type.kind != "tuple"
                or any(
                    index >= len(
                        row_type.row["ordered_component_type_ids"]
                    )
                    for index in indices
                )
                or key_type.row["ordered_component_type_ids"]
                != [
                    row_type.row["ordered_component_type_ids"][index]
                    for index in indices
                ]
            ):
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .TYPE_REGISTRY_INVALID
                )
        if kind == "u64-interval-sequence":
            endpoint = infos[row["endpoint_u64_type_id"]]
            if endpoint.kind != "u64":
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .TYPE_REGISTRY_INVALID
                )
    return infos, tuple(ordered_ids), maximum_depth


def _validate_interval_refinements(
    types: dict,
    profile_tree: dict,
) -> None:
    refinements = profile_tree["interval_refinement_rows"]
    if not refinements:
        return
    parameter_values = {
        row["parameter_slot_id"]: row["parameter_value_id"]
        for row in profile_tree["profile_parameter_rows"]
    }
    admitted_units = {
        parameter_values[row["endpoint_parameter_slot_id"]]
        for row in refinements
    }
    for info in types.values():
        if info.kind != "u64-interval-sequence":
            continue
        endpoint = types[info.row["endpoint_u64_type_id"]]
        if endpoint.row["unit_id"] not in admitted_units:
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .PROFILE_EXTENSION_INVALID
            )


def _read_u64(payload: memoryview, offset: int) -> tuple:
    if offset + 8 > len(payload):
        raise ValueError
    return int.from_bytes(payload[offset : offset + 8], "big"), offset + 8


def _read_framed_parts(
    payload: memoryview,
    *,
    expected_count: Optional[int] = None,
    maximum_count: int,
) -> tuple:
    count, offset = _read_u64(payload, 0)
    if (
        count > maximum_count
        or (expected_count is not None and count != expected_count)
    ):
        raise ValueError
    parts = []
    for _ in range(count):
        length, offset = _read_u64(payload, offset)
        if length > len(payload) - offset:
            raise ValueError
        parts.append(payload[offset : offset + length])
        offset += length
    if offset != len(payload):
        raise ValueError
    return tuple(parts)


def _encode_framed_parts(parts: tuple) -> bytes:
    encoded = bytearray(len(parts).to_bytes(8, "big"))
    for part in parts:
        encoded.extend(len(part).to_bytes(8, "big"))
        encoded.extend(part)
    return bytes(encoded)


def _decode_typed_value(
    type_id: str,
    payload: bytes,
    types: dict,
    limits: dict,
) -> _DecodedValue:
    payload_view = memoryview(payload)
    if not payload_view.readonly:
        payload_view = payload_view.toreadonly()
    return _decode_typed_value_view(
        type_id,
        payload_view,
        types,
        limits,
    )


def _decode_typed_value_view(
    type_id: str,
    payload: memoryview,
    types: dict,
    limits: dict,
) -> _DecodedValue:
    if len(payload) > limits["typed_payload_bytes"]:
        raise ValueError
    info = types[type_id]
    kind = info.kind
    row = info.row
    if kind == "boolean":
        if payload not in (b"\x00", b"\x01"):
            raise ValueError
        return _DecodedValue(kind, payload == b"\x01")
    if kind == "u64":
        if len(payload) != 8:
            raise ValueError
        return _DecodedValue(kind, int.from_bytes(payload, "big"))
    if kind == "token":
        try:
            token = bytes(payload).decode("ascii", "strict")
        except UnicodeError as error:
            raise ValueError from error
        if not _identifier(token):
            raise ValueError
        return _DecodedValue(kind, token)
    if kind == "octets":
        if len(payload) > limits["octet_value_bytes"]:
            raise ValueError
        return _DecodedValue(kind, bytes(payload))
    if kind == "sha256":
        if len(payload) != 32:
            raise ValueError
        return _DecodedValue(kind, bytes(payload))
    if kind == "optional":
        if not payload:
            raise ValueError
        if payload[0] == 0:
            if len(payload) != 1:
                raise ValueError
            return _DecodedValue(kind, None)
        if payload[0] != 1:
            raise ValueError
        length, offset = _read_u64(payload, 1)
        if length != len(payload) - offset:
            raise ValueError
        child_raw = payload[offset:]
        child = _decode_typed_value_view(
            row["item_type_id"], child_raw, types, limits
        )
        return _DecodedValue(kind, child, ((child_raw, child),))
    if kind in {"sequence", "tuple", "keyed-table"}:
        expected = (
            len(row["ordered_component_type_ids"])
            if kind == "tuple"
            else None
        )
        parts = _read_framed_parts(
            payload,
            expected_count=expected,
            maximum_count=limits["collection_items"],
        )
        if kind == "sequence":
            child_type_ids = (row["item_type_id"],) * len(parts)
        elif kind == "tuple":
            child_type_ids = tuple(row["ordered_component_type_ids"])
        else:
            child_type_ids = (row["row_tuple_type_id"],) * len(parts)
        decoded_parts = tuple(
            (
                part,
                _decode_typed_value_view(
                    child_type,
                    part,
                    types,
                    limits,
                ),
            )
            for part, child_type in zip(parts, child_type_ids)
        )
        if kind == "keyed-table":
            keys = []
            table_indices = row["ordered_key_component_indices"]
            for _, decoded_row in decoded_parts:
                if decoded_row.kind != "tuple":
                    raise ValueError
                key_parts = tuple(
                    decoded_row.parts[index][0] for index in table_indices
                )
                keys.append(_encode_framed_parts(key_parts))
            if len(keys) != len(set(keys)):
                raise ValueError
        return _DecodedValue(kind, decoded_parts, decoded_parts)
    if kind == "u64-interval-sequence":
        count, offset = _read_u64(payload, 0)
        if count > limits["collection_items"]:
            raise ValueError
        intervals = []
        for _ in range(count):
            start_length, offset = _read_u64(payload, offset)
            if start_length > len(payload) - offset:
                raise ValueError
            start_raw = payload[offset : offset + start_length]
            offset += start_length
            end_length, offset = _read_u64(payload, offset)
            if end_length > len(payload) - offset:
                raise ValueError
            end_raw = payload[offset : offset + end_length]
            offset += end_length
            start = _decode_typed_value_view(
                row["endpoint_u64_type_id"], start_raw, types, limits
            )
            end = _decode_typed_value_view(
                row["endpoint_u64_type_id"], end_raw, types, limits
            )
            if start.value > end.value:
                raise ValueError
            intervals.append(((start_raw, start), (end_raw, end)))
        if offset != len(payload):
            raise ValueError
        return _DecodedValue(kind, tuple(intervals))
    raise ValueError


def _validate_operand_registry(
    program: dict,
    types: dict,
    profile_tree: dict,
    limits: dict,
) -> tuple:
    rows = program["ordered_operand_rows"]
    exact_fields = (
        "operand_id",
        "type_id",
        "value_source_kind_id",
        "resolution_requirement_id",
        "ordered_authority_class_ids",
        "locator",
        "literal_value_bytes_hex",
        "source_shaping_node_id",
    )
    if (
        type(rows) is not list
        or len(rows) > limits["operand_rows"]
        or any(type(row) is not dict for row in rows)
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode.OPERAND_REGISTRY_INVALID
        )
    declared_authorities = profile_tree["authority_class_ids"]
    declared_authority_set = set(declared_authorities)
    for row in rows:
        if (
            not _exact_keys(row, exact_fields)
            or not _identifier(row.get("operand_id"))
            or not _identifier(row.get("type_id"))
            or not _identifier(row.get("value_source_kind_id"))
            or not _identifier(row.get("resolution_requirement_id"))
            or not _unique_identifiers(
                row.get("ordered_authority_class_ids"),
                nonempty=False,
                maximum=len(declared_authorities),
            )
            or type(row.get("locator")) is not dict
            or type(row.get("literal_value_bytes_hex")) is not str
            or not _envelope._empty_or_identifier(
                row.get("source_shaping_node_id")
            )
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .OPERAND_REGISTRY_INVALID
            )
    declared_ids = [row["operand_id"] for row in rows]
    if len(declared_ids) != len(set(declared_ids)):
        _fail(
            PortablePredicateProgramFormulaVerificationCode
            .OPERAND_REGISTRY_INVALID
        )
    by_id = {}
    ordered_ids = []
    input_ids = []
    derived_ids = []
    for index, row in enumerate(rows):
        if (
            row["type_id"] not in types
            or not set(row["ordered_authority_class_ids"]).issubset(
                declared_authority_set
            )
            or row["ordered_authority_class_ids"]
            != [
                authority
                for authority in declared_authorities
                if authority in set(row["ordered_authority_class_ids"])
            ]
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode.OPERAND_REGISTRY_INVALID
            )
        source = row["value_source_kind_id"]
        if source == _INPUT_RESOLVED:
            valid = (
                row["resolution_requirement_id"]
                in {
                    "REQUIRED_RUNTIME_FAIL",
                    "REQUIRED_EXTERNAL_NOT_EVALUATED",
                }
                and bool(row["ordered_authority_class_ids"])
                and bool(row["locator"])
                and row["literal_value_bytes_hex"] == ""
                and row["source_shaping_node_id"] == ""
            )
            input_ids.append(row["operand_id"])
        elif source == _PROGRAM_LITERAL:
            valid = (
                row["resolution_requirement_id"] == _STATIC_CONTRACT
                and row["ordered_authority_class_ids"] == []
                and row["locator"] == {}
                and row["source_shaping_node_id"] == ""
            )
        elif source == _DERIVED_TYPED_VALUE:
            valid = (
                row["resolution_requirement_id"] == _STATIC_CONTRACT
                and row["locator"] == {}
                and row["literal_value_bytes_hex"] == ""
                and _identifier(row["source_shaping_node_id"])
            )
            derived_ids.append(row["operand_id"])
        else:
            valid = False
        if not valid:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.OPERAND_REGISTRY_INVALID
            )
        by_id[row["operand_id"]] = (index, row)
        ordered_ids.append(row["operand_id"])
    return (
        rows,
        by_id,
        tuple(ordered_ids),
        tuple(input_ids),
        tuple(derived_ids),
    )


def _validate_program_literals(
    operand_rows: list,
    types: dict,
    limits: dict,
) -> dict:
    decoded = {}
    for row in operand_rows:
        if row["value_source_kind_id"] != _PROGRAM_LITERAL:
            continue
        if not _envelope._payload_hex(
            row["literal_value_bytes_hex"]
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .TYPED_PAYLOAD_INVALID
            )
        try:
            payload = bytes.fromhex(row["literal_value_bytes_hex"])
            decoded[row["operand_id"]] = _decode_typed_value(
                row["type_id"], payload, types, limits
            )
        except (ValueError, OverflowError):
            _fail(
                PortablePredicateProgramFormulaVerificationCode.TYPED_PAYLOAD_INVALID
            )
    return decoded


def _validate_typed_key_rows(
    value: object,
    types: dict,
    limits: dict,
) -> tuple:
    exact_fields = (
        "key_field_id",
        "key_type_id",
        "key_value_bytes_hex",
    )
    if (
        type(value) is not list
        or not 1 <= len(value) <= limits["selector_key_components"]
        or any(
            not _exact_keys(row, exact_fields)
            or not _identifier(row.get("key_field_id"))
            or not _identifier(row.get("key_type_id"))
            or row["key_type_id"] not in types
            or not _envelope._payload_hex(row.get("key_value_bytes_hex"))
            for row in value
        )
    ):
        _fail(PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID)
    decoded = []
    for row in value:
        try:
            payload = bytes.fromhex(row["key_value_bytes_hex"])
            decoded.append(
                _decode_typed_value(
                    row["key_type_id"], payload, types, limits
                )
            )
        except (ValueError, OverflowError):
            _fail(PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID)
    return tuple(decoded)


def _validate_path_segments(
    value: object,
    types: dict,
    limits: dict,
    *,
    nonempty: bool,
) -> None:
    if (
        type(value) is not list
        or (nonempty and not value)
        or len(value) > limits["locator_segments"]
    ):
        _fail(PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID)
    for segment in value:
        if type(segment) is not dict:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
            )
        kind = segment.get("segment_kind_id")
        if kind == "object-key":
            if (
                not _exact_keys(
                    segment, ("segment_kind_id", "object_key")
                )
                or not _identifier(segment["object_key"])
            ):
                _fail(
                    PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
                )
        elif kind == "list-index":
            if (
                not _exact_keys(
                    segment,
                    (
                        "segment_kind_id",
                        "list_index",
                        "expected_list_count",
                        "list_order_contract_sha256",
                    ),
                )
                or type(segment["list_index"]) is not int
                or type(segment["expected_list_count"]) is not int
                or not 0 <= segment["list_index"]
                < segment["expected_list_count"]
                <= limits["collection_items"]
                or not _sha256(segment["list_order_contract_sha256"])
            ):
                _fail(
                    PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
                )
        elif kind == "declared-keyed-list-item":
            if not _exact_keys(
                segment,
                ("segment_kind_id", "ordered_key_component_rows"),
            ):
                _fail(
                    PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
                )
            _validate_typed_key_rows(
                segment["ordered_key_component_rows"], types, limits
            )
        else:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
            )


def _select_locator_extension(
    locator: dict,
    profile_tree: dict,
) -> dict:
    candidates = [
        row
        for row in profile_tree["locator_extension_rows"]
        if set(row["exact_configuration_field_ids"]) == set(locator)
    ]
    profile_fields = _profile_fields(profile_tree)
    selected = []
    for row in candidates:
        discriminator_fields = [
            field_id
            for field_id in row["exact_configuration_field_ids"]
            if profile_fields[field_id]["semantic_role_id"]
            == "locator-kind-self"
        ]
        if not discriminator_fields or all(
            locator[field_id] == row["locator_kind_id"]
            for field_id in discriminator_fields
        ):
            selected.append(row)
    if len(selected) != 1:
        _fail(PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID)
    return selected[0]


def _validate_locator_field_binding(
    field_id: str,
    value: object,
    locator: dict,
    extension: dict,
    purpose_binding: dict,
    profile_tree: dict,
    types: dict,
    operands: dict,
    operand_index: int,
    limits: dict,
) -> None:
    schema = _profile_fields(profile_tree)[field_id]
    if not _field_value_schema_valid(
        schema["value_schema_id"], value, limits
    ):
        _fail(PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID)
    role = schema["semantic_role_id"]
    parameter = schema["role_parameter_id"]
    domains = _binding_by_role(profile_tree)
    anchors = {
        row["anchor_role_id"]: row
        for row in profile_tree["anchor_contract_rows"]
    }
    if role == "opaque-identifier":
        return
    if role == "artifact-type-for-role":
        if parameter not in domains or value != domains[parameter][
            "artifact_type_id"
        ]:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
            )
        return
    if role == "artifact-identity-semantics-for-role":
        if parameter not in domains or value != domains[parameter][
            "identity_semantics_id"
        ]:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
            )
        return
    if role == "artifact-identity-sha256-for-role":
        return
    if role == "anchor-artifact-type-for-role":
        if parameter not in anchors or value != anchors[parameter][
            "artifact_type_id"
        ]:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
            )
        return
    if role == "anchor-contract-sha256-for-role":
        if parameter not in anchors or value != anchors[parameter][
            "contract_sha256"
        ]:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
            )
        return
    if role == "identifier-member-of-purpose-field":
        target = purpose_binding.get(parameter)
        if type(target) is not list or value not in target:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
            )
        return
    if role == "locator-kind-self":
        if value != extension["locator_kind_id"]:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
            )
        return
    if role == "path-segments":
        _validate_path_segments(
            value,
            types,
            limits,
            nonempty=(
                field_id
                not in extension["exact_empty_placeholder_field_ids"]
            ),
        )
        return
    if role == "nonnegative-count":
        return
    if role == "index-below-field":
        count = locator.get(parameter)
        if type(count) is not int or value >= count:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
            )
        return
    if role == "typed-key-components":
        _validate_typed_key_rows(value, types, limits)
        return
    if role == "prior-input-resolved-operand":
        target = operands.get(value)
        if (
            target is None
            or target[0] >= operand_index
            or target[1]["value_source_kind_id"] != _INPUT_RESOLVED
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
            )
        return
    _fail(PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID)


def _validate_locators(
    operand_rows: list,
    operands: dict,
    purpose_binding: dict,
    profile_tree: dict,
    types: dict,
    limits: dict,
) -> dict:
    extension_by_operand = {}
    for operand_index, operand in enumerate(operand_rows):
        if operand["value_source_kind_id"] != _INPUT_RESOLVED:
            continue
        locator = operand["locator"]
        extension = _select_locator_extension(locator, profile_tree)
        for field_id in extension["exact_configuration_field_ids"]:
            _validate_locator_field_binding(
                field_id,
                locator[field_id],
                locator,
                extension,
                purpose_binding,
                profile_tree,
                types,
                operands,
                operand_index,
                limits,
            )
        for field_id in extension["exact_empty_placeholder_field_ids"]:
            if locator[field_id] != []:
                _fail(
                    PortablePredicateProgramFormulaVerificationCode.LOCATOR_INVALID
                )
        primitive = extension["locator_primitive_id"]
        if primitive not in {
            "bounded-artifact-path",
            "direct-bound-value",
            "ordered-index",
            "composite-key",
            "sibling-resolved-value",
        }:
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .PROFILE_EXTENSION_INVALID
            )
        extension_by_operand[operand["operand_id"]] = extension
    return extension_by_operand


def _constructor_relation_valid(
    constructor_id: str,
    output_type_id: str,
    input_type_ids: list,
    configuration: dict,
    types: dict,
) -> bool:
    output = types[output_type_id]
    inputs = [types[type_id] for type_id in input_type_ids]
    if constructor_id == "make-optional-none":
        return output.kind == "optional" and not inputs
    if constructor_id == "make-optional-some":
        return (
            output.kind == "optional"
            and len(inputs) == 1
            and output.row["item_type_id"] == input_type_ids[0]
        )
    if constructor_id == "require-optional-present":
        return (
            len(inputs) == 1
            and inputs[0].kind == "optional"
            and inputs[0].row["item_type_id"] == output_type_id
        )
    if constructor_id == "make-sequence":
        return output.kind == "sequence" and all(
            type_id == output.row["item_type_id"]
            for type_id in input_type_ids
        )
    if constructor_id == "make-tuple":
        return (
            output.kind == "tuple"
            and output.row["ordered_component_type_ids"] == input_type_ids
        )
    if constructor_id == "make-keyed-table":
        return output.kind == "keyed-table" and all(
            type_id == output.row["row_tuple_type_id"]
            for type_id in input_type_ids
        )
    if constructor_id == "make-u64-interval-sequence":
        return (
            output.kind == "u64-interval-sequence"
            and len(inputs) % 2 == 0
            and all(
                type_id == output.row["endpoint_u64_type_id"]
                for type_id in input_type_ids
            )
        )
    if constructor_id == "project-tuple-component":
        if len(inputs) != 1 or inputs[0].kind != "tuple":
            return False
        index = configuration["component_index"]
        return (
            index < len(inputs[0].row["ordered_component_type_ids"])
            and output_type_id
            == inputs[0].row["ordered_component_type_ids"][index]
        )
    if constructor_id == "project-keyed-table-column":
        if len(inputs) != 1 or inputs[0].kind != "keyed-table":
            return False
        row_type = types[inputs[0].row["row_tuple_type_id"]]
        index = configuration["component_index"]
        return (
            index < len(row_type.row["ordered_component_type_ids"])
            and output.kind == "sequence"
            and output.row["item_type_id"]
            == row_type.row["ordered_component_type_ids"][index]
        )
    if constructor_id == "project-keyed-table-keys":
        return (
            len(inputs) == 1
            and inputs[0].kind == "keyed-table"
            and output.kind == "sequence"
            and output.row["item_type_id"]
            == inputs[0].row["key_tuple_type_id"]
        )
    if constructor_id == "select-keyed-table-row":
        return (
            len(inputs) == 2
            and inputs[0].kind == "keyed-table"
            and input_type_ids[1] == inputs[0].row["key_tuple_type_id"]
            and output_type_id == inputs[0].row["row_tuple_type_id"]
        )
    if constructor_id == "canonical-sort-keyed-table":
        return (
            len(inputs) == 1
            and inputs[0].kind == "keyed-table"
            and output_type_id == input_type_ids[0]
        )
    return False


def _validate_shaping_nodes(
    program: dict,
    operands: dict,
    types: dict,
    profile_tree: dict,
    core_tree: dict,
) -> tuple:
    limits = core_tree["resource_limits"]
    rows = program["ordered_shaping_node_rows"]
    exact_fields = tuple(
        core_tree["program_contract"]["shaping_node_exact_field_ids"]
    )
    constructors = {
        row["constructor_id"]: row
        for row in core_tree["constructor_contract"]["constructor_rows"]
    }
    if (
        type(rows) is not list
        or len(rows) > limits["shaping_nodes"]
        or any(type(row) is not dict for row in rows)
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode.SHAPING_REGISTRY_INVALID
        )
    for row in rows:
        if (
            not _exact_keys(row, exact_fields)
            or not _identifier(row.get("shaping_node_id"))
            or not _identifier(row.get("constructor_id"))
            or not _identifier(row.get("output_operand_id"))
            or type(row.get("ordered_input_operand_ids")) is not list
            or len(row["ordered_input_operand_ids"])
            > limits["node_fanout"]
            or any(
                not _identifier(item)
                for item in row["ordered_input_operand_ids"]
            )
            or type(row.get("constructor_configuration")) is not dict
            or not _identifier(row.get("applicability_id"))
            or not _identifier(row.get("failure_oracle_id"))
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .SHAPING_REGISTRY_INVALID
            )
    declared_node_ids = [row["shaping_node_id"] for row in rows]
    if len(declared_node_ids) != len(set(declared_node_ids)):
        _fail(
            PortablePredicateProgramFormulaVerificationCode
            .SHAPING_REGISTRY_INVALID
        )
    if any(
        row["constructor_id"] not in constructors
        or row["applicability_id"] != _APPLICABILITY_ID
        or row["failure_oracle_id"] != _FAILURE_ORACLE_ID
        for row in rows
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode
            .SHAPING_REGISTRY_INVALID
        )
    derived_ids = {
        operand_id
        for operand_id, (_, operand) in operands.items()
        if operand["value_source_kind_id"] == _DERIVED_TYPED_VALUE
    }
    validated_outputs = set()
    validated_nodes = set()
    for row in rows:
        output_id = row["output_operand_id"]
        inputs = row["ordered_input_operand_ids"]
        output = operands.get(output_id)
        constructor = constructors[row["constructor_id"]]
        if (
            output is None
            or output[1]["value_source_kind_id"] != _DERIVED_TYPED_VALUE
            or output[1]["source_shaping_node_id"]
            != row["shaping_node_id"]
            or output_id in validated_outputs
            or any(operand_id not in operands for operand_id in inputs)
            or not constructor["minimum_input_count"]
            <= len(inputs)
            <= constructor["maximum_input_count"]
            or any(
                operands[operand_id][0] >= output[0]
                for operand_id in inputs
            )
            or any(
                operands[operand_id][1]["value_source_kind_id"]
                == _DERIVED_TYPED_VALUE
                and operands[operand_id][1]["source_shaping_node_id"]
                not in validated_nodes
                for operand_id in inputs
            )
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .SHAPING_REGISTRY_INVALID
            )
        validated_outputs.add(output_id)
        validated_nodes.add(row["shaping_node_id"])
    if validated_outputs != derived_ids:
        _fail(
            PortablePredicateProgramFormulaVerificationCode
            .SHAPING_REGISTRY_INVALID
        )
    declared_authorities = profile_tree["authority_class_ids"]
    prepass_authorities = {
        operand_id: set(operand["ordered_authority_class_ids"])
        for operand_id, (_, operand) in operands.items()
        if operand["value_source_kind_id"] != _DERIVED_TYPED_VALUE
    }
    for row in rows:
        inputs = row["ordered_input_operand_ids"]
        transitive_authorities = set().union(
            *(prepass_authorities[operand_id] for operand_id in inputs)
        ) if inputs else set()
        expected_authorities = [
            authority
            for authority in declared_authorities
            if authority in transitive_authorities
        ]
        output_id = row["output_operand_id"]
        if (
            operands[output_id][1]["ordered_authority_class_ids"]
            != expected_authorities
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .OPERAND_REGISTRY_INVALID
            )
        prepass_authorities[output_id] = transitive_authorities
    by_id = {}
    producer_by_output = {}
    authority_sets = {}
    for operand_id, (_, operand) in operands.items():
        if operand["value_source_kind_id"] == _INPUT_RESOLVED:
            authority_sets[operand_id] = set(
                operand["ordered_authority_class_ids"]
            )
        elif operand["value_source_kind_id"] == _PROGRAM_LITERAL:
            authority_sets[operand_id] = set()
    for index, row in enumerate(rows):
        constructor_id = row.get("constructor_id")
        constructor = (
            constructors.get(constructor_id)
            if type(constructor_id) is str
            else None
        )
        if constructor is None:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.SHAPING_REGISTRY_INVALID
            )
        inputs = row["ordered_input_operand_ids"]
        if not (
            constructor["minimum_input_count"]
            <= len(inputs)
            <= constructor["maximum_input_count"]
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode.SHAPING_REGISTRY_INVALID
            )
        expected_configuration = set(
            constructor["exact_configuration_field_ids"]
        )
        configuration = row["constructor_configuration"]
        if set(configuration) != expected_configuration:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.TYPE_RELATION_INVALID
            )
        if any(
            type(configuration[field_id]) is not int
            or configuration[field_id] < 0
            for field_id in expected_configuration
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode.TYPE_RELATION_INVALID
            )
        output = operands.get(row["output_operand_id"])
        if (
            output is None
            or output[1]["value_source_kind_id"] != _DERIVED_TYPED_VALUE
            or output[1]["source_shaping_node_id"]
            != row["shaping_node_id"]
            or row["output_operand_id"] in producer_by_output
            or any(operand_id not in operands for operand_id in inputs)
            or any(
                operands[operand_id][0] >= output[0]
                for operand_id in inputs
            )
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode.SHAPING_REGISTRY_INVALID
            )
        for operand_id in inputs:
            source = operands[operand_id][1]
            if (
                source["value_source_kind_id"] == _DERIVED_TYPED_VALUE
                and source["source_shaping_node_id"] not in by_id
            ):
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .SHAPING_REGISTRY_INVALID
                )
        transitive_authorities = set().union(
            *(authority_sets[operand_id] for operand_id in inputs)
        ) if inputs else set()
        expected_authorities = [
            authority
            for authority in declared_authorities
            if authority in transitive_authorities
        ]
        if output[1]["ordered_authority_class_ids"] != expected_authorities:
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .OPERAND_REGISTRY_INVALID
            )
        input_type_ids = [
            operands[operand_id][1]["type_id"] for operand_id in inputs
        ]
        if not _constructor_relation_valid(
            constructor_id,
            output[1]["type_id"],
            input_type_ids,
            configuration,
            types,
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode.TYPE_RELATION_INVALID
            )
        authority_sets[row["output_operand_id"]] = transitive_authorities
        by_id[row["shaping_node_id"]] = (index, row)
        producer_by_output[row["output_operand_id"]] = row["shaping_node_id"]
    if set(producer_by_output) != derived_ids:
        _fail(
            PortablePredicateProgramFormulaVerificationCode.SHAPING_REGISTRY_INVALID
        )
    return rows, by_id, tuple(row["shaping_node_id"] for row in rows)


def _literal_sequence_is_unique_nonempty(
    operand_id: str,
    operands: dict,
    decoded_literals: dict,
) -> bool:
    operand = operands[operand_id][1]
    decoded = decoded_literals.get(operand_id)
    if (
        operand["value_source_kind_id"] != _PROGRAM_LITERAL
        or decoded is None
        or decoded.kind != "sequence"
        or not decoded.parts
    ):
        return False
    raw_items = [part[0] for part in decoded.parts]
    return len(raw_items) == len(set(raw_items))


def _core_operator_relation_valid(
    operator_id: str,
    operand_ids: list,
    child_ids: list,
    configuration: dict,
    operands: dict,
    types: dict,
    decoded_literals: dict,
) -> bool:
    type_ids = [operands[operand_id][1]["type_id"] for operand_id in operand_ids]
    infos = [types[type_id] for type_id in type_ids]
    if operator_id in {"all", "any"}:
        return not operand_ids and bool(child_ids)
    if operator_id == "not":
        return not operand_ids and len(child_ids) == 1
    if operator_id == "absence":
        return len(infos) == 1 and infos[0].kind == "optional"
    if operator_id == "all-distinct":
        return len(infos) == 1 and infos[0].kind == "sequence"
    exact_kind_by_operator = {
        "boolean-is": "boolean",
        "u64-equal": "u64",
        "token-equal": "token",
        "octets-equal": "octets",
        "sha256-equal": "sha256",
    }
    if operator_id in exact_kind_by_operator:
        return (
            len(infos) == 2
            and type_ids[0] == type_ids[1]
            and infos[0].kind == exact_kind_by_operator[operator_id]
        )
    if operator_id == "ordered-sequence-equal":
        return (
            len(infos) == 2
            and type_ids[0] == type_ids[1]
            and infos[0].kind in {"sequence", "keyed-table"}
        )
    if operator_id in {"set-equal", "set-subset"}:
        return (
            len(infos) == 2
            and infos[0].kind == "sequence"
            and infos[1].kind == "sequence"
            and infos[0].row["item_type_id"]
            == infos[1].row["item_type_id"]
        )
    if operator_id == "count-equal":
        return (
            len(infos) == 2
            and infos[0].kind in {"sequence", "keyed-table"}
            and infos[1].kind == "u64"
            and infos[1].row["unit_id"] == "collection-item-count"
        )
    if operator_id == "digest-derived-from-bytes":
        return (
            len(infos) == 2
            and infos[0].kind == "octets"
            and infos[1].kind == "sha256"
            and infos[1].row["digest_semantics_id"] == _PLAIN_SHA256
        )
    if operator_id == "domain-digest-derived-from-bytes":
        return (
            len(infos) == 2
            and infos[0].kind == "octets"
            and infos[1].kind == "sha256"
            and infos[1].row["digest_semantics_id"]
            == _DOMAIN_SEPARATED_SHA256
        )
    if operator_id == "integer-sum-equal":
        return (
            len(infos) == 2
            and infos[0].kind == "sequence"
            and infos[1].kind == "u64"
            and infos[0].row["item_type_id"] == type_ids[1]
        )
    if operator_id == "interval-order":
        return (
            len(infos) == 1
            and infos[0].kind == "u64-interval-sequence"
            and configuration.get("interval_order_mode_id")
            in {"TOUCHING_ADMITTED", "STRICTLY_SEPARATED"}
        )
    if operator_id == "reference-resolves":
        return (
            len(infos) == 2
            and infos[0].kind == "sequence"
            and infos[1].kind == "keyed-table"
            and infos[0].row["item_type_id"]
            == infos[1].row["key_tuple_type_id"]
        )
    if operator_id == "member-of-frozen-program-set":
        return (
            len(infos) == 2
            and infos[1].kind == "sequence"
            and infos[1].row["item_type_id"] == type_ids[0]
            and _literal_sequence_is_unique_nonempty(
                operand_ids[1], operands, decoded_literals
            )
        )
    return False


def _profile_membership_relation_valid(
    specialization: dict,
    operand_ids: list,
    operands: dict,
    types: dict,
    decoded_literals: dict,
    profile_tree: dict,
) -> bool:
    if len(operand_ids) != 2:
        return False
    first_type_id = operands[operand_ids[0]][1]["type_id"]
    second_type_id = operands[operand_ids[1]][1]["type_id"]
    first = types[first_type_id]
    second = types[second_type_id]
    if (
        second.kind != "sequence"
        or second.row["item_type_id"] != first_type_id
        or not _literal_sequence_is_unique_nonempty(
            operand_ids[1], operands, decoded_literals
        )
    ):
        return False
    parameters = {
        row["parameter_slot_id"]: row["parameter_value_id"]
        for row in profile_tree["profile_parameter_rows"]
    }
    expected_domains = [
        parameters[slot_id]
        for slot_id in specialization["ordered_parameter_slot_ids"]
    ]
    if len(expected_domains) == 1:
        return (
            first.kind == "token"
            and first.row["token_domain_id"] == expected_domains[0]
        )
    if (
        first.kind != "tuple"
        or len(first.row["ordered_component_type_ids"])
        != len(expected_domains)
    ):
        return False
    component_infos = [
        types[type_id]
        for type_id in first.row["ordered_component_type_ids"]
    ]
    return all(
        info.kind == "token"
        and info.row["token_domain_id"] == expected
        for info, expected in zip(component_infos, expected_domains)
    )


def _validate_predicate_nodes(
    program: dict,
    operands: dict,
    shaping_nodes: dict,
    types: dict,
    decoded_literals: dict,
    profile_tree: dict,
    core_tree: dict,
) -> tuple:
    limits = core_tree["resource_limits"]
    rows = program["ordered_predicate_node_rows"]
    exact_fields = tuple(
        core_tree["program_contract"]["node_exact_field_ids"]
    )
    core_operators = {
        row["operator_id"]: row
        for row in core_tree["operator_contract"]["operator_rows"]
    }
    specializations = {
        row["exposed_operator_id"]: row
        for row in profile_tree["operator_specialization_rows"]
    }
    if (
        type(rows) is not list
        or not 1 <= len(rows) <= limits["predicate_nodes"]
        or any(type(row) is not dict for row in rows)
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode.PREDICATE_REGISTRY_INVALID
        )
    for row in rows:
        operand_ids = row.get("ordered_operand_ids")
        child_ids = row.get("ordered_child_node_ids")
        if (
            not _exact_keys(row, exact_fields)
            or not _identifier(row.get("node_id"))
            or not _identifier(row.get("operator_id"))
            or type(operand_ids) is not list
            or type(child_ids) is not list
            or len(operand_ids) > limits["node_fanout"]
            or len(child_ids) > limits["node_fanout"]
            or any(not _identifier(item) for item in operand_ids)
            or any(not _identifier(item) for item in child_ids)
            or type(row.get("operator_configuration")) is not dict
            or not _identifier(row.get("applicability_id"))
            or not _identifier(row.get("failure_oracle_id"))
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .PREDICATE_REGISTRY_INVALID
            )
    declared_node_ids = [row["node_id"] for row in rows]
    if (
        len(declared_node_ids) != len(set(declared_node_ids))
        or set(declared_node_ids).intersection(shaping_nodes)
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode
            .PREDICATE_REGISTRY_INVALID
        )
    for row in rows:
        operator_id = row["operator_id"]
        core_operator = core_operators.get(operator_id)
        specialization = specializations.get(operator_id)
        operator_schema = (
            core_operator
            if core_operator is not None
            else core_operators.get("member-of-frozen-program-set")
            if specialization is not None
            else None
        )
        if (
            operator_schema is None
            or row["applicability_id"] != _APPLICABILITY_ID
            or row["failure_oracle_id"] != _FAILURE_ORACLE_ID
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .PREDICATE_REGISTRY_INVALID
            )
    validated_predicates = set()
    for row in rows:
        operator_id = row["operator_id"]
        core_operator = core_operators.get(operator_id)
        specialization = specializations.get(operator_id)
        operator_schema = (
            core_operator
            if core_operator is not None
            else core_operators["member-of-frozen-program-set"]
        )
        operand_ids = row["ordered_operand_ids"]
        child_ids = row["ordered_child_node_ids"]
        if (
            not _unique_identifiers(
                operand_ids,
                nonempty=False,
                maximum=limits["node_fanout"],
            )
            or not _unique_identifiers(
                child_ids,
                nonempty=False,
                maximum=limits["node_fanout"],
            )
            or not operator_schema["minimum_operand_count"]
            <= len(operand_ids)
            <= operator_schema["maximum_operand_count"]
            or not operator_schema["minimum_child_count"]
            <= len(child_ids)
            <= operator_schema["maximum_child_count"]
            or any(operand_id not in operands for operand_id in operand_ids)
            or any(
                child_id not in validated_predicates
                for child_id in child_ids
            )
            or len(operand_ids) + len(child_ids) > limits["node_fanout"]
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .PREDICATE_REGISTRY_INVALID
            )
        validated_predicates.add(row["node_id"])
    by_id = {}
    for index, row in enumerate(rows):
        operator_id = row.get("operator_id")
        core_operator = (
            core_operators.get(operator_id)
            if type(operator_id) is str
            else None
        )
        specialization = (
            specializations.get(operator_id)
            if type(operator_id) is str
            else None
        )
        operator_schema = (
            core_operator
            if core_operator is not None
            else core_operators.get("member-of-frozen-program-set")
            if specialization is not None
            else None
        )
        if (
            operator_schema is None
            or not _unique_identifiers(
                row.get("ordered_operand_ids"),
                nonempty=False,
                maximum=limits["node_fanout"],
            )
            or not _unique_identifiers(
                row.get("ordered_child_node_ids"),
                nonempty=False,
                maximum=limits["node_fanout"],
            )
            or type(row.get("operator_configuration")) is not dict
            or row.get("applicability_id") != _APPLICABILITY_ID
            or row.get("failure_oracle_id") != _FAILURE_ORACLE_ID
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .PREDICATE_REGISTRY_INVALID
            )
        operand_ids = row["ordered_operand_ids"]
        child_ids = row["ordered_child_node_ids"]
        if (
            not operator_schema["minimum_operand_count"]
            <= len(operand_ids)
            <= operator_schema["maximum_operand_count"]
            or not operator_schema["minimum_child_count"]
            <= len(child_ids)
            <= operator_schema["maximum_child_count"]
            or any(operand_id not in operands for operand_id in operand_ids)
            or any(child_id not in by_id for child_id in child_ids)
            or len(operand_ids) + len(child_ids) > limits["node_fanout"]
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .PREDICATE_REGISTRY_INVALID
            )
        expected_configuration = set(
            operator_schema["exact_configuration_field_ids"]
        )
        configuration = row["operator_configuration"]
        if set(configuration) != expected_configuration:
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .TYPE_RELATION_INVALID
            )
        if "interval_order_mode_id" in expected_configuration and (
            type(configuration["interval_order_mode_id"]) is not str
            or configuration["interval_order_mode_id"]
            not in {"TOUCHING_ADMITTED", "STRICTLY_SEPARATED"}
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .TYPE_RELATION_INVALID
            )
        if core_operator is not None:
            valid_relation = _core_operator_relation_valid(
                operator_id,
                operand_ids,
                child_ids,
                configuration,
                operands,
                types,
                decoded_literals,
            )
            if not valid_relation:
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .TYPE_RELATION_INVALID
                )
        else:
            if not _core_operator_relation_valid(
                "member-of-frozen-program-set",
                operand_ids,
                child_ids,
                configuration,
                operands,
                types,
                decoded_literals,
            ):
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .TYPE_RELATION_INVALID
                )
            if (
                specialization["primitive_id"]
                != "member-of-frozen-program-set"
                or not _profile_membership_relation_valid(
                    specialization,
                    operand_ids,
                    operands,
                    types,
                    decoded_literals,
                    profile_tree,
                )
            ):
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .PROFILE_EXTENSION_INVALID
                )
        by_id[row["node_id"]] = (index, row)
    return rows, by_id, tuple(row["node_id"] for row in rows)


def _validate_whole_graph(
    program: dict,
    operands: dict,
    shaping_rows: list,
    shaping_nodes: dict,
    predicate_rows: list,
    predicate_nodes: dict,
    limits: dict,
) -> tuple:
    reference_count = sum(
        len(row["ordered_input_operand_ids"]) for row in shaping_rows
    ) + sum(
        len(row["ordered_operand_ids"])
        + len(row["ordered_child_node_ids"])
        for row in predicate_rows
    )
    if reference_count > limits["node_references"]:
        _fail(PortablePredicateProgramFormulaVerificationCode.GRAPH_INVALID)
    if (
        not predicate_rows
        or program["root_node_id"] != predicate_rows[-1]["node_id"]
    ):
        _fail(PortablePredicateProgramFormulaVerificationCode.GRAPH_INVALID)

    reachable_predicates = set()
    pending_predicates = [program["root_node_id"]]
    directly_used_operands = set()
    while pending_predicates:
        node_id = pending_predicates.pop()
        if node_id in reachable_predicates:
            continue
        node = predicate_nodes.get(node_id)
        if node is None:
            _fail(PortablePredicateProgramFormulaVerificationCode.GRAPH_INVALID)
        reachable_predicates.add(node_id)
        row = node[1]
        directly_used_operands.update(row["ordered_operand_ids"])
        pending_predicates.extend(row["ordered_child_node_ids"])
    if reachable_predicates != set(predicate_nodes):
        _fail(PortablePredicateProgramFormulaVerificationCode.GRAPH_INVALID)

    shaping_by_output = {
        row["output_operand_id"]: row for row in shaping_rows
    }
    used_operands = set()
    used_shaping = set()

    def mark_operand(operand_id: str) -> None:
        if operand_id in used_operands:
            return
        operand = operands.get(operand_id)
        if operand is None:
            _fail(PortablePredicateProgramFormulaVerificationCode.GRAPH_INVALID)
        used_operands.add(operand_id)
        if operand[1]["value_source_kind_id"] == _DERIVED_TYPED_VALUE:
            shaping = shaping_by_output.get(operand_id)
            if shaping is None:
                _fail(
                    PortablePredicateProgramFormulaVerificationCode.GRAPH_INVALID
                )
            used_shaping.add(shaping["shaping_node_id"])
            for input_id in shaping["ordered_input_operand_ids"]:
                mark_operand(input_id)

    for operand_id in directly_used_operands:
        mark_operand(operand_id)
    if used_operands != set(operands) or used_shaping != set(shaping_nodes):
        _fail(PortablePredicateProgramFormulaVerificationCode.GRAPH_INVALID)

    operand_depth = {}
    for operand_id, (_, operand) in operands.items():
        if operand["value_source_kind_id"] != _DERIVED_TYPED_VALUE:
            operand_depth[operand_id] = 0
            continue
        shaping = shaping_by_output.get(operand_id)
        if shaping is None or any(
            input_id not in operand_depth
            for input_id in shaping["ordered_input_operand_ids"]
        ):
            _fail(PortablePredicateProgramFormulaVerificationCode.GRAPH_INVALID)
        operand_depth[operand_id] = 1 + max(
            (
                operand_depth[input_id]
                for input_id in shaping["ordered_input_operand_ids"]
            ),
            default=0,
        )
    predicate_depth = {}
    for row in predicate_rows:
        if any(
            child_id not in predicate_depth
            for child_id in row["ordered_child_node_ids"]
        ):
            _fail(PortablePredicateProgramFormulaVerificationCode.GRAPH_INVALID)
        dependency_depths = [
            operand_depth[operand_id]
            for operand_id in row["ordered_operand_ids"]
        ] + [
            predicate_depth[child_id]
            for child_id in row["ordered_child_node_ids"]
        ]
        predicate_depth[row["node_id"]] = 1 + max(
            dependency_depths,
            default=0,
        )
    graph_depth = predicate_depth[program["root_node_id"]]
    if graph_depth > limits["graph_depth"]:
        _fail(PortablePredicateProgramFormulaVerificationCode.GRAPH_INVALID)
    return graph_depth, reference_count


def _traverse_object_path(value: object, path: list) -> object:
    current = value
    for field_id in path:
        if type(current) is not dict or field_id not in current:
            raise KeyError
        current = current[field_id]
    return current


def _validate_purpose_relations(
    purpose: dict,
    purpose_binding: dict,
    anchors: dict,
    operand_rows: list,
) -> None:
    comparison_count = 0
    for relation in purpose["purpose_relation_rows"]:
        primitive = relation["relation_primitive_id"]
        if primitive == (
            "exactly-one-pinned-anchor-row-canonical-equality-v1"
        ):
            try:
                collection = _traverse_object_path(
                    anchors[relation["anchor_role_id"]],
                    relation["anchor_row_array_path_ids"],
                )
            except (KeyError, TypeError):
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .PURPOSE_RELATION_UNSATISFIED
                )
            if (
                type(collection) is not list
                or any(type(row) is not dict for row in collection)
            ):
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .PURPOSE_RELATION_UNSATISFIED
                )
            match_count = 0
            for anchor_row in collection:
                matches = True
                for equality in relation["ordered_equality_rows"]:
                    comparison_count += 1
                    if (
                        comparison_count
                        > _MAXIMUM_PURPOSE_RELATION_COMPARISONS
                    ):
                        _fail(
                            PortablePredicateProgramFormulaVerificationCode
                            .PURPOSE_RELATION_UNSATISFIED
                        )
                    try:
                        anchor_value = _traverse_object_path(
                            anchor_row,
                            equality["anchor_row_value_path_ids"],
                        )
                    except (KeyError, TypeError):
                        _fail(
                            PortablePredicateProgramFormulaVerificationCode
                            .PURPOSE_RELATION_UNSATISFIED
                        )
                    purpose_value = purpose_binding[
                        equality["purpose_binding_field_id"]
                    ]
                    if not _same_exact(anchor_value, purpose_value):
                        matches = False
                        break
                if matches:
                    match_count += 1
            if match_count != 1:
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .PURPOSE_RELATION_UNSATISFIED
                )
        elif primitive == (
            "purpose-identifiers-exactly-covered-by-input-locators-v1"
        ):
            field_id = relation["locator_value_field_id"]
            observed = {
                operand["locator"][field_id]
                for operand in operand_rows
                if operand["value_source_kind_id"] == _INPUT_RESOLVED
                and field_id in operand["locator"]
            }
            required = set(
                purpose_binding[relation["purpose_binding_field_id"]]
            )
            if observed != required:
                _fail(
                    PortablePredicateProgramFormulaVerificationCode
                    .PURPOSE_RELATION_UNSATISFIED
                )
        else:
            _fail(
                PortablePredicateProgramFormulaVerificationCode.INTERNAL
            )


def _validate_nonclaims(
    program: dict,
    core_tree: dict,
    profile_tree: dict,
) -> None:
    expected_ids = set(core_tree["nonclaim_state"]) | set(
        profile_tree["nonclaim_state"]
    )
    state = program["nonclaim_state"]
    if (
        type(state) is not dict
        or set(state) != expected_ids
        or any(type(value) is not bool or value for value in state.values())
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode.NONCLAIM_STATE_INVALID
        )


def _map_envelope_failure(
    error: _envelope.PortablePredicateRuntimeEnvelopeVerificationError,
    *,
    program: bool,
) -> None:
    if error.code == (
        _envelope.PortablePredicateRuntimeEnvelopeVerificationCode
        .ARTIFACT_BINDING_MISMATCH.value
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode.PROGRAM_BINDING_MISMATCH
            if program
            else (
                PortablePredicateProgramFormulaVerificationCode
                .FORMULA_BINDING_MISMATCH
            )
        )
    if error.code == (
        _envelope.PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL.value
    ):
        _fail(PortablePredicateProgramFormulaVerificationCode.INTERNAL)
    _fail(
        PortablePredicateProgramFormulaVerificationCode.PROGRAM_ENVELOPE_INVALID
        if program
        else PortablePredicateProgramFormulaVerificationCode.FORMULA_ENVELOPE_INVALID
    )


def _verify_portable_predicate_program_formula_pair_v1_impl(
    program_artifact_bytes: bytes,
    formula_core_artifact_bytes: bytes,
    *,
    compiled_profile: (
        _envelope.CompiledPortablePredicateRuntimeVerifierProfileV1
    ),
    anchor_contract_artifacts: tuple = (),
) -> VerifiedPortablePredicateProgramFormulaPairV1:
    """Verify one complete static program and its exact formula projection."""

    if (
        type(program_artifact_bytes) is not bytes
        or type(formula_core_artifact_bytes) is not bytes
        or type(anchor_contract_artifacts) is not tuple
    ):
        _fail(PortablePredicateProgramFormulaVerificationCode.INPUT_TYPE)

    try:
        selected_profile = _envelope._revalidate_profile_snapshot(
            compiled_profile
        )
    except _envelope.PortablePredicateRuntimeEnvelopeVerificationError as error:
        if error.code == (
            _envelope.PortablePredicateRuntimeEnvelopeVerificationCode
            .INTERNAL.value
        ):
            _fail(PortablePredicateProgramFormulaVerificationCode.INTERNAL)
        _fail(
            PortablePredicateProgramFormulaVerificationCode.COMPILED_PROFILE_INVALID
        )

    core_tree = (
        _core.portable_predicate_language_core_verifier_contract_tree()
    )
    limits = core_tree["resource_limits"]
    maximum_artifact_bytes = limits["artifact_bytes"]
    if (
        not program_artifact_bytes
        or len(program_artifact_bytes) > maximum_artifact_bytes
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode
            .PROGRAM_INPUT_RESOURCE
        )
    if (
        not formula_core_artifact_bytes
        or len(formula_core_artifact_bytes) > maximum_artifact_bytes
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode
            .FORMULA_INPUT_RESOURCE
        )
    if len(anchor_contract_artifacts) > limits["collection_items"]:
        _fail(
            PortablePredicateProgramFormulaVerificationCode
            .ANCHOR_INPUT_RESOURCE
        )
    if any(
        type(row) is not tuple
        or len(row) != 2
        or type(row[0]) is not str
        or type(row[1]) is not bytes
        for row in anchor_contract_artifacts
    ):
        _fail(PortablePredicateProgramFormulaVerificationCode.INPUT_TYPE)
    program_raw = program_artifact_bytes
    formula_raw = formula_core_artifact_bytes
    anchor_snapshot = anchor_contract_artifacts
    if (
        any(
            not raw or len(raw) > maximum_artifact_bytes
            for _, raw in anchor_snapshot
        )
        or sum(len(raw) for _, raw in anchor_snapshot)
        > maximum_artifact_bytes
    ):
        _fail(
            PortablePredicateProgramFormulaVerificationCode.ANCHOR_INPUT_RESOURCE
        )

    program = _decode_canonical_json(
        program_raw,
        resource_code=(
            PortablePredicateProgramFormulaVerificationCode.PROGRAM_INPUT_RESOURCE
        ),
        json_code=(
            PortablePredicateProgramFormulaVerificationCode.PROGRAM_JSON_INVALID
        ),
        tree_code=(
            PortablePredicateProgramFormulaVerificationCode.PROGRAM_JSON_TREE_INVALID
        ),
        canonical_code=(
            PortablePredicateProgramFormulaVerificationCode.PROGRAM_CANONICAL_MISMATCH
        ),
    )
    formula = _decode_canonical_json(
        formula_raw,
        resource_code=(
            PortablePredicateProgramFormulaVerificationCode.FORMULA_INPUT_RESOURCE
        ),
        json_code=(
            PortablePredicateProgramFormulaVerificationCode.FORMULA_JSON_INVALID
        ),
        tree_code=(
            PortablePredicateProgramFormulaVerificationCode.FORMULA_JSON_TREE_INVALID
        ),
        canonical_code=(
            PortablePredicateProgramFormulaVerificationCode.FORMULA_CANONICAL_MISMATCH
        ),
    )

    try:
        program_envelope = (
            _envelope.verify_portable_predicate_runtime_envelope_v1(
                program_raw,
                expected_artifact_role_id="predicate-program",
                compiled_profile=selected_profile,
            )
        )
    except _envelope.PortablePredicateRuntimeEnvelopeVerificationError as error:
        _map_envelope_failure(error, program=True)
    try:
        formula_envelope = (
            _envelope.verify_portable_predicate_runtime_envelope_v1(
                formula_raw,
                expected_artifact_role_id="predicate-formula-core",
                compiled_profile=selected_profile,
            )
        )
    except _envelope.PortablePredicateRuntimeEnvelopeVerificationError as error:
        _map_envelope_failure(error, program=False)
    if type(program) is not dict or type(formula) is not dict:
        _fail(
            PortablePredicateProgramFormulaVerificationCode.PROGRAM_ENVELOPE_INVALID
        )

    profile_tree = _profile_tree(selected_profile)
    purpose, canonical_purpose_binding = _validate_purpose_binding(
        program, profile_tree, limits
    )
    required_anchor_roles = _ordered_required_anchor_roles(purpose)
    anchors = _validate_anchor_bundle(
        anchor_snapshot,
        required_anchor_roles,
        profile_tree,
    )
    types, ordered_type_ids, type_depth = _validate_types(
        program, core_tree
    )
    (
        operand_rows,
        operands,
        ordered_operand_ids,
        ordered_input_operand_ids,
        ordered_derived_operand_ids,
    ) = _validate_operand_registry(
        program, types, profile_tree, limits
    )
    decoded_literals = _validate_program_literals(
        operand_rows, types, limits
    )
    _validate_locators(
        operand_rows,
        operands,
        program["purpose_binding"],
        profile_tree,
        types,
        limits,
    )
    shaping_rows, shaping_nodes, ordered_shaping_node_ids = (
        _validate_shaping_nodes(
            program,
            operands,
            types,
            profile_tree,
            core_tree,
        )
    )
    predicate_rows, predicate_nodes, ordered_predicate_node_ids = (
        _validate_predicate_nodes(
            program,
            operands,
            shaping_nodes,
            types,
            decoded_literals,
            profile_tree,
            core_tree,
        )
    )
    _validate_interval_refinements(types, profile_tree)
    graph_depth, node_reference_count = _validate_whole_graph(
        program,
        operands,
        shaping_rows,
        shaping_nodes,
        predicate_rows,
        predicate_nodes,
        limits,
    )
    _validate_purpose_relations(
        purpose,
        program["purpose_binding"],
        anchors,
        operand_rows,
    )
    _validate_nonclaims(program, core_tree, profile_tree)

    domains = _binding_by_role(profile_tree)
    formula_binding = domains["predicate-formula-core"]
    projected_formula = {
        "artifact_type": formula_binding["artifact_type_id"],
        "format_version": program["format_version"],
        "semantic_core_contract_sha256": (
            program["semantic_core_contract_sha256"]
        ),
        "profile_contract_sha256": program["profile_contract_sha256"],
        "ordered_type_rows": program["ordered_type_rows"],
        "ordered_operand_rows": program["ordered_operand_rows"],
        "ordered_shaping_node_rows": (
            program["ordered_shaping_node_rows"]
        ),
        "ordered_predicate_node_rows": (
            program["ordered_predicate_node_rows"]
        ),
        "root_node_id": program["root_node_id"],
    }
    try:
        projected_formula_bytes = _envelope._encode_canonical(
            projected_formula
        )
    except _envelope.PortablePredicateRuntimeEnvelopeVerificationError:
        _fail(PortablePredicateProgramFormulaVerificationCode.INTERNAL)
    if len(projected_formula_bytes) > maximum_artifact_bytes:
        _fail(
            PortablePredicateProgramFormulaVerificationCode.FORMULA_INPUT_RESOURCE
        )
    if projected_formula_bytes != formula_raw:
        _fail(
            PortablePredicateProgramFormulaVerificationCode.FORMULA_PROJECTION_MISMATCH
        )

    formula_identity = _framed_digest(
        formula_binding["digest_domain_id"],
        projected_formula_bytes,
    )
    if program["formula_core_identity_sha256"] != formula_identity:
        _fail(
            PortablePredicateProgramFormulaVerificationCode.FORMULA_IDENTITY_MISMATCH
        )
    profile_fields = _profile_fields(profile_tree)
    for field_id, value in program["purpose_binding"].items():
        schema = profile_fields[field_id]
        if (
            schema["role_parameter_id"] == "predicate-formula-core"
            and (
                (
                    schema["semantic_role_id"]
                    == "artifact-identity-sha256-for-role"
                    and value != formula_identity
                )
                or (
                    schema["semantic_role_id"] == "artifact-type-for-role"
                    and value != formula_binding["artifact_type_id"]
                )
                or (
                    schema["semantic_role_id"]
                    == "artifact-identity-semantics-for-role"
                    and value != formula_binding["identity_semantics_id"]
                )
            )
        ):
            _fail(
                PortablePredicateProgramFormulaVerificationCode
                .FORMULA_IDENTITY_MISMATCH
            )

    return VerifiedPortablePredicateProgramFormulaPairV1(
        canonical_program_bytes=program_raw,
        canonical_formula_core_bytes=projected_formula_bytes,
        canonical_purpose_binding_bytes=canonical_purpose_binding,
        program_identity_sha256=program_envelope.artifact_identity_sha256,
        formula_core_identity_sha256=formula_identity,
        program_byte_count=len(program_raw),
        formula_core_byte_count=len(projected_formula_bytes),
        program_artifact_type=program_envelope.artifact_type,
        formula_core_artifact_type=formula_envelope.artifact_type,
        semantic_core_contract_sha256=(
            selected_profile.semantic_core_contract_sha256
        ),
        profile_contract_sha256=selected_profile.profile_contract_sha256,
        profile_id=selected_profile.profile_id,
        program_id=program["program_id"],
        program_purpose_id=program["program_purpose_id"],
        ordered_type_ids=ordered_type_ids,
        ordered_operand_ids=ordered_operand_ids,
        ordered_input_operand_ids=ordered_input_operand_ids,
        ordered_derived_operand_ids=ordered_derived_operand_ids,
        ordered_shaping_node_ids=ordered_shaping_node_ids,
        ordered_predicate_node_ids=ordered_predicate_node_ids,
        root_node_id=program["root_node_id"],
        required_anchor_role_ids=required_anchor_roles,
        type_depth=type_depth,
        graph_depth=graph_depth,
        node_reference_count=node_reference_count,
        validation_scope_id=_VALIDATION_SCOPE_ID,
        nested_program_semantics_validated=True,
        formula_projection_validated=True,
        evaluation_performed=False,
    )


def verify_portable_predicate_program_formula_pair_v1(
    program_artifact_bytes: bytes,
    formula_core_artifact_bytes: bytes,
    *,
    compiled_profile: (
        _envelope.CompiledPortablePredicateRuntimeVerifierProfileV1
    ),
    anchor_contract_artifacts: tuple = (),
) -> VerifiedPortablePredicateProgramFormulaPairV1:
    """Verify one canonical program and its exact formula projection."""

    try:
        return _verify_portable_predicate_program_formula_pair_v1_impl(
            program_artifact_bytes,
            formula_core_artifact_bytes,
            compiled_profile=compiled_profile,
            anchor_contract_artifacts=anchor_contract_artifacts,
        )
    except PortablePredicateProgramFormulaVerificationError:
        raise
    except MemoryError:
        raise
    except Exception:
        _fail(PortablePredicateProgramFormulaVerificationCode.INTERNAL)
