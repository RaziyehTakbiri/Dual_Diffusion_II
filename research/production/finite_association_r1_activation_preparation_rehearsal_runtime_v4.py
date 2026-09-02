"""Stdlib-only, privacy-safe environment child for the frozen V4 rehearsal.

The child cannot write authority custody.  It reads one request from stdin,
observes only its launch profile, removes Darwin's injected CF entry from the
real process environment, and emits one bounded canonical Boolean record.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any, Mapping, Sequence


REQUEST_SCHEMA = "heterodiff-a1-r1-activation-preparation-v4-runtime-request-v1"
OBSERVATION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-child-observation-v1"
)
MODULE_PATH = Path(__file__).absolute()
WORKSPACE_ROOT = MODULE_PATH.parents[2]
MACHINE_PATH = WORKSPACE_ROOT / (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_freeze_v1.json"
)
AUTHORIZATION_PATH = WORKSPACE_ROOT / (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "execution_authorization_v1.json"
)
MARKER_PATH = WORKSPACE_ROOT / "artifacts/a1_r1_activation_preparation_v4.attempt.json"
PREPARATION_ROOT = WORKSPACE_ROOT / "artifacts/a1_r1_activation_preparation_v4"
LEDGER_PATH = PREPARATION_ROOT / "ledger"
EVENTS_PATH = LEDGER_PATH / "events"
LOCK_PATH = LEDGER_PATH / "writer.lock"
GENESIS_PATH = LEDGER_PATH / "genesis.json"
TERMINAL_PATH = LEDGER_PATH / "terminal.json"
RESULT_PATH = WORKSPACE_ROOT / (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_result_v1.json"
)
PYTHON_PATH = WORKSPACE_ROOT / ".venv-m1/bin/python"
PYTHON_REALPATH = Path(
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
)
PYTHON_FLAGS = ("-P", "-B", "-S", "-X", "utf8")
EXPECTED_SYS_PATH = (
    "/Library/Frameworks/Python.framework/Versions/3.11/lib/python311.zip",
    "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11",
    "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/lib-dynload",
)
REQUESTED_ENVIRONMENT = {
    "BLIS_NUM_THREADS": "1",
    "CUDA_VISIBLE_DEVICES": "",
    "LANG": "C",
    "LC_ALL": "C",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONPYCACHEPREFIX": "/dev/null",
    "PYTHONSAFEPATH": "1",
    "PYTHONUTF8": "1",
    "TZ": "UTC",
    "VECLIB_MAXIMUM_THREADS": "1",
}
DARWIN_KEY = "__CF_USER_TEXT_ENCODING"
HASH_PROBE_STRINGS = (
    "heterodiff-a1",
    "dual-manifold",
    "runtime-attestor",
    "frozen-prerequisite-v2",
)
HASH_PROBE_SHA256 = "f7b1ba1308d7559c69fc44640d0fcd07dbeae53b9024da5d862463db71e230af"
MAXIMUM_STDIN_BYTES = 64 * 1024

AUTHORIZATION_CONTEXT_SHA256 = (
    "3e989c3935c829a5920992b29de6001369c29c9fb25f686eb44ee48be6026417"
)
VISIBLE_ASSENT_SHA256 = (
    "33c38693197abe2849d02736250138322c452c4294552258757cfd5ae3a77994"
)
ATTEMPT_ID_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-v4-attempt-identity-v1\0"
)
ATTEMPT_NONCE_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-v4-deterministic-attempt-nonce-v1\0"
)
PRECHILD_GATE_ORDER = (
    "registration_exact",
    "authorization_certificate_exact",
    "canonical_workspace_anchor_exact",
    "v3_terminal_registration_exact",
    "v3_terminal_custody_exact",
    "v3_attempt_count_one_retry_count_zero",
    "v3_spent_namespace_absent",
    "v2_terminal_custody_exact",
    "v4_source_closure_exact",
    "v4_closed_world_prefix_exact",
    "canonical_cwd_exact",
    "requested_environment_exact",
    "darwin_environment_normalized",
    "identity_nonprivileged_exact",
    "cpython_3_11_5_exact",
    "darwin_arm64_exact",
    "python_flags_exact",
    "hash_probe_matches_prefrozen_reference",
    "system_only_sys_path_exact",
    "site_module_absent",
    "native_argv_structural_tail_exact",
    "application_effects_absent",
)

GATE_ORDER = (
    "parent_linked_static_closure_exact",
    "direct_file_main",
    "python_argv_exact",
    "native_argv_structural_tail_exact",
    "cwd_exact",
    "requested_environment_exact",
    "darwin_environment_normalized",
    "identity_nonprivileged_exact",
    "interpreter_exact",
    "cpython_3_11_5_exact",
    "darwin_arm64_exact",
    "python_flags_exact",
    "hash_probe_matches_prefrozen_reference",
    "system_only_sys_path_exact",
    "site_module_absent",
    "application_effects_absent",
)
FAILURE_CODES = (
    "REQUEST",
    "DIRECT_FILE_MAIN",
    "PYTHON_ARGV",
    "NATIVE_ARGV",
    "CWD",
    "REQUESTED_ENVIRONMENT",
    "DARWIN_ENVIRONMENT",
    "IDENTITY",
    "INTERPRETER",
    "PYTHON_VERSION",
    "PLATFORM",
    "PYTHON_FLAGS",
    "HASH_PROBE",
    "SYS_PATH",
    "SITE_MODULE",
    "APPLICATION_EFFECT",
)


class ChildError(RuntimeError):
    """Privacy-safe child refusal."""


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ChildError("CHILD_CONTRACT") from exc


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _entry_present(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


REQUESTED_ENVIRONMENT_POLICY_SHA256 = _sha(_canonical(REQUESTED_ENVIRONMENT))
EXPECTED_PROFILE_SHA256 = _sha(
    _canonical(
        {
            "cpython_version": [3, 11, 5],
            "expected_sys_path": list(EXPECTED_SYS_PATH),
            "platform": ["Darwin", "arm64"],
            "python_flags": list(PYTHON_FLAGS),
            "python_realpath": str(PYTHON_REALPATH),
        }
    )
)


def _sha_value(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ChildError(label)
    return value


def _parse_request(raw: bytes) -> dict[str, Any]:
    if type(raw) is not bytes or not raw.endswith(b"\n") or raw.count(b"\n") != 1:
        raise ChildError("REQUEST")
    try:
        value = json.loads(raw[:-1].decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ChildError("REQUEST") from exc
    fields = {
        "schema_version",
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "registration_record_sha256",
        "registration_raw_sha256",
        "execution_authorization_record_sha256",
        "execution_authorization_raw_sha256",
        "admission_event_sha256",
        "child_launch_ordinal",
        "requested_environment_policy_sha256",
        "expected_profile_sha256",
        "expected_hash_probe_sha256",
        "raw_environment_requested",
        "network_requested",
        "workspace_write_requested",
        "temporary_write_requested",
        "scientific_import_or_execution_requested",
        "request_sha256",
    }
    if type(value) is not dict or set(value) != fields or _canonical(value) + b"\n" != raw:
        raise ChildError("REQUEST")
    if value["schema_version"] != REQUEST_SCHEMA:
        raise ChildError("REQUEST")
    for key in (
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "registration_record_sha256",
        "registration_raw_sha256",
        "execution_authorization_record_sha256",
        "execution_authorization_raw_sha256",
        "admission_event_sha256",
        "requested_environment_policy_sha256",
        "expected_profile_sha256",
        "expected_hash_probe_sha256",
        "request_sha256",
    ):
        _sha_value(value[key], "REQUEST")
    body = dict(value)
    claimed = body.pop("request_sha256")
    if claimed != _sha(_canonical(body)):
        raise ChildError("REQUEST")
    if type(value["child_launch_ordinal"]) is not int or value[
        "child_launch_ordinal"
    ] != 0:
        raise ChildError("REQUEST")
    if (
        value["requested_environment_policy_sha256"]
        != REQUESTED_ENVIRONMENT_POLICY_SHA256
        or value["expected_profile_sha256"] != EXPECTED_PROFILE_SHA256
        or value["expected_hash_probe_sha256"] != HASH_PROBE_SHA256
    ):
        raise ChildError("REQUEST")
    for key in (
        "raw_environment_requested",
        "network_requested",
        "workspace_write_requested",
        "temporary_write_requested",
        "scientific_import_or_execution_requested",
    ):
        if value[key] is not False:
            raise ChildError("REQUEST")
    return value


def _leaf_identity(status: os.stat_result) -> tuple[int, ...]:
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


def _read_record(
    path: Path, mode: int, self_key: str, maximum: int = 1 << 20
) -> tuple[bytes, dict[str, Any]]:
    before_path = path.lstat()
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != mode
        or before_path.st_nlink != 1
    ):
        raise ChildError("REQUEST")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(str(path), flags)
    try:
        before = os.fstat(descriptor)
        if _leaf_identity(before) != _leaf_identity(before_path):
            raise ChildError("REQUEST")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65536, maximum + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > maximum:
                raise ChildError("REQUEST")
        raw = b"".join(chunks)
        if len(raw) != before.st_size:
            raise ChildError("REQUEST")
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    if (
        _leaf_identity(before) != _leaf_identity(after)
        or _leaf_identity(after) != _leaf_identity(after_path)
    ):
        raise ChildError("REQUEST")
    if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
        raise ChildError("REQUEST")
    try:
        value = json.loads(raw[:-1].decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ChildError("REQUEST") from exc
    if type(value) is not dict or _canonical(value) + b"\n" != raw:
        raise ChildError("REQUEST")
    self_digest = value.get(self_key)
    _sha_value(self_digest, "REQUEST")
    body = dict(value)
    body.pop(self_key)
    if self_digest != _sha(_canonical(body)):
        raise ChildError("REQUEST")
    return raw, value


def _read_static_record(path: Path) -> tuple[bytes, dict[str, Any]]:
    return _read_record(path, 0o644, "record_sha256")


def _static_closure_exact(request: Mapping[str, Any]) -> bool:
    try:
        machine_raw, machine = _read_static_record(MACHINE_PATH)
        authorization_raw, authorization = _read_static_record(AUTHORIZATION_PATH)
        runtime_raw = _read_raw_file(MODULE_PATH, 0o644)
        root_status = WORKSPACE_ROOT.lstat()
        actual_anchor = {
            "device": root_status.st_dev,
            "inode": root_status.st_ino,
            "type_code": "DIRECTORY" if stat.S_ISDIR(root_status.st_mode) else "OTHER",
            "mode_octal": format(stat.S_IMODE(root_status.st_mode), "04o"),
            "uid": root_status.st_uid,
            "gid": root_status.st_gid,
        }
        runtime_rows = [
            row
            for row in machine.get("registration_bindings", [])
            if type(row) is dict and row.get("role") == "ENVIRONMENT_CHILD"
        ]
    except Exception:
        return False
    authorization_forbidden_false = all(
        authorization.get(key) is False
        for key in (
            "entropy_authorized",
            "network_authorized",
            "runtime_approval_authorized",
            "rank_authorized",
            "training_authorized",
            "production_authorized",
            "scientific_execution_authorized",
            "manuscript_claim_authorized",
            "cryptographic_user_authentication",
            "record_self_digests_are_user_authentication",
            "malicious_host_resistance_claimed",
        )
    )
    return (
        _sha(machine_raw) == request["registration_raw_sha256"]
        and machine["record_sha256"] == request["registration_record_sha256"]
        and _sha(authorization_raw)
        == request["execution_authorization_raw_sha256"]
        and authorization["record_sha256"]
        == request["execution_authorization_record_sha256"]
        and authorization.get("v4_registration_record_sha256")
        == request["registration_record_sha256"]
        and authorization.get("v4_registration_raw_sha256")
        == request["registration_raw_sha256"]
        and authorization.get("schema_version")
        == (
            "heterodiff-manuscript-v3-a1-r1-activation-preparation-v4-"
            "execution-authorization-v1"
        )
        and authorization.get("authorization_context_sha256")
        == "3e989c3935c829a5920992b29de6001369c29c9fb25f686eb44ee48be6026417"
        and authorization.get("normalized_visible_assent_sha256")
        == "33c38693197abe2849d02736250138322c452c4294552258757cfd5ae3a77994"
        and authorization.get("authorized_action") == "V4_EXECUTE_ONCE"
        and type(authorization.get("authorized_attempt_count")) is int
        and authorization.get("authorized_attempt_count") == 1
        and type(authorization.get("authorized_child_launch_maximum")) is int
        and authorization.get("authorized_child_launch_maximum") == 1
        and type(authorization.get("retry_count_authorized")) is int
        and authorization.get("retry_count_authorized") == 0
        and authorization.get("deterministic_nonce") is True
        and authorization.get("honest_host_procedural_authority") is True
        and authorization_forbidden_false
        and machine.get("schema_version")
        == (
            "heterodiff-manuscript-v3-a1-r1-activation-preparation-v4-"
            "transition-safe-live-host-environment-rehearsal-freeze-v1"
        )
        and machine.get("global_state") == "DRAFT_NOT_EXECUTABLE"
        and machine.get("workspace_anchor") == actual_anchor
        and not stat.S_ISLNK(root_status.st_mode)
        and len(runtime_rows) == 1
        and runtime_rows[0].get("path")
        == str(MODULE_PATH.relative_to(WORKSPACE_ROOT))
        and runtime_rows[0].get("raw_sha256") == _sha(runtime_raw)
        and type(runtime_rows[0].get("bytes")) is int
        and runtime_rows[0].get("bytes") == len(runtime_raw)
        and runtime_rows[0].get("mode_octal") == "0644"
        and type(runtime_rows[0].get("nlink")) is int
        and runtime_rows[0].get("nlink") == 1
    )


def _read_raw_file(path: Path, mode: int, maximum: int = 1 << 20) -> bytes:
    before_path = path.lstat()
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != mode
        or before_path.st_nlink != 1
    ):
        raise ChildError("REQUEST")
    descriptor = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before_fd = os.fstat(descriptor)
        if _leaf_identity(before_fd) != _leaf_identity(before_path):
            raise ChildError("REQUEST")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65536, maximum + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > maximum:
                raise ChildError("REQUEST")
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    raw = b"".join(chunks)
    if (
        _leaf_identity(before_fd) != _leaf_identity(after_fd)
        or _leaf_identity(after_fd) != _leaf_identity(after_path)
        or len(raw) != before_fd.st_size
    ):
        raise ChildError("REQUEST")
    return raw


def _stable_directory_names(path: Path) -> tuple[str, ...]:
    before_path = path.lstat()
    if (
        not stat.S_ISDIR(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != 0o700
    ):
        raise ChildError("REQUEST")
    descriptor = os.open(
        str(path),
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        before_fd = os.fstat(descriptor)
        if _leaf_identity(before_fd) != _leaf_identity(before_path):
            raise ChildError("REQUEST")
        names = os.listdir(descriptor)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    if (
        any(type(name) is not str or not name or "/" in name for name in names)
        or len(names) != len(set(names))
        or _leaf_identity(before_fd) != _leaf_identity(after_fd)
        or _leaf_identity(after_fd) != _leaf_identity(after_path)
    ):
        raise ChildError("REQUEST")
    return tuple(sorted(names))


def _common_event_exact(
    event: Mapping[str, Any],
    marker: Mapping[str, Any],
    marker_raw: bytes,
    request: Mapping[str, Any],
    ordinal: int,
    kind: str,
    previous_kind: str,
    previous_raw: bytes,
    previous_self: str,
    fallback: str,
) -> bool:
    fixed = {
        "event_ordinal": ordinal,
        "event_kind": kind,
        "attempt_id_sha256": request["attempt_id_sha256"],
        "attempt_nonce_sha256": request["attempt_nonce_sha256"],
        "registration_record_sha256": request["registration_record_sha256"],
        "registration_raw_sha256": request["registration_raw_sha256"],
        "marker_raw_sha256": _sha(marker_raw),
        "marker_sha256": marker["marker_sha256"],
        "previous_record_kind": previous_kind,
        "previous_record_raw_sha256": _sha(previous_raw),
        "previous_record_sha256": previous_self,
        "fallback_terminal_state": fallback,
        "retry_permitted": False,
    }
    return all(
        type(event.get(key)) is type(value) and event.get(key) == value
        for key, value in fixed.items()
    )


def _exact_mapping_equal(actual: Any, expected: Mapping[str, Any]) -> bool:
    return (
        type(actual) is dict
        and set(actual) == set(expected)
        and all(
            type(actual[key]) is type(value) and actual[key] == value
            for key, value in expected.items()
        )
    )


def _native_argv() -> tuple[str, ...]:
    if sys.platform != "darwin":
        return tuple(sys.argv)
    library = ctypes.CDLL(None)
    argc_pointer = library._NSGetArgc
    argc_pointer.restype = ctypes.POINTER(ctypes.c_int)
    argv_pointer = library._NSGetArgv
    argv_pointer.restype = ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))
    argc = argc_pointer().contents.value
    argv = argv_pointer().contents
    return tuple(argv[index].decode("utf-8", "strict") for index in range(argc))


def _native_tail_exact(native: Any) -> bool:
    if type(native) is not list or len(native) != len(PYTHON_FLAGS) + 3:
        return False
    argv0 = native[0]
    if type(argv0) is not str or not argv0 or not Path(argv0).is_absolute():
        return False
    expected_tail = [*PYTHON_FLAGS, str(MODULE_PATH), "--emit-child-observation"]
    return native[1:] == expected_tail


def _canonical_live_dispatch_exact() -> bool:
    try:
        return (
            __name__ == "__main__"
            and __spec__ is None
            and sys.argv == [str(MODULE_PATH), "--emit-child-observation"]
            and _native_tail_exact(list(_native_argv()))
            and Path.cwd().absolute() == WORKSPACE_ROOT
            and Path.cwd().resolve(strict=True) == WORKSPACE_ROOT
            and Path(sys.executable).absolute() == PYTHON_PATH
            and Path(sys.executable).resolve(strict=True) == PYTHON_REALPATH
            and MODULE_PATH.lstat().st_nlink == 1
            and stat.S_ISREG(MODULE_PATH.lstat().st_mode)
            and not stat.S_ISLNK(MODULE_PATH.lstat().st_mode)
        )
    except Exception:
        return False


def _claimed_child_prefix_exact(request_raw: bytes, request: Mapping[str, Any]) -> bool:
    try:
        event_names = (
            "00000000000000000000.json",
            "00000000000000000001.json",
            "00000000000000000002.json",
        )
        if (
            _stable_directory_names(PREPARATION_ROOT) != ("ledger",)
            or _stable_directory_names(LEDGER_PATH)
            != ("events", "genesis.json", "writer.lock")
            or _stable_directory_names(EVENTS_PATH) != event_names
            or _read_raw_file(LOCK_PATH, 0o600) != b""
            or _entry_present(TERMINAL_PATH)
            or _entry_present(RESULT_PATH)
        ):
            return False
        marker_raw, marker = _read_record(MARKER_PATH, 0o600, "marker_sha256")
        marker_fields = {
            "schema_version",
            "attempt_ordinal",
            "attempt_id_sha256",
            "attempt_nonce_sha256",
            "nonce_kind",
            "entropy_draw_count",
            "registration_record_sha256",
            "registration_raw_sha256",
            "execution_authorization_record_sha256",
            "execution_authorization_raw_sha256",
            "authorization_context_sha256",
            "visible_assent_sha256",
            "marker_path",
            "fallback_terminal_state",
            "retry_permitted",
            "marker_sha256",
        }
        if set(marker) != marker_fields:
            return False
        identity_body = {
            "attempt_ordinal": 0,
            "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
            "execution_authorization_raw_sha256": request[
                "execution_authorization_raw_sha256"
            ],
            "execution_authorization_record_sha256": request[
                "execution_authorization_record_sha256"
            ],
            "registration_record_sha256": request["registration_record_sha256"],
            "visible_assent_sha256": VISIBLE_ASSENT_SHA256,
        }
        attempt_id = _sha(ATTEMPT_ID_DOMAIN + _canonical(identity_body))
        marker_relative = str(MARKER_PATH.relative_to(WORKSPACE_ROOT))
        attempt_nonce = _sha(
            ATTEMPT_NONCE_DOMAIN
            + _canonical(
                {
                    "attempt_id_sha256": attempt_id,
                    "attempt_ordinal": 0,
                    "marker_path": marker_relative,
                }
            )
        )
        if (
            request["attempt_id_sha256"] != attempt_id
            or request["attempt_nonce_sha256"] != attempt_nonce
        ):
            return False
        marker_body = dict(marker)
        marker_body.pop("marker_sha256")
        if not _exact_mapping_equal(marker_body, {
            "schema_version": (
                "heterodiff-a1-r1-activation-preparation-v4-attempt-marker-v1"
            ),
            "attempt_ordinal": 0,
            "attempt_id_sha256": attempt_id,
            "attempt_nonce_sha256": attempt_nonce,
            "nonce_kind": "DETERMINISTIC_NONSECRET_CUSTODY_IDENTIFIER",
            "entropy_draw_count": 0,
            "registration_record_sha256": request["registration_record_sha256"],
            "registration_raw_sha256": request["registration_raw_sha256"],
            "execution_authorization_record_sha256": request[
                "execution_authorization_record_sha256"
            ],
            "execution_authorization_raw_sha256": request[
                "execution_authorization_raw_sha256"
            ],
            "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
            "visible_assent_sha256": VISIBLE_ASSENT_SHA256,
            "marker_path": marker_relative,
            "fallback_terminal_state": (
                "R1_A1_ACTIVATION_PREPARATION_V4_ATTEMPT_SPENT_RESERVATION_"
                "PUBLISHED_PRE_EVALUATION_TERMINAL_FALLBACK_NO_RETRY"
            ),
            "retry_permitted": False,
        }):
            return False
        genesis_raw, genesis = _read_record(
            GENESIS_PATH, 0o600, "genesis_sha256"
        )
        genesis_body = dict(genesis)
        genesis_body.pop("genesis_sha256")
        if not _exact_mapping_equal(genesis_body, {
            "schema_version": (
                "heterodiff-a1-r1-activation-preparation-v4-ledger-genesis-v1"
            ),
            "attempt_id_sha256": attempt_id,
            "attempt_nonce_sha256": attempt_nonce,
            "registration_record_sha256": request["registration_record_sha256"],
            "registration_raw_sha256": request["registration_raw_sha256"],
            "execution_authorization_record_sha256": request[
                "execution_authorization_record_sha256"
            ],
            "execution_authorization_raw_sha256": request[
                "execution_authorization_raw_sha256"
            ],
            "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
            "visible_assent_sha256": VISIBLE_ASSENT_SHA256,
            "marker_raw_sha256": _sha(marker_raw),
            "marker_sha256": marker["marker_sha256"],
            "event_count_before_genesis": 0,
            "global_state": "DRAFT_NOT_EXECUTABLE",
            "retry_permitted": False,
        }):
            return False
        event_raws: list[bytes] = []
        events: list[dict[str, Any]] = []
        for name in event_names:
            raw, event = _read_record(
                EVENTS_PATH / name, 0o600, "event_sha256"
            )
            event_raws.append(raw)
            events.append(event)
        event_zero, admission, child_claim = events
        common_fields = {
            "schema_version",
            "event_ordinal",
            "event_kind",
            "attempt_id_sha256",
            "attempt_nonce_sha256",
            "registration_record_sha256",
            "registration_raw_sha256",
            "marker_raw_sha256",
            "marker_sha256",
            "previous_record_kind",
            "previous_record_raw_sha256",
            "previous_record_sha256",
            "fallback_terminal_state",
            "retry_permitted",
            "event_sha256",
        }
        if (
            set(event_zero) != common_fields
            or event_zero.get("schema_version")
            != (
                "heterodiff-a1-r1-activation-preparation-v4-prechild-"
                "evaluation-claim-v1"
            )
            or not _common_event_exact(
                event_zero,
                marker,
                marker_raw,
                request,
                0,
                "PRECHILD_EVALUATION_CLAIM",
                "GENESIS",
                genesis_raw,
                genesis["genesis_sha256"],
                (
                    "R1_A1_ACTIVATION_PREPARATION_V4_ATTEMPT_SPENT_PRECHILD_"
                    "EVALUATION_CLAIMED_TERMINAL_FALLBACK_NO_RETRY"
                ),
            )
        ):
            return False
        admission_fields = common_fields | {
            "gate_vector",
            "gate_vector_sha256",
            "failure_code",
            "child_launch_count",
            "runtime_approval_created",
            "scientific_execution_performed",
        }
        gates = admission.get("gate_vector")
        if (
            set(admission) != admission_fields
            or admission.get("schema_version")
            != (
                "heterodiff-a1-r1-activation-preparation-v4-prechild-admission-v1"
            )
            or not _common_event_exact(
                admission,
                marker,
                marker_raw,
                request,
                1,
                "PRECHILD_ADMISSION",
                "EVENT",
                event_raws[0],
                event_zero["event_sha256"],
                (
                    "R1_A1_ACTIVATION_PREPARATION_V4_TERMINAL_PRECHILD_"
                    "ADMISSION_WITHOUT_CHILD_CLAIM_NO_RETRY_NOT_EXECUTABLE"
                ),
            )
            or type(gates) is not dict
            or set(gates) != set(PRECHILD_GATE_ORDER)
            or any(gates[name] is not True for name in PRECHILD_GATE_ORDER)
            or admission.get("gate_vector_sha256") != _sha(_canonical(gates))
            or admission.get("failure_code") != "NONE"
            or type(admission.get("child_launch_count")) is not int
            or admission.get("child_launch_count") != 0
            or admission.get("runtime_approval_created") is not False
            or admission.get("scientific_execution_performed") is not False
            or request["admission_event_sha256"] != admission["event_sha256"]
        ):
            return False
        child_fields = common_fields | {
            "admission_event_raw_sha256",
            "admission_event_sha256",
            "runtime_request",
            "runtime_request_raw_sha256",
            "runtime_request_sha256",
            "child_launch_ordinal",
            "child_launch_maximum",
        }
        nested_request = child_claim.get("runtime_request")
        nested_request_raw = (
            _canonical(nested_request) + b"\n"
            if type(nested_request) is dict
            else b""
        )
        if (
            set(child_claim) != child_fields
            or child_claim.get("schema_version")
            != (
                "heterodiff-a1-r1-activation-preparation-v4-child-launch-claim-v1"
            )
            or not _common_event_exact(
                child_claim,
                marker,
                marker_raw,
                request,
                2,
                "CHILD_LAUNCH_CLAIM",
                "EVENT",
                event_raws[1],
                admission["event_sha256"],
                (
                    "R1_A1_ACTIVATION_PREPARATION_V4_CHILD_LAUNCH_CLAIMED_"
                    "TERMINAL_FALLBACK_NO_RETRY"
                ),
            )
            or child_claim.get("admission_event_raw_sha256")
            != _sha(event_raws[1])
            or child_claim.get("admission_event_sha256")
            != admission["event_sha256"]
            or nested_request_raw != request_raw
            or child_claim.get("runtime_request_raw_sha256")
            != _sha(nested_request_raw)
            or child_claim.get("runtime_request_raw_sha256") != _sha(request_raw)
            or child_claim.get("runtime_request_sha256")
            != request["request_sha256"]
            or type(child_claim.get("child_launch_ordinal")) is not int
            or child_claim.get("child_launch_ordinal") != 0
            or type(child_claim.get("child_launch_maximum")) is not int
            or child_claim.get("child_launch_maximum") != 1
        ):
            return False
        return (
            _stable_directory_names(PREPARATION_ROOT) == ("ledger",)
            and _stable_directory_names(LEDGER_PATH)
            == ("events", "genesis.json", "writer.lock")
            and _stable_directory_names(EVENTS_PATH) == event_names
            and _read_raw_file(LOCK_PATH, 0o600) == b""
            and _read_raw_file(MARKER_PATH, 0o600) == marker_raw
            and _read_raw_file(GENESIS_PATH, 0o600) == genesis_raw
            and all(
                _read_raw_file(EVENTS_PATH / name, 0o600) == raw
                for name, raw in zip(event_names, event_raws)
            )
            and not _entry_present(TERMINAL_PATH)
            and not _entry_present(RESULT_PATH)
        )
    except Exception:
        return False


def _failure_code(gates: Mapping[str, bool]) -> str:
    for name, code in zip(GATE_ORDER, FAILURE_CODES):
        if gates[name] is not True:
            return code
    return "NONE"


def _hash_probe() -> str:
    return _sha(_canonical([hash(value) for value in HASH_PROBE_STRINGS]))


def evaluate_snapshot(
    snapshot: Mapping[str, Any], request_raw_sha256: str, request_sha256: str
) -> dict[str, Any]:
    """Evaluate a synthetic or live snapshot without retaining raw values."""

    if type(snapshot) is not dict:
        raise ChildError("CHILD_CONTRACT")
    environment = snapshot.get("environment")
    if type(environment) is not dict or any(
        type(key) is not str or type(value) is not str
        for key, value in environment.items()
    ):
        raise ChildError("REQUESTED_ENVIRONMENT")
    normalized = dict(environment)
    injected = normalized.pop(DARWIN_KEY, None)
    ids = tuple(snapshot.get(name) for name in ("uid", "euid", "gid", "egid"))
    ids_exact = all(type(value) is int and value >= 0 for value in ids)
    uid, euid, gid, egid = ids
    expected_injected = "0x%X:0x0:0x0" % uid if ids_exact else None
    flags = snapshot.get("flags") if type(snapshot.get("flags")) is dict else {}
    sys_path = snapshot.get("sys_path") if type(snapshot.get("sys_path")) is list else []
    effects_absent = all(
        snapshot.get(name) is False
        for name in (
            "entropy_contacted",
            "network_contacted",
            "workspace_write_performed",
            "temporary_write_performed",
            "scientific_import_or_execution_performed",
        )
    )
    gates = {
        "parent_linked_static_closure_exact": snapshot.get(
            "parent_linked_static_closure_exact"
        )
        is True,
        "direct_file_main": snapshot.get("name") == "__main__"
        and snapshot.get("spec_is_none") is True,
        "python_argv_exact": snapshot.get("python_argv")
        == [str(MODULE_PATH), "--emit-child-observation"],
        "native_argv_structural_tail_exact": _native_tail_exact(
            snapshot.get("native_argv")
        ),
        "cwd_exact": snapshot.get("cwd") == str(WORKSPACE_ROOT),
        "requested_environment_exact": normalized == REQUESTED_ENVIRONMENT,
        "darwin_environment_normalized": ids_exact
        and injected is not None
        and injected == expected_injected
        and snapshot.get("darwin_key_removed_from_actual_environment") is True
        and snapshot.get("actual_environment_equals_requested16") is True,
        "identity_nonprivileged_exact": ids_exact
        and uid == euid
        and gid == egid
        and uid != 0
        and gid != 0
        and snapshot.get("supplemental_root_group_absent") is True
        and snapshot.get("process_taint_absent") is True,
        "interpreter_exact": snapshot.get("executable") == str(PYTHON_PATH)
        and snapshot.get("executable_realpath") == str(PYTHON_REALPATH),
        "cpython_3_11_5_exact": snapshot.get("implementation") == "CPython"
        and snapshot.get("version_info") == [3, 11, 5],
        "darwin_arm64_exact": snapshot.get("platform") == ["Darwin", "arm64"],
        "python_flags_exact": flags
        == {
            "dont_write_bytecode": 1,
            "hash_randomization": 0,
            "ignore_environment": 0,
            "isolated": 0,
            "no_site": 1,
            "no_user_site": 1,
            "safe_path": True,
            "utf8_mode": 1,
            "pycache_prefix_is_dev_null": True,
        },
        "hash_probe_matches_prefrozen_reference": snapshot.get("hash_probe_sha256")
        == HASH_PROBE_SHA256,
        "system_only_sys_path_exact": sys_path == list(EXPECTED_SYS_PATH)
        and all(
            type(item) is str
            and item.startswith(
                "/Library/Frameworks/Python.framework/Versions/3.11/"
            )
            for item in sys_path
        ),
        "site_module_absent": snapshot.get("site_imported") is False,
        "application_effects_absent": effects_absent,
    }
    failure = _failure_code(gates)
    observation = {
        "schema_version": OBSERVATION_SCHEMA,
        "request_raw_sha256": _sha_value(request_raw_sha256, "REQUEST"),
        "request_sha256": _sha_value(request_sha256, "REQUEST"),
        "child_launch_ordinal": 0,
        "child_process_ordinal": 0,
        "gate_vector": gates,
        "gate_vector_sha256": _sha(_canonical(gates)),
        "failure_code": failure,
        "outcome": "PASS" if failure == "NONE" else "FAIL",
        "prefrozen_hash_probe_sha256": HASH_PROBE_SHA256,
        "hash_probe_matches_prefrozen_reference": gates[
            "hash_probe_matches_prefrozen_reference"
        ],
        "effective_environment_key_count": len(environment),
        "darwin_injected_key_present_before_normalization": injected is not None,
        "darwin_injected_value_formula_matches_uid": ids_exact
        and injected is not None
        and injected == expected_injected,
        "darwin_injected_removed_from_process_environment": snapshot.get(
            "darwin_key_removed_from_actual_environment"
        )
        is True,
        "application_effect_claim_basis": (
            "STATIC_CHILD_SOURCE_AND_ROUTE_CONTRACT_NOT_OS_INSTRUMENTATION"
        ),
        "raw_environment_emitted": False,
        "raw_identity_emitted": False,
        "raw_absolute_path_emitted": False,
        "raw_argv_emitted": False,
        "raw_stderr_emitted": False,
        "entropy_contacted": False,
        "network_contacted": False,
        "workspace_write_performed": False,
        "temporary_write_performed": False,
        "scientific_import_or_execution_performed": False,
    }
    observation["observation_sha256"] = _sha(_canonical(observation))
    return observation


def _live_invocation_exact(
    request_payload: bytes, request: Mapping[str, Any]
) -> bool:
    return (
        _canonical_live_dispatch_exact()
        and _static_closure_exact(request)
        and _claimed_child_prefix_exact(request_payload, request)
        and _canonical_live_dispatch_exact()
        and _static_closure_exact(request)
        and _claimed_child_prefix_exact(request_payload, request)
        and _canonical_live_dispatch_exact()
    )


def _live_snapshot(
    request_payload: bytes, request: Mapping[str, Any]
) -> dict[str, Any]:
    if not _live_invocation_exact(request_payload, request):
        raise ChildError("REQUEST")
    flags = {
        "dont_write_bytecode": int(sys.dont_write_bytecode),
        "hash_randomization": getattr(sys.flags, "hash_randomization", -1),
        "ignore_environment": getattr(sys.flags, "ignore_environment", -1),
        "isolated": getattr(sys.flags, "isolated", -1),
        "no_site": getattr(sys.flags, "no_site", -1),
        "no_user_site": getattr(sys.flags, "no_user_site", -1),
        "safe_path": bool(getattr(sys.flags, "safe_path", False)),
        "utf8_mode": getattr(sys.flags, "utf8_mode", -1),
        "pycache_prefix_is_dev_null": getattr(sys, "pycache_prefix", None)
        == "/dev/null",
    }
    uname = os.uname()
    if sys.platform == "darwin":
        issetugid = ctypes.CDLL(None).issetugid
        issetugid.restype = ctypes.c_int
        process_taint_absent = issetugid() == 0
    else:
        process_taint_absent = False
    return {
        "parent_linked_static_closure_exact": True,
        "environment": dict(os.environ),
        "uid": os.getuid(),
        "euid": os.geteuid(),
        "gid": os.getgid(),
        "egid": os.getegid(),
        "supplemental_root_group_absent": 0 not in os.getgroups(),
        "process_taint_absent": process_taint_absent,
        "name": __name__,
        "spec_is_none": __spec__ is None,
        "python_argv": list(sys.argv),
        "native_argv": list(_native_argv()),
        "cwd": str(Path.cwd().absolute()),
        "implementation": "CPython" if sys.implementation.name == "cpython" else "OTHER",
        "version_info": list(sys.version_info[:3]),
        "platform": [uname.sysname, uname.machine],
        "executable": str(Path(sys.executable).absolute()),
        "executable_realpath": str(Path(sys.executable).resolve(strict=True)),
        "flags": flags,
        "hash_probe_sha256": _hash_probe(),
        "sys_path": list(sys.path),
        "site_imported": "site" in sys.modules,
        "entropy_contacted": False,
        "network_contacted": False,
        "workspace_write_performed": False,
        "temporary_write_performed": False,
        "scientific_import_or_execution_performed": False,
    }


def _build_live_observation(request_payload: bytes) -> dict[str, Any]:
    request = _parse_request(request_payload)
    if not _live_invocation_exact(request_payload, request):
        raise ChildError("REQUEST")
    snapshot = _live_snapshot(request_payload, request)
    captured = snapshot["environment"]
    try:
        before_exact = type(captured) is dict and dict(os.environ) == captured
        removed = os.environ.get(DARWIN_KEY)
        if DARWIN_KEY in os.environ:
            del os.environ[DARWIN_KEY]
        snapshot["darwin_key_removed_from_actual_environment"] = (
            before_exact and removed is not None and DARWIN_KEY not in os.environ
        )
        snapshot["actual_environment_equals_requested16"] = (
            before_exact and dict(os.environ) == REQUESTED_ENVIRONMENT
        )
        request_raw_sha256 = _sha(request_payload)
        return evaluate_snapshot(
            snapshot, request_raw_sha256, request["request_sha256"]
        )
    finally:
        if type(captured) is dict:
            captured.clear()
        snapshot.clear()


def _read_stdin() -> bytes:
    payload = sys.stdin.buffer.read(MAXIMUM_STDIN_BYTES + 1)
    if len(payload) > MAXIMUM_STDIN_BYTES:
        raise ChildError("REQUEST")
    return payload


def main(arguments: Sequence[str] | None = None) -> int:
    supplied = list(sys.argv[1:] if arguments is None else arguments)
    if (
        arguments is not None
        or supplied != ["--emit-child-observation"]
        or not _canonical_live_dispatch_exact()
    ):
        return 64
    try:
        observation = _build_live_observation(_read_stdin())
        sys.stdout.buffer.write(_canonical(observation) + b"\n")
        sys.stdout.buffer.flush()
    except Exception:
        return 70
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ChildError",
    "DARWIN_KEY",
    "GATE_ORDER",
    "HASH_PROBE_SHA256",
    "HASH_PROBE_STRINGS",
    "MODULE_PATH",
    "OBSERVATION_SCHEMA",
    "PYTHON_FLAGS",
    "PYTHON_PATH",
    "PYTHON_REALPATH",
    "REQUESTED_ENVIRONMENT",
    "REQUEST_SCHEMA",
    "WORKSPACE_ROOT",
    "evaluate_snapshot",
]
