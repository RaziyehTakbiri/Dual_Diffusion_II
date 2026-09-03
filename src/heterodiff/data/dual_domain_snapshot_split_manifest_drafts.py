"""Pure draft schemas for two content-addressed snapshot/split pairs.

This module has no file, network, process, entropy, data-acquisition, or
scientific-execution route.  It accepts only caller-supplied in-memory
mappings.  The only constructor exposed here creates explicitly synthetic
qualification records.  Future real records require separate authority and
custody outside this package.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, Sequence, Tuple


CONTROL_PREDICATE = (
    "RETAIL_TASK_SCHEMA_AND_DUAL_DOMAIN_SNAPSHOT_SPLIT_MANIFEST_DRAFTS_VALIDATED"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
RECEIPT_STATES = (
    "SYNTHETIC_QUALIFICATION_ONLY",
    "FUTURE_POPULATED_AFTER_SEPARATE_AUTHORITY",
)
SPLITS = ("TRAIN", "VALIDATION", "TEST")
NUMERATORS = (70, 15, 15)
DENOMINATOR = 100

DOMAIN_CONTRACTS: Mapping[str, Mapping[str, Any]] = {
    "physionet-challenge-2012": {
        "slot_id": "R3-PHYS",
        "snapshot_schema": "heterodiff-physionet-content-addressed-snapshot-manifest-v1",
        "split_schema": "heterodiff-physionet-content-addressed-split-manifest-v1",
        "snapshot_digest_domain": b"heterodiff/physionet-snapshot-manifest/v1\0",
        "split_digest_domain": b"heterodiff/physionet-split-manifest/v1\0",
        "normalized_digest_domain": b"heterodiff/physionet-normalized-split-input/v1\0",
        "assignment_digest_domain": b"heterodiff/physionet-split-assignment/v1\0",
        "algorithm_id": "PHYSIONET_PATIENT_HASH_HAMILTON_70_15_15_V1",
        "splitter_predicate": (
            "PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN_AND_"
            "SYNTHETIC_QUALIFICATION_VALIDATED"
        ),
        "splitter_machine_sha256": (
            "a9fc01ae42ba7942e6c61def5120d6497b74fc99c82b0c5b68188f221b4b68a8"
        ),
        "minimum_group_count": 5,
        "normalization_contract_id": "PHYSIONET_MINIMAL_DECIMAL_PATIENT_RECORD_PROJECTION_V1",
    },
    "online-retail-ii": {
        "slot_id": "R4-RETAIL",
        "snapshot_schema": "heterodiff-retail-content-addressed-snapshot-manifest-v1",
        "split_schema": "heterodiff-retail-content-addressed-split-manifest-v1",
        "snapshot_digest_domain": b"heterodiff/retail-snapshot-manifest/v1\0",
        "split_digest_domain": b"heterodiff/retail-split-manifest/v1\0",
        "normalized_digest_domain": b"heterodiff/retail-normalized-split-input/v1\0",
        "assignment_digest_domain": (
            b"heterodiff/retail-customer-temporal-assignment/v1\0"
        ),
        "algorithm_id": "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_HAMILTON_70_15_15_V1",
        "splitter_predicate": (
            "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN_AND_"
            "SYNTHETIC_QUALIFICATION_VALIDATED"
        ),
        "splitter_machine_sha256": (
            "b27086c5979d2f7018b4b8b50b3fffacf03b3fe2691d60567bc42b179d53e98b"
        ),
        "minimum_group_count": 5,
        "normalization_contract_id": (
            "RETAIL_OPAQUE_CUSTOMER_KEY_UTC_MICROSECOND_ROW_PROJECTION_V1"
        ),
    },
}

PATIENT_ORDER_DOMAIN = b"heterodiff/physionet-patient-order/v1\0"
SYNTHETIC_RECEIPT_DOMAIN = b"heterodiff/synthetic-manifest-receipt/v1\0"
MAX_SIGNED_64 = 2**63 - 1
MIN_SIGNED_64 = -(2**63)

RETAIL_TASK_FUTURE_FIELDS: Tuple[Tuple[str, str, str], ...] = (
    ("F038", "/domains/1/snapshot_version", "NONEMPTY_ASCII_VERSION_RECEIPT"),
    ("F039", "/domains/1/raw_snapshot_sha256", "LOWERCASE_SHA256"),
    ("F040", "/domains/1/license_and_access_record", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F041", "/domains/1/governance_approval_record", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F042", "/domains/1/generated_endpoint_semantics", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F043", "/domains/1/context_semantics", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F044", "/domains/1/observation_semantics", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F045", "/domains/1/event_type_and_mark_schema", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F046", "/domains/1/physical_time_semantics", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F047", "/domains/1/horizon", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F048", "/domains/1/cap", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F049", "/domains/1/segmentation_rule", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F050", "/domains/1/overflow_and_exclusion_rule", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F051", "/domains/1/cancellation_country_and_simultaneous_line_item_rule", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F052", "/domains/1/clean_observation_kernel", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F053", "/domains/1/observation_reference", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F054", "/domains/1/positive_or_common_support_route", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F055", "/domains/1/detection_noise_confusion_clutter_rule", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F056", "/domains/1/method_blind_training_only_admission_statistic", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F057", "/domains/1/method_blind_training_only_admission_threshold", "CONTENT_ADDRESSED_CANONICAL_JSON_RECEIPT"),
    ("F059", "/split_and_leakage_plan/retail_split_manifest_path", "CONTENT_ADDRESSED_PRIVATE_CUSTODY_LOCATOR_RECEIPT"),
    ("F060", "/split_and_leakage_plan/retail_temporal_cutoff_and_window_rule", "CONTENT_ADDRESSED_SPLIT_MANIFEST_RECEIPT"),
    ("F061", "/split_and_leakage_plan/train_validation_test_proportions_or_counts", "POWER_REVIEWED_CONTENT_ADDRESSED_ALLOCATION_RECEIPT"),
)


class ManifestDraftError(ValueError):
    """Fail-closed schema, content, or crosslink violation."""


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
        raise ManifestDraftError("NONCANONICAL_VALUE") from error


def _require_exact_json_tree(value: Any, code: str, *, allow_none: bool) -> None:
    """Reject equality-compatible subclasses anywhere in a manifest tree."""

    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ManifestDraftError(code)
            _require_exact_json_tree(item, code, allow_none=allow_none)
        return
    if type(value) is list:
        for item in value:
            _require_exact_json_tree(item, code, allow_none=allow_none)
        return
    if type(value) in (str, int):
        return
    if value is None and allow_none:
        return
    raise ManifestDraftError(code)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_keys(value: Any, expected: Sequence[str], code: str) -> None:
    if type(value) is not dict or set(value) != set(expected):
        raise ManifestDraftError(code)


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_ascii(value: Any, maximum: int, code: str) -> str:
    if (
        type(value) is not str
        or not value
        or len(value) > maximum
        or not value.isascii()
        or value != value.strip()
        or any(ord(character) < 0x21 or ord(character) > 0x7E for character in value)
    ):
        raise ManifestDraftError(code)
    return value


def _contract(domain_id: Any) -> Mapping[str, Any]:
    if type(domain_id) is not str or domain_id not in DOMAIN_CONTRACTS:
        raise ManifestDraftError("UNKNOWN_DOMAIN")
    return DOMAIN_CONTRACTS[domain_id]


def _normalize_physionet(rows: Any) -> List[Dict[str, Any]]:
    if type(rows) is not list or not rows:
        raise ManifestDraftError("INVALID_NORMALIZED_MANIFEST")
    normalized: List[Dict[str, Any]] = []
    ordinals = set()
    for row in rows:
        _strict_keys(
            row,
            ("record_ordinal", "patient_id"),
            "INVALID_NORMALIZED_MANIFEST",
        )
        ordinal = row["record_ordinal"]
        patient_id = row["patient_id"]
        if (
            type(ordinal) is not int
            or ordinal < 0
            or ordinal in ordinals
            or type(patient_id) is not str
            or not patient_id
            or len(patient_id) > 64
            or not patient_id.isascii()
            or not patient_id.isdecimal()
            or any(character not in "0123456789" for character in patient_id)
            or patient_id == "0"
            or (len(patient_id) > 1 and patient_id.startswith("0"))
        ):
            raise ManifestDraftError("INVALID_NORMALIZED_MANIFEST")
        ordinals.add(ordinal)
        normalized.append({"patient_id": patient_id, "record_ordinal": ordinal})
    if ordinals != set(range(len(normalized))):
        raise ManifestDraftError("INVALID_NORMALIZED_MANIFEST")
    normalized.sort(key=lambda item: item["record_ordinal"])
    if len({item["patient_id"] for item in normalized}) < 5:
        raise ManifestDraftError("INSUFFICIENT_PATIENT_GROUPS")
    return normalized


def _normalize_retail(rows: Any) -> List[Dict[str, Any]]:
    if type(rows) is not list or not rows:
        raise ManifestDraftError("INVALID_NORMALIZED_MANIFEST")
    normalized: List[Dict[str, Any]] = []
    ordinals = set()
    for row in rows:
        _strict_keys(
            row,
            ("row_ordinal", "customer_key_hex", "timestamp_utc_microseconds"),
            "INVALID_NORMALIZED_MANIFEST",
        )
        ordinal = row["row_ordinal"]
        key_hex = row["customer_key_hex"]
        timestamp = row["timestamp_utc_microseconds"]
        if (
            type(ordinal) is not int
            or ordinal < 0
            or ordinal in ordinals
            or type(key_hex) is not str
            or not key_hex
            or len(key_hex) > 2048
            or len(key_hex) % 2
            or key_hex != key_hex.lower()
            or any(character not in "0123456789abcdef" for character in key_hex)
            or type(timestamp) is not int
            or timestamp < MIN_SIGNED_64
            or timestamp > MAX_SIGNED_64
        ):
            raise ManifestDraftError("INVALID_NORMALIZED_MANIFEST")
        ordinals.add(ordinal)
        normalized.append(
            {
                "customer_key_hex": key_hex,
                "row_ordinal": ordinal,
                "timestamp_utc_microseconds": timestamp,
            }
        )
    if ordinals != set(range(len(normalized))):
        raise ManifestDraftError("INVALID_NORMALIZED_MANIFEST")
    normalized.sort(key=lambda item: item["row_ordinal"])
    if len({bytes.fromhex(item["customer_key_hex"]) for item in normalized}) < 5:
        raise ManifestDraftError("INSUFFICIENT_CUSTOMER_GROUPS")
    return normalized


def normalize_projection(domain_id: str, rows: Any) -> List[Dict[str, Any]]:
    _contract(domain_id)
    if domain_id == "physionet-challenge-2012":
        return _normalize_physionet(rows)
    return _normalize_retail(rows)


def normalized_projection_sha256(domain_id: str, rows: Any) -> str:
    contract = _contract(domain_id)
    normalized = normalize_projection(domain_id, rows)
    return _sha256(contract["normalized_digest_domain"] + _canonical_bytes(normalized))


def _hamilton_counts(group_count: int) -> Dict[str, int]:
    if type(group_count) is not int or group_count < 5:
        raise ManifestDraftError("INSUFFICIENT_GROUPS")
    counts = [group_count * numerator // DENOMINATOR for numerator in NUMERATORS]
    remainders = [group_count * numerator % DENOMINATOR for numerator in NUMERATORS]
    remaining = group_count - sum(counts)
    priority = sorted(range(3), key=lambda index: (-remainders[index], index))
    for index in priority[:remaining]:
        counts[index] += 1
    if sum(counts) != group_count or any(count <= 0 for count in counts):
        raise ManifestDraftError("INSUFFICIENT_GROUPS")
    return dict(zip(SPLITS, counts))


def _physionet_assignment(rows: Any) -> Dict[str, Any]:
    normalized = _normalize_physionet(rows)
    patient_ids = {row["patient_id"] for row in normalized}
    counts = _hamilton_counts(len(patient_ids))

    def digest(patient_id: str) -> bytes:
        patient_bytes = patient_id.encode("ascii")
        return hashlib.sha256(
            PATIENT_ORDER_DOMAIN
            + len(patient_bytes).to_bytes(2, byteorder="big", signed=False)
            + patient_bytes
        ).digest()

    ordered = sorted(patient_ids, key=lambda item: (digest(item), item.encode("ascii")))
    split_by_patient: Dict[str, str] = {}
    cursor = 0
    for split in SPLITS:
        for patient_id in ordered[cursor : cursor + counts[split]]:
            split_by_patient[patient_id] = split
        cursor += counts[split]
    patient_assignments = [
        {
            "order_sha256": digest(patient_id).hex(),
            "patient_id": patient_id,
            "split": split_by_patient[patient_id],
        }
        for patient_id in sorted(patient_ids, key=lambda item: item.encode("ascii"))
    ]
    record_assignments = [
        {
            "patient_id": row["patient_id"],
            "record_ordinal": row["record_ordinal"],
            "split": split_by_patient[row["patient_id"]],
        }
        for row in normalized
    ]
    payload: Dict[str, Any] = {
        "algorithm_id": DOMAIN_CONTRACTS["physionet-challenge-2012"]["algorithm_id"],
        "input_manifest_sha256": normalized_projection_sha256(
            "physionet-challenge-2012", normalized
        ),
        "outcome": "PASS",
        "patient_assignments": patient_assignments,
        "patient_count": len(patient_assignments),
        "patient_counts": counts,
        "record_assignments": record_assignments,
        "record_count": len(record_assignments),
        "record_counts": {
            split: sum(item["split"] == split for item in record_assignments)
            for split in SPLITS
        },
    }
    result = dict(payload)
    result["assignment_manifest_sha256"] = _sha256(
        DOMAIN_CONTRACTS["physionet-challenge-2012"]["assignment_digest_domain"]
        + _canonical_bytes(payload)
    )
    return result


def _retail_assignment(rows: Any) -> Dict[str, Any]:
    normalized = _normalize_retail(rows)
    customers: Dict[bytes, List[Mapping[str, Any]]] = {}
    for row in normalized:
        customers.setdefault(bytes.fromhex(row["customer_key_hex"]), []).append(row)
    counts = _hamilton_counts(len(customers))
    timestamps = sorted({row["timestamp_utc_microseconds"] for row in normalized})
    intervals = {
        key: (
            min(row["timestamp_utc_microseconds"] for row in group),
            max(row["timestamp_utc_microseconds"] for row in group),
        )
        for key, group in customers.items()
    }
    selected = None
    for first_gap in range(max(0, len(timestamps) - 2)):
        for second_gap in range(first_gap + 1, len(timestamps) - 1):
            assignments: Dict[bytes, str] = {}
            for key, (minimum, maximum) in intervals.items():
                if maximum <= timestamps[first_gap]:
                    assignments[key] = "TRAIN"
                elif minimum >= timestamps[first_gap + 1] and maximum <= timestamps[second_gap]:
                    assignments[key] = "VALIDATION"
                elif minimum >= timestamps[second_gap + 1]:
                    assignments[key] = "TEST"
                else:
                    break
            else:
                observed = {
                    split: sum(value == split for value in assignments.values())
                    for split in SPLITS
                }
                if observed == counts:
                    selected = (first_gap, second_gap, assignments)
                    break
        if selected is not None:
            break
    if selected is None:
        raise ManifestDraftError("NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR")
    first_gap, second_gap, assignments = selected
    row_assignments = [
        {
            "row_ordinal": row["row_ordinal"],
            "split": assignments[bytes.fromhex(row["customer_key_hex"])],
        }
        for row in normalized
    ]
    payload: Dict[str, Any] = {
        "algorithm_id": DOMAIN_CONTRACTS["online-retail-ii"]["algorithm_id"],
        "outcome": "PASS",
        "input_manifest_sha256": normalized_projection_sha256(
            "online-retail-ii", normalized
        ),
        "row_count": len(normalized),
        "customer_count": len(customers),
        "customer_counts": counts,
        "row_counts": {
            split: sum(item["split"] == split for item in row_assignments)
            for split in SPLITS
        },
        "boundary": {
            "train_last_timestamp_utc_microseconds": timestamps[first_gap],
            "validation_first_timestamp_utc_microseconds": timestamps[first_gap + 1],
            "validation_last_timestamp_utc_microseconds": timestamps[second_gap],
            "test_first_timestamp_utc_microseconds": timestamps[second_gap + 1],
        },
        "customer_assignments": [
            {"customer_key_hex": key.hex(), "split": assignments[key]}
            for key in sorted(customers)
        ],
        "row_assignments": row_assignments,
    }
    payload["assignment_manifest_sha256"] = _sha256(
        DOMAIN_CONTRACTS["online-retail-ii"]["assignment_digest_domain"]
        + _canonical_bytes(payload)
    )
    return payload


def exact_assignment(domain_id: str, rows: Any) -> Dict[str, Any]:
    _contract(domain_id)
    if domain_id == "physionet-challenge-2012":
        return _physionet_assignment(rows)
    return _retail_assignment(rows)


SNAPSHOT_KEYS = (
    "schema_version",
    "domain_id",
    "slot_id",
    "receipt_state",
    "receipt_verification_state",
    "custody_class",
    "snapshot_version",
    "source_version_receipt_sha256",
    "raw_snapshot_sha256",
    "raw_snapshot_bytes",
    "archive_inventory_sha256",
    "source_schema_receipt_sha256",
    "license_and_access_receipt_sha256",
    "governance_approval_receipt_sha256",
    "normalization_contract_id",
    "normalized_projection_sha256",
    "normalized_projection_record_count",
    "split_contract_schema_version",
    "splitter_control_predicate",
    "splitter_machine_sha256",
    "post_snapshot_exclusion_count",
    "retry_resplit_topup_count",
    "snapshot_manifest_sha256",
)


def _snapshot_digest(record: Mapping[str, Any]) -> str:
    contract = _contract(record.get("domain_id"))
    payload = dict(record)
    payload.pop("snapshot_manifest_sha256", None)
    return _sha256(contract["snapshot_digest_domain"] + _canonical_bytes(payload))


def validate_snapshot_manifest(record: Any) -> Dict[str, Any]:
    _require_exact_json_tree(
        record, "SNAPSHOT_MANIFEST_EXACT_JSON_TYPE_REQUIRED", allow_none=False
    )
    _strict_keys(record, SNAPSHOT_KEYS, "INVALID_SNAPSHOT_MANIFEST")
    contract = _contract(record["domain_id"])
    expected_verification_state = (
        "SYNTHETIC_NOT_EXTERNAL_EVIDENCE"
        if record["receipt_state"] == "SYNTHETIC_QUALIFICATION_ONLY"
        else "STRUCTURAL_ONLY_NOT_INDEPENDENTLY_VERIFIED"
    )
    if (
        record["schema_version"] != contract["snapshot_schema"]
        or record["slot_id"] != contract["slot_id"]
        or record["receipt_state"] not in RECEIPT_STATES
        or record["receipt_verification_state"] != expected_verification_state
        or record["custody_class"] != "INTERNAL_RESTRICTED_NOT_PUBLICATION_SAFE"
        or record["normalization_contract_id"] != contract["normalization_contract_id"]
        or record["split_contract_schema_version"] != contract["split_schema"]
        or record["splitter_control_predicate"] != contract["splitter_predicate"]
        or record["splitter_machine_sha256"] != contract["splitter_machine_sha256"]
    ):
        raise ManifestDraftError("INVALID_SNAPSHOT_CONTRACT_CROSSLINK")
    _require_ascii(record["snapshot_version"], 128, "INVALID_SNAPSHOT_VERSION")
    for field in (
        "source_version_receipt_sha256",
        "raw_snapshot_sha256",
        "archive_inventory_sha256",
        "source_schema_receipt_sha256",
        "license_and_access_receipt_sha256",
        "governance_approval_receipt_sha256",
        "normalized_projection_sha256",
        "splitter_machine_sha256",
        "snapshot_manifest_sha256",
    ):
        if not _is_sha256(record[field]):
            raise ManifestDraftError("INVALID_SNAPSHOT_HASH_FIELD")
    if (
        type(record["raw_snapshot_bytes"]) is not int
        or record["raw_snapshot_bytes"] <= 0
        or type(record["normalized_projection_record_count"]) is not int
        or record["normalized_projection_record_count"] <= 0
        or type(record["post_snapshot_exclusion_count"]) is not int
        or record["post_snapshot_exclusion_count"] != 0
        or type(record["retry_resplit_topup_count"]) is not int
        or record["retry_resplit_topup_count"] != 0
    ):
        raise ManifestDraftError("INVALID_SNAPSHOT_COUNT_OR_ANTI_SELECTION_FIELD")
    if record["snapshot_manifest_sha256"] != _snapshot_digest(record):
        raise ManifestDraftError("SNAPSHOT_MANIFEST_DIGEST_MISMATCH")
    return dict(record)


def _synthetic_receipt(domain_id: str, label: str, role: str) -> str:
    return _sha256(
        SYNTHETIC_RECEIPT_DOMAIN
        + domain_id.encode("ascii")
        + b"\0"
        + label.encode("ascii")
        + b"\0"
        + role.encode("ascii")
    )


def build_synthetic_snapshot_manifest(
    domain_id: str, rows: Any, synthetic_label: str
) -> Dict[str, Any]:
    contract = _contract(domain_id)
    label = _require_ascii(synthetic_label, 64, "INVALID_SYNTHETIC_LABEL")
    normalized = normalize_projection(domain_id, rows)
    record: Dict[str, Any] = {
        "schema_version": contract["snapshot_schema"],
        "domain_id": domain_id,
        "slot_id": contract["slot_id"],
        "receipt_state": "SYNTHETIC_QUALIFICATION_ONLY",
        "receipt_verification_state": "SYNTHETIC_NOT_EXTERNAL_EVIDENCE",
        "custody_class": "INTERNAL_RESTRICTED_NOT_PUBLICATION_SAFE",
        "snapshot_version": "SYNTHETIC-QUALIFICATION-" + label,
        "source_version_receipt_sha256": _synthetic_receipt(domain_id, label, "SOURCE_VERSION"),
        "raw_snapshot_sha256": _synthetic_receipt(domain_id, label, "RAW_SNAPSHOT"),
        "raw_snapshot_bytes": len(_canonical_bytes(normalized)),
        "archive_inventory_sha256": _synthetic_receipt(domain_id, label, "ARCHIVE_INVENTORY"),
        "source_schema_receipt_sha256": _synthetic_receipt(domain_id, label, "SOURCE_SCHEMA"),
        "license_and_access_receipt_sha256": _synthetic_receipt(domain_id, label, "LICENSE_ACCESS"),
        "governance_approval_receipt_sha256": _synthetic_receipt(domain_id, label, "GOVERNANCE"),
        "normalization_contract_id": contract["normalization_contract_id"],
        "normalized_projection_sha256": normalized_projection_sha256(domain_id, normalized),
        "normalized_projection_record_count": len(normalized),
        "split_contract_schema_version": contract["split_schema"],
        "splitter_control_predicate": contract["splitter_predicate"],
        "splitter_machine_sha256": contract["splitter_machine_sha256"],
        "post_snapshot_exclusion_count": 0,
        "retry_resplit_topup_count": 0,
    }
    record["snapshot_manifest_sha256"] = _snapshot_digest(record)
    return validate_snapshot_manifest(record)


SPLIT_KEYS = (
    "schema_version",
    "domain_id",
    "slot_id",
    "receipt_state",
    "receipt_verification_state",
    "custody_class",
    "snapshot_manifest_sha256",
    "snapshot_normalized_projection_sha256",
    "splitter_control_predicate",
    "splitter_algorithm_id",
    "splitter_machine_sha256",
    "allocation_numerators",
    "allocation_denominator",
    "allocation_power_review_state",
    "allocation_power_review_receipt_sha256",
    "normalized_projection",
    "assignment_output",
    "exclusion_count",
    "retry_count",
    "resplit_count",
    "top_up_count",
    "split_manifest_sha256",
)


def _split_digest(record: Mapping[str, Any]) -> str:
    contract = _contract(record.get("domain_id"))
    payload = dict(record)
    payload.pop("split_manifest_sha256", None)
    return _sha256(contract["split_digest_domain"] + _canonical_bytes(payload))


def validate_split_manifest(record: Any, snapshot: Any) -> Dict[str, Any]:
    _require_exact_json_tree(
        record, "SPLIT_MANIFEST_EXACT_JSON_TYPE_REQUIRED", allow_none=True
    )
    _strict_keys(record, SPLIT_KEYS, "INVALID_SPLIT_MANIFEST")
    canonical_snapshot = validate_snapshot_manifest(snapshot)
    contract = _contract(record["domain_id"])
    synthetic = canonical_snapshot["receipt_state"] == "SYNTHETIC_QUALIFICATION_ONLY"
    expected_power_state = (
        "NOT_POWER_APPROVED"
        if synthetic
        else "STRUCTURALLY_BOUND_NOT_INDEPENDENTLY_VERIFIED"
    )
    if (
        record["schema_version"] != contract["split_schema"]
        or record["domain_id"] != canonical_snapshot["domain_id"]
        or record["slot_id"] != contract["slot_id"]
        or record["receipt_state"] != canonical_snapshot["receipt_state"]
        or record["receipt_verification_state"]
        != canonical_snapshot["receipt_verification_state"]
        or record["custody_class"] != "INTERNAL_RESTRICTED_NOT_PUBLICATION_SAFE"
        or record["snapshot_manifest_sha256"] != canonical_snapshot["snapshot_manifest_sha256"]
        or record["snapshot_normalized_projection_sha256"]
        != canonical_snapshot["normalized_projection_sha256"]
        or record["splitter_control_predicate"] != contract["splitter_predicate"]
        or record["splitter_algorithm_id"] != contract["algorithm_id"]
        or record["splitter_machine_sha256"] != contract["splitter_machine_sha256"]
        or record["allocation_numerators"] != list(NUMERATORS)
        or record["allocation_denominator"] != DENOMINATOR
        or record["allocation_power_review_state"] != expected_power_state
    ):
        raise ManifestDraftError("INVALID_SPLIT_CONTRACT_CROSSLINK")
    if synthetic:
        if record["allocation_power_review_receipt_sha256"] is not None:
            raise ManifestDraftError("SYNTHETIC_ALLOCATION_MUST_NOT_HAVE_POWER_RECEIPT")
    elif not _is_sha256(record["allocation_power_review_receipt_sha256"]):
        raise ManifestDraftError("FUTURE_ALLOCATION_POWER_RECEIPT_REQUIRED")
    for field in (
        "snapshot_manifest_sha256",
        "snapshot_normalized_projection_sha256",
        "splitter_machine_sha256",
        "split_manifest_sha256",
    ):
        if not _is_sha256(record[field]):
            raise ManifestDraftError("INVALID_SPLIT_HASH_FIELD")
    for field in ("exclusion_count", "retry_count", "resplit_count", "top_up_count"):
        if type(record[field]) is not int or record[field] != 0:
            raise ManifestDraftError("ANTI_SELECTION_COUNT_MUST_BE_ZERO")
    normalized = normalize_projection(record["domain_id"], record["normalized_projection"])
    if (
        len(normalized) != canonical_snapshot["normalized_projection_record_count"]
        or normalized_projection_sha256(record["domain_id"], normalized)
        != canonical_snapshot["normalized_projection_sha256"]
    ):
        raise ManifestDraftError("SNAPSHOT_SPLIT_PROJECTION_MISMATCH")
    expected_assignment = exact_assignment(record["domain_id"], normalized)
    if type(record["assignment_output"]) is not dict or record["assignment_output"] != expected_assignment:
        raise ManifestDraftError("ASSIGNMENT_DOES_NOT_MATCH_FROZEN_SPLITTER_CONTRACT")
    if record["split_manifest_sha256"] != _split_digest(record):
        raise ManifestDraftError("SPLIT_MANIFEST_DIGEST_MISMATCH")
    return dict(record)


def build_split_manifest(
    snapshot: Any, rows: Any
) -> Dict[str, Any]:
    canonical_snapshot = validate_snapshot_manifest(snapshot)
    if canonical_snapshot["receipt_state"] != "SYNTHETIC_QUALIFICATION_ONLY":
        raise ManifestDraftError("FUTURE_MANIFEST_CONSTRUCTION_NOT_AUTHORIZED")
    domain_id = canonical_snapshot["domain_id"]
    contract = _contract(domain_id)
    normalized = normalize_projection(domain_id, rows)
    if (
        len(normalized) != canonical_snapshot["normalized_projection_record_count"]
        or normalized_projection_sha256(domain_id, normalized)
        != canonical_snapshot["normalized_projection_sha256"]
    ):
        raise ManifestDraftError("SNAPSHOT_SPLIT_PROJECTION_MISMATCH")
    record: Dict[str, Any] = {
        "schema_version": contract["split_schema"],
        "domain_id": domain_id,
        "slot_id": contract["slot_id"],
        "receipt_state": canonical_snapshot["receipt_state"],
        "receipt_verification_state": canonical_snapshot["receipt_verification_state"],
        "custody_class": "INTERNAL_RESTRICTED_NOT_PUBLICATION_SAFE",
        "snapshot_manifest_sha256": canonical_snapshot["snapshot_manifest_sha256"],
        "snapshot_normalized_projection_sha256": canonical_snapshot["normalized_projection_sha256"],
        "splitter_control_predicate": contract["splitter_predicate"],
        "splitter_algorithm_id": contract["algorithm_id"],
        "splitter_machine_sha256": contract["splitter_machine_sha256"],
        "allocation_numerators": list(NUMERATORS),
        "allocation_denominator": DENOMINATOR,
        "allocation_power_review_state": "NOT_POWER_APPROVED",
        "allocation_power_review_receipt_sha256": None,
        "normalized_projection": normalized,
        "assignment_output": exact_assignment(domain_id, normalized),
        "exclusion_count": 0,
        "retry_count": 0,
        "resplit_count": 0,
        "top_up_count": 0,
    }
    record["split_manifest_sha256"] = _split_digest(record)
    return validate_split_manifest(record, canonical_snapshot)


def retail_task_schema_route_draft() -> Dict[str, Any]:
    return {
        "route_id": "RETAIL_CUSTOMER_EVENT_CONFIGURATION_TASK_SCHEMA_ROUTE_DRAFT_V1",
        "domain_id": "online-retail-ii",
        "slot_id": "R4-RETAIL",
        "route_state": "AGENT_SELECTED_CANDIDATE_AWAITING_ALL_TYPED_SOURCE_RECEIPTS",
        "unit_of_analysis_candidate": "CANONICAL_CUSTOMER_GROUP",
        "generated_endpoint_Y_candidate": (
            "COMPLETE_ADMITTED_CUSTOMER_TRANSACTION_LINE_ITEM_EVENT_CONFIGURATION"
        ),
        "context_z_candidate": "FUTURE_FROZEN_CONTEXT_SCHEMA_RECEIPT_REQUIRED",
        "observation_A_candidate": (
            "FUTURE_APPLICATION_JUSTIFIED_PARTIAL_OBSERVATION_KERNEL_RECEIPT_REQUIRED"
        ),
        "source_field_schema_or_semantics_verified": False,
        "cancellation_country_simultaneity_or_timezone_facts_asserted": False,
        "future_typed_receipts": [
            {
                "field_id": field_id,
                "pointer": pointer,
                "required_type": required_type,
                "state": "OPEN_FUTURE_TYPED_RECEIPT_REQUIRED",
                "value": None,
            }
            for field_id, pointer, required_type in RETAIL_TASK_FUTURE_FIELDS
        ],
        "failure_disposition": "RETAIL_DOMAIN_NO_GO_NO_EXCLUSION_RETRY_RESPLIT_OR_TOPUP",
        "domain_admitted": False,
        "scientific_effect": 0,
    }


def validate_manifest_pair(snapshot: Any, split: Any) -> Dict[str, Any]:
    canonical_snapshot = validate_snapshot_manifest(snapshot)
    canonical_split = validate_split_manifest(split, canonical_snapshot)
    return {
        "domain_id": canonical_snapshot["domain_id"],
        "snapshot_manifest_sha256": canonical_snapshot["snapshot_manifest_sha256"],
        "split_manifest_sha256": canonical_split["split_manifest_sha256"],
        "receipt_state": canonical_snapshot["receipt_state"],
        "crosslink_valid": True,
        "all_rows_preserved": True,
        "exclusion_retry_resplit_or_topup_performed": False,
        "structural_validation_only": True,
        "source_license_governance_custody_or_admission_verified": False,
        "allocation_power_approved": False,
        "allocation_power_receipt_independently_verified": False,
        "F061_closed": False,
        "domain_admitted": False,
        "scientific_effect": 0,
    }
