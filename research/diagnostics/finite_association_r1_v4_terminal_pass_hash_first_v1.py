#!/usr/bin/env python3
"""Hash-first trust envelope for the historical R1 V4→V3→V2 chain.

The accepted V4 and V3 read-only validators each authenticate a predecessor
path and then separately reread that path for execution.  This envelope is the
sole supported revalidation entrypoint: it captures and pins V4, V3, and V2
before compiling any project source, compiles only captured bytes, and replaces
both inherited pathname loaders.

The historical V4 receipt is immutable.  Current validation can still be on
HOLD when an inherited custody predicate refuses the present workspace; the
envelope never removes, ignores, or bypasses that refusal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping


SCHEMA_VERSION = "finite-association-r1-v4-terminal-pass-hash-first-v1"
CHAIN_INTEGRITY_STATE = "HASH_FIRST_V4_V3_V2_CHAIN_INTEGRITY_PASS"
CURRENT_CUSTODY_HOLD_STATE = (
    "HASH_FIRST_CHAIN_INTEGRITY_PASS_CURRENT_CUSTODY_HOLD"
)
CURRENT_CUSTODY_HOLD_REASON = "FROZEN_PREDECESSOR_BYTECODE_CACHE_EXISTS"
INHERITED_HOLD_MESSAGE = "frozen predecessor bytecode cache exists"
HISTORICAL_REGISTRATION_RECORD_SHA256 = (
    "9d69a41faa8f4a52c21c81ef9009d0eff0315e5d7e7d5ae3ff39cc135e4451bb"
)
EXPECTED_STATUS = {
    "schema": (
        "heterodiff-a1-r1-activation-preparation-v4-transition-safe-live-host-"
        "environment-rehearsal-terminal-pass-status-v1"
    ),
    "global_state": "DRAFT_NOT_EXECUTABLE",
    "terminal_state": (
        "R1_A1_ACTIVATION_PREPARATION_V4_TERMINAL_REHEARSAL_PASS_NO_RETRY_"
        "NO_RUNTIME_APPROVAL_NO_SCIENTIFIC_EXECUTION_AUTHORITY"
    ),
    "outcome": "PASS",
    "authoritative_event_ordinal": 3,
    "authoritative_event_sha256": (
        "3335688ef062c5f3d6815b35db025dc84c5abf0cf2f10866e52c2a91eb37058a"
    ),
    "attempt_id_sha256": (
        "62ec7fcd893509c7ddf13cb16f38bbf600884dcb8c56158308dd9326b1464b20"
    ),
    "attempt_nonce_sha256": (
        "963e04cee246a58c7c3c6a3643625913fd852c050c8876829f2c39d980a16e9d"
    ),
    "attempt_spent": True,
    "retry_permitted": False,
    "child_launch_claim_count": 1,
    "child_process_start_count": 1,
    "runtime_approval_created": False,
    "scientific_execution_performed": False,
    "effective_unresolved_null_count": 172,
    "open_blocker_count": 12,
    "test_data_unopened_before_freeze": None,
    "registration_record_sha256": HISTORICAL_REGISTRATION_RECORD_SHA256,
    "execution_authorized": False,
    "claim_promotion_permitted": False,
}

V4_VALIDATOR = (
    "research/diagnostics/finite_association_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_terminal_pass_"
    "registration_v1.py"
)
V3_VALIDATOR = (
    "research/diagnostics/finite_association_r1_activation_preparation_v3_"
    "live_host_environment_rehearsal_terminal_failure_registration_v1.py"
)
V2_VALIDATOR = (
    "research/diagnostics/finite_association_r1_activation_preparation_v2_"
    "terminal_failure_registration_v1.py"
)

VALIDATOR_PINS: tuple[tuple[str, int, str], ...] = (
    (
        V4_VALIDATOR,
        69_164,
        "573ac885e449a0203d4c0b78dfa833fb4269c1fc94aeb2289c9dd8e507460fb0",
    ),
    (
        V3_VALIDATOR,
        44_262,
        "2ae995d7609778f9201e3a90a2861c74898dfdc357b3f0b6f75b46bc68ce78bd",
    ),
    (
        V2_VALIDATOR,
        62_047,
        "ce59c0d855d22eea01e0091110ab6e928d071fe57ba1416f6e0ccab0e5bcf671",
    ),
)

MAX_VALIDATOR_BYTES = 1_048_576
_MODULE_NAMES = (
    "_r1_v4_hash_first_bound_v2",
    "_r1_v4_hash_first_bound_v3",
    "_r1_v4_hash_first_bound_v4",
)


class HashFirstR1ValidationError(RuntimeError):
    """Raised before unpinned project bytes can execute or on mixed states."""


@dataclass(frozen=True)
class BoundValidator:
    relative_path: str
    raw: bytes
    sha256: str
    size: int
    device: int
    inode: int
    uid: int
    gid: int
    mode: int
    nlink: int
    mtime_ns: int
    ctime_ns: int

    def identity(self) -> tuple[Any, ...]:
        return (
            self.relative_path,
            self.sha256,
            self.size,
            self.device,
            self.inode,
            self.uid,
            self.gid,
            self.mode,
            self.nlink,
            self.mtime_ns,
            self.ctime_ns,
        )

    def receipt(self) -> dict[str, Any]:
        return {
            "path": self.relative_path,
            "bytes": self.size,
            "sha256": self.sha256,
            "device": self.device,
            "inode": self.inode,
            "uid": self.uid,
            "gid": self.gid,
            "mode_octal": f"{self.mode:04o}",
            "nlink": self.nlink,
            "mtime_ns": self.mtime_ns,
            "ctime_ns": self.ctime_ns,
        }


def _fail(message: str) -> None:
    raise HashFirstR1ValidationError(message)


def _read_nofollow(root: Path, relative: str) -> tuple[bytes, os.stat_result]:
    if (
        not relative
        or relative.startswith("/")
        or "\x00" in relative
        or any(part in ("", ".", "..") for part in relative.split("/"))
    ):
        _fail(f"unsafe validator path: {relative!r}")

    absolute_root = root.absolute()
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in absolute_root.parts[1:]:
            nxt = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=fd,
            )
            os.close(fd)
            fd = nxt
        for part in relative.split("/")[:-1]:
            nxt = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=fd,
            )
            os.close(fd)
            fd = nxt
        leaf = os.open(
            relative.split("/")[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd
        )
        try:
            before = os.fstat(leaf)
            if (
                not stat.S_ISREG(before.st_mode)
                or stat.S_IMODE(before.st_mode) != 0o644
                or before.st_nlink != 1
                or before.st_size > MAX_VALIDATOR_BYTES
            ):
                _fail(f"unsafe validator custody: {relative}")
            chunks = bytearray()
            while chunk := os.read(leaf, 131_072):
                chunks.extend(chunk)
                if len(chunks) > MAX_VALIDATOR_BYTES:
                    _fail(f"validator exceeds byte ceiling: {relative}")
            after = os.fstat(leaf)
            if (
                before.st_dev,
                before.st_ino,
                before.st_uid,
                before.st_gid,
                before.st_mode,
                before.st_nlink,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            ) != (
                after.st_dev,
                after.st_ino,
                after.st_uid,
                after.st_gid,
                after.st_mode,
                after.st_nlink,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                _fail(f"validator changed during capture: {relative}")
            return bytes(chunks), after
        finally:
            os.close(leaf)
    finally:
        os.close(fd)


def _capture_one(
    root: Path, relative: str, expected_bytes: int, expected_sha256: str
) -> BoundValidator:
    raw, metadata = _read_nofollow(root, relative)
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != expected_bytes or digest != expected_sha256:
        _fail(f"validator pin mismatch before execution: {relative}")
    return BoundValidator(
        relative_path=relative,
        raw=raw,
        sha256=digest,
        size=len(raw),
        device=metadata.st_dev,
        inode=metadata.st_ino,
        uid=metadata.st_uid,
        gid=metadata.st_gid,
        mode=stat.S_IMODE(metadata.st_mode),
        nlink=metadata.st_nlink,
        mtime_ns=metadata.st_mtime_ns,
        ctime_ns=metadata.st_ctime_ns,
    )


def _capture_all(root: Path) -> dict[str, BoundValidator]:
    captured = tuple(
        _capture_one(root, relative, expected_bytes, expected_sha256)
        for relative, expected_bytes, expected_sha256 in VALIDATOR_PINS
    )
    if len(captured) != len({item.relative_path for item in captured}):
        _fail("duplicate validator pin")
    return {item.relative_path: item for item in captured}


def _verify_captured(captured: Mapping[str, BoundValidator]) -> None:
    expected = {
        relative: (expected_bytes, expected_sha256)
        for relative, expected_bytes, expected_sha256 in VALIDATOR_PINS
    }
    if set(captured) != set(expected):
        _fail("captured validator roster mismatch")
    for relative, (expected_bytes, expected_sha256) in expected.items():
        bound = captured[relative]
        if (
            type(bound) is not BoundValidator
            or bound.relative_path != relative
            or bound.size != expected_bytes
            or len(bound.raw) != expected_bytes
            or bound.sha256 != expected_sha256
            or hashlib.sha256(bound.raw).hexdigest() != expected_sha256
            or bound.mode != 0o644
            or bound.nlink != 1
        ):
            _fail(f"captured validator pin mismatch: {relative}")


def _exec_captured_module(
    bound: BoundValidator, root: Path, module_name: str
) -> ModuleType:
    module = ModuleType(module_name)
    module.__file__ = str(root.absolute() / bound.relative_path)
    module.__package__ = ""
    missing = object()
    previous = sys.modules.get(module_name, missing)
    sys.modules[module_name] = module
    try:
        exec(
            compile(bound.raw, module.__file__, "exec", dont_inherit=True),
            module.__dict__,
        )
    finally:
        if previous is missing:
            del sys.modules[module_name]
        else:
            sys.modules[module_name] = previous
    return module


def _same_root(requested: Any, captured_root: Path) -> None:
    if Path(requested).absolute() != captured_root.absolute():
        _fail("inherited validator requested a different root")


def _compile_chain(
    root: Path, captured: Mapping[str, BoundValidator]
) -> tuple[ModuleType, ModuleType, ModuleType]:
    _verify_captured(captured)
    captured_root = root.absolute()
    v2 = _exec_captured_module(captured[V2_VALIDATOR], captured_root, _MODULE_NAMES[0])
    v3 = _exec_captured_module(captured[V3_VALIDATOR], captured_root, _MODULE_NAMES[1])

    def _captured_v2_loader(requested_root: Any) -> ModuleType:
        _same_root(requested_root, captured_root)
        return v2

    v3._load_exact_v2_postmortem = _captured_v2_loader
    v4 = _exec_captured_module(captured[V4_VALIDATOR], captured_root, _MODULE_NAMES[2])

    def _captured_v3_loader(requested_root: Any) -> ModuleType:
        _same_root(requested_root, captured_root)
        return v3

    v4._load_exact_v3_validator = _captured_v3_loader
    return v4, v3, v2


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _validate_pass_status(status_value: Any) -> None:
    if type(status_value) is not dict or status_value != EXPECTED_STATUS:
        _fail("historical PASS status differs from the exact accepted projection")


def _hold_paths(v3: ModuleType, root: Path) -> tuple[str, ...]:
    paths = v3._frozen_predecessor_pyc_paths(root)
    if type(paths) is not tuple or not paths:
        _fail("custody HOLD reported without a focused bytecode-cache roster")
    if paths != tuple(sorted(paths)) or any(type(path) is not str for path in paths):
        _fail("focused bytecode-cache roster is noncanonical")
    return paths


def validate(root: Path) -> dict[str, Any]:
    root = root.absolute()
    captured_before = _capture_all(root)
    v4, v3, _v2 = _compile_chain(root, captured_before)

    calls = (
        ("custody_1", v4.audit_terminal_custody),
        ("custody_2", v4.audit_terminal_custody),
        ("status_1", v4.status),
        ("status_2", v4.status),
    )
    passed: dict[str, Any] = {}
    holds: list[str] = []
    for label, function in calls:
        try:
            passed[label] = function(root)
        except Exception as exc:
            if (
                type(exc) is v3.TerminalFailureRegistrationError
                and str(exc) == INHERITED_HOLD_MESSAGE
            ):
                holds.append(label)
            else:
                _fail(
                    "wrapped validation refused outside the registered HOLD: "
                    f"{type(exc).__name__}: {exc}"
                )

    if holds and len(holds) != len(calls):
        _fail("mixed PASS/HOLD result across repeated validation")

    if holds:
        hold_paths = _hold_paths(v3, root)
        state = CURRENT_CUSTODY_HOLD_STATE
        current_custody_pass = False
        historical_revalidated = False
        status_value = None
        custody_sha256 = None
    else:
        if set(passed) != {label for label, _function in calls}:
            _fail("incomplete PASS result roster")
        if _canonical(passed["custody_1"]) != _canonical(passed["custody_2"]):
            _fail("custody result changed across repeated validation")
        if _canonical(passed["status_1"]) != _canonical(passed["status_2"]):
            _fail("status result changed across repeated validation")
        _validate_pass_status(passed["status_1"])
        hold_paths = ()
        state = CHAIN_INTEGRITY_STATE
        current_custody_pass = True
        historical_revalidated = True
        status_value = passed["status_1"]
        custody_sha256 = hashlib.sha256(
            b"finite-association-r1-v4-current-custody-v1\0"
            + _canonical(passed["custody_1"])
        ).hexdigest()

    captured_after = _capture_all(root)
    for relative in captured_before:
        if captured_before[relative].identity() != captured_after[relative].identity():
            _fail(f"validator identity changed across validation: {relative}")

    hold_roster_sha256 = (
        hashlib.sha256(
            b"finite-association-r1-v4-focused-pyc-hold-roster-v1\0"
            + _canonical(list(hold_paths))
        ).hexdigest()
        if hold_paths
        else None
    )
    return {
        "status": "PASS" if current_custody_pass else "HOLD",
        "schema_version": SCHEMA_VERSION,
        "state": state,
        "chain_integrity_state": CHAIN_INTEGRITY_STATE,
        "compiled_from_captured_bytes_only": True,
        "inherited_pathname_loaders_replaced": True,
        "validator_identities_stable": True,
        "validator_count": len(captured_before),
        "current_v3_custody_pass": current_custody_pass,
        "current_custody_hold_reason": (
            None if current_custody_pass else CURRENT_CUSTODY_HOLD_REASON
        ),
        "current_custody_hold_paths": list(hold_paths),
        "current_custody_hold_roster_sha256": hold_roster_sha256,
        "historical_registration_revalidated": historical_revalidated,
        "historical_registration_record_sha256": (
            HISTORICAL_REGISTRATION_RECORD_SHA256
        ),
        "historical_pass_status": status_value,
        "current_custody_sha256": custody_sha256,
        "network_actions": 0,
        "subprocess_actions": 0,
        "filesystem_writes": 0,
        "operational_receipts": 0,
        "scientific_executions": 0,
        "tracker_files_edited": 0,
        "validator_receipts": [
            captured_before[relative].receipt()
            for relative, _size, _digest in VALIDATOR_PINS
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    args = parser.parse_args(argv)
    try:
        result = validate(args.root)
    except (HashFirstR1ValidationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    # HOLD is an honest, structured outcome but remains fail-closed for callers
    # that use the process status as a validation gate.
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
