"""Dedicated stdlib-only child for the V3 live-host environment rehearsal.

The child observes only its interpreter launch profile.  It does not import
project code, inspect a capsule or installed packages, contact the network,
draw entropy, or write a file.  Its only output is one privacy-safe canonical
JSON observation on stdout; raw environment and OS identity values are never
serialized or hashed.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, Mapping, Sequence, Tuple


CHILD_OBSERVATION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v3-live-host-environment-"
    "rehearsal-child-observation-v1"
)
REQUEST_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v3-live-host-environment-"
    "rehearsal-request-v1"
)
PROFILE_ID = "M1_REFERENCE_MACOS_ARM64_PY311_V3_ENVIRONMENT_REHEARSAL"
REQUEST_DOMAIN = (REQUEST_SCHEMA + "\0").encode("ascii")
OBSERVATION_DOMAIN = (CHILD_OBSERVATION_SCHEMA + "\0").encode("ascii")

MODULE_PATH = Path(__file__).absolute()
WORKSPACE_ROOT = MODULE_PATH.parents[2]
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
EXPECTED_PYTHON_ARGV = (str(MODULE_PATH), "--emit-child-observation")
EXPECTED_NATIVE_ARGV = (
    str(PYTHON_PATH),
    *PYTHON_FLAGS,
    str(MODULE_PATH),
    "--emit-child-observation",
)
FAILURE_PRIORITY = (
    (
        "ARGV",
        ("direct_file_main", "spec_is_none", "python_argv_exact", "native_argv_exact"),
    ),
    ("CWD", ("cwd_exact",)),
    (
        "DARWIN_ENVIRONMENT",
        (
            "darwin_injected_key_present",
            "darwin_injected_value_matches_uid",
            "darwin_injected_removed_before_observation",
        ),
    ),
    (
        "EFFECTIVE_ENVIRONMENT",
        (
            "requested_environment_exact_after_normalization",
            "pythonpath_absent",
            "pythonhome_absent",
        ),
    ),
    (
        "IDENTITY",
        (
            "uid_euid_equal",
            "gid_egid_equal",
            "nonprivileged_identity",
            "supplemental_root_group_absent",
            "process_taint_absent",
        ),
    ),
    ("INTERPRETER", ("venv_executable_exact", "interpreter_realpath_exact")),
    ("PLATFORM", ("implementation_exact", "version_exact", "platform_exact")),
    ("PYTHON_FLAGS", ("python_flags_exact", "hash_randomization_disabled")),
    ("HASH_PROBE", ("hash_probe_exact",)),
    ("SYS_PATH", ("sys_path_exact", "system_only_sys_path")),
    ("SITE_MODULE", ("site_not_imported",)),
)


class RehearsalChildError(RuntimeError):
    """A privacy-safe child error with no raw environment or identity data."""


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError) as error:
        raise RehearsalChildError("INTERNAL_FAILURE") from error


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require_sha256(value: Any) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise RehearsalChildError("CHILD_STDOUT")
    return value


def _parse_request(payload: bytes) -> Dict[str, Any]:
    if type(payload) is not bytes or not payload.endswith(b"\n"):
        raise RehearsalChildError("CHILD_STDOUT")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RehearsalChildError("CHILD_STDOUT") from error
    if type(value) is not dict or _canonical(value) + b"\n" != payload:
        raise RehearsalChildError("CHILD_STDOUT")
    expected_keys = {
        "schema",
        "registration_raw_sha256",
        "registration_record_sha256",
        "human_sha256",
        "contracts_sha256",
        "authority_sha256",
        "runtime_sha256",
        "test_sha256",
        "v2_terminal_registration_record_sha256",
        "environment_policy_sha256",
        "workspace_anchor_identity_sha256",
        "profile_id",
        "rehearsal_ordinal",
        "python_relative_path",
        "python_realpath",
        "python_flags",
        "requested_environment_sha256",
        "hash_probe_sha256",
        "child_observation_schema",
        "result_schema",
        "planned_result_relative_path",
        "future_v3_marker_relative_path",
        "future_v3_preparation_root_relative_path",
        "workspace_write_requested",
        "entropy_requested",
        "network_contact_requested",
        "scientific_execution_requested",
        "request_sha256",
    }
    if set(value) != expected_keys or value.get("schema") != REQUEST_SCHEMA:
        raise RehearsalChildError("CHILD_STDOUT")
    claimed = _require_sha256(value.get("request_sha256"))
    body = dict(value)
    body["request_sha256"] = None
    if claimed != _sha256(REQUEST_DOMAIN + _canonical(body)):
        raise RehearsalChildError("CHILD_STDOUT")
    if (
        value.get("profile_id") != PROFILE_ID
        or value.get("rehearsal_ordinal") != 0
        or value.get("python_flags") != list(PYTHON_FLAGS)
        or value.get("python_realpath") != str(PYTHON_REALPATH)
        or value.get("child_observation_schema") != CHILD_OBSERVATION_SCHEMA
        or any(
            value.get(name) is not False
            for name in (
                "workspace_write_requested",
                "entropy_requested",
                "network_contact_requested",
                "scientific_execution_requested",
            )
        )
    ):
        raise RehearsalChildError("CHILD_STDOUT")
    return value


def _read_stdin() -> bytes:
    payload = sys.stdin.buffer.read(MAXIMUM_STDIN_BYTES + 1)
    if len(payload) > MAXIMUM_STDIN_BYTES:
        raise RehearsalChildError("CHILD_STDOUT")
    return payload


def _native_argv() -> Tuple[str, ...]:
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


def _hash_probe() -> str:
    values = [hash(value) for value in HASH_PROBE_STRINGS]
    return _sha256(_canonical(values))


def _failure_code(gates: Mapping[str, bool]) -> str:
    for code, names in FAILURE_PRIORITY:
        if any(gates[name] is not True for name in names):
            return code
    return "NONE"


def evaluate_snapshot(
    snapshot: Mapping[str, Any], request_sha256: str
) -> Dict[str, Any]:
    """Evaluate a synthetic or live snapshot without exposing raw values."""

    if type(snapshot) is not dict:
        raise RehearsalChildError("INTERNAL_FAILURE")
    environment = snapshot.get("environment")
    if type(environment) is not dict or any(
        type(key) is not str or type(value) is not str
        for key, value in environment.items()
    ):
        raise RehearsalChildError("EFFECTIVE_ENVIRONMENT")
    normalized = dict(environment)
    injected = normalized.pop(DARWIN_KEY, None)
    uid = snapshot.get("uid")
    euid = snapshot.get("euid")
    gid = snapshot.get("gid")
    egid = snapshot.get("egid")
    exact_integers = all(
        type(value) is int and value >= 0 for value in (uid, euid, gid, egid)
    )
    expected_injected = None
    if exact_integers:
        expected_injected = "0x%X:0x0:0x0" % uid
    flags = snapshot.get("flags")
    if type(flags) is not dict:
        flags = {}
    python_argv = snapshot.get("python_argv")
    native_argv = snapshot.get("native_argv")
    hash_probe = snapshot.get("hash_probe_sha256")
    sys_path = snapshot.get("sys_path")
    if type(sys_path) is not list:
        sys_path = []
    forbidden_prefix_count = sum(
        1
        for key in normalized
        if key.startswith(("DYLD_", "AWS_", "GITHUB_", "GOOGLE_", "OPENAI_", "SSH_"))
    )
    gates = {
        "direct_file_main": snapshot.get("name") == "__main__",
        "spec_is_none": snapshot.get("spec_is_none") is True,
        "python_argv_exact": python_argv == list(EXPECTED_PYTHON_ARGV),
        "native_argv_exact": native_argv == list(EXPECTED_NATIVE_ARGV),
        "cwd_exact": snapshot.get("cwd") == str(WORKSPACE_ROOT),
        "requested_environment_exact_after_normalization": normalized
        == REQUESTED_ENVIRONMENT
        and snapshot.get("actual_environment_normalized_after_capture") is True,
        "darwin_injected_key_present": injected is not None,
        "darwin_injected_value_matches_uid": injected is not None
        and injected == expected_injected,
        "darwin_injected_removed_before_observation": snapshot.get(
            "actual_darwin_key_removed_before_observation"
        )
        is True,
        "uid_euid_equal": exact_integers and uid == euid,
        "gid_egid_equal": exact_integers and gid == egid,
        "nonprivileged_identity": exact_integers and uid != 0 and gid != 0,
        "implementation_exact": snapshot.get("implementation") == "CPython",
        "version_exact": snapshot.get("version_info") == [3, 11, 5],
        "platform_exact": snapshot.get("platform") == ["Darwin", "arm64"],
        "venv_executable_exact": snapshot.get("executable") == str(PYTHON_PATH),
        "interpreter_realpath_exact": snapshot.get("executable_realpath")
        == str(PYTHON_REALPATH),
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
        "hash_randomization_disabled": flags.get("hash_randomization") == 0,
        "hash_probe_exact": hash_probe == HASH_PROBE_SHA256,
        "sys_path_exact": sys_path == list(EXPECTED_SYS_PATH),
        "system_only_sys_path": len(sys_path) == len(EXPECTED_SYS_PATH)
        and all(
            type(item) is str
            and item.startswith("/Library/Frameworks/Python.framework/Versions/3.11/")
            for item in sys_path
        ),
        "supplemental_root_group_absent": snapshot.get("supplemental_root_group_absent")
        is True,
        "process_taint_absent": snapshot.get("process_taint_absent") is True,
        "site_not_imported": snapshot.get("site_imported") is False,
        "pythonpath_absent": "PYTHONPATH" not in normalized,
        "pythonhome_absent": "PYTHONHOME" not in normalized,
    }
    failure_code = _failure_code(gates)
    success = failure_code == "NONE" and forbidden_prefix_count == 0
    body = {
        "schema": CHILD_OBSERVATION_SCHEMA,
        "request_sha256": _require_sha256(request_sha256),
        "profile_id": PROFILE_ID,
        "outcome": "PASS" if success else "FAIL",
        "failure_code": failure_code,
        "direct_file_main": gates["direct_file_main"],
        "spec_is_none": gates["spec_is_none"],
        "python_argv_exact": gates["python_argv_exact"],
        "native_argv_exact": gates["native_argv_exact"],
        "cwd_exact": gates["cwd_exact"],
        "requested_environment_key_count": len(REQUESTED_ENVIRONMENT),
        "effective_environment_key_count": len(environment),
        "requested_environment_exact_after_normalization": gates[
            "requested_environment_exact_after_normalization"
        ],
        "darwin_injected_key_present": gates["darwin_injected_key_present"],
        "darwin_injected_value_matches_uid": gates["darwin_injected_value_matches_uid"],
        "darwin_injected_removed_before_observation": gates[
            "darwin_injected_removed_before_observation"
        ],
        "uid_euid_equal": gates["uid_euid_equal"],
        "gid_egid_equal": gates["gid_egid_equal"],
        "nonprivileged_identity": gates["nonprivileged_identity"],
        "supplemental_root_group_absent": gates["supplemental_root_group_absent"],
        "process_taint_absent": gates["process_taint_absent"],
        "implementation_code": "CPYTHON" if gates["implementation_exact"] else "OTHER",
        "version_code": "CPYTHON_3_11_5" if gates["version_exact"] else "OTHER",
        "platform_code": "DARWIN_ARM64" if gates["platform_exact"] else "OTHER",
        "venv_executable_exact": gates["venv_executable_exact"],
        "interpreter_realpath_exact": gates["interpreter_realpath_exact"],
        "python_flags_exact": gates["python_flags_exact"],
        "hash_randomization_disabled": gates["hash_randomization_disabled"],
        "hash_probe_sha256": HASH_PROBE_SHA256,
        "hash_probe_matches_prefrozen_reference": gates["hash_probe_exact"],
        "sys_path_exact": gates["sys_path_exact"],
        "system_only_sys_path": gates["system_only_sys_path"],
        "pythonpath_absent": gates["pythonpath_absent"],
        "pythonhome_absent": gates["pythonhome_absent"],
        "dyld_key_count": sum(1 for key in environment if key.startswith("DYLD_")),
        "credential_key_count": sum(
            1
            for key in environment
            if key in {"HOME", "SSH_AUTH_SOCK", "USER"}
            or key.startswith(("AWS_", "GITHUB_", "GOOGLE_", "OPENAI_", "SSH_"))
        ),
        "site_imported": snapshot.get("site_imported") is True,
        "entropy_contacted": False,
        "network_contacted": False,
        "scientific_imports_performed": False,
        "workspace_write_performed": False,
        "temporary_write_performed": False,
        "raw_environment_emitted": False,
        "raw_identity_emitted": False,
        "observation_sha256": None,
    }
    body["observation_sha256"] = _sha256(OBSERVATION_DOMAIN + _canonical(body))
    return body


def live_snapshot() -> Dict[str, Any]:
    """Capture only the exact launch-profile facts needed by the policy."""

    flags = {
        "dont_write_bytecode": int(sys.dont_write_bytecode),
        "hash_randomization": getattr(sys.flags, "hash_randomization", -1),
        "ignore_environment": getattr(sys.flags, "ignore_environment", -1),
        "isolated": getattr(sys.flags, "isolated", -1),
        "no_site": getattr(sys.flags, "no_site", -1),
        "no_user_site": getattr(sys.flags, "no_user_site", -1),
        "safe_path": getattr(sys.flags, "safe_path", False),
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
        "implementation": (
            "CPython" if sys.implementation.name == "cpython" else "OTHER"
        ),
        "version_info": list(sys.version_info[:3]),
        "platform": [uname.sysname, uname.machine],
        "executable": str(Path(sys.executable).absolute()),
        "executable_realpath": str(Path(sys.executable).resolve(strict=True)),
        "flags": flags,
        "hash_probe_sha256": _hash_probe(),
        "sys_path": list(sys.path),
        "site_imported": "site" in sys.modules,
    }


def build_live_observation(request_payload: bytes) -> Dict[str, Any]:
    request = _parse_request(request_payload)
    snapshot = live_snapshot()
    captured_environment = snapshot["environment"]
    uid = snapshot["uid"]
    expected_injected = "0x%X:0x0:0x0" % uid if type(uid) is int else None
    actual_before_matches_capture = (
        type(captured_environment) is dict and dict(os.environ) == captured_environment
    )
    removed = os.environ.get(DARWIN_KEY)
    if DARWIN_KEY in os.environ:
        del os.environ[DARWIN_KEY]
    snapshot["actual_darwin_key_removed_before_observation"] = (
        actual_before_matches_capture
        and removed is not None
        and removed == captured_environment.get(DARWIN_KEY)
        and DARWIN_KEY not in os.environ
    )
    snapshot["actual_environment_normalized_after_capture"] = (
        actual_before_matches_capture
        and removed == expected_injected
        and dict(os.environ) == REQUESTED_ENVIRONMENT
        and DARWIN_KEY not in os.environ
    )
    observation = evaluate_snapshot(snapshot, request["request_sha256"])
    # Erase the only in-memory raw environment carrier before returning.
    snapshot["environment"].clear()
    return observation


def main(arguments: Sequence[str] | None = None) -> int:
    supplied = list(sys.argv[1:] if arguments is None else arguments)
    if supplied != ["--emit-child-observation"]:
        return 64
    try:
        observation = build_live_observation(_read_stdin())
    except Exception:
        # No raw values, exception text, or traceback may reach stderr/stdout.
        return 70
    sys.stdout.buffer.write(_canonical(observation) + b"\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CHILD_OBSERVATION_SCHEMA",
    "DARWIN_KEY",
    "EXPECTED_NATIVE_ARGV",
    "EXPECTED_PYTHON_ARGV",
    "EXPECTED_SYS_PATH",
    "HASH_PROBE_SHA256",
    "HASH_PROBE_STRINGS",
    "MODULE_PATH",
    "PROFILE_ID",
    "PYTHON_FLAGS",
    "PYTHON_PATH",
    "PYTHON_REALPATH",
    "REQUESTED_ENVIRONMENT",
    "REQUEST_SCHEMA",
    "RehearsalChildError",
    "WORKSPACE_ROOT",
    "build_live_observation",
    "evaluate_snapshot",
    "live_snapshot",
    "main",
]
