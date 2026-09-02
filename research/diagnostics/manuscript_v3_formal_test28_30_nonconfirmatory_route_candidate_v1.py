#!/usr/bin/env python3
"""Hash-first validator for the nonconfirmatory Test-28--30 route."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from types import ModuleType
from typing import Dict, Tuple


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = (
    "heterodiff-formal-test28-30-nonconfirmatory-route-candidate-v1"
)
ROUTE_SCHEMA_VERSION = "heterodiff-formal-test28-30-nonconfirmatory-route-v1"
STATE = "NONCONFIRMATORY_SYNTHETIC_TEST28_30_ROUTES_JOINTLY_BOUND"
TASK_TEXT = (
    "Required Tests 28\u201330 routes run end to end on "
    "nonconfirmatory/synthetic inputs."
)
MACHINE_REL = (
    "research/fixtures/"
    "manuscript_v3_formal_test28_30_nonconfirmatory_route_candidate_v1.json"
)
SOURCE_REL = (
    "src/heterodiff/evaluation/formal_test28_30_nonconfirmatory_route.py"
)
HUMAN_REL = "PROJECT_FORMAL_TEST28_30_NONCONFIRMATORY_ROUTE_CANDIDATE.md"
TEST_REL = "tests/unit/test_formal_test28_30_nonconfirmatory_route.py"
VALIDATOR_REL = (
    "research/diagnostics/"
    "manuscript_v3_formal_test28_30_nonconfirmatory_route_candidate_v1.py"
)
ZERO_SHA256 = "0" * 64
MAX_FILE_BYTES = 10_000_000
MACHINE_DOMAIN = SCHEMA_VERSION.encode("ascii") + b"\0"

# Final exact values are inserted only after the route and whole-method lanes seal.
EXPECTED_MACHINE_BYTES = 8_841
EXPECTED_MACHINE_SHA256 = (
    "971f337f7e01be99372a7308c4036551c3660b11bb3d9a7a70487e88146cffe2"
)
EXPECTED_MACHINE_RECORD_SHA256 = (
    "96e3b976603a42f559846e1b611ba410c6eea02d9e5c44c3e5de6f68d0360491"
)
EXPECTED_ROUTE_RECEIPT_SHA256 = (
    "f26767444a3df2d5e7d353cf3930e806412902d6e837134a9f6dc821663740a8"
)
EXPECTED_STATIC_BINDINGS = (
    (
        "human",
        HUMAN_REL,
        8_266,
        "0bb2337e2100f9e8efdd5948d6655f382103514b2f11871ead1e2c9eef3ce5f6",
    ),
    (
        "route_source",
        SOURCE_REL,
        41_184,
        "aabbea24156c63d833beaa7fe1a29d2c4879a8a0cbd0d171ec0ca558d3a34a32",
    ),
    (
        "focused_tests",
        TEST_REL,
        16_290,
        "22b044a949f6c622eb5ec76a30a1ab5585ad410559a096d216e056c4c4c43425",
    ),
)
EXPECTED_PREDECESSOR_BINDINGS = (
    (
        "cp63_fixture",
        "research/fixtures/cp50_test28_mixed_initializer_v26.json",
        7_087_027,
        "7faed3c5b07415fbc45fec02d026e36d465819a38e9187369bf0a42a91c29f68",
    ),
    (
        "cp63_runner",
        "src/heterodiff/evaluation/"
        "mixed_initializer_test28_runner_recomputation_rehearsal.py",
        83_080,
        "27259edf2557a21b2527595eed7a954fc697755935e4a3deaeeb169765ba1c9c",
    ),
    (
        "cp63_independent_recomputation",
        "src/heterodiff/evaluation/"
        "mixed_initializer_test28_independent_recomputation.py",
        94_515,
        "5df076a008d8fe6848dc72083e2563e622c136ce0159441dd69db04c3b1cb9dc",
    ),
    (
        "test29_test30_hash_first_wrapper",
        "research/diagnostics/"
        "formal_test29_test30_two_macrostep_parent_custody_hash_first_v1.py",
        12_105,
        "e71f145bc73b47a8d6a19329e05989523d0ca14d5726c4b02a8ec0e07f9a455e",
    ),
    (
        "whole_method_machine",
        "research/fixtures/"
        "manuscript_v3_b12_whole_method_nonconfirmatory_runner_v1.json",
        9_789,
        "a5debbc0db537993191c1554529fdf52e34ace80a92cb24a3555889a11f0490b",
    ),
)


class ValidationError(RuntimeError):
    """Raised before unpinned package bytes can be trusted or executed."""


def _fail(message: str) -> None:
    raise ValidationError(message)


def _sha256(raw: bytes) -> str:
    if type(raw) is not bytes:
        raise TypeError("digest input must be exact bytes")
    return hashlib.sha256(raw).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _canonical_relative(value: object) -> PurePosixPath:
    if (
        type(value) is not str
        or not value
        or not value.isascii()
        or "\\" in value
        or "\x00" in value
    ):
        _fail("path must be exact nonempty ASCII POSIX text")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in ("", ".", "..") for part in value.split("/"))
    ):
        _fail("path is noncanonical or escapes the project root")
    return path


def _identity(value: os.stat_result) -> Tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_uid,
        value.st_gid,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _read_stable_regular(relative: str) -> Tuple[bytes, Tuple[int, ...]]:
    path = _canonical_relative(relative)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    root_fd = os.open(str(ROOT), flags)
    opened = []
    try:
        before_root = os.fstat(root_fd)
        current = root_fd
        for part in path.parts[:-1]:
            descriptor = os.open(part, flags, dir_fd=current)
            opened.append(descriptor)
            current = descriptor
        leaf = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=current)
        opened.append(leaf)
        before = os.fstat(leaf)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o644
            or before.st_nlink != 1
            or not 1 <= before.st_size <= MAX_FILE_BYTES
        ):
            _fail("file custody differs: " + relative)
        chunks = bytearray()
        while True:
            chunk = os.read(leaf, min(131_072, before.st_size + 1 - len(chunks)))
            if not chunk:
                break
            chunks.extend(chunk)
            if len(chunks) > before.st_size:
                _fail("file grew during capture: " + relative)
        after = os.fstat(leaf)
        after_root = os.fstat(root_fd)
        if (
            len(chunks) != before.st_size
            or _identity(before) != _identity(after)
            or _identity(before_root) != _identity(after_root)
        ):
            _fail("file or root changed during capture: " + relative)
        return bytes(chunks), _identity(after)
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)
        os.close(root_fd)


def _capture_binding(
    role: str, relative: str, expected_bytes: int, expected_sha256: str
) -> Tuple[str, str, int, str, bytes, Tuple[int, ...]]:
    if (
        type(role) is not str
        or not role
        or type(expected_bytes) is not int
        or expected_bytes <= 0
        or type(expected_sha256) is not str
        or len(expected_sha256) != 64
        or expected_sha256 == ZERO_SHA256
    ):
        _fail("unsealed expected binding: " + role)
    raw, identity = _read_stable_regular(relative)
    digest = _sha256(raw)
    if len(raw) != expected_bytes or digest != expected_sha256:
        _fail("file pin mismatch before use: " + relative)
    return role, relative, len(raw), digest, raw, identity


def _capture_roster(
    roster: Tuple[Tuple[str, str, int, str], ...]
) -> Dict[str, Tuple[str, str, int, str, bytes, Tuple[int, ...]]]:
    if type(roster) is not tuple or not roster:
        _fail("binding roster differs")
    captured = tuple(_capture_binding(*item) for item in roster)
    if len(captured) != len({item[0] for item in captured}):
        _fail("duplicate binding role")
    return {item[0]: item for item in captured}


def _verify_stable_reopen(
    before: Dict[str, Tuple[str, str, int, str, bytes, Tuple[int, ...]]],
    roster: Tuple[Tuple[str, str, int, str], ...],
) -> None:
    after = _capture_roster(roster)
    if set(before) != set(after):
        _fail("binding role set changed")
    for role in before:
        if before[role][0:4] != after[role][0:4] or before[role][5] != after[role][5]:
            _fail("binding identity changed across validation: " + role)


def _pairs_hook(pairs: object) -> Dict[str, object]:
    if type(pairs) is not list:
        _fail("JSON pair carrier differs")
    result: Dict[str, object] = {}
    for pair in pairs:
        if type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str:
            _fail("JSON key differs")
        key, value = pair
        if key in result:
            _fail("duplicate JSON key: " + key)
        result[key] = value
    return result


def _reject_float(value: str) -> None:
    _fail("machine JSON contains a floating-point value: " + value)


def _reject_constant(value: str) -> None:
    _fail("machine JSON contains a non-finite value: " + value)


def _decode_machine(raw: bytes) -> Dict[str, object]:
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        _fail("machine receipt must have exactly one terminal LF")
    try:
        text = raw[:-1].decode("ascii", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_pairs_hook,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError("machine receipt is not strict canonical JSON") from exc
    if type(value) is not dict or _canonical_bytes(value) + b"\n" != raw:
        _fail("machine receipt is not canonical JSON")
    return value


def _execute_captured_route_source(
    captured: Tuple[str, str, int, str, bytes, Tuple[int, ...]]
) -> Dict[str, object]:
    role, relative, byte_count, digest, raw, _identity_value = captured
    expected = {item[0]: item for item in EXPECTED_STATIC_BINDINGS}["route_source"]
    if (
        role != "route_source"
        or (relative, byte_count, digest) != expected[1:]
        or len(raw) != byte_count
        or _sha256(raw) != digest
    ):
        _fail("captured route source differs immediately before compile")
    module_name = "_bound_formal_test28_30_nonconfirmatory_route"
    module = ModuleType(module_name)
    module.__file__ = str(ROOT / relative)
    module.__package__ = ""
    missing = object()
    previous = sys.modules.get(module_name, missing)
    sys.modules[module_name] = module
    try:
        exec(
            compile(raw, module.__file__, "exec", dont_inherit=True),
            module.__dict__,
        )
        runner = module.__dict__.get("run_nonconfirmatory_test28_30_route")
        serializer = module.__dict__.get("route_receipt_canonical_json_bytes")
        if type(runner).__name__ != "function" or type(serializer).__name__ != "function":
            _fail("captured route public entrypoints differ")
        receipt = runner(str(ROOT))
        receipt_raw = serializer(receipt)
    finally:
        if previous is missing:
            del sys.modules[module_name]
        else:
            sys.modules[module_name] = previous
    if type(receipt_raw) is not bytes or not receipt_raw.endswith(b"\n"):
        _fail("route receipt serialization differs")
    value = json.loads(
        receipt_raw[:-1].decode("ascii"), object_pairs_hook=_pairs_hook
    )
    if type(value) is not dict or _canonical_bytes(value) + b"\n" != receipt_raw:
        _fail("route receipt is not canonical")
    return value


def _expected_execution_matrix(route_receipt: Dict[str, object]) -> list:
    cp63 = route_receipt["cp63_test28"]
    two = route_receipt["test29_test30_two_macrostep"]
    whole = route_receipt["whole_method"]
    return [
        {
            "case_count": cp63["row_count"],
            "component_id": route_receipt["route_component_ids"][0],
            "execution_mode": "HISTORICAL_ACCEPTED_NONCONFIRMATORY_RECEIPT_REVALIDATED",
            "fresh_execution_in_route_process": False,
            "repetition_count": cp63["repetitions_per_row"],
            "stable_receipt_sha256": cp63["acceptance_receipt_sha256"],
        },
        {
            "case_count": two["ordered_word_pair_cases_checked"],
            "component_id": route_receipt["route_component_ids"][1],
            "execution_mode": "FRESH_HASH_FIRST_SUPPLIED_INPUT_EXECUTION",
            "fresh_execution_in_route_process": True,
            "report_sha256": two["report_sha256"],
        },
        {
            "implementation_obligation_count": whole[
                "implementation_obligation_count"
            ],
            "component_id": route_receipt["route_component_ids"][2],
            "execution_mode": "SEPARATELY_EXECUTED_STABLE_RECEIPT_REVALIDATED",
            "fresh_execution_in_route_process": False,
            "stable_receipt_sha256": whole["receipt_sha256"],
        },
    ]


def _validate_machine_semantics(
    machine: Dict[str, object], route_receipt: Dict[str, object]
) -> None:
    expected_keys = {
        "schema_version",
        "state",
        "scope",
        "route_receipt",
        "execution_matrix",
        "proposed_timetable_delta",
        "effect_projection",
        "artifact_bindings",
        "predecessor_bindings",
        "residuals",
        "record_sha256",
    }
    if set(machine) != expected_keys:
        _fail("machine top-level key roster differs")
    supplied_record_sha256 = machine.get("record_sha256")
    if (
        type(supplied_record_sha256) is not str
        or len(supplied_record_sha256) != 64
        or supplied_record_sha256 == ZERO_SHA256
    ):
        _fail("machine record digest differs")
    unsigned = dict(machine)
    unsigned["record_sha256"] = ZERO_SHA256
    if _sha256(MACHINE_DOMAIN + _canonical_bytes(unsigned)) != supplied_record_sha256:
        _fail("machine self digest differs")
    if (
        machine["schema_version"] != SCHEMA_VERSION
        or machine["state"] != STATE
        or machine["scope"]
        != "OFFLINE_LOCAL_NONCONFIRMATORY_SYNTHETIC_ROUTE_QUALIFICATION_ONLY"
        or machine["route_receipt"] != route_receipt
        or route_receipt.get("schema_version") != ROUTE_SCHEMA_VERSION
        or route_receipt.get("receipt_sha256") != EXPECTED_ROUTE_RECEIPT_SHA256
        or route_receipt.get("route_components_jointly_bound") is not True
        or machine["execution_matrix"] != _expected_execution_matrix(route_receipt)
    ):
        _fail("machine route semantics differ")
    if machine["proposed_timetable_delta"] != {
        "applied_closure_count": 0,
        "proposed_closure_count": 1,
        "task_text": TASK_TEXT,
    }:
        _fail("proposed timetable delta differs")
    if machine["effect_projection"] != {
        "authority_asserted": False,
        "b12_closed": False,
        "blockers_closed": 0,
        "data_contacted": False,
        "entropy_consumed": False,
        "fields_closed": 0,
        "formal_test_28_state": "OPEN",
        "formal_test_29_state": "OPEN",
        "formal_test_30_state": "PENDING",
        "formal_tests_closed": 0,
        "network_contacted": False,
        "production_receipt_issued": False,
        "result_slots_filled": 0,
        "runtime_selected": False,
        "science_executed": False,
        "tracker_or_ledger_edited": False,
    }:
        _fail("machine effect projection differs")
    expected_artifacts = {
        role: {"bytes": size, "path": path, "sha256": digest}
        for role, path, size, digest in EXPECTED_STATIC_BINDINGS
    }
    expected_predecessors = {
        role: {"bytes": size, "path": path, "sha256": digest}
        for role, path, size, digest in EXPECTED_PREDECESSOR_BINDINGS
    }
    if (
        machine["artifact_bindings"] != expected_artifacts
        or machine["predecessor_bindings"] != expected_predecessors
    ):
        _fail("machine file bindings differ")
    if machine["residuals"] != [
        "Formal Test 28 remains OPEN; no production campaign, estimates, intervals, or decision.",
        "Formal Test 29 remains OPEN; continuous production realization and its decision predicate remain absent.",
        "Formal Test 30 remains PENDING; production coupled-path criteria and independent production evidence remain absent.",
        "B12, every field and blocker, all result slots, runtime selection, data contact, science, claims, and tracker/ledger mutation remain unchanged.",
    ]:
        _fail("machine residual roster differs")


def validate() -> Dict[str, object]:
    if (
        EXPECTED_MACHINE_BYTES <= 0
        or EXPECTED_MACHINE_SHA256 == ZERO_SHA256
        or EXPECTED_MACHINE_RECORD_SHA256 == ZERO_SHA256
        or EXPECTED_ROUTE_RECEIPT_SHA256 == ZERO_SHA256
    ):
        _fail("route package is not sealed")
    static_before = _capture_roster(EXPECTED_STATIC_BINDINGS)
    predecessor_before = _capture_roster(EXPECTED_PREDECESSOR_BINDINGS)
    machine_raw, machine_identity = _read_stable_regular(MACHINE_REL)
    if (
        len(machine_raw) != EXPECTED_MACHINE_BYTES
        or _sha256(machine_raw) != EXPECTED_MACHINE_SHA256
    ):
        _fail("machine raw pin differs")
    machine = _decode_machine(machine_raw)
    route_receipt = _execute_captured_route_source(static_before["route_source"])
    _validate_machine_semantics(machine, route_receipt)
    if machine["record_sha256"] != EXPECTED_MACHINE_RECORD_SHA256:
        _fail("machine semantic record pin differs")
    machine_after, machine_identity_after = _read_stable_regular(MACHINE_REL)
    if machine_raw != machine_after or machine_identity != machine_identity_after:
        _fail("machine identity changed across validation")
    _verify_stable_reopen(static_before, EXPECTED_STATIC_BINDINGS)
    _verify_stable_reopen(predecessor_before, EXPECTED_PREDECESSOR_BINDINGS)
    return {
        "status": "PASS",
        "schema_version": SCHEMA_VERSION,
        "state": STATE,
        "machine_record_sha256": machine["record_sha256"],
        "route_receipt_sha256": route_receipt["receipt_sha256"],
        "route_component_count": len(route_receipt["route_component_ids"]),
        "test28_state": "OPEN",
        "test29_state": "OPEN",
        "test30_state": "PENDING",
        "formal_tests_closed": 0,
        "fields_closed": 0,
        "blockers_closed": 0,
        "result_slots_filled": 0,
        "applied_timetable_task_closures": 0,
        "proposed_timetable_task_closures": 1,
        "tracker_or_ledger_edited": False,
    }


def main() -> int:
    try:
        result = validate()
    except (ValidationError, OSError, TypeError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
