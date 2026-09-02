"""Read-only custody registration for the single terminal-PASS V4 rehearsal.

This module has no writer, subprocess, child, entropy, network, data-access,
runtime-approval, or scientific route.  It reopens the already durable V4
marker and ledger, treats event ordinal 3 as the sole authoritative terminal
record, checks its projections, and preserves V3/V2 and preregistration state.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from types import ModuleType
from typing import Any, Dict, Mapping, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = (
    "heterodiff-manuscript-v3-a1-r1-activation-preparation-v4-transition-safe-"
    "live-host-environment-rehearsal-terminal-pass-registration-v1"
)
QUALIFICATION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-transition-safe-live-host-"
    "environment-rehearsal-terminal-pass-qualification-v1"
)
STATUS_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-transition-safe-live-host-"
    "environment-rehearsal-terminal-pass-status-v1"
)
REGISTRATION_DOMAIN = (SCHEMA + "\0").encode("ascii")
INVENTORY_DOMAIN = (SCHEMA + "-custody-inventory-v1\0").encode("ascii")
VISIBLE_AUTHORIZATION_DOMAIN = (
    b"heterodiff-manuscript-v3-a1-r1-activation-preparation-v4-transition-safe-"
    b"live-host-environment-rehearsal-terminal-pass-registration-visible-"
    b"authorization-v1\0"
)

GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
TERMINAL_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_TERMINAL_REHEARSAL_PASS_NO_RETRY_"
    "NO_RUNTIME_APPROVAL_NO_SCIENTIFIC_EXECUTION_AUTHORITY"
)
V3_TERMINAL_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V3_REHEARSAL_ATTEMPT_SPENT_TERMINAL_"
    "EXIT_70_EMPTY_TOOL_OUTPUT_FIELD_NO_TYPED_RESULT_NO_RETRY_NO_MARKER_"
    "NOT_EXECUTABLE"
)
V2_TERMINAL_STATE = (
    "A1_R1_ACTIVATION_PREPARATION_V2_ATTEMPT_SPENT_TERMINAL_RUNTIME_"
    "CAPTURE_A_CHILD_FAILED_NO_BINDING_NO_RETRY"
)

HUMAN_PATH = (
    "manuscript_v3/a1_r1_activation_preparation_v4_transition_safe_live_host_"
    "environment_rehearsal_terminal_pass_registration_v1.md"
)
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_terminal_pass_"
    "registration_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/finite_association_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_terminal_pass_"
    "registration_v1.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_a1_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_terminal_pass_"
    "registration_v1.py"
)

V4_HUMAN_PATH = (
    "manuscript_v3/a1_r1_activation_preparation_v4_transition_safe_live_host_"
    "environment_rehearsal_freeze_v1.md"
)
V4_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_freeze_v1.json"
)
V4_CONTRACTS_PATH = (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_contracts_v4.py"
)
V4_AUTHORITY_PATH = (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_authority_v4.py"
)
V4_RUNTIME_PATH = (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_runtime_v4.py"
)
V4_TEST_PATH = (
    "tests/unit/test_manuscript_v3_a1_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_freeze_v1.py"
)
AUTHORIZATION_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "execution_authorization_v1.json"
)
MARKER_PATH = "artifacts/a1_r1_activation_preparation_v4.attempt.json"
PREPARATION_ROOT_PATH = "artifacts/a1_r1_activation_preparation_v4"
LEDGER_PATH = PREPARATION_ROOT_PATH + "/ledger"
EVENTS_PATH = LEDGER_PATH + "/events"
LOCK_PATH = LEDGER_PATH + "/writer.lock"
GENESIS_PATH = LEDGER_PATH + "/genesis.json"
EVENT_PATHS = tuple(EVENTS_PATH + f"/{ordinal:020d}.json" for ordinal in range(4))
TERMINAL_PATH = LEDGER_PATH + "/terminal.json"
RESULT_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_result_v1.json"
)

V3_HUMAN_PATH = (
    "manuscript_v3/a1_r1_activation_preparation_v3_live_host_environment_"
    "rehearsal_terminal_failure_registration_v1.md"
)
V3_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v3_live_"
    "host_environment_rehearsal_terminal_failure_registration_v1.json"
)
V3_VALIDATOR_PATH = (
    "research/diagnostics/finite_association_r1_activation_preparation_v3_"
    "live_host_environment_rehearsal_terminal_failure_registration_v1.py"
)
V3_TEST_PATH = (
    "tests/unit/test_manuscript_v3_a1_r1_activation_preparation_v3_live_host_"
    "environment_rehearsal_terminal_failure_registration_v1.py"
)

V2_HUMAN_PATH = (
    "manuscript_v3/a1_r1_activation_preparation_v2_terminal_failure_"
    "registration_v1.md"
)
V2_MACHINE_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v2_"
    "terminal_failure_registration_v1.json"
)
V2_VALIDATOR_PATH = (
    "research/diagnostics/finite_association_r1_activation_preparation_v2_"
    "terminal_failure_registration_v1.py"
)
V2_TEST_PATH = (
    "tests/unit/test_manuscript_v3_a1_r1_activation_preparation_v2_terminal_"
    "failure_registration_v1.py"
)

PREREGISTRATION_PATH = (
    "research/fixtures/manuscript_v3_execution_preregistration_v1.json"
)
PREEXECUTION_CLOSURE_PATH = (
    "research/fixtures/manuscript_v3_execution_preregistration_"
    "preexecution_closure_v2.json"
)

V4_STATIC_BINDINGS = (
    (
        0,
        "V4_HUMAN_FREEZE",
        V4_HUMAN_PATH,
        17523,
        "2c472259323ace81c4a1991316a88ced749f99f6601c780f138234e78775ca34",
    ),
    (
        1,
        "V4_MACHINE_FREEZE",
        V4_MACHINE_PATH,
        22342,
        "ed9ea2bac212bcac71614ce7adcdabc8607912940eec88452c3e83a3e433376f",
    ),
    (
        2,
        "V4_CONTRACTS",
        V4_CONTRACTS_PATH,
        76189,
        "b3453d980d4f1a9f4312aa04acaa18c9369b7144d5b9ba7abe6cc368def441c2",
    ),
    (
        3,
        "V4_SOLE_WRITER_AUTHORITY",
        V4_AUTHORITY_PATH,
        141576,
        "02cedf038f3272b8aabc53ae16abf0b979f02a46f7103d0071bc8fad188c5b64",
    ),
    (
        4,
        "V4_ENVIRONMENT_CHILD",
        V4_RUNTIME_PATH,
        42900,
        "e2d2924dac36fa4114083d535166af87db590476fbf1bba9b01361404eda3bc2",
    ),
    (
        5,
        "V4_HOSTILE_TEST",
        V4_TEST_PATH,
        126608,
        "14cfb3cb7b256c187b2a1179c073d2c515048bb04c53211e70bbb08e0a54a03b",
    ),
)
V4_MACHINE_RECORD_SHA256 = (
    "c8ed3efc4d86b81777ced988c612990e3ea7ab25a68d1457c040d9363ecac282"
)
V4_STATIC_PLAN_SHA256 = (
    "6121d0db6fa021b1b173c8ff2321d229c4d2f3ba4faf94810e872a7f21b0b8a4"
)

V3_TERMINAL_BINDINGS = (
    (
        0,
        "V3_HUMAN_TERMINAL_REGISTRATION",
        V3_HUMAN_PATH,
        13052,
        "f89fcf120c3afdd4930621c325e3daec7715ba28443c1a9f191a0ac39a163c71",
    ),
    (
        1,
        "V3_MACHINE_TERMINAL_REGISTRATION",
        V3_MACHINE_PATH,
        21053,
        "282188fc035c835e54acb0da6f1cdafa0a3d9d4f98e89650180b583ba31218c7",
    ),
    (
        2,
        "V3_READ_ONLY_VALIDATOR",
        V3_VALIDATOR_PATH,
        44262,
        "2ae995d7609778f9201e3a90a2861c74898dfdc357b3f0b6f75b46bc68ce78bd",
    ),
    (
        3,
        "V3_HOSTILE_TEST",
        V3_TEST_PATH,
        26261,
        "6872b0923e118c4ceee297d5c8deb7d479a930892338596ce1751c055f29a2a5",
    ),
)
V3_TERMINAL_RECORD_SHA256 = (
    "69f730c8579c25750240831141f67777e8477b2b0ad93eab632ef7df4549216a"
)

V2_TERMINAL_BINDINGS = (
    (
        0,
        "V2_HUMAN_TERMINAL_REGISTRATION",
        V2_HUMAN_PATH,
        11507,
        "c29302fadc4a5c6a81a963442c85a681c92791ad664482267e80ef6d75f546ed",
    ),
    (
        1,
        "V2_MACHINE_TERMINAL_REGISTRATION",
        V2_MACHINE_PATH,
        17232,
        "bc73165ba905db1f26c5c81e2aebaf644e5e8009bd00daa477469479674d3085",
    ),
    (
        2,
        "V2_READ_ONLY_VALIDATOR",
        V2_VALIDATOR_PATH,
        62047,
        "ce59c0d855d22eea01e0091110ab6e928d071fe57ba1416f6e0ccab0e5bcf671",
    ),
    (
        3,
        "V2_HOSTILE_TEST",
        V2_TEST_PATH,
        19591,
        "7f28086bfeaab835241296961bfc91461789cadce6780ef38009569fd2189d5f",
    ),
)
V2_TERMINAL_RECORD_SHA256 = (
    "da57dda788f5de2b2a34ed30bdaf7f692db98696a00e420aa0484d44127b6ed0"
)

AUTHORIZATION_RAW_SHA256 = (
    "4d717ec020963e326d087ed0ab2222b5ed7db3de1036df8bedc9e45fae8cc33b"
)
AUTHORIZATION_RECORD_SHA256 = (
    "d818148364ffae575006d8277987c36e96e3323998ffab4fc2310d2d3c564c54"
)
AUTHORIZATION_CONTEXT_SHA256 = (
    "3e989c3935c829a5920992b29de6001369c29c9fb25f686eb44ee48be6026417"
)
V4_VISIBLE_ASSENT_SHA256 = (
    "33c38693197abe2849d02736250138322c452c4294552258757cfd5ae3a77994"
)
ATTEMPT_ID_SHA256 = "62ec7fcd893509c7ddf13cb16f38bbf600884dcb8c56158308dd9326b1464b20"
ATTEMPT_NONCE_SHA256 = (
    "963e04cee246a58c7c3c6a3643625913fd852c050c8876829f2c39d980a16e9d"
)

AUTHORIZATION_QUESTION = (
    "Do you authorize an additive V4 terminal-PASS custody registration only—"
    "no rerun, runtime approval, or science?"
)
AUTHORIZATION_ANSWER = "Yes."
AUTHORIZATION_COMBINED = "4- " + AUTHORIZATION_QUESTION + " " + AUTHORIZATION_ANSWER
AUTHORIZATION_QUESTION_SHA256 = (
    "088f9af040c2726d573d0cca4f5ea86d8423716d8da952ad532df7e972396181"
)
AUTHORIZATION_ANSWER_SHA256 = (
    "5f9a2b795615ba6a3d5455fd5624d773fbca5bcd16249c421fd37411dc9837da"
)
AUTHORIZATION_COMBINED_SHA256 = (
    "3ce2db7e58bb96db7b670ba3904708e59a3c96d71a53bb7d3c1c68460e56c60c"
)
AUTHORIZATION_DOMAIN_COMBINED_SHA256 = (
    "70993a9676d38bfd218ee7c2324accfcfca13fee4c05ee830764ec8c04bf4067"
)
AUTHORIZATION_RECORD_BINDING_SHA256 = (
    "1dd709fbebe096dc487b5d02efdf0c7f951874aa20ab02331523ee85acbfe31a"
)

PREREGISTRATION_RAW_SHA256 = (
    "edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706"
)
PREEXECUTION_CLOSURE_RAW_SHA256 = (
    "11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db"
)
PREEXECUTION_CLOSURE_RECORD_SHA256 = (
    "a393df8432e8ffd1b01368879290e090474ce34ab5b67edb102e3400b6cecae4"
)
D1_QUARANTINE_ROSTER_SHA256 = (
    "1efbc36a3bdba6c052900ec3131abc2ead3766bafc43bce435e1698a79f19a14"
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
TRANSPORT_GATE_ORDER = (
    "child_spawn_succeeded",
    "child_stdin_request_fully_written",
    "child_timeout_absent",
    "child_stdout_eof_and_within_bound",
    "child_stderr_eof_and_empty",
    "child_process_reap_observed",
    "child_exit_zero",
    "child_contract_exact",
    "postflight_custody_exact",
)
CHILD_GATE_ORDER = (
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

OPERATIONAL_FILE_EXPECTATIONS = (
    (
        "EXECUTION_AUTHORIZATION",
        AUTHORIZATION_PATH,
        3165,
        AUTHORIZATION_RAW_SHA256,
        0o644,
    ),
    (
        "ATTEMPT_MARKER",
        MARKER_PATH,
        1265,
        "1a4c1251d67041b38bfe085f23e2f523ad3ace2cc3aef5cfd2ef7d3e0839a95b",
        0o600,
    ),
    ("WRITER_LOCK", LOCK_PATH, 0, hashlib.sha256(b"").hexdigest(), 0o600),
    (
        "LEDGER_GENESIS",
        GENESIS_PATH,
        1195,
        "01224e4eca652e747a72bf82dc74d8c6ddcb04d558a3040decf698f44737b93f",
        0o600,
    ),
    (
        "EVENT_0_EVALUATION_CLAIM",
        EVENT_PATHS[0],
        1144,
        "80b0dcb0d75641de598bc4cc1a865714bcc039a6ac4e3ae921bec7ba2a85d396",
        0o600,
    ),
    (
        "EVENT_1_PRECHILD_ADMISSION",
        EVENT_PATHS[1],
        2102,
        "8113b87aaba3c25b42633e9756677b78e571d9d2a99a511964c64626fac3e907",
        0o600,
    ),
    (
        "EVENT_2_CHILD_LAUNCH_CLAIM",
        EVENT_PATHS[2],
        2883,
        "5d16691b6af43297242ce8b4ccd4ee22032546ac70ce8d0a5fb03e398e8940c3",
        0o600,
    ),
    (
        "EVENT_3_TERMINAL_OUTCOME",
        EVENT_PATHS[3],
        4539,
        "05dbee5babf2e4eb4ca73ecf9bcc3c8ee145eef766b5a1a346e9eda1e0421672",
        0o600,
    ),
    (
        "LOCAL_TERMINAL_PROJECTION",
        TERMINAL_PATH,
        1582,
        "fda70a9b187ff12b7c3157b2ec47b63843e8c1b7f5ab6d567f52d809b83f8628",
        0o600,
    ),
    (
        "PUBLISHED_RESULT",
        RESULT_PATH,
        977,
        "bd097ec53450eff70a5c44fd44721b75b7bd9cb5bc8573be7a45e08742832637",
        0o644,
    ),
)
DIRECTORY_EXPECTATIONS = (
    ("PREPARATION_ROOT", PREPARATION_ROOT_PATH, 0o700, 3, ("ledger",)),
    (
        "LEDGER_DIRECTORY",
        LEDGER_PATH,
        0o700,
        6,
        ("events", "genesis.json", "terminal.json", "writer.lock"),
    ),
    (
        "EVENTS_DIRECTORY",
        EVENTS_PATH,
        0o700,
        6,
        tuple(f"{i:020d}.json" for i in range(4)),
    ),
)
INVENTORY_SHA256 = "aeefd92513dc788260d1966b2564003ced8beb60958eb7d5020bf28149ae00f0"


class TerminalPassRegistrationError(ValueError):
    """The observed bytes are outside the exact terminal-PASS registration."""


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise TerminalPassRegistrationError("value is not canonical JSON") from error


def _file_bytes(value: Any) -> bytes:
    return _canonical(value) + b"\n"


def _sha256(payload: bytes) -> str:
    if type(payload) is not bytes:
        raise TerminalPassRegistrationError("digest input must be exact bytes")
    return hashlib.sha256(payload).hexdigest()


def _require_sha256(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TerminalPassRegistrationError(label + " is not lowercase SHA-256")
    return value


def _exact(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected) or _canonical(actual) != _canonical(expected):
        raise TerminalPassRegistrationError(label + " changed")


def _canonical_root(root: Any) -> Path:
    candidate = Path(root).absolute()
    if candidate != WORKSPACE_ROOT or candidate.resolve(strict=True) != WORKSPACE_ROOT:
        raise TerminalPassRegistrationError("only canonical workspace is auditable")
    information = candidate.lstat()
    if not stat.S_ISDIR(information.st_mode) or stat.S_ISLNK(information.st_mode):
        raise TerminalPassRegistrationError("workspace root custody changed")
    return candidate


def _normalized_relative_path(relative: Any) -> str:
    if type(relative) is not str or not relative or "\\" in relative:
        raise TerminalPassRegistrationError("path is not normalized")
    parsed = PurePosixPath(relative)
    if (
        parsed.is_absolute()
        or relative != parsed.as_posix()
        or any(part in ("", ".", "..") for part in parsed.parts)
    ):
        raise TerminalPassRegistrationError("path is not normalized")
    return relative


def _directory_fingerprint(info: os.stat_result) -> Tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_uid,
        info.st_gid,
        info.st_nlink,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _file_fingerprint(info: os.stat_result) -> Tuple[int, ...]:
    return _directory_fingerprint(info) + (info.st_size,)


def _ancestor_identities(
    root: Path, relative: str
) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
    current = root
    paths = [root]
    for part in PurePosixPath(_normalized_relative_path(relative)).parts[:-1]:
        current = current / part
        paths.append(current)
    rows = []
    for path in paths:
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise TerminalPassRegistrationError("ancestor custody changed")
        rows.append(
            (
                "" if path == root else path.relative_to(root).as_posix(),
                _directory_fingerprint(info),
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
        raise TerminalPassRegistrationError("file custody changed: " + relative)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if _file_fingerprint(opened) != _file_fingerprint(before):
            raise TerminalPassRegistrationError("file rebound: " + relative)
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    payload = b"".join(chunks)
    reopened = path.lstat()
    if (
        len(payload) != before.st_size
        or _file_fingerprint(before) != _file_fingerprint(after)
        or _file_fingerprint(after) != _file_fingerprint(reopened)
        or ancestors_before != _ancestor_identities(root, relative)
    ):
        raise TerminalPassRegistrationError("file changed during read: " + relative)
    return payload, reopened


def _read_directory(
    root: Path,
    relative: str,
    expected_mode: int,
    expected_nlink: int,
    expected_names: Sequence[str],
) -> os.stat_result:
    relative = _normalized_relative_path(relative)
    path = root / relative
    ancestors_before = _ancestor_identities(root, relative + "/leaf")
    before = path.lstat()
    if (
        not stat.S_ISDIR(before.st_mode)
        or stat.S_ISLNK(before.st_mode)
        or stat.S_IMODE(before.st_mode) != expected_mode
        or before.st_nlink != expected_nlink
    ):
        raise TerminalPassRegistrationError("directory custody changed: " + relative)
    names = tuple(sorted(entry.name for entry in os.scandir(path)))
    after = path.lstat()
    if names != tuple(sorted(expected_names)):
        raise TerminalPassRegistrationError("directory roster changed: " + relative)
    if _directory_fingerprint(before) != _directory_fingerprint(
        after
    ) or ancestors_before != _ancestor_identities(root, relative + "/leaf"):
        raise TerminalPassRegistrationError(
            "directory changed during read: " + relative
        )
    return after


def _parse_json(payload: bytes, label: str, newline: bool = True) -> Dict[str, Any]:
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TerminalPassRegistrationError(label + " is not JSON") from error
    expected = _file_bytes(value) if newline else _canonical(value)
    if type(value) is not dict or payload != expected:
        raise TerminalPassRegistrationError(label + " is not canonical")
    return value


def _read_canonical_json(
    root: Path, relative: str, mode: int = 0o644
) -> Tuple[bytes, Dict[str, Any]]:
    payload, _ = _read_stable_file(root, relative, mode)
    return payload, _parse_json(payload, relative)


def _validate_plain_self(record: Mapping[str, Any], key: str, label: str) -> str:
    if type(record) is not dict:
        raise TerminalPassRegistrationError(label + " is not a mapping")
    claimed = _require_sha256(record.get(key), label + " self digest")
    body = dict(record)
    body.pop(key, None)
    if claimed != _sha256(_canonical(body)):
        raise TerminalPassRegistrationError(label + " self digest changed")
    return claimed


def _binding_dict(row: Sequence[Any]) -> Dict[str, Any]:
    ordinal, role, path, size, digest = row
    return {
        "ordinal": ordinal,
        "role": role,
        "path": path,
        "bytes": size,
        "raw_sha256": digest,
        "lf_only": True,
        "mode_octal": "0644",
        "nlink": 1,
        "is_regular_file": True,
        "is_symlink": False,
    }


def _audit_binding_rows(root: Path, rows: Sequence[Sequence[Any]]) -> None:
    for ordinal, role, path, size, digest in rows:
        del role
        if type(ordinal) is not int:
            raise TerminalPassRegistrationError("binding ordinal changed")
        payload, _ = _read_stable_file(root, path)
        if len(payload) != size or _sha256(payload) != digest:
            raise TerminalPassRegistrationError("frozen bytes changed: " + path)


def _inventory_rows(root: Path) -> Sequence[Dict[str, Any]]:
    file_map = {
        role: (path, size, digest, mode)
        for role, path, size, digest, mode in OPERATIONAL_FILE_EXPECTATIONS
    }
    directory_map = {
        role: (path, mode, nlink, names)
        for role, path, mode, nlink, names in DIRECTORY_EXPECTATIONS
    }
    roles = (
        "EXECUTION_AUTHORIZATION",
        "ATTEMPT_MARKER",
        "PREPARATION_ROOT",
        "LEDGER_DIRECTORY",
        "EVENTS_DIRECTORY",
        "WRITER_LOCK",
        "LEDGER_GENESIS",
        "EVENT_0_EVALUATION_CLAIM",
        "EVENT_1_PRECHILD_ADMISSION",
        "EVENT_2_CHILD_LAUNCH_CLAIM",
        "EVENT_3_TERMINAL_OUTCOME",
        "LOCAL_TERMINAL_PROJECTION",
        "PUBLISHED_RESULT",
    )
    rows = []
    for ordinal, role in enumerate(roles):
        if role in file_map:
            path, size, digest, mode = file_map[role]
            payload, info = _read_stable_file(root, path, mode)
            if len(payload) != size or _sha256(payload) != digest:
                raise TerminalPassRegistrationError(
                    "operational bytes changed: " + path
                )
            rows.append(
                {
                    "ordinal": ordinal,
                    "role": role,
                    "path": path,
                    "entry_type": "REGULAR_FILE",
                    "bytes": len(payload),
                    "raw_sha256": _sha256(payload),
                    "mode_octal": format(stat.S_IMODE(info.st_mode), "04o"),
                    "nlink": info.st_nlink,
                    "is_symlink": False,
                }
            )
        else:
            path, mode, nlink, names = directory_map[role]
            info = _read_directory(root, path, mode, nlink, names)
            rows.append(
                {
                    "ordinal": ordinal,
                    "role": role,
                    "path": path,
                    "entry_type": "DIRECTORY",
                    "bytes": None,
                    "raw_sha256": None,
                    "mode_octal": format(stat.S_IMODE(info.st_mode), "04o"),
                    "nlink": info.st_nlink,
                    "is_symlink": False,
                }
            )
    if _sha256(INVENTORY_DOMAIN + _canonical(rows)) != INVENTORY_SHA256:
        raise TerminalPassRegistrationError("custody inventory digest changed")
    return rows


def _validate_authorization(record: Mapping[str, Any]) -> None:
    _validate_plain_self(record, "record_sha256", "execution authorization")
    expected = {
        "schema_version": "heterodiff-manuscript-v3-a1-r1-activation-preparation-v4-execution-authorization-v1",
        "v4_registration_record_sha256": V4_MACHINE_RECORD_SHA256,
        "v4_registration_raw_sha256": V4_STATIC_BINDINGS[1][4],
        "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
        "normalized_visible_assent_sha256": V4_VISIBLE_ASSENT_SHA256,
        "authorized_action": "V4_EXECUTE_ONCE",
        "authorized_attempt_count": 1,
        "authorized_child_launch_maximum": 1,
        "retry_count_authorized": 0,
        "deterministic_nonce": True,
        "entropy_authorized": False,
        "network_authorized": False,
        "runtime_approval_authorized": False,
        "rank_authorized": False,
        "training_authorized": False,
        "production_authorized": False,
        "scientific_execution_authorized": False,
        "manuscript_claim_authorized": False,
        "raw_transport_bytes_bound": False,
        "honest_host_procedural_authority": True,
        "cryptographic_user_authentication": False,
        "record_self_digests_are_user_authentication": False,
        "malicious_host_resistance_claimed": False,
    }
    for key, value in expected.items():
        _exact(record.get(key), value, "execution authorization." + key)
    outputs = record.get("authorized_output_paths")
    _exact(
        outputs,
        [
            AUTHORIZATION_PATH,
            MARKER_PATH,
            PREPARATION_ROOT_PATH,
            TERMINAL_PATH,
            RESULT_PATH,
        ],
        "authorized output paths",
    )


def _derive_attempt_identity() -> Tuple[str, str]:
    identity = {
        "attempt_ordinal": 0,
        "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
        "execution_authorization_raw_sha256": AUTHORIZATION_RAW_SHA256,
        "execution_authorization_record_sha256": AUTHORIZATION_RECORD_SHA256,
        "registration_record_sha256": V4_MACHINE_RECORD_SHA256,
        "visible_assent_sha256": V4_VISIBLE_ASSENT_SHA256,
    }
    attempt_id = _sha256(
        b"heterodiff-a1-r1-activation-preparation-v4-attempt-identity-v1\0"
        + _canonical(identity)
    )
    nonce = _sha256(
        b"heterodiff-a1-r1-activation-preparation-v4-deterministic-attempt-nonce-v1\0"
        + _canonical(
            {
                "attempt_id_sha256": attempt_id,
                "attempt_ordinal": 0,
                "marker_path": MARKER_PATH,
            }
        )
    )
    return attempt_id, nonce


def _all_true_gate_vector(
    value: Any, order: Sequence[str], label: str
) -> Dict[str, bool]:
    if type(value) is not dict or set(value) != set(order):
        raise TerminalPassRegistrationError(label + " roster changed")
    if any(type(value[key]) is not bool or value[key] is not True for key in order):
        raise TerminalPassRegistrationError(label + " did not pass exactly")
    return dict(value)


def _validate_operational_semantics(records: Mapping[str, Any]) -> Dict[str, Any]:
    required = {
        "authorization",
        "marker",
        "genesis",
        "event0",
        "event1",
        "event2",
        "event3",
        "terminal",
        "result",
    }
    if type(records) is not dict or set(records) != required:
        raise TerminalPassRegistrationError("operational record roster changed")
    authorization = records["authorization"]
    marker = records["marker"]
    genesis = records["genesis"]
    events = [records[f"event{i}"] for i in range(4)]
    terminal = records["terminal"]
    result = records["result"]
    _validate_authorization(authorization)
    _validate_plain_self(marker, "marker_sha256", "marker")
    _validate_plain_self(genesis, "genesis_sha256", "genesis")
    for ordinal, event in enumerate(events):
        _validate_plain_self(event, "event_sha256", f"event {ordinal}")
    _validate_plain_self(terminal, "terminal_sha256", "terminal projection")
    _validate_plain_self(result, "record_sha256", "published result")

    attempt_id, nonce = _derive_attempt_identity()
    _exact(attempt_id, ATTEMPT_ID_SHA256, "derived attempt identifier")
    _exact(nonce, ATTEMPT_NONCE_SHA256, "derived attempt nonce")
    marker_fixed = {
        "schema_version": "heterodiff-a1-r1-activation-preparation-v4-attempt-marker-v1",
        "attempt_id_sha256": attempt_id,
        "attempt_nonce_sha256": nonce,
        "attempt_ordinal": 0,
        "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
        "visible_assent_sha256": V4_VISIBLE_ASSENT_SHA256,
        "execution_authorization_raw_sha256": AUTHORIZATION_RAW_SHA256,
        "execution_authorization_record_sha256": AUTHORIZATION_RECORD_SHA256,
        "registration_raw_sha256": V4_STATIC_BINDINGS[1][4],
        "registration_record_sha256": V4_MACHINE_RECORD_SHA256,
        "entropy_draw_count": 0,
        "retry_permitted": False,
        "marker_path": MARKER_PATH,
        "nonce_kind": "DETERMINISTIC_NONSECRET_CUSTODY_IDENTIFIER",
    }
    for key, value in marker_fixed.items():
        _exact(marker.get(key), value, "marker." + key)

    genesis_fixed = {
        "schema_version": "heterodiff-a1-r1-activation-preparation-v4-ledger-genesis-v1",
        "attempt_id_sha256": attempt_id,
        "attempt_nonce_sha256": nonce,
        "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
        "visible_assent_sha256": V4_VISIBLE_ASSENT_SHA256,
        "execution_authorization_raw_sha256": AUTHORIZATION_RAW_SHA256,
        "execution_authorization_record_sha256": AUTHORIZATION_RECORD_SHA256,
        "registration_raw_sha256": V4_STATIC_BINDINGS[1][4],
        "registration_record_sha256": V4_MACHINE_RECORD_SHA256,
        "marker_raw_sha256": OPERATIONAL_FILE_EXPECTATIONS[1][3],
        "marker_sha256": marker["marker_sha256"],
        "event_count_before_genesis": 0,
        "global_state": GLOBAL_STATE,
        "retry_permitted": False,
    }
    for key, value in genesis_fixed.items():
        _exact(genesis.get(key), value, "genesis." + key)

    schemas = (
        "heterodiff-a1-r1-activation-preparation-v4-prechild-evaluation-claim-v1",
        "heterodiff-a1-r1-activation-preparation-v4-prechild-admission-v1",
        "heterodiff-a1-r1-activation-preparation-v4-child-launch-claim-v1",
        "heterodiff-a1-r1-activation-preparation-v4-terminal-outcome-v1",
    )
    kinds = (
        "PRECHILD_EVALUATION_CLAIM",
        "PRECHILD_ADMISSION",
        "CHILD_LAUNCH_CLAIM",
        "TERMINAL_OUTCOME",
    )
    previous_raw = _sha256(_file_bytes(genesis))
    previous_self = genesis["genesis_sha256"]
    previous_kind = "GENESIS"
    for ordinal, event in enumerate(events):
        for key, value in {
            "schema_version": schemas[ordinal],
            "event_kind": kinds[ordinal],
            "event_ordinal": ordinal,
            "attempt_id_sha256": attempt_id,
            "attempt_nonce_sha256": nonce,
            "registration_raw_sha256": V4_STATIC_BINDINGS[1][4],
            "registration_record_sha256": V4_MACHINE_RECORD_SHA256,
            "marker_raw_sha256": OPERATIONAL_FILE_EXPECTATIONS[1][3],
            "marker_sha256": marker["marker_sha256"],
            "previous_record_kind": previous_kind,
            "previous_record_raw_sha256": previous_raw,
            "previous_record_sha256": previous_self,
            "retry_permitted": False,
        }.items():
            _exact(event.get(key), value, f"event {ordinal}." + key)
        previous_raw = _sha256(_file_bytes(event))
        previous_self = event["event_sha256"]
        previous_kind = "EVENT"

    gates = _all_true_gate_vector(
        events[1].get("gate_vector"), PRECHILD_GATE_ORDER, "prechild gates"
    )
    _exact(
        events[1].get("gate_vector_sha256"),
        _sha256(_canonical(gates)),
        "prechild gate digest",
    )
    for key, value in {
        "failure_code": "NONE",
        "child_launch_count": 0,
        "runtime_approval_created": False,
        "scientific_execution_performed": False,
    }.items():
        _exact(events[1].get(key), value, "event 1." + key)

    request = events[2].get("runtime_request")
    if type(request) is not dict:
        raise TerminalPassRegistrationError("runtime request changed")
    _validate_plain_self(request, "request_sha256", "runtime request")
    request_raw = _file_bytes(request)
    for key, value in {
        "admission_event_sha256": events[1]["event_sha256"],
        "attempt_id_sha256": attempt_id,
        "attempt_nonce_sha256": nonce,
        "child_launch_ordinal": 0,
        "execution_authorization_raw_sha256": AUTHORIZATION_RAW_SHA256,
        "execution_authorization_record_sha256": AUTHORIZATION_RECORD_SHA256,
        "registration_raw_sha256": V4_STATIC_BINDINGS[1][4],
        "registration_record_sha256": V4_MACHINE_RECORD_SHA256,
        "network_requested": False,
        "raw_environment_requested": False,
        "scientific_import_or_execution_requested": False,
        "temporary_write_requested": False,
        "workspace_write_requested": False,
    }.items():
        _exact(request.get(key), value, "runtime request." + key)
    for key, value in {
        "admission_event_raw_sha256": _sha256(_file_bytes(events[1])),
        "admission_event_sha256": events[1]["event_sha256"],
        "child_launch_maximum": 1,
        "child_launch_ordinal": 0,
        "runtime_request_raw_sha256": _sha256(request_raw),
        "runtime_request_sha256": request["request_sha256"],
    }.items():
        _exact(events[2].get(key), value, "event 2." + key)

    transport = _all_true_gate_vector(
        events[3].get("transport_gate_vector"), TRANSPORT_GATE_ORDER, "transport gates"
    )
    _exact(
        events[3].get("transport_gate_vector_sha256"),
        _sha256(_canonical(transport)),
        "transport gate digest",
    )
    observation = events[3].get("child_observation")
    if type(observation) is not dict:
        raise TerminalPassRegistrationError("child observation changed")
    _validate_plain_self(observation, "observation_sha256", "child observation")
    observation_raw = _file_bytes(observation)
    child_gates = _all_true_gate_vector(
        observation.get("gate_vector"), CHILD_GATE_ORDER, "child gates"
    )
    _exact(
        observation.get("gate_vector_sha256"),
        _sha256(_canonical(child_gates)),
        "child gate digest",
    )
    for key, value in {
        "outcome": "PASS",
        "failure_code": "NONE",
        "child_launch_ordinal": 0,
        "child_process_ordinal": 0,
        "request_raw_sha256": _sha256(request_raw),
        "request_sha256": request["request_sha256"],
        "entropy_contacted": False,
        "network_contacted": False,
        "temporary_write_performed": False,
        "workspace_write_performed": False,
        "scientific_import_or_execution_performed": False,
        "raw_absolute_path_emitted": False,
        "raw_argv_emitted": False,
        "raw_environment_emitted": False,
        "raw_identity_emitted": False,
        "raw_stderr_emitted": False,
        "application_effect_claim_basis": "STATIC_CHILD_SOURCE_AND_ROUTE_CONTRACT_NOT_OS_INSTRUMENTATION",
    }.items():
        _exact(observation.get(key), value, "child observation." + key)
    event3_fixed = {
        "outcome": "PASS",
        "terminal_state": TERMINAL_STATE,
        "transport_failure_code": "NONE",
        "child_spawn_succeeded": True,
        "child_launch_claim_count": 1,
        "child_process_start_count": 1,
        "child_process_reap_observed": True,
        "child_exit_code_observed": True,
        "child_exit_code": 0,
        "child_timeout_observed": False,
        "child_stdin_captured_write_byte_count_observed": True,
        "child_stdin_captured_write_byte_count": 1332,
        "child_stdin_request_fully_written": True,
        "child_stdout_captured_byte_count_observed": True,
        "child_stdout_captured_byte_count": 1795,
        "child_stdout_eof_observed": True,
        "child_stdout_overflow_observed": False,
        "child_stderr_captured_byte_count_observed": True,
        "child_stderr_captured_byte_count": 0,
        "child_stderr_eof_observed": True,
        "child_stderr_overflow_observed": False,
        "child_observation_raw_sha256": _sha256(observation_raw),
        "child_observation_sha256": observation["observation_sha256"],
        "postflight_custody_exact": True,
        "raw_child_transport_persisted": False,
        "runtime_approval_created": False,
        "scientific_execution_performed": False,
    }
    for key, value in event3_fixed.items():
        _exact(events[3].get(key), value, "event 3." + key)

    for key, value in {
        "schema_version": "heterodiff-a1-r1-activation-preparation-v4-terminal-projection-v1",
        "attempt_id_sha256": attempt_id,
        "attempt_nonce_sha256": nonce,
        "registration_raw_sha256": V4_STATIC_BINDINGS[1][4],
        "registration_record_sha256": V4_MACHINE_RECORD_SHA256,
        "marker_raw_observed": True,
        "marker_self_valid": True,
        "marker_raw_sha256": OPERATIONAL_FILE_EXPECTATIONS[1][3],
        "marker_sha256": marker["marker_sha256"],
        "outcome": "PASS",
        "terminal_state": TERMINAL_STATE,
        "retry_permitted": False,
        "runtime_approval_created": False,
        "scientific_execution_performed": False,
        "authoritative_typed_event_present": True,
        "terminal_state_inferred_from_durable_prefix": False,
        "authoritative_event_schema": schemas[3],
        "authoritative_event_kind": kinds[3],
        "authoritative_event_ordinal": 3,
        "authoritative_event_raw_sha256": _sha256(_file_bytes(events[3])),
        "authoritative_event_sha256": events[3]["event_sha256"],
        "child_launch_claim_count": 1,
        "child_process_start_count": 1,
        "child_process_start_count_directly_observed": True,
    }.items():
        _exact(terminal.get(key), value, "terminal projection." + key)
    for key, value in {
        "schema_version": "heterodiff-a1-r1-activation-preparation-v4-published-result-v1",
        "attempt_id_sha256": attempt_id,
        "attempt_nonce_sha256": nonce,
        "registration_record_sha256": V4_MACHINE_RECORD_SHA256,
        "local_terminal_raw_sha256": _sha256(_file_bytes(terminal)),
        "local_terminal_sha256": terminal["terminal_sha256"],
        "outcome": "PASS",
        "terminal_state": TERMINAL_STATE,
        "retry_permitted": False,
        "runtime_approval_created": False,
        "scientific_execution_performed": False,
        "raw_environment_published": False,
        "raw_identity_published": False,
        "raw_path_or_argv_published": False,
    }.items():
        _exact(result.get(key), value, "published result." + key)
    return {
        "attempt_id_sha256": attempt_id,
        "attempt_nonce_sha256": nonce,
        "event3_sha256": events[3]["event_sha256"],
        "terminal_sha256": terminal["terminal_sha256"],
        "result_record_sha256": result["record_sha256"],
    }


def _load_operational_records(root: Path) -> Tuple[Dict[str, Any], Dict[str, bytes]]:
    paths = {
        "authorization": AUTHORIZATION_PATH,
        "marker": MARKER_PATH,
        "genesis": GENESIS_PATH,
        "event0": EVENT_PATHS[0],
        "event1": EVENT_PATHS[1],
        "event2": EVENT_PATHS[2],
        "event3": EVENT_PATHS[3],
        "terminal": TERMINAL_PATH,
        "result": RESULT_PATH,
    }
    modes = {
        "authorization": 0o644,
        "marker": 0o600,
        "genesis": 0o600,
        "event0": 0o600,
        "event1": 0o600,
        "event2": 0o600,
        "event3": 0o600,
        "terminal": 0o600,
        "result": 0o644,
    }
    raws: Dict[str, bytes] = {}
    records: Dict[str, Any] = {}
    for name, path in paths.items():
        raw, record = _read_canonical_json(root, path, modes[name])
        raws[name] = raw
        records[name] = record
    return records, raws


def _audit_v4_custody(root: Path) -> Dict[str, Any]:
    _audit_binding_rows(root, V4_STATIC_BINDINGS)
    machine_raw, machine = _read_canonical_json(root, V4_MACHINE_PATH)
    if (
        _sha256(machine_raw) != V4_STATIC_BINDINGS[1][4]
        or machine.get("record_sha256") != V4_MACHINE_RECORD_SHA256
        or machine.get("static_plan_sha256") != V4_STATIC_PLAN_SHA256
    ):
        raise TerminalPassRegistrationError("V4 static machine changed")
    rows = list(_inventory_rows(root))
    records, raws = _load_operational_records(root)
    semantics = _validate_operational_semantics(records)
    expected_raws = {
        "authorization": AUTHORIZATION_RAW_SHA256,
        "marker": OPERATIONAL_FILE_EXPECTATIONS[1][3],
        "genesis": OPERATIONAL_FILE_EXPECTATIONS[3][3],
        "event0": OPERATIONAL_FILE_EXPECTATIONS[4][3],
        "event1": OPERATIONAL_FILE_EXPECTATIONS[5][3],
        "event2": OPERATIONAL_FILE_EXPECTATIONS[6][3],
        "event3": OPERATIONAL_FILE_EXPECTATIONS[7][3],
        "terminal": OPERATIONAL_FILE_EXPECTATIONS[8][3],
        "result": OPERATIONAL_FILE_EXPECTATIONS[9][3],
    }
    for name, expected in expected_raws.items():
        if _sha256(raws[name]) != expected:
            raise TerminalPassRegistrationError(name + " raw digest changed")
    repeated_rows = list(_inventory_rows(root))
    repeated_records, repeated_raws = _load_operational_records(root)
    if (
        _canonical(rows) != _canonical(repeated_rows)
        or raws != repeated_raws
        or _canonical(records) != _canonical(repeated_records)
    ):
        raise TerminalPassRegistrationError("V4 custody changed during audit")
    return {"inventory": rows, "inventory_sha256": INVENTORY_SHA256, **semantics}


def _load_exact_v3_validator(root: Path) -> ModuleType:
    _audit_binding_rows(root, V3_TERMINAL_BINDINGS)
    payload, _ = _read_stable_file(root, V3_VALIDATOR_PATH)
    module = ModuleType("v3_terminal_failure_registration_for_v4_pass")
    module.__file__ = str(root / V3_VALIDATOR_PATH)
    module.__name__ = "v3_terminal_failure_registration_for_v4_pass"
    exec(compile(payload, module.__file__, "exec"), module.__dict__)
    return module


def _audit_predecessor_custody(root: Path) -> Dict[str, Any]:
    _audit_binding_rows(root, V3_TERMINAL_BINDINGS)
    _audit_binding_rows(root, V2_TERMINAL_BINDINGS)
    _, v3_machine = _read_canonical_json(root, V3_MACHINE_PATH)
    if v3_machine.get("record_sha256") != V3_TERMINAL_RECORD_SHA256:
        raise TerminalPassRegistrationError("V3 terminal self digest changed")
    v3_body = dict(v3_machine)
    v3_body["record_sha256"] = None
    if V3_TERMINAL_RECORD_SHA256 != _sha256(
        (v3_machine["schema_version"] + "\0").encode("ascii") + _canonical(v3_body)
    ):
        raise TerminalPassRegistrationError("V3 terminal semantic digest changed")
    module = _load_exact_v3_validator(root)
    status = module.status(root)
    custody = module.audit_terminal_custody(root)
    repeated_status = module.status(root)
    repeated_custody = module.audit_terminal_custody(root)
    if _canonical(status) != _canonical(repeated_status) or _canonical(
        custody
    ) != _canonical(repeated_custody):
        raise TerminalPassRegistrationError("predecessor custody changed during audit")
    exact = {
        "global_state": GLOBAL_STATE,
        "terminal_state": V3_TERMINAL_STATE,
        "canonical_rehearsal_attempt_count": 1,
        "canonical_rehearsal_retry_count": 0,
        "parent_action_exit_code": 70,
        "failure_stage": "UNOBSERVED_COLLAPSED_EXCEPTION",
        "failed_gate": None,
        "child_launch_count": None,
        "typed_result_present": False,
        "retry_permitted": False,
        "execution_authorized": False,
        "registration_record_sha256": V3_TERMINAL_RECORD_SHA256,
    }
    for key, value in exact.items():
        _exact(status.get(key), value, "V3 status." + key)
    if (
        custody.get("v2_terminal_registration_record_sha256")
        != V2_TERMINAL_RECORD_SHA256
        or custody.get("v2_attempt_marker_bytes") != 2171
        or custody.get("v2_attempt_marker_raw_sha256")
        != "e74195f33df40f255fbe4f956dd426a6a76676c93358f70e785f2f90c7db7cc4"
        or custody.get("v2_validated_preparation_event_count") != 3
        or custody.get("v2_validated_current_head_sha256")
        != "4ba4799fdfa3bf407ea269c035c6502114b9bae5b93bdde1b32c6ebe497646a5"
        or custody.get("v2_preparation_file_count") != 65
        or custody.get("v2_preparation_directory_count") != 20
        or custody.get("v2_preparation_symlink_count") != 0
        or custody.get("v2_capsule", {}).get("file_count") != 53
        or custody.get("v2_capsule", {}).get("directory_count") != 14
        or custody.get("v2_capsule", {}).get("inventory_sha256")
        != "c68e21aa648c4823bd87987399eb0ce76149adaa57c7b19b162783ad5dc01360"
        or custody.get("v2_retry_permitted") is not False
        or custody.get("v2_execution_authorized") is not False
    ):
        raise TerminalPassRegistrationError("V2 terminal custody changed")
    context = v3_machine.get("post_failure_exploratory_context")
    if (
        type(context) is not dict
        or context.get("probe_count") != 5
        or context.get("context_is_canonical_failure_evidence") is not False
        or context.get("independently_verified_from_durable_raw_receipts") is not False
        or context.get("raw_process_commands_bound_as_registered_workspace_artifacts")
        is not False
        or context.get("raw_process_outputs_bound_as_registered_workspace_artifacts")
        is not False
    ):
        raise TerminalPassRegistrationError("V3 probe quarantine changed")
    return {"v3_status": status, "v3_custody": custody}


def _count_nulls(value: Any) -> int:
    if value is None:
        return 1
    if type(value) is dict:
        return sum(_count_nulls(item) for item in value.values())
    if type(value) is list:
        return sum(_count_nulls(item) for item in value)
    return 0


def _audit_scientific_state(root: Path) -> Dict[str, Any]:
    prereg_raw, _ = _read_stable_file(root, PREREGISTRATION_PATH)
    if _sha256(prereg_raw) != PREREGISTRATION_RAW_SHA256:
        raise TerminalPassRegistrationError("historical preregistration changed")
    try:
        prereg = json.loads(prereg_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TerminalPassRegistrationError(
            "historical preregistration is not JSON"
        ) from error
    if type(prereg) is not dict or _count_nulls(prereg) != 174:
        raise TerminalPassRegistrationError("historical null count changed")
    if (
        prereg.get("freeze_predicate", {}).get(
            "test_data_unopened_before_freeze", "missing"
        )
        is not None
    ):
        raise TerminalPassRegistrationError("test-data-unopened state changed")
    closure_raw, _ = _read_stable_file(root, PREEXECUTION_CLOSURE_PATH)
    if _sha256(closure_raw) != PREEXECUTION_CLOSURE_RAW_SHA256:
        raise TerminalPassRegistrationError("preexecution closure changed")
    closure = _parse_json(closure_raw, PREEXECUTION_CLOSURE_PATH)
    closure_body = dict(closure)
    closure_body.pop("record_sha256", None)
    claimed = closure.get("record_sha256")
    if claimed != PREEXECUTION_CLOSURE_RECORD_SHA256 or claimed != _sha256(
        (closure["schema_version"] + "\0").encode("ascii") + _canonical(closure_body)
    ):
        raise TerminalPassRegistrationError("preexecution closure self digest changed")
    nulls = closure.get("null_projection", {})
    blockers = closure.get("blocker_projection", {})
    predicates = closure.get("freeze_predicate_projection", {}).get(
        "effective_predicate", {}
    )
    exact_nulls = {
        "historical_total_null_count": 174,
        "historical_preexecution_null_count": 168,
        "historical_deferred_postexecution_null_count": 6,
        "projected_resolved_pre_d1_null_count": 2,
        "effective_preexecution_unresolved_null_count": 166,
        "effective_deferred_postexecution_unresolved_null_count": 6,
        "effective_total_unresolved_null_count": 172,
        "historical_preregistration_mutated": False,
        "other_nulls_resolved": False,
    }
    for key, value in exact_nulls.items():
        _exact(nulls.get(key), value, "null projection." + key)
    _exact(
        len(closure.get("resolved_pre_d1_fields", [])), 2, "resolved pre-D1 field count"
    )
    _exact(blockers.get("effective_unresolved_blocker_count"), 12, "blocker count")
    _exact(blockers.get("blockers_closed_by_closure"), 0, "closed blocker count")
    _exact(
        blockers.get("effective_stage_counts"),
        {
            "CONFIRMATORY_EXECUTION": 10,
            "CLAIM_PROMOTION_AND_SUBMISSION_NOT_CONFIRMATORY_EXECUTION": 2,
        },
        "blocker stage counts",
    )
    for key in (
        "confirmatory_execution_authorized",
        "production_execution_authorized",
        "scientific_result_eligible",
        "claim_promoted",
    ):
        _exact(
            closure.get("state_preservation", {}).get(key),
            False,
            "state preservation." + key,
        )
    _exact(predicates.get("current_state"), GLOBAL_STATE, "effective global state")
    _exact(
        predicates.get("test_data_unopened_before_freeze", "missing"),
        None,
        "effective test-data-unopened state",
    )
    return {
        "historical_null_count": 174,
        "effective_unresolved_null_count": 172,
        "preexecution_unresolved_null_count": 166,
        "postexecution_unresolved_null_count": 6,
        "open_blocker_count": 12,
        "confirmatory_blocker_count": 10,
        "promotion_blocker_count": 2,
        "blockers_closed": 0,
        "test_data_unopened_before_freeze": None,
    }


def audit_terminal_custody(workspace_root: Any = WORKSPACE_ROOT) -> Dict[str, Any]:
    root = _canonical_root(workspace_root)
    v4 = _audit_v4_custody(root)
    predecessors = _audit_predecessor_custody(root)
    scientific = _audit_scientific_state(root)
    return {
        "schema": QUALIFICATION_SCHEMA,
        "global_state": GLOBAL_STATE,
        "terminal_state": TERMINAL_STATE,
        "authoritative_event_ordinal": 3,
        "authoritative_event_kind": "TERMINAL_OUTCOME",
        "outcome": "PASS",
        "attempt_spent": True,
        "retry_permitted": False,
        "runtime_approval_created": False,
        "scientific_execution_performed": False,
        "v4": v4,
        "predecessors": predecessors,
        "scientific_state": scientific,
    }


def _package_roster() -> Sequence[Dict[str, Any]]:
    return [
        {"ordinal": 0, "role": "HUMAN_REGISTRATION", "path": HUMAN_PATH},
        {"ordinal": 1, "role": "MACHINE_REGISTRATION", "path": MACHINE_PATH},
        {"ordinal": 2, "role": "READ_ONLY_VALIDATOR", "path": VALIDATOR_PATH},
        {"ordinal": 3, "role": "HOSTILE_TEST", "path": TEST_PATH},
    ]


def _expected_fixed_registration(root: Path = WORKSPACE_ROOT) -> Dict[str, Any]:
    root = _canonical_root(root)
    custody = audit_terminal_custody(root)
    del custody
    authorization_object = {
        "antecedent_visible_text": AUTHORIZATION_QUESTION,
        "normalized_combined_visible_text": AUTHORIZATION_COMBINED,
        "visible_assent_text": AUTHORIZATION_ANSWER,
        "visible_item_prefix": "4-",
    }
    return {
        "schema_version": SCHEMA,
        "registration_id": "A1_R1_ACTIVATION_PREPARATION_V4_TRANSITION_SAFE_LIVE_HOST_ENVIRONMENT_REHEARSAL_TERMINAL_PASS_REGISTRATION_V1",
        "registration_mode": "ADDITIVE_TERMINAL_PASS_CUSTODY_REGISTRATION_WITH_READ_ONLY_VALIDATOR_NO_RERUN",
        "global_state": GLOBAL_STATE,
        "terminal_state": TERMINAL_STATE,
        "authorization_provenance": {
            "source": "CONVERSATION_VISIBLE_ITEM_4",
            "visible_item_prefix": "4-",
            "antecedent_visible_text": AUTHORIZATION_QUESTION,
            "visible_assent_text": AUTHORIZATION_ANSWER,
            "normalized_combined_visible_text": AUTHORIZATION_COMBINED,
            "antecedent_utf8_bytes": len(AUTHORIZATION_QUESTION.encode("utf-8")),
            "visible_assent_utf8_bytes": len(AUTHORIZATION_ANSWER.encode("utf-8")),
            "normalized_combined_utf8_bytes": len(
                AUTHORIZATION_COMBINED.encode("utf-8")
            ),
            "antecedent_sha256": AUTHORIZATION_QUESTION_SHA256,
            "visible_assent_sha256": AUTHORIZATION_ANSWER_SHA256,
            "normalized_combined_sha256": AUTHORIZATION_COMBINED_SHA256,
            "domain_hex": VISIBLE_AUTHORIZATION_DOMAIN.hex(),
            "domain_plus_normalized_combined_sha256": AUTHORIZATION_DOMAIN_COMBINED_SHA256,
            "domain_plus_canonical_authorization_object_sha256": AUTHORIZATION_RECORD_BINDING_SHA256,
            "assent_normalization": "TRAILING_TRANSPORT_WHITESPACE_OR_ENTITY_REPRESENTATION_ONLY",
            "raw_transport_bytes_bound": False,
            "transport_framing_bound": False,
            "conversation_envelope_bound": False,
            "account_identity_bound": False,
            "timestamp_bound": False,
            "cryptographic_user_authentication": False,
            "honest_host_procedural_authorization": True,
            "authorized_scope": "ADDITIVE_V4_TERMINAL_PASS_CUSTODY_REGISTRATION_AND_AUDIT_ONLY",
            "user_selected_filenames_paths_schema_or_file_count": False,
            "package_paths_are_agent_selected_bounded_implementation_details": True,
            "rerun_runtime_approval_rank_training_production_science_or_claim_promotion_authorized": False,
        },
        "additive_package": {
            "file_count": 4,
            "paths_selected_by_agent": True,
            "paths_or_file_count_selected_by_user": False,
            "path_roster": list(_package_roster()),
            "machine_is_bound_by_domain_separated_record_self_digest": True,
            "machine_raw_digest_embedded_in_machine": False,
            "other_three_files_bound_by_raw_digest": True,
            "predecessor_or_operational_file_edited": False,
        },
        "scope": {
            "internal_evidence_only": True,
            "anonymous_or_public_release_permitted": False,
            "publication_safe_derivative_required": True,
            "raw_operational_custody_publication_permitted": False,
            "canonical_v4_v3_v2_or_scientific_file_mutated": False,
            "canonical_authority_or_child_invoked": False,
            "data_access_performed": False,
            "network_contact_performed": False,
            "entropy_contact_performed": False,
            "scientific_execution_performed": False,
            "synthetic_hostile_writes_are_temporary_noncanonical_and_nonoperational": True,
        },
        "v4_static_freeze": {
            "bindings": [_binding_dict(row) for row in V4_STATIC_BINDINGS],
            "machine_record_sha256": V4_MACHINE_RECORD_SHA256,
            "registration_static_plan_sha256": V4_STATIC_PLAN_SHA256,
            "all_six_reopened_exact": True,
        },
        "execution_authorization_certificate": {
            "path": AUTHORIZATION_PATH,
            "bytes": 3165,
            "raw_sha256": AUTHORIZATION_RAW_SHA256,
            "record_sha256": AUTHORIZATION_RECORD_SHA256,
            "authorized_attempt_count": 1,
            "authorized_child_launch_maximum": 1,
            "retry_count_authorized": 0,
            "honest_host_procedural_authority": True,
            "cryptographic_user_authentication": False,
            "runtime_approval_authorized": False,
            "scientific_execution_authorized": False,
        },
        "terminal_custody": {
            "attempt_id_sha256": ATTEMPT_ID_SHA256,
            "attempt_nonce_sha256": ATTEMPT_NONCE_SHA256,
            "attempt_nonce_is_deterministic_nonsecret_custody_identifier": True,
            "inventory": list(_inventory_rows(root)),
            "inventory_canonical_preimage_bytes": 3634,
            "inventory_sha256": INVENTORY_SHA256,
            "authoritative_record": {
                "event_ordinal": 3,
                "event_kind": "TERMINAL_OUTCOME",
                "raw_sha256": OPERATIONAL_FILE_EXPECTATIONS[7][3],
                "record_sha256": "3335688ef062c5f3d6815b35db025dc84c5abf0cf2f10866e52c2a91eb37058a",
            },
            "local_terminal_is_projection": True,
            "published_result_is_derivative": True,
            "projection_or_derivative_can_promote_or_replace_event3": False,
            "attempt_spent": True,
            "retry_permitted": False,
        },
        "pass_observation": {
            "outcome": "PASS",
            "supervisor_gate_count": 22,
            "supervisor_all_passed": True,
            "transport_gate_count": 9,
            "transport_all_passed": True,
            "child_gate_count": 16,
            "child_all_passed": True,
            "child_launch_claim_count": 1,
            "child_process_start_count": 1,
            "child_process_reap_observed": True,
            "child_exit_code_observed": True,
            "child_exit_code": 0,
            "child_stdin_captured_write_byte_count": 1332,
            "child_stdout_captured_byte_count": 1795,
            "child_stderr_captured_byte_count": 0,
            "timeout_observed": False,
            "stdout_overflow_observed": False,
            "stderr_overflow_observed": False,
            "postflight_custody_exact": True,
            "raw_child_transport_persisted": False,
            "validated_privacy_safe_child_observation_persisted_in_event3": True,
            "terminal_projection_or_result_embeds_full_child_observation": False,
            "application_effect_absence_basis": "STATIC_CHILD_SOURCE_AND_ROUTE_CONTRACT_NOT_OS_INSTRUMENTATION",
            "runtime_approval_created": False,
            "scientific_execution_performed": False,
        },
        "stdout_provenance": {
            "orchestrator_transcript_reports_single_stdout_canonical_result": True,
            "authority_invariant_requires_reopened_persisted_result_bytes": True,
            "independent_raw_stdout_receipt_bound": False,
            "independent_stdout_digest_claimed": False,
            "transcript_comparison_promoted_to_separate_custody_evidence": False,
        },
        "predecessor_v3_terminal_registration": {
            "bindings": [_binding_dict(row) for row in V3_TERMINAL_BINDINGS],
            "machine_record_sha256": V3_TERMINAL_RECORD_SHA256,
            "canonical_attempt_count": 1,
            "retry_count": 0,
            "exact_failure_stage": None,
            "child_launch_count": None,
            "five_postfailure_probe_count": 5,
            "probe_context_canonical_failure_evidence": False,
            "probe_context_independently_verified_from_raw_receipts": False,
            "probe_raw_commands_or_outputs_bound": False,
            "v4_is_v3_retry_repair_or_favorable_reclassification": False,
        },
        "predecessor_v2_terminal_registration": {
            "bindings": [_binding_dict(row) for row in V2_TERMINAL_BINDINGS],
            "machine_record_sha256": V2_TERMINAL_RECORD_SHA256,
            "terminal_state": V2_TERMINAL_STATE,
            "attempt_marker_bytes": 2171,
            "attempt_marker_raw_sha256": "e74195f33df40f255fbe4f956dd426a6a76676c93358f70e785f2f90c7db7cc4",
            "validated_event_count": 3,
            "validated_head_sha256": "4ba4799fdfa3bf407ea269c035c6502114b9bae5b93bdde1b32c6ebe497646a5",
            "preparation_file_count": 65,
            "preparation_directory_count": 20,
            "capsule_file_count": 53,
            "capsule_directory_count": 14,
            "capsule_inventory_sha256": "c68e21aa648c4823bd87987399eb0ce76149adaa57c7b19b162783ad5dc01360",
            "symlink_count": 0,
            "files_nlink_one": True,
            "retry_permitted": False,
            "execution_authorized": False,
        },
        "scientific_state": {
            "preregistration_path": PREREGISTRATION_PATH,
            "preregistration_raw_sha256": PREREGISTRATION_RAW_SHA256,
            "preexecution_closure_path": PREEXECUTION_CLOSURE_PATH,
            "preexecution_closure_raw_sha256": PREEXECUTION_CLOSURE_RAW_SHA256,
            "preexecution_closure_record_sha256": PREEXECUTION_CLOSURE_RECORD_SHA256,
            "historical_literal_null_count": 174,
            "projected_resolved_pre_d1_count": 2,
            "effective_unresolved_null_count": 172,
            "effective_preexecution_unresolved_null_count": 166,
            "deferred_postexecution_unresolved_null_count": 6,
            "open_blocker_count": 12,
            "confirmatory_execution_blocker_count": 10,
            "promotion_submission_blocker_count": 2,
            "blockers_closed": 0,
            "d1_quarantine_row_count": 550,
            "d1_quarantine_roster_sha256": D1_QUARANTINE_ROSTER_SHA256,
            "d1_admissible_as_production_evidence": False,
            "test_data_unopened_before_freeze": None,
            "confirmatory_execution_authorized": False,
            "scientific_result_eligible": False,
        },
        "nonclaims": {
            "registration_authorizes_v4_rerun": False,
            "registration_authorizes_runtime_approval": False,
            "registration_authorizes_rank_training_or_production": False,
            "registration_authorizes_scientific_execution": False,
            "registration_promotes_manuscript_claim_or_submission": False,
            "registration_closes_any_of_172_unresolved_fields": False,
            "registration_closes_any_of_12_blockers": False,
            "registration_resolves_test_data_unopened_predicate": False,
            "registration_admits_v3_probe_context_as_canonical_evidence": False,
            "terminal_projection_is_coequal_authority": False,
            "published_result_is_coequal_authority": False,
            "self_digests_are_cryptographic_user_authentication": False,
            "malicious_host_resistance_claimed": False,
        },
    }


def _binding_row(root: Path, ordinal: int, role: str, relative: str) -> Dict[str, Any]:
    payload, info = _read_stable_file(root, relative)
    return {
        "ordinal": ordinal,
        "role": role,
        "path": relative,
        "bytes": len(payload),
        "raw_sha256": _sha256(payload),
        "lf_only": b"\r" not in payload,
        "mode_octal": "0644",
        "nlink": info.st_nlink,
        "is_regular_file": stat.S_ISREG(info.st_mode),
        "is_symlink": stat.S_ISLNK(info.st_mode),
    }


def _build_registration_payload(root: Path = WORKSPACE_ROOT) -> bytes:
    root = _canonical_root(root)
    record = _expected_fixed_registration(root)
    record["registration_bindings"] = [
        _binding_row(root, ordinal, role, path)
        for ordinal, (role, path) in enumerate(
            (
                ("HUMAN_REGISTRATION", HUMAN_PATH),
                ("READ_ONLY_VALIDATOR", VALIDATOR_PATH),
                ("HOSTILE_TEST", TEST_PATH),
            )
        )
    ]
    record["record_sha256"] = None
    record["record_sha256"] = _sha256(REGISTRATION_DOMAIN + _canonical(record))
    return _file_bytes(record)


def _validate_machine_payload(root: Path, payload: bytes) -> Dict[str, Any]:
    record = _parse_json(payload, "terminal-PASS machine registration")
    fixed = _expected_fixed_registration(root)
    if set(record) != set(fixed) | {"registration_bindings", "record_sha256"}:
        raise TerminalPassRegistrationError("machine field roster changed")
    for key, expected in fixed.items():
        _exact(record.get(key), expected, "machine." + key)
    bindings = record.get("registration_bindings")
    paths = (HUMAN_PATH, VALIDATOR_PATH, TEST_PATH)
    roles = ("HUMAN_REGISTRATION", "READ_ONLY_VALIDATOR", "HOSTILE_TEST")
    if type(bindings) is not list or len(bindings) != 3:
        raise TerminalPassRegistrationError("registration binding roster changed")
    for ordinal, (claimed, role, path) in enumerate(zip(bindings, roles, paths)):
        _exact(claimed, _binding_row(root, ordinal, role, path), "registration binding")
    claimed = _require_sha256(record.get("record_sha256"), "registration self digest")
    body = dict(record)
    body["record_sha256"] = None
    if claimed != _sha256(REGISTRATION_DOMAIN + _canonical(body)):
        raise TerminalPassRegistrationError("registration self digest changed")
    return record


def _load_machine(root: Path) -> Tuple[bytes, Dict[str, Any]]:
    payload, _ = _read_stable_file(root, MACHINE_PATH)
    record = _validate_machine_payload(root, payload)
    repeated, _ = _read_stable_file(root, MACHINE_PATH)
    if repeated != payload:
        raise TerminalPassRegistrationError("machine changed during load")
    return payload, record


class TerminalPassQualification:
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
) -> TerminalPassQualification:
    root = _canonical_root(workspace_root)
    custody = audit_terminal_custody(root)
    _, registration = _load_machine(root)
    repeated_custody = audit_terminal_custody(root)
    _, repeated_registration = _load_machine(root)
    if _canonical(custody) != _canonical(repeated_custody) or _canonical(
        registration
    ) != _canonical(repeated_registration):
        raise TerminalPassRegistrationError(
            "registration custody changed during qualification"
        )
    value = object.__new__(TerminalPassQualification)
    object.__setattr__(value, "_registration", _canonical(registration))
    object.__setattr__(value, "_custody", _canonical(custody))
    object.__setattr__(value, "_record_sha256", registration["record_sha256"])
    return value


def status(workspace_root: Any = WORKSPACE_ROOT) -> Dict[str, Any]:
    qualification = load_qualification(workspace_root)
    custody = qualification.custody()
    scientific = custody["scientific_state"]
    return {
        "schema": STATUS_SCHEMA,
        "global_state": GLOBAL_STATE,
        "terminal_state": TERMINAL_STATE,
        "outcome": "PASS",
        "authoritative_event_ordinal": 3,
        "authoritative_event_sha256": custody["v4"]["event3_sha256"],
        "attempt_id_sha256": custody["v4"]["attempt_id_sha256"],
        "attempt_nonce_sha256": custody["v4"]["attempt_nonce_sha256"],
        "attempt_spent": True,
        "retry_permitted": False,
        "child_launch_claim_count": 1,
        "child_process_start_count": 1,
        "runtime_approval_created": False,
        "scientific_execution_performed": False,
        "effective_unresolved_null_count": scientific[
            "effective_unresolved_null_count"
        ],
        "open_blocker_count": scientific["open_blocker_count"],
        "test_data_unopened_before_freeze": scientific[
            "test_data_unopened_before_freeze"
        ],
        "registration_record_sha256": qualification.record_sha256,
        "execution_authorized": False,
        "claim_promotion_permitted": False,
    }


__all__ = [
    "GLOBAL_STATE",
    "HUMAN_PATH",
    "INVENTORY_DOMAIN",
    "INVENTORY_SHA256",
    "MACHINE_PATH",
    "QUALIFICATION_SCHEMA",
    "REGISTRATION_DOMAIN",
    "SCHEMA",
    "STATUS_SCHEMA",
    "TERMINAL_STATE",
    "TEST_PATH",
    "TerminalPassQualification",
    "TerminalPassRegistrationError",
    "VALIDATOR_PATH",
    "V2_TERMINAL_BINDINGS",
    "V3_TERMINAL_BINDINGS",
    "V4_STATIC_BINDINGS",
    "audit_terminal_custody",
    "load_qualification",
    "status",
]
