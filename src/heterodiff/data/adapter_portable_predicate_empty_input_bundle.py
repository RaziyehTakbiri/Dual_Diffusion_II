"""Construct an official context/input pair for zero-input programs.

Checkpoint 56D admits only the zero-runtime-input case.  The selected
profile and complete program/formula pair are revalidated, and construction
stops before producing either artifact when the program contains any
``INPUT_RESOLVED`` operand.  The module does not run a resolver, authenticate
an authority or source, establish nonce uniqueness, or evaluate a predicate.
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
    "PORTABLE_PREDICATE_EMPTY_INPUT_BUNDLE_VALIDATION_SCOPE_ID",
    "PortablePredicateEmptyInputBundleCode",
    "PortablePredicateEmptyInputBundleError",
    "PortablePredicateContextEmptyOfficialInputBundlePairV1",
    (
        "construct_portable_predicate_context_"
        "empty_official_input_bundle_pair_v1"
    ),
)


PORTABLE_PREDICATE_EMPTY_INPUT_BUNDLE_VALIDATION_SCOPE_ID: Final = (
    "CONTEXT_AND_OFFICIAL_EMPTY_INPUT_BUNDLE_ONLY_V1"
)
_MAXIMUM_ARTIFACT_BYTES: Final = 4 * 1024 * 1024
_MAXIMUM_ANCHOR_ROWS: Final = 4096
_MAXIMUM_ANCHOR_AGGREGATE_BYTES: Final = 4 * 1024 * 1024
_MAXIMUM_IDENTIFIER_CHARACTERS: Final = 512


class PortablePredicateEmptyInputBundleCode(str, Enum):
    """Closed ordinary failures for the Checkpoint-56D constructor."""

    INPUT_TYPE = "INPUT_TYPE"
    COMPILED_PROFILE_INVALID = "COMPILED_PROFILE_INVALID"
    PROGRAM_INPUT_RESOURCE = "PROGRAM_INPUT_RESOURCE"
    FORMULA_INPUT_RESOURCE = "FORMULA_INPUT_RESOURCE"
    ANCHOR_INPUT_RESOURCE = "ANCHOR_INPUT_RESOURCE"
    CONTEXT_NONCE_INVALID = "CONTEXT_NONCE_INVALID"
    PROGRAM_FORMULA_INVALID = "PROGRAM_FORMULA_INVALID"
    INPUT_RESOLUTION_REQUIRED = "INPUT_RESOLUTION_REQUIRED"
    CONTEXT_OUTPUT_RESOURCE = "CONTEXT_OUTPUT_RESOURCE"
    INPUT_BUNDLE_OUTPUT_RESOURCE = "INPUT_BUNDLE_OUTPUT_RESOURCE"
    INTERNAL = "INTERNAL"


_ERROR_MESSAGES: Final = {
    code: (
        "portable predicate empty input bundle "
        + code.value.lower().replace("_", " ")
    )
    for code in PortablePredicateEmptyInputBundleCode
}


class PortablePredicateEmptyInputBundleError(ValueError):
    """One fixed-message Checkpoint-56D construction failure."""

    def __init__(self, code: PortablePredicateEmptyInputBundleCode):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


@dataclass(frozen=True, repr=False)
class PortablePredicateContextEmptyOfficialInputBundlePairV1:
    """Receipt for one official context and empty official input bundle."""

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
            "PortablePredicateContextEmptyOfficialInputBundlePairV1("
            "evaluation_context_identity_sha256="
            f"{self.evaluation_context_identity_sha256!r}, "
            "input_bundle_identity_sha256="
            f"{self.input_bundle_identity_sha256!r}, "
            f"context_byte_count={self.context_byte_count!r}, "
            f"input_bundle_byte_count={self.input_bundle_byte_count!r}, "
            f"validation_scope_id={self.validation_scope_id!r})"
        )


def _reject(code: PortablePredicateEmptyInputBundleCode) -> None:
    raise PortablePredicateEmptyInputBundleError(code) from None


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
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)


def _check_outer_types(
    program_artifact_bytes: object,
    formula_core_artifact_bytes: object,
    context_nonce_bytes: object,
    anchor_contract_artifacts: object,
) -> tuple:
    if (
        type(program_artifact_bytes) is not bytes
        or type(formula_core_artifact_bytes) is not bytes
        or type(context_nonce_bytes) is not bytes
        or type(anchor_contract_artifacts) is not tuple
    ):
        _reject(PortablePredicateEmptyInputBundleCode.INPUT_TYPE)
    return (
        program_artifact_bytes,
        formula_core_artifact_bytes,
        context_nonce_bytes,
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
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    if failure_code is not None:
        _reject(
            PortablePredicateEmptyInputBundleCode.COMPILED_PROFILE_INVALID
        )
    return profile


def _check_raw_resources(
    program_bytes: bytes,
    formula_bytes: bytes,
    nonce_bytes: bytes,
    anchors: tuple,
) -> None:
    if not program_bytes or len(program_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateEmptyInputBundleCode.PROGRAM_INPUT_RESOURCE
        )
    if not formula_bytes or len(formula_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateEmptyInputBundleCode.FORMULA_INPUT_RESOURCE
        )
    if len(anchors) > _MAXIMUM_ANCHOR_ROWS:
        _reject(
            PortablePredicateEmptyInputBundleCode.ANCHOR_INPUT_RESOURCE
        )
    for row in anchors:
        if (
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not str
            or type(row[1]) is not bytes
        ):
            _reject(PortablePredicateEmptyInputBundleCode.INPUT_TYPE)
    aggregate_bytes = 0
    for role_id, anchor_bytes in anchors:
        if (
            len(role_id) > _MAXIMUM_IDENTIFIER_CHARACTERS
            or not anchor_bytes
            or len(anchor_bytes) > _MAXIMUM_ARTIFACT_BYTES
        ):
            _reject(
                PortablePredicateEmptyInputBundleCode
                .ANCHOR_INPUT_RESOURCE
            )
        aggregate_bytes += len(anchor_bytes)
        if aggregate_bytes > _MAXIMUM_ANCHOR_AGGREGATE_BYTES:
            _reject(
                PortablePredicateEmptyInputBundleCode
                .ANCHOR_INPUT_RESOURCE
            )
    if len(nonce_bytes) != 32 or nonce_bytes == b"\x00" * 32:
        _reject(
            PortablePredicateEmptyInputBundleCode.CONTEXT_NONCE_INVALID
        )


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
            _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
        _reject(
            PortablePredicateEmptyInputBundleCode.PROGRAM_FORMULA_INVALID
        )


def _profile_binding(profile_tree: dict, role_id: str) -> dict:
    rows = [
        row
        for row in profile_tree["artifact_domain_rows"]
        if row["artifact_role_id"] == role_id
    ]
    if len(rows) != 1:
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    row = rows[0]
    if (
        type(row) is not dict
        or row["identity_semantics_id"] != "DOMAIN_SEPARATED_SHA256"
        or not _runtime._is_identifier(row["artifact_type_id"])
        or not _runtime._is_identifier(row["digest_domain_id"])
    ):
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    return row


def _merged_nonclaims(profile_tree: dict) -> dict:
    core_claim_ids = tuple(
        _core.PORTABLE_PREDICATE_LANGUAGE_CORE_FALSE_CLAIM_IDS
    )
    if (
        len(set(core_claim_ids)) != len(core_claim_ids)
        or any(
            not _runtime._is_identifier(claim_id)
            for claim_id in core_claim_ids
        )
    ):
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    profile_nonclaims = profile_tree["nonclaim_state"]
    if type(profile_nonclaims) is not dict:
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    result = {claim_id: False for claim_id in core_claim_ids}
    for claim_id, value in profile_nonclaims.items():
        if (
            not _runtime._is_identifier(claim_id)
            or type(value) is not bool
            or value
        ):
            _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
        result[claim_id] = False
    if not result or any(
        type(value) is not bool or value
        for value in result.values()
    ):
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    return result


def _tree_input_operand_ids(value: object) -> tuple:
    if (
        type(value) is not dict
        or type(value.get("ordered_operand_rows")) is not list
    ):
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    result = []
    for row in value["ordered_operand_rows"]:
        if (
            type(row) is not dict
            or not _runtime._is_identifier(row.get("operand_id"))
            or not _runtime._is_identifier(
                row.get("value_source_kind_id")
            )
        ):
            _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
        if row["value_source_kind_id"] == "INPUT_RESOLVED":
            result.append(row["operand_id"])
    if len(set(result)) != len(result):
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    return tuple(result)


def _validate_zero_input_program(
    program_receipt: object,
    program_tree: object,
    formula_tree: object,
) -> tuple:
    receipt_ids = program_receipt.ordered_input_operand_ids
    if (
        type(receipt_ids) is not tuple
        or any(
            not _runtime._is_identifier(operand_id)
            for operand_id in receipt_ids
        )
        or len(set(receipt_ids)) != len(receipt_ids)
    ):
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    program_ids = _tree_input_operand_ids(program_tree)
    formula_ids = _tree_input_operand_ids(formula_tree)
    if receipt_ids != program_ids or receipt_ids != formula_ids:
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    if receipt_ids:
        _reject(
            PortablePredicateEmptyInputBundleCode
            .INPUT_RESOLUTION_REQUIRED
        )
    return receipt_ids


def _exact_context_tree_is_valid(
    value: object,
    *,
    binding: dict,
    semantic_core_sha256: str,
    profile_sha256: str,
    program_sha256: str,
    nonce_hex: str,
    nonclaims: dict,
) -> bool:
    exact_fields = {
        "artifact_type",
        "format_version",
        "semantic_core_contract_sha256",
        "profile_contract_sha256",
        "program_sha256",
        "context_nonce_hex",
        "nonclaim_state",
    }
    return (
        type(value) is dict
        and set(value) == exact_fields
        and value["artifact_type"] == binding["artifact_type_id"]
        and value["format_version"] == "1"
        and value["semantic_core_contract_sha256"]
        == semantic_core_sha256
        and value["profile_contract_sha256"] == profile_sha256
        and value["program_sha256"] == program_sha256
        and value["context_nonce_hex"] == nonce_hex
        and type(value["nonclaim_state"]) is dict
        and value["nonclaim_state"] == nonclaims
        and all(
            _runtime._is_identifier(claim_id)
            and type(claim_value) is bool
            and not claim_value
            for claim_id, claim_value in value[
                "nonclaim_state"
            ].items()
        )
    )


def _exact_empty_input_bundle_tree_is_valid(
    value: object,
    *,
    binding: dict,
    semantic_core_sha256: str,
    profile_sha256: str,
    program_sha256: str,
    context_identity_sha256: str,
    nonclaims: dict,
    ordered_input_operand_ids: tuple,
) -> bool:
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
    row_fields = {
        "operand_id",
        "input_state_id",
        "source_artifact_kind_id",
        "source_identity_sha256",
        "value_bytes_hex",
    }
    if (
        type(value) is not dict
        or set(value) != exact_fields
        or value["artifact_type"] != binding["artifact_type_id"]
        or value["format_version"] != "1"
        or value["semantic_core_contract_sha256"]
        != semantic_core_sha256
        or value["profile_contract_sha256"] != profile_sha256
        or value["program_sha256"] != program_sha256
        or value["evaluation_context_identity_sha256"]
        != context_identity_sha256
        or type(value["ordered_input_rows"]) is not list
        or type(value["nonclaim_state"]) is not dict
        or value["nonclaim_state"] != nonclaims
        or any(
            not _runtime._is_identifier(claim_id)
            or type(claim_value) is not bool
            or claim_value
            for claim_id, claim_value in value[
                "nonclaim_state"
            ].items()
        )
    ):
        return False
    rows = value["ordered_input_rows"]
    for row in rows:
        if (
            type(row) is not dict
            or set(row) != row_fields
            or not _runtime._is_identifier(row["operand_id"])
            or not _runtime._is_identifier(row["input_state_id"])
            or not _runtime._is_identifier(
                row["source_artifact_kind_id"]
            )
            or not _runtime._is_sha256(
                row["source_identity_sha256"]
            )
            or not _runtime._is_payload_hex(row["value_bytes_hex"])
        ):
            return False
    return (
        tuple(row["operand_id"] for row in rows)
        == ordered_input_operand_ids
        and not ordered_input_operand_ids
        and not rows
    )


def _self_recognize_constructed_artifact(
    value: bytes,
    *,
    role_id: str,
    expected_artifact_type: str,
    expected_identity_sha256: str,
    expected_semantic_core_sha256: str,
    expected_profile_sha256: str,
    compiled_profile: object,
) -> None:
    try:
        receipt = _runtime.parse_portable_predicate_runtime_envelope_v1(
            value,
            expected_artifact_role_id=role_id,
            compiled_profile=compiled_profile,
        )
    except _runtime.PortablePredicateRuntimeEnvelopeError:
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    if (
        receipt.canonical_artifact_bytes != value
        or receipt.artifact_identity_sha256
        != expected_identity_sha256
        or receipt.artifact_byte_count != len(value)
        or receipt.artifact_role_id != role_id
        or receipt.artifact_type != expected_artifact_type
        or receipt.semantic_core_contract_sha256
        != expected_semantic_core_sha256
        or receipt.profile_contract_sha256 != expected_profile_sha256
        or receipt.validation_scope_id
        != _runtime.PORTABLE_PREDICATE_RUNTIME_ENVELOPE_VALIDATION_SCOPE_ID
        or receipt.nested_payload_semantics_validated
    ):
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)


def _construct_empty_official_input_bundle_pair_v1_impl(
    program_artifact_bytes: object,
    formula_core_artifact_bytes: object,
    *,
    context_nonce_bytes: object,
    compiled_profile: object,
    anchor_contract_artifacts: object,
) -> PortablePredicateContextEmptyOfficialInputBundlePairV1:
    (
        program_bytes,
        formula_bytes,
        nonce_bytes,
        anchors,
    ) = _check_outer_types(
        program_artifact_bytes,
        formula_core_artifact_bytes,
        context_nonce_bytes,
        anchor_contract_artifacts,
    )
    profile = _revalidate_profile(compiled_profile)
    _check_raw_resources(
        program_bytes,
        formula_bytes,
        nonce_bytes,
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
    formula_tree = _decode_trusted_canonical(
        program_receipt.canonical_formula_core_bytes
    )
    if (
        type(profile_tree) is not dict
        or type(program_tree) is not dict
        or type(formula_tree) is not dict
    ):
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    input_operand_ids = _validate_zero_input_program(
        program_receipt,
        program_tree,
        formula_tree,
    )
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
    if not _exact_context_tree_is_valid(
        context_tree,
        binding=context_binding,
        semantic_core_sha256=(
            program_receipt.semantic_core_contract_sha256
        ),
        profile_sha256=program_receipt.profile_contract_sha256,
        program_sha256=program_receipt.program_identity_sha256,
        nonce_hex=nonce_bytes.hex(),
        nonclaims=nonclaims,
    ):
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    context_bytes = _runtime._canonical_json(context_tree)
    if len(context_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateEmptyInputBundleCode.CONTEXT_OUTPUT_RESOURCE
        )
    context_identity = _runtime._domain_sha256(
        context_binding["digest_domain_id"],
        context_bytes,
    )
    if not _runtime._is_sha256(context_identity):
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    _self_recognize_constructed_artifact(
        context_bytes,
        role_id="predicate-evaluation-context",
        expected_artifact_type=context_binding["artifact_type_id"],
        expected_identity_sha256=context_identity,
        expected_semantic_core_sha256=(
            program_receipt.semantic_core_contract_sha256
        ),
        expected_profile_sha256=(
            program_receipt.profile_contract_sha256
        ),
        compiled_profile=profile,
    )

    input_bundle_tree = {
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
    if not _exact_empty_input_bundle_tree_is_valid(
        input_bundle_tree,
        binding=input_binding,
        semantic_core_sha256=(
            program_receipt.semantic_core_contract_sha256
        ),
        profile_sha256=program_receipt.profile_contract_sha256,
        program_sha256=program_receipt.program_identity_sha256,
        context_identity_sha256=context_identity,
        nonclaims=nonclaims,
        ordered_input_operand_ids=input_operand_ids,
    ):
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
    input_bundle_bytes = _runtime._canonical_json(input_bundle_tree)
    if len(input_bundle_bytes) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(
            PortablePredicateEmptyInputBundleCode
            .INPUT_BUNDLE_OUTPUT_RESOURCE
        )
    input_bundle_identity = _runtime._domain_sha256(
        input_binding["digest_domain_id"],
        input_bundle_bytes,
    )
    if not _runtime._is_sha256(input_bundle_identity):
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)

    _self_recognize_constructed_artifact(
        input_bundle_bytes,
        role_id="predicate-input-bundle",
        expected_artifact_type=input_binding["artifact_type_id"],
        expected_identity_sha256=input_bundle_identity,
        expected_semantic_core_sha256=(
            program_receipt.semantic_core_contract_sha256
        ),
        expected_profile_sha256=(
            program_receipt.profile_contract_sha256
        ),
        compiled_profile=profile,
    )

    return PortablePredicateContextEmptyOfficialInputBundlePairV1(
        canonical_evaluation_context_bytes=context_bytes,
        canonical_input_bundle_bytes=input_bundle_bytes,
        evaluation_context_identity_sha256=context_identity,
        input_bundle_identity_sha256=input_bundle_identity,
        context_byte_count=len(context_bytes),
        input_bundle_byte_count=len(input_bundle_bytes),
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
        program_identity_sha256=(
            program_receipt.program_identity_sha256
        ),
        formula_core_identity_sha256=(
            program_receipt.formula_core_identity_sha256
        ),
        program_id=program_receipt.program_id,
        program_purpose_id=program_receipt.program_purpose_id,
        context_nonce_hex=nonce_bytes.hex(),
        ordered_input_operand_ids=input_operand_ids,
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


def construct_portable_predicate_context_empty_official_input_bundle_pair_v1(
    program_artifact_bytes: bytes,
    formula_core_artifact_bytes: bytes,
    *,
    context_nonce_bytes: bytes,
    compiled_profile: _runtime.CompiledPortablePredicateRuntimeProfileV1,
    anchor_contract_artifacts: tuple = (),
) -> PortablePredicateContextEmptyOfficialInputBundlePairV1:
    """Construct an official context/input pair for one zero-input program."""

    try:
        return _construct_empty_official_input_bundle_pair_v1_impl(
            program_artifact_bytes,
            formula_core_artifact_bytes,
            context_nonce_bytes=context_nonce_bytes,
            compiled_profile=compiled_profile,
            anchor_contract_artifacts=anchor_contract_artifacts,
        )
    except PortablePredicateEmptyInputBundleError:
        raise
    except MemoryError:
        raise
    except Exception:
        _reject(PortablePredicateEmptyInputBundleCode.INTERNAL)
