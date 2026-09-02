"""Strict, privacy-safe records for the transition-safe V4 rehearsal.

This module is pure.  Importing it performs no I/O, entropy, process, network, or
scientific action.  The future authority is the only filesystem writer.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence


REGISTRATION_SCHEMA = (
    "heterodiff-manuscript-v3-a1-r1-activation-preparation-v4-"
    "transition-safe-live-host-environment-rehearsal-freeze-v1"
)
QUALIFICATION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-transition-safe-live-host-"
    "environment-rehearsal-qualification-v1"
)
STATUS_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-transition-safe-live-host-"
    "environment-rehearsal-status-v1"
)
AUTHORIZATION_SCHEMA = (
    "heterodiff-manuscript-v3-a1-r1-activation-preparation-v4-"
    "execution-authorization-v1"
)
MARKER_SCHEMA = "heterodiff-a1-r1-activation-preparation-v4-attempt-marker-v1"
GENESIS_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-ledger-genesis-v1"
)
EVALUATION_CLAIM_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-prechild-evaluation-claim-v1"
)
PRECHILD_FAILURE_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-prechild-failure-v1"
)
PRECHILD_ADMISSION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-prechild-admission-v1"
)
POST_ADMISSION_FAILURE_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-"
    "post-admission-prechild-failure-v1"
)
CHILD_CLAIM_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-child-launch-claim-v1"
)
RUNTIME_REQUEST_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-runtime-request-v1"
)
CHILD_OBSERVATION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-child-observation-v1"
)
TERMINAL_OUTCOME_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-terminal-outcome-v1"
)
TERMINAL_PROJECTION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-terminal-projection-v1"
)
PUBLISHED_RESULT_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-published-result-v1"
)

STATIC_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_TRANSITION_SAFE_IMPLEMENTATION_FROZEN_"
    "AWAITING_FRESH_EXACT_AUTHORIZATION_NO_ATTEMPT_SPEND_NOT_EXECUTABLE"
)
AUTH_RECORDED_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_EXECUTION_AUTHORIZATION_RECORDED_"
    "AWAITING_ATTEMPT_SPEND_NO_SCIENTIFIC_EXECUTION_AUTHORITY"
)
MARKER_FALLBACK_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_ATTEMPT_SPENT_RESERVATION_PUBLISHED_"
    "PRE_EVALUATION_TERMINAL_FALLBACK_NO_RETRY"
)
EVALUATION_FALLBACK_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_ATTEMPT_SPENT_PRECHILD_EVALUATION_"
    "CLAIMED_TERMINAL_FALLBACK_NO_RETRY"
)
PRECHILD_FAILURE_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_TERMINAL_PRECHILD_FAILURE_NO_CHILD_"
    "NO_RETRY_NOT_EXECUTABLE"
)
ADMISSION_FALLBACK_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_TERMINAL_PRECHILD_ADMISSION_WITHOUT_"
    "CHILD_CLAIM_NO_RETRY_NOT_EXECUTABLE"
)
POST_ADMISSION_FAILURE_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_TERMINAL_POST_ADMISSION_PRECHILD_"
    "FAILURE_NO_CHILD_NO_RETRY_NOT_EXECUTABLE"
)
CHILD_FALLBACK_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_CHILD_LAUNCH_CLAIMED_TERMINAL_"
    "FALLBACK_NO_RETRY"
)
PASS_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_TERMINAL_REHEARSAL_PASS_NO_RETRY_"
    "NO_RUNTIME_APPROVAL_NO_SCIENTIFIC_EXECUTION_AUTHORITY"
)
FAIL_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_TERMINAL_REHEARSAL_FAIL_NO_RETRY_"
    "NO_RUNTIME_APPROVAL_NOT_EXECUTABLE"
)
INVALID_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_CUSTODY_INVALID_TERMINAL_NO_RETRY_"
    "NOT_EXECUTABLE"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"

MARKER_PATH = "artifacts/a1_r1_activation_preparation_v4.attempt.json"
ROOT_PATH = "artifacts/a1_r1_activation_preparation_v4"
LOCK_PATH = ROOT_PATH + "/ledger/writer.lock"
GENESIS_PATH = ROOT_PATH + "/ledger/genesis.json"
EVENTS_PATH = ROOT_PATH + "/ledger/events"
TERMINAL_PATH = ROOT_PATH + "/ledger/terminal.json"
AUTHORIZATION_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "execution_authorization_v1.json"
)
RESULT_PATH = (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_result_v1.json"
)

VISIBLE_ASSENT_TEXT = (
    "I authorize the single frozen V4 rehearsal attempt described above, "
    "with no retry or scientific execution."
)
VISIBLE_ASSENT_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-v4-visible-user-authorization-v1\0"
)
VISIBLE_ASSENT_SHA256 = (
    "33c38693197abe2849d02736250138322c452c4294552258757cfd5ae3a77994"
)
AUTHORIZATION_CONTEXT_TEXT = (
    "A1 R1 activation-preparation V4 authorization context: authorize no-clobber "
    "publication and audit of one canonical execution-authorization record binding "
    "this assent, then exactly one transition-safe live-host environment rehearsal "
    "attempt under the exact audited V4 static freeze; publish and fsync the "
    "disjoint no-clobber attempt marker by O_EXCL, then create and fsync the "
    "sole-writer ledger, all before any full custody audit, environment, identity, "
    "profile, entropy, subprocess, or child evaluation; use the frozen "
    "deterministic no-entropy attempt nonce; perform one privacy-safe prechild "
    "supervisor evaluation; persist exactly one typed prechild failure or admission; "
    "after admission only, claim and launch at most one environment-only child; "
    "persist a no-clobber local typed terminal outcome independently of stdout or "
    "tool transport; attempt one no-clobber publication of the terminal result; "
    "treat any partial transition, replay, or publication failure as spent with no "
    "live retry; authorize no runtime approval, rank, training, production, "
    "scientific execution, manuscript claim, network access, or additional probe."
)
AUTHORIZATION_CONTEXT_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-v4-authorization-context-v1\0"
)
AUTHORIZATION_CONTEXT_SHA256 = (
    "3e989c3935c829a5920992b29de6001369c29c9fb25f686eb44ee48be6026417"
)
SUPERSEDED_AUTHORIZATION_CONTEXT_SHA256 = (
    "b9dcb7c6f48a743a0b9977ff55fd8646dd077f1e39b7b1a0eb383bcfbb551f4e",
    "a96eccdbe23b5314cd8eb09f666389d84c6171b43124c9410b15ddef30f663c2",
    "4f8e2bffb835e0cb9966c74b4b527d014ef9a7f0e47b6b9a10a545bc18cfa7b1",
    "228867a3116d4a3e37c9b292907391ffd300a245a614eb8acdd0102cce600470",
)
ATTEMPT_ID_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-v4-attempt-identity-v1\0"
)
ATTEMPT_NONCE_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-v4-deterministic-attempt-nonce-v1\0"
)
REQUESTED_ENVIRONMENT_POLICY_SHA256 = (
    "b00a27ff04e61be7fb3456c512dcd39c102bb75212dbb251749508e729360c4b"
)
EXPECTED_PROFILE_SHA256 = (
    "ea478565849b51fe2eb0ce61bb5c5d8217cf2731abb6c051863e593a412dca77"
)
EXPECTED_HASH_PROBE_SHA256 = (
    "f7b1ba1308d7559c69fc44640d0fcd07dbeae53b9024da5d862463db71e230af"
)

AUTHORIZED_OUTPUT_PATHS = [
    AUTHORIZATION_PATH,
    MARKER_PATH,
    ROOT_PATH,
    TERMINAL_PATH,
    RESULT_PATH,
]
AUTHORIZED_SCOPE = [
    "ONE_V4_TRANSITION_SAFE_LIVE_HOST_ENVIRONMENT_REHEARSAL_ATTEMPT",
    "ONE_PRIVACY_SAFE_PRECHILD_SUPERVISOR_EVALUATION",
    "AT_MOST_ONE_ENVIRONMENT_ONLY_CHILD_AFTER_TYPED_ADMISSION",
    "LOCAL_NO_CLOBBER_TERMINAL_CUSTODY",
    "ONE_NO_CLOBBER_EXTERNAL_RESULT_PUBLICATION_ATTEMPT",
]

PRECHILD_GATE_ORDER = (
    "registration_exact",
    "authorization_certificate_exact",
    "canonical_workspace_anchor_exact",
    "v3_terminal_registration_exact",
    "v3_terminal_custody_exact",
    "v3_attempt_count_one_retry_count_zero",
    "v3_spent_namespace_absent",
    "v2_terminal_custody_exact",
    "v4_source_closure_exact",
    "v4_closed_world_prefix_exact",
    "canonical_cwd_exact",
    "requested_environment_exact",
    "darwin_environment_normalized",
    "identity_nonprivileged_exact",
    "cpython_3_11_5_exact",
    "darwin_arm64_exact",
    "python_flags_exact",
    "hash_probe_matches_prefrozen_reference",
    "system_only_sys_path_exact",
    "site_module_absent",
    "native_argv_structural_tail_exact",
    "application_effects_absent",
)

PRECHILD_FAILURE_CODES = (
    "NONE",
    "REGISTRATION",
    "AUTHORIZATION_CERTIFICATE",
    "WORKSPACE_ANCHOR",
    "V3_TERMINAL_REGISTRATION",
    "V3_TERMINAL_CUSTODY",
    "V3_ATTEMPT_HISTORY",
    "V3_SPENT_NAMESPACE",
    "V2_TERMINAL_CUSTODY",
    "V4_SOURCE_CLOSURE",
    "V4_PREFIX_CUSTODY",
    "CWD",
    "REQUESTED_ENVIRONMENT",
    "DARWIN_ENVIRONMENT",
    "IDENTITY",
    "PYTHON_VERSION",
    "PLATFORM",
    "PYTHON_FLAGS",
    "HASH_PROBE",
    "SYS_PATH",
    "SITE_MODULE",
    "NATIVE_ARGV",
    "APPLICATION_EFFECT",
)

CHILD_GATE_ORDER = (
    "parent_linked_static_closure_exact",
    "direct_file_main",
    "python_argv_exact",
    "native_argv_structural_tail_exact",
    "cwd_exact",
    "requested_environment_exact",
    "darwin_environment_normalized",
    "identity_nonprivileged_exact",
    "interpreter_exact",
    "cpython_3_11_5_exact",
    "darwin_arm64_exact",
    "python_flags_exact",
    "hash_probe_matches_prefrozen_reference",
    "system_only_sys_path_exact",
    "site_module_absent",
    "application_effects_absent",
)
CHILD_FAILURE_CODES = (
    "NONE",
    "REQUEST",
    "DIRECT_FILE_MAIN",
    "PYTHON_ARGV",
    "NATIVE_ARGV",
    "CWD",
    "REQUESTED_ENVIRONMENT",
    "DARWIN_ENVIRONMENT",
    "IDENTITY",
    "INTERPRETER",
    "PYTHON_VERSION",
    "PLATFORM",
    "PYTHON_FLAGS",
    "HASH_PROBE",
    "SYS_PATH",
    "SITE_MODULE",
    "APPLICATION_EFFECT",
)
TRANSPORT_FAILURE_CODES = (
    "NONE",
    "CHILD_SPAWN",
    "CHILD_STDIN",
    "CHILD_TIMEOUT",
    "CHILD_STDOUT",
    "CHILD_STDERR",
    "CHILD_REAP",
    "CHILD_EXIT",
    "CHILD_CONTRACT",
    "POSTFLIGHT_CUSTODY",
)
TRANSPORT_GATE_ORDER = (
    "child_spawn_succeeded",
    "child_stdin_request_fully_written",
    "child_timeout_absent",
    "child_stdout_eof_and_within_bound",
    "child_stderr_eof_and_empty",
    "child_process_reap_observed",
    "child_exit_zero",
    "child_contract_exact",
    "postflight_custody_exact",
)


class ContractError(ValueError):
    """A record is outside the exact V4 closed contract."""


def canonical_json_bytes(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ContractError("record is not canonical-JSON encodable") from exc
    return encoded


def canonical_file_bytes(value: Any) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _digest_body(record: Mapping[str, Any], digest_key: str) -> str:
    if digest_key not in record:
        raise ContractError("missing record digest")
    body = dict(record)
    body.pop(digest_key)
    return sha256_bytes(canonical_json_bytes(body))


def attach_digest(body: Mapping[str, Any], digest_key: str) -> dict[str, Any]:
    if digest_key in body:
        raise ContractError("digest key already present")
    result = dict(body)
    result[digest_key] = sha256_bytes(canonical_json_bytes(result))
    return result


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        raise ContractError(f"{label} must be a mapping")
    if not all(type(key) is str for key in value):
        raise ContractError(f"{label} keys must be strings")
    return value


def _require_exact_keys(
    value: Mapping[str, Any], fields: Sequence[str], label: str
) -> None:
    if set(value) != set(fields) or len(value) != len(fields):
        raise ContractError(f"{label} field roster mismatch")


def _require_bool(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise ContractError(f"{label} must be Boolean")
    return value


def _require_int(value: Any, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ContractError(f"{label} must be an integer >= {minimum}")
    return value


def _require_text(value: Any, label: str, maximum: int = 4096) -> str:
    if type(value) is not str or not value or len(value) > maximum:
        raise ContractError(f"{label} must be bounded nonempty text")
    if any(ord(char) < 0x20 or ord(char) > 0x7E for char in value):
        raise ContractError(f"{label} must be printable ASCII")
    return value


def _require_sha(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ContractError(f"{label} must be lowercase SHA-256")
    return value


def _require_enum(value: Any, choices: Sequence[str], label: str) -> str:
    if value not in choices or type(value) is not str:
        raise ContractError(f"{label} is outside the frozen enum")
    return value


def _require_fixed(
    record: Mapping[str, Any], key: str, expected: Any, label: str
) -> None:
    if type(record[key]) is not type(expected) or record[key] != expected:
        raise ContractError(f"{label}.{key} fixed value mismatch")


def _validate_self(
    record: Mapping[str, Any], digest_key: str, fields: Sequence[str], label: str
) -> dict[str, Any]:
    _require_exact_keys(record, fields, label)
    _require_sha(record[digest_key], f"{label}.{digest_key}")
    if record[digest_key] != _digest_body(record, digest_key):
        raise ContractError(f"{label} self digest mismatch")
    return dict(record)


def derive_attempt_identity(
    registration_record_sha256: str,
    authorization_record_sha256: str,
    authorization_raw_sha256: str,
) -> tuple[str, str]:
    for value, label in (
        (registration_record_sha256, "registration_record_sha256"),
        (authorization_record_sha256, "authorization_record_sha256"),
        (authorization_raw_sha256, "authorization_raw_sha256"),
    ):
        _require_sha(value, label)
    identity_preimage = canonical_json_bytes(
        {
            "attempt_ordinal": 0,
            "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
            "execution_authorization_raw_sha256": authorization_raw_sha256,
            "execution_authorization_record_sha256": authorization_record_sha256,
            "registration_record_sha256": registration_record_sha256,
            "visible_assent_sha256": VISIBLE_ASSENT_SHA256,
        }
    )
    attempt_id = sha256_bytes(ATTEMPT_ID_DOMAIN + identity_preimage)
    nonce_preimage = canonical_json_bytes(
        {
            "attempt_id_sha256": attempt_id,
            "attempt_ordinal": 0,
            "marker_path": MARKER_PATH,
        }
    )
    return attempt_id, sha256_bytes(ATTEMPT_NONCE_DOMAIN + nonce_preimage)


AUTHORIZATION_FIELDS = (
    "schema_version",
    "v4_registration_record_sha256",
    "v4_registration_raw_sha256",
    "authorization_context_text",
    "authorization_context_sha256",
    "normalized_visible_assent_text",
    "normalized_visible_assent_sha256",
    "assent_source",
    "assent_normalization",
    "raw_transport_bytes_bound",
    "authorization_record_path",
    "honest_host_procedural_authority",
    "cryptographic_user_authentication",
    "record_self_digests_are_user_authentication",
    "malicious_host_resistance_claimed",
    "authorized_action",
    "authorized_attempt_count",
    "authorized_child_launch_maximum",
    "authorized_output_paths",
    "retry_count_authorized",
    "deterministic_nonce",
    "entropy_authorized",
    "network_authorized",
    "runtime_approval_authorized",
    "rank_authorized",
    "training_authorized",
    "production_authorized",
    "scientific_execution_authorized",
    "manuscript_claim_authorized",
    "record_sha256",
)


def validate_authorization_record(
    value: Any,
    expected_registration_sha256: str,
    expected_registration_raw_sha256: str,
) -> dict[str, Any]:
    record = _require_mapping(value, "authorization record")
    checked = _validate_self(
        record, "record_sha256", AUTHORIZATION_FIELDS, "authorization record"
    )
    if checked["schema_version"] != AUTHORIZATION_SCHEMA:
        raise ContractError("authorization schema mismatch")
    _require_sha(expected_registration_sha256, "expected registration digest")
    _require_sha(
        expected_registration_raw_sha256, "expected registration raw digest"
    )
    fixed = {
        "v4_registration_record_sha256": expected_registration_sha256,
        "v4_registration_raw_sha256": expected_registration_raw_sha256,
        "authorization_context_text": AUTHORIZATION_CONTEXT_TEXT,
        "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
        "normalized_visible_assent_text": VISIBLE_ASSENT_TEXT,
        "normalized_visible_assent_sha256": VISIBLE_ASSENT_SHA256,
        "assent_source": "CONVERSATION_VISIBLE_TEXT",
        "assent_normalization": "TRAILING_TRANSPORT_WHITESPACE_OR_ENTITY_NORMALIZED",
        "raw_transport_bytes_bound": False,
        "authorization_record_path": AUTHORIZATION_PATH,
        "honest_host_procedural_authority": True,
        "cryptographic_user_authentication": False,
        "record_self_digests_are_user_authentication": False,
        "malicious_host_resistance_claimed": False,
        "authorized_action": "V4_EXECUTE_ONCE",
        "authorized_attempt_count": 1,
        "authorized_child_launch_maximum": 1,
        "authorized_output_paths": AUTHORIZED_OUTPUT_PATHS,
        "retry_count_authorized": 0,
        "deterministic_nonce": True,
        "entropy_authorized": False,
        "network_authorized": False,
        "runtime_approval_authorized": False,
        "rank_authorized": False,
        "training_authorized": False,
        "production_authorized": False,
        "scientific_execution_authorized": False,
        "manuscript_claim_authorized": False,
    }
    for key, expected in fixed.items():
        _require_fixed(checked, key, expected, "authorization record")
    return checked


MARKER_FIELDS = (
    "schema_version",
    "attempt_ordinal",
    "attempt_id_sha256",
    "attempt_nonce_sha256",
    "nonce_kind",
    "entropy_draw_count",
    "registration_record_sha256",
    "registration_raw_sha256",
    "execution_authorization_record_sha256",
    "execution_authorization_raw_sha256",
    "authorization_context_sha256",
    "visible_assent_sha256",
    "marker_path",
    "fallback_terminal_state",
    "retry_permitted",
    "marker_sha256",
)


def validate_marker(
    value: Any,
    authorization_record: Mapping[str, Any],
    expected_registration_record_sha256: str,
    expected_registration_raw_sha256: str,
) -> dict[str, Any]:
    record = _validate_self(
        _require_mapping(value, "marker"),
        "marker_sha256",
        MARKER_FIELDS,
        "marker",
    )
    if record["schema_version"] != MARKER_SCHEMA:
        raise ContractError("marker schema mismatch")
    for key in (
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "registration_record_sha256",
        "registration_raw_sha256",
        "execution_authorization_record_sha256",
        "execution_authorization_raw_sha256",
        "authorization_context_sha256",
        "visible_assent_sha256",
    ):
        _require_sha(record[key], f"marker.{key}")
    expected_id, expected_nonce = derive_attempt_identity(
        record["registration_record_sha256"],
        record["execution_authorization_record_sha256"],
        record["execution_authorization_raw_sha256"],
    )
    fixed = {
        "attempt_ordinal": 0,
        "attempt_id_sha256": expected_id,
        "attempt_nonce_sha256": expected_nonce,
        "nonce_kind": "DETERMINISTIC_NONSECRET_CUSTODY_IDENTIFIER",
        "entropy_draw_count": 0,
        "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
        "visible_assent_sha256": VISIBLE_ASSENT_SHA256,
        "marker_path": MARKER_PATH,
        "fallback_terminal_state": MARKER_FALLBACK_STATE,
        "retry_permitted": False,
    }
    for key, expected in fixed.items():
        _require_fixed(record, key, expected, "marker")
    _require_sha(
        expected_registration_record_sha256,
        "independent expected registration record digest",
    )
    _require_fixed(
        record,
        "registration_record_sha256",
        expected_registration_record_sha256,
        "marker",
    )
    _require_fixed(
        record,
        "registration_raw_sha256",
        expected_registration_raw_sha256,
        "marker",
    )
    authorization = validate_authorization_record(
        authorization_record,
        expected_registration_record_sha256,
        expected_registration_raw_sha256,
    )
    if (
        record["execution_authorization_record_sha256"]
        != authorization["record_sha256"]
    ):
        raise ContractError("marker authorization self link mismatch")
    if record["execution_authorization_raw_sha256"] != sha256_bytes(
        canonical_file_bytes(authorization)
    ):
        raise ContractError("marker authorization raw link mismatch")
    return record


GENESIS_FIELDS = (
    "schema_version",
    "attempt_id_sha256",
    "attempt_nonce_sha256",
    "registration_record_sha256",
    "registration_raw_sha256",
    "execution_authorization_record_sha256",
    "execution_authorization_raw_sha256",
    "authorization_context_sha256",
    "visible_assent_sha256",
    "marker_raw_sha256",
    "marker_sha256",
    "event_count_before_genesis",
    "global_state",
    "retry_permitted",
    "genesis_sha256",
)


def validate_genesis(
    value: Any,
    marker: Mapping[str, Any],
    authorization_record: Mapping[str, Any],
    expected_registration_record_sha256: str,
    expected_registration_raw_sha256: str,
    marker_raw: bytes,
) -> dict[str, Any]:
    marker_checked = validate_marker(
        marker,
        authorization_record,
        expected_registration_record_sha256,
        expected_registration_raw_sha256,
    )
    record = _validate_self(
        _require_mapping(value, "genesis"),
        "genesis_sha256",
        GENESIS_FIELDS,
        "genesis",
    )
    if record["schema_version"] != GENESIS_SCHEMA:
        raise ContractError("genesis schema mismatch")
    for key in (
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "registration_record_sha256",
        "registration_raw_sha256",
        "execution_authorization_record_sha256",
        "execution_authorization_raw_sha256",
        "authorization_context_sha256",
        "visible_assent_sha256",
        "marker_raw_sha256",
        "marker_sha256",
    ):
        _require_sha(record[key], f"genesis.{key}")
    for key in (
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "registration_record_sha256",
        "registration_raw_sha256",
        "execution_authorization_record_sha256",
        "execution_authorization_raw_sha256",
        "authorization_context_sha256",
        "visible_assent_sha256",
        "marker_sha256",
    ):
        if record[key] != marker_checked[key]:
            raise ContractError(f"genesis marker link {key} mismatch")
    if type(marker_raw) is not bytes or marker_raw != canonical_file_bytes(marker_checked):
        raise ContractError("genesis marker raw bytes mismatch")
    if record["marker_raw_sha256"] != sha256_bytes(marker_raw):
        raise ContractError("genesis marker raw link mismatch")
    for key, expected in {
        "event_count_before_genesis": 0,
        "global_state": GLOBAL_STATE,
        "retry_permitted": False,
    }.items():
        _require_fixed(record, key, expected, "genesis")
    return record


RUNTIME_REQUEST_FIELDS = (
    "schema_version",
    "attempt_id_sha256",
    "attempt_nonce_sha256",
    "registration_record_sha256",
    "registration_raw_sha256",
    "execution_authorization_record_sha256",
    "execution_authorization_raw_sha256",
    "admission_event_sha256",
    "child_launch_ordinal",
    "requested_environment_policy_sha256",
    "expected_profile_sha256",
    "expected_hash_probe_sha256",
    "raw_environment_requested",
    "network_requested",
    "workspace_write_requested",
    "temporary_write_requested",
    "scientific_import_or_execution_requested",
    "request_sha256",
)


def validate_runtime_request(value: Any) -> dict[str, Any]:
    record = _validate_self(
        _require_mapping(value, "runtime request"),
        "request_sha256",
        RUNTIME_REQUEST_FIELDS,
        "runtime request",
    )
    if record["schema_version"] != RUNTIME_REQUEST_SCHEMA:
        raise ContractError("runtime request schema mismatch")
    for key in (
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "registration_record_sha256",
        "registration_raw_sha256",
        "execution_authorization_record_sha256",
        "execution_authorization_raw_sha256",
        "admission_event_sha256",
        "requested_environment_policy_sha256",
        "expected_profile_sha256",
        "expected_hash_probe_sha256",
    ):
        _require_sha(record[key], f"request.{key}")
    _require_fixed(record, "child_launch_ordinal", 0, "runtime request")
    for key, expected in {
        "requested_environment_policy_sha256": REQUESTED_ENVIRONMENT_POLICY_SHA256,
        "expected_profile_sha256": EXPECTED_PROFILE_SHA256,
        "expected_hash_probe_sha256": EXPECTED_HASH_PROBE_SHA256,
    }.items():
        _require_fixed(record, key, expected, "runtime request")
    for key in (
        "raw_environment_requested",
        "network_requested",
        "workspace_write_requested",
        "temporary_write_requested",
        "scientific_import_or_execution_requested",
    ):
        if _require_bool(record[key], f"request.{key}"):
            raise ContractError(f"request effect {key} is forbidden")
    return record


def _validate_gate_map(
    value: Any, order: Sequence[str], label: str
) -> dict[str, bool]:
    gates = _require_mapping(value, label)
    _require_exact_keys(gates, order, label)
    return {name: _require_bool(gates[name], f"{label}.{name}") for name in order}


def prechild_failure_code(gates: Mapping[str, Any]) -> str:
    checked = _validate_gate_map(gates, PRECHILD_GATE_ORDER, "prechild gates")
    code_by_gate = dict(zip(PRECHILD_GATE_ORDER, PRECHILD_FAILURE_CODES[1:]))
    for name in PRECHILD_GATE_ORDER:
        if not checked[name]:
            return code_by_gate[name]
    return "NONE"


def child_failure_code(gates: Mapping[str, Any]) -> str:
    checked = _validate_gate_map(gates, CHILD_GATE_ORDER, "child gates")
    code_by_gate = dict(zip(CHILD_GATE_ORDER, CHILD_FAILURE_CODES[1:]))
    for name in CHILD_GATE_ORDER:
        if not checked[name]:
            return code_by_gate[name]
    return "NONE"


EVENT_COMMON_FIELDS = (
    "schema_version",
    "event_ordinal",
    "event_kind",
    "attempt_id_sha256",
    "attempt_nonce_sha256",
    "registration_record_sha256",
    "registration_raw_sha256",
    "marker_raw_sha256",
    "marker_sha256",
    "previous_record_kind",
    "previous_record_raw_sha256",
    "previous_record_sha256",
    "fallback_terminal_state",
    "retry_permitted",
)
EVALUATION_EVENT_FIELDS = EVENT_COMMON_FIELDS + ("event_sha256",)
PRECHILD_EVENT_FIELDS = EVENT_COMMON_FIELDS + (
    "gate_vector",
    "gate_vector_sha256",
    "failure_code",
    "child_launch_count",
    "runtime_approval_created",
    "scientific_execution_performed",
    "event_sha256",
)
POST_ADMISSION_EVENT_FIELDS = EVENT_COMMON_FIELDS + (
    "failure_code",
    "child_launch_count",
    "runtime_approval_created",
    "scientific_execution_performed",
    "event_sha256",
)
CHILD_EVENT_FIELDS = EVENT_COMMON_FIELDS + (
    "admission_event_raw_sha256",
    "admission_event_sha256",
    "runtime_request",
    "runtime_request_raw_sha256",
    "runtime_request_sha256",
    "child_launch_ordinal",
    "child_launch_maximum",
    "event_sha256",
)


def validate_event(value: Any) -> dict[str, Any]:
    mapping = _require_mapping(value, "event")
    schema = mapping.get("schema_version")
    if schema == EVALUATION_CLAIM_SCHEMA:
        fields = EVALUATION_EVENT_FIELDS
        expected = {
            "event_ordinal": 0,
            "event_kind": "PRECHILD_EVALUATION_CLAIM",
            "previous_record_kind": "GENESIS",
            "fallback_terminal_state": EVALUATION_FALLBACK_STATE,
            "retry_permitted": False,
        }
    elif schema in (PRECHILD_FAILURE_SCHEMA, PRECHILD_ADMISSION_SCHEMA):
        fields = PRECHILD_EVENT_FIELDS
        gates = _validate_gate_map(
            mapping.get("gate_vector"), PRECHILD_GATE_ORDER, "event gate vector"
        )
        failure = prechild_failure_code(gates)
        if mapping.get("gate_vector_sha256") != sha256_bytes(
            canonical_json_bytes(gates)
        ):
            raise ContractError("prechild gate vector digest mismatch")
        if schema == PRECHILD_FAILURE_SCHEMA:
            if failure == "NONE":
                raise ContractError("failure event has passing gates")
            expected = {
                "event_ordinal": 1,
                "event_kind": "PRECHILD_FAILURE",
                "fallback_terminal_state": PRECHILD_FAILURE_STATE,
                "failure_code": failure,
                "child_launch_count": 0,
                "runtime_approval_created": False,
                "scientific_execution_performed": False,
                "retry_permitted": False,
            }
        else:
            if failure != "NONE":
                raise ContractError("admission event has failing gates")
            expected = {
                "event_ordinal": 1,
                "event_kind": "PRECHILD_ADMISSION",
                "fallback_terminal_state": ADMISSION_FALLBACK_STATE,
                "failure_code": "NONE",
                "child_launch_count": 0,
                "runtime_approval_created": False,
                "scientific_execution_performed": False,
                "retry_permitted": False,
            }
    elif schema == POST_ADMISSION_FAILURE_SCHEMA:
        fields = POST_ADMISSION_EVENT_FIELDS
        _require_enum(
            mapping.get("failure_code"),
            ("POST_ADMISSION_CUSTODY", "REQUEST_CONSTRUCTION", "CHILD_CLAIM_PUBLICATION"),
            "post-admission failure code",
        )
        expected = {
            "event_ordinal": 2,
            "event_kind": "POST_ADMISSION_PRECHILD_FAILURE",
            "fallback_terminal_state": POST_ADMISSION_FAILURE_STATE,
            "child_launch_count": 0,
            "runtime_approval_created": False,
            "scientific_execution_performed": False,
            "retry_permitted": False,
        }
    elif schema == CHILD_CLAIM_SCHEMA:
        fields = CHILD_EVENT_FIELDS
        expected = {
            "event_ordinal": 2,
            "event_kind": "CHILD_LAUNCH_CLAIM",
            "fallback_terminal_state": CHILD_FALLBACK_STATE,
            "child_launch_ordinal": 0,
            "child_launch_maximum": 1,
            "retry_permitted": False,
        }
        request = validate_runtime_request(mapping.get("runtime_request"))
        if mapping.get("runtime_request_sha256") != request["request_sha256"]:
            raise ContractError("child event request self link mismatch")
        if mapping.get("runtime_request_raw_sha256") != sha256_bytes(
            canonical_file_bytes(request)
        ):
            raise ContractError("child event request raw link mismatch")
        _require_sha(
            mapping.get("admission_event_raw_sha256"),
            "child event admission raw digest",
        )
        _require_sha(
            mapping.get("admission_event_sha256"),
            "child event admission self digest",
        )
        for request_key, event_key in (
            ("attempt_id_sha256", "attempt_id_sha256"),
            ("attempt_nonce_sha256", "attempt_nonce_sha256"),
            ("registration_record_sha256", "registration_record_sha256"),
            ("registration_raw_sha256", "registration_raw_sha256"),
            ("admission_event_sha256", "admission_event_sha256"),
            ("child_launch_ordinal", "child_launch_ordinal"),
        ):
            if type(request[request_key]) is not type(mapping[event_key]) or request[
                request_key
            ] != mapping[event_key]:
                raise ContractError(f"child event request link {request_key} mismatch")
    elif schema == TERMINAL_OUTCOME_SCHEMA:
        return validate_terminal_outcome(mapping)
    else:
        raise ContractError("unknown event schema")
    record = _validate_self(mapping, "event_sha256", fields, "event")
    for key, expected_value in expected.items():
        _require_fixed(record, key, expected_value, "event")
    for key in (
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "registration_record_sha256",
        "registration_raw_sha256",
        "marker_raw_sha256",
        "marker_sha256",
        "previous_record_raw_sha256",
        "previous_record_sha256",
    ):
        _require_sha(record[key], f"event.{key}")
    _require_enum(record["previous_record_kind"], ("GENESIS", "EVENT"), "previous record kind")
    if record["event_ordinal"] == 0 and record["previous_record_kind"] != "GENESIS":
        raise ContractError("event zero must bind genesis")
    if record["event_ordinal"] > 0 and record["previous_record_kind"] != "EVENT":
        raise ContractError("later event must bind prior event")
    return record


def validate_event_chain(
    value: Any,
    marker: Mapping[str, Any],
    authorization_record: Mapping[str, Any],
    expected_registration_record_sha256: str,
    expected_registration_raw_sha256: str,
    marker_raw: bytes,
    genesis: Mapping[str, Any],
    genesis_raw: bytes,
    prior_event: Mapping[str, Any] | None,
    prior_event_raw: bytes | None,
) -> dict[str, Any]:
    marker_checked = validate_marker(
        marker,
        authorization_record,
        expected_registration_record_sha256,
        expected_registration_raw_sha256,
    )
    genesis_checked = validate_genesis(
        genesis,
        marker_checked,
        authorization_record,
        expected_registration_record_sha256,
        expected_registration_raw_sha256,
        marker_raw,
    )
    if type(genesis_raw) is not bytes or genesis_raw != canonical_file_bytes(
        genesis_checked
    ):
        raise ContractError("event genesis raw bytes mismatch")
    event = validate_event(value)
    for key in (
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "registration_record_sha256",
        "registration_raw_sha256",
        "marker_sha256",
    ):
        if event[key] != marker_checked[key]:
            raise ContractError(f"event marker link {key} mismatch")
    if event["marker_raw_sha256"] != sha256_bytes(marker_raw):
        raise ContractError("event marker raw link mismatch")
    ordinal = event["event_ordinal"]
    if ordinal == 0:
        if prior_event is not None or prior_event_raw is not None:
            raise ContractError("event zero cannot have prior event")
        if event["previous_record_raw_sha256"] != sha256_bytes(genesis_raw):
            raise ContractError("event zero genesis raw link mismatch")
        if event["previous_record_sha256"] != genesis_checked["genesis_sha256"]:
            raise ContractError("event zero genesis self link mismatch")
        return event
    if prior_event is None or type(prior_event_raw) is not bytes:
        raise ContractError("later event requires prior event bytes")
    prior = validate_event(prior_event)
    if prior_event_raw != canonical_file_bytes(prior):
        raise ContractError("prior event raw bytes mismatch")
    if ordinal != prior["event_ordinal"] + 1:
        raise ContractError("event ordinal is not contiguous")
    for key in (
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "registration_record_sha256",
        "registration_raw_sha256",
        "marker_raw_sha256",
        "marker_sha256",
    ):
        if prior[key] != event[key] or prior[key] != (
            marker_checked[key]
            if key in marker_checked
            else sha256_bytes(marker_raw)
        ):
            raise ContractError(f"cross-attempt prior event link mismatch: {key}")
    if event["previous_record_raw_sha256"] != sha256_bytes(prior_event_raw):
        raise ContractError("event prior raw link mismatch")
    if event["previous_record_sha256"] != prior["event_sha256"]:
        raise ContractError("event prior self link mismatch")
    if ordinal == 1:
        if prior["schema_version"] != EVALUATION_CLAIM_SCHEMA:
            raise ContractError("event one must follow evaluation claim")
    elif ordinal == 2:
        if prior["schema_version"] != PRECHILD_ADMISSION_SCHEMA:
            raise ContractError("event two must follow admission")
        if event["schema_version"] not in (
            POST_ADMISSION_FAILURE_SCHEMA,
            CHILD_CLAIM_SCHEMA,
        ):
            raise ContractError("event two branch schema mismatch")
        if event["schema_version"] == CHILD_CLAIM_SCHEMA:
            if event["admission_event_raw_sha256"] != sha256_bytes(prior_event_raw):
                raise ContractError("child claim admission raw link mismatch")
            if event["admission_event_sha256"] != prior["event_sha256"]:
                raise ContractError("child claim admission self link mismatch")
            request = event["runtime_request"]
            if request["execution_authorization_record_sha256"] != marker_checked[
                "execution_authorization_record_sha256"
            ]:
                raise ContractError("child request authorization self link mismatch")
            if request["execution_authorization_raw_sha256"] != marker_checked[
                "execution_authorization_raw_sha256"
            ]:
                raise ContractError("child request authorization raw link mismatch")
    elif ordinal == 3:
        if prior["schema_version"] != CHILD_CLAIM_SCHEMA:
            raise ContractError("terminal event must follow child claim")
        if event["schema_version"] != TERMINAL_OUTCOME_SCHEMA:
            raise ContractError("event three must be terminal outcome")
        request_raw = canonical_file_bytes(prior["runtime_request"])
        if event["child_stdin_captured_write_byte_count_observed"]:
            written = event["child_stdin_captured_write_byte_count"]
            if written > len(request_raw):
                raise ContractError("terminal stdin count exceeds request bytes")
            if event["child_stdin_request_fully_written"] != (
                written == len(request_raw)
            ):
                raise ContractError("terminal stdin completion/request mismatch")
        elif event["child_stdin_request_fully_written"]:
            raise ContractError("terminal stdin completion lacks count")
        observation = event["child_observation"]
        if observation is not None:
            request = prior["runtime_request"]
            if observation["request_raw_sha256"] != prior[
                "runtime_request_raw_sha256"
            ] or observation["request_sha256"] != request["request_sha256"]:
                raise ContractError("terminal child request link mismatch")
    else:
        raise ContractError("event ordinal outside frozen schedule")
    return event


CHILD_OBSERVATION_FIELDS = (
    "schema_version",
    "request_raw_sha256",
    "request_sha256",
    "child_launch_ordinal",
    "child_process_ordinal",
    "gate_vector",
    "gate_vector_sha256",
    "failure_code",
    "outcome",
    "prefrozen_hash_probe_sha256",
    "hash_probe_matches_prefrozen_reference",
    "effective_environment_key_count",
    "darwin_injected_key_present_before_normalization",
    "darwin_injected_value_formula_matches_uid",
    "darwin_injected_removed_from_process_environment",
    "application_effect_claim_basis",
    "raw_environment_emitted",
    "raw_identity_emitted",
    "raw_absolute_path_emitted",
    "raw_argv_emitted",
    "raw_stderr_emitted",
    "entropy_contacted",
    "network_contacted",
    "workspace_write_performed",
    "temporary_write_performed",
    "scientific_import_or_execution_performed",
    "observation_sha256",
)


def validate_child_observation(value: Any) -> dict[str, Any]:
    record = _validate_self(
        _require_mapping(value, "child observation"),
        "observation_sha256",
        CHILD_OBSERVATION_FIELDS,
        "child observation",
    )
    if record["schema_version"] != CHILD_OBSERVATION_SCHEMA:
        raise ContractError("child observation schema mismatch")
    for key in (
        "request_raw_sha256",
        "request_sha256",
        "gate_vector_sha256",
        "prefrozen_hash_probe_sha256",
    ):
        _require_sha(record[key], f"child observation.{key}")
    gates = _validate_gate_map(
        record["gate_vector"], CHILD_GATE_ORDER, "child observation gate vector"
    )
    if record["gate_vector_sha256"] != sha256_bytes(canonical_json_bytes(gates)):
        raise ContractError("child gate vector digest mismatch")
    failure = child_failure_code(gates)
    if record["failure_code"] != failure:
        raise ContractError("child failure priority mismatch")
    if record["outcome"] != ("PASS" if failure == "NONE" else "FAIL"):
        raise ContractError("child outcome mismatch")
    _require_fixed(record, "child_launch_ordinal", 0, "child observation")
    _require_fixed(record, "child_process_ordinal", 0, "child observation")
    _require_int(record["effective_environment_key_count"], "effective env key count")
    boolean_fields = (
        "hash_probe_matches_prefrozen_reference",
        "darwin_injected_key_present_before_normalization",
        "darwin_injected_value_formula_matches_uid",
        "darwin_injected_removed_from_process_environment",
        "raw_environment_emitted",
        "raw_identity_emitted",
        "raw_absolute_path_emitted",
        "raw_argv_emitted",
        "raw_stderr_emitted",
        "entropy_contacted",
        "network_contacted",
        "workspace_write_performed",
        "temporary_write_performed",
        "scientific_import_or_execution_performed",
    )
    for key in boolean_fields:
        _require_bool(record[key], f"child observation.{key}")
    _require_fixed(
        record,
        "application_effect_claim_basis",
        "STATIC_CHILD_SOURCE_AND_ROUTE_CONTRACT_NOT_OS_INSTRUMENTATION",
        "child observation",
    )
    if record["prefrozen_hash_probe_sha256"] != EXPECTED_HASH_PROBE_SHA256:
        raise ContractError("child hash probe carrier must remain prefrozen")
    if gates["hash_probe_matches_prefrozen_reference"] != record[
        "hash_probe_matches_prefrozen_reference"
    ]:
        raise ContractError("child hash probe Boolean contradiction")
    darwin_gate = all(
        record[key]
        for key in (
            "darwin_injected_key_present_before_normalization",
            "darwin_injected_value_formula_matches_uid",
            "darwin_injected_removed_from_process_environment",
        )
    )
    if gates["darwin_environment_normalized"] != darwin_gate:
        raise ContractError("child Darwin gate contradiction")
    forbidden_effect_fields = (
        "raw_environment_emitted",
        "raw_identity_emitted",
        "raw_absolute_path_emitted",
        "raw_argv_emitted",
        "raw_stderr_emitted",
        "entropy_contacted",
        "network_contacted",
        "workspace_write_performed",
        "temporary_write_performed",
        "scientific_import_or_execution_performed",
    )
    effects_absent = not any(record[key] for key in forbidden_effect_fields)
    if gates["application_effects_absent"] != effects_absent:
        raise ContractError("child application-effects gate contradiction")
    if gates["requested_environment_exact"] and gates[
        "darwin_environment_normalized"
    ]:
        _require_fixed(
            record,
            "effective_environment_key_count",
            17,
            "child observation",
        )
    if record["outcome"] == "PASS":
        if not all(gates.values()) or not effects_absent:
            raise ContractError("passing child contains a false gate or effect")
    return record


TERMINAL_OUTCOME_FIELDS = EVENT_COMMON_FIELDS + (
    "outcome",
    "terminal_state",
    "transport_gate_vector",
    "transport_gate_vector_sha256",
    "transport_failure_code",
    "child_launch_claim_count",
    "child_process_start_count",
    "child_spawn_succeeded",
    "child_stdin_captured_write_byte_count_observed",
    "child_stdin_captured_write_byte_count",
    "child_stdin_request_fully_written",
    "child_timeout_observed",
    "child_stdout_captured_byte_count_observed",
    "child_stdout_captured_byte_count",
    "child_stdout_eof_observed",
    "child_stdout_overflow_observed",
    "child_stderr_captured_byte_count_observed",
    "child_stderr_captured_byte_count",
    "child_stderr_eof_observed",
    "child_stderr_overflow_observed",
    "child_process_reap_observed",
    "child_exit_code_observed",
    "child_exit_code",
    "child_observation",
    "child_observation_raw_sha256",
    "child_observation_sha256",
    "postflight_custody_exact",
    "raw_child_transport_persisted",
    "runtime_approval_created",
    "scientific_execution_performed",
    "event_sha256",
)


def validate_terminal_outcome(value: Any) -> dict[str, Any]:
    record = _validate_self(
        _require_mapping(value, "terminal outcome"),
        "event_sha256",
        TERMINAL_OUTCOME_FIELDS,
        "terminal outcome",
    )
    if record["schema_version"] != TERMINAL_OUTCOME_SCHEMA:
        raise ContractError("terminal outcome schema mismatch")
    fixed = {
        "event_ordinal": 3,
        "event_kind": "TERMINAL_OUTCOME",
        "fallback_terminal_state": FAIL_STATE,
        "retry_permitted": False,
        "child_launch_claim_count": 1,
        "raw_child_transport_persisted": False,
        "runtime_approval_created": False,
        "scientific_execution_performed": False,
    }
    for key, expected in fixed.items():
        _require_fixed(record, key, expected, "terminal outcome")
    _require_fixed(
        record, "previous_record_kind", "EVENT", "terminal outcome"
    )
    _require_enum(
        record["transport_failure_code"], TRANSPORT_FAILURE_CODES, "transport code"
    )
    for key in (
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "registration_record_sha256",
        "registration_raw_sha256",
        "marker_raw_sha256",
        "marker_sha256",
        "previous_record_raw_sha256",
        "previous_record_sha256",
    ):
        _require_sha(record[key], f"terminal outcome.{key}")
    for key in (
        "child_spawn_succeeded",
        "child_stdin_captured_write_byte_count_observed",
        "child_stdin_request_fully_written",
        "child_timeout_observed",
        "child_stdout_captured_byte_count_observed",
        "child_stdout_eof_observed",
        "child_stdout_overflow_observed",
        "child_stderr_captured_byte_count_observed",
        "child_stderr_eof_observed",
        "child_stderr_overflow_observed",
        "child_process_reap_observed",
        "child_exit_code_observed",
        "postflight_custody_exact",
    ):
        _require_bool(record[key], f"terminal outcome.{key}")
    _require_int(record["child_process_start_count"], "child process start count")
    if record["child_process_start_count"] not in (0, 1):
        raise ContractError("child process start count outside 0..1")
    if record["child_process_start_count"] != int(record["child_spawn_succeeded"]):
        raise ContractError("child process start/spawn contradiction")
    count_specs = (
        (
            "child_stdin_captured_write_byte_count_observed",
            "child_stdin_captured_write_byte_count",
            1 << 20,
            "stdin captured write",
        ),
        (
            "child_stdout_captured_byte_count_observed",
            "child_stdout_captured_byte_count",
            65537,
            "stdout captured",
        ),
        (
            "child_stderr_captured_byte_count_observed",
            "child_stderr_captured_byte_count",
            4097,
            "stderr captured",
        ),
    )
    for observed_key, count_key, maximum, label in count_specs:
        if record[observed_key]:
            _require_int(record[count_key], f"child {label} count")
            if record[count_key] < 0 or record[count_key] > maximum:
                raise ContractError(f"child {label} count outside captured bound")
        elif record[count_key] is not None:
            raise ContractError(f"unobserved {label} count must be null")
    if record["child_stdin_request_fully_written"] and not record[
        "child_stdin_captured_write_byte_count_observed"
    ]:
        raise ContractError("fully written stdin lacks captured count")
    for stream, maximum in (("stdout", 65536), ("stderr", 4096)):
        observed = record[f"child_{stream}_captured_byte_count_observed"]
        count = record[f"child_{stream}_captured_byte_count"]
        eof = record[f"child_{stream}_eof_observed"]
        overflow = record[f"child_{stream}_overflow_observed"]
        if eof and (not observed or overflow):
            raise ContractError(f"child {stream} EOF/overflow contradiction")
        if overflow and (not observed or count != maximum + 1 or eof):
            raise ContractError(f"child {stream} overflow provenance mismatch")
        if observed and not overflow and count > maximum:
            raise ContractError(f"child {stream} captured count exceeds bound")
    if record["child_exit_code_observed"]:
        if type(record["child_exit_code"]) is not int:
            raise ContractError("observed child exit must be integer")
    elif record["child_exit_code"] is not None:
        raise ContractError("unobserved child exit must be null")
    observation = record["child_observation"]
    if observation is None:
        if record["child_observation_raw_sha256"] is not None or record["child_observation_sha256"] is not None:
            raise ContractError("absent observation has nonnull digest")
        child_pass = False
        child_contract_exact = False
    else:
        checked_observation = validate_child_observation(observation)
        _require_sha(record["child_observation_raw_sha256"], "observation raw digest")
        _require_sha(record["child_observation_sha256"], "observation self digest")
        if record["child_observation_sha256"] != checked_observation["observation_sha256"]:
            raise ContractError("terminal observation self link mismatch")
        if record["child_observation_raw_sha256"] != sha256_bytes(canonical_file_bytes(checked_observation)):
            raise ContractError("terminal observation raw link mismatch")
        child_pass = checked_observation["outcome"] == "PASS"
        child_contract_exact = True
    if record["child_process_reap_observed"] != record["child_exit_code_observed"]:
        raise ContractError("child reap/exit observation contradiction")
    if record["child_spawn_succeeded"] and not record[
        "child_process_reap_observed"
    ]:
        raise ContractError("spawned child without observed reap remains prefix-terminal")
    if not record["child_spawn_succeeded"]:
        impossible_without_spawn = (
            "child_stdin_captured_write_byte_count_observed",
            "child_stdin_request_fully_written",
            "child_timeout_observed",
            "child_stdout_captured_byte_count_observed",
            "child_stdout_eof_observed",
            "child_stdout_overflow_observed",
            "child_stderr_captured_byte_count_observed",
            "child_stderr_eof_observed",
            "child_stderr_overflow_observed",
            "child_process_reap_observed",
            "child_exit_code_observed",
        )
        if any(record[key] for key in impossible_without_spawn) or observation is not None:
            raise ContractError("unspawned child has impossible observations")
    if record["child_timeout_observed"] and observation is not None:
        raise ContractError("timed-out child has impossible terminal observation")
    if observation is not None:
        if (
            not record["child_spawn_succeeded"]
            or not record["child_stdin_request_fully_written"]
            or record["child_timeout_observed"]
            or not record["child_stdout_eof_observed"]
            or record["child_stdout_overflow_observed"]
            or not record["child_stderr_eof_observed"]
            or record["child_stderr_overflow_observed"]
            or not record["child_process_reap_observed"]
            or not record["child_exit_code_observed"]
            or record["child_exit_code"] != 0
        ):
            raise ContractError("nested observation transport provenance mismatch")
        if record["child_stdout_captured_byte_count"] != len(
            canonical_file_bytes(checked_observation)
        ):
            raise ContractError("child stdout count does not bind observation bytes")
    computed_transport_gates = {
        "child_spawn_succeeded": record["child_spawn_succeeded"],
        "child_stdin_request_fully_written": record[
            "child_stdin_request_fully_written"
        ],
        "child_timeout_absent": record["child_spawn_succeeded"]
        and not record["child_timeout_observed"],
        "child_stdout_eof_and_within_bound": record[
            "child_stdout_eof_observed"
        ]
        and not record["child_stdout_overflow_observed"]
        and record["child_stdout_captured_byte_count_observed"]
        and record["child_stdout_captured_byte_count"] <= 65536,
        "child_stderr_eof_and_empty": record["child_stderr_eof_observed"]
        and not record["child_stderr_overflow_observed"]
        and record["child_stderr_captured_byte_count_observed"]
        and record["child_stderr_captured_byte_count"] == 0,
        "child_process_reap_observed": record["child_process_reap_observed"],
        "child_exit_zero": record["child_exit_code_observed"]
        and record["child_exit_code"] == 0,
        "child_contract_exact": child_contract_exact,
        "postflight_custody_exact": record["postflight_custody_exact"],
    }
    transport_gates = _validate_gate_map(
        record["transport_gate_vector"],
        TRANSPORT_GATE_ORDER,
        "terminal transport gates",
    )
    if transport_gates != computed_transport_gates:
        raise ContractError("terminal transport gate vector contradiction")
    if record["transport_gate_vector_sha256"] != sha256_bytes(
        canonical_json_bytes(transport_gates)
    ):
        raise ContractError("terminal transport gate digest mismatch")
    code_by_gate = dict(zip(TRANSPORT_GATE_ORDER, TRANSPORT_FAILURE_CODES[1:]))
    derived_transport_code = "NONE"
    for gate_name in TRANSPORT_GATE_ORDER:
        if not transport_gates[gate_name]:
            derived_transport_code = code_by_gate[gate_name]
            break
    if record["transport_failure_code"] != derived_transport_code:
        raise ContractError("terminal transport failure priority mismatch")
    passed = derived_transport_code == "NONE" and child_pass
    expected_outcome = "PASS" if passed else "FAIL"
    expected_state = PASS_STATE if passed else FAIL_STATE
    if record["outcome"] != expected_outcome or record["terminal_state"] != expected_state:
        raise ContractError("terminal outcome/state mismatch")
    return record


TERMINAL_PROJECTION_FIELDS = (
    "schema_version",
    "attempt_id_sha256",
    "attempt_nonce_sha256",
    "registration_record_sha256",
    "registration_raw_sha256",
    "marker_raw_sha256",
    "marker_sha256",
    "marker_raw_observed",
    "marker_self_valid",
    "authoritative_event_ordinal",
    "authoritative_event_schema",
    "authoritative_event_kind",
    "authoritative_event_raw_sha256",
    "authoritative_event_sha256",
    "authoritative_typed_event_present",
    "terminal_state_inferred_from_durable_prefix",
    "terminal_state",
    "outcome",
    "child_launch_claim_count",
    "child_process_start_count",
    "child_process_start_count_directly_observed",
    "retry_permitted",
    "runtime_approval_created",
    "scientific_execution_performed",
    "terminal_sha256",
)


def validate_terminal_projection(value: Any) -> dict[str, Any]:
    record = _validate_self(
        _require_mapping(value, "terminal projection"),
        "terminal_sha256",
        TERMINAL_PROJECTION_FIELDS,
        "terminal projection",
    )
    if record["schema_version"] != TERMINAL_PROJECTION_SCHEMA:
        raise ContractError("terminal projection schema mismatch")
    for key in (
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "registration_record_sha256",
        "registration_raw_sha256",
    ):
        _require_sha(record[key], f"terminal projection.{key}")
    for key in (
        "authoritative_typed_event_present",
        "terminal_state_inferred_from_durable_prefix",
        "child_process_start_count_directly_observed",
        "marker_raw_observed",
        "marker_self_valid",
        "retry_permitted",
        "runtime_approval_created",
        "scientific_execution_performed",
    ):
        _require_bool(record[key], f"terminal projection.{key}")
    if record["retry_permitted"] or record["runtime_approval_created"] or record["scientific_execution_performed"]:
        raise ContractError("terminal projection overclaims authority/effects")
    _require_enum(record["outcome"], ("PASS", "FAIL", "INCOMPLETE"), "terminal outcome")
    state = _require_enum(
        record["terminal_state"],
        (
            MARKER_FALLBACK_STATE,
            EVALUATION_FALLBACK_STATE,
            PRECHILD_FAILURE_STATE,
            ADMISSION_FALLBACK_STATE,
            POST_ADMISSION_FAILURE_STATE,
            CHILD_FALLBACK_STATE,
            PASS_STATE,
            FAIL_STATE,
        ),
        "terminal state",
    )
    table = {
        MARKER_FALLBACK_STATE: (
            None,
            None,
            None,
            False,
            True,
            "INCOMPLETE",
            0,
            0,
        ),
        EVALUATION_FALLBACK_STATE: (
            0,
            EVALUATION_CLAIM_SCHEMA,
            "PRECHILD_EVALUATION_CLAIM",
            True,
            True,
            "INCOMPLETE",
            0,
            0,
        ),
        PRECHILD_FAILURE_STATE: (
            1,
            PRECHILD_FAILURE_SCHEMA,
            "PRECHILD_FAILURE",
            True,
            False,
            "FAIL",
            0,
            0,
        ),
        ADMISSION_FALLBACK_STATE: (
            1,
            PRECHILD_ADMISSION_SCHEMA,
            "PRECHILD_ADMISSION",
            True,
            True,
            "INCOMPLETE",
            0,
            0,
        ),
        POST_ADMISSION_FAILURE_STATE: (
            2,
            POST_ADMISSION_FAILURE_SCHEMA,
            "POST_ADMISSION_PRECHILD_FAILURE",
            True,
            False,
            "FAIL",
            0,
            0,
        ),
        CHILD_FALLBACK_STATE: (
            2,
            CHILD_CLAIM_SCHEMA,
            "CHILD_LAUNCH_CLAIM",
            True,
            True,
            "INCOMPLETE",
            1,
            None,
        ),
        PASS_STATE: (
            3,
            TERMINAL_OUTCOME_SCHEMA,
            "TERMINAL_OUTCOME",
            True,
            False,
            "PASS",
            1,
            1,
        ),
        FAIL_STATE: (
            3,
            TERMINAL_OUTCOME_SCHEMA,
            "TERMINAL_OUTCOME",
            True,
            False,
            "FAIL",
            1,
            "ZERO_OR_ONE",
        ),
    }
    _require_fixed(record, "marker_raw_observed", True, "terminal projection")
    _require_fixed(record, "marker_self_valid", True, "terminal projection")
    _require_sha(record["marker_raw_sha256"], "terminal projection marker raw digest")
    _require_sha(record["marker_sha256"], "terminal projection marker self digest")
    (
        ordinal,
        event_schema,
        event_kind,
        typed,
        inferred,
        outcome,
        child_claim_count,
        child_process_count,
    ) = table[state]
    expected = {
        "authoritative_event_ordinal": ordinal,
        "authoritative_event_schema": event_schema,
        "authoritative_event_kind": event_kind,
        "authoritative_typed_event_present": typed,
        "terminal_state_inferred_from_durable_prefix": inferred,
        "outcome": outcome,
        "child_launch_claim_count": child_claim_count,
    }
    if child_process_count == "ZERO_OR_ONE":
        if type(record["child_process_start_count"]) is not int or record[
            "child_process_start_count"
        ] not in (0, 1):
            raise ContractError("failed terminal process-start count outside 0..1")
        _require_fixed(
            record,
            "child_process_start_count_directly_observed",
            True,
            "terminal projection",
        )
    else:
        expected["child_process_start_count"] = child_process_count
        expected["child_process_start_count_directly_observed"] = (
            child_process_count is not None
        )
    for key, expected_value in expected.items():
        _require_fixed(record, key, expected_value, "terminal projection")
    if ordinal is None:
        if record["authoritative_event_raw_sha256"] is not None or record["authoritative_event_sha256"] is not None:
            raise ContractError("marker-only projection cannot name an event")
    else:
        _require_sha(
            record["authoritative_event_raw_sha256"],
            "terminal projection authoritative event raw digest",
        )
        _require_sha(
            record["authoritative_event_sha256"],
            "terminal projection authoritative event self digest",
        )
    return record


def validate_terminal_projection_against_prefix(
    value: Any,
    marker: Mapping[str, Any],
    marker_raw: bytes,
    authorization_record: Mapping[str, Any],
    expected_registration_record_sha256: str,
    expected_registration_raw_sha256: str,
    authoritative_event: Mapping[str, Any] | None,
    authoritative_event_raw: bytes | None,
) -> dict[str, Any]:
    projection = validate_terminal_projection(value)
    marker_checked = validate_marker(
        marker,
        authorization_record,
        expected_registration_record_sha256,
        expected_registration_raw_sha256,
    )
    if type(marker_raw) is not bytes or marker_raw != canonical_file_bytes(
        marker_checked
    ):
        raise ContractError("terminal projection marker raw bytes mismatch")
    marker_expected = {
        "attempt_id_sha256": marker_checked["attempt_id_sha256"],
        "attempt_nonce_sha256": marker_checked["attempt_nonce_sha256"],
        "registration_record_sha256": marker_checked["registration_record_sha256"],
        "registration_raw_sha256": marker_checked["registration_raw_sha256"],
        "marker_raw_sha256": sha256_bytes(marker_raw),
        "marker_sha256": marker_checked["marker_sha256"],
    }
    for key, expected_value in marker_expected.items():
        _require_fixed(projection, key, expected_value, "terminal projection marker")
    if projection["authoritative_event_ordinal"] is None:
        if authoritative_event is not None or authoritative_event_raw is not None:
            raise ContractError("marker-only projection received an event")
        return projection
    if authoritative_event is None or type(authoritative_event_raw) is not bytes:
        raise ContractError("terminal projection requires authoritative event bytes")
    event = validate_event(authoritative_event)
    if authoritative_event_raw != canonical_file_bytes(event):
        raise ContractError("terminal projection authoritative bytes mismatch")
    expected = {
        "authoritative_event_ordinal": event["event_ordinal"],
        "authoritative_event_schema": event["schema_version"],
        "authoritative_event_kind": event["event_kind"],
        "authoritative_event_raw_sha256": sha256_bytes(authoritative_event_raw),
        "authoritative_event_sha256": event["event_sha256"],
    }
    for key in (
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "registration_record_sha256",
        "registration_raw_sha256",
        "marker_raw_sha256",
        "marker_sha256",
    ):
        if event[key] != marker_expected[key]:
            raise ContractError(f"terminal projection cross-attempt event: {key}")
    if event["schema_version"] == TERMINAL_OUTCOME_SCHEMA:
        expected["terminal_state"] = event["terminal_state"]
        expected["outcome"] = event["outcome"]
        expected["child_launch_claim_count"] = event["child_launch_claim_count"]
        expected["child_process_start_count"] = event["child_process_start_count"]
        expected["child_process_start_count_directly_observed"] = True
    for key, expected_value in expected.items():
        _require_fixed(projection, key, expected_value, "terminal projection prefix")
    return projection


def validate_full_prefix(
    marker: Mapping[str, Any],
    marker_raw: bytes,
    authorization_record: Mapping[str, Any],
    expected_registration_record_sha256: str,
    expected_registration_raw_sha256: str,
    genesis: Mapping[str, Any],
    genesis_raw: bytes,
    events: Sequence[Mapping[str, Any]],
    event_raws: Sequence[bytes],
    terminal_projection: Mapping[str, Any] | None = None,
    terminal_projection_raw: bytes | None = None,
) -> dict[str, Any]:
    if type(events) not in (list, tuple) or type(event_raws) not in (list, tuple):
        raise ContractError("full prefix events must be concrete sequences")
    if len(events) != len(event_raws) or len(events) > 4:
        raise ContractError("full prefix event count mismatch")
    marker_checked = validate_marker(
        marker,
        authorization_record,
        expected_registration_record_sha256,
        expected_registration_raw_sha256,
    )
    genesis_checked = validate_genesis(
        genesis,
        marker_checked,
        authorization_record,
        expected_registration_record_sha256,
        expected_registration_raw_sha256,
        marker_raw,
    )
    if type(genesis_raw) is not bytes or genesis_raw != canonical_file_bytes(
        genesis_checked
    ):
        raise ContractError("full prefix genesis raw bytes mismatch")
    checked_events: list[dict[str, Any]] = []
    prior = None
    prior_raw = None
    for event_value, event_raw in zip(events, event_raws):
        event = validate_event_chain(
            event_value,
            marker_checked,
            authorization_record,
            expected_registration_record_sha256,
            expected_registration_raw_sha256,
            marker_raw,
            genesis,
            genesis_raw,
            prior,
            prior_raw,
        )
        if type(event_raw) is not bytes or event_raw != canonical_file_bytes(event):
            raise ContractError("full prefix event raw bytes mismatch")
        checked_events.append(event)
        prior = event
        prior_raw = event_raw
    schemas = [event["schema_version"] for event in checked_events]
    allowed = {
        (): MARKER_FALLBACK_STATE,
        (EVALUATION_CLAIM_SCHEMA,): EVALUATION_FALLBACK_STATE,
        (EVALUATION_CLAIM_SCHEMA, PRECHILD_FAILURE_SCHEMA): PRECHILD_FAILURE_STATE,
        (EVALUATION_CLAIM_SCHEMA, PRECHILD_ADMISSION_SCHEMA): ADMISSION_FALLBACK_STATE,
        (
            EVALUATION_CLAIM_SCHEMA,
            PRECHILD_ADMISSION_SCHEMA,
            POST_ADMISSION_FAILURE_SCHEMA,
        ): POST_ADMISSION_FAILURE_STATE,
        (
            EVALUATION_CLAIM_SCHEMA,
            PRECHILD_ADMISSION_SCHEMA,
            CHILD_CLAIM_SCHEMA,
        ): CHILD_FALLBACK_STATE,
    }
    schedule = tuple(schemas)
    terminal_schedule = (
        EVALUATION_CLAIM_SCHEMA,
        PRECHILD_ADMISSION_SCHEMA,
        CHILD_CLAIM_SCHEMA,
        TERMINAL_OUTCOME_SCHEMA,
    )
    if schedule == terminal_schedule:
        expected_state = checked_events[-1]["terminal_state"]
    elif schedule in allowed:
        expected_state = allowed[schedule]
    else:
        raise ContractError("full prefix schedule outside frozen state machine")
    terminal_checked = None
    if terminal_projection is None:
        if terminal_projection_raw is not None:
            raise ContractError("terminal projection raw bytes without record")
    else:
        terminal_checked = validate_terminal_projection_against_prefix(
            terminal_projection,
            marker_checked,
            marker_raw,
            authorization_record,
            expected_registration_record_sha256,
            expected_registration_raw_sha256,
            checked_events[-1] if checked_events else None,
            event_raws[-1] if checked_events else None,
        )
        if type(terminal_projection_raw) is not bytes or terminal_projection_raw != canonical_file_bytes(
            terminal_checked
        ):
            raise ContractError("terminal projection raw bytes mismatch")
        _require_fixed(
            terminal_checked,
            "terminal_state",
            expected_state,
            "full prefix terminal",
        )
    return {
        "attempt_id_sha256": marker_checked["attempt_id_sha256"],
        "attempt_nonce_sha256": marker_checked["attempt_nonce_sha256"],
        "event_count": len(checked_events),
        "events": checked_events,
        "expected_terminal_state": expected_state,
        "terminal_projection": terminal_checked,
    }


PUBLISHED_RESULT_FIELDS = (
    "schema_version",
    "registration_record_sha256",
    "attempt_id_sha256",
    "attempt_nonce_sha256",
    "local_terminal_raw_sha256",
    "local_terminal_sha256",
    "terminal_state",
    "outcome",
    "retry_permitted",
    "runtime_approval_created",
    "scientific_execution_performed",
    "raw_environment_published",
    "raw_identity_published",
    "raw_path_or_argv_published",
    "record_sha256",
)


def validate_published_result(
    value: Any, terminal: Mapping[str, Any]
) -> dict[str, Any]:
    terminal_checked = validate_terminal_projection(terminal)
    record = _validate_self(
        _require_mapping(value, "published result"),
        "record_sha256",
        PUBLISHED_RESULT_FIELDS,
        "published result",
    )
    if record["schema_version"] != PUBLISHED_RESULT_SCHEMA:
        raise ContractError("published result schema mismatch")
    for key in (
        "registration_record_sha256",
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "local_terminal_raw_sha256",
        "local_terminal_sha256",
    ):
        _require_sha(record[key], f"published result.{key}")
    for key in (
        "registration_record_sha256",
        "attempt_id_sha256",
        "attempt_nonce_sha256",
        "terminal_state",
        "outcome",
    ):
        if record[key] != terminal_checked[key]:
            raise ContractError(f"published result terminal link {key} mismatch")
    if record["local_terminal_sha256"] != terminal_checked["terminal_sha256"]:
        raise ContractError("published result terminal self link mismatch")
    if record["local_terminal_raw_sha256"] != sha256_bytes(
        canonical_file_bytes(terminal_checked)
    ):
        raise ContractError("published result terminal raw link mismatch")
    for key in (
        "retry_permitted",
        "runtime_approval_created",
        "scientific_execution_performed",
        "raw_environment_published",
        "raw_identity_published",
        "raw_path_or_argv_published",
    ):
        if _require_bool(record[key], f"published result.{key}"):
            raise ContractError(f"published result forbidden field {key}")
    return record


def validate_published_result_against_full_prefix(
    value: Any,
    marker: Mapping[str, Any],
    marker_raw: bytes,
    authorization_record: Mapping[str, Any],
    expected_registration_record_sha256: str,
    expected_registration_raw_sha256: str,
    genesis: Mapping[str, Any],
    genesis_raw: bytes,
    events: Sequence[Mapping[str, Any]],
    event_raws: Sequence[bytes],
    terminal_projection: Mapping[str, Any],
    terminal_projection_raw: bytes,
) -> dict[str, Any]:
    """Validate a publication only after reopening its complete durable prefix."""

    prefix = validate_full_prefix(
        marker,
        marker_raw,
        authorization_record,
        expected_registration_record_sha256,
        expected_registration_raw_sha256,
        genesis,
        genesis_raw,
        events,
        event_raws,
        terminal_projection,
        terminal_projection_raw,
    )
    anchored_terminal = prefix["terminal_projection"]
    if anchored_terminal is None:
        raise ContractError("published result requires an anchored terminal projection")
    return validate_published_result(value, anchored_terminal)


def load_canonical_record(raw: bytes, maximum_bytes: int = 1 << 20) -> dict[str, Any]:
    if type(raw) is not bytes or not raw or len(raw) > maximum_bytes:
        raise ContractError("record byte length outside contract")
    if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
        raise ContractError("record must contain one terminal LF")
    try:
        value = json.loads(raw[:-1].decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("record JSON invalid") from exc
    mapping = _require_mapping(value, "record")
    if canonical_file_bytes(mapping) != raw:
        raise ContractError("record bytes are not canonical")
    return dict(mapping)


def make_marker(
    registration_record_sha256: str,
    registration_raw_sha256: str,
    authorization_record_sha256: str,
    authorization_raw_sha256: str,
) -> dict[str, Any]:
    attempt_id, attempt_nonce = derive_attempt_identity(
        registration_record_sha256,
        authorization_record_sha256,
        authorization_raw_sha256,
    )
    return attach_digest(
        {
            "schema_version": MARKER_SCHEMA,
            "attempt_ordinal": 0,
            "attempt_id_sha256": attempt_id,
            "attempt_nonce_sha256": attempt_nonce,
            "nonce_kind": "DETERMINISTIC_NONSECRET_CUSTODY_IDENTIFIER",
            "entropy_draw_count": 0,
            "registration_record_sha256": registration_record_sha256,
            "registration_raw_sha256": registration_raw_sha256,
            "execution_authorization_record_sha256": authorization_record_sha256,
            "execution_authorization_raw_sha256": authorization_raw_sha256,
            "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
            "visible_assent_sha256": VISIBLE_ASSENT_SHA256,
            "marker_path": MARKER_PATH,
            "fallback_terminal_state": MARKER_FALLBACK_STATE,
            "retry_permitted": False,
        },
        "marker_sha256",
    )


__all__ = [name for name in globals() if name.isupper()] + [
    "ContractError",
    "attach_digest",
    "canonical_file_bytes",
    "canonical_json_bytes",
    "child_failure_code",
    "derive_attempt_identity",
    "load_canonical_record",
    "make_marker",
    "prechild_failure_code",
    "sha256_bytes",
    "validate_authorization_record",
    "validate_child_observation",
    "validate_event",
    "validate_event_chain",
    "validate_full_prefix",
    "validate_genesis",
    "validate_marker",
    "validate_published_result",
    "validate_published_result_against_full_prefix",
    "validate_runtime_request",
    "validate_terminal_outcome",
    "validate_terminal_projection",
    "validate_terminal_projection_against_prefix",
]
