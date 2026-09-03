"""Static composition and predecessor-projection receipts.

The generic compositor combines the frozen portable semantic core with any
profile admitted by the core's closed profile interface.  It has no
profile-identifier branches.

The Linux predecessor helper is deliberately weaker than a reimplementation
or a behavioral-equivalence proof.  It accepts the predecessor bytes and
their expected KAT from the caller, parses those bytes without importing the
monolithic predecessor module, and checks a named collection of static
registry projections.  No runtime program is parsed and no predicate is
evaluated.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Final

from .adapter_portable_predicate_language_core import (
    PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_ARTIFACT_TYPE,
    PortablePredicateLanguageCoreError,
    parse_portable_predicate_language_core_contract,
    portable_predicate_language_core_contract_sha256,
    portable_predicate_language_core_profile_interface_sha256,
    validate_portable_predicate_profile_tree,
)


PORTABLE_PREDICATE_LANGUAGE_COMPOSITION_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-composition-contract.v1"
)
PORTABLE_PREDICATE_LANGUAGE_COMPOSITION_CONTRACT_DIGEST_DOMAIN: Final = (
    PORTABLE_PREDICATE_LANGUAGE_COMPOSITION_CONTRACT_ARTIFACT_TYPE
)
PORTABLE_PREDICATE_LANGUAGE_COMPOSED_DESCRIPTOR_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-composed-descriptor.v1"
)
PORTABLE_PREDICATE_LANGUAGE_PREDECESSOR_PROJECTION_RESULT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-predecessor-projection-"
    "result.v1"
)
LINUX_CONFINEMENT_PREDECESSOR_ARTIFACT_TYPE: Final = (
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
_COMPOSITOR_ID: Final = (
    "heterodiff.adapter.portable-predicate-language-static-compositor.v1"
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

_V1_COMPOSITION_CONTRACT_BYTE_COUNT: Final = 3536
_V1_COMPOSITION_CONTRACT_PLAIN_SHA256: Final = (
    "99c37e0b78cf0efcfca08e40f8eea775650719885e8716d48cbf5740e7692926"
)
_V1_COMPOSITION_CONTRACT_SHA256: Final = (
    "41bd731707390d30517f80fd4440e377d00f31898bde0f465dddbd3f315429d4"
)
_V1_CORE_BYTE_COUNT: Final = 57674
_V1_CORE_PLAIN_SHA256: Final = (
    "b13e1d349c08449096bd901e46087bbcc44181365354b553e6ecd89172864dc2"
)
_V1_CORE_SHA256: Final = (
    "387b45d6f4ae8485433b36b929ed4d3a7b146c61e5d12629d46e2a74aa4536b2"
)
_V1_LINUX_PROFILE_BYTE_COUNT: Final = 15992
_V1_LINUX_PROFILE_PLAIN_SHA256: Final = (
    "82a36c2ca07d25afc4cc44e2fa6ae1b2e481b77fb96bc56396bd6e54fb5be658"
)
_V1_LINUX_PROFILE_SHA256: Final = (
    "31204b1598e203e920fb8b1349116bc27a5162a34fe50ec5112ef957cb9bbdd7"
)
_V1_PREDECESSOR_BYTE_COUNT: Final = 59865
_V1_PREDECESSOR_PLAIN_SHA256: Final = (
    "f019fccbb0fc05689bba21e57fa9e922735034865c01105ea4ab595cbfd93463"
)
_V1_PREDECESSOR_SHA256: Final = (
    "6cee841ff42b044c8a0fd25ca72e6a360079d25022e1022203991fb61667e8ee"
)

_LEGACY_TOP_LEVEL_FIELDS: Final = (
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

_CORE_PROJECTION_COMPONENT_IDS: Final = (
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

_PROFILE_PROJECTION_COMPONENT_IDS: Final = (
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

_LINUX_INTERVAL_LEGACY_TYPE_RULE: Final = (
    "prior-u64-endpoint-one-nominal-clock-run-binding-v1"
)
_CORE_INTERVAL_TYPE_RULE: Final = (
    "prior-nominal-u64-endpoint-and-closed-start-not-after-end-v1"
)
_LINUX_INTERVAL_LEGACY_TRUTH_RULE: Final = (
    "one-nominal-u64-interval-sequence-every-start-less-or-equal-end-by-type-"
    "validation-and-program-mode-adjacency-logical-truth-v1"
)
_CORE_INTERVAL_TRUTH_RULE: Final = (
    "closed-nominal-u64-intervals-and-program-mode-adjacency-v1"
)
_LINUX_STATUS_LEGACY_SOURCE_RULE: Final = (
    "second-approved-outcome-sequence-value-source-program-literal-and-"
    "canonical-unique-nonempty-at-program-validation-v1"
)
_LINUX_STATUS_LEGACY_TRUTH_RULE: Final = (
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


class PortablePredicateLanguageCompositionCode(str, Enum):
    """Closed failures for static composition and projection."""

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


_ERROR_MESSAGES: Final = {
    PortablePredicateLanguageCompositionCode.INPUT_TYPE: (
        "Portable predicate composition input has an invalid exact type"
    ),
    PortablePredicateLanguageCompositionCode.INPUT_RESOURCE: (
        "Portable predicate composition input exceeds its resource ceiling"
    ),
    PortablePredicateLanguageCompositionCode.JSON_INVALID: (
        "Portable predicate composition JSON is invalid"
    ),
    PortablePredicateLanguageCompositionCode.CORE_INVALID: (
        "Portable predicate semantic core is invalid"
    ),
    PortablePredicateLanguageCompositionCode.PROFILE_INVALID: (
        "Portable predicate profile is invalid"
    ),
    PortablePredicateLanguageCompositionCode.CANONICAL_MISMATCH: (
        "Portable predicate composition bytes are not canonical"
    ),
    PortablePredicateLanguageCompositionCode.ARTIFACT_PIN_MISMATCH: (
        "Portable predicate composition artifact pin does not match"
    ),
    PortablePredicateLanguageCompositionCode.PREDECESSOR_SCHEMA_INVALID: (
        "Linux predicate predecessor schema is invalid"
    ),
    PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH: (
        "Linux predicate predecessor static projection does not correspond"
    ),
    PortablePredicateLanguageCompositionCode.RESULT_INVALID: (
        "Portable predicate predecessor projection result is invalid"
    ),
    PortablePredicateLanguageCompositionCode.CONTRACT_DRIFT: (
        "Portable predicate composition contract drifted"
    ),
}


class PortablePredicateLanguageCompositionError(ValueError):
    """One stable failure from the static compositor."""

    def __init__(self, code: PortablePredicateLanguageCompositionCode):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


class _DuplicateKeyError(ValueError):
    pass


def _fail(code: PortablePredicateLanguageCompositionCode) -> None:
    raise PortablePredicateLanguageCompositionError(code)


def _domain_sha256(domain: str, payload: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


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
        _fail(PortablePredicateLanguageCompositionCode.RESULT_INVALID)
    if len(encoded) > _MAXIMUM_ARTIFACT_BYTES:
        _fail(PortablePredicateLanguageCompositionCode.INPUT_RESOURCE)
    return encoded


def _object_without_duplicates(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise ValueError


def _reject_float(_: str) -> None:
    raise ValueError


def _bounded_integer(value: str) -> int:
    if len(value.lstrip("-")) > _MAXIMUM_JSON_INTEGER_DIGITS:
        raise ValueError
    return int(value)


def _node_count(value: object) -> int:
    count = 0
    stack = [value]
    while stack:
        current = stack.pop()
        count += 1
        if count > _MAXIMUM_JSON_ITEMS:
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
        if maximum > _MAXIMUM_JSON_DEPTH:
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
        return set(left) == set(right) and all(
            _same_exact(left[key], right[key]) for key in left
        )
    if type(left) is list:
        return len(left) == len(right) and all(
            _same_exact(a, b) for a, b in zip(left, right)
        )
    return left == right


def _strict_json_bytes(
    value: bytes,
    *,
    invalid_code: PortablePredicateLanguageCompositionCode,
) -> dict:
    if type(value) is not bytes:
        _fail(PortablePredicateLanguageCompositionCode.INPUT_TYPE)
    if not value or len(value) > _MAXIMUM_ARTIFACT_BYTES:
        _fail(PortablePredicateLanguageCompositionCode.INPUT_RESOURCE)
    try:
        decoded = json.loads(
            value.decode("ascii", "strict"),
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
            parse_int=_bounded_integer,
        )
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _fail(PortablePredicateLanguageCompositionCode.JSON_INVALID)
    if (
        type(decoded) is not dict
        or _json_depth(decoded) > _MAXIMUM_JSON_DEPTH
        or _node_count(decoded) > _MAXIMUM_JSON_ITEMS
    ):
        _fail(invalid_code)
    if value != _canonical_json(decoded):
        _fail(PortablePredicateLanguageCompositionCode.CANONICAL_MISMATCH)
    return decoded


def portable_predicate_language_composition_contract_tree() -> dict:
    """Return the fixed, claim-bounded composition contract."""

    return {
        "artifact_type": (
            PORTABLE_PREDICATE_LANGUAGE_COMPOSITION_CONTRACT_ARTIFACT_TYPE
        ),
        "caller_supplied_profile_selection_pin_required": True,
        "caller_supplied_predecessor_kat_required": True,
        "core_projection_component_ids": list(
            _CORE_PROJECTION_COMPONENT_IDS
        ),
        "digest_computation_id": _DIGEST_COMPUTATION_ID,
        "encoding_id": _ENCODING_ID,
        "fixed_counts": {
            "core_projection_component_count": len(
                _CORE_PROJECTION_COMPONENT_IDS
            ),
            "profile_projection_component_count": len(
                _PROFILE_PROJECTION_COMPONENT_IDS
            ),
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
        "profile_projection_component_ids": list(
            _PROFILE_PROJECTION_COMPONENT_IDS
        ),
        "specialization_mapping_rows": [
            {
                "core_primitive_id": "interval-order",
                "core_rule_id": _CORE_INTERVAL_TRUTH_RULE,
                "legacy_exposed_id": "interval-order",
                "legacy_rule_id": _LINUX_INTERVAL_LEGACY_TRUTH_RULE,
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
                "legacy_rule_id": _LINUX_STATUS_LEGACY_TRUTH_RULE,
                "mapping_scope_id": (
                    "static-registry-correspondence-not-behavioral-proof"
                ),
            },
        ],
        "validation_scope_id": _VALIDATION_SCOPE,
    }


def portable_predicate_language_composition_contract_bytes() -> bytes:
    return _canonical_json(
        portable_predicate_language_composition_contract_tree()
    )


def portable_predicate_language_composition_contract_plain_sha256() -> str:
    return hashlib.sha256(
        portable_predicate_language_composition_contract_bytes()
    ).hexdigest()


def portable_predicate_language_composition_contract_sha256() -> str:
    return _domain_sha256(
        PORTABLE_PREDICATE_LANGUAGE_COMPOSITION_CONTRACT_DIGEST_DOMAIN,
        portable_predicate_language_composition_contract_bytes(),
    )


def parse_portable_predicate_language_composition_contract(
    value: bytes,
) -> dict:
    decoded = _strict_json_bytes(
        value,
        invalid_code=PortablePredicateLanguageCompositionCode.CORE_INVALID,
    )
    expected = portable_predicate_language_composition_contract_tree()
    if not _same_exact(decoded, expected):
        _fail(PortablePredicateLanguageCompositionCode.CORE_INVALID)
    return expected


def _parse_core(value: bytes) -> dict:
    try:
        return parse_portable_predicate_language_core_contract(value)
    except PortablePredicateLanguageCoreError:
        _fail(PortablePredicateLanguageCompositionCode.CORE_INVALID)


def _parse_profile(value: bytes) -> dict:
    tree = _strict_json_bytes(
        value,
        invalid_code=PortablePredicateLanguageCompositionCode.PROFILE_INVALID,
    )
    try:
        validated = validate_portable_predicate_profile_tree(tree)
    except PortablePredicateLanguageCoreError:
        _fail(PortablePredicateLanguageCompositionCode.PROFILE_INVALID)
    if value != _canonical_json(validated):
        _fail(PortablePredicateLanguageCompositionCode.CANONICAL_MISMATCH)
    return validated


def _validate_profile_selection_pin(
    profile_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> None:
    """Validate the caller's exact profile selection before profile parsing."""

    if (
        type(profile_bytes) is not bytes
        or type(expected_profile_artifact_type) is not str
        or type(expected_profile_contract_sha256) is not str
    ):
        _fail(PortablePredicateLanguageCompositionCode.INPUT_TYPE)
    if (
        not profile_bytes
        or len(profile_bytes) > _MAXIMUM_ARTIFACT_BYTES
    ):
        _fail(PortablePredicateLanguageCompositionCode.INPUT_RESOURCE)
    if (
        len(expected_profile_artifact_type)
        > _MAXIMUM_PROFILE_ARTIFACT_TYPE_BYTES
    ):
        _fail(PortablePredicateLanguageCompositionCode.INPUT_RESOURCE)
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
        _fail(PortablePredicateLanguageCompositionCode.ARTIFACT_PIN_MISMATCH)


def _validate_parsed_profile_selection(
    profile: dict,
    profile_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> None:
    """Recheck the selection against the parsed profile's committed type."""

    if (
        profile.get("artifact_type") != expected_profile_artifact_type
        or _domain_sha256(
            profile["artifact_type"],
            profile_bytes,
        )
        != expected_profile_contract_sha256
    ):
        _fail(PortablePredicateLanguageCompositionCode.ARTIFACT_PIN_MISMATCH)


def _ordered_ids(rows: list, field: str) -> list:
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
        PORTABLE_PREDICATE_LANGUAGE_COMPOSITION_CONTRACT_ARTIFACT_TYPE,
        PORTABLE_PREDICATE_LANGUAGE_COMPOSED_DESCRIPTOR_ARTIFACT_TYPE,
        PORTABLE_PREDICATE_LANGUAGE_PREDECESSOR_PROJECTION_RESULT_ARTIFACT_TYPE,
        *additional_metadata_artifact_types,
    }
    if (
        len(layer_metadata_types) != 3 + len(
            additional_metadata_artifact_types
        )
        or profile_surface_types.intersection(layer_metadata_types)
    ):
        _fail(PortablePredicateLanguageCompositionCode.PROFILE_INVALID)


def portable_predicate_language_composed_descriptor_tree(
    core_bytes: bytes,
    profile_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> dict:
    """Compose core and profile without dispatching on ``profile_id``."""

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
        != _domain_sha256(
            PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_ARTIFACT_TYPE,
            core_bytes,
        )
        or profile["core_profile_interface_sha256"]
        != portable_predicate_language_core_profile_interface_sha256()
        or profile["profile_interface_id"]
        != core["profile_interface"]["profile_interface_id"]
    ):
        _fail(PortablePredicateLanguageCompositionCode.PROFILE_INVALID)

    core_claims = core["nonclaim_state"]
    profile_claims = profile["nonclaim_state"]
    if set(core_claims).intersection(profile_claims):
        _fail(PortablePredicateLanguageCompositionCode.PROFILE_INVALID)
    claims = dict(core_claims)
    claims.update(profile_claims)
    if any(type(value) is not bool or value for value in claims.values()):
        _fail(PortablePredicateLanguageCompositionCode.PROFILE_INVALID)

    return {
        "artifact_type": (
            PORTABLE_PREDICATE_LANGUAGE_COMPOSED_DESCRIPTOR_ARTIFACT_TYPE
        ),
        "authority_class_ids": list(profile["authority_class_ids"]),
        "constructor_ids": _ordered_ids(
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
        "interval_refinement_ids": _ordered_ids(
            profile["interval_refinement_rows"],
            "exposed_refinement_id",
        ),
        "locator_kind_ids": _ordered_ids(
            profile["locator_extension_rows"],
            "locator_kind_id",
        ),
        "nonclaim_state": claims,
        "operator_ids": _ordered_ids(
            core["operator_contract"]["operator_rows"],
            "operator_id",
        ),
        "operator_specialization_ids": _ordered_ids(
            profile["operator_specialization_rows"],
            "exposed_operator_id",
        ),
        "profile_class_id": profile["profile_class_id"],
        "profile_artifact_type": profile["artifact_type"],
        "profile_contract_sha256": expected_profile_contract_sha256,
        "profile_field_ids": _ordered_ids(
            profile["profile_field_schema_rows"],
            "field_id",
        ),
        "profile_verification_result_artifact_type": profile[
            "profile_verification_result_artifact_type"
        ],
        "profile_id": profile["profile_id"],
        "profile_interface_id": profile["profile_interface_id"],
        "program_purpose_ids": _ordered_ids(
            profile["program_purpose_rows"],
            "program_purpose_id",
        ),
        "program_purpose_relation_ids": [
            relation["relation_id"]
            for purpose in profile["program_purpose_rows"]
            for relation in purpose["purpose_relation_rows"]
        ],
        "public_error_ids": list(profile["public_error_ids"]),
        "type_kind_ids": _ordered_ids(
            core["type_contract"]["type_kind_schema_rows"],
            "type_kind_id",
        ),
    }


def portable_predicate_language_composed_descriptor_bytes(
    core_bytes: bytes,
    profile_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> bytes:
    return _canonical_json(
        portable_predicate_language_composed_descriptor_tree(
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


def portable_predicate_language_composed_descriptor_sha256(
    core_bytes: bytes,
    profile_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> str:
    return _domain_sha256(
        PORTABLE_PREDICATE_LANGUAGE_COMPOSED_DESCRIPTOR_ARTIFACT_TYPE,
        portable_predicate_language_composed_descriptor_bytes(
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
class PortablePredicateLanguagePredecessorProjectionPinsV1:
    """Caller-supplied exact identities for all three input artifacts."""

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
class PortablePredicateLanguagePredecessorProjectionResultV1:
    """Static correspondence receipt; never a behavioral proof."""

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
    value: PortablePredicateLanguagePredecessorProjectionPinsV1,
) -> PortablePredicateLanguagePredecessorProjectionPinsV1:
    if type(value) is not PortablePredicateLanguagePredecessorProjectionPinsV1:
        _fail(PortablePredicateLanguageCompositionCode.INPUT_TYPE)
    counts = (
        value.core_contract_byte_count,
        value.profile_contract_byte_count,
        value.predecessor_contract_byte_count,
    )
    digests = (
        value.core_contract_plain_sha256,
        value.core_contract_sha256,
        value.profile_contract_plain_sha256,
        value.profile_contract_sha256,
        value.predecessor_contract_plain_sha256,
        value.predecessor_contract_sha256,
    )
    if (
        any(type(count) is not int or count <= 0 for count in counts)
        or any(not _valid_digest(digest) for digest in digests)
        or type(value.predecessor_contract_artifact_type) is not str
        or value.predecessor_contract_artifact_type
        != LINUX_CONFINEMENT_PREDECESSOR_ARTIFACT_TYPE
        or value.core_contract_byte_count != _V1_CORE_BYTE_COUNT
        or value.core_contract_plain_sha256 != _V1_CORE_PLAIN_SHA256
        or value.core_contract_sha256 != _V1_CORE_SHA256
        or value.profile_contract_byte_count != _V1_LINUX_PROFILE_BYTE_COUNT
        or value.profile_contract_plain_sha256
        != _V1_LINUX_PROFILE_PLAIN_SHA256
        or value.profile_contract_sha256 != _V1_LINUX_PROFILE_SHA256
        or value.predecessor_contract_byte_count
        != _V1_PREDECESSOR_BYTE_COUNT
        or value.predecessor_contract_plain_sha256
        != _V1_PREDECESSOR_PLAIN_SHA256
        or value.predecessor_contract_sha256 != _V1_PREDECESSOR_SHA256
    ):
        _fail(PortablePredicateLanguageCompositionCode.ARTIFACT_PIN_MISMATCH)
    return value


def _check_artifact_pin(
    raw: bytes,
    *,
    artifact_type: str,
    byte_count: int,
    plain_sha256: str,
    domain_sha256: str,
) -> None:
    if (
        len(raw) != byte_count
        or hashlib.sha256(raw).hexdigest() != plain_sha256
        or _domain_sha256(artifact_type, raw) != domain_sha256
    ):
        _fail(PortablePredicateLanguageCompositionCode.ARTIFACT_PIN_MISMATCH)


def _legacy_tree(value: bytes) -> dict:
    tree = _strict_json_bytes(
        value,
        invalid_code=(
            PortablePredicateLanguageCompositionCode
            .PREDECESSOR_SCHEMA_INVALID
        ),
    )
    if (
        set(tree) != set(_LEGACY_TOP_LEVEL_FIELDS)
        or tree.get("artifact_type")
        != LINUX_CONFINEMENT_PREDECESSOR_ARTIFACT_TYPE
        or tree.get("format_version") != "1"
        or type(tree.get("nonclaim_state")) is not dict
        or any(
            type(item) is not bool or item
            for item in tree["nonclaim_state"].values()
        )
    ):
        _fail(
            PortablePredicateLanguageCompositionCode
            .PREDECESSOR_SCHEMA_INVALID
        )
    return tree


def _normalized_legacy_type_rows(
    legacy: dict,
    profile: dict,
) -> list:
    rows = deepcopy(legacy["type_contract"]["type_kind_schema_rows"])
    refinements = profile["interval_refinement_rows"]
    if len(refinements) != 1:
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
    interval = next(
        (
            row
            for row in rows
            if row.get("type_kind_id") == "u64-interval-sequence"
        ),
        None,
    )
    refinement = refinements[0]
    if (
        type(interval) is not dict
        or interval.get("validation_rule_id")
        != _LINUX_INTERVAL_LEGACY_TYPE_RULE
        or refinement.get("validation_rule_id")
        != _LINUX_INTERVAL_LEGACY_TYPE_RULE
        or refinement.get("refinement_primitive_id")
        != "nominal-u64-endpoint-binding"
    ):
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
    interval["validation_rule_id"] = _CORE_INTERVAL_TYPE_RULE
    return rows


def _normalized_legacy_constructor_rows(legacy: dict) -> list:
    rows = deepcopy(legacy["constructor_contract"]["constructor_rows"])
    for row in rows:
        if (
            type(row) is not dict
            or "native_or_external_parsing_admitted" not in row
            or "external_parsing_admitted" in row
        ):
            _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
        row["external_parsing_admitted"] = row.pop(
            "native_or_external_parsing_admitted"
        )
    return rows


def _normalized_legacy_constructor_failure_rows(legacy: dict) -> list:
    rows = deepcopy(
        legacy["constructor_contract"]["constructor_failure_mapping_rows"]
    )
    for row in rows:
        if (
            type(row) is not dict
            or set(row)
            != {"failure_rule_id", "internal_condition_id"}
        ):
            _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
        row["public_error_role_id"] = "LOCAL_RULE_FAILED"
    return _sorted_rows(rows, "failure_rule_id")


def _normalized_legacy_fault_precedence_rows(legacy: dict) -> list:
    rows = deepcopy(legacy["operator_contract"]["fault_precedence_rows"])
    for row in rows:
        if (
            type(row) is not dict
            or set(row) != {"selected_disposition_id", "precedence_rank"}
        ):
            _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
        row["disposition_rank"] = row.pop("precedence_rank")
    return rows


def _row_without(value: dict, excluded: set) -> dict:
    return {key: item for key, item in value.items() if key not in excluded}


def _normalized_legacy_operator_rows(
    legacy: dict,
    core: dict,
    profile: dict,
) -> list:
    legacy_rows = legacy["operator_contract"]["operator_rows"]
    core_rows = core["operator_contract"]["operator_rows"]
    if (
        type(legacy_rows) is not list
        or len(legacy_rows) != len(core_rows)
    ):
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
    specializations = profile["operator_specialization_rows"]
    if len(specializations) != 1:
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
    specialization = specializations[0]
    normalized = []
    for legacy_row, core_row in zip(legacy_rows, core_rows):
        if legacy_row.get("operator_id") == "status-is-approved":
            varying = {
                "operator_id",
                "operand_source_rule_id",
                "type_and_truth_rule_id",
            }
            if (
                specialization.get("exposed_operator_id")
                != legacy_row.get("operator_id")
                or specialization.get("primitive_id")
                != core_row.get("operator_id")
                or specialization.get("operand_source_rule_id")
                != core_row.get("operand_source_rule_id")
                or specialization.get("type_and_truth_rule_id")
                != core_row.get("type_and_truth_rule_id")
                or legacy_row.get("operand_source_rule_id")
                != _LINUX_STATUS_LEGACY_SOURCE_RULE
                or legacy_row.get("type_and_truth_rule_id")
                != _LINUX_STATUS_LEGACY_TRUTH_RULE
                or not _same_exact(
                    _row_without(legacy_row, varying),
                    _row_without(core_row, varying),
                )
            ):
                _fail(
                    PortablePredicateLanguageCompositionCode
                    .PROJECTION_MISMATCH
                )
            normalized.append(deepcopy(core_row))
        elif legacy_row.get("operator_id") == "interval-order":
            if (
                core_row.get("operator_id") != "interval-order"
                or legacy_row.get("type_and_truth_rule_id")
                != _LINUX_INTERVAL_LEGACY_TRUTH_RULE
                or core_row.get("type_and_truth_rule_id")
                != _CORE_INTERVAL_TRUTH_RULE
                or not _same_exact(
                    _row_without(
                        legacy_row,
                        {"type_and_truth_rule_id"},
                    ),
                    _row_without(core_row, {"type_and_truth_rule_id"}),
                )
            ):
                _fail(
                    PortablePredicateLanguageCompositionCode
                    .PROJECTION_MISMATCH
                )
            normalized.append(deepcopy(core_row))
        else:
            normalized.append(deepcopy(legacy_row))
    return normalized


def _normalized_legacy_input_state_rows(
    legacy: dict,
    profile: dict,
) -> list:
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
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
    seen_state_ids = set()
    for row in rows:
        if (
            type(row) is not dict
            or row.get("internal_condition_id") != ""
            or "executed_error_id" not in row
            or row.get("input_state_id") not in expected_by_state
            or row.get("input_state_id") in seen_state_ids
        ):
            _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
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
            _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
        row["public_error_role_id"] = expected_role_id
    if seen_state_ids != set(expected_by_state):
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
    return rows


def _sorted_rows(rows: object, field: str) -> list:
    if type(rows) is not list or any(type(row) is not dict for row in rows):
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
    try:
        return sorted(deepcopy(rows), key=lambda row: row[field])
    except (KeyError, TypeError):
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)


def _validate_core_projection(
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
            _normalized_legacy_type_rows(legacy, profile),
            core["type_contract"]["type_kind_schema_rows"],
        ),
        (
            legacy["type_contract"]["value_encoding_rows"],
            core["type_contract"]["value_encoding_rows"],
        ),
        (
            _normalized_legacy_constructor_rows(legacy),
            core["constructor_contract"]["constructor_rows"],
        ),
        (
            _normalized_legacy_constructor_failure_rows(legacy),
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
            _normalized_legacy_operator_rows(legacy, core, profile),
            core["operator_contract"]["operator_rows"],
        ),
        (
            legacy["resolution_contract"]["resolution_requirement_rows"],
            core["resolution_contract"]["resolution_requirement_rows"],
        ),
        (
            _normalized_legacy_input_state_rows(legacy, profile),
            core["resolution_contract"]["input_state_rows"],
        ),
        (
            legacy["selector_contract"]["path_segment_schema_rows"],
            core["selector_contract"]["path_segment_schema_rows"],
        ),
        (
            _normalized_legacy_fault_precedence_rows(legacy),
            core["operator_contract"]["fault_precedence_rows"],
        ),
    )
    if len(comparisons) != len(_CORE_PROJECTION_COMPONENT_IDS) or any(
        not _same_exact(left, right) for left, right in comparisons
    ):
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)


def _validate_profile_projection(
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
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)

    legacy_family_by_type = {
        row["artifact_type_id"]: row
        for row in legacy["artifact_family_rows"]
    }
    purpose_rows = legacy["program_contract"]["program_purpose_rows"]
    legacy_linux_purpose = next(
        (
            row
            for row in purpose_rows
            if row.get("program_purpose_id")
            == profile["profile_parameter_rows"][0]["parameter_value_id"]
        ),
        None,
    )
    if type(legacy_linux_purpose) is not dict:
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
    binding_by_type = {
        row["fixed_artifact_type_id"]: row
        for row in legacy_linux_purpose["binding_identity_rule_rows"]
    }
    for row in profile["artifact_domain_rows"]:
        artifact_type = row["artifact_type_id"]
        if artifact_type in legacy_family_by_type:
            old = legacy_family_by_type[artifact_type]
            valid = (
                row["digest_domain_id"] == old["digest_domain_id"]
                and row["identity_semantics_id"]
                == old["artifact_identity_semantics_id"]
            )
        elif artifact_type in binding_by_type:
            old = binding_by_type[artifact_type]
            valid = (
                row["digest_domain_id"] == artifact_type
                and row["identity_semantics_id"]
                == old["required_identity_semantics_id"]
            )
        else:
            valid = False
        if not valid:
            _fail(
                PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH
            )

    if (
        not _same_exact(
            profile["authority_class_ids"],
            legacy["resolution_contract"]["authority_class_ids"],
        )
        or not _same_exact(
            profile["public_error_ids"],
            legacy["executed_layer_error_ids"],
        )
    ):
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)

    # Role totality is checked by the core profile validator; here each
    # nonempty predecessor input-state error must resolve through that map.
    _normalized_legacy_input_state_rows(legacy, profile)

    legacy_value_schema_by_field = {}
    for schema_row in legacy["field_value_schema_rows"]:
        field_ids = schema_row.get("field_ids")
        value_schema_id = schema_row.get("value_schema_id")
        if (
            type(field_ids) is not list
            or type(value_schema_id) is not str
            or any(type(field_id) is not str for field_id in field_ids)
            or any(
                field_id in legacy_value_schema_by_field
                for field_id in field_ids
            )
        ):
            _fail(
                PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH
            )
        for field_id in field_ids:
            legacy_value_schema_by_field[field_id] = value_schema_id
    if any(
        type(row) is not dict
        or legacy_value_schema_by_field.get(row.get("field_id"))
        != row.get("value_schema_id")
        for row in profile["profile_field_schema_rows"]
    ):
        _fail(
            PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH
        )

    parameter_by_slot = {
        row["parameter_slot_id"]: row["parameter_value_id"]
        for row in profile["profile_parameter_rows"]
    }
    components = legacy["operator_contract"]["source_operation_outcome_v1"][
        "ordered_component_rows"
    ]
    if (
        parameter_by_slot.get("primary-program-purpose-id")
        != legacy_linux_purpose["program_purpose_id"]
        or [
            parameter_by_slot.get(f"outcome-component-{index}-domain-id")
            for index in range(4)
        ]
        != [row.get("token_domain_id") for row in components]
        or parameter_by_slot.get("interval-endpoint-unit-id")
        != "linux-clock-run-binding"
    ):
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)

    legacy_locator_rows = [
        row
        for row in legacy["selector_contract"][
            "executable_locator_schema_rows"
        ]
        if row.get("program_purpose_admission_ids")
        == [legacy_linux_purpose["program_purpose_id"]]
    ]
    if not _same_exact(
        [
            row["locator_kind_id"]
            for row in profile["locator_extension_rows"]
        ],
        [row.get("locator_kind_id") for row in legacy_locator_rows],
    ):
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
    legacy_locator_by_id = {
        row["locator_kind_id"]: row for row in legacy_locator_rows
    }
    for row in profile["locator_extension_rows"]:
        old = legacy_locator_by_id.get(row["locator_kind_id"])
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
                PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH
            )

    profile_purposes = profile["program_purpose_rows"]
    if (
        len(profile_purposes) != 1
        or profile_purposes[0]["program_purpose_id"]
        != legacy_linux_purpose["program_purpose_id"]
        or not _same_exact(
            profile_purposes[0]["exact_binding_field_ids"],
            legacy_linux_purpose["exact_binding_field_ids"],
        )
        or profile_purposes[0]["validation_rule_id"]
        != legacy_linux_purpose["binding_validation_rule_id"]
    ):
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)
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
    legacy_program_family = legacy_family_by_type.get(program_type)
    if (
        not _same_exact(
            profile_purposes[0]["purpose_relation_rows"],
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
        _fail(PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH)

    # These helpers perform the exact legacy/core/profile specialization
    # correspondence checks.
    _normalized_legacy_operator_rows(legacy, core, profile)
    _normalized_legacy_type_rows(legacy, profile)

    for claim_id, value in profile["nonclaim_state"].items():
        if (
            type(value) is not bool
            or value
            or claim_id not in legacy["nonclaim_state"]
            or legacy["nonclaim_state"][claim_id] is not False
        ):
            _fail(
                PortablePredicateLanguageCompositionCode.PROJECTION_MISMATCH
            )


def verify_linux_confinement_predecessor_projection(
    core_bytes: bytes,
    profile_bytes: bytes,
    predecessor_bytes: bytes,
    pins: PortablePredicateLanguagePredecessorProjectionPinsV1,
) -> PortablePredicateLanguagePredecessorProjectionResultV1:
    """Validate a caller-pinned static projection, never equivalence."""

    validated_pins = _validated_pins(pins)
    if (
        type(core_bytes) is not bytes
        or type(profile_bytes) is not bytes
        or type(predecessor_bytes) is not bytes
    ):
        _fail(PortablePredicateLanguageCompositionCode.INPUT_TYPE)
    _check_artifact_pin(
        core_bytes,
        artifact_type=PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_ARTIFACT_TYPE,
        byte_count=validated_pins.core_contract_byte_count,
        plain_sha256=validated_pins.core_contract_plain_sha256,
        domain_sha256=validated_pins.core_contract_sha256,
    )
    core = _parse_core(core_bytes)
    _check_artifact_pin(
        profile_bytes,
        artifact_type=_LINUX_PROFILE_ARTIFACT_TYPE,
        byte_count=validated_pins.profile_contract_byte_count,
        plain_sha256=validated_pins.profile_contract_plain_sha256,
        domain_sha256=validated_pins.profile_contract_sha256,
    )
    profile = _parse_profile(profile_bytes)
    _validate_layer_metadata_artifact_type_disjointness(
        profile,
        additional_metadata_artifact_types=(
            LINUX_CONFINEMENT_PREDECESSOR_ARTIFACT_TYPE,
        ),
    )
    _check_artifact_pin(
        predecessor_bytes,
        artifact_type=validated_pins.predecessor_contract_artifact_type,
        byte_count=validated_pins.predecessor_contract_byte_count,
        plain_sha256=validated_pins.predecessor_contract_plain_sha256,
        domain_sha256=validated_pins.predecessor_contract_sha256,
    )
    descriptor = portable_predicate_language_composed_descriptor_tree(
        core_bytes,
        profile_bytes,
        expected_profile_artifact_type=_LINUX_PROFILE_ARTIFACT_TYPE,
        expected_profile_contract_sha256=(
            validated_pins.profile_contract_sha256
        ),
    )
    if (
        descriptor["profile_id"] != "LINUX_CONFINEMENT_V1"
        or descriptor["core_contract_sha256"]
        != portable_predicate_language_core_contract_sha256()
    ):
        _fail(PortablePredicateLanguageCompositionCode.PROFILE_INVALID)
    legacy = _legacy_tree(predecessor_bytes)
    _validate_core_projection(legacy, core, profile)
    _validate_profile_projection(legacy, core, profile)
    return PortablePredicateLanguagePredecessorProjectionResultV1(
        artifact_type=(
            PORTABLE_PREDICATE_LANGUAGE_PREDECESSOR_PROJECTION_RESULT_ARTIFACT_TYPE
        ),
        format_version="1",
        compositor_id=_COMPOSITOR_ID,
        implementation_status_id=_IMPLEMENTATION_STATUS,
        projection_status_id=_PROJECTION_STATUS,
        composition_contract_sha256=(
            portable_predicate_language_composition_contract_sha256()
        ),
        core_contract_byte_count=len(core_bytes),
        core_contract_plain_sha256=hashlib.sha256(core_bytes).hexdigest(),
        core_contract_sha256=_domain_sha256(
            PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_ARTIFACT_TYPE,
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
            portable_predicate_language_composed_descriptor_sha256(
                core_bytes,
                profile_bytes,
                expected_profile_artifact_type=(
                    _LINUX_PROFILE_ARTIFACT_TYPE
                ),
                expected_profile_contract_sha256=(
                    validated_pins.profile_contract_sha256
                ),
            )
        ),
        core_projection_component_count=len(_CORE_PROJECTION_COMPONENT_IDS),
        profile_projection_component_count=len(
            _PROFILE_PROJECTION_COMPONENT_IDS
        ),
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


def _projection_result_tree(
    value: PortablePredicateLanguagePredecessorProjectionResultV1,
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
        PortablePredicateLanguagePredecessorProjectionResultV1
        .__annotations__
        .items()
    ):
        expected_type = expected_types.get(annotation)
        field_value = getattr(value, field_id)
        if expected_type is None or type(field_value) is not expected_type:
            _fail(PortablePredicateLanguageCompositionCode.RESULT_INVALID)
        tree[field_id] = field_value
    return tree


def portable_predicate_language_predecessor_projection_result_bytes(
    value: PortablePredicateLanguagePredecessorProjectionResultV1,
) -> bytes:
    if type(value) is not PortablePredicateLanguagePredecessorProjectionResultV1:
        _fail(PortablePredicateLanguageCompositionCode.RESULT_INVALID)
    return _canonical_json(_projection_result_tree(value))


def portable_predicate_language_predecessor_projection_result_sha256(
    value: PortablePredicateLanguagePredecessorProjectionResultV1,
) -> str:
    return _domain_sha256(
        PORTABLE_PREDICATE_LANGUAGE_PREDECESSOR_PROJECTION_RESULT_ARTIFACT_TYPE,
        portable_predicate_language_predecessor_projection_result_bytes(value),
    )


def validate_portable_predicate_language_predecessor_projection_result(
    value: PortablePredicateLanguagePredecessorProjectionResultV1,
    core_bytes: bytes,
    profile_bytes: bytes,
    predecessor_bytes: bytes,
    pins: PortablePredicateLanguagePredecessorProjectionPinsV1,
) -> PortablePredicateLanguagePredecessorProjectionResultV1:
    """Reject every unequal or equal-value/wrong-type receipt."""

    if type(value) is not PortablePredicateLanguagePredecessorProjectionResultV1:
        _fail(PortablePredicateLanguageCompositionCode.RESULT_INVALID)
    expected = verify_linux_confinement_predecessor_projection(
        core_bytes,
        profile_bytes,
        predecessor_bytes,
        pins,
    )
    if not _same_exact(
        _projection_result_tree(value),
        _projection_result_tree(expected),
    ):
        _fail(PortablePredicateLanguageCompositionCode.RESULT_INVALID)
    return value


def _validate_frozen_contract() -> None:
    if len(
        {
            PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_ARTIFACT_TYPE,
            PORTABLE_PREDICATE_LANGUAGE_COMPOSITION_CONTRACT_ARTIFACT_TYPE,
            PORTABLE_PREDICATE_LANGUAGE_COMPOSED_DESCRIPTOR_ARTIFACT_TYPE,
            PORTABLE_PREDICATE_LANGUAGE_PREDECESSOR_PROJECTION_RESULT_ARTIFACT_TYPE,
            LINUX_CONFINEMENT_PREDECESSOR_ARTIFACT_TYPE,
        }
    ) != 5:
        _fail(PortablePredicateLanguageCompositionCode.CONTRACT_DRIFT)
    raw = portable_predicate_language_composition_contract_bytes()
    if (
        len(raw) != _V1_COMPOSITION_CONTRACT_BYTE_COUNT
        or hashlib.sha256(raw).hexdigest()
        != _V1_COMPOSITION_CONTRACT_PLAIN_SHA256
        or portable_predicate_language_composition_contract_sha256()
        != _V1_COMPOSITION_CONTRACT_SHA256
        or raw
        != _canonical_json(
            portable_predicate_language_composition_contract_tree()
        )
    ):
        _fail(PortablePredicateLanguageCompositionCode.CONTRACT_DRIFT)


_validate_frozen_contract()


__all__ = [
    "LINUX_CONFINEMENT_PREDECESSOR_ARTIFACT_TYPE",
    "PORTABLE_PREDICATE_LANGUAGE_COMPOSED_DESCRIPTOR_ARTIFACT_TYPE",
    "PORTABLE_PREDICATE_LANGUAGE_COMPOSITION_CONTRACT_ARTIFACT_TYPE",
    "PORTABLE_PREDICATE_LANGUAGE_COMPOSITION_CONTRACT_DIGEST_DOMAIN",
    "PORTABLE_PREDICATE_LANGUAGE_PREDECESSOR_PROJECTION_RESULT_ARTIFACT_TYPE",
    "PortablePredicateLanguageCompositionCode",
    "PortablePredicateLanguageCompositionError",
    "PortablePredicateLanguagePredecessorProjectionPinsV1",
    "PortablePredicateLanguagePredecessorProjectionResultV1",
    "parse_portable_predicate_language_composition_contract",
    "portable_predicate_language_composed_descriptor_bytes",
    "portable_predicate_language_composed_descriptor_sha256",
    "portable_predicate_language_composed_descriptor_tree",
    "portable_predicate_language_composition_contract_bytes",
    "portable_predicate_language_composition_contract_plain_sha256",
    "portable_predicate_language_composition_contract_sha256",
    "portable_predicate_language_composition_contract_tree",
    "portable_predicate_language_predecessor_projection_result_bytes",
    "portable_predicate_language_predecessor_projection_result_sha256",
    "validate_portable_predicate_language_predecessor_projection_result",
    "verify_linux_confinement_predecessor_projection",
]
