"""Independent verifier for the portable Linux native-mapping gap ledger.

This module intentionally does not import the companion native-mapping
builder.  It reconstructs the exact V1 ledger from the public evidence plan
and the implementation-separated semantic contract, parses caller-supplied
canonical bytes, and verifies complete unresolved coverage of 112 field
occurrences, 111 unique field profiles, 502 projection-leaf occurrences, and
24 predicates.

Successful verification proves only the static gap inventory.  It does not
acquire Linux evidence, implement a native parser or derivation, evaluate a
predicate, authenticate origin or custody, authorize release, establish
confinement, or support an empirical claim.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
import hashlib
import json
import re
from typing import Final

from .adapter_linux_confinement_acceptance import (
    linux_confinement_acceptance_contract_sha256,
)
from .adapter_linux_confinement_evidence import (
    linux_confinement_evidence_schema_contract_sha256,
)
from .adapter_linux_confinement_evidence_plan import (
    linux_confinement_evidence_plan_sha256,
    linux_confinement_evidence_plan_tree,
)
from .adapter_linux_confinement_policy import (
    LINUX_CONFINEMENT_POLICY_ARTIFACT_TYPE,
)
from .adapter_linux_confinement_semantic_verifier import (
    linux_confinement_semantic_verifier_contract_sha256,
    linux_confinement_semantic_verifier_contract_tree,
)
from .adapter_linux_confinement_staging_protocol import (
    linux_confinement_staging_protocol_contract_sha256,
)


LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_IMPLEMENTATION_SEPARATED_VERIFIER_ID: (
    Final
) = (
    "heterodiff.adapter.linux-confinement-native-mapping-gap-"
    "implementation-separated-verifier.v1"
)
LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_RESULT_ARTIFACT_TYPE: (
    Final
) = (
    "heterodiff.adapter.linux-confinement-native-mapping-gap-"
    "implementation-separated-verification-result.v1"
)
LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_RESULT_DIGEST_DOMAIN: (
    Final
) = LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_RESULT_ARTIFACT_TYPE
LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFIER_IMPLEMENTATION_STATUS: Final = (
    "IMPLEMENTATION_SEPARATED_PORTABLE_UNRESOLVED_MAPPING_GAP_VERIFIER_"
    "IMPLEMENTED"
)
LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_STATUS: Final = (
    "EXACT_CANONICAL_ANCHOR_OCCURRENCE_PROFILE_PROJECTION_LEAF_PREDICATE_"
    "AND_BLOCKING_GAP_COVERAGE_VALIDATED"
)
MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_RESULT_BYTES: (
    Final
) = 64 * 1024
_RESULT_ARTIFACT_TYPE: Final = (
    LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_RESULT_ARTIFACT_TYPE
)
_IMPLEMENTATION_SEPARATED_VERIFIER_ID: Final = (
    LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_IMPLEMENTATION_SEPARATED_VERIFIER_ID
)
_MAX_RESULT_BYTES: Final = (
    MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_RESULT_BYTES
)

_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-native-mapping-gap-contract.v1"
)
_CONTRACT_DIGEST_DOMAIN: Final = _CONTRACT_ARTIFACT_TYPE
_CONTRACT_STATUS: Final = (
    "PORTABLE_PREDICATE_MAPPING_INVENTORY_AND_GAP_CONTRACT_IMPLEMENTED"
)
_VALIDATION_SCOPE: Final = (
    "EXACT_UNRESOLVED_OCCURRENCE_PREDICATE_AND_PROJECTION_LEAF_COVERAGE_ONLY"
)
_ENCODING_ID: Final = "canonical-ascii-json-sort-keys-no-whitespace-v1"
_DIGEST_COMPUTATION_ID: Final = (
    "sha256-domain-nul-u64be-length-canonical-bytes-v1"
)
_OCCURRENCE_IDENTITY_COMPUTATION_ID: Final = (
    "utf8-observation-id-nul-ascii-decimal-index-nul-field-id-v1"
)
_V1_CONTRACT_SHA256: Final = (
    "db1f84a608d306a7955a9cb4d3a633456a7064094c9cd78c2ef28eeaea3956e3"
)
_V1_CONTRACT_PLAIN_SHA256: Final = (
    "6194f0eec126122bcf2710288697bc8cd550824ee8a1d3b946ab8c544b650540"
)
_V1_CONTRACT_BYTE_COUNT: Final = 571156
_V1_SEMANTIC_CONTRACT_SHA256: Final = (
    "11a2e7890039a1bb4ca19a571e3a3772a750afb24af24e01e5f3928c9092804e"
)
_CODEC_RECORD: Final = "canonical-ascii-json-object-v1"
_MAX_CONTRACT_BYTES: Final = 4 * 1024 * 1024
_MAX_JSON_DEPTH: Final = 32
_MAX_JSON_ITEMS: Final = 65536
_MAX_JSON_INTEGER_DIGITS: Final = 20
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")

_GAP_IDS: Final = (
    "NATIVE_SOURCE_TO_EVIDENCE_VALUE_DERIVATION_UNDEFINED",
    "EVIDENCE_OR_PROJECTION_TO_OPERAND_MAPPING_UNDEFINED",
    "PREDICATE_FORMULA_UNDEFINED",
    "SOURCE_AVAILABILITY_SEMANTICS_UNDEFINED",
    "EXTERNAL_AUTHORITY_PREIMAGE_UNAVAILABLE",
    "AUTHORIZING_GATE_BINDING_UNDEFINED",
    "CUSTODY_OR_PROVENANCE_UNANCHORED",
    "OPERAND_COVERAGE_NONVACUITY_UNPROVED",
)

_OPERAND_LOCATOR_KIND_IDS: Final = (
    "bound-artifact-member",
    "canonical-policy-path",
    "canonical-projection-path",
    "capture-binding-field",
    "decoded-direct-evidence",
    "derived-expression",
    "fixed-literal",
    "process-snapshot-field",
    "sibling-evidence-operand",
    "staging-event-field",
    "subject-identity-component",
)

_AUTHORITY_CLASS_IDS: Final = (
    "canonical-policy-path",
    "run-binding-field",
    "subject-or-snapshot-field",
    "staging-contract-field",
    "external-artifact-manifest-field",
    "external-platform-profile-field",
    "external-custody-field",
    "native-transcript-field",
    "derived-cross-record-field",
)

_OPERAND_PATH_SEGMENT_KIND_IDS: Final = (
    "declared-keyed-list-item",
    "list-index",
    "object-key",
)

_PROJECTION_SCHEMA_PATH_SEGMENT_KIND_IDS: Final = (
    "object-key",
    "schema-list-item",
)

_PREDICATE_OPERATOR_IDS: Final = (
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

_PREDICATE_RESULT_IDS: Final = ("PASS", "FAIL", "NOT_EVALUATED")

_EXECUTED_ERROR_IDS: Final = (
    "UNSUPPORTED_PLATFORM",
    "INPUT_TYPE",
    "INPUT_RESOURCE",
    "CONTRACT_DRIFT",
    "ARTIFACT_PIN_MISMATCH",
    "AUTHORITY_UNAVAILABLE",
    "CUSTODY_UNANCHORED",
    "SYSCALL_FAILED",
    "SOURCE_TRUNCATED",
    "SOURCE_TRAILING",
    "SOURCE_UNAVAILABLE",
    "IDENTITY_RACE",
    "PIDFD_BINDING_MISMATCH",
    "PARSER_REJECTED",
    "DERIVATION_MISMATCH",
    "PREDICATE_FAILED",
    "PREDICATE_NOT_EVALUATED",
    "CONTROL_ORACLE_FAILED",
    "TRANSCRIPT_ORDER",
    "TRANSCRIPT_BINDING",
    "DEADLINE_EXPIRED",
    "REAP_INCOMPLETE",
    "CGROUP_NOT_EMPTY",
    "STREAM_NOT_DRAINED",
    "INTERNAL",
)

_FALSE_CLAIM_IDS: Final = (
    "authorizing_gate_implemented",
    "custody_authenticated",
    "empirical_result_established",
    "hostile_controls_executed",
    "linux_confinement_established",
    "linux_execution_observed",
    "native_acquisition_implemented",
    "native_origin_authenticated",
    "policy_predicate_evaluated",
    "predicate_formula_implemented",
    "predicate_preimage_constructed",
    "raw_source_projection_relation_validated",
    "release_authorized",
    "teardown_executed",
)

_EXTERNAL_AUTHORITY_OBSERVATION_IDS: Final = frozenset(
    (
        "backend-static-sealed-executable-identity-matched",
        "cgroup-v2-leaf-owned-by-supervisor",
        "dependency-lock-identity-matched",
        "immutable-runtime-rootfs-identity-matched",
        "landlock-abi-and-ruleset-matched",
        "linux-platform-profile-matched",
        "sandbox-bootstrap-identity-matched",
        "sandbox-interpreter-identity-matched",
        "seccomp-filter-and-architecture-observed-before-release",
        "supervisor-dependency-closure-identity-matched",
        "supervisor-executable-identity-matched",
    )
)

_TRANSPORT_DECODER_ID_BY_CODEC: Final = {
    "bounded-opaque-octets-v1": (
        "bounded-opaque-octets-transport-decoder-v1"
    ),
    "canonical-ascii-json-object-v1": (
        "canonical-ascii-json-object-transport-decoder-v1"
    ),
    "nul-terminated-ordered-octet-strings-v1": (
        "nul-terminated-ordered-octet-strings-transport-decoder-v1"
    ),
    "sha256-lowercase-hex-ascii-v1": (
        "sha256-lowercase-hex-ascii-transport-decoder-v1"
    ),
    "unsigned-u64be-v1": "unsigned-u64be-transport-decoder-v1",
}


class LinuxConfinementNativeMappingGapVerificationCode(str, Enum):
    """Closed failures emitted by the independent gap verifier."""

    INPUT_TYPE = "INPUT_TYPE"
    INPUT_RESOURCE = "INPUT_RESOURCE"
    JSON_INVALID = "JSON_INVALID"
    CANONICAL_INVALID = "CANONICAL_INVALID"
    CONTRACT_MISMATCH = "CONTRACT_MISMATCH"
    ARTIFACT_PIN_MISMATCH = "ARTIFACT_PIN_MISMATCH"
    RESULT_INVALID = "RESULT_INVALID"


_ERROR_MESSAGES: Final = {
    LinuxConfinementNativeMappingGapVerificationCode.INPUT_TYPE: (
        "Linux native mapping gap verification input has an invalid exact type"
    ),
    LinuxConfinementNativeMappingGapVerificationCode.INPUT_RESOURCE: (
        "Linux native mapping gap verification input exceeds its resource "
        "ceiling"
    ),
    LinuxConfinementNativeMappingGapVerificationCode.JSON_INVALID: (
        "Linux native mapping gap verification JSON is invalid"
    ),
    LinuxConfinementNativeMappingGapVerificationCode.CANONICAL_INVALID: (
        "Linux native mapping gap verification bytes are not canonical"
    ),
    LinuxConfinementNativeMappingGapVerificationCode.CONTRACT_MISMATCH: (
        "Linux native mapping gap verification contract does not match V1"
    ),
    LinuxConfinementNativeMappingGapVerificationCode.ARTIFACT_PIN_MISMATCH: (
        "Linux native mapping gap verification artifact pin does not match"
    ),
    LinuxConfinementNativeMappingGapVerificationCode.RESULT_INVALID: (
        "Linux native mapping gap verification result is invalid"
    ),
}


class LinuxConfinementNativeMappingGapVerificationError(ValueError):
    """One fixed-message independent-verifier failure."""

    def __init__(
        self,
        code: LinuxConfinementNativeMappingGapVerificationCode,
    ) -> None:
        if type(code) is not LinuxConfinementNativeMappingGapVerificationCode:
            raise TypeError(
                "native mapping gap verification code must be exact"
            )
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class _DuplicateKeyError(ValueError):
    pass


def _fail(
    code: LinuxConfinementNativeMappingGapVerificationCode,
) -> None:
    raise LinuxConfinementNativeMappingGapVerificationError(code) from None


def _domain_sha256(domain: str, value: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(domain.encode("ascii"))
    digest.update(b"\x00")
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)
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
        _fail(
            LinuxConfinementNativeMappingGapVerificationCode.RESULT_INVALID
        )
    if not result or len(result) > maximum:
        _fail(
            LinuxConfinementNativeMappingGapVerificationCode.INPUT_RESOURCE
        )
    return result


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _reject_float(_: str) -> object:
    raise ValueError("floating-point JSON number")


def _reject_constant(_: str) -> object:
    raise ValueError("non-finite JSON constant")


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
        if maximum > _MAX_JSON_DEPTH:
            return maximum
        if type(current) is dict:
            stack.extend(
                (item, depth + 1)
                for item in current.values()
            )
        elif type(current) is list:
            stack.extend((item, depth + 1) for item in current)
    return maximum


def _typed_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return (
            set(left) == set(right)
            and all(_typed_equal(left[key], right[key]) for key in right)
        )
    if type(left) is list:
        return (
            len(left) == len(right)
            and all(
                _typed_equal(left_item, right_item)
                for left_item, right_item in zip(left, right)
            )
        )
    return left == right


def _parse_contract(value: bytes) -> dict:
    if type(value) is not bytes:
        _fail(LinuxConfinementNativeMappingGapVerificationCode.INPUT_TYPE)
    if not value or len(value) > _MAX_CONTRACT_BYTES:
        _fail(
            LinuxConfinementNativeMappingGapVerificationCode.INPUT_RESOURCE
        )
    try:
        decoded = json.loads(
            value.decode("ascii", "strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
            parse_int=_bounded_json_integer,
        )
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _fail(LinuxConfinementNativeMappingGapVerificationCode.JSON_INVALID)
    if (
        type(decoded) is not dict
        or _json_depth(decoded) > _MAX_JSON_DEPTH
        or _node_count(decoded) > _MAX_JSON_ITEMS
    ):
        _fail(
            LinuxConfinementNativeMappingGapVerificationCode.INPUT_RESOURCE
        )
    try:
        canonical = json.dumps(
            decoded,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _fail(LinuxConfinementNativeMappingGapVerificationCode.JSON_INVALID)
    if value != canonical:
        _fail(
            LinuxConfinementNativeMappingGapVerificationCode.CANONICAL_INVALID
        )
    return decoded


def _schema_path_id(segments: tuple) -> str:
    tokens = ["values"]
    for kind_id, token in segments:
        if kind_id == "object-key":
            tokens.append(token)
        elif kind_id == "schema-list-item":
            tokens.append("[]")
        else:
            raise RuntimeError("Linux native mapping V1 contract drifted")
    return "/" + "/".join(tokens)


def _segment(kind_id: str, token: str) -> dict:
    return {"path_token": token, "segment_kind_id": kind_id}


def _projection_leaf_inventory(
    node: dict,
    segments: tuple = (),
) -> list:
    try:
        kind_id = node["node_kind_id"]
    except (KeyError, TypeError):
        raise RuntimeError(
            "Linux native mapping V1 contract drifted"
        ) from None
    if kind_id == "object":
        result = []
        for field_row in node["field_rows"]:
            result.extend(
                _projection_leaf_inventory(
                    field_row["schema"],
                    segments
                    + (("object-key", field_row["field_id"]),),
                )
            )
        return result
    if kind_id == "list":
        return _projection_leaf_inventory(
            node["item_schema"],
            segments + (("schema-list-item", ""),),
        )
    return [
        {
            "coverage_status_id": "UNRESOLVED",
            "node_kind_id": kind_id,
            "schema_path_id": _schema_path_id(segments),
            "path_segments": [
                _segment(segment_kind_id, token)
                for segment_kind_id, token in segments
            ],
        }
    ]


def _mapping_id(
    observation_id: str,
    field_occurrence_index: int,
    field_id: str,
) -> str:
    return (
        "heterodiff.adapter.linux-native-field-mapping."
        + observation_id
        + "."
        + str(field_occurrence_index)
        + "."
        + field_id
        + ".v1"
    )


def _field_profile_id(field_id: str) -> str:
    return (
        "heterodiff.adapter.linux-native-field-profile."
        + field_id
        + ".v1"
    )


def _blocking_gap_ids(observation_id: str) -> list:
    return [
        gap_id
        for gap_id in _GAP_IDS
        if (
            gap_id != "EXTERNAL_AUTHORITY_PREIMAGE_UNAVAILABLE"
            or observation_id in _EXTERNAL_AUTHORITY_OBSERVATION_IDS
        )
    ]


def _independent_rows() -> tuple:
    plan = linux_confinement_evidence_plan_tree()
    semantic = linux_confinement_semantic_verifier_contract_tree()
    plan_observations = plan["observation_specs"]
    semantic_observations = semantic["observation_schemas"]
    plan_observation_ids = [
        row["item_id"] for row in plan_observations
    ]
    semantic_observation_ids = [
        row["observation_id"] for row in semantic_observations
    ]
    if (
        len(plan_observation_ids) != len(set(plan_observation_ids))
        or len(semantic_observation_ids)
        != len(set(semantic_observation_ids))
        or plan_observation_ids != semantic_observation_ids
    ):
        raise RuntimeError("Linux native mapping V1 contract drifted")
    semantic_by_observation = {
        row["observation_id"]: row
        for row in semantic_observations
    }
    projection_registry = semantic["canonical_projection_schema"][
        "projection_registry"
    ]
    projection_field_ids = [
        row["field_id"] for row in projection_registry
    ]
    if len(projection_field_ids) != len(set(projection_field_ids)):
        raise RuntimeError("Linux native mapping V1 contract drifted")
    projection_by_field = {
        row["field_id"]: row
        for row in projection_registry
    }
    occurrence_rows = []
    predicate_rows = []
    projection_leaf_count = 0
    for observation in plan_observations:
        observation_id = observation["item_id"]
        try:
            semantic_observation = semantic_by_observation[observation_id]
        except KeyError:
            raise RuntimeError(
                "Linux native mapping V1 contract drifted"
            ) from None
        semantic_fields = semantic_observation["raw_evidence_fields"]
        if (
            [field["field_id"] for field in semantic_fields]
            != observation["raw_evidence_field_ids"]
        ):
            raise RuntimeError("Linux native mapping V1 contract drifted")
        ordered_mapping_ids = []
        for occurrence_index, field in enumerate(semantic_fields):
            field_id = field["field_id"]
            codec_id = field["value_codec_id"]
            is_record = codec_id == _CODEC_RECORD
            projection_schema_id = ""
            leaf_rows = []
            parser_id = ""
            if is_record:
                try:
                    projection = projection_by_field[field_id]
                except KeyError:
                    raise RuntimeError(
                        "Linux native mapping V1 contract drifted"
                    ) from None
                projection_schema_id = projection["projection_schema_id"]
                leaf_rows = _projection_leaf_inventory(
                    projection["values_schema"]
                )
                projection_leaf_count += len(leaf_rows)
                parser_id = (
                    "heterodiff.adapter.linux-evidence-parser."
                    + field_id
                    + ".v1"
                )
            mapping_id = _mapping_id(
                observation_id,
                occurrence_index,
                field_id,
            )
            ordered_mapping_ids.append(mapping_id)
            occurrence_rows.append(
                {
                    "assertion_rows": [],
                    "blocking_gap_ids": _blocking_gap_ids(observation_id),
                    "comparator_id": field["comparator_id"],
                    "direct_value_coverage_status_id": (
                        "NOT_APPLICABLE" if is_record else "UNRESOLVED"
                    ),
                    "field_id": field_id,
                    "field_occurrence_index": occurrence_index,
                    "field_profile_id": _field_profile_id(field_id),
                    "lifecycle_stage_id": observation[
                        "lifecycle_stage_id"
                    ],
                    "mapping_id": mapping_id,
                    "mapping_resolution_id": "UNRESOLVED",
                    "native_derivation_contract_id": "",
                    "native_derivation_contract_sha256": "",
                    "semantic_projection_parser_id": parser_id,
                    "semantic_projection_parser_sha256": "",
                    "normalization_rows": [],
                    "observation_id": observation_id,
                    "positive_mapping_enabled": False,
                    "predicate_id": observation["predicate_id"],
                    "primitive_transform_contract_id": "",
                    "primitive_transform_contract_sha256": "",
                    "procedure_id": observation["procedure_id"],
                    "produced_predicate_operand_ids": [],
                    "projection_leaf_inventory_rows": leaf_rows,
                    "projection_schema_id": projection_schema_id,
                    "raw_to_projection_parser_required": is_record,
                    "semantic_type_id": field["semantic_type_id"],
                    "snapshot_stage_id": semantic_observation[
                        "snapshot_stage_id"
                    ],
                    "source_availability_rule_id": "UNRESOLVED",
                    "source_operand_rows": [],
                    "source_operation_rows": [],
                    "subject_role_ids": observation["subject_role_ids"],
                    "target_operand_rows": [],
                    "transport_decoder_id": (
                        _TRANSPORT_DECODER_ID_BY_CODEC[codec_id]
                    ),
                    "trusted_producer_id": observation[
                        "trusted_producer_id"
                    ],
                    "value_codec_id": codec_id,
                }
            )
        predicate_rows.append(
            {
                "blocking_gap_ids": _blocking_gap_ids(observation_id),
                "observation_id": observation_id,
                "ordered_mapping_ids": ordered_mapping_ids,
                "parser_failure_result_id": "FAIL",
                "positive_evaluation_enabled": False,
                "predicate_id": observation["predicate_id"],
                "predicate_resolution_id": "UNRESOLVED",
                "receipt_leaf_id": observation["receipt_leaf_id"],
                "required_bound_artifact_ids": [],
                "required_context_operand_ids": [],
                "required_policy_operand_ids": [],
                "required_subject_operand_ids": [],
                "root_assertion_id": "",
                "source_unavailable_result_id": "FAIL",
                "unresolved_mapping_result_id": "NOT_EVALUATED",
            }
        )
    record_field_ids = [
        row["field_id"]
        for row in occurrence_rows
        if row["raw_to_projection_parser_required"]
    ]
    if (
        len(occurrence_rows) != 112
        or len({row["field_id"] for row in occurrence_rows}) != 111
        or len(record_field_ids) != 85
        or sorted(set(record_field_ids)) != projection_field_ids
        or len(projection_field_ids) != 84
    ):
        raise RuntimeError("Linux native mapping V1 contract drifted")
    return occurrence_rows, predicate_rows, projection_leaf_count


def _field_profiles(occurrence_rows: list) -> list:
    grouped = {}
    for occurrence in occurrence_rows:
        field_id = occurrence["field_id"]
        if field_id not in grouped:
            grouped[field_id] = {
                "blocking_gap_ids": list(
                    occurrence["blocking_gap_ids"]
                ),
                "comparator_id": occurrence["comparator_id"],
                "field_id": field_id,
                "field_profile_id": occurrence["field_profile_id"],
                "semantic_projection_parser_id": occurrence[
                    "semantic_projection_parser_id"
                ],
                "semantic_projection_parser_sha256": "",
                "ordered_mapping_ids": [],
                "ordered_observation_ids": [],
                "positive_mapping_enabled": False,
                "primitive_transform_contract_id": "",
                "primitive_transform_contract_sha256": "",
                "projection_leaf_schema_count": len(
                    occurrence["projection_leaf_inventory_rows"]
                ),
                "projection_schema_id": occurrence[
                    "projection_schema_id"
                ],
                "raw_to_projection_parser_required": occurrence[
                    "raw_to_projection_parser_required"
                ],
                "semantic_type_id": occurrence["semantic_type_id"],
                "unique_profile_resolution_id": "UNRESOLVED",
                "value_codec_id": occurrence["value_codec_id"],
            }
        profile = grouped[field_id]
        comparable = (
            "comparator_id",
            "field_profile_id",
            "semantic_projection_parser_id",
            "projection_schema_id",
            "raw_to_projection_parser_required",
            "semantic_type_id",
            "value_codec_id",
        )
        if any(
            profile[key] != occurrence[key]
            for key in comparable
        ) or profile["projection_leaf_schema_count"] != len(
            occurrence["projection_leaf_inventory_rows"]
        ):
            raise RuntimeError("Linux native mapping V1 contract drifted")
        profile["ordered_mapping_ids"].append(occurrence["mapping_id"])
        profile["ordered_observation_ids"].append(
            occurrence["observation_id"]
        )
        profile["blocking_gap_ids"] = [
            gap_id
            for gap_id in _GAP_IDS
            if (
                gap_id in profile["blocking_gap_ids"]
                or gap_id in occurrence["blocking_gap_ids"]
            )
        ]
    return [
        dict(profile, occurrence_count=len(profile["ordered_mapping_ids"]))
        for profile in grouped.values()
    ]


def linux_confinement_native_mapping_gap_verifier_contract_tree() -> dict:
    """Independently reconstruct the one exact unresolved V1 gap ledger."""

    occurrence_rows, predicate_rows, projection_leaf_count = (
        _independent_rows()
    )
    unique_field_profile_rows = _field_profiles(occurrence_rows)
    semantic = linux_confinement_semantic_verifier_contract_tree()
    semantic_counts = semantic["fixed_counts"]
    comparator_counts = {}
    codec_counts = {}
    for occurrence in occurrence_rows:
        comparator_id = occurrence["comparator_id"]
        codec_id = occurrence["value_codec_id"]
        comparator_counts[comparator_id] = (
            comparator_counts.get(comparator_id, 0) + 1
        )
        codec_counts[codec_id] = codec_counts.get(codec_id, 0) + 1
    return {
        "anchor_contracts": {
            "acceptance_contract_sha256": (
                linux_confinement_acceptance_contract_sha256()
            ),
            "evidence_plan_sha256": (
                linux_confinement_evidence_plan_sha256()
            ),
            "evidence_schema_contract_sha256": (
                linux_confinement_evidence_schema_contract_sha256()
            ),
            "policy_artifact_type": (
                LINUX_CONFINEMENT_POLICY_ARTIFACT_TYPE
            ),
            "semantic_payload_contract_sha256": (
                linux_confinement_semantic_verifier_contract_sha256()
            ),
            "staging_protocol_contract_sha256": (
                linux_confinement_staging_protocol_contract_sha256()
            ),
        },
        "artifact_type": _CONTRACT_ARTIFACT_TYPE,
        "digest_computation_id": _DIGEST_COMPUTATION_ID,
        "encoding_id": _ENCODING_ID,
        "contract_parser_error_ids": [
            "INPUT_TYPE",
            "INPUT_RESOURCE",
            "JSON_INVALID",
            "SCHEMA_INVALID",
            "CANONICAL_MISMATCH",
            "CONTRACT_DRIFT",
        ],
        "executed_layer_error_ids": list(_EXECUTED_ERROR_IDS),
        "expected_operand_authority_class_ids": list(
            _AUTHORITY_CLASS_IDS
        ),
        "fixed_counts": {
            "canonical_json_field_occurrence_count": 85,
            "canonical_json_unique_field_count": 84,
            "digest_comparator_occurrence_count": comparator_counts[
                "exact-digest-policy-or-cross-record-pin-equality-v1"
            ],
            "direct_field_occurrence_count": 27,
            "field_occurrence_count": semantic_counts[
                "raw_evidence_field_occurrence_count"
            ],
            "nul_frame_field_occurrence_count": codec_counts[
                "nul-terminated-ordered-octet-strings-v1"
            ],
            "opaque_octets_field_occurrence_count": codec_counts[
                "bounded-opaque-octets-v1"
            ],
            "predicate_count": semantic_counts["observation_count"],
            "profile_input_comparator_occurrence_count": (
                comparator_counts[
                    "profile-predicate-input-not-portably-evaluated-v1"
                ]
            ),
            "projection_leaf_occurrence_count": projection_leaf_count,
            "sha256_field_occurrence_count": codec_counts[
                "sha256-lowercase-hex-ascii-v1"
            ],
            "u64_comparator_occurrence_count": comparator_counts[
                "exact-u64-policy-or-cross-record-equality-v1"
            ],
            "u64_field_occurrence_count": codec_counts[
                "unsigned-u64be-v1"
            ],
            "unique_field_count": semantic_counts[
                "raw_evidence_unique_field_count"
            ],
        },
        "format_version": "1",
        "gap_ids": list(_GAP_IDS),
        "implementation_status_id": _CONTRACT_STATUS,
        "nonclaim_state": {
            claim_id: False for claim_id in _FALSE_CLAIM_IDS
        },
        "occurrence_identity_computation_id": (
            _OCCURRENCE_IDENTITY_COMPUTATION_ID
        ),
        "occurrence_recipe_rows": occurrence_rows,
        "operand_locator_kind_ids": list(_OPERAND_LOCATOR_KIND_IDS),
        "operand_path_segment_schemas": [
            {
                "exact_payload_field_ids": [
                    "key_field_id",
                    "key_token",
                ],
                "segment_kind_id": "declared-keyed-list-item",
            },
            {
                "exact_payload_field_ids": ["list_index"],
                "segment_kind_id": "list-index",
            },
            {
                "exact_payload_field_ids": ["object_key"],
                "segment_kind_id": "object-key",
            },
        ],
        "operand_path_segment_kind_ids": list(
            _OPERAND_PATH_SEGMENT_KIND_IDS
        ),
        "projection_schema_path_segment_kind_ids": list(
            _PROJECTION_SCHEMA_PATH_SEGMENT_KIND_IDS
        ),
        "predicate_operator_ids": list(_PREDICATE_OPERATOR_IDS),
        "predicate_result_ids": list(_PREDICATE_RESULT_IDS),
        "predicate_rows": predicate_rows,
        "unique_field_profile_rows": unique_field_profile_rows,
        "validation_scope_id": _VALIDATION_SCOPE,
    }


def linux_confinement_native_mapping_gap_verifier_contract_bytes() -> bytes:
    """Serialize the independently reconstructed V1 contract."""

    return _canonical_json(
        linux_confinement_native_mapping_gap_verifier_contract_tree(),
        maximum=_MAX_CONTRACT_BYTES,
    )


def linux_confinement_native_mapping_gap_verifier_contract_sha256() -> str:
    """Return the independently reconstructed domain-separated identity."""

    return _domain_sha256(
        _CONTRACT_DIGEST_DOMAIN,
        linux_confinement_native_mapping_gap_verifier_contract_bytes(),
    )


@dataclass(frozen=True)
class LinuxConfinementNativeMappingGapVerificationPinsV1:
    """Externally supplied identity expected for the static gap contract."""

    native_mapping_gap_contract_sha256: str


@dataclass(frozen=True)
class LinuxConfinementNativeMappingGapVerificationResultV1:
    """Immutable result for exact static gap-contract verification."""

    artifact_type: str
    format_version: str
    verifier_id: str
    implementation_status_id: str
    verification_status_id: str
    native_mapping_gap_contract_byte_count: int
    native_mapping_gap_contract_plain_sha256: str
    native_mapping_gap_contract_sha256: str
    acceptance_contract_sha256: str
    evidence_plan_sha256: str
    evidence_schema_contract_sha256: str
    semantic_payload_contract_sha256: str
    staging_protocol_contract_sha256: str
    field_occurrence_count: int
    unique_field_count: int
    canonical_json_field_occurrence_count: int
    canonical_json_unique_field_count: int
    projection_leaf_occurrence_count: int
    predicate_count: int
    canonical_bytes_validated: bool
    exact_anchor_pins_validated: bool
    exact_occurrence_order_and_coverage_validated: bool
    exact_unique_profile_coverage_validated: bool
    exact_projection_leaf_coverage_validated: bool
    exact_predicate_order_and_coverage_validated: bool
    blocking_gap_nonvacuity_validated: bool
    unresolved_positive_disablement_validated: bool
    authorizing_gate_implemented: bool
    custody_authenticated: bool
    empirical_result_established: bool
    hostile_controls_executed: bool
    linux_confinement_established: bool
    linux_execution_observed: bool
    native_acquisition_implemented: bool
    native_origin_authenticated: bool
    policy_predicate_evaluated: bool
    predicate_formula_implemented: bool
    predicate_preimage_constructed: bool
    raw_source_projection_relation_validated: bool
    release_authorized: bool
    teardown_executed: bool


def _validated_pins(
    value: LinuxConfinementNativeMappingGapVerificationPinsV1,
) -> LinuxConfinementNativeMappingGapVerificationPinsV1:
    if type(value) is not LinuxConfinementNativeMappingGapVerificationPinsV1:
        _fail(LinuxConfinementNativeMappingGapVerificationCode.INPUT_TYPE)
    digest = value.native_mapping_gap_contract_sha256
    if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
        _fail(
            LinuxConfinementNativeMappingGapVerificationCode
            .ARTIFACT_PIN_MISMATCH
        )
    return value


def _verification_result(
    contract_bytes: bytes,
    contract: dict,
) -> LinuxConfinementNativeMappingGapVerificationResultV1:
    counts = contract["fixed_counts"]
    anchors = contract["anchor_contracts"]
    return LinuxConfinementNativeMappingGapVerificationResultV1(
        artifact_type=_RESULT_ARTIFACT_TYPE,
        format_version="1",
        verifier_id=_IMPLEMENTATION_SEPARATED_VERIFIER_ID,
        implementation_status_id=(
            LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFIER_IMPLEMENTATION_STATUS
        ),
        verification_status_id=(
            LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_STATUS
        ),
        native_mapping_gap_contract_byte_count=len(contract_bytes),
        native_mapping_gap_contract_plain_sha256=hashlib.sha256(
            contract_bytes
        ).hexdigest(),
        native_mapping_gap_contract_sha256=_domain_sha256(
            _CONTRACT_DIGEST_DOMAIN,
            contract_bytes,
        ),
        acceptance_contract_sha256=anchors[
            "acceptance_contract_sha256"
        ],
        evidence_plan_sha256=anchors["evidence_plan_sha256"],
        evidence_schema_contract_sha256=anchors[
            "evidence_schema_contract_sha256"
        ],
        semantic_payload_contract_sha256=anchors[
            "semantic_payload_contract_sha256"
        ],
        staging_protocol_contract_sha256=anchors[
            "staging_protocol_contract_sha256"
        ],
        field_occurrence_count=counts["field_occurrence_count"],
        unique_field_count=counts["unique_field_count"],
        canonical_json_field_occurrence_count=counts[
            "canonical_json_field_occurrence_count"
        ],
        canonical_json_unique_field_count=counts[
            "canonical_json_unique_field_count"
        ],
        projection_leaf_occurrence_count=counts[
            "projection_leaf_occurrence_count"
        ],
        predicate_count=counts["predicate_count"],
        canonical_bytes_validated=True,
        exact_anchor_pins_validated=True,
        exact_occurrence_order_and_coverage_validated=True,
        exact_unique_profile_coverage_validated=True,
        exact_projection_leaf_coverage_validated=True,
        exact_predicate_order_and_coverage_validated=True,
        blocking_gap_nonvacuity_validated=True,
        unresolved_positive_disablement_validated=True,
        authorizing_gate_implemented=False,
        custody_authenticated=False,
        empirical_result_established=False,
        hostile_controls_executed=False,
        linux_confinement_established=False,
        linux_execution_observed=False,
        native_acquisition_implemented=False,
        native_origin_authenticated=False,
        policy_predicate_evaluated=False,
        predicate_formula_implemented=False,
        predicate_preimage_constructed=False,
        raw_source_projection_relation_validated=False,
        release_authorized=False,
        teardown_executed=False,
    )


def verify_linux_confinement_native_mapping_gap_contract(
    contract_bytes: bytes,
    pins: LinuxConfinementNativeMappingGapVerificationPinsV1,
) -> LinuxConfinementNativeMappingGapVerificationResultV1:
    """Verify exact V1 static coverage without making a positive claim."""

    validated_pins = _validated_pins(pins)
    if type(contract_bytes) is not bytes:
        _fail(LinuxConfinementNativeMappingGapVerificationCode.INPUT_TYPE)
    if not contract_bytes or len(contract_bytes) > _MAX_CONTRACT_BYTES:
        _fail(
            LinuxConfinementNativeMappingGapVerificationCode.INPUT_RESOURCE
        )
    contract_sha256 = _domain_sha256(
        _CONTRACT_DIGEST_DOMAIN,
        contract_bytes,
    )
    if (
        contract_sha256 != _V1_CONTRACT_SHA256
        or contract_sha256
        != validated_pins.native_mapping_gap_contract_sha256
    ):
        _fail(
            LinuxConfinementNativeMappingGapVerificationCode
            .ARTIFACT_PIN_MISMATCH
        )
    contract = _parse_contract(contract_bytes)
    expected = linux_confinement_native_mapping_gap_verifier_contract_tree()
    if not _typed_equal(contract, expected):
        _fail(
            LinuxConfinementNativeMappingGapVerificationCode.CONTRACT_MISMATCH
        )
    return _verification_result(contract_bytes, contract)


def _result_tree(
    value: LinuxConfinementNativeMappingGapVerificationResultV1,
) -> dict:
    if type(value) is not LinuxConfinementNativeMappingGapVerificationResultV1:
        _fail(LinuxConfinementNativeMappingGapVerificationCode.INPUT_TYPE)
    state = {field.name: getattr(value, field.name) for field in fields(value)}
    return {
        "anchor_contracts": {
            "acceptance_contract_sha256": state.pop(
                "acceptance_contract_sha256"
            ),
            "evidence_plan_sha256": state.pop(
                "evidence_plan_sha256"
            ),
            "evidence_schema_contract_sha256": state.pop(
                "evidence_schema_contract_sha256"
            ),
            "semantic_payload_contract_sha256": state.pop(
                "semantic_payload_contract_sha256"
            ),
            "staging_protocol_contract_sha256": state.pop(
                "staging_protocol_contract_sha256"
            ),
        },
        "artifact_type": state.pop("artifact_type"),
        "contract_identity": {
            "byte_count": state.pop(
                "native_mapping_gap_contract_byte_count"
            ),
            "plain_sha256": state.pop(
                "native_mapping_gap_contract_plain_sha256"
            ),
            "sha256": state.pop(
                "native_mapping_gap_contract_sha256"
            ),
        },
        "fixed_counts": {
            "canonical_json_field_occurrence_count": state.pop(
                "canonical_json_field_occurrence_count"
            ),
            "canonical_json_unique_field_count": state.pop(
                "canonical_json_unique_field_count"
            ),
            "field_occurrence_count": state.pop(
                "field_occurrence_count"
            ),
            "predicate_count": state.pop("predicate_count"),
            "projection_leaf_occurrence_count": state.pop(
                "projection_leaf_occurrence_count"
            ),
            "unique_field_count": state.pop("unique_field_count"),
        },
        "format_version": state.pop("format_version"),
        "implementation_status_id": state.pop(
            "implementation_status_id"
        ),
        "nonclaim_state": {
            claim_id: state.pop(claim_id)
            for claim_id in _FALSE_CLAIM_IDS
        },
        "validation_state": {
            validation_id: state.pop(validation_id)
            for validation_id in (
                "blocking_gap_nonvacuity_validated",
                "canonical_bytes_validated",
                "exact_anchor_pins_validated",
                "exact_occurrence_order_and_coverage_validated",
                "exact_predicate_order_and_coverage_validated",
                "exact_projection_leaf_coverage_validated",
                "exact_unique_profile_coverage_validated",
                "unresolved_positive_disablement_validated",
            )
        },
        "verification_status_id": state.pop("verification_status_id"),
        "verifier_id": state.pop("verifier_id"),
    }


def linux_confinement_native_mapping_gap_verification_result_bytes(
    value: LinuxConfinementNativeMappingGapVerificationResultV1,
) -> bytes:
    """Serialize one immutable verification result."""

    tree = _result_tree(value)
    if (
        tree["artifact_type"] != _RESULT_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or tree["verifier_id"] != _IMPLEMENTATION_SEPARATED_VERIFIER_ID
        or tree["implementation_status_id"]
        != (
            LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFIER_IMPLEMENTATION_STATUS
        )
        or tree["verification_status_id"]
        != LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_STATUS
        or tree["contract_identity"]
        != {
            "byte_count": _V1_CONTRACT_BYTE_COUNT,
            "plain_sha256": _V1_CONTRACT_PLAIN_SHA256,
            "sha256": _V1_CONTRACT_SHA256,
        }
        or tree["fixed_counts"]
        != {
            "canonical_json_field_occurrence_count": 85,
            "canonical_json_unique_field_count": 84,
            "field_occurrence_count": 112,
            "predicate_count": 24,
            "projection_leaf_occurrence_count": 502,
            "unique_field_count": 111,
        }
        or tree["anchor_contracts"]
        != {
            "acceptance_contract_sha256": (
                linux_confinement_acceptance_contract_sha256()
            ),
            "evidence_plan_sha256": (
                linux_confinement_evidence_plan_sha256()
            ),
            "evidence_schema_contract_sha256": (
                linux_confinement_evidence_schema_contract_sha256()
            ),
            "semantic_payload_contract_sha256": (
                linux_confinement_semantic_verifier_contract_sha256()
            ),
            "staging_protocol_contract_sha256": (
                linux_confinement_staging_protocol_contract_sha256()
            ),
        }
        or any(tree["nonclaim_state"].values())
        or not all(tree["validation_state"].values())
    ):
        _fail(LinuxConfinementNativeMappingGapVerificationCode.RESULT_INVALID)
    return _canonical_json(
        tree,
        maximum=_MAX_RESULT_BYTES,
    )


def linux_confinement_native_mapping_gap_verification_result_sha256(
    value: LinuxConfinementNativeMappingGapVerificationResultV1,
) -> str:
    """Return the length-bound domain-separated result identity."""

    return _domain_sha256(
        LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_RESULT_DIGEST_DOMAIN,
        linux_confinement_native_mapping_gap_verification_result_bytes(value),
    )


def validate_linux_confinement_native_mapping_gap_verification_result(
    value: LinuxConfinementNativeMappingGapVerificationResultV1,
    contract_bytes: bytes,
    pins: LinuxConfinementNativeMappingGapVerificationPinsV1,
) -> LinuxConfinementNativeMappingGapVerificationResultV1:
    """Recompute and validate an independently produced result."""

    if type(value) is not LinuxConfinementNativeMappingGapVerificationResultV1:
        _fail(LinuxConfinementNativeMappingGapVerificationCode.INPUT_TYPE)
    expected = verify_linux_confinement_native_mapping_gap_contract(
        contract_bytes,
        pins,
    )
    if value != expected:
        _fail(LinuxConfinementNativeMappingGapVerificationCode.RESULT_INVALID)
    linux_confinement_native_mapping_gap_verification_result_bytes(value)
    return value


def _validate_frozen_contract() -> None:
    tree = linux_confinement_native_mapping_gap_verifier_contract_tree()
    counts = tree["fixed_counts"]
    occurrences = tree["occurrence_recipe_rows"]
    profiles = tree["unique_field_profile_rows"]
    predicates = tree["predicate_rows"]
    if (
        linux_confinement_semantic_verifier_contract_sha256()
        != _V1_SEMANTIC_CONTRACT_SHA256
        or linux_confinement_native_mapping_gap_verifier_contract_sha256()
        != _V1_CONTRACT_SHA256
        or counts["field_occurrence_count"] != 112
        or counts["unique_field_count"] != 111
        or counts["canonical_json_field_occurrence_count"] != 85
        or counts["canonical_json_unique_field_count"] != 84
        or counts["direct_field_occurrence_count"] != 27
        or counts["projection_leaf_occurrence_count"] != 502
        or counts["predicate_count"] != 24
        or counts["digest_comparator_occurrence_count"] != 19
        or counts["u64_comparator_occurrence_count"] != 2
        or counts["profile_input_comparator_occurrence_count"] != 91
        or len(occurrences) != 112
        or len(profiles) != 111
        or len(predicates) != 24
        or len({row["mapping_id"] for row in occurrences}) != 112
        or len({row["field_id"] for row in occurrences}) != 111
        or any(
            row["mapping_resolution_id"] != "UNRESOLVED"
            or row["positive_mapping_enabled"] is not False
            or not row["blocking_gap_ids"]
            or row["source_operation_rows"]
            or row["source_operand_rows"]
            or row["target_operand_rows"]
            or row["normalization_rows"]
            or row["assertion_rows"]
            for row in occurrences
        )
        or any(
            row["unique_profile_resolution_id"] != "UNRESOLVED"
            or row["positive_mapping_enabled"] is not False
            or not row["blocking_gap_ids"]
            for row in profiles
        )
        or any(
            row["predicate_resolution_id"] != "UNRESOLVED"
            or row["positive_evaluation_enabled"] is not False
            or not row["blocking_gap_ids"]
            or row["root_assertion_id"]
            for row in predicates
        )
        or any(tree["nonclaim_state"].values())
    ):
        raise RuntimeError("Linux native mapping V1 contract drifted")


_validate_frozen_contract()


__all__ = [
    (
        "LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_IMPLEMENTATION_SEPARATED_"
        "VERIFIER_ID"
    ),
    (
        "LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_RESULT_"
        "ARTIFACT_TYPE"
    ),
    (
        "LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_RESULT_"
        "DIGEST_DOMAIN"
    ),
    "LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_STATUS",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFIER_IMPLEMENTATION_STATUS",
    (
        "MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VERIFICATION_"
        "RESULT_BYTES"
    ),
    "LinuxConfinementNativeMappingGapVerificationCode",
    "LinuxConfinementNativeMappingGapVerificationError",
    "LinuxConfinementNativeMappingGapVerificationPinsV1",
    "LinuxConfinementNativeMappingGapVerificationResultV1",
    "linux_confinement_native_mapping_gap_verification_result_bytes",
    "linux_confinement_native_mapping_gap_verification_result_sha256",
    "linux_confinement_native_mapping_gap_verifier_contract_bytes",
    "linux_confinement_native_mapping_gap_verifier_contract_sha256",
    "linux_confinement_native_mapping_gap_verifier_contract_tree",
    "validate_linux_confinement_native_mapping_gap_verification_result",
    "verify_linux_confinement_native_mapping_gap_contract",
]
