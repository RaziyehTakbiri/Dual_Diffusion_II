"""Read-only validator for the all-or-nothing B05 F007--F018 design freeze.

The validator hard-pins and executes the certified known-law source from the
verified source bytes in memory.  It never imports that source by pathname and
never consults bytecode.  It binds the exact predecessor chain, rebuilds the
frozen reference certificate, and validates only the exact-self reference
candidate.  Ephemeral legacy bytecode presence is deliberately not authority.

This is pre-outcome project-control evidence.  It has no writer, network,
connector, subprocess, entropy, data, training, live-runtime, scientific, or
submission route.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import sys
from types import MappingProxyType, ModuleType
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = "heterodiff-manuscript-v3-gate-a-b05-known-law-design-freeze-v1"
RECORD_DOMAIN = (SCHEMA + "\0").encode("ascii")
STATE = "GATE_A_B05_F007_F018_KNOWN_LAW_DESIGN_FROZEN_PREOUTCOME"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
REPORTED_DATE = "2026-08-31"
PACKAGE_KIND = "ALL_OR_NOTHING_PREOUTCOME_F007_F018_KNOWN_LAW_DESIGN_FREEZE"
CONTROL_PREDICATE = (
    "B05_F007_F018_ALL_OR_NOTHING_KNOWN_LAW_DESIGN_FREEZE_CERTIFIED"
)

SOURCE_PATH = (
    "src/heterodiff/evaluation/"
    "mixed_marked_ctmc_ou_known_law_certified_reference.py"
)
HUMAN_PATH = "PROJECT_GATE_A_B05_KNOWN_LAW_DESIGN_FREEZE.md"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_gate_a_b05_known_law_design_freeze_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "manuscript_v3_gate_a_b05_known_law_design_freeze_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_gate_a_b05_known_law_design_freeze_v1.py"
)
PACKAGE_ROSTER = (SOURCE_PATH, HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH)

SOURCE_SHA256 = "98ffb1f42bee3efc097f378cc55a00b88f2d8570b9f3e8de1fe5f9a727f2e268"
SOURCE_BYTES = 124895
HUMAN_SHA256 = "ad03491578ba81c597906495f5aec5ceb36508cb9c0736f5f33af6d9babbc05d"
HUMAN_BYTES = 13766
SOURCE_SCHEMA = "heterodiff-mixed-marked-ctmc-ou-certified-reference-v1"
SOURCE_STATE = "PREOUTCOME_KNOWN_LAW_DESIGN_REFERENCE_ONLY"
SOURCE_CERTIFICATE_SHA256 = (
    "e202379f735e76dc43105cff62e4ff443a97ff810d89edecaf8091e5eefe187d"
)
REFERENCE_TABLE_SHA256 = (
    "1b6cfa0d42a8e9271af4e78cbdf5f81843dcf3df3507687754b373fa49a2d314"
)
GRID_SHA256 = "f3cdaafcd931dc41b37bf51666ff262c5d8eff25439b27f208ef2680e1464c8e"

AUTHORITY_TEXT = (
    "Okay, sounds good. What I want you to do is to set aside a significant "
    "portion of work to do such that you are busy for around 8 hours, because "
    "I am going to sleep, and dont want my absence to make you idle."
)

CLOSED_BEFORE = (
    "F060", "F106", "F107", "F108", "F113", "F128", "F129", "F148"
)
CLOSED_BY_PACKAGE = tuple("F" + str(index).zfill(3) for index in range(7, 19))
POST_FIELDS = ("F164", "F165", "F168", "F169", "F170", "F171")
PRE_FIELDS = tuple(
    "F" + str(index).zfill(3)
    for index in range(1, 173)
    if "F" + str(index).zfill(3) not in POST_FIELDS
)
CLOSED_AFTER = tuple(sorted(CLOSED_BEFORE + CLOSED_BY_PACKAGE))
OPEN_PRE_AFTER = tuple(field for field in PRE_FIELDS if field not in CLOSED_AFTER)


class ValidationError(ValueError):
    """Raised when custody, schema, or frozen semantics fail closed."""


# group, role, path, bytes, raw SHA-256, optional semantic self-digest
PREDECESSOR_SPECS: Tuple[
    Tuple[str, str, str, int, str, Optional[str]], ...
] = (
    ("A1_PRE_D1_SPEC", "human", "research/62_a1_association_guided_residual_falsification_spec.md", 47468, "475f4f450cb5703e6773c0d0ff242db995a16408acce5989401fa0674326e67c", None),
    ("MANUSCRIPT_V3_METHOD", "human", "manuscript_v3/manuscript_v3.md", 66023, "0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8", None),
    ("EXECUTION_PREREGISTRATION", "human", "manuscript_v3/execution_preregistration.md", 22491, "a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e", None),
    ("EXECUTION_PREREGISTRATION", "machine", "research/fixtures/manuscript_v3_execution_preregistration_v1.json", 39771, "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706", None),
    ("PREEXECUTION_CLOSURE_V2", "human", "manuscript_v3/execution_preregistration_preexecution_closure_v2.md", 14938, "fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d", None),
    ("PREEXECUTION_CLOSURE_V2", "machine", "research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json", 24571, "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db", "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4"),
    ("LEGACY_MIXED_ORACLE", "source", "src/heterodiff/evaluation/mixed_ctmc_ou_known_law_oracle.py", 35409, "b07c406f837e51d02a5608377330f4eed256801305712efc8082741e38822198", None),
    ("LEGACY_MIXED_ORACLE", "test", "tests/unit/test_mixed_ctmc_ou_known_law_oracle.py", 12220, "6592a5a5bb8e081bdc042adb9344e5a20f2c39799db22c6be2e631c302573372", None),
    ("LEGACY_PATH_KL", "source", "src/heterodiff/evaluation/mixed_ctmc_ou_path_kl_diagnostic.py", 31393, "448f50ebde693aa6f7141fcbd91541b781fba4efde92eaf8e0674d8537ca7d7f", None),
    ("LEGACY_PATH_KL", "test", "tests/unit/test_mixed_ctmc_ou_path_kl_diagnostic.py", 16000, "60c9d458f496e458722c29985b69aeb87df5e3df4a0d49489043cad833ac1e48", None),
    ("LEGACY_CAP_DEFECT", "source", "src/heterodiff/evaluation/mixed_ctmc_ou_cap_defect_cancellation_diagnostic.py", 28528, "50b9748a50982f10f289cba94c8ace9adab6ea003e57da091958fda8844f6ef9", None),
    ("LEGACY_CAP_DEFECT", "test", "tests/unit/test_mixed_ctmc_ou_cap_defect_cancellation_diagnostic.py", 10291, "6de986e9b40d57e4f7e4ffdac82ebe04ff4c68ab3287df61c3c8a8ab36cca663", None),
    ("C17_FORK_B_CONTRACT", "human", "manuscript_v3/c17_fork_b_direct_certificate_contract.md", 7109, "80c00dd62106e9fd4743fd6999c1e642f0ef31b063cf9ae3c84822b7a68deae4", None),
    ("C17_HYBRID_PATH_THEOREM", "human", "manuscript_v3/c17_hybrid_path_error_theorem.md", 34923, "d11dc3a98d19a52e7ab653aca1e06598490ad098a450b526870508b4499b9d8d", None),
    ("C17_CAP_CONTRACT", "human", "manuscript_v3/c17_cap_defect_cancellation_contract.md", 5931, "a0a57cdba08c588269c8706ab78bb68ac2360f29b97d20cd05cdcd3a8c93cb3f", None),
    ("ANTI_DRIFT_POLICY", "human", "PROJECT_ANTI_DRIFT_OPERATING_POLICY.md", 2240, "22f1006bfd0b4dde8eb51e6e30abd7b153882a3fd41d6f3a3494ffd98a98bbd3", None),
    ("CONTRIBUTION_REBASELINE", "human", "PROJECT_GATE_A_MINIMUM_CONTRIBUTION_ROUTE_REBASELINE.md", 16295, "9f472caa8f0dc5a38b0ee71f886e5652cadaac1d8970fca2f28e0fd45cc4f036", None),
    ("CONTRIBUTION_REBASELINE", "machine", "research/fixtures/manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.json", 20823, "38c0f11f03fe11d61660823e36404b0c26ff5a3de012400675ba8452c045a9a1", "8ac5d625513e9ccbf6267734eec250270e49a168421564764e73b60acd6b3c40"),
    ("CONTRIBUTION_REBASELINE", "validator", "research/diagnostics/manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.py", 38896, "b9f9828b1122d8e72b4a70a68e6fa137c8e2b3ff21dbfed2d6f3f34e103c5deb", None),
    ("CONTRIBUTION_REBASELINE", "test", "tests/unit/test_manuscript_v3_gate_a_minimum_contribution_route_rebaseline_v1.py", 38991, "9b36a183081d74e92b343eb0efa5f6ce6c60efa3c2a4a154e0e81588c3b45a30", None),
    ("F060_FIELD_FREEZE", "human", "PROJECT_GATE_A_RETAIL_TEMPORAL_RULE_FIELD_FREEZE.md", 10183, "e6125a472bacd83382ccfeb24d2ca9802886da62b79eecbe407dff1b4b168dfc", None),
    ("F060_FIELD_FREEZE", "machine", "research/fixtures/manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.json", 19860, "b7dc23fd0dfee04ffe4834ff1b186ca99dce23f784c4555a245aab0cfb47f068", "b48f21698908f3fb3506866db30f2658c9e050caf32da88e7906b428f86e1c51"),
    ("F060_FIELD_FREEZE", "validator", "research/diagnostics/manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.py", 46174, "b828463a8a78ebe96efda5588a5d288e11b890512e8a8f17913066ca7c965abf", None),
    ("F060_FIELD_FREEZE", "test", "tests/unit/test_manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.py", 31846, "74cda9146983d2276f615a510305d6f837ee398aa7703c80788149a5c46ec2c7", None),
)

ALLOWED_SOURCE_IMPORTS = {
    "__future__", "fractions", "hashlib", "json", "math", "types", "typing"
}
FORBIDDEN_SOURCE_NAMES = {
    "open", "input", "breakpoint", "compile", "eval", "exec", "__import__",
    "system", "popen", "run", "Popen", "urlopen", "socket", "urandom",
    "secrets", "random", "write_text", "write_bytes", "unlink", "rename",
    "replace", "mkdir", "makedirs", "rmdir", "remove", "submit",
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
                raise ValidationError(label + " key is not exact str")
            _require_json_builtins(item, label + "." + key)
        return
    raise ValidationError(label + " contains a forbidden runtime type")


def _canonical_payload_bytes(value: Any) -> bytes:
    _require_json_builtins(value)
    return json.dumps(
        value, ensure_ascii=True, allow_nan=False, sort_keys=True,
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
    return _sha256(
        (schema + "\0").encode("ascii") + _canonical_payload_bytes(payload)
    )


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
    root = root.resolve(strict=True)
    root_status = os.lstat(root)
    if not stat.S_ISDIR(root_status.st_mode) or stat.S_ISLNK(root_status.st_mode):
        raise ValidationError("root custody invalid")
    current = root
    for part in rel.parts[:-1]:
        current = current / part
        status = os.lstat(current)
        if stat.S_ISLNK(status.st_mode) or not stat.S_ISDIR(status.st_mode):
            raise ValidationError("path ancestor custody invalid: " + relative)
    return root.joinpath(*rel.parts)


def _fingerprint(status: os.stat_result) -> Tuple[Any, ...]:
    return (
        status.st_dev, status.st_ino, status.st_size, status.st_mode,
        status.st_nlink, status.st_uid, status.st_gid, status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _stable_read(
    root: Path,
    relative: str,
    expected_bytes: Optional[int] = None,
    expected_sha256: Optional[str] = None,
    terminal_lf: bool = True,
) -> bytes:
    path = _safe_path(root, relative)
    before = os.lstat(path)
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ValidationError(relative + " is not a regular non-symlink file")
    if before.st_nlink != 1 or stat.S_IMODE(before.st_mode) != 0o644:
        raise ValidationError(relative + " custody mode/link count changed")
    with path.open("rb") as handle:
        raw = handle.read()
    after = os.lstat(path)
    if _fingerprint(before) != _fingerprint(after):
        raise ValidationError(relative + " changed while read")
    if expected_bytes is not None and len(raw) != expected_bytes:
        raise ValidationError(relative + " byte count changed")
    if expected_sha256 is not None and _sha256(raw) != expected_sha256:
        raise ValidationError(relative + " raw SHA-256 changed")
    if terminal_lf and (not raw or not raw.endswith(b"\n")):
        raise ValidationError(relative + " lacks terminal LF")
    return raw


def _binding(
    root: Path,
    relative: str,
    expected_bytes: Optional[int] = None,
    expected_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    raw = _stable_read(root, relative, expected_bytes, expected_sha256)
    status = os.lstat(_safe_path(root, relative))
    return {
        "path": relative,
        "bytes": len(raw),
        "sha256": _sha256(raw),
        "mode": "0644",
        "nlink": status.st_nlink,
        "terminal_lf": raw.endswith(b"\n"),
    }


def _predecessor_bindings(root: Path) -> List[Dict[str, Any]]:
    bindings: List[Dict[str, Any]] = []
    for group, role, path, size, digest, self_digest in PREDECESSOR_SPECS:
        raw = _stable_read(root, path, size, digest)
        item: Dict[str, Any] = {
            "group": group,
            "role": role,
            "path": path,
            "bytes": size,
            "sha256": digest,
            "mode": "0644",
            "nlink": 1,
            "terminal_lf": True,
        }
        if self_digest is not None:
            parsed = _parse_json(raw, path)
            if parsed.get("record_sha256") != self_digest:
                raise ValidationError(path + " recorded semantic digest changed")
            if _input_record_sha256(parsed) != self_digest:
                raise ValidationError(path + " semantic self-digest invalid")
            item["semantic_self_digest"] = self_digest
        bindings.append(item)
    return bindings


def _package_bindings(root: Path) -> List[Dict[str, Any]]:
    return [
        _binding(root, SOURCE_PATH, SOURCE_BYTES, SOURCE_SHA256),
        _binding(root, HUMAN_PATH, HUMAN_BYTES, HUMAN_SHA256),
        _binding(root, VALIDATOR_PATH),
        _binding(root, TEST_PATH),
    ]


def _literal_key(node: ast.AST) -> Optional[Tuple[str, Any]]:
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return None
    if type(value) in (str, int, bool, type(None), float):
        return (type(value).__name__, value)
    return None


def _source_ast_safety(raw: bytes) -> ast.Module:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValidationError("certified source must be ASCII") from exc
    tree = ast.parse(text, filename=SOURCE_PATH, mode="exec")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] not in ALLOWED_SOURCE_IMPORTS:
                    raise ValidationError("certified source import is not allowed")
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or node.module is None:
                raise ValidationError("relative source import is forbidden")
            if node.module.split(".", 1)[0] not in ALLOWED_SOURCE_IMPORTS:
                raise ValidationError("certified source import is not allowed")
        elif isinstance(node, ast.Call):
            name: Optional[str] = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name in FORBIDDEN_SOURCE_NAMES:
                raise ValidationError("certified source contains forbidden call " + str(name))
        elif isinstance(node, ast.Dict):
            seen = set()
            for key in node.keys:
                if key is None:
                    continue
                literal = _literal_key(key)
                if literal is not None and literal in seen:
                    raise ValidationError("certified source has a duplicate literal dict key")
                if literal is not None:
                    seen.add(literal)
    return tree


def _load_source_from_verified_bytes(root: Path) -> ModuleType:
    raw = _stable_read(root, SOURCE_PATH, SOURCE_BYTES, SOURCE_SHA256)
    tree = _source_ast_safety(raw)
    code = compile(tree, SOURCE_PATH, "exec", dont_inherit=True, optimize=0)
    module = ModuleType("_hard_pinned_b05_known_law_reference")
    module.__file__ = str(_safe_path(root, SOURCE_PATH))
    module.__package__ = None
    exec(code, module.__dict__)
    return module


def _fraction(text: str) -> Tuple[int, int]:
    if type(text) is not str or "/" not in text:
        raise ValidationError("fraction text invalid")
    numerator_text, denominator_text = text.split("/", 1)
    try:
        numerator = int(numerator_text)
        denominator = int(denominator_text)
    except ValueError as exc:
        raise ValidationError("fraction text invalid") from exc
    if denominator <= 0:
        raise ValidationError("fraction denominator invalid")
    divisor = math.gcd(numerator, denominator)
    if divisor != 1:
        raise ValidationError("fraction is not canonical")
    return numerator, denominator


def _fraction_le(left: str, right: str) -> bool:
    ln, ld = _fraction(left)
    rn, rd = _fraction(right)
    return ln * rd <= rn * ld


def _validate_certificate_semantics(module: ModuleType, certificate: Dict[str, Any]) -> None:
    if certificate.get("schema_version") != SOURCE_SCHEMA:
        raise ValidationError("source certificate schema changed")
    if certificate.get("state") != SOURCE_STATE:
        raise ValidationError("source certificate state changed")
    if certificate.get("certificate_sha256") != SOURCE_CERTIFICATE_SHA256:
        raise ValidationError("source certificate digest changed")
    if certificate.get("reference_table_sha256") != REFERENCE_TABLE_SHA256:
        raise ValidationError("reference table digest changed")
    if certificate.get("grid_sha256") != GRID_SHA256:
        raise ValidationError("grid digest changed")
    fields = certificate.get("field_values")
    if type(fields) is not list:
        raise ValidationError("source field values changed shape")
    if [item.get("field_id") for item in fields] != list(CLOSED_BY_PACKAGE):
        raise ValidationError("source field roster is not exactly F007--F018")
    grid = certificate.get("grid")
    if type(grid) is not dict:
        raise ValidationError("grid changed shape")
    counts = grid.get("table_counts")
    if type(counts) is not dict:
        raise ValidationError("grid counts changed shape")
    if counts.get("path_quadrature_node_cells") != 1025:
        raise ValidationError("Simpson node count changed")
    if counts.get("total_bound_union_cells") != 1392:
        raise ValidationError("bound grid union count changed")
    if grid.get("path_quadrature_grid", {}).get("subinterval_count") != 1024:
        raise ValidationError("Simpson subinterval count changed")
    if counts.get("structural_case_cells") != len(grid.get("structural_case_order", [])):
        raise ValidationError("structural grid count is not roster-derived")
    summary = certificate.get("reference_summary")
    if type(summary) is not dict or summary.get("all_reference_precision_budgets_pass") is not True:
        raise ValidationError("reference precision budgets did not pass")
    checks = summary.get("reference_precision_budget_checks")
    if type(checks) is not list or len(checks) != 12:
        raise ValidationError("reference precision surface roster changed")
    for check in checks:
        if type(check) is not dict or check.get("pass") is not True:
            raise ValidationError("reference precision check did not pass")
        if not _fraction_le(check["maximum_width"], check["budget"]):
            raise ValidationError("reference width exceeds budget")
    nonclaims = certificate.get("nonclaims")
    if type(nonclaims) is not dict or any(value is not False for value in nonclaims.values()):
        raise ValidationError("source nonclaims changed")
    if type(module.SCIENTIFIC_THRESHOLDS) is not MappingProxyType:
        raise ValidationError("scientific thresholds are mutable")
    if type(module.NUMERICAL_WIDTH_BUDGETS) is not MappingProxyType:
        raise ValidationError("candidate width budgets are mutable")
    if type(module.REFERENCE_WIDTH_BUDGETS) is not MappingProxyType:
        raise ValidationError("reference width budgets are mutable")
    if type(module.CAP2_STRUCTURAL_INVARIANTS) is not MappingProxyType:
        raise ValidationError("cap2 structural invariants are mutable")
    if type(module.A1_SECTION_7_3) is not tuple:
        raise ValidationError("A1 table roster is mutable")
    if any(type(row) is not MappingProxyType for row in module.A1_SECTION_7_3):
        raise ValidationError("A1 table row is mutable")
    for forbidden_cache in ("_TRANSITION_CACHE", "_MARK_COEFFICIENT_CACHE"):
        if hasattr(module, forbidden_cache):
            raise ValidationError("authoritative module-global cache exists")
    if module.FROZEN_CERTIFICATE_SHA256 != SOURCE_CERTIFICATE_SHA256:
        raise ValidationError("builder frozen digest literal changed")


def _source_evaluation(root: Path) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    module = _load_source_from_verified_bytes(root)
    certificate = module.build_certificate()
    _validate_certificate_semantics(module, certificate)
    certificate_receipt = module.validate_certificate(certificate)
    candidate = module.build_exact_self_candidate(certificate)
    qualification = module.qualify_candidate_errors(certificate, candidate)
    if qualification.get("validation") != "PASS":
        raise ValidationError("exact-self source qualification did not pass")
    return certificate, candidate, {
        "source_certificate_validation": certificate_receipt,
        "exact_self_candidate_qualification": qualification,
    }


def _predecessor_group_counts() -> Dict[str, int]:
    result: Dict[str, int] = {}
    for group, _role, _path, _size, _digest, _self in PREDECESSOR_SPECS:
        result[group] = result.get(group, 0) + 1
    result["total"] = len(PREDECESSOR_SPECS)
    return result


def expected_record(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    predecessor_bindings = _predecessor_bindings(root)
    certificate, candidate, source_receipts = _source_evaluation(root)
    field_closures = []
    for item in certificate["field_values"]:
        field_closures.append({
            "field_id": item["field_id"],
            "json_pointer": item["json_pointer"],
            "status": "CLOSED_BY_ALL_OR_NOTHING_CERTIFIED_PREOUTCOME_DESIGN_FREEZE",
            "value": item["value"],
        })
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
            "autonomous_local_project_work_authorized": True,
            "additive_v4_terminal_pass_custody_registration_authorized_separately": True,
            "network_data_entropy_training_live_runtime_scientific_execution_or_submission_authorized": False,
            "tracker_edit_authorized_by_this_package": False,
        },
        "package_file_roster": list(PACKAGE_ROSTER),
        "package_bindings_excluding_machine_self": _package_bindings(root),
        "machine_self_binding": {
            "path": MACHINE_PATH,
            "semantic_self_digest_field": "record_sha256",
            "raw_self_hash_embedded": False,
        },
        "predecessor_bindings": predecessor_bindings,
        "predecessor_group_counts": _predecessor_group_counts(),
        "focused_legacy_cache_custody": {
            "global_cache_absence_claimed": False,
            "ephemeral_legacy_pyc_presence_or_hash_is_canonical_input": False,
            "focused_cache_directories_required_to_exist": False,
            "legacy_cache_files_read_written_deleted_or_restored_by_validator": False,
            "clean_checkout_or_unrelated_cache_cleanup_reopens_gate": False,
            "verified_source_executed_from_hard_pinned_in_memory_bytes": True,
            "pathname_loader_or_pyc_used": False,
        },
        "source_binding": {
            "path": SOURCE_PATH,
            "bytes": SOURCE_BYTES,
            "sha256": SOURCE_SHA256,
            "schema_version": SOURCE_SCHEMA,
            "state": SOURCE_STATE,
            "frozen_certificate_sha256": SOURCE_CERTIFICATE_SHA256,
            "reference_table_sha256": REFERENCE_TABLE_SHA256,
            "grid_sha256": GRID_SHA256,
            "hard_pinned_before_in_memory_execution": True,
            "source_ast_safety_pass": True,
            "source_duplicate_literal_dict_key_count": 0,
            "authoritative_module_global_computed_cache_count": 0,
        },
        "known_law_certificate": certificate,
        "source_certificate_validation": source_receipts["source_certificate_validation"],
        "exact_self_reference_candidate": candidate,
        "exact_self_reference_qualification": source_receipts["exact_self_candidate_qualification"],
        "field_closures": field_closures,
        "all_or_nothing_closure": {
            "required_field_ids": list(CLOSED_BY_PACKAGE),
            "closed_field_ids": list(CLOSED_BY_PACKAGE),
            "required_count": 12,
            "closed_count": 12,
            "partial_credit_permitted": False,
            "any_missing_or_failed_field_makes_whole_package_hold": True,
            "F148_preserved_as_prior_separate_closed_field": True,
        },
        "count_transition": {
            "before": {
                "pre_execution_open": 158,
                "pre_execution_closed": 8,
                "post_execution_open": 6,
                "post_execution_closed": 0,
                "total_open": 164,
                "total_closed": 8,
            },
            "closed_by_package": {
                "field_ids": list(CLOSED_BY_PACKAGE),
                "pre_execution": 12,
                "post_execution": 0,
                "total": 12,
            },
            "after": {
                "pre_execution_open": 146,
                "pre_execution_closed": 20,
                "post_execution_open": 6,
                "post_execution_closed": 0,
                "total_open": 152,
                "total_closed": 20,
            },
            "closed_before_ids": list(CLOSED_BEFORE),
            "closed_after_ids": list(CLOSED_AFTER),
            "open_pre_after_count": len(OPEN_PRE_AFTER),
            "open_pre_after_ids": list(OPEN_PRE_AFTER),
            "blockers_open_after": 12,
            "blockers_closed": 0,
            "formal_tests_closed": 0,
            "results_filled": 0,
        },
        "project_effects_and_nonclaims": {
            "only_fields_closed": list(CLOSED_BY_PACKAGE),
            "F148_prior_separate_closure_preserved": True,
            "F114_F127_and_F149_remain_open": True,
            "B05_remains_open": True,
            "Gate_A_remains_open": True,
            "all_12_blockers_remain_open": True,
            "formal_test_28_status": "OPEN",
            "formal_test_29_status": "OPEN",
            "formal_test_30_status": "PENDING",
            "R1_R2_R3_R4_remain_open": True,
            "C17_remains_unproved": True,
            "scientific_execution_performed": False,
            "learned_candidate_or_checkpoint_present": False,
            "real_data_acquired_or_used": False,
            "runtime_or_submission_performed": False,
            "result_or_claim_promoted": False,
            "tracker_edit_performed": False,
        },
        "qualification_boundary": {
            "validator_read_only": True,
            "source_execution_from_verified_in_memory_bytes_only": True,
            "source_pathname_import_or_bytecode_execution": False,
            "exact_self_reference_only": True,
            "nonzero_reference_perturbation_is_decision_candidate": False,
            "candidate_scientific_ceiling_reference_width_and_candidate_width_are_three_distinct_roles": True,
            "cache_and_bytecode_disabled_external_qualification_required": True,
            "canonical_package_or_predecessor_bytes_modified_by_validation": False,
            "writer_network_connector_subprocess_entropy_data_training_runtime_scientific_worker_or_submission_route_present": False,
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


def _validate_against_expected(actual: object, expected: object) -> None:
    if type(actual) is not dict or type(expected) is not dict:
        raise ValidationError("actual and expected records must be exact dicts")
    if actual.get("record_sha256") != record_sha256(actual):
        raise ValidationError("machine record semantic self-digest mismatch")
    _strict_equal(actual, expected, "package machine record")


def validate(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    expected = expected_record(root)
    raw = _stable_read(root, MACHINE_PATH)
    actual = _parse_json(raw, "package machine record")
    if raw != canonical_machine_bytes(actual):
        raise ValidationError("package machine record is not canonical JSON")
    _validate_against_expected(actual, expected)
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": actual["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "closed_field_ids": list(CLOSED_BY_PACKAGE),
        "closed_field_count": 12,
        "effective_pre_execution_open": 146,
        "effective_post_execution_open": 6,
        "effective_unresolved_field_count": 152,
        "effective_closed_field_count": 20,
        "B05_closed": False,
        "gate_a_closed": False,
        "scientific_result": False,
        "tracker_edit_performed": False,
        "validation": "PASS",
    }


def main(argv: Sequence[str]) -> int:
    if list(argv) == ["--emit-expected"]:
        sys.stdout.buffer.write(canonical_machine_bytes(expected_record()))
        return 0
    if argv:
        raise ValidationError("only --emit-expected is accepted")
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
