"""Hash-bound nonconfirmatory route across Formal Tests 28--30.

This module composes three already bounded development surfaces:

* the accepted CP63 sixteen-row, two-repetition Test-28 rehearsal and its
  source-independent 554-estimand recomputation receipt;
* a fresh invocation of the accepted hash-first Test-29/Test-30
  two-macrostep parent-custody wrapper; and
* the separately generated whole-method supplied-input synthetic receipt.

The route is project-control evidence only.  It consumes no entropy, network,
external data, runtime identity, or authority.  Formal Tests 28 and 29 remain
OPEN, Formal Test 30 remains PENDING, and no B12, field, blocker, result,
runtime, data, production, scientific, or manuscript-claim state changes.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
import decimal
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from types import ModuleType
from typing import Dict, Tuple


SCHEMA_VERSION = "heterodiff-formal-test28-30-nonconfirmatory-route-v1"
RECEIPT_DOMAIN = b"heterodiff-formal-test28-30-nonconfirmatory-route-v1\0"
STATE = "NONCONFIRMATORY_SYNTHETIC_TEST28_30_ROUTES_JOINTLY_BOUND"
PROPOSED_TIMETABLE_TASK = (
    "Required Tests 28\u201330 routes run end to end on "
    "nonconfirmatory/synthetic inputs."
)

CP63_FIXTURE_PATH = "research/fixtures/cp50_test28_mixed_initializer_v26.json"
CP63_FIXTURE_BYTES = 7_087_027
CP63_FIXTURE_SHA256 = (
    "7faed3c5b07415fbc45fec02d026e36d465819a38e9187369bf0a42a91c29f68"
)
CP63_RUNNER_PATH = (
    "src/heterodiff/evaluation/"
    "mixed_initializer_test28_runner_recomputation_rehearsal.py"
)
CP63_RUNNER_BYTES = 83_080
CP63_RUNNER_SHA256 = (
    "27259edf2557a21b2527595eed7a954fc697755935e4a3deaeeb169765ba1c9c"
)
CP63_INDEPENDENT_PATH = (
    "src/heterodiff/evaluation/"
    "mixed_initializer_test28_independent_recomputation.py"
)
CP63_INDEPENDENT_BYTES = 94_515
CP63_INDEPENDENT_SHA256 = (
    "5df076a008d8fe6848dc72083e2563e622c136ce0159441dd69db04c3b1cb9dc"
)
CP63_ACCEPTANCE_SHA256 = (
    "2b2f41f14424ddb164b6db793991ece8b222a4e4295d7e0143c6b6496c50097b"
)
CP63_ACCEPTANCE_CANONICAL_BYTES = 24_810
CP63_ACCEPTANCE_CANONICAL_PLAIN_SHA256 = (
    "83113460c4a4963ea815a2c54b9f1f7a8e2c1fbe7d4698fbb56a0f7addc1cf4d"
)
CP63_SEMANTIC_PIN_SHA256 = (
    "d7dfdae440b3b26b289279ccdda6e665fe43fee965c0836fe1d6dac91ce8d5e7"
)
CP63_RECOMPUTATION_RECORD_SHA256 = (
    "870b89d2252dd5e62fc0c10982d5d2f194402b2a941c4c7bd8a0b6214a2832dc"
)
CP63_RECOMPUTATION_PUBLIC_SHA256 = (
    "895b3afbe514158fdfbc3c3d2ae67175cdab2a5834cbf25b00297e69aa179406"
)
CP63_RECOMPUTATION_CANONICAL_PLAIN_SHA256 = (
    "4c281147b68adc5a83ddd88bab73c42cef619498a13a7f234acb4cd886a40ee7"
)

TWO_MACROSTEP_WRAPPER_PATH = (
    "research/diagnostics/"
    "formal_test29_test30_two_macrostep_parent_custody_hash_first_v1.py"
)
TWO_MACROSTEP_WRAPPER_BYTES = 12_105
TWO_MACROSTEP_WRAPPER_SHA256 = (
    "e71f145bc73b47a8d6a19329e05989523d0ca14d5726c4b02a8ec0e07f9a455e"
)
TWO_MACROSTEP_PREDICATE = (
    "SYNTHETIC_SUPPLIED_INPUT_TWO_MACROSTEP_ROLLING_LINEAGE_PATH_VALIDATED"
)
TWO_MACROSTEP_REPORT_SHA256 = (
    "2a278585373d017b3b60bed28dcbc0ab3830f72c0512891658fc2ab54c666d53"
)
TWO_MACROSTEP_PARENT_PINS = (
    (
        "src/heterodiff/evaluation/"
        "formal_test29_test30_two_macrostep_path_qualification.py",
        59_285,
        "d1c3013aa0f4e7b31e19cef98d4aa5edf7991c5b8634dbfe091f8053b1808176",
    ),
    (
        "src/heterodiff/evaluation/"
        "formal_test29_test30_single_macrostep_integration.py",
        61_434,
        "e2f57ede06cb432f8507eb32eead7a77fbfc8d8d44cc7725a941182e7aedd0c7",
    ),
    (
        "src/heterodiff/processes/"
        "formal_test29_finite_acyclic_route_oracle.py",
        52_186,
        "308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089",
    ),
    (
        "src/heterodiff/evaluation/"
        "formal_test30_synthetic_coupled_path_qualification.py",
        42_349,
        "373ef98c3605e0c0211da8dbc8782f2517cd5976026980e4fcd24435670839e0",
    ),
)

WHOLE_METHOD_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_b12_whole_method_nonconfirmatory_runner_v1.json"
)
WHOLE_METHOD_MACHINE_BYTES = 9_789
WHOLE_METHOD_MACHINE_SHA256 = (
    "a5debbc0db537993191c1554529fdf52e34ace80a92cb24a3555889a11f0490b"
)
WHOLE_METHOD_RECEIPT_SCHEMA = (
    "heterodiff-b12-whole-method-nonconfirmatory-receipt-v1"
)
WHOLE_METHOD_RECEIPT_SHA256 = (
    "677aedeac9fe02a3bac9a14316c2c1f1a0047d6839e9c7492063d344b5e93220"
)

_MAX_CP63_FIXTURE_BYTES = 8_388_608
_MAX_SOURCE_BYTES = 1_048_576
_MAX_WHOLE_METHOD_MACHINE_BYTES = 4_194_304
_ZERO_SHA256 = "0" * 64


class NonconfirmatoryRouteError(ValueError):
    """Raised before an unbound value crosses the route boundary."""


@dataclass(frozen=True)
class SourcePin:
    path: str
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class CP63NonconfirmatoryExecutionBinding:
    fixture: SourcePin
    runner_source: SourcePin
    independent_source: SourcePin
    acceptance_receipt_schema: str
    acceptance_receipt_sha256: str
    acceptance_receipt_canonical_byte_count: int
    acceptance_receipt_canonical_plain_sha256: str
    semantic_pin_receipt_sha256: str
    recomputation_record_sha256: str
    recomputation_public_sha256: str
    recomputation_canonical_plain_sha256: str
    row_count: int
    repetitions_per_row: int
    launch_count: int
    estimand_count: int
    observable_estimand_count: int
    rejection_first_attempt_estimand_count: int
    selected_feature_estimand_count: int
    historical_nonconfirmatory_execution_receipt_revalidated: bool
    fresh_execution_performed_here: bool
    confirmatory_evidence: bool


@dataclass(frozen=True)
class TwoMacrostepExecutionBinding:
    wrapper_source: SourcePin
    parent_sources: Tuple[SourcePin, ...]
    wrapper_schema_version: str
    predicate: str
    report_sha256: str
    ordered_word_pair_cases_checked: int
    distinct_input_sha256_count: int
    distinct_report_sha256_count: int
    compiled_from_captured_bytes_only: bool
    parent_source_bytes_hash_bound: bool
    source_identities_stable: bool
    fresh_execution_performed_here: bool
    confirmatory_evidence: bool


@dataclass(frozen=True)
class WholeMethodExecutionBinding:
    machine_receipt: SourcePin
    receipt_schema: str
    receipt_sha256: str
    supplied_input_sha256: str
    implementation_obligation_count: int
    open_residual_slot_count: int
    separate_recomputation_bytes_equal: bool
    separately_executed_and_validated: bool
    confirmatory_evidence: bool


@dataclass(frozen=True)
class NonconfirmatoryRouteReceipt:
    schema_version: str
    state: str
    cp63_test28: CP63NonconfirmatoryExecutionBinding
    test29_test30_two_macrostep: TwoMacrostepExecutionBinding
    whole_method: WholeMethodExecutionBinding
    route_component_ids: Tuple[str, ...]
    route_components_jointly_bound: bool
    formal_test_28_state: str
    formal_test_29_state: str
    formal_test_30_state: str
    formal_tests_closed: int
    b12_closed: bool
    fields_closed: int
    blockers_closed: int
    result_slots_filled: int
    runtime_selected: bool
    data_contacted: bool
    network_contacted: bool
    entropy_consumed: bool
    science_executed: bool
    authority_asserted: bool
    production_receipt_issued: bool
    tracker_or_ledger_edited: bool
    proposed_timetable_task: str
    proposed_timetable_task_closures: int
    applied_timetable_task_closures: int
    receipt_sha256: str


def _fail(message: str) -> None:
    raise NonconfirmatoryRouteError(message)


def _sha256(raw: bytes) -> str:
    if type(raw) is not bytes:
        raise TypeError("digest input must be exact bytes")
    return hashlib.sha256(raw).hexdigest()


def _exact_sha256(value: object, name: str, *, nonzero: bool = True) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
        or (nonzero and value == _ZERO_SHA256)
    ):
        _fail(name + " must be exact lowercase SHA-256")
    return value


def _safe_relative_path(value: object) -> str:
    if type(value) is not str or not value or "\x00" in value or "\\" in value:
        _fail("relative path must be exact nonempty POSIX text")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in ("", ".", "..") for part in value.split("/"))
    ):
        _fail("relative path must be canonical and confined")
    return value


def _canonical_root(value: object) -> Path:
    if type(value) is not str or not value.startswith("/") or "\x00" in value:
        _fail("project root must be exact absolute text")
    path = Path(value)
    if str(path) != value or not path.is_absolute():
        _fail("project root text is noncanonical")
    try:
        if path.resolve(strict=True) != path or not path.is_dir():
            _fail("project root is not one canonical directory")
    except OSError as exc:
        raise NonconfirmatoryRouteError("project root cannot be resolved") from exc
    return path


@dataclass(frozen=True)
class _CapturedFile:
    path: str
    raw: bytes
    byte_count: int
    sha256: str
    identity: Tuple[int, ...]


def _capture_regular(root: Path, relative: str, maximum: int) -> _CapturedFile:
    relative = _safe_relative_path(relative)
    if type(maximum) is not int or maximum <= 0:
        raise TypeError("maximum must be exact positive int")
    root_fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    fd = root_fd
    try:
        for part in root.parts[1:]:
            nxt = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
            )
            if fd != root_fd:
                os.close(fd)
            fd = nxt
        parts = relative.split("/")
        for part in parts[:-1]:
            nxt = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
            )
            if fd != root_fd:
                os.close(fd)
            fd = nxt
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            before = os.fstat(leaf)
            if (
                not stat.S_ISREG(before.st_mode)
                or stat.S_IMODE(before.st_mode) != 0o644
                or before.st_nlink != 1
                or before.st_size < 1
                or before.st_size > maximum
            ):
                _fail("unsafe file custody: " + relative)
            chunks = bytearray()
            while True:
                chunk = os.read(leaf, min(131_072, maximum + 1 - len(chunks)))
                if not chunk:
                    break
                chunks.extend(chunk)
                if len(chunks) > maximum:
                    _fail("file exceeds byte ceiling: " + relative)
            after = os.fstat(leaf)
            identity_before = (
                before.st_dev,
                before.st_ino,
                before.st_uid,
                before.st_gid,
                before.st_mode,
                before.st_nlink,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            )
            identity_after = (
                after.st_dev,
                after.st_ino,
                after.st_uid,
                after.st_gid,
                after.st_mode,
                after.st_nlink,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            )
            if identity_before != identity_after or len(chunks) != after.st_size:
                _fail("file changed during capture: " + relative)
            raw = bytes(chunks)
            return _CapturedFile(
                path=relative,
                raw=raw,
                byte_count=len(raw),
                sha256=_sha256(raw),
                identity=identity_after,
            )
        finally:
            os.close(leaf)
    finally:
        if fd != root_fd:
            os.close(fd)
        os.close(root_fd)


def _capture_pinned(
    root: Path,
    relative: str,
    expected_bytes: int,
    expected_sha256: str,
    *,
    maximum: int,
) -> _CapturedFile:
    _exact_sha256(expected_sha256, "expected file digest")
    captured = _capture_regular(root, relative, maximum)
    if (
        captured.byte_count != expected_bytes
        or captured.sha256 != expected_sha256
    ):
        _fail("file pin mismatch before use: " + relative)
    return captured


def _source_pin(captured: _CapturedFile) -> SourcePin:
    result = SourcePin(captured.path, captured.byte_count, captured.sha256)
    _validate_source_pin(result)
    return result


def _validate_source_pin(value: object) -> SourcePin:
    if type(value) is not SourcePin:
        raise TypeError("source pin must have exact concrete type")
    _safe_relative_path(value.path)
    if type(value.byte_count) is not int or value.byte_count <= 0:
        _fail("source byte count must be exact positive int")
    _exact_sha256(value.sha256, "source digest")
    return value


def _reject_duplicate_pairs(pairs: object) -> Dict[str, object]:
    if type(pairs) is not list:
        _fail("JSON object pair carrier differs")
    result: Dict[str, object] = {}
    for pair in pairs:
        if type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str:
            _fail("JSON object key differs")
        key, value = pair
        if key in result:
            _fail("duplicate JSON key: " + key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    _fail("non-finite JSON constant: " + value)


def _decode_json(raw: bytes, name: str) -> object:
    if type(raw) is not bytes:
        raise TypeError(name + " must be exact bytes")
    try:
        text = raw.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_float=Decimal,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, decimal.InvalidOperation) as exc:
        raise NonconfirmatoryRouteError(name + " is not strict JSON") from exc


def _plain_json_value(value: object) -> object:
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is tuple:
        return [_plain_json_value(item) for item in value]
    supported = (
        SourcePin,
        CP63NonconfirmatoryExecutionBinding,
        TwoMacrostepExecutionBinding,
        WholeMethodExecutionBinding,
        NonconfirmatoryRouteReceipt,
    )
    if type(value) in supported:
        return {
            item.name: _plain_json_value(getattr(value, item.name))
            for item in fields(value)
        }
    raise TypeError("value is outside the exact route canonical grammar")


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        _plain_json_value(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _exact_dict(value: object, name: str) -> Dict[str, object]:
    if type(value) is not dict:
        _fail(name + " must be exact JSON object")
    return value


def _expect_keys(value: Dict[str, object], keys: Tuple[str, ...], name: str) -> None:
    if set(value) != set(keys):
        _fail(name + " key roster differs")


def _cp63_binding(root: Path) -> CP63NonconfirmatoryExecutionBinding:
    fixture = _capture_pinned(
        root,
        CP63_FIXTURE_PATH,
        CP63_FIXTURE_BYTES,
        CP63_FIXTURE_SHA256,
        maximum=_MAX_CP63_FIXTURE_BYTES,
    )
    runner = _capture_pinned(
        root,
        CP63_RUNNER_PATH,
        CP63_RUNNER_BYTES,
        CP63_RUNNER_SHA256,
        maximum=_MAX_SOURCE_BYTES,
    )
    independent = _capture_pinned(
        root,
        CP63_INDEPENDENT_PATH,
        CP63_INDEPENDENT_BYTES,
        CP63_INDEPENDENT_SHA256,
        maximum=_MAX_SOURCE_BYTES,
    )
    document = _exact_dict(_decode_json(fixture.raw, "CP63 fixture"), "CP63 fixture")
    contracts = _exact_dict(document.get("diagnostic_contracts"), "CP63 contracts")
    summary = _exact_dict(
        contracts.get("whole_seed_runner_recomputation_rehearsal"),
        "CP63 rehearsal summary",
    )
    focused = _exact_dict(summary.get("focused_verification"), "CP63 focused proof")
    acceptance = _exact_dict(
        focused.get("acceptance_receipt"), "CP63 acceptance receipt"
    )
    receipt_keys = (
        "schema",
        "runner_source_sha256",
        "independent_source_sha256",
        "runner_bundle_record_sha256",
        "cp62_source_sha256",
        "cp62_bundle_sha256",
        "cp62_semantic_sha256",
        "runtime_lock_sha256",
        "rehearsal_id",
        "plan_seed_hex",
        "launch_count",
        "row_count",
        "repetitions_per_row",
        "case_receipts",
        "repetition_blind_554_receipt",
        "independent_554_inventory",
        "receipt_sha256",
    )
    _expect_keys(acceptance, receipt_keys, "CP63 acceptance receipt")
    canonical = json.dumps(
        acceptance,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    if (
        len(canonical) != CP63_ACCEPTANCE_CANONICAL_BYTES
        or _sha256(canonical) != CP63_ACCEPTANCE_CANONICAL_PLAIN_SHA256
        or acceptance.get("receipt_sha256") != CP63_ACCEPTANCE_SHA256
        or focused.get("acceptance_receipt_domain_sha256")
        != CP63_ACCEPTANCE_SHA256
        or focused.get("acceptance_receipt_canonical_json_bytes")
        != CP63_ACCEPTANCE_CANONICAL_BYTES
        or focused.get("acceptance_receipt_canonical_plain_sha256")
        != CP63_ACCEPTANCE_CANONICAL_PLAIN_SHA256
        or focused.get("all_sixteen_stable_and_compact_pins_independently_reconstructed")
        is not True
        or focused.get("source_hashes_checked_before_and_after_execution") is not True
        or focused.get("exit_code") != 0
        or focused.get("confirmatory_evidence") is not False
        or summary.get("semantic_pin_receipt", {}).get("record_sha256")
        != CP63_SEMANTIC_PIN_SHA256
    ):
        _fail("CP63 accepted execution binding differs")
    zeroed = dict(acceptance)
    zeroed["receipt_sha256"] = _ZERO_SHA256
    zeroed_bytes = json.dumps(
        zeroed,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    if _sha256(b"cp63-test28-16x2-acceptance-receipt-v1\0" + zeroed_bytes) != (
        CP63_ACCEPTANCE_SHA256
    ):
        _fail("CP63 acceptance receipt domain digest differs")
    cases = acceptance.get("case_receipts")
    if type(cases) is not list or len(cases) != 16:
        _fail("CP63 case roster differs")
    for ordinal, case in enumerate(cases, 1):
        row = _exact_dict(case, "CP63 case")
        repetitions = row.get("raw_repetitions")
        if (
            row.get("case_id") != "rehearsal-row-%02d" % ordinal
            or row.get("row_ordinal") != ordinal
            or type(repetitions) is not list
            or len(repetitions) != 2
            or tuple(item.get("repetition") for item in repetitions) != (1, 2)
        ):
            _fail("CP63 case/repetition order differs")
    recomputation = _exact_dict(
        acceptance.get("repetition_blind_554_receipt"),
        "CP63 recomputation receipt",
    )
    if (
        acceptance.get("schema") != "cp63-test28-16x2-acceptance-receipt-v1"
        or acceptance.get("runner_source_sha256") != runner.sha256
        or acceptance.get("independent_source_sha256") != independent.sha256
        or acceptance.get("row_count") != 16
        or acceptance.get("repetitions_per_row") != 2
        or acceptance.get("launch_count") != 32
        or recomputation.get("canonical_byte_count") != 12_939
        or recomputation.get("canonical_plain_sha256")
        != CP63_RECOMPUTATION_CANONICAL_PLAIN_SHA256
        or recomputation.get("record_sha256") != CP63_RECOMPUTATION_RECORD_SHA256
        or recomputation.get("public_sha256") != CP63_RECOMPUTATION_PUBLIC_SHA256
        or recomputation.get("repetitions_equal") is not True
        or recomputation.get("estimand_count") != 554
        or recomputation.get("observable_estimand_count") != 72
        or recomputation.get("rejection_first_attempt_estimand_count") != 170
        or recomputation.get("selected_feature_estimand_count") != 312
    ):
        _fail("CP63 independent recomputation binding differs")
    result = CP63NonconfirmatoryExecutionBinding(
        fixture=_source_pin(fixture),
        runner_source=_source_pin(runner),
        independent_source=_source_pin(independent),
        acceptance_receipt_schema="cp63-test28-16x2-acceptance-receipt-v1",
        acceptance_receipt_sha256=CP63_ACCEPTANCE_SHA256,
        acceptance_receipt_canonical_byte_count=CP63_ACCEPTANCE_CANONICAL_BYTES,
        acceptance_receipt_canonical_plain_sha256=(
            CP63_ACCEPTANCE_CANONICAL_PLAIN_SHA256
        ),
        semantic_pin_receipt_sha256=CP63_SEMANTIC_PIN_SHA256,
        recomputation_record_sha256=CP63_RECOMPUTATION_RECORD_SHA256,
        recomputation_public_sha256=CP63_RECOMPUTATION_PUBLIC_SHA256,
        recomputation_canonical_plain_sha256=(
            CP63_RECOMPUTATION_CANONICAL_PLAIN_SHA256
        ),
        row_count=16,
        repetitions_per_row=2,
        launch_count=32,
        estimand_count=554,
        observable_estimand_count=72,
        rejection_first_attempt_estimand_count=170,
        selected_feature_estimand_count=312,
        historical_nonconfirmatory_execution_receipt_revalidated=True,
        fresh_execution_performed_here=False,
        confirmatory_evidence=False,
    )
    return _validate_cp63_binding(result)


def _validate_cp63_binding(value: object) -> CP63NonconfirmatoryExecutionBinding:
    if type(value) is not CP63NonconfirmatoryExecutionBinding:
        raise TypeError("CP63 binding must have exact concrete type")
    for pin in (value.fixture, value.runner_source, value.independent_source):
        _validate_source_pin(pin)
    for name in (
        "acceptance_receipt_sha256",
        "acceptance_receipt_canonical_plain_sha256",
        "semantic_pin_receipt_sha256",
        "recomputation_record_sha256",
        "recomputation_public_sha256",
        "recomputation_canonical_plain_sha256",
    ):
        _exact_sha256(getattr(value, name), "CP63 " + name)
    expected = (
        value.fixture
        == SourcePin(CP63_FIXTURE_PATH, CP63_FIXTURE_BYTES, CP63_FIXTURE_SHA256)
        and value.runner_source
        == SourcePin(CP63_RUNNER_PATH, CP63_RUNNER_BYTES, CP63_RUNNER_SHA256)
        and value.independent_source
        == SourcePin(
            CP63_INDEPENDENT_PATH,
            CP63_INDEPENDENT_BYTES,
            CP63_INDEPENDENT_SHA256,
        )
        and type(value.acceptance_receipt_schema) is str
        and value.acceptance_receipt_schema == "cp63-test28-16x2-acceptance-receipt-v1"
        and value.acceptance_receipt_sha256 == CP63_ACCEPTANCE_SHA256
        and value.acceptance_receipt_canonical_byte_count
        == CP63_ACCEPTANCE_CANONICAL_BYTES
        and value.acceptance_receipt_canonical_plain_sha256
        == CP63_ACCEPTANCE_CANONICAL_PLAIN_SHA256
        and value.semantic_pin_receipt_sha256 == CP63_SEMANTIC_PIN_SHA256
        and value.recomputation_record_sha256 == CP63_RECOMPUTATION_RECORD_SHA256
        and value.recomputation_public_sha256 == CP63_RECOMPUTATION_PUBLIC_SHA256
        and value.recomputation_canonical_plain_sha256
        == CP63_RECOMPUTATION_CANONICAL_PLAIN_SHA256
        and all(
            type(item) is int
            for item in (
                value.row_count,
                value.repetitions_per_row,
                value.launch_count,
                value.estimand_count,
                value.observable_estimand_count,
                value.rejection_first_attempt_estimand_count,
                value.selected_feature_estimand_count,
            )
        )
        and (
            value.row_count,
            value.repetitions_per_row,
            value.launch_count,
            value.estimand_count,
            value.observable_estimand_count,
            value.rejection_first_attempt_estimand_count,
            value.selected_feature_estimand_count,
        )
        == (16, 2, 32, 554, 72, 170, 312)
        and value.historical_nonconfirmatory_execution_receipt_revalidated is True
        and value.fresh_execution_performed_here is False
        and value.confirmatory_evidence is False
    )
    if not expected:
        _fail("CP63 route binding differs")
    return value


def _execute_captured_wrapper(
    captured: _CapturedFile, root: Path
) -> Dict[str, object]:
    if (
        captured.path != TWO_MACROSTEP_WRAPPER_PATH
        or captured.byte_count != TWO_MACROSTEP_WRAPPER_BYTES
        or captured.sha256 != TWO_MACROSTEP_WRAPPER_SHA256
        or _sha256(captured.raw) != TWO_MACROSTEP_WRAPPER_SHA256
    ):
        _fail("captured two-macrostep wrapper differs before compile")
    module_name = "_formal_test28_30_route_bound_two_macrostep_wrapper"
    module = ModuleType(module_name)
    module.__file__ = str(root / captured.path)
    module.__package__ = ""
    missing = object()
    previous = sys.modules.get(module_name, missing)
    sys.modules[module_name] = module
    try:
        exec(
            compile(captured.raw, module.__file__, "exec", dont_inherit=True),
            module.__dict__,
        )
        validate = module.__dict__.get("validate")
        if type(validate).__name__ != "function":
            _fail("captured wrapper validation entrypoint differs")
        result = validate(root)
    finally:
        if previous is missing:
            del sys.modules[module_name]
        else:
            sys.modules[module_name] = previous
    return _exact_dict(result, "two-macrostep wrapper result")


def _two_macrostep_binding(root: Path) -> TwoMacrostepExecutionBinding:
    wrapper = _capture_pinned(
        root,
        TWO_MACROSTEP_WRAPPER_PATH,
        TWO_MACROSTEP_WRAPPER_BYTES,
        TWO_MACROSTEP_WRAPPER_SHA256,
        maximum=_MAX_SOURCE_BYTES,
    )
    output = _execute_captured_wrapper(wrapper, root)
    expected_keys = (
        "status",
        "schema_version",
        "predicate",
        "report_sha256",
        "ordered_word_pair_cases_checked",
        "candidate_report_parent_custody_authenticated",
        "envelope_parent_source_custody_authenticated",
        "compiled_from_captured_bytes_only",
        "source_identities_stable",
        "source_count",
        "formal_tests_closed",
        "fields_closed",
        "blockers_closed",
        "result_slots_filled",
        "tracker_files_edited",
        "source_receipts",
    )
    _expect_keys(output, expected_keys, "two-macrostep wrapper result")
    if (
        output.get("status") != "PASS"
        or output.get("schema_version")
        != "formal-test29-test30-two-macrostep-parent-custody-hash-first-v1"
        or output.get("predicate") != TWO_MACROSTEP_PREDICATE
        or output.get("report_sha256") != TWO_MACROSTEP_REPORT_SHA256
        or output.get("ordered_word_pair_cases_checked") != 1_024
        or output.get("candidate_report_parent_custody_authenticated") is not False
        or output.get("envelope_parent_source_custody_authenticated") is not True
        or output.get("compiled_from_captured_bytes_only") is not True
        or output.get("source_identities_stable") is not True
        or output.get("source_count") != 4
        or any(
            output.get(name) != 0
            for name in (
                "formal_tests_closed",
                "fields_closed",
                "blockers_closed",
                "result_slots_filled",
                "tracker_files_edited",
            )
        )
    ):
        _fail("two-macrostep route result differs")
    source_receipts = output.get("source_receipts")
    if type(source_receipts) is not list or len(source_receipts) != 4:
        _fail("two-macrostep parent source receipt roster differs")
    parent_pins = []
    for item in source_receipts:
        receipt = _exact_dict(item, "two-macrostep parent source receipt")
        if set(receipt) != {
            "path",
            "bytes",
            "sha256",
            "device",
            "inode",
            "uid",
            "gid",
            "mode_octal",
            "nlink",
            "mtime_ns",
            "ctime_ns",
        }:
            _fail("two-macrostep parent source receipt keys differ")
        parent_pins.append(
            _validate_source_pin(
                SourcePin(receipt["path"], receipt["bytes"], receipt["sha256"])
            )
        )
    after = _capture_pinned(
        root,
        TWO_MACROSTEP_WRAPPER_PATH,
        TWO_MACROSTEP_WRAPPER_BYTES,
        TWO_MACROSTEP_WRAPPER_SHA256,
        maximum=_MAX_SOURCE_BYTES,
    )
    if wrapper.identity != after.identity:
        _fail("two-macrostep wrapper identity changed across execution")
    result = TwoMacrostepExecutionBinding(
        wrapper_source=_source_pin(wrapper),
        parent_sources=tuple(parent_pins),
        wrapper_schema_version=(
            "formal-test29-test30-two-macrostep-parent-custody-hash-first-v1"
        ),
        predicate=TWO_MACROSTEP_PREDICATE,
        report_sha256=TWO_MACROSTEP_REPORT_SHA256,
        ordered_word_pair_cases_checked=1_024,
        distinct_input_sha256_count=1_024,
        distinct_report_sha256_count=1_024,
        compiled_from_captured_bytes_only=True,
        parent_source_bytes_hash_bound=True,
        source_identities_stable=True,
        fresh_execution_performed_here=True,
        confirmatory_evidence=False,
    )
    return _validate_two_macrostep_binding(result)


def _validate_two_macrostep_binding(value: object) -> TwoMacrostepExecutionBinding:
    if type(value) is not TwoMacrostepExecutionBinding:
        raise TypeError("two-macrostep binding must have exact concrete type")
    _validate_source_pin(value.wrapper_source)
    if type(value.parent_sources) is not tuple or len(value.parent_sources) != 4:
        _fail("two-macrostep parent pin roster differs")
    for item in value.parent_sources:
        _validate_source_pin(item)
    _exact_sha256(value.report_sha256, "two-macrostep report digest")
    if (
        value.wrapper_source
        != SourcePin(
            TWO_MACROSTEP_WRAPPER_PATH,
            TWO_MACROSTEP_WRAPPER_BYTES,
            TWO_MACROSTEP_WRAPPER_SHA256,
        )
        or value.parent_sources
        != tuple(SourcePin(*item) for item in TWO_MACROSTEP_PARENT_PINS)
        or type(value.wrapper_schema_version) is not str
        or value.wrapper_schema_version
        != "formal-test29-test30-two-macrostep-parent-custody-hash-first-v1"
        or type(value.predicate) is not str
        or value.predicate != TWO_MACROSTEP_PREDICATE
        or value.report_sha256 != TWO_MACROSTEP_REPORT_SHA256
        or any(
            type(item) is not int
            for item in (
                value.ordered_word_pair_cases_checked,
                value.distinct_input_sha256_count,
                value.distinct_report_sha256_count,
            )
        )
        or (
            value.ordered_word_pair_cases_checked,
            value.distinct_input_sha256_count,
            value.distinct_report_sha256_count,
        )
        != (1_024, 1_024, 1_024)
        or value.compiled_from_captured_bytes_only is not True
        or value.parent_source_bytes_hash_bound is not True
        or value.source_identities_stable is not True
        or value.fresh_execution_performed_here is not True
        or value.confirmatory_evidence is not False
    ):
        _fail("two-macrostep route binding differs")
    return value


def _whole_method_binding(root: Path) -> WholeMethodExecutionBinding:
    if (
        WHOLE_METHOD_MACHINE_PATH.startswith("__UNSEALED_")
        or WHOLE_METHOD_MACHINE_BYTES <= 0
        or WHOLE_METHOD_MACHINE_SHA256 == _ZERO_SHA256
        or WHOLE_METHOD_RECEIPT_SHA256 == _ZERO_SHA256
    ):
        _fail("whole-method lane is not sealed")
    captured = _capture_pinned(
        root,
        WHOLE_METHOD_MACHINE_PATH,
        WHOLE_METHOD_MACHINE_BYTES,
        WHOLE_METHOD_MACHINE_SHA256,
        maximum=_MAX_WHOLE_METHOD_MACHINE_BYTES,
    )
    document = _exact_dict(
        _decode_json(captured.raw, "whole-method machine receipt"),
        "whole-method machine receipt",
    )
    # The final exact extraction is sealed together with the disjoint lane.
    route = _exact_dict(document.get("route_binding"), "whole-method route binding")
    expected_keys = (
        "confirmatory_evidence",
        "implementation_obligation_count",
        "open_residual_slot_count",
        "receipt_schema",
        "separate_recomputation_bytes_equal",
        "separately_executed_and_validated",
        "stable_receipt_sha256",
        "supplied_input_sha256",
    )
    _expect_keys(route, expected_keys, "whole-method route binding")
    result = WholeMethodExecutionBinding(
        machine_receipt=_source_pin(captured),
        receipt_schema=route["receipt_schema"],
        receipt_sha256=route["stable_receipt_sha256"],
        supplied_input_sha256=route["supplied_input_sha256"],
        implementation_obligation_count=route[
            "implementation_obligation_count"
        ],
        open_residual_slot_count=route["open_residual_slot_count"],
        separate_recomputation_bytes_equal=route[
            "separate_recomputation_bytes_equal"
        ],
        separately_executed_and_validated=route[
            "separately_executed_and_validated"
        ],
        confirmatory_evidence=route["confirmatory_evidence"],
    )
    return _validate_whole_method_binding(result)


def _validate_whole_method_binding(value: object) -> WholeMethodExecutionBinding:
    if type(value) is not WholeMethodExecutionBinding:
        raise TypeError("whole-method binding must have exact concrete type")
    _validate_source_pin(value.machine_receipt)
    _exact_sha256(value.receipt_sha256, "whole-method receipt digest")
    _exact_sha256(value.supplied_input_sha256, "whole-method input digest")
    if (
        value.machine_receipt
        != SourcePin(
            WHOLE_METHOD_MACHINE_PATH,
            WHOLE_METHOD_MACHINE_BYTES,
            WHOLE_METHOD_MACHINE_SHA256,
        )
        or type(value.receipt_schema) is not str
        or value.receipt_schema != WHOLE_METHOD_RECEIPT_SCHEMA
        or value.receipt_sha256 != WHOLE_METHOD_RECEIPT_SHA256
        or type(value.implementation_obligation_count) is not int
        or value.implementation_obligation_count != 19
        or type(value.open_residual_slot_count) is not int
        or value.open_residual_slot_count != 50
        or value.separate_recomputation_bytes_equal is not True
        or value.separately_executed_and_validated is not True
        or value.confirmatory_evidence is not False
    ):
        _fail("whole-method route binding differs")
    return value


def _validate_route_receipt(value: object) -> NonconfirmatoryRouteReceipt:
    if type(value) is not NonconfirmatoryRouteReceipt:
        raise TypeError("route receipt must have exact concrete type")
    _validate_cp63_binding(value.cp63_test28)
    _validate_two_macrostep_binding(value.test29_test30_two_macrostep)
    _validate_whole_method_binding(value.whole_method)
    if (
        type(value.schema_version) is not str
        or value.schema_version != SCHEMA_VERSION
        or type(value.state) is not str
        or value.state != STATE
        or type(value.route_component_ids) is not tuple
        or any(type(item) is not str for item in value.route_component_ids)
        or value.route_component_ids
        != (
            "CP63_TEST28_ACCEPTED_16X2_RUNNER_AND_INDEPENDENT_RECOMPUTATION",
            "HASH_FIRST_TEST29_TEST30_TWO_MACROSTEP_1024_CASE_PATH",
            "WHOLE_METHOD_SUPPLIED_INPUT_SYNTHETIC_INTEGRATION",
        )
        or value.route_components_jointly_bound is not True
        or (
            value.formal_test_28_state,
            value.formal_test_29_state,
            value.formal_test_30_state,
        )
        != ("OPEN", "OPEN", "PENDING")
        or any(
            type(item) is not str
            for item in (
                value.formal_test_28_state,
                value.formal_test_29_state,
                value.formal_test_30_state,
                value.proposed_timetable_task,
            )
        )
        or any(
            type(item) is not int
            for item in (
                value.formal_tests_closed,
                value.fields_closed,
                value.blockers_closed,
                value.result_slots_filled,
                value.proposed_timetable_task_closures,
                value.applied_timetable_task_closures,
            )
        )
        or value.formal_tests_closed != 0
        or value.b12_closed is not False
        or any(
            item != 0
            for item in (
                value.fields_closed,
                value.blockers_closed,
                value.result_slots_filled,
            )
        )
        or any(
            item is not False
            for item in (
                value.runtime_selected,
                value.data_contacted,
                value.network_contacted,
                value.entropy_consumed,
                value.science_executed,
                value.authority_asserted,
                value.production_receipt_issued,
                value.tracker_or_ledger_edited,
            )
        )
        or value.proposed_timetable_task != PROPOSED_TIMETABLE_TASK
        or value.proposed_timetable_task_closures != 1
        or value.applied_timetable_task_closures != 0
    ):
        _fail("route receipt state/nonclaim boundary differs")
    _exact_sha256(value.receipt_sha256, "route receipt digest")
    zeroed = replace(value, receipt_sha256=_ZERO_SHA256)
    if value.receipt_sha256 != _sha256(
        RECEIPT_DOMAIN + _canonical_json_bytes(zeroed)
    ):
        _fail("route receipt digest differs")
    return value


def run_nonconfirmatory_test28_30_route(
    project_root: str,
) -> NonconfirmatoryRouteReceipt:
    """Run/bind the three bounded supplied-input routes once."""

    root = _canonical_root(project_root)
    cp63 = _cp63_binding(root)
    two_macrostep = _two_macrostep_binding(root)
    whole_method = _whole_method_binding(root)
    provisional = NonconfirmatoryRouteReceipt(
        schema_version=SCHEMA_VERSION,
        state=STATE,
        cp63_test28=cp63,
        test29_test30_two_macrostep=two_macrostep,
        whole_method=whole_method,
        route_component_ids=(
            "CP63_TEST28_ACCEPTED_16X2_RUNNER_AND_INDEPENDENT_RECOMPUTATION",
            "HASH_FIRST_TEST29_TEST30_TWO_MACROSTEP_1024_CASE_PATH",
            "WHOLE_METHOD_SUPPLIED_INPUT_SYNTHETIC_INTEGRATION",
        ),
        route_components_jointly_bound=True,
        formal_test_28_state="OPEN",
        formal_test_29_state="OPEN",
        formal_test_30_state="PENDING",
        formal_tests_closed=0,
        b12_closed=False,
        fields_closed=0,
        blockers_closed=0,
        result_slots_filled=0,
        runtime_selected=False,
        data_contacted=False,
        network_contacted=False,
        entropy_consumed=False,
        science_executed=False,
        authority_asserted=False,
        production_receipt_issued=False,
        tracker_or_ledger_edited=False,
        proposed_timetable_task=PROPOSED_TIMETABLE_TASK,
        proposed_timetable_task_closures=1,
        applied_timetable_task_closures=0,
        receipt_sha256=_ZERO_SHA256,
    )
    result = replace(
        provisional,
        receipt_sha256=_sha256(
            RECEIPT_DOMAIN + _canonical_json_bytes(provisional)
        ),
    )
    return _validate_route_receipt(result)


def validate_nonconfirmatory_test28_30_route_receipt(
    receipt: NonconfirmatoryRouteReceipt,
) -> NonconfirmatoryRouteReceipt:
    """Validate one exact route receipt without executing a route."""

    return _validate_route_receipt(receipt)


def route_receipt_canonical_json_bytes(
    receipt: NonconfirmatoryRouteReceipt,
) -> bytes:
    """Return exact canonical ASCII JSON plus one terminal LF."""

    return _canonical_json_bytes(_validate_route_receipt(receipt)) + b"\n"


__all__ = (
    "NonconfirmatoryRouteError",
    "SourcePin",
    "CP63NonconfirmatoryExecutionBinding",
    "TwoMacrostepExecutionBinding",
    "WholeMethodExecutionBinding",
    "NonconfirmatoryRouteReceipt",
    "SCHEMA_VERSION",
    "STATE",
    "PROPOSED_TIMETABLE_TASK",
    "run_nonconfirmatory_test28_30_route",
    "validate_nonconfirmatory_test28_30_route_receipt",
    "route_receipt_canonical_json_bytes",
)
