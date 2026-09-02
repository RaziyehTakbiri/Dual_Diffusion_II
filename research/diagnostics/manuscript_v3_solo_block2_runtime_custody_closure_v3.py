#!/usr/bin/env python3
"""Offline validator for the Solo Block 2 resolver/link repair candidate v3."""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "heterodiff-manuscript-v3-solo-block2-runtime-custody-closure-v3"
STATE = (
    "FINAL_V3_ENUM_AND_ROW1_LINK_REPAIR_QUALIFIED_"
    "NO_OPERATIONAL_ROOT_NO_FETCH_HOLD"
)
V2_ROOT = (
    "/Users/mahtab/.codex/.chatgpt-projects/"
    "g-p-6a5f91c1e79c819183983ba0010bb151/"
    "research/custody/solo_block2_public_documentation_runtime_v2"
)
V3_ROOT = (
    "/Users/mahtab/.codex/.chatgpt-projects/"
    "g-p-6a5f91c1e79c819183983ba0010bb151/"
    "research/custody/solo_block2_public_documentation_runtime_v3"
)
MACHINE_RELATIVE = (
    "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v3.json"
)
EXECUTOR_RELATIVE = (
    "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v3.py"
)
V3_PACKAGE_PATHS = {
    "PROJECT_SOLO_BLOCK2_RUNTIME_CUSTODY_CLOSURE_V3.md",
    "research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v3.py",
    "tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v3.py",
    EXECUTOR_RELATIVE,
    "tests/unit/test_solo_block2_runtime_custody_executor_v3.py",
}
V2_PACKAGE = {
    "PROJECT_SOLO_BLOCK2_RUNTIME_CUSTODY_CLOSURE_V2.md": (
        9_375,
        "42bc63cc9b9d828ea2f6d6774374d52f00c8bfadf7183fb50292c942e75d3451",
    ),
    "research/fixtures/manuscript_v3_solo_block2_runtime_custody_closure_v2.json": (
        14_588,
        "a1e477c9006eb5d47a4b8af9405ab58c91559c739a27e9ccaa0a68f6927bc6ab",
    ),
    "research/diagnostics/manuscript_v3_solo_block2_runtime_custody_closure_v2.py": (
        33_034,
        "cdda43c7b6032cfb5adb6b1d6bf20f8e6f88c6e93a5747fad9c7040c983cca1e",
    ),
    "tests/unit/test_manuscript_v3_solo_block2_runtime_custody_closure_v2.py": (
        7_389,
        "6d93642d186654aa0e01fe1eb226467977cba38067c16adaf9fb74aeb7855286",
    ),
    "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v2.py": (
        149_611,
        "26d72af736750c68581578ad000efa0b4906e354aebd8d2c4c799406aca4f1ec",
    ),
    "tests/unit/test_solo_block2_runtime_custody_executor_v2.py": (
        31_652,
        "358ef1ea59c9786c36d8835300c749da1e763ac0ec92996728c356655973c522",
    ),
}
V2_PACKAGE_AGGREGATE = (
    "48091940a7ceb844c892fb06fd263e479b8c86a1f46c4f0c88d00d72a87439cb"
)
V2_ROOT_ROSTER = {
    "package-lock.json",
    "preflight-authority.json",
    "runtime-preflight.json",
    "row0-independent-go.json",
    "row0-authority.json",
    "row0-physionet-root-v1",
}
V2_ROW_ROSTER = {
    "request.raw",
    "response-head.raw",
    "transfer-body.raw",
    "decoded-entity.raw",
    "tls-metadata.raw",
    "stderr.raw",
    "overflow-witness.raw",
    "intent.json",
    "error.json",
    "outcome.json",
}
V2_GATE_RAW = {
    "package-lock.json": "d5850ab5a1fcbaeecd61dee1beddbb21e67c4a5e17b86a00887af41ea782ac2f",
    "preflight-authority.json": "d9639612530820df9f1b7add818003954aca4b10cf5a63947921e64b9d43716f",
    "runtime-preflight.json": "daeb666b9c0c0a95104b2dd062c4897eea6b61483a6bf2dbbbee355e8c2edd8d",
    "row0-independent-go.json": "0679ad0b6fedd02e677955ac9a79b0041ded4a5270c52b3dbe97d2e0ab46b96c",
    "row0-authority.json": "78207407a891ffe2b7d35b8fd9d4b32ad412d3db4baa0ba4fc82b5f4e7659dc5",
}
V2_ROW_RAW = {
    "request.raw": "ac9c9c12e45d8690381803e003a36cfa22c330b8e8ea601d94725b4312be9449",
    "response-head.raw": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "transfer-body.raw": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "decoded-entity.raw": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "tls-metadata.raw": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "stderr.raw": "16e06149051bde2bff10be7ff6ab5f564d1b19dde02c872a024d4b4b13ff5e48",
    "overflow-witness.raw": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "intent.json": "a02263b26109ef29f7212a8ea72c987e9e4f7732a88f6ff6b305b99d89177b92",
    "error.json": "705ddcdb3f0be55ad434620c574a21ea3e02aff6c892ca88f1743d5da6ec3964",
    "outcome.json": "ae72c77609c10c21aaf3e64a8ab77bf4da3adb03c42e55f3bfdfa17f00a98458",
}
V2_RECORD_SEMANTIC = {
    "intent.json": "e3735ad4c4ab07e79ab0dbc3ef8e8f3c26f5ee86489a7233b854854dea5d1610",
    "error.json": "aaeca81dd0bd9305c624249cfdc057387fd465fee5b889b16b81ce752285ef55",
    "outcome.json": "b463ba6475fe82dae08aa98ca2a7d3710915b077f97de2748edf84445aca4924",
}
EXPECTED_TOP_KEYS = {
    "schema_version",
    "record_sha256",
    "state",
    "reported_date",
    "package_kind",
    "direct_v2_predecessor_bindings",
    "package_bindings",
    "executor_source_binding",
    "operational_custody_root",
    "v2_spent_incident",
    "operation_roster",
    "repair_contract",
    "executor_contract",
    "qualification_contract",
    "supersession_contract",
    "current_operational_slots",
    "checklist_effects",
}
EXPECTED_REPAIR_CONTRACT = {
    "resolver_system_enums_normalized_at_child_json_boundary": True,
    "resolver_numeric_leaves_are_exact_builtin_int": True,
    "resolver_parsed_leaves_retained_without_enum_reintroduction": True,
    "resolver_validation_precedes_socket": True,
    "resolver_validation_precedes_connect_tls_and_send": True,
    "row1_intent_link_uses_raw_receipt_sha256": True,
    "row1_semantic_digest_substitution_rejected": True,
    "exact_requests_changed": False,
    "v1_bytes_or_custody_modified": False,
    "v2_bytes_or_custody_modified": False,
}
EXPECTED_EXECUTOR_CONTRACT = {
    "executing_image_one_open_attestation_claimed": False,
    "concurrent_same_uid_path_substitution_excluded": False,
    "registrar_identity_externally_authenticated": False,
    "registrar_time_externally_attested": False,
    "registrar_identity_and_time_are_caller_assertions": True,
    "candidate_has_operational_root_binding": False,
    "production_commands_fail_closed_without_bound_root": True,
    "general_url_or_request_input_present": False,
    "network_calls_reachable_in_candidate_state": False,
    "attempt_limit_if_later_activated": 1,
    "retry_limit_if_later_activated": 0,
    "redirect_limit_if_later_activated": 0,
    "address_fallback_limit_if_later_activated": 0,
}
EXPECTED_QUALIFICATION_CONTRACT = {
    "external_network_permitted": False,
    "loopback_permitted": False,
    "browser_permitted": False,
    "operational_root_creation_permitted": False,
    "operational_receipt_materialization_permitted": False,
    "production_command_invocation_permitted": False,
    "qualification_can_spend_attempt": False,
    "qualification_can_verify_official_fact": False,
    "bytecode_cache_disabled_required": True,
    "pytest_cache_disabled_required": True,
}
EXPECTED_SUPERSESSION_CONTRACT = {
    "explicit_user_supersession_required": True,
    "new_version_or_root_resets_budget": False,
    "authority_present": False,
    "activation_package_present": False,
    "scope": "GLOBAL_SINGLE_ADDITIONAL_ROW0_ATTEMPT_ONLY",
    "additional_attempts_if_authorized": 1,
    "authorized_row_ordinal": 0,
    "authorized_operation_id": "SB2-PUBLIC-ROOT-PHYSIONET-000",
    "authorized_exact_url": "https://physionet.org/content/challenge-2012/1.0.0/",
    "authorized_exact_request_bytes": 282,
    "authorized_exact_request_sha256": (
        "ac9c9c12e45d8690381803e003a36cfa22c330b8e8ea601d94725b4312be9449"
    ),
    "v2_spent_attempt_acknowledgment_required": True,
    "v2_package_aggregate_sha256": V2_PACKAGE_AGGREGATE,
    "v2_intent_raw_sha256": V2_ROW_RAW["intent.json"],
    "v2_intent_record_sha256": V2_RECORD_SEMANTIC["intent.json"],
    "v2_error_raw_sha256": V2_ROW_RAW["error.json"],
    "v2_error_record_sha256": V2_RECORD_SEMANTIC["error.json"],
    "v2_outcome_raw_sha256": V2_ROW_RAW["outcome.json"],
    "v2_outcome_record_sha256": V2_RECORD_SEMANTIC["outcome.json"],
    "v2_terminal_state": "TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY",
    "unique_one_use_budget_id_required_on_activation": True,
    "unique_one_use_budget_id": None,
    "row1_may_consume_same_supersession_budget": False,
    "retry_limit": 0,
    "redirect_limit": 0,
    "address_fallback_limit": 0,
    "application_fallback_limit": 0,
    "resolver_high_level_call_limit": 1,
    "socket_instance_limit": 1,
    "connect_limit": 1,
    "tls_wrap_limit": 1,
    "sendall_limit": 1,
    "durable_intent_spends_successor_budget": True,
    "same_request_only": True,
    "v2_receipts_reusable": False,
    "final_authority_must_bind_activation_package_and_root": True,
    "final_authority_must_bind_all_v2_evidence_above": True,
}
EXPECTED_OPERATIONAL_SLOTS = {
    "package_lock": None,
    "preflight_authority": None,
    "runtime_preflight": None,
    "supersession_authority": None,
    "row0_independent_go": None,
    "row0_authority": None,
    "row0_intent": None,
    "row0_outcome": None,
    "row1_independent_go": None,
    "row1_authority": None,
    "row1_intent": None,
    "row1_outcome": None,
}
EXPECTED_CHECKLIST_EFFECTS = {
    "v1_bytes_modified": False,
    "v1_custody_modified": False,
    "v2_bytes_modified": False,
    "v2_custody_modified": False,
    "v2_attempt_budget_spent": True,
    "v3_operational_root_created": False,
    "v3_operational_receipt_created": False,
    "v3_durable_row_intent_created": False,
    "v3_resolver_call_performed": False,
    "v3_socket_created": False,
    "v3_fetch_performed": False,
    "data_accessed": False,
    "tracker_edited": False,
    "scientific_delta": "ZERO",
}
O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
DIR_OPEN_FLAGS = os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW

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


class ValidationError(RuntimeError):
    """A v3 repair-candidate invariant failed."""


def _fail(message: str) -> None:
    raise ValidationError(message)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            _fail("duplicate or non-string JSON key")
        result[key] = value
    return result


def _canonical(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8") + b"\n"
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ValidationError("non-canonical JSON data") from exc


def _self_digest(value: Mapping[str, Any]) -> str:
    clone = dict(value)
    clone["record_sha256"] = None
    return _sha256(_canonical(clone))


def _open_absolute_componentwise(path: Path, final_flags: int) -> int:
    value = str(path)
    if (
        not value.startswith("/")
        or value == "/"
        or "\x00" in value
        or "//" in value
        or value.endswith("/")
        or os.path.normpath(value) != value
    ):
        _fail("validator path is not exact normalized absolute")
    parts = value.split("/")[1:]
    if not parts or any(part in {"", ".", ".."} for part in parts):
        _fail("validator path contains an unsafe component")
    dirfd = os.open("/", DIR_OPEN_FLAGS)
    try:
        for component in parts[:-1]:
            nextfd = os.open(component, DIR_OPEN_FLAGS, dir_fd=dirfd)
            os.close(dirfd)
            dirfd = nextfd
        return os.open(parts[-1], final_flags | O_NOFOLLOW, dir_fd=dirfd)
    finally:
        os.close(dirfd)


def _read_regular(path: Path, cap: int = 1_048_576) -> tuple[bytes, os.stat_result]:
    fd = _open_absolute_componentwise(path.absolute(), os.O_RDONLY)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            _fail(f"not a regular nlink-one file: {path}")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(131_072, cap + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > cap:
                _fail(f"file exceeds cap: {path}")
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
            _fail(f"file changed while read: {path}")
        return b"".join(chunks), before
    finally:
        os.close(fd)


def _directory_identity_and_names(path: Path) -> tuple[dict[str, Any], set[str]]:
    absolute = path.absolute()
    fd = _open_absolute_componentwise(absolute, DIR_OPEN_FLAGS)
    try:
        st = os.fstat(fd)
        if not stat.S_ISDIR(st.st_mode):
            _fail(f"not an exact directory: {path}")
        identity = {
            "absolute_path": str(absolute),
            "device": st.st_dev,
            "inode": st.st_ino,
            "uid": st.st_uid,
            "gid": st.st_gid,
            "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}",
            "nlink": st.st_nlink,
        }
        names = os.listdir(fd)
        if len(names) != len(set(names)):
            _fail(f"duplicate directory entries observed: {path}")
        return identity, set(names)
    finally:
        os.close(fd)


def _read_record(path: Path) -> tuple[dict[str, Any], bytes, os.stat_result]:
    raw, st = _read_regular(path)
    if not raw.endswith(b"\n"):
        _fail(f"canonical record lacks newline: {path}")
    try:
        value = json.loads(raw, object_pairs_hook=_strict_pairs)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValidationError(f"invalid JSON record: {path}") from exc
    if type(value) is not dict or _canonical(value) != raw:
        _fail(f"record is not exact canonical JSON: {path}")
    if value.get("record_sha256") != _self_digest(value):
        _fail(f"record self digest mismatch: {path}")
    return value, raw, st


def _file_receipt(root: Path, relative: str, *, mtime: bool) -> dict[str, Any]:
    raw, st = _read_regular(root / relative)
    receipt: dict[str, Any] = {
        "path": relative,
        "bytes": len(raw),
        "sha256": _sha256(raw),
        "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}",
        "nlink": st.st_nlink,
    }
    if mtime:
        receipt["mtime_ns"] = st.st_mtime_ns
    return receipt


def _validate_bindings(root: Path, machine: Mapping[str, Any]) -> None:
    predecessor = machine.get("direct_v2_predecessor_bindings")
    if type(predecessor) is not list or len(predecessor) != len(V2_PACKAGE):
        _fail("v2 predecessor binding roster invalid")
    actual_predecessor = [
        _file_receipt(root, path, mtime=False) for path in sorted(V2_PACKAGE)
    ]
    for item in actual_predecessor:
        size, digest = V2_PACKAGE[item["path"]]
        if (item["bytes"], item["sha256"], item["mode_octal"], item["nlink"]) != (
            size,
            digest,
            "0644",
            1,
        ):
            _fail("locked v2 package byte binding drift")
    if predecessor != actual_predecessor:
        _fail("machine v2 predecessor bindings mismatch")

    bindings = machine.get("package_bindings")
    if type(bindings) is not list:
        _fail("v3 package bindings absent")
    actual = [
        _file_receipt(root, path, mtime=True) for path in sorted(V3_PACKAGE_PATHS)
    ]
    if bindings != actual:
        _fail("v3 package bindings mismatch")
    executor = next(item for item in actual if item["path"] == EXECUTOR_RELATIVE)
    if machine.get("executor_source_binding") != {
        "path": executor["path"],
        "bytes": executor["bytes"],
        "sha256": executor["sha256"],
    }:
        _fail("v3 executor source binding mismatch")


def _identity(path: Path) -> dict[str, Any]:
    identity, _names = _directory_identity_and_names(path)
    return identity


def _custody_receipt(path: Path) -> dict[str, Any]:
    raw, st = _read_regular(path)
    return {
        "bytes": len(raw),
        "sha256": _sha256(raw),
        "device": st.st_dev,
        "inode": st.st_ino,
        "uid": st.st_uid,
        "gid": st.st_gid,
        "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}",
        "nlink": st.st_nlink,
    }


def _validate_v2_incident(machine: Mapping[str, Any]) -> None:
    root = Path(V2_ROOT)
    row = root / "row0-physionet-root-v1"
    root_identity, root_names = _directory_identity_and_names(root)
    row_identity, row_names = _directory_identity_and_names(row)
    if root_names != V2_ROOT_ROSTER or row_names != V2_ROW_ROSTER:
        _fail("v2 incident roster drift")
    incident = machine.get("v2_spent_incident")
    if type(incident) is not dict:
        _fail("v2 incident binding absent")
    if incident.get("custody_root") != root_identity:
        _fail("v2 root identity mismatch")
    if incident.get("row_directory") != row_identity:
        _fail("v2 row identity mismatch")
    if incident.get("exact_root_roster") != sorted(V2_ROOT_ROSTER):
        _fail("v2 root roster machine mismatch")
    if incident.get("exact_row_roster") != sorted(V2_ROW_ROSTER):
        _fail("v2 row roster machine mismatch")

    gate_receipts = {
        name: _custody_receipt(root / name) for name in sorted(V2_GATE_RAW)
    }
    row_receipts = {
        name: _custody_receipt(row / name) for name in sorted(V2_ROW_RAW)
    }
    if incident.get("gate_receipts") != gate_receipts:
        _fail("v2 gate receipt machine mismatch")
    if incident.get("row_receipts") != row_receipts:
        _fail("v2 row receipt machine mismatch")
    if any(gate_receipts[name]["sha256"] != digest for name, digest in V2_GATE_RAW.items()):
        _fail("v2 gate raw digest drift")
    if any(row_receipts[name]["sha256"] != digest for name, digest in V2_ROW_RAW.items()):
        _fail("v2 row raw digest drift")

    records: dict[str, dict[str, Any]] = {}
    for name in ("intent.json", "error.json", "outcome.json"):
        value, raw, _st = _read_record(row / name)
        if _sha256(raw) != V2_ROW_RAW[name] or value["record_sha256"] != V2_RECORD_SEMANTIC[name]:
            _fail("v2 terminal record digest drift")
        records[name] = value
    intent = records["intent.json"]
    error = records["error.json"]
    outcome = records["outcome.json"]
    expected_progress = {
        "resolver_child_fork_site_count": 1,
        "resolver_high_level_call_count": 1,
        "socket_instance_count": 1,
        "connect_call_count": 1,
        "tls_wrap_call_count": 1,
        "sendall_call_count": 0,
        "request_emission_state": "NOT_ATTEMPTED",
    }
    if incident.get("package_aggregate_sha256") != V2_PACKAGE_AGGREGATE:
        _fail("v2 package aggregate incident mismatch")
    if intent.get("package_aggregate_sha256") != V2_PACKAGE_AGGREGATE:
        _fail("v2 intent package binding mismatch")
    if intent.get("terminal_contract") != "DURABLE_INTENT_SPENDS_ONE_ATTEMPT_NO_RETRY":
        _fail("v2 spend boundary drift")
    for key, expected in expected_progress.items():
        if error.get(key) != expected or outcome.get(key) != expected:
            _fail(f"v2 progress receipt mismatch: {key}")
    if (
        error.get("error_text") != "resolver receipt row value invalid"
        or outcome.get("terminal_state")
        != "TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY"
        or outcome.get("retry_permitted") is not False
        or outcome.get("qualified_root_page_observation") is not None
        or outcome.get("official_source_version_or_license_verified") is not False
        or outcome.get("approval_created") is not False
        or outcome.get("tracker_or_science_effect") is not False
    ):
        _fail("v2 terminal non-effect mismatch")
    if incident.get("progress") != expected_progress:
        _fail("machine v2 progress summary mismatch")
    if incident.get("terminal_state") != outcome["terminal_state"]:
        _fail("machine v2 terminal summary mismatch")
    if incident.get("retry_permitted") is not False:
        _fail("machine improperly resets v2 retry")
    if incident.get("qualified_observation") is not None:
        _fail("machine invents a v2 observation")

    expected_incident = {
        "custody_root": root_identity,
        "row_directory": row_identity,
        "exact_root_roster": sorted(V2_ROOT_ROSTER),
        "exact_row_roster": sorted(V2_ROW_ROSTER),
        "gate_receipts": gate_receipts,
        "row_receipts": row_receipts,
        "package_aggregate_sha256": V2_PACKAGE_AGGREGATE,
        "operation_id": "SB2-PUBLIC-ROOT-PHYSIONET-000",
        "exact_url": "https://physionet.org/content/challenge-2012/1.0.0/",
        "exact_request_bytes": 282,
        "exact_request_sha256": V2_ROW_RAW["request.raw"],
        "intent_raw_sha256": V2_ROW_RAW["intent.json"],
        "intent_record_sha256": V2_RECORD_SEMANTIC["intent.json"],
        "error_raw_sha256": V2_ROW_RAW["error.json"],
        "error_record_sha256": V2_RECORD_SEMANTIC["error.json"],
        "outcome_raw_sha256": V2_ROW_RAW["outcome.json"],
        "outcome_record_sha256": V2_RECORD_SEMANTIC["outcome.json"],
        "progress": expected_progress,
        "terminal_state": "TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY",
        "retry_permitted": False,
        "qualified_observation": None,
        "official_fact_verified": False,
        "tracker_or_science_effect": False,
        "row1_preempted": True,
        "live_failure_leaf": "socktype:socket.SocketKind_not_exact_builtin_int",
        "tls_handshake_completed_before_failure_inferred_from_source_order": True,
        "http_request_bytes_emitted": False,
    }
    if _canonical(incident) != _canonical(expected_incident):
        _fail("exact v2 incident summary contract mismatch")


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    _fail(f"executor function absent: {name}")
    raise AssertionError


def _assignment(tree: ast.Module, name: str) -> Any:
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target = node.target if isinstance(node, ast.AnnAssign) else node.targets[0]
            if isinstance(target, ast.Name) and target.id == name:
                try:
                    return ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    _fail(f"executor assignment is not literal: {name}")
    _fail(f"executor assignment absent: {name}")
    raise AssertionError


def _operation_literal_projection(tree: ast.Module) -> list[tuple[Any, ...]]:
    value: ast.AST | None = None
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "OPERATIONS"
        ):
            value = node.value
            break
    if not isinstance(value, ast.Tuple) or len(value.elts) != 2:
        _fail("executor operation tuple literal absent")
    result: list[tuple[Any, ...]] = []
    for item in value.elts:
        if (
            not isinstance(item, ast.Call)
            or _dotted(item.func) != "ExactOperation"
            or len(item.args) != 8
            or item.keywords
            or not isinstance(item.args[7], ast.Name)
        ):
            _fail("executor operation literal shape mismatch")
        try:
            prefix = tuple(ast.literal_eval(arg) for arg in item.args[:7])
        except (ValueError, TypeError) as exc:
            raise ValidationError("executor operation literal is dynamic") from exc
        result.append(prefix + (item.args[7].id,))
    return result


def _owned_calls(function: ast.FunctionDef) -> list[str]:
    """Return calls owned by one top-level function without nested definitions."""

    calls: list[str] = []
    stack: list[ast.AST] = list(function.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        if isinstance(node, ast.Call):
            calls.append(_dotted(node.func))
        stack.extend(ast.iter_child_nodes(node))
    return calls


def _validate_operational_call_ownership(tree: ast.Module) -> None:
    expected = {
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
    found: dict[str, list[str]] = {name: [] for name in expected}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for call in _owned_calls(node):
            if call in found:
                found[call].append(node.name)
    for name, (owner, count) in expected.items():
        if found[name] != [owner] * count:
            _fail(f"executor operational call ownership mismatch: {name}")


def _validate_executor(root: Path, machine: Mapping[str, Any]) -> None:
    raw, _st = _read_regular(root / EXECUTOR_RELATIVE)
    source = raw.decode("utf-8")
    tree = ast.parse(source)
    if _assignment(tree, "SCHEMA_VERSION") != "heterodiff-solo-block2-runtime-custody-executor-v3":
        _fail("v3 executor schema mismatch")
    if _assignment(tree, "MACHINE_STATE") != STATE:
        _fail("v3 executor state mismatch")
    expected_operation_literals = [
        (
            0,
            "SB2-PUBLIC-ROOT-PHYSIONET-000",
            "PhysioNet",
            "physionet.org",
            "/content/challenge-2012/1.0.0/",
            "https://physionet.org/content/challenge-2012/1.0.0/",
            "row0-physionet-root-v1",
            "_REQUEST_0",
        ),
        (
            1,
            "SB2-PUBLIC-ROOT-UCI-001",
            "UCI Machine Learning Repository",
            "archive.ics.uci.edu",
            "/dataset/502/online+retail+ii",
            "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
            "row1-uci-online-retail-ii-root-v1",
            "_REQUEST_1",
        ),
    ]
    if _operation_literal_projection(tree) != expected_operation_literals:
        _fail("executor operation literal roster mismatch")
    if _assignment(tree, "_REQUEST_0") != REQUESTS[0] or _assignment(
        tree, "_REQUEST_1"
    ) != REQUESTS[1]:
        _fail("executor exact request bytes mismatch")
    calls = [_dotted(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    _validate_operational_call_ownership(tree)
    for name, count in {"compile": 1, "exec": 1}.items():
        if calls.count(name) != count:
            _fail(f"executor dynamic-loader call count mismatch: {name}")
    if any(
        name in calls
        for name in (
            "os.remove",
            "os.unlink",
            "os.rename",
            "os.replace",
            "os.rmdir",
            "shutil.rmtree",
            "urllib.request.urlopen",
            "requests.get",
            "requests.post",
            "eval",
        )
    ):
        _fail("executor contains a destructive path")

    normalizer = ast.get_source_segment(source, _function(tree, "_resolver_system_tuple_to_json_row")) or ""
    strict = ast.get_source_segment(source, _function(tree, "_strict_resolver_rows")) or ""
    perform = ast.get_source_segment(source, _function(tree, "_perform_spent_attempt")) or ""
    row1 = ast.get_source_segment(source, _function(tree, "_validate_row0_success_for_row1")) or ""
    attempt = ast.get_source_segment(source, _function(tree, "attempt")) or ""
    if not all(token in normalizer for token in ("int(family)", "int(socktype)", "int(proto)")):
        _fail("system resolver enum normalization absent")
    if not all(
        token in strict
        for token in (
            "type(family) is not int",
            "type(socktype) is not int",
            "type(proto) is not int",
            '"family": family',
            '"socktype": socktype',
            '"protocol": proto',
        )
    ):
        _fail("strict resolver JSON-native projection absent")
    if '"socktype": socket.SOCK_STREAM' in strict or '"protocol": socket.IPPROTO_TCP' in strict:
        _fail("resolver receipt reintroduces socket enums")
    if not (
        perform.index("_validate_resolver_receipt_rows(")
        < perform.index("socket.socket(")
        < perform.index("raw_socket.connect(")
        < perform.index("ssl.SSLContext(")
        < perform.index("tls.sendall(")
    ):
        _fail("resolver/socket/TLS/send validation order mismatch")
    attempt_tokens = (
        "_revalidate_runtime_immediately_before_reservation(",
        "_mkdir_row(",
        '_exclusive_canonical_at(rowfd, "intent.json", intent)',
        "_perform_spent_attempt(",
    )
    if any(token not in attempt for token in attempt_tokens) or not (
        attempt.index(attempt_tokens[0])
        < attempt.index(attempt_tokens[1])
        < attempt.index(attempt_tokens[2])
        < attempt.index(attempt_tokens[3])
    ):
        _fail("runtime revalidation/reservation/intent/network order mismatch")
    if '_reopen_exact_digest_at(rowfd, "intent.json", intent_digest)' not in attempt:
        _fail("durable intent is not reopened before network")
    if "_require_raw_receipt_forward_link(" not in row1 or "intent_raw" not in row1:
        _fail("row0-to-row1 raw receipt link repair absent")
    if machine.get("executor_source_binding", {}).get("sha256") != _sha256(raw):
        _fail("executor machine binding drift")


def _validate_operations(machine: Mapping[str, Any]) -> None:
    rows = machine.get("operation_roster")
    if type(rows) is not list or len(rows) != 2:
        _fail("operation roster invalid")
    expected = (
        (
            0,
            "SB2-PUBLIC-ROOT-PHYSIONET-000",
            "PhysioNet",
            "https://physionet.org/content/challenge-2012/1.0.0/",
            "physionet.org",
            "/content/challenge-2012/1.0.0/",
            "row0-physionet-root-v1",
        ),
        (
            1,
            "SB2-PUBLIC-ROOT-UCI-001",
            "UCI Machine Learning Repository",
            "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
            "archive.ics.uci.edu",
            "/dataset/502/online+retail+ii",
            "row1-uci-online-retail-ii-root-v1",
        ),
    )
    exact_keys = {
        "ordinal",
        "operation_id",
        "domain",
        "url",
        "host",
        "path",
        "row_basename",
        "method",
        "request_base64",
        "request_bytes",
        "request_sha256",
        "attempt_limit",
        "retry_limit",
        "redirect_limit",
        "fetch_eligible",
    }
    for row, request, values in zip(rows, REQUESTS, expected):
        if type(row) is not dict or set(row) != exact_keys:
            _fail("operation schema mismatch")
        ordinal, operation_id, domain, url, host, path, basename = values
        if (
            row["ordinal"] != ordinal
            or type(row["ordinal"]) is not int
            or row["operation_id"] != operation_id
            or row["domain"] != domain
            or row["url"] != url
            or row["host"] != host
            or row["path"] != path
            or row["row_basename"] != basename
            or row["method"] != "GET"
            or row["request_base64"] != base64.b64encode(request).decode("ascii")
            or row["request_bytes"] != len(request)
            or type(row["request_bytes"]) is not int
            or row["request_sha256"] != _sha256(request)
            or (row["attempt_limit"], row["retry_limit"], row["redirect_limit"])
            != (1, 0, 0)
            or any(type(row[key]) is not int for key in ("attempt_limit", "retry_limit", "redirect_limit"))
            or row["fetch_eligible"] is not False
        ):
            _fail("operation value mismatch")


def _validate_contracts(machine: Mapping[str, Any]) -> None:
    exact_contracts = {
        "checklist_effects": EXPECTED_CHECKLIST_EFFECTS,
        "current_operational_slots": EXPECTED_OPERATIONAL_SLOTS,
        "repair_contract": EXPECTED_REPAIR_CONTRACT,
        "executor_contract": EXPECTED_EXECUTOR_CONTRACT,
        "qualification_contract": EXPECTED_QUALIFICATION_CONTRACT,
        "supersession_contract": EXPECTED_SUPERSESSION_CONTRACT,
    }
    for key, expected in exact_contracts.items():
        actual = machine.get(key)
        if type(actual) is not dict or _canonical(actual) != _canonical(expected):
            _fail(f"exact nested contract mismatch: {key}")
    if machine.get("operational_custody_root") is not None or Path(V3_ROOT).exists():
        _fail("v3 operational root must be absent")


def validate(root: Path) -> dict[str, Any]:
    root = root.absolute()
    machine, raw, _st = _read_record(root / MACHINE_RELATIVE)
    if set(machine) != EXPECTED_TOP_KEYS:
        _fail("machine top-level schema mismatch")
    if machine.get("schema_version") != SCHEMA or machine.get("state") != STATE:
        _fail("machine schema/state mismatch")
    if machine.get("reported_date") != "2026-08-31":
        _fail("reported date mismatch")
    if machine.get("package_kind") != "ADDITIVE_V3_OFFLINE_ENUM_AND_ROW1_LINK_REPAIR_CANDIDATE":
        _fail("package kind mismatch")
    _validate_bindings(root, machine)
    _validate_v2_incident(machine)
    _validate_operations(machine)
    _validate_executor(root, machine)
    _validate_contracts(machine)
    return {
        "status": "PASS",
        "schema_version": SCHEMA,
        "machine_raw_sha256": _sha256(raw),
        "machine_semantic_sha256": machine["record_sha256"],
        "v3_operational_root_present": False,
        "v3_network_actions": 0,
        "v2_attempt_spent_preserved": True,
        "official_facts_verified": 0,
        "tracker_or_science_effect": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        result = validate(args.root)
    except (ValidationError, OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
