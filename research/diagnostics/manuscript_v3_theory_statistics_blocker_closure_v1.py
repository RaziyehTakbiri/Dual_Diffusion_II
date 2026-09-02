#!/usr/bin/env python3
"""Read-only validator for the theory/statistics blocker-closure package."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Dict, Mapping, Tuple


ROOT = Path(os.path.abspath(__file__)).parents[2]
MACHINE_PATH = "research/fixtures/manuscript_v3_theory_statistics_blocker_closure_v1.json"
SOURCE_PATH = "src/heterodiff/evaluation/preoutcome_theory_statistics_contract.py"
R64_ADAPTER_PATH = "src/heterodiff/evaluation/fixed_r64_cks_statistical_adapter.py"
HUMAN_PATH = "PROJECT_THEORY_STATISTICS_BLOCKER_CLOSURE.md"
C17_PATH = "manuscript_v3/c17_retirement_no_claim_successor_v1.md"
STATISTICAL_SUCCESSOR_PATH = "manuscript_v3/manuscript_v3_f109_f112_statistical_successor_v1.md"
VALIDATOR_PATH = "research/diagnostics/manuscript_v3_theory_statistics_blocker_closure_v1.py"
TEST_PATH = "tests/unit/test_manuscript_v3_theory_statistics_blocker_closure_v1.py"
F105_INTEGRATION_HUMAN_PATH = "PROJECT_F105_MANUSCRIPT_PRODUCTION_INTEGRATION.md"
F105_PRODUCTION_SOURCE_PATH = "src/heterodiff/evaluation/two_domain_count_normalized_event_cks_production.py"
F105_PRODUCTION_TEST_PATH = "tests/unit/test_two_domain_count_normalized_event_cks_production.py"
F105_DISPLAY_MD_PATH = "manuscript_v3/manuscript_v3_f105_metric_integration_successor_v2.md"
F105_DISPLAY_TEX_PATH = "manuscript_v3/manuscript_v3_f105_metric_integration_successor_v2.tex"
F105_CLAIM_PATH = "manuscript_v3/claim_ledger_f105_metric_integration_successor_v2.md"
F105_INTEGRATION_MACHINE_PATH = "research/fixtures/manuscript_v3_f105_manuscript_production_integration_v1.json"
F105_INTEGRATION_VALIDATOR_PATH = "research/diagnostics/manuscript_v3_f105_manuscript_production_integration_v1.py"
F105_INTEGRATION_PACKAGE_TEST_PATH = "tests/unit/test_manuscript_v3_f105_manuscript_production_integration_v1.py"
F105_INTEGRATION_REVIEW_PATH = "PROJECT_F105_MANUSCRIPT_PRODUCTION_INTEGRATION_INDEPENDENT_REVIEW.md"
F105_EXACT_SOURCE_PATH = "src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py"
F105_EXACT_MACHINE_PATH = "research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json"
F105_LOCKED_ROUTE_PATH = "manuscript_v3/manuscript_v3_locked_route_successor_v1.md"
SCHEMA = "heterodiff-manuscript-v3-theory-statistics-blocker-closure-v1"
EXPECTED_SOURCE_SHA256 = (
    "1ad767ea4e6d8fec0b19837ba26a9bd6f920fc90be48fc7bb4059c30b10ea718"
)
EXPECTED_R64_ADAPTER_SHA256 = (
    "63dbc81b804ed643406d401559b38305654ef43d0b9a4ade17feb9e2152eb278"
)
EXPECTED_F105_INTEGRATION_MACHINE_RAW_SHA256 = (
    "251edc5792dd5545c40eb45ec528f98b133a0b154f5d0f5ef3bb3db4df325126"
)
EXPECTED_F105_INTEGRATION_SEMANTIC_SHA256 = (
    "6c5480374ed3d1993e28711ef8640d8f12c0cadf40a51e0ce7d8991f5233f5ae"
)
EXPECTED_F105_INTEGRATION_REVIEW_SHA256 = (
    "a8e6c5d42847b8dcf28e238bddd5d006852bbff85eb161967ca1ff398c204d82"
)
EXPECTED_SEED_REGISTRY_SHA256 = (
    "73ecdd8ecfb4c3dd164bd47e5f71bebc8d62c0bde4d46a20c4262291d88fa350"
)
EXPECTED_C17_WORDING = (
    "Claim C17 is retired from this route. We do not state or imply an "
    "end-to-end path-KL or total-variation theorem, an excess-risk-to-hybrid-"
    "Dirichlet control, or any empirical consequence attributed to C17."
)
EXPECTED_REAL_REAL_FLOOR_ID = (
    "VALIDATION_ONLY_GROUP_DISJOINT_SAME_CKS_BIASED_MMD2_"
    "DETERMINISTIC_256_SPLIT_Q95_NOT_SUBTRACTED"
)
EXPECTED_CONFIDENCE_METHOD_ID = (
    "FIXED_N_SEED_LEVEL_ONE_SIDED_HOEFFDING_"
    "EXACT_LOG_BOUND_TWO_DOMAIN_HOLM_V1"
)
EXPECTED_PILOT_VARIANCE_SOURCE = (
    "NO_EMPIRICAL_PILOT_DISTRIBUTION_FREE_CKS_PAIRED_RANGE_"
    "MINUS3_TO3_WIDTH6"
)
EXPECTED_B05_CERTIFICATION_SCOPE_ID = "B05_FROZEN_CONSTRAINT_INPUT_ENVELOPE_V1"
EXPECTED_B05_TERMINAL_STATUSES = (
    "COMPLETE",
    "ALGORITHMIC_FAILURE",
    "NONFINITE",
    "OOM_OR_TIMEOUT",
    "INFRA_ABORT",
)
EXPECTED_B05_VALUE_SPECS = (
    ("calibration_coverage_abs_error_upper", "ABSOLUTE_PROBABILITY_ERROR", "CERTIFIED_UPPER_ENDPOINT"),
    ("support_violation_count", "INTEGER_VIOLATION_COUNT", "CERTIFIED_EXACT_COUNT"),
    ("fidelity_guide_minus_direct_upper", "FROZEN_EVENT_COUNT_TYPE_MARK_TIME_ERROR_DIFFERENCE", "CERTIFIED_UPPER_ENDPOINT"),
    ("initializer_kl_upper_nat", "NAT", "CERTIFIED_UPPER_ENDPOINT"),
    ("association_tv_upper", "TOTAL_VARIATION", "CERTIFIED_UPPER_ENDPOINT"),
    ("guide_latency_upper", "NANOSECOND", "CERTIFIED_UPPER_ENDPOINT"),
    ("direct_latency_lower", "NANOSECOND", "CERTIFIED_POSITIVE_LOWER_ENDPOINT"),
    ("guide_peak_memory_upper", "BYTE", "CERTIFIED_UPPER_ENDPOINT"),
    ("direct_peak_memory_lower", "BYTE", "CERTIFIED_POSITIVE_LOWER_ENDPOINT"),
    ("guide_total_compute_upper", "F104_MATCHED_TOTAL_COMPUTE_UNIT", "CERTIFIED_UPPER_ENDPOINT"),
    ("direct_total_compute_lower", "F104_MATCHED_TOTAL_COMPUTE_UNIT", "CERTIFIED_POSITIVE_LOWER_ENDPOINT"),
)

EXPECTED_BINDING_PATHS = (
    SOURCE_PATH,
    R64_ADAPTER_PATH,
    C17_PATH,
    STATISTICAL_SUCCESSOR_PATH,
    HUMAN_PATH,
    VALIDATOR_PATH,
    TEST_PATH,
    F105_INTEGRATION_HUMAN_PATH,
    F105_PRODUCTION_SOURCE_PATH,
    F105_PRODUCTION_TEST_PATH,
    F105_DISPLAY_MD_PATH,
    F105_DISPLAY_TEX_PATH,
    F105_CLAIM_PATH,
    F105_INTEGRATION_MACHINE_PATH,
    F105_INTEGRATION_VALIDATOR_PATH,
    F105_INTEGRATION_PACKAGE_TEST_PATH,
    F105_INTEGRATION_REVIEW_PATH,
    F105_EXACT_SOURCE_PATH,
    F105_EXACT_MACHINE_PATH,
    F105_LOCKED_ROUTE_PATH,
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json",
    "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json",
    "PROJECT_GATE_A_MINIMUM_CONTRIBUTION_ROUTE_REBASELINE.md",
    "PROJECT_C17_PO13_INITIALIZER_KL_PROOF.md",
    "PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE.md",
    "PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE_INDEPENDENT_REVIEW.md",
    "PROJECT_GATE_A_LOCAL_STATISTICAL_AND_DOWNSTREAM_DECISION_FREEZE.md",
    "PROJECT_GATE_A_B05_KNOWN_LAW_DESIGN_FREEZE.md",
    "PROJECT_F120_INITIALIZER_ERROR_DIRECTION_FREEZE_INDEPENDENT_REVIEW_V2.md",
    "PROJECT_F122_ASSOCIATION_ERROR_DIRECTION_FREEZE_INDEPENDENT_REVIEW.md",
    "PROJECT_F137_HIERARCHICAL_PAIRED_ANALYSIS_FORMULA_FREEZE_INDEPENDENT_REVIEW.md",
    "PROJECT_REAL_DOMAIN_POWER_ALLOCATION_ROUTE.md",
)
EXPECTED_BINDING_ROLES = (
    "SOURCE",
    "R64_ADAPTER",
    "C17_SUCCESSOR",
    "STATISTICAL_SUCCESSOR",
    "HUMAN",
    "VALIDATOR",
    "TEST",
) + ("F105_JOINT_DEPENDENCY",) * 13 + ("PREDECESSOR",) * 12

EXPECTED_FIELD_IDS = (
    "F001", "F002", "F003", "F004", "F005", "F006",
    "F109", "F110", "F111", "F112",
    "F114", "F115", "F116", "F117", "F118", "F119",
    "F121", "F123", "F124", "F125", "F126", "F127", "F149",
    "F130", "F131", "F132", "F133", "F134", "F135", "F136", "F138",
)
EXPECTED_FIELD_POINTERS = (
    "/theory_and_known_law_plan/c17_final_theorem_statement",
    "/theory_and_known_law_plan/c17_assumption_inventory",
    "/theory_and_known_law_plan/c17_proof_artifact_path",
    "/theory_and_known_law_plan/c17_code_definition_crosswalk_path",
    "/theory_and_known_law_plan/excess_logistic_risk_to_hybrid_dirichlet_control_statement",
    "/theory_and_known_law_plan/coercivity_or_identifiability_assumptions",
    "/metric_and_estimand_plan/conditional_draws_per_case",
    "/metric_and_estimand_plan/minimum_meaningful_effect",
    "/metric_and_estimand_plan/real_real_floor_definition",
    "/metric_and_estimand_plan/confidence_interval_method",
    "/metric_and_estimand_plan/constraint_metrics/0/direction",
    "/metric_and_estimand_plan/constraint_metrics/0/threshold_or_margin",
    "/metric_and_estimand_plan/constraint_metrics/1/direction",
    "/metric_and_estimand_plan/constraint_metrics/1/threshold_or_margin",
    "/metric_and_estimand_plan/constraint_metrics/2/direction",
    "/metric_and_estimand_plan/constraint_metrics/2/threshold_or_margin",
    "/metric_and_estimand_plan/constraint_metrics/3/threshold_or_margin",
    "/metric_and_estimand_plan/constraint_metrics/4/threshold_or_margin",
    "/metric_and_estimand_plan/constraint_metrics/5/threshold_or_margin",
    "/metric_and_estimand_plan/constraint_metrics/6/threshold_or_margin",
    "/metric_and_estimand_plan/constraint_metrics/7/threshold_or_margin",
    "/metric_and_estimand_plan/constraint_metrics/8/threshold_or_margin",
    "/stopping_failure_and_exclusion_plan/maximum_admissible_failure_rate",
    "/power_and_seed_plan/minimum_effect_used_for_power",
    "/power_and_seed_plan/pilot_variance_source",
    "/power_and_seed_plan/independent_training_seed_count",
    "/power_and_seed_plan/training_seed_values_or_generation_receipt",
    "/power_and_seed_plan/natural_group_count_by_domain",
    "/power_and_seed_plan/conditioning_cases_per_group",
    "/power_and_seed_plan/conditional_draws_per_case",
    "/power_and_seed_plan/confidence_interval_resample_count",
)


class ValidationError(RuntimeError):
    pass


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise ValidationError("record is not canonical ASCII JSON") from error


def semantic_digest(record: Mapping[str, Any]) -> str:
    if record.get("schema_version") != SCHEMA:
        raise ValidationError("schema mismatch")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return hashlib.sha256(SCHEMA.encode("ascii") + b"\0" + _canonical_bytes(payload)).hexdigest()


def _open_component(parent_fd: int, name: str, *, directory: bool) -> int:
    if not name or name in (".", "..") or "/" in name or "\x00" in name:
        raise ValidationError("unsafe path component")
    flags = os.O_RDONLY
    if directory and hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return os.open(name, flags, dir_fd=parent_fd)


def _entry_status(parent_fd: int, name: str) -> os.stat_result:
    try:
        return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except (OSError, TypeError, NotImplementedError) as error:
        raise ValidationError("cannot lstat path component: " + name) from error


def _custody_identity(status: os.stat_result) -> Tuple[int, int, int, int]:
    return (status.st_dev, status.st_ino, status.st_mode, status.st_nlink)


def _open_bound_directory(
    parent_fd: int,
    name: str,
    *,
    descriptors: list[int],
    edges: list[tuple[int, str, Tuple[int, int, int, int]]],
    held_directories: list[tuple[int, Tuple[int, int, int, int]]],
) -> int:
    before = _entry_status(parent_fd, name)
    if not stat.S_ISDIR(before.st_mode):
        raise ValidationError("non-directory or symlink path component: " + name)
    try:
        child = _open_component(parent_fd, name, directory=True)
    except OSError as error:
        raise ValidationError("cannot open directory component: " + name) from error
    descriptors.append(child)
    after = os.fstat(child)
    identity = _custody_identity(before)
    if not stat.S_ISDIR(after.st_mode) or _custody_identity(after) != identity:
        raise ValidationError("directory component changed while opening: " + name)
    edges.append((parent_fd, name, identity))
    held_directories.append((child, identity))
    return child


def stable_read(relative_path: str, *, root: Path = ROOT) -> bytes:
    rel = Path(relative_path)
    if rel.is_absolute() or not rel.parts or any(part in ("", ".", "..") for part in rel.parts):
        raise ValidationError("unsafe relative path: " + relative_path)
    root_path = Path(os.fspath(root))
    if (
        not root_path.is_absolute()
        or not root_path.parts
        or root_path.parts[0] != os.sep
        or any(part in ("", ".", "..") for part in root_path.parts[1:])
    ):
        raise ValidationError("custody root must be an absolute path")
    descriptors: list[int] = []
    edges: list[tuple[int, str, Tuple[int, int, int, int]]] = []
    held_directories: list[tuple[int, Tuple[int, int, int, int]]] = []
    try:
        try:
            current = os.open(
                os.sep,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
            )
        except OSError as error:
            raise ValidationError("cannot open filesystem root") from error
        descriptors.append(current)
        root_status = os.fstat(current)
        if not stat.S_ISDIR(root_status.st_mode):
            raise ValidationError("filesystem root is not a directory")
        held_directories.append((current, _custody_identity(root_status)))
        for part in root_path.parts[1:]:
            current = _open_bound_directory(
                current,
                part,
                descriptors=descriptors,
                edges=edges,
                held_directories=held_directories,
            )
        for part in rel.parts[:-1]:
            current = _open_bound_directory(
                current,
                part,
                descriptors=descriptors,
                edges=edges,
                held_directories=held_directories,
            )
        leaf_name = rel.parts[-1]
        leaf_entry_before = _entry_status(current, leaf_name)
        if not stat.S_ISREG(leaf_entry_before.st_mode):
            raise ValidationError("leaf is not a regular non-symlink file: " + relative_path)
        try:
            leaf = _open_component(current, leaf_name, directory=False)
        except OSError as error:
            raise ValidationError("cannot open leaf: " + relative_path) from error
        descriptors.append(leaf)
        before = os.fstat(leaf)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o644
            or before.st_nlink != 1
            or _custody_identity(before) != _custody_identity(leaf_entry_before)
        ):
            raise ValidationError("leaf custody invalid: " + relative_path)
        edges.append((current, leaf_name, _custody_identity(before)))
        chunks = []
        while True:
            chunk = os.read(leaf, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(leaf)
        if (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_nlink,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_nlink,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValidationError("file changed during read: " + relative_path)
        raw = b"".join(chunks)
        if len(raw) != before.st_size:
            raise ValidationError("short read: " + relative_path)
        for descriptor, identity in held_directories:
            if _custody_identity(os.fstat(descriptor)) != identity:
                raise ValidationError("held directory custody changed during read")
        for parent_fd, name, identity in reversed(edges):
            if _custody_identity(_entry_status(parent_fd, name)) != identity:
                raise ValidationError("path entry changed during read: " + name)
        return raw
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _load_record(raw: bytes) -> Dict[str, Any]:
    if not raw.endswith(b"\n") or b"\r" in raw:
        raise ValidationError("machine record requires one LF convention")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValidationError("machine record must be ASCII") from error
    try:
        record = json.loads(text, object_pairs_hook=_pairs_no_duplicates)
    except (json.JSONDecodeError, ValidationError) as error:
        raise ValidationError("invalid machine JSON") from error
    if type(record) is not dict:
        raise ValidationError("machine record must be an object")
    if raw != _canonical_bytes(record) + b"\n":
        raise ValidationError("machine record is not canonical")
    if record.get("record_sha256") != semantic_digest(record):
        raise ValidationError("machine semantic digest mismatch")
    return record


def _load_foreign_json(raw: bytes, *, label: str) -> Dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValidationError(label + " must be UTF-8 JSON") from error
    try:
        record = json.loads(text, object_pairs_hook=_pairs_no_duplicates)
    except (json.JSONDecodeError, ValidationError) as error:
        raise ValidationError(label + " is not strict JSON") from error
    if type(record) is not dict:
        raise ValidationError(label + " must be an object")
    return record


def _verify_bindings(record: Mapping[str, Any], *, root: Path) -> Dict[str, bytes]:
    bindings = record.get("bindings")
    if type(bindings) is not list or not bindings:
        raise ValidationError("bindings missing")
    seen = set()
    raws: Dict[str, bytes] = {}
    for ordinal, binding in enumerate(bindings):
        if type(binding) is not dict or binding.get("ordinal") != ordinal:
            raise ValidationError("binding ordinal mismatch")
        if binding.get("role") != EXPECTED_BINDING_ROLES[ordinal]:
            raise ValidationError("binding role mismatch")
        path = binding.get("path")
        if type(path) is not str or path in seen:
            raise ValidationError("binding path invalid or duplicated")
        seen.add(path)
        raw = stable_read(path, root=root)
        if binding.get("bytes") != len(raw):
            raise ValidationError("binding size mismatch: " + path)
        if binding.get("raw_sha256") != hashlib.sha256(raw).hexdigest():
            raise ValidationError("binding digest mismatch: " + path)
        if binding.get("mode_octal") != "0644" or binding.get("nlink") != 1:
            raise ValidationError("binding custody declaration mismatch")
        if binding.get("terminal_lf") is not raw.endswith(b"\n"):
            raise ValidationError("binding LF declaration mismatch")
        raws[path] = raw
    if tuple(binding["path"] for binding in bindings) != EXPECTED_BINDING_PATHS:
        raise ValidationError("binding path roster mismatch")
    return raws


def _verify_f105_joint_dependency(raws: Mapping[str, bytes]) -> None:
    machine_raw = raws[F105_INTEGRATION_MACHINE_PATH]
    if hashlib.sha256(machine_raw).hexdigest() != EXPECTED_F105_INTEGRATION_MACHINE_RAW_SHA256:
        raise ValidationError("accepted F105 integration machine raw digest mismatch")
    machine = _load_foreign_json(machine_raw, label="F105 integration machine")
    if machine.get("schema_version") != "heterodiff-f105-manuscript-production-integration-v1":
        raise ValidationError("F105 integration schema mismatch")
    projection = dict(machine)
    projection["record_sha256"] = None
    semantic = hashlib.sha256(
        (machine["schema_version"] + "\0").encode("ascii")
        + _canonical_bytes(projection)
    ).hexdigest()
    if (
        machine.get("record_sha256") != EXPECTED_F105_INTEGRATION_SEMANTIC_SHA256
        or semantic != EXPECTED_F105_INTEGRATION_SEMANTIC_SHA256
    ):
        raise ValidationError("accepted F105 integration semantic digest mismatch")
    if machine.get("state") != "F105_MANUSCRIPT_DISPLAY_AND_PRODUCTION_EVALUATOR_INTEGRATED_PREOUTCOME":
        raise ValidationError("accepted F105 integration state mismatch")
    target = machine.get("target_predicate")
    if type(target) is not dict or target.get("value") is not True:
        raise ValidationError("accepted F105 integration predicate is not true")
    metric_semantics = machine.get("metric_semantics")
    if type(metric_semantics) is not dict or metric_semantics.get("draw_count_formal_domain") != {
        "minimum": 2,
        "maximum": 128,
    }:
        raise ValidationError("accepted F105 general draw domain mismatch")
    closure = machine.get("closure_effect")
    if (
        type(closure) is not dict
        or closure.get("f109_f112_closed") is not False
        or closure.get("b04_closed") is not False
        or closure.get("field_count_delta") != 0
        or closure.get("blocker_count_delta") != 0
    ):
        raise ValidationError("accepted F105 predecessor closure boundary mismatch")
    expected_package_paths = (
        F105_INTEGRATION_HUMAN_PATH,
        F105_PRODUCTION_SOURCE_PATH,
        F105_PRODUCTION_TEST_PATH,
        F105_DISPLAY_MD_PATH,
        F105_DISPLAY_TEX_PATH,
        F105_CLAIM_PATH,
    )
    package_bindings = machine.get("package_bindings")
    if type(package_bindings) is not list or tuple(
        item.get("path") for item in package_bindings if type(item) is dict
    ) != expected_package_paths:
        raise ValidationError("accepted F105 package-binding roster mismatch")
    for item in package_bindings:
        path = item["path"]
        if (
            item.get("bytes") != len(raws[path])
            or item.get("raw_sha256") != hashlib.sha256(raws[path]).hexdigest()
        ):
            raise ValidationError("accepted F105 package binding mismatch: " + path)
    expected_frozen_paths = (
        F105_EXACT_SOURCE_PATH,
        F105_EXACT_MACHINE_PATH,
        F105_LOCKED_ROUTE_PATH,
    )
    frozen_inputs = machine.get("frozen_inputs")
    if type(frozen_inputs) is not list or tuple(
        item.get("path") for item in frozen_inputs if type(item) is dict
    ) != expected_frozen_paths:
        raise ValidationError("accepted F105 frozen-input roster mismatch")
    for item in frozen_inputs:
        path = item["path"]
        if item.get("raw_sha256") != hashlib.sha256(raws[path]).hexdigest():
            raise ValidationError("accepted F105 frozen input mismatch: " + path)
    if machine.get("validator_and_tests_outside_semantic_self_binding") != [
        F105_INTEGRATION_VALIDATOR_PATH,
        F105_INTEGRATION_PACKAGE_TEST_PATH,
    ]:
        raise ValidationError("accepted F105 validator/test boundary mismatch")
    review_raw = raws[F105_INTEGRATION_REVIEW_PATH]
    if hashlib.sha256(review_raw).hexdigest() != EXPECTED_F105_INTEGRATION_REVIEW_SHA256:
        raise ValidationError("accepted F105 independent-review digest mismatch")
    review = " ".join(review_raw.decode("utf-8").split())
    for required in (
        "**Disposition:** `GO`",
        "**Severity count:** `P0=0`, `P1=0`, `P2=0`",
        EXPECTED_F105_INTEGRATION_SEMANTIC_SHA256,
        EXPECTED_F105_INTEGRATION_MACHINE_RAW_SHA256,
        "later additive confirmatory successor that narrows F109 to exactly `R=64`",
    ):
        if required not in review:
            raise ValidationError("accepted F105 independent-review wording mismatch")
    for path in expected_package_paths + (
        F105_INTEGRATION_MACHINE_PATH,
        F105_INTEGRATION_VALIDATOR_PATH,
        F105_INTEGRATION_PACKAGE_TEST_PATH,
    ):
        if hashlib.sha256(raws[path]).hexdigest() not in review:
            raise ValidationError(
                "accepted F105 review does not bind current byte: " + path
            )


def _verify_source_ast(raw: bytes) -> None:
    try:
        tree = ast.parse(raw.decode("utf-8"), filename=SOURCE_PATH)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValidationError("source does not parse") from error
    allowed_roots = {"__future__", "dataclasses", "fractions", "hashlib", "math", "typing"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] not in allowed_roots:
                    raise ValidationError("source import outside allowlist")
        elif isinstance(node, ast.ImportFrom):
            if node.module is None or node.module.split(".", 1)[0] not in allowed_roots:
                raise ValidationError("source from-import outside allowlist")
        elif isinstance(node, (ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom)):
            raise ValidationError("source contains an effectful control surface")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"open", "exec", "eval", "compile", "__import__", "input"}:
                raise ValidationError("source contains a forbidden call")


def _literal_source_assignment(raw: bytes, name: str) -> Any:
    try:
        tree = ast.parse(raw.decode("utf-8"), filename=SOURCE_PATH)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValidationError("source does not parse") from error
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == name
        ):
            try:
                return ast.literal_eval(node.value)
            except (TypeError, ValueError, SyntaxError) as error:
                raise ValidationError("source literal assignment changed: " + name) from error
    raise ValidationError("source literal assignment missing: " + name)


def _verify_r64_adapter_ast(raw: bytes) -> None:
    try:
        tree = ast.parse(raw.decode("utf-8"), filename=R64_ADAPTER_PATH)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValidationError("R64 adapter does not parse") from error
    allowed = {
        "__future__",
        "dataclasses",
        "math",
        "heterodiff.evaluation.two_domain_count_normalized_event_cks_production",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name not in allowed for alias in node.names):
                raise ValidationError("R64 adapter import outside allowlist")
        elif isinstance(node, ast.ImportFrom):
            if node.module not in allowed:
                raise ValidationError("R64 adapter from-import outside allowlist")
        elif isinstance(node, (ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom)):
            raise ValidationError("R64 adapter contains an effectful control surface")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"open", "exec", "eval", "compile", "__import__", "input"}:
                raise ValidationError("R64 adapter contains a forbidden call")
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    expected_positional = {
        "fixed_r64_conditional_cks_score": ("addressed_draws", "target"),
        "fixed_r64_direct_minus_guide": (
            "direct_addressed_draws",
            "guide_addressed_draws",
            "target",
        ),
    }
    for name, expected in expected_positional.items():
        node = functions.get(name)
        if node is None or tuple(argument.arg for argument in node.args.args) != expected:
            raise ValidationError("R64 adapter address-aware signature mismatch: " + name)
    classes = {
        node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
    }
    address_class = classes.get("F109DrawAddress")
    if address_class is None:
        raise ValidationError("R64 adapter address class missing")
    address_fields = tuple(
        node.target.id
        for node in address_class.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    )
    if address_fields != (
        "domain_id",
        "seed_id",
        "group_id",
        "case_id",
        "draw_id",
        "conditioning_id",
    ):
        raise ValidationError("R64 adapter address field roster mismatch")


def _fraction_record(numerator: int, denominator: int = 1) -> Dict[str, int]:
    return {"numerator": numerator, "denominator": denominator}


def recompute_seed_registry_sha256() -> str:
    prefix = b"HETERODIFF-CONFIRMATORY-TRAINING-SEED-REGISTRY-V1\x00"
    values = tuple(
        int.from_bytes(
            hashlib.sha256(prefix + ordinal.to_bytes(4, "big")).digest()[:8],
            "big",
        )
        for ordinal in range(256)
    )
    if len(set(values)) != 256:
        raise ValidationError("independently reconstructed seed registry collides")
    return hashlib.sha256(
        b"".join(value.to_bytes(8, "big") for value in values)
    ).hexdigest()


def expected_field_values() -> Mapping[str, Any]:
    return {
        "F001": "NOT_APPLICABLE_C17_RETIRED_NO_THEOREM_CLAIM",
        "F002": "NOT_APPLICABLE_NO_C17_ASSUMPTION_SET_IN_SELECTED_ROUTE",
        "F003": {"path": C17_PATH, "role": "NO_PROOF_CLAIMED"},
        "F004": {"path": C17_PATH, "role": "NO_C17_CODE_MAPPING_ASSERTED"},
        "F005": "NOT_APPLICABLE_NO_SUCH_CONTROL_CLAIMED",
        "F006": "NOT_APPLICABLE_NO_C17_IDENTIFIABILITY_CLAIM",
        "F109": 64,
        "F110": _fraction_record(1, 100),
        "F111": EXPECTED_REAL_REAL_FLOOR_ID,
        "F112": EXPECTED_CONFIDENCE_METHOD_ID,
        "F114": "UPPER_BOUND_ON_CERTIFIED_MAXIMUM_ABSOLUTE_ERROR",
        "F115": _fraction_record(1, 20),
        "F116": "ZERO_VIOLATIONS_REQUIRED",
        "F117": 0,
        "F118": "UPPER_BOUND_ON_GUIDE_MINUS_DIRECT_ERROR",
        "F119": _fraction_record(0),
        "F121": {"scalar": "NATURAL_GROUP_WEIGHTED_TARGET_FIRST_INITIALIZER_KL", "threshold_nat": _fraction_record(1, 100)},
        "F123": {"scalar": "NATURAL_GROUP_WEIGHTED_ASSOCIATION_TOTAL_VARIATION", "threshold": _fraction_record(1, 100)},
        "F124": _fraction_record(1, 20),
        "F125": {"ratio": "GUIDE_OVER_MATCHED_DIRECT_LATENCY", "upper": _fraction_record(2)},
        "F126": {"ratio": "GUIDE_OVER_MATCHED_DIRECT_PEAK_MEMORY", "upper": _fraction_record(2)},
        "F127": {"ratio": "GUIDE_OVER_MATCHED_DIRECT_F104_TOTAL_COMPUTE", "upper": _fraction_record(1)},
        "F149": _fraction_record(1, 20),
        "F130": _fraction_record(1),
        "F131": EXPECTED_PILOT_VARIANCE_SOURCE,
        "F132": 256,
        "F133": {
            "algorithm": "SHA256_PREFIX_PLUS_UINT32_BE_ORDINAL_TAKE_FIRST_UINT64_BE",
            "count": 256,
            "registry_sha256": EXPECTED_SEED_REGISTRY_SHA256,
            "entropy_consumed": False,
            "independence_claimed_by_registry_alone": False,
        },
        "F134": {"R3-PHYS": 128, "R4-RETAIL": 128},
        "F135": 1,
        "F136": 64,
        "F138": {"count": 0, "reason": "ANALYTIC_F112_NO_BOOTSTRAP_INFERENCE"},
    }


def expected_r64_adapter_contract() -> Mapping[str, Any]:
    return {
        "address_fields": [
            "domain_id",
            "seed_id",
            "group_id",
            "case_id",
            "draw_id",
            "conditioning_id",
        ],
        "draws_per_method": 64,
        "method_neutral_direct_guide_rosters_must_equal": True,
        "unique_addresses_within_one_case_required": True,
        "all_other_draw_counts_refuse": True,
        "caller_roster_consistency_checked": True,
        "configuration_provenance_proved": False,
        "independent_stream_law_proved": False,
    }


def expected_b05_decision_contract() -> Mapping[str, Any]:
    return {
        "certification_scope_id": EXPECTED_B05_CERTIFICATION_SCOPE_ID,
        "value_specs": [
            {
                "metric_id": metric_id,
                "unit_id": unit_id,
                "bound_kind": bound_kind,
            }
            for metric_id, unit_id, bound_kind in EXPECTED_B05_VALUE_SPECS
        ],
        "terminal_statuses": list(EXPECTED_B05_TERMINAL_STATUSES),
        "failure_counts_caller_supplied": False,
        "every_noncomplete_status_counts_as_failure": True,
        "resource_ratio_endpoint_rule": "GUIDE_UPPER_OVER_MATCHED_DIRECT_POSITIVE_LOWER",
        "roster_attempt_receipt_cross_binding_required": True,
        "receipt_authentication_performed": False,
        "project_gate_pass_returned": False,
        "positive_flag_semantics": "FROZEN_INEQUALITIES_ONLY_NOT_PROJECT_PASS",
    }


def expected_joint_b04_dependency() -> Mapping[str, Any]:
    return {
        "accepted_f105_integration_state": "F105_MANUSCRIPT_DISPLAY_AND_PRODUCTION_EVALUATOR_INTEGRATED_PREOUTCOME",
        "integration_machine_path": F105_INTEGRATION_MACHINE_PATH,
        "integration_machine_raw_sha256": EXPECTED_F105_INTEGRATION_MACHINE_RAW_SHA256,
        "integration_machine_semantic_sha256": EXPECTED_F105_INTEGRATION_SEMANTIC_SHA256,
        "integration_review_path": F105_INTEGRATION_REVIEW_PATH,
        "integration_review_raw_sha256": EXPECTED_F105_INTEGRATION_REVIEW_SHA256,
        "integration_review_disposition": "GO_P0_P1_P2_ZERO",
        "general_engine_draw_domain": {"minimum": 2, "maximum": 128},
        "confirmatory_adapter_draw_count": 64,
        "dependency_direction": "ACCEPTED_F105_PREDECESSOR_THEN_ADDITIVE_R64_SUCCESSOR",
    }


def _strict_equal(actual: object, expected: object, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if set(actual) != set(expected):
            raise ValidationError(label + " key mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + str(key))
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for ordinal, (left, right) in enumerate(zip(actual, expected)):
            _strict_equal(left, right, label + "[" + str(ordinal) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def validate(*, root: Path = ROOT) -> Mapping[str, Any]:
    machine_raw = stable_read(MACHINE_PATH, root=root)
    record = _load_record(machine_raw)
    expected_record_keys = {
        "authority",
        "b05_decision_contract",
        "bindings",
        "blocker_effects",
        "count_transition",
        "field_closures",
        "global_state",
        "joint_b04_dependency",
        "nonclaims",
        "power_certificate",
        "publication_boundary",
        "r64_adapter_contract",
        "record_sha256",
        "schema_version",
        "state",
    }
    if set(record) != expected_record_keys:
        raise ValidationError("machine top-level key roster mismatch")
    if record.get("state") != "THEORY_STATISTICS_31_FIELD_PREOUTCOME_CLOSURE_FROZEN":
        raise ValidationError("state mismatch")
    expected_authority = {
        "normalized_visible_text": "Alright sounds good. Go ahead and finish all 12 blockers and the broader manuscript-display/production-integration task",
        "utf8_bytes": 119,
        "sha256": "814eb0672097f91e20ae942e29ee9c4481200bd115981f17c1bc292a90b20b3c",
        "raw_transport_bound": False,
        "account_identity_authenticated": False,
        "scientific_execution_authorized": False,
        "entropy_consumed": False,
    }
    _strict_equal(record.get("authority"), expected_authority, "authority")
    raws = _verify_bindings(record, root=root)
    if hashlib.sha256(raws[SOURCE_PATH]).hexdigest() != EXPECTED_SOURCE_SHA256:
        raise ValidationError("source differs from the validator-frozen receipt")
    if hashlib.sha256(raws[R64_ADAPTER_PATH]).hexdigest() != EXPECTED_R64_ADAPTER_SHA256:
        raise ValidationError("R64 adapter differs from the validator-frozen receipt")
    _verify_f105_joint_dependency(raws)
    _verify_source_ast(raws[SOURCE_PATH])
    _verify_r64_adapter_ast(raws[R64_ADAPTER_PATH])

    closures = record.get("field_closures")
    if type(closures) is not list or tuple(row.get("field_id") for row in closures) != EXPECTED_FIELD_IDS:
        raise ValidationError("field closure roster mismatch")
    for ordinal, row in enumerate(closures):
        if type(row) is not dict or set(row) != {
            "field_id",
            "json_pointer",
            "status",
            "value",
        }:
            raise ValidationError("field closure schema mismatch")
        if row["json_pointer"] != EXPECTED_FIELD_POINTERS[ordinal]:
            raise ValidationError("field closure pointer mismatch")
        if row["status"] != "CLOSED_BY_ADDITIVE_PREOUTCOME_THEORY_STATISTICS_FREEZE":
            raise ValidationError("field closure status mismatch")
    values = {row["field_id"]: row.get("value") for row in closures}
    _strict_equal(values, dict(expected_field_values()), "field values")
    if len(values) != 31:
        raise ValidationError("field count mismatch")
    if recompute_seed_registry_sha256() != EXPECTED_SEED_REGISTRY_SHA256:
        raise ValidationError("independent seed-registry digest mismatch")
    _strict_equal(
        record.get("r64_adapter_contract"),
        dict(expected_r64_adapter_contract()),
        "R64 adapter contract",
    )
    _strict_equal(
        record.get("b05_decision_contract"),
        dict(expected_b05_decision_contract()),
        "B05 decision contract",
    )
    _strict_equal(
        record.get("joint_b04_dependency"),
        dict(expected_joint_b04_dependency()),
        "joint B04 dependency",
    )

    normalized_wording = " ".join(EXPECTED_C17_WORDING.split())
    source_wording = _literal_source_assignment(
        raws[SOURCE_PATH], "C17_FINAL_PUBLICATION_WORDING"
    )
    if type(source_wording) is not str or " ".join(source_wording.split()) != normalized_wording:
        raise ValidationError("source C17 wording mismatch")
    normalized_c17_document = " ".join(
        raws[C17_PATH].decode("utf-8").replace("> ", "").split()
    )
    if normalized_wording not in normalized_c17_document:
        raise ValidationError("C17 final wording mismatch")
    human = raws[HUMAN_PATH].decode("utf-8")
    for required in ("exactly 31", "122 open / 44 closed", "91 open / 75 closed", "12 open to 8 open"):
        if required not in human:
            raise ValidationError("human count/blocker wording missing")
    successor = raws[STATISTICAL_SUCCESSOR_PATH].decode("utf-8")
    for required in (
        "exactly `R=64`",
        "fixed_r64_cks_statistical_adapter.py",
        "F109--F112 remained open",
        "completes B04",
    ):
        if required not in successor:
            raise ValidationError("statistical successor wording missing")

    expected_counts = {
        "before": {"pre_open": 122, "pre_closed": 44, "post_open": 3, "post_closed": 3, "total_open": 125, "total_closed": 47},
        "after": {"pre_open": 91, "pre_closed": 75, "post_open": 3, "post_closed": 3, "total_open": 94, "total_closed": 78},
        "closed_field_count": 31,
        "theory_statistics_before": {"open": 31, "closed": 23},
        "theory_statistics_after": {"open": 0, "closed": 54},
    }
    _strict_equal(record.get("count_transition"), expected_counts, "count transition")
    expected_blockers = {
        "B01": "CLOSED_BY_FINAL_C17_RETIREMENT_NO_CLAIM_WORDING",
        "B04": "ELIGIBLE_ON_THIS_PACKAGE_ACCEPTANCE_WITH_BOUND_ACCEPTED_F105_INTEGRATION_PREDECESSOR",
        "B05": "CLOSED_BY_EXACT_THRESHOLDS_FAILURE_RULES_AND_TESTED_DECISION_ALGEBRA",
        "B07": "CLOSED_BY_FIXED_DISTRIBUTION_FREE_POWER_AND_SEED_SCHEDULE",
        "before_open": 12,
        "after_open_under_B04_joint_acceptance": 8,
    }
    _strict_equal(record.get("blocker_effects"), expected_blockers, "blocker effects")
    expected_nonclaims = {
        "c17_proved": False,
        "c20_promoted": False,
        "data_accessed": False,
        "entropy_drawn": False,
        "formal_test_closed": False,
        "ledger_or_timetable_edited": False,
        "model_trained": False,
        "resource_capacity_proved": False,
        "result_produced": False,
        "runtime_admitted": False,
        "scientific_execution_performed": False,
        "seed_registry_alone_proves_independence": False,
        "submission_performed": False,
    }
    _strict_equal(record.get("nonclaims"), expected_nonclaims, "nonclaims")
    expected_power = {
        "paired_range": {
            "lower": _fraction_record(-3),
            "upper": _fraction_record(3),
            "width": _fraction_record(6),
        },
        "null_margin": _fraction_record(1, 100),
        "planning_alternative": _fraction_record(1),
        "alpha_per_domain": _fraction_record(1, 40),
        "beta_per_domain": _fraction_record(1, 20),
        "certified_minimum_training_seeds": 246,
        "frozen_training_seeds": 256,
        "target_joint_power": _fraction_record(9, 10),
        "joint_power_route": "UNION_BOUND_NO_DOMAIN_INDEPENDENCE_ASSUMED",
    }
    _strict_equal(record.get("power_certificate"), expected_power, "power certificate")
    expected_publication = {
        "c17_final_wording_path": C17_PATH,
        "fresh_anonymity_and_claim_audit_required": True,
        "internal_package_publication_safe_as_is": False,
    }
    _strict_equal(
        record.get("publication_boundary"),
        expected_publication,
        "publication boundary",
    )
    if record.get("global_state") != "DRAFT_NOT_EXECUTABLE":
        raise ValidationError("global state mismatch")
    return {
        "validation": "PASS",
        "record_sha256": record["record_sha256"],
        "field_closure_count": 31,
        "certified_minimum_training_seeds": 246,
        "frozen_training_seeds": 256,
        "seed_registry_sha256": EXPECTED_SEED_REGISTRY_SHA256,
        "blockers_eligible_on_independent_acceptance": 4,
        "accepted_f105_joint_dependency": True,
        "scientific_execution": False,
    }


def main() -> int:
    try:
        result = validate()
    except Exception as error:
        print(json.dumps({"validation": "FAIL", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
