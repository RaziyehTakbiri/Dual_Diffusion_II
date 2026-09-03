"""Pure dormant simulator for two Solo Block 2 root-page operations.

Importing or calling this module performs no filesystem, network, process,
clock, randomness, entropy, tracker, data, or scientific action.  The module
contains no production execution entrypoint and accepts no general URL.  It
only validates immutable in-memory transcripts against a frozen future request
specification, parses supplied HTTP/1.1 response bytes, and derives explicitly
qualification-only records.

The future client, runtime closure, receipt custody, dirfd/O_EXCL mechanics,
durability, authority, and actual outbound operations are unimplemented and unproved.
Accordingly ``FETCH_ELIGIBLE`` is permanently false in this package.
"""

from __future__ import annotations

import datetime as _datetime
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any


EXECUTOR_SCHEMA_VERSION = "heterodiff-sb2-public-root-dormant-transcript-simulator-v2"
INERT_TRANSCRIPT_SCHEMA_VERSION = "heterodiff-sb2-public-root-inert-transcript-v2"
INTENT_SCHEMA_VERSION = "heterodiff-sb2-public-root-in-memory-intent-model-v2"
OUTCOME_SCHEMA_VERSION = "heterodiff-sb2-public-root-inert-outcome-v2"
SIMULATION_RESULT_SCHEMA_VERSION = OUTCOME_SCHEMA_VERSION

EXACT_RUNTIME_ADMITTED = False
FETCH_ELIGIBLE = False
RUNTIME_HOLD_REASON = (
    "RUNTIME_NETWORK_AUTHORITY_AND_FILESYSTEM_CUSTODY_CLOSURES_UNIMPLEMENTED_UNPROVED"
)
PACKAGE_ROLE = "DORMANT_TRANSCRIPT_SIMULATOR"

MAX_STATUS_BYTES = 8_192
MAX_HEADER_BYTES = 131_072
MAX_HEAD_BYTES = MAX_STATUS_BYTES + MAX_HEADER_BYTES
MAX_ENCODED_BODY_BYTES = 2_097_152
MAX_DECODED_BODY_BYTES = 2_097_152
MAX_TOTAL_RESPONSE_BYTES = MAX_HEAD_BYTES + MAX_ENCODED_BODY_BYTES
MAX_HEADER_COUNT = 128
MAX_HEADER_LINE_BYTES = 8_192
MAX_CERTIFICATE_BYTES = 1_048_576
MAX_TRANSCRIPT_CHUNK_COUNT = 4_096
MAX_PLAIN_CLONE_DEPTH = 64
MAX_PLAIN_CLONE_NODES = 65_536
MAX_PLAIN_CONTAINER_ITEMS = 8_192
MAX_PLAIN_STRING_CODEPOINTS = 262_144
MAX_PLAIN_STRING_UTF8_BYTES = 1_048_576
MAX_PLAIN_BYTES_LENGTH = MAX_TOTAL_RESPONSE_BYTES
MAX_PLAIN_INTEGER_BITS = 256
MAX_PLAIN_FLOAT_ABS = 1.0e100
USER_AGENT = "heterodiff-precontact-public-doc-recon-v2/2.0"
ACCEPT = "text/html, application/xhtml+xml;q=0.9, text/plain;q=0.8"

HUMAN_RELATIVE_PATH = (
    "PROJECT_SOLO_BLOCK2_PUBLIC_DOCUMENTATION_RECONNAISSANCE_AMENDMENT.md"
)
MACHINE_RELATIVE_PATH = (
    "research/fixtures/"
    "manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.json"
)
VALIDATOR_RELATIVE_PATH = (
    "research/diagnostics/"
    "manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.py"
)
AMENDMENT_TEST_RELATIVE_PATH = (
    "tests/unit/"
    "test_manuscript_v3_solo_block2_public_documentation_reconnaissance_amendment_v2.py"
)
EXECUTOR_RELATIVE_PATH = (
    "src/heterodiff/artifacts/"
    "solo_block2_public_documentation_reconnaissance_executor_v2.py"
)
EXECUTOR_TEST_RELATIVE_PATH = (
    "tests/unit/test_solo_block2_public_documentation_reconnaissance_executor_v2.py"
)

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
RFC3339_UTC = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z"
)
HEADER_NAME = re.compile(rb"[!#$%&'*+\-.^_`|~0-9A-Za-z]+\Z")
STATUS_LINE = re.compile(rb"HTTP/1\.1 ([0-9]{3}) ([\x20-\x7e]*)\r\n\Z")
TOKEN = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+\Z")


def _clone_plain(value: Any) -> Any:
    """Boundedly clone exact builtins without invoking caller protocols."""

    active_container_ids: set[int] = set()
    visited_nodes = 0

    def clone(current: Any, depth: int) -> Any:
        nonlocal visited_nodes
        visited_nodes += 1
        if visited_nodes > MAX_PLAIN_CLONE_NODES:
            raise TypeError("plain data node ceiling exceeded")
        if depth > MAX_PLAIN_CLONE_DEPTH:
            raise TypeError("plain data depth ceiling exceeded")
        if current is None or type(current) is bool:
            return current
        if type(current) is int:
            if current.bit_length() > MAX_PLAIN_INTEGER_BITS:
                raise TypeError("plain integer bit ceiling exceeded")
            return current
        if type(current) is float:
            if (
                current != current
                or current < -MAX_PLAIN_FLOAT_ABS
                or current > MAX_PLAIN_FLOAT_ABS
            ):
                raise TypeError("plain float magnitude must be finite and bounded")
            return current
        if type(current) is str:
            if len(current) > MAX_PLAIN_STRING_CODEPOINTS:
                raise TypeError("plain string codepoint ceiling exceeded")
            try:
                encoded_length = len(current.encode("utf-8"))
            except UnicodeEncodeError as exc:
                raise TypeError("plain string must be valid UTF-8 data") from exc
            if encoded_length > MAX_PLAIN_STRING_UTF8_BYTES:
                raise TypeError("plain string UTF-8 byte ceiling exceeded")
            return current
        if type(current) is bytes:
            if len(current) > MAX_PLAIN_BYTES_LENGTH:
                raise TypeError("plain bytes ceiling exceeded")
            return current
        if type(current) not in {list, tuple, dict}:
            raise TypeError("only exact builtin plain data is accepted")
        if len(current) > MAX_PLAIN_CONTAINER_ITEMS:
            raise TypeError("plain container item ceiling exceeded")
        identity = id(current)
        if identity in active_container_ids:
            raise TypeError("cyclic plain data forbidden")
        active_container_ids.add(identity)
        try:
            if type(current) is list:
                return [clone(item, depth + 1) for item in current]
            if type(current) is tuple:
                return tuple(clone(item, depth + 1) for item in current)
            result: dict[str, Any] = {}
            for key, item in current.items():
                if type(key) is not str:
                    raise TypeError("plain record keys must be exact strings")
                cloned_key = clone(key, depth + 1)
                result[cloned_key] = clone(item, depth + 1)
            return result
        finally:
            active_container_ids.remove(identity)

    return clone(value, 0)


def _strict_plain_equal(left: Any, right: Any) -> bool:
    """Compare already-cloned exact builtin data with type identity at every node."""

    if type(left) is not type(right):
        return False
    if type(left) is dict:
        if set(left) != set(right):
            return False
        return all(_strict_plain_equal(left[key], right[key]) for key in left)
    if type(left) in {list, tuple}:
        return len(left) == len(right) and all(
            _strict_plain_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    return bool(left == right)


class ReconnaissanceError(RuntimeError):
    """Base class for deterministic, in-memory qualification refusals."""

    code = "UNCLASSIFIED_FAILURE"
    terminal_state = "TERMINAL_PROTOCOL_VIOLATION_NO_RETRY"

    def __init__(
        self,
        message: str = "",
        *,
        evidence: dict[str, Any] | None = None,
        captured_head: bytes = b"",
        captured_body: bytes = b"",
        decoded_body: bytes = b"",
    ) -> None:
        super().__init__(message)
        if evidence is None:
            self.evidence = {}
        elif type(evidence) is dict:
            self.evidence = _clone_plain(evidence)
        else:
            raise TypeError("error evidence must be an exact builtin dict")
        if type(captured_head) is not bytes:
            raise TypeError("captured_head must be exact bytes")
        if type(captured_body) is not bytes:
            raise TypeError("captured_body must be exact bytes")
        if type(decoded_body) is not bytes:
            raise TypeError("decoded_body must be exact bytes")
        self.captured_head = captured_head
        self.captured_body = captured_body
        self.decoded_body = decoded_body


class AdmissionError(ReconnaissanceError):
    code = "ADMISSION_HOLD"


class ProtocolError(ReconnaissanceError):
    code = "PROTOCOL_VIOLATION"
    terminal_state = "TERMINAL_PROTOCOL_VIOLATION_NO_RETRY"


class ScopeError(ReconnaissanceError):
    code = "SCOPE_VIOLATION"
    terminal_state = "TERMINAL_SCOPE_VIOLATION_NO_RETRY"


class ContentError(ReconnaissanceError):
    code = "TRANSPORT_OR_CONTENT_NO_GO"
    terminal_state = "TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY"


class TransportError(ReconnaissanceError):
    code = "TRANSPORT_FAILURE"
    terminal_state = "TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY"


@dataclass(frozen=True)
class Operation:
    ordinal: int
    operation_id: str
    domain_id: str
    url: str
    host: str
    request_target: str

    @property
    def request_bytes(self) -> bytes:
        lines = (
            f"GET {self.request_target} HTTP/1.1",
            f"Host: {self.host}",
            f"User-Agent: {USER_AGENT}",
            f"Accept: {ACCEPT}",
            "Accept-Encoding: identity",
            "Cache-Control: no-cache",
            "Pragma: no-cache",
            "Connection: close",
            "",
            "",
        )
        return "\r\n".join(lines).encode("ascii")

    @property
    def exact_request_sha256(self) -> str:
        return _sha256(self.request_bytes)


_OPERATION_LITERALS = (
    (
        0,
        "SB2-PUBLIC-ROOT-PHYSIONET-000",
        "physionet-challenge-2012",
        "https://physionet.org/content/challenge-2012/1.0.0/",
        "physionet.org",
        "/content/challenge-2012/1.0.0/",
    ),
    (
        1,
        "SB2-PUBLIC-ROOT-UCI-001",
        "online-retail-ii",
        "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
        "archive.ics.uci.edu",
        "/dataset/502/online+retail+ii",
    ),
)


def _new_operation(row_ordinal: int) -> Operation:
    return Operation(*_OPERATION_LITERALS[row_ordinal])


@dataclass(frozen=True)
class InertTranscript:
    """Immutable plain data; every event is explicitly simulated."""

    intent_utc: str
    started_utc: str
    finished_utc: str
    simulated_resolver_host: str
    simulated_resolver_port: int
    simulated_resolver_results: tuple[str, ...]
    simulated_selected_address: str
    simulated_socket_instance_count: int
    simulated_connect_attempt_count: int
    simulated_tls_wrap_count: int
    simulated_send_attempt_count: int
    simulated_emitted_request_bytes: bytes | None
    supplied_tls_version: str | None
    supplied_alpn: str | None
    supplied_cipher_name: str | None
    supplied_cipher_protocol: str | None
    supplied_cipher_bits: int | None
    supplied_peer_certificate_bytes: bytes | None
    response_chunks: tuple[bytes, ...]
    injected_failure_stage: str | None


@dataclass(frozen=True)
class _ResponseResult:
    status_code: int
    protocol: str
    framing: str
    framing_complete: bool
    header_diagnostics_complete: bool
    content_type_header_count: int
    content_type_raw_values: list[str]
    normalized_media_type: str
    content_disposition_header_count: int
    content_disposition_raw_values: list[str]
    location_header_count: int
    location_raw_values: list[str]
    content_encoding_header_count: int
    content_encoding_raw_values: list[str]
    content_encoding_normalized_values: list[str]
    transfer_encoding_header_count: int
    transfer_encoding_raw_values: list[str]
    transfer_encoding_normalized_values: list[str]
    transfer_encoding_semantics_valid: bool
    dechunk_complete: bool
    decoded_entity_body_receipt_complete: bool
    raw_head: bytes
    raw_body: bytes
    decoded_body: bytes
    body_utf8_valid: bool
    forbidden_magic_detected: bool
    forbidden_magic_prefix_matches: list[str]
    challenge_page_detected: bool
    rejection_substring_matches: list[str]
    title_classifier_matches: list[str]
    login_wall_detected: bool
    consent_wall_detected: bool
    robot_block_detected: bool
    error_page_detected: bool
    raw_status_start: int
    raw_status_end_exclusive: int
    raw_headers_start: int
    raw_headers_end_exclusive: int


ALLOWED_MEDIA_TYPES = frozenset(
    {"text/html", "application/xhtml+xml", "text/plain"}
)
FORBIDDEN_MAGIC_PREFIXES = tuple(
    bytes.fromhex(value)
    for value in (
        "1f8b",
        "504b0304",
        "504b0506",
        "425a68",
        "fd377a585a00",
        "377abcaf271c",
        "526172211a0700",
        "526172211a070100",
        "50415231",
        "894844460d0a1a0a",
        "53514c69746520666f726d6174203300",
        "43444601",
        "43444602",
        "4152524f5731",
        "8002",
        "8003",
        "8004",
        "8005",
    )
)
CHALLENGE_MARKERS = (
    b'type="password"',
    b"type='password'",
    b'name="password"',
    b"name='password'",
    b"captcha",
    b"cf-chl-",
    b"cloudflare ray id",
    b"enable javascript and cookies",
    b"verify you are human",
    b"checking your browser",
    b"just a moment",
    b"attention required",
    b"are you a robot",
    b"authentication required",
    b"consent required",
    b"log in",
    b"login required",
    b"sign in",
    b"robot check",
    b"access denied",
    b"temporarily unavailable",
    b"internal server error",
    b"error 403",
    b"error 404",
    b"error 500",
)

ARTIFACT_SUFFIXES = (
    ("intent", ".intent.json"),
    ("raw_request", ".raw-request.bin"),
    ("raw_response_head", ".raw-response-head.bin"),
    ("raw_transfer_body", ".raw-transfer-body.bin"),
    ("raw_metadata", ".raw-metadata.bin"),
    ("raw_stderr", ".raw-stderr.bin"),
    ("decoded_entity_body", ".decoded-entity-body.bin"),
    ("outcome", ".outcome.json"),
)

OUTCOME_DIAGNOSTIC_FIELD_TYPES = (
    ("status_code", "EXACT_INT_OR_NULL"),
    ("protocol", "EXACT_STRING_OR_NULL"),
    ("framing", "EXACT_STRING_OR_NULL"),
    ("framing_complete", "EXACT_BOOL"),
    ("header_diagnostics_complete", "EXACT_BOOL"),
    ("content_type_header_count", "EXACT_INT_OR_NULL"),
    ("content_type_raw_values", "EXACT_LIST_OF_EXACT_STRING"),
    ("normalized_media_type", "EXACT_STRING_OR_NULL"),
    ("content_disposition_header_count", "EXACT_INT_OR_NULL"),
    ("content_disposition_raw_values", "EXACT_LIST_OF_EXACT_STRING"),
    ("location_header_count", "EXACT_INT_OR_NULL"),
    ("location_raw_values", "EXACT_LIST_OF_EXACT_STRING"),
    ("content_encoding_header_count", "EXACT_INT_OR_NULL"),
    ("content_encoding_raw_values", "EXACT_LIST_OF_EXACT_STRING"),
    ("content_encoding_normalized_values", "EXACT_LIST_OF_EXACT_STRING"),
    ("transfer_encoding_header_count", "EXACT_INT_OR_NULL"),
    ("transfer_encoding_raw_values", "EXACT_LIST_OF_EXACT_STRING"),
    ("transfer_encoding_normalized_values", "EXACT_LIST_OF_EXACT_STRING"),
    ("transfer_encoding_semantics_valid", "EXACT_BOOL"),
    ("dechunk_complete", "EXACT_BOOL"),
    ("decoded_entity_body_receipt_complete", "EXACT_BOOL"),
    ("body_utf8_valid", "EXACT_BOOL"),
    ("forbidden_magic_detected", "EXACT_BOOL"),
    ("forbidden_magic_prefix_matches", "EXACT_LIST_OF_EXACT_STRING"),
    ("challenge_page_detected", "EXACT_BOOL"),
    ("login_wall_detected", "EXACT_BOOL"),
    ("consent_wall_detected", "EXACT_BOOL"),
    ("robot_block_detected", "EXACT_BOOL"),
    ("error_page_detected", "EXACT_BOOL"),
    ("rejection_substring_matches", "EXACT_LIST_OF_EXACT_STRING"),
    ("title_classifier_matches", "EXACT_LIST_OF_EXACT_STRING"),
    ("raw_status_start", "EXACT_INT_OR_NULL"),
    ("raw_status_end_exclusive", "EXACT_INT_OR_NULL"),
    ("raw_headers_start", "EXACT_INT_OR_NULL"),
    ("raw_headers_end_exclusive", "EXACT_INT_OR_NULL"),
    ("body_truncated", "EXACT_BOOL"),
)


def _sha256(raw: bytes) -> str:
    if type(raw) is not bytes:
        raise TypeError("hash input must be exact bytes")
    return hashlib.sha256(raw).hexdigest()


def _canonical_no_lf(value: Any) -> bytes:
    try:
        return json.dumps(
            _clone_plain(value),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AdmissionError("non-canonical value") from exc


def _canonical(value: Any) -> bytes:
    return _canonical_no_lf(value) + b"\n"


def _self_digest(record: dict[str, Any]) -> str:
    if type(record) is not dict:
        raise TypeError("self-digest record must be an exact builtin dict")
    clone = _clone_plain(record)
    clone["record_sha256"] = None
    return _sha256(_canonical(clone))


OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256 = _sha256(
    _canonical_no_lf(
        [
            {"field": field, "exact_type": exact_type}
            for field, exact_type in OUTCOME_DIAGNOSTIC_FIELD_TYPES
        ]
    )
)


def _require_exact_int(value: Any, label: str, *, minimum: int = 0) -> int:
    if (
        type(value) is not int
        or value < minimum
        or value.bit_length() > MAX_PLAIN_INTEGER_BITS
    ):
        raise AdmissionError(f"{label}: exact int >= {minimum} required")
    return value


def _require_string(value: Any, label: str) -> str:
    if type(value) is not str or not value:
        raise AdmissionError(f"{label}: exact nonempty string required")
    if len(value) > MAX_PLAIN_STRING_CODEPOINTS:
        raise AdmissionError(f"{label}: string codepoint ceiling exceeded")
    try:
        encoded_length = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise AdmissionError(f"{label}: valid UTF-8 string required") from exc
    if encoded_length > MAX_PLAIN_STRING_UTF8_BYTES:
        raise AdmissionError(f"{label}: string UTF-8 byte ceiling exceeded")
    return value


def _require_hex64(value: Any, label: str) -> str:
    if type(value) is not str or HEX64.fullmatch(value) is None:
        raise AdmissionError(f"{label}: lowercase hex64 required")
    return value


def _parse_utc(value: Any, label: str) -> _datetime.datetime:
    text = _require_string(value, label)
    if RFC3339_UTC.fullmatch(text) is None:
        raise AdmissionError(f"{label}: canonical second-resolution UTC required")
    try:
        return _datetime.datetime(
            int(text[0:4]),
            int(text[5:7]),
            int(text[8:10]),
            int(text[11:13]),
            int(text[14:16]),
            int(text[17:19]),
            tzinfo=_datetime.timezone.utc,
        )
    except ValueError as exc:
        raise AdmissionError(f"{label}: invalid UTC timestamp") from exc


def _operation(row_ordinal: Any) -> Operation:
    if type(row_ordinal) is not int or row_ordinal not in (0, 1):
        raise AdmissionError("row_ordinal must be exact int 0 or 1")
    return _new_operation(row_ordinal)


def _operation_record(operation: Operation) -> dict[str, Any]:
    return {
        "ordinal": operation.ordinal,
        "operation_id": operation.operation_id,
        "domain_id": operation.domain_id,
        "url": operation.url,
        "scheme": "https",
        "host": operation.host,
        "port": 443,
        "request_target": operation.request_target,
        "method": "GET",
        "http_version": "HTTP/1.1",
        "exact_request_bytes": len(operation.request_bytes),
        "exact_request_sha256": operation.exact_request_sha256,
        "request_body_bytes": 0,
        "request_body_sha256": _sha256(b""),
        "future_attempt_limit": 1,
        "future_retry_limit": 0,
        "future_redirect_limit": 0,
    }


def _operation_roster_record() -> list[dict[str, Any]]:
    return [_operation_record(_new_operation(ordinal)) for ordinal in (0, 1)]


OPERATION_ROSTER_SHA256 = _sha256(_canonical_no_lf(_operation_roster_record()))


def _custody_plan_record(operation: Operation) -> dict[str, Any]:
    return {
        "schema_version": "heterodiff-sb2-public-root-future-custody-plan-v2",
        "row_ordinal": operation.ordinal,
        "operation_id": operation.operation_id,
        "operational_row_directory_basename": None,
        "non_authoritative_row_label": f"row-{operation.ordinal:03d}",
        "artifacts": [
            {
                "role": role,
                "logical_name": f"row-{operation.ordinal:03d}{suffix}",
                "future_create_flags": [
                    "O_WRONLY", "O_CREAT", "O_EXCL", "O_NOFOLLOW"
                ],
                "future_mode_octal": "0600",
                "future_regular_file_required": True,
                "future_nlink_required": 1,
                "future_file_fsync_required": True,
                "future_directory_fsync_required": True,
            }
            for role, suffix in ARTIFACT_SUFFIXES
        ],
        "filesystem_materialized": False,
        "dirfd_mechanics_implemented": False,
        "exclusive_creation_qualified": False,
        "nofollow_qualified": False,
        "durability_qualified": False,
        "path_reopen_performed": False,
        "filesystem_effect": 0,
    }


def custody_plan(row_ordinal: int) -> dict[str, Any]:
    """Return a detached future custody plan; materialize nothing."""

    return _clone_plain(_custody_plan_record(_operation(row_ordinal)))


def _executor_contract_record() -> dict[str, Any]:
    return {
    "schema_version": EXECUTOR_SCHEMA_VERSION,
    "package_role": PACKAGE_ROLE,
    "operation_roster": _operation_roster_record(),
    "operation_roster_sha256": OPERATION_ROSTER_SHA256,
    "exact_runtime_admitted": EXACT_RUNTIME_ADMITTED,
    "fetch_eligible": FETCH_ELIGIBLE,
    "runtime_hold_reason": RUNTIME_HOLD_REASON,
    "general_url_input": False,
    "production_execution_entrypoint": False,
    "qualification_input": "EXACT_IMMUTABLE_INERT_TRANSCRIPT",
    "caller_supplied_callable_surface": False,
    "row1_prior_input": (
        "EXACT_ROW0_INERT_TRANSCRIPT_PLUS_CLAIMED_FULL_ROW0_OUTCOME"
    ),
    "row1_prior_validation": (
        "FULL_CONTEXTUAL_RECOMPUTATION_THEN_STRICT_RECURSIVE_EQUALITY"
    ),
    "outcome_diagnostic_field_types": [
        {"field": field, "exact_type": exact_type}
        for field, exact_type in OUTCOME_DIAGNOSTIC_FIELD_TYPES
    ],
    "outcome_diagnostic_field_types_sha256": (
        OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256
    ),
    "effects": {
        "filesystem_reads": 0,
        "filesystem_writes": 0,
        "directory_creations": 0,
        "network_calls": 0,
        "process_calls": 0,
        "clock_reads": 0,
        "randomness_reads": 0,
        "entropy_actions": 0,
        "tracker_edits": 0,
        "data_actions": 0,
        "scientific_actions": 0,
    },
    "operational_bindings": {
        "machine_raw_sha256": None,
        "machine_record_sha256": None,
        "package_aggregate_sha256": None,
        "executor_raw_sha256": None,
        "environment_manifest_sha256": None,
        "operational_admission_receipt_sha256": None,
        "operational_qualification_receipt_sha256": None,
        "operational_independent_go_receipt_sha256": None,
        "operational_fresh_authority_receipt_sha256": None,
        "operational_custody_root_path": None,
        "custody_root_identity_sha256": None,
        "operational_row_directory_basename": None,
    },
    "future_network_specification_not_executable": {
        "resolver_calls": 1,
        "socket_instances": 1,
        "connect_calls": 1,
        "tls_wrap_calls": 1,
        "request_send_calls": 1,
        "request_count": 1,
        "retries": 0,
        "redirects": 0,
        "tls_minimum": "TLSv1.2",
        "tls_maximum": "TLSv1.3",
        "alpn_required": "http/1.1",
        "certificate_verification_required": True,
        "hostname_verification_required": True,
        "authentication": False,
        "cookies": False,
        "forms": False,
        "subresources": False,
        "child_links": False,
        "automatic_decompression": False,
    },
    "limits": {
        "max_status_bytes": MAX_STATUS_BYTES,
        "max_header_bytes": MAX_HEADER_BYTES,
        "max_head_bytes": MAX_HEAD_BYTES,
        "max_encoded_body_bytes": MAX_ENCODED_BODY_BYTES,
        "max_decoded_body_bytes": MAX_DECODED_BODY_BYTES,
        "max_total_response_bytes": MAX_TOTAL_RESPONSE_BYTES,
        "max_header_count": MAX_HEADER_COUNT,
        "max_header_line_bytes": MAX_HEADER_LINE_BYTES,
        "max_certificate_bytes": MAX_CERTIFICATE_BYTES,
        "max_transcript_chunk_count": MAX_TRANSCRIPT_CHUNK_COUNT,
        "max_plain_clone_depth": MAX_PLAIN_CLONE_DEPTH,
        "max_plain_clone_nodes": MAX_PLAIN_CLONE_NODES,
        "max_plain_container_items": MAX_PLAIN_CONTAINER_ITEMS,
        "max_plain_string_codepoints": MAX_PLAIN_STRING_CODEPOINTS,
        "max_plain_string_utf8_bytes": MAX_PLAIN_STRING_UTF8_BYTES,
        "max_plain_bytes_length": MAX_PLAIN_BYTES_LENGTH,
        "max_plain_integer_bits": MAX_PLAIN_INTEGER_BITS,
        "max_plain_float_abs": MAX_PLAIN_FLOAT_ABS,
    },
    "future_custody": {
        "plans": [
            _custody_plan_record(_new_operation(ordinal)) for ordinal in (0, 1)
        ],
        "filesystem_materialized": False,
        "dirfd_mechanics_implemented": False,
        "o_excl_nofollow_implemented": False,
        "file_and_directory_fsync_implemented": False,
        "retained_descriptor_revalidation_implemented": False,
        "forward_hash_chain_modeled_in_memory": True,
        "durable_outcome_append_implemented": False,
        "durable_outcome_link_qualified": False,
    },
    "response_predicates": {
        "status_code": 200,
        "protocol": "HTTP/1.1",
        "global_terminal_precedence": (
            "COMPLETE_PROTOCOL_AND_FRAMING_VALIDATION_OF_ALL_SUPPLIED_BYTES_"
            "BEFORE_SCOPE_STATUS_OR_CONTENT_CLASSIFICATION"
        ),
        "content_type_header_count": 1,
        "allowed_media_types": sorted(ALLOWED_MEDIA_TYPES),
        "content_disposition_header_count": 0,
        "location_header_count": 0,
        "content_encoding_header_count_allowed": [0, 1],
        "content_encoding_normalized_values_allowed": [[], ["identity"]],
        "transfer_encoding_header_count_allowed": [0, 1],
        "transfer_encoding_normalized_values_allowed": [[], ["chunked"]],
        "transfer_encoding_semantics_valid_required": True,
        "chunk_extensions": False,
        "chunk_trailers": False,
        "connection_close_requires_exactly_one_final_inert_eof_event": True,
        "dechunk_complete_required_when_chunked": True,
        "decoded_entity_body_receipt_complete_required": True,
        "body_truncated_semantics": (
            "TRUE_IFF_SUPPLIED_BODY_OR_DECODED_ENTITY_BYTES_WERE_NOT_FULLY_"
            "RETAINED_DUE_TO_A_FROZEN_BYTE_CEILING"
        ),
        "body_utf8_valid_semantics": (
            "TRUE_AFTER_SUCCESSFUL_UTF8_DECODE_EVEN_IF_A_LATER_SCOPE_STATUS_"
            "OR_CONTENT_CLASSIFIER_REJECTS"
        ),
        "challenge_login_consent_robot_error_allowed": False,
        "archive_or_data_magic_allowed": False,
        "page_text_normalization": (
            "UTF8_DECODE_THEN_UNICODE_CASEFOLD_THEN_COLLAPSE_ASCII_WHITESPACE_RUNS_THEN_STRIP"
        ),
        "rejection_substrings": [
            marker.decode("ascii") for marker in CHALLENGE_MARKERS
        ],
        "rejection_substring_matches_semantics": (
            "SORTED_UNIQUE_EXACT_MEMBERS_OF_REJECTION_SUBSTRINGS_ONLY"
        ),
        "magic_diagnostic_field": "forbidden_magic_prefix_matches",
        "magic_diagnostic_allowed_values": [
            prefix.hex() for prefix in FORBIDDEN_MAGIC_PREFIXES
        ],
        "title_classifier_diagnostic_field": "title_classifier_matches",
        "title_classifier_allowed_values": [
            "captcha", "challenge", "denied", "error", "login", "sign in"
        ],
    },
    "qualification_success_state": (
        "QUALIFICATION_ONLY_TERMINAL_INERT_ROOT_PAGE_TRANSCRIPT_ACCEPTED_NO_NETWORK"
    ),
    }


EXECUTOR_CONTRACT_SHA256 = _sha256(_canonical_no_lf(_executor_contract_record()))


def executor_contract() -> dict[str, Any]:
    """Return a detached inert copy of the frozen contract."""

    return _executor_contract_record()


def operation_spec(row_ordinal: int) -> dict[str, Any]:
    """Return a fresh exact operation specification."""

    return _operation_record(_operation(row_ordinal))


def exact_request_bytes(row_ordinal: int) -> bytes:
    """Return the frozen request bytes for one of the two literal rows."""

    return _operation(row_ordinal).request_bytes


def _parse_content_type(value: str) -> tuple[str, str]:
    if not value or "," in value or any(
        ord(character) < 32 or ord(character) >= 127 for character in value
    ):
        raise ScopeError("invalid Content-Type")
    parts = [part.strip() for part in value.split(";")]
    media = parts[0].lower()
    if media not in ALLOWED_MEDIA_TYPES:
        raise ScopeError("media type outside root-page allowlist")
    seen: set[str] = set()
    for part in parts[1:]:
        if "=" not in part:
            raise ScopeError("invalid Content-Type parameter")
        name, parameter = (item.strip() for item in part.split("=", 1))
        name = name.lower()
        if TOKEN.fullmatch(name) is None or name in seen or name != "charset":
            raise ScopeError("unsupported or duplicate Content-Type parameter")
        seen.add(name)
        if len(parameter) >= 2 and parameter[0] == parameter[-1] == '"':
            parameter = parameter[1:-1]
        if parameter.lower() not in {"utf-8", "utf8", "us-ascii"}:
            raise ScopeError("unsupported charset")
    return value, media


def _parse_headers(head: bytes) -> tuple[int, dict[str, list[str]]]:
    """Parse all head-level protocol structure without scope classification."""

    if type(head) is not bytes:
        raise TypeError("head must be exact bytes")
    if len(head) > MAX_HEAD_BYTES or not head.endswith(b"\r\n\r\n"):
        raise ProtocolError("response head framing invalid")
    split = head.find(b"\r\n")
    if split < 0:
        raise ProtocolError("status terminator missing")
    status_raw = head[: split + 2]
    headers_raw = head[split + 2 :]
    if len(status_raw) > MAX_STATUS_BYTES or len(headers_raw) > MAX_HEADER_BYTES:
        raise ProtocolError("status or header byte ceiling exceeded")
    match = STATUS_LINE.fullmatch(status_raw)
    if match is None:
        raise ProtocolError("status line is not exact HTTP/1.1")
    status_code = int(match.group(1))
    lines = headers_raw[:-4].split(b"\r\n") if headers_raw != b"\r\n" else []
    if len(lines) > MAX_HEADER_COUNT:
        raise ProtocolError("header count ceiling exceeded")
    values: dict[str, list[str]] = {}
    for line in lines:
        if not line or len(line) > MAX_HEADER_LINE_BYTES:
            raise ProtocolError("empty or oversized header line")
        if line[:1] in (b" ", b"\t") or b":" not in line:
            raise ProtocolError("obsolete folding or missing colon")
        name_raw, value_raw = line.split(b":", 1)
        if HEADER_NAME.fullmatch(name_raw) is None:
            raise ProtocolError("invalid header name")
        if any(byte < 32 and byte != 9 for byte in value_raw) or 127 in value_raw:
            raise ProtocolError("prohibited header control byte")
        if any(byte >= 128 for byte in value_raw):
            raise ProtocolError("non-ASCII header value forbidden")
        name = name_raw.decode("ascii").lower()
        value = value_raw.decode("ascii").strip(" \t")
        values.setdefault(name, []).append(value)

    lengths = values.get("content-length", [])
    transfers = values.get("transfer-encoding", [])
    connections = values.get("connection", [])
    if len(lengths) > 1:
        raise ProtocolError("multiple Content-Length forbidden")
    if lengths and re.fullmatch(r"0|[1-9][0-9]*", lengths[0]) is None:
        raise ProtocolError("invalid Content-Length")
    if lengths:
        maximum_content_length = str(MAX_ENCODED_BODY_BYTES)
        if (
            len(lengths[0]) > len(maximum_content_length)
            or (
                len(lengths[0]) == len(maximum_content_length)
                and lengths[0] > maximum_content_length
            )
        ):
            raise ProtocolError("Content-Length exceeds frozen body ceiling")
    if len(transfers) > 1:
        raise ProtocolError("multiple Transfer-Encoding forbidden")
    if transfers and transfers[0].lower() != "chunked":
        raise ProtocolError("unsupported Transfer-Encoding")
    if lengths and transfers:
        raise ProtocolError("ambiguous response framing")
    if len(connections) > 1:
        raise ProtocolError("multiple Connection headers forbidden")
    if 100 <= status_code <= 199:
        raise ProtocolError("interim response heads forbidden")

    return status_code, values


def _classify_header_scope(
    values: dict[str, list[str]],
) -> tuple[str, str]:
    """Apply header scope only after complete response framing is proved."""

    for forbidden in (
        "location",
        "www-authenticate",
        "proxy-authenticate",
        "set-cookie",
        "refresh",
        "content-disposition",
    ):
        if forbidden in values:
            raise ScopeError(f"forbidden response header: {forbidden}")
    if len(values.get("content-type", [])) != 1:
        raise ScopeError("exactly one Content-Type required")
    content_type_raw, media_type = _parse_content_type(values["content-type"][0])
    encodings = values.get("content-encoding", [])
    if len(encodings) > 1 or (encodings and encodings[0].lower() != "identity"):
        raise ScopeError("nonidentity or ambiguous Content-Encoding")
    connections = values.get("connection", [])
    if connections and connections[0].lower() != "close":
        raise ScopeError("response connection mode must be close when stated")
    return content_type_raw, media_type


class _ChunkDecoder:
    def __init__(self) -> None:
        self.buffer = bytearray()
        self.decoded = bytearray()
        self.remaining: int | None = None
        self.done = False

    def feed(self, raw: bytes) -> None:
        if type(raw) is not bytes:
            raise TypeError("chunk input must be exact bytes")
        if self.done and raw:
            raise ProtocolError("bytes after terminal chunk")
        self.buffer.extend(raw)
        while True:
            if self.remaining is None:
                end = self.buffer.find(b"\r\n")
                if end < 0:
                    if len(self.buffer) > MAX_HEADER_LINE_BYTES:
                        raise ProtocolError("chunk-size line too long")
                    return
                line = bytes(self.buffer[:end])
                del self.buffer[: end + 2]
                if (
                    not line
                    or b";" in line
                    or re.fullmatch(rb"[0-9A-Fa-f]+", line) is None
                ):
                    raise ProtocolError("invalid or extended chunk-size line")
                size = int(line, 16)
                if size == 0:
                    if len(self.buffer) < 2:
                        self.remaining = 0
                        return
                    if self.buffer[:2] != b"\r\n":
                        raise ProtocolError("chunk trailers forbidden")
                    del self.buffer[:2]
                    self.done = True
                    if self.buffer:
                        raise ProtocolError("bytes after terminal chunk")
                    return
                self.remaining = size
            elif self.remaining == 0:
                if len(self.buffer) < 2:
                    return
                if self.buffer[:2] != b"\r\n":
                    raise ProtocolError("chunk trailers forbidden")
                del self.buffer[:2]
                self.done = True
                if self.buffer:
                    raise ProtocolError("bytes after terminal chunk")
                return
            else:
                needed = self.remaining + 2
                if len(self.buffer) < needed:
                    return
                self.decoded.extend(self.buffer[: self.remaining])
                if self.buffer[self.remaining : needed] != b"\r\n":
                    raise ProtocolError("chunk data terminator missing")
                del self.buffer[:needed]
                self.remaining = None

    def finish(self) -> bytes:
        if not self.done or self.buffer:
            raise ProtocolError("incomplete chunked body")
        return bytes(self.decoded)


def _validate_body_protocol(body: bytes) -> None:
    """Reject a second response head before any scope/content decision."""

    stripped = body.lstrip(b" \t\r\n\f\v")
    if stripped[:7].lower() == b"http/1.":
        raise ProtocolError("multiple response heads forbidden", decoded_body=body)


def _first_title_content(lowered: bytes) -> bytes | None:
    """Return the first syntactically bounded title using linear byte scans."""

    if type(lowered) is not bytes:
        raise TypeError("lowered page bytes must be exact bytes")
    ascii_whitespace = b" \t\r\n\f\v"
    opening_cursor = 0
    content_start: int | None = None
    while True:
        opening = lowered.find(b"<title", opening_cursor)
        if opening < 0:
            return None
        name_end = opening + len(b"<title")
        if name_end >= len(lowered):
            return None
        following = lowered[name_end]
        if following == ord(">"):
            content_start = name_end + 1
            break
        if following not in ascii_whitespace:
            opening_cursor = name_end
            continue
        opening_end = lowered.find(b">", name_end + 1)
        if opening_end < 0:
            return None
        content_start = opening_end + 1
        break

    closing_cursor = content_start
    while True:
        closing = lowered.find(b"</title", closing_cursor)
        if closing < 0:
            return None
        suffix = closing + len(b"</title")
        while suffix < len(lowered) and lowered[suffix] in ascii_whitespace:
            suffix += 1
        if suffix < len(lowered) and lowered[suffix] == ord(">"):
            return lowered[content_start:closing]
        closing_cursor = closing + len(b"</title")


def _validate_body(body: bytes, media_type: str) -> dict[str, Any]:
    if type(body) is not bytes:
        raise TypeError("body must be exact bytes")
    if not body:
        raise ContentError("empty root page")
    matches_magic = sorted(
        {prefix.hex() for prefix in FORBIDDEN_MAGIC_PREFIXES if body.startswith(prefix)}
    )
    if matches_magic:
        raise ScopeError(
            "archive or data magic prefix detected",
            evidence={
                "forbidden_magic_detected": True,
                "forbidden_magic_prefix_matches": matches_magic,
                "rejection_substring_matches": [],
                "title_classifier_matches": [],
            },
            decoded_body=body,
        )
    if body.startswith((b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")):
        raise ContentError("BOM forbidden", decoded_body=body)
    if any(
        byte == 0 or (byte < 32 and byte not in (9, 10, 13)) or byte == 127
        for byte in body
    ):
        raise ContentError("prohibited body control byte", decoded_body=body)
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContentError("body is not UTF-8", decoded_body=body) from exc
    body_evidence = {
        "body_utf8_valid": True,
        "forbidden_magic_detected": False,
        "forbidden_magic_prefix_matches": [],
        "challenge_page_detected": False,
        "rejection_substring_matches": [],
        "title_classifier_matches": [],
        "login_wall_detected": False,
        "consent_wall_detected": False,
        "robot_block_detected": False,
        "error_page_detected": False,
    }
    normalized_text = re.sub(
        r"[ \t\r\n\f\v]+", " ", text.casefold()
    ).strip()
    lowered = normalized_text.encode("utf-8")
    matches = sorted(
        {marker.decode("ascii") for marker in CHALLENGE_MARKERS if marker in lowered}
    )
    login = any(
        value in matches
        for value in (
            'type="password"',
            "type='password'",
            'name="password"',
            "name='password'",
            "log in",
            "login required",
            "sign in",
        )
    )
    consent = any("consent" in value for value in matches)
    robot = any(
        value in matches
        for value in (
            "captcha",
            "cf-chl-",
            "cloudflare ray id",
            "enable javascript and cookies",
            "verify you are human",
            "checking your browser",
            "just a moment",
            "attention required",
            "are you a robot",
            "robot check",
        )
    )
    error_page = any(
        value in matches
        for value in (
            "access denied",
            "temporarily unavailable",
            "internal server error",
            "error 403",
            "error 404",
            "error 500",
        )
    )
    title = _first_title_content(lowered)
    title_tokens: list[str] = []
    if title is not None:
        title_tokens = sorted(
            token.decode("ascii")
            for token in (
                b"login", b"sign in", b"error", b"denied", b"challenge", b"captcha"
            )
            if token in title
        )
    if title_tokens:
        login = login or b"login" in title or b"sign in" in title
        error_page = error_page or b"error" in title or b"denied" in title
        robot = robot or b"challenge" in title or b"captcha" in title
    if matches or title_tokens:
        body_evidence.update(
            {
                "challenge_page_detected": True,
                "login_wall_detected": login,
                "consent_wall_detected": consent,
                "robot_block_detected": robot,
                "error_page_detected": error_page,
                "rejection_substring_matches": matches,
                "title_classifier_matches": title_tokens,
            }
        )
        raise ScopeError(
            "login, consent, challenge, robot, or error page detected",
            evidence=body_evidence,
            decoded_body=body,
        )
    if media_type in {"text/html", "application/xhtml+xml"} and not (
        b"<html" in lowered or b"<!doctype html" in lowered
    ):
        raise ContentError(
            "HTML media type lacks root document marker",
            evidence=body_evidence,
            decoded_body=body,
        )
    return body_evidence


def _receive_response(response_chunks: tuple[bytes, ...]) -> _ResponseResult:
    """Parse supplied TLS-application bytes without invoking any byte source."""

    if type(response_chunks) is not tuple:
        raise ProtocolError("response_chunks must be an exact bytes tuple")
    if len(response_chunks) > MAX_TRANSCRIPT_CHUNK_COUNT:
        raise ProtocolError("response chunk count ceiling exceeded")
    if any(type(chunk) is not bytes for chunk in response_chunks):
        raise ProtocolError("response_chunks must be an exact bytes tuple")
    wire = bytearray()
    total_overflow = False
    nonterminal_eof = False
    terminal_eof = bool(response_chunks) and response_chunks[-1] == b""
    eof_event_count = 0
    retention_limit = MAX_TOTAL_RESPONSE_BYTES + 1
    for ordinal, chunk in enumerate(response_chunks):
        if chunk == b"":
            eof_event_count += 1
            if ordinal != len(response_chunks) - 1:
                nonterminal_eof = True
            continue
        room = max(0, retention_limit - len(wire))
        wire.extend(chunk[:room])
        if len(chunk) > room:
            total_overflow = True
    total_overflow = total_overflow or len(wire) > MAX_TOTAL_RESPONSE_BYTES

    wire_bytes = bytes(wire)
    terminator = wire_bytes.find(b"\r\n\r\n")
    if terminator < 0:
        first_line = wire_bytes.find(b"\r\n")
        if first_line < 0 and len(wire_bytes) > MAX_STATUS_BYTES:
            raise ProtocolError(
                "status byte ceiling exceeded",
                captured_head=wire_bytes[:MAX_STATUS_BYTES],
            )
        if first_line >= 0 and first_line + 2 > MAX_STATUS_BYTES:
            raise ProtocolError(
                "status byte ceiling exceeded",
                captured_head=wire_bytes[:MAX_STATUS_BYTES],
            )
        if len(wire_bytes) > MAX_HEAD_BYTES:
            raise ProtocolError(
                "head byte ceiling exceeded",
                captured_head=wire_bytes[:MAX_HEAD_BYTES],
            )
        raise ProtocolError(
            "EOF before complete response head", captured_head=wire_bytes
        )

    head_end = terminator + 4
    raw_body_all = wire_bytes[head_end:]
    retained_body = raw_body_all[:MAX_ENCODED_BODY_BYTES]
    body_capture_truncated = (
        total_overflow or len(raw_body_all) > MAX_ENCODED_BODY_BYTES
    )
    capture_evidence = {"body_truncated": body_capture_truncated}
    status_end = wire_bytes.find(b"\r\n") + 2
    if status_end <= 1 or status_end > MAX_STATUS_BYTES:
        raise ProtocolError(
            "status byte ceiling exceeded",
            evidence=capture_evidence,
            captured_head=wire_bytes[:MAX_STATUS_BYTES],
            captured_body=retained_body,
        )
    if head_end > MAX_HEAD_BYTES:
        raise ProtocolError(
            "head byte ceiling exceeded",
            evidence=capture_evidence,
            captured_head=wire_bytes[:MAX_HEAD_BYTES],
            captured_body=retained_body,
        )
    if head_end - status_end > MAX_HEADER_BYTES:
        raise ProtocolError(
            "header byte ceiling exceeded",
            evidence=capture_evidence,
            captured_head=wire_bytes[: status_end + MAX_HEADER_BYTES],
            captured_body=retained_body,
        )
    head_raw = wire_bytes[:head_end]
    if nonterminal_eof:
        raise ProtocolError(
            "inert EOF marker must be terminal",
            evidence=capture_evidence,
            captured_head=head_raw,
            captured_body=retained_body,
        )
    if total_overflow:
        raise ProtocolError(
            "response transcript total byte ceiling prevents complete framing proof",
            evidence={"body_truncated": True},
            captured_head=head_raw,
            captured_body=retained_body,
        )

    try:
        status, headers = _parse_headers(head_raw)
    except ReconnaissanceError as exc:
        merged = _clone_plain(capture_evidence)
        merged.update(_clone_plain(exc.evidence))
        exc.evidence = merged
        exc.captured_head = head_raw
        exc.captured_body = retained_body
        raise
    transfer = headers.get("transfer-encoding", [])
    lengths = headers.get("content-length", [])
    if transfer:
        framing = "CHUNKED"
        expected_length = None
        decoder: _ChunkDecoder | None = _ChunkDecoder()
    elif lengths:
        try:
            expected_length = int(lengths[0])
        except (ValueError, OverflowError) as exc:
            raise ProtocolError(
                "Content-Length conversion failed after bounded validation",
                captured_head=head_raw,
                captured_body=retained_body,
            ) from exc
        framing = "CONTENT_LENGTH"
        decoder = None
    else:
        framing = "CONNECTION_CLOSE"
        expected_length = None
        decoder = None

    content_types = headers.get("content-type", [])
    content_encodings = headers.get("content-encoding", [])
    transfers = headers.get("transfer-encoding", [])
    dispositions = headers.get("content-disposition", [])
    locations = headers.get("location", [])
    parsed_evidence = {
        "response_complete": False,
        "status_code": status,
        "protocol": "HTTP/1.1",
        "framing": framing,
        "framing_complete": False,
        "header_diagnostics_complete": True,
        "content_type_header_count": len(content_types),
        "content_type_raw_values": list(content_types),
        "normalized_media_type": None,
        "content_disposition_header_count": len(dispositions),
        "content_disposition_raw_values": list(dispositions),
        "location_header_count": len(locations),
        "location_raw_values": list(locations),
        "content_encoding_header_count": len(content_encodings),
        "content_encoding_raw_values": list(content_encodings),
        "content_encoding_normalized_values": [
            value.lower() for value in content_encodings
        ],
        "transfer_encoding_header_count": len(transfers),
        "transfer_encoding_raw_values": list(transfers),
        "transfer_encoding_normalized_values": [
            value.lower() for value in transfers
        ],
        "transfer_encoding_semantics_valid": not transfers,
        "dechunk_complete": False,
        "decoded_entity_body_receipt_complete": False,
        "body_truncated": body_capture_truncated,
        "raw_status_start": 0,
        "raw_status_end_exclusive": status_end,
        "raw_headers_start": status_end,
        "raw_headers_end_exclusive": len(head_raw),
    }

    decoded = b""
    try:
        if framing == "CONNECTION_CLOSE" and (
            not terminal_eof or eof_event_count != 1
        ):
            raise ProtocolError(
                "connection-close framing requires explicit terminal inert EOF marker"
            )
        if expected_length is not None:
            if len(raw_body_all) > expected_length:
                raise ProtocolError("bytes beyond Content-Length")
            if len(raw_body_all) < expected_length:
                raise ProtocolError("Content-Length body incomplete")
            decoded = raw_body_all
        elif decoder is not None:
            decoder.feed(raw_body_all)
            decoded = decoder.finish()
        else:
            decoded = raw_body_all
        _validate_body_protocol(decoded)
        parsed_evidence["framing_complete"] = True
        parsed_evidence["transfer_encoding_semantics_valid"] = True
        parsed_evidence["dechunk_complete"] = True
        within_caps = (
            len(raw_body_all) <= MAX_ENCODED_BODY_BYTES
            and len(decoded) <= MAX_DECODED_BODY_BYTES
        )
        parsed_evidence["body_truncated"] = not within_caps
        parsed_evidence["response_complete"] = within_caps
        parsed_evidence["decoded_entity_body_receipt_complete"] = within_caps

        try:
            content_type_raw, media_type = _classify_header_scope(headers)
        except ReconnaissanceError as exc:
            merged = _clone_plain(parsed_evidence)
            merged.update(_clone_plain(exc.evidence))
            exc.evidence = merged
            raise
        parsed_evidence["normalized_media_type"] = media_type
        try:
            body_evidence = _validate_body(decoded, media_type)
        except ReconnaissanceError as exc:
            merged = _clone_plain(parsed_evidence)
            merged.update(_clone_plain(exc.evidence))
            exc.evidence = merged
            raise
        parsed_evidence.update(_clone_plain(body_evidence))
        if status != 200:
            raise ContentError("only status 200 can qualify", evidence=parsed_evidence)
        if len(raw_body_all) > MAX_ENCODED_BODY_BYTES:
            raise ContentError(
                "encoded body byte ceiling exceeded", evidence=parsed_evidence
            )
        if len(decoded) > MAX_DECODED_BODY_BYTES:
            raise ContentError(
                "decoded body ceiling exceeded", evidence=parsed_evidence
            )
    except ReconnaissanceError as exc:
        partial_decoded = bytes(decoder.decoded) if decoder is not None else decoded
        if len(partial_decoded) > MAX_DECODED_BODY_BYTES:
            parsed_evidence["body_truncated"] = True
        merged = _clone_plain(parsed_evidence)
        merged.update(_clone_plain(exc.evidence))
        exc.evidence = merged
        exc.captured_head = head_raw
        exc.captured_body = retained_body
        exc.decoded_body = partial_decoded[:MAX_DECODED_BODY_BYTES]
        raise

    return _ResponseResult(
        status_code=status,
        protocol="HTTP/1.1",
        framing=framing,
        framing_complete=True,
        header_diagnostics_complete=True,
        content_type_header_count=len(content_types),
        content_type_raw_values=list(content_types),
        normalized_media_type=media_type,
        content_disposition_header_count=len(dispositions),
        content_disposition_raw_values=list(dispositions),
        location_header_count=len(locations),
        location_raw_values=list(locations),
        content_encoding_header_count=len(content_encodings),
        content_encoding_raw_values=list(content_encodings),
        content_encoding_normalized_values=[
            value.lower() for value in content_encodings
        ],
        transfer_encoding_header_count=len(transfers),
        transfer_encoding_raw_values=list(transfers),
        transfer_encoding_normalized_values=[value.lower() for value in transfers],
        transfer_encoding_semantics_valid=True,
        dechunk_complete=True,
        decoded_entity_body_receipt_complete=True,
        raw_head=head_raw,
        raw_body=raw_body_all,
        decoded_body=decoded,
        body_utf8_valid=body_evidence["body_utf8_valid"],
        forbidden_magic_detected=body_evidence["forbidden_magic_detected"],
        forbidden_magic_prefix_matches=body_evidence["forbidden_magic_prefix_matches"],
        challenge_page_detected=body_evidence["challenge_page_detected"],
        rejection_substring_matches=body_evidence["rejection_substring_matches"],
        title_classifier_matches=body_evidence["title_classifier_matches"],
        login_wall_detected=body_evidence["login_wall_detected"],
        consent_wall_detected=body_evidence["consent_wall_detected"],
        robot_block_detected=body_evidence["robot_block_detected"],
        error_page_detected=body_evidence["error_page_detected"],
        raw_status_start=0,
        raw_status_end_exclusive=status_end,
        raw_headers_start=status_end,
        raw_headers_end_exclusive=len(head_raw),
    )


def _validate_transcript(
    transcript: InertTranscript, operation: Operation
) -> tuple[InertTranscript, dict[str, Any], str]:
    if type(transcript) is not InertTranscript:
        raise AdmissionError("exact InertTranscript required")
    transcript = InertTranscript(
        transcript.intent_utc,
        transcript.started_utc,
        transcript.finished_utc,
        transcript.simulated_resolver_host,
        transcript.simulated_resolver_port,
        transcript.simulated_resolver_results,
        transcript.simulated_selected_address,
        transcript.simulated_socket_instance_count,
        transcript.simulated_connect_attempt_count,
        transcript.simulated_tls_wrap_count,
        transcript.simulated_send_attempt_count,
        transcript.simulated_emitted_request_bytes,
        transcript.supplied_tls_version,
        transcript.supplied_alpn,
        transcript.supplied_cipher_name,
        transcript.supplied_cipher_protocol,
        transcript.supplied_cipher_bits,
        transcript.supplied_peer_certificate_bytes,
        transcript.response_chunks,
        transcript.injected_failure_stage,
    )
    for label, value in (
        ("intent_utc", transcript.intent_utc),
        ("started_utc", transcript.started_utc),
        ("finished_utc", transcript.finished_utc),
        ("simulated_resolver_host", transcript.simulated_resolver_host),
        ("simulated_selected_address", transcript.simulated_selected_address),
    ):
        if type(value) is not str:
            raise AdmissionError(f"transcript.{label}: exact string required")
        _require_string(value, f"transcript.{label}")
    for label, value in (
        ("simulated_resolver_port", transcript.simulated_resolver_port),
        ("simulated_socket_instance_count", transcript.simulated_socket_instance_count),
        ("simulated_connect_attempt_count", transcript.simulated_connect_attempt_count),
        ("simulated_tls_wrap_count", transcript.simulated_tls_wrap_count),
        ("simulated_send_attempt_count", transcript.simulated_send_attempt_count),
    ):
        _require_exact_int(value, f"transcript.{label}")
    if type(transcript.simulated_resolver_results) is not tuple:
        raise AdmissionError("simulated resolver results must be an exact string tuple")
    if len(transcript.simulated_resolver_results) != 2:
        raise AdmissionError("simulated resolver result count must be exact 2")
    if any(type(item) is not str for item in transcript.simulated_resolver_results):
        raise AdmissionError("simulated resolver results must be an exact string tuple")
    for ordinal, item in enumerate(transcript.simulated_resolver_results):
        _require_string(item, f"transcript.simulated_resolver_results[{ordinal}]")
    for label, value in (
        ("simulated_emitted_request_bytes", transcript.simulated_emitted_request_bytes),
        ("supplied_peer_certificate_bytes", transcript.supplied_peer_certificate_bytes),
    ):
        if value is not None and type(value) is not bytes:
            raise AdmissionError(f"transcript.{label}: exact bytes or null required")
    for label, value in (
        ("supplied_tls_version", transcript.supplied_tls_version),
        ("supplied_alpn", transcript.supplied_alpn),
        ("supplied_cipher_name", transcript.supplied_cipher_name),
        ("supplied_cipher_protocol", transcript.supplied_cipher_protocol),
        ("injected_failure_stage", transcript.injected_failure_stage),
    ):
        if value is not None and type(value) is not str:
            raise AdmissionError(f"transcript.{label}: exact string or null required")
        if value is not None:
            _require_string(value, f"transcript.{label}")
    if (
        transcript.supplied_cipher_bits is not None
        and type(transcript.supplied_cipher_bits) is not int
    ):
        raise AdmissionError("transcript.supplied_cipher_bits: exact int or null required")
    if transcript.supplied_cipher_bits is not None:
        _require_exact_int(
            transcript.supplied_cipher_bits,
            "transcript.supplied_cipher_bits",
            minimum=1,
        )
    if type(transcript.response_chunks) is not tuple:
        raise AdmissionError("response chunks must be an exact bytes tuple")
    if len(transcript.response_chunks) > MAX_TRANSCRIPT_CHUNK_COUNT:
        raise AdmissionError("response chunk count ceiling exceeded")
    if any(type(chunk) is not bytes for chunk in transcript.response_chunks):
        raise AdmissionError("response chunks must be an exact bytes tuple")
    response_total = 0
    for chunk in transcript.response_chunks:
        response_total += len(chunk)
        if response_total > MAX_TOTAL_RESPONSE_BYTES:
            raise AdmissionError("response transcript total byte ceiling exceeded")
    intent_time = _parse_utc(transcript.intent_utc, "transcript.intent_utc")
    started_time = _parse_utc(transcript.started_utc, "transcript.started_utc")
    finished_time = _parse_utc(transcript.finished_utc, "transcript.finished_utc")
    if not (intent_time <= started_time <= finished_time):
        raise AdmissionError("transcript timestamp order invalid")
    if transcript.simulated_resolver_host != operation.host:
        raise AdmissionError("simulated resolver host mismatch")
    if (
        type(transcript.simulated_resolver_port) is not int
        or transcript.simulated_resolver_port != 443
    ):
        raise AdmissionError("simulated resolver port mismatch")
    expected_results = ("192.0.2.10:443", "[2001:db8::10]:443")
    if transcript.simulated_resolver_results != expected_results:
        raise AdmissionError("simulated resolver result roster mismatch")
    if transcript.simulated_selected_address != expected_results[0]:
        raise AdmissionError("simulated deterministic address selection mismatch")
    for label, actual, expected in (
        ("socket_instance_count", transcript.simulated_socket_instance_count, 1),
        ("connect_attempt_count", transcript.simulated_connect_attempt_count, 1),
    ):
        if type(actual) is not int or actual != expected:
            raise AdmissionError(f"simulated {label}: exact {expected} required")
    for label, value in (
        ("tls_wrap_count", transcript.simulated_tls_wrap_count),
        ("send_attempt_count", transcript.simulated_send_attempt_count),
    ):
        if type(value) is not int or value not in (0, 1):
            raise AdmissionError(f"simulated {label}: exact 0 or 1 required")
    if transcript.injected_failure_stage not in {None, "CONNECT_FAILURE", "SEND_FAILURE"}:
        raise AdmissionError("injected failure stage invalid")
    if transcript.injected_failure_stage == "CONNECT_FAILURE":
        expected = (0, 0, None, None, None, None, None, None, None, ())
        actual = (
            transcript.simulated_tls_wrap_count,
            transcript.simulated_send_attempt_count,
            transcript.simulated_emitted_request_bytes,
            transcript.supplied_tls_version,
            transcript.supplied_alpn,
            transcript.supplied_cipher_name,
            transcript.supplied_cipher_protocol,
            transcript.supplied_cipher_bits,
            transcript.supplied_peer_certificate_bytes,
            transcript.response_chunks,
        )
        if actual != expected:
            raise AdmissionError("connect-failure transcript has post-connect events")
    else:
        if transcript.simulated_tls_wrap_count != 1:
            raise AdmissionError("non-connect-failure transcript requires one TLS event")
        for label, value in (
            ("supplied_tls_version", transcript.supplied_tls_version),
            ("supplied_alpn", transcript.supplied_alpn),
            ("supplied_cipher_name", transcript.supplied_cipher_name),
            ("supplied_cipher_protocol", transcript.supplied_cipher_protocol),
        ):
            _require_string(value, f"transcript.{label}")
        _require_exact_int(
            transcript.supplied_cipher_bits,
            "transcript.supplied_cipher_bits",
            minimum=1,
        )
        certificate = transcript.supplied_peer_certificate_bytes
        if (
            type(certificate) is not bytes
            or not certificate
            or len(certificate) > MAX_CERTIFICATE_BYTES
        ):
            raise AdmissionError("supplied certificate byte bound invalid")
        policy_valid = (
            transcript.supplied_tls_version in {"TLSv1.2", "TLSv1.3"}
            and transcript.supplied_alpn == "http/1.1"
        )
        if transcript.injected_failure_stage == "SEND_FAILURE":
            if (
                not policy_valid
                or transcript.simulated_send_attempt_count != 1
                or transcript.simulated_emitted_request_bytes != operation.request_bytes
                or transcript.response_chunks != ()
            ):
                raise AdmissionError("send-failure transcript shape mismatch")
        elif policy_valid:
            if (
                transcript.simulated_send_attempt_count != 1
                or transcript.simulated_emitted_request_bytes != operation.request_bytes
            ):
                raise AdmissionError("successful-send transcript shape mismatch")
        elif (
            transcript.simulated_send_attempt_count != 0
            or transcript.simulated_emitted_request_bytes is not None
            or transcript.response_chunks != ()
        ):
            raise AdmissionError("TLS-policy-failure transcript has send or response events")

    chunks = [
        {"ordinal": index, "bytes": len(chunk), "raw_sha256": _sha256(chunk)}
        for index, chunk in enumerate(transcript.response_chunks)
    ]
    value = {
        "schema_version": INERT_TRANSCRIPT_SCHEMA_VERSION,
        "row_ordinal": operation.ordinal,
        "operation_id": operation.operation_id,
        "intent_utc": transcript.intent_utc,
        "started_utc": transcript.started_utc,
        "finished_utc": transcript.finished_utc,
        "simulated_resolver_host": transcript.simulated_resolver_host,
        "simulated_resolver_port": transcript.simulated_resolver_port,
        "simulated_resolver_results": list(transcript.simulated_resolver_results),
        "simulated_selected_address": transcript.simulated_selected_address,
        "simulated_socket_instance_count": transcript.simulated_socket_instance_count,
        "simulated_connect_attempt_count": transcript.simulated_connect_attempt_count,
        "simulated_tls_wrap_count": transcript.simulated_tls_wrap_count,
        "simulated_send_attempt_count": transcript.simulated_send_attempt_count,
        "simulated_emitted_request_bytes": (
            None
            if transcript.simulated_emitted_request_bytes is None
            else len(transcript.simulated_emitted_request_bytes)
        ),
        "simulated_emitted_request_sha256": (
            None
            if transcript.simulated_emitted_request_bytes is None
            else _sha256(transcript.simulated_emitted_request_bytes)
        ),
        "supplied_tls_version": transcript.supplied_tls_version,
        "supplied_alpn": transcript.supplied_alpn,
        "supplied_cipher_name": transcript.supplied_cipher_name,
        "supplied_cipher_protocol": transcript.supplied_cipher_protocol,
        "supplied_cipher_bits": transcript.supplied_cipher_bits,
        "supplied_peer_certificate_bytes": (
            None
            if transcript.supplied_peer_certificate_bytes is None
            else len(transcript.supplied_peer_certificate_bytes)
        ),
        "supplied_peer_certificate_sha256": (
            None
            if transcript.supplied_peer_certificate_bytes is None
            else _sha256(transcript.supplied_peer_certificate_bytes)
        ),
        "response_chunks": chunks,
        "injected_failure_stage": transcript.injected_failure_stage,
        "external_effect": 0,
    }
    digest = _sha256(_canonical_no_lf(value))
    return transcript, value, digest


def transcript_receipt(row_ordinal: int, transcript: InertTranscript) -> dict[str, Any]:
    """Return the detached canonical receipt model for an inert transcript."""

    _snapshot, record, digest = _validate_transcript(
        transcript, _operation(row_ordinal)
    )
    return {**_clone_plain(record), "inert_transcript_sha256": digest}


def _intent_record(
    operation: Operation,
    transcript: InertTranscript,
    transcript_sha256: str,
    previous_outcome_sha256: str | None,
) -> dict[str, Any]:
    value = {
        "schema_version": INTENT_SCHEMA_VERSION,
        "record_kind": "QUALIFICATION_ONLY_IN_MEMORY_INTENT_MODEL",
        "row_ordinal": operation.ordinal,
        "operation_id": operation.operation_id,
        "created_utc": transcript.intent_utc,
        "previous_qualification_outcome_sha256": previous_outcome_sha256,
        "inert_transcript_sha256": transcript_sha256,
        "exact_request_sha256": operation.exact_request_sha256,
        "method": "GET",
        "url": operation.url,
        "future_attempt_limit": 1,
        "future_retry_limit": 0,
        "future_redirect_limit": 0,
        "machine_raw_sha256": None,
        "machine_record_sha256": None,
        "package_aggregate_sha256": None,
        "executor_raw_sha256": None,
        "environment_manifest_sha256": None,
        "operational_admission_receipt_sha256": None,
        "operational_qualification_receipt_sha256": None,
        "operational_independent_go_receipt_sha256": None,
        "operational_fresh_authority_receipt_sha256": None,
        "operational_custody_root_path": None,
        "custody_root_identity_sha256": None,
        "operational_row_directory_basename": None,
        "filesystem_materialized": False,
        "intent_durable": False,
        "attempt_spent_in_external_system": False,
        "external_effect": 0,
        "record_sha256": None,
    }
    value["record_sha256"] = _self_digest(value)
    return value


def _metadata_record(
    operation: Operation,
    transcript: InertTranscript,
    transcript_sha256: str,
) -> dict[str, Any]:
    certificate = transcript.supplied_peer_certificate_bytes
    return {
        "schema_version": "heterodiff-sb2-public-root-inert-transport-metadata-v2",
        "evidence_kind": "SUPPLIED_INERT_TRANSCRIPT_NOT_LIVE_NEGOTIATION",
        "row_ordinal": operation.ordinal,
        "operation_id": operation.operation_id,
        "server_hostname": operation.host,
        "port": 443,
        "inert_transcript_sha256": transcript_sha256,
        "simulated_resolver_result_count": len(transcript.simulated_resolver_results),
        "simulated_selected_address": transcript.simulated_selected_address,
        "simulated_socket_instance_count": transcript.simulated_socket_instance_count,
        "simulated_connect_attempt_count": transcript.simulated_connect_attempt_count,
        "simulated_tls_wrap_count": transcript.simulated_tls_wrap_count,
        "simulated_send_attempt_count": transcript.simulated_send_attempt_count,
        "supplied_tls_version": transcript.supplied_tls_version,
        "supplied_cipher_name": transcript.supplied_cipher_name,
        "supplied_cipher_protocol": transcript.supplied_cipher_protocol,
        "supplied_cipher_bits": transcript.supplied_cipher_bits,
        "supplied_alpn": transcript.supplied_alpn,
        "supplied_peer_certificate_sha256": (
            None if certificate is None else _sha256(certificate)
        ),
        "live_tls_negotiation": False,
        "certificate_verification_performed": False,
        "hostname_verification_performed": False,
        "external_effect": 0,
    }


def _artifact_name(operation: Operation, role: str) -> str:
    suffix_by_role = dict(ARTIFACT_SUFFIXES)
    if role not in suffix_by_role:
        raise AdmissionError("unknown modeled artifact role")
    return f"row-{operation.ordinal:03d}{suffix_by_role[role]}"


def _artifact_receipt(operation: Operation, role: str, raw: bytes) -> dict[str, Any]:
    return {
        "role": role,
        "logical_name": _artifact_name(operation, role),
        "bytes": len(raw),
        "raw_sha256": _sha256(raw),
        "filesystem_materialized": False,
        "future_mode_octal": "0600",
        "future_nlink_required": 1,
        "filesystem_effect": 0,
    }


def _chain_links(
    previous: str | None, artifacts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    head = previous
    for ordinal, item in enumerate(artifacts):
        payload = {
            "schema_version": "heterodiff-sb2-public-root-forward-link-v2",
            "ordinal": ordinal,
            "role": item["role"],
            "artifact_raw_sha256": item["raw_sha256"],
            "previous_link_sha256": head,
        }
        link = _sha256(_canonical_no_lf(payload))
        links.append({**payload, "link_sha256": link})
        head = link
    return links


OUTCOME_NON_DIAGNOSTIC_KEYS = frozenset(
    {
        "schema_version",
        "record_kind",
        "row_ordinal",
        "operation_id",
        "inert_transcript_sha256",
        "modeled_intent_record_sha256",
        "modeled_custody_plan_sha256",
        "previous_qualification_outcome_sha256",
        "machine_raw_sha256",
        "machine_record_sha256",
        "package_aggregate_sha256",
        "executor_raw_sha256",
        "environment_manifest_sha256",
        "operational_admission_receipt_sha256",
        "operational_qualification_receipt_sha256",
        "operational_independent_go_receipt_sha256",
        "operational_fresh_authority_receipt_sha256",
        "operational_custody_root_path",
        "custody_root_identity_sha256",
        "operational_row_directory_basename",
        "started_utc",
        "finished_utc",
        "terminal_state",
        "failure_code",
        "fetch_eligible",
        "request_emitted_count",
        "live_request_emitted_count",
        "transcript_request_emission_event_count",
        "external_network_effect",
        "retry_count",
        "redirect_count",
        "url",
        "effective_url",
        "effective_url_sha256",
        "exact_request_sha256",
        "tls_evidence_kind",
        "tls_version",
        "cipher_name",
        "cipher_protocol",
        "cipher_bits",
        "alpn",
        "peer_certificate_sha256",
        "root_page_success",
        "inert_transcript_accepted",
        "filesystem_materialized",
        "custody_mechanics_qualified",
        "intent_durable",
        "attempt_spent_in_external_system",
        "approval_created",
        "source_selection_success_created",
        "field_closed",
        "box_closed",
        "scientific_effect",
        "modeled_artifacts",
        "forward_hash_chain",
        "record_sha256",
    }
)
OUTCOME_DIAGNOSTIC_FIELDS = frozenset(
    field for field, _exact_type in OUTCOME_DIAGNOSTIC_FIELD_TYPES
)
OUTCOME_KEYS = OUTCOME_NON_DIAGNOSTIC_KEYS | OUTCOME_DIAGNOSTIC_FIELDS


def _exact_keys(value: dict[str, Any], expected: frozenset[str], label: str) -> None:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise AdmissionError(f"{label}: exact builtin string-key dict required")
    if set(value) != expected:
        raise AdmissionError(
            f"{label}: exact keys required missing={sorted(expected - set(value))} "
            f"extra={sorted(set(value) - expected)}"
        )


def _validate_diagnostic_lists(outcome: dict[str, Any]) -> None:
    rosters = {
        "rejection_substring_matches": {
            marker.decode("ascii") for marker in CHALLENGE_MARKERS
        },
        "forbidden_magic_prefix_matches": {
            prefix.hex() for prefix in FORBIDDEN_MAGIC_PREFIXES
        },
        "title_classifier_matches": {
            "captcha", "challenge", "denied", "error", "login", "sign in"
        },
    }
    for key, allowed in rosters.items():
        value = outcome.get(key)
        if (
            type(value) is not list
            or any(type(item) is not str for item in value)
            or value != sorted(set(value))
            or not set(value) <= allowed
        ):
            raise AdmissionError(f"{key}: exact sorted unique diagnostic roster required")


def _validate_outcome_diagnostic_field_types(outcome: dict[str, Any]) -> None:
    if len(OUTCOME_DIAGNOSTIC_FIELDS) != len(OUTCOME_DIAGNOSTIC_FIELD_TYPES):
        raise AdmissionError("outcome diagnostic roster contains duplicate fields")
    for field, exact_type in OUTCOME_DIAGNOSTIC_FIELD_TYPES:
        if field not in outcome:
            raise AdmissionError(f"outcome diagnostic field missing: {field}")
        value = outcome[field]
        valid = False
        if exact_type == "EXACT_INT_OR_NULL":
            valid = value is None or type(value) is int
        elif exact_type == "EXACT_STRING_OR_NULL":
            valid = value is None or type(value) is str
        elif exact_type == "EXACT_BOOL":
            valid = type(value) is bool
        elif exact_type == "EXACT_LIST_OF_EXACT_STRING":
            valid = type(value) is list and all(
                type(item) is str for item in value
            )
        if not valid:
            raise AdmissionError(
                f"outcome diagnostic field {field}: {exact_type} required"
            )

    if outcome["header_diagnostics_complete"]:
        relations = (
            ("content_type_header_count", "content_type_raw_values"),
            (
                "content_disposition_header_count",
                "content_disposition_raw_values",
            ),
            ("location_header_count", "location_raw_values"),
            ("content_encoding_header_count", "content_encoding_raw_values"),
            ("transfer_encoding_header_count", "transfer_encoding_raw_values"),
        )
        for count_field, values_field in relations:
            if outcome[count_field] != len(outcome[values_field]):
                raise AdmissionError(
                    f"outcome diagnostic relation mismatch: {count_field}"
                )
        if outcome["content_encoding_normalized_values"] != [
            value.lower() for value in outcome["content_encoding_raw_values"]
        ]:
            raise AdmissionError("content encoding normalization mismatch")
        if outcome["transfer_encoding_normalized_values"] != [
            value.lower() for value in outcome["transfer_encoding_raw_values"]
        ]:
            raise AdmissionError("transfer encoding normalization mismatch")
    else:
        for count_field in (
            "content_type_header_count",
            "content_disposition_header_count",
            "location_header_count",
            "content_encoding_header_count",
            "transfer_encoding_header_count",
        ):
            if outcome[count_field] is not None:
                raise AdmissionError(
                    f"incomplete header diagnostics require null {count_field}"
                )
        for values_field in (
            "content_type_raw_values",
            "content_disposition_raw_values",
            "location_raw_values",
            "content_encoding_raw_values",
            "content_encoding_normalized_values",
            "transfer_encoding_raw_values",
            "transfer_encoding_normalized_values",
        ):
            if outcome[values_field] != []:
                raise AdmissionError(
                    f"incomplete header diagnostics require empty {values_field}"
                )
        if outcome["normalized_media_type"] is not None:
            raise AdmissionError(
                "incomplete header diagnostics require null normalized media type"
            )
    if outcome["framing_complete"] and not outcome["header_diagnostics_complete"]:
        raise AdmissionError("framing completion requires header diagnostics")
    if outcome["dechunk_complete"] and not outcome["framing_complete"]:
        raise AdmissionError("dechunk completion requires framing completion")
    if outcome["decoded_entity_body_receipt_complete"] and not (
        outcome["framing_complete"] and outcome["dechunk_complete"]
    ):
        raise AdmissionError("decoded receipt completeness relation invalid")
    if outcome["body_truncated"] and outcome[
        "decoded_entity_body_receipt_complete"
    ]:
        raise AdmissionError(
            "truncated body cannot have a complete decoded entity receipt"
        )


def _derive_validated_outcome(
    *,
    operation: Operation,
    transcript: InertTranscript,
    transcript_sha256: str,
    previous_sha256: str | None,
) -> dict[str, Any]:
    """Derive one outcome from already snapshotted and validated plain data."""

    intent = _intent_record(operation, transcript, transcript_sha256, previous_sha256)
    custody = _custody_plan_record(operation)
    custody_sha256 = _sha256(_canonical_no_lf(custody))
    metadata = _metadata_record(operation, transcript, transcript_sha256)
    response: _ResponseResult | None = None
    terminal_error: ReconnaissanceError | None = None
    transcript_emission_event = 0
    captured_head = b""
    captured_body = b""
    decoded_body = b""

    try:
        if transcript.injected_failure_stage == "CONNECT_FAILURE":
            raise TransportError("inert transcript models one connect failure")
        if transcript.supplied_tls_version not in {"TLSv1.2", "TLSv1.3"}:
            raise ProtocolError("supplied TLS version outside frozen future policy")
        if transcript.supplied_alpn != "http/1.1":
            raise ProtocolError("supplied ALPN outside frozen future policy")
        transcript_emission_event = 1
        if transcript.injected_failure_stage == "SEND_FAILURE":
            raise TransportError("inert transcript models partial-send failure")
        response = _receive_response(transcript.response_chunks)
        captured_head = response.raw_head
        captured_body = response.raw_body
        decoded_body = response.decoded_body
    except ReconnaissanceError as exc:
        terminal_error = exc
        captured_head = exc.captured_head
        captured_body = exc.captured_body
        decoded_body = exc.decoded_body

    accepted = terminal_error is None and response is not None
    evidence = {} if terminal_error is None else terminal_error.evidence

    def observed(name: str, default: Any = None) -> Any:
        if response is not None and hasattr(response, name):
            return getattr(response, name)
        return _clone_plain(evidence.get(name, default))

    error_code = "NONE" if accepted else terminal_error.code
    artifact_payloads = {
        "intent": _canonical(intent),
        "raw_request": operation.request_bytes,
        "raw_response_head": captured_head,
        "raw_transfer_body": captured_body,
        "raw_metadata": _canonical(metadata),
        "raw_stderr": (error_code + "\n").encode("ascii"),
        "decoded_entity_body": decoded_body,
    }
    artifact_roles = [
        "intent",
        "raw_request",
        "raw_response_head",
        "raw_transfer_body",
        "raw_metadata",
        "raw_stderr",
        "decoded_entity_body",
    ]
    artifacts = [
        _artifact_receipt(operation, role, artifact_payloads[role])
        for role in artifact_roles
    ]
    links = _chain_links(previous_sha256, artifacts)
    terminal_state = (
        "QUALIFICATION_ONLY_TERMINAL_INERT_ROOT_PAGE_TRANSCRIPT_ACCEPTED_NO_NETWORK"
        if accepted
        else "QUALIFICATION_ONLY_" + terminal_error.terminal_state
    )
    certificate = transcript.supplied_peer_certificate_bytes
    outcome = {
        "schema_version": OUTCOME_SCHEMA_VERSION,
        "record_kind": "QUALIFICATION_ONLY_INERT_ROOT_PAGE_TERMINAL_OUTCOME",
        "row_ordinal": operation.ordinal,
        "operation_id": operation.operation_id,
        "inert_transcript_sha256": transcript_sha256,
        "modeled_intent_record_sha256": intent["record_sha256"],
        "modeled_custody_plan_sha256": custody_sha256,
        "previous_qualification_outcome_sha256": previous_sha256,
        "machine_raw_sha256": None,
        "machine_record_sha256": None,
        "package_aggregate_sha256": None,
        "executor_raw_sha256": None,
        "environment_manifest_sha256": None,
        "operational_admission_receipt_sha256": None,
        "operational_qualification_receipt_sha256": None,
        "operational_independent_go_receipt_sha256": None,
        "operational_fresh_authority_receipt_sha256": None,
        "operational_custody_root_path": None,
        "custody_root_identity_sha256": None,
        "operational_row_directory_basename": None,
        "started_utc": transcript.started_utc,
        "finished_utc": transcript.finished_utc,
        "terminal_state": terminal_state,
        "failure_code": None if accepted else terminal_error.code,
        "fetch_eligible": False,
        "request_emitted_count": 0,
        "live_request_emitted_count": 0,
        "transcript_request_emission_event_count": transcript_emission_event,
        "external_network_effect": 0,
        "retry_count": 0,
        "redirect_count": 0,
        "url": operation.url,
        "effective_url": None,
        "effective_url_sha256": None,
        "exact_request_sha256": operation.exact_request_sha256,
        "status_code": observed("status_code"),
        "protocol": observed("protocol"),
        "tls_evidence_kind": "SUPPLIED_INERT_TRANSCRIPT_NOT_LIVE_NEGOTIATION",
        "tls_version": transcript.supplied_tls_version,
        "cipher_name": transcript.supplied_cipher_name,
        "cipher_protocol": transcript.supplied_cipher_protocol,
        "cipher_bits": transcript.supplied_cipher_bits,
        "alpn": transcript.supplied_alpn,
        "peer_certificate_sha256": (
            None if certificate is None else _sha256(certificate)
        ),
        "framing": observed("framing"),
        "framing_complete": observed("framing_complete", False),
        "header_diagnostics_complete": observed(
            "header_diagnostics_complete", False
        ),
        "content_type_header_count": observed("content_type_header_count"),
        "content_type_raw_values": observed("content_type_raw_values", []),
        "normalized_media_type": observed("normalized_media_type"),
        "content_disposition_header_count": observed(
            "content_disposition_header_count"
        ),
        "content_disposition_raw_values": observed(
            "content_disposition_raw_values", []
        ),
        "location_header_count": observed("location_header_count"),
        "location_raw_values": observed("location_raw_values", []),
        "content_encoding_header_count": observed(
            "content_encoding_header_count"
        ),
        "content_encoding_raw_values": observed(
            "content_encoding_raw_values", []
        ),
        "content_encoding_normalized_values": observed(
            "content_encoding_normalized_values", []
        ),
        "transfer_encoding_header_count": observed(
            "transfer_encoding_header_count"
        ),
        "transfer_encoding_raw_values": observed(
            "transfer_encoding_raw_values", []
        ),
        "transfer_encoding_normalized_values": observed(
            "transfer_encoding_normalized_values", []
        ),
        "transfer_encoding_semantics_valid": observed(
            "transfer_encoding_semantics_valid", False
        ),
        "dechunk_complete": observed("dechunk_complete", False),
        "decoded_entity_body_receipt_complete": observed(
            "decoded_entity_body_receipt_complete", False
        ),
        "body_utf8_valid": observed("body_utf8_valid", accepted),
        "forbidden_magic_detected": observed("forbidden_magic_detected", False),
        "forbidden_magic_prefix_matches": observed(
            "forbidden_magic_prefix_matches", []
        ),
        "challenge_page_detected": observed("challenge_page_detected", False),
        "rejection_substring_matches": observed("rejection_substring_matches", []),
        "title_classifier_matches": observed("title_classifier_matches", []),
        "login_wall_detected": observed("login_wall_detected", False),
        "consent_wall_detected": observed("consent_wall_detected", False),
        "robot_block_detected": observed("robot_block_detected", False),
        "error_page_detected": observed("error_page_detected", False),
        "raw_status_start": observed("raw_status_start"),
        "raw_status_end_exclusive": observed("raw_status_end_exclusive"),
        "raw_headers_start": observed("raw_headers_start"),
        "raw_headers_end_exclusive": observed("raw_headers_end_exclusive"),
        "body_truncated": observed("body_truncated", False),
        "root_page_success": False,
        "inert_transcript_accepted": accepted,
        "filesystem_materialized": False,
        "custody_mechanics_qualified": False,
        "intent_durable": False,
        "attempt_spent_in_external_system": False,
        "approval_created": False,
        "source_selection_success_created": False,
        "field_closed": False,
        "box_closed": False,
        "scientific_effect": 0,
        "modeled_artifacts": artifacts,
        "forward_hash_chain": links,
        "record_sha256": None,
    }
    _exact_keys(outcome, OUTCOME_KEYS, "inert outcome")
    _validate_outcome_diagnostic_field_types(outcome)
    _validate_diagnostic_lists(outcome)
    outcome["record_sha256"] = _self_digest(outcome)
    return _clone_plain(outcome)


def qualify_row_from_inert_transcript(
    row_ordinal: int,
    *,
    transcript: InertTranscript,
    prior_transcript: InertTranscript | None = None,
    prior_outcome: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive an offline outcome, contextually recomputing row 0 for row 1."""

    operation = _operation(row_ordinal)
    transcript, _record, transcript_sha256 = _validate_transcript(
        transcript, operation
    )
    previous_sha256: str | None = None
    if operation.ordinal == 0:
        if prior_transcript is not None or prior_outcome is not None:
            raise AdmissionError("row0 prior transcript and outcome must both be null")
    else:
        if type(prior_transcript) is not InertTranscript:
            raise AdmissionError("row1 requires exact row0 InertTranscript")
        if type(prior_outcome) is not dict:
            raise AdmissionError("row1 requires exact claimed row0 outcome dict")
        prior_operation = _operation(0)
        prior_snapshot, _prior_record, prior_transcript_sha256 = _validate_transcript(
            prior_transcript, prior_operation
        )
        expected_prior = _derive_validated_outcome(
            operation=prior_operation,
            transcript=prior_snapshot,
            transcript_sha256=prior_transcript_sha256,
            previous_sha256=None,
        )
        try:
            claimed_prior = _clone_plain(prior_outcome)
        except (TypeError, RecursionError) as exc:
            raise AdmissionError("claimed row0 outcome must be exact plain data") from exc
        if not _strict_plain_equal(claimed_prior, expected_prior):
            raise AdmissionError(
                "claimed row0 outcome differs from full contextual recomputation"
            )
        if expected_prior["inert_transcript_accepted"] is not True:
            raise AdmissionError("recomputed row0 transcript was not accepted")
        prior_finished = _parse_utc(
            expected_prior["finished_utc"], "recomputed row0 finished_utc"
        )
        if prior_finished >= _parse_utc(
            transcript.intent_utc, "row1 transcript.intent_utc"
        ):
            raise AdmissionError("row1 transcript does not follow row0 outcome")
        previous_sha256 = _sha256(_canonical(expected_prior))

    return _derive_validated_outcome(
        operation=operation,
        transcript=transcript,
        transcript_sha256=transcript_sha256,
        previous_sha256=previous_sha256,
    )


__all__ = [
    "EXECUTOR_CONTRACT_SHA256",
    "EXECUTOR_SCHEMA_VERSION",
    "FETCH_ELIGIBLE",
    "INERT_TRANSCRIPT_SCHEMA_VERSION",
    "INTENT_SCHEMA_VERSION",
    "InertTranscript",
    "OPERATION_ROSTER_SHA256",
    "OUTCOME_DIAGNOSTIC_FIELD_TYPES",
    "OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256",
    "OUTCOME_SCHEMA_VERSION",
    "PACKAGE_ROLE",
    "RUNTIME_HOLD_REASON",
    "SIMULATION_RESULT_SCHEMA_VERSION",
    "AdmissionError",
    "ContentError",
    "ProtocolError",
    "ReconnaissanceError",
    "ScopeError",
    "TransportError",
    "custody_plan",
    "exact_request_bytes",
    "executor_contract",
    "operation_spec",
    "qualify_row_from_inert_transcript",
    "transcript_receipt",
]
