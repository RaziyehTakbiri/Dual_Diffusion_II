#!/usr/bin/env python3
"""Offline validator for the Solo Block 2 V5 construction closure."""

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

SCHEMA = "heterodiff-manuscript-v3-solo-block2-runtime-custody-closure-v5"
STATE = "FINAL_V5_OFFLINE_ACTIVATION_SUCCESSOR_FROZEN_RECEIPTS_NULL_NETWORK_HOLD"
MACHINE_RELATIVE = "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v5.json"
EXECUTOR_RELATIVE = "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v5.py"
V4_VALIDATOR = "research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v4.py"
V5_ROOT = Path("/Users/mahtab/.codex/.chatgpt-projects/g-p-6a5f91c1e79c819183983ba0010bb151/research/custody/solo_block2_public_documentation_runtime_v4")
AUTHORITY_BYTES = 32
AUTHORITY_SHA256 = "654128b6829a8a04e609174149b6c55068b12cc994e21c0c24b9a91a9db080e0"
EXECUTOR_SHA256 = "bdb5ba02e4fcf651ec7d5f66639b3ff8f15bda2bfc2a8ac27ebce83e64eb900c"
SEMANTIC_AST_SHA256 = {
    "_spend_successor_budget_after_last_authority_gate": "0c183ab6cf00be53f9f75c0b7a1660d2e898beb67ad6d98800d396196df2a152",
    "_exclusive_precomputed_successor_budget_marker": "4025f0e1f8581a52934f648cf914ac7bb193b9948c6990b1105603bc65c26693",
    "_operation": "32aa7973d5594c391cf92df73a06c5c7a3cabc588069e5c24f30e206acecee74",
    "main": "612661eafba0090da74e1f73307116178e9bb1710e1269ac2995a44f7c1d72ac",
    "_late_pretransport_gate": "56fda2e1548051192e05f45dc7142aaff78d08f60fedbc8ac42db510ca7ee536",
    "register_preflight_authority": "8bf38a7452ce20009e6e0e014e6efaeeb70657acd63263a818b92db78e34f68a",
    "register_row_authority": "9de260f5f070ea057ea2c4814e140b420c3f3787faed362643b80d86fcb712ef",
}
KEY_ROSTER_SHA256 = {"ROW_AUTHORITY_KEYS":"654c0e9fa116e5e1c2eb9b7176e39dff1a0e421ad93a3b2a054d7f93cc4b71a6","SUCCESSOR_BUDGET_SPEND_KEYS":"b4f99f0b8329e75b8899f60b6d7f2e7ec02f3f83d8df0741ea513678bb980554"}
V5_PACKAGE_PATHS = {
    "PROJECT_SOLO_BLOCK2_RUNTIME_CUSTODY_CLOSURE_V5.md",
    "research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v5.py",
    "tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v5.py",
    EXECUTOR_RELATIVE,
    "tests/unit/test_solo_block2_runtime_custody_executor_v5.py",
}
V4_PACKAGE = {
    "PROJECT_SOLO_BLOCK2_RUNTIME_CUSTODY_CLOSURE_V4.md": (4296, "864d13f46b6f27d34fc92b425c97413a05c44a5fb0a0d0e49652b7216a328788"),
    "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v4.json": (16200, "8a18ebb868b657282cba04c1be43ae0f953fabf870002a4edcbdd1bddcd9fc70"),
    V4_VALIDATOR: (20334, "bc32e4775a6ea1ac557bafc66a27411f5cddfeb79e4daa0bd4dfc09e89af7a44"),
    "tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v4.py": (12056, "2cfa1bb546d7912c23708991965e0ff1ffc98678d65996b0c1c1f69724ff8b07"),
    "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v4.py": (155742, "52097725e4a162a93ae51b5b879db8c2aa1ae3934230b6e796ecb27fd650e586"),
    "tests/unit/test_solo_block2_runtime_custody_executor_v4.py": (41103, "404c2668ffbbfebee20e3d45478fa8d479f9925d18ca82248909632db7a0ba36"),
}
EXPECTED_TOP_KEYS = {
    "activation_checklist_effects", "activation_operational_slots",
    "direct_v4_predecessor_bindings", "executor_contract",
    "executor_source_binding", "offline_construction_authority",
    "operation_roster", "operational_custody_root", "package_bindings",
    "package_kind", "qualification_contract", "record_sha256",
    "reported_date", "schema_version", "state", "successor_budget_definition",
    "v2_spent_incident", "v4_package_aggregate_sha256",
}
EXPECTED_ROOT = {"absolute_path": str(V5_ROOT), "device": 16777234, "inode": 67067435, "uid": 501, "gid": 20, "mode_octal": "0700", "nlink_at_construction": 2, "empty_roster_at_construction": []}
EXPECTED_EFFECTS = {
    "v5_root_newly_created": False, "v5_reused_exact_authorized_v4_root": True, "v5_package_built": True,
    "v5_operational_receipt_created": False, "v5_durable_intent_created": False, "v5_durable_row_intent_created": False,
    "v5_resolver_call_performed": False, "v5_socket_created": False,
    "v5_connect_performed": False, "v5_tls_wrap_performed": False,
    "v5_sendall_performed": False, "v5_http_request_performed": False,
    "v5_row0_attempt_spent": False, "v5_row1_attempt_spent": False,
    "v5_fetch_performed": False, "v5_successor_budget_spent": False,
    "tracker_edited": False, "data_accessed": False, "scientific_execution_performed": False,
    "scientific_delta": "ZERO", "v2_attempt_budget_spent_preserved": True,
    "v1_bytes_or_custody_modified": False, "v2_bytes_or_custody_modified": False,
    "v3_bytes_or_custody_modified": False,
    "v4_bytes_or_custody_modified": False,
}
EXPECTED_SLOTS = {name: None for name in (
    "package_lock", "supersession_authority", "preflight_authority", "runtime_preflight",
    "row0_independent_go", "row0_authority", "row0_intent", "row0_outcome",
    "row1_independent_go", "row1_authority", "row1_intent", "row1_outcome",
    "successor_budget_spend", "unique_one_use_budget_id",
)}
EXPECTED_BUDGET = {
    "scope": "GLOBAL_SINGLE_ADDITIONAL_ROW0_ATTEMPT_ONLY",
    "authorized_definition": 1, "activated": 0, "remaining_usable": 0,
    "successor_budget_definition_id": "da3af347580d19b11f83b8590018a61b2e4296c613f78d8a1039c1c9cfdfb9ce",
    "activated_unique_one_use_budget_id": None,
    "row1_may_consume": False, "activation_authority_present": False,
    "activation_package_present": True, "fixture_resigning_can_activate": False,
    "separately_frozen_successor_activation_package_required": False,
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
    "schema_version": "heterodiff-solo-block2-runtime-custody-executor-v5",
    "machine_schema": SCHEMA, "machine_state": STATE,
    "current_operational_authority_present": False,
    "current_fetch_eligible": False, "current_usable_successor_attempt_budget": 0,
    "frozen_successor_attempt_definition": 1,
    "successor_budget_scope": "GLOBAL_SINGLE_ADDITIONAL_ROW0_ATTEMPT_ONLY",
    "successor_budget_definition_id": "da3af347580d19b11f83b8590018a61b2e4296c613f78d8a1039c1c9cfdfb9ce",
    "production_surface_is_row0_only_without_row_argument": True,
    "fixture_edit_or_resign_cannot_create_operational_authority": True,
    "fixed_root_marker_uniqueness_beyond_root_os_attested": False,
    "executing_image_one_open_attestation_claimed": False,
    "concurrent_same_uid_path_substitution_excluded": False,
    "registrar_identity_externally_authenticated": False,
    "registrar_time_externally_attested": False,
    "registrar_identity_and_time_are_caller_assertions": True,
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
def _load_v4_validator(root: Path):
    raw, _ = _read(root / V4_VALIDATOR)
    namespace = {"__name__": "_v5_bound_v4_validator", "__file__": str(root / V4_VALIDATOR)}
    exec(compile(raw, str(root / V4_VALIDATOR), "exec", dont_inherit=True), namespace)
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
    for name,digest in SEMANTIC_AST_SHA256.items():
        raw=json.dumps(_ast_semantic(functions.get(name)),sort_keys=True,separators=(",",":")).encode()
        if _sha(raw)!=digest:_fail(f"semantic AST mismatch: {name}")
    assignments={node.target.id:node.value for node in tree.body if isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name)}
    if ast.unparse(assignments.get("FILE_CREATE_FLAGS"))!="os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW":_fail("exclusive file-create flags mismatch")
    if ast.unparse(assignments.get("O_NOFOLLOW"))!="getattr(os, 'O_NOFOLLOW', 0)":_fail("O_NOFOLLOW derivation mismatch")
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
    forbidden = {"os.remove","os.unlink","os.rename","os.replace","os.rmdir","shutil.rmtree","urllib.request.urlopen","requests.get","requests.post"}
    if forbidden.intersection(all_calls): _fail("destructive or alternate network API present")
    for node in ast.walk(tree):
        if isinstance(node,ast.Dict):
            keys=[k.value for k in node.keys if isinstance(k,ast.Constant) and type(k.value) is str]
            if len(keys)!=len(set(keys)):_fail("duplicate constant-string dict key")
    source = ast.unparse(tree)
    functions_source = {name: ast.unparse(node) for name, node in functions.items()}
    perform = functions_source["_perform_spent_attempt"]
    ordered = ("_validate_resolver_receipt_rows(", "socket.socket(", "raw_socket.connect(", "ssl.SSLContext(", "context.wrap_socket(", "tls.sendall(")
    if any(token not in perform for token in ordered) or [perform.index(token) for token in ordered] != sorted(perform.index(token) for token in ordered):
        _fail("resolver/socket/TLS/send order mismatch")
    attempt = functions_source["attempt"]
    attempt_order = ("_spend_successor_budget_after_last_authority_gate(", "_revalidate_runtime_immediately_before_reservation(", "_mkdir_row(", "_exclusive_canonical_at(rowfd, 'intent.json', intent)", "_reopen_exact_digest_at(rowfd, 'intent.json', intent_digest)", "_perform_spent_attempt(")
    if any(token not in attempt for token in attempt_order) or [attempt.index(token) for token in attempt_order] != sorted(attempt.index(token) for token in attempt_order):
        _fail("runtime/reservation/durable-intent/network order mismatch")
    adjacency=False
    for parent in ast.walk(functions["attempt"]):
        for _field,value in ast.iter_fields(parent):
            if isinstance(value,list):
                for left,right in zip(value,value[1:]):
                    lc=[_dotted(n.func) for n in ast.walk(left) if isinstance(n,ast.Call)]
                    rc=[_dotted(n.func) for n in ast.walk(right) if isinstance(n,ast.Call)]
                    if "_late_pretransport_gate" in lc and "_perform_spent_attempt" in rc: adjacency=True
    if not adjacency:_fail("late pre-transport gate is not statement-adjacent to transport")
    marker = functions_source["_exclusive_precomputed_successor_budget_marker"]
    if "os.open('successor-budget-spend.json', FILE_CREATE_FLAGS, 384, dir_fd=rootfd)" not in marker or marker.index("os.open(") > marker.index("try:"):
        _fail("spend marker is not fixed-name O_EXCL-first")
    spend = functions_source["_spend_successor_budget_after_last_authority_gate"]
    spend_order=("_validate_row_authority(","_read_receipt_at(","_exclusive_precomputed_successor_budget_marker(","_reopen_exact_digest_at(")
    if any(t not in spend for t in spend_order) or [spend.index(t) for t in spend_order] != sorted(spend.index(t) for t in spend_order): _fail("last authority/marker order mismatch")
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
        "normalization": "EXACT_VISIBLE_TEXT_NO_TERMINAL_NEWLINE",
        "source": "visible_user_message_in_current_task",
        "scope": "CONSTRUCT_AND_FREEZE_OFFLINE_V5_SUCCESSOR_ONLY",
        "context": "immediately_preceding_described_stage_only",
        "user_message_created_unix_ns": None, "user_message_time_supplied": False,
        "created_time_externally_attested": False, "authority_identity_externally_authenticated": False,
        "network_or_contact_authorized": False, "resolver_socket_tls_http_authorized": False,
        "operational_receipt_registration_authorized": False, "preflight_authorized": False, "same_url_attempt_authorized": False,
        "tracker_or_science_authorized": False,
    }: _fail("construction authority contract mismatch")
def _validate_root(machine: Mapping[str, Any]) -> None:
    if machine.get("operational_custody_root") != EXPECTED_ROOT: _fail("V5 root machine identity mismatch")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in V5_ROOT.parts[1:]:
            if not part or part in (".", "..") or "/" in part or "\x00" in part: _fail("unsafe root component")
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = nxt
        st = os.fstat(fd)
        actual = {"absolute_path": str(V5_ROOT), "device": st.st_dev, "inode": st.st_ino, "uid": st.st_uid, "gid": st.st_gid, "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}", "nlink_at_construction": st.st_nlink, "empty_roster_at_construction": sorted(os.listdir(fd))}
        if not stat.S_ISDIR(st.st_mode) or actual != EXPECTED_ROOT: _fail("V5 root is not exact empty construction root")
    finally: os.close(fd)

def validate(root: Path) -> dict[str, Any]:
    root = root.absolute(); machine, raw = _record(root / MACHINE_RELATIVE)
    if set(machine) != EXPECTED_TOP_KEYS: _fail("machine top-level key roster mismatch")
    if machine.get("schema_version") != SCHEMA or machine.get("state") != STATE: _fail("schema/state mismatch")
    if machine.get("reported_date") != "2026-08-31": _fail("reported date mismatch")
    _validate_authority(machine); _validate_root(machine)
    v4 = _load_v4_validator(root); v4_result = v4["validate"](root)
    if v4_result.get("status") != "PASS": _fail("V4 predecessor validation failed")
    actual_v4 = [_receipt(root, path, False) for path in sorted(V4_PACKAGE)]
    for item in actual_v4:
        size, digest = V4_PACKAGE[item["path"]]
        if (item["bytes"], item["sha256"]) != (size, digest): _fail("V4 predecessor bytes drift")
    if machine.get("direct_v4_predecessor_bindings") != actual_v4: _fail("V4 binding roster mismatch")
    v4_machine, _ = _record(root / "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v4.json")
    if machine.get("v2_spent_incident") != v4_machine.get("v2_spent_incident"): _fail("V2 incident projection mismatch")
    if machine.get("operation_roster") != [v4_machine.get("operation_roster")[0]]: _fail("exact row0-only operation roster mismatch")
    if machine.get("v4_package_aggregate_sha256")!="449c5d4954e4ac3829994d4ba5dd17ed401388548a93469cf1f0bb35e67ecb02":_fail("V4 aggregate mismatch")
    operations = machine["operation_roster"]
    if type(operations) is not list or len(operations) != 1 or type(operations[0]) is not dict or operations[0].get("fetch_eligible") is not False: _fail("operation eligibility mismatch")
    if operations[0].get("request_sha256") != "ac9c9c12e45d8690381803e003a36cfa22c330b8e8ea601d94725b4312be9449": _fail("exact request digest mismatch")
    actual = [_receipt(root, path, True) for path in sorted(V5_PACKAGE_PATHS)]
    if machine.get("package_bindings") != actual: _fail("V5 package bindings mismatch")
    executor = next(item for item in actual if item["path"] == EXECUTOR_RELATIVE)
    if machine.get("executor_source_binding") != {k: executor[k] for k in ("path", "bytes", "sha256")}: _fail("executor binding mismatch")
    for key, expected in (("activation_checklist_effects", EXPECTED_EFFECTS), ("activation_operational_slots", EXPECTED_SLOTS), ("successor_budget_definition", EXPECTED_BUDGET), ("qualification_contract", EXPECTED_QUALIFICATION), ("executor_contract", EXPECTED_EXECUTOR)):
        if machine.get(key) != expected: _fail(f"exact nested contract mismatch: {key}")
    source, _ = _read(root / EXECUTOR_RELATIVE)
    if _sha(source) != EXECUTOR_SHA256: _fail("frozen V5 executor byte anchor mismatch")
    tree = ast.parse(source); _validate_executor_tree(tree)
    constants: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            try: constants[node.target.id] = ast.literal_eval(node.value)
            except (ValueError, TypeError): pass
    exact_constants = {
        "SCHEMA_VERSION": EXPECTED_EXECUTOR["schema_version"],
        "MACHINE_SCHEMA": SCHEMA, "MACHINE_STATE": STATE,
        "SUCCESSOR_BUDGET_SCOPE": EXPECTED_BUDGET["scope"],
        "SUCCESSOR_BUDGET_DEFINITION_ID": EXPECTED_BUDGET["successor_budget_definition_id"],
        "V5_OPERATIONAL_ROOT": str(V5_ROOT),
        "V4_PACKAGE_AGGREGATE_SHA256": "449c5d4954e4ac3829994d4ba5dd17ed401388548a93469cf1f0bb35e67ecb02",
    }
    if any(constants.get(k) != v for k, v in exact_constants.items()): _fail("compiled dormant constant mismatch")
    functions = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    signatures={
        "register_package_lock":["custody_root","independent_reviewer_principal","created_unix_ns"],
        "register_supersession_authority":["custody_root","created_unix_ns","activated_successor_budget_id","normalized_visible_text"],
        "register_preflight_authority":["custody_root","created_unix_ns","normalized_visible_text"],
        "preflight":["custody_root"],"register_independent_go":["custody_root","independent_reviewer_principal","created_unix_ns"],
        "register_row_authority":["custody_root","created_unix_ns","expires_unix_ns","normalized_visible_text"],"attempt":["custody_root"],
    }
    for name,args in signatures.items():
        fn=functions.get(name)
        if fn is None or [a.arg for a in fn.args.args]!=args or fn.args.vararg or fn.args.kwarg or fn.args.defaults:_fail(f"public signature mismatch: {name}")
    for roster_name in ("ROW_AUTHORITY_KEYS","SUCCESSOR_BUDGET_SPEND_KEYS"):
        roster=constants.get(roster_name)
        digest=_sha(json.dumps(roster,separators=(",",":")).encode()) if type(roster) is tuple else ""
        if len(roster)!=len(set(roster)) or digest!=KEY_ROSTER_SHA256[roster_name]: _fail("authority/marker schema roster invalid")
    if machine.get("package_kind") != "V5_OFFLINE_ACTIVATION_SUCCESSOR_CLOSURE": _fail("package kind mismatch")
    return {"status": "PASS", "schema_version": SCHEMA, "machine_raw_sha256": _sha(raw), "machine_semantic_sha256": machine["record_sha256"], "v5_root_entries": 0, "v5_operational_receipts": 0, "v5_activated_budget": 0, "v5_network_actions": 0, "v2_attempt_spent_preserved": True}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2]); args = parser.parse_args(argv)
    try: result = validate(args.root)
    except (ValidationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True)); return 1
    print(json.dumps(result, sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
