"""Exact source-closure binding for a development adapter child.

This module gives the declarative
``archive-selected-exact-module-closure-v1`` policy a bounded byte format.  It
maps one adapter identity and two fixed entry points to exact module sources in
one path-free source archive.  Validation reparses every selected source,
closes protected-namespace imports, admits only declared external import
roots, and requires the archive to contain exactly the declared logical and
physical source members.

The artifact is source preparation, not a loader or an execution receipt.
Validation does not import or execute a module, construct or invoke an
adapter, install an import hook, deny host fallback at runtime, enforce
containment, establish expected-material nonexposure, or make a decision.
Those nonclaims are fixed in the validation receipt.

The module is intentionally not re-exported from :mod:`heterodiff.data`.
"""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import keyword
import re
from types import MappingProxyType
from typing import Dict, NamedTuple, Optional, Tuple

from . import adapter_source_archive as _archive


IMPLEMENTATION_CLOSURE_ARTIFACT_TYPE = (
    "heterodiff.adapter.implementation-closure.v1"
)
IMPLEMENTATION_CLOSURE_DIGEST_DOMAIN = IMPLEMENTATION_CLOSURE_ARTIFACT_TYPE
IMPLEMENTATION_CLOSURE_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.implementation-closure-validation-receipt.v1"
)
IMPLEMENTATION_CLOSURE_RECEIPT_DIGEST_DOMAIN = (
    IMPLEMENTATION_CLOSURE_RECEIPT_ARTIFACT_TYPE
)
IMPLEMENTATION_IMPORT_GRAPH_DIGEST_DOMAIN = (
    "heterodiff.adapter.implementation-closure-import-graph.v1"
)
IMPLEMENTATION_CLOSURE_CONSTRUCTION_MODE_ID = (
    "zero-argument-factory-v1"
)
IMPLEMENTATION_CLOSURE_VALIDATION_STATUS_ID = (
    "IMPLEMENTATION_CLOSURE_ARCHIVE_AND_IMPORT_GRAPH_MATCHED_"
    "UNEXECUTED_DEVELOPMENT_SOURCE"
)
IMPLEMENTATION_CLOSURE_DECISION_STATUS_ID = (
    "NOT_MADE_BY_IMPLEMENTATION_CLOSURE_VALIDATOR"
)

IMPLEMENTATION_CLOSURE_ALLOWED_ROLE_IDS = (
    "adapter-source",
    "contract-source",
    "support-source",
)
IMPLEMENTATION_CLOSURE_BANNED_NAME_TOKENS = (
    "authority",
    "comparator",
    "expected",
    "guard",
    "oracle",
    "publisher",
    "test",
    "verifier",
)

MAXIMUM_IMPLEMENTATION_CLOSURE_BYTES = 4 * 1024 * 1024
MAXIMUM_IMPLEMENTATION_CLOSURE_RECEIPT_BYTES = 64 * 1024
MAXIMUM_IMPLEMENTATION_DEPENDENCY_LOCK_BYTES = 4 * 1024 * 1024
MAXIMUM_IMPLEMENTATION_MODULES = _archive.MAXIMUM_SOURCE_ARCHIVE_ENTRIES
MAXIMUM_IMPLEMENTATION_MODULE_NAME_BYTES = 512
MAXIMUM_IMPLEMENTATION_CALLABLE_NAME_BYTES = 128
MAXIMUM_IMPLEMENTATION_IMPORT_ROOTS = 1024
MAXIMUM_IMPLEMENTATION_JSON_DEPTH = 32
MAXIMUM_IMPLEMENTATION_JSON_TOKENS = 200_000
MAXIMUM_IMPLEMENTATION_JSON_STRING_BYTES = 512 * 1024
MAXIMUM_IMPLEMENTATION_SOURCE_AST_NODES = 200_000
MAXIMUM_IMPLEMENTATION_SOURCE_AST_DEPTH = 128
MAXIMUM_IMPLEMENTATION_SOURCE_LINES = 100_000
MAXIMUM_IMPLEMENTATION_SOURCE_LINE_BYTES = 64 * 1024

_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ADAPTER_ID_RE = re.compile(
    r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$"
)
_VERSION_RE = re.compile(r"^[1-9][0-9]{0,9}$")
_MODULE_COMPONENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SOURCE_OBJECT_ID_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"
)
_FORBIDDEN_DYNAMIC_IMPORT_ROOTS = frozenset(
    ("builtins", "pkgutil", "runpy")
)
_FORBIDDEN_DYNAMIC_CALL_ROOTS = _FORBIDDEN_DYNAMIC_IMPORT_ROOTS.union(
    ("importlib",)
)
_FORBIDDEN_DYNAMIC_CALL_NAMES = frozenset(
    ("__import__", "compile", "eval", "exec")
)
_BANNED_IMPORT_ROOTS = frozenset(
    IMPLEMENTATION_CLOSURE_BANNED_NAME_TOKENS
    + ("pytest", "unittest")
)


class ImplementationClosureCode(str, Enum):
    """Closed failures without interpolation of untrusted source text."""

    INPUT_TYPE = "IMPLEMENTATION_CLOSURE_INPUT_TYPE"
    RESOURCE = "IMPLEMENTATION_CLOSURE_RESOURCE"
    JSON = "IMPLEMENTATION_CLOSURE_JSON"
    NONCANONICAL = "IMPLEMENTATION_CLOSURE_NONCANONICAL"
    SCHEMA = "IMPLEMENTATION_CLOSURE_SCHEMA"
    NAME_POLICY = "IMPLEMENTATION_CLOSURE_NAME_POLICY"
    PACKAGE_CLOSURE = "IMPLEMENTATION_CLOSURE_PACKAGE_CLOSURE"
    ENTRY_POINT = "IMPLEMENTATION_CLOSURE_ENTRY_POINT"
    IMPORT_POLICY = "IMPLEMENTATION_CLOSURE_IMPORT_POLICY"
    ARCHIVE = "IMPLEMENTATION_CLOSURE_ARCHIVE"
    ARCHIVE_MEMBERSHIP = "IMPLEMENTATION_CLOSURE_ARCHIVE_MEMBERSHIP"
    DEPENDENCY_LOCK = "IMPLEMENTATION_CLOSURE_DEPENDENCY_LOCK"
    RECEIPT = "IMPLEMENTATION_CLOSURE_RECEIPT"
    INTERNAL = "IMPLEMENTATION_CLOSURE_INTERNAL"


_ERROR_MESSAGES = MappingProxyType(
    {
        ImplementationClosureCode.INPUT_TYPE: (
            "implementation closure input has an invalid exact type"
        ),
        ImplementationClosureCode.RESOURCE: (
            "implementation closure exceeds a fixed resource ceiling"
        ),
        ImplementationClosureCode.JSON: (
            "implementation closure is not strict canonical-profile JSON"
        ),
        ImplementationClosureCode.NONCANONICAL: (
            "implementation closure JSON is not canonical"
        ),
        ImplementationClosureCode.SCHEMA: (
            "implementation closure has an invalid closed schema"
        ),
        ImplementationClosureCode.NAME_POLICY: (
            "implementation closure violates the fixed source-name policy"
        ),
        ImplementationClosureCode.PACKAGE_CLOSURE: (
            "implementation closure does not close all package parents"
        ),
        ImplementationClosureCode.ENTRY_POINT: (
            "implementation closure entry point is not exact"
        ),
        ImplementationClosureCode.IMPORT_POLICY: (
            "implementation closure source imports are not closed"
        ),
        ImplementationClosureCode.ARCHIVE: (
            "implementation closure source archive is invalid"
        ),
        ImplementationClosureCode.ARCHIVE_MEMBERSHIP: (
            "implementation closure does not exactly match its source archive"
        ),
        ImplementationClosureCode.DEPENDENCY_LOCK: (
            "implementation closure dependency lock does not match"
        ),
        ImplementationClosureCode.RECEIPT: (
            "implementation closure validation receipt is invalid"
        ),
        ImplementationClosureCode.INTERNAL: (
            "implementation closure validation failed internally"
        ),
    }
)


class ImplementationClosureError(ValueError):
    """One fixed coded implementation-closure failure."""

    def __init__(self, code: ImplementationClosureCode) -> None:
        if type(code) is not ImplementationClosureCode:
            raise TypeError("implementation closure code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: ImplementationClosureCode) -> None:
    raise ImplementationClosureError(code) from None


class _NamePolicyViolation(ValueError):
    """Internal marker for one fixed public name-policy failure."""


class _PackageClosureViolation(ValueError):
    """Internal marker for one fixed public package-closure failure."""


class _EntryPointViolation(ValueError):
    """Internal marker for one fixed public entry-point failure."""


def _sha256_text(value: object, *, name: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(name + " must be a lowercase SHA-256")
    return value


def _ascii_text(
    value: object,
    *,
    name: str,
    maximum: int,
    allow_empty: bool = False,
) -> str:
    if type(value) is not str:
        raise TypeError(name + " must be exact text")
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        raise ValueError(name + " must contain only ASCII") from None
    if (
        (not encoded and not allow_empty)
        or len(encoded) > maximum
        or b"\x00" in encoded
    ):
        raise ValueError(name + " is outside its fixed text bound")
    return value


def _adapter_id(value: object) -> str:
    result = _ascii_text(
        value,
        name="adapter_id",
        maximum=128,
    )
    if _ADAPTER_ID_RE.fullmatch(result) is None:
        raise ValueError("adapter_id is not canonical")
    _require_name_policy(result)
    return result


def _adapter_version(value: object) -> str:
    result = _ascii_text(
        value,
        name="adapter_version",
        maximum=10,
    )
    if _VERSION_RE.fullmatch(result) is None:
        raise ValueError("adapter_version is not canonical")
    return result


def _module_name(value: object, *, name: str) -> str:
    result = _ascii_text(
        value,
        name=name,
        maximum=MAXIMUM_IMPLEMENTATION_MODULE_NAME_BYTES,
    )
    components = result.split(".")
    if (
        not components
        or any(
            _MODULE_COMPONENT_RE.fullmatch(component) is None
            or keyword.iskeyword(component)
            for component in components
        )
    ):
        raise ValueError(name + " is not a canonical module name")
    _require_name_policy(result)
    return result


def _callable_name(value: object, *, name: str) -> str:
    result = _ascii_text(
        value,
        name=name,
        maximum=MAXIMUM_IMPLEMENTATION_CALLABLE_NAME_BYTES,
    )
    if (
        not result.isidentifier()
        or keyword.iskeyword(result)
        or (result.startswith("__") and result.endswith("__"))
    ):
        raise ValueError(name + " is not a canonical callable name")
    _require_name_policy(result)
    return result


def _source_object_id(value: object) -> str:
    result = _ascii_text(
        value,
        name="source_object_id",
        maximum=_archive.MAXIMUM_SOURCE_OBJECT_ID_BYTES,
    )
    if _SOURCE_OBJECT_ID_RE.fullmatch(result) is None:
        raise ValueError("source_object_id is not canonical")
    _require_name_policy(result)
    return result


def _name_tokens(value: str) -> Tuple[str, ...]:
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    return tuple(
        item.lower()
        for item in re.split(r"[^A-Za-z0-9]+", separated)
        if item
    )


def _require_name_policy(value: str) -> None:
    tokens = _name_tokens(value)
    if any(
        token in IMPLEMENTATION_CLOSURE_BANNED_NAME_TOKENS
        for token in tokens
    ):
        raise _NamePolicyViolation(
            "implementation source name contains a banned token"
        )


def _root_tuple(
    value: object,
    *,
    protected: bool,
) -> Tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError("import roots must be an exact tuple")
    if len(value) > MAXIMUM_IMPLEMENTATION_IMPORT_ROOTS:
        raise ValueError("too many implementation import roots")
    if protected and not value:
        raise ValueError("protected namespace roots must be nonempty")
    result = tuple(
        _module_name(item, name="protected_namespace_root")
        if protected
        else _external_root(item)
        for item in value
    )
    if result != tuple(sorted(set(result))):
        raise ValueError("implementation import roots must be sorted and unique")
    if protected and any(
        left == right
        or left.startswith(right + ".")
        or right.startswith(left + ".")
        for index, left in enumerate(result)
        for right in result[index + 1 :]
    ):
        raise ValueError("protected namespace roots must not overlap")
    return result


def _external_root(value: object) -> str:
    result = _ascii_text(
        value,
        name="external_import_root",
        maximum=MAXIMUM_IMPLEMENTATION_MODULE_NAME_BYTES,
    )
    if (
        _MODULE_COMPONENT_RE.fullmatch(result) is None
        or keyword.iskeyword(result)
    ):
        raise ValueError("external import root is not allowed")
    if (
        result in _BANNED_IMPORT_ROOTS
        or result in _FORBIDDEN_DYNAMIC_IMPORT_ROOTS
    ):
        raise _NamePolicyViolation(
            "external import root is forbidden by name policy"
        )
    _require_name_policy(result)
    return result


def _under_root(value: str, root: str) -> bool:
    return value == root or value.startswith(root + ".")


def _protected_root_for(
    value: str,
    roots: Tuple[str, ...],
) -> Optional[str]:
    matches = tuple(root for root in roots if _under_root(value, root))
    if len(matches) > 1:
        raise ValueError("protected namespace roots overlap")
    return matches[0] if matches else None


@dataclass(frozen=True)
class ImplementationClosureModuleV1:
    """One exact module-to-archive-object mapping."""

    module_name: str
    is_package: bool
    role_id: str
    source_byte_count: int
    source_object_id: str
    source_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not ImplementationClosureModuleV1:
            raise TypeError("implementation closure module must be exact")
        _module_name(self.module_name, name="module_name")
        if type(self.is_package) is not bool:
            raise TypeError("is_package must be an exact boolean")
        if (
            type(self.role_id) is not str
            or self.role_id not in IMPLEMENTATION_CLOSURE_ALLOWED_ROLE_IDS
        ):
            raise _NamePolicyViolation(
                "implementation source role is not allowed"
            )
        if (
            type(self.source_byte_count) is not int
            or self.source_byte_count < 0
            or self.source_byte_count
            > _archive.MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES
        ):
            raise ValueError("implementation source byte count is invalid")
        _source_object_id(self.source_object_id)
        _sha256_text(self.source_sha256, name="source_sha256")


@dataclass(frozen=True)
class ImplementationClosureModuleInputV1:
    """Builder input for one exact already-captured source module."""

    module_name: str
    is_package: bool
    role_id: str
    source_object_id: str
    source_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not ImplementationClosureModuleInputV1:
            raise TypeError("implementation source input must be exact")
        if type(self.source_bytes) is not bytes:
            raise TypeError("implementation source bytes must be exact")
        if len(self.source_bytes) > _archive.MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES:
            raise ValueError("implementation source bytes exceed their ceiling")
        ImplementationClosureModuleV1(
            module_name=self.module_name,
            is_package=self.is_package,
            role_id=self.role_id,
            source_byte_count=len(self.source_bytes),
            source_object_id=self.source_object_id,
            source_sha256=hashlib.sha256(self.source_bytes).hexdigest(),
        )


@dataclass(frozen=True)
class AdapterImplementationEntryPointV1:
    """The adapter-construction callable selected before case dispatch."""

    module_name: str
    callable_name: str
    construction_mode_id: str = field(
        default=IMPLEMENTATION_CLOSURE_CONSTRUCTION_MODE_ID,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not AdapterImplementationEntryPointV1:
            raise TypeError("adapter implementation entry point must be exact")
        _module_name(self.module_name, name="entry_point.module_name")
        _callable_name(self.callable_name, name="entry_point.callable_name")
        if (
            type(self.construction_mode_id) is not str
            or self.construction_mode_id
            != IMPLEMENTATION_CLOSURE_CONSTRUCTION_MODE_ID
        ):
            raise ValueError("adapter construction mode differs")


@dataclass(frozen=True)
class AdapterImplementationRuntimeEntryPointV1:
    """The trusted child-runtime callable bound into the same closure."""

    module_name: str
    callable_name: str

    def __post_init__(self) -> None:
        if type(self) is not AdapterImplementationRuntimeEntryPointV1:
            raise TypeError("adapter runtime entry point must be exact")
        _module_name(self.module_name, name="runtime_entry_point.module_name")
        _callable_name(
            self.callable_name,
            name="runtime_entry_point.callable_name",
        )


@dataclass(frozen=True)
class AdapterImplementationClosureV1:
    """The complete signed-wire adapter implementation closure."""

    adapter_id: str
    adapter_version: str
    dependency_lock_sha256: str
    entry_point: AdapterImplementationEntryPointV1
    external_import_roots: Tuple[str, ...]
    modules: Tuple[ImplementationClosureModuleV1, ...]
    protected_namespace_roots: Tuple[str, ...]
    runtime_entry_point: AdapterImplementationRuntimeEntryPointV1
    source_archive_inventory_sha256: str
    source_archive_sha256: str
    artifact_type: str = field(
        default=IMPLEMENTATION_CLOSURE_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)

    def __post_init__(self) -> None:
        if type(self) is not AdapterImplementationClosureV1:
            raise TypeError("adapter implementation closure must be exact")
        _adapter_id(self.adapter_id)
        _adapter_version(self.adapter_version)
        _sha256_text(
            self.dependency_lock_sha256,
            name="dependency_lock_sha256",
        )
        if type(self.entry_point) is not AdapterImplementationEntryPointV1:
            raise TypeError("entry_point must be exact")
        AdapterImplementationEntryPointV1.__post_init__(self.entry_point)
        if (
            type(self.runtime_entry_point)
            is not AdapterImplementationRuntimeEntryPointV1
        ):
            raise TypeError("runtime_entry_point must be exact")
        AdapterImplementationRuntimeEntryPointV1.__post_init__(
            self.runtime_entry_point
        )
        external = _root_tuple(
            self.external_import_roots,
            protected=False,
        )
        protected = _root_tuple(
            self.protected_namespace_roots,
            protected=True,
        )
        if external != self.external_import_roots:
            raise ValueError("external import roots differ")
        if protected != self.protected_namespace_roots:
            raise ValueError("protected namespace roots differ")
        if any(root in external for root in protected):
            raise ValueError("protected and external roots overlap")
        if type(self.modules) is not tuple or not self.modules:
            raise TypeError("modules must be a nonempty exact tuple")
        if len(self.modules) > MAXIMUM_IMPLEMENTATION_MODULES:
            raise ValueError("too many implementation modules")
        if any(
            type(item) is not ImplementationClosureModuleV1
            for item in self.modules
        ):
            raise TypeError("modules contain a nonexact record")
        for item in self.modules:
            ImplementationClosureModuleV1.__post_init__(item)
        names = tuple(item.module_name for item in self.modules)
        if names != tuple(sorted(set(names))):
            raise ValueError("module names must be sorted and unique")
        source_objects = tuple(
            (item.role_id, item.source_object_id) for item in self.modules
        )
        if len(source_objects) != len(set(source_objects)):
            raise ValueError("module source-object selections must be unique")
        if len({item.source_object_id for item in self.modules}) != len(
            self.modules
        ):
            raise ValueError("source object identifiers must be globally unique")
        if any(
            _protected_root_for(item.module_name, protected) is None
            for item in self.modules
        ):
            raise _PackageClosureViolation(
                "module is outside every protected namespace"
            )
        by_name = {item.module_name: item for item in self.modules}
        for root in protected:
            root_record = by_name.get(root)
            if root_record is None or root_record.is_package is not True:
                raise _PackageClosureViolation(
                    "protected root is not a declared package"
                )
        for item in self.modules:
            parts = item.module_name.split(".")
            for end in range(1, len(parts)):
                parent = ".".join(parts[:end])
                record = by_name.get(parent)
                if record is None or record.is_package is not True:
                    raise _PackageClosureViolation(
                        "module package parent is not closed"
                    )
        entry_record = by_name.get(self.entry_point.module_name)
        runtime_record = by_name.get(self.runtime_entry_point.module_name)
        if (
            entry_record is None
            or entry_record.is_package
            or entry_record.role_id != "adapter-source"
            or runtime_record is None
            or runtime_record.is_package
            or runtime_record.role_id != "contract-source"
        ):
            raise _EntryPointViolation(
                "implementation entry-point module differs"
            )
        _sha256_text(
            self.source_archive_inventory_sha256,
            name="source_archive_inventory_sha256",
        )
        _sha256_text(
            self.source_archive_sha256,
            name="source_archive_sha256",
        )
        if (
            self.artifact_type != IMPLEMENTATION_CLOSURE_ARTIFACT_TYPE
            or type(self.artifact_type) is not str
            or self.format_version != "1"
            or type(self.format_version) is not str
        ):
            raise ValueError("implementation closure constants differ")


class ValidatedImplementationClosureModuleV1(NamedTuple):
    """One archive-selected source and its statically observed imports."""

    module: ImplementationClosureModuleV1
    source_bytes: bytes
    imported_module_names: Tuple[str, ...]


@dataclass(frozen=True)
class ImplementationClosureValidationReceiptV1:
    """Canonical source-consistency receipt with fixed execution nonclaims."""

    adapter_id: str
    adapter_version: str
    closure_byte_count: int
    closure_file_sha256: str
    closure_sha256: str
    dependency_lock_sha256: str
    entry_point_module_name: str
    entry_point_callable_name: str
    runtime_entry_point_module_name: str
    runtime_entry_point_callable_name: str
    module_count: int
    observed_import_edge_count: int
    observed_import_graph_sha256: str
    source_archive_inventory_sha256: str
    source_archive_sha256: str
    canonical_closure_validated: bool
    exact_archive_membership_validated: bool
    package_parent_closure_validated: bool
    protected_import_closure_validated: bool
    external_import_roots_validated: bool
    recognized_dynamic_import_primitives_rejected: bool
    entry_point_zero_argument_mode_validated: bool
    source_loaded: bool
    runtime_entry_point_executed: bool
    adapter_constructed: bool
    adapter_executed: bool
    runtime_host_fallback_denial_enforced: bool
    execution_attested: bool
    containment_enforced: bool
    containment_attested: bool
    expected_material_nonexposure_attested: bool
    semantic_truth_attested: bool
    decision_made: bool
    artifact_type: str = field(
        default=IMPLEMENTATION_CLOSURE_RECEIPT_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)
    status_id: str = field(
        default=IMPLEMENTATION_CLOSURE_VALIDATION_STATUS_ID,
        init=False,
    )
    decision_status_id: str = field(
        default=IMPLEMENTATION_CLOSURE_DECISION_STATUS_ID,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not ImplementationClosureValidationReceiptV1:
            raise TypeError("implementation closure receipt must be exact")
        _adapter_id(self.adapter_id)
        _adapter_version(self.adapter_version)
        if (
            type(self.closure_byte_count) is not int
            or self.closure_byte_count <= 0
            or self.closure_byte_count > MAXIMUM_IMPLEMENTATION_CLOSURE_BYTES
            or type(self.module_count) is not int
            or self.module_count <= 0
            or self.module_count > MAXIMUM_IMPLEMENTATION_MODULES
            or type(self.observed_import_edge_count) is not int
            or self.observed_import_edge_count < 0
            or self.observed_import_edge_count
            > MAXIMUM_IMPLEMENTATION_JSON_TOKENS
        ):
            raise ValueError("implementation closure receipt count is invalid")
        for name in (
            "closure_file_sha256",
            "closure_sha256",
            "dependency_lock_sha256",
            "observed_import_graph_sha256",
            "source_archive_inventory_sha256",
            "source_archive_sha256",
        ):
            _sha256_text(getattr(self, name), name=name)
        _module_name(
            self.entry_point_module_name,
            name="entry_point_module_name",
        )
        _callable_name(
            self.entry_point_callable_name,
            name="entry_point_callable_name",
        )
        _module_name(
            self.runtime_entry_point_module_name,
            name="runtime_entry_point_module_name",
        )
        _callable_name(
            self.runtime_entry_point_callable_name,
            name="runtime_entry_point_callable_name",
        )
        true_claims = (
            self.canonical_closure_validated,
            self.exact_archive_membership_validated,
            self.package_parent_closure_validated,
            self.protected_import_closure_validated,
            self.external_import_roots_validated,
            self.recognized_dynamic_import_primitives_rejected,
            self.entry_point_zero_argument_mode_validated,
        )
        false_claims = (
            self.source_loaded,
            self.runtime_entry_point_executed,
            self.adapter_constructed,
            self.adapter_executed,
            self.runtime_host_fallback_denial_enforced,
            self.execution_attested,
            self.containment_enforced,
            self.containment_attested,
            self.expected_material_nonexposure_attested,
            self.semantic_truth_attested,
            self.decision_made,
        )
        if any(value is not True for value in true_claims):
            raise ValueError("implementation closure receipt claims must be true")
        if any(value is not False for value in false_claims):
            raise ValueError("implementation closure nonclaims must remain false")
        if (
            self.artifact_type
            != IMPLEMENTATION_CLOSURE_RECEIPT_ARTIFACT_TYPE
            or self.format_version != "1"
            or self.status_id
            != IMPLEMENTATION_CLOSURE_VALIDATION_STATUS_ID
            or self.decision_status_id
            != IMPLEMENTATION_CLOSURE_DECISION_STATUS_ID
        ):
            raise ValueError("implementation closure receipt constants differ")


class ValidatedAdapterImplementationClosureV1(NamedTuple):
    """Validated raw closure, archive, sources, import graph, and receipt."""

    closure: AdapterImplementationClosureV1
    closure_bytes: bytes
    closure_file_sha256: str
    closure_sha256: str
    source_archive: _archive.ValidatedSourceArchiveV1
    dependency_lock_bytes: bytes
    modules: Tuple[ValidatedImplementationClosureModuleV1, ...]
    receipt: ImplementationClosureValidationReceiptV1
    receipt_bytes: bytes
    receipt_sha256: str


_CLOSURE_KEYS = (
    "adapter_id",
    "adapter_version",
    "artifact_type",
    "dependency_lock_sha256",
    "entry_point",
    "external_import_roots",
    "format_version",
    "modules",
    "protected_namespace_roots",
    "runtime_entry_point",
    "source_archive_inventory_sha256",
    "source_archive_sha256",
)
_ENTRY_POINT_KEYS = (
    "callable_name",
    "construction_mode_id",
    "module_name",
)
_RUNTIME_ENTRY_POINT_KEYS = ("callable_name", "module_name")
_MODULE_KEYS = (
    "is_package",
    "module_name",
    "role_id",
    "source_byte_count",
    "source_object_id",
    "source_sha256",
)
_RECEIPT_KEYS = (
    "adapter_constructed",
    "adapter_executed",
    "adapter_id",
    "adapter_version",
    "artifact_type",
    "canonical_closure_validated",
    "closure_byte_count",
    "closure_file_sha256",
    "closure_sha256",
    "containment_attested",
    "containment_enforced",
    "decision_made",
    "decision_status_id",
    "dependency_lock_sha256",
    "entry_point_callable_name",
    "entry_point_module_name",
    "entry_point_zero_argument_mode_validated",
    "exact_archive_membership_validated",
    "execution_attested",
    "expected_material_nonexposure_attested",
    "external_import_roots_validated",
    "format_version",
    "module_count",
    "observed_import_edge_count",
    "observed_import_graph_sha256",
    "package_parent_closure_validated",
    "protected_import_closure_validated",
    "recognized_dynamic_import_primitives_rejected",
    "runtime_entry_point_callable_name",
    "runtime_entry_point_executed",
    "runtime_entry_point_module_name",
    "runtime_host_fallback_denial_enforced",
    "semantic_truth_attested",
    "source_archive_inventory_sha256",
    "source_archive_sha256",
    "source_loaded",
    "status_id",
)


def adapter_implementation_closure_tree(
    value: AdapterImplementationClosureV1,
) -> dict:
    """Return the exact plain signed-wire projection."""

    if type(value) is not AdapterImplementationClosureV1:
        raise TypeError("adapter implementation closure must be exact")
    AdapterImplementationClosureV1.__post_init__(value)
    return {
        "adapter_id": value.adapter_id,
        "adapter_version": value.adapter_version,
        "artifact_type": value.artifact_type,
        "dependency_lock_sha256": value.dependency_lock_sha256,
        "entry_point": {
            "callable_name": value.entry_point.callable_name,
            "construction_mode_id": (
                value.entry_point.construction_mode_id
            ),
            "module_name": value.entry_point.module_name,
        },
        "external_import_roots": list(value.external_import_roots),
        "format_version": value.format_version,
        "modules": [
            {
                "is_package": item.is_package,
                "module_name": item.module_name,
                "role_id": item.role_id,
                "source_byte_count": item.source_byte_count,
                "source_object_id": item.source_object_id,
                "source_sha256": item.source_sha256,
            }
            for item in value.modules
        ],
        "protected_namespace_roots": list(
            value.protected_namespace_roots
        ),
        "runtime_entry_point": {
            "callable_name": value.runtime_entry_point.callable_name,
            "module_name": value.runtime_entry_point.module_name,
        },
        "source_archive_inventory_sha256": (
            value.source_archive_inventory_sha256
        ),
        "source_archive_sha256": value.source_archive_sha256,
    }


def _canonical_json_bytes(value: object, *, maximum: int) -> bytes:
    try:
        result = json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        _fail(ImplementationClosureCode.SCHEMA)
    if not result or len(result) > maximum:
        _fail(ImplementationClosureCode.RESOURCE)
    return result


def adapter_implementation_closure_bytes(
    value: AdapterImplementationClosureV1,
) -> bytes:
    """Serialize one closure as bounded canonical ASCII JSON."""

    return _canonical_json_bytes(
        adapter_implementation_closure_tree(value),
        maximum=MAXIMUM_IMPLEMENTATION_CLOSURE_BYTES,
    )


def _domain_sha256(domain: str, payload: bytes) -> str:
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except (AttributeError, UnicodeError):
        _fail(ImplementationClosureCode.INTERNAL)
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def adapter_implementation_closure_sha256(
    value: object,
) -> str:
    """Return the domain-separated digest of closure bytes or a typed closure."""

    if type(value) is AdapterImplementationClosureV1:
        payload = adapter_implementation_closure_bytes(value)
    elif type(value) is bytes:
        payload = value
        if (
            not payload
            or len(payload) > MAXIMUM_IMPLEMENTATION_CLOSURE_BYTES
        ):
            _fail(ImplementationClosureCode.RESOURCE)
    else:
        _fail(ImplementationClosureCode.INPUT_TYPE)
    return _domain_sha256(IMPLEMENTATION_CLOSURE_DIGEST_DOMAIN, payload)


def implementation_closure_validation_receipt_tree(
    value: ImplementationClosureValidationReceiptV1,
) -> dict:
    """Return the exact canonical receipt projection."""

    if type(value) is not ImplementationClosureValidationReceiptV1:
        raise TypeError("implementation closure receipt must be exact")
    ImplementationClosureValidationReceiptV1.__post_init__(value)
    return {name: getattr(value, name) for name in _RECEIPT_KEYS}


def implementation_closure_validation_receipt_bytes(
    value: ImplementationClosureValidationReceiptV1,
) -> bytes:
    """Serialize the fixed-claim validation receipt."""

    return _canonical_json_bytes(
        implementation_closure_validation_receipt_tree(value),
        maximum=MAXIMUM_IMPLEMENTATION_CLOSURE_RECEIPT_BYTES,
    )


def implementation_closure_validation_receipt_sha256(
    value: ImplementationClosureValidationReceiptV1,
) -> str:
    """Return the receipt's domain-separated digest."""

    return _domain_sha256(
        IMPLEMENTATION_CLOSURE_RECEIPT_DIGEST_DOMAIN,
        implementation_closure_validation_receipt_bytes(value),
    )


def parse_implementation_closure_validation_receipt(
    receipt_bytes: bytes,
) -> ImplementationClosureValidationReceiptV1:
    """Strict-parse canonical receipt bytes into the exact receipt type."""

    if type(receipt_bytes) is not bytes:
        _fail(ImplementationClosureCode.INPUT_TYPE)
    if (
        not receipt_bytes
        or len(receipt_bytes)
        > MAXIMUM_IMPLEMENTATION_CLOSURE_RECEIPT_BYTES
    ):
        _fail(ImplementationClosureCode.RESOURCE)
    tree = _strict_json_tree(receipt_bytes)
    if (
        type(tree) is not dict
        or tuple(sorted(tree)) != tuple(sorted(_RECEIPT_KEYS))
    ):
        _fail(ImplementationClosureCode.RECEIPT)
    fields = ImplementationClosureValidationReceiptV1.__dataclass_fields__
    try:
        receipt = ImplementationClosureValidationReceiptV1(
            **{
                name: tree[name]
                for name, record in fields.items()
                if record.init
            }
        )
        if implementation_closure_validation_receipt_tree(receipt) != tree:
            _fail(ImplementationClosureCode.RECEIPT)
        if (
            implementation_closure_validation_receipt_bytes(receipt)
            != receipt_bytes
        ):
            _fail(ImplementationClosureCode.NONCANONICAL)
    except ImplementationClosureError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError):
        _fail(ImplementationClosureCode.RECEIPT)
    return receipt


def _lexical_preflight(value: object) -> bytes:
    if type(value) is not bytes:
        _fail(ImplementationClosureCode.INPUT_TYPE)
    if not value or len(value) > MAXIMUM_IMPLEMENTATION_CLOSURE_BYTES:
        _fail(ImplementationClosureCode.RESOURCE)
    if any(byte >= 0x80 for byte in value):
        _fail(ImplementationClosureCode.JSON)
    depth = 0
    tokens = 0
    in_string = False
    escaped = False
    string_bytes = 0
    for byte in value:
        if in_string:
            string_bytes += 1
            if string_bytes > MAXIMUM_IMPLEMENTATION_JSON_STRING_BYTES:
                _fail(ImplementationClosureCode.RESOURCE)
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
            string_bytes = 0
            tokens += 1
        elif byte in (0x7B, 0x5B):
            depth += 1
            tokens += 1
            if depth > MAXIMUM_IMPLEMENTATION_JSON_DEPTH:
                _fail(ImplementationClosureCode.RESOURCE)
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0:
                _fail(ImplementationClosureCode.JSON)
        elif byte in (0x2C, 0x3A):
            tokens += 1
        if tokens > MAXIMUM_IMPLEMENTATION_JSON_TOKENS:
            _fail(ImplementationClosureCode.RESOURCE)
    if in_string or depth != 0:
        _fail(ImplementationClosureCode.JSON)
    return value


class _DuplicateKeyError(ValueError):
    pass


def _validate_json_tree(value: object) -> None:
    nodes = 0
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if (
            nodes > MAXIMUM_IMPLEMENTATION_JSON_TOKENS
            or depth > MAXIMUM_IMPLEMENTATION_JSON_DEPTH
        ):
            _fail(ImplementationClosureCode.RESOURCE)
        if current is None or type(current) is bool:
            continue
        if type(current) is int:
            if abs(current) > _MAXIMUM_SAFE_INTEGER:
                _fail(ImplementationClosureCode.JSON)
            continue
        if type(current) is str:
            try:
                encoded = current.encode("utf-8", "strict")
            except UnicodeError:
                _fail(ImplementationClosureCode.JSON)
            if len(encoded) > MAXIMUM_IMPLEMENTATION_JSON_STRING_BYTES:
                _fail(ImplementationClosureCode.RESOURCE)
            continue
        if type(current) is list:
            stack.extend((item, depth + 1) for item in reversed(current))
            continue
        if type(current) is dict:
            for key, item in reversed(tuple(current.items())):
                if type(key) is not str:
                    _fail(ImplementationClosureCode.JSON)
                stack.append((item, depth + 1))
                stack.append((key, depth + 1))
            continue
        _fail(ImplementationClosureCode.JSON)


def _strict_json_tree(value: object) -> object:
    raw = _lexical_preflight(value)

    def object_pairs(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                raise _DuplicateKeyError()
            result[key] = item
        return result

    def parse_integer(token):
        digits = token[1:] if token.startswith("-") else token
        if len(digits) > 16:
            raise ValueError()
        result = int(token, 10)
        if abs(result) > _MAXIMUM_SAFE_INTEGER:
            raise ValueError()
        return result

    def reject_number(_token):
        raise ValueError()

    try:
        text = raw.decode("ascii", "strict")
        tree = json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_int=parse_integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
    except (
        _DuplicateKeyError,
        TypeError,
        UnicodeError,
        ValueError,
        RecursionError,
    ):
        _fail(ImplementationClosureCode.JSON)
    _validate_json_tree(tree)
    try:
        canonical = _canonical_json_bytes(
            tree,
            maximum=MAXIMUM_IMPLEMENTATION_CLOSURE_BYTES,
        )
    except ImplementationClosureError as error:
        if error.code == ImplementationClosureCode.RESOURCE.value:
            raise
        _fail(ImplementationClosureCode.JSON)
    if canonical != raw:
        _fail(ImplementationClosureCode.NONCANONICAL)
    return tree


def _require_keys(value: object, names: Tuple[str, ...]) -> dict:
    if (
        type(value) is not dict
        or tuple(sorted(value)) != tuple(sorted(names))
    ):
        _fail(ImplementationClosureCode.SCHEMA)
    return value


def _entry_point_from_tree(value: object) -> AdapterImplementationEntryPointV1:
    tree = _require_keys(value, _ENTRY_POINT_KEYS)
    if (
        tree["construction_mode_id"]
        != IMPLEMENTATION_CLOSURE_CONSTRUCTION_MODE_ID
        or type(tree["construction_mode_id"]) is not str
    ):
        _fail(ImplementationClosureCode.SCHEMA)
    try:
        return AdapterImplementationEntryPointV1(
            module_name=tree["module_name"],
            callable_name=tree["callable_name"],
        )
    except _NamePolicyViolation:
        _fail(ImplementationClosureCode.NAME_POLICY)
    except (TypeError, ValueError):
        _fail(ImplementationClosureCode.SCHEMA)


def _runtime_entry_point_from_tree(
    value: object,
) -> AdapterImplementationRuntimeEntryPointV1:
    tree = _require_keys(value, _RUNTIME_ENTRY_POINT_KEYS)
    try:
        return AdapterImplementationRuntimeEntryPointV1(
            module_name=tree["module_name"],
            callable_name=tree["callable_name"],
        )
    except _NamePolicyViolation:
        _fail(ImplementationClosureCode.NAME_POLICY)
    except (TypeError, ValueError):
        _fail(ImplementationClosureCode.SCHEMA)


def _module_from_tree(value: object) -> ImplementationClosureModuleV1:
    tree = _require_keys(value, _MODULE_KEYS)
    try:
        return ImplementationClosureModuleV1(
            module_name=tree["module_name"],
            is_package=tree["is_package"],
            role_id=tree["role_id"],
            source_byte_count=tree["source_byte_count"],
            source_object_id=tree["source_object_id"],
            source_sha256=tree["source_sha256"],
        )
    except _NamePolicyViolation:
        _fail(ImplementationClosureCode.NAME_POLICY)
    except (TypeError, ValueError):
        _fail(ImplementationClosureCode.SCHEMA)


def parse_adapter_implementation_closure(
    closure_bytes: bytes,
) -> AdapterImplementationClosureV1:
    """Strict-parse arbitrary bytes into the exact closure type."""

    tree = _require_keys(_strict_json_tree(closure_bytes), _CLOSURE_KEYS)
    if (
        tree["artifact_type"] != IMPLEMENTATION_CLOSURE_ARTIFACT_TYPE
        or type(tree["artifact_type"]) is not str
        or tree["format_version"] != "1"
        or type(tree["format_version"]) is not str
        or type(tree["external_import_roots"]) is not list
        or type(tree["protected_namespace_roots"]) is not list
        or type(tree["modules"]) is not list
        or not tree["modules"]
    ):
        _fail(ImplementationClosureCode.SCHEMA)
    try:
        closure = AdapterImplementationClosureV1(
            adapter_id=tree["adapter_id"],
            adapter_version=tree["adapter_version"],
            dependency_lock_sha256=tree["dependency_lock_sha256"],
            entry_point=_entry_point_from_tree(tree["entry_point"]),
            external_import_roots=tuple(tree["external_import_roots"]),
            modules=tuple(_module_from_tree(item) for item in tree["modules"]),
            protected_namespace_roots=tuple(
                tree["protected_namespace_roots"]
            ),
            runtime_entry_point=_runtime_entry_point_from_tree(
                tree["runtime_entry_point"]
            ),
            source_archive_inventory_sha256=(
                tree["source_archive_inventory_sha256"]
            ),
            source_archive_sha256=tree["source_archive_sha256"],
        )
        canonical = adapter_implementation_closure_bytes(closure)
    except ImplementationClosureError:
        raise
    except _NamePolicyViolation:
        _fail(ImplementationClosureCode.NAME_POLICY)
    except _PackageClosureViolation:
        _fail(ImplementationClosureCode.PACKAGE_CLOSURE)
    except _EntryPointViolation:
        _fail(ImplementationClosureCode.ENTRY_POINT)
    except (TypeError, ValueError):
        _fail(ImplementationClosureCode.SCHEMA)
    if canonical != closure_bytes:
        _fail(ImplementationClosureCode.NONCANONICAL)
    return closure


def _expected_archive_members(
    modules: Tuple[ImplementationClosureModuleV1, ...],
) -> Tuple[_archive.SourceArchiveMemberV1, ...]:
    counts = Counter(
        (item.source_sha256, item.source_byte_count) for item in modules
    )
    return tuple(
        _archive.SourceArchiveMemberV1(
            content_byte_count=byte_count,
            content_sha256=digest,
            occurrence_count=counts[(digest, byte_count)],
        )
        for digest, byte_count in sorted(counts)
    )


def _expected_archive_objects(
    modules: Tuple[ImplementationClosureModuleV1, ...],
) -> Tuple[_archive.SourceArchiveObjectV1, ...]:
    return tuple(
        sorted(
            (
                _archive.SourceArchiveObjectV1(
                    role_id=item.role_id,
                    source_byte_count=item.source_byte_count,
                    source_object_id=item.source_object_id,
                    source_sha256=item.source_sha256,
                )
                for item in modules
            ),
            key=lambda item: (item.role_id, item.source_object_id),
        )
    )


def _source_bytes_by_identity(
    source_archive: _archive.ValidatedSourceArchiveV1,
) -> Dict[Tuple[str, int], bytes]:
    result = {}
    for member in source_archive.members:
        key = (member.content_sha256, member.content_byte_count)
        previous = result.get(key)
        if previous is not None and previous != member.content_bytes:
            _fail(ImplementationClosureCode.ARCHIVE_MEMBERSHIP)
        result[key] = member.content_bytes
    return result


def _source_tree(value: bytes) -> ast.Module:
    if type(value) is not bytes:
        _fail(ImplementationClosureCode.ARCHIVE_MEMBERSHIP)
    if len(value) > _archive.MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES:
        _fail(ImplementationClosureCode.RESOURCE)
    if value.startswith(b"\xef\xbb\xbf") or b"\x00" in value or b"\r" in value:
        _fail(ImplementationClosureCode.IMPORT_POLICY)
    try:
        text = value.decode("utf-8", "strict")
    except UnicodeError:
        _fail(ImplementationClosureCode.IMPORT_POLICY)
    if text.encode("utf-8", "strict") != value:
        _fail(ImplementationClosureCode.IMPORT_POLICY)
    lines = value.splitlines()
    if (
        len(lines) > MAXIMUM_IMPLEMENTATION_SOURCE_LINES
        or any(
            len(line) > MAXIMUM_IMPLEMENTATION_SOURCE_LINE_BYTES
            for line in lines
        )
    ):
        _fail(ImplementationClosureCode.RESOURCE)
    try:
        tree = ast.parse(
            text,
            filename="<implementation-closure-source>",
            mode="exec",
            type_comments=False,
            feature_version=9,
        )
    except (IndentationError, SyntaxError, ValueError):
        _fail(ImplementationClosureCode.IMPORT_POLICY)
    except (MemoryError, RecursionError):
        _fail(ImplementationClosureCode.RESOURCE)
    count = 0
    stack = [(tree, 0)]
    while stack:
        node, depth = stack.pop()
        count += 1
        if (
            count > MAXIMUM_IMPLEMENTATION_SOURCE_AST_NODES
            or depth > MAXIMUM_IMPLEMENTATION_SOURCE_AST_DEPTH
        ):
            _fail(ImplementationClosureCode.RESOURCE)
        stack.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
    return tree


def _relative_base(
    module: ImplementationClosureModuleV1,
    level: int,
) -> str:
    package = (
        module.module_name
        if module.is_package
        else module.module_name.rpartition(".")[0]
    )
    parts = package.split(".") if package else []
    ascend = level - 1
    if level <= 0 or ascend >= len(parts):
        _fail(ImplementationClosureCode.IMPORT_POLICY)
    return ".".join(parts[: len(parts) - ascend])


def _attribute_root(value: ast.AST) -> Optional[str]:
    current = value
    while isinstance(current, ast.Attribute):
        current = current.value
    if isinstance(current, ast.Name):
        return current.id
    return None


def _module_imports(
    module: ImplementationClosureModuleV1,
    source_bytes: bytes,
    *,
    module_names: frozenset,
    protected_roots: Tuple[str, ...],
    external_roots: Tuple[str, ...],
) -> Tuple[ast.Module, Tuple[str, ...]]:
    tree = _source_tree(source_bytes)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Name)
                and node.func.id in _FORBIDDEN_DYNAMIC_CALL_NAMES
            ):
                _fail(ImplementationClosureCode.IMPORT_POLICY)
            root = _attribute_root(node.func)
            if root in _FORBIDDEN_DYNAMIC_CALL_ROOTS:
                _fail(ImplementationClosureCode.IMPORT_POLICY)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported = alias.name
                if type(imported) is not str or not imported:
                    _fail(ImplementationClosureCode.IMPORT_POLICY)
                if imported.split(".", 1)[0] == "importlib":
                    _fail(ImplementationClosureCode.IMPORT_POLICY)
                imports.add(imported)
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__" and node.level == 0:
                continue
            if node.level:
                base = _relative_base(module, node.level)
                imported = (
                    base + "." + node.module
                    if node.module
                    else base
                )
            else:
                imported = node.module
            if type(imported) is not str or not imported:
                _fail(ImplementationClosureCode.IMPORT_POLICY)
            if node.level == 0 and imported.split(".", 1)[0] == "importlib":
                if imported == "importlib":
                    if (
                        not node.names
                        or any(
                            alias.name != "metadata"
                            for alias in node.names
                        )
                    ):
                        _fail(ImplementationClosureCode.IMPORT_POLICY)
                elif imported != "importlib.metadata":
                    _fail(ImplementationClosureCode.IMPORT_POLICY)
            imports.add(imported)
            for alias in node.names:
                candidate = imported + "." + alias.name
                if candidate in module_names:
                    imports.add(candidate)
    ordered = tuple(sorted(imports))
    for imported in ordered:
        try:
            _module_name(imported, name="imported_module_name")
        except (TypeError, ValueError):
            _fail(ImplementationClosureCode.IMPORT_POLICY)
        root = imported.split(".", 1)[0]
        if (
            root in _BANNED_IMPORT_ROOTS
            or root in _FORBIDDEN_DYNAMIC_IMPORT_ROOTS
        ):
            _fail(ImplementationClosureCode.IMPORT_POLICY)
        protected = _protected_root_for(imported, protected_roots)
        if protected is not None:
            if imported not in module_names:
                _fail(ImplementationClosureCode.IMPORT_POLICY)
        elif root not in external_roots:
            _fail(ImplementationClosureCode.IMPORT_POLICY)
    return tree, ordered


def _required_argument_count(arguments: ast.arguments, *, method: bool) -> int:
    positional = tuple(arguments.posonlyargs) + tuple(arguments.args)
    defaults = tuple(arguments.defaults)
    required = len(positional) - len(defaults)
    if method:
        required = max(0, required - 1)
    required += sum(
        default is None for default in arguments.kw_defaults
    )
    return required


def _has_runtime_entry_signature(arguments: ast.arguments) -> bool:
    positional = tuple(arguments.posonlyargs) + tuple(arguments.args)
    return (
        len(positional) == 2
        and tuple(item.arg for item in positional)
        == ("case_input_bytes", "adapter")
        and not arguments.defaults
        and arguments.vararg is None
        and arguments.kwarg is None
        and not any(
            default is None for default in arguments.kw_defaults
        )
    )


def _entry_definition(
    tree: ast.Module,
    callable_name: str,
) -> Optional[ast.AST]:
    matches = tuple(
        item
        for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and item.name == callable_name
    )
    return matches[0] if len(matches) == 1 else None


def _validate_entry_points(
    closure: AdapterImplementationClosureV1,
    trees: Dict[str, ast.Module],
) -> None:
    entry_tree = trees.get(closure.entry_point.module_name)
    runtime_tree = trees.get(closure.runtime_entry_point.module_name)
    if entry_tree is None or runtime_tree is None:
        _fail(ImplementationClosureCode.ENTRY_POINT)
    entry = _entry_definition(
        entry_tree,
        closure.entry_point.callable_name,
    )
    runtime = _entry_definition(
        runtime_tree,
        closure.runtime_entry_point.callable_name,
    )
    if (
        entry is None
        or runtime is None
        or isinstance(entry, ast.AsyncFunctionDef)
        or isinstance(runtime, (ast.AsyncFunctionDef, ast.ClassDef))
    ):
        _fail(ImplementationClosureCode.ENTRY_POINT)
    if isinstance(entry, ast.FunctionDef):
        if entry.decorator_list or _required_argument_count(
            entry.args,
            method=False,
        ):
            _fail(ImplementationClosureCode.ENTRY_POINT)
    elif isinstance(entry, ast.ClassDef):
        if entry.decorator_list or entry.keywords:
            _fail(ImplementationClosureCode.ENTRY_POINT)
        constructors = tuple(
            item
            for item in entry.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            and item.name in ("__init__", "__new__")
        )
        if any(
            isinstance(item, ast.AsyncFunctionDef)
            or item.decorator_list
            or _required_argument_count(item.args, method=True)
            for item in constructors
        ):
            _fail(ImplementationClosureCode.ENTRY_POINT)
    else:  # pragma: no cover - exhaustive AST types above
        _fail(ImplementationClosureCode.ENTRY_POINT)
    if (
        runtime.decorator_list
        or not _has_runtime_entry_signature(runtime.args)
    ):
        _fail(ImplementationClosureCode.ENTRY_POINT)


def _import_graph_sha256(
    modules: Tuple[ValidatedImplementationClosureModuleV1, ...],
) -> str:
    tree = [
        {
            "imported_module_names": list(item.imported_module_names),
            "module_name": item.module.module_name,
        }
        for item in modules
    ]
    payload = _canonical_json_bytes(
        tree,
        maximum=MAXIMUM_IMPLEMENTATION_CLOSURE_BYTES,
    )
    return _domain_sha256(
        IMPLEMENTATION_IMPORT_GRAPH_DIGEST_DOMAIN,
        payload,
    )


def _snapshot_dependency_lock(value: object) -> bytes:
    if type(value) is not bytes:
        _fail(ImplementationClosureCode.INPUT_TYPE)
    if (
        not value
        or len(value) > MAXIMUM_IMPLEMENTATION_DEPENDENCY_LOCK_BYTES
    ):
        _fail(ImplementationClosureCode.RESOURCE)
    return bytes(value)


def _validate_adapter_implementation_closure(
    closure_bytes: bytes,
    *,
    source_archive_inventory_bytes: bytes,
    source_archive_bytes: bytes,
    dependency_lock_bytes: bytes,
) -> ValidatedAdapterImplementationClosureV1:
    closure = parse_adapter_implementation_closure(closure_bytes)
    dependency_lock = _snapshot_dependency_lock(dependency_lock_bytes)
    if (
        hashlib.sha256(dependency_lock).hexdigest()
        != closure.dependency_lock_sha256
    ):
        _fail(ImplementationClosureCode.DEPENDENCY_LOCK)
    if (
        type(source_archive_inventory_bytes) is not bytes
        or type(source_archive_bytes) is not bytes
    ):
        _fail(ImplementationClosureCode.INPUT_TYPE)
    if (
        hashlib.sha256(source_archive_inventory_bytes).hexdigest()
        != closure.source_archive_inventory_sha256
        or hashlib.sha256(source_archive_bytes).hexdigest()
        != closure.source_archive_sha256
    ):
        _fail(ImplementationClosureCode.ARCHIVE)
    try:
        source_archive = _archive.validate_source_archive(
            source_archive_inventory_bytes,
            source_archive_bytes,
        )
    except (_archive.SourceArchiveValidationError, TypeError, ValueError):
        _fail(ImplementationClosureCode.ARCHIVE)
    try:
        expected_objects = _expected_archive_objects(closure.modules)
        expected_members = _expected_archive_members(closure.modules)
    except (TypeError, ValueError):
        _fail(ImplementationClosureCode.ARCHIVE_MEMBERSHIP)
    if (
        source_archive.inventory.source_objects != expected_objects
        or source_archive.inventory.members != expected_members
        or sum(
            item.occurrence_count
            for item in source_archive.inventory.members
        )
        != len(closure.modules)
    ):
        _fail(ImplementationClosureCode.ARCHIVE_MEMBERSHIP)
    by_identity = _source_bytes_by_identity(source_archive)
    module_names = frozenset(item.module_name for item in closure.modules)
    trees = {}
    validated_modules = []
    for item in closure.modules:
        source_bytes = by_identity.get(
            (item.source_sha256, item.source_byte_count)
        )
        if (
            type(source_bytes) is not bytes
            or len(source_bytes) != item.source_byte_count
            or hashlib.sha256(source_bytes).hexdigest() != item.source_sha256
        ):
            _fail(ImplementationClosureCode.ARCHIVE_MEMBERSHIP)
        tree, imported = _module_imports(
            item,
            source_bytes,
            module_names=module_names,
            protected_roots=closure.protected_namespace_roots,
            external_roots=closure.external_import_roots,
        )
        trees[item.module_name] = tree
        validated_modules.append(
            ValidatedImplementationClosureModuleV1(
                module=item,
                source_bytes=source_bytes,
                imported_module_names=imported,
            )
        )
    modules = tuple(validated_modules)
    _validate_entry_points(closure, trees)
    graph_sha256 = _import_graph_sha256(modules)
    import_edges = sum(len(item.imported_module_names) for item in modules)
    closure_file_sha256 = hashlib.sha256(closure_bytes).hexdigest()
    closure_sha256 = adapter_implementation_closure_sha256(closure_bytes)
    receipt = ImplementationClosureValidationReceiptV1(
        adapter_id=closure.adapter_id,
        adapter_version=closure.adapter_version,
        closure_byte_count=len(closure_bytes),
        closure_file_sha256=closure_file_sha256,
        closure_sha256=closure_sha256,
        dependency_lock_sha256=closure.dependency_lock_sha256,
        entry_point_module_name=closure.entry_point.module_name,
        entry_point_callable_name=closure.entry_point.callable_name,
        runtime_entry_point_module_name=(
            closure.runtime_entry_point.module_name
        ),
        runtime_entry_point_callable_name=(
            closure.runtime_entry_point.callable_name
        ),
        module_count=len(modules),
        observed_import_edge_count=import_edges,
        observed_import_graph_sha256=graph_sha256,
        source_archive_inventory_sha256=(
            closure.source_archive_inventory_sha256
        ),
        source_archive_sha256=closure.source_archive_sha256,
        canonical_closure_validated=True,
        exact_archive_membership_validated=True,
        package_parent_closure_validated=True,
        protected_import_closure_validated=True,
        external_import_roots_validated=True,
        recognized_dynamic_import_primitives_rejected=True,
        entry_point_zero_argument_mode_validated=True,
        source_loaded=False,
        runtime_entry_point_executed=False,
        adapter_constructed=False,
        adapter_executed=False,
        runtime_host_fallback_denial_enforced=False,
        execution_attested=False,
        containment_enforced=False,
        containment_attested=False,
        expected_material_nonexposure_attested=False,
        semantic_truth_attested=False,
        decision_made=False,
    )
    receipt_bytes = implementation_closure_validation_receipt_bytes(receipt)
    return ValidatedAdapterImplementationClosureV1(
        closure=closure,
        closure_bytes=closure_bytes,
        closure_file_sha256=closure_file_sha256,
        closure_sha256=closure_sha256,
        source_archive=source_archive,
        dependency_lock_bytes=dependency_lock,
        modules=modules,
        receipt=receipt,
        receipt_bytes=receipt_bytes,
        receipt_sha256=implementation_closure_validation_receipt_sha256(
            receipt
        ),
    )


def validate_adapter_implementation_closure(
    closure_bytes: bytes,
    *,
    source_archive_inventory_bytes: bytes,
    source_archive_bytes: bytes,
    dependency_lock_bytes: bytes,
) -> ValidatedAdapterImplementationClosureV1:
    """Validate exact closure, archive, dependency lock, and source imports."""

    try:
        return _validate_adapter_implementation_closure(
            closure_bytes,
            source_archive_inventory_bytes=source_archive_inventory_bytes,
            source_archive_bytes=source_archive_bytes,
            dependency_lock_bytes=dependency_lock_bytes,
        )
    except ImplementationClosureError:
        raise
    except Exception:
        _fail(ImplementationClosureCode.INTERNAL)


def build_adapter_implementation_closure(
    *,
    adapter_id: str,
    adapter_version: str,
    entry_point: AdapterImplementationEntryPointV1,
    runtime_entry_point: AdapterImplementationRuntimeEntryPointV1,
    modules: Tuple[ImplementationClosureModuleInputV1, ...],
    protected_namespace_roots: Tuple[str, ...],
    external_import_roots: Tuple[str, ...],
    source_archive_inventory_bytes: bytes,
    source_archive_bytes: bytes,
    dependency_lock_bytes: bytes,
) -> ValidatedAdapterImplementationClosureV1:
    """Build canonical closure bytes, then rerun the complete raw validator."""

    if type(modules) is not tuple or not modules:
        _fail(ImplementationClosureCode.INPUT_TYPE)
    if len(modules) > MAXIMUM_IMPLEMENTATION_MODULES:
        _fail(ImplementationClosureCode.RESOURCE)
    try:
        snapshots = []
        for item in modules:
            if type(item) is not ImplementationClosureModuleInputV1:
                _fail(ImplementationClosureCode.INPUT_TYPE)
            ImplementationClosureModuleInputV1.__post_init__(item)
            snapshots.append(
                ImplementationClosureModuleInputV1(
                    module_name=item.module_name,
                    is_package=item.is_package,
                    role_id=item.role_id,
                    source_object_id=item.source_object_id,
                    source_bytes=item.source_bytes,
                )
            )
        ordered = tuple(sorted(snapshots, key=lambda item: item.module_name))
        module_records = tuple(
            ImplementationClosureModuleV1(
                module_name=item.module_name,
                is_package=item.is_package,
                role_id=item.role_id,
                source_byte_count=len(item.source_bytes),
                source_object_id=item.source_object_id,
                source_sha256=hashlib.sha256(item.source_bytes).hexdigest(),
            )
            for item in ordered
        )
        dependency_lock = _snapshot_dependency_lock(dependency_lock_bytes)
        if (
            type(source_archive_inventory_bytes) is not bytes
            or type(source_archive_bytes) is not bytes
        ):
            _fail(ImplementationClosureCode.INPUT_TYPE)
        closure = AdapterImplementationClosureV1(
            adapter_id=adapter_id,
            adapter_version=adapter_version,
            dependency_lock_sha256=hashlib.sha256(
                dependency_lock
            ).hexdigest(),
            entry_point=entry_point,
            external_import_roots=external_import_roots,
            modules=module_records,
            protected_namespace_roots=protected_namespace_roots,
            runtime_entry_point=runtime_entry_point,
            source_archive_inventory_sha256=hashlib.sha256(
                source_archive_inventory_bytes
            ).hexdigest(),
            source_archive_sha256=hashlib.sha256(
                source_archive_bytes
            ).hexdigest(),
        )
        closure_bytes = adapter_implementation_closure_bytes(closure)
    except ImplementationClosureError:
        raise
    except _NamePolicyViolation:
        _fail(ImplementationClosureCode.NAME_POLICY)
    except _PackageClosureViolation:
        _fail(ImplementationClosureCode.PACKAGE_CLOSURE)
    except _EntryPointViolation:
        _fail(ImplementationClosureCode.ENTRY_POINT)
    except (AttributeError, TypeError, ValueError):
        _fail(ImplementationClosureCode.SCHEMA)
    return validate_adapter_implementation_closure(
        closure_bytes,
        source_archive_inventory_bytes=source_archive_inventory_bytes,
        source_archive_bytes=source_archive_bytes,
        dependency_lock_bytes=dependency_lock,
    )


def validate_implementation_closure_validation_receipt(
    value: object,
) -> ImplementationClosureValidationReceiptV1:
    """Return a fresh recursively validated receipt snapshot."""

    if type(value) is not ImplementationClosureValidationReceiptV1:
        _fail(ImplementationClosureCode.RECEIPT)
    try:
        fields = {
            name: getattr(value, name)
            for name in ImplementationClosureValidationReceiptV1.__dataclass_fields__
            if ImplementationClosureValidationReceiptV1.__dataclass_fields__[
                name
            ].init
        }
        result = ImplementationClosureValidationReceiptV1(**fields)
        if implementation_closure_validation_receipt_bytes(result) != (
            implementation_closure_validation_receipt_bytes(value)
        ):
            _fail(ImplementationClosureCode.RECEIPT)
        return result
    except ImplementationClosureError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(ImplementationClosureCode.RECEIPT)


__all__ = [
    "IMPLEMENTATION_CLOSURE_ALLOWED_ROLE_IDS",
    "IMPLEMENTATION_CLOSURE_ARTIFACT_TYPE",
    "IMPLEMENTATION_CLOSURE_BANNED_NAME_TOKENS",
    "IMPLEMENTATION_CLOSURE_CONSTRUCTION_MODE_ID",
    "IMPLEMENTATION_CLOSURE_DECISION_STATUS_ID",
    "IMPLEMENTATION_CLOSURE_DIGEST_DOMAIN",
    "IMPLEMENTATION_CLOSURE_RECEIPT_ARTIFACT_TYPE",
    "IMPLEMENTATION_CLOSURE_VALIDATION_STATUS_ID",
    "MAXIMUM_IMPLEMENTATION_CLOSURE_BYTES",
    "MAXIMUM_IMPLEMENTATION_CLOSURE_RECEIPT_BYTES",
    "MAXIMUM_IMPLEMENTATION_DEPENDENCY_LOCK_BYTES",
    "MAXIMUM_IMPLEMENTATION_MODULES",
    "AdapterImplementationClosureV1",
    "AdapterImplementationEntryPointV1",
    "AdapterImplementationRuntimeEntryPointV1",
    "ImplementationClosureCode",
    "ImplementationClosureError",
    "ImplementationClosureModuleInputV1",
    "ImplementationClosureModuleV1",
    "ImplementationClosureValidationReceiptV1",
    "ValidatedAdapterImplementationClosureV1",
    "ValidatedImplementationClosureModuleV1",
    "adapter_implementation_closure_bytes",
    "adapter_implementation_closure_sha256",
    "adapter_implementation_closure_tree",
    "build_adapter_implementation_closure",
    "implementation_closure_validation_receipt_bytes",
    "implementation_closure_validation_receipt_sha256",
    "implementation_closure_validation_receipt_tree",
    "parse_adapter_implementation_closure",
    "parse_implementation_closure_validation_receipt",
    "validate_adapter_implementation_closure",
    "validate_implementation_closure_validation_receipt",
]
