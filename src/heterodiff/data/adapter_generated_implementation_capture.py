"""Capture source-bound closure artifacts for the five generated cases.

This filesystem-reading helper is deliberately outside the child and outside
the generic closure validator.  It captures a frozen set of repository source
modules into the path-free archive format and then invokes the same raw-byte
closure validator used by the supervisor.  Execution consumes only its
returned immutable bytes, never these source paths.

The generated adapters span continuous-time, symbolic, clinical-style, and
transaction fixtures.  They are development demonstrations of the generic
boundary, not official-dataset results or evidence of generalization.
"""

from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path
import stat
from types import MappingProxyType
from typing import Dict, NamedTuple, Tuple

from .adapter_implementation_closure import (
    AdapterImplementationEntryPointV1,
    AdapterImplementationRuntimeEntryPointV1,
    ImplementationClosureModuleInputV1,
    ValidatedAdapterImplementationClosureV1,
    build_adapter_implementation_closure,
)
from .adapter_output_blind_trusted_runtime_profile import (
    OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES,
)
from .adapter_source_archive import (
    MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES,
    SourceArchiveObjectV1,
    build_source_archive,
    build_source_archive_inventory,
    source_archive_inventory_bytes,
)

_SOURCE_READ_CHUNK_BYTES = 64 * 1024


GENERATED_IMPLEMENTATION_RUNTIME_MODULE = (
    "heterodiff.data.adapter_output_blind_child_runtime"
)
GENERATED_IMPLEMENTATION_RUNTIME_CALLABLE = (
    "run_output_blind_adapter_case"
)
GENERATED_IMPLEMENTATION_ENTRYPOINT_MODULE = (
    "heterodiff.data.adapter_generated_child_entrypoints"
)
GENERATED_IMPLEMENTATION_ADAPTER_VERSION = "1"

_ENTRYPOINTS = MappingProxyType(
    {
        "generated.native.family-a": "build_generated_h_adapter",
        "generated.native.family-b": "build_generated_m_adapter",
        "generated.native.family-c": "build_generated_p_adapter",
        "generated.native.family-d": "build_generated_r_adapter",
    }
)

# Package parents that must not execute the broad installed package
# initializers.  Their exact empty bytes are explicit closure members.
_SYNTHETIC_PACKAGE_MODULES = (
    "heterodiff",
    "heterodiff.artifacts",
    "heterodiff.data",
)

_SOURCE_MODULE_PATHS = MappingProxyType(
    {
        "heterodiff.artifacts.manifest": (
            "heterodiff/artifacts/manifest.py"
        ),
        "heterodiff.data.adapter_child_bundle_codec": (
            "heterodiff/data/adapter_child_bundle_codec.py"
        ),
        "heterodiff.data.adapter_contract": (
            "heterodiff/data/adapter_contract.py"
        ),
        "heterodiff.data.adapter_evidence": (
            "heterodiff/data/adapter_evidence.py"
        ),
        "heterodiff.data.adapter_generated_child_entrypoints": (
            "heterodiff/data/adapter_generated_child_entrypoints.py"
        ),
        "heterodiff.data.adapter_output_blind_case_input": (
            "heterodiff/data/adapter_output_blind_case_input.py"
        ),
        "heterodiff.data.adapter_output_blind_child_runtime": (
            "heterodiff/data/adapter_output_blind_child_runtime.py"
        ),
        "heterodiff.data.atomic_counting_grid": (
            "heterodiff/data/atomic_counting_grid.py"
        ),
        "heterodiff.data.cross_domain_counting_fixtures": (
            "heterodiff/data/cross_domain_counting_fixtures.py"
        ),
        "heterodiff.data.generated_conformance_adapters": (
            "heterodiff/data/generated_conformance_adapters.py"
        ),
        "heterodiff.data.generated_hawkes_fixture": (
            "heterodiff/data/generated_hawkes_fixture.py"
        ),
        "heterodiff.data.generated_transaction_fixture": (
            "heterodiff/data/generated_transaction_fixture.py"
        ),
        "heterodiff.data.maestro_inventory": (
            "heterodiff/data/maestro_inventory.py"
        ),
        "heterodiff.data.maestro_semantics": (
            "heterodiff/data/maestro_semantics.py"
        ),
        "heterodiff.data.midi_raw": "heterodiff/data/midi_raw.py",
        "heterodiff.data.physionet_2012_adapter": (
            "heterodiff/data/physionet_2012_adapter.py"
        ),
        "heterodiff.data.physionet_2012_raw": (
            "heterodiff/data/physionet_2012_raw.py"
        ),
        "heterodiff.data.synthetic_typed_hawkes": (
            "heterodiff/data/synthetic_typed_hawkes.py"
        ),
        "heterodiff.events": "heterodiff/events/__init__.py",
        "heterodiff.events.configuration": (
            "heterodiff/events/configuration.py"
        ),
        "heterodiff.events.observations": (
            "heterodiff/events/observations.py"
        ),
        "heterodiff.events.schema": "heterodiff/events/schema.py",
        "heterodiff.events.transforms": (
            "heterodiff/events/transforms.py"
        ),
    }
)


class GeneratedImplementationCaptureError(ValueError):
    """A repository source capture violates the frozen development profile."""


class CapturedGeneratedAdapterImplementationV1(NamedTuple):
    """Raw artifacts ready for one or more child-runner invocations."""

    validated_closure: ValidatedAdapterImplementationClosureV1
    implementation_closure_bytes: bytes
    source_archive_inventory_bytes: bytes
    source_archive_bytes: bytes
    dependency_lock_bytes: bytes
    module_names: Tuple[str, ...]


def _module_role(module_name: str) -> str:
    if module_name in (
        GENERATED_IMPLEMENTATION_ENTRYPOINT_MODULE,
        "heterodiff.data.generated_conformance_adapters",
    ):
        return "adapter-source"
    if module_name in (
        "heterodiff.data.adapter_child_bundle_codec",
        "heterodiff.data.adapter_contract",
        "heterodiff.data.adapter_evidence",
        "heterodiff.data.adapter_output_blind_case_input",
        GENERATED_IMPLEMENTATION_RUNTIME_MODULE,
        "heterodiff.events",
        "heterodiff.events.configuration",
        "heterodiff.events.observations",
        "heterodiff.events.schema",
        "heterodiff.events.transforms",
    ):
        return "contract-source"
    return "support-source"


def _stat_identity(status: os.stat_result) -> tuple:
    return (status.st_dev, status.st_ino)


def _stable_stat_key(status: os.stat_result) -> tuple:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        stat.S_IMODE(status.st_mode),
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _descriptor_open_flags(*, directory: bool) -> int:
    required = ("O_CLOEXEC", "O_NOFOLLOW")
    if directory:
        required += ("O_DIRECTORY",)
    if any(not hasattr(os, name) for name in required):
        raise GeneratedImplementationCaptureError(
            "generated implementation source capture failed"
        )
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    elif hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    return flags


def _relative_components(relative_path: str) -> Tuple[str, ...]:
    if type(relative_path) is not str or not relative_path:
        raise GeneratedImplementationCaptureError(
            "generated implementation source escaped its root"
        )
    components = tuple(relative_path.split("/"))
    if (
        relative_path.startswith("/")
        or any(item in ("", ".", "..") for item in components)
        or "/".join(components) != relative_path
    ):
        raise GeneratedImplementationCaptureError(
            "generated implementation source escaped its root"
        )
    return components


def _lstat_at(directory_fd: int, name: str) -> os.stat_result:
    return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)


def _read_bounded_descriptor(
    source_fd: int,
    *,
    expected_size: int,
) -> bytes:
    if (
        type(expected_size) is not int
        or expected_size <= 0
        or expected_size > MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES
    ):
        raise GeneratedImplementationCaptureError(
            "generated implementation source bytes are invalid"
        )
    remaining = expected_size
    chunks = []
    while remaining:
        chunk = os.read(
            source_fd,
            min(remaining, _SOURCE_READ_CHUNK_BYTES),
        )
        if type(chunk) is not bytes or not chunk or len(chunk) > remaining:
            raise GeneratedImplementationCaptureError(
                "generated implementation source bytes are invalid"
            )
        chunks.append(chunk)
        remaining -= len(chunk)
    if os.read(source_fd, 1):
        raise GeneratedImplementationCaptureError(
            "generated implementation source bytes are invalid"
        )
    raw = b"".join(chunks)
    if len(raw) != expected_size:
        raise GeneratedImplementationCaptureError(
            "generated implementation source bytes are invalid"
        )
    return raw


def _read_exact_source(source_root_fd: int, relative_path: str) -> bytes:
    if type(source_root_fd) is not int or source_root_fd < 0:
        raise TypeError("source_root_fd must be a nonnegative exact integer")
    components = _relative_components(relative_path)
    opened_directory_fds = []
    source_fd = None
    edges = []
    try:
        parent_fd = source_root_fd
        for component in components[:-1]:
            lexical_status = _lstat_at(parent_fd, component)
            if stat.S_ISLNK(lexical_status.st_mode):
                raise GeneratedImplementationCaptureError(
                    "generated implementation source must not be a symlink"
                )
            if not stat.S_ISDIR(lexical_status.st_mode):
                raise GeneratedImplementationCaptureError(
                    "generated implementation source capture failed"
                )
            directory_fd = os.open(
                component,
                _descriptor_open_flags(directory=True),
                dir_fd=parent_fd,
            )
            descriptor_status = os.fstat(directory_fd)
            if (
                not stat.S_ISDIR(descriptor_status.st_mode)
                or _stable_stat_key(descriptor_status)
                != _stable_stat_key(lexical_status)
            ):
                os.close(directory_fd)
                raise GeneratedImplementationCaptureError(
                    "generated implementation source capture failed"
                )
            edges.append((parent_fd, component, lexical_status))
            opened_directory_fds.append(directory_fd)
            parent_fd = directory_fd

        leaf_name = components[-1]
        lexical_status = _lstat_at(parent_fd, leaf_name)
        if stat.S_ISLNK(lexical_status.st_mode):
            raise GeneratedImplementationCaptureError(
                "generated implementation source must not be a symlink"
            )
        if not stat.S_ISREG(lexical_status.st_mode):
            raise GeneratedImplementationCaptureError(
                "generated implementation source is not a regular file"
            )
        if (
            lexical_status.st_size <= 0
            or lexical_status.st_size
            > MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES
        ):
            raise GeneratedImplementationCaptureError(
                "generated implementation source bytes are invalid"
            )
        source_fd = os.open(
            leaf_name,
            _descriptor_open_flags(directory=False),
            dir_fd=parent_fd,
        )
        descriptor_status = os.fstat(source_fd)
        if (
            not stat.S_ISREG(descriptor_status.st_mode)
            or _stable_stat_key(descriptor_status)
            != _stable_stat_key(lexical_status)
        ):
            raise GeneratedImplementationCaptureError(
                "generated implementation source capture failed"
            )
        edges.append((parent_fd, leaf_name, lexical_status))
        raw = _read_bounded_descriptor(
            source_fd,
            expected_size=descriptor_status.st_size,
        )
        final_descriptor_status = os.fstat(source_fd)
        if (
            _stable_stat_key(final_descriptor_status)
            != _stable_stat_key(descriptor_status)
        ):
            raise GeneratedImplementationCaptureError(
                "generated implementation source capture failed"
            )
        for directory_fd, name, expected_status in edges:
            current_status = _lstat_at(directory_fd, name)
            if (
                _stable_stat_key(current_status)
                != _stable_stat_key(expected_status)
            ):
                raise GeneratedImplementationCaptureError(
                    "generated implementation source capture failed"
                )
    except GeneratedImplementationCaptureError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise GeneratedImplementationCaptureError(
            "generated implementation source capture failed"
        ) from error
    finally:
        if source_fd is not None:
            try:
                os.close(source_fd)
            except OSError:
                pass
        for directory_fd in reversed(opened_directory_fds):
            try:
                os.close(directory_fd)
            except OSError:
                pass
    if (
        not raw
        or len(raw) != descriptor_status.st_size
        or b"\x00" in raw
        or b"\r" in raw
    ):
        raise GeneratedImplementationCaptureError(
            "generated implementation source bytes are invalid"
        )
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError as error:
        raise GeneratedImplementationCaptureError(
            "generated implementation source is not exact UTF-8"
        ) from error
    if text.encode("utf-8", "strict") != raw:
        raise GeneratedImplementationCaptureError(
            "generated implementation source UTF-8 does not round-trip"
        )
    return raw


def _capture_sources(source_root_fd: int) -> Dict[str, bytes]:
    result = {
        name: b"" for name in _SYNTHETIC_PACKAGE_MODULES
    }
    for module_name, relative_path in _SOURCE_MODULE_PATHS.items():
        result[module_name] = _read_exact_source(
            source_root_fd,
            relative_path,
        )
    return result


def _validate_trusted_runtime_capture_sources(
    sources: Dict[str, bytes],
) -> None:
    for expected in OUTPUT_BLIND_TRUSTED_RUNTIME_SOURCE_MODULES:
        source = sources.get(expected.module_name)
        is_package = (
            expected.module_name in _SYNTHETIC_PACKAGE_MODULES
            or expected.module_name == "heterodiff.events"
        )
        if (
            type(source) is not bytes
            or is_package is not expected.is_package
            or _module_role(expected.module_name) != expected.role_id
            or expected.source_object_id
            != "module:" + expected.module_name
            or len(source) != expected.source_byte_count
            or hashlib.sha256(source).hexdigest()
            != expected.source_sha256
        ):
            raise GeneratedImplementationCaptureError(
                "generated implementation trusted runtime source profile "
                "differs"
            )


def _external_import_roots(
    sources: Dict[str, bytes],
) -> Tuple[str, ...]:
    roots = set()
    try:
        for source in sources.values():
            if not source:
                continue
            tree = ast.parse(
                source.decode("utf-8", "strict"),
                filename="<generated-implementation-capture>",
                mode="exec",
                type_comments=False,
                feature_version=9,
            )
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    roots.update(
                        alias.name.split(".", 1)[0]
                        for alias in node.names
                    )
                elif (
                    isinstance(node, ast.ImportFrom)
                    and node.level == 0
                    and node.module not in (None, "__future__")
                ):
                    roots.add(node.module.split(".", 1)[0])
    except (SyntaxError, TypeError, UnicodeError, ValueError) as error:
        raise GeneratedImplementationCaptureError(
            "generated implementation imports could not be captured"
        ) from error
    roots.discard("heterodiff")
    return tuple(sorted(roots))


def _module_inputs(
    sources: Dict[str, bytes],
) -> Tuple[ImplementationClosureModuleInputV1, ...]:
    return tuple(
        ImplementationClosureModuleInputV1(
            module_name=name,
            is_package=(
                name in _SYNTHETIC_PACKAGE_MODULES
                or name == "heterodiff.events"
            ),
            role_id=_module_role(name),
            source_object_id="module:" + name,
            source_bytes=sources[name],
        )
        for name in sorted(sources)
    )


def _archive_objects(
    modules: Tuple[ImplementationClosureModuleInputV1, ...],
) -> Tuple[SourceArchiveObjectV1, ...]:
    values = tuple(
        SourceArchiveObjectV1(
            role_id=item.role_id,
            source_byte_count=len(item.source_bytes),
            source_object_id=item.source_object_id,
            source_sha256=hashlib.sha256(item.source_bytes).hexdigest(),
        )
        for item in modules
    )
    return tuple(
        sorted(values, key=lambda item: (item.role_id, item.source_object_id))
    )


def capture_generated_adapter_implementation(
    *,
    adapter_id: str,
    source_root: Path,
    dependency_lock_bytes: bytes,
) -> CapturedGeneratedAdapterImplementationV1:
    """Capture one adapter factory and its shared exact source closure."""

    if type(adapter_id) is not str or adapter_id not in _ENTRYPOINTS:
        raise GeneratedImplementationCaptureError(
            "generated adapter identifier is not supported"
        )
    if not isinstance(source_root, Path):
        raise TypeError("source_root must be a pathlib.Path")
    if (
        type(dependency_lock_bytes) is not bytes
        or not dependency_lock_bytes
    ):
        raise TypeError("dependency_lock_bytes must be nonempty exact bytes")
    try:
        root = source_root.resolve(strict=True)
        lexical_root_status = os.stat(str(root), follow_symlinks=False)
    except (OSError, RuntimeError) as error:
        raise GeneratedImplementationCaptureError(
            "generated source root is invalid"
        ) from error
    if not stat.S_ISDIR(lexical_root_status.st_mode):
        raise GeneratedImplementationCaptureError(
            "generated source root is not a directory"
        )
    root_fd = None
    try:
        root_fd = os.open(
            str(root),
            _descriptor_open_flags(directory=True),
        )
        descriptor_root_status = os.fstat(root_fd)
        if (
            not stat.S_ISDIR(descriptor_root_status.st_mode)
            or _stable_stat_key(descriptor_root_status)
            != _stable_stat_key(lexical_root_status)
        ):
            raise GeneratedImplementationCaptureError(
                "generated source root is invalid"
            )
        sources = _capture_sources(root_fd)
        _validate_trusted_runtime_capture_sources(sources)
        final_descriptor_root_status = os.fstat(root_fd)
        final_lexical_root_status = os.stat(
            str(root),
            follow_symlinks=False,
        )
        if (
            _stable_stat_key(final_descriptor_root_status)
            != _stable_stat_key(descriptor_root_status)
            or _stat_identity(final_lexical_root_status)
            != _stat_identity(descriptor_root_status)
        ):
            raise GeneratedImplementationCaptureError(
                "generated source root is invalid"
            )
    except GeneratedImplementationCaptureError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise GeneratedImplementationCaptureError(
            "generated source root is invalid"
        ) from error
    finally:
        if root_fd is not None:
            try:
                os.close(root_fd)
            except OSError:
                pass
    modules = _module_inputs(sources)
    source_members = tuple(item.source_bytes for item in modules)
    try:
        archive_bytes = build_source_archive(source_members)
        inventory = build_source_archive_inventory(
            archive_bytes,
            source_members,
            _archive_objects(modules),
        )
        inventory_bytes = source_archive_inventory_bytes(inventory)
        validated = build_adapter_implementation_closure(
            adapter_id=adapter_id,
            adapter_version=GENERATED_IMPLEMENTATION_ADAPTER_VERSION,
            entry_point=AdapterImplementationEntryPointV1(
                module_name=GENERATED_IMPLEMENTATION_ENTRYPOINT_MODULE,
                callable_name=_ENTRYPOINTS[adapter_id],
            ),
            runtime_entry_point=(
                AdapterImplementationRuntimeEntryPointV1(
                    module_name=GENERATED_IMPLEMENTATION_RUNTIME_MODULE,
                    callable_name=(
                        GENERATED_IMPLEMENTATION_RUNTIME_CALLABLE
                    ),
                )
            ),
            modules=modules,
            protected_namespace_roots=("heterodiff",),
            external_import_roots=_external_import_roots(sources),
            source_archive_inventory_bytes=inventory_bytes,
            source_archive_bytes=archive_bytes,
            dependency_lock_bytes=dependency_lock_bytes,
        )
    except Exception as error:
        raise GeneratedImplementationCaptureError(
            "generated implementation closure construction failed"
        ) from error
    return CapturedGeneratedAdapterImplementationV1(
        validated_closure=validated,
        implementation_closure_bytes=validated.closure_bytes,
        source_archive_inventory_bytes=inventory_bytes,
        source_archive_bytes=archive_bytes,
        dependency_lock_bytes=bytes(dependency_lock_bytes),
        module_names=tuple(item.module_name for item in modules),
    )


__all__ = [
    "CapturedGeneratedAdapterImplementationV1",
    "GENERATED_IMPLEMENTATION_ADAPTER_VERSION",
    "GENERATED_IMPLEMENTATION_ENTRYPOINT_MODULE",
    "GENERATED_IMPLEMENTATION_RUNTIME_CALLABLE",
    "GENERATED_IMPLEMENTATION_RUNTIME_MODULE",
    "GeneratedImplementationCaptureError",
    "capture_generated_adapter_implementation",
]
