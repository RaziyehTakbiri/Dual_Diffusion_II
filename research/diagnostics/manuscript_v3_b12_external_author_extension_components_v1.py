#!/usr/bin/env python3
"""Read-only hash-first validator for the eight external-extension components.

All candidate and transitive predecessor bytes are captured and checked before
any project source is compiled.  Captured modules are then loaded into fresh
module objects, the exact candidate semantics are reconstructed, and the
canonical machine record is compared byte-for-byte.  The validator performs no
writes, network access, subprocess invocation, entropy use, data access,
training, inference, upstream-package execution, or project-control action.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
from types import ModuleType
from typing import Any, Dict, Iterable, Mapping, Tuple


SCHEMA_VERSION = "heterodiff-b12-external-author-extension-components-record-v1"
STATE = (
    "OFFLINE_AUTHOR_EXTENSION_COMPONENTS_IMPLEMENTED_PENDING_INDEPENDENT_"
    "REVIEW_RUNTIME_OPEN"
)
PASS_TOKEN = "PASS_B12_EXTERNAL_AUTHOR_EXTENSION_COMPONENTS_ONLY"
MACHINE_REL = (
    "research/fixtures/"
    "manuscript_v3_b12_external_author_extension_components_v1.json"
)
VALIDATOR_REL = (
    "research/diagnostics/"
    "manuscript_v3_b12_external_author_extension_components_v1.py"
)
SOURCE_REL = (
    "src/heterodiff/evaluation/b12_external_author_extension_components.py"
)

# role, path, exact byte count, raw SHA-256
EXPECTED_STATIC_BINDINGS = (
    (
        "human",
        "PROJECT_B12_EXTERNAL_AUTHOR_EXTENSION_COMPONENTS.md",
        12064,
        "e6d841513c500e5b6c997bd76b34fb30aad55b30e02cd35ff52d4e0fc746d347",
    ),
    (
        "source",
        SOURCE_REL,
        56988,
        "859d719c1782a9964cd7219af29faeac696f1bd1d8029efa8f176dc8b4f93807",
    ),
    (
        "tests",
        "tests/unit/test_b12_external_author_extension_components.py",
        26524,
        "159bd645f78e0ba2323b425b836b4e4b20750eb4730178e10102f38b57f2e94e",
    ),
)

EXPECTED_PREDECESSOR_BINDINGS = (
    (
        "b06_human",
        "PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE.md",
        41198,
        "6a10a546a70d43aa71cb878e72ba09c24be949cd932e1cdf5becdeb732fa816a",
    ),
    (
        "b06_machine",
        "research/fixtures/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json",
        186707,
        "b789b4b39aef1cef3134dddee506409f311b79cc70b1d121daa0a2ff22267f21",
    ),
    (
        "b06_matched_compute_source",
        "src/heterodiff/experiments/matched_total_compute.py",
        15028,
        "be31b346c67b7d0ce0b82a3ff784739bf3d825fd9b94108dc1f8ae808586f8a0",
    ),
    (
        "b06_registry_source",
        "src/heterodiff/experiments/two_domain_baseline_registry.py",
        47098,
        "d8938ac2111000275a02ad9605602ecf11f2ef9c38903d5431d6c3604c1645f1",
    ),
    (
        "b06_independent_review",
        "PROJECT_B06_BASELINE_IDENTITIES_MATCHED_COMPUTE_FREEZE_INDEPENDENT_REVIEW.md",
        13421,
        "a0aa207a0a68545d0af7ba5e252d7c30f1349d799e0e61ebf807c2426ee22209",
    ),
    (
        "f105_human",
        "PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE.md",
        15242,
        "5d495ee917357a763e53b73cd40008a02da32918c7cb83503cbd0df851227cef",
    ),
    (
        "f105_machine",
        "research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json",
        23899,
        "560b6275a4e30d188cc35ed8190118ba01ad8fc3bacc9199daf5b6f305cc96c9",
    ),
    (
        "f105_source",
        "src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py",
        25342,
        "567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881",
    ),
    (
        "f105_independent_review",
        "PROJECT_F105_TWO_DOMAIN_CKS_METRIC_INSTANCE_INDEPENDENT_REVIEW.md",
        5932,
        "368fd5444b958c5eef1a62b25ad45062415a6c396863e33864f63a81356171a3",
    ),
    (
        "legacy_b12_receipt_source_transitive",
        "src/heterodiff/evaluation/b12_integrated_offline_candidate.py",
        14944,
        "b77c6eea6859fa9d6181a94a27112d97555e5a4d60ab1df1ee03a30c7808defd",
    ),
    (
        "accepted_adapter_stack_human",
        "PROJECT_B12_TWO_DOMAIN_ADAPTER_STACK.md",
        8866,
        "900eb147602eb7d74e1a54e69d9d684cf8a1e8fc433c030cad4d50a2a2937b49",
    ),
    (
        "accepted_adapter_stack_machine",
        "research/fixtures/manuscript_v3_b12_two_domain_adapter_stack_v1.json",
        9956,
        "ba65fe357caca90f64e89bac9d9c78fbbe379342fcf7f6321aceb4caf4f7b502",
    ),
    (
        "accepted_adapter_stack_source",
        "src/heterodiff/evaluation/b12_two_domain_adapter_stack.py",
        34660,
        "44ece6452c8edfaadc7d6013a37208fb8648d3a6dbb3ce29bcecd97a90880a57",
    ),
    (
        "accepted_adapter_stack_independent_review",
        "PROJECT_B12_TWO_DOMAIN_ADAPTER_STACK_INDEPENDENT_REVIEW.md",
        8571,
        "3441c64ede3298ce5f0f0c58747e96c4818179b46abfa4c0d13753a5f66510e3",
    ),
    (
        "accepted_training_plan_human",
        "PROJECT_F139_F144_F147_TRAINING_CHECKPOINT_PLAN_FREEZE.md",
        19707,
        "ac318d432b0634b96547ffd0773f93c3ad0f4978dc9db287b6b7f13e1cfdf442",
    ),
    (
        "accepted_training_plan_machine",
        "research/fixtures/manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.json",
        82095,
        "ca43c2efa1b378e8ad2989cc258698a3fee9810b721b5e32294906b7ca221e1e",
    ),
    (
        "accepted_training_plan_source",
        "src/heterodiff/experiments/two_domain_training_checkpoint_plan.py",
        33918,
        "9ac7d6e6d93bb0691fde67070dc97b566e716797dd05f82ed053c8dc77e2fbcf",
    ),
    (
        "accepted_training_plan_independent_review",
        "PROJECT_F139_F144_F147_TRAINING_CHECKPOINT_PLAN_FREEZE_INDEPENDENT_REVIEW.md",
        10543,
        "bf049974dee56926e2d9afaafccabcbebb1ee056465022f29040fd627e7b0cdf",
    ),
)

_CAPTURED_MODULE_SPECS = (
    (
        "heterodiff.experiments.matched_total_compute",
        "src/heterodiff/experiments/matched_total_compute.py",
    ),
    (
        "heterodiff.experiments.two_domain_baseline_registry",
        "src/heterodiff/experiments/two_domain_baseline_registry.py",
    ),
    (
        "heterodiff.evaluation.b12_integrated_offline_candidate",
        "src/heterodiff/evaluation/b12_integrated_offline_candidate.py",
    ),
    (
        "heterodiff.evaluation.two_domain_count_normalized_event_cks",
        "src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py",
    ),
    (
        "heterodiff.evaluation.b12_two_domain_adapter_stack",
        "src/heterodiff/evaluation/b12_two_domain_adapter_stack.py",
    ),
    (
        "heterodiff.experiments.two_domain_training_checkpoint_plan",
        "src/heterodiff/experiments/two_domain_training_checkpoint_plan.py",
    ),
    (
        "heterodiff.evaluation.b12_external_author_extension_components",
        SOURCE_REL,
    ),
)


class ValidationError(RuntimeError):
    pass


MAX_FILE_BYTES = 5_000_000


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _digest(domain: str, value: Any) -> str:
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


@contextmanager
def _opened_stable_root(root: Path):
    flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(root, flags)
    except OSError as error:
        raise ValidationError(f"cannot safely open project root: {error}") from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISDIR(before.st_mode):
            raise ValidationError("project root is not a directory")
        root_identity = _identity(before)
        yield descriptor, root_identity
        if _identity(os.fstat(descriptor)) != root_identity:
            raise ValidationError("project root changed during package validation")
    finally:
        os.close(descriptor)


def _assert_root_stable(root_fd: int, root_identity: Tuple[int, ...]) -> None:
    if _identity(os.fstat(root_fd)) != root_identity:
        raise ValidationError("project root changed during package validation")


def _read_stable_regular(
    root_fd: int,
    root_identity: Tuple[int, ...],
    relative_path: str,
) -> bytes:
    relative = _canonical_relative(relative_path)
    _assert_root_stable(root_fd, root_identity)
    opened = []
    parent_identities = []
    current_fd = root_fd
    try:
        for part in relative.parts[:-1]:
            flags = os.O_RDONLY | os.O_DIRECTORY
            if hasattr(os, "O_CLOEXEC"):
                flags |= os.O_CLOEXEC
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                directory_fd = os.open(part, flags, dir_fd=current_fd)
            except OSError as error:
                raise ValidationError(
                    f"cannot safely open parent of {relative_path}: {error}"
                ) from error
            opened.append(directory_fd)
            directory_metadata = os.fstat(directory_fd)
            if not stat.S_ISDIR(directory_metadata.st_mode):
                raise ValidationError(f"parent is not a directory: {relative_path}")
            parent_identities.append(
                (directory_fd, _identity(directory_metadata))
            )
            current_fd = directory_fd
        flags = os.O_RDONLY
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            leaf_fd = os.open(relative.name, flags, dir_fd=current_fd)
        except OSError as error:
            raise ValidationError(
                f"cannot safely open {relative_path}: {error}"
            ) from error
        opened.append(leaf_fd)
        before = os.fstat(leaf_fd)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o644
            or before.st_nlink != 1
            or not 1 <= before.st_size <= MAX_FILE_BYTES
        ):
            raise ValidationError(f"file custody or size differs: {relative_path}")
        chunks = []
        total = 0
        while total <= before.st_size:
            chunk = os.read(
                leaf_fd,
                min(1024 * 1024, before.st_size + 1 - total),
            )
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        after = os.fstat(leaf_fd)
        if _identity(before) != _identity(after):
            raise ValidationError(f"file changed during read: {relative_path}")
        data = b"".join(chunks)
        if len(data) != before.st_size:
            raise ValidationError(f"short or expanded read: {relative_path}")
        for directory_fd, expected_identity in parent_identities:
            if _identity(os.fstat(directory_fd)) != expected_identity:
                raise ValidationError(
                    f"parent changed during read: {relative_path}"
                )
        _assert_root_stable(root_fd, root_identity)
        return data
    finally:
        for descriptor in reversed(opened):
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
    root_fd: int,
    root_identity: Tuple[int, ...],
    expected: Iterable[Tuple[str, str, int, str]],
) -> Tuple[Dict[str, Any], ...]:
    results = []
    for role, path, expected_bytes, expected_sha256 in expected:
        data = _read_stable_regular(root_fd, root_identity, path)
        if len(data) != expected_bytes:
            raise ValidationError(f"byte count mismatch: {path}")
        if hashlib.sha256(data).hexdigest() != expected_sha256:
            raise ValidationError(f"raw SHA-256 mismatch: {path}")
        if not data.endswith(b"\n"):
            raise ValidationError(f"terminal LF missing: {path}")
        results.append(_binding(role, path, data))
    return tuple(results)


def _load_json_no_duplicates(data: bytes) -> Dict[str, Any]:
    if not data.endswith(b"\n") or data[:-1].endswith(b"\n"):
        raise ValidationError("machine record must have exactly one terminal LF")
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


def _fresh_package(name: str, path: Path) -> ModuleType:
    module = ModuleType(name)
    module.__package__ = name
    module.__path__ = [str(path)]  # type: ignore[attr-defined]
    sys.modules[name] = module
    return module


def _compile_captured_modules(
    root: Path, captured: Mapping[str, bytes]
) -> ModuleType:
    sys.dont_write_bytecode = True
    for name in tuple(sys.modules):
        if name == "heterodiff" or name.startswith("heterodiff."):
            del sys.modules[name]
    source_root = root / "src"
    top = _fresh_package("heterodiff", source_root / "heterodiff")
    evaluation = _fresh_package(
        "heterodiff.evaluation", source_root / "heterodiff/evaluation"
    )
    experiments = _fresh_package(
        "heterodiff.experiments", source_root / "heterodiff/experiments"
    )
    setattr(top, "evaluation", evaluation)
    setattr(top, "experiments", experiments)

    candidate: ModuleType | None = None
    for name, relative_path in _CAPTURED_MODULE_SPECS:
        data = captured[relative_path]
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValidationError(f"source is not UTF-8: {relative_path}") from error
        module = ModuleType(name)
        module.__file__ = str(root / relative_path)
        module.__package__ = name.rsplit(".", 1)[0]
        sys.modules[name] = module
        parent_name, child_name = name.rsplit(".", 1)
        setattr(sys.modules[parent_name], child_name, module)
        try:
            code = compile(text, module.__file__, "exec")
            exec(code, module.__dict__)
        except Exception as error:
            raise ValidationError(f"captured module failed: {relative_path}: {error}") from error
        if relative_path == SOURCE_REL:
            candidate = module
    if candidate is None:
        raise ValidationError("candidate module was not captured")
    return candidate


def _capture_source_bytes(
    root_fd: int, root_identity: Tuple[int, ...]
) -> Dict[str, bytes]:
    result: Dict[str, bytes] = {}
    for _, path in _CAPTURED_MODULE_SPECS:
        if path not in result:
            result[path] = _read_stable_regular(root_fd, root_identity, path)
    return result


def _expected_machine(
    root: Path,
    root_fd: int,
    root_identity: Tuple[int, ...],
) -> Dict[str, Any]:
    static_bindings = _verify_fixed_bindings(
        root_fd, root_identity, EXPECTED_STATIC_BINDINGS
    )
    predecessor_bindings = _verify_fixed_bindings(
        root_fd, root_identity, EXPECTED_PREDECESSOR_BINDINGS
    )
    validator_data = _read_stable_regular(
        root_fd, root_identity, VALIDATOR_REL
    )
    if not validator_data.endswith(b"\n"):
        raise ValidationError("validator terminal LF missing")
    validator_binding = _binding("validator", VALIDATOR_REL, validator_data)
    captured = _capture_source_bytes(root_fd, root_identity)
    module = _compile_captured_modules(root, captured)
    source_sha256 = hashlib.sha256(captured[SOURCE_REL]).hexdigest()
    try:
        semantics_raw = module.candidate_semantics(
            module_source_sha256=source_sha256
        )
    except Exception as error:
        raise ValidationError(f"candidate semantics failed: {error}") from error
    semantics = json.loads(_canonical(semantics_raw).decode("ascii"))
    expected_ids = [
        *(f"CSDI_AUTHOR_EXTENSION_{index}" for index in range(1, 5)),
        *(f"EDITPP_AUTHOR_EXTENSION_{index}" for index in range(1, 5)),
    ]
    if semantics["component_implementation_predicate_ids"] != expected_ids:
        raise ValidationError("component implementation predicate roster differs")
    if semantics["draw_count_per_interface"] != 64:
        raise ValidationError("draw count differs from exact 64")
    if len(semantics["implementation_record_sha256s"]) != 8:
        raise ValidationError("implementation-record roster is not exact eight")
    effects = {
        "blocker_delta": 0,
        "field_delta": 0,
        "formal_test_delta": 0,
        "result_delta": 0,
        "science_delta": 0,
        "timetable_task_delta": 0,
        "tracker_edited": False,
    }
    if semantics["effects"] != effects:
        raise ValidationError("candidate effects differ from exact zero delta")
    if any(value is not False for value in semantics["nonclaims"].values()):
        raise ValidationError("candidate contains a forbidden positive claim")
    unsigned = {
        "bindings": [*static_bindings, validator_binding],
        "effects": effects,
        "predecessor_bindings": list(predecessor_bindings),
        "schema_version": SCHEMA_VERSION,
        "semantics": semantics,
        "state": STATE,
    }
    result = dict(unsigned)
    result["record_sha256"] = _digest(SCHEMA_VERSION, unsigned)
    return result


def validate(root: Path) -> Dict[str, Any]:
    with _opened_stable_root(root) as (root_fd, root_identity):
        expected = _expected_machine(root, root_fd, root_identity)
        machine_data = _read_stable_regular(
            root_fd, root_identity, MACHINE_REL
        )
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
        if machine != expected:
            raise ValidationError("machine record differs from reconstructed semantics")
        _assert_root_stable(root_fd, root_identity)
        return {
            "adapter_count": 2,
            "draw_count_per_interface": 64,
            "implementation_predicate_count": 8,
            "record_sha256": machine["record_sha256"],
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--emit-expected", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = _parse_args()
    root = (
        arguments.root.absolute()
        if arguments.root is not None
        else Path(__file__).resolve().parents[2]
    )
    if not root.is_dir():
        print("FAIL — project root is not a directory", file=sys.stderr)
        return 1
    try:
        if arguments.emit_expected:
            with _opened_stable_root(root) as (root_fd, root_identity):
                expected = _expected_machine(
                    root, root_fd, root_identity
                )
                _assert_root_stable(root_fd, root_identity)
            print(_canonical(expected).decode("ascii"))
            return 0
        result = validate(root)
    except Exception as error:
        print(f"FAIL — {error}", file=sys.stderr)
        return 1
    print(
        f"{PASS_TOKEN} — exact eight implementation-only predicates; "
        f"record {result['record_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
