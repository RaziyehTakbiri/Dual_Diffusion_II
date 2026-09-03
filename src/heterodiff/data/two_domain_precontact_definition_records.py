"""Pure offline records for three locally decidable B02/B03 definitions."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Tuple

HELD_OUT_MATERIAL_DEFINITION_ID = (
    "PHYSIONET_AND_RETAIL_TEST_PARTITIONS_AND_ALL_OUTCOME_BEARING_DERIVATIVES_V1"
)
FINAL_OPENING_RULE_ID = (
    "SEPARATE_FRESH_EXACT_AUTHORITY_AFTER_CONTENT_ADDRESSED_EXECUTABLE_FREEZE_V1"
)
APPEND_ONLY_LOG_SCHEMA_ID = (
    "HASH_LINKED_CONTACT_ACCESS_LOG_O_EXCL_INTENT_BEFORE_OPERATION_V1"
)
DURABLE_INTENT_RULE_ID = (
    "O_EXCL_0600_FILE_FSYNC_PARENT_FSYNC_BEFORE_EACH_CONTACT_OR_ACCESS_V1"
)
PHYSIONET_SPLIT_CONTRACT_ID = (
    "PHYSIONET_PATIENT_HASH_EXPLICIT_F061_HAMILTON_V1"
)
PHYSIONET_SPLIT_CONTRACT_SHA256 = (
    "32651b654a1b11ceb256f4f6cc6df1ff567d34538c3c2c6033d9acf1fc020b2d"
)
RETAIL_SPLIT_CONTRACT_ID = (
    "RETAIL_F060_SOURCE_CIVIL_SHARED_F061_INTEGRATED_REPLAY_V3"
)
RETAIL_SPLIT_CONTRACT_SHA256 = (
    "b1a4fef836a50987b5d723e2bd133605bd907b4d7904f7cd6e87ca1d83077659"
)

_DOMAINS = {
    "held_out_material_definition": (
        b"heterodiff/b02-b03/held-out-material-definition/v1\0"
    ),
    "final_opening_rule": b"heterodiff/b02-b03/final-opening-rule/v1\0",
    "append_only_log_schema": b"heterodiff/b02-b03/contact-access-log-schema/v1\0",
}


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def record_sha256(name: str, record: object) -> str:
    if type(name) is not str or name not in _DOMAINS or type(record) is not dict:
        raise TypeError("exact known record name and built-in dict required")
    return hashlib.sha256(_DOMAINS[name] + _canonical(record)).hexdigest()


def held_out_material_definition() -> Dict[str, Any]:
    return {
        "schema_version": "heterodiff-two-domain-held-out-material-definition-v1",
        "definition_id": HELD_OUT_MATERIAL_DEFINITION_ID,
        "domain_split_lineage": [
            {
                "domain_id": "physionet-challenge-2012",
                "split_contract_id": PHYSIONET_SPLIT_CONTRACT_ID,
                "split_contract_sha256": PHYSIONET_SPLIT_CONTRACT_SHA256,
            },
            {
                "domain_id": "online-retail-ii",
                "split_contract_id": RETAIL_SPLIT_CONTRACT_ID,
                "split_contract_sha256": RETAIL_SPLIT_CONTRACT_SHA256,
            },
        ],
        "held_out_root": "COMPLETE_TEST_ASSIGNMENT_IN_CONTENT_ADDRESSED_SPLIT_MANIFEST",
        "covered_material": [
            "RAW_AND_NORMALIZED_TEST_RECORDS_AND_LABELS_OR_OUTCOMES",
            (
                "TEST_DERIVED_FEATURES_CACHES_PREDICTIONS_"
                "AND_PER_EXAMPLE_OUTPUTS"
            ),
            "AGGREGATE_METRICS_BOOTSTRAPS_DIAGNOSTICS_PLOTS_TABLES_AND_DISPLAYS",
            "ANY_DESCENDANT_OR_MIXED_ARTIFACT_INCORPORATING_TEST_INFORMATION",
        ],
        "inheritance_rule": "ANY_TEST_INFORMATION_MAKES_THE_ARTIFACT_HELD_OUT",
        "membership_authority": "REPLAY_VERIFIED_CONTENT_ADDRESSED_SPLIT_MANIFEST",
        "unknown_lineage_disposition": "TREAT_AS_HELD_OUT_AND_FAIL_CLOSED",
        "post_split_exclusion_reassignment_or_preview_permitted": False,
        "material_or_manifest_claimed_present": False,
    }


def final_opening_rule() -> Dict[str, Any]:
    return {
        "schema_version": "heterodiff-two-domain-final-opening-rule-v1",
        "rule_id": FINAL_OPENING_RULE_ID,
        "held_out_material_definition_sha256": record_sha256(
            "held_out_material_definition", held_out_material_definition()
        ),
        "prerequisites": [
            "CONTENT_ADDRESSED_EXECUTABLE_AND_MANUSCRIPT_FREEZE",
            "TRAINING_AND_VALIDATION_ANALYSES_CLOSED",
            "DISTINCT_ACCEPTED_INDEPENDENT_FINAL_OPENING_APPROVER",
            "FRESH_EXACT_AUTHORITY_BOUND_TO_PACKAGE_MATERIAL_SPLITS_AND_OPERATION",
            "DURABLE_O_EXCL_INTENT_FILE_AND_PARENT_FSYNC_BEFORE_OPENING",
            "PRIOR_APPEND_ONLY_LOG_HEAD_BOUND",
        ],
        "maximum_attempts": 1,
        "retry_redirect_fallback_preview_query_or_repair_permitted": False,
        "missing_ambiguous_or_rejected_authority_disposition": "TERMINAL_NO_GO",
        "durable_intent_without_outcome_disposition": (
            "TERMINAL_SPENT_INCOMPLETE_NO_RETRY"
        ),
        "opening_authorizes_publication": False,
        "approver_authority_or_opening_claimed_present": False,
    }


def append_only_log_schema() -> Dict[str, Any]:
    entry_fields = [
        ("ordinal", "INTEGER", False),
        ("event_kind", "ENUM_INTENT_OUTCOME", False),
        ("intent_entry_sha256", "LOWERCASE_SHA256", True),
        ("operation_ordinal", "EXACT_NONNEGATIVE_INTEGER", False),
        ("domain_id", "ENUM_PHYSIONET_CHALLENGE_2012_ONLINE_RETAIL_II", False),
        ("phase", "ENUM_ADMIN_DATA_FINAL_OPENING", False),
        ("exact_target_sha256", "LOWERCASE_SHA256", False),
        ("request_kind_sha256", "LOWERCASE_SHA256", False),
        ("package_identity_sha256", "LOWERCASE_SHA256", False),
        ("population_identity_sha256", "LOWERCASE_SHA256", False),
        ("authority_receipt_sha256", "LOWERCASE_SHA256", False),
        ("dependency_receipts", "ORDERED_ROLE_SHA256_OBJECT_ARRAY", False),
        ("durable_intent_receipt_sha256", "LOWERCASE_SHA256", False),
        ("operation_started_time", "RFC3339_UTC_NANOSECONDS", False),
        ("operation_finished_time", "RFC3339_UTC_NANOSECONDS", True),
        ("outcome", "CLOSED_ENUM", True),
        ("observation_or_response_sha256", "LOWERCASE_SHA256", True),
        ("previous_entry_sha256", "LOWERCASE_SHA256", False),
        ("entry_sha256", "LOWERCASE_SHA256", False),
    ]
    return {
        "schema_version": "heterodiff-two-domain-contact-access-log-v1",
        "log_schema_id": APPEND_ONLY_LOG_SCHEMA_ID,
        "durable_intent_rule_id": DURABLE_INTENT_RULE_ID,
        "genesis_previous_entry_sha256": "0" * 64,
        "entry_schema": [
            {"name": name, "exact_type": exact_type, "nullable": nullable}
            for name, exact_type, nullable in entry_fields
        ],
        "ordinal_rule": "CONTIGUOUS_ZERO_BASED_EXACT_NONNEGATIVE_INTEGERS",
        "previous_link_rule": (
            "ORDINAL_ZERO_EQUALS_GENESIS_OTHERWISE_EQUALS_EXACT_PRIOR_ENTRY_SHA256"
        ),
        "dependency_digest_order": (
            "ASCENDING_ASCII_DEPENDENCY_ROLE_THEN_ASCENDING_LOWERCASE_SHA256"
        ),
        "dependency_receipt_item_schema": {
            "role": "NONEMPTY_ASCII_STRING",
            "sha256": "LOWERCASE_SHA256",
        },
        "event_pairing_and_state_rule": (
            "EACH_OPERATION_HAS_EXACTLY_ONE_INTENT_THEN_ZERO_OR_ONE_OUTCOME_"
            "OUTCOME_BINDS_INTENT_ENTRY_SHA256_NO_OTHER_EVENT_KIND_"
            "OUTCOME_OPERATION_STARTED_TIME_EXACTLY_EQUALS_BOUND_INTENT_"
            "OPERATION_STARTED_TIME_"
            "INTENT_HAS_NULL_INTENT_LINK_FINISH_OUTCOME_RESPONSE_"
            "OUTCOME_HAS_NON_NULL_FINISH_OUTCOME_AND_"
            "OBSERVATION_ERROR_OR_RESPONSE_RECEIPT_SHA256"
        ),
        "outcome_start_time_binding_rule": (
            "OUTCOME_OPERATION_STARTED_TIME_EXACTLY_EQUALS_BOUND_INTENT_"
            "OPERATION_STARTED_TIME"
        ),
        "allowed_outcomes": [
            "SUCCESS", "TERMINAL_NO_GO", "TERMINAL_SPENT_INCOMPLETE_NO_RETRY",
            "PROTOCOL_VIOLATION", "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO",
            "APPROVAL_OR_AUTHORITY_TERMINAL_NO_GO",
        ],
        "entry_digest_rule": "DOMAIN_SEPARATED_CANONICAL_JSON_EXCLUDING_ENTRY_SHA256",
        "entry_digest_domain_display_label": (
            "heterodiff/b02-b03/contact-access-log-entry/v1"
        ),
        "entry_digest_domain_display_escape_rule": (
            "UTF8_ASCII_DISPLAY_LABEL_FOLLOWED_BY_ONE_NUL_OCTET"
        ),
        "entry_digest_domain_is_nul_terminated": True,
        "entry_digest_domain_hex": (
            b"heterodiff/b02-b03/contact-access-log-entry/v1\0".hex()
        ),
        "entry_storage_layout": "entries/{ordinal:020d}-{entry_sha256}.json",
        "entry_write_rule": (
            "ONE_IMMUTABLE_FILE_PER_ENTRY_O_CREAT_O_EXCL_MODE_0600_"
            "WRITE_ALL_FSYNC_FILE_FSYNC_ENTRIES_DIRECTORY"
        ),
        "head_storage_layout": "heads/{ordinal:020d}.json",
        "head_record_schema": {
            "ordinal": "EXACT_NONNEGATIVE_INTEGER",
            "entry_sha256": "LOWERCASE_SHA256",
            "prior_head_sha256": "LOWERCASE_SHA256",
            "head_sha256": "LOWERCASE_SHA256",
        },
        "head_digest_domain_hex": (
            b"heterodiff/b02-b03/contact-access-log-head/v1\0".hex()
        ),
        "head_digest_rule": (
            "DOMAIN_HEX_BYTES_PLUS_CANONICAL_JSON_EXCLUDING_HEAD_SHA256"
        ),
        "head_previous_link_rule": (
            "HEAD_ORDINAL_ZERO_PRIOR_HEAD_SHA256_EQUALS_64_LOWERCASE_ZEROES_"
            "OTHERWISE_EQUALS_EXACT_HEAD_SHA256_AT_ORDINAL_MINUS_ONE"
        ),
        "head_update_rule": (
            "CREATE_ONE_IMMUTABLE_HEAD_FILE_O_CREAT_O_EXCL_MODE_0600_AFTER_"
            "ENTRY_FSYNC_BIND_EXACT_PRIOR_HEAD_THEN_FSYNC_HEAD_AND_DIRECTORY"
        ),
        "current_head_rule": (
            "HIGHEST_CONTIGUOUS_FULLY_VERIFIED_IMMUTABLE_HEAD_ORDINAL"
        ),
        "sensitive_payload_rule": (
            "PRIVATE_CONTENT_ADDRESSED_CUSTODY_HASHES_ONLY_IN_LOG"
        ),
        "timestamp_attestation_rule": (
            "OPERATIONAL_RECEIPT_TIMESTAMPS_ONLY_NO_EXTERNAL_ATTESTATION_"
            "UNLESS_SEPARATELY_SUPPLIED"
        ),
        "timestamp_source_and_order_rule": (
            "CALLER_SUPPLIED_OPERATIONAL_RECEIPT_RFC3339_UTC_EXACTLY_9_"
            "FRACTIONAL_DIGITS_Z_SUFFIX_FINISH_NULL_OR_NOT_BEFORE_START"
        ),
        "recovery_rule": (
            "UNPUBLISHED_ENTRY_FILE_IS_ORPHAN_TERMINAL_MANUAL_REVIEW_NO_REUSE_"
            "HEAD_COLLISION_GAP_OR_PRIOR_LINK_MISMATCH_TERMINAL_NO_RETRY"
        ),
        "intent_without_outcome_disposition": "TERMINAL_SPENT_INCOMPLETE_NO_RETRY",
        "rewrite_deletion_retry_fallback_or_reordering_permitted": False,
        "operational_log_or_head_claimed_present": False,
    }


def outcome_start_time_matches_bound_intent(
    intent_started_time: object, outcome_started_time: object,
) -> bool:
    """Return the narrow exact cross-event start-time continuity predicate."""
    return (
        type(intent_started_time) is str
        and type(outcome_started_time) is str
        and outcome_started_time == intent_started_time
    )


def definition_records() -> Tuple[Tuple[str, Dict[str, Any], str], ...]:
    records = (
        ("held_out_material_definition", held_out_material_definition()),
        ("final_opening_rule", final_opening_rule()),
        ("append_only_log_schema", append_only_log_schema()),
    )
    return tuple(
        (name, record, record_sha256(name, record)) for name, record in records
    )


BLOCKED_NON_F061_SLOTS = (
    "physionet_selector_record_sha256", "retail_selector_record_sha256",
    "contact_target_roster_sha256", "contact_target_count",
    "approval_requirement_roster_sha256",
    "approval_receipt_validator_roster_sha256",
    "contact_roster_complete", "escrow_control_binding_sha256",
)
SEPARATELY_BLOCKED_SLOT = "conflict_of_interest_determination_sha256"


def unresolved_operational_state() -> Dict[str, Any]:
    return {
        "blocked_non_f061_slots": {name: None for name in BLOCKED_NON_F061_SLOTS},
        "conflict_of_interest_determination_sha256": None,
        "owner_principals": [None] * 9,
        "owner_acceptance_sha256s": [None] * 9,
        "keys": None, "acl": None, "external_observations": None,
        "independent_review_receipt_sha256": None,
        "authority": False, "network_or_contact": False, "data_opened": False,
        "escrow_activated": False, "scientific_execution": False,
        "budgets": {name: 0 for name in (
            "admin_contact", "data_access", "snapshot_open", "split_execution",
            "escrow_activation", "scientific_execution",
        )},
        "closures": {name: 0 for name in (
            "B02", "B03", "F061", "operational_tasks", "scientific_fields",
        )},
    }


__all__ = (
    "APPEND_ONLY_LOG_SCHEMA_ID", "BLOCKED_NON_F061_SLOTS",
    "FINAL_OPENING_RULE_ID", "HELD_OUT_MATERIAL_DEFINITION_ID",
    "SEPARATELY_BLOCKED_SLOT", "append_only_log_schema", "definition_records",
    "final_opening_rule", "held_out_material_definition",
    "outcome_start_time_matches_bound_intent", "record_sha256",
    "unresolved_operational_state",
)
