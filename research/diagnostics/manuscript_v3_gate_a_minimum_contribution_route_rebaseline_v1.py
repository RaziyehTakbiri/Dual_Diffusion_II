"""Read-only validator for the Gate-A minimum-contribution rebaseline.

The module validates exact local package and predecessor custody and exposes
pure project-control state algebra.  It has no writer, network, connector,
entropy, runtime, training, data, or scientific-execution route.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-gate-a-minimum-contribution-route-" "rebaseline-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "GATE_A_MINIMUM_EMPIRICAL_CONTRIBUTION_ROUTE_REBASELINED_PREOUTCOME"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
REPORTED_DATE = "2026-08-31"
PACKAGE_KIND = "ADDITIVE_PREOUTCOME_MINIMUM_CONTRIBUTION_ROUTE_CONTROL"

ROUTE_CONTROL_PREDICATE = "EMPIRICAL_CONTRIBUTION_ROUTE_FROZEN_PREOUTCOME"
CONTRIBUTION_CLASS = (
    "HIGH_QUALITY_EMPIRICAL_BENCHMARK_AND_ASSOCIATION_MECHANISM_EVALUATION_"
    "WITH_NO_NOVEL_MECHANISM_CLAIM"
)
GO_STATE = "EMPIRICAL_CONTRIBUTION_GO"
NO_GO_STATE = "EMPIRICAL_CONTRIBUTION_TERMINAL_NO_GO"
PENDING_STATE = "EMPIRICAL_CONTRIBUTION_PENDING"
COMPONENT_STATES = ("PENDING", "PASS", "TERMINAL_NO_GO")
F106_VALUE = "POSITIVE_DIRECT_MINUS_GUIDE_FAVORS_GUIDE"
F108_VALUE = "TRAIN_ONLY"

HUMAN_PATH = "PROJECT_GATE_A_MINIMUM_CONTRIBUTION_ROUTE_REBASELINE.md"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.py"
)
PACKAGE_ROSTER = (HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH)

AUTHORITY_TEXT = (
    "Okay, sounds good. What I want you to do is to set aside a significant "
    "portion of work to do such that you are busy for around 8 hours, because "
    "I am going to sleep, and dont want my absence to make you idle."
)


class ValidationError(ValueError):
    """Raised when exact custody, schema, or route semantics fail closed."""


COMPONENT_DEFINITIONS: Tuple[Mapping[str, str], ...] = (
    {
        "component_id": "R1_VALID_PASS",
        "pass_predicate": (
            "EVERY_FROZEN_R1_PHASE_HAS_ACCEPTED_CANONICAL_SAME_ATTEMPT_PASS_"
            "RECEIPT_IN_REQUIRED_ORDER"
        ),
        "terminal_no_go_predicate": (
            "ANY_R1_FAIL_HOLD_INFRA_ABORT_PROTOCOL_INVALID_MISSING_OR_INVALID_"
            "TERMINAL_RECEIPT_OR_PROHIBITED_RETRY"
        ),
    },
    {
        "component_id": "R2_VALID_PASS",
        "pass_predicate": (
            "ACCEPTED_CANONICAL_R2_PASS_AFTER_VALID_R1_PASS_AND_ALL_OTHER_"
            "ELIGIBILITY_GATES"
        ),
        "terminal_no_go_predicate": (
            "ANY_R2_FAIL_HOLD_INFRA_ABORT_PROTOCOL_INVALID_MISSING_OR_INVALID_"
            "TERMINAL_RECEIPT_OR_R2_BEFORE_R1"
        ),
    },
    {
        "component_id": "R3_PHYS_DOMAIN_ADMITTED",
        "pass_predicate": (
            "EXACT_PHYSIONET_INSTANCE_ADMITTED_PREOUTCOME_UNDER_ALL_"
            "ACQUISITION_LICENSE_GOVERNANCE_REPRESENTATION_SPLIT_SUPPORT_TASK_"
            "AND_CUSTODY_RULES"
        ),
        "terminal_no_go_predicate": (
            "PHYSIONET_PREOUTCOME_NONADMISSION_OR_INVALID_OR_MISSING_"
            "ADMISSION_AT_TERMINAL_ROUTE_DECISION"
        ),
    },
    {
        "component_id": "R4_RETAIL_DOMAIN_ADMITTED",
        "pass_predicate": (
            "EXACT_ONLINE_RETAIL_II_INSTANCE_ADMITTED_PREOUTCOME_UNDER_ALL_"
            "ACQUISITION_LICENSE_PRIVACY_REPRESENTATION_SPLIT_SUPPORT_TASK_"
            "AND_CUSTODY_RULES"
        ),
        "terminal_no_go_predicate": (
            "RETAIL_PREOUTCOME_NONADMISSION_OR_INVALID_OR_MISSING_ADMISSION_"
            "AT_TERMINAL_ROUTE_DECISION"
        ),
    },
    {
        "component_id": "MATCHED_COMPUTE_BASELINE_SUITE_PASS",
        "pass_predicate": (
            "EVERY_REQUIRED_CONTROL_LITERATURE_COMPARATOR_AND_EXTERNAL_DOMAIN_"
            "BASELINE_IMPLEMENTED_OR_PREOUTCOME_JUSTIFIED_AND_ALL_FROZEN_"
            "OBJECTIVE_CONDITIONING_MODEL_TASK_AND_PLANNED_REALIZED_COMPUTE_"
            "MATCHING_RULES_PASS"
        ),
        "terminal_no_go_predicate": (
            "REQUIRED_COMPARATOR_MISSING_POSTOUTCOME_SUBSTITUTED_UNJUSTIFIABLY_"
            "INAPPLICABLE_OR_EQUIVALENT_OR_COMPUTE_OR_INTERFACE_MATCHING_FAILS"
        ),
    },
    {
        "component_id": "R3_PHYS_PRIMARY_EFFECT_PASS",
        "pass_predicate": (
            "PHYSIONET_MULTIPLICITY_ADJUSTED_LOWER_BOUND_FOR_NATURAL_GROUP_"
            "WEIGHTED_PAIRED_DIRECT_MINUS_GUIDE_PRIMARY_LOSS_EXCEEDS_FROZEN_"
            "POSITIVE_MINIMUM_EFFECT"
        ),
        "terminal_no_go_predicate": (
            "PHYSIONET_VALID_FROZEN_PRIMARY_ANALYSIS_DOES_NOT_PASS_EXACT_" "EFFECT_RULE"
        ),
    },
    {
        "component_id": "R4_RETAIL_PRIMARY_EFFECT_PASS",
        "pass_predicate": (
            "RETAIL_MULTIPLICITY_ADJUSTED_LOWER_BOUND_FOR_NATURAL_GROUP_"
            "WEIGHTED_PAIRED_DIRECT_MINUS_GUIDE_PRIMARY_LOSS_EXCEEDS_FROZEN_"
            "POSITIVE_MINIMUM_EFFECT"
        ),
        "terminal_no_go_predicate": (
            "RETAIL_VALID_FROZEN_PRIMARY_ANALYSIS_DOES_NOT_PASS_EXACT_EFFECT_" "RULE"
        ),
    },
    {
        "component_id": "R3_PHYS_NO_REGRESSION_PASS",
        "pass_predicate": (
            "EVERY_PREREGISTERED_PHYSIONET_BASE_QUALITY_CALIBRATION_COVERAGE_"
            "SUPPORT_EVENT_FIDELITY_FAILURE_LATENCY_MEMORY_AND_COMPUTE_"
            "CONSTRAINT_PASSES_ITS_FROZEN_SIMULTANEOUS_NO_REGRESSION_MARGIN_"
            "ON_FULL_ADMITTED_ANALYSIS_POPULATION"
        ),
        "terminal_no_go_predicate": (
            "ANY_REQUIRED_PHYSIONET_CONSTRAINT_FAILS_IS_UNDEFINED_WITHOUT_"
            "FROZEN_RULE_OR_IS_FAVORABLY_EXCLUDED"
        ),
    },
    {
        "component_id": "R4_RETAIL_NO_REGRESSION_PASS",
        "pass_predicate": (
            "EVERY_PREREGISTERED_RETAIL_BASE_QUALITY_CALIBRATION_COVERAGE_"
            "SUPPORT_EVENT_FIDELITY_FAILURE_LATENCY_MEMORY_AND_COMPUTE_"
            "CONSTRAINT_PASSES_ITS_FROZEN_SIMULTANEOUS_NO_REGRESSION_MARGIN_"
            "ON_FULL_ADMITTED_ANALYSIS_POPULATION"
        ),
        "terminal_no_go_predicate": (
            "ANY_REQUIRED_RETAIL_CONSTRAINT_FAILS_IS_UNDEFINED_WITHOUT_"
            "FROZEN_RULE_OR_IS_FAVORABLY_EXCLUDED"
        ),
    },
    {
        "component_id": "R3_PHYS_ASSOCIATION_MECHANISM_CONTRAST_PASS",
        "pass_predicate": (
            "FULL_ASSOCIATION_AWARE_ROUTE_PASSES_PRECOMMITTED_PHYSIONET_"
            "MATCHED_COMPUTE_CONTRAST_AGAINST_ASSOCIATION_DESTROYED_OR_"
            "FACTORIZED_EVENTWISE_CONTROL_USING_PREOUTCOME_MARGIN_AND_"
            "INFERENCE_RULE"
        ),
        "terminal_no_go_predicate": (
            "PHYSIONET_ASSOCIATION_CONTRAST_FAILS_IS_ABSENT_OR_IS_CHANGED_OR_"
            "SELECTED_AFTER_OUTCOME"
        ),
    },
    {
        "component_id": "R4_RETAIL_ASSOCIATION_MECHANISM_CONTRAST_PASS",
        "pass_predicate": (
            "FULL_ASSOCIATION_AWARE_ROUTE_PASSES_PRECOMMITTED_RETAIL_MATCHED_"
            "COMPUTE_CONTRAST_AGAINST_ASSOCIATION_DESTROYED_OR_FACTORIZED_"
            "EVENTWISE_CONTROL_USING_PREOUTCOME_MARGIN_AND_INFERENCE_RULE"
        ),
        "terminal_no_go_predicate": (
            "RETAIL_ASSOCIATION_CONTRAST_FAILS_IS_ABSENT_OR_IS_CHANGED_OR_"
            "SELECTED_AFTER_OUTCOME"
        ),
    },
    {
        "component_id": "PRECOMMITTED_KNOWN_LAW_AND_TWO_DOMAIN_SCALING_PASS",
        "pass_predicate": (
            "EVERY_FROZEN_KNOWN_LAW_AND_BOTH_REAL_DOMAIN_SCALING_COORDINATE_"
            "PASSES_PRECOMMITTED_ACCURACY_BASE_QUALITY_ASSOCIATION_COMPUTE_"
            "AND_NO_REGRESSION_RULES_WITHOUT_POSTRESULT_TOPUP"
        ),
        "terminal_no_go_predicate": (
            "ANY_REQUIRED_SCALING_COORDINATE_FAILS_IS_MISSING_OR_IS_REDEFINED_"
            "AFTER_OBSERVATION"
        ),
    },
    {
        "component_id": "FULL_FAILURE_ACCOUNTING_AND_CEILING_PASS",
        "pass_predicate": (
            "EVERY_SCHEDULED_AND_ABORTED_ATTEMPT_RETAINED_EXCLUSION_DEVIATION_"
            "AND_FAILURE_LEDGER_COMPLETE_NO_FAVORABLE_RETRY_OR_OMISSION_AND_"
            "EVERY_FROZEN_FAILURE_RATE_CEILING_PASSES_ITS_STATED_DENOMINATOR"
        ),
        "terminal_no_go_predicate": (
            "RECEIPT_MISSING_ATTEMPT_FAVORABLY_EXCLUDED_RETRIED_OR_RELABELLED_"
            "DENOMINATOR_CHANGED_OR_REQUIRED_FAILURE_CEILING_EXCEEDED"
        ),
    },
    {
        "component_id": "CLEAN_ROOM_REPRODUCTION_PASS",
        "pass_predicate": (
            "INDEPENDENT_CLEAN_ROOM_RECONSTRUCTS_FROZEN_ENVIRONMENT_AND_"
            "ARTIFACTS_RECOMPUTES_EVERY_PROMOTION_INPUT_AND_REPRODUCES_ALL_"
            "COMPONENT_STATES_AND_OVERALL_DECISION_FROM_HASH_BOUND_INPUTS"
        ),
        "terminal_no_go_predicate": (
            "CLEAN_ROOM_AUDIT_ABSENT_AT_TERMINAL_REVIEW_CANNOT_RECONSTRUCT_"
            "REQUIRED_INPUT_OR_DISAGREES_WITH_REQUIRED_VALUE_OR_DECISION"
        ),
    },
)
COMPONENT_IDS = tuple(row["component_id"] for row in COMPONENT_DEFINITIONS)


# group, role, path, byte count, raw SHA-256, optional semantic record SHA-256
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
        "CKS_COUNT_NORMALIZED_EVENT_THEOREM_V1",
        "human",
        "PROJECT_CKS_COUNT_NORMALIZED_EVENT_THEOREM.md",
        16151,
        "53445cb8617fb6573105ad8912616967dcad601dcf6b30b4a28d3bf9a3034c15",
        None,
    ),
    (
        "CKS_COUNT_NORMALIZED_EVENT_THEOREM_V1",
        "machine",
        "research/fixtures/manuscript_v3_cks_count_normalized_event_theorem_v1.json",
        10073,
        "33dd22403ad7d71375c53c05028dd59567f127e233a8dc247a7a7ea730f13f6f",
        "613dd2a1be716f382215769babca2503bd9b0c6cd9ae48fa2972e5df353743a3",
    ),
    (
        "CKS_COUNT_NORMALIZED_EVENT_THEOREM_V1",
        "validator",
        "research/diagnostics/manuscript_v3_cks_count_normalized_event_theorem_v1.py",
        25728,
        "722d5781f05646e3252609939768a8e021274288ca90d9142eee7c220bf30576",
        None,
    ),
    (
        "CKS_COUNT_NORMALIZED_EVENT_THEOREM_V1",
        "test",
        "tests/unit/test_manuscript_v3_cks_count_normalized_event_theorem_v1.py",
        15192,
        "527e6349962e7180d19cfa6ebad9747a638b37a06225d3cc068fff7f1c15b61b",
        None,
    ),
    (
        "C17_PO13_INITIALIZER_KL_PROOF_V1",
        "human",
        "PROJECT_C17_PO13_INITIALIZER_KL_PROOF.md",
        15990,
        "a2a6ed5cd7e95b9c64fcb9ff0b4bf37124eb5bb4d9d471d6959822b54eb91071",
        None,
    ),
    (
        "C17_PO13_INITIALIZER_KL_PROOF_V1",
        "machine",
        "research/fixtures/manuscript_v3_c17_po13_initializer_kl_proof_v1.json",
        23091,
        "ac7338877223bc4aeab58d28289d7342ce4bd6acf6f21573f372f9a537233a64",
        "3e3576a1a861057994badd775d7e2d8db4854bf9b9584dfa93720a5871ecf9f8",
    ),
    (
        "C17_PO13_INITIALIZER_KL_PROOF_V1",
        "validator",
        "research/diagnostics/manuscript_v3_c17_po13_initializer_kl_proof_v1.py",
        45225,
        "962d58194d4ee2b7a4af9703929f3e2f5302bb72fb79f9d2689720ae2bb212b2",
        None,
    ),
    (
        "C17_PO13_INITIALIZER_KL_PROOF_V1",
        "test",
        "tests/unit/test_manuscript_v3_c17_po13_initializer_kl_proof_v1.py",
        24807,
        "a4c7f7b864eefca13dc5c74d9da4e544165073cf19f5aa4277992df93cd402ca",
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
)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_payload_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_payload_bytes(record) + b"\n"


def record_sha256(record: Mapping[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256(RECORD_DOMAIN + _canonical_payload_bytes(payload))


def _input_record_sha256(record: Mapping[str, Any]) -> str:
    schema = record.get("schema_version")
    if type(schema) is not str or not schema.isascii() or not schema:
        raise ValidationError("predecessor schema invalid")
    payload = dict(record)
    payload.pop("record_sha256", None)
    domain = (schema + "\0").encode("ascii")
    return _sha256(domain + _canonical_payload_bytes(payload))


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
        raise ValidationError(label + " must be ASCII JSON") from exc
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
        raise ValidationError(label + " top level must be object")
    return value


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


def _safe_path(root: Path, relative: str) -> Path:
    if type(relative) is not str or not relative:
        raise ValidationError("relative path invalid")
    rel = Path(relative)
    if rel.is_absolute() or not rel.parts or ".." in rel.parts:
        raise ValidationError("unsafe relative path")
    root_resolved = root.resolve(strict=True)
    root_status = os.lstat(root_resolved)
    if not stat.S_ISDIR(root_status.st_mode):
        raise ValidationError("root is not directory")
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
    record_digest: Optional[str] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
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
    if record_digest is not None:
        result["record_sha256"] = record_digest
    return result


def _predecessor_bindings(root: Path) -> List[Dict[str, Any]]:
    bindings: List[Dict[str, Any]] = []
    for ordinal, spec in enumerate(PREDECESSOR_SPECS):
        group, role, path, expected_bytes, expected_sha, expected_record = spec
        raw = _stable_read(root, path)
        if len(raw) != expected_bytes or _sha256(raw) != expected_sha:
            raise ValidationError("predecessor exact-byte mismatch: " + path)
        if expected_record is not None:
            parsed = _parse_json(raw, "predecessor " + path)
            if parsed.get("record_sha256") != expected_record:
                raise ValidationError("predecessor registered self digest mismatch")
            if _input_record_sha256(parsed) != expected_record:
                raise ValidationError("predecessor recomputed self digest mismatch")
        bindings.append(_binding(ordinal, group, role, path, raw, expected_record))
    return bindings


def _package_bindings(root: Path) -> List[Dict[str, Any]]:
    rows = []
    for ordinal, (role, path) in enumerate(
        (("human", HUMAN_PATH), ("validator", VALIDATOR_PATH), ("test", TEST_PATH))
    ):
        rows.append(
            _binding(ordinal, "CURRENT_PACKAGE", role, path, _stable_read(root, path))
        )
    return rows


def _checked_states(states: Any, label: str = "component states") -> Dict[str, str]:
    if type(states) is not dict:
        raise ValidationError(label + " must contain exact built-in dict roster")
    if any(type(key) is not str for key in states):
        raise ValidationError(label + " keys must be exact built-in str")
    if set(states) != set(COMPONENT_IDS):
        raise ValidationError(label + " must contain exact built-in dict roster")
    checked: Dict[str, str] = {}
    for component_id in COMPONENT_IDS:
        value = states[component_id]
        if type(value) is not str or value not in COMPONENT_STATES:
            raise ValidationError(label + " has invalid state for " + component_id)
        checked[component_id] = value
    return checked


def evaluate_contribution_route(states: Any) -> Dict[str, Any]:
    """Project the frozen route algebra over synthetic caller-supplied states."""

    checked = _checked_states(states)
    passed = [key for key in COMPONENT_IDS if checked[key] == "PASS"]
    pending = [key for key in COMPONENT_IDS if checked[key] == "PENDING"]
    failed = [key for key in COMPONENT_IDS if checked[key] == "TERMINAL_NO_GO"]
    if failed:
        route_state = NO_GO_STATE
    elif len(passed) == len(COMPONENT_IDS):
        route_state = GO_STATE
    else:
        route_state = PENDING_STATE
    return {
        "schema_version": (
            "heterodiff-manuscript-v3-minimum-contribution-route-projection-v1"
        ),
        "contribution_class": CONTRIBUTION_CLASS,
        "route_state": route_state,
        "empirical_contribution_go": route_state == GO_STATE,
        "empirical_contribution_terminal_no_go": route_state == NO_GO_STATE,
        "empirical_contribution_pending": route_state == PENDING_STATE,
        "passed_components": passed,
        "pending_components": pending,
        "terminal_no_go_components": failed,
        "terminal_no_go_absorbing": True,
        "c17_required_for_go": False,
        "post_outcome_route_fallback_permitted": False,
        "caller_states_verified_as_evidence": False,
        "scientific_result": False,
    }


def advance_route_states(previous: Any, proposed: Any) -> Dict[str, Any]:
    """Reject reopening, rollback, or replacement after a frozen transition."""

    before = _checked_states(previous, "previous component states")
    after = _checked_states(proposed, "proposed component states")
    prior_projection = evaluate_contribution_route(before)
    if prior_projection["empirical_contribution_terminal_no_go"]:
        if before != after:
            raise ValidationError("terminal NO_GO route cannot be changed")
        return prior_projection
    for component_id in COMPONENT_IDS:
        old = before[component_id]
        new = after[component_id]
        if old == "PASS" and new == "PENDING":
            raise ValidationError("PASS cannot return to PENDING")
        if old == "TERMINAL_NO_GO" and new != "TERMINAL_NO_GO":
            raise ValidationError("terminal component cannot reopen")
    return evaluate_contribution_route(after)


def expected_record(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    predecessors = _predecessor_bindings(root)
    package_bindings = _package_bindings(root)
    components = [
        {
            "ordinal": ordinal,
            "component_id": row["component_id"],
            "current_state": "PENDING",
            "pass_predicate": row["pass_predicate"],
            "terminal_no_go_predicate": row["terminal_no_go_predicate"],
        }
        for ordinal, row in enumerate(COMPONENT_DEFINITIONS)
    ]
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "reported_date": REPORTED_DATE,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "package_kind": PACKAGE_KIND,
        "authority_provenance": {
            "normalized_visible_text": AUTHORITY_TEXT,
            "normalized_visible_text_sha256": _sha256(AUTHORITY_TEXT.encode("utf-8")),
            "local_autonomous_project_work_authorized": True,
            "agent_selected_paths_schema_class_predicates_and_direction": True,
            "raw_transport_bytes_or_trailing_html_space_bound": False,
            "network_or_source_contact_authorized": False,
            "data_acquisition_or_access_authorized": False,
            "scientific_entropy_runtime_training_or_execution_authorized": False,
            "claim_promotion_or_submission_authorized": False,
        },
        "package_file_roster": list(PACKAGE_ROSTER),
        "package_bindings_excluding_machine_self": package_bindings,
        "machine_self_binding": {
            "path": MACHINE_PATH,
            "semantic_self_digest_field": "record_sha256",
            "raw_self_hash_embedded": False,
        },
        "predecessor_bindings": predecessors,
        "predecessor_group_counts": {
            "EXECUTION_PREREGISTRATION": 2,
            "PREEXECUTION_CLOSURE_V2": 4,
            "CKS_COUNT_NORMALIZED_EVENT_THEOREM_V1": 4,
            "C17_PO13_INITIALIZER_KL_PROOF_V1": 4,
            "GATE_A_LOCAL_STATISTICAL_FREEZE_V1": 4,
            "total": 18,
        },
        "c17_disposition": {
            "bound_current_route_decision": (
                "REAL_DOMAIN_C17_PROMOTION_UNDER_CURRENT_FORK_B_OBSERVABILITY_" "NO_GO"
            ),
            "c17_required_real_domain_headline": False,
            "c17_required_for_empirical_contribution_go": False,
            "c17_proved": False,
            "c17_real_domain_promotion_permitted": False,
            "c17_novel_mechanism_claim_permitted": False,
            "permitted_residual_roles": [
                "UNPROVED_SPECIFICATION",
                "CONDITIONAL_THEOREM_TARGET",
                "FINITE_OR_MIXED_KNOWN_LAW_FALSIFICATION_ROUTE",
            ],
            "legacy_c17_field_or_blocker_closed_by_package": False,
            "post_outcome_c17_revival_permitted": False,
        },
        "contribution_route": {
            "route_control_predicate": ROUTE_CONTROL_PREDICATE,
            "contribution_class": CONTRIBUTION_CLASS,
            "novel_mechanism_or_method_claim_required": False,
            "novel_mechanism_or_method_claim_permitted_by_route": False,
            "exact_state_domain": list(COMPONENT_STATES),
            "go_predicate": "ALL_14_COMPONENTS_PASS",
            "terminal_no_go_predicate": ("ANY_OF_14_COMPONENTS_TERMINAL_NO_GO"),
            "pending_predicate": "NO_COMPONENT_TERMINAL_NO_GO_AND_NOT_ALL_PASS",
            "components": components,
            "current_projection": {
                "route_state": PENDING_STATE,
                "empirical_contribution_go": False,
                "empirical_contribution_terminal_no_go": False,
                "empirical_contribution_pending": True,
                "all_14_component_states": "PENDING",
            },
            "components_are_conjunctive_and_noncompensatory": True,
            "cross_domain_pooling_or_rescue_permitted": False,
            "secondary_metric_rescue_permitted": False,
            "terminal_no_go_absorbing": True,
            "post_outcome_route_fallback_permitted": False,
            "replacement_metric_sign_threshold_seed_baseline_control_domain_"
            "claim_or_c17_route_permitted": False,
            "different_future_project_is_current_route_fallback": False,
            "predicate_achievement_evidenced_by_package": False,
        },
        "metric_direction_freeze": {
            "field_id": "F106",
            "json_pointer": "/metric_and_estimand_plan/favorable_direction",
            "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_FREEZE",
            "value": F106_VALUE,
            "every_admissible_primary_metric_represented_as_lower_is_better_loss": True,
            "higher_is_better_source_metric_requires_preoutcome_fixed_order_"
            "reversing_transform": True,
            "transform_units_domain_ties_missing_nonfinite_and_numeric_"
            "implementation_frozen_preoutcome": True,
            "outcome_dependent_sign_or_transform_permitted": False,
            "primary_score_token_semantics": (
                "PRIMARY_LOSS_DIRECT_MINUS_PRIMARY_LOSS_GUIDE"
            ),
            "strictly_positive_difference_favors_guide": True,
            "zero_difference_favors_guide": False,
            "F105_primary_metric_id_value": None,
            "F105_primary_metric_id_open": True,
            "B04_open": True,
        },
        "metric_fitting_scope_freeze": {
            "field_id": "F108",
            "json_pointer": (
                "/metric_and_estimand_plan/training_only_metric_fitting_rule"
            ),
            "status": "CLOSED_BY_EXACT_DUPLICATE_SCOPE_PROJECTION",
            "value": F108_VALUE,
            "source_json_pointer": (
                "/split_and_leakage_plan/primary_metric_fitting_scope"
            ),
            "source_value": "TRAIN_ONLY",
            "source_and_projection_semantically_identical_scope": True,
            "primary_metric_parameter_or_data_dependent_transform_fit_on_"
            "validation_permitted": False,
            "primary_metric_parameter_or_data_dependent_transform_fit_on_"
            "test_permitted": False,
            "primary_metric_selected": False,
            "fitting_algorithm_selected": False,
            "kernel_bandwidth_or_numeric_value_selected": False,
            "transform_or_approximation_selected": False,
            "validation_checkpoint_or_model_selection_rule_selected": False,
            "B04_open": True,
        },
        "field_closures": [
            {
                "field_id": "F106",
                "json_pointer": "/metric_and_estimand_plan/favorable_direction",
                "status": "CLOSED_BY_ADDITIVE_PREOUTCOME_FREEZE",
                "value": F106_VALUE,
                "evidence": (
                    "ALL_ADMISSIBLE_PRIMARY_METRICS_USE_LOWER_IS_BETTER_LOSS_"
                    "REPRESENTATION_BEFORE_PROTECTED_OUTCOMES"
                ),
            },
            {
                "field_id": "F108",
                "json_pointer": (
                    "/metric_and_estimand_plan/training_only_metric_fitting_rule"
                ),
                "status": "CLOSED_BY_EXACT_DUPLICATE_SCOPE_PROJECTION",
                "value": F108_VALUE,
                "source_json_pointer": (
                    "/split_and_leakage_plan/primary_metric_fitting_scope"
                ),
                "source_value": "TRAIN_ONLY",
            },
        ],
        "count_transition": {
            "before": {
                "pre_execution_open": 161,
                "pre_execution_closed": 5,
                "post_execution_open": 6,
                "post_execution_closed": 0,
                "total_open": 167,
                "total_closed": 5,
            },
            "closed_by_package": {
                "field_ids": ["F106", "F108"],
                "pre_execution": 2,
                "post_execution": 0,
                "total": 2,
            },
            "after": {
                "pre_execution_open": 159,
                "pre_execution_closed": 7,
                "post_execution_open": 6,
                "post_execution_closed": 0,
                "total_open": 165,
                "total_closed": 7,
            },
            "blockers_open_after": 12,
            "blockers_closed": 0,
            "formal_tests_closed": 0,
            "results_filled": 0,
        },
        "project_control_effects": {
            "minimum_contribution_route_rebaselined_preoutcome": True,
            "c17_retired_as_required_real_domain_headline": True,
            "empirical_contribution_go_achieved": False,
            "empirical_contribution_terminal_no_go_achieved": False,
            "empirical_contribution_pending": True,
            "unresolved_fields_closed": 2,
            "only_fields_closed": ["F106", "F108"],
            "B04_closed": False,
            "F105_closed": False,
            "all_other_fields_closed": False,
            "blockers_closed": 0,
            "formal_tests_closed": 0,
            "result_slots_filled": 0,
            "gate_a_venue_or_primary_claim_item_closed": False,
            "tracker_edit_performed": False,
        },
        "scope_and_nonclaims": {
            "all_14_component_states_are_pending": True,
            "r1_or_r2_validated": False,
            "domain_admitted": False,
            "matched_compute_baseline_suite_validated": False,
            "two_domain_effect_or_no_regression_result_observed": False,
            "association_mechanism_contrast_observed": False,
            "scaling_result_observed": False,
            "failure_rate_observed": False,
            "clean_room_reproduction_completed": False,
            "primary_metric_selected": False,
            "scientific_execution_performed": False,
            "data_or_test_outcome_accessed": False,
            "network_or_external_contact_performed": False,
            "scientific_entropy_consumed": False,
            "runtime_or_training_performed": False,
            "claim_promoted": False,
            "submission_or_venue_quality_established": False,
        },
        "qualification_boundary": {
            "validator_read_only": True,
            "validator_imports_project_science": False,
            "synthetic_state_projection_only": True,
            "validator_or_pure_state_surface_writer_present": False,
            "validator_or_pure_state_surface_network_connector_subprocess_or_"
            "scientific_worker_route_present": False,
            "validator_or_pure_state_surface_scientific_seed_or_protocol_"
            "entropy_route_present": False,
            "qualification_launches_python_and_pytest_interpreters": True,
            "hostile_tests_write_disposable_pytest_temporary_copies": True,
            "hostile_tests_mutate_only_disposable_copy_bytes_modes_and_links": True,
            "canonical_package_or_predecessor_bytes_modified_by_qualification": False,
            "global_process_absence_claimed": False,
            "global_filesystem_write_absence_claimed": False,
            "ordinary_temporary_name_randomness_absence_claimed": False,
            "cache_disabled_qualification_required": True,
            "caller_supplied_pass_labels_are_scientific_evidence": False,
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
        raise ValidationError("package machine record self digest mismatch")
    _strict_equal(actual, expected, "package machine record")
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": actual["record_sha256"],
        "route_control_predicate": ROUTE_CONTROL_PREDICATE,
        "current_contribution_state": PENDING_STATE,
        "empirical_contribution_go_achieved": False,
        "empirical_contribution_terminal_no_go_achieved": False,
        "c17_required_real_domain_headline": False,
        "post_outcome_route_fallback_permitted": False,
        "F106_closed": True,
        "F106_value": F106_VALUE,
        "F108_closed": True,
        "F108_value": F108_VALUE,
        "F105_open": True,
        "B04_open": True,
        "unresolved_fields_closed": 2,
        "effective_unresolved_field_count": 165,
        "effective_open_blocker_count": 12,
        "gate_a_venue_or_primary_claim_item_closed": False,
        "tracker_edit_performed": False,
        "scientific_result": False,
        "validation": "PASS",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))
