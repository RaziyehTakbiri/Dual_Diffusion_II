"""Pure offline definition of the two-domain precontact activation boundary.

This module has no file, network, process, credential, dataset, parsing,
splitting, escrow, entropy, training, inference, or scientific-execution route.
It can establish only that a closed-world offline population is structurally
eligible for a separate external independent review. It cannot accept review
metadata, advance into a reviewed state, grant authority, or allocate an
operational attempt budget.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
from typing import Any, Dict, Optional, Tuple


SCHEMA_VERSION = "heterodiff-two-domain-offline-precontact-activation-v2"
PACKAGE_KIND = "TWO_DOMAIN_OFFLINE_PRECONTACT_ACTIVATION"
PHYSIONET_DOMAIN = "physionet-challenge-2012"
RETAIL_DOMAIN = "online-retail-ii"
PHYSIONET_URL = "https://physionet.org/content/challenge-2012/1.0.0/"
RETAIL_URL = "https://archive.ics.uci.edu/dataset/502/online+retail+ii"

PHYSIONET_SELECTOR_ID = (
    "PHYSIONET_CHALLENGE_2012_VERSION_1_0_0_EXACT_REGISTERED_URL_SELECTOR_V1"
)
RETAIL_SELECTOR_ID = "UCI_DATASET_502_ONLINE_RETAIL_II_EXACT_REGISTERED_URL_SELECTOR_V1"
SELECTOR_SCHEMA_VERSION = "heterodiff-two-domain-acquisition-selector-v1"

PHYSIONET_SPLIT_CONTRACT_ID = "PHYSIONET_PATIENT_HASH_EXPLICIT_F061_HAMILTON_V1"
PHYSIONET_SPLIT_CONTRACT_SHA256 = (
    "32651b654a1b11ceb256f4f6cc6df1ff567d34538c3c2c6033d9acf1fc020b2d"
)
RETAIL_SPLIT_CONTRACT_ID = (
    "RETAIL_F060_SOURCE_CIVIL_SHARED_F061_INTEGRATED_REPLAY_V3"
)
RETAIL_SPLIT_CONTRACT_SHA256 = (
    "b1a4fef836a50987b5d723e2bd133605bd907b4d7904f7cd6e87ca1d83077659"
)

F061_ALLOCATION_SCHEMA = "heterodiff-two-domain-f061-shared-policy-v1"
F061_ALLOWED_METHOD_ID = "POWER_REVIEWED_EXACT_PROPORTIONS_HAMILTON_V1"
F061_ALLOWED_MODES = ("EXACT_PROPORTIONS_HAMILTON",)
F061_HAMILTON_ROUNDING_RULE_ID = (
    "HAMILTON_DESCENDING_INTEGER_REMAINDER_TIE_TRAIN_VALIDATION_TEST_V1"
)
RETAIL_F061_PROPOSAL_SCHEMA = "heterodiff-f061-exact-allocation-definition-v1"
RETAIL_F061_ADAPTER_ID = "SHARED_POLICY_TO_RETAIL_F061_PROPOSAL_ADAPTER_V1"
RETAIL_F061_ADAPTER_SHA256 = (
    "c442a1a7ee95078d07852d600f7ea2c35ec52c309b6f97d9cbdba41374f878ee"
)
PHYSIONET_F061_ADAPTER_ID = (
    "SHARED_POLICY_AND_NATURAL_GROUP_COUNT_TO_PHYSIONET_F061_PROPOSAL_ADAPTER_V1"
)
PHYSIONET_F061_ADAPTER_SHA256 = (
    "018def4ab7d7f991d4820da612489b5162d91d8c04e4231f3429295cb032a52b"
)

ESCROW_CONTROL_ID = "INDEPENDENT_HELD_OUT_ESCROW_LEAST_PRIVILEGE_ACL_V1"
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

ADMIN_QUESTIONS: Tuple[str, ...] = (
    "What is the canonical dataset identifier and current immutable version or "
    "revision for the registered target?",
    "Is there exactly one immutable archive locator, with SHA-256 and byte count, "
    "for that version?",
    "What exact license or terms govern access, storage, analysis, publication, "
    "redistribution, and retention?",
    "What account, authentication, or data-use-agreement requirements apply?",
    "What governance, ethics, privacy, clinical, or institutional approvals are "
    "required before access?",
    "What storage, deletion, retention, disclosure, and publication controls are mandatory?",
    "What schema and timezone metadata are required to evaluate the frozen selector "
    "and split rules deterministically?",
)

ADMIN_SUCCESS_PREDICATE = (
    "EXACT_REGISTERED_TARGET_NO_REDIRECT_AND_ONE_CANONICAL_VERSION_REVISION_"
    "AND_EXACTLY_ONE_IMMUTABLE_ARCHIVE_LOCATOR_SHA256_BYTE_COUNT_AND_COMPLETE_"
    "LICENSE_GOVERNANCE_ACCESS_SCHEMA_TIMEZONE_REQUIREMENTS_RECEIPT"
)
DATA_SUCCESS_PREDICATE = (
    "EXACT_MATCHING_ADMIN_SUCCESS_AND_ALL_REQUIRED_APPROVAL_RECEIPTS_AND_"
    "SEPARATELY_REVIEWED_DATA_ACCESS_INSTANCE_AND_FRESH_EXACT_DATA_ACCESS_"
    "AUTHORITY_AND_DURABLE_INTENT_AND_ONE_CONTENT_ADDRESSED_ARCHIVE_MATCHING_"
    "VERSION_LOCATOR_SHA256_AND_BYTE_COUNT"
)

TERMINAL_FAILURE_MAP: Tuple[Tuple[str, str], ...] = (
    ("PROTOCOL_VIOLATION", "TERMINAL_PROTOCOL_VIOLATION_NO_REPAIR"),
    ("INTENT_WITHOUT_OUTCOME", "TERMINAL_SPENT_INCOMPLETE_NO_RETRY"),
    ("ADMIN_DENIED", "ADMIN_CONTACT_TERMINAL_NO_GO"),
    ("ADMIN_FAILED", "ADMIN_CONTACT_TERMINAL_NO_GO"),
    ("ADMIN_CANCELLED", "ADMIN_CONTACT_TERMINAL_NO_GO"),
    ("REQUIRED_APPROVALS_INCOMPLETE", "APPROVALS_INCOMPLETE_TERMINAL_NO_GO"),
    ("SELECTED_VERSION_UNAVAILABLE", "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO"),
    ("ACQUISITION_SELECTOR_MISMATCH", "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO"),
    ("SNAPSHOT_IDENTITY_OR_HASH_MISMATCH", "SELECTOR_OR_SNAPSHOT_TERMINAL_NO_GO"),
    ("DATA_ACCESS_DENIED", "DATA_ACCESS_TERMINAL_NO_GO"),
    ("DATA_ACCESS_FAILED", "DATA_ACCESS_TERMINAL_NO_GO"),
    ("DATA_ACCESS_CANCELLED", "DATA_ACCESS_TERMINAL_NO_GO"),
)

STATE_MACHINE: Tuple[str, ...] = (
    "DESIGN_FROZEN_AWAITING_POPULATED_PRECONTACT_INSTANCE",
    "PRECONTACT_INSTANCE_POPULATED_AWAITING_INDEPENDENT_REVIEW",
    "PRECONTACT_INSTANCE_REVIEWED_AWAITING_FRESH_ADMIN_CONTACT_AUTHORITY",
    "ADMIN_CONTACT_AUTHORIZED_AWAITING_DURABLE_INTENT",
    "ADMIN_CONTACT_INTENT_RESERVED_AWAITING_CONTACT",
    "ADMIN_CONTACT_OUTCOME_RECORDED_AWAITING_REQUIRED_APPROVALS",
    "APPROVALS_COMPLETE_AWAITING_REVIEWED_DATA_ACCESS_INSTANCE",
    "DATA_ACCESS_INSTANCE_REVIEWED_AWAITING_FRESH_DATA_ACCESS_AUTHORITY",
    "DATA_ACCESS_AUTHORIZED_AWAITING_DURABLE_INTENT",
    "DATA_ACCESS_INTENT_RESERVED_AWAITING_ACCESS",
    "SNAPSHOT_OBSERVED_AND_CUSTODIED_AWAITING_DETERMINISTIC_SPLIT",
    "SPLIT_ASSIGNED_AND_HELD_OUT_ESCROW_ACTIVE",
    "FINAL_OPENING_AWAITING_SEPARATE_AUTHORITY",
)

OFFLINE_ELIGIBLE_DECISION = "ELIGIBLE_FOR_EXTERNAL_INDEPENDENT_REVIEW"
OFFLINE_HOLD_DECISION = "HOLD_OFFLINE_PRECONTACT_POPULATION_INCOMPLETE"

_OPERATION_IDENTITY_DOMAIN = b"heterodiff/offline-precontact-operation/v2\0"
_POPULATION_IDENTITY_DOMAIN = b"heterodiff/offline-precontact-population/v2\0"
_PACKAGE_IDENTITY_DOMAIN = b"heterodiff/offline-precontact-package/v2\0"
_F061_PROPOSAL_DOMAIN = b"heterodiff/two-domain-f061-shared-policy-proposal/v1\0"
_F061_DEFINITION_DOMAIN = b"heterodiff/two-domain-f061-shared-policy-definition/v1\0"
_RETAIL_ADAPTER_DOMAIN = b"heterodiff/two-domain-f061-retail-adapter-contract/v1\0"
_PHYSIONET_ADAPTER_DOMAIN = (
    b"heterodiff/two-domain-f061-physionet-adapter-contract/v1\0"
)


class OfflineActivationError(ValueError):
    """Fail-closed malformed, drifted, or over-authorized offline input."""


@dataclass(frozen=True)
class OperationSpec:
    """One inert, content-addressed future operation definition."""

    global_ordinal: int
    operation_id: str
    domain_id: str
    phase: str
    exact_target: Optional[str]
    exact_target_derivation: str
    selector_identity: str
    exact_permitted_request_kind: str
    administrative_questions: Tuple[str, ...]
    matching_admin_operation_id: Optional[str]
    required_prior_receipts: Tuple[str, ...]
    success_predicate: str
    terminal_disposition: str
    maximum_attempt_count: int
    retry_limit: int
    redirect_limit: int
    address_fallback_limit: int
    authentication_permitted: bool
    download_permitted: bool
    data_opening_permitted: bool
    currently_eligible: bool
    operation_identity_sha256: str


@dataclass(frozen=True)
class OwnerManifest:
    """Nine accountable principals and their acceptance receipt bindings."""

    accountable_governance_owner_id: Optional[str]
    accountable_governance_owner_acceptance_sha256: Optional[str]
    license_privacy_institutional_approval_endpoint_id: Optional[str]
    license_privacy_institutional_approval_endpoint_acceptance_sha256: Optional[str]
    raw_snapshot_custodian_id: Optional[str]
    raw_snapshot_custodian_acceptance_sha256: Optional[str]
    deterministic_split_operator_id: Optional[str]
    deterministic_split_operator_acceptance_sha256: Optional[str]
    independent_held_out_escrow_custodian_id: Optional[str]
    independent_held_out_escrow_custodian_acceptance_sha256: Optional[str]
    independent_final_opening_approver_id: Optional[str]
    independent_final_opening_approver_acceptance_sha256: Optional[str]
    key_acl_acceptance_authority_id: Optional[str]
    key_acl_acceptance_authority_acceptance_sha256: Optional[str]
    retention_deletion_owner_id: Optional[str]
    retention_deletion_owner_acceptance_sha256: Optional[str]
    incident_response_owner_id: Optional[str]
    incident_response_owner_acceptance_sha256: Optional[str]


@dataclass(frozen=True)
class OfflineDefinitionBindings:
    """Closed-world definitions and future content-addressed binding slots."""

    selector_schema_version: str
    physionet_selector_id: str
    physionet_selector_record_sha256: Optional[str]
    retail_selector_id: str
    retail_selector_record_sha256: Optional[str]
    physionet_split_contract_id: str
    physionet_split_contract_sha256: str
    retail_split_contract_id: str
    retail_split_contract_sha256: str
    retail_f061_adapter_id: str
    retail_f061_adapter_sha256: str
    physionet_f061_adapter_id: str
    physionet_f061_adapter_sha256: str
    f061_allocation_schema: str
    f061_allowed_method_id: str
    f061_allocation_id: Optional[str]
    f061_mode: Optional[str]
    f061_values: Optional[Tuple[int, int, int]]
    f061_denominator_is_null: Optional[bool]
    f061_denominator: Optional[int]
    f061_minimum_counts: Optional[Tuple[int, int, int]]
    f061_rounding_rule_id: Optional[str]
    f061_power_requirement_id: Optional[str]
    f061_allocation_proposal_sha256: Optional[str]
    f061_power_review_receipt_sha256: Optional[str]
    f061_power_review_accepted: Optional[bool]
    f061_allocation_definition_sha256: Optional[str]
    contact_target_roster_sha256: Optional[str]
    contact_target_count: Optional[int]
    approval_requirement_roster_sha256: Optional[str]
    approval_receipt_validator_roster_sha256: Optional[str]
    conflict_of_interest_determination_sha256: Optional[str]
    contact_roster_complete: Optional[bool]
    escrow_control_id: str
    held_out_material_definition_id: str
    final_opening_rule_id: str
    escrow_control_binding_sha256: Optional[str]
    held_out_material_definition_sha256: Optional[str]
    final_opening_rule_sha256: Optional[str]
    append_only_log_schema_id: str
    append_only_log_schema_sha256: Optional[str]
    durable_intent_rule_id: str
    terminal_failure_map: Tuple[Tuple[str, str], ...]
    unknown_or_missing_outcome_is_success: bool
    repair_retry_replacement_fallback_permitted: bool


@dataclass(frozen=True)
class ExternalObservationSlots:
    """Future-observed values that must remain strict null offline."""

    domain_id: str
    administrative_contact_outcome: None
    data_access_outcome: None
    observed_snapshot_version: None
    raw_snapshot_sha256: None
    raw_snapshot_byte_count: None
    etag_or_equivalent: None
    license_text_receipt_sha256: None
    governance_approval_receipt_sha256: None
    ethics_approval_receipt_sha256: None
    split_counts: None
    split_manifest_sha256: None
    escrow_receipt_sha256: None


@dataclass(frozen=True)
class ExecutionBoundary:
    """Every operational capability is fixed to false and every budget to zero."""

    operational_authority_present: bool
    admin_contact_authority_present: bool
    data_access_authority_present: bool
    durable_intent_present: bool
    network_or_contact_authorized: bool
    authentication_authorized: bool
    download_authorized: bool
    data_opening_authorized: bool
    split_execution_authorized: bool
    escrow_activation_authorized: bool
    admin_contact_attempt_budget: int
    data_access_attempt_budget: int
    snapshot_open_budget: int
    split_execution_budget: int
    escrow_activation_budget: int
    scientific_execution_budget: int


@dataclass(frozen=True)
class OfflinePrecontactActivation:
    """Content-addressed immutable offline population candidate."""

    schema_version: str
    package_kind: str
    predecessor_set_sha256: str
    state_machine: Tuple[str, ...]
    current_state_ordinal: int
    operation_roster: Tuple[OperationSpec, ...]
    owner_manifest: OwnerManifest
    definition_bindings: OfflineDefinitionBindings
    external_observations: Tuple[ExternalObservationSlots, ...]
    access_log_head_sha256: None
    external_review_receipt_sha256: None
    external_review_decision: None
    external_reviewer_principal_id: None
    execution_boundary: ExecutionBoundary
    population_identity_sha256: str
    package_identity_sha256: str


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise OfflineActivationError("NONCANONICAL_VALUE") from error


def _digest(domain: bytes, value: Any) -> str:
    return hashlib.sha256(domain + _canonical_bytes(value)).hexdigest()


def retail_f061_adapter_record() -> Dict[str, Any]:
    """Return the canonical shared-policy-to-Retail adapter contract."""

    return {
        "schema_version": "heterodiff-f061-adapter-contract-v1",
        "adapter_id": RETAIL_F061_ADAPTER_ID,
        "source_schema": F061_ALLOCATION_SCHEMA,
        "target_schema": RETAIL_F061_PROPOSAL_SCHEMA,
        "required_inputs": [
            "allocation_id", "mode", "values", "denominator",
            "minimum_counts", "power_requirement_id",
        ],
        "outputs": [
            "schema_version", "allocation_id", "mode", "values", "denominator",
            "minimum_counts", "power_requirement_id",
        ],
        "algorithm": "MAP_TUPLES_TO_TRAIN_VALIDATION_TEST_INTEGER_MAPPINGS_V1",
        "review_semantics": (
            "SHARED_POLICY_REVIEW_ONLY_NO_DOMAIN_RESOLUTION_REVIEW_V1"
        ),
    }


def physionet_f061_adapter_record() -> Dict[str, Any]:
    """Return the canonical shared-policy-to-PhysioNet adapter contract."""

    return {
        "schema_version": "heterodiff-f061-adapter-contract-v1",
        "adapter_id": PHYSIONET_F061_ADAPTER_ID,
        "source_schema": F061_ALLOCATION_SCHEMA,
        "target_schema": "PHYSIONET_F061_SNAPSHOT_RESOLVED_PROPOSAL_CODEC_V1",
        "required_inputs": [
            "values", "denominator", "minimum_counts", "rounding_rule_id",
            "natural_group_count",
        ],
        "outputs": [
            "patient_count", "numerators", "denominator", "counts",
            "minimum_counts", "rounding_rule_id",
        ],
        "algorithm": (
            "HAMILTON_DESCENDING_REMAINDER_TIE_TRAIN_VALIDATION_TEST_V1"
        ),
        "review_semantics": (
            "REQUIRES_SEPARATE_LATER_PHYSIONET_RESOLVED_COUNT_REVIEW_V1"
        ),
    }


def retail_f061_adapter_sha256(record: Optional[Dict[str, Any]] = None) -> str:
    """Recompute the domain-separated Retail adapter contract digest."""

    value = retail_f061_adapter_record() if record is None else record
    return _digest(_RETAIL_ADAPTER_DOMAIN, value)


def physionet_f061_adapter_sha256(record: Optional[Dict[str, Any]] = None) -> str:
    """Recompute the domain-separated PhysioNet adapter contract digest."""

    value = physionet_f061_adapter_record() if record is None else record
    return _digest(_PHYSIONET_ADAPTER_DOMAIN, value)


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_sha256(value: Any, name: str) -> str:
    if not _is_sha256(value):
        raise OfflineActivationError(f"{name}:INVALID_SHA256")
    return value


def _require_identifier(value: Any, name: str) -> str:
    if (
        type(value) is not str
        or not value
        or len(value) > 256
        or value != value.strip()
        or not value.isascii()
        or any(ord(character) < 0x21 or ord(character) > 0x7E for character in value)
    ):
        raise OfflineActivationError(f"{name}:INVALID_IDENTIFIER")
    return value


def _operation_core(operation: OperationSpec) -> Dict[str, Any]:
    value = asdict(operation)
    value.pop("operation_identity_sha256")
    return value


def operation_identity_sha256(operation: OperationSpec) -> str:
    """Return the domain-separated identity of one inert operation."""

    if type(operation) is not OperationSpec:
        raise OfflineActivationError("OPERATION_WRONG_TYPE")
    return _digest(_OPERATION_IDENTITY_DOMAIN, _operation_core(operation))


def _seal_operation(operation: OperationSpec) -> OperationSpec:
    return replace(
        operation,
        operation_identity_sha256=operation_identity_sha256(operation),
    )


def _operation(
    ordinal: int,
    operation_id: str,
    domain_id: str,
    phase: str,
    exact_target: Optional[str],
    target_derivation: str,
    selector_identity: str,
    request_kind: str,
    questions: Tuple[str, ...],
    matching_admin_operation_id: Optional[str],
    required_prior_receipts: Tuple[str, ...],
    success_predicate: str,
    terminal_disposition: str,
) -> OperationSpec:
    return _seal_operation(
        OperationSpec(
            global_ordinal=ordinal,
            operation_id=operation_id,
            domain_id=domain_id,
            phase=phase,
            exact_target=exact_target,
            exact_target_derivation=target_derivation,
            selector_identity=selector_identity,
            exact_permitted_request_kind=request_kind,
            administrative_questions=questions,
            matching_admin_operation_id=matching_admin_operation_id,
            required_prior_receipts=required_prior_receipts,
            success_predicate=success_predicate,
            terminal_disposition=terminal_disposition,
            maximum_attempt_count=1,
            retry_limit=0,
            redirect_limit=0,
            address_fallback_limit=0,
            authentication_permitted=False,
            download_permitted=False,
            data_opening_permitted=False,
            currently_eligible=False,
            operation_identity_sha256="0" * 64,
        )
    )


EXACT_OPERATION_ROSTER: Tuple[OperationSpec, ...] = (
    _operation(
        0,
        "PHYSIONET_ADMIN_METADATA_LICENSE_GOVERNANCE",
        PHYSIONET_DOMAIN,
        "ADMIN",
        PHYSIONET_URL,
        "LITERAL_REGISTERED_SOURCE_URL",
        PHYSIONET_SELECTOR_ID,
        "ADMIN_METADATA_LICENSE_GOVERNANCE_ONLY_NO_AUTH_NO_DOWNLOAD_NO_DATA",
        ADMIN_QUESTIONS,
        None,
        (
            "POPULATED_INSTANCE_REVIEW",
            "FRESH_EXACT_ADMIN_CONTACT_AUTHORITY",
            "DURABLE_INTENT",
        ),
        ADMIN_SUCCESS_PREDICATE,
        "ADMIN_CONTACT_TERMINAL_NO_GO",
    ),
    _operation(
        1,
        "RETAIL_ADMIN_METADATA_LICENSE_GOVERNANCE",
        RETAIL_DOMAIN,
        "ADMIN",
        RETAIL_URL,
        "LITERAL_REGISTERED_SOURCE_URL",
        RETAIL_SELECTOR_ID,
        "ADMIN_METADATA_LICENSE_GOVERNANCE_ONLY_NO_AUTH_NO_DOWNLOAD_NO_DATA",
        ADMIN_QUESTIONS,
        None,
        (
            "POPULATED_INSTANCE_REVIEW",
            "FRESH_EXACT_ADMIN_CONTACT_AUTHORITY",
            "DURABLE_INTENT",
        ),
        ADMIN_SUCCESS_PREDICATE,
        "ADMIN_CONTACT_TERMINAL_NO_GO",
    ),
    _operation(
        2,
        "PHYSIONET_DATA_AUTHENTICATION_OR_DOWNLOAD",
        PHYSIONET_DOMAIN,
        "DATA",
        None,
        "DETERMINISTIC_FROM_MATCHING_ADMIN_EXACT_SUCCESS_ONLY",
        PHYSIONET_SELECTOR_ID,
        "DORMANT_DATA_OPERATION_NOT_AUTHORIZED_BY_OFFLINE_PACKAGE",
        (),
        "PHYSIONET_ADMIN_METADATA_LICENSE_GOVERNANCE",
        (
            "MATCHING_ADMIN_EXACT_SUCCESS",
            "ALL_REQUIRED_APPROVAL_RECEIPTS",
            "SEPARATELY_REVIEWED_DATA_ACCESS_INSTANCE",
            "FRESH_EXACT_DATA_ACCESS_AUTHORITY",
            "DURABLE_INTENT",
        ),
        DATA_SUCCESS_PREDICATE,
        "DATA_ACCESS_TERMINAL_NO_GO",
    ),
    _operation(
        3,
        "RETAIL_DATA_AUTHENTICATION_OR_DOWNLOAD",
        RETAIL_DOMAIN,
        "DATA",
        None,
        "DETERMINISTIC_FROM_MATCHING_ADMIN_EXACT_SUCCESS_ONLY",
        RETAIL_SELECTOR_ID,
        "DORMANT_DATA_OPERATION_NOT_AUTHORIZED_BY_OFFLINE_PACKAGE",
        (),
        "RETAIL_ADMIN_METADATA_LICENSE_GOVERNANCE",
        (
            "MATCHING_ADMIN_EXACT_SUCCESS",
            "ALL_REQUIRED_APPROVAL_RECEIPTS",
            "SEPARATELY_REVIEWED_DATA_ACCESS_INSTANCE",
            "FRESH_EXACT_DATA_ACCESS_AUTHORITY",
            "DURABLE_INTENT",
        ),
        DATA_SUCCESS_PREDICATE,
        "DATA_ACCESS_TERMINAL_NO_GO",
    ),
)


ZERO_EXECUTION_BOUNDARY = ExecutionBoundary(
    operational_authority_present=False,
    admin_contact_authority_present=False,
    data_access_authority_present=False,
    durable_intent_present=False,
    network_or_contact_authorized=False,
    authentication_authorized=False,
    download_authorized=False,
    data_opening_authorized=False,
    split_execution_authorized=False,
    escrow_activation_authorized=False,
    admin_contact_attempt_budget=0,
    data_access_attempt_budget=0,
    snapshot_open_budget=0,
    split_execution_budget=0,
    escrow_activation_budget=0,
    scientific_execution_budget=0,
)


def unresolved_owner_manifest() -> OwnerManifest:
    """Return nine principal roles and acceptance bindings as strict nulls."""

    return OwnerManifest(*([None] * 18))


def unresolved_definition_bindings() -> OfflineDefinitionBindings:
    """Return fixed definitions with every future-dependent binding null."""

    return OfflineDefinitionBindings(
        selector_schema_version=SELECTOR_SCHEMA_VERSION,
        physionet_selector_id=PHYSIONET_SELECTOR_ID,
        physionet_selector_record_sha256=None,
        retail_selector_id=RETAIL_SELECTOR_ID,
        retail_selector_record_sha256=None,
        physionet_split_contract_id=PHYSIONET_SPLIT_CONTRACT_ID,
        physionet_split_contract_sha256=PHYSIONET_SPLIT_CONTRACT_SHA256,
        retail_split_contract_id=RETAIL_SPLIT_CONTRACT_ID,
        retail_split_contract_sha256=RETAIL_SPLIT_CONTRACT_SHA256,
        retail_f061_adapter_id=RETAIL_F061_ADAPTER_ID,
        retail_f061_adapter_sha256=RETAIL_F061_ADAPTER_SHA256,
        physionet_f061_adapter_id=PHYSIONET_F061_ADAPTER_ID,
        physionet_f061_adapter_sha256=PHYSIONET_F061_ADAPTER_SHA256,
        f061_allocation_schema=F061_ALLOCATION_SCHEMA,
        f061_allowed_method_id=F061_ALLOWED_METHOD_ID,
        f061_allocation_id=None,
        f061_mode=None,
        f061_values=None,
        f061_denominator_is_null=None,
        f061_denominator=None,
        f061_minimum_counts=None,
        f061_rounding_rule_id=None,
        f061_power_requirement_id=None,
        f061_allocation_proposal_sha256=None,
        f061_power_review_receipt_sha256=None,
        f061_power_review_accepted=None,
        f061_allocation_definition_sha256=None,
        contact_target_roster_sha256=None,
        contact_target_count=None,
        approval_requirement_roster_sha256=None,
        approval_receipt_validator_roster_sha256=None,
        conflict_of_interest_determination_sha256=None,
        contact_roster_complete=None,
        escrow_control_id=ESCROW_CONTROL_ID,
        held_out_material_definition_id=HELD_OUT_MATERIAL_DEFINITION_ID,
        final_opening_rule_id=FINAL_OPENING_RULE_ID,
        escrow_control_binding_sha256=None,
        held_out_material_definition_sha256=None,
        final_opening_rule_sha256=None,
        append_only_log_schema_id=APPEND_ONLY_LOG_SCHEMA_ID,
        append_only_log_schema_sha256=None,
        durable_intent_rule_id=DURABLE_INTENT_RULE_ID,
        terminal_failure_map=TERMINAL_FAILURE_MAP,
        unknown_or_missing_outcome_is_success=False,
        repair_retry_replacement_fallback_permitted=False,
    )


def _empty_observation(domain_id: str) -> ExternalObservationSlots:
    return ExternalObservationSlots(domain_id, *([None] * 12))


EMPTY_EXTERNAL_OBSERVATIONS: Tuple[ExternalObservationSlots, ...] = (
    _empty_observation(PHYSIONET_DOMAIN),
    _empty_observation(RETAIL_DOMAIN),
)

_OWNER_ID_FIELDS = tuple(
    field for field in OwnerManifest.__dataclass_fields__ if field.endswith("_id")
)
_OWNER_ACCEPTANCE_FIELDS = tuple(
    field
    for field in OwnerManifest.__dataclass_fields__
    if field.endswith("_acceptance_sha256")
)
_FUTURE_BINDING_DIGEST_FIELDS = (
    "physionet_selector_record_sha256",
    "retail_selector_record_sha256",
    "f061_allocation_proposal_sha256",
    "f061_power_review_receipt_sha256",
    "f061_allocation_definition_sha256",
    "contact_target_roster_sha256",
    "approval_requirement_roster_sha256",
    "approval_receipt_validator_roster_sha256",
    "conflict_of_interest_determination_sha256",
    "escrow_control_binding_sha256",
    "held_out_material_definition_sha256",
    "final_opening_rule_sha256",
    "append_only_log_schema_sha256",
)


def _validate_owner_manifest(owner: OwnerManifest) -> Tuple[str, ...]:
    if type(owner) is not OwnerManifest:
        raise OfflineActivationError("OWNER_MANIFEST_WRONG_TYPE")
    missing = []
    principals = []
    for field in _OWNER_ID_FIELDS:
        value = getattr(owner, field)
        if value is None:
            missing.append(field)
        else:
            principals.append(_require_identifier(value, f"owner_manifest.{field}"))
    for field in _OWNER_ACCEPTANCE_FIELDS:
        value = getattr(owner, field)
        if value is None:
            missing.append(field)
        else:
            _require_sha256(value, f"owner_manifest.{field}")
    if not missing and len(set(principals)) != len(principals):
        raise OfflineActivationError("PRINCIPAL_ROLE_ALIAS_FORBIDDEN")
    return tuple(missing)


def _f061_proposal_payload(bindings: OfflineDefinitionBindings) -> Dict[str, Any]:
    return {
        "schema_version": bindings.f061_allocation_schema,
        "allocation_id": bindings.f061_allocation_id,
        "mode": bindings.f061_mode,
        "values": bindings.f061_values,
        "denominator_is_null": bindings.f061_denominator_is_null,
        "denominator": bindings.f061_denominator,
        "minimum_counts": bindings.f061_minimum_counts,
        "rounding_rule_id": bindings.f061_rounding_rule_id,
        "power_requirement_id": bindings.f061_power_requirement_id,
    }


def f061_allocation_proposal_sha256(
    bindings: OfflineDefinitionBindings,
) -> str:
    """Hash the exact proposed F061 definition before external power review."""

    if type(bindings) is not OfflineDefinitionBindings:
        raise OfflineActivationError("DEFINITION_BINDINGS_WRONG_TYPE")
    payload = _f061_proposal_payload(bindings)
    if any(value is None for value in payload.values()):
        raise OfflineActivationError("F061_PROPOSAL_INCOMPLETE")
    return _digest(_F061_PROPOSAL_DOMAIN, payload)


def f061_allocation_definition_sha256(
    bindings: OfflineDefinitionBindings,
) -> str:
    """Hash proposal, external review receipt, and exact accepted=True."""

    if type(bindings) is not OfflineDefinitionBindings:
        raise OfflineActivationError("DEFINITION_BINDINGS_WRONG_TYPE")
    proposal_sha256 = _require_sha256(
        bindings.f061_allocation_proposal_sha256,
        "definition_bindings.f061_allocation_proposal_sha256",
    )
    review_sha256 = _require_sha256(
        bindings.f061_power_review_receipt_sha256,
        "definition_bindings.f061_power_review_receipt_sha256",
    )
    if type(bindings.f061_power_review_accepted) is not bool:
        raise OfflineActivationError("F061_POWER_REVIEW_ACCEPTED_INVALID")
    if not bindings.f061_power_review_accepted:
        raise OfflineActivationError("F061_POWER_REVIEW_NOT_ACCEPTED")
    return _digest(
        _F061_DEFINITION_DOMAIN,
        {
            "allocation_proposal_sha256": proposal_sha256,
            "power_review_receipt_sha256": review_sha256,
            "power_review_accepted": True,
        },
    )


def project_shared_policy_to_retail_f061_proposal(
    bindings: OfflineDefinitionBindings,
) -> Dict[str, Any]:
    """Project the reviewed shared policy into Retail's distinct proposal codec."""

    missing = _validate_definition_bindings(bindings)
    if missing:
        raise OfflineActivationError("F061_SHARED_POLICY_INCOMPLETE")
    split_names = ("TRAIN", "VALIDATION", "TEST")
    return {
        "schema_version": RETAIL_F061_PROPOSAL_SCHEMA,
        "allocation_id": bindings.f061_allocation_id,
        "mode": "EXACT_PROPORTIONS_HAMILTON",
        "values": dict(zip(split_names, bindings.f061_values)),
        "denominator": bindings.f061_denominator,
        "minimum_counts": dict(zip(split_names, bindings.f061_minimum_counts)),
        "power_requirement_id": bindings.f061_power_requirement_id,
    }


def project_shared_policy_to_physionet_f061_proposal(
    bindings: OfflineDefinitionBindings,
    natural_group_count: int,
) -> Dict[str, Any]:
    """Resolve a shared policy for PhysioNet's later exact-count review.

    This projection does not claim that the shared-policy review accepted the
    snapshot-resolved counts. The returned proposal must receive its own later
    PhysioNet external review after ``natural_group_count`` is observed.
    """

    missing = _validate_definition_bindings(bindings)
    if missing:
        raise OfflineActivationError("F061_SHARED_POLICY_INCOMPLETE")
    if type(natural_group_count) is not int or natural_group_count < 1:
        raise OfflineActivationError("PHYSIONET_NATURAL_GROUP_COUNT_INVALID")
    numerators = bindings.f061_values
    denominator = bindings.f061_denominator
    base = tuple(natural_group_count * value // denominator for value in numerators)
    remainders = tuple(
        natural_group_count * value % denominator for value in numerators
    )
    remaining = natural_group_count - sum(base)
    order = sorted(range(3), key=lambda index: (-remainders[index], index))
    counts = list(base)
    for index in order[:remaining]:
        counts[index] += 1
    if any(
        count < minimum
        for count, minimum in zip(counts, bindings.f061_minimum_counts)
    ):
        raise OfflineActivationError("PHYSIONET_F061_RESOLVED_COUNTS_UNDERPOWERED")
    return {
        "patient_count": natural_group_count,
        "numerators": numerators,
        "denominator": denominator,
        "counts": tuple(counts),
        "minimum_counts": bindings.f061_minimum_counts,
        "rounding_rule_id": bindings.f061_rounding_rule_id,
    }


def _validate_definition_bindings(
    bindings: OfflineDefinitionBindings,
) -> Tuple[str, ...]:
    if type(bindings) is not OfflineDefinitionBindings:
        raise OfflineActivationError("DEFINITION_BINDINGS_WRONG_TYPE")
    if retail_f061_adapter_sha256() != RETAIL_F061_ADAPTER_SHA256:
        raise OfflineActivationError("ADAPTER_CONTRACT_DIGEST_MISMATCH:retail")
    if physionet_f061_adapter_sha256() != PHYSIONET_F061_ADAPTER_SHA256:
        raise OfflineActivationError("ADAPTER_CONTRACT_DIGEST_MISMATCH:physionet")
    exact_fields = {
        "selector_schema_version": SELECTOR_SCHEMA_VERSION,
        "physionet_selector_id": PHYSIONET_SELECTOR_ID,
        "retail_selector_id": RETAIL_SELECTOR_ID,
        "physionet_split_contract_id": PHYSIONET_SPLIT_CONTRACT_ID,
        "physionet_split_contract_sha256": PHYSIONET_SPLIT_CONTRACT_SHA256,
        "retail_split_contract_id": RETAIL_SPLIT_CONTRACT_ID,
        "retail_split_contract_sha256": RETAIL_SPLIT_CONTRACT_SHA256,
        "retail_f061_adapter_id": RETAIL_F061_ADAPTER_ID,
        "retail_f061_adapter_sha256": RETAIL_F061_ADAPTER_SHA256,
        "physionet_f061_adapter_id": PHYSIONET_F061_ADAPTER_ID,
        "physionet_f061_adapter_sha256": PHYSIONET_F061_ADAPTER_SHA256,
        "f061_allocation_schema": F061_ALLOCATION_SCHEMA,
        "f061_allowed_method_id": F061_ALLOWED_METHOD_ID,
        "escrow_control_id": ESCROW_CONTROL_ID,
        "held_out_material_definition_id": HELD_OUT_MATERIAL_DEFINITION_ID,
        "final_opening_rule_id": FINAL_OPENING_RULE_ID,
        "append_only_log_schema_id": APPEND_ONLY_LOG_SCHEMA_ID,
        "durable_intent_rule_id": DURABLE_INTENT_RULE_ID,
        "terminal_failure_map": TERMINAL_FAILURE_MAP,
        "unknown_or_missing_outcome_is_success": False,
        "repair_retry_replacement_fallback_permitted": False,
    }
    for field, expected in exact_fields.items():
        value = getattr(bindings, field)
        if type(value) is not type(expected) or value != expected:
            raise OfflineActivationError(f"DEFINITION_DRIFT:{field}")
    if any(
        type(pair) is not tuple
        or len(pair) != 2
        or any(type(item) is not str for item in pair)
        for pair in bindings.terminal_failure_map
    ):
        raise OfflineActivationError("DEFINITION_DRIFT:terminal_failure_map")

    missing = []
    for field in ("f061_allocation_id", "f061_power_requirement_id"):
        value = getattr(bindings, field)
        if value is None:
            missing.append(field)
        else:
            _require_identifier(value, f"definition_bindings.{field}")
    if bindings.f061_mode is None:
        missing.append("f061_mode")
    elif type(bindings.f061_mode) is not str or bindings.f061_mode not in F061_ALLOWED_MODES:
        raise OfflineActivationError("F061_MODE_INVALID")
    if bindings.f061_values is None:
        missing.append("f061_values")
    elif (
        type(bindings.f061_values) is not tuple
        or len(bindings.f061_values) != 3
        or any(type(value) is not int or value < 1 for value in bindings.f061_values)
    ):
        raise OfflineActivationError("F061_VALUES_INVALID")
    if bindings.f061_denominator_is_null is None:
        missing.append("f061_denominator_is_null")
    elif (
        type(bindings.f061_denominator_is_null) is not bool
        or bindings.f061_denominator_is_null is not False
    ):
        raise OfflineActivationError("F061_DENOMINATOR_NULL_FLAG_INVALID")
    if bindings.f061_denominator is None:
        missing.append("f061_denominator")
    elif (
        type(bindings.f061_denominator) is not int
        or bindings.f061_denominator < 1
    ):
        raise OfflineActivationError("F061_DENOMINATOR_INVALID")
    if bindings.f061_minimum_counts is None:
        missing.append("f061_minimum_counts")
    elif (
        type(bindings.f061_minimum_counts) is not tuple
        or len(bindings.f061_minimum_counts) != 3
        or any(
            type(value) is not int or value < 1
            for value in bindings.f061_minimum_counts
        )
    ):
        raise OfflineActivationError("F061_MINIMUM_COUNTS_INVALID")
    if bindings.f061_rounding_rule_id is None:
        missing.append("f061_rounding_rule_id")
    else:
        _require_identifier(
            bindings.f061_rounding_rule_id,
            "definition_bindings.f061_rounding_rule_id",
        )
        if bindings.f061_rounding_rule_id != F061_HAMILTON_ROUNDING_RULE_ID:
            raise OfflineActivationError("F061_ROUNDING_RULE_INVALID")
    f061_core_complete = not any(
        field in missing
        for field in (
            "f061_mode",
            "f061_values",
            "f061_denominator_is_null",
            "f061_denominator",
            "f061_minimum_counts",
            "f061_rounding_rule_id",
        )
    )
    if f061_core_complete:
        if (
            bindings.f061_denominator_is_null is not False
            or type(bindings.f061_denominator) is not int
            or bindings.f061_denominator < 1
            or sum(bindings.f061_values) != bindings.f061_denominator
            or bindings.f061_rounding_rule_id != F061_HAMILTON_ROUNDING_RULE_ID
        ):
            raise OfflineActivationError("F061_HAMILTON_DEFINITION_INCOHERENT")
    if bindings.f061_power_review_accepted is None:
        missing.append("f061_power_review_accepted")
    elif type(bindings.f061_power_review_accepted) is not bool:
        raise OfflineActivationError("F061_POWER_REVIEW_ACCEPTED_INVALID")
    elif not bindings.f061_power_review_accepted:
        raise OfflineActivationError("F061_POWER_REVIEW_NOT_ACCEPTED")
    for field in _FUTURE_BINDING_DIGEST_FIELDS:
        value = getattr(bindings, field)
        if value is None:
            missing.append(field)
        else:
            _require_sha256(value, f"definition_bindings.{field}")
    if bindings.contact_target_count is None:
        missing.append("contact_target_count")
    elif type(bindings.contact_target_count) is not int or bindings.contact_target_count < 2:
        raise OfflineActivationError("CONTACT_TARGET_COUNT_INVALID")
    if bindings.contact_roster_complete is None:
        missing.append("contact_roster_complete")
    elif (
        type(bindings.contact_roster_complete) is not bool
        or not bindings.contact_roster_complete
    ):
        raise OfflineActivationError("CONTACT_ROSTER_NOT_COMPLETE")
    f061_binding_fields = (
        "f061_allocation_id",
        "f061_mode",
        "f061_values",
        "f061_denominator_is_null",
        "f061_denominator",
        "f061_minimum_counts",
        "f061_rounding_rule_id",
        "f061_power_requirement_id",
        "f061_allocation_proposal_sha256",
        "f061_power_review_receipt_sha256",
        "f061_power_review_accepted",
        "f061_allocation_definition_sha256",
    )
    if not any(field in missing for field in f061_binding_fields):
        if (
            bindings.f061_allocation_proposal_sha256
            != f061_allocation_proposal_sha256(bindings)
        ):
            raise OfflineActivationError("F061_PROPOSAL_BINDING_MISMATCH")
        if (
            bindings.f061_allocation_definition_sha256
            != f061_allocation_definition_sha256(bindings)
        ):
            raise OfflineActivationError("F061_DEFINITION_BINDING_MISMATCH")
    return tuple(missing)


def _validate_execution_boundary(boundary: ExecutionBoundary) -> None:
    if type(boundary) is not ExecutionBoundary:
        raise OfflineActivationError("EXECUTION_BOUNDARY_WRONG_TYPE")
    for field, value in asdict(boundary).items():
        if field.endswith("_budget"):
            if type(value) is not int or value != 0:
                raise OfflineActivationError("NONZERO_EXECUTION_BUDGET")
        elif type(value) is not bool or value is not False:
            raise OfflineActivationError("OPERATIONAL_AUTHORITY_SMUGGLED")


def _validate_observations(
    observations: Tuple[ExternalObservationSlots, ...],
) -> None:
    if type(observations) is not tuple or len(observations) != 2:
        raise OfflineActivationError("EXTERNAL_OBSERVATION_ROSTER_INVALID")
    for expected_domain, observation in zip(
        (PHYSIONET_DOMAIN, RETAIL_DOMAIN), observations
    ):
        if type(observation) is not ExternalObservationSlots:
            raise OfflineActivationError("EXTERNAL_OBSERVATION_WRONG_TYPE")
        if type(observation.domain_id) is not str or observation.domain_id != expected_domain:
            raise OfflineActivationError("EXTERNAL_OBSERVATION_DOMAIN_MISMATCH")
        for field, value in asdict(observation).items():
            if field != "domain_id" and value is not None:
                raise OfflineActivationError(
                    "EXTERNAL_OBSERVATION_PRESENT_BEFORE_EXECUTION"
                )


def _validate_operation(operation: OperationSpec, expected: OperationSpec) -> None:
    if type(operation) is not OperationSpec:
        raise OfflineActivationError("OPERATION_WRONG_TYPE")
    tuple_fields = ("administrative_questions", "required_prior_receipts")
    if any(type(getattr(operation, field)) is not tuple for field in tuple_fields):
        raise OfflineActivationError("OPERATION_TUPLE_CARRIER_INVALID")
    if any(
        type(item) is not str
        for field in tuple_fields
        for item in getattr(operation, field)
    ):
        raise OfflineActivationError("OPERATION_TUPLE_ITEM_INVALID")
    string_fields = (
        "operation_id",
        "domain_id",
        "phase",
        "exact_target_derivation",
        "selector_identity",
        "exact_permitted_request_kind",
        "success_predicate",
        "terminal_disposition",
    )
    if any(type(getattr(operation, field)) is not str for field in string_fields):
        raise OfflineActivationError("OPERATION_STRING_TYPE_INVALID")
    if operation.exact_target is not None and type(operation.exact_target) is not str:
        raise OfflineActivationError("OPERATION_TARGET_TYPE_INVALID")
    if (
        operation.matching_admin_operation_id is not None
        and type(operation.matching_admin_operation_id) is not str
    ):
        raise OfflineActivationError("OPERATION_STRING_TYPE_INVALID")
    integer_fields = (
        "global_ordinal",
        "maximum_attempt_count",
        "retry_limit",
        "redirect_limit",
        "address_fallback_limit",
    )
    if any(type(getattr(operation, field)) is not int for field in integer_fields):
        raise OfflineActivationError("OPERATION_INTEGER_TYPE_INVALID")
    boolean_fields = (
        "authentication_permitted",
        "download_permitted",
        "data_opening_permitted",
        "currently_eligible",
    )
    if any(type(getattr(operation, field)) is not bool for field in boolean_fields):
        raise OfflineActivationError("OPERATION_BOOLEAN_TYPE_INVALID")
    _require_sha256(
        operation.operation_identity_sha256,
        "operation.operation_identity_sha256",
    )
    if operation_identity_sha256(operation) != operation.operation_identity_sha256:
        raise OfflineActivationError("OPERATION_IDENTITY_MISMATCH")
    if operation != expected:
        raise OfflineActivationError("OPERATION_ROSTER_DRIFT")


def _population_payload(
    predecessor_set_sha256: str,
    owner_manifest: OwnerManifest,
    definition_bindings: OfflineDefinitionBindings,
) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "package_kind": PACKAGE_KIND,
        "predecessor_set_sha256": predecessor_set_sha256,
        "state_machine": STATE_MACHINE,
        "operation_roster": tuple(asdict(row) for row in EXACT_OPERATION_ROSTER),
        "owner_manifest": asdict(owner_manifest),
        "definition_bindings": asdict(definition_bindings),
        "external_observations": tuple(
            asdict(row) for row in EMPTY_EXTERNAL_OBSERVATIONS
        ),
        "access_log_head_sha256": None,
        "external_review_receipt_sha256": None,
        "external_review_decision": None,
        "external_reviewer_principal_id": None,
        "execution_boundary": asdict(ZERO_EXECUTION_BOUNDARY),
    }


def population_identity_sha256(
    predecessor_set_sha256: str,
    owner_manifest: OwnerManifest,
    definition_bindings: OfflineDefinitionBindings,
) -> str:
    """Hash the exact population that a later external review must bind."""

    _require_sha256(predecessor_set_sha256, "predecessor_set_sha256")
    _validate_owner_manifest(owner_manifest)
    _validate_definition_bindings(definition_bindings)
    return _digest(
        _POPULATION_IDENTITY_DOMAIN,
        _population_payload(
            predecessor_set_sha256,
            owner_manifest,
            definition_bindings,
        ),
    )


def _package_payload(package: OfflinePrecontactActivation) -> Dict[str, Any]:
    value = asdict(package)
    value.pop("package_identity_sha256")
    return value


def _package_identity(package: OfflinePrecontactActivation) -> str:
    return _digest(_PACKAGE_IDENTITY_DOMAIN, _package_payload(package))


def build_offline_precontact_activation(
    predecessor_set_sha256: str,
    owner_manifest: Optional[OwnerManifest] = None,
    definition_bindings: Optional[OfflineDefinitionBindings] = None,
) -> OfflinePrecontactActivation:
    """Build state 0 or externally-reviewable state 1, never reviewed state 2."""

    _require_sha256(predecessor_set_sha256, "predecessor_set_sha256")
    owners = unresolved_owner_manifest() if owner_manifest is None else owner_manifest
    bindings = (
        unresolved_definition_bindings()
        if definition_bindings is None
        else definition_bindings
    )
    owner_missing = _validate_owner_manifest(owners)
    binding_missing = _validate_definition_bindings(bindings)
    state = 1 if not owner_missing and not binding_missing else 0
    population_identity = population_identity_sha256(
        predecessor_set_sha256,
        owners,
        bindings,
    )
    draft = OfflinePrecontactActivation(
        schema_version=SCHEMA_VERSION,
        package_kind=PACKAGE_KIND,
        predecessor_set_sha256=predecessor_set_sha256,
        state_machine=STATE_MACHINE,
        current_state_ordinal=state,
        operation_roster=EXACT_OPERATION_ROSTER,
        owner_manifest=owners,
        definition_bindings=bindings,
        external_observations=EMPTY_EXTERNAL_OBSERVATIONS,
        access_log_head_sha256=None,
        external_review_receipt_sha256=None,
        external_review_decision=None,
        external_reviewer_principal_id=None,
        execution_boundary=ZERO_EXECUTION_BOUNDARY,
        population_identity_sha256=population_identity,
        package_identity_sha256="0" * 64,
    )
    return replace(draft, package_identity_sha256=_package_identity(draft))


def evaluate_offline_admission(
    package: OfflinePrecontactActivation,
) -> Dict[str, Any]:
    """Validate offline population and return HOLD or external-review eligibility."""

    if type(package) is not OfflinePrecontactActivation:
        raise OfflineActivationError("PACKAGE_WRONG_TYPE")
    if (
        type(package.schema_version) is not str
        or type(package.package_kind) is not str
        or package.schema_version != SCHEMA_VERSION
        or package.package_kind != PACKAGE_KIND
    ):
        raise OfflineActivationError("PACKAGE_IDENTITY_FIELDS_INVALID")
    _require_sha256(package.predecessor_set_sha256, "predecessor_set_sha256")
    if (
        type(package.state_machine) is not tuple
        or any(type(state) is not str for state in package.state_machine)
        or package.state_machine != STATE_MACHINE
    ):
        raise OfflineActivationError("STATE_MACHINE_DRIFT")
    if type(package.current_state_ordinal) is not int:
        raise OfflineActivationError("CURRENT_STATE_ORDINAL_INVALID")
    if type(package.operation_roster) is not tuple or len(package.operation_roster) != 4:
        raise OfflineActivationError("OPERATION_ROSTER_INVALID")
    for operation, expected in zip(package.operation_roster, EXACT_OPERATION_ROSTER):
        _validate_operation(operation, expected)
    _validate_execution_boundary(package.execution_boundary)
    _validate_observations(package.external_observations)
    if package.access_log_head_sha256 is not None:
        raise OfflineActivationError("ACCESS_LOG_CREATED_BEFORE_EXECUTION")
    if any(
        value is not None
        for value in (
            package.external_review_receipt_sha256,
            package.external_review_decision,
            package.external_reviewer_principal_id,
        )
    ):
        raise OfflineActivationError("EXTERNAL_REVIEW_METADATA_NOT_ADMISSIBLE_HERE")

    owner_missing = _validate_owner_manifest(package.owner_manifest)
    binding_missing = _validate_definition_bindings(package.definition_bindings)
    expected_population = population_identity_sha256(
        package.predecessor_set_sha256,
        package.owner_manifest,
        package.definition_bindings,
    )
    _require_sha256(package.population_identity_sha256, "population_identity_sha256")
    if package.population_identity_sha256 != expected_population:
        raise OfflineActivationError("POPULATION_IDENTITY_MISMATCH")
    expected_state = 1 if not owner_missing and not binding_missing else 0
    if package.current_state_ordinal != expected_state:
        raise OfflineActivationError("FORWARD_ONLY_STAGE_SKIPPED_OR_REVERSED")
    if package.current_state_ordinal > 1:
        raise OfflineActivationError("PURE_MODULE_CANNOT_ADMIT_EXTERNAL_REVIEW")
    _require_sha256(package.package_identity_sha256, "package_identity_sha256")
    if package.package_identity_sha256 != _package_identity(package):
        raise OfflineActivationError("PACKAGE_IDENTITY_MISMATCH")

    missing = tuple(
        f"owner_manifest.{field}" for field in owner_missing
    ) + tuple(f"definition_bindings.{field}" for field in binding_missing)
    eligible = not missing
    return {
        "decision": (
            OFFLINE_ELIGIBLE_DECISION if eligible else OFFLINE_HOLD_DECISION
        ),
        "current_state": STATE_MACHINE[package.current_state_ordinal],
        "current_state_ordinal": package.current_state_ordinal,
        "missing_offline_fields": list(missing),
        "operation_count": 4,
        "population_identity_sha256": package.population_identity_sha256,
        "package_identity_sha256": package.package_identity_sha256,
        "external_independent_review_required": True,
        "external_review_admitted": False,
        "execution_budget": 0,
        "operational_authority_present": False,
        "admin_contact_authorized": False,
        "data_access_authorized": False,
        "external_observations_present": False,
    }


def canonical_activation_bytes(package: OfflinePrecontactActivation) -> bytes:
    """Return one-line canonical ASCII JSON with exactly one terminal LF."""

    evaluate_offline_admission(package)
    return _canonical_bytes(asdict(package)) + b"\n"


def activation_file_sha256(package: OfflinePrecontactActivation) -> str:
    """Return the ordinary SHA-256 of :func:`canonical_activation_bytes`."""

    return hashlib.sha256(canonical_activation_bytes(package)).hexdigest()


__all__: Tuple[str, ...] = (
    "ADMIN_QUESTIONS",
    "APPEND_ONLY_LOG_SCHEMA_ID",
    "EMPTY_EXTERNAL_OBSERVATIONS",
    "EXACT_OPERATION_ROSTER",
    "ExecutionBoundary",
    "ExternalObservationSlots",
    "F061_ALLOCATION_SCHEMA",
    "F061_ALLOWED_METHOD_ID",
    "F061_ALLOWED_MODES",
    "F061_HAMILTON_ROUNDING_RULE_ID",
    "OFFLINE_ELIGIBLE_DECISION",
    "OFFLINE_HOLD_DECISION",
    "OfflineActivationError",
    "OfflineDefinitionBindings",
    "OfflinePrecontactActivation",
    "OperationSpec",
    "OwnerManifest",
    "PACKAGE_KIND",
    "PHYSIONET_DOMAIN",
    "PHYSIONET_F061_ADAPTER_ID",
    "PHYSIONET_F061_ADAPTER_SHA256",
    "PHYSIONET_SELECTOR_ID",
    "PHYSIONET_URL",
    "RETAIL_DOMAIN",
    "RETAIL_F061_ADAPTER_ID",
    "RETAIL_F061_ADAPTER_SHA256",
    "RETAIL_F061_PROPOSAL_SCHEMA",
    "RETAIL_SELECTOR_ID",
    "RETAIL_URL",
    "SCHEMA_VERSION",
    "STATE_MACHINE",
    "TERMINAL_FAILURE_MAP",
    "ZERO_EXECUTION_BOUNDARY",
    "activation_file_sha256",
    "build_offline_precontact_activation",
    "canonical_activation_bytes",
    "evaluate_offline_admission",
    "f061_allocation_definition_sha256",
    "f061_allocation_proposal_sha256",
    "operation_identity_sha256",
    "population_identity_sha256",
    "physionet_f061_adapter_record",
    "physionet_f061_adapter_sha256",
    "project_shared_policy_to_physionet_f061_proposal",
    "project_shared_policy_to_retail_f061_proposal",
    "retail_f061_adapter_record",
    "retail_f061_adapter_sha256",
    "unresolved_definition_bindings",
    "unresolved_owner_manifest",
)
