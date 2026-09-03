"""Independent raw-byte verification for the development oracle boundary.

This module deliberately imports only the Python standard library.  It does
not import the publisher, runner, archive, ABI, source-policy, fixture, or
package projection implementations.  All schemas, framing rules, digest
rules, and archive checks used here are implemented locally from the frozen
Phase-D byte contracts.

The verifier accepts only raw immutable bytes.  It independently reconciles
the oracle registry, deterministic path-free source archive, selected-source
membership receipt, static-policy receipt, typed golden receipt, fixed V1
request/response frames, and the strongest-success development-runner
receipt.  It then checks the response's canonical configuration and compact
evidence commitment digests against the golden receipt.

The result is permanently nondecision.  In particular:

* caller-supplied custody is not authenticated;
* no approved case authority or execution-input-set membership artifact is
  supplied, so neither relationship is authenticated;
* the static policy receipt is parsed and byte-bound, but the Python source
  policy is not independently re-executed here;
* configuration and compact evidence payloads are strict ABI JSON and
  digest-bound, but their full semantic schemas are not authenticated;
* the development receipt's elapsed time, interpreter/cwd/argv/environment,
  and process observations are structurally checked but are not authenticated
  historical events;
* matching intended interpreter bytes does not attest which executable the
  kernel ran; and
* ABI V1 carries a compact evidence commitment, not a leaf-complete semantic
  bundle.

Constructing one of this module's dataclasses directly is not evidence.
Consumers at a raw-byte boundary must call
``verify_independent_oracle_bytes`` or the raw-input deep revalidator.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
import hashlib
import io
import json
import re
import stat
from types import MappingProxyType
from typing import NamedTuple, Tuple
import unicodedata
import zipfile


INDEPENDENT_ORACLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter."
    "development-independent-oracle-byte-verification-receipt.v1"
)
INDEPENDENT_ORACLE_VERIFICATION_RECEIPT_DIGEST_DOMAIN = (
    INDEPENDENT_ORACLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE
)
INDEPENDENT_ORACLE_VERIFICATION_INPUT_DIGEST_DOMAIN = (
    "heterodiff.adapter.development-independent-oracle-verification-input.v1"
)
INDEPENDENT_ORACLE_VERIFIER_ID = (
    "heterodiff-development-independent-oracle-byte-verifier-v1"
)
INDEPENDENT_ORACLE_VERIFIER_IMPLEMENTATION_STATUS = (
    "DEVELOPMENT_ONLY_STANDALONE_RAW_BYTE_VERIFIER"
)
INDEPENDENT_ORACLE_VERIFICATION_STATUS = (
    "INDEPENDENT_RAW_BYTE_BINDINGS_MATCHED_"
    "UNATTESTED_DEVELOPMENT_EXECUTION"
)
INDEPENDENT_ORACLE_VERIFIER_DECISION_STATUS = "NOT_MADE_BY_VERIFIER"
INDEPENDENT_ORACLE_SEMANTIC_SCOPE_ID = (
    "oracle-worker-abi-v1-compact-commitment-only"
)
INDEPENDENT_ORACLE_RUN_RECEIPT_SCOPE_ID = (
    "strongest-success-static-byte-bindings-matched-"
    "historical-observations-unattested"
)

GOLDEN_ORACLE_REGISTRY_ARTIFACT_TYPE = (
    "heterodiff.adapter.golden-oracle-registry.v1"
)
INDEPENDENT_GOLDEN_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.independent-golden-receipt.v1"
)
INDEPENDENT_GOLDEN_RECEIPT_DIGEST_DOMAIN = (
    INDEPENDENT_GOLDEN_RECEIPT_ARTIFACT_TYPE
)

SOURCE_ARCHIVE_INVENTORY_ARTIFACT_TYPE = (
    "heterodiff.adapter.source-archive-inventory.v1"
)
SOURCE_ARCHIVE_FORMAT_ID = "zip-stored-path-free-source-custody-v1"
SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.source-archive-membership-receipt.v1"
)
SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_DIGEST_DOMAIN = (
    SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE
)
SOURCE_ARCHIVE_ORACLE_ROLE_ID = "oracle-source"
SOURCE_ARCHIVE_ROLE_IDS = (
    "adapter-source",
    "contract-source",
    "execution-guard-source",
    SOURCE_ARCHIVE_ORACLE_ROLE_ID,
    "oracle-worker-source",
    "publisher-source",
    "support-source",
    "test-source",
    "verifier-source",
)

ORACLE_SOURCE_POLICY_ARTIFACT_TYPE = (
    "heterodiff.adapter.oracle-source-policy-receipt.v1"
)
ORACLE_SOURCE_POLICY_DIGEST_DOMAIN = ORACLE_SOURCE_POLICY_ARTIFACT_TYPE
ORACLE_SOURCE_POLICY_ID = "heterodiff-oracle-source-python-policy-v1"
ORACLE_SOURCE_PARSER_ID = "cpython-ast-feature-version-3.9-v1"
ORACLE_SOURCE_POLICY_STATUS = "pass"
ALLOWED_ORACLE_SOURCE_IMPORT_IDS = (
    "base64",
    "binascii",
    "hashlib",
    "json",
    "sys",
)

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

DESCRIPTOR_DIGEST_DOMAIN = "heterodiff.adapter.descriptor.v1"
SPLIT_MANIFEST_DIGEST_DOMAIN = "heterodiff.adapter.split-manifest.v1"
PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN = (
    "heterodiff.adapter.private-native-configuration.v1"
)
EXPECTED_EVIDENCE_DIGEST_DOMAIN = (
    "heterodiff.adapter.expected-evidence.v1"
)

DEVELOPMENT_ORACLE_RUN_RECEIPT_ARTIFACT_TYPE = (
    "heterodiff.adapter.development-archive-selected-oracle-run-receipt.v1"
)
DEVELOPMENT_ORACLE_RUN_RECEIPT_DIGEST_DOMAIN = (
    DEVELOPMENT_ORACLE_RUN_RECEIPT_ARTIFACT_TYPE
)
DEVELOPMENT_ORACLE_RUNNER_ID = (
    "heterodiff-development-archive-selected-oracle-runner-v1"
)
DEVELOPMENT_ORACLE_IMPLEMENTATION_STATUS = (
    "DEVELOPMENT_ONLY_ARCHIVE_SELECTED_ARGV_BOUND"
)
DEVELOPMENT_ORACLE_COMPLETED_STATUS = (
    "completed_response_identity_matched"
)
DEVELOPMENT_ORACLE_RESPONSE_MATCHED_STATUS = "matched"
DEVELOPMENT_ORACLE_OUTPUT_LIMIT_NONE = "none"
DEVELOPMENT_ORACLE_CONTAINMENT_STATUS_ID = "absent"
DEVELOPMENT_ORACLE_NOT_PROVIDED_ID = "not-provided"
DEVELOPMENT_ORACLE_SEMANTIC_STATUS_ID = "not-evaluated"
DEVELOPMENT_ORACLE_ARGV_MODE_ID = (
    "interpreter-isolated-no-site-no-bytecode-command-flags-v1"
)
DEVELOPMENT_ORACLE_SOURCE_LOAD_METHOD_ID = (
    "exact-archive-member-as-interpreter-command-argv-v1"
)
DEVELOPMENT_ORACLE_INTERPRETER_CAPTURE_METHOD_ID = (
    "retained-read-fd-pre-post-path-stat-not-exec-sealed-v1"
)
DEVELOPMENT_ORACLE_EXECUTION_BACKEND_ID = (
    "python-stdlib-posix-selector-subprocess-development-v1"
)
DEVELOPMENT_ORACLE_CWD_LAUNCH_METHOD_ID = (
    "path-cwd-pre-post-stat-unsealed-v1"
)
DEVELOPMENT_ORACLE_OUTPUT_CAPTURE_METHOD_ID = (
    "bounded-duplex-pipe-retained-prefix-sha256-v1"
)
DEVELOPMENT_ORACLE_PROCESS_CONTAINMENT_ID = (
    "posix-process-group-escapeable-v1"
)
DEVELOPMENT_ORACLE_PROCESS_CLEANUP_METHOD_ID = (
    "posix-process-group-term-kill-reap-observation-v1"
)
DEVELOPMENT_ORACLE_CLOCK_METHOD_ID = "system-monotonic-ns"

MAXIMUM_ORACLE_REGISTRY_BYTES = 4 * 1024 * 1024
MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES = 4 * 1024 * 1024
MAXIMUM_SOURCE_ARCHIVE_BYTES = 32 * 1024 * 1024
MAXIMUM_SOURCE_ARCHIVE_ENTRIES = 4096
MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES = 8 * 1024 * 1024
MAXIMUM_SOURCE_ARCHIVE_EXPANDED_BYTES = 32 * 1024 * 1024
MAXIMUM_SOURCE_ARCHIVE_RECEIPT_BYTES = 4 * 1024 * 1024
MAXIMUM_ORACLE_POLICY_RECEIPT_BYTES = 256 * 1024
MAXIMUM_INDEPENDENT_GOLDEN_RECEIPT_BYTES = 128 * 1024
MAXIMUM_ORACLE_WORKER_FRAME_BYTES = 32 * 1024 * 1024
MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES = 16 * 1024 * 1024
MAXIMUM_ORACLE_WORKER_SOURCE_BYTES = 64 * 1024
MAXIMUM_ORACLE_SOURCE_BYTES = 1024 * 1024
MAXIMUM_ORACLE_ID_BYTES = 128
MAXIMUM_ORACLE_WORKER_CASE_ORDINAL = 4095
MAXIMUM_ORACLE_ABI_JSON_DEPTH = 32
MAXIMUM_ORACLE_ABI_JSON_NODES = 200_000
MAXIMUM_ORACLE_ABI_JSON_STRING_BYTES = 512 * 1024
MAXIMUM_ORACLE_DEVELOPMENT_STDERR_BYTES = 64 * 1024
MAXIMUM_ORACLE_DEVELOPMENT_SOURCE_ARGV_BYTES = 64 * 1024
MAXIMUM_ORACLE_DEVELOPMENT_INTERPRETER_BYTES = 64 * 1024 * 1024
MAXIMUM_ORACLE_DEVELOPMENT_RECEIPT_BYTES = 64 * 1024
MAXIMUM_ORACLE_DEVELOPMENT_AGGREGATE_OUTPUT_BYTES = (
    MAXIMUM_ORACLE_WORKER_FRAME_BYTES + 32 * 1024
)
MAXIMUM_ORACLE_DEVELOPMENT_WALL_TIME_NANOSECONDS = 180 * 1_000_000_000
# Verifier-specific inclusive live-input budget.  It bounds concurrent
# retention of the eleven independently supplied values; crossing it is a
# verifier resource rejection, not a claim that each producer artifact is
# individually invalid.
MAXIMUM_INDEPENDENT_ORACLE_VERIFICATION_INPUT_BYTES = 128 * 1024 * 1024
MAXIMUM_VERIFICATION_RECEIPT_BYTES = 64 * 1024

MAXIMUM_JSON_DEPTH = MAXIMUM_ORACLE_ABI_JSON_DEPTH
MAXIMUM_JSON_NODES = MAXIMUM_ORACLE_ABI_JSON_NODES
MAXIMUM_JSON_STRING_BYTES = MAXIMUM_ORACLE_ABI_JSON_STRING_BYTES
MAXIMUM_POLICY_BANS = 1024
MAXIMUM_PRIVATE_ID_CODEPOINTS = 256
MAXIMUM_ADAPTER_SOURCE_BYTES = 32 * 1024 * 1024
MAXIMUM_ADAPTER_VERSION_DIGITS = 10
MAXIMUM_PUBLIC_TOKEN_BYTES = 128
# The approved conformance-case path applies this normative Phase-D ceiling
# before constructing a case.  Bare AdapterCapabilities projections outside
# that path are not inputs to this verifier.
MAXIMUM_APPROVED_CASE_REPRESENTATION_IDS = 64
MAXIMUM_SPLIT_ENTRIES = 4096
MAXIMUM_SPLIT_GROUPS = 128

_MAXIMUM_SAFE_INTEGER = (1 << 53) - 1
_EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
_FIXED_SOURCE_ARCHIVE_TIME = (1980, 1, 1, 0, 0, 0)
_FIXED_SOURCE_ARCHIVE_MODE = stat.S_IFREG | 0o444
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_PUBLIC_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_ADAPTER_ID_RE = _PUBLIC_ID_RE
_VERSION_RE = re.compile(r"^[1-9][0-9]{0,9}$")
_MEMBER_NAME_RE = re.compile(
    r"^objects/[0-9a-f]{64}-[0-9a-f]{16}-[0-9]{8}\.bin$"
)
_UNICODE_DATABASE = unicodedata.ucd_3_2_0

_VERIFICATION_INPUT_FIELD_NAMES = (
    b"oracle_registry_bytes",
    b"source_archive_inventory_bytes",
    b"source_archive_bytes",
    b"source_archive_membership_receipt_bytes",
    b"source_policy_receipt_bytes",
    b"independent_golden_receipt_bytes",
    b"request_frame_bytes",
    b"response_frame_bytes",
    b"stderr_bytes",
    b"interpreter_executable_bytes",
    b"development_runner_receipt_bytes",
)


class IndependentOracleVerificationCode(str, Enum):
    """Closed, interpolation-free independent-verifier failures."""

    INPUT_TYPE = "VER_ORACLE_INPUT_TYPE"
    INPUT_RESOURCE = "VER_ORACLE_INPUT_RESOURCE"
    REGISTRY_INVALID = "VER_ORACLE_REGISTRY_INVALID"
    ARCHIVE_INVALID = "VER_ORACLE_ARCHIVE_INVALID"
    MEMBERSHIP_INVALID = "VER_ORACLE_MEMBERSHIP_INVALID"
    POLICY_RECEIPT_INVALID = "VER_ORACLE_POLICY_RECEIPT_INVALID"
    GOLDEN_RECEIPT_INVALID = "VER_ORACLE_GOLDEN_RECEIPT_INVALID"
    REQUEST_INVALID = "VER_ORACLE_REQUEST_INVALID"
    RESPONSE_INVALID = "VER_ORACLE_RESPONSE_INVALID"
    RUN_RECEIPT_INVALID = "VER_ORACLE_RUN_RECEIPT_INVALID"
    BYTE_BINDING_MISMATCH = "VER_ORACLE_BYTE_BINDING_MISMATCH"
    PAYLOAD_MISMATCH = "VER_ORACLE_PAYLOAD_MISMATCH"
    RECEIPT_INVALID = "VER_ORACLE_VERIFICATION_RECEIPT_INVALID"
    CANONICALIZATION_FAILED = "VER_ORACLE_CANONICALIZATION_FAILED"
    INTERNAL_ERROR = "VER_ORACLE_INTERNAL_ERROR"


_ERROR_MESSAGES = MappingProxyType(
    {
        IndependentOracleVerificationCode.INPUT_TYPE: (
            "independent oracle verifier input has an invalid exact type"
        ),
        IndependentOracleVerificationCode.INPUT_RESOURCE: (
            "independent oracle verifier input exceeds a resource ceiling"
        ),
        IndependentOracleVerificationCode.REGISTRY_INVALID: (
            "independent oracle registry bytes are invalid"
        ),
        IndependentOracleVerificationCode.ARCHIVE_INVALID: (
            "independent source archive bytes are invalid"
        ),
        IndependentOracleVerificationCode.MEMBERSHIP_INVALID: (
            "independent source membership receipt is invalid"
        ),
        IndependentOracleVerificationCode.POLICY_RECEIPT_INVALID: (
            "independent source policy receipt is invalid"
        ),
        IndependentOracleVerificationCode.GOLDEN_RECEIPT_INVALID: (
            "independent golden receipt bytes are invalid"
        ),
        IndependentOracleVerificationCode.REQUEST_INVALID: (
            "independent oracle request frame is invalid"
        ),
        IndependentOracleVerificationCode.RESPONSE_INVALID: (
            "independent oracle response frame is invalid"
        ),
        IndependentOracleVerificationCode.RUN_RECEIPT_INVALID: (
            "independent development run receipt is invalid"
        ),
        IndependentOracleVerificationCode.BYTE_BINDING_MISMATCH: (
            "independent oracle raw-byte bindings differ"
        ),
        IndependentOracleVerificationCode.PAYLOAD_MISMATCH: (
            "independent oracle response commitments differ"
        ),
        IndependentOracleVerificationCode.RECEIPT_INVALID: (
            "independent oracle verification receipt is invalid"
        ),
        IndependentOracleVerificationCode.CANONICALIZATION_FAILED: (
            "independent oracle verification receipt cannot be canonicalized"
        ),
        IndependentOracleVerificationCode.INTERNAL_ERROR: (
            "independent oracle verification failed internally"
        ),
    }
)


class IndependentOracleVerificationError(ValueError):
    """One fixed coded failure without attacker-controlled text."""

    def __init__(self, code: IndependentOracleVerificationCode) -> None:
        if type(code) is not IndependentOracleVerificationCode:
            raise TypeError("independent oracle verifier code must be exact")
        super().__init__(_ERROR_MESSAGES[code])
        self.code = code.value


def _fail(code: IndependentOracleVerificationCode) -> None:
    raise IndependentOracleVerificationError(code) from None


class _Rejected(ValueError):
    pass


def _reject() -> None:
    raise _Rejected() from None


def _plain_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _domain_sha256(domain: str, payload: bytes) -> str:
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except UnicodeError:
        _reject()
    if (
        not domain_bytes
        or len(domain_bytes) > 256
        or b"\x00" in domain_bytes
        or type(payload) is not bytes
    ):
        _reject()
    digest = hashlib.sha256()
    digest.update(domain_bytes)
    digest.update(b"\x00")
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def _sequence_sha256(domain: str, values: Tuple[bytes, ...]) -> str:
    try:
        domain_bytes = domain.encode("ascii", "strict")
    except UnicodeError:
        _reject()
    if not domain_bytes or type(values) is not tuple:
        _reject()
    digest = hashlib.sha256()
    digest.update(len(domain_bytes).to_bytes(8, "big"))
    digest.update(domain_bytes)
    digest.update(len(values).to_bytes(8, "big"))
    for value in values:
        if type(value) is not bytes:
            _reject()
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    return digest.hexdigest()


def _named_sequence_sha256(
    domain: str,
    names: Tuple[bytes, ...],
    values: Tuple[bytes, ...],
) -> str:
    if len(names) != len(values):
        _reject()
    payloads = []
    for name, value in zip(names, values):
        if type(name) is not bytes or not name or type(value) is not bytes:
            _reject()
        payloads.extend((name, value))
    return _sequence_sha256(domain, tuple(payloads))


def _require_digest(value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _reject()
    return value


def _require_token(value: object, *, maximum: int = MAXIMUM_PUBLIC_TOKEN_BYTES) -> str:
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
    if type(value) is not str or _PUBLIC_ID_RE.fullmatch(value) is None:
        _reject()
    if len(value.encode("ascii", "strict")) > MAXIMUM_PUBLIC_TOKEN_BYTES:
        _reject()
    return value


def _require_adapter_identity(adapter_id: object, version: object) -> None:
    if (
        type(adapter_id) is not str
        or _ADAPTER_ID_RE.fullmatch(adapter_id) is None
        or len(adapter_id.encode("ascii", "strict"))
        > MAXIMUM_PUBLIC_TOKEN_BYTES
        or type(version) is not str
        or _VERSION_RE.fullmatch(version) is None
        or len(version) > MAXIMUM_ADAPTER_VERSION_DIGITS
    ):
        _reject()


def _require_integer(
    value: object,
    *,
    minimum: int = 0,
    maximum: int = _MAXIMUM_SAFE_INTEGER,
) -> int:
    if type(value) is not int or value < minimum or value > maximum:
        _reject()
    return value


def _require_bool(value: object) -> bool:
    if type(value) is not bool:
        _reject()
    return value


def _require_private_text(value: object) -> str:
    if type(value) is not str or not value:
        _reject()
    if len(value) > MAXIMUM_PRIVATE_ID_CODEPOINTS:
        _reject()
    if _UNICODE_DATABASE.normalize("NFC", value) != value:
        _reject()
    categories = tuple(_UNICODE_DATABASE.category(char) for char in value)
    if any(
        category in {"Cc", "Cs", "Co", "Cn", "Zl", "Zp"}
        for category in categories
    ):
        _reject()
    if categories[0] == "Zs" or categories[-1] == "Zs":
        _reject()
    return value


def _require_keys(value: object, expected: Tuple[str, ...]) -> dict:
    if type(value) is not dict:
        _reject()
    if tuple(sorted(value)) != tuple(sorted(expected)):
        _reject()
    return value


def _validate_json_tree(
    value: object,
    *,
    maximum_nodes: int,
    maximum_depth: int,
    maximum_string_bytes: int,
) -> None:
    nodes = 0
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > maximum_nodes or depth > maximum_depth:
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
            if len(encoded) > maximum_string_bytes:
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
                    key_bytes = key.encode("utf-8", "strict")
                except UnicodeError:
                    _reject()
                if len(key_bytes) > maximum_string_bytes:
                    _reject()
                stack.append((item, depth + 1))
            continue
        _reject()


def _canonical_json_bytes(value: object, *, maximum: int) -> bytes:
    _validate_json_tree(
        value,
        maximum_nodes=MAXIMUM_JSON_NODES,
        maximum_depth=MAXIMUM_JSON_DEPTH,
        maximum_string_bytes=MAXIMUM_JSON_STRING_BYTES,
    )
    try:
        result = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _reject()
    if not result or len(result) > maximum:
        _reject()
    return result


def _json_lexical_preflight(value: bytes, *, maximum: int) -> None:
    if type(value) is not bytes or not value or len(value) > maximum:
        _reject()
    if any(byte >= 0x80 for byte in value):
        _reject()
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
            if string_bytes > MAXIMUM_JSON_STRING_BYTES:
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
            tokens += 1
        elif byte in (0x7B, 0x5B):
            depth += 1
            tokens += 1
            if depth > MAXIMUM_JSON_DEPTH:
                _reject()
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0:
                _reject()
        elif byte in (0x2C, 0x3A):
            tokens += 1
        if tokens > MAXIMUM_JSON_NODES * 2:
            _reject()
    if in_string or escaped or depth != 0:
        _reject()


def _strict_json_bytes(value: bytes, *, maximum: int) -> object:
    _json_lexical_preflight(value, maximum=maximum)
    try:
        text = value.decode("ascii", "strict")
    except UnicodeError:
        _reject()

    def object_pairs(pairs):
        result = {}
        for key, item in pairs:
            if key in result:
                _reject()
            result[key] = item
        return result

    def parse_integer(token):
        digits = token[1:] if token.startswith("-") else token
        if not digits or len(digits) > 16:
            _reject()
        result = int(token, 10)
        if abs(result) > _MAXIMUM_SAFE_INTEGER:
            _reject()
        return result

    def reject_number(_token):
        _reject()

    try:
        tree = json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_int=parse_integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
        _validate_json_tree(
            tree,
            maximum_nodes=MAXIMUM_JSON_NODES,
            maximum_depth=MAXIMUM_JSON_DEPTH,
            maximum_string_bytes=MAXIMUM_JSON_STRING_BYTES,
        )
        canonical = _canonical_json_bytes(tree, maximum=maximum)
    except _Rejected:
        raise
    except (TypeError, ValueError, UnicodeError, RecursionError):
        _reject()
    if canonical != value:
        _reject()
    return tree


def _exact_bytes(
    value: object,
    *,
    maximum: int,
    allow_empty: bool = False,
) -> bytes:
    if type(value) is not bytes:
        raise TypeError("raw verifier fields must be exact bytes")
    if len(value) > maximum or (not allow_empty and not value):
        raise ValueError("raw verifier field exceeds its byte bound")
    return value


@dataclass(frozen=True)
class IndependentOracleVerificationInputV1:
    """Eleven exact raw inputs under one inclusive 128-MiB live-byte budget."""

    oracle_registry_bytes: bytes
    source_archive_inventory_bytes: bytes
    source_archive_bytes: bytes
    source_archive_membership_receipt_bytes: bytes
    source_policy_receipt_bytes: bytes
    independent_golden_receipt_bytes: bytes
    request_frame_bytes: bytes
    response_frame_bytes: bytes
    stderr_bytes: bytes
    interpreter_executable_bytes: bytes
    development_runner_receipt_bytes: bytes

    def __post_init__(self) -> None:
        if type(self) is not IndependentOracleVerificationInputV1:
            raise TypeError("independent verifier input must be exact")
        limits = (
            ("oracle_registry_bytes", MAXIMUM_ORACLE_REGISTRY_BYTES, False),
            (
                "source_archive_inventory_bytes",
                MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES,
                False,
            ),
            ("source_archive_bytes", MAXIMUM_SOURCE_ARCHIVE_BYTES, False),
            (
                "source_archive_membership_receipt_bytes",
                MAXIMUM_SOURCE_ARCHIVE_RECEIPT_BYTES,
                False,
            ),
            (
                "source_policy_receipt_bytes",
                MAXIMUM_ORACLE_POLICY_RECEIPT_BYTES,
                False,
            ),
            (
                "independent_golden_receipt_bytes",
                MAXIMUM_INDEPENDENT_GOLDEN_RECEIPT_BYTES,
                False,
            ),
            (
                "request_frame_bytes",
                MAXIMUM_ORACLE_WORKER_FRAME_BYTES,
                False,
            ),
            (
                "response_frame_bytes",
                MAXIMUM_ORACLE_WORKER_FRAME_BYTES,
                False,
            ),
            (
                "stderr_bytes",
                MAXIMUM_ORACLE_DEVELOPMENT_STDERR_BYTES,
                True,
            ),
            (
                "interpreter_executable_bytes",
                MAXIMUM_ORACLE_DEVELOPMENT_INTERPRETER_BYTES,
                False,
            ),
            (
                "development_runner_receipt_bytes",
                MAXIMUM_ORACLE_DEVELOPMENT_RECEIPT_BYTES,
                False,
            ),
        )
        for name, maximum, allow_empty in limits:
            _exact_bytes(
                getattr(self, name),
                maximum=maximum,
                allow_empty=allow_empty,
            )
        if (
            sum(len(getattr(self, name)) for name, _maximum, _empty in limits)
            > MAXIMUM_INDEPENDENT_ORACLE_VERIFICATION_INPUT_BYTES
        ):
            raise ValueError("raw verifier input aggregate exceeds its bound")
        if (
            len(self.response_frame_bytes) + len(self.stderr_bytes)
            > MAXIMUM_ORACLE_DEVELOPMENT_AGGREGATE_OUTPUT_BYTES
        ):
            raise ValueError("raw verifier output aggregate exceeds its bound")


def _snapshot_input(
    value: object,
) -> IndependentOracleVerificationInputV1:
    if type(value) is not IndependentOracleVerificationInputV1:
        _fail(IndependentOracleVerificationCode.INPUT_TYPE)
    try:
        IndependentOracleVerificationInputV1.__post_init__(value)
        return IndependentOracleVerificationInputV1(
            **{
                item.name: getattr(value, item.name)
                for item in fields(IndependentOracleVerificationInputV1)
            }
        )
    except IndependentOracleVerificationError:
        raise
    except (AttributeError, TypeError):
        _fail(IndependentOracleVerificationCode.INPUT_TYPE)
    except ValueError:
        _fail(IndependentOracleVerificationCode.INPUT_RESOURCE)


class _RegistryEntry(NamedTuple):
    oracle_id: str
    oracle_source_byte_count: int
    oracle_source_sha256: str
    forbidden_import_ids: Tuple[str, ...]
    forbidden_name_ids: Tuple[str, ...]


_REGISTRY_KEYS = ("artifact_type", "format_version", "oracles")
_REGISTRY_ENTRY_KEYS = (
    "forbidden_import_ids",
    "forbidden_name_ids",
    "oracle_id",
    "oracle_source_byte_count",
    "oracle_source_sha256",
)


def _sorted_token_list(
    value: object,
    *,
    allow_empty: bool,
    maximum_count: int,
) -> Tuple[str, ...]:
    if type(value) is not list:
        _reject()
    if (not allow_empty and not value) or len(value) > maximum_count:
        _reject()
    result = tuple(_require_token(item) for item in value)
    if result != tuple(sorted(set(result))):
        _reject()
    return result


def _parse_registry(value: bytes) -> Tuple[_RegistryEntry, ...]:
    tree = _require_keys(
        _strict_json_bytes(value, maximum=MAXIMUM_ORACLE_REGISTRY_BYTES),
        _REGISTRY_KEYS,
    )
    if (
        tree["artifact_type"] != GOLDEN_ORACLE_REGISTRY_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or type(tree["oracles"]) is not list
        or not tree["oracles"]
        or len(tree["oracles"]) > MAXIMUM_SOURCE_ARCHIVE_ENTRIES
    ):
        _reject()
    entries = []
    for raw_entry in tree["oracles"]:
        entry = _require_keys(raw_entry, _REGISTRY_ENTRY_KEYS)
        entries.append(
            _RegistryEntry(
                oracle_id=_require_token(entry["oracle_id"]),
                oracle_source_byte_count=_require_integer(
                    entry["oracle_source_byte_count"],
                    minimum=1,
                    maximum=MAXIMUM_ORACLE_SOURCE_BYTES,
                ),
                oracle_source_sha256=_require_digest(
                    entry["oracle_source_sha256"]
                ),
                forbidden_import_ids=_sorted_token_list(
                    entry["forbidden_import_ids"],
                    allow_empty=False,
                    maximum_count=MAXIMUM_POLICY_BANS,
                ),
                forbidden_name_ids=_sorted_token_list(
                    entry["forbidden_name_ids"],
                    allow_empty=False,
                    maximum_count=MAXIMUM_POLICY_BANS,
                ),
            )
        )
    result = tuple(entries)
    oracle_ids = tuple(item.oracle_id for item in result)
    if oracle_ids != tuple(sorted(set(oracle_ids))):
        _reject()
    return result


class _InventoryMember(NamedTuple):
    content_byte_count: int
    content_sha256: str
    occurrence_count: int


class _SourceObject(NamedTuple):
    role_id: str
    source_byte_count: int
    source_object_id: str
    source_sha256: str


class _Inventory(NamedTuple):
    archive_byte_count: int
    archive_sha256: str
    members: Tuple[_InventoryMember, ...]
    source_objects: Tuple[_SourceObject, ...]


class _ArchiveMaterial(NamedTuple):
    inventory: _Inventory
    member_contents: Tuple[bytes, ...]


_INVENTORY_KEYS = (
    "archive_byte_count",
    "archive_format_id",
    "archive_sha256",
    "artifact_type",
    "format_version",
    "members",
    "source_objects",
)
_INVENTORY_MEMBER_KEYS = (
    "content_byte_count",
    "content_sha256",
    "occurrence_count",
)
_SOURCE_OBJECT_KEYS = (
    "role_id",
    "source_byte_count",
    "source_object_id",
    "source_sha256",
)


def _parse_inventory(value: bytes) -> _Inventory:
    tree = _require_keys(
        _strict_json_bytes(
            value,
            maximum=MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES,
        ),
        _INVENTORY_KEYS,
    )
    if (
        tree["archive_format_id"] != SOURCE_ARCHIVE_FORMAT_ID
        or tree["artifact_type"] != SOURCE_ARCHIVE_INVENTORY_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or type(tree["members"]) is not list
        or not tree["members"]
        or type(tree["source_objects"]) is not list
        or not tree["source_objects"]
        or len(tree["members"]) > MAXIMUM_SOURCE_ARCHIVE_ENTRIES
        or len(tree["source_objects"]) > MAXIMUM_SOURCE_ARCHIVE_ENTRIES
    ):
        _reject()
    members = []
    for raw_member in tree["members"]:
        member = _require_keys(raw_member, _INVENTORY_MEMBER_KEYS)
        members.append(
            _InventoryMember(
                content_byte_count=_require_integer(
                    member["content_byte_count"],
                    maximum=MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES,
                ),
                content_sha256=_require_digest(member["content_sha256"]),
                occurrence_count=_require_integer(
                    member["occurrence_count"],
                    minimum=1,
                    maximum=MAXIMUM_SOURCE_ARCHIVE_ENTRIES,
                ),
            )
        )
    member_tuple = tuple(members)
    member_keys = tuple(
        (item.content_sha256, item.content_byte_count)
        for item in member_tuple
    )
    if member_keys != tuple(sorted(set(member_keys))):
        _reject()
    if (
        sum(item.occurrence_count for item in member_tuple)
        > MAXIMUM_SOURCE_ARCHIVE_ENTRIES
    ):
        _reject()
    if (
        sum(
            item.content_byte_count * item.occurrence_count
            for item in member_tuple
        )
        > MAXIMUM_SOURCE_ARCHIVE_EXPANDED_BYTES
    ):
        _reject()

    objects = []
    for raw_object in tree["source_objects"]:
        source_object = _require_keys(raw_object, _SOURCE_OBJECT_KEYS)
        role = source_object["role_id"]
        if type(role) is not str or role not in SOURCE_ARCHIVE_ROLE_IDS:
            _reject()
        objects.append(
            _SourceObject(
                role_id=role,
                source_byte_count=_require_integer(
                    source_object["source_byte_count"],
                    maximum=MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES,
                ),
                source_object_id=_require_token(
                    source_object["source_object_id"]
                ),
                source_sha256=_require_digest(
                    source_object["source_sha256"]
                ),
            )
        )
    object_tuple = tuple(objects)
    object_keys = tuple(
        (item.role_id, item.source_object_id) for item in object_tuple
    )
    if object_keys != tuple(sorted(set(object_keys))):
        _reject()
    member_identity_set = set(member_keys)
    if any(
        (item.source_sha256, item.source_byte_count)
        not in member_identity_set
        for item in object_tuple
    ):
        _reject()
    oracle_digests = {
        item.source_sha256
        for item in object_tuple
        if item.role_id == SOURCE_ARCHIVE_ORACLE_ROLE_ID
    }
    other_digests = {
        item.source_sha256
        for item in object_tuple
        if item.role_id != SOURCE_ARCHIVE_ORACLE_ROLE_ID
    }
    if oracle_digests.intersection(other_digests):
        _reject()
    return _Inventory(
        archive_byte_count=_require_integer(
            tree["archive_byte_count"],
            minimum=1,
            maximum=MAXIMUM_SOURCE_ARCHIVE_BYTES,
        ),
        archive_sha256=_require_digest(tree["archive_sha256"]),
        members=member_tuple,
        source_objects=object_tuple,
    )


def _archive_member_name(
    digest: str,
    byte_count: int,
    ordinal: int,
) -> str:
    return "objects/{}-{:016x}-{:08d}.bin".format(
        digest,
        byte_count,
        ordinal,
    )


def _canonical_zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, _FIXED_SOURCE_ARCHIVE_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.create_version = 20
    info.extract_version = 20
    info.external_attr = _FIXED_SOURCE_ARCHIVE_MODE << 16
    info.internal_attr = 0
    info.flag_bits = 0
    info.extra = b""
    info.comment = b""
    info.volume = 0
    return info


def _build_deterministic_archive(contents: Tuple[bytes, ...]) -> bytes:
    ordered = tuple(
        sorted(
            contents,
            key=lambda raw: (_plain_sha256(raw), len(raw), raw),
        )
    )
    occurrences = {}
    output = io.BytesIO()
    try:
        with zipfile.ZipFile(
            output,
            mode="w",
            compression=zipfile.ZIP_STORED,
            allowZip64=False,
        ) as archive:
            archive.comment = b""
            for raw in ordered:
                identity = (_plain_sha256(raw), len(raw))
                ordinal = occurrences.get(identity, 0)
                occurrences[identity] = ordinal + 1
                archive.writestr(
                    _canonical_zip_info(
                        _archive_member_name(
                            identity[0],
                            identity[1],
                            ordinal,
                        )
                    ),
                    raw,
                )
    except (
        OSError,
        RuntimeError,
        ValueError,
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
    ):
        _reject()
    result = output.getvalue()
    if not result or len(result) > MAXIMUM_SOURCE_ARCHIVE_BYTES:
        _reject()
    return result


def _preflight_zip(value: bytes) -> None:
    if len(value) < 22:
        _reject()
    end_record = value[-22:]
    if end_record[:4] != b"PK\x05\x06":
        _reject()
    disk_number = int.from_bytes(end_record[4:6], "little")
    central_disk = int.from_bytes(end_record[6:8], "little")
    entries_on_disk = int.from_bytes(end_record[8:10], "little")
    entry_count = int.from_bytes(end_record[10:12], "little")
    central_size = int.from_bytes(end_record[12:16], "little")
    central_offset = int.from_bytes(end_record[16:20], "little")
    comment_size = int.from_bytes(end_record[20:22], "little")
    if (
        disk_number != 0
        or central_disk != 0
        or entries_on_disk != entry_count
        or entry_count == 0
        or entry_count > MAXIMUM_SOURCE_ARCHIVE_ENTRIES
        or central_size == 0
        or comment_size != 0
        or central_offset + central_size != len(value) - 22
    ):
        _reject()
    position = central_offset
    central_end = central_offset + central_size
    observed = 0
    expanded = 0
    while position < central_end:
        if (
            central_end - position < 46
            or value[position : position + 4] != b"PK\x01\x02"
        ):
            _reject()
        header = value[position : position + 46]
        version_made_by = int.from_bytes(header[4:6], "little")
        version_needed = int.from_bytes(header[6:8], "little")
        flag_bits = int.from_bytes(header[8:10], "little")
        compression = int.from_bytes(header[10:12], "little")
        modified_time = int.from_bytes(header[12:14], "little")
        modified_date = int.from_bytes(header[14:16], "little")
        compressed_size = int.from_bytes(header[20:24], "little")
        uncompressed_size = int.from_bytes(header[24:28], "little")
        name_size = int.from_bytes(header[28:30], "little")
        extra_size = int.from_bytes(header[30:32], "little")
        member_comment_size = int.from_bytes(header[32:34], "little")
        member_disk = int.from_bytes(header[34:36], "little")
        internal_attr = int.from_bytes(header[36:38], "little")
        external_attr = int.from_bytes(header[38:42], "little")
        local_offset = int.from_bytes(header[42:46], "little")
        record_size = 46 + name_size + extra_size + member_comment_size
        if (
            record_size > central_end - position
            or version_made_by != ((3 << 8) | 20)
            or version_needed != 20
            or flag_bits != 0
            or compression != 0
            or modified_time != 0
            or modified_date != 0x21
            or compressed_size != uncompressed_size
            or uncompressed_size > MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES
            or name_size == 0
            or name_size > 128
            or extra_size != 0
            or member_comment_size != 0
            or member_disk != 0
            or internal_attr != 0
            or external_attr != (_FIXED_SOURCE_ARCHIVE_MODE << 16)
            or local_offset >= central_offset
        ):
            _reject()
        name_start = position + 46
        try:
            name = value[
                name_start : name_start + name_size
            ].decode("ascii", "strict")
        except UnicodeError:
            _reject()
        if _MEMBER_NAME_RE.fullmatch(name) is None:
            _reject()
        observed += 1
        expanded += uncompressed_size
        if (
            observed > MAXIMUM_SOURCE_ARCHIVE_ENTRIES
            or expanded > MAXIMUM_SOURCE_ARCHIVE_EXPANDED_BYTES
        ):
            _reject()
        position += record_size
    if position != central_end or observed != entry_count:
        _reject()


def _read_archive_contents(value: bytes) -> Tuple[bytes, ...]:
    _preflight_zip(value)
    try:
        with zipfile.ZipFile(io.BytesIO(value), mode="r") as archive:
            if archive.comment != b"":
                _reject()
            infos = archive.infolist()
            if (
                not infos
                or len(infos) > MAXIMUM_SOURCE_ARCHIVE_ENTRIES
            ):
                _reject()
            names = tuple(info.filename for info in infos)
            if names != tuple(sorted(set(names))):
                _reject()
            expanded = 0
            for info in infos:
                try:
                    name_bytes = info.filename.encode("ascii", "strict")
                except UnicodeError:
                    _reject()
                if (
                    not name_bytes
                    or len(name_bytes) > 128
                    or _MEMBER_NAME_RE.fullmatch(info.filename) is None
                    or info.orig_filename != info.filename
                    or info.date_time != _FIXED_SOURCE_ARCHIVE_TIME
                    or info.compress_type != zipfile.ZIP_STORED
                    or info.create_system != 3
                    or info.create_version != 20
                    or info.extract_version != 20
                    or info.external_attr
                    != (_FIXED_SOURCE_ARCHIVE_MODE << 16)
                    or info.internal_attr != 0
                    or info.flag_bits != 0
                    or info.extra != b""
                    or info.comment != b""
                    or info.volume != 0
                    or info.is_dir()
                    or info.file_size != info.compress_size
                    or info.file_size > MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES
                ):
                    _reject()
                expanded += info.file_size
                if expanded > MAXIMUM_SOURCE_ARCHIVE_EXPANDED_BYTES:
                    _reject()
            contents = []
            for info in infos:
                with archive.open(info, mode="r") as member:
                    raw = member.read(info.file_size + 1)
                    trailing = member.read(1)
                if (
                    len(raw) != info.file_size
                    or trailing != b""
                    or _plain_sha256(raw) not in info.filename
                ):
                    _reject()
                contents.append(raw)
    except _Rejected:
        raise
    except (
        EOFError,
        OSError,
        RuntimeError,
        ValueError,
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
    ):
        _reject()
    ordered = tuple(
        sorted(
            contents,
            key=lambda raw: (_plain_sha256(raw), len(raw), raw),
        )
    )
    occurrences = {}
    expected_names = []
    for raw in ordered:
        identity = (_plain_sha256(raw), len(raw))
        ordinal = occurrences.get(identity, 0)
        occurrences[identity] = ordinal + 1
        expected_names.append(
            _archive_member_name(identity[0], identity[1], ordinal)
        )
    if tuple(expected_names) != names:
        _reject()
    if _build_deterministic_archive(tuple(contents)) != value:
        _reject()
    return ordered


def _validate_archive(
    inventory_bytes: bytes,
    archive_bytes: bytes,
) -> _ArchiveMaterial:
    inventory = _parse_inventory(inventory_bytes)
    if (
        inventory.archive_byte_count != len(archive_bytes)
        or inventory.archive_sha256 != _plain_sha256(archive_bytes)
    ):
        _reject()
    contents = _read_archive_contents(archive_bytes)
    counts = {}
    for raw in contents:
        identity = (_plain_sha256(raw), len(raw))
        counts[identity] = counts.get(identity, 0) + 1
    observed_members = tuple(
        _InventoryMember(
            content_byte_count=byte_count,
            content_sha256=digest,
            occurrence_count=counts[(digest, byte_count)],
        )
        for digest, byte_count in sorted(counts)
    )
    if observed_members != inventory.members:
        _reject()
    return _ArchiveMaterial(inventory=inventory, member_contents=contents)


_MEMBERSHIP_KEYS = (
    "archive_sha256",
    "artifact_type",
    "format_version",
    "inventory_sha256",
    "role_id",
    "source_byte_count",
    "source_object_id",
    "source_sha256",
)


class _Membership(NamedTuple):
    archive_sha256: str
    inventory_sha256: str
    role_id: str
    source_byte_count: int
    source_object_id: str
    source_sha256: str


def _parse_membership(value: bytes) -> _Membership:
    tree = _require_keys(
        _strict_json_bytes(
            value,
            maximum=MAXIMUM_SOURCE_ARCHIVE_RECEIPT_BYTES,
        ),
        _MEMBERSHIP_KEYS,
    )
    if (
        tree["artifact_type"]
        != SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_ARTIFACT_TYPE
        or tree["format_version"] != "1"
        or tree["role_id"] != SOURCE_ARCHIVE_ORACLE_ROLE_ID
    ):
        _reject()
    return _Membership(
        archive_sha256=_require_digest(tree["archive_sha256"]),
        inventory_sha256=_require_digest(tree["inventory_sha256"]),
        role_id=tree["role_id"],
        source_byte_count=_require_integer(
            tree["source_byte_count"],
            maximum=MAXIMUM_SOURCE_ARCHIVE_MEMBER_BYTES,
        ),
        source_object_id=_require_token(tree["source_object_id"]),
        source_sha256=_require_digest(tree["source_sha256"]),
    )


_POLICY_RECEIPT_KEYS = (
    "allowed_import_ids",
    "artifact_type",
    "decision_eligible",
    "forbidden_import_ids",
    "forbidden_name_ids",
    "format_version",
    "oracle_id",
    "oracle_source_byte_count",
    "oracle_source_sha256",
    "parser_id",
    "policy_id",
    "status_id",
)


class _PolicyReceipt(NamedTuple):
    oracle_id: str
    oracle_source_byte_count: int
    oracle_source_sha256: str
    forbidden_import_ids: Tuple[str, ...]
    forbidden_name_ids: Tuple[str, ...]


def _parse_policy_receipt(value: bytes) -> _PolicyReceipt:
    tree = _require_keys(
        _strict_json_bytes(
            value,
            maximum=MAXIMUM_ORACLE_POLICY_RECEIPT_BYTES,
        ),
        _POLICY_RECEIPT_KEYS,
    )
    if (
        tree["artifact_type"] != ORACLE_SOURCE_POLICY_ARTIFACT_TYPE
        or tree["decision_eligible"] is not False
        or tree["format_version"] != "1"
        or tree["parser_id"] != ORACLE_SOURCE_PARSER_ID
        or tree["policy_id"] != ORACLE_SOURCE_POLICY_ID
        or tree["status_id"] != ORACLE_SOURCE_POLICY_STATUS
        or type(tree["allowed_import_ids"]) is not list
        or tuple(tree["allowed_import_ids"])
        != ALLOWED_ORACLE_SOURCE_IMPORT_IDS
    ):
        _reject()
    for item in tree["allowed_import_ids"]:
        _require_token(item)
    return _PolicyReceipt(
        oracle_id=_require_token(tree["oracle_id"]),
        oracle_source_byte_count=_require_integer(
            tree["oracle_source_byte_count"],
            minimum=1,
            maximum=MAXIMUM_ORACLE_SOURCE_BYTES,
        ),
        oracle_source_sha256=_require_digest(
            tree["oracle_source_sha256"]
        ),
        forbidden_import_ids=_sorted_token_list(
            tree["forbidden_import_ids"],
            allow_empty=False,
            maximum_count=MAXIMUM_POLICY_BANS,
        ),
        forbidden_name_ids=_sorted_token_list(
            tree["forbidden_name_ids"],
            allow_empty=False,
            maximum_count=MAXIMUM_POLICY_BANS,
        ),
    )


_GOLDEN_RECEIPT_KEYS = (
    "adapter_id",
    "adapter_version",
    "artifact_type",
    "descriptor_sha256",
    "expected_configuration_payload_byte_count",
    "expected_configuration_sha256",
    "expected_evidence_sha256",
    "expected_native_observation_sha256",
    "format_version",
    "oracle_id",
    "oracle_registry_sha256",
    "oracle_source_byte_count",
    "oracle_source_sha256",
    "source_byte_count",
    "source_sha256",
    "split_manifest_sha256",
)


class _GoldenReceipt(NamedTuple):
    adapter_id: str
    adapter_version: str
    descriptor_sha256: str
    expected_configuration_payload_byte_count: int
    expected_configuration_sha256: str
    expected_evidence_sha256: str
    expected_native_observation_sha256: str
    oracle_id: str
    oracle_registry_sha256: str
    oracle_source_byte_count: int
    oracle_source_sha256: str
    source_byte_count: int
    source_sha256: str
    split_manifest_sha256: str


def _parse_golden_receipt(value: bytes) -> _GoldenReceipt:
    tree = _require_keys(
        _strict_json_bytes(
            value,
            maximum=MAXIMUM_INDEPENDENT_GOLDEN_RECEIPT_BYTES,
        ),
        _GOLDEN_RECEIPT_KEYS,
    )
    if (
        tree["artifact_type"] != INDEPENDENT_GOLDEN_RECEIPT_ARTIFACT_TYPE
        or tree["format_version"] != "1"
    ):
        _reject()
    _require_adapter_identity(
        tree["adapter_id"],
        tree["adapter_version"],
    )
    return _GoldenReceipt(
        adapter_id=tree["adapter_id"],
        adapter_version=tree["adapter_version"],
        descriptor_sha256=_require_digest(tree["descriptor_sha256"]),
        expected_configuration_payload_byte_count=_require_integer(
            tree["expected_configuration_payload_byte_count"],
            minimum=1,
            maximum=MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
        ),
        expected_configuration_sha256=_require_digest(
            tree["expected_configuration_sha256"]
        ),
        expected_evidence_sha256=_require_digest(
            tree["expected_evidence_sha256"]
        ),
        expected_native_observation_sha256=_require_digest(
            tree["expected_native_observation_sha256"]
        ),
        oracle_id=_require_token(tree["oracle_id"]),
        oracle_registry_sha256=_require_digest(
            tree["oracle_registry_sha256"]
        ),
        oracle_source_byte_count=_require_integer(
            tree["oracle_source_byte_count"],
            minimum=1,
            maximum=MAXIMUM_ORACLE_SOURCE_BYTES,
        ),
        oracle_source_sha256=_require_digest(
            tree["oracle_source_sha256"]
        ),
        source_byte_count=_require_integer(
            tree["source_byte_count"],
            minimum=1,
            maximum=MAXIMUM_ADAPTER_SOURCE_BYTES,
        ),
        source_sha256=_require_digest(tree["source_sha256"]),
        split_manifest_sha256=_require_digest(
            tree["split_manifest_sha256"]
        ),
    )


class _Request(NamedTuple):
    execution_input_set_sha256: str
    case_ordinal: int
    oracle_id: str
    oracle_source_byte_count: int
    oracle_source_sha256: str
    source_bytes: bytes
    descriptor_payload_bytes: bytes
    partition_payload_bytes: bytes
    split_manifest_payload_bytes: bytes


class _Response(NamedTuple):
    request_frame_sha256: str
    case_ordinal: int
    oracle_id: str
    oracle_source_byte_count: int
    oracle_source_sha256: str
    expected_configuration_payload_bytes: bytes
    expected_evidence_payload_bytes: bytes
    expected_native_observation_sha256: str


def _read_u64(value: bytes, offset: int) -> Tuple[int, int]:
    end = offset + 8
    if offset < 0 or end > len(value):
        _reject()
    return int.from_bytes(value[offset:end], "big"), end


def _parse_frame(
    value: bytes,
    *,
    domain: bytes,
    field_names: Tuple[bytes, ...],
) -> Tuple[bytes, ...]:
    if (
        type(value) is not bytes
        or not value
        or len(value) > MAXIMUM_ORACLE_WORKER_FRAME_BYTES
    ):
        _reject()
    domain_end = len(domain)
    if (
        len(value) < domain_end + 1
        or value[:domain_end] != domain
        or value[domain_end] != 0
    ):
        _reject()
    offset = domain_end + 1
    field_count, offset = _read_u64(value, offset)
    if field_count != len(field_names):
        _reject()
    values = []
    for expected_name in field_names:
        name_length, offset = _read_u64(value, offset)
        if name_length > len(value) - offset:
            _reject()
        name_end = offset + name_length
        if value[offset:name_end] != expected_name:
            _reject()
        offset = name_end
        item_length, offset = _read_u64(value, offset)
        if item_length > len(value) - offset:
            _reject()
        item_end = offset + item_length
        values.append(value[offset:item_end])
        offset = item_end
    if offset != len(value):
        _reject()
    return tuple(values)


def _build_frame(
    domain: bytes,
    names: Tuple[bytes, ...],
    values: Tuple[bytes, ...],
) -> bytes:
    if len(names) != len(values):
        _reject()
    parts = [domain, b"\x00", len(names).to_bytes(8, "big")]
    for name, value in zip(names, values):
        parts.extend(
            (
                len(name).to_bytes(8, "big"),
                name,
                len(value).to_bytes(8, "big"),
                value,
            )
        )
    result = b"".join(parts)
    if not result or len(result) > MAXIMUM_ORACLE_WORKER_FRAME_BYTES:
        _reject()
    return result


def _decode_ascii(value: bytes) -> str:
    try:
        return value.decode("ascii", "strict")
    except UnicodeError:
        _reject()


def _decode_fixed_u64(value: bytes) -> int:
    if len(value) != 8:
        _reject()
    return int.from_bytes(value, "big")


def _strict_structured_payload(value: bytes) -> object:
    if (
        type(value) is not bytes
        or not value
        or len(value) > MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES
    ):
        _reject()
    return _strict_json_bytes(
        value,
        maximum=MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
    )


def _parse_request(value: bytes) -> _Request:
    fields_raw = _parse_frame(
        value,
        domain=ORACLE_WORKER_REQUEST_DOMAIN_BYTES,
        field_names=ORACLE_WORKER_REQUEST_FIELD_NAMES,
    )
    execution_sha256 = _require_digest(_decode_ascii(fields_raw[0]))
    case_ordinal = _decode_fixed_u64(fields_raw[1])
    _require_integer(
        case_ordinal,
        maximum=MAXIMUM_ORACLE_WORKER_CASE_ORDINAL,
    )
    oracle_id = _require_token(
        _decode_ascii(fields_raw[2]),
        maximum=MAXIMUM_ORACLE_ID_BYTES,
    )
    oracle_source_byte_count = _decode_fixed_u64(fields_raw[3])
    _require_integer(
        oracle_source_byte_count,
        minimum=1,
        maximum=MAXIMUM_ORACLE_SOURCE_BYTES,
    )
    oracle_source_sha256 = _require_digest(
        _decode_ascii(fields_raw[4])
    )
    source_bytes = fields_raw[5]
    if (
        not source_bytes
        or len(source_bytes) > MAXIMUM_ORACLE_WORKER_SOURCE_BYTES
    ):
        _reject()
    descriptor_payload_bytes = fields_raw[6]
    partition_payload_bytes = fields_raw[7]
    split_manifest_payload_bytes = fields_raw[8]
    _strict_structured_payload(descriptor_payload_bytes)
    _strict_structured_payload(partition_payload_bytes)
    _strict_structured_payload(split_manifest_payload_bytes)
    rebuilt = _build_frame(
        ORACLE_WORKER_REQUEST_DOMAIN_BYTES,
        ORACLE_WORKER_REQUEST_FIELD_NAMES,
        (
            execution_sha256.encode("ascii"),
            case_ordinal.to_bytes(8, "big"),
            oracle_id.encode("ascii"),
            oracle_source_byte_count.to_bytes(8, "big"),
            oracle_source_sha256.encode("ascii"),
            source_bytes,
            descriptor_payload_bytes,
            partition_payload_bytes,
            split_manifest_payload_bytes,
        ),
    )
    if rebuilt != value:
        _reject()
    return _Request(
        execution_input_set_sha256=execution_sha256,
        case_ordinal=case_ordinal,
        oracle_id=oracle_id,
        oracle_source_byte_count=oracle_source_byte_count,
        oracle_source_sha256=oracle_source_sha256,
        source_bytes=source_bytes,
        descriptor_payload_bytes=descriptor_payload_bytes,
        partition_payload_bytes=partition_payload_bytes,
        split_manifest_payload_bytes=split_manifest_payload_bytes,
    )


def _parse_response(value: bytes) -> _Response:
    fields_raw = _parse_frame(
        value,
        domain=ORACLE_WORKER_RESPONSE_DOMAIN_BYTES,
        field_names=ORACLE_WORKER_RESPONSE_FIELD_NAMES,
    )
    request_sha256 = _require_digest(_decode_ascii(fields_raw[0]))
    case_ordinal = _decode_fixed_u64(fields_raw[1])
    _require_integer(
        case_ordinal,
        maximum=MAXIMUM_ORACLE_WORKER_CASE_ORDINAL,
    )
    oracle_id = _require_token(
        _decode_ascii(fields_raw[2]),
        maximum=MAXIMUM_ORACLE_ID_BYTES,
    )
    oracle_source_byte_count = _decode_fixed_u64(fields_raw[3])
    _require_integer(
        oracle_source_byte_count,
        minimum=1,
        maximum=MAXIMUM_ORACLE_SOURCE_BYTES,
    )
    oracle_source_sha256 = _require_digest(
        _decode_ascii(fields_raw[4])
    )
    configuration_bytes = fields_raw[5]
    evidence_bytes = fields_raw[6]
    _strict_structured_payload(configuration_bytes)
    _strict_structured_payload(evidence_bytes)
    native_sha256 = _require_digest(_decode_ascii(fields_raw[7]))
    rebuilt = _build_frame(
        ORACLE_WORKER_RESPONSE_DOMAIN_BYTES,
        ORACLE_WORKER_RESPONSE_FIELD_NAMES,
        (
            request_sha256.encode("ascii"),
            case_ordinal.to_bytes(8, "big"),
            oracle_id.encode("ascii"),
            oracle_source_byte_count.to_bytes(8, "big"),
            oracle_source_sha256.encode("ascii"),
            configuration_bytes,
            evidence_bytes,
            native_sha256.encode("ascii"),
        ),
    )
    if rebuilt != value:
        _reject()
    return _Response(
        request_frame_sha256=request_sha256,
        case_ordinal=case_ordinal,
        oracle_id=oracle_id,
        oracle_source_byte_count=oracle_source_byte_count,
        oracle_source_sha256=oracle_source_sha256,
        expected_configuration_payload_bytes=configuration_bytes,
        expected_evidence_payload_bytes=evidence_bytes,
        expected_native_observation_sha256=native_sha256,
    )


_DESCRIPTOR_KEYS = ("capabilities", "identity", "unicode_profile")
_DESCRIPTOR_IDENTITY_KEYS = (
    "adapter_id",
    "adapter_version",
    "contract_version",
    "policy_sha256",
)
_DESCRIPTOR_CAPABILITY_KEYS = (
    "evaluation_labels",
    "fitted_state",
    "multiplicity_mode",
    "private_provenance",
    "raw_byte_reconstruction",
    "semantic_reconstruction",
    "static_context",
    "supported_representation_ids",
    "time_measure",
)
_PARTITION_KEYS = ("group_id", "sample_id", "split", "unicode_profile")
_SPLIT_MANIFEST_KEYS = ("entries", "unicode_profile")
_SPLIT_ENTRY_KEYS = ("group_id", "sample_id", "split")


def _validate_descriptor(
    value: bytes,
    golden: _GoldenReceipt,
) -> None:
    tree = _require_keys(
        _strict_json_bytes(
            value,
            maximum=MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
        ),
        _DESCRIPTOR_KEYS,
    )
    if tree["unicode_profile"] != "ucd-3.2.0":
        _reject()
    identity = _require_keys(tree["identity"], _DESCRIPTOR_IDENTITY_KEYS)
    _require_adapter_identity(
        identity["adapter_id"],
        identity["adapter_version"],
    )
    if (
        identity["adapter_id"] != golden.adapter_id
        or identity["adapter_version"] != golden.adapter_version
        or identity["contract_version"]
        != "heterodiff-native-event-adapter-v1"
    ):
        _reject()
    _require_digest(identity["policy_sha256"])
    capabilities = _require_keys(
        tree["capabilities"],
        _DESCRIPTOR_CAPABILITY_KEYS,
    )
    for name in (
        "evaluation_labels",
        "fitted_state",
        "private_provenance",
        "raw_byte_reconstruction",
        "semantic_reconstruction",
        "static_context",
    ):
        _require_bool(capabilities[name])
    if capabilities["semantic_reconstruction"] is not True:
        _reject()
    if capabilities["multiplicity_mode"] not in (
        "simple",
        "finite_counting",
    ):
        _reject()
    if capabilities["time_measure"] not in (
        "continuous",
        "atomic_grid",
        "mixed",
    ):
        _reject()
    representations = capabilities["supported_representation_ids"]
    if (
        type(representations) is not list
        or len(representations) > MAXIMUM_APPROVED_CASE_REPRESENTATION_IDS
    ):
        _reject()
    checked = tuple(_require_public_id(item) for item in representations)
    if checked != tuple(sorted(set(checked))):
        _reject()
    if (
        "heterodiff.atomic-counting-grid.v1" in checked
        and capabilities["time_measure"] != "atomic_grid"
    ):
        _reject()


def _parse_partition(value: bytes) -> Tuple[str, str, str]:
    tree = _require_keys(
        _strict_json_bytes(
            value,
            maximum=MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
        ),
        _PARTITION_KEYS,
    )
    if tree["unicode_profile"] != "ucd-3.2.0":
        _reject()
    split = tree["split"]
    if type(split) is not str or split not in ("train", "validation", "test"):
        _reject()
    return (
        _require_private_text(tree["sample_id"]),
        _require_private_text(tree["group_id"]),
        split,
    )


def _validate_split_manifest(
    value: bytes,
    partition: Tuple[str, str, str],
) -> None:
    tree = _require_keys(
        _strict_json_bytes(
            value,
            maximum=MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES,
        ),
        _SPLIT_MANIFEST_KEYS,
    )
    if (
        tree["unicode_profile"] != "ucd-3.2.0"
        or type(tree["entries"]) is not list
        or not tree["entries"]
        or len(tree["entries"]) > MAXIMUM_SPLIT_ENTRIES
    ):
        _reject()
    entries = []
    for raw_entry in tree["entries"]:
        entry = _require_keys(raw_entry, _SPLIT_ENTRY_KEYS)
        split = entry["split"]
        if type(split) is not str or split not in (
            "train",
            "validation",
            "test",
        ):
            _reject()
        entries.append(
            (
                _require_private_text(entry["sample_id"]),
                _require_private_text(entry["group_id"]),
                split,
            )
        )
    # Serialized order is (group_id, sample_id, split), while tuple storage
    # above is (sample_id, group_id, split).
    if tuple(entries) != tuple(
        sorted(entries, key=lambda item: (item[1], item[0], item[2]))
    ):
        _reject()
    sample_ids = tuple(item[0] for item in entries)
    if len(sample_ids) != len(set(sample_ids)):
        _reject()
    group_splits = {}
    for _sample_id, group_id, split in entries:
        prior = group_splits.setdefault(group_id, split)
        if (
            prior != split
            or len(group_splits) > MAXIMUM_SPLIT_GROUPS
        ):
            _reject()
    matching = tuple(item for item in entries if item[0] == partition[0])
    if matching != (partition,):
        _reject()


_DEVELOPMENT_RUN_RECEIPT_KEYS = (
    "address_space_limit_bytes",
    "address_space_limit_method_id",
    "aggregate_output_limit_bytes",
    "argv_mode_id",
    "argv_sha256",
    "artifact_type",
    "captured_interpreter_executable_byte_count",
    "captured_interpreter_executable_sha256",
    "clock_method_id",
    "containment_attestation_sha256",
    "containment_status_id",
    "cwd_launch_method_id",
    "decision_eligible",
    "direct_child_reaped",
    "elapsed_monotonic_nanoseconds",
    "environment_sha256",
    "execution_attested",
    "execution_backend_id",
    "exit_status",
    "filesystem_confinement_id",
    "filesystem_read_scope_attested",
    "filesystem_write_scope_attested",
    "format_version",
    "implementation_status_id",
    "interpreter_capture_method_id",
    "interpreter_execution_identity_attested",
    "interpreter_observation_sha256",
    "managed_process_group_observed_quiescent",
    "measured_peak_rss_bytes",
    "network_confinement_id",
    "network_denial_attested",
    "oracle_id",
    "oracle_registry_byte_count",
    "oracle_registry_sha256",
    "output_capture_method_id",
    "output_limit_kind_id",
    "peak_rss_enforcement_exact",
    "peak_rss_limit_bytes",
    "peak_rss_method_id",
    "process_cleanup_method_id",
    "process_containment_id",
    "process_group_cleanup_triggered",
    "process_group_nonquiescence_triggered",
    "process_tree_escape_prevented",
    "process_tree_quiescence_attested",
    "request_frame_byte_count",
    "request_frame_sha256",
    "response_frame_byte_count",
    "response_frame_sha256",
    "response_identity_status_id",
    "run_input_sha256",
    "runner_id",
    "selected_source_byte_count",
    "selected_source_sha256",
    "semantic_validation_status_id",
    "source_archive_byte_count",
    "source_archive_inventory_byte_count",
    "source_archive_inventory_sha256",
    "source_archive_membership_receipt_byte_count",
    "source_archive_membership_receipt_sha256",
    "source_archive_sha256",
    "source_load_method_id",
    "source_object_id",
    "source_policy_receipt_byte_count",
    "source_policy_receipt_sha256",
    "source_role_id",
    "status_id",
    "stderr_complete",
    "stderr_limit_bytes",
    "stderr_sha256",
    "stderr_size_bytes",
    "stdin_complete",
    "stdin_limit_bytes",
    "stdin_written_sha256",
    "stdin_written_size_bytes",
    "stdout_complete",
    "stdout_limit_bytes",
    "stdout_sha256",
    "stdout_size_bytes",
    "terminating_signal",
    "wall_limit_triggered",
    "wall_time_limit_nanoseconds",
    "working_directory_sha256",
)


def _empty_environment_sha256() -> str:
    return _sequence_sha256(
        "heterodiff.adapter.execution.environment.v1",
        (),
    )


def _parse_successful_development_receipt(
    value: bytes,
    *,
    raw_input: IndependentOracleVerificationInputV1,
    oracle_id: str,
    selected_source: bytes,
) -> dict:
    tree = _require_keys(
        _strict_json_bytes(
            value,
            maximum=MAXIMUM_ORACLE_DEVELOPMENT_RECEIPT_BYTES,
        ),
        _DEVELOPMENT_RUN_RECEIPT_KEYS,
    )
    fixed_values = {
        "artifact_type": DEVELOPMENT_ORACLE_RUN_RECEIPT_ARTIFACT_TYPE,
        "format_version": "1",
        "runner_id": DEVELOPMENT_ORACLE_RUNNER_ID,
        "implementation_status_id": DEVELOPMENT_ORACLE_IMPLEMENTATION_STATUS,
        "containment_status_id": (
            DEVELOPMENT_ORACLE_CONTAINMENT_STATUS_ID
        ),
        "source_role_id": SOURCE_ARCHIVE_ORACLE_ROLE_ID,
        "source_load_method_id": (
            DEVELOPMENT_ORACLE_SOURCE_LOAD_METHOD_ID
        ),
        "argv_mode_id": DEVELOPMENT_ORACLE_ARGV_MODE_ID,
        "interpreter_capture_method_id": (
            DEVELOPMENT_ORACLE_INTERPRETER_CAPTURE_METHOD_ID
        ),
        "execution_backend_id": DEVELOPMENT_ORACLE_EXECUTION_BACKEND_ID,
        "cwd_launch_method_id": DEVELOPMENT_ORACLE_CWD_LAUNCH_METHOD_ID,
        "output_capture_method_id": (
            DEVELOPMENT_ORACLE_OUTPUT_CAPTURE_METHOD_ID
        ),
        "semantic_validation_status_id": (
            DEVELOPMENT_ORACLE_SEMANTIC_STATUS_ID
        ),
        "clock_method_id": DEVELOPMENT_ORACLE_CLOCK_METHOD_ID,
        "address_space_limit_method_id": (
            DEVELOPMENT_ORACLE_NOT_PROVIDED_ID
        ),
        "peak_rss_method_id": DEVELOPMENT_ORACLE_NOT_PROVIDED_ID,
        "filesystem_confinement_id": (
            DEVELOPMENT_ORACLE_NOT_PROVIDED_ID
        ),
        "network_confinement_id": DEVELOPMENT_ORACLE_NOT_PROVIDED_ID,
        "process_containment_id": (
            DEVELOPMENT_ORACLE_PROCESS_CONTAINMENT_ID
        ),
        "process_cleanup_method_id": (
            DEVELOPMENT_ORACLE_PROCESS_CLEANUP_METHOD_ID
        ),
        "stdin_limit_bytes": MAXIMUM_ORACLE_WORKER_FRAME_BYTES,
        "stdout_limit_bytes": MAXIMUM_ORACLE_WORKER_FRAME_BYTES,
        "stderr_limit_bytes": MAXIMUM_ORACLE_DEVELOPMENT_STDERR_BYTES,
        "aggregate_output_limit_bytes": (
            MAXIMUM_ORACLE_DEVELOPMENT_AGGREGATE_OUTPUT_BYTES
        ),
        "wall_time_limit_nanoseconds": (
            MAXIMUM_ORACLE_DEVELOPMENT_WALL_TIME_NANOSECONDS
        ),
        "status_id": DEVELOPMENT_ORACLE_COMPLETED_STATUS,
        "response_identity_status_id": (
            DEVELOPMENT_ORACLE_RESPONSE_MATCHED_STATUS
        ),
        "output_limit_kind_id": DEVELOPMENT_ORACLE_OUTPUT_LIMIT_NONE,
    }
    if any(tree[name] != expected for name, expected in fixed_values.items()):
        _reject()
    fixed_false = (
        "decision_eligible",
        "execution_attested",
        "interpreter_execution_identity_attested",
        "peak_rss_enforcement_exact",
        "process_tree_escape_prevented",
        "process_tree_quiescence_attested",
        "filesystem_read_scope_attested",
        "filesystem_write_scope_attested",
        "network_denial_attested",
        "wall_limit_triggered",
        "process_group_cleanup_triggered",
        "process_group_nonquiescence_triggered",
    )
    if any(tree[name] is not False for name in fixed_false):
        _reject()
    fixed_true = (
        "direct_child_reaped",
        "managed_process_group_observed_quiescent",
        "stdin_complete",
        "stdout_complete",
        "stderr_complete",
    )
    if any(tree[name] is not True for name in fixed_true):
        _reject()
    if (
        tree["containment_attestation_sha256"] is not None
        or tree["address_space_limit_bytes"] is not None
        or tree["peak_rss_limit_bytes"] is not None
        or tree["measured_peak_rss_bytes"] is not None
        or tree["terminating_signal"] is not None
        or tree["exit_status"] != 0
    ):
        _reject()

    for name in (
        "run_input_sha256",
        "oracle_registry_sha256",
        "source_archive_inventory_sha256",
        "source_archive_sha256",
        "source_archive_membership_receipt_sha256",
        "selected_source_sha256",
        "source_policy_receipt_sha256",
        "captured_interpreter_executable_sha256",
        "interpreter_observation_sha256",
        "argv_sha256",
        "environment_sha256",
        "working_directory_sha256",
        "request_frame_sha256",
        "stdin_written_sha256",
        "response_frame_sha256",
        "stdout_sha256",
        "stderr_sha256",
    ):
        _require_digest(tree[name])
    for name in ("oracle_id", "source_object_id"):
        _require_token(tree[name])
    for name in (
        "oracle_registry_byte_count",
        "source_archive_inventory_byte_count",
        "source_archive_byte_count",
        "source_archive_membership_receipt_byte_count",
        "selected_source_byte_count",
        "source_policy_receipt_byte_count",
        "captured_interpreter_executable_byte_count",
        "request_frame_byte_count",
        "stdin_written_size_bytes",
        "response_frame_byte_count",
        "stdout_size_bytes",
        "stderr_size_bytes",
        "elapsed_monotonic_nanoseconds",
        "exit_status",
    ):
        _require_integer(tree[name])

    if (
        tree["oracle_id"] != oracle_id
        or tree["source_object_id"] != oracle_id
        or tree["oracle_registry_byte_count"]
        != len(raw_input.oracle_registry_bytes)
        or tree["oracle_registry_sha256"]
        != _plain_sha256(raw_input.oracle_registry_bytes)
        or tree["source_archive_inventory_byte_count"]
        != len(raw_input.source_archive_inventory_bytes)
        or tree["source_archive_inventory_sha256"]
        != _plain_sha256(raw_input.source_archive_inventory_bytes)
        or tree["source_archive_byte_count"]
        != len(raw_input.source_archive_bytes)
        or tree["source_archive_sha256"]
        != _plain_sha256(raw_input.source_archive_bytes)
        or tree["source_archive_membership_receipt_byte_count"]
        != len(raw_input.source_archive_membership_receipt_bytes)
        or tree["source_archive_membership_receipt_sha256"]
        != _domain_sha256(
            SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_DIGEST_DOMAIN,
            raw_input.source_archive_membership_receipt_bytes,
        )
        or tree["selected_source_byte_count"] != len(selected_source)
        or tree["selected_source_sha256"] != _plain_sha256(selected_source)
        or tree["source_policy_receipt_byte_count"]
        != len(raw_input.source_policy_receipt_bytes)
        or tree["source_policy_receipt_sha256"]
        != _domain_sha256(
            ORACLE_SOURCE_POLICY_DIGEST_DOMAIN,
            raw_input.source_policy_receipt_bytes,
        )
        or tree["captured_interpreter_executable_byte_count"]
        != len(raw_input.interpreter_executable_bytes)
        or tree["captured_interpreter_executable_sha256"]
        != _plain_sha256(raw_input.interpreter_executable_bytes)
        or tree["environment_sha256"] != _empty_environment_sha256()
        or tree["request_frame_byte_count"]
        != len(raw_input.request_frame_bytes)
        or tree["request_frame_sha256"]
        != _plain_sha256(raw_input.request_frame_bytes)
        or tree["stdin_written_size_bytes"]
        != len(raw_input.request_frame_bytes)
        or tree["stdin_written_sha256"]
        != _plain_sha256(raw_input.request_frame_bytes)
        or tree["response_frame_byte_count"]
        != len(raw_input.response_frame_bytes)
        or tree["response_frame_sha256"]
        != _plain_sha256(raw_input.response_frame_bytes)
        or tree["stdout_size_bytes"] != len(raw_input.response_frame_bytes)
        or tree["stdout_sha256"]
        != _plain_sha256(raw_input.response_frame_bytes)
        or tree["stderr_size_bytes"] != len(raw_input.stderr_bytes)
        or tree["stderr_sha256"] != _plain_sha256(raw_input.stderr_bytes)
        or raw_input.stderr_bytes != b""
        or tree["elapsed_monotonic_nanoseconds"]
        > MAXIMUM_ORACLE_DEVELOPMENT_WALL_TIME_NANOSECONDS
    ):
        _reject()
    return tree


@dataclass(frozen=True)
class IndependentOracleByteVerificationReceiptV1:
    """Deterministic static byte-agreement receipt; never authority."""

    verification_input_sha256: str
    oracle_id: str
    oracle_registry_byte_count: int
    oracle_registry_sha256: str
    source_archive_inventory_byte_count: int
    source_archive_inventory_sha256: str
    source_archive_byte_count: int
    source_archive_sha256: str
    source_archive_membership_receipt_byte_count: int
    source_archive_membership_receipt_sha256: str
    source_policy_receipt_byte_count: int
    source_policy_receipt_sha256: str
    independent_golden_receipt_byte_count: int
    independent_golden_receipt_sha256: str
    selected_source_byte_count: int
    selected_source_sha256: str
    interpreter_executable_byte_count: int
    interpreter_executable_sha256: str
    development_runner_receipt_byte_count: int
    development_runner_receipt_sha256: str
    request_frame_byte_count: int
    request_frame_sha256: str
    response_frame_byte_count: int
    response_frame_sha256: str
    stderr_byte_count: int
    stderr_sha256: str
    expected_configuration_payload_byte_count: int
    expected_configuration_sha256: str
    expected_evidence_sha256: str
    expected_native_observation_sha256: str
    descriptor_sha256: str
    split_manifest_sha256: str
    development_runner_status_id: str
    artifact_type: str = field(
        default=INDEPENDENT_ORACLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE,
        init=False,
    )
    format_version: str = field(default="1", init=False)
    verifier_id: str = field(
        default=INDEPENDENT_ORACLE_VERIFIER_ID,
        init=False,
    )
    implementation_status_id: str = field(
        default=INDEPENDENT_ORACLE_VERIFIER_IMPLEMENTATION_STATUS,
        init=False,
    )
    status_id: str = field(
        default=INDEPENDENT_ORACLE_VERIFICATION_STATUS,
        init=False,
    )
    decision_status: str = field(
        default=INDEPENDENT_ORACLE_VERIFIER_DECISION_STATUS,
        init=False,
    )
    decision_eligible: bool = field(default=False, init=False)
    execution_attested: bool = field(default=False, init=False)
    containment_attested: bool = field(default=False, init=False)
    custody_authenticated: bool = field(default=False, init=False)
    execution_input_set_membership_authenticated: bool = field(
        default=False,
        init=False,
    )
    case_authority_authenticated: bool = field(
        default=False,
        init=False,
    )
    response_payload_schema_authenticated: bool = field(
        default=False,
        init=False,
    )
    semantic_truth_attested: bool = field(default=False, init=False)
    expected_evidence_leaf_complete: bool = field(
        default=False,
        init=False,
    )
    source_policy_semantics_independently_evaluated: bool = field(
        default=False,
        init=False,
    )
    interpreter_execution_identity_attested: bool = field(
        default=False,
        init=False,
    )
    elapsed_time_authenticated: bool = field(default=False, init=False)
    platform_observations_authenticated: bool = field(
        default=False,
        init=False,
    )
    process_observations_authenticated: bool = field(
        default=False,
        init=False,
    )
    semantic_scope_id: str = field(
        default=INDEPENDENT_ORACLE_SEMANTIC_SCOPE_ID,
        init=False,
    )
    development_runner_receipt_scope_id: str = field(
        default=INDEPENDENT_ORACLE_RUN_RECEIPT_SCOPE_ID,
        init=False,
    )

    def __post_init__(self) -> None:
        if type(self) is not IndependentOracleByteVerificationReceiptV1:
            raise TypeError("independent oracle verification receipt must be exact")
        _validate_verification_receipt_fields(self)


def _validate_verification_receipt_fields(
    value: IndependentOracleByteVerificationReceiptV1,
) -> None:
    try:
        for name in (
            "verification_input_sha256",
            "oracle_registry_sha256",
            "source_archive_inventory_sha256",
            "source_archive_sha256",
            "source_archive_membership_receipt_sha256",
            "source_policy_receipt_sha256",
            "independent_golden_receipt_sha256",
            "selected_source_sha256",
            "interpreter_executable_sha256",
            "development_runner_receipt_sha256",
            "request_frame_sha256",
            "response_frame_sha256",
            "stderr_sha256",
            "expected_configuration_sha256",
            "expected_evidence_sha256",
            "expected_native_observation_sha256",
            "descriptor_sha256",
            "split_manifest_sha256",
        ):
            _require_digest(getattr(value, name))
        _require_token(value.oracle_id)
        for name in (
            "oracle_registry_byte_count",
            "source_archive_inventory_byte_count",
            "source_archive_byte_count",
            "source_archive_membership_receipt_byte_count",
            "source_policy_receipt_byte_count",
            "independent_golden_receipt_byte_count",
            "selected_source_byte_count",
            "interpreter_executable_byte_count",
            "development_runner_receipt_byte_count",
            "request_frame_byte_count",
            "response_frame_byte_count",
            "stderr_byte_count",
            "expected_configuration_payload_byte_count",
        ):
            _require_integer(getattr(value, name))
        fixed_values = {
            "artifact_type": (
                INDEPENDENT_ORACLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE
            ),
            "format_version": "1",
            "verifier_id": INDEPENDENT_ORACLE_VERIFIER_ID,
            "implementation_status_id": (
                INDEPENDENT_ORACLE_VERIFIER_IMPLEMENTATION_STATUS
            ),
            "status_id": INDEPENDENT_ORACLE_VERIFICATION_STATUS,
            "decision_status": INDEPENDENT_ORACLE_VERIFIER_DECISION_STATUS,
            "semantic_scope_id": INDEPENDENT_ORACLE_SEMANTIC_SCOPE_ID,
            "development_runner_receipt_scope_id": (
                INDEPENDENT_ORACLE_RUN_RECEIPT_SCOPE_ID
            ),
            "development_runner_status_id": (
                DEVELOPMENT_ORACLE_COMPLETED_STATUS
            ),
        }
        if any(
            type(getattr(value, name)) is not type(expected)
            or getattr(value, name) != expected
            for name, expected in fixed_values.items()
        ):
            _reject()
        false_fields = (
            "decision_eligible",
            "execution_attested",
            "containment_attested",
            "custody_authenticated",
            "execution_input_set_membership_authenticated",
            "case_authority_authenticated",
            "response_payload_schema_authenticated",
            "semantic_truth_attested",
            "expected_evidence_leaf_complete",
            "source_policy_semantics_independently_evaluated",
            "interpreter_execution_identity_attested",
            "elapsed_time_authenticated",
            "platform_observations_authenticated",
            "process_observations_authenticated",
        )
        if any(getattr(value, name) is not False for name in false_fields):
            _reject()
        if (
            value.oracle_registry_byte_count <= 0
            or value.oracle_registry_byte_count
            > MAXIMUM_ORACLE_REGISTRY_BYTES
            or value.source_archive_inventory_byte_count <= 0
            or value.source_archive_inventory_byte_count
            > MAXIMUM_SOURCE_ARCHIVE_INVENTORY_BYTES
            or value.source_archive_byte_count <= 0
            or value.source_archive_byte_count > MAXIMUM_SOURCE_ARCHIVE_BYTES
            or value.source_archive_membership_receipt_byte_count <= 0
            or value.source_archive_membership_receipt_byte_count
            > MAXIMUM_SOURCE_ARCHIVE_RECEIPT_BYTES
            or value.source_policy_receipt_byte_count <= 0
            or value.source_policy_receipt_byte_count
            > MAXIMUM_ORACLE_POLICY_RECEIPT_BYTES
            or value.independent_golden_receipt_byte_count <= 0
            or value.independent_golden_receipt_byte_count
            > MAXIMUM_INDEPENDENT_GOLDEN_RECEIPT_BYTES
            or value.selected_source_byte_count <= 0
            or value.selected_source_byte_count
            > MAXIMUM_ORACLE_DEVELOPMENT_SOURCE_ARGV_BYTES
            or value.interpreter_executable_byte_count <= 0
            or value.interpreter_executable_byte_count
            > MAXIMUM_ORACLE_DEVELOPMENT_INTERPRETER_BYTES
            or value.development_runner_receipt_byte_count <= 0
            or value.development_runner_receipt_byte_count
            > MAXIMUM_ORACLE_DEVELOPMENT_RECEIPT_BYTES
            or value.request_frame_byte_count <= 0
            or value.request_frame_byte_count
            > MAXIMUM_ORACLE_WORKER_FRAME_BYTES
            or value.response_frame_byte_count <= 0
            or value.response_frame_byte_count
            > MAXIMUM_ORACLE_WORKER_FRAME_BYTES
            or value.stderr_byte_count != 0
            or value.stderr_sha256 != _EMPTY_SHA256
            or value.expected_configuration_payload_byte_count <= 0
            or value.expected_configuration_payload_byte_count
            > MAXIMUM_ORACLE_WORKER_STRUCTURED_PAYLOAD_BYTES
        ):
            _reject()
    except _Rejected as error:
        raise ValueError(
            "independent oracle verification receipt fields are invalid"
        ) from error


def _receipt_tree(
    value: IndependentOracleByteVerificationReceiptV1,
) -> dict:
    if type(value) is not IndependentOracleByteVerificationReceiptV1:
        raise TypeError("independent oracle verification receipt must be exact")
    IndependentOracleByteVerificationReceiptV1.__post_init__(value)
    return {
        item.name: getattr(value, item.name)
        for item in fields(IndependentOracleByteVerificationReceiptV1)
    }


def independent_oracle_verification_receipt_bytes(
    value: IndependentOracleByteVerificationReceiptV1,
) -> bytes:
    """Return canonical ASCII JSON for one nondecision verifier receipt."""

    try:
        result = _canonical_json_bytes(
            _receipt_tree(value),
            maximum=MAXIMUM_VERIFICATION_RECEIPT_BYTES,
        )
    except (
        AttributeError,
        TypeError,
        ValueError,
        _Rejected,
        RecursionError,
    ):
        _fail(IndependentOracleVerificationCode.CANONICALIZATION_FAILED)
    return result


def independent_oracle_verification_receipt_sha256(
    value: IndependentOracleByteVerificationReceiptV1,
) -> str:
    """Return the Phase-D single-payload domain digest of the receipt."""

    payload = independent_oracle_verification_receipt_bytes(value)
    try:
        return _domain_sha256(
            INDEPENDENT_ORACLE_VERIFICATION_RECEIPT_DIGEST_DOMAIN,
            payload,
        )
    except _Rejected:
        _fail(IndependentOracleVerificationCode.CANONICALIZATION_FAILED)


def validate_independent_oracle_verification_receipt(
    value: object,
) -> IndependentOracleByteVerificationReceiptV1:
    """Return a fresh structural receipt snapshot without evidence authority."""

    if type(value) is not IndependentOracleByteVerificationReceiptV1:
        _fail(IndependentOracleVerificationCode.RECEIPT_INVALID)
    try:
        IndependentOracleByteVerificationReceiptV1.__post_init__(value)
        return IndependentOracleByteVerificationReceiptV1(
            **{
                item.name: getattr(value, item.name)
                for item in fields(IndependentOracleByteVerificationReceiptV1)
                if item.init
            }
        )
    except IndependentOracleVerificationError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(IndependentOracleVerificationCode.RECEIPT_INVALID)


@dataclass(frozen=True)
class IndependentOracleByteVerificationResultV1:
    """Constructible structural transport; deep raw-input validation is required."""

    receipt: IndependentOracleByteVerificationReceiptV1
    receipt_bytes: bytes
    receipt_sha256: str

    def __post_init__(self) -> None:
        if type(self) is not IndependentOracleByteVerificationResultV1:
            raise TypeError("independent oracle verification result must be exact")
        _validate_result_transport(self)


def _validate_result_transport(
    value: IndependentOracleByteVerificationResultV1,
) -> None:
    receipt = validate_independent_oracle_verification_receipt(value.receipt)
    if type(value.receipt_bytes) is not bytes:
        raise TypeError("independent verifier receipt bytes must be exact")
    if (
        not value.receipt_bytes
        or len(value.receipt_bytes) > MAXIMUM_VERIFICATION_RECEIPT_BYTES
    ):
        raise ValueError("independent verifier receipt bytes exceed their bound")
    if type(value.receipt_sha256) is not str:
        raise TypeError("independent verifier receipt digest must be exact")
    try:
        _require_digest(value.receipt_sha256)
    except _Rejected as error:
        raise ValueError(
            "independent verifier receipt digest is invalid"
        ) from error
    if (
        independent_oracle_verification_receipt_bytes(receipt)
        != value.receipt_bytes
        or independent_oracle_verification_receipt_sha256(receipt)
        != value.receipt_sha256
    ):
        raise ValueError("independent verifier result transport differs")


def _parse_registry_closed(value: bytes) -> Tuple[_RegistryEntry, ...]:
    try:
        return _parse_registry(value)
    except _Rejected:
        _fail(IndependentOracleVerificationCode.REGISTRY_INVALID)


def _validate_archive_closed(
    inventory_bytes: bytes,
    archive_bytes: bytes,
) -> _ArchiveMaterial:
    try:
        return _validate_archive(inventory_bytes, archive_bytes)
    except _Rejected:
        _fail(IndependentOracleVerificationCode.ARCHIVE_INVALID)


def _parse_membership_closed(value: bytes) -> _Membership:
    try:
        return _parse_membership(value)
    except _Rejected:
        _fail(IndependentOracleVerificationCode.MEMBERSHIP_INVALID)


def _parse_policy_closed(value: bytes) -> _PolicyReceipt:
    try:
        return _parse_policy_receipt(value)
    except _Rejected:
        _fail(IndependentOracleVerificationCode.POLICY_RECEIPT_INVALID)


def _parse_golden_closed(value: bytes) -> _GoldenReceipt:
    try:
        return _parse_golden_receipt(value)
    except _Rejected:
        _fail(IndependentOracleVerificationCode.GOLDEN_RECEIPT_INVALID)


def _parse_request_closed(value: bytes) -> _Request:
    try:
        return _parse_request(value)
    except _Rejected:
        _fail(IndependentOracleVerificationCode.REQUEST_INVALID)


def _parse_response_closed(value: bytes) -> _Response:
    try:
        return _parse_response(value)
    except _Rejected:
        _fail(IndependentOracleVerificationCode.RESPONSE_INVALID)


def _selected_source(
    archive: _ArchiveMaterial,
    *,
    oracle_id: str,
) -> Tuple[_SourceObject, bytes]:
    records = tuple(
        item
        for item in archive.inventory.source_objects
        if item.role_id == SOURCE_ARCHIVE_ORACLE_ROLE_ID
        and item.source_object_id == oracle_id
    )
    if len(records) != 1:
        _reject()
    record = records[0]
    matching = tuple(
        raw
        for raw in archive.member_contents
        if len(raw) == record.source_byte_count
        and _plain_sha256(raw) == record.source_sha256
    )
    if not matching or any(raw != matching[0] for raw in matching):
        _reject()
    if (
        len(matching[0])
        > MAXIMUM_ORACLE_DEVELOPMENT_SOURCE_ARGV_BYTES
    ):
        _reject()
    return record, matching[0]


def _verification_input_sha256(
    value: IndependentOracleVerificationInputV1,
) -> str:
    raw_values = tuple(
        getattr(value, name.decode("ascii"))
        for name in _VERIFICATION_INPUT_FIELD_NAMES
    )
    return _named_sequence_sha256(
        INDEPENDENT_ORACLE_VERIFICATION_INPUT_DIGEST_DOMAIN,
        _VERIFICATION_INPUT_FIELD_NAMES,
        raw_values,
    )


def _build_verified_result(
    raw_input: IndependentOracleVerificationInputV1,
) -> IndependentOracleByteVerificationResultV1:
    registry = _parse_registry_closed(raw_input.oracle_registry_bytes)
    archive = _validate_archive_closed(
        raw_input.source_archive_inventory_bytes,
        raw_input.source_archive_bytes,
    )
    membership = _parse_membership_closed(
        raw_input.source_archive_membership_receipt_bytes
    )
    policy = _parse_policy_closed(raw_input.source_policy_receipt_bytes)
    golden = _parse_golden_closed(
        raw_input.independent_golden_receipt_bytes
    )
    request = _parse_request_closed(raw_input.request_frame_bytes)
    response = _parse_response_closed(raw_input.response_frame_bytes)

    try:
        registry_identities = tuple(
            (
                item.oracle_id,
                item.oracle_source_byte_count,
                item.oracle_source_sha256,
            )
            for item in registry
        )
        archive_identities = tuple(
            (
                item.source_object_id,
                item.source_byte_count,
                item.source_sha256,
            )
            for item in archive.inventory.source_objects
            if item.role_id == SOURCE_ARCHIVE_ORACLE_ROLE_ID
        )
        if registry_identities != archive_identities:
            _reject()
        registry_entries = tuple(
            item for item in registry if item.oracle_id == request.oracle_id
        )
        if len(registry_entries) != 1:
            _reject()
        registry_entry = registry_entries[0]
        source_object, source_bytes = _selected_source(
            archive,
            oracle_id=request.oracle_id,
        )
        expected_membership = _Membership(
            archive_sha256=_plain_sha256(raw_input.source_archive_bytes),
            inventory_sha256=_plain_sha256(
                raw_input.source_archive_inventory_bytes
            ),
            role_id=SOURCE_ARCHIVE_ORACLE_ROLE_ID,
            source_byte_count=source_object.source_byte_count,
            source_object_id=source_object.source_object_id,
            source_sha256=source_object.source_sha256,
        )
        if membership != expected_membership:
            _reject()
    except _Rejected:
        _fail(IndependentOracleVerificationCode.BYTE_BINDING_MISMATCH)

    try:
        expected_oracle_identity = (
            request.oracle_id,
            len(source_bytes),
            _plain_sha256(source_bytes),
        )
        if (
            expected_oracle_identity
            != (
                registry_entry.oracle_id,
                registry_entry.oracle_source_byte_count,
                registry_entry.oracle_source_sha256,
            )
            or expected_oracle_identity
            != (
                policy.oracle_id,
                policy.oracle_source_byte_count,
                policy.oracle_source_sha256,
            )
            or policy.forbidden_import_ids
            != registry_entry.forbidden_import_ids
            or policy.forbidden_name_ids
            != registry_entry.forbidden_name_ids
            or expected_oracle_identity
            != (
                golden.oracle_id,
                golden.oracle_source_byte_count,
                golden.oracle_source_sha256,
            )
            or expected_oracle_identity
            != (
                request.oracle_id,
                request.oracle_source_byte_count,
                request.oracle_source_sha256,
            )
            or golden.oracle_registry_sha256
            != _plain_sha256(raw_input.oracle_registry_bytes)
            or golden.source_byte_count != len(request.source_bytes)
            or golden.source_sha256 != _plain_sha256(request.source_bytes)
        ):
            _reject()
    except _Rejected:
        _fail(IndependentOracleVerificationCode.BYTE_BINDING_MISMATCH)

    try:
        _validate_descriptor(request.descriptor_payload_bytes, golden)
        partition = _parse_partition(request.partition_payload_bytes)
        _validate_split_manifest(
            request.split_manifest_payload_bytes,
            partition,
        )
        descriptor_sha256 = _domain_sha256(
            DESCRIPTOR_DIGEST_DOMAIN,
            request.descriptor_payload_bytes,
        )
        split_manifest_sha256 = _domain_sha256(
            SPLIT_MANIFEST_DIGEST_DOMAIN,
            request.split_manifest_payload_bytes,
        )
        if (
            descriptor_sha256 != golden.descriptor_sha256
            or split_manifest_sha256 != golden.split_manifest_sha256
        ):
            _reject()
    except _Rejected:
        _fail(IndependentOracleVerificationCode.PAYLOAD_MISMATCH)

    try:
        request_sha256 = _plain_sha256(raw_input.request_frame_bytes)
        if (
            response.request_frame_sha256 != request_sha256
            or response.case_ordinal != request.case_ordinal
            or response.oracle_id != request.oracle_id
            or response.oracle_source_byte_count
            != request.oracle_source_byte_count
            or response.oracle_source_sha256
            != request.oracle_source_sha256
        ):
            _reject()
    except _Rejected:
        _fail(IndependentOracleVerificationCode.RESPONSE_INVALID)

    try:
        configuration_sha256 = _domain_sha256(
            PRIVATE_NATIVE_CONFIGURATION_DIGEST_DOMAIN,
            response.expected_configuration_payload_bytes,
        )
        evidence_sha256 = _domain_sha256(
            EXPECTED_EVIDENCE_DIGEST_DOMAIN,
            response.expected_evidence_payload_bytes,
        )
        if (
            len(response.expected_configuration_payload_bytes)
            != golden.expected_configuration_payload_byte_count
            or configuration_sha256
            != golden.expected_configuration_sha256
            or evidence_sha256 != golden.expected_evidence_sha256
            or response.expected_native_observation_sha256
            != golden.expected_native_observation_sha256
        ):
            _reject()
    except _Rejected:
        _fail(IndependentOracleVerificationCode.PAYLOAD_MISMATCH)

    try:
        development_receipt = _parse_successful_development_receipt(
            raw_input.development_runner_receipt_bytes,
            raw_input=raw_input,
            oracle_id=request.oracle_id,
            selected_source=source_bytes,
        )
    except _Rejected:
        _fail(IndependentOracleVerificationCode.RUN_RECEIPT_INVALID)

    try:
        receipt = IndependentOracleByteVerificationReceiptV1(
            verification_input_sha256=_verification_input_sha256(raw_input),
            oracle_id=request.oracle_id,
            oracle_registry_byte_count=len(raw_input.oracle_registry_bytes),
            oracle_registry_sha256=_plain_sha256(
                raw_input.oracle_registry_bytes
            ),
            source_archive_inventory_byte_count=len(
                raw_input.source_archive_inventory_bytes
            ),
            source_archive_inventory_sha256=_plain_sha256(
                raw_input.source_archive_inventory_bytes
            ),
            source_archive_byte_count=len(raw_input.source_archive_bytes),
            source_archive_sha256=_plain_sha256(
                raw_input.source_archive_bytes
            ),
            source_archive_membership_receipt_byte_count=len(
                raw_input.source_archive_membership_receipt_bytes
            ),
            source_archive_membership_receipt_sha256=_domain_sha256(
                SOURCE_ARCHIVE_MEMBERSHIP_RECEIPT_DIGEST_DOMAIN,
                raw_input.source_archive_membership_receipt_bytes,
            ),
            source_policy_receipt_byte_count=len(
                raw_input.source_policy_receipt_bytes
            ),
            source_policy_receipt_sha256=_domain_sha256(
                ORACLE_SOURCE_POLICY_DIGEST_DOMAIN,
                raw_input.source_policy_receipt_bytes,
            ),
            independent_golden_receipt_byte_count=len(
                raw_input.independent_golden_receipt_bytes
            ),
            independent_golden_receipt_sha256=_domain_sha256(
                INDEPENDENT_GOLDEN_RECEIPT_DIGEST_DOMAIN,
                raw_input.independent_golden_receipt_bytes,
            ),
            selected_source_byte_count=len(source_bytes),
            selected_source_sha256=_plain_sha256(source_bytes),
            interpreter_executable_byte_count=len(
                raw_input.interpreter_executable_bytes
            ),
            interpreter_executable_sha256=_plain_sha256(
                raw_input.interpreter_executable_bytes
            ),
            development_runner_receipt_byte_count=len(
                raw_input.development_runner_receipt_bytes
            ),
            development_runner_receipt_sha256=_sequence_sha256(
                DEVELOPMENT_ORACLE_RUN_RECEIPT_DIGEST_DOMAIN,
                (raw_input.development_runner_receipt_bytes,),
            ),
            request_frame_byte_count=len(raw_input.request_frame_bytes),
            request_frame_sha256=request_sha256,
            response_frame_byte_count=len(raw_input.response_frame_bytes),
            response_frame_sha256=_plain_sha256(
                raw_input.response_frame_bytes
            ),
            stderr_byte_count=len(raw_input.stderr_bytes),
            stderr_sha256=_plain_sha256(raw_input.stderr_bytes),
            expected_configuration_payload_byte_count=len(
                response.expected_configuration_payload_bytes
            ),
            expected_configuration_sha256=configuration_sha256,
            expected_evidence_sha256=evidence_sha256,
            expected_native_observation_sha256=(
                response.expected_native_observation_sha256
            ),
            descriptor_sha256=descriptor_sha256,
            split_manifest_sha256=split_manifest_sha256,
            development_runner_status_id=development_receipt["status_id"],
        )
        receipt_bytes = independent_oracle_verification_receipt_bytes(
            receipt
        )
        return IndependentOracleByteVerificationResultV1(
            receipt=receipt,
            receipt_bytes=receipt_bytes,
            receipt_sha256=(
                independent_oracle_verification_receipt_sha256(receipt)
            ),
        )
    except IndependentOracleVerificationError:
        raise
    except (_Rejected, AttributeError, TypeError, ValueError):
        _fail(IndependentOracleVerificationCode.INTERNAL_ERROR)


def verify_independent_oracle_bytes(
    value: IndependentOracleVerificationInputV1,
) -> IndependentOracleByteVerificationResultV1:
    """Independently validate the exact static V1 oracle byte relationships."""

    raw_input = _snapshot_input(value)
    try:
        return _build_verified_result(raw_input)
    except IndependentOracleVerificationError:
        raise
    except Exception:
        _fail(IndependentOracleVerificationCode.INTERNAL_ERROR)


def validate_independent_oracle_verification_result(
    value: IndependentOracleByteVerificationResultV1,
    raw_input: IndependentOracleVerificationInputV1,
) -> IndependentOracleByteVerificationResultV1:
    """Rebuild a result from all eleven raw inputs and require exact identity."""

    if type(value) is not IndependentOracleByteVerificationResultV1:
        _fail(IndependentOracleVerificationCode.RECEIPT_INVALID)
    try:
        _validate_result_transport(value)
    except IndependentOracleVerificationError:
        raise
    except (AttributeError, TypeError, ValueError):
        _fail(IndependentOracleVerificationCode.RECEIPT_INVALID)
    expected = verify_independent_oracle_bytes(raw_input)
    if value != expected:
        _fail(IndependentOracleVerificationCode.RECEIPT_INVALID)
    return expected


__all__ = [
    "DEVELOPMENT_ORACLE_COMPLETED_STATUS",
    "INDEPENDENT_ORACLE_RUN_RECEIPT_SCOPE_ID",
    "INDEPENDENT_ORACLE_SEMANTIC_SCOPE_ID",
    "INDEPENDENT_ORACLE_VERIFICATION_INPUT_DIGEST_DOMAIN",
    "INDEPENDENT_ORACLE_VERIFICATION_RECEIPT_ARTIFACT_TYPE",
    "INDEPENDENT_ORACLE_VERIFICATION_RECEIPT_DIGEST_DOMAIN",
    "INDEPENDENT_ORACLE_VERIFICATION_STATUS",
    "INDEPENDENT_ORACLE_VERIFIER_DECISION_STATUS",
    "INDEPENDENT_ORACLE_VERIFIER_ID",
    "INDEPENDENT_ORACLE_VERIFIER_IMPLEMENTATION_STATUS",
    "IndependentOracleByteVerificationReceiptV1",
    "IndependentOracleByteVerificationResultV1",
    "IndependentOracleVerificationCode",
    "IndependentOracleVerificationError",
    "IndependentOracleVerificationInputV1",
    "MAXIMUM_INDEPENDENT_ORACLE_VERIFICATION_INPUT_BYTES",
    "independent_oracle_verification_receipt_bytes",
    "independent_oracle_verification_receipt_sha256",
    "validate_independent_oracle_verification_receipt",
    "validate_independent_oracle_verification_result",
    "verify_independent_oracle_bytes",
]
