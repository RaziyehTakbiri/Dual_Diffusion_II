"""Sole-writer authority for the frozen transition-safe V4 rehearsal.

Import and status paths are read-only.  The future ``--execute-once`` route is
the only canonical writer.  It is frozen here but is not authorized or invoked
by this milestone.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


MODULE_PATH = Path(__file__).absolute()
WORKSPACE_ROOT = MODULE_PATH.parents[2]
HUMAN_PATH = WORKSPACE_ROOT / (
    "manuscript_v3/a1_r1_activation_preparation_v4_transition_safe_live_host_"
    "environment_rehearsal_freeze_v1.md"
)
MACHINE_PATH = WORKSPACE_ROOT / (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_freeze_v1.json"
)
CONTRACTS_PATH = WORKSPACE_ROOT / (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_contracts_v4.py"
)
AUTHORITY_PATH = MODULE_PATH
AUTHORITY_RELATIVE_PATH = Path(
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_authority_v4.py"
)
RUNTIME_PATH = WORKSPACE_ROOT / (
    "research/production/finite_association_r1_activation_preparation_"
    "rehearsal_runtime_v4.py"
)
TEST_PATH = WORKSPACE_ROOT / (
    "tests/unit/test_manuscript_v3_a1_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_freeze_v1.py"
)
AUTHORIZATION_PATH = WORKSPACE_ROOT / (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "execution_authorization_v1.json"
)
MARKER_PATH = WORKSPACE_ROOT / "artifacts/a1_r1_activation_preparation_v4.attempt.json"
PREPARATION_ROOT = WORKSPACE_ROOT / "artifacts/a1_r1_activation_preparation_v4"
LEDGER_PATH = PREPARATION_ROOT / "ledger"
EVENTS_PATH = LEDGER_PATH / "events"
LOCK_PATH = LEDGER_PATH / "writer.lock"
GENESIS_PATH = LEDGER_PATH / "genesis.json"
TERMINAL_PATH = LEDGER_PATH / "terminal.json"
RESULT_PATH = WORKSPACE_ROOT / (
    "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
    "transition_safe_live_host_environment_rehearsal_result_v1.json"
)
V3_TERMINAL_VALIDATOR_PATH = WORKSPACE_ROOT / (
    "research/diagnostics/finite_association_r1_activation_preparation_v3_"
    "live_host_environment_rehearsal_terminal_failure_registration_v1.py"
)

REGISTRATION_SCHEMA = (
    "heterodiff-manuscript-v3-a1-r1-activation-preparation-v4-transition-safe-"
    "live-host-environment-rehearsal-freeze-v1"
)
AUTHORIZATION_SCHEMA = (
    "heterodiff-manuscript-v3-a1-r1-activation-preparation-v4-"
    "execution-authorization-v1"
)
GLOBAL_STATE = "DRAFT_NOT_EXECUTABLE"
STATIC_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_TRANSITION_SAFE_IMPLEMENTATION_FROZEN_"
    "AWAITING_FRESH_EXACT_AUTHORIZATION_NO_ATTEMPT_SPEND_NOT_EXECUTABLE"
)
AUTH_RECORDED_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_EXECUTION_AUTHORIZATION_RECORDED_"
    "AWAITING_ATTEMPT_SPEND_NO_SCIENTIFIC_EXECUTION_AUTHORITY"
)
STATUS_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-transition-safe-live-host-"
    "environment-rehearsal-status-v1"
)
TERMINAL_PROJECTION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-terminal-projection-v1"
)
PUBLISHED_RESULT_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-published-result-v1"
)
MARKER_FALLBACK_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_ATTEMPT_SPENT_RESERVATION_PUBLISHED_"
    "PRE_EVALUATION_TERMINAL_FALLBACK_NO_RETRY"
)
EVALUATION_FALLBACK_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_ATTEMPT_SPENT_PRECHILD_EVALUATION_"
    "CLAIMED_TERMINAL_FALLBACK_NO_RETRY"
)
INVALID_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_CUSTODY_INVALID_TERMINAL_NO_RETRY_"
    "NOT_EXECUTABLE"
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
AUTHORIZATION_CONTEXT_SHA256 = (
    "3e989c3935c829a5920992b29de6001369c29c9fb25f686eb44ee48be6026417"
)
VISIBLE_ASSENT_TEXT = (
    "I authorize the single frozen V4 rehearsal attempt described above, with no "
    "retry or scientific execution."
)
VISIBLE_ASSENT_SHA256 = (
    "33c38693197abe2849d02736250138322c452c4294552258757cfd5ae3a77994"
)
ATTEMPT_ID_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-v4-attempt-identity-v1\0"
)
ATTEMPT_NONCE_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-v4-deterministic-attempt-nonce-v1\0"
)
EXPECTED_CONTRACTS_RAW_SHA256 = (
    "b3453d980d4f1a9f4312aa04acaa18c9369b7144d5b9ba7abe6cc368def441c2"
)
EXPECTED_RUNTIME_RAW_SHA256 = (
    "e2d2924dac36fa4114083d535166af87db590476fbf1bba9b01361404eda3bc2"
)
EXPECTED_V3_TERMINAL_VALIDATOR_RAW_SHA256 = (
    "2ae995d7609778f9201e3a90a2861c74898dfdc357b3f0b6f75b46bc68ce78bd"
)
# Rebound after the machine static plan is generated.  It deliberately excludes
# registration_bindings and record_sha256, breaking the unavoidable self-cycle.
EXPECTED_REGISTRATION_STATIC_PLAN_SHA256 = (
    "6121d0db6fa021b1b173c8ff2321d229c4d2f3ba4faf94810e872a7f21b0b8a4"
)

PYTHON_PATH = WORKSPACE_ROOT / ".venv-m1/bin/python"
PYTHON_REALPATH = Path(
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
)
PYTHON_FLAGS = ("-P", "-B", "-S", "-X", "utf8")
REQUESTED_ENVIRONMENT = {
    "BLIS_NUM_THREADS": "1",
    "CUDA_VISIBLE_DEVICES": "",
    "LANG": "C",
    "LC_ALL": "C",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONPYCACHEPREFIX": "/dev/null",
    "PYTHONSAFEPATH": "1",
    "PYTHONUTF8": "1",
    "TZ": "UTC",
    "VECLIB_MAXIMUM_THREADS": "1",
}
DARWIN_KEY = "__CF_USER_TEXT_ENCODING"
HASH_PROBE_STRINGS = (
    "heterodiff-a1",
    "dual-manifold",
    "runtime-attestor",
    "frozen-prerequisite-v2",
)
HASH_PROBE_SHA256 = "f7b1ba1308d7559c69fc44640d0fcd07dbeae53b9024da5d862463db71e230af"
MAX_RECORD_BYTES = 1 << 20
MAX_STDOUT_BYTES = 64 * 1024
MAX_STDERR_BYTES = 4 * 1024
CHILD_TIMEOUT_SECONDS = 20.0

# These literals deliberately duplicate the audited record contract so that a
# controlled contracts-module admission failure can still be durably expressed
# as event 1 after event 0 has spent the attempt.  The loaded contracts module
# is cross-checked against this roster whenever it is available.
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
EVALUATION_CLAIM_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-prechild-evaluation-claim-v1"
)
PRECHILD_FAILURE_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-prechild-failure-v1"
)
PRECHILD_ADMISSION_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-prechild-admission-v1"
)
PRECHILD_FAILURE_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_TERMINAL_PRECHILD_FAILURE_NO_CHILD_"
    "NO_RETRY_NOT_EXECUTABLE"
)
ADMISSION_FALLBACK_STATE = (
    "R1_A1_ACTIVATION_PREPARATION_V4_TERMINAL_PRECHILD_ADMISSION_WITHOUT_"
    "CHILD_CLAIM_NO_RETRY_NOT_EXECUTABLE"
)
POST_ADMISSION_FAILURE_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-"
    "post-admission-prechild-failure-v1"
)
CHILD_CLAIM_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-child-launch-claim-v1"
)
TERMINAL_OUTCOME_SCHEMA = (
    "heterodiff-a1-r1-activation-preparation-v4-terminal-outcome-v1"
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

# This tracker describes only explicit application-level forbidden API/source
# effects.  It is not instrumentation of Python startup, the kernel, or the OS.
_APPLICATION_EFFECTS: Dict[str, int] = {
    "explicit_entropy_api_calls": 0,
    "explicit_network_api_calls": 0,
    "scientific_import_or_execution_calls": 0,
    "temporary_output_writes": 0,
    "unregistered_workspace_writes": 0,
    "raw_environment_emissions": 0,
    "raw_identity_emissions": 0,
    "raw_path_or_argv_emissions": 0,
}

# Installed only by the exact direct-file route after a canonical marker has
# been durably published and reopened.  It is an honest-host procedural guard,
# not a cryptographic capability or a malicious-same-process boundary.
_LIVE_CUSTODY: Optional[Dict[str, Any]] = None


class AuthorityError(RuntimeError):
    """A privacy-safe, fail-closed authority error."""


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise AuthorityError("canonical record failure") from exc


def _file_bytes(value: Any) -> bytes:
    return _canonical(value) + b"\n"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _attach(body: Mapping[str, Any], digest_key: str) -> Dict[str, Any]:
    if type(body) is not dict or digest_key in body:
        raise AuthorityError("record construction failure")
    record = dict(body)
    record[digest_key] = _sha(_canonical(record))
    return record


def _is_sha(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _record_self_exact(record: Mapping[str, Any], key: str) -> bool:
    if type(record) is not dict or not _is_sha(record.get(key)):
        return False
    body = dict(record)
    claimed = body.pop(key)
    return claimed == _sha(_canonical(body))


def _lstat(path: Path) -> Optional[os.stat_result]:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def _structural_identity(status: os.stat_result) -> Tuple[int, int, int, int, int, int]:
    return (
        status.st_dev,
        status.st_ino,
        stat.S_IFMT(status.st_mode),
        stat.S_IMODE(status.st_mode),
        status.st_uid,
        status.st_gid,
    )


def _leaf_identity(status: os.stat_result) -> Tuple[int, ...]:
    return (
        *_structural_identity(status),
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _lexically_normal_absolute(path: Path) -> Path:
    if not path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise AuthorityError("noncanonical path")
    normalized = Path(os.path.normpath(str(path)))
    if normalized != path:
        raise AuthorityError("non-normalized path")
    return path


def _ancestor_snapshot(
    path: Path, stop: Optional[Path] = None
) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
    path = _lexically_normal_absolute(path)
    boundary = WORKSPACE_ROOT.parent if stop is None else _lexically_normal_absolute(stop)
    if boundary != path.parent and boundary not in path.parents:
        raise AuthorityError("path is outside custody boundary")
    rows: List[Tuple[str, Tuple[int, ...]]] = []
    current = path.parent
    while True:
        status = current.lstat()
        if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
            raise AuthorityError("unsafe ancestor")
        rows.append((str(current), _structural_identity(status)))
        if current == boundary:
            break
        if current == current.parent:
            raise AuthorityError("path escapes workspace ancestry")
        current = current.parent
    return tuple(rows)


def _require_ancestors(snapshot: Tuple[Tuple[str, Tuple[int, ...]], ...]) -> None:
    for raw_path, expected in snapshot:
        status = Path(raw_path).lstat()
        if _structural_identity(status) != expected:
            raise AuthorityError("ancestor identity changed")


def _stable_read(
    path: Path,
    mode: int = 0o644,
    maximum: int = MAX_RECORD_BYTES,
    ancestry_stop: Optional[Path] = None,
) -> bytes:
    ancestors = _ancestor_snapshot(path, ancestry_stop)
    before_path = path.lstat()
    if (
        not stat.S_ISREG(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != mode
        or before_path.st_nlink != 1
    ):
        raise AuthorityError("file custody invalid")
    descriptor = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before_fd = os.fstat(descriptor)
        if _leaf_identity(before_fd) != _leaf_identity(before_path):
            raise AuthorityError("file identity mismatch")
        chunks: List[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65536, maximum + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > maximum:
                raise AuthorityError("file exceeds bound")
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    joined = b"".join(chunks)
    if (
        _leaf_identity(before_fd) != _leaf_identity(after_fd)
        or _leaf_identity(after_fd) != _leaf_identity(after_path)
        or len(joined) != before_fd.st_size
        or not stat.S_ISREG(after_path.st_mode)
        or stat.S_ISLNK(after_path.st_mode)
        or stat.S_IMODE(after_path.st_mode) != mode
        or after_path.st_nlink != 1
        or after_fd.st_nlink != 1
    ):
        raise AuthorityError("file changed during read")
    _require_ancestors(ancestors)
    return joined


def _parse_canonical(raw: bytes) -> Dict[str, Any]:
    if not raw or not raw.endswith(b"\n") or raw.count(b"\n") != 1:
        raise AuthorityError("noncanonical record framing")
    try:
        value = json.loads(raw[:-1].decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthorityError("invalid record JSON") from exc
    if type(value) is not dict or _file_bytes(value) != raw:
        raise AuthorityError("record bytes are noncanonical")
    return value


def _read_record(
    path: Path, mode: int = 0o644, ancestry_stop: Optional[Path] = None
) -> Tuple[bytes, Dict[str, Any]]:
    raw = _stable_read(path, mode, ancestry_stop=ancestry_stop)
    return raw, _parse_canonical(raw)


def _registration_static_plan_sha256(record: Mapping[str, Any]) -> str:
    body = dict(record)
    body.pop("record_sha256", None)
    body.pop("static_plan_sha256", None)
    body.pop("registration_bindings", None)
    return _sha(_canonical(body))


def _validate_registration_binding_shape(record: Mapping[str, Any]) -> None:
    rows = record.get("registration_bindings")
    expected = (
        ("HUMAN_FREEZE", HUMAN_PATH),
        ("CONTRACTS", CONTRACTS_PATH),
        ("SOLE_WRITER_AUTHORITY", AUTHORITY_PATH),
        ("ENVIRONMENT_CHILD", RUNTIME_PATH),
        ("HOSTILE_TEST", TEST_PATH),
    )
    if type(rows) is not list or len(rows) != len(expected):
        raise AuthorityError("registration binding roster invalid")
    for ordinal, (row, (role, path)) in enumerate(zip(rows, expected)):
        if type(row) is not dict or set(row) != {
            "ordinal",
            "role",
            "path",
            "raw_sha256",
            "bytes",
            "mode_octal",
            "nlink",
        }:
            raise AuthorityError("registration binding field roster invalid")
        fixed = {
            "ordinal": ordinal,
            "role": role,
            "path": str(path.relative_to(WORKSPACE_ROOT)),
            "mode_octal": "0644",
            "nlink": 1,
        }
        for key, expected_value in fixed.items():
            if type(row[key]) is not type(expected_value) or row[key] != expected_value:
                raise AuthorityError("registration binding shape mismatch")
        if not _is_sha(row["raw_sha256"]) or type(row["bytes"]) is not int or row[
            "bytes"
        ] <= 0:
            raise AuthorityError("registration binding digest/size invalid")


def _load_registration() -> Tuple[bytes, Dict[str, Any]]:
    raw, record = _read_record(MACHINE_PATH)
    if (
        record.get("schema_version") != REGISTRATION_SCHEMA
        or record.get("global_state") != GLOBAL_STATE
        or record.get("milestone_state") != STATIC_STATE
        or not _record_self_exact(record, "record_sha256")
        or record.get("static_plan_sha256")
        != _registration_static_plan_sha256(record)
        or record.get("static_plan_sha256")
        != EXPECTED_REGISTRATION_STATIC_PLAN_SHA256
    ):
        raise AuthorityError("static registration invalid")
    _validate_registration_binding_shape(record)
    return raw, record


def _authorization_expected_fields() -> Dict[str, Any]:
    return {
        "schema_version": AUTHORIZATION_SCHEMA,
        "authorization_context_text": AUTHORIZATION_CONTEXT_TEXT,
        "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
        "normalized_visible_assent_text": VISIBLE_ASSENT_TEXT,
        "normalized_visible_assent_sha256": VISIBLE_ASSENT_SHA256,
        "assent_source": "CONVERSATION_VISIBLE_TEXT",
        "assent_normalization": "TRAILING_TRANSPORT_WHITESPACE_OR_ENTITY_NORMALIZED",
        "raw_transport_bytes_bound": False,
        "authorization_record_path": str(AUTHORIZATION_PATH.relative_to(WORKSPACE_ROOT)),
        "honest_host_procedural_authority": True,
        "cryptographic_user_authentication": False,
        "record_self_digests_are_user_authentication": False,
        "malicious_host_resistance_claimed": False,
        "authorized_action": "V4_EXECUTE_ONCE",
        "authorized_attempt_count": 1,
        "authorized_child_launch_maximum": 1,
        "authorized_output_paths": [
            str(AUTHORIZATION_PATH.relative_to(WORKSPACE_ROOT)),
            str(MARKER_PATH.relative_to(WORKSPACE_ROOT)),
            str(PREPARATION_ROOT.relative_to(WORKSPACE_ROOT)),
            str(TERMINAL_PATH.relative_to(WORKSPACE_ROOT)),
            str(RESULT_PATH.relative_to(WORKSPACE_ROOT)),
        ],
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


def _load_authorization_anchor_at(
    path: Path, ancestry_stop: Optional[Path] = None
) -> Tuple[bytes, Dict[str, Any]]:
    raw, record = _read_record(path, ancestry_stop=ancestry_stop)
    expected = _authorization_expected_fields()
    if set(record) != set(expected) | {
        "v4_registration_record_sha256",
        "v4_registration_raw_sha256",
        "record_sha256",
    }:
        raise AuthorityError("authorization field roster invalid")
    for key, value in expected.items():
        if type(record[key]) is not type(value) or record[key] != value:
            raise AuthorityError("authorization semantics invalid")
    if not _record_self_exact(record, "record_sha256"):
        raise AuthorityError("authorization self digest invalid")
    if not _is_sha(record["v4_registration_record_sha256"]) or not _is_sha(
        record["v4_registration_raw_sha256"]
    ):
        raise AuthorityError("authorization registration anchor invalid")
    return raw, record


def _load_authorization_anchor() -> Tuple[bytes, Dict[str, Any]]:
    return _load_authorization_anchor_at(AUTHORIZATION_PATH)


def _load_authorization(
    registration_raw: bytes, registration: Mapping[str, Any]
) -> Tuple[bytes, Dict[str, Any]]:
    raw, record = _load_authorization_anchor()
    if (
        record["v4_registration_record_sha256"] != registration["record_sha256"]
        or record["v4_registration_raw_sha256"] != _sha(registration_raw)
    ):
        raise AuthorityError("authorization-to-registration anchor mismatch")
    return raw, record


def _load_bootstrap_closure() -> Tuple[
    bytes, Dict[str, Any], bytes, Dict[str, Any]
]:
    authorization_raw, authorization = _load_authorization_anchor()
    registration_raw, registration = _load_registration()
    if (
        _sha(registration_raw) != authorization["v4_registration_raw_sha256"]
        or registration["record_sha256"]
        != authorization["v4_registration_record_sha256"]
    ):
        raise AuthorityError("bootstrap external registration anchor mismatch")
    return registration_raw, registration, authorization_raw, authorization


def _derive_attempt(
    registration: Mapping[str, Any], authorization_raw: bytes, authorization: Mapping[str, Any]
) -> Tuple[str, str]:
    identity = _canonical(
        {
            "attempt_ordinal": 0,
            "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
            "execution_authorization_raw_sha256": _sha(authorization_raw),
            "execution_authorization_record_sha256": authorization["record_sha256"],
            "registration_record_sha256": registration["record_sha256"],
            "visible_assent_sha256": VISIBLE_ASSENT_SHA256,
        }
    )
    attempt_id = _sha(ATTEMPT_ID_DOMAIN + identity)
    nonce = _sha(
        ATTEMPT_NONCE_DOMAIN
        + _canonical(
            {
                "attempt_id_sha256": attempt_id,
                "attempt_ordinal": 0,
                "marker_path": str(MARKER_PATH.relative_to(WORKSPACE_ROOT)),
            }
        )
    )
    return attempt_id, nonce


def _make_marker(
    registration_raw: bytes,
    registration: Mapping[str, Any],
    authorization_raw: bytes,
    authorization: Mapping[str, Any],
) -> Dict[str, Any]:
    attempt_id, nonce = _derive_attempt(registration, authorization_raw, authorization)
    return _attach(
        {
            "schema_version": "heterodiff-a1-r1-activation-preparation-v4-attempt-marker-v1",
            "attempt_ordinal": 0,
            "attempt_id_sha256": attempt_id,
            "attempt_nonce_sha256": nonce,
            "nonce_kind": "DETERMINISTIC_NONSECRET_CUSTODY_IDENTIFIER",
            "entropy_draw_count": 0,
            "registration_record_sha256": registration["record_sha256"],
            "registration_raw_sha256": _sha(registration_raw),
            "execution_authorization_record_sha256": authorization["record_sha256"],
            "execution_authorization_raw_sha256": _sha(authorization_raw),
            "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
            "visible_assent_sha256": VISIBLE_ASSENT_SHA256,
            "marker_path": str(MARKER_PATH.relative_to(WORKSPACE_ROOT)),
            "fallback_terminal_state": (
                "R1_A1_ACTIVATION_PREPARATION_V4_ATTEMPT_SPENT_RESERVATION_"
                "PUBLISHED_PRE_EVALUATION_TERMINAL_FALLBACK_NO_RETRY"
            ),
            "retry_permitted": False,
        },
        "marker_sha256",
    )


def _native_argv() -> Tuple[str, ...]:
    import ctypes

    if sys.platform != "darwin":
        return tuple(sys.argv)
    library = ctypes.CDLL(None)
    argc_pointer = library._NSGetArgc
    argc_pointer.restype = ctypes.POINTER(ctypes.c_int)
    argv_pointer = library._NSGetArgv
    argv_pointer.restype = ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))
    argc = argc_pointer().contents.value
    argv = argv_pointer().contents
    return tuple(argv[index].decode("utf-8", "strict") for index in range(argc))


def _dispatch_scope_exact() -> bool:
    if __name__ != "__main__" or __spec__ is not None:
        return False
    if sys.argv != [str(AUTHORITY_RELATIVE_PATH), "--execute-once"]:
        return False
    try:
        native = _native_argv()
    except Exception:
        return False
    expected_tail = (*PYTHON_FLAGS, str(AUTHORITY_RELATIVE_PATH), "--execute-once")
    return (
        len(native) == len(expected_tail) + 1
        and type(native[0]) is str
        and bool(native[0])
        and Path(native[0]).is_absolute()
        and native[1:] == expected_tail
        and (WORKSPACE_ROOT / AUTHORITY_RELATIVE_PATH).resolve(strict=True)
        == AUTHORITY_PATH.resolve(strict=True)
        and AUTHORITY_PATH.resolve(strict=True) == MODULE_PATH.resolve(strict=True)
        and WORKSPACE_ROOT.resolve(strict=True) == WORKSPACE_ROOT
    )


def _require_live_write_scope(
    marker_required: bool = True,
    expected_result_raw: Optional[bytes] = None,
) -> None:
    if not _dispatch_scope_exact():
        raise AuthorityError("noncanonical live write scope")
    if not marker_required:
        if _LIVE_CUSTODY is not None:
            raise AuthorityError("live custody already installed")
        return
    live = _LIVE_CUSTODY
    if type(live) is not dict or set(live) != {
        "marker_raw",
        "marker",
        "registration_raw",
        "registration",
        "authorization_raw",
        "authorization",
    }:
        raise AuthorityError("live custody capability absent")
    marker_raw = _stable_read(MARKER_PATH, 0o600)
    marker = _parse_canonical(marker_raw)
    if (
        marker_raw != live["marker_raw"]
        or marker != live["marker"]
        or not _record_self_exact(marker, "marker_sha256")
    ):
        raise AuthorityError("canonical marker custody mismatch")
    registration_raw, registration, authorization_raw, authorization = (
        _load_bootstrap_closure()
    )
    if (
        registration_raw != live["registration_raw"]
        or registration != live["registration"]
        or authorization_raw != live["authorization_raw"]
        or authorization != live["authorization"]
        or marker["registration_record_sha256"] != registration["record_sha256"]
        or marker["registration_raw_sha256"] != _sha(registration_raw)
        or marker["execution_authorization_record_sha256"]
        != authorization["record_sha256"]
        or marker["execution_authorization_raw_sha256"] != _sha(authorization_raw)
    ):
        raise AuthorityError("live static-anchor custody mismatch")
    if expected_result_raw is None:
        if _lstat(RESULT_PATH) is not None:
            raise AuthorityError("authority cannot run after external result publication")
    else:
        if type(expected_result_raw) is not bytes:
            raise AuthorityError("expected external result bytes invalid")
        if _stable_read(RESULT_PATH, 0o644) != expected_result_raw:
            raise AuthorityError("external result reservation/publication mismatch")


def _fsync_directory(path: Path) -> None:
    snapshot = _ancestor_snapshot(path / "sentinel")
    before = path.lstat()
    if not stat.S_ISDIR(before.st_mode) or stat.S_ISLNK(before.st_mode):
        raise AuthorityError("directory custody invalid")
    descriptor = os.open(
        str(path),
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        opened = os.fstat(descriptor)
        if _structural_identity(opened) != _structural_identity(before):
            raise AuthorityError("directory descriptor mismatch")
        os.fsync(descriptor)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    if (
        _structural_identity(opened) != _structural_identity(after_fd)
        or _structural_identity(after_fd) != _structural_identity(after)
    ):
        raise AuthorityError("directory identity changed")
    _require_ancestors(snapshot)


def _mkdir_live(path: Path) -> None:
    _require_live_write_scope()
    if path not in (PREPARATION_ROOT, LEDGER_PATH, EVENTS_PATH):
        raise AuthorityError("unregistered directory target")
    parent_snapshot = _ancestor_snapshot(path)
    os.mkdir(str(path), 0o700)
    os.chmod(str(path), 0o700, follow_symlinks=False)
    before_path = path.lstat()
    descriptor = os.open(
        str(path),
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        before_fd = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(before_fd.st_mode)
            or stat.S_ISLNK(before_path.st_mode)
            or stat.S_IMODE(before_fd.st_mode) != 0o700
            or _leaf_identity(before_fd) != _leaf_identity(before_path)
        ):
            raise AuthorityError("new directory custody invalid")
        os.fsync(descriptor)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    if (
        _leaf_identity(before_fd) != _leaf_identity(after_fd)
        or _leaf_identity(after_fd) != _leaf_identity(after_path)
    ):
        raise AuthorityError("new directory identity changed")
    _require_ancestors(parent_snapshot)
    _fsync_directory(path.parent)
    if _leaf_identity(path.lstat()) != _leaf_identity(after_path):
        raise AuthorityError("new directory changed during parent fsync")


def _allowed_live_file(path: Path) -> bool:
    if path in (LOCK_PATH, GENESIS_PATH, TERMINAL_PATH):
        return True
    if path.parent == EVENTS_PATH and path.name in {
        f"{ordinal:020d}.json" for ordinal in range(4)
    }:
        return True
    return False


def _write_new_live(path: Path, raw: bytes) -> None:
    _require_live_write_scope()
    if not _allowed_live_file(path) or type(raw) is not bytes or not raw:
        raise AuthorityError("unregistered live file write")
    parent_snapshot = _ancestor_snapshot(path)
    descriptor = os.open(
        str(path),
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        os.fchmod(descriptor, 0o600)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise AuthorityError("new file descriptor custody invalid")
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            if written <= 0:
                raise AuthorityError("short live file write")
            offset += written
        os.fsync(descriptor)
        published = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_status = path.lstat()
    if (
        _structural_identity(opened) != _structural_identity(published)
        or _leaf_identity(published) != _leaf_identity(path_status)
        or stat.S_IMODE(path_status.st_mode) != 0o600
        or path_status.st_nlink != 1
        or path_status.st_size != len(raw)
    ):
        raise AuthorityError("published file identity mismatch")
    _require_ancestors(parent_snapshot)
    _fsync_directory(path.parent)
    if _stable_read(path, 0o600) != raw:
        raise AuthorityError("published file reopen mismatch")


def _reserve_and_publish_marker(
    raw: bytes,
    marker: Mapping[str, Any],
    registration_raw: bytes,
    registration: Mapping[str, Any],
    authorization_raw: bytes,
    authorization: Mapping[str, Any],
) -> None:
    # This is the first operational action.  Only minimal direct-file dispatch,
    # static-registration parsing, authorization validation, and path derivation
    # may have occurred before it.
    _require_live_write_scope(marker_required=False)
    if (
        type(raw) is not bytes
        or not raw
        or type(marker) is not dict
        or raw != _file_bytes(marker)
        or not _record_self_exact(marker, "marker_sha256")
    ):
        raise AuthorityError("marker bytes invalid")
    if _lstat(MARKER_PATH) is not None or _lstat(PREPARATION_ROOT) is not None or _lstat(RESULT_PATH) is not None:
        raise AuthorityError("V4 attempt/output namespace is not pristine")
    parent_snapshot = _ancestor_snapshot(MARKER_PATH)
    descriptor = os.open(
        str(MARKER_PATH),
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        os.fchmod(descriptor, 0o600)
        reserved = os.fstat(descriptor)
        if not stat.S_ISREG(reserved.st_mode) or reserved.st_nlink != 1:
            raise AuthorityError("marker reservation custody invalid")
        os.fsync(descriptor)
        _fsync_directory(MARKER_PATH.parent)
        reserved_synced = os.fstat(descriptor)
        reserved_path = MARKER_PATH.lstat()
        if (
            _structural_identity(reserved) != _structural_identity(reserved_synced)
            or _leaf_identity(reserved_synced) != _leaf_identity(reserved_path)
            or reserved_synced.st_size != 0
        ):
            raise AuthorityError("marker reservation identity mismatch")
        import fcntl

        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if _lstat(PREPARATION_ROOT) is not None or _lstat(RESULT_PATH) is not None:
            raise AuthorityError("output race after marker reservation")
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            if written <= 0:
                raise AuthorityError("marker write failed")
            offset += written
        os.fsync(descriptor)
        published = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    current = MARKER_PATH.lstat()
    if (
        _structural_identity(reserved) != _structural_identity(published)
        or _leaf_identity(published) != _leaf_identity(current)
        or current.st_size != len(raw)
        or current.st_nlink != 1
        or stat.S_IMODE(current.st_mode) != 0o600
    ):
        raise AuthorityError("marker publication custody invalid")
    _require_ancestors(parent_snapshot)
    _fsync_directory(MARKER_PATH.parent)
    if _stable_read(MARKER_PATH, 0o600) != raw:
        raise AuthorityError("marker publication reopen mismatch")
    global _LIVE_CUSTODY
    _LIVE_CUSTODY = {
        "marker_raw": raw,
        "marker": dict(marker),
        "registration_raw": registration_raw,
        "registration": dict(registration),
        "authorization_raw": authorization_raw,
        "authorization": dict(authorization),
    }
    _require_live_write_scope()


def _create_lock() -> int:
    _require_live_write_scope()
    parent_snapshot = _ancestor_snapshot(LOCK_PATH)
    descriptor = os.open(
        str(LOCK_PATH),
        os.O_RDWR
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        import fcntl

        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or stat.S_IMODE(opened.st_mode) != 0o600
            or opened.st_size != 0
        ):
            raise AuthorityError("writer lock descriptor custody invalid")
        os.fsync(descriptor)
        synced = os.fstat(descriptor)
        current = LOCK_PATH.lstat()
        if (
            _leaf_identity(opened) != _leaf_identity(synced)
            or _leaf_identity(synced) != _leaf_identity(current)
        ):
            raise AuthorityError("writer lock custody invalid")
        _require_ancestors(parent_snapshot)
        _fsync_directory(LOCK_PATH.parent)
        after_fd = os.fstat(descriptor)
        after_path = LOCK_PATH.lstat()
        if (
            _leaf_identity(synced) != _leaf_identity(after_fd)
            or _leaf_identity(after_fd) != _leaf_identity(after_path)
        ):
            raise AuthorityError("writer lock changed during parent fsync")
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _binding_map(registration: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    rows = registration.get("registration_bindings")
    if type(rows) is not list:
        raise AuthorityError("registration binding roster invalid")
    mapping: Dict[str, Mapping[str, Any]] = {}
    for ordinal, row in enumerate(rows):
        if type(row) is not dict or row.get("ordinal") != ordinal:
            raise AuthorityError("registration binding row invalid")
        role = row.get("role")
        if type(role) is not str or role in mapping:
            raise AuthorityError("registration binding role invalid")
        mapping[role] = row
    return mapping


def _audit_v4_source_closure(
    registration_raw: bytes, registration: Mapping[str, Any]
) -> Dict[str, bytes]:
    bindings = _binding_map(registration)
    expected_paths = {
        "HUMAN_FREEZE": HUMAN_PATH,
        "CONTRACTS": CONTRACTS_PATH,
        "SOLE_WRITER_AUTHORITY": AUTHORITY_PATH,
        "ENVIRONMENT_CHILD": RUNTIME_PATH,
        "HOSTILE_TEST": TEST_PATH,
    }
    if set(bindings) != set(expected_paths):
        raise AuthorityError("registration binding role roster mismatch")
    reopened: Dict[str, bytes] = {}
    for role, path in expected_paths.items():
        raw = _stable_read(path, 0o644)
        row = bindings[role]
        expected_relative = str(path.relative_to(WORKSPACE_ROOT))
        fixed = {
            "path": expected_relative,
            "raw_sha256": _sha(raw),
            "bytes": len(raw),
            "mode_octal": "0644",
            "nlink": 1,
        }
        for key, expected in fixed.items():
            if type(row.get(key)) is not type(expected) or row.get(key) != expected:
                raise AuthorityError("registration binding mismatch")
        reopened[role] = raw
    if _sha(reopened["CONTRACTS"]) != EXPECTED_CONTRACTS_RAW_SHA256:
        raise AuthorityError("contracts external pin mismatch")
    if _sha(reopened["ENVIRONMENT_CHILD"]) != EXPECTED_RUNTIME_RAW_SHA256:
        raise AuthorityError("runtime external pin mismatch")
    return reopened


def _load_exact_module(path: Path, raw_sha256: str, name: str) -> Any:
    raw = _stable_read(path, 0o644)
    if _sha(raw) != raw_sha256:
        raise AuthorityError("module raw pin mismatch")
    import types

    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    module.__spec__ = None
    try:
        code = compile(raw, str(path), "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except Exception as exc:
        raise AuthorityError("verified module execution failed") from exc
    if _sha(_stable_read(path, 0o644)) != raw_sha256:
        raise AuthorityError("module changed during load")
    return module


def _load_contracts() -> Any:
    return _load_exact_module(CONTRACTS_PATH, EXPECTED_CONTRACTS_RAW_SHA256, "_v4_contracts")


def _audit_v3_terminal() -> Mapping[str, Any]:
    validator = _load_exact_module(
        V3_TERMINAL_VALIDATOR_PATH,
        EXPECTED_V3_TERMINAL_VALIDATOR_RAW_SHA256,
        "_v3_terminal_validator",
    )
    custody = validator.audit_terminal_custody(WORKSPACE_ROOT)
    if (
        type(custody) is not dict
        or custody.get("v2_preparation_file_count") != 65
        or custody.get("v2_preparation_directory_count") != 20
        or custody.get("v2_capsule", {}).get("file_count") != 53
        or custody.get("v2_capsule", {}).get("directory_count") != 14
        or custody.get("v2_unresolved_null_count") != 172
        or custody.get("v2_open_blocker_count") != 12
        or custody.get("v2_d1_quarantine_row_count") != 550
    ):
        raise AuthorityError("V3/V2 terminal custody mismatch")
    return custody


def _record_common(
    schema: str,
    ordinal: int,
    kind: str,
    marker_raw: bytes,
    marker: Mapping[str, Any],
    registration_raw: bytes,
    previous_kind: str,
    previous_raw: bytes,
    previous_self: str,
    fallback: str,
) -> Dict[str, Any]:
    return {
        "schema_version": schema,
        "event_ordinal": ordinal,
        "event_kind": kind,
        "attempt_id_sha256": marker["attempt_id_sha256"],
        "attempt_nonce_sha256": marker["attempt_nonce_sha256"],
        "registration_record_sha256": marker["registration_record_sha256"],
        "registration_raw_sha256": _sha(registration_raw),
        "marker_raw_sha256": _sha(marker_raw),
        "marker_sha256": marker["marker_sha256"],
        "previous_record_kind": previous_kind,
        "previous_record_raw_sha256": _sha(previous_raw),
        "previous_record_sha256": previous_self,
        "fallback_terminal_state": fallback,
        "retry_permitted": False,
    }


def _make_genesis(
    marker_raw: bytes,
    marker: Mapping[str, Any],
    registration_raw: bytes,
    authorization_raw: bytes,
    authorization: Mapping[str, Any],
) -> Dict[str, Any]:
    return _attach(
        {
            "schema_version": (
                "heterodiff-a1-r1-activation-preparation-v4-ledger-genesis-v1"
            ),
            "attempt_id_sha256": marker["attempt_id_sha256"],
            "attempt_nonce_sha256": marker["attempt_nonce_sha256"],
            "registration_record_sha256": marker["registration_record_sha256"],
            "registration_raw_sha256": _sha(registration_raw),
            "execution_authorization_record_sha256": authorization[
                "record_sha256"
            ],
            "execution_authorization_raw_sha256": _sha(authorization_raw),
            "authorization_context_sha256": AUTHORIZATION_CONTEXT_SHA256,
            "visible_assent_sha256": VISIBLE_ASSENT_SHA256,
            "marker_raw_sha256": _sha(marker_raw),
            "marker_sha256": marker["marker_sha256"],
            "event_count_before_genesis": 0,
            "global_state": GLOBAL_STATE,
            "retry_permitted": False,
        },
        "genesis_sha256",
    )


def _make_event_zero(
    marker_raw: bytes,
    marker: Mapping[str, Any],
    registration_raw: bytes,
    genesis_raw: bytes,
    genesis: Mapping[str, Any],
) -> Dict[str, Any]:
    body = _record_common(
        EVALUATION_CLAIM_SCHEMA,
        0,
        "PRECHILD_EVALUATION_CLAIM",
        marker_raw,
        marker,
        registration_raw,
        "GENESIS",
        genesis_raw,
        genesis["genesis_sha256"],
        (
            "R1_A1_ACTIVATION_PREPARATION_V4_ATTEMPT_SPENT_PRECHILD_"
            "EVALUATION_CLAIMED_TERMINAL_FALLBACK_NO_RETRY"
        ),
    )
    return _attach(body, "event_sha256")


def _prechild_failure_code(gates: Mapping[str, Any]) -> str:
    if type(gates) is not dict or set(gates) != set(PRECHILD_GATE_ORDER):
        raise AuthorityError("prechild gate roster mismatch")
    code_by_gate = dict(zip(PRECHILD_GATE_ORDER, PRECHILD_FAILURE_CODES[1:]))
    for name in PRECHILD_GATE_ORDER:
        if type(gates[name]) is not bool:
            raise AuthorityError("prechild gate type mismatch")
        if not gates[name]:
            return code_by_gate[name]
    return "NONE"


def _make_prechild_event(
    contracts: Optional[Any],
    admitted: bool,
    gates: Mapping[str, bool],
    marker_raw: bytes,
    marker: Mapping[str, Any],
    registration_raw: bytes,
    event_zero_raw: bytes,
    event_zero: Mapping[str, Any],
) -> Dict[str, Any]:
    failure = _prechild_failure_code(gates)
    if contracts is not None:
        if (
            tuple(contracts.PRECHILD_GATE_ORDER) != PRECHILD_GATE_ORDER
            or tuple(contracts.PRECHILD_FAILURE_CODES) != PRECHILD_FAILURE_CODES
            or contracts.prechild_failure_code(gates) != failure
        ):
            raise AuthorityError("contracts prechild priority mismatch")
    if admitted != (failure == "NONE"):
        raise AuthorityError("prechild branch mismatch")
    if admitted:
        schema = PRECHILD_ADMISSION_SCHEMA
        kind = "PRECHILD_ADMISSION"
        fallback = ADMISSION_FALLBACK_STATE
    else:
        schema = PRECHILD_FAILURE_SCHEMA
        kind = "PRECHILD_FAILURE"
        fallback = PRECHILD_FAILURE_STATE
    body = _record_common(
        schema,
        1,
        kind,
        marker_raw,
        marker,
        registration_raw,
        "EVENT",
        event_zero_raw,
        event_zero["event_sha256"],
        fallback,
    )
    body.update(
        {
            "gate_vector": dict(gates),
            "gate_vector_sha256": _sha(_canonical(gates)),
            "failure_code": failure,
            "child_launch_count": 0,
            "runtime_approval_created": False,
            "scientific_execution_performed": False,
        }
    )
    return _attach(body, "event_sha256")


def _make_runtime_request(
    contracts: Any,
    marker: Mapping[str, Any],
    registration_raw: bytes,
    authorization_raw: bytes,
    authorization: Mapping[str, Any],
    admission: Mapping[str, Any],
) -> Dict[str, Any]:
    return contracts.attach_digest(
        {
            "schema_version": contracts.RUNTIME_REQUEST_SCHEMA,
            "attempt_id_sha256": marker["attempt_id_sha256"],
            "attempt_nonce_sha256": marker["attempt_nonce_sha256"],
            "registration_record_sha256": marker["registration_record_sha256"],
            "registration_raw_sha256": _sha(registration_raw),
            "execution_authorization_record_sha256": authorization[
                "record_sha256"
            ],
            "execution_authorization_raw_sha256": _sha(authorization_raw),
            "admission_event_sha256": admission["event_sha256"],
            "child_launch_ordinal": 0,
            "requested_environment_policy_sha256": (
                contracts.REQUESTED_ENVIRONMENT_POLICY_SHA256
            ),
            "expected_profile_sha256": contracts.EXPECTED_PROFILE_SHA256,
            "expected_hash_probe_sha256": contracts.EXPECTED_HASH_PROBE_SHA256,
            "raw_environment_requested": False,
            "network_requested": False,
            "workspace_write_requested": False,
            "temporary_write_requested": False,
            "scientific_import_or_execution_requested": False,
        },
        "request_sha256",
    )


def _make_child_claim(
    contracts: Any,
    marker_raw: bytes,
    marker: Mapping[str, Any],
    registration_raw: bytes,
    admission_raw: bytes,
    admission: Mapping[str, Any],
    request: Mapping[str, Any],
) -> Dict[str, Any]:
    request_raw = contracts.canonical_file_bytes(request)
    body = _record_common(
        contracts.CHILD_CLAIM_SCHEMA,
        2,
        "CHILD_LAUNCH_CLAIM",
        marker_raw,
        marker,
        registration_raw,
        "EVENT",
        admission_raw,
        admission["event_sha256"],
        contracts.CHILD_FALLBACK_STATE,
    )
    body.update(
        {
            "admission_event_raw_sha256": _sha(admission_raw),
            "admission_event_sha256": admission["event_sha256"],
            "runtime_request": dict(request),
            "runtime_request_raw_sha256": _sha(request_raw),
            "runtime_request_sha256": request["request_sha256"],
            "child_launch_ordinal": 0,
            "child_launch_maximum": 1,
        }
    )
    return _attach(body, "event_sha256")


def _make_post_admission_failure(
    contracts: Any,
    failure_code: str,
    marker_raw: bytes,
    marker: Mapping[str, Any],
    registration_raw: bytes,
    admission_raw: bytes,
    admission: Mapping[str, Any],
) -> Dict[str, Any]:
    body = _record_common(
        contracts.POST_ADMISSION_FAILURE_SCHEMA,
        2,
        "POST_ADMISSION_PRECHILD_FAILURE",
        marker_raw,
        marker,
        registration_raw,
        "EVENT",
        admission_raw,
        admission["event_sha256"],
        contracts.POST_ADMISSION_FAILURE_STATE,
    )
    body.update(
        {
            "failure_code": failure_code,
            "child_launch_count": 0,
            "runtime_approval_created": False,
            "scientific_execution_performed": False,
        }
    )
    return _attach(body, "event_sha256")


def _hash_probe() -> str:
    return _sha(_canonical([hash(value) for value in HASH_PROBE_STRINGS]))


def _normalize_darwin_environment(
    genesis_raw: bytes, event_zero_raw: bytes
) -> Tuple[bool, bool]:
    _require_local_prefix(genesis_raw, [event_zero_raw])
    event_zero = _parse_canonical(event_zero_raw)
    if (
        event_zero.get("schema_version") != EVALUATION_CLAIM_SCHEMA
        or event_zero.get("event_ordinal") != 0
        or event_zero.get("event_kind") != "PRECHILD_EVALUATION_CLAIM"
    ):
        raise AuthorityError("live supervisor requires exact event-zero custody")
    captured = dict(os.environ)
    uid = os.getuid()
    injected = captured.get(DARWIN_KEY)
    formula = injected is not None and injected == "0x%X:0x0:0x0" % uid
    if DARWIN_KEY in os.environ:
        del os.environ[DARWIN_KEY]
    normalized = formula and dict(os.environ) == REQUESTED_ENVIRONMENT
    captured.clear()
    return formula, normalized


def _profile_gate_vector(
    contracts: Optional[Any],
    registration_raw: bytes,
    registration: Mapping[str, Any],
    authorization_raw: bytes,
    authorization: Mapping[str, Any],
    prefix_exact: bool,
    genesis_raw: bytes,
    event_zero_raw: bytes,
) -> Dict[str, bool]:
    _require_local_prefix(genesis_raw, [event_zero_raw])
    gates = {name: False for name in PRECHILD_GATE_ORDER}
    try:
        reopened_registration_raw, reopened_registration, reopened_auth_raw, reopened_auth = (
            _load_bootstrap_closure()
        )
        gates["registration_exact"] = (
            reopened_registration_raw == registration_raw
            and reopened_registration == registration
        )
        gates["authorization_certificate_exact"] = (
            reopened_auth_raw == authorization_raw
            and reopened_auth == authorization
        )
    except Exception:
        pass
    try:
        reopened = _audit_v4_source_closure(registration_raw, registration)
        gates["v4_source_closure_exact"] = (
            _sha(reopened["CONTRACTS"]) == EXPECTED_CONTRACTS_RAW_SHA256
            and _sha(reopened["ENVIRONMENT_CHILD"])
            == EXPECTED_RUNTIME_RAW_SHA256
            and contracts is not None
            and tuple(contracts.PRECHILD_GATE_ORDER) == PRECHILD_GATE_ORDER
            and tuple(contracts.PRECHILD_FAILURE_CODES)
            == PRECHILD_FAILURE_CODES
            and contracts.EVALUATION_CLAIM_SCHEMA == EVALUATION_CLAIM_SCHEMA
            and contracts.PRECHILD_FAILURE_SCHEMA == PRECHILD_FAILURE_SCHEMA
            and contracts.PRECHILD_ADMISSION_SCHEMA == PRECHILD_ADMISSION_SCHEMA
        )
    except Exception:
        pass
    try:
        anchor = registration.get("workspace_anchor")
        root_status = WORKSPACE_ROOT.lstat()
        actual_anchor = {
            "device": root_status.st_dev,
            "inode": root_status.st_ino,
            "type_code": "DIRECTORY" if stat.S_ISDIR(root_status.st_mode) else "OTHER",
            "mode_octal": format(stat.S_IMODE(root_status.st_mode), "04o"),
            "uid": root_status.st_uid,
            "gid": root_status.st_gid,
        }
        gates["canonical_workspace_anchor_exact"] = (
            type(anchor) is dict
            and anchor == actual_anchor
            and not stat.S_ISLNK(root_status.st_mode)
            and WORKSPACE_ROOT.resolve(strict=True) == WORKSPACE_ROOT
        )
    except Exception:
        pass
    try:
        custody = _audit_v3_terminal()
        gates["v3_terminal_registration_exact"] = True
        gates["v3_terminal_custody_exact"] = True
        gates["v3_attempt_count_one_retry_count_zero"] = True
        gates["v2_terminal_custody_exact"] = (
            custody["v2_preparation_file_count"] == 65
            and custody["v2_preparation_directory_count"] == 20
        )
    except Exception:
        pass
    v3_absence_paths = (
        WORKSPACE_ROOT / "artifacts/a1_r1_activation_preparation_v3.attempt.json",
        WORKSPACE_ROOT / "artifacts/a1_r1_activation_preparation_v3",
        WORKSPACE_ROOT
        / (
            "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v3_"
            "live_host_environment_rehearsal_result_v1.json"
        ),
    )
    try:
        gates["v3_spent_namespace_absent"] = all(
            _lstat(path) is None for path in v3_absence_paths
        )
    except Exception:
        pass
    gates["v4_closed_world_prefix_exact"] = type(prefix_exact) is bool and prefix_exact
    try:
        gates["canonical_cwd_exact"] = (
            Path.cwd().absolute() == WORKSPACE_ROOT
            and Path.cwd().resolve(strict=True) == WORKSPACE_ROOT
        )
    except Exception:
        pass
    try:
        effective_count_before = len(os.environ)
        formula, normalized = _normalize_darwin_environment(
            genesis_raw, event_zero_raw
        )
        gates["requested_environment_exact"] = normalized
        gates["darwin_environment_normalized"] = (
            effective_count_before == 17 and formula and normalized
        )
    except Exception:
        pass
    try:
        ids = (os.getuid(), os.geteuid(), os.getgid(), os.getegid())
        if sys.platform == "darwin":
            import ctypes

            issetugid = ctypes.CDLL(None).issetugid
            issetugid.restype = ctypes.c_int
            untainted = issetugid() == 0
        else:
            untainted = False
        gates["identity_nonprivileged_exact"] = (
            ids[0] == ids[1]
            and ids[2] == ids[3]
            and ids[0] != 0
            and ids[2] != 0
            and 0 not in os.getgroups()
            and untainted
        )
    except Exception:
        pass
    try:
        gates["cpython_3_11_5_exact"] = (
            sys.implementation.name == "cpython"
            and list(sys.version_info[:3]) == [3, 11, 5]
        )
    except Exception:
        pass
    try:
        uname = os.uname()
        gates["darwin_arm64_exact"] = [uname.sysname, uname.machine] == [
            "Darwin",
            "arm64",
        ]
    except Exception:
        pass
    try:
        gates["python_flags_exact"] = {
            "dont_write_bytecode": int(sys.dont_write_bytecode),
            "hash_randomization": getattr(sys.flags, "hash_randomization", -1),
            "ignore_environment": getattr(sys.flags, "ignore_environment", -1),
            "isolated": getattr(sys.flags, "isolated", -1),
            "no_site": getattr(sys.flags, "no_site", -1),
            "no_user_site": getattr(sys.flags, "no_user_site", -1),
            "safe_path": bool(getattr(sys.flags, "safe_path", False)),
            "utf8_mode": getattr(sys.flags, "utf8_mode", -1),
            "pycache_prefix_is_dev_null": getattr(sys, "pycache_prefix", None)
            == "/dev/null",
        } == {
            "dont_write_bytecode": 1,
            "hash_randomization": 0,
            "ignore_environment": 0,
            "isolated": 0,
            "no_site": 1,
            "no_user_site": 1,
            "safe_path": True,
            "utf8_mode": 1,
            "pycache_prefix_is_dev_null": True,
        }
    except Exception:
        pass
    try:
        gates["hash_probe_matches_prefrozen_reference"] = (
            _hash_probe() == HASH_PROBE_SHA256
        )
    except Exception:
        pass
    try:
        gates["system_only_sys_path_exact"] = list(sys.path) == [
            "/Library/Frameworks/Python.framework/Versions/3.11/lib/python311.zip",
            "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11",
            "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/lib-dynload",
        ]
    except Exception:
        pass
    try:
        gates["site_module_absent"] = "site" not in sys.modules
    except Exception:
        pass
    try:
        native = _native_argv()
        expected_tail = (*PYTHON_FLAGS, str(AUTHORITY_RELATIVE_PATH), "--execute-once")
        executable = Path(sys.executable)
        gates["native_argv_structural_tail_exact"] = (
            len(native) == len(expected_tail) + 1
            and type(native[0]) is str
            and bool(native[0])
            and Path(native[0]).is_absolute()
            and native[1:] == expected_tail
            and executable == PYTHON_PATH
            and executable.resolve(strict=True) == PYTHON_REALPATH
        )
    except Exception:
        pass
    try:
        gates["application_effects_absent"] = (
            type(_APPLICATION_EFFECTS) is dict
            and set(_APPLICATION_EFFECTS)
            == {
                "explicit_entropy_api_calls",
                "explicit_network_api_calls",
                "scientific_import_or_execution_calls",
                "temporary_output_writes",
                "unregistered_workspace_writes",
                "raw_environment_emissions",
                "raw_identity_emissions",
                "raw_path_or_argv_emissions",
            }
            and all(type(value) is int and value == 0 for value in _APPLICATION_EFFECTS.values())
        )
    except Exception:
        pass
    return gates


class SyntheticStateRoot:
    """A read-only, non-live capability for isolated transition fixtures."""

    __slots__ = ("path",)

    def __init__(self, path: Path) -> None:
        candidate = _lexically_normal_absolute(Path(path).absolute())
        status = candidate.lstat()
        if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
            raise AuthorityError("synthetic state root is not a real directory")
        resolved = candidate.resolve(strict=True)
        if resolved != candidate:
            raise AuthorityError("synthetic state root contains an alias")
        try:
            resolved.relative_to(WORKSPACE_ROOT)
        except ValueError:
            pass
        else:
            raise AuthorityError("synthetic state root overlaps canonical workspace")
        try:
            WORKSPACE_ROOT.relative_to(resolved)
        except ValueError:
            pass
        else:
            raise AuthorityError("synthetic state root contains canonical workspace")
        self.path = candidate


def _operational_paths(root: Path) -> Dict[str, Path]:
    return {
        "authorization": root
        / (
            "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
            "execution_authorization_v1.json"
        ),
        "marker": root / "artifacts/a1_r1_activation_preparation_v4.attempt.json",
        "root": root / "artifacts/a1_r1_activation_preparation_v4",
        "ledger": root / "artifacts/a1_r1_activation_preparation_v4/ledger",
        "events": root / "artifacts/a1_r1_activation_preparation_v4/ledger/events",
        "lock": root / "artifacts/a1_r1_activation_preparation_v4/ledger/writer.lock",
        "genesis": root / "artifacts/a1_r1_activation_preparation_v4/ledger/genesis.json",
        "terminal": root / "artifacts/a1_r1_activation_preparation_v4/ledger/terminal.json",
        "result": root
        / (
            "research/fixtures/manuscript_v3_a1_r1_activation_preparation_v4_"
            "transition_safe_live_host_environment_rehearsal_result_v1.json"
        ),
    }


def _stable_directory_names(
    path: Path, mode: int, ancestry_stop: Optional[Path] = None
) -> Tuple[str, ...]:
    ancestors = _ancestor_snapshot(path / "sentinel", ancestry_stop)
    before_path = path.lstat()
    if (
        not stat.S_ISDIR(before_path.st_mode)
        or stat.S_ISLNK(before_path.st_mode)
        or stat.S_IMODE(before_path.st_mode) != mode
    ):
        raise AuthorityError("directory roster custody invalid")
    descriptor = os.open(
        str(path),
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        before_fd = os.fstat(descriptor)
        if _leaf_identity(before_fd) != _leaf_identity(before_path):
            raise AuthorityError("directory roster descriptor mismatch")
        names = os.listdir(descriptor)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = path.lstat()
    if (
        any(type(name) is not str or not name or "/" in name for name in names)
        or len(names) != len(set(names))
        or _leaf_identity(before_fd) != _leaf_identity(after_fd)
        or _leaf_identity(after_fd) != _leaf_identity(after_path)
    ):
        raise AuthorityError("directory roster changed during scan")
    _require_ancestors(ancestors)
    return tuple(sorted(names))


def _prefix_summary(
    state: str,
    event_count: int,
    terminal_present: bool,
    result_present: bool,
    result_exact: bool,
    *,
    terminal_exact: bool = False,
    trailing_record_invalid_or_incomplete_kind: Optional[str] = None,
    trailing_record_invalid_or_incomplete_event_ordinal: Optional[int] = None,
    adjunct_error_code: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "milestone_state": state,
        "event_count": event_count,
        "event_count_directly_validated": True,
        "authoritative_typed_event_present": event_count > 0,
        "local_terminal_projection_present": terminal_present,
        "local_terminal_projection_exact": terminal_exact,
        "external_result_present": result_present,
        "external_result_exact": result_exact,
        "trailing_record_invalid_or_incomplete_kind": (
            trailing_record_invalid_or_incomplete_kind
        ),
        "trailing_record_invalid_or_incomplete_event_ordinal": (
            trailing_record_invalid_or_incomplete_event_ordinal
        ),
        "trailing_record_cause_unobserved": (
            trailing_record_invalid_or_incomplete_kind is not None
        ),
        "adjunct_error_code": adjunct_error_code,
    }


def _scan_valid_prefix(
    contracts: Any,
    paths: Mapping[str, Path],
    ancestry_stop: Path,
    registration_raw: bytes,
    registration: Mapping[str, Any],
    authorization: Mapping[str, Any],
    marker_raw: bytes,
    marker: Mapping[str, Any],
) -> Dict[str, Any]:
    contracts.validate_marker(
        marker,
        authorization,
        registration["record_sha256"],
        _sha(registration_raw),
    )
    root_status = _lstat(paths["root"])
    result_present = _lstat(paths["result"]) is not None
    if root_status is None:
        if result_present:
            raise AuthorityError("result exists without a local ledger")
        if _lstat(paths["root"]) is not None or _lstat(paths["result"]) is not None:
            raise AuthorityError("marker-only roster changed during scan")
        return _prefix_summary(MARKER_FALLBACK_STATE, 0, False, False, False)
    root_names = _stable_directory_names(paths["root"], 0o700, ancestry_stop)
    if root_names == ():
        if result_present:
            raise AuthorityError("result exists before a ledger")
        if (
            _stable_directory_names(paths["root"], 0o700, ancestry_stop) != root_names
            or (_lstat(paths["result"]) is not None) != result_present
        ):
            raise AuthorityError("root-only roster changed during scan")
        return _prefix_summary(MARKER_FALLBACK_STATE, 0, False, False, False)
    if root_names != ("ledger",):
        raise AuthorityError("preparation root closed-world roster invalid")
    ledger_names = _stable_directory_names(paths["ledger"], 0o700, ancestry_stop)
    allowed_ledger = {"events", "writer.lock", "genesis.json", "terminal.json"}
    if not set(ledger_names).issubset(allowed_ledger):
        raise AuthorityError("ledger closed-world roster invalid")
    if "events" not in ledger_names:
        if ledger_names or result_present:
            raise AuthorityError("ledger prefix order invalid before events directory")
        if (
            _stable_directory_names(paths["root"], 0o700, ancestry_stop) != root_names
            or _stable_directory_names(paths["ledger"], 0o700, ancestry_stop)
            != ledger_names
            or (_lstat(paths["result"]) is not None) != result_present
        ):
            raise AuthorityError("pre-events roster changed during scan")
        return _prefix_summary(MARKER_FALLBACK_STATE, 0, False, False, False)
    event_names = _stable_directory_names(paths["events"], 0o700, ancestry_stop)
    if "writer.lock" not in ledger_names:
        if event_names or set(ledger_names) != {"events"} or result_present:
            raise AuthorityError("ledger prefix order invalid before writer lock")
        if (
            _stable_directory_names(paths["root"], 0o700, ancestry_stop) != root_names
            or _stable_directory_names(paths["ledger"], 0o700, ancestry_stop)
            != ledger_names
            or _stable_directory_names(paths["events"], 0o700, ancestry_stop)
            != event_names
            or (_lstat(paths["result"]) is not None) != result_present
        ):
            raise AuthorityError("pre-lock roster changed during scan")
        return _prefix_summary(MARKER_FALLBACK_STATE, 0, False, False, False)
    if _stable_read(paths["lock"], 0o600, ancestry_stop=ancestry_stop) != b"":
        raise AuthorityError("writer lock content is not empty")
    if "genesis.json" not in ledger_names:
        if event_names or "terminal.json" in ledger_names or result_present:
            raise AuthorityError("ledger prefix order invalid before genesis")
        if (
            _stable_directory_names(paths["root"], 0o700, ancestry_stop) != root_names
            or _stable_directory_names(paths["ledger"], 0o700, ancestry_stop)
            != ledger_names
            or _stable_directory_names(paths["events"], 0o700, ancestry_stop)
            != event_names
            or (_lstat(paths["result"]) is not None) != result_present
        ):
            raise AuthorityError("pre-genesis roster changed during scan")
        return _prefix_summary(MARKER_FALLBACK_STATE, 0, False, False, False)
    expected_event_names = tuple(
        f"{ordinal:020d}.json" for ordinal in range(len(event_names))
    )
    if event_names != expected_event_names or len(event_names) > 4:
        raise AuthorityError("event roster is not a contiguous frozen prefix")
    genesis_raw = _stable_read(
        paths["genesis"], 0o600, ancestry_stop=ancestry_stop
    )
    try:
        genesis = _parse_canonical(genesis_raw)
    except AuthorityError:
        if event_names or "terminal.json" in ledger_names or result_present:
            raise AuthorityError("noncanonical genesis is not a trailing write")
        if (
            _stable_directory_names(paths["root"], 0o700, ancestry_stop) != root_names
            or _stable_directory_names(paths["ledger"], 0o700, ancestry_stop)
            != ledger_names
            or _stable_directory_names(paths["events"], 0o700, ancestry_stop)
            != event_names
            or _lstat(paths["result"]) is not None
        ):
            raise AuthorityError("torn genesis roster changed during scan")
        return _prefix_summary(
            MARKER_FALLBACK_STATE,
            0,
            False,
            False,
            False,
            trailing_record_invalid_or_incomplete_kind="GENESIS",
        )
    events: List[Dict[str, Any]] = []
    event_raws: List[bytes] = []
    prefix = contracts.validate_full_prefix(
        marker,
        marker_raw,
        authorization,
        registration["record_sha256"],
        _sha(registration_raw),
        genesis,
        genesis_raw,
        events,
        event_raws,
    )
    for ordinal, name in enumerate(event_names):
        raw = _stable_read(
            paths["events"] / name, 0o600, ancestry_stop=ancestry_stop
        )
        try:
            event = _parse_canonical(raw)
        except AuthorityError:
            if (
                ordinal != len(event_names) - 1
                or "terminal.json" in ledger_names
                or result_present
            ):
                raise AuthorityError("noncanonical event is not a trailing write")
            if (
                _stable_directory_names(paths["root"], 0o700, ancestry_stop)
                != root_names
                or _stable_directory_names(paths["ledger"], 0o700, ancestry_stop)
                != ledger_names
                or _stable_directory_names(paths["events"], 0o700, ancestry_stop)
                != event_names
                or _lstat(paths["result"]) is not None
            ):
                raise AuthorityError("torn event roster changed during scan")
            return _prefix_summary(
                prefix["expected_terminal_state"],
                len(events),
                False,
                False,
                False,
                trailing_record_invalid_or_incomplete_kind="EVENT",
                trailing_record_invalid_or_incomplete_event_ordinal=ordinal,
            )
        event_raws.append(raw)
        events.append(event)
        prefix = contracts.validate_full_prefix(
            marker,
            marker_raw,
            authorization,
            registration["record_sha256"],
            _sha(registration_raw),
            genesis,
            genesis_raw,
            events,
            event_raws,
        )
    terminal_present = "terminal.json" in ledger_names
    terminal_raw: Optional[bytes] = None
    terminal: Optional[Dict[str, Any]] = None
    terminal_observed_raw: Optional[bytes] = None
    terminal_exact = False
    adjunct_error: Optional[str] = None
    if terminal_present:
        try:
            terminal_observed_raw = _stable_read(
                paths["terminal"], 0o600, ancestry_stop=ancestry_stop
            )
            terminal_raw = terminal_observed_raw
            terminal = _parse_canonical(terminal_raw)
            contracts.validate_full_prefix(
                marker,
                marker_raw,
                authorization,
                registration["record_sha256"],
                _sha(registration_raw),
                genesis,
                genesis_raw,
                events,
                event_raws,
                terminal,
                terminal_raw,
            )
            terminal_exact = True
        except Exception:
            terminal_raw = None
            terminal = None
            adjunct_error = "LOCAL_TERMINAL_PROJECTION_INVALID"
    result_exact = False
    result_observed_raw: Optional[bytes] = None
    if result_present:
        if not terminal_exact or terminal is None or terminal_raw is None:
            adjunct_error = adjunct_error or "RESULT_WITHOUT_EXACT_LOCAL_TERMINAL"
        else:
            try:
                result_observed_raw = _stable_read(
                    paths["result"], 0o644, ancestry_stop=ancestry_stop
                )
                result_raw = result_observed_raw
                result = _parse_canonical(result_raw)
                contracts.validate_published_result_against_full_prefix(
                    result,
                    marker,
                    marker_raw,
                    authorization,
                    registration["record_sha256"],
                    _sha(registration_raw),
                    genesis,
                    genesis_raw,
                    events,
                    event_raws,
                    terminal,
                    terminal_raw,
                )
                result_exact = result_raw == contracts.canonical_file_bytes(result)
            except Exception:
                adjunct_error = "EXTERNAL_RESULT_INVALID"
    if (
        _stable_directory_names(paths["root"], 0o700, ancestry_stop) != root_names
        or _stable_directory_names(paths["ledger"], 0o700, ancestry_stop)
        != ledger_names
        or _stable_directory_names(paths["events"], 0o700, ancestry_stop)
        != event_names
        or (_lstat(paths["result"]) is not None) != result_present
    ):
        raise AuthorityError("closed-world roster changed during full scan")
    if (
        _stable_read(paths["marker"], 0o600, ancestry_stop=ancestry_stop)
        != marker_raw
        or _stable_read(MACHINE_PATH, 0o644) != registration_raw
        or _stable_read(paths["authorization"], 0o644, ancestry_stop=ancestry_stop)
        != _file_bytes(authorization)
        or _stable_read(paths["lock"], 0o600, ancestry_stop=ancestry_stop) != b""
        or _stable_read(paths["genesis"], 0o600, ancestry_stop=ancestry_stop)
        != genesis_raw
        or any(
            _stable_read(
                paths["events"] / name,
                0o600,
                ancestry_stop=ancestry_stop,
            )
            != raw
            for name, raw in zip(event_names, event_raws)
        )
    ):
        raise AuthorityError("authoritative prefix bytes changed during scan")
    if terminal_exact and (
        terminal_observed_raw is None
        or _stable_read(paths["terminal"], 0o600, ancestry_stop=ancestry_stop)
        != terminal_observed_raw
    ):
        raise AuthorityError("exact terminal projection changed during scan")
    if result_exact and (
        result_observed_raw is None
        or _stable_read(paths["result"], 0o644, ancestry_stop=ancestry_stop)
        != result_observed_raw
    ):
        raise AuthorityError("exact external result changed during scan")
    return _prefix_summary(
        prefix["expected_terminal_state"],
        len(events),
        terminal_present,
        result_present,
        result_exact,
        terminal_exact=terminal_exact,
        adjunct_error_code=adjunct_error,
    )


def _recover_longest_valid_prefix(
    contracts: Any,
    paths: Mapping[str, Path],
    ancestry_stop: Path,
    registration_raw: bytes,
    registration: Mapping[str, Any],
    authorization: Mapping[str, Any],
    marker_raw: bytes,
    marker: Mapping[str, Any],
) -> Dict[str, Any]:
    """Conservatively preserve only the contiguous typed prefix already proved."""

    result_present = _lstat(paths["result"]) is not None
    terminal_present = _lstat(paths["terminal"]) is not None
    summary = _prefix_summary(
        MARKER_FALLBACK_STATE,
        0,
        terminal_present,
        result_present,
        False,
        adjunct_error_code="CLOSED_WORLD_INVALID_AFTER_LONGEST_PREFIX",
    )
    try:
        genesis_raw, genesis = _read_record(
            paths["genesis"], 0o600, ancestry_stop=ancestry_stop
        )
        events: List[Dict[str, Any]] = []
        event_raws: List[bytes] = []
        prefix = contracts.validate_full_prefix(
            marker,
            marker_raw,
            authorization,
            registration["record_sha256"],
            _sha(registration_raw),
            genesis,
            genesis_raw,
            events,
            event_raws,
        )
        summary = _prefix_summary(
            prefix["expected_terminal_state"],
            0,
            terminal_present,
            result_present,
            False,
            adjunct_error_code="CLOSED_WORLD_INVALID_AFTER_LONGEST_PREFIX",
        )
        for ordinal in range(4):
            path = paths["events"] / f"{ordinal:020d}.json"
            if _lstat(path) is None:
                break
            raw, event = _read_record(path, 0o600, ancestry_stop=ancestry_stop)
            candidate_events = [*events, event]
            candidate_raws = [*event_raws, raw]
            candidate = contracts.validate_full_prefix(
                marker,
                marker_raw,
                authorization,
                registration["record_sha256"],
                _sha(registration_raw),
                genesis,
                genesis_raw,
                candidate_events,
                candidate_raws,
            )
            events = candidate_events
            event_raws = candidate_raws
            prefix = candidate
            summary = _prefix_summary(
                prefix["expected_terminal_state"],
                len(events),
                terminal_present,
                result_present,
                False,
                adjunct_error_code="CLOSED_WORLD_INVALID_AFTER_LONGEST_PREFIX",
            )
    except Exception:
        pass
    return summary


def _status_record(
    state: str,
    *,
    registration_record_exact: bool,
    authorization_present: bool,
    authorization_exact: bool,
    marker_present: bool,
    marker_raw_observed: bool,
    marker_self_valid: bool,
    preparation_root_present: bool,
    summary: Optional[Mapping[str, Any]],
    invalid_reason_code: Optional[str],
) -> Dict[str, Any]:
    if summary is None:
        event_count = None
        event_count_validated = False
        typed_event = False
        terminal_present = False
        terminal_exact = False
        result_present = False
        result_exact = False
        last_valid_prefix_state = None
        trailing_record_kind = None
        trailing_record_ordinal = None
        trailing_record_cause_unobserved = False
        adjunct_error_code = None
    else:
        event_count = summary["event_count"]
        event_count_validated = summary["event_count_directly_validated"]
        typed_event = summary["authoritative_typed_event_present"]
        terminal_present = summary["local_terminal_projection_present"]
        terminal_exact = summary["local_terminal_projection_exact"]
        result_present = summary["external_result_present"]
        result_exact = summary["external_result_exact"]
        last_valid_prefix_state = summary["milestone_state"]
        trailing_record_kind = summary[
            "trailing_record_invalid_or_incomplete_kind"
        ]
        trailing_record_ordinal = summary[
            "trailing_record_invalid_or_incomplete_event_ordinal"
        ]
        trailing_record_cause_unobserved = summary[
            "trailing_record_cause_unobserved"
        ]
        adjunct_error_code = summary["adjunct_error_code"]
    return _attach(
        {
            "schema_version": STATUS_SCHEMA,
            "global_state": GLOBAL_STATE,
            "milestone_state": state,
            "status_source": "FULL_READ_ONLY_CLOSED_WORLD_RECONSTRUCTION",
            "registration_record_exact": registration_record_exact,
            "source_closure_evaluated_by_status": False,
            "source_closure_exact_claimed_by_status": False,
            "authorization_record_present": authorization_present,
            "authorization_record_exact": authorization_exact,
            "marker_present": marker_present,
            "marker_raw_observed": marker_raw_observed,
            "marker_self_valid": marker_self_valid,
            "preparation_root_present": preparation_root_present,
            "attempt_spent": marker_present,
            "event_count": event_count,
            "event_count_directly_validated": event_count_validated,
            "authoritative_typed_event_present": typed_event,
            "local_terminal_projection_present": terminal_present,
            "local_terminal_projection_exact": terminal_exact,
            "external_result_present": result_present,
            "external_result_exact": result_exact,
            "last_valid_prefix_state": last_valid_prefix_state,
            "trailing_record_invalid_or_incomplete_kind": trailing_record_kind,
            "trailing_record_invalid_or_incomplete_event_ordinal": (
                trailing_record_ordinal
            ),
            "trailing_record_cause_unobserved": trailing_record_cause_unobserved,
            "adjunct_error_code": adjunct_error_code,
            "invalid_reason_code": invalid_reason_code,
            "live_rehearsal_authorized_by_certificate": (
                state == AUTH_RECORDED_STATE
            ),
            "prechild_admission_ready_claimed": False,
            "retry_permitted": False,
            "runtime_approval_created": False,
            "scientific_execution_authorized": False,
            "scientific_execution_performed": False,
        },
        "status_sha256",
    )


def status(synthetic_root: Optional[SyntheticStateRoot] = None) -> Dict[str, Any]:
    """Reconstruct the canonical or isolated-fixture state without writing."""

    if synthetic_root is not None and type(synthetic_root) is not SyntheticStateRoot:
        raise AuthorityError("synthetic status requires its dedicated capability")
    root = WORKSPACE_ROOT if synthetic_root is None else synthetic_root.path
    paths = _operational_paths(root)
    boundary = WORKSPACE_ROOT.parent if synthetic_root is None else root.parent
    try:
        registration_raw, registration = _load_registration()
    except Exception:
        return _status_record(
            INVALID_STATE,
            registration_record_exact=False,
            authorization_present=_lstat(paths["authorization"]) is not None,
            authorization_exact=False,
            marker_present=_lstat(paths["marker"]) is not None,
            marker_raw_observed=False,
            marker_self_valid=False,
            preparation_root_present=_lstat(paths["root"]) is not None,
            summary=None,
            invalid_reason_code="STATIC_REGISTRATION_INVALID",
        )
    auth_present = _lstat(paths["authorization"]) is not None
    marker_present = _lstat(paths["marker"]) is not None
    root_present = _lstat(paths["root"]) is not None
    result_present = _lstat(paths["result"]) is not None
    if not auth_present:
        if marker_present or root_present or result_present:
            return _status_record(
                INVALID_STATE,
                registration_record_exact=True,
                authorization_present=False,
                authorization_exact=False,
                marker_present=marker_present,
                marker_raw_observed=False,
                marker_self_valid=False,
                preparation_root_present=root_present,
                summary=None,
                invalid_reason_code="OPERATIONAL_STATE_WITHOUT_AUTHORIZATION",
            )
        return _status_record(
            STATIC_STATE,
            registration_record_exact=True,
            authorization_present=False,
            authorization_exact=False,
            marker_present=False,
            marker_raw_observed=False,
            marker_self_valid=False,
            preparation_root_present=False,
            summary=_prefix_summary(STATIC_STATE, 0, False, False, False),
            invalid_reason_code=None,
        )
    try:
        authorization_raw, authorization = _load_authorization_anchor_at(
            paths["authorization"], boundary
        )
        if (
            authorization["v4_registration_record_sha256"]
            != registration["record_sha256"]
            or authorization["v4_registration_raw_sha256"]
            != _sha(registration_raw)
        ):
            raise AuthorityError("authorization registration link mismatch")
    except Exception:
        return _status_record(
            INVALID_STATE,
            registration_record_exact=True,
            authorization_present=True,
            authorization_exact=False,
            marker_present=marker_present,
            marker_raw_observed=False,
            marker_self_valid=False,
            preparation_root_present=root_present,
            summary=None,
            invalid_reason_code="AUTHORIZATION_RECORD_INVALID",
        )
    if not marker_present:
        if root_present or result_present:
            return _status_record(
                INVALID_STATE,
                registration_record_exact=True,
                authorization_present=True,
                authorization_exact=True,
                marker_present=False,
                marker_raw_observed=False,
                marker_self_valid=False,
                preparation_root_present=root_present,
                summary=None,
                invalid_reason_code="OPERATIONAL_STATE_WITHOUT_MARKER",
            )
        return _status_record(
            AUTH_RECORDED_STATE,
            registration_record_exact=True,
            authorization_present=True,
            authorization_exact=True,
            marker_present=False,
            marker_raw_observed=False,
            marker_self_valid=False,
            preparation_root_present=False,
            summary=_prefix_summary(AUTH_RECORDED_STATE, 0, False, False, False),
            invalid_reason_code=None,
        )
    marker_raw_observed = False
    marker_self_valid = False
    contracts: Optional[Any] = None
    try:
        marker_raw = _stable_read(
            paths["marker"], 0o600, ancestry_stop=boundary
        )
        marker_raw_observed = True
        marker = _parse_canonical(marker_raw)
        if not _record_self_exact(marker, "marker_sha256"):
            raise AuthorityError("marker self digest invalid")
        expected_marker = _make_marker(
            registration_raw,
            registration,
            authorization_raw,
            authorization,
        )
        if marker != expected_marker or marker_raw != _file_bytes(expected_marker):
            raise AuthorityError("marker does not match frozen local construction")
        marker_self_valid = True
    except Exception:
        return _status_record(
            INVALID_STATE,
            registration_record_exact=True,
            authorization_present=True,
            authorization_exact=True,
            marker_present=True,
            marker_raw_observed=marker_raw_observed,
            marker_self_valid=marker_self_valid,
            preparation_root_present=root_present,
            summary=None,
            invalid_reason_code="MARKER_INVALID",
        )
    try:
        contracts = _load_contracts()
        contracts.validate_marker(
            marker,
            authorization,
            registration["record_sha256"],
            _sha(registration_raw),
        )
    except Exception:
        # Validator/source loss cannot erase the independently reopened marker
        # spend.  No source/profile reevaluation is attempted by read-only status.
        summary = _prefix_summary(
            MARKER_FALLBACK_STATE,
            0,
            _lstat(paths["terminal"]) is not None,
            result_present,
            False,
            adjunct_error_code="VALIDATOR_UNAVAILABLE",
        )
        return _status_record(
            INVALID_STATE,
            registration_record_exact=True,
            authorization_present=True,
            authorization_exact=True,
            marker_present=True,
            marker_raw_observed=True,
            marker_self_valid=True,
            preparation_root_present=root_present,
            summary=summary,
            invalid_reason_code="VALIDATOR_UNAVAILABLE",
        )
    try:
        summary = _scan_valid_prefix(
            contracts,
            paths,
            boundary,
            registration_raw,
            registration,
            authorization,
            marker_raw,
            marker,
        )
    except Exception:
        recovered = _recover_longest_valid_prefix(
            contracts,
            paths,
            boundary,
            registration_raw,
            registration,
            authorization,
            marker_raw,
            marker,
        )
        return _status_record(
            INVALID_STATE,
            registration_record_exact=True,
            authorization_present=True,
            authorization_exact=True,
            marker_present=True,
            marker_raw_observed=marker_raw_observed,
            marker_self_valid=True,
            preparation_root_present=root_present,
            summary=recovered,
            invalid_reason_code="LEDGER_CLOSED_WORLD_INVALID",
        )
    return _status_record(
        summary["milestone_state"],
        registration_record_exact=True,
        authorization_present=True,
        authorization_exact=True,
        marker_present=True,
        marker_raw_observed=True,
        marker_self_valid=True,
        preparation_root_present=root_present,
        summary=summary,
        invalid_reason_code=None,
    )


def _event_path(ordinal: int) -> Path:
    if type(ordinal) is not int or ordinal not in range(4):
        raise AuthorityError("event ordinal outside frozen range")
    return EVENTS_PATH / f"{ordinal:020d}.json"


def _require_pre_genesis_prefix() -> None:
    _require_live_write_scope()
    if (
        _stable_directory_names(PREPARATION_ROOT, 0o700) != ("ledger",)
        or _stable_directory_names(LEDGER_PATH, 0o700)
        != ("events", "writer.lock")
        or _stable_directory_names(EVENTS_PATH, 0o700) != ()
        or _stable_read(LOCK_PATH, 0o600) != b""
        or _lstat(GENESIS_PATH) is not None
        or _lstat(TERMINAL_PATH) is not None
        or _lstat(RESULT_PATH) is not None
    ):
        raise AuthorityError("pre-genesis live prefix is not exact")


def _require_local_prefix(
    genesis_raw: bytes,
    event_raws: Sequence[bytes],
    terminal_raw: Optional[bytes] = None,
    result_raw: Optional[bytes] = None,
) -> None:
    _require_live_write_scope(expected_result_raw=result_raw)
    if type(genesis_raw) is not bytes or type(event_raws) not in (list, tuple):
        raise AuthorityError("local prefix inputs invalid")
    expected_event_names = tuple(
        f"{ordinal:020d}.json" for ordinal in range(len(event_raws))
    )
    expected_ledger_names = ["events", "genesis.json", "writer.lock"]
    if terminal_raw is not None:
        expected_ledger_names.append("terminal.json")
    expected_ledger = tuple(sorted(expected_ledger_names))
    if (
        _stable_directory_names(PREPARATION_ROOT, 0o700) != ("ledger",)
        or _stable_directory_names(LEDGER_PATH, 0o700) != expected_ledger
        or _stable_directory_names(EVENTS_PATH, 0o700) != expected_event_names
        or _stable_read(LOCK_PATH, 0o600) != b""
        or _stable_read(GENESIS_PATH, 0o600) != genesis_raw
        or any(
            _stable_read(_event_path(ordinal), 0o600) != raw
            for ordinal, raw in enumerate(event_raws)
        )
        or (
            terminal_raw is None
            and _lstat(TERMINAL_PATH) is not None
        )
        or (
            terminal_raw is not None
            and _stable_read(TERMINAL_PATH, 0o600) != terminal_raw
        )
        or (
            result_raw is None
            and _lstat(RESULT_PATH) is not None
        )
        or (
            result_raw is not None
            and _stable_read(RESULT_PATH, 0o644) != result_raw
        )
    ):
        raise AuthorityError("local authoritative prefix is not exact")
    if (
        _stable_directory_names(PREPARATION_ROOT, 0o700) != ("ledger",)
        or _stable_directory_names(LEDGER_PATH, 0o700) != expected_ledger
        or _stable_directory_names(EVENTS_PATH, 0o700) != expected_event_names
        or (
            terminal_raw is not None
            and _stable_read(TERMINAL_PATH, 0o600) != terminal_raw
        )
        or (
            result_raw is not None
            and _stable_read(RESULT_PATH, 0o644) != result_raw
        )
    ):
        raise AuthorityError("local prefix roster changed during reopen")


def _make_terminal_projection(
    marker_raw: bytes,
    marker: Mapping[str, Any],
    registration_raw: bytes,
    authoritative_event_raw: Optional[bytes],
    authoritative_event: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    if authoritative_event is None:
        if authoritative_event_raw is not None:
            raise AuthorityError("marker projection cannot carry event bytes")
        state = MARKER_FALLBACK_STATE
        outcome = "INCOMPLETE"
        event_ordinal = None
        event_schema = None
        event_kind = None
        event_raw_sha = None
        event_self = None
        typed = False
        inferred = True
        child_claims = 0
        child_processes: Optional[int] = 0
        process_count_observed = True
    else:
        if type(authoritative_event) is not dict or type(authoritative_event_raw) is not bytes:
            raise AuthorityError("terminal projection event input invalid")
        schema = authoritative_event["schema_version"]
        table = {
            EVALUATION_CLAIM_SCHEMA: (
                EVALUATION_FALLBACK_STATE,
                "INCOMPLETE",
                True,
                0,
                0,
                True,
            ),
            PRECHILD_FAILURE_SCHEMA: (
                PRECHILD_FAILURE_STATE,
                "FAIL",
                False,
                0,
                0,
                True,
            ),
            PRECHILD_ADMISSION_SCHEMA: (
                ADMISSION_FALLBACK_STATE,
                "INCOMPLETE",
                True,
                0,
                0,
                True,
            ),
            POST_ADMISSION_FAILURE_SCHEMA: (
                POST_ADMISSION_FAILURE_STATE,
                "FAIL",
                False,
                0,
                0,
                True,
            ),
            CHILD_CLAIM_SCHEMA: (
                CHILD_FALLBACK_STATE,
                "INCOMPLETE",
                True,
                1,
                None,
                False,
            ),
        }
        if schema == TERMINAL_OUTCOME_SCHEMA:
            state = authoritative_event["terminal_state"]
            outcome = authoritative_event["outcome"]
            inferred = False
            child_claims = authoritative_event["child_launch_claim_count"]
            child_processes = authoritative_event["child_process_start_count"]
            process_count_observed = True
        elif schema in table:
            (
                state,
                outcome,
                inferred,
                child_claims,
                child_processes,
                process_count_observed,
            ) = table[schema]
        else:
            raise AuthorityError("terminal projection event schema invalid")
        event_ordinal = authoritative_event["event_ordinal"]
        event_schema = schema
        event_kind = authoritative_event["event_kind"]
        event_raw_sha = _sha(authoritative_event_raw)
        event_self = authoritative_event["event_sha256"]
        typed = True
    return _attach(
        {
            "schema_version": TERMINAL_PROJECTION_SCHEMA,
            "attempt_id_sha256": marker["attempt_id_sha256"],
            "attempt_nonce_sha256": marker["attempt_nonce_sha256"],
            "registration_record_sha256": marker["registration_record_sha256"],
            "registration_raw_sha256": _sha(registration_raw),
            "marker_raw_sha256": _sha(marker_raw),
            "marker_sha256": marker["marker_sha256"],
            "marker_raw_observed": True,
            "marker_self_valid": True,
            "authoritative_event_ordinal": event_ordinal,
            "authoritative_event_schema": event_schema,
            "authoritative_event_kind": event_kind,
            "authoritative_event_raw_sha256": event_raw_sha,
            "authoritative_event_sha256": event_self,
            "authoritative_typed_event_present": typed,
            "terminal_state_inferred_from_durable_prefix": inferred,
            "terminal_state": state,
            "outcome": outcome,
            "child_launch_claim_count": child_claims,
            "child_process_start_count": child_processes,
            "child_process_start_count_directly_observed": process_count_observed,
            "retry_permitted": False,
            "runtime_approval_created": False,
            "scientific_execution_performed": False,
        },
        "terminal_sha256",
    )


def _make_published_result(
    registration: Mapping[str, Any],
    marker: Mapping[str, Any],
    terminal_raw: bytes,
    terminal: Mapping[str, Any],
) -> Dict[str, Any]:
    return _attach(
        {
            "schema_version": PUBLISHED_RESULT_SCHEMA,
            "registration_record_sha256": registration["record_sha256"],
            "attempt_id_sha256": marker["attempt_id_sha256"],
            "attempt_nonce_sha256": marker["attempt_nonce_sha256"],
            "local_terminal_raw_sha256": _sha(terminal_raw),
            "local_terminal_sha256": terminal["terminal_sha256"],
            "terminal_state": terminal["terminal_state"],
            "outcome": terminal["outcome"],
            "retry_permitted": False,
            "runtime_approval_created": False,
            "scientific_execution_performed": False,
            "raw_environment_published": False,
            "raw_identity_published": False,
            "raw_path_or_argv_published": False,
        },
        "record_sha256",
    )


def _validate_local_published_result(
    result: Mapping[str, Any],
    registration: Mapping[str, Any],
    marker: Mapping[str, Any],
    terminal_raw: bytes,
    terminal: Mapping[str, Any],
) -> Dict[str, Any]:
    fields = {
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
    }
    if type(result) is not dict or set(result) != fields:
        raise AuthorityError("published result field roster invalid")
    expected = {
        "schema_version": PUBLISHED_RESULT_SCHEMA,
        "registration_record_sha256": registration["record_sha256"],
        "attempt_id_sha256": marker["attempt_id_sha256"],
        "attempt_nonce_sha256": marker["attempt_nonce_sha256"],
        "local_terminal_raw_sha256": _sha(terminal_raw),
        "local_terminal_sha256": terminal["terminal_sha256"],
        "terminal_state": terminal["terminal_state"],
        "outcome": terminal["outcome"],
        "retry_permitted": False,
        "runtime_approval_created": False,
        "scientific_execution_performed": False,
        "raw_environment_published": False,
        "raw_identity_published": False,
        "raw_path_or_argv_published": False,
    }
    for key, value in expected.items():
        if type(result[key]) is not type(value) or result[key] != value:
            raise AuthorityError("published result semantic mismatch")
    if not _record_self_exact(result, "record_sha256"):
        raise AuthorityError("published result self digest invalid")
    return dict(result)


def _validate_local_prechild_failure_publication_prefix(
    marker_raw: bytes,
    marker: Mapping[str, Any],
    registration_raw: bytes,
    registration: Mapping[str, Any],
    authorization: Mapping[str, Any],
    genesis_raw: bytes,
    event_raws: Sequence[bytes],
    terminal_raw: bytes,
    terminal: Mapping[str, Any],
    result: Mapping[str, Any],
) -> None:
    """Close the one contracts-unavailable controlled-failure publication path.

    This is deliberately narrower than the canonical contracts validator: it
    accepts only the exact locally generated event-0/effect-free event-1 failure
    schedule.  It exists so loss of the contracts module can itself have a local,
    transport-independent terminal result without turning this authority into a
    second general record contract.
    """

    if type(event_raws) not in (list, tuple) or len(event_raws) != 2:
        raise AuthorityError("local fallback event schedule invalid")
    live = _LIVE_CUSTODY
    if type(live) is not dict:
        raise AuthorityError("local fallback live custody absent")
    authorization_raw = _file_bytes(authorization)
    if (
        live.get("marker_raw") != marker_raw
        or live.get("marker") != marker
        or live.get("registration_raw") != registration_raw
        or live.get("registration") != registration
        or live.get("authorization_raw") != authorization_raw
        or live.get("authorization") != authorization
    ):
        raise AuthorityError("local fallback static custody mismatch")
    expected_marker = _make_marker(
        registration_raw,
        registration,
        authorization_raw,
        authorization,
    )
    if marker != expected_marker or marker_raw != _file_bytes(expected_marker):
        raise AuthorityError("local fallback marker mismatch")
    genesis = _parse_canonical(genesis_raw)
    expected_genesis = _make_genesis(
        marker_raw,
        marker,
        registration_raw,
        authorization_raw,
        authorization,
    )
    if genesis != expected_genesis or genesis_raw != _file_bytes(expected_genesis):
        raise AuthorityError("local fallback genesis mismatch")
    event_zero = _parse_canonical(event_raws[0])
    expected_zero = _make_event_zero(
        marker_raw,
        marker,
        registration_raw,
        genesis_raw,
        genesis,
    )
    if event_zero != expected_zero or event_raws[0] != _file_bytes(expected_zero):
        raise AuthorityError("local fallback evaluation claim mismatch")
    event_one = _parse_canonical(event_raws[1])
    gates = event_one.get("gate_vector")
    if type(gates) is not dict or set(gates) != set(PRECHILD_GATE_ORDER):
        raise AuthorityError("local fallback gate vector invalid")
    if any(type(gates[name]) is not bool for name in PRECHILD_GATE_ORDER):
        raise AuthorityError("local fallback gate type invalid")
    failure_code = _prechild_failure_code(gates)
    if failure_code == "NONE":
        raise AuthorityError("local fallback cannot carry admission")
    expected_one = _make_prechild_event(
        None,
        False,
        gates,
        marker_raw,
        marker,
        registration_raw,
        event_raws[0],
        event_zero,
    )
    if event_one != expected_one or event_raws[1] != _file_bytes(expected_one):
        raise AuthorityError("local fallback prechild failure mismatch")
    expected_terminal = _make_terminal_projection(
        marker_raw,
        marker,
        registration_raw,
        event_raws[1],
        event_one,
    )
    if terminal != expected_terminal or terminal_raw != _file_bytes(expected_terminal):
        raise AuthorityError("local fallback terminal projection mismatch")
    expected_result = _make_published_result(
        registration,
        marker,
        terminal_raw,
        terminal,
    )
    if result != expected_result:
        raise AuthorityError("local fallback published result mismatch")
    _validate_local_published_result(
        result,
        registration,
        marker,
        terminal_raw,
        terminal,
    )


def _publish_result_live(
    raw: bytes,
    genesis_raw: bytes,
    event_raws: Sequence[bytes],
    terminal_raw: bytes,
) -> bytes:
    _require_live_write_scope()
    if (
        type(raw) is not bytes
        or not raw
        or type(terminal_raw) is not bytes
        or not terminal_raw
        or _lstat(RESULT_PATH) is not None
    ):
        raise AuthorityError("external result publication is not pristine")
    _require_local_prefix(genesis_raw, event_raws, terminal_raw=terminal_raw)
    parent_snapshot = _ancestor_snapshot(RESULT_PATH)
    descriptor = os.open(
        str(RESULT_PATH),
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0),
        0o644,
    )
    try:
        os.fchmod(descriptor, 0o644)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or stat.S_IMODE(opened.st_mode) != 0o644
            or opened.st_size != 0
        ):
            raise AuthorityError("external result descriptor custody invalid")
        os.fsync(descriptor)
        _fsync_directory(RESULT_PATH.parent)
        reserved = os.fstat(descriptor)
        reserved_path = RESULT_PATH.lstat()
        if (
            _leaf_identity(opened) != _leaf_identity(reserved)
            or _leaf_identity(reserved) != _leaf_identity(reserved_path)
            or reserved.st_size != 0
        ):
            raise AuthorityError("external result reservation custody invalid")
        # The no-clobber inode is now durable.  Reopen the complete authoritative
        # prefix and exact local terminal before placing any derivative bytes in it.
        _require_local_prefix(
            genesis_raw,
            event_raws,
            terminal_raw=terminal_raw,
            result_raw=b"",
        )
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            if written <= 0:
                raise AuthorityError("short external result write")
            offset += written
        os.fsync(descriptor)
        published = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    current = RESULT_PATH.lstat()
    if (
        _structural_identity(reserved) != _structural_identity(published)
        or reserved.st_nlink != published.st_nlink
        or _leaf_identity(published) != _leaf_identity(current)
        or current.st_nlink != 1
        or stat.S_IMODE(current.st_mode) != 0o644
        or current.st_size != len(raw)
    ):
        raise AuthorityError("external result publication custody invalid")
    _require_ancestors(parent_snapshot)
    _fsync_directory(RESULT_PATH.parent)
    reopened = _stable_read(RESULT_PATH, 0o644)
    if reopened != raw:
        raise AuthorityError("external result publication reopen mismatch")
    _require_local_prefix(
        genesis_raw,
        event_raws,
        terminal_raw=terminal_raw,
        result_raw=raw,
    )
    return reopened


def _persist_terminal_projection(
    contracts: Optional[Any],
    marker_raw: bytes,
    marker: Mapping[str, Any],
    registration_raw: bytes,
    registration: Mapping[str, Any],
    authorization: Mapping[str, Any],
    genesis_raw: bytes,
    event_raws: Sequence[bytes],
    authoritative_event: Mapping[str, Any],
) -> Dict[str, Any]:
    _require_local_prefix(genesis_raw, event_raws)
    authoritative_raw = event_raws[-1]
    projection = _make_terminal_projection(
        marker_raw,
        marker,
        registration_raw,
        authoritative_raw,
        authoritative_event,
    )
    genesis: Dict[str, Any] = _parse_canonical(genesis_raw)
    events: List[Dict[str, Any]] = [_parse_canonical(item) for item in event_raws]
    if contracts is not None:
        contracts.validate_full_prefix(
            marker,
            marker_raw,
            authorization,
            registration["record_sha256"],
            _sha(registration_raw),
            genesis,
            genesis_raw,
            events,
            list(event_raws),
        )
        contracts.validate_terminal_projection_against_prefix(
            projection,
            marker,
            marker_raw,
            authorization,
            registration["record_sha256"],
            _sha(registration_raw),
            authoritative_event,
            authoritative_raw,
        )
    raw = _file_bytes(projection)
    _write_new_live(TERMINAL_PATH, raw)
    if _stable_read(TERMINAL_PATH, 0o600) != raw:
        raise AuthorityError("local terminal projection reopen mismatch")
    if contracts is not None:
        summary = _scan_valid_prefix(
            contracts,
            _operational_paths(WORKSPACE_ROOT),
            WORKSPACE_ROOT.parent,
            registration_raw,
            registration,
            authorization,
            marker_raw,
            marker,
        )
        if (
            summary["milestone_state"] != projection["terminal_state"]
            or not summary["local_terminal_projection_exact"]
            or summary["external_result_present"]
        ):
            raise AuthorityError("persisted terminal projection is not fully anchored")
    _require_local_prefix(genesis_raw, event_raws, terminal_raw=raw)
    result = _make_published_result(
        registration, marker, raw, projection
    )
    _validate_local_published_result(
        result, registration, marker, raw, projection
    )
    if contracts is not None:
        contracts.validate_published_result_against_full_prefix(
            result,
            marker,
            marker_raw,
            authorization,
            registration["record_sha256"],
            _sha(registration_raw),
            genesis,
            genesis_raw,
            events,
            list(event_raws),
            projection,
            raw,
        )
    else:
        _validate_local_prechild_failure_publication_prefix(
            marker_raw,
            marker,
            registration_raw,
            registration,
            authorization,
            genesis_raw,
            event_raws,
            raw,
            projection,
            result,
        )
    result_raw = _file_bytes(result)
    if contracts is not None and result_raw != contracts.canonical_file_bytes(result):
        raise AuthorityError("published result canonical encoding mismatch")
    reopened_result_raw = _publish_result_live(
        result_raw,
        genesis_raw,
        event_raws,
        raw,
    )
    reopened_result = _parse_canonical(reopened_result_raw)
    if reopened_result != result:
        raise AuthorityError("external result is not fully prefix-anchored")
    if contracts is not None:
        final_summary = _scan_valid_prefix(
            contracts,
            _operational_paths(WORKSPACE_ROOT),
            WORKSPACE_ROOT.parent,
            registration_raw,
            registration,
            authorization,
            marker_raw,
            marker,
        )
        if (
            final_summary["milestone_state"] != projection["terminal_state"]
            or not final_summary["local_terminal_projection_exact"]
            or not final_summary["external_result_exact"]
        ):
            raise AuthorityError("external result is not fully prefix-anchored")
    return reopened_result


def _run_child_bounded(
    contracts: Any,
    request_raw: bytes,
    genesis_raw: bytes,
    event_raws: Sequence[bytes],
    registration_raw: bytes,
    registration: Mapping[str, Any],
) -> Dict[str, Any]:
    import selectors
    import signal
    import subprocess
    import time

    transport: Dict[str, Any] = {
        "child_spawn_succeeded": False,
        "child_stdin_captured_write_byte_count_observed": False,
        "child_stdin_captured_write_byte_count": None,
        "child_stdin_request_fully_written": False,
        "child_timeout_observed": False,
        "child_stdout_captured_byte_count_observed": False,
        "child_stdout_captured_byte_count": None,
        "child_stdout_eof_observed": False,
        "child_stdout_overflow_observed": False,
        "child_stderr_captured_byte_count_observed": False,
        "child_stderr_captured_byte_count": None,
        "child_stderr_eof_observed": False,
        "child_stderr_overflow_observed": False,
        "child_process_reap_observed": False,
        "child_exit_code_observed": False,
        "child_exit_code": None,
        "child_observation": None,
    }
    command = [
        str(PYTHON_PATH),
        *PYTHON_FLAGS,
        str(RUNTIME_PATH),
        "--emit-child-observation",
    ]
    process: Any = None
    selector: Any = None
    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    stdin_count_observed = False
    stdout_count_observed = False
    stderr_count_observed = False
    stdin_offset = 0
    eof = {"stdout": False, "stderr": False}
    overflow = {"stdout": False, "stderr": False}
    deadline: Optional[float] = None

    def terminate() -> None:
        if process is None:
            return
        try:
            if process.poll() is not None:
                return
        except Exception:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    def reap_within(seconds: float) -> str:
        if process is None:
            return "ERROR"
        try:
            code = process.wait(timeout=max(0.0, seconds))
        except subprocess.TimeoutExpired:
            return "TIMEOUT"
        except Exception:
            return "ERROR"
        if type(code) is not int:
            return "ERROR"
        transport["child_process_reap_observed"] = True
        transport["child_exit_code_observed"] = True
        transport["child_exit_code"] = code
        return "REAPED"

    def unregister_and_close(stream: Any) -> None:
        if stream is None:
            return
        if selector is not None:
            try:
                selector.unregister(stream.fileno())
            except Exception:
                pass
        try:
            stream.close()
        except Exception:
            pass

    try:
        if type(event_raws) not in (list, tuple) or len(event_raws) != 3:
            raise AuthorityError("prelaunch event prefix invalid")
        child_claim = _parse_canonical(event_raws[-1])
        if (
            child_claim.get("schema_version") != CHILD_CLAIM_SCHEMA
            or child_claim.get("runtime_request") is None
            or request_raw != _file_bytes(child_claim["runtime_request"])
            or not _postflight_custody_exact(
                contracts,
                genesis_raw,
                event_raws,
                registration_raw,
                registration,
            )
        ):
            raise AuthorityError("prelaunch full-prefix custody mismatch")
        # The one deadline covers process creation, nonblocking stdin transfer,
        # bounded output capture, and ordinary reap observation.
        deadline = time.monotonic() + CHILD_TIMEOUT_SECONDS
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(WORKSPACE_ROOT),
            env=dict(REQUESTED_ENVIRONMENT),
            close_fds=True,
            start_new_session=True,
            bufsize=0,
        )
        transport["child_spawn_succeeded"] = True
        if process.stdin is None or process.stdout is None or process.stderr is None:
            raise AuthorityError("child pipe setup incomplete")
        selector = selectors.DefaultSelector()
        input_fd = process.stdin.fileno()
        stdout_fd = process.stdout.fileno()
        stderr_fd = process.stderr.fileno()
        stdin_count_observed = True
        stdout_count_observed = True
        stderr_count_observed = True
        os.set_blocking(input_fd, False)
        os.set_blocking(stdout_fd, False)
        os.set_blocking(stderr_fd, False)
        selector.register(input_fd, selectors.EVENT_WRITE, "stdin")
        streams = {
            stdout_fd: ("stdout", stdout_buffer, MAX_STDOUT_BYTES),
            stderr_fd: ("stderr", stderr_buffer, MAX_STDERR_BYTES),
        }
        for descriptor in streams:
            selector.register(descriptor, selectors.EVENT_READ, streams[descriptor][0])
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                transport["child_timeout_observed"] = True
                break
            ready = selector.select(min(remaining, 0.25))
            for key, _mask in ready:
                if key.data == "stdin":
                    if stdin_offset >= len(request_raw):
                        transport["child_stdin_request_fully_written"] = True
                        unregister_and_close(process.stdin)
                        continue
                    try:
                        written = os.write(
                            key.fd,
                            request_raw[stdin_offset : stdin_offset + 8192],
                        )
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        unregister_and_close(process.stdin)
                        continue
                    if written <= 0:
                        unregister_and_close(process.stdin)
                        continue
                    stdin_offset += written
                    if stdin_offset == len(request_raw):
                        transport["child_stdin_request_fully_written"] = True
                        unregister_and_close(process.stdin)
                    continue
                name, buffer, limit = streams[key.fd]
                allowance = limit + 1 - len(buffer)
                if allowance <= 0:
                    overflow[name] = True
                    selector.unregister(key.fd)
                    continue
                try:
                    chunk = os.read(key.fd, min(8192, allowance))
                except BlockingIOError:
                    continue
                if not chunk:
                    eof[name] = True
                    selector.unregister(key.fd)
                    continue
                buffer.extend(chunk)
                if len(buffer) > limit:
                    overflow[name] = True
                    selector.unregister(key.fd)
            if any(overflow.values()):
                break
        if transport["child_timeout_observed"] or any(overflow.values()):
            terminate()
        else:
            remaining = max(0.0, deadline - time.monotonic())
            reap_status = reap_within(remaining)
            if reap_status == "TIMEOUT":
                transport["child_timeout_observed"] = True
                terminate()
            elif reap_status == "ERROR":
                terminate()
        if not transport["child_process_reap_observed"]:
            reap_within(2.0)
    except Exception:
        terminate()
    finally:
        if process is not None and not transport["child_process_reap_observed"]:
            terminate()
            reap_within(2.0)
        transport["child_stdin_captured_write_byte_count_observed"] = (
            stdin_count_observed
        )
        transport["child_stdin_captured_write_byte_count"] = (
            stdin_offset if stdin_count_observed else None
        )
        transport["child_stdout_captured_byte_count_observed"] = (
            stdout_count_observed
        )
        transport["child_stdout_captured_byte_count"] = (
            len(stdout_buffer) if stdout_count_observed else None
        )
        transport["child_stdout_eof_observed"] = eof["stdout"]
        transport["child_stdout_overflow_observed"] = overflow["stdout"]
        transport["child_stderr_captured_byte_count_observed"] = (
            stderr_count_observed
        )
        transport["child_stderr_captured_byte_count"] = (
            len(stderr_buffer) if stderr_count_observed else None
        )
        transport["child_stderr_eof_observed"] = eof["stderr"]
        transport["child_stderr_overflow_observed"] = overflow["stderr"]
        if (
            transport["child_stdin_request_fully_written"]
            and eof["stdout"]
            and not overflow["stdout"]
            and eof["stderr"]
            and not overflow["stderr"]
            and len(stderr_buffer) == 0
            and transport["child_process_reap_observed"]
            and transport["child_exit_code_observed"]
            and transport["child_exit_code"] == 0
            and not transport["child_timeout_observed"]
        ):
            try:
                observation = contracts.load_canonical_record(bytes(stdout_buffer))
                transport["child_observation"] = contracts.validate_child_observation(
                    observation
                )
            except Exception:
                pass
        if selector is not None:
            try:
                selector.close()
            except Exception:
                pass
        for stream_name in ("stdin", "stdout", "stderr"):
            stream = getattr(process, stream_name, None) if process is not None else None
            if stream is not None:
                try:
                    stream.close()
                except Exception:
                    pass
        stdout_buffer.clear()
        stderr_buffer.clear()
    return transport


def _make_terminal_outcome(
    contracts: Any,
    marker_raw: bytes,
    marker: Mapping[str, Any],
    registration_raw: bytes,
    child_claim_raw: bytes,
    child_claim: Mapping[str, Any],
    transport: Mapping[str, Any],
    postflight_custody_exact: bool,
) -> Dict[str, Any]:
    if transport["child_spawn_succeeded"] and not transport[
        "child_process_reap_observed"
    ]:
        raise AuthorityError("terminal outcome forbidden while child reap is unknown")
    observation = transport["child_observation"]
    observation_raw = (
        contracts.canonical_file_bytes(observation) if observation is not None else None
    )
    gates = {
        "child_spawn_succeeded": transport["child_spawn_succeeded"],
        "child_stdin_request_fully_written": transport[
            "child_stdin_request_fully_written"
        ],
        "child_timeout_absent": transport["child_spawn_succeeded"]
        and not transport["child_timeout_observed"],
        "child_stdout_eof_and_within_bound": transport[
            "child_stdout_eof_observed"
        ]
        and not transport["child_stdout_overflow_observed"]
        and transport["child_stdout_captured_byte_count_observed"]
        and transport["child_stdout_captured_byte_count"] <= MAX_STDOUT_BYTES,
        "child_stderr_eof_and_empty": transport["child_stderr_eof_observed"]
        and not transport["child_stderr_overflow_observed"]
        and transport["child_stderr_captured_byte_count_observed"]
        and transport["child_stderr_captured_byte_count"] == 0,
        "child_process_reap_observed": transport["child_process_reap_observed"],
        "child_exit_zero": transport["child_exit_code_observed"]
        and transport["child_exit_code"] == 0,
        "child_contract_exact": observation is not None,
        "postflight_custody_exact": postflight_custody_exact,
    }
    code_by_gate = dict(
        zip(contracts.TRANSPORT_GATE_ORDER, contracts.TRANSPORT_FAILURE_CODES[1:])
    )
    failure_code = "NONE"
    for name in contracts.TRANSPORT_GATE_ORDER:
        if not gates[name]:
            failure_code = code_by_gate[name]
            break
    passed = (
        failure_code == "NONE"
        and observation is not None
        and observation["outcome"] == "PASS"
    )
    body = _record_common(
        TERMINAL_OUTCOME_SCHEMA,
        3,
        "TERMINAL_OUTCOME",
        marker_raw,
        marker,
        registration_raw,
        "EVENT",
        child_claim_raw,
        child_claim["event_sha256"],
        FAIL_STATE,
    )
    body.update(
        {
            "outcome": "PASS" if passed else "FAIL",
            "terminal_state": PASS_STATE if passed else FAIL_STATE,
            "transport_gate_vector": gates,
            "transport_gate_vector_sha256": _sha(_canonical(gates)),
            "transport_failure_code": failure_code,
            "child_launch_claim_count": 1,
            "child_process_start_count": int(transport["child_spawn_succeeded"]),
            "child_spawn_succeeded": transport["child_spawn_succeeded"],
            "child_stdin_captured_write_byte_count_observed": transport[
                "child_stdin_captured_write_byte_count_observed"
            ],
            "child_stdin_captured_write_byte_count": transport[
                "child_stdin_captured_write_byte_count"
            ],
            "child_stdin_request_fully_written": transport[
                "child_stdin_request_fully_written"
            ],
            "child_timeout_observed": transport["child_timeout_observed"],
            "child_stdout_captured_byte_count_observed": transport[
                "child_stdout_captured_byte_count_observed"
            ],
            "child_stdout_captured_byte_count": transport[
                "child_stdout_captured_byte_count"
            ],
            "child_stdout_eof_observed": transport["child_stdout_eof_observed"],
            "child_stdout_overflow_observed": transport[
                "child_stdout_overflow_observed"
            ],
            "child_stderr_captured_byte_count_observed": transport[
                "child_stderr_captured_byte_count_observed"
            ],
            "child_stderr_captured_byte_count": transport[
                "child_stderr_captured_byte_count"
            ],
            "child_stderr_eof_observed": transport["child_stderr_eof_observed"],
            "child_stderr_overflow_observed": transport[
                "child_stderr_overflow_observed"
            ],
            "child_process_reap_observed": transport["child_process_reap_observed"],
            "child_exit_code_observed": transport["child_exit_code_observed"],
            "child_exit_code": transport["child_exit_code"],
            "child_observation": observation,
            "child_observation_raw_sha256": (
                _sha(observation_raw) if observation_raw is not None else None
            ),
            "child_observation_sha256": (
                observation["observation_sha256"] if observation is not None else None
            ),
            "postflight_custody_exact": postflight_custody_exact,
            "raw_child_transport_persisted": False,
            "runtime_approval_created": False,
            "scientific_execution_performed": False,
        }
    )
    return contracts.validate_terminal_outcome(_attach(body, "event_sha256"))


def _postflight_custody_exact(
    contracts: Any,
    genesis_raw: bytes,
    event_raws: Sequence[bytes],
    registration_raw: bytes,
    registration: Mapping[str, Any],
) -> bool:
    try:
        _require_local_prefix(genesis_raw, event_raws)
        _audit_v4_source_closure(registration_raw, registration)
        _audit_v3_terminal()
        live = _LIVE_CUSTODY
        if type(live) is not dict:
            return False
        summary = _scan_valid_prefix(
            contracts,
            _operational_paths(WORKSPACE_ROOT),
            WORKSPACE_ROOT.parent,
            registration_raw,
            registration,
            live["authorization"],
            live["marker_raw"],
            live["marker"],
        )
        return (
            summary["event_count"] == 3
            and summary["milestone_state"] == CHILD_FALLBACK_STATE
            and not summary["local_terminal_projection_present"]
            and not summary["external_result_present"]
        )
    except Exception:
        return False


def execute_once(arguments: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Execute the future frozen route; dormant until a fresh certificate exists."""

    if arguments is not None or not _dispatch_scope_exact():
        raise AuthorityError("execute-once is restricted to exact native dispatch")
    registration_raw, registration, authorization_raw, authorization = (
        _load_bootstrap_closure()
    )
    marker = _make_marker(
        registration_raw, registration, authorization_raw, authorization
    )
    marker_raw = _file_bytes(marker)
    _reserve_and_publish_marker(
        marker_raw,
        marker,
        registration_raw,
        registration,
        authorization_raw,
        authorization,
    )
    lock_descriptor: Optional[int] = None
    try:
        _mkdir_live(PREPARATION_ROOT)
        _mkdir_live(LEDGER_PATH)
        _mkdir_live(EVENTS_PATH)
        lock_descriptor = _create_lock()
        genesis = _make_genesis(
            marker_raw,
            marker,
            registration_raw,
            authorization_raw,
            authorization,
        )
        genesis_raw = _file_bytes(genesis)
        _require_pre_genesis_prefix()
        _write_new_live(GENESIS_PATH, genesis_raw)
        event_zero = _make_event_zero(
            marker_raw, marker, registration_raw, genesis_raw, genesis
        )
        event_zero_raw = _file_bytes(event_zero)
        _require_local_prefix(genesis_raw, [])
        _write_new_live(_event_path(0), event_zero_raw)
        contracts: Optional[Any]
        try:
            contracts = _load_contracts()
            contracts.validate_full_prefix(
                marker,
                marker_raw,
                authorization,
                registration["record_sha256"],
                _sha(registration_raw),
                genesis,
                genesis_raw,
                [event_zero],
                [event_zero_raw],
            )
            prefix_exact = True
        except Exception:
            contracts = None
            prefix_exact = False
        gates = _profile_gate_vector(
            contracts,
            registration_raw,
            registration,
            authorization_raw,
            authorization,
            prefix_exact,
            genesis_raw,
            event_zero_raw,
        )
        admitted = _prechild_failure_code(gates) == "NONE"
        event_one = _make_prechild_event(
            contracts,
            admitted,
            gates,
            marker_raw,
            marker,
            registration_raw,
            event_zero_raw,
            event_zero,
        )
        event_one_raw = _file_bytes(event_one)
        if contracts is not None:
            contracts.validate_event_chain(
                event_one,
                marker,
                authorization,
                registration["record_sha256"],
                _sha(registration_raw),
                marker_raw,
                genesis,
                genesis_raw,
                event_zero,
                event_zero_raw,
            )
        _require_local_prefix(genesis_raw, [event_zero_raw])
        _write_new_live(_event_path(1), event_one_raw)
        if contracts is not None:
            contracts.validate_full_prefix(
                marker,
                marker_raw,
                authorization,
                registration["record_sha256"],
                _sha(registration_raw),
                genesis,
                genesis_raw,
                [event_zero, event_one],
                [event_zero_raw, event_one_raw],
            )
            _require_local_prefix(genesis_raw, [event_zero_raw, event_one_raw])
        if not admitted:
            return _persist_terminal_projection(
                contracts,
                marker_raw,
                marker,
                registration_raw,
                registration,
                authorization,
                genesis_raw,
                [event_zero_raw, event_one_raw],
                event_one,
            )
        if contracts is None:
            raise AuthorityError("admission without exact contracts is forbidden")
        try:
            request = _make_runtime_request(
                contracts,
                marker,
                registration_raw,
                authorization_raw,
                authorization,
                event_one,
            )
            contracts.validate_runtime_request(request)
        except Exception:
            failure = _make_post_admission_failure(
                contracts,
                "REQUEST_CONSTRUCTION",
                marker_raw,
                marker,
                registration_raw,
                event_one_raw,
                event_one,
            )
            failure_raw = _file_bytes(failure)
            contracts.validate_event_chain(
                failure,
                marker,
                authorization,
                registration["record_sha256"],
                _sha(registration_raw),
                marker_raw,
                genesis,
                genesis_raw,
                event_one,
                event_one_raw,
            )
            _require_local_prefix(genesis_raw, [event_zero_raw, event_one_raw])
            _write_new_live(_event_path(2), failure_raw)
            contracts.validate_full_prefix(
                marker,
                marker_raw,
                authorization,
                registration["record_sha256"],
                _sha(registration_raw),
                genesis,
                genesis_raw,
                [event_zero, event_one, failure],
                [event_zero_raw, event_one_raw, failure_raw],
            )
            return _persist_terminal_projection(
                contracts,
                marker_raw,
                marker,
                registration_raw,
                registration,
                authorization,
                genesis_raw,
                [event_zero_raw, event_one_raw, failure_raw],
                failure,
            )
        request_raw = contracts.canonical_file_bytes(request)
        try:
            child_claim = _make_child_claim(
                contracts,
                marker_raw,
                marker,
                registration_raw,
                event_one_raw,
                event_one,
                request,
            )
            contracts.validate_event_chain(
                child_claim,
                marker,
                authorization,
                registration["record_sha256"],
                _sha(registration_raw),
                marker_raw,
                genesis,
                genesis_raw,
                event_one,
                event_one_raw,
            )
        except Exception:
            failure = _make_post_admission_failure(
                contracts,
                "CHILD_CLAIM_PUBLICATION",
                marker_raw,
                marker,
                registration_raw,
                event_one_raw,
                event_one,
            )
            failure_raw = _file_bytes(failure)
            contracts.validate_event_chain(
                failure,
                marker,
                authorization,
                registration["record_sha256"],
                _sha(registration_raw),
                marker_raw,
                genesis,
                genesis_raw,
                event_one,
                event_one_raw,
            )
            _require_local_prefix(genesis_raw, [event_zero_raw, event_one_raw])
            _write_new_live(_event_path(2), failure_raw)
            contracts.validate_full_prefix(
                marker,
                marker_raw,
                authorization,
                registration["record_sha256"],
                _sha(registration_raw),
                genesis,
                genesis_raw,
                [event_zero, event_one, failure],
                [event_zero_raw, event_one_raw, failure_raw],
            )
            return _persist_terminal_projection(
                contracts,
                marker_raw,
                marker,
                registration_raw,
                registration,
                authorization,
                genesis_raw,
                [event_zero_raw, event_one_raw, failure_raw],
                failure,
            )
        child_claim_raw = _file_bytes(child_claim)
        _require_local_prefix(genesis_raw, [event_zero_raw, event_one_raw])
        _write_new_live(_event_path(2), child_claim_raw)
        contracts.validate_full_prefix(
            marker,
            marker_raw,
            authorization,
            registration["record_sha256"],
            _sha(registration_raw),
            genesis,
            genesis_raw,
            [event_zero, event_one, child_claim],
            [event_zero_raw, event_one_raw, child_claim_raw],
        )
        _require_local_prefix(
            genesis_raw, [event_zero_raw, event_one_raw, child_claim_raw]
        )
        transport = _run_child_bounded(
            contracts,
            request_raw,
            genesis_raw,
            [event_zero_raw, event_one_raw, child_claim_raw],
            registration_raw,
            registration,
        )
        if transport["child_spawn_succeeded"] and not transport[
            "child_process_reap_observed"
        ]:
            # The durable child-claim prefix is the terminal fallback.  Never
            # assert a typed event-3 outcome while process liveness is unknown.
            raise AuthorityError("child reap was not directly observed")
        postflight_exact = _postflight_custody_exact(
            contracts,
            genesis_raw,
            [event_zero_raw, event_one_raw, child_claim_raw],
            registration_raw,
            registration,
        )
        terminal_event = _make_terminal_outcome(
            contracts,
            marker_raw,
            marker,
            registration_raw,
            child_claim_raw,
            child_claim,
            transport,
            postflight_exact,
        )
        terminal_event_raw = _file_bytes(terminal_event)
        contracts.validate_event_chain(
            terminal_event,
            marker,
            authorization,
            registration["record_sha256"],
            _sha(registration_raw),
            marker_raw,
            genesis,
            genesis_raw,
            child_claim,
            child_claim_raw,
        )
        _require_local_prefix(
            genesis_raw, [event_zero_raw, event_one_raw, child_claim_raw]
        )
        _write_new_live(_event_path(3), terminal_event_raw)
        contracts.validate_full_prefix(
            marker,
            marker_raw,
            authorization,
            registration["record_sha256"],
            _sha(registration_raw),
            genesis,
            genesis_raw,
            [event_zero, event_one, child_claim, terminal_event],
            [
                event_zero_raw,
                event_one_raw,
                child_claim_raw,
                terminal_event_raw,
            ],
        )
        return _persist_terminal_projection(
            contracts,
            marker_raw,
            marker,
            registration_raw,
            registration,
            authorization,
            genesis_raw,
            [
                event_zero_raw,
                event_one_raw,
                child_claim_raw,
                terminal_event_raw,
            ],
            terminal_event,
        )
    finally:
        if lock_descriptor is not None:
            try:
                os.close(lock_descriptor)
            except Exception:
                pass


def main(arguments: Optional[Sequence[str]] = None) -> int:
    supplied = list(sys.argv[1:] if arguments is None else arguments)
    if arguments is not None or supplied != ["--execute-once"]:
        return 64
    try:
        projection = execute_once()
    except Exception:
        return 70
    try:
        sys.stdout.buffer.write(_file_bytes(projection))
        sys.stdout.buffer.flush()
    except Exception:
        return 70
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "AUTHORIZATION_CONTEXT_SHA256",
    "AUTHORIZATION_CONTEXT_TEXT",
    "AUTHORIZATION_PATH",
    "AuthorityError",
    "GLOBAL_STATE",
    "MARKER_PATH",
    "PREPARATION_ROOT",
    "RESULT_PATH",
    "STATIC_STATE",
    "SyntheticStateRoot",
    "TERMINAL_PATH",
    "VISIBLE_ASSENT_SHA256",
    "VISIBLE_ASSENT_TEXT",
    "execute_once",
    "main",
    "status",
]
