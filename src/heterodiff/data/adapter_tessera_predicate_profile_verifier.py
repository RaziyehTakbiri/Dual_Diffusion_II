"""Implementation-separated verifier for the synthetic Tessera profile.

This module reconstructs the exact static profile through the verifier lane of
the portable predicate core.  It neither imports the source profile nor the
source core.  Successful verification establishes only canonical static
parameterization; it does not run a resolver, evaluator, or conformance case,
and it does not establish real-domain generality or an empirical result.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Final

from .adapter_portable_predicate_language_core_verifier import (
    PortablePredicateLanguageCoreVerificationError,
    portable_predicate_language_core_verifier_contract_sha256,
    portable_predicate_language_core_verifier_contract_tree,
    portable_predicate_language_core_verifier_profile_interface_sha256,
    portable_predicate_language_core_verifier_profile_interface_tree,
    validate_portable_predicate_profile_verifier_tree,
)


TESSERA_PREDICATE_PROFILE_VERIFIER_IMPLEMENTATION_STATUS: Final = (
    "IMPLEMENTATION_SEPARATED_STATIC_TESSERA_PROFILE_VERIFIER_IMPLEMENTED"
)
TESSERA_PREDICATE_PROFILE_VERIFICATION_STATUS: Final = (
    "STATIC_TESSERA_PROFILE_VERIFIED_RUNTIME_EVALUATOR_NOT_IMPLEMENTED"
)

_PROFILE_ARTIFACT_TYPE: Final = (
    "heterodiff.synthetic.tessera.predicate-profile.v1"
)
_PROFILE_DIGEST_DOMAIN: Final = _PROFILE_ARTIFACT_TYPE
_RESULT_ARTIFACT_TYPE: Final = (
    "heterodiff.synthetic.tessera.predicate-profile-verification-result.v1"
)
_VERIFIER_ID: Final = (
    "heterodiff.synthetic.tessera.predicate-profile-"
    "implementation-separated-verifier.v1"
)
_PROFILE_ID: Final = "tessera-routing-v1"
_PROFILE_CLASS_ID: Final = "synthetic-conformance-only"
_PROFILE_STATUS: Final = (
    "static-synthetic-tessera-profile-implemented-runtime-evaluator-not-"
    "implemented"
)
_VALIDATION_SCOPE: Final = "static-profile-parameterization-only"
_ENCODING_ID: Final = "canonical-ascii-json-sort-keys-no-whitespace-v1"
_DIGEST_COMPUTATION_ID: Final = (
    "sha256-domain-nul-u64be-length-canonical-bytes-v1"
)

_V1_CORE_CONTRACT_SHA256: Final = (
    "387b45d6f4ae8485433b36b929ed4d3a7b146c61e5d12629d46e2a74aa4536b2"
)
_V1_CORE_PROFILE_INTERFACE_SHA256: Final = (
    "2698f51d7326cc89d7a90880a7feea59d4cab81b3fffd4d04bc995ae646464b2"
)
_V1_PROFILE_BYTE_COUNT: Final = 9695
_V1_PROFILE_PLAIN_SHA256: Final = (
    "6118c948d579a26ff5b94b9b97cdde288c71f5f394d77cb7c895a20587e9ec15"
)
_V1_PROFILE_SHA256: Final = (
    "786d01e7e4e22545d2ea39a938ef0e49c23348a6d451022e6b0bad932721fbf2"
)
_V1_RESULT_BYTE_COUNT: Final = 1729
_V1_RESULT_PLAIN_SHA256: Final = (
    "6bad58fb199eaf216bce32897f3a4a7398b5bec28e3e039ae97a2a13452925ad"
)
_V1_RESULT_SHA256: Final = (
    "71f7d2a0c2bfe0e1f782e52886be6b59ef8d40568f4199dff4ba998470f3cdd8"
)

_MAX_ARTIFACT_BYTES: Final = 4 * 1024 * 1024
_MAX_RESULT_BYTES: Final = 1024 * 1024
_MAX_JSON_DEPTH: Final = 32
_MAX_JSON_ITEMS: Final = 65536
_MAX_JSON_INTEGER_DIGITS: Final = 20
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")

_AUTHORITY_CLASS_IDS: Final = (
    "scenario-fixture-authority",
    "catalog-fixture-authority",
    "oracle-fixture-authority",
    "external-fixture-authority",
)
_PUBLIC_ERROR_IDS: Final = (
    "tessera-local-rule-failed",
    "tessera-fixture-unavailable",
    "tessera-fixture-decode-rejected",
    "tessera-fixture-derivation-mismatch",
    "tessera-upstream-rule-failed",
    "tessera-external-authority-unavailable",
    "tessera-static-mapping-unresolved",
)
_PUBLIC_ERROR_ROLE_SPECS: Final = (
    ("LOCAL_RULE_FAILED", "tessera-local-rule-failed"),
    ("RUNTIME_SOURCE_UNAVAILABLE", "tessera-fixture-unavailable"),
    ("PARSER_REJECTED", "tessera-fixture-decode-rejected"),
    ("DERIVATION_MISMATCH", "tessera-fixture-derivation-mismatch"),
    ("UPSTREAM_RULE_FAILED", "tessera-upstream-rule-failed"),
    (
        "EXTERNAL_AUTHORITY_UNAVAILABLE",
        "tessera-external-authority-unavailable",
    ),
    (
        "STATIC_MAPPING_UNRESOLVED",
        "tessera-static-mapping-unresolved",
    ),
)
_NONCLAIM_IDS: Final = (
    "real-domain-generality-established",
    "synthetic-profile-conformance-executed",
)

_ARTIFACT_DOMAIN_SPECS: Final = (
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
    ("fixture", "heterodiff.synthetic.tessera.fixture.v1"),
    (
        "list-order-contract",
        "heterodiff.synthetic.tessera.list-order-contract.v1",
    ),
)
_PROFILE_PARAMETER_SPECS: Final = (
    ("primary-program-purpose-id", "tessera-routing-conformance"),
    ("tessera-action-domain-slot", "tessera-action-id"),
    ("tessera-route-domain-slot", "tessera-route-id"),
    ("tessera-priority-domain-slot", "tessera-priority-id"),
)
_LOCATOR_SPECS: Final = (
    (
        "tessera-conformance-slot",
        "direct-bound-value",
        ("input-slot-id",),
        "exact-synthetic-input-slot-binding-v1",
    ),
    (
        "tessera-fixture-direct-value",
        "direct-bound-value",
        (
            "fixture-artifact-type-id",
            "fixture-identity-sha256",
            "mapping-id",
        ),
        "exact-fixture-identity-and-mapping-binding-v1",
    ),
    (
        "tessera-fixture-object-member",
        "bounded-artifact-path",
        (
            "fixture-artifact-type-id",
            "fixture-identity-sha256",
            "mapping-id",
            "ordered-path-segments",
        ),
        "exact-object-member-path-without-wildcards-v1",
    ),
    (
        "tessera-fixture-ordered-index",
        "ordered-index",
        (
            "expected-list-count",
            "list-index",
            "list-order-contract-sha256",
        ),
        "exact-index-count-and-order-contract-v1",
    ),
    (
        "tessera-fixture-composite-key",
        "composite-key",
        ("ordered-key-component-rows",),
        "one-to-four-typed-components-exactly-one-match-v1",
    ),
    (
        "tessera-sibling-resolved-value",
        "sibling-resolved-value",
        ("sibling-operand-id",),
        "exact-prior-resolved-sibling-operand-v1",
    ),
)


class TesseraPredicateProfileVerificationCode(str, Enum):
    """Closed failures for independent static profile verification."""

    INPUT_TYPE = "INPUT_TYPE"
    INPUT_RESOURCE = "INPUT_RESOURCE"
    JSON_INVALID = "JSON_INVALID"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    CANONICAL_MISMATCH = "CANONICAL_MISMATCH"
    ARTIFACT_PIN_MISMATCH = "ARTIFACT_PIN_MISMATCH"
    CONTRACT_MISMATCH = "CONTRACT_MISMATCH"
    RESULT_INVALID = "RESULT_INVALID"


_ERROR_MESSAGES: Final = {
    TesseraPredicateProfileVerificationCode.INPUT_TYPE: (
        "Tessera profile verifier input has an invalid exact type"
    ),
    TesseraPredicateProfileVerificationCode.INPUT_RESOURCE: (
        "Tessera profile verifier input exceeds its resource ceiling"
    ),
    TesseraPredicateProfileVerificationCode.JSON_INVALID: (
        "Tessera profile verifier JSON is invalid"
    ),
    TesseraPredicateProfileVerificationCode.SCHEMA_INVALID: (
        "Tessera profile verifier schema is invalid"
    ),
    TesseraPredicateProfileVerificationCode.CANONICAL_MISMATCH: (
        "Tessera profile verifier bytes are not canonical"
    ),
    TesseraPredicateProfileVerificationCode.ARTIFACT_PIN_MISMATCH: (
        "Tessera profile verifier artifact pin does not match"
    ),
    TesseraPredicateProfileVerificationCode.CONTRACT_MISMATCH: (
        "Tessera profile verifier reconstruction does not match"
    ),
    TesseraPredicateProfileVerificationCode.RESULT_INVALID: (
        "Tessera profile verification result is invalid"
    ),
}


class TesseraPredicateProfileVerificationError(ValueError):
    """One fixed-message profile-verification failure."""

    def __init__(
        self, code: TesseraPredicateProfileVerificationCode
    ) -> None:
        if type(code) is not TesseraPredicateProfileVerificationCode:
            raise TypeError("Tessera profile verification code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class _DuplicateKeyError(ValueError):
    pass


@dataclass(frozen=True)
class TesseraPredicateProfileVerificationPinsV1:
    """Externally supplied identity for the exact Tessera profile."""

    tessera_predicate_profile_contract_sha256: str


@dataclass(frozen=True)
class TesseraPredicateProfileVerificationResultV1:
    """Immutable result of static Tessera-profile verification."""

    artifact_type: str
    format_version: str
    verifier_id: str
    implementation_status_id: str
    verification_status_id: str
    tessera_predicate_profile_contract_byte_count: int
    tessera_predicate_profile_contract_plain_sha256: str
    tessera_predicate_profile_contract_sha256: str
    portable_core_contract_sha256: str
    portable_core_profile_interface_sha256: str
    artifact_domain_count: int
    authority_class_count: int
    interval_refinement_count: int
    locator_extension_count: int
    operator_specialization_count: int
    profile_parameter_count: int
    program_purpose_count: int
    public_error_count: int
    canonical_bytes_validated: bool
    exact_artifact_pin_validated: bool
    exact_core_contract_anchor_validated: bool
    exact_profile_interface_anchor_validated: bool
    independent_profile_reconstruction_validated: bool
    closed_profile_schema_validated: bool
    all_locator_primitive_bindings_declared: bool
    interval_refinement_declared: bool
    operator_specialization_declared: bool
    runtime_resolver_implemented: bool
    runtime_evaluator_implemented: bool
    synthetic_profile_conformance_executed: bool
    real_domain_generality_established: bool
    empirical_result_established: bool
    portable_typed_formula_evaluated: bool


def _fail(code: TesseraPredicateProfileVerificationCode) -> None:
    raise TesseraPredicateProfileVerificationError(code) from None


def _domain_sha256(domain: str, payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _canonical_json(value: object, *, maximum: int) -> bytes:
    try:
        result = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _fail(TesseraPredicateProfileVerificationCode.SCHEMA_INVALID)
    if not result or len(result) > maximum:
        _fail(TesseraPredicateProfileVerificationCode.INPUT_RESOURCE)
    return result


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
    if not digits or len(digits) > _MAX_JSON_INTEGER_DIGITS:
        raise ValueError("JSON integer exceeds fixed syntax bound")
    return int(value, 10)


def _node_count(value: object) -> int:
    count = 0
    stack = [value]
    while stack:
        current = stack.pop()
        count += 1
        if count > _MAX_JSON_ITEMS:
            return count
        if type(current) is dict:
            stack.extend(current.values())
        elif type(current) is list:
            stack.extend(current)
    return count


def _json_depth(value: object) -> int:
    deepest = 0
    stack = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        deepest = max(deepest, depth)
        if deepest > _MAX_JSON_DEPTH:
            return deepest
        if type(current) is dict:
            stack.extend(
                (item, depth + 1) for item in current.values()
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


def _parse_contract(value: bytes) -> dict:
    if type(value) is not bytes:
        _fail(TesseraPredicateProfileVerificationCode.INPUT_TYPE)
    if not value or len(value) > _MAX_ARTIFACT_BYTES:
        _fail(TesseraPredicateProfileVerificationCode.INPUT_RESOURCE)
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
        _DuplicateKeyError,
    ):
        _fail(TesseraPredicateProfileVerificationCode.JSON_INVALID)
    if type(decoded) is not dict:
        _fail(TesseraPredicateProfileVerificationCode.SCHEMA_INVALID)
    if (
        _json_depth(decoded) > _MAX_JSON_DEPTH
        or _node_count(decoded) > _MAX_JSON_ITEMS
    ):
        _fail(TesseraPredicateProfileVerificationCode.INPUT_RESOURCE)
    if (
        _canonical_json(decoded, maximum=_MAX_ARTIFACT_BYTES)
        != value
    ):
        _fail(TesseraPredicateProfileVerificationCode.CANONICAL_MISMATCH)
    return decoded


def _independent_artifact_domain_rows() -> list:
    result = []
    for role_id, artifact_type_id in _ARTIFACT_DOMAIN_SPECS:
        result.append(
            {
                "artifact_role_id": role_id,
                "artifact_type_id": artifact_type_id,
                "digest_domain_id": artifact_type_id,
                "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
            }
        )
    return result


def _independent_locator_rows() -> list:
    rows = []
    for kind_id, primitive_id, field_ids, rule_id in _LOCATOR_SPECS:
        rows.append(
            {
                "exact_configuration_field_ids": list(field_ids),
                "exact_empty_placeholder_field_ids": [],
                "locator_kind_id": kind_id,
                "locator_primitive_id": primitive_id,
                "validation_primitive_id": (
                    "profile-field-schema-and-locator-primitive-v1"
                ),
                "validation_rule_id": rule_id,
            }
        )
    return rows


def _independent_profile_field_schema_rows() -> list:
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


def tessera_predicate_profile_verifier_contract_tree() -> dict:
    """Independently reconstruct the exact static Tessera profile."""

    core = portable_predicate_language_core_verifier_contract_tree()
    interface = (
        portable_predicate_language_core_verifier_profile_interface_tree()
    )
    error_roles = [
        {
            "public_error_role_id": role_id,
            "public_error_id": error_id,
        }
        for role_id, error_id in _PUBLIC_ERROR_ROLE_SPECS
    ]
    parameters = [
        {
            "parameter_slot_id": slot_id,
            "parameter_value_id": value_id,
        }
        for slot_id, value_id in _PROFILE_PARAMETER_SPECS
    ]
    domains = _independent_artifact_domain_rows()
    locators = _independent_locator_rows()
    profile_fields = _independent_profile_field_schema_rows()
    purposes = [
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
        }
    ]
    specializations = [
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
    refinements = []
    anchors = []
    errors = list(_PUBLIC_ERROR_IDS)
    claims = {claim_id: False for claim_id in _NONCLAIM_IDS}
    tree = {
        "anchor_contract_rows": anchors,
        "artifact_domain_rows": domains,
        "artifact_type": _PROFILE_ARTIFACT_TYPE,
        "authority_class_ids": list(_AUTHORITY_CLASS_IDS),
        "core_contract_sha256": (
            portable_predicate_language_core_verifier_contract_sha256()
        ),
        "core_profile_interface_sha256": (
            portable_predicate_language_core_verifier_profile_interface_sha256()
        ),
        "digest_computation_id": core["digest_computation_id"],
        "encoding_id": core["encoding_id"],
        "fixed_counts": {
            "anchor_contract_count": len(anchors),
            "artifact_domain_count": len(domains),
            "authority_class_count": len(_AUTHORITY_CLASS_IDS),
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
        "implementation_status_id": _PROFILE_STATUS,
        "interval_refinement_rows": refinements,
        "locator_extension_rows": locators,
        "nonclaim_state": claims,
        "operator_specialization_rows": specializations,
        "profile_class_id": _PROFILE_CLASS_ID,
        "profile_id": _PROFILE_ID,
        "profile_interface_id": interface["profile_interface_id"],
        "profile_field_schema_rows": profile_fields,
        "profile_parameter_rows": parameters,
        "profile_verification_result_artifact_type": (
            _RESULT_ARTIFACT_TYPE
        ),
        "program_purpose_rows": purposes,
        "public_error_ids": errors,
        "public_error_role_rows": error_roles,
        "validation_scope_id": _VALIDATION_SCOPE,
    }
    try:
        validate_portable_predicate_profile_verifier_tree(tree)
    except PortablePredicateLanguageCoreVerificationError:
        _fail(TesseraPredicateProfileVerificationCode.CONTRACT_MISMATCH)
    return tree


def tessera_predicate_profile_verifier_contract_bytes() -> bytes:
    """Serialize the independently reconstructed profile."""

    return _canonical_json(
        tessera_predicate_profile_verifier_contract_tree(),
        maximum=_MAX_ARTIFACT_BYTES,
    )


def tessera_predicate_profile_verifier_contract_plain_sha256() -> str:
    """Return ordinary SHA-256 over the reconstructed profile."""

    return hashlib.sha256(
        tessera_predicate_profile_verifier_contract_bytes()
    ).hexdigest()


def tessera_predicate_profile_verifier_contract_sha256() -> str:
    """Return the length-bound domain-separated profile identity."""

    return _domain_sha256(
        _PROFILE_DIGEST_DOMAIN,
        tessera_predicate_profile_verifier_contract_bytes(),
    )


def _validated_pins(
    value: TesseraPredicateProfileVerificationPinsV1,
) -> TesseraPredicateProfileVerificationPinsV1:
    if type(value) is not TesseraPredicateProfileVerificationPinsV1:
        _fail(TesseraPredicateProfileVerificationCode.INPUT_TYPE)
    digest = value.tessera_predicate_profile_contract_sha256
    if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
        _fail(TesseraPredicateProfileVerificationCode.ARTIFACT_PIN_MISMATCH)
    return value


def _verification_result(
    contract_bytes: bytes, contract: dict
) -> TesseraPredicateProfileVerificationResultV1:
    counts = contract["fixed_counts"]
    if (
        contract["profile_verification_result_artifact_type"]
        != _RESULT_ARTIFACT_TYPE
    ):
        _fail(TesseraPredicateProfileVerificationCode.SCHEMA_INVALID)
    return TesseraPredicateProfileVerificationResultV1(
        artifact_type=contract[
            "profile_verification_result_artifact_type"
        ],
        format_version="1",
        verifier_id=_VERIFIER_ID,
        implementation_status_id=(
            TESSERA_PREDICATE_PROFILE_VERIFIER_IMPLEMENTATION_STATUS
        ),
        verification_status_id=(
            TESSERA_PREDICATE_PROFILE_VERIFICATION_STATUS
        ),
        tessera_predicate_profile_contract_byte_count=len(contract_bytes),
        tessera_predicate_profile_contract_plain_sha256=hashlib.sha256(
            contract_bytes
        ).hexdigest(),
        tessera_predicate_profile_contract_sha256=_domain_sha256(
            _PROFILE_DIGEST_DOMAIN, contract_bytes
        ),
        portable_core_contract_sha256=contract["core_contract_sha256"],
        portable_core_profile_interface_sha256=contract[
            "core_profile_interface_sha256"
        ],
        artifact_domain_count=counts["artifact_domain_count"],
        authority_class_count=counts["authority_class_count"],
        interval_refinement_count=counts["interval_refinement_count"],
        locator_extension_count=counts["locator_extension_count"],
        operator_specialization_count=counts[
            "operator_specialization_count"
        ],
        profile_parameter_count=counts["profile_parameter_count"],
        program_purpose_count=counts["program_purpose_count"],
        public_error_count=counts["public_error_count"],
        canonical_bytes_validated=True,
        exact_artifact_pin_validated=True,
        exact_core_contract_anchor_validated=True,
        exact_profile_interface_anchor_validated=True,
        independent_profile_reconstruction_validated=True,
        closed_profile_schema_validated=True,
        all_locator_primitive_bindings_declared=True,
        interval_refinement_declared=(
            counts["interval_refinement_count"] > 0
        ),
        operator_specialization_declared=True,
        runtime_resolver_implemented=False,
        runtime_evaluator_implemented=False,
        synthetic_profile_conformance_executed=False,
        real_domain_generality_established=False,
        empirical_result_established=False,
        portable_typed_formula_evaluated=False,
    )


def verify_tessera_predicate_profile_contract(
    contract_bytes: bytes,
    pins: TesseraPredicateProfileVerificationPinsV1,
) -> TesseraPredicateProfileVerificationResultV1:
    """Verify exact static profile bytes without evaluating a formula."""

    validated_pins = _validated_pins(pins)
    if type(contract_bytes) is not bytes:
        _fail(TesseraPredicateProfileVerificationCode.INPUT_TYPE)
    if not contract_bytes or len(contract_bytes) > _MAX_ARTIFACT_BYTES:
        _fail(TesseraPredicateProfileVerificationCode.INPUT_RESOURCE)
    contract_sha256 = _domain_sha256(
        _PROFILE_DIGEST_DOMAIN, contract_bytes
    )
    if (
        contract_sha256 != _V1_PROFILE_SHA256
        or contract_sha256
        != validated_pins.tessera_predicate_profile_contract_sha256
    ):
        _fail(TesseraPredicateProfileVerificationCode.ARTIFACT_PIN_MISMATCH)
    contract = _parse_contract(contract_bytes)
    expected = tessera_predicate_profile_verifier_contract_tree()
    try:
        validate_portable_predicate_profile_verifier_tree(contract)
    except PortablePredicateLanguageCoreVerificationError:
        _fail(TesseraPredicateProfileVerificationCode.SCHEMA_INVALID)
    if (
        not _same_exact(contract, expected)
        or contract_bytes
        != tessera_predicate_profile_verifier_contract_bytes()
        or len(contract_bytes) != _V1_PROFILE_BYTE_COUNT
        or hashlib.sha256(contract_bytes).hexdigest()
        != _V1_PROFILE_PLAIN_SHA256
        or contract["core_contract_sha256"]
        != _V1_CORE_CONTRACT_SHA256
        or contract["core_profile_interface_sha256"]
        != _V1_CORE_PROFILE_INTERFACE_SHA256
        or portable_predicate_language_core_verifier_contract_sha256()
        != _V1_CORE_CONTRACT_SHA256
        or portable_predicate_language_core_verifier_profile_interface_sha256()
        != _V1_CORE_PROFILE_INTERFACE_SHA256
    ):
        _fail(TesseraPredicateProfileVerificationCode.CONTRACT_MISMATCH)
    return _verification_result(contract_bytes, contract)


def _result_tree(
    value: TesseraPredicateProfileVerificationResultV1,
) -> dict:
    if type(value) is not TesseraPredicateProfileVerificationResultV1:
        _fail(TesseraPredicateProfileVerificationCode.RESULT_INVALID)
    result = {}
    expected_types = {
        "bool": bool,
        "int": int,
        "str": str,
        bool: bool,
        int: int,
        str: str,
    }
    for field_id, annotation in (
        TesseraPredicateProfileVerificationResultV1.__annotations__.items()
    ):
        expected_type = expected_types.get(annotation)
        field_value = getattr(value, field_id)
        if expected_type is None or type(field_value) is not expected_type:
            _fail(TesseraPredicateProfileVerificationCode.RESULT_INVALID)
        result[field_id] = field_value
    return result


def tessera_predicate_profile_verification_result_bytes(
    value: TesseraPredicateProfileVerificationResultV1,
) -> bytes:
    """Serialize a static verification result as canonical ASCII JSON."""

    return _canonical_json(_result_tree(value), maximum=_MAX_RESULT_BYTES)


def tessera_predicate_profile_verification_result_sha256(
    value: TesseraPredicateProfileVerificationResultV1,
) -> str:
    """Return the result's length-bound domain-separated identity."""

    return _domain_sha256(
        _RESULT_ARTIFACT_TYPE,
        tessera_predicate_profile_verification_result_bytes(value),
    )


def validate_tessera_predicate_profile_verification_result(
    value: TesseraPredicateProfileVerificationResultV1,
    contract_bytes: bytes,
    pins: TesseraPredicateProfileVerificationPinsV1,
) -> TesseraPredicateProfileVerificationResultV1:
    """Reject a forged or stale static profile-verification result."""

    expected = verify_tessera_predicate_profile_contract(
        contract_bytes, pins
    )
    if type(value) is not TesseraPredicateProfileVerificationResultV1:
        _fail(TesseraPredicateProfileVerificationCode.RESULT_INVALID)
    if not _same_exact(_result_tree(value), _result_tree(expected)):
        _fail(TesseraPredicateProfileVerificationCode.RESULT_INVALID)
    tessera_predicate_profile_verification_result_bytes(value)
    return value


def _validate_frozen_reconstruction() -> None:
    raw = tessera_predicate_profile_verifier_contract_bytes()
    tree = tessera_predicate_profile_verifier_contract_tree()
    core_tree = (
        portable_predicate_language_core_verifier_contract_tree()
    )
    resource_limits = core_tree["resource_limits"]
    interface = (
        portable_predicate_language_core_verifier_profile_interface_tree()
    )
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
    pins = TesseraPredicateProfileVerificationPinsV1(
        tessera_predicate_profile_contract_sha256=_V1_PROFILE_SHA256
    )
    result = verify_tessera_predicate_profile_contract(raw, pins)
    result_raw = tessera_predicate_profile_verification_result_bytes(result)
    if (
        raw != _canonical_json(tree, maximum=_MAX_ARTIFACT_BYTES)
        or len(raw) != _V1_PROFILE_BYTE_COUNT
        or tessera_predicate_profile_verifier_contract_plain_sha256()
        != _V1_PROFILE_PLAIN_SHA256
        or tessera_predicate_profile_verifier_contract_sha256()
        != _V1_PROFILE_SHA256
        or tree["core_contract_sha256"] != _V1_CORE_CONTRACT_SHA256
        or tree["core_profile_interface_sha256"]
        != _V1_CORE_PROFILE_INTERFACE_SHA256
        or tree["profile_verification_result_artifact_type"]
        != _RESULT_ARTIFACT_TYPE
        or tree["encoding_id"] != _ENCODING_ID
        or tree["digest_computation_id"] != _DIGEST_COMPUTATION_ID
        or resource_limits["artifact_bytes"] != _MAX_ARTIFACT_BYTES
        or resource_limits["json_depth"] != _MAX_JSON_DEPTH
        or resource_limits["json_items"] != _MAX_JSON_ITEMS
        or {
            row["locator_primitive_id"]
            for row in tree["locator_extension_rows"]
        }
        != set(interface["admitted_locator_primitive_ids"])
        or profile_fields != _independent_profile_field_schema_rows()
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
        or result.interval_refinement_declared
        != (tree["fixed_counts"]["interval_refinement_count"] > 0)
        or any(tree["nonclaim_state"].values())
        or b"linux" in raw.lower()
        or len(result_raw) != _V1_RESULT_BYTE_COUNT
        or hashlib.sha256(result_raw).hexdigest()
        != _V1_RESULT_PLAIN_SHA256
        or tessera_predicate_profile_verification_result_sha256(result)
        != _V1_RESULT_SHA256
    ):
        raise RuntimeError(
            _ERROR_MESSAGES[
                TesseraPredicateProfileVerificationCode.CONTRACT_MISMATCH
            ]
        )


_validate_frozen_reconstruction()


__all__ = [
    "TESSERA_PREDICATE_PROFILE_VERIFICATION_STATUS",
    "TESSERA_PREDICATE_PROFILE_VERIFIER_IMPLEMENTATION_STATUS",
    "TesseraPredicateProfileVerificationCode",
    "TesseraPredicateProfileVerificationError",
    "TesseraPredicateProfileVerificationPinsV1",
    "TesseraPredicateProfileVerificationResultV1",
    "tessera_predicate_profile_verification_result_bytes",
    "tessera_predicate_profile_verification_result_sha256",
    "tessera_predicate_profile_verifier_contract_bytes",
    "tessera_predicate_profile_verifier_contract_plain_sha256",
    "tessera_predicate_profile_verifier_contract_sha256",
    "tessera_predicate_profile_verifier_contract_tree",
    "validate_tessera_predicate_profile_verification_result",
    "verify_tessera_predicate_profile_contract",
]
