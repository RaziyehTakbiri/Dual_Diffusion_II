"""Pure offline contract for the remaining B02/B03/B09 external evidence.

This module defines and validates an intake envelope.  It never authenticates a
person, verifies an external signature, contacts a source, opens data, or grants
operational authority.  A structurally complete envelope is merely eligible
for a separate external independent review.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from typing import Any, Dict, Mapping, Sequence, Tuple

SCHEMA_VERSION = "heterodiff-b02-b03-b09-external-evidence-intake-v1"
CONTRACT_STATE = "INTAKE_CONTRACT_FROZEN_AWAITING_REAL_EXTERNAL_EVIDENCE"
EMPTY_DECISION = "HOLD_REAL_EXTERNAL_EVIDENCE_INCOMPLETE"
COMPLETE_DECISION = "ELIGIBLE_FOR_SEPARATE_EXTERNAL_INDEPENDENT_REVIEW"

_CONTRACT_DOMAIN = b"heterodiff/b02-b03-b09/external-evidence-intake-contract/v1\0"
_RECEIPT_DOMAINS = {
    "principal_acceptance": (
        b"heterodiff/b02-b03-b09/principal-acceptance-receipt/v1\0"
    ),
    "definition_record": (
        b"heterodiff/b02-b03-b09/external-definition-record/v1\0"
    ),
    "evidence_object": b"heterodiff/b02-b03-b09/evidence-object/v1\0",
}
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_IDENTIFIER = re.compile(r"[A-Z0-9][A-Z0-9._:-]{2,127}\Z")
_RFC3339_UTC = re.compile(
    r"(?:19|20)[0-9]{2}-(?:0[1-9]|1[0-2])-"
    r"(?:0[1-9]|[12][0-9]|3[01])T"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\."
    r"[0-9]{9}Z\Z"
)
_EVIDENCE_PATH = re.compile(
    r"research/private_evidence/b02_b03_b09/"
    r"[a-z0-9][a-z0-9_-]{1,63}/[a-z0-9][a-z0-9_.-]{1,127}\Z"
)


class IntakeValidationError(ValueError):
    """Malformed, incomplete, aliased, or authority-expanding intake."""


OWNER_ROLES: Tuple[Tuple[str, str, str], ...] = (
    (
        "ACCOUNTABLE_GOVERNANCE_OWNER",
        "accountable_governance_owner_id",
        "accountable_governance_owner_acceptance_sha256",
    ),
    (
        "LICENSE_PRIVACY_INSTITUTIONAL_APPROVAL_ENDPOINT",
        "license_privacy_institutional_approval_endpoint_id",
        "license_privacy_institutional_approval_endpoint_acceptance_sha256",
    ),
    (
        "RAW_SNAPSHOT_CUSTODIAN",
        "raw_snapshot_custodian_id",
        "raw_snapshot_custodian_acceptance_sha256",
    ),
    (
        "DETERMINISTIC_SPLIT_OPERATOR",
        "deterministic_split_operator_id",
        "deterministic_split_operator_acceptance_sha256",
    ),
    (
        "INDEPENDENT_HELD_OUT_ESCROW_CUSTODIAN",
        "independent_held_out_escrow_custodian_id",
        "independent_held_out_escrow_custodian_acceptance_sha256",
    ),
    (
        "INDEPENDENT_FINAL_OPENING_APPROVER",
        "independent_final_opening_approver_id",
        "independent_final_opening_approver_acceptance_sha256",
    ),
    (
        "KEY_ACL_ACCEPTANCE_AUTHORITY",
        "key_acl_acceptance_authority_id",
        "key_acl_acceptance_authority_acceptance_sha256",
    ),
    (
        "RETENTION_DELETION_OWNER",
        "retention_deletion_owner_id",
        "retention_deletion_owner_acceptance_sha256",
    ),
    (
        "INCIDENT_RESPONSE_OWNER",
        "incident_response_owner_id",
        "incident_response_owner_acceptance_sha256",
    ),
)

UNRESOLVED_DEFINITION_SLOTS: Tuple[Tuple[str, str], ...] = (
    ("physionet_selector_record_sha256", "LOWERCASE_SHA256"),
    ("retail_selector_record_sha256", "LOWERCASE_SHA256"),
    ("contact_target_roster_sha256", "LOWERCASE_SHA256"),
    ("contact_target_count", "EXACT_INTEGER_TWO"),
    ("approval_requirement_roster_sha256", "LOWERCASE_SHA256"),
    ("approval_receipt_validator_roster_sha256", "LOWERCASE_SHA256"),
    ("conflict_of_interest_determination_sha256", "LOWERCASE_SHA256"),
    ("contact_roster_complete", "EXACT_TRUE"),
    ("escrow_control_binding_sha256", "LOWERCASE_SHA256"),
)

RESOLVED_LOCAL_DEFINITIONS = {
    "held_out_material_definition_sha256": (
        "6aa31c23117ee604cf862c8654175f33a7baa5c501a02983e91de4146154fc5d"
    ),
    "final_opening_rule_sha256": (
        "fe0b51906c69930d6c1252491634588b1b08f4a3ec888a9a92bd6c13720c5efd"
    ),
    "append_only_log_schema_sha256": (
        "cf2e70cffd0e9deea4c5884b72489fccbcb0731695f2493fcf2a1f2182274fd3"
    ),
    "f061_allocation_definition_sha256": (
        "6c7beda87ccf1b9b60b0787619fc637eeb3ab34d5f68e09608d46b4dcf11f946"
    ),
    "f061_power_review_receipt_raw_sha256": (
        "906b12b78400cba6bc2b32527a1410c6d42f154bbad0775591d69ada7485668d"
    ),
}

EVIDENCE_OBJECT_ROLES = (
    "PHYSIONET_SELECTOR_RECORD",
    "RETAIL_SELECTOR_RECORD",
    "CONTACT_TARGET_ROSTER",
    "APPROVAL_REQUIREMENT_ROSTER",
    "APPROVAL_RECEIPT_VALIDATOR_ROSTER",
    "CONFLICT_OF_INTEREST_DETERMINATION",
    "ESCROW_CONTROL_BINDING",
    "KEY_MANIFEST",
    "ACL_MANIFEST",
) + tuple(role + "_ACCEPTANCE" for role, _, _ in OWNER_ROLES)

_DEFINITION_ROLE_TO_FIELD = {
    "PHYSIONET_SELECTOR_RECORD": "physionet_selector_record_sha256",
    "RETAIL_SELECTOR_RECORD": "retail_selector_record_sha256",
    "CONTACT_TARGET_ROSTER": "contact_target_roster_sha256",
    "APPROVAL_REQUIREMENT_ROSTER": "approval_requirement_roster_sha256",
    "APPROVAL_RECEIPT_VALIDATOR_ROSTER": (
        "approval_receipt_validator_roster_sha256"
    ),
    "CONFLICT_OF_INTEREST_DETERMINATION": (
        "conflict_of_interest_determination_sha256"
    ),
    "ESCROW_CONTROL_BINDING": "escrow_control_binding_sha256",
}

_DOMAIN_SELECTOR_SPECS = {
    "PHYSIONET_SELECTOR_RECORD": {
        "domain_id": "physionet-challenge-2012",
        "selector_id": (
            "PHYSIONET_CHALLENGE_2012_VERSION_1_0_0_"
            "EXACT_REGISTERED_URL_SELECTOR_V1"
        ),
        "exact_registered_target": (
            "https://physionet.org/content/challenge-2012/1.0.0/"
        ),
    },
    "RETAIL_SELECTOR_RECORD": {
        "domain_id": "online-retail-ii",
        "selector_id": (
            "UCI_DATASET_502_ONLINE_RETAIL_II_EXACT_REGISTERED_URL_SELECTOR_V1"
        ),
        "exact_registered_target": (
            "https://archive.ics.uci.edu/dataset/502/online+retail+ii"
        ),
    },
}

PROHIBITED_AUTHORITY_CLAIMS = (
    "NETWORK_OR_CONTACT",
    "AUTHENTICATION",
    "DOWNLOAD_OR_DATA_ACCESS",
    "SNAPSHOT_OPENING",
    "SPLIT_EXECUTION",
    "ESCROW_ACTIVATION",
    "FINAL_OPENING",
    "SCIENTIFIC_EXECUTION",
    "PUBLICATION_OR_SUBMISSION",
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def content_sha256(domain_name: str, value: object) -> str:
    """Hash a canonical record under an exact domain-separation tag."""

    if type(domain_name) is not str or domain_name not in _RECEIPT_DOMAINS:
        raise IntakeValidationError("UNKNOWN_DIGEST_DOMAIN")
    if type(value) is not dict:
        raise IntakeValidationError("RECORD_MUST_BE_EXACT_DICT")
    return hashlib.sha256(_RECEIPT_DOMAINS[domain_name] + _canonical(value)).hexdigest()


def contract_record() -> Dict[str, Any]:
    """Return the closed-world, reusable intake contract."""

    return {
        "schema_version": SCHEMA_VERSION,
        "purpose": "COLLECT_REAL_EXTERNAL_EVIDENCE_WITHOUT_CREATING_AUTHORITY",
        "owner_roles": [
            {
                "ordinal": ordinal,
                "role_id": role,
                "principal_field": principal_field,
                "acceptance_field": acceptance_field,
                "principal_must_be_distinct_across_all_nine_roles": True,
            }
            for ordinal, (role, principal_field, acceptance_field) in enumerate(
                OWNER_ROLES
            )
        ],
        "owner_acceptance_receipt_schema": {
            "required_field_order": [
                "schema_version",
                "role_id",
                "principal_id",
                "intake_contract_sha256",
                "accepted_scope",
                "acknowledged_prohibitions",
                "conflict_of_interest_determination_sha256",
                "authentication_method_id",
                "authentication_evidence_sha256",
                "issued_time_rfc3339_utc",
                "acceptance",
            ],
            "schema_version": "heterodiff-principal-role-acceptance-v1",
            "accepted_scope_rule": "EXACT_ROLE_SPECIFIC_SCOPE_NO_DELEGATION_BY_THIS_RECEIPT",
            "acknowledged_prohibitions": list(PROHIBITED_AUTHORITY_CLAIMS),
            "acceptance_must_be_exact_true": True,
            "authentication_must_be_external_and_separately_verifiable": True,
            "canonical_digest_domain": "principal_acceptance",
        },
        "definition_slots": [
            {"ordinal": ordinal, "field": field, "exact_type": exact_type}
            for ordinal, (field, exact_type) in enumerate(
                UNRESOLVED_DEFINITION_SLOTS
            )
        ],
        "definition_record_requirements": {
            "selector_records": {
                "required_fields": [
                    "schema_version",
                    "domain_id",
                    "selector_id",
                    "exact_registered_target",
                    "target_derivation",
                    "version_or_revision_rule",
                    "immutable_archive_locator_rule",
                    "required_metadata_fields",
                    "exclusion_or_substitution_permitted",
                    "accountable_owner_principal_id",
                ],
                "exact_domains": [
                    "physionet-challenge-2012",
                    "online-retail-ii",
                ],
                "exclusion_or_substitution_permitted": False,
            },
            "contact_target_roster": {
                "required_fields": [
                    "schema_version",
                    "targets",
                    "declared_count",
                    "complete",
                    "accountable_owner_principal_id",
                ],
                "target_required_fields": [
                    "ordinal",
                    "domain_id",
                    "operation_id",
                    "contact_target_id",
                    "contact_mechanism_id",
                    "exact_destination_sha256",
                    "permitted_questions_sha256",
                ],
                "required_admin_operations": [
                    "PHYSIONET_ADMIN_METADATA_LICENSE_GOVERNANCE",
                    "RETAIL_ADMIN_METADATA_LICENSE_GOVERNANCE",
                ],
                "count_equals_exact_target_array_length": True,
                "exact_target_count": 2,
                "additional_or_fallback_targets_permitted": False,
                "complete_must_be_exact_true": True,
            },
            "approval_requirement_roster": {
                "required_fields": [
                    "schema_version",
                    "domains",
                    "accountable_endpoint_principal_id",
                ],
                "domain_required_fields": [
                    "domain_id",
                    "determination",
                    "requirements",
                    "source_evidence_sha256",
                ],
                "determination_enum": [
                    "REQUIREMENTS_ENUMERATED",
                    "NO_APPROVAL_REQUIRED_WITH_SIGNED_DETERMINATION",
                ],
                "unknown_or_silent_is_not_no_approval": True,
            },
            "approval_receipt_validator_roster": {
                "required_fields": [
                    "schema_version",
                    "validators",
                    "all_approval_requirements_covered",
                ],
                "validator_required_fields": [
                    "requirement_id",
                    "validator_principal_id",
                    "validation_method_id",
                    "accepted_issuer_roster_sha256",
                    "revocation_check_rule",
                ],
                "complete_coverage_must_be_exact_true": True,
            },
            "conflict_of_interest_determination": {
                "required_fields": [
                    "schema_version",
                    "nine_role_assignments_sha256",
                    "relationships_examined",
                    "conflicts",
                    "determination",
                    "determiner_principal_id",
                    "authentication_evidence_sha256",
                ],
                "determination": (
                    "NO_PROHIBITED_ROLE_ALIAS_AND_NO_IDENTIFIED_CONFLICT_V1"
                ),
                "all_nine_pairwise_distinct_required": True,
                "managed_or_unmanaged_conflict_permitted_in_v1": False,
            },
            "escrow_control_binding": {
                "required_fields": [
                    "schema_version",
                    "escrow_control_id",
                    "held_out_material_definition_sha256",
                    "final_opening_rule_sha256",
                    "escrow_custodian_principal_id",
                    "final_opening_approver_principal_id",
                    "key_acl_acceptance_authority_principal_id",
                    "raw_snapshot_custodian_principal_id",
                    "deterministic_split_operator_principal_id",
                    "retention_deletion_owner_principal_id",
                    "incident_response_owner_principal_id",
                    "key_manifest_sha256",
                    "acl_manifest_sha256",
                    "storage_boundary_sha256",
                    "retention_deletion_policy_sha256",
                    "incident_response_policy_sha256",
                    "activation_claimed",
                ],
                "activation_claimed_must_be_exact_false_at_intake": True,
                "key_manifest_required_fields": [
                    "schema_version",
                    "key_id",
                    "algorithm_id",
                    "public_fingerprint_sha256",
                    "accepted_by_principal_id",
                    "custody_principal_id",
                    "private_key_location_disclosed_in_public_packet",
                    "rotation_or_revocation_rule_sha256",
                ],
                "private_key_location_disclosed_in_public_packet": False,
                "acl_manifest_required_fields": [
                    "schema_version",
                    "entries",
                ],
                "acl_entry_required_fields": [
                    "resource_id",
                    "principal_id",
                    "permission_enum",
                    "effective_time_rfc3339_utc",
                    "revocation_rule_sha256",
                ],
            },
        },
        "evidence_manifest_schema": {
            "required_roles": list(EVIDENCE_OBJECT_ROLES),
            "raw_evidence_bundle": {
                "exact_mapping_keys": list(EVIDENCE_OBJECT_ROLES),
                "value_type": "EXACT_BUILTIN_BYTES",
                "maximum_bytes_per_object": 1000000,
                "encoding": "ASCII_CANONICAL_JSON_WITH_ONE_TERMINAL_LF",
                "duplicate_keys_permitted": False,
                "all_raw_sha256_and_byte_counts_recomputed": True,
                "all_payload_digests_and_crosslinks_semantically_replayed": True,
            },
            "evidence_object_envelope_field_order": [
                "schema_version",
                "role",
                "payload",
                "authentication",
                "verification_receipt_sha256",
            ],
            "evidence_object_authentication_field_order": [
                "external_verifier_principal_id",
                "method_id",
                "evidence_sha256",
                "verified",
            ],
            "item_field_order": [
                "ordinal",
                "role",
                "private_path",
                "byte_count",
                "raw_sha256",
                "media_type",
                "contains_personal_or_sensitive_information",
                "external_authentication_verified",
                "verification_receipt_sha256",
            ],
            "private_path_pattern": _EVIDENCE_PATH.pattern,
            "path_is_locator_not_authority": True,
            "public_packet_must_not_embed_secrets_or_raw_personal_data": True,
        },
        "population_rules": {
            "all_nine_principals_pairwise_distinct": True,
            "all_nine_acceptance_receipts_required": True,
            "all_nine_definition_slots_required": True,
            "evidence_roles_exactly_once": True,
            "principal_ids_are_opaque_not_names_or_email_addresses": True,
            "all_external_authentication_must_be_independently_verified": True,
            "structural_completion_grants_authority": False,
            "separate_external_independent_review_required": True,
            "separate_fresh_exact_operation_authority_required": True,
        },
        "resolved_local_definitions": dict(RESOLVED_LOCAL_DEFINITIONS),
        "authority_boundary": {
            "prohibited_claims": list(PROHIBITED_AUTHORITY_CLAIMS),
            "all_current_budgets": {
                name: 0
                for name in (
                    "admin_contact",
                    "data_access",
                    "snapshot_open",
                    "split_execution",
                    "escrow_activation",
                    "final_opening",
                    "scientific_execution",
                )
            },
            "network_or_contact_authorized": False,
            "data_access_authorized": False,
            "scientific_execution_authorized": False,
        },
    }


def intake_contract_sha256() -> str:
    return hashlib.sha256(_CONTRACT_DOMAIN + _canonical(contract_record())).hexdigest()


def empty_intake_instance() -> Dict[str, Any]:
    """Return an inert population envelope containing no real identity or claim."""

    principals: Dict[str, Any] = {}
    acceptances: Dict[str, Any] = {}
    for _role, principal_field, acceptance_field in OWNER_ROLES:
        principals[principal_field] = None
        acceptances[acceptance_field] = None
    return {
        "schema_version": SCHEMA_VERSION,
        "intake_contract_sha256": intake_contract_sha256(),
        "principals": principals,
        "acceptance_receipts": acceptances,
        "definition_bindings": {
            field: None for field, _exact_type in UNRESOLVED_DEFINITION_SLOTS
        },
        "evidence_manifest": [],
        "external_independent_review_receipt_sha256": None,
        "authority": {
            "network_or_contact": False,
            "authentication": False,
            "download_or_data_access": False,
            "snapshot_open": False,
            "split_execution": False,
            "escrow_activation": False,
            "final_opening": False,
            "scientific_execution": False,
            "publication_or_submission": False,
        },
        "attempt_budgets": {
            "admin_contact": 0,
            "data_access": 0,
            "snapshot_open": 0,
            "split_execution": 0,
            "escrow_activation": 0,
            "final_opening": 0,
            "scientific_execution": 0,
        },
        "tracker_or_ledger_edited": False,
        "blockers_closed": [],
    }


def _exact_mapping(value: object, expected_keys: Sequence[str], label: str) -> Mapping[str, Any]:
    if type(value) is not dict or tuple(value) != tuple(expected_keys):
        raise IntakeValidationError(label + "_CLOSED_WORLD_MAPPING_MISMATCH")
    return value


def _require_sha(value: object, label: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise IntakeValidationError(label + "_INVALID_SHA256")
    return value


def _require_identifier(value: object, label: str) -> str:
    if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
        raise IntakeValidationError(label + "_INVALID_OPAQUE_IDENTIFIER")
    if "@" in value or " " in value:
        raise IntakeValidationError(label + "_PERSONAL_IDENTIFIER_FORBIDDEN")
    return value


def _require_rfc3339_utc(value: object, label: str) -> str:
    if type(value) is not str or _RFC3339_UTC.fullmatch(value) is None:
        raise IntakeValidationError(label + "_INVALID_RFC3339_UTC")
    try:
        date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
    except ValueError as exc:
        raise IntakeValidationError(label + "_INVALID_GREGORIAN_DATE") from exc
    return value


def _require_exact(value: object, expected: object, label: str) -> None:
    """Require recursive built-in type identity and exact value equality."""

    if type(value) is not type(expected):
        raise IntakeValidationError(label + "_EXACT_TYPE_MISMATCH")
    if type(expected) is dict:
        if tuple(value) != tuple(expected):
            raise IntakeValidationError(label + "_KEY_ORDER_MISMATCH")
        for key in expected:
            _require_exact(value[key], expected[key], label + "." + key)
    elif type(expected) is list:
        if len(value) != len(expected):
            raise IntakeValidationError(label + "_LIST_LENGTH_MISMATCH")
        for ordinal, (actual_item, expected_item) in enumerate(zip(value, expected)):
            _require_exact(actual_item, expected_item, f"{label}[{ordinal}]")
    elif value != expected:
        raise IntakeValidationError(label + "_VALUE_MISMATCH")


def _canonical_mapping(
    value: object, expected_keys: Sequence[str], label: str,
) -> Mapping[str, Any]:
    return _exact_mapping(value, tuple(sorted(expected_keys)), label)


def _parse_evidence_bytes(raw: object, label: str) -> Dict[str, Any]:
    if type(raw) is not bytes or not raw or len(raw) > 1_000_000:
        raise IntakeValidationError(label + "_RAW_BYTES_INVALID")

    def reject_duplicates(pairs: list) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise IntakeValidationError(label + "_DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    try:
        value = json.loads(
            raw.decode("ascii"), object_pairs_hook=reject_duplicates
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntakeValidationError(label + "_NONCANONICAL_JSON") from exc
    if type(value) is not dict or raw != _canonical(value) + b"\n":
        raise IntakeValidationError(label + "_NONCANONICAL_JSON")
    return value


def _payload_sha256(role: str, payload: Dict[str, Any]) -> str:
    if role.endswith("_ACCEPTANCE"):
        return content_sha256("principal_acceptance", payload)
    return content_sha256("definition_record", {"payload": payload, "role": role})


def _verification_receipt_sha256(
    role: str, payload: Dict[str, Any], authentication: Dict[str, Any],
) -> str:
    return content_sha256(
        "evidence_object",
        {
            "authentication": authentication,
            "payload_sha256": _payload_sha256(role, payload),
            "role": role,
        },
    )


def evidence_object_bytes(
    role: str, payload: Dict[str, Any], authentication: Dict[str, Any],
) -> bytes:
    """Build canonical raw bytes for one future externally verified object."""

    if type(role) is not str or role not in EVIDENCE_OBJECT_ROLES:
        raise IntakeValidationError("EVIDENCE_ROLE_INVALID")
    if type(payload) is not dict or type(authentication) is not dict:
        raise IntakeValidationError("EVIDENCE_PAYLOAD_OR_AUTH_INVALID")
    record = {
        "schema_version": "heterodiff-external-evidence-object-v1",
        "role": role,
        "payload": payload,
        "authentication": authentication,
        "verification_receipt_sha256": _verification_receipt_sha256(
            role, payload, authentication
        ),
    }
    return _canonical(record) + b"\n"


def _validate_envelope(
    role: str, raw: bytes, principal_ids: Sequence[str],
) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    record = _parse_evidence_bytes(raw, role)
    _canonical_mapping(
        record,
        (
            "schema_version", "role", "payload", "authentication",
            "verification_receipt_sha256",
        ),
        role + ".envelope",
    )
    _require_exact(
        record["schema_version"],
        "heterodiff-external-evidence-object-v1",
        role + ".schema_version",
    )
    _require_exact(record["role"], role, role + ".role")
    if type(record["payload"]) is not dict:
        raise IntakeValidationError(role + "_PAYLOAD_INVALID")
    authentication = _canonical_mapping(
        record["authentication"],
        (
            "external_verifier_principal_id", "method_id", "evidence_sha256",
            "verified",
        ),
        role + ".authentication",
    )
    verifier = _require_identifier(
        authentication["external_verifier_principal_id"],
        role + ".external_verifier_principal_id",
    )
    if verifier in principal_ids:
        raise IntakeValidationError(role + "_EXTERNAL_VERIFIER_ROLE_ALIAS")
    _require_identifier(authentication["method_id"], role + ".method_id")
    _require_sha(authentication["evidence_sha256"], role + ".evidence_sha256")
    if authentication["verified"] is not True:
        raise IntakeValidationError(role + "_AUTHENTICATION_NOT_VERIFIED")
    expected_receipt = _verification_receipt_sha256(
        role, record["payload"], dict(authentication)
    )
    _require_exact(
        record["verification_receipt_sha256"],
        expected_receipt,
        role + ".verification_receipt_sha256",
    )
    return record["payload"], dict(authentication), expected_receipt


def _principal_assignments(principals: Mapping[str, Any]) -> list:
    return [
        {"principal_id": principals[principal_field], "role_id": role}
        for role, principal_field, _acceptance_field in OWNER_ROLES
    ]


def _role_assignments_sha256(principals: Mapping[str, Any]) -> str:
    return content_sha256(
        "definition_record", {"role_assignments": _principal_assignments(principals)}
    )


def _relationship_roster() -> list:
    roles = [role for role, _principal, _acceptance in OWNER_ROLES]
    return [
        roles[left] + "|" + roles[right]
        for left in range(len(roles))
        for right in range(left + 1, len(roles))
    ]


def _validate_acceptance_payload(
    role: str,
    payload: Mapping[str, Any],
    authentication: Mapping[str, Any],
    principals: Mapping[str, Any],
    definitions: Mapping[str, Any],
) -> None:
    fields = tuple(
        contract_record()["owner_acceptance_receipt_schema"]["required_field_order"]
    )
    value = _canonical_mapping(payload, fields, role + ".payload")
    base_role = role[:-len("_ACCEPTANCE")]
    spec = next(item for item in OWNER_ROLES if item[0] == base_role)
    principal_id = principals[spec[1]]
    _require_exact(
        value["schema_version"],
        "heterodiff-principal-role-acceptance-v1",
        role + ".payload.schema_version",
    )
    _require_exact(value["role_id"], base_role, role + ".payload.role_id")
    _require_exact(
        value["principal_id"], principal_id, role + ".payload.principal_id"
    )
    _require_exact(
        value["intake_contract_sha256"],
        intake_contract_sha256(),
        role + ".payload.intake_contract_sha256",
    )
    _require_exact(
        value["accepted_scope"], base_role + "_SCOPE_V1", role + ".accepted_scope"
    )
    _require_exact(
        value["acknowledged_prohibitions"],
        list(PROHIBITED_AUTHORITY_CLAIMS),
        role + ".acknowledged_prohibitions",
    )
    _require_exact(
        value["conflict_of_interest_determination_sha256"],
        definitions["conflict_of_interest_determination_sha256"],
        role + ".conflict_of_interest_determination_sha256",
    )
    _require_exact(
        value["authentication_method_id"],
        authentication["method_id"],
        role + ".authentication_method_id",
    )
    _require_exact(
        value["authentication_evidence_sha256"],
        authentication["evidence_sha256"],
        role + ".authentication_evidence_sha256",
    )
    _require_rfc3339_utc(
        value["issued_time_rfc3339_utc"], role + ".issued_time_rfc3339_utc"
    )
    if value["acceptance"] is not True:
        raise IntakeValidationError(role + "_ACCEPTANCE_NOT_TRUE")


def _validate_selector_payload(
    role: str, payload: Mapping[str, Any], principals: Mapping[str, Any],
) -> None:
    fields = contract_record()["definition_record_requirements"]["selector_records"][
        "required_fields"
    ]
    value = _canonical_mapping(payload, fields, role + ".payload")
    expected = _DOMAIN_SELECTOR_SPECS[role]
    _require_exact(
        value["schema_version"],
        "heterodiff-two-domain-acquisition-selector-record-v1",
        role + ".schema_version",
    )
    for field in ("domain_id", "selector_id", "exact_registered_target"):
        _require_exact(value[field], expected[field], role + "." + field)
    _require_exact(
        value["target_derivation"],
        "LITERAL_REGISTERED_SOURCE_URL",
        role + ".target_derivation",
    )
    _require_exact(
        value["version_or_revision_rule"],
        "ONE_CANONICAL_IMMUTABLE_VERSION_OR_REVISION_REQUIRED",
        role + ".version_or_revision_rule",
    )
    _require_exact(
        value["immutable_archive_locator_rule"],
        "EXACTLY_ONE_LOCATOR_SHA256_AND_BYTE_COUNT_REQUIRED",
        role + ".immutable_archive_locator_rule",
    )
    _require_exact(
        value["required_metadata_fields"],
        ["VERSION_OR_REVISION", "ARCHIVE_LOCATOR", "SHA256", "BYTE_COUNT"],
        role + ".required_metadata_fields",
    )
    if value["exclusion_or_substitution_permitted"] is not False:
        raise IntakeValidationError(role + "_EXCLUSION_OR_SUBSTITUTION_FORBIDDEN")
    _require_exact(
        value["accountable_owner_principal_id"],
        principals["accountable_governance_owner_id"],
        role + ".accountable_owner_principal_id",
    )


def _validate_contact_payload(
    payload: Mapping[str, Any],
    principals: Mapping[str, Any],
    definitions: Mapping[str, Any],
) -> None:
    requirements = contract_record()["definition_record_requirements"][
        "contact_target_roster"
    ]
    value = _canonical_mapping(
        payload, requirements["required_fields"], "CONTACT_TARGET_ROSTER.payload"
    )
    _require_exact(
        value["schema_version"],
        "heterodiff-contact-target-roster-v1",
        "CONTACT_TARGET_ROSTER.schema_version",
    )
    _require_exact(
        value["accountable_owner_principal_id"],
        principals["accountable_governance_owner_id"],
        "CONTACT_TARGET_ROSTER.accountable_owner_principal_id",
    )
    if type(value["targets"]) is not list or len(value["targets"]) != 2:
        raise IntakeValidationError("CONTACT_TARGET_ROSTER_TARGETS_INVALID")
    if type(value["declared_count"]) is not int or value["declared_count"] != 2:
        raise IntakeValidationError("CONTACT_TARGET_ROSTER_COUNT_INVALID")
    if value["complete"] is not True:
        raise IntakeValidationError("CONTACT_TARGET_ROSTER_NOT_COMPLETE")
    _require_exact(
        definitions["contact_target_count"], 2, "definition.contact_target_count"
    )
    if definitions["contact_roster_complete"] is not True:
        raise IntakeValidationError("DEFINITION_CONTACT_ROSTER_NOT_COMPLETE")
    specs = (
        (
            "physionet-challenge-2012",
            "PHYSIONET_ADMIN_METADATA_LICENSE_GOVERNANCE",
            _DOMAIN_SELECTOR_SPECS["PHYSIONET_SELECTOR_RECORD"][
                "exact_registered_target"
            ],
        ),
        (
            "online-retail-ii",
            "RETAIL_ADMIN_METADATA_LICENSE_GOVERNANCE",
            _DOMAIN_SELECTOR_SPECS["RETAIL_SELECTOR_RECORD"][
                "exact_registered_target"
            ],
        ),
    )
    target_fields = requirements["target_required_fields"]
    target_ids = []
    for ordinal, (target, (domain, operation, url)) in enumerate(
        zip(value["targets"], specs)
    ):
        item = _canonical_mapping(
            target, target_fields, f"CONTACT_TARGET_ROSTER.targets[{ordinal}]"
        )
        if type(item["ordinal"]) is not int or item["ordinal"] != ordinal:
            raise IntakeValidationError("CONTACT_TARGET_ORDINAL_INVALID")
        _require_exact(item["domain_id"], domain, "contact.domain_id")
        _require_exact(item["operation_id"], operation, "contact.operation_id")
        target_ids.append(
            _require_identifier(item["contact_target_id"], "contact_target_id")
        )
        _require_identifier(item["contact_mechanism_id"], "contact_mechanism_id")
        _require_exact(
            item["exact_destination_sha256"],
            hashlib.sha256(url.encode("ascii")).hexdigest(),
            "contact.exact_destination_sha256",
        )
        _require_sha(item["permitted_questions_sha256"], "permitted_questions")
    if len(set(target_ids)) != 2:
        raise IntakeValidationError("CONTACT_TARGET_ALIAS_FORBIDDEN")


def _validate_approval_requirements(
    payload: Mapping[str, Any], principals: Mapping[str, Any],
) -> Dict[str, Dict[str, Any]]:
    spec = contract_record()["definition_record_requirements"][
        "approval_requirement_roster"
    ]
    value = _canonical_mapping(
        payload, spec["required_fields"], "APPROVAL_REQUIREMENT_ROSTER.payload"
    )
    _require_exact(
        value["schema_version"],
        "heterodiff-approval-requirement-roster-v1",
        "approval_requirements.schema_version",
    )
    _require_exact(
        value["accountable_endpoint_principal_id"],
        principals["license_privacy_institutional_approval_endpoint_id"],
        "approval_requirements.accountable_endpoint",
    )
    if type(value["domains"]) is not list or len(value["domains"]) != 2:
        raise IntakeValidationError("APPROVAL_DOMAIN_ROSTER_INVALID")
    expected_domains = ("physionet-challenge-2012", "online-retail-ii")
    requirements: Dict[str, Dict[str, Any]] = {}
    for ordinal, (item, expected_domain) in enumerate(zip(value["domains"], expected_domains)):
        domain = _canonical_mapping(
            item, spec["domain_required_fields"], f"approval.domains[{ordinal}]"
        )
        _require_exact(domain["domain_id"], expected_domain, "approval.domain_id")
        if type(domain["determination"]) is not str or domain["determination"] not in spec[
            "determination_enum"
        ]:
            raise IntakeValidationError("APPROVAL_DETERMINATION_INVALID")
        _require_sha(domain["source_evidence_sha256"], "approval.source_evidence")
        if type(domain["requirements"]) is not list:
            raise IntakeValidationError("APPROVAL_REQUIREMENTS_INVALID")
        if (
            domain["determination"] == "REQUIREMENTS_ENUMERATED"
            and not domain["requirements"]
        ):
            raise IntakeValidationError("ENUMERATED_APPROVALS_EMPTY")
        if (
            domain["determination"]
            == "NO_APPROVAL_REQUIRED_WITH_SIGNED_DETERMINATION"
            and domain["requirements"]
        ):
            raise IntakeValidationError("NO_APPROVAL_WITH_REQUIREMENTS_CONTRADICTION")
        for requirement in domain["requirements"]:
            record = _canonical_mapping(
                requirement,
                (
                    "requirement_id", "approval_type_id", "issuer_id",
                    "required_before_phase", "receipt_schema_sha256",
                ),
                "approval.requirement",
            )
            requirement_id = _require_identifier(
                record["requirement_id"], "approval.requirement_id"
            )
            if requirement_id in requirements:
                raise IntakeValidationError("DUPLICATE_APPROVAL_REQUIREMENT")
            _require_identifier(record["approval_type_id"], "approval.approval_type")
            _require_identifier(record["issuer_id"], "approval.issuer_id")
            _require_exact(
                record["required_before_phase"], "DATA", "approval.required_phase"
            )
            _require_sha(record["receipt_schema_sha256"], "approval.receipt_schema")
            requirements[requirement_id] = dict(record)
    return requirements


def _validate_approval_validators(
    payload: Mapping[str, Any],
    approval_requirements: Mapping[str, Dict[str, Any]],
    principal_ids: Sequence[str],
) -> None:
    spec = contract_record()["definition_record_requirements"][
        "approval_receipt_validator_roster"
    ]
    value = _canonical_mapping(
        payload, spec["required_fields"], "APPROVAL_VALIDATOR_ROSTER.payload"
    )
    _require_exact(
        value["schema_version"],
        "heterodiff-approval-receipt-validator-roster-v1",
        "approval_validators.schema_version",
    )
    if value["all_approval_requirements_covered"] is not True:
        raise IntakeValidationError("APPROVAL_VALIDATOR_COVERAGE_NOT_COMPLETE")
    if type(value["validators"]) is not list:
        raise IntakeValidationError("APPROVAL_VALIDATOR_ROSTER_INVALID")
    seen = []
    for item in value["validators"]:
        record = _canonical_mapping(
            item, spec["validator_required_fields"], "approval.validator"
        )
        requirement_id = _require_identifier(
            record["requirement_id"], "validator.requirement_id"
        )
        if requirement_id not in approval_requirements or requirement_id in seen:
            raise IntakeValidationError("VALIDATOR_REQUIREMENT_COVERAGE_INVALID")
        seen.append(requirement_id)
        validator_id = _require_identifier(
            record["validator_principal_id"], "validator.principal_id"
        )
        if validator_id in principal_ids:
            raise IntakeValidationError("APPROVAL_VALIDATOR_ROLE_ALIAS")
        _require_identifier(record["validation_method_id"], "validation_method")
        expected_issuer = content_sha256(
            "definition_record",
            {
                "accepted_issuer_ids": [
                    approval_requirements[requirement_id]["issuer_id"]
                ],
                "requirement_id": requirement_id,
            },
        )
        _require_exact(
            record["accepted_issuer_roster_sha256"],
            expected_issuer,
            "validator.accepted_issuer_roster",
        )
        _require_sha(record["revocation_check_rule"], "validator.revocation_rule")
    if set(seen) != set(approval_requirements) or len(seen) != len(
        approval_requirements
    ):
        raise IntakeValidationError("VALIDATOR_REQUIREMENT_COVERAGE_INVALID")


def _validate_coi_payload(
    payload: Mapping[str, Any],
    principals: Mapping[str, Any],
    principal_ids: Sequence[str],
) -> None:
    spec = contract_record()["definition_record_requirements"][
        "conflict_of_interest_determination"
    ]
    value = _canonical_mapping(
        payload, spec["required_fields"], "COI_DETERMINATION.payload"
    )
    _require_exact(
        value["schema_version"],
        "heterodiff-nine-role-conflict-of-interest-determination-v1",
        "coi.schema_version",
    )
    _require_exact(
        value["nine_role_assignments_sha256"],
        _role_assignments_sha256(principals),
        "coi.nine_role_assignments_sha256",
    )
    _require_exact(
        value["relationships_examined"],
        _relationship_roster(),
        "coi.relationships_examined",
    )
    _require_exact(value["conflicts"], [], "coi.conflicts")
    _require_exact(
        value["determination"],
        "NO_PROHIBITED_ROLE_ALIAS_AND_NO_IDENTIFIED_CONFLICT_V1",
        "coi.determination",
    )
    determiner = _require_identifier(
        value["determiner_principal_id"], "coi.determiner_principal_id"
    )
    if determiner in principal_ids:
        raise IntakeValidationError("COI_DETERMINER_ROLE_ALIAS")
    _require_sha(value["authentication_evidence_sha256"], "coi.authentication")


def _validate_key_payload(
    payload: Mapping[str, Any], principals: Mapping[str, Any],
) -> None:
    fields = contract_record()["definition_record_requirements"][
        "escrow_control_binding"
    ]["key_manifest_required_fields"]
    value = _canonical_mapping(payload, fields, "KEY_MANIFEST.payload")
    _require_exact(
        value["schema_version"],
        "heterodiff-held-out-key-manifest-v1",
        "key.schema_version",
    )
    _require_identifier(value["key_id"], "key.key_id")
    _require_identifier(value["algorithm_id"], "key.algorithm_id")
    _require_sha(value["public_fingerprint_sha256"], "key.fingerprint")
    _require_exact(
        value["accepted_by_principal_id"],
        principals["key_acl_acceptance_authority_id"],
        "key.accepted_by_principal_id",
    )
    _require_exact(
        value["custody_principal_id"],
        principals["independent_held_out_escrow_custodian_id"],
        "key.custody_principal_id",
    )
    if value["private_key_location_disclosed_in_public_packet"] is not False:
        raise IntakeValidationError("PRIVATE_KEY_LOCATION_DISCLOSED")
    _require_sha(value["rotation_or_revocation_rule_sha256"], "key.rotation")


def _validate_acl_payload(
    payload: Mapping[str, Any], principals: Mapping[str, Any],
) -> None:
    spec = contract_record()["definition_record_requirements"][
        "escrow_control_binding"
    ]
    value = _canonical_mapping(
        payload, spec["acl_manifest_required_fields"], "ACL_MANIFEST.payload"
    )
    _require_exact(
        value["schema_version"],
        "heterodiff-held-out-acl-manifest-v1",
        "acl.schema_version",
    )
    if type(value["entries"]) is not list or len(value["entries"]) != 3:
        raise IntakeValidationError("ACL_ENTRY_ROSTER_INVALID")
    expected = (
        (
            principals["independent_held_out_escrow_custodian_id"],
            "CUSTODY_CIPHERTEXT_NO_OPEN",
        ),
        (
            principals["independent_final_opening_approver_id"],
            "APPROVE_OPEN_NO_KEY_CUSTODY",
        ),
        (
            principals["key_acl_acceptance_authority_id"],
            "ACCEPT_KEY_AND_ACL_NO_DATA_OPEN",
        ),
    )
    for ordinal, (entry, (principal_id, permission)) in enumerate(
        zip(value["entries"], expected)
    ):
        item = _canonical_mapping(
            entry, spec["acl_entry_required_fields"], f"acl.entries[{ordinal}]"
        )
        _require_exact(
            item["resource_id"],
            "TWO-DOMAIN-HELD-OUT-ESCROW",
            "acl.resource_id",
        )
        _require_exact(item["principal_id"], principal_id, "acl.principal_id")
        _require_exact(item["permission_enum"], permission, "acl.permission")
        _require_rfc3339_utc(
            item["effective_time_rfc3339_utc"], "acl.effective_time_rfc3339_utc"
        )
        _require_sha(item["revocation_rule_sha256"], "acl.revocation_rule")


def _validate_escrow_payload(
    payload: Mapping[str, Any],
    principals: Mapping[str, Any],
    key_sha256: str,
    acl_sha256: str,
) -> None:
    fields = contract_record()["definition_record_requirements"][
        "escrow_control_binding"
    ]["required_fields"]
    value = _canonical_mapping(payload, fields, "ESCROW_CONTROL_BINDING.payload")
    _require_exact(
        value["schema_version"],
        "heterodiff-held-out-escrow-control-binding-v1",
        "escrow.schema_version",
    )
    _require_exact(
        value["escrow_control_id"],
        "INDEPENDENT_HELD_OUT_ESCROW_LEAST_PRIVILEGE_ACL_V1",
        "escrow.control_id",
    )
    _require_exact(
        value["held_out_material_definition_sha256"],
        RESOLVED_LOCAL_DEFINITIONS["held_out_material_definition_sha256"],
        "escrow.held_out_definition",
    )
    _require_exact(
        value["final_opening_rule_sha256"],
        RESOLVED_LOCAL_DEFINITIONS["final_opening_rule_sha256"],
        "escrow.final_opening_rule",
    )
    principal_links = {
        "escrow_custodian_principal_id": (
            "independent_held_out_escrow_custodian_id"
        ),
        "final_opening_approver_principal_id": (
            "independent_final_opening_approver_id"
        ),
        "key_acl_acceptance_authority_principal_id": (
            "key_acl_acceptance_authority_id"
        ),
        "raw_snapshot_custodian_principal_id": "raw_snapshot_custodian_id",
        "deterministic_split_operator_principal_id": (
            "deterministic_split_operator_id"
        ),
        "retention_deletion_owner_principal_id": "retention_deletion_owner_id",
        "incident_response_owner_principal_id": "incident_response_owner_id",
    }
    for escrow_field, principal_field in principal_links.items():
        _require_exact(
            value[escrow_field], principals[principal_field], "escrow." + escrow_field
        )
    _require_exact(value["key_manifest_sha256"], key_sha256, "escrow.key_manifest")
    _require_exact(value["acl_manifest_sha256"], acl_sha256, "escrow.acl_manifest")
    for field in (
        "storage_boundary_sha256", "retention_deletion_policy_sha256",
        "incident_response_policy_sha256",
    ):
        _require_sha(value[field], "escrow." + field)
    if value["activation_claimed"] is not False:
        raise IntakeValidationError("ESCROW_ACTIVATION_CLAIM_FORBIDDEN")


def _replay_evidence_bundle(
    instance: Mapping[str, Any], evidence_objects: object,
) -> None:
    if type(evidence_objects) is not dict or tuple(evidence_objects) != (
        EVIDENCE_OBJECT_ROLES
    ):
        raise IntakeValidationError("RAW_EVIDENCE_BUNDLE_ROLE_MISMATCH")
    principals = instance["principals"]
    definitions = instance["definition_bindings"]
    principal_ids = list(principals.values())
    manifest = instance["evidence_manifest"]
    payloads: Dict[str, Dict[str, Any]] = {}
    authentications: Dict[str, Dict[str, Any]] = {}
    for ordinal, role in enumerate(EVIDENCE_OBJECT_ROLES):
        raw = evidence_objects[role]
        payload, authentication, verification_receipt = _validate_envelope(
            role, raw, principal_ids
        )
        item = manifest[ordinal]
        _require_exact(item["role"], role, role + ".manifest.role")
        if type(raw) is not bytes:
            raise IntakeValidationError(role + "_RAW_BYTES_TYPE_INVALID")
        if type(item["byte_count"]) is not int or item["byte_count"] != len(raw):
            raise IntakeValidationError(role + "_MANIFEST_BYTE_COUNT_MISMATCH")
        _require_exact(
            item["raw_sha256"],
            hashlib.sha256(raw).hexdigest(),
            role + ".manifest.raw_sha256",
        )
        _require_exact(
            item["verification_receipt_sha256"],
            verification_receipt,
            role + ".manifest.verification_receipt",
        )
        payloads[role] = payload
        authentications[role] = authentication
    for role, principal_field, acceptance_field in OWNER_ROLES:
        evidence_role = role + "_ACCEPTANCE"
        _validate_acceptance_payload(
            evidence_role,
            payloads[evidence_role],
            authentications[evidence_role],
            principals,
            definitions,
        )
        _require_exact(
            instance["acceptance_receipts"][acceptance_field],
            _payload_sha256(evidence_role, payloads[evidence_role]),
            evidence_role + ".acceptance_binding",
        )
    for role in ("PHYSIONET_SELECTOR_RECORD", "RETAIL_SELECTOR_RECORD"):
        _validate_selector_payload(role, payloads[role], principals)
    _validate_contact_payload(payloads["CONTACT_TARGET_ROSTER"], principals, definitions)
    approval_requirements = _validate_approval_requirements(
        payloads["APPROVAL_REQUIREMENT_ROSTER"], principals
    )
    _validate_approval_validators(
        payloads["APPROVAL_RECEIPT_VALIDATOR_ROSTER"],
        approval_requirements,
        principal_ids,
    )
    _validate_coi_payload(
        payloads["CONFLICT_OF_INTEREST_DETERMINATION"], principals, principal_ids
    )
    _validate_key_payload(payloads["KEY_MANIFEST"], principals)
    _validate_acl_payload(payloads["ACL_MANIFEST"], principals)
    key_sha = _payload_sha256("KEY_MANIFEST", payloads["KEY_MANIFEST"])
    acl_sha = _payload_sha256("ACL_MANIFEST", payloads["ACL_MANIFEST"])
    _validate_escrow_payload(
        payloads["ESCROW_CONTROL_BINDING"], principals, key_sha, acl_sha
    )
    for role, field in _DEFINITION_ROLE_TO_FIELD.items():
        _require_exact(
            definitions[field],
            _payload_sha256(role, payloads[role]),
            role + ".definition_binding",
        )


def _all_empty(instance: Mapping[str, Any]) -> bool:
    return (
        all(value is None for value in instance["principals"].values())
        and all(value is None for value in instance["acceptance_receipts"].values())
        and all(value is None for value in instance["definition_bindings"].values())
        and instance["evidence_manifest"] == []
    )


def validate_population(
    instance: object, evidence_objects: object = None,
) -> Dict[str, Any]:
    """Validate an empty template or a fully populated future intake envelope.

    Partial population is deliberately rejected so no incomplete packet can be
    mistaken for a reviewable or operational object.
    """

    expected = empty_intake_instance()
    top_keys = tuple(expected)
    value = _exact_mapping(instance, top_keys, "INSTANCE")
    _require_exact(
        value["schema_version"], SCHEMA_VERSION, "instance.schema_version"
    )
    _require_exact(
        value["intake_contract_sha256"],
        intake_contract_sha256(),
        "instance.intake_contract_sha256",
    )
    principal_fields = tuple(item[1] for item in OWNER_ROLES)
    acceptance_fields = tuple(item[2] for item in OWNER_ROLES)
    principals = _exact_mapping(value["principals"], principal_fields, "PRINCIPALS")
    acceptances = _exact_mapping(
        value["acceptance_receipts"], acceptance_fields, "ACCEPTANCES"
    )
    slot_fields = tuple(item[0] for item in UNRESOLVED_DEFINITION_SLOTS)
    definitions = _exact_mapping(
        value["definition_bindings"], slot_fields, "DEFINITION_BINDINGS"
    )
    _exact_mapping(value["authority"], tuple(expected["authority"]), "AUTHORITY")
    _exact_mapping(
        value["attempt_budgets"], tuple(expected["attempt_budgets"]), "BUDGETS"
    )
    if any(item is not False for item in value["authority"].values()):
        raise IntakeValidationError("AUTHORITY_EXPANSION_FORBIDDEN")
    if any(type(item) is not int or item != 0 for item in value["attempt_budgets"].values()):
        raise IntakeValidationError("NONZERO_OR_NONINTEGER_BUDGET_FORBIDDEN")
    if value["tracker_or_ledger_edited"] is not False:
        raise IntakeValidationError("TRACKER_EDIT_CLAIM_FORBIDDEN")
    if type(value["blockers_closed"]) is not list or value["blockers_closed"]:
        raise IntakeValidationError("BLOCKER_CLOSURE_CLAIM_FORBIDDEN")
    if value["external_independent_review_receipt_sha256"] is not None:
        raise IntakeValidationError("SELF_INGESTED_EXTERNAL_REVIEW_FORBIDDEN")
    if _all_empty(value):
        if evidence_objects is not None and (
            type(evidence_objects) is not dict or evidence_objects
        ):
            raise IntakeValidationError("EMPTY_INSTANCE_WITH_EVIDENCE_FORBIDDEN")
        return {
            "decision": EMPTY_DECISION,
            "owner_principals_present": 0,
            "definition_slots_present": 0,
            "evidence_objects_present": 0,
            "authority_present": False,
        }
    if any(item is None for item in principals.values()):
        raise IntakeValidationError("PARTIAL_PRINCIPAL_ROSTER_FORBIDDEN")
    if any(item is None for item in acceptances.values()):
        raise IntakeValidationError("PARTIAL_ACCEPTANCE_ROSTER_FORBIDDEN")
    if any(item is None for item in definitions.values()):
        raise IntakeValidationError("PARTIAL_DEFINITION_ROSTER_FORBIDDEN")
    principal_ids = [
        _require_identifier(principals[field], field) for field in principal_fields
    ]
    if len(set(principal_ids)) != len(principal_ids):
        raise IntakeValidationError("PRINCIPAL_ROLE_ALIAS_FORBIDDEN")
    for field in acceptance_fields:
        _require_sha(acceptances[field], field)
    for field, exact_type in UNRESOLVED_DEFINITION_SLOTS:
        item = definitions[field]
        if exact_type == "LOWERCASE_SHA256":
            _require_sha(item, field)
        elif exact_type == "EXACT_INTEGER_TWO":
            if type(item) is not int or item != 2:
                raise IntakeValidationError("CONTACT_TARGET_COUNT_INVALID")
        elif exact_type == "EXACT_TRUE" and item is not True:
            raise IntakeValidationError("CONTACT_ROSTER_NOT_COMPLETE")
    manifest = value["evidence_manifest"]
    if type(manifest) is not list or len(manifest) != len(EVIDENCE_OBJECT_ROLES):
        raise IntakeValidationError("EVIDENCE_MANIFEST_LENGTH_MISMATCH")
    roles = []
    item_fields = tuple(
        contract_record()["evidence_manifest_schema"]["item_field_order"]
    )
    for ordinal, item in enumerate(manifest):
        record = _exact_mapping(item, item_fields, "EVIDENCE_ITEM")
        if type(record["ordinal"]) is not int or record["ordinal"] != ordinal:
            raise IntakeValidationError("EVIDENCE_ORDINAL_MISMATCH")
        if type(record["role"]) is not str:
            raise IntakeValidationError("EVIDENCE_ROLE_INVALID")
        roles.append(record["role"])
        if type(record["private_path"]) is not str or _EVIDENCE_PATH.fullmatch(
            record["private_path"]
        ) is None:
            raise IntakeValidationError("EVIDENCE_PATH_INVALID")
        if type(record["byte_count"]) is not int or record["byte_count"] < 1:
            raise IntakeValidationError("EVIDENCE_BYTE_COUNT_INVALID")
        _require_sha(record["raw_sha256"], "evidence.raw_sha256")
        if type(record["media_type"]) is not str or not record["media_type"]:
            raise IntakeValidationError("EVIDENCE_MEDIA_TYPE_INVALID")
        if type(record["contains_personal_or_sensitive_information"]) is not bool:
            raise IntakeValidationError("EVIDENCE_SENSITIVITY_FLAG_INVALID")
        if record["external_authentication_verified"] is not True:
            raise IntakeValidationError("EVIDENCE_EXTERNAL_AUTHENTICATION_ABSENT")
        _require_sha(
            record["verification_receipt_sha256"],
            "evidence.verification_receipt_sha256",
        )
    if tuple(roles) != EVIDENCE_OBJECT_ROLES:
        raise IntakeValidationError("EVIDENCE_ROLE_ORDER_OR_COMPLETENESS_MISMATCH")
    _replay_evidence_bundle(value, evidence_objects)
    return {
        "decision": COMPLETE_DECISION,
        "owner_principals_present": 9,
        "definition_slots_present": 9,
        "evidence_objects_present": len(EVIDENCE_OBJECT_ROLES),
        "authority_present": False,
    }


def synthetic_complete_bundle() -> Tuple[Dict[str, Any], Dict[str, bytes]]:
    """Return cross-bound synthetic values solely for qualification tests."""

    value = empty_intake_instance()
    for ordinal, (_role, principal_field, _acceptance_field) in enumerate(
        OWNER_ROLES
    ):
        value["principals"][principal_field] = f"SYNTHETIC-PRINCIPAL-{ordinal:02d}"
    principals = value["principals"]
    deterministic_sha = lambda label: hashlib.sha256(label.encode("ascii")).hexdigest()
    selector_common = {
        "target_derivation": "LITERAL_REGISTERED_SOURCE_URL",
        "version_or_revision_rule": (
            "ONE_CANONICAL_IMMUTABLE_VERSION_OR_REVISION_REQUIRED"
        ),
        "immutable_archive_locator_rule": (
            "EXACTLY_ONE_LOCATOR_SHA256_AND_BYTE_COUNT_REQUIRED"
        ),
        "required_metadata_fields": [
            "VERSION_OR_REVISION", "ARCHIVE_LOCATOR", "SHA256", "BYTE_COUNT"
        ],
        "exclusion_or_substitution_permitted": False,
        "accountable_owner_principal_id": principals[
            "accountable_governance_owner_id"
        ],
    }
    payloads: Dict[str, Dict[str, Any]] = {}
    for role in ("PHYSIONET_SELECTOR_RECORD", "RETAIL_SELECTOR_RECORD"):
        spec = _DOMAIN_SELECTOR_SPECS[role]
        payloads[role] = {
            "schema_version": "heterodiff-two-domain-acquisition-selector-record-v1",
            "domain_id": spec["domain_id"],
            "selector_id": spec["selector_id"],
            "exact_registered_target": spec["exact_registered_target"],
            **selector_common,
        }
    payloads["CONTACT_TARGET_ROSTER"] = {
        "schema_version": "heterodiff-contact-target-roster-v1",
        "targets": [
            {
                "ordinal": ordinal,
                "domain_id": domain,
                "operation_id": operation,
                "contact_target_id": f"SYNTHETIC-CONTACT-TARGET-{ordinal:02d}",
                "contact_mechanism_id": "SYNTHETIC-PUBLIC-WEB-ENDPOINT",
                "exact_destination_sha256": hashlib.sha256(
                    url.encode("ascii")
                ).hexdigest(),
                "permitted_questions_sha256": deterministic_sha(
                    f"synthetic-permitted-questions-{ordinal}"
                ),
            }
            for ordinal, (domain, operation, url) in enumerate(
                (
                    (
                        "physionet-challenge-2012",
                        "PHYSIONET_ADMIN_METADATA_LICENSE_GOVERNANCE",
                        _DOMAIN_SELECTOR_SPECS["PHYSIONET_SELECTOR_RECORD"][
                            "exact_registered_target"
                        ],
                    ),
                    (
                        "online-retail-ii",
                        "RETAIL_ADMIN_METADATA_LICENSE_GOVERNANCE",
                        _DOMAIN_SELECTOR_SPECS["RETAIL_SELECTOR_RECORD"][
                            "exact_registered_target"
                        ],
                    ),
                )
            )
        ],
        "declared_count": 2,
        "complete": True,
        "accountable_owner_principal_id": principals[
            "accountable_governance_owner_id"
        ],
    }
    requirement_specs = (
        (
            "physionet-challenge-2012", "SYNTHETIC-PHYSIONET-APPROVAL",
            "SYNTHETIC-PHYSIONET-ISSUER",
        ),
        (
            "online-retail-ii", "SYNTHETIC-RETAIL-APPROVAL",
            "SYNTHETIC-RETAIL-ISSUER",
        ),
    )
    payloads["APPROVAL_REQUIREMENT_ROSTER"] = {
        "schema_version": "heterodiff-approval-requirement-roster-v1",
        "domains": [
            {
                "domain_id": domain,
                "determination": "REQUIREMENTS_ENUMERATED",
                "requirements": [
                    {
                        "requirement_id": requirement,
                        "approval_type_id": "SYNTHETIC-DATA-ACCESS-APPROVAL",
                        "issuer_id": issuer,
                        "required_before_phase": "DATA",
                        "receipt_schema_sha256": deterministic_sha(
                            "synthetic-receipt-schema-" + requirement
                        ),
                    }
                ],
                "source_evidence_sha256": deterministic_sha(
                    "synthetic-approval-source-" + domain
                ),
            }
            for domain, requirement, issuer in requirement_specs
        ],
        "accountable_endpoint_principal_id": principals[
            "license_privacy_institutional_approval_endpoint_id"
        ],
    }
    payloads["APPROVAL_RECEIPT_VALIDATOR_ROSTER"] = {
        "schema_version": "heterodiff-approval-receipt-validator-roster-v1",
        "validators": [
            {
                "requirement_id": requirement,
                "validator_principal_id": f"SYNTHETIC-APPROVAL-VALIDATOR-{ordinal:02d}",
                "validation_method_id": "SYNTHETIC-DETACHED-SIGNATURE-VALIDATION",
                "accepted_issuer_roster_sha256": content_sha256(
                    "definition_record",
                    {
                        "accepted_issuer_ids": [issuer],
                        "requirement_id": requirement,
                    },
                ),
                "revocation_check_rule": deterministic_sha(
                    "synthetic-revocation-check-" + requirement
                ),
            }
            for ordinal, (_domain, requirement, issuer) in enumerate(
                requirement_specs
            )
        ],
        "all_approval_requirements_covered": True,
    }
    payloads["CONFLICT_OF_INTEREST_DETERMINATION"] = {
        "schema_version": (
            "heterodiff-nine-role-conflict-of-interest-determination-v1"
        ),
        "nine_role_assignments_sha256": _role_assignments_sha256(principals),
        "relationships_examined": _relationship_roster(),
        "conflicts": [],
        "determination": "NO_PROHIBITED_ROLE_ALIAS_AND_NO_IDENTIFIED_CONFLICT_V1",
        "determiner_principal_id": "SYNTHETIC-EXTERNAL-COI-DETERMINER",
        "authentication_evidence_sha256": deterministic_sha(
            "synthetic-coi-authentication"
        ),
    }
    payloads["KEY_MANIFEST"] = {
        "schema_version": "heterodiff-held-out-key-manifest-v1",
        "key_id": "SYNTHETIC-HELD-OUT-KEY",
        "algorithm_id": "SYNTHETIC-AEAD-ALGORITHM",
        "public_fingerprint_sha256": deterministic_sha("synthetic-public-key"),
        "accepted_by_principal_id": principals["key_acl_acceptance_authority_id"],
        "custody_principal_id": principals[
            "independent_held_out_escrow_custodian_id"
        ],
        "private_key_location_disclosed_in_public_packet": False,
        "rotation_or_revocation_rule_sha256": deterministic_sha(
            "synthetic-key-rotation"
        ),
    }
    acl_links = (
        (
            principals["independent_held_out_escrow_custodian_id"],
            "CUSTODY_CIPHERTEXT_NO_OPEN",
        ),
        (
            principals["independent_final_opening_approver_id"],
            "APPROVE_OPEN_NO_KEY_CUSTODY",
        ),
        (
            principals["key_acl_acceptance_authority_id"],
            "ACCEPT_KEY_AND_ACL_NO_DATA_OPEN",
        ),
    )
    payloads["ACL_MANIFEST"] = {
        "schema_version": "heterodiff-held-out-acl-manifest-v1",
        "entries": [
            {
                "resource_id": "TWO-DOMAIN-HELD-OUT-ESCROW",
                "principal_id": principal_id,
                "permission_enum": permission,
                "effective_time_rfc3339_utc": "2026-09-01T00:00:00.000000000Z",
                "revocation_rule_sha256": deterministic_sha(
                    f"synthetic-acl-revocation-{ordinal}"
                ),
            }
            for ordinal, (principal_id, permission) in enumerate(acl_links)
        ],
    }
    key_sha = _payload_sha256("KEY_MANIFEST", payloads["KEY_MANIFEST"])
    acl_sha = _payload_sha256("ACL_MANIFEST", payloads["ACL_MANIFEST"])
    payloads["ESCROW_CONTROL_BINDING"] = {
        "schema_version": "heterodiff-held-out-escrow-control-binding-v1",
        "escrow_control_id": "INDEPENDENT_HELD_OUT_ESCROW_LEAST_PRIVILEGE_ACL_V1",
        "held_out_material_definition_sha256": RESOLVED_LOCAL_DEFINITIONS[
            "held_out_material_definition_sha256"
        ],
        "final_opening_rule_sha256": RESOLVED_LOCAL_DEFINITIONS[
            "final_opening_rule_sha256"
        ],
        "escrow_custodian_principal_id": principals[
            "independent_held_out_escrow_custodian_id"
        ],
        "final_opening_approver_principal_id": principals[
            "independent_final_opening_approver_id"
        ],
        "key_acl_acceptance_authority_principal_id": principals[
            "key_acl_acceptance_authority_id"
        ],
        "raw_snapshot_custodian_principal_id": principals[
            "raw_snapshot_custodian_id"
        ],
        "deterministic_split_operator_principal_id": principals[
            "deterministic_split_operator_id"
        ],
        "retention_deletion_owner_principal_id": principals[
            "retention_deletion_owner_id"
        ],
        "incident_response_owner_principal_id": principals[
            "incident_response_owner_id"
        ],
        "key_manifest_sha256": key_sha,
        "acl_manifest_sha256": acl_sha,
        "storage_boundary_sha256": deterministic_sha("synthetic-storage-boundary"),
        "retention_deletion_policy_sha256": deterministic_sha(
            "synthetic-retention-policy"
        ),
        "incident_response_policy_sha256": deterministic_sha(
            "synthetic-incident-response"
        ),
        "activation_claimed": False,
    }
    for role, field in _DEFINITION_ROLE_TO_FIELD.items():
        value["definition_bindings"][field] = _payload_sha256(role, payloads[role])
    value["definition_bindings"]["contact_target_count"] = 2
    value["definition_bindings"]["contact_roster_complete"] = True
    coi_sha = value["definition_bindings"][
        "conflict_of_interest_determination_sha256"
    ]
    for role, principal_field, acceptance_field in OWNER_ROLES:
        evidence_role = role + "_ACCEPTANCE"
        authentication_evidence = deterministic_sha(
            "synthetic-acceptance-authentication-" + role
        )
        payloads[evidence_role] = {
            "schema_version": "heterodiff-principal-role-acceptance-v1",
            "role_id": role,
            "principal_id": principals[principal_field],
            "intake_contract_sha256": intake_contract_sha256(),
            "accepted_scope": role + "_SCOPE_V1",
            "acknowledged_prohibitions": list(PROHIBITED_AUTHORITY_CLAIMS),
            "conflict_of_interest_determination_sha256": coi_sha,
            "authentication_method_id": "SYNTHETIC-DETACHED-SIGNATURE",
            "authentication_evidence_sha256": authentication_evidence,
            "issued_time_rfc3339_utc": "2026-09-01T00:00:00.000000000Z",
            "acceptance": True,
        }
        value["acceptance_receipts"][acceptance_field] = _payload_sha256(
            evidence_role, payloads[evidence_role]
        )
    evidence_objects: Dict[str, bytes] = {}
    manifest = []
    for ordinal, role in enumerate(EVIDENCE_OBJECT_ROLES):
        if role.endswith("_ACCEPTANCE"):
            method = payloads[role]["authentication_method_id"]
            authentication_evidence = payloads[role][
                "authentication_evidence_sha256"
            ]
        else:
            method = "SYNTHETIC-DETACHED-SIGNATURE"
            authentication_evidence = deterministic_sha(
                "synthetic-object-authentication-" + role
            )
        authentication = {
            "external_verifier_principal_id": (
                f"SYNTHETIC-EXTERNAL-VERIFIER-{ordinal:02d}"
            ),
            "method_id": method,
            "evidence_sha256": authentication_evidence,
            "verified": True,
        }
        raw = evidence_object_bytes(role, payloads[role], authentication)
        evidence_objects[role] = raw
        envelope = json.loads(raw.decode("ascii"))
        manifest.append(
            {
                "ordinal": ordinal,
                "role": role,
                "private_path": (
                    "research/private_evidence/b02_b03_b09/"
                    f"synthetic-{ordinal:02d}/receipt.json"
                ),
                "byte_count": len(raw),
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "media_type": "application/json",
                "contains_personal_or_sensitive_information": False,
                "external_authentication_verified": True,
                "verification_receipt_sha256": envelope[
                    "verification_receipt_sha256"
                ],
            }
        )
    value["evidence_manifest"] = manifest
    return value, evidence_objects


def synthetic_complete_instance() -> Dict[str, Any]:
    """Return only the synthetic envelope; raw evidence is intentionally separate."""

    return synthetic_complete_bundle()[0]


__all__ = (
    "COMPLETE_DECISION",
    "CONTRACT_STATE",
    "EMPTY_DECISION",
    "EVIDENCE_OBJECT_ROLES",
    "IntakeValidationError",
    "OWNER_ROLES",
    "PROHIBITED_AUTHORITY_CLAIMS",
    "RESOLVED_LOCAL_DEFINITIONS",
    "SCHEMA_VERSION",
    "UNRESOLVED_DEFINITION_SLOTS",
    "content_sha256",
    "contract_record",
    "empty_intake_instance",
    "evidence_object_bytes",
    "intake_contract_sha256",
    "synthetic_complete_bundle",
    "synthetic_complete_instance",
    "validate_population",
)
