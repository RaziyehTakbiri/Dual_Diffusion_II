"""Solo Block 2 row-zero-only V5 successor runtime/custody executor.

This additive successor has closed offline receipt registrars and one exact
row-zero attempt.  No row-one production route exists.  A root-level durable
successor-budget marker is created only after the final authority is reopened
and revalidated; that marker permanently spends the single successor budget
before intent, resolver, socket, TLS, or request activity.

``preflight CUSTODY_ROOT`` captures an offline runtime/custody receipt after
an independently stopped package lock and exact local-preflight authority are
present.  ``attempt CUSTODY_ROOT`` performs at most one row-zero attempt, but
only after it byte-reopens every package, runtime, GO, authority, sequence and
custody gate and durably reserves the row intent.  After the interpreter and
import loader have loaded the exact bound modules, this module's top-level
application code invokes no resolver, socket, subprocess, entropy API or
canonical write.  Python startup/import filesystem activity and hash-seed
entropy are runtime-manifest inputs, not claimed absent.

The source/interpreter receipts are post-load path checks, not a one-open OS
attestation of the already executing images.  Concurrent same-UID path
substitution is outside the technical gate.  Likewise registrar principals
and nanosecond times are exact caller assertions, not externally signed
identity or trusted-clock attestations; every resulting receipt says so.

There is no injected transport, resolver, filesystem, clock, environment or
socket seam.  The pure HTTP helpers accept bytes only so hostile qualification
can be loopback-free; the production entrypoint never accepts a transcript.
"""

from __future__ import annotations

import base64
import ctypes
import errno
import fcntl
import hashlib
import ipaddress
import json
import locale
import os
import platform
import re
import select
import signal
import socket
import ssl
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Final, Mapping, NoReturn, Sequence


SCHEMA_VERSION: Final = "heterodiff-solo-block2-runtime-custody-executor-v5"
MACHINE_SCHEMA: Final = (
    "heterodiff-manuscript-v3-solo-block2-runtime-custody-closure-v5"
)
MACHINE_STATE: Final = (
    "FINAL_V5_OFFLINE_ACTIVATION_SUCCESSOR_FROZEN_RECEIPTS_NULL_NETWORK_HOLD"
)
PACKAGE_AGGREGATE_SCHEMA: Final = "heterodiff-solo-block2-runtime-package-aggregate-v5"
PACKAGE_LOCK_SCHEMA: Final = "heterodiff-solo-block2-runtime-package-lock-v5"
SUPERSESSION_AUTHORITY_SCHEMA: Final = (
    "heterodiff-solo-block2-runtime-supersession-authority-v5"
)
PREFLIGHT_AUTHORITY_SCHEMA: Final = (
    "heterodiff-solo-block2-runtime-preflight-authority-v5"
)
RUNTIME_PREFLIGHT_SCHEMA: Final = "heterodiff-solo-block2-runtime-preflight-v5"
INDEPENDENT_GO_SCHEMA: Final = "heterodiff-solo-block2-root-row-independent-go-v5"
ROW_AUTHORITY_SCHEMA: Final = "heterodiff-solo-block2-root-row-authority-v5"
INTENT_SCHEMA: Final = "heterodiff-solo-block2-root-row-intent-v5"
OUTCOME_SCHEMA: Final = "heterodiff-solo-block2-root-row-outcome-v5"
ERROR_SCHEMA: Final = "heterodiff-solo-block2-root-row-error-v5"
SUCCESSOR_BUDGET_SPEND_SCHEMA: Final = (
    "heterodiff-solo-block2-successor-budget-spend-v5"
)

V5_OPERATIONAL_ROOT: Final = (
    "/Users/mahtab/.codex/.chatgpt-projects/"
    "g-p-6a5f91c1e79c819183983ba0010bb151/research/custody/"
    "solo_block2_public_documentation_runtime_v4"
)
V5_ROOT_DEVICE: Final = 16777234
V5_ROOT_INODE: Final = 67067435
V5_ROOT_UID: Final = 501
V5_ROOT_GID: Final = 20
V5_ROOT_MODE: Final = 0o700
SUCCESSOR_BUDGET_DEFINITION_ID: Final = (
    "da3af347580d19b11f83b8590018a61b2e4296c613f78d8a1039c1c9cfdfb9ce"
)
SUCCESSOR_BUDGET_SCOPE: Final = "GLOBAL_SINGLE_ADDITIONAL_ROW0_ATTEMPT_ONLY"
V4_PACKAGE_AGGREGATE_SHA256: Final = (
    "449c5d4954e4ac3829994d4ba5dd17ed401388548a93469cf1f0bb35e67ecb02"
)
V4_MACHINE_RAW_SHA256: Final = (
    "8a18ebb868b657282cba04c1be43ae0f953fabf870002a4edcbdd1bddcd9fc70"
)
V4_MACHINE_SEMANTIC_SHA256: Final = (
    "b3e924742dd164583b5a0aac7a5aec5deca431f75395a3dd7e7800a276bfbea6"
)
V2_PACKAGE_AGGREGATE_SHA256: Final = (
    "48091940a7ceb844c892fb06fd263e479b8c86a1f46c4f0c88d00d72a87439cb"
)
V2_INTENT_RAW_SHA256: Final = "a02263b26109ef29f7212a8ea72c987e9e4f7732a88f6ff6b305b99d89177b92"
V2_INTENT_SEMANTIC_SHA256: Final = "e3735ad4c4ab07e79ab0dbc3ef8e8f3c26f5ee86489a7233b854854dea5d1610"
V2_ERROR_RAW_SHA256: Final = "705ddcdb3f0be55ad434620c574a21ea3e02aff6c892ca88f1743d5da6ec3964"
V2_ERROR_SEMANTIC_SHA256: Final = "aaeca81dd0bd9305c624249cfdc057387fd465fee5b889b16b81ce752285ef55"
V2_OUTCOME_RAW_SHA256: Final = "ae72c77609c10c21aaf3e64a8ab77bf4da3adb03c42e55f3bfdfa17f00a98458"
V2_OUTCOME_SEMANTIC_SHA256: Final = "b463ba6475fe82dae08aa98ca2a7d3710915b077f97de2748edf84445aca4924"

EXPECTED_INTERPRETER: Final = (
    "/Users/mahtab/.cache/codex-runtimes/codex-primary-runtime/"
    "dependencies/python/bin/python3.12"
)
EXPECTED_INTERPRETER_SHA256: Final = (
    "71720f1fc66989ebd691e81c96111b47ae6ff3f1a478666084d1cacbf0fccbf2"
)
EXPECTED_PYTHON_VERSION: Final = (
    "3.12.13 (main, Aug  7 2026, 02:15:23) [Clang 22.1.3 ]"
)
EXPECTED_CACHE_TAG: Final = "cpython-312"
EXPECTED_PYTHON_FLAGS: Final = {
    "bytes_warning": 0,
    "debug": 0,
    "dev_mode": False,
    "dont_write_bytecode": 1,
    "hash_randomization": 1,
    "ignore_environment": 1,
    "inspect": 0,
    "int_max_str_digits": 4300,
    "interactive": 0,
    "isolated": 1,
    "no_site": 1,
    "no_user_site": 1,
    "optimize": 0,
    "quiet": 0,
    "safe_path": True,
    "utf8_mode": 1,
    "verbose": 0,
    "warn_default_encoding": 0,
}
EXPECTED_OPENSSL_VERSION: Final = "OpenSSL 3.5.7 9 Jun 2026"
EXPECTED_CA_PATH: Final = "/private/etc/ssl/cert.pem"
EXPECTED_CA_SHA256: Final = (
    "9dae8d76e55cb08991f2b672d58999ea15560d910759c16b544f843bdffbb994"
)
DYLD_CACHE_PATHS: Final = (
    "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/"
    "dyld_shared_cache_arm64e",
    "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/"
    "dyld_shared_cache_arm64e.01",
    "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/"
    "dyld_shared_cache_arm64e.02",
    "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/"
    "dyld_shared_cache_arm64e.atlas",
    "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/"
    "dyld_shared_cache_arm64e.map",
)
SCUTIL_PATH: Final = "/usr/sbin/scutil"
ENV_PATH: Final = "/usr/bin/env"
RESOLV_CONF_PATH: Final = "/private/var/run/resolv.conf"
HOSTS_PATH: Final = "/private/etc/hosts"

PACKAGE_ROOT: Final = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
MACHINE_RELATIVE_PATH: Final = (
    "research/fixtures/"
    "manuscript_v3_solo_block2_runtime_custody_closure_v5.json"
)
SOURCE_RELATIVE_PATH: Final = (
    "src/heterodiff/artifacts/solo_block2_runtime_custody_executor_v5.py"
)
PARENT_PARSER_RELATIVE_PATH: Final = (
    "src/heterodiff/artifacts/"
    "solo_block2_public_documentation_reconnaissance_executor_v2.py"
)
PARENT_PARSER_RAW_SHA256: Final = (
    "9387a1fdab15cb808f6271ec04bd8ff749222561e6bdfe3b33ed69700633ec7f"
)
PARENT_PARSER_CONTRACT_SHA256: Final = (
    "0bd86fe3b851603e68ea642619645e71334a8f689be8d97438490d04a51fe9f2"
)
PARENT_OPERATION_ROSTER_SHA256: Final = (
    "5f305448d4032b55dac54057d2d659212dd512e65113c1123409aa3c089b7548"
)
OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256: Final = (
    "a8fdba4d39e97ac3fbf23d065ae2bd9805cc0513f77d2232c23c7bf4799966dd"
)

MAX_CANONICAL_RECEIPT_BYTES: Final = 1_048_576
MAX_SCUTIL_BYTES: Final = 262_144
MAX_RESOLVER_PIPE_BYTES: Final = 131_072
MAX_STATUS_AND_HEADERS_BYTES: Final = 139_264
MAX_RAW_TRANSFER_BODY_BYTES: Final = 2_097_152
MAX_DECODED_ENTITY_BYTES: Final = 2_097_152
MAX_TLS_METADATA_BYTES: Final = 65_536
MAX_STDERR_BYTES: Final = 65_536
DNS_WAIT_SECONDS: Final = 12.0
CONNECT_SECONDS: Final = 12.0
TLS_SECONDS: Final = 12.0
SEND_SECONDS: Final = 6.0
HEAD_SECONDS: Final = 12.0
BODY_SECONDS: Final = 18.0
TOTAL_ATTEMPT_SECONDS: Final = 45.0
MAX_AUTHORITY_LIFETIME_NS: Final = 3_600_000_000_000

# Receipt leaves must use exact JSON-native builtin integers.  Socket constants
# are IntEnum instances on some supported Python builds and must never be
# reintroduced into retained resolver rows.
AF_INET_INT: Final[int] = int(socket.AF_INET)
AF_INET6_INT: Final[int] = int(socket.AF_INET6)
SOCK_STREAM_INT: Final[int] = int(socket.SOCK_STREAM)
IPPROTO_TCP_INT: Final[int] = int(socket.IPPROTO_TCP)

PACKAGE_LOCK_KEYS: Final = (
    "bound_file_receipts",
    "created_unix_ns",
    "created_time_externally_attested",
    "decision",
    "independent_reviewer_principal",
    "machine_raw_sha256",
    "machine_semantic_sha256",
    "package_aggregate_sha256",
    "record_sha256",
    "reviewer_is_package_author",
    "reviewer_identity_externally_authenticated",
    "schema_version",
)
SUPERSESSION_AUTHORITY_KEYS: Final = (
    "acknowledge_v2_row0_spent_at_durable_intent",
    "acknowledge_v2_terminal_no_retry",
    "acknowledge_sendall_zero_does_not_restore_budget",
    "address_fallback_limit",
    "activated_successor_budget_id",
    "authority_identity_externally_authenticated",
    "created_time_externally_attested",
    "created_unix_ns",
    "custody_root",
    "attempt_limit",
    "connect_limit",
    "exact_request_bytes",
    "exact_request_sha256",
    "exact_url",
    "network_or_contact_authorized",
    "normalized_visible_text",
    "normalized_visible_text_sha256",
    "normalized_visible_text_utf8_bytes",
    "package_aggregate_sha256",
    "package_lock_record_sha256",
    "operation_id",
    "redirect_limit",
    "record_sha256",
    "schema_version",
    "successor_budget_definition_id",
    "successor_budget_scope",
    "resolver_high_level_call_limit",
    "resolver_child_fork_site_limit",
    "retry_limit",
    "row1_may_consume",
    "socket_instance_limit",
    "tls_wrap_limit",
    "request_send_limit",
    "v2_attempt_spend_acknowledged",
    "v2_error_raw_sha256",
    "v2_error_semantic_sha256",
    "v2_intent_raw_sha256",
    "v2_intent_semantic_sha256",
    "v2_outcome_raw_sha256",
    "v2_outcome_semantic_sha256",
    "v2_package_aggregate_sha256",
    "v4_machine_raw_sha256",
    "v4_machine_semantic_sha256",
    "v4_package_aggregate_sha256",
)
PREFLIGHT_AUTHORITY_KEYS: Final = (
    "activated_successor_budget_id",
    "authority_identity_externally_authenticated",
    "created_unix_ns",
    "created_time_externally_attested",
    "network_or_contact_authorized",
    "normalized_visible_text",
    "normalized_visible_text_sha256",
    "normalized_visible_text_utf8_bytes",
    "package_aggregate_sha256",
    "record_sha256",
    "schema_version",
    "successor_budget_definition_id",
    "supersession_authority_record_sha256",
)
RUNTIME_PREFLIGHT_KEYS: Final = (
    "activated_successor_budget_id",
    "created_unix_ns",
    "decision",
    "durable_row_intents_created",
    "fetch_eligible",
    "network_actions_performed",
    "package_aggregate_sha256",
    "package_lock_record_sha256",
    "preflight_authority_record_sha256",
    "record_sha256",
    "runtime_manifest",
    "runtime_manifest_sha256",
    "schema_version",
    "successor_budget_definition_id",
    "supersession_authority_record_sha256",
)
INDEPENDENT_GO_KEYS: Final = (
    "activated_successor_budget_id",
    "attempt_limit",
    "created_unix_ns",
    "created_time_externally_attested",
    "decision",
    "exact_request_sha256",
    "exact_url",
    "independent_reviewer_principal",
    "operation_id",
    "package_aggregate_sha256",
    "record_sha256",
    "redirect_limit",
    "retry_limit",
    "reviewer_is_executor_or_package_author",
    "reviewer_identity_externally_authenticated",
    "row0_success_outcome_sha256",
    "row_ordinal",
    "runtime_manifest_sha256",
    "runtime_preflight_record_sha256",
    "schema_version",
    "successor_budget_definition_id",
    "supersession_authority_record_sha256",
)
ROW_AUTHORITY_KEYS: Final = (
    "acknowledge_sendall_zero_does_not_restore_budget",
    "acknowledge_v2_row0_spent_at_durable_intent",
    "acknowledge_v2_terminal_no_retry",
    "activated_successor_budget_id",
    "authority_identity_externally_authenticated",
    "address_fallback_limit",
    "attempt_limit",
    "connect_limit",
    "created_unix_ns",
    "custody_root",
    "created_time_externally_attested",
    "expires_unix_ns",
    "expiry_time_externally_attested",
    "independent_go_record_sha256",
    "exact_request_bytes",
    "exact_request_sha256",
    "exact_url",
    "operation_id",
    "package_aggregate_sha256",
    "package_lock_record_sha256",
    "preflight_authority_record_sha256",
    "runtime_manifest_sha256",
    "runtime_preflight_record_sha256",
    "negated_or_revoked",
    "normalized_visible_text",
    "normalized_visible_text_sha256",
    "normalized_visible_text_utf8_bytes",
    "record_sha256",
    "resolver_child_fork_site_limit",
    "resolver_high_level_call_limit",
    "socket_instance_limit",
    "tls_wrap_limit",
    "request_send_limit",
    "retry_limit",
    "redirect_limit",
    "row_ordinal",
    "row1_may_consume",
    "schema_version",
    "supersession_authority_record_sha256",
    "successor_budget_definition_id",
    "successor_budget_scope",
    "v4_package_aggregate_sha256",
    "v4_machine_raw_sha256",
    "v4_machine_semantic_sha256",
    "v2_package_aggregate_sha256",
    "v2_intent_raw_sha256",
    "v2_intent_semantic_sha256",
    "v2_error_raw_sha256",
    "v2_error_semantic_sha256",
    "v2_outcome_raw_sha256",
    "v2_outcome_semantic_sha256",
    "v2_receipts_reused",
    "version_or_root_reset_spent_budget",
)
SUCCESSOR_BUDGET_SPEND_KEYS: Final = (
    "acknowledge_sendall_zero_does_not_restore_budget",
    "acknowledge_v2_row0_spent_at_durable_intent",
    "acknowledge_v2_terminal_no_retry",
    "activated_successor_budget_id",
    "attempt_limit",
    "address_fallback_limit",
    "authority_record_sha256",
    "authority_expires_unix_ns",
    "authority_negated_or_revoked",
    "authority_revocation_slot_absent",
    "connect_limit",
    "created_unix_ns",
    "exact_request_bytes",
    "exact_request_sha256",
    "exact_url",
    "operation_id",
    "package_aggregate_sha256",
    "package_lock_record_sha256",
    "preflight_authority_record_sha256",
    "runtime_manifest_sha256",
    "runtime_preflight_record_sha256",
    "independent_go_record_sha256",
    "supersession_authority_record_sha256",
    "record_sha256",
    "redirect_limit",
    "request_send_limit",
    "resolver_high_level_call_limit",
    "resolver_child_fork_site_limit",
    "retry_limit",
    "row1_may_consume",
    "row_ordinal",
    "schema_version",
    "successor_budget_definition_id",
    "successor_budget_scope",
    "tls_wrap_limit",
    "socket_instance_limit",
    "custody_root",
    "v4_package_aggregate_sha256",
    "v4_machine_raw_sha256",
    "v4_machine_semantic_sha256",
    "v2_package_aggregate_sha256",
    "v2_intent_raw_sha256",
    "v2_intent_semantic_sha256",
    "v2_error_raw_sha256",
    "v2_error_semantic_sha256",
    "v2_outcome_raw_sha256",
    "v2_outcome_semantic_sha256",
    "v2_attempt_spend_acknowledged",
    "v2_receipts_reused",
    "version_or_root_reset_spent_budget",
)
INTENT_KEYS: Final = (
    "address_fallback_limit",
    "application_retry_or_fallback_limit",
    "attempt_limit",
    "authority_record_sha256",
    "connect_limit",
    "created_unix_ns",
    "custody_root",
    "custody_root_after_row_mkdir",
    "encrypted_wire_bytes_claimed_exact",
    "exact_plaintext_http_bytes_passed_to_tls_only",
    "exact_request_sha256",
    "exact_url",
    "independent_go_record_sha256",
    "operation_id",
    "package_aggregate_sha256",
    "precreated_sidecars",
    "record_sha256",
    "redirect_limit",
    "request_send_limit",
    "resolver_high_level_call_limit",
    "resolver_packet_count_wire_ttl_cache_server_bound",
    "retry_limit",
    "row0_success_outcome_sha256",
    "row_directory",
    "row_ordinal",
    "runtime_manifest_sha256",
    "runtime_preflight_record_sha256",
    "schema_version",
    "scientific_entropy_authorized",
    "successor_budget_spend_raw_sha256",
    "successor_budget_spend_record_sha256",
    "terminal_contract",
    "tls_transport_entropy_authorized_by_exact_row_authority",
    "tcp_retransmission_tls_record_behavior_and_os_scheduling_bound",
)
OUTCOME_KEYS: Final = (
    "address_fallback_used",
    "approval_created",
    "created_unix_ns",
    "custody_root_final",
    "error_record_sha256",
    "exact_url",
    "intent_record_sha256",
    "official_source_version_or_license_verified",
    "operation_id",
    "qualified_root_page_observation",
    "record_sha256",
    "redirect_followed",
    "request_emission_state",
    "resolver_child_fork_site_count",
    "resolver_high_level_call_count",
    "resolver_packet_count_wire_ttl_cache_server_bound",
    "resolver_rows",
    "retry_permitted",
    "row_ordinal",
    "row_directory_final",
    "schema_version",
    "sidecar_receipts",
    "socket_instance_count",
    "connect_call_count",
    "tls_wrap_call_count",
    "sendall_call_count",
    "terminal_state",
    "tracker_or_science_effect",
)

O_NOFOLLOW: Final = getattr(os, "O_NOFOLLOW", 0)
O_DIRECTORY: Final = getattr(os, "O_DIRECTORY", 0)
FILE_CREATE_FLAGS: Final = os.O_WRONLY | os.O_CREAT | os.O_EXCL | O_NOFOLLOW
SIDECAR_CREATE_FLAGS: Final = os.O_RDWR | os.O_CREAT | os.O_EXCL | O_NOFOLLOW
DIR_OPEN_FLAGS: Final = os.O_RDONLY | O_DIRECTORY | O_NOFOLLOW
READ_FLAGS: Final = os.O_RDONLY | O_NOFOLLOW


@dataclass(frozen=True)
class ExactOperation:
    ordinal: int
    operation_id: str
    domain: str
    host: str
    path: str
    url: str
    row_basename: str
    request_bytes: bytes


_REQUEST_0: Final = (
    b"GET /content/challenge-2012/1.0.0/ HTTP/1.1\r\n"
    b"Host: physionet.org\r\n"
    b"User-Agent: heterodiff-precontact-public-doc-recon-v2/2.0\r\n"
    b"Accept: text/html, application/xhtml+xml;q=0.9, text/plain;q=0.8\r\n"
    b"Accept-Encoding: identity\r\n"
    b"Cache-Control: no-cache\r\n"
    b"Pragma: no-cache\r\n"
    b"Connection: close\r\n"
    b"\r\n"
)
_REQUEST_1: Final = (
    b"GET /dataset/502/online+retail+ii HTTP/1.1\r\n"
    b"Host: archive.ics.uci.edu\r\n"
    b"User-Agent: heterodiff-precontact-public-doc-recon-v2/2.0\r\n"
    b"Accept: text/html, application/xhtml+xml;q=0.9, text/plain;q=0.8\r\n"
    b"Accept-Encoding: identity\r\n"
    b"Cache-Control: no-cache\r\n"
    b"Pragma: no-cache\r\n"
    b"Connection: close\r\n"
    b"\r\n"
)

OPERATIONS: Final = (
    ExactOperation(
        0,
        "SB2-PUBLIC-ROOT-PHYSIONET-000",
        "PhysioNet",
        "physionet.org",
        "/content/challenge-2012/1.0.0/",
        "https://physionet.org/content/challenge-2012/1.0.0/",
        "row0-physionet-root-v1",
        _REQUEST_0,
    ),
    ExactOperation(
        1,
        "SB2-PUBLIC-ROOT-UCI-001",
        "UCI Machine Learning Repository",
        "archive.ics.uci.edu",
        "/dataset/502/online+retail+ii",
        "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
        "row1-uci-online-retail-ii-root-v1",
        _REQUEST_1,
    ),
)

SIDECAR_BASENAMES: Final = (
    "request.raw",
    "response-head.raw",
    "transfer-body.raw",
    "decoded-entity.raw",
    "tls-metadata.raw",
    "stderr.raw",
    "overflow-witness.raw",
)

class ExecutorError(RuntimeError):
    """Fail-closed base exception."""


class GateError(ExecutorError):
    """A pre-network gate failed."""


class CustodyError(ExecutorError):
    """An exclusive custody invariant failed."""


class ProtocolError(ExecutorError):
    """The retained HTTP response is ambiguous or malformed."""


class ScopeError(ExecutorError):
    """The exact root-page scope was violated."""


class ContentError(ExecutorError):
    """The response cannot be treated as a bounded public text page."""


_PARENT_PARSER: Any = None


def _ensure_parent_parser() -> Any:
    """Load only the byte-pinned accepted v2 semantic parser."""

    global _PARENT_PARSER
    if _PARENT_PARSER is not None:
        return _PARENT_PARSER
    path = os.path.join(PACKAGE_ROOT, PARENT_PARSER_RELATIVE_PATH)
    raw, receipt = _read_regular_path_nofollow(path, 200_000)
    if (
        receipt["sha256"] != PARENT_PARSER_RAW_SHA256
        or receipt["size"] != 91_141
    ):
        raise GateError("accepted v2 parser raw binding mismatch")
    name = "_heterodiff_accepted_solo_block2_parser_v2"
    if name in sys.modules:
        raise GateError("accepted v2 parser module name prepopulated")
    # Compile the exact bytes read from the same no-follow descriptor that
    # produced the admitted receipt.  Path import loaders may reopen the path
    # and may read a pre-existing .pyc even under ``-B`` (which only disables
    # cache writes), so they are deliberately outside this trust boundary.
    module = type(os)(name)
    module.__file__ = path
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    sys.modules[name] = module
    try:
        code = compile(raw, path, "exec", dont_inherit=True, optimize=0)
        exec(code, module.__dict__)
        if module.EXECUTOR_CONTRACT_SHA256 != PARENT_PARSER_CONTRACT_SHA256:
            raise GateError("accepted v2 parser semantic contract drift")
        if module.OPERATION_ROSTER_SHA256 != PARENT_OPERATION_ROSTER_SHA256:
            raise GateError("accepted v2 parser operation roster drift")
        if (
            module.OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256
            != OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256
            or len(module.OUTCOME_DIAGNOSTIC_FIELD_TYPES) != 36
        ):
            raise GateError("accepted v2 diagnostic roster drift")
        for ordinal, operation in enumerate(OPERATIONS):
            spec_record = module.operation_spec(ordinal)
            if (
                spec_record["operation_id"] != operation.operation_id
                or spec_record["url"] != operation.url
                or module.exact_request_bytes(ordinal) != operation.request_bytes
            ):
                raise GateError("accepted v2 operation/request mismatch")
    except BaseException:
        del sys.modules[name]
        raise
    _PARENT_PARSER = module
    return module


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise GateError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _self_digest(value: Mapping[str, Any]) -> str:
    clone = dict(value)
    if "record_sha256" not in clone:
        raise GateError("record_sha256 absent")
    clone["record_sha256"] = None
    return _sha256(_canonical_bytes(clone))


def _parse_canonical_record(
    raw: bytes,
    *,
    schema: str,
    exact_keys: Sequence[str] | None = None,
) -> dict[str, Any]:
    if not raw or len(raw) > MAX_CANONICAL_RECEIPT_BYTES:
        raise GateError("canonical receipt size invalid")
    try:
        value = json.loads(raw, object_pairs_hook=_strict_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise GateError("canonical receipt parse failure") from exc
    if type(value) is not dict:
        raise GateError("canonical receipt must be an object")
    if _canonical_bytes(value) != raw:
        raise GateError("receipt is not exact canonical JSON plus LF")
    if exact_keys is not None and list(value) != sorted(exact_keys):
        raise GateError("receipt key roster mismatch")
    if value.get("schema_version") != schema:
        raise GateError("receipt schema mismatch")
    digest = value.get("record_sha256")
    if type(digest) is not str or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise GateError("receipt self digest malformed")
    if digest != _self_digest(value):
        raise GateError("receipt self digest mismatch")
    return value


def _parse_nonself_canonical(raw: bytes, label: str) -> dict[str, Any]:
    if not raw or len(raw) > MAX_CANONICAL_RECEIPT_BYTES:
        raise GateError(f"{label} size invalid")
    try:
        value = json.loads(raw, object_pairs_hook=_strict_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise GateError(f"{label} parse failure") from exc
    if type(value) is not dict or _canonical_bytes(value) != raw:
        raise GateError(f"{label} is not canonical JSON plus LF")
    return value


def _hash_fd(fd: int, *, limit: int | None = None) -> tuple[str, int]:
    os.lseek(fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    total = 0
    while True:
        chunk = os.read(fd, 131_072)
        if not chunk:
            break
        total += len(chunk)
        if limit is not None and total > limit:
            raise GateError("file exceeds admitted ceiling")
        digest.update(chunk)
    os.lseek(fd, 0, os.SEEK_SET)
    return digest.hexdigest(), total


def _open_absolute_componentwise_nofollow(path: str, final_flags: int) -> int:
    """Open an exact absolute path without following any path component."""

    if (
        type(path) is not str
        or not path.startswith("/")
        or path == "/"
        or "\x00" in path
        or "//" in path
        or path.endswith("/")
        or os.path.normpath(path) != path
    ):
        raise GateError("runtime input path must be exact normalized absolute")
    components = path.split("/")[1:]
    if not components or any(part in {"", ".", ".."} for part in components):
        raise GateError("runtime input path component is unsafe")
    dirfd = os.open("/", DIR_OPEN_FLAGS)
    try:
        for component in components[:-1]:
            nextfd = os.open(component, DIR_OPEN_FLAGS, dir_fd=dirfd)
            os.close(dirfd)
            dirfd = nextfd
        return os.open(
            components[-1], final_flags | O_NOFOLLOW, dir_fd=dirfd
        )
    finally:
        os.close(dirfd)


def _receipt_for_open_regular(
    path: str, fd: int, *, raw_cap: int | None = None
) -> tuple[bytes | None, dict[str, Any]]:
    before = os.fstat(fd)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise GateError(f"non-regular or multiply linked runtime input: {path}")
    if raw_cap is None:
        digest, size = _hash_fd(fd)
        raw: bytes | None = None
    else:
        raw = _read_all_fd(fd, raw_cap)
        digest = _sha256(raw)
        size = len(raw)
        os.lseek(fd, 0, os.SEEK_SET)
    after = os.fstat(fd)
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise GateError(f"runtime input changed during read: {path}")
    return raw, {
        "path": path,
        "sha256": digest,
        "size": size,
        "device": before.st_dev,
        "inode": before.st_ino,
        "uid": before.st_uid,
        "gid": before.st_gid,
        "mode_octal": f"{stat.S_IMODE(before.st_mode):04o}",
        "nlink": before.st_nlink,
        "mtime_ns": before.st_mtime_ns,
        "ctime_ns": before.st_ctime_ns,
    }


def _read_regular_path_nofollow(
    path: str, cap: int
) -> tuple[bytes, dict[str, Any]]:
    fd = _open_absolute_componentwise_nofollow(path, os.O_RDONLY)
    try:
        raw, receipt = _receipt_for_open_regular(path, fd, raw_cap=cap)
        assert raw is not None
        return raw, receipt
    finally:
        os.close(fd)


def _hash_path_nofollow(path: str) -> dict[str, Any]:
    fd = _open_absolute_componentwise_nofollow(path, os.O_RDONLY)
    try:
        _raw, receipt = _receipt_for_open_regular(path, fd)
        return receipt
    finally:
        os.close(fd)


def _path_entry_receipt_nofollow(path: str) -> dict[str, Any]:
    fd = _open_absolute_componentwise_nofollow(path, os.O_RDONLY)
    try:
        st = os.fstat(fd)
        if stat.S_ISREG(st.st_mode):
            _raw, receipt = _receipt_for_open_regular(path, fd)
            return {"path": path, "exists": True, "kind": "regular", "receipt": receipt}
        if stat.S_ISDIR(st.st_mode):
            return {
                "path": path,
                "exists": True,
                "kind": "directory",
                "device": st.st_dev,
                "inode": st.st_ino,
                "uid": st.st_uid,
                "gid": st.st_gid,
                "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}",
                "nlink": st.st_nlink,
                "mtime_ns": st.st_mtime_ns,
                "ctime_ns": st.st_ctime_ns,
            }
        raise GateError("runtime path entry has unsupported type")
    finally:
        os.close(fd)


def _read_all_fd(fd: int, cap: int) -> bytes:
    out = bytearray()
    while True:
        chunk = os.read(fd, min(131_072, cap + 1 - len(out)))
        if not chunk:
            return bytes(out)
        out.extend(chunk)
        if len(out) > cap:
            raise GateError("receipt read ceiling exceeded")


def _validate_regular_receipt_stat(st: os.stat_result, *, mode: int) -> None:
    if not stat.S_ISREG(st.st_mode):
        raise GateError("receipt is not regular")
    if stat.S_IMODE(st.st_mode) != mode:
        raise GateError("receipt mode mismatch")
    if st.st_uid != os.getuid() or st.st_gid != os.getgid() or st.st_nlink != 1:
        raise GateError("receipt owner/group/link invariant failed")


def _read_receipt_at(
    dirfd: int,
    basename: str,
    *,
    schema: str,
    mode: int = 0o600,
    exact_keys: Sequence[str] | None = None,
) -> tuple[dict[str, Any], bytes, os.stat_result]:
    _require_basename(basename)
    fd = os.open(basename, READ_FLAGS, dir_fd=dirfd)
    try:
        before = os.fstat(fd)
        _validate_regular_receipt_stat(before, mode=mode)
        raw = _read_all_fd(fd, MAX_CANONICAL_RECEIPT_BYTES)
        os.fsync(fd)
        after = os.fstat(fd)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
            before.st_mode,
            before.st_uid,
            before.st_gid,
            before.st_nlink,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
            after.st_mode,
            after.st_uid,
            after.st_gid,
            after.st_nlink,
        ):
            raise GateError("receipt changed during read")
    finally:
        os.close(fd)
    return _parse_canonical_record(
        raw, schema=schema, exact_keys=exact_keys
    ), raw, before


def _require_raw_receipt_forward_link(
    claimed_sha256: Any, raw_receipt: bytes, label: str
) -> None:
    """Require a forward link to the exact canonical receipt bytes."""

    if (
        type(claimed_sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", claimed_sha256) is None
        or claimed_sha256 != _sha256(raw_receipt)
    ):
        raise GateError(f"{label} raw receipt forward link mismatch")


def _require_basename(name: str) -> None:
    if (
        type(name) is not str
        or not name
        or name in {".", ".."}
        or "/" in name
        or "\x00" in name
    ):
        raise GateError("unsafe basename")


def _open_root(path: str) -> tuple[int, os.stat_result]:
    if type(path) is not str or path != V5_OPERATIONAL_ROOT:
        raise GateError("custody root is not the one exact V5 operational root")
    if (
        type(path) is not str
        or not path.startswith("/")
        or path == "/"
        or "\x00" in path
        or "//" in path
        or path.endswith("/")
        or os.path.normpath(path) != path
    ):
        raise GateError("custody root must be an exact normalized absolute path")
    components = path.split("/")[1:]
    if not components or any(part in {"", ".", ".."} or "/" in part for part in components):
        raise GateError("custody root contains an unsafe path component")
    fd = os.open("/", DIR_OPEN_FLAGS)
    try:
        for component in components:
            next_fd = os.open(component, DIR_OPEN_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = next_fd
    except BaseException:
        os.close(fd)
        raise
    st = os.fstat(fd)
    if not stat.S_ISDIR(st.st_mode):
        os.close(fd)
        raise GateError("custody root is not a directory")
    if stat.S_IMODE(st.st_mode) != 0o700 or st.st_uid != os.getuid():
        os.close(fd)
        raise GateError("custody root owner/mode mismatch")
    return fd, st


def _root_identity(path: str, st: os.stat_result) -> dict[str, Any]:
    return {
        "absolute_path": path,
        "device": st.st_dev,
        "inode": st.st_ino,
        "uid": st.st_uid,
        "gid": st.st_gid,
        "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}",
        "nlink": st.st_nlink,
    }


def _runtime_root_identity(path: str, st: os.stat_result) -> dict[str, Any]:
    """Stable root projection across the two admitted row-directory additions."""

    return {
        "absolute_path": path,
        "device": st.st_dev,
        "inode": st.st_ino,
        "uid": st.st_uid,
        "gid": st.st_gid,
        "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}",
    }


def _require_machine_bound_root(
    machine: Mapping[str, Any], path: str, st: os.stat_result, rootfd: int
) -> None:
    expected = machine.get("operational_custody_root")
    if type(expected) is not dict:
        raise GateError("machine-bound operational root absent")
    static_actual = {
        "absolute_path": path,
        "device": st.st_dev,
        "inode": st.st_ino,
        "uid": st.st_uid,
        "gid": st.st_gid,
        "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}",
    }
    for key, value in static_actual.items():
        if expected.get(key) != value or type(expected.get(key)) is not type(value):
            raise GateError(f"operational root binding mismatch: {key}")
    compiled = {
        "absolute_path": V5_OPERATIONAL_ROOT,
        "device": V5_ROOT_DEVICE,
        "inode": V5_ROOT_INODE,
        "uid": V5_ROOT_UID,
        "gid": V5_ROOT_GID,
        "mode_octal": "0700",
    }
    if static_actual != compiled:
        raise GateError("live operational root differs from compiled V5 identity")
    base_nlink = expected.get("nlink_at_package_construction")
    names = os.listdir(rootfd)
    if (
        type(base_nlink) is not int
        or len(names) != len(set(names))
        or st.st_nlink < base_nlink
        or st.st_nlink > base_nlink + len(names)
    ):
        raise GateError("operational root link count outside live-entry bound")


def _exclusive_canonical_at(
    dirfd: int,
    basename: str,
    record: dict[str, Any],
) -> tuple[str, os.stat_result]:
    _require_basename(basename)
    if record.get("record_sha256") is not None:
        raise CustodyError("new record must begin with null self digest")
    record["record_sha256"] = _self_digest(record)
    raw = _canonical_bytes(record)
    fd = os.open(basename, FILE_CREATE_FLAGS, 0o600, dir_fd=dirfd)
    try:
        st0 = os.fstat(fd)
        _validate_regular_receipt_stat(st0, mode=0o600)
        _write_all(fd, raw)
        os.fsync(fd)
        st1 = os.fstat(fd)
        _validate_regular_receipt_stat(st1, mode=0o600)
        if (st0.st_dev, st0.st_ino) != (st1.st_dev, st1.st_ino):
            raise CustodyError("exclusive receipt identity changed")
    finally:
        os.close(fd)
    os.fsync(dirfd)
    return _sha256(raw), st1


def _reopen_exact_digest_at(
    dirfd: int, basename: str, expected_sha256: str, *, mode: int = 0o600
) -> os.stat_result:
    _require_basename(basename)
    fd = os.open(basename, READ_FLAGS, dir_fd=dirfd)
    try:
        before = os.fstat(fd)
        _validate_regular_receipt_stat(before, mode=mode)
        digest, _ = _hash_fd(fd, limit=MAX_CANONICAL_RECEIPT_BYTES)
        os.fsync(fd)
        after = os.fstat(fd)
        _validate_regular_receipt_stat(after, mode=mode)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
            before.st_mode,
            before.st_uid,
            before.st_gid,
            before.st_nlink,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
            after.st_mode,
            after.st_uid,
            after.st_gid,
            after.st_nlink,
        ):
            raise CustodyError("reopened receipt changed during verification")
        if digest != expected_sha256:
            raise CustodyError("reopened receipt digest mismatch")
        return after
    finally:
        os.close(fd)


def _identity_digest_at(
    dirfd: int, basename: str, *, mode: int = 0o600
) -> dict[str, Any]:
    """Capture content plus identity for a custody-root receipt."""

    _require_basename(basename)
    fd = os.open(basename, READ_FLAGS, dir_fd=dirfd)
    try:
        before = os.fstat(fd)
        _validate_regular_receipt_stat(before, mode=mode)
        digest, size = _hash_fd(fd, limit=MAX_CANONICAL_RECEIPT_BYTES)
        after = os.fstat(fd)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise CustodyError("gate receipt changed during identity capture")
        return {
            "basename": basename,
            "sha256": digest,
            "bytes": size,
            "device": before.st_dev,
            "inode": before.st_ino,
            "uid": before.st_uid,
            "gid": before.st_gid,
            "mode_octal": f"{stat.S_IMODE(before.st_mode):04o}",
            "nlink": before.st_nlink,
            "mtime_ns": before.st_mtime_ns,
            "ctime_ns": before.st_ctime_ns,
        }
    finally:
        os.close(fd)


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    sent = 0
    while sent < len(view):
        count = os.write(fd, view[sent:])
        if count <= 0:
            raise CustodyError("short local custody write")
        sent += count


def _require_fd_baseline(allowed: frozenset[int] = frozenset()) -> None:
    unexpected: list[int] = []
    # /dev/fd enumerates the entire live descriptor table.  os.listdir's own
    # temporary directory descriptor is closed before the F_GETFD check and is
    # therefore ignored, while inherited descriptors above 1023 remain visible.
    try:
        candidates = sorted(
            {int(name) for name in os.listdir("/dev/fd") if name.isdecimal()}
        )
    except (OSError, ValueError) as exc:
        raise GateError("cannot enumerate complete descriptor policy") from exc
    for fd in candidates:
        if fd < 3:
            continue
        if fd in allowed:
            continue
        try:
            fcntl.fcntl(fd, fcntl.F_GETFD)
        except OSError as exc:
            if exc.errno == errno.EBADF:
                continue
            raise GateError("cannot inspect descriptor policy") from exc
        unexpected.append(fd)
    if unexpected:
        raise GateError(f"unexpected inherited descriptors: {unexpected}")


def _close_all_fds_except(allowed: frozenset[int]) -> None:
    """Close the complete child descriptor roster except explicit survivors."""

    try:
        candidates = sorted(
            {int(name) for name in os.listdir("/dev/fd") if name.isdecimal()},
            reverse=True,
        )
    except (OSError, ValueError):
        os._exit(126)
    for fd in candidates:
        if fd in allowed:
            continue
        try:
            os.close(fd)
        except OSError as exc:
            if exc.errno != errno.EBADF:
                os._exit(126)


def _normalize_stdio_to_devnull() -> None:
    """Make preflight and later attempts independent of terminal/pipe inodes."""

    fd = os.open("/dev/null", os.O_RDWR | O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISCHR(st.st_mode) or st.st_uid != 0:
            raise GateError("/dev/null identity is not admitted")
        for target in (0, 1, 2):
            os.dup2(fd, target, inheritable=False)
    finally:
        if fd > 2:
            os.close(fd)


def _stdio_receipts() -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for fd in (0, 1, 2):
        st = os.fstat(fd)
        kind = (
            "regular"
            if stat.S_ISREG(st.st_mode)
            else "character"
            if stat.S_ISCHR(st.st_mode)
            else "fifo"
            if stat.S_ISFIFO(st.st_mode)
            else "socket"
            if stat.S_ISSOCK(st.st_mode)
            else "other"
        )
        receipts.append(
            {
                "fd": fd,
                "kind": kind,
                "device": st.st_dev,
                "inode": st.st_ino,
                "uid": st.st_uid,
                "gid": st.st_gid,
                "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}",
            }
        )
    return receipts


def _require_machine_state(machine: Mapping[str, Any]) -> None:
    if machine.get("state") != MACHINE_STATE:
        raise GateError("machine state is not the frozen V5 successor state")


def _require_machine_non_effects(machine: Mapping[str, Any]) -> None:
    effects = machine.get("activation_checklist_effects")
    slots = machine.get("activation_operational_slots")
    if (
        type(effects) is not dict
        or effects.get("v5_fetch_performed") is not False
        or effects.get("v5_resolver_call_performed") is not False
        or effects.get("v5_durable_row_intent_created") is not False
        or effects.get("v5_operational_receipt_created") is not False
        or effects.get("v5_successor_budget_spent") is not False
        or type(slots) is not dict
        or any(value is not None for value in slots.values())
        or type(machine.get("operational_custody_root")) is not dict
    ):
        raise GateError("machine falsely reports pre-activation V5 activity")


def _load_machine() -> tuple[dict[str, Any], bytes]:
    path = os.path.join(PACKAGE_ROOT, MACHINE_RELATIVE_PATH)
    raw, _receipt = _read_regular_path_nofollow(
        path, MAX_CANONICAL_RECEIPT_BYTES
    )
    machine = _parse_canonical_record(raw, schema=MACHINE_SCHEMA)
    _require_machine_state(machine)
    _require_machine_non_effects(machine)
    contract = machine.get("executor_contract")
    if (
        type(contract) is not dict
        or contract.get("executing_image_one_open_attestation_claimed") is not False
        or contract.get("concurrent_same_uid_path_substitution_excluded") is not False
        or contract.get("registrar_identity_externally_authenticated") is not False
        or contract.get("registrar_time_externally_attested") is not False
        or contract.get("registrar_identity_and_time_are_caller_assertions") is not True
    ):
        raise GateError("machine omits executing-image/identity/time nonclaims")
    source = _hash_path_nofollow(os.path.join(PACKAGE_ROOT, SOURCE_RELATIVE_PATH))
    expected = machine.get("executor_source_binding")
    if type(expected) is not dict or source["sha256"] != expected.get("sha256"):
        raise GateError("running executor bytes are not machine-bound")
    if source["size"] != expected.get("bytes"):
        raise GateError("running executor length is not machine-bound")
    return machine, raw


def _require_exact_python_runtime_flags() -> dict[str, Any]:
    actual = {
        name: getattr(sys.flags, name)
        for name in EXPECTED_PYTHON_FLAGS
    }
    if actual != EXPECTED_PYTHON_FLAGS:
        raise GateError("production Python flag roster mismatch")
    if sys._xoptions != {} or sys.warnoptions != []:
        raise GateError("production Python extended/warning option roster is not empty")
    return {
        **actual,
        "xoptions": {},
        "warnoptions": [],
    }


def _require_production_process(
    command: str,
    root: str,
    row: int | None,
    extra_argv: Sequence[str] = (),
) -> None:
    source_path = os.path.join(PACKAGE_ROOT, SOURCE_RELATIVE_PATH)
    expected_argv = [source_path, command, root]
    if row is not None:
        expected_argv.append(str(row))
    expected_argv.extend(extra_argv)
    if __name__ != "__main__" or sys.argv != expected_argv:
        raise GateError("production functions require exact direct-script CLI surface")
    if sys.executable != EXPECTED_INTERPRETER:
        raise GateError("production launcher interpreter path mismatch")
    expected_original_argv = [
        EXPECTED_INTERPRETER,
        "-I",
        "-S",
        "-B",
        *expected_argv,
    ]
    if sys.orig_argv != expected_original_argv:
        raise GateError("production original argv must be exact interpreter -I -S -B CLI")
    _require_exact_python_runtime_flags()
    if dict(os.environ) != {
        "__CF_USER_TEXT_ENCODING": "0x1F5:0x0:0x0",
        "LC_CTYPE": "C.UTF-8",
    }:
        raise GateError("production launcher environment is not exact env -i output")


def _current_package_inputs(
    machine: Mapping[str, Any], machine_raw: bytes
) -> tuple[list[dict[str, Any]], str]:
    bindings = machine.get("package_bindings")
    if type(bindings) is not list or len(bindings) != 5:
        raise GateError("package binding count mismatch")
    for binding in bindings:
        if type(binding) is not dict or set(binding) != {
            "bytes",
            "mode_octal",
            "mtime_ns",
            "nlink",
            "path",
            "sha256",
        }:
            raise GateError("package binding schema mismatch")
        relative = binding["path"]
        if (
            type(relative) is not str
            or relative.startswith("/")
            or ".." in relative.split("/")
            or "\x00" in relative
        ):
            raise GateError("package binding path unsafe")
        actual = _hash_path_nofollow(os.path.join(PACKAGE_ROOT, relative))
        expected_projection = {
            "path": relative,
            "sha256": actual["sha256"],
            "bytes": actual["size"],
            "mode_octal": actual["mode_octal"],
            "nlink": actual["nlink"],
            "mtime_ns": actual["mtime_ns"],
        }
        if binding != expected_projection:
            raise GateError(f"package-bound file drift: {relative}")
    aggregate_payload = {
        "schema_version": "heterodiff-solo-block2-runtime-package-aggregate-v5",
        "machine_raw_sha256": _sha256(machine_raw),
        "machine_semantic_sha256": machine.get("record_sha256"),
        "bound_file_receipts": bindings,
    }
    return bindings, _sha256(_canonical_bytes(aggregate_payload))


def _package_runtime_identity_snapshot(machine: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Capture same-inode package identities for the post-intent byte stop."""

    paths = [MACHINE_RELATIVE_PATH, PARENT_PARSER_RELATIVE_PATH]
    bindings = machine.get("package_bindings")
    if type(bindings) is not list:
        raise GateError("package binding roster unavailable")
    paths.extend(item.get("path") for item in bindings if type(item) is dict)
    if any(type(path) is not str for path in paths) or len(paths) != 7:
        raise GateError("package runtime identity roster invalid")
    if len(set(paths)) != len(paths):
        raise GateError("package runtime identity roster contains duplicates")
    return [
        _hash_path_nofollow(os.path.join(PACKAGE_ROOT, path)) for path in paths
    ]


def _load_package_lock(rootfd: int, machine: Mapping[str, Any], machine_raw: bytes) -> dict[str, Any]:
    lock, _, lock_st = _read_receipt_at(
        rootfd,
        "package-lock.json",
        schema=PACKAGE_LOCK_SCHEMA,
        exact_keys=PACKAGE_LOCK_KEYS,
    )
    if lock.get("decision") != "INDEPENDENT_PACKAGE_BYTES_GO":
        raise GateError("package lock decision is not exact GO")
    if lock.get("machine_raw_sha256") != _sha256(machine_raw):
        raise GateError("package lock machine raw digest mismatch")
    if lock.get("machine_semantic_sha256") != machine.get("record_sha256"):
        raise GateError("package lock machine semantic digest mismatch")
    bindings, aggregate = _current_package_inputs(machine, machine_raw)
    if lock.get("bound_file_receipts") != bindings:
        raise GateError("package lock file roster mismatch")
    if lock.get("package_aggregate_sha256") != aggregate:
        raise GateError("package aggregate mismatch")
    if lock.get("reviewer_is_package_author") is not False:
        raise GateError("package review independence not asserted")
    if (
        lock.get("reviewer_identity_externally_authenticated") is not False
        or lock.get("created_time_externally_attested") is not False
    ):
        raise GateError("package lock overclaims identity or trusted time")
    reviewer = lock.get("independent_reviewer_principal")
    created = lock.get("created_unix_ns")
    if type(reviewer) is not str or not reviewer or type(created) is not int:
        raise GateError("package lock reviewer/chronology invalid")
    machine_receipt = _hash_path_nofollow(
        os.path.join(PACKAGE_ROOT, MACHINE_RELATIVE_PATH)
    )
    if created <= max(
        [item["mtime_ns"] for item in bindings] + [machine_receipt["mtime_ns"]]
    ):
        raise GateError("package lock does not postdate stopped package bytes")
    if lock_st.st_mtime_ns < created:
        raise GateError("package lock file mtime predates its creation claim")
    return lock


def _dyld_images() -> list[str]:
    lib = ctypes.CDLL(None)
    count_fn = lib._dyld_image_count
    count_fn.restype = ctypes.c_uint32
    name_fn = lib._dyld_get_image_name
    name_fn.argtypes = [ctypes.c_uint32]
    name_fn.restype = ctypes.c_char_p
    count = int(count_fn())
    if count <= 0 or count > 4096:
        raise GateError("dyld image count outside admitted bound")
    names: list[str] = []
    for index in range(count):
        raw = name_fn(index)
        if raw is None:
            raise GateError("dyld image name unavailable")
        name = os.fsdecode(raw)
        if not os.path.isabs(name):
            raise GateError("dyld image path is not absolute")
        names.append(name)
    if len(names) != len(set(names)):
        raise GateError("duplicate dyld image path")
    return sorted(names)


def _dyld_receipts() -> dict[str, Any]:
    image_paths = _dyld_images()
    image_receipts: list[dict[str, Any]] = []
    for path in image_paths:
        try:
            item = _hash_path_nofollow(path)
        except FileNotFoundError:
            item = {"path": path, "storage": "macos_dyld_shared_cache"}
        image_receipts.append(item)
    return {
        "loaded_images": image_receipts,
        "arm64e_shared_cache_components": [
            _hash_path_nofollow(path) for path in DYLD_CACHE_PATHS
        ],
    }


def _file_backed_modules() -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for name, module in sorted(sys.modules.items()):
        if module is None:
            continue
        path = getattr(module, "__file__", None)
        if path is None:
            origin = getattr(getattr(module, "__spec__", None), "origin", None)
            receipts.append({"module": name, "kind": "builtin_or_frozen", "origin": origin})
            continue
        absolute = os.path.abspath(path)
        source_or_extension = _hash_path_nofollow(absolute)
        cached = getattr(module, "__cached__", None)
        cached_receipt: dict[str, Any]
        if type(cached) is str:
            try:
                exact_cached = _hash_path_nofollow(os.path.abspath(cached))
            except FileNotFoundError:
                cached_receipt = {"exists": False, "path": os.path.abspath(cached)}
            else:
                cached_receipt = {"exists": True, "receipt": exact_cached}
        else:
            cached_receipt = {"exists": False, "path": None}
        receipts.append(
            {
                "module": name,
                "kind": "file",
                "source_or_extension_receipt": source_or_extension,
                "cached_bytecode_receipt": cached_receipt,
                "loader_type": type(getattr(module, "__loader__", None)).__name__,
                "spec_origin": getattr(getattr(module, "__spec__", None), "origin", None),
            }
        )
    return receipts


def _sys_path_receipts() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in sys.path:
        try:
            out.append(_path_entry_receipt_nofollow(path))
        except FileNotFoundError:
            out.append({"path": path, "exists": False})
    return out


def _capture_scutil_dns() -> dict[str, Any]:
    scutil = _hash_path_nofollow(SCUTIL_PATH)
    completed = subprocess.run(
        [SCUTIL_PATH, "--dns"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=5.0,
        env={
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "LANG": "C",
            "LC_ALL": "C",
        },
    )
    if len(completed.stdout) > MAX_SCUTIL_BYTES or len(completed.stderr) > MAX_SCUTIL_BYTES:
        raise GateError("scutil output ceiling exceeded")
    return {
        "executable": scutil,
        "argv": [SCUTIL_PATH, "--dns"],
        "returncode": completed.returncode,
        "stdout_base64": base64.b64encode(completed.stdout).decode("ascii"),
        "stdout_sha256": _sha256(completed.stdout),
        "stdout_bytes": len(completed.stdout),
        "stderr_base64": base64.b64encode(completed.stderr).decode("ascii"),
        "stderr_sha256": _sha256(completed.stderr),
        "stderr_bytes": len(completed.stderr),
        "dynamic_daemon_cache_wire_state_bound": False,
        "claim_about_dns_packet_count_ttl_cache_or_server_determinism": False,
    }


def _environment_receipt() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for key in sorted(os.environ):
        value = os.environ[key]
        raw = value.encode("utf-8", "surrogateescape")
        out.append(
            {
                "name": key,
                "value_utf8_surrogateescape_bytes": len(raw),
                "value_sha256": _sha256(raw),
            }
        )
    return out


def _normalized_mac_version() -> list[Any]:
    """Return ``platform.mac_ver`` entirely in the canonical JSON data model."""

    version, release, machine = platform.mac_ver()
    return [version, list(release), machine]


def _runtime_manifest(root_path: str, root_st: os.stat_result) -> dict[str, Any]:
    parent_parser = _ensure_parent_parser()
    if sys.executable != EXPECTED_INTERPRETER:
        raise GateError("interpreter path mismatch")
    interpreter = _hash_path_nofollow(sys.executable)
    if interpreter["sha256"] != EXPECTED_INTERPRETER_SHA256:
        raise GateError("interpreter raw digest mismatch")
    if sys.version != EXPECTED_PYTHON_VERSION:
        raise GateError("Python build string mismatch")
    if sys.implementation.cache_tag != EXPECTED_CACHE_TAG:
        raise GateError("Python cache tag mismatch")
    if ssl.OPENSSL_VERSION != EXPECTED_OPENSSL_VERSION:
        raise GateError("OpenSSL version mismatch")
    python_flags = _require_exact_python_runtime_flags()
    expected_sys_path = [
        "/Users/mahtab/.cache/codex-runtimes/codex-primary-runtime/"
        "dependencies/python/lib/python312.zip",
        "/Users/mahtab/.cache/codex-runtimes/codex-primary-runtime/"
        "dependencies/python/lib/python3.12",
        "/Users/mahtab/.cache/codex-runtimes/codex-primary-runtime/"
        "dependencies/python/lib/python3.12/lib-dynload",
    ]
    if sys.path != expected_sys_path:
        raise GateError("isolated sys.path roster mismatch")
    expected_environment = {
        "__CF_USER_TEXT_ENCODING": "0x1F5:0x0:0x0",
        "LC_CTYPE": "C.UTF-8",
    }
    if dict(os.environ) != expected_environment:
        raise GateError("production environment is not exact /usr/bin/env -i roster")
    ca = _hash_path_nofollow(EXPECTED_CA_PATH)
    if ca["sha256"] != EXPECTED_CA_SHA256:
        raise GateError("CA bytes mismatch")
    resolv = _hash_path_nofollow(RESOLV_CONF_PATH)
    hosts = _hash_path_nofollow(HOSTS_PATH)
    cwd = os.getcwd()
    cwd_st = os.stat(cwd, follow_symlinks=False)
    if not stat.S_ISDIR(cwd_st.st_mode):
        raise GateError("cwd is not a directory")
    dns_snapshot = _capture_scutil_dns()
    _require_admissible_resolver_snapshot(
        {"resolver_systemconfiguration_snapshot": dns_snapshot}
    )
    platform_value = platform.platform()
    # ``platform.mac_ver()`` returns a nested tuple for the release triplet.
    # Normalize the complete value to the JSON data model before hashing so a
    # canonical receipt survives serialize/parse without a false tuple/list
    # inequality at the immediate pre-reservation gate.
    mac_version_value = _normalized_mac_version()
    locale_value = list(locale.getlocale())
    timezone_value = list(time.tzname)
    dyld_receipts = _dyld_receipts()
    module_receipts = _file_backed_modules()
    sys_path_receipts = _sys_path_receipts()
    manifest = {
        "schema_version": "heterodiff-solo-block2-loaded-runtime-manifest-v5",
        "interpreter": interpreter,
        "launcher_env_executable": _hash_path_nofollow(ENV_PATH),
        "launcher_argv_prefix": [
            ENV_PATH,
            "-i",
            EXPECTED_INTERPRETER,
            "-I",
            "-S",
            "-B",
            os.path.join(PACKAGE_ROOT, SOURCE_RELATIVE_PATH),
        ],
        "python_version": sys.version,
        "python_cache_tag": sys.implementation.cache_tag,
        "python_implementation": sys.implementation.name,
        "openssl_version": ssl.OPENSSL_VERSION,
        "ssl_backend": "CPython built-in _ssl with statically linked OpenSSL",
        "ca": ca,
        "dyld": dyld_receipts,
        "imported_module_receipts": module_receipts,
        "sys_path_receipts": sys_path_receipts,
        "accepted_parent_parser": {
            "raw_sha256": PARENT_PARSER_RAW_SHA256,
            "semantic_contract_sha256": parent_parser.EXECUTOR_CONTRACT_SHA256,
            "operation_roster_sha256": parent_parser.OPERATION_ROSTER_SHA256,
            "diagnostic_roster_sha256": (
                parent_parser.OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256
            ),
        },
        "resolver_resolv_conf": resolv,
        "resolver_hosts": hosts,
        "resolver_systemconfiguration_snapshot": dns_snapshot,
        "resolver_call_policy": {
            "high_level_calls": 1,
            "function": "socket.getaddrinfo",
            "family": "AF_UNSPEC",
            "socket_type": "SOCK_STREAM",
            "protocol": "IPPROTO_TCP",
            "flags": "AI_ADDRCONFIG",
            "child_wait_deadline_seconds": DNS_WAIT_SECONDS,
            "underlying_packet_count_bound": False,
            "answer_wire_ttl_cache_and_server_bound": False,
            "kill_stops_system_resolver_daemon_claimed": False,
        },
        "uname": list(os.uname()),
        "platform": platform_value,
        "mac_version": mac_version_value,
        "machine": platform.machine(),
        "byteorder": sys.byteorder,
        "uid": os.getuid(),
        "gid": os.getgid(),
        "groups": sorted(os.getgroups()),
        "environment_name_value_digest_roster": _environment_receipt(),
        "exact_sys_path": list(sys.path),
        "python_flags": python_flags,
        "cwd": {
            "path": cwd,
            "device": cwd_st.st_dev,
            "inode": cwd_st.st_ino,
            "uid": cwd_st.st_uid,
            "mode_octal": f"{stat.S_IMODE(cwd_st.st_mode):04o}",
        },
        "locale": locale_value,
        "timezone": timezone_value,
        "daylight": time.daylight,
        "forced_process_umask_octal": "0077",
        "fd_policy": "ONLY_0_1_2_PLUS_EXPLICIT_RETAINED_ROOT_DIRFD",
        "stdio_receipts": _stdio_receipts(),
        "custody_root": _runtime_root_identity(root_path, root_st),
    }
    manifest["manifest_sha256"] = _sha256(_canonical_bytes(manifest))
    return manifest


def _validate_runtime_manifest_self_digest(manifest: Mapping[str, Any]) -> str:
    if type(manifest) is not dict:
        raise GateError("runtime manifest must be an exact object")
    claimed = manifest.get("manifest_sha256")
    if type(claimed) is not str or re.fullmatch(r"[0-9a-f]{64}", claimed) is None:
        raise GateError("runtime manifest digest malformed")
    payload = dict(manifest)
    del payload["manifest_sha256"]
    if _sha256(_canonical_bytes(payload)) != claimed:
        raise GateError("runtime manifest self digest mismatch")
    return claimed


def _render_supersession_authority(
    package_lock: Mapping[str, Any], root: Mapping[str, Any], activated_budget_id: str
) -> str:
    return "\n".join(
        [
            "AUTHORIZE_SOLO_BLOCK2_V5_SUCCESSOR_SUPERSESSION_AND_OFFLINE_PREFLIGHT",
            f"package_aggregate_sha256={package_lock['package_aggregate_sha256']}",
            f"package_lock_record_sha256={package_lock['record_sha256']}",
            f"v4_package_aggregate_sha256={V4_PACKAGE_AGGREGATE_SHA256}",
            f"v4_machine_raw_sha256={V4_MACHINE_RAW_SHA256}",
            f"v4_machine_semantic_sha256={V4_MACHINE_SEMANTIC_SHA256}",
            f"v2_package_aggregate_sha256={V2_PACKAGE_AGGREGATE_SHA256}",
            f"v2_intent_raw_sha256={V2_INTENT_RAW_SHA256}",
            f"v2_intent_semantic_sha256={V2_INTENT_SEMANTIC_SHA256}",
            f"v2_error_raw_sha256={V2_ERROR_RAW_SHA256}",
            f"v2_error_semantic_sha256={V2_ERROR_SEMANTIC_SHA256}",
            f"v2_outcome_raw_sha256={V2_OUTCOME_RAW_SHA256}",
            f"v2_outcome_semantic_sha256={V2_OUTCOME_SEMANTIC_SHA256}",
            f"successor_budget_definition_id={SUCCESSOR_BUDGET_DEFINITION_ID}",
            f"activated_successor_budget_id={activated_budget_id}",
            f"successor_budget_scope={SUCCESSOR_BUDGET_SCOPE}",
            f"custody_root_absolute_path={root['absolute_path']}",
            f"custody_root_device={root['device']}",
            f"custody_root_inode={root['inode']}",
            f"custody_root_uid={root['uid']}",
            f"custody_root_gid={root['gid']}",
            f"custody_root_mode_octal={root['mode_octal']}",
            f"operation_id={OPERATIONS[0].operation_id}",
            f"exact_url={OPERATIONS[0].url}",
            f"exact_request_bytes={len(OPERATIONS[0].request_bytes)}",
            f"exact_request_sha256={_sha256(OPERATIONS[0].request_bytes)}",
            "resolver_high_level_call_limit=1",
            "resolver_child_fork_site_limit=1",
            "socket_instance_limit=1",
            "connect_limit=1",
            "tls_wrap_limit=1",
            "request_send_limit=1",
            "attempt_limit=1",
            "retry_limit=0",
            "redirect_limit=0",
            "address_fallback_limit=0",
            "v2_attempt_spend_acknowledged=true",
            "acknowledge_v2_row0_spent_at_durable_intent=true",
            "acknowledge_v2_terminal_no_retry=true",
            "acknowledge_sendall_zero_does_not_restore_budget=true",
            "v2_receipts_reused=false",
            "new_version_or_root_resets_spent_budget=false",
            "row1_may_consume=false",
            "scope=ONE_NEW_GLOBAL_ROW0_SUCCESSOR_BUDGET_AND_OFFLINE_PREFLIGHT_ONLY",
            "network_or_contact_authorized=false",
            "authority_identity_externally_authenticated=false",
            "created_time_externally_attested=false",
        ]
    )


def _validate_supersession_authority(
    rootfd: int, package_lock: Mapping[str, Any], root: Mapping[str, Any]
) -> dict[str, Any]:
    authority, _, st = _read_receipt_at(
        rootfd, "supersession-authority.json",
        schema=SUPERSESSION_AUTHORITY_SCHEMA,
        exact_keys=SUPERSESSION_AUTHORITY_KEYS,
    )
    activated = authority.get("activated_successor_budget_id")
    if (
        type(activated) is not str
        or re.fullmatch(r"[0-9a-f]{64}", activated) is None
        or activated == SUCCESSOR_BUDGET_DEFINITION_ID
    ):
        raise GateError("activated successor budget ID invalid")
    exact = _render_supersession_authority(package_lock, root, activated)
    raw = exact.encode("utf-8")
    checks = {
        "normalized_visible_text": exact,
        "normalized_visible_text_utf8_bytes": len(raw),
        "normalized_visible_text_sha256": _sha256(raw),
        "package_lock_record_sha256": package_lock["record_sha256"],
        "package_aggregate_sha256": package_lock["package_aggregate_sha256"],
        "successor_budget_definition_id": SUCCESSOR_BUDGET_DEFINITION_ID,
        "activated_successor_budget_id": authority["activated_successor_budget_id"],
        "successor_budget_scope": SUCCESSOR_BUDGET_SCOPE,
        "v4_package_aggregate_sha256": V4_PACKAGE_AGGREGATE_SHA256,
        "v4_machine_raw_sha256": V4_MACHINE_RAW_SHA256,
        "v4_machine_semantic_sha256": V4_MACHINE_SEMANTIC_SHA256,
        "v2_package_aggregate_sha256": V2_PACKAGE_AGGREGATE_SHA256,
        "v2_intent_raw_sha256": V2_INTENT_RAW_SHA256,
        "v2_intent_semantic_sha256": V2_INTENT_SEMANTIC_SHA256,
        "v2_error_raw_sha256": V2_ERROR_RAW_SHA256,
        "v2_error_semantic_sha256": V2_ERROR_SEMANTIC_SHA256,
        "v2_outcome_raw_sha256": V2_OUTCOME_RAW_SHA256,
        "v2_outcome_semantic_sha256": V2_OUTCOME_SEMANTIC_SHA256,
        "v2_attempt_spend_acknowledged": True,
        "acknowledge_v2_row0_spent_at_durable_intent": True,
        "acknowledge_v2_terminal_no_retry": True,
        "acknowledge_sendall_zero_does_not_restore_budget": True,
        "custody_root": root,
        "operation_id": OPERATIONS[0].operation_id,
        "exact_url": OPERATIONS[0].url,
        "exact_request_bytes": len(OPERATIONS[0].request_bytes),
        "exact_request_sha256": _sha256(OPERATIONS[0].request_bytes),
        "resolver_high_level_call_limit": 1,
        "resolver_child_fork_site_limit": 1,
        "socket_instance_limit": 1,
        "connect_limit": 1,
        "tls_wrap_limit": 1,
        "request_send_limit": 1,
        "attempt_limit": 1,
        "retry_limit": 0,
        "redirect_limit": 0,
        "address_fallback_limit": 0,
        "row1_may_consume": False,
        "network_or_contact_authorized": False,
        "authority_identity_externally_authenticated": False,
        "created_time_externally_attested": False,
    }
    for key, expected in checks.items():
        if authority.get(key) != expected or type(authority.get(key)) is not type(expected):
            raise GateError(f"supersession authority mismatch: {key}")
    created = authority.get("created_unix_ns")
    if type(created) is not int or created <= package_lock["created_unix_ns"] or st.st_mtime_ns < created:
        raise GateError("supersession authority chronology invalid")
    return authority


def _render_preflight_authority(
    package_lock: Mapping[str, Any], supersession: Mapping[str, Any], root: Mapping[str, Any]
) -> str:
    return "\n".join(
        [
            "AUTHORIZE_SOLO_BLOCK2_OFFLINE_RUNTIME_PREFLIGHT_V5",
            f"package_aggregate_sha256={package_lock['package_aggregate_sha256']}",
            f"package_lock_record_sha256={package_lock['record_sha256']}",
            f"supersession_authority_record_sha256={supersession['record_sha256']}",
            f"successor_budget_definition_id={SUCCESSOR_BUDGET_DEFINITION_ID}",
            f"activated_successor_budget_id={supersession['activated_successor_budget_id']}",
            f"custody_root_absolute_path={root['absolute_path']}",
            f"custody_root_device={root['device']}",
            f"custody_root_inode={root['inode']}",
            "scope=OFFLINE_RUNTIME_AND_CUSTODY_PREFLIGHT_ONLY",
            "network_or_contact_authorized=false",
            "authority_identity_externally_authenticated=false",
            "created_time_externally_attested=false",
        ]
    )


def _validate_preflight_authority(
    rootfd: int, package_lock: Mapping[str, Any], root: Mapping[str, Any]
) -> dict[str, Any]:
    authority, _, st = _read_receipt_at(
        rootfd,
        "preflight-authority.json",
        schema=PREFLIGHT_AUTHORITY_SCHEMA,
        exact_keys=PREFLIGHT_AUTHORITY_KEYS,
    )
    supersession = _validate_supersession_authority(rootfd, package_lock, root)
    exact = _render_preflight_authority(package_lock, supersession, root)
    if authority.get("normalized_visible_text") != exact:
        raise GateError("offline preflight authority is not exact affirmative equality")
    raw = exact.encode("utf-8")
    if authority.get("normalized_visible_text_utf8_bytes") != len(raw):
        raise GateError("offline preflight authority length mismatch")
    if authority.get("normalized_visible_text_sha256") != _sha256(raw):
        raise GateError("offline preflight authority digest mismatch")
    if authority.get("network_or_contact_authorized") is not False:
        raise GateError("offline authority scope broadened")
    if (
        authority.get("authority_identity_externally_authenticated") is not False
        or authority.get("created_time_externally_attested") is not False
    ):
        raise GateError("offline authority overclaims identity or trusted time")
    if authority.get("package_aggregate_sha256") != package_lock.get(
        "package_aggregate_sha256"
    ):
        raise GateError("offline preflight authority package binding mismatch")
    if (
        authority.get("supersession_authority_record_sha256") != supersession["record_sha256"]
        or authority.get("successor_budget_definition_id") != SUCCESSOR_BUDGET_DEFINITION_ID
        or authority.get("activated_successor_budget_id") != supersession["activated_successor_budget_id"]
    ):
        raise GateError("offline preflight authority supersession binding mismatch")
    created = authority.get("created_unix_ns")
    if (
        type(created) is not int
        or created <= package_lock.get("created_unix_ns", 0)
        or created <= supersession.get("created_unix_ns", 0)
    ):
        raise GateError("offline preflight authority chronology invalid")
    if st.st_mtime_ns < created:
        raise GateError("offline preflight authority file chronology invalid")
    return authority


def _runtime_preflight_record(
    package_lock: Mapping[str, Any],
    authority: Mapping[str, Any],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": RUNTIME_PREFLIGHT_SCHEMA,
        "record_sha256": None,
        "decision": "OFFLINE_RUNTIME_AND_CUSTODY_PREFLIGHT_QUALIFIED_FETCH_STILL_HOLD",
        "package_aggregate_sha256": package_lock["package_aggregate_sha256"],
        "package_lock_record_sha256": package_lock["record_sha256"],
        "preflight_authority_record_sha256": authority["record_sha256"],
        "supersession_authority_record_sha256": authority["supersession_authority_record_sha256"],
        "successor_budget_definition_id": SUCCESSOR_BUDGET_DEFINITION_ID,
        "activated_successor_budget_id": authority["activated_successor_budget_id"],
        "runtime_manifest": manifest,
        "runtime_manifest_sha256": manifest["manifest_sha256"],
        "created_unix_ns": time.time_ns(),
        "network_actions_performed": 0,
        "durable_row_intents_created": 0,
        "fetch_eligible": False,
    }


def _require_admissible_resolver_snapshot(manifest: Mapping[str, Any]) -> None:
    snapshot = manifest.get("resolver_systemconfiguration_snapshot")
    if type(snapshot) is not dict:
        raise GateError("system resolver snapshot absent")
    try:
        stdout = base64.b64decode(snapshot["stdout_base64"], validate=True)
        stderr = base64.b64decode(snapshot["stderr_base64"], validate=True)
    except (KeyError, ValueError) as exc:
        raise GateError("system resolver snapshot bytes malformed") from exc
    if (
        snapshot.get("returncode") != 0
        or not stdout.strip()
        or stdout.strip() == b"No DNS configuration available"
        or stderr
    ):
        raise GateError("system resolver configuration unavailable; preflight remains HOLD")
    if snapshot.get("dynamic_daemon_cache_wire_state_bound") is not False:
        raise GateError("resolver snapshot overclaims dynamic state")


def preflight(custody_root: str) -> str:
    """Create the one offline runtime preflight receipt; never touch network."""

    _require_production_process("preflight", custody_root, None)
    os.umask(0o077)
    _require_fd_baseline()
    machine, machine_raw = _load_machine()
    rootfd, root_st = _open_root(custody_root)
    try:
        _require_machine_bound_root(machine, custody_root, root_st, rootfd)
        _require_fd_baseline(frozenset({rootfd}))
        _require_root_roster(
            rootfd, {"package-lock.json", "supersession-authority.json", "preflight-authority.json"}
        )
        root = _root_identity(custody_root, root_st)
        package_lock = _load_package_lock(rootfd, machine, machine_raw)
        authority = _validate_preflight_authority(rootfd, package_lock, root)
        if _entry_exists_at(rootfd, "runtime-preflight.json"):
            raise CustodyError("runtime preflight already exists")
        manifest = _runtime_manifest(custody_root, root_st)
        _require_admissible_resolver_snapshot(manifest)
        record = _runtime_preflight_record(package_lock, authority, manifest)
        digest, _ = _exclusive_canonical_at(
            rootfd, "runtime-preflight.json", record
        )
        _reopen_exact_digest_at(rootfd, "runtime-preflight.json", digest)
        _require_root_roster(
            rootfd,
            {
                "package-lock.json",
                "supersession-authority.json",
                "preflight-authority.json",
                "runtime-preflight.json",
            },
        )
        return digest
    finally:
        os.close(rootfd)


def _validate_runtime_preflight(
    rootfd: int,
    root_path: str,
    root_st: os.stat_result,
    package_lock: Mapping[str, Any],
) -> dict[str, Any]:
    receipt, _, st = _read_receipt_at(
        rootfd,
        "runtime-preflight.json",
        schema=RUNTIME_PREFLIGHT_SCHEMA,
        exact_keys=RUNTIME_PREFLIGHT_KEYS,
    )
    if receipt.get("decision") != (
        "OFFLINE_RUNTIME_AND_CUSTODY_PREFLIGHT_QUALIFIED_FETCH_STILL_HOLD"
    ):
        raise GateError("runtime preflight decision mismatch")
    if receipt.get("package_aggregate_sha256") != package_lock.get(
        "package_aggregate_sha256"
    ):
        raise GateError("runtime preflight package mismatch")
    if receipt.get("package_lock_record_sha256") != package_lock.get("record_sha256"):
        raise GateError("runtime preflight package-lock receipt mismatch")
    root = _root_identity(root_path, root_st)
    authority = _validate_preflight_authority(rootfd, package_lock, root)
    supersession = _validate_supersession_authority(rootfd, package_lock, root)
    if (
        receipt.get("supersession_authority_record_sha256") != supersession["record_sha256"]
        or receipt.get("successor_budget_definition_id") != SUCCESSOR_BUDGET_DEFINITION_ID
        or receipt.get("activated_successor_budget_id") != supersession["activated_successor_budget_id"]
    ):
        raise GateError("runtime preflight supersession binding mismatch")
    if receipt.get("preflight_authority_record_sha256") != authority.get(
        "record_sha256"
    ):
        raise GateError("runtime preflight authority receipt mismatch")
    if (
        receipt.get("network_actions_performed") != 0
        or type(receipt.get("network_actions_performed")) is not int
        or receipt.get("durable_row_intents_created") != 0
        or type(receipt.get("durable_row_intents_created")) is not int
        or receipt.get("fetch_eligible") is not False
    ):
        raise GateError("runtime preflight non-effect relation mismatch")
    created = receipt.get("created_unix_ns")
    if (
        type(created) is not int
        or created <= package_lock.get("created_unix_ns", 0)
        or created <= authority.get("created_unix_ns", 0)
    ):
        raise GateError("runtime preflight chronology invalid")
    if st.st_mtime_ns < created:
        raise GateError("runtime preflight file chronology invalid")
    manifest = receipt.get("runtime_manifest")
    manifest_digest = _validate_runtime_manifest_self_digest(manifest)
    if receipt.get("runtime_manifest_sha256") != manifest_digest:
        raise GateError("runtime preflight manifest receipt mismatch")
    if manifest.get("custody_root") != _runtime_root_identity(root_path, root_st):
        raise GateError("runtime preflight custody-root identity mismatch")
    _require_admissible_resolver_snapshot(manifest)
    return receipt


def _revalidate_runtime_immediately_before_reservation(
    root_path: str,
    root_st: os.stat_result,
    preflight: Mapping[str, Any],
) -> None:
    current = _runtime_manifest(root_path, root_st)
    admitted = preflight.get("runtime_manifest")
    if type(admitted) is not dict or _canonical_bytes(admitted) != _canonical_bytes(
        current
    ):
        raise GateError("loaded runtime/custody/environment drift")
    if preflight.get("runtime_manifest_sha256") != current["manifest_sha256"]:
        raise GateError("runtime manifest digest drift")


def _operation(row: int) -> ExactOperation:
    if type(row) is not int or row != 0:
        raise GateError("V5 production operation is exact builtin integer row 0 only")
    return OPERATIONS[0]


def _read_raw_sidecar_at(
    dirfd: int, basename: str, cap: int
) -> tuple[bytes, dict[str, Any]]:
    _require_basename(basename)
    fd = os.open(basename, READ_FLAGS, dir_fd=dirfd)
    try:
        before = os.fstat(fd)
        _validate_regular_receipt_stat(before, mode=0o600)
        raw = _read_all_fd(fd, cap)
        os.fsync(fd)
        after = os.fstat(fd)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
            before.st_mode,
            before.st_uid,
            before.st_gid,
            before.st_nlink,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
            after.st_mode,
            after.st_uid,
            after.st_gid,
            after.st_nlink,
        ):
            raise GateError("raw sidecar changed during contextual reopen")
        return raw, {
            "basename": basename,
            "device": before.st_dev,
            "inode": before.st_ino,
            "uid": before.st_uid,
            "gid": before.st_gid,
            "mode_octal": f"{stat.S_IMODE(before.st_mode):04o}",
            "nlink": before.st_nlink,
            "bytes": len(raw),
            "sha256": _sha256(raw),
        }
    finally:
        os.close(fd)


def _entry_exists_at(dirfd: int, basename: str) -> bool:
    try:
        os.stat(basename, dir_fd=dirfd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def _require_root_roster(rootfd: int, expected: set[str]) -> None:
    names = os.listdir(rootfd)
    if (
        any(type(name) is not str for name in names)
        or len(names) != len(set(names))
        or set(names) != expected
    ):
        raise CustodyError(
            "custody root roster mismatch: "
            f"missing={sorted(expected - set(names))} "
            f"extra={sorted(set(names) - expected)}"
        )


def _expected_root_before_row_phase(row: int, phase: str) -> set[str]:
    if type(row) is not int or row != 0:
        raise GateError("V5 production custody phases are exact row 0 only")
    if phase not in {"GO", "AUTHORITY", "ATTEMPT"}:
        raise GateError("unknown row custody phase")
    expected = {
        "package-lock.json",
        "supersession-authority.json",
        "preflight-authority.json",
        "runtime-preflight.json",
    }
    if phase in {"AUTHORITY", "ATTEMPT"}:
        expected.add(f"row{row}-independent-go.json")
    if phase == "ATTEMPT":
        expected.add(f"row{row}-authority.json")
    return expected


def _validate_go(
    rootfd: int,
    op: ExactOperation,
    package_lock: Mapping[str, Any],
    preflight_receipt: Mapping[str, Any],
    row0_outcome: Mapping[str, Any] | None,
) -> dict[str, Any]:
    go, _, go_st = _read_receipt_at(
        rootfd,
        f"row{op.ordinal}-independent-go.json",
        schema=INDEPENDENT_GO_SCHEMA,
        exact_keys=INDEPENDENT_GO_KEYS,
    )
    root = _root_identity(V5_OPERATIONAL_ROOT, os.fstat(rootfd))
    supersession = _validate_supersession_authority(rootfd, package_lock, root)
    exact = {
        "decision": "GO_EXACT_SINGLE_ROOT_PAGE_ATTEMPT_NO_RETRY",
        "row_ordinal": op.ordinal,
        "operation_id": op.operation_id,
        "exact_url": op.url,
        "exact_request_sha256": _sha256(op.request_bytes),
        "package_aggregate_sha256": package_lock["package_aggregate_sha256"],
        "runtime_preflight_record_sha256": preflight_receipt["record_sha256"],
        "runtime_manifest_sha256": preflight_receipt["runtime_manifest_sha256"],
        "row0_success_outcome_sha256": (
            None if row0_outcome is None else row0_outcome["record_sha256"]
        ),
        "attempt_limit": 1,
        "retry_limit": 0,
        "redirect_limit": 0,
        "reviewer_is_executor_or_package_author": False,
        "reviewer_identity_externally_authenticated": False,
        "created_time_externally_attested": False,
        "supersession_authority_record_sha256": supersession["record_sha256"],
        "successor_budget_definition_id": SUCCESSOR_BUDGET_DEFINITION_ID,
        "activated_successor_budget_id": supersession["activated_successor_budget_id"],
    }
    for key, expected in exact.items():
        if go.get(key) != expected or type(go.get(key)) is not type(expected):
            raise GateError(f"independent GO mismatch: {key}")
    reviewer = go.get("independent_reviewer_principal")
    if type(reviewer) is not str or not reviewer or len(reviewer.encode()) > 512:
        raise GateError("independent reviewer principal invalid")
    created = go.get("created_unix_ns")
    if type(created) is not int or created <= preflight_receipt.get(
        "created_unix_ns", 0
    ):
        raise GateError("independent GO chronology invalid")
    if go_st.st_mtime_ns < created:
        raise GateError("independent GO file chronology invalid")
    if row0_outcome is not None:
        raise GateError("V5 row-zero GO prior outcome must be null")
    return go


def _render_row_authority(
    op: ExactOperation,
    package_lock: Mapping[str, Any],
    preflight: Mapping[str, Any],
    go: Mapping[str, Any],
    root: Mapping[str, Any],
    row0_outcome: Mapping[str, Any] | None,
    supersession: Mapping[str, Any],
    created_unix_ns: int,
    expires_unix_ns: int,
) -> str:
    return "\n".join(
        [
            "AUTHORIZE_SOLO_BLOCK2_EXACT_ROOT_PAGE_ATTEMPT_V5_ROW0_SUCCESSOR",
            f"row_ordinal={op.ordinal}",
            f"operation_id={op.operation_id}",
            f"exact_url={op.url}",
            f"exact_request_sha256={_sha256(op.request_bytes)}",
            f"package_aggregate_sha256={package_lock['package_aggregate_sha256']}",
            f"runtime_preflight_record_sha256={preflight['record_sha256']}",
            f"runtime_manifest_sha256={preflight['runtime_manifest_sha256']}",
            f"independent_go_record_sha256={go['record_sha256']}",
            f"supersession_authority_record_sha256={go['supersession_authority_record_sha256']}",
            f"successor_budget_definition_id={SUCCESSOR_BUDGET_DEFINITION_ID}",
            f"successor_budget_scope={SUCCESSOR_BUDGET_SCOPE}",
            f"activated_successor_budget_id={supersession['activated_successor_budget_id']}",
            f"v4_package_aggregate_sha256={V4_PACKAGE_AGGREGATE_SHA256}",
            f"v4_machine_raw_sha256={V4_MACHINE_RAW_SHA256}",
            f"v4_machine_semantic_sha256={V4_MACHINE_SEMANTIC_SHA256}",
            f"v2_package_aggregate_sha256={V2_PACKAGE_AGGREGATE_SHA256}",
            f"v2_intent_raw_sha256={V2_INTENT_RAW_SHA256}",
            f"v2_intent_semantic_sha256={V2_INTENT_SEMANTIC_SHA256}",
            f"v2_error_raw_sha256={V2_ERROR_RAW_SHA256}",
            f"v2_error_semantic_sha256={V2_ERROR_SEMANTIC_SHA256}",
            f"v2_outcome_raw_sha256={V2_OUTCOME_RAW_SHA256}",
            f"v2_outcome_semantic_sha256={V2_OUTCOME_SEMANTIC_SHA256}",
            f"row0_success_outcome_sha256={None if row0_outcome is None else row0_outcome['record_sha256']}",
            f"custody_root_absolute_path={root['absolute_path']}",
            f"custody_root_device={root['device']}",
            f"custody_root_inode={root['inode']}",
            "system_resolver_high_level_call_limit=1",
            "dns_packet_count_wire_ttl_cache_server_determinism_claimed=false",
            "https_socket_connect_limit=1",
            "address_fallback_limit=0",
            "https_get_send_limit=1",
            "retry_limit=0",
            "retry_limit_scope=APPLICATION_RESOLVER_CONNECT_TLS_HTTP_ONLY",
            "tcp_retransmission_tls_record_behavior_os_scheduling_bound=false",
            "redirect_limit=0",
            "v2_attempt_spend_acknowledged=true",
            "v2_receipts_reused=false",
            "new_version_or_root_resets_spent_budget=false",
            "row1_may_consume=false",
            f"created_unix_ns={created_unix_ns}",
            f"expires_unix_ns={expires_unix_ns}",
            "negated_or_revoked=false",
            "tls_transport_cryptographic_entropy_authorized=true",
            "scientific_entropy_authorized=false",
            "plaintext_http_request_exact_encrypted_wire_bytes_exact=false",
            "scope=READ_ONLY_EXACT_REGISTERED_ROOT_PAGE_ONLY",
            "authority_identity_externally_authenticated=false",
            "created_time_externally_attested=false",
            "expiry_time_externally_attested=false",
        ]
    )


def _validate_row_authority(
    rootfd: int,
    op: ExactOperation,
    package_lock: Mapping[str, Any],
    preflight: Mapping[str, Any],
    go: Mapping[str, Any],
    root: Mapping[str, Any],
    row0_outcome: Mapping[str, Any] | None,
) -> dict[str, Any]:
    authority, _, st = _read_receipt_at(
        rootfd,
        f"row{op.ordinal}-authority.json",
        schema=ROW_AUTHORITY_SCHEMA,
        exact_keys=ROW_AUTHORITY_KEYS,
    )
    supersession = _validate_supersession_authority(rootfd, package_lock, root)
    exact = _render_row_authority(
        op, package_lock, preflight, go, root, row0_outcome, supersession,
        authority.get("created_unix_ns"), authority.get("expires_unix_ns")
    )
    if authority.get("normalized_visible_text") != exact:
        raise GateError("row authority text is not exact affirmative equality")
    raw = exact.encode("utf-8")
    if authority.get("normalized_visible_text_utf8_bytes") != len(raw):
        raise GateError("row authority byte count mismatch")
    if authority.get("normalized_visible_text_sha256") != _sha256(raw):
        raise GateError("row authority digest mismatch")
    if authority.get("row_ordinal") != op.ordinal or type(
        authority.get("row_ordinal")
    ) is not int:
        raise GateError("row authority ordinal mismatch")
    if authority.get("independent_go_record_sha256") != go["record_sha256"]:
        raise GateError("row authority GO binding mismatch")
    if (
        authority.get("supersession_authority_record_sha256") != supersession["record_sha256"]
        or authority.get("successor_budget_definition_id") != SUCCESSOR_BUDGET_DEFINITION_ID
        or authority.get("activated_successor_budget_id") != supersession["activated_successor_budget_id"]
    ):
        raise GateError("row authority successor budget binding mismatch")
    direct = {
        "operation_id": op.operation_id,
        "exact_url": op.url,
        "exact_request_bytes": len(op.request_bytes),
        "exact_request_sha256": _sha256(op.request_bytes),
        "package_aggregate_sha256": package_lock["package_aggregate_sha256"],
        "package_lock_record_sha256": package_lock["record_sha256"],
        "preflight_authority_record_sha256": preflight["preflight_authority_record_sha256"],
        "runtime_preflight_record_sha256": preflight["record_sha256"],
        "runtime_manifest_sha256": preflight["runtime_manifest_sha256"],
        "custody_root": root,
        "v4_package_aggregate_sha256": V4_PACKAGE_AGGREGATE_SHA256,
        "v4_machine_raw_sha256": V4_MACHINE_RAW_SHA256,
        "v4_machine_semantic_sha256": V4_MACHINE_SEMANTIC_SHA256,
        "v2_package_aggregate_sha256": V2_PACKAGE_AGGREGATE_SHA256,
        "v2_intent_raw_sha256": V2_INTENT_RAW_SHA256,
        "v2_intent_semantic_sha256": V2_INTENT_SEMANTIC_SHA256,
        "v2_error_raw_sha256": V2_ERROR_RAW_SHA256,
        "v2_error_semantic_sha256": V2_ERROR_SEMANTIC_SHA256,
        "v2_outcome_raw_sha256": V2_OUTCOME_RAW_SHA256,
        "v2_outcome_semantic_sha256": V2_OUTCOME_SEMANTIC_SHA256,
        "resolver_high_level_call_limit": 1,
        "resolver_child_fork_site_limit": 1,
        "socket_instance_limit": 1,
        "connect_limit": 1,
        "tls_wrap_limit": 1,
        "address_fallback_limit": 0,
        "request_send_limit": 1,
        "attempt_limit": 1,
        "retry_limit": 0,
        "redirect_limit": 0,
        "acknowledge_v2_row0_spent_at_durable_intent": True,
        "acknowledge_v2_terminal_no_retry": True,
        "acknowledge_sendall_zero_does_not_restore_budget": True,
        "successor_budget_scope": SUCCESSOR_BUDGET_SCOPE,
        "row1_may_consume": False,
        "v2_receipts_reused": False,
        "version_or_root_reset_spent_budget": False,
    }
    for key, expected in direct.items():
        if authority.get(key) != expected or type(authority.get(key)) is not type(expected):
            raise GateError(f"row authority direct binding mismatch: {key}")
    created = authority.get("created_unix_ns")
    expires = authority.get("expires_unix_ns")
    if type(created) is not int or type(expires) is not int:
        raise GateError("row authority chronology types invalid")
    if expires <= created or expires - created > MAX_AUTHORITY_LIFETIME_NS:
        raise GateError("row authority lifetime invalid")
    now = time.time_ns()
    if now < created or now > expires:
        raise GateError("row authority is not currently fresh")
    if st.st_mtime_ns < created or st.st_mtime_ns > expires:
        raise GateError("row authority file chronology invalid")
    if authority.get("negated_or_revoked") is not False:
        raise GateError("row authority negated or revoked")
    if (
        authority.get("authority_identity_externally_authenticated") is not False
        or authority.get("created_time_externally_attested") is not False
        or authority.get("expiry_time_externally_attested") is not False
    ):
        raise GateError("row authority overclaims identity or trusted time")
    if created <= go.get("created_unix_ns", 0):
        raise GateError("row authority does not postdate independent GO")
    return authority


def _open_registrar_root(
    command: str,
    custody_root: str,
    row: int | None,
    extra_argv: Sequence[str],
) -> tuple[dict[str, Any], bytes, int, os.stat_result]:
    _require_production_process(command, custody_root, row, extra_argv)
    os.umask(0o077)
    _require_fd_baseline()
    machine, machine_raw = _load_machine()
    rootfd, root_st = _open_root(custody_root)
    try:
        _require_machine_bound_root(machine, custody_root, root_st, rootfd)
        _require_fd_baseline(frozenset({rootfd}))
    except BaseException:
        os.close(rootfd)
        raise
    return machine, machine_raw, rootfd, root_st


def _require_reviewer_principal(value: str) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > 512
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
    ):
        raise GateError("independent reviewer principal invalid")
    return value


def register_package_lock(
    custody_root: str, independent_reviewer_principal: str, created_unix_ns: int
) -> str:
    """Materialize one independently reviewed stopped-package lock."""

    machine, machine_raw, rootfd, _root_st = _open_registrar_root(
        "register-package-lock",
        custody_root,
        None,
        (independent_reviewer_principal, str(created_unix_ns)),
    )
    try:
        _require_root_roster(rootfd, set())
        reviewer = _require_reviewer_principal(independent_reviewer_principal)
        if type(created_unix_ns) is not int:
            raise GateError("package-lock chronology type invalid")
        bindings, aggregate = _current_package_inputs(machine, machine_raw)
        machine_receipt = _hash_path_nofollow(
            os.path.join(PACKAGE_ROOT, MACHINE_RELATIVE_PATH)
        )
        if created_unix_ns <= max(
            [item["mtime_ns"] for item in bindings]
            + [machine_receipt["mtime_ns"]]
        ):
            raise GateError("package-lock event predates stopped package")
        if created_unix_ns > time.time_ns():
            raise GateError("package-lock event is in the future")
        record = {
            "schema_version": PACKAGE_LOCK_SCHEMA,
            "record_sha256": None,
            "decision": "INDEPENDENT_PACKAGE_BYTES_GO",
            "machine_raw_sha256": _sha256(machine_raw),
            "machine_semantic_sha256": machine["record_sha256"],
            "bound_file_receipts": bindings,
            "package_aggregate_sha256": aggregate,
            "independent_reviewer_principal": reviewer,
            "reviewer_is_package_author": False,
            "reviewer_identity_externally_authenticated": False,
            "created_unix_ns": created_unix_ns,
            "created_time_externally_attested": False,
        }
        digest, _ = _exclusive_canonical_at(rootfd, "package-lock.json", record)
        _reopen_exact_digest_at(rootfd, "package-lock.json", digest)
        _require_root_roster(rootfd, {"package-lock.json"})
        return digest
    finally:
        os.close(rootfd)


def register_preflight_authority(
    custody_root: str, created_unix_ns: int, normalized_visible_text: str
) -> str:
    """Materialize exact offline-only preflight authority from CLI bytes."""

    machine, machine_raw, rootfd, root_st = _open_registrar_root(
        "register-preflight-authority",
        custody_root,
        None,
        (str(created_unix_ns), normalized_visible_text),
    )
    try:
        _require_root_roster(rootfd, {"package-lock.json", "supersession-authority.json"})
        package_lock = _load_package_lock(rootfd, machine, machine_raw)
        root = _root_identity(custody_root, root_st)
        supersession = _validate_supersession_authority(rootfd, package_lock, root)
        exact = _render_preflight_authority(package_lock, supersession, root)
        if (
            normalized_visible_text != exact
            or type(created_unix_ns) is not int
            or created_unix_ns <= package_lock["created_unix_ns"]
            or created_unix_ns <= supersession["created_unix_ns"]
            or created_unix_ns > time.time_ns()
        ):
            raise GateError("preflight-authority event mismatch")
        raw = exact.encode("utf-8")
        record = {
            "schema_version": PREFLIGHT_AUTHORITY_SCHEMA,
            "record_sha256": None,
            "normalized_visible_text": exact,
            "normalized_visible_text_utf8_bytes": len(raw),
            "normalized_visible_text_sha256": _sha256(raw),
            "network_or_contact_authorized": False,
            "authority_identity_externally_authenticated": False,
            "package_aggregate_sha256": package_lock["package_aggregate_sha256"],
            "supersession_authority_record_sha256": supersession["record_sha256"],
            "successor_budget_definition_id": SUCCESSOR_BUDGET_DEFINITION_ID,
            "activated_successor_budget_id": supersession["activated_successor_budget_id"],
            "created_unix_ns": created_unix_ns,
            "created_time_externally_attested": False,
        }
        digest, _ = _exclusive_canonical_at(
            rootfd, "preflight-authority.json", record
        )
        _reopen_exact_digest_at(rootfd, "preflight-authority.json", digest)
        _require_root_roster(
            rootfd, {"package-lock.json", "supersession-authority.json", "preflight-authority.json"}
        )
        return digest
    finally:
        os.close(rootfd)


def register_supersession_authority(
    custody_root: str,
    created_unix_ns: int,
    activated_successor_budget_id: str,
    normalized_visible_text: str,
) -> str:
    """Materialize the exact V2-spend/V4-definition supersession authority."""

    machine, machine_raw, rootfd, root_st = _open_registrar_root(
        "register-supersession-authority", custody_root, None,
        (str(created_unix_ns), activated_successor_budget_id, normalized_visible_text),
    )
    try:
        _require_root_roster(rootfd, {"package-lock.json"})
        package_lock = _load_package_lock(rootfd, machine, machine_raw)
        root = _root_identity(custody_root, root_st)
        if (
            type(activated_successor_budget_id) is not str
            or re.fullmatch(r"[0-9a-f]{64}", activated_successor_budget_id) is None
            or activated_successor_budget_id == SUCCESSOR_BUDGET_DEFINITION_ID
        ):
            raise GateError("activated successor budget ID invalid")
        exact = _render_supersession_authority(
            package_lock, root, activated_successor_budget_id
        )
        if (
            normalized_visible_text != exact
            or type(created_unix_ns) is not int
            or created_unix_ns <= package_lock["created_unix_ns"]
            or created_unix_ns > time.time_ns()
        ):
            raise GateError("supersession-authority event mismatch")
        raw = exact.encode("utf-8")
        record = {
            "schema_version": SUPERSESSION_AUTHORITY_SCHEMA,
            "record_sha256": None,
            "normalized_visible_text": exact,
            "normalized_visible_text_utf8_bytes": len(raw),
            "normalized_visible_text_sha256": _sha256(raw),
            "package_lock_record_sha256": package_lock["record_sha256"],
            "package_aggregate_sha256": package_lock["package_aggregate_sha256"],
            "successor_budget_definition_id": SUCCESSOR_BUDGET_DEFINITION_ID,
            "activated_successor_budget_id": activated_successor_budget_id,
            "successor_budget_scope": SUCCESSOR_BUDGET_SCOPE,
            "v4_package_aggregate_sha256": V4_PACKAGE_AGGREGATE_SHA256,
            "v4_machine_raw_sha256": V4_MACHINE_RAW_SHA256,
            "v4_machine_semantic_sha256": V4_MACHINE_SEMANTIC_SHA256,
            "v2_package_aggregate_sha256": V2_PACKAGE_AGGREGATE_SHA256,
            "v2_intent_raw_sha256": V2_INTENT_RAW_SHA256,
            "v2_intent_semantic_sha256": V2_INTENT_SEMANTIC_SHA256,
            "v2_error_raw_sha256": V2_ERROR_RAW_SHA256,
            "v2_error_semantic_sha256": V2_ERROR_SEMANTIC_SHA256,
            "v2_outcome_raw_sha256": V2_OUTCOME_RAW_SHA256,
            "v2_outcome_semantic_sha256": V2_OUTCOME_SEMANTIC_SHA256,
            "v2_attempt_spend_acknowledged": True,
            "acknowledge_v2_row0_spent_at_durable_intent": True,
            "acknowledge_v2_terminal_no_retry": True,
            "acknowledge_sendall_zero_does_not_restore_budget": True,
            "custody_root": root,
            "operation_id": OPERATIONS[0].operation_id,
            "exact_url": OPERATIONS[0].url,
            "exact_request_bytes": len(OPERATIONS[0].request_bytes),
            "exact_request_sha256": _sha256(OPERATIONS[0].request_bytes),
            "resolver_high_level_call_limit": 1,
            "resolver_child_fork_site_limit": 1,
            "socket_instance_limit": 1,
            "connect_limit": 1,
            "tls_wrap_limit": 1,
            "request_send_limit": 1,
            "attempt_limit": 1,
            "retry_limit": 0,
            "redirect_limit": 0,
            "address_fallback_limit": 0,
            "row1_may_consume": False,
            "network_or_contact_authorized": False,
            "authority_identity_externally_authenticated": False,
            "created_unix_ns": created_unix_ns,
            "created_time_externally_attested": False,
        }
        digest, _ = _exclusive_canonical_at(rootfd, "supersession-authority.json", record)
        _reopen_exact_digest_at(rootfd, "supersession-authority.json", digest)
        _require_root_roster(rootfd, {"package-lock.json", "supersession-authority.json"})
        return digest
    finally:
        os.close(rootfd)


def register_independent_go(
    custody_root: str,
    independent_reviewer_principal: str,
    created_unix_ns: int,
) -> str:
    """Materialize the one exact row-zero independent GO from CLI bytes."""

    row = 0
    op = OPERATIONS[0]
    machine, machine_raw, rootfd, root_st = _open_registrar_root(
        "register-independent-go",
        custody_root,
        None,
        (independent_reviewer_principal, str(created_unix_ns)),
    )
    try:
        _require_root_roster(
            rootfd, _expected_root_before_row_phase(row, "GO")
        )
        package_lock = _load_package_lock(rootfd, machine, machine_raw)
        preflight_receipt = _validate_runtime_preflight(
            rootfd, custody_root, root_st, package_lock
        )
        row0_outcome = None
        supersession = _validate_supersession_authority(
            rootfd, package_lock, _root_identity(custody_root, root_st)
        )
        reviewer = _require_reviewer_principal(independent_reviewer_principal)
        if (
            type(created_unix_ns) is not int
            or created_unix_ns <= preflight_receipt["created_unix_ns"]
            or created_unix_ns > time.time_ns()
        ):
            raise GateError("independent-GO event chronology invalid")
        record = {
            "schema_version": INDEPENDENT_GO_SCHEMA,
            "record_sha256": None,
            "decision": "GO_EXACT_SINGLE_ROOT_PAGE_ATTEMPT_NO_RETRY",
            "row_ordinal": row,
            "operation_id": op.operation_id,
            "exact_url": op.url,
            "exact_request_sha256": _sha256(op.request_bytes),
            "package_aggregate_sha256": package_lock["package_aggregate_sha256"],
            "runtime_preflight_record_sha256": preflight_receipt["record_sha256"],
            "runtime_manifest_sha256": preflight_receipt["runtime_manifest_sha256"],
            "row0_success_outcome_sha256": (
                None
            ),
            "supersession_authority_record_sha256": supersession["record_sha256"],
            "successor_budget_definition_id": SUCCESSOR_BUDGET_DEFINITION_ID,
            "activated_successor_budget_id": supersession["activated_successor_budget_id"],
            "attempt_limit": 1,
            "retry_limit": 0,
            "redirect_limit": 0,
            "reviewer_is_executor_or_package_author": False,
            "reviewer_identity_externally_authenticated": False,
            "independent_reviewer_principal": reviewer,
            "created_unix_ns": created_unix_ns,
            "created_time_externally_attested": False,
        }
        basename = f"row{row}-independent-go.json"
        digest, _ = _exclusive_canonical_at(rootfd, basename, record)
        _reopen_exact_digest_at(rootfd, basename, digest)
        _require_root_roster(
            rootfd, _expected_root_before_row_phase(row, "AUTHORITY")
        )
        return digest
    finally:
        os.close(rootfd)


def register_row_authority(
    custody_root: str,
    created_unix_ns: int,
    expires_unix_ns: int,
    normalized_visible_text: str,
) -> str:
    """Materialize exact expiring row authority from exact CLI text bytes."""

    row = 0
    op = OPERATIONS[0]
    machine, machine_raw, rootfd, root_st = _open_registrar_root(
        "register-row-authority",
        custody_root,
        None,
        (str(created_unix_ns), str(expires_unix_ns), normalized_visible_text),
    )
    try:
        _require_root_roster(
            rootfd, _expected_root_before_row_phase(row, "AUTHORITY")
        )
        root = _root_identity(custody_root, root_st)
        package_lock = _load_package_lock(rootfd, machine, machine_raw)
        preflight_receipt = _validate_runtime_preflight(
            rootfd, custody_root, root_st, package_lock
        )
        row0_outcome = None
        supersession = _validate_supersession_authority(rootfd, package_lock, root)
        go = _validate_go(
            rootfd, op, package_lock, preflight_receipt, row0_outcome
        )
        exact = _render_row_authority(
            op, package_lock, preflight_receipt, go, root, row0_outcome, supersession,
            created_unix_ns, expires_unix_ns
        )
        now = time.time_ns()
        if (
            normalized_visible_text != exact
            or type(created_unix_ns) is not int
            or type(expires_unix_ns) is not int
            or created_unix_ns <= go["created_unix_ns"]
            or created_unix_ns > now
            or expires_unix_ns < now
            or expires_unix_ns <= created_unix_ns
            or expires_unix_ns - created_unix_ns > MAX_AUTHORITY_LIFETIME_NS
        ):
            raise GateError("row-authority event mismatch")
        raw = exact.encode("utf-8")
        record = {
            "schema_version": ROW_AUTHORITY_SCHEMA,
            "record_sha256": None,
            "row_ordinal": row,
            "operation_id": op.operation_id,
            "exact_url": op.url,
            "exact_request_bytes": len(op.request_bytes),
            "exact_request_sha256": _sha256(op.request_bytes),
            "package_aggregate_sha256": package_lock["package_aggregate_sha256"],
            "package_lock_record_sha256": package_lock["record_sha256"],
            "preflight_authority_record_sha256": preflight_receipt["preflight_authority_record_sha256"],
            "runtime_preflight_record_sha256": preflight_receipt["record_sha256"],
            "runtime_manifest_sha256": preflight_receipt["runtime_manifest_sha256"],
            "independent_go_record_sha256": go["record_sha256"],
            "supersession_authority_record_sha256": supersession["record_sha256"],
            "successor_budget_definition_id": SUCCESSOR_BUDGET_DEFINITION_ID,
            "activated_successor_budget_id": supersession["activated_successor_budget_id"],
            "successor_budget_scope": SUCCESSOR_BUDGET_SCOPE,
            "row1_may_consume": False,
            "v2_receipts_reused": False,
            "version_or_root_reset_spent_budget": False,
            "custody_root": root,
            "v4_package_aggregate_sha256": V4_PACKAGE_AGGREGATE_SHA256,
            "v4_machine_raw_sha256": V4_MACHINE_RAW_SHA256,
            "v4_machine_semantic_sha256": V4_MACHINE_SEMANTIC_SHA256,
            "v2_package_aggregate_sha256": V2_PACKAGE_AGGREGATE_SHA256,
            "v2_intent_raw_sha256": V2_INTENT_RAW_SHA256,
            "v2_intent_semantic_sha256": V2_INTENT_SEMANTIC_SHA256,
            "v2_error_raw_sha256": V2_ERROR_RAW_SHA256,
            "v2_error_semantic_sha256": V2_ERROR_SEMANTIC_SHA256,
            "v2_outcome_raw_sha256": V2_OUTCOME_RAW_SHA256,
            "v2_outcome_semantic_sha256": V2_OUTCOME_SEMANTIC_SHA256,
            "resolver_high_level_call_limit": 1,
            "resolver_child_fork_site_limit": 1,
            "socket_instance_limit": 1,
            "connect_limit": 1,
            "tls_wrap_limit": 1,
            "address_fallback_limit": 0,
            "request_send_limit": 1,
            "attempt_limit": 1,
            "retry_limit": 0,
            "redirect_limit": 0,
            "acknowledge_v2_row0_spent_at_durable_intent": True,
            "acknowledge_v2_terminal_no_retry": True,
            "acknowledge_sendall_zero_does_not_restore_budget": True,
            "normalized_visible_text": exact,
            "normalized_visible_text_utf8_bytes": len(raw),
            "normalized_visible_text_sha256": _sha256(raw),
            "created_unix_ns": created_unix_ns,
            "created_time_externally_attested": False,
            "expires_unix_ns": expires_unix_ns,
            "expiry_time_externally_attested": False,
            "authority_identity_externally_authenticated": False,
            "negated_or_revoked": False,
        }
        basename = f"row{row}-authority.json"
        digest, _ = _exclusive_canonical_at(rootfd, basename, record)
        _reopen_exact_digest_at(rootfd, basename, digest)
        _require_root_roster(
            rootfd, _expected_root_before_row_phase(row, "ATTEMPT")
        )
        return digest
    finally:
        os.close(rootfd)


def _mkdir_row(
    rootfd: int, root_st: os.stat_result, op: ExactOperation
) -> tuple[int, os.stat_result]:
    _require_basename(op.row_basename)
    os.mkdir(op.row_basename, 0o700, dir_fd=rootfd)
    os.fsync(rootfd)
    rowfd = os.open(op.row_basename, DIR_OPEN_FLAGS, dir_fd=rootfd)
    st = os.fstat(rowfd)
    if not stat.S_ISDIR(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o700:
        os.close(rowfd)
        raise CustodyError("row directory type/mode mismatch")
    if (
        st.st_uid != os.getuid()
        or st.st_gid != os.getgid()
        or st.st_dev != root_st.st_dev
        or st.st_nlink != 2
    ):
        os.close(rowfd)
        raise CustodyError("row directory device/owner/group/link mismatch")
    return rowfd, st


@dataclass
class Sidecar:
    basename: str
    fd: int
    stat_before: os.stat_result
    expected_device: int
    digest: Any
    bytes_written: int = 0

    def write(self, data: bytes, cap: int) -> None:
        if self.bytes_written + len(data) > cap:
            raise CustodyError(f"{self.basename} ceiling exceeded")
        _write_all(self.fd, data)
        self.digest.update(data)
        self.bytes_written += len(data)

    def verify_current_bytes(self) -> os.stat_result:
        os.fsync(self.fd)
        before = os.fstat(self.fd)
        _validate_regular_receipt_stat(before, mode=0o600)
        if (before.st_dev, before.st_ino) != (
            self.stat_before.st_dev,
            self.stat_before.st_ino,
        ):
            raise CustodyError(f"{self.basename} identity changed")
        if before.st_dev != self.expected_device:
            raise CustodyError(f"{self.basename} device changed")
        digest, size = _hash_fd(self.fd, limit=self.bytes_written)
        after = os.fstat(self.fd)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise CustodyError(f"{self.basename} changed during byte verification")
        if size != self.bytes_written or digest != self.digest.hexdigest():
            raise CustodyError(f"{self.basename} byte custody mismatch")
        os.lseek(self.fd, 0, os.SEEK_END)
        return after

    def fsync_and_receipt(self) -> dict[str, Any]:
        st = self.verify_current_bytes()
        return {
            "basename": self.basename,
            "device": st.st_dev,
            "inode": st.st_ino,
            "uid": st.st_uid,
            "gid": st.st_gid,
            "mode_octal": f"{stat.S_IMODE(st.st_mode):04o}",
            "nlink": st.st_nlink,
            "bytes": self.bytes_written,
            "sha256": self.digest.hexdigest(),
        }


@dataclass
class AttemptProgress:
    resolver_child_fork_site_count: int = 0
    resolver_high_level_call_count: int = 0
    resolver_result_roster: list[dict[str, Any]] | None = None
    socket_instance_count: int = 0
    connect_call_count: int = 0
    tls_wrap_call_count: int = 0
    sendall_call_count: int = 0
    request_emission_state: str = "NOT_ATTEMPTED"


def _create_sidecars(rowfd: int, row_st: os.stat_result) -> dict[str, Sidecar]:
    out: dict[str, Sidecar] = {}
    try:
        for basename in SIDECAR_BASENAMES:
            fd = os.open(basename, SIDECAR_CREATE_FLAGS, 0o600, dir_fd=rowfd)
            st = os.fstat(fd)
            _validate_regular_receipt_stat(st, mode=0o600)
            os.fsync(fd)
            if st.st_dev != row_st.st_dev:
                raise CustodyError("sidecar created on unexpected device")
            out[basename] = Sidecar(
                basename, fd, st, row_st.st_dev, hashlib.sha256()
            )
        os.fsync(rowfd)
        return out
    except BaseException:
        for sidecar in out.values():
            os.close(sidecar.fd)
        raise


def _sidecar_identity_roster(sidecars: Mapping[str, Sidecar]) -> list[dict[str, Any]]:
    return [
        {
            "basename": name,
            "device": sidecars[name].stat_before.st_dev,
            "inode": sidecars[name].stat_before.st_ino,
            "uid": sidecars[name].stat_before.st_uid,
            "gid": sidecars[name].stat_before.st_gid,
            "mode_octal": f"{stat.S_IMODE(sidecars[name].stat_before.st_mode):04o}",
            "nlink": sidecars[name].stat_before.st_nlink,
            "bytes_at_intent": sidecars[name].bytes_written,
            "sha256_at_intent": sidecars[name].digest.hexdigest(),
        }
        for name in SIDECAR_BASENAMES
    ]


def _make_intent(
    op: ExactOperation,
    package_lock: Mapping[str, Any],
    preflight: Mapping[str, Any],
    go: Mapping[str, Any],
    authority: Mapping[str, Any],
    root: Mapping[str, Any],
    root_after_mkdir: os.stat_result,
    row_st: os.stat_result,
    sidecars: Mapping[str, Sidecar],
    row0_outcome: Mapping[str, Any] | None,
    spend: Mapping[str, Any],
    spend_raw_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": INTENT_SCHEMA,
        "record_sha256": None,
        "terminal_contract": "DURABLE_INTENT_SPENDS_ONE_ATTEMPT_NO_RETRY",
        "row_ordinal": op.ordinal,
        "operation_id": op.operation_id,
        "exact_url": op.url,
        "exact_request_sha256": _sha256(op.request_bytes),
        "package_aggregate_sha256": package_lock["package_aggregate_sha256"],
        "runtime_preflight_record_sha256": preflight["record_sha256"],
        "runtime_manifest_sha256": preflight["runtime_manifest_sha256"],
        "independent_go_record_sha256": go["record_sha256"],
        "authority_record_sha256": authority["record_sha256"],
        "successor_budget_spend_record_sha256": spend["record_sha256"],
        "successor_budget_spend_raw_sha256": spend_raw_sha256,
        "row0_success_outcome_sha256": (
            None if row0_outcome is None else row0_outcome["record_sha256"]
        ),
        "custody_root": root,
        "custody_root_after_row_mkdir": {
            "device": root_after_mkdir.st_dev,
            "inode": root_after_mkdir.st_ino,
            "uid": root_after_mkdir.st_uid,
            "gid": root_after_mkdir.st_gid,
            "mode_octal": f"{stat.S_IMODE(root_after_mkdir.st_mode):04o}",
            "nlink": root_after_mkdir.st_nlink,
        },
        "row_directory": {
            "basename": op.row_basename,
            "device": row_st.st_dev,
            "inode": row_st.st_ino,
            "uid": row_st.st_uid,
            "gid": row_st.st_gid,
            "mode_octal": f"{stat.S_IMODE(row_st.st_mode):04o}",
            "nlink": row_st.st_nlink,
        },
        "precreated_sidecars": _sidecar_identity_roster(sidecars),
        "attempt_limit": 1,
        "retry_limit": 0,
        "redirect_limit": 0,
        "resolver_high_level_call_limit": 1,
        "resolver_packet_count_wire_ttl_cache_server_bound": False,
        "connect_limit": 1,
        "address_fallback_limit": 0,
        "request_send_limit": 1,
        "exact_plaintext_http_bytes_passed_to_tls_only": True,
        "encrypted_wire_bytes_claimed_exact": False,
        "application_retry_or_fallback_limit": 0,
        "tcp_retransmission_tls_record_behavior_and_os_scheduling_bound": False,
        "tls_transport_entropy_authorized_by_exact_row_authority": True,
        "scientific_entropy_authorized": False,
        "created_unix_ns": time.time_ns(),
    }


def _remaining(deadline: float, cap: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("absolute attempt deadline expired")
    return min(remaining, cap)


def _resolver_system_tuple_to_json_row(value: Any) -> list[Any]:
    """Normalize one system ``getaddrinfo`` tuple at the child trust boundary."""

    if type(value) is not tuple or len(value) != 5:
        raise ExecutorError("system resolver tuple shape invalid")
    family, socktype, proto, canonname, sockaddr = value
    if (
        type(family) not in {int, type(socket.AF_INET)}
        or type(socktype) not in {int, type(socket.SOCK_STREAM)}
        or type(proto) is not int
        or type(canonname) is not str
        or type(sockaddr) is not tuple
    ):
        raise ExecutorError("system resolver tuple leaf type invalid")
    return [int(family), int(socktype), int(proto), canonname, list(sockaddr)]


def _strict_resolver_rows(value: Any, host: str) -> list[dict[str, Any]]:
    if type(value) is not list or not value or len(value) > 128:
        raise ExecutorError("resolver result roster invalid")
    rows: list[dict[str, Any]] = []
    for item in value:
        if type(item) is not list or len(item) != 5:
            raise ExecutorError("resolver tuple shape invalid")
        family, socktype, proto, canonname, sockaddr = item
        if (
            type(family) is not int
            or type(socktype) is not int
            or type(proto) is not int
        ):
            raise ExecutorError("resolver numeric tuple leaves must be exact integers")
        if family not in (AF_INET_INT, AF_INET6_INT):
            raise ExecutorError("resolver returned unsupported address family")
        if socktype != SOCK_STREAM_INT or proto != IPPROTO_TCP_INT:
            raise ExecutorError("resolver returned non-TCP tuple")
        if type(canonname) is not str or type(sockaddr) is not list:
            raise ExecutorError("resolver tuple leaf type invalid")
        if len(canonname.encode("utf-8", "surrogateescape")) > 1024 or any(
            ord(character) < 0x20 or ord(character) == 0x7F
            for character in canonname
        ):
            raise ExecutorError("resolver canonical name invalid")
        if family == AF_INET_INT:
            if len(sockaddr) != 2:
                raise ExecutorError("IPv4 sockaddr shape invalid")
            ip, port = sockaddr
            flowinfo = 0
            scope_id = 0
            ip_obj = ipaddress.IPv4Address(ip)
        else:
            if len(sockaddr) != 4:
                raise ExecutorError("IPv6 sockaddr shape invalid")
            ip, port, flowinfo, scope_id = sockaddr
            ip_obj = ipaddress.IPv6Address(ip)
        if type(ip) is not str:
            raise ExecutorError("resolver numeric IP leaf must be exact string")
        if not ip_obj.is_global:
            raise ExecutorError("resolver returned non-global address")
        if type(port) is not int or port != 443:
            raise ExecutorError("resolver port mismatch")
        if (
            type(flowinfo) is not int
            or type(scope_id) is not int
            or not 0 <= flowinfo <= 0xFFFFF
            or not 0 <= scope_id <= 0xFFFFFFFF
        ):
            raise ExecutorError("resolver IPv6 integers invalid")
        rows.append(
            {
                "family": family,
                "socktype": socktype,
                "protocol": proto,
                "canonical_name": canonname,
                "numeric_ip": str(ip_obj),
                "port": port,
                "flowinfo": flowinfo,
                "scope_id": scope_id,
                "queried_host": host,
            }
        )
    if not rows:
        raise ExecutorError("resolver returned no admissible address")
    return rows


def _bounded_single_getaddrinfo(
    host: str, deadline: float, progress: AttemptProgress
) -> list[dict[str, Any]]:
    resolver_deadline = min(deadline, time.monotonic() + DNS_WAIT_SECONDS)
    read_fd, write_fd = os.pipe()
    progress.resolver_child_fork_site_count += 1
    pid = os.fork()
    if pid == 0:
        try:
            os.close(read_fd)
            # The resolver child retains only its bounded result-pipe writer.
            # It cannot mutate custody, intent, raw sinks, stdio or the root.
            _close_all_fds_except(frozenset({write_fd}))
            try:
                _write_all(write_fd, b"S")
                rows = socket.getaddrinfo(
                    host,
                    443,
                    socket.AF_UNSPEC,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                    socket.AI_ADDRCONFIG,
                )
                payload_value: dict[str, Any] = {
                    "ok": True,
                    "rows": [
                        _resolver_system_tuple_to_json_row(item) for item in rows
                    ],
                }
            except BaseException as exc:
                payload_value = {
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc)[:2048],
                }
            payload = _canonical_bytes(payload_value)
            if len(payload) <= MAX_RESOLVER_PIPE_BYTES:
                _write_all(write_fd, payload)
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    data = bytearray()
    status: int | None = None
    try:
        while True:
            timeout = _remaining(resolver_deadline, DNS_WAIT_SECONDS)
            ready, _, _ = select.select([read_fd], [], [], timeout)
            if not ready:
                raise TimeoutError("bounded resolver child deadline expired")
            chunk = os.read(read_fd, min(8192, MAX_RESOLVER_PIPE_BYTES + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            if data[:1] == b"S":
                progress.resolver_high_level_call_count = 1
            if len(data) > MAX_RESOLVER_PIPE_BYTES:
                raise ExecutorError("resolver child output ceiling exceeded")
        _, status = os.waitpid(pid, 0)
    except BaseException:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        os.waitpid(pid, 0)
        raise
    finally:
        os.close(read_fd)
    if status is None or not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
        raise ExecutorError("resolver child exit invalid")
    if data[:1] != b"S":
        raise ExecutorError("resolver child did not attest call-site entry")
    try:
        payload = json.loads(bytes(data[1:]), object_pairs_hook=_strict_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise ExecutorError("resolver child payload invalid") from exc
    if type(payload) is not dict or payload.get("ok") is not True:
        raise ExecutorError("single resolver call failed")
    rows = _strict_resolver_rows(payload.get("rows"), host)
    progress.resolver_result_roster = rows
    return rows


def _qualify_retained_response_context(
    head: bytes,
    raw_transfer_body: bytes,
    *,
    row_ordinal: int = 0,
    tls_version: str = "TLSv1.3",
    alpn: str = "http/1.1",
    cipher_name: str = "QUALIFICATION-ONLY-CIPHER",
    cipher_protocol: str = "TLSv1.3",
    cipher_bits: int = 256,
    peer_certificate_bytes: bytes = b"qualification-only-certificate",
    terminal_eof: bool = True,
    prior_parent_transcript: Any | None = None,
    prior_parent_outcome: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], Any, dict[str, Any]]:
    """Return the accepted-v2 observation and its exact parent context."""

    if type(head) is not bytes or type(raw_transfer_body) is not bytes:
        raise TypeError("qualification accepts exact bytes only")
    if type(row_ordinal) is not int or row_ordinal not in (0, 1):
        raise TypeError("row ordinal must be exact integer 0 or 1")
    parent = _ensure_parent_parser()
    operation = OPERATIONS[row_ordinal]
    timestamp = (
        "2000-01-01T00:00:00Z"
        if row_ordinal == 0
        else "2000-01-02T00:00:00Z"
    )
    transcript = parent.InertTranscript(
        timestamp,
        timestamp,
        timestamp,
        operation.host,
        443,
        ("192.0.2.10:443", "[2001:db8::10]:443"),
        "192.0.2.10:443",
        1,
        1,
        1,
        1,
        operation.request_bytes,
        tls_version,
        alpn,
        cipher_name,
        cipher_protocol,
        cipher_bits,
        peer_certificate_bytes,
        ((head + raw_transfer_body, b"") if terminal_eof else (head + raw_transfer_body,)),
        None,
    )
    if row_ordinal == 0:
        if prior_parent_transcript is not None or prior_parent_outcome is not None:
            raise GateError("row 0 qualification forbids prior context")
        modeled = parent.qualify_row_from_inert_transcript(
            row_ordinal, transcript=transcript
        )
    else:
        if type(prior_parent_transcript) is not parent.InertTranscript:
            raise GateError("row 1 requires custody-requalified row 0 transcript")
        if type(prior_parent_outcome) is not dict:
            raise GateError("row 1 requires custody-requalified row 0 outcome")
        modeled = parent.qualify_row_from_inert_transcript(
            row_ordinal,
            transcript=transcript,
            prior_transcript=prior_parent_transcript,
            prior_outcome=prior_parent_outcome,
        )
    diagnostics = {
        field: modeled[field]
        for field, _exact_type in parent.OUTCOME_DIAGNOSTIC_FIELD_TYPES
    }
    parser_error_type: str | None = None
    parser_error_text: str | None = None
    try:
        response = parent._receive_response(
            (head + raw_transfer_body, b"")
            if terminal_eof
            else (head + raw_transfer_body,)
        )
        captured_head = response.raw_head
        captured_body = response.raw_body
        decoded_entity = response.decoded_body
    except parent.ReconnaissanceError as exc:
        parser_error_type = type(exc).__name__
        parser_error_text = str(exc)
        captured_head = exc.captured_head
        captured_body = exc.captured_body
        decoded_entity = exc.decoded_body
    if captured_head != head or captured_body != raw_transfer_body:
        raise ProtocolError("accepted v2 parser custody projection mismatch")
    observation = {
        "accepted": modeled["inert_transcript_accepted"],
        "parent_terminal_state": modeled["terminal_state"],
        "failure_code": modeled["failure_code"],
        "parent_modeled_outcome_record_sha256": modeled["record_sha256"],
        "previous_qualification_outcome_sha256": modeled[
            "previous_qualification_outcome_sha256"
        ],
        "diagnostic_field_types_sha256": (
            parent.OUTCOME_DIAGNOSTIC_FIELD_TYPES_SHA256
        ),
        "diagnostics": diagnostics,
        "decoded_entity": decoded_entity,
        "raw_head_bytes": len(head),
        "raw_head_sha256": _sha256(head),
        "raw_transfer_body_bytes": len(raw_transfer_body),
        "raw_transfer_body_sha256": _sha256(raw_transfer_body),
        "decoded_entity_bytes": len(decoded_entity),
        "decoded_entity_sha256": _sha256(decoded_entity),
        "parent_parser_error_type": parser_error_type,
        "parent_parser_error_text": parser_error_text,
    }
    # The 36 fields are also projected at top level for exact differential
    # comparison, while the nested copy remains an explicit closed roster for
    # operational outcome custody.
    observation.update(diagnostics)
    return observation, transcript, modeled


def _qualify_retained_response_observation(
    head: bytes,
    raw_transfer_body: bytes,
    *,
    row_ordinal: int = 0,
    tls_version: str = "TLSv1.3",
    alpn: str = "http/1.1",
    cipher_name: str = "QUALIFICATION-ONLY-CIPHER",
    cipher_protocol: str = "TLSv1.3",
    cipher_bits: int = 256,
    peer_certificate_bytes: bytes = b"qualification-only-certificate",
    terminal_eof: bool = True,
    prior_parent_transcript: Any | None = None,
    prior_parent_outcome: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the byte-pinned accepted v2 parser and preserve its 36 diagnostics."""

    observation, _transcript, _modeled = _qualify_retained_response_context(
        head,
        raw_transfer_body,
        row_ordinal=row_ordinal,
        tls_version=tls_version,
        alpn=alpn,
        cipher_name=cipher_name,
        cipher_protocol=cipher_protocol,
        cipher_bits=cipher_bits,
        peer_certificate_bytes=peer_certificate_bytes,
        terminal_eof=terminal_eof,
        prior_parent_transcript=prior_parent_transcript,
        prior_parent_outcome=prior_parent_outcome,
    )
    return observation


def qualify_retained_response(
    head: bytes,
    raw_transfer_body: bytes,
    *,
    row_ordinal: int = 0,
    tls_version: str = "TLSv1.3",
    alpn: str = "http/1.1",
    cipher_name: str = "QUALIFICATION-ONLY-CIPHER",
    cipher_protocol: str = "TLSv1.3",
    cipher_bits: int = 256,
    peer_certificate_bytes: bytes = b"qualification-only-certificate",
    terminal_eof: bool = True,
    prior_row0: tuple[bytes, bytes] | None = None,
) -> dict[str, Any]:
    """Qualify exact retained bytes or raise the accepted v2 error class."""

    if type(head) is not bytes or type(raw_transfer_body) is not bytes:
        raise TypeError("qualification accepts exact bytes only")
    if len(raw_transfer_body) > MAX_RAW_TRANSFER_BODY_BYTES:
        parent = _ensure_parent_parser()
        try:
            parent._receive_response((head + raw_transfer_body, b""))
        except parent.ProtocolError as exc:
            raise ProtocolError(str(exc)) from exc
        except parent.ScopeError as exc:
            raise ScopeError(str(exc)) from exc
        except (parent.ContentError, parent.TransportError) as exc:
            raise ContentError(str(exc)) from exc
        raise ContentError("accepted v2 did not reject oversized transfer body")
    prior_parent_transcript: Any | None = None
    prior_parent_outcome: dict[str, Any] | None = None
    if row_ordinal == 1:
        if (
            type(prior_row0) is not tuple
            or len(prior_row0) != 2
            or type(prior_row0[0]) is not bytes
            or type(prior_row0[1]) is not bytes
        ):
            raise TypeError("row 1 qualification requires exact retained row 0 bytes")
        prior_observation, prior_parent_transcript, prior_parent_outcome = (
            _qualify_retained_response_context(
                prior_row0[0], prior_row0[1], row_ordinal=0
            )
        )
        if prior_observation["accepted"] is not True:
            raise GateError("row 1 prior row 0 qualification is not accepted")
    elif prior_row0 is not None:
        raise TypeError("row 0 qualification forbids prior row 0 bytes")
    observation = _qualify_retained_response_observation(
        head,
        raw_transfer_body,
        row_ordinal=row_ordinal,
        tls_version=tls_version,
        alpn=alpn,
        cipher_name=cipher_name,
        cipher_protocol=cipher_protocol,
        cipher_bits=cipher_bits,
        peer_certificate_bytes=peer_certificate_bytes,
        terminal_eof=terminal_eof,
        prior_parent_transcript=prior_parent_transcript,
        prior_parent_outcome=prior_parent_outcome,
    )
    if observation["accepted"] is True:
        return observation
    error_type = observation["parent_parser_error_type"]
    message = observation["parent_parser_error_text"] or observation["failure_code"]
    if error_type == "ProtocolError":
        raise ProtocolError(message)
    if error_type == "ScopeError":
        raise ScopeError(message)
    if error_type in {"ContentError", "TransportError"}:
        raise ContentError(message)
    raise ExecutorError(f"accepted v2 parser returned unknown failure: {error_type}")


def _recv_exact_response(
    tls: ssl.SSLSocket,
    head_sink: Sidecar,
    body_sink: Sidecar,
    overflow_sink: Sidecar,
    deadline: float,
) -> tuple[bytes, bytes, str | None, str | None]:
    head_deadline = min(deadline, time.monotonic() + HEAD_SECONDS)
    head_memory = bytearray()
    pending = bytearray()
    initial_body = b""
    while True:
        try:
            tls.settimeout(_remaining(head_deadline, HEAD_SECONDS))
            remaining = MAX_STATUS_AND_HEADERS_BYTES - len(head_memory)
            chunk = tls.recv(min(16_384, remaining + 1))
        except BaseException as exc:
            if pending:
                head_sink.write(bytes(pending), MAX_STATUS_AND_HEADERS_BYTES)
                head_memory.extend(pending)
            return bytes(head_memory), b"", None, f"{type(exc).__name__}: {str(exc)[:2048]}"
        if not chunk:
            if pending:
                head_sink.write(bytes(pending), MAX_STATUS_AND_HEADERS_BYTES)
                head_memory.extend(pending)
            return bytes(head_memory), b"", None, None
        candidate = bytes(pending) + chunk
        boundary = candidate.find(b"\r\n\r\n")
        if boundary >= 0:
            through = boundary + 4
            head_piece = candidate[:through]
            if len(head_memory) + len(head_piece) > MAX_STATUS_AND_HEADERS_BYTES:
                accepted = head_piece[: MAX_STATUS_AND_HEADERS_BYTES - len(head_memory)]
                if accepted:
                    head_sink.write(accepted, MAX_STATUS_AND_HEADERS_BYTES)
                    head_memory.extend(accepted)
                overflow_sink.write(
                    head_piece[len(accepted) :][:1], 1
                )
                return bytes(head_memory), b"", "HEAD", None
            head_sink.write(head_piece, MAX_STATUS_AND_HEADERS_BYTES)
            head_memory.extend(head_piece)
            initial_body = candidate[through:]
            break
        if len(head_memory) + len(candidate) > MAX_STATUS_AND_HEADERS_BYTES:
            overflow_sink.write(
                candidate[MAX_STATUS_AND_HEADERS_BYTES - len(head_memory) :][:1], 1
            )
            if len(head_memory) < MAX_STATUS_AND_HEADERS_BYTES:
                accepted = candidate[: MAX_STATUS_AND_HEADERS_BYTES - len(head_memory)]
                head_sink.write(accepted, MAX_STATUS_AND_HEADERS_BYTES)
                head_memory.extend(accepted)
            return bytes(head_memory), b"", "HEAD", None
        safe = max(0, len(candidate) - 3)
        if safe:
            head_sink.write(candidate[:safe], MAX_STATUS_AND_HEADERS_BYTES)
            head_memory.extend(candidate[:safe])
        pending = bytearray(candidate[safe:])
    head = bytes(head_memory)
    body_deadline = min(deadline, time.monotonic() + BODY_SECONDS)
    raw = bytearray()
    if initial_body:
        if len(initial_body) > MAX_RAW_TRANSFER_BODY_BYTES:
            body_sink.write(initial_body[:MAX_RAW_TRANSFER_BODY_BYTES], MAX_RAW_TRANSFER_BODY_BYTES)
            raw.extend(initial_body[:MAX_RAW_TRANSFER_BODY_BYTES])
            overflow_sink.write(initial_body[MAX_RAW_TRANSFER_BODY_BYTES :][:1], 1)
            return head, bytes(raw), "BODY", None
        body_sink.write(initial_body, MAX_RAW_TRANSFER_BODY_BYTES)
        raw.extend(initial_body)
    while True:
        try:
            tls.settimeout(_remaining(body_deadline, BODY_SECONDS))
            remaining = MAX_RAW_TRANSFER_BODY_BYTES - len(raw)
            chunk = tls.recv(min(65_536, remaining + 1))
        except BaseException as exc:
            return head, bytes(raw), None, f"{type(exc).__name__}: {str(exc)[:2048]}"
        if not chunk:
            return head, bytes(raw), None, None
        if len(chunk) > remaining:
            if remaining:
                body_sink.write(chunk[:remaining], MAX_RAW_TRANSFER_BODY_BYTES)
                raw.extend(chunk[:remaining])
            overflow_sink.write(chunk[remaining:][:1], 1)
            return head, bytes(raw), "BODY", None
        body_sink.write(chunk, MAX_RAW_TRANSFER_BODY_BYTES)
        raw.extend(chunk)


def _numeric_sockaddr(row: Mapping[str, Any]) -> tuple[Any, ...]:
    if row["family"] == AF_INET_INT:
        return (row["numeric_ip"], 443)
    return (row["numeric_ip"], 443, row["flowinfo"], row["scope_id"])


def _validate_resolver_receipt_rows(
    rows: Any, op: ExactOperation
) -> list[dict[str, Any]]:
    exact_keys = {
        "family",
        "socktype",
        "protocol",
        "canonical_name",
        "numeric_ip",
        "port",
        "flowinfo",
        "scope_id",
        "queried_host",
    }
    if type(rows) is not list or not rows or len(rows) > 128:
        raise GateError("resolver receipt roster invalid")
    for row in rows:
        if type(row) is not dict or set(row) != exact_keys:
            raise GateError("resolver receipt row schema invalid")
        if (
            type(row["family"]) is not int
            or type(row["socktype"]) is not int
            or type(row["protocol"]) is not int
            or type(row["port"]) is not int
            or type(row["flowinfo"]) is not int
            or type(row["scope_id"]) is not int
            or row["family"] not in {AF_INET_INT, AF_INET6_INT}
            or row["socktype"] != SOCK_STREAM_INT
            or row["protocol"] != IPPROTO_TCP_INT
            or row["port"] != 443
            or row["queried_host"] != op.host
            or type(row["canonical_name"]) is not str
            or type(row["numeric_ip"]) is not str
            or not 0 <= row["flowinfo"] <= 0xFFFFF
            or not 0 <= row["scope_id"] <= 0xFFFFFFFF
            or len(row["canonical_name"].encode("utf-8", "surrogateescape")) > 1024
            or any(
                ord(character) < 0x20 or ord(character) == 0x7F
                for character in row["canonical_name"]
            )
        ):
            raise GateError("resolver receipt row value invalid")
        try:
            address = ipaddress.ip_address(row["numeric_ip"])
        except ValueError as exc:
            raise GateError("resolver receipt numeric address invalid") from exc
        if (
            not address.is_global
            or str(address) != row["numeric_ip"]
            or (row["family"] == AF_INET_INT) is not isinstance(
                address, ipaddress.IPv4Address
            )
        ):
            raise GateError("resolver receipt address/family/global relation invalid")
    return rows


def _tls_metadata(tls: ssl.SSLSocket, chosen: Mapping[str, Any]) -> dict[str, Any]:
    peer_cert = tls.getpeercert(binary_form=True)
    if not peer_cert:
        raise ExecutorError("peer certificate bytes unavailable")
    cipher = tls.cipher()
    ssl_object = getattr(tls, "_sslobj", None)
    if ssl_object is None or not hasattr(ssl_object, "get_verified_chain"):
        raise ExecutorError("verified TLS chain API unavailable")
    chain = ssl_object.get_verified_chain()
    if type(chain) is not list or not chain or len(chain) > 32:
        raise ExecutorError("verified TLS chain roster invalid")
    chain_receipts: list[dict[str, Any]] = []
    for ordinal, cert in enumerate(chain):
        rendered = cert.public_bytes()
        raw = rendered.encode("ascii") if type(rendered) is str else bytes(rendered)
        if not raw or len(raw) > 65_536:
            raise ExecutorError("verified TLS certificate receipt outside cap")
        chain_receipts.append(
            {"ordinal": ordinal, "public_bytes_sha256": _sha256(raw), "bytes": len(raw)}
        )
    return {
        "chosen_endpoint": dict(chosen),
        "tls_version": tls.version(),
        "cipher": list(cipher) if cipher is not None else None,
        "selected_alpn": tls.selected_alpn_protocol(),
        "peer_certificate_der_sha256": _sha256(peer_cert),
        "peer_certificate_der_bytes": len(peer_cert),
        "peer_certificate_der_base64": base64.b64encode(peer_cert).decode("ascii"),
        "verified_chain_public_byte_receipts": chain_receipts,
        "hostname_verification": True,
        "sni_host": chosen["queried_host"],
        "minimum_tls": "TLSv1_2",
        "maximum_tls": "TLSv1_3",
        "session_resumption_disabled": True,
        "session_reused": tls.session_reused,
        "client_certificate_loaded": False,
    }


def _validate_tls_metadata_record(
    metadata: Any, op: ExactOperation, resolver_rows: Any
) -> tuple[list[Any], bytes]:
    exact_keys = {
        "chosen_endpoint",
        "tls_version",
        "cipher",
        "selected_alpn",
        "peer_certificate_der_sha256",
        "peer_certificate_der_bytes",
        "peer_certificate_der_base64",
        "verified_chain_public_byte_receipts",
        "hostname_verification",
        "sni_host",
        "minimum_tls",
        "maximum_tls",
        "session_resumption_disabled",
        "session_reused",
        "client_certificate_loaded",
        "ca_before_and_after_load_receipt",
    }
    if type(metadata) is not dict or set(metadata) != exact_keys:
        raise GateError("TLS metadata key roster invalid")
    rows = _validate_resolver_receipt_rows(resolver_rows, op)
    if metadata["chosen_endpoint"] != rows[0]:
        raise GateError("TLS chosen endpoint is not first resolver row")
    cipher = metadata["cipher"]
    if (
        type(cipher) is not list
        or len(cipher) != 3
        or type(cipher[0]) is not str
        or not cipher[0]
        or type(cipher[1]) is not str
        or not cipher[1]
        or type(cipher[2]) is not int
        or cipher[2] <= 0
    ):
        raise GateError("TLS cipher receipt invalid")
    if (
        metadata["tls_version"] not in {"TLSv1.2", "TLSv1.3"}
        or metadata["selected_alpn"] != "http/1.1"
        or metadata["hostname_verification"] is not True
        or metadata["sni_host"] != op.host
        or metadata["minimum_tls"] != "TLSv1_2"
        or metadata["maximum_tls"] != "TLSv1_3"
        or metadata["session_resumption_disabled"] is not True
        or metadata["session_reused"] is not False
        or metadata["client_certificate_loaded"] is not False
    ):
        raise GateError("TLS policy receipt invalid")
    try:
        certificate = base64.b64decode(
            metadata["peer_certificate_der_base64"], validate=True
        )
    except (TypeError, ValueError) as exc:
        raise GateError("TLS peer certificate encoding invalid") from exc
    if (
        not certificate
        or len(certificate) > 1_048_576
        or metadata["peer_certificate_der_bytes"] != len(certificate)
        or metadata["peer_certificate_der_sha256"] != _sha256(certificate)
    ):
        raise GateError("TLS peer certificate receipt invalid")
    chain = metadata["verified_chain_public_byte_receipts"]
    if type(chain) is not list or not chain or len(chain) > 32:
        raise GateError("TLS verified chain receipt invalid")
    for ordinal, item in enumerate(chain):
        if (
            type(item) is not dict
            or set(item) != {"ordinal", "public_bytes_sha256", "bytes"}
            or item["ordinal"] != ordinal
            or type(item["ordinal"]) is not int
            or type(item["bytes"]) is not int
            or not 0 < item["bytes"] <= 65_536
            or type(item["public_bytes_sha256"]) is not str
            or re.fullmatch(r"[0-9a-f]{64}", item["public_bytes_sha256"]) is None
        ):
            raise GateError("TLS verified chain member invalid")
    ca = metadata["ca_before_and_after_load_receipt"]
    if (
        type(ca) is not dict
        or ca.get("path") != EXPECTED_CA_PATH
        or ca.get("sha256") != EXPECTED_CA_SHA256
    ):
        raise GateError("TLS CA receipt invalid")
    return cipher, certificate


def _apply_receive_terminal_precedence(
    qualified: dict[str, Any],
    overflow_kind: str | None,
    transport_error: str | None,
) -> None:
    """Apply protocol > scope > transport/content terminal precedence."""

    if overflow_kind not in {None, "HEAD", "BODY"}:
        raise ExecutorError("unknown overflow classification")
    if transport_error is not None and type(transport_error) is not str:
        raise ExecutorError("transport error classification is not exact text")
    parser_message = qualified.get("parent_parser_error_text")
    incomplete_failure = parser_message in {
        "EOF before complete response head",
        "connection-close framing requires explicit terminal inert EOF marker",
        "Content-Length body incomplete",
        "incomplete chunked body",
    }
    if overflow_kind == "HEAD":
        qualified["accepted"] = False
        qualified["failure_code"] = "PROTOCOL_VIOLATION"
        qualified["parent_terminal_state"] = (
            "QUALIFICATION_ONLY_TERMINAL_PROTOCOL_VIOLATION_NO_RETRY"
        )
    elif overflow_kind == "BODY":
        # A cap-plus-one body is transport/content no-go unless the retained
        # prefix already proves a complete higher-priority scope or intrinsic
        # protocol violation.  Incompleteness caused by truncation is not
        # promoted to protocol failure.
        fixed_framing_overrun = (
            qualified.get("framing") in {"CONTENT_LENGTH", "CHUNKED"}
            and qualified.get("framing_complete") is True
        )
        preserve = qualified.get("failure_code") == "SCOPE_VIOLATION" or (
            qualified.get("failure_code") == "PROTOCOL_VIOLATION"
            and not incomplete_failure
        )
        if fixed_framing_overrun:
            qualified["accepted"] = False
            qualified["failure_code"] = "PROTOCOL_VIOLATION"
            qualified["parent_terminal_state"] = (
                "QUALIFICATION_ONLY_TERMINAL_PROTOCOL_VIOLATION_NO_RETRY"
            )
        elif not preserve:
            qualified["accepted"] = False
            qualified["failure_code"] = "TRANSPORT_OR_CONTENT_NO_GO"
            qualified["parent_terminal_state"] = (
                "QUALIFICATION_ONLY_TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY"
            )
        qualified["diagnostics"]["body_truncated"] = True
        qualified["body_truncated"] = True
    if transport_error is not None:
        # A fully evidenced protocol or scope refusal outranks a later receive
        # error.  Parser failures that merely say the response is incomplete
        # are consequences of that transport error and do not outrank it.
        preserve = qualified.get("failure_code") == "SCOPE_VIOLATION" or (
            qualified.get("failure_code") == "PROTOCOL_VIOLATION"
            and not incomplete_failure
        )
        if not preserve:
            qualified["accepted"] = False
            qualified["failure_code"] = "TRANSPORT_FAILURE"
            qualified["parent_terminal_state"] = (
                "QUALIFICATION_ONLY_TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY"
            )
        qualified["transport_receive_error"] = transport_error


def _perform_spent_attempt(
    op: ExactOperation,
    sidecars: Mapping[str, Sidecar],
    deadline: float,
    progress: AttemptProgress,
    prior_parent_context: tuple[Any, Mapping[str, Any]] | None,
) -> dict[str, Any]:
    resolver_rows = _validate_resolver_receipt_rows(
        _bounded_single_getaddrinfo(op.host, deadline, progress), op
    )
    chosen = resolver_rows[0]
    family = chosen["family"]
    progress.socket_instance_count += 1
    raw_socket = socket.socket(family, SOCK_STREAM_INT, IPPROTO_TCP_INT)
    try:
        raw_socket.settimeout(_remaining(deadline, CONNECT_SECONDS))
        progress.connect_call_count += 1
        raw_socket.connect(_numeric_sockaddr(chosen))
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        context.options |= getattr(ssl, "OP_NO_TICKET", 0)
        ca_before = _hash_path_nofollow(EXPECTED_CA_PATH)
        if ca_before["sha256"] != EXPECTED_CA_SHA256:
            raise ExecutorError("CA receipt drift before TLS load")
        context.load_verify_locations(cafile=EXPECTED_CA_PATH)
        ca_after = _hash_path_nofollow(EXPECTED_CA_PATH)
        if ca_after != ca_before:
            raise ExecutorError("CA bytes/stat changed across TLS load")
        context.set_alpn_protocols(["http/1.1"])
        progress.tls_wrap_call_count += 1
        tls = context.wrap_socket(
            raw_socket,
            server_hostname=op.host,
            do_handshake_on_connect=False,
        )
        raw_socket = None  # type: ignore[assignment]
        try:
            tls.settimeout(_remaining(deadline, TLS_SECONDS))
            tls.do_handshake()
            if tls.selected_alpn_protocol() != "http/1.1":
                raise ProtocolError("ALPN is not exact http/1.1")
            if tls.session_reused is not False:
                raise ProtocolError("TLS session reuse forbidden")
            metadata = _tls_metadata(tls, chosen)
            metadata["ca_before_and_after_load_receipt"] = ca_before
            cipher, peer_certificate = _validate_tls_metadata_record(
                metadata, op, resolver_rows
            )
            metadata_raw = _canonical_bytes(metadata)
            sidecars["tls-metadata.raw"].write(metadata_raw, MAX_TLS_METADATA_BYTES)
            tls.settimeout(_remaining(deadline, SEND_SECONDS))
            progress.sendall_call_count += 1
            progress.request_emission_state = "UNKNOWN_AFTER_SENDALL_ENTERED"
            tls.sendall(op.request_bytes)
            progress.request_emission_state = "COMPLETED_PLAINTEXT_PASSED_TO_TLS"
            head, raw_body, overflow_kind, transport_error = _recv_exact_response(
                tls,
                sidecars["response-head.raw"],
                sidecars["transfer-body.raw"],
                sidecars["overflow-witness.raw"],
                deadline,
            )
        finally:
            tls.close()
    finally:
        if raw_socket is not None:
            raw_socket.close()
    qualified = _qualify_retained_response_observation(
        head,
        raw_body,
        row_ordinal=op.ordinal,
        tls_version=metadata["tls_version"],
        alpn=metadata["selected_alpn"],
        cipher_name=cipher[0],
        cipher_protocol=cipher[1],
        cipher_bits=cipher[2],
        peer_certificate_bytes=peer_certificate,
        terminal_eof=(transport_error is None and overflow_kind is None),
        prior_parent_transcript=(
            None if prior_parent_context is None else prior_parent_context[0]
        ),
        prior_parent_outcome=(
            None if prior_parent_context is None else prior_parent_context[1]
        ),
    )
    _apply_receive_terminal_precedence(qualified, overflow_kind, transport_error)
    entity = qualified.pop("decoded_entity")
    sidecars["decoded-entity.raw"].write(entity, MAX_DECODED_ENTITY_BYTES)
    return qualified


def _terminal_for_exception(exc: BaseException) -> str:
    if isinstance(exc, ProtocolError):
        return "TERMINAL_PROTOCOL_VIOLATION_NO_RETRY"
    if isinstance(exc, ScopeError):
        return "TERMINAL_SCOPE_VIOLATION_NO_RETRY"
    return "TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY"


def _error_record(
    op: ExactOperation,
    intent_digest: str,
    exc: BaseException,
    progress: AttemptProgress,
) -> dict[str, Any]:
    return {
        "schema_version": ERROR_SCHEMA,
        "record_sha256": None,
        "row_ordinal": op.ordinal,
        "operation_id": op.operation_id,
        "intent_record_sha256": intent_digest,
        "error_type": type(exc).__name__,
        "error_text": str(exc)[:4096],
        "request_emission_state": progress.request_emission_state,
        "resolver_child_fork_site_count": progress.resolver_child_fork_site_count,
        "resolver_high_level_call_count": progress.resolver_high_level_call_count,
        "socket_instance_count": progress.socket_instance_count,
        "connect_call_count": progress.connect_call_count,
        "tls_wrap_call_count": progress.tls_wrap_call_count,
        "sendall_call_count": progress.sendall_call_count,
        "terminal_state": _terminal_for_exception(exc),
        "retry_permitted": False,
    }


def _exclusive_precomputed_successor_budget_marker(
    rootfd: int, marker_raw: bytes, marker_digest: str
) -> os.stat_result:
    """Write already-final canonical marker bytes; O_EXCL open is first action."""

    fd = os.open("successor-budget-spend.json", FILE_CREATE_FLAGS, 0o600, dir_fd=rootfd)
    try:
        st0 = os.fstat(fd)
        _validate_regular_receipt_stat(st0, mode=0o600)
        _write_all(fd, marker_raw)
        os.fsync(fd)
        st1 = os.fstat(fd)
        _validate_regular_receipt_stat(st1, mode=0o600)
        if (st0.st_dev, st0.st_ino) != (st1.st_dev, st1.st_ino):
            raise CustodyError("successor budget marker identity changed")
    finally:
        os.close(fd)
    os.fsync(rootfd)
    if _sha256(marker_raw) != marker_digest:
        raise CustodyError("precomputed successor budget marker digest drift")
    return st1


def _spend_successor_budget_after_last_authority_gate(
    rootfd: int,
    op: ExactOperation,
    package_lock: Mapping[str, Any],
    preflight: Mapping[str, Any],
    go: Mapping[str, Any],
    root: Mapping[str, Any],
    supersession: Mapping[str, Any],
) -> tuple[dict[str, Any], str]:
    """Perform the last authority gate and irreversibly reserve the V5 budget."""

    if _entry_exists_at(rootfd, "successor-budget-spend.json"):
        raise CustodyError("successor budget marker already exists; budget is spent")
    if _entry_exists_at(rootfd, "row0-authority.revoked"):
        raise GateError("row authority revocation slot is present")
    authority = _validate_row_authority(
        rootfd, op, package_lock, preflight, go, root, None
    )
    record = {
        "schema_version": SUCCESSOR_BUDGET_SPEND_SCHEMA,
        "record_sha256": None,
        "successor_budget_definition_id": SUCCESSOR_BUDGET_DEFINITION_ID,
        "activated_successor_budget_id": supersession["activated_successor_budget_id"],
        "successor_budget_scope": SUCCESSOR_BUDGET_SCOPE,
        "row_ordinal": 0,
        "row1_may_consume": False,
        "operation_id": op.operation_id,
        "exact_url": op.url,
        "exact_request_bytes": len(op.request_bytes),
        "exact_request_sha256": _sha256(op.request_bytes),
        "package_aggregate_sha256": package_lock["package_aggregate_sha256"],
        "package_lock_record_sha256": package_lock["record_sha256"],
        "preflight_authority_record_sha256": preflight["preflight_authority_record_sha256"],
        "runtime_manifest_sha256": preflight["runtime_manifest_sha256"],
        "supersession_authority_record_sha256": supersession["record_sha256"],
        "runtime_preflight_record_sha256": preflight["record_sha256"],
        "independent_go_record_sha256": go["record_sha256"],
        "authority_record_sha256": authority["record_sha256"],
        "authority_expires_unix_ns": authority["expires_unix_ns"],
        "authority_negated_or_revoked": authority["negated_or_revoked"],
        "authority_revocation_slot_absent": True,
        "custody_root": root,
        "v4_package_aggregate_sha256": V4_PACKAGE_AGGREGATE_SHA256,
        "v4_machine_raw_sha256": V4_MACHINE_RAW_SHA256,
        "v4_machine_semantic_sha256": V4_MACHINE_SEMANTIC_SHA256,
        "v2_package_aggregate_sha256": V2_PACKAGE_AGGREGATE_SHA256,
        "v2_intent_raw_sha256": V2_INTENT_RAW_SHA256,
        "v2_intent_semantic_sha256": V2_INTENT_SEMANTIC_SHA256,
        "v2_error_raw_sha256": V2_ERROR_RAW_SHA256,
        "v2_error_semantic_sha256": V2_ERROR_SEMANTIC_SHA256,
        "v2_outcome_raw_sha256": V2_OUTCOME_RAW_SHA256,
        "v2_outcome_semantic_sha256": V2_OUTCOME_SEMANTIC_SHA256,
        "resolver_high_level_call_limit": 1,
        "resolver_child_fork_site_limit": 1,
        "socket_instance_limit": 1,
        "connect_limit": 1,
        "tls_wrap_limit": 1,
        "address_fallback_limit": 0,
        "request_send_limit": 1,
        "attempt_limit": 1,
        "retry_limit": 0,
        "redirect_limit": 0,
        "v2_attempt_spend_acknowledged": True,
        "acknowledge_v2_row0_spent_at_durable_intent": True,
        "acknowledge_v2_terminal_no_retry": True,
        "acknowledge_sendall_zero_does_not_restore_budget": True,
        "v2_receipts_reused": False,
        "version_or_root_reset_spent_budget": False,
        "created_unix_ns": time.time_ns(),
    }
    record["record_sha256"] = _self_digest(record)
    marker_raw = _canonical_bytes(record)
    marker_digest = _sha256(marker_raw)
    authority_reopened, authority_raw, authority_st = _read_receipt_at(
        rootfd, "row0-authority.json",
        schema=ROW_AUTHORITY_SCHEMA, exact_keys=ROW_AUTHORITY_KEYS,
    )
    if authority_reopened != authority:
        raise CustodyError("final row authority changed at spend boundary")
    if (
        stat.S_IMODE(authority_st.st_mode) != 0o600
        or authority_st.st_nlink != 1
        or time.time_ns() > authority["expires_unix_ns"]
        or authority["negated_or_revoked"] is not False
        or _entry_exists_at(rootfd, "row0-authority.revoked")
    ):
        raise GateError("final row authority failed last spend gate")
    _exclusive_precomputed_successor_budget_marker(rootfd, marker_raw, marker_digest)
    _reopen_exact_digest_at(rootfd, "successor-budget-spend.json", marker_digest)
    reopened, raw, _ = _read_receipt_at(
        rootfd, "successor-budget-spend.json",
        schema=SUCCESSOR_BUDGET_SPEND_SCHEMA,
        exact_keys=SUCCESSOR_BUDGET_SPEND_KEYS,
    )
    if reopened != record or _sha256(authority_raw) != _sha256(_canonical_bytes(authority)):
        raise CustodyError("successor budget marker/authority reopen mismatch")
    return reopened, _sha256(raw)


def _late_pretransport_gate(
    rootfd: int,
    authority: Mapping[str, Any],
    spend: Mapping[str, Any],
    spend_raw_sha256: str,
    expected_root_roster: set[str],
) -> None:
    """Last read-only gate; caller must invoke transport in the next statement."""

    authority_after, authority_raw, authority_st = _read_receipt_at(
        rootfd, "row0-authority.json",
        schema=ROW_AUTHORITY_SCHEMA, exact_keys=ROW_AUTHORITY_KEYS,
    )
    if (
        authority_after != authority
        or _sha256(authority_raw) != _sha256(_canonical_bytes(authority))
        or stat.S_IMODE(authority_st.st_mode) != 0o600
        or authority_st.st_nlink != 1
        or authority.get("negated_or_revoked") is not False
        or time.time_ns() > authority.get("expires_unix_ns", 0)
        or _entry_exists_at(rootfd, "row0-authority.revoked")
    ):
        raise GateError("late pre-transport authority/revocation/expiry gate failed")
    spend_after, spend_raw, _ = _read_receipt_at(
        rootfd, "successor-budget-spend.json",
        schema=SUCCESSOR_BUDGET_SPEND_SCHEMA,
        exact_keys=SUCCESSOR_BUDGET_SPEND_KEYS,
    )
    if spend_after != spend or _sha256(spend_raw) != spend_raw_sha256:
        raise CustodyError("late pre-transport successor spend gate failed")
    _require_root_roster(rootfd, expected_root_roster)


def attempt(custody_root: str) -> str:
    """Run the exact gated row attempt.  A durable intent always spends it."""

    _require_production_process("attempt", custody_root, None)
    os.umask(0o077)
    _require_fd_baseline()
    row = 0
    op = OPERATIONS[0]
    machine, machine_raw = _load_machine()
    rootfd, root_st = _open_root(custody_root)
    rowfd: int | None = None
    sidecars: dict[str, Sidecar] = {}
    try:
        _require_machine_bound_root(machine, custody_root, root_st, rootfd)
        _require_fd_baseline(frozenset({rootfd}))
        _require_root_roster(
            rootfd, _expected_root_before_row_phase(row, "ATTEMPT")
        )
        root = _root_identity(custody_root, root_st)
        package_lock = _load_package_lock(rootfd, machine, machine_raw)
        preflight_receipt = _validate_runtime_preflight(
            rootfd, custody_root, root_st, package_lock
        )
        row0_outcome = None
        go = _validate_go(
            rootfd, op, package_lock, preflight_receipt, row0_outcome
        )
        authority = _validate_row_authority(
            rootfd,
            op,
            package_lock,
            preflight_receipt,
            go,
            root,
            row0_outcome,
        )
        supersession = _validate_supersession_authority(rootfd, package_lock, root)
        spend, spend_raw_sha256 = _spend_successor_budget_after_last_authority_gate(
            rootfd, op, package_lock, preflight_receipt, go, root, supersession
        )
        gate_basenames = (
            "package-lock.json",
            "supersession-authority.json",
            "preflight-authority.json",
            "runtime-preflight.json",
            f"row{op.ordinal}-independent-go.json",
            f"row{op.ordinal}-authority.json",
            "successor-budget-spend.json",
        )
        gate_identity_before = [
            _identity_digest_at(rootfd, basename) for basename in gate_basenames
        ]
        package_identity_before = _package_runtime_identity_snapshot(machine)
        _revalidate_runtime_immediately_before_reservation(
            custody_root, root_st, preflight_receipt
        )
        authority_after_spend = _validate_row_authority(
            rootfd, op, package_lock, preflight_receipt, go, root, None
        )
        if (
            authority_after_spend != authority
            or _entry_exists_at(rootfd, "row0-authority.revoked")
            or time.time_ns() > authority["expires_unix_ns"]
        ):
            raise GateError("row authority changed/revoked/expired after budget spend")
        if _entry_exists_at(rootfd, op.row_basename):
            raise CustodyError("row directory already exists; attempt cannot start or retry")
        rowfd, row_st = _mkdir_row(rootfd, root_st, op)
        root_after_mkdir = os.fstat(rootfd)
        if (
            root_after_mkdir.st_dev,
            root_after_mkdir.st_ino,
            root_after_mkdir.st_uid,
            root_after_mkdir.st_gid,
            stat.S_IMODE(root_after_mkdir.st_mode),
        ) != (
            root_st.st_dev,
            root_st.st_ino,
            root_st.st_uid,
            root_st.st_gid,
            0o700,
        ):
            raise CustodyError("custody root identity changed during row reservation")
        if root_after_mkdir.st_nlink not in {root_st.st_nlink, root_st.st_nlink + 1}:
            raise CustodyError("custody root link-count transition invalid")
        sidecars = _create_sidecars(rowfd, row_st)
        sidecars["request.raw"].write(op.request_bytes, len(op.request_bytes))
        os.fsync(sidecars["request.raw"].fd)
        for sidecar in sidecars.values():
            sidecar.verify_current_bytes()
        os.fsync(rowfd)
        intent = _make_intent(
            op,
            package_lock,
            preflight_receipt,
            go,
            authority,
            root,
            root_after_mkdir,
            row_st,
            sidecars,
            row0_outcome,
            spend,
            spend_raw_sha256,
        )
        intent_digest, _ = _exclusive_canonical_at(rowfd, "intent.json", intent)
        _reopen_exact_digest_at(rowfd, "intent.json", intent_digest)
        # Byte-reopen every pre-network gate after intent durability.  Exact
        # semantic equality rejects replacement even when a forged digest field
        # is internally consistent.
        package_lock_after = _load_package_lock(rootfd, machine, machine_raw)
        preflight_after, _, _ = _read_receipt_at(
            rootfd,
            "runtime-preflight.json",
            schema=RUNTIME_PREFLIGHT_SCHEMA,
            exact_keys=RUNTIME_PREFLIGHT_KEYS,
        )
        go_after, _, _ = _read_receipt_at(
            rootfd,
            f"row{op.ordinal}-independent-go.json",
            schema=INDEPENDENT_GO_SCHEMA,
            exact_keys=INDEPENDENT_GO_KEYS,
        )
        authority_after, _, _ = _read_receipt_at(
            rootfd,
            f"row{op.ordinal}-authority.json",
            schema=ROW_AUTHORITY_SCHEMA,
            exact_keys=ROW_AUTHORITY_KEYS,
        )
        spend_after, spend_raw_after, _ = _read_receipt_at(
            rootfd, "successor-budget-spend.json",
            schema=SUCCESSOR_BUDGET_SPEND_SCHEMA,
            exact_keys=SUCCESSOR_BUDGET_SPEND_KEYS,
        )
        if package_lock_after != package_lock or preflight_after != preflight_receipt:
            raise CustodyError("package/runtime gate replaced after intent")
        if go_after != go or authority_after != authority:
            raise CustodyError("GO/authority gate replaced after intent")
        if spend_after != spend or _sha256(spend_raw_after) != spend_raw_sha256:
            raise CustodyError("successor budget marker changed after intent")
        gate_identity_after = [
            _identity_digest_at(rootfd, basename) for basename in gate_basenames
        ]
        package_identity_after = _package_runtime_identity_snapshot(machine)
        if gate_identity_after != gate_identity_before:
            raise CustodyError("gate receipt identity changed after intent")
        if package_identity_after != package_identity_before:
            raise CustodyError("package/runtime identity changed after intent")
        if time.time_ns() > authority["expires_unix_ns"]:
            raise GateError("row authority expired after intent before resolver")
        for sidecar in sidecars.values():
            sidecar.verify_current_bytes()
        # No resolver, fork, socket, TLS context, connect, send or receive site is
        # reachable before the preceding intent file and row directory fsyncs.
        deadline = time.monotonic() + TOTAL_ATTEMPT_SECONDS
        progress = AttemptProgress()
        qualified: dict[str, Any] | None = None
        terminal = "TERMINAL_SPENT_INCOMPLETE_NO_RETRY"
        error_digest: str | None = None
        expected_pretransport_root_roster = _expected_root_before_row_phase(
            row, "ATTEMPT"
        ) | {op.row_basename, "successor-budget-spend.json"}
        try:
            _late_pretransport_gate(
                rootfd, authority, spend, spend_raw_sha256,
                expected_pretransport_root_roster,
            )
            qualified = _perform_spent_attempt(
                op,
                sidecars,
                deadline,
                progress,
                None,
            )
            if qualified["accepted"] is True:
                terminal = "TERMINAL_ROOT_PAGE_OBSERVED_UNVERIFIED_NO_RETRY"
            elif qualified["failure_code"] == "PROTOCOL_VIOLATION":
                terminal = "TERMINAL_PROTOCOL_VIOLATION_NO_RETRY"
            elif qualified["failure_code"] == "SCOPE_VIOLATION":
                terminal = "TERMINAL_SCOPE_VIOLATION_NO_RETRY"
            else:
                terminal = "TERMINAL_TRANSPORT_OR_CONTENT_NO_GO_NO_RETRY"
        except BaseException as exc:
            terminal = _terminal_for_exception(exc)
            stderr = f"{type(exc).__name__}: {str(exc)[:4096]}\n".encode(
                "utf-8", "replace"
            )
            sidecars["stderr.raw"].write(stderr, MAX_STDERR_BYTES)
            error = _error_record(op, intent_digest, exc, progress)
            error_digest, _ = _exclusive_canonical_at(rowfd, "error.json", error)
        receipts = [sidecars[name].fsync_and_receipt() for name in SIDECAR_BASENAMES]
        expected_row_names = set(SIDECAR_BASENAMES) | {"intent.json"}
        if error_digest is not None:
            expected_row_names.add("error.json")
        _require_root_roster(rowfd, expected_row_names)
        expected_root_names = _expected_root_before_row_phase(row, "ATTEMPT") | {
            op.row_basename,
            "successor-budget-spend.json",
        }
        _require_root_roster(rootfd, expected_root_names)
        root_final = os.fstat(rootfd)
        row_final = os.fstat(rowfd)
        if (
            root_final.st_dev,
            root_final.st_ino,
            root_final.st_uid,
            root_final.st_gid,
            stat.S_IMODE(root_final.st_mode),
            root_final.st_nlink,
        ) != (
            root_after_mkdir.st_dev,
            root_after_mkdir.st_ino,
            root_after_mkdir.st_uid,
            root_after_mkdir.st_gid,
            0o700,
            root_after_mkdir.st_nlink,
        ):
            raise CustodyError("custody root final identity drift")
        if (
            row_final.st_dev,
            row_final.st_ino,
            row_final.st_uid,
            row_final.st_gid,
            stat.S_IMODE(row_final.st_mode),
        ) != (
            row_st.st_dev,
            row_st.st_ino,
            row_st.st_uid,
            row_st.st_gid,
            0o700,
        ) or not (
            row_st.st_nlink
            <= row_final.st_nlink
            <= row_st.st_nlink + len(expected_row_names)
        ):
            raise CustodyError("row directory final identity drift")
        os.fsync(rowfd)
        outcome = {
            "schema_version": OUTCOME_SCHEMA,
            "record_sha256": None,
            "row_ordinal": op.ordinal,
            "operation_id": op.operation_id,
            "exact_url": op.url,
            "intent_record_sha256": intent_digest,
            "terminal_state": terminal,
            "retry_permitted": False,
            "request_emission_state": progress.request_emission_state,
            "resolver_child_fork_site_count": progress.resolver_child_fork_site_count,
            "resolver_high_level_call_count": progress.resolver_high_level_call_count,
            "resolver_rows": (
                []
                if progress.resolver_result_roster is None
                else progress.resolver_result_roster
            ),
            "socket_instance_count": progress.socket_instance_count,
            "connect_call_count": progress.connect_call_count,
            "tls_wrap_call_count": progress.tls_wrap_call_count,
            "sendall_call_count": progress.sendall_call_count,
            "resolver_packet_count_wire_ttl_cache_server_bound": False,
            "address_fallback_used": False,
            "redirect_followed": False,
            "qualified_root_page_observation": qualified,
            "sidecar_receipts": receipts,
            "error_record_sha256": error_digest,
            "official_source_version_or_license_verified": False,
            "approval_created": False,
            "tracker_or_science_effect": False,
            "created_unix_ns": time.time_ns(),
            "custody_root_final": {
                "device": root_final.st_dev,
                "inode": root_final.st_ino,
                "uid": root_final.st_uid,
                "gid": root_final.st_gid,
                "mode_octal": f"{stat.S_IMODE(root_final.st_mode):04o}",
                "nlink": root_final.st_nlink,
            },
            "row_directory_final": {
                "device": row_final.st_dev,
                "inode": row_final.st_ino,
                "uid": row_final.st_uid,
                "gid": row_final.st_gid,
                "mode_octal": f"{stat.S_IMODE(row_final.st_mode):04o}",
                "nlink": row_final.st_nlink,
            },
        }
        outcome_digest, _ = _exclusive_canonical_at(rowfd, "outcome.json", outcome)
        _require_root_roster(rowfd, expected_row_names | {"outcome.json"})
        _require_root_roster(rootfd, expected_root_names)
        root_post_outcome = os.fstat(rootfd)
        row_post_outcome = os.fstat(rowfd)
        if (
            root_post_outcome.st_dev,
            root_post_outcome.st_ino,
            root_post_outcome.st_uid,
            root_post_outcome.st_gid,
            stat.S_IMODE(root_post_outcome.st_mode),
            root_post_outcome.st_nlink,
        ) != (
            root_final.st_dev,
            root_final.st_ino,
            root_final.st_uid,
            root_final.st_gid,
            0o700,
            root_final.st_nlink,
        ) or (
            row_post_outcome.st_dev,
            row_post_outcome.st_ino,
            row_post_outcome.st_uid,
            row_post_outcome.st_gid,
            stat.S_IMODE(row_post_outcome.st_mode),
        ) != (
            row_final.st_dev,
            row_final.st_ino,
            row_final.st_uid,
            row_final.st_gid,
            0o700,
        ) or row_post_outcome.st_nlink not in {
            row_final.st_nlink,
            row_final.st_nlink + 1,
        }:
            raise CustodyError("root/row identity drift after outcome")
        return outcome_digest
    finally:
        for sidecar in sidecars.values():
            try:
                os.close(sidecar.fd)
            except OSError:
                pass
        if rowfd is not None:
            os.close(rowfd)
        os.close(rootfd)


def _usage() -> NoReturn:
    raise SystemExit(
        "usage: solo_block2_runtime_custody_executor_v5.py "
        "register-package-lock ROOT REVIEWER CREATED_UNIX_NS | "
        "register-supersession-authority ROOT CREATED_UNIX_NS ACTIVATED_BUDGET_ID EXACT_TEXT | "
        "register-preflight-authority ROOT CREATED_UNIX_NS EXACT_TEXT | "
        "preflight ROOT | "
        "register-independent-go ROOT REVIEWER CREATED_UNIX_NS | "
        "register-row-authority ROOT CREATED_UNIX_NS EXPIRES_UNIX_NS EXACT_TEXT | "
        "attempt ROOT"
    )


def main() -> int:
    _normalize_stdio_to_devnull()
    args = list(sys.argv[1:])
    try:
        if len(args) == 2 and args[0] == "preflight":
            digest = preflight(args[1])
        elif len(args) == 4 and args[0] == "register-package-lock":
            digest = register_package_lock(args[1], args[2], int(args[3]))
        elif len(args) == 5 and args[0] == "register-supersession-authority":
            digest = register_supersession_authority(
                args[1], int(args[2]), args[3], args[4]
            )
        elif len(args) == 4 and args[0] == "register-preflight-authority":
            digest = register_preflight_authority(args[1], int(args[2]), args[3])
        elif (
            len(args) == 4
            and args[0] == "register-independent-go"
        ):
            digest = register_independent_go(
                args[1], args[2], int(args[3])
            )
        elif (
            len(args) == 5
            and args[0] == "register-row-authority"
        ):
            digest = register_row_authority(
                args[1],
                int(args[2]),
                int(args[3]),
                args[4],
            )
        elif len(args) == 2 and args[0] == "attempt":
            digest = attempt(args[1])
        else:
            _usage()
    except ValueError:
        _usage()
    del digest
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
