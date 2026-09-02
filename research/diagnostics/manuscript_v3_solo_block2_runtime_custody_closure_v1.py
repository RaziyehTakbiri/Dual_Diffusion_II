#!/usr/bin/env python3
"""Read-only validator for the Solo Block 2 runtime/custody closure v1."""

from __future__ import annotations

import ast
import base64
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA = "heterodiff-manuscript-v3-solo-block2-runtime-custody-closure-v1"
STATE = "FINAL_EXECUTOR_QUALIFIED_OPERATIONAL_RECEIPTS_NULL_FETCH_HOLD"
EXPECTED_AUTHORITY = "Alright, go through it then. I am overseeing you to the end."
EXPECTED_AUTHORITY_SHA256 = (
    "2e8560c4586f620abe2f276793c09a49e0008aaed86ba2b4a112a01565ae50fb"
)
EXPECTED_ROOT = (
    "/Users/mahtab/.codex/.chatgpt-projects/"
    "g-p-6a5f91c1e79c819183983ba0010bb151/"
    "research/custody/solo_block2_public_documentation_runtime_v1"
)
EXPECTED_ROOT_IDENTITY = {
    "absolute_path": EXPECTED_ROOT,
    "device": 16777234,
    "inode": 66899471,
    "uid": 501,
    "gid": 20,
    "mode_octal": "0700",
    "nlink_at_package_construction": 2,
    "empty_at_package_construction": True,
    "row_directories_present": False,
}
EXPECTED_OPERATIONS = (
    {
        "ordinal": 0,
        "operation_id": "SB2-PUBLIC-ROOT-PHYSIONET-000",
        "domain": "PhysioNet",
        "host": "physionet.org",
        "path": "/content/challenge-2012/1.0.0/",
        "url": "https://physionet.org/content/challenge-2012/1.0.0/",
        "row_basename": "row0-physionet-root-v1",
        "request": (
            b"GET /content/challenge-2012/1.0.0/ HTTP/1.1\r\n"
            b"Host: physionet.org\r\n"
            b"User-Agent: heterodiff-precontact-public-doc-recon-v2/2.0\r\n"
            b"Accept: text/html, application/xhtml+xml;q=0.9, text/plain;q=0.8\r\n"
            b"Accept-Encoding: identity\r\n"
            b"Cache-Control: no-cache\r\n"
            b"Pragma: no-cache\r\n"
            b"Connection: close\r\n\r\n"
        ),
    },
    {
        "ordinal": 1,
        "operation_id": "SB2-PUBLIC-ROOT-UCI-001",
        "domain": "UCI Online Retail II",
        "host": "archive.ics.uci.edu",
        "path": "/dataset/502/online+retail+ii",
        "url": "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
        "row_basename": "row1-uci-online-retail-ii-root-v1",
        "request": (
            b"GET /dataset/502/online+retail+ii HTTP/1.1\r\n"
            b"Host: archive.ics.uci.edu\r\n"
            b"User-Agent: heterodiff-precontact-public-doc-recon-v2/2.0\r\n"
            b"Accept: text/html, application/xhtml+xml;q=0.9, text/plain;q=0.8\r\n"
            b"Accept-Encoding: identity\r\n"
            b"Cache-Control: no-cache\r\n"
            b"Pragma: no-cache\r\n"
            b"Connection: close\r\n\r\n"
        ),
    },
)
EXPECTED_TOP_KEYS = {
    "authority_provenance",
    "checklist_effects",
    "current_operational_slots",
    "executor_contract",
    "executor_source_binding",
    "immutable_predecessor_bindings",
    "operation_roster",
    "operational_custody_root",
    "package_bindings",
    "package_kind",
    "qualification_contract",
    "record_sha256",
    "reported_date",
    "runtime_contract",
    "schema_version",
    "state",
}
EXPECTED_PACKAGE_PATHS = {
    "PROJECT_SOLO_BLOCK2_RUNTIME_CUSTODY_CLOSURE.md",
    "research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v1.py",
    "tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v1.py",
    "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v1.py",
    "tests/unit/test_solo_block2_runtime_custody_executor_v1.py",
}
EXPECTED_PREDECESSOR_PATHS = {
    "PROJECT_SOLO_BLOCK2_PUBLIC_DOCUMENTATION_RECONNAISSANCE_AMENDMENT.md",
    "research/fixtures/manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.json",
    "research/diagnostics/manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.py",
    "tests/unit/test_manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.py",
    "src/heterodiff/artifacts/solo_block2_public_documentation_reconnaissance_executor_v2.py",
    "tests/unit/test_solo_block2_public_documentation_reconnaissance_executor_v2.py",
}
EXPECTED_PRODUCTION_COMMANDS = [
    "register-package-lock ROOT REVIEWER CREATED_UNIX_NS",
    "register-preflight-authority ROOT CREATED_UNIX_NS EXACT_TEXT",
    "preflight ROOT",
    "register-independent-go ROOT ROW REVIEWER CREATED_UNIX_NS",
    "register-row-authority ROOT ROW CREATED_UNIX_NS EXPIRES_UNIX_NS EXACT_TEXT",
    "attempt ROOT ROW",
]
EXPECTED_EXECUTOR_CONTRACT = {
    "all_package_runtime_go_authority_sequence_and_custody_gates_precede_resolver_socket": True,
    "application_retry_limit": 0,
    "concurrent_same_uid_path_substitution_excluded": False,
    "directory_link_count_bounded_by_live_entry_roster": True,
    "durable_intent_reopened_before_resolver": True,
    "executing_image_one_open_attestation_claimed": False,
    "final_production_executor_surface_frozen": True,
    "general_url_or_request_input_present": False,
    "global_address_only_first_returned_no_fallback": True,
    "hostname_and_sni_verification_required": True,
    "network_calls_reachable_in_stopped_state": False,
    "network_or_operational_execution_performed_in_qualification": False,
    "oversized_response_uses_accepted_parser_precedence": True,
    "plaintext_https_get_send_limit": 1,
    "preintent_partial_reservation_terminal": (
        "TERMINAL_ABANDONED_PREINTENT_RESERVATION_NO_REQUEST_NO_RETRY"
    ),
    "production_commands": EXPECTED_PRODUCTION_COMMANDS,
    "production_entrypoint_has_injected_seam": False,
    "redirect_limit": 0,
    "registrar_identity_and_time_are_caller_assertions": True,
    "registrar_identity_externally_authenticated": False,
    "registrar_time_externally_attested": False,
    "resolver_child_absolute_monotonic_wait_seconds": 12.0,
    "resolver_high_level_call_limit": 1,
    "resolver_packet_wire_ttl_cache_server_determinism_claimed": False,
    "row1_requires_actual_custody_requalified_parent_context": True,
    "row1_requires_recursive_row0_intent_outcome_sidecar_requalification": True,
    "row1_synthetic_prior_present": False,
    "socket_connect_limit": 1,
    "tcp_retransmission_tls_record_and_os_scheduling_bound": False,
    "tls_alpn_exact": "http/1.1",
    "tls_maximum": "TLSv1_3",
    "tls_minimum": "TLSv1_2",
    "tls_session_resumption_and_client_certificate_permitted": False,
    "transcript_or_fake_transport_production_input_present": False,
}
EXPECTED_QUALIFICATION_CONTRACT = {
    "bytecode_cache_disabled_required": True,
    "executor_hostile_test_minimum_count": 59,
    "external_network_permitted": False,
    "loopback_permitted": False,
    "operational_receipt_or_intent_materialization_permitted": False,
    "operational_root_write_permitted": False,
    "pytest_cache_disabled_required": True,
    "qualification_can_close_operational_box_or_verify_fact": False,
    "transcript_inputs_are_inert_bytes_only": True,
    "validator_hostile_test_minimum_count": 23,
}
EXPECTED_RUNTIME_CONTRACT_KEYS = {
    "ca_path",
    "ca_sha256",
    "concurrent_same_uid_path_substitution_excluded",
    "current_fetch_eligible",
    "current_runtime_preflight_admitted",
    "current_systemconfiguration_snapshot",
    "current_systemconfiguration_snapshot_receipt",
    "dyld_arm64e_cache_paths",
    "environment_exact",
    "exact_launcher_prefix",
    "interpreter_sha256",
    "openssl_version",
    "operational_receipt_key_rosters",
    "python_flags_exact",
    "python_version",
    "registrar_identity_and_time_are_caller_assertions",
    "resolver_unavailable_disposition",
    "runtime_drift_disposition",
    "runtime_preflight_materialized",
    "sidecar_basenames",
    "source_and_interpreter_receipts_are_post_load",
}
FORWARD_ROOT_PREFIX = (
    "package-lock.json",
    "preflight-authority.json",
    "runtime-preflight.json",
    "row0-independent-go.json",
    "row0-authority.json",
    "row0-physionet-root-v1",
    "row1-independent-go.json",
    "row1-authority.json",
    "row1-uci-online-retail-ii-root-v1",
)
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
DIR_OPEN_FLAGS = os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW
READ_FLAGS = os.O_RDONLY | O_NOFOLLOW


class ValidationError(RuntimeError):
    pass


def _fail(message: str) -> None:
    raise ValidationError(message)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            _fail(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def _canonical(value: Mapping[str, Any]) -> bytes:
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
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            _fail("validator input changed while read")
        return b"".join(chunks), before
    finally:
        os.close(fd)


def _read_machine(path: Path) -> tuple[dict[str, Any], bytes]:
    raw, _st = _read_absolute_regular(str(path.absolute()))
    if len(raw) > 1_048_576 or not raw:
        _fail("machine size invalid")
    try:
        value = json.loads(raw, object_pairs_hook=_strict_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise ValidationError("machine JSON invalid") from exc
    if type(value) is not dict:
        _fail("machine top level is not an object")
    if raw != _canonical(value):
        _fail("machine is not canonical JSON plus LF")
    if set(value) != EXPECTED_TOP_KEYS:
        _fail("machine top-level key roster mismatch")
    if value.get("schema_version") != SCHEMA or value.get("state") != STATE:
        _fail("machine schema/state mismatch")
    digest = value.get("record_sha256")
    if type(digest) is not str or not re.fullmatch(r"[0-9a-f]{64}", digest):
        _fail("machine self digest malformed")
    if digest != _self_digest(value):
        _fail("machine self digest mismatch")
    return value, raw


def _regular_receipt(root: Path, relative: str) -> dict[str, Any]:
    if relative.startswith("/") or ".." in relative.split("/") or "\x00" in relative:
        _fail(f"unsafe bound path: {relative}")
    path = os.path.join(str(root.absolute()), relative)
    raw, st0 = _read_absolute_regular(path)
    return {
        "path": relative,
        "sha256": _sha256(raw),
        "bytes": len(raw),
        "mode_octal": f"{stat.S_IMODE(st0.st_mode):04o}",
        "nlink": st0.st_nlink,
        "mtime_ns": st0.st_mtime_ns,
    }


def _validate_bindings(
    root: Path,
    bindings: Any,
    expected_paths: set[str],
    *,
    include_mtime: bool,
) -> None:
    if type(bindings) is not list or len(bindings) != len(expected_paths):
        _fail("binding count mismatch")
    seen: set[str] = set()
    for item in bindings:
        if type(item) is not dict:
            _fail("binding is not an object")
        expected_keys = {"path", "sha256", "bytes", "mode_octal", "nlink"}
        if include_mtime:
            expected_keys.add("mtime_ns")
        if set(item) != expected_keys:
            _fail("binding key roster mismatch")
        path = item.get("path")
        if type(path) is not str or path in seen:
            _fail("binding path type/duplication invalid")
        seen.add(path)
        actual = _regular_receipt(root, path)
        if not include_mtime:
            actual.pop("mtime_ns")
        if item != actual:
            _fail(f"binding receipt mismatch: {path}")
    if seen != expected_paths:
        _fail("binding path closure mismatch")


def _validate_authority(machine: Mapping[str, Any]) -> None:
    value = machine["authority_provenance"]
    required = {
        "source",
        "normalized_visible_text",
        "normalized_visible_text_utf8_bytes",
        "normalized_visible_text_sha256",
        "normalization",
        "package_construction_review_qualification_authorized",
        "empty_custody_root_preparation_authorized",
        "package_lock_materialization_authorized",
        "runtime_preflight_materialization_authorized",
        "dns_or_https_authorized",
        "tls_transport_entropy_authorized",
        "contact_authentication_download_or_data_authorized",
        "scientific_entropy_or_execution_authorized",
        "tracker_edit_authorized",
        "raw_transport_or_account_identity_bound",
    }
    if type(value) is not dict or set(value) != required:
        _fail("authority schema mismatch")
    if value["normalized_visible_text"] != EXPECTED_AUTHORITY:
        _fail("authority exact text mismatch")
    raw = EXPECTED_AUTHORITY.encode("utf-8")
    if len(raw) != 60 or value["normalized_visible_text_utf8_bytes"] != 60:
        _fail("authority UTF-8 byte count mismatch")
    if _sha256(raw) != EXPECTED_AUTHORITY_SHA256:
        _fail("validator authority fixture inconsistent")
    if value["normalized_visible_text_sha256"] != EXPECTED_AUTHORITY_SHA256:
        _fail("authority digest mismatch")
    if value["package_construction_review_qualification_authorized"] is not True:
        _fail("package construction authority absent")
    if value["empty_custody_root_preparation_authorized"] is not True:
        _fail("custody root preparation authority absent")
    false_fields = required - {
        "source",
        "normalized_visible_text",
        "normalized_visible_text_utf8_bytes",
        "normalized_visible_text_sha256",
        "normalization",
        "package_construction_review_qualification_authorized",
        "empty_custody_root_preparation_authorized",
    }
    if any(value[key] is not False for key in false_fields):
        _fail("authority broadened beyond build/review/root preparation")


def _validate_root(machine: Mapping[str, Any]) -> int:
    if machine["operational_custody_root"] != EXPECTED_ROOT_IDENTITY:
        _fail("operational custody root machine identity mismatch")
    rootfd = _open_absolute_componentwise(EXPECTED_ROOT, DIR_OPEN_FLAGS)
    try:
        st = os.fstat(rootfd)
        names = os.listdir(rootfd)
        if len(names) != len(set(names)):
            _fail("operational custody root contains duplicate names")
        name_set = set(names)
        admitted_sets = {
            frozenset(FORWARD_ROOT_PREFIX[:count])
            for count in range(len(FORWARD_ROOT_PREFIX) + 1)
        }
        if frozenset(name_set) not in admitted_sets:
            _fail("operational custody root is outside the forward-only prefix roster")
        row_names = {
            "row0-physionet-root-v1",
            "row1-uci-online-retail-ii-root-v1",
        }
        for name in names:
            entry = os.stat(name, dir_fd=rootfd, follow_symlinks=False)
            if name in row_names:
                if (
                    not stat.S_ISDIR(entry.st_mode)
                    or stat.S_IMODE(entry.st_mode) != 0o700
                    or entry.st_uid != st.st_uid
                    or entry.st_gid != st.st_gid
                    or entry.st_dev != st.st_dev
                    or entry.st_nlink != 2
                ):
                    _fail("forward row-directory custody identity invalid")
            elif (
                not stat.S_ISREG(entry.st_mode)
                or stat.S_IMODE(entry.st_mode) != 0o600
                or entry.st_uid != st.st_uid
                or entry.st_gid != st.st_gid
                or entry.st_dev != st.st_dev
                or entry.st_nlink != 1
            ):
                _fail("forward receipt custody identity invalid")
    finally:
        os.close(rootfd)
    actual_static = {
        "absolute_path": EXPECTED_ROOT,
        "device": st.st_dev,
        "inode": st.st_ino,
        "uid": st.st_uid,
        "gid": st.st_gid,
        "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}",
    }
    expected_static = {
        key: EXPECTED_ROOT_IDENTITY[key]
        for key in (
            "absolute_path",
            "device",
            "inode",
            "uid",
            "gid",
            "mode_octal",
        )
    }
    base_nlink = EXPECTED_ROOT_IDENTITY["nlink_at_package_construction"]
    if (
        not stat.S_ISDIR(st.st_mode)
        or actual_static != expected_static
        or st.st_nlink < base_nlink
        or st.st_nlink > base_nlink + len(name_set)
    ):
        _fail("operational custody root live identity mismatch")
    return len(name_set)


def _validate_operations(machine: Mapping[str, Any]) -> None:
    roster = machine["operation_roster"]
    if type(roster) is not list or len(roster) != 2:
        _fail("operation roster not exact two rows")
    for actual, expected in zip(roster, EXPECTED_OPERATIONS):
        if type(actual) is not dict or set(actual) != {
            "ordinal",
            "operation_id",
            "domain",
            "host",
            "path",
            "url",
            "row_basename",
            "request_base64",
            "request_bytes",
            "request_sha256",
            "method",
            "attempt_limit",
            "retry_limit",
            "redirect_limit",
            "fetch_eligible",
        }:
            _fail("operation row schema mismatch")
        for key in ("ordinal", "operation_id", "domain", "host", "path", "url", "row_basename"):
            if actual[key] != expected[key] or type(actual[key]) is not type(expected[key]):
                _fail(f"operation {expected['ordinal']} mismatch: {key}")
        request = expected["request"]
        if base64.b64decode(actual["request_base64"], validate=True) != request:
            _fail("operation request base64 mismatch")
        if actual["request_bytes"] != len(request) or actual["request_sha256"] != _sha256(request):
            _fail("operation request receipt mismatch")
        if actual["method"] != "GET" or actual["attempt_limit"] != 1:
            _fail("operation method/attempt mismatch")
        if actual["retry_limit"] != 0 or actual["redirect_limit"] != 0:
            _fail("operation retry/redirect broadened")
        if actual["fetch_eligible"] is not False:
            _fail("stopped operation falsely eligible")


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
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
        ):
            try:
                return ast.literal_eval(node.value)
            except (ValueError, TypeError) as exc:
                raise ValidationError(f"executor literal is not static: {name}") from exc
    _fail(f"executor literal absent: {name}")
    raise AssertionError


def _validate_executor_ast(root: Path, machine: Mapping[str, Any]) -> None:
    relative = "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v1.py"
    source_raw, _source_st = _read_absolute_regular(
        os.path.join(str(root.absolute()), relative)
    )
    source = source_raw.decode("utf-8")
    tree = ast.parse(source)
    binding = machine["executor_source_binding"]
    receipt = _regular_receipt(root, relative)
    if type(binding) is not dict or set(binding) != {"path", "sha256", "bytes"}:
        _fail("executor source binding schema mismatch")
    if binding != {key: receipt[key] for key in ("path", "sha256", "bytes")}:
        _fail("executor source binding mismatch")
    calls = [_dotted(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    required_counts = {
        "socket.getaddrinfo": 1,
        "socket.socket": 1,
        "ssl.SSLContext": 1,
        "os.fork": 1,
        "subprocess.run": 1,
        "tls.sendall": 1,
        "compile": 1,
        "exec": 1,
    }
    for name, count in required_counts.items():
        if calls.count(name) != count:
            _fail(f"executor operational call count mismatch: {name}")
    forbidden = {
        "os.remove",
        "os.unlink",
        "os.rename",
        "os.replace",
        "shutil.rmtree",
        "urllib.request.urlopen",
        "requests.get",
        "requests.post",
        "eval",
    }
    if set(calls) & forbidden:
        _fail("executor exposes destructive/dynamic/general-network call")
    preflight = _function_node(tree, "preflight")
    attempt = _function_node(tree, "attempt")
    parent_loader = _function_node(tree, "_ensure_parent_parser")
    if [arg.arg for arg in preflight.args.args] != ["custody_root"]:
        _fail("preflight production surface broadened")
    if [arg.arg for arg in attempt.args.args] != ["custody_root", "row"]:
        _fail("attempt production surface broadened")
    registrar_signatures = {
        "register_package_lock": [
            "custody_root",
            "independent_reviewer_principal",
            "created_unix_ns",
        ],
        "register_preflight_authority": [
            "custody_root",
            "created_unix_ns",
            "normalized_visible_text",
        ],
        "register_independent_go": [
            "custody_root",
            "row",
            "independent_reviewer_principal",
            "created_unix_ns",
        ],
        "register_row_authority": [
            "custody_root",
            "row",
            "created_unix_ns",
            "expires_unix_ns",
            "normalized_visible_text",
        ],
    }
    for name, signature in registrar_signatures.items():
        node = _function_node(tree, name)
        if [arg.arg for arg in node.args.args] != signature:
            _fail(f"registrar production surface mismatch: {name}")
    loader_text = ast.get_source_segment(source, parent_loader) or ""
    if (
        "_read_regular_path_nofollow" not in loader_text
        or "compile(raw" not in loader_text
        or "exec(code" not in loader_text
        or "spec_from_file_location" in source
        or "exec_module" in source
        or ".proposal.json" in source
        or "QUALIFICATION-CONTEXT-CIPHER" in source
        or "qualification-context-certificate" in source
    ):
        _fail("accepted parser loader, prior context, or registrar surface drift")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        literals: set[Any] = set()
        for key in node.keys:
            if isinstance(key, ast.Constant) and isinstance(
                key.value, (str, int, float, bytes)
            ):
                if key.value in literals:
                    _fail(f"duplicate literal dictionary key at line {node.lineno}")
                literals.add(key.value)
    runtime_contract = machine["runtime_contract"]
    rosters = runtime_contract.get("operational_receipt_key_rosters")
    if type(rosters) is not dict:
        _fail("machine operational receipt rosters absent")
    for name in (
        "PACKAGE_LOCK_KEYS",
        "PREFLIGHT_AUTHORITY_KEYS",
        "RUNTIME_PREFLIGHT_KEYS",
        "INDEPENDENT_GO_KEYS",
        "ROW_AUTHORITY_KEYS",
        "INTENT_KEYS",
        "OUTCOME_KEYS",
    ):
        if rosters.get(name) != list(_assignment_literal(tree, name)):
            _fail(f"machine/source receipt-key roster mismatch: {name}")
    if runtime_contract.get("sidecar_basenames") != list(
        _assignment_literal(tree, "SIDECAR_BASENAMES")
    ):
        _fail("machine/source sidecar roster mismatch")
    if runtime_contract.get("dyld_arm64e_cache_paths") != list(
        _assignment_literal(tree, "DYLD_CACHE_PATHS")
    ):
        _fail("machine/source dyld cache roster mismatch")
    launcher = runtime_contract.get("exact_launcher_prefix")
    if (
        type(launcher) is not list
        or len(launcher) != 7
        or launcher[2] != _assignment_literal(tree, "EXPECTED_INTERPRETER")
        or launcher[-1] != str(root / relative)
    ):
        _fail("machine/source exact launcher mismatch")
    expected_python_flags = _assignment_literal(tree, "EXPECTED_PYTHON_FLAGS")
    if runtime_contract.get("python_flags_exact") != expected_python_flags:
        _fail("machine/source exact Python flag roster mismatch")
    production_guard = _function_node(tree, "_require_production_process")
    manifest_builder = _function_node(tree, "_runtime_manifest")
    production_guard_text = ast.get_source_segment(source, production_guard) or ""
    manifest_builder_text = ast.get_source_segment(source, manifest_builder) or ""
    if (
        "sys.orig_argv != expected_original_argv" not in production_guard_text
        or "_require_exact_python_runtime_flags()" not in production_guard_text
        or "_require_exact_python_runtime_flags()" not in manifest_builder_text
    ):
        _fail("exact original-argv or Python-flag runtime guard absent")
    attempt_text = ast.get_source_segment(source, attempt) or ""
    intent_token = '_exclusive_canonical_at(rowfd, "intent.json", intent)'
    network_token = "_perform_spent_attempt("
    if intent_token not in attempt_text or network_token not in attempt_text:
        _fail("attempt intent/network markers absent")
    if attempt_text.index(intent_token) >= attempt_text.index(network_token):
        _fail("network path precedes durable intent creation")
    if "_reopen_exact_digest_at(rowfd, \"intent.json\", intent_digest)" not in attempt_text:
        _fail("intent is not reopened before network")
    if "row directory already exists; attempt cannot start or retry" not in attempt_text:
        _fail("preintent poison guard absent")
    if "_validate_row0_success_for_row1" not in attempt_text:
        _fail("row1 contextual row0 gate absent")
    for token in (
        "row0_context_after_intent = _validate_row0_success_for_row1(",
        "row0_context_after_attempt = _validate_row0_success_for_row1(",
        "else (row0_context[1], row0_context[2])",
    ):
        if token not in attempt_text:
            _fail("row1 actual contextual replay/revalidation drift")


def _validate_null_effects(machine: Mapping[str, Any]) -> None:
    slots = machine["current_operational_slots"]
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
    }:
        _fail("operational null-slot roster mismatch")
    if any(value is not None for value in slots.values()):
        _fail("an operational slot is nonnull")
    effects = machine["checklist_effects"]
    if type(effects) is not dict:
        _fail("checklist effects absent")
    required_false = {
        "fetch_performed",
        "resolver_call_performed",
        "durable_row_intent_created",
        "official_fact_verified",
        "administrative_contact_opened",
        "approval_created",
        "data_accessed",
        "scientific_execution_performed",
        "tracker_edited",
        "any_original_solo_block2_operational_box_closed",
    }
    if set(effects) != required_false | {
        "original_solo_block2_operational_boxes_open",
        "scientific_delta",
    }:
        _fail("checklist effects schema mismatch")
    if any(effects[key] is not False for key in required_false):
        _fail("package falsely claims an operational effect")
    if effects["original_solo_block2_operational_boxes_open"] != 7:
        _fail("original Solo Block 2 open-box count changed")
    if effects["scientific_delta"] != "ZERO":
        _fail("scientific delta is not zero")


def validate(root: Path) -> dict[str, Any]:
    machine_path = (
        root
        / "research"
        / "fixtures"
        / "manuscript_v3_solo_block2_runtime_custody_closure_v1.json"
    )
    machine, raw = _read_machine(machine_path)
    if machine["reported_date"] != "2026-08-31":
        _fail("reported date mismatch")
    if machine["package_kind"] != "FINAL_TWO_ROOT_RUNTIME_CUSTODY_EXECUTOR_CLOSURE":
        _fail("package kind mismatch")
    _validate_authority(machine)
    _validate_bindings(
        root,
        machine["immutable_predecessor_bindings"],
        EXPECTED_PREDECESSOR_PATHS,
        include_mtime=False,
    )
    _validate_bindings(
        root,
        machine["package_bindings"],
        EXPECTED_PACKAGE_PATHS,
        include_mtime=True,
    )
    operational_root_entries = _validate_root(machine)
    _validate_operations(machine)
    _validate_executor_ast(root, machine)
    _validate_null_effects(machine)
    contract = machine["executor_contract"]
    if contract != EXPECTED_EXECUTOR_CONTRACT:
        _fail("executor contract is not the exact closed contract")
    runtime = machine["runtime_contract"]
    if type(runtime) is not dict or set(runtime) != EXPECTED_RUNTIME_CONTRACT_KEYS:
        _fail("runtime contract key roster mismatch")
    expected_snapshot = {
        "argv": ["/usr/sbin/scutil", "--dns"],
        "returncode": 1,
        "stdout_base64": "Tm8gRE5TIGNvbmZpZ3VyYXRpb24gYXZhaWxhYmxlCg==",
        "stdout_sha256": (
            "af5688abacd134979a96688203aaa0c19462c6e93261b933c922396fdcba7651"
        ),
        "stdout_bytes": 31,
        "stderr_base64": "",
        "stderr_sha256": (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ),
        "stderr_bytes": 0,
        "dynamic_daemon_cache_wire_state_bound": False,
        "claim_about_dns_packet_count_ttl_cache_or_server_determinism": False,
    }
    expected_runtime_scalars = {
        "ca_path": "/private/etc/ssl/cert.pem",
        "ca_sha256": (
            "9dae8d76e55cb08991f2b672d58999ea15560d910759c16b544f843bdffbb994"
        ),
        "concurrent_same_uid_path_substitution_excluded": False,
        "current_fetch_eligible": False,
        "current_runtime_preflight_admitted": False,
        "current_systemconfiguration_snapshot": "No DNS configuration available",
        "current_systemconfiguration_snapshot_receipt": expected_snapshot,
        "environment_exact": {
            "LC_CTYPE": "C.UTF-8",
            "__CF_USER_TEXT_ENCODING": "0x1F5:0x0:0x0",
        },
        "interpreter_sha256": (
            "71720f1fc66989ebd691e81c96111b47ae6ff3f1a478666084d1cacbf0fccbf2"
        ),
        "openssl_version": "OpenSSL 3.5.7 9 Jun 2026",
        "python_version": "3.12.13 (main, Aug  7 2026, 02:15:23) [Clang 22.1.3 ]",
        "registrar_identity_and_time_are_caller_assertions": True,
        "resolver_unavailable_disposition": "HOLD_WITHOUT_PREFLIGHT_RECEIPT",
        "runtime_drift_disposition": "HOLD_BEFORE_INTENT",
        "runtime_preflight_materialized": False,
        "source_and_interpreter_receipts_are_post_load": True,
    }
    if any(runtime.get(key) != expected for key, expected in expected_runtime_scalars.items()):
        _fail("runtime contract scalar/nonclaim mismatch")
    qualification = machine["qualification_contract"]
    if qualification != EXPECTED_QUALIFICATION_CONTRACT:
        _fail("qualification contract is not exact closed zero-effect policy")
    human_raw, _human_st = _read_absolute_regular(
        os.path.join(str(root.absolute()), "PROJECT_SOLO_BLOCK2_RUNTIME_CUSTODY_CLOSURE.md")
    )
    human = human_raw.decode("utf-8")
    for token in (
        STATE,
        EXPECTED_AUTHORITY,
        "TERMINAL_ABANDONED_PREINTENT_RESERVATION_NO_REQUEST_NO_RETRY",
        "No DNS configuration available",
        "No original Solo Block 2 operational box is closed",
        "post-load path receipts",
        "not externally authenticated, signed or trusted-clock attested",
        "no synthetic prior is available",
    ):
        if token not in human:
            _fail(f"human contract missing binding token: {token}")
    return {
        "status": "PASS",
        "schema_version": SCHEMA,
        "state": STATE,
        "machine_raw_sha256": _sha256(raw),
        "machine_record_sha256": machine["record_sha256"],
        "operation_count": 2,
        "fetches_performed": 0,
        "durable_intents_created": 0,
        "operational_root_entries": operational_root_entries,
        "scientific_delta": "ZERO",
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        raise SystemExit("usage: validator.py [REPOSITORY_ROOT]")
    root = Path(args[0]).resolve() if args else Path(__file__).resolve().parents[2]
    try:
        result = validate(root)
    except (OSError, ValidationError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
