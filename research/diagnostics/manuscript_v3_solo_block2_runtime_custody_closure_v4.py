#!/usr/bin/env python3
"""Offline validator for the Solo Block 2 V4 construction closure."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "heterodiff-manuscript-v3-solo-block2-runtime-custody-closure-v4"
STATE = "FINAL_V4_OFFLINE_ACTIVATION_CONSTRUCTION_EMPTY_ROOT_RECEIPTS_NULL_NETWORK_HOLD"
MACHINE_RELATIVE = "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v4.json"
EXECUTOR_RELATIVE = "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v4.py"
V3_VALIDATOR = "research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v3.py"
V4_ROOT = Path("/Users/mahtab/.codex/.chatgpt-projects/g-p-6a5f91c1e79c819183983ba0010bb151/research/custody/solo_block2_public_documentation_runtime_v4")
AUTHORITY_BYTES = 2160
AUTHORITY_SHA256 = "ddc50a0920cdcf6fb11f582cd471ffe640f968fa365a92389d326a4b1d0c164a"
EXECUTOR_SHA256 = "52097725e4a162a93ae51b5b879db8c2aa1ae3934230b6e796ecb27fd650e586"
GATE_AST_SHA256 = {
    "_require_activation_authority_present": "95d4a22e5fa232fc1de97363f63052d1c0a3c4f575fd23d9824caf7250dfa072",
    "_require_dormant_production_row0": "7e97129cab8ce8e9d4777bbe208186ab7ed34a194cd8fbafc0a2c8eca33a28dc",
}
V4_PACKAGE_PATHS = {
    "PROJECT_SOLO_BLOCK2_RUNTIME_CUSTODY_CLOSURE_V4.md",
    "research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v4.py",
    "tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v4.py",
    EXECUTOR_RELATIVE,
    "tests/unit/test_solo_block2_runtime_custody_executor_v4.py",
}
V3_PACKAGE = {
    "PROJECT_SOLO_BLOCK2_RUNTIME_CUSTODY_CLOSURE_V3.md": (7636, "7761bcf3e87dd527e6f17fe3d74783b848f886957baee3e1ca69678ed24efd60"),
    "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v3.json": (14215, "a9b007e61a5e26f1d44a642442c305281408f2998d7dc48a7545b81c2c5d3779"),
    V3_VALIDATOR: (36357, "53fb7a3afb8f0cf798e9d0cd0970fe370f5e2c0a7ed72bef0ce5c9f414de1153"),
    "tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v3.py": (11236, "07852addf23917e844ee3a7c6fcb00eed0c94255b74aa2772c78b5b6db644d18"),
    "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v3.py": (151888, "e2059b19e1bfa447370392451fdf3574145ef68618b31b2f9c9af8a21239c2a9"),
    "tests/unit/test_solo_block2_runtime_custody_executor_v3.py": (37330, "50ec9de7e18d43a81d0d1164a3710165fd02f40cd43489f37754b95ca0132fdf"),
}
EXPECTED_TOP_KEYS = {
    "construction_checklist_effects", "construction_operational_slots",
    "direct_v3_predecessor_bindings", "executor_contract",
    "executor_source_binding", "offline_construction_authority",
    "operation_roster", "operational_custody_root", "package_bindings",
    "package_kind", "qualification_contract", "record_sha256",
    "reported_date", "schema_version", "state", "successor_budget_definition",
    "v2_spent_incident",
}
EXPECTED_ROOT = {"absolute_path": str(V4_ROOT), "device": 16777234, "inode": 67067435, "uid": 501, "gid": 20, "mode_octal": "0700", "nlink_at_construction": 2, "empty_roster_at_construction": []}
EXPECTED_EFFECTS = {
    "v4_root_created": True, "v4_package_built": True,
    "v4_operational_receipt_created": False, "v4_durable_intent_created": False,
    "v4_resolver_call_performed": False, "v4_socket_created": False,
    "v4_connect_performed": False, "v4_tls_wrap_performed": False,
    "v4_sendall_performed": False, "v4_http_request_performed": False,
    "v4_row0_attempt_spent": False, "v4_row1_attempt_spent": False,
    "tracker_edited": False, "data_accessed": False, "scientific_execution_performed": False,
    "scientific_delta": "ZERO", "v2_attempt_budget_spent_preserved": True,
    "v1_bytes_or_custody_modified": False, "v2_bytes_or_custody_modified": False,
    "v3_bytes_or_custody_modified": False,
}
EXPECTED_SLOTS = {name: None for name in (
    "package_lock", "supersession_authority", "preflight_authority", "runtime_preflight",
    "row0_independent_go", "row0_authority", "row0_intent", "row0_outcome",
    "row1_independent_go", "row1_authority", "row1_intent", "row1_outcome",
    "unique_one_use_budget_id",
)}
EXPECTED_BUDGET = {
    "scope": "GLOBAL_SINGLE_ADDITIONAL_ROW0_ATTEMPT_ONLY",
    "authorized_definition": 1, "activated": 0, "remaining_usable": 0,
    "successor_budget_definition_id": "da3af347580d19b11f83b8590018a61b2e4296c613f78d8a1039c1c9cfdfb9ce",
    "activated_unique_one_use_budget_id": None,
    "row1_may_consume": False, "activation_authority_present": False,
    "activation_package_present": False, "fixture_resigning_can_activate": False,
    "separately_frozen_successor_activation_package_required": True,
    "fresh_exact_activation_authority_required": True,
    "future_package_and_authority_must_bind_definition_id": True,
    "new_version_or_root_resets_spent_v2_budget": False,
}
EXPECTED_QUALIFICATION = {
    "external_network_permitted": False, "loopback_permitted": False,
    "production_command_invocation_permitted": False,
    "operational_root_write_permitted": False,
    "operational_receipt_materialization_permitted": False,
    "qualification_can_spend_attempt": False, "qualification_can_verify_official_fact": False,
    "bytecode_cache_disabled_required": True, "pytest_cache_disabled_required": True,
}
EXPECTED_EXECUTOR = {
    "schema_version": "heterodiff-solo-block2-runtime-custody-executor-v4",
    "machine_schema": SCHEMA, "machine_state": STATE,
    "compiled_activation_authority_present": False,
    "compiled_fetch_eligible": False, "compiled_authorized_successor_attempt_budget": 0,
    "planned_global_successor_attempt_limit": 1,
    "successor_budget_scope": "GLOBAL_SINGLE_ADDITIONAL_ROW0_ATTEMPT_ONLY",
    "successor_budget_definition_id": "da3af347580d19b11f83b8590018a61b2e4296c613f78d8a1039c1c9cfdfb9ce",
    "all_production_surfaces_fail_before_root_machine_process_or_network": True,
    "row_surfaces_accept_only_exact_builtin_int_zero_then_fail_dormant": True,
    "fixture_edit_or_resign_cannot_activate_compiled_false_gate": True,
    "separately_frozen_successor_activation_package_required": True,
}

class ValidationError(RuntimeError): pass
def _fail(message: str) -> None: raise ValidationError(message)
def _sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()
def _canonical(value: Mapping[str, Any]) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode() + b"\n"
def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in out: _fail("duplicate JSON key")
        out[key] = value
    return out
def _read(path: Path) -> tuple[bytes, os.stat_result]:
    absolute = path.absolute()
    parts = absolute.parts[1:]
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd); os.close(fd); fd = nxt
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            st = os.fstat(leaf)
            if not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o644 or st.st_nlink != 1: _fail(f"unsafe package file: {path}")
            raw = bytearray()
            while chunk := os.read(leaf, 131072): raw.extend(chunk)
            return bytes(raw), st
        finally: os.close(leaf)
    finally: os.close(fd)
def _record(path: Path) -> tuple[dict[str, Any], bytes]:
    raw, _ = _read(path)
    value = json.loads(raw, object_pairs_hook=_pairs)
    if type(value) is not dict or _canonical(value) != raw: _fail("machine is not canonical")
    clone = dict(value); claimed = clone.get("record_sha256"); clone["record_sha256"] = None
    if type(claimed) is not str or claimed != _sha(_canonical(clone)): _fail("machine self digest mismatch")
    return value, raw
def _receipt(root: Path, relative: str, mtime: bool) -> dict[str, Any]:
    raw, st = _read(root / relative)
    out = {"path": relative, "bytes": len(raw), "sha256": _sha(raw), "mode_octal": "0644", "nlink": 1}
    if mtime: out["mtime_ns"] = st.st_mtime_ns
    return out
def _load_v3_validator(root: Path):
    raw, _ = _read(root / V3_VALIDATOR)
    namespace = {"__name__": "_v4_bound_v3_validator", "__file__": str(root / V3_VALIDATOR)}
    exec(compile(raw, str(root / V3_VALIDATOR), "exec", dont_inherit=True), namespace)
    return namespace
def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute): return f"{_dotted(node.value)}.{node.attr}"
    return ""
def _owned_calls(function: ast.FunctionDef) -> list[str]:
    calls: list[str] = []; stack: list[ast.AST] = list(function.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)): continue
        if isinstance(node, ast.Call): calls.append(_dotted(node.func))
        stack.extend(ast.iter_child_nodes(node))
    return calls
def _ast_semantic(node: Any) -> Any:
    if isinstance(node, ast.AST):
        out = {"_": type(node).__name__}
        for key, value in ast.iter_fields(node):
            projected = _ast_semantic(value)
            if projected not in (None, [], {}): out[key] = projected
        return out
    if isinstance(node, list): return [_ast_semantic(item) for item in node]
    return node
def _validate_executor_tree(tree: ast.Module) -> None:
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    for name, expected in GATE_AST_SHA256.items():
        node = functions.get(name)
        semantic = json.dumps(_ast_semantic(node), sort_keys=True, separators=(",", ":")).encode() if node is not None else b""
        if node is None or _sha(semantic) != expected:
            _fail(f"compiled dormant gate AST mismatch: {name}")
    expected_calls = {
        "socket.getaddrinfo": ("_bounded_single_getaddrinfo", 1),
        "socket.socket": ("_perform_spent_attempt", 1),
        "raw_socket.connect": ("_perform_spent_attempt", 1),
        "ssl.SSLContext": ("_perform_spent_attempt", 1),
        "context.wrap_socket": ("_perform_spent_attempt", 1),
        "tls.sendall": ("_perform_spent_attempt", 1),
        "os.fork": ("_bounded_single_getaddrinfo", 1),
        "subprocess.run": ("_capture_scutil_dns", 1),
        "_bounded_single_getaddrinfo": ("_perform_spent_attempt", 1),
        "_perform_spent_attempt": ("attempt", 1),
    }
    found = {name: [] for name in expected_calls}
    for function in functions.values():
        for call in _owned_calls(function):
            if call in found: found[call].append(function.name)
    for name, (owner, count) in expected_calls.items():
        if found[name] != [owner] * count: _fail(f"operational call ownership mismatch: {name}")
    all_calls = [_dotted(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    for name, (_owner, count) in expected_calls.items():
        if all_calls.count(name) != count: _fail(f"whole-module operational call count mismatch: {name}")
    source = ast.unparse(tree)
    functions_source = {name: ast.unparse(node) for name, node in functions.items()}
    perform = functions_source["_perform_spent_attempt"]
    ordered = ("_validate_resolver_receipt_rows(", "socket.socket(", "raw_socket.connect(", "ssl.SSLContext(", "context.wrap_socket(", "tls.sendall(")
    if any(token not in perform for token in ordered) or [perform.index(token) for token in ordered] != sorted(perform.index(token) for token in ordered):
        _fail("resolver/socket/TLS/send order mismatch")
    attempt = functions_source["attempt"]
    attempt_order = ("_revalidate_runtime_immediately_before_reservation(", "_mkdir_row(", "_exclusive_canonical_at(rowfd, 'intent.json', intent)", "_reopen_exact_digest_at(rowfd, 'intent.json', intent_digest)", "_perform_spent_attempt(")
    if any(token not in attempt for token in attempt_order) or [attempt.index(token) for token in attempt_order] != sorted(attempt.index(token) for token in attempt_order):
        _fail("runtime/reservation/durable-intent/network order mismatch")
def _validate_authority(machine: Mapping[str, Any]) -> None:
    authority = machine.get("offline_construction_authority")
    if type(authority) is not dict: _fail("construction authority absent")
    text = authority.get("normalized_visible_text")
    if type(text) is not str or text.endswith("\n"): _fail("authority text framing invalid")
    raw = text.encode()
    if len(raw) != AUTHORITY_BYTES or _sha(raw) != AUTHORITY_SHA256: _fail("authority exact bytes mismatch")
    if authority != {
        "normalized_visible_text": text, "normalized_visible_text_utf8_bytes": AUTHORITY_BYTES,
        "normalized_visible_text_sha256": AUTHORITY_SHA256,
        "normalization": "EXACT_VISIBLE_TEXT_LF_NO_TERMINAL_NEWLINE",
        "source": "visible_user_message_in_current_task",
        "scope": "CREATE_ONE_EMPTY_RUNTIME_V4_ROOT_AND_BUILD_OFFLINE_ACTIVATION_PACKAGE_ONLY",
        "user_message_created_unix_ns": None, "user_message_time_supplied": False,
        "created_time_externally_attested": False, "authority_identity_externally_authenticated": False,
        "network_or_contact_authorized": False, "resolver_socket_tls_http_authorized": False,
        "operational_receipt_registration_authorized": False, "same_url_attempt_authorized": False,
        "tracker_or_science_authorized": False,
    }: _fail("construction authority contract mismatch")
def _validate_root(machine: Mapping[str, Any]) -> None:
    if machine.get("operational_custody_root") != EXPECTED_ROOT: _fail("V4 root machine identity mismatch")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in V4_ROOT.parts[1:]:
            if not part or part in (".", "..") or "/" in part or "\x00" in part: _fail("unsafe root component")
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = nxt
        st = os.fstat(fd)
        actual = {"absolute_path": str(V4_ROOT), "device": st.st_dev, "inode": st.st_ino, "uid": st.st_uid, "gid": st.st_gid, "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}", "nlink_at_construction": st.st_nlink, "empty_roster_at_construction": sorted(os.listdir(fd))}
        if not stat.S_ISDIR(st.st_mode) or actual != EXPECTED_ROOT: _fail("V4 root is not exact empty construction root")
    finally: os.close(fd)

def validate(root: Path) -> dict[str, Any]:
    root = root.absolute(); machine, raw = _record(root / MACHINE_RELATIVE)
    if set(machine) != EXPECTED_TOP_KEYS: _fail("machine top-level key roster mismatch")
    if machine.get("schema_version") != SCHEMA or machine.get("state") != STATE: _fail("schema/state mismatch")
    if machine.get("reported_date") != "2026-08-31": _fail("reported date mismatch")
    _validate_authority(machine); _validate_root(machine)
    v3 = _load_v3_validator(root); v3_result = v3["validate"](root)
    if v3_result.get("status") != "PASS": _fail("V3 predecessor validation failed")
    actual_v3 = [_receipt(root, path, False) for path in sorted(V3_PACKAGE)]
    for item in actual_v3:
        size, digest = V3_PACKAGE[item["path"]]
        if (item["bytes"], item["sha256"]) != (size, digest): _fail("V3 predecessor bytes drift")
    if machine.get("direct_v3_predecessor_bindings") != actual_v3: _fail("V3 binding roster mismatch")
    v3_machine, _ = _record(root / "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v3.json")
    if machine.get("v2_spent_incident") != v3_machine.get("v2_spent_incident"): _fail("V2 incident projection mismatch")
    if machine.get("operation_roster") != v3_machine.get("operation_roster"): _fail("exact dormant operation roster mismatch")
    operations = machine["operation_roster"]
    if type(operations) is not list or len(operations) != 2 or any(type(row) is not dict or row.get("fetch_eligible") is not False for row in operations): _fail("operation eligibility mismatch")
    if operations[0].get("request_sha256") != "ac9c9c12e45d8690381803e003a36cfa22c330b8e8ea601d94725b4312be9449" or operations[1].get("request_sha256") != "94271e586cfbec1d25c03754b1c4f47aadbd8e9459cffad6c050e0a80cf16b1b": _fail("exact request digest mismatch")
    actual = [_receipt(root, path, True) for path in sorted(V4_PACKAGE_PATHS)]
    if machine.get("package_bindings") != actual: _fail("V4 package bindings mismatch")
    executor = next(item for item in actual if item["path"] == EXECUTOR_RELATIVE)
    if machine.get("executor_source_binding") != {k: executor[k] for k in ("path", "bytes", "sha256")}: _fail("executor binding mismatch")
    for key, expected in (("construction_checklist_effects", EXPECTED_EFFECTS), ("construction_operational_slots", EXPECTED_SLOTS), ("successor_budget_definition", EXPECTED_BUDGET), ("qualification_contract", EXPECTED_QUALIFICATION), ("executor_contract", EXPECTED_EXECUTOR)):
        if machine.get(key) != expected: _fail(f"exact nested contract mismatch: {key}")
    source, _ = _read(root / EXECUTOR_RELATIVE)
    if _sha(source) != EXECUTOR_SHA256: _fail("frozen V4 executor byte anchor mismatch")
    tree = ast.parse(source); _validate_executor_tree(tree)
    constants: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            try: constants[node.target.id] = ast.literal_eval(node.value)
            except (ValueError, TypeError): pass
    exact_constants = {
        "SCHEMA_VERSION": EXPECTED_EXECUTOR["schema_version"],
        "MACHINE_SCHEMA": SCHEMA, "MACHINE_STATE": STATE,
        "ACTIVATION_AUTHORITY_PRESENT": False, "FETCH_ELIGIBLE": False,
        "AUTHORIZED_SUCCESSOR_ATTEMPT_BUDGET": 0,
        "PLANNED_GLOBAL_SUCCESSOR_ATTEMPT_LIMIT": 1,
        "SUCCESSOR_BUDGET_SCOPE": EXPECTED_BUDGET["scope"],
        "SUCCESSOR_BUDGET_ID": EXPECTED_BUDGET["successor_budget_definition_id"],
        "V4_OPERATIONAL_ROOT": str(V4_ROOT),
    }
    if any(constants.get(k) != v for k, v in exact_constants.items()): _fail("compiled dormant constant mismatch")
    functions = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for name in ("preflight", "register_package_lock", "register_preflight_authority", "main"):
        body = functions[name].body
        first = body[1] if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str) else body[0]
        if not (isinstance(first, ast.Expr) and isinstance(first.value, ast.Call) and isinstance(first.value.func, ast.Name) and first.value.func.id == "_require_activation_authority_present"):
            _fail(f"production surface is not dormant-first: {name}")
    for name in ("register_independent_go", "register_row_authority", "attempt"):
        body = functions[name].body
        first = body[1] if isinstance(body[0], ast.Expr) else body[0]
        if not (isinstance(first, ast.Expr) and isinstance(first.value, ast.Call) and isinstance(first.value.func, ast.Name) and first.value.func.id == "_require_dormant_production_row0"):
            _fail(f"row surface is not exact-row dormant-first: {name}")
    if machine.get("package_kind") != "V4_OFFLINE_ACTIVATION_CONSTRUCTION_EMPTY_ROOT_CLOSURE": _fail("package kind mismatch")
    return {"status": "PASS", "schema_version": SCHEMA, "machine_raw_sha256": _sha(raw), "machine_semantic_sha256": machine["record_sha256"], "v4_root_entries": 0, "v4_operational_receipts": 0, "v4_activated_budget": 0, "v4_network_actions": 0, "v2_attempt_spent_preserved": True}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2]); args = parser.parse_args(argv)
    try: result = validate(args.root)
    except (ValidationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True)); return 1
    print(json.dumps(result, sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
