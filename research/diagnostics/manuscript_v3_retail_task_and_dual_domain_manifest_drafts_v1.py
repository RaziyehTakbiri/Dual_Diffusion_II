#!/usr/bin/env python3
"""Read-only validator for the stopped dual-domain manifest draft package."""

from __future__ import annotations

import ast
import hashlib
import itertools
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from types import ModuleType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


SCHEMA = "heterodiff-manuscript-v3-retail-task-and-dual-domain-manifest-drafts-v1"
STATE = "RETAIL_TASK_AND_DUAL_DOMAIN_MANIFEST_DRAFTS_SYNTHETICALLY_VALIDATED"
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
REPORTED_DATE = "2026-08-31"
CONTROL_PREDICATE = (
    "RETAIL_TASK_SCHEMA_AND_DUAL_DOMAIN_SNAPSHOT_SPLIT_MANIFEST_DRAFTS_VALIDATED"
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = "src/heterodiff/data/dual_domain_snapshot_split_manifest_drafts.py"
HUMAN_PATH = "PROJECT_RETAIL_TASK_AND_DUAL_DOMAIN_MANIFEST_DRAFTS.md"
MACHINE_PATH = (
    "research/fixtures/manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.json"
)
VALIDATOR_PATH = (
    "research/diagnostics/manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.py"
)
TEST_PATH = (
    "tests/unit/test_manuscript_v3_retail_task_and_dual_domain_manifest_drafts_v1.py"
)
EXPECTED_SOURCE_SHA256 = (
    "701616d9746f53e6a4082a147363e4fab98f3dd9cccc30dcf2c73fe98a2350c8"
)

AUTHORITY_TEXT = (
    "Okay, sounds good. What I want you to do is to set aside a significant "
    "portion of work to do such that you are busy for around 8 hours, because "
    "I am going to sleep, and dont want my absence to make you idle."
)
AUTHORITY_SHA256 = "44ed1336dd467043e3daebe7ad85093c5ab954921a895483153c98cb6d32bb9a"


class ValidationError(RuntimeError):
    pass


INPUT_SPECS: Tuple[Mapping[str, Any], ...] = (
    {"role":"EXECUTION_PREREGISTRATION_HUMAN","path":"manuscript_v3/execution_preregistration.md","bytes":22491,"raw_sha256":"a68215e77fe7d20dd0738e9f758f6037c2cd69304c98e92670ded3af3e00b64e"},
    {"role":"EXECUTION_PREREGISTRATION_MACHINE","path":"research/fixtures/manuscript_v3_execution_preregistration_v1.json","bytes":39771,"raw_sha256":"edd572fc8d8c1b72ad3bc947c4427b79095d45b4d9f44371c5806066d71b0706"},
    {"role":"PREEXECUTION_CLOSURE_HUMAN","path":"manuscript_v3/execution_preregistration_preexecution_closure_v2.md","bytes":14938,"raw_sha256":"fb1218e86b4a4fdf434ed6b37b3ccf81e2698cc3fb46e331b5a52f279fd24a3d"},
    {"role":"PREEXECUTION_CLOSURE_MACHINE","path":"research/fixtures/manuscript_v3_execution_preregistration_preexecution_closure_v2.json","bytes":24571,"raw_sha256":"11329efc97d844f5a39223f170e8c4d5ea5341756ed6f89d9e40bbf4e0c529db"},
    {"role":"PROSPECTIVE_SEAL_HUMAN","path":"PROJECT_TEST_DATA_PROSPECTIVE_SEAL.md","bytes":7078,"raw_sha256":"ad58c5fcb9d47531a7af041eb59f71386fd42a81b1fe31701df167f064f951c2"},
    {"role":"PROSPECTIVE_SEAL_MACHINE","path":"research/fixtures/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.json","bytes":8461,"raw_sha256":"0357fc48394d5888632e3e2d7f5c9180e683141ebc10bef3dec9879a58cdf0e8"},
    {"role":"PROSPECTIVE_SEAL_VALIDATOR","path":"research/diagnostics/manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py","bytes":32156,"raw_sha256":"3647c367506519149d5df60dc2dcfb07a8f5dc976526b88700321b0de89a2258"},
    {"role":"PROSPECTIVE_SEAL_HOSTILE_TEST","path":"tests/unit/test_manuscript_v3_test_data_prospective_no_acquisition_seal_v1.py","bytes":16698,"raw_sha256":"2285525223f42154553a0302bb46a8f04f0ff7ff35233906a37f4f1a9bf47403"},
    {"role":"PHYSIONET_TASK_HUMAN","path":"PROJECT_PHYSIONET_TASK_SUPPORT_ROUTE_DRAFT.md","bytes":10756,"raw_sha256":"d41f107f92a8cda85ff1c2afab7e6f38e6fcc46223214d34e5a3cdbf6666be0b"},
    {"role":"PHYSIONET_TASK_MACHINE","path":"research/fixtures/manuscript_v3_physionet_task_support_route_draft_v1.json","bytes":12418,"raw_sha256":"2934e6499fb3645e5c8bcd95185594d11e0873bce06a68102765a9168e9e5f9b"},
    {"role":"PHYSIONET_TASK_VALIDATOR","path":"research/diagnostics/manuscript_v3_physionet_task_support_route_draft_v1.py","bytes":26115,"raw_sha256":"c44767152f1fb9ddd53066cc6991122d6a3c46fc419eaff4f9c2b5d46f10ad63"},
    {"role":"PHYSIONET_TASK_HOSTILE_TEST","path":"tests/unit/test_manuscript_v3_physionet_task_support_route_draft_v1.py","bytes":14201,"raw_sha256":"bd8b7c0d7a93eebf3f918b98fd8f8b04802eacc257a97bb88ab219f6fc748356"},
    {"role":"PHYSIONET_SPLIT_HUMAN","path":"PROJECT_PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN.md","bytes":10761,"raw_sha256":"2d84753fe87032a81d377a469f858f1702b14474371bfd2d147fd87824bb4b7a"},
    {"role":"PHYSIONET_SPLIT_MACHINE","path":"research/fixtures/manuscript_v3_physionet_patient_disjoint_split_design_v1.json","bytes":16543,"raw_sha256":"a9fc01ae42ba7942e6c61def5120d6497b74fc99c82b0c5b68188f221b4b68a8"},
    {"role":"PHYSIONET_SPLIT_VALIDATOR","path":"research/diagnostics/manuscript_v3_physionet_patient_disjoint_split_design_v1.py","bytes":35894,"raw_sha256":"429e4e9291bb42172a6de3b664b13938a537a8840e14ab0f8f4d6e963072a91e"},
    {"role":"PHYSIONET_SPLIT_HOSTILE_TEST","path":"tests/unit/test_manuscript_v3_physionet_patient_disjoint_split_design_v1.py","bytes":15720,"raw_sha256":"10faf21f66129330eef239ca3e561ecbddee78779a4849e5d60df07624c59982"},
    {"role":"RETAIL_SPLIT_HUMAN","path":"PROJECT_RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN.md","bytes":11226,"raw_sha256":"49a38fbe8bfdbc2fcb93de766f7280ba8affd18b2ebedbcc004d079550b752d1"},
    {"role":"RETAIL_SPLIT_MACHINE","path":"research/fixtures/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json","bytes":13409,"raw_sha256":"b27086c5979d2f7018b4b8b50b3fffacf03b3fe2691d60567bc42b179d53e98b"},
    {"role":"RETAIL_SPLIT_VALIDATOR","path":"research/diagnostics/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py","bytes":38492,"raw_sha256":"c377c87ae74ee3a4bfc0dd8f695e0df3531c3eec2c080f5b81379e852424a22e"},
    {"role":"RETAIL_SPLIT_HOSTILE_TEST","path":"tests/unit/test_manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py","bytes":24025,"raw_sha256":"99ecada07b8325b25e7d227bf9bb5c6e38957619115a7040c636dbdc33cb7109"},
)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_payload_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise ValidationError("noncanonical value") from error


def record_sha256(record: Mapping[str, Any]) -> str:
    schema = record.get("schema_version")
    if type(schema) is not str or not schema.isascii():
        raise ValidationError("machine schema invalid")
    payload = dict(record)
    payload.pop("record_sha256", None)
    return _sha256((schema + "\0").encode("ascii") + _canonical_payload_bytes(payload))


def canonical_machine_bytes(record: Mapping[str, Any]) -> bytes:
    return _canonical_payload_bytes(record) + b"\n"


def _strict_equal(actual: Any, expected: Any, label: str) -> None:
    if type(actual) is not type(expected):
        raise ValidationError(label + " type mismatch")
    if type(expected) is dict:
        if set(actual) != set(expected):
            raise ValidationError(label + " key roster mismatch")
        for key in expected:
            _strict_equal(actual[key], expected[key], label + "." + key)
        return
    if type(expected) is list:
        if len(actual) != len(expected):
            raise ValidationError(label + " length mismatch")
        for index, (observed, wanted) in enumerate(zip(actual, expected)):
            _strict_equal(observed, wanted, label + "[" + str(index) + "]")
        return
    if actual != expected:
        raise ValidationError(label + " value mismatch")


def _safe_path(root: Path, relative_path: str) -> Path:
    if type(relative_path) is not str:
        raise ValidationError("path type invalid")
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or not pure.parts or any(part in ("", ".", "..") for part in pure.parts):
        raise ValidationError("unsafe path")
    result = root.joinpath(*pure.parts)
    if result == root or root not in result.parents:
        raise ValidationError("path escaped root")
    return result


def _ancestor_snapshot(root: Path, path: Path) -> Tuple[Tuple[Any, ...], ...]:
    rows = []
    current = path.parent
    while True:
        status = current.lstat()
        if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
            raise ValidationError("ancestor custody invalid")
        rows.append((status.st_dev, status.st_ino, stat.S_IFMT(status.st_mode), stat.S_IMODE(status.st_mode), status.st_uid, status.st_gid))
        if current == root:
            break
        if root not in current.parents:
            raise ValidationError("ancestor escaped root")
        current = current.parent
    return tuple(reversed(rows))


def _fingerprint(status: os.stat_result) -> Tuple[Any, ...]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        stat.S_IMODE(status.st_mode),
        status.st_uid,
        status.st_gid,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _stable_read(root: Path, relative_path: str) -> bytes:
    path = _safe_path(root, relative_path)
    ancestors = _ancestor_snapshot(root, path)
    before_path = path.lstat()
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != 0o644
        or before_path.st_nlink != 1
    ):
        raise ValidationError("file custody invalid: " + relative_path)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        before_fd = os.fstat(descriptor)
        chunks = []
        while True:
            chunk = os.read(descriptor, 131072)
            if not chunk:
                break
            chunks.append(chunk)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    if not (_fingerprint(before_path) == _fingerprint(before_fd) == _fingerprint(after_fd) == _fingerprint(after_path)):
        raise ValidationError("file changed during stable read: " + relative_path)
    if ancestors != _ancestor_snapshot(root, path):
        raise ValidationError("ancestor changed during stable read")
    raw = b"".join(chunks)
    if len(raw) != after_fd.st_size:
        raise ValidationError("short read")
    return raw


def _binding(ordinal: int, role: str, path: str, raw: bytes) -> Dict[str, Any]:
    return {
        "ordinal": ordinal,
        "role": role,
        "path": path,
        "bytes": len(raw),
        "raw_sha256": _sha256(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "trailing_lf": raw.endswith(b"\n"),
    }


def _read_and_pin_inputs(root: Path) -> Dict[str, bytes]:
    pinned: Dict[str, bytes] = {}
    for spec in INPUT_SPECS:
        raw = _stable_read(root, spec["path"])
        if len(raw) != spec["bytes"] or _sha256(raw) != spec["raw_sha256"] or not raw.endswith(b"\n"):
            raise ValidationError("immutable predecessor mismatch: " + spec["path"])
        pinned[spec["path"]] = raw
    if len(pinned) != len(INPUT_SPECS):
        raise ValidationError("duplicate predecessor path")
    return pinned


def _scan_source(source_raw: bytes) -> None:
    try:
        text = source_raw.decode("utf-8")
        tree = ast.parse(text, filename=SOURCE_PATH)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValidationError("source parse failed") from error
    allowed_imports = {"__future__", "hashlib", "json", "typing"}
    banned_calls = {"open", "exec", "eval", "compile", "__import__", "input"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in allowed_imports:
                    raise ValidationError("source import forbidden")
        if isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in allowed_imports:
                raise ValidationError("source import-from forbidden")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in banned_calls:
            raise ValidationError("source effectful call forbidden")
    banned_tokens = (
        "subprocess", "socket", "urllib", "requests", "http://", "https://",
        "pathlib", "os.", "random", "secrets", "numpy.random", "torch", "pickle",
    )
    if any(token in text for token in banned_tokens):
        raise ValidationError("source banned token")


def load_qualified_source(root: Optional[Path] = None) -> ModuleType:
    workspace = ROOT if root is None else Path(root).resolve()
    pinned = _read_and_pin_inputs(workspace)
    source_raw = _stable_read(workspace, SOURCE_PATH)
    if _sha256(source_raw) != EXPECTED_SOURCE_SHA256:
        raise ValidationError("hard-pinned source differs before execution")
    if set(pinned) != {spec["path"] for spec in INPUT_SPECS}:
        raise ValidationError("predecessor pin set incomplete before execution")
    _scan_source(source_raw)
    module = ModuleType("dual_domain_snapshot_split_manifest_drafts_stable_bytes")
    module.__file__ = SOURCE_PATH
    code = compile(source_raw, SOURCE_PATH, "exec", dont_inherit=True)
    exec(code, module.__dict__)
    return module


def _json_from_pinned(pinned: Mapping[str, bytes], path: str) -> Dict[str, Any]:
    try:
        value = json.loads(pinned[path].decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("bound JSON invalid: " + path) from error
    if type(value) is not dict:
        raise ValidationError("bound JSON root invalid")
    return value


def _load_pinned_parent_module(
    workspace: Path,
    pinned: Mapping[str, bytes],
    relative_path: str,
    module_name: str,
) -> ModuleType:
    """Execute one already hard-pinned parent from its stable byte buffer."""

    if relative_path not in pinned:
        raise ValidationError("parent was not hard-pinned before execution")
    expected = [spec for spec in INPUT_SPECS if spec["path"] == relative_path]
    if len(expected) != 1 or _sha256(pinned[relative_path]) != expected[0]["raw_sha256"]:
        raise ValidationError("parent pin mismatch before execution")
    module = ModuleType(module_name)
    module.__file__ = str(_safe_path(workspace, relative_path))
    code = compile(pinned[relative_path], relative_path, "exec", dont_inherit=True)
    exec(code, module.__dict__)
    return module


def load_qualified_parent_splitters(
    root: Optional[Path] = None,
) -> Tuple[ModuleType, ModuleType]:
    workspace = ROOT if root is None else Path(root).resolve()
    pinned = _read_and_pin_inputs(workspace)
    phys_path = "research/diagnostics/manuscript_v3_physionet_patient_disjoint_split_design_v1.py"
    retail_path = "research/diagnostics/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py"
    return (
        _load_pinned_parent_module(workspace, pinned, phys_path, "pinned_physionet_split_parent"),
        _load_pinned_parent_module(workspace, pinned, retail_path, "pinned_retail_split_parent"),
    )


def _predecessor_contract_checks(pinned: Mapping[str, bytes]) -> Dict[str, Any]:
    prereg = _json_from_pinned(pinned, "research/fixtures/manuscript_v3_execution_preregistration_v1.json")
    phys_task = _json_from_pinned(pinned, "research/fixtures/manuscript_v3_physionet_task_support_route_draft_v1.json")
    phys_split = _json_from_pinned(pinned, "research/fixtures/manuscript_v3_physionet_patient_disjoint_split_design_v1.json")
    retail_split = _json_from_pinned(pinned, "research/fixtures/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json")
    if [row.get("domain_id") for row in prereg.get("domains", [])] != ["physionet-challenge-2012", "online-retail-ii"]:
        raise ValidationError("prereg domain roster mismatch")
    required_nulls = [
        prereg["domains"][0]["snapshot_version"], prereg["domains"][0]["raw_snapshot_sha256"],
        prereg["domains"][1]["snapshot_version"], prereg["domains"][1]["raw_snapshot_sha256"],
        prereg["split_and_leakage_plan"]["physionet_split_manifest_path"],
        prereg["split_and_leakage_plan"]["retail_split_manifest_path"],
        prereg["split_and_leakage_plan"]["retail_temporal_cutoff_and_window_rule"],
        prereg["split_and_leakage_plan"]["train_validation_test_proportions_or_counts"],
    ]
    if required_nulls != [None] * len(required_nulls):
        raise ValidationError("predecessor open/null seam changed")
    if phys_task["draft_identity"]["control_predicate"] != "PHYSIONET_TASK_SUPPORT_ROUTE_DRAFT_VALIDATED":
        raise ValidationError("PhysioNet task predicate mismatch")
    if phys_split["design_identity"]["algorithm_id"] != "PHYSIONET_PATIENT_HASH_HAMILTON_70_15_15_V1":
        raise ValidationError("PhysioNet algorithm mismatch")
    if phys_split["allocation_contract"]["numerators"] != [70, 15, 15] or phys_split["allocation_contract"]["denominator"] != 100:
        raise ValidationError("PhysioNet allocation mismatch")
    if retail_split["design_identity"]["algorithm_id"] != "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_HAMILTON_70_15_15_V1":
        raise ValidationError("Retail algorithm mismatch")
    if retail_split["hamilton_allocation_contract"]["numerators"] != [70, 15, 15] or retail_split["hamilton_allocation_contract"]["denominator"] != 100:
        raise ValidationError("Retail allocation mismatch")
    return {
        "preregistration_domain_roster_exact": True,
        "snapshot_and_split_target_values_still_null": True,
        "physionet_task_predicate_exact": True,
        "physionet_split_algorithm_exact": True,
        "retail_split_algorithm_exact": True,
        "both_allocation_contracts_exact_70_15_15_over_100": True,
    }


def _physionet_rows() -> list:
    return [
        {"record_ordinal": 0, "patient_id": "1"},
        {"record_ordinal": 1, "patient_id": "2"},
        {"record_ordinal": 2, "patient_id": "3"},
        {"record_ordinal": 3, "patient_id": "4"},
        {"record_ordinal": 4, "patient_id": "5"},
        {"record_ordinal": 5, "patient_id": "6"},
        {"record_ordinal": 6, "patient_id": "1"},
    ]


def _retail_rows() -> list:
    return [
        {"row_ordinal": index, "customer_key_hex": format(index + 1, "02x"), "timestamp_utc_microseconds": (index + 1) * 10}
        for index in range(10)
    ]


def _compare_one(
    new_callable: Any,
    parent_callable: Any,
    rows: Any,
    label: str,
) -> None:
    outcomes = []
    for callable_value in (new_callable, parent_callable):
        try:
            outcomes.append(("PASS", callable_value(copy_rows(rows))))
        except (ValueError, TypeError) as error:
            outcomes.append(("ERROR", str(error)))
    if outcomes[0] != outcomes[1]:
        raise ValidationError("splitter semantic drift: " + label)


def copy_rows(rows: Any) -> Any:
    """Copy JSON-shaped fixtures without accepting subclass semantics."""

    return json.loads(json.dumps(rows, sort_keys=True, separators=(",", ":")))


def _splitter_equivalence_receipt(
    module: ModuleType,
    phys_parent: ModuleType,
    retail_parent: ModuleType,
) -> Dict[str, Any]:
    compared = 0
    constructive = 0
    permutations = 0
    exhaustive = 0
    refusal = 0

    for patient_count in range(5, 11):
        rows = [
            {"record_ordinal": index, "patient_id": str(index + 1)}
            for index in range(patient_count)
        ]
        if patient_count == 6:
            rows.append({"record_ordinal": 6, "patient_id": "1"})
        _compare_one(
            lambda value: module.exact_assignment("physionet-challenge-2012", value),
            phys_parent.split_physionet_manifest,
            rows,
            "physionet-constructive-" + str(patient_count),
        )
        constructive += 1
        compared += 1
        _compare_one(
            lambda value: module.exact_assignment("physionet-challenge-2012", value),
            phys_parent.split_physionet_manifest,
            list(reversed(rows)),
            "physionet-permutation-" + str(patient_count),
        )
        permutations += 1
        compared += 1

    for patient_order in itertools.permutations(("1", "2", "3", "4", "5")):
        rows = [
            {"record_ordinal": index, "patient_id": patient_id}
            for index, patient_id in enumerate(patient_order)
        ]
        _compare_one(
            lambda value: module.exact_assignment("physionet-challenge-2012", value),
            phys_parent.split_physionet_manifest,
            rows,
            "physionet-exhaustive-order",
        )
        exhaustive += 1
        compared += 1

    for rows, label in (
        ([{"record_ordinal": index, "patient_id": str(index + 1)} for index in range(4)], "physionet-too-small"),
        ([{"record_ordinal": index, "patient_id": "01" if index == 0 else str(index + 1)} for index in range(5)], "physionet-leading-zero"),
    ):
        _compare_one(
            lambda value: module.exact_assignment("physionet-challenge-2012", value),
            phys_parent.split_physionet_manifest,
            rows,
            label,
        )
        refusal += 1
        compared += 1

    for customer_count in range(5, 13):
        rows = [
            {
                "row_ordinal": index,
                "customer_key_hex": format(index + 1, "02x"),
                "timestamp_utc_microseconds": (index + 1) * 10,
            }
            for index in range(customer_count)
        ]
        _compare_one(
            lambda value: module.exact_assignment("online-retail-ii", value),
            retail_parent.split_retail_rows,
            rows,
            "retail-constructive-" + str(customer_count),
        )
        constructive += 1
        compared += 1
        _compare_one(
            lambda value: module.exact_assignment("online-retail-ii", value),
            retail_parent.split_retail_rows,
            list(reversed(rows)),
            "retail-permutation-" + str(customer_count),
        )
        permutations += 1
        compared += 1

    for timestamp_pattern in itertools.product((0, 1, 2), repeat=5):
        rows = [
            {
                "row_ordinal": index,
                "customer_key_hex": format(index + 1, "02x"),
                "timestamp_utc_microseconds": timestamp,
            }
            for index, timestamp in enumerate(timestamp_pattern)
        ]
        _compare_one(
            lambda value: module.exact_assignment("online-retail-ii", value),
            retail_parent.split_retail_rows,
            rows,
            "retail-exhaustive-timestamp-pattern",
        )
        exhaustive += 1
        compared += 1

    spanning = []
    ordinal = 0
    for customer in range(5):
        for timestamp in (0, 100):
            spanning.append(
                {
                    "row_ordinal": ordinal,
                    "customer_key_hex": format(customer + 1, "02x"),
                    "timestamp_utc_microseconds": timestamp,
                }
            )
            ordinal += 1
    for rows, label in (
        (spanning, "retail-spanning-infeasible"),
        ([{"row_ordinal": index, "customer_key_hex": format(index + 1, "02X"), "timestamp_utc_microseconds": index} for index in range(5)], "retail-uppercase-key"),
        ([{"row_ordinal": index, "customer_key_hex": format(index + 1, "02x"), "timestamp_utc_microseconds": index} for index in range(4)], "retail-too-small"),
    ):
        _compare_one(
            lambda value: module.exact_assignment("online-retail-ii", value),
            retail_parent.split_retail_rows,
            rows,
            label,
        )
        refusal += 1
        compared += 1

    if compared != 396 or constructive != 14 or permutations != 14 or exhaustive != 363 or refusal != 5:
        raise ValidationError("equivalence fixture accounting mismatch")
    return {
        "comparison_kind": "HARD_PINNED_PARENT_STABLE_BYTES_IN_MEMORY_DIFFERENTIAL_QUALIFICATION",
        "parent_pathname_import_used": False,
        "parent_bytecode_loader_used": False,
        "constructive_case_count": constructive,
        "permutation_case_count": permutations,
        "small_exhaustive_case_count": exhaustive,
        "refusal_case_count": refusal,
        "total_case_count": compared,
        "successful_outputs_equal_exactly": True,
        "failure_codes_equal_exactly": True,
        "physionet_contract_equivalent_on_qualified_fixture_domain": True,
        "retail_contract_equivalent_on_qualified_fixture_domain": True,
        "universal_equivalence_claimed": False,
    }


def _qualification_receipt(module: ModuleType) -> Dict[str, Any]:
    phys_rows = _physionet_rows()
    retail_rows = _retail_rows()
    phys_snapshot = module.build_synthetic_snapshot_manifest("physionet-challenge-2012", phys_rows, "PHYS-A")
    retail_snapshot = module.build_synthetic_snapshot_manifest("online-retail-ii", retail_rows, "RETAIL-A")
    phys_split = module.build_split_manifest(phys_snapshot, phys_rows)
    retail_split = module.build_split_manifest(retail_snapshot, retail_rows)
    phys_pair = module.validate_manifest_pair(phys_snapshot, phys_split)
    retail_pair = module.validate_manifest_pair(retail_snapshot, retail_split)
    if not phys_pair["crosslink_valid"] or not retail_pair["crosslink_valid"]:
        raise ValidationError("synthetic pair validation failed")
    return {
        "qualification_kind": "DETERMINISTIC_IN_MEMORY_SYNTHETIC_SCHEMA_QUALIFICATION_ONLY",
        "physionet_snapshot_manifest_sha256": phys_snapshot["snapshot_manifest_sha256"],
        "physionet_split_manifest_sha256": phys_split["split_manifest_sha256"],
        "physionet_record_count": phys_split["assignment_output"]["record_count"],
        "physionet_patient_count": phys_split["assignment_output"]["patient_count"],
        "physionet_patient_counts": phys_split["assignment_output"]["patient_counts"],
        "retail_snapshot_manifest_sha256": retail_snapshot["snapshot_manifest_sha256"],
        "retail_split_manifest_sha256": retail_split["split_manifest_sha256"],
        "retail_row_count": retail_split["assignment_output"]["row_count"],
        "retail_customer_count": retail_split["assignment_output"]["customer_count"],
        "retail_customer_counts": retail_split["assignment_output"]["customer_counts"],
        "both_snapshot_split_crosslinks_valid": True,
        "both_assignments_recomputed_under_exact_stopped_contracts": True,
        "all_rows_preserved": True,
        "exclusion_retry_resplit_or_topup_performed": False,
        "structural_validation_only": True,
        "source_license_governance_custody_or_admission_verified": False,
        "allocation_power_approved": False,
        "allocation_power_receipt_independently_verified": False,
        "F061_closed": False,
        "real_source_or_data_used": False,
        "domain_admission_evidence": False,
        "scientific_effect": 0,
    }


def build_expected_record(root: Optional[Path] = None) -> Dict[str, Any]:
    workspace = ROOT if root is None else Path(root).resolve()
    pinned = _read_and_pin_inputs(workspace)
    module = load_qualified_source(workspace)
    phys_parent = _load_pinned_parent_module(
        workspace,
        pinned,
        "research/diagnostics/manuscript_v3_physionet_patient_disjoint_split_design_v1.py",
        "pinned_physionet_split_parent_for_expected_record",
    )
    retail_parent = _load_pinned_parent_module(
        workspace,
        pinned,
        "research/diagnostics/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py",
        "pinned_retail_split_parent_for_expected_record",
    )
    predecessor_checks = _predecessor_contract_checks(pinned)
    source_contracts = module.DOMAIN_CONTRACTS
    record: Dict[str, Any] = {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "reported_date": REPORTED_DATE,
        "package_kind": "STATIC_RETAIL_TASK_AND_DUAL_DOMAIN_MANIFEST_DRAFTS_ONLY",
        "control_predicate": CONTROL_PREDICATE,
        "authority_provenance": {
            "normalized_visible_text": AUTHORITY_TEXT,
            "normalized_visible_text_utf8_bytes": len(AUTHORITY_TEXT.encode("utf-8")),
            "normalized_visible_text_sha256": AUTHORITY_SHA256,
            "normalization": "VISIBLE_TEXT_EXACT_TRAILING_TRANSPORT_FRAMING_UNBOUND",
            "raw_transport_bytes_bound": False,
            "conversation_envelope_bound": False,
            "account_identity_bound": False,
            "timestamp_bound": False,
            "cryptographic_user_authentication_claimed": False,
            "continued_bounded_local_project_work_authorized": True,
            "internal_renewed_scope_review_performed": True,
            "renewed_scope_review_is_agent_adjudication": True,
            "sole_justification": "CLOSE_NAMED_SOLO_BLOCK5_RETAIL_TASK_AND_DUAL_MANIFEST_DRAFT_CHECKBOX_ONLY",
            "external_contact_or_browsing_authorized": False,
            "data_access_or_download_authorized": False,
            "entropy_or_live_randomness_authorized": False,
            "runtime_approval_authorized": False,
            "scientific_execution_authorized": False,
            "training_authorized": False,
            "claim_promotion_or_submission_authorized": False,
            "tracker_edit_authorized_by_package": False,
        },
        "scope_review": {
            "additional_layer_beyond_stopped_predecessors": True,
            "physical_file_count": 5,
            "exact_package_roster": [SOURCE_PATH, HUMAN_PATH, MACHINE_PATH, VALIDATOR_PATH, TEST_PATH],
            "hard_pinned_predecessor_file_count": len(INPUT_SPECS),
            "hard_pinned_source_before_in_memory_execution": True,
            "pathname_loader_used_for_verified_source": False,
            "bytecode_loader_used_for_verified_source": False,
            "mutable_tracker_input_or_reverse_binding_present": False,
            "tracker_edited_by_package": False,
        },
        "predecessor_contract_checks": predecessor_checks,
        "splitter_contract_equivalence_receipt": _splitter_equivalence_receipt(
            module, phys_parent, retail_parent
        ),
        "retail_task_schema_route_draft": module.retail_task_schema_route_draft(),
        "snapshot_manifest_schema": {
            "exact_field_roster": list(module.SNAPSHOT_KEYS),
            "receipt_states": list(module.RECEIPT_STATES),
            "receipt_verification_state_required": True,
            "future_receipt_validation_is_structural_only": True,
            "custody_class": "INTERNAL_RESTRICTED_NOT_PUBLICATION_SAFE",
            "strict_types_and_closed_keys": True,
            "domain_separated_content_digest": True,
            "split_contract_crosslink_required": True,
            "post_snapshot_exclusion_count_must_equal_zero": True,
            "retry_resplit_topup_count_must_equal_zero": True,
            "real_manifest_present": False,
        },
        "split_manifest_schema": {
            "exact_field_roster": list(module.SPLIT_KEYS),
            "snapshot_digest_and_projection_crosslinks_required": True,
            "complete_private_normalized_projection_required": True,
            "exact_stopped_assignment_recomputation_required": True,
            "allocation_numerators": list(module.NUMERATORS),
            "allocation_denominator": module.DENOMINATOR,
            "allocation_power_review_state_and_receipt_slot_required": True,
            "synthetic_allocation_power_state": "NOT_POWER_APPROVED",
            "future_power_receipt_independently_verified_by_package": False,
            "F061_closed_by_structural_manifest": False,
            "exclusion_retry_resplit_and_topup_counts_must_equal_zero": True,
            "domain_separated_content_digest": True,
            "real_manifest_present": False,
        },
        "domain_contracts": [
            {
                "domain_id": domain_id,
                "slot_id": source_contracts[domain_id]["slot_id"],
                "snapshot_schema": source_contracts[domain_id]["snapshot_schema"],
                "split_schema": source_contracts[domain_id]["split_schema"],
                "normalization_contract_id": source_contracts[domain_id]["normalization_contract_id"],
                "splitter_control_predicate": source_contracts[domain_id]["splitter_predicate"],
                "splitter_algorithm_id": source_contracts[domain_id]["algorithm_id"],
                "splitter_machine_sha256": source_contracts[domain_id]["splitter_machine_sha256"],
                "minimum_group_count": source_contracts[domain_id]["minimum_group_count"],
                "allocation_numerators": [70, 15, 15],
                "allocation_denominator": 100,
                "allocation_power_justified": False,
            }
            for domain_id in ("physionet-challenge-2012", "online-retail-ii")
        ],
        "qualification_receipt": _qualification_receipt(module),
        "nonclosure": {
            "open_field_roster": ["F" + str(index).zfill(3) for index in range(19, 62)],
            "f038_through_f061_all_open_and_null": True,
            "blocker_roster_remaining_open": ["B" + str(index).zfill(2) for index in range(1, 13)],
            "B02_open": True,
            "B03_open": True,
            "B09_open": True,
            "formal_test_states": {"FORMAL_TEST_28":"OPEN", "FORMAL_TEST_29":"OPEN", "FORMAL_TEST_30":"OPEN"},
            "result_slots_remaining_open": ["R1", "R2", "R3", "R4"],
            "unresolved_fields_closed": 0,
            "blockers_closed": 0,
            "formal_tests_closed": 0,
            "results_filled": 0,
            "mutable_project_totals_asserted_or_bound": False,
            "scientific_effect": 0,
        },
        "publication_boundary": {
            "internal_evidence_only": True,
            "anonymous_or_public_inclusion_permitted": False,
            "publication_safe_derivative_required": True,
            "fresh_anonymity_license_and_governance_review_required": True,
            "visible_authority_text_permitted_in_derivative": False,
            "internal_paths_hashes_receipts_or_private_projection_permitted_in_derivative": False,
            "real_patient_customer_identifier_timestamp_or_row_present": False,
            "credentials_tokens_cookies_or_secrets_present": False,
            "protected_outcome_or_scientific_result_present": False,
        },
        "scope_and_nonclaims": {
            "web_network_connector_or_external_contact_used": False,
            "source_documentation_license_or_governance_contacted": False,
            "data_acquired_opened_parsed_snapshotted_or_split": False,
            "entropy_or_scientific_randomness_used": False,
            "runtime_science_training_or_submission_performed": False,
            "real_task_schema_or_source_fact_verified": False,
            "real_snapshot_or_split_manifest_present": False,
            "domain_admitted": False,
            "tracker_edited": False,
            "independent_audit_claimed": False,
            "package_internal_only": True,
        },
        "input_bindings": [
            _binding(index, spec["role"], spec["path"], pinned[spec["path"]])
            for index, spec in enumerate(INPUT_SPECS)
        ],
        "package_bindings": [
            _binding(index, role, path, _stable_read(workspace, path))
            for index, (role, path) in enumerate((
                ("PURE_SCHEMA_SOURCE", SOURCE_PATH),
                ("HUMAN_DRAFT", HUMAN_PATH),
                ("READ_ONLY_VALIDATOR", VALIDATOR_PATH),
                ("HOSTILE_SYNTHETIC_TEST", TEST_PATH),
            ))
        ],
    }
    record["record_sha256"] = record_sha256(record)
    return record


def validate(root: Optional[Path] = None) -> Dict[str, Any]:
    workspace = ROOT if root is None else Path(root).resolve()
    expected = build_expected_record(workspace)
    machine_raw = _stable_read(workspace, MACHINE_PATH)
    try:
        machine = json.loads(machine_raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("machine record invalid") from error
    if type(machine) is not dict:
        raise ValidationError("machine root invalid")
    if canonical_machine_bytes(machine) != machine_raw:
        raise ValidationError("machine record is not canonical")
    if machine.get("record_sha256") != record_sha256(machine):
        raise ValidationError("machine self digest mismatch")
    _strict_equal(machine, expected, "machine")
    return {
        "schema_version": SCHEMA,
        "state": STATE,
        "global_state": GLOBAL_STATE,
        "record_sha256": machine["record_sha256"],
        "control_predicate": CONTROL_PREDICATE,
        "eligible_after_independent_audit": True,
        "solo_block5_draft_milestone_only": True,
        "existing_fields_closed": 0,
        "blockers_closed": 0,
        "formal_tests_closed": 0,
        "results_filled": 0,
        "scientific_effect": 0,
        "validation": "PASS",
    }


def main() -> int:
    try:
        status = validate()
    except (OSError, ValidationError, ValueError, TypeError, KeyError) as error:
        print("VALIDATION_ERROR: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(status, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
