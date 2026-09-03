"""Static Linux profile for the portable predicate-language core.

The profile supplies only Linux-specific registries, bindings, refinements,
artifact domains, and permanently false claims.  It does not implement a
runtime parser, evaluator, native acquisition, or an authorization decision.
"""

from __future__ import annotations

from enum import Enum
import hashlib
import json
from typing import Final

from .adapter_linux_confinement_native_mapping import (
    LINUX_CONFINEMENT_NATIVE_MAPPING_AUTHORITY_CLASS_IDS,
    LINUX_CONFINEMENT_NATIVE_MAPPING_ERROR_IDS,
    LINUX_CONFINEMENT_NATIVE_MAPPING_OPERAND_LOCATOR_KIND_IDS,
    linux_confinement_native_mapping_gap_contract_sha256,
)
from .adapter_portable_predicate_language_core import (
    portable_predicate_language_core_contract_sha256,
    portable_predicate_language_core_profile_interface_sha256,
    portable_predicate_language_core_profile_interface_tree,
    validate_portable_predicate_profile_tree,
)


LINUX_CONFINEMENT_PREDICATE_PROFILE_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-predicate-profile-contract.v1"
)
LINUX_CONFINEMENT_PREDICATE_PROFILE_VERIFICATION_RESULT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-predicate-profile-verification-"
    "result.v1"
)
LINUX_CONFINEMENT_PREDICATE_PROFILE_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_PREDICATE_PROFILE_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_PREDICATE_PROFILE_STATUS: Final = (
    "STATIC_LINUX_PREDICATE_PROFILE_IMPLEMENTED_RUNTIME_EVALUATOR_NOT_"
    "IMPLEMENTED"
)
LINUX_CONFINEMENT_PREDICATE_PROFILE_VALIDATION_SCOPE: Final = (
    "STATIC_PROFILE_REGISTRIES_BINDINGS_REFINEMENTS_AND_LEGACY_PROJECTION_"
    "ONLY"
)
LINUX_CONFINEMENT_PREDICATE_PROFILE_ID: Final = "LINUX_CONFINEMENT_V1"
LINUX_CONFINEMENT_PREDICATE_PROFILE_CLASS_ID: Final = (
    "PLATFORM_SECURITY_STATIC_PROFILE"
)
LINUX_CONFINEMENT_PREDICATE_PROFILE_ENCODING_ID: Final = (
    "canonical-ascii-json-sort-keys-no-whitespace-v1"
)
LINUX_CONFINEMENT_PREDICATE_PROFILE_DIGEST_COMPUTATION_ID: Final = (
    "sha256-domain-nul-u64be-length-canonical-bytes-v1"
)

MAXIMUM_LINUX_CONFINEMENT_PREDICATE_PROFILE_BYTES: Final = 1024 * 1024
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_PROFILE_JSON_DEPTH: Final = 32
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_PROFILE_JSON_ITEMS: Final = 32768
_MAXIMUM_JSON_INTEGER_DIGITS: Final = 20
_V1_PROFILE_BYTE_COUNT: Final = 15992
_V1_PROFILE_PLAIN_SHA256: Final = (
    "82a36c2ca07d25afc4cc44e2fa6ae1b2e481b77fb96bc56396bd6e54fb5be658"
)
_V1_PROFILE_SHA256: Final = (
    "31204b1598e203e920fb8b1349116bc27a5162a34fe50ec5112ef957cb9bbdd7"
)
_V1_CORE_SHA256: Final = (
    "387b45d6f4ae8485433b36b929ed4d3a7b146c61e5d12629d46e2a74aa4536b2"
)
_V1_CORE_PROFILE_INTERFACE_SHA256: Final = (
    "2698f51d7326cc89d7a90880a7feea59d4cab81b3fffd4d04bc995ae646464b2"
)

LINUX_CONFINEMENT_PREDICATE_PROFILE_CLAIM_IDS: Final = (
    "authorizing_gate_implemented",
    "custody_authenticated",
    "linux_confinement_established",
    "linux_execution_observed",
    "native_acquisition_implemented",
    "native_origin_authenticated",
    "native_source_derivations_validated",
    "observation_formula_inventory_implemented",
    "operand_authorities_authenticated",
    "operand_locators_resolved",
    "policy_predicate_evaluated",
    "predicate_formula_implemented",
    "release_authorized",
)


class LinuxConfinementPredicateProfileCode(str, Enum):
    """Closed failures for the exact static Linux profile."""

    INPUT_TYPE = "INPUT_TYPE"
    INPUT_RESOURCE = "INPUT_RESOURCE"
    JSON_INVALID = "JSON_INVALID"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    CANONICAL_MISMATCH = "CANONICAL_MISMATCH"
    CONTRACT_DRIFT = "CONTRACT_DRIFT"


_ERROR_MESSAGES: Final = {
    LinuxConfinementPredicateProfileCode.INPUT_TYPE: (
        "Linux predicate profile input has an invalid exact type"
    ),
    LinuxConfinementPredicateProfileCode.INPUT_RESOURCE: (
        "Linux predicate profile input exceeds its resource ceiling"
    ),
    LinuxConfinementPredicateProfileCode.JSON_INVALID: (
        "Linux predicate profile JSON is invalid"
    ),
    LinuxConfinementPredicateProfileCode.SCHEMA_INVALID: (
        "Linux predicate profile schema is invalid"
    ),
    LinuxConfinementPredicateProfileCode.CANONICAL_MISMATCH: (
        "Linux predicate profile bytes are not canonical"
    ),
    LinuxConfinementPredicateProfileCode.CONTRACT_DRIFT: (
        "Linux predicate profile implementation drifted from its contract"
    ),
}


class LinuxConfinementPredicateProfileError(ValueError):
    """One fixed-message profile failure."""

    def __init__(self, code: LinuxConfinementPredicateProfileCode):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


class _DuplicateKeyError(ValueError):
    pass


def _fail(code: LinuxConfinementPredicateProfileCode) -> None:
    raise LinuxConfinementPredicateProfileError(code)


def _canonical_json(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _fail(LinuxConfinementPredicateProfileCode.SCHEMA_INVALID)
    if len(encoded) > MAXIMUM_LINUX_CONFINEMENT_PREDICATE_PROFILE_BYTES:
        _fail(LinuxConfinementPredicateProfileCode.INPUT_RESOURCE)
    return encoded


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
    raise ValueError


def _reject_json_float(_: str) -> None:
    raise ValueError


def _bounded_json_integer(value: str) -> int:
    if len(value.lstrip("-")) > _MAXIMUM_JSON_INTEGER_DIGITS:
        raise ValueError
    return int(value)


def _node_count(value: object) -> int:
    count = 0
    stack = [value]
    while stack:
        current = stack.pop()
        count += 1
        if (
            count
            > MAXIMUM_LINUX_CONFINEMENT_PREDICATE_PROFILE_JSON_ITEMS
        ):
            return count
        if type(current) is dict:
            stack.extend(current.values())
        elif type(current) is list:
            stack.extend(current)
    return count


def _json_depth(value: object) -> int:
    maximum = 0
    stack = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        maximum = max(maximum, depth)
        if (
            maximum
            > MAXIMUM_LINUX_CONFINEMENT_PREDICATE_PROFILE_JSON_DEPTH
        ):
            return maximum
        if type(current) is dict:
            stack.extend((item, depth + 1) for item in current.values())
        elif type(current) is list:
            stack.extend((item, depth + 1) for item in current)
    return maximum


def _same_exact(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return list(left) == list(right) and all(
            _same_exact(left[key], right[key]) for key in left
        )
    if type(left) is list:
        return len(left) == len(right) and all(
            _same_exact(a, b) for a, b in zip(left, right)
        )
    return left == right


def _public_error_role_rows() -> list:
    return [
        {
            "public_error_id": public_error_id,
            "public_error_role_id": public_error_role_id,
        }
        for public_error_role_id, public_error_id in (
            ("LOCAL_RULE_FAILED", "PREDICATE_FAILED"),
            ("RUNTIME_SOURCE_UNAVAILABLE", "SOURCE_UNAVAILABLE"),
            ("PARSER_REJECTED", "PARSER_REJECTED"),
            ("DERIVATION_MISMATCH", "DERIVATION_MISMATCH"),
            ("UPSTREAM_RULE_FAILED", "PREDICATE_FAILED"),
            (
                "EXTERNAL_AUTHORITY_UNAVAILABLE",
                "AUTHORITY_UNAVAILABLE",
            ),
            (
                "STATIC_MAPPING_UNRESOLVED",
                "PREDICATE_NOT_EVALUATED",
            ),
        )
    ]


def _profile_parameter_rows() -> list:
    return [
        {
            "parameter_slot_id": parameter_slot_id,
            "parameter_value_id": parameter_value_id,
        }
        for parameter_slot_id, parameter_value_id in (
            (
                "primary-program-purpose-id",
                "LINUX_OBSERVATION_PREDICATE",
            ),
            ("outcome-component-0-domain-id", "source-operation-id"),
            (
                "outcome-component-1-domain-id",
                "source-availability-id",
            ),
            ("outcome-component-2-domain-id", "source-status-id"),
            ("outcome-component-3-domain-id", "linux-errno-id"),
            (
                "interval-endpoint-unit-id",
                "linux-clock-run-binding",
            ),
        )
    ]


def _profile_field_schema_rows() -> list:
    return [
        {
            "field_id": "formula_core_artifact_type_id",
            "role_parameter_id": "predicate-formula-core",
            "semantic_role_id": "artifact-type-for-role",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "formula_core_identity_semantics_id",
            "role_parameter_id": "predicate-formula-core",
            "semantic_role_id": "artifact-identity-semantics-for-role",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "formula_core_identity_sha256",
            "role_parameter_id": "predicate-formula-core",
            "semantic_role_id": "artifact-identity-sha256-for-role",
            "value_schema_id": "lowercase-sha256-string-v1",
        },
        {
            "field_id": "locator_kind_id",
            "role_parameter_id": "NONE",
            "semantic_role_id": "locator-kind-self",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "mapping_id",
            "role_parameter_id": "ordered_required_mapping_ids",
            "semantic_role_id": "identifier-member-of-purpose-field",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "observation_id",
            "role_parameter_id": "NONE",
            "semantic_role_id": "opaque-identifier",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "ordered_path_segments",
            "role_parameter_id": "NONE",
            "semantic_role_id": "path-segments",
            "value_schema_id": "ordered-exact-object-row-array-v1",
        },
        {
            "field_id": "ordered_required_mapping_ids",
            "role_parameter_id": "NONE",
            "semantic_role_id": "ordered-unique-identifiers",
            "value_schema_id": "ordered-identifier-array-v1",
        },
        {
            "field_id": "platform_profile_artifact_type_id",
            "role_parameter_id": "platform-profile",
            "semantic_role_id": "artifact-type-for-role",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "platform_profile_identity_semantics_id",
            "role_parameter_id": "platform-profile",
            "semantic_role_id": "artifact-identity-semantics-for-role",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "platform_profile_identity_sha256",
            "role_parameter_id": "platform-profile",
            "semantic_role_id": "artifact-identity-sha256-for-role",
            "value_schema_id": "lowercase-sha256-string-v1",
        },
        {
            "field_id": "policy_artifact_type_id",
            "role_parameter_id": "policy",
            "semantic_role_id": "artifact-type-for-role",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "policy_identity_semantics_id",
            "role_parameter_id": "policy",
            "semantic_role_id": "artifact-identity-semantics-for-role",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "policy_identity_sha256",
            "role_parameter_id": "policy",
            "semantic_role_id": "artifact-identity-sha256-for-role",
            "value_schema_id": "lowercase-sha256-string-v1",
        },
        {
            "field_id": "predicate_id",
            "role_parameter_id": "NONE",
            "semantic_role_id": "opaque-identifier",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "resolver_contract_artifact_type",
            "role_parameter_id": "linux-native-mapping-gap",
            "semantic_role_id": "anchor-artifact-type-for-role",
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "field_id": "resolver_contract_sha256",
            "role_parameter_id": "linux-native-mapping-gap",
            "semantic_role_id": "anchor-contract-sha256-for-role",
            "value_schema_id": "lowercase-sha256-string-v1",
        },
    ]


def _locator_extension_rows() -> list:
    primitive_by_locator = {
        "bound-artifact-member": "bounded-artifact-path",
        "canonical-policy-path": "bounded-artifact-path",
        "canonical-projection-path": "bounded-artifact-path",
        "capture-binding-field": "bounded-artifact-path",
        "decoded-direct-evidence": "direct-bound-value",
        "process-snapshot-field": "bounded-artifact-path",
        "sibling-evidence-operand": "direct-bound-value",
        "staging-event-field": "bounded-artifact-path",
        "subject-identity-component": "bounded-artifact-path",
    }
    return [
        {
            "exact_configuration_field_ids": [
                "locator_kind_id",
                "resolver_contract_artifact_type",
                "resolver_contract_sha256",
                "mapping_id",
                "ordered_path_segments",
            ],
            "exact_empty_placeholder_field_ids": (
                ["ordered_path_segments"]
                if locator_kind_id
                in {
                    "decoded-direct-evidence",
                    "sibling-evidence-operand",
                }
                else []
            ),
            "locator_kind_id": locator_kind_id,
            "locator_primitive_id": primitive_by_locator[locator_kind_id],
            "validation_primitive_id": (
                "profile-field-schema-and-locator-primitive-v1"
            ),
            "validation_rule_id": (
                "strict-artifact-type-domain-contract-sha256-and-mapping-id-"
                "resolving-same-53a-occurrence-and-membership-in-program-"
                "ordered-required-mapping-ids-v1"
            ),
        }
        for locator_kind_id in (
            LINUX_CONFINEMENT_NATIVE_MAPPING_OPERAND_LOCATOR_KIND_IDS
        )
        if locator_kind_id not in {"derived-expression", "fixed-literal"}
    ]


def _linux_purpose_row() -> dict:
    return {
        "exact_binding_field_ids": [
            "observation_id",
            "predicate_id",
            "ordered_required_mapping_ids",
            "policy_artifact_type_id",
            "policy_identity_semantics_id",
            "policy_identity_sha256",
            "platform_profile_artifact_type_id",
            "platform_profile_identity_semantics_id",
            "platform_profile_identity_sha256",
            "formula_core_artifact_type_id",
            "formula_core_identity_semantics_id",
            "formula_core_identity_sha256",
        ],
        "program_purpose_id": "LINUX_OBSERVATION_PREDICATE",
        "purpose_relation_rows": [
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
                        "anchor_row_value_path_ids": [
                            "ordered_mapping_ids"
                        ],
                        "purpose_binding_field_id": (
                            "ordered_required_mapping_ids"
                        ),
                    },
                ],
                "relation_id": (
                    "linux-native-predicate-row-exact-match"
                ),
                "relation_primitive_id": (
                    "exactly-one-pinned-anchor-row-canonical-equality-v1"
                ),
            },
            {
                "locator_value_field_id": "mapping_id",
                "purpose_binding_field_id": (
                    "ordered_required_mapping_ids"
                ),
                "relation_id": "linux-required-mapping-coverage",
                "relation_primitive_id": (
                    "purpose-identifiers-exactly-covered-by-input-"
                    "locators-v1"
                ),
            },
        ],
        "validation_primitive_id": (
            "profile-field-schema-and-purpose-relations-v1"
        ),
        "validation_rule_id": (
            "exact-one-53a-predicate-row-observation-and-predicate-match-with-"
            "byte-exact-nonempty-unique-ordered-mapping-ids-and-typed-policy-"
            "platform-formula-core-identities-v1"
        ),
    }


def _artifact_domain_rows() -> list:
    return [
        {
            "artifact_role_id": role_id,
            "artifact_type_id": artifact_type_id,
            "digest_domain_id": artifact_type_id,
            "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
        }
        for role_id, artifact_type_id in (
            (
                "predicate-program",
                "heterodiff.adapter.linux-confinement-predicate-program.v1",
            ),
            (
                "predicate-evaluation-context",
                "heterodiff.adapter.linux-confinement-predicate-evaluation-"
                "context.v1",
            ),
            (
                "predicate-input-bundle",
                "heterodiff.adapter.linux-confinement-predicate-input-"
                "bundle.v1",
            ),
            (
                "predicate-evaluation-result",
                "heterodiff.adapter.linux-confinement-predicate-evaluation-"
                "result.v1",
            ),
            (
                "predicate-formula-core",
                "heterodiff.adapter.linux-confinement-predicate-formula-"
                "core.v1",
            ),
            (
                "policy",
                "heterodiff.adapter.linux-confinement-policy.v1",
            ),
            (
                "platform-profile",
                "heterodiff.adapter.linux-platform-profile.v1",
            ),
        )
    ]


def _outcome_specialization_row() -> dict:
    return {
        "exposed_operator_id": "status-is-approved",
        "operand_source_rule_id": (
            "second-membership-sequence-program-literal-canonical-unique-"
            "nonempty-v1"
        ),
        "ordered_parameter_slot_ids": [
            "outcome-component-0-domain-id",
            "outcome-component-1-domain-id",
            "outcome-component-2-domain-id",
            "outcome-component-3-domain-id",
        ],
        "primitive_id": "member-of-frozen-program-set",
        "type_and_truth_rule_id": (
            "one-value-and-unique-nonempty-sequence-of-identical-item-type-"
            "exact-membership-v1"
        ),
    }


def _interval_refinement_row() -> dict:
    return {
        "endpoint_parameter_slot_id": "interval-endpoint-unit-id",
        "exposed_refinement_id": "LINUX_CLOCK_RUN_BOUND_ENDPOINT",
        "refinement_primitive_id": "nominal-u64-endpoint-binding",
        "validation_rule_id": (
            "prior-u64-endpoint-one-nominal-clock-run-binding-v1"
        ),
    }


def linux_confinement_predicate_profile_contract_tree() -> dict:
    """Return the exact static Linux profile contract."""

    interface = portable_predicate_language_core_profile_interface_tree()
    anchors = [
        {
            "anchor_role_id": "linux-native-mapping-gap",
            "artifact_type_id": (
                "heterodiff.adapter.linux-confinement-native-mapping-gap-"
                "contract.v1"
            ),
            "contract_sha256": (
                linux_confinement_native_mapping_gap_contract_sha256()
            ),
        }
    ]
    domains = _artifact_domain_rows()
    authorities = list(
        LINUX_CONFINEMENT_NATIVE_MAPPING_AUTHORITY_CLASS_IDS
    )
    errors = list(LINUX_CONFINEMENT_NATIVE_MAPPING_ERROR_IDS)
    error_roles = _public_error_role_rows()
    parameters = _profile_parameter_rows()
    profile_fields = _profile_field_schema_rows()
    locators = _locator_extension_rows()
    purposes = [_linux_purpose_row()]
    specializations = [_outcome_specialization_row()]
    refinements = [_interval_refinement_row()]
    claims = {
        claim_id: False
        for claim_id in LINUX_CONFINEMENT_PREDICATE_PROFILE_CLAIM_IDS
    }
    tree = {
        "anchor_contract_rows": anchors,
        "artifact_domain_rows": _artifact_domain_rows(),
        "artifact_type": LINUX_CONFINEMENT_PREDICATE_PROFILE_ARTIFACT_TYPE,
        "authority_class_ids": authorities,
        "core_contract_sha256": (
            portable_predicate_language_core_contract_sha256()
        ),
        "core_profile_interface_sha256": (
            portable_predicate_language_core_profile_interface_sha256()
        ),
        "digest_computation_id": (
            LINUX_CONFINEMENT_PREDICATE_PROFILE_DIGEST_COMPUTATION_ID
        ),
        "encoding_id": LINUX_CONFINEMENT_PREDICATE_PROFILE_ENCODING_ID,
        "fixed_counts": {
            "anchor_contract_count": len(anchors),
            "artifact_domain_count": len(domains),
            "authority_class_count": len(authorities),
            "interval_refinement_count": len(refinements),
            "locator_extension_count": len(locators),
            "operator_specialization_count": len(specializations),
            "profile_claim_count": len(claims),
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
        "implementation_status_id": (
            LINUX_CONFINEMENT_PREDICATE_PROFILE_STATUS
        ),
        "interval_refinement_rows": refinements,
        "locator_extension_rows": locators,
        "nonclaim_state": claims,
        "operator_specialization_rows": specializations,
        "profile_class_id": (
            LINUX_CONFINEMENT_PREDICATE_PROFILE_CLASS_ID
        ),
        "profile_field_schema_rows": profile_fields,
        "profile_id": LINUX_CONFINEMENT_PREDICATE_PROFILE_ID,
        "profile_interface_id": interface["profile_interface_id"],
        "profile_parameter_rows": parameters,
        "profile_verification_result_artifact_type": (
            LINUX_CONFINEMENT_PREDICATE_PROFILE_VERIFICATION_RESULT_ARTIFACT_TYPE
        ),
        "program_purpose_rows": purposes,
        "public_error_ids": errors,
        "public_error_role_rows": error_roles,
        "validation_scope_id": (
            LINUX_CONFINEMENT_PREDICATE_PROFILE_VALIDATION_SCOPE
        ),
    }
    return validate_portable_predicate_profile_tree(tree)


def linux_confinement_predicate_profile_contract_bytes() -> bytes:
    """Return canonical bytes for the exact static Linux profile."""

    return _canonical_json(
        linux_confinement_predicate_profile_contract_tree()
    )


def linux_confinement_predicate_profile_contract_plain_sha256() -> str:
    """Return the ordinary SHA-256 of the canonical profile bytes."""

    return hashlib.sha256(
        linux_confinement_predicate_profile_contract_bytes()
    ).hexdigest()


def linux_confinement_predicate_profile_contract_sha256() -> str:
    """Return the length-bound domain-separated profile identity."""

    return _domain_sha256(
        LINUX_CONFINEMENT_PREDICATE_PROFILE_DIGEST_DOMAIN,
        linux_confinement_predicate_profile_contract_bytes(),
    )


def parse_linux_confinement_predicate_profile_contract(
    value: bytes,
) -> dict:
    """Strictly parse the one exact static Linux profile."""

    if type(value) is not bytes:
        _fail(LinuxConfinementPredicateProfileCode.INPUT_TYPE)
    if (
        not value
        or len(value) > MAXIMUM_LINUX_CONFINEMENT_PREDICATE_PROFILE_BYTES
    ):
        _fail(LinuxConfinementPredicateProfileCode.INPUT_RESOURCE)
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
        _fail(LinuxConfinementPredicateProfileCode.JSON_INVALID)
    if (
        _json_depth(decoded)
        > MAXIMUM_LINUX_CONFINEMENT_PREDICATE_PROFILE_JSON_DEPTH
        or _node_count(decoded)
        > MAXIMUM_LINUX_CONFINEMENT_PREDICATE_PROFILE_JSON_ITEMS
    ):
        _fail(LinuxConfinementPredicateProfileCode.INPUT_RESOURCE)
    expected = linux_confinement_predicate_profile_contract_tree()
    if not _same_exact(decoded, expected):
        _fail(LinuxConfinementPredicateProfileCode.SCHEMA_INVALID)
    if value != linux_confinement_predicate_profile_contract_bytes():
        _fail(LinuxConfinementPredicateProfileCode.CANONICAL_MISMATCH)
    return expected


def linux_confinement_predicate_profile_legacy_projection() -> dict:
    """Return the normalized Linux-owned projection expected in legacy V1."""

    tree = linux_confinement_predicate_profile_contract_tree()
    return {
        "anchor_contract_rows": tree["anchor_contract_rows"],
        "artifact_domain_rows": tree["artifact_domain_rows"],
        "authority_class_ids": tree["authority_class_ids"],
        "interval_refinement_rows": tree["interval_refinement_rows"],
        "locator_extension_rows": tree["locator_extension_rows"],
        "nonclaim_state": tree["nonclaim_state"],
        "operator_specialization_rows": tree[
            "operator_specialization_rows"
        ],
        "profile_parameter_rows": tree["profile_parameter_rows"],
        "program_purpose_rows": tree["program_purpose_rows"],
        "public_error_ids": tree["public_error_ids"],
        "public_error_role_rows": tree["public_error_role_rows"],
    }


def _validate_contract_coherence() -> None:
    tree = linux_confinement_predicate_profile_contract_tree()
    interface = portable_predicate_language_core_profile_interface_tree()
    raw = linux_confinement_predicate_profile_contract_bytes()
    profile_fields = tree["profile_field_schema_rows"]
    referenced_profile_field_ids = {
        field_id
        for row in tree["locator_extension_rows"]
        for field_id in row["exact_configuration_field_ids"]
    } | {
        field_id
        for row in tree["program_purpose_rows"]
        for field_id in row["exact_binding_field_ids"]
    }
    if (
        tree["profile_interface_id"] != interface["profile_interface_id"]
        or tree["core_contract_sha256"]
        != portable_predicate_language_core_contract_sha256()
        or tree["core_profile_interface_sha256"]
        != portable_predicate_language_core_profile_interface_sha256()
        or tree["operator_specialization_rows"][0]["primitive_id"]
        != "member-of-frozen-program-set"
        or profile_fields != _profile_field_schema_rows()
        or [row["field_id"] for row in profile_fields]
        != sorted(referenced_profile_field_ids)
        or any(
            row["validation_primitive_id"]
            != interface["profile_locator_validation_primitive_id"]
            for row in tree["locator_extension_rows"]
        )
        or any(
            row["validation_primitive_id"]
            != interface[
                "profile_program_purpose_validation_primitive_id"
            ]
            for row in tree["program_purpose_rows"]
        )
        or next(
            row["locator_primitive_id"]
            for row in tree["locator_extension_rows"]
            if row["locator_kind_id"] == "sibling-evidence-operand"
        )
        != "direct-bound-value"
        or tree["core_contract_sha256"] != _V1_CORE_SHA256
        or tree["core_profile_interface_sha256"]
        != _V1_CORE_PROFILE_INTERFACE_SHA256
        or len(raw) != _V1_PROFILE_BYTE_COUNT
        or hashlib.sha256(raw).hexdigest() != _V1_PROFILE_PLAIN_SHA256
        or _domain_sha256(
            LINUX_CONFINEMENT_PREDICATE_PROFILE_DIGEST_DOMAIN,
            raw,
        )
        != _V1_PROFILE_SHA256
    ):
        _fail(LinuxConfinementPredicateProfileCode.CONTRACT_DRIFT)


_validate_contract_coherence()


__all__ = [
    "LINUX_CONFINEMENT_PREDICATE_PROFILE_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_PREDICATE_PROFILE_CLAIM_IDS",
    "LINUX_CONFINEMENT_PREDICATE_PROFILE_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_PREDICATE_PROFILE_VERIFICATION_RESULT_ARTIFACT_TYPE",
    "LinuxConfinementPredicateProfileCode",
    "LinuxConfinementPredicateProfileError",
    "linux_confinement_predicate_profile_contract_bytes",
    "linux_confinement_predicate_profile_contract_plain_sha256",
    "linux_confinement_predicate_profile_contract_sha256",
    "linux_confinement_predicate_profile_contract_tree",
    "linux_confinement_predicate_profile_legacy_projection",
    "parse_linux_confinement_predicate_profile_contract",
]
