#!/usr/bin/env python3
"""Hash-first validator for the B12 whole-method nonconfirmatory candidate."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from types import ModuleType
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

SCHEMA_VERSION = (
    "heterodiff-b12-whole-method-nonconfirmatory-runner-candidate-v1"
)
STATE = "WHOLE_METHOD_NONCONFIRMATORY_CANDIDATE_PENDING_INDEPENDENT_REVIEW"
MACHINE_REL = (
    "research/fixtures/"
    "manuscript_v3_b12_whole_method_nonconfirmatory_runner_v1.json"
)
VALIDATOR_REL = (
    "research/diagnostics/"
    "manuscript_v3_b12_whole_method_nonconfirmatory_runner_v1.py"
)
PRIMARY_REL = (
    "src/heterodiff/evaluation/b12_whole_method_nonconfirmatory_runner.py"
)
INDEPENDENT_REL = (
    "src/heterodiff/evaluation/"
    "b12_whole_method_nonconfirmatory_recomputation.py"
)
EXTERNAL_REL = (
    "src/heterodiff/evaluation/b12_external_author_extension_components.py"
)
TEST_REL = "tests/unit/test_b12_whole_method_nonconfirmatory_runner.py"
MAX_FILE_BYTES = 5_000_000

TASKS = (
    "Produce whole-method beta: initializer, continuous path, jump/edit law, and sampler integrated.",
    "End-to-end method is feature-complete.",
)
EXTERNAL_IDS = tuple(
    "CSDI_AUTHOR_EXTENSION_%d" % ordinal for ordinal in range(1, 5)
) + tuple("EDITPP_AUTHOR_EXTENSION_%d" % ordinal for ordinal in range(1, 5))

EXPECTED_STATIC_BINDINGS = (
    (
        "human",
        "PROJECT_B12_WHOLE_METHOD_NONCONFIRMATORY_RUNNER.md",
        9575,
        "60a084e03c93f731968394b734a181da62f450835fbba03b887fdf126f152eed",
    ),
    (
        "primary_runner_source",
        PRIMARY_REL,
        40451,
        "c1c5c44584af43631def5f13e862a6a486f9622dfa970e476a915d4ff488509d",
    ),
    (
        "independent_recomputation_source",
        INDEPENDENT_REL,
        25993,
        "edca70eaa2e4090f9ee224e1be55c7f587b24eba310033b6317c6049c7c545c5",
    ),
    (
        "external_author_extension_source",
        EXTERNAL_REL,
        56988,
        "859d719c1782a9964cd7219af29faeac696f1bd1d8029efa8f176dc8b4f93807",
    ),
    (
        "focused_hostile_tests",
        TEST_REL,
        15841,
        "1319b3c420fc1bf2a083d9627c5da7896027f317f6479ab70d1461af4bc158d1",
    ),
)


class ValidationError(RuntimeError):
    """Raised when exact-byte or semantic candidate validation fails."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _domain_sha256(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("ascii") + b"\0" + _canonical(value)).hexdigest()


def _identity(metadata: os.stat_result) -> Tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _canonical_relative(value: str) -> PurePosixPath:
    if type(value) is not str or not value or not value.isascii() or "\\" in value:
        raise ValidationError("path must be exact nonempty ASCII POSIX text")
    relative = PurePosixPath(value)
    if (
        relative.as_posix() != value
        or relative.is_absolute()
        or any(part in ("", ".", "..") for part in relative.parts)
    ):
        raise ValidationError("path is noncanonical or escapes project root")
    return relative


def _read_stable_regular(relative_path: str) -> bytes:
    relative = _canonical_relative(relative_path)
    root_flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        root_flags |= os.O_NOFOLLOW
    root_fd = os.open(str(ROOT), root_flags)
    opened = []
    try:
        before_root = os.fstat(root_fd)
        current = root_fd
        for part in relative.parts[:-1]:
            flags = os.O_RDONLY | os.O_DIRECTORY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(part, flags, dir_fd=current)
            opened.append(descriptor)
            current = descriptor
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        leaf = os.open(relative.name, flags, dir_fd=current)
        opened.append(leaf)
        before = os.fstat(leaf)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o644
            or before.st_nlink != 1
            or not 1 <= before.st_size <= MAX_FILE_BYTES
        ):
            raise ValidationError("file custody or size differs: " + relative_path)
        chunks = []
        total = 0
        while total <= before.st_size:
            chunk = os.read(leaf, min(131_072, before.st_size + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(leaf)
        after_root = os.fstat(root_fd)
        if (
            len(raw) != before.st_size
            or _identity(before) != _identity(after)
            or _identity(before_root) != _identity(after_root)
        ):
            raise ValidationError("file or root changed during read")
        return raw
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)
        os.close(root_fd)


def _binding(role: str, path: str, raw: bytes) -> Dict[str, Any]:
    return {
        "bytes": len(raw),
        "mode_octal": "0644",
        "nlink": 1,
        "path": path,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "role": role,
        "terminal_lf": raw.endswith(b"\n"),
    }


def _verify_static_bindings() -> Tuple[Dict[str, Any], ...]:
    result = []
    for role, path, byte_count, digest in EXPECTED_STATIC_BINDINGS:
        raw = _read_stable_regular(path)
        if (
            len(raw) != byte_count
            or hashlib.sha256(raw).hexdigest() != digest
            or not raw.endswith(b"\n")
        ):
            raise ValidationError("fixed binding differs: " + path)
        result.append(_binding(role, path, raw))
    return tuple(result)


def _strict_json(value: object, name: str) -> None:
    if value is None or type(value) in (str, int, bool):
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _strict_json(item, "%s[%d]" % (name, index))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValidationError(name + " has a non-text key")
            _strict_json(item, name + "." + key)
        return
    raise ValidationError(name + " has a non-exact JSON type")


def _pairs(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    if type(pairs) is not list:
        raise ValidationError("JSON pairs differ")
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise ValidationError("duplicate or non-text JSON key")
        result[key] = value
    return result


def _load_machine(raw: bytes) -> Dict[str, Any]:
    if type(raw) is not bytes or not raw.endswith(b"\n") or raw[:-1].endswith(b"\n"):
        raise ValidationError("machine record framing differs")
    try:
        value = json.loads(raw[:-1].decode("ascii"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("machine JSON differs") from error
    if type(value) is not dict:
        raise ValidationError("machine root differs")
    _strict_json(value, "machine")
    if _canonical(value) + b"\n" != raw:
        raise ValidationError("machine JSON is not canonical")
    return value


_TARGET_SPECS = (
    (
        "heterodiff.evaluation.b12_whole_method_nonconfirmatory_recomputation",
        INDEPENDENT_REL,
    ),
    (
        "heterodiff.evaluation.b12_whole_method_nonconfirmatory_runner",
        PRIMARY_REL,
    ),
)


@contextmanager
def _captured_target_modules():
    """Compile and execute both target modules from the hash-checked bytes."""

    import heterodiff.evaluation as evaluation_package

    missing = object()
    saved_modules = {
        name: sys.modules.get(name, missing) for name, _ in _TARGET_SPECS
    }
    saved_attributes = {
        name: getattr(evaluation_package, name.rsplit(".", 1)[1], missing)
        for name, _ in _TARGET_SPECS
    }
    exact = {
        path: (size, digest)
        for _, path, size, digest in EXPECTED_STATIC_BINDINGS
    }
    modules: Dict[str, ModuleType] = {}
    try:
        for name, relative in _TARGET_SPECS:
            raw = _read_stable_regular(relative)
            if exact[relative] != (len(raw), hashlib.sha256(raw).hexdigest()):
                raise ValidationError("captured target differs: " + relative)
            path = ROOT.joinpath(*_canonical_relative(relative).parts)
            code = compile(raw, str(path), "exec", dont_inherit=True)
            module = ModuleType(name)
            module.__file__ = str(path)
            module.__package__ = name.rpartition(".")[0]
            sys.modules[name] = module
            setattr(evaluation_package, name.rsplit(".", 1)[1], module)
            exec(code, module.__dict__)
            modules[name] = module
        yield modules
    finally:
        for name, _ in reversed(_TARGET_SPECS):
            attribute = name.rsplit(".", 1)[1]
            prior_attribute = saved_attributes[name]
            if prior_attribute is missing:
                try:
                    delattr(evaluation_package, attribute)
                except AttributeError:
                    pass
            else:
                setattr(evaluation_package, attribute, prior_attribute)
            prior_module = saved_modules[name]
            if prior_module is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = prior_module


def _registration() -> Dict[str, Any]:
    return {
        "applied_timetable_task_delta": 0,
        "independent_review_required_before_registration": True,
        "proposed_timetable_task_closure_count": 2,
        "proposed_timetable_task_closures": list(TASKS),
    }


def _effects() -> Dict[str, Any]:
    return {
        "authority_created": False,
        "blocker_delta": 0,
        "confirmatory_evidence": False,
        "data_accessed": False,
        "entropy_acquired": False,
        "field_delta": 0,
        "formal_test_delta": 0,
        "network_used": False,
        "production_receipts_minted": False,
        "result_delta": 0,
        "science_executed": False,
        "timetable_task_delta_applied": 0,
        "tracker_or_evidence_ledger_edited": False,
        "training_executed": False,
        "upstream_packages_executed": False,
    }


def derive_semantics() -> Dict[str, Any]:
    with _captured_target_modules() as modules:
        primary = modules[
            "heterodiff.evaluation.b12_whole_method_nonconfirmatory_runner"
        ]
        supplied = primary.build_frozen_nonconfirmatory_input()
        captured: Dict[str, Any] = {}
        original_core = primary._core_output

        def capture_core(project_root: str, supplied_input: object):
            result = original_core(project_root, supplied_input)
            captured["core"] = result[0]
            return result

        primary._core_output = capture_core
        try:
            receipt = primary.run_supplied_nonconfirmatory_whole_method(
                str(ROOT), supplied
            )
        finally:
            primary._core_output = original_core
        primary.validate_whole_method_nonconfirmatory_receipt(receipt)
        receipt_bytes = primary.receipt_canonical_json_bytes(receipt)
        receipt_document = _load_machine(receipt_bytes)
        core = captured.get("core")
        if type(core) is not dict:
            raise ValidationError("primary core capture differs")
        external = core["external_author_extensions"]
        if tuple(external["predicate_ids"]) != EXTERNAL_IDS:
            raise ValidationError("external obligation roster differs")
        interfaces = external["conditioning_interfaces"]
        if (
            [row["draw_count"] for row in interfaces] != [64, 64]
            or [row["generated_output_count"] for row in interfaces] != [0, 0]
        ):
            raise ValidationError("external draw boundary differs")
        if receipt.core_output_sha256 != receipt.independent_output_sha256:
            raise ValidationError("independent output differs")
        if len(receipt.open_residual_predicate_ids) != 50:
            raise ValidationError("open residual roster differs")
        if len(receipt.implementation_obligations_exercised) != 19:
            raise ValidationError("implementation obligation roster differs")
        if core["effects"] != {
            "authority_created": False,
            "blocker_delta": 0,
            "data_accessed": False,
            "entropy_acquired": False,
            "field_delta": 0,
            "formal_test_delta": 0,
            "network_used": False,
            "production_receipts_minted": False,
            "result_delta": 0,
            "science_executed": False,
            "tracker_edited": False,
            "training_executed": False,
        }:
            raise ValidationError("effect boundary differs")
        route_binding = {
            "confirmatory_evidence": False,
            "implementation_obligation_count": 19,
            "open_residual_slot_count": 50,
            "receipt_schema": receipt.schema_version,
            "separate_recomputation_bytes_equal": True,
            "separately_executed_and_validated": True,
            "stable_receipt_sha256": receipt.receipt_sha256,
            "supplied_input_sha256": receipt.supplied_input_sha256,
        }
        return {
            "adapter_and_capsule": {
                "adapter_manifest_sha256": receipt.adapter_manifest_sha256,
                "capsule_manifest_sha256": receipt.capsule_manifest_sha256,
                "corrected_adapter_receipt_count": core["adapter_and_capsule"][
                    "adapter_receipt_count"
                ],
                "context_dimensions": [
                    row["context_dimension"] for row in core["context_encoders"]
                ],
            },
            "external_author_extensions": {
                "adapter_count": len(external["adapters"]),
                "all_pending_output_counts": [
                    row["generated_output_count"] for row in interfaces
                ],
                "conditioning_draw_counts": [
                    row["draw_count"] for row in interfaces
                ],
                "implementation_manifest_sha256": external[
                    "implementation_manifest_sha256"
                ],
                "module_source_sha256": external["module_source_sha256"],
                "predicate_ids": list(EXTERNAL_IDS),
                "upstream_packages_executed": False,
            },
            "formal_test_states": dict(core["formal_test_states"]),
            "frozen_input": dict(supplied.payload()),
            "implementation_obligations_exercised": list(
                receipt.implementation_obligations_exercised
            ),
            "initializer_and_sampler": {
                "budget": core["initializer_and_sampler"]["budget"],
                "fixture_id": core["initializer_and_sampler"]["fixture_id"],
                "plan_seed_hex": core["initializer_and_sampler"]["plan_seed_hex"],
                "selected_configuration_sha256": core["initializer_and_sampler"][
                    "selected_configuration_sha256"
                ],
                "strategy": core["initializer_and_sampler"]["strategy"],
            },
            "metric_checkpoint_bridges": [
                {
                    "b06_domain_id": row["b06_domain_id"],
                    "f105_domain_id": row["f105_domain_id"],
                    "namespace_subjects_byte_equal": row[
                        "factory_and_f144_namespace_subjects_byte_equal"
                    ],
                    "production_history_authenticated": row[
                        "production_history_authenticated"
                    ],
                    "structurally_eligible": row["structural_checkpoint_receipt"][
                        "eligible_under_f144_structure"
                    ],
                }
                for row in core["f105_checkpoint_bridges"]
            ],
            "nonclaims": {
                "b12_closed": False,
                "confirmatory_evidence": False,
                "production_receipts_minted": False,
                "real_residual_receipts_present": 0,
                "result_or_claim_created": False,
            },
            "path": {
                "bounded_two_macrostep_path_integrated": core[
                    "two_macrostep_continuous_jump_path"
                ]["bounded_two_macrostep_path_integrated"],
                "step_families": [
                    row["family"]
                    for row in core["two_macrostep_continuous_jump_path"]["steps"]
                ],
                "total_central_jumps": core[
                    "two_macrostep_continuous_jump_path"
                ]["total_central_jumps"],
                "total_left_heun_applications": core[
                    "two_macrostep_continuous_jump_path"
                ]["total_left_heun_applications"],
                "total_right_heun_applications": core[
                    "two_macrostep_continuous_jump_path"
                ]["total_right_heun_applications"],
            },
            "receipt": receipt_document,
            "route_binding": route_binding,
            "schema_version": SCHEMA_VERSION,
            "state": STATE,
        }


def _unsigned_record() -> Dict[str, Any]:
    bindings = list(_verify_static_bindings())
    validator_raw = _read_stable_regular(VALIDATOR_REL)
    if not validator_raw.endswith(b"\n"):
        raise ValidationError("validator lacks terminal LF")
    bindings.append(_binding("validator", VALIDATOR_REL, validator_raw))
    semantics = derive_semantics()
    return {
        "bindings": bindings,
        "effects": _effects(),
        "registration_proposal": _registration(),
        "route_binding": semantics["route_binding"],
        "schema_version": SCHEMA_VERSION,
        "semantics": semantics,
        "state": STATE,
    }


def build_machine_record() -> Dict[str, Any]:
    record = _unsigned_record()
    record["record_sha256"] = _domain_sha256(SCHEMA_VERSION, record)
    return dict(sorted(record.items()))


def validate() -> Dict[str, Any]:
    machine = _load_machine(_read_stable_regular(MACHINE_REL))
    supplied_record_sha256 = machine.get("record_sha256")
    if type(supplied_record_sha256) is not str:
        raise ValidationError("record digest differs")
    unsigned = dict(machine)
    del unsigned["record_sha256"]
    if supplied_record_sha256 != _domain_sha256(SCHEMA_VERSION, unsigned):
        raise ValidationError("record self-digest differs")
    expected = build_machine_record()
    if machine != expected:
        raise ValidationError("machine record differs from exact recomputation")
    return {
        "decision": "PASS_CANDIDATE_PENDING_INDEPENDENT_REVIEW",
        "proposed_timetable_task_closure_count": 2,
        "stable_receipt_sha256": machine["route_binding"][
            "stable_receipt_sha256"
        ],
    }


def main() -> int:
    try:
        print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))
    except Exception as error:
        print(
            json.dumps(
                {
                    "decision": "FAIL_CLOSED",
                    "error": "%s: %s" % (type(error).__name__, str(error)),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
