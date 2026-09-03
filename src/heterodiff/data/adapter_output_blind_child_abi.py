"""Bounded binary ABI for one output-blind adapter development child.

This module defines transport only.  It performs no process launch, source
archive validation, module loading, adapter call, expected-value comparison,
containment, attestation, publication, or decision.  The request carries one
already canonical five-field pre-output case document.  Success and failure
responses carry only closed audit fields; no exception text is serialized.

The ABI is deliberately not re-exported from :mod:`heterodiff.data`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import re
from types import MappingProxyType
from typing import NamedTuple, Tuple

from .adapter_output_blind_case_input import (
    MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES,
    output_blind_case_input_v1_sha256,
    parse_output_blind_case_input_v1,
)


OUTPUT_BLIND_ADAPTER_CHILD_REQUEST_DOMAIN = (
    "heterodiff.adapter.output-blind-adapter-child-request.v1"
)
OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_MODULE_DOMAIN = (
    "heterodiff.adapter.output-blind-adapter-child-source-module.v1"
)
OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_DOMAIN = (
    "heterodiff.adapter.output-blind-adapter-child-source-load-report.v1"
)
OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_DOMAIN = (
    "heterodiff.adapter.output-blind-adapter-child-success-response.v1"
)
OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_DOMAIN = (
    "heterodiff.adapter.output-blind-adapter-child-failure-response.v1"
)

OUTPUT_BLIND_ADAPTER_CHILD_REQUEST_FIELD_NAMES = ("case_input_bytes",)
OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_MODULE_FIELD_NAMES = (
    "module_name",
    "source_object_id",
    "source_byte_count",
    "source_sha256",
)
OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_FIELD_NAMES = (
    "implementation_closure_sha256",
    "entrypoint_module_name",
    "entrypoint_callable_name",
    "loaded_project_modules",
    "protected_namespace_host_fallback_count",
)
OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_FIELD_NAMES = (
    "request_frame_sha256",
    "case_input_sha256",
    "implementation_closure_sha256",
    "adapter_id",
    "adapter_version",
    "runner_direct_adapt_complete_call_count",
    "runner_direct_adapt_call_count",
    "source_load_report_bytes",
    "adapted_evidence_bundle_bytes",
)
OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_FIELD_NAMES = (
    "request_frame_sha256",
    "case_input_sha256",
    "implementation_closure_sha256",
    "failure_code",
)

MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_REQUEST_FRAME_BYTES = (
    MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES + 1024
)
MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_BYTES = 1024 * 1024
MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_BYTES = 2 * 1024 * 1024
MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_BYTES = 64 * 1024
MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_LOADED_PROJECT_MODULES = 4096
MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_MODULE_NAME_BYTES = 256
MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_OBJECT_ID_BYTES = 128
MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_ENTRYPOINT_NAME_BYTES = 128
MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_ADAPTER_ID_BYTES = 128
MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_ADAPTER_VERSION_BYTES = 10
MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_BYTES = 8 * 1024 * 1024

_MAXIMUM_U64 = (1 << 64) - 1
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MODULE_NAME_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$"
)
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_PUBLIC_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_ADAPTER_VERSION_RE = re.compile(r"^[1-9][0-9]{0,9}$")
_PROTECTED_PROJECT_MODULE_ROOT = "heterodiff"


class OutputBlindAdapterChildABICode(str, Enum):
    """Closed, nonreflecting transport failure categories."""

    INPUT_TYPE = "OUTPUT_BLIND_ADAPTER_CHILD_INPUT_TYPE"
    INPUT_RESOURCE = "OUTPUT_BLIND_ADAPTER_CHILD_INPUT_RESOURCE"
    FRAME_FORMAT = "OUTPUT_BLIND_ADAPTER_CHILD_FRAME_FORMAT"
    FRAME_DOMAIN = "OUTPUT_BLIND_ADAPTER_CHILD_FRAME_DOMAIN"
    FRAME_FIELD = "OUTPUT_BLIND_ADAPTER_CHILD_FRAME_FIELD"
    FRAME_VALUE = "OUTPUT_BLIND_ADAPTER_CHILD_FRAME_VALUE"
    CASE_INPUT_INVALID = "OUTPUT_BLIND_ADAPTER_CHILD_CASE_INPUT_INVALID"
    SOURCE_LOAD_REPORT_INVALID = (
        "OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_INVALID"
    )
    RESPONSE_BINDING = "OUTPUT_BLIND_ADAPTER_CHILD_RESPONSE_BINDING"
    INTERNAL = "OUTPUT_BLIND_ADAPTER_CHILD_INTERNAL"


_ERROR_MESSAGES = MappingProxyType(
    {
        OutputBlindAdapterChildABICode.INPUT_TYPE: (
            "output-blind adapter child ABI input has an invalid exact type"
        ),
        OutputBlindAdapterChildABICode.INPUT_RESOURCE: (
            "output-blind adapter child ABI input exceeds a resource ceiling"
        ),
        OutputBlindAdapterChildABICode.FRAME_FORMAT: (
            "output-blind adapter child frame has an invalid binary format"
        ),
        OutputBlindAdapterChildABICode.FRAME_DOMAIN: (
            "output-blind adapter child frame has an invalid domain"
        ),
        OutputBlindAdapterChildABICode.FRAME_FIELD: (
            "output-blind adapter child frame has an invalid field sequence"
        ),
        OutputBlindAdapterChildABICode.FRAME_VALUE: (
            "output-blind adapter child frame has an invalid field value"
        ),
        OutputBlindAdapterChildABICode.CASE_INPUT_INVALID: (
            "output-blind adapter child request case input is invalid"
        ),
        OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID: (
            "output-blind adapter child source-load report is invalid"
        ),
        OutputBlindAdapterChildABICode.RESPONSE_BINDING: (
            "output-blind adapter child response identities do not match"
        ),
        OutputBlindAdapterChildABICode.INTERNAL: (
            "output-blind adapter child ABI processing failed internally"
        ),
    }
)


class OutputBlindAdapterChildABIError(ValueError):
    """One fixed-message ABI error that never reflects untrusted input."""

    def __init__(self, code: OutputBlindAdapterChildABICode) -> None:
        if type(code) is not OutputBlindAdapterChildABICode:
            raise TypeError("adapter child ABI code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class OutputBlindAdapterChildFailureCode(str, Enum):
    """Closed failure values that a child may serialize."""

    CLOSURE_INVALID = "CHILD_CLOSURE_INVALID"
    SOURCE_LOAD_FAILED = "CHILD_SOURCE_LOAD_FAILED"
    ENTRYPOINT_INVALID = "CHILD_ENTRYPOINT_INVALID"
    PROTOCOL_INVALID = "CHILD_PROTOCOL_INVALID"
    DESCRIPTOR_INVALID = "CHILD_DESCRIPTOR_INVALID"
    ADAPT_COMPLETE_FAILED = "CHILD_ADAPT_COMPLETE_FAILED"
    OUTPUT_INVALID = "CHILD_OUTPUT_INVALID"
    BUNDLE_BUILD_FAILED = "CHILD_BUNDLE_BUILD_FAILED"
    POSTMUTATION = "CHILD_POSTMUTATION"
    INTERNAL = "CHILD_INTERNAL"


def _fail(code: OutputBlindAdapterChildABICode) -> None:
    raise OutputBlindAdapterChildABIError(code) from None


def _exact_bytes(value: object, *, maximum: int, allow_empty: bool = False) -> bytes:
    if type(value) is not bytes:
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    if (not value and not allow_empty) or len(value) > maximum:
        _fail(OutputBlindAdapterChildABICode.INPUT_RESOURCE)
    return bytes(value)


def _sha256(value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(OutputBlindAdapterChildABICode.FRAME_VALUE)
    return value


def _bounded_ascii(
    value: object,
    *,
    maximum: int,
    pattern: re.Pattern,
) -> str:
    if type(value) is not str:
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        _fail(OutputBlindAdapterChildABICode.FRAME_VALUE)
    if (
        not encoded
        or len(encoded) > maximum
        or pattern.fullmatch(value) is None
    ):
        _fail(OutputBlindAdapterChildABICode.FRAME_VALUE)
    return value


def _bounded_u64(value: object, *, maximum: int = _MAXIMUM_U64) -> int:
    if type(value) is not int:
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    if value < 0 or value > maximum:
        _fail(OutputBlindAdapterChildABICode.FRAME_VALUE)
    return value


def _u64_bytes(value: int) -> bytes:
    return _bounded_u64(value).to_bytes(8, "big")


def _u64_value(value: bytes) -> int:
    if type(value) is not bytes or len(value) != 8:
        _fail(OutputBlindAdapterChildABICode.FRAME_VALUE)
    return int.from_bytes(value, "big")


def _ascii_value(
    value: bytes,
    *,
    maximum: int,
    pattern: re.Pattern,
) -> str:
    if type(value) is not bytes:
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    try:
        decoded = value.decode("ascii", "strict")
    except UnicodeError:
        _fail(OutputBlindAdapterChildABICode.FRAME_VALUE)
    return _bounded_ascii(decoded, maximum=maximum, pattern=pattern)


def _encoded_frame_size(domain: bytes, names: Tuple[bytes, ...], values: Tuple[bytes, ...]) -> int:
    size = len(domain) + 1 + 8
    for name, value in zip(names, values):
        size += 8 + len(name) + 8 + len(value)
    return size


def _build_frame(
    *,
    domain: str,
    field_names: Tuple[str, ...],
    values: Tuple[bytes, ...],
    maximum: int,
) -> bytes:
    if (
        type(domain) is not str
        or type(field_names) is not tuple
        or type(values) is not tuple
        or len(field_names) != len(values)
        or any(type(name) is not str for name in field_names)
        or any(type(value) is not bytes for value in values)
    ):
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    try:
        domain_bytes = domain.encode("ascii", "strict")
        names = tuple(name.encode("ascii", "strict") for name in field_names)
    except UnicodeError:
        _fail(OutputBlindAdapterChildABICode.INTERNAL)
    if (
        not domain_bytes
        or b"\x00" in domain_bytes
        or not names
        or len(set(names)) != len(names)
    ):
        _fail(OutputBlindAdapterChildABICode.INTERNAL)
    if _encoded_frame_size(domain_bytes, names, values) > maximum:
        _fail(OutputBlindAdapterChildABICode.INPUT_RESOURCE)
    parts = [domain_bytes, b"\x00", _u64_bytes(len(values))]
    for name, value in zip(names, values):
        parts.extend((_u64_bytes(len(name)), name, _u64_bytes(len(value)), value))
    frame = b"".join(parts)
    if not frame or len(frame) > maximum:
        _fail(OutputBlindAdapterChildABICode.INTERNAL)
    return frame


def _read_u64(frame: bytes, offset: int) -> Tuple[int, int]:
    if offset < 0 or offset + 8 > len(frame):
        _fail(OutputBlindAdapterChildABICode.FRAME_FORMAT)
    return int.from_bytes(frame[offset : offset + 8], "big"), offset + 8


def _parse_frame(
    frame: object,
    *,
    domain: str,
    field_names: Tuple[str, ...],
    maximum: int,
) -> Tuple[bytes, ...]:
    raw = _exact_bytes(frame, maximum=maximum)
    try:
        domain_bytes = domain.encode("ascii", "strict")
        expected_names = tuple(
            name.encode("ascii", "strict") for name in field_names
        )
    except UnicodeError:
        _fail(OutputBlindAdapterChildABICode.INTERNAL)
    prefix = domain_bytes + b"\x00"
    if not raw.startswith(prefix):
        _fail(OutputBlindAdapterChildABICode.FRAME_DOMAIN)
    offset = len(prefix)
    field_count, offset = _read_u64(raw, offset)
    if field_count != len(expected_names):
        _fail(OutputBlindAdapterChildABICode.FRAME_FIELD)
    values = []
    for expected_name in expected_names:
        name_count, offset = _read_u64(raw, offset)
        if name_count != len(expected_name) or offset + name_count > len(raw):
            _fail(OutputBlindAdapterChildABICode.FRAME_FIELD)
        name = raw[offset : offset + name_count]
        offset += name_count
        if name != expected_name:
            _fail(OutputBlindAdapterChildABICode.FRAME_FIELD)
        value_count, offset = _read_u64(raw, offset)
        if value_count > maximum or offset + value_count > len(raw):
            _fail(OutputBlindAdapterChildABICode.FRAME_FORMAT)
        values.append(raw[offset : offset + value_count])
        offset += value_count
    if offset != len(raw):
        _fail(OutputBlindAdapterChildABICode.FRAME_FORMAT)
    return tuple(values)


def _validated_case_input_bytes(value: object) -> bytes:
    raw = _exact_bytes(
        value,
        maximum=MAXIMUM_OUTPUT_BLIND_CASE_INPUT_BYTES,
    )
    try:
        parse_output_blind_case_input_v1(raw)
    except Exception:
        _fail(OutputBlindAdapterChildABICode.CASE_INPUT_INVALID)
    return raw


@dataclass(frozen=True)
class OutputBlindAdapterChildRequestV1:
    """One-field request with no dedicated output-derived metadata field."""

    case_input_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not OutputBlindAdapterChildRequestV1:
            _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
        object.__setattr__(
            self,
            "case_input_bytes",
            _validated_case_input_bytes(self.case_input_bytes),
        )


def build_output_blind_adapter_child_request_frame(
    value: OutputBlindAdapterChildRequestV1,
) -> bytes:
    if type(value) is not OutputBlindAdapterChildRequestV1:
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    try:
        snapshot = OutputBlindAdapterChildRequestV1(value.case_input_bytes)
    except OutputBlindAdapterChildABIError:
        raise
    except Exception:
        _fail(OutputBlindAdapterChildABICode.INTERNAL)
    return _build_frame(
        domain=OUTPUT_BLIND_ADAPTER_CHILD_REQUEST_DOMAIN,
        field_names=OUTPUT_BLIND_ADAPTER_CHILD_REQUEST_FIELD_NAMES,
        values=(snapshot.case_input_bytes,),
        maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_REQUEST_FRAME_BYTES,
    )


def parse_output_blind_adapter_child_request_frame(
    frame: bytes,
) -> OutputBlindAdapterChildRequestV1:
    values = _parse_frame(
        frame,
        domain=OUTPUT_BLIND_ADAPTER_CHILD_REQUEST_DOMAIN,
        field_names=OUTPUT_BLIND_ADAPTER_CHILD_REQUEST_FIELD_NAMES,
        maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_REQUEST_FRAME_BYTES,
    )
    return OutputBlindAdapterChildRequestV1(case_input_bytes=values[0])


@dataclass(frozen=True)
class LoadedProjectModuleV1:
    """One path-free project module reported by the closure loader."""

    module_name: str
    source_object_id: str
    source_byte_count: int
    source_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not LoadedProjectModuleV1:
            _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
        _bounded_ascii(
            self.module_name,
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_MODULE_NAME_BYTES,
            pattern=_MODULE_NAME_RE,
        )
        if not (
            self.module_name == _PROTECTED_PROJECT_MODULE_ROOT
            or self.module_name.startswith(
                _PROTECTED_PROJECT_MODULE_ROOT + "."
            )
        ):
            _fail(OutputBlindAdapterChildABICode.FRAME_VALUE)
        _bounded_ascii(
            self.source_object_id,
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_OBJECT_ID_BYTES,
            pattern=_TOKEN_RE,
        )
        _bounded_u64(
            self.source_byte_count,
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_BYTES,
        )
        _sha256(self.source_sha256)


def _loaded_project_module_frame(value: LoadedProjectModuleV1) -> bytes:
    if type(value) is not LoadedProjectModuleV1:
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    try:
        snapshot = LoadedProjectModuleV1(
            module_name=value.module_name,
            source_object_id=value.source_object_id,
            source_byte_count=value.source_byte_count,
            source_sha256=value.source_sha256,
        )
    except OutputBlindAdapterChildABIError:
        raise
    except Exception:
        _fail(OutputBlindAdapterChildABICode.INTERNAL)
    return _build_frame(
        domain=OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_MODULE_DOMAIN,
        field_names=OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_MODULE_FIELD_NAMES,
        values=(
            snapshot.module_name.encode("ascii"),
            snapshot.source_object_id.encode("ascii"),
            _u64_bytes(snapshot.source_byte_count),
            snapshot.source_sha256.encode("ascii"),
        ),
        maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_BYTES,
    )


def _parse_loaded_project_module_frame(frame: bytes) -> LoadedProjectModuleV1:
    values = _parse_frame(
        frame,
        domain=OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_MODULE_DOMAIN,
        field_names=OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_MODULE_FIELD_NAMES,
        maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_BYTES,
    )
    return LoadedProjectModuleV1(
        module_name=_ascii_value(
            values[0],
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_MODULE_NAME_BYTES,
            pattern=_MODULE_NAME_RE,
        ),
        source_object_id=_ascii_value(
            values[1],
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_OBJECT_ID_BYTES,
            pattern=_TOKEN_RE,
        ),
        source_byte_count=_bounded_u64(
            _u64_value(values[2]),
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_BYTES,
        ),
        source_sha256=_ascii_value(
            values[3],
            maximum=64,
            pattern=_SHA256_RE,
        ),
    )


def _loaded_project_modules_bytes(
    values: Tuple[LoadedProjectModuleV1, ...],
) -> bytes:
    if type(values) is not tuple:
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    if (
        not values
        or len(values)
        > MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_LOADED_PROJECT_MODULES
        or any(type(item) is not LoadedProjectModuleV1 for item in values)
    ):
        _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
    parts = [_u64_bytes(len(values))]
    total = 8
    for item in values:
        frame = _loaded_project_module_frame(item)
        total += 8 + len(frame)
        if total > MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_BYTES:
            _fail(OutputBlindAdapterChildABICode.INPUT_RESOURCE)
        parts.extend((_u64_bytes(len(frame)), frame))
    return b"".join(parts)


def _parse_loaded_project_modules_bytes(
    value: bytes,
) -> Tuple[LoadedProjectModuleV1, ...]:
    raw = _exact_bytes(
        value,
        maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_BYTES,
    )
    count, offset = _read_u64(raw, 0)
    if (
        count == 0
        or count > MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_LOADED_PROJECT_MODULES
    ):
        _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
    modules = []
    for _ in range(count):
        frame_count, offset = _read_u64(raw, offset)
        if (
            frame_count == 0
            or frame_count
            > MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_BYTES
            or offset + frame_count > len(raw)
        ):
            _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
        try:
            module = _parse_loaded_project_module_frame(
                raw[offset : offset + frame_count]
            )
        except Exception:
            _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
        modules.append(module)
        offset += frame_count
    if offset != len(raw):
        _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
    return tuple(modules)


@dataclass(frozen=True)
class OutputBlindAdapterChildSourceLoadReportV1:
    """Local loader report; this is not executed-source attestation."""

    implementation_closure_sha256: str
    entrypoint_module_name: str
    entrypoint_callable_name: str
    loaded_project_modules: Tuple[LoadedProjectModuleV1, ...]
    protected_namespace_host_fallback_count: int

    def __post_init__(self) -> None:
        if type(self) is not OutputBlindAdapterChildSourceLoadReportV1:
            _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
        _sha256(self.implementation_closure_sha256)
        _bounded_ascii(
            self.entrypoint_module_name,
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_MODULE_NAME_BYTES,
            pattern=_MODULE_NAME_RE,
        )
        if not self.entrypoint_module_name.startswith(
            _PROTECTED_PROJECT_MODULE_ROOT + "."
        ):
            _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
        _bounded_ascii(
            self.entrypoint_callable_name,
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_ENTRYPOINT_NAME_BYTES,
            pattern=_IDENTIFIER_RE,
        )
        if (
            type(self.loaded_project_modules) is not tuple
            or not self.loaded_project_modules
            or len(self.loaded_project_modules)
            > MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_LOADED_PROJECT_MODULES
            or any(
                type(item) is not LoadedProjectModuleV1
                for item in self.loaded_project_modules
            )
        ):
            _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
        try:
            snapshots = tuple(
                LoadedProjectModuleV1(
                    module_name=item.module_name,
                    source_object_id=item.source_object_id,
                    source_byte_count=item.source_byte_count,
                    source_sha256=item.source_sha256,
                )
                for item in self.loaded_project_modules
            )
        except OutputBlindAdapterChildABIError:
            raise
        except Exception:
            _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
        names = tuple(item.module_name for item in snapshots)
        if names != tuple(sorted(set(names))):
            _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
        if self.entrypoint_module_name not in set(names):
            _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
        if (
            type(self.protected_namespace_host_fallback_count) is not int
            or self.protected_namespace_host_fallback_count != 0
        ):
            _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
        object.__setattr__(self, "loaded_project_modules", snapshots)


def build_output_blind_adapter_child_source_load_report_frame(
    value: OutputBlindAdapterChildSourceLoadReportV1,
) -> bytes:
    if type(value) is not OutputBlindAdapterChildSourceLoadReportV1:
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    try:
        snapshot = OutputBlindAdapterChildSourceLoadReportV1(
            implementation_closure_sha256=value.implementation_closure_sha256,
            entrypoint_module_name=value.entrypoint_module_name,
            entrypoint_callable_name=value.entrypoint_callable_name,
            loaded_project_modules=value.loaded_project_modules,
            protected_namespace_host_fallback_count=(
                value.protected_namespace_host_fallback_count
            ),
        )
    except OutputBlindAdapterChildABIError:
        raise
    except Exception:
        _fail(OutputBlindAdapterChildABICode.INTERNAL)
    module_bytes = _loaded_project_modules_bytes(
        snapshot.loaded_project_modules
    )
    return _build_frame(
        domain=OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_DOMAIN,
        field_names=OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_FIELD_NAMES,
        values=(
            snapshot.implementation_closure_sha256.encode("ascii"),
            snapshot.entrypoint_module_name.encode("ascii"),
            snapshot.entrypoint_callable_name.encode("ascii"),
            module_bytes,
            _u64_bytes(snapshot.protected_namespace_host_fallback_count),
        ),
        maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_BYTES,
    )


def parse_output_blind_adapter_child_source_load_report_frame(
    frame: bytes,
) -> OutputBlindAdapterChildSourceLoadReportV1:
    values = _parse_frame(
        frame,
        domain=OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_DOMAIN,
        field_names=OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_FIELD_NAMES,
        maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_BYTES,
    )
    try:
        return OutputBlindAdapterChildSourceLoadReportV1(
            implementation_closure_sha256=_ascii_value(
                values[0], maximum=64, pattern=_SHA256_RE
            ),
            entrypoint_module_name=_ascii_value(
                values[1],
                maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_MODULE_NAME_BYTES,
                pattern=_MODULE_NAME_RE,
            ),
            entrypoint_callable_name=_ascii_value(
                values[2],
                maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_ENTRYPOINT_NAME_BYTES,
                pattern=_IDENTIFIER_RE,
            ),
            loaded_project_modules=_parse_loaded_project_modules_bytes(
                values[3]
            ),
            protected_namespace_host_fallback_count=_u64_value(values[4]),
        )
    except Exception:
        _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)


def _validated_source_load_report_bytes(value: object) -> bytes:
    raw = _exact_bytes(
        value,
        maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_BYTES,
    )
    try:
        report = parse_output_blind_adapter_child_source_load_report_frame(raw)
        rebuilt = build_output_blind_adapter_child_source_load_report_frame(
            report
        )
    except Exception:
        _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
    if rebuilt != raw:
        _fail(OutputBlindAdapterChildABICode.SOURCE_LOAD_REPORT_INVALID)
    return raw


@dataclass(frozen=True)
class OutputBlindAdapterChildSuccessResponseV1:
    """One closed success response carrying the adapted bundle."""

    request_frame_sha256: str
    case_input_sha256: str
    implementation_closure_sha256: str
    adapter_id: str
    adapter_version: str
    runner_direct_adapt_complete_call_count: int
    runner_direct_adapt_call_count: int
    source_load_report_bytes: bytes
    adapted_evidence_bundle_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not OutputBlindAdapterChildSuccessResponseV1:
            _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
        _sha256(self.request_frame_sha256)
        _sha256(self.case_input_sha256)
        _sha256(self.implementation_closure_sha256)
        _bounded_ascii(
            self.adapter_id,
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_ADAPTER_ID_BYTES,
            pattern=_PUBLIC_ID_RE,
        )
        _bounded_ascii(
            self.adapter_version,
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_ADAPTER_VERSION_BYTES,
            pattern=_ADAPTER_VERSION_RE,
        )
        if (
            type(self.runner_direct_adapt_complete_call_count) is not int
            or self.runner_direct_adapt_complete_call_count != 1
            or type(self.runner_direct_adapt_call_count) is not int
            or self.runner_direct_adapt_call_count != 0
        ):
            _fail(OutputBlindAdapterChildABICode.FRAME_VALUE)
        report_bytes = _validated_source_load_report_bytes(
            self.source_load_report_bytes
        )
        report = parse_output_blind_adapter_child_source_load_report_frame(
            report_bytes
        )
        if (
            report.implementation_closure_sha256
            != self.implementation_closure_sha256
        ):
            _fail(OutputBlindAdapterChildABICode.RESPONSE_BINDING)
        bundle_bytes = _exact_bytes(
            self.adapted_evidence_bundle_bytes,
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_BYTES,
        )
        object.__setattr__(self, "source_load_report_bytes", report_bytes)
        object.__setattr__(
            self, "adapted_evidence_bundle_bytes", bundle_bytes
        )


def build_output_blind_adapter_child_success_response_frame(
    value: OutputBlindAdapterChildSuccessResponseV1,
) -> bytes:
    if type(value) is not OutputBlindAdapterChildSuccessResponseV1:
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    try:
        snapshot = OutputBlindAdapterChildSuccessResponseV1(
            request_frame_sha256=value.request_frame_sha256,
            case_input_sha256=value.case_input_sha256,
            implementation_closure_sha256=value.implementation_closure_sha256,
            adapter_id=value.adapter_id,
            adapter_version=value.adapter_version,
            runner_direct_adapt_complete_call_count=(
                value.runner_direct_adapt_complete_call_count
            ),
            runner_direct_adapt_call_count=value.runner_direct_adapt_call_count,
            source_load_report_bytes=value.source_load_report_bytes,
            adapted_evidence_bundle_bytes=value.adapted_evidence_bundle_bytes,
        )
    except OutputBlindAdapterChildABIError:
        raise
    except Exception:
        _fail(OutputBlindAdapterChildABICode.INTERNAL)
    return _build_frame(
        domain=OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_DOMAIN,
        field_names=OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_FIELD_NAMES,
        values=(
            snapshot.request_frame_sha256.encode("ascii"),
            snapshot.case_input_sha256.encode("ascii"),
            snapshot.implementation_closure_sha256.encode("ascii"),
            snapshot.adapter_id.encode("ascii"),
            snapshot.adapter_version.encode("ascii"),
            _u64_bytes(snapshot.runner_direct_adapt_complete_call_count),
            _u64_bytes(snapshot.runner_direct_adapt_call_count),
            snapshot.source_load_report_bytes,
            snapshot.adapted_evidence_bundle_bytes,
        ),
        maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_BYTES,
    )


def parse_output_blind_adapter_child_success_response_frame(
    frame: bytes,
) -> OutputBlindAdapterChildSuccessResponseV1:
    values = _parse_frame(
        frame,
        domain=OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_DOMAIN,
        field_names=OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_FIELD_NAMES,
        maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_BYTES,
    )
    return OutputBlindAdapterChildSuccessResponseV1(
        request_frame_sha256=_ascii_value(
            values[0], maximum=64, pattern=_SHA256_RE
        ),
        case_input_sha256=_ascii_value(
            values[1], maximum=64, pattern=_SHA256_RE
        ),
        implementation_closure_sha256=_ascii_value(
            values[2], maximum=64, pattern=_SHA256_RE
        ),
        adapter_id=_ascii_value(
            values[3],
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_ADAPTER_ID_BYTES,
            pattern=_PUBLIC_ID_RE,
        ),
        adapter_version=_ascii_value(
            values[4],
            maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_ADAPTER_VERSION_BYTES,
            pattern=_ADAPTER_VERSION_RE,
        ),
        runner_direct_adapt_complete_call_count=_u64_value(values[5]),
        runner_direct_adapt_call_count=_u64_value(values[6]),
        source_load_report_bytes=values[7],
        adapted_evidence_bundle_bytes=values[8],
    )


@dataclass(frozen=True)
class OutputBlindAdapterChildFailureResponseV1:
    """One fixed-code child failure without exception or diagnostic text."""

    request_frame_sha256: str
    case_input_sha256: str
    implementation_closure_sha256: str
    failure_code: OutputBlindAdapterChildFailureCode

    def __post_init__(self) -> None:
        if type(self) is not OutputBlindAdapterChildFailureResponseV1:
            _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
        _sha256(self.request_frame_sha256)
        _sha256(self.case_input_sha256)
        _sha256(self.implementation_closure_sha256)
        if type(self.failure_code) is not OutputBlindAdapterChildFailureCode:
            _fail(OutputBlindAdapterChildABICode.FRAME_VALUE)


def build_output_blind_adapter_child_failure_response_frame(
    value: OutputBlindAdapterChildFailureResponseV1,
) -> bytes:
    if type(value) is not OutputBlindAdapterChildFailureResponseV1:
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    try:
        snapshot = OutputBlindAdapterChildFailureResponseV1(
            request_frame_sha256=value.request_frame_sha256,
            case_input_sha256=value.case_input_sha256,
            implementation_closure_sha256=value.implementation_closure_sha256,
            failure_code=value.failure_code,
        )
    except OutputBlindAdapterChildABIError:
        raise
    except Exception:
        _fail(OutputBlindAdapterChildABICode.INTERNAL)
    return _build_frame(
        domain=OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_DOMAIN,
        field_names=OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_FIELD_NAMES,
        values=(
            snapshot.request_frame_sha256.encode("ascii"),
            snapshot.case_input_sha256.encode("ascii"),
            snapshot.implementation_closure_sha256.encode("ascii"),
            snapshot.failure_code.value.encode("ascii"),
        ),
        maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_BYTES,
    )


def parse_output_blind_adapter_child_failure_response_frame(
    frame: bytes,
) -> OutputBlindAdapterChildFailureResponseV1:
    values = _parse_frame(
        frame,
        domain=OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_DOMAIN,
        field_names=OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_FIELD_NAMES,
        maximum=MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_BYTES,
    )
    try:
        failure_code = OutputBlindAdapterChildFailureCode(
            values[3].decode("ascii", "strict")
        )
    except (UnicodeError, ValueError):
        _fail(OutputBlindAdapterChildABICode.FRAME_VALUE)
    return OutputBlindAdapterChildFailureResponseV1(
        request_frame_sha256=_ascii_value(
            values[0], maximum=64, pattern=_SHA256_RE
        ),
        case_input_sha256=_ascii_value(
            values[1], maximum=64, pattern=_SHA256_RE
        ),
        implementation_closure_sha256=_ascii_value(
            values[2], maximum=64, pattern=_SHA256_RE
        ),
        failure_code=failure_code,
    )


class ValidatedOutputBlindAdapterChildSuccessV1(NamedTuple):
    """Cross-bound success transport; still not execution attestation."""

    request: OutputBlindAdapterChildRequestV1
    response: OutputBlindAdapterChildSuccessResponseV1
    source_load_report: OutputBlindAdapterChildSourceLoadReportV1
    adapted_evidence_bundle_bytes: bytes


class ValidatedOutputBlindAdapterChildFailureV1(NamedTuple):
    """Cross-bound closed child failure transport."""

    request: OutputBlindAdapterChildRequestV1
    response: OutputBlindAdapterChildFailureResponseV1


def _expected_request_identities(
    request_frame_bytes: bytes,
) -> Tuple[OutputBlindAdapterChildRequestV1, str, str]:
    request = parse_output_blind_adapter_child_request_frame(
        request_frame_bytes
    )
    request_sha256 = hashlib.sha256(request_frame_bytes).hexdigest()
    try:
        case_input_sha256 = output_blind_case_input_v1_sha256(
            request.case_input_bytes
        )
    except Exception:
        _fail(OutputBlindAdapterChildABICode.CASE_INPUT_INVALID)
    return request, request_sha256, case_input_sha256


def validate_output_blind_adapter_child_success_identity(
    request_frame_bytes: bytes,
    response_frame_bytes: bytes,
    *,
    implementation_closure_sha256: str,
) -> ValidatedOutputBlindAdapterChildSuccessV1:
    if type(implementation_closure_sha256) is not str:
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    closure_sha256 = _sha256(implementation_closure_sha256)
    request, request_sha256, case_input_sha256 = _expected_request_identities(
        request_frame_bytes
    )
    response = parse_output_blind_adapter_child_success_response_frame(
        response_frame_bytes
    )
    report = parse_output_blind_adapter_child_source_load_report_frame(
        response.source_load_report_bytes
    )
    if (
        response.request_frame_sha256 != request_sha256
        or response.case_input_sha256 != case_input_sha256
        or response.implementation_closure_sha256 != closure_sha256
        or report.implementation_closure_sha256 != closure_sha256
    ):
        _fail(OutputBlindAdapterChildABICode.RESPONSE_BINDING)
    return ValidatedOutputBlindAdapterChildSuccessV1(
        request=request,
        response=response,
        source_load_report=report,
        adapted_evidence_bundle_bytes=bytes(
            response.adapted_evidence_bundle_bytes
        ),
    )


def validate_output_blind_adapter_child_failure_identity(
    request_frame_bytes: bytes,
    response_frame_bytes: bytes,
    *,
    implementation_closure_sha256: str,
) -> ValidatedOutputBlindAdapterChildFailureV1:
    if type(implementation_closure_sha256) is not str:
        _fail(OutputBlindAdapterChildABICode.INPUT_TYPE)
    closure_sha256 = _sha256(implementation_closure_sha256)
    request, request_sha256, case_input_sha256 = _expected_request_identities(
        request_frame_bytes
    )
    response = parse_output_blind_adapter_child_failure_response_frame(
        response_frame_bytes
    )
    if (
        response.request_frame_sha256 != request_sha256
        or response.case_input_sha256 != case_input_sha256
        or response.implementation_closure_sha256 != closure_sha256
    ):
        _fail(OutputBlindAdapterChildABICode.RESPONSE_BINDING)
    return ValidatedOutputBlindAdapterChildFailureV1(
        request=request,
        response=response,
    )


__all__ = [
    "MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_ADAPTER_ID_BYTES",
    "MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_ADAPTER_VERSION_BYTES",
    "MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_ENTRYPOINT_NAME_BYTES",
    "MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_BYTES",
    "MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_LOADED_PROJECT_MODULES",
    "MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_MODULE_NAME_BYTES",
    "MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_REQUEST_FRAME_BYTES",
    "MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_BYTES",
    "MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_OBJECT_ID_BYTES",
    "MAXIMUM_OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_BYTES",
    "OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_DOMAIN",
    "OUTPUT_BLIND_ADAPTER_CHILD_FAILURE_RESPONSE_FIELD_NAMES",
    "OUTPUT_BLIND_ADAPTER_CHILD_REQUEST_DOMAIN",
    "OUTPUT_BLIND_ADAPTER_CHILD_REQUEST_FIELD_NAMES",
    "OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_DOMAIN",
    "OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_LOAD_REPORT_FIELD_NAMES",
    "OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_MODULE_DOMAIN",
    "OUTPUT_BLIND_ADAPTER_CHILD_SOURCE_MODULE_FIELD_NAMES",
    "OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_DOMAIN",
    "OUTPUT_BLIND_ADAPTER_CHILD_SUCCESS_RESPONSE_FIELD_NAMES",
    "LoadedProjectModuleV1",
    "OutputBlindAdapterChildABICode",
    "OutputBlindAdapterChildABIError",
    "OutputBlindAdapterChildFailureCode",
    "OutputBlindAdapterChildFailureResponseV1",
    "OutputBlindAdapterChildRequestV1",
    "OutputBlindAdapterChildSourceLoadReportV1",
    "OutputBlindAdapterChildSuccessResponseV1",
    "ValidatedOutputBlindAdapterChildFailureV1",
    "ValidatedOutputBlindAdapterChildSuccessV1",
    "build_output_blind_adapter_child_failure_response_frame",
    "build_output_blind_adapter_child_request_frame",
    "build_output_blind_adapter_child_source_load_report_frame",
    "build_output_blind_adapter_child_success_response_frame",
    "parse_output_blind_adapter_child_failure_response_frame",
    "parse_output_blind_adapter_child_request_frame",
    "parse_output_blind_adapter_child_source_load_report_frame",
    "parse_output_blind_adapter_child_success_response_frame",
    "validate_output_blind_adapter_child_failure_identity",
    "validate_output_blind_adapter_child_success_identity",
]
