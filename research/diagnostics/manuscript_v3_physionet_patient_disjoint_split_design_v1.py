"""Pure PhysioNet split design plus read-only custody validator.

This module does not open a dataset, contact a source, assign a real split, or
write a file.  Its splitter accepts only an already-normalized in-memory
synthetic/private projection.  The canonical validator only reopens a closed
roster of ordinary workspace files read-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = "heterodiff-manuscript-v3-physionet-patient-disjoint-split-design-v1"
CONTROL_PREDICATE = (
    "PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN_AND_SYNTHETIC_QUALIFICATION_VALIDATED"
)
STATE = (
    "PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN_FROZEN_AND_"
    "SYNTHETICALLY_QUALIFIED_NO_DATA_ACCESS"
)
ALGORITHM_ID = "PHYSIONET_PATIENT_HASH_HAMILTON_70_15_15_V1"
MACHINE_PATH = Path(
    "research/fixtures/manuscript_v3_physionet_patient_disjoint_split_design_v1.json"
)
HUMAN_PATH = Path("PROJECT_PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN.md")
VALIDATOR_PATH = Path(
    "research/diagnostics/manuscript_v3_physionet_patient_disjoint_split_design_v1.py"
)
TEST_PATH = Path(
    "tests/unit/test_manuscript_v3_physionet_patient_disjoint_split_design_v1.py"
)
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]

SPLITS = ("TRAIN", "VALIDATION", "TEST")
NUMERATORS = (70, 15, 15)
DENOMINATOR = 100
MINIMUM_PATIENT_COUNT = 5
MAXIMUM_PATIENT_ID_ASCII_BYTES = 64
PATIENT_ORDER_DOMAIN = b"heterodiff/physionet-patient-order/v1\x00"
INPUT_DIGEST_DOMAIN = b"heterodiff/physionet-normalized-split-input/v1\x00"
ASSIGNMENT_DIGEST_DOMAIN = b"heterodiff/physionet-split-assignment/v1\x00"
RECORD_DIGEST_DOMAIN = (
    b"heterodiff/physionet-patient-disjoint-split-design/v1/record\x00"
)

NORMALIZED_AUTHORITY_TEXT = (
    "Sounds great. Go ahead and finish them in parallel. "
    "Mark all the completed tasks as the end."
)
NORMALIZED_AUTHORITY_SHA256 = (
    "465aa47a0714b7914e33b6b6772afbfad3a56959cb6eb9f10b8e98f39c0f8d38"
)


class PhysioNetSplitDesignError(ValueError):
    """A fail-closed normalized-manifest or split-contract error."""


class CustodyError(RuntimeError):
    """A bound file or canonical machine-record mismatch."""


LIVE_INPUT_SPECS: Tuple[Mapping[str, Any], ...] = (
    {
        "role": "EXECUTION_PREREGISTRATION_HUMAN",
        "path": "manuscript_v3/execution_preregistration.md",
        "bytes": 22491,
        "raw_sha256": "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e",
    },
    {
        "role": "EXECUTION_PREREGISTRATION_MACHINE",
        "path": "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        "bytes": 39771,
        "raw_sha256": "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
    },
    {
        "role": "PREEXECUTION_CLOSURE_HUMAN",
        "path": "manuscript_v3/execution_preregistration_preexecution_closure_v2.md",
        "bytes": 14938,
        "raw_sha256": "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d",
    },
    {
        "role": "PREEXECUTION_CLOSURE_MACHINE",
        "path": "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
        "bytes": 24571,
        "raw_sha256": "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db",
        "record_sha256": "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4",
    },
    {
        "role": "PROSPECTIVE_SEAL_HUMAN",
        "path": "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md",
        "bytes": 7078,
        "raw_sha256": "ad58c5fcb9d47531a7af041eb59f71386fd42a81b1fe31701df167f064f951c2",
    },
    {
        "role": "PROSPECTIVE_SEAL_MACHINE",
        "path": "research/fixtures/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json",
        "bytes": 8461,
        "raw_sha256": "0357fc48394d5888632e3e2d7f5c9180e683141ebc10bef3dec9879a58cdf0e8",
        "record_sha256": "d11d5336f1ede024ab56f92bc64e620681e53fc406fd954aa3da36b7861485a6",
    },
    {
        "role": "PROSPECTIVE_SEAL_VALIDATOR",
        "path": "research/diagnostics/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py",
        "bytes": 32156,
        "raw_sha256": "3647c367506519149d5df60dc2dcfb07a8f5dc976526b88700321b0de89a2258",
    },
    {
        "role": "PROSPECTIVE_SEAL_HOSTILE_TEST",
        "path": "tests/unit/test_manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py",
        "bytes": 16698,
        "raw_sha256": "2285525223f42154553a0302bb46a8f04f0ff7ff35233906a37f4f1a9bf47403",
    },
    {
        "role": "STATIC_SELECTION_HUMAN",
        "path": "PROJECT_SOLO_BLOCK2_STATIC_SELECTION_FREEZE.md",
        "bytes": 23012,
        "raw_sha256": "ab80a009f3d83be4186d3d2da13e3efd5939362e4215477dd2b1a89b870b3126",
    },
    {
        "role": "STATIC_SELECTION_MACHINE",
        "path": "research/fixtures/manuscript_v3_solo_block2_static_selection_freeze_v1.json",
        "bytes": 33638,
        "raw_sha256": "7ff0bf3bb5d9a03e2212f2f7f1853cde2283694b33e072931d258d98e1882590",
        "record_sha256": "1f02200d524749d6708695072dfbc8b785a6f03d5be908b3563f121d7fcd5b53",
    },
    {
        "role": "STATIC_SELECTION_VALIDATOR",
        "path": "research/diagnostics/manuscript_v3_solo_block2_static_selection_freeze_v1.py",
        "bytes": 56344,
        "raw_sha256": "8843cef229c24cbd25cd00e55697755c8fc7a1247f20044dfe110e182e558ec0",
    },
    {
        "role": "STATIC_SELECTION_HOSTILE_TEST",
        "path": "tests/unit/test_manuscript_v3_solo_block2_static_selection_freeze_v1.py",
        "bytes": 48158,
        "raw_sha256": "801fc7c87f57eb72da6cdfa7b2be93c6edd66b974fefe47dabbe5b91eaa0f005",
    },
    {
        "role": "PRECONTACT_CANDIDATE_HUMAN",
        "path": "PROJECT_SOLO_BLOCK2_PRECONTACT_INSTANCE_CANDIDATE.md",
        "bytes": 17965,
        "raw_sha256": "ed211b7bf5aaf45a839e18d15484177fa0c51d7cb95540cdccc61587b2b8250f",
    },
    {
        "role": "PRECONTACT_CANDIDATE_MACHINE",
        "path": "research/fixtures/manuscript_v3_solo_block2_precontact_instance_candidate_v1.json",
        "bytes": 23932,
        "raw_sha256": "95bae0a0ff0d5a199afc23cfc048de04cce28c47300ada301b927c21c60166be",
        "record_sha256": "2c4c068c553bdfab04d49f01163c84923b9108b2f762872ba00015c2fadd9304",
    },
    {
        "role": "PRECONTACT_CANDIDATE_VALIDATOR",
        "path": "research/diagnostics/manuscript_v3_solo_block2_precontact_instance_candidate_v1.py",
        "bytes": 46460,
        "raw_sha256": "6bdfe3c943c8238d88dc5fba908918d9304ab9f377517a483c65cfac887a39dc",
    },
    {
        "role": "PRECONTACT_CANDIDATE_HOSTILE_TEST",
        "path": "tests/unit/test_manuscript_v3_solo_block2_precontact_instance_candidate_v1.py",
        "bytes": 27389,
        "raw_sha256": "40ba6642f81323fb9254520113697785513bb705e72232731657ae1c481d2856",
    },
    {
        "role": "RETAIL_SPLIT_DESIGN_HUMAN",
        "path": "PROJECT_RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN.md",
        "bytes": 11226,
        "raw_sha256": "49a38fbe8bfdbc2fcb93de766f7280ba8affd18b2ebedbcc004d079550b752d1",
    },
    {
        "role": "RETAIL_SPLIT_DESIGN_MACHINE",
        "path": "research/fixtures/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json",
        "bytes": 13409,
        "raw_sha256": "b27086c5979d2f7018b4b8b50b3fffacf03b3fe2691d60567bc42b179d53e98b",
        "record_sha256": "0aa3b6e992ade5343b0d840b382e544ecf5140e352b97a508f359a2fa0d0bed2",
    },
    {
        "role": "RETAIL_SPLIT_DESIGN_VALIDATOR",
        "path": "research/diagnostics/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py",
        "bytes": 38492,
        "raw_sha256": "c377c87ae74ee3a4bfc0dd8f695e0df3531c3eec2c080f5b81379e852424a22e",
    },
    {
        "role": "RETAIL_SPLIT_DESIGN_HOSTILE_TEST",
        "path": "tests/unit/test_manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py",
        "bytes": 24025,
        "raw_sha256": "99ecada07b8325b25e7d227bf9bb5c6e38957619115a7040c636dbdc33cb7109",
    },
    {
        "role": "POWER_ROUTE_HUMAN",
        "path": "PROJECT_REAL_DOMAIN_POWER_ALLOCATION_ROUTE.md",
        "bytes": 15223,
        "raw_sha256": "a8edf99303e30b6ae6ea9912dce6350fadc9e07361fcd25743c03446a2bb0139",
    },
    {
        "role": "POWER_ROUTE_MACHINE",
        "path": "research/fixtures/manuscript_v3_real_domain_power_allocation_route_v1.json",
        "bytes": 15915,
        "raw_sha256": "536493388d23aac2cc3aaf6f9bdc34a12fba77103e9546cbf110c1c8223dfd28",
        "record_sha256": "3846714fca604b3a0a5f05702326b8fd6856f08639bda51a1b7a7dad8a44eef4",
    },
    {
        "role": "POWER_ROUTE_VALIDATOR",
        "path": "research/diagnostics/manuscript_v3_real_domain_power_allocation_route_v1.py",
        "bytes": 36100,
        "raw_sha256": "be5bcf6cde26d1c4eff044f6fad4705c1e87c850c77f38b2a4f7ef670a03b129",
    },
    {
        "role": "POWER_ROUTE_HOSTILE_TEST",
        "path": "tests/unit/test_manuscript_v3_real_domain_power_allocation_route_v1.py",
        "bytes": 19344,
        "raw_sha256": "3c0846ecd924f4e39f7a98414755fdc06c2c1e5d60491879fa4190f5730b9926",
    },
)


def _canonical_json_bytes(value: Any, *, trailing_lf: bool = False) -> bytes:
    text = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return (text + ("\n" if trailing_lf else "")).encode("ascii")


def _sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _strict_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        if set(left) != set(right):
            return False
        return all(_strict_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _strict_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def _require_exact_keys(mapping: Mapping[str, Any], keys: Iterable[str]) -> None:
    expected = set(keys)
    if set(mapping) != expected:
        raise PhysioNetSplitDesignError("INVALID_NORMALIZED_MANIFEST")


def _normalize_patient_id(value: Any) -> Tuple[str, bytes]:
    if type(value) is not str:
        raise PhysioNetSplitDesignError("INVALID_NORMALIZED_MANIFEST")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise PhysioNetSplitDesignError("INVALID_NORMALIZED_MANIFEST") from exc
    if not 1 <= len(encoded) <= MAXIMUM_PATIENT_ID_ASCII_BYTES:
        raise PhysioNetSplitDesignError("INVALID_NORMALIZED_MANIFEST")
    if any(byte < 48 or byte > 57 for byte in encoded):
        raise PhysioNetSplitDesignError("INVALID_NORMALIZED_MANIFEST")
    integer = int(value)
    if integer <= 0 or str(integer) != value:
        raise PhysioNetSplitDesignError("INVALID_NORMALIZED_MANIFEST")
    return value, encoded


def _normalize_rows(rows: Any) -> List[Dict[str, Any]]:
    if type(rows) is not list or not rows:
        raise PhysioNetSplitDesignError("INVALID_NORMALIZED_MANIFEST")
    normalized: List[Dict[str, Any]] = []
    ordinals = set()
    for row in rows:
        if type(row) is not dict:
            raise PhysioNetSplitDesignError("INVALID_NORMALIZED_MANIFEST")
        _require_exact_keys(row, ("record_ordinal", "patient_id"))
        ordinal = row["record_ordinal"]
        if type(ordinal) is not int or ordinal < 0 or ordinal in ordinals:
            raise PhysioNetSplitDesignError("INVALID_NORMALIZED_MANIFEST")
        patient_id, _ = _normalize_patient_id(row["patient_id"])
        ordinals.add(ordinal)
        normalized.append({"patient_id": patient_id, "record_ordinal": ordinal})
    if ordinals != set(range(len(normalized))):
        raise PhysioNetSplitDesignError("INVALID_NORMALIZED_MANIFEST")
    normalized.sort(key=lambda item: item["record_ordinal"])
    return normalized


def _patient_order_digest(patient_bytes: bytes) -> bytes:
    if type(patient_bytes) is not bytes:
        raise TypeError("patient_bytes must be exact bytes")
    preimage = (
        PATIENT_ORDER_DOMAIN
        + len(patient_bytes).to_bytes(2, byteorder="big", signed=False)
        + patient_bytes
    )
    return hashlib.sha256(preimage).digest()


def _hamilton_counts(patient_count: int) -> Dict[str, int]:
    if type(patient_count) is not int or patient_count < MINIMUM_PATIENT_COUNT:
        raise PhysioNetSplitDesignError("INSUFFICIENT_PATIENT_GROUPS")
    counts = [patient_count * numerator // DENOMINATOR for numerator in NUMERATORS]
    remainders = [patient_count * numerator % DENOMINATOR for numerator in NUMERATORS]
    remaining = patient_count - sum(counts)
    priority = sorted(range(len(SPLITS)), key=lambda i: (-remainders[i], i))
    for index in priority[:remaining]:
        counts[index] += 1
    if sum(counts) != patient_count or any(count <= 0 for count in counts):
        raise PhysioNetSplitDesignError("INSUFFICIENT_PATIENT_GROUPS")
    return dict(zip(SPLITS, counts))


def split_physionet_manifest(rows: Any) -> Dict[str, Any]:
    """Return one deterministic in-memory patient-disjoint split assignment."""

    normalized = _normalize_rows(rows)
    patient_bytes_by_id = {
        patient_id: _normalize_patient_id(patient_id)[1]
        for patient_id in {row["patient_id"] for row in normalized}
    }
    if len(patient_bytes_by_id) < MINIMUM_PATIENT_COUNT:
        raise PhysioNetSplitDesignError("INSUFFICIENT_PATIENT_GROUPS")
    counts = _hamilton_counts(len(patient_bytes_by_id))

    ordered = sorted(
        patient_bytes_by_id,
        key=lambda patient_id: (
            _patient_order_digest(patient_bytes_by_id[patient_id]),
            patient_bytes_by_id[patient_id],
        ),
    )
    patient_split: Dict[str, str] = {}
    cursor = 0
    for split in SPLITS:
        stop = cursor + counts[split]
        for patient_id in ordered[cursor:stop]:
            patient_split[patient_id] = split
        cursor = stop
    if cursor != len(ordered) or set(patient_split) != set(ordered):
        raise PhysioNetSplitDesignError("INTERNAL_PATIENT_DISJOINTNESS_FAILURE")

    patient_assignments = [
        {
            "order_sha256": _patient_order_digest(
                patient_bytes_by_id[patient_id]
            ).hex(),
            "patient_id": patient_id,
            "split": patient_split[patient_id],
        }
        for patient_id in sorted(patient_bytes_by_id, key=patient_bytes_by_id.get)
    ]
    record_assignments = [
        {
            "patient_id": row["patient_id"],
            "record_ordinal": row["record_ordinal"],
            "split": patient_split[row["patient_id"]],
        }
        for row in normalized
    ]
    record_counts = {
        split: sum(item["split"] == split for item in record_assignments)
        for split in SPLITS
    }
    payload: Dict[str, Any] = {
        "algorithm_id": ALGORITHM_ID,
        "input_manifest_sha256": _sha256_hex(
            INPUT_DIGEST_DOMAIN + _canonical_json_bytes(normalized)
        ),
        "outcome": "PASS",
        "patient_assignments": patient_assignments,
        "patient_count": len(patient_assignments),
        "patient_counts": counts,
        "record_assignments": record_assignments,
        "record_count": len(record_assignments),
        "record_counts": record_counts,
    }
    result = dict(payload)
    result["assignment_manifest_sha256"] = _sha256_hex(
        ASSIGNMENT_DIGEST_DOMAIN + _canonical_json_bytes(payload)
    )
    _validate_split_output(normalized, result)
    return result


def _validate_split_output(
    normalized: Sequence[Mapping[str, Any]], result: Mapping[str, Any]
) -> None:
    expected_keys = {
        "algorithm_id",
        "assignment_manifest_sha256",
        "input_manifest_sha256",
        "outcome",
        "patient_assignments",
        "patient_count",
        "patient_counts",
        "record_assignments",
        "record_count",
        "record_counts",
    }
    if type(result) is not dict or set(result) != expected_keys:
        raise PhysioNetSplitDesignError("INTERNAL_ALL_RECORD_PRESERVATION_FAILURE")
    expected_ordinals = list(range(len(normalized)))
    observed_ordinals = [
        item["record_ordinal"] for item in result["record_assignments"]
    ]
    if observed_ordinals != expected_ordinals:
        raise PhysioNetSplitDesignError("INTERNAL_ALL_RECORD_PRESERVATION_FAILURE")
    if result["record_count"] != len(normalized):
        raise PhysioNetSplitDesignError("INTERNAL_ALL_RECORD_PRESERVATION_FAILURE")
    patients = {row["patient_id"] for row in normalized}
    assigned_patients = {item["patient_id"] for item in result["patient_assignments"]}
    if assigned_patients != patients or result["patient_count"] != len(patients):
        raise PhysioNetSplitDesignError("INTERNAL_PATIENT_DISJOINTNESS_FAILURE")
    split_by_patient = {
        item["patient_id"]: item["split"] for item in result["patient_assignments"]
    }
    if any(
        item["split"] != split_by_patient.get(item["patient_id"])
        for item in result["record_assignments"]
    ):
        raise PhysioNetSplitDesignError("INTERNAL_PATIENT_DISJOINTNESS_FAILURE")
    if sum(result["patient_counts"].values()) != len(patients):
        raise PhysioNetSplitDesignError("INTERNAL_PATIENT_DISJOINTNESS_FAILURE")
    if any(result["patient_counts"][split] <= 0 for split in SPLITS):
        raise PhysioNetSplitDesignError("INTERNAL_PATIENT_DISJOINTNESS_FAILURE")


def _stat_identity(value: os.stat_result) -> Tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_uid,
        value.st_gid,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _safe_relative_path(root: Path, relative: str) -> Path:
    if type(relative) is not str or not relative or relative.startswith("/"):
        raise CustodyError("bound path must be a nonempty relative path")
    pieces = Path(relative).parts
    if any(piece in ("", ".", "..") for piece in pieces):
        raise CustodyError("bound path is not lexically canonical")
    current = root
    for piece in pieces:
        current = current / piece
        status = os.lstat(current)
        if stat.S_ISLNK(status.st_mode):
            raise CustodyError("bound path contains a symlink")
    return current


def _stable_read(root: Path, relative: str) -> bytes:
    path = _safe_relative_path(root, relative)
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode):
        raise CustodyError("bound leaf must be a regular file")
    if stat.S_IMODE(before.st_mode) != 0o644 or before.st_nlink != 1:
        raise CustodyError("bound leaf mode/link count mismatch")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        opened_before = os.fstat(descriptor)
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                break
            chunks.append(chunk)
        opened_after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = os.lstat(path)
    identity = _stat_identity(before)
    if not (
        identity
        == _stat_identity(opened_before)
        == _stat_identity(opened_after)
        == _stat_identity(after)
    ):
        raise CustodyError("bound leaf changed during stable read")
    return b"".join(chunks)


def _binding_from_spec(
    root: Path, ordinal: int, spec: Mapping[str, Any]
) -> Dict[str, Any]:
    raw = _stable_read(root, spec["path"])
    if len(raw) != spec["bytes"] or _sha256_hex(raw) != spec["raw_sha256"]:
        raise CustodyError("immutable predecessor raw binding mismatch")
    if not raw.endswith(b"\n"):
        raise CustodyError("immutable predecessor lacks trailing LF")
    row: Dict[str, Any] = {
        "bytes": spec["bytes"],
        "mode_octal": "0644",
        "nlink": 1,
        "ordinal": ordinal,
        "path": spec["path"],
        "raw_sha256": spec["raw_sha256"],
        "role": spec["role"],
        "trailing_lf": True,
    }
    if "record_sha256" in spec:
        parsed = _load_json_no_duplicates(raw)
        if parsed.get("record_sha256") != spec["record_sha256"]:
            raise CustodyError("immutable predecessor record digest mismatch")
        row["record_sha256"] = spec["record_sha256"]
    return row


def _package_binding(root: Path, ordinal: int, path: Path, role: str) -> Dict[str, Any]:
    raw = _stable_read(root, path.as_posix())
    if not raw.endswith(b"\n"):
        raise CustodyError("package source lacks trailing LF")
    return {
        "bytes": len(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "ordinal": ordinal,
        "path": path.as_posix(),
        "raw_sha256": _sha256_hex(raw),
        "role": role,
        "trailing_lf": True,
    }


def _load_json_no_duplicates(raw: bytes) -> Dict[str, Any]:
    def pairs_hook(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise CustodyError("duplicate JSON key")
            result[key] = value
        return result

    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=pairs_hook)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CustodyError("machine record is not canonical ASCII JSON") from exc
    if type(value) is not dict:
        raise CustodyError("machine record must be a mapping")
    return value


def _record_self_digest(record: Mapping[str, Any]) -> str:
    payload = dict(record)
    payload["record_sha256"] = None
    return _sha256_hex(RECORD_DIGEST_DOMAIN + _canonical_json_bytes(payload))


def build_expected_record(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    root = Path(root).resolve()
    live_bindings = [
        _binding_from_spec(root, ordinal, spec)
        for ordinal, spec in enumerate(LIVE_INPUT_SPECS)
    ]
    package_bindings = [
        _package_binding(root, 0, HUMAN_PATH, "HUMAN_DESIGN"),
        _package_binding(
            root, 1, VALIDATOR_PATH, "PURE_SPLITTER_AND_READ_ONLY_VALIDATOR"
        ),
        _package_binding(root, 2, TEST_PATH, "HOSTILE_SYNTHETIC_TEST"),
    ]
    record: Dict[str, Any] = {
        "allocation_contract": {
            "all_three_counts_strictly_positive_required": True,
            "alternate_proportion_after_observation_permitted": False,
            "denominator": DENOMINATOR,
            "floor_rule": "INTEGER_FLOOR_N_TIMES_NUMERATOR_DIVIDED_BY_100",
            "minimum_patient_count": MINIMUM_PATIENT_COUNT,
            "numerators": list(NUMERATORS),
            "patient_order": "LEXICOGRAPHIC_SHA256_DIGEST_BYTES_THEN_CANONICAL_PATIENT_BYTES",
            "remainder_rule": "DESCENDING_INTEGER_REMAINDER",
            "seed_or_entropy_used": False,
            "split_names": list(SPLITS),
            "tie_priority": list(SPLITS),
        },
        "authority_provenance": {
            "account_identity_bound": False,
            "conversation_envelope_bound": False,
            "cryptographic_user_authentication_claimed": False,
            "data_access_or_download_authorized": False,
            "dataset_documentation_license_governance_or_approval_contact_authorized": False,
            "escrow_operation_authorized": False,
            "later_one_way_tracker_update_after_independent_go_authorized": True,
            "normalization": "VISIBLE_TEXT_EXACT_TRAILING_TRANSPORT_FRAMING_UNBOUND",
            "normalized_visible_text": NORMALIZED_AUTHORITY_TEXT,
            "normalized_visible_text_sha256": NORMALIZED_AUTHORITY_SHA256,
            "normalized_visible_text_utf8_bytes": 92,
            "raw_transport_bytes_bound": False,
            "renewed_scope_review_for_one_bounded_physionet_design_package": True,
            "renewed_scope_review_interpretation_is_agent_adjudication": True,
            "runtime_or_scientific_execution_authorized": False,
            "scientific_entropy_authorized": False,
            "timestamp_bound": False,
            "tracker_edit_performed_by_this_package": False,
        },
        "checklist_effects": {
            "B02_closed": False,
            "B07_closed": False,
            "F058_closed": False,
            "F058_value": None,
            "F061_closed": False,
            "F061_value": None,
            "blockers_closed": 0,
            "domain_admission_complete": False,
            "effective_open_blocker_count": 12,
            "effective_unresolved_field_count": 172,
            "formal_tests_closed": 0,
            "original_populated_instance_checkbox_closed": False,
            "power_justification_complete": False,
            "project_control_predicate": CONTROL_PREDICATE,
            "project_control_predicate_value_after_validation": True,
            "results_filled": 0,
            "scientific_effect": 0,
            "unresolved_fields_closed": 0,
        },
        "design_identity": {
            "algorithm_id": ALGORITHM_ID,
            "canonical_patient_encoding_frozen": True,
            "design_frozen": True,
            "hash_collision_tie_break_frozen": True,
            "literal_hash_domain_frozen": True,
            "power_justified": False,
            "production_runner_present": False,
            "pure_implementation_present": True,
            "raw_to_normalized_parser_present": False,
            "real_physionet_feasibility_observed": False,
            "real_physionet_snapshot_opened": False,
            "real_split_performed": False,
            "split_manifest_persisted": False,
            "synthetic_qualification_present": True,
        },
        "failure_contract": {
            "fallback_retry_exclusion_alias_repair_resplit_or_patient_migration_permitted": False,
            "insufficient_patient_code": "INSUFFICIENT_PATIENT_GROUPS",
            "internal_all_record_preservation_code": "INTERNAL_ALL_RECORD_PRESERVATION_FAILURE",
            "internal_patient_disjointness_code": "INTERNAL_PATIENT_DISJOINTNESS_FAILURE",
            "invalid_manifest_code": "INVALID_NORMALIZED_MANIFEST",
            "real_manifest_failure_is_terminal_domain_no_go_for_this_rule": True,
        },
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "live_immutable_input_bindings": live_bindings,
        "local_design_context_provenance": {
            "candidate_historical_snapshot_receipts_are_only_bound_provenance": True,
            "current_context_source_bytes_bound_as_live_authority": False,
            "official_source_schema_dataset_or_contact_evidence": False,
            "paths_read_as_text": [
                "src/heterodiff/data/physionet_2012_raw.py",
                "src/heterodiff/data/physionet_2012_adapter.py",
                "src/heterodiff/data/physionet_2012_inventory.py",
            ],
            "preexisting_source_imported_or_executed": False,
            "read_only_text_inspection_performed": True,
        },
        "normalized_manifest_contract": {
            "exact_row_keys": ["record_ordinal", "patient_id"],
            "extra_label_outcome_prediction_loss_or_test_indicator_fields_accepted": False,
            "future_manifest_must_cover_every_snapshot_record": True,
            "future_raw_to_manifest_binding_required": True,
            "input_kind": "CALLER_SUPPLIED_FINITE_NORMALIZED_RECORD_PROJECTION",
            "invalid_or_unrepresentable_record_disposition": "WHOLE_MANIFEST_INVALID_DOMAIN_NO_GO",
            "patient_id": "MINIMAL_POSITIVE_ASCII_DECIMAL_STRING_MAX_64_BYTES",
            "real_manifest_present": False,
            "real_manifest_sha256": None,
            "record_ordinals": "STRICT_INTEGERS_EXACT_SET_0_THROUGH_R_MINUS_1_INPUT_ORDER_IRRELEVANT",
            "record_quarantine_exclusion_deletion_or_repair_permitted": False,
        },
        "output_contract": {
            "all_records_and_patients_preserved": True,
            "assignment_digest_domain": ASSIGNMENT_DIGEST_DOMAIN[:-1].decode("ascii"),
            "assignment_digest_domain_nul_terminated": True,
            "canonical_json_preimage_has_trailing_lf": False,
            "exact_fields": [
                "algorithm_id",
                "assignment_manifest_sha256",
                "input_manifest_sha256",
                "outcome",
                "patient_assignments",
                "patient_count",
                "patient_counts",
                "record_assignments",
                "record_count",
                "record_counts",
            ],
            "file_or_external_effect": False,
            "input_digest_domain": INPUT_DIGEST_DOMAIN[:-1].decode("ascii"),
            "input_digest_domain_nul_terminated": True,
            "output_kind": "CANONICAL_IN_MEMORY_INTERNAL_PRIVATE_ASSIGNMENT_NOT_PUBLICATION_SAFE",
            "patient_assignment_order": "CANONICAL_PATIENT_BYTES_ASCENDING",
            "real_output_present": False,
            "record_assignment_order": "RECORD_ORDINAL_ASCENDING",
        },
        "package_bindings": package_bindings,
        "package_kind": "STATIC_PHYSIONET_SPLIT_DESIGN_AND_SYNTHETIC_QUALIFICATION_ONLY",
        "patient_order_contract": {
            "canonical_patient_bytes": "ASCII_OF_MINIMAL_POSITIVE_DECIMAL_PATIENT_ID",
            "collision_tie_break": "CANONICAL_PATIENT_BYTES_ASCENDING",
            "digest": "SHA256",
            "domain_ascii": "heterodiff/physionet-patient-order/v1",
            "domain_nul_terminated": True,
            "length_prefix": "UNSIGNED_16_BIT_BIG_ENDIAN",
            "maximum_patient_bytes": MAXIMUM_PATIENT_ID_ASCII_BYTES,
            "ordering": "LEXICOGRAPHIC_DIGEST_BYTES_THEN_CANONICAL_PATIENT_BYTES",
            "platform_hash_or_locale_used": False,
        },
        "predecessor_effects": {
            "approval_contact_roster_completed": False,
            "candidate_four_row_operation_roster_changed": False,
            "candidate_population_or_admission_changed": False,
            "candidate_power_seam_closed": False,
            "candidate_predecessor_modified": False,
            "candidate_retail_rule_preserved": True,
            "physionet_local_hash_rule_closed_additively": True,
            "real_escrow_seam_closed": False,
        },
        "publication_anonymity_boundary": {
            "anonymous_or_public_supplement": False,
            "credentials_tokens_or_key_material_present": False,
            "local_absolute_path_present": False,
            "package_internal_only": True,
            "protected_outcome_or_scientific_result_present": False,
            "publication_safe_derivative_required": True,
            "real_patient_identifier_record_or_timestamp_present": False,
            "source_response_or_receipt_present": False,
        },
        "record_sha256": None,
        "reported_date": "2026-08-30",
        "schema_version": SCHEMA_VERSION,
        "scope_and_nonclaims": {
            "blockers_closed": 0,
            "characterized_as_third_populated_precontact_instance": False,
            "data_accessed": False,
            "dataset_source_license_governance_or_approval_contacted": False,
            "existing_files_modified": False,
            "formal_scientific_tests_closed": 0,
            "one_way_predecessor_bindings": True,
            "populated_precontact_instance_present_or_admitted": False,
            "preexisting_scientific_or_runtime_project_code_imported": False,
            "real_split_or_escrow_operation_performed": False,
            "scientific_execution_performed": False,
            "scientific_results_produced": 0,
            "standalone_B02_F058_F061_design_under_renewed_scope": True,
            "static_or_synthetic_only": True,
            "test_outcome_accessed": False,
            "tracker_reverse_binding_present": False,
            "unresolved_fields_closed": 0,
            "web_or_network_used": False,
        },
        "state": STATE,
        "synthetic_qualification_contract": {
            "cases": [
                "CONSTRUCTIVE_ALLOCATION",
                "MULTIRECORD_PATIENT_GROUPING",
                "HAMILTON_REMAINDER_AND_TIE_PRIORITY",
                "INPUT_PERMUTATION_INVARIANCE",
                "INJECTED_HASH_COLLISION_CANONICAL_TIE_BREAK",
                "MINIMUM_PATIENT_COUNT",
                "INVALID_MISSING_EXTRA_BOOL_OVERFLOW_ORDINAL_CASES",
                "INVALID_PATIENT_ID_AND_LEADING_ZERO_ALIAS_CASES",
                "ALL_RECORD_AND_PATIENT_PRESERVATION",
                "LABEL_OUTCOME_AND_TEST_INDICATOR_REJECTION",
                "CANONICAL_MACHINE_SELF_AND_CUSTODY",
                "STATIC_SOURCE_SAFETY_AND_ZERO_EFFECTS",
            ],
            "global_workspace_write_absence_claimed": False,
            "hostile_test_source_process_network_or_canonical_writer_exposed": False,
            "ordinary_software_qualification_interpreter_processes_performed": True,
            "qualification_command_stdout_or_cache_receipt_bound": False,
            "qualification_pytest_cacheprovider_disabled": True,
            "qualification_python_bytecode_disabled": True,
            "qualification_result_provenance": "OWNER_OBSERVED_TOOL_OUTPUT_NOT_REGISTERED_WORKSPACE_RECEIPT",
            "real_data_fixture_opened": False,
            "real_split_feasible": None,
            "scientific_or_domain_admission_evidence": False,
            "synthetic_rows_only": True,
            "validator_source_process_network_or_writer_exposed": False,
        },
    }
    record["record_sha256"] = _record_self_digest(record)
    return record


def canonical_record_bytes(root: Path = WORKSPACE_ROOT) -> bytes:
    return _canonical_json_bytes(build_expected_record(root), trailing_lf=True)


def validate_record_mapping(record: Any, root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    expected = build_expected_record(root)
    if not _strict_equal(record, expected):
        raise CustodyError("machine record differs from the exact expected record")
    if record["record_sha256"] != _record_self_digest(record):
        raise CustodyError("machine record self-digest mismatch")
    return expected


def audit_canonical_workspace(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    root = Path(root).resolve()
    raw = _stable_read(root, MACHINE_PATH.as_posix())
    if not raw.endswith(b"\n"):
        raise CustodyError("machine record lacks trailing LF")
    parsed = _load_json_no_duplicates(raw)
    expected = validate_record_mapping(parsed, root)
    if raw != _canonical_json_bytes(expected, trailing_lf=True):
        raise CustodyError("machine record bytes are not canonical")
    return {
        "control_predicate": CONTROL_PREDICATE,
        "machine_raw_sha256": _sha256_hex(raw),
        "machine_record_sha256": expected["record_sha256"],
        "state": STATE,
        "status": "PASS_STATIC_DESIGN_ONLY_NO_DATA_ACCESS",
    }


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--audit", action="store_true")
    group.add_argument("--emit-record", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = _parse_args(sys.argv[1:] if argv is None else argv)
    if arguments.emit_record:
        sys.stdout.buffer.write(canonical_record_bytes())
        return 0
    result = audit_canonical_workspace()
    sys.stdout.buffer.write(_canonical_json_bytes(result, trailing_lf=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
