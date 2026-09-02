"""Read-only validator for the additive F060 Retail temporal-rule freeze.

The module hash-binds the exact predecessor chain, validates one additive
field closure, and exposes a pure allocation-parameterized reference selector.
It has no writer, network, connector, subprocess, entropy, data-access,
training, runtime, or scientific-worker route.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-gate-a-retail-temporal-rule-field-freeze-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "GATE_A_RETAIL_F060_TEMPORAL_RULE_FROZEN_PREOUTCOME"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
REPORTED_DATE = "2026-08-31"
PACKAGE_KIND = "ADDITIVE_PREOUTCOME_EXACT_F060_FIELD_CLOSURE"
CONTROL_PREDICATE = "RETAIL_F060_PARAMETERIZED_TEMPORAL_CUTOFF_WINDOW_RULE_FROZEN"

HUMAN_PATH = "PROJECT_GATE_A_RETAIL_TEMPORAL_RULE_FIELD_FREEZE.md"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.py"
)
PACKAGE_ROSTER = (HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH)

AUTHORITY_TEXT = (
    "Okay, sounds good. What I want you to do is to set aside a significant "
    "portion of work to do such that you are busy for around 8 hours, because "
    "I am going to sleep, and dont want my absence to make you idle."
)

F060_POINTER = "/split_and_leakage_plan/retail_temporal_cutoff_and_window_rule"
F061_POINTER = "/split_and_leakage_plan/train_validation_test_proportions_or_counts"
RULE_ID = (
    "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_EXHAUSTIVE_GAP_PAIR_"
    "F061_PARAMETERIZED_V1"
)
TARGET_NAMES = ("TRAIN", "VALIDATION", "TEST")
ROW_KEYS = ("row_ordinal", "customer_key_hex", "timestamp_utc_microseconds")
NO_FEASIBLE = "NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR"
INPUT_DOMAIN = b"heterodiff/retail-f060-parameterized-input/v1\0"
ASSIGNMENT_DOMAIN = b"heterodiff/retail-f060-parameterized-assignment/v1\0"
SIGNED_64_MIN = -(2**63)
SIGNED_64_MAX = 2**63 - 1

FEASIBILITY_REQUIREMENTS = (
    "EVERY_COMPLETE_CUSTOMER_INTERVAL_IN_EXACTLY_ONE_WINDOW",
    "EVERY_INPUT_ROW_ASSIGNED_EXACTLY_ONCE",
    "CUSTOMER_SETS_PAIRWISE_DISJOINT_AND_COMPLETE",
    "CUSTOMER_COUNTS_EQUAL_EXACT_FROZEN_F061_COUNTS",
    "ALL_ROW_AND_CUSTOMER_COUNTS_POSITIVE",
    "MAX_TRAIN_TIMESTAMP_STRICTLY_BELOW_MIN_VALIDATION_TIMESTAMP",
    "MAX_VALIDATION_TIMESTAMP_STRICTLY_BELOW_MIN_TEST_TIMESTAMP",
)

F060_VALUE: Mapping[str, Any] = {
    "rule_id": RULE_ID,
    "rule_kind": (
        "DETERMINISTIC_FUNCTION_OF_NORMALIZED_ROWS_AND_RESOLVED_F061_COUNT_"
        "PROJECTION"
    ),
    "normalized_row_exact_keys": list(ROW_KEYS),
    "customer_key": (
        "NONEMPTY_LOWERCASE_EVEN_LENGTH_HEX_OF_OPAQUE_CANONICAL_BYTES_"
        "MAX_2048_CHARS"
    ),
    "timestamp": "STRICT_SIGNED_64_BIT_UTC_MICROSECONDS_SINCE_UNIX_EPOCH",
    "target_customer_count_names": list(TARGET_NAMES),
    "target_customer_counts_source_json_pointer": F061_POINTER,
    "target_customer_counts_input_semantics": (
        "EXACT_POSITIVE_INTEGER_COUNT_PROJECTION_PRODUCED_BY_COMPLETE_F061_"
        "VALUE_WHETHER_F061_USES_COUNTS_OR_PROPORTIONS_PLUS_ITS_OWN_ROUNDING_RULE"
    ),
    "target_customer_counts_value_frozen_by_this_rule": False,
    "f061_raw_representation_or_rounding_rule_frozen_by_this_rule": False,
    "customer_interval": (
        "CLOSED_MINIMUM_TO_MAXIMUM_UTC_MICROSECOND_INTERVAL_OVER_ALL_"
        "CUSTOMER_ROWS"
    ),
    "candidate_timestamps": "SORTED_DISTINCT_OBSERVED_ROW_TIMESTAMPS",
    "candidate_gap_pairs": "ALL_ORDERED_GAP_INDEX_PAIRS_0_LE_G1_LT_G2_LE_M_MINUS_2",
    "train_window": "T_LE_T_G1",
    "validation_window": "T_G1_LT_T_LE_T_G2",
    "test_window": "T_GT_T_G2",
    "boundary_spanning_customer_makes_pair_infeasible": True,
    "feasibility_requirements": list(FEASIBILITY_REQUIREMENTS),
    "selection_order": "LEXICOGRAPHIC_T_G1_T_G1_PLUS_1_T_G2_T_G2_PLUS_1",
    "outcome_label_or_model_result_used": False,
    "no_feasible_pair_code": NO_FEASIBLE,
    "fallback_retry_boundary_relaxation_exclusion_censoring_quarantine_"
    "resplit_customer_migration_or_row_reassignment_permitted": False,
    "observed_cutoff_or_window_frozen": False,
}

PRIOR_CLOSED_FIELDS = ("F106", "F107", "F108", "F113", "F128", "F129", "F148")
POST_FIELDS = ("F164", "F165", "F168", "F169", "F170", "F171")
PRE_FIELDS = tuple(
    "F" + str(index).zfill(3)
    for index in range(1, 173)
    if "F" + str(index).zfill(3) not in POST_FIELDS
)
CLOSED_AFTER = tuple(sorted(PRIOR_CLOSED_FIELDS + ("F060",)))
OPEN_PRE_AFTER = tuple(field for field in PRE_FIELDS if field not in CLOSED_AFTER)


class ValidationError(ValueError):
    """Raised when custody, schema, or frozen semantics fail closed."""


class TemporalRuleError(ValueError):
    """Raised when a caller-supplied temporal-rule input fails closed."""


# group, role, path, byte count, raw SHA-256, optional semantic self-digest
PREDECESSOR_SPECS: Tuple[Tuple[str, str, str, int, str, Optional[str]], ...] = (
    (
        "EXECUTION_PREREGISTRATION",
        "human",
        "manuscript_v3/execution_preregistration.md",
        22491,
        "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e",
        None,
    ),
    (
        "EXECUTION_PREREGISTRATION",
        "machine",
        "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
        39771,
        "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706",
        None,
    ),
    (
        "PREEXECUTION_CLOSURE_V2",
        "human",
        "manuscript_v3/execution_preregistration_preexecution_closure_v2.md",
        14938,
        "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d",
        None,
    ),
    (
        "PREEXECUTION_CLOSURE_V2",
        "machine",
        "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
        24571,
        "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db",
        "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4",
    ),
    (
        "PREEXECUTION_CLOSURE_V2",
        "validator",
        "research/diagnostics/finite_association_r1_rank_prefix_binder_qualification.py",
        32874,
        "f5a71c17a2e6144c1ca82722d2eb1324bc614ad2d14dc565edf57b0c4586d799",
        None,
    ),
    (
        "PREEXECUTION_CLOSURE_V2",
        "test",
        "tests/unit/test_manuscript_v3_execution_preregistration_preexecution_closure_v2.py",
        54965,
        "238e008326846d68246cf8e375cbb3aeb4132d2f52b178354713f35e9b387f59",
        None,
    ),
    (
        "PROSPECTIVE_NO_ACQUISITION_SEAL_V1",
        "human",
        "PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md",
        7078,
        "ad58c5fcb9d47531a7af041eb59f71386fd42a81b1fe31701df167f064f951c2",
        None,
    ),
    (
        "PROSPECTIVE_NO_ACQUISITION_SEAL_V1",
        "machine",
        "research/fixtures/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json",
        8461,
        "0357fc48394d5888632e3e2d7f5c9180e683141ebc10bef3dec9879a58cdf0e8",
        "d11d5336f1ede024ab56f92bc64e620681e53fc406fd954aa3da36b7861485a6",
    ),
    (
        "PROSPECTIVE_NO_ACQUISITION_SEAL_V1",
        "validator",
        "research/diagnostics/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py",
        32156,
        "3647c367506519149d5df60dc2dcfb07a8f5dc976526b88700321b0de89a2258",
        None,
    ),
    (
        "PROSPECTIVE_NO_ACQUISITION_SEAL_V1",
        "test",
        "tests/unit/test_manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py",
        16698,
        "2285525223f42154553a0302bb46a8f04f0ff7ff35233906a37f4f1a9bf47403",
        None,
    ),
    (
        "RETAIL_TEMPORAL_SPLIT_DESIGN_V1",
        "human",
        "PROJECT_RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN.md",
        11226,
        "49a38fbe8bfdbc2fcb93de766f7280ba8affd18b2ebedbcc004d079550b752d1",
        None,
    ),
    (
        "RETAIL_TEMPORAL_SPLIT_DESIGN_V1",
        "machine",
        "research/fixtures/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json",
        13409,
        "b27086c5979d2f7018b4b8b50b3fffacf03b3fe2691d60567bc42b179d53e98b",
        "0aa3b6e992ade5343b0d840b382e544ecf5140e352b97a508f359a2fa0d0bed2",
    ),
    (
        "RETAIL_TEMPORAL_SPLIT_DESIGN_V1",
        "validator",
        "research/diagnostics/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py",
        38492,
        "c377c87ae74ee3a4bfc0dd8f695e0df3531c3eec2c080f5b81379e852424a22e",
        None,
    ),
    (
        "RETAIL_TEMPORAL_SPLIT_DESIGN_V1",
        "test",
        "tests/unit/test_manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py",
        24025,
        "99ecada07b8325b25e7d227bf9bb5c6e38957619115a7040c636dbdc33cb7109",
        None,
    ),
    (
        "RETAIL_TASK_DUAL_MANIFEST_DRAFTS_V1",
        "human",
        "PROJECT_RETAIL_TASK_AND_DUAL_DOMAIN_MANIFEST_DRAFTS.md",
        12733,
        "9367f1fd9f13f89ea734eff1020d3ea0f3e0d9993f5c490c6339b65f4beeb377",
        None,
    ),
    (
        "RETAIL_TASK_DUAL_MANIFEST_DRAFTS_V1",
        "machine",
        "research/fixtures/manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.json",
        21912,
        "0e91275c1671e2725aea60c32d4cac2216c6bb71c2cda195b53b79d8fd295388",
        "2f5a8ec8871ece584099b20b10ee2cf6424ac9a724becc34c691b49d1e7fba87",
    ),
    (
        "RETAIL_TASK_DUAL_MANIFEST_DRAFTS_V1",
        "validator",
        "research/diagnostics/manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.py",
        37865,
        "5d678a8d0d0cb91f5aeebca538fe3595ac340d9f1c57e6d955a0c26bc7981af7",
        None,
    ),
    (
        "RETAIL_TASK_DUAL_MANIFEST_DRAFTS_V1",
        "test",
        "tests/unit/test_manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.py",
        22607,
        "638bf468b1a6a72686d0dc45331e1eca83a7d6918452a5bd613515a909a754ca",
        None,
    ),
    (
        "GATE_A_LOCAL_STATISTICAL_FREEZE_V1",
        "human",
        "PROJECT_GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISION_FREEZE.md",
        8073,
        "ca9a593c54a9d3587f58a3d414defd5cf81a3765395d5ebb8494e6effa6dd44d",
        None,
    ),
    (
        "GATE_A_LOCAL_STATISTICAL_FREEZE_V1",
        "machine",
        "research/fixtures/manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json",
        8455,
        "b8a74f1131f85aa1b7497f2f43bd34a0e30bc471953c935d4362a5a8dea1446a",
        "aa3fe845190d6c74472706749598ba245de1925ce03a5702d1d2eed81a88bffa",
    ),
    (
        "GATE_A_LOCAL_STATISTICAL_FREEZE_V1",
        "validator",
        "research/diagnostics/manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.py",
        22410,
        "3769017b9d6e2b1d2e1f876a84d5cfb49ccb9160e2505338ce5095b03bf790c5",
        None,
    ),
    (
        "GATE_A_LOCAL_STATISTICAL_FREEZE_V1",
        "test",
        "tests/unit/test_manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.py",
        28454,
        "82955f1d0cfefeef439e63ebf1cc8d478225b6529485257ccdb7a5d402d245e7",
        None,
    ),
    (
        "GATE_A_MINIMUM_CONTRIBUTION_REBASELINE_V1",
        "human",
        "PROJECT_GATE_A_MINIMUM_CONTRIBUTION_ROUTE_REBASELINE.md",
        16295,
        "9f472caa8f0dc5a38b0ee71f886e5652cadaac1d8970fca2f28e0fd45cc4f036",
        None,
    ),
    (
        "GATE_A_MINIMUM_CONTRIBUTION_REBASELINE_V1",
        "machine",
        "research/fixtures/manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.json",
        20823,
        "38c0f11f03fe11d61660823e36404b0c26ff5a3de012400675ba8452c045a9a1",
        "8ac5d625513e9ccbf6267734eec250270e49a168421564764e73b60acd6b3c40",
    ),
    (
        "GATE_A_MINIMUM_CONTRIBUTION_REBASELINE_V1",
        "validator",
        "research/diagnostics/manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.py",
        38896,
        "b9f9828b1122d8e72b4a70a68e6fa137c8e2b3ff21dbfed2d6f3f34e103c5deb",
        None,
    ),
    (
        "GATE_A_MINIMUM_CONTRIBUTION_REBASELINE_V1",
        "test",
        "tests/unit/test_manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.py",
        38991,
        "9b36a183081d74e92b343eb0efa5f6ce6c60efa3c2a4a154e0e81588c3b45a30",
        None,
    ),
)

PREDECESSOR_GROUP_COUNTS: Mapping[str, int] = {
    "EXECUTION_PREREGISTRATION": 2,
    "PREEXECUTION_CLOSURE_V2": 4,
    "PROSPECTIVE_NO_ACQUISITION_SEAL_V1": 4,
    "RETAIL_TEMPORAL_SPLIT_DESIGN_V1": 4,
    "RETAIL_TASK_DUAL_MANIFEST_DRAFTS_V1": 4,
    "GATE_A_LOCAL_STATISTICAL_FREEZE_V1": 4,
    "GATE_A_MINIMUM_CONTRIBUTION_REBASELINE_V1": 4,
    "total": 26,
}


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _require_json_builtins(value: Any, label: str = "value") -> None:
    if value is None or type(value) in (bool, int, str):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValidationError(label + " contains nonfinite float")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _require_json_builtins(item, label + "[" + str(index) + "]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValidationError(label + " key must be exact built-in str")
            _require_json_builtins(item, label + "." + key)
        return
    raise ValidationError(label + " contains unsupported or subclassed JSON type")


def _canonical_payload_bytes(value: Any) -> bytes:
    _require_json_builtins(value)
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    if type(record) is not dict:
        raise ValidationError("machine record must be exact built-in dict")
    return _canonical_payload_bytes(record) + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict:
        raise ValidationError("record must be exact built-in dict")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _canonical_payload_bytes(payload))


def _input_record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict:
        raise ValidationError("predecessor record must be exact built-in dict")
    schema = record.get("schema_version")
    if type(schema) is not str or not schema or not schema.isascii():
        raise ValidationError("predecessor schema invalid")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256((schema + "\0").encode("ascii") + _canonical_payload_bytes(payload))


def _unique_object(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _parse_json(raw: bytes, label: str) -> Dict[str, Any]:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValidationError(label + " must be ASCII") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValidationError(label + " contains nonfinite token " + token)
            ),
        )
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValidationError(label + " JSON invalid") from exc
    if type(value) is not dict:
        raise ValidationError(label + " top level must be exact object")
    _require_json_builtins(value, label)
    return value


def _strict_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if any(type(key) is not str for key in actual):
            raise ValidationError(label + " key type mismatch")
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


def _safe_path(root: Path, relative: str) -> Path:
    if type(relative) is not str or not relative:
        raise ValidationError("relative path invalid")
    rel = Path(relative)
    if rel.is_absolute() or not rel.parts or ".." in rel.parts:
        raise ValidationError("unsafe relative path")
    root_resolved = root.resolve(strict=True)
    root_status = os.lstat(root_resolved)
    if not stat.S_ISDIR(root_status.st_mode) or stat.S_ISLNK(root_status.st_mode):
        raise ValidationError("root custody invalid")
    target = root_resolved.joinpath(*rel.parts)
    if target.resolve(strict=False) != target:
        raise ValidationError("path contains symlink")
    return target


def _ancestor_fingerprint(status: os.stat_result) -> Tuple[Any, ...]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        stat.S_IMODE(status.st_mode),
        status.st_uid,
        status.st_gid,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _ancestor_snapshot(root: Path, target: Path) -> Tuple[Tuple[str, Any], ...]:
    root_resolved = root.resolve(strict=True)
    current = target.parent
    rows: List[Tuple[str, Any]] = []
    while True:
        status = os.lstat(current)
        if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
            raise ValidationError("unsafe ancestor")
        rows.append((str(current), _ancestor_fingerprint(status)))
        if current == root_resolved:
            break
        if root_resolved not in current.parents:
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


def _stable_read(root: Path, relative: str) -> bytes:
    target = _safe_path(root, relative)
    ancestors_before = _ancestor_snapshot(root, target)
    before_path = os.lstat(target)
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != 0o644
        or before_path.st_nlink != 1
    ):
        raise ValidationError("leaf custody invalid: " + relative)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(target, flags)
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
    after_path = os.lstat(target)
    fingerprint = _leaf_fingerprint(before_path)
    if not (
        fingerprint
        == _leaf_fingerprint(before_fd)
        == _leaf_fingerprint(after_fd)
        == _leaf_fingerprint(after_path)
    ):
        raise ValidationError("leaf changed during read: " + relative)
    raw = b"".join(chunks)
    if len(raw) != before_fd.st_size:
        raise ValidationError("short read: " + relative)
    if ancestors_before != _ancestor_snapshot(root, target):
        raise ValidationError("ancestor changed during read: " + relative)
    return raw


def _binding(
    ordinal: int,
    group: str,
    role: str,
    path: str,
    raw: bytes,
    semantic_digest: Optional[str] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "ordinal": ordinal,
        "group": group,
        "role": role,
        "path": path,
        "bytes": len(raw),
        "raw_sha256": _sha256(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "terminal_lf": raw.endswith(b"\n"),
    }
    if semantic_digest is not None:
        row["record_sha256"] = semantic_digest
    return row


def _predecessor_state(root: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    bindings: List[Dict[str, Any]] = []
    records: Dict[str, Dict[str, Any]] = {}
    for ordinal, spec in enumerate(PREDECESSOR_SPECS):
        group, role, path, expected_bytes, expected_sha, expected_record = spec
        raw = _stable_read(root, path)
        if len(raw) != expected_bytes or _sha256(raw) != expected_sha:
            raise ValidationError("predecessor exact-byte mismatch: " + path)
        if role == "machine":
            parsed = _parse_json(raw, "predecessor " + path)
            records[path] = parsed
            if expected_record is not None:
                if parsed.get("record_sha256") != expected_record:
                    raise ValidationError("predecessor self-digest field mismatch")
                if _input_record_sha256(parsed) != expected_record:
                    raise ValidationError("predecessor recomputed self-digest mismatch")
        bindings.append(
            _binding(ordinal, group, role, path, raw, expected_record)
        )
    return bindings, records


def _package_bindings(root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for ordinal, (role, path) in enumerate(
        (("human", HUMAN_PATH), ("validator", VALIDATOR_PATH), ("test", TEST_PATH))
    ):
        rows.append(_binding(ordinal, "CURRENT_PACKAGE", role, path, _stable_read(root, path)))
    return rows


def _validate_predecessor_semantics(records: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    prereg_path = "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
    seal_path = "research/fixtures/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json"
    retail_path = "research/fixtures/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json"
    drafts_path = "research/fixtures/manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.json"
    gate_path = "research/fixtures/manuscript_v3_gate_a_local_statistical_and_downstream_decision_freeze_v1.json"
    contribution_path = "research/fixtures/manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.json"
    prereg = records[prereg_path]
    split = prereg.get("split_and_leakage_plan")
    if type(split) is not dict:
        raise ValidationError("preregistration split plan absent")
    for key in (
        "physionet_split_manifest_path",
        "retail_split_manifest_path",
        "retail_temporal_cutoff_and_window_rule",
        "train_validation_test_proportions_or_counts",
    ):
        if split.get(key) is not None:
            raise ValidationError("preregistration split seam was populated: " + key)
    if prereg.get("state") != GLOBAL_STATE or prereg.get("confirmatory_execution_authorized") is not False:
        raise ValidationError("preregistration global state changed")

    seal = records[seal_path]
    observation = seal.get("observation_boundary")
    if (
        seal.get("state") != "NO_TEST_DATA_ACQUIRED_USER_REPORTED_PROSPECTIVE_SEAL_ACTIVE"
        or seal.get("global_state") != GLOBAL_STATE
        or type(observation) is not dict
        or observation.get("test_data_acquisition_performed") is not False
        or observation.get("test_data_opening_performed") is not False
        or observation.get("network_access_performed") is not False
    ):
        raise ValidationError("prospective seal boundary changed")

    retail = records[retail_path]
    design = retail.get("design_identity")
    effects = retail.get("checklist_effects")
    boundary = retail.get("temporal_boundary_contract")
    if type(design) is not dict or type(effects) is not dict or type(boundary) is not dict:
        raise ValidationError("Retail predecessor structure invalid")
    if (
        design.get("design_frozen") is not True
        or design.get("real_retail_snapshot_opened") is not False
        or design.get("real_retail_feasibility_observed") is not False
        or design.get("real_split_performed") is not False
        or design.get("power_justified") is not False
        or design.get("domain_admitted") is not False
        or effects.get("f060_value_written_into_immutable_preregistration") is not False
        or effects.get("f061_value_written_into_immutable_preregistration") is not False
        or effects.get("unresolved_fields_closed") != 0
    ):
        raise ValidationError("Retail predecessor nonclosure changed")
    common_boundary = {
        key: F060_VALUE[key]
        for key in (
            "customer_interval",
            "candidate_timestamps",
            "candidate_gap_pairs",
            "train_window",
            "validation_window",
            "test_window",
            "boundary_spanning_customer_makes_pair_infeasible",
            "selection_order",
            "outcome_label_or_model_result_used",
            "no_feasible_pair_code",
        )
    }
    for key, wanted in common_boundary.items():
        _strict_equal(boundary.get(key), wanted, "Retail temporal projection." + key)
    old_requirements = list(boundary.get("feasibility_requirements", []))
    if old_requirements != [
        item.replace("EXACT_FROZEN_F061_COUNTS", "EXACT_HAMILTON_COUNTS")
        for item in FEASIBILITY_REQUIREMENTS
    ]:
        raise ValidationError("Retail feasibility projection changed")

    drafts = records[drafts_path]
    nonclosure = drafts.get("nonclosure")
    scope = drafts.get("scope_and_nonclaims")
    if type(nonclosure) is not dict or type(scope) is not dict:
        raise ValidationError("manifest-draft predecessor structure invalid")
    if (
        nonclosure.get("f038_through_f061_all_open_and_null") is not True
        or nonclosure.get("unresolved_fields_closed") != 0
        or nonclosure.get("B03_open") is not True
        or scope.get("real_snapshot_or_split_manifest_present") is not False
        or scope.get("data_acquired_opened_parsed_snapshotted_or_split") is not False
        or scope.get("domain_admitted") is not False
    ):
        raise ValidationError("manifest-draft nonclosure changed")

    gate = records[gate_path]
    if [row.get("field_id") for row in gate.get("field_closures", [])] != [
        "F107",
        "F113",
        "F128",
        "F129",
        "F148",
    ]:
        raise ValidationError("local statistical field roster changed")
    _strict_equal(
        gate.get("count_transition", {}).get("after"),
        {"post_execution_open": 6, "pre_execution_open": 161, "total_open": 167},
        "local statistical count",
    )

    contribution = records[contribution_path]
    if [row.get("field_id") for row in contribution.get("field_closures", [])] != [
        "F106",
        "F108",
    ]:
        raise ValidationError("contribution field roster changed")
    _strict_equal(
        contribution.get("count_transition", {}).get("after"),
        {
            "post_execution_closed": 0,
            "post_execution_open": 6,
            "pre_execution_closed": 7,
            "pre_execution_open": 159,
            "total_closed": 7,
            "total_open": 165,
        },
        "contribution count",
    )
    return {
        "preregistration_F058_F059_F060_F061_null": True,
        "prospective_seal_active_no_acquisition_or_opening": True,
        "historical_retail_design_f060_and_f061_zero_delta_preserved": True,
        "historical_manifest_drafts_f019_through_f061_zero_delta_preserved": True,
        "retail_temporal_projection_matches_bound_design_except_f061_parameterization": True,
        "baseline_closed_field_ids": list(PRIOR_CLOSED_FIELDS),
        "baseline_pre_execution_open": 159,
        "baseline_pre_execution_closed": 7,
        "baseline_post_execution_open": 6,
        "baseline_total_open": 165,
        "baseline_total_closed": 7,
    }


def _checked_target_counts(target_counts: Any) -> Dict[str, int]:
    if type(target_counts) is not dict:
        raise TemporalRuleError("target counts must be exact built-in dict")
    if any(type(key) is not str for key in target_counts):
        raise TemporalRuleError("target count keys must be exact built-in str")
    if set(target_counts) != set(TARGET_NAMES):
        raise TemporalRuleError("target count roster invalid")
    checked: Dict[str, int] = {}
    for name in TARGET_NAMES:
        value = target_counts[name]
        if type(value) is not int or value <= 0:
            raise TemporalRuleError("target counts must be positive exact integers")
        checked[name] = value
    return checked


def _normalize_rows(rows: Any) -> Tuple[List[Dict[str, Any]], Dict[bytes, List[Dict[str, Any]]]]:
    if type(rows) is not list or not rows:
        raise TemporalRuleError("rows must be nonempty exact built-in list")
    normalized: List[Dict[str, Any]] = []
    ordinals = set()
    for row in rows:
        if type(row) is not dict or any(type(key) is not str for key in row):
            raise TemporalRuleError("each row must be exact built-in dict with string keys")
        if set(row) != set(ROW_KEYS):
            raise TemporalRuleError("row key roster invalid")
        ordinal = row["row_ordinal"]
        key_hex = row["customer_key_hex"]
        timestamp = row["timestamp_utc_microseconds"]
        if type(ordinal) is not int or ordinal < 0:
            raise TemporalRuleError("row ordinal invalid")
        if ordinal in ordinals:
            raise TemporalRuleError("duplicate row ordinal")
        ordinals.add(ordinal)
        if (
            type(key_hex) is not str
            or not key_hex
            or not key_hex.isascii()
            or key_hex != key_hex.lower()
            or len(key_hex) > 2048
            or len(key_hex) % 2 != 0
        ):
            raise TemporalRuleError("customer key invalid")
        try:
            key = bytes.fromhex(key_hex)
        except ValueError as exc:
            raise TemporalRuleError("customer key invalid") from exc
        if not key or key.hex() != key_hex:
            raise TemporalRuleError("customer key invalid")
        if (
            type(timestamp) is not int
            or timestamp < SIGNED_64_MIN
            or timestamp > SIGNED_64_MAX
        ):
            raise TemporalRuleError("timestamp invalid")
        normalized.append(
            {
                "row_ordinal": ordinal,
                "customer_key_hex": key_hex,
                "timestamp_utc_microseconds": timestamp,
            }
        )
    if ordinals != set(range(len(normalized))):
        raise TemporalRuleError("row ordinals must be exact zero-based range")
    normalized.sort(key=lambda row: row["row_ordinal"])
    customers: Dict[bytes, List[Dict[str, Any]]] = {}
    for row in normalized:
        customers.setdefault(bytes.fromhex(row["customer_key_hex"]), []).append(row)
    return normalized, customers


def select_temporal_boundary(rows: Any, target_customer_counts: Any) -> Dict[str, Any]:
    """Apply the frozen F060 rule to synthetic caller-supplied exact inputs.

    The target counts are a typed F061 input. Supplying them to this helper does
    not freeze F061 and is not evidence of a real allocation or split.
    """

    normalized, customers = _normalize_rows(rows)
    targets = _checked_target_counts(target_customer_counts)
    if sum(targets.values()) != len(customers):
        raise TemporalRuleError("target counts do not cover exact customer roster")
    timestamps = sorted({row["timestamp_utc_microseconds"] for row in normalized})
    if len(timestamps) < 3:
        raise TemporalRuleError(NO_FEASIBLE)
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
            for key, (minimum, maximum) in intervals.items():
                if maximum <= first_left:
                    assignments[key] = "TRAIN"
                elif minimum >= first_right and maximum <= second_left:
                    assignments[key] = "VALIDATION"
                elif minimum >= second_right:
                    assignments[key] = "TEST"
                else:
                    assignments = {}
                    break
            if not assignments:
                continue
            observed = {
                name: sum(value == name for value in assignments.values())
                for name in TARGET_NAMES
            }
            if observed != targets:
                continue
            selected = (first_gap, second_gap, assignments)
            break
        if selected is not None:
            break
    if selected is None:
        raise TemporalRuleError(NO_FEASIBLE)
    first_gap, second_gap, assignments = selected
    customer_assignments = [
        {"customer_key_hex": key.hex(), "split": assignments[key]}
        for key in sorted(customers)
    ]
    row_assignments = [
        {
            "row_ordinal": row["row_ordinal"],
            "split": assignments[bytes.fromhex(row["customer_key_hex"])],
        }
        for row in normalized
    ]
    row_counts = {
        name: sum(row["split"] == name for row in row_assignments)
        for name in TARGET_NAMES
    }
    if any(row_counts[name] <= 0 for name in TARGET_NAMES):
        raise TemporalRuleError("internal positive-row invariant failed")
    split_times = {
        name: [
            normalized[row["row_ordinal"]]["timestamp_utc_microseconds"]
            for row in row_assignments
            if row["split"] == name
        ]
        for name in TARGET_NAMES
    }
    if not (
        max(split_times["TRAIN"]) < min(split_times["VALIDATION"])
        and max(split_times["VALIDATION"]) < min(split_times["TEST"])
    ):
        raise TemporalRuleError("internal temporal invariant failed")
    rule_input = {"normalized_rows": normalized, "target_customer_counts": targets}
    payload: Dict[str, Any] = {
        "schema_version": "heterodiff-retail-f060-parameterized-assignment-v1",
        "rule_id": RULE_ID,
        "outcome": "PASS",
        "rule_input_sha256": _sha256(INPUT_DOMAIN + _canonical_payload_bytes(rule_input)),
        "row_count": len(normalized),
        "customer_count": len(customers),
        "target_customer_counts": targets,
        "row_counts": row_counts,
        "boundary": {
            "train_last_timestamp_utc_microseconds": timestamps[first_gap],
            "validation_first_timestamp_utc_microseconds": timestamps[first_gap + 1],
            "validation_last_timestamp_utc_microseconds": timestamps[second_gap],
            "test_first_timestamp_utc_microseconds": timestamps[second_gap + 1],
        },
        "customer_assignments": customer_assignments,
        "row_assignments": row_assignments,
        "caller_inputs_verified_as_real_or_scientific_evidence": False,
    }
    payload["assignment_manifest_sha256"] = _sha256(
        ASSIGNMENT_DOMAIN + _canonical_payload_bytes(payload)
    )
    return payload


def _audit_groups() -> List[Dict[str, Any]]:
    return [
        {"field_ids": "F001-F018", "reason": "FINAL_THEOREM_OR_EXACT_KNOWN_LAW_PROOF_FIXTURE_AND_TOLERANCE_DEPENDENCIES_OPEN"},
        {"field_ids": "F019-F057", "reason": "REAL_SNAPSHOT_SOURCE_LICENSE_GOVERNANCE_SCHEMA_TASK_KERNEL_OR_ADMISSION_EVIDENCE_ABSENT"},
        {"field_ids": "F058,F059", "reason": "ACTUAL_CONTENT_ADDRESSED_REAL_SPLIT_MANIFEST_PATHS_ABSENT"},
        {"field_ids": "F061", "reason": "ALLOCATION_POWER_JUSTIFICATION_AND_RECEIPT_ABSENT"},
        {"field_ids": "F062-F104", "reason": "FINAL_METHOD_BASELINE_CONTROL_IDENTITY_AND_MATCHED_COMPUTE_EVIDENCE_ABSENT"},
        {"field_ids": "F105,F109-F112", "reason": "ADMITTED_EXACT_PRIMARY_METRIC_INSTANCE_AND_ASSOCIATED_NUMERIC_DESIGN_ABSENT"},
        {"field_ids": "F114-F127", "reason": "EXACT_SCALAR_CONSTRAINT_DEFINITIONS_DIRECTIONS_AND_MARGINS_ABSENT"},
        {"field_ids": "F130-F138", "reason": "POWER_PILOT_SEEDS_SAMPLE_SIZES_ANALYSIS_AND_RESAMPLE_DESIGN_ABSENT"},
        {"field_ids": "F139-F147", "reason": "FINAL_IMPLEMENTATION_METRIC_TRAINING_BUDGET_AND_CHECKPOINT_RULE_ABSENT"},
        {"field_ids": "F149", "reason": "SCIENTIFIC_FAILURE_RATE_OPERATING_THRESHOLD_REQUIRES_POWER_AND_COMPUTE_SEMANTICS"},
        {"field_ids": "F150-F162", "reason": "ACTUAL_HARDWARE_ENVIRONMENT_CAPACITY_AND_COMPUTE_BUDGET_EVIDENCE_ABSENT"},
        {"field_ids": "F163,F166,F167", "reason": "VERIFIED_DOMAIN_SPECIFIC_LICENSE_GOVERNANCE_INTERPRETATION_AND_PRIVACY_FACTS_ABSENT"},
        {"field_ids": "F172", "reason": "FINAL_SEALED_FREEZE_LEAF_RESERVED_FOR_GATE_C"},
    ]


def expected_record(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    predecessor_bindings, records = _predecessor_state(root)
    receipt = _validate_predecessor_semantics(records)
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "reported_date": REPORTED_DATE,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": PACKAGE_KIND,
        "control_predicate": CONTROL_PREDICATE,
        "authority_provenance": {
            "normalized_visible_text": AUTHORITY_TEXT,
            "normalized_visible_text_sha256": _sha256(AUTHORITY_TEXT.encode("utf-8")),
            "local_autonomous_project_work_authorized": True,
            "agent_selected_paths_schema_parameterization_and_qualification_cases": True,
            "raw_transport_bytes_or_trailing_html_space_bound": False,
            "network_source_contact_or_data_access_authorized": False,
            "entropy_runtime_training_scientific_execution_or_real_split_authorized": False,
            "claim_promotion_submission_or_tracker_edit_authorized_by_this_package": False,
        },
        "package_file_roster": list(PACKAGE_ROSTER),
        "package_bindings_excluding_machine_self": _package_bindings(root),
        "machine_self_binding": {
            "path": MACHINE_PATH,
            "semantic_self_digest_field": "record_sha256",
            "raw_self_hash_embedded": False,
        },
        "predecessor_bindings": predecessor_bindings,
        "predecessor_group_counts": dict(PREDECESSOR_GROUP_COUNTS),
        "predecessor_projection_receipt": receipt,
        "field_closures": [
            {
                "field_id": "F060",
                "json_pointer": F060_POINTER,
                "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_PARAMETERIZED_RULE_FREEZE",
                "value": dict(F060_VALUE),
                "separate_unresolved_input_field_id": "F061",
                "separate_unresolved_input_json_pointer": F061_POINTER,
                "separate_unresolved_input_value": None,
            }
        ],
        "f060_f061_separation": {
            "distinct_sibling_json_pointers": True,
            "f060_owns_temporal_mapping_not_allocation": True,
            "f061_owns_target_proportions_or_counts_and_power_justification": True,
            "f061_may_use_counts_or_proportions_plus_its_own_rounding_rule": True,
            "f061_raw_representation_or_conversion_selected_by_package": False,
            "historical_hamilton_70_15_15_identity_used_as_f060_value": False,
            "historical_70_15_15_instantiation_qualified": True,
            "non_70_15_15_target_count_instantiation_qualified": True,
            "f060_rule_requires_exact_f061_counts_before_any_real_application": True,
            "f061_value_selected_or_shadow_bound_by_package": False,
        },
        "count_transition": {
            "before": {
                "pre_execution_open": 159,
                "pre_execution_closed": 7,
                "post_execution_open": 6,
                "post_execution_closed": 0,
                "total_open": 165,
                "total_closed": 7,
            },
            "closed_by_package": {
                "field_ids": ["F060"],
                "pre_execution": 1,
                "post_execution": 0,
                "total": 1,
            },
            "after": {
                "pre_execution_open": 158,
                "pre_execution_closed": 8,
                "post_execution_open": 6,
                "post_execution_closed": 0,
                "total_open": 164,
                "total_closed": 8,
            },
            "blockers_open_after": 12,
            "blockers_closed": 0,
            "formal_tests_closed": 0,
            "results_filled": 0,
        },
        "comprehensive_pre_field_sweep": {
            "total_pre_fields": 166,
            "closed_before_ids": list(PRIOR_CLOSED_FIELDS),
            "eligible_now_ids": ["F060"],
            "closed_after_ids": list(CLOSED_AFTER),
            "open_after_count": 158,
            "open_after_ids": list(OPEN_PRE_AFTER),
            "audit_groups": _audit_groups(),
            "additional_eligible_field_count": 0,
            "anti_drift_no_precursor_created_for_ineligible_fields": True,
        },
        "project_effects_and_nonclaims": {
            "only_field_closed": "F060",
            "F058_open_actual_physionet_manifest_absent": True,
            "F059_open_actual_retail_manifest_absent": True,
            "F061_open_null_unpowered": True,
            "F105_F109_F110_F111_F112_open_no_admitted_metric_instance": True,
            "F149_open_no_power_compute_operating_semantics": True,
            "all_other_open_pre_fields_remain_open": True,
            "B03_open": True,
            "all_12_blockers_open": True,
            "formal_tests_28_29_30_open": True,
            "R1_R2_R3_R4_open": True,
            "gate_a_closed_by_package": False,
            "domain_admitted": False,
            "real_snapshot_or_split_manifest_present": False,
            "real_cutoff_or_window_observed": False,
            "real_feasibility_observed": False,
            "power_justification_complete": False,
            "scientific_result": False,
            "tracker_edit_performed": False,
        },
        "qualification_boundary": {
            "validator_read_only": True,
            "pure_reference_selector_uses_caller_supplied_synthetic_values_only": True,
            "caller_values_verified_as_real_or_scientific_evidence": False,
            "production_splitter_claimed": False,
            "validator_or_helper_writer_network_connector_subprocess_entropy_data_"
            "training_runtime_or_scientific_worker_route_present": False,
            "qualification_launches_python_and_pytest_interpreters": True,
            "hostile_tests_write_disposable_pytest_temporary_copies": True,
            "canonical_package_or_predecessor_bytes_modified_by_qualification": False,
            "cache_disabled_qualification_required": True,
        },
        "publication_boundary": {
            "internal_project_control_only": True,
            "anonymous_or_public_inclusion_permitted": False,
            "publication_safe_derivative_required": True,
            "fresh_anonymity_methods_statistics_and_claim_boundary_audit_required": True,
        },
    }
    record["record_sha256"] = record_sha256(record)
    return record


def validate(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    expected = expected_record(root)
    raw = _stable_read(root, MACHINE_PATH)
    actual = _parse_json(raw, "package machine record")
    if raw != canonical_machine_bytes(actual):
        raise ValidationError("package machine record is not canonical JSON")
    if actual.get("record_sha256") != record_sha256(actual):
        raise ValidationError("package machine record self-digest mismatch")
    _strict_equal(actual, expected, "package machine record")
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": actual["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "F060_closed": True,
        "F060_rule_id": RULE_ID,
        "F061_closed": False,
        "F061_value": None,
        "unresolved_fields_closed": 1,
        "effective_pre_execution_open": 158,
        "effective_post_execution_open": 6,
        "effective_unresolved_field_count": 164,
        "effective_closed_field_count": 8,
        "effective_open_blocker_count": 12,
        "domain_admitted": False,
        "real_split_performed": False,
        "scientific_result": False,
        "tracker_edit_performed": False,
        "validation": "PASS",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))
