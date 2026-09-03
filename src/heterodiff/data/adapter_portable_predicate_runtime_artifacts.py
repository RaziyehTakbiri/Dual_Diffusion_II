"""Canonical envelopes for portable predicate runtime artifacts.

This module implements only the Checkpoint-56A envelope boundary.  It compiles
an immutable snapshot of one selected profile and recognizes the canonical
top-level envelope of the five runtime artifact families.  It does not validate
nested program semantics, resolve inputs, execute constructors or predicates,
validate result claims, or establish an empirical result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import re
from typing import Final

from heterodiff.data import adapter_portable_predicate_language_core as _core


__all__ = (
    "CompiledPortablePredicateRuntimeProfileV1",
    "PortablePredicateRuntimeEnvelopeCode",
    "PortablePredicateRuntimeEnvelopeError",
    "PortablePredicateRuntimeEnvelopeV1",
    "compile_portable_predicate_runtime_profile_v1",
    "parse_portable_predicate_runtime_envelope_v1",
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


class PortablePredicateRuntimeEnvelopeCode(str, Enum):
    """Closed failures for the Checkpoint-56A envelope boundary."""

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
    PortablePredicateRuntimeEnvelopeCode.PROFILE_INPUT_TYPE: (
        "portable predicate runtime profile input has an invalid exact type"
    ),
    PortablePredicateRuntimeEnvelopeCode.PROFILE_INPUT_RESOURCE: (
        "portable predicate runtime profile input exceeds its resource ceiling"
    ),
    PortablePredicateRuntimeEnvelopeCode.PROFILE_JSON_INVALID: (
        "portable predicate runtime profile JSON is invalid"
    ),
    PortablePredicateRuntimeEnvelopeCode.PROFILE_JSON_TREE_INVALID: (
        "portable predicate runtime profile JSON tree is inadmissible"
    ),
    PortablePredicateRuntimeEnvelopeCode.PROFILE_CANONICAL_MISMATCH: (
        "portable predicate runtime profile bytes are not canonical"
    ),
    PortablePredicateRuntimeEnvelopeCode.PROFILE_SCHEMA_INVALID: (
        "portable predicate runtime profile schema is invalid"
    ),
    PortablePredicateRuntimeEnvelopeCode.PROFILE_BINDING_MISMATCH: (
        "portable predicate runtime profile selection pins do not match"
    ),
    PortablePredicateRuntimeEnvelopeCode.COMPILED_PROFILE_INVALID: (
        "portable predicate runtime compiled profile is invalid"
    ),
    PortablePredicateRuntimeEnvelopeCode.ARTIFACT_INPUT_TYPE: (
        "portable predicate runtime artifact input has an invalid exact type"
    ),
    PortablePredicateRuntimeEnvelopeCode.EXPECTED_ROLE_INVALID: (
        "portable predicate runtime expected artifact role is invalid"
    ),
    PortablePredicateRuntimeEnvelopeCode.ARTIFACT_INPUT_RESOURCE: (
        "portable predicate runtime artifact exceeds its resource ceiling"
    ),
    PortablePredicateRuntimeEnvelopeCode.ARTIFACT_JSON_INVALID: (
        "portable predicate runtime artifact JSON is invalid"
    ),
    PortablePredicateRuntimeEnvelopeCode.ARTIFACT_JSON_TREE_INVALID: (
        "portable predicate runtime artifact JSON tree is inadmissible"
    ),
    PortablePredicateRuntimeEnvelopeCode.ARTIFACT_CANONICAL_MISMATCH: (
        "portable predicate runtime artifact bytes are not canonical"
    ),
    PortablePredicateRuntimeEnvelopeCode.ARTIFACT_SCHEMA_INVALID: (
        "portable predicate runtime artifact envelope schema is invalid"
    ),
    PortablePredicateRuntimeEnvelopeCode.ARTIFACT_BINDING_MISMATCH: (
        "portable predicate runtime artifact profile binding does not match"
    ),
    PortablePredicateRuntimeEnvelopeCode.INTERNAL: (
        "portable predicate runtime envelope implementation is inconsistent"
    ),
}


class PortablePredicateRuntimeEnvelopeError(ValueError):
    """One fixed-message Checkpoint-56A envelope failure."""

    def __init__(self, code: PortablePredicateRuntimeEnvelopeCode):
        self.code = code.value
        super().__init__(_ERROR_MESSAGES[code])


@dataclass(frozen=True)
class CompiledPortablePredicateRuntimeProfileV1:
    """Immutable envelope-relevant projection of one validated profile."""

    canonical_profile_bytes: bytes = field(repr=False)
    profile_artifact_type: str
    profile_contract_sha256: str
    profile_id: str
    semantic_core_contract_sha256: str
    artifact_domain_bindings: tuple
    validation_scope_id: str


@dataclass(frozen=True)
class PortablePredicateRuntimeEnvelopeV1:
    """Immutable result of envelope-only runtime artifact recognition."""

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


def _fail(code: PortablePredicateRuntimeEnvelopeCode) -> None:
    raise PortablePredicateRuntimeEnvelopeError(code) from None


def _object_without_duplicates(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _reject_json_constant(_: str) -> None:
    raise ValueError


def _reject_json_float(_: str) -> None:
    raise ValueError


def _bounded_json_integer(value: str) -> int:
    if len(value.lstrip("-")) > _MAXIMUM_JSON_INTEGER_DIGITS:
        raise ValueError
    return int(value)


def _scan_json_string_token(value: bytes, start: int) -> int:
    index = start + 1
    while index < len(value):
        byte = value[index]
        if byte == 0x22:
            return index + 1
        if byte < 0x20 or byte >= 0x80:
            return -1
        if byte != 0x5C:
            index += 1
            continue
        index += 1
        if index >= len(value):
            return -1
        escape = value[index]
        if escape in b'"\\/bfnrt':
            index += 1
            continue
        if escape != 0x75 or index + 4 >= len(value):
            return -1
        if any(
            digit not in b"0123456789abcdefABCDEF"
            for digit in value[index + 1 : index + 5]
        ):
            return -1
        index += 5
    return -1


def _scan_json_number_token(value: bytes, start: int) -> tuple:
    index = start
    if value[index] == 0x2D:
        index += 1
        if index >= len(value):
            return (-1, False)
    integer_start = index
    if value[index] == 0x30:
        index += 1
    elif 0x31 <= value[index] <= 0x39:
        index += 1
        while index < len(value) and 0x30 <= value[index] <= 0x39:
            index += 1
    else:
        return (-1, False)
    integer_is_overlong = (
        index - integer_start > _MAXIMUM_JSON_INTEGER_DIGITS
    )
    forbidden_float = False
    if index < len(value) and value[index] == 0x2E:
        forbidden_float = True
        index += 1
        fraction_start = index
        while index < len(value) and 0x30 <= value[index] <= 0x39:
            index += 1
        if index == fraction_start:
            return (-1, False)
    if index < len(value) and value[index] in (0x45, 0x65):
        forbidden_float = True
        index += 1
        if index < len(value) and value[index] in (0x2B, 0x2D):
            index += 1
        exponent_start = index
        while index < len(value) and 0x30 <= value[index] <= 0x39:
            index += 1
        if index == exponent_start:
            return (-1, False)
    return (index, integer_is_overlong or forbidden_float)


def _decode_json_key_token(
    value: bytes,
    start: int,
    end: int,
) -> object:
    try:
        token = value[start:end].decode("ascii", "strict")
        decoded, consumed = json.decoder.scanstring(token, 1, True)
    except (UnicodeError, ValueError):
        return None
    if consumed != len(token) or type(decoded) is not str:
        return None
    return decoded


def _bounded_json_preflight_status(value: bytes) -> str:
    """Validate syntax and bound values before allocating a decoded tree."""

    array_first = 1
    array_value = 2
    array_after = 3
    object_first_key = 4
    object_key = 5
    object_colon = 6
    object_value = 7
    object_after = 8
    root_value = 9
    root_after = 10

    stack = bytearray()
    root_state = root_value
    index = 0
    item_count = 0
    resource_invalid = False
    contract_json_invalid = False
    object_key_sets = {}
    whitespace = (0x20, 0x09, 0x0A, 0x0D)

    while True:
        while index < len(value) and value[index] in whitespace:
            index += 1
        state = stack[-1] if stack else root_state

        if not stack and state == root_after:
            if index != len(value):
                return "syntax-invalid"
            if contract_json_invalid:
                return "syntax-invalid"
            return "resource-invalid" if resource_invalid else "valid"

        if state in (object_first_key, object_key):
            if (
                state == object_first_key
                and index < len(value)
                and value[index] == 0x7D
            ):
                object_key_sets.pop(len(stack) - 1, None)
                stack.pop()
                index += 1
                continue
            if index >= len(value) or value[index] != 0x22:
                return "syntax-invalid"
            key_start = index
            index = _scan_json_string_token(value, key_start)
            if index < 0:
                return "syntax-invalid"
            if not resource_invalid:
                decoded_key = _decode_json_key_token(
                    value,
                    key_start,
                    index,
                )
                if decoded_key is None:
                    return "syntax-invalid"
                key_set = object_key_sets.setdefault(
                    len(stack) - 1,
                    set(),
                )
                if decoded_key in key_set:
                    contract_json_invalid = True
                else:
                    key_set.add(decoded_key)
            stack[-1] = object_colon
            continue

        if state == object_colon:
            if index >= len(value) or value[index] != 0x3A:
                return "syntax-invalid"
            stack[-1] = object_value
            index += 1
            continue

        if state in (array_after, object_after):
            closing = 0x5D if state == array_after else 0x7D
            if index < len(value) and value[index] == closing:
                if state == object_after:
                    object_key_sets.pop(len(stack) - 1, None)
                stack.pop()
                index += 1
                continue
            if index >= len(value) or value[index] != 0x2C:
                return "syntax-invalid"
            stack[-1] = (
                array_value if state == array_after else object_key
            )
            index += 1
            continue

        if state not in (
            root_value,
            array_first,
            array_value,
            object_value,
        ):
            return "syntax-invalid"
        if (
            state == array_first
            and index < len(value)
            and value[index] == 0x5D
        ):
            stack.pop()
            index += 1
            continue
        if index >= len(value):
            return "syntax-invalid"

        item_count += 1
        depth = len(stack) + 1
        if item_count > _MAXIMUM_JSON_ITEMS or depth > _MAXIMUM_JSON_DEPTH:
            resource_invalid = True
        if not stack:
            root_state = root_after
        elif state in (array_first, array_value):
            stack[-1] = array_after
        else:
            stack[-1] = object_after

        byte = value[index]
        if byte == 0x7B:
            stack.append(object_first_key)
            if not resource_invalid:
                object_key_sets[len(stack) - 1] = set()
            index += 1
        elif byte == 0x5B:
            stack.append(array_first)
            index += 1
        elif byte == 0x22:
            index = _scan_json_string_token(value, index)
            if index < 0:
                return "syntax-invalid"
        elif byte == 0x2D or 0x30 <= byte <= 0x39:
            index, invalid_number = _scan_json_number_token(value, index)
            if index < 0:
                return "syntax-invalid"
            contract_json_invalid = (
                contract_json_invalid or invalid_number
            )
        elif value.startswith(b"true", index):
            index += 4
        elif value.startswith(b"false", index):
            index += 5
        elif value.startswith(b"null", index):
            index += 4
        else:
            return "syntax-invalid"


def _json_string_byte_count(value: str, maximum: int) -> int:
    if maximum < 0:
        return 0
    if maximum < 2:
        return maximum + 1
    if len(value) > maximum - 2:
        return maximum + 1
    count = 2
    for character in value:
        codepoint = ord(character)
        if character in '"\\\b\f\n\r\t':
            count += 2
        elif codepoint < 0x20:
            count += 6
        elif codepoint <= 0x7E:
            count += 1
        elif codepoint <= 0xFFFF:
            count += 6
        else:
            count += 12
        if count > maximum:
            return count
    return count


def _bounded_exact_json_status(value: object) -> str:
    """Mirror the frozen core's exact-JSON item and depth convention."""

    item_count = 0
    encoded_byte_count = 0
    active_container_ids = set()
    frames = []
    current = value
    depth = 1
    while True:
        item_count += 1
        if (
            item_count > _MAXIMUM_JSON_ITEMS
            or depth > _MAXIMUM_JSON_DEPTH
        ):
            return "resource-invalid"

        current_type = type(current)
        if current_type is str:
            encoded_byte_count += _json_string_byte_count(
                current,
                _MAXIMUM_ARTIFACT_BYTES - encoded_byte_count,
            )
        elif current_type is bool:
            encoded_byte_count += 4 if current else 5
        elif current_type is int:
            if abs(current) >= 10**_MAXIMUM_JSON_INTEGER_DIGITS:
                return "tree-invalid"
            encoded_byte_count += len(str(current))
        elif current_type in (list, dict):
            container_id = id(current)
            if container_id in active_container_ids:
                return "tree-invalid"
            if len(current) > _MAXIMUM_JSON_ITEMS - item_count:
                return "resource-invalid"
            element_count = len(current)
            encoded_byte_count += (
                2
                + max(element_count - 1, 0)
                + (element_count if current_type is dict else 0)
            )
            if current_type is dict:
                if any(type(key) is not str for key in current):
                    return "tree-invalid"
                for key in current:
                    encoded_byte_count += _json_string_byte_count(
                        key,
                        _MAXIMUM_ARTIFACT_BYTES - encoded_byte_count,
                    )
                    if encoded_byte_count > _MAXIMUM_ARTIFACT_BYTES:
                        return "resource-invalid"
                children = iter(current.values())
            else:
                children = iter(current)
            active_container_ids.add(container_id)
            frames.append((children, depth + 1, container_id))
        else:
            return "tree-invalid"

        if encoded_byte_count > _MAXIMUM_ARTIFACT_BYTES:
            return "resource-invalid"

        while frames:
            children, child_depth, container_id = frames[-1]
            try:
                current = next(children)
            except StopIteration:
                frames.pop()
                active_container_ids.remove(container_id)
                continue
            except RuntimeError:
                return "tree-invalid"
            depth = child_depth
            break
        else:
            return "valid"


def _strict_json(
    value: bytes,
    *,
    resource_code: PortablePredicateRuntimeEnvelopeCode,
    json_code: PortablePredicateRuntimeEnvelopeCode,
    tree_code: PortablePredicateRuntimeEnvelopeCode,
) -> object:
    if not value or len(value) > _MAXIMUM_ARTIFACT_BYTES:
        _fail(resource_code)
    preflight_status = _bounded_json_preflight_status(value)
    if preflight_status == "syntax-invalid":
        _fail(json_code)
    if preflight_status != "valid":
        _fail(resource_code)
    try:
        decoded = json.loads(
            value.decode("ascii", "strict"),
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_json_constant,
            parse_float=_reject_json_float,
            parse_int=_bounded_json_integer,
        )
    except (
        UnicodeError,
        ValueError,
        TypeError,
        RecursionError,
        json.JSONDecodeError,
    ):
        _fail(json_code)
    status = _bounded_exact_json_status(decoded)
    if status == "resource-invalid":
        _fail(resource_code)
    if status != "valid":
        _fail(tree_code)
    return decoded


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _fail(PortablePredicateRuntimeEnvelopeCode.INTERNAL)


def _domain_sha256(domain: str, payload: bytes) -> str:
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except (AttributeError, UnicodeError):
        _fail(PortablePredicateRuntimeEnvelopeCode.INTERNAL)
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _is_identifier(value: object) -> bool:
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


def _is_empty_or_identifier(value: object) -> bool:
    return value == "" or _is_identifier(value)


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and _SHA256_RE.fullmatch(value) is not None
    )


def _is_payload_hex(value: object) -> bool:
    return (
        type(value) is str
        and _PAYLOAD_HEX_RE.fullmatch(value) is not None
    )


def _is_nonzero_context_nonce(value: object) -> bool:
    return (
        type(value) is str
        and _CONTEXT_NONCE_RE.fullmatch(value) is not None
        and value != "0" * 64
    )


def _compile_profile(
    profile_contract_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> CompiledPortablePredicateRuntimeProfileV1:
    if (
        type(profile_contract_bytes) is not bytes
        or not _is_identifier(expected_profile_artifact_type)
        or not _is_sha256(expected_profile_contract_sha256)
    ):
        _fail(PortablePredicateRuntimeEnvelopeCode.PROFILE_INPUT_TYPE)
    decoded = _strict_json(
        profile_contract_bytes,
        resource_code=(
            PortablePredicateRuntimeEnvelopeCode.PROFILE_INPUT_RESOURCE
        ),
        json_code=PortablePredicateRuntimeEnvelopeCode.PROFILE_JSON_INVALID,
        tree_code=(
            PortablePredicateRuntimeEnvelopeCode.PROFILE_JSON_TREE_INVALID
        ),
    )
    canonical = _canonical_json(decoded)
    if profile_contract_bytes != canonical:
        _fail(
            PortablePredicateRuntimeEnvelopeCode.PROFILE_CANONICAL_MISMATCH
        )
    if type(decoded) is not dict:
        _fail(PortablePredicateRuntimeEnvelopeCode.PROFILE_SCHEMA_INVALID)
    validated = None
    schema_failure = False
    internal_failure = False
    try:
        validated = _core.validate_portable_predicate_profile_tree(decoded)
    except _core.PortablePredicateLanguageCoreError:
        schema_failure = True
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        schema_failure = True
    except MemoryError:
        raise
    except Exception:
        internal_failure = True
    if internal_failure:
        _fail(PortablePredicateRuntimeEnvelopeCode.INTERNAL)
    if schema_failure or type(validated) is not dict:
        _fail(PortablePredicateRuntimeEnvelopeCode.PROFILE_SCHEMA_INVALID)
    if (
        _bounded_exact_json_status(validated) != "valid"
        or _canonical_json(validated) != canonical
    ):
        _fail(PortablePredicateRuntimeEnvelopeCode.PROFILE_SCHEMA_INVALID)
    if (
        validated["artifact_type"] != expected_profile_artifact_type
        or _domain_sha256(validated["artifact_type"], canonical)
        != expected_profile_contract_sha256
    ):
        _fail(PortablePredicateRuntimeEnvelopeCode.PROFILE_BINDING_MISMATCH)
    domain_bindings = tuple(
        (
            row["artifact_role_id"],
            row["artifact_type_id"],
            row["digest_domain_id"],
            row["identity_semantics_id"],
        )
        for row in validated["artifact_domain_rows"]
    )
    return CompiledPortablePredicateRuntimeProfileV1(
        canonical_profile_bytes=canonical,
        profile_artifact_type=validated["artifact_type"],
        profile_contract_sha256=expected_profile_contract_sha256,
        profile_id=validated["profile_id"],
        semantic_core_contract_sha256=validated["core_contract_sha256"],
        artifact_domain_bindings=domain_bindings,
        validation_scope_id=(
            PORTABLE_PREDICATE_RUNTIME_ENVELOPE_VALIDATION_SCOPE_ID
        ),
    )


def compile_portable_predicate_runtime_profile_v1(
    profile_contract_bytes: bytes,
    *,
    expected_profile_artifact_type: str,
    expected_profile_contract_sha256: str,
) -> CompiledPortablePredicateRuntimeProfileV1:
    """Compile one exact selected profile into an immutable value snapshot."""

    return _compile_profile(
        profile_contract_bytes,
        expected_profile_artifact_type=expected_profile_artifact_type,
        expected_profile_contract_sha256=(
            expected_profile_contract_sha256
        ),
    )


def _exact_compiled_profile_snapshot(
    value: object,
) -> object:
    if type(value) is not CompiledPortablePredicateRuntimeProfileV1:
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
    return CompiledPortablePredicateRuntimeProfileV1(
        canonical_profile_bytes=canonical_profile_bytes,
        profile_artifact_type=profile_artifact_type,
        profile_contract_sha256=profile_contract_sha256,
        profile_id=profile_id,
        semantic_core_contract_sha256=semantic_core_contract_sha256,
        artifact_domain_bindings=artifact_domain_bindings,
        validation_scope_id=validation_scope_id,
    )


def _compiled_profiles_match_exactly(
    left: CompiledPortablePredicateRuntimeProfileV1,
    right: CompiledPortablePredicateRuntimeProfileV1,
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


def _revalidate_compiled_profile(
    compiled_profile: object,
) -> CompiledPortablePredicateRuntimeProfileV1:
    snapshot = _exact_compiled_profile_snapshot(compiled_profile)
    if snapshot is None:
        _fail(PortablePredicateRuntimeEnvelopeCode.COMPILED_PROFILE_INVALID)
    revalidation_failure_code = None
    try:
        recompiled = _compile_profile(
            snapshot.canonical_profile_bytes,
            expected_profile_artifact_type=(
                snapshot.profile_artifact_type
            ),
            expected_profile_contract_sha256=(
                snapshot.profile_contract_sha256
            ),
        )
    except PortablePredicateRuntimeEnvelopeError as error:
        revalidation_failure_code = error.code
    if (
        revalidation_failure_code
        == PortablePredicateRuntimeEnvelopeCode.INTERNAL.value
    ):
        _fail(PortablePredicateRuntimeEnvelopeCode.INTERNAL)
    if revalidation_failure_code is not None:
        _fail(PortablePredicateRuntimeEnvelopeCode.COMPILED_PROFILE_INVALID)
    if not _compiled_profiles_match_exactly(snapshot, recompiled):
        _fail(PortablePredicateRuntimeEnvelopeCode.COMPILED_PROFILE_INVALID)
    return recompiled


def _field_schema_by_id(core_tree: dict) -> dict:
    result = {}
    for row in core_tree["field_value_schema_rows"]:
        for field_id in row["field_ids"]:
            if field_id in result:
                _fail(PortablePredicateRuntimeEnvelopeCode.INTERNAL)
            result[field_id] = row["value_schema_id"]
    return result


def _field_value_is_valid(value_schema_id: str, value: object) -> bool:
    if value_schema_id == "fixed-format-version-v1":
        return type(value) is str and value == "1"
    if value_schema_id == "strict-identifier-string-v1":
        return _is_identifier(value)
    if value_schema_id == "empty-or-strict-identifier-string-v1":
        return _is_empty_or_identifier(value)
    if value_schema_id == "lowercase-sha256-string-v1":
        return _is_sha256(value)
    if value_schema_id == "empty-or-lowercase-sha256-string-v1":
        return value == "" or _is_sha256(value)
    if value_schema_id == "canonical-payload-hex-string-v1":
        return _is_payload_hex(value)
    if value_schema_id == "nonzero-context-nonce-hex-string-v1":
        return _is_nonzero_context_nonce(value)
    if value_schema_id == "nonnegative-index-or-count-integer-v1":
        return type(value) is int and value >= 0
    if value_schema_id == "declared-claim-boolean-v1":
        return type(value) is bool
    if value_schema_id == "ordered-identifier-array-v1":
        return (
            type(value) is list
            and all(_is_identifier(item) for item in value)
        )
    if value_schema_id == "ordered-index-array-v1":
        return (
            type(value) is list
            and all(type(item) is int and item >= 0 for item in value)
        )
    if value_schema_id == "ordered-exact-object-row-array-v1":
        return (
            type(value) is list
            and all(type(item) is dict for item in value)
        )
    if value_schema_id == "context-refined-exact-object-v1":
        return type(value) is dict
    _fail(PortablePredicateRuntimeEnvelopeCode.INTERNAL)


def _runtime_family_row(core_tree: dict, role_id: str) -> dict:
    rows = [
        row
        for row in core_tree["artifact_family_rows"]
        if row["artifact_role_id"] == role_id
    ]
    if len(rows) != 1:
        _fail(PortablePredicateRuntimeEnvelopeCode.INTERNAL)
    return rows[0]


def _runtime_domain_binding(
    compiled_profile: CompiledPortablePredicateRuntimeProfileV1,
    role_id: str,
) -> tuple:
    rows = [
        row
        for row in compiled_profile.artifact_domain_bindings
        if type(row) is tuple and len(row) == 4 and row[0] == role_id
    ]
    if len(rows) != 1:
        _fail(PortablePredicateRuntimeEnvelopeCode.COMPILED_PROFILE_INVALID)
    return rows[0]


def parse_portable_predicate_runtime_envelope_v1(
    artifact_bytes: bytes,
    *,
    expected_artifact_role_id: str,
    compiled_profile: CompiledPortablePredicateRuntimeProfileV1,
) -> PortablePredicateRuntimeEnvelopeV1:
    """Recognize one canonical top-level runtime envelope.

    Acceptance does not validate any nested purpose, locator, type, payload,
    graph, input, evaluation, fault, result, or claim semantics.
    """

    if type(artifact_bytes) is not bytes:
        _fail(PortablePredicateRuntimeEnvelopeCode.ARTIFACT_INPUT_TYPE)
    if type(expected_artifact_role_id) is not str:
        _fail(PortablePredicateRuntimeEnvelopeCode.EXPECTED_ROLE_INVALID)
    profile = _revalidate_compiled_profile(compiled_profile)
    core_tree = _core.portable_predicate_language_core_contract_tree()
    required_roles = tuple(
        _core.PORTABLE_PREDICATE_LANGUAGE_CORE_REQUIRED_ARTIFACT_ROLE_IDS
    )
    if expected_artifact_role_id not in required_roles:
        _fail(PortablePredicateRuntimeEnvelopeCode.EXPECTED_ROLE_INVALID)
    decoded = _strict_json(
        artifact_bytes,
        resource_code=(
            PortablePredicateRuntimeEnvelopeCode.ARTIFACT_INPUT_RESOURCE
        ),
        json_code=PortablePredicateRuntimeEnvelopeCode.ARTIFACT_JSON_INVALID,
        tree_code=(
            PortablePredicateRuntimeEnvelopeCode.ARTIFACT_JSON_TREE_INVALID
        ),
    )
    canonical = _canonical_json(decoded)
    if artifact_bytes != canonical:
        _fail(
            PortablePredicateRuntimeEnvelopeCode.ARTIFACT_CANONICAL_MISMATCH
        )
    if type(decoded) is not dict:
        _fail(PortablePredicateRuntimeEnvelopeCode.ARTIFACT_SCHEMA_INVALID)

    family_row = _runtime_family_row(
        core_tree,
        expected_artifact_role_id,
    )
    field_schemas = _field_schema_by_id(core_tree)
    common_fields = (
        "artifact_type",
        "format_version",
        "semantic_core_contract_sha256",
        "profile_contract_sha256",
    )
    if any(field_id not in decoded for field_id in common_fields):
        _fail(PortablePredicateRuntimeEnvelopeCode.ARTIFACT_SCHEMA_INVALID)
    for field_id in common_fields:
        value_schema_id = field_schemas.get(field_id)
        if (
            value_schema_id is None
            or not _field_value_is_valid(
                value_schema_id,
                decoded[field_id],
            )
        ):
            _fail(PortablePredicateRuntimeEnvelopeCode.ARTIFACT_SCHEMA_INVALID)

    domain_binding = _runtime_domain_binding(
        profile,
        expected_artifact_role_id,
    )
    (
        _,
        selected_artifact_type,
        selected_digest_domain,
        selected_identity_semantics,
    ) = domain_binding
    if (
        selected_identity_semantics != "DOMAIN_SEPARATED_SHA256"
        or decoded["artifact_type"] != selected_artifact_type
        or decoded["semantic_core_contract_sha256"]
        != profile.semantic_core_contract_sha256
        or decoded["profile_contract_sha256"]
        != profile.profile_contract_sha256
    ):
        _fail(
            PortablePredicateRuntimeEnvelopeCode.ARTIFACT_BINDING_MISMATCH
        )

    exact_field_ids = tuple(family_row["exact_field_ids"])
    if set(decoded) != set(exact_field_ids):
        _fail(PortablePredicateRuntimeEnvelopeCode.ARTIFACT_SCHEMA_INVALID)
    for field_id in exact_field_ids:
        value_schema_id = field_schemas.get(field_id)
        if (
            value_schema_id is None
            or not _field_value_is_valid(
                value_schema_id,
                decoded[field_id],
            )
        ):
            _fail(PortablePredicateRuntimeEnvelopeCode.ARTIFACT_SCHEMA_INVALID)

    return PortablePredicateRuntimeEnvelopeV1(
        canonical_artifact_bytes=canonical,
        artifact_identity_sha256=_domain_sha256(
            selected_digest_domain,
            canonical,
        ),
        artifact_byte_count=len(canonical),
        artifact_role_id=expected_artifact_role_id,
        artifact_family_id=family_row["artifact_family_id"],
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
