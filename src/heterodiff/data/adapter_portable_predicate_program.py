"""Validate portable predicate programs and exact formula-core projections.

Checkpoint 56B parses only the static nested program structure. It does not
resolve a locator, execute a constructor or predicate, construct a runtime
input, or validate an empirical claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Final

from heterodiff.data import (
    adapter_portable_predicate_language_core as _core,
)
from heterodiff.data import (
    adapter_portable_predicate_runtime_artifacts as _runtime,
)


__all__ = (
    "PortablePredicateProgramFormulaCode",
    "PortablePredicateProgramFormulaError",
    "PortablePredicateProgramFormulaPairV1",
    "parse_portable_predicate_program_formula_pair_v1",
)


PORTABLE_PREDICATE_PROGRAM_FORMULA_VALIDATION_SCOPE_ID: Final = (
    "FULL_PROGRAM_FORMULA_STRUCTURE_AND_PROJECTION_ONLY_V1"
)
_MAXIMUM_ARTIFACT_BYTES: Final = 4 * 1024 * 1024
_MAXIMUM_TYPED_PAYLOAD_BYTES: Final = 1024 * 1024
_MAXIMUM_COLLECTION_ITEMS: Final = 4096
_MAXIMUM_ANCHOR_AGGREGATE_BYTES: Final = 4 * 1024 * 1024
_MAXIMUM_PURPOSE_RELATION_COMPARISONS: Final = 1024 * 1024


class PortablePredicateProgramFormulaCode(str, Enum):
    """Closed ordinary failures for the Checkpoint-56B pair boundary."""

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
    code: (
        "portable predicate program/formula "
        + code.value.lower().replace("_", " ")
    )
    for code in PortablePredicateProgramFormulaCode
}


class PortablePredicateProgramFormulaError(ValueError):
    """One fixed-message Checkpoint-56B failure."""

    def __init__(self, code: PortablePredicateProgramFormulaCode):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


@dataclass(frozen=True)
class PortablePredicateProgramFormulaPairV1:
    """Immutable receipt for one fully parsed program/formula pair."""

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


def _reject(code: PortablePredicateProgramFormulaCode) -> None:
    raise PortablePredicateProgramFormulaError(code) from None


def _exact_keys(value: object, keys: tuple) -> bool:
    return type(value) is dict and set(value) == set(keys)


def _same_exact(left: object, right: object) -> bool:
    pending = [(left, right)]
    while pending:
        current_left, current_right = pending.pop()
        if type(current_left) is not type(current_right):
            return False
        if type(current_left) is dict:
            if set(current_left) != set(current_right):
                return False
            pending.extend(
                (current_left[key], current_right[key])
                for key in current_left
            )
        elif type(current_left) is list:
            if len(current_left) != len(current_right):
                return False
            pending.extend(zip(current_left, current_right))
        elif current_left != current_right:
            return False
    return True


def _decode_trusted_canonical(value: bytes) -> object:
    try:
        return json.loads(value.decode("ascii", "strict"))
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _reject(PortablePredicateProgramFormulaCode.INTERNAL)


def _snapshot_anchor_arguments(value: object) -> tuple:
    if type(value) is not tuple:
        _reject(PortablePredicateProgramFormulaCode.INPUT_TYPE)
    for row in value:
        if (
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not str
            or type(row[1]) is not bytes
        ):
            _reject(PortablePredicateProgramFormulaCode.INPUT_TYPE)
    return value


def _revalidate_profile(compiled_profile: object) -> object:
    failure_code = None
    try:
        profile = _runtime._revalidate_compiled_profile(compiled_profile)
    except _runtime.PortablePredicateRuntimeEnvelopeError as error:
        failure_code = error.code
    if failure_code == _runtime.PortablePredicateRuntimeEnvelopeCode.INTERNAL.value:
        _reject(PortablePredicateProgramFormulaCode.INTERNAL)
    if failure_code is not None:
        _reject(
            PortablePredicateProgramFormulaCode.COMPILED_PROFILE_INVALID
        )
    return profile


def _check_program_formula_resource_limits(
    program_bytes: bytes,
    formula_bytes: bytes,
) -> None:
    if not program_bytes or len(program_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateProgramFormulaCode.PROGRAM_INPUT_RESOURCE
        )
    if not formula_bytes or len(formula_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateProgramFormulaCode.FORMULA_INPUT_RESOURCE
        )


def _check_anchor_resource_limits(anchors: tuple) -> None:
    total = 0
    for _, anchor_bytes in anchors:
        if (
            not anchor_bytes
            or len(anchor_bytes) > _MAXIMUM_ARTIFACT_BYTES
        ):
            _reject(
                PortablePredicateProgramFormulaCode.ANCHOR_INPUT_RESOURCE
            )
        total += len(anchor_bytes)
        if total > _MAXIMUM_ANCHOR_AGGREGATE_BYTES:
            _reject(
                PortablePredicateProgramFormulaCode.ANCHOR_INPUT_RESOURCE
            )


def _strict_runtime_tree(
    value: bytes,
    *,
    resource_code: PortablePredicateProgramFormulaCode,
    json_code: PortablePredicateProgramFormulaCode,
    tree_code: PortablePredicateProgramFormulaCode,
    canonical_code: PortablePredicateProgramFormulaCode,
) -> object:
    runtime_failure = None
    try:
        decoded = _runtime._strict_json(
            value,
            resource_code=(
                _runtime
                .PortablePredicateRuntimeEnvelopeCode
                .ARTIFACT_INPUT_RESOURCE
            ),
            json_code=(
                _runtime
                .PortablePredicateRuntimeEnvelopeCode
                .ARTIFACT_JSON_INVALID
            ),
            tree_code=(
                _runtime
                .PortablePredicateRuntimeEnvelopeCode
                .ARTIFACT_JSON_TREE_INVALID
            ),
        )
    except _runtime.PortablePredicateRuntimeEnvelopeError as error:
        runtime_failure = error.code
    if runtime_failure is not None:
        if runtime_failure == (
            _runtime
            .PortablePredicateRuntimeEnvelopeCode
            .ARTIFACT_INPUT_RESOURCE
            .value
        ):
            _reject(resource_code)
        if runtime_failure == (
            _runtime
            .PortablePredicateRuntimeEnvelopeCode
            .ARTIFACT_JSON_INVALID
            .value
        ):
            _reject(json_code)
        if runtime_failure == (
            _runtime
            .PortablePredicateRuntimeEnvelopeCode
            .ARTIFACT_JSON_TREE_INVALID
            .value
        ):
            _reject(tree_code)
        _reject(PortablePredicateProgramFormulaCode.INTERNAL)
    canonical = _runtime._canonical_json(decoded)
    if len(canonical) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(resource_code)
    if value != canonical:
        _reject(canonical_code)
    return decoded


def _validate_envelope(
    value: bytes,
    *,
    role_id: str,
    profile: object,
    envelope_code: PortablePredicateProgramFormulaCode,
    binding_code: PortablePredicateProgramFormulaCode,
) -> object:
    failure_code = None
    try:
        envelope = (
            _runtime.parse_portable_predicate_runtime_envelope_v1(
                value,
                expected_artifact_role_id=role_id,
                compiled_profile=profile,
            )
        )
    except _runtime.PortablePredicateRuntimeEnvelopeError as error:
        failure_code = error.code
    if failure_code is not None:
        if failure_code == (
            _runtime.PortablePredicateRuntimeEnvelopeCode.INTERNAL.value
        ):
            _reject(PortablePredicateProgramFormulaCode.INTERNAL)
        if failure_code in {
            _runtime
            .PortablePredicateRuntimeEnvelopeCode
            .PROFILE_INPUT_TYPE
            .value,
            _runtime
            .PortablePredicateRuntimeEnvelopeCode
            .PROFILE_INPUT_RESOURCE
            .value,
            _runtime
            .PortablePredicateRuntimeEnvelopeCode
            .PROFILE_JSON_INVALID
            .value,
            _runtime
            .PortablePredicateRuntimeEnvelopeCode
            .PROFILE_JSON_TREE_INVALID
            .value,
            _runtime
            .PortablePredicateRuntimeEnvelopeCode
            .PROFILE_CANONICAL_MISMATCH
            .value,
            _runtime
            .PortablePredicateRuntimeEnvelopeCode
            .PROFILE_SCHEMA_INVALID
            .value,
            _runtime
            .PortablePredicateRuntimeEnvelopeCode
            .PROFILE_BINDING_MISMATCH
            .value,
            _runtime
            .PortablePredicateRuntimeEnvelopeCode
            .COMPILED_PROFILE_INVALID
            .value,
        }:
            _reject(
                PortablePredicateProgramFormulaCode.COMPILED_PROFILE_INVALID
            )
        if failure_code == (
            _runtime
            .PortablePredicateRuntimeEnvelopeCode
            .ARTIFACT_BINDING_MISMATCH
            .value
        ):
            _reject(binding_code)
        _reject(envelope_code)
    return envelope


def _profile_binding(profile_tree: dict, role_id: str) -> dict:
    rows = [
        row
        for row in profile_tree["artifact_domain_rows"]
        if row["artifact_role_id"] == role_id
    ]
    if len(rows) != 1:
        _reject(PortablePredicateProgramFormulaCode.INTERNAL)
    return rows[0]


def _validate_type_row_primitive(
    row: object,
    schema_by_kind: dict,
    limits: dict,
) -> None:
    if type(row) is not dict:
        _reject(PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID)
    kind_id = row.get("type_kind_id")
    schema = (
        schema_by_kind.get(kind_id)
        if _runtime._is_identifier(kind_id)
        else None
    )
    if (
        schema is None
        or not _exact_keys(row, tuple(schema["exact_field_ids"]))
        or not _runtime._is_identifier(row.get("type_id"))
    ):
        _reject(PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID)
    if kind_id in {"boolean", "u64", "token", "octets"}:
        domain_field = {
            "boolean": "proposition_domain_id",
            "u64": "unit_id",
            "token": "token_domain_id",
            "octets": "octet_domain_id",
        }[kind_id]
        valid = _runtime._is_identifier(row[domain_field])
    elif kind_id == "sha256":
        valid = (
            row["digest_semantics_id"] == "PLAIN_SHA256"
            and type(row["digest_domain_id"]) is str
            and row["digest_domain_id"] == ""
        ) or (
            row["digest_semantics_id"] == "DOMAIN_SEPARATED_SHA256"
            and _runtime._is_identifier(row["digest_domain_id"])
        )
    elif kind_id in {"optional", "sequence"}:
        valid = _runtime._is_identifier(row["item_type_id"])
    elif kind_id == "tuple":
        components = row["ordered_component_type_ids"]
        valid = (
            type(components) is list
            and 1 <= len(components) <= limits["tuple_components"]
            and all(_runtime._is_identifier(item) for item in components)
        )
    elif kind_id == "keyed-table":
        indices = row["ordered_key_component_indices"]
        valid = (
            _runtime._is_identifier(row["row_tuple_type_id"])
            and _runtime._is_identifier(row["key_tuple_type_id"])
            and type(indices) is list
            and 1 <= len(indices) <= limits["selector_key_components"]
            and all(type(index) is int and index >= 0 for index in indices)
            and len(indices) == len(set(indices))
        )
    elif kind_id == "u64-interval-sequence":
        valid = _runtime._is_identifier(row["endpoint_u64_type_id"])
    else:
        valid = False
    if not valid:
        _reject(PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID)


def _parse_type_registry(
    rows: object,
    limits: dict,
) -> tuple:
    if type(rows) is not list or len(rows) > limits["type_rows"]:
        _reject(
            PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID
        )
    schema_by_kind = {
        row["type_kind_id"]: row
        for row in _core.portable_predicate_language_core_contract_tree()[
            "type_contract"
        ]["type_kind_schema_rows"]
    }
    for row in rows:
        _validate_type_row_primitive(row, schema_by_kind, limits)
    declared_type_ids = [row["type_id"] for row in rows]
    if len(declared_type_ids) != len(set(declared_type_ids)):
        _reject(PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID)
    types = {}
    depths = {}
    for row in rows:
        if type(row) is not dict:
            _reject(
                PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID
            )
        kind_id = row.get("type_kind_id")
        schema = (
            schema_by_kind.get(kind_id)
            if _runtime._is_identifier(kind_id)
            else None
        )
        if (
            schema is None
            or not _exact_keys(row, tuple(schema["exact_field_ids"]))
            or not _runtime._is_identifier(row.get("type_id"))
            or row["type_id"] in types
        ):
            _reject(
                PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID
            )
        type_id = row["type_id"]
        reference_ids = []
        if kind_id in {"boolean", "u64", "token", "octets"}:
            domain_field = {
                "boolean": "proposition_domain_id",
                "u64": "unit_id",
                "token": "token_domain_id",
                "octets": "octet_domain_id",
            }[kind_id]
            if not _runtime._is_identifier(row[domain_field]):
                _reject(
                    PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID
                )
        elif kind_id == "sha256":
            semantics = row["digest_semantics_id"]
            domain = row["digest_domain_id"]
            if not (
                (
                    semantics == "PLAIN_SHA256"
                    and type(domain) is str
                    and domain == ""
                )
                or (
                    semantics == "DOMAIN_SEPARATED_SHA256"
                    and _runtime._is_identifier(domain)
                )
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID
                )
        elif kind_id in {"optional", "sequence"}:
            reference_ids = [row["item_type_id"]]
        elif kind_id == "tuple":
            components = row["ordered_component_type_ids"]
            if (
                type(components) is not list
                or not 1 <= len(components) <= limits["tuple_components"]
                or any(
                    not _runtime._is_identifier(item)
                    for item in components
                )
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID
                )
            reference_ids = list(components)
        elif kind_id == "keyed-table":
            indices = row["ordered_key_component_indices"]
            if (
                type(indices) is not list
                or not 1
                <= len(indices)
                <= limits["selector_key_components"]
                or any(
                    type(index) is not int or index < 0
                    for index in indices
                )
                or len(indices) != len(set(indices))
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID
                )
            reference_ids = [
                row["row_tuple_type_id"],
                row["key_tuple_type_id"],
            ]
        elif kind_id == "u64-interval-sequence":
            reference_ids = [row["endpoint_u64_type_id"]]
        else:
            _reject(PortablePredicateProgramFormulaCode.INTERNAL)
        if any(
            not _runtime._is_identifier(item) or item not in types
            for item in reference_ids
        ):
            _reject(
                PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID
            )
        depth = 1 + max(
            (depths[item] for item in reference_ids),
            default=0,
        )
        if depth > limits["type_depth"]:
            _reject(
                PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID
            )
        if kind_id == "keyed-table":
            row_type = types[row["row_tuple_type_id"]]
            key_type = types[row["key_tuple_type_id"]]
            if (
                row_type["type_kind_id"] != "tuple"
                or key_type["type_kind_id"] != "tuple"
                or any(
                    index
                    >= len(row_type["ordered_component_type_ids"])
                    for index in row["ordered_key_component_indices"]
                )
                or key_type["ordered_component_type_ids"]
                != [
                    row_type["ordered_component_type_ids"][index]
                    for index in row[
                        "ordered_key_component_indices"
                    ]
                ]
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID
                )
        if kind_id == "u64-interval-sequence":
            endpoint = types[row["endpoint_u64_type_id"]]
            if endpoint["type_kind_id"] != "u64":
                _reject(
                    PortablePredicateProgramFormulaCode.TYPE_REGISTRY_INVALID
                )
        types[type_id] = row
        depths[type_id] = depth
    return (
        types,
        tuple(row["type_id"] for row in rows),
        max(depths.values(), default=0),
    )


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
    for row in types.values():
        if row["type_kind_id"] != "u64-interval-sequence":
            continue
        endpoint = types[row["endpoint_u64_type_id"]]
        if endpoint["unit_id"] not in admitted_units:
            _reject(
                PortablePredicateProgramFormulaCode.PROFILE_EXTENSION_INVALID
            )


def _read_u64(value: memoryview, offset: int) -> tuple:
    if offset + 8 > len(value):
        _reject(
            PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
        )
    return (int.from_bytes(value[offset : offset + 8], "big"), offset + 8)


def _read_frame(value: memoryview, offset: int) -> tuple:
    length, offset = _read_u64(value, offset)
    if length > len(value) - offset:
        _reject(
            PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
        )
    end = offset + length
    return (value[offset:end], end)


def _decode_typed_payload(
    type_id: str,
    payload: bytes,
    types: dict,
) -> object:
    return _decode_typed_payload_view(
        type_id,
        memoryview(payload),
        types,
    )


def _decode_typed_payload_view(
    type_id: str,
    payload: memoryview,
    types: dict,
) -> object:
    if len(payload) > _MAXIMUM_TYPED_PAYLOAD_BYTES:
        _reject(
            PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
        )
    row = types.get(type_id)
    if row is None:
        _reject(
            PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
        )
    kind_id = row["type_kind_id"]
    if kind_id == "boolean":
        if len(payload) != 1 or payload[0] not in (0, 1):
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        return payload[0] == 1
    if kind_id == "u64":
        if len(payload) != 8:
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        return int.from_bytes(payload, "big")
    if kind_id == "token":
        try:
            token = bytes(payload).decode("ascii", "strict")
        except UnicodeError:
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        if not _runtime._is_identifier(token):
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        return token
    if kind_id == "octets":
        if len(payload) > 262144:
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        return bytes(payload)
    if kind_id == "sha256":
        if len(payload) != 32:
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        return bytes(payload)
    if kind_id == "optional":
        if len(payload) == 1 and payload[0] == 0:
            return ("optional-none",)
        if not payload or payload[0] != 1:
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        item, end = _read_frame(payload, 1)
        if end != len(payload):
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        return (
            "optional-some",
            _decode_typed_payload_view(
                row["item_type_id"],
                item,
                types,
            ),
        )
    count, offset = _read_u64(payload, 0)
    if count > _MAXIMUM_COLLECTION_ITEMS:
        _reject(
            PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
        )
    if kind_id == "sequence":
        values = []
        for _ in range(count):
            item, offset = _read_frame(payload, offset)
            values.append(
                _decode_typed_payload_view(
                    row["item_type_id"],
                    item,
                    types,
                )
            )
        if offset != len(payload):
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        return ("sequence", tuple(values))
    if kind_id == "tuple":
        component_ids = row["ordered_component_type_ids"]
        if count != len(component_ids):
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        values = []
        for component_id in component_ids:
            item, offset = _read_frame(payload, offset)
            values.append(
                _decode_typed_payload_view(
                    component_id,
                    item,
                    types,
                )
            )
        if offset != len(payload):
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        return ("tuple", tuple(values))
    if kind_id == "keyed-table":
        rows = []
        keys = set()
        row_type = types[row["row_tuple_type_id"]]
        indices = row["ordered_key_component_indices"]
        for _ in range(count):
            item, offset = _read_frame(payload, offset)
            decoded_row = _decode_typed_payload_view(
                row["row_tuple_type_id"],
                item,
                types,
            )
            if (
                row_type["type_kind_id"] != "tuple"
                or decoded_row[0] != "tuple"
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
                )
            key = tuple(decoded_row[1][index] for index in indices)
            if key in keys:
                _reject(
                    PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
                )
            keys.add(key)
            rows.append(decoded_row)
        if offset != len(payload):
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        return ("keyed-table", tuple(rows))
    if kind_id == "u64-interval-sequence":
        endpoint_id = row["endpoint_u64_type_id"]
        intervals = []
        for _ in range(count):
            start_raw, offset = _read_frame(payload, offset)
            end_raw, offset = _read_frame(payload, offset)
            start = _decode_typed_payload_view(
                endpoint_id,
                start_raw,
                types,
            )
            end = _decode_typed_payload_view(
                endpoint_id,
                end_raw,
                types,
            )
            if start > end:
                _reject(
                    PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
                )
            intervals.append((start, end))
        if offset != len(payload):
            _reject(
                PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
            )
        return ("u64-interval-sequence", tuple(intervals))
    _reject(PortablePredicateProgramFormulaCode.INTERNAL)


def _decode_payload_hex(
    type_id: str,
    value: object,
    types: dict,
) -> object:
    if (
        not _runtime._is_payload_hex(value)
        or len(value) // 2 > _MAXIMUM_TYPED_PAYLOAD_BYTES
    ):
        _reject(
            PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
        )
    try:
        payload = bytes.fromhex(value)
    except (TypeError, ValueError):
        _reject(
            PortablePredicateProgramFormulaCode.TYPED_PAYLOAD_INVALID
        )
    return _decode_typed_payload(type_id, payload, types)


def _profile_field_value_is_valid(schema_id: str, value: object) -> bool:
    if schema_id == "strict-identifier-string-v1":
        return _runtime._is_identifier(value)
    if schema_id == "lowercase-sha256-string-v1":
        return _runtime._is_sha256(value)
    if schema_id == "nonnegative-index-or-count-integer-v1":
        return (
            type(value) is int
            and 0 <= value <= _MAXIMUM_COLLECTION_ITEMS
        )
    if schema_id == "ordered-identifier-array-v1":
        return (
            type(value) is list
            and len(value) <= _MAXIMUM_COLLECTION_ITEMS
            and all(_runtime._is_identifier(item) for item in value)
        )
    if schema_id == "ordered-exact-object-row-array-v1":
        return (
            type(value) is list
            and len(value) <= _MAXIMUM_COLLECTION_ITEMS
            and all(type(item) is dict for item in value)
        )
    _reject(PortablePredicateProgramFormulaCode.INTERNAL)


def _select_and_validate_purpose(
    program_tree: dict,
    profile_tree: dict,
) -> tuple:
    purpose_id = program_tree["program_purpose_id"]
    rows = [
        row
        for row in profile_tree["program_purpose_rows"]
        if row["program_purpose_id"] == purpose_id
    ]
    if len(rows) != 1:
        _reject(
            PortablePredicateProgramFormulaCode.PURPOSE_BINDING_INVALID
        )
    purpose = rows[0]
    binding = program_tree["purpose_binding"]
    if not _exact_keys(
        binding,
        tuple(purpose["exact_binding_field_ids"]),
    ):
        _reject(
            PortablePredicateProgramFormulaCode.PURPOSE_BINDING_INVALID
        )
    field_rows = {
        row["field_id"]: row
        for row in profile_tree["profile_field_schema_rows"]
    }
    domain_rows = {
        row["artifact_role_id"]: row
        for row in profile_tree["artifact_domain_rows"]
    }
    anchor_rows = {
        row["anchor_role_id"]: row
        for row in profile_tree["anchor_contract_rows"]
    }
    for field_id in purpose["exact_binding_field_ids"]:
        field_row = field_rows.get(field_id)
        if (
            field_row is None
            or not _profile_field_value_is_valid(
                field_row["value_schema_id"],
                binding[field_id],
            )
        ):
            _reject(
                PortablePredicateProgramFormulaCode.PURPOSE_BINDING_INVALID
            )
        role_id = field_row["semantic_role_id"]
        parameter_id = field_row["role_parameter_id"]
        value = binding[field_id]
        if role_id == "opaque-identifier":
            continue
        if role_id == "artifact-type-for-role":
            domain = domain_rows.get(parameter_id)
            valid = domain is not None and value == domain["artifact_type_id"]
        elif role_id == "artifact-identity-semantics-for-role":
            domain = domain_rows.get(parameter_id)
            valid = (
                domain is not None
                and value == domain["identity_semantics_id"]
            )
        elif role_id == "artifact-identity-sha256-for-role":
            valid = parameter_id in domain_rows
        elif role_id == "anchor-artifact-type-for-role":
            anchor = anchor_rows.get(parameter_id)
            valid = (
                anchor is not None
                and value == anchor["artifact_type_id"]
            )
        elif role_id == "anchor-contract-sha256-for-role":
            anchor = anchor_rows.get(parameter_id)
            valid = (
                anchor is not None
                and value == anchor["contract_sha256"]
            )
        elif role_id == "ordered-unique-identifiers":
            valid = len(value) == len(set(value))
        elif role_id == "identifier-member-of-purpose-field":
            target = binding.get(parameter_id)
            valid = type(target) is list and value in target
        elif role_id == "nonnegative-count":
            valid = True
        elif role_id == "index-below-field":
            target = binding.get(parameter_id)
            valid = (
                type(target) is int
                and type(value) is int
                and 0 <= value < target
            )
        elif role_id in {
            "locator-kind-self",
            "path-segments",
            "typed-key-components",
            "prior-input-resolved-operand",
        }:
            valid = False
        else:
            valid = False
        if not valid:
            _reject(
                PortablePredicateProgramFormulaCode.PURPOSE_BINDING_INVALID
            )
    return (purpose, binding, field_rows)


def _required_anchor_roles(purpose: dict) -> tuple:
    result = []
    for relation in purpose["purpose_relation_rows"]:
        if relation["relation_primitive_id"] == (
            "exactly-one-pinned-anchor-row-canonical-equality-v1"
        ):
            role_id = relation["anchor_role_id"]
            if role_id not in result:
                result.append(role_id)
    return tuple(result)


def _validate_anchor_bundle(
    anchor_snapshot: tuple,
    required_roles: tuple,
    profile_tree: dict,
) -> dict:
    actual_roles = tuple(row[0] for row in anchor_snapshot)
    if (
        actual_roles != required_roles
        or len(actual_roles) != len(set(actual_roles))
        or any(not _runtime._is_identifier(role) for role in actual_roles)
    ):
        _reject(
            PortablePredicateProgramFormulaCode.ANCHOR_BUNDLE_INVALID
        )
    pinned = {
        row["anchor_role_id"]: row
        for row in profile_tree["anchor_contract_rows"]
    }
    result = {}
    for role_id, raw in anchor_snapshot:
        row = pinned.get(role_id)
        if row is None:
            _reject(
                PortablePredicateProgramFormulaCode.ANCHOR_BUNDLE_INVALID
            )
        tree = _strict_runtime_tree(
            raw,
            resource_code=(
                PortablePredicateProgramFormulaCode.ANCHOR_INPUT_RESOURCE
            ),
            json_code=PortablePredicateProgramFormulaCode.ANCHOR_JSON_INVALID,
            tree_code=(
                PortablePredicateProgramFormulaCode.ANCHOR_JSON_TREE_INVALID
            ),
            canonical_code=(
                PortablePredicateProgramFormulaCode.ANCHOR_CANONICAL_MISMATCH
            ),
        )
        if (
            type(tree) is not dict
            or not _runtime._is_identifier(tree.get("artifact_type"))
            or tree["artifact_type"] != row["artifact_type_id"]
            or _runtime._domain_sha256(row["artifact_type_id"], raw)
            != row["contract_sha256"]
        ):
            _reject(
                PortablePredicateProgramFormulaCode.ANCHOR_BINDING_MISMATCH
            )
        result[role_id] = tree
    return result


def _validate_key_component_rows(
    value: object,
    types: dict,
) -> None:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 4
    ):
        _reject(PortablePredicateProgramFormulaCode.LOCATOR_INVALID)
    for row in value:
        if (
            not _exact_keys(
                row,
                (
                    "key_field_id",
                    "key_type_id",
                    "key_value_bytes_hex",
                ),
            )
            or not _runtime._is_identifier(row["key_field_id"])
            or not _runtime._is_identifier(row["key_type_id"])
            or row["key_type_id"] not in types
        ):
            _reject(PortablePredicateProgramFormulaCode.LOCATOR_INVALID)
        try:
            _decode_payload_hex(
                row["key_type_id"],
                row["key_value_bytes_hex"],
                types,
            )
        except PortablePredicateProgramFormulaError as error:
            if error.code == (
                PortablePredicateProgramFormulaCode
                .TYPED_PAYLOAD_INVALID
                .value
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.LOCATOR_INVALID
                )
            raise


def _validate_path_segments(
    value: object,
    types: dict,
    *,
    nonempty: bool,
    maximum_segments: int,
) -> None:
    if (
        type(value) is not list
        or (nonempty and not value)
        or len(value) > maximum_segments
    ):
        _reject(PortablePredicateProgramFormulaCode.LOCATOR_INVALID)
    for segment in value:
        if type(segment) is not dict:
            _reject(PortablePredicateProgramFormulaCode.LOCATOR_INVALID)
        kind_id = segment.get("segment_kind_id")
        if kind_id == "object-key":
            if (
                not _exact_keys(
                    segment,
                    ("segment_kind_id", "object_key"),
                )
                or not _runtime._is_identifier(segment["object_key"])
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.LOCATOR_INVALID
                )
        elif kind_id == "list-index":
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
                or not 0
                <= segment["list_index"]
                < segment["expected_list_count"]
                <= _MAXIMUM_COLLECTION_ITEMS
                or not _runtime._is_sha256(
                    segment["list_order_contract_sha256"]
                )
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.LOCATOR_INVALID
                )
        elif kind_id == "declared-keyed-list-item":
            if not _exact_keys(
                segment,
                ("segment_kind_id", "ordered_key_component_rows"),
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.LOCATOR_INVALID
                )
            _validate_key_component_rows(
                segment["ordered_key_component_rows"],
                types,
            )
        else:
            _reject(PortablePredicateProgramFormulaCode.LOCATOR_INVALID)


def _select_locator_row(
    locator: dict,
    profile_tree: dict,
    profile_fields: dict,
) -> dict:
    shape = set(locator)
    candidates = [
        row
        for row in profile_tree["locator_extension_rows"]
        if set(row["exact_configuration_field_ids"]) == shape
    ]
    if len(candidates) > 1:
        candidates = [
            row
            for row in candidates
            if all(
                locator[field_id] == row["locator_kind_id"]
                for field_id in row["exact_configuration_field_ids"]
                if profile_fields[field_id]["semantic_role_id"]
                == "locator-kind-self"
            )
        ]
    if len(candidates) != 1:
        _reject(PortablePredicateProgramFormulaCode.LOCATOR_INVALID)
    return candidates[0]


def _validate_locator(
    locator: object,
    *,
    profile_tree: dict,
    profile_fields: dict,
    purpose_binding: dict,
    types: dict,
    prior_operands: dict,
    limits: dict,
) -> dict:
    if type(locator) is not dict or not locator:
        _reject(PortablePredicateProgramFormulaCode.LOCATOR_INVALID)
    selected = _select_locator_row(
        locator,
        profile_tree,
        profile_fields,
    )
    domain_rows = {
        row["artifact_role_id"]: row
        for row in profile_tree["artifact_domain_rows"]
    }
    anchor_rows = {
        row["anchor_role_id"]: row
        for row in profile_tree["anchor_contract_rows"]
    }
    for field_id in selected["exact_configuration_field_ids"]:
        field_row = profile_fields.get(field_id)
        if (
            field_row is None
            or not _profile_field_value_is_valid(
                field_row["value_schema_id"],
                locator[field_id],
            )
        ):
            _reject(PortablePredicateProgramFormulaCode.LOCATOR_INVALID)
        role_id = field_row["semantic_role_id"]
        parameter_id = field_row["role_parameter_id"]
        value = locator[field_id]
        if role_id == "opaque-identifier":
            valid = True
        elif role_id == "artifact-type-for-role":
            target = domain_rows.get(parameter_id)
            valid = (
                target is not None
                and value == target["artifact_type_id"]
            )
        elif role_id == "artifact-identity-semantics-for-role":
            target = domain_rows.get(parameter_id)
            valid = (
                target is not None
                and value == target["identity_semantics_id"]
            )
        elif role_id == "artifact-identity-sha256-for-role":
            valid = parameter_id in domain_rows
        elif role_id == "anchor-artifact-type-for-role":
            target = anchor_rows.get(parameter_id)
            valid = (
                target is not None
                and value == target["artifact_type_id"]
            )
        elif role_id == "anchor-contract-sha256-for-role":
            target = anchor_rows.get(parameter_id)
            valid = (
                target is not None
                and value == target["contract_sha256"]
            )
        elif role_id == "identifier-member-of-purpose-field":
            target = purpose_binding.get(parameter_id)
            valid = type(target) is list and value in target
        elif role_id == "locator-kind-self":
            valid = value == selected["locator_kind_id"]
        elif role_id in {
            "path-segments",
            "nonnegative-count",
            "index-below-field",
            "typed-key-components",
            "prior-input-resolved-operand",
        }:
            valid = True
        else:
            valid = False
        if not valid:
            _reject(PortablePredicateProgramFormulaCode.LOCATOR_INVALID)
    for field_id in selected["exact_empty_placeholder_field_ids"]:
        if locator[field_id] != []:
            _reject(PortablePredicateProgramFormulaCode.LOCATOR_INVALID)
    for field_id in selected["exact_configuration_field_ids"]:
        field_row = profile_fields[field_id]
        role_id = field_row["semantic_role_id"]
        value = locator[field_id]
        if role_id == "path-segments" and field_id not in (
            selected["exact_empty_placeholder_field_ids"]
        ):
            _validate_path_segments(
                value,
                types,
                nonempty=True,
                maximum_segments=limits["locator_segments"],
            )
        elif role_id == "index-below-field":
            target = locator.get(field_row["role_parameter_id"])
            if not (
                type(target) is int
                and type(value) is int
                and 0 <= value < target
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.LOCATOR_INVALID
                )
        elif role_id == "typed-key-components":
            _validate_key_component_rows(value, types)
        elif role_id == "prior-input-resolved-operand":
            prior = prior_operands.get(value)
            if (
                prior is None
                or prior["value_source_kind_id"] != "INPUT_RESOLVED"
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.LOCATOR_INVALID
                )
    primitive_id = selected["locator_primitive_id"]
    if primitive_id == "bounded-artifact-path":
        path_fields = [
            field_id
            for field_id in selected["exact_configuration_field_ids"]
            if profile_fields[field_id]["semantic_role_id"]
            == "path-segments"
        ]
        if len(path_fields) != 1:
            _reject(PortablePredicateProgramFormulaCode.INTERNAL)
    elif primitive_id == "direct-bound-value":
        pass
    elif primitive_id == "ordered-index":
        pass
    elif primitive_id == "composite-key":
        pass
    elif primitive_id == "sibling-resolved-value":
        pass
    else:
        _reject(PortablePredicateProgramFormulaCode.INTERNAL)
    return selected


def _ordered_authorities_valid(
    values: object,
    declared_authorities: list,
    *,
    nonempty: bool,
) -> bool:
    if (
        type(values) is not list
        or (nonempty and not values)
        or any(type(value) is not str for value in values)
        or len(values) != len(set(values))
    ):
        return False
    indices = []
    by_id = {
        authority_id: index
        for index, authority_id in enumerate(declared_authorities)
    }
    for value in values:
        if value not in by_id:
            return False
        indices.append(by_id[value])
    return indices == sorted(indices)


def _parse_operand_registry(
    rows: object,
    *,
    types: dict,
    profile_tree: dict,
    profile_fields: dict,
    purpose_binding: dict,
    limits: dict,
) -> tuple:
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
    if type(rows) is not list or len(rows) > limits["operand_rows"]:
        _reject(
            PortablePredicateProgramFormulaCode.OPERAND_REGISTRY_INVALID
        )
    for row in rows:
        if (
            not _exact_keys(row, exact_fields)
            or not _runtime._is_identifier(row["operand_id"])
            or not _runtime._is_identifier(row["type_id"])
            or not _runtime._is_identifier(
                row["value_source_kind_id"]
            )
            or not _runtime._is_identifier(
                row["resolution_requirement_id"]
            )
            or type(row["ordered_authority_class_ids"]) is not list
            or any(
                not _runtime._is_identifier(item)
                for item in row["ordered_authority_class_ids"]
            )
            or type(row["locator"]) is not dict
            or type(row["literal_value_bytes_hex"]) is not str
            or not _runtime._is_empty_or_identifier(
                row["source_shaping_node_id"]
            )
        ):
            _reject(
                PortablePredicateProgramFormulaCode.OPERAND_REGISTRY_INVALID
            )
    declared_operand_ids = [row["operand_id"] for row in rows]
    if len(declared_operand_ids) != len(set(declared_operand_ids)):
        _reject(
            PortablePredicateProgramFormulaCode.OPERAND_REGISTRY_INVALID
        )
    operands = {}
    input_ids = []
    derived_ids = []
    declared_authorities = profile_tree["authority_class_ids"]
    for index, row in enumerate(rows):
        if row["type_id"] not in types:
            _reject(
                PortablePredicateProgramFormulaCode.OPERAND_REGISTRY_INVALID
            )
        kind_id = row["value_source_kind_id"]
        if kind_id == "INPUT_RESOLVED":
            if (
                row["resolution_requirement_id"]
                not in {
                    "REQUIRED_RUNTIME_FAIL",
                    "REQUIRED_EXTERNAL_NOT_EVALUATED",
                }
                or not _ordered_authorities_valid(
                    row["ordered_authority_class_ids"],
                    declared_authorities,
                    nonempty=True,
                )
                or not row["locator"]
                or row["literal_value_bytes_hex"] != ""
                or row["source_shaping_node_id"] != ""
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.OPERAND_REGISTRY_INVALID
                )
            input_ids.append(row["operand_id"])
        elif kind_id == "PROGRAM_LITERAL":
            if (
                row["resolution_requirement_id"] != "STATIC_CONTRACT"
                or row["ordered_authority_class_ids"] != []
                or row["locator"] != {}
                or row["source_shaping_node_id"] != ""
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.OPERAND_REGISTRY_INVALID
                )
        elif kind_id == "DERIVED_TYPED_VALUE":
            if (
                row["resolution_requirement_id"] != "STATIC_CONTRACT"
                or not _ordered_authorities_valid(
                    row["ordered_authority_class_ids"],
                    declared_authorities,
                    nonempty=False,
                )
                or row["locator"] != {}
                or row["literal_value_bytes_hex"] != ""
                or not _runtime._is_identifier(
                    row["source_shaping_node_id"]
                )
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.OPERAND_REGISTRY_INVALID
                )
            derived_ids.append(row["operand_id"])
        else:
            _reject(
                PortablePredicateProgramFormulaCode.OPERAND_REGISTRY_INVALID
            )
        copied = dict(row)
        copied["_declaration_index"] = index
        operands[row["operand_id"]] = copied
    literal_values = {}
    for row in rows:
        if row["value_source_kind_id"] == "PROGRAM_LITERAL":
            literal_values[row["operand_id"]] = _decode_payload_hex(
                row["type_id"],
                row["literal_value_bytes_hex"],
                types,
            )
    prior_input_operands = {}
    for row in rows:
        if row["value_source_kind_id"] != "INPUT_RESOLVED":
            continue
        _validate_locator(
            row["locator"],
            profile_tree=profile_tree,
            profile_fields=profile_fields,
            purpose_binding=purpose_binding,
            types=types,
            prior_operands=prior_input_operands,
            limits=limits,
        )
        prior_input_operands[row["operand_id"]] = operands[
            row["operand_id"]
        ]
    return (
        operands,
        literal_values,
        tuple(row["operand_id"] for row in rows),
        tuple(input_ids),
        tuple(derived_ids),
    )


def _validate_constructor_relation(
    constructor_id: str,
    configuration: dict,
    input_ids: list,
    output_id: str,
    operands: dict,
    types: dict,
) -> None:
    input_types = [operands[item]["type_id"] for item in input_ids]
    output_type_id = operands[output_id]["type_id"]
    output_type = types[output_type_id]
    valid = False
    if constructor_id == "make-optional-none":
        valid = output_type["type_kind_id"] == "optional"
    elif constructor_id == "make-optional-some":
        valid = (
            output_type["type_kind_id"] == "optional"
            and output_type["item_type_id"] == input_types[0]
        )
    elif constructor_id == "require-optional-present":
        input_type = types[input_types[0]]
        valid = (
            input_type["type_kind_id"] == "optional"
            and input_type["item_type_id"] == output_type_id
        )
    elif constructor_id == "make-sequence":
        valid = (
            output_type["type_kind_id"] == "sequence"
            and all(
                item == output_type["item_type_id"]
                for item in input_types
            )
        )
    elif constructor_id == "make-tuple":
        valid = (
            output_type["type_kind_id"] == "tuple"
            and output_type["ordered_component_type_ids"] == input_types
        )
    elif constructor_id == "make-keyed-table":
        valid = (
            output_type["type_kind_id"] == "keyed-table"
            and all(
                item == output_type["row_tuple_type_id"]
                for item in input_types
            )
        )
    elif constructor_id == "make-u64-interval-sequence":
        valid = (
            output_type["type_kind_id"] == "u64-interval-sequence"
            and len(input_types) % 2 == 0
            and all(
                item == output_type["endpoint_u64_type_id"]
                for item in input_types
            )
        )
    elif constructor_id == "project-tuple-component":
        input_type = types[input_types[0]]
        index = configuration["component_index"]
        valid = (
            input_type["type_kind_id"] == "tuple"
            and type(index) is int
            and 0 <= index < len(input_type["ordered_component_type_ids"])
            and output_type_id
            == input_type["ordered_component_type_ids"][index]
        )
    elif constructor_id == "project-keyed-table-column":
        input_type = types[input_types[0]]
        index = configuration["component_index"]
        if input_type["type_kind_id"] == "keyed-table":
            row_type = types[input_type["row_tuple_type_id"]]
            valid = (
                type(index) is int
                and 0
                <= index
                < len(row_type["ordered_component_type_ids"])
                and output_type["type_kind_id"] == "sequence"
                and output_type["item_type_id"]
                == row_type["ordered_component_type_ids"][index]
            )
    elif constructor_id == "project-keyed-table-keys":
        input_type = types[input_types[0]]
        valid = (
            input_type["type_kind_id"] == "keyed-table"
            and output_type["type_kind_id"] == "sequence"
            and output_type["item_type_id"]
            == input_type["key_tuple_type_id"]
        )
    elif constructor_id == "select-keyed-table-row":
        table_type = types[input_types[0]]
        valid = (
            table_type["type_kind_id"] == "keyed-table"
            and input_types[1] == table_type["key_tuple_type_id"]
            and output_type_id == table_type["row_tuple_type_id"]
        )
    elif constructor_id == "canonical-sort-keyed-table":
        valid = (
            types[input_types[0]]["type_kind_id"] == "keyed-table"
            and input_types[0] == output_type_id
        )
    else:
        _reject(PortablePredicateProgramFormulaCode.INTERNAL)
    if not valid:
        _reject(PortablePredicateProgramFormulaCode.TYPE_RELATION_INVALID)


def _parse_shaping_registry(
    rows: object,
    *,
    operands: dict,
    types: dict,
    profile_tree: dict,
    limits: dict,
) -> tuple:
    if type(rows) is not list or len(rows) > limits["shaping_nodes"]:
        _reject(
            PortablePredicateProgramFormulaCode.SHAPING_REGISTRY_INVALID
        )
    core_tree = _core.portable_predicate_language_core_contract_tree()
    constructor_rows = {
        row["constructor_id"]: row
        for row in core_tree["constructor_contract"]["constructor_rows"]
    }
    exact_fields = tuple(
        core_tree["program_contract"]["shaping_node_exact_field_ids"]
    )
    for row in rows:
        if (
            not _exact_keys(row, exact_fields)
            or not _runtime._is_identifier(row["shaping_node_id"])
            or not _runtime._is_identifier(row["constructor_id"])
            or not _runtime._is_identifier(row["output_operand_id"])
            or type(row["ordered_input_operand_ids"]) is not list
            or len(row["ordered_input_operand_ids"])
            > limits["node_fanout"]
            or any(
                not _runtime._is_identifier(item)
                for item in row["ordered_input_operand_ids"]
            )
            or type(row["constructor_configuration"]) is not dict
            or not _runtime._is_identifier(row["applicability_id"])
            or not _runtime._is_identifier(row["failure_oracle_id"])
        ):
            _reject(
                PortablePredicateProgramFormulaCode.SHAPING_REGISTRY_INVALID
            )
    declared_node_ids = [row["shaping_node_id"] for row in rows]
    if len(declared_node_ids) != len(set(declared_node_ids)):
        _reject(
            PortablePredicateProgramFormulaCode.SHAPING_REGISTRY_INVALID
        )
    if any(
        row["constructor_id"] not in constructor_rows
        or row["applicability_id"] != "ALWAYS"
        or row["failure_oracle_id"]
        != "FAIL_CLOSED_FOUR_DISPOSITION_V1"
        for row in rows
    ):
        _reject(
            PortablePredicateProgramFormulaCode.SHAPING_REGISTRY_INVALID
        )
    derived_ids = {
        operand_id
        for operand_id, operand in operands.items()
        if operand["value_source_kind_id"] == "DERIVED_TYPED_VALUE"
    }
    declared_authorities = profile_tree["authority_class_ids"]
    validated_outputs = set()
    validated_nodes = set()
    for row in rows:
        node_id = row["shaping_node_id"]
        output_id = row["output_operand_id"]
        input_ids = row["ordered_input_operand_ids"]
        constructor = constructor_rows[row["constructor_id"]]
        if (
            output_id not in derived_ids
            or output_id in validated_outputs
            or any(item not in operands for item in input_ids)
            or not constructor["minimum_input_count"]
            <= len(input_ids)
            <= constructor["maximum_input_count"]
            or operands[output_id]["source_shaping_node_id"] != node_id
            or any(
                operands[item]["_declaration_index"]
                >= operands[output_id]["_declaration_index"]
                for item in input_ids
            )
            or any(
                operands[item]["value_source_kind_id"]
                == "DERIVED_TYPED_VALUE"
                and operands[item]["source_shaping_node_id"]
                not in validated_nodes
                for item in input_ids
            )
        ):
            _reject(
                PortablePredicateProgramFormulaCode.SHAPING_REGISTRY_INVALID
            )
        validated_outputs.add(output_id)
        validated_nodes.add(node_id)
    if validated_outputs != derived_ids:
        _reject(
            PortablePredicateProgramFormulaCode.SHAPING_REGISTRY_INVALID
        )
    for row in rows:
        authority_set = {
            authority_id
            for input_id in row["ordered_input_operand_ids"]
            for authority_id in operands[input_id][
                "ordered_authority_class_ids"
            ]
        }
        expected_authorities = [
            authority_id
            for authority_id in declared_authorities
            if authority_id in authority_set
        ]
        if (
            operands[row["output_operand_id"]][
                "ordered_authority_class_ids"
            ]
            != expected_authorities
        ):
            _reject(
                PortablePredicateProgramFormulaCode.OPERAND_REGISTRY_INVALID
            )
    producers = {}
    shaping = {}
    depths = {}
    dependencies = {}
    reference_count = 0
    for row in rows:
        node_id = row["shaping_node_id"]
        output_id = row["output_operand_id"]
        input_ids = row["ordered_input_operand_ids"]
        constructor = constructor_rows[row["constructor_id"]]
        if (
            output_id not in derived_ids
            or output_id in producers
            or any(item not in operands for item in input_ids)
            or not constructor["minimum_input_count"]
            <= len(input_ids)
            <= constructor["maximum_input_count"]
            or len(input_ids) > limits["node_fanout"]
            or operands[output_id]["source_shaping_node_id"] != node_id
            or any(
                operands[item]["_declaration_index"]
                >= operands[output_id]["_declaration_index"]
                for item in input_ids
            )
        ):
            _reject(
                PortablePredicateProgramFormulaCode.SHAPING_REGISTRY_INVALID
            )
        expected_configuration = tuple(
            constructor["exact_configuration_field_ids"]
        )
        if not _exact_keys(
            row["constructor_configuration"],
            expected_configuration,
        ):
            _reject(
                PortablePredicateProgramFormulaCode.TYPE_RELATION_INVALID
            )
        producer_dependencies = []
        for input_id in input_ids:
            input_operand = operands[input_id]
            if input_operand["value_source_kind_id"] == (
                "DERIVED_TYPED_VALUE"
            ):
                producer_id = input_operand["source_shaping_node_id"]
                if producer_id not in shaping:
                    _reject(
                        PortablePredicateProgramFormulaCode.SHAPING_REGISTRY_INVALID
                    )
                producer_dependencies.append(producer_id)
        authority_set = {
            authority_id
            for input_id in input_ids
            for authority_id in operands[input_id][
                "ordered_authority_class_ids"
            ]
        }
        expected_authorities = [
            authority_id
            for authority_id in declared_authorities
            if authority_id in authority_set
        ]
        if (
            operands[output_id]["ordered_authority_class_ids"]
            != expected_authorities
        ):
            _reject(
                PortablePredicateProgramFormulaCode.OPERAND_REGISTRY_INVALID
            )
        _validate_constructor_relation(
            row["constructor_id"],
            row["constructor_configuration"],
            input_ids,
            output_id,
            operands,
            types,
        )
        depth = 1 + max(
            (depths[item] for item in producer_dependencies),
            default=0,
        )
        reference_count += len(input_ids)
        producers[output_id] = node_id
        shaping[node_id] = row
        depths[node_id] = depth
        dependencies[node_id] = tuple(producer_dependencies)
    if set(producers) != derived_ids:
        _reject(
            PortablePredicateProgramFormulaCode.SHAPING_REGISTRY_INVALID
        )
    return (
        shaping,
        producers,
        depths,
        dependencies,
        tuple(row["shaping_node_id"] for row in rows),
        reference_count,
    )


def _operator_type_relation_valid(
    operator_id: str,
    operand_ids: list,
    operands: dict,
    types: dict,
    literal_values: dict,
) -> bool:
    type_ids = [operands[item]["type_id"] for item in operand_ids]
    type_rows = [types[item] for item in type_ids]
    if operator_id == "absence":
        return type_rows[0]["type_kind_id"] == "optional"
    if operator_id == "all-distinct":
        return type_rows[0]["type_kind_id"] == "sequence"
    if operator_id in {
        "boolean-is",
        "u64-equal",
        "token-equal",
        "octets-equal",
        "sha256-equal",
    }:
        expected_kind = {
            "boolean-is": "boolean",
            "u64-equal": "u64",
            "token-equal": "token",
            "octets-equal": "octets",
            "sha256-equal": "sha256",
        }[operator_id]
        return (
            type_ids[0] == type_ids[1]
            and type_rows[0]["type_kind_id"] == expected_kind
        )
    if operator_id == "count-equal":
        return (
            type_rows[0]["type_kind_id"] in {"sequence", "keyed-table"}
            and type_rows[1]["type_kind_id"] == "u64"
            and type_rows[1]["unit_id"] == "collection-item-count"
        )
    if operator_id == "digest-derived-from-bytes":
        return (
            type_rows[0]["type_kind_id"] == "octets"
            and type_rows[1]["type_kind_id"] == "sha256"
            and type_rows[1]["digest_semantics_id"] == "PLAIN_SHA256"
        )
    if operator_id == "domain-digest-derived-from-bytes":
        return (
            type_rows[0]["type_kind_id"] == "octets"
            and type_rows[1]["type_kind_id"] == "sha256"
            and type_rows[1]["digest_semantics_id"]
            == "DOMAIN_SEPARATED_SHA256"
        )
    if operator_id == "integer-sum-equal":
        return (
            type_rows[0]["type_kind_id"] == "sequence"
            and type_rows[1]["type_kind_id"] == "u64"
            and type_rows[0]["item_type_id"] == type_ids[1]
        )
    if operator_id == "interval-order":
        return type_rows[0]["type_kind_id"] == "u64-interval-sequence"
    if operator_id == "octets-equal":
        return (
            type_ids[0] == type_ids[1]
            and type_rows[0]["type_kind_id"] == "octets"
        )
    if operator_id == "ordered-sequence-equal":
        return (
            type_ids[0] == type_ids[1]
            and type_rows[0]["type_kind_id"]
            in {"sequence", "keyed-table"}
        )
    if operator_id in {"set-equal", "set-subset"}:
        return (
            type_rows[0]["type_kind_id"] == "sequence"
            and type_rows[1]["type_kind_id"] == "sequence"
            and type_rows[0]["item_type_id"]
            == type_rows[1]["item_type_id"]
        )
    if operator_id == "reference-resolves":
        return (
            type_rows[0]["type_kind_id"] == "sequence"
            and type_rows[1]["type_kind_id"] == "keyed-table"
            and type_rows[0]["item_type_id"]
            == type_rows[1]["key_tuple_type_id"]
        )
    if operator_id == "member-of-frozen-program-set":
        if (
            type_rows[1]["type_kind_id"] != "sequence"
            or type_rows[1]["item_type_id"] != type_ids[0]
            or operands[operand_ids[1]]["value_source_kind_id"]
            != "PROGRAM_LITERAL"
        ):
            return False
        value = literal_values.get(operand_ids[1])
        return (
            type(value) is tuple
            and len(value) == 2
            and value[0] == "sequence"
            and bool(value[1])
            and len(value[1]) == len(set(value[1]))
        )
    if operator_id in {"all", "any", "not"}:
        return not operand_ids
    return False


def _specialization_type_is_valid(
    specialization: dict,
    operand_type_id: str,
    types: dict,
    profile_tree: dict,
) -> bool:
    parameter_by_slot = {
        row["parameter_slot_id"]: row["parameter_value_id"]
        for row in profile_tree["profile_parameter_rows"]
    }
    expected_domains = [
        parameter_by_slot[item]
        for item in specialization["ordered_parameter_slot_ids"]
    ]
    operand_type = types[operand_type_id]
    if len(expected_domains) == 1:
        return (
            operand_type["type_kind_id"] == "token"
            and operand_type["token_domain_id"] == expected_domains[0]
        )
    if operand_type["type_kind_id"] != "tuple":
        return False
    component_ids = operand_type["ordered_component_type_ids"]
    return (
        len(component_ids) == len(expected_domains)
        and all(
            types[component_id]["type_kind_id"] == "token"
            and types[component_id]["token_domain_id"] == expected_domain
            for component_id, expected_domain in zip(
                component_ids,
                expected_domains,
            )
        )
    )


def _parse_predicate_registry(
    rows: object,
    *,
    operands: dict,
    types: dict,
    literal_values: dict,
    shaping: dict,
    shaping_depths: dict,
    profile_tree: dict,
    limits: dict,
) -> tuple:
    if (
        type(rows) is not list
        or not rows
        or len(rows) > limits["predicate_nodes"]
    ):
        _reject(
            PortablePredicateProgramFormulaCode.PREDICATE_REGISTRY_INVALID
        )
    core_tree = _core.portable_predicate_language_core_contract_tree()
    core_operators = {
        row["operator_id"]: row
        for row in core_tree["operator_contract"]["operator_rows"]
    }
    specializations = {
        row["exposed_operator_id"]: row
        for row in profile_tree["operator_specialization_rows"]
    }
    exact_fields = tuple(core_tree["program_contract"]["node_exact_field_ids"])
    for row in rows:
        if (
            not _exact_keys(row, exact_fields)
            or not _runtime._is_identifier(row["node_id"])
            or not _runtime._is_identifier(row["operator_id"])
            or type(row["ordered_operand_ids"]) is not list
            or type(row["ordered_child_node_ids"]) is not list
            or len(row["ordered_operand_ids"]) > limits["node_fanout"]
            or len(row["ordered_child_node_ids"]) > limits["node_fanout"]
            or any(
                not _runtime._is_identifier(item)
                for item in (
                    row["ordered_operand_ids"]
                    + row["ordered_child_node_ids"]
                )
            )
            or type(row["operator_configuration"]) is not dict
            or not _runtime._is_identifier(row["applicability_id"])
            or not _runtime._is_identifier(row["failure_oracle_id"])
        ):
            _reject(
                PortablePredicateProgramFormulaCode
                .PREDICATE_REGISTRY_INVALID
            )
    declared_node_ids = [row["node_id"] for row in rows]
    if (
        len(declared_node_ids) != len(set(declared_node_ids))
        or set(declared_node_ids).intersection(shaping)
    ):
        _reject(
            PortablePredicateProgramFormulaCode.PREDICATE_REGISTRY_INVALID
        )
    for row in rows:
        specialization = specializations.get(row["operator_id"])
        primitive_id = (
            specialization["primitive_id"]
            if specialization is not None
            else row["operator_id"]
        )
        operator = core_operators.get(primitive_id)
        if (
            operator is None
            or row["applicability_id"] != operator["applicability_id"]
            or row["failure_oracle_id"] != operator["failure_oracle_id"]
        ):
            _reject(
                PortablePredicateProgramFormulaCode
                .PREDICATE_REGISTRY_INVALID
            )
    validated_predicates = set()
    for row in rows:
        specialization = specializations.get(row["operator_id"])
        primitive_id = (
            specialization["primitive_id"]
            if specialization is not None
            else row["operator_id"]
        )
        operator = core_operators[primitive_id]
        operand_ids = row["ordered_operand_ids"]
        child_ids = row["ordered_child_node_ids"]
        if (
            len(operand_ids) != len(set(operand_ids))
            or len(child_ids) != len(set(child_ids))
            or any(item not in operands for item in operand_ids)
            or any(item not in validated_predicates for item in child_ids)
            or not operator["minimum_operand_count"]
            <= len(operand_ids)
            <= operator["maximum_operand_count"]
            or not operator["minimum_child_count"]
            <= len(child_ids)
            <= operator["maximum_child_count"]
            or len(operand_ids) + len(child_ids) > limits["node_fanout"]
        ):
            _reject(
                PortablePredicateProgramFormulaCode
                .PREDICATE_REGISTRY_INVALID
            )
        validated_predicates.add(row["node_id"])
    predicates = {}
    depths = {}
    dependencies = {}
    reference_count = 0
    for row in rows:
        operator_id = row.get("operator_id")
        specialization = (
            specializations.get(operator_id)
            if _runtime._is_identifier(operator_id)
            else None
        )
        primitive_id = (
            specialization["primitive_id"]
            if specialization is not None
            else operator_id
        )
        operator = (
            core_operators.get(primitive_id)
            if _runtime._is_identifier(primitive_id)
            else None
        )
        if (
            operator is None
            or len(row["ordered_operand_ids"])
            != len(set(row["ordered_operand_ids"]))
            or len(row["ordered_child_node_ids"])
            != len(set(row["ordered_child_node_ids"]))
            or row["applicability_id"] != operator["applicability_id"]
            or row["failure_oracle_id"] != operator["failure_oracle_id"]
        ):
            _reject(
                PortablePredicateProgramFormulaCode.PREDICATE_REGISTRY_INVALID
            )
        operand_ids = row["ordered_operand_ids"]
        child_ids = row["ordered_child_node_ids"]
        if (
            any(item not in operands for item in operand_ids)
            or any(item not in predicates for item in child_ids)
            or not operator["minimum_operand_count"]
            <= len(operand_ids)
            <= operator["maximum_operand_count"]
            or not operator["minimum_child_count"]
            <= len(child_ids)
            <= operator["maximum_child_count"]
            or len(operand_ids) + len(child_ids) > limits["node_fanout"]
        ):
            _reject(
                PortablePredicateProgramFormulaCode.PREDICATE_REGISTRY_INVALID
            )
        expected_configuration = tuple(
            operator["exact_configuration_field_ids"]
        )
        if not _exact_keys(
            row["operator_configuration"],
            expected_configuration,
        ):
            _reject(
                PortablePredicateProgramFormulaCode.TYPE_RELATION_INVALID
            )
        if primitive_id == "interval-order":
            interval_order_mode_id = row["operator_configuration"][
                "interval_order_mode_id"
            ]
            if (
                type(interval_order_mode_id) is not str
                or interval_order_mode_id
                not in {
                    "TOUCHING_ADMITTED",
                    "STRICTLY_SEPARATED",
                }
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.TYPE_RELATION_INVALID
                )
        if not _operator_type_relation_valid(
            primitive_id,
            operand_ids,
            operands,
            types,
            literal_values,
        ):
            _reject(
                PortablePredicateProgramFormulaCode.TYPE_RELATION_INVALID
            )
        if specialization is not None and not _specialization_type_is_valid(
            specialization,
            operands[operand_ids[0]]["type_id"],
            types,
            profile_tree,
        ):
            _reject(
                PortablePredicateProgramFormulaCode.PROFILE_EXTENSION_INVALID
            )
        producer_dependencies = [
            operands[operand_id]["source_shaping_node_id"]
            for operand_id in operand_ids
            if operands[operand_id]["value_source_kind_id"]
            == "DERIVED_TYPED_VALUE"
        ]
        dependency_depths = [
            depths[child_id] for child_id in child_ids
        ] + [
            shaping_depths[producer_id]
            for producer_id in producer_dependencies
        ]
        depth = 1 + max(dependency_depths, default=0)
        node_id = row["node_id"]
        predicates[node_id] = row
        depths[node_id] = depth
        dependencies[node_id] = (
            tuple(child_ids),
            tuple(producer_dependencies),
        )
        reference_count += len(operand_ids) + len(child_ids)
    return (
        predicates,
        depths,
        dependencies,
        tuple(row["node_id"] for row in rows),
        reference_count,
    )


def _validate_whole_graph(
    *,
    program_tree: dict,
    operands: dict,
    shaping: dict,
    shaping_dependencies: dict,
    predicate_dependencies: dict,
    predicate_depths: dict,
    reference_count: int,
    limits: dict,
) -> int:
    predicate_rows = program_tree["ordered_predicate_node_rows"]
    root_id = program_tree["root_node_id"]
    if (
        not _runtime._is_identifier(root_id)
        or not predicate_rows
        or root_id != predicate_rows[-1]["node_id"]
        or reference_count > limits["node_references"]
        or predicate_depths.get(root_id, limits["graph_depth"] + 1)
        > limits["graph_depth"]
    ):
        _reject(PortablePredicateProgramFormulaCode.GRAPH_INVALID)
    reached_predicates = set()
    reached_shaping = set()
    stack = [("predicate", root_id)]
    while stack:
        kind_id, node_id = stack.pop()
        if kind_id == "predicate":
            if node_id in reached_predicates:
                continue
            reached_predicates.add(node_id)
            child_ids, producer_ids = predicate_dependencies[node_id]
            stack.extend(("predicate", item) for item in child_ids)
            stack.extend(("shaping", item) for item in producer_ids)
        else:
            if node_id in reached_shaping:
                continue
            reached_shaping.add(node_id)
            stack.extend(
                ("shaping", item)
                for item in shaping_dependencies[node_id]
            )
    if reached_predicates != set(predicate_dependencies):
        _reject(PortablePredicateProgramFormulaCode.GRAPH_INVALID)
    if reached_shaping != set(shaping):
        _reject(PortablePredicateProgramFormulaCode.GRAPH_INVALID)
    used_operands = set()
    for node_id in reached_predicates:
        used_operands.update(
            next(
                row["ordered_operand_ids"]
                for row in predicate_rows
                if row["node_id"] == node_id
            )
        )
    for node_id in reached_shaping:
        row = shaping[node_id]
        used_operands.add(row["output_operand_id"])
        used_operands.update(row["ordered_input_operand_ids"])
    if used_operands != set(operands):
        _reject(PortablePredicateProgramFormulaCode.GRAPH_INVALID)
    return predicate_depths[root_id]


def _resolve_exact_object_path(value: object, path_ids: list) -> object:
    current = value
    for path_id in path_ids:
        if type(current) is not dict or path_id not in current:
            _reject(
                PortablePredicateProgramFormulaCode.PURPOSE_RELATION_UNSATISFIED
            )
        current = current[path_id]
    return current


def _validate_purpose_relations(
    *,
    purpose: dict,
    purpose_binding: dict,
    anchor_trees: dict,
    operands: dict,
) -> None:
    comparison_count = 0
    for relation in purpose["purpose_relation_rows"]:
        primitive_id = relation["relation_primitive_id"]
        if primitive_id == (
            "exactly-one-pinned-anchor-row-canonical-equality-v1"
        ):
            anchor = anchor_trees.get(relation["anchor_role_id"])
            if anchor is None:
                _reject(
                    PortablePredicateProgramFormulaCode.PURPOSE_RELATION_UNSATISFIED
                )
            rows = _resolve_exact_object_path(
                anchor,
                relation["anchor_row_array_path_ids"],
            )
            if type(rows) is not list or any(
                type(row) is not dict for row in rows
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.PURPOSE_RELATION_UNSATISFIED
                )
            match_count = 0
            for row in rows:
                matched = True
                for equality in relation["ordered_equality_rows"]:
                    comparison_count += 1
                    if (
                        comparison_count
                        > _MAXIMUM_PURPOSE_RELATION_COMPARISONS
                    ):
                        _reject(
                            PortablePredicateProgramFormulaCode
                            .PURPOSE_RELATION_UNSATISFIED
                        )
                    candidate = _resolve_exact_object_path(
                        row,
                        equality["anchor_row_value_path_ids"],
                    )
                    expected = purpose_binding[
                        equality["purpose_binding_field_id"]
                    ]
                    if not _same_exact(candidate, expected):
                        matched = False
                        break
                if matched:
                    match_count += 1
            if match_count != 1:
                _reject(
                    PortablePredicateProgramFormulaCode.PURPOSE_RELATION_UNSATISFIED
                )
        elif primitive_id == (
            "purpose-identifiers-exactly-covered-by-input-locators-v1"
        ):
            locator_field_id = relation["locator_value_field_id"]
            collected = []
            for operand in operands.values():
                if operand["value_source_kind_id"] != "INPUT_RESOLVED":
                    continue
                locator = operand["locator"]
                if locator_field_id in locator:
                    collected.append(locator[locator_field_id])
            expected = purpose_binding[
                relation["purpose_binding_field_id"]
            ]
            if (
                any(not _runtime._is_identifier(item) for item in collected)
                or set(collected) != set(expected)
            ):
                _reject(
                    PortablePredicateProgramFormulaCode.PURPOSE_RELATION_UNSATISFIED
                )
        else:
            _reject(PortablePredicateProgramFormulaCode.INTERNAL)


def _validate_nonclaims(
    program_tree: dict,
    profile_tree: dict,
) -> None:
    expected_ids = set(
        _core.PORTABLE_PREDICATE_LANGUAGE_CORE_FALSE_CLAIM_IDS
    ) | set(profile_tree["nonclaim_state"])
    claims = program_tree["nonclaim_state"]
    if (
        type(claims) is not dict
        or set(claims) != expected_ids
        or any(type(value) is not bool or value for value in claims.values())
    ):
        _reject(
            PortablePredicateProgramFormulaCode.NONCLAIM_STATE_INVALID
        )


def _construct_and_validate_formula(
    *,
    program_tree: dict,
    formula_bytes: bytes,
    formula_tree: dict,
    purpose: dict,
    purpose_binding: dict,
    profile_tree: dict,
    profile_fields: dict,
) -> tuple:
    formula_binding = _profile_binding(
        profile_tree,
        "predicate-formula-core",
    )
    projected = {
        "artifact_type": formula_binding["artifact_type_id"],
        "format_version": program_tree["format_version"],
        "semantic_core_contract_sha256": (
            program_tree["semantic_core_contract_sha256"]
        ),
        "profile_contract_sha256": (
            program_tree["profile_contract_sha256"]
        ),
        "ordered_type_rows": program_tree["ordered_type_rows"],
        "ordered_operand_rows": program_tree["ordered_operand_rows"],
        "ordered_shaping_node_rows": (
            program_tree["ordered_shaping_node_rows"]
        ),
        "ordered_predicate_node_rows": (
            program_tree["ordered_predicate_node_rows"]
        ),
        "root_node_id": program_tree["root_node_id"],
    }
    canonical = _runtime._canonical_json(projected)
    if len(canonical) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateProgramFormulaCode.FORMULA_INPUT_RESOURCE
        )
    if (
        formula_bytes != canonical
        or not _same_exact(formula_tree, projected)
    ):
        _reject(
            PortablePredicateProgramFormulaCode.FORMULA_PROJECTION_MISMATCH
        )
    formula_identity = _runtime._domain_sha256(
        formula_binding["digest_domain_id"],
        canonical,
    )
    if program_tree["formula_core_identity_sha256"] != formula_identity:
        _reject(
            PortablePredicateProgramFormulaCode.FORMULA_IDENTITY_MISMATCH
        )
    for field_id in purpose["exact_binding_field_ids"]:
        field_row = profile_fields[field_id]
        if field_row["role_parameter_id"] != "predicate-formula-core":
            continue
        role_id = field_row["semantic_role_id"]
        value = purpose_binding[field_id]
        if role_id == "artifact-type-for-role":
            expected = formula_binding["artifact_type_id"]
        elif role_id == "artifact-identity-semantics-for-role":
            expected = formula_binding["identity_semantics_id"]
        elif role_id == "artifact-identity-sha256-for-role":
            expected = formula_identity
        else:
            continue
        if value != expected:
            _reject(
                PortablePredicateProgramFormulaCode.FORMULA_IDENTITY_MISMATCH
            )
    return (canonical, formula_identity, formula_binding)


def _parse_portable_predicate_program_formula_pair_v1_impl(
    program_artifact_bytes: bytes,
    formula_core_artifact_bytes: bytes,
    *,
    compiled_profile: _runtime.CompiledPortablePredicateRuntimeProfileV1,
    anchor_contract_artifacts: tuple = (),
) -> PortablePredicateProgramFormulaPairV1:
    """Validate one canonical program and its exact formula-core projection."""

    if (
        type(program_artifact_bytes) is not bytes
        or type(formula_core_artifact_bytes) is not bytes
        or type(anchor_contract_artifacts) is not tuple
    ):
        _reject(PortablePredicateProgramFormulaCode.INPUT_TYPE)
    profile = _revalidate_profile(compiled_profile)
    _check_program_formula_resource_limits(
        program_artifact_bytes,
        formula_core_artifact_bytes,
    )
    if len(anchor_contract_artifacts) > _MAXIMUM_COLLECTION_ITEMS:
        _reject(
            PortablePredicateProgramFormulaCode.ANCHOR_INPUT_RESOURCE
        )
    anchor_snapshot = _snapshot_anchor_arguments(
        anchor_contract_artifacts
    )
    _check_anchor_resource_limits(anchor_snapshot)
    program_tree = _strict_runtime_tree(
        program_artifact_bytes,
        resource_code=(
            PortablePredicateProgramFormulaCode.PROGRAM_INPUT_RESOURCE
        ),
        json_code=PortablePredicateProgramFormulaCode.PROGRAM_JSON_INVALID,
        tree_code=(
            PortablePredicateProgramFormulaCode.PROGRAM_JSON_TREE_INVALID
        ),
        canonical_code=(
            PortablePredicateProgramFormulaCode.PROGRAM_CANONICAL_MISMATCH
        ),
    )
    formula_tree = _strict_runtime_tree(
        formula_core_artifact_bytes,
        resource_code=(
            PortablePredicateProgramFormulaCode.FORMULA_INPUT_RESOURCE
        ),
        json_code=PortablePredicateProgramFormulaCode.FORMULA_JSON_INVALID,
        tree_code=(
            PortablePredicateProgramFormulaCode.FORMULA_JSON_TREE_INVALID
        ),
        canonical_code=(
            PortablePredicateProgramFormulaCode.FORMULA_CANONICAL_MISMATCH
        ),
    )
    program_envelope = _validate_envelope(
        program_artifact_bytes,
        role_id="predicate-program",
        profile=profile,
        envelope_code=(
            PortablePredicateProgramFormulaCode.PROGRAM_ENVELOPE_INVALID
        ),
        binding_code=(
            PortablePredicateProgramFormulaCode.PROGRAM_BINDING_MISMATCH
        ),
    )
    formula_envelope = _validate_envelope(
        formula_core_artifact_bytes,
        role_id="predicate-formula-core",
        profile=profile,
        envelope_code=(
            PortablePredicateProgramFormulaCode.FORMULA_ENVELOPE_INVALID
        ),
        binding_code=(
            PortablePredicateProgramFormulaCode.FORMULA_BINDING_MISMATCH
        ),
    )
    if type(program_tree) is not dict or type(formula_tree) is not dict:
        _reject(PortablePredicateProgramFormulaCode.INTERNAL)
    profile_tree = _decode_trusted_canonical(
        profile.canonical_profile_bytes
    )
    if type(profile_tree) is not dict:
        _reject(PortablePredicateProgramFormulaCode.INTERNAL)
    core_tree = _core.portable_predicate_language_core_contract_tree()
    limits = core_tree["resource_limits"]
    purpose, purpose_binding, profile_fields = (
        _select_and_validate_purpose(program_tree, profile_tree)
    )
    required_anchor_roles = _required_anchor_roles(purpose)
    anchor_trees = _validate_anchor_bundle(
        anchor_snapshot,
        required_anchor_roles,
        profile_tree,
    )
    types, type_ids, type_depth = _parse_type_registry(
        program_tree["ordered_type_rows"],
        limits,
    )
    (
        operands,
        literal_values,
        operand_ids,
        input_operand_ids,
        derived_operand_ids,
    ) = _parse_operand_registry(
        program_tree["ordered_operand_rows"],
        types=types,
        profile_tree=profile_tree,
        profile_fields=profile_fields,
        purpose_binding=purpose_binding,
        limits=limits,
    )
    (
        shaping,
        _,
        shaping_depths,
        shaping_dependencies,
        shaping_ids,
        shaping_reference_count,
    ) = _parse_shaping_registry(
        program_tree["ordered_shaping_node_rows"],
        operands=operands,
        types=types,
        profile_tree=profile_tree,
        limits=limits,
    )
    (
        _,
        predicate_depths,
        predicate_dependencies,
        predicate_ids,
        predicate_reference_count,
    ) = _parse_predicate_registry(
        program_tree["ordered_predicate_node_rows"],
        operands=operands,
        types=types,
        literal_values=literal_values,
        shaping=shaping,
        shaping_depths=shaping_depths,
        profile_tree=profile_tree,
        limits=limits,
    )
    _validate_interval_refinements(types, profile_tree)
    node_reference_count = (
        shaping_reference_count + predicate_reference_count
    )
    graph_depth = _validate_whole_graph(
        program_tree=program_tree,
        operands=operands,
        shaping=shaping,
        shaping_dependencies=shaping_dependencies,
        predicate_dependencies=predicate_dependencies,
        predicate_depths=predicate_depths,
        reference_count=node_reference_count,
        limits=limits,
    )
    _validate_purpose_relations(
        purpose=purpose,
        purpose_binding=purpose_binding,
        anchor_trees=anchor_trees,
        operands=operands,
    )
    _validate_nonclaims(program_tree, profile_tree)
    (
        canonical_formula,
        formula_identity,
        formula_binding,
    ) = _construct_and_validate_formula(
        program_tree=program_tree,
        formula_bytes=formula_core_artifact_bytes,
        formula_tree=formula_tree,
        purpose=purpose,
        purpose_binding=purpose_binding,
        profile_tree=profile_tree,
        profile_fields=profile_fields,
    )
    if formula_envelope.artifact_identity_sha256 != formula_identity:
        _reject(PortablePredicateProgramFormulaCode.INTERNAL)
    return PortablePredicateProgramFormulaPairV1(
        canonical_program_bytes=program_artifact_bytes,
        canonical_formula_core_bytes=canonical_formula,
        canonical_purpose_binding_bytes=_runtime._canonical_json(
            purpose_binding
        ),
        program_identity_sha256=(
            program_envelope.artifact_identity_sha256
        ),
        formula_core_identity_sha256=formula_identity,
        program_byte_count=len(program_artifact_bytes),
        formula_core_byte_count=len(canonical_formula),
        program_artifact_type=program_tree["artifact_type"],
        formula_core_artifact_type=(
            formula_binding["artifact_type_id"]
        ),
        semantic_core_contract_sha256=(
            program_tree["semantic_core_contract_sha256"]
        ),
        profile_contract_sha256=(
            program_tree["profile_contract_sha256"]
        ),
        profile_id=profile.profile_id,
        program_id=program_tree["program_id"],
        program_purpose_id=program_tree["program_purpose_id"],
        ordered_type_ids=type_ids,
        ordered_operand_ids=operand_ids,
        ordered_input_operand_ids=input_operand_ids,
        ordered_derived_operand_ids=derived_operand_ids,
        ordered_shaping_node_ids=shaping_ids,
        ordered_predicate_node_ids=predicate_ids,
        root_node_id=program_tree["root_node_id"],
        required_anchor_role_ids=required_anchor_roles,
        type_depth=type_depth,
        graph_depth=graph_depth,
        node_reference_count=node_reference_count,
        validation_scope_id=(
            PORTABLE_PREDICATE_PROGRAM_FORMULA_VALIDATION_SCOPE_ID
        ),
        nested_program_semantics_validated=True,
        formula_projection_validated=True,
        evaluation_performed=False,
    )


def parse_portable_predicate_program_formula_pair_v1(
    program_artifact_bytes: bytes,
    formula_core_artifact_bytes: bytes,
    *,
    compiled_profile: _runtime.CompiledPortablePredicateRuntimeProfileV1,
    anchor_contract_artifacts: tuple = (),
) -> PortablePredicateProgramFormulaPairV1:
    """Validate one canonical program and its exact formula-core projection."""

    try:
        return _parse_portable_predicate_program_formula_pair_v1_impl(
            program_artifact_bytes,
            formula_core_artifact_bytes,
            compiled_profile=compiled_profile,
            anchor_contract_artifacts=anchor_contract_artifacts,
        )
    except PortablePredicateProgramFormulaError:
        raise
    except MemoryError:
        raise
    except Exception:
        _reject(PortablePredicateProgramFormulaCode.INTERNAL)
