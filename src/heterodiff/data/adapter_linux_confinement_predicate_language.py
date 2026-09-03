"""Static contract for the portable nominal predicate language.

This module freezes syntax, resource limits, nominal value types, operand
resolution classes, exact selectors, typed shaping constructors, predicate
operators, and fail-closed outcome propagation.  It does not implement the
evaluator, resolve an operand, parse a Linux source, evaluate an observation
predicate, authorize release, or establish confinement.
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


LINUX_CONFINEMENT_PREDICATE_LANGUAGE_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-portable-predicate-language-"
    "contract.v1"
)
LINUX_CONFINEMENT_PREDICATE_LANGUAGE_CONTRACT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_PREDICATE_LANGUAGE_CONTRACT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_PREDICATE_LANGUAGE_CONTRACT_STATUS: Final = (
    "PORTABLE_PREDICATE_LANGUAGE_SCHEMA_CONTRACT_IMPLEMENTED_"
    "EVALUATOR_NOT_IMPLEMENTED"
)
LINUX_CONFINEMENT_PREDICATE_LANGUAGE_VALIDATION_SCOPE: Final = (
    "STATIC_NOMINAL_TYPE_SELECTOR_CONSTRUCTOR_OPERATOR_AND_OUTCOME_"
    "SCHEMA_ONLY"
)
LINUX_CONFINEMENT_PREDICATE_LANGUAGE_ENCODING_ID: Final = (
    "canonical-ascii-json-sort-keys-no-whitespace-v1"
)
LINUX_CONFINEMENT_PREDICATE_LANGUAGE_DIGEST_COMPUTATION_ID: Final = (
    "sha256-domain-nul-u64be-length-canonical-bytes-v1"
)
LINUX_CONFINEMENT_PREDICATE_TYPED_IDENTITY_COMPUTATION_ID: Final = (
    "u64be-type-id-length-type-id-u64be-payload-length-payload-v1"
)
LINUX_CONFINEMENT_PREDICATE_IDENTIFIER_GRAMMAR: Final = (
    "[A-Za-z0-9][A-Za-z0-9._:/+\\-]*"
)

MAXIMUM_LINUX_CONFINEMENT_PREDICATE_LANGUAGE_ARTIFACT_BYTES: Final = (
    4 * 1024 * 1024
)
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_LANGUAGE_JSON_DEPTH: Final = 32
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_LANGUAGE_JSON_ITEMS: Final = 65536
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_IDENTIFIER_BYTES: Final = 512
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_TYPE_ROWS: Final = 512
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_OPERAND_ROWS: Final = 512
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_SHAPING_NODES: Final = 256
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_NODES: Final = 256
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_TYPE_DEPTH: Final = 8
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_GRAPH_DEPTH: Final = 32
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_NODE_FANOUT: Final = 64
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_NODE_REFERENCES: Final = 1024
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_LOCATOR_SEGMENTS: Final = 16
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_SELECTOR_KEY_COMPONENTS: Final = 4
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_TUPLE_COMPONENTS: Final = 32
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_COLLECTION_ITEMS: Final = 4096
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_OCTETS: Final = 262144
MAXIMUM_LINUX_CONFINEMENT_PREDICATE_TYPED_PAYLOAD_BYTES: Final = (
    1024 * 1024
)

LINUX_CONFINEMENT_PREDICATE_TYPE_KIND_IDS: Final = (
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
LINUX_CONFINEMENT_PREDICATE_DIGEST_SEMANTICS_IDS: Final = (
    "PLAIN_SHA256",
    "DOMAIN_SEPARATED_SHA256",
)
LINUX_CONFINEMENT_PREDICATE_VALUE_SOURCE_KIND_IDS: Final = (
    "INPUT_RESOLVED",
    "PROGRAM_LITERAL",
    "DERIVED_TYPED_VALUE",
)
LINUX_CONFINEMENT_PREDICATE_RESOLUTION_REQUIREMENT_IDS: Final = (
    "REQUIRED_RUNTIME_FAIL",
    "REQUIRED_EXTERNAL_NOT_EVALUATED",
    "STATIC_CONTRACT",
)
LINUX_CONFINEMENT_PREDICATE_INPUT_STATE_IDS: Final = (
    "AVAILABLE",
    "REQUIRED_RUNTIME_SOURCE_UNAVAILABLE",
    "PARSER_FAILED",
    "DERIVATION_FAILED",
    "UPSTREAM_PREDICATE_FAILED",
    "EXTERNAL_AUTHORITY_UNAVAILABLE",
    "STATIC_MAPPING_UNRESOLVED",
)
LINUX_CONFINEMENT_PREDICATE_INTERNAL_DISPOSITION_IDS: Final = (
    "LOGICAL_TRUE",
    "LOGICAL_FALSE",
    "HARD_FAILURE",
    "NOT_EVALUATED",
)
LINUX_CONFINEMENT_PREDICATE_SHAPING_VALUE_STATE_IDS: Final = (
    "VALUE_AVAILABLE",
    "HARD_FAILURE",
    "NOT_EVALUATED",
)
LINUX_CONFINEMENT_PREDICATE_RESULT_IDS: Final = (
    "PASS",
    "FAIL",
    "NOT_EVALUATED",
)
LINUX_CONFINEMENT_PREDICATE_PATH_SEGMENT_KIND_IDS: Final = (
    "object-key",
    "list-index",
    "declared-keyed-list-item",
)
LINUX_CONFINEMENT_PREDICATE_SHAPING_CONSTRUCTOR_IDS: Final = (
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
LINUX_CONFINEMENT_PREDICATE_OPERATOR_IDS: Final = (
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
    "status-is-approved",
    "token-equal",
    "u64-equal",
)
LINUX_CONFINEMENT_PREDICATE_INTERVAL_ORDER_MODE_IDS: Final = (
    "TOUCHING_ADMITTED",
    "STRICTLY_SEPARATED",
)
LINUX_CONFINEMENT_PREDICATE_INTERNAL_CONDITION_IDS: Final = (
    "LOGICAL_FALSE",
    "ARITHMETIC_RANGE",
    "DUPLICATE_VALUE",
    "INVALID_INTERVAL",
    "KEY_SELECTION_CARDINALITY",
    "OPTIONAL_REQUIRED_ABSENT",
    "DERIVED_VALUE_RESOURCE_LIMIT",
)
LINUX_CONFINEMENT_PREDICATE_PROGRAM_PURPOSE_IDS: Final = (
    "GENERIC_PORTABLE_CONFORMANCE",
    "LINUX_OBSERVATION_PREDICATE",
)
LINUX_CONFINEMENT_PREDICATE_ARTIFACT_FAMILY_IDS: Final = (
    "PredicateProgramV1",
    "PredicateEvaluationContextV1",
    "PredicateInputBundleV1",
    "PredicateEvaluationResultV1",
)
LINUX_CONFINEMENT_PREDICATE_FALSE_CLAIM_IDS: Final = (
    "authorizing_gate_implemented",
    "custody_authenticated",
    "empirical_result_established",
    "linux_confinement_established",
    "linux_execution_observed",
    "native_acquisition_implemented",
    "native_origin_authenticated",
    "native_source_derivations_validated",
    "observation_formula_inventory_implemented",
    "operand_authorities_authenticated",
    "operand_locators_resolved",
    "policy_predicate_evaluated",
    "portable_typed_formula_evaluated",
    "predicate_formula_implemented",
    "release_authorized",
)


class LinuxConfinementPredicateLanguageCode(str, Enum):
    """Closed failures for the static language contract."""

    INPUT_TYPE = "INPUT_TYPE"
    INPUT_RESOURCE = "INPUT_RESOURCE"
    JSON_INVALID = "JSON_INVALID"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    CANONICAL_MISMATCH = "CANONICAL_MISMATCH"
    CONTRACT_DRIFT = "CONTRACT_DRIFT"


_ERROR_MESSAGES: Final = {
    LinuxConfinementPredicateLanguageCode.INPUT_TYPE: (
        "Linux predicate language contract input has an invalid exact type"
    ),
    LinuxConfinementPredicateLanguageCode.INPUT_RESOURCE: (
        "Linux predicate language contract input exceeds its resource ceiling"
    ),
    LinuxConfinementPredicateLanguageCode.JSON_INVALID: (
        "Linux predicate language contract JSON is invalid"
    ),
    LinuxConfinementPredicateLanguageCode.SCHEMA_INVALID: (
        "Linux predicate language contract schema is invalid"
    ),
    LinuxConfinementPredicateLanguageCode.CANONICAL_MISMATCH: (
        "Linux predicate language contract bytes are not canonical"
    ),
    LinuxConfinementPredicateLanguageCode.CONTRACT_DRIFT: (
        "Linux predicate language contract anchors drifted"
    ),
}


class LinuxConfinementPredicateLanguageError(ValueError):
    """One fixed-message static-language contract failure."""

    def __init__(
        self,
        code: LinuxConfinementPredicateLanguageCode,
    ) -> None:
        if type(code) is not LinuxConfinementPredicateLanguageCode:
            raise TypeError("predicate language code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class _DuplicateKeyError(ValueError):
    pass


def _fail(code: LinuxConfinementPredicateLanguageCode) -> None:
    raise LinuxConfinementPredicateLanguageError(code) from None


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
        _fail(LinuxConfinementPredicateLanguageCode.SCHEMA_INVALID)
    if (
        not result
        or len(result)
        > MAXIMUM_LINUX_CONFINEMENT_PREDICATE_LANGUAGE_ARTIFACT_BYTES
    ):
        _fail(LinuxConfinementPredicateLanguageCode.INPUT_RESOURCE)
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


def _node_count(value: object) -> int:
    count = 0
    stack = [value]
    while stack:
        current = stack.pop()
        count += 1
        if count > MAXIMUM_LINUX_CONFINEMENT_PREDICATE_LANGUAGE_JSON_ITEMS:
            return count
        if type(current) is dict:
            for key, item in current.items():
                stack.append(key)
                stack.append(item)
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
            > MAXIMUM_LINUX_CONFINEMENT_PREDICATE_LANGUAGE_JSON_DEPTH
        ):
            return maximum
        if type(current) is dict:
            stack.extend(
                (item, depth + 1)
                for item in current.values()
            )
        elif type(current) is list:
            stack.extend((item, depth + 1) for item in current)
    return maximum


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
                "prior-u64-endpoint-one-nominal-clock-run-binding-v1"
            ),
        },
    ]


def _value_encoding_rows() -> list:
    return [
        {
            "encoding_id": "one-byte-00-or-01-v1",
            "maximum_payload_bytes": 1,
            "minimum_payload_bytes": 1,
            "type_kind_id": "boolean",
        },
        {
            "encoding_id": "unsigned-u64be-eight-bytes-v1",
            "maximum_payload_bytes": 8,
            "minimum_payload_bytes": 8,
            "type_kind_id": "u64",
        },
        {
            "encoding_id": "strict-identifier-ascii-v1",
            "maximum_payload_bytes": 512,
            "minimum_payload_bytes": 1,
            "type_kind_id": "token",
        },
        {
            "encoding_id": "bounded-uninterpreted-octets-v1",
            "maximum_payload_bytes": 262144,
            "minimum_payload_bytes": 0,
            "type_kind_id": "octets",
        },
        {
            "encoding_id": "raw-sha256-thirty-two-bytes-v1",
            "maximum_payload_bytes": 32,
            "minimum_payload_bytes": 32,
            "type_kind_id": "sha256",
        },
        {
            "encoding_id": (
                "tag-00-or-tag-01-u64be-length-item-payload-v1"
            ),
            "maximum_payload_bytes": 1048576,
            "minimum_payload_bytes": 1,
            "type_kind_id": "optional",
        },
        {
            "encoding_id": (
                "u64be-count-repeated-u64be-length-item-payload-v1"
            ),
            "maximum_payload_bytes": 1048576,
            "minimum_payload_bytes": 8,
            "type_kind_id": "sequence",
        },
        {
            "encoding_id": (
                "u64be-count-repeated-u64be-length-component-payload-v1"
            ),
            "maximum_payload_bytes": 1048576,
            "minimum_payload_bytes": 8,
            "type_kind_id": "tuple",
        },
        {
            "encoding_id": (
                "u64be-row-count-repeated-u64be-length-tuple-payload-v1"
            ),
            "maximum_payload_bytes": 1048576,
            "minimum_payload_bytes": 8,
            "type_kind_id": "keyed-table",
        },
        {
            "encoding_id": (
                "u64be-count-repeated-two-u64be-length-u64-payloads-v1"
            ),
            "maximum_payload_bytes": 1048576,
            "minimum_payload_bytes": 8,
            "type_kind_id": "u64-interval-sequence",
        },
    ]


def _input_state_rows() -> list:
    return [
        {
            "admitted_resolution_requirement_ids": [
                "REQUIRED_RUNTIME_FAIL",
                "REQUIRED_EXTERNAL_NOT_EVALUATED",
            ],
            "executed_error_id": "",
            "internal_condition_id": "",
            "input_state_id": "AVAILABLE",
            "internal_disposition_id": "",
            "source_artifact_rule_id": (
                "strict-kind-and-lowercase-sha256-v1"
            ),
            "value_bytes_rule_id": (
                "nonempty-except-canonical-zero-length-octets-payload-v1"
            ),
        },
        {
            "admitted_resolution_requirement_ids": [
                "REQUIRED_RUNTIME_FAIL"
            ],
            "executed_error_id": "SOURCE_UNAVAILABLE",
            "internal_condition_id": "",
            "input_state_id": "REQUIRED_RUNTIME_SOURCE_UNAVAILABLE",
            "internal_disposition_id": "HARD_FAILURE",
            "source_artifact_rule_id": (
                "strict-kind-and-lowercase-sha256-v1"
            ),
            "value_bytes_rule_id": "empty-v1",
        },
        {
            "admitted_resolution_requirement_ids": [
                "REQUIRED_RUNTIME_FAIL"
            ],
            "executed_error_id": "PARSER_REJECTED",
            "internal_condition_id": "",
            "input_state_id": "PARSER_FAILED",
            "internal_disposition_id": "HARD_FAILURE",
            "source_artifact_rule_id": (
                "strict-kind-and-lowercase-sha256-v1"
            ),
            "value_bytes_rule_id": "empty-v1",
        },
        {
            "admitted_resolution_requirement_ids": [
                "REQUIRED_RUNTIME_FAIL"
            ],
            "executed_error_id": "DERIVATION_MISMATCH",
            "internal_condition_id": "",
            "input_state_id": "DERIVATION_FAILED",
            "internal_disposition_id": "HARD_FAILURE",
            "source_artifact_rule_id": (
                "strict-kind-and-lowercase-sha256-v1"
            ),
            "value_bytes_rule_id": "empty-v1",
        },
        {
            "admitted_resolution_requirement_ids": [
                "REQUIRED_RUNTIME_FAIL"
            ],
            "executed_error_id": "PREDICATE_FAILED",
            "internal_condition_id": "",
            "input_state_id": "UPSTREAM_PREDICATE_FAILED",
            "internal_disposition_id": "HARD_FAILURE",
            "source_artifact_rule_id": (
                "strict-kind-and-lowercase-sha256-v1"
            ),
            "value_bytes_rule_id": "empty-v1",
        },
        {
            "admitted_resolution_requirement_ids": [
                "REQUIRED_EXTERNAL_NOT_EVALUATED"
            ],
            "executed_error_id": "AUTHORITY_UNAVAILABLE",
            "internal_condition_id": "",
            "input_state_id": "EXTERNAL_AUTHORITY_UNAVAILABLE",
            "internal_disposition_id": "NOT_EVALUATED",
            "source_artifact_rule_id": (
                "strict-kind-and-lowercase-sha256-v1"
            ),
            "value_bytes_rule_id": "empty-v1",
        },
        {
            "admitted_resolution_requirement_ids": [
                "REQUIRED_EXTERNAL_NOT_EVALUATED"
            ],
            "executed_error_id": "PREDICATE_NOT_EVALUATED",
            "internal_condition_id": "",
            "input_state_id": "STATIC_MAPPING_UNRESOLVED",
            "internal_disposition_id": "NOT_EVALUATED",
            "source_artifact_rule_id": (
                "strict-kind-and-lowercase-sha256-v1"
            ),
            "value_bytes_rule_id": "empty-v1",
        },
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


def _selector_schema_rows() -> list:
    return [
        {
            "exact_field_ids": [
                "segment_kind_id",
                "object_key",
            ],
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


def _constructor_rows() -> list:
    rows = [
        (
            "make-optional-none",
            0,
            0,
            [],
            "output-optional-no-input-v1",
            "none",
        ),
        (
            "make-optional-some",
            1,
            1,
            [],
            "output-optional-item-equals-input-v1",
            "none",
        ),
        (
            "require-optional-present",
            1,
            1,
            [],
            "input-optional-present-item-to-output-item-v1",
            "required-optional",
        ),
        (
            "make-sequence",
            0,
            64,
            [],
            "output-sequence-item-equals-every-input-v1",
            "none",
        ),
        (
            "make-tuple",
            1,
            32,
            [],
            "output-tuple-components-equal-ordered-inputs-v1",
            "none",
        ),
        (
            "make-keyed-table",
            0,
            64,
            [],
            "output-table-row-tuple-equals-every-input-v1",
            "duplicate-key",
        ),
        (
            "make-u64-interval-sequence",
            2,
            64,
            [],
            "even-start-end-inputs-one-nominal-u64-endpoint-type-v1",
            "invalid-interval",
        ),
        (
            "project-tuple-component",
            1,
            1,
            ["component_index"],
            "output-equals-selected-tuple-component-v1",
            "none",
        ),
        (
            "project-keyed-table-column",
            1,
            1,
            ["component_index"],
            "output-sequence-item-equals-selected-row-component-v1",
            "none",
        ),
        (
            "project-keyed-table-keys",
            1,
            1,
            [],
            "output-sequence-of-table-key-tuples-v1",
            "duplicate-key",
        ),
        (
            "select-keyed-table-row",
            2,
            2,
            [],
            "table-and-exact-key-tuple-to-one-row-tuple-v1",
            "exact-one-key",
        ),
        (
            "canonical-sort-keyed-table",
            1,
            1,
            [],
            "same-table-type-lexicographic-length-framed-key-order-v1",
            "duplicate-key",
        ),
    ]
    return [
        {
            "constructor_id": constructor_id,
            "configuration_validation_rule_id": (
                "exact-component-index-json-u64-in-declared-range-v1"
                if configuration == ["component_index"]
                else "exact-empty-object-v1"
            ),
            "exact_configuration_field_ids": configuration,
            "failure_rule_id": failure,
            "maximum_input_count": maximum,
            "minimum_input_count": minimum,
            "native_or_external_parsing_admitted": False,
            "type_relation_id": relation,
        }
        for (
            constructor_id,
            minimum,
            maximum,
            configuration,
            relation,
            failure,
        ) in rows
    ]


def _operator_rows() -> list:
    specs = [
        ("absence", 1, 1, 0, 0, [], "optional-absent-tag-v1", "none"),
        ("all", 0, 0, 1, 64, [], "all-logically-true-v1", "none"),
        (
            "all-distinct",
            1,
            1,
            0,
            0,
            [],
            "one-sequence-canonical-item-distinctness-v1",
            "duplicate-logical-false",
        ),
        ("any", 0, 0, 1, 64, [], "at-least-one-logically-true-v1", "none"),
        (
            "boolean-is",
            2,
            2,
            0,
            0,
            [],
            "identical-nominal-boolean-types-exact-equality-v1",
            "none",
        ),
        (
            "count-equal",
            2,
            2,
            0,
            0,
            [],
            "collection-and-item-count-u64-v1",
            "none",
        ),
        (
            "digest-derived-from-bytes",
            2,
            2,
            0,
            0,
            [],
            "octets-and-plain-sha256-v1",
            "none",
        ),
        (
            "domain-digest-derived-from-bytes",
            2,
            2,
            0,
            0,
            [],
            "octets-and-type-fixed-domain-sha256-frame-v1",
            "none",
        ),
        (
            "integer-sum-equal",
            2,
            2,
            0,
            0,
            [],
            "sequence-u64-and-identical-nominal-u64-v1",
            "checked-overflow-hard",
        ),
        (
            "interval-order",
            1,
            1,
            0,
            0,
            ["interval_order_mode_id"],
            "one-nominal-u64-interval-sequence-every-start-less-or-equal-"
            "end-by-type-validation-and-program-mode-adjacency-logical-"
            "truth-v1",
            "none",
        ),
        ("not", 0, 0, 1, 1, [], "logical-inversion-only-v1", "none"),
        (
            "octets-equal",
            2,
            2,
            0,
            0,
            [],
            "identical-nominal-octet-types-exact-equality-v1",
            "none",
        ),
        (
            "ordered-sequence-equal",
            2,
            2,
            0,
            0,
            [],
            "identical-nominal-sequence-or-table-types-v1",
            "none",
        ),
        (
            "reference-resolves",
            2,
            2,
            0,
            0,
            [],
            "unique-key-tuple-sequence-into-keyed-table-v1",
            "duplicate-hard",
        ),
        (
            "set-equal",
            2,
            2,
            0,
            0,
            [],
            "sequences-with-identical-item-type-v1",
            "duplicate-hard",
        ),
        (
            "set-subset",
            2,
            2,
            0,
            0,
            [],
            "sequences-with-identical-item-type-v1",
            "duplicate-hard",
        ),
        (
            "sha256-equal",
            2,
            2,
            0,
            0,
            [],
            "identical-nominal-sha256-types-exact-equality-v1",
            "none",
        ),
        (
            "status-is-approved",
            2,
            2,
            0,
            0,
            [],
            "full-outcome-tuple-and-unique-nonempty-sequence-v1",
            "duplicate-hard",
        ),
        (
            "token-equal",
            2,
            2,
            0,
            0,
            [],
            "identical-nominal-token-types-exact-equality-v1",
            "none",
        ),
        (
            "u64-equal",
            2,
            2,
            0,
            0,
            [],
            "identical-nominal-u64-types-exact-equality-v1",
            "none",
        ),
    ]
    return [
        {
            "applicability_id": "ALWAYS",
            "configuration_validation_rule_id": (
                "exact-interval-order-mode-id-enum-v1"
                if operator_id == "interval-order"
                else "exact-empty-object-v1"
            ),
            "duplicate_or_range_rule_id": failure,
            "exact_configuration_field_ids": configuration,
            "failure_oracle_id": "FAIL_CLOSED_FOUR_DISPOSITION_V1",
            "maximum_child_count": maximum_children,
            "maximum_operand_count": maximum_operands,
            "minimum_child_count": minimum_children,
            "minimum_operand_count": minimum_operands,
            "operand_source_rule_id": (
                "second-approved-outcome-sequence-value-source-program-"
                "literal-and-canonical-unique-nonempty-at-program-"
                "validation-v1"
                if operator_id == "status-is-approved"
                else "no-additional-source-restriction-v1"
            ),
            "operator_id": operator_id,
            "same_operand_reference_admitted": False,
            "required_nominal_unit_id": (
                "collection-item-count"
                if operator_id == "count-equal"
                else ""
            ),
            "type_and_truth_rule_id": relation,
        }
        for (
            operator_id,
            minimum_operands,
            maximum_operands,
            minimum_children,
            maximum_children,
            configuration,
            relation,
            failure,
        ) in specs
    ]


def _program_purpose_rows() -> list:
    return [
        {
            "exact_binding_field_ids": [],
            "binding_validation_rule_id": "exact-empty-object-v1",
            "binding_identity_rule_rows": [],
            "positive_observation_claim_admitted": False,
            "program_purpose_id": "GENERIC_PORTABLE_CONFORMANCE",
        },
        {
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
            "binding_validation_rule_id": (
                "exact-one-53a-predicate-row-observation-and-predicate-"
                "match-with-byte-exact-nonempty-unique-ordered-mapping-"
                "ids-and-typed-policy-platform-formula-core-identities-v1"
            ),
            "binding_identity_rule_rows": [
                {
                    "artifact_type_field_id": "policy_artifact_type_id",
                    "fixed_artifact_type_id": (
                        "heterodiff.adapter.linux-confinement-policy.v1"
                    ),
                    "identity_field_id": "policy_identity_sha256",
                    "identity_semantics_field_id": (
                        "policy_identity_semantics_id"
                    ),
                    "required_identity_semantics_id": (
                        "DOMAIN_SEPARATED_SHA256"
                    ),
                },
                {
                    "artifact_type_field_id": (
                        "platform_profile_artifact_type_id"
                    ),
                    "fixed_artifact_type_id": (
                        "heterodiff.adapter.linux-platform-profile.v1"
                    ),
                    "identity_field_id": (
                        "platform_profile_identity_sha256"
                    ),
                    "identity_semantics_field_id": (
                        "platform_profile_identity_semantics_id"
                    ),
                    "required_identity_semantics_id": (
                        "DOMAIN_SEPARATED_SHA256"
                    ),
                },
                {
                    "artifact_type_field_id": (
                        "formula_core_artifact_type_id"
                    ),
                    "fixed_artifact_type_id": (
                        "heterodiff.adapter.linux-confinement-predicate-"
                        "formula-core.v1"
                    ),
                    "identity_field_id": "formula_core_identity_sha256",
                    "identity_semantics_field_id": (
                        "formula_core_identity_semantics_id"
                    ),
                    "required_identity_semantics_id": (
                        "DOMAIN_SEPARATED_SHA256"
                    ),
                },
            ],
            "positive_observation_claim_admitted": False,
            "program_purpose_id": "LINUX_OBSERVATION_PREDICATE",
        },
    ]


def _field_value_schema_rows() -> list:
    """Return base JSON-kind and lexical rules for every artifact field."""

    return [
        {
            "admitted_json_kind_id": "string",
            "field_ids": ["format_version"],
            "validation_rule_id": "exact-ascii-string-one-v1",
            "value_schema_id": "fixed-format-version-v1",
        },
        {
            "admitted_json_kind_id": "string",
            "field_ids": [
                "applicability_id",
                "artifact_type",
                "constructor_id",
                "digest_semantics_id",
                "endpoint_u64_type_id",
                "failure_oracle_id",
                "formula_core_artifact_type_id",
                "formula_core_identity_semantics_id",
                "input_slot_id",
                "input_state_id",
                "internal_disposition_id",
                "interval_order_mode_id",
                "item_type_id",
                "key_field_id",
                "key_tuple_type_id",
                "key_type_id",
                "locator_kind_id",
                "mapping_id",
                "object_key",
                "observation_id",
                "octet_domain_id",
                "operator_id",
                "origin_kind_id",
                "output_operand_id",
                "platform_profile_artifact_type_id",
                "platform_profile_identity_semantics_id",
                "policy_artifact_type_id",
                "policy_identity_semantics_id",
                "predicate_id",
                "predicate_result_id",
                "program_id",
                "program_purpose_id",
                "proposition_domain_id",
                "resolution_requirement_id",
                "resolver_contract_artifact_type",
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
            ],
            "validation_rule_id": (
                "strict-identifier-ascii-one-to-five-hundred-twelve-"
                "bytes-v1"
            ),
            "value_schema_id": "strict-identifier-string-v1",
        },
        {
            "admitted_json_kind_id": "string",
            "field_ids": [
                "digest_domain_id",
                "executed_error_id",
                "internal_condition_id",
                "node_id",
                "operand_id",
                "root_executed_error_id",
                "root_internal_condition_id",
                "source_shaping_node_id",
            ],
            "validation_rule_id": (
                "empty-or-strict-identifier-ascii-up-to-five-hundred-"
                "twelve-bytes-v1"
            ),
            "value_schema_id": "empty-or-strict-identifier-string-v1",
        },
        {
            "admitted_json_kind_id": "string",
            "field_ids": [
                "evaluation_context_identity_sha256",
                "formula_core_identity_sha256",
                "input_bundle_sha256",
                "list_order_contract_sha256",
                "native_mapping_gap_contract_sha256",
                "platform_profile_identity_sha256",
                "policy_identity_sha256",
                "predicate_language_contract_sha256",
                "program_sha256",
                "resolver_contract_sha256",
                "source_identity_sha256",
            ],
            "validation_rule_id": (
                "exact-sixty-four-lowercase-hex-digits-v1"
            ),
            "value_schema_id": "lowercase-sha256-string-v1",
        },
        {
            "admitted_json_kind_id": "string",
            "field_ids": [
                "typed_value_identity_sha256",
            ],
            "validation_rule_id": (
                "empty-or-exact-sixty-four-lowercase-hex-digits-v1"
            ),
            "value_schema_id": "empty-or-lowercase-sha256-string-v1",
        },
        {
            "admitted_json_kind_id": "string",
            "field_ids": [
                "key_value_bytes_hex",
                "literal_value_bytes_hex",
                "value_bytes_hex",
            ],
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
            "field_ids": [
                "component_index",
                "expected_list_count",
                "list_index",
                "node_index",
                "operand_declaration_index",
            ],
            "validation_rule_id": (
                "nonnegative-json-integer-with-containing-schema-"
                "ceiling-v1"
            ),
            "value_schema_id": "nonnegative-index-or-count-integer-v1",
        },
        {
            "admitted_json_kind_id": "boolean",
            "field_ids": list(
                LINUX_CONFINEMENT_PREDICATE_FALSE_CLAIM_IDS
            ),
            "validation_rule_id": (
                "exact-json-boolean-refined-by-claim-schema-v1"
            ),
            "value_schema_id": "claim-boolean-v1",
        },
        {
            "admitted_json_kind_id": "array",
            "field_ids": [
                "ordered_authority_class_ids",
                "ordered_child_node_ids",
                "ordered_component_type_ids",
                "ordered_input_operand_ids",
                "ordered_operand_ids",
                "ordered_required_mapping_ids",
            ],
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
                "bounded-array-of-nonnegative-json-integers-refined-by-"
                "containing-schema-v1"
            ),
            "value_schema_id": "ordered-index-array-v1",
        },
        {
            "admitted_json_kind_id": "array",
            "field_ids": [
                "ordered_input_rows",
                "ordered_key_component_rows",
                "ordered_operand_rows",
                "ordered_path_segments",
                "ordered_predicate_node_rows",
                "ordered_predicate_result_rows",
                "ordered_shaping_node_rows",
                "ordered_shaping_result_rows",
                "ordered_type_rows",
            ],
            "validation_rule_id": (
                "bounded-array-of-exact-json-objects-with-element-"
                "schema-order-and-cardinality-refined-by-containing-"
                "schema-v1"
            ),
            "value_schema_id": "ordered-exact-object-row-array-v1",
        },
        {
            "admitted_json_kind_id": "object",
            "field_ids": [
                "claim_state",
                "constructor_configuration",
                "locator",
                "nonclaim_state",
                "operator_configuration",
                "purpose_binding",
                "selected_fault_origin",
            ],
            "validation_rule_id": (
                "exact-json-object-fields-and-values-refined-by-"
                "containing-schema-v1"
            ),
            "value_schema_id": "context-refined-exact-object-v1",
        },
    ]


def _artifact_family_rows() -> list:
    return [
        {
            "artifact_family_id": "PredicateProgramV1",
            "artifact_type_id": (
                "heterodiff.adapter.linux-confinement-predicate-program.v1"
            ),
            "artifact_identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
            "digest_domain_id": (
                "heterodiff.adapter.linux-confinement-predicate-program.v1"
            ),
            "cross_field_validation_rule_ids": [
                "fixed-artifact-type-format-one-contract-and-gap-pins-v1",
                "purpose-binding-exactly-matches-purpose-schema-v1",
                "linux-purpose-every-required-mapping-id-is-referenced-by-"
                "at-least-one-input-resolved-locator-and-no-other-mapping-"
                "id-occurs-generic-purpose-vacuous-v1",
                "formula-core-is-canonical-projection-for-all-purposes-and-"
                "linux-purpose-identity-matches-generic-purpose-has-no-"
                "identity-field-v1",
                "all-program-row-and-whole-graph-rules-hold-v1",
            ],
            "exact_top_level_field_ids": [
                "artifact_type",
                "format_version",
                "predicate_language_contract_sha256",
                "native_mapping_gap_contract_sha256",
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
            "nested_schema_ids": [
                "program-purpose-binding-v1",
                "predicate-formula-core-v1",
                "program-type-row-by-kind-v1",
                "program-operand-row-by-source-kind-v1",
                "program-shaping-node-row-v1",
                "program-predicate-node-row-v1",
                "all-false-static-nonclaim-state-v1",
            ],
        },
        {
            "artifact_family_id": "PredicateEvaluationContextV1",
            "artifact_type_id": (
                "heterodiff.adapter.linux-confinement-predicate-evaluation-"
                "context.v1"
            ),
            "artifact_identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
            "digest_domain_id": (
                "heterodiff.adapter.linux-confinement-predicate-evaluation-"
                "context.v1"
            ),
            "cross_field_validation_rule_ids": [
                "fixed-artifact-type-format-one-and-contract-pin-v1",
                "program-identity-matches-exact-program-v1",
                "nonzero-context-nonce-and-all-false-nonclaims-v1",
            ],
            "exact_top_level_field_ids": [
                "artifact_type",
                "format_version",
                "predicate_language_contract_sha256",
                "program_sha256",
                "context_nonce_hex",
                "nonclaim_state",
            ],
            "field_validation_rule_rows": [
                {
                    "field_id": "context_nonce_hex",
                    "validation_rule_id": (
                        "exact-sixty-four-lowercase-hex-nonzero-v1"
                    ),
                },
            ],
            "nested_schema_ids": [
                "all-false-static-nonclaim-state-v1",
            ],
        },
        {
            "artifact_family_id": "PredicateInputBundleV1",
            "artifact_type_id": (
                "heterodiff.adapter.linux-confinement-predicate-input-"
                "bundle.v1"
            ),
            "artifact_identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
            "digest_domain_id": (
                "heterodiff.adapter.linux-confinement-predicate-input-"
                "bundle.v1"
            ),
            "cross_field_validation_rule_ids": [
                "fixed-artifact-type-format-one-and-contract-pin-v1",
                "program-and-context-identities-match-exact-artifacts-v1",
                "one-input-row-per-input-resolved-operand-in-declaration-"
                "order-and-no-literal-or-derived-rows-v1",
                "all-false-nonclaims-v1",
            ],
            "exact_top_level_field_ids": [
                "artifact_type",
                "format_version",
                "predicate_language_contract_sha256",
                "program_sha256",
                "evaluation_context_identity_sha256",
                "ordered_input_rows",
                "nonclaim_state",
            ],
            "nested_schema_ids": [
                "input-bundle-row-by-declared-resolution-v1",
                "all-false-static-nonclaim-state-v1",
            ],
        },
        {
            "artifact_family_id": "PredicateEvaluationResultV1",
            "artifact_type_id": (
                "heterodiff.adapter.linux-confinement-predicate-evaluation-"
                "result.v1"
            ),
            "artifact_identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
            "digest_domain_id": (
                "heterodiff.adapter.linux-confinement-predicate-evaluation-"
                "result.v1"
            ),
            "cross_field_validation_rule_ids": [
                "fixed-artifact-type-format-one-and-contract-pin-v1",
                "program-input-and-context-identities-byte-exact-match-v1",
                "one-shaping-and-predicate-result-row-per-program-node-in-"
                "program-order-v1",
                "root-result-error-condition-and-origin-byte-exact-mirror-"
                "root-predicate-result-row-v1",
                "claim-state-exactly-follows-evaluation-result-rule-v1",
            ],
            "exact_top_level_field_ids": [
                "artifact_type",
                "format_version",
                "predicate_language_contract_sha256",
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
            "nested_schema_ids": [
                "shaping-result-row-v1",
                "predicate-result-row-v1",
                "selected-fault-origin-v1",
                "evaluation-result-claim-state-v1",
            ],
        },
    ]


def _artifact_nested_schema_rows() -> list:
    return [
        {
            "exact_field_ids": [],
            "schema_id": "program-purpose-binding-v1",
            "validation_rule_id": (
                "exact-fields-selected-by-program-purpose-row-v1"
            ),
        },
        {
            "exact_field_ids": [],
            "schema_id": "program-type-row-by-kind-v1",
            "validation_rule_id": (
                "exact-fields-selected-by-topological-type-kind-row-v1"
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
                        "generic-empty-or-linux-one-to-nine-ordered-unique-"
                        "by-program-purpose-v1"
                    ),
                    "literal_value_rule_id": "empty-v1",
                    "locator_rule_id": (
                        "nonempty-executable-input-locator-v1"
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
                        "authorities-empty-for-literal-only-shaping-v1"
                    ),
                    "literal_value_rule_id": "empty-v1",
                    "locator_rule_id": "empty-v1",
                    "resolution_requirement_ids": ["STATIC_CONTRACT"],
                    "source_shaping_node_rule_id": (
                        "strict-exactly-one-producing-shaping-node-id-v1"
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
                "ordered_type_rows",
                "ordered_operand_rows",
                "ordered_shaping_node_rows",
                "ordered_predicate_node_rows",
                "root_node_id",
            ],
            "schema_id": "predicate-formula-core-v1",
            "validation_rule_id": (
                "canonical-acyclic-program-core-excludes-purpose-binding-"
                "and-claim-state-v1"
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
            "schema_id": "input-bundle-row-by-declared-resolution-v1",
            "validation_rule_id": (
                "exact-state-admitted-by-operand-resolution-requirement-v1"
            ),
        },
        {
            "exact_field_ids": list(
                LINUX_CONFINEMENT_PREDICATE_FALSE_CLAIM_IDS
            ),
            "schema_id": "all-false-static-nonclaim-state-v1",
            "validation_rule_id": "every-exact-claim-false-v1",
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
            "value_state_rule_rows": [
                {
                    "field_rule_id": (
                        "typed-value-identity-present-error-condition-empty-"
                        "fault-origin-none-v1"
                    ),
                    "value_state_id": "VALUE_AVAILABLE",
                },
                {
                    "field_rule_id": (
                        "typed-value-identity-empty-fail-error-present-"
                        "condition-preserved-or-fixed-or-empty-and-"
                        "selected-origin-v1"
                    ),
                    "value_state_id": "HARD_FAILURE",
                },
                {
                    "field_rule_id": (
                        "typed-value-identity-empty-not-evaluated-error-"
                        "present-condition-preserved-or-empty-and-"
                        "selected-origin-v1"
                    ),
                    "value_state_id": "NOT_EVALUATED",
                },
            ],
            "validation_rule_id": (
                "exact-derived-value-or-propagated-fault-row-v1"
            ),
        },
        {
            "exact_field_ids": [
                "node_id",
                "internal_disposition_id",
                "predicate_result_id",
                "executed_error_id",
                "internal_condition_id",
                "selected_fault_origin",
            ],
            "disposition_rule_rows": [
                {
                    "field_rule_id": (
                        "pass-error-condition-empty-fault-origin-none-v1"
                    ),
                    "internal_disposition_id": "LOGICAL_TRUE",
                    "predicate_result_id": "PASS",
                },
                {
                    "field_rule_id": (
                        "fail-predicate-failed-logical-false-condition-"
                        "fault-origin-none-v1"
                    ),
                    "internal_disposition_id": "LOGICAL_FALSE",
                    "predicate_result_id": "FAIL",
                },
                {
                    "field_rule_id": (
                        "fail-origin-error-condition-preserved-or-empty-"
                        "and-selected-fault-origin-present-v1"
                    ),
                    "internal_disposition_id": "HARD_FAILURE",
                    "predicate_result_id": "FAIL",
                },
                {
                    "field_rule_id": (
                        "not-evaluated-origin-error-condition-preserved-or-"
                        "empty-and-selected-fault-origin-present-v1"
                    ),
                    "internal_disposition_id": "NOT_EVALUATED",
                    "predicate_result_id": "NOT_EVALUATED",
                },
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
                        "exact-operand-index-and-id-node-index-sentinel-"
                        "and-node-id-empty-v1"
                    ),
                    "origin_kind_id": "INPUT_OPERAND",
                },
                {
                    "id_and_index_rule_id": (
                        "exact-global-shaping-node-index-and-id-with-"
                        "earliest-causative-operand-or-operand-sentinel-v1"
                    ),
                    "origin_kind_id": "SHAPING_NODE",
                },
                {
                    "id_and_index_rule_id": (
                        "exact-global-predicate-node-index-and-id-with-"
                        "earliest-causative-operand-or-operand-sentinel-v1"
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
            "exact_field_ids": list(
                LINUX_CONFINEMENT_PREDICATE_FALSE_CLAIM_IDS
            ),
            "schema_id": "evaluation-result-claim-state-v1",
            "validation_rule_id": (
                "only-portable-typed-formula-evaluated-conditionally-"
                "true-all-other-claims-false-v1"
            ),
        },
    ]


def linux_confinement_predicate_language_contract_tree() -> dict:
    """Return the exact static nominal predicate-language contract."""

    resource_limits = {
        "artifact_bytes": 4194304,
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
        "typed_payload_bytes": 1048576,
    }
    return {
        "anchor_contracts": {
            "native_mapping_gap_contract_sha256": (
                linux_confinement_native_mapping_gap_contract_sha256()
            ),
        },
        "artifact_family_rows": _artifact_family_rows(),
        "field_value_json_kind_ids": [
            "array",
            "boolean",
            "integer",
            "object",
            "string",
        ],
        "field_value_schema_rows": _field_value_schema_rows(),
        "artifact_nested_schema_rows": _artifact_nested_schema_rows(),
        "artifact_identity_reference_rows": [
            {
                "field_id": "predicate_language_contract_sha256",
                "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
                "referenced_artifact_type_id": (
                    LINUX_CONFINEMENT_PREDICATE_LANGUAGE_CONTRACT_ARTIFACT_TYPE
                ),
            },
            {
                "field_id": "native_mapping_gap_contract_sha256",
                "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
                "referenced_artifact_type_id": (
                    "heterodiff.adapter.linux-confinement-native-mapping-"
                    "gap-contract.v1"
                ),
            },
            {
                "field_id": "formula_core_identity_sha256",
                "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
                "referenced_artifact_type_id": (
                    "heterodiff.adapter.linux-confinement-predicate-"
                    "formula-core.v1"
                ),
            },
            {
                "field_id": "program_sha256",
                "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
                "referenced_artifact_type_id": (
                    "heterodiff.adapter.linux-confinement-predicate-"
                    "program.v1"
                ),
            },
            {
                "field_id": "evaluation_context_identity_sha256",
                "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
                "referenced_artifact_type_id": (
                    "heterodiff.adapter.linux-confinement-predicate-"
                    "evaluation-context.v1"
                ),
            },
            {
                "field_id": "input_bundle_sha256",
                "identity_semantics_id": "DOMAIN_SEPARATED_SHA256",
                "referenced_artifact_type_id": (
                    "heterodiff.adapter.linux-confinement-predicate-input-"
                    "bundle.v1"
                ),
            },
        ],
        "artifact_type": (
            LINUX_CONFINEMENT_PREDICATE_LANGUAGE_CONTRACT_ARTIFACT_TYPE
        ),
        "constructor_contract": {
            "static_type_relation_mismatch_rule_id": (
                "reject-program-artifact-before-evaluation-v1"
            ),
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
            "constructor_failure_mapping_rows": [
                {
                    "failure_rule_id": "duplicate-key",
                    "internal_condition_id": "DUPLICATE_VALUE",
                },
                {
                    "failure_rule_id": "exact-one-key",
                    "internal_condition_id": "KEY_SELECTION_CARDINALITY",
                },
                {
                    "failure_rule_id": "invalid-interval",
                    "internal_condition_id": "INVALID_INTERVAL",
                },
                {
                    "failure_rule_id": "required-optional",
                    "internal_condition_id": "OPTIONAL_REQUIRED_ABSENT",
                },
                {
                    "failure_rule_id": "resource",
                    "internal_condition_id": (
                        "DERIVED_VALUE_RESOURCE_LIMIT"
                    ),
                },
            ],
            "constructor_rows": _constructor_rows(),
            "native_or_external_parser_constructor_count": 0,
            "post_constructor_output_resource_rule_id": (
                "every-constructor-canonical-output-obeys-declared-type-"
                "collection-octet-and-one-mebibyte-payload-ceilings-"
                "resource-failure-applies-after-specific-validation-v1"
            ),
            "shaping_constructor_ids": list(
                LINUX_CONFINEMENT_PREDICATE_SHAPING_CONSTRUCTOR_IDS
            ),
            "shaping_value_state_ids": list(
                LINUX_CONFINEMENT_PREDICATE_SHAPING_VALUE_STATE_IDS
            ),
        },
        "contract_parser_error_ids": [
            code.value for code in LinuxConfinementPredicateLanguageCode
        ],
        "digest_computation_id": (
            LINUX_CONFINEMENT_PREDICATE_LANGUAGE_DIGEST_COMPUTATION_ID
        ),
        "encoding_id": LINUX_CONFINEMENT_PREDICATE_LANGUAGE_ENCODING_ID,
        "executed_layer_error_ids": list(
            LINUX_CONFINEMENT_NATIVE_MAPPING_ERROR_IDS
        ),
        "fixed_counts": {
            "artifact_family_count": 4,
            "artifact_identity_reference_count": 6,
            "artifact_nested_schema_count": 12,
            "authority_class_count": 9,
            "constructor_count": 12,
            "digest_semantics_count": 2,
            "executable_locator_kind_count": 10,
            "false_claim_count": 15,
            "field_value_schema_covered_field_count": 115,
            "field_value_schema_count": 13,
            "input_state_count": 7,
            "internal_condition_count": 7,
            "internal_disposition_count": 4,
            "json_kind_count": 5,
            "operator_count": 20,
            "path_segment_kind_count": 3,
            "program_purpose_count": 2,
            "resolution_requirement_count": 3,
            "shaping_value_state_count": 3,
            "type_kind_count": 10,
            "value_source_kind_count": 3,
        },
        "format_version": "1",
        "identifier_syntax": {
            "grammar": LINUX_CONFINEMENT_PREDICATE_IDENTIFIER_GRAMMAR,
            "maximum_ascii_bytes": 512,
            "minimum_ascii_bytes": 1,
            "nul_admitted": False,
            "unicode_admitted": False,
        },
        "implementation_status_id": (
            LINUX_CONFINEMENT_PREDICATE_LANGUAGE_CONTRACT_STATUS
        ),
        "nonclaim_state": {
            claim_id: False
            for claim_id in LINUX_CONFINEMENT_PREDICATE_FALSE_CLAIM_IDS
        },
        "operator_contract": {
            "static_type_relation_mismatch_rule_id": (
                "reject-program-artifact-before-evaluation-v1"
            ),
            "evaluation_order_rule_id": (
                "validate-entire-artifact-then-full-topological-"
                "evaluate-each-reachable-node-once-v1"
            ),
            "fault_precedence_rows": [
                {
                    "precedence_rank": 0,
                    "selected_disposition_id": "HARD_FAILURE",
                },
                {
                    "precedence_rank": 1,
                    "selected_disposition_id": "NOT_EVALUATED",
                },
            ],
            "logical_fallback_rule_id": (
                "when-no-fault-operator-computes-logical-true-or-false-v1"
            ),
            "fault_tie_break_field_ids": [
                "disposition_rank",
                "operand_declaration_index",
                "node_index",
            ],
            "no_operand_fault_index_value": 4294967295,
            "no_node_fault_index_value": 4294967295,
            "global_node_index_rule_id": (
                "shaping-node-index-zero-through-s-minus-one-then-"
                "predicate-node-index-s-through-s-plus-p-minus-one-v1"
            ),
            "fault_origin_propagation_rule_id": (
                "retain-earliest-original-operand-and-node-origin-v1"
            ),
            "digest_derivation_rows": [
                {
                    "digest_semantics_id": "PLAIN_SHA256",
                    "preimage_component_ids": ["exact-octet-payload"],
                },
                {
                    "digest_semantics_id": "DOMAIN_SEPARATED_SHA256",
                    "preimage_component_ids": [
                        "digest-domain-ascii",
                        "nul-byte",
                        "u64be-exact-octet-payload-byte-count",
                        "exact-octet-payload",
                    ],
                },
            ],
            "internal_condition_rows": [
                {
                    "executed_error_id": "PREDICATE_FAILED",
                    "internal_condition_id": condition_id,
                }
                for condition_id in (
                    LINUX_CONFINEMENT_PREDICATE_INTERNAL_CONDITION_IDS
                )
            ],
            "internal_disposition_ids": list(
                LINUX_CONFINEMENT_PREDICATE_INTERNAL_DISPOSITION_IDS
            ),
            "interval_order_mode_ids": list(
                LINUX_CONFINEMENT_PREDICATE_INTERVAL_ORDER_MODE_IDS
            ),
            "operator_rows": _operator_rows(),
            "operator_failure_mapping_rows": [
                {
                    "duplicate_or_range_rule_id": "duplicate-hard",
                    "internal_condition_id": "DUPLICATE_VALUE",
                },
                {
                    "duplicate_or_range_rule_id": (
                        "checked-overflow-hard"
                    ),
                    "internal_condition_id": "ARITHMETIC_RANGE",
                },
            ],
            "predicate_operator_ids": list(
                LINUX_CONFINEMENT_PREDICATE_OPERATOR_IDS
            ),
            "predicate_result_ids": list(
                LINUX_CONFINEMENT_PREDICATE_RESULT_IDS
            ),
            "source_operation_outcome_v1": {
                "ordered_component_rows": [
                    {
                        "component_index": 0,
                        "token_domain_id": "source-operation-id",
                        "type_kind_id": "token",
                    },
                    {
                        "component_index": 1,
                        "token_domain_id": "source-availability-id",
                        "type_kind_id": "token",
                    },
                    {
                        "component_index": 2,
                        "token_domain_id": "source-status-id",
                        "type_kind_id": "token",
                    },
                    {
                        "component_index": 3,
                        "token_domain_id": "linux-errno-id",
                        "type_kind_id": "token",
                    },
                ],
                "tuple_binding_rule_id": (
                    "declared-tuple-components-exactly-bind-ordered-"
                    "nominal-token-domain-rows-v1"
                ),
            },
            "truth_mapping_rows": [
                {
                    "executed_error_rule_id": "EMPTY",
                    "internal_condition_rule_id": "EMPTY",
                    "internal_disposition_id": "LOGICAL_TRUE",
                    "predicate_result_id": "PASS",
                },
                {
                    "executed_error_rule_id": (
                        "FIXED_PREDICATE_FAILED"
                    ),
                    "internal_condition_rule_id": (
                        "FIXED_LOGICAL_FALSE"
                    ),
                    "internal_disposition_id": "LOGICAL_FALSE",
                    "predicate_result_id": "FAIL",
                },
                {
                    "executed_error_rule_id": (
                        "PROPAGATE_ORIGIN_EXISTING_ERROR"
                    ),
                    "internal_condition_rule_id": (
                        "PROPAGATE_ORIGIN_CONDITION_OR_EMPTY"
                    ),
                    "internal_disposition_id": "HARD_FAILURE",
                    "predicate_result_id": "FAIL",
                },
                {
                    "executed_error_rule_id": (
                        "PROPAGATE_ORIGIN_EXISTING_ERROR"
                    ),
                    "internal_condition_rule_id": (
                        "PROPAGATE_ORIGIN_CONDITION_OR_EMPTY"
                    ),
                    "internal_disposition_id": "NOT_EVALUATED",
                    "predicate_result_id": "NOT_EVALUATED",
                },
            ],
        },
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
            "formula_core_identity_computation_id": (
                "sha256-domain-nul-u64be-length-canonical-formula-core-"
                "artifact-bytes-v1"
            ),
            "formula_core_artifact_type_id": (
                "heterodiff.adapter.linux-confinement-predicate-formula-"
                "core.v1"
            ),
            "formula_core_digest_domain_id": (
                "heterodiff.adapter.linux-confinement-predicate-formula-"
                "core.v1"
            ),
            "formula_core_schema_id": "predicate-formula-core-v1",
            "formula_core_cross_binding_rule_id": (
                "linux-purpose-binding-formula-core-type-semantics-and-"
                "digest-equal-recomputed-canonical-program-core-generic-"
                "purpose-has-canonical-projection-without-identity-field-v1"
            ),
            "program_purpose_ids": list(
                LINUX_CONFINEMENT_PREDICATE_PROGRAM_PURPOSE_IDS
            ),
            "program_purpose_rows": _program_purpose_rows(),
            "evaluation_result_claim_rule": {
                "conditionally_true_claim_id": (
                    "portable_typed_formula_evaluated"
                ),
                "condition_id": (
                    "validated-program-evaluation-context-and-input-bundle-"
                    "with-root-disposition-computed-v1"
                ),
                "permanently_false_claim_ids": [
                    claim_id
                    for claim_id in (
                        LINUX_CONFINEMENT_PREDICATE_FALSE_CLAIM_IDS
                    )
                    if claim_id != "portable_typed_formula_evaluated"
                ],
            },
            "self_comparison_tautology_admitted": False,
            "short_circuit_evaluation_admitted": False,
            "topological_nodes_required": True,
            "unreachable_nodes_admitted": False,
            "unused_operands_admitted": False,
            "identity_uniqueness_rule_id": (
                "type-operand-shaping-node-and-predicate-node-ids-each-"
                "unique-with-disjoint-node-id-namespaces-v1"
            ),
            "whole_graph_root_rule_id": (
                "root-is-final-predicate-node-all-predicate-nodes-"
                "reachable-all-shaping-nodes-and-derived-operands-"
                "transitively-used-combined-depth-and-reference-ceilings-v1"
            ),
        },
        "resolution_contract": {
            "authority_class_ids": list(
                LINUX_CONFINEMENT_NATIVE_MAPPING_AUTHORITY_CLASS_IDS
            ),
            "input_bundle_row_exact_field_ids": [
                "operand_id",
                "input_state_id",
                "source_artifact_kind_id",
                "source_identity_sha256",
                "value_bytes_hex",
            ],
            "input_state_ids": list(
                LINUX_CONFINEMENT_PREDICATE_INPUT_STATE_IDS
            ),
            "input_state_rows": _input_state_rows(),
            "operand_declaration_exact_field_ids": [
                "operand_id",
                "type_id",
                "value_source_kind_id",
                "resolution_requirement_id",
                "ordered_authority_class_ids",
                "locator",
                "literal_value_bytes_hex",
                "source_shaping_node_id",
            ],
            "resolution_requirement_ids": list(
                LINUX_CONFINEMENT_PREDICATE_RESOLUTION_REQUIREMENT_IDS
            ),
            "resolution_requirement_rows": (
                _resolution_requirement_rows()
            ),
            "source_identity_rule_id": (
                "strict-artifact-kind-and-lowercase-sha256-transport-"
                "commitment-not-authentication-v1"
            ),
            "derived_value_state_rule_id": (
                "full-evaluation-transitively-propagates-input-and-"
                "constructor-dispositions-v1"
            ),
            "value_source_kind_ids": list(
                LINUX_CONFINEMENT_PREDICATE_VALUE_SOURCE_KIND_IDS
            ),
        },
        "resource_limits": resource_limits,
        "selector_contract": {
            "exact_key_match_count": 1,
            "inherited_inventory_locator_kind_ids": list(
                LINUX_CONFINEMENT_NATIVE_MAPPING_OPERAND_LOCATOR_KIND_IDS
            ),
            "executable_input_locator_kind_ids": [
                "generic-conformance-input-slot",
            ] + [
                locator_kind_id
                for locator_kind_id in (
                    LINUX_CONFINEMENT_NATIVE_MAPPING_OPERAND_LOCATOR_KIND_IDS
                )
                if locator_kind_id
                not in {"derived-expression", "fixed-literal"}
            ],
            "non_executable_inherited_locator_kind_ids": [
                "derived-expression",
                "fixed-literal",
            ],
            "language_specific_locator_kind_ids": [
                "generic-conformance-input-slot"
            ],
            "executable_locator_schema_rows": [
                {
                    "exact_field_ids": [
                        "locator_kind_id",
                        "input_slot_id",
                    ],
                    "locator_kind_id": (
                        "generic-conformance-input-slot"
                    ),
                    "ordered_path_segment_count_rule_id": "zero-v1",
                    "program_purpose_admission_ids": [
                        "GENERIC_PORTABLE_CONFORMANCE"
                    ],
                    "resolver_binding_rule_id": (
                        "predicate-language-contract-and-exact-operand-id-"
                        "synthetic-nonclaiming-input-slot-v1"
                    ),
                },
            ] + [
                {
                    "exact_field_ids": [
                        "locator_kind_id",
                        "resolver_contract_artifact_type",
                        "resolver_contract_sha256",
                        "mapping_id",
                        "ordered_path_segments",
                    ],
                    "locator_kind_id": locator_kind_id,
                    "ordered_path_segment_count_rule_id": (
                        "zero-v1"
                        if locator_kind_id
                        in {
                            "decoded-direct-evidence",
                            "sibling-evidence-operand",
                        }
                        else "one-to-sixteen-v1"
                    ),
                    "resolver_binding_rule_id": (
                        "strict-artifact-type-domain-contract-sha256-and-"
                        "mapping-id-resolving-same-53a-occurrence-and-"
                        "membership-in-program-ordered-required-mapping-"
                        "ids-v1"
                    ),
                    "program_purpose_admission_ids": [
                        "LINUX_OBSERVATION_PREDICATE"
                    ],
                }
                for locator_kind_id in (
                    LINUX_CONFINEMENT_NATIVE_MAPPING_OPERAND_LOCATOR_KIND_IDS
                )
                if locator_kind_id
                not in {"derived-expression", "fixed-literal"}
            ],
            "path_segment_kind_ids": list(
                LINUX_CONFINEMENT_PREDICATE_PATH_SEGMENT_KIND_IDS
            ),
            "path_segment_schema_rows": _selector_schema_rows(),
            "schema_list_wildcard_admitted": False,
        },
        "type_contract": {
            "canonical_value_hex_rule": {
                "applied_field_ids": [
                    "literal_value_bytes_hex",
                    "value_bytes_hex",
                    "key_value_bytes_hex",
                ],
                "decoded_value_rule_id": (
                    "exact-declared-type-canonical-payload-and-decoded-"
                    "byte-ceilings-v1"
                ),
                "lexical_rule_id": (
                    "lowercase-even-length-zero-or-more-hex-digits-v1"
                ),
            },
            "collection_count_encoding_id": "unsigned-u64be-v1",
            "digest_semantics_ids": list(
                LINUX_CONFINEMENT_PREDICATE_DIGEST_SEMANTICS_IDS
            ),
            "implicit_conversion_admitted": False,
            "nominal_type_equality_required": True,
            "recursive_types_admitted": False,
            "keyed_table_payload_validation_rule_id": (
                "artifact-validation-rejects-duplicate-canonical-key-"
                "tuples-before-evaluation-v1"
            ),
            "topological_type_rows_required": True,
            "type_kind_ids": list(
                LINUX_CONFINEMENT_PREDICATE_TYPE_KIND_IDS
            ),
            "type_kind_schema_rows": _type_kind_schema_rows(),
            "typed_identity_preimage_computation_id": (
                LINUX_CONFINEMENT_PREDICATE_TYPED_IDENTITY_COMPUTATION_ID
            ),
            "typed_value_identity_sha256_computation_id": (
                "plain-sha256-of-exact-typed-identity-preimage-v1"
            ),
            "u64_interval_payload_validation_rule_id": (
                "every-framed-pair-start-less-or-equal-end-reject-"
                "artifact-before-evaluation-v1"
            ),
            "value_encoding_rows": _value_encoding_rows(),
        },
        "validation_scope_id": (
            LINUX_CONFINEMENT_PREDICATE_LANGUAGE_VALIDATION_SCOPE
        ),
    }


def linux_confinement_predicate_language_contract_bytes() -> bytes:
    """Serialize the exact static language contract."""

    return _canonical_json(
        linux_confinement_predicate_language_contract_tree()
    )


def linux_confinement_predicate_language_contract_plain_sha256() -> str:
    """Return ordinary SHA-256 over the exact contract bytes."""

    return hashlib.sha256(
        linux_confinement_predicate_language_contract_bytes()
    ).hexdigest()


def linux_confinement_predicate_language_contract_sha256() -> str:
    """Return the length-bound domain-separated contract identity."""

    return _domain_sha256(
        LINUX_CONFINEMENT_PREDICATE_LANGUAGE_CONTRACT_DIGEST_DOMAIN,
        linux_confinement_predicate_language_contract_bytes(),
    )


def parse_linux_confinement_predicate_language_contract(
    value: bytes,
) -> dict:
    """Strictly parse the one exact static predicate-language contract."""

    if type(value) is not bytes:
        _fail(LinuxConfinementPredicateLanguageCode.INPUT_TYPE)
    if (
        not value
        or len(value)
        > MAXIMUM_LINUX_CONFINEMENT_PREDICATE_LANGUAGE_ARTIFACT_BYTES
    ):
        _fail(LinuxConfinementPredicateLanguageCode.INPUT_RESOURCE)
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
        _fail(LinuxConfinementPredicateLanguageCode.JSON_INVALID)
    if (
        _json_depth(decoded)
        > MAXIMUM_LINUX_CONFINEMENT_PREDICATE_LANGUAGE_JSON_DEPTH
        or _node_count(decoded)
        > MAXIMUM_LINUX_CONFINEMENT_PREDICATE_LANGUAGE_JSON_ITEMS
    ):
        _fail(LinuxConfinementPredicateLanguageCode.INPUT_RESOURCE)
    expected = linux_confinement_predicate_language_contract_tree()
    if not _same_exact(decoded, expected):
        _fail(LinuxConfinementPredicateLanguageCode.SCHEMA_INVALID)
    if value != linux_confinement_predicate_language_contract_bytes():
        _fail(LinuxConfinementPredicateLanguageCode.CANONICAL_MISMATCH)
    return expected


def _validate_contract_coherence() -> None:
    tree = linux_confinement_predicate_language_contract_tree()
    counts = tree["fixed_counts"]
    type_contract = tree["type_contract"]
    constructor_contract = tree["constructor_contract"]
    operator_contract = tree["operator_contract"]
    resolution_contract = tree["resolution_contract"]
    selector_contract = tree["selector_contract"]
    program_contract = tree["program_contract"]
    artifact_families = tree["artifact_family_rows"]
    nested_schemas = tree["artifact_nested_schema_rows"]
    field_value_schemas = tree["field_value_schema_rows"]

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

    def collect_exact_artifact_field_ids(value: object) -> set:
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

    nested_schema_ids = [
        row["schema_id"] for row in nested_schemas
    ]
    nested_schema_references = [
        schema_id
        for family in artifact_families
        for schema_id in family["nested_schema_ids"]
    ]
    source_kind_schema = next(
        row
        for row in nested_schemas
        if row["schema_id"]
        == "program-operand-row-by-source-kind-v1"
    )
    fault_origin_schema = next(
        row
        for row in nested_schemas
        if row["schema_id"] == "selected-fault-origin-v1"
    )
    inherited_locator_ids = set(
        selector_contract["inherited_inventory_locator_kind_ids"]
    )
    language_locator_ids = set(
        selector_contract["language_specific_locator_kind_ids"]
    )
    executable_locator_ids = set(
        selector_contract["executable_input_locator_kind_ids"]
    )
    non_executable_locator_ids = set(
        selector_contract[
            "non_executable_inherited_locator_kind_ids"
        ]
    )
    inherited_executable_ids = (
        executable_locator_ids - language_locator_ids
    )
    constructor_hard_rules = {
        row["failure_rule_id"]
        for row in constructor_contract["constructor_rows"]
        if row["failure_rule_id"] != "none"
    }
    constructor_mapped_rules = {
        row["failure_rule_id"]
        for row in constructor_contract[
            "constructor_failure_mapping_rows"
        ]
    }
    operator_hard_rules = {
        row["duplicate_or_range_rule_id"]
        for row in operator_contract["operator_rows"]
        if row["duplicate_or_range_rule_id"]
        in {"duplicate-hard", "checked-overflow-hard"}
    }
    operator_mapped_rules = {
        row["duplicate_or_range_rule_id"]
        for row in operator_contract["operator_failure_mapping_rows"]
    }
    exact_artifact_field_ids = collect_exact_artifact_field_ids(tree)
    covered_field_ids = [
        field_id
        for row in field_value_schemas
        for field_id in row["field_ids"]
    ]
    if (
        counts
        != {
            "artifact_family_count": 4,
            "artifact_identity_reference_count": 6,
            "artifact_nested_schema_count": 12,
            "authority_class_count": 9,
            "constructor_count": 12,
            "digest_semantics_count": 2,
            "executable_locator_kind_count": 10,
            "false_claim_count": 15,
            "field_value_schema_covered_field_count": 115,
            "field_value_schema_count": 13,
            "input_state_count": 7,
            "internal_condition_count": 7,
            "internal_disposition_count": 4,
            "json_kind_count": 5,
            "operator_count": 20,
            "path_segment_kind_count": 3,
            "program_purpose_count": 2,
            "resolution_requirement_count": 3,
            "shaping_value_state_count": 3,
            "type_kind_count": 10,
            "value_source_kind_count": 3,
        }
        or len(tree["artifact_family_rows"]) != 4
        or len(tree["artifact_identity_reference_rows"]) != 6
        or len(nested_schemas) != 12
        or len(field_value_schemas) != 13
        or len(tree["constructor_contract"]["constructor_rows"]) != 12
        or len(tree["operator_contract"]["operator_rows"]) != 20
        or len(tree["type_contract"]["type_kind_schema_rows"]) != 10
        or len(tree["type_contract"]["value_encoding_rows"]) != 10
        or len(
            tree["resolution_contract"]["input_state_rows"]
        ) != 7
        or len(
            tree["resolution_contract"]["resolution_requirement_rows"]
        ) != 3
        or not field_id_lists_are_unique(tree)
        or counts["field_value_schema_count"]
        != len(field_value_schemas)
        or counts["field_value_schema_covered_field_count"]
        != len(covered_field_ids)
        or counts["json_kind_count"]
        != len(tree["field_value_json_kind_ids"])
        or not unique(
            [row["value_schema_id"] for row in field_value_schemas]
        )
        or any(
            not row["field_ids"]
            or row["field_ids"] != sorted(row["field_ids"])
            for row in field_value_schemas
        )
        or [
            row["value_schema_id"] for row in field_value_schemas
        ]
        != [
            "fixed-format-version-v1",
            "strict-identifier-string-v1",
            "empty-or-strict-identifier-string-v1",
            "lowercase-sha256-string-v1",
            "empty-or-lowercase-sha256-string-v1",
            "canonical-payload-hex-string-v1",
            "nonzero-context-nonce-hex-string-v1",
            "nonnegative-index-or-count-integer-v1",
            "claim-boolean-v1",
            "ordered-identifier-array-v1",
            "ordered-index-array-v1",
            "ordered-exact-object-row-array-v1",
            "context-refined-exact-object-v1",
        ]
        or not unique(covered_field_ids)
        or len(covered_field_ids) != 115
        or set(covered_field_ids) != exact_artifact_field_ids
        or tree["field_value_json_kind_ids"]
        != ["array", "boolean", "integer", "object", "string"]
        or {
            row["admitted_json_kind_id"]
            for row in field_value_schemas
        }
        != {"array", "boolean", "integer", "object", "string"}
        or not unique(
            [row["artifact_family_id"] for row in artifact_families]
        )
        or [
            row["artifact_family_id"] for row in artifact_families
        ]
        != list(LINUX_CONFINEMENT_PREDICATE_ARTIFACT_FAMILY_IDS)
        or not unique(
            [row["artifact_type_id"] for row in artifact_families]
        )
        or not unique(nested_schema_ids)
        or counts["artifact_nested_schema_count"]
        != len(nested_schema_ids)
        or counts["artifact_identity_reference_count"]
        != len(tree["artifact_identity_reference_rows"])
        or counts["authority_class_count"]
        != len(resolution_contract["authority_class_ids"])
        or not unique(resolution_contract["authority_class_ids"])
        or counts["false_claim_count"] != len(tree["nonclaim_state"])
        or not unique(list(tree["nonclaim_state"]))
        or counts["digest_semantics_count"]
        != len(type_contract["digest_semantics_ids"])
        or not unique(type_contract["digest_semantics_ids"])
        or counts["internal_disposition_count"]
        != len(operator_contract["internal_disposition_ids"])
        or not unique(operator_contract["internal_disposition_ids"])
        or counts["internal_condition_count"]
        != len(operator_contract["internal_condition_rows"])
        or counts["program_purpose_count"]
        != len(program_contract["program_purpose_ids"])
        or not unique(program_contract["program_purpose_ids"])
        or counts["shaping_value_state_count"]
        != len(constructor_contract["shaping_value_state_ids"])
        or not unique(constructor_contract["shaping_value_state_ids"])
        or counts["executable_locator_kind_count"]
        != len(selector_contract["executable_input_locator_kind_ids"])
        or not unique(
            selector_contract["executable_input_locator_kind_ids"]
        )
        or set(nested_schema_references) != set(nested_schema_ids)
        or not unique(
            [
                row["field_id"]
                for row in tree["artifact_identity_reference_rows"]
            ]
        )
        or [
            row["type_kind_id"]
            for row in type_contract["type_kind_schema_rows"]
        ]
        != type_contract["type_kind_ids"]
        or [
            row["type_kind_id"]
            for row in type_contract["value_encoding_rows"]
        ]
        != type_contract["type_kind_ids"]
        or [
            row["constructor_id"]
            for row in constructor_contract["constructor_rows"]
        ]
        != constructor_contract["shaping_constructor_ids"]
        or [
            row["operator_id"]
            for row in operator_contract["operator_rows"]
        ]
        != operator_contract["predicate_operator_ids"]
        or [
            row["input_state_id"]
            for row in resolution_contract["input_state_rows"]
        ]
        != resolution_contract["input_state_ids"]
        or [
            row["resolution_requirement_id"]
            for row in resolution_contract[
                "resolution_requirement_rows"
            ]
        ]
        != resolution_contract["resolution_requirement_ids"]
        or [
            row["value_source_kind_id"]
            for row in source_kind_schema["source_kind_rule_rows"]
        ]
        != resolution_contract["value_source_kind_ids"]
        or [
            row["segment_kind_id"]
            for row in selector_contract["path_segment_schema_rows"]
        ]
        != selector_contract["path_segment_kind_ids"]
        or {
            row["locator_kind_id"]
            for row in selector_contract[
                "executable_locator_schema_rows"
            ]
        }
        != executable_locator_ids
        or language_locator_ids & inherited_locator_ids
        or inherited_executable_ids & non_executable_locator_ids
        or inherited_executable_ids | non_executable_locator_ids
        != inherited_locator_ids
        or [
            row["program_purpose_id"]
            for row in program_contract["program_purpose_rows"]
        ]
        != program_contract["program_purpose_ids"]
        or constructor_hard_rules | {"resource"}
        != constructor_mapped_rules
        or [
            row["failure_class_id"]
            for row in constructor_contract[
                "constructor_failure_precedence_rows"
            ]
        ]
        != [
            "PROPAGATED_INPUT_FAULT",
            "CONSTRUCTOR_SPECIFIC",
            "OUTPUT_RESOURCE",
        ]
        or [
            row["precedence_rank"]
            for row in constructor_contract[
                "constructor_failure_precedence_rows"
            ]
        ]
        != [0, 1, 2]
        or operator_hard_rules != operator_mapped_rules
        or [
            row["internal_condition_id"]
            for row in operator_contract["internal_condition_rows"]
        ]
        != list(LINUX_CONFINEMENT_PREDICATE_INTERNAL_CONDITION_IDS)
        or [
            row["internal_disposition_id"]
            for row in operator_contract["truth_mapping_rows"]
        ]
        != list(LINUX_CONFINEMENT_PREDICATE_INTERNAL_DISPOSITION_IDS)
        or {
            row["selected_disposition_id"]
            for row in operator_contract["fault_precedence_rows"]
        }
        != {"HARD_FAILURE", "NOT_EVALUATED"}
        or [
            row["origin_kind_id"]
            for row in fault_origin_schema["origin_kind_rule_rows"]
        ]
        != fault_origin_schema["origin_kind_ids"]
        or constructor_contract["shaping_value_state_ids"]
        != list(LINUX_CONFINEMENT_PREDICATE_SHAPING_VALUE_STATE_IDS)
        or any(tree["nonclaim_state"].values())
        or tree["constructor_contract"][
            "native_or_external_parser_constructor_count"
        ] != 0
        or tree["selector_contract"]["schema_list_wildcard_admitted"]
        is not False
        or tree["program_contract"]["short_circuit_evaluation_admitted"]
        is not False
    ):
        raise RuntimeError(
            _ERROR_MESSAGES[
                LinuxConfinementPredicateLanguageCode.CONTRACT_DRIFT
            ]
        )


_validate_contract_coherence()


__all__ = [
    "LINUX_CONFINEMENT_PREDICATE_ARTIFACT_FAMILY_IDS",
    "LINUX_CONFINEMENT_PREDICATE_DIGEST_SEMANTICS_IDS",
    "LINUX_CONFINEMENT_PREDICATE_FALSE_CLAIM_IDS",
    "LINUX_CONFINEMENT_PREDICATE_IDENTIFIER_GRAMMAR",
    "LINUX_CONFINEMENT_PREDICATE_INPUT_STATE_IDS",
    "LINUX_CONFINEMENT_PREDICATE_INTERNAL_CONDITION_IDS",
    "LINUX_CONFINEMENT_PREDICATE_INTERNAL_DISPOSITION_IDS",
    "LINUX_CONFINEMENT_PREDICATE_INTERVAL_ORDER_MODE_IDS",
    "LINUX_CONFINEMENT_PREDICATE_LANGUAGE_CONTRACT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_PREDICATE_LANGUAGE_CONTRACT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_PREDICATE_LANGUAGE_CONTRACT_STATUS",
    "LINUX_CONFINEMENT_PREDICATE_LANGUAGE_DIGEST_COMPUTATION_ID",
    "LINUX_CONFINEMENT_PREDICATE_LANGUAGE_ENCODING_ID",
    "LINUX_CONFINEMENT_PREDICATE_LANGUAGE_VALIDATION_SCOPE",
    "LINUX_CONFINEMENT_PREDICATE_OPERATOR_IDS",
    "LINUX_CONFINEMENT_PREDICATE_PATH_SEGMENT_KIND_IDS",
    "LINUX_CONFINEMENT_PREDICATE_PROGRAM_PURPOSE_IDS",
    "LINUX_CONFINEMENT_PREDICATE_RESOLUTION_REQUIREMENT_IDS",
    "LINUX_CONFINEMENT_PREDICATE_RESULT_IDS",
    "LINUX_CONFINEMENT_PREDICATE_SHAPING_CONSTRUCTOR_IDS",
    "LINUX_CONFINEMENT_PREDICATE_SHAPING_VALUE_STATE_IDS",
    "LINUX_CONFINEMENT_PREDICATE_TYPED_IDENTITY_COMPUTATION_ID",
    "LINUX_CONFINEMENT_PREDICATE_TYPE_KIND_IDS",
    "LINUX_CONFINEMENT_PREDICATE_VALUE_SOURCE_KIND_IDS",
    "MAXIMUM_LINUX_CONFINEMENT_PREDICATE_LANGUAGE_ARTIFACT_BYTES",
    "LinuxConfinementPredicateLanguageCode",
    "LinuxConfinementPredicateLanguageError",
    "linux_confinement_predicate_language_contract_bytes",
    "linux_confinement_predicate_language_contract_plain_sha256",
    "linux_confinement_predicate_language_contract_sha256",
    "linux_confinement_predicate_language_contract_tree",
    "parse_linux_confinement_predicate_language_contract",
]
