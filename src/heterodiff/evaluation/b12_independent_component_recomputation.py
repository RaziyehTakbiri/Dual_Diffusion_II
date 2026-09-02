"""Independent offline recomputation for the B12 component-binding seam.

This module intentionally does not import :mod:`b12_integration_stack`.  It
reopens an exact binding document, independently verifies the four existing
Formal-Test-29/30 component sources, reruns their deterministic supplied-input
qualifications, and independently serializes the bounded integration result.

The result is an integration/custody fixture only.  It uses no entropy,
network, protected data, clock, training, or scientific execution and does not
close a field, blocker, Formal Test, result slot, or timetable task.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from types import ModuleType
from typing import Any, Dict, Mapping, Sequence, Tuple


BINDING_DOCUMENT_SCHEMA = "heterodiff-b12-component-binding-document-v1"
OUTPUT_SCHEMA = "heterodiff-b12-bound-formal29-30-synthetic-output-v1"
OUTPUT_STATE = "OFFLINE_SYNTHETIC_COMPONENT_QUALIFICATION_ONLY"
MAX_BINDING_DOCUMENT_BYTES = 131_072
MAX_COMPONENT_SOURCE_BYTES = 2_000_000

_COMPONENT_SPECS = (
    (
        "FORMAL_TEST29_FINITE_ACYCLIC_ROUTE_ORACLE",
        "heterodiff.processes.formal_test29_finite_acyclic_route_oracle",
        "src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py",
        "FORMAL_TEST29_FINITE_ACYCLIC_SCHEMA_VERSION",
        "formal-test29-finite-acyclic-route-oracle-v1",
        ("qualify_finite_acyclic_fixture",),
    ),
    (
        "FORMAL_TEST30_SYNTHETIC_COUPLED_PATH",
        "heterodiff.evaluation.formal_test30_synthetic_coupled_path_qualification",
        "src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py",
        "SCHEMA_VERSION",
        "heterodiff-formal-test30-synthetic-coupled-path-v1",
        ("run_frozen_synthetic_qualification",),
    ),
    (
        "FORMAL_TEST29_TEST30_SINGLE_MACROSTEP",
        "heterodiff.evaluation.formal_test29_test30_single_macrostep_integration",
        "src/heterodiff/evaluation/formal_test29_test30_single_macrostep_integration.py",
        "SCHEMA_VERSION",
        "heterodiff-test29-test30-single-macrostep-integration-v1",
        ("frozen_central_jump_fixture", "run_frozen_single_macrostep_qualification"),
    ),
    (
        "FORMAL_TEST29_TEST30_TWO_MACROSTEP",
        "heterodiff.evaluation.formal_test29_test30_two_macrostep_path_qualification",
        "src/heterodiff/evaluation/formal_test29_test30_two_macrostep_path_qualification.py",
        "SCHEMA_VERSION",
        "heterodiff-test29-test30-two-macrostep-path-v1",
        ("run_frozen_two_macrostep_qualification",),
    ),
)


class IndependentRecomputationError(ValueError):
    """Raised when an independent binding or recomputation check fails."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _sha256(raw: bytes) -> str:
    if type(raw) is not bytes:
        raise TypeError("raw digest input must be exact bytes")
    return hashlib.sha256(raw).hexdigest()


def _domain_sha256(domain: str, value: object) -> str:
    if type(domain) is not str or not domain or "\0" in domain:
        raise TypeError("digest domain must be exact nonempty text without NUL")
    return _sha256(domain.encode("ascii") + b"\0" + _canonical_bytes(value))


def _pairs(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    if type(pairs) is not list:
        raise IndependentRecomputationError("JSON object pairs must be a list")
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise IndependentRecomputationError("duplicate or non-text JSON key")
        result[key] = value
    return result


def _strict_json(value: object, *, name: str) -> None:
    if value is None or type(value) in (str, int, bool):
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _strict_json(item, name="%s[%d]" % (name, index))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise IndependentRecomputationError(name + " has a non-text key")
            _strict_json(item, name=name + "." + key)
        return
    raise IndependentRecomputationError(name + " has a non-exact JSON type")


def _decode_canonical(raw: bytes) -> object:
    if type(raw) is not bytes or not raw.endswith(b"\n"):
        raise IndependentRecomputationError("canonical JSON requires terminal LF")
    if not 1 <= len(raw) <= MAX_BINDING_DOCUMENT_BYTES:
        raise IndependentRecomputationError("binding document size is outside bounds")
    try:
        value = json.loads(raw[:-1].decode("ascii"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IndependentRecomputationError("binding document is not canonical JSON") from error
    _strict_json(value, name="binding_document")
    if _canonical_bytes(value) + b"\n" != raw:
        raise IndependentRecomputationError("binding document bytes are noncanonical")
    return value


def _safe_relative_path(value: object) -> PurePosixPath:
    if type(value) is not str or not value or not value.isascii() or "\\" in value:
        raise IndependentRecomputationError("source path must be exact ASCII POSIX text")
    path = PurePosixPath(value)
    if (
        path.as_posix() != value
        or path.is_absolute()
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise IndependentRecomputationError(
            "source path is noncanonical or escapes the project root"
        )
    return path


def _canonical_root(value: object) -> Path:
    if type(value) is not str or not value:
        raise TypeError("project_root must be exact nonempty text")
    path = Path(value)
    if (
        str(path) != value
        or not path.is_absolute()
        or path.resolve(strict=True) != path
    ):
        raise IndependentRecomputationError("project_root must be canonical and absolute")
    return path


def _stable_read(root: Path, relative: PurePosixPath, expected_bytes: int) -> bytes:
    if not isinstance(root, Path) or type(relative) is not PurePosixPath:
        raise TypeError("stable-read inputs must have exact concrete types")
    if type(expected_bytes) is not int or not 1 <= expected_bytes <= MAX_COMPONENT_SOURCE_BYTES:
        raise IndependentRecomputationError("component byte count is outside bounds")
    root_flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        root_flags |= os.O_NOFOLLOW
    root_fd = os.open(str(root), root_flags)
    opened = []
    try:
        before_root = os.fstat(root_fd)
        current = root_fd
        for part in relative.parts[:-1]:
            flags = os.O_RDONLY | os.O_DIRECTORY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            next_fd = os.open(part, flags, dir_fd=current)
            opened.append(next_fd)
            current = next_fd
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        leaf_fd = os.open(relative.name, flags, dir_fd=current)
        opened.append(leaf_fd)
        before = os.fstat(leaf_fd)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o644
            or before.st_nlink != 1
            or before.st_size != expected_bytes
        ):
            raise IndependentRecomputationError("component source custody differs")
        chunks = []
        total = 0
        while total <= expected_bytes:
            chunk = os.read(leaf_fd, min(131_072, expected_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(leaf_fd)
        after_root = os.fstat(root_fd)
        identity = lambda item: (
            item.st_dev,
            item.st_ino,
            item.st_mode,
            item.st_nlink,
            item.st_size,
            item.st_mtime_ns,
            item.st_ctime_ns,
        )
        if len(raw) != expected_bytes or identity(before) != identity(after):
            raise IndependentRecomputationError("component source changed while read")
        if identity(before_root) != identity(after_root):
            raise IndependentRecomputationError("project root changed while read")
        return raw
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)
        os.close(root_fd)


def _checked_binding_rows(document: object, root: Path) -> Tuple[Mapping[str, object], ...]:
    if type(document) is not dict or tuple(document) != ("bindings", "schema_version"):
        raise IndependentRecomputationError("binding document top-level schema differs")
    if document["schema_version"] != BINDING_DOCUMENT_SCHEMA:
        raise IndependentRecomputationError("binding document version differs")
    bindings = document["bindings"]
    if type(bindings) is not list or len(bindings) != len(_COMPONENT_SPECS):
        raise IndependentRecomputationError("binding roster length differs")
    checked = []
    expected_keys = (
        "byte_count",
        "component_id",
        "entrypoints",
        "interface_sha256",
        "module_name",
        "ordinal",
        "schema_attribute",
        "schema_value",
        "source_path",
        "source_sha256",
    )
    for ordinal, (row, spec) in enumerate(zip(bindings, _COMPONENT_SPECS)):
        if type(row) is not dict or tuple(row) != expected_keys:
            raise IndependentRecomputationError("binding row schema differs")
        component_id, module_name, source_path, schema_attribute, schema_value, entrypoints = spec
        fixed = (
            row["ordinal"] == ordinal
            and row["component_id"] == component_id
            and row["module_name"] == module_name
            and row["source_path"] == source_path
            and row["schema_attribute"] == schema_attribute
            and row["schema_value"] == schema_value
            and row["entrypoints"] == list(entrypoints)
        )
        if not fixed or type(row["ordinal"]) is not int:
            raise IndependentRecomputationError("binding identity or order differs")
        if type(row["byte_count"]) is not int or type(row["source_sha256"]) is not str:
            raise IndependentRecomputationError("binding byte metadata has wrong type")
        relative = _safe_relative_path(row["source_path"])
        raw = _stable_read(root, relative, row["byte_count"])
        if _sha256(raw) != row["source_sha256"]:
            raise IndependentRecomputationError("component source digest differs")
        payload = dict(row)
        claimed_interface = payload.pop("interface_sha256")
        if type(claimed_interface) is not str or claimed_interface != _domain_sha256(
            "heterodiff-b12-component-binding-v1", payload
        ):
            raise IndependentRecomputationError("component interface digest differs")
        checked.append(row)
    return tuple(checked)


def _load_modules(rows: Tuple[Mapping[str, object], ...], root: Path) -> Tuple[ModuleType, ...]:
    modules = []
    for row in rows:
        module = importlib.import_module(row["module_name"])
        if type(module) is not ModuleType:
            raise IndependentRecomputationError("component import is not an exact module")
        module_path = Path(module.__file__).resolve(strict=True)
        expected_path = root.joinpath(*PurePosixPath(row["source_path"]).parts)
        if module_path != expected_path:
            raise IndependentRecomputationError("component module path differs")
        if getattr(module, row["schema_attribute"], None) != row["schema_value"]:
            raise IndependentRecomputationError("component runtime schema differs")
        for entrypoint in row["entrypoints"]:
            candidate = getattr(module, entrypoint, None)
            if not callable(candidate) or getattr(candidate, "__module__", None) != module.__name__:
                raise IndependentRecomputationError("component entrypoint differs")
        modules.append(module)
    return tuple(modules)


def _result_document(
    rows: Tuple[Mapping[str, object], ...], modules: Tuple[ModuleType, ...]
) -> Mapping[str, object]:
    test29, test30, single, two = modules
    fixture = single.frozen_central_jump_fixture(test29)
    test29_result = test29.qualify_finite_acyclic_fixture(fixture)
    test30_result = test30.run_frozen_synthetic_qualification()
    single_result = single.run_frozen_single_macrostep_qualification(test29, test30)
    two_result = two.run_frozen_two_macrostep_qualification(single, test29, test30)
    if type(test29_result) is not test29.FiniteAcyclicQualification:
        raise IndependentRecomputationError("Test-29 result type differs")
    if type(test30_result) is not test30.SyntheticCoupledPathQualification:
        raise IndependentRecomputationError("Test-30 result type differs")
    if type(single_result) is not single.FrozenSingleMacrostepQualification:
        raise IndependentRecomputationError("single-macrostep result type differs")
    if type(two_result) is not two.FrozenTwoMacrostepQualification:
        raise IndependentRecomputationError("two-macrostep result type differs")
    return {
        "binding_interface_sha256s": [row["interface_sha256"] for row in rows],
        "effects": {
            "authority_created": False,
            "blocker_delta": 0,
            "data_accessed": False,
            "field_delta": 0,
            "formal_test_delta": 0,
            "network_used": False,
            "result_delta": 0,
            "science_executed": False,
            "tracker_edited": False,
        },
        "formal_test29": {
            "bounded_fixture_completion": test29_result.unconditional_bounded_fixture_completion_proved,
            "closed": test29_result.formal_test29_closed,
            "fixture_id": test29_result.fixture_id,
            "production_integrated": test29_result.production_cp24_execution_integrated,
            "schema_version": test29_result.schema_version,
        },
        "formal_test30": {
            "closed": test30_result.formal_test30_closed,
            "independent_recomputation_present": test30_result.independent_recomputation_present,
            "passed": test30_result.passed,
            "report_sha256": test30_result.report_sha256,
            "schema_version": test30_result.schema_version,
        },
        "schema_version": OUTPUT_SCHEMA,
        "single_macrostep": {
            "blockers_closed": single_result.blockers_closed,
            "formal_tests_closed": single_result.formal_tests_closed,
            "passed": single_result.passed,
            "report_sha256": single_result.report_sha256,
            "schema_version": single_result.schema_version,
        },
        "state": OUTPUT_STATE,
        "two_macrostep": {
            "blockers_closed": two_result.blockers_closed,
            "formal_tests_closed": two_result.formal_tests_closed,
            "parent_custody_authenticated": two_result.parent_custody_authenticated,
            "passed": two_result.passed,
            "report_sha256": two_result.report_sha256,
            "schema_version": two_result.schema_version,
        },
    }


def independently_recompute_component_output(
    project_root: str, binding_document_bytes: bytes
) -> bytes:
    """Return independently reconstructed canonical output bytes.

    ``binding_document_bytes`` is reopened semantically and all source paths are
    validated through stable no-follow descriptors before any qualification is
    run.  This is a separate integration-level orchestration and serializer;
    it does not claim an independent scientific implementation of the parent
    Formal-Test components.
    """

    if type(binding_document_bytes) is not bytes:
        raise TypeError("binding_document_bytes must be exact bytes")
    root = _canonical_root(project_root)
    document = _decode_canonical(binding_document_bytes)
    rows = _checked_binding_rows(document, root)
    modules = _load_modules(rows, root)
    result = _result_document(rows, modules)
    return _canonical_bytes(result) + b"\n"


__all__ = [
    "BINDING_DOCUMENT_SCHEMA",
    "OUTPUT_SCHEMA",
    "OUTPUT_STATE",
    "IndependentRecomputationError",
    "independently_recompute_component_output",
]
