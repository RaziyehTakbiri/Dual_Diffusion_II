"""Construct contexts and quarantined resolver-input candidates.

Checkpoint 56C constructs an official evaluation context and a distinct
framework-owned quarantine artifact from exact caller-supplied
resolver-outcome witnesses.  It never emits an official input bundle.  A
witness is not proof that a resolver ran, that a locator was resolved, or
that a source is authentic.  This module does not execute constructors or
predicates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Final

from heterodiff.data import (
    adapter_portable_predicate_language_core as _core,
)
from heterodiff.data import (
    adapter_portable_predicate_program as _program,
)
from heterodiff.data import (
    adapter_portable_predicate_runtime_artifacts as _runtime,
)


__all__ = (
    "PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_ARTIFACT_TYPE",
    "PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_IDENTITY_DOMAIN",
    "PORTABLE_PREDICATE_RESOLVER_OUTCOME_IDS",
    "PortablePredicateContextInputCode",
    "PortablePredicateContextInputError",
    "PortablePredicateContextQuarantinedInputCandidatePairV1",
    (
        "construct_portable_predicate_context_"
        "quarantined_input_candidate_pair_v1"
    ),
)


PORTABLE_PREDICATE_CONTEXT_INPUT_VALIDATION_SCOPE_ID: Final = (
    "CONTEXT_AND_QUARANTINED_RESOLVER_INPUT_CANDIDATE_ONLY_V1"
)
PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_SCOPE_ID: Final = (
    "UNAUTHENTICATED_RESOLVER_WITNESS_PROJECTION_ONLY_V1"
)
PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_ARTIFACT_TYPE: Final = (
    "heterodiff.portable-predicate."
    "quarantined-resolver-input-candidate.v1"
)
PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_IDENTITY_DOMAIN: Final = (
    "heterodiff.portable-predicate."
    "quarantined-resolver-input-candidate.identity.v1"
)
PORTABLE_PREDICATE_RESOLVER_OUTCOME_IDS: Final = (
    "RESOLVER_OUTCOME_VALUE_AVAILABLE",
    "RESOLVER_OUTCOME_RUNTIME_SOURCE_UNAVAILABLE",
    "RESOLVER_OUTCOME_PARSER_REJECTED",
    "RESOLVER_OUTCOME_DERIVATION_MISMATCH",
    "RESOLVER_OUTCOME_UPSTREAM_RULE_FAILED",
    "RESOLVER_OUTCOME_EXTERNAL_AUTHORITY_UNAVAILABLE",
    "RESOLVER_OUTCOME_STATIC_MAPPING_UNRESOLVED",
)
_OUTCOME_PREFIX: Final = "RESOLVER_OUTCOME_"
_MAXIMUM_ARTIFACT_BYTES: Final = 4 * 1024 * 1024
_MAXIMUM_ANCHOR_ROWS: Final = 4096
_MAXIMUM_ANCHOR_AGGREGATE_BYTES: Final = 4 * 1024 * 1024
_MAXIMUM_WITNESS_ROWS: Final = 512
_MAXIMUM_TYPED_PAYLOAD_BYTES: Final = 1024 * 1024
_MAXIMUM_WITNESS_VALUE_AGGREGATE_BYTES: Final = 4 * 1024 * 1024
_MAXIMUM_COLLECTION_ITEMS: Final = 4096
_MAXIMUM_IDENTIFIER_CHARACTERS: Final = 512


class PortablePredicateContextInputCode(str, Enum):
    """Closed ordinary failures for the Checkpoint-56C constructor."""

    INPUT_TYPE = "INPUT_TYPE"
    COMPILED_PROFILE_INVALID = "COMPILED_PROFILE_INVALID"
    CANDIDATE_NAMESPACE_COLLISION = "CANDIDATE_NAMESPACE_COLLISION"
    PROGRAM_INPUT_RESOURCE = "PROGRAM_INPUT_RESOURCE"
    FORMULA_INPUT_RESOURCE = "FORMULA_INPUT_RESOURCE"
    CONTEXT_INPUT_RESOURCE = "CONTEXT_INPUT_RESOURCE"
    CANDIDATE_INPUT_RESOURCE = "CANDIDATE_INPUT_RESOURCE"
    ANCHOR_INPUT_RESOURCE = "ANCHOR_INPUT_RESOURCE"
    WITNESS_INPUT_RESOURCE = "WITNESS_INPUT_RESOURCE"
    CONTEXT_NONCE_INVALID = "CONTEXT_NONCE_INVALID"
    PROGRAM_FORMULA_INVALID = "PROGRAM_FORMULA_INVALID"
    CONTEXT_JSON_INVALID = "CONTEXT_JSON_INVALID"
    CONTEXT_JSON_TREE_INVALID = "CONTEXT_JSON_TREE_INVALID"
    CONTEXT_CANONICAL_MISMATCH = "CONTEXT_CANONICAL_MISMATCH"
    CONTEXT_ENVELOPE_INVALID = "CONTEXT_ENVELOPE_INVALID"
    CONTEXT_BINDING_MISMATCH = "CONTEXT_BINDING_MISMATCH"
    CONTEXT_NONCLAIM_STATE_INVALID = "CONTEXT_NONCLAIM_STATE_INVALID"
    CANDIDATE_JSON_INVALID = "CANDIDATE_JSON_INVALID"
    CANDIDATE_JSON_TREE_INVALID = "CANDIDATE_JSON_TREE_INVALID"
    CANDIDATE_CANONICAL_MISMATCH = "CANDIDATE_CANONICAL_MISMATCH"
    CANDIDATE_SCHEMA_INVALID = "CANDIDATE_SCHEMA_INVALID"
    WITNESS_COVERAGE_MISMATCH = "WITNESS_COVERAGE_MISMATCH"
    WITNESS_OUTCOME_INVALID = "WITNESS_OUTCOME_INVALID"
    WITNESS_REQUIREMENT_MISMATCH = "WITNESS_REQUIREMENT_MISMATCH"
    WITNESS_SOURCE_INVALID = "WITNESS_SOURCE_INVALID"
    WITNESS_VALUE_INVALID = "WITNESS_VALUE_INVALID"
    CANDIDATE_BINDING_MISMATCH = "CANDIDATE_BINDING_MISMATCH"
    CANDIDATE_ROW_MISMATCH = "CANDIDATE_ROW_MISMATCH"
    CONTEXT_OUTPUT_RESOURCE = "CONTEXT_OUTPUT_RESOURCE"
    CANDIDATE_OUTPUT_RESOURCE = "CANDIDATE_OUTPUT_RESOURCE"
    INTERNAL = "INTERNAL"


_ERROR_MESSAGES: Final = {
    code: (
        "portable predicate context/input "
        + code.value.lower().replace("_", " ")
    )
    for code in PortablePredicateContextInputCode
}


class PortablePredicateContextInputError(ValueError):
    """One fixed-message Checkpoint-56C construction failure."""

    def __init__(self, code: PortablePredicateContextInputCode):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


@dataclass(frozen=True, repr=False)
class PortablePredicateContextQuarantinedInputCandidatePairV1:
    """Receipt for one context and one quarantined witness projection."""

    __slots__ = (
        "canonical_evaluation_context_bytes",
        "canonical_quarantined_input_candidate_bytes",
        "evaluation_context_identity_sha256",
        "quarantined_input_candidate_identity_sha256",
        "context_byte_count",
        "quarantined_input_candidate_byte_count",
        "evaluation_context_artifact_type",
        "quarantined_input_candidate_artifact_type",
        "target_input_bundle_artifact_type",
        "semantic_core_contract_sha256",
        "profile_contract_sha256",
        "profile_id",
        "program_identity_sha256",
        "formula_core_identity_sha256",
        "program_id",
        "program_purpose_id",
        "context_nonce_hex",
        "ordered_input_operand_ids",
        "ordered_claimed_resolver_outcome_ids",
        "ordered_mapped_input_state_ids",
        "ordered_claimed_source_artifact_kind_ids",
        "ordered_claimed_source_identity_sha256s",
        "available_input_count",
        "hard_failure_input_count",
        "not_evaluated_input_count",
        "available_value_byte_count",
        "validation_scope_id",
        "program_formula_revalidated",
        "context_constructed_and_envelope_validated",
        "resolver_outcome_transport_structurally_validated",
        "candidate_input_states_mapped_from_witnesses",
        "available_values_typed_validated",
        "quarantined_candidate_constructed_and_schema_validated",
        "official_input_bundle_constructed",
        "resolver_derived_input_semantics_validated",
        "context_nonce_uniqueness_validated",
        "runtime_resolver_executed",
        "locator_resolution_validated",
        "source_authenticity_validated",
        "evaluation_performed",
    )

    canonical_evaluation_context_bytes: bytes
    canonical_quarantined_input_candidate_bytes: bytes
    evaluation_context_identity_sha256: str
    quarantined_input_candidate_identity_sha256: str
    context_byte_count: int
    quarantined_input_candidate_byte_count: int
    evaluation_context_artifact_type: str
    quarantined_input_candidate_artifact_type: str
    target_input_bundle_artifact_type: str
    semantic_core_contract_sha256: str
    profile_contract_sha256: str
    profile_id: str
    program_identity_sha256: str
    formula_core_identity_sha256: str
    program_id: str
    program_purpose_id: str
    context_nonce_hex: str
    ordered_input_operand_ids: tuple
    ordered_claimed_resolver_outcome_ids: tuple
    ordered_mapped_input_state_ids: tuple
    ordered_claimed_source_artifact_kind_ids: tuple
    ordered_claimed_source_identity_sha256s: tuple
    available_input_count: int
    hard_failure_input_count: int
    not_evaluated_input_count: int
    available_value_byte_count: int
    validation_scope_id: str
    program_formula_revalidated: bool
    context_constructed_and_envelope_validated: bool
    resolver_outcome_transport_structurally_validated: bool
    candidate_input_states_mapped_from_witnesses: bool
    available_values_typed_validated: bool
    quarantined_candidate_constructed_and_schema_validated: bool
    official_input_bundle_constructed: bool
    resolver_derived_input_semantics_validated: bool
    context_nonce_uniqueness_validated: bool
    runtime_resolver_executed: bool
    locator_resolution_validated: bool
    source_authenticity_validated: bool
    evaluation_performed: bool

    def __repr__(self) -> str:
        return (
            "PortablePredicateContextQuarantinedInputCandidatePairV1("
            "evaluation_context_identity_sha256="
            f"{self.evaluation_context_identity_sha256!r}, "
            "quarantined_input_candidate_identity_sha256="
            f"{self.quarantined_input_candidate_identity_sha256!r}, "
            f"context_byte_count={self.context_byte_count!r}, "
            "quarantined_input_candidate_byte_count="
            f"{self.quarantined_input_candidate_byte_count!r}, "
            f"validation_scope_id={self.validation_scope_id!r})"
        )


class _TypedPayloadInvalid(ValueError):
    pass


def _reject(code: PortablePredicateContextInputCode) -> None:
    raise PortablePredicateContextInputError(code) from None


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
        _reject(PortablePredicateContextInputCode.INTERNAL)


def _check_outer_types(
    program_artifact_bytes: object,
    formula_core_artifact_bytes: object,
    context_nonce_bytes: object,
    resolver_outcome_witnesses: object,
    anchor_contract_artifacts: object,
) -> tuple:
    if (
        type(program_artifact_bytes) is not bytes
        or type(formula_core_artifact_bytes) is not bytes
        or type(context_nonce_bytes) is not bytes
        or type(resolver_outcome_witnesses) is not tuple
        or type(anchor_contract_artifacts) is not tuple
    ):
        _reject(PortablePredicateContextInputCode.INPUT_TYPE)
    return (
        program_artifact_bytes,
        formula_core_artifact_bytes,
        context_nonce_bytes,
        resolver_outcome_witnesses,
        anchor_contract_artifacts,
    )


def _revalidate_profile(compiled_profile: object) -> object:
    failure_code = None
    try:
        profile = _runtime._revalidate_compiled_profile(compiled_profile)
    except _runtime.PortablePredicateRuntimeEnvelopeError as error:
        failure_code = error.code
    if failure_code == (
        _runtime.PortablePredicateRuntimeEnvelopeCode.INTERNAL.value
    ):
        _reject(PortablePredicateContextInputCode.INTERNAL)
    if failure_code is not None:
        _reject(
            PortablePredicateContextInputCode.COMPILED_PROFILE_INVALID
        )
    return profile


def _reject_candidate_namespace_collision(profile: object) -> None:
    reserved = {
        PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_ARTIFACT_TYPE,
        PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_IDENTITY_DOMAIN,
    }
    if profile.profile_artifact_type in reserved or any(
        row[1] in reserved or row[2] in reserved
        for row in profile.artifact_domain_bindings
    ):
        _reject(
            PortablePredicateContextInputCode
            .CANDIDATE_NAMESPACE_COLLISION
        )


def _check_raw_resources(
    program_bytes: bytes,
    formula_bytes: bytes,
    nonce_bytes: bytes,
    witnesses: tuple,
    anchors: tuple,
) -> None:
    if not program_bytes or len(program_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(PortablePredicateContextInputCode.PROGRAM_INPUT_RESOURCE)
    if not formula_bytes or len(formula_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(PortablePredicateContextInputCode.FORMULA_INPUT_RESOURCE)
    if len(anchors) > _MAXIMUM_ANCHOR_ROWS:
        _reject(PortablePredicateContextInputCode.ANCHOR_INPUT_RESOURCE)
    for row in anchors:
        if (
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not str
            or type(row[1]) is not bytes
        ):
            _reject(PortablePredicateContextInputCode.INPUT_TYPE)
    for row in anchors:
        if len(row[0]) > _MAXIMUM_IDENTIFIER_CHARACTERS:
            _reject(
                PortablePredicateContextInputCode.ANCHOR_INPUT_RESOURCE
            )
        anchor_bytes = row[1]
        if (
            not anchor_bytes
            or len(anchor_bytes) > _MAXIMUM_ARTIFACT_BYTES
        ):
            _reject(
                PortablePredicateContextInputCode.ANCHOR_INPUT_RESOURCE
            )
    if sum(len(row[1]) for row in anchors) > (
        _MAXIMUM_ANCHOR_AGGREGATE_BYTES
    ):
        _reject(PortablePredicateContextInputCode.ANCHOR_INPUT_RESOURCE)
    if len(witnesses) > _MAXIMUM_WITNESS_ROWS:
        _reject(PortablePredicateContextInputCode.WITNESS_INPUT_RESOURCE)
    for row in witnesses:
        if (
            type(row) is not tuple
            or len(row) != 5
            or type(row[0]) is not str
            or type(row[1]) is not str
            or type(row[2]) is not str
            or type(row[3]) is not bytes
            or type(row[4]) is not bytes
        ):
            _reject(PortablePredicateContextInputCode.INPUT_TYPE)
    for row in witnesses:
        if any(
            len(row[index]) > _MAXIMUM_IDENTIFIER_CHARACTERS
            for index in (0, 1, 2)
        ):
            _reject(
                PortablePredicateContextInputCode.WITNESS_INPUT_RESOURCE
            )
        value_bytes = row[4]
        if len(value_bytes) > _MAXIMUM_TYPED_PAYLOAD_BYTES:
            _reject(
                PortablePredicateContextInputCode.WITNESS_INPUT_RESOURCE
            )
    if sum(len(row[4]) for row in witnesses) > (
        _MAXIMUM_WITNESS_VALUE_AGGREGATE_BYTES
    ):
        _reject(PortablePredicateContextInputCode.WITNESS_INPUT_RESOURCE)
    if len(nonce_bytes) != 32 or nonce_bytes == b"\x00" * 32:
        _reject(PortablePredicateContextInputCode.CONTEXT_NONCE_INVALID)


def _revalidate_program_formula(
    program_bytes: bytes,
    formula_bytes: bytes,
    *,
    compiled_profile: object,
    anchors: tuple,
) -> object:
    try:
        return _program.parse_portable_predicate_program_formula_pair_v1(
            program_bytes,
            formula_bytes,
            compiled_profile=compiled_profile,
            anchor_contract_artifacts=anchors,
        )
    except _program.PortablePredicateProgramFormulaError as error:
        if error.code == (
            _program.PortablePredicateProgramFormulaCode.INTERNAL.value
        ):
            _reject(PortablePredicateContextInputCode.INTERNAL)
        _reject(PortablePredicateContextInputCode.PROGRAM_FORMULA_INVALID)


def _profile_binding(profile_tree: dict, role_id: str) -> dict:
    rows = [
        row
        for row in profile_tree["artifact_domain_rows"]
        if row["artifact_role_id"] == role_id
    ]
    if len(rows) != 1:
        _reject(PortablePredicateContextInputCode.INTERNAL)
    row = rows[0]
    if row["identity_semantics_id"] != "DOMAIN_SEPARATED_SHA256":
        _reject(PortablePredicateContextInputCode.INTERNAL)
    return row


def _merged_nonclaims(profile_tree: dict) -> dict:
    result = {
        claim_id: False
        for claim_id in (
            _core.PORTABLE_PREDICATE_LANGUAGE_CORE_FALSE_CLAIM_IDS
        )
    }
    for claim_id, value in profile_tree["nonclaim_state"].items():
        if (
            not _runtime._is_identifier(claim_id)
            or type(value) is not bool
            or value
        ):
            _reject(PortablePredicateContextInputCode.INTERNAL)
        result[claim_id] = False
    return result


def _outcome_state_rows() -> dict:
    resolution = _core.portable_predicate_language_core_contract_tree()[
        "resolution_contract"
    ]
    rows = resolution["input_state_rows"]
    requirement_rows = resolution["resolution_requirement_rows"]
    by_role = {}
    by_state = {}
    for row in rows:
        role_id = row["public_error_role_id"]
        state_id = row["input_state_id"]
        if (
            type(role_id) is not str
            or role_id in by_role
            or not _runtime._is_identifier(state_id)
            or state_id in by_state
            or row["source_artifact_rule_id"]
            != "strict-kind-and-lowercase-sha256-v1"
        ):
            _reject(PortablePredicateContextInputCode.INTERNAL)
        by_role[role_id] = row
        by_state[state_id] = row
    expected_roles = {
        "",
        "RUNTIME_SOURCE_UNAVAILABLE",
        "PARSER_REJECTED",
        "DERIVATION_MISMATCH",
        "UPSTREAM_RULE_FAILED",
        "EXTERNAL_AUTHORITY_UNAVAILABLE",
        "STATIC_MAPPING_UNRESOLVED",
    }
    if set(by_role) != expected_roles:
        _reject(PortablePredicateContextInputCode.INTERNAL)
    expected_dispositions = {
        "": "",
        "RUNTIME_SOURCE_UNAVAILABLE": "HARD_FAILURE",
        "PARSER_REJECTED": "HARD_FAILURE",
        "DERIVATION_MISMATCH": "HARD_FAILURE",
        "UPSTREAM_RULE_FAILED": "HARD_FAILURE",
        "EXTERNAL_AUTHORITY_UNAVAILABLE": "NOT_EVALUATED",
        "STATIC_MAPPING_UNRESOLVED": "NOT_EVALUATED",
    }
    for role_id, disposition_id in expected_dispositions.items():
        row = by_role[role_id]
        expected_value_rule = (
            "nonempty-except-canonical-zero-length-octets-payload-v1"
            if role_id == ""
            else "empty-v1"
        )
        if (
            row["internal_disposition_id"] != disposition_id
            or row["value_bytes_rule_id"] != expected_value_rule
        ):
            _reject(PortablePredicateContextInputCode.INTERNAL)
    requirements = {}
    for row in requirement_rows:
        requirement_id = row["resolution_requirement_id"]
        if (
            not _runtime._is_identifier(requirement_id)
            or requirement_id in requirements
        ):
            _reject(PortablePredicateContextInputCode.INTERNAL)
        requirements[requirement_id] = row
    for state_id, state_row in by_state.items():
        for requirement_id in state_row[
            "admitted_resolution_requirement_ids"
        ]:
            requirement = requirements.get(requirement_id)
            if (
                requirement is None
                or state_id not in requirement["admitted_input_state_ids"]
            ):
                _reject(PortablePredicateContextInputCode.INTERNAL)
    for requirement_id, requirement in requirements.items():
        for state_id in requirement["admitted_input_state_ids"]:
            state_row = by_state.get(state_id)
            if (
                state_row is None
                or requirement_id
                not in state_row["admitted_resolution_requirement_ids"]
            ):
                _reject(PortablePredicateContextInputCode.INTERNAL)
    outcome_rows = {}
    for outcome_id in PORTABLE_PREDICATE_RESOLVER_OUTCOME_IDS:
        suffix = outcome_id[len(_OUTCOME_PREFIX) :]
        role_id = "" if suffix == "VALUE_AVAILABLE" else suffix
        row = by_role.get(role_id)
        if row is None:
            _reject(PortablePredicateContextInputCode.INTERNAL)
        outcome_rows[outcome_id] = row
    return (outcome_rows, requirements)


def _read_u64(value: memoryview, offset: int) -> tuple:
    if offset + 8 > len(value):
        raise _TypedPayloadInvalid
    return (int.from_bytes(value[offset : offset + 8], "big"), offset + 8)


def _read_frame(value: memoryview, offset: int) -> tuple:
    length, offset = _read_u64(value, offset)
    if length > len(value) - offset:
        raise _TypedPayloadInvalid
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
        raise _TypedPayloadInvalid
    row = types.get(type_id)
    if row is None:
        raise _TypedPayloadInvalid
    kind_id = row["type_kind_id"]
    if kind_id == "boolean":
        if len(payload) != 1 or payload[0] not in (0, 1):
            raise _TypedPayloadInvalid
        return payload[0] == 1
    if kind_id == "u64":
        if len(payload) != 8:
            raise _TypedPayloadInvalid
        return int.from_bytes(payload, "big")
    if kind_id == "token":
        try:
            token = bytes(payload).decode("ascii", "strict")
        except UnicodeError:
            raise _TypedPayloadInvalid from None
        if not _runtime._is_identifier(token):
            raise _TypedPayloadInvalid
        return token
    if kind_id == "octets":
        if len(payload) > 262144:
            raise _TypedPayloadInvalid
        return bytes(payload)
    if kind_id == "sha256":
        if len(payload) != 32:
            raise _TypedPayloadInvalid
        return bytes(payload)
    if kind_id == "optional":
        if len(payload) == 1 and payload[0] == 0:
            return ("optional-none",)
        if not payload or payload[0] != 1:
            raise _TypedPayloadInvalid
        item, end = _read_frame(payload, 1)
        if end != len(payload):
            raise _TypedPayloadInvalid
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
        raise _TypedPayloadInvalid
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
            raise _TypedPayloadInvalid
        return ("sequence", tuple(values))
    if kind_id == "tuple":
        component_ids = row["ordered_component_type_ids"]
        if count != len(component_ids):
            raise _TypedPayloadInvalid
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
            raise _TypedPayloadInvalid
        return ("tuple", tuple(values))
    if kind_id == "keyed-table":
        decoded_rows = []
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
                raise _TypedPayloadInvalid
            key = tuple(decoded_row[1][index] for index in indices)
            if key in keys:
                raise _TypedPayloadInvalid
            keys.add(key)
            decoded_rows.append(decoded_row)
        if offset != len(payload):
            raise _TypedPayloadInvalid
        return ("keyed-table", tuple(decoded_rows))
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
                raise _TypedPayloadInvalid
            intervals.append((start, end))
        if offset != len(payload):
            raise _TypedPayloadInvalid
        return ("u64-interval-sequence", tuple(intervals))
    raise _TypedPayloadInvalid


def _derive_input_rows(
    program_tree: dict,
    witnesses: tuple,
) -> tuple:
    input_operands = [
        row
        for row in program_tree["ordered_operand_rows"]
        if row["value_source_kind_id"] == "INPUT_RESOLVED"
    ]
    input_ids = tuple(row["operand_id"] for row in input_operands)
    witness_ids = tuple(row[0] for row in witnesses)
    if witness_ids != input_ids:
        _reject(
            PortablePredicateContextInputCode.WITNESS_COVERAGE_MISMATCH
        )
    outcome_rows, requirements = _outcome_state_rows()
    selected_states = []
    for witness in witnesses:
        outcome_id = witness[1]
        state_row = outcome_rows.get(outcome_id)
        if state_row is None:
            _reject(
                PortablePredicateContextInputCode.WITNESS_OUTCOME_INVALID
            )
        selected_states.append(state_row)
    for operand, state_row in zip(input_operands, selected_states):
        requirement_id = operand["resolution_requirement_id"]
        requirement = requirements.get(requirement_id)
        if (
            requirement is None
            or "INPUT_RESOLVED"
            not in requirement["admitted_value_source_kind_ids"]
        ):
            _reject(PortablePredicateContextInputCode.INTERNAL)
        if (
            requirement_id
            not in state_row["admitted_resolution_requirement_ids"]
            or state_row["input_state_id"]
            not in requirement["admitted_input_state_ids"]
        ):
            _reject(
                PortablePredicateContextInputCode
                .WITNESS_REQUIREMENT_MISMATCH
            )
    for witness in witnesses:
        if (
            not _runtime._is_identifier(witness[2])
            or len(witness[3]) != 32
        ):
            _reject(
                PortablePredicateContextInputCode.WITNESS_SOURCE_INVALID
            )
    types = {
        row["type_id"]: row
        for row in program_tree["ordered_type_rows"]
    }
    available_value_byte_count = 0
    for operand, witness, state_row in zip(
        input_operands,
        witnesses,
        selected_states,
    ):
        value_bytes = witness[4]
        if state_row["input_state_id"] == "AVAILABLE":
            try:
                _decode_typed_payload(
                    operand["type_id"],
                    value_bytes,
                    types,
                )
            except _TypedPayloadInvalid:
                _reject(
                    PortablePredicateContextInputCode.WITNESS_VALUE_INVALID
                )
            available_value_byte_count += len(value_bytes)
        elif value_bytes:
            _reject(
                PortablePredicateContextInputCode.WITNESS_VALUE_INVALID
            )
    rows = [
        {
            "operand_id": operand["operand_id"],
            "claimed_resolver_outcome_id": witness[1],
            "mapped_input_state_id": state_row["input_state_id"],
            "claimed_source_artifact_kind_id": witness[2],
            "claimed_source_identity_sha256": witness[3].hex(),
            "claimed_value_bytes_hex": witness[4].hex(),
        }
        for operand, witness, state_row in zip(
            input_operands,
            witnesses,
            selected_states,
        )
    ]
    return (
        rows,
        input_ids,
        tuple(row[1] for row in witnesses),
        tuple(row["input_state_id"] for row in selected_states),
        tuple(row[2] for row in witnesses),
        tuple(row[3].hex() for row in witnesses),
        tuple(row["internal_disposition_id"] for row in selected_states),
        available_value_byte_count,
    )


def _validate_constructed_envelope(
    value: bytes,
    *,
    role_id: str,
    compiled_profile: object,
) -> object:
    try:
        return _runtime.parse_portable_predicate_runtime_envelope_v1(
            value,
            expected_artifact_role_id=role_id,
            compiled_profile=compiled_profile,
        )
    except _runtime.PortablePredicateRuntimeEnvelopeError:
        _reject(PortablePredicateContextInputCode.INTERNAL)


def _validate_quarantined_candidate_tree(value: object) -> None:
    exact_fields = {
        "artifact_type",
        "format_version",
        "validation_scope_id",
        "semantic_core_contract_sha256",
        "profile_contract_sha256",
        "program_sha256",
        "evaluation_context_identity_sha256",
        "ordered_candidate_input_rows",
    }
    if (
        type(value) is not dict
        or set(value) != exact_fields
        or value["artifact_type"]
        != PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_ARTIFACT_TYPE
        or value["format_version"] != "1"
        or value["validation_scope_id"]
        != PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_SCOPE_ID
        or not _runtime._is_sha256(
            value["semantic_core_contract_sha256"]
        )
        or not _runtime._is_sha256(value["profile_contract_sha256"])
        or not _runtime._is_sha256(value["program_sha256"])
        or not _runtime._is_sha256(
            value["evaluation_context_identity_sha256"]
        )
        or type(value["ordered_candidate_input_rows"]) is not list
        or len(value["ordered_candidate_input_rows"])
        > _MAXIMUM_WITNESS_ROWS
    ):
        _reject(PortablePredicateContextInputCode.INTERNAL)
    row_fields = {
        "operand_id",
        "claimed_resolver_outcome_id",
        "mapped_input_state_id",
        "claimed_source_artifact_kind_id",
        "claimed_source_identity_sha256",
        "claimed_value_bytes_hex",
    }
    for row in value["ordered_candidate_input_rows"]:
        if (
            type(row) is not dict
            or set(row) != row_fields
            or not _runtime._is_identifier(row["operand_id"])
            or row["claimed_resolver_outcome_id"]
            not in PORTABLE_PREDICATE_RESOLVER_OUTCOME_IDS
            or not _runtime._is_identifier(row["mapped_input_state_id"])
            or not _runtime._is_identifier(
                row["claimed_source_artifact_kind_id"]
            )
            or not _runtime._is_sha256(
                row["claimed_source_identity_sha256"]
            )
            or not _runtime._is_payload_hex(
                row["claimed_value_bytes_hex"]
            )
        ):
            _reject(PortablePredicateContextInputCode.INTERNAL)


def _construct_quarantined_candidate_pair_v1_impl(
    program_artifact_bytes: object,
    formula_core_artifact_bytes: object,
    *,
    context_nonce_bytes: object,
    resolver_outcome_witnesses: object,
    compiled_profile: object,
    anchor_contract_artifacts: object,
) -> PortablePredicateContextQuarantinedInputCandidatePairV1:
    (
        program_bytes,
        formula_bytes,
        nonce_bytes,
        witnesses,
        anchors,
    ) = _check_outer_types(
        program_artifact_bytes,
        formula_core_artifact_bytes,
        context_nonce_bytes,
        resolver_outcome_witnesses,
        anchor_contract_artifacts,
    )
    profile = _revalidate_profile(compiled_profile)
    _reject_candidate_namespace_collision(profile)
    _check_raw_resources(
        program_bytes,
        formula_bytes,
        nonce_bytes,
        witnesses,
        anchors,
    )
    program_receipt = _revalidate_program_formula(
        program_bytes,
        formula_bytes,
        compiled_profile=profile,
        anchors=anchors,
    )
    profile_tree = _decode_trusted_canonical(
        profile.canonical_profile_bytes
    )
    program_tree = _decode_trusted_canonical(
        program_receipt.canonical_program_bytes
    )
    if type(profile_tree) is not dict or type(program_tree) is not dict:
        _reject(PortablePredicateContextInputCode.INTERNAL)
    (
        input_rows,
        input_ids,
        outcome_ids,
        state_ids,
        source_kind_ids,
        source_sha256s,
        dispositions,
        available_value_bytes,
    ) = _derive_input_rows(program_tree, witnesses)
    nonclaims = _merged_nonclaims(profile_tree)
    context_binding = _profile_binding(
        profile_tree,
        "predicate-evaluation-context",
    )
    input_binding = _profile_binding(
        profile_tree,
        "predicate-input-bundle",
    )
    context_tree = {
        "artifact_type": context_binding["artifact_type_id"],
        "format_version": "1",
        "semantic_core_contract_sha256": (
            program_receipt.semantic_core_contract_sha256
        ),
        "profile_contract_sha256": (
            program_receipt.profile_contract_sha256
        ),
        "program_sha256": program_receipt.program_identity_sha256,
        "context_nonce_hex": nonce_bytes.hex(),
        "nonclaim_state": nonclaims,
    }
    context_bytes = _runtime._canonical_json(context_tree)
    if len(context_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateContextInputCode.CONTEXT_OUTPUT_RESOURCE
        )
    context_identity = _runtime._domain_sha256(
        context_binding["digest_domain_id"],
        context_bytes,
    )
    candidate_tree = {
        "artifact_type": (
            PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_ARTIFACT_TYPE
        ),
        "format_version": "1",
        "validation_scope_id": (
            PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_SCOPE_ID
        ),
        "semantic_core_contract_sha256": (
            program_receipt.semantic_core_contract_sha256
        ),
        "profile_contract_sha256": (
            program_receipt.profile_contract_sha256
        ),
        "program_sha256": program_receipt.program_identity_sha256,
        "evaluation_context_identity_sha256": (
            context_identity
        ),
        "ordered_candidate_input_rows": input_rows,
    }
    _validate_quarantined_candidate_tree(candidate_tree)
    candidate_bytes = _runtime._canonical_json(candidate_tree)
    if len(candidate_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateContextInputCode
            .CANDIDATE_OUTPUT_RESOURCE
        )
    candidate_identity = _runtime._domain_sha256(
        PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_IDENTITY_DOMAIN,
        candidate_bytes,
    )
    context_envelope = _validate_constructed_envelope(
        context_bytes,
        role_id="predicate-evaluation-context",
        compiled_profile=profile,
    )
    if (
        context_envelope.artifact_type
        != context_binding["artifact_type_id"]
        or context_envelope.artifact_identity_sha256 != context_identity
    ):
        _reject(PortablePredicateContextInputCode.INTERNAL)
    return PortablePredicateContextQuarantinedInputCandidatePairV1(
        canonical_evaluation_context_bytes=context_bytes,
        canonical_quarantined_input_candidate_bytes=candidate_bytes,
        evaluation_context_identity_sha256=(
            context_identity
        ),
        quarantined_input_candidate_identity_sha256=(
            candidate_identity
        ),
        context_byte_count=len(context_bytes),
        quarantined_input_candidate_byte_count=len(candidate_bytes),
        evaluation_context_artifact_type=(
            context_binding["artifact_type_id"]
        ),
        quarantined_input_candidate_artifact_type=(
            PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_ARTIFACT_TYPE
        ),
        target_input_bundle_artifact_type=(
            input_binding["artifact_type_id"]
        ),
        semantic_core_contract_sha256=(
            program_receipt.semantic_core_contract_sha256
        ),
        profile_contract_sha256=(
            program_receipt.profile_contract_sha256
        ),
        profile_id=program_receipt.profile_id,
        program_identity_sha256=(
            program_receipt.program_identity_sha256
        ),
        formula_core_identity_sha256=(
            program_receipt.formula_core_identity_sha256
        ),
        program_id=program_receipt.program_id,
        program_purpose_id=program_receipt.program_purpose_id,
        context_nonce_hex=nonce_bytes.hex(),
        ordered_input_operand_ids=input_ids,
        ordered_claimed_resolver_outcome_ids=outcome_ids,
        ordered_mapped_input_state_ids=state_ids,
        ordered_claimed_source_artifact_kind_ids=source_kind_ids,
        ordered_claimed_source_identity_sha256s=source_sha256s,
        available_input_count=state_ids.count("AVAILABLE"),
        hard_failure_input_count=dispositions.count("HARD_FAILURE"),
        not_evaluated_input_count=dispositions.count("NOT_EVALUATED"),
        available_value_byte_count=available_value_bytes,
        validation_scope_id=(
            PORTABLE_PREDICATE_CONTEXT_INPUT_VALIDATION_SCOPE_ID
        ),
        program_formula_revalidated=True,
        context_constructed_and_envelope_validated=True,
        resolver_outcome_transport_structurally_validated=True,
        candidate_input_states_mapped_from_witnesses=True,
        available_values_typed_validated=True,
        quarantined_candidate_constructed_and_schema_validated=True,
        official_input_bundle_constructed=False,
        resolver_derived_input_semantics_validated=False,
        context_nonce_uniqueness_validated=False,
        runtime_resolver_executed=False,
        locator_resolution_validated=False,
        source_authenticity_validated=False,
        evaluation_performed=False,
    )


def construct_portable_predicate_context_quarantined_input_candidate_pair_v1(
    program_artifact_bytes: bytes,
    formula_core_artifact_bytes: bytes,
    *,
    context_nonce_bytes: bytes,
    resolver_outcome_witnesses: tuple,
    compiled_profile: _runtime.CompiledPortablePredicateRuntimeProfileV1,
    anchor_contract_artifacts: tuple = (),
) -> PortablePredicateContextQuarantinedInputCandidatePairV1:
    """Construct one official context and one quarantined candidate."""

    try:
        return (
            _construct_quarantined_candidate_pair_v1_impl(
                program_artifact_bytes,
                formula_core_artifact_bytes,
                context_nonce_bytes=context_nonce_bytes,
                resolver_outcome_witnesses=resolver_outcome_witnesses,
                compiled_profile=compiled_profile,
                anchor_contract_artifacts=anchor_contract_artifacts,
            )
        )
    except PortablePredicateContextInputError:
        raise
    except MemoryError:
        raise
    except Exception:
        _reject(PortablePredicateContextInputCode.INTERNAL)
