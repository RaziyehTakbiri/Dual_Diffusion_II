"""Static synthetic Tessera profile for the portable predicate core.

The profile exercises the closed core/profile parameterization boundary with
synthetic artifact domains, authorities, public errors, locators, and two
membership specializations of different parameter arities.  It deliberately
declares no interval refinement.  It does not implement an evaluator or
resolver, validate a real domain, establish generality, or report an empirical
result.
"""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from typing import Final

from .adapter_portable_predicate_language_core import (
    MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_ARTIFACT_BYTES,
    PortablePredicateLanguageCoreError,
    portable_predicate_language_core_contract_sha256,
    portable_predicate_language_core_contract_tree,
    portable_predicate_language_core_profile_interface_sha256,
    portable_predicate_language_core_profile_interface_tree,
    validate_portable_predicate_profile_tree,
)


TESSERA_PREDICATE_PROFILE_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.synthetic.tessera.predicate-profile.v1"
)
TESSERA_PREDICATE_PROFILE_VERIFICATION_RESULT_ARTIFACT_TYPE: Final = (
    "heterodiff.synthetic.tessera.predicate-profile-verification-result.v1"
)
TESSERA_PREDICATE_PROFILE_CONTRACT_DIGEST_DOMAIN: Final = (
    TESSERA_PREDICATE_PROFILE_CONTRACT_ARTIFACT_TYPE
)
TESSERA_PREDICATE_PROFILE_ID: Final = "tessera-routing-v1"
TESSERA_PREDICATE_PROFILE_CLASS_ID: Final = (
    "synthetic-conformance-only"
)
TESSERA_PREDICATE_PROFILE_STATUS: Final = (
    "static-synthetic-tessera-profile-implemented-runtime-evaluator-not-"
    "implemented"
)
TESSERA_PREDICATE_PROFILE_VALIDATION_SCOPE: Final = (
    "static-profile-parameterization-only"
)

TESSERA_PREDICATE_PROFILE_AUTHORITY_CLASS_IDS: Final = (
    "scenario-fixture-authority",
    "catalog-fixture-authority",
    "oracle-fixture-authority",
    "external-fixture-authority",
)
TESSERA_PREDICATE_PROFILE_PUBLIC_ERROR_IDS: Final = (
    "tessera-local-rule-failed",
    "tessera-fixture-unavailable",
    "tessera-fixture-decode-rejected",
    "tessera-fixture-derivation-mismatch",
    "tessera-upstream-rule-failed",
    "tessera-external-authority-unavailable",
    "tessera-static-mapping-unresolved",
)
TESSERA_PREDICATE_PROFILE_LOCATOR_KIND_IDS: Final = (
    "tessera-conformance-slot",
    "tessera-fixture-direct-value",
    "tessera-fixture-object-member",
    "tessera-fixture-ordered-index",
    "tessera-fixture-composite-key",
    "tessera-sibling-resolved-value",
)
TESSERA_PREDICATE_PROFILE_NONCLAIM_IDS: Final = (
    "real-domain-generality-established",
    "synthetic-profile-conformance-executed",
)

_V1_CORE_CONTRACT_SHA256: Final = (
    "387b45d6f4ae8485433b36b929ed4d3a7b146c61e5d12629d46e2a74aa4536b2"
)
_V1_CORE_PROFILE_INTERFACE_SHA256: Final = (
    "2698f51d7326cc89d7a90880a7feea59d4cab81b3fffd4d04bc995ae646464b2"
)
_V1_CONTRACT_BYTE_COUNT: Final = 9695
_V1_CONTRACT_PLAIN_SHA256: Final = (
    "6118c948d579a26ff5b94b9b97cdde288c71f5f394d77cb7c895a20587e9ec15"
)
_V1_CONTRACT_SHA256: Final = (
    "786d01e7e4e22545d2ea39a938ef0e49c23348a6d451022e6b0bad932721fbf2"
)


class TesseraPredicateProfileCode(str, Enum):
    """Closed failures for the exact static Tessera profile."""

    INPUT_TYPE = "INPUT_TYPE"
    INPUT_RESOURCE = "INPUT_RESOURCE"
    JSON_INVALID = "JSON_INVALID"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    CANONICAL_MISMATCH = "CANONICAL_MISMATCH"
    CONTRACT_DRIFT = "CONTRACT_DRIFT"


_ERROR_MESSAGES: Final = {
    TesseraPredicateProfileCode.INPUT_TYPE: (
        "Tessera predicate profile input has an invalid exact type"
    ),
    TesseraPredicateProfileCode.INPUT_RESOURCE: (
        "Tessera predicate profile input exceeds its resource ceiling"
    ),
    TesseraPredicateProfileCode.JSON_INVALID: (
        "Tessera predicate profile JSON is invalid"
    ),
    TesseraPredicateProfileCode.SCHEMA_INVALID: (
        "Tessera predicate profile schema does not match V1"
    ),
    TesseraPredicateProfileCode.CANONICAL_MISMATCH: (
        "Tessera predicate profile bytes are not canonical"
    ),
    TesseraPredicateProfileCode.CONTRACT_DRIFT: (
        "Tessera predicate profile contract drifted from its invariants"
    ),
}


class TesseraPredicateProfileError(ValueError):
    """One fixed-message Tessera profile failure."""

    def __init__(self, code: TesseraPredicateProfileCode) -> None:
        if type(code) is not TesseraPredicateProfileCode:
            raise TypeError("Tessera predicate profile code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class _DuplicateKeyError(ValueError):
    pass


def _fail(code: TesseraPredicateProfileCode) -> None:
    raise TesseraPredicateProfileError(code) from None


def _canonical_json(value: object) -> bytes:
    try:
        result = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _fail(TesseraPredicateProfileCode.SCHEMA_INVALID)
    if (
        not result
        or len(result)
        > MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_ARTIFACT_BYTES
    ):
        _fail(TesseraPredicateProfileCode.INPUT_RESOURCE)
    return result


def _domain_sha256(domain: str, payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _object_without_duplicates(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _reject_json_constant(_: str) -> None:
    raise ValueError("non-finite JSON constant")


def _reject_json_float(_: str) -> None:
    raise ValueError("floating-point JSON number")


def _bounded_json_integer(value: str) -> int:
    digits = value[1:] if value.startswith("-") else value
    if not digits or len(digits) > 20:
        raise ValueError("JSON integer exceeds fixed syntax bound")
    return int(value, 10)


def _node_count(value: object, maximum: int) -> int:
    count = 0
    stack = [value]
    while stack:
        current = stack.pop()
        count += 1
        if count > maximum:
            return count
        if type(current) is dict:
            stack.extend(current.values())
        elif type(current) is list:
            stack.extend(current)
    return count


def _json_depth(value: object, maximum: int) -> int:
    deepest = 0
    stack = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        deepest = max(deepest, depth)
        if deepest > maximum:
            return deepest
        if type(current) is dict:
            stack.extend(
                (item, depth + 1)
                for item in current.values()
            )
        elif type(current) is list:
            stack.extend((item, depth + 1) for item in current)
    return deepest


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


def _artifact_domain_rows() -> list:
    rows = [
        (
            "predicate-program",
            "heterodiff.synthetic.tessera.predicate-program.v1",
        ),
        (
            "predicate-evaluation-context",
            "heterodiff.synthetic.tessera.evaluation-context.v1",
        ),
        (
            "predicate-input-bundle",
            "heterodiff.synthetic.tessera.input-bundle.v1",
        ),
        (
            "predicate-evaluation-result",
            "heterodiff.synthetic.tessera.evaluation-result.v1",
        ),
        (
            "predicate-formula-core",
            "heterodiff.synthetic.tessera.formula-core.v1",
        ),
        (
            "fixture",
            "heterodiff.synthetic.tessera.fixture.v1",
        ),
        (
            "list-order-contract",
            "heterodiff.synthetic.tessera.list-order-contract.v1",
        ),
    ]
    return [
        {
            "artifact_role_id": role_id,
            "artifact_type_id": artifact_type_id,
            "digest_domain_id": artifact_type_id,
            "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
        }
        for role_id, artifact_type_id in rows
    ]


def _public_error_role_rows() -> list:
    return [
        {
            "public_error_role_id": role_id,
            "public_error_id": error_id,
        }
        for role_id, error_id in (
            ("LOCAL_RULE_FAILED", "tessera-local-rule-failed"),
            (
                "RUNTIME_SOURCE_UNAVAILABLE",
                "tessera-fixture-unavailable",
            ),
            ("PARSER_REJECTED", "tessera-fixture-decode-rejected"),
            (
                "DERIVATION_MISMATCH",
                "tessera-fixture-derivation-mismatch",
            ),
            (
                "UPSTREAM_RULE_FAILED",
                "tessera-upstream-rule-failed",
            ),
            (
                "EXTERNAL_AUTHORITY_UNAVAILABLE",
                "tessera-external-authority-unavailable",
            ),
            (
                "STATIC_MAPPING_UNRESOLVED",
                "tessera-static-mapping-unresolved",
            ),
        )
    ]


def _profile_parameter_rows() -> list:
    rows = (
        (
            "primary-program-purpose-id",
            "tessera-routing-conformance",
        ),
        (
            "tessera-action-domain-slot",
            "tessera-action-id",
        ),
        (
            "tessera-route-domain-slot",
            "tessera-route-id",
        ),
        (
            "tessera-priority-domain-slot",
            "tessera-priority-id",
        ),
    )
    return [
        {
            "parameter_slot_id": slot_id,
            "parameter_value_id": value_id,
        }
        for slot_id, value_id in rows
    ]


def _profile_field_schema_rows() -> list:
    return [
        {
            "field_id": "expected-list-count",
            "role_parameter_id": "NONE",
            "semantic_role_id": "nonnegative-count",
            "value_schema_id": "nonnegative-index-or-count-integer-v1",
        },
        {
            "field_id": "fixture-artifact-type-id",
            "role_parameter_id": "fixture",
            "semantic_role_id": "artifact-type-for-role",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "fixture-identity-sha256",
            "role_parameter_id": "fixture",
            "semantic_role_id": "artifact-identity-sha256-for-role",
            "value_schema_id": "lowercase-sha256-string-v1",
        },
        {
            "field_id": "input-slot-id",
            "role_parameter_id": "NONE",
            "semantic_role_id": "opaque-identifier",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "list-index",
            "role_parameter_id": "expected-list-count",
            "semantic_role_id": "index-below-field",
            "value_schema_id": "nonnegative-index-or-count-integer-v1",
        },
        {
            "field_id": "list-order-contract-sha256",
            "role_parameter_id": "list-order-contract",
            "semantic_role_id": "artifact-identity-sha256-for-role",
            "value_schema_id": "lowercase-sha256-string-v1",
        },
        {
            "field_id": "mapping-id",
            "role_parameter_id": "NONE",
            "semantic_role_id": "opaque-identifier",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "ordered-key-component-rows",
            "role_parameter_id": "NONE",
            "semantic_role_id": "typed-key-components",
            "value_schema_id": "ordered-exact-object-row-array-v1",
        },
        {
            "field_id": "ordered-path-segments",
            "role_parameter_id": "NONE",
            "semantic_role_id": "path-segments",
            "value_schema_id": "ordered-exact-object-row-array-v1",
        },
        {
            "field_id": "scenario-id",
            "role_parameter_id": "NONE",
            "semantic_role_id": "opaque-identifier",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "sibling-operand-id",
            "role_parameter_id": "NONE",
            "semantic_role_id": "prior-input-resolved-operand",
            "value_schema_id": "strict-identifier-string-v1",
        },
    ]


def _locator_extension_rows() -> list:
    return [
        {
            "exact_configuration_field_ids": ["input-slot-id"],
            "exact_empty_placeholder_field_ids": [],
            "locator_kind_id": "tessera-conformance-slot",
            "locator_primitive_id": "direct-bound-value",
            "validation_primitive_id": (
                "profile-field-schema-and-locator-primitive-v1"
            ),
            "validation_rule_id": (
                "exact-synthetic-input-slot-binding-v1"
            ),
        },
        {
            "exact_configuration_field_ids": [
                "fixture-artifact-type-id",
                "fixture-identity-sha256",
                "mapping-id",
            ],
            "exact_empty_placeholder_field_ids": [],
            "locator_kind_id": "tessera-fixture-direct-value",
            "locator_primitive_id": "direct-bound-value",
            "validation_primitive_id": (
                "profile-field-schema-and-locator-primitive-v1"
            ),
            "validation_rule_id": (
                "exact-fixture-identity-and-mapping-binding-v1"
            ),
        },
        {
            "exact_configuration_field_ids": [
                "fixture-artifact-type-id",
                "fixture-identity-sha256",
                "mapping-id",
                "ordered-path-segments",
            ],
            "exact_empty_placeholder_field_ids": [],
            "locator_kind_id": "tessera-fixture-object-member",
            "locator_primitive_id": "bounded-artifact-path",
            "validation_primitive_id": (
                "profile-field-schema-and-locator-primitive-v1"
            ),
            "validation_rule_id": (
                "exact-object-member-path-without-wildcards-v1"
            ),
        },
        {
            "exact_configuration_field_ids": [
                "expected-list-count",
                "list-index",
                "list-order-contract-sha256",
            ],
            "exact_empty_placeholder_field_ids": [],
            "locator_kind_id": "tessera-fixture-ordered-index",
            "locator_primitive_id": "ordered-index",
            "validation_primitive_id": (
                "profile-field-schema-and-locator-primitive-v1"
            ),
            "validation_rule_id": (
                "exact-index-count-and-order-contract-v1"
            ),
        },
        {
            "exact_configuration_field_ids": [
                "ordered-key-component-rows",
            ],
            "exact_empty_placeholder_field_ids": [],
            "locator_kind_id": "tessera-fixture-composite-key",
            "locator_primitive_id": "composite-key",
            "validation_primitive_id": (
                "profile-field-schema-and-locator-primitive-v1"
            ),
            "validation_rule_id": (
                "one-to-four-typed-components-exactly-one-match-v1"
            ),
        },
        {
            "exact_configuration_field_ids": ["sibling-operand-id"],
            "exact_empty_placeholder_field_ids": [],
            "locator_kind_id": "tessera-sibling-resolved-value",
            "locator_primitive_id": "sibling-resolved-value",
            "validation_primitive_id": (
                "profile-field-schema-and-locator-primitive-v1"
            ),
            "validation_rule_id": (
                "exact-prior-resolved-sibling-operand-v1"
            ),
        },
    ]


def _program_purpose_rows() -> list:
    return [
        {
            "exact_binding_field_ids": [
                "fixture-artifact-type-id",
                "fixture-identity-sha256",
                "scenario-id",
            ],
            "program_purpose_id": "tessera-routing-conformance",
            "purpose_relation_rows": [],
            "validation_primitive_id": (
                "profile-field-schema-and-purpose-relations-v1"
            ),
            "validation_rule_id": (
                "exact-typed-fixture-identity-and-strict-scenario-"
                "identifier-v1"
            ),
        },
    ]


def _operator_specialization_rows() -> list:
    return [
        {
            "exposed_operator_id": "tessera-route-is-admitted",
            "operand_source_rule_id": (
                "second-membership-sequence-program-literal-canonical-"
                "unique-nonempty-v1"
            ),
            "ordered_parameter_slot_ids": [
                "tessera-action-domain-slot",
                "tessera-route-domain-slot",
            ],
            "primitive_id": "member-of-frozen-program-set",
            "type_and_truth_rule_id": (
                "one-value-and-unique-nonempty-sequence-of-identical-"
                "item-type-exact-membership-v1"
            ),
        },
        {
            "exposed_operator_id": "tessera-priority-is-admitted",
            "operand_source_rule_id": (
                "second-membership-sequence-program-literal-canonical-"
                "unique-nonempty-v1"
            ),
            "ordered_parameter_slot_ids": [
                "tessera-priority-domain-slot",
            ],
            "primitive_id": "member-of-frozen-program-set",
            "type_and_truth_rule_id": (
                "one-value-and-unique-nonempty-sequence-of-identical-"
                "item-type-exact-membership-v1"
            ),
        },
    ]


def _interval_refinement_rows() -> list:
    return []


def tessera_predicate_profile_contract_tree() -> dict:
    """Return the exact synthetic Tessera profile contract."""

    core_tree = portable_predicate_language_core_contract_tree()
    interface = (
        portable_predicate_language_core_profile_interface_tree()
    )
    anchors = []
    domains = _artifact_domain_rows()
    locators = _locator_extension_rows()
    purposes = _program_purpose_rows()
    errors = list(TESSERA_PREDICATE_PROFILE_PUBLIC_ERROR_IDS)
    error_roles = _public_error_role_rows()
    parameters = _profile_parameter_rows()
    profile_fields = _profile_field_schema_rows()
    specializations = _operator_specialization_rows()
    refinements = _interval_refinement_rows()
    nonclaims = {
        claim_id: False
        for claim_id in TESSERA_PREDICATE_PROFILE_NONCLAIM_IDS
    }
    tree = {
        "anchor_contract_rows": anchors,
        "artifact_domain_rows": domains,
        "artifact_type": (
            TESSERA_PREDICATE_PROFILE_CONTRACT_ARTIFACT_TYPE
        ),
        "authority_class_ids": list(
            TESSERA_PREDICATE_PROFILE_AUTHORITY_CLASS_IDS
        ),
        "core_contract_sha256": (
            portable_predicate_language_core_contract_sha256()
        ),
        "core_profile_interface_sha256": (
            portable_predicate_language_core_profile_interface_sha256()
        ),
        "digest_computation_id": core_tree["digest_computation_id"],
        "encoding_id": core_tree["encoding_id"],
        "fixed_counts": {
            "anchor_contract_count": len(anchors),
            "artifact_domain_count": len(domains),
            "authority_class_count": len(
                TESSERA_PREDICATE_PROFILE_AUTHORITY_CLASS_IDS
            ),
            "interval_refinement_count": len(refinements),
            "locator_extension_count": len(locators),
            "operator_specialization_count": len(specializations),
            "profile_claim_count": len(nonclaims),
            "profile_field_schema_count": len(profile_fields),
            "profile_parameter_count": len(parameters),
            "program_purpose_count": len(purposes),
            "program_purpose_relation_count": sum(
                len(row["purpose_relation_rows"]) for row in purposes
            ),
            "public_error_count": len(errors),
            "public_error_role_count": len(error_roles),
        },
        "format_version": "1",
        "implementation_status_id": TESSERA_PREDICATE_PROFILE_STATUS,
        "interval_refinement_rows": refinements,
        "locator_extension_rows": locators,
        "nonclaim_state": nonclaims,
        "operator_specialization_rows": specializations,
        "profile_class_id": TESSERA_PREDICATE_PROFILE_CLASS_ID,
        "profile_id": TESSERA_PREDICATE_PROFILE_ID,
        "profile_interface_id": interface["profile_interface_id"],
        "profile_field_schema_rows": profile_fields,
        "profile_parameter_rows": parameters,
        "profile_verification_result_artifact_type": (
            TESSERA_PREDICATE_PROFILE_VERIFICATION_RESULT_ARTIFACT_TYPE
        ),
        "program_purpose_rows": purposes,
        "public_error_ids": errors,
        "public_error_role_rows": error_roles,
        "validation_scope_id": (
            TESSERA_PREDICATE_PROFILE_VALIDATION_SCOPE
        ),
    }
    try:
        validate_portable_predicate_profile_tree(tree)
    except PortablePredicateLanguageCoreError:
        _fail(TesseraPredicateProfileCode.CONTRACT_DRIFT)
    return tree


def tessera_predicate_profile_contract_bytes() -> bytes:
    """Serialize the exact Tessera profile contract."""

    return _canonical_json(tessera_predicate_profile_contract_tree())


def tessera_predicate_profile_contract_plain_sha256() -> str:
    """Return ordinary SHA-256 over the exact profile bytes."""

    return hashlib.sha256(
        tessera_predicate_profile_contract_bytes()
    ).hexdigest()


def tessera_predicate_profile_contract_sha256() -> str:
    """Return the length-bound domain-separated profile identity."""

    return _domain_sha256(
        TESSERA_PREDICATE_PROFILE_CONTRACT_DIGEST_DOMAIN,
        tessera_predicate_profile_contract_bytes(),
    )


def parse_tessera_predicate_profile_contract(value: bytes) -> dict:
    """Strictly parse the one exact Tessera profile contract."""

    if type(value) is not bytes:
        _fail(TesseraPredicateProfileCode.INPUT_TYPE)
    core_limits = portable_predicate_language_core_contract_tree()[
        "resource_limits"
    ]
    if not value or len(value) > core_limits["artifact_bytes"]:
        _fail(TesseraPredicateProfileCode.INPUT_RESOURCE)
    try:
        decoded = json.loads(
            value.decode("ascii", "strict"),
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_json_constant,
            parse_float=_reject_json_float,
            parse_int=_bounded_json_integer,
        )
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _fail(TesseraPredicateProfileCode.JSON_INVALID)
    if type(decoded) is not dict:
        _fail(TesseraPredicateProfileCode.SCHEMA_INVALID)
    if (
        _json_depth(decoded, core_limits["json_depth"])
        > core_limits["json_depth"]
        or _node_count(decoded, core_limits["json_items"])
        > core_limits["json_items"]
    ):
        _fail(TesseraPredicateProfileCode.INPUT_RESOURCE)
    expected = tessera_predicate_profile_contract_tree()
    if not _same_exact(decoded, expected):
        _fail(TesseraPredicateProfileCode.SCHEMA_INVALID)
    if value != tessera_predicate_profile_contract_bytes():
        _fail(TesseraPredicateProfileCode.CANONICAL_MISMATCH)
    return expected


def _validate_contract_coherence() -> None:
    tree = tessera_predicate_profile_contract_tree()
    interface = (
        portable_predicate_language_core_profile_interface_tree()
    )
    domains = tree["artifact_domain_rows"]
    error_rows = tree["public_error_role_rows"]
    parameter_rows = tree["profile_parameter_rows"]
    locator_rows = tree["locator_extension_rows"]
    profile_fields = tree["profile_field_schema_rows"]
    specializations = tree["operator_specialization_rows"]
    refinements = tree["interval_refinement_rows"]
    referenced_profile_field_ids = {
        field_id
        for row in locator_rows
        for field_id in row["exact_configuration_field_ids"]
    } | {
        field_id
        for row in tree["program_purpose_rows"]
        for field_id in row["exact_binding_field_ids"]
    }
    if (
        tree["core_contract_sha256"]
        != portable_predicate_language_core_contract_sha256()
        or tree["core_profile_interface_sha256"]
        != portable_predicate_language_core_profile_interface_sha256()
        or tree["profile_interface_id"]
        != interface["profile_interface_id"]
        or [
            row["public_error_role_id"] for row in error_rows
        ]
        != interface["required_public_error_role_ids"]
        or [
            row["parameter_slot_id"]
            for row in parameter_rows[
                : len(interface["required_profile_parameter_slot_ids"])
            ]
        ]
        != interface["required_profile_parameter_slot_ids"]
        or [
            row["locator_kind_id"] for row in locator_rows
        ]
        != list(TESSERA_PREDICATE_PROFILE_LOCATOR_KIND_IDS)
        or {
            row["locator_primitive_id"] for row in locator_rows
        }
        != set(interface["admitted_locator_primitive_ids"])
        or profile_fields != _profile_field_schema_rows()
        or [row["field_id"] for row in profile_fields]
        != sorted(referenced_profile_field_ids)
        or any(
            row["validation_primitive_id"]
            != interface["profile_locator_validation_primitive_id"]
            for row in locator_rows
        )
        or any(
            row["validation_primitive_id"]
            != interface[
                "profile_program_purpose_validation_primitive_id"
            ]
            for row in tree["program_purpose_rows"]
        )
        or [
            len(row["ordered_parameter_slot_ids"])
            for row in specializations
        ]
        != [2, 1]
        or any(
            row["primitive_id"]
            not in interface[
                "admitted_profile_bound_operator_primitive_ids"
            ]
            for row in specializations
        )
        or refinements != []
        or [
            row["artifact_role_id"] for row in domains[:5]
        ]
        != interface["required_runtime_artifact_role_ids"]
        or any(
            row["artifact_type_id"] != row["digest_domain_id"]
            for row in domains
        )
        or any(tree["nonclaim_state"].values())
        or b"linux" in tessera_predicate_profile_contract_bytes().lower()
    ):
        raise RuntimeError(
            _ERROR_MESSAGES[
                TesseraPredicateProfileCode.CONTRACT_DRIFT
            ]
        )


_validate_contract_coherence()


def _validate_frozen_contract() -> None:
    raw = tessera_predicate_profile_contract_bytes()
    tree = tessera_predicate_profile_contract_tree()
    if (
        len(raw) != _V1_CONTRACT_BYTE_COUNT
        or hashlib.sha256(raw).hexdigest()
        != _V1_CONTRACT_PLAIN_SHA256
        or tessera_predicate_profile_contract_sha256()
        != _V1_CONTRACT_SHA256
        or tree["core_contract_sha256"]
        != _V1_CORE_CONTRACT_SHA256
        or tree["core_profile_interface_sha256"]
        != _V1_CORE_PROFILE_INTERFACE_SHA256
        or any(tree["nonclaim_state"].values())
    ):
        raise RuntimeError(
            _ERROR_MESSAGES[
                TesseraPredicateProfileCode.CONTRACT_DRIFT
            ]
        )


_validate_frozen_contract()


__all__ = [
    "TESSERA_PREDICATE_PROFILE_AUTHORITY_CLASS_IDS",
    "TESSERA_PREDICATE_PROFILE_CLASS_ID",
    "TESSERA_PREDICATE_PROFILE_CONTRACT_ARTIFACT_TYPE",
    "TESSERA_PREDICATE_PROFILE_CONTRACT_DIGEST_DOMAIN",
    "TESSERA_PREDICATE_PROFILE_ID",
    "TESSERA_PREDICATE_PROFILE_LOCATOR_KIND_IDS",
    "TESSERA_PREDICATE_PROFILE_NONCLAIM_IDS",
    "TESSERA_PREDICATE_PROFILE_PUBLIC_ERROR_IDS",
    "TESSERA_PREDICATE_PROFILE_VERIFICATION_RESULT_ARTIFACT_TYPE",
    "TesseraPredicateProfileCode",
    "TesseraPredicateProfileError",
    "parse_tessera_predicate_profile_contract",
    "tessera_predicate_profile_contract_bytes",
    "tessera_predicate_profile_contract_plain_sha256",
    "tessera_predicate_profile_contract_sha256",
    "tessera_predicate_profile_contract_tree",
]
