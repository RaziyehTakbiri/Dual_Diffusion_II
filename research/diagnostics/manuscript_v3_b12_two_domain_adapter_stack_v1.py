#!/usr/bin/env python3
"""Read-only validator for the corrected B12 two-domain adapter stack."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType
from typing import Any, Dict, Iterable, Tuple


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
MACHINE_REL = "research/fixtures/manuscript_v3_b12_two_domain_adapter_stack_v1.json"
SOURCE_REL = "src/heterodiff/evaluation/b12_two_domain_adapter_stack.py"

EXPECTED_STATIC_BINDINGS = (
    (
        "human",
        "PROJECT_B12_TWO_DOMAIN_ADAPTER_STACK.md",
        8866,
        "900eb147602eb7d74e1a54e69d9d684cf8a1e8fc433c030cad4d50a2a2937b49",
    ),
    (
        "source",
        SOURCE_REL,
        34660,
        "44ece6452c8edfaadc7d6013a37208fb8648d3a6dbb3ce29bcecd97a90880a57",
    ),
    (
        "tests",
        "tests/unit/test_b12_two_domain_adapter_stack.py",
        13259,
        "268ba5bf9e4ff57e1df1108aceb4106a957df7a541a6f1de43f2b6ff2f197d64",
    ),
)

EXPECTED_PREDECESSOR_BINDINGS = (
    (
        "b06_registry_source",
        "src/heterodiff/experiments/two_domain_baseline_registry.py",
        47098,
        "d8938ac2111000275a02ad9605602ecf11f2ef9c38903d5431d6c3604c1645f1",
    ),
    (
        "b06_machine",
        "research/fixtures/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json",
        186707,
        "b789b4b39aef1cef3134dddee506409f311b79cc70b1d121daa0a2ff22267f21",
    ),
    (
        "f105_exact_instance_source",
        "src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py",
        25342,
        "567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881",
    ),
    (
        "legacy_b12_partial_source",
        "src/heterodiff/evaluation/b12_integrated_offline_candidate.py",
        14944,
        "b77c6eea6859fa9d6181a94a27112d97555e5a4d60ab1df1ee03a30c7808defd",
    ),
    (
        "legacy_b12_partial_machine",
        "research/fixtures/manuscript_v3_b12_integrated_offline_gap_package_v1.json",
        8755,
        "825cfde8412474eba97dea4a4d2fb92fa8af99568ebeada05f6b33b71fcc680c",
    ),
    (
        "legacy_b12_final_replacement_review",
        "PROJECT_B12_INTEGRATED_OFFLINE_IMPLEMENTATION_GAP_PACKAGE_INDEPENDENT_REVIEW.md",
        4988,
        "90e7d4f9f4f70bcd4a6da599c532a944629101d3d5b245f7b05ece01cb463a46",
    ),
)


class ValidationError(RuntimeError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("ascii") + b"\0" + _canonical(value)).hexdigest()


def _read_stable_regular(relative_path: str) -> bytes:
    if type(relative_path) is not str or not relative_path or relative_path.startswith("/"):
        raise ValidationError("path must be a nonempty project-relative string")
    parts = Path(relative_path).parts
    if any(part in ("", ".", "..") for part in parts):
        raise ValidationError("path contains a forbidden component")
    path = ROOT.joinpath(*parts)
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValidationError(f"not a regular file: {relative_path}")
        if before.st_nlink != 1:
            raise ValidationError(f"link count differs from one: {relative_path}")
        if stat.S_IMODE(before.st_mode) != 0o644:
            raise ValidationError(f"mode differs from 0644: {relative_path}")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_nlink,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_nlink,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if identity_before != identity_after:
            raise ValidationError(f"file changed during read: {relative_path}")
        data = b"".join(chunks)
        if len(data) != before.st_size:
            raise ValidationError(f"short or expanded read: {relative_path}")
        return data
    finally:
        os.close(descriptor)


def _binding(role: str, path: str, data: bytes) -> Dict[str, Any]:
    return {
        "bytes": len(data),
        "mode_octal": "0644",
        "nlink": 1,
        "path": path,
        "raw_sha256": hashlib.sha256(data).hexdigest(),
        "role": role,
        "terminal_lf": data.endswith(b"\n"),
    }


def _verify_fixed_bindings(
    expected: Iterable[Tuple[str, str, int, str]]
) -> Tuple[Dict[str, Any], ...]:
    results = []
    for role, path, expected_bytes, expected_sha256 in expected:
        data = _read_stable_regular(path)
        if len(data) != expected_bytes:
            raise ValidationError(f"byte count mismatch: {path}")
        if hashlib.sha256(data).hexdigest() != expected_sha256:
            raise ValidationError(f"raw SHA-256 mismatch: {path}")
        results.append(_binding(role, path, data))
    return tuple(results)


def _load_json_no_duplicates(data: bytes) -> Dict[str, Any]:
    if not data.endswith(b"\n") or data[:-1].endswith(b"\n"):
        raise ValidationError("machine record must have one terminal LF")
    try:
        text = data[:-1].decode("ascii")
    except UnicodeDecodeError as error:
        raise ValidationError("machine record is not ASCII") from error

    def pairs_hook(pairs: list[tuple[str, Any]]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(text, object_pairs_hook=pairs_hook)
    except (ValueError, json.JSONDecodeError) as error:
        raise ValidationError("machine record is invalid JSON") from error
    if type(value) is not dict:
        raise ValidationError("machine record root is not an exact object")
    if _canonical(value) != data[:-1]:
        raise ValidationError("machine record is not canonical JSON")
    return value


def _compile_captured_source(source_bytes: bytes) -> ModuleType:
    name = "heterodiff.evaluation._b12_two_domain_adapter_stack_validated"
    module = ModuleType(name)
    module.__file__ = str(ROOT / SOURCE_REL)
    module.__package__ = "heterodiff.evaluation"
    sys.modules[name] = module
    try:
        code = compile(source_bytes, module.__file__, "exec")
        exec(code, module.__dict__)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def _expected_semantics(module: ModuleType, source_sha256: str) -> Dict[str, Any]:
    retail, physionet = module.qualification_fixture_configurations()
    manifest = module.build_synthetic_conformance_manifest(
        retail_configuration=retail,
        physionet_configuration=physionet,
        module_source_sha256=source_sha256,
    )
    manifest_payloads = [record.semantic_payload() for record in manifest]
    receipt_payloads = []
    for record in manifest:
        receipt = record.receipt
        receipt.validate()
        receipt_payloads.append(
            {
                "adapter_id": receipt.adapter_id,
                "config_sha256": receipt.config_sha256,
                "domain_id": receipt.domain_id,
                "implementation_source_sha256": receipt.implementation_source_sha256,
                "input_sha256": receipt.input_sha256,
                "output_sha256": receipt.output_sha256,
                "predicate_receipt_sha256": receipt.predicate.receipt_sha256,
            }
        )
    extensions = []
    for obligation in module.AUTHOR_EXTENSION_OBLIGATIONS:
        obligation.validate()
        extensions.append(
            {
                "adapter_id": obligation.adapter_id,
                "domain_id": obligation.domain_id,
                "domain_scale_qualification_claimed": (
                    obligation.domain_scale_qualification_claimed
                ),
                "extension_id": obligation.extension_id,
                "ordinal_within_adapter": obligation.ordinal_within_adapter,
                "predicate_id": obligation.predicate_id,
                "status": obligation.status,
                "upstream_execution_claimed": obligation.upstream_execution_claimed,
            }
        )
    class_counts: Dict[str, int] = {}
    for record in manifest:
        class_counts[record.adapter_class] = class_counts.get(record.adapter_class, 0) + 1
    return {
        "adapter_class_counts": class_counts,
        "adapter_count": 22,
        "author_extension_count": 8,
        "author_extension_obligations": extensions,
        "corrected_adapter_roster": [list(row) for row in module.ADAPTER_ROSTER_SNAPSHOT],
        "effects": {
            "blocker_delta": 0,
            "field_delta": 0,
            "formal_test_delta": 0,
            "result_delta": 0,
            "science_delta": 0,
            "tracker_edited": False,
        },
        "legacy_partial_roster_mismatch_ordinals": list(
            module.LEGACY_PARTIAL_ROSTER_MISMATCH_ORDINALS
        ),
        "manifest_record_sha256": _sha256(
            "heterodiff-b12-two-domain-adapter-manifest-v1", manifest_payloads
        ),
        "nonclaims": {
            "author_extensions_implemented": False,
            "b12_closed": False,
            "data_accessed": False,
            "domain_scale_runtime_qualified": False,
            "entropy_used": False,
            "independent_review_completed": False,
            "network_used": False,
            "production_adapter_residuals_closed": False,
            "scientific_training_or_inference_performed": False,
            "typed_receipts_are_synthetic_interface_only": True,
            "upstream_packages_executed": False,
        },
        "primary_context_dimension": module.PRIMARY_CONTEXT_DIMENSION,
        "receipt_roster_sha256": _sha256(
            "heterodiff-b12-two-domain-adapter-receipt-roster-v1", receipt_payloads
        ),
        "schema": module.SCHEMA_VERSION,
        "state": "SYNTHETIC_INTERFACE_IMPLEMENTED_RUNTIME_AND_ALGORITHM_RESIDUALS_OPEN",
    }


def validate() -> Dict[str, Any]:
    static_bindings = _verify_fixed_bindings(EXPECTED_STATIC_BINDINGS)
    predecessor_bindings = _verify_fixed_bindings(EXPECTED_PREDECESSOR_BINDINGS)
    validator_data = _read_stable_regular(
        "research/diagnostics/manuscript_v3_b12_two_domain_adapter_stack_v1.py"
    )
    validator_binding = _binding(
        "validator",
        "research/diagnostics/manuscript_v3_b12_two_domain_adapter_stack_v1.py",
        validator_data,
    )
    machine_data = _read_stable_regular(MACHINE_REL)
    machine = _load_json_no_duplicates(machine_data)
    required_keys = (
        "bindings",
        "effects",
        "predecessor_bindings",
        "record_sha256",
        "schema_version",
        "semantics",
        "state",
    )
    if tuple(machine) != required_keys:
        raise ValidationError("machine top-level key roster or order differs")
    expected_bindings = list(static_bindings) + [validator_binding]
    if machine["bindings"] != expected_bindings:
        raise ValidationError("current-package bindings differ")
    if machine["predecessor_bindings"] != list(predecessor_bindings):
        raise ValidationError("predecessor bindings differ")
    if machine["schema_version"] != "heterodiff-b12-two-domain-adapter-stack-record-v1":
        raise ValidationError("machine schema differs")
    if machine["state"] != "SYNTHETIC_INTERFACE_IMPLEMENTED_RUNTIME_AND_ALGORITHM_RESIDUALS_OPEN":
        raise ValidationError("machine state differs")
    source_data = _read_stable_regular(SOURCE_REL)
    source_sha256 = hashlib.sha256(source_data).hexdigest()
    module = _compile_captured_source(source_data)
    expected_semantics = _expected_semantics(module, source_sha256)
    if machine["semantics"] != expected_semantics:
        raise ValidationError("machine semantics differ from captured source")
    if machine["effects"] != expected_semantics["effects"]:
        raise ValidationError("top-level effects differ from semantics")
    unsigned = dict(machine)
    supplied_record_sha256 = unsigned.pop("record_sha256")
    expected_record_sha256 = _sha256(
        "heterodiff-b12-two-domain-adapter-stack-record-v1", unsigned
    )
    if supplied_record_sha256 != expected_record_sha256:
        raise ValidationError("machine semantic self-digest differs")
    return {
        "adapter_count": 22,
        "author_extension_count": 8,
        "decision": "PASS_SYNTHETIC_INTERFACE_ONLY",
        "legacy_mismatch_count": 8,
        "manifest_record_sha256": expected_semantics["manifest_record_sha256"],
        "record_sha256": expected_record_sha256,
    }


def main() -> int:
    try:
        result = validate()
    except Exception as error:
        print(f"FAIL — {error}", file=sys.stderr)
        return 1
    print(
        "PASS — 22 corrected B06 adapter interface rows; "
        f"record {result['record_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
