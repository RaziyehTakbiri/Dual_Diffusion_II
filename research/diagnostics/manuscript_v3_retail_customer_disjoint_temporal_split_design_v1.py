"""Pure Retail split design plus read-only static-package validator.

The splitter accepts only caller-supplied normalized synthetic manifests.  The
validator reopens a fixed predecessor/package roster.  Neither route opens raw
data or exposes a writer, network, connector, subprocess, entropy, authority,
runtime, training, or scientific action.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Optional, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-retail-customer-disjoint-temporal-split-design-v1"
STATE = (
    "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN_FROZEN_AND_"
    "SYNTHETICALLY_QUALIFIED_NO_DATA_ACCESS"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
PACKAGE_KIND = "STATIC_RETAIL_SPLIT_DESIGN_AND_SYNTHETIC_QUALIFICATION_ONLY"
REPORTED_DATE = "2026-08-30"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
INPUT_DOMAIN = b"heterodiff/retail-normalized-split-input/v1\0"
ASSIGNMENT_DOMAIN = b"heterodiff/retail-customer-temporal-assignment/v1\0"
ALGORITHM_ID = "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_HAMILTON_70_15_15_V1"
CONTROL_PREDICATE = (
    "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN_AND_"
    "SYNTHETIC_QUALIFICATION_VALIDATED"
)

HUMAN_PATH = "PROJECT_RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN.md"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py"
)

PREREGISTRATION_PATH = (
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
)
CLOSURE_PATH = (
    "research/fixtures/"
    "manuscript_v3_execution_preregistration_preexecution_closure_v2.json"
)
SEAL_HUMAN_PATH = "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md"
SEAL_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json"
)
SEAL_VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py"
)
SEAL_TEST_PATH = (
    "tests/unit/test_manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py"
)
STATIC_HUMAN_PATH = "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md"
STATIC_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json"
)
STATIC_VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_solo_block2_static_selection_freeze_v1.py"
)
STATIC_TEST_PATH = (
    "tests/unit/test_manuscript_v3_solo_block2_static_selection_freeze_v1.py"
)
CANDIDATE_HUMAN_PATH = "PROJECT_SOLO_BLOCK2_PRECONTACT_INSTANCE_CANDIDATE.md"
CANDIDATE_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_solo_block2_precontact_instance_candidate_v1.json"
)
CANDIDATE_VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_solo_block2_precontact_instance_candidate_v1.py"
)
CANDIDATE_TEST_PATH = (
    "tests/unit/test_manuscript_v3_solo_block2_precontact_instance_candidate_v1.py"
)

NORMALIZED_AUTHORITY_TEXT = "Alright, sounds good. Go ahead then."
AUTHORITY_TEXT_SHA256 = (
    "834e4a9458adde27cebea9341c11ef09e49dc04dbfb2d7b9a05ed9108a16413b"
)
RETAIL_URL = "https://archive.ics.uci.edu/dataset/502/online+retail+ii"
SPLIT_NAMES = ("TRAIN", "VALIDATION", "TEST")
SPLIT_NUMERATORS = (70, 15, 15)
DENOMINATOR = 100
MINIMUM_CUSTOMER_COUNT = 5
ROW_KEYS = {"row_ordinal", "customer_key_hex", "timestamp_utc_microseconds"}
MIN_SIGNED_64 = -(2**63)
MAX_SIGNED_64 = 2**63 - 1


class ValidationError(ValueError):
    """Raised when static package custody or semantics fail closed."""


class SplitDesignError(ValueError):
    """Typed fail-closed result for a normalized synthetic manifest."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_json_bytes(record) + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _canonical_json_bytes(payload))


def _self_digest(record: Mapping[str, Any]) -> str:
    schema = record.get("schema_version")
    if type(schema) is not str or not schema.isascii():
        raise ValidationError("self schema invalid")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256((schema + "\0").encode("ascii") + _canonical_json_bytes(payload))


def _strict_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if set(actual) != set(expected):
            raise ValidationError(label + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + key)
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for index, (item, wanted) in enumerate(zip(actual, expected)):
            _strict_equal(item, wanted, label + "[" + str(index) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def hamilton_customer_counts(customer_count: int) -> Dict[str, int]:
    """Return exact 70/15/15 Hamilton counts or fail closed."""

    if type(customer_count) is not int or customer_count < MINIMUM_CUSTOMER_COUNT:
        raise SplitDesignError("INSUFFICIENT_CUSTOMER_GROUPS")
    floors = [
        customer_count * numerator // DENOMINATOR
        for numerator in SPLIT_NUMERATORS
    ]
    remainders = [
        customer_count * numerator % DENOMINATOR
        for numerator in SPLIT_NUMERATORS
    ]
    seats = customer_count - sum(floors)
    order = sorted(range(3), key=lambda index: (-remainders[index], index))
    for index in order[:seats]:
        floors[index] += 1
    if sum(floors) != customer_count or any(count <= 0 for count in floors):
        raise SplitDesignError("INSUFFICIENT_CUSTOMER_GROUPS")
    return {name: floors[index] for index, name in enumerate(SPLIT_NAMES)}


def _normalize_rows(rows: Any) -> Tuple[List[Dict[str, Any]], Dict[bytes, List[Dict[str, Any]]]]:
    if type(rows) is not list or not rows:
        raise SplitDesignError("INVALID_NORMALIZED_MANIFEST")
    normalized: List[Dict[str, Any]] = []
    decoded_keys: Dict[int, bytes] = {}
    for row in rows:
        if type(row) is not dict or set(row) != ROW_KEYS:
            raise SplitDesignError("INVALID_NORMALIZED_MANIFEST")
        ordinal = row["row_ordinal"]
        key_hex = row["customer_key_hex"]
        timestamp = row["timestamp_utc_microseconds"]
        if type(ordinal) is not int or ordinal < 0:
            raise SplitDesignError("INVALID_NORMALIZED_MANIFEST")
        if (
            type(key_hex) is not str
            or not key_hex
            or len(key_hex) > 2048
            or len(key_hex) % 2 != 0
            or key_hex != key_hex.lower()
            or any(character not in "0123456789abcdef" for character in key_hex)
        ):
            raise SplitDesignError("INVALID_NORMALIZED_MANIFEST")
        if (
            type(timestamp) is not int
            or timestamp < MIN_SIGNED_64
            or timestamp > MAX_SIGNED_64
        ):
            raise SplitDesignError("INVALID_NORMALIZED_MANIFEST")
        key_bytes = bytes.fromhex(key_hex)
        if not key_bytes:
            raise SplitDesignError("INVALID_NORMALIZED_MANIFEST")
        decoded_keys[ordinal] = key_bytes
        normalized.append(
            {
                "row_ordinal": ordinal,
                "customer_key_hex": key_hex,
                "timestamp_utc_microseconds": timestamp,
            }
        )
    normalized.sort(key=lambda row: row["row_ordinal"])
    if [row["row_ordinal"] for row in normalized] != list(range(len(normalized))):
        raise SplitDesignError("INVALID_NORMALIZED_MANIFEST")
    customers: Dict[bytes, List[Dict[str, Any]]] = {}
    for row in normalized:
        key_bytes = decoded_keys[row["row_ordinal"]]
        customers.setdefault(key_bytes, []).append(row)
    return normalized, customers


def split_retail_rows(rows: Any) -> Dict[str, Any]:
    """Apply the exact pure split rule to one normalized synthetic manifest."""

    normalized, customers = _normalize_rows(rows)
    customer_counts = hamilton_customer_counts(len(customers))
    timestamps = sorted({row["timestamp_utc_microseconds"] for row in normalized})
    if len(timestamps) < 3:
        raise SplitDesignError(
            "NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR"
        )
    intervals = {
        key: (
            min(row["timestamp_utc_microseconds"] for row in customer_rows),
            max(row["timestamp_utc_microseconds"] for row in customer_rows),
        )
        for key, customer_rows in customers.items()
    }

    selected: Optional[Tuple[int, int, Dict[bytes, str]]] = None
    for first_gap in range(len(timestamps) - 2):
        for second_gap in range(first_gap + 1, len(timestamps) - 1):
            first_left = timestamps[first_gap]
            first_right = timestamps[first_gap + 1]
            second_left = timestamps[second_gap]
            second_right = timestamps[second_gap + 1]
            assignments: Dict[bytes, str] = {}
            feasible = True
            for key, (minimum, maximum) in intervals.items():
                if maximum <= first_left:
                    assignments[key] = "TRAIN"
                elif minimum >= first_right and maximum <= second_left:
                    assignments[key] = "VALIDATION"
                elif minimum >= second_right:
                    assignments[key] = "TEST"
                else:
                    feasible = False
                    break
            if not feasible:
                continue
            observed_counts = {
                name: sum(value == name for value in assignments.values())
                for name in SPLIT_NAMES
            }
            if observed_counts != customer_counts:
                continue
            selected = (first_gap, second_gap, assignments)
            break
        if selected is not None:
            break

    if selected is None:
        raise SplitDesignError(
            "NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR"
        )

    first_gap, second_gap, assignments = selected
    row_assignments = [
        {
            "row_ordinal": row["row_ordinal"],
            "split": assignments[bytes.fromhex(row["customer_key_hex"])],
        }
        for row in normalized
    ]
    customer_assignments = [
        {"customer_key_hex": key.hex(), "split": assignments[key]}
        for key in sorted(customers)
    ]
    row_counts = {
        name: sum(row["split"] == name for row in row_assignments)
        for name in SPLIT_NAMES
    }
    if len(row_assignments) != len(normalized):
        raise SplitDesignError("INTERNAL_ALL_ROW_PRESERVATION_FAILURE")
    if {row["row_ordinal"] for row in row_assignments} != set(range(len(normalized))):
        raise SplitDesignError("INTERNAL_ALL_ROW_PRESERVATION_FAILURE")
    for name in SPLIT_NAMES:
        if row_counts[name] <= 0:
            raise SplitDesignError("INTERNAL_TEMPORAL_INVARIANT_FAILURE")
    split_timestamps = {
        name: [
            normalized[row["row_ordinal"]]["timestamp_utc_microseconds"]
            for row in row_assignments
            if row["split"] == name
        ]
        for name in SPLIT_NAMES
    }
    if not (
        max(split_timestamps["TRAIN"]) < min(split_timestamps["VALIDATION"])
        and max(split_timestamps["VALIDATION"]) < min(split_timestamps["TEST"])
    ):
        raise SplitDesignError("INTERNAL_TEMPORAL_INVARIANT_FAILURE")

    payload: Dict[str, Any] = {
        "algorithm_id": ALGORITHM_ID,
        "outcome": "PASS",
        "input_manifest_sha256": _sha256(
            INPUT_DOMAIN + _canonical_json_bytes(normalized)
        ),
        "row_count": len(normalized),
        "customer_count": len(customers),
        "customer_counts": customer_counts,
        "row_counts": row_counts,
        "boundary": {
            "train_last_timestamp_utc_microseconds": timestamps[first_gap],
            "validation_first_timestamp_utc_microseconds": timestamps[first_gap + 1],
            "validation_last_timestamp_utc_microseconds": timestamps[second_gap],
            "test_first_timestamp_utc_microseconds": timestamps[second_gap + 1],
        },
        "customer_assignments": customer_assignments,
        "row_assignments": row_assignments,
    }
    payload["assignment_manifest_sha256"] = _sha256(
        ASSIGNMENT_DOMAIN + _canonical_json_bytes(payload)
    )
    return payload


def _safe_relative_path(root: Path, relative_path: str) -> Path:
    if type(relative_path) is not str:
        raise ValidationError("path type invalid")
    rel = Path(relative_path)
    if rel.is_absolute() or not rel.parts or ".." in rel.parts:
        raise ValidationError("unsafe path")
    return root.joinpath(*rel.parts)


def _ancestor_snapshot(root: Path, path: Path) -> Tuple[Tuple[Any, ...], ...]:
    rows: List[Tuple[Any, ...]] = []
    current = path.parent
    while True:
        status = current.lstat()
        if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
            raise ValidationError("unsafe ancestor")
        rows.append(
            (
                str(current),
                status.st_dev,
                status.st_ino,
                stat.S_IFMT(status.st_mode),
                stat.S_IMODE(status.st_mode),
                status.st_uid,
                status.st_gid,
            )
        )
        if current == root:
            break
        if root not in current.parents:
            raise ValidationError("path escaped root")
        current = current.parent
    return tuple(reversed(rows))


def _leaf_fingerprint(status: os.stat_result) -> Tuple[Any, ...]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        stat.S_IMODE(status.st_mode),
        status.st_uid,
        status.st_gid,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _stable_read(root: Path, relative_path: str) -> bytes:
    path = _safe_relative_path(root, relative_path)
    ancestors = _ancestor_snapshot(root, path)
    before_path = path.lstat()
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != 0o644
        or before_path.st_nlink != 1
    ):
        raise ValidationError("file custody invalid: " + relative_path)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        before_fd = os.fstat(descriptor)
        chunks: List[bytes] = []
        while True:
            chunk = os.read(descriptor, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    raw = b"".join(chunks)
    fingerprint = _leaf_fingerprint(before_path)
    if not (
        fingerprint
        == _leaf_fingerprint(before_fd)
        == _leaf_fingerprint(after_fd)
        == _leaf_fingerprint(after_path)
    ):
        raise ValidationError("file changed during read: " + relative_path)
    if len(raw) != before_fd.st_size:
        raise ValidationError("short read: " + relative_path)
    if ancestors != _ancestor_snapshot(root, path):
        raise ValidationError("ancestor changed during read")
    return raw


def _binding(
    ordinal: int,
    role: str,
    path: str,
    raw: bytes,
    *,
    self_digest: Optional[str] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "ordinal": ordinal,
        "role": role,
        "path": path,
        "bytes": len(raw),
        "raw_sha256": _sha256(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": raw.endswith(b"\n"),
    }
    if self_digest is not None:
        row["record_sha256"] = self_digest
    return row


LIVE_IMMUTABLE_BINDINGS: Tuple[Mapping[str, Any], ...] = (
    {"ordinal": 0, "role": "EXECUTION_PREREGISTRATION", "path": PREREGISTRATION_PATH, "bytes": 39771, "raw_sha256": "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 1, "role": "PREEXECUTION_CLOSURE", "path": CLOSURE_PATH, "bytes": 24571, "raw_sha256": "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "record_sha256": "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4"},
    {"ordinal": 2, "role": "PROSPECTIVE_SEAL_HUMAN", "path": SEAL_HUMAN_PATH, "bytes": 7078, "raw_sha256": "ad58c5fcb9d47531a7af041eb59f71386fd42a81b1fe31701df167f064f951c2", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 3, "role": "PROSPECTIVE_SEAL_MACHINE", "path": SEAL_MACHINE_PATH, "bytes": 8461, "raw_sha256": "0357fc48394d5888632e3e2d7f5c9180e683141ebc10bef3dec9879a58cdf0e8", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "record_sha256": "d11d5336f1ede024ab56f92bc64e620681e53fc406fd954aa3da36b7861485a6"},
    {"ordinal": 4, "role": "PROSPECTIVE_SEAL_VALIDATOR", "path": SEAL_VALIDATOR_PATH, "bytes": 32156, "raw_sha256": "3647c367506519149d5df60dc2dcfb07a8f5dc976526b88700321b0de89a2258", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 5, "role": "PROSPECTIVE_SEAL_HOSTILE_TEST", "path": SEAL_TEST_PATH, "bytes": 16698, "raw_sha256": "2285525223f42154553a0302bb46a8f04f0ff7ff35233906a37f4f1a9bf47403", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 6, "role": "STATIC_SELECTION_HUMAN", "path": STATIC_HUMAN_PATH, "bytes": 23012, "raw_sha256": "ab80a009f3d83be4186d3d2da13e3efd5939362e4215477dd2b1a89b870b3126", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 7, "role": "STATIC_SELECTION_MACHINE", "path": STATIC_MACHINE_PATH, "bytes": 33638, "raw_sha256": "7ff0bf3bb5d9a03e2212f2f7f1853cde2283694b33e072931d258d98e1882590", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "record_sha256": "1f02200d524749d6708695072dfbc8b785a6f03d5be908b3563f121d7fcd5b53"},
    {"ordinal": 8, "role": "STATIC_SELECTION_VALIDATOR", "path": STATIC_VALIDATOR_PATH, "bytes": 56344, "raw_sha256": "8843cef229c24cbd25cd00e55697755c8fc7a1247f20044dfe110e182e558ec0", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 9, "role": "STATIC_SELECTION_HOSTILE_TEST", "path": STATIC_TEST_PATH, "bytes": 48158, "raw_sha256": "801fc7c87f57eb72da6cdfa7b2be93c6edd66b974fefe47dabbe5b91eaa0f005", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 10, "role": "PRECONTACT_CANDIDATE_HUMAN", "path": CANDIDATE_HUMAN_PATH, "bytes": 17965, "raw_sha256": "ed211b7bf5aaf45a839e18d15484177fa0c51d7cb95540cdccc61587b2b8250f", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 11, "role": "PRECONTACT_CANDIDATE_MACHINE", "path": CANDIDATE_MACHINE_PATH, "bytes": 23932, "raw_sha256": "95bae0a0ff0d5a199afc23cfc048de04cce28c47300ada301b927c21c60166be", "mode_octal": "0644", "nlink": 1, "trailing_lf": True, "record_sha256": "2c4c068c553bdfab04d49f01163c84923b9108b2f762872ba00015c2fadd9304"},
    {"ordinal": 12, "role": "PRECONTACT_CANDIDATE_VALIDATOR", "path": CANDIDATE_VALIDATOR_PATH, "bytes": 46460, "raw_sha256": "6bdfe3c943c8238d88dc5fba908918d9304ab9f377517a483c65cfac887a39dc", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
    {"ordinal": 13, "role": "PRECONTACT_CANDIDATE_HOSTILE_TEST", "path": CANDIDATE_TEST_PATH, "bytes": 27389, "raw_sha256": "40ba6642f81323fb9254520113697785513bb705e72232731657ae1c481d2856", "mode_octal": "0644", "nlink": 1, "trailing_lf": True},
)


EXPECTED_AUTHORITY: Mapping[str, Any] = {
    "normalized_visible_text": NORMALIZED_AUTHORITY_TEXT,
    "normalized_visible_text_utf8_bytes": 36,
    "normalized_visible_text_sha256": AUTHORITY_TEXT_SHA256,
    "normalization": "TRAILING_HTML_SPACE_ENTITY_AND_TRANSPORT_WHITESPACE_REMOVED_ONLY",
    "raw_transport_bytes_bound": False,
    "conversation_envelope_bound": False,
    "account_identity_bound": False,
    "timestamp_bound": False,
    "cryptographic_user_authentication_claimed": False,
    "retail_static_design_and_synthetic_qualification_authorized": True,
    "external_contact_or_browsing_authorized": False,
    "data_access_or_real_split_authorized": False,
    "tracker_edit_authorized": False,
    "scientific_execution_authorized": False,
    "user_selected_paths_schema_or_algorithm_details": False,
    "agent_selected_bounded_implementation_details": True,
}


EXPECTED_IDENTITY: Mapping[str, Any] = {
    "algorithm_id": ALGORITHM_ID,
    "design_frozen": True,
    "pure_implementation_present": True,
    "synthetic_qualification_present": True,
    "real_retail_snapshot_opened": False,
    "real_retail_feasibility_observed": False,
    "real_split_performed": False,
    "raw_to_normalized_parser_present": False,
    "production_runner_present": False,
    "split_manifest_persisted": False,
    "power_justified": False,
    "domain_admitted": False,
    "candidate_precontact_package_modified": False,
}


EXPECTED_MANIFEST: Mapping[str, Any] = {
    "input_kind": "CALLER_SUPPLIED_FINITE_NORMALIZED_ROW_PROJECTION",
    "exact_row_keys": ["row_ordinal", "customer_key_hex", "timestamp_utc_microseconds"],
    "row_ordinals": "STRICT_INTEGERS_EXACT_SET_0_THROUGH_R_MINUS_1_INPUT_ORDER_IRRELEVANT",
    "customer_key": "NONEMPTY_LOWERCASE_EVEN_LENGTH_HEX_OF_OPAQUE_CANONICAL_BYTES_MAX_2048_CHARS",
    "timestamp": "STRICT_SIGNED_64_BIT_UTC_MICROSECONDS_SINCE_UNIX_EPOCH",
    "future_raw_to_manifest_binding_required": True,
    "future_manifest_must_cover_every_snapshot_row": True,
    "missing_invalid_ambiguous_or_unrepresentable_row_disposition": "WHOLE_MANIFEST_INVALID_DOMAIN_NO_GO",
    "row_quarantine_censoring_exclusion_repair_or_reassignment_permitted": False,
    "extra_label_outcome_prediction_loss_test_indicator_fields_accepted": False,
    "real_manifest_present": False,
    "real_manifest_sha256": None,
}


EXPECTED_HAMILTON: Mapping[str, Any] = {
    "split_names": list(SPLIT_NAMES),
    "numerators": list(SPLIT_NUMERATORS),
    "denominator": DENOMINATOR,
    "floor_rule": "INTEGER_FLOOR_N_TIMES_NUMERATOR_DIVIDED_BY_100",
    "remainder_rule": "DESCENDING_INTEGER_REMAINDER",
    "tie_priority": list(SPLIT_NAMES),
    "minimum_customer_count": MINIMUM_CUSTOMER_COUNT,
    "all_three_counts_strictly_positive_required": True,
    "seed_or_entropy_used": False,
    "alternate_proportion_after_observation_permitted": False,
}


EXPECTED_BOUNDARY: Mapping[str, Any] = {
    "customer_interval": "CLOSED_MINIMUM_TO_MAXIMUM_UTC_MICROSECOND_INTERVAL_OVER_ALL_CUSTOMER_ROWS",
    "candidate_timestamps": "SORTED_DISTINCT_OBSERVED_ROW_TIMESTAMPS",
    "candidate_gap_pairs": "ALL_ORDERED_GAP_INDEX_PAIRS_0_LE_G1_LT_G2_LE_M_MINUS_2",
    "train_window": "T_LE_T_G1",
    "validation_window": "T_G1_LT_T_LE_T_G2",
    "test_window": "T_GT_T_G2",
    "boundary_spanning_customer_makes_pair_infeasible": True,
    "feasibility_requirements": [
        "EVERY_COMPLETE_CUSTOMER_INTERVAL_IN_EXACTLY_ONE_WINDOW",
        "EVERY_INPUT_ROW_ASSIGNED_EXACTLY_ONCE",
        "CUSTOMER_SETS_PAIRWISE_DISJOINT_AND_COMPLETE",
        "CUSTOMER_COUNTS_EQUAL_EXACT_HAMILTON_COUNTS",
        "ALL_ROW_AND_CUSTOMER_COUNTS_POSITIVE",
        "MAX_TRAIN_TIMESTAMP_STRICTLY_BELOW_MIN_VALIDATION_TIMESTAMP",
        "MAX_VALIDATION_TIMESTAMP_STRICTLY_BELOW_MIN_TEST_TIMESTAMP",
    ],
    "selection_order": "LEXICOGRAPHIC_T_G1_T_G1_PLUS_1_T_G2_T_G2_PLUS_1",
    "outcome_label_or_model_result_used": False,
    "no_feasible_pair_code": "NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR",
    "fallback_relaxation_retry_exclusion_censoring_quarantine_or_reassignment_permitted": False,
}


EXPECTED_OUTPUT: Mapping[str, Any] = {
    "output_kind": "CANONICAL_IN_MEMORY_INTERNAL_NORMALIZED_ASSIGNMENT_NOT_PUBLICATION_SAFE",
    "exact_fields": [
        "algorithm_id",
        "outcome",
        "input_manifest_sha256",
        "row_count",
        "customer_count",
        "customer_counts",
        "row_counts",
        "boundary",
        "customer_assignments",
        "row_assignments",
        "assignment_manifest_sha256",
    ],
    "input_digest_domain": INPUT_DOMAIN[:-1].decode("ascii"),
    "assignment_digest_domain": ASSIGNMENT_DOMAIN[:-1].decode("ascii"),
    "customer_assignment_order": "DECODED_CUSTOMER_KEY_BYTES_ASCENDING",
    "row_assignment_order": "ROW_ORDINAL_ASCENDING",
    "all_rows_preserved": True,
    "file_or_external_effect": False,
    "real_output_present": False,
}


EXPECTED_FAILURE: Mapping[str, Any] = {
    "invalid_manifest_code": "INVALID_NORMALIZED_MANIFEST",
    "insufficient_customer_code": "INSUFFICIENT_CUSTOMER_GROUPS",
    "no_feasible_pair_code": "NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR",
    "internal_all_row_preservation_code": "INTERNAL_ALL_ROW_PRESERVATION_FAILURE",
    "internal_temporal_invariant_code": "INTERNAL_TEMPORAL_INVARIANT_FAILURE",
    "failure_is_terminal_no_go_for_this_rule": True,
    "fallback_retry_boundary_relaxation_resplit_customer_migration_or_row_exclusion_permitted": False,
}


EXPECTED_QUALIFICATION: Mapping[str, Any] = {
    "synthetic_rows_only": True,
    "real_data_fixture_opened": False,
    "ordinary_software_qualification_interpreter_processes_performed": True,
    "pytest_temporary_fixtures_used": True,
    "global_workspace_write_absence_claimed": False,
    "validator_source_process_network_or_writer_exposed": False,
    "hostile_test_source_process_or_network_exposed": False,
    "hostile_test_writer_scope": "PYTEST_TEMPORARY_REPLICAS_ONLY",
    "qualification_python_bytecode_disabled": True,
    "qualification_pytest_cacheprovider_disabled": True,
    "cases": [
        "CONSTRUCTIVE_FEASIBLE",
        "MULTIROW_CUSTOMER_GROUPING",
        "INTERLEAVED_INTERVAL_NO_FEASIBLE_PAIR",
        "EQUAL_BOUNDARY_TIMESTAMP_INFEASIBLE",
        "MINIMUM_CUSTOMER_COUNT",
        "HAMILTON_REMAINDER_AND_TIE_PRIORITY",
        "INVALID_MISSING_EXTRA_BOOL_OVERFLOW_DUPLICATE_ORDINAL_KEY_CASES",
        "ALL_ROW_AND_CUSTOMER_PRESERVATION",
        "INPUT_PERMUTATION_INVARIANCE",
        "LABEL_OUTCOME_AND_TEST_INDICATOR_REJECTION",
        "NO_FEASIBLE_PAIR_TERMINAL_NO_GO",
        "STATIC_CUSTODY_AND_SOURCE_SAFETY",
    ],
    "real_snapshot_contract_satisfied": False,
    "real_feasible_boundary_pair_exists": None,
    "scientific_or_domain_admission_evidence": False,
}


EXPECTED_PREDECESSOR_EFFECTS: Mapping[str, Any] = {
    "candidate_predecessor_state": "PRECONTACT_INSTANCE_LOCAL_CANDIDATE_COMPLETE_AWAITING_PRECONTACT_PREREQUISITES_AND_INDEPENDENT_REVIEW",
    "candidate_predecessor_modified": False,
    "candidate_retail_design_seam_closed_additively": True,
    "candidate_approval_roster_seam_closed": False,
    "candidate_power_seam_closed": False,
    "candidate_real_escrow_seam_closed": False,
    "candidate_population_or_admission_changed": False,
    "candidate_four_row_operation_roster_changed": False,
}


EXPECTED_CHECKLIST: Mapping[str, Any] = {
    "project_control_predicate": CONTROL_PREDICATE,
    "project_control_predicate_value_after_validation": True,
    "targeted_project_location": "B03_F060_F061_RETAIL_TEMPORAL_AND_ALLOCATION_SPLIT_DESIGN",
    "f060_value_written_into_immutable_preregistration": False,
    "f061_value_written_into_immutable_preregistration": False,
    "unresolved_fields_closed": 0,
    "blockers_closed": 0,
    "formal_tests_closed": 0,
    "results_filled": 0,
    "effective_unresolved_field_count": 172,
    "effective_open_blocker_count": 12,
    "original_populated_instance_checkbox_closed": False,
    "precontact_population_blocked": True,
    "power_review_complete": False,
    "domain_admission_complete": False,
    "external_contact_data_access_or_science_performed": False,
    "tracker_edit_performed": False,
}


EXPECTED_SCOPE: Mapping[str, Any] = {
    "separately_authorized_b03_f060_f061_design_artifact": True,
    "characterized_as_third_precontact_micro_layer": False,
    "four_files_form_one_validation_package": True,
    "existing_file_modified": False,
    "tracker_reverse_binding_present": False,
    "real_data_or_source_absence_is_not_permanent_future_gate": True,
}


EXPECTED_ANONYMITY: Mapping[str, Any] = {
    "package_internal_only": True,
    "anonymous_or_public_supplement": False,
    "publication_safe_derivative_required": True,
    "real_customer_key_timestamp_or_row_present": False,
    "credentials_tokens_or_key_material_present": False,
    "source_response_or_receipt_present": False,
    "protected_outcome_or_scientific_result_present": False,
    "local_absolute_path_present": False,
}


EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "state",
    "global_state",
    "package_kind",
    "reported_date",
    "authority_provenance",
    "live_immutable_input_bindings",
    "design_identity",
    "normalized_manifest_contract",
    "hamilton_allocation_contract",
    "temporal_boundary_contract",
    "output_contract",
    "failure_contract",
    "synthetic_qualification_contract",
    "predecessor_effects",
    "checklist_effects",
    "scope_review",
    "publication_anonymity_boundary",
    "package_bindings",
    "record_sha256",
}


def _validate_no_absolute_paths(value: Any, key: str = "") -> None:
    if type(value) is dict:
        for child_key, child in value.items():
            _validate_no_absolute_paths(child, child_key)
    elif type(value) is list:
        for child in value:
            _validate_no_absolute_paths(child, key)
    elif type(value) is str and (key == "path" or key.endswith("_path")):
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValidationError("absolute or unsafe path")


def _package_bindings(root: Path) -> List[Dict[str, Any]]:
    return [
        _binding(ordinal, role, path, _stable_read(root, path))
        for ordinal, role, path in (
            (0, "HUMAN_DESIGN", HUMAN_PATH),
            (1, "PURE_SPLITTER_AND_READ_ONLY_VALIDATOR", VALIDATOR_PATH),
            (2, "HOSTILE_SYNTHETIC_TEST", TEST_PATH),
        )
    ]


def expected_record(root: Optional[Path] = None) -> Dict[str, Any]:
    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": PACKAGE_KIND,
        "reported_date": REPORTED_DATE,
        "authority_provenance": dict(EXPECTED_AUTHORITY),
        "live_immutable_input_bindings": [dict(row) for row in LIVE_IMMUTABLE_BINDINGS],
        "design_identity": dict(EXPECTED_IDENTITY),
        "normalized_manifest_contract": dict(EXPECTED_MANIFEST),
        "hamilton_allocation_contract": dict(EXPECTED_HAMILTON),
        "temporal_boundary_contract": dict(EXPECTED_BOUNDARY),
        "output_contract": dict(EXPECTED_OUTPUT),
        "failure_contract": dict(EXPECTED_FAILURE),
        "synthetic_qualification_contract": dict(EXPECTED_QUALIFICATION),
        "predecessor_effects": dict(EXPECTED_PREDECESSOR_EFFECTS),
        "checklist_effects": dict(EXPECTED_CHECKLIST),
        "scope_review": dict(EXPECTED_SCOPE),
        "publication_anonymity_boundary": dict(EXPECTED_ANONYMITY),
        "package_bindings": _package_bindings(workspace),
        "record_sha256": "",
    }
    record["record_sha256"] = record_sha256(record)
    return record


def _validate_live_inputs(root: Path, record: Mapping[str, Any]) -> Dict[str, bytes]:
    _strict_equal(
        record["live_immutable_input_bindings"],
        [dict(row) for row in LIVE_IMMUTABLE_BINDINGS],
        "live immutable roster",
    )
    raws: Dict[str, bytes] = {}
    for expected in LIVE_IMMUTABLE_BINDINGS:
        raw = _stable_read(root, expected["path"])
        raws[expected["path"]] = raw
        observed = _binding(
            expected["ordinal"],
            expected["role"],
            expected["path"],
            raw,
            self_digest=expected.get("record_sha256"),
        )
        _strict_equal(observed, dict(expected), "live immutable input")

    prereg = json.loads(raws[PREREGISTRATION_PATH].decode("ascii"))
    if type(prereg) is not dict or prereg.get("state") != GLOBAL_STATE:
        raise ValidationError("preregistration state changed")
    domains = prereg.get("domains")
    split = prereg.get("split_and_leakage_plan")
    if (
        type(domains) is not list
        or len(domains) != 2
        or domains[1].get("source_url") != RETAIL_URL
        or domains[1].get("split_policy") != "CUSTOMER_DISJOINT_AND_TEMPORAL"
        or domains[1].get("post_outcome_replacement_permitted") is not False
        or type(split) is not dict
        or split.get("test_set_exclusion_permitted") is not False
        or split.get("retail_temporal_cutoff_and_window_rule") is not None
        or split.get("train_validation_test_proportions_or_counts") is not None
    ):
        raise ValidationError("preregistration Retail split boundary changed")

    closure = json.loads(raws[CLOSURE_PATH].decode("ascii"))
    if type(closure) is not dict or _self_digest(closure) != closure.get("record_sha256"):
        raise ValidationError("closure self invalid")
    if (
        closure.get("null_projection", {}).get("effective_total_unresolved_null_count") != 172
        or closure.get("blocker_projection", {}).get("effective_unresolved_blocker_count") != 12
    ):
        raise ValidationError("closure counts changed")

    seal = json.loads(raws[SEAL_MACHINE_PATH].decode("ascii"))
    if type(seal) is not dict or _self_digest(seal) != seal.get("record_sha256"):
        raise ValidationError("seal self invalid")
    boundary = seal.get("authority_boundary", {})
    if (
        type(boundary) is not dict
        or boundary.get("network_access_authorized") is not False
        or boundary.get("connector_contact_authorized") is not False
        or boundary.get("test_data_acquisition_authorized") is not False
    ):
        raise ValidationError("seal authority changed")

    static = json.loads(raws[STATIC_MACHINE_PATH].decode("ascii"))
    if type(static) is not dict or _self_digest(static) != static.get("record_sha256"):
        raise ValidationError("static selection self invalid")
    if static.get("state") != "SOLO_BLOCK2_STATIC_SELECTIONS_FROZEN_NO_EXTERNAL_CONTACT_AUTHORITY":
        raise ValidationError("static selection state changed")

    candidate = json.loads(raws[CANDIDATE_MACHINE_PATH].decode("ascii"))
    if type(candidate) is not dict or _self_digest(candidate) != candidate.get("record_sha256"):
        raise ValidationError("candidate self invalid")
    if candidate.get("state") != EXPECTED_PREDECESSOR_EFFECTS["candidate_predecessor_state"]:
        raise ValidationError("candidate state changed")
    identity = candidate.get("candidate_identity", {})
    retail = candidate.get("candidate_split_and_leakage_rules", {}).get("retail", {})
    if (
        type(identity) is not dict
        or type(retail) is not dict
        or identity.get("populated_instance_present") is not False
        or identity.get("populated_instance_admitted") is not False
        or identity.get("precontact_population_blocked") is not True
        or retail.get("exact_temporal_rule_populated") is not False
        or retail.get("test_set_exclusion_permitted") is not False
        or retail.get("customer_invoice_or_row_censoring_permitted") is not False
    ):
        raise ValidationError("candidate nonclaim changed")
    return raws


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate exact design custody and return a privacy-safe status."""

    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    machine_raw = _stable_read(workspace, MACHINE_PATH)
    record = json.loads(machine_raw.decode("ascii"))
    if type(record) is not dict or set(record) != EXPECTED_TOP_LEVEL_KEYS:
        raise ValidationError("machine field roster invalid")
    if canonical_machine_bytes(record) != machine_raw:
        raise ValidationError("machine record not canonical")
    if type(record.get("record_sha256")) is not str:
        raise ValidationError("record self type invalid")
    if record["record_sha256"] != record_sha256(record):
        raise ValidationError("record self invalid")
    _strict_equal(record, expected_record(workspace), "Retail design record")
    _validate_no_absolute_paths(record)
    _validate_live_inputs(workspace, record)
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": record["record_sha256"],
        "project_control_predicate": True,
        "pure_split_design_frozen": True,
        "synthetic_qualification_present": True,
        "real_data_accessed": False,
        "real_split_performed": False,
        "real_feasibility_observed": False,
        "all_row_preservation_required": True,
        "row_exclusion_or_quarantine_permitted": False,
        "outcome_or_label_used": False,
        "unresolved_fields_closed": 0,
        "blockers_closed": 0,
        "effective_unresolved_field_count": 172,
        "effective_open_blocker_count": 12,
        "precontact_population_blocked": True,
        "validation": "PASS",
    }


__all__ = [
    "SplitDesignError",
    "ValidationError",
    "canonical_machine_bytes",
    "expected_record",
    "hamilton_customer_counts",
    "record_sha256",
    "split_retail_rows",
    "validate",
]
