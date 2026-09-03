"""Independent supplemental verifier for a Phase-D expected-leaf bundle.

This module is deliberately additive.  It does not modify, reinterpret, or
upgrade the V1 oracle-worker protocol.  Verification first requires the
standalone V1 raw-byte verifier to accept its original eleven inputs.  A
separately supplied canonical JSON bundle is then parsed and checked here.

The successful result is a development-only structural result.  It establishes
that all expected-side Phase-C leaf preimages are present under closed schemas,
that their byte commitments and cross-leaf relations can be rebuilt, and that
the derived compact configuration/evidence/native values equal the V1
response.  It does not authenticate custody, authorship, case authority,
format-specific payload meaning, oracle or adapter execution, containment, or
semantic truth, and it never makes a gate decision.

Only the standard library and the already separate V1 verifier are imported.
No publisher, adapter-contract, evidence, fixture, worker, or ABI helper is
used for bundle parsing, serialization, or digest reconstruction.
"""

from __future__ import annotations

import base64
from collections import Counter
from dataclasses import dataclass, field, fields
from enum import Enum
import hashlib
import json
import math
import re
from types import MappingProxyType
from typing import Dict, List, NamedTuple, Optional, Tuple
import unicodedata

from . import adapter_oracle_independent_verifier as _v1


EXPECTED_LEAF_BUNDLE_ARTIFACT_TYPE = (
    "heterodiff.adapter.expected-evidence-leaf-bundle.v1"
)
EXPECTED_LEAF_BUNDLE_DIGEST_DOMAIN = EXPECTED_LEAF_BUNDLE_ARTIFACT_TYPE
EXPECTED_LEAF_BUNDLE_VERIFICATION_INPUT_DIGEST_DOMAIN = (
    "heterodiff.adapter.development-independent-expected-leaf-bundle-"
    "verification-input.v1"
)
EXPECTED_LEAF_BUNDLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.development-independent-expected-leaf-bundle-"
    "verification-receipt.v1"
)
EXPECTED_LEAF_BUNDLE_VERIFICATION_RECEIPT_DIGEST_DOMAIN = (
    EXPECTED_LEAF_BUNDLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE
)
EXPECTED_LEAF_BUNDLE_VERIFIER_ID = (
    "heterodiff-development-independent-expected-leaf-bundle-verifier-v1"
)
EXPECTED_LEAF_BUNDLE_VERIFIER_IMPLEMENTATION_STATUS = (
    "DEVELOPMENT_ONLY_STANDALONE_EXPECTED_LEAF_SCHEMA_VERIFIER"
)
EXPECTED_LEAF_BUNDLE_VERIFICATION_STATUS = (
    "INDEPENDENT_EXPECTED_LEAF_SCHEMAS_AND_BINDINGS_MATCHED_"
    "UNATTESTED_DEVELOPMENT_EXECUTION"
)
EXPECTED_LEAF_BUNDLE_VERIFIER_DECISION_STATUS = "NOT_MADE_BY_VERIFIER"
EXPECTED_LEAF_BUNDLE_SEMANTIC_SCOPE_ID = (
    "oracle-worker-abi-v1-supplemental-expected-leaf-preimages-only"
)

ORACLE_WORKER_REQUEST_DOMAIN = b"heterodiff.adapter.oracle-worker-request.v1"
ORACLE_WORKER_RESPONSE_DOMAIN = b"heterodiff.adapter.oracle-worker-response.v1"
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

DESCRIPTOR_DIGEST_DOMAIN = "heterodiff.adapter.descriptor.v1"
SCHEMA_DIGEST_DOMAIN = "heterodiff.adapter.schema.v1"
SPLIT_MANIFEST_DIGEST_DOMAIN = "heterodiff.adapter.split-manifest.v1"
NATIVE_OBSERVATION_DIGEST_DOMAIN = (
    "heterodiff.adapter.native-observation.v1"
)
NATIVE_OCCURRENCE_DIGEST_DOMAIN = (
    "heterodiff.adapter.native-occurrence.v1"
)
SOURCE_ITEM_DIGEST_DOMAIN = "heterodiff.adapter.source-item.v1"
SOURCE_INVENTORY_DIGEST_DOMAIN = "heterodiff.adapter.source-inventory.v1"
COVERAGE_LEDGER_DIGEST_DOMAIN = "heterodiff.adapter.coverage-ledger.v1"
STATIC_CONTEXT_DIGEST_DOMAIN = "heterodiff.adapter.static-context.v1"
EVALUATION_LABELS_DIGEST_DOMAIN = (
    "heterodiff.adapter.evaluation-labels.v1"
)
PRIVATE_PROVENANCE_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-provenance.v1"
)
FITTED_STATE_DIGEST_DOMAIN = "heterodiff.adapter.fitted-state.v1"
TRAINING_GROUP_SET_DIGEST_DOMAIN = (
    "heterodiff.adapter.training-group-set.v1"
)
SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN = (
    "heterodiff.adapter.semantic-reconstruction.v1"
)
EXPECTED_EVIDENCE_DIGEST_DOMAIN = (
    "heterodiff.adapter.expected-evidence.v1"
)

PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-native-configuration.v1"
)
PRIVATE_SOURCE_INVENTORY_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-source-inventory.v1"
)
PRIVATE_COVERAGE_LEDGER_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-coverage-ledger.v1"
)
PRIVATE_STATIC_CONTEXT_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-static-context.v1"
)
PRIVATE_EVALUATION_LABELS_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-evaluation-labels.v1"
)
PRIVATE_PROVENANCE_PAYLOAD_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-provenance-payload.v1"
)
PRIVATE_FITTED_STATE_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-fitted-state.v1"
)
PRIVATE_SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-semantic-reconstruction.v1"
)

ADAPTER_CONTRACT_VERSION = "heterodiff-native-event-adapter-v1"
UNICODE_PROFILE = "ucd-3.2.0"
ATOMIC_COUNTING_GRID_REPRESENTATION_ID = (
    "heterodiff.atomic-counting-grid.v1"
)

MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES = 32 * 1024 * 1024
MAXIMUM_EXPECTED_LEAF_VERIFICATION_INPUT_BYTES = 160 * 1024 * 1024
MAXIMUM_EXPECTED_LEAF_VERIFICATION_RECEIPT_BYTES = 64 * 1024
MAXIMUM_CANONICAL_DEPTH = 32
MAXIMUM_CANONICAL_NODES = 200_000
MAXIMUM_CANONICAL_STRING_BYTES = 512 * 1024
MAXIMUM_PRIVATE_PAYLOAD_BYTES = 16 * 1024 * 1024
MAXIMUM_SINGLE_PAYLOAD_BYTES = 256 * 1024
MAXIMUM_SOURCE_BYTES = 64 * 1024
MAXIMUM_INVENTORY_ITEMS = 4096
MAXIMUM_SEMANTIC_OCCURRENCES = 2048
MAXIMUM_SPLIT_ENTRIES = 4096
MAXIMUM_SPLIT_GROUPS = 128
MAXIMUM_DECLARED_EVENT_TYPES = 1024
MAXIMUM_FIELDS_PER_EVENT_TYPE = 16
MAXIMUM_SCALAR_COORDINATES_PER_EVENT_TYPE = 16
MAXIMUM_SCALAR_COORDINATES_PER_OCCURRENCE = 16
MAXIMUM_TIME_ATOMS = 4096
MAXIMUM_EVENT_ID_TUPLE_ARITY = 8
MAXIMUM_EVENT_ID_COMPONENT_BYTES = 256
MAXIMUM_EVENT_ID_METADATA_BYTES = 2 * 1024 * 1024
MAXIMUM_KEYED_LEAF_ENTRIES = 4096
MAXIMUM_FIELD_STATUSES_PER_OCCURRENCE = 16
MAXIMUM_SOURCE_LINKS_PER_OCCURRENCE = 4096
MAXIMUM_TOTAL_PROVENANCE_SOURCE_LINKS = MAXIMUM_INVENTORY_ITEMS
MAXIMUM_SECONDARY_TAGS_PER_ITEM = 64
MAXIMUM_TOTAL_SECONDARY_TAGS = MAXIMUM_INVENTORY_ITEMS
MAXIMUM_REASON_CODES = 1024
MAXIMUM_REPRESENTATION_IDS = 64
MAXIMUM_PUBLIC_TOKEN_BYTES = 128
MAXIMUM_PRIVATE_TEXT_CODEPOINTS = 256

_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_ID_RE = re.compile(
    r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$"
)
_VERSION_RE = re.compile(r"^[1-9][0-9]{0,9}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_UCD = unicodedata.ucd_3_2_0

_TOP_LEVEL_KEYS = (
    "allowed_censor_reason_codes",
    "allowed_exclusion_reason_codes",
    "artifact_type",
    "descriptor_sha256",
    "expected",
    "format_version",
    "source_byte_count",
    "source_sha256",
    "split_manifest_sha256",
)
_EXPECTED_KEYS = (
    "coverage_ledger",
    "detached_native_observation",
    "evaluation_labels",
    "expected_evidence_commitment",
    "fitted_state",
    "identity_bearing_native_configuration",
    "private_provenance",
    "semantic_reconstruction",
    "source_inventory",
    "static_context",
)
_WRAPPER_KEYS = ("payload", "payload_byte_count", "payload_sha256")
_RAW_BYTE_KEYS = ("byte_count", "bytes_b64", "sha256")
_V1_INPUT_FIELDS = (
    "oracle_registry_bytes",
    "source_archive_inventory_bytes",
    "source_archive_bytes",
    "source_archive_membership_receipt_bytes",
    "source_policy_receipt_bytes",
    "independent_golden_receipt_bytes",
    "request_frame_bytes",
    "response_frame_bytes",
    "stderr_bytes",
    "interpreter_executable_bytes",
    "development_runner_receipt_bytes",
)


class ExpectedLeafBundleVerificationCode(str, Enum):
    INPUT_TYPE = "EXPECTED_LEAF_INPUT_TYPE"
    INPUT_RESOURCE = "EXPECTED_LEAF_INPUT_RESOURCE"
    V1_VERIFICATION_FAILED = "EXPECTED_LEAF_V1_VERIFICATION_FAILED"
    FRAME_INVALID = "EXPECTED_LEAF_FRAME_INVALID"
    JSON_INVALID = "EXPECTED_LEAF_JSON_INVALID"
    BINDING_MISMATCH = "EXPECTED_LEAF_BINDING_MISMATCH"
    RECEIPT_INVALID = "EXPECTED_LEAF_RECEIPT_INVALID"
    CANONICALIZATION_FAILED = "EXPECTED_LEAF_CANONICALIZATION_FAILED"
    INTERNAL_ERROR = "EXPECTED_LEAF_INTERNAL_ERROR"


_ERROR_MESSAGES = MappingProxyType(
    {
        ExpectedLeafBundleVerificationCode.INPUT_TYPE: (
            "expected-leaf verifier input has an invalid exact type"
        ),
        ExpectedLeafBundleVerificationCode.INPUT_RESOURCE: (
            "expected-leaf verifier input exceeds a fixed resource bound"
        ),
        ExpectedLeafBundleVerificationCode.V1_VERIFICATION_FAILED: (
            "the prerequisite V1 raw-byte verification did not succeed"
        ),
        ExpectedLeafBundleVerificationCode.FRAME_INVALID: (
            "an oracle-worker frame is invalid at the supplemental boundary"
        ),
        ExpectedLeafBundleVerificationCode.JSON_INVALID: (
            "expected-leaf bytes are not strict canonical-profile JSON"
        ),
        ExpectedLeafBundleVerificationCode.BINDING_MISMATCH: (
            "expected-leaf cross-object bindings do not match"
        ),
        ExpectedLeafBundleVerificationCode.RECEIPT_INVALID: (
            "expected-leaf verification receipt is invalid"
        ),
        ExpectedLeafBundleVerificationCode.CANONICALIZATION_FAILED: (
            "expected-leaf canonical serialization failed"
        ),
        ExpectedLeafBundleVerificationCode.INTERNAL_ERROR: (
            "expected-leaf verification failed internally"
        ),
    }
)


class ExpectedLeafBundleVerificationError(ValueError):
    """One closed, interpolation-free supplemental verification failure."""

    def __init__(self, code: ExpectedLeafBundleVerificationCode) -> None:
        if type(code) is not ExpectedLeafBundleVerificationCode:
            raise TypeError("expected-leaf verification code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


class _Rejected(ValueError):
    pass


def _fail(code: ExpectedLeafBundleVerificationCode) -> None:
    raise ExpectedLeafBundleVerificationError(code) from None


def _reject() -> None:
    raise _Rejected() from None


def _exact_bytes(
    value: object, *, maximum: int, allow_empty: bool = False
) -> bytes:
    if type(value) is not bytes:
        raise TypeError("value must be exact immutable bytes")
    if (not value and not allow_empty) or len(value) > maximum:
        raise ValueError("byte value is outside its bound")
    return value


def _require_keys(value: object, expected: Tuple[str, ...]) -> dict:
    if type(value) is not dict or tuple(sorted(value)) != tuple(
        sorted(expected)
    ):
        _reject()
    return value


def _require_list(value: object, *, maximum: int) -> list:
    if type(value) is not list or len(value) > maximum:
        _reject()
    return value


def _require_bool(value: object) -> bool:
    if type(value) is not bool:
        _reject()
    return value


def _require_integer(
    value: object,
    *,
    maximum: int = _MAXIMUM_SAFE_INTEGER,
    minimum: int = 0,
) -> int:
    if type(value) is not int or value < minimum or value > maximum:
        _reject()
    return value


def _require_digest(value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _reject()
    return value


def _require_ascii_token(value: object, *, maximum: int = MAXIMUM_PUBLIC_TOKEN_BYTES) -> str:
    if type(value) is not str:
        _reject()
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        _reject()
    if (
        not encoded
        or len(encoded) > maximum
        or _TOKEN_RE.fullmatch(value) is None
    ):
        _reject()
    return value


def _require_public_id(value: object) -> str:
    if type(value) is not str:
        _reject()
    try:
        encoded = value.encode("ascii", "strict")
    except UnicodeError:
        _reject()
    if (
        not encoded
        or len(encoded) > MAXIMUM_PUBLIC_TOKEN_BYTES
        or _PUBLIC_ID_RE.fullmatch(value) is None
    ):
        _reject()
    return value


def _require_private_text(
    value: object,
    *,
    allow_empty: bool = False,
) -> str:
    if type(value) is not str:
        _reject()
    if not value:
        if allow_empty:
            return value
        _reject()
    if len(value) > MAXIMUM_PRIVATE_TEXT_CODEPOINTS:
        _reject()
    try:
        value.encode("utf-8", "strict")
    except UnicodeError:
        _reject()
    if _UCD.normalize("NFC", value) != value:
        _reject()
    categories = tuple(_UCD.category(character) for character in value)
    forbidden = {"Cc", "Cs", "Co", "Cn", "Zl", "Zp"}
    if any(category in forbidden for category in categories):
        _reject()
    if categories and (categories[0] == "Zs" or categories[-1] == "Zs"):
        _reject()
    return value


def _require_float_hex(value: object) -> float:
    if type(value) is not str or value != value.lower():
        _reject()
    try:
        result = float.fromhex(value)
    except (TypeError, ValueError, OverflowError):
        _reject()
    if not math.isfinite(result):
        _reject()
    canonical = (0.0 if result == 0.0 else result).hex().lower()
    if canonical != value:
        _reject()
    return 0.0 if result == 0.0 else result


def _plain_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _domain_sha256(domain: str, payload: bytes) -> str:
    try:
        encoded_domain = domain.encode("ascii", "strict")
    except UnicodeError:
        _reject()
    return hashlib.sha256(
        encoded_domain
        + b"\x00"
        + len(payload).to_bytes(8, "big")
        + payload
    ).hexdigest()


def _canonical_json_bytes(
    value: object,
    *,
    maximum: int = MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES,
) -> bytes:
    _validate_json_tree(value)
    try:
        result = json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _reject()
    if not result or len(result) > maximum:
        _reject()
    return result


def _validate_json_tree(value: object) -> None:
    nodes = 0
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAXIMUM_CANONICAL_NODES or depth > MAXIMUM_CANONICAL_DEPTH:
            _reject()
        if current is None or type(current) is bool:
            continue
        if type(current) is int:
            if abs(current) > _MAXIMUM_SAFE_INTEGER:
                _reject()
            continue
        if type(current) is str:
            try:
                encoded = current.encode("utf-8", "strict")
            except UnicodeError:
                _reject()
            if len(encoded) > MAXIMUM_CANONICAL_STRING_BYTES:
                _reject()
            continue
        if type(current) is list:
            stack.extend((item, depth + 1) for item in reversed(current))
            continue
        if type(current) is dict:
            for key, item in reversed(tuple(current.items())):
                if type(key) is not str:
                    _reject()
                try:
                    encoded_key = key.encode("utf-8", "strict")
                except UnicodeError:
                    _reject()
                if len(encoded_key) > MAXIMUM_CANONICAL_STRING_BYTES:
                    _reject()
                stack.append((item, depth + 1))
            continue
        _reject()


def _lexical_json_preflight(value: bytes) -> None:
    if not value or len(value) > MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES:
        _reject()
    if any(byte >= 0x80 for byte in value):
        _reject()
    depth = 0
    in_string = False
    escaped = False
    string_bytes = 0
    for byte in value:
        if in_string:
            if not escaped and byte == 0x22:
                in_string = False
                continue
            string_bytes += 1
            if string_bytes > MAXIMUM_CANONICAL_STRING_BYTES:
                _reject()
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            continue
        if byte == 0x22:
            in_string = True
            escaped = False
            string_bytes = 0
        elif byte in (0x7B, 0x5B):
            depth += 1
            if depth > MAXIMUM_CANONICAL_DEPTH:
                _reject()
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0:
                _reject()
    if in_string or depth != 0:
        _reject()


def _strict_json_bytes(value: bytes, *, maximum: int) -> dict:
    if type(value) is not bytes or not value or len(value) > maximum:
        _reject()
    _lexical_json_preflight(value)

    def object_pairs(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                _reject()
            result[key] = item
        return result

    def parse_integer(token):
        digits = token[1:] if token.startswith("-") else token
        if len(digits) > 16:
            _reject()
        result = int(token, 10)
        if abs(result) > _MAXIMUM_SAFE_INTEGER:
            _reject()
        return result

    def reject_number(_token):
        _reject()

    try:
        tree = json.loads(
            value.decode("ascii", "strict"),
            object_pairs_hook=object_pairs,
            parse_int=parse_integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
    except _Rejected:
        raise
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _reject()
    if type(tree) is not dict:
        _reject()
    _validate_json_tree(tree)
    if _canonical_json_bytes(tree, maximum=maximum) != value:
        _reject()
    return tree


def _named_sequence_sha256(
    domain: str,
    names: Tuple[bytes, ...],
    values: Tuple[bytes, ...],
) -> str:
    if len(names) != len(values):
        _reject()
    parts = [
        domain.encode("ascii"),
        b"\x00",
        len(names).to_bytes(8, "big"),
    ]
    for name, raw in zip(names, values):
        parts.extend(
            (
                len(name).to_bytes(8, "big"),
                name,
                len(raw).to_bytes(8, "big"),
                raw,
            )
        )
    return hashlib.sha256(b"".join(parts)).hexdigest()


def _parse_named_frame(
    value: bytes,
    *,
    domain: bytes,
    names: Tuple[bytes, ...],
) -> Tuple[bytes, ...]:
    if (
        type(value) is not bytes
        or not value
        or len(value) > _v1.MAXIMUM_ORACLE_WORKER_FRAME_BYTES
        or len(value) < len(domain) + 9
        or value[: len(domain)] != domain
        or value[len(domain)] != 0
    ):
        _reject()
    offset = len(domain) + 1

    def read_u64() -> int:
        nonlocal offset
        end = offset + 8
        if end > len(value):
            _reject()
        result = int.from_bytes(value[offset:end], "big")
        offset = end
        return result

    if read_u64() != len(names):
        _reject()
    result = []
    for expected_name in names:
        name_length = read_u64()
        if name_length > len(value) - offset:
            _reject()
        name_end = offset + name_length
        if value[offset:name_end] != expected_name:
            _reject()
        offset = name_end
        raw_length = read_u64()
        if raw_length > len(value) - offset:
            _reject()
        raw_end = offset + raw_length
        result.append(value[offset:raw_end])
        offset = raw_end
    if offset != len(value):
        _reject()
    return tuple(result)


class _RequestMaterial(NamedTuple):
    source_bytes: bytes
    descriptor_bytes: bytes
    partition_bytes: bytes
    split_manifest_bytes: bytes


class _ResponseMaterial(NamedTuple):
    configuration_bytes: bytes
    evidence_bytes: bytes
    native_sha256: str


def _parse_v1_material(
    value: _v1.IndependentOracleVerificationInputV1,
) -> Tuple[_RequestMaterial, _ResponseMaterial]:
    request_values = _parse_named_frame(
        value.request_frame_bytes,
        domain=ORACLE_WORKER_REQUEST_DOMAIN,
        names=ORACLE_WORKER_REQUEST_FIELD_NAMES,
    )
    response_values = _parse_named_frame(
        value.response_frame_bytes,
        domain=ORACLE_WORKER_RESPONSE_DOMAIN,
        names=ORACLE_WORKER_RESPONSE_FIELD_NAMES,
    )
    if (
        len(request_values[1]) != 8
        or len(request_values[3]) != 8
        or len(response_values[1]) != 8
        or len(response_values[3]) != 8
    ):
        _reject()
    try:
        request_identity = (
            int.from_bytes(request_values[1], "big"),
            request_values[2].decode("ascii", "strict"),
            int.from_bytes(request_values[3], "big"),
            request_values[4].decode("ascii", "strict"),
        )
        response_identity = (
            int.from_bytes(response_values[1], "big"),
            response_values[2].decode("ascii", "strict"),
            int.from_bytes(response_values[3], "big"),
            response_values[4].decode("ascii", "strict"),
        )
        request_hash = response_values[0].decode("ascii", "strict")
        native_sha256 = response_values[7].decode("ascii", "strict")
    except UnicodeError:
        _reject()
    _require_digest(request_hash)
    _require_digest(native_sha256)
    if (
        request_identity != response_identity
        or request_hash != _plain_sha256(value.request_frame_bytes)
    ):
        _reject()
    return (
        _RequestMaterial(
            source_bytes=request_values[5],
            descriptor_bytes=request_values[6],
            partition_bytes=request_values[7],
            split_manifest_bytes=request_values[8],
        ),
        _ResponseMaterial(
            configuration_bytes=response_values[5],
            evidence_bytes=response_values[6],
            native_sha256=native_sha256,
        ),
    )


@dataclass(frozen=True)
class IndependentExpectedLeafBundleVerificationInputV1:
    """Original V1 raw bundle plus one exact supplemental leaf bundle."""

    oracle_input: _v1.IndependentOracleVerificationInputV1
    expected_leaf_bundle_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not IndependentExpectedLeafBundleVerificationInputV1:
            raise TypeError("supplemental verifier input must be exact")
        if type(self.oracle_input) is not _v1.IndependentOracleVerificationInputV1:
            raise TypeError("oracle_input must be the exact V1 input")
        _exact_bytes(
            self.expected_leaf_bundle_bytes,
            maximum=MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES,
        )
        total = len(self.expected_leaf_bundle_bytes)
        for name in _V1_INPUT_FIELDS:
            raw = getattr(self.oracle_input, name)
            if type(raw) is not bytes:
                raise TypeError("nested V1 raw inputs must be exact bytes")
            total += len(raw)
        if total > MAXIMUM_EXPECTED_LEAF_VERIFICATION_INPUT_BYTES:
            raise ValueError("supplemental verifier input exceeds its aggregate")


def _snapshot_input(
    value: object,
) -> IndependentExpectedLeafBundleVerificationInputV1:
    if type(value) is not IndependentExpectedLeafBundleVerificationInputV1:
        _fail(ExpectedLeafBundleVerificationCode.INPUT_TYPE)
    try:
        IndependentExpectedLeafBundleVerificationInputV1.__post_init__(value)
        nested = _v1.IndependentOracleVerificationInputV1(
            **{
                name: getattr(value.oracle_input, name)
                for name in _V1_INPUT_FIELDS
            }
        )
        return IndependentExpectedLeafBundleVerificationInputV1(
            oracle_input=nested,
            expected_leaf_bundle_bytes=value.expected_leaf_bundle_bytes,
        )
    except ExpectedLeafBundleVerificationError:
        raise
    except (AttributeError, TypeError):
        _fail(ExpectedLeafBundleVerificationCode.INPUT_TYPE)
    except ValueError:
        _fail(ExpectedLeafBundleVerificationCode.INPUT_RESOURCE)


class _RawBudget:
    def __init__(self) -> None:
        self.decoded_bytes = 0

    def decode(self, value: object) -> bytes:
        tree = _require_keys(value, _RAW_BYTE_KEYS)
        byte_count = _require_integer(
            tree["byte_count"], maximum=MAXIMUM_SINGLE_PAYLOAD_BYTES
        )
        encoded = tree["bytes_b64"]
        if type(encoded) is not str:
            _reject()
        try:
            encoded_bytes = encoded.encode("ascii", "strict")
        except UnicodeError:
            _reject()
        expected_encoded_size = 4 * ((byte_count + 2) // 3)
        if len(encoded_bytes) != expected_encoded_size:
            _reject()
        try:
            raw = base64.b64decode(encoded_bytes, validate=True)
        except (ValueError, TypeError):
            _reject()
        if (
            len(raw) != byte_count
            or base64.b64encode(raw) != encoded_bytes
            or _require_digest(tree["sha256"]) != _plain_sha256(raw)
        ):
            _reject()
        self.decoded_bytes += len(raw)
        if self.decoded_bytes > MAXIMUM_PRIVATE_PAYLOAD_BYTES:
            _reject()
        return raw


class _WrapperMaterial(NamedTuple):
    payload: dict
    payload_bytes: bytes
    payload_sha256: str


def _parse_wrapper(
    value: object,
    *,
    domain: str,
) -> _WrapperMaterial:
    tree = _require_keys(value, _WRAPPER_KEYS)
    if type(tree["payload"]) is not dict:
        _reject()
    payload_bytes = _canonical_json_bytes(
        tree["payload"], maximum=MAXIMUM_PRIVATE_PAYLOAD_BYTES
    )
    if (
        _require_integer(
            tree["payload_byte_count"],
            maximum=MAXIMUM_PRIVATE_PAYLOAD_BYTES,
        )
        != len(payload_bytes)
        or _require_digest(tree["payload_sha256"])
        != _domain_sha256(domain, payload_bytes)
    ):
        _reject()
    return _WrapperMaterial(
        payload=tree["payload"],
        payload_bytes=payload_bytes,
        payload_sha256=tree["payload_sha256"],
    )


class _DescriptorMaterial(NamedTuple):
    adapter_id: str
    adapter_version: str
    contract_version: str
    policy_sha256: str
    time_measure: str
    multiplicity_mode: str
    supported_representation_ids: Tuple[str, ...]
    static_context: bool
    evaluation_labels: bool
    fitted_state: bool
    private_provenance: bool
    raw_byte_reconstruction: bool
    semantic_reconstruction: bool
    descriptor_sha256: str


def _parse_descriptor(value: bytes) -> _DescriptorMaterial:
    tree = _strict_json_bytes(
        value, maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES
    )
    _require_keys(tree, ("capabilities", "identity", "unicode_profile"))
    if tree["unicode_profile"] != UNICODE_PROFILE:
        _reject()
    capabilities = _require_keys(
        tree["capabilities"],
        (
            "evaluation_labels",
            "fitted_state",
            "multiplicity_mode",
            "private_provenance",
            "raw_byte_reconstruction",
            "semantic_reconstruction",
            "static_context",
            "supported_representation_ids",
            "time_measure",
        ),
    )
    identity = _require_keys(
        tree["identity"],
        (
            "adapter_id",
            "adapter_version",
            "contract_version",
            "policy_sha256",
        ),
    )
    adapter_id = _require_public_id(identity["adapter_id"])
    adapter_version = identity["adapter_version"]
    if (
        type(adapter_version) is not str
        or _VERSION_RE.fullmatch(adapter_version) is None
    ):
        _reject()
    if identity["contract_version"] != ADAPTER_CONTRACT_VERSION:
        _reject()
    policy_sha256 = _require_digest(identity["policy_sha256"])
    time_measure = capabilities["time_measure"]
    multiplicity_mode = capabilities["multiplicity_mode"]
    if time_measure not in ("continuous", "atomic_grid", "mixed"):
        _reject()
    if multiplicity_mode not in ("simple", "finite_counting"):
        _reject()
    representations_raw = _require_list(
        capabilities["supported_representation_ids"],
        maximum=MAXIMUM_REPRESENTATION_IDS,
    )
    representations = tuple(
        _require_public_id(item) for item in representations_raw
    )
    if representations != tuple(sorted(set(representations))):
        _reject()
    if (
        ATOMIC_COUNTING_GRID_REPRESENTATION_ID in representations
        and time_measure != "atomic_grid"
    ):
        _reject()
    semantic = _require_bool(capabilities["semantic_reconstruction"])
    if semantic is not True:
        _reject()
    return _DescriptorMaterial(
        adapter_id=adapter_id,
        adapter_version=adapter_version,
        contract_version=ADAPTER_CONTRACT_VERSION,
        policy_sha256=policy_sha256,
        time_measure=time_measure,
        multiplicity_mode=multiplicity_mode,
        supported_representation_ids=representations,
        static_context=_require_bool(capabilities["static_context"]),
        evaluation_labels=_require_bool(capabilities["evaluation_labels"]),
        fitted_state=_require_bool(capabilities["fitted_state"]),
        private_provenance=_require_bool(
            capabilities["private_provenance"]
        ),
        raw_byte_reconstruction=_require_bool(
            capabilities["raw_byte_reconstruction"]
        ),
        semantic_reconstruction=semantic,
        descriptor_sha256=_domain_sha256(DESCRIPTOR_DIGEST_DOMAIN, value),
    )


class _PartitionMaterial(NamedTuple):
    sample_id: str
    group_id: str
    split: str


def _parse_partition(value: bytes) -> _PartitionMaterial:
    tree = _strict_json_bytes(
        value, maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES
    )
    _require_keys(tree, ("group_id", "sample_id", "split", "unicode_profile"))
    if tree["unicode_profile"] != UNICODE_PROFILE:
        _reject()
    split = tree["split"]
    if split not in ("train", "validation", "test"):
        _reject()
    return _PartitionMaterial(
        sample_id=_require_private_text(tree["sample_id"]),
        group_id=_require_private_text(tree["group_id"]),
        split=split,
    )


def _parse_split_manifest(
    value: bytes,
) -> Tuple[Tuple[_PartitionMaterial, ...], str]:
    tree = _strict_json_bytes(
        value, maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES
    )
    _require_keys(tree, ("entries", "unicode_profile"))
    if tree["unicode_profile"] != UNICODE_PROFILE:
        _reject()
    entries_raw = _require_list(tree["entries"], maximum=MAXIMUM_SPLIT_ENTRIES)
    if not entries_raw:
        _reject()
    entries = []
    groups = set()
    for item in entries_raw:
        entry = _require_keys(item, ("group_id", "sample_id", "split"))
        split = entry["split"]
        if split not in ("train", "validation", "test"):
            _reject()
        parsed = _PartitionMaterial(
            sample_id=_require_private_text(entry["sample_id"]),
            group_id=_require_private_text(entry["group_id"]),
            split=split,
        )
        entries.append(parsed)
        groups.add(parsed.group_id)
        if len(groups) > MAXIMUM_SPLIT_GROUPS:
            _reject()
    keys = tuple(
        (entry.group_id, entry.sample_id, entry.split) for entry in entries
    )
    sample_ids = tuple(entry.sample_id for entry in entries)
    group_splits = {}
    for entry in entries:
        prior = group_splits.setdefault(entry.group_id, entry.split)
        if prior != entry.split:
            _reject()
    if (
        keys != tuple(sorted(set(keys)))
        or len(sample_ids) != len(set(sample_ids))
    ):
        _reject()
    return tuple(entries), _domain_sha256(SPLIT_MANIFEST_DIGEST_DOMAIN, value)


class _FieldMaterial(NamedTuple):
    name: str
    dimension: int
    support: str
    lower: Optional[float]
    upper: Optional[float]
    unit: Optional[str]


class _EventTypeMaterial(NamedTuple):
    type_id: int
    name: str
    fields: Tuple[_FieldMaterial, ...]


class _SchemaMaterial(NamedTuple):
    tree: dict
    schema_sha256: str
    event_types: Tuple[_EventTypeMaterial, ...]
    event_types_by_id: Dict[int, _EventTypeMaterial]
    horizon: Optional[float]
    time_measure: str
    multiplicity_mode: str
    allow_simultaneous: bool
    time_atoms: Tuple[float, ...]


def _parse_schema(value: object) -> _SchemaMaterial:
    tree = _require_keys(
        value,
        (
            "allow_simultaneous",
            "event_types",
            "horizon",
            "multiplicity_mode",
            "time_measure",
            "time_reference",
            "version",
        ),
    )
    time_measure = tree["time_measure"]
    multiplicity = tree["multiplicity_mode"]
    if time_measure not in ("continuous", "atomic_grid", "mixed"):
        _reject()
    if multiplicity not in ("simple", "finite_counting"):
        _reject()
    version = _require_private_text(tree["version"])
    del version
    horizon = None
    if tree["horizon"] is not None:
        horizon = _require_float_hex(tree["horizon"])
        if horizon <= 0.0:
            _reject()
    reference = _require_keys(
        tree["time_reference"],
        ("atom_weights", "atoms", "continuous_weight", "kind"),
    )
    if reference["kind"] != time_measure:
        _reject()
    atoms_raw = _require_list(reference["atoms"], maximum=MAXIMUM_TIME_ATOMS)
    weights_raw = _require_list(
        reference["atom_weights"], maximum=MAXIMUM_TIME_ATOMS
    )
    if len(atoms_raw) != len(weights_raw):
        _reject()
    atoms = tuple(_require_float_hex(item) for item in atoms_raw)
    weights = tuple(_require_float_hex(item) for item in weights_raw)
    continuous_weight = _require_float_hex(reference["continuous_weight"])
    if (
        any(item < 0.0 for item in atoms)
        or atoms != tuple(sorted(set(atoms)))
        or any(item <= 0.0 for item in weights)
        or continuous_weight < 0.0
        or (horizon is not None and any(item > horizon for item in atoms))
    ):
        _reject()
    if time_measure == "continuous":
        if atoms or weights or continuous_weight <= 0.0:
            _reject()
    elif time_measure == "atomic_grid":
        if not atoms or continuous_weight != 0.0:
            _reject()
    elif not atoms or continuous_weight <= 0.0:
        _reject()

    event_types_raw = _require_list(
        tree["event_types"], maximum=MAXIMUM_DECLARED_EVENT_TYPES
    )
    if not event_types_raw:
        _reject()
    event_types = []
    for raw_event_type in event_types_raw:
        event_type = _require_keys(
            raw_event_type, ("fields", "name", "type_id")
        )
        fields_raw = _require_list(
            event_type["fields"], maximum=MAXIMUM_FIELDS_PER_EVENT_TYPE
        )
        parsed_fields = []
        scalar_count = 0
        for raw_field in fields_raw:
            field_tree = _require_keys(
                raw_field,
                ("dimension", "lower", "name", "support", "unit", "upper"),
            )
            dimension = _require_integer(
                field_tree["dimension"],
                maximum=MAXIMUM_SCALAR_COORDINATES_PER_EVENT_TYPE,
                minimum=1,
            )
            scalar_count += dimension
            if scalar_count > MAXIMUM_SCALAR_COORDINATES_PER_EVENT_TYPE:
                _reject()
            support = field_tree["support"]
            if support not in ("real", "positive", "bounded", "simplex"):
                _reject()
            lower = (
                None
                if field_tree["lower"] is None
                else _require_float_hex(field_tree["lower"])
            )
            upper = (
                None
                if field_tree["upper"] is None
                else _require_float_hex(field_tree["upper"])
            )
            if support == "bounded":
                if lower is None or upper is None or lower >= upper:
                    _reject()
                width = upper - lower
                if (
                    not math.isfinite(width)
                    or math.nextafter(lower, upper) >= upper
                ):
                    _reject()
            elif lower is not None or upper is not None:
                _reject()
            if support == "simplex" and dimension < 2:
                _reject()
            unit = field_tree["unit"]
            if unit is not None:
                unit = _require_private_text(unit)
            parsed_fields.append(
                _FieldMaterial(
                    name=_require_private_text(field_tree["name"]),
                    dimension=dimension,
                    support=support,
                    lower=lower,
                    upper=upper,
                    unit=unit,
                )
            )
        field_names = tuple(item.name for item in parsed_fields)
        if field_names != tuple(sorted(set(field_names))):
            _reject()
        event_types.append(
            _EventTypeMaterial(
                type_id=_require_integer(event_type["type_id"]),
                name=_require_private_text(event_type["name"]),
                fields=tuple(parsed_fields),
            )
        )
    type_ids = tuple(item.type_id for item in event_types)
    type_names = tuple(item.name for item in event_types)
    if (
        type_ids != tuple(sorted(set(type_ids)))
        or len(type_names) != len(set(type_names))
    ):
        _reject()
    schema_bytes = _canonical_json_bytes(
        tree, maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES
    )
    return _SchemaMaterial(
        tree=tree,
        schema_sha256=_domain_sha256(SCHEMA_DIGEST_DOMAIN, schema_bytes),
        event_types=tuple(event_types),
        event_types_by_id={item.type_id: item for item in event_types},
        horizon=horizon,
        time_measure=time_measure,
        multiplicity_mode=multiplicity,
        allow_simultaneous=_require_bool(tree["allow_simultaneous"]),
        time_atoms=atoms,
    )


class _OccurrenceMaterial(NamedTuple):
    detached_tree: dict
    event_type: int
    marks: Dict[str, Tuple[float, ...]]
    model_key: tuple
    observation_key: tuple
    event_id_key: tuple


class _ConfigurationMaterial(NamedTuple):
    payload: dict
    payload_bytes: bytes
    schema: _SchemaMaterial
    sample_id: str
    group_id: str
    occurrences: Tuple[_OccurrenceMaterial, ...]
    detached_payload: dict
    detached_payload_bytes: bytes
    native_observation_sha256: str
    native_occurrence_sha256: Tuple[str, ...]


def _parse_event_id(value: object) -> Tuple[tuple, Optional[tuple], int]:
    if type(value) is not dict:
        _reject()
    kind = value.get("kind")
    if kind == "none":
        _require_keys(value, ("kind",))
        return (0,), None, 0
    if kind == "text":
        tree = _require_keys(value, ("kind", "value"))
        text = _require_private_text(tree["value"])
        encoded_size = len(text.encode("utf-8"))
        if encoded_size > MAXIMUM_EVENT_ID_COMPONENT_BYTES:
            _reject()
        key = ("text", text)
        return (1, text), key, 1 + encoded_size
    if kind != "tuple":
        _reject()
    tree = _require_keys(value, ("components", "kind"))
    components_raw = _require_list(
        tree["components"], maximum=MAXIMUM_EVENT_ID_TUPLE_ARITY
    )
    if not components_raw:
        _reject()
    sort_components = []
    identity_components = []
    metadata = 1
    for component_raw in components_raw:
        component = _require_keys(component_raw, ("kind", "value"))
        component_kind = component["kind"]
        if component_kind == "integer":
            integer = component["value"]
            if type(integer) is not int or abs(integer) > _MAXIMUM_SAFE_INTEGER:
                _reject()
            sort_components.append((0, integer))
            identity_components.append(("integer", integer))
            metadata += 9
        elif component_kind == "text":
            text = _require_private_text(component["value"])
            encoded_size = len(text.encode("utf-8"))
            if encoded_size > MAXIMUM_EVENT_ID_COMPONENT_BYTES:
                _reject()
            sort_components.append((1, text))
            identity_components.append(("text", text))
            metadata += 1 + encoded_size
        else:
            _reject()
    identity = ("tuple", tuple(identity_components))
    return (2, tuple(sort_components)), identity, metadata


def _field_by_name(
    event_type: _EventTypeMaterial,
) -> Dict[str, _FieldMaterial]:
    return {field.name: field for field in event_type.fields}


def _validate_mark_vector(
    value: object,
    *,
    field: _FieldMaterial,
) -> Tuple[float, ...]:
    vector_raw = _require_list(
        value, maximum=MAXIMUM_SCALAR_COORDINATES_PER_OCCURRENCE
    )
    if len(vector_raw) != field.dimension:
        _reject()
    vector = tuple(_require_float_hex(item) for item in vector_raw)
    if field.support == "positive" and any(item <= 0.0 for item in vector):
        _reject()
    if field.support == "bounded" and any(
        not field.lower < item < field.upper  # type: ignore[operator]
        for item in vector
    ):
        _reject()
    if field.support == "simplex":
        if any(item <= 0.0 for item in vector):
            _reject()
        tolerance = 32.0 * 2.220446049250313e-16 * field.dimension
        if not math.isclose(
            sum(vector), 1.0, rel_tol=0.0, abs_tol=tolerance
        ):
            _reject()
    return vector


def _parse_configuration(value: object) -> _ConfigurationMaterial:
    tree = _require_keys(
        value,
        (
            "group_id",
            "occurrences",
            "observation_pattern",
            "sample_id",
            "schema",
        ),
    )
    schema = _parse_schema(tree["schema"])
    sample_id = _require_private_text(tree["sample_id"])
    group_id = _require_private_text(tree["group_id"])
    observation_pattern = _require_keys(
        tree["observation_pattern"], ("cardinality_observed",)
    )
    cardinality_observed = _require_bool(
        observation_pattern["cardinality_observed"]
    )
    occurrences_raw = _require_list(
        tree["occurrences"], maximum=MAXIMUM_SEMANTIC_OCCURRENCES
    )
    occurrences = []
    seen_event_ids = set()
    event_id_metadata_bytes = 0
    for occurrence_raw in occurrences_raw:
        occurrence = _require_keys(
            occurrence_raw, ("event", "observation")
        )
        event = _require_keys(
            occurrence["event"],
            ("event_id", "event_time", "event_type", "marks"),
        )
        observation = _require_keys(
            occurrence["observation"],
            ("observed_marks", "time_observed", "type_observed"),
        )
        event_time = _require_float_hex(event["event_time"])
        event_type_id = _require_integer(event["event_type"])
        event_type = schema.event_types_by_id.get(event_type_id)
        if event_type is None:
            _reject()
        if (
            event_time < 0.0
            or (schema.horizon is not None and event_time > schema.horizon)
            or (
                schema.time_measure == "atomic_grid"
                and event_time not in schema.time_atoms
            )
        ):
            _reject()
        marks_tree = event["marks"]
        if type(marks_tree) is not dict or len(marks_tree) > (
            MAXIMUM_FIELDS_PER_EVENT_TYPE
        ):
            _reject()
        if tuple(marks_tree) != tuple(sorted(marks_tree)):
            _reject()
        applicable_fields = _field_by_name(event_type)
        marks = {}
        scalar_count = 0
        for name, vector_raw in marks_tree.items():
            validated_name = _require_private_text(name)
            field_material = applicable_fields.get(validated_name)
            if field_material is None:
                _reject()
            vector = _validate_mark_vector(
                vector_raw, field=field_material
            )
            scalar_count += len(vector)
            if scalar_count > MAXIMUM_SCALAR_COORDINATES_PER_OCCURRENCE:
                _reject()
            marks[validated_name] = vector
        observed_marks_raw = _require_list(
            observation["observed_marks"],
            maximum=MAXIMUM_FIELDS_PER_EVENT_TYPE,
        )
        observed_marks = tuple(
            _require_private_text(item) for item in observed_marks_raw
        )
        if observed_marks != tuple(sorted(set(observed_marks))):
            _reject()
        if any(name not in marks for name in observed_marks):
            _reject()
        if any(name not in applicable_fields for name in observed_marks):
            _reject()
        time_observed = _require_bool(observation["time_observed"])
        type_observed = _require_bool(observation["type_observed"])
        event_id_sort, event_id_identity, metadata_size = _parse_event_id(
            event["event_id"]
        )
        event_id_metadata_bytes += metadata_size
        if event_id_metadata_bytes > MAXIMUM_EVENT_ID_METADATA_BYTES:
            _reject()
        if event_id_identity is not None:
            if event_id_identity in seen_event_ids:
                _reject()
            seen_event_ids.add(event_id_identity)
        detached_tree = {
            "event": {
                "event_time": event["event_time"],
                "event_type": event_type_id,
                "marks": marks_tree,
            },
            "observation": {
                "observed_marks": list(observed_marks),
                "time_observed": time_observed,
                "type_observed": type_observed,
            },
        }
        model_key = (
            event_time,
            event_type_id,
            tuple((name, marks[name]) for name in sorted(marks)),
        )
        observation_key = (
            time_observed,
            type_observed,
            observed_marks,
        )
        occurrences.append(
            _OccurrenceMaterial(
                detached_tree=detached_tree,
                event_type=event_type_id,
                marks=marks,
                model_key=model_key,
                observation_key=observation_key,
                event_id_key=event_id_sort,
            )
        )
    canonical_keys = tuple(
        (
            item.model_key,
            item.observation_key,
            item.event_id_key,
        )
        for item in occurrences
    )
    if canonical_keys != tuple(sorted(canonical_keys)):
        _reject()
    for previous, current in zip(occurrences, occurrences[1:]):
        if previous.model_key == current.model_key:
            if schema.multiplicity_mode == "simple":
                _reject()
            continue
        if (
            not schema.allow_simultaneous
            and previous.model_key[0] == current.model_key[0]
        ):
            _reject()
    payload_bytes = _canonical_json_bytes(
        tree, maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES
    )
    detached = {
        "occurrences": [item.detached_tree for item in occurrences],
        "observation_pattern": {
            "cardinality_observed": cardinality_observed
        },
        "schema": schema.tree,
    }
    detached_bytes = _canonical_json_bytes(
        detached, maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES
    )
    native_sha256 = _domain_sha256(
        NATIVE_OBSERVATION_DIGEST_DOMAIN, detached_bytes
    )
    native_occurrence_sha256 = tuple(
        _domain_sha256(
            NATIVE_OCCURRENCE_DIGEST_DOMAIN,
            _canonical_json_bytes(
                {
                    "event": item.detached_tree["event"],
                    "observation": item.detached_tree["observation"],
                    "schema_sha256": schema.schema_sha256,
                },
                maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
            ),
        )
        for item in occurrences
    )
    return _ConfigurationMaterial(
        payload=tree,
        payload_bytes=payload_bytes,
        schema=schema,
        sample_id=sample_id,
        group_id=group_id,
        occurrences=tuple(occurrences),
        detached_payload=detached,
        detached_payload_bytes=detached_bytes,
        native_observation_sha256=native_sha256,
        native_occurrence_sha256=native_occurrence_sha256,
    )


def _blob_commitment(raw: bytes) -> dict:
    return {
        "payload_sha256": _plain_sha256(raw),
        "payload_size_bytes": len(raw),
    }


class _InventoryMaterial(NamedTuple):
    payload: dict
    source_sha256: str
    source_size_bytes: int
    policy_sha256: str
    item_keys: Tuple[str, ...]
    phase_c_sha256: str


def _parse_source_inventory(
    value: object,
    *,
    budget: _RawBudget,
) -> _InventoryMaterial:
    tree = _require_keys(
        value,
        (
            "item_format_id",
            "items",
            "policy_sha256",
            "source_sha256",
            "source_size_bytes",
        ),
    )
    item_format_id = _require_public_id(tree["item_format_id"])
    items_raw = _require_list(
        tree["items"], maximum=MAXIMUM_INVENTORY_ITEMS
    )
    item_keys = []
    phase_items = []
    for raw_item in items_raw:
        item = _require_keys(
            raw_item,
            ("canonical_item", "item_key", "source_item_sha256"),
        )
        item_key = _require_private_text(item["item_key"])
        canonical_item = budget.decode(item["canonical_item"])
        phase_item_payload = {
            "canonical_item": _blob_commitment(canonical_item),
            "item_format_id": item_format_id,
            "item_key": item_key,
        }
        phase_item_sha256 = _domain_sha256(
            SOURCE_ITEM_DIGEST_DOMAIN,
            _canonical_json_bytes(
                phase_item_payload,
                maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
            ),
        )
        if _require_digest(item["source_item_sha256"]) != phase_item_sha256:
            _reject()
        item_keys.append(item_key)
        phase_items.append(
            {
                "item_key": item_key,
                "source_item_sha256": phase_item_sha256,
            }
        )
    if tuple(item_keys) != tuple(sorted(set(item_keys))):
        _reject()
    source_size = _require_integer(
        tree["source_size_bytes"], maximum=MAXIMUM_SOURCE_BYTES
    )
    source_sha256 = _require_digest(tree["source_sha256"])
    policy_sha256 = _require_digest(tree["policy_sha256"])
    phase_payload = {
        "item_format_id": item_format_id,
        "items": phase_items,
        "policy_sha256": policy_sha256,
        "source_sha256": source_sha256,
        "source_size_bytes": source_size,
    }
    phase_digest = _domain_sha256(
        SOURCE_INVENTORY_DIGEST_DOMAIN,
        _canonical_json_bytes(
            phase_payload,
            maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
        ),
    )
    return _InventoryMaterial(
        payload=tree,
        source_sha256=source_sha256,
        source_size_bytes=source_size,
        policy_sha256=policy_sha256,
        item_keys=tuple(item_keys),
        phase_c_sha256=phase_digest,
    )


class _CoverageEntryMaterial(NamedTuple):
    item_key: str
    disposition: str
    target_key: Optional[str]
    exclusion_reason_code: Optional[str]
    secondary_tags: Tuple[str, ...]


class _CoverageMaterial(NamedTuple):
    payload: dict
    source_sha256: str
    source_size_bytes: int
    policy_sha256: str
    source_inventory_sha256: str
    entries: Tuple[_CoverageEntryMaterial, ...]
    phase_c_sha256: str


def _parse_coverage(
    value: object,
    *,
    allowed_exclusions: Tuple[str, ...],
) -> _CoverageMaterial:
    tree = _require_keys(
        value,
        (
            "entries",
            "policy_sha256",
            "source_inventory_sha256",
            "source_sha256",
            "source_size_bytes",
        ),
    )
    entries_raw = _require_list(
        tree["entries"], maximum=MAXIMUM_INVENTORY_ITEMS
    )
    entries = []
    total_tags = 0
    allowed = set(allowed_exclusions)
    for raw_entry in entries_raw:
        entry = _require_keys(
            raw_entry,
            (
                "disposition",
                "exclusion_reason_code",
                "item_key",
                "secondary_tags",
                "target_key",
            ),
        )
        disposition = entry["disposition"]
        if disposition not in (
            "event_occurrence",
            "static_context",
            "evaluation_only_label",
            "excluded_with_reason",
        ):
            _reject()
        item_key = _require_private_text(entry["item_key"])
        secondary_raw = _require_list(
            entry["secondary_tags"],
            maximum=MAXIMUM_SECONDARY_TAGS_PER_ITEM,
        )
        secondary = tuple(_require_public_id(item) for item in secondary_raw)
        if secondary != tuple(sorted(set(secondary))):
            _reject()
        total_tags += len(secondary)
        if total_tags > MAXIMUM_TOTAL_SECONDARY_TAGS:
            _reject()
        if disposition == "excluded_with_reason":
            if entry["target_key"] is not None:
                _reject()
            exclusion_reason = _require_public_id(
                entry["exclusion_reason_code"]
            )
            if exclusion_reason not in allowed:
                _reject()
            target_key = None
        else:
            if entry["exclusion_reason_code"] is not None:
                _reject()
            exclusion_reason = None
            target_key = _require_private_text(entry["target_key"])
        entries.append(
            _CoverageEntryMaterial(
                item_key=item_key,
                disposition=disposition,
                target_key=target_key,
                exclusion_reason_code=exclusion_reason,
                secondary_tags=secondary,
            )
        )
    keys = tuple(entry.item_key for entry in entries)
    if keys != tuple(sorted(set(keys))):
        _reject()
    source_sha256 = _require_digest(tree["source_sha256"])
    source_size_bytes = _require_integer(
        tree["source_size_bytes"], maximum=MAXIMUM_SOURCE_BYTES
    )
    policy_sha256 = _require_digest(tree["policy_sha256"])
    inventory_sha256 = _require_digest(tree["source_inventory_sha256"])
    if entries:
        phase_digest = _domain_sha256(
            COVERAGE_LEDGER_DIGEST_DOMAIN,
            _canonical_json_bytes(
                tree,
                maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
            ),
        )
    else:
        phase_digest = _domain_sha256(
            COVERAGE_LEDGER_DIGEST_DOMAIN,
            _canonical_json_bytes(
                {"kind": "empty"},
                maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
            ),
        )
    return _CoverageMaterial(
        payload=tree,
        source_sha256=source_sha256,
        source_size_bytes=source_size_bytes,
        policy_sha256=policy_sha256,
        source_inventory_sha256=inventory_sha256,
        entries=tuple(entries),
        phase_c_sha256=phase_digest,
    )


class _KeyedLeafMaterial(NamedTuple):
    payload: dict
    source_sha256: str
    policy_sha256: str
    format_id: str
    entry_keys: Tuple[str, ...]
    phase_c_sha256: str


def _parse_keyed_leaf(
    value: object,
    *,
    budget: _RawBudget,
    phase_domain: str,
) -> _KeyedLeafMaterial:
    tree = _require_keys(
        value, ("entries", "format_id", "policy_sha256", "source_sha256")
    )
    format_id = _require_public_id(tree["format_id"])
    entries_raw = _require_list(
        tree["entries"], maximum=MAXIMUM_KEYED_LEAF_ENTRIES
    )
    entry_keys = []
    phase_entries = []
    for raw_entry in entries_raw:
        entry = _require_keys(
            raw_entry, ("canonical_payload", "entry_key")
        )
        entry_key = _require_private_text(entry["entry_key"])
        raw_payload = budget.decode(entry["canonical_payload"])
        entry_keys.append(entry_key)
        phase_entries.append(
            {
                "canonical_payload": _blob_commitment(raw_payload),
                "entry_key": entry_key,
            }
        )
    if tuple(entry_keys) != tuple(sorted(set(entry_keys))):
        _reject()
    source_sha256 = _require_digest(tree["source_sha256"])
    policy_sha256 = _require_digest(tree["policy_sha256"])
    if entry_keys:
        phase_payload = {
            "entries": phase_entries,
            "format_id": format_id,
            "policy_sha256": policy_sha256,
            "source_sha256": source_sha256,
        }
    else:
        phase_payload = {"kind": "empty"}
    return _KeyedLeafMaterial(
        payload=tree,
        source_sha256=source_sha256,
        policy_sha256=policy_sha256,
        format_id=format_id,
        entry_keys=tuple(entry_keys),
        phase_c_sha256=_domain_sha256(
            phase_domain,
            _canonical_json_bytes(
                phase_payload,
                maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
            ),
        ),
    )


class _FieldStatusMaterial(NamedTuple):
    field_name: str
    status: str
    reason_code: Optional[str]


class _ProvenanceEntryMaterial(NamedTuple):
    provenance_key: str
    native_occurrence_sha256: str
    source_item_keys: Tuple[str, ...]
    field_statuses: Tuple[_FieldStatusMaterial, ...]


class _ProvenanceMaterial(NamedTuple):
    payload: dict
    source_sha256: str
    native_observation_sha256: str
    policy_sha256: str
    entries: Tuple[_ProvenanceEntryMaterial, ...]
    phase_c_sha256: str


def _parse_provenance(
    value: object,
    *,
    budget: _RawBudget,
    allowed_censors: Tuple[str, ...],
) -> _ProvenanceMaterial:
    tree = _require_keys(
        value,
        (
            "entries",
            "native_observation_sha256",
            "policy_sha256",
            "source_sha256",
        ),
    )
    entries_raw = _require_list(
        tree["entries"], maximum=MAXIMUM_SEMANTIC_OCCURRENCES
    )
    entries = []
    phase_entries = []
    total_links = 0
    allowed = set(allowed_censors)
    for raw_entry in entries_raw:
        entry = _require_keys(
            raw_entry,
            (
                "field_statuses",
                "native_occurrence_sha256",
                "private_format_id",
                "private_payload",
                "provenance_key",
                "source_item_keys",
            ),
        )
        provenance_key = _require_private_text(entry["provenance_key"])
        native_occurrence_sha256 = _require_digest(
            entry["native_occurrence_sha256"]
        )
        private_format_id = _require_public_id(entry["private_format_id"])
        private_payload = budget.decode(entry["private_payload"])
        source_keys_raw = _require_list(
            entry["source_item_keys"],
            maximum=MAXIMUM_SOURCE_LINKS_PER_OCCURRENCE,
        )
        source_keys = tuple(
            _require_private_text(item) for item in source_keys_raw
        )
        if not source_keys or source_keys != tuple(sorted(set(source_keys))):
            _reject()
        total_links += len(source_keys)
        if total_links > MAXIMUM_TOTAL_PROVENANCE_SOURCE_LINKS:
            _reject()
        statuses_raw = _require_list(
            entry["field_statuses"],
            maximum=MAXIMUM_FIELD_STATUSES_PER_OCCURRENCE,
        )
        statuses = []
        for raw_status in statuses_raw:
            status_tree = _require_keys(
                raw_status, ("field_name", "reason_code", "status")
            )
            status = status_tree["status"]
            if status not in ("present", "source_missing", "censored"):
                _reject()
            if status == "censored":
                reason = _require_public_id(status_tree["reason_code"])
                if reason not in allowed:
                    _reject()
            else:
                if status_tree["reason_code"] is not None:
                    _reject()
                reason = None
            statuses.append(
                _FieldStatusMaterial(
                    field_name=_require_private_text(
                        status_tree["field_name"]
                    ),
                    status=status,
                    reason_code=reason,
                )
            )
        status_names = tuple(item.field_name for item in statuses)
        if status_names != tuple(sorted(set(status_names))):
            _reject()
        entries.append(
            _ProvenanceEntryMaterial(
                provenance_key=provenance_key,
                native_occurrence_sha256=native_occurrence_sha256,
                source_item_keys=source_keys,
                field_statuses=tuple(statuses),
            )
        )
        phase_entries.append(
            {
                "field_statuses": [
                    {
                        "field_name": item.field_name,
                        "reason_code": item.reason_code,
                        "status": item.status,
                    }
                    for item in statuses
                ],
                "native_occurrence_sha256": native_occurrence_sha256,
                "private_format_id": private_format_id,
                "private_payload": _blob_commitment(private_payload),
                "provenance_key": provenance_key,
                "source_item_keys": list(source_keys),
            }
        )
    provenance_keys = tuple(item.provenance_key for item in entries)
    if provenance_keys != tuple(sorted(set(provenance_keys))):
        _reject()
    source_sha256 = _require_digest(tree["source_sha256"])
    native_sha256 = _require_digest(tree["native_observation_sha256"])
    policy_sha256 = _require_digest(tree["policy_sha256"])
    if entries:
        phase_payload = {
            "entries": phase_entries,
            "native_observation_sha256": native_sha256,
            "policy_sha256": policy_sha256,
            "source_sha256": source_sha256,
        }
    else:
        phase_payload = {"kind": "empty"}
    return _ProvenanceMaterial(
        payload=tree,
        source_sha256=source_sha256,
        native_observation_sha256=native_sha256,
        policy_sha256=policy_sha256,
        entries=tuple(entries),
        phase_c_sha256=_domain_sha256(
            PRIVATE_PROVENANCE_DIGEST_DOMAIN,
            _canonical_json_bytes(
                phase_payload,
                maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
            ),
        ),
    )


class _FittedMaterial(NamedTuple):
    payload: dict
    present: bool
    phase_c_sha256: str
    descriptor_sha256: Optional[str]
    adapter_id: Optional[str]
    adapter_version: Optional[str]
    contract_version: Optional[str]
    policy_sha256: Optional[str]
    schema_sha256: Optional[str]
    split_manifest_sha256: Optional[str]
    training_group_set_sha256: Optional[str]


def _parse_fitted_state(
    value: object,
    *,
    budget: _RawBudget,
) -> _FittedMaterial:
    if type(value) is dict and tuple(sorted(value)) == ("kind",):
        if value["kind"] != "no_fit":
            _reject()
        phase_digest = _domain_sha256(
            FITTED_STATE_DIGEST_DOMAIN,
            _canonical_json_bytes(
                {"kind": "no_fit"},
                maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
            ),
        )
        return _FittedMaterial(
            payload=value,
            present=False,
            phase_c_sha256=phase_digest,
            descriptor_sha256=None,
            adapter_id=None,
            adapter_version=None,
            contract_version=None,
            policy_sha256=None,
            schema_sha256=None,
            split_manifest_sha256=None,
            training_group_set_sha256=None,
        )
    tree = _require_keys(
        value,
        (
            "adapter_id",
            "adapter_version",
            "contract_version",
            "descriptor_sha256",
            "fit_configuration",
            "fitted_parameters",
            "policy_sha256",
            "schema_sha256",
            "split_manifest_sha256",
            "training_group_set_sha256",
            "unseen_value_policy_id",
        ),
    )
    adapter_id = _require_public_id(tree["adapter_id"])
    adapter_version = tree["adapter_version"]
    if (
        type(adapter_version) is not str
        or _VERSION_RE.fullmatch(adapter_version) is None
    ):
        _reject()
    if tree["contract_version"] != ADAPTER_CONTRACT_VERSION:
        _reject()
    fit_tree = _require_keys(
        tree["fit_configuration"], ("format_id", "payload")
    )
    parameter_tree = _require_keys(
        tree["fitted_parameters"], ("format_id", "payload")
    )
    fit_format = _require_public_id(fit_tree["format_id"])
    parameter_format = _require_public_id(parameter_tree["format_id"])
    fit_bytes = budget.decode(fit_tree["payload"])
    parameter_bytes = budget.decode(parameter_tree["payload"])
    descriptor_sha256 = _require_digest(tree["descriptor_sha256"])
    policy_sha256 = _require_digest(tree["policy_sha256"])
    schema_sha256 = _require_digest(tree["schema_sha256"])
    split_sha256 = _require_digest(tree["split_manifest_sha256"])
    training_sha256 = _require_digest(tree["training_group_set_sha256"])
    unseen_policy = _require_public_id(tree["unseen_value_policy_id"])
    phase_payload = {
        "adapter_id": adapter_id,
        "adapter_version": adapter_version,
        "contract_version": ADAPTER_CONTRACT_VERSION,
        "descriptor_sha256": descriptor_sha256,
        "fit_configuration": {
            "format_id": fit_format,
            **_blob_commitment(fit_bytes),
        },
        "fitted_parameters": {
            "format_id": parameter_format,
            **_blob_commitment(parameter_bytes),
        },
        "policy_sha256": policy_sha256,
        "schema_sha256": schema_sha256,
        "split_manifest_sha256": split_sha256,
        "training_group_set_sha256": training_sha256,
        "unseen_value_policy_id": unseen_policy,
    }
    return _FittedMaterial(
        payload=tree,
        present=True,
        phase_c_sha256=_domain_sha256(
            FITTED_STATE_DIGEST_DOMAIN,
            _canonical_json_bytes(
                phase_payload,
                maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
            ),
        ),
        descriptor_sha256=descriptor_sha256,
        adapter_id=adapter_id,
        adapter_version=adapter_version,
        contract_version=ADAPTER_CONTRACT_VERSION,
        policy_sha256=policy_sha256,
        schema_sha256=schema_sha256,
        split_manifest_sha256=split_sha256,
        training_group_set_sha256=training_sha256,
    )


class _SemanticMaterial(NamedTuple):
    payload: dict
    source_sha256: str
    schema_sha256: str
    policy_sha256: str
    record_count: int
    phase_c_sha256: str


def _parse_semantic_reconstruction(
    value: object,
    *,
    budget: _RawBudget,
) -> _SemanticMaterial:
    tree = _require_keys(
        value,
        (
            "canonical_payload",
            "policy_sha256",
            "record_count",
            "schema_sha256",
            "semantic_format_id",
            "source_sha256",
        ),
    )
    raw_payload = budget.decode(tree["canonical_payload"])
    source_sha256 = _require_digest(tree["source_sha256"])
    schema_sha256 = _require_digest(tree["schema_sha256"])
    policy_sha256 = _require_digest(tree["policy_sha256"])
    record_count = _require_integer(
        tree["record_count"], maximum=MAXIMUM_INVENTORY_ITEMS
    )
    format_id = _require_public_id(tree["semantic_format_id"])
    phase_payload = {
        "canonical_payload": _blob_commitment(raw_payload),
        "policy_sha256": policy_sha256,
        "record_count": record_count,
        "schema_sha256": schema_sha256,
        "semantic_format_id": format_id,
        "source_sha256": source_sha256,
    }
    return _SemanticMaterial(
        payload=tree,
        source_sha256=source_sha256,
        schema_sha256=schema_sha256,
        policy_sha256=policy_sha256,
        record_count=record_count,
        phase_c_sha256=_domain_sha256(
            SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN,
            _canonical_json_bytes(
                phase_payload,
                maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
            ),
        ),
    )


class _BundleMaterial(NamedTuple):
    tree: dict
    bundle_sha256: str
    descriptor_sha256: str
    source_byte_count: int
    source_sha256: str
    split_manifest_sha256: str
    expected_configuration_sha256: str
    expected_evidence_sha256: str
    expected_native_observation_sha256: str
    source_inventory_sha256: str
    coverage_ledger_sha256: str
    static_context_sha256: str
    evaluation_labels_sha256: str
    private_provenance_sha256: str
    fitted_state_sha256: str
    semantic_reconstruction_sha256: str


_EXPECTED_WRAPPER_DOMAINS = MappingProxyType(
    {
        "coverage_ledger": PRIVATE_COVERAGE_LEDGER_DIGEST_DOMAIN,
        "detached_native_observation": NATIVE_OBSERVATION_DIGEST_DOMAIN,
        "evaluation_labels": PRIVATE_EVALUATION_LABELS_DIGEST_DOMAIN,
        "expected_evidence_commitment": EXPECTED_EVIDENCE_DIGEST_DOMAIN,
        "fitted_state": PRIVATE_FITTED_STATE_DIGEST_DOMAIN,
        "identity_bearing_native_configuration": (
            PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN
        ),
        "private_provenance": (
            PRIVATE_PROVENANCE_PAYLOAD_DIGEST_DOMAIN
        ),
        "semantic_reconstruction": (
            PRIVATE_SEMANTIC_RECONSTRUCTION_DIGEST_DOMAIN
        ),
        "source_inventory": PRIVATE_SOURCE_INVENTORY_DIGEST_DOMAIN,
        "static_context": PRIVATE_STATIC_CONTEXT_DIGEST_DOMAIN,
    }
)


def _reason_registry(value: object) -> Tuple[str, ...]:
    raw = _require_list(value, maximum=MAXIMUM_REASON_CODES)
    result = tuple(_require_public_id(item) for item in raw)
    if result != tuple(sorted(set(result))):
        _reject()
    return result


def _training_group_set_sha256(
    entries: Tuple[_PartitionMaterial, ...],
) -> str:
    groups = tuple(
        sorted(
            {
                item.group_id
                for item in entries
                if item.split == "train"
            }
        )
    )
    return _domain_sha256(
        TRAINING_GROUP_SET_DIGEST_DOMAIN,
        _canonical_json_bytes(
            {"group_ids": list(groups), "unicode_profile": UNICODE_PROFILE},
            maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
        ),
    )


def _validate_cross_leaf_relations(
    *,
    descriptor: _DescriptorMaterial,
    partition: _PartitionMaterial,
    split_entries: Tuple[_PartitionMaterial, ...],
    split_sha256: str,
    source_bytes: bytes,
    configuration: _ConfigurationMaterial,
    inventory: _InventoryMaterial,
    coverage: _CoverageMaterial,
    static_context: _KeyedLeafMaterial,
    evaluation_labels: _KeyedLeafMaterial,
    provenance: _ProvenanceMaterial,
    fitted: _FittedMaterial,
    semantic: _SemanticMaterial,
) -> None:
    source_sha256 = _plain_sha256(source_bytes)
    source_size = len(source_bytes)
    policy_sha256 = descriptor.policy_sha256
    if (
        configuration.sample_id != partition.sample_id
        or configuration.group_id != partition.group_id
        or partition not in split_entries
        or configuration.schema.time_measure != descriptor.time_measure
        or configuration.schema.multiplicity_mode
        != descriptor.multiplicity_mode
    ):
        _reject()
    for leaf_source, leaf_size, leaf_policy in (
        (
            inventory.source_sha256,
            inventory.source_size_bytes,
            inventory.policy_sha256,
        ),
        (
            coverage.source_sha256,
            coverage.source_size_bytes,
            coverage.policy_sha256,
        ),
    ):
        if (
            leaf_source != source_sha256
            or leaf_size != source_size
            or leaf_policy != policy_sha256
        ):
            _reject()
    for leaf_source, leaf_policy in (
        (static_context.source_sha256, static_context.policy_sha256),
        (
            evaluation_labels.source_sha256,
            evaluation_labels.policy_sha256,
        ),
        (provenance.source_sha256, provenance.policy_sha256),
        (semantic.source_sha256, semantic.policy_sha256),
    ):
        if leaf_source != source_sha256 or leaf_policy != policy_sha256:
            _reject()
    if (
        coverage.source_inventory_sha256 != inventory.phase_c_sha256
        or tuple(item.item_key for item in coverage.entries)
        != inventory.item_keys
    ):
        _reject()
    if semantic.schema_sha256 != configuration.schema.schema_sha256:
        _reject()
    if (
        provenance.native_observation_sha256
        != configuration.native_observation_sha256
    ):
        _reject()

    provenance_by_key = {
        item.provenance_key: item for item in provenance.entries
    }
    event_targets = {
        item.target_key
        for item in coverage.entries
        if item.disposition == "event_occurrence"
    }
    static_targets = {
        item.target_key
        for item in coverage.entries
        if item.disposition == "static_context"
    }
    label_targets = {
        item.target_key
        for item in coverage.entries
        if item.disposition == "evaluation_only_label"
    }
    if (
        event_targets != set(provenance_by_key)
        or static_targets != set(static_context.entry_keys)
        or label_targets != set(evaluation_labels.entry_keys)
    ):
        _reject()
    if Counter(configuration.native_occurrence_sha256) != Counter(
        item.native_occurrence_sha256 for item in provenance.entries
    ):
        _reject()
    event_items_by_target: Dict[str, List[str]] = {}
    for item in coverage.entries:
        if item.disposition == "event_occurrence":
            if item.target_key is None:
                _reject()
            event_items_by_target.setdefault(item.target_key, []).append(
                item.item_key
            )
    for key, item in provenance_by_key.items():
        if item.source_item_keys != tuple(
            sorted(event_items_by_target.get(key, ()))
        ):
            _reject()

    occurrence_by_digest = {
        digest: occurrence
        for digest, occurrence in zip(
            configuration.native_occurrence_sha256,
            configuration.occurrences,
        )
    }
    for item in provenance.entries:
        occurrence = occurrence_by_digest.get(item.native_occurrence_sha256)
        if occurrence is None:
            _reject()
        event_type = configuration.schema.event_types_by_id[
            occurrence.event_type
        ]
        applicable = tuple(field.name for field in event_type.fields)
        statuses = {status.field_name: status for status in item.field_statuses}
        if tuple(sorted(statuses)) != applicable:
            _reject()
        for name in applicable:
            present = name in occurrence.marks
            if present != (statuses[name].status == "present"):
                _reject()

    if descriptor.static_context != bool(static_context.entry_keys):
        _reject()
    if descriptor.evaluation_labels != bool(
        evaluation_labels.entry_keys
    ):
        _reject()
    if descriptor.private_provenance != bool(provenance.entries):
        _reject()
    if configuration.occurrences and not provenance.entries:
        _reject()
    if descriptor.fitted_state != fitted.present:
        _reject()
    if fitted.present and (
        fitted.descriptor_sha256 != descriptor.descriptor_sha256
        or fitted.adapter_id != descriptor.adapter_id
        or fitted.adapter_version != descriptor.adapter_version
        or fitted.contract_version != descriptor.contract_version
        or fitted.policy_sha256 != descriptor.policy_sha256
        or fitted.schema_sha256 != configuration.schema.schema_sha256
        or fitted.split_manifest_sha256 != split_sha256
        or fitted.training_group_set_sha256
        != _training_group_set_sha256(split_entries)
    ):
        _reject()


def _expected_evidence_tree(
    *,
    inventory: _InventoryMaterial,
    coverage: _CoverageMaterial,
    static_context: _KeyedLeafMaterial,
    evaluation_labels: _KeyedLeafMaterial,
    provenance: _ProvenanceMaterial,
    fitted: _FittedMaterial,
    semantic: _SemanticMaterial,
    native_sha256: str,
) -> dict:
    return {
        "coverage": {
            "coverage_ledger_sha256": coverage.phase_c_sha256,
            "policy_sha256": coverage.policy_sha256,
            "source_inventory_sha256": (
                coverage.source_inventory_sha256
            ),
            "source_sha256": coverage.source_sha256,
            "source_size_bytes": coverage.source_size_bytes,
        },
        "evaluation_labels": {
            "evaluation_labels_sha256": (
                evaluation_labels.phase_c_sha256
            ),
            "format_id": evaluation_labels.format_id,
            "policy_sha256": evaluation_labels.policy_sha256,
            "source_sha256": evaluation_labels.source_sha256,
        },
        "fitted_state_sha256": fitted.phase_c_sha256,
        "native_observation_sha256": native_sha256,
        "private_provenance": {
            "native_observation_sha256": (
                provenance.native_observation_sha256
            ),
            "policy_sha256": provenance.policy_sha256,
            "private_provenance_sha256": provenance.phase_c_sha256,
            "source_sha256": provenance.source_sha256,
        },
        "semantic_reconstruction_sha256": semantic.phase_c_sha256,
        "source_inventory_sha256": inventory.phase_c_sha256,
        "static_context": {
            "format_id": static_context.format_id,
            "policy_sha256": static_context.policy_sha256,
            "source_sha256": static_context.source_sha256,
            "static_context_sha256": static_context.phase_c_sha256,
        },
    }


def _parse_and_validate_bundle(
    bundle_bytes: bytes,
    *,
    request: _RequestMaterial,
    response: _ResponseMaterial,
    v1_result: _v1.IndependentOracleByteVerificationResultV1,
) -> _BundleMaterial:
    tree = _strict_json_bytes(
        bundle_bytes, maximum=MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES
    )
    _require_keys(tree, _TOP_LEVEL_KEYS)
    if (
        tree["artifact_type"] != EXPECTED_LEAF_BUNDLE_ARTIFACT_TYPE
        or tree["format_version"] != "1"
    ):
        _reject()
    allowed_censors = _reason_registry(
        tree["allowed_censor_reason_codes"]
    )
    allowed_exclusions = _reason_registry(
        tree["allowed_exclusion_reason_codes"]
    )
    if len(allowed_censors) + len(allowed_exclusions) > MAXIMUM_REASON_CODES:
        _reject()
    expected_tree = _require_keys(tree["expected"], _EXPECTED_KEYS)
    wrappers = {
        name: _parse_wrapper(
            expected_tree[name],
            domain=_EXPECTED_WRAPPER_DOMAINS[name],
        )
        for name in _EXPECTED_KEYS
    }
    descriptor = _parse_descriptor(request.descriptor_bytes)
    partition = _parse_partition(request.partition_bytes)
    split_entries, split_sha256 = _parse_split_manifest(
        request.split_manifest_bytes
    )
    source_sha256 = _plain_sha256(request.source_bytes)
    if (
        _require_digest(tree["descriptor_sha256"])
        != descriptor.descriptor_sha256
        or _require_digest(tree["source_sha256"]) != source_sha256
        or _require_integer(
            tree["source_byte_count"], maximum=MAXIMUM_SOURCE_BYTES
        )
        != len(request.source_bytes)
        or _require_digest(tree["split_manifest_sha256"]) != split_sha256
        or descriptor.descriptor_sha256
        != v1_result.receipt.descriptor_sha256
        or split_sha256 != v1_result.receipt.split_manifest_sha256
    ):
        _reject()

    configuration_wrapper = wrappers[
        "identity_bearing_native_configuration"
    ]
    configuration = _parse_configuration(configuration_wrapper.payload)
    if configuration.payload_bytes != response.configuration_bytes:
        _reject()
    if (
        configuration_wrapper.payload_sha256
        != _domain_sha256(
            PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN,
            configuration.payload_bytes,
        )
        or configuration_wrapper.payload_sha256
        != v1_result.receipt.expected_configuration_sha256
    ):
        _reject()

    budget = _RawBudget()
    inventory = _parse_source_inventory(
        wrappers["source_inventory"].payload, budget=budget
    )
    coverage = _parse_coverage(
        wrappers["coverage_ledger"].payload,
        allowed_exclusions=allowed_exclusions,
    )
    static_context = _parse_keyed_leaf(
        wrappers["static_context"].payload,
        budget=budget,
        phase_domain=STATIC_CONTEXT_DIGEST_DOMAIN,
    )
    evaluation_labels = _parse_keyed_leaf(
        wrappers["evaluation_labels"].payload,
        budget=budget,
        phase_domain=EVALUATION_LABELS_DIGEST_DOMAIN,
    )
    provenance = _parse_provenance(
        wrappers["private_provenance"].payload,
        budget=budget,
        allowed_censors=allowed_censors,
    )
    fitted = _parse_fitted_state(
        wrappers["fitted_state"].payload, budget=budget
    )
    semantic = _parse_semantic_reconstruction(
        wrappers["semantic_reconstruction"].payload, budget=budget
    )
    _validate_cross_leaf_relations(
        descriptor=descriptor,
        partition=partition,
        split_entries=split_entries,
        split_sha256=split_sha256,
        source_bytes=request.source_bytes,
        configuration=configuration,
        inventory=inventory,
        coverage=coverage,
        static_context=static_context,
        evaluation_labels=evaluation_labels,
        provenance=provenance,
        fitted=fitted,
        semantic=semantic,
    )

    detached_wrapper = wrappers["detached_native_observation"]
    if (
        detached_wrapper.payload != configuration.detached_payload
        or detached_wrapper.payload_bytes
        != configuration.detached_payload_bytes
        or detached_wrapper.payload_sha256
        != configuration.native_observation_sha256
        or response.native_sha256
        != configuration.native_observation_sha256
        or v1_result.receipt.expected_native_observation_sha256
        != configuration.native_observation_sha256
    ):
        _reject()
    expected_evidence = _expected_evidence_tree(
        inventory=inventory,
        coverage=coverage,
        static_context=static_context,
        evaluation_labels=evaluation_labels,
        provenance=provenance,
        fitted=fitted,
        semantic=semantic,
        native_sha256=configuration.native_observation_sha256,
    )
    expected_evidence_bytes = _canonical_json_bytes(
        expected_evidence,
        maximum=_v1.MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
    )
    expected_evidence_sha256 = _domain_sha256(
        EXPECTED_EVIDENCE_DIGEST_DOMAIN, expected_evidence_bytes
    )
    evidence_wrapper = wrappers["expected_evidence_commitment"]
    if (
        evidence_wrapper.payload != expected_evidence
        or evidence_wrapper.payload_bytes != expected_evidence_bytes
        or evidence_wrapper.payload_sha256 != expected_evidence_sha256
        or response.evidence_bytes != expected_evidence_bytes
        or v1_result.receipt.expected_evidence_sha256
        != expected_evidence_sha256
    ):
        _reject()
    return _BundleMaterial(
        tree=tree,
        bundle_sha256=_domain_sha256(
            EXPECTED_LEAF_BUNDLE_DIGEST_DOMAIN, bundle_bytes
        ),
        descriptor_sha256=descriptor.descriptor_sha256,
        source_byte_count=len(request.source_bytes),
        source_sha256=source_sha256,
        split_manifest_sha256=split_sha256,
        expected_configuration_sha256=configuration_wrapper.payload_sha256,
        expected_evidence_sha256=expected_evidence_sha256,
        expected_native_observation_sha256=(
            configuration.native_observation_sha256
        ),
        source_inventory_sha256=inventory.phase_c_sha256,
        coverage_ledger_sha256=coverage.phase_c_sha256,
        static_context_sha256=static_context.phase_c_sha256,
        evaluation_labels_sha256=evaluation_labels.phase_c_sha256,
        private_provenance_sha256=provenance.phase_c_sha256,
        fitted_state_sha256=fitted.phase_c_sha256,
        semantic_reconstruction_sha256=semantic.phase_c_sha256,
    )


@dataclass(frozen=True)
class IndependentExpectedLeafBundleVerificationReceiptV1:
    """Deterministic expected-leaf structural receipt; never authority."""

    verification_input_sha256: str
    v1_verification_receipt_sha256: str
    oracle_id: str
    expected_leaf_bundle_byte_count: int
    expected_leaf_bundle_sha256: str
    descriptor_sha256: str
    source_byte_count: int
    source_sha256: str
    split_manifest_sha256: str
    expected_configuration_sha256: str
    expected_evidence_sha256: str
    expected_native_observation_sha256: str
    source_inventory_sha256: str
    coverage_ledger_sha256: str
    static_context_sha256: str
    evaluation_labels_sha256: str
    private_provenance_sha256: str
    fitted_state_sha256: str
    semantic_reconstruction_sha256: str
    artifact_type: str = field(
        default=EXPECTED_LEAF_BUNDLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)
    verifier_id: str = field(
        default=EXPECTED_LEAF_BUNDLE_VERIFIER_ID, init=False
    )
    implementation_status_id: str = field(
        default=EXPECTED_LEAF_BUNDLE_VERIFIER_IMPLEMENTATION_STATUS,
        init=False,
    )
    status_id: str = field(
        default=EXPECTED_LEAF_BUNDLE_VERIFICATION_STATUS, init=False
    )
    decision_status: str = field(
        default=EXPECTED_LEAF_BUNDLE_VERIFIER_DECISION_STATUS,
        init=False,
    )
    semantic_scope_id: str = field(
        default=EXPECTED_LEAF_BUNDLE_SEMANTIC_SCOPE_ID,
        init=False,
    )
    v1_raw_byte_bindings_validated: bool = field(
        default=True, init=False
    )
    response_payload_schema_independently_validated: bool = field(
        default=True, init=False
    )
    expected_leaf_cross_relations_independently_validated: bool = field(
        default=True, init=False
    )
    expected_leaf_commitments_independently_recomputed: bool = field(
        default=True, init=False
    )
    expected_evidence_leaf_complete: bool = field(
        default=True, init=False
    )
    expected_private_payload_set_rebuilt: bool = field(
        default=True, init=False
    )
    decision_eligible: bool = field(default=False, init=False)
    execution_attested: bool = field(default=False, init=False)
    containment_attested: bool = field(default=False, init=False)
    custody_authenticated: bool = field(default=False, init=False)
    approved_profile_authenticated: bool = field(default=False, init=False)
    execution_input_set_membership_authenticated: bool = field(
        default=False, init=False
    )
    case_authority_authenticated: bool = field(default=False, init=False)
    response_payload_schema_authenticated: bool = field(
        default=False, init=False
    )
    semantic_truth_attested: bool = field(default=False, init=False)
    format_specific_payload_semantics_attested: bool = field(
        default=False, init=False
    )
    source_policy_semantics_independently_evaluated: bool = field(
        default=False, init=False
    )
    interpreter_execution_identity_attested: bool = field(
        default=False, init=False
    )
    elapsed_time_authenticated: bool = field(default=False, init=False)
    platform_observations_authenticated: bool = field(
        default=False, init=False
    )
    process_observations_authenticated: bool = field(
        default=False, init=False
    )
    adapted_evidence_leaf_complete: bool = field(
        default=False, init=False
    )
    publication_artifacts_rebuilt: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if type(self) is not IndependentExpectedLeafBundleVerificationReceiptV1:
            raise TypeError("expected-leaf verification receipt must be exact")
        _validate_receipt_fields(self)


_RECEIPT_DIGEST_FIELDS = (
    "verification_input_sha256",
    "v1_verification_receipt_sha256",
    "expected_leaf_bundle_sha256",
    "descriptor_sha256",
    "source_sha256",
    "split_manifest_sha256",
    "expected_configuration_sha256",
    "expected_evidence_sha256",
    "expected_native_observation_sha256",
    "source_inventory_sha256",
    "coverage_ledger_sha256",
    "static_context_sha256",
    "evaluation_labels_sha256",
    "private_provenance_sha256",
    "fitted_state_sha256",
    "semantic_reconstruction_sha256",
)
_RECEIPT_TRUE_FIELDS = (
    "v1_raw_byte_bindings_validated",
    "response_payload_schema_independently_validated",
    "expected_leaf_cross_relations_independently_validated",
    "expected_leaf_commitments_independently_recomputed",
    "expected_evidence_leaf_complete",
    "expected_private_payload_set_rebuilt",
)
_RECEIPT_FALSE_FIELDS = (
    "decision_eligible",
    "execution_attested",
    "containment_attested",
    "custody_authenticated",
    "approved_profile_authenticated",
    "execution_input_set_membership_authenticated",
    "case_authority_authenticated",
    "response_payload_schema_authenticated",
    "semantic_truth_attested",
    "format_specific_payload_semantics_attested",
    "source_policy_semantics_independently_evaluated",
    "interpreter_execution_identity_attested",
    "elapsed_time_authenticated",
    "platform_observations_authenticated",
    "process_observations_authenticated",
    "adapted_evidence_leaf_complete",
    "publication_artifacts_rebuilt",
)


def _validate_receipt_fields(
    value: IndependentExpectedLeafBundleVerificationReceiptV1,
) -> None:
    try:
        for name in _RECEIPT_DIGEST_FIELDS:
            _require_digest(getattr(value, name))
        _require_ascii_token(value.oracle_id)
        _require_integer(
            value.expected_leaf_bundle_byte_count,
            maximum=MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES,
            minimum=1,
        )
        _require_integer(
            value.source_byte_count,
            maximum=MAXIMUM_SOURCE_BYTES,
            minimum=1,
        )
        fixed = {
            "artifact_type": (
                EXPECTED_LEAF_BUNDLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE
            ),
            "format_version": "1",
            "verifier_id": EXPECTED_LEAF_BUNDLE_VERIFIER_ID,
            "implementation_status_id": (
                EXPECTED_LEAF_BUNDLE_VERIFIER_IMPLEMENTATION_STATUS
            ),
            "status_id": EXPECTED_LEAF_BUNDLE_VERIFICATION_STATUS,
            "decision_status": (
                EXPECTED_LEAF_BUNDLE_VERIFIER_DECISION_STATUS
            ),
            "semantic_scope_id": EXPECTED_LEAF_BUNDLE_SEMANTIC_SCOPE_ID,
        }
        if any(
            type(getattr(value, name)) is not type(expected)
            or getattr(value, name) != expected
            for name, expected in fixed.items()
        ):
            _reject()
        if any(getattr(value, name) is not True for name in _RECEIPT_TRUE_FIELDS):
            _reject()
        if any(
            getattr(value, name) is not False
            for name in _RECEIPT_FALSE_FIELDS
        ):
            _reject()
    except _Rejected as error:
        raise ValueError(
            "expected-leaf verification receipt fields are invalid"
        ) from error


def _receipt_tree(
    value: IndependentExpectedLeafBundleVerificationReceiptV1,
) -> dict:
    if type(value) is not IndependentExpectedLeafBundleVerificationReceiptV1:
        raise TypeError("expected-leaf verification receipt must be exact")
    IndependentExpectedLeafBundleVerificationReceiptV1.__post_init__(value)
    return {item.name: getattr(value, item.name) for item in fields(value)}


def independent_expected_leaf_bundle_verification_receipt_bytes(
    value: IndependentExpectedLeafBundleVerificationReceiptV1,
) -> bytes:
    """Return canonical ASCII JSON for the supplemental nondecision receipt."""

    try:
        return _canonical_json_bytes(
            _receipt_tree(value),
            maximum=MAXIMUM_EXPECTED_LEAF_VERIFICATION_RECEIPT_BYTES,
        )
    except (
        AttributeError,
        TypeError,
        ValueError,
        _Rejected,
        RecursionError,
    ):
        _fail(ExpectedLeafBundleVerificationCode.CANONICALIZATION_FAILED)


def independent_expected_leaf_bundle_verification_receipt_sha256(
    value: IndependentExpectedLeafBundleVerificationReceiptV1,
) -> str:
    """Return the domain-separated supplemental receipt commitment."""

    payload = independent_expected_leaf_bundle_verification_receipt_bytes(value)
    try:
        return _domain_sha256(
            EXPECTED_LEAF_BUNDLE_VERIFICATION_RECEIPT_DIGEST_DOMAIN,
            payload,
        )
    except _Rejected:
        _fail(ExpectedLeafBundleVerificationCode.CANONICALIZATION_FAILED)


def validate_independent_expected_leaf_bundle_verification_receipt(
    value: object,
) -> IndependentExpectedLeafBundleVerificationReceiptV1:
    """Return a fresh structural receipt snapshot without evidence authority."""

    if type(value) is not IndependentExpectedLeafBundleVerificationReceiptV1:
        _fail(ExpectedLeafBundleVerificationCode.RECEIPT_INVALID)
    try:
        IndependentExpectedLeafBundleVerificationReceiptV1.__post_init__(value)
        return IndependentExpectedLeafBundleVerificationReceiptV1(
            **{
                item.name: getattr(value, item.name)
                for item in fields(value)
                if item.init
            }
        )
    except ExpectedLeafBundleVerificationError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(ExpectedLeafBundleVerificationCode.RECEIPT_INVALID)


@dataclass(frozen=True)
class IndependentExpectedLeafBundleVerificationResultV1:
    """Constructible transport; raw-input deep validation remains required."""

    receipt: IndependentExpectedLeafBundleVerificationReceiptV1
    receipt_bytes: bytes
    receipt_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not IndependentExpectedLeafBundleVerificationResultV1:
            raise TypeError("expected-leaf verification result must be exact")
        _validate_result_transport(self)


def _validate_result_transport(
    value: IndependentExpectedLeafBundleVerificationResultV1,
) -> None:
    receipt = validate_independent_expected_leaf_bundle_verification_receipt(
        value.receipt
    )
    if (
        type(value.receipt_bytes) is not bytes
        or not value.receipt_bytes
        or len(value.receipt_bytes)
        > MAXIMUM_EXPECTED_LEAF_VERIFICATION_RECEIPT_BYTES
        or type(value.receipt_sha256) is not str
    ):
        raise ValueError("expected-leaf result transport is outside its bound")
    try:
        _require_digest(value.receipt_sha256)
    except _Rejected as error:
        raise ValueError("expected-leaf result digest is invalid") from error
    if (
        independent_expected_leaf_bundle_verification_receipt_bytes(receipt)
        != value.receipt_bytes
        or independent_expected_leaf_bundle_verification_receipt_sha256(
            receipt
        )
        != value.receipt_sha256
    ):
        raise ValueError("expected-leaf result transport differs")


def _verification_input_sha256(
    value: IndependentExpectedLeafBundleVerificationInputV1,
    *,
    v1_input_sha256: str,
) -> str:
    return _named_sequence_sha256(
        EXPECTED_LEAF_BUNDLE_VERIFICATION_INPUT_DIGEST_DOMAIN,
        (
            b"oracle_verification_input_sha256",
            b"expected_leaf_bundle_bytes",
        ),
        (
            v1_input_sha256.encode("ascii"),
            value.expected_leaf_bundle_bytes,
        ),
    )


def _build_verified_result(
    value: IndependentExpectedLeafBundleVerificationInputV1,
) -> IndependentExpectedLeafBundleVerificationResultV1:
    try:
        v1_result = _v1.verify_independent_oracle_bytes(value.oracle_input)
    except _v1.IndependentOracleVerificationError:
        _fail(ExpectedLeafBundleVerificationCode.V1_VERIFICATION_FAILED)
    try:
        request, response = _parse_v1_material(value.oracle_input)
    except _Rejected:
        _fail(ExpectedLeafBundleVerificationCode.FRAME_INVALID)
    try:
        _strict_json_bytes(
            value.expected_leaf_bundle_bytes,
            maximum=MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES,
        )
    except _Rejected:
        _fail(ExpectedLeafBundleVerificationCode.JSON_INVALID)
    try:
        bundle = _parse_and_validate_bundle(
            value.expected_leaf_bundle_bytes,
            request=request,
            response=response,
            v1_result=v1_result,
        )
    except _Rejected:
        _fail(ExpectedLeafBundleVerificationCode.BINDING_MISMATCH)
    try:
        receipt = IndependentExpectedLeafBundleVerificationReceiptV1(
            verification_input_sha256=_verification_input_sha256(
                value,
                v1_input_sha256=(
                    v1_result.receipt.verification_input_sha256
                ),
            ),
            v1_verification_receipt_sha256=v1_result.receipt_sha256,
            oracle_id=v1_result.receipt.oracle_id,
            expected_leaf_bundle_byte_count=len(
                value.expected_leaf_bundle_bytes
            ),
            expected_leaf_bundle_sha256=bundle.bundle_sha256,
            descriptor_sha256=bundle.descriptor_sha256,
            source_byte_count=bundle.source_byte_count,
            source_sha256=bundle.source_sha256,
            split_manifest_sha256=bundle.split_manifest_sha256,
            expected_configuration_sha256=(
                bundle.expected_configuration_sha256
            ),
            expected_evidence_sha256=bundle.expected_evidence_sha256,
            expected_native_observation_sha256=(
                bundle.expected_native_observation_sha256
            ),
            source_inventory_sha256=bundle.source_inventory_sha256,
            coverage_ledger_sha256=bundle.coverage_ledger_sha256,
            static_context_sha256=bundle.static_context_sha256,
            evaluation_labels_sha256=bundle.evaluation_labels_sha256,
            private_provenance_sha256=bundle.private_provenance_sha256,
            fitted_state_sha256=bundle.fitted_state_sha256,
            semantic_reconstruction_sha256=(
                bundle.semantic_reconstruction_sha256
            ),
        )
        receipt_bytes = (
            independent_expected_leaf_bundle_verification_receipt_bytes(
                receipt
            )
        )
        return IndependentExpectedLeafBundleVerificationResultV1(
            receipt=receipt,
            receipt_bytes=receipt_bytes,
            receipt_sha256=(
                independent_expected_leaf_bundle_verification_receipt_sha256(
                    receipt
                )
            ),
        )
    except ExpectedLeafBundleVerificationError:
        raise
    except (_Rejected, AttributeError, TypeError, ValueError):
        _fail(ExpectedLeafBundleVerificationCode.INTERNAL_ERROR)


def verify_independent_expected_leaf_bundle(
    value: IndependentExpectedLeafBundleVerificationInputV1,
) -> IndependentExpectedLeafBundleVerificationResultV1:
    """Validate V1 first, then independently rebuild expected leaf schemas."""

    raw_input = _snapshot_input(value)
    try:
        return _build_verified_result(raw_input)
    except ExpectedLeafBundleVerificationError:
        raise
    except Exception:
        _fail(ExpectedLeafBundleVerificationCode.INTERNAL_ERROR)


def validate_independent_expected_leaf_bundle_verification_result(
    value: IndependentExpectedLeafBundleVerificationResultV1,
    raw_input: IndependentExpectedLeafBundleVerificationInputV1,
) -> IndependentExpectedLeafBundleVerificationResultV1:
    """Rerun both verification layers and require exact result identity."""

    if type(value) is not IndependentExpectedLeafBundleVerificationResultV1:
        _fail(ExpectedLeafBundleVerificationCode.RECEIPT_INVALID)
    try:
        _validate_result_transport(value)
    except ExpectedLeafBundleVerificationError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(ExpectedLeafBundleVerificationCode.RECEIPT_INVALID)
    expected = verify_independent_expected_leaf_bundle(raw_input)
    if value != expected:
        _fail(ExpectedLeafBundleVerificationCode.RECEIPT_INVALID)
    return expected


__all__ = [
    "EXPECTED_LEAF_BUNDLE_ARTIFACT_TYPE",
    "EXPECTED_LEAF_BUNDLE_DIGEST_DOMAIN",
    "EXPECTED_LEAF_BUNDLE_SEMANTIC_SCOPE_ID",
    "EXPECTED_LEAF_BUNDLE_VERIFICATION_INPUT_DIGEST_DOMAIN",
    "EXPECTED_LEAF_BUNDLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE",
    "EXPECTED_LEAF_BUNDLE_VERIFICATION_RECEIPT_DIGEST_DOMAIN",
    "EXPECTED_LEAF_BUNDLE_VERIFICATION_STATUS",
    "EXPECTED_LEAF_BUNDLE_VERIFIER_DECISION_STATUS",
    "EXPECTED_LEAF_BUNDLE_VERIFIER_ID",
    "EXPECTED_LEAF_BUNDLE_VERIFIER_IMPLEMENTATION_STATUS",
    "ExpectedLeafBundleVerificationCode",
    "ExpectedLeafBundleVerificationError",
    "IndependentExpectedLeafBundleVerificationInputV1",
    "IndependentExpectedLeafBundleVerificationReceiptV1",
    "IndependentExpectedLeafBundleVerificationResultV1",
    "MAXIMUM_EXPECTED_LEAF_BUNDLE_BYTES",
    "MAXIMUM_EXPECTED_LEAF_VERIFICATION_INPUT_BYTES",
    "independent_expected_leaf_bundle_verification_receipt_bytes",
    "independent_expected_leaf_bundle_verification_receipt_sha256",
    "validate_independent_expected_leaf_bundle_verification_receipt",
    "validate_independent_expected_leaf_bundle_verification_result",
    "verify_independent_expected_leaf_bundle",
]
