"""Implementation-separated verifier for static predicate composition.

This module uses only verifier-lane dependencies.  It never imports the
source compositor or the frozen monolithic Linux predecessor implementation.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Final

from .adapter_portable_predicate_language_core_verifier import (
    PortablePredicateLanguageCoreVerificationError,
    parse_portable_predicate_language_core_verifier_contract,
    portable_predicate_language_core_verifier_contract_sha256,
    portable_predicate_language_core_verifier_profile_interface_sha256,
    validate_portable_predicate_profile_verifier_tree,
)


_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-composition-contract.v1"
)
_CORE_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-semantic-core-contract.v1"
)
_DESCRIPTOR_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-composed-descriptor.v1"
)
_RESULT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-predecessor-projection-"
    "result.v1"
)
_PREDECESSOR_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-portable-predicate-language-"
    "contract.v1"
)
_LINUX_PROFILE_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-predicate-profile-contract.v1"
)
_ENCODING_ID: Final = "canonical-ascii-json-sort-keys-no-whitespace-v1"
_DIGEST_COMPUTATION_ID: Final = (
    "sha256-domain-nul-u64be-length-canonical-bytes-v1"
)
_IMPLEMENTATION_STATUS: Final = (
    "STATIC_GENERIC_COMPOSITION_AND_LINUX_PREDECESSOR_PROJECTION_IMPLEMENTED_"
    "RUNTIME_EVALUATOR_NOT_IMPLEMENTED"
)
_VALIDATION_SCOPE: Final = (
    "GENERIC_CORE_PROFILE_COMPOSITION_AND_NAMED_STATIC_LINUX_PREDECESSOR_"
    "PROJECTIONS_ONLY"
)
_VERIFIER_ID: Final = (
    "heterodiff.adapter.portable-predicate-language-composition-"
    "implementation-separated-verifier.v1"
)
_PROJECTION_STATUS: Final = (
    "CALLER_PINNED_PREDECESSOR_KAT_AND_STATIC_PROJECTION_CORRESPONDENCE_"
    "VALIDATED_NO_BEHAVIORAL_EQUIVALENCE_CLAIM"
)

_MAXIMUM_ARTIFACT_BYTES: Final = 4 * 1024 * 1024
_MAXIMUM_JSON_DEPTH: Final = 32
_MAXIMUM_JSON_ITEMS: Final = 65536
_MAXIMUM_JSON_INTEGER_DIGITS: Final = 20
_MAXIMUM_PROFILE_ARTIFACT_TYPE_BYTES: Final = 512
_IDENTIFIER_RE: Final = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$"
)
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")

_V1_CONTRACT_BYTE_COUNT: Final = 3536
_V1_CONTRACT_PLAIN_SHA256: Final = (
    "99c37e0b78cf0efcfca08e40f8eea775650719885e8716d48cbf5740e7692926"
)
_V1_CONTRACT_SHA256: Final = (
    "41bd731707390d30517f80fd4440e377d00f31898bde0f465dddbd3f315429d4"
)
_V1_CORE_BYTE_COUNT: Final = 57674
_V1_CORE_PLAIN_SHA256: Final = (
    "b13e1d349c08449096bd901e46087bbcc44181365354b553e6ecd89172864dc2"
)
_V1_CORE_SHA256: Final = (
    "387b45d6f4ae8485433b36b929ed4d3a7b146c61e5d12629d46e2a74aa4536b2"
)
_V1_PROFILE_BYTE_COUNT: Final = 15992
_V1_PROFILE_PLAIN_SHA256: Final = (
    "82a36c2ca07d25afc4cc44e2fa6ae1b2e481b77fb96bc56396bd6e54fb5be658"
)
_V1_PROFILE_SHA256: Final = (
    "31204b1598e203e920fb8b1349116bc27a5162a34fe50ec5112ef957cb9bbdd7"
)
_V1_PREDECESSOR_BYTE_COUNT: Final = 59865
_V1_PREDECESSOR_PLAIN_SHA256: Final = (
    "f019fccbb0fc05689bba21e57fa9e922735034865c01105ea4ab595cbfd93463"
)
_V1_PREDECESSOR_SHA256: Final = (
    "6cee841ff42b044c8a0fd25ca72e6a360079d25022e1022203991fb61667e8ee"
)

_CORE_COMPONENT_IDS: Final = (
    "field-value-json-kind-registry",
    "contract-parser-error-registry",
    "resource-limits",
    "type-kind-schema-with-interval-refinement",
    "value-encoding-registry",
    "constructor-registry-with-field-alias",
    "constructor-failure-registry-order-insensitive",
    "constructor-failure-precedence",
    "operator-registry-with-profile-specializations",
    "resolution-requirement-registry",
    "input-state-registry-with-public-error-role-map",
    "path-segment-schema-registry",
    "fault-precedence-registry",
)
_PROFILE_COMPONENT_IDS: Final = (
    "native-mapping-anchor",
    "artifact-domain-bindings",
    "authority-class-registry",
    "public-error-registry",
    "public-error-role-bindings",
    "local-rule-failed-public-error-binding",
    "profile-parameter-bindings",
    "locator-extension-bindings",
    "locator-path-cardinality-bindings",
    "program-purpose-binding",
    "program-purpose-relation-bindings",
    "profile-field-value-schema-bindings",
    "operator-specialization-binding",
    "interval-refinement-binding",
    "profile-nonclaim-subset",
)
_LEGACY_FIELDS: Final = (
    "anchor_contracts",
    "artifact_family_rows",
    "artifact_identity_reference_rows",
    "artifact_nested_schema_rows",
    "artifact_type",
    "constructor_contract",
    "contract_parser_error_ids",
    "digest_computation_id",
    "encoding_id",
    "executed_layer_error_ids",
    "field_value_json_kind_ids",
    "field_value_schema_rows",
    "fixed_counts",
    "format_version",
    "identifier_syntax",
    "implementation_status_id",
    "nonclaim_state",
    "operator_contract",
    "program_contract",
    "resolution_contract",
    "resource_limits",
    "selector_contract",
    "type_contract",
    "validation_scope_id",
)

_OLD_INTERVAL_TYPE_RULE: Final = (
    "prior-u64-endpoint-one-nominal-clock-run-binding-v1"
)
_NEW_INTERVAL_TYPE_RULE: Final = (
    "prior-nominal-u64-endpoint-and-closed-start-not-after-end-v1"
)
_OLD_INTERVAL_TRUTH_RULE: Final = (
    "one-nominal-u64-interval-sequence-every-start-less-or-equal-end-by-type-"
    "validation-and-program-mode-adjacency-logical-truth-v1"
)
_NEW_INTERVAL_TRUTH_RULE: Final = (
    "closed-nominal-u64-intervals-and-program-mode-adjacency-v1"
)
_OLD_STATUS_SOURCE_RULE: Final = (
    "second-approved-outcome-sequence-value-source-program-literal-and-"
    "canonical-unique-nonempty-at-program-validation-v1"
)
_OLD_STATUS_TRUTH_RULE: Final = (
    "full-outcome-tuple-and-unique-nonempty-sequence-v1"
)
_LEGACY_INPUT_STATE_ROLE_ROWS: Final = (
    ("AVAILABLE", "", ""),
    (
        "REQUIRED_RUNTIME_SOURCE_UNAVAILABLE",
        "SOURCE_UNAVAILABLE",
        "RUNTIME_SOURCE_UNAVAILABLE",
    ),
    ("PARSER_FAILED", "PARSER_REJECTED", "PARSER_REJECTED"),
    (
        "DERIVATION_FAILED",
        "DERIVATION_MISMATCH",
        "DERIVATION_MISMATCH",
    ),
    (
        "UPSTREAM_PREDICATE_FAILED",
        "PREDICATE_FAILED",
        "UPSTREAM_RULE_FAILED",
    ),
    (
        "EXTERNAL_AUTHORITY_UNAVAILABLE",
        "AUTHORITY_UNAVAILABLE",
        "EXTERNAL_AUTHORITY_UNAVAILABLE",
    ),
    (
        "STATIC_MAPPING_UNRESOLVED",
        "PREDICATE_NOT_EVALUATED",
        "STATIC_MAPPING_UNRESOLVED",
    ),
)


class PortablePredicateLanguageCompositionVerificationCode(str, Enum):
    INPUT_TYPE = "INPUT_TYPE"
    INPUT_RESOURCE = "INPUT_RESOURCE"
    JSON_INVALID = "JSON_INVALID"
    CORE_INVALID = "CORE_INVALID"
    PROFILE_INVALID = "PROFILE_INVALID"
    CANONICAL_MISMATCH = "CANONICAL_MISMATCH"
    ARTIFACT_PIN_MISMATCH = "ARTIFACT_PIN_MISMATCH"
    PREDECESSOR_SCHEMA_INVALID = "PREDECESSOR_SCHEMA_INVALID"
    PROJECTION_MISMATCH = "PROJECTION_MISMATCH"
    RESULT_INVALID = "RESULT_INVALID"
    CONTRACT_DRIFT = "CONTRACT_DRIFT"


_MESSAGES: Final = {
    code: f"Portable predicate composition verifier rejected {code.value}"
    for code in PortablePredicateLanguageCompositionVerificationCode
}


class PortablePredicateLanguageCompositionVerificationError(ValueError):
    def __init__(
        self,
        code: PortablePredicateLanguageCompositionVerificationCode,
    ):
        self.code = code.value
        super().__init__(_MESSAGES[code])


class _DuplicateKeyError(ValueError):
    pass


def _fail(code: PortablePredicateLanguageCompositionVerificationCode) -> None:
    raise PortablePredicateLanguageCompositionVerificationError(code)


def _domain_sha256(domain: str, payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _canonical_json(value: object) -> bytes:
    try:
        raw = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _fail(PortablePredicateLanguageCompositionVerificationCode.RESULT_INVALID)
    if len(raw) > _MAXIMUM_ARTIFACT_BYTES:
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.INPUT_RESOURCE
        )
    return raw


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _reject_number(_: str) -> None:
    raise ValueError


def _bounded_integer(value: str) -> int:
    if len(value.lstrip("-")) > _MAXIMUM_JSON_INTEGER_DIGITS:
        raise ValueError
    return int(value)


def _node_count(value: object) -> int:
    count = 0
    stack = [value]
    while stack:
        item = stack.pop()
        count += 1
        if count > _MAXIMUM_JSON_ITEMS:
            return count
        if type(item) is dict:
            stack.extend(item.values())
        elif type(item) is list:
            stack.extend(item)
    return count


def _json_depth(value: object) -> int:
    maximum = 0
    stack = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        maximum = max(maximum, depth)
        if maximum > _MAXIMUM_JSON_DEPTH:
            return maximum
        if type(item) is dict:
            stack.extend((child, depth + 1) for child in item.values())
        elif type(item) is list:
            stack.extend((child, depth + 1) for child in item)
    return maximum


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


def _strict_json(
    value: bytes,
    invalid_code: PortablePredicateLanguageCompositionVerificationCode,
) -> dict:
    if type(value) is not bytes:
        _fail(PortablePredicateLanguageCompositionVerificationCode.INPUT_TYPE)
    if not value or len(value) > _MAXIMUM_ARTIFACT_BYTES:
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.INPUT_RESOURCE
        )
    try:
        tree = json.loads(
            value.decode("ascii", "strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_number,
            parse_float=_reject_number,
            parse_int=_bounded_integer,
        )
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _fail(PortablePredicateLanguageCompositionVerificationCode.JSON_INVALID)
    if (
        type(tree) is not dict
        or _json_depth(tree) > _MAXIMUM_JSON_DEPTH
        or _node_count(tree) > _MAXIMUM_JSON_ITEMS
    ):
        _fail(invalid_code)
    if value != _canonical_json(tree):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .CANONICAL_MISMATCH
        )
    return tree


def portable_predicate_language_composition_verifier_contract_tree() -> dict:
    return {
        "artifact_type": _CONTRACT_ARTIFACT_TYPE,
        "caller_supplied_profile_selection_pin_required": True,
        "caller_supplied_predecessor_kat_required": True,
        "core_projection_component_ids": list(_CORE_COMPONENT_IDS),
        "digest_computation_id": _DIGEST_COMPUTATION_ID,
        "encoding_id": _ENCODING_ID,
        "fixed_counts": {
            "core_projection_component_count": len(_CORE_COMPONENT_IDS),
            "profile_projection_component_count": len(_PROFILE_COMPONENT_IDS),
            "specialization_mapping_count": 2,
        },
        "format_version": "1",
        "generic_composition_rule_id": (
            "parse-exact-core-validate-closed-profile-derive-registries-and-"
            "merge-all-false-nonclaims-without-profile-id-branches-v1"
        ),
        "layer_metadata_artifact_type_disjointness_rule_id": (
            "composition-descriptor-and-projection-types-disjoint-from-"
            "selected-profile-metadata-anchors-and-runtime-domains-v1"
        ),
        "implementation_status_id": _IMPLEMENTATION_STATUS,
        "linux_receipt_pin_rule_id": (
            "caller-supplied-pins-must-exactly-match-frozen-core-linux-"
            "profile-and-predecessor-v1"
        ),
        "nonclaim_state": {
            "behavioral_equivalence_established": False,
            "empirical_result_established": False,
            "legacy_bytes_reconstructed": False,
            "portable_typed_formula_evaluated": False,
            "runtime_evaluator_implemented": False,
            "runtime_program_parser_implemented": False,
        },
        "predecessor_bytes_supplied_by_caller": True,
        "profile_selection_pin_rule_id": (
            "caller-supplied-profile-artifact-type-and-domain-sha256-match-"
            "before-and-after-profile-parse-v1"
        ),
        "profile_field_inventory_commitment_rule_id": (
            "derive-count-and-preserve-validated-profile-field-order-v1"
        ),
        "profile_relation_inventory_commitment_rule_id": (
            "derive-count-and-preserve-purpose-and-relation-order-v1"
        ),
        "profile_projection_component_ids": list(_PROFILE_COMPONENT_IDS),
        "specialization_mapping_rows": [
            {
                "core_primitive_id": "interval-order",
                "core_rule_id": _NEW_INTERVAL_TRUTH_RULE,
                "legacy_exposed_id": "interval-order",
                "legacy_rule_id": _OLD_INTERVAL_TRUTH_RULE,
                "mapping_scope_id": (
                    "static-registry-correspondence-not-behavioral-proof"
                ),
            },
            {
                "core_primitive_id": "member-of-frozen-program-set",
                "core_rule_id": (
                    "one-value-and-unique-nonempty-sequence-of-identical-item-"
                    "type-exact-membership-v1"
                ),
                "legacy_exposed_id": "status-is-approved",
                "legacy_rule_id": _OLD_STATUS_TRUTH_RULE,
                "mapping_scope_id": (
                    "static-registry-correspondence-not-behavioral-proof"
                ),
            },
        ],
        "validation_scope_id": _VALIDATION_SCOPE,
    }


def portable_predicate_language_composition_verifier_contract_bytes() -> bytes:
    return _canonical_json(
        portable_predicate_language_composition_verifier_contract_tree()
    )


def portable_predicate_language_composition_verifier_contract_plain_sha256(
) -> str:
    return hashlib.sha256(
        portable_predicate_language_composition_verifier_contract_bytes()
    ).hexdigest()


def portable_predicate_language_composition_verifier_contract_sha256() -> str:
    return _domain_sha256(
        _CONTRACT_ARTIFACT_TYPE,
        portable_predicate_language_composition_verifier_contract_bytes(),
    )


def parse_portable_predicate_language_composition_verifier_contract(
    value: bytes,
) -> dict:
    tree = _strict_json(
        value,
        PortablePredicateLanguageCompositionVerificationCode.CORE_INVALID,
    )
    expected = portable_predicate_language_composition_verifier_contract_tree()
    if not _same_exact(tree, expected):
        _fail(PortablePredicateLanguageCompositionVerificationCode.CORE_INVALID)
    return expected


def _parse_core(value: bytes) -> dict:
    try:
        return parse_portable_predicate_language_core_verifier_contract(value)
    except PortablePredicateLanguageCoreVerificationError:
        _fail(PortablePredicateLanguageCompositionVerificationCode.CORE_INVALID)


def _parse_profile(value: bytes) -> dict:
    tree = _strict_json(
        value,
        PortablePredicateLanguageCompositionVerificationCode.PROFILE_INVALID,
    )
    try:
        validated = validate_portable_predicate_profile_verifier_tree(tree)
    except PortablePredicateLanguageCoreVerificationError:
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.PROFILE_INVALID
        )
    return validated


def _validate_profile_selection_pin(
    profile_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> None:
    if (
        type(profile_bytes) is not bytes
        or type(expected_profile_artifact_type) is not str
        or type(expected_profile_contract_sha256) is not str
    ):
        _fail(PortablePredicateLanguageCompositionVerificationCode.INPUT_TYPE)
    if (
        not profile_bytes
        or len(profile_bytes) > _MAXIMUM_ARTIFACT_BYTES
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.INPUT_RESOURCE
        )
    if (
        len(expected_profile_artifact_type)
        > _MAXIMUM_PROFILE_ARTIFACT_TYPE_BYTES
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.INPUT_RESOURCE
        )
    if (
        not expected_profile_artifact_type
        or not expected_profile_artifact_type.isascii()
        or _IDENTIFIER_RE.fullmatch(expected_profile_artifact_type) is None
        or _SHA256_RE.fullmatch(expected_profile_contract_sha256) is None
        or _domain_sha256(
            expected_profile_artifact_type,
            profile_bytes,
        )
        != expected_profile_contract_sha256
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .ARTIFACT_PIN_MISMATCH
        )


def _validate_parsed_profile_selection(
    profile: dict,
    profile_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> None:
    if (
        profile.get("artifact_type") != expected_profile_artifact_type
        or _domain_sha256(
            profile["artifact_type"],
            profile_bytes,
        )
        != expected_profile_contract_sha256
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .ARTIFACT_PIN_MISMATCH
        )


def _ids(rows: list, field: str) -> list:
    return [row[field] for row in rows]


def _validate_layer_metadata_artifact_type_disjointness(
    profile: dict,
    *,
    additional_metadata_artifact_types: tuple = (),
) -> None:
    profile_surface_types = {
        profile["artifact_type"],
        profile["profile_verification_result_artifact_type"],
        *[
            row["artifact_type_id"]
            for row in profile["anchor_contract_rows"]
        ],
        *[
            row["artifact_type_id"]
            for row in profile["artifact_domain_rows"]
        ],
    }
    layer_metadata_types = {
        _CONTRACT_ARTIFACT_TYPE,
        _DESCRIPTOR_ARTIFACT_TYPE,
        _RESULT_ARTIFACT_TYPE,
        *additional_metadata_artifact_types,
    }
    if (
        len(layer_metadata_types) != 3 + len(
            additional_metadata_artifact_types
        )
        or profile_surface_types.intersection(layer_metadata_types)
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROFILE_INVALID
        )


def portable_predicate_language_composed_descriptor_verifier_tree(
    core_bytes: bytes,
    profile_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> dict:
    _validate_profile_selection_pin(
        profile_bytes,
        expected_profile_artifact_type=expected_profile_artifact_type,
        expected_profile_contract_sha256=expected_profile_contract_sha256,
    )
    core = _parse_core(core_bytes)
    profile = _parse_profile(profile_bytes)
    _validate_parsed_profile_selection(
        profile,
        profile_bytes,
        expected_profile_artifact_type=expected_profile_artifact_type,
        expected_profile_contract_sha256=expected_profile_contract_sha256,
    )
    _validate_layer_metadata_artifact_type_disjointness(profile)
    if (
        profile["core_contract_sha256"]
        != _domain_sha256(_CORE_ARTIFACT_TYPE, core_bytes)
        or profile["core_profile_interface_sha256"]
        != portable_predicate_language_core_verifier_profile_interface_sha256()
        or profile["profile_interface_id"]
        != core["profile_interface"]["profile_interface_id"]
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.PROFILE_INVALID
        )
    claims = dict(core["nonclaim_state"])
    if set(claims).intersection(profile["nonclaim_state"]):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.PROFILE_INVALID
        )
    claims.update(profile["nonclaim_state"])
    if any(type(value) is not bool or value for value in claims.values()):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.PROFILE_INVALID
        )
    return {
        "artifact_type": _DESCRIPTOR_ARTIFACT_TYPE,
        "authority_class_ids": list(profile["authority_class_ids"]),
        "constructor_ids": _ids(
            core["constructor_contract"]["constructor_rows"],
            "constructor_id",
        ),
        "core_contract_sha256": profile["core_contract_sha256"],
        "core_profile_interface_sha256": profile[
            "core_profile_interface_sha256"
        ],
        "fixed_counts": {
            "artifact_domain_count": profile["fixed_counts"][
                "artifact_domain_count"
            ],
            "authority_class_count": profile["fixed_counts"][
                "authority_class_count"
            ],
            "constructor_count": core["fixed_counts"]["constructor_count"],
            "interval_refinement_count": profile["fixed_counts"][
                "interval_refinement_count"
            ],
            "locator_extension_count": profile["fixed_counts"][
                "locator_extension_count"
            ],
            "operator_count": core["fixed_counts"]["operator_count"],
            "operator_specialization_count": profile["fixed_counts"][
                "operator_specialization_count"
            ],
            "program_purpose_count": profile["fixed_counts"][
                "program_purpose_count"
            ],
            "profile_field_schema_count": len(
                profile["profile_field_schema_rows"]
            ),
            "program_purpose_relation_count": profile["fixed_counts"][
                "program_purpose_relation_count"
            ],
            "public_error_count": profile["fixed_counts"][
                "public_error_count"
            ],
            "type_kind_count": core["fixed_counts"]["type_kind_count"],
        },
        "format_version": "1",
        "interval_refinement_ids": _ids(
            profile["interval_refinement_rows"],
            "exposed_refinement_id",
        ),
        "locator_kind_ids": _ids(
            profile["locator_extension_rows"],
            "locator_kind_id",
        ),
        "nonclaim_state": claims,
        "operator_ids": _ids(
            core["operator_contract"]["operator_rows"],
            "operator_id",
        ),
        "operator_specialization_ids": _ids(
            profile["operator_specialization_rows"],
            "exposed_operator_id",
        ),
        "profile_class_id": profile["profile_class_id"],
        "profile_artifact_type": profile["artifact_type"],
        "profile_contract_sha256": expected_profile_contract_sha256,
        "profile_field_ids": _ids(
            profile["profile_field_schema_rows"],
            "field_id",
        ),
        "profile_verification_result_artifact_type": profile[
            "profile_verification_result_artifact_type"
        ],
        "profile_id": profile["profile_id"],
        "profile_interface_id": profile["profile_interface_id"],
        "program_purpose_ids": _ids(
            profile["program_purpose_rows"],
            "program_purpose_id",
        ),
        "program_purpose_relation_ids": [
            relation["relation_id"]
            for purpose in profile["program_purpose_rows"]
            for relation in purpose["purpose_relation_rows"]
        ],
        "public_error_ids": list(profile["public_error_ids"]),
        "type_kind_ids": _ids(
            core["type_contract"]["type_kind_schema_rows"],
            "type_kind_id",
        ),
    }


def portable_predicate_language_composed_descriptor_verifier_bytes(
    core_bytes: bytes,
    profile_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> bytes:
    return _canonical_json(
        portable_predicate_language_composed_descriptor_verifier_tree(
            core_bytes,
            profile_bytes,
            expected_profile_artifact_type=(
                expected_profile_artifact_type
            ),
            expected_profile_contract_sha256=(
                expected_profile_contract_sha256
            ),
        )
    )


def portable_predicate_language_composed_descriptor_verifier_sha256(
    core_bytes: bytes,
    profile_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> str:
    return _domain_sha256(
        _DESCRIPTOR_ARTIFACT_TYPE,
        portable_predicate_language_composed_descriptor_verifier_bytes(
            core_bytes,
            profile_bytes,
            expected_profile_artifact_type=(
                expected_profile_artifact_type
            ),
            expected_profile_contract_sha256=(
                expected_profile_contract_sha256
            ),
        ),
    )


@dataclass(frozen=True)
class PortablePredicateLanguageCompositionVerificationPinsV1:
    core_contract_byte_count: int
    core_contract_plain_sha256: str
    core_contract_sha256: str
    profile_contract_byte_count: int
    profile_contract_plain_sha256: str
    profile_contract_sha256: str
    predecessor_contract_artifact_type: str
    predecessor_contract_byte_count: int
    predecessor_contract_plain_sha256: str
    predecessor_contract_sha256: str


@dataclass(frozen=True)
class PortablePredicateLanguageCompositionVerificationResultV1:
    """Independent receipt.

    ``compositor_id`` intentionally names this verifier implementation, so it
    differs from the source-lane receipt while every substantive field agrees.
    """

    artifact_type: str
    format_version: str
    compositor_id: str
    implementation_status_id: str
    projection_status_id: str
    composition_contract_sha256: str
    core_contract_byte_count: int
    core_contract_plain_sha256: str
    core_contract_sha256: str
    profile_contract_byte_count: int
    profile_contract_plain_sha256: str
    profile_contract_sha256: str
    predecessor_contract_artifact_type: str
    predecessor_contract_byte_count: int
    predecessor_contract_plain_sha256: str
    predecessor_contract_sha256: str
    composed_descriptor_sha256: str
    core_projection_component_count: int
    profile_projection_component_count: int
    canonical_inputs_validated: bool
    caller_supplied_exact_kats_validated: bool
    closed_profile_interface_validated: bool
    core_projection_correspondence_validated: bool
    profile_projection_correspondence_validated: bool
    behavioral_equivalence_established: bool
    empirical_result_established: bool
    legacy_bytes_reconstructed: bool
    portable_typed_formula_evaluated: bool
    runtime_evaluator_implemented: bool
    runtime_program_parser_implemented: bool


def _valid_digest(value: object) -> bool:
    return type(value) is str and _SHA256_RE.fullmatch(value) is not None


def _validated_pins(
    value: PortablePredicateLanguageCompositionVerificationPinsV1,
) -> PortablePredicateLanguageCompositionVerificationPinsV1:
    if type(value) is not PortablePredicateLanguageCompositionVerificationPinsV1:
        _fail(PortablePredicateLanguageCompositionVerificationCode.INPUT_TYPE)
    if (
        type(value.core_contract_byte_count) is not int
        or type(value.profile_contract_byte_count) is not int
        or type(value.predecessor_contract_byte_count) is not int
        or value.core_contract_byte_count != _V1_CORE_BYTE_COUNT
        or value.core_contract_plain_sha256 != _V1_CORE_PLAIN_SHA256
        or value.core_contract_sha256 != _V1_CORE_SHA256
        or value.profile_contract_byte_count != _V1_PROFILE_BYTE_COUNT
        or value.profile_contract_plain_sha256 != _V1_PROFILE_PLAIN_SHA256
        or value.profile_contract_sha256 != _V1_PROFILE_SHA256
        or value.predecessor_contract_artifact_type
        != _PREDECESSOR_ARTIFACT_TYPE
        or value.predecessor_contract_byte_count
        != _V1_PREDECESSOR_BYTE_COUNT
        or value.predecessor_contract_plain_sha256
        != _V1_PREDECESSOR_PLAIN_SHA256
        or value.predecessor_contract_sha256 != _V1_PREDECESSOR_SHA256
        or any(
            not _valid_digest(digest)
            for digest in (
                value.core_contract_plain_sha256,
                value.core_contract_sha256,
                value.profile_contract_plain_sha256,
                value.profile_contract_sha256,
                value.predecessor_contract_plain_sha256,
                value.predecessor_contract_sha256,
            )
        )
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .ARTIFACT_PIN_MISMATCH
        )
    return value


def _check_pin(
    raw: bytes,
    artifact_type: str,
    count: int,
    plain: str,
    domain: str,
) -> None:
    if (
        len(raw) != count
        or hashlib.sha256(raw).hexdigest() != plain
        or _domain_sha256(artifact_type, raw) != domain
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .ARTIFACT_PIN_MISMATCH
        )


def _legacy_tree(value: bytes) -> dict:
    tree = _strict_json(
        value,
        PortablePredicateLanguageCompositionVerificationCode
        .PREDECESSOR_SCHEMA_INVALID,
    )
    if (
        set(tree) != set(_LEGACY_FIELDS)
        or tree.get("artifact_type") != _PREDECESSOR_ARTIFACT_TYPE
        or tree.get("format_version") != "1"
        or type(tree.get("nonclaim_state")) is not dict
        or any(
            type(item) is not bool or item
            for item in tree["nonclaim_state"].values()
        )
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PREDECESSOR_SCHEMA_INVALID
        )
    return tree


def _without(row: dict, fields: set) -> dict:
    return {key: value for key, value in row.items() if key not in fields}


def _normalized_type_rows(legacy: dict, profile: dict) -> list:
    rows = deepcopy(legacy["type_contract"]["type_kind_schema_rows"])
    interval = next(
        (
            row
            for row in rows
            if row.get("type_kind_id") == "u64-interval-sequence"
        ),
        None,
    )
    refinements = profile["interval_refinement_rows"]
    if (
        type(interval) is not dict
        or len(refinements) != 1
        or interval.get("validation_rule_id") != _OLD_INTERVAL_TYPE_RULE
        or refinements[0].get("validation_rule_id")
        != _OLD_INTERVAL_TYPE_RULE
        or refinements[0].get("refinement_primitive_id")
        != "nominal-u64-endpoint-binding"
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )
    interval["validation_rule_id"] = _NEW_INTERVAL_TYPE_RULE
    return rows


def _normalized_constructors(legacy: dict) -> list:
    rows = deepcopy(legacy["constructor_contract"]["constructor_rows"])
    for row in rows:
        if (
            type(row) is not dict
            or "native_or_external_parsing_admitted" not in row
            or "external_parsing_admitted" in row
        ):
            _fail(
                PortablePredicateLanguageCompositionVerificationCode
                .PROJECTION_MISMATCH
            )
        row["external_parsing_admitted"] = row.pop(
            "native_or_external_parsing_admitted"
        )
    return rows


def _normalized_constructor_failures(legacy: dict) -> list:
    rows = deepcopy(
        legacy["constructor_contract"]["constructor_failure_mapping_rows"]
    )
    for row in rows:
        if (
            type(row) is not dict
            or set(row)
            != {"failure_rule_id", "internal_condition_id"}
        ):
            _fail(
                PortablePredicateLanguageCompositionVerificationCode
                .PROJECTION_MISMATCH
            )
        row["public_error_role_id"] = "LOCAL_RULE_FAILED"
    return _sorted_rows(rows, "failure_rule_id")


def _normalized_fault_precedence_rows(legacy: dict) -> list:
    rows = deepcopy(legacy["operator_contract"]["fault_precedence_rows"])
    for row in rows:
        if (
            type(row) is not dict
            or set(row) != {"selected_disposition_id", "precedence_rank"}
        ):
            _fail(
                PortablePredicateLanguageCompositionVerificationCode
                .PROJECTION_MISMATCH
            )
        row["disposition_rank"] = row.pop("precedence_rank")
    return rows


def _normalized_operators(
    legacy: dict,
    core: dict,
    profile: dict,
) -> list:
    old_rows = legacy["operator_contract"]["operator_rows"]
    new_rows = core["operator_contract"]["operator_rows"]
    specializations = profile["operator_specialization_rows"]
    if (
        type(old_rows) is not list
        or len(old_rows) != len(new_rows)
        or len(specializations) != 1
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )
    specialization = specializations[0]
    result = []
    for old, new in zip(old_rows, new_rows):
        if old.get("operator_id") == "status-is-approved":
            varying = {
                "operator_id",
                "operand_source_rule_id",
                "type_and_truth_rule_id",
            }
            valid = (
                specialization.get("exposed_operator_id")
                == old.get("operator_id")
                and specialization.get("primitive_id")
                == new.get("operator_id")
                and specialization.get("operand_source_rule_id")
                == new.get("operand_source_rule_id")
                and specialization.get("type_and_truth_rule_id")
                == new.get("type_and_truth_rule_id")
                and old.get("operand_source_rule_id")
                == _OLD_STATUS_SOURCE_RULE
                and old.get("type_and_truth_rule_id")
                == _OLD_STATUS_TRUTH_RULE
                and _same_exact(
                    _without(old, varying),
                    _without(new, varying),
                )
            )
            if not valid:
                _fail(
                    PortablePredicateLanguageCompositionVerificationCode
                    .PROJECTION_MISMATCH
                )
            result.append(deepcopy(new))
        elif old.get("operator_id") == "interval-order":
            if (
                new.get("operator_id") != "interval-order"
                or old.get("type_and_truth_rule_id")
                != _OLD_INTERVAL_TRUTH_RULE
                or new.get("type_and_truth_rule_id")
                != _NEW_INTERVAL_TRUTH_RULE
                or not _same_exact(
                    _without(old, {"type_and_truth_rule_id"}),
                    _without(new, {"type_and_truth_rule_id"}),
                )
            ):
                _fail(
                    PortablePredicateLanguageCompositionVerificationCode
                    .PROJECTION_MISMATCH
                )
            result.append(deepcopy(new))
        else:
            result.append(deepcopy(old))
    return result


def _normalized_input_states(legacy: dict, profile: dict) -> list:
    error_by_role = {
        row["public_error_role_id"]: row["public_error_id"]
        for row in profile["public_error_role_rows"]
    }
    expected_by_state = {
        state_id: (error_id, role_id)
        for state_id, error_id, role_id in _LEGACY_INPUT_STATE_ROLE_ROWS
    }
    rows = deepcopy(legacy["resolution_contract"]["input_state_rows"])
    if (
        len(rows) != len(expected_by_state)
        or len(error_by_role) != len(profile["public_error_role_rows"])
        or error_by_role.get("LOCAL_RULE_FAILED") != "PREDICATE_FAILED"
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )
    seen_state_ids = set()
    for row in rows:
        if (
            type(row) is not dict
            or row.get("internal_condition_id") != ""
            or "executed_error_id" not in row
            or row.get("input_state_id") not in expected_by_state
            or row.get("input_state_id") in seen_state_ids
        ):
            _fail(
                PortablePredicateLanguageCompositionVerificationCode
                .PROJECTION_MISMATCH
            )
        state_id = row["input_state_id"]
        seen_state_ids.add(state_id)
        expected_error_id, expected_role_id = expected_by_state[state_id]
        error = row.pop("executed_error_id")
        row.pop("internal_condition_id")
        if (
            error != expected_error_id
            or (
                expected_role_id
                and error_by_role.get(expected_role_id) != error
            )
        ):
            _fail(
                PortablePredicateLanguageCompositionVerificationCode
                .PROJECTION_MISMATCH
            )
        row["public_error_role_id"] = expected_role_id
    if seen_state_ids != set(expected_by_state):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )
    return rows


def _sorted_rows(rows: object, field: str) -> list:
    if type(rows) is not list or any(type(row) is not dict for row in rows):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )
    try:
        return sorted(deepcopy(rows), key=lambda row: row[field])
    except (KeyError, TypeError):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )


def _verify_core_projection(
    legacy: dict,
    core: dict,
    profile: dict,
) -> None:
    comparisons = (
        (
            legacy["field_value_json_kind_ids"],
            core["field_value_json_kind_ids"],
        ),
        (
            legacy["contract_parser_error_ids"],
            core["contract_parser_error_ids"],
        ),
        (legacy["resource_limits"], core["resource_limits"]),
        (
            _normalized_type_rows(legacy, profile),
            core["type_contract"]["type_kind_schema_rows"],
        ),
        (
            legacy["type_contract"]["value_encoding_rows"],
            core["type_contract"]["value_encoding_rows"],
        ),
        (
            _normalized_constructors(legacy),
            core["constructor_contract"]["constructor_rows"],
        ),
        (
            _normalized_constructor_failures(legacy),
            _sorted_rows(
                core["constructor_contract"][
                    "constructor_failure_mapping_rows"
                ],
                "failure_rule_id",
            ),
        ),
        (
            legacy["constructor_contract"][
                "constructor_failure_precedence_rows"
            ],
            core["constructor_contract"][
                "constructor_failure_precedence_rows"
            ],
        ),
        (
            _normalized_operators(legacy, core, profile),
            core["operator_contract"]["operator_rows"],
        ),
        (
            legacy["resolution_contract"]["resolution_requirement_rows"],
            core["resolution_contract"]["resolution_requirement_rows"],
        ),
        (
            _normalized_input_states(legacy, profile),
            core["resolution_contract"]["input_state_rows"],
        ),
        (
            legacy["selector_contract"]["path_segment_schema_rows"],
            core["selector_contract"]["path_segment_schema_rows"],
        ),
        (
            _normalized_fault_precedence_rows(legacy),
            core["operator_contract"]["fault_precedence_rows"],
        ),
    )
    if len(comparisons) != len(_CORE_COMPONENT_IDS) or any(
        not _same_exact(left, right) for left, right in comparisons
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )


def _verify_profile_projection(
    legacy: dict,
    core: dict,
    profile: dict,
) -> None:
    anchors = profile["anchor_contract_rows"]
    if (
        len(anchors) != 1
        or anchors[0].get("anchor_role_id") != "linux-native-mapping-gap"
        or anchors[0].get("contract_sha256")
        != legacy["anchor_contracts"].get(
            "native_mapping_gap_contract_sha256"
        )
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )

    parameters = {
        row["parameter_slot_id"]: row["parameter_value_id"]
        for row in profile["profile_parameter_rows"]
    }
    purpose = next(
        (
            row
            for row in legacy["program_contract"]["program_purpose_rows"]
            if row.get("program_purpose_id")
            == parameters.get("primary-program-purpose-id")
        ),
        None,
    )
    if type(purpose) is not dict:
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )
    families = {
        row["artifact_type_id"]: row
        for row in legacy["artifact_family_rows"]
    }
    bindings = {
        row["fixed_artifact_type_id"]: row
        for row in purpose["binding_identity_rule_rows"]
    }
    for row in profile["artifact_domain_rows"]:
        artifact_type = row["artifact_type_id"]
        if artifact_type in families:
            old = families[artifact_type]
            valid = (
                row["digest_domain_id"] == old["digest_domain_id"]
                and row["identity_semantics_id"]
                == old["artifact_identity_semantics_id"]
            )
        elif artifact_type in bindings:
            old = bindings[artifact_type]
            valid = (
                row["digest_domain_id"] == artifact_type
                and row["identity_semantics_id"]
                == old["required_identity_semantics_id"]
            )
        else:
            valid = False
        if not valid:
            _fail(
                PortablePredicateLanguageCompositionVerificationCode
                .PROJECTION_MISMATCH
            )

    components = legacy["operator_contract"]["source_operation_outcome_v1"][
        "ordered_component_rows"
    ]
    if (
        not _same_exact(
            profile["authority_class_ids"],
            legacy["resolution_contract"]["authority_class_ids"],
        )
        or not _same_exact(
            profile["public_error_ids"],
            legacy["executed_layer_error_ids"],
        )
        or [
            parameters.get(f"outcome-component-{index}-domain-id")
            for index in range(4)
        ]
        != [row.get("token_domain_id") for row in components]
        or parameters.get("interval-endpoint-unit-id")
        != "linux-clock-run-binding"
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )
    _normalized_input_states(legacy, profile)

    legacy_field_value_schemas = {}
    for legacy_schema in legacy["field_value_schema_rows"]:
        legacy_field_ids = legacy_schema.get("field_ids")
        legacy_value_schema_id = legacy_schema.get("value_schema_id")
        if (
            type(legacy_field_ids) is not list
            or type(legacy_value_schema_id) is not str
            or any(type(field_id) is not str for field_id in legacy_field_ids)
            or any(
                field_id in legacy_field_value_schemas
                for field_id in legacy_field_ids
            )
        ):
            _fail(
                PortablePredicateLanguageCompositionVerificationCode
                .PROJECTION_MISMATCH
            )
        for legacy_field_id in legacy_field_ids:
            legacy_field_value_schemas[
                legacy_field_id
            ] = legacy_value_schema_id
    if any(
        type(profile_schema) is not dict
        or legacy_field_value_schemas.get(profile_schema.get("field_id"))
        != profile_schema.get("value_schema_id")
        for profile_schema in profile["profile_field_schema_rows"]
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )

    locator_rows = [
        row
        for row in legacy["selector_contract"][
            "executable_locator_schema_rows"
        ]
        if row.get("program_purpose_admission_ids")
        == [purpose["program_purpose_id"]]
    ]
    if not _same_exact(
        [
            row["locator_kind_id"]
            for row in profile["locator_extension_rows"]
        ],
        [row.get("locator_kind_id") for row in locator_rows],
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )
    locators = {row["locator_kind_id"]: row for row in locator_rows}
    for row in profile["locator_extension_rows"]:
        old = locators.get(row["locator_kind_id"])
        old_path_rule = (
            old.get("ordered_path_segment_count_rule_id")
            if type(old) is dict
            else None
        )
        if old_path_rule == "zero-v1":
            expected_primitive_id = "direct-bound-value"
            expected_placeholder_field_ids = ["ordered_path_segments"]
        elif old_path_rule == "one-to-sixteen-v1":
            expected_primitive_id = "bounded-artifact-path"
            expected_placeholder_field_ids = []
        else:
            expected_primitive_id = None
            expected_placeholder_field_ids = None
        if (
            type(old) is not dict
            or not _same_exact(
                row["exact_configuration_field_ids"],
                old["exact_field_ids"],
            )
            or row["locator_primitive_id"] != expected_primitive_id
            or not _same_exact(
                row["exact_empty_placeholder_field_ids"],
                expected_placeholder_field_ids,
            )
            or row["validation_rule_id"]
            != old["resolver_binding_rule_id"]
        ):
            _fail(
                PortablePredicateLanguageCompositionVerificationCode
                .PROJECTION_MISMATCH
            )

    purposes = profile["program_purpose_rows"]
    if (
        len(purposes) != 1
        or purposes[0]["program_purpose_id"]
        != purpose["program_purpose_id"]
        or not _same_exact(
            purposes[0]["exact_binding_field_ids"],
            purpose["exact_binding_field_ids"],
        )
        or purposes[0]["validation_rule_id"]
        != purpose["binding_validation_rule_id"]
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )
    expected_purpose_relations = [
        {
            "anchor_role_id": "linux-native-mapping-gap",
            "anchor_row_array_path_ids": ["predicate_rows"],
            "ordered_equality_rows": [
                {
                    "anchor_row_value_path_ids": ["observation_id"],
                    "purpose_binding_field_id": "observation_id",
                },
                {
                    "anchor_row_value_path_ids": ["predicate_id"],
                    "purpose_binding_field_id": "predicate_id",
                },
                {
                    "anchor_row_value_path_ids": ["ordered_mapping_ids"],
                    "purpose_binding_field_id": (
                        "ordered_required_mapping_ids"
                    ),
                },
            ],
            "relation_id": "linux-native-predicate-row-exact-match",
            "relation_primitive_id": (
                "exactly-one-pinned-anchor-row-canonical-equality-v1"
            ),
        },
        {
            "locator_value_field_id": "mapping_id",
            "purpose_binding_field_id": "ordered_required_mapping_ids",
            "relation_id": "linux-required-mapping-coverage",
            "relation_primitive_id": (
                "purpose-identifiers-exactly-covered-by-input-locators-v1"
            ),
        },
    ]
    program_type = next(
        row["artifact_type_id"]
        for row in profile["artifact_domain_rows"]
        if row["artifact_role_id"] == "predicate-program"
    )
    legacy_program_family = families.get(program_type)
    if (
        not _same_exact(
            purposes[0]["purpose_relation_rows"],
            expected_purpose_relations,
        )
        or type(legacy_program_family) is not dict
        or (
            "linux-purpose-every-required-mapping-id-is-referenced-by-at-"
            "least-one-input-resolved-locator-and-no-other-mapping-id-occurs-"
            "generic-purpose-vacuous-v1"
        )
        not in legacy_program_family["cross_field_validation_rule_ids"]
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )
    _normalized_operators(legacy, core, profile)
    _normalized_type_rows(legacy, profile)
    if any(
        type(value) is not bool
        or value
        or legacy["nonclaim_state"].get(claim_id) is not False
        for claim_id, value in profile["nonclaim_state"].items()
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode
            .PROJECTION_MISMATCH
        )


def verify_linux_confinement_predecessor_projection_independently(
    core_bytes: bytes,
    profile_bytes: bytes,
    predecessor_bytes: bytes,
    pins: PortablePredicateLanguageCompositionVerificationPinsV1,
) -> PortablePredicateLanguageCompositionVerificationResultV1:
    validated = _validated_pins(pins)
    if (
        type(core_bytes) is not bytes
        or type(profile_bytes) is not bytes
        or type(predecessor_bytes) is not bytes
    ):
        _fail(PortablePredicateLanguageCompositionVerificationCode.INPUT_TYPE)
    _check_pin(
        core_bytes,
        _CORE_ARTIFACT_TYPE,
        validated.core_contract_byte_count,
        validated.core_contract_plain_sha256,
        validated.core_contract_sha256,
    )
    core = _parse_core(core_bytes)
    _check_pin(
        profile_bytes,
        _LINUX_PROFILE_ARTIFACT_TYPE,
        validated.profile_contract_byte_count,
        validated.profile_contract_plain_sha256,
        validated.profile_contract_sha256,
    )
    profile = _parse_profile(profile_bytes)
    _validate_layer_metadata_artifact_type_disjointness(
        profile,
        additional_metadata_artifact_types=(
            _PREDECESSOR_ARTIFACT_TYPE,
        ),
    )
    _check_pin(
        predecessor_bytes,
        validated.predecessor_contract_artifact_type,
        validated.predecessor_contract_byte_count,
        validated.predecessor_contract_plain_sha256,
        validated.predecessor_contract_sha256,
    )
    descriptor = (
        portable_predicate_language_composed_descriptor_verifier_tree(
            core_bytes,
            profile_bytes,
            expected_profile_artifact_type=_LINUX_PROFILE_ARTIFACT_TYPE,
            expected_profile_contract_sha256=(
                validated.profile_contract_sha256
            ),
        )
    )
    if (
        descriptor["profile_id"] != "LINUX_CONFINEMENT_V1"
        or descriptor["core_contract_sha256"]
        != portable_predicate_language_core_verifier_contract_sha256()
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.PROFILE_INVALID
        )
    legacy = _legacy_tree(predecessor_bytes)
    _verify_core_projection(legacy, core, profile)
    _verify_profile_projection(legacy, core, profile)
    return PortablePredicateLanguageCompositionVerificationResultV1(
        artifact_type=_RESULT_ARTIFACT_TYPE,
        format_version="1",
        compositor_id=_VERIFIER_ID,
        implementation_status_id=_IMPLEMENTATION_STATUS,
        projection_status_id=_PROJECTION_STATUS,
        composition_contract_sha256=(
            portable_predicate_language_composition_verifier_contract_sha256()
        ),
        core_contract_byte_count=len(core_bytes),
        core_contract_plain_sha256=hashlib.sha256(core_bytes).hexdigest(),
        core_contract_sha256=_domain_sha256(
            _CORE_ARTIFACT_TYPE,
            core_bytes,
        ),
        profile_contract_byte_count=len(profile_bytes),
        profile_contract_plain_sha256=hashlib.sha256(
            profile_bytes
        ).hexdigest(),
        profile_contract_sha256=_domain_sha256(
            profile["artifact_type"],
            profile_bytes,
        ),
        predecessor_contract_artifact_type=legacy["artifact_type"],
        predecessor_contract_byte_count=len(predecessor_bytes),
        predecessor_contract_plain_sha256=hashlib.sha256(
            predecessor_bytes
        ).hexdigest(),
        predecessor_contract_sha256=_domain_sha256(
            legacy["artifact_type"],
            predecessor_bytes,
        ),
        composed_descriptor_sha256=(
            portable_predicate_language_composed_descriptor_verifier_sha256(
                core_bytes,
                profile_bytes,
                expected_profile_artifact_type=(
                    _LINUX_PROFILE_ARTIFACT_TYPE
                ),
                expected_profile_contract_sha256=(
                    validated.profile_contract_sha256
                ),
            )
        ),
        core_projection_component_count=len(_CORE_COMPONENT_IDS),
        profile_projection_component_count=len(_PROFILE_COMPONENT_IDS),
        canonical_inputs_validated=True,
        caller_supplied_exact_kats_validated=True,
        closed_profile_interface_validated=True,
        core_projection_correspondence_validated=True,
        profile_projection_correspondence_validated=True,
        behavioral_equivalence_established=False,
        empirical_result_established=False,
        legacy_bytes_reconstructed=False,
        portable_typed_formula_evaluated=False,
        runtime_evaluator_implemented=False,
        runtime_program_parser_implemented=False,
    )


def _verification_result_tree(
    value: PortablePredicateLanguageCompositionVerificationResultV1,
) -> dict:
    expected_types = {
        "bool": bool,
        "int": int,
        "str": str,
        bool: bool,
        int: int,
        str: str,
    }
    tree = {}
    for field_id, annotation in (
        PortablePredicateLanguageCompositionVerificationResultV1
        .__annotations__
        .items()
    ):
        expected_type = expected_types.get(annotation)
        field_value = getattr(value, field_id)
        if expected_type is None or type(field_value) is not expected_type:
            _fail(
                PortablePredicateLanguageCompositionVerificationCode
                .RESULT_INVALID
            )
        tree[field_id] = field_value
    return tree


def portable_predicate_language_composition_verification_result_bytes(
    value: PortablePredicateLanguageCompositionVerificationResultV1,
) -> bytes:
    if type(value) is not PortablePredicateLanguageCompositionVerificationResultV1:
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.RESULT_INVALID
        )
    return _canonical_json(_verification_result_tree(value))


def portable_predicate_language_composition_verification_result_sha256(
    value: PortablePredicateLanguageCompositionVerificationResultV1,
) -> str:
    return _domain_sha256(
        _RESULT_ARTIFACT_TYPE,
        portable_predicate_language_composition_verification_result_bytes(
            value
        ),
    )


def validate_portable_predicate_language_composition_verification_result(
    value: PortablePredicateLanguageCompositionVerificationResultV1,
    core_bytes: bytes,
    profile_bytes: bytes,
    predecessor_bytes: bytes,
    pins: PortablePredicateLanguageCompositionVerificationPinsV1,
) -> PortablePredicateLanguageCompositionVerificationResultV1:
    if type(value) is not PortablePredicateLanguageCompositionVerificationResultV1:
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.RESULT_INVALID
        )
    expected = verify_linux_confinement_predecessor_projection_independently(
        core_bytes,
        profile_bytes,
        predecessor_bytes,
        pins,
    )
    if not _same_exact(
        _verification_result_tree(value),
        _verification_result_tree(expected),
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.RESULT_INVALID
        )
    return value


def _validate_reconstruction() -> None:
    if len(
        {
            _CORE_ARTIFACT_TYPE,
            _CONTRACT_ARTIFACT_TYPE,
            _DESCRIPTOR_ARTIFACT_TYPE,
            _RESULT_ARTIFACT_TYPE,
            _PREDECESSOR_ARTIFACT_TYPE,
        }
    ) != 5:
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.CONTRACT_DRIFT
        )
    raw = portable_predicate_language_composition_verifier_contract_bytes()
    if (
        len(raw) != _V1_CONTRACT_BYTE_COUNT
        or hashlib.sha256(raw).hexdigest() != _V1_CONTRACT_PLAIN_SHA256
        or portable_predicate_language_composition_verifier_contract_sha256()
        != _V1_CONTRACT_SHA256
        or raw
        != _canonical_json(
            portable_predicate_language_composition_verifier_contract_tree()
        )
    ):
        _fail(
            PortablePredicateLanguageCompositionVerificationCode.CONTRACT_DRIFT
        )


_validate_reconstruction()


__all__ = [
    "PortablePredicateLanguageCompositionVerificationCode",
    "PortablePredicateLanguageCompositionVerificationError",
    "PortablePredicateLanguageCompositionVerificationPinsV1",
    "PortablePredicateLanguageCompositionVerificationResultV1",
    "parse_portable_predicate_language_composition_verifier_contract",
    "portable_predicate_language_composed_descriptor_verifier_bytes",
    "portable_predicate_language_composed_descriptor_verifier_sha256",
    "portable_predicate_language_composed_descriptor_verifier_tree",
    "portable_predicate_language_composition_verification_result_bytes",
    "portable_predicate_language_composition_verification_result_sha256",
    "portable_predicate_language_composition_verifier_contract_bytes",
    "portable_predicate_language_composition_verifier_contract_plain_sha256",
    "portable_predicate_language_composition_verifier_contract_sha256",
    "portable_predicate_language_composition_verifier_contract_tree",
    "validate_portable_predicate_language_composition_verification_result",
    "verify_linux_confinement_predecessor_projection_independently",
]
