#!/usr/bin/env python3
"""Hash-first validator for the additive Test-28--30 route V2 successor."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import threading
from types import ModuleType
from typing import Dict, Tuple


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "heterodiff-formal-test28-30-nonconfirmatory-route-v2-successor-record-v1"
RECORD_DOMAIN = SCHEMA.encode("ascii") + b"\0"
MACHINE = "research/fixtures/manuscript_v3_formal_test28_30_nonconfirmatory_route_v2_successor.json"
SOURCE = "src/heterodiff/evaluation/formal_test28_30_nonconfirmatory_route_v2.py"
HUMAN = "PROJECT_FORMAL_TEST28_30_NONCONFIRMATORY_ROUTE_V2_SUCCESSOR.md"
TEST = "tests/unit/test_formal_test28_30_nonconfirmatory_route_v2.py"
TASK = "Required Tests 28\u201330 routes run end to end on nonconfirmatory/synthetic inputs."
MACHINE_BYTES = 2_495
MACHINE_SHA256 = "0a0c67721ca8cfa5e916389787f7b4672e9a38790e81ab19f842f687e02332cf"
MACHINE_RECORD_SHA256 = "39a0cb5b95bf81759f704128989404d424f019188876648ec5be28279a6e9378"
ROUTE_RECEIPT_SHA256 = "eab918f4aa9a58f56466673f5e8bcaefb6180692acbdfd9a6e6a694c2a3b6c4f"
ROUTE_SUBJECT_SHA256 = "a1fb05402feb3efbf7a413e36e3eafc6528ec811ce9768d2bf49332e57d67a03"
STATIC = (
    ("human", HUMAN, 6_735, "fd7a2a5db5e34f25e5be45d606aa5c4153e8a80059d71593588e7e4a0b3c04dd"),
    ("route_source", SOURCE, 37_060, "ffbe30e00629e2fab14148c5c8593604eaccf5c9b22d75cf8566ab21868f72fa"),
    ("focused_tests", TEST, 21_469, "2568810b0c03a96ebf98b0422598ff11b8643886bbbe599cd8bc44826f49f7c3"),
)
PREDECESSORS = (
    ("rejected_v1_route_source", "src/heterodiff/evaluation/formal_test28_30_nonconfirmatory_route.py", 41_184, "aabbea24156c63d833beaa7fe1a29d2c4879a8a0cbd0d171ec0ca558d3a34a32"),
    ("repaired_whole_machine", "research/fixtures/manuscript_v3_b12_whole_method_initializer_path_integration_successor_v1.json", 30_010, "e247add0ef427cfd2c77f27a9347c28bc0b70df8bb53b803864619d27d1e7ea8"),
    ("repaired_whole_review", "PROJECT_B12_WHOLE_METHOD_INITIALIZER_PATH_INTEGRATION_SUCCESSOR_INDEPENDENT_REVIEW.md", 11_076, "e24f2e97a67048323170b44d6e537ab07c3a7a6692cf682bc3053c1165732765"),
)
_VALIDATOR_EXECUTION_LOCK = threading.RLock()


class ValidationError(RuntimeError):
    pass


def _fail(message: str) -> None:
    raise ValidationError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def _pairs(pairs: object) -> Dict[str, object]:
    if type(pairs) is not list:
        _fail("JSON pair carrier differs")
    result: Dict[str, object] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            _fail("duplicate or non-text JSON key")
        result[key] = value
    return result


def _relative(value: object) -> str:
    if type(value) is not str or not value or "\0" in value or "\\" in value:
        _fail("relative path differs")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(part in ("", ".", "..") for part in value.split("/")):
        _fail("relative path is noncanonical")
    return value


def _root(value: object) -> Path:
    if type(value) is not str:
        raise TypeError("root must be exact text")
    result = Path(value)
    if (
        not result.is_absolute() or str(result) != value
        or result.as_posix() != value or result.resolve(strict=True) != result
    ):
        _fail("root differs")
    return result


def _identity(meta: os.stat_result) -> Tuple[int, ...]:
    return (meta.st_dev, meta.st_ino, meta.st_uid, meta.st_gid, meta.st_mode, meta.st_nlink, meta.st_size, meta.st_mtime_ns, meta.st_ctime_ns)


def _capture(root: Path, relative: str, size: int, digest: str) -> Tuple[bytes, Tuple[int, ...]]:
    _relative(relative)
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    root_fd = os.open("/", flags)
    fd = root_fd
    opened = []
    try:
        for part in root.parts[1:] + tuple(relative.split("/"))[:-1]:
            fd = os.open(part, flags, dir_fd=fd)
            opened.append(fd)
        leaf = os.open(relative.split("/")[-1], os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=fd)
        opened.append(leaf)
        before = os.fstat(leaf)
        if not stat.S_ISREG(before.st_mode) or stat.S_IMODE(before.st_mode) != 0o644 or before.st_nlink != 1 or before.st_size != size:
            _fail("file custody differs: " + relative)
        raw = b""
        while len(raw) <= size:
            block = os.read(leaf, min(131_072, size + 1 - len(raw)))
            if not block:
                break
            raw += block
        if len(raw) != size or _sha(raw) != digest or _identity(before) != _identity(os.fstat(leaf)):
            _fail("file bytes or identity differ: " + relative)
        return raw, _identity(before)
    finally:
        for item in reversed(opened):
            os.close(item)
        os.close(root_fd)


def _machine(root: Path) -> Tuple[Dict[str, object], Tuple[int, ...]]:
    raw, identity = _capture(root, MACHINE, MACHINE_BYTES, MACHINE_SHA256)
    if not raw.endswith(b"\n"):
        _fail("machine terminal LF differs")
    try:
        document = json.loads(raw[:-1].decode("ascii"), object_pairs_hook=_pairs)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError("machine is not strict JSON") from exc
    if type(document) is not dict or _canonical(document) + b"\n" != raw:
        _fail("machine is not canonical")
    supplied = document.get("record_sha256")
    unsigned = dict(document)
    unsigned.pop("record_sha256", None)
    if supplied != MACHINE_RECORD_SHA256 or _sha(RECORD_DOMAIN + _canonical(unsigned)) != MACHINE_RECORD_SHA256:
        _fail("machine self-record differs")
    return document, identity


def _load_route(root: Path) -> ModuleType:
    raw, _ = _capture(root, SOURCE, STATIC[1][2], STATIC[1][3])
    name = "_formal_test28_30_route_v2_validator_bound_source"
    missing = object()
    prior = sys.modules.get(name, missing)
    module = ModuleType(name)
    module.__file__ = str(root / SOURCE)
    module.__package__ = ""
    try:
        sys.modules[name] = module
        exec(compile(raw, module.__file__, "exec", dont_inherit=True), module.__dict__)
        return module
    finally:
        if prior is missing:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prior


def validate(root: object = str(ROOT)) -> Dict[str, object]:
    root = _root(root)
    before = {}
    for role, path, size, digest in STATIC + PREDECESSORS:
        raw, identity = _capture(root, path, size, digest)
        before[path] = identity
    document, machine_before = _machine(root)
    expected_artifacts = {
        role: {"bytes": size, "path": path, "sha256": digest}
        for role, path, size, digest in STATIC
    }
    expected_predecessors = {
        role: {"bytes": size, "path": path, "sha256": digest}
        for role, path, size, digest in PREDECESSORS
    }
    if document.get("artifact_bindings") != expected_artifacts or document.get("predecessor_bindings") != expected_predecessors:
        _fail("machine binding roster differs")
    with _VALIDATOR_EXECUTION_LOCK:
        module = _load_route(root)
        callback = module.__dict__.get("run_nonconfirmatory_test28_30_route_v2")
        serializer = module.__dict__.get("route_v2_receipt_canonical_json_bytes")
        if type(callback).__name__ != "function" or type(serializer).__name__ != "function":
            _fail("route entrypoint differs")
        receipt = callback(str(root))
        receipt_bytes = serializer(receipt)
    route_record = document.get("route_receipt")
    if type(route_record) is not dict or route_record != {
        "canonical_bytes": 6513,
        "receipt_sha256": ROUTE_RECEIPT_SHA256,
        "route_subject_sha256": ROUTE_SUBJECT_SHA256,
        "schema_version": "heterodiff-formal-test28-30-nonconfirmatory-route-v2",
        "state": "NONCONFIRMATORY_SYNTHETIC_TEST28_30_REPAIRED_ROUTES_JOINTLY_BOUND",
    }:
        _fail("route receipt machine projection differs")
    if len(receipt_bytes) != 6513 or receipt.receipt_sha256 != ROUTE_RECEIPT_SHA256 or receipt.route_subject_sha256 != ROUTE_SUBJECT_SHA256:
        _fail("executed route receipt differs")
    if document.get("effects") != {
        "applied_timetable_task_closures": 0, "blockers_closed": 0,
        "data_contacted": False, "fields_closed": 0, "formal_tests_closed": 0,
        "network_contacted": False, "result_slots_filled": 0,
        "science_executed": False, "tracker_or_ledger_edited": False,
    } or document.get("proposed_timetable_delta") != {"applied": 0, "proposed": 1, "task": TASK}:
        _fail("machine scope/effect projection differs")
    if document.get("execution_matrix") != {
        "cp63_estimands": 554, "cp63_fresh_execution": False,
        "cp63_launches": 32, "cp63_repetitions_per_row": 2, "cp63_rows": 16,
        "focused_tests_passed": 69, "test29_test30_fresh_cases": 1024,
        "whole_method_independent_go": True,
    }:
        _fail("machine execution matrix differs")
    for _, path, size, digest in STATIC + PREDECESSORS:
        _, after = _capture(root, path, size, digest)
        if after != before[path]:
            _fail("binding identity changed: " + path)
    _, machine_after = _capture(root, MACHINE, MACHINE_BYTES, MACHINE_SHA256)
    if machine_after != machine_before:
        _fail("machine identity changed across full validation")
    return {
        "status": "PASS",
        "record_sha256": MACHINE_RECORD_SHA256,
        "receipt_sha256": ROUTE_RECEIPT_SHA256,
        "route_subject_sha256": ROUTE_SUBJECT_SHA256,
        "formal_test_states": ["OPEN", "OPEN", "PENDING"],
        "proposed_timetable_task_closures": 1,
        "applied_timetable_task_closures": 0,
        "tracker_or_ledger_edited": False,
    }


def main() -> int:
    result = validate()
    print("PASS_FORMAL_TEST28_30_ROUTE_V2_SUCCESSOR — record %s; receipt %s" % (result["record_sha256"], result["receipt_sha256"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, OSError, TypeError, ValueError) as exc:
        print("FAIL_FORMAL_TEST28_30_ROUTE_V2_SUCCESSOR — " + str(exc), file=sys.stderr)
        raise SystemExit(1)
