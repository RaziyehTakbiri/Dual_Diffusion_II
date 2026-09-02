"""Offline B12 capsule, ledger, binding, and runner integration stack.

This successor implementation consumes the corrected B06-derived 22-adapter
roster exported by :mod:`b12_two_domain_adapter_stack`.  It deliberately does
not use the stale eight-row literature-family configuration hashes embedded in
the accepted zero-delta B12 v2 candidate.  The accepted candidate's exact
immutable receipt component types remain the wire interface.

All operations in this module are deterministic and local.  The capsule is a
closed-world *component/evidence directory roster*: it contains the exact
component-binding document and every payload named by its manifest, but it is
not represented as a standalone executable or a transitive dependency/source
closure.  Synthetic fixture receipts qualify interfaces only: they do not
authenticate a person, select a production runtime, access data, execute
science, close Formal Tests 29/30, or close B08/B12 or any timetable task.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from types import ModuleType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from heterodiff.evaluation import b12_integrated_offline_candidate as _v2


ZERO_SHA256 = "0" * 64
CAPSULE_SCHEMA = (
    "heterodiff-b12-closed-world-component-evidence-capsule-v1"
)
CAPSULE_FINALIZED_SCHEMA = (
    "heterodiff-b12-closed-world-component-evidence-capsule-finalized-v1"
)
CAPSULE_SCOPE = (
    "CLOSED_WORLD_COMPONENT_EVIDENCE_DIRECTORY_ROSTER_"
    "NOT_STANDALONE_EXECUTABLE_OR_TRANSITIVE_DEPENDENCY_CLOSURE"
)
COMPONENT_BINDING_PAYLOAD_NAME = "component-bindings.json"
COMPONENT_BINDING_DOCUMENT_SCHEMA = (
    "heterodiff-b12-component-binding-document-v1"
)
BOUND_OUTPUT_SCHEMA = "heterodiff-b12-bound-formal29-30-synthetic-output-v1"
BOUND_OUTPUT_STATE = "OFFLINE_SYNTHETIC_COMPONENT_QUALIFICATION_ONLY"
LEDGER_FILE_SCHEMA = "heterodiff-b12-durable-ledger-event-v1"
RUNTIME_IDENTITY_SCHEMA = "heterodiff-b12-runtime-identity-binding-v1"
RUNNER_STATE = "B12_INTEGRATION_STRUCTURE_ONLY_REAL_RESIDUAL_RECEIPTS_OPEN"
PRODUCTION_RUNNER_STATE = (
    "B12_PRODUCTION_EVIDENCE_BOUND_PENDING_INDEPENDENT_REVIEW"
)

MAX_CAPSULE_FILES = 64
MAX_CAPSULE_FILE_BYTES = 4_000_000
MAX_CAPSULE_MANIFEST_BYTES = 1_000_000
MAX_LEDGER_EVENT_BYTES = 65_536

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

DEFAULT_CAPSULE_SOURCE_PATHS = (
    "src/heterodiff/evaluation/b12_integrated_offline_candidate.py",
    "src/heterodiff/evaluation/b12_two_domain_adapter_stack.py",
    "src/heterodiff/evaluation/b12_integration_stack.py",
    "src/heterodiff/evaluation/b12_independent_component_recomputation.py",
    "src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py",
    "src/heterodiff/experiments/two_domain_baseline_registry.py",
    "src/heterodiff/experiments/matched_total_compute.py",
    "src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py",
    "src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py",
    "src/heterodiff/evaluation/formal_test29_test30_single_macrostep_integration.py",
    "src/heterodiff/evaluation/formal_test29_test30_two_macrostep_path_qualification.py",
)

_RESIDUAL_IDS = tuple(_v2.semantics()["residual_predicate_ids"])
if len(_RESIDUAL_IDS) != 50 or len(set(_RESIDUAL_IDS)) != 50:
    raise RuntimeError("accepted B12 residual roster is not exact 50-row unique")

_NONPRODUCTION_AUTHENTICATION_MARKERS = frozenset(
    (
        "DEMO",
        "FIXTURE",
        "LOCAL",
        "MOCK",
        "OFFLINE",
        "QUALIFICATION",
        "SYNTHETIC",
        "TEST",
    )
)


class B12IntegrationError(ValueError):
    """Raised before an object crosses the B12 integration boundary."""


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
        raise TypeError("digest input must be exact bytes")
    return hashlib.sha256(raw).hexdigest()


def _domain_sha256(domain: str, value: object) -> str:
    if type(domain) is not str or not domain or "\0" in domain:
        raise TypeError("digest domain must be exact nonempty text without NUL")
    return _sha256(domain.encode("ascii") + b"\0" + _canonical_bytes(value))


def _raw_domain_sha256(domain: str, raw: bytes) -> str:
    if type(domain) is not str or not domain or "\0" in domain:
        raise TypeError("digest domain must be exact nonempty text without NUL")
    if type(raw) is not bytes:
        raise TypeError("raw digest input must be exact bytes")
    return _sha256(domain.encode("ascii") + b"\0" + raw)


def _exact_sha256(value: object, *, name: str, nonzero: bool = False) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise B12IntegrationError(name + " must be lowercase SHA-256 hex")
    if nonzero and value == ZERO_SHA256:
        raise B12IntegrationError(name + " must be nonzero")
    return value


def _exact_identifier(value: object, *, name: str, maximum: int = 160) -> str:
    if type(value) is not str or not value or len(value) > maximum or not value.isascii():
        raise TypeError(name + " must be bounded nonempty exact ASCII text")
    if any(not (character.isalnum() or character in "-_.:") for character in value):
        raise B12IntegrationError(name + " contains a noncanonical character")
    return value


def _safe_relative_path(value: object) -> PurePosixPath:
    if type(value) is not str or not value or not value.isascii() or "\\" in value:
        raise B12IntegrationError("relative path must be exact ASCII POSIX text")
    path = PurePosixPath(value)
    if (
        path.as_posix() != value
        or path.is_absolute()
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise B12IntegrationError("relative path is noncanonical or escapes its root")
    return path


def _safe_leaf_name(value: object) -> str:
    text = _exact_identifier(value, name="leaf_name", maximum=128)
    if "/" in text or text in (".", ".."):
        raise B12IntegrationError("leaf name is not a single safe component")
    return text


def _canonical_root(value: object, *, mode: Optional[int] = None) -> Path:
    if type(value) is not str or not value:
        raise TypeError("root path must be exact nonempty text")
    path = Path(value)
    if (
        str(path) != value
        or not path.is_absolute()
        or path.resolve(strict=True) != path
    ):
        raise B12IntegrationError("root path must be canonical and absolute")
    metadata = path.lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise B12IntegrationError("root path must be a real directory")
    if mode is not None and stat.S_IMODE(metadata.st_mode) != mode:
        raise B12IntegrationError("root directory mode differs")
    return path


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


def _stable_read_path(
    root: Path,
    relative: PurePosixPath,
    *,
    expected_mode: int,
    maximum_bytes: int,
    expected_bytes: Optional[int] = None,
) -> bytes:
    if not isinstance(root, Path) or type(relative) is not PurePosixPath:
        raise TypeError("stable-read paths must have exact concrete types")
    if type(expected_mode) is not int or type(maximum_bytes) is not int:
        raise TypeError("stable-read bounds must be exact integers")
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
            or stat.S_IMODE(before.st_mode) != expected_mode
            or before.st_nlink != 1
            or not 0 <= before.st_size <= maximum_bytes
            or (expected_bytes is not None and before.st_size != expected_bytes)
        ):
            raise B12IntegrationError("file custody or size differs")
        chunks = []
        total = 0
        while total <= before.st_size:
            chunk = os.read(leaf_fd, min(131_072, before.st_size + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(leaf_fd)
        after_root = os.fstat(root_fd)
        if (
            len(raw) != before.st_size
            or _identity(before) != _identity(after)
            or _identity(before_root) != _identity(after_root)
        ):
            raise B12IntegrationError("file or root changed during stable read")
        return raw
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)
        os.close(root_fd)


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
                raise B12IntegrationError(name + " contains a non-text key")
            _strict_json(item, name=name + "." + key)
        return
    raise B12IntegrationError(name + " contains a non-exact JSON type")


def _pairs(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    if type(pairs) is not list:
        raise B12IntegrationError("JSON object pairs must be an exact list")
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise B12IntegrationError("duplicate or non-text JSON key")
        result[key] = value
    return result


def _decode_canonical(raw: bytes, *, maximum_bytes: int) -> object:
    if type(raw) is not bytes or not raw.endswith(b"\n"):
        raise B12IntegrationError("canonical JSON requires exact bytes and terminal LF")
    if type(maximum_bytes) is not int or not 1 <= len(raw) <= maximum_bytes:
        raise B12IntegrationError("canonical JSON byte count is outside bounds")
    try:
        value = json.loads(raw[:-1].decode("ascii"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise B12IntegrationError("canonical JSON decoding failed") from error
    _strict_json(value, name="document")
    if _canonical_bytes(value) + b"\n" != raw:
        raise B12IntegrationError("JSON bytes are not canonical")
    return value


@dataclass(frozen=True)
class ReceiptAuthentication:
    reviewer_principal_id: str
    authentication_method_id: str
    authentication_evidence_sha256: str

    def validate(self) -> None:
        if type(self) is not ReceiptAuthentication:
            raise TypeError("authentication must have exact concrete type")
        _exact_identifier(self.reviewer_principal_id, name="reviewer_principal_id")
        _exact_identifier(self.authentication_method_id, name="authentication_method_id")
        _exact_sha256(
            self.authentication_evidence_sha256,
            name="authentication_evidence_sha256",
            nonzero=True,
        )


def build_authenticated_predicate(
    predicate_id: str,
    subject_sha256: str,
    authentication: ReceiptAuthentication,
) -> _v2.AuthenticatedPredicateReceipt:
    _exact_identifier(predicate_id, name="predicate_id")
    if predicate_id in _RESIDUAL_IDS:
        raise B12IntegrationError(
            "real residual receipts must be caller supplied, not locally minted"
        )
    subject = _exact_sha256(subject_sha256, name="subject_sha256")
    if type(authentication) is not ReceiptAuthentication:
        raise TypeError("authentication must have exact concrete type")
    authentication.validate()
    payload = {
        "authentication_evidence_sha256": authentication.authentication_evidence_sha256,
        "authentication_method_id": authentication.authentication_method_id,
        "disposition": "ACCEPT",
        "predicate_id": predicate_id,
        "reviewer_principal_id": authentication.reviewer_principal_id,
        "subject_sha256": subject,
    }
    receipt = _v2.AuthenticatedPredicateReceipt(
        predicate_id=predicate_id,
        subject_sha256=subject,
        reviewer_principal_id=authentication.reviewer_principal_id,
        authentication_method_id=authentication.authentication_method_id,
        authentication_evidence_sha256=authentication.authentication_evidence_sha256,
        disposition="ACCEPT",
        receipt_sha256=_v2.sha("heterodiff-b12-authenticated-predicate-v1", payload),
    )
    receipt.payload()
    return receipt


def _require_production_authentication(
    receipt: _v2.AuthenticatedPredicateReceipt,
) -> None:
    if type(receipt) is not _v2.AuthenticatedPredicateReceipt:
        raise TypeError("predicate receipt must have exact accepted type")
    payload = receipt.payload()
    for field_name in ("reviewer_principal_id", "authentication_method_id"):
        value = payload[field_name]
        _exact_identifier(value, name=field_name)
        normalized = value.upper()
        if any(
            marker in normalized
            for marker in _NONPRODUCTION_AUTHENTICATION_MARKERS
        ):
            raise B12IntegrationError(
                "real residual receipt uses a local or synthetic authentication identity"
            )


@dataclass(frozen=True)
class RuntimeIdentityBinding:
    schema_version: str
    runtime_identity_id: str
    hardware_receipt_sha256: str
    software_environment_sha256: str
    lockfile_sha256: str
    deterministic_settings_sha256: str
    capacity_receipt_sha256: str
    generation: int
    predecessor_binding_sha256: str
    binding_sha256: str

    def payload(self) -> Mapping[str, object]:
        if type(self) is not RuntimeIdentityBinding:
            raise TypeError("runtime identity must have exact concrete type")
        if self.schema_version != RUNTIME_IDENTITY_SCHEMA:
            raise B12IntegrationError("runtime identity schema differs")
        _exact_identifier(self.runtime_identity_id, name="runtime_identity_id")
        fields = (
            self.hardware_receipt_sha256,
            self.software_environment_sha256,
            self.lockfile_sha256,
            self.deterministic_settings_sha256,
            self.capacity_receipt_sha256,
        )
        for name, value in zip(
            (
                "hardware_receipt_sha256",
                "software_environment_sha256",
                "lockfile_sha256",
                "deterministic_settings_sha256",
                "capacity_receipt_sha256",
            ),
            fields,
        ):
            _exact_sha256(value, name=name, nonzero=True)
        if type(self.generation) is not int or self.generation < 1:
            raise TypeError("runtime identity generation must be a positive exact integer")
        predecessor = _exact_sha256(
            self.predecessor_binding_sha256,
            name="predecessor_binding_sha256",
        )
        if (self.generation == 1) != (predecessor == ZERO_SHA256):
            raise B12IntegrationError("runtime identity predecessor/generation differs")
        payload = {
            "capacity_receipt_sha256": self.capacity_receipt_sha256,
            "deterministic_settings_sha256": self.deterministic_settings_sha256,
            "generation": self.generation,
            "hardware_receipt_sha256": self.hardware_receipt_sha256,
            "lockfile_sha256": self.lockfile_sha256,
            "predecessor_binding_sha256": predecessor,
            "runtime_identity_id": self.runtime_identity_id,
            "schema_version": self.schema_version,
            "software_environment_sha256": self.software_environment_sha256,
        }
        if self.binding_sha256 != _domain_sha256(
            "heterodiff-b12-runtime-identity-binding-v1", payload
        ):
            raise B12IntegrationError("runtime identity binding digest differs")
        return payload

    def validate_fresh(
        self, expected_generation: int, expected_predecessor_sha256: str
    ) -> None:
        self.payload()
        if type(expected_generation) is not int or expected_generation < 1:
            raise TypeError("expected_generation must be a positive exact integer")
        expected_predecessor = _exact_sha256(
            expected_predecessor_sha256,
            name="expected_predecessor_sha256",
        )
        if (
            self.generation != expected_generation
            or self.predecessor_binding_sha256 != expected_predecessor
        ):
            raise B12IntegrationError("runtime identity binding is stale")

    @classmethod
    def from_mapping(cls, value: object) -> "RuntimeIdentityBinding":
        expected = (
            "binding_sha256",
            "capacity_receipt_sha256",
            "deterministic_settings_sha256",
            "generation",
            "hardware_receipt_sha256",
            "lockfile_sha256",
            "predecessor_binding_sha256",
            "runtime_identity_id",
            "schema_version",
            "software_environment_sha256",
        )
        if type(value) is not dict or tuple(sorted(value)) != expected:
            raise B12IntegrationError("runtime identity mapping has missing or extra fields")
        result = cls(
            schema_version=value["schema_version"],
            runtime_identity_id=value["runtime_identity_id"],
            hardware_receipt_sha256=value["hardware_receipt_sha256"],
            software_environment_sha256=value["software_environment_sha256"],
            lockfile_sha256=value["lockfile_sha256"],
            deterministic_settings_sha256=value["deterministic_settings_sha256"],
            capacity_receipt_sha256=value["capacity_receipt_sha256"],
            generation=value["generation"],
            predecessor_binding_sha256=value["predecessor_binding_sha256"],
            binding_sha256=value["binding_sha256"],
        )
        result.payload()
        return result


@dataclass(frozen=True)
class ComponentBinding:
    ordinal: int
    component_id: str
    module_name: str
    source_path: str
    source_sha256: str
    byte_count: int
    schema_attribute: str
    schema_value: str
    entrypoints: Tuple[str, ...]
    interface_sha256: str

    def payload(self) -> Mapping[str, object]:
        if type(self) is not ComponentBinding:
            raise TypeError("component binding must have exact concrete type")
        if type(self.ordinal) is not int or not 0 <= self.ordinal < len(_COMPONENT_SPECS):
            raise TypeError("component ordinal must be an in-range exact integer")
        spec = _COMPONENT_SPECS[self.ordinal]
        expected = (self.component_id, self.module_name, self.source_path,
                    self.schema_attribute, self.schema_value, self.entrypoints)
        if expected != (spec[0], spec[1], spec[2], spec[3], spec[4], spec[5]):
            raise B12IntegrationError("component binding identity differs")
        _safe_relative_path(self.source_path)
        _exact_sha256(self.source_sha256, name="component source_sha256", nonzero=True)
        if type(self.byte_count) is not int or not 1 <= self.byte_count <= MAX_CAPSULE_FILE_BYTES:
            raise TypeError("component byte_count must be a bounded positive exact integer")
        if type(self.entrypoints) is not tuple or not all(
            type(value) is str for value in self.entrypoints
        ):
            raise TypeError("component entrypoints must be exact text in an exact tuple")
        payload = {
            "byte_count": self.byte_count,
            "component_id": self.component_id,
            "entrypoints": list(self.entrypoints),
            "module_name": self.module_name,
            "ordinal": self.ordinal,
            "schema_attribute": self.schema_attribute,
            "schema_value": self.schema_value,
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
        }
        if self.interface_sha256 != _domain_sha256(
            "heterodiff-b12-component-binding-v1", payload
        ):
            raise B12IntegrationError("component interface digest differs")
        return payload

    def validate_source(self, project_root: str) -> ModuleType:
        self.payload()
        root = _canonical_root(project_root)
        raw = _stable_read_path(
            root,
            _safe_relative_path(self.source_path),
            expected_mode=0o644,
            maximum_bytes=MAX_CAPSULE_FILE_BYTES,
            expected_bytes=self.byte_count,
        )
        if _sha256(raw) != self.source_sha256:
            raise B12IntegrationError("component source digest differs")
        module = importlib.import_module(self.module_name)
        if type(module) is not ModuleType:
            raise B12IntegrationError("component import is not an exact module")
        if Path(module.__file__).resolve(strict=True) != root.joinpath(
            *_safe_relative_path(self.source_path).parts
        ):
            raise B12IntegrationError("component import path differs")
        if getattr(module, self.schema_attribute, None) != self.schema_value:
            raise B12IntegrationError("component runtime schema differs")
        for entrypoint in self.entrypoints:
            candidate = getattr(module, entrypoint, None)
            if not callable(candidate) or getattr(candidate, "__module__", None) != module.__name__:
                raise B12IntegrationError("component entrypoint differs")
        return module


def build_component_bindings(project_root: str) -> Tuple[ComponentBinding, ...]:
    root = _canonical_root(project_root)
    bindings = []
    for ordinal, spec in enumerate(_COMPONENT_SPECS):
        component_id, module_name, source_path, schema_attribute, schema_value, entrypoints = spec
        raw = _stable_read_path(
            root,
            _safe_relative_path(source_path),
            expected_mode=0o644,
            maximum_bytes=MAX_CAPSULE_FILE_BYTES,
        )
        payload = {
            "byte_count": len(raw),
            "component_id": component_id,
            "entrypoints": list(entrypoints),
            "module_name": module_name,
            "ordinal": ordinal,
            "schema_attribute": schema_attribute,
            "schema_value": schema_value,
            "source_path": source_path,
            "source_sha256": _sha256(raw),
        }
        binding = ComponentBinding(
            ordinal=ordinal,
            component_id=component_id,
            module_name=module_name,
            source_path=source_path,
            source_sha256=payload["source_sha256"],
            byte_count=len(raw),
            schema_attribute=schema_attribute,
            schema_value=schema_value,
            entrypoints=entrypoints,
            interface_sha256=_domain_sha256(
                "heterodiff-b12-component-binding-v1", payload
            ),
        )
        binding.validate_source(str(root))
        bindings.append(binding)
    return tuple(bindings)


def component_binding_document_bytes(bindings: object) -> bytes:
    if type(bindings) is not tuple or len(bindings) != len(_COMPONENT_SPECS):
        raise TypeError("bindings must be the exact complete tuple")
    if not all(type(binding) is ComponentBinding for binding in bindings):
        raise TypeError("every component binding must have exact concrete type")
    rows = []
    for ordinal, binding in enumerate(bindings):
        if binding.ordinal != ordinal:
            raise B12IntegrationError("component binding order differs")
        row = dict(binding.payload())
        row["interface_sha256"] = binding.interface_sha256
        rows.append(row)
    document = {
        "bindings": rows,
        "schema_version": COMPONENT_BINDING_DOCUMENT_SCHEMA,
    }
    return _canonical_bytes(document) + b"\n"


def _validate_component_binding_payload(
    binding_document: bytes,
    files: Tuple["CapsuleFileRecord", ...],
) -> Tuple[ComponentBinding, ...]:
    """Validate the in-capsule binding document against its source payloads."""

    document = _decode_canonical(
        binding_document, maximum_bytes=MAX_CAPSULE_MANIFEST_BYTES
    )
    if (
        type(document) is not dict
        or tuple(document) != ("bindings", "schema_version")
        or document["schema_version"] != COMPONENT_BINDING_DOCUMENT_SCHEMA
    ):
        raise B12IntegrationError("component binding payload schema differs")
    rows = document["bindings"]
    if type(rows) is not list or len(rows) != len(_COMPONENT_SPECS):
        raise B12IntegrationError("component binding payload roster differs")
    if type(files) is not tuple or not all(
        type(item) is CapsuleFileRecord for item in files
    ):
        raise TypeError("capsule files must contain exact file records")
    by_source_path = {item.source_path: item for item in files}
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
    bindings = []
    for ordinal, row in enumerate(rows):
        if type(row) is not dict or tuple(row) != expected_keys:
            raise B12IntegrationError("component binding payload row schema differs")
        if type(row["entrypoints"]) is not list or not all(
            type(value) is str for value in row["entrypoints"]
        ):
            raise TypeError("component binding entrypoints must be exact text list")
        binding = ComponentBinding(
            ordinal=row["ordinal"],
            component_id=row["component_id"],
            module_name=row["module_name"],
            source_path=row["source_path"],
            source_sha256=row["source_sha256"],
            byte_count=row["byte_count"],
            schema_attribute=row["schema_attribute"],
            schema_value=row["schema_value"],
            entrypoints=tuple(row["entrypoints"]),
            interface_sha256=row["interface_sha256"],
        )
        if binding.ordinal != ordinal:
            raise B12IntegrationError("component binding payload order differs")
        binding.payload()
        source = by_source_path.get(binding.source_path)
        if (
            source is None
            or source.byte_count != binding.byte_count
            or source.raw_sha256 != binding.source_sha256
        ):
            raise B12IntegrationError(
                "component binding payload is not bound to its capsule source"
            )
        bindings.append(binding)
    return tuple(bindings)


def _bound_result_document(
    bindings: Tuple[ComponentBinding, ...], modules: Tuple[ModuleType, ...]
) -> Mapping[str, object]:
    if type(bindings) is not tuple or type(modules) is not tuple:
        raise TypeError("bound-result inputs must be exact tuples")
    if len(bindings) != 4 or len(modules) != 4:
        raise B12IntegrationError("bound-result component roster differs")
    test29, test30, single, two = modules
    fixture = single.frozen_central_jump_fixture(test29)
    test29_result = test29.qualify_finite_acyclic_fixture(fixture)
    test30_result = test30.run_frozen_synthetic_qualification()
    single_result = single.run_frozen_single_macrostep_qualification(test29, test30)
    two_result = two.run_frozen_two_macrostep_qualification(single, test29, test30)
    if type(test29_result) is not test29.FiniteAcyclicQualification:
        raise B12IntegrationError("Test-29 result type differs")
    if type(test30_result) is not test30.SyntheticCoupledPathQualification:
        raise B12IntegrationError("Test-30 result type differs")
    if type(single_result) is not single.FrozenSingleMacrostepQualification:
        raise B12IntegrationError("single-macrostep result type differs")
    if type(two_result) is not two.FrozenTwoMacrostepQualification:
        raise B12IntegrationError("two-macrostep result type differs")
    return {
        "binding_interface_sha256s": [
            binding.interface_sha256 for binding in bindings
        ],
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
            "bounded_fixture_completion": (
                test29_result.unconditional_bounded_fixture_completion_proved
            ),
            "closed": test29_result.formal_test29_closed,
            "fixture_id": test29_result.fixture_id,
            "production_integrated": (
                test29_result.production_cp24_execution_integrated
            ),
            "schema_version": test29_result.schema_version,
        },
        "formal_test30": {
            "closed": test30_result.formal_test30_closed,
            "independent_recomputation_present": (
                test30_result.independent_recomputation_present
            ),
            "passed": test30_result.passed,
            "report_sha256": test30_result.report_sha256,
            "schema_version": test30_result.schema_version,
        },
        "schema_version": BOUND_OUTPUT_SCHEMA,
        "single_macrostep": {
            "blockers_closed": single_result.blockers_closed,
            "formal_tests_closed": single_result.formal_tests_closed,
            "passed": single_result.passed,
            "report_sha256": single_result.report_sha256,
            "schema_version": single_result.schema_version,
        },
        "state": BOUND_OUTPUT_STATE,
        "two_macrostep": {
            "blockers_closed": two_result.blockers_closed,
            "formal_tests_closed": two_result.formal_tests_closed,
            "parent_custody_authenticated": (
                two_result.parent_custody_authenticated
            ),
            "passed": two_result.passed,
            "report_sha256": two_result.report_sha256,
            "schema_version": two_result.schema_version,
        },
    }


def run_bound_component_output(
    project_root: str, bindings: object
) -> bytes:
    if type(bindings) is not tuple or len(bindings) != len(_COMPONENT_SPECS):
        raise TypeError("bindings must be the exact complete tuple")
    if not all(type(binding) is ComponentBinding for binding in bindings):
        raise TypeError("component binding member has wrong concrete type")
    modules = tuple(binding.validate_source(project_root) for binding in bindings)
    result = _bound_result_document(bindings, modules)
    return _canonical_bytes(result) + b"\n"


@dataclass(frozen=True)
class BoundOutputPair:
    binding_document_bytes: bytes
    candidate_output_bytes: bytes
    independent_output_bytes: bytes
    candidate_output_sha256: str
    independent_output_sha256: str
    independent_implementation_sha256: str

    def validate(self) -> None:
        if type(self) is not BoundOutputPair:
            raise TypeError("bound output pair must have exact concrete type")
        for name, value in (
            ("binding_document_bytes", self.binding_document_bytes),
            ("candidate_output_bytes", self.candidate_output_bytes),
            ("independent_output_bytes", self.independent_output_bytes),
        ):
            if type(value) is not bytes or not value.endswith(b"\n"):
                raise TypeError(name + " must be exact canonical bytes with terminal LF")
        candidate = _sha256(self.candidate_output_bytes)
        independent = _sha256(self.independent_output_bytes)
        if self.candidate_output_sha256 != candidate:
            raise B12IntegrationError("candidate output digest differs")
        if self.independent_output_sha256 != independent:
            raise B12IntegrationError("independent output digest differs")
        if candidate != independent or self.candidate_output_bytes != self.independent_output_bytes:
            raise B12IntegrationError("independent output differs from candidate output")
        _exact_sha256(
            self.independent_implementation_sha256,
            name="independent_implementation_sha256",
            nonzero=True,
        )


def run_and_independently_recompute(
    project_root: str, bindings: object
) -> BoundOutputPair:
    if type(bindings) is not tuple or not all(
        type(binding) is ComponentBinding for binding in bindings
    ):
        raise TypeError("bindings must contain exact ComponentBinding values")
    root = _canonical_root(project_root)
    binding_bytes = component_binding_document_bytes(bindings)
    candidate_bytes = run_bound_component_output(str(root), bindings)
    independent_path = _safe_relative_path(
        "src/heterodiff/evaluation/b12_independent_component_recomputation.py"
    )
    independent_raw = _stable_read_path(
        root,
        independent_path,
        expected_mode=0o644,
        maximum_bytes=MAX_CAPSULE_FILE_BYTES,
    )
    independent_module = importlib.import_module(
        "heterodiff.evaluation.b12_independent_component_recomputation"
    )
    if type(independent_module) is not ModuleType:
        raise B12IntegrationError("independent recomputation import differs")
    if Path(independent_module.__file__).resolve(strict=True) != root.joinpath(
        *independent_path.parts
    ):
        raise B12IntegrationError("independent recomputation source path differs")
    independent_bytes = independent_module.independently_recompute_component_output(
        str(root), binding_bytes
    )
    result = BoundOutputPair(
        binding_document_bytes=binding_bytes,
        candidate_output_bytes=candidate_bytes,
        independent_output_bytes=independent_bytes,
        candidate_output_sha256=_sha256(candidate_bytes),
        independent_output_sha256=_sha256(independent_bytes),
        independent_implementation_sha256=_sha256(independent_raw),
    )
    result.validate()
    return result


@dataclass(frozen=True)
class CapsuleFileRecord:
    ordinal: int
    source_path: str
    payload_name: str
    byte_count: int
    raw_sha256: str
    raw_bytes: bytes

    def payload(self) -> Mapping[str, object]:
        if type(self) is not CapsuleFileRecord:
            raise TypeError("capsule file record must have exact concrete type")
        if type(self.ordinal) is not int or not 0 <= self.ordinal < MAX_CAPSULE_FILES:
            raise TypeError("capsule ordinal must be an in-range exact integer")
        _safe_relative_path(self.source_path)
        expected_name = "%03d.payload" % self.ordinal
        if self.payload_name != expected_name:
            raise B12IntegrationError("capsule payload name differs")
        if type(self.byte_count) is not int or not 1 <= self.byte_count <= MAX_CAPSULE_FILE_BYTES:
            raise TypeError("capsule byte_count must be bounded positive exact integer")
        if type(self.raw_bytes) is not bytes or len(self.raw_bytes) != self.byte_count:
            raise TypeError("capsule raw bytes differ from byte_count")
        digest = _exact_sha256(self.raw_sha256, name="capsule raw_sha256", nonzero=True)
        if _sha256(self.raw_bytes) != digest:
            raise B12IntegrationError("capsule raw digest differs")
        return {
            "byte_count": self.byte_count,
            "ordinal": self.ordinal,
            "payload_name": self.payload_name,
            "raw_sha256": digest,
            "source_path": self.source_path,
        }


def _predicate_document(receipt: _v2.AuthenticatedPredicateReceipt) -> Mapping[str, object]:
    if type(receipt) is not _v2.AuthenticatedPredicateReceipt:
        raise TypeError("predicate receipt must have exact accepted type")
    payload = dict(receipt.payload())
    payload["receipt_sha256"] = receipt.receipt_sha256
    return payload


def _predicate_from_document(value: object) -> _v2.AuthenticatedPredicateReceipt:
    expected = (
        "authentication_evidence_sha256",
        "authentication_method_id",
        "disposition",
        "predicate_id",
        "receipt_sha256",
        "reviewer_principal_id",
        "subject_sha256",
    )
    if type(value) is not dict or tuple(sorted(value)) != expected:
        raise B12IntegrationError("predicate receipt document schema differs")
    receipt = _v2.AuthenticatedPredicateReceipt(
        predicate_id=value["predicate_id"],
        subject_sha256=value["subject_sha256"],
        reviewer_principal_id=value["reviewer_principal_id"],
        authentication_method_id=value["authentication_method_id"],
        authentication_evidence_sha256=value["authentication_evidence_sha256"],
        disposition=value["disposition"],
        receipt_sha256=value["receipt_sha256"],
    )
    receipt.payload()
    return receipt


@dataclass(frozen=True)
class ClosedWorldCapsulePlan:
    capsule_id: str
    files: Tuple[CapsuleFileRecord, ...]
    component_binding_document_bytes: bytes
    component_binding_document_sha256: str
    receipt: _v2.CapsuleReceipt
    manifest_bytes: bytes
    manifest_raw_sha256: str

    def validate(self) -> None:
        if type(self) is not ClosedWorldCapsulePlan:
            raise TypeError("capsule plan must have exact concrete type")
        _exact_identifier(self.capsule_id, name="capsule_id")
        if type(self.files) is not tuple or not 1 <= len(self.files) <= MAX_CAPSULE_FILES:
            raise TypeError("capsule files must be a bounded nonempty exact tuple")
        if not all(type(item) is CapsuleFileRecord for item in self.files):
            raise TypeError("capsule file member has wrong concrete type")
        for ordinal, item in enumerate(self.files):
            if item.ordinal != ordinal:
                raise B12IntegrationError("capsule file order differs")
            item.payload()
        source_paths = tuple(item.source_path for item in self.files)
        payload_names = tuple(item.payload_name for item in self.files)
        digests = tuple(item.raw_sha256 for item in self.files)
        if (
            len(set(source_paths)) != len(source_paths)
            or len(set(payload_names)) != len(payload_names)
            or len(set(digests)) != len(digests)
        ):
            raise B12IntegrationError("capsule path or digest roster is not unique")
        if (
            type(self.component_binding_document_bytes) is not bytes
            or not self.component_binding_document_bytes.endswith(b"\n")
        ):
            raise TypeError(
                "component binding document must be exact canonical bytes with terminal LF"
            )
        binding_sha256 = _exact_sha256(
            self.component_binding_document_sha256,
            name="component_binding_document_sha256",
            nonzero=True,
        )
        if _sha256(self.component_binding_document_bytes) != binding_sha256:
            raise B12IntegrationError("component binding payload digest differs")
        _validate_component_binding_payload(
            self.component_binding_document_bytes, self.files
        )
        if type(self.receipt) is not _v2.CapsuleReceipt:
            raise TypeError("capsule receipt must have exact accepted type")
        self.receipt.validate()
        if self.receipt.capsule_id != self.capsule_id:
            raise B12IntegrationError("capsule receipt identity differs")
        receipt_digests = digests + (binding_sha256,)
        if len(set(receipt_digests)) != len(receipt_digests):
            raise B12IntegrationError("capsule payload digest roster is not unique")
        if self.receipt.ordered_file_sha256s != receipt_digests:
            raise B12IntegrationError("capsule receipt file digest roster differs")
        expected_manifest = _capsule_manifest_document(
            self.capsule_id,
            self.files,
            self.component_binding_document_bytes,
            self.component_binding_document_sha256,
            self.receipt,
        )
        if self.manifest_bytes != _canonical_bytes(expected_manifest) + b"\n":
            raise B12IntegrationError("capsule manifest bytes differ")
        if self.manifest_raw_sha256 != _sha256(self.manifest_bytes):
            raise B12IntegrationError("capsule manifest raw digest differs")


def _capsule_manifest_document(
    capsule_id: str,
    files: Tuple[CapsuleFileRecord, ...],
    component_binding_document_bytes: bytes,
    component_binding_document_sha256: str,
    receipt: _v2.CapsuleReceipt,
) -> Mapping[str, object]:
    return {
        "accepted_capsule_receipt": {
            "capsule_id": receipt.capsule_id,
            "manifest_sha256": receipt.manifest_sha256,
            "ordered_file_sha256s": list(receipt.ordered_file_sha256s),
            "predicate": _predicate_document(receipt.predicate),
        },
        "capsule_id": capsule_id,
        "component_binding_payload": {
            "byte_count": len(component_binding_document_bytes),
            "payload_name": COMPONENT_BINDING_PAYLOAD_NAME,
            "raw_sha256": component_binding_document_sha256,
        },
        "effects": {
            "authority_created": False,
            "blocker_delta": 0,
            "data_accessed": False,
            "field_delta": 0,
            "formal_test_delta": 0,
            "network_used": False,
            "science_executed": False,
        },
        "files": [item.payload() for item in files],
        "schema_version": CAPSULE_SCHEMA,
        "scope": CAPSULE_SCOPE,
    }


def build_closed_world_capsule_plan(
    project_root: str,
    capsule_id: str,
    source_paths: object,
    component_bindings: object,
    authentication: ReceiptAuthentication,
) -> ClosedWorldCapsulePlan:
    root = _canonical_root(project_root)
    _exact_identifier(capsule_id, name="capsule_id")
    if type(source_paths) is not tuple or not 1 <= len(source_paths) <= MAX_CAPSULE_FILES:
        raise TypeError("source_paths must be a bounded nonempty exact tuple")
    if not all(type(value) is str for value in source_paths):
        raise TypeError("source path member must be exact text")
    if len(set(source_paths)) != len(source_paths):
        raise B12IntegrationError("source path roster contains duplicates")
    if type(component_bindings) is not tuple:
        raise TypeError("component_bindings must be an exact tuple")
    binding_document = component_binding_document_bytes(component_bindings)
    records = []
    for ordinal, source_path in enumerate(source_paths):
        relative = _safe_relative_path(source_path)
        raw = _stable_read_path(
            root,
            relative,
            expected_mode=0o644,
            maximum_bytes=MAX_CAPSULE_FILE_BYTES,
        )
        records.append(
            CapsuleFileRecord(
                ordinal=ordinal,
                source_path=source_path,
                payload_name="%03d.payload" % ordinal,
                byte_count=len(raw),
                raw_sha256=_sha256(raw),
                raw_bytes=raw,
            )
        )
    files = tuple(records)
    binding_sha256 = _sha256(binding_document)
    ordered_payload_sha256s = tuple(item.raw_sha256 for item in files) + (
        binding_sha256,
    )
    receipt_payload = {
        "capsule_id": capsule_id,
        "ordered_file_sha256s": list(ordered_payload_sha256s),
    }
    accepted_manifest_sha256 = _v2.sha(
        "heterodiff-b12-capsule-v1", receipt_payload
    )
    predicate = build_authenticated_predicate(
        "CAPSULE_RECEIPT", accepted_manifest_sha256, authentication
    )
    receipt = _v2.CapsuleReceipt(
        capsule_id=capsule_id,
        ordered_file_sha256s=ordered_payload_sha256s,
        manifest_sha256=accepted_manifest_sha256,
        predicate=predicate,
    )
    receipt.validate()
    manifest_document = _capsule_manifest_document(
        capsule_id, files, binding_document, binding_sha256, receipt
    )
    manifest_bytes = _canonical_bytes(manifest_document) + b"\n"
    plan = ClosedWorldCapsulePlan(
        capsule_id=capsule_id,
        files=files,
        component_binding_document_bytes=binding_document,
        component_binding_document_sha256=binding_sha256,
        receipt=receipt,
        manifest_bytes=manifest_bytes,
        manifest_raw_sha256=_sha256(manifest_bytes),
    )
    plan.validate()
    return plan


def _open_directory(path: Path) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return os.open(str(path), flags)


def _write_atomic_new(directory_fd: int, name: str, raw: bytes) -> None:
    if type(directory_fd) is not int:
        raise TypeError("directory_fd must be an exact integer")
    leaf = _safe_leaf_name(name)
    if type(raw) is not bytes:
        raise TypeError("atomic write payload must be exact bytes")
    pending = "." + leaf + ".pending"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(pending, flags, 0o600, dir_fd=directory_fd)
    try:
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            if written <= 0:
                raise OSError("atomic write made no progress")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.link(
        pending,
        leaf,
        src_dir_fd=directory_fd,
        dst_dir_fd=directory_fd,
        follow_symlinks=False,
    )
    os.unlink(pending, dir_fd=directory_fd)
    os.fsync(directory_fd)


def write_closed_world_capsule(
    plan: ClosedWorldCapsulePlan, parent_root: str, directory_name: str
) -> str:
    if type(plan) is not ClosedWorldCapsulePlan:
        raise TypeError("plan must have exact concrete type")
    plan.validate()
    parent = _canonical_root(parent_root)
    name = _safe_leaf_name(directory_name)
    parent_fd = _open_directory(parent)
    try:
        os.mkdir(name, 0o700, dir_fd=parent_fd)
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)
    destination = parent / name
    directory_fd = _open_directory(destination)
    try:
        for item in plan.files:
            _write_atomic_new(directory_fd, item.payload_name, item.raw_bytes)
        _write_atomic_new(
            directory_fd,
            COMPONENT_BINDING_PAYLOAD_NAME,
            plan.component_binding_document_bytes,
        )
        _write_atomic_new(directory_fd, "manifest.json", plan.manifest_bytes)
        finalized = {
            "capsule_id": plan.capsule_id,
            "manifest_raw_sha256": plan.manifest_raw_sha256,
            "schema_version": CAPSULE_FINALIZED_SCHEMA,
        }
        _write_atomic_new(
            directory_fd, "FINALIZED", _canonical_bytes(finalized) + b"\n"
        )
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    validate_closed_world_capsule(str(destination), expected_plan=plan)
    return str(destination)


def _parse_capsule_manifest(
    manifest_bytes: bytes,
    payloads: Mapping[str, bytes],
    component_binding_document_bytes: bytes,
) -> ClosedWorldCapsulePlan:
    document = _decode_canonical(
        manifest_bytes, maximum_bytes=MAX_CAPSULE_MANIFEST_BYTES
    )
    expected_top = (
        "accepted_capsule_receipt",
        "capsule_id",
        "component_binding_payload",
        "effects",
        "files",
        "schema_version",
        "scope",
    )
    if type(document) is not dict or tuple(sorted(document)) != expected_top:
        raise B12IntegrationError("capsule manifest top-level schema differs")
    if document["schema_version"] != CAPSULE_SCHEMA:
        raise B12IntegrationError("capsule manifest version differs")
    if document["scope"] != CAPSULE_SCOPE:
        raise B12IntegrationError("capsule scope differs")
    effects = document["effects"]
    if effects != {
        "authority_created": False,
        "blocker_delta": 0,
        "data_accessed": False,
        "field_delta": 0,
        "formal_test_delta": 0,
        "network_used": False,
        "science_executed": False,
    }:
        raise B12IntegrationError("capsule effects differ")
    binding_payload = document["component_binding_payload"]
    if (
        type(binding_payload) is not dict
        or tuple(binding_payload)
        != ("byte_count", "payload_name", "raw_sha256")
        or binding_payload["payload_name"] != COMPONENT_BINDING_PAYLOAD_NAME
        or type(binding_payload["byte_count"]) is not int
        or binding_payload["byte_count"] != len(component_binding_document_bytes)
        or binding_payload["raw_sha256"]
        != _sha256(component_binding_document_bytes)
    ):
        raise B12IntegrationError("component binding payload metadata differs")
    rows = document["files"]
    if type(rows) is not list or not 1 <= len(rows) <= MAX_CAPSULE_FILES:
        raise B12IntegrationError("capsule file roster length differs")
    records = []
    expected_row_keys = (
        "byte_count",
        "ordinal",
        "payload_name",
        "raw_sha256",
        "source_path",
    )
    for ordinal, row in enumerate(rows):
        if type(row) is not dict or tuple(sorted(row)) != expected_row_keys:
            raise B12IntegrationError("capsule file row schema differs")
        if row["ordinal"] != ordinal or type(row["ordinal"]) is not int:
            raise B12IntegrationError("capsule ordinal differs")
        payload_name = row["payload_name"]
        if type(payload_name) is not str or payload_name not in payloads:
            raise B12IntegrationError("capsule payload is absent")
        record = CapsuleFileRecord(
            ordinal=ordinal,
            source_path=row["source_path"],
            payload_name=payload_name,
            byte_count=row["byte_count"],
            raw_sha256=row["raw_sha256"],
            raw_bytes=payloads[payload_name],
        )
        record.payload()
        records.append(record)
    receipt_document = document["accepted_capsule_receipt"]
    expected_receipt_keys = (
        "capsule_id",
        "manifest_sha256",
        "ordered_file_sha256s",
        "predicate",
    )
    if (
        type(receipt_document) is not dict
        or tuple(sorted(receipt_document)) != expected_receipt_keys
        or type(receipt_document["ordered_file_sha256s"]) is not list
    ):
        raise B12IntegrationError("accepted capsule receipt document differs")
    receipt = _v2.CapsuleReceipt(
        capsule_id=receipt_document["capsule_id"],
        ordered_file_sha256s=tuple(receipt_document["ordered_file_sha256s"]),
        manifest_sha256=receipt_document["manifest_sha256"],
        predicate=_predicate_from_document(receipt_document["predicate"]),
    )
    plan = ClosedWorldCapsulePlan(
        capsule_id=document["capsule_id"],
        files=tuple(records),
        component_binding_document_bytes=component_binding_document_bytes,
        component_binding_document_sha256=binding_payload["raw_sha256"],
        receipt=receipt,
        manifest_bytes=manifest_bytes,
        manifest_raw_sha256=_sha256(manifest_bytes),
    )
    plan.validate()
    return plan


def validate_closed_world_capsule(
    capsule_root: str, expected_plan: Optional[ClosedWorldCapsulePlan] = None
) -> ClosedWorldCapsulePlan:
    root = _canonical_root(capsule_root, mode=0o700)
    directory_fd = _open_directory(root)
    try:
        names = os.listdir(directory_fd)
    finally:
        os.close(directory_fd)
    if type(names) is not list or not all(type(name) is str for name in names):
        raise B12IntegrationError("capsule directory listing differs")
    if "manifest.json" not in names or "FINALIZED" not in names:
        raise B12IntegrationError("capsule is partial or unfinalized")
    manifest = _stable_read_path(
        root,
        PurePosixPath("manifest.json"),
        expected_mode=0o600,
        maximum_bytes=MAX_CAPSULE_MANIFEST_BYTES,
    )
    manifest_document = _decode_canonical(
        manifest, maximum_bytes=MAX_CAPSULE_MANIFEST_BYTES
    )
    if type(manifest_document) is not dict or type(manifest_document.get("files")) is not list:
        raise B12IntegrationError("capsule manifest file roster differs")
    payload_names = tuple(
        row.get("payload_name") if type(row) is dict else None
        for row in manifest_document["files"]
    )
    if not all(type(name) is str for name in payload_names):
        raise B12IntegrationError("capsule manifest payload names differ")
    expected_names = set(payload_names) | {
        COMPONENT_BINDING_PAYLOAD_NAME,
        "manifest.json",
        "FINALIZED",
    }
    if set(names) != expected_names or len(names) != len(expected_names):
        raise B12IntegrationError("capsule closed-world directory roster differs")
    payloads = {}
    for name in payload_names:
        payloads[name] = _stable_read_path(
            root,
            PurePosixPath(name),
            expected_mode=0o600,
            maximum_bytes=MAX_CAPSULE_FILE_BYTES,
        )
    binding_document = _stable_read_path(
        root,
        PurePosixPath(COMPONENT_BINDING_PAYLOAD_NAME),
        expected_mode=0o600,
        maximum_bytes=MAX_CAPSULE_MANIFEST_BYTES,
    )
    plan = _parse_capsule_manifest(manifest, payloads, binding_document)
    finalized_bytes = _stable_read_path(
        root,
        PurePosixPath("FINALIZED"),
        expected_mode=0o600,
        maximum_bytes=4_096,
    )
    finalized = _decode_canonical(finalized_bytes, maximum_bytes=4_096)
    if finalized != {
        "capsule_id": plan.capsule_id,
        "manifest_raw_sha256": plan.manifest_raw_sha256,
        "schema_version": CAPSULE_FINALIZED_SCHEMA,
    }:
        raise B12IntegrationError("capsule finalization record differs")
    if expected_plan is not None:
        if type(expected_plan) is not ClosedWorldCapsulePlan:
            raise TypeError("expected_plan must have exact concrete type")
        expected_plan.validate()
        if plan != expected_plan:
            raise B12IntegrationError("capsule differs from expected plan")
    return plan


def _ledger_event_document(event: _v2.LedgerEvent) -> Mapping[str, object]:
    if type(event) is not _v2.LedgerEvent:
        raise TypeError("ledger event must have exact accepted type")
    payload = dict(event.payload())
    payload["event_sha256"] = event.event_sha256
    payload["schema_version"] = LEDGER_FILE_SCHEMA
    return payload


def _ledger_event_from_document(value: object) -> _v2.LedgerEvent:
    expected = (
        "event_kind",
        "event_sha256",
        "observation_sha256",
        "operation_id",
        "ordinal",
        "previous_event_sha256",
        "request_sha256",
        "schema_version",
    )
    if type(value) is not dict or tuple(sorted(value)) != expected:
        raise B12IntegrationError("ledger event file schema differs")
    if value["schema_version"] != LEDGER_FILE_SCHEMA:
        raise B12IntegrationError("ledger event file version differs")
    event = _v2.LedgerEvent(
        ordinal=value["ordinal"],
        event_kind=value["event_kind"],
        operation_id=value["operation_id"],
        request_sha256=value["request_sha256"],
        observation_sha256=value["observation_sha256"],
        previous_event_sha256=value["previous_event_sha256"],
        event_sha256=value["event_sha256"],
    )
    event.payload()
    return event


@dataclass(frozen=True)
class DurableLedgerReplay:
    events: Tuple[_v2.LedgerEvent, ...]
    complete_pairs: bool
    pair_count: int
    final_event_sha256: str

    def validate(self, *, allow_empty: bool = False) -> None:
        if type(self) is not DurableLedgerReplay:
            raise TypeError("ledger replay must have exact concrete type")
        if type(self.events) is not tuple or not all(
            type(event) is _v2.LedgerEvent for event in self.events
        ):
            raise TypeError("ledger replay events must have exact accepted types")
        if type(self.complete_pairs) is not bool or type(self.pair_count) is not int:
            raise TypeError("ledger replay summary types differ")
        if not self.events:
            if not allow_empty:
                raise B12IntegrationError("ledger replay is empty")
            if not self.complete_pairs or self.pair_count != 0 or self.final_event_sha256 != ZERO_SHA256:
                raise B12IntegrationError("empty ledger replay summary differs")
            return
        previous = ZERO_SHA256
        for ordinal, event in enumerate(self.events):
            event.payload()
            if event.ordinal != ordinal or event.previous_event_sha256 != previous:
                raise B12IntegrationError("ledger ordinal or previous-event chain differs")
            expected_kind = "INTENT" if ordinal % 2 == 0 else "OUTCOME"
            if event.event_kind != expected_kind:
                raise B12IntegrationError("ledger INTENT/OUTCOME order differs")
            if ordinal % 2:
                intent = self.events[ordinal - 1]
                if (
                    event.operation_id != intent.operation_id
                    or event.request_sha256 != intent.request_sha256
                ):
                    raise B12IntegrationError("ledger pair cross-binding differs")
            previous = event.event_sha256
        complete = len(self.events) % 2 == 0
        if self.complete_pairs is not complete or self.pair_count != len(self.events) // 2:
            raise B12IntegrationError("ledger replay completion summary differs")
        if self.final_event_sha256 != self.events[-1].event_sha256:
            raise B12IntegrationError("ledger replay final digest differs")
        if complete:
            _v2.validate_ledger(self.events)


def create_durable_ledger(parent_root: str, directory_name: str) -> str:
    parent = _canonical_root(parent_root)
    name = _safe_leaf_name(directory_name)
    parent_fd = _open_directory(parent)
    try:
        os.mkdir(name, 0o700, dir_fd=parent_fd)
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)
    ledger_path = parent / name
    _canonical_root(str(ledger_path), mode=0o700)
    return str(ledger_path)


def replay_durable_ledger(
    ledger_root: str,
    *,
    require_complete: bool = True,
    allow_empty: bool = False,
) -> DurableLedgerReplay:
    if type(require_complete) is not bool or type(allow_empty) is not bool:
        raise TypeError("ledger replay flags must be exact booleans")
    root = _canonical_root(ledger_root, mode=0o700)
    directory_fd = _open_directory(root)
    try:
        names = os.listdir(directory_fd)
    finally:
        os.close(directory_fd)
    if type(names) is not list or not all(type(name) is str for name in names):
        raise B12IntegrationError("ledger directory listing differs")
    expected_names = ["%020d.json" % ordinal for ordinal in range(len(names))]
    if sorted(names) != expected_names:
        raise B12IntegrationError("ledger is partial, noncontiguous, or contains extra files")
    events = []
    for ordinal, name in enumerate(expected_names):
        raw = _stable_read_path(
            root,
            PurePosixPath(name),
            expected_mode=0o600,
            maximum_bytes=MAX_LEDGER_EVENT_BYTES,
        )
        document = _decode_canonical(raw, maximum_bytes=MAX_LEDGER_EVENT_BYTES)
        event = _ledger_event_from_document(document)
        if event.ordinal != ordinal:
            raise B12IntegrationError("ledger filename/ordinal binding differs")
        events.append(event)
    event_tuple = tuple(events)
    replay = DurableLedgerReplay(
        events=event_tuple,
        complete_pairs=len(event_tuple) % 2 == 0,
        pair_count=len(event_tuple) // 2,
        final_event_sha256=(event_tuple[-1].event_sha256 if event_tuple else ZERO_SHA256),
    )
    replay.validate(allow_empty=allow_empty)
    if require_complete and not replay.complete_pairs:
        raise B12IntegrationError("ledger has a durable INTENT without OUTCOME")
    return replay


def _build_ledger_event(
    *,
    ordinal: int,
    event_kind: str,
    operation_id: str,
    request_sha256: str,
    observation_sha256: Optional[str],
    previous_event_sha256: str,
) -> _v2.LedgerEvent:
    payload = {
        "event_kind": event_kind,
        "observation_sha256": observation_sha256,
        "operation_id": operation_id,
        "ordinal": ordinal,
        "previous_event_sha256": previous_event_sha256,
        "request_sha256": request_sha256,
    }
    event = _v2.LedgerEvent(
        ordinal=ordinal,
        event_kind=event_kind,
        operation_id=operation_id,
        request_sha256=request_sha256,
        observation_sha256=observation_sha256,
        previous_event_sha256=previous_event_sha256,
        event_sha256=_v2.sha("heterodiff-b12-ledger-event-v1", payload),
    )
    event.payload()
    return event


def _persist_ledger_event(ledger_root: str, event: _v2.LedgerEvent) -> None:
    if type(event) is not _v2.LedgerEvent:
        raise TypeError("ledger event must have exact accepted type")
    root = _canonical_root(ledger_root, mode=0o700)
    raw = _canonical_bytes(_ledger_event_document(event)) + b"\n"
    directory_fd = _open_directory(root)
    try:
        _write_atomic_new(directory_fd, "%020d.json" % event.ordinal, raw)
    finally:
        os.close(directory_fd)


def append_ledger_intent(
    ledger_root: str, operation_id: str, request_bytes: bytes
) -> _v2.LedgerEvent:
    _exact_identifier(operation_id, name="operation_id")
    if type(request_bytes) is not bytes or not request_bytes:
        raise TypeError("request_bytes must be nonempty exact bytes")
    replay = replay_durable_ledger(
        ledger_root, require_complete=True, allow_empty=True
    )
    ordinal = len(replay.events)
    request_sha256 = _raw_domain_sha256(
        "heterodiff-b12-operation-request-v1", request_bytes
    )
    event = _build_ledger_event(
        ordinal=ordinal,
        event_kind="INTENT",
        operation_id=operation_id,
        request_sha256=request_sha256,
        observation_sha256=None,
        previous_event_sha256=replay.final_event_sha256,
    )
    _persist_ledger_event(ledger_root, event)
    after = replay_durable_ledger(
        ledger_root, require_complete=False, allow_empty=False
    )
    if after.events[-1] != event or after.complete_pairs:
        raise B12IntegrationError("durable INTENT replay differs")
    return event


def append_ledger_outcome(
    ledger_root: str,
    operation_id: str,
    request_bytes: bytes,
    outcome_bytes: bytes,
) -> _v2.LedgerEvent:
    _exact_identifier(operation_id, name="operation_id")
    if type(request_bytes) is not bytes or not request_bytes:
        raise TypeError("request_bytes must be nonempty exact bytes")
    if type(outcome_bytes) is not bytes or not outcome_bytes:
        raise TypeError("outcome_bytes must be nonempty exact bytes")
    replay = replay_durable_ledger(
        ledger_root, require_complete=False, allow_empty=False
    )
    if replay.complete_pairs:
        raise B12IntegrationError("ledger has no unmatched durable INTENT")
    intent = replay.events[-1]
    request_sha256 = _raw_domain_sha256(
        "heterodiff-b12-operation-request-v1", request_bytes
    )
    if (
        intent.event_kind != "INTENT"
        or intent.operation_id != operation_id
        or intent.request_sha256 != request_sha256
    ):
        raise B12IntegrationError("OUTCOME does not match the durable INTENT")
    event = _build_ledger_event(
        ordinal=len(replay.events),
        event_kind="OUTCOME",
        operation_id=operation_id,
        request_sha256=request_sha256,
        observation_sha256=_raw_domain_sha256(
            "heterodiff-b12-operation-outcome-v1", outcome_bytes
        ),
        previous_event_sha256=intent.event_sha256,
    )
    _persist_ledger_event(ledger_root, event)
    after = replay_durable_ledger(
        ledger_root, require_complete=True, allow_empty=False
    )
    if after.events[-1] != event:
        raise B12IntegrationError("durable OUTCOME replay differs")
    return event


def append_ledger_pair(
    ledger_root: str,
    operation_id: str,
    request_bytes: bytes,
    outcome_bytes: bytes,
) -> Tuple[_v2.LedgerEvent, _v2.LedgerEvent]:
    intent = append_ledger_intent(ledger_root, operation_id, request_bytes)
    outcome = append_ledger_outcome(
        ledger_root, operation_id, request_bytes, outcome_bytes
    )
    return intent, outcome


@dataclass(frozen=True)
class AdapterManifestBinding:
    receipts: Tuple[_v2.AdapterReceipt, ...]
    adapter_subject_sha256s: Tuple[str, ...]
    manifest_sha256: str
    synthetic_interface_only: bool

    def validate(self) -> None:
        if type(self) is not AdapterManifestBinding:
            raise TypeError("adapter manifest binding must have exact concrete type")
        adapter_api = importlib.import_module(
            "heterodiff.evaluation.b12_two_domain_adapter_stack"
        )
        corrected = getattr(adapter_api, "ADAPTER_ROSTER_SNAPSHOT", None)
        legacy = getattr(adapter_api, "LEGACY_PARTIAL_ROSTER_SNAPSHOT", None)
        mismatches = getattr(
            adapter_api, "LEGACY_PARTIAL_ROSTER_MISMATCH_ORDINALS", None
        )
        if (
            type(corrected) is not tuple
            or len(corrected) != 22
            or not all(type(row) is tuple and len(row) == 3 for row in corrected)
        ):
            raise B12IntegrationError("corrected adapter roster surface differs")
        if type(self.receipts) is not tuple or len(self.receipts) != 22:
            raise TypeError("adapter receipt manifest must be an exact 22-row tuple")
        if not all(type(receipt) is _v2.AdapterReceipt for receipt in self.receipts):
            raise TypeError("adapter receipt member has wrong concrete type")
        triples = tuple(
            (receipt.adapter_id, receipt.domain_id, receipt.config_sha256)
            for receipt in self.receipts
        )
        if legacy is not None and triples == legacy and legacy != corrected:
            raise B12IntegrationError(
                "legacy B12 v2 eight-row literature-family hash mismatch is rejected"
            )
        if triples != corrected:
            raise B12IntegrationError("adapter receipt roster differs from corrected B06")
        if mismatches != tuple(range(12, 20)):
            raise B12IntegrationError("legacy/corrected mismatch boundary differs")
        subjects = []
        for receipt in self.receipts:
            receipt.validate()
            subjects.append(receipt.subject_sha256())
        subject_tuple = tuple(subjects)
        if len(set(subject_tuple)) != 22:
            raise B12IntegrationError("adapter subjects are not exact 22-row unique")
        if self.adapter_subject_sha256s != subject_tuple:
            raise B12IntegrationError("adapter subject roster differs")
        if type(self.synthetic_interface_only) is not bool or not self.synthetic_interface_only:
            raise B12IntegrationError("adapter nonclaim was widened")
        payload = {
            "adapter_subject_sha256s": list(subject_tuple),
            "corrected_roster": [list(row) for row in corrected],
            "legacy_mismatch_ordinals": list(mismatches),
            "synthetic_interface_only": True,
        }
        if self.manifest_sha256 != _domain_sha256(
            "heterodiff-b12-corrected-adapter-manifest-v1", payload
        ):
            raise B12IntegrationError("adapter manifest digest differs")


def validate_adapter_receipt_manifest(receipts: object) -> AdapterManifestBinding:
    if type(receipts) is not tuple or not all(
        type(receipt) is _v2.AdapterReceipt for receipt in receipts
    ):
        raise TypeError("receipts must contain exact accepted AdapterReceipt values")
    adapter_api = importlib.import_module(
        "heterodiff.evaluation.b12_two_domain_adapter_stack"
    )
    corrected = adapter_api.ADAPTER_ROSTER_SNAPSHOT
    mismatches = adapter_api.LEGACY_PARTIAL_ROSTER_MISMATCH_ORDINALS
    subjects = tuple(receipt.subject_sha256() for receipt in receipts)
    payload = {
        "adapter_subject_sha256s": list(subjects),
        "corrected_roster": [list(row) for row in corrected],
        "legacy_mismatch_ordinals": list(mismatches),
        "synthetic_interface_only": True,
    }
    result = AdapterManifestBinding(
        receipts=receipts,
        adapter_subject_sha256s=subjects,
        manifest_sha256=_domain_sha256(
            "heterodiff-b12-corrected-adapter-manifest-v1", payload
        ),
        synthetic_interface_only=True,
    )
    result.validate()
    return result


def build_synthetic_adapter_manifest_binding(
    project_root: str,
) -> AdapterManifestBinding:
    """Consume the adapter agent's deterministic builder without widening it."""

    root = _canonical_root(project_root)
    source_path = _safe_relative_path(
        "src/heterodiff/evaluation/b12_two_domain_adapter_stack.py"
    )
    raw = _stable_read_path(
        root,
        source_path,
        expected_mode=0o644,
        maximum_bytes=MAX_CAPSULE_FILE_BYTES,
    )
    adapter_api = importlib.import_module(
        "heterodiff.evaluation.b12_two_domain_adapter_stack"
    )
    if type(adapter_api) is not ModuleType:
        raise B12IntegrationError("adapter stack import differs")
    retail, physionet = adapter_api.qualification_fixture_configurations()
    receipts = adapter_api.build_synthetic_adapter_receipts(
        retail_configuration=retail,
        physionet_configuration=physionet,
        module_source_sha256=_sha256(raw),
    )
    return validate_adapter_receipt_manifest(receipts)


def compute_execution_subject_v3(
    capsule: _v2.CapsuleReceipt,
    adapters: AdapterManifestBinding,
    ledger: Tuple[_v2.LedgerEvent, ...],
    runtime_identity: Optional[RuntimeIdentityBinding],
) -> str:
    if type(capsule) is not _v2.CapsuleReceipt:
        raise TypeError("capsule must have exact accepted type")
    capsule.validate()
    if type(adapters) is not AdapterManifestBinding:
        raise TypeError("adapters must have exact corrected manifest type")
    adapters.validate()
    if type(ledger) is not tuple or not ledger or not all(
        type(event) is _v2.LedgerEvent for event in ledger
    ):
        raise TypeError("ledger must be a nonempty exact event tuple")
    _v2.validate_ledger(ledger)
    if runtime_identity is not None:
        if type(runtime_identity) is not RuntimeIdentityBinding:
            raise TypeError("runtime identity has wrong concrete type")
        runtime_identity.payload()
    return _domain_sha256(
        "heterodiff-b12-execution-subject-v3-corrected-roster",
        {
            "adapter_manifest_sha256": adapters.manifest_sha256,
            "adapter_subject_sha256s": list(adapters.adapter_subject_sha256s),
            "capsule_manifest_sha256": capsule.manifest_sha256,
            "ledger_event_sha256s": [event.event_sha256 for event in ledger],
            "runtime_identity_binding_sha256": (
                None if runtime_identity is None else runtime_identity.binding_sha256
            ),
        },
    )


def build_recomputation_receipt(
    execution_subject_sha256: str,
    outputs: BoundOutputPair,
    authentication: ReceiptAuthentication,
) -> _v2.RecomputationReceipt:
    execution_subject = _exact_sha256(
        execution_subject_sha256, name="execution_subject_sha256", nonzero=True
    )
    if type(outputs) is not BoundOutputPair:
        raise TypeError("outputs must have exact BoundOutputPair type")
    outputs.validate()
    receipt_subject = _v2.sha(
        "heterodiff-b12-recomputation-subject-v1",
        {
            "candidate_output_sha256": outputs.candidate_output_sha256,
            "independent_implementation_sha256": (
                outputs.independent_implementation_sha256
            ),
            "independent_output_sha256": outputs.independent_output_sha256,
            "subject_sha256": execution_subject,
        },
    )
    predicate = build_authenticated_predicate(
        "RECOMPUTATION_RECEIPT", receipt_subject, authentication
    )
    receipt = _v2.RecomputationReceipt(
        subject_sha256=execution_subject,
        independent_implementation_sha256=(
            outputs.independent_implementation_sha256
        ),
        candidate_output_sha256=outputs.candidate_output_sha256,
        independent_output_sha256=outputs.independent_output_sha256,
        predicate=predicate,
    )
    receipt.validate(execution_subject)
    return receipt


def compute_runner_subject_v3(
    capsule: _v2.CapsuleReceipt,
    adapters: AdapterManifestBinding,
    ledger: Tuple[_v2.LedgerEvent, ...],
    recomputation: _v2.RecomputationReceipt,
    runtime_identity: Optional[RuntimeIdentityBinding],
) -> str:
    execution_subject = compute_execution_subject_v3(
        capsule, adapters, ledger, runtime_identity
    )
    if type(recomputation) is not _v2.RecomputationReceipt:
        raise TypeError("recomputation must have exact accepted type")
    recomputation.validate(execution_subject)
    return _domain_sha256(
        "heterodiff-b12-runner-subject-v3-corrected-roster",
        {
            "adapter_manifest_sha256": adapters.manifest_sha256,
            "adapter_subject_sha256s": list(adapters.adapter_subject_sha256s),
            "capsule_manifest_sha256": capsule.manifest_sha256,
            "ledger_final_event_sha256": ledger[-1].event_sha256,
            "recomputation_subject_sha256": (
                recomputation.receipt_subject_sha256()
            ),
            "runtime_identity_binding_sha256": (
                None if runtime_identity is None else runtime_identity.binding_sha256
            ),
        },
    )


@dataclass(frozen=True)
class ResidualPredicateSlot:
    """Exact subject-bound slot for one real B12 residual predicate.

    An absent receipt is an explicit OPEN state.  A present receipt must be a
    caller-supplied accepted-contract receipt whose subject matches the whole
    runner and whose authentication identifiers contain no local/synthetic
    qualification markers.
    """

    predicate_id: str
    expected_subject_sha256: str
    receipt: Optional[_v2.AuthenticatedPredicateReceipt]

    def validate(
        self, expected_predicate_id: str, expected_subject_sha256: str
    ) -> None:
        if type(self) is not ResidualPredicateSlot:
            raise TypeError("residual predicate slot must have exact concrete type")
        predicate_id = _exact_identifier(
            self.predicate_id, name="residual predicate_id"
        )
        expected_id = _exact_identifier(
            expected_predicate_id, name="expected residual predicate_id"
        )
        subject = _exact_sha256(
            self.expected_subject_sha256,
            name="residual expected_subject_sha256",
            nonzero=True,
        )
        expected_subject = _exact_sha256(
            expected_subject_sha256,
            name="expected runner subject_sha256",
            nonzero=True,
        )
        if predicate_id != expected_id:
            raise B12IntegrationError("runner residual predicate roster differs")
        if subject != expected_subject:
            raise B12IntegrationError(
                "runner predicate slot subject cross-binding differs"
            )
        if self.receipt is None:
            return
        if type(self.receipt) is not _v2.AuthenticatedPredicateReceipt:
            raise TypeError("runner predicate receipt has wrong concrete type")
        payload = self.receipt.payload()
        if (
            payload["predicate_id"] != predicate_id
            or payload["subject_sha256"] != subject
        ):
            raise B12IntegrationError(
                "runner predicate receipt subject cross-binding differs"
            )
        _require_production_authentication(self.receipt)

    def state(self) -> str:
        if type(self) is not ResidualPredicateSlot:
            raise TypeError("residual predicate slot must have exact concrete type")
        return (
            "OPEN_RECEIPT_ABSENT"
            if self.receipt is None
            else "CALLER_SUPPLIED_RECEIPT_PRESENT_PENDING_REVIEW"
        )


@dataclass(frozen=True)
class IntegratedRunnerReceiptV3:
    state: str
    capsule: _v2.CapsuleReceipt
    adapters: AdapterManifestBinding
    ledger: Tuple[_v2.LedgerEvent, ...]
    recomputation: _v2.RecomputationReceipt
    predicate_slots: Tuple[ResidualPredicateSlot, ...]
    runtime_identity: Optional[RuntimeIdentityBinding]

    def validate(self) -> None:
        if type(self) is not IntegratedRunnerReceiptV3:
            raise TypeError("runner receipt must have exact concrete type")
        if self.state not in (RUNNER_STATE, PRODUCTION_RUNNER_STATE):
            raise B12IntegrationError("runner nonclaim state differs")
        if type(self.capsule) is not _v2.CapsuleReceipt:
            raise TypeError("runner capsule has wrong concrete type")
        self.capsule.validate()
        if type(self.adapters) is not AdapterManifestBinding:
            raise TypeError("runner adapter manifest has wrong concrete type")
        self.adapters.validate()
        if type(self.ledger) is not tuple or not self.ledger or not all(
            type(event) is _v2.LedgerEvent for event in self.ledger
        ):
            raise TypeError("runner ledger member has wrong concrete type")
        _v2.validate_ledger(self.ledger)
        if self.runtime_identity is not None:
            if type(self.runtime_identity) is not RuntimeIdentityBinding:
                raise TypeError("runner runtime identity has wrong concrete type")
            self.runtime_identity.payload()
        if type(self.recomputation) is not _v2.RecomputationReceipt:
            raise TypeError("runner recomputation has wrong concrete type")
        runner_subject = compute_runner_subject_v3(
            self.capsule,
            self.adapters,
            self.ledger,
            self.recomputation,
            self.runtime_identity,
        )
        if type(self.predicate_slots) is not tuple or not all(
            type(slot) is ResidualPredicateSlot for slot in self.predicate_slots
        ):
            raise TypeError("runner predicate slot has wrong concrete type")
        if tuple(slot.predicate_id for slot in self.predicate_slots) != _RESIDUAL_IDS:
            raise B12IntegrationError("runner residual predicate roster differs")
        for predicate_id, slot in zip(_RESIDUAL_IDS, self.predicate_slots):
            slot.validate(predicate_id, runner_subject)
        present_count = sum(
            slot.receipt is not None for slot in self.predicate_slots
        )
        if present_count not in (0, len(_RESIDUAL_IDS)):
            raise B12IntegrationError(
                "runner residual receipt roster is partial"
            )
        if present_count == 0:
            if self.state != RUNNER_STATE or self.runtime_identity is not None:
                raise B12IntegrationError(
                    "open structural runner state or runtime identity differs"
                )
        elif self.state != PRODUCTION_RUNNER_STATE or self.runtime_identity is None:
            raise B12IntegrationError(
                "production-bound runner state or runtime identity differs"
            )

    def status(self) -> Mapping[str, object]:
        self.validate()
        present = sum(slot.receipt is not None for slot in self.predicate_slots)
        return {
            "b12_closed": False,
            "blocker_delta": 0,
            "field_delta": 0,
            "formal_test_states": {"28": "OPEN", "29": "OPEN", "30": "PENDING"},
            "residual_receipts_missing": len(_RESIDUAL_IDS) - present,
            "residual_receipts_present": present,
            "result_delta": 0,
            "runtime_identity_present": self.runtime_identity is not None,
            "science_executed": False,
            "state": self.state,
        }


def build_open_residual_slots(
    runner_subject_sha256: str,
) -> Tuple[ResidualPredicateSlot, ...]:
    """Build the exact 50-row OPEN subject roster without minting evidence."""

    subject = _exact_sha256(
        runner_subject_sha256,
        name="runner_subject_sha256",
        nonzero=True,
    )
    return tuple(
        ResidualPredicateSlot(
            predicate_id=predicate_id,
            expected_subject_sha256=subject,
            receipt=None,
        )
        for predicate_id in _RESIDUAL_IDS
    )


def build_open_integrated_runner_exercise(
    capsule: _v2.CapsuleReceipt,
    adapters: AdapterManifestBinding,
    ledger: object,
    recomputation: _v2.RecomputationReceipt,
) -> IntegratedRunnerReceiptV3:
    """Exercise all runner bindings while leaving all real predicates OPEN."""

    if type(ledger) is not tuple:
        raise TypeError("runner ledger must be an exact tuple")
    subject = compute_runner_subject_v3(
        capsule, adapters, ledger, recomputation, None
    )
    result = IntegratedRunnerReceiptV3(
        state=RUNNER_STATE,
        capsule=capsule,
        adapters=adapters,
        ledger=ledger,
        recomputation=recomputation,
        predicate_slots=build_open_residual_slots(subject),
        runtime_identity=None,
    )
    result.validate()
    return result


def build_integrated_runner_receipt(
    capsule: _v2.CapsuleReceipt,
    adapters: AdapterManifestBinding,
    ledger: object,
    recomputation: _v2.RecomputationReceipt,
    predicate_receipts: object,
    runtime_identity: Optional[RuntimeIdentityBinding] = None,
) -> IntegratedRunnerReceiptV3:
    """Bind a future caller-supplied production receipt set without closing B12."""

    if type(ledger) is not tuple or type(predicate_receipts) is not tuple:
        raise TypeError("runner ledger and predicate roster must be exact tuples")
    if runtime_identity is None:
        raise B12IntegrationError(
            "production runner requires a caller-supplied runtime identity"
        )
    if type(runtime_identity) is not RuntimeIdentityBinding:
        raise TypeError("runtime identity has wrong concrete type")
    if not all(
        type(receipt) is _v2.AuthenticatedPredicateReceipt
        for receipt in predicate_receipts
    ):
        raise TypeError("runner predicate receipt has wrong concrete type")
    for receipt in predicate_receipts:
        _require_production_authentication(receipt)
    if tuple(receipt.predicate_id for receipt in predicate_receipts) != _RESIDUAL_IDS:
        raise B12IntegrationError("runner residual predicate roster differs")
    subject = compute_runner_subject_v3(
        capsule, adapters, ledger, recomputation, runtime_identity
    )
    slots = []
    for predicate_id, receipt in zip(_RESIDUAL_IDS, predicate_receipts):
        slot = ResidualPredicateSlot(predicate_id, subject, receipt)
        slot.validate(predicate_id, subject)
        slots.append(slot)
    result = IntegratedRunnerReceiptV3(
        state=PRODUCTION_RUNNER_STATE,
        capsule=capsule,
        adapters=adapters,
        ledger=ledger,
        recomputation=recomputation,
        predicate_slots=tuple(slots),
        runtime_identity=runtime_identity,
    )
    result.validate()
    return result


def residual_predicate_ids() -> Tuple[str, ...]:
    return tuple(_RESIDUAL_IDS)


__all__ = [
    "AdapterManifestBinding",
    "B12IntegrationError",
    "BOUND_OUTPUT_SCHEMA",
    "BOUND_OUTPUT_STATE",
    "BoundOutputPair",
    "CAPSULE_SCOPE",
    "CAPSULE_SCHEMA",
    "COMPONENT_BINDING_PAYLOAD_NAME",
    "ClosedWorldCapsulePlan",
    "ComponentBinding",
    "DEFAULT_CAPSULE_SOURCE_PATHS",
    "DurableLedgerReplay",
    "IntegratedRunnerReceiptV3",
    "LEDGER_FILE_SCHEMA",
    "PRODUCTION_RUNNER_STATE",
    "ResidualPredicateSlot",
    "RUNNER_STATE",
    "ReceiptAuthentication",
    "RuntimeIdentityBinding",
    "append_ledger_intent",
    "append_ledger_outcome",
    "append_ledger_pair",
    "build_authenticated_predicate",
    "build_closed_world_capsule_plan",
    "build_component_bindings",
    "build_integrated_runner_receipt",
    "build_open_integrated_runner_exercise",
    "build_open_residual_slots",
    "build_recomputation_receipt",
    "build_synthetic_adapter_manifest_binding",
    "component_binding_document_bytes",
    "compute_execution_subject_v3",
    "compute_runner_subject_v3",
    "create_durable_ledger",
    "replay_durable_ledger",
    "residual_predicate_ids",
    "run_and_independently_recompute",
    "run_bound_component_output",
    "validate_adapter_receipt_manifest",
    "validate_closed_world_capsule",
    "write_closed_world_capsule",
]
