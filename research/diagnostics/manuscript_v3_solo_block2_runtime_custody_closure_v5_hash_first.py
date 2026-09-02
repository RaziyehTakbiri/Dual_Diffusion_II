#!/usr/bin/env python3
"""Hash-first verification envelope for the accepted Solo Block 2 V5 package.

The accepted V5 validator dynamically evaluates its exact V4 predecessor, and
that exact V4 validator dynamically evaluates V3.  This envelope is the only
supported trust entrypoint for that chain: it captures and byte-pins all three
validators before evaluating any of them, evaluates only the captured bytes,
replaces both inherited dynamic loaders with captured-namespace loaders, runs
the V5 validation, and then proves that every validator identity stayed fixed.

It is read-only.  It never imports or invokes the V5 production executor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = (
    "heterodiff-manuscript-v3-solo-block2-runtime-custody-closure-"
    "v5-hash-first-remediation-v1"
)

V5_VALIDATOR = (
    "research/diagnostics/"
    "manuscript_v3_solo_block2_runtime_custody_closure_v5.py"
)
V4_VALIDATOR = (
    "research/diagnostics/"
    "manuscript_v3_solo_block2_runtime_custody_closure_v4.py"
)
V3_VALIDATOR = (
    "research/diagnostics/"
    "manuscript_v3_solo_block2_runtime_custody_closure_v3.py"
)

# The order is deliberately newest-to-oldest for capture.  No source is
# compiled until the entire tuple has been captured and verified.
VALIDATOR_PINS: tuple[tuple[str, int, str], ...] = (
    (
        V5_VALIDATOR,
        23_872,
        "4699e3073ec19b3f82320b70f29d4b9a63169622a9ed042a30262c3fe7d01c96",
    ),
    (
        V4_VALIDATOR,
        20_334,
        "bc32e4775a6ea1ac557bafc66a27411f5cddfeb79e4daa0bd4dfc09e89af7a44",
    ),
    (
        V3_VALIDATOR,
        36_357,
        "53fb7a3afb8f0cf798e9d0cd0970fe370f5e2c0a7ed72bef0ce5c9f414de1153",
    ),
)

MAX_VALIDATOR_BYTES = 1_048_576


class HashFirstValidationError(RuntimeError):
    """Raised before untrusted or unstable validator bytes can execute."""


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
    raise HashFirstValidationError(message)


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
    # Tuple evaluation completes every read and pin comparison before this
    # function returns and before _compile_chain can be called.
    captured = tuple(
        _capture_one(root, relative, expected_bytes, expected_sha256)
        for relative, expected_bytes, expected_sha256 in VALIDATOR_PINS
    )
    if len(captured) != len({item.relative_path for item in captured}):
        _fail("duplicate validator pin")
    return {item.relative_path: item for item in captured}


def _exec_captured(
    bound: BoundValidator, root: Path, namespace_name: str
) -> dict[str, Any]:
    filename = str(root.absolute() / bound.relative_path)
    namespace: dict[str, Any] = {
        "__name__": namespace_name,
        "__file__": filename,
    }
    exec(compile(bound.raw, filename, "exec", dont_inherit=True), namespace)
    return namespace


def _same_root(requested: Path, captured_root: Path) -> None:
    if requested.absolute() != captured_root.absolute():
        _fail("inherited validator requested a different root")


def _compile_chain(
    root: Path, captured: Mapping[str, BoundValidator]
) -> dict[str, Any]:
    """Compile only captured bytes and replace both inherited disk loaders."""

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
    captured_root = root.absolute()

    v3 = _exec_captured(captured[V3_VALIDATOR], captured_root, "_v5hf_bound_v3")
    v4 = _exec_captured(captured[V4_VALIDATOR], captured_root, "_v5hf_bound_v4")

    def _captured_v3_loader(requested_root: Path) -> dict[str, Any]:
        _same_root(requested_root, captured_root)
        return v3

    v4["_load_v3_validator"] = _captured_v3_loader
    v5 = _exec_captured(captured[V5_VALIDATOR], captured_root, "_v5hf_bound_v5")

    def _captured_v4_loader(requested_root: Path) -> dict[str, Any]:
        _same_root(requested_root, captured_root)
        return v4

    v5["_load_v4_validator"] = _captured_v4_loader
    return v5


def validate(root: Path) -> dict[str, Any]:
    root = root.absolute()
    captured_before = _capture_all(root)
    v5 = _compile_chain(root, captured_before)
    result = v5["validate"](root)
    if type(result) is not dict or result.get("status") != "PASS":
        _fail("wrapped V5 validation did not pass")
    captured_after = _capture_all(root)
    for relative in captured_before:
        if (
            captured_before[relative].identity()
            != captured_after[relative].identity()
        ):
            _fail(f"validator identity changed across validation: {relative}")
    return {
        "status": "PASS",
        "schema_version": SCHEMA_VERSION,
        "wrapped_v5_status": result["status"],
        "validator_count": len(captured_before),
        "compiled_from_captured_bytes_only": True,
        "inherited_disk_loaders_replaced": True,
        "validator_identities_stable": True,
        "network_actions": 0,
        "operational_receipts": 0,
        "activated_budget": 0,
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
    except (HashFirstValidationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
