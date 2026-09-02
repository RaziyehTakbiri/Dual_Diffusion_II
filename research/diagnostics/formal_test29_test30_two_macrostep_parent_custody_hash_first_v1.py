#!/usr/bin/env python3
"""Hash-first parent-custody envelope for the two-macrostep precursor.

The underlying development API deliberately accepts caller-supplied parent
modules and therefore cannot authenticate them.  This envelope is the sole
supported reusable qualification entrypoint: it captures and pins the exact
candidate plus all three parent sources before compiling any project source,
compiles only those captured bytes into exact ModuleType objects, runs the
frozen qualification, and proves that all source identities remained stable.
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


SCHEMA_VERSION = (
    "formal-test29-test30-two-macrostep-parent-custody-hash-first-v1"
)
EXPECTED_PREDICATE = (
    "SYNTHETIC_SUPPLIED_INPUT_TWO_MACROSTEP_ROLLING_LINEAGE_PATH_VALIDATED"
)
EXPECTED_REPORT_SHA256 = (
    "2a278585373d017b3b60bed28dcbc0ab3830f72c0512891658fc2ab54c666d53"
)

CANDIDATE = (
    "src/heterodiff/evaluation/"
    "formal_test29_test30_two_macrostep_path_qualification.py"
)
SINGLE_PARENT = (
    "src/heterodiff/evaluation/"
    "formal_test29_test30_single_macrostep_integration.py"
)
TEST29_PARENT = (
    "src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py"
)
TEST30_PARENT = (
    "src/heterodiff/evaluation/"
    "formal_test30_synthetic_coupled_path_qualification.py"
)

# All four sources are fully captured and verified before the first compile.
SOURCE_PINS: tuple[tuple[str, int, str], ...] = (
    (
        CANDIDATE,
        59_285,
        "d1c3013aa0f4e7b31e19cef98d4aa5edf7991c5b8634dbfe091f8053b1808176",
    ),
    (
        SINGLE_PARENT,
        61_434,
        "e2f57ede06cb432f8507eb32eead7a77fbfc8d8d44cc7725a941182e7aedd0c7",
    ),
    (
        TEST29_PARENT,
        52_186,
        "308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089",
    ),
    (
        TEST30_PARENT,
        42_349,
        "373ef98c3605e0c0211da8dbc8782f2517cd5976026980e4fcd24435670839e0",
    ),
)

MAX_SOURCE_BYTES = 1_048_576


class ParentCustodyError(RuntimeError):
    """Raised before unpinned or unstable project source can execute."""


@dataclass(frozen=True)
class BoundSource:
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
    raise ParentCustodyError(message)


def _read_nofollow(root: Path, relative: str) -> tuple[bytes, os.stat_result]:
    if (
        not relative
        or relative.startswith("/")
        or "\x00" in relative
        or any(part in ("", ".", "..") for part in relative.split("/"))
    ):
        _fail(f"unsafe source path: {relative!r}")

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
        parts = relative.split("/")
        for part in parts[:-1]:
            nxt = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=fd,
            )
            os.close(fd)
            fd = nxt
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            before = os.fstat(leaf)
            if (
                not stat.S_ISREG(before.st_mode)
                or stat.S_IMODE(before.st_mode) != 0o644
                or before.st_nlink != 1
                or before.st_size > MAX_SOURCE_BYTES
            ):
                _fail(f"unsafe source custody: {relative}")
            chunks = bytearray()
            while chunk := os.read(leaf, 131_072):
                chunks.extend(chunk)
                if len(chunks) > MAX_SOURCE_BYTES:
                    _fail(f"source exceeds byte ceiling: {relative}")
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
                _fail(f"source changed during capture: {relative}")
            return bytes(chunks), after
        finally:
            os.close(leaf)
    finally:
        os.close(fd)


def _capture_one(
    root: Path, relative: str, expected_bytes: int, expected_sha256: str
) -> BoundSource:
    raw, metadata = _read_nofollow(root, relative)
    digest = hashlib.sha256(raw).hexdigest()
    if len(raw) != expected_bytes or digest != expected_sha256:
        _fail(f"source pin mismatch before execution: {relative}")
    return BoundSource(
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


def _capture_all(root: Path) -> dict[str, BoundSource]:
    captured = tuple(
        _capture_one(root, relative, expected_bytes, expected_sha256)
        for relative, expected_bytes, expected_sha256 in SOURCE_PINS
    )
    if len(captured) != len({item.relative_path for item in captured}):
        _fail("duplicate source pin")
    return {item.relative_path: item for item in captured}


def _verify_captured(captured: Mapping[str, BoundSource]) -> None:
    expected = {
        relative: (expected_bytes, expected_sha256)
        for relative, expected_bytes, expected_sha256 in SOURCE_PINS
    }
    if set(captured) != set(expected):
        _fail("captured source roster mismatch")
    for relative, (expected_bytes, expected_sha256) in expected.items():
        bound = captured[relative]
        if (
            type(bound) is not BoundSource
            or bound.relative_path != relative
            or bound.size != expected_bytes
            or len(bound.raw) != expected_bytes
            or bound.sha256 != expected_sha256
            or hashlib.sha256(bound.raw).hexdigest() != expected_sha256
            or bound.mode != 0o644
            or bound.nlink != 1
        ):
            _fail(f"captured source pin mismatch: {relative}")


def _exec_captured_module(
    bound: BoundSource, root: Path, module_name: str
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


def _compile_modules(
    root: Path, captured: Mapping[str, BoundSource]
) -> tuple[ModuleType, ModuleType, ModuleType, ModuleType]:
    """Compile exact captured buffers only, after a second complete pin check."""

    _verify_captured(captured)
    single = _exec_captured_module(
        captured[SINGLE_PARENT], root, "_two_macrostep_bound_single"
    )
    test29 = _exec_captured_module(
        captured[TEST29_PARENT], root, "_two_macrostep_bound_test29"
    )
    test30 = _exec_captured_module(
        captured[TEST30_PARENT], root, "_two_macrostep_bound_test30"
    )
    candidate = _exec_captured_module(
        captured[CANDIDATE], root, "_two_macrostep_bound_candidate"
    )
    return candidate, single, test29, test30


def validate(root: Path) -> dict[str, Any]:
    root = root.absolute()
    captured_before = _capture_all(root)
    candidate, single, test29, test30 = _compile_modules(root, captured_before)
    result = candidate.run_frozen_two_macrostep_qualification(
        single, test29, test30
    )
    if (
        type(result) is not candidate.FrozenTwoMacrostepQualification
        or result.passed is not True
        or result.predicate != EXPECTED_PREDICATE
        or result.ordered_word_pair_cases_checked != 1_024
        or result.distinct_input_sha256_count != 1_024
        or result.distinct_report_sha256_count != 1_024
        or result.report_sha256 != EXPECTED_REPORT_SHA256
        or result.parent_custody_authenticated is not False
        or result.arbitrary_length_general_strang_path_integrated is not False
        or any(
            value != 0
            for value in (
                result.formal_tests_closed,
                result.fields_closed,
                result.blockers_closed,
                result.result_slots_filled,
                result.tracker_files_edited,
            )
        )
    ):
        _fail("two-macrostep qualification result differs")
    captured_after = _capture_all(root)
    for relative in captured_before:
        if (
            captured_before[relative].identity()
            != captured_after[relative].identity()
        ):
            _fail(f"source identity changed across qualification: {relative}")
    return {
        "status": "PASS",
        "schema_version": SCHEMA_VERSION,
        "predicate": EXPECTED_PREDICATE,
        "report_sha256": result.report_sha256,
        "ordered_word_pair_cases_checked": result.ordered_word_pair_cases_checked,
        "candidate_report_parent_custody_authenticated": False,
        "envelope_parent_source_custody_authenticated": True,
        "compiled_from_captured_bytes_only": True,
        "source_identities_stable": True,
        "source_count": len(captured_before),
        "formal_tests_closed": 0,
        "fields_closed": 0,
        "blockers_closed": 0,
        "result_slots_filled": 0,
        "tracker_files_edited": 0,
        "source_receipts": [
            captured_before[relative].receipt()
            for relative, _size, _digest in SOURCE_PINS
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
    except (ParentCustodyError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
