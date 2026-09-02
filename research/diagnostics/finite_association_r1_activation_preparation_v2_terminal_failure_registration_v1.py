"""Read-only audit for the spent A1 R1 activation-preparation v2 attempt.

This module has no writer, entropy, subprocess, network, import-time execution,
or scientific execution route.  It independently reopens the immutable v2
freeze and the exact terminal custody prefix, then loads the additive forensic
registration.  It never imports the v2 authority module.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Mapping, Sequence, Tuple


MODULE_PATH = Path(__file__).resolve()
WORKSPACE_ROOT = MODULE_PATH.parents[2]

SCHEMA = (
    "heterodiff-manuscript-v3-a1-r1-activation-preparation-v2-"
    "terminal-failure-registration-v1"
)
QUALIFICATION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v2-terminal-failure-" "qualification-v1"
)
REGISTRATION_DOMAIN = (SCHEMA + "\0").encode("ascii")
ASSENT_DOMAIN = b"heterodiff-a1-r1-activation-preparation-v2-user-assent-v1\0"
CAPSULE_INVENTORY_DOMAIN = b"heterodiff-a1-r1-source-capsule-live-inventory-v2\0"
OPERATION_NONCE_DOMAIN = b"heterodiff-a1-r1-preparation-operation-nonce-v2\0"

HUMAN_PATH = (
    "manuscript_v3/"
    "a1_r1_activation_preparation_v2_terminal_failure_registration_v1.md"
)
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_a1_r1_activation_preparation_v2_"
    "terminal_failure_registration_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/"
    "finite_association_r1_activation_preparation_v2_"
    "terminal_failure_registration_v1.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_a1_r1_activation_preparation_v2_"
    "terminal_failure_registration_v1.py"
)

V2_HUMAN_PATH = "manuscript_v3/a1_r1_activation_preparation_implementation_freeze_v2.md"
V2_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_a1_r1_activation_preparation_implementation_freeze_v2.json"
)
V2_CONTRACTS_PATH = (
    "research/production/"
    "finite_association_r1_activation_preparation_contracts_v2.py"
)
V2_AUTHORITY_PATH = (
    "research/production/"
    "finite_association_r1_activation_preparation_authority_v2.py"
)
V2_RUNTIME_PATH = (
    "research/production/" "finite_association_r1_activation_preparation_runtime_v2.py"
)
V2_TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_a1_r1_activation_preparation_implementation_freeze_v2.py"
)

MARKER_PATH = "artifacts/a1_r1_activation_preparation_v2.attempt.json"
PREPARATION_ROOT = "artifacts/a1_r1_activation_preparation_v2"
CAPSULE_ROOT = PREPARATION_ROOT + "/capsule"
RUNTIME_CANDIDATE_ROOT = PREPARATION_ROOT + "/runtime-candidate"

TERMINAL_STATE = (
    "A1_R1_ACTIVATION_PREPARATION_V2_ATTEMPT_SPENT_TERMINAL_"
    "RUNTIME_CAPTURE_A_CHILD_FAILED_NO_BINDING_NO_RETRY"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"

FROZEN_V2_BINDINGS = (
    {
        "ordinal": 0,
        "role": "V2_HUMAN_FREEZE",
        "path": V2_HUMAN_PATH,
        "bytes": 10686,
        "mode_octal": "0644",
        "nlink": 1,
        "raw_sha256": (
            "b6893f6870e913633d186812690d4fc1b836dfe740f28588f3266cca4b5f8d28"
        ),
    },
    {
        "ordinal": 1,
        "role": "V2_MACHINE_FREEZE",
        "path": V2_MACHINE_PATH,
        "bytes": 46331,
        "mode_octal": "0644",
        "nlink": 1,
        "raw_sha256": (
            "b80fd02cb15dc7b5b051678af940c05dbc043992bbe1daee35ddc00dfe51f305"
        ),
    },
    {
        "ordinal": 2,
        "role": "V2_CONTRACTS_MODULE",
        "path": V2_CONTRACTS_PATH,
        "bytes": 19039,
        "mode_octal": "0644",
        "nlink": 1,
        "raw_sha256": (
            "ee18bf3a1b6daf09717bae3960c1c1649b64da03985ee5ea4cc5d44c1267414d"
        ),
    },
    {
        "ordinal": 3,
        "role": "V2_AUTHORITY_MODULE",
        "path": V2_AUTHORITY_PATH,
        "bytes": 143460,
        "mode_octal": "0644",
        "nlink": 1,
        "raw_sha256": (
            "2bd8f1dd450f2ddf9fd16b1c20dc865ff2bb219ca7f675262508356cbd7fa28e"
        ),
    },
    {
        "ordinal": 4,
        "role": "V2_RUNTIME_ORACLE",
        "path": V2_RUNTIME_PATH,
        "bytes": 45459,
        "mode_octal": "0644",
        "nlink": 1,
        "raw_sha256": (
            "59c3f08bd88b376d4a1bbadcd095c024e94c69ab0fe75029a069255998d11097"
        ),
    },
    {
        "ordinal": 5,
        "role": "V2_HOSTILE_TEST",
        "path": V2_TEST_PATH,
        "bytes": 47279,
        "mode_octal": "0644",
        "nlink": 1,
        "raw_sha256": (
            "176ef2e220bf37f3cd493ef91f436266030c6d28b5d72c09bc7d116ac4da11c8"
        ),
    },
)
V2_MACHINE_RECORD_SHA256 = (
    "7ef6ec8e5c61f254277730a9879e89e6ef8be43d917eb9adc0bcc747b1e74f0e"
)
V2_STATIC_SNAPSHOT_SHA256 = (
    "d2931175f4ccd7ed7dbaf6d656ab0fa6e39b37809500ed7ab9f39a0977237964"
)

OPERATOR_AUTHORIZATION_CONTEXT = (
    "I authorize the irreversible A1 R1 activation-preparation v2 sequence: its "
    "one-shot marker, deterministic source-capsule materialization, and exactly "
    "two privacy-safe runtime inspections; this does not authorize runtime "
    "approval, rank, training, production, scientific execution, claim promotion, "
    "or activation."
)
OPERATOR_AUTHORIZATION_SHA256 = (
    "d1a7808a81a67b5969f949c59c337d40f48b2b5a47e92d445c40a7f2f4718cda"
)
USER_ASSENT_TEXT = "Yes, authorize the V2 preparation attempt."
USER_ASSENT_NORMALIZATION = "NFC_UTF8_WITH_TRAILING_ASCII_SPACE_TAB_CR_LF_REMOVED"

EXPECTED_EFFECTIVE_ENVIRONMENT = {
    "LANG": "C",
    "LC_ALL": "C",
    "PYTHONHASHSEED": "0",
    "__CF_USER_TEXT_ENCODING": "0x1F5:0x0:0x0",
}
FROZEN_REQUESTED_ENVIRONMENT = {
    "LANG": "C",
    "LC_ALL": "C",
    "PYTHONHASHSEED": "0",
}

RECORD_ROWS = (
    {
        "ordinal": 0,
        "role": "ATTEMPT_MARKER",
        "path": MARKER_PATH,
        "schema": "heterodiff-a1-r1-activation-preparation-attempt-marker-v2",
        "terminal_digest_key": "marker_sha256",
        "bytes": 2171,
        "raw_sha256": (
            "e74195f33df40f255fbe4f956dd426a6a76676c93358f70e785f2f90c7db7cc4"
        ),
        "record_sha256": (
            "e9cc86c08ab20b44fee62c0bd8476d08130b059c826eb820c4924be3d2e16f45"
        ),
    },
    {
        "ordinal": 1,
        "role": "LEDGER_GENESIS",
        "path": PREPARATION_ROOT + "/ledger/genesis.json",
        "schema": "heterodiff-a1-r1-preparation-ledger-genesis-v2",
        "terminal_digest_key": "genesis_sha256",
        "bytes": 1616,
        "raw_sha256": (
            "1ea198cbedfcebb557f7ad872d4e1a49003d39aa007c8a4bdb1b752df0c53779"
        ),
        "record_sha256": (
            "6b7267d63ad7842a89dca1b5d99340933a7df3300fd727076bc142c6767afc69"
        ),
    },
    {
        "ordinal": 2,
        "role": "EVENT_0_NONCE_CLAIM",
        "path": PREPARATION_ROOT
        + "/ledger/nonce-claims/event-00000000000000000000.json",
        "schema": "heterodiff-a1-r1-preparation-operation-nonce-claim-v2",
        "terminal_digest_key": "claim_sha256",
        "bytes": 811,
        "raw_sha256": (
            "64fca0f0cb7b22d674ac581d47decb58c37d78a8e5c7a9106b495c923d23862d"
        ),
        "record_sha256": (
            "5cff31b87b27dbb83f8aa474fc36d613b3a57e22b36d07919e6caddc56a518ff"
        ),
    },
    {
        "ordinal": 3,
        "role": "EVENT_0",
        "path": PREPARATION_ROOT + "/ledger/events/00000000000000000000.json",
        "schema": "heterodiff-a1-r1-preparation-ledger-event-v2",
        "terminal_digest_key": "event_sha256",
        "bytes": 1299,
        "raw_sha256": (
            "3910afb3a96e1da2510bf32a45fd5929a3307fff145e0ffbb847718afcca6301"
        ),
        "record_sha256": (
            "9409499d860d4b6b2d909b3480be19053ed5af97f4bcbf9bf6f8f9815bcfb2bd"
        ),
    },
    {
        "ordinal": 4,
        "role": "SOURCE_CAPSULE_MANIFEST",
        "path": PREPARATION_ROOT + "/ledger/receipts/source-capsule-manifest.json",
        "schema": "heterodiff-a1-r1-source-capsule-manifest-v2",
        "terminal_digest_key": "manifest_sha256",
        "bytes": 22366,
        "raw_sha256": (
            "29bd8aba8cfaf85ed5c542293f703f4e0ac08ff51596c5edca208e02e934084f"
        ),
        "record_sha256": (
            "77576eaf4c6c741c7ac2c9de467c2a6b33ca52c7b021144f41e146622d856702"
        ),
    },
    {
        "ordinal": 5,
        "role": "EVENT_1_NONCE_CLAIM",
        "path": PREPARATION_ROOT
        + "/ledger/nonce-claims/event-00000000000000000001.json",
        "schema": "heterodiff-a1-r1-preparation-operation-nonce-claim-v2",
        "terminal_digest_key": "claim_sha256",
        "bytes": 797,
        "raw_sha256": (
            "7b0e164c1963c816a850673c78b33b93596fc395edd0a5d4939bbe3b3cc11f7d"
        ),
        "record_sha256": (
            "768c1f8661e1c889e6e55704d0056fb14f07b16ef6f756471f58af51f3f6a230"
        ),
    },
    {
        "ordinal": 6,
        "role": "EVENT_1",
        "path": PREPARATION_ROOT + "/ledger/events/00000000000000000001.json",
        "schema": "heterodiff-a1-r1-preparation-ledger-event-v2",
        "terminal_digest_key": "event_sha256",
        "bytes": 1314,
        "raw_sha256": (
            "f31b4805efcd74af94d87e38a9217ce1d6c8301bba808e5a5604c27127bbfb4c"
        ),
        "record_sha256": (
            "2cd92a085303f6f41d53aa849f9a9c38299a049d6910eabbbbeaa47bd2d1d60f"
        ),
    },
    {
        "ordinal": 7,
        "role": "SOURCE_CAPSULE_ADMISSION",
        "path": PREPARATION_ROOT + "/ledger/receipts/source-capsule-admission.json",
        "schema": "heterodiff-a1-r1-source-capsule-admission-v2",
        "terminal_digest_key": "admission_sha256",
        "bytes": 974,
        "raw_sha256": (
            "e7d88bd02ffa2f29b4f70368f0de27c3cf8ede73512b8cfd36dc76d30eec06cf"
        ),
        "record_sha256": (
            "3f4c41adeb59b74461218fc23155584618d4c24c8db10a9a87d8d334bf6e5834"
        ),
    },
    {
        "ordinal": 8,
        "role": "EVENT_2_NONCE_CLAIM",
        "path": PREPARATION_ROOT
        + "/ledger/nonce-claims/event-00000000000000000002.json",
        "schema": "heterodiff-a1-r1-preparation-operation-nonce-claim-v2",
        "terminal_digest_key": "claim_sha256",
        "bytes": 810,
        "raw_sha256": (
            "a611905e2fd6e591790607bcb0e52bc5d61c6e1c7b7f6feaa0a1cedec80c9d51"
        ),
        "record_sha256": (
            "6d106204929efef19a9ee1e76d2c76feb9acbb6a672055cfaad204f91789ed50"
        ),
    },
    {
        "ordinal": 9,
        "role": "EVENT_2",
        "path": PREPARATION_ROOT + "/ledger/events/00000000000000000002.json",
        "schema": "heterodiff-a1-r1-preparation-ledger-event-v2",
        "terminal_digest_key": "event_sha256",
        "bytes": 1312,
        "raw_sha256": (
            "2e138e029fb19e06db466adb32c8d31deca2783b8a576c848ed42f62019d0e0f"
        ),
        "record_sha256": (
            "4ba4799fdfa3bf407ea269c035c6502114b9bae5b93bdde1b32c6ebe497646a5"
        ),
    },
    {
        "ordinal": 10,
        "role": "RUNTIME_DOUBLE_CAPTURE_REQUEST",
        "path": PREPARATION_ROOT
        + "/ledger/receipts/runtime-double-capture-request.json",
        "schema": "heterodiff-a1-r1-runtime-double-capture-request-v2",
        "terminal_digest_key": "request_sha256",
        "bytes": 1539,
        "raw_sha256": (
            "a4b5850d1bded22be30e7d93eed3396a8b2478fd6ae6dd7fc3e1538349016d4b"
        ),
        "record_sha256": (
            "a6453702e03a9f01c6b3544a387491bd41f904af3eb2161821d36753de608b87"
        ),
    },
    {
        "ordinal": 11,
        "role": "RUNTIME_CAPTURE_A_LAUNCH_CLAIM",
        "path": PREPARATION_ROOT + "/ledger/nonce-claims/runtime-capture-a.json",
        "schema": "heterodiff-a1-r1-preparation-operation-nonce-claim-v2",
        "terminal_digest_key": "claim_sha256",
        "bytes": 801,
        "raw_sha256": (
            "d9f7a0d343604ab5171bbc592b21f0eb4b0a97ea5b3fa2103c6b854493ba16af"
        ),
        "record_sha256": (
            "6140a49e94c472fcd75d6ccfb55d4de0030190b39d57b2e59ebcd9c49fc7eda4"
        ),
    },
)

ABSENT_V2_ROWS = (
    {
        "role": "RUNTIME_CAPTURE_A_BINDING",
        "path": PREPARATION_ROOT + "/ledger/receipts/runtime-capture-a.binding.json",
    },
    {
        "role": "RUNTIME_CAPTURE_B_LAUNCH_CLAIM",
        "path": PREPARATION_ROOT + "/ledger/nonce-claims/runtime-capture-b.json",
    },
    {
        "role": "RUNTIME_CAPTURE_B_BINDING",
        "path": PREPARATION_ROOT + "/ledger/receipts/runtime-capture-b.binding.json",
    },
    {
        "role": "RUNTIME_CANDIDATE",
        "path": PREPARATION_ROOT + "/runtime-candidate/candidate.json",
    },
    {
        "role": "EVENT_3_NONCE_CLAIM",
        "path": PREPARATION_ROOT
        + "/ledger/nonce-claims/event-00000000000000000003.json",
    },
    {
        "role": "EVENT_3",
        "path": PREPARATION_ROOT + "/ledger/events/00000000000000000003.json",
    },
    {
        "role": "EVENT_4_NONCE_CLAIM",
        "path": PREPARATION_ROOT
        + "/ledger/nonce-claims/event-00000000000000000004.json",
    },
    {
        "role": "EVENT_4",
        "path": PREPARATION_ROOT + "/ledger/events/00000000000000000004.json",
    },
)

EXPECTED_PUBLIC_STATUS = {
    "live_state": "PREPARATION_ATTEMPT_SPENT_TERMINAL_CUSTODY_INVALID",
    "marker_present": True,
    "marker_attempt_spent": True,
    "marker_sha256": (
        "e9cc86c08ab20b44fee62c0bd8476d08130b059c826eb820c4924be3d2e16f45"
    ),
    "terminal_reason_class": "PreparationAuthorityError",
    "preparation_event_count": 0,
    "closed": True,
    "retry_permitted": False,
    "execution_authorized": False,
}

FROZEN_TEST_FAILURES = (
    {
        "test_name": (
            "test_owned_paths_are_exactly_additive_and_" "no_operational_output_exists"
        ),
        "definition_line": 314,
        "first_failing_assertion_line": 316,
        "frozen_assertion": "canonical v2 marker path has no directory entry",
        "current_observation": "canonical v2 marker path is a spent regular record",
        "outcome": "FAIL",
    },
    {
        "test_name": (
            "test_status_is_zero_write_transition_aware_and_"
            "initially_awaiting_authorization"
        ),
        "definition_line": 401,
        "first_failing_assertion_line": 415,
        "frozen_assertion": (
            "live transition equals the initial awaiting-authorization object"
        ),
        "current_observation": (
            "live transition is terminal custody invalid with marker spent"
        ),
        "outcome": "FAIL",
    },
)


class TerminalFailureRegistrationError(RuntimeError):
    """Raised when immutable postmortem custody does not reopen exactly."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require_sha256(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TerminalFailureRegistrationError(label + " is not a SHA-256 digest")
    return value


def _normalized_assent(text: str) -> str:
    if type(text) is not str:
        raise TerminalFailureRegistrationError("user assent is not exact text")
    trailing_ui_whitespace = " " + "".join(chr(value) for value in (9, 13, 10))
    return unicodedata.normalize("NFC", text.rstrip(trailing_ui_whitespace))


def user_assent_sha256() -> str:
    normalized = _normalized_assent(USER_ASSENT_TEXT)
    return _sha256(ASSENT_DOMAIN + normalized.encode("utf-8"))


def _path_has_entry(path: Path) -> bool:
    try:
        path.lstat()
        return True
    except FileNotFoundError:
        return False


def _structural_identity(information: os.stat_result) -> Tuple[int, ...]:
    return (
        information.st_dev,
        information.st_ino,
        information.st_mode,
        information.st_nlink,
        information.st_uid,
        information.st_gid,
    )


def _ancestor_identity(information: os.stat_result) -> Tuple[int, ...]:
    return (
        information.st_dev,
        information.st_ino,
        information.st_mode,
        information.st_uid,
        information.st_gid,
    )


def _full_identity(information: os.stat_result) -> Tuple[int, ...]:
    return _structural_identity(information) + (
        information.st_size,
        information.st_mtime_ns,
        information.st_ctime_ns,
    )


def _ancestor_identities(
    path: Path, root: Path
) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise TerminalFailureRegistrationError("path escaped workspace") from error
    rows = []
    current = root
    root_information = current.lstat()
    if stat.S_ISLNK(root_information.st_mode) or not stat.S_ISDIR(
        root_information.st_mode
    ):
        raise TerminalFailureRegistrationError("workspace root is not a directory")
    rows.append(("", _ancestor_identity(root_information)))
    for part in relative.parts[:-1]:
        current = current / part
        information = current.lstat()
        if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(information.st_mode):
            raise TerminalFailureRegistrationError(
                "custody ancestor is not a directory"
            )
        rows.append(
            (current.relative_to(root).as_posix(), _ancestor_identity(information))
        )
    return tuple(rows)


def _read_stable_file(
    root: Path,
    relative_path: str,
    *,
    expected_mode: int | None = None,
    expected_nlink: int | None = None,
) -> Tuple[bytes, os.stat_result]:
    path = root / relative_path
    before_ancestors = _ancestor_identities(path, root)
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise TerminalFailureRegistrationError(relative_path + " is not a regular file")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        opened_before = os.fstat(descriptor)
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                break
            chunks.append(chunk)
        opened_after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    after_ancestors = _ancestor_identities(path, root)
    identities = (
        _full_identity(before),
        _full_identity(opened_before),
        _full_identity(opened_after),
        _full_identity(after),
    )
    if len(set(identities)) != 1 or before_ancestors != after_ancestors:
        raise TerminalFailureRegistrationError(relative_path + " changed during read")
    if expected_mode is not None and stat.S_IMODE(after.st_mode) != expected_mode:
        raise TerminalFailureRegistrationError(relative_path + " mode changed")
    if expected_nlink is not None and after.st_nlink != expected_nlink:
        raise TerminalFailureRegistrationError(relative_path + " link count changed")
    return b"".join(chunks), after


def _parse_canonical_record(payload: bytes, row: Mapping[str, Any]) -> Dict[str, Any]:
    if len(payload) != row["bytes"] or _sha256(payload) != row["raw_sha256"]:
        raise TerminalFailureRegistrationError(row["role"] + " raw custody changed")
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TerminalFailureRegistrationError(row["role"] + " is not JSON") from error
    if type(record) is not dict or payload != _canonical(record) + b"\n":
        raise TerminalFailureRegistrationError(row["role"] + " is not canonical")
    if record.get("schema") != row["schema"]:
        raise TerminalFailureRegistrationError(row["role"] + " schema changed")
    key = row["terminal_digest_key"]
    claimed = _require_sha256(record.get(key), row["role"] + " self digest")
    body = dict(record)
    body[key] = None
    expected = _sha256(row["schema"].encode("ascii") + b"\0" + _canonical(body))
    if claimed != expected or claimed != row["record_sha256"]:
        raise TerminalFailureRegistrationError(row["role"] + " self digest changed")
    return record


def _load_exact_record(
    root: Path, row: Mapping[str, Any]
) -> Tuple[bytes, Dict[str, Any]]:
    payload, _ = _read_stable_file(
        root, row["path"], expected_mode=0o600, expected_nlink=1
    )
    if len(payload) != row["bytes"] or _sha256(payload) != row["raw_sha256"]:
        raise TerminalFailureRegistrationError(row["role"] + " raw custody changed")
    return payload, _parse_canonical_record(payload, row)


def _tree_snapshot(root: Path) -> Dict[str, Any]:
    information = root.lstat()
    if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(information.st_mode):
        raise TerminalFailureRegistrationError("preparation root type changed")
    directories = [("", _full_identity(information))]
    files = []
    for current_text, directory_names, file_names in os.walk(root, followlinks=False):
        current = Path(current_text)
        directory_names.sort()
        file_names.sort()
        if current != root:
            current_information = current.lstat()
            if stat.S_ISLNK(current_information.st_mode) or not stat.S_ISDIR(
                current_information.st_mode
            ):
                raise TerminalFailureRegistrationError("tree directory type changed")
            directories.append(
                (
                    current.relative_to(root).as_posix(),
                    _full_identity(current_information),
                )
            )
        for name in directory_names:
            child_information = (current / name).lstat()
            if stat.S_ISLNK(child_information.st_mode) or not stat.S_ISDIR(
                child_information.st_mode
            ):
                raise TerminalFailureRegistrationError("tree directory link detected")
        for name in file_names:
            child = current / name
            child_information = child.lstat()
            if stat.S_ISLNK(child_information.st_mode) or not stat.S_ISREG(
                child_information.st_mode
            ):
                raise TerminalFailureRegistrationError("tree file link detected")
            files.append(
                (child.relative_to(root).as_posix(), _full_identity(child_information))
            )
    return {"directories": sorted(directories), "files": sorted(files)}


def _safe_capsule_path(value: Any) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise TerminalFailureRegistrationError("capsule path is not exact")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise TerminalFailureRegistrationError("capsule path is unsafe")
    if path.as_posix() != value:
        raise TerminalFailureRegistrationError("capsule path is not normalized")
    return value


def _capsule_directories(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    directories = {""}
    for row in rows:
        current = PurePosixPath(_safe_capsule_path(row["capsule_relative_path"])).parent
        while current.as_posix() != ".":
            directories.add(current.as_posix())
            current = current.parent
    return sorted(directories)


def _audit_capsule(
    root: Path, manifest: Mapping[str, Any], admission: Mapping[str, Any]
) -> Dict[str, Any]:
    rows = manifest.get("rows")
    if type(rows) is not list or len(rows) != 53:
        raise TerminalFailureRegistrationError("capsule manifest row count changed")
    expected_row_keys = {
        "ordinal",
        "capsule_relative_path",
        "source_path",
        "source_role",
        "payload_kind",
        "bytes",
        "raw_sha256",
        "overlay_rule",
        "overlay_rule_sha256",
    }
    paths = []
    for ordinal, row in enumerate(rows):
        if type(row) is not dict or set(row) != expected_row_keys:
            raise TerminalFailureRegistrationError("capsule manifest row changed")
        if type(row["ordinal"]) is not int or row["ordinal"] != ordinal:
            raise TerminalFailureRegistrationError("capsule ordinal changed")
        if type(row["bytes"]) is not int or row["bytes"] < 0:
            raise TerminalFailureRegistrationError("capsule byte count changed")
        _require_sha256(row["raw_sha256"], "capsule row digest")
        paths.append(_safe_capsule_path(row["capsule_relative_path"]))
    if len(set(paths)) != 53:
        raise TerminalFailureRegistrationError("capsule paths are not unique")
    directories = _capsule_directories(rows)
    if manifest.get("directory_count") != len(directories) or len(directories) != 14:
        raise TerminalFailureRegistrationError("capsule directory count changed")

    capsule = root / CAPSULE_ROOT
    before = _tree_snapshot(capsule)
    if [row[0] for row in before["files"]] != sorted(paths):
        raise TerminalFailureRegistrationError("capsule file closure changed")
    if [row[0] for row in before["directories"]] != directories:
        raise TerminalFailureRegistrationError("capsule directory closure changed")

    def read_rows() -> list[Dict[str, Any]]:
        observed = []
        for row in rows:
            relative = CAPSULE_ROOT + "/" + row["capsule_relative_path"]
            payload, _ = _read_stable_file(
                root, relative, expected_mode=0o600, expected_nlink=1
            )
            if len(payload) != row["bytes"] or _sha256(payload) != row["raw_sha256"]:
                raise TerminalFailureRegistrationError("capsule row custody changed")
            observed.append(
                {
                    "ordinal": row["ordinal"],
                    "path": row["capsule_relative_path"],
                    "bytes": len(payload),
                    "raw_sha256": _sha256(payload),
                    "mode_octal": "0600",
                }
            )
        return observed

    first = read_rows()
    second = read_rows()
    for relative, _ in before["directories"]:
        directory = capsule if not relative else capsule / relative
        information = directory.lstat()
        if stat.S_IMODE(information.st_mode) != 0o700:
            raise TerminalFailureRegistrationError("capsule directory mode changed")
    after = _tree_snapshot(capsule)
    if before != after or first != second:
        raise TerminalFailureRegistrationError("capsule changed during audit")
    body = {
        "manifest_sha256": manifest["manifest_sha256"],
        "rows": first,
        "directories": directories,
    }
    inventory = _sha256(CAPSULE_INVENTORY_DOMAIN + _canonical(body))
    if (
        admission.get("inventory_sha256") != inventory
        or admission.get("file_count") != 53
        or admission.get("directory_count") != 14
        or admission.get("execution_admissible") is not False
        or manifest.get("source_capsule_execution_admissible") is not False
    ):
        raise TerminalFailureRegistrationError("capsule admission changed")
    return {
        "file_count": 53,
        "directory_count": 14,
        "inventory_sha256": inventory,
        "all_rows_reopened_twice": True,
        "closed_world_verified": True,
    }


def _expected_preparation_tree(
    manifest: Mapping[str, Any]
) -> Tuple[list[str], list[str]]:
    capsule_files = [
        "capsule/" + row["capsule_relative_path"] for row in manifest["rows"]
    ]
    ledger_files = [
        "ledger/writer.lock",
        "ledger/genesis.json",
        "ledger/events/00000000000000000000.json",
        "ledger/events/00000000000000000001.json",
        "ledger/events/00000000000000000002.json",
        "ledger/nonce-claims/event-00000000000000000000.json",
        "ledger/nonce-claims/event-00000000000000000001.json",
        "ledger/nonce-claims/event-00000000000000000002.json",
        "ledger/nonce-claims/runtime-capture-a.json",
        "ledger/receipts/source-capsule-manifest.json",
        "ledger/receipts/source-capsule-admission.json",
        "ledger/receipts/runtime-double-capture-request.json",
    ]
    directories = {
        "",
        "ledger",
        "ledger/events",
        "ledger/nonce-claims",
        "ledger/receipts",
        "runtime-candidate",
    }
    directories.update(
        "capsule" if not item else "capsule/" + item
        for item in _capsule_directories(manifest["rows"])
    )
    return sorted(capsule_files + ledger_files), sorted(directories)


def _validate_record_links(records: Mapping[str, Mapping[str, Any]]) -> None:
    marker = records["ATTEMPT_MARKER"]
    genesis = records["LEDGER_GENESIS"]
    if (
        marker["marker_sha256"] != RECORD_ROWS[0]["record_sha256"]
        or marker["preparation_instance_nonce_sha256"]
        != "81fd9baa8c75ed51e7027142328e4f52ac25458570516419c29644b41b96b9fb"
        or marker["operator_authorization_context"] != OPERATOR_AUTHORIZATION_CONTEXT
        or marker["operator_authorization_sha256"] != OPERATOR_AUTHORIZATION_SHA256
        or marker["entropy_source"] != "secrets.token_bytes"
        or marker["entropy_byte_count"] != 32
        or marker["raw_entropy_persisted"] is not False
        or marker["exclusive_inode_reserved_before_entropy"] is not True
        or marker["attempt_state"]
        != "PREPARATION_ATTEMPT_SPENT_TERMINAL_MARKER_CREATED_NO_RETRY"
        or marker["scientific_campaign_nonce_minted"] is not False
    ):
        raise TerminalFailureRegistrationError("marker semantics changed")
    if (
        genesis["marker_raw_sha256"] != RECORD_ROWS[0]["raw_sha256"]
        or genesis["marker_sha256"] != marker["marker_sha256"]
        or genesis["preparation_instance_nonce_sha256"]
        != marker["preparation_instance_nonce_sha256"]
        or genesis["genesis_sha256"] != RECORD_ROWS[1]["record_sha256"]
        or genesis["next_preparation_event_ordinal"] != 0
        or genesis["scientific_authority_ledger_created"] is not False
        or genesis["scientific_campaign_nonce_minted"] is not False
    ):
        raise TerminalFailureRegistrationError("genesis link changed")

    common_roles = (
        "EVENT_0_NONCE_CLAIM",
        "EVENT_0",
        "SOURCE_CAPSULE_MANIFEST",
        "EVENT_1_NONCE_CLAIM",
        "EVENT_1",
        "SOURCE_CAPSULE_ADMISSION",
        "EVENT_2_NONCE_CLAIM",
        "EVENT_2",
        "RUNTIME_DOUBLE_CAPTURE_REQUEST",
        "RUNTIME_CAPTURE_A_LAUNCH_CLAIM",
    )
    for role in common_roles:
        record = records[role]
        if (
            record.get("marker_sha256") != marker["marker_sha256"]
            or record.get("genesis_sha256") != genesis["genesis_sha256"]
        ):
            raise TerminalFailureRegistrationError(role + " common custody changed")
        if "preparation_instance_nonce_sha256" in record and (
            record["preparation_instance_nonce_sha256"]
            != marker["preparation_instance_nonce_sha256"]
        ):
            raise TerminalFailureRegistrationError(role + " nonce custody changed")

    event_roles = ("EVENT_0", "EVENT_1", "EVENT_2")
    claim_roles = (
        "EVENT_0_NONCE_CLAIM",
        "EVENT_1_NONCE_CLAIM",
        "EVENT_2_NONCE_CLAIM",
    )
    payload_roles = (
        "SOURCE_CAPSULE_MANIFEST",
        "SOURCE_CAPSULE_ADMISSION",
        "RUNTIME_DOUBLE_CAPTURE_REQUEST",
    )
    event_kinds = (
        "CAPSULE_MATERIALIZATION_OPENED",
        "CAPSULE_ADMITTED",
        "RUNTIME_DOUBLE_CAPTURE_OPENED",
    )
    outcomes = ("OPENED", "ADMITTED_PREPARATION_CUSTODY_ONLY", "OPENED")
    previous = genesis["genesis_sha256"]
    for ordinal, (claim_role, event_role, payload_role, kind, outcome) in enumerate(
        zip(claim_roles, event_roles, payload_roles, event_kinds, outcomes)
    ):
        claim = records[claim_role]
        event = records[event_role]
        payload = records[payload_role]
        payload_row = next(row for row in RECORD_ROWS if row["role"] == payload_role)
        if (
            claim["claim_scope"] != "PREPARATION_EVENT"
            or claim["preparation_event_ordinal"] != ordinal
            or claim["operation_kind"] != kind
            or claim["previous_head_sha256"] != previous
            or claim["recovery_policy"] != "DETERMINISTIC_MISSING_ROWS_MAY_RESUME"
            or claim["claim_state"] != "OPERATION_NONCE_SPENT"
            or event["preparation_event_ordinal"] != ordinal
            or event["preparation_event_kind"] != kind
            or event["previous_head_sha256"] != previous
            or event["nonce_claim_sha256"] != claim["claim_sha256"]
            or event["operation_nonce_sha256"] != claim["operation_nonce_sha256"]
            or event["payload_raw_sha256"] != payload_row["raw_sha256"]
            or event["payload_record_sha256"] != payload_row["record_sha256"]
            or event["payload_schema"] != payload["schema"]
            or event["payload_relative_path"] != payload_row["path"]
            or event["event_outcome"] != outcome
            or event["scientific_authority_event_ordinal"] is not None
            or event["scientific_execution_performed"] is not False
            or event["rank_execution_performed"] is not False
            or event["training_execution_performed"] is not False
        ):
            raise TerminalFailureRegistrationError("event chain changed")
        expected_operation_nonce = _sha256(
            OPERATION_NONCE_DOMAIN
            + marker["marker_sha256"].encode("ascii")
            + b"\0"
            + kind.encode("ascii")
        )
        if claim["operation_nonce_sha256"] != expected_operation_nonce:
            raise TerminalFailureRegistrationError("event operation nonce changed")
        previous = event["event_sha256"]
    if previous != "4ba4799fdfa3bf407ea269c035c6502114b9bae5b93bdde1b32c6ebe497646a5":
        raise TerminalFailureRegistrationError("validated event head changed")

    manifest = records["SOURCE_CAPSULE_MANIFEST"]
    admission = records["SOURCE_CAPSULE_ADMISSION"]
    request = records["RUNTIME_DOUBLE_CAPTURE_REQUEST"]
    capture_a = records["RUNTIME_CAPTURE_A_LAUNCH_CLAIM"]
    if (
        admission["manifest_raw_sha256"] != RECORD_ROWS[4]["raw_sha256"]
        or admission["manifest_sha256"] != manifest["manifest_sha256"]
        or request["source_capsule_manifest_sha256"] != manifest["manifest_sha256"]
        or request["source_capsule_admission_sha256"] != admission["admission_sha256"]
        or request["capture_count"] != 2
        or request["capture_ordinals"] != [0, 1]
        or request["environment_policy_sha256"]
        != "ae8d89b962a633a7691519d86f2d1617d9c9ee23fdb94dd6bc37f5c16259a018"
        or request["raw_capture_envelopes_persisted"] is not False
        or request["scientific_compute_requested"] is not False
        or request["runtime_approval_requested"] is not False
        or capture_a["claim_scope"] != "RUNTIME_CAPTURE_LAUNCH"
        or capture_a["preparation_event_ordinal"] is not None
        or capture_a["operation_kind"] != "RUNTIME_CAPTURE_A_LAUNCH"
        or capture_a["previous_head_sha256"] != previous
        or capture_a["recovery_policy"] != "LAUNCH_SPENT_NO_RECAPTURE"
        or capture_a["claim_state"] != "OPERATION_NONCE_SPENT"
    ):
        raise TerminalFailureRegistrationError("runtime request or A claim changed")
    expected_capture_nonce = _sha256(
        OPERATION_NONCE_DOMAIN
        + marker["marker_sha256"].encode("ascii")
        + b"\0RUNTIME_CAPTURE_A_LAUNCH"
    )
    if capture_a["operation_nonce_sha256"] != expected_capture_nonce:
        raise TerminalFailureRegistrationError("capture A operation nonce changed")


def _load_v2_machine(root: Path) -> Dict[str, Any]:
    payload, _ = _read_stable_file(root, V2_MACHINE_PATH)
    expected = FROZEN_V2_BINDINGS[1]
    if len(payload) != expected["bytes"] or _sha256(payload) != expected["raw_sha256"]:
        raise TerminalFailureRegistrationError("v2 machine freeze raw custody changed")
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TerminalFailureRegistrationError(
            "v2 machine freeze is not JSON"
        ) from error
    if payload != _canonical(record) + b"\n":
        raise TerminalFailureRegistrationError("v2 machine freeze is not canonical")
    if record.get("record_sha256") != V2_MACHINE_RECORD_SHA256:
        raise TerminalFailureRegistrationError("v2 machine self digest changed")
    body = dict(record)
    body["record_sha256"] = None
    domain = (record["schema_version"] + "\0").encode("ascii")
    if _sha256(domain + _canonical(body)) != V2_MACHINE_RECORD_SHA256:
        raise TerminalFailureRegistrationError("v2 machine self digest is invalid")
    snapshot = record.get("static_qualification_snapshot")
    if (
        type(snapshot) is not dict
        or snapshot.get("snapshot_sha256") != V2_STATIC_SNAPSHOT_SHA256
    ):
        raise TerminalFailureRegistrationError("v2 static snapshot changed")
    snapshot_body = dict(snapshot)
    del snapshot_body["snapshot_sha256"]
    expected_snapshot = _sha256(
        b"heterodiff-a1-r1-activation-preparation-static-qualification-v2\0"
        + _canonical(snapshot_body)
    )
    if expected_snapshot != V2_STATIC_SNAPSHOT_SHA256:
        raise TerminalFailureRegistrationError("v2 static snapshot is invalid")
    return record


def _audit_frozen_v2_files(root: Path) -> None:
    for row in FROZEN_V2_BINDINGS:
        payload, information = _read_stable_file(
            root, row["path"], expected_mode=0o644, expected_nlink=1
        )
        if (
            len(payload) != row["bytes"]
            or _sha256(payload) != row["raw_sha256"]
            or stat.S_ISLNK(information.st_mode)
            or not stat.S_ISREG(information.st_mode)
        ):
            raise TerminalFailureRegistrationError(row["role"] + " changed")


def _audit_frozen_test_defect(root: Path) -> None:
    payload, _ = _read_stable_file(root, V2_TEST_PATH)
    lines = payload.decode("utf-8").splitlines()
    expected_fragments = {
        314: "def test_owned_paths_are_exactly_additive_and_no_operational_output_exists",
        316: "assert not authority._path_has_entry(WORKSPACE / authority.MARKER_PATH)",
        401: "def test_status_is_zero_write_transition_aware_and_initially_awaiting_authorization",
        415: 'assert observed["live_transition"] == {',
    }
    for line_number, fragment in expected_fragments.items():
        if fragment not in lines[line_number - 1]:
            raise TerminalFailureRegistrationError("frozen stale-test evidence changed")
    if not _path_has_entry(root / MARKER_PATH):
        raise TerminalFailureRegistrationError("first stale assertion is not false")
    authority_payload, _ = _read_stable_file(
        root, V2_AUTHORITY_PATH, expected_mode=0o644, expected_nlink=1
    )
    authority_lines = authority_payload.decode("utf-8").splitlines()
    authority_fragments = {
        3074: "if not binding_present:",
        3107: "raise PreparationAuthorityError(",
        3108: "runtime launch claim is terminal without its in-memory result binding",
        3411: ('"live_state": "PREPARATION_ATTEMPT_SPENT_TERMINAL_CUSTODY_INVALID"'),
        3416: '"preparation_event_count": 0',
    }
    for line_number, fragment in authority_fragments.items():
        if fragment not in authority_lines[line_number - 1]:
            raise TerminalFailureRegistrationError(
                "v2 status-collapse evidence changed"
            )
    if not _path_has_entry(
        root / (PREPARATION_ROOT + "/ledger/nonce-claims/runtime-capture-a.json")
    ) or _path_has_entry(
        root / (PREPARATION_ROOT + "/ledger/receipts/runtime-capture-a.binding.json")
    ):
        raise TerminalFailureRegistrationError("second stale assertion is not false")


def _assert_absent(path: Path, label: str) -> None:
    if _path_has_entry(path):
        raise TerminalFailureRegistrationError(label + " is unexpectedly present")


def audit_terminal_custody(workspace_root: Any = WORKSPACE_ROOT) -> Dict[str, Any]:
    root = Path(workspace_root).absolute()
    if root != WORKSPACE_ROOT or root.resolve(strict=True) != WORKSPACE_ROOT:
        raise TerminalFailureRegistrationError(
            "only the canonical workspace is auditable"
        )
    _audit_frozen_v2_files(root)
    v2_machine = _load_v2_machine(root)

    before = _tree_snapshot(root / PREPARATION_ROOT)
    records: Dict[str, Dict[str, Any]] = {}
    for row in RECORD_ROWS:
        _, record = _load_exact_record(root, row)
        records[row["role"]] = record
    _validate_record_links(records)
    capsule = _audit_capsule(
        root,
        records["SOURCE_CAPSULE_MANIFEST"],
        records["SOURCE_CAPSULE_ADMISSION"],
    )

    expected_files, expected_directories = _expected_preparation_tree(
        records["SOURCE_CAPSULE_MANIFEST"]
    )
    after = _tree_snapshot(root / PREPARATION_ROOT)
    if before != after:
        raise TerminalFailureRegistrationError("preparation tree changed during audit")
    if [row[0] for row in after["files"]] != expected_files:
        raise TerminalFailureRegistrationError("terminal preparation files changed")
    if [row[0] for row in after["directories"]] != expected_directories:
        raise TerminalFailureRegistrationError(
            "terminal preparation directories changed"
        )
    for relative, identity in after["files"]:
        mode = stat.S_IMODE(identity[2])
        nlink = identity[3]
        if mode != 0o600 or nlink != 1:
            raise TerminalFailureRegistrationError("terminal file custody changed")
        if relative == "ledger/writer.lock" and identity[6] != 0:
            raise TerminalFailureRegistrationError("writer lock content changed")
    for _, identity in after["directories"]:
        if stat.S_IMODE(identity[2]) != 0o700:
            raise TerminalFailureRegistrationError("terminal directory mode changed")

    for row in ABSENT_V2_ROWS:
        _assert_absent(root / row["path"], row["role"])
    if any((root / RUNTIME_CANDIDATE_ROOT).iterdir()):
        raise TerminalFailureRegistrationError("runtime candidate root is not empty")

    path_roster = v2_machine["static_qualification_snapshot"]["path_roster"]
    frozen_snapshot = v2_machine["static_qualification_snapshot"]
    if (
        frozen_snapshot["current_unresolved_null_count"] != 172
        or frozen_snapshot["current_open_blocker_count"] != 12
        or frozen_snapshot["d1_quarantine"]["row_count"] != 550
        or frozen_snapshot["d1_quarantine"]["roster_sha256"]
        != "1efbc36a3bdba6c052900ec3131abc2ead3766bafc43bce435e1698a79f19a14"
    ):
        raise TerminalFailureRegistrationError("frozen blocker or D1 custody changed")
    for relative in path_roster["dormant_v1_paths_permanently_absent"]:
        _assert_absent(root / relative, "dormant v1 path")
    _assert_absent(
        root / path_roster["permanently_absent_v1_src_adapter"],
        "permanently absent v1 src adapter",
    )
    _audit_frozen_test_defect(root)
    _audit_frozen_v2_files(root)
    repeated_v2_machine = _load_v2_machine(root)
    if _canonical(repeated_v2_machine) != _canonical(v2_machine):
        raise TerminalFailureRegistrationError("v2 machine changed during audit")
    for row in ABSENT_V2_ROWS:
        _assert_absent(root / row["path"], row["role"])
    final_tree = _tree_snapshot(root / PREPARATION_ROOT)
    if before != after or before != final_tree:
        raise TerminalFailureRegistrationError("preparation tree changed during audit")
    return {
        "schema": QUALIFICATION_SCHEMA,
        "terminal_state": TERMINAL_STATE,
        "global_state": GLOBAL_STATE,
        "marker_attempt_spent": True,
        "retry_permitted": False,
        "validated_preparation_event_count": 3,
        "validated_current_head_sha256": records["EVENT_2"]["event_sha256"],
        "capture_a_launch_claim_spent": True,
        "capture_a_binding_present": False,
        "capture_b_launch_claim_present": False,
        "capture_b_binding_present": False,
        "runtime_candidate_present": False,
        "typed_terminal_ledger_event_present": False,
        "raw_runtime_envelopes_persisted": False,
        "capsule": capsule,
        "preparation_file_count": len(expected_files),
        "preparation_directory_count": len(expected_directories),
        "frozen_test_failure_count": 2,
        "unresolved_null_count": 172,
        "open_blocker_count": 12,
        "d1_quarantine_row_count": 550,
        "d1_quarantine_roster_sha256": (
            "1efbc36a3bdba6c052900ec3131abc2ead3766bafc43bce435e1698a79f19a14"
        ),
        "execution_authorized": False,
    }


def _expected_fixed_registration() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "registration_id": (
            "A1_R1_ACTIVATION_PREPARATION_V2_TERMINAL_FAILURE_REGISTRATION_V1"
        ),
        "registration_mode": (
            "ADDITIVE_READ_ONLY_TERMINAL_FAILURE_FORENSIC_REGISTRATION"
        ),
        "scope": "INTERNAL_PREREGISTRATION_TERMINAL_CUSTODY",
        "terminal_state": TERMINAL_STATE,
        "global_state": GLOBAL_STATE,
        "predecessor_freeze": {
            "bindings": [dict(row) for row in FROZEN_V2_BINDINGS],
            "machine_record_sha256": V2_MACHINE_RECORD_SHA256,
            "static_snapshot_sha256": V2_STATIC_SNAPSHOT_SHA256,
            "frozen_bytes_edited": False,
        },
        "authorization": {
            "operator_authorization_context": OPERATOR_AUTHORIZATION_CONTEXT,
            "operator_authorization_sha256": OPERATOR_AUTHORIZATION_SHA256,
            "user_assent_text": USER_ASSENT_TEXT,
            "user_assent_normalization": USER_ASSENT_NORMALIZATION,
            "user_assent_sha256": user_assent_sha256(),
            "user_assent_source": "CONVERSATION_VISIBLE_TEXT",
            "user_message_envelope_bound_as_workspace_artifact": False,
            "authorized_scope": (
                "V2_MARKER_CAPSULE_AND_EXACTLY_TWO_PRIVACY_SAFE_RUNTIME_INSPECTIONS"
            ),
            "runtime_approval_authorized": False,
            "rank_training_production_science_authorized": False,
        },
        "observed_terminal_custody": {
            "records": [dict(row) for row in RECORD_ROWS],
            "record_count": len(RECORD_ROWS),
            "validated_preparation_event_count": 3,
            "validated_current_head_sha256": (
                "4ba4799fdfa3bf407ea269c035c6502114b9bae5b93bdde1b32c6ebe497646a5"
            ),
            "capture_a_launch_claim_spent": True,
            "capture_a_binding_present": False,
            "capture_b_launch_claim_present": False,
            "capture_b_binding_present": False,
            "runtime_candidate_present": False,
            "runtime_candidate_directory_empty": True,
            "typed_pre_envelope_terminal_event_present": False,
            "event_3_nonce_claim_present": False,
            "event_3_present": False,
            "event_4_nonce_claim_present": False,
            "event_4_present": False,
            "raw_capture_envelopes_persisted": False,
            "capsule_file_count": 53,
            "capsule_directory_count": 14,
            "capsule_inventory_sha256": (
                "c68e21aa648c4823bd87987399eb0ce76149adaa57c7b19b162783ad5dc01360"
            ),
            "capsule_execution_admissible": False,
            "capsule_admission_is_preparation_custody_only": True,
            "capsule_admission_is_scientific_execution_evidence": False,
            "preparation_file_count": 65,
            "preparation_directory_count": 20,
            "owner_only_regular_nonsymlink_closed_world": True,
        },
        "failure_diagnosis": {
            "canonical_action": "--capture-runtime-candidate",
            "authority_call_chain": [
                "_execute_runtime_at_root",
                "_run_runtime_child",
                "PreparationAuthorityError(runtime capture child failed closed)",
            ],
            "reported_canonical_action_exit_code": 1,
            "child_exit_code_directly_observed": False,
            "reported_canonical_action_wall_time_seconds": "1.99",
            "canonical_action_result_source": "ORCHESTRATOR_REPORTED_CANONICAL_RUN",
            "canonical_action_raw_command_receipt_bound_as_workspace_artifact": False,
            "timeout_observed": False,
            "stdout_size_failure_observed": False,
            "stderr_size_failure_observed": False,
            "raw_child_stderr_persisted": False,
            "raw_child_stderr_surfaced": False,
            "verbatim_child_exception_claimed": False,
            "diagnostic_method": (
                "READ_ONLY_EQUIVALENT_NON_ORACLE_PROFILE_PROBE_PLUS_FROZEN_CONTROL_FLOW"
            ),
            "equivalent_profile_probe_raw_receipt_bound_as_workspace_artifact": False,
            "frozen_requested_environment": dict(FROZEN_REQUESTED_ENVIRONMENT),
            "equivalent_profile_probe_effective_environment_internal": dict(
                EXPECTED_EFFECTIVE_ENVIRONMENT
            ),
            "failed_child_environment_directly_observed": False,
            "cause_is_frozen_control_flow_inference": True,
            "unexpected_effective_key": "__CF_USER_TEXT_ENCODING",
            "unexpected_effective_value_internal": "0x1F5:0x0:0x0",
            "unexpected_effective_value_is_uid_like": True,
            "current_uid_decimal": 501,
            "future_v3_value_derivation": "0x%X:0x0:0x0 % os.getuid()",
            "public_derivative_token": "<DARWIN_USER_TEXT_ENCODING>",
            "exact_environment_equality_result": False,
            "isolation_flags_match": True,
            "venv_executable_match": True,
            "framework_realpath_match": True,
            "isolated_sys_path_match": True,
            "cpython_3_11_darwin_arm64_match": True,
            "deterministic_first_failing_check": (
                "runtime child environment is not exact"
            ),
            "downstream_runtime_checks_reached": False,
            "additional_downstream_failure_absence_claimed": False,
        },
        "public_status_defect": {
            "orchestrator_reported_immediate_post_failure_live_transition": dict(
                EXPECTED_PUBLIC_STATUS
            ),
            "status_observation_source": (
                "ORCHESTRATOR_REPORTED_IMMEDIATE_POST_FAILURE_STATUS"
            ),
            "status_raw_receipt_bound_as_workspace_artifact": False,
            "status_fallback_independently_reconstructed_from_frozen_source_and_terminal_custody": True,
            "status_spent_closed_no_retry_unauthorized_booleans_correct": True,
            "status_generic_custody_invalid_reason_is_forensically_precise": False,
            "status_reported_preparation_event_count": 0,
            "independently_validated_preparation_event_count": 3,
            "valid_prefix_collapsed_on_terminal_exception": True,
            "status_is_complete_forensic_receipt": False,
        },
        "frozen_test_defect": {
            "test_path": V2_TEST_PATH,
            "targeted_test_count": 2,
            "targeted_pass_count": 0,
            "targeted_failure_count": 2,
            "targeted_exit_code": 1,
            "targeted_result_source": "ORCHESTRATOR_REPORTED_POST_TRANSITION_RUN",
            "targeted_test_raw_receipt_bound_as_workspace_artifact": False,
            "failure_conditions_independently_reopened": True,
            "failures": [dict(row) for row in FROZEN_TEST_FAILURES],
            "claimed_transition_awareness_is_durable": False,
            "frozen_test_edited": False,
        },
        "nonclaims": {
            "v2_retry_permitted": False,
            "v2_repair_or_resume_permitted": False,
            "postmortem_edited_deleted_or_replaced_v2_files_or_artifacts": False,
            "postmortem_contacted_entropy": False,
            "postmortem_invoked_v2_writer": False,
            "postmortem_invoked_v2_runtime_oracle_or_capture_child": False,
            "capture_a_binding_created": False,
            "capture_b_launch_claim_created": False,
            "capture_b_binding_created": False,
            "runtime_candidate_created": False,
            "runtime_review_created": False,
            "runtime_approval_created": False,
            "scientific_campaign_nonce_minted": False,
            "postmortem_network_contacted": False,
            "rank_execution_performed": False,
            "training_execution_performed": False,
            "production_execution_performed": False,
            "scientific_execution_performed": False,
            "claim_or_submission_promoted": False,
            "v3_authorized": False,
        },
        "state_preservation": {
            "projection_source": "FROZEN_V2_STATIC_QUALIFICATION_SNAPSHOT",
            "projection_values_reopened_from_frozen_snapshot": True,
            "postmortem_underlying_rosters_recomputed": False,
            "unresolved_null_count": 172,
            "open_blocker_count": 12,
            "d1_quarantine_row_count": 550,
            "d1_quarantine_roster_sha256": (
                "1efbc36a3bdba6c052900ec3131abc2ead3766bafc43bce435e1698a79f19a14"
            ),
            "d1_execution_admissible": False,
            "global_state": GLOBAL_STATE,
        },
        "publication_anonymity_boundary": {
            "internal_only": True,
            "anonymous_submission_inclusion_permitted": False,
            "public_release_inclusion_permitted": False,
            "postmortem_registration_package_inclusion_permitted": False,
            "raw_v2_operational_custody_inclusion_permitted": False,
            "raw_child_stderr_available_for_publication": False,
            "uid_like_effective_environment_value_publication_safe": False,
            "human_prose_reproduces_uid_like_value": False,
            "uid_like_value_internal_workspace_carriers": [
                MACHINE_PATH,
                VALIDATOR_PATH,
                TEST_PATH,
            ],
            "conversation_or_tool_logs_may_retain_uid_like_value": True,
            "all_uid_like_value_workspace_carriers_excluded_from_publication": True,
            "internal_conversation_and_tool_logs_excluded_from_publication": True,
            "publication_safe_derivative_required": True,
            "publication_safe_derivative_path": None,
            "darwin_value_must_be_tokenized": True,
            "fresh_anonymity_audit_required": True,
        },
        "next_gate": {
            "v2_terminal_artifacts_must_remain_immutable": True,
            "v2_retry_delete_repair_forbidden": True,
            "additive_disjoint_v3_registration_required": True,
            "v3_marker_and_root_must_not_reuse_v2_paths": True,
            "v3_environment_policy_must_distinguish_requested_and_effective": True,
            "v3_darwin_value_must_derive_from_os_getuid_not_geteuid": True,
            "v3_read_only_non_oracle_profile_preflight_before_marker_required": True,
            "v3_canonical_tests_must_be_genuinely_transition_aware": True,
            "v3_requires_new_explicit_operator_authorization": True,
            "v3_currently_authorized": False,
            "runtime_approval_rank_training_production_science_authorized": False,
        },
    }


def _validate_machine_registration_payload(
    root: Path, payload: bytes
) -> Dict[str, Any]:
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TerminalFailureRegistrationError(
            "postmortem machine record is not JSON"
        ) from error
    if type(record) is not dict or payload != _canonical(record) + b"\n":
        raise TerminalFailureRegistrationError(
            "postmortem machine record is not canonical"
        )
    fixed = _expected_fixed_registration()
    expected_keys = set(fixed) | {"registration_bindings", "record_sha256"}
    if set(record) != expected_keys:
        raise TerminalFailureRegistrationError("postmortem machine fields changed")
    for key, value in fixed.items():
        if type(record[key]) is not type(value) or _canonical(
            record[key]
        ) != _canonical(value):
            raise TerminalFailureRegistrationError("postmortem field changed: " + key)
    bindings = record["registration_bindings"]
    expected_paths = (HUMAN_PATH, VALIDATOR_PATH, TEST_PATH)
    expected_roles = ("HUMAN_REGISTRATION", "READ_ONLY_VALIDATOR", "HOSTILE_TEST")
    if type(bindings) is not list or len(bindings) != 3:
        raise TerminalFailureRegistrationError("postmortem bindings changed")
    for ordinal, (binding, relative, role) in enumerate(
        zip(bindings, expected_paths, expected_roles)
    ):
        if type(binding) is not dict or set(binding) != {
            "ordinal",
            "role",
            "path",
            "bytes",
            "raw_sha256",
            "lf_only",
            "mode_octal",
            "nlink",
            "is_regular_file",
            "is_symlink",
        }:
            raise TerminalFailureRegistrationError("postmortem binding shape changed")
        bound_payload, information = _read_stable_file(
            root, relative, expected_mode=0o644, expected_nlink=1
        )
        expected_binding = {
            "ordinal": ordinal,
            "role": role,
            "path": relative,
            "bytes": len(bound_payload),
            "raw_sha256": _sha256(bound_payload),
            "lf_only": bytes((13,)) not in bound_payload,
            "mode_octal": "0644",
            "nlink": 1,
            "is_regular_file": stat.S_ISREG(information.st_mode),
            "is_symlink": stat.S_ISLNK(information.st_mode),
        }
        if _canonical(binding) != _canonical(expected_binding):
            raise TerminalFailureRegistrationError("postmortem binding value changed")
    claimed = _require_sha256(record.get("record_sha256"), "postmortem self digest")
    body = dict(record)
    body["record_sha256"] = None
    if claimed != _sha256(REGISTRATION_DOMAIN + _canonical(body)):
        raise TerminalFailureRegistrationError("postmortem self digest changed")
    return record


def _load_machine_registration(root: Path) -> Tuple[bytes, Dict[str, Any]]:
    payload, _ = _read_stable_file(
        root, MACHINE_PATH, expected_mode=0o644, expected_nlink=1
    )
    record = _validate_machine_registration_payload(root, payload)
    repeated, _ = _read_stable_file(
        root, MACHINE_PATH, expected_mode=0o644, expected_nlink=1
    )
    if repeated != payload:
        raise TerminalFailureRegistrationError("postmortem machine changed during load")
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
    root = Path(workspace_root).absolute()
    custody = audit_terminal_custody(root)
    _, registration = _load_machine_registration(root)
    custody_repeat = audit_terminal_custody(root)
    if _canonical(custody_repeat) != _canonical(custody):
        raise TerminalFailureRegistrationError("terminal custody changed during load")
    value = object.__new__(TerminalFailureQualification)
    object.__setattr__(value, "_registration", _canonical(registration))
    object.__setattr__(value, "_custody", _canonical(custody))
    object.__setattr__(value, "_record_sha256", registration["record_sha256"])
    return value


def status(workspace_root: Any = WORKSPACE_ROOT) -> Dict[str, Any]:
    qualification = load_qualification(workspace_root)
    custody = qualification.custody()
    return {
        "schema": (
            "heterodiff-a1-r1-activation-preparation-v2-terminal-failure-status-v1"
        ),
        "terminal_state": custody["terminal_state"],
        "global_state": custody["global_state"],
        "marker_attempt_spent": True,
        "retry_permitted": False,
        "validated_preparation_event_count": 3,
        "validated_current_head_sha256": custody["validated_current_head_sha256"],
        "capture_a_launch_claim_spent": True,
        "capture_a_binding_present": False,
        "capture_b_launch_claim_present": False,
        "runtime_candidate_present": False,
        "v2_status_event_count_collapse_registered": True,
        "frozen_test_failure_count": 2,
        "v3_authorized": False,
        "execution_authorized": False,
        "registration_record_sha256": qualification.record_sha256,
    }


__all__ = [
    "ABSENT_V2_ROWS",
    "ASSENT_DOMAIN",
    "FROZEN_TEST_FAILURES",
    "FROZEN_V2_BINDINGS",
    "GLOBAL_STATE",
    "HUMAN_PATH",
    "MACHINE_PATH",
    "QUALIFICATION_SCHEMA",
    "RECORD_ROWS",
    "REGISTRATION_DOMAIN",
    "SCHEMA",
    "TERMINAL_STATE",
    "TEST_PATH",
    "TerminalFailureQualification",
    "TerminalFailureRegistrationError",
    "VALIDATOR_PATH",
    "WORKSPACE_ROOT",
    "audit_terminal_custody",
    "load_qualification",
    "status",
    "user_assent_sha256",
]
