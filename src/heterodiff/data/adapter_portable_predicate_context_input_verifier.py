"""Independent verifier for contexts and quarantined input candidates.

Checkpoint 56C verifies one official evaluation context and one distinct
framework-owned quarantine artifact reconstructed from exact caller-supplied
resolver-outcome witnesses.  It never verifies or emits an official input
bundle.  Witnesses do not prove resolver execution, locator resolution, or
source authenticity.  This module imports only verifier-side dependencies
and does not execute constructors or predicates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Final

from heterodiff.data import (
    adapter_portable_predicate_language_core_verifier as _core,
)
from heterodiff.data import (
    adapter_portable_predicate_program_verifier as _program,
)
from heterodiff.data import (
    adapter_portable_predicate_runtime_artifacts_verifier as _runtime,
)


__all__ = (
    "PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_ARTIFACT_TYPE",
    "PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_IDENTITY_DOMAIN",
    "PORTABLE_PREDICATE_RESOLVER_OUTCOME_IDS",
    "PortablePredicateContextInputVerificationCode",
    "PortablePredicateContextInputVerificationError",
    "VerifiedPortablePredicateContextQuarantinedInputCandidatePairV1",
    (
        "verify_portable_predicate_context_"
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
_MAXIMUM_JSON_INTEGER_DIGITS: Final = 20
_MAXIMUM_IDENTIFIER_CHARACTERS: Final = 512


class PortablePredicateContextInputVerificationCode(str, Enum):
    """Closed ordinary failures for the Checkpoint-56C verifier."""

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
    for code in PortablePredicateContextInputVerificationCode
}


class PortablePredicateContextInputVerificationError(ValueError):
    """One fixed-message verifier failure."""

    def __init__(
        self,
        code: PortablePredicateContextInputVerificationCode,
    ):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


@dataclass(frozen=True, repr=False)
class VerifiedPortablePredicateContextQuarantinedInputCandidatePairV1:
    """Independent receipt for one context and one quarantine artifact."""

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
            "VerifiedPortablePredicateContext"
            "QuarantinedInputCandidatePairV1("
            f"context_byte_count={self.context_byte_count}, "
            "quarantined_input_candidate_byte_count="
            f"{self.quarantined_input_candidate_byte_count}, "
            f"available_input_count={self.available_input_count}, "
            f"hard_failure_input_count={self.hard_failure_input_count}, "
            f"not_evaluated_input_count={self.not_evaluated_input_count}, "
            f"validation_scope_id={self.validation_scope_id!r}, "
            f"evaluation_performed={self.evaluation_performed})"
        )


class _TypedPayloadInvalid(ValueError):
    pass


def _reject(
    code: PortablePredicateContextInputVerificationCode,
) -> None:
    raise PortablePredicateContextInputVerificationError(code) from None


def _check_outer_types(
    program_artifact_bytes: object,
    formula_core_artifact_bytes: object,
    evaluation_context_artifact_bytes: object,
    quarantined_input_candidate_artifact_bytes: object,
    context_nonce_bytes: object,
    resolver_outcome_witnesses: object,
    anchor_contract_artifacts: object,
) -> tuple:
    if (
        type(program_artifact_bytes) is not bytes
        or type(formula_core_artifact_bytes) is not bytes
        or type(evaluation_context_artifact_bytes) is not bytes
        or type(quarantined_input_candidate_artifact_bytes) is not bytes
        or type(context_nonce_bytes) is not bytes
        or type(resolver_outcome_witnesses) is not tuple
        or type(anchor_contract_artifacts) is not tuple
    ):
        _reject(PortablePredicateContextInputVerificationCode.INPUT_TYPE)
    return (
        program_artifact_bytes,
        formula_core_artifact_bytes,
        evaluation_context_artifact_bytes,
        quarantined_input_candidate_artifact_bytes,
        context_nonce_bytes,
        resolver_outcome_witnesses,
        anchor_contract_artifacts,
    )


def _revalidate_profile(compiled_profile: object) -> object:
    failure_code = None
    try:
        profile = _runtime._revalidate_profile_snapshot(compiled_profile)
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError as error:
        failure_code = error.code
        profile = None
    if failure_code == (
        _runtime
        .PortablePredicateRuntimeEnvelopeVerificationCode
        .INTERNAL
        .value
    ):
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    if failure_code is not None:
        _reject(
            PortablePredicateContextInputVerificationCode
            .COMPILED_PROFILE_INVALID
        )
    if profile is None:
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
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
            PortablePredicateContextInputVerificationCode
            .CANDIDATE_NAMESPACE_COLLISION
        )


def _check_raw_resources(
    program_bytes: bytes,
    formula_bytes: bytes,
    context_bytes: bytes,
    candidate_bytes: bytes,
    nonce_bytes: bytes,
    witnesses: tuple,
    anchors: tuple,
) -> None:
    if not program_bytes or len(program_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateContextInputVerificationCode
            .PROGRAM_INPUT_RESOURCE
        )
    if not formula_bytes or len(formula_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateContextInputVerificationCode
            .FORMULA_INPUT_RESOURCE
        )
    if not context_bytes or len(context_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateContextInputVerificationCode
            .CONTEXT_INPUT_RESOURCE
        )
    if not candidate_bytes or len(candidate_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateContextInputVerificationCode
            .CANDIDATE_INPUT_RESOURCE
        )
    if len(anchors) > _MAXIMUM_ANCHOR_ROWS:
        _reject(
            PortablePredicateContextInputVerificationCode
            .ANCHOR_INPUT_RESOURCE
        )
    for row in anchors:
        if (
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not str
            or type(row[1]) is not bytes
        ):
            _reject(PortablePredicateContextInputVerificationCode.INPUT_TYPE)
    for row in anchors:
        anchor_bytes = row[1]
        if (
            len(row[0]) > _MAXIMUM_IDENTIFIER_CHARACTERS
            or not anchor_bytes
            or len(anchor_bytes) > _MAXIMUM_ARTIFACT_BYTES
        ):
            _reject(
                PortablePredicateContextInputVerificationCode
                .ANCHOR_INPUT_RESOURCE
            )
    if (
        sum(len(row[1]) for row in anchors)
        > _MAXIMUM_ANCHOR_AGGREGATE_BYTES
    ):
        _reject(
            PortablePredicateContextInputVerificationCode
            .ANCHOR_INPUT_RESOURCE
        )
    if len(witnesses) > _MAXIMUM_WITNESS_ROWS:
        _reject(
            PortablePredicateContextInputVerificationCode
            .WITNESS_INPUT_RESOURCE
        )
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
            _reject(PortablePredicateContextInputVerificationCode.INPUT_TYPE)
    for row in witnesses:
        if any(
            len(row[index]) > _MAXIMUM_IDENTIFIER_CHARACTERS
            for index in (0, 1, 2)
        ):
            _reject(
                PortablePredicateContextInputVerificationCode
                .WITNESS_INPUT_RESOURCE
            )
        value_bytes = row[4]
        if len(value_bytes) > _MAXIMUM_TYPED_PAYLOAD_BYTES:
            _reject(
                PortablePredicateContextInputVerificationCode
                .WITNESS_INPUT_RESOURCE
            )
    if (
        sum(len(row[4]) for row in witnesses)
        > _MAXIMUM_WITNESS_VALUE_AGGREGATE_BYTES
    ):
        _reject(
            PortablePredicateContextInputVerificationCode
            .WITNESS_INPUT_RESOURCE
        )
    if len(nonce_bytes) != 32 or nonce_bytes == b"\x00" * 32:
        _reject(
            PortablePredicateContextInputVerificationCode
            .CONTEXT_NONCE_INVALID
        )


def _revalidate_program_formula(
    program_bytes: bytes,
    formula_bytes: bytes,
    *,
    compiled_profile: object,
    anchors: tuple,
) -> object:
    try:
        return _program.verify_portable_predicate_program_formula_pair_v1(
            program_bytes,
            formula_bytes,
            compiled_profile=compiled_profile,
            anchor_contract_artifacts=anchors,
        )
    except _program.PortablePredicateProgramFormulaVerificationError as error:
        if error.code == (
            _program
            .PortablePredicateProgramFormulaVerificationCode
            .INTERNAL
            .value
        ):
            _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
        _reject(
            PortablePredicateContextInputVerificationCode
            .PROGRAM_FORMULA_INVALID
        )


def _bounded_integer(value: str) -> int:
    digits = value[1:] if value.startswith("-") else value
    if not digits or len(digits) > _MAXIMUM_JSON_INTEGER_DIGITS:
        raise ValueError("bounded JSON integer")
    return int(value, 10)


def _decode_expected_artifact(
    raw: bytes,
    *,
    resource_code: PortablePredicateContextInputVerificationCode,
    json_code: PortablePredicateContextInputVerificationCode,
    tree_code: PortablePredicateContextInputVerificationCode,
    canonical_code: PortablePredicateContextInputVerificationCode,
) -> object:
    try:
        preflight = _runtime._preflight_json(raw)
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError:
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    if preflight == "syntax-invalid":
        _reject(json_code)
    if preflight != "valid":
        _reject(resource_code)
    try:
        decoded = json.loads(
            raw.decode("ascii", "strict"),
            object_pairs_hook=_runtime._unique_object,
            parse_constant=_runtime._reject_constant,
            parse_float=_runtime._reject_float,
            parse_int=_bounded_integer,
        )
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _reject(json_code)
    try:
        status = _runtime._bounded_tree_status(decoded)
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError:
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    if status == "resource-invalid":
        _reject(resource_code)
    if status != "valid":
        _reject(tree_code)
    try:
        canonical = _runtime._encode_canonical(decoded)
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError:
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    if raw != canonical:
        _reject(canonical_code)
    return decoded


def _decode_trusted_canonical(value: bytes) -> dict:
    try:
        decoded = json.loads(value.decode("ascii", "strict"))
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    if type(decoded) is not dict:
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    return decoded


def _verify_expected_envelope(
    value: bytes,
    *,
    role_id: str,
    compiled_profile: object,
    envelope_code: PortablePredicateContextInputVerificationCode,
    binding_code: PortablePredicateContextInputVerificationCode,
) -> object:
    try:
        return _runtime.verify_portable_predicate_runtime_envelope_v1(
            value,
            expected_artifact_role_id=role_id,
            compiled_profile=compiled_profile,
        )
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError as error:
        if error.code == (
            _runtime
            .PortablePredicateRuntimeEnvelopeVerificationCode
            .INTERNAL
            .value
        ):
            _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
        if error.code == (
            _runtime
            .PortablePredicateRuntimeEnvelopeVerificationCode
            .ARTIFACT_BINDING_MISMATCH
            .value
        ):
            _reject(binding_code)
        _reject(envelope_code)


def _profile_binding(profile_tree: dict, role_id: str) -> dict:
    rows = [
        row
        for row in profile_tree["artifact_domain_rows"]
        if row["artifact_role_id"] == role_id
    ]
    if len(rows) != 1:
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    row = rows[0]
    if row["identity_semantics_id"] != "DOMAIN_SEPARATED_SHA256":
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    return row


def _merged_nonclaims(core_tree: dict, profile_tree: dict) -> dict:
    core_nonclaims = core_tree.get("nonclaim_state")
    profile_nonclaims = profile_tree.get("nonclaim_state")
    if type(core_nonclaims) is not dict or type(profile_nonclaims) is not dict:
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    result = {}
    for claim_id, value in core_nonclaims.items():
        if (
            not _runtime._identifier(claim_id)
            or type(value) is not bool
            or value
            or claim_id in result
        ):
            _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
        result[claim_id] = False
    for claim_id, value in profile_nonclaims.items():
        if (
            not _runtime._identifier(claim_id)
            or type(value) is not bool
            or value
        ):
            _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
        result[claim_id] = False
    return result


def _same_exact(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return (
            set(left) == set(right)
            and all(_same_exact(left[key], right[key]) for key in right)
        )
    if type(left) is list:
        return (
            len(left) == len(right)
            and all(
                _same_exact(left_item, right_item)
                for left_item, right_item in zip(left, right)
            )
        )
    return left == right


def _framed_digest(domain: str, payload: bytes) -> str:
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except UnicodeError:
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _outcome_state_rows(core_tree: dict) -> tuple:
    try:
        resolution = core_tree["resolution_contract"]
        rows = resolution["input_state_rows"]
        requirement_rows = resolution["resolution_requirement_rows"]
    except (KeyError, TypeError):
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    by_role = {}
    by_state = {}
    for row in rows:
        try:
            role_id = row["public_error_role_id"]
            state_id = row["input_state_id"]
        except (KeyError, TypeError):
            _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
        if (
            type(role_id) is not str
            or role_id in by_role
            or not _runtime._identifier(state_id)
            or state_id in by_state
            or row.get("source_artifact_rule_id")
            != "strict-kind-and-lowercase-sha256-v1"
        ):
            _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
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
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
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
            row.get("internal_disposition_id") != disposition_id
            or row.get("value_bytes_rule_id") != expected_value_rule
        ):
            _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    requirements = {}
    for row in requirement_rows:
        try:
            requirement_id = row["resolution_requirement_id"]
        except (KeyError, TypeError):
            _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
        if (
            not _runtime._identifier(requirement_id)
            or requirement_id in requirements
        ):
            _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
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
                _reject(
                    PortablePredicateContextInputVerificationCode.INTERNAL
                )
    for requirement_id, requirement in requirements.items():
        for state_id in requirement["admitted_input_state_ids"]:
            state_row = by_state.get(state_id)
            if (
                state_row is None
                or requirement_id
                not in state_row["admitted_resolution_requirement_ids"]
            ):
                _reject(
                    PortablePredicateContextInputVerificationCode.INTERNAL
                )
    outcome_rows = {}
    for outcome_id in PORTABLE_PREDICATE_RESOLVER_OUTCOME_IDS:
        suffix = outcome_id[len(_OUTCOME_PREFIX) :]
        role_id = "" if suffix == "VALUE_AVAILABLE" else suffix
        row = by_role.get(role_id)
        if row is None:
            _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
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
    payload_view = memoryview(payload)
    if not payload_view.readonly:
        payload_view = payload_view.toreadonly()
    return _decode_typed_payload_view(
        type_id,
        payload_view,
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
        if payload not in {b"\x00", b"\x01"}:
            raise _TypedPayloadInvalid
        return payload == b"\x01"
    if kind_id == "u64":
        if len(payload) != 8:
            raise _TypedPayloadInvalid
        return int.from_bytes(payload, "big")
    if kind_id == "token":
        try:
            token = bytes(payload).decode("ascii", "strict")
        except UnicodeError:
            raise _TypedPayloadInvalid from None
        if not _runtime._identifier(token):
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
        if payload == b"\x00":
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


def _derive_candidate_rows(
    program_tree: dict,
    witnesses: tuple,
    core_tree: dict,
) -> tuple:
    try:
        input_operands = [
            row
            for row in program_tree["ordered_operand_rows"]
            if row["value_source_kind_id"] == "INPUT_RESOLVED"
        ]
    except (KeyError, TypeError):
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    input_ids = tuple(row["operand_id"] for row in input_operands)
    witness_ids = tuple(row[0] for row in witnesses)
    if witness_ids != input_ids:
        _reject(
            PortablePredicateContextInputVerificationCode
            .WITNESS_COVERAGE_MISMATCH
        )
    outcome_rows, requirements = _outcome_state_rows(core_tree)
    selected_states = []
    for witness in witnesses:
        state_row = outcome_rows.get(witness[1])
        if state_row is None:
            _reject(
                PortablePredicateContextInputVerificationCode
                .WITNESS_OUTCOME_INVALID
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
            _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
        if (
            requirement_id
            not in state_row["admitted_resolution_requirement_ids"]
            or state_row["input_state_id"]
            not in requirement["admitted_input_state_ids"]
        ):
            _reject(
                PortablePredicateContextInputVerificationCode
                .WITNESS_REQUIREMENT_MISMATCH
            )
    for witness in witnesses:
        if (
            not _runtime._identifier(witness[2])
            or len(witness[3]) != 32
        ):
            _reject(
                PortablePredicateContextInputVerificationCode
                .WITNESS_SOURCE_INVALID
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
                    PortablePredicateContextInputVerificationCode
                    .WITNESS_VALUE_INVALID
                )
            available_value_byte_count += len(value_bytes)
        elif value_bytes:
            _reject(
                PortablePredicateContextInputVerificationCode
                .WITNESS_VALUE_INVALID
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


def _encode_output(
    tree: dict,
    *,
    resource_code: PortablePredicateContextInputVerificationCode,
) -> bytes:
    try:
        raw = _runtime._encode_canonical(tree)
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError:
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
    if len(raw) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(resource_code)
    return raw


def _validate_expected_candidate_schema(value: object) -> None:
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
        or not _runtime._sha256(
            value["semantic_core_contract_sha256"]
        )
        or not _runtime._sha256(value["profile_contract_sha256"])
        or not _runtime._sha256(value["program_sha256"])
        or not _runtime._sha256(
            value["evaluation_context_identity_sha256"]
        )
        or type(value["ordered_candidate_input_rows"]) is not list
        or len(value["ordered_candidate_input_rows"])
        > _MAXIMUM_WITNESS_ROWS
    ):
        _reject(
            PortablePredicateContextInputVerificationCode
            .CANDIDATE_SCHEMA_INVALID
        )
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
            or not _runtime._identifier(row["operand_id"])
            or row["claimed_resolver_outcome_id"]
            not in PORTABLE_PREDICATE_RESOLVER_OUTCOME_IDS
            or not _runtime._identifier(row["mapped_input_state_id"])
            or not _runtime._identifier(
                row["claimed_source_artifact_kind_id"]
            )
            or not _runtime._sha256(
                row["claimed_source_identity_sha256"]
            )
            or not _runtime._payload_hex(
                row["claimed_value_bytes_hex"]
            )
        ):
            _reject(
                PortablePredicateContextInputVerificationCode
                .CANDIDATE_SCHEMA_INVALID
            )


def _verify_context_quarantined_candidate_pair_v1_impl(
    program_artifact_bytes: object,
    formula_core_artifact_bytes: object,
    evaluation_context_artifact_bytes: object,
    quarantined_input_candidate_artifact_bytes: object,
    *,
    context_nonce_bytes: object,
    resolver_outcome_witnesses: object,
    compiled_profile: object,
    anchor_contract_artifacts: object,
) -> VerifiedPortablePredicateContextQuarantinedInputCandidatePairV1:
    (
        program_bytes,
        formula_bytes,
        context_bytes,
        candidate_bytes,
        nonce_bytes,
        witnesses,
        anchors,
    ) = _check_outer_types(
        program_artifact_bytes,
        formula_core_artifact_bytes,
        evaluation_context_artifact_bytes,
        quarantined_input_candidate_artifact_bytes,
        context_nonce_bytes,
        resolver_outcome_witnesses,
        anchor_contract_artifacts,
    )
    profile = _revalidate_profile(compiled_profile)
    _reject_candidate_namespace_collision(profile)
    _check_raw_resources(
        program_bytes,
        formula_bytes,
        context_bytes,
        candidate_bytes,
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
    core_tree = (
        _core.portable_predicate_language_core_verifier_contract_tree()
    )
    profile_tree = _decode_trusted_canonical(
        profile.canonical_profile_bytes
    )
    program_tree = _decode_trusted_canonical(
        program_receipt.canonical_program_bytes
    )
    nonclaims = _merged_nonclaims(core_tree, profile_tree)
    context_binding = _profile_binding(
        profile_tree,
        "predicate-evaluation-context",
    )
    input_binding = _profile_binding(
        profile_tree,
        "predicate-input-bundle",
    )

    context_tree = _decode_expected_artifact(
        context_bytes,
        resource_code=(
            PortablePredicateContextInputVerificationCode
            .CONTEXT_INPUT_RESOURCE
        ),
        json_code=(
            PortablePredicateContextInputVerificationCode
            .CONTEXT_JSON_INVALID
        ),
        tree_code=(
            PortablePredicateContextInputVerificationCode
            .CONTEXT_JSON_TREE_INVALID
        ),
        canonical_code=(
            PortablePredicateContextInputVerificationCode
            .CONTEXT_CANONICAL_MISMATCH
        ),
    )
    context_envelope = _verify_expected_envelope(
        context_bytes,
        role_id="predicate-evaluation-context",
        compiled_profile=profile,
        envelope_code=(
            PortablePredicateContextInputVerificationCode
            .CONTEXT_ENVELOPE_INVALID
        ),
        binding_code=(
            PortablePredicateContextInputVerificationCode
            .CONTEXT_BINDING_MISMATCH
        ),
    )
    if not (
        type(context_tree) is dict
        and context_tree.get("artifact_type")
        == context_binding["artifact_type_id"]
        and context_tree.get("semantic_core_contract_sha256")
        == program_receipt.semantic_core_contract_sha256
        and context_tree.get("profile_contract_sha256")
        == program_receipt.profile_contract_sha256
        and context_tree.get("program_sha256")
        == program_receipt.program_identity_sha256
        and context_tree.get("context_nonce_hex") == nonce_bytes.hex()
    ):
        _reject(
            PortablePredicateContextInputVerificationCode
            .CONTEXT_BINDING_MISMATCH
        )
    if not _same_exact(context_tree.get("nonclaim_state"), nonclaims):
        _reject(
            PortablePredicateContextInputVerificationCode
            .CONTEXT_NONCLAIM_STATE_INVALID
        )

    candidate_tree = _decode_expected_artifact(
        candidate_bytes,
        resource_code=(
            PortablePredicateContextInputVerificationCode
            .CANDIDATE_INPUT_RESOURCE
        ),
        json_code=(
            PortablePredicateContextInputVerificationCode
            .CANDIDATE_JSON_INVALID
        ),
        tree_code=(
            PortablePredicateContextInputVerificationCode
            .CANDIDATE_JSON_TREE_INVALID
        ),
        canonical_code=(
            PortablePredicateContextInputVerificationCode
            .CANDIDATE_CANONICAL_MISMATCH
        ),
    )
    _validate_expected_candidate_schema(candidate_tree)

    (
        input_rows,
        input_ids,
        outcome_ids,
        state_ids,
        source_kind_ids,
        source_sha256s,
        dispositions,
        available_value_bytes,
    ) = _derive_candidate_rows(program_tree, witnesses, core_tree)

    expected_context_tree = {
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
    reconstructed_context_bytes = _encode_output(
        expected_context_tree,
        resource_code=(
            PortablePredicateContextInputVerificationCode
            .CONTEXT_OUTPUT_RESOURCE
        ),
    )
    if reconstructed_context_bytes != context_bytes:
        _reject(
            PortablePredicateContextInputVerificationCode
            .CONTEXT_BINDING_MISMATCH
        )
    context_identity = _framed_digest(
        context_binding["digest_domain_id"],
        reconstructed_context_bytes,
    )
    if context_identity != context_envelope.artifact_identity_sha256:
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)

    if not (
        candidate_tree["semantic_core_contract_sha256"]
        == program_receipt.semantic_core_contract_sha256
        and candidate_tree["profile_contract_sha256"]
        == program_receipt.profile_contract_sha256
        and candidate_tree["program_sha256"]
        == program_receipt.program_identity_sha256
        and candidate_tree["evaluation_context_identity_sha256"]
        == context_identity
    ):
        _reject(
            PortablePredicateContextInputVerificationCode
            .CANDIDATE_BINDING_MISMATCH
        )
    if not _same_exact(
        candidate_tree["ordered_candidate_input_rows"],
        input_rows,
    ):
        _reject(
            PortablePredicateContextInputVerificationCode
            .CANDIDATE_ROW_MISMATCH
        )
    expected_candidate_tree = {
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
        "evaluation_context_identity_sha256": context_identity,
        "ordered_candidate_input_rows": input_rows,
    }
    reconstructed_candidate_bytes = _encode_output(
        expected_candidate_tree,
        resource_code=(
            PortablePredicateContextInputVerificationCode
            .CANDIDATE_OUTPUT_RESOURCE
        ),
    )
    if reconstructed_candidate_bytes != candidate_bytes:
        _reject(
            PortablePredicateContextInputVerificationCode
            .CANDIDATE_ROW_MISMATCH
        )
    candidate_identity = _framed_digest(
        PORTABLE_PREDICATE_QUARANTINED_INPUT_CANDIDATE_IDENTITY_DOMAIN,
        reconstructed_candidate_bytes,
    )

    return VerifiedPortablePredicateContextQuarantinedInputCandidatePairV1(
        canonical_evaluation_context_bytes=reconstructed_context_bytes,
        canonical_quarantined_input_candidate_bytes=(
            reconstructed_candidate_bytes
        ),
        evaluation_context_identity_sha256=context_identity,
        quarantined_input_candidate_identity_sha256=candidate_identity,
        context_byte_count=len(reconstructed_context_bytes),
        quarantined_input_candidate_byte_count=(
            len(reconstructed_candidate_bytes)
        ),
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
        program_identity_sha256=program_receipt.program_identity_sha256,
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


def verify_portable_predicate_context_quarantined_input_candidate_pair_v1(
    program_artifact_bytes: bytes,
    formula_core_artifact_bytes: bytes,
    evaluation_context_artifact_bytes: bytes,
    quarantined_input_candidate_artifact_bytes: bytes,
    *,
    context_nonce_bytes: bytes,
    resolver_outcome_witnesses: tuple,
    compiled_profile: (
        _runtime.CompiledPortablePredicateRuntimeVerifierProfileV1
    ),
    anchor_contract_artifacts: tuple = (),
) -> VerifiedPortablePredicateContextQuarantinedInputCandidatePairV1:
    """Verify one official context and one quarantined candidate."""

    try:
        return (
            _verify_context_quarantined_candidate_pair_v1_impl(
                program_artifact_bytes,
                formula_core_artifact_bytes,
                evaluation_context_artifact_bytes,
                quarantined_input_candidate_artifact_bytes,
                context_nonce_bytes=context_nonce_bytes,
                resolver_outcome_witnesses=resolver_outcome_witnesses,
                compiled_profile=compiled_profile,
                anchor_contract_artifacts=anchor_contract_artifacts,
            )
        )
    except PortablePredicateContextInputVerificationError:
        raise
    except MemoryError:
        raise
    except Exception:
        _reject(PortablePredicateContextInputVerificationCode.INTERNAL)
