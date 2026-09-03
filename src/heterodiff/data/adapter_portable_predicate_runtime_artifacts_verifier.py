"""Implementation-separated verifier for runtime-artifact envelopes.

This module independently reconstructs the Checkpoint-56A envelope boundary.
It uses only the frozen verifier-side semantic core and profile validator.  It
does not import the source runtime-artifact implementation or the source
semantic core.  Acceptance is limited to canonical top-level envelopes and
their selected-profile pins; it does not validate nested runtime semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import re
from typing import Final

from heterodiff.data import (
    adapter_portable_predicate_language_core_verifier as _verified_core,
)


__all__ = (
    "CompiledPortablePredicateRuntimeVerifierProfileV1",
    "PortablePredicateRuntimeEnvelopeVerificationCode",
    "PortablePredicateRuntimeEnvelopeVerificationError",
    "PortablePredicateRuntimeVerifierEnvelopeV1",
    "compile_portable_predicate_runtime_verifier_profile_v1",
    "verify_portable_predicate_runtime_envelope_v1",
)


PORTABLE_PREDICATE_RUNTIME_ENVELOPE_VALIDATION_SCOPE_ID: Final = (
    "CANONICAL_ENVELOPE_AND_PROFILE_PINS_ONLY_V1"
)
_MAXIMUM_ARTIFACT_BYTES: Final = 4 * 1024 * 1024
_MAXIMUM_JSON_DEPTH: Final = 32
_MAXIMUM_JSON_ITEMS: Final = 65536
_MAXIMUM_JSON_INTEGER_DIGITS: Final = 20
_MAXIMUM_IDENTIFIER_BYTES: Final = 512
_IDENTIFIER_RE: Final = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:/+\-]*$"
)
_SHA256_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_PAYLOAD_HEX_RE: Final = re.compile(r"^(?:[0-9a-f]{2})*$")
_CONTEXT_NONCE_RE: Final = re.compile(r"^[0-9a-f]{64}$")


class PortablePredicateRuntimeEnvelopeVerificationCode(str, Enum):
    """Closed verifier failures matching the source envelope boundary."""

    PROFILE_INPUT_TYPE = "PROFILE_INPUT_TYPE"
    PROFILE_INPUT_RESOURCE = "PROFILE_INPUT_RESOURCE"
    PROFILE_JSON_INVALID = "PROFILE_JSON_INVALID"
    PROFILE_JSON_TREE_INVALID = "PROFILE_JSON_TREE_INVALID"
    PROFILE_CANONICAL_MISMATCH = "PROFILE_CANONICAL_MISMATCH"
    PROFILE_SCHEMA_INVALID = "PROFILE_SCHEMA_INVALID"
    PROFILE_BINDING_MISMATCH = "PROFILE_BINDING_MISMATCH"
    COMPILED_PROFILE_INVALID = "COMPILED_PROFILE_INVALID"
    ARTIFACT_INPUT_TYPE = "ARTIFACT_INPUT_TYPE"
    EXPECTED_ROLE_INVALID = "EXPECTED_ROLE_INVALID"
    ARTIFACT_INPUT_RESOURCE = "ARTIFACT_INPUT_RESOURCE"
    ARTIFACT_JSON_INVALID = "ARTIFACT_JSON_INVALID"
    ARTIFACT_JSON_TREE_INVALID = "ARTIFACT_JSON_TREE_INVALID"
    ARTIFACT_CANONICAL_MISMATCH = "ARTIFACT_CANONICAL_MISMATCH"
    ARTIFACT_SCHEMA_INVALID = "ARTIFACT_SCHEMA_INVALID"
    ARTIFACT_BINDING_MISMATCH = "ARTIFACT_BINDING_MISMATCH"
    INTERNAL = "INTERNAL"


_ERROR_MESSAGES: Final = {
    PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_INPUT_TYPE: (
        "portable predicate runtime profile input has an invalid exact type"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_INPUT_RESOURCE: (
        "portable predicate runtime profile input exceeds its resource ceiling"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_JSON_INVALID: (
        "portable predicate runtime profile JSON is invalid"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_JSON_TREE_INVALID: (
        "portable predicate runtime profile JSON tree is inadmissible"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_CANONICAL_MISMATCH: (
        "portable predicate runtime profile bytes are not canonical"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_SCHEMA_INVALID: (
        "portable predicate runtime profile schema is invalid"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_BINDING_MISMATCH: (
        "portable predicate runtime profile selection pins do not match"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.COMPILED_PROFILE_INVALID: (
        "portable predicate runtime compiled profile is invalid"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_INPUT_TYPE: (
        "portable predicate runtime artifact input has an invalid exact type"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.EXPECTED_ROLE_INVALID: (
        "portable predicate runtime expected artifact role is invalid"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_INPUT_RESOURCE: (
        "portable predicate runtime artifact exceeds its resource ceiling"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_JSON_INVALID: (
        "portable predicate runtime artifact JSON is invalid"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_JSON_TREE_INVALID: (
        "portable predicate runtime artifact JSON tree is inadmissible"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_CANONICAL_MISMATCH: (
        "portable predicate runtime artifact bytes are not canonical"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_SCHEMA_INVALID: (
        "portable predicate runtime artifact envelope schema is invalid"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_BINDING_MISMATCH: (
        "portable predicate runtime artifact profile binding does not match"
    ),
    PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL: (
        "portable predicate runtime envelope implementation is inconsistent"
    ),
}


class PortablePredicateRuntimeEnvelopeVerificationError(ValueError):
    """One fixed-message verifier-side envelope failure."""

    def __init__(
        self,
        code: PortablePredicateRuntimeEnvelopeVerificationCode,
    ):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


@dataclass(frozen=True)
class CompiledPortablePredicateRuntimeVerifierProfileV1:
    """Immutable verifier projection of one selected profile."""

    canonical_profile_bytes: bytes = field(repr=False)
    profile_artifact_type: str
    profile_contract_sha256: str
    profile_id: str
    semantic_core_contract_sha256: str
    artifact_domain_bindings: tuple
    validation_scope_id: str


@dataclass(frozen=True)
class PortablePredicateRuntimeVerifierEnvelopeV1:
    """Immutable verifier result for envelope-only recognition."""

    canonical_artifact_bytes: bytes = field(repr=False)
    artifact_identity_sha256: str
    artifact_byte_count: int
    artifact_role_id: str
    artifact_family_id: str
    artifact_type: str
    semantic_core_contract_sha256: str
    profile_contract_sha256: str
    validation_scope_id: str
    nested_payload_semantics_validated: bool


class _DuplicateKeyError(ValueError):
    pass


def _reject(
    code: PortablePredicateRuntimeEnvelopeVerificationCode,
) -> None:
    raise PortablePredicateRuntimeEnvelopeVerificationError(code) from None


def _unique_object(pairs: list) -> dict:
    decoded = {}
    for key, value in pairs:
        if key in decoded:
            raise _DuplicateKeyError
        decoded[key] = value
    return decoded


def _reject_constant(_: str) -> None:
    raise ValueError


def _reject_float(_: str) -> None:
    raise ValueError


def _bounded_integer(value: str) -> int:
    if len(value.lstrip("-")) > _MAXIMUM_JSON_INTEGER_DIGITS:
        raise ValueError
    return int(value)


def _scan_string_lexeme(raw: bytes, offset: int) -> int:
    cursor = offset + 1
    raw_count = len(raw)
    while cursor < raw_count:
        current = raw[cursor]
        if current == 34:
            return cursor + 1
        if current < 32 or current > 127:
            return -1
        if current != 92:
            cursor += 1
            continue
        cursor += 1
        if cursor == raw_count:
            return -1
        escaped = raw[cursor]
        if escaped in b'"\\/bfnrt':
            cursor += 1
            continue
        if escaped != 117 or cursor + 4 >= raw_count:
            return -1
        hexadecimal = raw[cursor + 1 : cursor + 5]
        if len(hexadecimal) != 4 or any(
            item not in b"0123456789ABCDEFabcdef"
            for item in hexadecimal
        ):
            return -1
        cursor += 5
    return -1


def _scan_number_lexeme(raw: bytes, offset: int) -> tuple:
    cursor = offset
    raw_count = len(raw)
    if raw[cursor] == 45:
        cursor += 1
        if cursor == raw_count:
            return (-1, False)
    first_digit = cursor
    if raw[cursor] == 48:
        cursor += 1
    elif 49 <= raw[cursor] <= 57:
        cursor += 1
        while cursor < raw_count and 48 <= raw[cursor] <= 57:
            cursor += 1
    else:
        return (-1, False)
    forbidden = cursor - first_digit > _MAXIMUM_JSON_INTEGER_DIGITS
    if cursor < raw_count and raw[cursor] == 46:
        forbidden = True
        cursor += 1
        digits_begin = cursor
        while cursor < raw_count and 48 <= raw[cursor] <= 57:
            cursor += 1
        if cursor == digits_begin:
            return (-1, False)
    if cursor < raw_count and raw[cursor] in (69, 101):
        forbidden = True
        cursor += 1
        if cursor < raw_count and raw[cursor] in (43, 45):
            cursor += 1
        digits_begin = cursor
        while cursor < raw_count and 48 <= raw[cursor] <= 57:
            cursor += 1
        if cursor == digits_begin:
            return (-1, False)
    return (cursor, forbidden)


def _decode_key_lexeme(
    raw: bytes,
    begin: int,
    end: int,
) -> object:
    try:
        lexeme = raw[begin:end].decode("ascii", "strict")
        key, consumed = json.decoder.scanstring(lexeme, 1, True)
    except (UnicodeError, ValueError):
        return None
    if consumed != len(lexeme) or type(key) is not str:
        return None
    return key


def _preflight_json(raw: bytes) -> str:
    """Check full grammar and resource counts before JSON tree allocation."""

    array_initial = 1
    array_required = 2
    array_separator = 3
    object_initial = 4
    object_required = 5
    object_colon = 6
    object_value = 7
    object_separator = 8
    document_value = 9
    document_end = 10

    frames = bytearray()
    document_state = document_value
    cursor = 0
    values_seen = 0
    resource_exceeded = False
    contract_json_invalid = False
    keys_at_frame = {}
    whitespace_bytes = (32, 9, 10, 13)
    raw_count = len(raw)

    while True:
        while cursor < raw_count and raw[cursor] in whitespace_bytes:
            cursor += 1
        state = frames[-1] if frames else document_state

        if not frames and state == document_end:
            if cursor != raw_count:
                return "syntax-invalid"
            if contract_json_invalid:
                return "syntax-invalid"
            return (
                "resource-invalid"
                if resource_exceeded
                else "valid"
            )

        if state in (object_initial, object_required):
            if (
                state == object_initial
                and cursor < raw_count
                and raw[cursor] == 125
            ):
                keys_at_frame.pop(len(frames) - 1, None)
                frames.pop()
                cursor += 1
                continue
            if cursor == raw_count or raw[cursor] != 34:
                return "syntax-invalid"
            key_begin = cursor
            cursor = _scan_string_lexeme(raw, key_begin)
            if cursor < 0:
                return "syntax-invalid"
            if not resource_exceeded:
                decoded_key = _decode_key_lexeme(
                    raw,
                    key_begin,
                    cursor,
                )
                if decoded_key is None:
                    return "syntax-invalid"
                keys = keys_at_frame.setdefault(
                    len(frames) - 1,
                    set(),
                )
                if decoded_key in keys:
                    contract_json_invalid = True
                else:
                    keys.add(decoded_key)
            frames[-1] = object_colon
            continue

        if state == object_colon:
            if cursor == raw_count or raw[cursor] != 58:
                return "syntax-invalid"
            frames[-1] = object_value
            cursor += 1
            continue

        if state in (array_separator, object_separator):
            terminator = 93 if state == array_separator else 125
            if cursor < raw_count and raw[cursor] == terminator:
                if state == object_separator:
                    keys_at_frame.pop(len(frames) - 1, None)
                frames.pop()
                cursor += 1
                continue
            if cursor == raw_count or raw[cursor] != 44:
                return "syntax-invalid"
            frames[-1] = (
                array_required
                if state == array_separator
                else object_required
            )
            cursor += 1
            continue

        if state not in (
            document_value,
            array_initial,
            array_required,
            object_value,
        ):
            return "syntax-invalid"
        if (
            state == array_initial
            and cursor < raw_count
            and raw[cursor] == 93
        ):
            frames.pop()
            cursor += 1
            continue
        if cursor == raw_count:
            return "syntax-invalid"

        values_seen += 1
        value_depth = len(frames) + 1
        if (
            values_seen > _MAXIMUM_JSON_ITEMS
            or value_depth > _MAXIMUM_JSON_DEPTH
        ):
            resource_exceeded = True
        if not frames:
            document_state = document_end
        elif state in (array_initial, array_required):
            frames[-1] = array_separator
        else:
            frames[-1] = object_separator

        current = raw[cursor]
        if current == 123:
            frames.append(object_initial)
            if not resource_exceeded:
                keys_at_frame[len(frames) - 1] = set()
            cursor += 1
        elif current == 91:
            frames.append(array_initial)
            cursor += 1
        elif current == 34:
            cursor = _scan_string_lexeme(raw, cursor)
            if cursor < 0:
                return "syntax-invalid"
        elif current == 45 or 48 <= current <= 57:
            cursor, forbidden = _scan_number_lexeme(raw, cursor)
            if cursor < 0:
                return "syntax-invalid"
            contract_json_invalid = contract_json_invalid or forbidden
        elif raw.startswith(b"true", cursor):
            cursor += 4
        elif raw.startswith(b"false", cursor):
            cursor += 5
        elif raw.startswith(b"null", cursor):
            cursor += 4
        else:
            return "syntax-invalid"


def _json_string_size(value: str, remaining: int) -> int:
    if remaining < 0:
        return 0
    if remaining < 2:
        return remaining + 1
    if len(value) > remaining - 2:
        return remaining + 1
    size = 2
    for character in value:
        codepoint = ord(character)
        if character in '"\\\b\f\n\r\t':
            size += 2
        elif codepoint < 0x20:
            size += 6
        elif codepoint <= 0x7E:
            size += 1
        elif codepoint <= 0xFFFF:
            size += 6
        else:
            size += 12
        if size > remaining:
            return size
    return size


def _bounded_tree_status(root: object) -> str:
    """Independently enforce the frozen core's exact-JSON convention."""

    item_count = 0
    encoded_size = 0
    active_ids = set()
    stack = []
    current = root
    depth = 1
    while True:
        item_count += 1
        if (
            item_count > _MAXIMUM_JSON_ITEMS
            or depth > _MAXIMUM_JSON_DEPTH
        ):
            return "resource-invalid"

        kind = type(current)
        if kind is str:
            encoded_size += _json_string_size(
                current,
                _MAXIMUM_ARTIFACT_BYTES - encoded_size,
            )
        elif kind is bool:
            encoded_size += 4 if current else 5
        elif kind is int:
            if abs(current) >= 10**_MAXIMUM_JSON_INTEGER_DIGITS:
                return "tree-invalid"
            encoded_size += len(str(current))
        elif kind in (list, dict):
            identity = id(current)
            if identity in active_ids:
                return "tree-invalid"
            if len(current) > _MAXIMUM_JSON_ITEMS - item_count:
                return "resource-invalid"
            count = len(current)
            encoded_size += (
                2
                + max(count - 1, 0)
                + (count if kind is dict else 0)
            )
            if kind is dict:
                if any(type(key) is not str for key in current):
                    return "tree-invalid"
                for key in current:
                    encoded_size += _json_string_size(
                        key,
                        _MAXIMUM_ARTIFACT_BYTES - encoded_size,
                    )
                    if encoded_size > _MAXIMUM_ARTIFACT_BYTES:
                        return "resource-invalid"
                children = iter(current.values())
            else:
                children = iter(current)
            active_ids.add(identity)
            stack.append((children, depth + 1, identity))
        else:
            return "tree-invalid"

        if encoded_size > _MAXIMUM_ARTIFACT_BYTES:
            return "resource-invalid"

        while stack:
            children, child_depth, identity = stack[-1]
            try:
                current = next(children)
            except StopIteration:
                stack.pop()
                active_ids.remove(identity)
                continue
            except RuntimeError:
                return "tree-invalid"
            depth = child_depth
            break
        else:
            return "valid"


def _decode_json(
    value: bytes,
    *,
    resource_code: PortablePredicateRuntimeEnvelopeVerificationCode,
    json_code: PortablePredicateRuntimeEnvelopeVerificationCode,
    tree_code: PortablePredicateRuntimeEnvelopeVerificationCode,
) -> object:
    if not value or len(value) > _MAXIMUM_ARTIFACT_BYTES:
        _reject(resource_code)
    preflight = _preflight_json(value)
    if preflight == "syntax-invalid":
        _reject(json_code)
    if preflight != "valid":
        _reject(resource_code)
    try:
        decoded = json.loads(
            value.decode("ascii", "strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
            parse_int=_bounded_integer,
        )
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _reject(json_code)
    status = _bounded_tree_status(decoded)
    if status == "resource-invalid":
        _reject(resource_code)
    if status != "valid":
        _reject(tree_code)
    return decoded


def _append_u16_escape(encoded: bytearray, codepoint: int) -> None:
    hexadecimal = b"0123456789abcdef"
    encoded.extend(b"\\u")
    encoded.append(hexadecimal[(codepoint >> 12) & 0xF])
    encoded.append(hexadecimal[(codepoint >> 8) & 0xF])
    encoded.append(hexadecimal[(codepoint >> 4) & 0xF])
    encoded.append(hexadecimal[codepoint & 0xF])


def _append_canonical_string(encoded: bytearray, value: str) -> None:
    short_escapes = {
        0x08: b"\\b",
        0x09: b"\\t",
        0x0A: b"\\n",
        0x0C: b"\\f",
        0x0D: b"\\r",
    }
    encoded.append(0x22)
    for character in value:
        codepoint = ord(character)
        if codepoint == 0x22:
            encoded.extend(b'\\"')
        elif codepoint == 0x5C:
            encoded.extend(b"\\\\")
        elif codepoint in short_escapes:
            encoded.extend(short_escapes[codepoint])
        elif codepoint < 0x20:
            _append_u16_escape(encoded, codepoint)
        elif codepoint <= 0x7E:
            encoded.append(codepoint)
        elif codepoint <= 0xFFFF:
            _append_u16_escape(encoded, codepoint)
        else:
            adjusted = codepoint - 0x10000
            _append_u16_escape(
                encoded,
                0xD800 + (adjusted >> 10),
            )
            _append_u16_escape(
                encoded,
                0xDC00 + (adjusted & 0x3FF),
            )
    encoded.append(0x22)


def _append_canonical_value(encoded: bytearray, value: object) -> None:
    kind = type(value)
    if kind is str:
        _append_canonical_string(encoded, value)
        return
    if kind is bool:
        encoded.extend(b"true" if value else b"false")
        return
    if kind is int:
        encoded.extend(str(value).encode("ascii", "strict"))
        return
    if kind is list:
        encoded.append(0x5B)
        for index, item in enumerate(value):
            if index:
                encoded.append(0x2C)
            _append_canonical_value(encoded, item)
        encoded.append(0x5D)
        return
    if kind is dict:
        encoded.append(0x7B)
        for index, key in enumerate(sorted(value)):
            if type(key) is not str:
                _reject(
                    PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL
                )
            if index:
                encoded.append(0x2C)
            _append_canonical_string(encoded, key)
            encoded.append(0x3A)
            _append_canonical_value(encoded, value[key])
        encoded.append(0x7D)
        return
    _reject(PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL)


def _encode_canonical(value: object) -> bytes:
    encoded = bytearray()
    try:
        _append_canonical_value(encoded, value)
    except PortablePredicateRuntimeEnvelopeVerificationError:
        raise
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _reject(PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL)
    return bytes(encoded)


def _framed_digest(domain: str, payload: bytes) -> str:
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except (AttributeError, UnicodeError):
        _reject(PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL)
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _identifier(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        return False
    return (
        1 <= len(encoded) <= _MAXIMUM_IDENTIFIER_BYTES
        and _IDENTIFIER_RE.fullmatch(value) is not None
    )


def _empty_or_identifier(value: object) -> bool:
    return value == "" or _identifier(value)


def _sha256(value: object) -> bool:
    return type(value) is str and _SHA256_RE.fullmatch(value) is not None


def _payload_hex(value: object) -> bool:
    return (
        type(value) is str
        and _PAYLOAD_HEX_RE.fullmatch(value) is not None
    )


def _nonzero_nonce(value: object) -> bool:
    return (
        type(value) is str
        and _CONTEXT_NONCE_RE.fullmatch(value) is not None
        and value != "0" * 64
    )


def _compile_profile_snapshot(
    profile_contract_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> CompiledPortablePredicateRuntimeVerifierProfileV1:
    if (
        type(profile_contract_bytes) is not bytes
        or not _identifier(expected_profile_artifact_type)
        or not _sha256(expected_profile_contract_sha256)
    ):
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_INPUT_TYPE
        )
    decoded = _decode_json(
        profile_contract_bytes,
        resource_code=(
            PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_INPUT_RESOURCE
        ),
        json_code=(
            PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_JSON_INVALID
        ),
        tree_code=(
            PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_JSON_TREE_INVALID
        ),
    )
    canonical = _encode_canonical(decoded)
    if profile_contract_bytes != canonical:
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_CANONICAL_MISMATCH
        )
    if type(decoded) is not dict:
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_SCHEMA_INVALID
        )
    validated = None
    schema_failure = False
    internal_failure = False
    try:
        validated = (
            _verified_core.validate_portable_predicate_profile_verifier_tree(
                decoded
            )
        )
    except _verified_core.PortablePredicateLanguageCoreVerificationError:
        schema_failure = True
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        schema_failure = True
    except MemoryError:
        raise
    except Exception:
        internal_failure = True
    if internal_failure:
        _reject(PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL)
    if schema_failure or type(validated) is not dict:
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_SCHEMA_INVALID
        )
    if (
        _bounded_tree_status(validated) != "valid"
        or _encode_canonical(validated) != canonical
    ):
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_SCHEMA_INVALID
        )
    if (
        validated["artifact_type"] != expected_profile_artifact_type
        or _framed_digest(validated["artifact_type"], canonical)
        != expected_profile_contract_sha256
    ):
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.PROFILE_BINDING_MISMATCH
        )
    bindings = tuple(
        (
            row["artifact_role_id"],
            row["artifact_type_id"],
            row["digest_domain_id"],
            row["identity_semantics_id"],
        )
        for row in validated["artifact_domain_rows"]
    )
    return CompiledPortablePredicateRuntimeVerifierProfileV1(
        canonical_profile_bytes=canonical,
        profile_artifact_type=validated["artifact_type"],
        profile_contract_sha256=expected_profile_contract_sha256,
        profile_id=validated["profile_id"],
        semantic_core_contract_sha256=validated["core_contract_sha256"],
        artifact_domain_bindings=bindings,
        validation_scope_id=(
            PORTABLE_PREDICATE_RUNTIME_ENVELOPE_VALIDATION_SCOPE_ID
        ),
    )


def compile_portable_predicate_runtime_verifier_profile_v1(
    profile_contract_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> CompiledPortablePredicateRuntimeVerifierProfileV1:
    """Compile one selected profile through the verifier-side core."""

    return _compile_profile_snapshot(
        profile_contract_bytes,
        expected_profile_artifact_type=expected_profile_artifact_type,
        expected_profile_contract_sha256=(
            expected_profile_contract_sha256
        ),
    )


def _exact_compiled_profile_snapshot(
    value: object,
) -> object:
    if type(value) is not CompiledPortablePredicateRuntimeVerifierProfileV1:
        return None
    try:
        projected = (
            value.canonical_profile_bytes,
            value.profile_artifact_type,
            value.profile_contract_sha256,
            value.profile_id,
            value.semantic_core_contract_sha256,
            value.artifact_domain_bindings,
            value.validation_scope_id,
        )
    except Exception:
        return None
    (
        canonical_profile_bytes,
        profile_artifact_type,
        profile_contract_sha256,
        profile_id,
        semantic_core_contract_sha256,
        artifact_domain_bindings,
        validation_scope_id,
    ) = projected
    if not (
        type(canonical_profile_bytes) is bytes
        and type(profile_artifact_type) is str
        and type(profile_contract_sha256) is str
        and type(profile_id) is str
        and type(semantic_core_contract_sha256) is str
        and type(artifact_domain_bindings) is tuple
        and all(
            type(row) is tuple
            and len(row) == 4
            and all(type(item) is str for item in row)
            for row in artifact_domain_bindings
        )
        and type(validation_scope_id) is str
    ):
        return None
    return CompiledPortablePredicateRuntimeVerifierProfileV1(
        canonical_profile_bytes=canonical_profile_bytes,
        profile_artifact_type=profile_artifact_type,
        profile_contract_sha256=profile_contract_sha256,
        profile_id=profile_id,
        semantic_core_contract_sha256=semantic_core_contract_sha256,
        artifact_domain_bindings=artifact_domain_bindings,
        validation_scope_id=validation_scope_id,
    )


def _compiled_profiles_match_exactly(
    left: CompiledPortablePredicateRuntimeVerifierProfileV1,
    right: CompiledPortablePredicateRuntimeVerifierProfileV1,
) -> bool:
    return (
        left.canonical_profile_bytes == right.canonical_profile_bytes
        and left.profile_artifact_type == right.profile_artifact_type
        and left.profile_contract_sha256 == right.profile_contract_sha256
        and left.profile_id == right.profile_id
        and left.semantic_core_contract_sha256
        == right.semantic_core_contract_sha256
        and left.artifact_domain_bindings == right.artifact_domain_bindings
        and left.validation_scope_id == right.validation_scope_id
    )


def _revalidate_profile_snapshot(
    compiled_profile: object,
) -> CompiledPortablePredicateRuntimeVerifierProfileV1:
    snapshot = _exact_compiled_profile_snapshot(compiled_profile)
    if snapshot is None:
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.COMPILED_PROFILE_INVALID
        )
    revalidation_failure_code = None
    try:
        rebuilt = _compile_profile_snapshot(
            snapshot.canonical_profile_bytes,
            expected_profile_artifact_type=(
                snapshot.profile_artifact_type
            ),
            expected_profile_contract_sha256=(
                snapshot.profile_contract_sha256
            ),
        )
    except PortablePredicateRuntimeEnvelopeVerificationError as error:
        revalidation_failure_code = error.code
    if (
        revalidation_failure_code
        == PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL.value
    ):
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL
        )
    if revalidation_failure_code is not None:
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.COMPILED_PROFILE_INVALID
        )
    if not _compiled_profiles_match_exactly(snapshot, rebuilt):
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.COMPILED_PROFILE_INVALID
        )
    return rebuilt


def _field_schemas(core_tree: dict) -> dict:
    by_field = {}
    for schema in core_tree["field_value_schema_rows"]:
        for field_id in schema["field_ids"]:
            if field_id in by_field:
                _reject(
                    PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL
                )
            by_field[field_id] = schema["value_schema_id"]
    return by_field


def _valid_field_value(schema_id: str, value: object) -> bool:
    if schema_id == "fixed-format-version-v1":
        return type(value) is str and value == "1"
    if schema_id == "strict-identifier-string-v1":
        return _identifier(value)
    if schema_id == "empty-or-strict-identifier-string-v1":
        return _empty_or_identifier(value)
    if schema_id == "lowercase-sha256-string-v1":
        return _sha256(value)
    if schema_id == "empty-or-lowercase-sha256-string-v1":
        return value == "" or _sha256(value)
    if schema_id == "canonical-payload-hex-string-v1":
        return _payload_hex(value)
    if schema_id == "nonzero-context-nonce-hex-string-v1":
        return _nonzero_nonce(value)
    if schema_id == "nonnegative-index-or-count-integer-v1":
        return type(value) is int and value >= 0
    if schema_id == "declared-claim-boolean-v1":
        return type(value) is bool
    if schema_id == "ordered-identifier-array-v1":
        return (
            type(value) is list
            and all(_identifier(item) for item in value)
        )
    if schema_id == "ordered-index-array-v1":
        return (
            type(value) is list
            and all(type(item) is int and item >= 0 for item in value)
        )
    if schema_id == "ordered-exact-object-row-array-v1":
        return (
            type(value) is list
            and all(type(item) is dict for item in value)
        )
    if schema_id == "context-refined-exact-object-v1":
        return type(value) is dict
    _reject(PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL)


def _family_for_role(core_tree: dict, role_id: str) -> dict:
    matching = [
        row
        for row in core_tree["artifact_family_rows"]
        if row["artifact_role_id"] == role_id
    ]
    if len(matching) != 1:
        _reject(PortablePredicateRuntimeEnvelopeVerificationCode.INTERNAL)
    return matching[0]


def _binding_for_role(
    profile: CompiledPortablePredicateRuntimeVerifierProfileV1,
    role_id: str,
) -> tuple:
    matching = [
        row
        for row in profile.artifact_domain_bindings
        if type(row) is tuple and len(row) == 4 and row[0] == role_id
    ]
    if len(matching) != 1:
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.COMPILED_PROFILE_INVALID
        )
    return matching[0]


def verify_portable_predicate_runtime_envelope_v1(
    artifact_bytes: bytes,
    *,
    expected_artifact_role_id: str,
    compiled_profile: CompiledPortablePredicateRuntimeVerifierProfileV1,
) -> PortablePredicateRuntimeVerifierEnvelopeV1:
    """Independently recognize one canonical top-level runtime envelope.

    Acceptance does not validate any nested purpose, locator, type, payload,
    graph, input, evaluation, fault, result, or claim semantics.
    """

    if type(artifact_bytes) is not bytes:
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_INPUT_TYPE
        )
    if type(expected_artifact_role_id) is not str:
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.EXPECTED_ROLE_INVALID
        )
    profile = _revalidate_profile_snapshot(compiled_profile)
    core_tree = (
        _verified_core.portable_predicate_language_core_verifier_contract_tree()
    )
    required_roles = tuple(
        core_tree["profile_interface"][
            "required_runtime_artifact_role_ids"
        ]
    )
    if expected_artifact_role_id not in required_roles:
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.EXPECTED_ROLE_INVALID
        )
    decoded = _decode_json(
        artifact_bytes,
        resource_code=(
            PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_INPUT_RESOURCE
        ),
        json_code=(
            PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_JSON_INVALID
        ),
        tree_code=(
            PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_JSON_TREE_INVALID
        ),
    )
    canonical = _encode_canonical(decoded)
    if artifact_bytes != canonical:
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_CANONICAL_MISMATCH
        )
    if type(decoded) is not dict:
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_SCHEMA_INVALID
        )

    family = _family_for_role(core_tree, expected_artifact_role_id)
    schemas = _field_schemas(core_tree)
    common_fields = (
        "artifact_type",
        "format_version",
        "semantic_core_contract_sha256",
        "profile_contract_sha256",
    )
    if any(field_id not in decoded for field_id in common_fields):
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_SCHEMA_INVALID
        )
    for field_id in common_fields:
        schema_id = schemas.get(field_id)
        if (
            schema_id is None
            or not _valid_field_value(schema_id, decoded[field_id])
        ):
            _reject(
                PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_SCHEMA_INVALID
            )

    binding = _binding_for_role(profile, expected_artifact_role_id)
    (
        _,
        selected_artifact_type,
        selected_digest_domain,
        selected_identity_semantics,
    ) = binding
    if (
        selected_identity_semantics != "DOMAIN_SEPARATED_SHA256"
        or decoded["artifact_type"] != selected_artifact_type
        or decoded["semantic_core_contract_sha256"]
        != profile.semantic_core_contract_sha256
        or decoded["profile_contract_sha256"]
        != profile.profile_contract_sha256
    ):
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_BINDING_MISMATCH
        )

    exact_fields = tuple(family["exact_field_ids"])
    if set(decoded) != set(exact_fields):
        _reject(
            PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_SCHEMA_INVALID
        )
    for field_id in exact_fields:
        schema_id = schemas.get(field_id)
        if (
            schema_id is None
            or not _valid_field_value(schema_id, decoded[field_id])
        ):
            _reject(
                PortablePredicateRuntimeEnvelopeVerificationCode.ARTIFACT_SCHEMA_INVALID
            )

    return PortablePredicateRuntimeVerifierEnvelopeV1(
        canonical_artifact_bytes=canonical,
        artifact_identity_sha256=_framed_digest(
            selected_digest_domain,
            canonical,
        ),
        artifact_byte_count=len(canonical),
        artifact_role_id=expected_artifact_role_id,
        artifact_family_id=family["artifact_family_id"],
        artifact_type=selected_artifact_type,
        semantic_core_contract_sha256=(
            profile.semantic_core_contract_sha256
        ),
        profile_contract_sha256=profile.profile_contract_sha256,
        validation_scope_id=(
            PORTABLE_PREDICATE_RUNTIME_ENVELOPE_VALIDATION_SCOPE_ID
        ),
        nested_payload_semantics_validated=False,
    )
