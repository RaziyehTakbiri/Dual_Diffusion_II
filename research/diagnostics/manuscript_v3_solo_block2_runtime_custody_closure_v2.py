#!/usr/bin/env python3
"""Read-only validator for the Solo Block 2 runtime/custody closure v2."""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "heterodiff-manuscript-v3-solo-block2-runtime-custody-closure-v2"
STATE = "FINAL_V2_EXECUTOR_QUALIFIED_OPERATIONAL_RECEIPTS_NULL_FETCH_HOLD"
V2_ROOT = (
    "/Users/mahtab/.codex/.chatgpt-projects/"
    "g-p-6a5f91c1e79c819183983ba0010bb151/"
    "research/custody/solo_block2_public_documentation_runtime_v2"
)
V1_ROOT = (
    "/Users/mahtab/.codex/.chatgpt-projects/"
    "g-p-6a5f91c1e79c819183983ba0010bb151/"
    "research/custody/solo_block2_public_documentation_runtime_v1"
)
V2_ROOT_IDENTITY = {
    "absolute_path": V2_ROOT,
    "device": 16777234,
    "inode": 66956470,
    "uid": 501,
    "gid": 20,
    "mode_octal": "0700",
    "nlink_at_package_construction": 2,
    "empty_at_package_construction": True,
    "row_directories_present": False,
}
V1_ROOT_IDENTITY = {
    "absolute_path": V1_ROOT,
    "device": 16777234,
    "inode": 66899471,
    "uid": 501,
    "gid": 20,
    "mode_octal": "0700",
}
V1_GATE_RECEIPTS = {
    "package-lock.json": {
        "raw_sha256": "b82a85ae8444fefab8539631c6ac96c8eafd21ace6fc48e8a2e6eda42d02c966",
        "record_sha256": "02dd917f4308ffca5fcc212b891246f2d8869023eb436087e5fc6164407094b9",
    },
    "preflight-authority.json": {
        "raw_sha256": "7e6d367b7d6b6e167f6b356d80a2b5e52b61209bd3c72ce66a9341161c6e7008",
        "record_sha256": "e4124a038fc49d02b22d71f2edee555bd3bb200c343d33e08f5eddf441dd36b5",
    },
    "runtime-preflight.json": {
        "raw_sha256": "7f132cd4b7f3d2c39c3dde36f0511eacbb6425c01c199434dd460e0e8e68806f",
        "record_sha256": "302760729f8036dac4a54e5d4cc3ebd709e2f7fe0a3f983d5c98291c9f1376ce",
    },
    "row0-independent-go.json": {
        "raw_sha256": "af3c24fb108060aa93c86b34243726df8e7fdd68665177b6a6c1344554a641c1",
        "record_sha256": "41638552af9b49c03190877d0aa60fe9d49546b3f3635ad0d12b93b88875e60f",
    },
    "row0-authority.json": {
        "raw_sha256": "f07da9ea979713422fb513c61311e11ddcd97ad8f1db58be07dbc12d4108809d",
        "record_sha256": "f925a87c6e2b5c6a1d0321d339a233fe44a82b33dd29fd10b8f8972dc700ae45",
    },
}
V1_PREDECESSOR = {
    "PROJECT_SOLO_BLOCK2_RUNTIME_CUSTODY_CLOSURE.md": (
        18_638,
        "a95e36d82c3fa1841420c05d6505934311494bbf97f19de1cd6508be25484bba",
    ),
    "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v1.json": (
        15_148,
        "d3babc578e1fa33a5bdbc8a3bd18139e500324fe81a2967c733c91bde21eff93",
    ),
    "research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v1.py": (
        35_434,
        "53a4f9c3a0bdeebb470ba7f289a215c448375393871e20cb515ed0582fe7a7ca",
    ),
    "tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v1.py": (
        13_234,
        "e86f67c2a7506efa81a2710570b50fddfde6dfbcf78630a168113ea8ef2e8a33",
    ),
    "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v1.py": (
        148_728,
        "da92f4546eb7ec1cb60071a9d54afef2d1c91fbfaa386014870c3f642d33d407",
    ),
    "tests/unit/test_solo_block2_runtime_custody_executor_v1.py": (
        23_022,
        "f47a50ff57f79c9c79a8206c1a53b014559826bad20940346b4e7f1fa37b51b6",
    ),
}
V2_PACKAGE_PATHS = {
    "PROJECT_SOLO_BLOCK2_RUNTIME_CUSTODY_CLOSURE_V2.md",
    "research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v2.py",
    "tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v2.py",
    "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v2.py",
    "tests/unit/test_solo_block2_runtime_custody_executor_v2.py",
}
MACHINE_RELATIVE = (
    "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v2.json"
)
EXECUTOR_RELATIVE = (
    "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v2.py"
)
EXPECTED_TOP_KEYS = {
    "schema_version",
    "record_sha256",
    "state",
    "reported_date",
    "package_kind",
    "direct_v1_predecessor_bindings",
    "package_bindings",
    "executor_source_binding",
    "operational_custody_root",
    "v1_pre_reservation_incident",
    "operation_roster",
    "runtime_manifest_contract",
    "executor_contract",
    "qualification_contract",
    "current_operational_slots",
    "checklist_effects",
}
EXPECTED_COMMANDS = [
    "register-package-lock ROOT REVIEWER CREATED_UNIX_NS",
    "register-preflight-authority ROOT CREATED_UNIX_NS EXACT_TEXT",
    "preflight ROOT",
    "register-independent-go ROOT ROW REVIEWER CREATED_UNIX_NS",
    "register-row-authority ROOT ROW CREATED_UNIX_NS EXPIRES_UNIX_NS EXACT_TEXT",
    "attempt ROOT ROW",
]

REQUESTS = (
    (
        b"GET /content/challenge-2012/1.0.0/ HTTP/1.1\r\n"
        b"Host: physionet.org\r\n"
        b"User-Agent: heterodiff-precontact-public-doc-recon-v2/2.0\r\n"
        b"Accept: text/html, application/xhtml+xml;q=0.9, text/plain;q=0.8\r\n"
        b"Accept-Encoding: identity\r\n"
        b"Cache-Control: no-cache\r\n"
        b"Pragma: no-cache\r\n"
        b"Connection: close\r\n\r\n"
    ),
    (
        b"GET /dataset/502/online+retail+ii HTTP/1.1\r\n"
        b"Host: archive.ics.uci.edu\r\n"
        b"User-Agent: heterodiff-precontact-public-doc-recon-v2/2.0\r\n"
        b"Accept: text/html, application/xhtml+xml;q=0.9, text/plain;q=0.8\r\n"
        b"Accept-Encoding: identity\r\n"
        b"Cache-Control: no-cache\r\n"
        b"Pragma: no-cache\r\n"
        b"Connection: close\r\n\r\n"
    ),
)
EXPECTED_OPERATIONS = (
    {
        "ordinal": 0,
        "operation_id": "SB2-PUBLIC-ROOT-PHYSIONET-000",
        "domain": "PhysioNet",
        "url": "https://physionet.org/content/challenge-2012/1.0.0/",
        "host": "physionet.org",
        "path": "/content/challenge-2012/1.0.0/",
        "row_basename": "row0-physionet-root-v1",
    },
    {
        "ordinal": 1,
        "operation_id": "SB2-PUBLIC-ROOT-UCI-001",
        "domain": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
        "host": "archive.ics.uci.edu",
        "path": "/dataset/502/online+retail+ii",
        "row_basename": "row1-uci-online-retail-ii-root-v1",
    },
)
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
DIR_OPEN_FLAGS = os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW


class ValidationError(RuntimeError):
    """A stopped closure invariant is not exact."""


def _fail(message: str) -> None:
    raise ValidationError(message)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in out:
            _fail("duplicate or non-string JSON key")
        out[key] = value
    return out


def _canonical(value: Mapping[str, Any]) -> bytes:
    try:
        return (
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
        )
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ValidationError("value is not canonical JSON data") from exc


def _self_digest(value: Mapping[str, Any]) -> str:
    clone = dict(value)
    clone["record_sha256"] = None
    return _sha256(_canonical(clone))


def _open_absolute_componentwise(path: str, final_flags: int) -> int:
    if (
        type(path) is not str
        or not path.startswith("/")
        or path == "/"
        or "\x00" in path
        or "//" in path
        or path.endswith("/")
        or os.path.normpath(path) != path
    ):
        _fail("validator path is not exact normalized absolute")
    components = path.split("/")[1:]
    if not components or any(part in {"", ".", ".."} for part in components):
        _fail("validator path component is unsafe")
    dirfd = os.open("/", DIR_OPEN_FLAGS)
    try:
        for component in components[:-1]:
            nextfd = os.open(component, DIR_OPEN_FLAGS, dir_fd=dirfd)
            os.close(dirfd)
            dirfd = nextfd
        return os.open(components[-1], final_flags | O_NOFOLLOW, dir_fd=dirfd)
    finally:
        os.close(dirfd)


def _read_absolute_regular(path: str, cap: int = 1_048_576) -> tuple[bytes, os.stat_result]:
    fd = _open_absolute_componentwise(path, os.O_RDONLY)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            _fail("validator input is not regular nlink-one")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(131_072, cap + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > cap:
                _fail("validator input exceeds byte ceiling")
        after = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
            before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size,
                                    after.st_mtime_ns, after.st_ctime_ns):
            _fail("validator input changed while read")
        return b"".join(chunks), before
    finally:
        os.close(fd)


def _read_machine(path: Path) -> tuple[dict[str, Any], bytes]:
    raw, _st = _read_absolute_regular(str(path.absolute()))
    if len(raw) > 1_000_000 or not raw.endswith(b"\n"):
        _fail("machine byte framing invalid")
    try:
        value = json.loads(raw, object_pairs_hook=_strict_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValidationError("machine JSON invalid") from exc
    if type(value) is not dict or set(value) != EXPECTED_TOP_KEYS:
        _fail("machine exact top-level keys invalid")
    if _canonical(value) != raw:
        _fail("machine is not canonical JSON")
    if value.get("schema_version") != SCHEMA or value.get("state") != STATE:
        _fail("machine schema/state mismatch")
    if value.get("record_sha256") != _self_digest(value):
        _fail("machine self digest mismatch")
    return value, raw


def _regular_receipt(root: Path, relative: str, *, include_mtime: bool) -> dict[str, Any]:
    if (
        type(relative) is not str
        or relative.startswith("/")
        or "\x00" in relative
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    ):
        _fail("unsafe binding path")
    path = os.path.join(str(root.absolute()), relative)
    raw, st = _read_absolute_regular(path)
    receipt = {
        "path": relative,
        "bytes": len(raw),
        "sha256": _sha256(raw),
        "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}",
        "nlink": st.st_nlink,
    }
    if include_mtime:
        receipt["mtime_ns"] = st.st_mtime_ns
    return receipt


def _validate_binding_roster(
    root: Path,
    bindings: Any,
    expected_paths: set[str],
    *,
    include_mtime: bool,
) -> None:
    if type(bindings) is not list or len(bindings) != len(expected_paths):
        _fail("binding roster count invalid")
    if any(type(item) is not dict for item in bindings):
        _fail("binding roster entry invalid")
    paths = [item.get("path") for item in bindings]
    if len(paths) != len(set(paths)) or set(paths) != expected_paths:
        _fail("binding path roster invalid")
    for item in bindings:
        if item != _regular_receipt(root, item["path"], include_mtime=include_mtime):
            _fail(f"binding receipt mismatch: {item['path']}")


def _validate_v1_predecessor(root: Path, machine: Mapping[str, Any]) -> None:
    expected_paths = set(V1_PREDECESSOR)
    bindings = machine.get("direct_v1_predecessor_bindings")
    _validate_binding_roster(root, bindings, expected_paths, include_mtime=False)
    for item in bindings:
        size, digest = V1_PREDECESSOR[item["path"]]
        if item["bytes"] != size or item["sha256"] != digest:
            _fail("direct v1 predecessor literal receipt mismatch")


def _root_identity(path: str) -> dict[str, Any]:
    st = os.stat(path, follow_symlinks=False)
    if not stat.S_ISDIR(st.st_mode):
        _fail("custody root is not a directory")
    return {
        "absolute_path": path,
        "device": st.st_dev,
        "inode": st.st_ino,
        "uid": st.st_uid,
        "gid": st.st_gid,
        "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}",
    }


def _validate_v2_root(machine: Mapping[str, Any]) -> None:
    if machine.get("operational_custody_root") != V2_ROOT_IDENTITY:
        _fail("v2 root machine identity mismatch")
    if _root_identity(V2_ROOT) != {
        key: value for key, value in V2_ROOT_IDENTITY.items()
        if key not in {"nlink_at_package_construction", "empty_at_package_construction", "row_directories_present"}
    }:
        _fail("v2 root live identity mismatch")
    st = os.stat(V2_ROOT, follow_symlinks=False)
    if st.st_nlink != 2 or os.listdir(V2_ROOT) != []:
        _fail("v2 operational root is not exact empty construction root")


def _read_incident_record(path: Path) -> tuple[str, str]:
    raw, _st = _read_absolute_regular(str(path.absolute()))
    try:
        value = json.loads(raw, object_pairs_hook=_strict_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValidationError("v1 incident receipt invalid") from exc
    if type(value) is not dict or type(value.get("record_sha256")) is not str:
        _fail("v1 incident receipt record digest absent")
    return _sha256(raw), value["record_sha256"]


def _validate_v1_incident(machine: Mapping[str, Any]) -> None:
    incident = machine.get("v1_pre_reservation_incident")
    if type(incident) is not dict:
        _fail("v1 incident projection absent")
    exact_scalars = {
        "custody_root": V1_ROOT_IDENTITY,
        "gate_receipts": V1_GATE_RECEIPTS,
        "exact_root_roster": sorted(V1_GATE_RECEIPTS),
        "row_basename": "row0-physionet-root-v1",
        "row_directory_absent": True,
        "intent_absent": True,
        "launcher_exit_code": 1,
        "launcher_elapsed_seconds_approximate": 9.37,
        "launcher_time_externally_attested": False,
        "first_failing_gate": "FULL_RUNTIME_MANIFEST_EQUALITY_BEFORE_ROW_RESERVATION",
        "admitted_and_current_canonical_manifest_projections_equal": True,
        "python_direct_equality_failed_only_on_mac_version_nested_tuple_list_type": True,
        "resolver_high_level_call_count": 0,
        "socket_instance_count": 0,
        "tls_wrap_call_count": 0,
        "sendall_call_count": 0,
        "http_request_count": 0,
        "durable_intent_count": 0,
        "attempt_budget_spent": False,
        "retry_of_v1_authorized": False,
        "same_uid_external_substitution_excluded": False,
    }
    if incident != exact_scalars:
        _fail("v1 incident exact projection mismatch")
    if _root_identity(V1_ROOT) != V1_ROOT_IDENTITY:
        _fail("v1 root live identity mismatch")
    names = sorted(os.listdir(V1_ROOT))
    if names != sorted(V1_GATE_RECEIPTS):
        _fail("v1 incident root exact roster mismatch")
    if os.path.lexists(os.path.join(V1_ROOT, "row0-physionet-root-v1")):
        _fail("v1 row directory unexpectedly present")
    for name, expected in V1_GATE_RECEIPTS.items():
        raw_digest, record_digest = _read_incident_record(Path(V1_ROOT) / name)
        if {"raw_sha256": raw_digest, "record_sha256": record_digest} != expected:
            _fail(f"v1 incident receipt drift: {name}")


def _validate_operations(machine: Mapping[str, Any]) -> None:
    rows = machine.get("operation_roster")
    if type(rows) is not list or len(rows) != 2:
        _fail("operation roster count invalid")
    for ordinal, (row, exact, request) in enumerate(zip(rows, EXPECTED_OPERATIONS, REQUESTS)):
        if type(row) is not dict:
            _fail("operation row is not exact object")
        exact_keys = {
            "ordinal", "operation_id", "domain", "url", "host", "path", "row_basename",
            "method", "request_bytes", "request_sha256", "request_base64",
            "attempt_limit", "retry_limit", "redirect_limit", "fetch_eligible",
        }
        if set(row) != exact_keys:
            _fail("operation exact key roster mismatch")
        projection = {key: row.get(key) for key in exact}
        if projection != exact or any(type(projection[k]) is not type(exact[k]) for k in exact):
            _fail("operation identity mismatch")
        if any(type(row[key]) is not int for key in (
            "ordinal", "request_bytes", "attempt_limit", "retry_limit", "redirect_limit"
        )):
            _fail("operation integer leaf type mismatch")
        if any(type(row[key]) is not str for key in (
            "operation_id", "domain", "url", "host", "path", "row_basename", "method",
            "request_sha256", "request_base64",
        )) or type(row["fetch_eligible"]) is not bool:
            _fail("operation scalar leaf type mismatch")
        if (
            row.get("method") != "GET"
            or row.get("request_bytes") != len(request)
            or row.get("request_sha256") != _sha256(request)
            or row.get("request_base64") != base64.b64encode(request).decode("ascii")
            or row.get("attempt_limit") != 1
            or row.get("retry_limit") != 0
            or row.get("redirect_limit") != 0
            or row.get("fetch_eligible") is not False
            or row.get("ordinal") != ordinal
        ):
            _fail("operation request or 1/0/0 contract mismatch")


def _validate_contracts(machine: Mapping[str, Any]) -> None:
    runtime = machine.get("runtime_manifest_contract")
    required_runtime = {
        "schema_version": "heterodiff-solo-block2-loaded-runtime-manifest-v2",
        "full_manifest_exact_no_stable_volatile_carveout": True,
        "mac_version_json_native_leaf_required": True,
        "mac_version_shape": "[EXACT_STRING,LIST_OF_EXACT_STRING,EXACT_STRING]",
        "canonical_json_equality_accepts_historical_tuple_list_round_trip": True,
        "recursive_non_mac_version_tuple_prohibition_claimed": False,
        "canonical_bytes_equality_required_immediately_before_reservation": True,
        "manifest_digest_equality_required_immediately_before_reservation": True,
        "v1_false_hold_leaf": "mac_version[1]:TUPLE_VS_JSON_LIST",
        "real_nested_drift_disposition": "HOLD_BEFORE_ROW_RESERVATION",
        "operational_receipt_key_rosters": runtime.get("operational_receipt_key_rosters"),
        "sidecar_basenames": runtime.get("sidecar_basenames"),
        "dyld_arm64e_cache_paths": runtime.get("dyld_arm64e_cache_paths"),
        "exact_launcher_prefix": runtime.get("exact_launcher_prefix"),
        "python_flags_exact": runtime.get("python_flags_exact"),
    }
    if runtime != required_runtime:
        _fail("runtime manifest round-trip contract mismatch")
    executor = machine.get("executor_contract")
    required_executor = {
        "production_commands": EXPECTED_COMMANDS,
        "general_url_or_request_input_present": False,
        "network_calls_reachable_in_stopped_state": False,
        "qualification_network_permitted": False,
        "resolver_high_level_call_limit": 1,
        "socket_connect_limit": 1,
        "plaintext_https_get_send_limit": 1,
        "application_retry_limit": 0,
        "redirect_limit": 0,
        "response_protocol_framing_precedes_scope_status_size_content": True,
        "oversized_duplicate_content_length_terminal": "PROTOCOL_VIOLATION",
        "oversized_location_terminal": "SCOPE_VIOLATION",
        "row1_uses_synthetic_row0_context": False,
        "row1_requires_actual_custody_requalified_parent_context": True,
        "resolver_socket_tls_send_unreachable_before_durable_intent": True,
        "preintent_partial_reservation_is_terminal_no_retry": True,
        "concurrent_same_uid_path_substitution_excluded": False,
        "executing_image_one_open_attestation_claimed": False,
        "registrar_identity_externally_authenticated": False,
        "registrar_time_externally_attested": False,
        "registrar_identity_and_time_are_caller_assertions": True,
    }
    if executor != required_executor:
        _fail("executor contract mismatch")
    qualification = machine.get("qualification_contract")
    if qualification != {
        "bytecode_cache_disabled_required": True,
        "pytest_cache_disabled_required": True,
        "external_network_permitted": False,
        "loopback_permitted": False,
        "operational_root_write_permitted": False,
        "operational_receipt_or_intent_materialization_permitted": False,
        "qualification_can_spend_attempt_or_verify_official_fact": False,
    }:
        _fail("qualification contract mismatch")


def _validate_null_effects(machine: Mapping[str, Any]) -> None:
    slots = machine.get("current_operational_slots")
    if type(slots) is not dict or set(slots) != {
        "package_lock",
        "preflight_authority",
        "runtime_preflight",
        "row0_independent_go",
        "row0_authority",
        "row0_intent",
        "row0_outcome",
        "row1_independent_go",
        "row1_authority",
        "row1_intent",
        "row1_outcome",
    } or any(value is not None for value in slots.values()):
        _fail("v2 operational slots are not exact null")
    if machine.get("checklist_effects") != {
        "v1_bytes_modified": False,
        "v1_custody_modified": False,
        "v1_attempt_budget_spent": False,
        "v2_fetch_performed": False,
        "v2_resolver_call_performed": False,
        "v2_socket_created": False,
        "v2_durable_row_intent_created": False,
        "v2_operational_receipt_created": False,
        "tracker_edited": False,
        "data_accessed": False,
        "scientific_delta": "ZERO",
    }:
        _fail("checklist effect roster mismatch")


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    _fail(f"executor function absent: {name}")
    raise AssertionError


def _assignment_literal(tree: ast.Module, name: str) -> Any:
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            try:
                return ast.literal_eval(node.value)
            except (ValueError, TypeError) as exc:
                raise ValidationError(f"executor literal is not static: {name}") from exc
    _fail(f"executor literal absent: {name}")
    raise AssertionError


def _validate_transport_call_placement(tree: ast.Module) -> None:
    expected = {
        "socket.getaddrinfo": ("_bounded_single_getaddrinfo", 1),
        "socket.socket": ("_perform_spent_attempt", 1),
        "raw_socket.connect": ("_perform_spent_attempt", 1),
        "ssl.SSLContext": ("_perform_spent_attempt", 1),
        "context.wrap_socket": ("_perform_spent_attempt", 1),
        "tls.sendall": ("_perform_spent_attempt", 1),
        "os.fork": ("_bounded_single_getaddrinfo", 1),
        "subprocess.run": ("_capture_scutil_dns", 1),
    }
    found = {name: [] for name in expected}
    for parent in ast.walk(tree):
        if not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(parent):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not parent:
                continue
            if isinstance(node, ast.Call):
                name = _dotted(node.func)
                if name in found:
                    found[name].append(parent.name)
    for name, (owner, count) in expected.items():
        if found[name] != [owner] * count:
            _fail(f"executor operational call placement mismatch: {name}")


def _validate_executor_source(root: Path, machine: Mapping[str, Any]) -> None:
    source_path = root / EXECUTOR_RELATIVE
    raw, _st = _read_absolute_regular(str(source_path.absolute()))
    binding = machine.get("executor_source_binding")
    expected = next(
        item for item in machine["package_bindings"] if item["path"] == EXECUTOR_RELATIVE
    )
    if binding != {"path": EXECUTOR_RELATIVE, "bytes": len(raw), "sha256": _sha256(raw)}:
        _fail("executor source binding mismatch")
    if expected["bytes"] != len(raw) or expected["sha256"] != _sha256(raw):
        _fail("executor package/source binding disagreement")
    try:
        tree = ast.parse(raw.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as exc:
        raise ValidationError("executor source invalid") from exc
    text = raw.decode("utf-8")
    required_literals = (
        "heterodiff-solo-block2-runtime-custody-executor-v2",
        "manuscript_v3_solo_block2_runtime_custody_closure_v2.json",
        "def _normalized_mac_version",
        "_canonical_bytes(admitted)",
    )
    for literal in required_literals:
        if literal not in text:
            _fail(f"executor source missing v2 literal: {literal}")
    if "solo_block2_public_documentation_runtime_v1" in text:
        _fail("v2 executor source contains v1 operational root")
    calls = [_dotted(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    for name, count in {
        "socket.getaddrinfo": 1, "socket.socket": 1, "ssl.SSLContext": 1,
        "os.fork": 1, "subprocess.run": 1, "tls.sendall": 1,
        "compile": 1, "exec": 1,
    }.items():
        if calls.count(name) != count:
            _fail(f"executor operational call count mismatch: {name}")
    _validate_transport_call_placement(tree)
    if set(calls) & {"os.remove", "os.unlink", "os.rename", "os.replace",
                     "shutil.rmtree", "urllib.request.urlopen", "requests.get",
                     "requests.post", "eval"}:
        _fail("executor exposes destructive/dynamic/general-network call")
    signatures = {
        "preflight": ["custody_root"], "attempt": ["custody_root", "row"],
        "register_package_lock": ["custody_root", "independent_reviewer_principal", "created_unix_ns"],
        "register_preflight_authority": ["custody_root", "created_unix_ns", "normalized_visible_text"],
        "register_independent_go": ["custody_root", "row", "independent_reviewer_principal", "created_unix_ns"],
        "register_row_authority": ["custody_root", "row", "created_unix_ns", "expires_unix_ns", "normalized_visible_text"],
    }
    for name, signature in signatures.items():
        if [arg.arg for arg in _function_node(tree, name).args.args] != signature:
            _fail(f"production command surface mismatch: {name}")
    loader_text = ast.get_source_segment(text, _function_node(tree, "_ensure_parent_parser")) or ""
    if ("_read_regular_path_nofollow" not in loader_text or "compile(raw" not in loader_text
            or "exec(code" not in loader_text or "spec_from_file_location" in text
            or "exec_module" in text or ".proposal.json" in text):
        _fail("raw parent parser loader drift")
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            seen: set[Any] = set()
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, (str, int, float, bytes)):
                    if key.value in seen:
                        _fail(f"duplicate literal dictionary key at line {node.lineno}")
                    seen.add(key.value)
    runtime = machine["runtime_manifest_contract"]
    for name in ("PACKAGE_LOCK_KEYS", "PREFLIGHT_AUTHORITY_KEYS", "RUNTIME_PREFLIGHT_KEYS",
                 "INDEPENDENT_GO_KEYS", "ROW_AUTHORITY_KEYS", "INTENT_KEYS", "OUTCOME_KEYS"):
        if runtime["operational_receipt_key_rosters"].get(name) != list(_assignment_literal(tree, name)):
            _fail(f"machine/source receipt-key roster mismatch: {name}")
    if runtime["sidecar_basenames"] != list(_assignment_literal(tree, "SIDECAR_BASENAMES")):
        _fail("machine/source sidecar roster mismatch")
    if runtime["dyld_arm64e_cache_paths"] != list(_assignment_literal(tree, "DYLD_CACHE_PATHS")):
        _fail("machine/source dyld roster mismatch")
    launcher = runtime["exact_launcher_prefix"]
    if (type(launcher) is not list or len(launcher) != 7
            or launcher[2] != _assignment_literal(tree, "EXPECTED_INTERPRETER")
            or launcher[-1] != str(source_path)):
        _fail("machine/source launcher mismatch")
    if runtime["python_flags_exact"] != _assignment_literal(tree, "EXPECTED_PYTHON_FLAGS"):
        _fail("machine/source Python flags mismatch")
    guard_text = ast.get_source_segment(text, _function_node(tree, "_require_production_process")) or ""
    manifest_text = ast.get_source_segment(text, _function_node(tree, "_runtime_manifest")) or ""
    if ("sys.orig_argv != expected_original_argv" not in guard_text
            or "_require_exact_python_runtime_flags()" not in guard_text
            or "_require_exact_python_runtime_flags()" not in manifest_text):
        _fail("production argv/Python flag guards absent")
    normalized = ast.get_source_segment(text, _function_node(tree, "_normalized_mac_version")) or ""
    if "return [version, list(release), machine]" not in normalized:
        _fail("mac_version JSON normalization drift")
    revalidate = ast.get_source_segment(text, _function_node(tree, "_revalidate_runtime_immediately_before_reservation")) or ""
    if ("_canonical_bytes(admitted) != _canonical_bytes(" not in revalidate
            or 'current["manifest_sha256"]' not in revalidate):
        _fail("pre-reservation canonical/digest revalidation drift")
    attempt_text = ast.get_source_segment(text, _function_node(tree, "attempt")) or ""
    tokens = ["_revalidate_runtime_immediately_before_reservation(", "_mkdir_row(",
              '_exclusive_canonical_at(rowfd, "intent.json", intent)', "_perform_spent_attempt("]
    if any(token not in attempt_text for token in tokens):
        _fail("attempt ordering marker absent")
    if not (attempt_text.index(tokens[0]) < attempt_text.index(tokens[1]) <
            attempt_text.index(tokens[2]) < attempt_text.index(tokens[3])):
        _fail("pre-reservation/intent/network ordering invalid")
    if '_reopen_exact_digest_at(rowfd, "intent.json", intent_digest)' not in attempt_text:
        _fail("durable intent is not reopened before network")
    for token in ("row directory already exists; attempt cannot start or retry",
                  "_validate_row0_success_for_row1", "row0_context_after_intent",
                  "row0_context_after_attempt", "else (row0_context[1], row0_context[2])"):
        if token not in attempt_text:
            _fail("poison or actual row0 contextual gate drift")
    if _assignment_literal(tree, "_REQUEST_0") != REQUESTS[0] or _assignment_literal(tree, "_REQUEST_1") != REQUESTS[1]:
        _fail("executor exact request bytes drift")


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    machine, _raw = _read_machine(root / MACHINE_RELATIVE)
    _validate_v1_predecessor(root, machine)
    _validate_binding_roster(
        root,
        machine.get("package_bindings"),
        V2_PACKAGE_PATHS,
        include_mtime=True,
    )
    _validate_v2_root(machine)
    _validate_v1_incident(machine)
    _validate_operations(machine)
    _validate_contracts(machine)
    _validate_null_effects(machine)
    _validate_executor_source(root, machine)
    if machine.get("reported_date") != "2026-08-31" or machine.get(
        "package_kind"
    ) != "ADDITIVE_V2_RUNTIME_CUSTODY_FALSE_HOLD_REPAIR":
        _fail("package metadata mismatch")
    return {
        "status": "PASS",
        "state": STATE,
        "operation_count": 2,
        "v1_gate_receipt_count": 5,
        "v1_attempt_budget_spent": False,
        "v2_operational_root_entries": 0,
        "v2_fetches_performed": 0,
        "v2_durable_intents_created": 0,
        "scientific_delta": "ZERO",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate(args.root)
    except (ValidationError, OSError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
