"""Profile-neutral static semantics for the portable predicate language.

This module freezes canonical encoding, nominal value structure, shaping
constructors, generic predicate operators, fail-closed propagation, runtime
artifact templates, and a closed profile interface.  It does not parse a
runtime program, evaluate an operator, resolve an operand, or validate an
empirical claim.
"""

from __future__ import annotations

from enum import Enum
import hashlib
import json
import re
from typing import Final


PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-semantic-core-contract.v1"
)
PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_DIGEST_DOMAIN: Final = (
    PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_ARTIFACT_TYPE
)
PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_INTERFACE_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-profile-interface.v1"
)
PORTABLE_PREDICATE_LANGUAGE_CORE_VERIFICATION_RESULT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.portable-predicate-language-core-verification-result.v1"
)
PORTABLE_PREDICATE_LANGUAGE_CORE_STATUS: Final = (
    "STATIC_PROFILE_NEUTRAL_SEMANTIC_CORE_IMPLEMENTED_RUNTIME_EVALUATOR_NOT_"
    "IMPLEMENTED"
)
PORTABLE_PREDICATE_LANGUAGE_CORE_VALIDATION_SCOPE: Final = (
    "STATIC_ENCODING_NOMINAL_TYPE_CONSTRUCTOR_OPERATOR_PROPAGATION_RUNTIME_"
    "TEMPLATE_AND_PROFILE_INTERFACE_ONLY"
)
PORTABLE_PREDICATE_LANGUAGE_CORE_ENCODING_ID: Final = (
    "canonical-ascii-json-sort-keys-no-whitespace-v1"
)
PORTABLE_PREDICATE_LANGUAGE_CORE_DIGEST_COMPUTATION_ID: Final = (
    "sha256-domain-nul-u64be-length-canonical-bytes-v1"
)
PORTABLE_PREDICATE_LANGUAGE_CORE_TYPED_IDENTITY_COMPUTATION_ID: Final = (
    "u64be-type-id-length-type-id-u64be-payload-length-payload-v1"
)
PORTABLE_PREDICATE_LANGUAGE_CORE_IDENTIFIER_GRAMMAR: Final = (
    "[A-Za-z0-9][A-Za-z0-9._:/+\\-]*"
)

MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_ARTIFACT_BYTES: Final = 4 * 1024 * 1024
MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_JSON_DEPTH: Final = 32
MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_JSON_ITEMS: Final = 65536
MAXIMUM_PORTABLE_PREDICATE_IDENTIFIER_BYTES: Final = 512
_MAXIMUM_JSON_INTEGER_DIGITS: Final = 20
_V1_CORE_CONTRACT_BYTE_COUNT: Final = 57674
_V1_CORE_CONTRACT_PLAIN_SHA256: Final = (
    "b13e1d349c08449096bd901e46087bbcc44181365354b553e6ecd89172864dc2"
)
_V1_CORE_CONTRACT_SHA256: Final = (
    "387b45d6f4ae8485433b36b929ed4d3a7b146c61e5d12629d46e2a74aa4536b2"
)
_V1_PROFILE_INTERFACE_SHA256: Final = (
    "2698f51d7326cc89d7a90880a7feea59d4cab81b3fffd4d04bc995ae646464b2"
)

PORTABLE_PREDICATE_LANGUAGE_CORE_TYPE_KIND_IDS: Final = (
    "boolean",
    "u64",
    "token",
    "octets",
    "sha256",
    "optional",
    "sequence",
    "tuple",
    "keyed-table",
    "u64-interval-sequence",
)
PORTABLE_PREDICATE_LANGUAGE_CORE_CONSTRUCTOR_IDS: Final = (
    "make-optional-none",
    "make-optional-some",
    "require-optional-present",
    "make-sequence",
    "make-tuple",
    "make-keyed-table",
    "make-u64-interval-sequence",
    "project-tuple-component",
    "project-keyed-table-column",
    "project-keyed-table-keys",
    "select-keyed-table-row",
    "canonical-sort-keyed-table",
)
PORTABLE_PREDICATE_LANGUAGE_CORE_OPERATOR_IDS: Final = (
    "absence",
    "all",
    "all-distinct",
    "any",
    "boolean-is",
    "count-equal",
    "digest-derived-from-bytes",
    "domain-digest-derived-from-bytes",
    "integer-sum-equal",
    "interval-order",
    "not",
    "octets-equal",
    "ordered-sequence-equal",
    "reference-resolves",
    "set-equal",
    "set-subset",
    "sha256-equal",
    "member-of-frozen-program-set",
    "token-equal",
    "u64-equal",
)
PORTABLE_PREDICATE_LANGUAGE_CORE_PUBLIC_ERROR_ROLE_IDS: Final = (
    "LOCAL_RULE_FAILED",
    "RUNTIME_SOURCE_UNAVAILABLE",
    "PARSER_REJECTED",
    "DERIVATION_MISMATCH",
    "UPSTREAM_RULE_FAILED",
    "EXTERNAL_AUTHORITY_UNAVAILABLE",
    "STATIC_MAPPING_UNRESOLVED",
)
PORTABLE_PREDICATE_LANGUAGE_CORE_LOCATOR_PRIMITIVE_IDS: Final = (
    "bounded-artifact-path",
    "direct-bound-value",
    "ordered-index",
    "composite-key",
    "sibling-resolved-value",
)
PORTABLE_PREDICATE_LANGUAGE_CORE_PURPOSE_RELATION_PRIMITIVE_IDS: Final = (
    "exactly-one-pinned-anchor-row-canonical-equality-v1",
    "purpose-identifiers-exactly-covered-by-input-locators-v1",
)
PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_PARAMETER_SLOT_IDS: Final = (
    "primary-program-purpose-id",
)
PORTABLE_PREDICATE_LANGUAGE_CORE_REQUIRED_ARTIFACT_ROLE_IDS: Final = (
    "predicate-program",
    "predicate-evaluation-context",
    "predicate-input-bundle",
    "predicate-evaluation-result",
    "predicate-formula-core",
)
PORTABLE_PREDICATE_LANGUAGE_CORE_RESERVED_METADATA_ARTIFACT_ROLE_IDS: Final = (
    "semantic-core-contract",
    "selected-profile-contract",
)
PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_FIELD_VALUE_SCHEMA_IDS: Final = (
    "strict-identifier-string-v1",
    "lowercase-sha256-string-v1",
    "nonnegative-index-or-count-integer-v1",
    "ordered-identifier-array-v1",
    "ordered-exact-object-row-array-v1",
)
PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_FIELD_SEMANTIC_ROLE_IDS: Final = (
    "opaque-identifier",
    "artifact-type-for-role",
    "artifact-identity-semantics-for-role",
    "artifact-identity-sha256-for-role",
    "anchor-artifact-type-for-role",
    "anchor-contract-sha256-for-role",
    "ordered-unique-identifiers",
    "identifier-member-of-purpose-field",
    "locator-kind-self",
    "path-segments",
    "nonnegative-count",
    "index-below-field",
    "typed-key-components",
    "prior-input-resolved-operand",
)
PORTABLE_PREDICATE_LANGUAGE_CORE_FALSE_CLAIM_IDS: Final = (
    "empirical_result_established",
    "portable_typed_formula_evaluated",
    "runtime_evaluator_implemented",
)

_IDENTIFIER_RE: Final = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$"
)
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")


class PortablePredicateLanguageCoreCode(str, Enum):
    """Closed failures for the exact static core and profile interface."""

    INPUT_TYPE = "INPUT_TYPE"
    INPUT_RESOURCE = "INPUT_RESOURCE"
    JSON_INVALID = "JSON_INVALID"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    CANONICAL_MISMATCH = "CANONICAL_MISMATCH"
    CONTRACT_DRIFT = "CONTRACT_DRIFT"


_ERROR_MESSAGES: Final = {
    PortablePredicateLanguageCoreCode.INPUT_TYPE: (
        "portable predicate-language core input has an invalid exact type"
    ),
    PortablePredicateLanguageCoreCode.INPUT_RESOURCE: (
        "portable predicate-language core input exceeds its resource ceiling"
    ),
    PortablePredicateLanguageCoreCode.JSON_INVALID: (
        "portable predicate-language core JSON is invalid"
    ),
    PortablePredicateLanguageCoreCode.SCHEMA_INVALID: (
        "portable predicate-language core schema is invalid"
    ),
    PortablePredicateLanguageCoreCode.CANONICAL_MISMATCH: (
        "portable predicate-language core bytes are not canonical"
    ),
    PortablePredicateLanguageCoreCode.CONTRACT_DRIFT: (
        "portable predicate-language core implementation drifted from its "
        "contract"
    ),
}


class PortablePredicateLanguageCoreError(ValueError):
    """One fixed-message core failure."""

    def __init__(self, code: PortablePredicateLanguageCoreCode):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


class _DuplicateKeyError(ValueError):
    pass


def _fail(code: PortablePredicateLanguageCoreCode) -> None:
    raise PortablePredicateLanguageCoreError(code)


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
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
    if len(encoded) > MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_ARTIFACT_BYTES:
        _fail(PortablePredicateLanguageCoreCode.INPUT_RESOURCE)
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


def _json_string_byte_count(value: str, maximum: int) -> int:
    """Return the canonical ensure-ASCII JSON-string size, capped early."""

    if maximum < 0:
        return 0
    if maximum < 2:
        return maximum + 1
    if len(value) > maximum - 2:
        return maximum + 1
    count = 2
    for character in value:
        codepoint = ord(character)
        if character in '"\\\b\f\n\r\t':
            count += 2
        elif codepoint < 0x20:
            count += 6
        elif codepoint <= 0x7E:
            count += 1
        elif codepoint <= 0xFFFF:
            count += 6
        else:
            count += 12
        if count > maximum:
            return count
    return count


def _bounded_exact_json_status(value: object) -> str:
    """Validate an acyclic exact-JSON tree before materializing its encoding."""

    item_count = 0
    encoded_byte_count = 0
    active_container_ids = set()
    frames = []
    current = value
    depth = 1
    while True:
        item_count += 1
        if (
            item_count
            > MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_JSON_ITEMS
            or depth > MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_JSON_DEPTH
        ):
            return "resource-invalid"

        current_type = type(current)
        if current_type is str:
            encoded_byte_count += _json_string_byte_count(
                current,
                MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_ARTIFACT_BYTES
                - encoded_byte_count,
            )
        elif current_type is bool:
            encoded_byte_count += 4 if current else 5
        elif current_type is int:
            if abs(current) >= 10**_MAXIMUM_JSON_INTEGER_DIGITS:
                return "schema-invalid"
            encoded_byte_count += len(str(current))
        elif current_type in (list, dict):
            container_id = id(current)
            if container_id in active_container_ids:
                return "schema-invalid"
            if (
                len(current)
                > MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_JSON_ITEMS
                - item_count
            ):
                return "resource-invalid"

            element_count = len(current)
            encoded_byte_count += (
                2
                + max(element_count - 1, 0)
                + (element_count if current_type is dict else 0)
            )
            if current_type is dict:
                if any(type(key) is not str for key in current):
                    return "schema-invalid"
                for key in current:
                    encoded_byte_count += _json_string_byte_count(
                        key,
                        MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_ARTIFACT_BYTES
                        - encoded_byte_count,
                    )
                    if (
                        encoded_byte_count
                        > MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_ARTIFACT_BYTES
                    ):
                        return "resource-invalid"
                children = iter(current.values())
            else:
                children = iter(current)
            active_container_ids.add(container_id)
            frames.append((children, depth + 1, container_id))
        else:
            return "schema-invalid"

        if (
            encoded_byte_count
            > MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_ARTIFACT_BYTES
        ):
            return "resource-invalid"

        while frames:
            children, child_depth, container_id = frames[-1]
            try:
                current = next(children)
            except StopIteration:
                frames.pop()
                active_container_ids.remove(container_id)
                continue
            except RuntimeError:
                return "schema-invalid"
            depth = child_depth
            break
        else:
            return "valid"


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


def _is_identifier(value: object) -> bool:
    return (
        type(value) is str
        and 1 <= len(value.encode("ascii", "ignore"))
        <= MAXIMUM_PORTABLE_PREDICATE_IDENTIFIER_BYTES
        and value.isascii()
        and _IDENTIFIER_RE.fullmatch(value) is not None
    )


def _is_sha256(value: object) -> bool:
    return type(value) is str and _SHA256_RE.fullmatch(value) is not None


def _unique_identifiers(values: object, *, nonempty: bool = True) -> bool:
    return (
        type(values) is list
        and (bool(values) or not nonempty)
        and all(_is_identifier(value) for value in values)
        and len(values) == len(set(values))
    )


def _type_kind_schema_rows() -> list:
    return [
        {
            "exact_field_ids": [
                "type_id",
                "type_kind_id",
                "proposition_domain_id",
            ],
            "reference_field_ids": [],
            "type_kind_id": "boolean",
            "validation_rule_id": (
                "strict-nominal-boolean-proposition-domain-v1"
            ),
        },
        {
            "exact_field_ids": ["type_id", "type_kind_id", "unit_id"],
            "reference_field_ids": [],
            "type_kind_id": "u64",
            "validation_rule_id": "strict-nominal-u64-unit-v1",
        },
        {
            "exact_field_ids": [
                "type_id",
                "type_kind_id",
                "token_domain_id",
            ],
            "reference_field_ids": [],
            "type_kind_id": "token",
            "validation_rule_id": "strict-nominal-token-domain-v1",
        },
        {
            "exact_field_ids": [
                "type_id",
                "type_kind_id",
                "octet_domain_id",
            ],
            "reference_field_ids": [],
            "type_kind_id": "octets",
            "validation_rule_id": "strict-nominal-octet-domain-v1",
        },
        {
            "exact_field_ids": [
                "type_id",
                "type_kind_id",
                "digest_semantics_id",
                "digest_domain_id",
            ],
            "reference_field_ids": [],
            "type_kind_id": "sha256",
            "validation_rule_id": (
                "plain-empty-domain-or-domain-separated-nonempty-domain-v1"
            ),
        },
        {
            "exact_field_ids": [
                "type_id",
                "type_kind_id",
                "item_type_id",
            ],
            "reference_field_ids": ["item_type_id"],
            "type_kind_id": "optional",
            "validation_rule_id": "prior-item-type-reference-v1",
        },
        {
            "exact_field_ids": [
                "type_id",
                "type_kind_id",
                "item_type_id",
            ],
            "reference_field_ids": ["item_type_id"],
            "type_kind_id": "sequence",
            "validation_rule_id": "prior-item-type-reference-v1",
        },
        {
            "exact_field_ids": [
                "type_id",
                "type_kind_id",
                "ordered_component_type_ids",
            ],
            "reference_field_ids": ["ordered_component_type_ids"],
            "type_kind_id": "tuple",
            "validation_rule_id": (
                "one-to-thirty-two-prior-component-type-references-v1"
            ),
        },
        {
            "exact_field_ids": [
                "type_id",
                "type_kind_id",
                "row_tuple_type_id",
                "key_tuple_type_id",
                "ordered_key_component_indices",
            ],
            "reference_field_ids": [
                "row_tuple_type_id",
                "key_tuple_type_id",
            ],
            "type_kind_id": "keyed-table",
            "validation_rule_id": (
                "prior-row-and-key-tuple-types-one-to-four-distinct-key-"
                "indices-with-exact-selected-component-type-match-v1"
            ),
        },
        {
            "exact_field_ids": [
                "type_id",
                "type_kind_id",
                "endpoint_u64_type_id",
            ],
            "reference_field_ids": ["endpoint_u64_type_id"],
            "type_kind_id": "u64-interval-sequence",
            "validation_rule_id": (
                "prior-nominal-u64-endpoint-and-closed-start-not-after-end-v1"
            ),
        },
    ]


def _value_encoding_rows() -> list:
    rows = (
        ("boolean", "one-byte-00-or-01-v1", 1, 1),
        ("u64", "unsigned-u64be-eight-bytes-v1", 8, 8),
        ("token", "strict-identifier-ascii-v1", 1, 512),
        ("octets", "bounded-uninterpreted-octets-v1", 0, 262144),
        ("sha256", "raw-sha256-thirty-two-bytes-v1", 32, 32),
        (
            "optional",
            "tag-00-or-tag-01-u64be-length-item-payload-v1",
            1,
            1048576,
        ),
        (
            "sequence",
            "u64be-count-repeated-u64be-length-item-payload-v1",
            8,
            1048576,
        ),
        (
            "tuple",
            "u64be-count-repeated-u64be-length-component-payload-v1",
            8,
            1048576,
        ),
        (
            "keyed-table",
            "u64be-row-count-repeated-u64be-length-tuple-payload-v1",
            8,
            1048576,
        ),
        (
            "u64-interval-sequence",
            "u64be-count-repeated-two-u64be-length-u64-payloads-v1",
            8,
            1048576,
        ),
    )
    return [
        {
            "encoding_id": encoding_id,
            "maximum_payload_bytes": maximum,
            "minimum_payload_bytes": minimum,
            "type_kind_id": kind_id,
        }
        for kind_id, encoding_id, minimum, maximum in rows
    ]


def _constructor_row(
    constructor_id: str,
    minimum_input_count: int,
    maximum_input_count: int,
    type_relation_id: str,
    failure_rule_id: str = "none",
    configuration_fields: tuple = (),
    configuration_rule: str = "exact-empty-object-v1",
) -> dict:
    return {
        "configuration_validation_rule_id": configuration_rule,
        "constructor_id": constructor_id,
        "exact_configuration_field_ids": list(configuration_fields),
        "failure_rule_id": failure_rule_id,
        "maximum_input_count": maximum_input_count,
        "minimum_input_count": minimum_input_count,
        "external_parsing_admitted": False,
        "type_relation_id": type_relation_id,
    }


def _constructor_rows() -> list:
    return [
        _constructor_row(
            "make-optional-none",
            0,
            0,
            "output-optional-no-input-v1",
        ),
        _constructor_row(
            "make-optional-some",
            1,
            1,
            "output-optional-item-equals-input-v1",
        ),
        _constructor_row(
            "require-optional-present",
            1,
            1,
            "input-optional-present-item-to-output-item-v1",
            "required-optional",
        ),
        _constructor_row(
            "make-sequence",
            0,
            64,
            "output-sequence-item-equals-every-input-v1",
        ),
        _constructor_row(
            "make-tuple",
            1,
            32,
            "output-tuple-components-equal-ordered-inputs-v1",
        ),
        _constructor_row(
            "make-keyed-table",
            0,
            64,
            "output-table-row-tuple-equals-every-input-v1",
            "duplicate-key",
        ),
        _constructor_row(
            "make-u64-interval-sequence",
            2,
            64,
            "even-start-end-inputs-one-nominal-u64-endpoint-type-v1",
            "invalid-interval",
        ),
        _constructor_row(
            "project-tuple-component",
            1,
            1,
            "output-equals-selected-tuple-component-v1",
            configuration_fields=("component_index",),
            configuration_rule=(
                "exact-component-index-json-u64-in-declared-range-v1"
            ),
        ),
        _constructor_row(
            "project-keyed-table-column",
            1,
            1,
            "output-sequence-item-equals-selected-row-component-v1",
            configuration_fields=("component_index",),
            configuration_rule=(
                "exact-component-index-json-u64-in-declared-range-v1"
            ),
        ),
        _constructor_row(
            "project-keyed-table-keys",
            1,
            1,
            "output-sequence-of-table-key-tuples-v1",
            "duplicate-key",
        ),
        _constructor_row(
            "select-keyed-table-row",
            2,
            2,
            "table-and-exact-key-tuple-to-one-row-tuple-v1",
            "exact-one-key",
        ),
        _constructor_row(
            "canonical-sort-keyed-table",
            1,
            1,
            "same-table-type-lexicographic-length-framed-key-order-v1",
            "duplicate-key",
        ),
    ]


def _operator_row(
    operator_id: str,
    operand_counts: tuple,
    child_counts: tuple,
    truth_rule: str,
    duplicate_or_range_rule: str = "none",
    configuration_fields: tuple = (),
    configuration_rule: str = "exact-empty-object-v1",
    operand_source_rule: str = "no-additional-source-restriction-v1",
    required_nominal_unit_id: str = "",
) -> dict:
    return {
        "applicability_id": "ALWAYS",
        "configuration_validation_rule_id": configuration_rule,
        "duplicate_or_range_rule_id": duplicate_or_range_rule,
        "exact_configuration_field_ids": list(configuration_fields),
        "failure_oracle_id": "FAIL_CLOSED_FOUR_DISPOSITION_V1",
        "maximum_child_count": child_counts[1],
        "maximum_operand_count": operand_counts[1],
        "minimum_child_count": child_counts[0],
        "minimum_operand_count": operand_counts[0],
        "operand_source_rule_id": operand_source_rule,
        "operator_id": operator_id,
        "required_nominal_unit_id": required_nominal_unit_id,
        "same_operand_reference_admitted": False,
        "type_and_truth_rule_id": truth_rule,
    }


def _operator_rows() -> list:
    return [
        _operator_row(
            "absence",
            (1, 1),
            (0, 0),
            "optional-absent-tag-v1",
        ),
        _operator_row(
            "all",
            (0, 0),
            (1, 64),
            "all-logically-true-v1",
        ),
        _operator_row(
            "all-distinct",
            (1, 1),
            (0, 0),
            "one-sequence-canonical-item-distinctness-v1",
            "duplicate-logical-false",
        ),
        _operator_row(
            "any",
            (0, 0),
            (1, 64),
            "at-least-one-logically-true-v1",
        ),
        _operator_row(
            "boolean-is",
            (2, 2),
            (0, 0),
            "identical-nominal-boolean-types-exact-equality-v1",
        ),
        _operator_row(
            "count-equal",
            (2, 2),
            (0, 0),
            "collection-and-item-count-u64-v1",
            required_nominal_unit_id="collection-item-count",
        ),
        _operator_row(
            "digest-derived-from-bytes",
            (2, 2),
            (0, 0),
            "octets-and-plain-sha256-v1",
        ),
        _operator_row(
            "domain-digest-derived-from-bytes",
            (2, 2),
            (0, 0),
            "octets-and-type-fixed-domain-sha256-frame-v1",
        ),
        _operator_row(
            "integer-sum-equal",
            (2, 2),
            (0, 0),
            "sequence-u64-and-identical-nominal-u64-v1",
            "checked-overflow-hard",
        ),
        _operator_row(
            "interval-order",
            (1, 1),
            (0, 0),
            "closed-nominal-u64-intervals-and-program-mode-adjacency-v1",
            configuration_fields=("interval_order_mode_id",),
            configuration_rule="exact-interval-order-mode-id-enum-v1",
        ),
        _operator_row(
            "not",
            (0, 0),
            (1, 1),
            "logical-inversion-only-v1",
        ),
        _operator_row(
            "octets-equal",
            (2, 2),
            (0, 0),
            "identical-nominal-octet-types-exact-equality-v1",
        ),
        _operator_row(
            "ordered-sequence-equal",
            (2, 2),
            (0, 0),
            "identical-nominal-sequence-or-table-types-v1",
        ),
        _operator_row(
            "reference-resolves",
            (2, 2),
            (0, 0),
            "unique-key-tuple-sequence-into-keyed-table-v1",
            "duplicate-hard",
        ),
        _operator_row(
            "set-equal",
            (2, 2),
            (0, 0),
            "sequences-with-identical-item-type-v1",
            "duplicate-hard",
        ),
        _operator_row(
            "set-subset",
            (2, 2),
            (0, 0),
            "sequences-with-identical-item-type-v1",
            "duplicate-hard",
        ),
        _operator_row(
            "sha256-equal",
            (2, 2),
            (0, 0),
            "identical-nominal-sha256-types-exact-equality-v1",
        ),
        _operator_row(
            "member-of-frozen-program-set",
            (2, 2),
            (0, 0),
            (
                "one-value-and-unique-nonempty-sequence-of-identical-item-"
                "type-exact-membership-v1"
            ),
            "duplicate-hard",
            operand_source_rule=(
                "second-membership-sequence-program-literal-canonical-unique-"
                "nonempty-v1"
            ),
        ),
        _operator_row(
            "token-equal",
            (2, 2),
            (0, 0),
            "identical-nominal-token-types-exact-equality-v1",
        ),
        _operator_row(
            "u64-equal",
            (2, 2),
            (0, 0),
            "identical-nominal-u64-types-exact-equality-v1",
        ),
    ]


def _input_state_rows() -> list:
    rows = (
        (
            "AVAILABLE",
            "",
            "",
            (
                "REQUIRED_RUNTIME_FAIL",
                "REQUIRED_EXTERNAL_NOT_EVALUATED",
            ),
        ),
        (
            "REQUIRED_RUNTIME_SOURCE_UNAVAILABLE",
            "HARD_FAILURE",
            "RUNTIME_SOURCE_UNAVAILABLE",
            ("REQUIRED_RUNTIME_FAIL",),
        ),
        (
            "PARSER_FAILED",
            "HARD_FAILURE",
            "PARSER_REJECTED",
            ("REQUIRED_RUNTIME_FAIL",),
        ),
        (
            "DERIVATION_FAILED",
            "HARD_FAILURE",
            "DERIVATION_MISMATCH",
            ("REQUIRED_RUNTIME_FAIL",),
        ),
        (
            "UPSTREAM_PREDICATE_FAILED",
            "HARD_FAILURE",
            "UPSTREAM_RULE_FAILED",
            ("REQUIRED_RUNTIME_FAIL",),
        ),
        (
            "EXTERNAL_AUTHORITY_UNAVAILABLE",
            "NOT_EVALUATED",
            "EXTERNAL_AUTHORITY_UNAVAILABLE",
            ("REQUIRED_EXTERNAL_NOT_EVALUATED",),
        ),
        (
            "STATIC_MAPPING_UNRESOLVED",
            "NOT_EVALUATED",
            "STATIC_MAPPING_UNRESOLVED",
            ("REQUIRED_EXTERNAL_NOT_EVALUATED",),
        ),
    )
    return [
        {
            "admitted_resolution_requirement_ids": list(requirements),
            "input_state_id": state_id,
            "internal_disposition_id": disposition_id,
            "public_error_role_id": error_role_id,
            "source_artifact_rule_id": (
                "strict-kind-and-lowercase-sha256-v1"
            ),
            "value_bytes_rule_id": (
                "nonempty-except-canonical-zero-length-octets-payload-v1"
                if state_id == "AVAILABLE"
                else "empty-v1"
            ),
        }
        for state_id, disposition_id, error_role_id, requirements in rows
    ]


def _resolution_requirement_rows() -> list:
    return [
        {
            "admitted_input_state_ids": [
                "AVAILABLE",
                "REQUIRED_RUNTIME_SOURCE_UNAVAILABLE",
                "PARSER_FAILED",
                "DERIVATION_FAILED",
                "UPSTREAM_PREDICATE_FAILED",
            ],
            "admitted_value_source_kind_ids": ["INPUT_RESOLVED"],
            "resolution_requirement_id": "REQUIRED_RUNTIME_FAIL",
        },
        {
            "admitted_input_state_ids": [
                "AVAILABLE",
                "EXTERNAL_AUTHORITY_UNAVAILABLE",
                "STATIC_MAPPING_UNRESOLVED",
            ],
            "admitted_value_source_kind_ids": ["INPUT_RESOLVED"],
            "resolution_requirement_id": (
                "REQUIRED_EXTERNAL_NOT_EVALUATED"
            ),
        },
        {
            "admitted_input_state_ids": [],
            "admitted_value_source_kind_ids": [
                "PROGRAM_LITERAL",
                "DERIVED_TYPED_VALUE",
            ],
            "resolution_requirement_id": "STATIC_CONTRACT",
        },
    ]


def _path_segment_schema_rows() -> list:
    return [
        {
            "exact_field_ids": ["segment_kind_id", "object_key"],
            "segment_kind_id": "object-key",
            "validation_rule_id": "strict-object-key-identifier-v1",
        },
        {
            "exact_field_ids": [
                "segment_kind_id",
                "list_index",
                "expected_list_count",
                "list_order_contract_sha256",
            ],
            "segment_kind_id": "list-index",
            "validation_rule_id": (
                "bounded-index-exact-count-and-order-contract-required-v1"
            ),
        },
        {
            "exact_field_ids": [
                "segment_kind_id",
                "ordered_key_component_rows",
            ],
            "key_component_exact_field_ids": [
                "key_field_id",
                "key_type_id",
                "key_value_bytes_hex",
            ],
            "segment_kind_id": "declared-keyed-list-item",
            "validation_rule_id": (
                "one-to-four-typed-components-exactly-one-row-match-v1"
            ),
        },
    ]


def _fixed_field_value_schema_rows() -> list:
    return [
        {
            "admitted_json_kind_id": "string",
            "field_ids": ["format_version"],
            "validation_rule_id": "exact-ascii-string-one-v1",
            "value_schema_id": "fixed-format-version-v1",
        },
        {
            "admitted_json_kind_id": "string",
            "field_ids": sorted(
                [
                    "applicability_id",
                    "artifact_type",
                    "constructor_id",
                    "digest_semantics_id",
                    "endpoint_u64_type_id",
                    "failure_oracle_id",
                    "input_state_id",
                    "internal_disposition_id",
                    "interval_order_mode_id",
                    "item_type_id",
                    "key_field_id",
                    "key_tuple_type_id",
                    "key_type_id",
                    "object_key",
                    "octet_domain_id",
                    "operator_id",
                    "origin_kind_id",
                    "output_operand_id",
                    "predicate_result_id",
                    "program_id",
                    "program_purpose_id",
                    "proposition_domain_id",
                    "resolution_requirement_id",
                    "root_node_id",
                    "root_result_id",
                    "row_tuple_type_id",
                    "segment_kind_id",
                    "shaping_node_id",
                    "source_artifact_kind_id",
                    "token_domain_id",
                    "type_id",
                    "type_kind_id",
                    "unit_id",
                    "value_source_kind_id",
                    "value_state_id",
                ]
            ),
            "validation_rule_id": (
                "strict-identifier-ascii-one-to-five-hundred-twelve-bytes-v1"
            ),
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "admitted_json_kind_id": "string",
            "field_ids": sorted(
                [
                    "digest_domain_id",
                    "executed_error_id",
                    "internal_condition_id",
                    "node_id",
                    "operand_id",
                    "root_executed_error_id",
                    "root_internal_condition_id",
                    "source_shaping_node_id",
                ]
            ),
            "validation_rule_id": (
                "empty-or-strict-identifier-ascii-up-to-five-hundred-twelve-"
                "bytes-v1"
            ),
            "value_schema_id": "empty-or-strict-identifier-string-v1",
        },
        {
            "admitted_json_kind_id": "string",
            "field_ids": sorted(
                [
                    "evaluation_context_identity_sha256",
                    "formula_core_identity_sha256",
                    "input_bundle_sha256",
                    "list_order_contract_sha256",
                    "profile_contract_sha256",
                    "program_sha256",
                    "semantic_core_contract_sha256",
                    "source_identity_sha256",
                ]
            ),
            "validation_rule_id": (
                "exact-sixty-four-lowercase-hex-digits-v1"
            ),
            "value_schema_id": "lowercase-sha256-string-v1",
        },
        {
            "admitted_json_kind_id": "string",
            "field_ids": ["typed_value_identity_sha256"],
            "validation_rule_id": (
                "empty-or-exact-sixty-four-lowercase-hex-digits-v1"
            ),
            "value_schema_id": "empty-or-lowercase-sha256-string-v1",
        },
        {
            "admitted_json_kind_id": "string",
            "field_ids": sorted(
                [
                    "key_value_bytes_hex",
                    "literal_value_bytes_hex",
                    "value_bytes_hex",
                ]
            ),
            "validation_rule_id": (
                "lowercase-even-length-zero-or-more-hex-digits-v1"
            ),
            "value_schema_id": "canonical-payload-hex-string-v1",
        },
        {
            "admitted_json_kind_id": "string",
            "field_ids": ["context_nonce_hex"],
            "validation_rule_id": (
                "exact-sixty-four-lowercase-hex-nonzero-v1"
            ),
            "value_schema_id": "nonzero-context-nonce-hex-string-v1",
        },
        {
            "admitted_json_kind_id": "integer",
            "field_ids": sorted(
                [
                    "component_index",
                    "expected_list_count",
                    "list_index",
                    "node_index",
                    "operand_declaration_index",
                ]
            ),
            "validation_rule_id": (
                "nonnegative-json-integer-with-containing-schema-ceiling-v1"
            ),
            "value_schema_id": "nonnegative-index-or-count-integer-v1",
        },
        {
            "additional_field_id_source_rule_id": (
                "selected-profile-nonclaim-state-keys-v1"
            ),
            "admitted_json_kind_id": "boolean",
            "field_ids": sorted(
                PORTABLE_PREDICATE_LANGUAGE_CORE_FALSE_CLAIM_IDS
            ),
            "validation_rule_id": (
                "exact-json-boolean-refined-by-claim-schema-v1"
            ),
            "value_schema_id": "declared-claim-boolean-v1",
        },
        {
            "admitted_json_kind_id": "array",
            "field_ids": sorted(
                [
                    "ordered_authority_class_ids",
                    "ordered_child_node_ids",
                    "ordered_component_type_ids",
                    "ordered_input_operand_ids",
                    "ordered_operand_ids",
                ]
            ),
            "validation_rule_id": (
                "bounded-array-of-strict-identifiers-with-order-and-"
                "cardinality-refined-by-containing-schema-v1"
            ),
            "value_schema_id": "ordered-identifier-array-v1",
        },
        {
            "admitted_json_kind_id": "array",
            "field_ids": ["ordered_key_component_indices"],
            "validation_rule_id": (
                "bounded-ordered-nonnegative-json-integer-array-v1"
            ),
            "value_schema_id": "ordered-index-array-v1",
        },
        {
            "admitted_json_kind_id": "array",
            "field_ids": sorted(
                [
                    "ordered_input_rows",
                    "ordered_key_component_rows",
                    "ordered_operand_rows",
                    "ordered_path_segments",
                    "ordered_predicate_node_rows",
                    "ordered_predicate_result_rows",
                    "ordered_shaping_node_rows",
                    "ordered_shaping_result_rows",
                    "ordered_type_rows",
                ]
            ),
            "validation_rule_id": (
                "bounded-array-of-exact-json-objects-with-element-schema-"
                "order-and-cardinality-refined-by-containing-schema-v1"
            ),
            "value_schema_id": "ordered-exact-object-row-array-v1",
        },
        {
            "admitted_json_kind_id": "object",
            "field_ids": sorted(
                [
                    "claim_state",
                    "constructor_configuration",
                    "locator",
                    "nonclaim_state",
                    "operator_configuration",
                    "purpose_binding",
                    "selected_fault_origin",
                ]
            ),
            "validation_rule_id": (
                "exact-json-object-fields-and-values-refined-by-containing-"
                "schema-v1"
            ),
            "value_schema_id": "context-refined-exact-object-v1",
        },
    ]


def _artifact_nested_schema_rows() -> list:
    return [
        {
            "exact_field_ids": [],
            "exact_field_source_rule_id": (
                "selected-profile-program-purpose-schema-v1"
            ),
            "schema_id": "program-purpose-binding-v1",
            "validation_rule_id": (
                "exact-fields-from-selected-profile-purpose-v1"
            ),
        },
        {
            "exact_field_ids": [],
            "exact_field_source_rule_id": (
                "selected-core-type-kind-schema-row-v1"
            ),
            "schema_id": "program-type-row-by-kind-v1",
            "validation_rule_id": (
                "exact-fields-and-prior-type-references-by-kind-v1"
            ),
        },
        {
            "exact_field_ids": [
                "operand_id",
                "type_id",
                "value_source_kind_id",
                "resolution_requirement_id",
                "ordered_authority_class_ids",
                "locator",
                "literal_value_bytes_hex",
                "source_shaping_node_id",
            ],
            "schema_id": "program-operand-row-by-source-kind-v1",
            "source_kind_rule_rows": [
                {
                    "authority_class_rule_id": (
                        "one-to-profile-authority-count-ordered-unique-v1"
                    ),
                    "literal_value_rule_id": "empty-v1",
                    "locator_rule_id": (
                        "nonempty-profile-declared-input-locator-v1"
                    ),
                    "resolution_requirement_ids": [
                        "REQUIRED_RUNTIME_FAIL",
                        "REQUIRED_EXTERNAL_NOT_EVALUATED",
                    ],
                    "source_shaping_node_rule_id": "empty-v1",
                    "value_source_kind_id": "INPUT_RESOLVED",
                },
                {
                    "authority_class_rule_id": "empty-v1",
                    "literal_value_rule_id": (
                        "canonical-declared-type-payload-v1"
                    ),
                    "locator_rule_id": "empty-v1",
                    "resolution_requirement_ids": ["STATIC_CONTRACT"],
                    "source_shaping_node_rule_id": "empty-v1",
                    "value_source_kind_id": "PROGRAM_LITERAL",
                },
                {
                    "authority_class_rule_id": (
                        "ordered-canonical-union-of-transitive-input-"
                        "authorities-v1"
                    ),
                    "literal_value_rule_id": "empty-v1",
                    "locator_rule_id": "empty-v1",
                    "resolution_requirement_ids": ["STATIC_CONTRACT"],
                    "source_shaping_node_rule_id": (
                        "exactly-one-prior-producing-shaping-node-v1"
                    ),
                    "value_source_kind_id": "DERIVED_TYPED_VALUE",
                },
            ],
            "validation_rule_id": (
                "exact-conditional-source-kind-fields-and-relations-v1"
            ),
        },
        {
            "exact_field_ids": [
                "artifact_type",
                "format_version",
                "semantic_core_contract_sha256",
                "profile_contract_sha256",
                "ordered_type_rows",
                "ordered_operand_rows",
                "ordered_shaping_node_rows",
                "ordered_predicate_node_rows",
                "root_node_id",
            ],
            "schema_id": "predicate-formula-core-v1",
            "validation_rule_id": (
                "canonical-program-projection-with-fixed-core-and-profile-"
                "pins-excluding-program-identity-purpose-and-nonclaims-v1"
            ),
        },
        {
            "exact_field_ids": [
                "shaping_node_id",
                "constructor_id",
                "output_operand_id",
                "ordered_input_operand_ids",
                "constructor_configuration",
                "applicability_id",
                "failure_oracle_id",
            ],
            "schema_id": "program-shaping-node-row-v1",
            "validation_rule_id": (
                "closed-constructor-schema-and-derived-dag-rule-v1"
            ),
        },
        {
            "exact_field_ids": [
                "node_id",
                "operator_id",
                "ordered_operand_ids",
                "ordered_child_node_ids",
                "operator_configuration",
                "applicability_id",
                "failure_oracle_id",
            ],
            "schema_id": "program-predicate-node-row-v1",
            "validation_rule_id": (
                "closed-operator-schema-topological-reachable-dag-v1"
            ),
        },
        {
            "exact_field_ids": [
                "operand_id",
                "input_state_id",
                "source_artifact_kind_id",
                "source_identity_sha256",
                "value_bytes_hex",
            ],
            "derived_input_state_rule_id": (
                "state-is-deterministically-derived-by-profile-locator-"
                "resolver-and-core-parser-or-derivation-outcome-never-"
                "caller-selected-v1"
            ),
            "schema_id": "input-bundle-row-by-declared-resolution-v1",
            "validation_rule_id": (
                "exact-state-admitted-by-operand-resolution-requirement-v1"
            ),
        },
        {
            "exact_field_ids": [],
            "exact_field_source_rule_id": (
                "ordered-union-core-and-selected-profile-nonclaim-ids-v1"
            ),
            "schema_id": "merged-static-nonclaim-state-v1",
            "validation_rule_id": "exact-derived-fields-all-false-v1",
        },
        {
            "exact_field_ids": [
                "shaping_node_id",
                "output_operand_id",
                "value_state_id",
                "executed_error_id",
                "internal_condition_id",
                "selected_fault_origin",
                "typed_value_identity_sha256",
            ],
            "schema_id": "shaping-result-row-v1",
            "validation_rule_id": (
                "exact-derived-value-or-selected-propagated-fault-row-v1"
            ),
            "value_state_rule_rows": [
                {
                    "error_role_rule_id": "EMPTY",
                    "internal_condition_rule_id": "EMPTY",
                    "field_rule_id": (
                        "typed-value-identity-present-error-condition-empty-"
                        "fault-origin-none-v1"
                    ),
                    "value_state_id": "VALUE_AVAILABLE",
                },
                {
                    "error_role_rule_id": (
                        "FIXED_LOCAL_RULE_FAILED_OR_PROPAGATE_SELECTED_ORIGIN"
                    ),
                    "internal_condition_rule_id": (
                        "FIXED_CONSTRUCTOR_CONDITION_OR_PROPAGATE_SELECTED_"
                        "ORIGIN_CONDITION_OR_EMPTY"
                    ),
                    "field_rule_id": (
                        "typed-value-identity-empty-local-or-origin-error-"
                        "condition-and-selected-origin-v1"
                    ),
                    "value_state_id": "HARD_FAILURE",
                },
                {
                    "error_role_rule_id": (
                        "PROPAGATE_SELECTED_ORIGIN_PUBLIC_ERROR"
                    ),
                    "internal_condition_rule_id": (
                        "PROPAGATE_SELECTED_ORIGIN_CONDITION_OR_EMPTY"
                    ),
                    "field_rule_id": (
                        "typed-value-identity-empty-origin-error-condition-"
                        "and-selected-origin-v1"
                    ),
                    "value_state_id": "NOT_EVALUATED",
                },
            ],
        },
        {
            "disposition_rule_rows": [
                {
                    "error_role_rule_id": "EMPTY",
                    "internal_condition_rule_id": "EMPTY",
                    "field_rule_id": (
                        "pass-error-condition-empty-fault-origin-none-v1"
                    ),
                    "internal_disposition_id": "LOGICAL_TRUE",
                    "predicate_result_id": "PASS",
                },
                {
                    "error_role_rule_id": "FIXED_LOCAL_RULE_FAILED",
                    "internal_condition_rule_id": "FIXED_LOGICAL_FALSE",
                    "field_rule_id": (
                        "fail-local-rule-failed-logical-false-condition-"
                        "fault-origin-none-v1"
                    ),
                    "internal_disposition_id": "LOGICAL_FALSE",
                    "predicate_result_id": "FAIL",
                },
                {
                    "error_role_rule_id": (
                        "PROPAGATE_SELECTED_ORIGIN_PUBLIC_ERROR"
                    ),
                    "internal_condition_rule_id": (
                        "PROPAGATE_SELECTED_ORIGIN_CONDITION_OR_EMPTY"
                    ),
                    "field_rule_id": (
                        "fail-origin-error-condition-and-selected-fault-"
                        "origin-present-v1"
                    ),
                    "internal_disposition_id": "HARD_FAILURE",
                    "predicate_result_id": "FAIL",
                },
                {
                    "error_role_rule_id": (
                        "PROPAGATE_SELECTED_ORIGIN_PUBLIC_ERROR"
                    ),
                    "internal_condition_rule_id": (
                        "PROPAGATE_SELECTED_ORIGIN_CONDITION_OR_EMPTY"
                    ),
                    "field_rule_id": (
                        "not-evaluated-origin-error-condition-and-selected-"
                        "fault-origin-present-v1"
                    ),
                    "internal_disposition_id": "NOT_EVALUATED",
                    "predicate_result_id": "NOT_EVALUATED",
                },
            ],
            "exact_field_ids": [
                "node_id",
                "internal_disposition_id",
                "predicate_result_id",
                "executed_error_id",
                "internal_condition_id",
                "selected_fault_origin",
            ],
            "schema_id": "predicate-result-row-v1",
            "validation_rule_id": (
                "exact-four-disposition-public-result-row-v1"
            ),
        },
        {
            "exact_field_ids": [
                "origin_kind_id",
                "operand_declaration_index",
                "node_index",
                "operand_id",
                "node_id",
            ],
            "origin_kind_ids": [
                "NONE",
                "INPUT_OPERAND",
                "SHAPING_NODE",
                "PREDICATE_NODE",
            ],
            "origin_kind_rule_rows": [
                {
                    "id_and_index_rule_id": (
                        "both-index-sentinels-and-both-ids-empty-v1"
                    ),
                    "origin_kind_id": "NONE",
                },
                {
                    "id_and_index_rule_id": (
                        "exact-operand-index-and-id-node-sentinel-empty-v1"
                    ),
                    "origin_kind_id": "INPUT_OPERAND",
                },
                {
                    "id_and_index_rule_id": (
                        "exact-global-shaping-index-id-and-earliest-"
                        "causative-operand-or-sentinel-v1"
                    ),
                    "origin_kind_id": "SHAPING_NODE",
                },
                {
                    "id_and_index_rule_id": (
                        "exact-global-predicate-index-id-and-earliest-"
                        "causative-operand-or-sentinel-v1"
                    ),
                    "origin_kind_id": "PREDICATE_NODE",
                },
            ],
            "schema_id": "selected-fault-origin-v1",
            "validation_rule_id": (
                "exact-origin-or-all-sentinel-fields-v1"
            ),
        },
        {
            "exact_field_ids": [],
            "exact_field_source_rule_id": (
                "ordered-union-core-and-selected-profile-claim-ids-v1"
            ),
            "schema_id": "evaluation-result-claim-state-v1",
            "validation_rule_id": (
                "only-portable-typed-formula-evaluated-conditionally-true-"
                "all-other-claims-false-v1"
            ),
        },
    ]


def _artifact_identity_reference_rows() -> list:
    return [
        {
            "field_id": "semantic_core_contract_sha256",
            "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
            "referenced_artifact_role_id": "semantic-core-contract",
        },
        {
            "field_id": "profile_contract_sha256",
            "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
            "referenced_artifact_role_id": "selected-profile-contract",
        },
        {
            "field_id": "formula_core_identity_sha256",
            "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
            "referenced_artifact_role_id": "predicate-formula-core",
        },
        {
            "field_id": "program_sha256",
            "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
            "referenced_artifact_role_id": "predicate-program",
        },
        {
            "field_id": "evaluation_context_identity_sha256",
            "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
            "referenced_artifact_role_id": (
                "predicate-evaluation-context"
            ),
        },
        {
            "field_id": "input_bundle_sha256",
            "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
            "referenced_artifact_role_id": "predicate-input-bundle",
        },
    ]


def _artifact_family_rows() -> list:
    return [
        {
            "artifact_family_id": "PredicateProgramV1",
            "artifact_role_id": "predicate-program",
            "cross_field_validation_rule_ids": [
                "fixed-role-type-format-core-and-profile-pins-v1",
                "purpose-binding-exact-selected-profile-schema-v1",
                "formula-core-is-canonical-program-projection-v1",
                "all-program-row-and-whole-graph-rules-hold-v1",
                "merged-static-nonclaims-exact-and-all-false-v1",
            ],
            "exact_field_ids": [
                "artifact_type",
                "format_version",
                "semantic_core_contract_sha256",
                "profile_contract_sha256",
                "formula_core_identity_sha256",
                "program_id",
                "program_purpose_id",
                "purpose_binding",
                "ordered_type_rows",
                "ordered_operand_rows",
                "ordered_shaping_node_rows",
                "ordered_predicate_node_rows",
                "root_node_id",
                "nonclaim_state",
            ],
            "identity_projection_rule_id": (
                "whole-canonical-artifact-with-recomputed-profile-domain-"
                "formula-core-identity-v1"
            ),
            "nested_schema_ids": [
                "program-purpose-binding-v1",
                "predicate-formula-core-v1",
                "program-type-row-by-kind-v1",
                "program-operand-row-by-source-kind-v1",
                "program-shaping-node-row-v1",
                "program-predicate-node-row-v1",
                "merged-static-nonclaim-state-v1",
            ],
        },
        {
            "artifact_family_id": "PredicateFormulaCoreV1",
            "artifact_role_id": "predicate-formula-core",
            "cross_field_validation_rule_ids": [
                "fixed-role-type-format-core-and-profile-pins-v1",
                "exact-canonical-projection-of-one-predicate-program-v1",
                "all-program-row-and-whole-graph-rules-hold-v1",
            ],
            "exact_field_ids": [
                "artifact_type",
                "format_version",
                "semantic_core_contract_sha256",
                "profile_contract_sha256",
                "ordered_type_rows",
                "ordered_operand_rows",
                "ordered_shaping_node_rows",
                "ordered_predicate_node_rows",
                "root_node_id",
            ],
            "identity_projection_rule_id": "whole-canonical-artifact-v1",
            "nested_schema_ids": [
                "predicate-formula-core-v1",
                "program-type-row-by-kind-v1",
                "program-operand-row-by-source-kind-v1",
                "program-shaping-node-row-v1",
                "program-predicate-node-row-v1",
            ],
        },
        {
            "artifact_family_id": "PredicateEvaluationContextV1",
            "artifact_role_id": "predicate-evaluation-context",
            "cross_field_validation_rule_ids": [
                "fixed-role-type-format-core-and-profile-pins-v1",
                "program-identity-matches-exact-program-v1",
                "nonzero-context-nonce-and-all-false-nonclaims-v1",
            ],
            "exact_field_ids": [
                "artifact_type",
                "format_version",
                "semantic_core_contract_sha256",
                "profile_contract_sha256",
                "program_sha256",
                "context_nonce_hex",
                "nonclaim_state",
            ],
            "identity_projection_rule_id": "whole-canonical-artifact-v1",
            "nested_schema_ids": ["merged-static-nonclaim-state-v1"],
        },
        {
            "artifact_family_id": "PredicateInputBundleV1",
            "artifact_role_id": "predicate-input-bundle",
            "cross_field_validation_rule_ids": [
                "fixed-role-type-format-core-and-profile-pins-v1",
                "program-and-context-identities-match-exact-artifacts-v1",
                "one-input-row-per-input-resolved-operand-in-order-v1",
                "merged-static-nonclaims-exact-and-all-false-v1",
            ],
            "exact_field_ids": [
                "artifact_type",
                "format_version",
                "semantic_core_contract_sha256",
                "profile_contract_sha256",
                "program_sha256",
                "evaluation_context_identity_sha256",
                "ordered_input_rows",
                "nonclaim_state",
            ],
            "identity_projection_rule_id": "whole-canonical-artifact-v1",
            "nested_schema_ids": [
                "input-bundle-row-by-declared-resolution-v1",
                "merged-static-nonclaim-state-v1",
            ],
        },
        {
            "artifact_family_id": "PredicateEvaluationResultV1",
            "artifact_role_id": "predicate-evaluation-result",
            "cross_field_validation_rule_ids": [
                "fixed-role-type-format-core-and-profile-pins-v1",
                "program-input-context-identities-exact-match-v1",
                "one-result-row-per-program-node-in-program-order-v1",
                "root-fields-byte-exact-mirror-root-predicate-result-v1",
                "claim-state-exactly-follows-evaluation-result-rule-v1",
            ],
            "exact_field_ids": [
                "artifact_type",
                "format_version",
                "semantic_core_contract_sha256",
                "profile_contract_sha256",
                "program_sha256",
                "input_bundle_sha256",
                "evaluation_context_identity_sha256",
                "ordered_shaping_result_rows",
                "ordered_predicate_result_rows",
                "root_result_id",
                "root_executed_error_id",
                "root_internal_condition_id",
                "selected_fault_origin",
                "claim_state",
            ],
            "identity_projection_rule_id": "whole-canonical-artifact-v1",
            "nested_schema_ids": [
                "shaping-result-row-v1",
                "predicate-result-row-v1",
                "selected-fault-origin-v1",
                "evaluation-result-claim-state-v1",
            ],
        },
    ]


def _profile_field_semantic_role_rows() -> list:
    rows = (
        (
            "opaque-identifier",
            ("strict-identifier-string-v1",),
            "literal-none-sentinel-v1",
        ),
        (
            "artifact-type-for-role",
            ("strict-identifier-string-v1",),
            "declared-artifact-role-id-v1",
        ),
        (
            "artifact-identity-semantics-for-role",
            ("strict-identifier-string-v1",),
            "declared-artifact-role-id-v1",
        ),
        (
            "artifact-identity-sha256-for-role",
            ("lowercase-sha256-string-v1",),
            "declared-artifact-role-id-v1",
        ),
        (
            "anchor-artifact-type-for-role",
            ("strict-identifier-string-v1",),
            "declared-anchor-role-id-v1",
        ),
        (
            "anchor-contract-sha256-for-role",
            ("lowercase-sha256-string-v1",),
            "declared-anchor-role-id-v1",
        ),
        (
            "ordered-unique-identifiers",
            ("ordered-identifier-array-v1",),
            "literal-none-sentinel-v1",
        ),
        (
            "identifier-member-of-purpose-field",
            ("strict-identifier-string-v1",),
            "other-purpose-ordered-identifier-field-id-v1",
        ),
        (
            "locator-kind-self",
            ("strict-identifier-string-v1",),
            "literal-none-sentinel-v1",
        ),
        (
            "path-segments",
            ("ordered-exact-object-row-array-v1",),
            "literal-none-sentinel-v1",
        ),
        (
            "nonnegative-count",
            ("nonnegative-index-or-count-integer-v1",),
            "literal-none-sentinel-v1",
        ),
        (
            "index-below-field",
            ("nonnegative-index-or-count-integer-v1",),
            "co-located-nonnegative-count-field-id-v1",
        ),
        (
            "typed-key-components",
            ("ordered-exact-object-row-array-v1",),
            "literal-none-sentinel-v1",
        ),
        (
            "prior-input-resolved-operand",
            ("strict-identifier-string-v1",),
            "literal-none-sentinel-v1",
        ),
    )
    return [
        {
            "admitted_value_schema_ids": list(value_schema_ids),
            "role_parameter_rule_id": parameter_rule_id,
            "semantic_role_id": semantic_role_id,
        }
        for semantic_role_id, value_schema_ids, parameter_rule_id in rows
    ]


def _locator_primitive_profile_field_constraint_rows() -> list:
    rows = (
        (
            "bounded-artifact-path",
            ("path-segments",),
            (("path-segments", 1),),
        ),
        (
            "direct-bound-value",
            (),
            (),
        ),
        (
            "ordered-index",
            ("nonnegative-count", "index-below-field"),
            (
                ("nonnegative-count", 1),
                ("index-below-field", 1),
                ("artifact-identity-sha256-for-role", 1),
            ),
        ),
        (
            "composite-key",
            ("typed-key-components",),
            (("typed-key-components", 1),),
        ),
        (
            "sibling-resolved-value",
            ("prior-input-resolved-operand",),
            (("prior-input-resolved-operand", 1),),
        ),
    )
    return [
        {
            "admitted_selection_semantic_role_ids": list(admitted_role_ids),
            "locator_primitive_id": primitive_id,
            "required_semantic_role_count_rows": [
                {
                    "required_count": required_count,
                    "semantic_role_id": semantic_role_id,
                }
                for semantic_role_id, required_count in required_rows
            ],
        }
        for primitive_id, admitted_role_ids, required_rows in rows
    ]


def _program_purpose_relation_primitive_rows() -> list:
    return [
        {
            "cardinality_rule_id": "exactly-one-matching-row-v1",
            "comparison_rule_id": "exact-recursive-json-type-and-value-v1",
            "path_resolution_rule_id": "exact-object-keys-only-v1",
            "relation_primitive_id": (
                "exactly-one-pinned-anchor-row-canonical-equality-v1"
            ),
            "source_kind_id": "PINNED_ANCHOR_CONTRACT",
        },
        {
            "cardinality_rule_id": (
                "duplicate-locator-uses-admitted-required-identifiers-"
                "unique-v1"
            ),
            "comparison_rule_id": (
                "set-of-program-input-locator-field-values-exactly-equals-"
                "purpose-identifier-array-v1"
            ),
            "path_resolution_rule_id": "not-applicable-v1",
            "relation_primitive_id": (
                "purpose-identifiers-exactly-covered-by-input-locators-v1"
            ),
            "source_kind_id": "PROGRAM_INPUT_LOCATORS",
        },
    ]


def _profile_interface_tree() -> dict:
    semantic_role_rows = _profile_field_semantic_role_rows()
    return {
        "admitted_interval_refinement_ids": [
            "nominal-u64-endpoint-binding"
        ],
        "admitted_locator_primitive_ids": list(
            PORTABLE_PREDICATE_LANGUAGE_CORE_LOCATOR_PRIMITIVE_IDS
        ),
        "admitted_profile_bound_operator_primitive_ids": [
            "member-of-frozen-program-set"
        ],
        "admitted_profile_field_value_schema_ids": list(
            PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_FIELD_VALUE_SCHEMA_IDS
        ),
        "interval_refinement_primitive_rows": [
            {
                "parameter_reference_field_id": (
                    "endpoint_parameter_slot_id"
                ),
                "refinement_primitive_id": (
                    "nominal-u64-endpoint-binding"
                ),
            },
        ],
        "locator_primitive_profile_field_constraint_rows": (
            _locator_primitive_profile_field_constraint_rows()
        ),
        "locator_empty_placeholder_value_rule_id": (
            "exact-empty-json-array-never-traversed-v1"
        ),
        "maximum_profile_registry_counts": {
            "anchor_contract_rows": 64,
            "artifact_domain_rows": 64,
            "authority_class_ids": 256,
            "interval_refinement_rows": 64,
            "locator_extension_rows": 256,
            "nonclaim_state": 256,
            "operator_specialization_rows": 64,
            "profile_field_schema_rows": 1024,
            "profile_parameter_rows": 128,
            "program_purpose_equality_rows": 4096,
            "program_purpose_relation_rows": 256,
            "program_purpose_rows": 64,
            "public_error_ids": 128,
        },
        "profile_bound_operator_primitive_rows": [
            {
                "maximum_parameter_slot_count": 32,
                "minimum_parameter_slot_count": 1,
                "operand_source_rule_id": (
                    "second-membership-sequence-program-literal-canonical-"
                    "unique-nonempty-v1"
                ),
                "parameter_binding_rule_id": (
                    "one-parameter-binds-token-item-domain-more-than-one-"
                    "binds-exact-tuple-of-ordered-token-component-domains-v1"
                ),
                "primitive_id": "member-of-frozen-program-set",
                "type_and_truth_rule_id": (
                    "one-value-and-unique-nonempty-sequence-of-identical-"
                    "item-type-exact-membership-v1"
                ),
            },
        ],
        "artifact_type": (
            PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_INTERFACE_ARTIFACT_TYPE
        ),
        "closed_profile_exact_field_ids": [
            "anchor_contract_rows",
            "artifact_domain_rows",
            "artifact_type",
            "authority_class_ids",
            "core_contract_sha256",
            "core_profile_interface_sha256",
            "digest_computation_id",
            "encoding_id",
            "fixed_counts",
            "format_version",
            "implementation_status_id",
            "interval_refinement_rows",
            "locator_extension_rows",
            "nonclaim_state",
            "operator_specialization_rows",
            "profile_class_id",
            "profile_id",
            "profile_interface_id",
            "profile_field_schema_rows",
            "profile_parameter_rows",
            "profile_verification_result_artifact_type",
            "program_purpose_rows",
            "public_error_ids",
            "public_error_role_rows",
            "validation_scope_id",
        ],
        "forbidden_profile_override_ids": [
            "canonical-encoding",
            "constructor-registry",
            "fault-precedence",
            "graph-rules",
            "identifier-grammar",
            "internal-dispositions",
            "operator-semantics",
            "resource-limits",
            "result-mapping",
            "type-codecs",
        ],
        "format_version": "1",
        "profile_interface_id": (
            "PORTABLE_PREDICATE_LANGUAGE_CLOSED_PROFILE_INTERFACE_V1"
        ),
        "profile_field_semantic_role_rows": semantic_role_rows,
        "profile_locator_validation_primitive_id": (
            "profile-field-schema-and-locator-primitive-v1"
        ),
        "profile_program_purpose_validation_primitive_id": (
            "profile-field-schema-and-purpose-relations-v1"
        ),
        "program_purpose_relation_primitive_rows": (
            _program_purpose_relation_primitive_rows()
        ),
        "profile_validation_rule_label_semantics_id": (
            "non-authoritative-descriptive-legacy-correspondence-label-v1"
        ),
        "required_profile_parameter_slot_ids": list(
            PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_PARAMETER_SLOT_IDS
        ),
        "required_public_error_role_ids": list(
            PORTABLE_PREDICATE_LANGUAGE_CORE_PUBLIC_ERROR_ROLE_IDS
        ),
        "required_runtime_artifact_role_ids": list(
            PORTABLE_PREDICATE_LANGUAGE_CORE_REQUIRED_ARTIFACT_ROLE_IDS
        ),
        "reserved_metadata_artifact_role_ids": list(
            PORTABLE_PREDICATE_LANGUAGE_CORE_RESERVED_METADATA_ARTIFACT_ROLE_IDS
        ),
        "reserved_core_metadata_artifact_type_ids": [
            PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_ARTIFACT_TYPE,
            PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_INTERFACE_ARTIFACT_TYPE,
            PORTABLE_PREDICATE_LANGUAGE_CORE_VERIFICATION_RESULT_ARTIFACT_TYPE,
        ],
        "validation_rule_ids": [
            "exact-fields-no-core-overrides-v1",
            "exact-recursive-json-types-and-resource-ceilings-v1",
            "core-and-interface-pins-exact-v1",
            "ordered-registries-unique-v1",
            "zero-to-bounded-authorities-locators-and-profile-claims-v1",
            "public-error-role-map-total-v1",
            "required-profile-parameters-present-additional-slots-bounded-v1",
            "every-additional-parameter-slot-referenced-by-an-extension-v1",
            "required-runtime-artifact-role-map-total-v1",
            "zero-to-bounded-specializations-with-row-local-parameter-arity-v1",
            "zero-to-bounded-interval-refinements-v1",
            "profile-primitives-from-closed-core-registries-v1",
            "profile-fields-exactly-once-typed-and-semantically-covered-v1",
            "profile-field-role-parameters-resolve-with-compatible-types-v1",
            "closed-locator-and-purpose-validation-primitives-v1",
            "purpose-relations-use-closed-data-only-primitives-v1",
            "purpose-member-fields-have-exact-locator-coverage-relations-v1",
            "direct-locator-path-fields-are-explicit-empty-placeholders-v1",
            "locator-shape-or-self-discriminator-unambiguous-v1",
            "reserved-artifact-types-and-role-namespaces-disjoint-v1",
            "profile-claims-bounded-and-all-false-v1",
            "fixed-counts-derived-v1",
        ],
    }


def portable_predicate_language_core_contract_tree() -> dict:
    """Return the exact profile-neutral semantic-core contract."""

    type_rows = _type_kind_schema_rows()
    encoding_rows = _value_encoding_rows()
    constructor_rows = _constructor_rows()
    operator_rows = _operator_rows()
    input_rows = _input_state_rows()
    requirement_rows = _resolution_requirement_rows()
    segment_rows = _path_segment_schema_rows()
    field_rows = _fixed_field_value_schema_rows()
    nested_rows = _artifact_nested_schema_rows()
    identity_rows = _artifact_identity_reference_rows()
    family_rows = _artifact_family_rows()
    interface = _profile_interface_tree()
    return {
        "artifact_family_rows": family_rows,
        "artifact_identity_reference_rows": identity_rows,
        "artifact_nested_schema_rows": nested_rows,
        "artifact_type": (
            PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_ARTIFACT_TYPE
        ),
        "constructor_contract": {
            "constructor_failure_mapping_rows": [
                {
                    "failure_rule_id": "required-optional",
                    "internal_condition_id": "OPTIONAL_REQUIRED_ABSENT",
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
                {
                    "failure_rule_id": "duplicate-key",
                    "internal_condition_id": "DUPLICATE_VALUE",
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
                {
                    "failure_rule_id": "invalid-interval",
                    "internal_condition_id": "INVALID_INTERVAL",
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
                {
                    "failure_rule_id": "exact-one-key",
                    "internal_condition_id": (
                        "KEY_SELECTION_CARDINALITY"
                    ),
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
                {
                    "failure_rule_id": "resource",
                    "internal_condition_id": (
                        "DERIVED_VALUE_RESOURCE_LIMIT"
                    ),
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
            ],
            "constructor_failure_precedence_rows": [
                {
                    "failure_class_id": "PROPAGATED_INPUT_FAULT",
                    "precedence_rank": 0,
                },
                {
                    "failure_class_id": "CONSTRUCTOR_SPECIFIC",
                    "precedence_rank": 1,
                },
                {
                    "failure_class_id": "OUTPUT_RESOURCE",
                    "precedence_rank": 2,
                },
            ],
            "constructor_rows": constructor_rows,
            "post_constructor_output_resource_rule_id": (
                "canonical-payload-and-all-resource-limits-before-"
                "availability-v1"
            ),
            "shaping_value_state_ids": [
                "VALUE_AVAILABLE",
                "HARD_FAILURE",
                "NOT_EVALUATED",
            ],
            "static_type_relation_mismatch_rule_id": (
                "reject-program-before-evaluation-v1"
            ),
        },
        "contract_parser_error_ids": [
            code.value for code in PortablePredicateLanguageCoreCode
        ],
        "digest_computation_id": (
            PORTABLE_PREDICATE_LANGUAGE_CORE_DIGEST_COMPUTATION_ID
        ),
        "encoding_id": PORTABLE_PREDICATE_LANGUAGE_CORE_ENCODING_ID,
        "field_value_json_kind_ids": [
            "array",
            "boolean",
            "integer",
            "object",
            "string",
        ],
        "field_value_schema_rows": field_rows,
        "fixed_counts": {
            "artifact_family_count": len(family_rows),
            "artifact_identity_reference_count": len(identity_rows),
            "artifact_nested_schema_count": len(nested_rows),
            "constructor_count": len(constructor_rows),
            "field_value_schema_count": len(field_rows),
            "field_value_schema_covered_field_count": sum(
                len(row["field_ids"]) for row in field_rows
            ),
            "input_state_count": len(input_rows),
            "internal_condition_count": 7,
            "internal_disposition_count": 4,
            "json_kind_count": 5,
            "operator_count": len(operator_rows),
            "path_segment_kind_count": len(segment_rows),
            "profile_interface_error_role_count": len(
                PORTABLE_PREDICATE_LANGUAGE_CORE_PUBLIC_ERROR_ROLE_IDS
            ),
            "profile_interface_locator_primitive_count": len(
                PORTABLE_PREDICATE_LANGUAGE_CORE_LOCATOR_PRIMITIVE_IDS
            ),
            "profile_interface_purpose_relation_primitive_count": len(
                PORTABLE_PREDICATE_LANGUAGE_CORE_PURPOSE_RELATION_PRIMITIVE_IDS
            ),
            "profile_field_semantic_role_count": len(
                interface["profile_field_semantic_role_rows"]
            ),
            "profile_parameter_slot_count": len(
                PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_PARAMETER_SLOT_IDS
            ),
            "resolution_requirement_count": len(requirement_rows),
            "type_kind_count": len(type_rows),
            "value_source_kind_count": 3,
        },
        "format_version": "1",
        "identifier_syntax": {
            "grammar": (
                PORTABLE_PREDICATE_LANGUAGE_CORE_IDENTIFIER_GRAMMAR
            ),
            "maximum_ascii_bytes": (
                MAXIMUM_PORTABLE_PREDICATE_IDENTIFIER_BYTES
            ),
            "minimum_ascii_bytes": 1,
            "nul_admitted": False,
            "unicode_admitted": False,
        },
        "implementation_status_id": PORTABLE_PREDICATE_LANGUAGE_CORE_STATUS,
        "nonclaim_state": {
            claim_id: False
            for claim_id in PORTABLE_PREDICATE_LANGUAGE_CORE_FALSE_CLAIM_IDS
        },
        "operator_contract": {
            "evaluation_order_rule_id": (
                "all-referenced-operands-and-children-evaluated-before-node-"
                "disposition-v1"
            ),
            "fault_origin_propagation_rule_id": (
                "retain-earliest-original-operand-and-node-origin-v1"
            ),
            "fault_precedence_rows": [
                {
                    "disposition_rank": 0,
                    "selected_disposition_id": "HARD_FAILURE",
                },
                {
                    "disposition_rank": 1,
                    "selected_disposition_id": "NOT_EVALUATED",
                },
            ],
            "fault_tie_break_field_ids": [
                "disposition_rank",
                "operand_declaration_index",
                "node_index",
            ],
            "global_node_index_rule_id": (
                "shaping-node-index-zero-through-s-minus-one-then-predicate-"
                "node-index-s-through-s-plus-p-minus-one-v1"
            ),
            "internal_condition_rows": [
                {
                    "internal_condition_id": "LOGICAL_FALSE",
                    "internal_disposition_id": "LOGICAL_FALSE",
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
                {
                    "internal_condition_id": "ARITHMETIC_RANGE",
                    "internal_disposition_id": "HARD_FAILURE",
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
                {
                    "internal_condition_id": "DUPLICATE_VALUE",
                    "internal_disposition_id": "HARD_FAILURE",
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
                {
                    "internal_condition_id": "INVALID_INTERVAL",
                    "internal_disposition_id": "HARD_FAILURE",
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
                {
                    "internal_condition_id": "KEY_SELECTION_CARDINALITY",
                    "internal_disposition_id": "HARD_FAILURE",
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
                {
                    "internal_condition_id": "OPTIONAL_REQUIRED_ABSENT",
                    "internal_disposition_id": "HARD_FAILURE",
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
                {
                    "internal_condition_id": (
                        "DERIVED_VALUE_RESOURCE_LIMIT"
                    ),
                    "internal_disposition_id": "HARD_FAILURE",
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
            ],
            "internal_disposition_ids": [
                "LOGICAL_TRUE",
                "LOGICAL_FALSE",
                "HARD_FAILURE",
                "NOT_EVALUATED",
            ],
            "interval_order_mode_ids": [
                "TOUCHING_ADMITTED",
                "STRICTLY_SEPARATED",
            ],
            "logical_fallback_rule_id": (
                "when-no-fault-operator-computes-logical-true-or-false-v1"
            ),
            "no_node_fault_index_value": 4294967295,
            "no_operand_fault_index_value": 4294967295,
            "operator_failure_mapping_rows": [
                {
                    "duplicate_or_range_rule_id": "duplicate-hard",
                    "internal_condition_id": "DUPLICATE_VALUE",
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
                {
                    "duplicate_or_range_rule_id": (
                        "checked-overflow-hard"
                    ),
                    "internal_condition_id": "ARITHMETIC_RANGE",
                    "public_error_role_id": "LOCAL_RULE_FAILED",
                },
            ],
            "operator_rows": operator_rows,
            "predicate_result_ids": ["PASS", "FAIL", "NOT_EVALUATED"],
            "public_error_role_resolution_rule_id": (
                "map-nonempty-role-through-selected-profile-total-error-role-"
                "row-to-exact-public-error-id-v1"
            ),
            "static_type_relation_mismatch_rule_id": (
                "reject-program-before-evaluation-v1"
            ),
            "truth_mapping_rows": [
                {
                    "executed_error_role_rule_id": "EMPTY",
                    "internal_condition_rule_id": "EMPTY",
                    "internal_disposition_id": "LOGICAL_TRUE",
                    "predicate_result_id": "PASS",
                },
                {
                    "executed_error_role_rule_id": (
                        "FIXED_LOCAL_RULE_FAILED"
                    ),
                    "internal_condition_rule_id": "FIXED_LOGICAL_FALSE",
                    "internal_disposition_id": "LOGICAL_FALSE",
                    "predicate_result_id": "FAIL",
                },
                {
                    "executed_error_role_rule_id": (
                        "PROPAGATE_SELECTED_ORIGIN_PUBLIC_ERROR"
                    ),
                    "internal_condition_rule_id": (
                        "PROPAGATE_SELECTED_ORIGIN_CONDITION_OR_EMPTY"
                    ),
                    "internal_disposition_id": "HARD_FAILURE",
                    "predicate_result_id": "FAIL",
                },
                {
                    "executed_error_role_rule_id": (
                        "PROPAGATE_SELECTED_ORIGIN_PUBLIC_ERROR"
                    ),
                    "internal_condition_rule_id": (
                        "PROPAGATE_SELECTED_ORIGIN_CONDITION_OR_EMPTY"
                    ),
                    "internal_disposition_id": "NOT_EVALUATED",
                    "predicate_result_id": "NOT_EVALUATED",
                },
            ],
        },
        "profile_interface": interface,
        "program_contract": {
            "applicability_id": "ALWAYS",
            "failure_oracle_id": "FAIL_CLOSED_FOUR_DISPOSITION_V1",
            "node_exact_field_ids": [
                "node_id",
                "operator_id",
                "ordered_operand_ids",
                "ordered_child_node_ids",
                "operator_configuration",
                "applicability_id",
                "failure_oracle_id",
            ],
            "shaping_node_exact_field_ids": [
                "shaping_node_id",
                "constructor_id",
                "output_operand_id",
                "ordered_input_operand_ids",
                "constructor_configuration",
                "applicability_id",
                "failure_oracle_id",
            ],
            "derived_operand_graph_rule_id": (
                "one-shaping-node-per-derived-output-prior-input-operand-"
                "indices-topological-acyclic-and-reachable-v1"
            ),
            "evaluation_result_claim_rule": {
                "conditionally_true_claim_id": (
                    "portable_typed_formula_evaluated"
                ),
                "condition_id": (
                    "validated-program-context-and-input-with-root-"
                    "disposition-computed-v1"
                ),
                "permanently_false_claim_ids": [
                    "empirical_result_established",
                    "runtime_evaluator_implemented",
                ],
            },
            "formula_core_artifact_role_id": "predicate-formula-core",
            "formula_core_cross_binding_rule_id": (
                "program-formula-core-identity-equals-recomputed-selected-"
                "profile-domain-digest-of-canonical-program-projection-v1"
            ),
            "formula_core_identity_computation_id": (
                PORTABLE_PREDICATE_LANGUAGE_CORE_DIGEST_COMPUTATION_ID
            ),
            "formula_core_schema_id": "predicate-formula-core-v1",
            "identity_uniqueness_rule_id": (
                "type-operand-shaping-node-and-predicate-node-ids-each-"
                "unique-with-disjoint-node-id-namespaces-v1"
            ),
            "self_comparison_tautology_admitted": False,
            "short_circuit_evaluation_admitted": False,
            "topological_nodes_required": True,
            "unreachable_nodes_admitted": False,
            "unused_operands_admitted": False,
            "whole_graph_root_rule_id": (
                "root-is-final-predicate-node-all-predicate-nodes-reachable-"
                "all-shaping-nodes-and-derived-operands-transitively-used-"
                "combined-depth-and-reference-ceilings-v1"
            ),
        },
        "resolution_contract": {
            "input_state_derivation_rule_id": (
                "profile-resolver-produces-source-outcome-core-maps-it-to-"
                "exact-closed-input-state-never-trust-caller-label-v1"
            ),
            "input_state_rows": input_rows,
            "resolution_requirement_rows": requirement_rows,
            "source_identity_rule_id": (
                "every-input-state-binds-source-artifact-kind-and-sha256-v1"
            ),
            "value_source_kind_ids": [
                "INPUT_RESOLVED",
                "PROGRAM_LITERAL",
                "DERIVED_TYPED_VALUE",
            ],
        },
        "resource_limits": {
            "artifact_bytes": 4 * 1024 * 1024,
            "collection_items": 4096,
            "graph_depth": 32,
            "identifier_bytes": 512,
            "json_depth": 32,
            "json_items": 65536,
            "locator_segments": 16,
            "node_fanout": 64,
            "node_references": 1024,
            "octet_value_bytes": 262144,
            "operand_rows": 512,
            "predicate_nodes": 256,
            "selector_key_components": 4,
            "shaping_nodes": 256,
            "tuple_components": 32,
            "type_depth": 8,
            "type_rows": 512,
            "typed_payload_bytes": 1024 * 1024,
        },
        "runtime_artifact_contract": {
            "artifact_family_registry_field_id": "artifact_family_rows",
            "artifact_identity_reference_registry_field_id": (
                "artifact_identity_reference_rows"
            ),
            "artifact_nested_schema_registry_field_id": (
                "artifact_nested_schema_rows"
            ),
            "artifact_role_binding_rule_id": (
                "each-required-family-role-resolves-exactly-once-through-"
                "selected-profile-artifact-domain-rows-v1"
            ),
            "caller_supplied_result_boolean_admitted": False,
            "evaluation_nonce_rule_id": (
                "exactly-thirty-two-nonzero-bytes-lowercase-hex-v1"
            ),
            "field_value_schema_registry_field_id": (
                "field_value_schema_rows"
            ),
            "identity_reference_rule_id": (
                "program-pins-formula-core-context-pins-program-input-pins-"
                "program-and-context-result-pins-program-context-and-input-v1"
            ),
            "profile_identity_pin_rule_id": (
                "every-runtime-artifact-pins-exact-selected-profile-"
                "contract-domain-sha256-v1"
            ),
            "result_error_mapping_rule_id": (
                "nonempty-public-error-role-maps-through-selected-profile-"
                "total-role-map-before-result-serialization-v1"
            ),
        },
        "selector_contract": {
            "path_segment_schema_rows": segment_rows,
            "schema_list_wildcard_admitted": False,
        },
        "type_contract": {
            "canonical_value_hex_rule": (
                "lowercase-even-length-complete-canonical-payload-v1"
            ),
            "collection_count_encoding_id": "unsigned-u64be-v1",
            "digest_semantics_ids": [
                "PLAIN_SHA256",
                "DOMAIN_SEPARATED_SHA256",
            ],
            "implicit_conversion_admitted": False,
            "keyed_table_payload_validation_rule_id": (
                "complete-framing-exact-row-type-and-unique-canonical-keys-v1"
            ),
            "nominal_type_equality_required": True,
            "recursive_types_admitted": False,
            "topological_type_rows_required": True,
            "type_kind_schema_rows": type_rows,
            "typed_identity_preimage_computation_id": (
                PORTABLE_PREDICATE_LANGUAGE_CORE_TYPED_IDENTITY_COMPUTATION_ID
            ),
            "typed_value_identity_sha256_computation_id": (
                "plain-sha256-of-exact-typed-identity-preimage-v1"
            ),
            "u64_interval_payload_validation_rule_id": (
                "complete-framing-exact-u64-endpoints-and-start-not-after-end-"
                "v1"
            ),
            "value_encoding_rows": encoding_rows,
        },
        "validation_scope_id": (
            PORTABLE_PREDICATE_LANGUAGE_CORE_VALIDATION_SCOPE
        ),
    }


def portable_predicate_language_core_contract_bytes() -> bytes:
    """Return canonical bytes for the exact semantic core."""

    return _canonical_json(portable_predicate_language_core_contract_tree())


def portable_predicate_language_core_contract_plain_sha256() -> str:
    """Return the ordinary SHA-256 of the canonical core."""

    return hashlib.sha256(
        portable_predicate_language_core_contract_bytes()
    ).hexdigest()


def portable_predicate_language_core_contract_sha256() -> str:
    """Return the length-bound domain-separated core identity."""

    return _domain_sha256(
        PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_DIGEST_DOMAIN,
        portable_predicate_language_core_contract_bytes(),
    )


def portable_predicate_language_core_profile_interface_tree() -> dict:
    """Return the exact closed profile-interface subsection."""

    return _profile_interface_tree()


def portable_predicate_language_core_profile_interface_sha256() -> str:
    """Return the length-bound identity of the profile interface."""

    return _domain_sha256(
        PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_INTERFACE_ARTIFACT_TYPE,
        _canonical_json(
            portable_predicate_language_core_profile_interface_tree()
        ),
    )


def parse_portable_predicate_language_core_contract(value: bytes) -> dict:
    """Strictly parse the one exact semantic-core contract."""

    if type(value) is not bytes:
        _fail(PortablePredicateLanguageCoreCode.INPUT_TYPE)
    if (
        not value
        or len(value)
        > MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_ARTIFACT_BYTES
    ):
        _fail(PortablePredicateLanguageCoreCode.INPUT_RESOURCE)
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
        _fail(PortablePredicateLanguageCoreCode.JSON_INVALID)
    json_status = _bounded_exact_json_status(decoded)
    if json_status == "schema-invalid":
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
    if json_status != "valid":
        _fail(PortablePredicateLanguageCoreCode.INPUT_RESOURCE)
    expected = portable_predicate_language_core_contract_tree()
    if not _same_exact(decoded, expected):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
    if value != portable_predicate_language_core_contract_bytes():
        _fail(PortablePredicateLanguageCoreCode.CANONICAL_MISMATCH)
    return expected


def _exact_keys(value: object, keys: tuple) -> bool:
    return type(value) is dict and set(value) == set(keys)


def _validate_portable_predicate_profile_tree_impl(
    profile_tree: object,
) -> dict:
    """Validate one profile using only the closed core interface.

    This is a structural interface validator, not a profile-specific known
    answer and not a runtime evaluator.
    """

    if type(profile_tree) is not dict:
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
    json_status = _bounded_exact_json_status(profile_tree)
    if json_status == "schema-invalid":
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
    if json_status != "valid":
        _fail(PortablePredicateLanguageCoreCode.INPUT_RESOURCE)
    _canonical_json(profile_tree)

    interface = portable_predicate_language_core_profile_interface_tree()
    maxima = interface["maximum_profile_registry_counts"]
    expected_fields = tuple(interface["closed_profile_exact_field_ids"])
    if not _exact_keys(profile_tree, expected_fields):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
    tree = profile_tree
    scalar_identifier_fields = (
        "artifact_type",
        "digest_computation_id",
        "encoding_id",
        "format_version",
        "implementation_status_id",
        "profile_class_id",
        "profile_id",
        "profile_interface_id",
        "profile_verification_result_artifact_type",
        "validation_scope_id",
    )
    if (
        any(not _is_identifier(tree[field]) for field in scalar_identifier_fields)
        or tree["format_version"] != "1"
        or tree["encoding_id"]
        != PORTABLE_PREDICATE_LANGUAGE_CORE_ENCODING_ID
        or tree["digest_computation_id"]
        != PORTABLE_PREDICATE_LANGUAGE_CORE_DIGEST_COMPUTATION_ID
        or not _is_sha256(tree["core_contract_sha256"])
        or tree["core_contract_sha256"]
        != portable_predicate_language_core_contract_sha256()
        or not _is_sha256(tree["core_profile_interface_sha256"])
        or tree["core_profile_interface_sha256"]
        != portable_predicate_language_core_profile_interface_sha256()
        or tree["profile_interface_id"] != interface["profile_interface_id"]
        or not _unique_identifiers(
            tree["authority_class_ids"], nonempty=False
        )
        or len(tree["authority_class_ids"])
        > maxima["authority_class_ids"]
        or not _unique_identifiers(tree["public_error_ids"])
        or len(tree["public_error_ids"]) > maxima["public_error_ids"]
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    anchors = tree["anchor_contract_rows"]
    if (
        type(anchors) is not list
        or len(anchors) > maxima["anchor_contract_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "anchor_role_id",
                    "artifact_type_id",
                    "contract_sha256",
                ),
            )
            or not _is_identifier(row["anchor_role_id"])
            or not _is_identifier(row["artifact_type_id"])
            or not _is_sha256(row["contract_sha256"])
            for row in anchors
        )
        or len([row["anchor_role_id"] for row in anchors])
        != len(set(row["anchor_role_id"] for row in anchors))
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    domains = tree["artifact_domain_rows"]
    if (
        type(domains) is not list
        or not domains
        or len(domains) > maxima["artifact_domain_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "artifact_role_id",
                    "artifact_type_id",
                    "digest_domain_id",
                    "identity_semantics_id",
                ),
            )
            or not _is_identifier(row["artifact_role_id"])
            or not _is_identifier(row["artifact_type_id"])
            or not _is_identifier(row["digest_domain_id"])
            or row["digest_domain_id"] != row["artifact_type_id"]
            or row["identity_semantics_id"]
            != "DOMAIN_SEPARATED_SHA256"
            for row in domains
        )
        or len([row["artifact_role_id"] for row in domains])
        != len(set(row["artifact_role_id"] for row in domains))
        or len([row["artifact_type_id"] for row in domains])
        != len(set(row["artifact_type_id"] for row in domains))
        or [
            row["artifact_role_id"]
            for row in domains[
                : len(
                    PORTABLE_PREDICATE_LANGUAGE_CORE_REQUIRED_ARTIFACT_ROLE_IDS
                )
            ]
        ]
        != list(
            PORTABLE_PREDICATE_LANGUAGE_CORE_REQUIRED_ARTIFACT_ROLE_IDS
        )
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
    anchor_role_ids = {row["anchor_role_id"] for row in anchors}
    artifact_role_ids = {row["artifact_role_id"] for row in domains}
    reserved_artifact_types = [
        tree["artifact_type"],
        tree["profile_verification_result_artifact_type"],
        *interface["reserved_core_metadata_artifact_type_ids"],
        *[row["artifact_type_id"] for row in anchors],
        *[row["artifact_type_id"] for row in domains],
    ]
    if (
        anchor_role_ids.intersection(artifact_role_ids)
        or anchor_role_ids.intersection(
            PORTABLE_PREDICATE_LANGUAGE_CORE_RESERVED_METADATA_ARTIFACT_ROLE_IDS
        )
        or artifact_role_ids.intersection(
            PORTABLE_PREDICATE_LANGUAGE_CORE_RESERVED_METADATA_ARTIFACT_ROLE_IDS
        )
        or len(reserved_artifact_types) != len(set(reserved_artifact_types))
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    error_rows = tree["public_error_role_rows"]
    required_roles = list(
        PORTABLE_PREDICATE_LANGUAGE_CORE_PUBLIC_ERROR_ROLE_IDS
    )
    if (
        type(error_rows) is not list
        or any(type(row) is not dict for row in error_rows)
        or [row.get("public_error_role_id") for row in error_rows]
        != required_roles
        or any(
            not _exact_keys(
                row,
                ("public_error_role_id", "public_error_id"),
            )
            or not _is_identifier(row["public_error_role_id"])
            or row["public_error_id"] not in tree["public_error_ids"]
            for row in error_rows
        )
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    parameter_rows = tree["profile_parameter_rows"]
    required_slots = list(
        PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_PARAMETER_SLOT_IDS
    )
    if (
        type(parameter_rows) is not list
        or len(parameter_rows) < len(required_slots)
        or len(parameter_rows) > maxima["profile_parameter_rows"]
        or any(type(row) is not dict for row in parameter_rows)
        or [
            row.get("parameter_slot_id")
            for row in parameter_rows[: len(required_slots)]
        ]
        != required_slots
        or any(
            not _exact_keys(
                row,
                ("parameter_slot_id", "parameter_value_id"),
            )
            or not _is_identifier(row["parameter_slot_id"])
            or not _is_identifier(row["parameter_value_id"])
            for row in parameter_rows
        )
        or len([row["parameter_slot_id"] for row in parameter_rows])
        != len(set(row["parameter_slot_id"] for row in parameter_rows))
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
    declared_parameter_slots = {
        row["parameter_slot_id"] for row in parameter_rows
    }

    locators = tree["locator_extension_rows"]
    if (
        type(locators) is not list
        or len(locators) > maxima["locator_extension_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "exact_configuration_field_ids",
                    "exact_empty_placeholder_field_ids",
                    "locator_kind_id",
                    "locator_primitive_id",
                    "validation_primitive_id",
                    "validation_rule_id",
                ),
            )
            or not _is_identifier(row["locator_kind_id"])
            or row["locator_primitive_id"]
            not in PORTABLE_PREDICATE_LANGUAGE_CORE_LOCATOR_PRIMITIVE_IDS
            or not _unique_identifiers(
                row["exact_configuration_field_ids"],
                nonempty=False,
            )
            or not _unique_identifiers(
                row["exact_empty_placeholder_field_ids"],
                nonempty=False,
            )
            or not set(
                row["exact_empty_placeholder_field_ids"]
            ).issubset(row["exact_configuration_field_ids"])
            or row["validation_primitive_id"]
            != interface["profile_locator_validation_primitive_id"]
            or not _is_identifier(row["validation_rule_id"])
            for row in locators
        )
        or len([row["locator_kind_id"] for row in locators])
        != len(set(row["locator_kind_id"] for row in locators))
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    purposes = tree["program_purpose_rows"]
    relation_primitive_ids = set(
        PORTABLE_PREDICATE_LANGUAGE_CORE_PURPOSE_RELATION_PRIMITIVE_IDS
    )
    if (
        type(purposes) is not list
        or not purposes
        or any(type(row) is not dict for row in purposes)
        or len(purposes) > maxima["program_purpose_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "exact_binding_field_ids",
                    "program_purpose_id",
                    "purpose_relation_rows",
                    "validation_primitive_id",
                    "validation_rule_id",
                ),
            )
            or not _unique_identifiers(
                row["exact_binding_field_ids"], nonempty=False
            )
            or not _is_identifier(row["program_purpose_id"])
            or type(row["purpose_relation_rows"]) is not list
            or not _is_identifier(row["validation_rule_id"])
            for row in purposes
        )
        or len([row["program_purpose_id"] for row in purposes])
        != len(set(row["program_purpose_id"] for row in purposes))
        or purposes[0]["program_purpose_id"]
        != next(
            row["parameter_value_id"]
            for row in parameter_rows
            if row["parameter_slot_id"] == "primary-program-purpose-id"
        )
        or any(
            row["validation_primitive_id"]
            != interface["profile_program_purpose_validation_primitive_id"]
            for row in purposes
        )
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
    purpose_relation_rows = [
        relation
        for purpose in purposes
        for relation in purpose["purpose_relation_rows"]
    ]
    purpose_equality_rows = [
        equality
        for relation in purpose_relation_rows
        if type(relation) is dict
        and relation.get("relation_primitive_id")
        == "exactly-one-pinned-anchor-row-canonical-equality-v1"
        for equality in (
            relation.get("ordered_equality_rows", [])
            if type(relation.get("ordered_equality_rows")) is list
            else []
        )
    ]
    if (
        len(purpose_relation_rows)
        > maxima["program_purpose_relation_rows"]
        or len(purpose_equality_rows)
        > maxima["program_purpose_equality_rows"]
        or any(type(row) is not dict for row in purpose_relation_rows)
        or any(
            not _is_identifier(row.get("relation_primitive_id"))
            or row.get("relation_primitive_id")
            not in relation_primitive_ids
            for row in purpose_relation_rows
        )
        or any(
            not _is_identifier(row.get("relation_id"))
            for row in purpose_relation_rows
        )
        or len(
            [row.get("relation_id") for row in purpose_relation_rows]
        )
        != len(
            set(row.get("relation_id") for row in purpose_relation_rows)
        )
        or any(
            [
                row.get("relation_id")
                for row in purpose["purpose_relation_rows"]
            ]
            != sorted(
                row.get("relation_id")
                for row in purpose["purpose_relation_rows"]
            )
            for purpose in purposes
        )
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
    for purpose in purposes:
        binding_field_ids = purpose["exact_binding_field_ids"]
        binding_field_index = {
            field_id: index
            for index, field_id in enumerate(binding_field_ids)
        }
        for relation in purpose["purpose_relation_rows"]:
            primitive_id = relation["relation_primitive_id"]
            if primitive_id == (
                "exactly-one-pinned-anchor-row-canonical-equality-v1"
            ):
                if not _exact_keys(
                    relation,
                    (
                        "anchor_role_id",
                        "anchor_row_array_path_ids",
                        "ordered_equality_rows",
                        "relation_id",
                        "relation_primitive_id",
                    ),
                ):
                    _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
                path_ids = relation["anchor_row_array_path_ids"]
                equality_rows = relation["ordered_equality_rows"]
                if (
                    not _is_identifier(relation["anchor_role_id"])
                    or relation["anchor_role_id"] not in anchor_role_ids
                    or not _is_identifier(relation["relation_id"])
                    or type(path_ids) is not list
                    or not 1 <= len(path_ids) <= 16
                    or any(not _is_identifier(item) for item in path_ids)
                    or type(equality_rows) is not list
                    or not 1 <= len(equality_rows) <= 64
                    or any(
                        not _exact_keys(
                            equality,
                            (
                                "anchor_row_value_path_ids",
                                "purpose_binding_field_id",
                            ),
                        )
                        or type(equality["anchor_row_value_path_ids"])
                        is not list
                        or not 1
                        <= len(equality["anchor_row_value_path_ids"])
                        <= 16
                        or any(
                            not _is_identifier(item)
                            for item in equality[
                                "anchor_row_value_path_ids"
                            ]
                        )
                        or not _is_identifier(
                            equality["purpose_binding_field_id"]
                        )
                        or equality["purpose_binding_field_id"]
                        not in binding_field_index
                        for equality in equality_rows
                    )
                    or len(
                        [
                            equality["purpose_binding_field_id"]
                            for equality in equality_rows
                        ]
                    )
                    != len(
                        {
                            equality["purpose_binding_field_id"]
                            for equality in equality_rows
                        }
                    )
                    or len(
                        [
                            tuple(equality["anchor_row_value_path_ids"])
                            for equality in equality_rows
                        ]
                    )
                    != len(
                        {
                            tuple(equality["anchor_row_value_path_ids"])
                            for equality in equality_rows
                        }
                    )
                    or [
                        binding_field_index[
                            equality["purpose_binding_field_id"]
                        ]
                        for equality in equality_rows
                    ]
                    != sorted(
                        binding_field_index[
                            equality["purpose_binding_field_id"]
                        ]
                        for equality in equality_rows
                    )
                ):
                    _fail(
                        PortablePredicateLanguageCoreCode.SCHEMA_INVALID
                    )
            elif primitive_id == (
                "purpose-identifiers-exactly-covered-by-input-locators-v1"
            ):
                if (
                    not _exact_keys(
                        relation,
                        (
                            "locator_value_field_id",
                            "purpose_binding_field_id",
                            "relation_id",
                            "relation_primitive_id",
                        ),
                    )
                    or not _is_identifier(relation["relation_id"])
                    or not _is_identifier(
                        relation["locator_value_field_id"]
                    )
                    or not _is_identifier(
                        relation["purpose_binding_field_id"]
                    )
                    or relation["purpose_binding_field_id"]
                    not in binding_field_index
                ):
                    _fail(
                        PortablePredicateLanguageCoreCode.SCHEMA_INVALID
                    )
            else:
                _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    profile_field_rows = tree["profile_field_schema_rows"]
    semantic_role_by_id = {
        row["semantic_role_id"]: row
        for row in interface["profile_field_semantic_role_rows"]
    }
    core_value_schema_by_field = {
        field_id: row["value_schema_id"]
        for row in _fixed_field_value_schema_rows()
        for field_id in row["field_ids"]
    }
    locator_field_sets = [
        set(row["exact_configuration_field_ids"]) for row in locators
    ]
    purpose_field_sets = [
        set(row["exact_binding_field_ids"]) for row in purposes
    ]
    locator_field_ids = set().union(*locator_field_sets) if locators else set()
    purpose_field_ids = set().union(*purpose_field_sets)
    referenced_profile_field_ids = locator_field_ids | purpose_field_ids
    if (
        type(profile_field_rows) is not list
        or len(profile_field_rows) > maxima["profile_field_schema_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "field_id",
                    "role_parameter_id",
                    "semantic_role_id",
                    "value_schema_id",
                ),
            )
            or not _is_identifier(row["field_id"])
            or not _is_identifier(row["role_parameter_id"])
            or not _is_identifier(row["semantic_role_id"])
            or row["semantic_role_id"] not in semantic_role_by_id
            or row["value_schema_id"]
            not in interface["admitted_profile_field_value_schema_ids"]
            or row["value_schema_id"]
            not in semantic_role_by_id[row["semantic_role_id"]][
                "admitted_value_schema_ids"
            ]
            for row in profile_field_rows
        )
        or len([row["field_id"] for row in profile_field_rows])
        != len(set(row["field_id"] for row in profile_field_rows))
        or [row["field_id"] for row in profile_field_rows]
        != sorted(row["field_id"] for row in profile_field_rows)
        or {row["field_id"] for row in profile_field_rows}
        != referenced_profile_field_ids
        or any(
            row["field_id"] in core_value_schema_by_field
            and row["value_schema_id"]
            != core_value_schema_by_field[row["field_id"]]
            for row in profile_field_rows
        )
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
    profile_field_by_id = {
        row["field_id"]: row for row in profile_field_rows
    }

    no_parameter_role_ids = {
        "opaque-identifier",
        "ordered-unique-identifiers",
        "locator-kind-self",
        "path-segments",
        "nonnegative-count",
        "typed-key-components",
        "prior-input-resolved-operand",
    }
    artifact_parameter_role_ids = {
        "artifact-type-for-role",
        "artifact-identity-semantics-for-role",
        "artifact-identity-sha256-for-role",
    }
    anchor_parameter_role_ids = {
        "anchor-artifact-type-for-role",
        "anchor-contract-sha256-for-role",
    }

    def fields_share_one_group(
        field_id: str,
        other_field_id: str,
        groups: list,
    ) -> bool:
        return any(
            {field_id, other_field_id}.issubset(group) for group in groups
        )

    for row in profile_field_rows:
        field_id = row["field_id"]
        parameter_id = row["role_parameter_id"]
        role_id = row["semantic_role_id"]
        if role_id in no_parameter_role_ids:
            valid_parameter = parameter_id == "NONE"
        elif role_id in artifact_parameter_role_ids:
            valid_parameter = parameter_id in artifact_role_ids
        elif role_id in anchor_parameter_role_ids:
            valid_parameter = parameter_id in anchor_role_ids
        elif role_id == "identifier-member-of-purpose-field":
            target = profile_field_by_id.get(parameter_id)
            valid_parameter = (
                field_id in locator_field_ids
                and parameter_id != field_id
                and parameter_id in purpose_field_ids
                and target is not None
                and target["value_schema_id"]
                == "ordered-identifier-array-v1"
                and all(
                    parameter_id in purpose_field_set
                    for purpose_field_set in purpose_field_sets
                )
            )
        elif role_id == "index-below-field":
            target = profile_field_by_id.get(parameter_id)
            valid_parameter = (
                parameter_id != field_id
                and target is not None
                and target["value_schema_id"]
                == "nonnegative-index-or-count-integer-v1"
                and target["semantic_role_id"] == "nonnegative-count"
                and fields_share_one_group(
                    field_id,
                    parameter_id,
                    locator_field_sets + purpose_field_sets,
                )
            )
        else:
            valid_parameter = False
        placement_is_valid = (
            role_id
            not in {
                "locator-kind-self",
                "path-segments",
                "typed-key-components",
                "prior-input-resolved-operand",
                "identifier-member-of-purpose-field",
            }
            or field_id in locator_field_ids
        )
        if not valid_parameter or not placement_is_valid:
            _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    selection_role_ids = {
        "path-segments",
        "nonnegative-count",
        "index-below-field",
        "typed-key-components",
        "prior-input-resolved-operand",
    }
    locator_constraint_by_primitive = {
        row["locator_primitive_id"]: row
        for row in interface[
            "locator_primitive_profile_field_constraint_rows"
        ]
    }
    for locator in locators:
        configuration_field_ids = locator["exact_configuration_field_ids"]
        placeholder_field_ids = locator[
            "exact_empty_placeholder_field_ids"
        ]
        placeholder_field_id_set = set(placeholder_field_ids)
        locator_field_rows = [
            profile_field_by_id[field_id]
            for field_id in configuration_field_ids
        ]
        effective_locator_field_rows = [
            row
            for row in locator_field_rows
            if row["field_id"] not in placeholder_field_id_set
        ]
        locator_role_ids = [
            row["semantic_role_id"] for row in effective_locator_field_rows
        ]
        primitive_id = locator["locator_primitive_id"]
        constraint = locator_constraint_by_primitive[primitive_id]
        admitted_selection_role_ids = set(
            constraint["admitted_selection_semantic_role_ids"]
        )
        required_role_counts = {
            row["semantic_role_id"]: row["required_count"]
            for row in constraint["required_semantic_role_count_rows"]
        }
        path_field_ids = [
            row["field_id"]
            for row in locator_field_rows
            if row["semantic_role_id"] == "path-segments"
        ]
        if (
            placeholder_field_ids
            != [
                field_id
                for field_id in configuration_field_ids
                if field_id in placeholder_field_id_set
            ]
            or len(placeholder_field_ids) > 1
            or any(
                profile_field_by_id[field_id]["semantic_role_id"]
                != "path-segments"
                or profile_field_by_id[field_id]["value_schema_id"]
                != "ordered-exact-object-row-array-v1"
                for field_id in placeholder_field_ids
            )
            or (
                primitive_id == "direct-bound-value"
                and placeholder_field_ids != path_field_ids
            )
            or (
                primitive_id != "direct-bound-value"
                and bool(placeholder_field_ids)
            )
            or set(locator_role_ids).intersection(selection_role_ids)
            - admitted_selection_role_ids
            or any(
                locator_role_ids.count(role_id) != required_count
                for role_id, required_count in (
                    required_role_counts.items()
                )
            )
            or any(
                locator_role_ids.count(role_id) > 1
                for role_id in admitted_selection_role_ids
            )
            or any(
                row["role_parameter_id"]
                not in {
                    candidate["field_id"]
                    for candidate in effective_locator_field_rows
                    if candidate["semantic_role_id"]
                    == "nonnegative-count"
                }
                for row in effective_locator_field_rows
                if row["semantic_role_id"] == "index-below-field"
            )
        ):
            _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    purpose_member_field_rows = [
        row
        for row in profile_field_rows
        if row["semantic_role_id"] == "identifier-member-of-purpose-field"
    ]
    for purpose in purposes:
        coverage_relations = [
            relation
            for relation in purpose["purpose_relation_rows"]
            if relation["relation_primitive_id"]
            == "purpose-identifiers-exactly-covered-by-input-locators-v1"
        ]
        for relation in coverage_relations:
            locator_field = profile_field_by_id.get(
                relation["locator_value_field_id"]
            )
            purpose_field = profile_field_by_id.get(
                relation["purpose_binding_field_id"]
            )
            if (
                locator_field is None
                or purpose_field is None
                or relation["locator_value_field_id"]
                not in locator_field_ids
                or locator_field["semantic_role_id"]
                != "identifier-member-of-purpose-field"
                or locator_field["value_schema_id"]
                != "strict-identifier-string-v1"
                or locator_field["role_parameter_id"]
                != relation["purpose_binding_field_id"]
                or purpose_field["semantic_role_id"]
                != "ordered-unique-identifiers"
                or purpose_field["value_schema_id"]
                != "ordered-identifier-array-v1"
            ):
                _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
        for member_field in purpose_member_field_rows:
            if sum(
                relation["locator_value_field_id"]
                == member_field["field_id"]
                and relation["purpose_binding_field_id"]
                == member_field["role_parameter_id"]
                for relation in coverage_relations
            ) != 1:
                _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    locator_rows_by_field_shape = {}
    for locator in locators:
        shape = frozenset(locator["exact_configuration_field_ids"])
        locator_rows_by_field_shape.setdefault(shape, []).append(locator)
    for shape, shape_locators in locator_rows_by_field_shape.items():
        if len(shape_locators) > 1 and sum(
            profile_field_by_id[field_id]["semantic_role_id"]
            == "locator-kind-self"
            for field_id in shape
        ) != 1:
            _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    specializations = tree["operator_specialization_rows"]
    primitive_by_id = {
        row["primitive_id"]: row
        for row in interface["profile_bound_operator_primitive_rows"]
    }
    if (
        type(specializations) is not list
        or len(specializations) > maxima["operator_specialization_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "exposed_operator_id",
                    "operand_source_rule_id",
                    "ordered_parameter_slot_ids",
                    "primitive_id",
                    "type_and_truth_rule_id",
                ),
            )
            or not _is_identifier(row["primitive_id"])
            or row["primitive_id"] not in primitive_by_id
            or not _is_identifier(row["exposed_operator_id"])
            or row["exposed_operator_id"]
            in PORTABLE_PREDICATE_LANGUAGE_CORE_OPERATOR_IDS
            or not _unique_identifiers(
                row["ordered_parameter_slot_ids"],
                nonempty=False,
            )
            or not set(row["ordered_parameter_slot_ids"]).issubset(
                declared_parameter_slots
            )
            or set(row["ordered_parameter_slot_ids"]).intersection(
                required_slots
            )
            or len(row["ordered_parameter_slot_ids"])
            < primitive_by_id[row["primitive_id"]][
                "minimum_parameter_slot_count"
            ]
            or len(row["ordered_parameter_slot_ids"])
            > primitive_by_id[row["primitive_id"]][
                "maximum_parameter_slot_count"
            ]
            or row["operand_source_rule_id"]
            != primitive_by_id[row["primitive_id"]][
                "operand_source_rule_id"
            ]
            or row["type_and_truth_rule_id"]
            != primitive_by_id[row["primitive_id"]][
                "type_and_truth_rule_id"
            ]
            for row in specializations
        )
        or len([row["exposed_operator_id"] for row in specializations])
        != len(set(row["exposed_operator_id"] for row in specializations))
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    refinements = tree["interval_refinement_rows"]
    refinement_primitive_ids = {
        row["refinement_primitive_id"]
        for row in interface["interval_refinement_primitive_rows"]
    }
    if (
        type(refinements) is not list
        or len(refinements) > maxima["interval_refinement_rows"]
        or any(
            not _exact_keys(
                row,
                (
                    "endpoint_parameter_slot_id",
                    "exposed_refinement_id",
                    "refinement_primitive_id",
                    "validation_rule_id",
                ),
            )
            or not _is_identifier(row["refinement_primitive_id"])
            or row["refinement_primitive_id"]
            not in refinement_primitive_ids
            or not _is_identifier(row["endpoint_parameter_slot_id"])
            or row["endpoint_parameter_slot_id"]
            not in declared_parameter_slots
            or row["endpoint_parameter_slot_id"] in required_slots
            or not _is_identifier(row["exposed_refinement_id"])
            or not _is_identifier(row["validation_rule_id"])
            for row in refinements
        )
        or len([row["exposed_refinement_id"] for row in refinements])
        != len(set(row["exposed_refinement_id"] for row in refinements))
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    referenced_extension_slots = {
        slot_id
        for row in specializations
        for slot_id in row["ordered_parameter_slot_ids"]
    } | {
        row["endpoint_parameter_slot_id"] for row in refinements
    }
    if referenced_extension_slots != (
        declared_parameter_slots - set(required_slots)
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    claims = tree["nonclaim_state"]
    if (
        type(claims) is not dict
        or len(claims) > maxima["nonclaim_state"]
        or any(not _is_identifier(key) for key in claims)
        or any(type(value) is not bool or value for value in claims.values())
    ):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)

    expected_counts = {
        "anchor_contract_count": len(anchors),
        "artifact_domain_count": len(domains),
        "authority_class_count": len(tree["authority_class_ids"]),
        "interval_refinement_count": len(refinements),
        "locator_extension_count": len(locators),
        "operator_specialization_count": len(specializations),
        "profile_claim_count": len(claims),
        "profile_field_schema_count": len(profile_field_rows),
        "profile_parameter_count": len(parameter_rows),
        "program_purpose_relation_count": len(purpose_relation_rows),
        "program_purpose_count": len(purposes),
        "public_error_count": len(tree["public_error_ids"]),
        "public_error_role_count": len(error_rows),
    }
    if not _same_exact(tree["fixed_counts"], expected_counts):
        _fail(PortablePredicateLanguageCoreCode.SCHEMA_INVALID)
    return tree


def validate_portable_predicate_profile_tree(profile_tree: object) -> dict:
    """Validate one profile and contain malformed-tree implementation leaks."""

    try:
        return _validate_portable_predicate_profile_tree_impl(profile_tree)
    except PortablePredicateLanguageCoreError:
        raise
    except (
        AttributeError,
        IndexError,
        KeyError,
        RuntimeError,
        StopIteration,
        TypeError,
        ValueError,
    ):
        raise PortablePredicateLanguageCoreError(
            PortablePredicateLanguageCoreCode.SCHEMA_INVALID
        ) from None


def _validate_contract_coherence() -> None:
    tree = portable_predicate_language_core_contract_tree()
    counts = tree["fixed_counts"]
    type_rows = tree["type_contract"]["type_kind_schema_rows"]
    encoding_rows = tree["type_contract"]["value_encoding_rows"]
    constructor_contract = tree["constructor_contract"]
    constructors = constructor_contract["constructor_rows"]
    operator_contract = tree["operator_contract"]
    operators = operator_contract["operator_rows"]
    input_rows = tree["resolution_contract"]["input_state_rows"]
    interface = tree["profile_interface"]
    profile_field_semantic_rows = interface[
        "profile_field_semantic_role_rows"
    ]
    locator_field_constraint_rows = interface[
        "locator_primitive_profile_field_constraint_rows"
    ]
    purpose_relation_primitive_rows = interface[
        "program_purpose_relation_primitive_rows"
    ]
    families = tree["artifact_family_rows"]
    nested_rows = tree["artifact_nested_schema_rows"]
    identity_rows = tree["artifact_identity_reference_rows"]
    field_rows = tree["field_value_schema_rows"]

    def unique(values: list) -> bool:
        return len(values) == len(set(values))

    def field_id_lists_are_unique(value: object) -> bool:
        stack = [value]
        while stack:
            current = stack.pop()
            if type(current) is dict:
                for key, item in current.items():
                    if (
                        key.endswith("field_ids")
                        and type(item) is list
                        and not unique(item)
                    ):
                        return False
                    stack.append(item)
            elif type(current) is list:
                stack.extend(current)
        return True

    def collect_exact_field_ids(value: object) -> set:
        result = set()
        stack = [value]
        while stack:
            current = stack.pop()
            if type(current) is dict:
                for key, item in current.items():
                    if (
                        "exact" in key
                        and key.endswith("field_ids")
                        and type(item) is list
                    ):
                        result.update(item)
                    stack.append(item)
            elif type(current) is list:
                stack.extend(current)
        return result

    runtime_schema_sources = [
        families,
        nested_rows,
        type_rows,
        tree["selector_contract"]["path_segment_schema_rows"],
        constructors,
        operators,
    ]
    exact_runtime_field_ids = set()
    for source in runtime_schema_sources:
        exact_runtime_field_ids.update(collect_exact_field_ids(source))
    covered_field_ids = [
        field_id for row in field_rows for field_id in row["field_ids"]
    ]
    nested_schema_ids = [row["schema_id"] for row in nested_rows]
    nested_schema_references = [
        schema_id
        for family in families
        for schema_id in family["nested_schema_ids"]
    ]
    source_kind_schema = next(
        row
        for row in nested_rows
        if row["schema_id"] == "program-operand-row-by-source-kind-v1"
    )
    fault_origin_schema = next(
        row
        for row in nested_rows
        if row["schema_id"] == "selected-fault-origin-v1"
    )
    constructor_hard_rules = {
        row["failure_rule_id"]
        for row in constructors
        if row["failure_rule_id"] != "none"
    }
    constructor_mapping_rows = constructor_contract[
        "constructor_failure_mapping_rows"
    ]
    operator_hard_rules = {
        row["duplicate_or_range_rule_id"]
        for row in operators
        if row["duplicate_or_range_rule_id"]
        in {"duplicate-hard", "checked-overflow-hard"}
    }
    operator_mapping_rows = operator_contract[
        "operator_failure_mapping_rows"
    ]
    forbidden = (
        b"linux",
        b"confinement",
        b"tessera",
        b"53a",
        b"errno",
        b"pidfd",
        b"cgroup",
        b"syscall",
    )
    canonical_raw = _canonical_json(tree)
    lower_raw = canonical_raw.lower()
    if (
        counts
        != {
            "artifact_family_count": len(families),
            "artifact_identity_reference_count": len(identity_rows),
            "artifact_nested_schema_count": len(nested_rows),
            "constructor_count": len(constructors),
            "field_value_schema_count": len(field_rows),
            "field_value_schema_covered_field_count": len(
                covered_field_ids
            ),
            "input_state_count": len(input_rows),
            "internal_condition_count": len(
                operator_contract["internal_condition_rows"]
            ),
            "internal_disposition_count": len(
                operator_contract["internal_disposition_ids"]
            ),
            "json_kind_count": len(tree["field_value_json_kind_ids"]),
            "operator_count": len(operators),
            "path_segment_kind_count": len(
                tree["selector_contract"]["path_segment_schema_rows"]
            ),
            "profile_interface_error_role_count": len(
                PORTABLE_PREDICATE_LANGUAGE_CORE_PUBLIC_ERROR_ROLE_IDS
            ),
            "profile_interface_locator_primitive_count": len(
                PORTABLE_PREDICATE_LANGUAGE_CORE_LOCATOR_PRIMITIVE_IDS
            ),
            "profile_interface_purpose_relation_primitive_count": len(
                purpose_relation_primitive_rows
            ),
            "profile_field_semantic_role_count": len(
                profile_field_semantic_rows
            ),
            "profile_parameter_slot_count": len(
                PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_PARAMETER_SLOT_IDS
            ),
            "resolution_requirement_count": len(
                tree["resolution_contract"][
                    "resolution_requirement_rows"
                ]
            ),
            "type_kind_count": len(type_rows),
            "value_source_kind_count": len(
                tree["resolution_contract"]["value_source_kind_ids"]
            ),
        }
        or counts["type_kind_count"] != len(type_rows)
        or counts["constructor_count"] != len(constructors)
        or counts["operator_count"] != len(operators)
        or counts["input_state_count"] != len(input_rows)
        or counts["artifact_family_count"] != 5
        or counts["artifact_nested_schema_count"] != 12
        or counts["artifact_identity_reference_count"] != 6
        or counts["internal_condition_count"] != 7
        or counts["internal_disposition_count"] != 4
        or not field_id_lists_are_unique(tree)
        or not unique(covered_field_ids)
        or not exact_runtime_field_ids.issubset(set(covered_field_ids))
        or any(
            not row["field_ids"]
            or row["field_ids"] != sorted(row["field_ids"])
            for row in field_rows
        )
        or not unique([row["value_schema_id"] for row in field_rows])
        or {
            row["admitted_json_kind_id"] for row in field_rows
        }
        != {"array", "boolean", "integer", "object", "string"}
        or not unique(
            [row["artifact_family_id"] for row in families]
        )
        or {
            row["artifact_role_id"] for row in families
        }
        != set(PORTABLE_PREDICATE_LANGUAGE_CORE_REQUIRED_ARTIFACT_ROLE_IDS)
        or not unique(nested_schema_ids)
        or set(nested_schema_references) != set(nested_schema_ids)
        or not unique([row["field_id"] for row in identity_rows])
        or [
            row["type_kind_id"] for row in type_rows
        ]
        != list(PORTABLE_PREDICATE_LANGUAGE_CORE_TYPE_KIND_IDS)
        or [
            row["type_kind_id"] for row in encoding_rows
        ]
        != list(PORTABLE_PREDICATE_LANGUAGE_CORE_TYPE_KIND_IDS)
        or [
            row["constructor_id"] for row in constructors
        ]
        != list(PORTABLE_PREDICATE_LANGUAGE_CORE_CONSTRUCTOR_IDS)
        or [
            row["operator_id"] for row in operators
        ]
        != list(PORTABLE_PREDICATE_LANGUAGE_CORE_OPERATOR_IDS)
        or [
            row["value_source_kind_id"]
            for row in source_kind_schema["source_kind_rule_rows"]
        ]
        != tree["resolution_contract"]["value_source_kind_ids"]
        or constructor_hard_rules | {"resource"}
        != {
            row["failure_rule_id"] for row in constructor_mapping_rows
        }
        or any(
            row["public_error_role_id"] != "LOCAL_RULE_FAILED"
            for row in constructor_mapping_rows
        )
        or operator_hard_rules
        != {
            row["duplicate_or_range_rule_id"]
            for row in operator_mapping_rows
        }
        or any(
            row["public_error_role_id"] != "LOCAL_RULE_FAILED"
            for row in operator_mapping_rows
        )
        or any(
            row["public_error_role_id"] != "LOCAL_RULE_FAILED"
            for row in operator_contract["internal_condition_rows"]
        )
        or [
            row["internal_disposition_id"]
            for row in operator_contract["truth_mapping_rows"]
        ]
        != operator_contract["internal_disposition_ids"]
        or [
            row["executed_error_role_rule_id"]
            for row in operator_contract["truth_mapping_rows"]
        ]
        != [
            "EMPTY",
            "FIXED_LOCAL_RULE_FAILED",
            "PROPAGATE_SELECTED_ORIGIN_PUBLIC_ERROR",
            "PROPAGATE_SELECTED_ORIGIN_PUBLIC_ERROR",
        ]
        or operator_contract["fault_tie_break_field_ids"]
        != [
            "disposition_rank",
            "operand_declaration_index",
            "node_index",
        ]
        or operator_contract["no_operand_fault_index_value"] != 4294967295
        or operator_contract["no_node_fault_index_value"] != 4294967295
        or [
            row["origin_kind_id"]
            for row in fault_origin_schema["origin_kind_rule_rows"]
        ]
        != fault_origin_schema["origin_kind_ids"]
        or interface["required_public_error_role_ids"]
        != list(PORTABLE_PREDICATE_LANGUAGE_CORE_PUBLIC_ERROR_ROLE_IDS)
        or interface["required_profile_parameter_slot_ids"]
        != list(PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_PARAMETER_SLOT_IDS)
        or interface["required_runtime_artifact_role_ids"]
        != list(
            PORTABLE_PREDICATE_LANGUAGE_CORE_REQUIRED_ARTIFACT_ROLE_IDS
        )
        or interface["reserved_metadata_artifact_role_ids"]
        != list(
            PORTABLE_PREDICATE_LANGUAGE_CORE_RESERVED_METADATA_ARTIFACT_ROLE_IDS
        )
        or interface["reserved_core_metadata_artifact_type_ids"]
        != [
            PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_ARTIFACT_TYPE,
            PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_INTERFACE_ARTIFACT_TYPE,
            PORTABLE_PREDICATE_LANGUAGE_CORE_VERIFICATION_RESULT_ARTIFACT_TYPE,
        ]
        or not _unique_identifiers(
            interface["reserved_core_metadata_artifact_type_ids"]
        )
        or set(interface["reserved_metadata_artifact_role_ids"]).intersection(
            interface["required_runtime_artifact_role_ids"]
        )
        or interface["admitted_profile_field_value_schema_ids"]
        != list(
            PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_FIELD_VALUE_SCHEMA_IDS
        )
        or not set(
            interface["admitted_profile_field_value_schema_ids"]
        ).issubset({row["value_schema_id"] for row in field_rows})
        or [
            row["semantic_role_id"] for row in profile_field_semantic_rows
        ]
        != list(
            PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_FIELD_SEMANTIC_ROLE_IDS
        )
        or any(
            not _exact_keys(
                row,
                (
                    "admitted_value_schema_ids",
                    "role_parameter_rule_id",
                    "semantic_role_id",
                ),
            )
            or not _unique_identifiers(row["admitted_value_schema_ids"])
            or not set(row["admitted_value_schema_ids"]).issubset(
                interface["admitted_profile_field_value_schema_ids"]
            )
            or not _is_identifier(row["role_parameter_rule_id"])
            for row in profile_field_semantic_rows
        )
        or interface["profile_locator_validation_primitive_id"]
        != "profile-field-schema-and-locator-primitive-v1"
        or interface["profile_program_purpose_validation_primitive_id"]
        != "profile-field-schema-and-purpose-relations-v1"
        or interface["locator_empty_placeholder_value_rule_id"]
        != "exact-empty-json-array-never-traversed-v1"
        or interface["profile_validation_rule_label_semantics_id"]
        != "non-authoritative-descriptive-legacy-correspondence-label-v1"
        or interface["maximum_profile_registry_counts"][
            "profile_field_schema_rows"
        ]
        != 1024
        or interface["maximum_profile_registry_counts"][
            "program_purpose_relation_rows"
        ]
        != 256
        or interface["maximum_profile_registry_counts"][
            "program_purpose_equality_rows"
        ]
        != 4096
        or [
            row["relation_primitive_id"]
            for row in purpose_relation_primitive_rows
        ]
        != list(
            PORTABLE_PREDICATE_LANGUAGE_CORE_PURPOSE_RELATION_PRIMITIVE_IDS
        )
        or any(
            not _exact_keys(
                row,
                (
                    "cardinality_rule_id",
                    "comparison_rule_id",
                    "path_resolution_rule_id",
                    "relation_primitive_id",
                    "source_kind_id",
                ),
            )
            or any(not _is_identifier(value) for value in row.values())
            for row in purpose_relation_primitive_rows
        )
        or [
            row["locator_primitive_id"]
            for row in locator_field_constraint_rows
        ]
        != list(PORTABLE_PREDICATE_LANGUAGE_CORE_LOCATOR_PRIMITIVE_IDS)
        or any(
            not _exact_keys(
                row,
                (
                    "admitted_selection_semantic_role_ids",
                    "locator_primitive_id",
                    "required_semantic_role_count_rows",
                ),
            )
            or not _unique_identifiers(
                row["admitted_selection_semantic_role_ids"],
                nonempty=False,
            )
            or not set(
                row["admitted_selection_semantic_role_ids"]
            ).issubset(
                set(
                    PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_FIELD_SEMANTIC_ROLE_IDS
                )
            )
            or type(row["required_semantic_role_count_rows"]) is not list
            or any(
                not _exact_keys(
                    required_row,
                    ("required_count", "semantic_role_id"),
                )
                or type(required_row["required_count"]) is not int
                or required_row["required_count"] != 1
                or required_row["semantic_role_id"]
                not in PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_FIELD_SEMANTIC_ROLE_IDS
                for required_row in row[
                    "required_semantic_role_count_rows"
                ]
            )
            or not unique(
                [
                    required_row["semantic_role_id"]
                    for required_row in row[
                        "required_semantic_role_count_rows"
                    ]
                ]
            )
            for row in locator_field_constraint_rows
        )
        or next(
            row
            for row in locator_field_constraint_rows
            if row["locator_primitive_id"] == "direct-bound-value"
        )["admitted_selection_semantic_role_ids"]
        != []
        or "profile_field_schema_rows"
        not in interface["closed_profile_exact_field_ids"]
        or "profile_verification_result_artifact_type"
        not in interface["closed_profile_exact_field_ids"]
        or [
            row["primitive_id"]
            for row in interface[
                "profile_bound_operator_primitive_rows"
            ]
        ]
        != interface["admitted_profile_bound_operator_primitive_ids"]
        or [
            row["refinement_primitive_id"]
            for row in interface["interval_refinement_primitive_rows"]
        ]
        != interface["admitted_interval_refinement_ids"]
        or interface["profile_bound_operator_primitive_rows"][0][
            "parameter_binding_rule_id"
        ]
        != (
            "one-parameter-binds-token-item-domain-more-than-one-binds-exact-"
            "tuple-of-ordered-token-component-domains-v1"
        )
        or len(
            {
                PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_ARTIFACT_TYPE,
                PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_INTERFACE_ARTIFACT_TYPE,
                PORTABLE_PREDICATE_LANGUAGE_CORE_VERIFICATION_RESULT_ARTIFACT_TYPE,
            }
        )
        != 3
        or tree["type_contract"][
            "typed_value_identity_sha256_computation_id"
        ]
        != "plain-sha256-of-exact-typed-identity-preimage-v1"
        or any(tree["nonclaim_state"].values())
        or any(token in lower_raw for token in forbidden)
        or len(canonical_raw) != _V1_CORE_CONTRACT_BYTE_COUNT
        or hashlib.sha256(canonical_raw).hexdigest()
        != _V1_CORE_CONTRACT_PLAIN_SHA256
        or _domain_sha256(
            PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_DIGEST_DOMAIN,
            canonical_raw,
        )
        != _V1_CORE_CONTRACT_SHA256
        or portable_predicate_language_core_profile_interface_sha256()
        != _V1_PROFILE_INTERFACE_SHA256
    ):
        _fail(PortablePredicateLanguageCoreCode.CONTRACT_DRIFT)


_validate_contract_coherence()


__all__ = [
    "MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_ARTIFACT_BYTES",
    "MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_JSON_DEPTH",
    "MAXIMUM_PORTABLE_PREDICATE_LANGUAGE_CORE_JSON_ITEMS",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_CONSTRUCTOR_IDS",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_ARTIFACT_TYPE",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_CONTRACT_DIGEST_DOMAIN",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_FALSE_CLAIM_IDS",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_LOCATOR_PRIMITIVE_IDS",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_OPERATOR_IDS",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_PURPOSE_RELATION_PRIMITIVE_IDS",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_FIELD_SEMANTIC_ROLE_IDS",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_FIELD_VALUE_SCHEMA_IDS",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_INTERFACE_ARTIFACT_TYPE",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_VERIFICATION_RESULT_ARTIFACT_TYPE",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_PROFILE_PARAMETER_SLOT_IDS",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_PUBLIC_ERROR_ROLE_IDS",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_REQUIRED_ARTIFACT_ROLE_IDS",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_RESERVED_METADATA_ARTIFACT_ROLE_IDS",
    "PORTABLE_PREDICATE_LANGUAGE_CORE_TYPE_KIND_IDS",
    "PortablePredicateLanguageCoreCode",
    "PortablePredicateLanguageCoreError",
    "parse_portable_predicate_language_core_contract",
    "portable_predicate_language_core_contract_bytes",
    "portable_predicate_language_core_contract_plain_sha256",
    "portable_predicate_language_core_contract_sha256",
    "portable_predicate_language_core_contract_tree",
    "portable_predicate_language_core_profile_interface_sha256",
    "portable_predicate_language_core_profile_interface_tree",
    "validate_portable_predicate_profile_tree",
]
