"""Independent verifier for the zero-input official runtime pair.

Checkpoint 56D admits one deliberately narrow constructive boundary: when a
fully revalidated portable predicate program has no ``INPUT_RESOLVED``
operands, its official input bundle is uniquely the canonical empty bundle.
No resolver evidence is needed in that zero-input case.  This verifier
independently reconstructs both the evaluation context and that empty input
bundle from verifier-side contracts and requires exact byte equality.

This module does not import the source constructor, any source-side type or
constant, or the Checkpoint-56C quarantine implementation.  Acceptance does
not claim nonce uniqueness, resolver execution, locator resolution, source
authenticity, authority authentication, or predicate evaluation.
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
    "PORTABLE_PREDICATE_EMPTY_INPUT_BUNDLE_VALIDATION_SCOPE_ID",
    "PortablePredicateEmptyInputBundleVerificationCode",
    "PortablePredicateEmptyInputBundleVerificationError",
    "VerifiedPortablePredicateContextEmptyOfficialInputBundlePairV1",
    (
        "verify_portable_predicate_context_"
        "empty_official_input_bundle_pair_v1"
    ),
)


PORTABLE_PREDICATE_EMPTY_INPUT_BUNDLE_VALIDATION_SCOPE_ID: Final = (
    "CONTEXT_AND_OFFICIAL_EMPTY_INPUT_BUNDLE_ONLY_V1"
)
_MAXIMUM_ARTIFACT_BYTES: Final = 4 * 1024 * 1024
_MAXIMUM_ANCHOR_ROWS: Final = 4096
_MAXIMUM_ANCHOR_AGGREGATE_BYTES: Final = 4 * 1024 * 1024
_MAXIMUM_INPUT_ROWS: Final = 512
_MAXIMUM_JSON_INTEGER_DIGITS: Final = 20
_MAXIMUM_IDENTIFIER_CHARACTERS: Final = 512


class PortablePredicateEmptyInputBundleVerificationCode(str, Enum):
    """Closed ordinary failures for the independent Checkpoint-56D lane."""

    INPUT_TYPE = "INPUT_TYPE"
    COMPILED_PROFILE_INVALID = "COMPILED_PROFILE_INVALID"
    PROGRAM_INPUT_RESOURCE = "PROGRAM_INPUT_RESOURCE"
    FORMULA_INPUT_RESOURCE = "FORMULA_INPUT_RESOURCE"
    CONTEXT_INPUT_RESOURCE = "CONTEXT_INPUT_RESOURCE"
    INPUT_BUNDLE_INPUT_RESOURCE = "INPUT_BUNDLE_INPUT_RESOURCE"
    ANCHOR_INPUT_RESOURCE = "ANCHOR_INPUT_RESOURCE"
    CONTEXT_NONCE_INVALID = "CONTEXT_NONCE_INVALID"
    PROGRAM_FORMULA_INVALID = "PROGRAM_FORMULA_INVALID"
    INPUT_RESOLUTION_REQUIRED = "INPUT_RESOLUTION_REQUIRED"
    CONTEXT_JSON_INVALID = "CONTEXT_JSON_INVALID"
    CONTEXT_JSON_TREE_INVALID = "CONTEXT_JSON_TREE_INVALID"
    CONTEXT_CANONICAL_MISMATCH = "CONTEXT_CANONICAL_MISMATCH"
    CONTEXT_ENVELOPE_INVALID = "CONTEXT_ENVELOPE_INVALID"
    CONTEXT_BINDING_MISMATCH = "CONTEXT_BINDING_MISMATCH"
    CONTEXT_NONCLAIM_STATE_INVALID = "CONTEXT_NONCLAIM_STATE_INVALID"
    INPUT_BUNDLE_JSON_INVALID = "INPUT_BUNDLE_JSON_INVALID"
    INPUT_BUNDLE_JSON_TREE_INVALID = "INPUT_BUNDLE_JSON_TREE_INVALID"
    INPUT_BUNDLE_CANONICAL_MISMATCH = "INPUT_BUNDLE_CANONICAL_MISMATCH"
    INPUT_BUNDLE_ENVELOPE_INVALID = "INPUT_BUNDLE_ENVELOPE_INVALID"
    INPUT_BUNDLE_BINDING_MISMATCH = "INPUT_BUNDLE_BINDING_MISMATCH"
    INPUT_BUNDLE_SCHEMA_INVALID = "INPUT_BUNDLE_SCHEMA_INVALID"
    INPUT_BUNDLE_ROW_MISMATCH = "INPUT_BUNDLE_ROW_MISMATCH"
    INPUT_BUNDLE_NONCLAIM_STATE_INVALID = (
        "INPUT_BUNDLE_NONCLAIM_STATE_INVALID"
    )
    CONTEXT_OUTPUT_RESOURCE = "CONTEXT_OUTPUT_RESOURCE"
    INPUT_BUNDLE_OUTPUT_RESOURCE = "INPUT_BUNDLE_OUTPUT_RESOURCE"
    INTERNAL = "INTERNAL"


_ERROR_MESSAGES: Final = {
    code: (
        "portable predicate empty input bundle verification "
        + code.value.lower().replace("_", " ")
    )
    for code in PortablePredicateEmptyInputBundleVerificationCode
}


class PortablePredicateEmptyInputBundleVerificationError(ValueError):
    """One fixed-message independent-verifier failure."""

    def __init__(
        self,
        code: PortablePredicateEmptyInputBundleVerificationCode,
    ):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


@dataclass(frozen=True, repr=False)
class VerifiedPortablePredicateContextEmptyOfficialInputBundlePairV1:
    """Immutable verification receipt for one exact zero-input pair."""

    __slots__ = (
        "canonical_evaluation_context_bytes",
        "canonical_input_bundle_bytes",
        "evaluation_context_identity_sha256",
        "input_bundle_identity_sha256",
        "context_byte_count",
        "input_bundle_byte_count",
        "evaluation_context_artifact_type",
        "input_bundle_artifact_type",
        "semantic_core_contract_sha256",
        "profile_contract_sha256",
        "profile_id",
        "program_identity_sha256",
        "formula_core_identity_sha256",
        "program_id",
        "program_purpose_id",
        "context_nonce_hex",
        "ordered_input_operand_ids",
        "input_row_count",
        "validation_scope_id",
        "program_formula_revalidated",
        "zero_input_program_validated",
        "context_constructed_and_envelope_validated",
        "official_input_bundle_constructed",
        "official_input_bundle_envelope_validated",
        "official_input_bundle_nested_semantics_validated",
        "no_input_resolution_required",
        "resolver_derived_input_semantics_validated",
        "context_nonce_uniqueness_validated",
        "runtime_resolver_executed",
        "locator_resolution_validated",
        "source_authenticity_validated",
        "authority_authentication_validated",
        "evaluation_performed",
    )

    canonical_evaluation_context_bytes: bytes
    canonical_input_bundle_bytes: bytes
    evaluation_context_identity_sha256: str
    input_bundle_identity_sha256: str
    context_byte_count: int
    input_bundle_byte_count: int
    evaluation_context_artifact_type: str
    input_bundle_artifact_type: str
    semantic_core_contract_sha256: str
    profile_contract_sha256: str
    profile_id: str
    program_identity_sha256: str
    formula_core_identity_sha256: str
    program_id: str
    program_purpose_id: str
    context_nonce_hex: str
    ordered_input_operand_ids: tuple
    input_row_count: int
    validation_scope_id: str
    program_formula_revalidated: bool
    zero_input_program_validated: bool
    context_constructed_and_envelope_validated: bool
    official_input_bundle_constructed: bool
    official_input_bundle_envelope_validated: bool
    official_input_bundle_nested_semantics_validated: bool
    no_input_resolution_required: bool
    resolver_derived_input_semantics_validated: bool
    context_nonce_uniqueness_validated: bool
    runtime_resolver_executed: bool
    locator_resolution_validated: bool
    source_authenticity_validated: bool
    authority_authentication_validated: bool
    evaluation_performed: bool

    def __repr__(self) -> str:
        return (
            "VerifiedPortablePredicateContext"
            "EmptyOfficialInputBundlePairV1("
            f"context_byte_count={self.context_byte_count}, "
            f"input_bundle_byte_count={self.input_bundle_byte_count}, "
            f"input_row_count={self.input_row_count}, "
            f"validation_scope_id={self.validation_scope_id!r}, "
            f"evaluation_performed={self.evaluation_performed})"
        )


def _reject(
    code: PortablePredicateEmptyInputBundleVerificationCode,
) -> None:
    raise PortablePredicateEmptyInputBundleVerificationError(code) from None


def _check_outer_types(
    program_artifact_bytes: object,
    formula_core_artifact_bytes: object,
    evaluation_context_artifact_bytes: object,
    input_bundle_artifact_bytes: object,
    context_nonce_bytes: object,
    anchor_contract_artifacts: object,
) -> tuple:
    if (
        type(program_artifact_bytes) is not bytes
        or type(formula_core_artifact_bytes) is not bytes
        or type(evaluation_context_artifact_bytes) is not bytes
        or type(input_bundle_artifact_bytes) is not bytes
        or type(context_nonce_bytes) is not bytes
        or type(anchor_contract_artifacts) is not tuple
    ):
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INPUT_TYPE)
    return (
        program_artifact_bytes,
        formula_core_artifact_bytes,
        evaluation_context_artifact_bytes,
        input_bundle_artifact_bytes,
        context_nonce_bytes,
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
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    if failure_code is not None:
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .COMPILED_PROFILE_INVALID
        )
    if profile is None:
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    return profile


def _check_raw_resources(
    program_bytes: bytes,
    formula_bytes: bytes,
    context_bytes: bytes,
    input_bundle_bytes: bytes,
    nonce_bytes: bytes,
    anchors: tuple,
) -> None:
    if not program_bytes or len(program_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .PROGRAM_INPUT_RESOURCE
        )
    if not formula_bytes or len(formula_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .FORMULA_INPUT_RESOURCE
        )
    if not context_bytes or len(context_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .CONTEXT_INPUT_RESOURCE
        )
    if (
        not input_bundle_bytes
        or len(input_bundle_bytes) > _MAXIMUM_ARTIFACT_BYTES
    ):
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_INPUT_RESOURCE
        )
    if len(anchors) > _MAXIMUM_ANCHOR_ROWS:
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .ANCHOR_INPUT_RESOURCE
        )
    for row in anchors:
        if (
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not str
            or type(row[1]) is not bytes
        ):
            _reject(
                PortablePredicateEmptyInputBundleVerificationCode.INPUT_TYPE
            )
    for row in anchors:
        anchor_bytes = row[1]
        if (
            len(row[0]) > _MAXIMUM_IDENTIFIER_CHARACTERS
            or not anchor_bytes
            or len(anchor_bytes) > _MAXIMUM_ARTIFACT_BYTES
        ):
            _reject(
                PortablePredicateEmptyInputBundleVerificationCode
                .ANCHOR_INPUT_RESOURCE
            )
    if (
        sum(len(row[1]) for row in anchors)
        > _MAXIMUM_ANCHOR_AGGREGATE_BYTES
    ):
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .ANCHOR_INPUT_RESOURCE
        )
    if len(nonce_bytes) != 32 or nonce_bytes == b"\x00" * 32:
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
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
            _reject(
                PortablePredicateEmptyInputBundleVerificationCode.INTERNAL
            )
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
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
    resource_code: PortablePredicateEmptyInputBundleVerificationCode,
    json_code: PortablePredicateEmptyInputBundleVerificationCode,
    tree_code: PortablePredicateEmptyInputBundleVerificationCode,
    canonical_code: PortablePredicateEmptyInputBundleVerificationCode,
) -> object:
    try:
        preflight = _runtime._preflight_json(raw)
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError:
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
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
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    if status == "resource-invalid":
        _reject(resource_code)
    if status != "valid":
        _reject(tree_code)
    try:
        canonical = _runtime._encode_canonical(decoded)
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError:
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
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
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    if type(decoded) is not dict:
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    return decoded


def _verify_expected_envelope(
    value: bytes,
    *,
    role_id: str,
    compiled_profile: object,
    envelope_code: PortablePredicateEmptyInputBundleVerificationCode,
    binding_code: PortablePredicateEmptyInputBundleVerificationCode,
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
            _reject(
                PortablePredicateEmptyInputBundleVerificationCode.INTERNAL
            )
        if error.code == (
            _runtime
            .PortablePredicateRuntimeEnvelopeVerificationCode
            .ARTIFACT_BINDING_MISMATCH
            .value
        ):
            _reject(binding_code)
        _reject(envelope_code)


def _profile_binding(profile_tree: dict, role_id: str) -> dict:
    try:
        rows = [
            row
            for row in profile_tree["artifact_domain_rows"]
            if row["artifact_role_id"] == role_id
        ]
    except (KeyError, TypeError):
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    if len(rows) != 1:
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    row = rows[0]
    if row.get("identity_semantics_id") != "DOMAIN_SEPARATED_SHA256":
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    if (
        not _runtime._identifier(row.get("artifact_type_id"))
        or not _runtime._identifier(row.get("digest_domain_id"))
    ):
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    return row


def _merged_nonclaims(core_tree: dict, profile_tree: dict) -> dict:
    core_nonclaims = core_tree.get("nonclaim_state")
    profile_nonclaims = profile_tree.get("nonclaim_state")
    if type(core_nonclaims) is not dict or type(profile_nonclaims) is not dict:
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    result = {}
    for claim_id, value in core_nonclaims.items():
        if (
            not _runtime._identifier(claim_id)
            or type(value) is not bool
            or value
            or claim_id in result
        ):
            _reject(
                PortablePredicateEmptyInputBundleVerificationCode.INTERNAL
            )
        result[claim_id] = False
    for claim_id, value in profile_nonclaims.items():
        if (
            not _runtime._identifier(claim_id)
            or type(value) is not bool
            or value
        ):
            _reject(
                PortablePredicateEmptyInputBundleVerificationCode.INTERNAL
            )
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
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _validate_envelope_receipt(
    receipt: object,
    raw: bytes,
    *,
    identity_sha256: str,
    role_id: str,
    family_id: str,
    artifact_type: str,
    semantic_core_sha256: str,
    profile_sha256: str,
) -> None:
    if (
        type(receipt)
        is not _runtime.PortablePredicateRuntimeVerifierEnvelopeV1
        or receipt.canonical_artifact_bytes != raw
        or receipt.artifact_identity_sha256 != identity_sha256
        or receipt.artifact_byte_count != len(raw)
        or receipt.artifact_role_id != role_id
        or receipt.artifact_family_id != family_id
        or receipt.artifact_type != artifact_type
        or receipt.semantic_core_contract_sha256
        != semantic_core_sha256
        or receipt.profile_contract_sha256 != profile_sha256
        or receipt.validation_scope_id
        != _runtime
        .PORTABLE_PREDICATE_RUNTIME_ENVELOPE_VALIDATION_SCOPE_ID
        or receipt.nested_payload_semantics_validated
    ):
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)


def _tree_input_operand_ids(value: object) -> tuple:
    if (
        type(value) is not dict
        or type(value.get("ordered_operand_rows")) is not list
    ):
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    result = []
    for row in value["ordered_operand_rows"]:
        if (
            type(row) is not dict
            or not _runtime._identifier(row.get("operand_id"))
            or not _runtime._identifier(
                row.get("value_source_kind_id")
            )
        ):
            _reject(
                PortablePredicateEmptyInputBundleVerificationCode.INTERNAL
            )
        if row["value_source_kind_id"] == "INPUT_RESOLVED":
            result.append(row["operand_id"])
    if len(set(result)) != len(result):
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    return tuple(result)


def _validate_zero_input_program(
    program_receipt: object,
    program_tree: object,
    formula_tree: object,
) -> tuple:
    try:
        receipt_ids = program_receipt.ordered_input_operand_ids
    except AttributeError:
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    if (
        type(receipt_ids) is not tuple
        or any(
            not _runtime._identifier(operand_id)
            for operand_id in receipt_ids
        )
        or len(set(receipt_ids)) != len(receipt_ids)
    ):
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    program_ids = _tree_input_operand_ids(program_tree)
    formula_ids = _tree_input_operand_ids(formula_tree)
    if receipt_ids != program_ids or receipt_ids != formula_ids:
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    if receipt_ids:
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_RESOLUTION_REQUIRED
        )
    return receipt_ids


def _validate_input_bundle_nested_schema(value: object) -> None:
    exact_fields = {
        "artifact_type",
        "format_version",
        "semantic_core_contract_sha256",
        "profile_contract_sha256",
        "program_sha256",
        "evaluation_context_identity_sha256",
        "ordered_input_rows",
        "nonclaim_state",
    }
    if (
        type(value) is not dict
        or set(value) != exact_fields
        or type(value.get("ordered_input_rows")) is not list
        or len(value["ordered_input_rows"]) > _MAXIMUM_INPUT_ROWS
    ):
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_SCHEMA_INVALID
        )
    row_fields = {
        "operand_id",
        "input_state_id",
        "source_artifact_kind_id",
        "source_identity_sha256",
        "value_bytes_hex",
    }
    for row in value["ordered_input_rows"]:
        if (
            type(row) is not dict
            or set(row) != row_fields
            or not _runtime._identifier(row["operand_id"])
            or not _runtime._identifier(row["input_state_id"])
            or not _runtime._identifier(row["source_artifact_kind_id"])
            or not _runtime._sha256(row["source_identity_sha256"])
            or not _runtime._payload_hex(row["value_bytes_hex"])
        ):
            _reject(
                PortablePredicateEmptyInputBundleVerificationCode
                .INPUT_BUNDLE_SCHEMA_INVALID
            )


def _encode_output(
    tree: dict,
    *,
    resource_code: PortablePredicateEmptyInputBundleVerificationCode,
) -> bytes:
    try:
        raw = _runtime._encode_canonical(tree)
    except _runtime.PortablePredicateRuntimeEnvelopeVerificationError:
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
    if len(raw) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(resource_code)
    return raw


def _verify_context_empty_official_input_bundle_pair_v1_impl(
    program_artifact_bytes: object,
    formula_core_artifact_bytes: object,
    evaluation_context_artifact_bytes: object,
    input_bundle_artifact_bytes: object,
    *,
    context_nonce_bytes: object,
    compiled_profile: object,
    anchor_contract_artifacts: object,
) -> VerifiedPortablePredicateContextEmptyOfficialInputBundlePairV1:
    (
        program_bytes,
        formula_bytes,
        context_bytes,
        input_bundle_bytes,
        nonce_bytes,
        anchors,
    ) = _check_outer_types(
        program_artifact_bytes,
        formula_core_artifact_bytes,
        evaluation_context_artifact_bytes,
        input_bundle_artifact_bytes,
        context_nonce_bytes,
        anchor_contract_artifacts,
    )
    profile = _revalidate_profile(compiled_profile)
    _check_raw_resources(
        program_bytes,
        formula_bytes,
        context_bytes,
        input_bundle_bytes,
        nonce_bytes,
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
    formula_tree = _decode_trusted_canonical(
        program_receipt.canonical_formula_core_bytes
    )
    input_ids = _validate_zero_input_program(
        program_receipt,
        program_tree,
        formula_tree,
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
            PortablePredicateEmptyInputBundleVerificationCode
            .CONTEXT_INPUT_RESOURCE
        ),
        json_code=(
            PortablePredicateEmptyInputBundleVerificationCode
            .CONTEXT_JSON_INVALID
        ),
        tree_code=(
            PortablePredicateEmptyInputBundleVerificationCode
            .CONTEXT_JSON_TREE_INVALID
        ),
        canonical_code=(
            PortablePredicateEmptyInputBundleVerificationCode
            .CONTEXT_CANONICAL_MISMATCH
        ),
    )
    context_envelope = _verify_expected_envelope(
        context_bytes,
        role_id="predicate-evaluation-context",
        compiled_profile=profile,
        envelope_code=(
            PortablePredicateEmptyInputBundleVerificationCode
            .CONTEXT_ENVELOPE_INVALID
        ),
        binding_code=(
            PortablePredicateEmptyInputBundleVerificationCode
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
            PortablePredicateEmptyInputBundleVerificationCode
            .CONTEXT_BINDING_MISMATCH
        )
    if not _same_exact(context_tree.get("nonclaim_state"), nonclaims):
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .CONTEXT_NONCLAIM_STATE_INVALID
        )

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
            PortablePredicateEmptyInputBundleVerificationCode
            .CONTEXT_OUTPUT_RESOURCE
        ),
    )
    if reconstructed_context_bytes != context_bytes:
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .CONTEXT_BINDING_MISMATCH
        )
    context_identity = _framed_digest(
        context_binding["digest_domain_id"],
        reconstructed_context_bytes,
    )
    _validate_envelope_receipt(
        context_envelope,
        reconstructed_context_bytes,
        identity_sha256=context_identity,
        role_id="predicate-evaluation-context",
        family_id="PredicateEvaluationContextV1",
        artifact_type=context_binding["artifact_type_id"],
        semantic_core_sha256=(
            program_receipt.semantic_core_contract_sha256
        ),
        profile_sha256=program_receipt.profile_contract_sha256,
    )

    input_bundle_tree = _decode_expected_artifact(
        input_bundle_bytes,
        resource_code=(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_INPUT_RESOURCE
        ),
        json_code=(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_JSON_INVALID
        ),
        tree_code=(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_JSON_TREE_INVALID
        ),
        canonical_code=(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_CANONICAL_MISMATCH
        ),
    )
    input_bundle_envelope = _verify_expected_envelope(
        input_bundle_bytes,
        role_id="predicate-input-bundle",
        compiled_profile=profile,
        envelope_code=(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_ENVELOPE_INVALID
        ),
        binding_code=(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_BINDING_MISMATCH
        ),
    )
    _validate_input_bundle_nested_schema(input_bundle_tree)
    if not (
        input_bundle_tree["artifact_type"]
        == input_binding["artifact_type_id"]
        and input_bundle_tree["semantic_core_contract_sha256"]
        == program_receipt.semantic_core_contract_sha256
        and input_bundle_tree["profile_contract_sha256"]
        == program_receipt.profile_contract_sha256
        and input_bundle_tree["program_sha256"]
        == program_receipt.program_identity_sha256
        and input_bundle_tree["evaluation_context_identity_sha256"]
        == context_identity
    ):
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_BINDING_MISMATCH
        )
    if input_bundle_tree["ordered_input_rows"] != []:
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_ROW_MISMATCH
        )
    if not _same_exact(
        input_bundle_tree.get("nonclaim_state"),
        nonclaims,
    ):
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_NONCLAIM_STATE_INVALID
        )

    expected_input_bundle_tree = {
        "artifact_type": input_binding["artifact_type_id"],
        "format_version": "1",
        "semantic_core_contract_sha256": (
            program_receipt.semantic_core_contract_sha256
        ),
        "profile_contract_sha256": (
            program_receipt.profile_contract_sha256
        ),
        "program_sha256": program_receipt.program_identity_sha256,
        "evaluation_context_identity_sha256": context_identity,
        "ordered_input_rows": [],
        "nonclaim_state": nonclaims,
    }
    reconstructed_input_bundle_bytes = _encode_output(
        expected_input_bundle_tree,
        resource_code=(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_OUTPUT_RESOURCE
        ),
    )
    if reconstructed_input_bundle_bytes != input_bundle_bytes:
        _reject(
            PortablePredicateEmptyInputBundleVerificationCode
            .INPUT_BUNDLE_ROW_MISMATCH
        )
    input_bundle_identity = _framed_digest(
        input_binding["digest_domain_id"],
        reconstructed_input_bundle_bytes,
    )
    _validate_envelope_receipt(
        input_bundle_envelope,
        reconstructed_input_bundle_bytes,
        identity_sha256=input_bundle_identity,
        role_id="predicate-input-bundle",
        family_id="PredicateInputBundleV1",
        artifact_type=input_binding["artifact_type_id"],
        semantic_core_sha256=(
            program_receipt.semantic_core_contract_sha256
        ),
        profile_sha256=program_receipt.profile_contract_sha256,
    )

    return VerifiedPortablePredicateContextEmptyOfficialInputBundlePairV1(
        canonical_evaluation_context_bytes=reconstructed_context_bytes,
        canonical_input_bundle_bytes=reconstructed_input_bundle_bytes,
        evaluation_context_identity_sha256=context_identity,
        input_bundle_identity_sha256=input_bundle_identity,
        context_byte_count=len(reconstructed_context_bytes),
        input_bundle_byte_count=len(reconstructed_input_bundle_bytes),
        evaluation_context_artifact_type=(
            context_binding["artifact_type_id"]
        ),
        input_bundle_artifact_type=input_binding["artifact_type_id"],
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
        input_row_count=0,
        validation_scope_id=(
            PORTABLE_PREDICATE_EMPTY_INPUT_BUNDLE_VALIDATION_SCOPE_ID
        ),
        program_formula_revalidated=True,
        zero_input_program_validated=True,
        context_constructed_and_envelope_validated=True,
        official_input_bundle_constructed=True,
        official_input_bundle_envelope_validated=True,
        official_input_bundle_nested_semantics_validated=True,
        no_input_resolution_required=True,
        resolver_derived_input_semantics_validated=False,
        context_nonce_uniqueness_validated=False,
        runtime_resolver_executed=False,
        locator_resolution_validated=False,
        source_authenticity_validated=False,
        authority_authentication_validated=False,
        evaluation_performed=False,
    )


def verify_portable_predicate_context_empty_official_input_bundle_pair_v1(
    program_artifact_bytes: bytes,
    formula_core_artifact_bytes: bytes,
    evaluation_context_artifact_bytes: bytes,
    input_bundle_artifact_bytes: bytes,
    *,
    context_nonce_bytes: bytes,
    compiled_profile: (
        _runtime.CompiledPortablePredicateRuntimeVerifierProfileV1
    ),
    anchor_contract_artifacts: tuple = (),
) -> VerifiedPortablePredicateContextEmptyOfficialInputBundlePairV1:
    """Verify one exact official context/empty-input-bundle pair."""

    try:
        return _verify_context_empty_official_input_bundle_pair_v1_impl(
            program_artifact_bytes,
            formula_core_artifact_bytes,
            evaluation_context_artifact_bytes,
            input_bundle_artifact_bytes,
            context_nonce_bytes=context_nonce_bytes,
            compiled_profile=compiled_profile,
            anchor_contract_artifacts=anchor_contract_artifacts,
        )
    except PortablePredicateEmptyInputBundleVerificationError:
        raise
    except MemoryError:
        raise
    except Exception:
        _reject(PortablePredicateEmptyInputBundleVerificationCode.INTERNAL)
