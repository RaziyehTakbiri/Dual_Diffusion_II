"""Read-only validator and synthetic comparator for the F122 freeze."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

SCHEMA = "heterodiff-manuscript-v3-f122-association-error-direction-freeze-v1"
PREDICATE = "F122_ASSOCIATION_APPROXIMATION_ERROR_DIRECTION_UPPER_BOUND_FROZEN_PREOUTCOME"
FIELD_ID = "F122"
POINTER = "/metric_and_estimand_plan/constraint_metrics/4/direction"
METRIC_INDEX = 4
METRIC_ID = "association-approximation-error"
DIRECTION = "UPPER_BOUND"
REFUSAL = "F122_DIRECTION_REFUSAL_NO_GATE_DECISION"
VALIDATOR_RAW_AUTHENTICITY_BOUNDARY = "INDEPENDENT_REVIEW_BOUND_NOT_SELF_AUTHENTICATING"
MACHINE_PATH = "research/fixtures/manuscript_v3_f122_association_error_direction_freeze_v1.json"
HUMAN_PATH = "PROJECT_F122_ASSOCIATION_ERROR_DIRECTION_FREEZE.md"
VALIDATOR_PATH = "research/diagnostics/manuscript_v3_f122_association_error_direction_freeze_v1.py"
TEST_PATH = "tests/unit/test_manuscript_v3_f122_association_error_direction_freeze_v1.py"
PACKAGE_ROSTER = [HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH]
ROOT = Path(__file__).resolve().parents[2]

TOP_KEYS = [
    "certifications", "certified_upper_endpoint", "direction", "f123_threshold",
    "f123_threshold_record_sha256", "metric_id", "metric_index",
    "scalar_definition_sha256",
]
CERT_KEYS = [
    "f123_threshold_final_and_frozen", "same_scalar_and_units",
    "scalar_definition_final_and_frozen", "upper_endpoint_certified",
]
RATIONAL_KEYS = ["denominator", "numerator"]
RESULT_KEYS = [
    "decision", "direction", "equality_passes", "metric_id", "metric_index",
    "production_inputs_authenticated",
]

FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp", "boto3", "httpx", "numpy", "pandas", "requests", "scipy",
    "secrets", "socket", "subprocess", "torch", "urllib",
}
FORBIDDEN_CALLS = {
    "compile", "eval", "exec", "input", "open", "breakpoint",
    "os.system", "os.popen", "os.spawnl", "os.spawnlp", "os.spawnv",
    "os.spawnvp", "os.remove", "os.rename", "os.replace", "os.unlink",
    "Path.write_bytes", "Path.write_text", "random.random", "random.seed", "secrets.token_bytes",
    "subprocess.call", "subprocess.Popen", "subprocess.run",
    "time.time", "time.monotonic", "urllib.request.urlopen",
}

EXPECTED_PREDECESSORS = [
    ("PROJECT_ANTI_DRIFT_OPERATING_POLICY.md", 2240, "22f1006bfd0b4dde8eb51e6e30abd7b153882a3fd41d6f3a3494ffd98a98bbd3", None),
    ("manuscript_v3/execution_preregistration.md", 22491, "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e", None),
    ("research/fixtures/manuscript_v3_execution_preregistration_v1.json", 39771, "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706", None),
    ("manuscript_v3/execution_preregistration_preexecution_closure_v2.md", 14938, "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d", None),
    ("research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json", 24571, "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db", "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4"),
    ("src/heterodiff/evaluation/mixed_marked_ctmc_ou_known_law_certified_reference.py", 124895, "98ffb1f42bee3efc097f378cc55a00b88f2d8570b9f3e8de1fe5f9a727f2e268", None),
    ("PROJECT_GATE_A_B05_KNOWN_LAW_DESIGN_FREEZE.md", 13766, "ad03491578ba81c597906495f5aec5ceb36508cb9c0736f5f33af6d9babbc05d", None),
    ("research/fixtures/manuscript_v3_gate_a_b05_known_law_design_freeze_v1.json", 269205, "c49ef829cab9c8a7459216d37cb70382d4c0027e20aa3c343c5fbd0ed825ee32", "d81b52f94fe420b50f3aa5bf5d0edc97c5b55bdedf19c5bb9a8b499a23397e8b"),
    ("research/diagnostics/manuscript_v3_gate_a_b05_known_law_design_freeze_v1.py", 33523, "d53a5656e4322e5b169bd859af531ea208ccaf413ddd9660a31c350d93cc2eb2", None),
    ("tests/unit/test_manuscript_v3_gate_a_b05_known_law_design_freeze_v1.py", 18517, "052190e27ea71f06b1f93ba8df647867d813447464870c6e0f78c75f61b8524a", None),
    ("PROJECT_F120_INITIALIZER_ERROR_DIRECTION_FREEZE.md", 7259, "dc41516bc22ab5d8b908bf9935216c0aade1df0ddcb31d484f8104b53e759589", None),
    ("research/fixtures/manuscript_v3_f120_initializer_error_direction_freeze_v1.json", 11986, "d246c46f006e87a512985d67b8a446ccdc3cf1ab06f0ceb28990ae2e0e977808", "c3d018a4bfc8eab4eaa80285edca8f87d1b6e980a09dd3b10abe126b6fbf1ad3"),
    ("research/diagnostics/manuscript_v3_f120_initializer_error_direction_freeze_v1.py", 33065, "74d141b6f871cffbe57dffbd29a4f900d64b8301f3ef1cc86136b420c338ec8f", None),
    ("tests/unit/test_manuscript_v3_f120_initializer_error_direction_freeze_v1.py", 17983, "72f91a3f6d1fa9e423449f87283086cf33408a4bfb61c207c0badb0c9e4128dd", None),
    ("PROJECT_F120_INITIALIZER_ERROR_DIRECTION_FREEZE_INDEPENDENT_REVIEW_V2.md", 9584, "6c98574385da17411ab01a28f94036505d9870462036cbfb9798b67c680187ef", None),
]
EXPECTED_PREDECESSOR_META = [
    ("ANTI_DRIFT_POLICY", "policy"),
    ("EXECUTION_PREREGISTRATION_V1", "human"),
    ("EXECUTION_PREREGISTRATION_V1", "machine"),
    ("PREEXECUTION_CLOSURE_V2", "human"),
    ("PREEXECUTION_CLOSURE_V2", "machine"),
    ("B05_KNOWN_LAW_ORIENTATION", "certified_reference_source"),
    ("B05_KNOWN_LAW_ORIENTATION", "human"),
    ("B05_KNOWN_LAW_ORIENTATION", "machine"),
    ("B05_KNOWN_LAW_ORIENTATION", "validator"),
    ("B05_KNOWN_LAW_ORIENTATION", "test"),
    ("ACCEPTED_F120_BASELINE", "human"),
    ("ACCEPTED_F120_BASELINE", "machine"),
    ("ACCEPTED_F120_BASELINE", "validator"),
    ("ACCEPTED_F120_BASELINE", "test"),
    ("ACCEPTED_F120_BASELINE", "independent_review_v2"),
]

# Human and hostile-test bytes are installed only after those two files stop.
# The validator binding is derived from the stable-open validator descriptor;
# this avoids an impossible raw-hash self-reference and matches accepted F120 V2.
EXPECTED_HUMAN_BYTES = 7664
EXPECTED_HUMAN_SHA256 = "7198ac7069f558add5862230dc4371037c57b6aa1054c8386ec9a13fff9d434c"
EXPECTED_TEST_BYTES = 18680
EXPECTED_TEST_SHA256 = "0ca79d214f0d2418e08bca87d1600913d8896d683410d1b520f4f54d12548e6f"


class F122Refusal(ValueError):
    """Fail-closed refusal with no gate decision."""

    def __init__(self, reason_code: str):
        super().__init__(f"{REFUSAL}:{reason_code}")
        self.disposition = REFUSAL
        self.reason_code = reason_code
        self.gate_decision_produced = False


def _exact_keys(value: Any, expected: list[str], reason: str) -> Mapping[str, Any]:
    if type(value) is not dict or list(value) != expected:
        raise F122Refusal(reason)
    return value


def _sha256_shape(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _rational(value: Any) -> tuple[int, int]:
    value = _exact_keys(value, RATIONAL_KEYS, "RATIONAL_SCHEMA_NONCANONICAL")
    d, n = value["denominator"], value["numerator"]
    if type(d) is not int or type(n) is not int or d <= 0 or n < 0:
        raise F122Refusal("RATIONAL_VALUE_NONCANONICAL")
    if math.gcd(n, d) != 1:
        raise F122Refusal("RATIONAL_NOT_LOWEST_TERMS")
    return n, d


def evaluate_association_error_gate(payload: Any) -> dict[str, Any]:
    """Apply only the frozen direction to synthetic, caller-certified inputs."""
    payload = _exact_keys(payload, TOP_KEYS, "INPUT_SCHEMA_NONCANONICAL")
    if type(payload["metric_index"]) is not int or payload["metric_index"] != METRIC_INDEX:
        raise F122Refusal("METRIC_INDEX_NONCANONICAL")
    if type(payload["metric_id"]) is not str or payload["metric_id"] != METRIC_ID:
        raise F122Refusal("METRIC_ID_NONCANONICAL")
    if type(payload["direction"]) is not str or payload["direction"] != DIRECTION:
        raise F122Refusal("DIRECTION_NONCANONICAL")
    for name in ("scalar_definition_sha256", "f123_threshold_record_sha256"):
        if not _sha256_shape(payload[name]):
            raise F122Refusal("DIGEST_NONCANONICAL")
    certs = _exact_keys(payload["certifications"], CERT_KEYS, "CERTIFICATION_SCHEMA_NONCANONICAL")
    for name in CERT_KEYS:
        if type(certs[name]) is not bool or certs[name] is not True:
            raise F122Refusal("REQUIRED_CERTIFICATION_ABSENT")
    upper_n, upper_d = _rational(payload["certified_upper_endpoint"])
    threshold_n, threshold_d = _rational(payload["f123_threshold"])
    decision = "PASS" if upper_n * threshold_d <= threshold_n * upper_d else "FAIL"
    return {
        "decision": decision,
        "direction": DIRECTION,
        "equality_passes": True,
        "metric_id": METRIC_ID,
        "metric_index": METRIC_INDEX,
        "production_inputs_authenticated": False,
    }


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("ascii")


def semantic_digest(record: Mapping[str, Any]) -> str:
    candidate = dict(record)
    candidate.pop("record_sha256", None)
    schema = record.get("schema_version")
    if type(schema) is not str:
        raise ValueError("semantic record requires exact schema_version")
    return hashlib.sha256((schema + "\0").encode("ascii") + canonical_json(candidate)[:-1]).hexdigest()


def _fingerprint(s: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns,
            s.st_mode, s.st_nlink)


def _validate_leaf_status(value: os.stat_result, label: str) -> None:
    if not stat.S_ISREG(value.st_mode):
        raise ValueError(label + " must be a regular file")
    if stat.S_IMODE(value.st_mode) != 0o644:
        raise ValueError(label + " mode must be exactly 0644")
    if value.st_nlink != 1:
        raise ValueError(label + " must have exactly one hard link")


def stable_read(root: Path, relative: str) -> bytes:
    """Componentwise no-follow stable read with exact regular-file custody."""
    if not isinstance(root, Path) or not root.is_absolute():
        raise ValueError("workspace root must be an absolute Path")
    if type(relative) is not str:
        raise ValueError("path must be exact built-in string")
    posix = PurePosixPath(relative)
    if posix.is_absolute() or str(posix) != relative or not posix.parts or any(p in ("", ".", "..") for p in posix.parts):
        raise ValueError("unsafe relative path")
    opened: list[int] = []
    namespace_rows: list[tuple[int, str, tuple[int, ...]]] = []
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    cloexec = getattr(os, "O_CLOEXEC", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    root_before = root.lstat()
    try:
        root_fd = os.open(str(root), os.O_RDONLY | directory | nofollow | cloexec)
        opened.append(root_fd)
        root_open = os.fstat(root_fd)
        if stat.S_ISLNK(root_before.st_mode) or not stat.S_ISDIR(root_before.st_mode) or _fingerprint(root_before) != _fingerprint(root_open):
            raise ValueError("workspace root identity mismatch")
        dir_fd = root_fd
        for component in posix.parts[:-1]:
            entry_before = os.stat(component, dir_fd=dir_fd, follow_symlinks=False)
            fd = os.open(component, os.O_RDONLY | directory | nofollow | cloexec, dir_fd=dir_fd)
            opened.append(fd)
            opened_status = os.fstat(fd)
            if stat.S_ISLNK(entry_before.st_mode) or not stat.S_ISDIR(entry_before.st_mode) or _fingerprint(entry_before) != _fingerprint(opened_status):
                raise ValueError("unsafe or changed path component")
            namespace_rows.append((dir_fd, component, _fingerprint(entry_before)))
            dir_fd = fd
        leaf = posix.parts[-1]
        before_path = os.stat(leaf, dir_fd=dir_fd, follow_symlinks=False)
        _validate_leaf_status(before_path, "before-path binding")
        fd = os.open(leaf, os.O_RDONLY | nofollow | cloexec, dir_fd=dir_fd)
        opened.append(fd)
        before_fd = os.fstat(fd)
        _validate_leaf_status(before_fd, "before-descriptor binding")
        if stat.S_ISLNK(before_path.st_mode) or _fingerprint(before_path) != _fingerprint(before_fd):
            raise ValueError("binding must be a stable regular file")
        namespace_rows.append((dir_fd, leaf, _fingerprint(before_path)))
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(fd)
        _validate_leaf_status(after_fd, "after-descriptor binding")
        if _fingerprint(before_fd) != _fingerprint(after_fd):
            raise ValueError("binding changed during descriptor read")
        for parent_fd, component, expected in namespace_rows:
            current = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            if parent_fd == dir_fd and component == leaf:
                _validate_leaf_status(current, "after-path binding")
            if _fingerprint(current) != expected:
                raise ValueError("binding namespace changed during read")
        root_after = root.lstat()
        if _fingerprint(root_before) != _fingerprint(root_after):
            raise ValueError("workspace root changed during read")
        raw = b"".join(chunks)
        if len(raw) != before_fd.st_size:
            raise ValueError("short binding read")
        return raw
    except OSError as error:
        raise ValueError("stable no-follow read failed: " + relative) from error
    finally:
        for fd in reversed(opened):
            os.close(fd)


def _binding_map(record: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    bindings = record.get("predecessor_bindings")
    if type(bindings) is not list or len(bindings) != 15:
        raise ValueError("exact 15-file predecessor roster required")
    paths = [b.get("path") for b in bindings if type(b) is dict]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate predecessor path")
    expected_paths = [row[0] for row in EXPECTED_PREDECESSORS]
    if paths != expected_paths:
        raise ValueError("predecessor roster differs from fixed expected roster")
    for ordinal, (binding, (path, size, raw_sha, semantic_sha), (group, role)) in enumerate(zip(bindings, EXPECTED_PREDECESSORS, EXPECTED_PREDECESSOR_META)):
        if binding.get("path") != path or binding.get("bytes") != size or binding.get("raw_sha256") != raw_sha:
            raise ValueError("predecessor receipt differs from fixed expected receipt")
        if binding.get("ordinal") != ordinal or binding.get("group") != group or binding.get("role") != role:
            raise ValueError("predecessor group/ordinal/role metadata drift")
        if binding.get("mode_octal") != "0644" or binding.get("nlink") != 1 or binding.get("terminal_lf") is not True:
            raise ValueError("predecessor custody metadata drift")
        if semantic_sha is not None and binding.get("record_sha256") != semantic_sha:
            raise ValueError("predecessor semantic receipt differs from fixed expected receipt")
        if semantic_sha is None and "record_sha256" in binding:
            raise ValueError("unexpected predecessor semantic receipt")
    return {b["path"]: b for b in bindings}


def _verify_binding(root: Path, binding: Mapping[str, Any]) -> bytes:
    raw = stable_read(root, binding["path"])
    if len(raw) != binding["bytes"] or hashlib.sha256(raw).hexdigest() != binding["raw_sha256"]:
        raise ValueError(f"predecessor receipt mismatch: {binding['path']}")
    if binding.get("mode_octal") != "0644" or binding.get("nlink") != 1:
        raise ValueError("binding custody declaration mismatch")
    if binding.get("terminal_lf") is not raw.endswith(b"\n"):
        raise ValueError("terminal LF mismatch")
    if "record_sha256" in binding:
        parsed = json.loads(raw)
        if parsed.get("record_sha256") != binding["record_sha256"] or semantic_digest(parsed) != binding["record_sha256"]:
            raise ValueError("predecessor semantic digest mismatch")
    return raw


def _validate_source_effect_surface(raw: bytes) -> None:
    tree = ast.parse(raw.decode("utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots = {a.name.split(".")[0] for a in node.names}
            if roots & FORBIDDEN_IMPORT_ROOTS:
                raise ValueError("forbidden import")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in FORBIDDEN_IMPORT_ROOTS:
                raise ValueError("forbidden import")
        elif isinstance(node, ast.Call):
            target = node.func
            parts: list[str] = []
            while isinstance(target, ast.Attribute):
                parts.append(target.attr)
                target = target.value
            if isinstance(target, ast.Name):
                parts.append(target.id)
            name = ".".join(reversed(parts))
            if name in FORBIDDEN_CALLS:
                raise ValueError(f"forbidden effect call: {name}")


def _fixed_package_binding(root: Path, ordinal: int, role: str, path: str,
                           expected_bytes: int | None = None,
                           expected_sha256: str | None = None) -> dict[str, Any]:
    raw = stable_read(root, path)
    raw_sha = hashlib.sha256(raw).hexdigest()
    if expected_bytes is not None and (len(raw) != expected_bytes or raw_sha != expected_sha256):
        raise ValueError("fixed current-package binding drift: " + path)
    return {"bytes": len(raw), "group": "CURRENT_PACKAGE", "mode_octal": "0644",
            "nlink": 1, "ordinal": ordinal, "path": path, "raw_sha256": raw_sha,
            "role": role, "terminal_lf": raw.endswith(b"\n")}


def _expected_predecessor_bindings(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ordinal, ((path, size, raw_sha, semantic_sha), (group, role)) in enumerate(zip(EXPECTED_PREDECESSORS, EXPECTED_PREDECESSOR_META)):
        raw = stable_read(root, path)
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != raw_sha:
            raise ValueError("fixed predecessor drift: " + path)
        row = {"bytes": size, "group": group, "mode_octal": "0644", "nlink": 1,
               "ordinal": ordinal, "path": path, "raw_sha256": raw_sha,
               "role": role, "terminal_lf": True}
        if semantic_sha is not None:
            parsed = json.loads(raw)
            if parsed.get("record_sha256") != semantic_sha or semantic_digest(parsed) != semantic_sha:
                raise ValueError("fixed predecessor semantic drift: " + path)
            row["record_sha256"] = semantic_sha
        rows.append(row)
    return rows


def expected_record(root: Path = ROOT) -> dict[str, Any]:
    """Reconstruct every canonical machine field from fixed source authority."""
    package_bindings = [
        _fixed_package_binding(root, 0, "human", HUMAN_PATH, EXPECTED_HUMAN_BYTES, EXPECTED_HUMAN_SHA256),
        _fixed_package_binding(root, 1, "validator", VALIDATOR_PATH),
        _fixed_package_binding(root, 2, "test", TEST_PATH, EXPECTED_TEST_BYTES, EXPECTED_TEST_SHA256),
    ]
    predecessor_bindings = _expected_predecessor_bindings(root)
    record: dict[str, Any] = {
        "authority_provenance": {
            "network_contact_data_runtime_entropy_or_science_authorized": False,
            "offline_local_package_construction_authorized": True,
            "tracker_ledger_predecessor_or_receipt_edit_authorized": False,
        },
        "control_predicate": PREDICATE,
        "count_transition": {
            "after": {"post_execution_closed": 3, "post_execution_open": 3, "pre_execution_closed": 26, "pre_execution_open": 140, "total_closed": 29, "total_open": 143},
            "before": {"post_execution_closed": 3, "post_execution_open": 3, "pre_execution_closed": 25, "pre_execution_open": 141, "total_closed": 28, "total_open": 144},
            "delta": {"closed": 1, "closed_fields": ["F122"], "open": -1},
        },
        "direction_contract": {
            "certification_keys": list(CERT_KEYS),
            "comparator": "CERTIFIED_UPPER_ENDPOINT_LE_SEPARATELY_FROZEN_F123_THRESHOLD",
            "equality_passes": True,
            "exact_value": DIRECTION,
            "f123_threshold_selected_here": False,
            "association_error_scalar_selected_here": False,
            "input_key_order": list(TOP_KEYS),
            "kl_or_tv_selected_here": False,
            "metric_id": METRIC_ID,
            "metric_index": METRIC_INDEX,
            "production_inputs_authenticated_by_helper": False,
            "production_numeric_representation_selected_here": False,
            "qualification_rational_encoding_only": {"denominator_positive": True, "exact_builtin_integers": True, "lowest_terms": True, "nonnegative": True, "production_representation_selected": False},
            "rational_key_order": list(RATIONAL_KEYS),
            "refusal_disposition": REFUSAL,
            "unknown_missing_extra_reordered_or_noncanonical_input_refuses": True,
        },
        "field_closures": [{"field_id": FIELD_ID, "json_pointer": POINTER,
                            "owner_role": "OWNER_A_THEORY_AND_STATISTICS", "value": DIRECTION}],
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "machine_self_binding": {"path": MACHINE_PATH, "raw_self_hash_embedded": False,
                                 "semantic_self_digest_field": "record_sha256"},
        "package_bindings_excluding_machine_self": package_bindings,
        "package_file_roster": list(PACKAGE_ROSTER),
        "package_kind": "ADDITIVE_PREOUTCOME_EXACT_F122_FIELD_CLOSURE",
        "predecessor_bindings": predecessor_bindings,
        "predecessor_path_roster": [row[0] for row in EXPECTED_PREDECESSORS],
        "predecessor_semantic_receipt": {
            "anti_drift_direct_named_field_rule_bound": True,
            "b05_known_law_orientation_evidence_only_no_F016_or_real_domain_threshold_reuse": True,
            "b05_certificate_sha256": "e202379f735e76dc43105cff62e4ff443a97ff810d89edecaf8091e5eefe187d",
            "b05_grid_sha256": "f3cdaafcd931dc41b37bf51666ff262c5d8eff25439b27f208ef2680e1464c8e",
            "b05_reference_table_sha256": "1b6cfa0d42a8e9271af4e78cbdf5f81843dcf3df3507687754b373fa49a2d314",
            "base_constraint_metric_count": 9,
            "base_index4_exact": {"direction": None, "metric_id": METRIC_ID, "threshold_or_margin": None},
            "f120_after_pre_141_25_post_3_3_total_144_28": True,
            "f120_independent_review_v2_go_and_only_F120_closed": True,
        },
        "project_effects_and_nonclaims": {
            "B05_remains_open": True,
            "F114_F119_remain_open": True,
            "F120_prior_closure_preserved": True,
            "F123_F127_remain_open": True,
            "F149_remains_open": True,
            "all_12_blockers_remain_open": True,
            "formal_tests_remain_open_or_pending": True,
            "formal_test_28_status": "OPEN",
            "formal_test_29_status": "OPEN",
            "formal_test_30_status": "PENDING",
            "formal_tests_closed": 0,
            "association_error_formula_units_aggregation_or_normalization_selected": False,
            "interval_confidence_or_multiplicity_procedure_selected": False,
            "only_fields_closed": [FIELD_ID],
            "F121_status": "OPEN_HOLD",
            "result_claim_or_submission_promoted": False,
            "results_filled": 0,
            "runtime_data_or_science_performed": False,
            "tracker_or_ledger_edited": False,
            "validator_raw_authenticity_boundary": VALIDATOR_RAW_AUTHENTICITY_BOUNDARY,
            "validator_raw_self_authenticated_by_package": False,
            "second_consecutive_B05_artifact": True,
            "third_consecutive_B05_artifact_requires_explicit_scope_review": True,
        },
        "qualification_boundary": {
            "canonical_duplicate_free_ascii_json_required": True,
            "hostile_mutations_use_disposable_replicas_only": True,
            "independent_review_required_before_registration": True,
            "read_only_stable_no_follow_validator": True,
            "self_validation_is_independent_acceptance": False,
            "synthetic_exact_rational_comparator_only": True,
            "second_consecutive_B05_artifact": True,
            "third_consecutive_B05_artifact_requires_explicit_scope_review": True,
            "validator_raw_authenticity": VALIDATOR_RAW_AUTHENTICITY_BOUNDARY,
            "validator_raw_authenticity_becomes_durable_only_in_later_exact_independent_review_receipt": True,
            "validator_raw_self_authenticating": False,
        },
        "reported_date": "2026-09-01",
        "schema_version": SCHEMA,
        "source_effect_surface": {"connector_or_subprocess": False, "data_reader_or_writer": False,
                                  "environment_or_project_science_import": False, "filesystem_writer": False,
                                  "network": False, "rng_or_entropy": False,
                                  "runtime_or_scientific_execution": False},
            "state": PREDICATE,
        "workstream_transition": {
            "after": {"data_governance_reproduction": {"closed": 4, "open": 48}, "final_sealed_freeze": {"closed": 0, "open": 1}, "method_runtime_compute": {"closed": 3, "open": 62}, "theory_statistics": {"closed": 22, "open": 32}},
            "before": {"data_governance_reproduction": {"closed": 4, "open": 48}, "final_sealed_freeze": {"closed": 0, "open": 1}, "method_runtime_compute": {"closed": 3, "open": 62}, "theory_statistics": {"closed": 21, "open": 33}},
        },
    }
    record["record_sha256"] = semantic_digest(record)
    return record


def validate(root: Path = ROOT) -> dict[str, Any]:
    machine_raw = stable_read(root, MACHINE_PATH)
    record = json.loads(machine_raw, object_pairs_hook=lambda pairs: _no_duplicates(pairs))
    if machine_raw != canonical_json(record):
        raise ValueError("machine JSON is not canonical ASCII plus LF")
    expected = expected_record(root)
    if record != expected:
        raise ValueError("machine record differs from full exact reconstructed record")
    if record.get("schema_version") != SCHEMA or record.get("control_predicate") != PREDICATE:
        raise ValueError("identity mismatch")
    if record.get("record_sha256") != semantic_digest(record):
        raise ValueError("machine semantic self-digest mismatch")
    if record.get("package_file_roster") != PACKAGE_ROSTER:
        raise ValueError("package roster mismatch")
    package_bindings = record.get("package_bindings_excluding_machine_self")
    if type(package_bindings) is not list or [x.get("path") for x in package_bindings if type(x) is dict] != [HUMAN_PATH, VALIDATOR_PATH, TEST_PATH]:
        raise ValueError("current-package binding roster mismatch")
    for binding in package_bindings:
        _verify_binding(root, binding)
    closure = record.get("field_closures")
    expected_closure = [{"field_id": FIELD_ID, "json_pointer": POINTER,
                         "owner_role": "OWNER_A_THEORY_AND_STATISTICS", "value": DIRECTION}]
    if closure != expected_closure:
        raise ValueError("sole F122 closure mismatch")
    if record.get("count_transition") != {
        "after": {"post_execution_closed": 3, "post_execution_open": 3,
                  "pre_execution_closed": 26, "pre_execution_open": 140,
                  "total_closed": 29, "total_open": 143},
        "before": {"post_execution_closed": 3, "post_execution_open": 3,
                   "pre_execution_closed": 25, "pre_execution_open": 141,
                   "total_closed": 28, "total_open": 144},
        "delta": {"closed": 1, "closed_fields": ["F122"], "open": -1},
    }:
        raise ValueError("count transition mismatch")
    work = record.get("workstream_transition")
    if work != {
        "after": {"data_governance_reproduction": {"closed": 4, "open": 48},
                  "final_sealed_freeze": {"closed": 0, "open": 1},
                  "method_runtime_compute": {"closed": 3, "open": 62},
                  "theory_statistics": {"closed": 22, "open": 32}},
        "before": {"data_governance_reproduction": {"closed": 4, "open": 48},
                   "final_sealed_freeze": {"closed": 0, "open": 1},
                   "method_runtime_compute": {"closed": 3, "open": 62},
                   "theory_statistics": {"closed": 21, "open": 33}},
    }:
        raise ValueError("workstream transition mismatch")
    policy = record.get("direction_contract")
    if type(policy) is not dict or policy.get("exact_value") != DIRECTION:
        raise ValueError("direction contract mismatch")
    required_policy = {
        "comparator": "CERTIFIED_UPPER_ENDPOINT_LE_SEPARATELY_FROZEN_F123_THRESHOLD",
        "equality_passes": True,
        "f123_threshold_selected_here": False,
        "association_error_scalar_selected_here": False,
        "kl_or_tv_selected_here": False,
        "production_numeric_representation_selected_here": False,
        "refusal_disposition": REFUSAL,
    }
    for key, expected in required_policy.items():
        if policy.get(key) != expected:
            raise ValueError(f"direction contract mismatch: {key}")
    effects = record.get("project_effects_and_nonclaims")
    if type(effects) is not dict or effects.get("only_fields_closed") != ["F122"]:
        raise ValueError("effect surface mismatch")
    for key in (
        "B05_remains_open", "F114_F119_remain_open", "F120_prior_closure_preserved", "F123_F127_remain_open",
        "F149_remains_open", "all_12_blockers_remain_open",
        "formal_tests_remain_open_or_pending", "runtime_data_or_science_performed",
        "result_claim_or_submission_promoted", "tracker_or_ledger_edited",
    ):
        expected = False if key in {"runtime_data_or_science_performed", "result_claim_or_submission_promoted", "tracker_or_ledger_edited"} else True
        if effects.get(key) is not expected:
            raise ValueError(f"nonclosure mismatch: {key}")
    bindings = _binding_map(record)
    expected_paths = record.get("predecessor_path_roster")
    if type(expected_paths) is not list or list(bindings) != expected_paths:
        raise ValueError("predecessor roster/order mismatch")
    raws = {path: _verify_binding(root, binding) for path, binding in bindings.items()}
    base = json.loads(raws["research/fixtures/manuscript_v3_execution_preregistration_v1.json"])
    metrics = base["metric_and_estimand_plan"]["constraint_metrics"]
    if len(metrics) != 9 or metrics[4] != {"metric_id": METRIC_ID, "direction": None, "threshold_or_margin": None}:
        raise ValueError("base metric index/id/null state mismatch")
    f120 = json.loads(raws["research/fixtures/manuscript_v3_f120_initializer_error_direction_freeze_v1.json"])
    if f120.get("record_sha256") != "c3d018a4bfc8eab4eaa80285edca8f87d1b6e980a09dd3b10abe126b6fbf1ad3":
        raise ValueError("F120 semantic baseline mismatch")
    if f120.get("project_effects_and_nonclaims", {}).get("only_fields_closed") != ["F120"]:
        raise ValueError("F120 sole-closure baseline mismatch")
    if f120.get("count_transition", {}).get("after") != {"post_execution_closed": 3, "post_execution_open": 3, "pre_execution_closed": 25, "pre_execution_open": 141, "total_closed": 28, "total_open": 144}:
        raise ValueError("F120 count baseline mismatch")
    b05 = json.loads(raws["research/fixtures/manuscript_v3_gate_a_b05_known_law_design_freeze_v1.json"])
    if "F016" not in b05.get("all_or_nothing_closure", {}).get("closed_field_ids", []):
        raise ValueError("B05 F016 orientation evidence absent")
    if b05.get("project_effects_and_nonclaims", {}).get("B05_remains_open") is not True:
        raise ValueError("B05 nonclosure mismatch")
    if b05.get("known_law_certificate", {}).get("certificate_sha256") != "e202379f735e76dc43105cff62e4ff443a97ff810d89edecaf8091e5eefe187d":
        raise ValueError("B05 certificate semantic mismatch")
    review = raws["PROJECT_F120_INITIALIZER_ERROR_DIRECTION_FREEZE_INDEPENDENT_REVIEW_V2.md"].decode("utf-8")
    if "INDEPENDENT_REVIEW_GO" not in review or not all(f"| P{i} | 0 |" in review for i in range(3)):
        raise ValueError("F120 V2 independent acceptance mismatch")
    _validate_source_effect_surface(stable_read(root, VALIDATOR_PATH))
    sample = {
        "certifications": {k: True for k in CERT_KEYS},
        "certified_upper_endpoint": {"denominator": 2, "numerator": 1},
        "direction": DIRECTION,
        "f123_threshold": {"denominator": 2, "numerator": 1},
        "f123_threshold_record_sha256": "2" * 64,
        "metric_id": METRIC_ID,
        "metric_index": METRIC_INDEX,
        "scalar_definition_sha256": "1" * 64,
    }
    if evaluate_association_error_gate(sample)["decision"] != "PASS":
        raise ValueError("equality qualification failed")
    return {"status": "PASS", "record_sha256": record["record_sha256"],
            "predecessors_verified": len(bindings), "sole_field": FIELD_ID}


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))
