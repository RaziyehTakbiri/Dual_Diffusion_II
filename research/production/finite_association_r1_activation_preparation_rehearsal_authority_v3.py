"""Read-only supervisor for the V3 live-host environment rehearsal.

This module implements one exact direct-file rehearsal route.  It has no
marker writer, nonce source, capsule materializer, authority ledger, runtime
approval, or scientific launcher.  The route launches one dedicated stdlib
child, emits one typed privacy-safe result on stdout, and writes no application
file.  One-shot behavior before result publication is procedural, not a
mechanical replay boundary.
"""

from __future__ import annotations

import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import sys
import time
from types import ModuleType
from typing import Any, Dict, Mapping, Sequence, Tuple


MODULE_PATH = Path(__file__).absolute()
WORKSPACE_ROOT = MODULE_PATH.parents[2]
HUMAN_PATH = (
    "manuscript_v3/"
    "a1_r1_activation_preparation_v3_live_host_environment_rehearsal_freeze_v1.md"
)
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v3_live_host_"
    "environment_rehearsal_freeze_v1.json"
)
CONTRACTS_PATH = (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_contracts_v3.py"
)
AUTHORITY_PATH = (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_authority_v3.py"
)
RUNTIME_PATH = (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_runtime_v3.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_a1_r1_activation_preparation_v3_live_host_"
    "environment_rehearsal_freeze_v1.py"
)
RESULT_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v3_live_host_"
    "environment_rehearsal_result_v1.json"
)
FUTURE_V3_MARKER_PATH = "artifacts/a1_r1_activation_preparation_v3.attempt.json"
FUTURE_V3_PREPARATION_ROOT = "artifacts/a1_r1_activation_preparation_v3"

POSTMORTEM_HUMAN_PATH = (
    "manuscript_v3/"
    "a1_r1_activation_preparation_v2_terminal_failure_registration_v1.md"
)
POSTMORTEM_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v2_terminal_"
    "failure_registration_v1.json"
)
POSTMORTEM_VALIDATOR_PATH = (
    "research/diagnostics/finite_association_r1_activation_preparation_v2_"
    "terminal_failure_registration_v1.py"
)
POSTMORTEM_TEST_PATH = (
    "tests/unit/test_manuscript_v3_a1_r1_activation_preparation_v2_terminal_"
    "failure_registration_v1.py"
)
POSTMORTEM_BINDINGS = (
    (
        POSTMORTEM_HUMAN_PATH,
        "c29302fadc4a5c6a81a963442c85a681c92791ad664482267e80ef6d75f546ed",
        11507,
    ),
    (
        POSTMORTEM_MACHINE_PATH,
        "bc73165ba905db1f26c5c81e2aebaf644e5e8009bd00daa477469479674d3085",
        17232,
    ),
    (
        POSTMORTEM_VALIDATOR_PATH,
        "ce59c0d855d22eea01e0091110ab6e928d071fe57ba1416f6e0ccab0e5bcf671",
        62047,
    ),
    (
        POSTMORTEM_TEST_PATH,
        "7f28086bfeaab835241296961bfc91461789cadce6780ef38009569fd2189d5f",
        19591,
    ),
)
POSTMORTEM_RECORD_SHA256 = (
    "da57dda788f5de2b2a34ed30bdaf7f692db98696a00e420aa0484d44127b6ed0"
)

REGISTRATION_SCHEMA = (
    "heterodiff-manuscript-v3-a1-r1-activation-preparation-v3-live-host-"
    "environment-rehearsal-freeze-v1"
)
QUALIFICATION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v3-live-host-environment-"
    "rehearsal-qualification-v1"
)
PROTECTED_SNAPSHOT_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v3-live-host-environment-"
    "rehearsal-protected-snapshot-v1"
)
REGISTRATION_DOMAIN = (REGISTRATION_SCHEMA + "\0").encode("ascii")
PROTECTED_ROSTER_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-v3-protected-path-roster-v1\0"
)
PROTECTED_SNAPSHOT_DOMAIN = (PROTECTED_SNAPSHOT_SCHEMA + "\0").encode("ascii")

GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
PRE_RUN_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V3_LIVE_HOST_ENVIRONMENT_REHEARSAL_"
    "IMPLEMENTATION_FROZEN_AWAITING_SINGLE_READ_ONLY_REHEARSAL_NO_MARKER_"
    "NOT_EXECUTABLE"
)
PASS_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V3_LIVE_HOST_ENVIRONMENT_REHEARSAL_PASSED_"
    "RESULT_FROZEN_NO_MARKER_NOT_EXECUTABLE"
)
FAIL_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V3_LIVE_HOST_ENVIRONMENT_REHEARSAL_FAILED_"
    "RESULT_FROZEN_MARKER_INELIGIBLE_NOT_EXECUTABLE"
)
UNVALIDATED_FUTURE_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V3_FUTURE_NAMESPACE_PRESENT_REQUIRES_"
    "ADDITIVE_SUPERSESSION_VALIDATOR_NOT_EXECUTABLE"
)
INVALID_RESULT_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V3_RESULT_PRESENT_BUT_INVALID_NOT_EXECUTABLE"
)

PROFILE_ID = "M1_REFERENCE_MACOS_ARM64_PY311_V3_ENVIRONMENT_REHEARSAL"
PYTHON_FLAGS = ("-P", "-B", "-S", "-X", "utf8")
PYTHON_RELATIVE_PATH = ".venv-m1/bin/python"
PYTHON_PATH = WORKSPACE_ROOT / PYTHON_RELATIVE_PATH
PYTHON_REALPATH = Path(
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
)
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
USER_VISIBLE_ASSENT_TEXT = "Okay, go through it."
USER_VISIBLE_ASSENT_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-v3-visible-user-assent-v1\0"
)
MAXIMUM_CHILD_STDOUT_BYTES = 64 * 1024
MAXIMUM_CHILD_STDERR_BYTES = 4 * 1024
CHILD_TIMEOUT_SECONDS = 30.0
EXPECTED_CONTRACTS_RAW_SHA256 = (
    "8ea49970e6419ef6851f511f31c88daab4a785cfd4c674700de2449533edb191"
)
EXPECTED_RUNTIME_RAW_SHA256 = (
    "1c4f729d65d585b4c38ae977f0001f97d0e8cbfa23ad566d1e9d999b370eeac6"
)

SUPERVISOR_RELATIVE_ARGV = (
    AUTHORITY_PATH,
    "--rehearse-live-host",
)
SUPERVISOR_NATIVE_ARGV = (
    PYTHON_RELATIVE_PATH,
    *PYTHON_FLAGS,
    *SUPERVISOR_RELATIVE_ARGV,
)
CHILD_ARGV = (
    str(PYTHON_PATH),
    *PYTHON_FLAGS,
    str(WORKSPACE_ROOT / RUNTIME_PATH),
    "--emit-child-observation",
)

STATIC_BINDING_PATHS = (
    ("HUMAN_REGISTRATION", HUMAN_PATH),
    ("CONTRACTS_MODULE", CONTRACTS_PATH),
    ("READ_ONLY_SUPERVISOR", AUTHORITY_PATH),
    ("ENVIRONMENT_ONLY_CHILD", RUNTIME_PATH),
    ("HOSTILE_TEST", TEST_PATH),
)
PROTECTED_PATHS = (
    (MACHINE_PATH,)
    + tuple(path for _, path in STATIC_BINDING_PATHS)
    + tuple(path for path, _, _ in POSTMORTEM_BINDINGS)
)


class RehearsalAuthorityError(RuntimeError):
    """Fail-closed V3 rehearsal error with no execution authority."""


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
        raise RehearsalAuthorityError("value is not canonical ASCII JSON") from error


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require_sha256(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise RehearsalAuthorityError(label + " must be one lowercase SHA-256")
    return value


def _path_has_entry(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _ancestor_identity(value: os.stat_result) -> Tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_uid,
        value.st_gid,
    )


def _file_identity(value: os.stat_result) -> Tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _ancestor_snapshot(path: Path) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
    rows = []
    for ancestor in reversed(path.absolute().parents):
        try:
            information = ancestor.lstat()
        except FileNotFoundError:
            break
        if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(information.st_mode):
            raise RehearsalAuthorityError("protected path has a linked ancestor")
        rows.append((ancestor.as_posix(), _ancestor_identity(information)))
    return tuple(rows)


def _read_stable_file(
    root: Path,
    relative_path: str,
    *,
    expected_mode: int = 0o644,
    expected_nlink: int = 1,
) -> Tuple[bytes, os.stat_result]:
    if (
        type(relative_path) is not str
        or not relative_path
        or relative_path.startswith("/")
        or ".." in Path(relative_path).parts
        or Path(relative_path).as_posix() != relative_path
    ):
        raise RehearsalAuthorityError("protected relative path changed")
    path = root / relative_path
    ancestors = _ancestor_snapshot(path)
    before = path.lstat()
    if (
        stat.S_ISLNK(before.st_mode)
        or not stat.S_ISREG(before.st_mode)
        or stat.S_IMODE(before.st_mode) != expected_mode
        or before.st_nlink != expected_nlink
    ):
        raise RehearsalAuthorityError("protected file type or custody changed")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    chunks = []
    try:
        opened = os.fstat(descriptor)
        if _file_identity(opened) != _file_identity(before):
            raise RehearsalAuthorityError("protected file changed before open")
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(1 << 20, remaining))
            if not chunk:
                raise RehearsalAuthorityError("protected file ended early")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise RehearsalAuthorityError("protected file grew during read")
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    if (
        ancestors != _ancestor_snapshot(path)
        or _file_identity(before) != _file_identity(after_descriptor)
        or _file_identity(after_descriptor) != _file_identity(after)
    ):
        raise RehearsalAuthorityError("protected file changed during read")
    return b"".join(chunks), after


def _load_module(name: str, path: Path) -> ModuleType:
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RehearsalAuthorityError("read-only module cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def _load_contracts() -> ModuleType:
    _bootstrap_static_bindings(WORKSPACE_ROOT)
    return _load_module(
        "finite_association_r1_activation_preparation_rehearsal_contracts_v3",
        WORKSPACE_ROOT / CONTRACTS_PATH,
    )


def _load_postmortem() -> ModuleType:
    payload, _ = _read_stable_file(WORKSPACE_ROOT, POSTMORTEM_VALIDATOR_PATH)
    expected = POSTMORTEM_BINDINGS[2]
    if len(payload) != expected[2] or _sha256(payload) != expected[1]:
        raise RehearsalAuthorityError("V2 postmortem validator changed")
    return _load_module(
        "finite_association_r1_activation_preparation_v2_terminal_failure_"
        "registration_v1_for_v3",
        WORKSPACE_ROOT / POSTMORTEM_VALIDATOR_PATH,
    )


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
    return _sha256(_canonical([hash(value) for value in HASH_PROBE_STRINGS]))


def _supervisor_snapshot() -> Dict[str, Any]:
    environment = dict(os.environ)
    normalized = dict(environment)
    injected = normalized.pop(DARWIN_KEY, None)
    uid = os.getuid()
    gid = os.getgid()
    expected_injected = "0x%X:0x0:0x0" % uid
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
    gates = {
        "supervisor_direct_file_main": __name__ == "__main__",
        "supervisor_spec_is_none": __spec__ is None,
        "supervisor_python_argv_exact": tuple(sys.argv) == SUPERVISOR_RELATIVE_ARGV,
        "supervisor_native_argv_exact": _native_argv() == SUPERVISOR_NATIVE_ARGV,
        "supervisor_environment_exact_after_normalization": (
            normalized == REQUESTED_ENVIRONMENT
            and injected == expected_injected
            and len(environment) == len(REQUESTED_ENVIRONMENT) + 1
        ),
        "supervisor_python_flags_exact": flags
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
        "supervisor_cwd_exact": Path.cwd().absolute() == WORKSPACE_ROOT,
        "supervisor_profile_exact": (
            sys.implementation.name == "cpython"
            and list(sys.version_info[:3]) == [3, 11, 5]
            and [uname.sysname, uname.machine] == ["Darwin", "arm64"]
            and Path(sys.executable).absolute() == PYTHON_PATH
            and Path(sys.executable).resolve(strict=True) == PYTHON_REALPATH
            and tuple(sys.path) == EXPECTED_SYS_PATH
            and "site" not in sys.modules
            and _hash_probe() == HASH_PROBE_SHA256
            and os.geteuid() == uid
            and os.getegid() == gid
            and uid != 0
            and gid != 0
            and 0 not in os.getgroups()
            and process_taint_absent
        ),
    }
    # The raw Darwin value and numeric identities never leave this stack frame.
    environment.clear()
    normalized.clear()
    return gates


def _require_live_supervisor_boundary() -> Dict[str, bool]:
    gates = _supervisor_snapshot()
    if any(value is not True for value in gates.values()):
        raise RehearsalAuthorityError("live supervisor boundary failed closed")
    # Normalize before loading any other project module or launching the child.
    del os.environ[DARWIN_KEY]
    if dict(os.environ) != REQUESTED_ENVIRONMENT:
        raise RehearsalAuthorityError("supervisor environment normalization failed")
    return {
        name: value for name, value in gates.items() if name.startswith("supervisor_")
    }


def _binding_row(root: Path, ordinal: int, role: str, relative: str) -> Dict[str, Any]:
    payload, information = _read_stable_file(root, relative)
    return {
        "ordinal": ordinal,
        "role": role,
        "path": relative,
        "bytes": len(payload),
        "raw_sha256": _sha256(payload),
        "lf_only": b"\r" not in payload,
        "mode_octal": "0644",
        "nlink": 1,
        "is_regular_file": stat.S_ISREG(information.st_mode),
        "is_symlink": stat.S_ISLNK(information.st_mode),
    }


def _bootstrap_static_bindings(root: Path) -> Tuple[bytes, Dict[str, Any]]:
    """Authenticate executable contract bytes before importing them."""

    payload, _ = _read_stable_file(root, MACHINE_PATH)
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RehearsalAuthorityError(
            "V3 bootstrap registration is not JSON"
        ) from error
    if (
        type(record) is not dict
        or payload != _canonical(record) + b"\n"
        or record.get("schema_version") != REGISTRATION_SCHEMA
    ):
        raise RehearsalAuthorityError("V3 bootstrap registration changed")
    claimed = _require_sha256(record.get("record_sha256"), "bootstrap registration")
    body = dict(record)
    body["record_sha256"] = None
    if claimed != _sha256(REGISTRATION_DOMAIN + _canonical(body)):
        raise RehearsalAuthorityError("V3 bootstrap registration self digest changed")
    bindings = record.get("registration_bindings")
    if type(bindings) is not list or len(bindings) != len(STATIC_BINDING_PATHS):
        raise RehearsalAuthorityError("V3 bootstrap binding roster changed")
    for ordinal, ((role, relative), row) in enumerate(
        zip(STATIC_BINDING_PATHS, bindings)
    ):
        expected = _binding_row(root, ordinal, role, relative)
        if type(row) is not dict or _canonical(row) != _canonical(expected):
            raise RehearsalAuthorityError("V3 bootstrap static bytes changed")
    contracts_row = next(row for row in bindings if row["role"] == "CONTRACTS_MODULE")
    if contracts_row["raw_sha256"] != EXPECTED_CONTRACTS_RAW_SHA256:
        raise RehearsalAuthorityError(
            "V3 executable contracts do not match audited bytes"
        )
    runtime_row = next(
        row for row in bindings if row["role"] == "ENVIRONMENT_ONLY_CHILD"
    )
    if runtime_row["raw_sha256"] != EXPECTED_RUNTIME_RAW_SHA256:
        raise RehearsalAuthorityError("V3 child does not match audited bytes")
    return payload, record


def workspace_anchor_identity(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    if root != WORKSPACE_ROOT or root.resolve(strict=True) != WORKSPACE_ROOT:
        raise RehearsalAuthorityError("workspace anchor is not canonical")
    root_info = root.lstat()
    anchor_info = (root / "pyproject.toml").lstat()
    if (
        stat.S_ISLNK(root_info.st_mode)
        or not stat.S_ISDIR(root_info.st_mode)
        or stat.S_ISLNK(anchor_info.st_mode)
        or not stat.S_ISREG(anchor_info.st_mode)
        or anchor_info.st_nlink != 1
    ):
        raise RehearsalAuthorityError("workspace anchor custody changed")
    body = {
        "schema": ("heterodiff-a1-r1-activation-preparation-v3-workspace-anchor-v1"),
        "root_identity": [
            root_info.st_dev,
            root_info.st_ino,
            root_info.st_mode,
        ],
        "pyproject_identity": [
            anchor_info.st_dev,
            anchor_info.st_ino,
            anchor_info.st_mode,
            anchor_info.st_nlink,
        ],
        "contains_no_path_uid_gid_or_cf_value": True,
        "publication_inclusion_permitted": False,
    }
    return {
        **body,
        "identity_sha256": _sha256(
            b"heterodiff-a1-r1-activation-preparation-v3-workspace-anchor-v1\0"
            + _canonical(body)
        ),
    }


def protected_path_roster() -> Dict[str, Any]:
    body = {
        "schema": (
            "heterodiff-a1-r1-activation-preparation-v3-protected-path-roster-v1"
        ),
        "paths": list(PROTECTED_PATHS),
        "path_count": len(PROTECTED_PATHS),
        "v2_terminal_marker_path": "artifacts/a1_r1_activation_preparation_v2.attempt.json",
        "v2_terminal_root": "artifacts/a1_r1_activation_preparation_v2",
        "future_v3_marker_path": FUTURE_V3_MARKER_PATH,
        "future_v3_preparation_root": FUTURE_V3_PREPARATION_ROOT,
        "planned_result_path": RESULT_PATH,
    }
    return {
        **body,
        "roster_sha256": _sha256(PROTECTED_ROSTER_DOMAIN + _canonical(body)),
    }


def _expected_fixed_registration(contracts: ModuleType) -> Dict[str, Any]:
    policy = contracts.environment_policy()
    roster = protected_path_roster()
    return {
        "schema_version": REGISTRATION_SCHEMA,
        "registration_id": (
            "A1_R1_ACTIVATION_PREPARATION_V3_LIVE_HOST_ENVIRONMENT_REHEARSAL_"
            "FREEZE_V1"
        ),
        "registration_mode": "ADDITIVE_PRE_MARKER_READ_ONLY_REHEARSAL_FREEZE",
        "global_state": GLOBAL_STATE,
        "milestone_state": PRE_RUN_STATE,
        "owned_paths": {
            "human": HUMAN_PATH,
            "machine": MACHINE_PATH,
            "contracts": CONTRACTS_PATH,
            "authority": AUTHORITY_PATH,
            "runtime": RUNTIME_PATH,
            "test": TEST_PATH,
            "planned_result": RESULT_PATH,
        },
        "future_v3_namespace": {
            "marker_path": FUTURE_V3_MARKER_PATH,
            "preparation_root": FUTURE_V3_PREPARATION_ROOT,
            "marker_schema_frozen": False,
            "writer_implemented": False,
            "marker_authorized": False,
            "marker_present_at_freeze": False,
            "preparation_root_present_at_freeze": False,
            "disjoint_from_v2": True,
        },
        "schemas": {
            "registration": contracts.REGISTRATION_SCHEMA,
            "qualification": contracts.QUALIFICATION_SCHEMA,
            "request": contracts.REQUEST_SCHEMA,
            "child_observation": contracts.CHILD_OBSERVATION_SCHEMA,
            "result": contracts.RESULT_SCHEMA,
            "protected_snapshot": contracts.PROTECTED_SNAPSHOT_SCHEMA,
        },
        "v2_terminal_predecessor": {
            "bindings": [
                {"path": path, "raw_sha256": digest, "bytes": size}
                for path, digest, size in POSTMORTEM_BINDINGS
            ],
            "registration_record_sha256": POSTMORTEM_RECORD_SHA256,
            "terminal_retry_permitted": False,
            "terminal_custody_must_remain_immutable": True,
        },
        "protected_path_roster": roster,
        "workspace_anchor_identity": workspace_anchor_identity(),
        "environment_policy": policy,
        "hash_probe": {
            "profile": "CPYTHON_3_11_5_64BIT_DARWIN_ARM64_HASHSEED_0",
            "ordered_strings": list(contracts.HASH_PROBE_STRINGS),
            "signed_integer_values": list(contracts.HASH_PROBE_VALUES),
            "canonical_preimage_ascii_bytes": len(contracts.HASH_PROBE_PREIMAGE),
            "canonical_preimage_has_lf": False,
            "digest_domain": "DIRECT_SHA256_NO_DOMAIN_SEPARATOR",
            "sha256": contracts.HASH_PROBE_SHA256,
            "fixture_known_before_live_rehearsal": True,
            "fixture_derived_without_live_profile_probe": True,
            "fixture_derivation": "CPYTHON_3_11_SIPHASH13_SEED_0_ALL_ZERO_SECRET",
        },
        "user_authorization_provenance": {
            "source": "CONVERSATION_VISIBLE_TEXT",
            "normalized_visible_assent_text": USER_VISIBLE_ASSENT_TEXT,
            "normalized_visible_assent_sha256": _sha256(
                USER_VISIBLE_ASSENT_DOMAIN + USER_VISIBLE_ASSENT_TEXT.encode("ascii")
            ),
            "antecedent_scope": (
                "WHOLLY_DISJOINT_V3_STATIC_PACKAGE_AND_NO_WRITE_LIVE_HOST_"
                "ENVIRONMENT_REHEARSAL_WITH_NO_MARKER"
            ),
            "trailing_transport_whitespace_or_entity_normalized": True,
            "raw_user_message_transport_bytes_bound_as_registered_workspace_artifact": False,
            "authorized_scope": [
                "SIX_FILE_STATIC_FREEZE_AND_INDEPENDENT_AUDIT",
                "ONE_AUDITED_READ_ONLY_LIVE_HOST_ENVIRONMENT_REHEARSAL_AFTER_GO",
                "MANDATORY_ADDITIVE_EXACT_PASS_OR_FAIL_RESULT_PUBLICATION",
            ],
            "rehearsal_retry_authorized": False,
            "v3_marker_root_nonce_or_capsule_authorized": False,
            "runtime_approval_rank_training_production_or_science_authorized": False,
        },
        "publication_boundary": {
            "evidence_classification": "INTERNAL_PUBLICATION_EXCLUDED",
            "six_static_files_anonymous_or_public_release_permitted": False,
            "future_result_workspace_registration_required": True,
            "future_result_anonymous_or_public_release_permitted": False,
            "v2_custody_publication_permitted": False,
            "workspace_anchor_publication_permitted": False,
            "internal_tool_or_conversation_log_publication_permitted": False,
            "publication_safe_derivative_requires_fresh_anonymity_audit": True,
            "publication_safe_derivative_must_omit_anchor_and_uid_like_data": True,
        },
        "rehearsal_protocol": {
            "canonical_command": [
                "/usr/bin/env",
                "-i",
                *[
                    key + "=" + value
                    for key, value in contracts.REQUESTED_ENVIRONMENT.items()
                ],
                contracts.PYTHON_RELATIVE_PATH,
                *contracts.PYTHON_FLAGS,
                AUTHORITY_PATH,
                "--rehearse-live-host",
            ],
            "parent_process_count": 1,
            "child_launch_maximum_count": 1,
            "retry_count": 0,
            "result_transport": "CANONICAL_ASCII_JSON_PLUS_LF_ON_STDOUT_ONLY",
            "result_publication": "LATER_EXACT_APPLY_PATCH_TO_PLANNED_RESULT_PATH",
            "stderr_must_be_empty": True,
            "raw_environment_emission_permitted": False,
            "raw_uid_gid_emission_permitted": False,
            "raw_cf_value_or_digest_emission_permitted": False,
            "application_workspace_or_temporary_write_permitted": False,
            "network_contact_permitted": False,
            "entropy_contact_permitted": False,
            "scientific_import_or_execution_permitted": False,
            "mechanical_one_shot_enforcement": False,
            "prepublication_replay_resistance": False,
            "procedural_single_launch_only": True,
            "failure_requires_new_version_not_retry": True,
            "typed_result_guaranteed_after_successful_pre_and_post_custody_and_transport": True,
            "typed_result_guaranteed_on_static_supervisor_postflight_or_transport_loss": False,
            "static_supervisor_postflight_or_transport_loss_requires_additive_postmortem": True,
        },
        "transition_states": {
            "pre_run": PRE_RUN_STATE,
            "pass": PASS_STATE,
            "fail": FAIL_STATE,
            "unvalidated_future_namespace": UNVALIDATED_FUTURE_STATE,
            "invalid_result": INVALID_RESULT_STATE,
            "pre_marker_static_suite_remains_fail_closed_after_future_namespace": True,
        },
        "state_preservation": {
            "unresolved_null_count": 172,
            "open_blocker_count": 12,
            "d1_quarantine_row_count": 550,
            "d1_quarantine_roster_sha256": (
                "1efbc36a3bdba6c052900ec3131abc2ead3766bafc43bce435e1698a79f19a14"
            ),
            "projection_source": "REOPENED_V2_TERMINAL_REGISTRATION",
            "scientific_execution_admissible": False,
        },
        "nonclaims": {
            "live_rehearsal_performed_at_freeze": False,
            "live_child_launched_at_freeze": False,
            "rehearsal_result_issued_at_freeze": False,
            "v3_marker_created": False,
            "v3_preparation_root_created": False,
            "v3_preparation_instance_nonce_minted": False,
            "scientific_campaign_nonce_minted": False,
            "capsule_materialized": False,
            "runtime_candidate_created": False,
            "runtime_approval_created": False,
            "runtime_admitted": False,
            "rank_execution_performed": False,
            "training_execution_performed": False,
            "production_execution_performed": False,
            "scientific_execution_performed": False,
            "network_contacted": False,
            "workspace_src_amended": False,
            "executable_preregistration_completed": False,
            "submission_ready": False,
            "environment_rehearsal_is_runtime_approval": False,
            "environment_rehearsal_qualifies_numerical_determinism": False,
            "fresh_v3_marker_authorization_inferred_from_current_user_request": False,
        },
        "next_gate": {
            "independent_exact_byte_audit_required": True,
            "single_canonical_read_only_rehearsal_after_go": True,
            "emitted_canonical_pass_or_fail_result_must_be_published_without_retry_or_selection": True,
            "additive_result_publication_required": True,
            "fresh_v3_writer_design_required_after_pass": True,
            "fresh_exact_user_marker_authorization_required": True,
            "marker_runtime_approval_rank_training_production_science_authorized": False,
        },
    }


def _load_registration(
    root: Path, contracts: ModuleType
) -> Tuple[bytes, Dict[str, Any]]:
    payload, _ = _read_stable_file(root, MACHINE_PATH)
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RehearsalAuthorityError("V3 registration is not JSON") from error
    if type(record) is not dict or payload != _canonical(record) + b"\n":
        raise RehearsalAuthorityError("V3 registration is not canonical")
    fixed = _expected_fixed_registration(contracts)
    if set(record) != set(fixed) | {"registration_bindings", "record_sha256"}:
        raise RehearsalAuthorityError("V3 registration fields changed")
    for key, expected in fixed.items():
        if type(record[key]) is not type(expected) or _canonical(
            record[key]
        ) != _canonical(expected):
            raise RehearsalAuthorityError("V3 registration field changed: " + key)
    bindings = record["registration_bindings"]
    if type(bindings) is not list or len(bindings) != len(STATIC_BINDING_PATHS):
        raise RehearsalAuthorityError("V3 registration bindings changed")
    for ordinal, ((role, relative), claimed) in enumerate(
        zip(STATIC_BINDING_PATHS, bindings)
    ):
        expected = _binding_row(root, ordinal, role, relative)
        if type(claimed) is not dict or _canonical(claimed) != _canonical(expected):
            raise RehearsalAuthorityError("V3 static binding changed")
    claimed_self = _require_sha256(record["record_sha256"], "registration digest")
    body = dict(record)
    body["record_sha256"] = None
    if claimed_self != _sha256(REGISTRATION_DOMAIN + _canonical(body)):
        raise RehearsalAuthorityError("V3 registration self digest changed")
    return payload, record


def _audit_postmortem() -> Dict[str, Any]:
    for relative, digest, size in POSTMORTEM_BINDINGS:
        payload, _ = _read_stable_file(WORKSPACE_ROOT, relative)
        if len(payload) != size or _sha256(payload) != digest:
            raise RehearsalAuthorityError("V2 terminal registration changed")
    postmortem = _load_postmortem()
    status = postmortem.status(WORKSPACE_ROOT)
    if (
        status["registration_record_sha256"] != POSTMORTEM_RECORD_SHA256
        or status["marker_attempt_spent"] is not True
        or status["retry_permitted"] is not False
        or status["validated_preparation_event_count"] != 3
        or status["capture_a_launch_claim_spent"] is not True
        or status["capture_a_binding_present"] is not False
        or status["capture_b_launch_claim_present"] is not False
        or status["runtime_candidate_present"] is not False
        or status["execution_authorized"] is not False
    ):
        raise RehearsalAuthorityError("V2 terminal status changed")
    return status


def _protected_snapshot(root: Path, registration: Mapping[str, Any]) -> Dict[str, Any]:
    rows = []
    for ordinal, relative in enumerate(PROTECTED_PATHS):
        payload, information = _read_stable_file(root, relative)
        rows.append(
            {
                "ordinal": ordinal,
                "path": relative,
                "bytes": len(payload),
                "raw_sha256": _sha256(payload),
                "mode_octal": "0644",
                "nlink": information.st_nlink,
            }
        )
    v2_status = _audit_postmortem()
    body = {
        "schema": PROTECTED_SNAPSHOT_SCHEMA,
        "protected_path_roster_sha256": registration["protected_path_roster"][
            "roster_sha256"
        ],
        "workspace_anchor_identity_sha256": registration["workspace_anchor_identity"][
            "identity_sha256"
        ],
        "rows": rows,
        "v2_terminal_registration_record_sha256": v2_status[
            "registration_record_sha256"
        ],
        "v2_terminal_validated_head_sha256": v2_status["validated_current_head_sha256"],
        "v2_terminal_preparation_event_count": v2_status[
            "validated_preparation_event_count"
        ],
        "future_v3_marker_absent": not _path_has_entry(root / FUTURE_V3_MARKER_PATH),
        "future_v3_preparation_root_absent": not _path_has_entry(
            root / FUTURE_V3_PREPARATION_ROOT
        ),
        "planned_result_absent": not _path_has_entry(root / RESULT_PATH),
    }
    return {
        **body,
        "snapshot_sha256": _sha256(PROTECTED_SNAPSHOT_DOMAIN + _canonical(body)),
    }


def _build_request(
    contracts: ModuleType,
    registration_payload: bytes,
    registration: Mapping[str, Any],
) -> Dict[str, Any]:
    by_role = {
        row["role"]: row["raw_sha256"] for row in registration["registration_bindings"]
    }
    body = {
        "schema": contracts.REQUEST_SCHEMA,
        "registration_raw_sha256": _sha256(registration_payload),
        "registration_record_sha256": registration["record_sha256"],
        "human_sha256": by_role["HUMAN_REGISTRATION"],
        "contracts_sha256": by_role["CONTRACTS_MODULE"],
        "authority_sha256": by_role["READ_ONLY_SUPERVISOR"],
        "runtime_sha256": by_role["ENVIRONMENT_ONLY_CHILD"],
        "test_sha256": by_role["HOSTILE_TEST"],
        "v2_terminal_registration_record_sha256": POSTMORTEM_RECORD_SHA256,
        "environment_policy_sha256": contracts.environment_policy()["policy_sha256"],
        "workspace_anchor_identity_sha256": registration["workspace_anchor_identity"][
            "identity_sha256"
        ],
        "profile_id": contracts.PROFILE_ID,
        "rehearsal_ordinal": 0,
        "python_relative_path": contracts.PYTHON_RELATIVE_PATH,
        "python_realpath": contracts.PYTHON_REALPATH,
        "python_flags": list(contracts.PYTHON_FLAGS),
        "requested_environment_sha256": contracts.REQUESTED_ENVIRONMENT_SHA256,
        "hash_probe_sha256": contracts.HASH_PROBE_SHA256,
        "child_observation_schema": contracts.CHILD_OBSERVATION_SCHEMA,
        "result_schema": contracts.RESULT_SCHEMA,
        "planned_result_relative_path": contracts.PLANNED_RESULT_RELATIVE_PATH,
        "future_v3_marker_relative_path": contracts.FUTURE_V3_MARKER_RELATIVE_PATH,
        "future_v3_preparation_root_relative_path": (
            contracts.FUTURE_V3_PREPARATION_ROOT_RELATIVE_PATH
        ),
        "workspace_write_requested": False,
        "entropy_requested": False,
        "network_contact_requested": False,
        "scientific_execution_requested": False,
        "request_sha256": None,
    }
    return contracts.finish_request(body)


def _bounded_extend(target: bytearray, chunk: bytes, limit: int) -> bool:
    if (
        type(target) is not bytearray
        or type(chunk) is not bytes
        or type(limit) is not int
    ):
        raise RehearsalAuthorityError("bounded transport types changed")
    if limit < 0 or len(target) > limit:
        raise RehearsalAuthorityError("bounded transport state changed")
    remaining = limit - len(target)
    target.extend(chunk[:remaining])
    return len(chunk) > remaining


def _run_child_bounded(request_payload: bytes) -> Dict[str, Any]:
    process = None
    selector = selectors.DefaultSelector()
    stdout = bytearray()
    stderr = bytearray()
    start = time.monotonic()
    failure_code = None
    try:
        process = subprocess.Popen(
            list(CHILD_ARGV),
            cwd=str(WORKSPACE_ROOT),
            env=dict(REQUESTED_ENVIRONMENT),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            start_new_session=True,
        )
        if process.stdin is None or process.stdout is None or process.stderr is None:
            raise RehearsalAuthorityError("child pipes unavailable")
        process.stdin.write(request_payload)
        process.stdin.close()
        os.set_blocking(process.stdout.fileno(), False)
        os.set_blocking(process.stderr.fileno(), False)
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        while selector.get_map():
            remaining = CHILD_TIMEOUT_SECONDS - (time.monotonic() - start)
            if remaining <= 0:
                failure_code = "CHILD_TIMEOUT"
                process.kill()
                break
            events = selector.select(min(remaining, 0.25))
            if not events and process.poll() is not None:
                events = [
                    (key, selectors.EVENT_READ)
                    for key in list(selector.get_map().values())
                ]
            for key, _ in events:
                target = stdout if key.data == "stdout" else stderr
                limit = (
                    MAXIMUM_CHILD_STDOUT_BYTES
                    if key.data == "stdout"
                    else MAXIMUM_CHILD_STDERR_BYTES
                )
                chunk = os.read(
                    key.fileobj.fileno(), min(8192, max(1, limit - len(target) + 1))
                )
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                if _bounded_extend(target, chunk, limit):
                    failure_code = (
                        "CHILD_STDOUT" if key.data == "stdout" else "CHILD_STDERR"
                    )
                    process.kill()
                    break
            if failure_code is not None:
                break
        exit_code = process.wait(timeout=2.0)
        if failure_code is None and stderr:
            failure_code = "CHILD_STDERR"
        if failure_code is None and exit_code != 0:
            failure_code = "CHILD_PROCESS"
        return {
            "launch_count": 1,
            "exit_observed": True,
            "exit_code": exit_code,
            "stdout": bytes(stdout),
            "stderr_byte_count": len(stderr),
            "failure_code": failure_code,
        }
    except (OSError, subprocess.SubprocessError, RehearsalAuthorityError):
        if process is not None:
            try:
                process.kill()
            except OSError:
                pass
            try:
                process.wait(timeout=2.0)
            except (OSError, subprocess.SubprocessError):
                pass
            return {
                "launch_count": 1,
                "exit_observed": process.returncode is not None,
                "exit_code": process.returncode,
                "stdout": bytes(stdout),
                "stderr_byte_count": len(stderr),
                "failure_code": "CHILD_PROCESS",
            }
        return {
            "launch_count": 0,
            "exit_observed": False,
            "exit_code": None,
            "stdout": b"",
            "stderr_byte_count": 0,
            "failure_code": "CHILD_PROCESS",
        }
    finally:
        selector.close()


def _build_result(
    contracts: ModuleType,
    request_payload: bytes,
    request: Mapping[str, Any],
    supervisor: Mapping[str, bool],
    preflight: Mapping[str, Any],
    postflight: Mapping[str, Any],
    child: Mapping[str, Any],
) -> Dict[str, Any]:
    observation = None
    observation_payload = None
    failure_code = child["failure_code"]
    if failure_code is None:
        try:
            observation = contracts.parse_canonical(
                child["stdout"], "CHILD_OBSERVATION"
            )
        except contracts.ContractError:
            failure_code = "CHILD_STDOUT"
        else:
            observation_payload = child["stdout"]
            if observation["request_sha256"] != request["request_sha256"]:
                failure_code = "CHILD_STDOUT"
            elif observation["outcome"] != "PASS":
                failure_code = observation["failure_code"]
    protected_unchanged = _canonical(preflight) == _canonical(postflight)
    preflight_clean = all(
        (
            preflight["future_v3_marker_absent"],
            preflight["future_v3_preparation_root_absent"],
            preflight["planned_result_absent"],
        )
    )
    postflight_clean = all(
        (
            postflight["future_v3_marker_absent"],
            postflight["future_v3_preparation_root_absent"],
            postflight["planned_result_absent"],
        )
    )
    if not preflight_clean:
        failure_code = "PROTECTED_CUSTODY"
    elif failure_code is None and (not protected_unchanged or not postflight_clean):
        failure_code = "PROTECTED_CUSTODY"
    success = failure_code is None
    body = {
        "schema": contracts.RESULT_SCHEMA,
        "request_raw_sha256": _sha256(request_payload),
        "request_sha256": request["request_sha256"],
        "child_observation_raw_sha256": (
            _sha256(observation_payload) if observation_payload is not None else None
        ),
        "child_observation_sha256": (
            observation["observation_sha256"] if observation is not None else None
        ),
        "child_observation": observation,
        "outcome": "PASS" if success else "FAIL",
        "failure_code": "NONE" if success else failure_code,
        "child_exit_code": child["exit_code"],
        "child_transport_failure_code": child["failure_code"] or "NONE",
        "child_stdout_byte_count": len(child["stdout"]),
        "child_stderr_byte_count": child["stderr_byte_count"],
        "preflight_snapshot_sha256": preflight["snapshot_sha256"],
        "postflight_snapshot_sha256": postflight["snapshot_sha256"],
        "protected_snapshot_schema": PROTECTED_SNAPSHOT_SCHEMA,
        "protected_path_roster_sha256": preflight["protected_path_roster_sha256"],
        "workspace_anchor_identity_sha256": preflight[
            "workspace_anchor_identity_sha256"
        ],
        **dict(supervisor),
        "parent_environment_observation_passed": all(supervisor.values()),
        "child_environment_observation_passed": (
            observation is not None and observation["outcome"] == "PASS"
        ),
        "parent_child_environment_semantics_match": (
            observation is not None
            and observation["requested_environment_exact_after_normalization"] is True
            and observation["darwin_injected_value_matches_uid"] is True
        ),
        "protected_custody_unchanged": protected_unchanged,
        "v2_terminal_custody_revalidated_intact_before": True,
        "v2_terminal_custody_revalidated_intact_after": True,
        "v3_marker_absent_before": preflight["future_v3_marker_absent"],
        "v3_marker_absent_after": postflight["future_v3_marker_absent"],
        "v3_preparation_root_absent_before": preflight[
            "future_v3_preparation_root_absent"
        ],
        "v3_preparation_root_absent_after": postflight[
            "future_v3_preparation_root_absent"
        ],
        "planned_result_absent_before": preflight["planned_result_absent"],
        "planned_result_absent_after": postflight["planned_result_absent"],
        "application_workspace_write_performed": False,
        "application_temporary_write_performed": False,
        "entropy_contacted": False,
        "network_contacted": False,
        "scientific_execution_performed": False,
        "runtime_approval_created": False,
        "marker_creation_authorized": False,
        "child_launch_count": child["launch_count"],
        "retry_count": 0,
        "child_exit_observed": child["exit_observed"],
        "mechanical_one_shot_enforced": False,
        "prepublication_replay_resistance": False,
        "result_sha256": None,
    }
    return contracts.finish_result(body)


def rehearse_live_host() -> bytes:
    supervisor = _require_live_supervisor_boundary()
    contracts = _load_contracts()
    registration_payload, registration = _load_registration(WORKSPACE_ROOT, contracts)
    if (
        _path_has_entry(WORKSPACE_ROOT / RESULT_PATH)
        or _path_has_entry(WORKSPACE_ROOT / FUTURE_V3_MARKER_PATH)
        or _path_has_entry(WORKSPACE_ROOT / FUTURE_V3_PREPARATION_ROOT)
    ):
        raise RehearsalAuthorityError("rehearsal refuses a consumed or future state")
    preflight = _protected_snapshot(WORKSPACE_ROOT, registration)
    if not all(
        (
            preflight["future_v3_marker_absent"],
            preflight["future_v3_preparation_root_absent"],
            preflight["planned_result_absent"],
        )
    ):
        raise RehearsalAuthorityError("rehearsal preflight is not pristine")
    request = _build_request(contracts, registration_payload, registration)
    request_payload = contracts.canonical_json(request) + b"\n"
    child = _run_child_bounded(request_payload)
    postflight = _protected_snapshot(WORKSPACE_ROOT, registration)
    result = _build_result(
        contracts,
        request_payload,
        request,
        supervisor,
        preflight,
        postflight,
        child,
    )
    return contracts.canonical_json(result) + b"\n"


def _classify_transition(
    result_state: str, marker_present: bool, preparation_root_present: bool
) -> str:
    if marker_present or preparation_root_present:
        return UNVALIDATED_FUTURE_STATE
    if result_state == "ABSENT":
        return PRE_RUN_STATE
    if result_state == "PASS":
        return PASS_STATE
    if result_state == "FAIL":
        return FAIL_STATE
    return INVALID_RESULT_STATE


def _historical_preresult_snapshot(current: Mapping[str, Any]) -> str:
    body = dict(current)
    body.pop("snapshot_sha256", None)
    body["future_v3_marker_absent"] = True
    body["future_v3_preparation_root_absent"] = True
    body["planned_result_absent"] = True
    return _sha256(PROTECTED_SNAPSHOT_DOMAIN + _canonical(body))


def _result_matches_canonical_route(result: Mapping[str, Any]) -> bool:
    required_true = (
        "supervisor_direct_file_main",
        "supervisor_spec_is_none",
        "supervisor_python_argv_exact",
        "supervisor_native_argv_exact",
        "supervisor_environment_exact_after_normalization",
        "supervisor_python_flags_exact",
        "supervisor_cwd_exact",
        "supervisor_profile_exact",
        "parent_environment_observation_passed",
        "protected_custody_unchanged",
        "v2_terminal_custody_revalidated_intact_before",
        "v2_terminal_custody_revalidated_intact_after",
        "v3_marker_absent_before",
        "v3_marker_absent_after",
        "v3_preparation_root_absent_before",
        "v3_preparation_root_absent_after",
        "planned_result_absent_before",
        "planned_result_absent_after",
    )
    required_false = (
        "application_workspace_write_performed",
        "application_temporary_write_performed",
        "entropy_contacted",
        "network_contacted",
        "scientific_execution_performed",
        "runtime_approval_created",
        "marker_creation_authorized",
        "mechanical_one_shot_enforced",
        "prepublication_replay_resistance",
    )
    if not (
        all(result[name] is True for name in required_true)
        and all(result[name] is False for name in required_false)
    ):
        return False
    child = result["child_observation"]
    if child is None:
        return True
    child_required_false = (
        "entropy_contacted",
        "network_contacted",
        "scientific_imports_performed",
        "workspace_write_performed",
        "temporary_write_performed",
        "raw_environment_emitted",
        "raw_identity_emitted",
    )
    return child["hash_probe_sha256"] == HASH_PROBE_SHA256 and all(
        child[name] is False for name in child_required_false
    )


def status(workspace_root: Any = WORKSPACE_ROOT) -> Dict[str, Any]:
    root = Path(workspace_root).absolute()
    if root != WORKSPACE_ROOT or root.resolve(strict=True) != WORKSPACE_ROOT:
        raise RehearsalAuthorityError("only the canonical workspace is auditable")
    contracts = _load_contracts()
    registration_payload, registration = _load_registration(root, contracts)
    expected_request = _build_request(contracts, registration_payload, registration)
    expected_request_payload = contracts.canonical_json(expected_request) + b"\n"
    snapshot = _protected_snapshot(root, registration)
    marker_present = _path_has_entry(root / FUTURE_V3_MARKER_PATH)
    preparation_root_present = _path_has_entry(root / FUTURE_V3_PREPARATION_ROOT)
    result_present = _path_has_entry(root / RESULT_PATH)
    result_state = "ABSENT"
    result_sha256 = None
    if result_present:
        try:
            payload, _ = _read_stable_file(root, RESULT_PATH)
            result = contracts.parse_canonical(payload, "RESULT")
            if (
                result["request_raw_sha256"] != _sha256(expected_request_payload)
                or result["request_sha256"] != expected_request["request_sha256"]
                or result["protected_path_roster_sha256"]
                != registration["protected_path_roster"]["roster_sha256"]
                or result["workspace_anchor_identity_sha256"]
                != registration["workspace_anchor_identity"]["identity_sha256"]
                or result["preflight_snapshot_sha256"]
                != _historical_preresult_snapshot(snapshot)
                or result["postflight_snapshot_sha256"]
                != _historical_preresult_snapshot(snapshot)
                or not _result_matches_canonical_route(result)
            ):
                raise RehearsalAuthorityError("result is not bound to this freeze")
            result_state = result["outcome"]
            result_sha256 = result["result_sha256"]
        except (RehearsalAuthorityError, contracts.ContractError):
            result_state = "INVALID"
    return {
        "schema": QUALIFICATION_SCHEMA,
        "global_state": GLOBAL_STATE,
        "milestone_state": _classify_transition(
            result_state, marker_present, preparation_root_present
        ),
        "static_registration_record_sha256": registration["record_sha256"],
        "protected_snapshot_sha256": snapshot["snapshot_sha256"],
        "result_present": result_present,
        "result_state": result_state,
        "result_sha256": result_sha256,
        "future_v3_marker_present": marker_present,
        "future_v3_preparation_root_present": preparation_root_present,
        "mechanical_one_shot_enforced": False,
        "prepublication_replay_resistance": False,
        "marker_authorized": False,
        "runtime_approval_created": False,
        "execution_authorized": False,
    }


class StaticRehearsalQualification:
    __slots__ = ("_registration", "_status", "_record_sha256")

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise TypeError("qualification is constructed only by the canonical loader")

    def registration(self) -> Dict[str, Any]:
        return json.loads(self._registration.decode("ascii"))

    def status(self) -> Dict[str, Any]:
        return json.loads(self._status.decode("ascii"))

    @property
    def record_sha256(self) -> str:
        return self._record_sha256

    def __setattr__(self, name: str, value: Any) -> None:
        del name, value
        raise AttributeError("qualification is immutable")


def load_static_qualification(
    workspace_root: Any = WORKSPACE_ROOT,
) -> StaticRehearsalQualification:
    root = Path(workspace_root).absolute()
    contracts = _load_contracts()
    _, registration = _load_registration(root, contracts)
    observed = status(root)
    repeated = status(root)
    if _canonical(observed) != _canonical(repeated):
        raise RehearsalAuthorityError("V3 static status changed during load")
    value = object.__new__(StaticRehearsalQualification)
    object.__setattr__(value, "_registration", _canonical(registration))
    object.__setattr__(value, "_status", _canonical(observed))
    object.__setattr__(value, "_record_sha256", registration["record_sha256"])
    return value


def main(arguments: Sequence[str] | None = None) -> int:
    supplied = list(sys.argv[1:] if arguments is None else arguments)
    if supplied != ["--rehearse-live-host"]:
        return 64
    try:
        payload = rehearse_live_host()
    except Exception:
        # The live route never exposes raw environment, identity, or traceback.
        return 70
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "AUTHORITY_PATH",
    "CONTRACTS_PATH",
    "FAIL_STATE",
    "FUTURE_V3_MARKER_PATH",
    "FUTURE_V3_PREPARATION_ROOT",
    "GLOBAL_STATE",
    "HUMAN_PATH",
    "INVALID_RESULT_STATE",
    "MACHINE_PATH",
    "PASS_STATE",
    "POSTMORTEM_BINDINGS",
    "POSTMORTEM_RECORD_SHA256",
    "PRE_RUN_STATE",
    "PROFILE_ID",
    "PROTECTED_PATHS",
    "PROTECTED_SNAPSHOT_SCHEMA",
    "PYTHON_FLAGS",
    "QUALIFICATION_SCHEMA",
    "REGISTRATION_DOMAIN",
    "REGISTRATION_SCHEMA",
    "REQUESTED_ENVIRONMENT",
    "RESULT_PATH",
    "RUNTIME_PATH",
    "RehearsalAuthorityError",
    "STATIC_BINDING_PATHS",
    "StaticRehearsalQualification",
    "TEST_PATH",
    "UNVALIDATED_FUTURE_STATE",
    "WORKSPACE_ROOT",
    "load_static_qualification",
    "main",
    "protected_path_roster",
    "rehearse_live_host",
    "status",
]
