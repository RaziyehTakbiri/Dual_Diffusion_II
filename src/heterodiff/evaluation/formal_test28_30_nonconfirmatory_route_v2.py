"""Additive V2 route across Formal Tests 28--30 on synthetic inputs only.

The route revalidates the historical CP63 Test-28 rehearsal, freshly executes
the accepted 1,024-case Test-29/Test-30 wrapper, and binds the independently
accepted initializer-to-path whole-method successor.  It is project-control
evidence, not a Formal-Test, production, runtime, data, or scientific result.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from decimal import Decimal
import decimal
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import threading
from types import ModuleType
from typing import Dict, Mapping, Tuple


SCHEMA_VERSION = "heterodiff-formal-test28-30-nonconfirmatory-route-v2"
STATE = "NONCONFIRMATORY_SYNTHETIC_TEST28_30_REPAIRED_ROUTES_JOINTLY_BOUND"
RECEIPT_DOMAIN = b"heterodiff-formal-test28-30-nonconfirmatory-route-v2\0"
SUBJECT_DOMAIN = b"heterodiff-formal-test28-30-nonconfirmatory-route-subject-v2\0"
PROPOSED_TIMETABLE_TASK = (
    "Required Tests 28\u201330 routes run end to end on "
    "nonconfirmatory/synthetic inputs."
)
ZERO_SHA256 = "0" * 64

V1_SOURCE_PATH = "src/heterodiff/evaluation/formal_test28_30_nonconfirmatory_route.py"
V1_SOURCE_BYTES = 41_184
V1_SOURCE_SHA256 = "aabbea24156c63d833beaa7fe1a29d2c4879a8a0cbd0d171ec0ca558d3a34a32"

WHOLE_MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_b12_whole_method_initializer_path_integration_successor_v1.json"
)
WHOLE_MACHINE_BYTES = 30_010
WHOLE_MACHINE_SHA256 = "e247add0ef427cfd2c77f27a9347c28bc0b70df8bb53b803864619d27d1e7ea8"
WHOLE_MACHINE_RECORD_SHA256 = "384f4a15fa28c18f3e84177f7bc42332b612ac8ed3afff6a5a5ee918b02ab107"
WHOLE_MACHINE_RECORD_DOMAIN = (
    "heterodiff-b12-whole-method-initializer-path-successor-record-v1"
)
WHOLE_REVIEW_PATH = (
    "PROJECT_B12_WHOLE_METHOD_INITIALIZER_PATH_INTEGRATION_SUCCESSOR_"
    "INDEPENDENT_REVIEW.md"
)
WHOLE_REVIEW_BYTES = 11_076
WHOLE_REVIEW_SHA256 = "e24f2e97a67048323170b44d6e537ab07c3a7a6692cf682bc3053c1165732765"
WHOLE_RECEIPT_SHA256 = "7f3af61499f4c618daa38d72e38570c4759c5e146eeeef61bb182b9b4f20e102"
WHOLE_CORE_SHA256 = "73887c5411e8822942c9c37ddbdfb1a485f96ef1a2fce4c4ff56f503b4b9bc8e"
WHOLE_SUPPLIED_INPUT_SHA256 = "f7e213442d073f88df73d2b33c21e43add4269a8a45b07714bfbd60b4b4ff971"
WHOLE_STABLE_INITIALIZER_SHA256 = "5bca3f822a6a526fb0775cc7bf422347df7e65227141b4f2c76a462d3d597f85"
WHOLE_SELECTED_CONFIGURATION_SHA256 = "c9450132be2800eddc7e8e36547c49e8b7839e1e282e32f0736b453267b92b06"
WHOLE_INITIAL_STATE_SHA256 = "2338839b5c7df9c0845063a4053e6ab40d16132f232713ef515d5599d728f05f"
WHOLE_TRANSFORM_SHA256 = "72a27a8f315e4a1fa95933fde4fe8711d08bcd1d00766dea80bf50275ebcb5b4"
WHOLE_PATH_INPUT_SHA256 = "63aa54613cad1b89973bbceb83cab2479f2cacbcd92e8c2b925f1ff34912f9a4"
WHOLE_PATH_REPORT_SHA256 = "15b46792946d98a9893ba3b7fe31ff83c483500c45751564c8bfbbe9fb247b81"
WHOLE_CUSTODY_SHA256 = "037d50b89289979c8b40bc843f14fd47fc0365792c0b12c4315b4132c6e428ca"
WHOLE_TRANSFORM_POLICY = (
    "TEST28-TYPE-PARITY-FIRST-COORDINATE-ZERO-DIM-ZERO-TO-PATH-STATE-V1"
)
WHOLE_PREDECESSOR_RECEIPT_SHA256 = (
    "677aedeac9fe02a3bac9a14316c2c1f1a0047d6839e9c7492063d344b5e93220"
)
WHOLE_PREDECESSOR_RECORD_SHA256 = (
    "451ef6059fea8cb2f98128c388056bcd82739645a97dfdd56021055744cb04af"
)

MAX_SOURCE_BYTES = 1_048_576
MAX_MACHINE_BYTES = 4_194_304
_V1_EXECUTION_LOCK = threading.RLock()


class NonconfirmatoryRouteV2Error(ValueError):
    """Raised before an unbound value crosses the V2 route boundary."""


@dataclass(frozen=True)
class FilePin:
    path: str
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class WholeMethodSuccessorBinding:
    machine: FilePin
    independent_review: FilePin
    machine_record_sha256: str
    receipt_sha256: str
    core_output_sha256: str
    supplied_input_sha256: str
    stable_initializer_execution_sha256: str
    selected_configuration_sha256: str
    transform_policy_id: str
    transform_sha256: str
    derived_initial_state_sha256: str
    integrated_path_input_sha256: str
    integrated_path_report_sha256: str
    custody_chain_sha256: str
    predecessor_machine_record_sha256: str
    predecessor_receipt_sha256: str
    isolated_hash_first_validator_pass: bool
    independent_review_go: bool
    test28_initializer_admissible: bool
    initializer_to_path_integrated: bool
    bounded_two_macrostep_path_integrated: bool
    test29_route_and_lineage_semantics_integrated: bool
    test30_heun_primitive_integrated: bool
    separate_recomputation_bytes_equal: bool
    open_residual_slot_count: int
    confirmatory_evidence: bool


@dataclass(frozen=True)
class NonconfirmatoryRouteV2Receipt:
    schema_version: str
    state: str
    cp63_test28: Mapping[str, object]
    test29_test30_two_macrostep: Mapping[str, object]
    whole_method_successor: WholeMethodSuccessorBinding
    route_component_ids: Tuple[str, ...]
    route_subject_sha256: str
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
    raise NonconfirmatoryRouteV2Error(message)


def _sha256(raw: bytes) -> str:
    if type(raw) is not bytes:
        raise TypeError("digest input must be exact bytes")
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _domain(domain: str, value: object) -> str:
    if type(domain) is not str or not domain or not domain.isascii():
        raise TypeError("domain must be exact nonempty ASCII")
    return _sha256(domain.encode("ascii") + b"\0" + _canonical(value))


def _exact_sha(value: object, name: str) -> str:
    if (
        type(value) is not str or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
        or value == ZERO_SHA256
    ):
        _fail(name + " must be exact nonzero lowercase SHA-256")
    return value


def _safe_relative(value: object) -> str:
    if type(value) is not str or not value or "\0" in value or "\\" in value:
        _fail("relative path text differs")
    path = PurePosixPath(value)
    if (
        path.is_absolute() or path.as_posix() != value
        or any(part in ("", ".", "..") for part in value.split("/"))
    ):
        _fail("relative path is noncanonical or escapes")
    return value


def _root(value: object) -> Path:
    if type(value) is not str or not value.startswith("/") or "\0" in value:
        _fail("root must be exact absolute text")
    result = Path(value)
    if str(result) != value or not result.is_absolute():
        _fail("root text is noncanonical")
    try:
        if result.resolve(strict=True) != result or not result.is_dir():
            _fail("root must be one physical canonical directory")
    except OSError as exc:
        raise NonconfirmatoryRouteV2Error("root cannot be resolved") from exc
    return result


def _identity(value: os.stat_result) -> Tuple[int, ...]:
    return (
        value.st_dev, value.st_ino, value.st_uid, value.st_gid, value.st_mode,
        value.st_nlink, value.st_size, value.st_mtime_ns, value.st_ctime_ns,
    )


def _capture(root: Path, relative: str, size: int, digest: str, ceiling: int) -> bytes:
    _safe_relative(relative)
    _exact_sha(digest, "expected digest")
    if type(size) is not int or size <= 0 or size > ceiling:
        _fail("expected byte count differs")
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    root_fd = os.open("/", flags)
    fd = root_fd
    opened = []
    try:
        for part in root.parts[1:] + tuple(relative.split("/"))[:-1]:
            nxt = os.open(part, flags, dir_fd=fd)
            opened.append(nxt)
            fd = nxt
        leaf = os.open(
            relative.split("/")[-1],
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=fd,
        )
        opened.append(leaf)
        before = os.fstat(leaf)
        if (
            not stat.S_ISREG(before.st_mode) or stat.S_IMODE(before.st_mode) != 0o644
            or before.st_nlink != 1 or before.st_size != size
        ):
            _fail("file custody differs: " + relative)
        chunks = []
        total = 0
        while total <= size:
            block = os.read(leaf, min(131_072, size + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
        raw = b"".join(chunks)
        if len(raw) != size or _sha256(raw) != digest or _identity(before) != _identity(os.fstat(leaf)):
            _fail("file bytes or stable identity differ: " + relative)
        return raw
    finally:
        for item in reversed(opened):
            os.close(item)
        os.close(root_fd)


def _pairs(pairs: object) -> Dict[str, object]:
    if type(pairs) is not list:
        _fail("JSON pair carrier differs")
    out: Dict[str, object] = {}
    for key, value in pairs:
        if type(key) is not str or key in out:
            _fail("duplicate or non-text JSON key")
        out[key] = value
    return out


def _decode(raw: bytes, name: str, *, terminal_lf: bool) -> object:
    if terminal_lf and not raw.endswith(b"\n"):
        _fail(name + " terminal LF differs")
    body = raw[:-1] if terminal_lf else raw
    try:
        result = json.loads(
            body.decode("ascii"), object_pairs_hook=_pairs,
            parse_float=Decimal,
            parse_constant=lambda item: _fail("nonfinite JSON: " + item),
        )
    except (UnicodeError, json.JSONDecodeError, decimal.InvalidOperation) as exc:
        raise NonconfirmatoryRouteV2Error(name + " is not strict JSON") from exc
    if _canonical(result) != body:
        _fail(name + " is not canonical JSON")
    return result


def _dict(value: object, name: str) -> Dict[str, object]:
    if type(value) is not dict:
        _fail(name + " must be exact object")
    return value


def _keys(value: Dict[str, object], names: Tuple[str, ...], label: str) -> None:
    if set(value) != set(names):
        _fail(label + " key roster differs")


def _plain(value: object) -> object:
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) in (tuple, list):
        return [_plain(item) for item in value]
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise TypeError("canonical mapping keys must be exact text")
        return {key: _plain(item) for key, item in value.items()}
    if type(value) in (FilePin, WholeMethodSuccessorBinding, NonconfirmatoryRouteV2Receipt):
        return {item.name: _plain(getattr(value, item.name)) for item in fields(value)}
    raise TypeError("value is outside the route V2 canonical grammar")


def _pin(path: str, size: int, digest: str) -> FilePin:
    result = FilePin(path, size, digest)
    _validate_pin(result)
    return result


def _validate_pin(value: object) -> FilePin:
    if type(value) is not FilePin:
        raise TypeError("file pin must have exact type")
    _safe_relative(value.path)
    if type(value.byte_count) is not int or value.byte_count <= 0:
        _fail("file byte count differs")
    _exact_sha(value.sha256, "file digest")
    return value


def _load_v1(root: Path) -> ModuleType:
    raw = _capture(root, V1_SOURCE_PATH, V1_SOURCE_BYTES, V1_SOURCE_SHA256, MAX_SOURCE_BYTES)
    name = "_formal_test28_30_route_v2_bound_v1"
    missing = object()
    prior = sys.modules.get(name, missing)
    module = ModuleType(name)
    module.__file__ = str(root / V1_SOURCE_PATH)
    module.__package__ = ""
    try:
        sys.modules[name] = module
        exec(compile(raw, module.__file__, "exec", dont_inherit=True), module.__dict__)
        if type(module) is not ModuleType:
            _fail("captured V1 module differs")
        return module
    finally:
        if prior is missing:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = prior


def _validate_plain_pin(value: object, expected: Tuple[str, int, str], label: str) -> Dict[str, object]:
    item = _dict(value, label)
    _keys(item, ("path", "byte_count", "sha256"), label)
    if (
        type(item["path"]) is not str or type(item["byte_count"]) is not int
        or type(item["sha256"]) is not str
        or (item["path"], item["byte_count"], item["sha256"]) != expected
    ):
        _fail(label + " accepted pin differs")
    _safe_relative(item["path"])
    _exact_sha(item["sha256"], label + " digest")
    return item


def _validate_cp63_plain(value: object) -> Dict[str, object]:
    item = _dict(value, "CP63 binding")
    keys = (
        "fixture", "runner_source", "independent_source",
        "acceptance_receipt_schema", "acceptance_receipt_sha256",
        "acceptance_receipt_canonical_byte_count",
        "acceptance_receipt_canonical_plain_sha256", "semantic_pin_receipt_sha256",
        "recomputation_record_sha256", "recomputation_public_sha256",
        "recomputation_canonical_plain_sha256", "row_count",
        "repetitions_per_row", "launch_count", "estimand_count",
        "observable_estimand_count", "rejection_first_attempt_estimand_count",
        "selected_feature_estimand_count",
        "historical_nonconfirmatory_execution_receipt_revalidated",
        "fresh_execution_performed_here", "confirmatory_evidence",
    )
    _keys(item, keys, "CP63 binding")
    _validate_plain_pin(item["fixture"], (
        "research/fixtures/cp50_test28_mixed_initializer_v26.json", 7_087_027,
        "7faed3c5b07415fbc45fec02d026e36d465819a38e9187369bf0a42a91c29f68",
    ), "CP63 fixture")
    _validate_plain_pin(item["runner_source"], (
        "src/heterodiff/evaluation/mixed_initializer_test28_runner_recomputation_rehearsal.py",
        83_080, "27259edf2557a21b2527595eed7a954fc697755935e4a3deaeeb169765ba1c9c",
    ), "CP63 runner")
    _validate_plain_pin(item["independent_source"], (
        "src/heterodiff/evaluation/mixed_initializer_test28_independent_recomputation.py",
        94_515, "5df076a008d8fe6848dc72083e2563e622c136ce0159441dd69db04c3b1cb9dc",
    ), "CP63 independent")
    expected = {
        "acceptance_receipt_schema": "cp63-test28-16x2-acceptance-receipt-v1",
        "acceptance_receipt_sha256": "2b2f41f14424ddb164b6db793991ece8b222a4e4295d7e0143c6b6496c50097b",
        "acceptance_receipt_canonical_byte_count": 24_810,
        "acceptance_receipt_canonical_plain_sha256": "83113460c4a4963ea815a2c54b9f1f7a8e2c1fbe7d4698fbb56a0f7addc1cf4d",
        "semantic_pin_receipt_sha256": "d7dfdae440b3b26b289279ccdda6e665fe43fee965c0836fe1d6dac91ce8d5e7",
        "recomputation_record_sha256": "870b89d2252dd5e62fc0c10982d5d2f194402b2a941c4c7bd8a0b6214a2832dc",
        "recomputation_public_sha256": "895b3afbe514158fdfbc3c3d2ae67175cdab2a5834cbf25b00297e69aa179406",
        "recomputation_canonical_plain_sha256": "4c281147b68adc5a83ddd88bab73c42cef619498a13a7f234acb4cd886a40ee7",
        "row_count": 16, "repetitions_per_row": 2, "launch_count": 32,
        "estimand_count": 554, "observable_estimand_count": 72,
        "rejection_first_attempt_estimand_count": 170,
        "selected_feature_estimand_count": 312,
        "historical_nonconfirmatory_execution_receipt_revalidated": True,
        "fresh_execution_performed_here": False, "confirmatory_evidence": False,
    }
    for key, expected_value in expected.items():
        actual = item[key]
        if type(actual) is not type(expected_value) or actual != expected_value:
            _fail("CP63 accepted value differs: " + key)
    return item


def _validate_two_plain(value: object) -> Dict[str, object]:
    item = _dict(value, "two-macrostep binding")
    keys = (
        "wrapper_source", "parent_sources", "wrapper_schema_version", "predicate",
        "report_sha256", "ordered_word_pair_cases_checked",
        "distinct_input_sha256_count", "distinct_report_sha256_count",
        "compiled_from_captured_bytes_only", "parent_source_bytes_hash_bound",
        "source_identities_stable", "fresh_execution_performed_here",
        "confirmatory_evidence",
    )
    _keys(item, keys, "two-macrostep binding")
    _validate_plain_pin(item["wrapper_source"], (
        "research/diagnostics/formal_test29_test30_two_macrostep_parent_custody_hash_first_v1.py",
        12_105, "e71f145bc73b47a8d6a19329e05989523d0ca14d5726c4b02a8ec0e07f9a455e",
    ), "two-macrostep wrapper")
    parents = item["parent_sources"]
    if type(parents) is not list or len(parents) != 4:
        _fail("two-macrostep parent roster differs")
    expected_parents = (
        ("src/heterodiff/evaluation/formal_test29_test30_two_macrostep_path_qualification.py", 59_285, "d1c3013aa0f4e7b31e19cef98d4aa5edf7991c5b8634dbfe091f8053b1808176"),
        ("src/heterodiff/evaluation/formal_test29_test30_single_macrostep_integration.py", 61_434, "e2f57ede06cb432f8507eb32eead7a77fbfc8d8d44cc7725a941182e7aedd0c7"),
        ("src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py", 52_186, "308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089"),
        ("src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py", 42_349, "373ef98c3605e0c0211da8dbc8782f2517cd5976026980e4fcd24435670839e0"),
    )
    for ordinal, (row, expected) in enumerate(zip(parents, expected_parents)):
        _validate_plain_pin(row, expected, "two-macrostep parent %d" % ordinal)
    expected = {
        "wrapper_schema_version": "formal-test29-test30-two-macrostep-parent-custody-hash-first-v1",
        "predicate": "SYNTHETIC_SUPPLIED_INPUT_TWO_MACROSTEP_ROLLING_LINEAGE_PATH_VALIDATED",
        "report_sha256": "2a278585373d017b3b60bed28dcbc0ab3830f72c0512891658fc2ab54c666d53",
        "ordered_word_pair_cases_checked": 1024,
        "distinct_input_sha256_count": 1024,
        "distinct_report_sha256_count": 1024,
        "compiled_from_captured_bytes_only": True,
        "parent_source_bytes_hash_bound": True,
        "source_identities_stable": True,
        "fresh_execution_performed_here": True,
        "confirmatory_evidence": False,
    }
    for key, expected_value in expected.items():
        actual = item[key]
        if type(actual) is not type(expected_value) or actual != expected_value:
            _fail("two-macrostep accepted value differs: " + key)
    return item


def _historical_components(root: Path) -> Tuple[Dict[str, object], Dict[str, object]]:
    with _V1_EXECUTION_LOCK:
        module = _load_v1(root)
        cp63 = module._cp63_binding(root)
        two = module._two_macrostep_binding(root)
        module._validate_cp63_binding(cp63)
        module._validate_two_macrostep_binding(two)
        cp63_plain = _validate_cp63_plain(module._plain_json_value(cp63))
        two_plain = _validate_two_plain(module._plain_json_value(two))
    if (
        cp63_plain.get("row_count") != 16
        or cp63_plain.get("repetitions_per_row") != 2
        or cp63_plain.get("launch_count") != 32
        or cp63_plain.get("estimand_count") != 554
        or cp63_plain.get("historical_nonconfirmatory_execution_receipt_revalidated") is not True
        or cp63_plain.get("fresh_execution_performed_here") is not False
        or cp63_plain.get("confirmatory_evidence") is not False
    ):
        _fail("historical CP63 boundary differs")
    if (
        two_plain.get("ordered_word_pair_cases_checked") != 1024
        or two_plain.get("distinct_input_sha256_count") != 1024
        or two_plain.get("distinct_report_sha256_count") != 1024
        or two_plain.get("fresh_execution_performed_here") is not True
        or two_plain.get("confirmatory_evidence") is not False
    ):
        _fail("fresh Test29/Test30 boundary differs")
    return cp63_plain, two_plain


def _whole_binding(root: Path) -> WholeMethodSuccessorBinding:
    raw = _capture(root, WHOLE_MACHINE_PATH, WHOLE_MACHINE_BYTES, WHOLE_MACHINE_SHA256, MAX_MACHINE_BYTES)
    review = _capture(root, WHOLE_REVIEW_PATH, WHOLE_REVIEW_BYTES, WHOLE_REVIEW_SHA256, MAX_SOURCE_BYTES)
    if (
        b"**GO \xe2\x80\x94 authorize exactly the existing timetable registration**" not in review
        or b"P0/P1/P2 = 0/0/0" not in review
        or b"Produce whole-method beta: initializer, continuous path, jump/edit law" not in review
    ):
        _fail("whole-method independent GO review boundary differs")
    document = _dict(_decode(raw, "whole-method machine", terminal_lf=True), "whole-method machine")
    supplied_record = document.get("record_sha256")
    unsigned = dict(document)
    unsigned.pop("record_sha256", None)
    if (
        supplied_record != WHOLE_MACHINE_RECORD_SHA256
        or _domain(WHOLE_MACHINE_RECORD_DOMAIN, unsigned) != WHOLE_MACHINE_RECORD_SHA256
    ):
        _fail("whole-method machine self-record differs")
    semantics = _dict(document.get("semantics"), "whole semantics")
    core = _dict(semantics.get("core"), "whole core")
    receipt = _dict(semantics.get("receipt"), "whole receipt")
    constants = _dict(semantics.get("supplied_input_constants"), "whole supplied input")
    route = _dict(document.get("route_binding"), "whole route binding")
    if _sha256(_canonical(core) + b"\n") != WHOLE_CORE_SHA256 or semantics.get("core_output_sha256") != WHOLE_CORE_SHA256:
        _fail("whole core digest differs")
    receipt_payload = dict(receipt)
    supplied_receipt = receipt_payload.pop("receipt_sha256", None)
    if supplied_receipt != WHOLE_RECEIPT_SHA256 or _domain(
        "heterodiff-b12-whole-method-beta-successor-receipt-v1", receipt_payload
    ) != WHOLE_RECEIPT_SHA256:
        _fail("whole receipt semantic digest differs")
    input_payload = {
        "checkpoint_step": constants.get("checkpoint_step"),
        "initializer_row_ordinal": constants.get("initializer_row_ordinal"),
        "initializer_seed": int(constants.get("initializer_seed_hex"), 16)
        if type(constants.get("initializer_seed_hex")) is str else None,
        "path_first_word": constants.get("path_words", [None, None])[0]
        if type(constants.get("path_words")) is list and len(constants.get("path_words")) == 2 else None,
        "path_second_word": constants.get("path_words", [None, None])[1]
        if type(constants.get("path_words")) is list and len(constants.get("path_words")) == 2 else None,
        "schema_version": constants.get("schema_version"),
    }
    if constants.get("supplied_input_sha256") != WHOLE_SUPPLIED_INPUT_SHA256 or _domain(
        "heterodiff-b12-whole-method-nonconfirmatory-input-v1", input_payload
    ) != WHOLE_SUPPLIED_INPUT_SHA256:
        _fail("whole supplied-input semantic digest differs")
    state = _dict(core.get("initializer_path_state"), "initializer-path state")
    state_payload = dict(state)
    transform_sha = state_payload.pop("transform_sha256", None)
    occurrences = state.get("occurrences")
    if type(occurrences) is not list:
        _fail("initializer-path occurrence roster differs")
    if _domain("heterodiff-b12-beta-integrated-path-state-v1", occurrences) != WHOLE_INITIAL_STATE_SHA256:
        _fail("derived initial-state digest differs")
    if transform_sha != WHOLE_TRANSFORM_SHA256 or _domain(
        "heterodiff-b12-beta-initializer-path-transform-v1", state_payload
    ) != WHOLE_TRANSFORM_SHA256:
        _fail("initializer transform digest differs")
    path = _dict(core.get("integrated_path"), "integrated path")
    path_payload = dict(path)
    path_report = path_payload.pop("path_report_sha256", None)
    path_input_payload = {
        "initial_state_sha256": WHOLE_INITIAL_STATE_SHA256,
        "path_policy_id": path.get("path_policy_id"),
        "selected_configuration_sha256": WHOLE_SELECTED_CONFIGURATION_SHA256,
        "transform_sha256": WHOLE_TRANSFORM_SHA256,
        "words": [2, 27],
    }
    if _domain("heterodiff-b12-beta-integrated-path-input-v1", path_input_payload) != WHOLE_PATH_INPUT_SHA256:
        _fail("integrated path-input digest differs")
    if path_report != WHOLE_PATH_REPORT_SHA256 or _domain(
        "heterodiff-b12-beta-integrated-path-report-v1", path_payload
    ) != WHOLE_PATH_REPORT_SHA256:
        _fail("integrated path-report digest differs")
    custody = _dict(core.get("custody_chain"), "whole custody chain")
    custody_payload = dict(custody)
    custody_sha = custody_payload.pop("custody_chain_sha256", None)
    if custody_sha != WHOLE_CUSTODY_SHA256 or _domain(
        "heterodiff-b12-beta-end-to-end-custody-v1", custody_payload
    ) != WHOLE_CUSTODY_SHA256:
        _fail("whole end-to-end custody digest differs")
    expected = {
        "authoritative_qualification_requires_isolated_validator": True,
        "custody_chain_sha256": WHOLE_CUSTODY_SHA256,
        "derived_initial_state_sha256": WHOLE_INITIAL_STATE_SHA256,
        "direct_public_api_custody_authenticated": False,
        "gate_b0_feature_complete_eligible": False,
        "independent_output_sha256": WHOLE_CORE_SHA256,
        "initializer_to_path_integrated": True,
        "integrated_path_input_sha256": WHOLE_PATH_INPUT_SHA256,
        "integrated_path_report_sha256": WHOLE_PATH_REPORT_SHA256,
        "isolated_hash_first_validator_pass": True,
        "open_residual_slot_count": 50,
        "predecessor_machine_record_sha256": WHOLE_PREDECESSOR_RECORD_SHA256,
        "predecessor_receipt_sha256": WHOLE_PREDECESSOR_RECEIPT_SHA256,
        "selected_configuration_sha256": WHOLE_SELECTED_CONFIGURATION_SHA256,
        "stable_initializer_execution_sha256": WHOLE_STABLE_INITIALIZER_SHA256,
        "supplied_input_sha256": WHOLE_SUPPLIED_INPUT_SHA256,
        "test28_initializer_admissible": True,
        "transform_policy_id": WHOLE_TRANSFORM_POLICY,
        "transform_sha256": WHOLE_TRANSFORM_SHA256,
    }
    for key, value in expected.items():
        actual = route.get(key)
        receipt_actual = receipt.get(key) if key in receipt else None
        if (
            type(actual) is not type(value) or actual != value
            or (
                key in receipt
                and (type(receipt_actual) is not type(value) or receipt_actual != value)
            )
        ):
            _fail("whole route/receipt accepted value differs: " + key)
    if (
        core.get("formal_test_states") != {"28": "OPEN", "29": "OPEN", "30": "PENDING"}
        or path.get("initializer_to_path_integrated") is not True
        or path.get("bounded_two_macrostep_path_integrated") is not True
        or path.get("test29_route_and_lineage_semantics_integrated") is not True
        or path.get("test30_heun_primitive_integrated") is not True
        or path.get("test28_initializer_admissible") is not True
        or path.get("formal_test28_production_law_admissible") is not False
        or any(path.get(name) is not False for name in (
            "formal_test_28_closed", "formal_test_29_closed", "formal_test_30_closed",
            "arbitrary_length_general_strang_path_integrated", "upstream_runtime_executed",
        ))
        or core.get("nonclaims") != {
            "arbitrary_length_general_path": False, "b12_closed": False,
            "confirmatory_evidence": False, "gate_b0_feature_complete": False,
            "direct_public_api_custody_authenticated": False,
            "production_receipt": False, "real_residual_receipts_present": 0,
            "upstream_external_runtime": False,
        }
        or len(core.get("open_residual_predicate_ids", [])) != 50
    ):
        _fail("whole structural admissibility/nonclaim boundary differs")
    effects = document.get("effects")
    if effects != {
        "blocker_delta": 0, "data_accessed": False, "field_delta": 0,
        "formal_test_delta": 0, "network_used": False, "result_delta": 0,
        "science_executed": False, "tracker_or_ledger_edited": False,
        "training_executed": False, "upstream_runtimes_executed": False,
    } or core.get("effects") != effects:
        _fail("whole zero-effect boundary differs")
    result = WholeMethodSuccessorBinding(
        machine=_pin(WHOLE_MACHINE_PATH, WHOLE_MACHINE_BYTES, WHOLE_MACHINE_SHA256),
        independent_review=_pin(WHOLE_REVIEW_PATH, WHOLE_REVIEW_BYTES, WHOLE_REVIEW_SHA256),
        machine_record_sha256=WHOLE_MACHINE_RECORD_SHA256,
        receipt_sha256=WHOLE_RECEIPT_SHA256,
        core_output_sha256=WHOLE_CORE_SHA256,
        supplied_input_sha256=WHOLE_SUPPLIED_INPUT_SHA256,
        stable_initializer_execution_sha256=WHOLE_STABLE_INITIALIZER_SHA256,
        selected_configuration_sha256=WHOLE_SELECTED_CONFIGURATION_SHA256,
        transform_policy_id=WHOLE_TRANSFORM_POLICY,
        transform_sha256=WHOLE_TRANSFORM_SHA256,
        derived_initial_state_sha256=WHOLE_INITIAL_STATE_SHA256,
        integrated_path_input_sha256=WHOLE_PATH_INPUT_SHA256,
        integrated_path_report_sha256=WHOLE_PATH_REPORT_SHA256,
        custody_chain_sha256=WHOLE_CUSTODY_SHA256,
        predecessor_machine_record_sha256=WHOLE_PREDECESSOR_RECORD_SHA256,
        predecessor_receipt_sha256=WHOLE_PREDECESSOR_RECEIPT_SHA256,
        isolated_hash_first_validator_pass=True,
        independent_review_go=True,
        test28_initializer_admissible=True,
        initializer_to_path_integrated=True,
        bounded_two_macrostep_path_integrated=True,
        test29_route_and_lineage_semantics_integrated=True,
        test30_heun_primitive_integrated=True,
        separate_recomputation_bytes_equal=True,
        open_residual_slot_count=50,
        confirmatory_evidence=False,
    )
    return _validate_whole(result)


def _validate_whole(value: object) -> WholeMethodSuccessorBinding:
    if type(value) is not WholeMethodSuccessorBinding:
        raise TypeError("whole binding must have exact type")
    _validate_pin(value.machine)
    _validate_pin(value.independent_review)
    for item in fields(value):
        if item.name.endswith("sha256"):
            _exact_sha(getattr(value, item.name), item.name)
    for name in (
        "isolated_hash_first_validator_pass", "independent_review_go",
        "test28_initializer_admissible", "initializer_to_path_integrated",
        "bounded_two_macrostep_path_integrated",
        "test29_route_and_lineage_semantics_integrated",
        "test30_heun_primitive_integrated", "separate_recomputation_bytes_equal",
        "confirmatory_evidence",
    ):
        if type(getattr(value, name)) is not bool:
            raise TypeError(name + " must be exact bool")
    if type(value.open_residual_slot_count) is not int:
        raise TypeError("open residual slot count must be exact int")
    if type(value.transform_policy_id) is not str:
        raise TypeError("transform policy must be exact text")
    expected = WholeMethodSuccessorBinding(
        _pin(WHOLE_MACHINE_PATH, WHOLE_MACHINE_BYTES, WHOLE_MACHINE_SHA256),
        _pin(WHOLE_REVIEW_PATH, WHOLE_REVIEW_BYTES, WHOLE_REVIEW_SHA256),
        WHOLE_MACHINE_RECORD_SHA256, WHOLE_RECEIPT_SHA256, WHOLE_CORE_SHA256,
        WHOLE_SUPPLIED_INPUT_SHA256, WHOLE_STABLE_INITIALIZER_SHA256,
        WHOLE_SELECTED_CONFIGURATION_SHA256, WHOLE_TRANSFORM_POLICY,
        WHOLE_TRANSFORM_SHA256, WHOLE_INITIAL_STATE_SHA256,
        WHOLE_PATH_INPUT_SHA256, WHOLE_PATH_REPORT_SHA256, WHOLE_CUSTODY_SHA256,
        WHOLE_PREDECESSOR_RECORD_SHA256, WHOLE_PREDECESSOR_RECEIPT_SHA256,
        True, True, True, True, True, True, True, True, 50, False,
    )
    if value != expected:
        _fail("whole-method successor binding differs")
    return value


def _subject(receipt: NonconfirmatoryRouteV2Receipt) -> Dict[str, object]:
    return {
        "cp63_test28": _plain(_validate_cp63_plain(receipt.cp63_test28)),
        "route_component_ids": _plain(receipt.route_component_ids),
        "test29_test30_two_macrostep": _plain(_validate_two_plain(receipt.test29_test30_two_macrostep)),
        "whole_method_successor": _plain(receipt.whole_method_successor),
    }


def _validate_receipt(value: object) -> NonconfirmatoryRouteV2Receipt:
    if type(value) is not NonconfirmatoryRouteV2Receipt:
        raise TypeError("route receipt must have exact type")
    _validate_cp63_plain(value.cp63_test28)
    _validate_two_plain(value.test29_test30_two_macrostep)
    _validate_whole(value.whole_method_successor)
    for name in (
        "formal_tests_closed", "fields_closed", "blockers_closed",
        "result_slots_filled", "proposed_timetable_task_closures",
        "applied_timetable_task_closures",
    ):
        if type(getattr(value, name)) is not int:
            raise TypeError(name + " must be exact int")
    for name in (
        "schema_version", "state", "route_subject_sha256", "formal_test_28_state",
        "formal_test_29_state", "formal_test_30_state", "proposed_timetable_task",
        "receipt_sha256",
    ):
        if type(getattr(value, name)) is not str:
            raise TypeError(name + " must be exact text")
    if type(value.route_component_ids) is not tuple or any(
        type(item) is not str for item in value.route_component_ids
    ):
        raise TypeError("route component roster must be exact text tuple")
    if value.route_subject_sha256 != _sha256(SUBJECT_DOMAIN + _canonical(_subject(value))):
        _fail("route subject digest differs")
    if (
        value.schema_version != SCHEMA_VERSION or value.state != STATE
        or value.route_component_ids != (
            "CP63_TEST28_HISTORICAL_16X2_32_LAUNCH_554_RECOMPUTATION",
            "HASH_FIRST_TEST29_TEST30_FRESH_1024_CASE_ROUTE",
            "REPAIRED_SELECTED_CONFIGURATION_TO_INTEGRATED_PATH_SUCCESSOR_GO",
        )
        or value.route_components_jointly_bound is not True
        or (value.formal_test_28_state, value.formal_test_29_state, value.formal_test_30_state)
        != ("OPEN", "OPEN", "PENDING")
        or value.formal_tests_closed != 0 or value.b12_closed is not False
        or any(item != 0 for item in (value.fields_closed, value.blockers_closed, value.result_slots_filled))
        or any(item is not False for item in (
            value.runtime_selected, value.data_contacted, value.network_contacted,
            value.entropy_consumed, value.science_executed, value.authority_asserted,
            value.production_receipt_issued, value.tracker_or_ledger_edited,
        ))
        or value.proposed_timetable_task != PROPOSED_TIMETABLE_TASK
        or value.proposed_timetable_task_closures != 1
        or value.applied_timetable_task_closures != 0
    ):
        _fail("route V2 state/nonclaim boundary differs")
    _exact_sha(value.receipt_sha256, "route receipt digest")
    if value.receipt_sha256 != _sha256(
        RECEIPT_DOMAIN + _canonical(_plain(replace(value, receipt_sha256=ZERO_SHA256)))
    ):
        _fail("route receipt digest differs")
    return value


def run_nonconfirmatory_test28_30_route_v2(project_root: str) -> NonconfirmatoryRouteV2Receipt:
    root = _root(project_root)
    cp63, two = _historical_components(root)
    whole = _whole_binding(root)
    provisional = NonconfirmatoryRouteV2Receipt(
        SCHEMA_VERSION, STATE, cp63, two, whole,
        (
            "CP63_TEST28_HISTORICAL_16X2_32_LAUNCH_554_RECOMPUTATION",
            "HASH_FIRST_TEST29_TEST30_FRESH_1024_CASE_ROUTE",
            "REPAIRED_SELECTED_CONFIGURATION_TO_INTEGRATED_PATH_SUCCESSOR_GO",
        ),
        ZERO_SHA256, True, "OPEN", "OPEN", "PENDING", 0, False, 0, 0, 0,
        False, False, False, False, False, False, False, False,
        PROPOSED_TIMETABLE_TASK, 1, 0, ZERO_SHA256,
    )
    subject_sha = _sha256(SUBJECT_DOMAIN + _canonical(_subject(provisional)))
    with_subject = replace(provisional, route_subject_sha256=subject_sha)
    receipt_sha = _sha256(
        RECEIPT_DOMAIN + _canonical(_plain(with_subject))
    )
    return _validate_receipt(replace(with_subject, receipt_sha256=receipt_sha))


def validate_nonconfirmatory_test28_30_route_v2_receipt(
    receipt: NonconfirmatoryRouteV2Receipt,
) -> NonconfirmatoryRouteV2Receipt:
    return _validate_receipt(receipt)


def route_v2_receipt_canonical_json_bytes(receipt: NonconfirmatoryRouteV2Receipt) -> bytes:
    return _canonical(_plain(_validate_receipt(receipt))) + b"\n"


__all__ = (
    "FilePin", "NonconfirmatoryRouteV2Error", "NonconfirmatoryRouteV2Receipt",
    "PROPOSED_TIMETABLE_TASK", "SCHEMA_VERSION", "STATE",
    "WholeMethodSuccessorBinding", "route_v2_receipt_canonical_json_bytes",
    "run_nonconfirmatory_test28_30_route_v2",
    "validate_nonconfirmatory_test28_30_route_v2_receipt",
)
