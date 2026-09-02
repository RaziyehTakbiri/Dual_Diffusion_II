"""Read-only validator for the additive F104 matched-compute formula freeze.

The module validates one parameterized scientific-plan field and exposes the
same pure integer/rational calculator as the accepted predecessor draft.  It
has no writer, network, connector, subprocess, entropy, data, training,
runtime-capture, production, or scientific-execution route.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-f104-matched-total-compute-formula-freeze-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "F104_MATCHED_TOTAL_COMPUTE_FORMULA_FROZEN_RESOURCE_VALUES_NULL"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
REPORTED_DATE = "2026-08-31"
PACKAGE_KIND = "ADDITIVE_PREOUTCOME_EXACT_F104_FIELD_CLOSURE"
CONTROL_PREDICATE = "MATCHED_TOTAL_COMPUTE_FORMULA_F104_FROZEN_PREOUTCOME"

HUMAN_PATH = "PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE.md"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py"
)
PACKAGE_ROSTER = (HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH)

AUTHORITY_TEXT = (
    "Okay, sounds good. What I want you to do is to set aside a significant "
    "portion of work to do such that you are busy for around 8 hours, because "
    "I am going to sleep, and dont want my absence to make you idle."
)
EVIDENCE_READY_REGISTRATION = (
    "Upon independent acceptance, register only this delta: F104 "
    "(`/method_and_baseline_plan/matched_total_compute_formula`) is closed by "
    "the exact parameterized formula `C[m,d] = sum_p sum_k n[m,d,p,k] * "
    "w[d,k]`, with exact nonnegative integer counts and strictly positive exact "
    "rational weights under the frozen phase, resource-event, calibration, "
    "fairness, and hard-axis rules. Effective pre-execution counts move from "
    "146 open / 20 closed to 145 open / 21 closed; post-execution counts remain "
    "6 open / 0 closed. B06, B08, B12, and all 12 blockers remain open; Formal "
    "Tests 28 and 29 remain OPEN, Formal Test 30 remains PENDING, and R1-R4 "
    "remain unexecuted. This registration supplies no resource value, "
    "operational receipt, runtime, scientific result, claim, submission, other "
    "field closure, or blocker closure."
)

F104_POINTER = "/method_and_baseline_plan/matched_total_compute_formula"
FORMULA_ID = "EXACT_WEIGHTED_RESOURCE_LEDGER_V1"
PHASES = ("PILOT", "TUNING", "FINAL_TRAINING", "CONFIRMATORY_INFERENCE")
RESOURCE_EVENTS = (
    "BASE_FORWARD",
    "BASE_BACKWARD",
    "CONDITIONER_FORWARD",
    "CONDITIONER_BACKWARD",
    "GUIDE_EVALUATION",
    "RESAMPLING_STEP",
    "ODE_OR_SDE_STEP",
    "DATA_ADAPTER_RECORD",
    "METRIC_DRAW_EVALUATION",
    "OTHER_DECLARED_OPERATION",
)
HARD_AXES = (
    "WALL_TIME",
    "ACCELERATOR_TIME",
    "PEAK_DEVICE_MEMORY",
    "PEAK_HOST_MEMORY",
    "MODEL_EVALUATION_COUNT",
    "PERSISTENT_BYTES",
    "FAILURE_COUNT",
    "PARAMETER_COUNT",
)
MAX_RATIONAL_COMPONENT_BITS = 4096
MAX_ACCUMULATED_COMPONENT_BITS = 8192

FORMULA_VALUE: Mapping[str, Any] = {
    "calculator_id": FORMULA_ID,
    "formula": (
        "C_M_D_EQUALS_SUM_OVER_PHASE_AND_RESOURCE_OF_INTEGER_COUNT_TIMES_"
        "EXACT_RATIONAL_WEIGHT"
    ),
    "phases": list(PHASES),
    "resource_events": list(RESOURCE_EVENTS),
    "accepted_count_type": "EXACT_NONNEGATIVE_PYTHON_INT_NOT_BOOL",
    "accepted_weight_type": (
        "STRICTLY_POSITIVE_EXACT_INT_OR_FRACTIONS_FRACTION_NOT_BOOL_OR_FLOAT"
    ),
    "normalized_component_bit_bound": MAX_RATIONAL_COMPONENT_BITS,
    "accumulated_component_bit_bound": MAX_ACCUMULATED_COMPONENT_BITS,
    "hardware_calibration_weights_populated": False,
    "hardware_or_environment_selected": False,
    "prospective_equal_ceiling_required_for_primary_pair_within_domain": True,
    "same_base_groups_cases_draws_precision_and_metric_workload_required": True,
    "failed_attempts_author_extensions_and_unique_preprocessing_charged": True,
    "unused_budget_transfer_or_postresult_topup_permitted": False,
    "scalar_cost_sufficient_without_hard_axis_ceilings": False,
    "additional_hard_axes": list(HARD_AXES),
    "fairness_interpretation": (
        "EQUAL_PROSPECTIVE_CEILING_AND_SELECTION_OPPORTUNITY_WITH_ALL_REALIZED_"
        "USE_REPORTED"
    ),
    "real_compute_budget_or_capacity_claimed": False,
}

POST_FIELDS = ("F164", "F165", "F168", "F169", "F170", "F171")
PRE_FIELDS = tuple(
    "F" + str(index).zfill(3)
    for index in range(1, 173)
    if "F" + str(index).zfill(3) not in POST_FIELDS
)
CLOSED_BEFORE = (
    "F007",
    "F008",
    "F009",
    "F010",
    "F011",
    "F012",
    "F013",
    "F014",
    "F015",
    "F016",
    "F017",
    "F018",
    "F060",
    "F106",
    "F107",
    "F108",
    "F113",
    "F128",
    "F129",
    "F148",
)
CLOSED_AFTER = tuple(sorted(CLOSED_BEFORE + ("F104",)))
OPEN_BEFORE = tuple(field for field in PRE_FIELDS if field not in CLOSED_BEFORE)
OPEN_AFTER = tuple(field for field in PRE_FIELDS if field not in CLOSED_AFTER)


class ValidationError(ValueError):
    """Exact arithmetic, custody, schema, or semantic validation failed."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    if type(value) is not dict:
        raise ValidationError("canonical JSON input must be an exact dictionary")
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise ValidationError("value is not canonical ASCII JSON") from error


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_payload_bytes(record) + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict:
        raise ValidationError("record must be an exact dictionary")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _canonical_payload_bytes(payload))


def _predecessor_record_sha256(record: Mapping[str, Any]) -> str:
    if type(record) is not dict or type(record.get("schema_version")) is not str:
        raise ValidationError("predecessor machine record has no exact schema")
    payload = dict(record)
    payload.pop("record_sha256", None)
    domain = (record["schema_version"] + "\0").encode("ascii")
    return _sha256(domain + _canonical_payload_bytes(payload))


def _object_without_duplicate_keys(
    pairs: Sequence[Tuple[str, Any]],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _parse_json(raw: bytes, label: str) -> Dict[str, Any]:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValidationError(label + " must be ASCII JSON") from error
    try:
        value = json.loads(text, object_pairs_hook=_object_without_duplicate_keys)
    except (json.JSONDecodeError, ValidationError) as error:
        raise ValidationError(label + " is not strict JSON") from error
    if type(value) is not dict:
        raise ValidationError(label + " top level must be an exact object")
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
        for index, expected_item in enumerate(expected):
            _strict_equal(actual[index], expected_item, label + "[" + str(index) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def _fraction(value: Any, label: str, *, positive: bool) -> Fraction:
    if type(value) is int:
        result = Fraction(value, 1)
    elif type(value) is Fraction:
        result = value
    else:
        raise ValidationError(label + " must be an exact int or Fraction")
    if positive and result <= 0:
        raise ValidationError(label + " must be strictly positive")
    if not positive and result < 0:
        raise ValidationError(label + " must be nonnegative")
    if (
        result.numerator.bit_length() > MAX_RATIONAL_COMPONENT_BITS
        or result.denominator.bit_length() > MAX_RATIONAL_COMPONENT_BITS
    ):
        raise ValidationError(label + " exceeds the normalized component bit bound")
    return result


def _count(value: Any, label: str) -> int:
    if type(value) is not int:
        raise ValidationError(label + " must be an exact nonnegative integer")
    if value < 0:
        raise ValidationError(label + " must be nonnegative")
    if value.bit_length() > MAX_RATIONAL_COMPONENT_BITS:
        raise ValidationError(label + " exceeds the count bit bound")
    return value


def _fraction_record(value: Fraction) -> Dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def exact_compute_cost(
    counts_by_phase: Mapping[str, Mapping[str, int]],
    weights: Mapping[str, Any],
) -> Dict[str, Any]:
    """Calculate the exact F104 scalar for one method/domain ledger."""

    if type(counts_by_phase) is not dict:
        raise ValidationError("counts_by_phase must be an exact dictionary")
    if tuple(counts_by_phase) != PHASES:
        raise ValidationError("phase key roster or order mismatch")
    if type(weights) is not dict:
        raise ValidationError("weights must be an exact dictionary")
    if tuple(weights) != RESOURCE_EVENTS:
        raise ValidationError("weight key roster or order mismatch")
    exact_weights = {
        event: _fraction(weights[event], "weight " + event, positive=True)
        for event in RESOURCE_EVENTS
    }
    phase_costs: Dict[str, Dict[str, int]] = {}
    total = Fraction(0, 1)
    for phase in PHASES:
        counts = counts_by_phase[phase]
        if type(counts) is not dict or tuple(counts) != RESOURCE_EVENTS:
            raise ValidationError(
                "resource count key roster or order mismatch: " + phase
            )
        phase_cost = Fraction(0, 1)
        for event in RESOURCE_EVENTS:
            phase_cost += (
                _count(counts[event], phase + " " + event) * exact_weights[event]
            )
        if (
            phase_cost.numerator.bit_length() > MAX_ACCUMULATED_COMPONENT_BITS
            or phase_cost.denominator.bit_length() > MAX_ACCUMULATED_COMPONENT_BITS
        ):
            raise ValidationError("phase cost exceeds accumulated bit bound")
        phase_costs[phase] = _fraction_record(phase_cost)
        total += phase_cost
    if (
        total.numerator.bit_length() > MAX_ACCUMULATED_COMPONENT_BITS
        or total.denominator.bit_length() > MAX_ACCUMULATED_COMPONENT_BITS
    ):
        raise ValidationError("total cost exceeds accumulated bit bound")
    return {
        "calculator_id": FORMULA_ID,
        "phase_costs": phase_costs,
        "total_cost": _fraction_record(total),
        "binary_float_used": False,
    }


def _zero_counts() -> Dict[str, Dict[str, int]]:
    return {
        phase: {event: 0 for event in RESOURCE_EVENTS}
        for phase in PHASES
    }


SYNTHETIC_WEIGHTS: Dict[str, Fraction] = {
    "BASE_FORWARD": Fraction(3, 2),
    "BASE_BACKWARD": Fraction(3, 1),
    "CONDITIONER_FORWARD": Fraction(1, 1),
    "CONDITIONER_BACKWARD": Fraction(2, 1),
    "GUIDE_EVALUATION": Fraction(1, 4),
    "RESAMPLING_STEP": Fraction(1, 2),
    "ODE_OR_SDE_STEP": Fraction(1, 3),
    "DATA_ADAPTER_RECORD": Fraction(1, 10),
    "METRIC_DRAW_EVALUATION": Fraction(2, 5),
    "OTHER_DECLARED_OPERATION": Fraction(1, 1),
}
SYNTHETIC_COUNTS = _zero_counts()
SYNTHETIC_COUNTS["PILOT"]["BASE_FORWARD"] = 2
SYNTHETIC_COUNTS["PILOT"]["GUIDE_EVALUATION"] = 4
SYNTHETIC_COUNTS["TUNING"]["BASE_FORWARD"] = 4
SYNTHETIC_COUNTS["TUNING"]["BASE_BACKWARD"] = 2
SYNTHETIC_COUNTS["TUNING"]["CONDITIONER_FORWARD"] = 4
SYNTHETIC_COUNTS["TUNING"]["CONDITIONER_BACKWARD"] = 2
SYNTHETIC_COUNTS["FINAL_TRAINING"]["BASE_FORWARD"] = 6
SYNTHETIC_COUNTS["FINAL_TRAINING"]["BASE_BACKWARD"] = 3
SYNTHETIC_COUNTS["FINAL_TRAINING"]["CONDITIONER_FORWARD"] = 6
SYNTHETIC_COUNTS["FINAL_TRAINING"]["CONDITIONER_BACKWARD"] = 3
SYNTHETIC_COUNTS["FINAL_TRAINING"]["DATA_ADAPTER_RECORD"] = 10
SYNTHETIC_COUNTS["CONFIRMATORY_INFERENCE"]["BASE_FORWARD"] = 8
SYNTHETIC_COUNTS["CONFIRMATORY_INFERENCE"]["CONDITIONER_FORWARD"] = 8
SYNTHETIC_COUNTS["CONFIRMATORY_INFERENCE"]["GUIDE_EVALUATION"] = 8
SYNTHETIC_COUNTS["CONFIRMATORY_INFERENCE"]["RESAMPLING_STEP"] = 4
SYNTHETIC_COUNTS["CONFIRMATORY_INFERENCE"]["ODE_OR_SDE_STEP"] = 6
SYNTHETIC_COUNTS["CONFIRMATORY_INFERENCE"]["METRIC_DRAW_EVALUATION"] = 10
SYNTHETIC_QUALIFICATION = exact_compute_cost(SYNTHETIC_COUNTS, SYNTHETIC_WEIGHTS)


# group, role, path, byte count, raw SHA-256, optional semantic self-digest
PREDECESSOR_SPECS: Tuple[
    Tuple[str, str, str, int, str, Optional[str]], ...
] = (
    (
        "BASELINE_COMPUTE_DRAFT_V1",
        "human",
        "PROJECT_BASELINE_CAPABILITY_COMPUTE_MODEL_DRAFT.md",
        10754,
        "33c9df737f45411861f2a60a9ed99220f61e4ac66461999ed0367c482b5dbe3d",
        None,
    ),
    (
        "BASELINE_COMPUTE_DRAFT_V1",
        "machine",
        "research/fixtures/manuscript_v3_baseline_capability_compute_model_draft_v1.json",
        24004,
        "be7a96ab4898e89cf0167fcce48204142143bf071a194b24d480091a6c60530a",
        "4cad447dca7896d45c424ee16594cddf3cd83e8497ed0cb3ec875ced03dd5840",
    ),
    (
        "BASELINE_COMPUTE_DRAFT_V1",
        "validator",
        "research/diagnostics/manuscript_v3_baseline_capability_compute_model_draft_v1.py",
        33361,
        "7032ad65de5b5f3f3aeed7e7d0b4866dbd318a3bc42850beeb9a1cfdd4a58297",
        None,
    ),
    (
        "BASELINE_COMPUTE_DRAFT_V1",
        "test",
        "tests/unit/test_manuscript_v3_baseline_capability_compute_model_draft_v1.py",
        20209,
        "2dbc64fd4830b410cda7c9911495cbfbf9603e4ec598f6af3e2094326a01cddc",
        None,
    ),
    (
        "GATE_A_B05_FREEZE_V1",
        "source",
        "src/heterodiff/evaluation/mixed_marked_ctmc_ou_known_law_certified_reference.py",
        124895,
        "98ffb1f42bee3efc097f378cc55a00b88f2d8570b9f3e8de1fe5f9a727f2e268",
        None,
    ),
    (
        "GATE_A_B05_FREEZE_V1",
        "human",
        "PROJECT_GATE_A_B05_KNOWN_LAW_DESIGN_FREEZE.md",
        13766,
        "ad03491578ba81c597906495f5aec5ceb36508cb9c0736f5f33af6d9babbc05d",
        None,
    ),
    (
        "GATE_A_B05_FREEZE_V1",
        "machine",
        "research/fixtures/manuscript_v3_gate_a_b05_known_law_design_freeze_v1.json",
        269205,
        "c49ef829cab9c8a7459216d37cb70382d4c0027e20aa3c343c5fbd0ed825ee32",
        "d81b52f94fe420b50f3aa5bf5d0edc97c5b55bdedf19c5bb9a8b499a23397e8b",
    ),
    (
        "GATE_A_B05_FREEZE_V1",
        "validator",
        "research/diagnostics/manuscript_v3_gate_a_b05_known_law_design_freeze_v1.py",
        33523,
        "d53a5656e4322e5b169bd859af531ea208ccaf413ddd9660a31c350d93cc2eb2",
        None,
    ),
    (
        "GATE_A_B05_FREEZE_V1",
        "test",
        "tests/unit/test_manuscript_v3_gate_a_b05_known_law_design_freeze_v1.py",
        18517,
        "052190e27ea71f06b1f93ba8df647867d813447464870c6e0f78c75f61b8524a",
        None,
    ),
)
PREDECESSOR_GROUP_COUNTS = {
    "BASELINE_COMPUTE_DRAFT_V1": 4,
    "GATE_A_B05_FREEZE_V1": 5,
}


def _canonical_relative_path(relative: Any) -> Tuple[str, ...]:
    if type(relative) is not str or not relative or "\\" in relative:
        raise ValidationError("binding path must be a nonempty POSIX string")
    path = Path(relative)
    if path.is_absolute() or relative.startswith("/"):
        raise ValidationError("binding path must be relative")
    if "/".join(path.parts) != relative:
        raise ValidationError("binding path must be canonical")
    if any(part in (".", "..") for part in path.parts):
        raise ValidationError("binding path traversal is forbidden")
    return tuple(path.parts)


def _ancestor_snapshot(root: Path, target: Path) -> Tuple[Tuple[int, int, int], ...]:
    snapshots: List[Tuple[int, int, int]] = []
    current = target.parent
    while True:
        status = current.lstat()
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise ValidationError("unsafe ancestor: " + str(current))
        snapshots.append((status.st_dev, status.st_ino, stat.S_IFMT(status.st_mode)))
        if current == root:
            return tuple(snapshots)
        if root not in current.parents:
            raise ValidationError("binding path escaped the workspace root")
        current = current.parent


def _fingerprint(value: os.stat_result) -> Tuple[int, int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
        stat.S_IFMT(value.st_mode),
        value.st_nlink,
    )


def _stable_read(root: Path, relative: str) -> bytes:
    if not isinstance(root, Path) or not root.is_absolute():
        raise ValidationError("workspace root must be an absolute Path")
    parts = _canonical_relative_path(relative)
    target = root.joinpath(*parts)
    ancestors_before = _ancestor_snapshot(root, target)
    before_path = target.lstat()
    if stat.S_ISLNK(before_path.st_mode) or not stat.S_ISREG(before_path.st_mode):
        raise ValidationError("binding must be a regular non-symlink file")
    if stat.S_IMODE(before_path.st_mode) != 0o644:
        raise ValidationError("binding mode must be exactly 0644")
    if before_path.st_nlink != 1:
        raise ValidationError("binding must have exactly one hard link")
    descriptor = os.open(target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
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
    after_path = target.lstat()
    if not (
        _fingerprint(before_path)
        == _fingerprint(before_fd)
        == _fingerprint(after_fd)
        == _fingerprint(after_path)
    ):
        raise ValidationError("binding changed during read: " + relative)
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


def _predecessor_state(
    root: Path,
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
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
            if expected_record is None:
                raise ValidationError("machine predecessor lacks a semantic digest")
            if parsed.get("record_sha256") != expected_record:
                raise ValidationError("predecessor semantic digest field mismatch")
            if _predecessor_record_sha256(parsed) != expected_record:
                raise ValidationError("predecessor semantic digest recomputation failed")
        bindings.append(
            _binding(ordinal, group, role, path, raw, expected_record)
        )
    return bindings, records


def _package_bindings(root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for ordinal, (role, path) in enumerate(
        (("human", HUMAN_PATH), ("validator", VALIDATOR_PATH), ("test", TEST_PATH))
    ):
        rows.append(
            _binding(ordinal, "CURRENT_PACKAGE", role, path, _stable_read(root, path))
        )
    return rows


def _validate_predecessor_semantics(
    records: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    baseline_path = (
        "research/fixtures/"
        "manuscript_v3_baseline_capability_compute_model_draft_v1.json"
    )
    b05_path = (
        "research/fixtures/"
        "manuscript_v3_gate_a_b05_known_law_design_freeze_v1.json"
    )
    if set(records) != {baseline_path, b05_path}:
        raise ValidationError("machine predecessor roster mismatch")
    baseline = records[baseline_path]
    if (
        baseline.get("global_state") != GLOBAL_STATE
        or baseline.get("package_kind")
        != "STATIC_BASELINE_CAPABILITY_AND_COMPUTE_MODEL_DRAFT_NO_SCIENTIFIC_EFFECT"
    ):
        raise ValidationError("baseline predecessor state changed")
    _strict_equal(
        baseline.get("matched_compute_contract"),
        dict(FORMULA_VALUE),
        "baseline matched-compute contract",
    )
    draft_identity = baseline.get("draft_identity")
    nonclosure = baseline.get("nonclosure")
    if type(draft_identity) is not dict or type(nonclosure) is not dict:
        raise ValidationError("baseline predecessor boundary is absent")
    if (
        draft_identity.get("B06_closed") is not False
        or draft_identity.get("B08_closed") is not False
        or draft_identity.get("compute_capacity_selected_or_reserved") is not False
        or nonclosure.get("blocker_status") != {"B06": "OPEN", "B08": "OPEN"}
        or nonclosure.get("unresolved_fields_closed") != 0
        or nonclosure.get("matched_total_compute_formula_written_to_preregistration")
        is not False
        or nonclosure.get("hardware_or_capacity_fields_written_to_preregistration")
        is not False
    ):
        raise ValidationError("baseline predecessor nonclosure changed")
    open_values = nonclosure.get("open_field_values")
    if type(open_values) is not dict or open_values.get("F104", "ABSENT") is not None:
        raise ValidationError("baseline F104 was not null/open")
    _strict_equal(
        baseline.get("synthetic_qualification"),
        SYNTHETIC_QUALIFICATION,
        "baseline synthetic exact qualification",
    )

    b05 = records[b05_path]
    transition = b05.get("count_transition")
    effects = b05.get("project_effects_and_nonclaims")
    if (
        b05.get("global_state") != GLOBAL_STATE
        or type(transition) is not dict
        or type(effects) is not dict
    ):
        raise ValidationError("B05 predecessor state is absent")
    if transition.get("after") != {
        "post_execution_closed": 0,
        "post_execution_open": 6,
        "pre_execution_closed": 20,
        "pre_execution_open": 146,
        "total_closed": 20,
        "total_open": 152,
    }:
        raise ValidationError("B05 predecessor current count changed")
    if tuple(transition.get("closed_after_ids", ())) != CLOSED_BEFORE:
        raise ValidationError("B05 predecessor closed-field roster changed")
    if tuple(transition.get("open_pre_after_ids", ())) != OPEN_BEFORE:
        raise ValidationError("B05 predecessor open-field roster changed")
    if (
        "F104" not in transition["open_pre_after_ids"]
        or transition.get("blockers_open_after") != 12
        or transition.get("blockers_closed") != 0
        or transition.get("formal_tests_closed") != 0
        or transition.get("results_filled") != 0
        or effects.get("all_12_blockers_remain_open") is not True
        or effects.get("scientific_execution_performed") is not False
        or effects.get("runtime_or_submission_performed") is not False
        or effects.get("result_or_claim_promoted") is not False
    ):
        raise ValidationError("B05 predecessor nonclosure changed")
    return {
        "baseline_formula_exactly_recovered": True,
        "baseline_synthetic_total_cost": 85,
        "f104_open_before": True,
        "pre_execution_open_before": 146,
        "pre_execution_closed_before": 20,
        "post_execution_open_before": 6,
        "post_execution_closed_before": 0,
        "blockers_open_before": 12,
        "formal_tests_closed_before": 0,
        "results_filled_before": 0,
    }


def expected_record(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    predecessor_bindings, records = _predecessor_state(root)
    predecessor_receipt = _validate_predecessor_semantics(records)
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "reported_date": REPORTED_DATE,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": PACKAGE_KIND,
        "control_predicate": CONTROL_PREDICATE,
        "authority_provenance": {
            "normalized_visible_text": AUTHORITY_TEXT,
            "normalized_visible_text_sha256": _sha256(
                AUTHORITY_TEXT.encode("utf-8")
            ),
            "bounded_offline_local_project_work_authorized": True,
            "raw_transport_bytes_or_conversation_envelope_bound": False,
            "identity_or_time_externally_authenticated": False,
            "network_contact_repository_license_or_data_access_authorized": False,
            "hardware_reservation_operational_receipt_or_runtime_capture_authorized": False,
            "entropy_training_scientific_or_production_execution_authorized": False,
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
        "predecessor_projection_receipt": predecessor_receipt,
        "field_closures": [
            {
                "field_id": "F104",
                "json_pointer": F104_POINTER,
                "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_PARAMETERIZED_FORMULA_FREEZE",
                "value": dict(FORMULA_VALUE),
            }
        ],
        "f104_parameterization_boundary": {
            "formula_and_accounting_semantics_frozen": True,
            "resource_counts_populated": False,
            "calibration_weights_populated": False,
            "hardware_or_environment_selected": False,
            "method_training_inference_or_tuning_budgets_populated": False,
            "resource_ceilings_or_allocations_populated": False,
            "actual_compute_capacity_or_reservation_present": False,
            "synthetic_vector_is_budget_or_capacity_evidence": False,
            "f104_may_be_evaluated_only_after_future_inputs_are_frozen": True,
        },
        "count_transition": {
            "before": {
                "pre_execution_open": 146,
                "pre_execution_closed": 20,
                "post_execution_open": 6,
                "post_execution_closed": 0,
                "total_open": 152,
                "total_closed": 20,
            },
            "closed_by_package": {
                "field_ids": ["F104"],
                "pre_execution": 1,
                "post_execution": 0,
                "total": 1,
            },
            "after": {
                "pre_execution_open": 145,
                "pre_execution_closed": 21,
                "post_execution_open": 6,
                "post_execution_closed": 0,
                "total_open": 151,
                "total_closed": 21,
            },
            "blockers_open_after": 12,
            "blockers_closed": 0,
            "formal_tests_closed": 0,
            "results_filled": 0,
        },
        "comprehensive_field_sweep": {
            "total_pre_execution_fields": 166,
            "total_post_execution_fields": 6,
            "closed_before_ids": list(CLOSED_BEFORE),
            "eligible_now_ids": ["F104"],
            "closed_after_ids": list(CLOSED_AFTER),
            "open_after_ids": list(OPEN_AFTER),
            "open_after_count": 145,
            "all_post_execution_fields_remain_open": list(POST_FIELDS),
            "additional_eligible_field_count": 0,
        },
        "project_effects_and_nonclaims": {
            "only_field_closed": "F104",
            "F062_F103_remain_open": True,
            "F139_F147_remain_open": True,
            "F150_F162_remain_open": True,
            "B06_remains_open": True,
            "B08_remains_open": True,
            "B12_remains_open": True,
            "all_12_blockers_remain_open": True,
            "formal_test_28_status": "OPEN",
            "formal_test_29_status": "OPEN",
            "formal_test_30_status": "PENDING",
            "R1_R2_R3_R4_remain_unexecuted": True,
            "hardware_or_capacity_selected_reserved_or_claimed": False,
            "runtime_or_operational_receipt_created": False,
            "network_contact_repository_license_or_data_access_performed": False,
            "entropy_training_scientific_or_production_execution_performed": False,
            "result_or_claim_promoted": False,
            "submission_performed": False,
            "tracker_or_evidence_ledger_edited": False,
        },
        "evidence_ready_registration": {
            "conditional_on_independent_acceptance": True,
            "proposed_text": EVIDENCE_READY_REGISTRATION,
            "registration_performed_by_this_package": False,
            "permitted_field_delta": ["F104"],
            "permitted_blocker_delta": [],
            "permitted_formal_test_delta": [],
            "permitted_result_delta": [],
        },
        "qualification_boundary": {
            "validator_read_only": True,
            "calculator_accepts_caller_supplied_synthetic_values_only": True,
            "caller_values_verified_as_real_resource_or_scientific_evidence": False,
            "validator_writer_network_connector_subprocess_entropy_data_training_"
            "runtime_production_or_science_route_present": False,
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
        raise ValidationError("package machine record semantic digest mismatch")
    _strict_equal(actual, expected, "package machine record")
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": actual["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "F104_closed": True,
        "unresolved_fields_closed": 1,
        "effective_pre_execution_open": 145,
        "effective_pre_execution_closed": 21,
        "effective_post_execution_open": 6,
        "effective_post_execution_closed": 0,
        "effective_open_blocker_count": 12,
        "B06_open": True,
        "B08_open": True,
        "B12_open": True,
        "formal_tests_closed": 0,
        "results_filled": 0,
        "scientific_execution": False,
        "tracker_edit_performed": False,
        "validation": "PASS",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=True, sort_keys=True, separators=(",", ":")))
