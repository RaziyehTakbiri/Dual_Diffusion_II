"""Read-only registration for the spent empty-tool-output V3 rehearsal attempt.

This module never imports or invokes the frozen V3 authority or child.  It has
no writer, subprocess, entropy, network, marker, runtime-approval, or
scientific route.  It reopens exact frozen bytes and existing V2 custody, then
validates one additive terminal-failure registration.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import stat
from types import ModuleType
from typing import Any, Dict, Mapping, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = (
    "heterodiff-manuscript-v3-a1-r1-activation-preparation-v3-live-host-"
    "environment-rehearsal-terminal-failure-registration-v1"
)
QUALIFICATION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v3-live-host-environment-"
    "rehearsal-terminal-failure-qualification-v1"
)
STATUS_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v3-live-host-environment-"
    "rehearsal-terminal-failure-status-v1"
)
REGISTRATION_DOMAIN = (SCHEMA + "\0").encode("ascii")
COMMAND_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-v3-canonical-rehearsal-command-v1\0"
)

GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
TERMINAL_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V3_REHEARSAL_ATTEMPT_SPENT_TERMINAL_"
    "EXIT_70_EMPTY_TOOL_OUTPUT_FIELD_NO_TYPED_RESULT_NO_RETRY_NO_MARKER_"
    "NOT_EXECUTABLE"
)
FROZEN_PRE_RUN_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V3_LIVE_HOST_ENVIRONMENT_REHEARSAL_"
    "IMPLEMENTATION_FROZEN_AWAITING_SINGLE_READ_ONLY_REHEARSAL_NO_MARKER_"
    "NOT_EXECUTABLE"
)

HUMAN_PATH = (
    "manuscript_v3/a1_r1_activation_preparation_v3_live_host_environment_"
    "rehearsal_terminal_failure_registration_v1.md"
)
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v3_live_host_"
    "environment_rehearsal_terminal_failure_registration_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/finite_association_r1_activation_preparation_v3_live_"
    "host_environment_rehearsal_terminal_failure_registration_v1.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_a1_r1_activation_preparation_v3_live_host_"
    "environment_rehearsal_terminal_failure_registration_v1.py"
)

V3_HUMAN_PATH = (
    "manuscript_v3/a1_r1_activation_preparation_v3_live_host_environment_"
    "rehearsal_freeze_v1.md"
)
V3_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v3_live_host_"
    "environment_rehearsal_freeze_v1.json"
)
V3_CONTRACTS_PATH = (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_contracts_v3.py"
)
V3_AUTHORITY_PATH = (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_authority_v3.py"
)
V3_RUNTIME_PATH = (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_runtime_v3.py"
)
V3_TEST_PATH = (
    "tests/unit/test_manuscript_v3_a1_r1_activation_preparation_v3_live_host_"
    "environment_rehearsal_freeze_v1.py"
)
V3_RESULT_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v3_live_host_"
    "environment_rehearsal_result_v1.json"
)
V3_MARKER_PATH = "artifacts/a1_r1_activation_preparation_v3.attempt.json"
V3_ROOT_PATH = "artifacts/a1_r1_activation_preparation_v3"

V2_POSTMORTEM_HUMAN_PATH = (
    "manuscript_v3/a1_r1_activation_preparation_v2_terminal_failure_"
    "registration_v1.md"
)
V2_POSTMORTEM_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v2_terminal_"
    "failure_registration_v1.json"
)
V2_POSTMORTEM_VALIDATOR_PATH = (
    "research/diagnostics/finite_association_r1_activation_preparation_v2_"
    "terminal_failure_registration_v1.py"
)
V2_POSTMORTEM_TEST_PATH = (
    "tests/unit/test_manuscript_v3_a1_r1_activation_preparation_v2_terminal_"
    "failure_registration_v1.py"
)

V3_FREEZE_BINDINGS = (
    {
        "ordinal": 0,
        "role": "V3_HUMAN_FREEZE",
        "path": V3_HUMAN_PATH,
        "bytes": 11329,
        "raw_sha256": "e4afa4a9c3db43ee7036c0f69ccd12d806a4e41ca7c263e21a4c00c5bba2ce5b",
    },
    {
        "ordinal": 1,
        "role": "V3_MACHINE_FREEZE",
        "path": V3_MACHINE_PATH,
        "bytes": 14326,
        "raw_sha256": "09b2892d84a446f6057461d562eca9c076491a7a48fe25756b834d9b39f375d1",
    },
    {
        "ordinal": 2,
        "role": "V3_CONTRACTS",
        "path": V3_CONTRACTS_PATH,
        "bytes": 35283,
        "raw_sha256": "8ea49970e6419ef6851f511f31c88daab4a785cfd4c674700de2449533edb191",
    },
    {
        "ordinal": 3,
        "role": "V3_READ_ONLY_SUPERVISOR",
        "path": V3_AUTHORITY_PATH,
        "bytes": 55103,
        "raw_sha256": "24dba07ac156104eec0d06cc95a64fe9470715bdda5f4b57107efe884faad5ec",
    },
    {
        "ordinal": 4,
        "role": "V3_ENVIRONMENT_CHILD",
        "path": V3_RUNTIME_PATH,
        "bytes": 19530,
        "raw_sha256": "1c4f729d65d585b4c38ae977f0001f97d0e8cbfa23ad566d1e9d999b370eeac6",
    },
    {
        "ordinal": 5,
        "role": "V3_HOSTILE_TEST",
        "path": V3_TEST_PATH,
        "bytes": 30285,
        "raw_sha256": "18305d55f1ef15b9c754223b10ae02f67d56bed44104b967181fdb525e5793f2",
    },
)
V3_MACHINE_RECORD_SHA256 = (
    "7b082199634154c23baa341a19c957ea3191298a1d9f3366e00ea57c376a206a"
)

V2_POSTMORTEM_BINDINGS = (
    {
        "path": V2_POSTMORTEM_HUMAN_PATH,
        "bytes": 11507,
        "raw_sha256": "c29302fadc4a5c6a81a963442c85a681c92791ad664482267e80ef6d75f546ed",
    },
    {
        "path": V2_POSTMORTEM_MACHINE_PATH,
        "bytes": 17232,
        "raw_sha256": "bc73165ba905db1f26c5c81e2aebaf644e5e8009bd00daa477469479674d3085",
    },
    {
        "path": V2_POSTMORTEM_VALIDATOR_PATH,
        "bytes": 62047,
        "raw_sha256": "ce59c0d855d22eea01e0091110ab6e928d071fe57ba1416f6e0ccab0e5bcf671",
    },
    {
        "path": V2_POSTMORTEM_TEST_PATH,
        "bytes": 19591,
        "raw_sha256": "7f28086bfeaab835241296961bfc91461789cadce6780ef38009569fd2189d5f",
    },
)
V2_POSTMORTEM_RECORD_SHA256 = (
    "da57dda788f5de2b2a34ed30bdaf7f692db98696a00e420aa0484d44127b6ed0"
)
V2_ATTEMPT_MARKER_RAW_SHA256 = (
    "e74195f33df40f255fbe4f956dd426a6a76676c93358f70e785f2f90c7db7cc4"
)
V2_VALIDATED_HEAD_SHA256 = (
    "4ba4799fdfa3bf407ea269c035c6502114b9bae5b93bdde1b32c6ebe497646a5"
)

COLLAPSED_STAGE_ROSTER = (
    "SUPERVISOR_BOUNDARY",
    "STATIC_CONTRACT_ADMISSION",
    "REGISTRATION_ADMISSION",
    "ENTRY_STATE_CHECK",
    "PREFLIGHT_CUSTODY",
    "REQUEST_CONSTRUCTION",
    "CHILD_LAUNCH_OR_TRANSPORT",
    "POSTFLIGHT_CUSTODY",
    "RESULT_CONSTRUCTION",
)

PROBE_ZERO_FIELD_ROSTER = (
    "cpython_3_11_5",
    "cwd_matches_expected",
    "darwin_arm64",
    "darwin_key_present",
    "darwin_value_matches_uid",
    "effective_environment_count_17",
    "gid_egid_equal",
    "hash_probe_matches",
    "nonroot",
    "normalized_environment_exact16",
    "process_taint_absent",
    "python_flags_exact",
    "site_absent",
    "supplemental_root_group_absent",
    "sys_path_exact",
    "uid_euid_equal",
)

PROBE_ROSTER = (
    {
        "ordinal": 0,
        "reported_process_exit_code": 0,
        "description": "BROAD_PARENT_PROFILE_BOOLEAN_VECTOR",
        "reported_fields": list(PROBE_ZERO_FIELD_ROSTER),
        "reported_values": {name: True for name in PROBE_ZERO_FIELD_ROSTER},
        "cross_process_transfer_permitted": False,
        "canonical_failure_process_binding": False,
    },
    {
        "ordinal": 1,
        "reported_process_exit_code": 0,
        "description": "NATIVE_ARGC_C_MODE_COMBINED_PREFIX_RELATIVE_ARGV0",
        "reported_fields": [
            "native_argc_expected_for_c",
            "native_c_mode_exact",
            "native_flag_prefix_exact",
            "native_interpreter_relative_exact",
            "native_payload_present",
        ],
        "reported_values": {
            "native_argc_expected_for_c": True,
            "native_c_mode_exact": True,
            "native_flag_prefix_exact": False,
            "native_interpreter_relative_exact": False,
            "native_payload_present": True,
        },
        "cross_process_transfer_permitted": False,
        "canonical_failure_process_binding": False,
    },
    {
        "ordinal": 2,
        "reported_process_exit_code": 0,
        "description": "NATIVE_FLAGS_ABSOLUTE_SYMLINK_AND_REALPATH_ARGV0",
        "reported_fields": [
            "native_flags_exact",
            "native_interpreter_absolute_symlink_exact",
            "native_interpreter_realpath_exact",
        ],
        "reported_values": {
            "native_flags_exact": True,
            "native_interpreter_absolute_symlink_exact": False,
            "native_interpreter_realpath_exact": False,
        },
        "cross_process_transfer_permitted": False,
        "canonical_failure_process_binding": False,
    },
    {
        "ordinal": 3,
        "reported_process_exit_code": 0,
        "description": "NATIVE_ARGV0_ALLOWLISTED_EXECUTABLE_AND_BASENAME_CLASSIFICATION",
        "reported_fields": [
            "ABSOLUTE_PYTHON3_11",
            "BASENAME_PYTHON",
            "BASENAME_PYTHON3_11",
            "BASE_EXECUTABLE",
            "BASE_EXECUTABLE_REALPATH",
            "RELATIVE_PYTHON3_11",
            "SYS_EXECUTABLE",
            "SYS_EXECUTABLE_REALPATH",
        ],
        "reported_values": {
            "ABSOLUTE_PYTHON3_11": False,
            "BASENAME_PYTHON": False,
            "BASENAME_PYTHON3_11": False,
            "BASE_EXECUTABLE": False,
            "BASE_EXECUTABLE_REALPATH": False,
            "RELATIVE_PYTHON3_11": False,
            "SYS_EXECUTABLE": False,
            "SYS_EXECUTABLE_REALPATH": False,
        },
        "cross_process_transfer_permitted": False,
        "canonical_failure_process_binding": False,
    },
    {
        "ordinal": 4,
        "reported_process_exit_code": 0,
        "description": "NATIVE_ARGV0_ABSOLUTE_LENGTH_AND_ENV_SHAPE_CLASSIFICATION",
        "reported_fields": [
            "ARGV0_ABSOLUTE",
            "ARGV0_DASH_C",
            "ARGV0_EMPTY",
            "ARGV0_ENV",
            "ARGV0_ENV_BASENAME",
            "ARGV0_LENGTH_UNDER_64",
        ],
        "reported_values": {
            "ARGV0_ABSOLUTE": True,
            "ARGV0_DASH_C": False,
            "ARGV0_EMPTY": False,
            "ARGV0_ENV": False,
            "ARGV0_ENV_BASENAME": False,
            "ARGV0_LENGTH_UNDER_64": False,
        },
        "cross_process_transfer_permitted": False,
        "canonical_failure_process_binding": False,
    },
)


class TerminalFailureRegistrationError(RuntimeError):
    """Raised when immutable terminal custody or registration bytes change."""


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
        raise TerminalFailureRegistrationError("value is not canonical JSON") from error


def _sha256(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise TerminalFailureRegistrationError("digest input must be exact bytes")
    return hashlib.sha256(payload).hexdigest()


def _require_sha256(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TerminalFailureRegistrationError(label + " is not lowercase SHA-256")
    return value


def _canonical_root(root: Any) -> Path:
    candidate = Path(root).absolute()
    if candidate != WORKSPACE_ROOT or candidate.resolve(strict=True) != WORKSPACE_ROOT:
        raise TerminalFailureRegistrationError("only canonical workspace is auditable")
    information = candidate.lstat()
    if not stat.S_ISDIR(information.st_mode) or stat.S_ISLNK(information.st_mode):
        raise TerminalFailureRegistrationError("workspace root custody changed")
    return candidate


def _path_has_entry(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _normalized_relative_path(relative: Any) -> str:
    if type(relative) is not str or not relative or "\\" in relative:
        raise TerminalFailureRegistrationError("file path is not normalized")
    parsed = PurePosixPath(relative)
    if (
        parsed.is_absolute()
        or relative != parsed.as_posix()
        or any(part in ("", ".", "..") for part in parsed.parts)
    ):
        raise TerminalFailureRegistrationError("file path is not normalized")
    return relative


def _structural_directory_identity(information: os.stat_result) -> Tuple[int, ...]:
    return (
        information.st_dev,
        information.st_ino,
        information.st_mode,
        information.st_uid,
        information.st_gid,
    )


def _ancestor_identities(
    root: Path, relative: str
) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
    parsed = PurePosixPath(_normalized_relative_path(relative))
    paths = [root]
    current = root
    for part in parsed.parts[:-1]:
        current = current / part
        paths.append(current)
    rows = []
    for path in paths:
        information = path.lstat()
        if not stat.S_ISDIR(information.st_mode) or stat.S_ISLNK(information.st_mode):
            raise TerminalFailureRegistrationError("file ancestor custody changed")
        rows.append(
            (
                path.relative_to(root).as_posix() if path != root else "",
                _structural_directory_identity(information),
            )
        )
    return tuple(rows)


def _read_stable_file(
    root: Path, relative: str, expected_mode: int = 0o644, expected_nlink: int = 1
) -> Tuple[bytes, os.stat_result]:
    relative = _normalized_relative_path(relative)
    path = root / relative
    ancestors_before = _ancestor_identities(root, relative)
    before = path.lstat()
    if (
        not stat.S_ISREG(before.st_mode)
        or stat.S_ISLNK(before.st_mode)
        or stat.S_IMODE(before.st_mode) != expected_mode
        or before.st_nlink != expected_nlink
    ):
        raise TerminalFailureRegistrationError("file custody changed: " + relative)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise TerminalFailureRegistrationError("file rebound: " + relative)
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    reopened = path.lstat()
    ancestors_after = _ancestor_identities(root, relative)
    identity = lambda value: (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )
    if identity(before) != identity(opened) or identity(opened) != identity(after):
        raise TerminalFailureRegistrationError("file changed during read: " + relative)
    if identity(after) != identity(reopened):
        raise TerminalFailureRegistrationError("file changed after read: " + relative)
    if ancestors_before != ancestors_after:
        raise TerminalFailureRegistrationError("file ancestor changed: " + relative)
    return b"".join(chunks), reopened


def _read_canonical_json(root: Path, relative: str) -> Tuple[bytes, Dict[str, Any]]:
    payload, _ = _read_stable_file(root, relative)
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TerminalFailureRegistrationError(relative + " is not JSON") from error
    if type(record) is not dict or payload != _canonical(record) + b"\n":
        raise TerminalFailureRegistrationError(relative + " is not canonical")
    return payload, record


def _audit_exact_bindings(root: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    for ordinal, row in enumerate(rows):
        if "ordinal" in row and row["ordinal"] != ordinal:
            raise TerminalFailureRegistrationError("binding ordinal changed")
        payload, _ = _read_stable_file(root, row["path"])
        if len(payload) != row["bytes"] or _sha256(payload) != row["raw_sha256"]:
            raise TerminalFailureRegistrationError(
                "frozen bytes changed: " + row["path"]
            )


def _validate_v3_machine(root: Path) -> Dict[str, Any]:
    payload, record = _read_canonical_json(root, V3_MACHINE_PATH)
    expected = V3_FREEZE_BINDINGS[1]
    if len(payload) != expected["bytes"] or _sha256(payload) != expected["raw_sha256"]:
        raise TerminalFailureRegistrationError("V3 machine bytes changed")
    if record.get("record_sha256") != V3_MACHINE_RECORD_SHA256:
        raise TerminalFailureRegistrationError("V3 machine self digest changed")
    body = dict(record)
    body["record_sha256"] = None
    schema = record.get("schema_version")
    if type(schema) is not str or V3_MACHINE_RECORD_SHA256 != _sha256(
        (schema + "\0").encode("ascii") + _canonical(body)
    ):
        raise TerminalFailureRegistrationError("V3 machine semantic digest changed")
    if record.get("milestone_state") != FROZEN_PRE_RUN_STATE:
        raise TerminalFailureRegistrationError("V3 frozen pre-run state changed")
    return record


def _load_exact_v2_postmortem(root: Path) -> ModuleType:
    _audit_exact_bindings(root, V2_POSTMORTEM_BINDINGS)
    payload, _ = _read_stable_file(root, V2_POSTMORTEM_VALIDATOR_PATH)
    module = ModuleType("v2_terminal_postmortem_for_v3_empty_tool_output")
    module.__file__ = str(root / V2_POSTMORTEM_VALIDATOR_PATH)
    module.__name__ = "v2_terminal_postmortem_for_v3_empty_tool_output"
    exec(compile(payload, module.__file__, "exec"), module.__dict__)
    return module


def _audit_v2_terminal(root: Path) -> Dict[str, Any]:
    module = _load_exact_v2_postmortem(root)
    observed_status = module.status(root)
    observed_custody = module.audit_terminal_custody(root)
    repeated_status = module.status(root)
    repeated_custody = module.audit_terminal_custody(root)
    if _canonical(observed_status) != _canonical(repeated_status) or _canonical(
        observed_custody
    ) != _canonical(repeated_custody):
        raise TerminalFailureRegistrationError(
            "V2 terminal custody changed during audit"
        )
    if (
        observed_status["registration_record_sha256"] != V2_POSTMORTEM_RECORD_SHA256
        or observed_status["marker_attempt_spent"] is not True
        or observed_status["retry_permitted"] is not False
        or observed_status["validated_preparation_event_count"] != 3
        or observed_status["validated_current_head_sha256"] != V2_VALIDATED_HEAD_SHA256
        or observed_status["capture_a_launch_claim_spent"] is not True
        or observed_status["capture_a_binding_present"] is not False
        or observed_status["capture_b_launch_claim_present"] is not False
        or observed_status["runtime_candidate_present"] is not False
        or observed_status["execution_authorized"] is not False
        or observed_custody["preparation_file_count"] != 65
        or observed_custody["preparation_directory_count"] != 20
        or observed_custody["capsule"]["file_count"] != 53
        or observed_custody["capsule"]["directory_count"] != 14
        or observed_custody["capsule"]["inventory_sha256"]
        != "c68e21aa648c4823bd87987399eb0ce76149adaa57c7b19b162783ad5dc01360"
        or observed_custody["capsule"]["all_rows_reopened_twice"] is not True
        or observed_custody["capsule"]["closed_world_verified"] is not True
        or observed_custody["raw_runtime_envelopes_persisted"] is not False
        or observed_custody["typed_terminal_ledger_event_present"] is not False
    ):
        raise TerminalFailureRegistrationError("V2 terminal status changed")
    return {"status": observed_status, "custody": observed_custody}


def _frozen_predecessor_pyc_paths(root: Path) -> Sequence[str]:
    stems = (
        Path(V3_CONTRACTS_PATH).stem,
        Path(V3_AUTHORITY_PATH).stem,
        Path(V3_RUNTIME_PATH).stem,
        Path(V3_TEST_PATH).stem,
    )
    found = []
    for relative in (
        "research/production/__pycache__",
        "research/diagnostics/__pycache__",
        "tests/unit/__pycache__",
    ):
        directory = root / relative
        if not directory.exists():
            continue
        for path in directory.iterdir():
            if any(stem in path.name for stem in stems):
                found.append(path.relative_to(root).as_posix())
    return tuple(sorted(found))


def _v3_terminal_namespace_absences(root: Path) -> Dict[str, bool]:
    return {
        "v3_result_lstat_absent": not _path_has_entry(root / V3_RESULT_PATH),
        "v3_marker_lstat_absent": not _path_has_entry(root / V3_MARKER_PATH),
        "v3_root_lstat_absent": not _path_has_entry(root / V3_ROOT_PATH),
    }


def audit_terminal_custody(workspace_root: Any = WORKSPACE_ROOT) -> Dict[str, Any]:
    root = _canonical_root(workspace_root)
    _audit_exact_bindings(root, V3_FREEZE_BINDINGS)
    v3_machine = _validate_v3_machine(root)
    v2_status = _audit_v2_terminal(root)
    absences = _v3_terminal_namespace_absences(root)
    if any(value is not True for value in absences.values()):
        raise TerminalFailureRegistrationError("spent V3 namespace is no longer absent")
    predecessor_pyc = list(_frozen_predecessor_pyc_paths(root))
    if predecessor_pyc:
        raise TerminalFailureRegistrationError(
            "frozen predecessor bytecode cache exists"
        )
    return {
        "schema": (
            "heterodiff-a1-r1-activation-preparation-v3-live-host-environment-"
            "rehearsal-terminal-custody-v1"
        ),
        "terminal_state": TERMINAL_STATE,
        "global_state": GLOBAL_STATE,
        "v3_freeze_binding_count": len(V3_FREEZE_BINDINGS),
        "v3_machine_record_sha256": v3_machine["record_sha256"],
        **absences,
        "frozen_predecessor_pyc_paths": predecessor_pyc,
        "registration_hygiene_requires_no_focused_pyc_at_freeze": True,
        "v2_terminal_registration_bindings": [
            dict(row) for row in V2_POSTMORTEM_BINDINGS
        ],
        "v2_terminal_registration_record_sha256": v2_status["status"][
            "registration_record_sha256"
        ],
        "v2_terminal_custody_projection": dict(v2_status["custody"]),
        "v2_attempt_marker_bytes": 2171,
        "v2_attempt_marker_raw_sha256": V2_ATTEMPT_MARKER_RAW_SHA256,
        "v2_validated_current_head_sha256": v2_status["status"][
            "validated_current_head_sha256"
        ],
        "v2_validated_preparation_event_count": v2_status["status"][
            "validated_preparation_event_count"
        ],
        "v2_preparation_file_count": v2_status["custody"]["preparation_file_count"],
        "v2_preparation_directory_count": v2_status["custody"][
            "preparation_directory_count"
        ],
        "v2_preparation_file_mode_octal": "0600",
        "v2_preparation_directory_mode_octal": "0700",
        "v2_preparation_files_nlink_one": True,
        "v2_preparation_symlink_count": 0,
        "v2_capsule": dict(v2_status["custody"]["capsule"]),
        "v2_raw_runtime_envelopes_persisted": False,
        "v2_typed_terminal_ledger_event_present": False,
        "v2_unresolved_null_count": v2_status["custody"]["unresolved_null_count"],
        "v2_open_blocker_count": v2_status["custody"]["open_blocker_count"],
        "v2_d1_quarantine_row_count": v2_status["custody"]["d1_quarantine_row_count"],
        "v2_d1_quarantine_roster_sha256": v2_status["custody"][
            "d1_quarantine_roster_sha256"
        ],
        "v2_marker_attempt_spent": True,
        "v2_retry_permitted": False,
        "v2_execution_authorized": False,
        "custody_revalidated": True,
    }


def _canonical_command(v3_machine: Mapping[str, Any]) -> Sequence[str]:
    command = v3_machine["rehearsal_protocol"]["canonical_command"]
    if type(command) is not list or any(type(item) is not str for item in command):
        raise TerminalFailureRegistrationError("frozen command changed")
    return list(command)


def _expected_fixed_registration(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    root = _canonical_root(root)
    _audit_exact_bindings(root, V3_FREEZE_BINDINGS)
    v3_machine = _validate_v3_machine(root)
    custody = audit_terminal_custody(root)
    command = _canonical_command(v3_machine)
    return {
        "schema_version": SCHEMA,
        "registration_id": (
            "A1_R1_ACTIVATION_PREPARATION_V3_LIVE_HOST_ENVIRONMENT_REHEARSAL_"
            "TERMINAL_FAILURE_REGISTRATION_V1"
        ),
        "registration_mode": (
            "ADDITIVE_TERMINAL_REGISTRATION_WITH_READ_ONLY_VALIDATOR_"
            "EMPTY_TOOL_OUTPUT_POSTMORTEM"
        ),
        "scope": {
            "internal_evidence_only": True,
            "anonymous_or_public_release_permitted": False,
            "raw_conversation_or_tool_log_publication_permitted": False,
            "publication_safe_derivative_requires_fresh_anonymity_audit": True,
            "frozen_v3_files_edited": False,
            "v2_custody_edited": False,
            "isolated_pytest_temporary_fixture_custody_exercised": True,
            "synthetic_fixture_writes_are_noncanonical_and_nonoperational": True,
            "synthetic_fixture_operation_roster": [
                "CREATE_PAYLOAD",
                "CHMOD",
                "HARDLINK",
                "SYMLINK",
                "UNLINK",
                "FAKE_PYC",
                "SYNTHETIC_FUTURE_SUCCESSOR_ENTRY",
            ],
            "canonical_v2_or_v3_operational_path_mutated_by_hostiles": False,
            "canonical_predecessor_paths_read_for_audit": True,
        },
        "global_state": GLOBAL_STATE,
        "terminal_state": TERMINAL_STATE,
        "predecessor_v3_freeze": {
            "bindings": [dict(row) for row in V3_FREEZE_BINDINGS],
            "machine_record_sha256": V3_MACHINE_RECORD_SHA256,
            "static_freeze_remains_exact": True,
            "registered_user_authorization_provenance": v3_machine[
                "user_authorization_provenance"
            ],
        },
        "execution_observation": {
            "source": "ORCHESTRATOR_REPORTED_CANONICAL_ACTION_RESULT",
            "raw_command_receipt_bound_as_registered_workspace_artifact": False,
            "registered_command_vector": command,
            "registered_command_vector_sha256": _sha256(
                COMMAND_DOMAIN + _canonical(command)
            ),
            "orchestrator_reported_command_was_canonical": True,
            "command_match_independently_recomputed_from_raw_receipt": False,
            "canonical_rehearsal_invocation_ordinal": 0,
            "canonical_rehearsal_attempt_count": 1,
            "canonical_rehearsal_retry_count": 0,
            "reported_parent_action_exit_code": 70,
            "child_exit_code": None,
            "reported_wall_time_less_than_0_01_seconds": True,
            "reported_wall_time_bound_source": "ORCHESTRATOR_VISIBLE_TOOL_RESULT",
            "exact_wall_time_lexeme_bound_as_registered_workspace_artifact": False,
            "tool_output_field_byte_count": 0,
            "tool_output_field_sha256": _sha256(b""),
            "tool_output_original_token_count": 0,
            "os_level_combined_stream_observation_claimed": False,
            "stdout_byte_count_separately_observed": None,
            "stderr_byte_count_separately_observed": None,
            "typed_result_emitted": False,
            "typed_result_path_created": False,
            "durable_v3_attempt_marker_created": False,
            "procedural_spend_has_durable_operational_marker": False,
            "mechanical_one_shot_enforced": False,
            "filesystem_state_alone_can_encode_procedural_spend": False,
            "terminality_source": (
                "ADDITIVE_REGISTRATION_OF_ORCHESTRATOR_REPORTED_CANONICAL_" "INVOCATION"
            ),
            "attempt_procedurally_spent": True,
            "retry_forbidden_by_registration_and_original_authorization": True,
            "retry_permitted": False,
        },
        "collapsed_failure_diagnosis": {
            "failure_stage": "UNOBSERVED_COLLAPSED_EXCEPTION",
            "exact_failure_stage": None,
            "failed_gate": None,
            "supervisor_gate_vector": None,
            "child_launch_count": None,
            "child_launch_count_directly_observed": False,
            "no_child_launch_claimed": False,
            "child_exit_code": None,
            "exception_class": None,
            "collapsed_stage_roster": list(COLLAPSED_STAGE_ROSTER),
            "first_possible_source_step": "_require_live_supervisor_boundary",
            "timing_is_consistent_with_but_does_not_localize_an_early_failure": True,
            "timing_supports_failure_stage_localization": False,
            "timing_inference_is_direct_observation": False,
            "timing_inference_is_causal_proof": False,
            "deterministic_darwin_or_native_argv_cause_claimed": False,
            "downstream_stage_absence_claimed": False,
        },
        "post_failure_exploratory_context": {
            "context_source": "IMPLEMENTATION_TRANSCRIPT_AUDITED_TOOL_LOG_REPORT",
            "phase": "AFTER_FAILURE_BEFORE_TERMINAL_REGISTRATION",
            "initially_reported_process_count": 3,
            "first_corrected_process_count": 4,
            "final_transcript_audited_process_count": 5,
            "count_correction_chain": [3, 4, 5],
            "broad_vector_initially_reported_boolean_count": 15,
            "broad_vector_corrected_boolean_count": 16,
            "count_corrections_present": True,
            "raw_process_commands_bound_as_registered_workspace_artifacts": False,
            "raw_process_outputs_bound_as_registered_workspace_artifacts": False,
            "stderr_streams_separately_observed": False,
            "independently_verified_from_durable_raw_receipts": False,
            "probe_mode": "STDLIB_ONLY_PYTHON_C_NOT_DIRECT_FILE",
            "transcript_reported_authority_module_invocation_count": 0,
            "transcript_reported_runtime_child_invocation_count": 0,
            "transcript_reported_project_module_import_count": 0,
            "transcript_reported_explicit_application_entropy_api_call_count": 0,
            "transcript_reported_explicit_application_network_api_call_count": 0,
            "transcript_reported_explicit_application_workspace_output_write_count": 0,
            "os_level_entropy_contact_independently_observed": None,
            "os_level_network_contact_independently_observed": None,
            "os_level_filesystem_effects_independently_observed": None,
            "transcript_reported_raw_uid_cf_or_absolute_path_output_count": 0,
            "transcript_reported_output_shape": "BOOLEAN_ONLY_PRIVACY_SAFE_CONTEXT",
            "reported_probe_safety_facts_independently_verified_from_durable_receipts": False,
            "canonical_rehearsal_attempts_added": 0,
            "canonical_retry_count_added": 0,
            "canonical_stage_gate_or_child_count_narrowed": False,
            "context_is_canonical_failure_evidence": False,
            "probe_ordinal_roster_closed": True,
            "probe_count": 5,
            "reported_process_exit_code_vector": [0, 0, 0, 0, 0],
            "reported_process_exit_codes_source": (
                "IMPLEMENTATION_TRANSCRIPT_TOOL_LOG_REPORT"
            ),
            "further_contextual_probe_permitted": False,
            "covered_by_frozen_rehearsal_route": False,
            "separate_exact_user_authorization_bound": False,
            "authorization_for_contextual_probes_claimed": False,
            "unexpected_long_absolute_argv0_is_future_portability_hypothesis_only": True,
            "probe_roster": [dict(row) for row in PROBE_ROSTER],
        },
        "frozen_status_defect": {
            "status_projection_source": "FROZEN_SOURCE_PLUS_LSTAT_ABSENCE_INFERENCE",
            "direct_status_invocation_used_as_postmortem_evidence": False,
            "post_failure_status_raw_receipt_bound_as_registered_workspace_artifact": False,
            "frozen_status_result_state": "ABSENT",
            "frozen_status_milestone_state": FROZEN_PRE_RUN_STATE,
            "procedurally_spent_attempt_represented": False,
            "empty_tool_output_exit_without_result_represented": False,
            "transition_complete_for_no_result_attempt": False,
            "frozen_status_must_not_authorize_retry": True,
            "absent_v3_filesystem_is_indistinguishable_from_true_pre_run": True,
            "frozen_status_files_edited": False,
        },
        "terminal_custody": custody,
        "state_preservation": {
            "projection_source": "REOPENED_FROZEN_V2_TERMINAL_CUSTODY",
            "underlying_rosters_recomputed_by_postmortem": False,
            "unresolved_null_count": custody["v2_unresolved_null_count"],
            "open_blocker_count": custody["v2_open_blocker_count"],
            "d1_quarantine_row_count": custody["v2_d1_quarantine_row_count"],
            "d1_quarantine_roster_sha256": custody["v2_d1_quarantine_roster_sha256"],
            "d1_execution_admissible": False,
        },
        "future_v4_boundary": {
            "v3_result_marker_root_required_to_remain_absent_and_nonreusable": True,
            "v3_namespace_reuse_permitted": False,
            "future_v3_physical_absence_mechanically_guaranteed": False,
            "future_version_label": "V4",
            "exact_future_v4_operational_paths_frozen_here": False,
            "durable_loader_revalidates_future_v4_absence": False,
            "future_v4_must_be_wholly_disjoint_from_v2_and_v3": True,
            "postmortem_defines_or_claims_exact_v4_operational_path": False,
            "future_v4_must_bind_all_four_terminal_registration_files_by_raw_sha256": True,
            "future_v4_must_bind_this_registration_record_sha256": True,
            "future_v4_loader_must_revalidate_v3_terminal_custody": True,
            "v3_canonical_attempt_count_to_carry": 1,
            "v3_retry_count_to_carry": 0,
            "v3_terminal_state_to_carry": TERMINAL_STATE,
            "v4_is_new_disjoint_version_attempt_not_v3_retry": True,
            "v3_spent_namespace_must_be_reopened_before_any_v4_authority_route": True,
            "fresh_v4_freeze_and_exact_audit_required": True,
            "fresh_exact_user_authorization_required": True,
            "typed_privacy_safe_supervisor_failure_receipt_required_for_every_prechild_failure": True,
            "typed_prechild_admission_receipt_required_before_any_child_launch": True,
            "outer_transport_must_preserve_failure_or_admission_typed_outcome": True,
            "fresh_disjoint_v4_attempt_identity_and_nonce_required": True,
            "durable_no_clobber_v4_attempt_spend_required_before_any_live_evaluation": True,
            "v4_attempt_spend_publication_must_use_o_excl_and_fsync": True,
            "if_v4_nonce_uses_entropy_durable_o_excl_reservation_must_precede_sole_draw": True,
            "v4_partial_reservation_or_postdraw_failure_must_be_terminal_spent": True,
            "v4_sole_writer_ledger_or_equivalent_required": True,
            "v4_typed_terminal_outcome_must_be_no_clobber_locally_persisted_independent_of_stdout_or_tool_transport": True,
            "v4_replay_or_retry_must_fail_closed": True,
            "post_outcome_probe_context_must_be_disclosed_as_prior_knowledge": True,
            "v4_authorized_at_terminal_registration": False,
            "runtime_approval_rank_training_production_science_authorized": False,
        },
        "nonclaims": {
            "postmortem_edited_any_frozen_v3_file": False,
            "postmortem_edited_v2_custody": False,
            "postmortem_retried_v3_authority": False,
            "postmortem_invoked_v3_runtime_child": False,
            "postmortem_created_v3_result": False,
            "postmortem_created_v3_marker": False,
            "postmortem_created_v3_root": False,
            "exact_failure_stage_claimed": False,
            "exact_failed_gate_claimed": False,
            "child_launch_count_claimed": False,
            "child_exit_code_claimed": False,
            "exploratory_probe_context_admitted_as_canonical_evidence": False,
            "runtime_candidate_or_approval_created": False,
            "rank_execution_performed": False,
            "training_execution_performed": False,
            "production_execution_performed": False,
            "scientific_execution_performed": False,
            "manuscript_or_submission_claim_promoted": False,
            "explicit_application_network_api_invoked_by_postmortem_registration": False,
            "explicit_application_entropy_api_invoked_by_postmortem_registration": False,
            "postmortem_authorized_v4": False,
        },
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
        "nlink": information.st_nlink,
        "is_regular_file": stat.S_ISREG(information.st_mode),
        "is_symlink": stat.S_ISLNK(information.st_mode),
    }


def _build_registration_payload(root: Path = WORKSPACE_ROOT) -> bytes:
    root = _canonical_root(root)
    record = _expected_fixed_registration(root)
    record["registration_bindings"] = [
        _binding_row(root, ordinal, role, relative)
        for ordinal, (role, relative) in enumerate(
            (
                ("HUMAN_REGISTRATION", HUMAN_PATH),
                ("READ_ONLY_VALIDATOR", VALIDATOR_PATH),
                ("HOSTILE_TEST", TEST_PATH),
            )
        )
    ]
    record["record_sha256"] = None
    record["record_sha256"] = _sha256(REGISTRATION_DOMAIN + _canonical(record))
    return _canonical(record) + b"\n"


def _validate_machine_payload(root: Path, payload: bytes) -> Dict[str, Any]:
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TerminalFailureRegistrationError("machine record is not JSON") from error
    if type(record) is not dict or payload != _canonical(record) + b"\n":
        raise TerminalFailureRegistrationError("machine record is not canonical")
    fixed = _expected_fixed_registration(root)
    if set(record) != set(fixed) | {"registration_bindings", "record_sha256"}:
        raise TerminalFailureRegistrationError("machine fields changed")
    for key, expected in fixed.items():
        if type(record[key]) is not type(expected) or _canonical(
            record[key]
        ) != _canonical(expected):
            raise TerminalFailureRegistrationError("machine field changed: " + key)
    expected_paths = (HUMAN_PATH, VALIDATOR_PATH, TEST_PATH)
    expected_roles = ("HUMAN_REGISTRATION", "READ_ONLY_VALIDATOR", "HOSTILE_TEST")
    bindings = record["registration_bindings"]
    if type(bindings) is not list or len(bindings) != 3:
        raise TerminalFailureRegistrationError("registration bindings changed")
    for ordinal, (claimed, role, relative) in enumerate(
        zip(bindings, expected_roles, expected_paths)
    ):
        expected = _binding_row(root, ordinal, role, relative)
        if type(claimed) is not dict or _canonical(claimed) != _canonical(expected):
            raise TerminalFailureRegistrationError("registration binding changed")
    claimed = _require_sha256(record.get("record_sha256"), "registration self digest")
    body = dict(record)
    body["record_sha256"] = None
    if claimed != _sha256(REGISTRATION_DOMAIN + _canonical(body)):
        raise TerminalFailureRegistrationError("registration self digest changed")
    return record


def _load_machine(root: Path) -> Tuple[bytes, Dict[str, Any]]:
    payload, _ = _read_stable_file(root, MACHINE_PATH)
    record = _validate_machine_payload(root, payload)
    repeated, _ = _read_stable_file(root, MACHINE_PATH)
    if repeated != payload:
        raise TerminalFailureRegistrationError("machine changed during load")
    return payload, record


class TerminalFailureQualification:
    __slots__ = ("_registration", "_custody", "_record_sha256")

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise TypeError("qualification is constructed only by the canonical loader")

    def registration(self) -> Dict[str, Any]:
        return json.loads(self._registration.decode("ascii"))

    def custody(self) -> Dict[str, Any]:
        return json.loads(self._custody.decode("ascii"))

    @property
    def record_sha256(self) -> str:
        return self._record_sha256

    def __setattr__(self, name: str, value: Any) -> None:
        del name, value
        raise AttributeError("qualification is immutable")


def load_qualification(
    workspace_root: Any = WORKSPACE_ROOT,
) -> TerminalFailureQualification:
    root = _canonical_root(workspace_root)
    custody = audit_terminal_custody(root)
    _, registration = _load_machine(root)
    repeated = audit_terminal_custody(root)
    _, repeated_registration = _load_machine(root)
    if _canonical(custody) != _canonical(repeated):
        raise TerminalFailureRegistrationError("custody changed during qualification")
    if _canonical(registration) != _canonical(repeated_registration):
        raise TerminalFailureRegistrationError(
            "registration bindings changed during qualification"
        )
    value = object.__new__(TerminalFailureQualification)
    object.__setattr__(value, "_registration", _canonical(registration))
    object.__setattr__(value, "_custody", _canonical(custody))
    object.__setattr__(value, "_record_sha256", registration["record_sha256"])
    return value


def status(workspace_root: Any = WORKSPACE_ROOT) -> Dict[str, Any]:
    qualification = load_qualification(workspace_root)
    custody = qualification.custody()
    return {
        "schema": STATUS_SCHEMA,
        "global_state": GLOBAL_STATE,
        "terminal_state": TERMINAL_STATE,
        "canonical_rehearsal_attempt_count": 1,
        "canonical_rehearsal_retry_count": 0,
        "parent_action_exit_code": 70,
        "failure_stage": "UNOBSERVED_COLLAPSED_EXCEPTION",
        "failed_gate": None,
        "child_launch_count": None,
        "typed_result_present": False,
        "v3_result_lstat_absent": custody["v3_result_lstat_absent"],
        "v3_marker_lstat_absent": custody["v3_marker_lstat_absent"],
        "v3_root_lstat_absent": custody["v3_root_lstat_absent"],
        "frozen_status_still_reports_pre_run": True,
        "post_failure_context_process_count": 5,
        "post_failure_context_admissible_as_canonical_evidence": False,
        "retry_permitted": False,
        "v4_authorized_at_terminal_registration": False,
        "future_v4_authorization_assessed_by_this_status": False,
        "execution_authorized": False,
        "registration_record_sha256": qualification.record_sha256,
    }


__all__ = [
    "GLOBAL_STATE",
    "HUMAN_PATH",
    "MACHINE_PATH",
    "PROBE_ROSTER",
    "PROBE_ZERO_FIELD_ROSTER",
    "QUALIFICATION_SCHEMA",
    "REGISTRATION_DOMAIN",
    "SCHEMA",
    "TERMINAL_STATE",
    "TEST_PATH",
    "TerminalFailureQualification",
    "TerminalFailureRegistrationError",
    "VALIDATOR_PATH",
    "V3_FREEZE_BINDINGS",
    "V3_MACHINE_RECORD_SHA256",
    "audit_terminal_custody",
    "load_qualification",
    "status",
]
