"""Fixed, non-executing binary ABI for an experimental oracle worker.

This module only defines immutable request/response values and their exact
wire representation.  It performs no filesystem access, source loading,
subprocess execution, adapter callback, source-policy check, or gate decision.
In particular, parsing a response is not evidence that an oracle was executed
in an isolated or decision-eligible environment.

Frames use one fixed layout::

    DOMAIN || NUL || u64be(field_count) ||
        u64be(name_length) || ASCII_NAME ||
        u64be(value_length) || RAW_VALUE || ...

Field names and their order are part of the V1 ABI.  Request frames
deliberately contain no expected-output payload.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Tuple


ORACLE_WORKER_REQUEST_DOMAIN_BYTES = (
    b"heterodiff.adapter.oracle-worker-request.v1"
)
ORACLE_WORKER_RESPONSE_DOMAIN_BYTES = (
    b"heterodiff.adapter.oracle-worker-response.v1"
)

ORACLE_WORKER_REQUEST_FIELD_NAMES = (
    b"execution_input_set_sha256",
    b"case_ordinal",
    b"oracle_id",
    b"oracle_source_byte_count",
    b"oracle_source_sha256",
    b"source_bytes",
    b"descriptor_payload_bytes",
    b"partition_payload_bytes",
    b"split_manifest_payload_bytes",
)
ORACLE_WORKER_RESPONSE_FIELD_NAMES = (
    b"request_frame_sha256",
    b"case_ordinal",
    b"oracle_id",
    b"oracle_source_byte_count",
    b"oracle_source_sha256",
    b"expected_configuration_payload_bytes",
    b"expected_evidence_payload_bytes",
    b"expected_native_observation_sha256",
)

MAXIMUM_ORACLE_WORKER_FRAME_BYTES = 32 * 1024 * 1024
MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES = 16 * 1024 * 1024
MAXIMUM_ORACLE_WORKER_SOURCE_BYTES = 64 * 1024
MAXIMUM_ORACLE_SOURCE_BYTES = 1024 * 1024
MAXIMUM_ORACLE_ID_BYTES = 128
MAXIMUM_ORACLE_WORKER_CASE_ORDINAL = 4095

MAXIMUM_ORACLE_ABI_JSON_DEPTH = 32
MAXIMUM_ORACLE_ABI_JSON_NODES = 200_000
MAXIMUM_ORACLE_ABI_JSON_STRING_BYTES = 512 * 1024

_MAXIMUM_U64 = (1 << 64) - 1
_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class OracleWorkerABICode(str, Enum):
    """Closed error identifiers for the V1 oracle-worker ABI."""

    ABI_INPUT_TYPE = "ABI_INPUT_TYPE"
    ABI_FRAME_SIZE = "ABI_FRAME_SIZE"
    ABI_FRAME_DOMAIN = "ABI_FRAME_DOMAIN"
    ABI_FRAME_FIELD_COUNT = "ABI_FRAME_FIELD_COUNT"
    ABI_FRAME_FIELD_ORDER = "ABI_FRAME_FIELD_ORDER"
    ABI_FRAME_TRUNCATED = "ABI_FRAME_TRUNCATED"
    ABI_FRAME_TRAILING = "ABI_FRAME_TRAILING"
    ABI_FIELD_VALUE = "ABI_FIELD_VALUE"
    ABI_PAYLOAD_JSON = "ABI_PAYLOAD_JSON"
    ABI_PAYLOAD_NONCANONICAL = "ABI_PAYLOAD_NONCANONICAL"
    ABI_RESPONSE_IDENTITY = "ABI_RESPONSE_IDENTITY"


_ERROR_MESSAGES = MappingProxyType(
    {
        OracleWorkerABICode.ABI_INPUT_TYPE: (
            "oracle-worker ABI input has an invalid exact type"
        ),
        OracleWorkerABICode.ABI_FRAME_SIZE: (
            "oracle-worker ABI frame is outside its fixed byte bound"
        ),
        OracleWorkerABICode.ABI_FRAME_DOMAIN: (
            "oracle-worker ABI frame has the wrong fixed domain"
        ),
        OracleWorkerABICode.ABI_FRAME_FIELD_COUNT: (
            "oracle-worker ABI frame has the wrong fixed field count"
        ),
        OracleWorkerABICode.ABI_FRAME_FIELD_ORDER: (
            "oracle-worker ABI frame has the wrong fixed field order"
        ),
        OracleWorkerABICode.ABI_FRAME_TRUNCATED: (
            "oracle-worker ABI frame is structurally truncated"
        ),
        OracleWorkerABICode.ABI_FRAME_TRAILING: (
            "oracle-worker ABI frame has trailing bytes"
        ),
        OracleWorkerABICode.ABI_FIELD_VALUE: (
            "oracle-worker ABI field violates its fixed value contract"
        ),
        OracleWorkerABICode.ABI_PAYLOAD_JSON: (
            "oracle-worker ABI payload is not strict canonical-profile JSON"
        ),
        OracleWorkerABICode.ABI_PAYLOAD_NONCANONICAL: (
            "oracle-worker ABI payload JSON is not canonical"
        ),
        OracleWorkerABICode.ABI_RESPONSE_IDENTITY: (
            "oracle-worker response does not match its exact request identity"
        ),
    }
)


class OracleWorkerABIError(ValueError):
    """One fixed coded ABI failure with no untrusted interpolation."""

    def __init__(self, code: OracleWorkerABICode) -> None:
        if type(code) is not OracleWorkerABICode:
            raise TypeError("oracle-worker ABI code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: OracleWorkerABICode) -> None:
    raise OracleWorkerABIError(code) from None


def _exact_type(condition: bool) -> None:
    if not condition:
        _fail(OracleWorkerABICode.ABI_INPUT_TYPE)


def _digest(value: object) -> str:
    _exact_type(type(value) is str)
    if _SHA256_RE.fullmatch(value) is None:
        _fail(OracleWorkerABICode.ABI_FIELD_VALUE)
    return value


def _u64(value: object) -> int:
    _exact_type(type(value) is int)
    if value < 0 or value > _MAXIMUM_U64:
        _fail(OracleWorkerABICode.ABI_FIELD_VALUE)
    return value


def _positive_bounded_integer(value: object, maximum: int) -> int:
    result = _u64(value)
    if result == 0 or result > maximum:
        _fail(OracleWorkerABICode.ABI_FIELD_VALUE)
    return result


def _bounded_case_ordinal(value: object) -> int:
    result = _u64(value)
    if result > MAXIMUM_ORACLE_WORKER_CASE_ORDINAL:
        _fail(OracleWorkerABICode.ABI_FIELD_VALUE)
    return result


def _oracle_id(value: object) -> str:
    _exact_type(type(value) is str)
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        _fail(OracleWorkerABICode.ABI_FIELD_VALUE)
    if (
        not encoded
        or len(encoded) > MAXIMUM_ORACLE_ID_BYTES
        or _TOKEN_RE.fullmatch(value) is None
    ):
        _fail(OracleWorkerABICode.ABI_FIELD_VALUE)
    return value


def _bounded_bytes(value: object, *, maximum: int) -> bytes:
    _exact_type(type(value) is bytes)
    if not value or len(value) > maximum:
        _fail(OracleWorkerABICode.ABI_FIELD_VALUE)
    return value


def _lexical_json_preflight(value: bytes) -> None:
    if any(byte >= 0x80 for byte in value):
        _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
    depth = 0
    tokens = 0
    in_string = False
    escaped = False
    string_bytes = 0
    for byte in value:
        if in_string:
            if not escaped and byte == 0x22:
                in_string = False
                continue
            string_bytes += 1
            if string_bytes > MAXIMUM_ORACLE_ABI_JSON_STRING_BYTES:
                _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            continue
        if byte == 0x22:
            in_string = True
            string_bytes = 0
            tokens += 1
        elif byte in (0x7B, 0x5B):
            depth += 1
            tokens += 1
            if depth > MAXIMUM_ORACLE_ABI_JSON_DEPTH:
                _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0:
                _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
        elif byte in (0x2C, 0x3A):
            tokens += 1
        if tokens > MAXIMUM_ORACLE_ABI_JSON_NODES * 2:
            _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
    if in_string or depth != 0:
        _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)


def _validate_json_tree(value: object) -> None:
    nodes = 0
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAXIMUM_ORACLE_ABI_JSON_NODES:
            _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
        if depth > MAXIMUM_ORACLE_ABI_JSON_DEPTH:
            _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
        if current is None or type(current) is bool:
            continue
        if type(current) is int:
            if abs(current) > _MAXIMUM_SAFE_INTEGER:
                _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
            continue
        if type(current) is str:
            try:
                encoded = current.encode("utf-8", "strict")
            except UnicodeError:
                _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
            if len(encoded) > MAXIMUM_ORACLE_ABI_JSON_STRING_BYTES:
                _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
            continue
        if type(current) is list:
            stack.extend((item, depth + 1) for item in reversed(current))
            continue
        if type(current) is dict:
            for key, item in reversed(tuple(current.items())):
                if type(key) is not str:
                    _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
                try:
                    encoded_key = key.encode("utf-8", "strict")
                except UnicodeError:
                    _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
                if len(encoded_key) > MAXIMUM_ORACLE_ABI_JSON_STRING_BYTES:
                    _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
                stack.append((item, depth + 1))
            continue
        _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)


def _canonical_json_payload(value: object) -> bytes:
    _exact_type(type(value) is bytes)
    if (
        not value
        or len(value) > MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES
    ):
        _fail(OracleWorkerABICode.ABI_FIELD_VALUE)
    _lexical_json_preflight(value)
    try:
        text = value.decode("ascii", "strict")
    except UnicodeError:
        _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)

    def object_pairs(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
            result[key] = item
        return result

    def parse_integer(token):
        digits = token[1:] if token.startswith("-") else token
        if len(digits) > 16:
            _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
        result = int(token, 10)
        if abs(result) > _MAXIMUM_SAFE_INTEGER:
            _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
        return result

    def reject_number(_token):
        _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)

    try:
        tree = json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_int=parse_integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
    except OracleWorkerABIError:
        raise
    except (TypeError, ValueError, RecursionError):
        _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
    _validate_json_tree(tree)
    try:
        canonical = json.dumps(
            tree,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        _fail(OracleWorkerABICode.ABI_PAYLOAD_JSON)
    if canonical != value:
        _fail(OracleWorkerABICode.ABI_PAYLOAD_NONCANONICAL)
    return value


def _encoded_frame_size(
    domain: bytes,
    field_names: Tuple[bytes, ...],
    values: Tuple[bytes, ...],
) -> int:
    return (
        len(domain)
        + 1
        + 8
        + sum(8 + len(name) + 8 + len(value) for name, value in zip(
            field_names,
            values,
        ))
    )


def _validate_frame_size(
    domain: bytes,
    field_names: Tuple[bytes, ...],
    values: Tuple[bytes, ...],
) -> None:
    if _encoded_frame_size(domain, field_names, values) > (
        MAXIMUM_ORACLE_WORKER_FRAME_BYTES
    ):
        _fail(OracleWorkerABICode.ABI_FRAME_SIZE)


@dataclass(frozen=True)
class OracleWorkerRequestV1:
    """Exact inputs made available to one oracle case invocation."""

    execution_input_set_sha256: str
    case_ordinal: int
    oracle_id: str
    oracle_source_byte_count: int
    oracle_source_sha256: str
    source_bytes: bytes
    descriptor_payload_bytes: bytes
    partition_payload_bytes: bytes
    split_manifest_payload_bytes: bytes

    def __post_init__(self) -> None:
        _exact_type(type(self) is OracleWorkerRequestV1)
        _digest(self.execution_input_set_sha256)
        _bounded_case_ordinal(self.case_ordinal)
        _oracle_id(self.oracle_id)
        _positive_bounded_integer(
            self.oracle_source_byte_count,
            MAXIMUM_ORACLE_SOURCE_BYTES,
        )
        _digest(self.oracle_source_sha256)
        _bounded_bytes(
            self.source_bytes,
            maximum=MAXIMUM_ORACLE_WORKER_SOURCE_BYTES,
        )
        _canonical_json_payload(self.descriptor_payload_bytes)
        _canonical_json_payload(self.partition_payload_bytes)
        _canonical_json_payload(self.split_manifest_payload_bytes)
        _validate_frame_size(
            ORACLE_WORKER_REQUEST_DOMAIN_BYTES,
            ORACLE_WORKER_REQUEST_FIELD_NAMES,
            _request_values(self),
        )


@dataclass(frozen=True)
class OracleWorkerResponseV1:
    """Exact output payloads returned for one request frame."""

    request_frame_sha256: str
    case_ordinal: int
    oracle_id: str
    oracle_source_byte_count: int
    oracle_source_sha256: str
    expected_configuration_payload_bytes: bytes
    expected_evidence_payload_bytes: bytes
    expected_native_observation_sha256: str

    def __post_init__(self) -> None:
        _exact_type(type(self) is OracleWorkerResponseV1)
        _digest(self.request_frame_sha256)
        _bounded_case_ordinal(self.case_ordinal)
        _oracle_id(self.oracle_id)
        _positive_bounded_integer(
            self.oracle_source_byte_count,
            MAXIMUM_ORACLE_SOURCE_BYTES,
        )
        _digest(self.oracle_source_sha256)
        _canonical_json_payload(
            self.expected_configuration_payload_bytes
        )
        _canonical_json_payload(self.expected_evidence_payload_bytes)
        _digest(self.expected_native_observation_sha256)
        _validate_frame_size(
            ORACLE_WORKER_RESPONSE_DOMAIN_BYTES,
            ORACLE_WORKER_RESPONSE_FIELD_NAMES,
            _response_values(self),
        )


@dataclass(frozen=True)
class ValidatedOracleWorkerResponseIdentityV1:
    """A parsed response byte-matched to one complete request frame."""

    request: OracleWorkerRequestV1
    response: OracleWorkerResponseV1
    request_frame_sha256: str

    def __post_init__(self) -> None:
        _exact_type(type(self) is ValidatedOracleWorkerResponseIdentityV1)
        _exact_type(type(self.request) is OracleWorkerRequestV1)
        _exact_type(type(self.response) is OracleWorkerResponseV1)
        OracleWorkerRequestV1.__post_init__(self.request)
        OracleWorkerResponseV1.__post_init__(self.response)
        _digest(self.request_frame_sha256)
        canonical_request_frame = build_oracle_worker_request_frame(
            self.request
        )
        canonical_request_sha256 = hashlib.sha256(
            canonical_request_frame
        ).hexdigest()
        if (
            canonical_request_sha256 != self.request_frame_sha256
            or
            self.response.request_frame_sha256 != self.request_frame_sha256
            or self.response.case_ordinal != self.request.case_ordinal
            or self.response.oracle_id != self.request.oracle_id
            or self.response.oracle_source_byte_count
            != self.request.oracle_source_byte_count
            or self.response.oracle_source_sha256
            != self.request.oracle_source_sha256
        ):
            _fail(OracleWorkerABICode.ABI_RESPONSE_IDENTITY)


def _request_values(value: OracleWorkerRequestV1) -> Tuple[bytes, ...]:
    return (
        value.execution_input_set_sha256.encode("ascii"),
        value.case_ordinal.to_bytes(8, "big"),
        value.oracle_id.encode("ascii"),
        value.oracle_source_byte_count.to_bytes(8, "big"),
        value.oracle_source_sha256.encode("ascii"),
        value.source_bytes,
        value.descriptor_payload_bytes,
        value.partition_payload_bytes,
        value.split_manifest_payload_bytes,
    )


def _response_values(value: OracleWorkerResponseV1) -> Tuple[bytes, ...]:
    return (
        value.request_frame_sha256.encode("ascii"),
        value.case_ordinal.to_bytes(8, "big"),
        value.oracle_id.encode("ascii"),
        value.oracle_source_byte_count.to_bytes(8, "big"),
        value.oracle_source_sha256.encode("ascii"),
        value.expected_configuration_payload_bytes,
        value.expected_evidence_payload_bytes,
        value.expected_native_observation_sha256.encode("ascii"),
    )


def _build_frame(
    domain: bytes,
    field_names: Tuple[bytes, ...],
    values: Tuple[bytes, ...],
) -> bytes:
    _validate_frame_size(domain, field_names, values)
    parts = [domain, b"\x00", len(field_names).to_bytes(8, "big")]
    for name, value in zip(field_names, values):
        parts.extend(
            (
                len(name).to_bytes(8, "big"),
                name,
                len(value).to_bytes(8, "big"),
                value,
            )
        )
    result = b"".join(parts)
    if len(result) > MAXIMUM_ORACLE_WORKER_FRAME_BYTES:  # pragma: no cover
        _fail(OracleWorkerABICode.ABI_FRAME_SIZE)
    return result


def build_oracle_worker_request_frame(
    value: OracleWorkerRequestV1,
) -> bytes:
    """Build the sole V1 request representation."""

    _exact_type(type(value) is OracleWorkerRequestV1)
    OracleWorkerRequestV1.__post_init__(value)
    return _build_frame(
        ORACLE_WORKER_REQUEST_DOMAIN_BYTES,
        ORACLE_WORKER_REQUEST_FIELD_NAMES,
        _request_values(value),
    )


def build_oracle_worker_response_frame(
    value: OracleWorkerResponseV1,
) -> bytes:
    """Build the sole V1 response representation."""

    _exact_type(type(value) is OracleWorkerResponseV1)
    OracleWorkerResponseV1.__post_init__(value)
    return _build_frame(
        ORACLE_WORKER_RESPONSE_DOMAIN_BYTES,
        ORACLE_WORKER_RESPONSE_FIELD_NAMES,
        _response_values(value),
    )


def _read_u64(frame: bytes, offset: int) -> Tuple[int, int]:
    end = offset + 8
    if end > len(frame):
        _fail(OracleWorkerABICode.ABI_FRAME_TRUNCATED)
    return int.from_bytes(frame[offset:end], "big"), end


def _parse_frame(
    frame: object,
    *,
    domain: bytes,
    field_names: Tuple[bytes, ...],
) -> Tuple[bytes, ...]:
    _exact_type(type(frame) is bytes)
    if not frame or len(frame) > MAXIMUM_ORACLE_WORKER_FRAME_BYTES:
        _fail(OracleWorkerABICode.ABI_FRAME_SIZE)
    domain_end = len(domain)
    if (
        len(frame) < domain_end + 1
        or frame[:domain_end] != domain
        or frame[domain_end] != 0
    ):
        _fail(OracleWorkerABICode.ABI_FRAME_DOMAIN)
    offset = domain_end + 1
    field_count, offset = _read_u64(frame, offset)
    if field_count != len(field_names):
        _fail(OracleWorkerABICode.ABI_FRAME_FIELD_COUNT)
    values = []
    for expected_name in field_names:
        name_length, offset = _read_u64(frame, offset)
        if name_length > len(frame) - offset:
            _fail(OracleWorkerABICode.ABI_FRAME_TRUNCATED)
        name_end = offset + name_length
        name = frame[offset:name_end]
        offset = name_end
        if name != expected_name:
            _fail(OracleWorkerABICode.ABI_FRAME_FIELD_ORDER)
        value_length, offset = _read_u64(frame, offset)
        if value_length > len(frame) - offset:
            _fail(OracleWorkerABICode.ABI_FRAME_TRUNCATED)
        value_end = offset + value_length
        values.append(frame[offset:value_end])
        offset = value_end
    if offset != len(frame):
        _fail(OracleWorkerABICode.ABI_FRAME_TRAILING)
    return tuple(values)


def _ascii(value: bytes) -> str:
    try:
        return value.decode("ascii", "strict")
    except UnicodeError:
        _fail(OracleWorkerABICode.ABI_FIELD_VALUE)


def _fixed_u64(value: bytes) -> int:
    if len(value) != 8:
        _fail(OracleWorkerABICode.ABI_FIELD_VALUE)
    return int.from_bytes(value, "big")


def parse_oracle_worker_request_frame(
    frame: bytes,
) -> OracleWorkerRequestV1:
    """Strict-parse one complete request frame."""

    values = _parse_frame(
        frame,
        domain=ORACLE_WORKER_REQUEST_DOMAIN_BYTES,
        field_names=ORACLE_WORKER_REQUEST_FIELD_NAMES,
    )
    return OracleWorkerRequestV1(
        execution_input_set_sha256=_ascii(values[0]),
        case_ordinal=_fixed_u64(values[1]),
        oracle_id=_ascii(values[2]),
        oracle_source_byte_count=_fixed_u64(values[3]),
        oracle_source_sha256=_ascii(values[4]),
        source_bytes=values[5],
        descriptor_payload_bytes=values[6],
        partition_payload_bytes=values[7],
        split_manifest_payload_bytes=values[8],
    )


def parse_oracle_worker_response_frame(
    frame: bytes,
) -> OracleWorkerResponseV1:
    """Strict-parse one complete response frame."""

    values = _parse_frame(
        frame,
        domain=ORACLE_WORKER_RESPONSE_DOMAIN_BYTES,
        field_names=ORACLE_WORKER_RESPONSE_FIELD_NAMES,
    )
    return OracleWorkerResponseV1(
        request_frame_sha256=_ascii(values[0]),
        case_ordinal=_fixed_u64(values[1]),
        oracle_id=_ascii(values[2]),
        oracle_source_byte_count=_fixed_u64(values[3]),
        oracle_source_sha256=_ascii(values[4]),
        expected_configuration_payload_bytes=values[5],
        expected_evidence_payload_bytes=values[6],
        expected_native_observation_sha256=_ascii(values[7]),
    )


def validate_oracle_worker_response_identity(
    request_frame_bytes: bytes,
    response_frame_bytes: bytes,
) -> ValidatedOracleWorkerResponseIdentityV1:
    """Parse both frames and exact-match the response request identity."""

    _exact_type(type(request_frame_bytes) is bytes)
    _exact_type(type(response_frame_bytes) is bytes)
    request = parse_oracle_worker_request_frame(request_frame_bytes)
    response = parse_oracle_worker_response_frame(response_frame_bytes)
    request_frame_sha256 = hashlib.sha256(request_frame_bytes).hexdigest()
    return ValidatedOracleWorkerResponseIdentityV1(
        request=request,
        response=response,
        request_frame_sha256=request_frame_sha256,
    )


__all__ = [
    "MAXIMUM_ORACLE_ID_BYTES",
    "MAXIMUM_ORACLE_SOURCE_BYTES",
    "MAXIMUM_ORACLE_WORKER_FRAME_BYTES",
    "MAXIMUM_ORACLE_WORKER_CASE_ORDINAL",
    "MAXIMUM_ORACLE_WORKER_SOURCE_BYTES",
    "MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES",
    "ORACLE_WORKER_REQUEST_DOMAIN_BYTES",
    "ORACLE_WORKER_REQUEST_FIELD_NAMES",
    "ORACLE_WORKER_RESPONSE_DOMAIN_BYTES",
    "ORACLE_WORKER_RESPONSE_FIELD_NAMES",
    "OracleWorkerABICode",
    "OracleWorkerABIError",
    "OracleWorkerRequestV1",
    "OracleWorkerResponseV1",
    "ValidatedOracleWorkerResponseIdentityV1",
    "build_oracle_worker_request_frame",
    "build_oracle_worker_response_frame",
    "parse_oracle_worker_request_frame",
    "parse_oracle_worker_response_frame",
    "validate_oracle_worker_response_identity",
]
