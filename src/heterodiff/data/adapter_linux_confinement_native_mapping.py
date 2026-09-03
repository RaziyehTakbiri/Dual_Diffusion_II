"""Portable Linux native-mapping inventory and explicit gap contract.

This module does not inspect Linux, parse native evidence, evaluate a policy
predicate, authorize release, or establish confinement.  It freezes the exact
112 field occurrences and 24 predicate identifiers inherited from the current
evidence and semantic contracts, inventories every typed projection leaf, and
marks all unresolved native-source, operand, formula, authority, provenance,
and authorization relations explicitly.

The purpose of this contract is nonvacuity: future mapping work cannot omit a
field, projection leaf, or predicate while claiming complete coverage.  A row
with a blocking gap is ineligible for positive derivation or evaluation.
"""

from __future__ import annotations

from enum import Enum
import hashlib
import json
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
from .adapter_linux_confinement_semantic_payload import (
    LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT,
    linux_confinement_evidence_field_parser_id,
    linux_confinement_semantic_payload_contract_sha256,
    linux_confinement_semantic_payload_contract_tree,
)
from .adapter_linux_confinement_staging_protocol import (
    linux_confinement_staging_protocol_contract_sha256,
)


LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_ARTIFACT_TYPE: Final = (
    "heterodiff.adapter.linux-confinement-native-mapping-gap-contract.v1"
)
LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_DIGEST_DOMAIN: Final = (
    LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_ARTIFACT_TYPE
)
LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_STATUS: Final = (
    "PORTABLE_PREDICATE_MAPPING_INVENTORY_AND_GAP_CONTRACT_IMPLEMENTED"
)
LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VALIDATION_SCOPE: Final = (
    "EXACT_UNRESOLVED_OCCURRENCE_PREDICATE_AND_PROJECTION_LEAF_COVERAGE_ONLY"
)
LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_ENCODING_ID: Final = (
    "canonical-ascii-json-sort-keys-no-whitespace-v1"
)
LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_DIGEST_COMPUTATION_ID: Final = (
    "sha256-domain-nul-u64be-length-canonical-bytes-v1"
)
LINUX_CONFINEMENT_NATIVE_MAPPING_OCCURRENCE_IDENTITY_COMPUTATION_ID: Final = (
    "utf8-observation-id-nul-ascii-decimal-index-nul-field-id-v1"
)
MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_BYTES: Final = (
    4 * 1024 * 1024
)
MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_JSON_DEPTH: Final = 32
MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_JSON_ITEMS: Final = 65536


LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_IDS: Final = (
    "NATIVE_SOURCE_TO_EVIDENCE_VALUE_DERIVATION_UNDEFINED",
    "EVIDENCE_OR_PROJECTION_TO_OPERAND_MAPPING_UNDEFINED",
    "PREDICATE_FORMULA_UNDEFINED",
    "SOURCE_AVAILABILITY_SEMANTICS_UNDEFINED",
    "EXTERNAL_AUTHORITY_PREIMAGE_UNAVAILABLE",
    "AUTHORIZING_GATE_BINDING_UNDEFINED",
    "CUSTODY_OR_PROVENANCE_UNANCHORED",
    "OPERAND_COVERAGE_NONVACUITY_UNPROVED",
)

LINUX_CONFINEMENT_NATIVE_MAPPING_OPERAND_LOCATOR_KIND_IDS: Final = (
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

LINUX_CONFINEMENT_NATIVE_MAPPING_AUTHORITY_CLASS_IDS: Final = (
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

LINUX_CONFINEMENT_NATIVE_MAPPING_OPERAND_PATH_SEGMENT_KIND_IDS: Final = (
    "declared-keyed-list-item",
    "list-index",
    "object-key",
)

_PROJECTION_SCHEMA_PATH_KIND_IDS: Final = (
    "object-key",
    "schema-list-item",
)
LINUX_CONFINEMENT_NATIVE_MAPPING_PROJECTION_SCHEMA_PATH_SEGMENT_KIND_IDS: (
    Final
) = _PROJECTION_SCHEMA_PATH_KIND_IDS

LINUX_CONFINEMENT_NATIVE_MAPPING_PREDICATE_OPERATOR_IDS: Final = (
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

LINUX_CONFINEMENT_NATIVE_MAPPING_PREDICATE_RESULT_IDS: Final = (
    "PASS",
    "FAIL",
    "NOT_EVALUATED",
)

LINUX_CONFINEMENT_NATIVE_MAPPING_ERROR_IDS: Final = (
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

LINUX_CONFINEMENT_NATIVE_MAPPING_FALSE_CLAIM_IDS: Final = (
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

class LinuxConfinementNativeMappingGapCode(str, Enum):
    """Closed failures for the static portable gap contract."""

    INPUT_TYPE = "INPUT_TYPE"
    INPUT_RESOURCE = "INPUT_RESOURCE"
    JSON_INVALID = "JSON_INVALID"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    CANONICAL_MISMATCH = "CANONICAL_MISMATCH"
    CONTRACT_DRIFT = "CONTRACT_DRIFT"


_ERROR_MESSAGES: Final = {
    LinuxConfinementNativeMappingGapCode.INPUT_TYPE: (
        "Linux native mapping gap contract input has an invalid exact type"
    ),
    LinuxConfinementNativeMappingGapCode.INPUT_RESOURCE: (
        "Linux native mapping gap contract input exceeds its resource ceiling"
    ),
    LinuxConfinementNativeMappingGapCode.JSON_INVALID: (
        "Linux native mapping gap contract JSON is invalid"
    ),
    LinuxConfinementNativeMappingGapCode.SCHEMA_INVALID: (
        "Linux native mapping gap contract schema is invalid"
    ),
    LinuxConfinementNativeMappingGapCode.CANONICAL_MISMATCH: (
        "Linux native mapping gap contract bytes are not canonical"
    ),
    LinuxConfinementNativeMappingGapCode.CONTRACT_DRIFT: (
        "Linux native mapping gap contract anchors drifted"
    ),
}


class LinuxConfinementNativeMappingGapError(ValueError):
    """One fixed-message contract failure."""

    def __init__(self, code: LinuxConfinementNativeMappingGapCode) -> None:
        if type(code) is not LinuxConfinementNativeMappingGapCode:
            raise TypeError("native mapping gap code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class _DuplicateKeyError(ValueError):
    pass


def _fail(code: LinuxConfinementNativeMappingGapCode) -> None:
    raise LinuxConfinementNativeMappingGapError(code) from None


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
        _fail(LinuxConfinementNativeMappingGapCode.SCHEMA_INVALID)
    if (
        not result
        or len(result)
        > MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_BYTES
    ):
        _fail(LinuxConfinementNativeMappingGapCode.INPUT_RESOURCE)
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


def _reject_json_constant(value: str) -> None:
    raise ValueError("non-finite JSON constant")


def _reject_json_float(value: str) -> None:
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
        if count > MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_JSON_ITEMS:
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
        if maximum > MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_JSON_DEPTH:
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


def _path_id(segments: tuple) -> str:
    tokens = ["values"]
    for kind_id, value in segments:
        if kind_id == "object-key":
            tokens.append(value)
        elif kind_id == "schema-list-item":
            tokens.append("[]")
        else:
            raise RuntimeError("unsupported static path segment")
    return "/" + "/".join(tokens)


def _path_segment_tree(kind_id: str, value: str) -> dict:
    return {
        "path_token": value,
        "segment_kind_id": kind_id,
    }


def _projection_leaf_rows(node: dict, segments: tuple = ()) -> list:
    kind_id = node["node_kind_id"]
    if kind_id == "object":
        result = []
        for field in node["field_rows"]:
            result.extend(
                _projection_leaf_rows(
                    field["schema"],
                    segments
                    + (("object-key", field["field_id"]),),
                )
            )
        return result
    if kind_id == "list":
        return _projection_leaf_rows(
            node["item_schema"],
            segments + (("schema-list-item", ""),),
        )
    return [
        {
            "coverage_status_id": "UNRESOLVED",
            "node_kind_id": kind_id,
            "schema_path_id": _path_id(segments),
            "path_segments": [
                _path_segment_tree(segment_kind_id, value)
                for segment_kind_id, value in segments
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
    result = [
        gap_id
        for gap_id in LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_IDS
        if gap_id != "EXTERNAL_AUTHORITY_PREIMAGE_UNAVAILABLE"
    ]
    if observation_id in _EXTERNAL_AUTHORITY_OBSERVATION_IDS:
        result.append("EXTERNAL_AUTHORITY_PREIMAGE_UNAVAILABLE")
    return [
        gap_id
        for gap_id in LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_IDS
        if gap_id in result
    ]


def _contract_rows_unchecked() -> tuple:
    plan = linux_confinement_evidence_plan_tree()
    semantic = linux_confinement_semantic_payload_contract_tree()
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
        _fail(LinuxConfinementNativeMappingGapCode.CONTRACT_DRIFT)
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
        _fail(LinuxConfinementNativeMappingGapCode.CONTRACT_DRIFT)
    projection_by_field = {
        row["field_id"]: row
        for row in projection_registry
    }
    occurrence_rows = []
    predicate_rows = []
    projection_leaf_occurrence_count = 0
    record_field_ids = []
    for observation in plan_observations:
        observation_id = observation["item_id"]
        try:
            semantic_observation = semantic_by_observation[observation_id]
        except KeyError:
            _fail(LinuxConfinementNativeMappingGapCode.CONTRACT_DRIFT)
        mappings = []
        semantic_fields = semantic_observation["raw_evidence_fields"]
        if (
            [row["field_id"] for row in semantic_fields]
            != observation["raw_evidence_field_ids"]
        ):
            _fail(LinuxConfinementNativeMappingGapCode.CONTRACT_DRIFT)
        for index, field in enumerate(semantic_fields):
            field_id = field["field_id"]
            codec_id = field["value_codec_id"]
            is_record = (
                codec_id
                == LINUX_CONFINEMENT_CODEC_CANONICAL_JSON_OBJECT
            )
            projection_schema_id = ""
            projection_leaf_rows = []
            if is_record:
                record_field_ids.append(field_id)
                try:
                    projection = projection_by_field[field_id]
                except KeyError:
                    _fail(
                        LinuxConfinementNativeMappingGapCode.CONTRACT_DRIFT
                    )
                projection_schema_id = projection[
                    "projection_schema_id"
                ]
                projection_leaf_rows = _projection_leaf_rows(
                    projection["values_schema"]
                )
                projection_leaf_occurrence_count += len(
                    projection_leaf_rows
                )
                semantic_projection_parser_id = (
                    linux_confinement_evidence_field_parser_id(field_id)
                )
            else:
                semantic_projection_parser_id = ""
            mapping_id = _mapping_id(
                observation_id,
                index,
                field_id,
            )
            mappings.append(mapping_id)
            occurrence_rows.append(
                {
                    "assertion_rows": [],
                    "blocking_gap_ids": _blocking_gap_ids(
                        observation_id
                    ),
                    "comparator_id": field["comparator_id"],
                    "field_profile_id": _field_profile_id(field_id),
                    "projection_leaf_inventory_rows": (
                        projection_leaf_rows
                    ),
                    "direct_value_coverage_status_id": (
                        "NOT_APPLICABLE"
                        if is_record
                        else "UNRESOLVED"
                    ),
                    "field_id": field_id,
                    "field_occurrence_index": index,
                    "lifecycle_stage_id": observation[
                        "lifecycle_stage_id"
                    ],
                    "mapping_id": mapping_id,
                    "mapping_resolution_id": "UNRESOLVED",
                    "native_derivation_contract_id": "",
                    "native_derivation_contract_sha256": "",
                    "semantic_projection_parser_id": (
                        semantic_projection_parser_id
                    ),
                    "semantic_projection_parser_sha256": "",
                    "normalization_rows": [],
                    "observation_id": observation_id,
                    "positive_mapping_enabled": False,
                    "predicate_id": observation["predicate_id"],
                    "primitive_transform_contract_id": "",
                    "primitive_transform_contract_sha256": "",
                    "procedure_id": observation["procedure_id"],
                    "produced_predicate_operand_ids": [],
                    "projection_schema_id": projection_schema_id,
                    "raw_to_projection_parser_required": is_record,
                    "semantic_type_id": field["semantic_type_id"],
                    "snapshot_stage_id": semantic_observation[
                        "snapshot_stage_id"
                    ],
                    "source_availability_rule_id": "UNRESOLVED",
                    "source_operand_rows": [],
                    "source_operation_rows": [],
                    "subject_role_ids": observation[
                        "subject_role_ids"
                    ],
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
                "ordered_mapping_ids": mappings,
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
                "observation_id": observation_id,
            }
        )
    if (
        len(occurrence_rows) != 112
        or len({row["field_id"] for row in occurrence_rows}) != 111
        or len(record_field_ids) != 85
        or sorted(set(record_field_ids)) != projection_field_ids
        or len(projection_field_ids) != 84
    ):
        _fail(LinuxConfinementNativeMappingGapCode.CONTRACT_DRIFT)
    return (
        occurrence_rows,
        predicate_rows,
        projection_leaf_occurrence_count,
    )


def _contract_rows() -> tuple:
    try:
        return _contract_rows_unchecked()
    except LinuxConfinementNativeMappingGapError:
        raise
    except (KeyError, TypeError, IndexError, AttributeError):
        _fail(LinuxConfinementNativeMappingGapCode.CONTRACT_DRIFT)


def _unique_field_profile_rows(occurrence_rows: list) -> list:
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
        comparable_fields = (
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
            for key in comparable_fields
        ):
            _fail(LinuxConfinementNativeMappingGapCode.CONTRACT_DRIFT)
        if profile["projection_leaf_schema_count"] != len(
            occurrence["projection_leaf_inventory_rows"]
        ):
            _fail(LinuxConfinementNativeMappingGapCode.CONTRACT_DRIFT)
        profile["ordered_mapping_ids"].append(occurrence["mapping_id"])
        profile["ordered_observation_ids"].append(
            occurrence["observation_id"]
        )
        for gap_id in occurrence["blocking_gap_ids"]:
            if gap_id not in profile["blocking_gap_ids"]:
                profile["blocking_gap_ids"].append(gap_id)
        profile["blocking_gap_ids"] = [
            gap_id
            for gap_id in LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_IDS
            if gap_id in profile["blocking_gap_ids"]
        ]
    return [
        dict(profile, occurrence_count=len(profile["ordered_mapping_ids"]))
        for profile in grouped.values()
    ]


def linux_confinement_native_mapping_gap_contract_tree() -> dict:
    """Return the exact unresolved mapping and predicate coverage ledger."""

    (
        occurrence_rows,
        predicate_rows,
        projection_leaf_occurrence_count,
    ) = _contract_rows()
    unique_field_profile_rows = _unique_field_profile_rows(
        occurrence_rows
    )
    semantic = linux_confinement_semantic_payload_contract_tree()
    fixed_counts = semantic["fixed_counts"]
    comparator_counts = {}
    codec_counts = {}
    for occurrence in occurrence_rows:
        comparator_id = occurrence["comparator_id"]
        codec_id = occurrence["value_codec_id"]
        comparator_counts[comparator_id] = (
            comparator_counts.get(comparator_id, 0) + 1
        )
        codec_counts[codec_id] = codec_counts.get(codec_id, 0) + 1
    if (
        set(comparator_counts)
        != {
            "exact-digest-policy-or-cross-record-pin-equality-v1",
            "exact-u64-policy-or-cross-record-equality-v1",
            "profile-predicate-input-not-portably-evaluated-v1",
        }
        or set(codec_counts) != set(_TRANSPORT_DECODER_ID_BY_CODEC)
    ):
        _fail(LinuxConfinementNativeMappingGapCode.CONTRACT_DRIFT)
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
                linux_confinement_semantic_payload_contract_sha256()
            ),
            "staging_protocol_contract_sha256": (
                linux_confinement_staging_protocol_contract_sha256()
            ),
        },
        "artifact_type": (
            LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_ARTIFACT_TYPE
        ),
        "digest_computation_id": (
            LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_DIGEST_COMPUTATION_ID
        ),
        "encoding_id": (
            LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_ENCODING_ID
        ),
        "contract_parser_error_ids": [
            code.value for code in LinuxConfinementNativeMappingGapCode
        ],
        "executed_layer_error_ids": list(
            LINUX_CONFINEMENT_NATIVE_MAPPING_ERROR_IDS
        ),
        "expected_operand_authority_class_ids": list(
            LINUX_CONFINEMENT_NATIVE_MAPPING_AUTHORITY_CLASS_IDS
        ),
        "fixed_counts": {
            "canonical_json_field_occurrence_count": 85,
            "canonical_json_unique_field_count": 84,
            "digest_comparator_occurrence_count": comparator_counts[
                "exact-digest-policy-or-cross-record-pin-equality-v1"
            ],
            "direct_field_occurrence_count": 27,
            "field_occurrence_count": fixed_counts[
                "raw_evidence_field_occurrence_count"
            ],
            "nul_frame_field_occurrence_count": codec_counts[
                "nul-terminated-ordered-octet-strings-v1"
            ],
            "opaque_octets_field_occurrence_count": codec_counts[
                "bounded-opaque-octets-v1"
            ],
            "predicate_count": fixed_counts["observation_count"],
            "profile_input_comparator_occurrence_count": (
                comparator_counts[
                    "profile-predicate-input-not-portably-evaluated-v1"
                ]
            ),
            "projection_leaf_occurrence_count": (
                projection_leaf_occurrence_count
            ),
            "sha256_field_occurrence_count": codec_counts[
                "sha256-lowercase-hex-ascii-v1"
            ],
            "u64_comparator_occurrence_count": comparator_counts[
                "exact-u64-policy-or-cross-record-equality-v1"
            ],
            "u64_field_occurrence_count": codec_counts[
                "unsigned-u64be-v1"
            ],
            "unique_field_count": fixed_counts[
                "raw_evidence_unique_field_count"
            ],
        },
        "format_version": "1",
        "gap_ids": list(LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_IDS),
        "implementation_status_id": (
            LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_STATUS
        ),
        "nonclaim_state": {
            claim_id: False
            for claim_id in (
                LINUX_CONFINEMENT_NATIVE_MAPPING_FALSE_CLAIM_IDS
            )
        },
        "occurrence_identity_computation_id": (
            LINUX_CONFINEMENT_NATIVE_MAPPING_OCCURRENCE_IDENTITY_COMPUTATION_ID
        ),
        "occurrence_recipe_rows": occurrence_rows,
        "operand_locator_kind_ids": list(
            LINUX_CONFINEMENT_NATIVE_MAPPING_OPERAND_LOCATOR_KIND_IDS
        ),
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
            LINUX_CONFINEMENT_NATIVE_MAPPING_OPERAND_PATH_SEGMENT_KIND_IDS
        ),
        "projection_schema_path_segment_kind_ids": list(
            _PROJECTION_SCHEMA_PATH_KIND_IDS
        ),
        "predicate_operator_ids": list(
            LINUX_CONFINEMENT_NATIVE_MAPPING_PREDICATE_OPERATOR_IDS
        ),
        "predicate_result_ids": list(
            LINUX_CONFINEMENT_NATIVE_MAPPING_PREDICATE_RESULT_IDS
        ),
        "predicate_rows": predicate_rows,
        "unique_field_profile_rows": unique_field_profile_rows,
        "validation_scope_id": (
            LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VALIDATION_SCOPE
        ),
    }


def linux_confinement_native_mapping_gap_contract_bytes() -> bytes:
    """Serialize the fixed gap contract as bounded canonical ASCII JSON."""

    return _canonical_json(
        linux_confinement_native_mapping_gap_contract_tree()
    )


def linux_confinement_native_mapping_gap_contract_plain_sha256() -> str:
    """Return ordinary SHA-256 for the exact canonical contract bytes."""

    return hashlib.sha256(
        linux_confinement_native_mapping_gap_contract_bytes()
    ).hexdigest()


def linux_confinement_native_mapping_gap_contract_sha256() -> str:
    """Return the length-bound domain-separated contract digest."""

    return _domain_sha256(
        LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_DIGEST_DOMAIN,
        linux_confinement_native_mapping_gap_contract_bytes(),
    )


def parse_linux_confinement_native_mapping_gap_contract(
    value: bytes,
) -> dict:
    """Strictly parse the one exact static mapping-gap contract."""

    if type(value) is not bytes:
        _fail(LinuxConfinementNativeMappingGapCode.INPUT_TYPE)
    if (
        not value
        or len(value)
        > MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_BYTES
    ):
        _fail(LinuxConfinementNativeMappingGapCode.INPUT_RESOURCE)
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
        _fail(LinuxConfinementNativeMappingGapCode.JSON_INVALID)
    if (
        _json_depth(decoded)
        > MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_JSON_DEPTH
        or _node_count(decoded)
        > MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_JSON_ITEMS
    ):
        _fail(LinuxConfinementNativeMappingGapCode.INPUT_RESOURCE)
    expected = linux_confinement_native_mapping_gap_contract_tree()
    if not _same_exact(decoded, expected):
        _fail(LinuxConfinementNativeMappingGapCode.SCHEMA_INVALID)
    if value != linux_confinement_native_mapping_gap_contract_bytes():
        _fail(
            LinuxConfinementNativeMappingGapCode.CANONICAL_MISMATCH
        )
    return expected


def _validate_contract_coherence() -> None:
    tree = linux_confinement_native_mapping_gap_contract_tree()
    counts = tree["fixed_counts"]
    occurrence_rows = tree["occurrence_recipe_rows"]
    predicate_rows = tree["predicate_rows"]
    unique_field_profile_rows = tree["unique_field_profile_rows"]
    mapping_ids = [
        row["mapping_id"] for row in occurrence_rows
    ]
    field_ids = [row["field_id"] for row in occurrence_rows]
    if (
        counts["field_occurrence_count"] != 112
        or counts["unique_field_count"] != 111
        or counts["canonical_json_field_occurrence_count"] != 85
        or counts["canonical_json_unique_field_count"] != 84
        or counts["direct_field_occurrence_count"] != 27
        or counts["digest_comparator_occurrence_count"] != 19
        or counts["u64_comparator_occurrence_count"] != 2
        or counts["profile_input_comparator_occurrence_count"] != 91
        or counts["sha256_field_occurrence_count"] != 19
        or counts["u64_field_occurrence_count"] != 2
        or counts["nul_frame_field_occurrence_count"] != 2
        or counts["opaque_octets_field_occurrence_count"] != 4
        or counts["predicate_count"] != 24
        or len(occurrence_rows) != 112
        or len(predicate_rows) != 24
        or len(unique_field_profile_rows) != 111
        or len(set(mapping_ids)) != 112
        or len(set(field_ids)) != 111
        or any(
            row["mapping_resolution_id"] != "UNRESOLVED"
            or not row["blocking_gap_ids"]
            or row["source_operation_rows"]
            or row["source_operand_rows"]
            or row["target_operand_rows"]
            or row["normalization_rows"]
            or row["assertion_rows"]
            or row["native_derivation_contract_id"]
            or row["native_derivation_contract_sha256"]
            or row["semantic_projection_parser_sha256"]
            or row["primitive_transform_contract_id"]
            or row["primitive_transform_contract_sha256"]
            or row["positive_mapping_enabled"] is not False
            for row in occurrence_rows
        )
        or any(
            row["unique_profile_resolution_id"] != "UNRESOLVED"
            or row["positive_mapping_enabled"] is not False
            or not row["blocking_gap_ids"]
            or row["semantic_projection_parser_sha256"]
            or row["primitive_transform_contract_id"]
            or row["primitive_transform_contract_sha256"]
            for row in unique_field_profile_rows
        )
        or any(
            row["predicate_resolution_id"] != "UNRESOLVED"
            or row["positive_evaluation_enabled"] is not False
            or row["root_assertion_id"]
            or not row["blocking_gap_ids"]
            for row in predicate_rows
        )
        or any(tree["nonclaim_state"].values())
    ):
        raise RuntimeError(
            _ERROR_MESSAGES[
                LinuxConfinementNativeMappingGapCode.CONTRACT_DRIFT
            ]
        )


_validate_contract_coherence()


__all__ = [
    "LINUX_CONFINEMENT_NATIVE_MAPPING_AUTHORITY_CLASS_IDS",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_ERROR_IDS",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_FALSE_CLAIM_IDS",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_ARTIFACT_TYPE",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_DIGEST_DOMAIN",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_STATUS",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_ENCODING_ID",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_IDS",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_VALIDATION_SCOPE",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_OPERAND_LOCATOR_KIND_IDS",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_OCCURRENCE_IDENTITY_COMPUTATION_ID",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_OPERAND_PATH_SEGMENT_KIND_IDS",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_PREDICATE_OPERATOR_IDS",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_PREDICATE_RESULT_IDS",
    "LINUX_CONFINEMENT_NATIVE_MAPPING_PROJECTION_SCHEMA_PATH_SEGMENT_KIND_IDS",
    "MAXIMUM_LINUX_CONFINEMENT_NATIVE_MAPPING_GAP_CONTRACT_BYTES",
    "LinuxConfinementNativeMappingGapCode",
    "LinuxConfinementNativeMappingGapError",
    "linux_confinement_native_mapping_gap_contract_bytes",
    "linux_confinement_native_mapping_gap_contract_plain_sha256",
    "linux_confinement_native_mapping_gap_contract_sha256",
    "linux_confinement_native_mapping_gap_contract_tree",
    "parse_linux_confinement_native_mapping_gap_contract",
]
