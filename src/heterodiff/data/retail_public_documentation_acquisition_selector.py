"""Pure Online Retail II public-documentation selector and readiness contract.

This module freezes facts visible on the official UCI dataset record and a
fail-closed future acquisition identity.  It performs no I/O and does not
authenticate people, approvals, custody, data, or scientific evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Mapping


SCHEMA_VERSION = "heterodiff-retail-public-documentation-selector-v1"
PACKAGE_STATE = "RETAIL_PUBLIC_DOCUMENTATION_SELECTOR_FROZEN_NO_DATA_ACCESS"
SELECTOR_CORE_DIGEST_DOMAIN = (
    b"heterodiff/retail/public-documentation-selector-core/v1\0"
)
SOURCE_VERSION_RECEIPT_DOMAIN = (
    b"heterodiff/retail/content-addressed-source-version/v1\0"
)
INTAKE_DEFINITION_RECORD_DOMAIN = (
    b"heterodiff/b02-b03-b09/external-definition-record/v1\0"
)

PUBLIC_DOCUMENTATION_RECORD = {
    "record_kind": "SEMANTIC_PUBLIC_DOCUMENTATION_OBSERVATION_NOT_PAGE_BYTE_SNAPSHOT",
    "official_dataset_page": (
        "https://archive.ics.uci.edu/dataset/502/online+retail+ii"
    ),
    "official_direct_archive_locator": (
        "https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip"
    ),
    "dataset_id": 502,
    "dataset_name": "Online Retail II",
    "doi": "10.24432/C5CG6D",
    "creator": "Daqing Chen",
    "citation_year": 2012,
    "page_donation_display": "9/20/2019",
    "license_short_name": "CC-BY-4.0",
    "license_name": "Creative Commons Attribution 4.0 International",
    "license_url": "https://creativecommons.org/licenses/by/4.0/legalcode",
    "advertised_instance_count": 1067371,
    "advertised_has_missing_values": True,
    "advertised_member_name": "online_retail_II.xlsx",
    "advertised_member_is_directory": False,
    "advertised_member_byte_count": 45622278,
    "advertised_archive_byte_count": 45622418,
    "advertised_display_size": "43.5 MB",
    "advertised_source_period": "01/12/2009 THROUGH 09/12/2011",
    "advertised_raw_fields": [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
    ],
    "immutable_revision_exposed_by_public_page": False,
    "raw_archive_sha256_exposed_by_public_page": False,
    "governance_or_privacy_approval_inferred_from_license": False,
}

ACQUISITION_SELECTOR_CORE = {
    "schema_version": "heterodiff-retail-public-documentation-selector-v1",
    "domain_id": "online-retail-ii",
    "slot_id": "R4-RETAIL",
    "selector_id": (
        "UCI_DATASET_502_ONLINE_RETAIL_II_OFFICIAL_ARCHIVE_CONTENT_ADDRESSED_V1"
    ),
    "registered_metadata_target": (
        "https://archive.ics.uci.edu/dataset/502/online+retail+ii"
    ),
    "exact_archive_target": (
        "https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip"
    ),
    "request_method": "GET",
    "redirect_limit": 0,
    "fallback_limit": 0,
    "retry_limit": 0,
    "attempt_budget_before_fresh_authority": 0,
    "authentication_permitted": False,
    "archive_member_allowlist": ["online_retail_II.xlsx"],
    "additional_archive_members_permitted": False,
    "expected_member_byte_count": 45622278,
    "expected_archive_byte_count": 45622418,
    "version_rule": "UCI-502-C5CG6D-ARCHIVE-SHA256-{raw_archive_sha256}",
    "version_is_unresolved_until_private_bytes_are_rehashed": True,
    "raw_hash_is_unresolved_until_private_bytes_are_rehashed": True,
    "owner_bound_intake_wrapper_required": True,
    "substitution_or_silent_update_permitted": False,
}

EXTERNAL_READINESS_CHECKLIST = (
    {
        "obligation_id": "RET-W3-01-OWNER-BOUND-SELECTOR",
        "principal_role": "ACCOUNTABLE_GOVERNANCE_OWNER",
        "evidence_type": "OWNER_BOUND_RETAIL_SELECTOR_RECORD_AND_ACCEPTANCE",
        "affected_ids": ["B03", "B09"],
    },
    {
        "obligation_id": "RET-W3-02-EXACT-DATA-AUTHORITY-AND-INTENT",
        "principal_role": "RAW_SNAPSHOT_CUSTODIAN",
        "evidence_type": "FRESH_EXACT_AUTHORITY_AND_DURABLE_NO_CLOBBER_INTENT",
        "affected_ids": ["B03"],
    },
    {
        "obligation_id": "RET-W3-03-CONTENT-ADDRESSED-SNAPSHOT",
        "principal_role": "RAW_SNAPSHOT_CUSTODIAN",
        "evidence_type": "RAW_ARCHIVE_HASH_BYTE_COUNT_INVENTORY_AND_VERSION_RECEIPT",
        "affected_ids": ["F038", "F039", "B03"],
    },
    {
        "obligation_id": "RET-W3-04-GOVERNANCE-DETERMINATION",
        "principal_role": "LICENSE_PRIVACY_INSTITUTIONAL_APPROVAL_ENDPOINT",
        "evidence_type": "AUTHENTICATED_APPLICABLE_GOVERNANCE_PRIVACY_DETERMINATION",
        "affected_ids": ["F041", "B03", "B09"],
    },
    {
        "obligation_id": "RET-W3-05-SCHEMA-TIME-IDENTITY-RECONCILIATION",
        "principal_role": "RAW_SNAPSHOT_CUSTODIAN",
        "evidence_type": "COMPLETE_SCHEMA_TIMEZONE_CUSTOMER_ID_AND_ROW_PRESERVATION_RECEIPT",
        "affected_ids": ["B03"],
    },
    {
        "obligation_id": "RET-W3-06-OBSERVATION-REFERENCE",
        "principal_role": "ACCOUNTABLE_GOVERNANCE_OWNER",
        "evidence_type": "NORMALIZED_CODE_MATCHED_OBSERVATION_REFERENCE_RECEIPT",
        "affected_ids": ["F053", "B03"],
    },
    {
        "obligation_id": "RET-W3-07-COMMON-SUPPORT",
        "principal_role": "ACCOUNTABLE_GOVERNANCE_OWNER",
        "evidence_type": "ACQUISITION_JUSTIFICATION_PROOF_IMPLEMENTATION_CERTIFICATE_AND_REVIEW",
        "affected_ids": ["F054", "B03"],
    },
    {
        "obligation_id": "RET-W3-08-POPULATED-PRIVATE-SPLIT",
        "principal_role": "DETERMINISTIC_SPLIT_OPERATOR",
        "evidence_type": "POPULATED_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_AND_F061_REPLAY",
        "affected_ids": ["F059", "B03"],
    },
    {
        "obligation_id": "RET-W3-09-TEMPORAL-FEASIBILITY",
        "principal_role": "DETERMINISTIC_SPLIT_OPERATOR",
        "evidence_type": "EXHAUSTIVE_GAP_PAIR_FEASIBILITY_OR_TERMINAL_NO_GO_RECEIPT",
        "affected_ids": ["B03"],
    },
    {
        "obligation_id": "RET-W3-10-DUPLICATE-LEAKAGE-AUDIT",
        "principal_role": "INDEPENDENT_HELD_OUT_ESCROW_CUSTODIAN",
        "evidence_type": "COMPLETE_EXACT_AND_RULE_BOUND_NEAR_DUPLICATE_AUDIT_RECEIPT",
        "affected_ids": ["B03", "B09"],
    },
    {
        "obligation_id": "RET-W3-11-ZERO-VIOLATION-ADMISSION",
        "principal_role": "ACCOUNTABLE_GOVERNANCE_OWNER",
        "evidence_type": "THIRTEEN_ZERO_COUNTS_SIX_VERIFIED_RECEIPTS_AND_INDEPENDENT_ADMISSION",
        "affected_ids": ["B03"],
    },
    {
        "obligation_id": "RET-W3-12-PLAN-OWNER-ACCEPTANCE",
        "principal_role": "ACCOUNTABLE_GOVERNANCE_OWNER",
        "evidence_type": "F163_AND_F167_APPLICABLE_OWNER_ACCEPTANCE_AND_RELEASE_BOUNDARY",
        "affected_ids": ["B09"],
    },
)

NONCLAIMS = {
    "tracker_or_ledger_edited": False,
    "dataset_downloaded_opened_or_parsed": False,
    "principal_or_approval_fabricated": False,
    "network_or_data_authority_created": False,
    "retail_selector_intake_slot_closed": False,
    "F038_closed": False,
    "F039_closed": False,
    "F041_closed": False,
    "F053_closed": False,
    "F054_closed": False,
    "F059_closed": False,
    "B03_closed": False,
    "B09_closed": False,
    "blockers_closed": 0,
    "formal_tests_closed": 0,
    "scientific_results_created": 0,
}

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_PRINCIPAL = re.compile(r"[A-Z0-9][A-Z0-9._:-]{2,127}\Z")
_PLACEHOLDERS = frozenset({"NONE", "NULL", "PENDING", "TBD", "UNKNOWN"})


class RetailSelectorError(ValueError):
    """Malformed, incomplete, substituted, or authority-expanding input."""


def canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise RetailSelectorError("NONCANONICAL_VALUE") from error


def _digest(domain: bytes, value: object) -> str:
    return hashlib.sha256(domain + canonical_bytes(value)).hexdigest()


def _sha256(value: object, name: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise RetailSelectorError(name + "_MUST_BE_LOWERCASE_SHA256")
    return value


def _principal(value: object, name: str) -> str:
    if (
        type(value) is not str
        or _PRINCIPAL.fullmatch(value) is None
        or value in _PLACEHOLDERS
    ):
        raise RetailSelectorError(name + "_MUST_BE_OPAQUE_NONPLACEHOLDER_ID")
    return value


def _exact_mapping(value: object, keys: tuple[str, ...], name: str) -> Mapping[str, Any]:
    if type(value) is not dict or tuple(value.keys()) != keys:
        raise RetailSelectorError(name + "_ROSTER_MISMATCH")
    return value


def selector_core_sha256() -> str:
    """Return the owner-independent, public-documentation selector digest."""

    return _digest(SELECTOR_CORE_DIGEST_DOMAIN, ACQUISITION_SELECTOR_CORE)


def owner_bound_intake_selector(accountable_owner_principal_id: str) -> Dict[str, Any]:
    """Build the exact future Retail selector payload required by intake v1.

    This only constructs bytes.  It does not authenticate the owner or close
    the intake slot; the external evidence bundle must do both.
    """

    owner = _principal(
        accountable_owner_principal_id, "accountable_owner_principal_id"
    )
    return {
        "accountable_owner_principal_id": owner,
        "domain_id": "online-retail-ii",
        "exact_registered_target": PUBLIC_DOCUMENTATION_RECORD[
            "official_dataset_page"
        ],
        "exclusion_or_substitution_permitted": False,
        "immutable_archive_locator_rule": (
            "EXACTLY_ONE_LOCATOR_SHA256_AND_BYTE_COUNT_REQUIRED"
        ),
        "required_metadata_fields": [
            "VERSION_OR_REVISION",
            "ARCHIVE_LOCATOR",
            "SHA256",
            "BYTE_COUNT",
        ],
        "schema_version": "heterodiff-two-domain-acquisition-selector-record-v1",
        "selector_id": (
            "UCI_DATASET_502_ONLINE_RETAIL_II_EXACT_REGISTERED_URL_SELECTOR_V1"
        ),
        "target_derivation": "LITERAL_REGISTERED_SOURCE_URL",
        "version_or_revision_rule": (
            "ONE_CANONICAL_IMMUTABLE_VERSION_OR_REVISION_REQUIRED"
        ),
    }


def owner_bound_intake_selector_sha256(accountable_owner_principal_id: str) -> str:
    payload = owner_bound_intake_selector(accountable_owner_principal_id)
    return _digest(
        INTAKE_DEFINITION_RECORD_DOMAIN,
        {"payload": payload, "role": "RETAIL_SELECTOR_RECORD"},
    )


def derive_content_addressed_snapshot_version(raw_archive_sha256: str) -> str:
    digest = _sha256(raw_archive_sha256, "raw_archive_sha256")
    return "UCI-502-C5CG6D-ARCHIVE-SHA256-" + digest


_ACQUISITION_KEYS = (
    "schema_version",
    "selector_core_sha256",
    "registered_metadata_target",
    "exact_archive_target",
    "archive_http_status",
    "redirect_count",
    "fallback_count",
    "raw_archive_sha256",
    "raw_archive_byte_count",
    "archive_member_name",
    "archive_member_sha256",
    "archive_member_byte_count",
    "archive_inventory_sha256",
    "response_headers_sha256",
    "durable_intent_sha256",
    "exact_data_authority_sha256",
    "custodian_acceptance_sha256",
    "raw_hash_recomputed_from_private_bytes",
    "archive_inventory_recomputed_from_private_bytes",
    "independent_custody_verification",
    "dataset_opened_or_parsed",
)


def validate_future_acquisition_receipt(value: object) -> Dict[str, Any]:
    """Validate a future externally supplied raw-custody receipt structurally.

    Passing this pure function is not authentication.  The returned candidate
    still requires private-file replay and an external independent review.
    """

    row = _exact_mapping(value, _ACQUISITION_KEYS, "ACQUISITION_RECEIPT")
    expected = {
        "schema_version": "heterodiff-retail-raw-acquisition-receipt-v1",
        "selector_core_sha256": selector_core_sha256(),
        "registered_metadata_target": ACQUISITION_SELECTOR_CORE[
            "registered_metadata_target"
        ],
        "exact_archive_target": ACQUISITION_SELECTOR_CORE["exact_archive_target"],
        "archive_http_status": 200,
        "redirect_count": 0,
        "fallback_count": 0,
        "raw_archive_byte_count": ACQUISITION_SELECTOR_CORE[
            "expected_archive_byte_count"
        ],
        "archive_member_name": "online_retail_II.xlsx",
        "archive_member_byte_count": ACQUISITION_SELECTOR_CORE[
            "expected_member_byte_count"
        ],
        "raw_hash_recomputed_from_private_bytes": True,
        "archive_inventory_recomputed_from_private_bytes": True,
        "independent_custody_verification": True,
        "dataset_opened_or_parsed": False,
    }
    for name, expected_value in expected.items():
        if type(row[name]) is not type(expected_value) or row[name] != expected_value:
            raise RetailSelectorError("ACQUISITION_RECEIPT_DRIFT:" + name)
    for name in (
        "raw_archive_sha256",
        "archive_member_sha256",
        "archive_inventory_sha256",
        "response_headers_sha256",
        "durable_intent_sha256",
        "exact_data_authority_sha256",
        "custodian_acceptance_sha256",
    ):
        _sha256(row[name], name)
    version = derive_content_addressed_snapshot_version(row["raw_archive_sha256"])
    source_payload = {
        "schema_version": "heterodiff-retail-content-addressed-source-version-v1",
        "dataset_id": 502,
        "doi": "10.24432/C5CG6D",
        "snapshot_version": version,
        "raw_snapshot_sha256": row["raw_archive_sha256"],
        "raw_snapshot_byte_count": row["raw_archive_byte_count"],
        "archive_inventory_sha256": row["archive_inventory_sha256"],
        "selector_core_sha256": row["selector_core_sha256"],
    }
    return {
        **source_payload,
        "source_version_receipt_sha256": _digest(
            SOURCE_VERSION_RECEIPT_DOMAIN, source_payload
        ),
        "structural_decision": (
            "CANDIDATE_F038_F039_REQUIRES_PRIVATE_CUSTODY_REPLAY_AND_EXTERNAL_REVIEW"
        ),
        "authority_created": False,
        "field_closed": False,
    }


def empty_readiness_status() -> Dict[str, None]:
    return {row["obligation_id"]: None for row in EXTERNAL_READINESS_CHECKLIST}


def assess_external_readiness(value: object) -> Dict[str, Any]:
    """Accept only the wholly empty or wholly complete checklist shape."""

    identifiers = tuple(row["obligation_id"] for row in EXTERNAL_READINESS_CHECKLIST)
    status = _exact_mapping(value, identifiers, "READINESS_STATUS")
    if all(status[item] is None for item in identifiers):
        return {
            "decision": "HOLD_REAL_RETAIL_EVIDENCE_INCOMPLETE",
            "completed_count": 0,
            "remaining_obligation_ids": list(identifiers),
            "field_closure_authorized": False,
            "blocker_closure_authorized": False,
        }
    if any(status[item] is None for item in identifiers):
        raise RetailSelectorError("PARTIAL_READINESS_POPULATION_FORBIDDEN")
    for definition in EXTERNAL_READINESS_CHECKLIST:
        item = definition["obligation_id"]
        receipt = _exact_mapping(
            status[item],
            (
                "obligation_id",
                "principal_role",
                "principal_id",
                "evidence_sha256",
                "acceptance_sha256",
                "externally_authenticated",
                "independently_verified",
            ),
            item,
        )
        if receipt["obligation_id"] != item:
            raise RetailSelectorError("READINESS_OBLIGATION_ID_MISMATCH:" + item)
        if receipt["principal_role"] != definition["principal_role"]:
            raise RetailSelectorError("READINESS_PRINCIPAL_ROLE_MISMATCH:" + item)
        _principal(receipt["principal_id"], item + ".principal_id")
        _sha256(receipt["evidence_sha256"], item + ".evidence_sha256")
        _sha256(receipt["acceptance_sha256"], item + ".acceptance_sha256")
        if receipt["externally_authenticated"] is not True:
            raise RetailSelectorError("READINESS_EXTERNAL_AUTHENTICATION_ABSENT:" + item)
        if receipt["independently_verified"] is not True:
            raise RetailSelectorError("READINESS_INDEPENDENT_VERIFICATION_ABSENT:" + item)
    return {
        "decision": (
            "STRUCTURALLY_COMPLETE_INPUT_REQUIRES_PRIVATE_CUSTODY_REPLAY_"
            "AND_EXTERNAL_INDEPENDENT_REVIEW"
        ),
        "completed_count": len(identifiers),
        "remaining_obligation_ids": [],
        "field_closure_authorized": False,
        "blocker_closure_authorized": False,
    }


__all__ = [
    "ACQUISITION_SELECTOR_CORE",
    "EXTERNAL_READINESS_CHECKLIST",
    "NONCLAIMS",
    "PACKAGE_STATE",
    "PUBLIC_DOCUMENTATION_RECORD",
    "RetailSelectorError",
    "SCHEMA_VERSION",
    "assess_external_readiness",
    "canonical_bytes",
    "derive_content_addressed_snapshot_version",
    "empty_readiness_status",
    "owner_bound_intake_selector",
    "owner_bound_intake_selector_sha256",
    "selector_core_sha256",
    "validate_future_acquisition_receipt",
]
