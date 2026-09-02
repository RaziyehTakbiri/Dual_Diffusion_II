"""Sole dormant filesystem authority for A1 R1 activation preparation v2.

The implementation is frozen but not invoked.  Live writes are available only
from the exact isolated direct-file CLI after an explicit future authorization.
No function in this module launches rank, training, production, or scientific
work, and no runtime approval or scientific authority ledger can be issued.
"""

from __future__ import annotations

import ast
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import selectors
import secrets
import stat
import subprocess
import sys
import time
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from research.production import (
    finite_association_r1_activation_preparation_contracts_v2 as contracts,
)
from research.production import (
    finite_association_r1_activation_preparation_runtime_v2 as runtime,
)
from research.production import finite_association_r1_successor_adapter_v1 as v1_adapter
from research.production import (
    finite_association_r1_successor_authority_v1 as v1_authority,
)


HUMAN_PATH = "manuscript_v3/a1_r1_activation_preparation_implementation_freeze_v2.md"
MACHINE_PATH = (
    "research/fixtures/"
    "manuscript_v3_a1_r1_activation_preparation_implementation_freeze_v2.json"
)
CONTRACTS_PATH = (
    "research/production/finite_association_r1_activation_preparation_contracts_v2.py"
)
AUTHORITY_PATH = (
    "research/production/finite_association_r1_activation_preparation_authority_v2.py"
)
RUNTIME_PATH = (
    "research/production/finite_association_r1_activation_preparation_runtime_v2.py"
)
TEST_PATH = (
    "tests/unit/"
    "test_manuscript_v3_a1_r1_activation_preparation_implementation_freeze_v2.py"
)
REGISTRATION_ID = "A1_R1_ACTIVATION_PREPARATION_IMPLEMENTATION_FREEZE_V2"
REGISTRATION_DOMAIN = (contracts.REGISTRATION_SCHEMA + "\0").encode("ascii")
QUALIFICATION_SNAPSHOT_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-static-qualification-v2\0"
)
PATH_ROSTER_DOMAIN = b"heterodiff-a1-r1-activation-preparation-path-roster-v2\0"
CAPSULE_PLAN_DOMAIN = b"heterodiff-a1-r1-activation-preparation-capsule-plan-v2\0"
EVENT_PROTOCOL_DOMAIN = b"heterodiff-a1-r1-preparation-event-protocol-v2\0"
SCIENTIFIC_EVENT_PROTOCOL_DOMAIN = (
    b"heterodiff-a1-r1-preparation-bound-scientific-event-protocol-v2\0"
)
PREPARATION_NONCE_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-instance-nonce-v2\0"
)
OPERATION_NONCE_DOMAIN = b"heterodiff-a1-r1-preparation-operation-nonce-v2\0"
LAUNCH_BINDING_DOMAIN = b"heterodiff-a1-r1-runtime-capture-launch-binding-v2\0"
OPERATOR_AUTHORIZATION_DOMAIN = (
    b"heterodiff-a1-r1-activation-preparation-operator-authorization-v2\0"
)
INVENTORY_DOMAIN = b"heterodiff-a1-r1-source-capsule-live-inventory-v2\0"
RUNTIME_ORACLE_API_SHA256 = hashlib.sha256(
    b"heterodiff-a1-r1-runtime-inspection-oracle-api-v2\0"
    b"build_raw_capture_envelope(request_payload:bytes,capture_ordinal:int)->bytes"
).hexdigest()
FROZEN_REGISTRY = (
    4052249444591756,
    3253,
    5003,
    7411,
    10007,
    13007,
    16001,
    20011,
)

MARKER_PATH = "artifacts/a1_r1_activation_preparation_v2.attempt.json"
PREPARATION_ROOT = "artifacts/a1_r1_activation_preparation_v2"
LEDGER_ROOT = PREPARATION_ROOT + "/ledger"
LEDGER_LOCK_PATH = LEDGER_ROOT + "/writer.lock"
LEDGER_GENESIS_PATH = LEDGER_ROOT + "/genesis.json"
LEDGER_EVENTS_ROOT = LEDGER_ROOT + "/events"
LEDGER_NONCE_ROOT = LEDGER_ROOT + "/nonce-claims"
LEDGER_RECEIPTS_ROOT = LEDGER_ROOT + "/receipts"
CAPSULE_ROOT = PREPARATION_ROOT + "/capsule"
RUNTIME_CANDIDATE_ROOT = PREPARATION_ROOT + "/runtime-candidate"
CAPSULE_MANIFEST_PATH = LEDGER_RECEIPTS_ROOT + "/source-capsule-manifest.json"
CAPSULE_ADMISSION_PATH = LEDGER_RECEIPTS_ROOT + "/source-capsule-admission.json"
RUNTIME_REQUEST_PATH = LEDGER_RECEIPTS_ROOT + "/runtime-double-capture-request.json"
RUNTIME_BINDING_A_PATH = LEDGER_RECEIPTS_ROOT + "/runtime-capture-a.binding.json"
RUNTIME_BINDING_B_PATH = LEDGER_RECEIPTS_ROOT + "/runtime-capture-b.binding.json"
RUNTIME_CANDIDATE_PATH = RUNTIME_CANDIDATE_ROOT + "/candidate.json"
RUNTIME_CAPTURE_A_CLAIM_PATH = LEDGER_NONCE_ROOT + "/runtime-capture-a.json"
RUNTIME_CAPTURE_B_CLAIM_PATH = LEDGER_NONCE_ROOT + "/runtime-capture-b.json"

PREDECESSOR_HUMAN_PATH = v1_authority.HUMAN_PATH
PREDECESSOR_MACHINE_PATH = v1_authority.MACHINE_PATH
PREDECESSOR_CONTRACTS_PATH = v1_authority.CONTRACTS_PATH
PREDECESSOR_AUTHORITY_PATH = v1_authority.AUTHORITY_PATH
PREDECESSOR_RUNTIME_PATH = v1_authority.ADAPTER_PATH
PREDECESSOR_TEST_PATH = v1_authority.TEST_PATH
PREDECESSOR_RAW_SHA256 = {
    PREDECESSOR_HUMAN_PATH: "4194d47c2c64b1f73ab1bcd8e1c450842164199b326448ff493fa8bcadce669c",
    PREDECESSOR_MACHINE_PATH: "0434078c44541eb7fe85f00d5e1f284030644e8934b9a2292f80dfc520f1a96f",
    PREDECESSOR_CONTRACTS_PATH: "e1fb4ec4f0e1a6a674ef8ee105752565276056a34f99edf9d12d52a3f3c92e5c",
    PREDECESSOR_AUTHORITY_PATH: "5182fa48aac81208161e1b8af432072fa9adf8815a60438c148140a2518c9e86",
    PREDECESSOR_RUNTIME_PATH: "b3a5f04079a45247e2a886fe830b066b80226986c0e594ac129be2384af8f149",
    PREDECESSOR_TEST_PATH: "183ac5d8d16d2b3970fa381460a92ccef7d295adb87b8cb5a1af1e129d0fd128",
}
PREDECESSOR_RECORD_SHA256 = (
    "7f15db9beb810aa3ffb34184841ee58d83be104cee80795b39ae77c7c5114fc1"
)

DORMANT_V1_PATHS = (
    "artifacts/a1_r1_successor_authority_ledger_v1",
    "artifacts/a1_r1_successor_candidate_decision_v1",
    "artifacts/a1_r1_successor_exact_campaign_v1",
    "artifacts/a1_r1_successor_independent_audit_v1",
    "artifacts/a1_r1_successor_precreation_attempt_v1.json",
    "artifacts/a1_r1_successor_primary_metrics_v1",
    "artifacts/a1_r1_successor_publication_decision_v1",
    "artifacts/a1_r1_successor_rank_gate_v1",
    "artifacts/a1_r1_successor_sampled_campaign_v1",
    "artifacts/a1_r1_successor_source_capsule_v1",
    "requirements/a1_r1_successor_runtime_admission_v1",
    "requirements/a1_r1_successor_runtime_admission_v1/approval-receipt.json",
    "requirements/a1_r1_successor_runtime_admission_v1/candidate-manifest.json",
    "requirements/a1_r1_successor_runtime_admission_v1/review-report.json",
    "requirements/a1_r1_successor_runtime_admission_v1/runtime-identity.json",
    "research/fixtures/"
    "manuscript_v3_a1_r1_successor_executable_preregistration_freeze_receipt_v1.json",
    "research/fixtures/manuscript_v3_a1_r1_successor_executable_preregistration_v1.json",
)
PERMANENTLY_ABSENT_V1_SRC_ADAPTER = (
    "src/heterodiff/experiments/finite_association_registry_aware_capsule_v1.py"
)

OPERATOR_AUTHORIZATION_CONTEXT = (
    "I authorize the irreversible A1 R1 activation-preparation v2 sequence: its "
    "one-shot marker, deterministic source-capsule materialization, and exactly "
    "two privacy-safe runtime inspections; this does not authorize runtime "
    "approval, rank, training, production, scientific execution, claim promotion, "
    "or activation."
)
OPERATOR_AUTHORIZATION_SHA256 = hashlib.sha256(
    OPERATOR_AUTHORIZATION_DOMAIN + OPERATOR_AUTHORIZATION_CONTEXT.encode("utf-8")
).hexdigest()

EVENT_KINDS = (
    "CAPSULE_MATERIALIZATION_OPENED",
    "CAPSULE_ADMITTED",
    "RUNTIME_DOUBLE_CAPTURE_OPENED",
    "RUNTIME_CANDIDATE_ADMITTED_OR_REJECTED",
    "PREPARATION_CLOSED",
)
EVENT_MATRIX = {
    0: {
        "allowed_kinds": ("CAPSULE_MATERIALIZATION_OPENED",),
        "payload_schema": contracts.SOURCE_CAPSULE_MANIFEST_SCHEMA,
        "payload_path": CAPSULE_MANIFEST_PATH,
        "allowed_outcomes": ("OPENED",),
    },
    1: {
        "allowed_kinds": ("CAPSULE_ADMITTED",),
        "payload_schema": contracts.SOURCE_CAPSULE_ADMISSION_SCHEMA,
        "payload_path": CAPSULE_ADMISSION_PATH,
        "allowed_outcomes": ("ADMITTED_PREPARATION_CUSTODY_ONLY",),
    },
    2: {
        "allowed_kinds": ("RUNTIME_DOUBLE_CAPTURE_OPENED",),
        "payload_schema": contracts.RUNTIME_REQUEST_SCHEMA,
        "payload_path": RUNTIME_REQUEST_PATH,
        "allowed_outcomes": ("OPENED",),
    },
    3: {
        "allowed_kinds": (
            "RUNTIME_CANDIDATE_ADMITTED",
            "RUNTIME_DOUBLE_CAPTURE_REJECTED",
        ),
        "payload_schema": contracts.RUNTIME_CANDIDATE_SCHEMA,
        "payload_path": RUNTIME_CANDIDATE_PATH,
        "allowed_outcomes": (
            "ADMITTED_UNAPPROVED_PREPARATION_ONLY",
            "REJECTED_DOUBLE_CAPTURE_MISMATCH",
        ),
    },
    4: {
        "allowed_kinds": ("PREPARATION_CLOSED_AWAITING_OPERATOR_APPROVAL",),
        "payload_schema": contracts.RUNTIME_CANDIDATE_SCHEMA,
        "payload_path": RUNTIME_CANDIDATE_PATH,
        "allowed_outcomes": ("CLOSED_AWAITING_OPERATOR_APPROVAL",),
    },
}

EVENT_FILE_PATHS = tuple(
    LEDGER_EVENTS_ROOT + "/%020d.json" % ordinal for ordinal in range(5)
)
EVENT_CLAIM_PATHS = tuple(
    LEDGER_NONCE_ROOT + "/event-%020d.json" % ordinal for ordinal in range(5)
)
STATIC_V2_PATHS = (
    MARKER_PATH,
    PREPARATION_ROOT,
    LEDGER_ROOT,
    LEDGER_LOCK_PATH,
    LEDGER_GENESIS_PATH,
    LEDGER_EVENTS_ROOT,
    *EVENT_FILE_PATHS,
    LEDGER_NONCE_ROOT,
    *EVENT_CLAIM_PATHS,
    RUNTIME_CAPTURE_A_CLAIM_PATH,
    RUNTIME_CAPTURE_B_CLAIM_PATH,
    LEDGER_RECEIPTS_ROOT,
    CAPSULE_MANIFEST_PATH,
    CAPSULE_ADMISSION_PATH,
    RUNTIME_REQUEST_PATH,
    RUNTIME_BINDING_A_PATH,
    RUNTIME_BINDING_B_PATH,
    CAPSULE_ROOT,
    RUNTIME_CANDIDATE_ROOT,
    RUNTIME_CANDIDATE_PATH,
)
RUNTIME_FORBIDDEN_OUTPUT_NAMES = (
    "review.json",
    "approval.json",
    "final-runtime-manifest.json",
    "capture-a.envelope.json",
    "capture-b.envelope.json",
)

CANONICAL_PYTHON_RELATIVE_PATH = ".venv-m1/bin/python"
CANONICAL_INTERPRETER_REALPATH = (
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
)
NATIVE_PYTHON_ARGV0 = (
    "/Library/Frameworks/Python.framework/Versions/3.11/Resources/"
    "Python.app/Contents/MacOS/Python"
)
LIVE_ACTIONS = (
    "--create-marker-after-explicit-authorization",
    "--resume-genesis",
    "--materialize-capsule",
    "--capture-runtime-candidate",
)
MODULE_RELATIVE_PATH = AUTHORITY_PATH
ENTROPY_BYTE_COUNT = 32

NONCLAIMS = {
    "workspace_src_amended": False,
    "executable_preregistration_completed": False,
    "prerequisite_evidence_loadable": False,
    "canonical_preparation_sequence_executed": False,
    "canonical_marker_created": False,
    "live_os_entropy_contacted": False,
    "canonical_preparation_instance_nonce_minted": False,
    "scientific_campaign_nonce_minted": False,
    "canonical_capsule_materialized": False,
    "canonical_source_capsule_execution_admitted": False,
    "live_runtime_capture_performed": False,
    "canonical_raw_runtime_envelopes_persisted": False,
    "canonical_runtime_candidate_created": False,
    "canonical_runtime_review_created": False,
    "canonical_runtime_approval_created": False,
    "canonical_runtime_admitted": False,
    "scientific_authority_ledger_created": False,
    "rank_execution_authorized": False,
    "rank_execution_performed": False,
    "training_execution_authorized": False,
    "training_execution_performed": False,
    "production_execution_authorized": False,
    "production_execution_performed": False,
    "scientific_execution_authorized": False,
    "scientific_execution_performed": False,
    "claim_promoted": False,
    "submission_ready": False,
    "activation_complete": False,
}

PUBLICATION_ANONYMITY_BOUNDARY = {
    "internal_registration_not_submission_artifact": True,
    "anonymous_submission_inclusion_permitted": False,
    "public_release_inclusion_permitted": False,
    "raw_runtime_capture_envelope_persistence_permitted": False,
    "v2_root_must_pass_recursive_absolute_path_scan": True,
    "publication_safe_derivative_required": True,
    "publication_safe_derivative_path": None,
    "publication_roster_frozen": False,
    "fresh_anonymity_audit_required": True,
}


class PreparationAuthorityError(RuntimeError):
    """Fail-closed activation-preparation authority error."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(value: Any) -> bytes:
    return contracts.canonical_json(value)


def _normalized_existing_root(root: Path) -> Path:
    if not isinstance(root, Path):
        raise PreparationAuthorityError("custody root is not a Path")
    lexical = root.absolute()
    if ".." in lexical.parts:
        raise PreparationAuthorityError("custody root contains a parent traversal")
    resolved = root.resolve(strict=True)
    if lexical.as_posix() != resolved.as_posix():
        raise PreparationAuthorityError("custody root is aliased or symlinked")
    information = root.lstat()
    resolved_information = resolved.lstat()
    if (
        stat.S_ISLNK(information.st_mode)
        or not stat.S_ISDIR(information.st_mode)
        or information.st_dev != resolved_information.st_dev
        or information.st_ino != resolved_information.st_ino
    ):
        raise PreparationAuthorityError("custody root identity changed")
    return resolved


def _is_canonical_root(root: Path) -> bool:
    return _normalized_existing_root(root) == WORKSPACE_ROOT.resolve(strict=True)


def _guard_canonical_mutation(root: Path, live_action: str | None) -> None:
    normalized = _normalized_existing_root(root)
    if normalized == WORKSPACE_ROOT.resolve(strict=True):
        if live_action is None:
            raise PreparationAuthorityError(
                "canonical custody mutation requires an action-scoped live boundary"
            )
        observed = _require_live_cli_boundary(live_action)
        if observed != normalized:
            raise PreparationAuthorityError("canonical live root changed")


def _stat_identity(value: Any) -> Tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _ancestor_identity(value: Any) -> Tuple[int, ...]:
    return (value.st_dev, value.st_ino, value.st_mode, value.st_uid, value.st_gid)


def _existing_ancestors(path: Path) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
    rows = []
    for ancestor in reversed(path.absolute().parents):
        try:
            information = ancestor.lstat()
        except FileNotFoundError:
            break
        if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(information.st_mode):
            raise PreparationAuthorityError("custody path has a linked ancestor")
        rows.append((str(ancestor), _ancestor_identity(information)))
    return tuple(rows)


def _read_stable_file(path: Path) -> Tuple[bytes, Any]:
    ancestors = _existing_ancestors(path)
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise PreparationAuthorityError(
            "custody entry is not a regular nonsymlink file"
        )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if _stat_identity(opened) != _stat_identity(before):
            raise PreparationAuthorityError("custody entry changed before open")
        chunks = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(1 << 20, remaining))
            if not chunk:
                raise PreparationAuthorityError("custody entry ended during read")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise PreparationAuthorityError("custody entry grew during read")
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    payload = b"".join(chunks)
    after = path.lstat()
    if ancestors != _existing_ancestors(path):
        raise PreparationAuthorityError("custody ancestors changed during read")
    if (
        _stat_identity(before) != _stat_identity(after_descriptor)
        or _stat_identity(after_descriptor) != _stat_identity(after)
        or len(payload) != after.st_size
    ):
        raise PreparationAuthorityError("custody entry changed during read")
    return payload, after


def _path_has_entry(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _require_absent(path: Path) -> None:
    ancestors = _existing_ancestors(path)
    try:
        path.lstat()
    except FileNotFoundError:
        if ancestors != _existing_ancestors(path):
            raise PreparationAuthorityError("absence ancestors changed")
        return
    raise PreparationAuthorityError("required-absent path has an entry: " + str(path))


def _load_canonical_json(path: Path) -> Tuple[bytes, Dict[str, Any]]:
    payload, _ = _read_stable_file(path)
    try:
        record = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PreparationAuthorityError("custody JSON is invalid") from error
    if type(record) is not dict or payload != _canonical(record) + b"\n":
        raise PreparationAuthorityError("custody JSON is not canonical")
    return payload, record


def _file_sha256(root: Path, relative_path: str) -> str:
    return _sha256(_read_stable_file(root / relative_path)[0])


def _fsync_directory(path: Path) -> None:
    ancestors = _existing_ancestors(path)
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise PreparationAuthorityError("fsync target is not a nonsymlink directory")
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        opened = os.fstat(descriptor)
        if _ancestor_identity(opened) != _ancestor_identity(before):
            raise PreparationAuthorityError("fsync directory changed before open")
        os.fsync(descriptor)
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    if (
        ancestors != _existing_ancestors(path)
        or _ancestor_identity(before) != _ancestor_identity(after_descriptor)
        or _ancestor_identity(after_descriptor) != _ancestor_identity(after)
    ):
        raise PreparationAuthorityError("fsync directory changed")


def _write_all(descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise PreparationAuthorityError("short custody write")
        view = view[written:]


def _write_new_file(
    path: Path,
    payload: bytes,
    mode: int = 0o600,
    *,
    live_action: str | None = None,
) -> None:
    absolute = path.absolute()
    if ".." in absolute.parts:
        raise PreparationAuthorityError("custody file path contains a parent traversal")
    resolved_target = path.parent.resolve(strict=True) / path.name
    try:
        resolved_target.relative_to(WORKSPACE_ROOT.resolve(strict=True))
    except ValueError:
        pass
    else:
        _guard_canonical_mutation(WORKSPACE_ROOT, live_action)
    ancestors = _existing_ancestors(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, mode)
    try:
        os.fchmod(descriptor, mode)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            raise PreparationAuthorityError("new custody inode type changed")
        _write_all(descriptor, payload)
        os.fsync(descriptor)
        published = os.fstat(descriptor)
        if (
            published.st_dev != opened.st_dev
            or published.st_ino != opened.st_ino
            or published.st_nlink != 1
            or stat.S_IMODE(published.st_mode) != mode
            or published.st_size != len(payload)
        ):
            raise PreparationAuthorityError("new custody inode changed during write")
        if ancestors != _existing_ancestors(path):
            raise PreparationAuthorityError("custody ancestors changed during write")
    finally:
        os.close(descriptor)
    _fsync_directory(path.parent)
    reopened, information = _read_stable_file(path)
    if (
        reopened != payload
        or information.st_dev != published.st_dev
        or information.st_ino != published.st_ino
        or stat.S_IMODE(information.st_mode) != mode
        or information.st_nlink != 1
    ):
        raise PreparationAuthorityError("new custody file changed after publication")


def _ensure_directory(
    path: Path, mode: int = 0o700, *, live_action: str | None = None
) -> None:
    absolute = path.absolute()
    if ".." in absolute.parts:
        raise PreparationAuthorityError(
            "custody directory path contains a parent traversal"
        )
    resolved_target = path.parent.resolve(strict=True) / path.name
    try:
        resolved_target.relative_to(WORKSPACE_ROOT.resolve(strict=True))
    except ValueError:
        pass
    else:
        _guard_canonical_mutation(WORKSPACE_ROOT, live_action)
    if _path_has_entry(path):
        information = path.lstat()
        if (
            stat.S_ISLNK(information.st_mode)
            or not stat.S_ISDIR(information.st_mode)
            or stat.S_IMODE(information.st_mode) != mode
        ):
            raise PreparationAuthorityError("custody directory mode or type changed")
        return
    ancestors = _existing_ancestors(path)
    os.mkdir(path, mode)
    information = path.lstat()
    if (
        stat.S_ISLNK(information.st_mode)
        or not stat.S_ISDIR(information.st_mode)
        or stat.S_IMODE(information.st_mode) != mode
        or ancestors != _existing_ancestors(path)
    ):
        raise PreparationAuthorityError("new custody directory changed")
    _fsync_directory(path.parent)


def _event_protocol() -> Dict[str, Any]:
    rows = []
    for ordinal in range(5):
        matrix = EVENT_MATRIX[ordinal]
        rows.append(
            {
                "preparation_event_ordinal": ordinal,
                "allowed_kinds": list(matrix["allowed_kinds"]),
                "payload_schema": matrix["payload_schema"],
                "payload_relative_path": matrix["payload_path"],
                "allowed_outcomes": list(matrix["allowed_outcomes"]),
            }
        )
    body = {
        "schema": "heterodiff-a1-r1-preparation-event-protocol-v2",
        "namespace": "PREPARATION_ONLY",
        "genesis_has_event_ordinal": False,
        "maximum_success_event_count": 5,
        "rejection_terminal_event_count": 4,
        "rows": rows,
        "separate_from_scientific_authority_ordinals_0_through_589": True,
        "operation_nonce_formula": (
            "SHA256(domain || marker_sha256_ascii || NUL || event_kind_ascii)"
        ),
        "immediate_previous_head_required": True,
        "no_mutable_head_file": True,
    }
    return {
        **body,
        "protocol_sha256": _sha256(EVENT_PROTOCOL_DOMAIN + _canonical(body)),
    }


def _scientific_event_protocol(predecessor: Mapping[str, Any]) -> Dict[str, Any]:
    event = predecessor["event_ledger_protocol"]
    body = {
        "predecessor_event_protocol_sha256": event["protocol_sha256"],
        "scientific_event_next_ordinal": event["next_unused_authority_event_ordinal"],
        "scientific_event_range": [0, 589],
        "preparation_event_namespace_is_disjoint": True,
        "scientific_authority_ledger_created": False,
    }
    return {
        **body,
        "protocol_sha256": _sha256(SCIENTIFIC_EVENT_PROTOCOL_DOMAIN + _canonical(body)),
    }


def _path_roster() -> Dict[str, Any]:
    body = {
        "schema": "heterodiff-a1-r1-activation-preparation-path-roster-v2",
        "marker_path": MARKER_PATH,
        "preparation_root": PREPARATION_ROOT,
        "static_paths": list(STATIC_V2_PATHS),
        "static_path_count": len(STATIC_V2_PATHS),
        "dormant_v1_paths_permanently_absent": list(DORMANT_V1_PATHS),
        "dormant_v1_path_count": len(DORMANT_V1_PATHS),
        "permanently_absent_v1_src_adapter": PERMANENTLY_ABSENT_V1_SRC_ADAPTER,
        "capsule_dynamic_paths_bound_only_by_capsule_manifest": True,
        "runtime_candidate_root_allowed_files": ["candidate.json"],
        "raw_capture_envelope_paths_exist": False,
        "runtime_review_approval_final_paths_exist": False,
    }
    return {
        **body,
        "roster_sha256": _sha256(PATH_ROSTER_DOMAIN + _canonical(body)),
    }


def _verify_predecessor(root: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    for relative_path, expected in PREDECESSOR_RAW_SHA256.items():
        if _file_sha256(root, relative_path) != expected:
            raise PreparationAuthorityError("dormant-v1 predecessor bytes changed")
    payload, record = _load_canonical_json(root / PREDECESSOR_MACHINE_PATH)
    if (
        _sha256(payload) != PREDECESSOR_RAW_SHA256[PREDECESSOR_MACHINE_PATH]
        or record.get("record_sha256") != PREDECESSOR_RECORD_SHA256
    ):
        raise PreparationAuthorityError("dormant-v1 registration identity changed")
    try:
        qualification = v1_authority.load_dormant_protocol_qualification(root)
    except (v1_authority.AuthorityProtocolError, OSError, ValueError) as error:
        raise PreparationAuthorityError(
            "dormant-v1 live qualification no longer validates"
        ) from error
    if qualification.record_sha256 != PREDECESSOR_RECORD_SHA256:
        raise PreparationAuthorityError("dormant-v1 live qualification changed")
    for relative_path in DORMANT_V1_PATHS:
        _require_absent(root / relative_path)
    _require_absent(root / PERMANENTLY_ABSENT_V1_SRC_ADAPTER)
    return record, qualification.snapshot()


def _capsule_content_plan(root: Path, predecessor: Mapping[str, Any]) -> Dict[str, Any]:
    v1_plan = predecessor["planned_source_capsule_manifest"]
    source = predecessor["precreation_snapshot"]["qualification_snapshot"][
        "source_manifest"
    ]
    overlay_rules = {
        row["rule"]["path"]: row
        for row in predecessor["precreation_snapshot"]["qualification_snapshot"][
            "overlay_rules"
        ]
    }
    rows = []
    for row in v1_plan["rows"]:
        rule_row = overlay_rules.get(row["source_path"])
        rows.append(
            {
                "ordinal": len(rows),
                "source_role": row["source_role"],
                "source_path": row["source_path"],
                "capsule_relative_path": row["capsule_relative_path"],
                "payload_kind": (
                    "ONE_LITERAL_OVERLAY" if rule_row is not None else "COPIED_BYTES"
                ),
                "overlay_rule": None if rule_row is None else rule_row["rule"],
                "overlay_rule_sha256": (
                    None if rule_row is None else rule_row["rule_sha256"]
                ),
                "bytes": row["bytes"],
                "raw_sha256": row["raw_sha256"],
            }
        )
    protocol_rows = (
        (
            "FROZEN_DORMANT_V1_CONTRACTS_COPY",
            PREDECESSOR_CONTRACTS_PATH,
            v1_plan["contracts_copy_relative_path"],
            _file_sha256(root, PREDECESSOR_CONTRACTS_PATH),
            len(_read_stable_file(root / PREDECESSOR_CONTRACTS_PATH)[0]),
            "COPIED_BYTES",
        ),
        (
            "FROZEN_DORMANT_V1_ADAPTER_COPY",
            PREDECESSOR_RUNTIME_PATH,
            v1_plan["adapter_copy_relative_path"],
            _file_sha256(root, PREDECESSOR_RUNTIME_PATH),
            len(_read_stable_file(root / PREDECESSOR_RUNTIME_PATH)[0]),
            "COPIED_BYTES",
        ),
    )
    for role, source_path, capsule_path, digest, size, kind in protocol_rows:
        rows.append(
            {
                "ordinal": len(rows),
                "source_role": role,
                "source_path": source_path,
                "capsule_relative_path": capsule_path,
                "payload_kind": kind,
                "overlay_rule": None,
                "overlay_rule_sha256": None,
                "bytes": size,
                "raw_sha256": digest,
            }
        )
    bootstrap_payload = _canonical(v1_adapter.frozen_bootstrap_spec()) + b"\n"
    rows.append(
        {
            "ordinal": len(rows),
            "source_role": "FROZEN_DORMANT_V1_BOOTSTRAP_SPEC",
            "source_path": None,
            "capsule_relative_path": v1_plan["bootstrap_spec_copy_relative_path"],
            "payload_kind": "GENERATED_BOOTSTRAP_JSON",
            "overlay_rule": None,
            "overlay_rule_sha256": None,
            "bytes": len(bootstrap_payload),
            "raw_sha256": _sha256(bootstrap_payload),
        }
    )
    if len(rows) != 53 or [row["ordinal"] for row in rows] != list(range(53)):
        raise PreparationAuthorityError("v2 capsule plan is not exactly 53 rows")
    if len({row["capsule_relative_path"] for row in rows}) != 53:
        raise PreparationAuthorityError("v2 capsule plan paths are duplicated")
    directories = {""}
    for row in rows:
        path = PureRelativePath(row["capsule_relative_path"])
        for parent in path.parents:
            if parent != ".":
                directories.add(parent)
    body = {
        "schema": "heterodiff-a1-r1-activation-preparation-capsule-content-plan-v2",
        "capsule_root_relative_path": CAPSULE_ROOT,
        "predecessor_source_manifest_sha256": source["manifest_sha256"],
        "registry_semantic_sha256": predecessor["precreation_snapshot"][
            "qualification_snapshot"
        ]["coordinate_manifests"]["registry_sha256"],
        "row_count": len(rows),
        "rows": rows,
        "directory_count": len(directories),
        "directories": sorted(directories),
        "local_package_source_count": 47,
        "nonpackage_input_count": 3,
        "protocol_copy_count": 3,
        "parent_authority_in_child_import_path": False,
    }
    return {**body, "plan_sha256": _sha256(CAPSULE_PLAN_DOMAIN + _canonical(body))}


class PureRelativePath(str):
    """Validated normalized relative POSIX path used only for custody plans."""

    def __new__(cls, value: Any) -> "PureRelativePath":
        if type(value) is not str or not value or "\\" in value or "\x00" in value:
            raise PreparationAuthorityError("capsule path is not normalized POSIX text")
        path = Path(value)
        if path.is_absolute() or path.as_posix() != value or ".." in path.parts:
            raise PreparationAuthorityError("capsule path escapes its root")
        return str.__new__(cls, value)

    @property
    def parents(self) -> Tuple[str, ...]:
        value = Path(str(self))
        return tuple(parent.as_posix() for parent in value.parents)


def static_qualification_snapshot(workspace_root: Any) -> Dict[str, Any]:
    root = Path(workspace_root).absolute()
    predecessor_record, predecessor = _verify_predecessor(root)
    capsule_plan = _capsule_content_plan(root, predecessor)
    event_protocol = _event_protocol()
    scientific_protocol = _scientific_event_protocol(predecessor)
    path_roster = _path_roster()
    d1 = predecessor["completion_evidence_protocol"]["d1_execution_lineage_quarantine"]
    implementation = {
        "contracts_path": CONTRACTS_PATH,
        "contracts_sha256": _file_sha256(root, CONTRACTS_PATH),
        "authority_path": AUTHORITY_PATH,
        "authority_sha256": _file_sha256(root, AUTHORITY_PATH),
        "runtime_path": RUNTIME_PATH,
        "runtime_sha256": _file_sha256(root, RUNTIME_PATH),
    }
    body = {
        "schema": contracts.QUALIFICATION_SCHEMA,
        "milestone_state": contracts.MILESTONE_STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "live_state_at_freeze": "AWAITING_EXPLICIT_MARKER_AUTHORIZATION",
        "supersedes_only_dormant_v1_activation_path_design": True,
        "dormant_v1_registration_raw_sha256": PREDECESSOR_RAW_SHA256[
            PREDECESSOR_MACHINE_PATH
        ],
        "dormant_v1_registration_record_sha256": PREDECESSOR_RECORD_SHA256,
        "dormant_v1_qualification_snapshot_sha256": _sha256(
            b"heterodiff-a1-r1-dormant-v1-snapshot-binding-v2\0"
            + _canonical(predecessor_record["qualification_snapshot"])
        ),
        "dormant_v1_exact_bindings": [
            {"path": path, "raw_sha256": digest}
            for path, digest in PREDECESSOR_RAW_SHA256.items()
        ],
        "dormant_v1_paths_remain_permanently_absent": True,
        "path_roster": path_roster,
        "capsule_content_plan": capsule_plan,
        "preparation_event_protocol": event_protocol,
        "scientific_event_protocol": scientific_protocol,
        "d1_quarantine": {
            "row_count": d1["row_count"],
            "roster_sha256": d1["roster_sha256"],
            "seed_1729_is_development_only": True,
            "scientific_carrier_rejection_required": True,
            "preparation_records_are_not_scientific_carriers": True,
        },
        "runtime_protocol": {
            "target_profile_id": runtime.TARGET_PROFILE_ID,
            "environment_policy": runtime.environment_policy(),
            "runtime_inspection_oracle_is_outside_scientific_capsule": True,
            "runtime_inspection_oracle_is_nonscientific_preparation_evidence_code": True,
            "runtime_oracle_path": RUNTIME_PATH,
            "runtime_oracle_api_sha256": RUNTIME_ORACLE_API_SHA256,
            "capture_count": 2,
            "raw_capture_envelopes_persisted": False,
            "candidate_not_reusable_as_formal_runtime_approval": True,
            "fresh_approval_recapture_required": True,
            "runtime_review_schema_present": False,
            "runtime_approval_schema_present": False,
            "runtime_final_manifest_schema_present": False,
        },
        "contract_catalog": contracts.contract_catalog(),
        "implementation": implementation,
        "implemented_writer_routes": {
            "precreation_marker_and_nonce": True,
            "deterministic_capsule_materialization_and_admission": True,
            "privacy_safe_runtime_double_capture_candidate": True,
            "preparation_ledger": True,
            "scientific_authority_ledger": False,
        },
        "current_unresolved_null_count": 172,
        "current_open_blocker_count": 12,
        "synthetic_temp_replica_testing_disclosed": True,
        "synthetic_temp_replica_testing_contacted_entropy_or_child_process": False,
        "preparation_sequence_is_nonscientific_and_not_blocked_by_current_preregistration": True,
        "explicit_operator_authorization_required": True,
        "operator_authorization_context": OPERATOR_AUTHORIZATION_CONTEXT,
        "operator_authorization_sha256": OPERATOR_AUTHORIZATION_SHA256,
        "prerequisite_evidence_loadable": False,
        "activation_permitted": False,
        "nonclaims_scope": "CANONICAL_LIVE_WORKSPACE_AT_FREEZE",
        "nonclaims": dict(NONCLAIMS),
    }
    return {
        **body,
        "snapshot_sha256": _sha256(QUALIFICATION_SNAPSHOT_DOMAIN + _canonical(body)),
    }


def next_gate(static: Mapping[str, Any]) -> Dict[str, Any]:
    if static.get("snapshot_sha256") is None:
        raise PreparationAuthorityError("static qualification snapshot is incomplete")
    return {
        "state": "AWAITING_EXPLICIT_MARKER_AUTHORIZATION",
        "explicit_operator_authorization_required": True,
        "operator_authorization_context": OPERATOR_AUTHORIZATION_CONTEXT,
        "operator_authorization_sha256": OPERATOR_AUTHORIZATION_SHA256,
        "irreversible_marker_attempt_warning_required": True,
        "scope_that_exact_future_assent_would_authorize": (
            "V2_MARKER_CAPSULE_AND_EXACTLY_TWO_PRIVACY_SAFE_RUNTIME_INSPECTIONS"
        ),
        "runtime_approval_authorized": False,
        "rank_training_production_scientific_execution_authorized": False,
        "canonical_marker_command": (
            ".venv-m1/bin/python -I -S -B "
            + AUTHORITY_PATH
            + " --create-marker-after-explicit-authorization"
        ),
        "static_snapshot_sha256": static["snapshot_sha256"],
    }


def _registration_bindings(root: Path, rows: Any) -> Dict[str, str]:
    expected = (
        ("HUMAN_REGISTRATION", HUMAN_PATH),
        ("CONTRACTS_MODULE", CONTRACTS_PATH),
        ("AUTHORITY_MODULE", AUTHORITY_PATH),
        ("RUNTIME_MODULE", RUNTIME_PATH),
        ("HOSTILE_TEST", TEST_PATH),
    )
    if type(rows) is not list or len(rows) != len(expected):
        raise PreparationAuthorityError("v2 registration binding count changed")
    result = {}
    for ordinal, (row, (role, relative_path)) in enumerate(zip(rows, expected)):
        payload, information = _read_stable_file(root / relative_path)
        fields = {
            "ordinal",
            "role",
            "path",
            "bytes",
            "raw_sha256",
            "lf_only",
            "is_regular_file",
            "is_symlink",
        }
        if (
            type(row) is not dict
            or set(row) != fields
            or type(row["ordinal"]) is not int
            or row["ordinal"] != ordinal
            or row["role"] != role
            or row["path"] != relative_path
            or type(row["bytes"]) is not int
            or row["bytes"] != len(payload)
            or row["raw_sha256"] != _sha256(payload)
            or row["lf_only"] is not True
            or row["is_regular_file"] is not True
            or row["is_symlink"] is not False
            or b"\r" in payload
            or not stat.S_ISREG(information.st_mode)
            or stat.S_ISLNK(information.st_mode)
        ):
            raise PreparationAuthorityError("v2 registration binding changed")
        result[role] = row["raw_sha256"]
    return result


def _load_registration(root: Path) -> Tuple[bytes, Dict[str, Any], Dict[str, str]]:
    payload, record = _load_canonical_json(root / MACHINE_PATH)
    fields = {
        "schema_version",
        "registration_id",
        "registration_mode",
        "scope",
        "milestone_state",
        "global_state",
        "static_qualification_snapshot",
        "nonclaims",
        "publication_anonymity_boundary",
        "next_gate",
        "registration_bindings",
        "record_sha256",
    }
    if type(record) is not dict or set(record) != fields:
        raise PreparationAuthorityError("v2 registration fields changed")
    claimed = contracts.require_sha256(record["record_sha256"], "record_sha256")
    body = dict(record)
    body["record_sha256"] = None
    if _sha256(REGISTRATION_DOMAIN + _canonical(body)) != claimed:
        raise PreparationAuthorityError("v2 registration self digest changed")
    if (
        record["schema_version"] != contracts.REGISTRATION_SCHEMA
        or record["registration_id"] != REGISTRATION_ID
        or record["registration_mode"]
        != "ADDITIVE_V2_IMPLEMENTATION_FREEZE_ZERO_EXECUTION"
        or record["scope"] != "INTERNAL_PREREGISTRATION_PREPARATION_CUSTODY"
        or record["milestone_state"] != contracts.MILESTONE_STATE
        or record["global_state"] != "DRAFT_NOT_EXECUTABLE"
        or record["nonclaims"] != NONCLAIMS
        or record["publication_anonymity_boundary"] != PUBLICATION_ANONYMITY_BOUNDARY
    ):
        raise PreparationAuthorityError("v2 registration state changed")
    bindings = _registration_bindings(root, record["registration_bindings"])
    fresh = static_qualification_snapshot(root)
    if _canonical(record["static_qualification_snapshot"]) != _canonical(fresh):
        raise PreparationAuthorityError("v2 static qualification changed")
    if record["next_gate"] != next_gate(fresh):
        raise PreparationAuthorityError("v2 next gate changed")
    return payload, record, bindings


def _record_digest(record: Mapping[str, Any]) -> str:
    terminal_by_schema = {
        contracts.ATTEMPT_MARKER_SCHEMA: "marker_sha256",
        contracts.LEDGER_GENESIS_SCHEMA: "genesis_sha256",
        contracts.LEDGER_EVENT_SCHEMA: "event_sha256",
        contracts.OPERATION_NONCE_CLAIM_SCHEMA: "claim_sha256",
        contracts.SOURCE_CAPSULE_MANIFEST_SCHEMA: "manifest_sha256",
        contracts.SOURCE_CAPSULE_ADMISSION_SCHEMA: "admission_sha256",
        contracts.RUNTIME_REQUEST_SCHEMA: "request_sha256",
        contracts.RUNTIME_ENVELOPE_BINDING_SCHEMA: "binding_sha256",
        contracts.RUNTIME_CANDIDATE_SCHEMA: "candidate_sha256",
    }
    schema = record.get("schema")
    if type(schema) is not str or schema not in terminal_by_schema:
        raise PreparationAuthorityError("record schema has no terminal digest mapping")
    key = terminal_by_schema[schema]
    return contracts.require_sha256(record.get(key), key)


def _load_contract(
    root: Path, relative_path: str, contract_id: str
) -> Tuple[bytes, Dict[str, Any]]:
    payload, information = _read_stable_file(root / relative_path)
    if stat.S_IMODE(information.st_mode) != 0o600 or information.st_nlink != 1:
        raise PreparationAuthorityError("operational record mode changed")
    try:
        record = contracts.parse_record(payload, contract_id)
    except contracts.ContractError as error:
        raise PreparationAuthorityError(
            "operational record contract changed"
        ) from error
    return payload, record


def _operation_nonce(marker_sha256: str, operation_kind: str) -> str:
    contracts.require_sha256(marker_sha256, "marker_sha256")
    if type(operation_kind) is not str or not operation_kind:
        raise PreparationAuthorityError("operation kind is invalid")
    return _sha256(
        OPERATION_NONCE_DOMAIN
        + marker_sha256.encode("ascii")
        + b"\0"
        + operation_kind.encode("ascii")
    )


def _launch_binding(preimage_sha256: str, ordinal: int) -> str:
    contracts.require_sha256(preimage_sha256, "launch_binding_preimage_sha256")
    if ordinal not in (0, 1):
        raise PreparationAuthorityError("capture launch ordinal changed")
    return _sha256(
        LAUNCH_BINDING_DOMAIN
        + preimage_sha256.encode("ascii")
        + b"\0"
        + str(ordinal).encode("ascii")
    )


def _event_claim_path(ordinal: int) -> str:
    if ordinal < 0 or ordinal > 4:
        raise PreparationAuthorityError("preparation event ordinal is invalid")
    return EVENT_CLAIM_PATHS[ordinal]


def _event_path(ordinal: int) -> str:
    if ordinal < 0 or ordinal > 4:
        raise PreparationAuthorityError("preparation event ordinal is invalid")
    return EVENT_FILE_PATHS[ordinal]


def _validate_event(
    row: Mapping[str, Any], expected_previous_head: str
) -> Dict[str, Any]:
    checked = contracts.validate_record(dict(row), "LEDGER_EVENT")
    ordinal = checked["preparation_event_ordinal"]
    if ordinal not in EVENT_MATRIX:
        raise PreparationAuthorityError("preparation event ordinal changed")
    matrix = EVENT_MATRIX[ordinal]
    if (
        checked["preparation_event_kind"] not in matrix["allowed_kinds"]
        or checked["payload_schema"] != matrix["payload_schema"]
        or checked["payload_relative_path"] != matrix["payload_path"]
        or checked["event_outcome"] not in matrix["allowed_outcomes"]
        or checked["previous_head_sha256"] != expected_previous_head
        or checked["operation_nonce_sha256"]
        != _operation_nonce(checked["marker_sha256"], checked["preparation_event_kind"])
    ):
        raise PreparationAuthorityError("preparation event discriminant changed")
    if ordinal == 3:
        admitted = checked["preparation_event_kind"] == "RUNTIME_CANDIDATE_ADMITTED"
        if admitted != (
            checked["event_outcome"] == "ADMITTED_UNAPPROVED_PREPARATION_ONLY"
        ):
            raise PreparationAuthorityError("runtime candidate branch is inconsistent")
    if ordinal == 4 and (
        checked["preparation_event_kind"]
        != "PREPARATION_CLOSED_AWAITING_OPERATOR_APPROVAL"
        or checked["event_outcome"] != "CLOSED_AWAITING_OPERATOR_APPROVAL"
    ):
        raise PreparationAuthorityError("preparation closure branch is inconsistent")
    return checked


def _expected_capsule_payload(root: Path, row: Mapping[str, Any]) -> bytes:
    kind = row["payload_kind"]
    if kind == "GENERATED_BOOTSTRAP_JSON":
        payload = _canonical(v1_adapter.frozen_bootstrap_spec()) + b"\n"
    else:
        source_path = row["source_path"]
        if type(source_path) is not str:
            raise PreparationAuthorityError("capsule source path changed")
        payload, _ = _read_stable_file(root / source_path)
        if kind == "ONE_LITERAL_OVERLAY":
            payload = v1_authority._apply_frozen_overlay(payload, row["overlay_rule"])
        elif kind != "COPIED_BYTES":
            raise PreparationAuthorityError("capsule payload kind changed")
    if len(payload) != row["bytes"] or _sha256(payload) != row["raw_sha256"]:
        raise PreparationAuthorityError("capsule source payload identity changed")
    return payload


def _capsule_manifest(
    static: Mapping[str, Any], marker: Mapping[str, Any], genesis: Mapping[str, Any]
) -> Dict[str, Any]:
    plan = static["capsule_content_plan"]
    record = {
        "schema": contracts.SOURCE_CAPSULE_MANIFEST_SCHEMA,
        "marker_sha256": marker["marker_sha256"],
        "genesis_sha256": genesis["genesis_sha256"],
        "capsule_root_relative_path": CAPSULE_ROOT,
        "predecessor_source_manifest_sha256": plan[
            "predecessor_source_manifest_sha256"
        ],
        "registry_semantic_sha256": plan["registry_semantic_sha256"],
        "row_count": 53,
        "directory_count": plan["directory_count"],
        "rows": plan["rows"],
        "protocol_copy_count": 3,
        "local_package_source_count": 47,
        "nonpackage_input_count": 3,
        "parent_authority_in_child_import_path": False,
        "source_capsule_execution_admissible": False,
        "manifest_sha256": None,
    }
    return contracts.finish_record(record, "SOURCE_CAPSULE_MANIFEST")


def _tree_snapshot(root: Path) -> Dict[str, Any]:
    root_information = root.lstat()
    if stat.S_ISLNK(root_information.st_mode) or not stat.S_ISDIR(
        root_information.st_mode
    ):
        raise PreparationAuthorityError("capsule root type changed")
    directories = [("", _stat_identity(root_information))]
    files = []
    for current, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current)
        directory_names.sort()
        file_names.sort()
        if current_path != root:
            relative = current_path.relative_to(root).as_posix()
            information = current_path.lstat()
            if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(
                information.st_mode
            ):
                raise PreparationAuthorityError("capsule directory type changed")
            directories.append((relative, _stat_identity(information)))
        for name in directory_names:
            information = (current_path / name).lstat()
            if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(
                information.st_mode
            ):
                raise PreparationAuthorityError("capsule directory link detected")
        for name in file_names:
            path = current_path / name
            information = path.lstat()
            if stat.S_ISLNK(information.st_mode) or not stat.S_ISREG(
                information.st_mode
            ):
                raise PreparationAuthorityError("capsule file type changed")
            files.append(
                (path.relative_to(root).as_posix(), _stat_identity(information))
            )
    return {"directories": sorted(directories), "files": sorted(files)}


def _audit_capsule(
    root: Path, static: Mapping[str, Any], manifest: Mapping[str, Any]
) -> Dict[str, Any]:
    capsule = root / CAPSULE_ROOT
    before = _tree_snapshot(capsule)
    plan = static["capsule_content_plan"]
    expected_paths = [row["capsule_relative_path"] for row in plan["rows"]]
    expected_directories = plan["directories"]
    if [row[0] for row in before["files"]] != sorted(expected_paths):
        raise PreparationAuthorityError("capsule has missing or extra files")
    if [row[0] for row in before["directories"]] != sorted(expected_directories):
        raise PreparationAuthorityError("capsule has missing or extra directories")

    def read_inventory() -> list[Dict[str, Any]]:
        inventory = []
        overlay_count = 0
        for row in plan["rows"]:
            path = capsule / row["capsule_relative_path"]
            payload, information = _read_stable_file(path)
            if (
                payload != _expected_capsule_payload(root, row)
                or stat.S_IMODE(information.st_mode) != 0o600
                or information.st_nlink != 1
                or path.suffix == ".pyc"
            ):
                raise PreparationAuthorityError("capsule row custody changed")
            if row["payload_kind"] == "ONE_LITERAL_OVERLAY":
                overlay_count += 1
                rule = row["overlay_rule"]
                try:
                    module = ast.parse(payload.decode("utf-8"))
                except (UnicodeDecodeError, SyntaxError) as error:
                    raise PreparationAuthorityError(
                        "overlaid capsule source is not valid Python"
                    ) from error
                assignments = []
                for statement in module.body:
                    if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
                        continue
                    targets = (
                        statement.targets
                        if isinstance(statement, ast.Assign)
                        else [statement.target]
                    )
                    if any(
                        isinstance(target, ast.Name)
                        and target.id == rule["constant_name"]
                        for target in targets
                    ):
                        assignments.append(statement.value)
                if len(assignments) != 1 or not isinstance(assignments[0], ast.Tuple):
                    raise PreparationAuthorityError(
                        "overlaid registry assignment changed"
                    )
                values = []
                for element in assignments[0].elts:
                    if (
                        not isinstance(element, ast.Constant)
                        or type(element.value) is not int
                    ):
                        raise PreparationAuthorityError(
                            "overlaid registry contains a non-integer"
                        )
                    values.append(element.value)
                if tuple(values) != FROZEN_REGISTRY or 1729 in values:
                    raise PreparationAuthorityError(
                        "overlaid registry semantics changed"
                    )
            inventory.append(
                {
                    "ordinal": row["ordinal"],
                    "path": row["capsule_relative_path"],
                    "bytes": len(payload),
                    "raw_sha256": _sha256(payload),
                    "mode_octal": "0600",
                }
            )
        if overlay_count != 5:
            raise PreparationAuthorityError("capsule overlay count changed")
        return inventory

    inventory_rows = read_inventory()
    second_inventory_rows = read_inventory()
    for relative, _ in before["directories"]:
        information = (capsule / relative).lstat() if relative else capsule.lstat()
        if stat.S_IMODE(information.st_mode) != 0o700:
            raise PreparationAuthorityError("capsule directory mode changed")
    after = _tree_snapshot(capsule)
    if before != after or inventory_rows != second_inventory_rows:
        raise PreparationAuthorityError("capsule tree changed during audit")
    body = {
        "manifest_sha256": manifest["manifest_sha256"],
        "rows": inventory_rows,
        "directories": sorted(expected_directories),
    }
    return {
        "inventory_sha256": _sha256(INVENTORY_DOMAIN + _canonical(body)),
        "file_count": len(inventory_rows),
        "directory_count": len(expected_directories),
    }


def _capsule_admission(
    root: Path,
    static: Mapping[str, Any],
    marker: Mapping[str, Any],
    genesis: Mapping[str, Any],
    manifest_payload: bytes,
    manifest: Mapping[str, Any],
) -> Dict[str, Any]:
    inventory = _audit_capsule(root, static, manifest)
    record = {
        "schema": contracts.SOURCE_CAPSULE_ADMISSION_SCHEMA,
        "marker_sha256": marker["marker_sha256"],
        "genesis_sha256": genesis["genesis_sha256"],
        "manifest_raw_sha256": _sha256(manifest_payload),
        "manifest_sha256": manifest["manifest_sha256"],
        "capsule_root_relative_path": CAPSULE_ROOT,
        "file_count": 53,
        "directory_count": inventory["directory_count"],
        "inventory_sha256": inventory["inventory_sha256"],
        "all_rows_reopened_twice": True,
        "regular_files_only": True,
        "no_symlinks": True,
        "no_hardlinks": True,
        "no_extra_files": True,
        "no_extra_directories": True,
        "no_pyc": True,
        "owner_only_modes": True,
        "registry_seed_1729_absent": True,
        "scientific_execution_performed": False,
        "execution_admissible": False,
        "admission_sha256": None,
    }
    return contracts.finish_record(record, "SOURCE_CAPSULE_ADMISSION")


def _preparation_instance_nonce(raw: bytes) -> str:
    if type(raw) is not bytes or len(raw) != ENTROPY_BYTE_COUNT:
        raise PreparationAuthorityError("preparation entropy is not exactly 32 bytes")
    return _sha256(PREPARATION_NONCE_DOMAIN + raw)


def _marker_record(
    registration_payload: bytes,
    registration: Mapping[str, Any],
    bindings: Mapping[str, str],
    nonce_sha256: str,
) -> Dict[str, Any]:
    static = registration["static_qualification_snapshot"]
    record = {
        "schema": contracts.ATTEMPT_MARKER_SCHEMA,
        "registration_raw_sha256": _sha256(registration_payload),
        "registration_record_sha256": registration["record_sha256"],
        "predecessor_registration_raw_sha256": PREDECESSOR_RAW_SHA256[
            PREDECESSOR_MACHINE_PATH
        ],
        "predecessor_registration_record_sha256": PREDECESSOR_RECORD_SHA256,
        "predecessor_qualification_snapshot_sha256": static[
            "dormant_v1_qualification_snapshot_sha256"
        ],
        "human_sha256": bindings["HUMAN_REGISTRATION"],
        "contracts_sha256": bindings["CONTRACTS_MODULE"],
        "authority_sha256": bindings["AUTHORITY_MODULE"],
        "runtime_sha256": bindings["RUNTIME_MODULE"],
        "test_sha256": bindings["HOSTILE_TEST"],
        "path_roster_sha256": static["path_roster"]["roster_sha256"],
        "d1_quarantine_roster_sha256": static["d1_quarantine"]["roster_sha256"],
        "operator_authorization_context": OPERATOR_AUTHORIZATION_CONTEXT,
        "operator_authorization_sha256": OPERATOR_AUTHORIZATION_SHA256,
        "preparation_instance_nonce_sha256": nonce_sha256,
        "entropy_source": "secrets.token_bytes",
        "entropy_byte_count": 32,
        "raw_entropy_persisted": False,
        "exclusive_inode_reserved_before_entropy": True,
        "all_dormant_v1_paths_absent_after_reservation": True,
        "v2_root_absent_after_reservation": True,
        "scientific_campaign_nonce_minted": False,
        "attempt_state": ("PREPARATION_ATTEMPT_SPENT_TERMINAL_MARKER_CREATED_NO_RETRY"),
        "marker_sha256": None,
    }
    return contracts.finish_record(record, "ATTEMPT_MARKER")


def _genesis_record(
    registration_payload: bytes,
    registration: Mapping[str, Any],
    marker_payload: bytes,
    marker: Mapping[str, Any],
) -> Dict[str, Any]:
    static = registration["static_qualification_snapshot"]
    record = {
        "schema": contracts.LEDGER_GENESIS_SCHEMA,
        "marker_raw_sha256": _sha256(marker_payload),
        "marker_sha256": marker["marker_sha256"],
        "registration_raw_sha256": _sha256(registration_payload),
        "registration_record_sha256": registration["record_sha256"],
        "predecessor_registration_record_sha256": PREDECESSOR_RECORD_SHA256,
        "predecessor_qualification_snapshot_sha256": static[
            "dormant_v1_qualification_snapshot_sha256"
        ],
        "preparation_instance_nonce_sha256": marker[
            "preparation_instance_nonce_sha256"
        ],
        "path_roster_sha256": static["path_roster"]["roster_sha256"],
        "source_capsule_plan_sha256": static["capsule_content_plan"]["plan_sha256"],
        "registry_semantic_sha256": static["capsule_content_plan"][
            "registry_semantic_sha256"
        ],
        "d1_quarantine_roster_sha256": static["d1_quarantine"]["roster_sha256"],
        "preparation_event_protocol_sha256": static["preparation_event_protocol"][
            "protocol_sha256"
        ],
        "scientific_event_protocol_sha256": static["scientific_event_protocol"][
            "protocol_sha256"
        ],
        "writer_lock_relative_path": LEDGER_LOCK_PATH,
        "next_preparation_event_ordinal": 0,
        "scientific_authority_ledger_created": False,
        "scientific_campaign_nonce_minted": False,
        "genesis_sha256": None,
    }
    return contracts.finish_record(record, "LEDGER_GENESIS")


def _nonce_claim(
    marker: Mapping[str, Any],
    genesis: Mapping[str, Any],
    claim_scope: str,
    ordinal: int | None,
    operation_kind: str,
    previous_head_sha256: str,
    recovery_policy: str,
) -> Dict[str, Any]:
    record = {
        "schema": contracts.OPERATION_NONCE_CLAIM_SCHEMA,
        "marker_sha256": marker["marker_sha256"],
        "genesis_sha256": genesis["genesis_sha256"],
        "preparation_instance_nonce_sha256": marker[
            "preparation_instance_nonce_sha256"
        ],
        "claim_scope": claim_scope,
        "preparation_event_ordinal": ordinal,
        "operation_kind": operation_kind,
        "operation_nonce_sha256": _operation_nonce(
            marker["marker_sha256"], operation_kind
        ),
        "previous_head_sha256": previous_head_sha256,
        "recovery_policy": recovery_policy,
        "claim_state": "OPERATION_NONCE_SPENT",
        "claim_sha256": None,
    }
    return contracts.finish_record(record, "OPERATION_NONCE_CLAIM")


def _event_record(
    marker: Mapping[str, Any],
    genesis: Mapping[str, Any],
    ordinal: int,
    kind: str,
    previous_head_sha256: str,
    claim: Mapping[str, Any],
    payload_path: str,
    payload_bytes: bytes,
    payload_record: Mapping[str, Any],
    outcome: str,
) -> Dict[str, Any]:
    matrix = EVENT_MATRIX[ordinal]
    if (
        kind not in matrix["allowed_kinds"]
        or outcome not in matrix["allowed_outcomes"]
        or payload_path != matrix["payload_path"]
        or payload_record.get("schema") != matrix["payload_schema"]
    ):
        raise PreparationAuthorityError("event payload discriminant changed")
    record = {
        "schema": contracts.LEDGER_EVENT_SCHEMA,
        "marker_sha256": marker["marker_sha256"],
        "genesis_sha256": genesis["genesis_sha256"],
        "preparation_instance_nonce_sha256": marker[
            "preparation_instance_nonce_sha256"
        ],
        "preparation_event_ordinal": ordinal,
        "preparation_event_kind": kind,
        "previous_head_sha256": previous_head_sha256,
        "operation_nonce_sha256": claim["operation_nonce_sha256"],
        "nonce_claim_sha256": claim["claim_sha256"],
        "payload_schema": payload_record["schema"],
        "payload_relative_path": payload_path,
        "payload_raw_sha256": _sha256(payload_bytes),
        "payload_record_sha256": _record_digest(payload_record),
        "event_outcome": outcome,
        "scientific_authority_event_ordinal": None,
        "rank_execution_performed": False,
        "training_execution_performed": False,
        "scientific_execution_performed": False,
        "event_sha256": None,
    }
    finished = contracts.finish_record(record, "LEDGER_EVENT")
    return _validate_event(finished, previous_head_sha256)


def _ensure_preparation_directories(root: Path, live_action: str | None = None) -> None:
    _guard_canonical_mutation(root, live_action)
    _ensure_directory(root / PREPARATION_ROOT, live_action=live_action)
    _ensure_directory(root / LEDGER_ROOT, live_action=live_action)
    _ensure_directory(root / LEDGER_EVENTS_ROOT, live_action=live_action)
    _ensure_directory(root / LEDGER_NONCE_ROOT, live_action=live_action)
    _ensure_directory(root / LEDGER_RECEIPTS_ROOT, live_action=live_action)
    _ensure_directory(root / RUNTIME_CANDIDATE_ROOT, live_action=live_action)
    lock_path = root / LEDGER_LOCK_PATH
    if not _path_has_entry(lock_path):
        _write_new_file(lock_path, b"", 0o600, live_action=live_action)
    else:
        payload, information = _read_stable_file(lock_path)
        if payload != b"" or stat.S_IMODE(information.st_mode) != 0o600:
            raise PreparationAuthorityError("writer lock custody changed")


def _acquire_writer_lock(root: Path) -> int:
    path = root / LEDGER_LOCK_PATH
    ancestors = _existing_ancestors(path)
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise PreparationAuthorityError("writer lock path type changed")
    descriptor = os.open(path, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        if (
            _stat_identity(opened) != _stat_identity(before)
            or opened.st_nlink != 1
            or stat.S_IMODE(opened.st_mode) != 0o600
        ):
            raise PreparationAuthorityError("writer lock fd custody changed")
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        after = path.lstat()
        if ancestors != _existing_ancestors(path) or _stat_identity(
            opened
        ) != _stat_identity(after):
            raise PreparationAuthorityError("writer lock path changed after flock")
    except (OSError, PreparationAuthorityError):
        os.close(descriptor)
        raise PreparationAuthorityError(
            "preparation authority writer lock is invalid or already active"
        )
    return descriptor


def _acquire_marker_bootstrap_lock(root: Path) -> int:
    path = root / MARKER_PATH
    ancestors = _existing_ancestors(path)
    before = path.lstat()
    descriptor = os.open(path, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    try:
        information = os.fstat(descriptor)
        if (
            not stat.S_ISREG(information.st_mode)
            or information.st_nlink != 1
            or stat.S_IMODE(information.st_mode) != 0o600
            or _stat_identity(information) != _stat_identity(before)
        ):
            raise PreparationAuthorityError("marker bootstrap lock custody changed")
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        after = path.lstat()
        if ancestors != _existing_ancestors(path) or _stat_identity(
            information
        ) != _stat_identity(after):
            raise PreparationAuthorityError("marker bootstrap lock path changed")
    except Exception:
        os.close(descriptor)
        raise
    return descriptor


def _ensure_genesis(
    root: Path,
    registration_payload: bytes,
    registration: Mapping[str, Any],
    marker_payload: bytes,
    marker: Mapping[str, Any],
    live_action: str | None = None,
) -> Dict[str, Any]:
    _guard_canonical_mutation(root, live_action)
    before_state = _audit_preparation_prefix(root)
    if "TERMINAL" in before_state["live_state"]:
        raise PreparationAuthorityError("genesis refuses a terminal preparation state")
    marker_descriptor = _acquire_marker_bootstrap_lock(root)
    try:
        _ensure_preparation_directories(root, live_action)
        descriptor = _acquire_writer_lock(root)
        try:
            expected = _genesis_record(
                registration_payload, registration, marker_payload, marker
            )
            path = root / LEDGER_GENESIS_PATH
            if not _path_has_entry(path):
                _write_new_file(
                    path, _canonical(expected) + b"\n", live_action=live_action
                )
            _, observed = _load_contract(root, LEDGER_GENESIS_PATH, "LEDGER_GENESIS")
            if _canonical(observed) != _canonical(expected):
                raise PreparationAuthorityError(
                    "ledger genesis differs from frozen marker"
                )
            after_state = _audit_preparation_prefix(root)
            if "TERMINAL" in after_state["live_state"]:
                raise PreparationAuthorityError(
                    "genesis publication failed the full prefix scan"
                )
            return observed
        finally:
            os.close(descriptor)
    finally:
        os.close(marker_descriptor)


def _marker_static_revalidation(
    root: Path,
) -> Tuple[bytes, Dict[str, Any], Dict[str, str]]:
    registration_payload, registration, bindings = _load_registration(root)
    for relative_path in DORMANT_V1_PATHS:
        _require_absent(root / relative_path)
    _require_absent(root / PERMANENTLY_ABSENT_V1_SRC_ADAPTER)
    return registration_payload, registration, bindings


def _reserve_marker_inode(root: Path, live_action: str | None = None) -> int:
    _guard_canonical_mutation(root, live_action)
    artifacts = root / "artifacts"
    information = artifacts.lstat()
    if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(information.st_mode):
        raise PreparationAuthorityError(
            "artifacts parent is not a nonsymlink directory"
        )
    marker = root / MARKER_PATH
    ancestors = _existing_ancestors(marker)
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(marker, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        opened = os.fstat(descriptor)
        observed = marker.lstat()
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or stat.S_IMODE(opened.st_mode) != 0o600
            or opened.st_dev != observed.st_dev
            or opened.st_ino != observed.st_ino
            or ancestors != _existing_ancestors(marker)
        ):
            raise PreparationAuthorityError("reserved marker inode custody changed")
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.fsync(descriptor)
        _fsync_directory(marker.parent)
        after = os.fstat(descriptor)
        after_path = marker.lstat()
        if (
            after.st_dev != opened.st_dev
            or after.st_ino != opened.st_ino
            or after.st_nlink != 1
            or after_path.st_dev != opened.st_dev
            or after_path.st_ino != opened.st_ino
        ):
            raise PreparationAuthorityError("reserved marker inode changed")
    except Exception:
        os.close(descriptor)
        raise
    return descriptor


def _publish_marker_on_reserved_descriptor(
    root: Path, descriptor: int, payload: bytes
) -> Any:
    marker_path = root / MARKER_PATH
    before = os.fstat(descriptor)
    os.lseek(descriptor, 0, os.SEEK_SET)
    _write_all(descriptor, payload)
    os.ftruncate(descriptor, len(payload))
    os.fsync(descriptor)
    after = os.fstat(descriptor)
    observed = marker_path.lstat()
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or after.st_nlink != 1
        or stat.S_IMODE(after.st_mode) != 0o600
        or after.st_size != len(payload)
        or observed.st_dev != after.st_dev
        or observed.st_ino != after.st_ino
    ):
        raise PreparationAuthorityError("marker inode changed during publication")
    _fsync_directory(marker_path.parent)
    return after


def _complete_reserved_marker_synthetic(
    root: Path,
    descriptor: int,
    registration_payload: bytes,
    registration: Mapping[str, Any],
    bindings: Mapping[str, str],
    raw_nonce: bytes,
) -> Tuple[bytes, Dict[str, Any]]:
    if _is_canonical_root(root):
        raise PreparationAuthorityError(
            "synthetic marker publisher refuses canonical workspace"
        )
    marker = _marker_record(
        registration_payload,
        registration,
        bindings,
        _preparation_instance_nonce(raw_nonce),
    )
    payload = _canonical(marker) + b"\n"
    _publish_marker_on_reserved_descriptor(root, descriptor, payload)
    return payload, marker


def _execute_marker_live() -> None:
    root = _require_live_cli_boundary("--create-marker-after-explicit-authorization")
    registration_payload, registration, bindings = _marker_static_revalidation(root)
    if _audit_preparation_prefix(root)["live_state"] != (
        "AWAITING_EXPLICIT_MARKER_AUTHORIZATION"
    ):
        raise PreparationAuthorityError("marker attempt is not in its initial state")
    _require_absent(root / MARKER_PATH)
    _require_absent(root / PREPARATION_ROOT)
    action = "--create-marker-after-explicit-authorization"
    descriptor = _reserve_marker_inode(root, action)
    try:
        _marker_static_revalidation(root)
        _require_absent(root / PREPARATION_ROOT)
        raw_nonce = secrets.token_bytes(32)
        _guard_canonical_mutation(root, action)
        marker = _marker_record(
            registration_payload,
            registration,
            bindings,
            _preparation_instance_nonce(raw_nonce),
        )
        marker_payload = _canonical(marker) + b"\n"
        published = _publish_marker_on_reserved_descriptor(
            root, descriptor, marker_payload
        )
        raw_nonce = b""
    finally:
        os.close(descriptor)
    reopened, observed = _load_contract(root, MARKER_PATH, "ATTEMPT_MARKER")
    if (
        reopened != marker_payload
        or observed != marker
        or (root / MARKER_PATH).lstat().st_dev != published.st_dev
        or (root / MARKER_PATH).lstat().st_ino != published.st_ino
    ):
        raise PreparationAuthorityError("marker changed after publication")
    _marker_static_revalidation(root)
    _ensure_genesis(
        root,
        registration_payload,
        registration,
        marker_payload,
        marker,
        action,
    )
    if "TERMINAL" in _audit_preparation_prefix(root)["live_state"]:
        raise PreparationAuthorityError("marker sequence failed its final prefix scan")


def _test_publish_marker(root: Path, raw_nonce: bytes) -> Dict[str, Any]:
    if root.resolve() == WORKSPACE_ROOT.resolve():
        raise PreparationAuthorityError("test marker helper refuses canonical root")
    registration_payload, registration, bindings = _load_registration(root)
    _require_absent(root / MARKER_PATH)
    _require_absent(root / PREPARATION_ROOT)
    descriptor = _reserve_marker_inode(root)
    try:
        payload, marker = _complete_reserved_marker_synthetic(
            root,
            descriptor,
            registration_payload,
            registration,
            bindings,
            raw_nonce,
        )
    finally:
        os.close(descriptor)
    _ensure_genesis(root, registration_payload, registration, payload, marker)
    return marker


def _load_marker_and_genesis(
    root: Path,
) -> Tuple[bytes, Dict[str, Any], bytes, Dict[str, Any]]:
    marker_payload, marker = _load_contract(root, MARKER_PATH, "ATTEMPT_MARKER")
    genesis_payload, genesis = _load_contract(
        root, LEDGER_GENESIS_PATH, "LEDGER_GENESIS"
    )
    if (
        genesis["marker_raw_sha256"] != _sha256(marker_payload)
        or genesis["marker_sha256"] != marker["marker_sha256"]
        or genesis["preparation_instance_nonce_sha256"]
        != marker["preparation_instance_nonce_sha256"]
    ):
        raise PreparationAuthorityError("marker and genesis are not linked")
    return marker_payload, marker, genesis_payload, genesis


def _claim_or_load(
    root: Path,
    relative_path: str,
    expected: Mapping[str, Any],
    live_action: str | None = None,
) -> Dict[str, Any]:
    if not _path_has_entry(root / relative_path):
        _write_new_file(
            root / relative_path,
            _canonical(expected) + b"\n",
            live_action=live_action,
        )
    _, observed = _load_contract(root, relative_path, "OPERATION_NONCE_CLAIM")
    if _canonical(observed) != _canonical(expected):
        raise PreparationAuthorityError("operation nonce claim changed")
    return observed


def _write_or_load_record(
    root: Path,
    relative_path: str,
    contract_id: str,
    expected: Mapping[str, Any],
    live_action: str | None = None,
) -> Tuple[bytes, Dict[str, Any]]:
    if not _path_has_entry(root / relative_path):
        _write_new_file(
            root / relative_path,
            _canonical(expected) + b"\n",
            live_action=live_action,
        )
    payload, observed = _load_contract(root, relative_path, contract_id)
    if _canonical(observed) != _canonical(expected):
        raise PreparationAuthorityError("deterministic operational record changed")
    return payload, observed


def _write_or_load_event(
    root: Path,
    ordinal: int,
    expected: Mapping[str, Any],
    live_action: str | None = None,
) -> Dict[str, Any]:
    relative_path = _event_path(ordinal)
    if not _path_has_entry(root / relative_path):
        _write_new_file(
            root / relative_path,
            _canonical(expected) + b"\n",
            live_action=live_action,
        )
    _, observed = _load_contract(root, relative_path, "LEDGER_EVENT")
    if _canonical(observed) != _canonical(expected):
        raise PreparationAuthorityError("preparation ledger event changed")
    return observed


def _event_head(root: Path, genesis: Mapping[str, Any], through: int) -> str:
    head = genesis["genesis_sha256"]
    for ordinal in range(through + 1):
        _, event = _load_contract(root, _event_path(ordinal), "LEDGER_EVENT")
        event = _validate_event(event, head)
        head = event["event_sha256"]
    return head


def _materialize_missing_capsule_rows(
    root: Path, static: Mapping[str, Any], live_action: str | None = None
) -> None:
    _guard_canonical_mutation(root, live_action)
    capsule = root / CAPSULE_ROOT
    _ensure_directory(capsule, live_action=live_action)
    for relative in static["capsule_content_plan"]["directories"]:
        if relative:
            current = capsule
            for part in Path(relative).parts:
                current = current / part
                _ensure_directory(current, live_action=live_action)
    for row in static["capsule_content_plan"]["rows"]:
        payload = _expected_capsule_payload(root, row)
        path = capsule / row["capsule_relative_path"]
        if not _path_has_entry(path):
            _write_new_file(path, payload, 0o600, live_action=live_action)
        else:
            observed, information = _read_stable_file(path)
            if (
                observed != payload
                or stat.S_IMODE(information.st_mode) != 0o600
                or information.st_nlink != 1
            ):
                raise PreparationAuthorityError(
                    "partial capsule row differs; resume is forbidden"
                )
    for relative in reversed(static["capsule_content_plan"]["directories"]):
        _fsync_directory(capsule / relative if relative else capsule)


def _execute_capsule_at_root(
    root: Path, live_action: str | None = None
) -> Dict[str, Any]:
    _guard_canonical_mutation(root, live_action)
    before_state = _audit_preparation_prefix(root)
    if "TERMINAL" in before_state["live_state"]:
        raise PreparationAuthorityError("capsule writer refuses terminal custody")
    registration_payload, registration, _ = _load_registration(root)
    del registration_payload
    static = registration["static_qualification_snapshot"]
    _, marker, _, genesis = _load_marker_and_genesis(root)
    descriptor = _acquire_writer_lock(root)
    try:
        claim1_present = _path_has_entry(root / _event_claim_path(1))
        admission_present = _path_has_entry(root / CAPSULE_ADMISSION_PATH)
        event1_present = _path_has_entry(root / _event_path(1))
        if admission_present and not claim1_present:
            raise PreparationAuthorityError(
                "capsule admission exists without its prior nonce claim"
            )
        if event1_present and (not claim1_present or not admission_present):
            raise PreparationAuthorityError(
                "capsule event exists without complete admission custody"
            )
        if _path_has_entry(root / _event_path(1)):
            manifest_payload, manifest = _load_contract(
                root, CAPSULE_MANIFEST_PATH, "SOURCE_CAPSULE_MANIFEST"
            )
            _, observed_admission = _load_contract(
                root, CAPSULE_ADMISSION_PATH, "SOURCE_CAPSULE_ADMISSION"
            )
            expected_admission = _capsule_admission(
                root, static, marker, genesis, manifest_payload, manifest
            )
            if observed_admission != expected_admission:
                raise PreparationAuthorityError(
                    "post-admission capsule custody changed; repair is forbidden"
                )
            after_state = _audit_preparation_prefix(root)
            if "TERMINAL" in after_state["live_state"]:
                raise PreparationAuthorityError("capsule reopen failed full scan")
            return observed_admission
        head = genesis["genesis_sha256"]
        manifest = _capsule_manifest(static, marker, genesis)
        claim0 = _nonce_claim(
            marker,
            genesis,
            "PREPARATION_EVENT",
            0,
            "CAPSULE_MATERIALIZATION_OPENED",
            head,
            "DETERMINISTIC_MISSING_ROWS_MAY_RESUME",
        )
        claim0 = _claim_or_load(root, _event_claim_path(0), claim0, live_action)
        manifest_payload, manifest = _write_or_load_record(
            root,
            CAPSULE_MANIFEST_PATH,
            "SOURCE_CAPSULE_MANIFEST",
            manifest,
            live_action,
        )
        event0 = _event_record(
            marker,
            genesis,
            0,
            "CAPSULE_MATERIALIZATION_OPENED",
            head,
            claim0,
            CAPSULE_MANIFEST_PATH,
            manifest_payload,
            manifest,
            "OPENED",
        )
        event0 = _write_or_load_event(root, 0, event0, live_action)
        if claim1_present:
            _audit_capsule(root, static, manifest)
        else:
            _materialize_missing_capsule_rows(root, static, live_action)
        materialized_state = _audit_preparation_prefix(root)
        if materialized_state["live_state"] != (
            "CAPSULE_MATERIALIZATION_OPENED_RESUMABLE"
        ):
            raise PreparationAuthorityError(
                "capsule materialization failed its pre-admission full scan"
            )
        admission = _capsule_admission(
            root, static, marker, genesis, manifest_payload, manifest
        )
        pre_admission_state = _audit_preparation_prefix(root)
        if pre_admission_state["live_state"] != (
            "CAPSULE_MATERIALIZATION_OPENED_RESUMABLE"
        ):
            raise PreparationAuthorityError(
                "capsule admission failed its immediate pre-publication scan"
            )
        claim1 = _nonce_claim(
            marker,
            genesis,
            "PREPARATION_EVENT",
            1,
            "CAPSULE_ADMITTED",
            event0["event_sha256"],
            "DETERMINISTIC_MISSING_ROWS_MAY_RESUME",
        )
        claim1 = _claim_or_load(root, _event_claim_path(1), claim1, live_action)
        admission_payload, admission = _write_or_load_record(
            root,
            CAPSULE_ADMISSION_PATH,
            "SOURCE_CAPSULE_ADMISSION",
            admission,
            live_action,
        )
        event1 = _event_record(
            marker,
            genesis,
            1,
            "CAPSULE_ADMITTED",
            event0["event_sha256"],
            claim1,
            CAPSULE_ADMISSION_PATH,
            admission_payload,
            admission,
            "ADMITTED_PREPARATION_CUSTODY_ONLY",
        )
        _write_or_load_event(root, 1, event1, live_action)
        after_state = _audit_preparation_prefix(root)
        if "TERMINAL" in after_state["live_state"]:
            raise PreparationAuthorityError("capsule publication failed full scan")
        return admission
    finally:
        os.close(descriptor)


def _runtime_request(
    marker: Mapping[str, Any],
    genesis: Mapping[str, Any],
    manifest: Mapping[str, Any],
    admission: Mapping[str, Any],
) -> Dict[str, Any]:
    provisional = {
        "schema": contracts.RUNTIME_REQUEST_SCHEMA,
        "marker_sha256": marker["marker_sha256"],
        "genesis_sha256": genesis["genesis_sha256"],
        "preparation_instance_nonce_sha256": marker[
            "preparation_instance_nonce_sha256"
        ],
        "source_capsule_manifest_sha256": manifest["manifest_sha256"],
        "source_capsule_admission_sha256": admission["admission_sha256"],
        "target_profile_id": runtime.TARGET_PROFILE_ID,
        "capture_operation": "EXACTLY_TWO_CAPTURES_NO_SCIENTIFIC_COMPUTE",
        "capture_count": 2,
        "capture_ordinals": [0, 1],
        "python_relative_path": runtime.PYTHON_RELATIVE_PATH,
        "capsule_root_relative_path": CAPSULE_ROOT,
        "site_packages_relative_path": runtime.SITE_PACKAGES_RELATIVE_PATH,
        "python_flags": list(runtime.PYTHON_FLAGS),
        "environment_policy_sha256": runtime.environment_policy()["policy_sha256"],
        "launch_binding_preimage_sha256": "0" * 64,
        "launch_binding_a_sha256": "0" * 64,
        "launch_binding_b_sha256": "0" * 64,
        "raw_capture_envelopes_persisted": False,
        "scientific_compute_requested": False,
        "runtime_approval_requested": False,
        "request_sha256": None,
    }
    seed_body = dict(provisional)
    seed_body["launch_binding_preimage_sha256"] = None
    seed_body["launch_binding_a_sha256"] = None
    seed_body["launch_binding_b_sha256"] = None
    seed_body["request_sha256"] = None
    request_seed = _sha256(
        b"heterodiff-a1-r1-runtime-request-launch-seed-v2\0" + _canonical(seed_body)
    )
    provisional["launch_binding_preimage_sha256"] = request_seed
    provisional["launch_binding_a_sha256"] = _launch_binding(request_seed, 0)
    provisional["launch_binding_b_sha256"] = _launch_binding(request_seed, 1)
    finished = contracts.finish_record(provisional, "RUNTIME_REQUEST")
    # Launch identities are bound to a preimage seed to avoid a request/self cycle.
    return runtime.validate_runtime_request(finished)


def _run_runtime_child(
    request_payload: bytes,
    ordinal: int,
    expected_runtime_sha256: str,
    expected_contracts_sha256: str,
) -> Tuple[bytes, Dict[str, Any]]:
    if ordinal not in (0, 1):
        raise PreparationAuthorityError("runtime child ordinal changed")
    if (
        _file_sha256(WORKSPACE_ROOT, RUNTIME_PATH) != expected_runtime_sha256
        or _file_sha256(WORKSPACE_ROOT, CONTRACTS_PATH) != expected_contracts_sha256
    ):
        raise PreparationAuthorityError("runtime inspection oracle bytes changed")
    command = [
        (WORKSPACE_ROOT / runtime.PYTHON_RELATIVE_PATH).as_posix(),
        *runtime.PYTHON_FLAGS,
        RUNTIME_PATH,
        "--capture-a" if ordinal == 0 else "--capture-b",
    ]
    process = subprocess.Popen(
        command,
        cwd=WORKSPACE_ROOT,
        env=dict(runtime.CAPTURE_ENVIRONMENT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.stdin is None or process.stdout is None or process.stderr is None:
        process.kill()
        process.wait()
        raise PreparationAuthorityError("runtime capture pipes are unavailable")
    try:
        process.stdin.write(request_payload)
        process.stdin.flush()
        process.stdin.close()
        os.set_blocking(process.stdout.fileno(), False)
        os.set_blocking(process.stderr.fileno(), False)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        stdout_chunks = []
        stderr_chunks = []
        stdout_count = 0
        stderr_count = 0
        deadline = time.monotonic() + 900.0
        while selector.get_map():
            if time.monotonic() >= deadline:
                raise PreparationAuthorityError("runtime capture child timed out")
            for key, _ in selector.select(timeout=0.25):
                chunk = os.read(key.fileobj.fileno(), 1 << 20)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                if key.data == "stdout":
                    stdout_count += len(chunk)
                    if stdout_count > runtime.MAXIMUM_RAW_ENVELOPE_BYTES:
                        raise PreparationAuthorityError(
                            "runtime capture stdout exceeded its hard bound"
                        )
                    stdout_chunks.append(chunk)
                else:
                    stderr_count += len(chunk)
                    if stderr_count > 1 << 20:
                        raise PreparationAuthorityError(
                            "runtime capture stderr exceeded its hard bound"
                        )
                    stderr_chunks.append(chunk)
        exit_code = process.wait(timeout=5)
    except Exception:
        process.kill()
        process.wait()
        raise
    finally:
        process.stdout.close()
        process.stderr.close()
    stdout = b"".join(stdout_chunks)
    stderr = b"".join(stderr_chunks)
    if exit_code != 0 or stderr:
        raise PreparationAuthorityError("runtime capture child failed closed")
    if (
        _file_sha256(WORKSPACE_ROOT, RUNTIME_PATH) != expected_runtime_sha256
        or _file_sha256(WORKSPACE_ROOT, CONTRACTS_PATH) != expected_contracts_sha256
    ):
        raise PreparationAuthorityError(
            "runtime inspection oracle bytes changed across launch"
        )
    return stdout, {
        "child_process_id": process.pid,
        "child_exit_code": 0,
        "child_stdout_byte_count": len(stdout),
        "child_stderr_byte_count": 0,
        "child_oracle_raw_sha256": expected_runtime_sha256,
        "child_oracle_api_sha256": RUNTIME_ORACLE_API_SHA256,
    }


def _capture_claim(
    marker: Mapping[str, Any],
    genesis: Mapping[str, Any],
    event2: Mapping[str, Any],
    ordinal: int,
) -> Dict[str, Any]:
    label = "RUNTIME_CAPTURE_A_LAUNCH" if ordinal == 0 else "RUNTIME_CAPTURE_B_LAUNCH"
    return _nonce_claim(
        marker,
        genesis,
        "RUNTIME_CAPTURE_LAUNCH",
        None,
        label,
        event2["event_sha256"],
        "LAUNCH_SPENT_NO_RECAPTURE",
    )


def _candidate_record(
    marker: Mapping[str, Any],
    genesis: Mapping[str, Any],
    request: Mapping[str, Any],
    binding_a_payload: bytes,
    binding_a: Mapping[str, Any],
    binding_b_payload: bytes,
    binding_b: Mapping[str, Any],
) -> Dict[str, Any]:
    stable = (
        binding_a["semantic_manifest_sha256"] == binding_b["semantic_manifest_sha256"]
        and binding_a["installed_files_manifest_sha256"]
        == binding_b["installed_files_manifest_sha256"]
        and binding_a["source_capsule_manifest_sha256"]
        == binding_b["source_capsule_manifest_sha256"]
        and binding_a["target_profile_id"] == binding_b["target_profile_id"]
    )
    complete = (
        binding_a["complete_installed_file_verification"] is True
        and binding_b["complete_installed_file_verification"] is True
    )
    privacy_body = {
        "binding_a_projection_sha256": binding_a["privacy_projection_sha256"],
        "binding_b_projection_sha256": binding_b["privacy_projection_sha256"],
        "semantic_manifest_sha256": binding_a["semantic_manifest_sha256"],
    }
    record = {
        "schema": contracts.RUNTIME_CANDIDATE_SCHEMA,
        "marker_sha256": marker["marker_sha256"],
        "genesis_sha256": genesis["genesis_sha256"],
        "preparation_instance_nonce_sha256": marker[
            "preparation_instance_nonce_sha256"
        ],
        "request_sha256": request["request_sha256"],
        "binding_a_raw_sha256": _sha256(binding_a_payload),
        "binding_a_sha256": binding_a["binding_sha256"],
        "binding_b_raw_sha256": _sha256(binding_b_payload),
        "binding_b_sha256": binding_b["binding_sha256"],
        "raw_envelope_a_sha256": binding_a["raw_envelope_sha256"],
        "raw_envelope_a_record_sha256": binding_a["raw_envelope_record_sha256"],
        "raw_envelope_b_sha256": binding_b["raw_envelope_sha256"],
        "raw_envelope_b_record_sha256": binding_b["raw_envelope_record_sha256"],
        "raw_capture_envelopes_persisted": False,
        "semantic_manifest_a_sha256": binding_a["semantic_manifest_sha256"],
        "semantic_manifest_b_sha256": binding_b["semantic_manifest_sha256"],
        "installed_files_manifest_a_sha256": binding_a[
            "installed_files_manifest_sha256"
        ],
        "installed_files_manifest_b_sha256": binding_b[
            "installed_files_manifest_sha256"
        ],
        "double_capture_semantically_stable": stable,
        "complete_installed_file_verification": complete,
        "candidate_state": (
            "UNAPPROVED_PREPARATION_CANDIDATE"
            if stable and complete
            else "REJECTED_DOUBLE_CAPTURE_MISMATCH"
        ),
        "approved": False,
        "runtime_admitted": False,
        "scientific_compute_executed": False,
        "execution_admissible": False,
        "candidate_not_reusable_as_formal_runtime_approval": True,
        "fresh_approval_recapture_required": True,
        "privacy_projection_sha256": _sha256(
            b"heterodiff-a1-r1-runtime-candidate-privacy-binding-v2\0"
            + _canonical(privacy_body)
        ),
        "unclassified_absolute_path_count": 0,
        "candidate_sha256": None,
    }
    return contracts.finish_record(record, "RUNTIME_CANDIDATE")


def _validate_binding_against_capsule(
    root: Path,
    static: Mapping[str, Any],
    request: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> Dict[str, Any]:
    checked = runtime.validate_persisted_binding(binding, request)
    projection = checked["privacy_safe_projection"]["semantic_projection"]
    capsule_inventory = projection["source_capsule_inventory"]
    expected_rows = sorted(
        [
            {
                "path": row["capsule_relative_path"],
                "bytes": row["bytes"],
                "raw_sha256": row["raw_sha256"],
                "mode_octal": "0600",
            }
            for row in static["capsule_content_plan"]["rows"]
        ],
        key=lambda row: row["path"],
    )
    if (
        capsule_inventory["root"] != "<WORKSPACE>/" + CAPSULE_ROOT
        or capsule_inventory["rows"] != expected_rows
        or capsule_inventory["file_count"] != 53
        or capsule_inventory["directory_count"]
        != static["capsule_content_plan"]["directory_count"]
        or checked["child_oracle_raw_sha256"]
        != static["implementation"]["runtime_sha256"]
        or checked["child_oracle_api_sha256"] != RUNTIME_ORACLE_API_SHA256
    ):
        raise PreparationAuthorityError(
            "runtime binding does not match the admitted capsule or oracle"
        )
    manifest_payload, manifest = _load_contract(
        root, CAPSULE_MANIFEST_PATH, "SOURCE_CAPSULE_MANIFEST"
    )
    del manifest_payload
    _audit_capsule(root, static, manifest)
    return checked


def _execute_runtime_at_root(
    root: Path,
    capture_oracle: Any = None,
    live_action: str | None = None,
) -> Dict[str, Any]:
    _guard_canonical_mutation(root, live_action)
    before_state = _audit_preparation_prefix(root)
    if "TERMINAL" in before_state["live_state"]:
        raise PreparationAuthorityError("runtime writer refuses terminal custody")
    if root.resolve() == WORKSPACE_ROOT.resolve() and capture_oracle is not None:
        raise PreparationAuthorityError("canonical runtime capture refuses injection")
    registration_payload, registration, registration_bindings = _load_registration(root)
    del registration_payload
    static = registration["static_qualification_snapshot"]
    _, marker, _, genesis = _load_marker_and_genesis(root)
    _, manifest = _load_contract(root, CAPSULE_MANIFEST_PATH, "SOURCE_CAPSULE_MANIFEST")
    _, admission = _load_contract(
        root, CAPSULE_ADMISSION_PATH, "SOURCE_CAPSULE_ADMISSION"
    )
    descriptor = _acquire_writer_lock(root)
    try:
        head = _event_head(root, genesis, 1)
        request = _runtime_request(marker, genesis, manifest, admission)
        claim2 = _nonce_claim(
            marker,
            genesis,
            "PREPARATION_EVENT",
            2,
            "RUNTIME_DOUBLE_CAPTURE_OPENED",
            head,
            "DETERMINISTIC_MISSING_ROWS_MAY_RESUME",
        )
        claim2 = _claim_or_load(root, _event_claim_path(2), claim2, live_action)
        request_payload, request = _write_or_load_record(
            root, RUNTIME_REQUEST_PATH, "RUNTIME_REQUEST", request, live_action
        )
        event2 = _event_record(
            marker,
            genesis,
            2,
            "RUNTIME_DOUBLE_CAPTURE_OPENED",
            head,
            claim2,
            RUNTIME_REQUEST_PATH,
            request_payload,
            request,
            "OPENED",
        )
        event2 = _write_or_load_event(root, 2, event2, live_action)
        bindings = []
        for ordinal, (claim_path, binding_path) in enumerate(
            (
                (RUNTIME_CAPTURE_A_CLAIM_PATH, RUNTIME_BINDING_A_PATH),
                (RUNTIME_CAPTURE_B_CLAIM_PATH, RUNTIME_BINDING_B_PATH),
            )
        ):
            if _path_has_entry(root / binding_path):
                binding_payload, binding = _load_contract(
                    root, binding_path, "RUNTIME_ENVELOPE_BINDING"
                )
                claim = _capture_claim(marker, genesis, event2, ordinal)
                _, observed_claim = _load_contract(
                    root, claim_path, "OPERATION_NONCE_CLAIM"
                )
                if observed_claim != claim:
                    raise PreparationAuthorityError("capture launch claim changed")
                binding = _validate_binding_against_capsule(
                    root, static, request, binding
                )
                if (
                    binding["capture_ordinal"] != ordinal
                    or binding["launch_claim_sha256"] != claim["claim_sha256"]
                ):
                    raise PreparationAuthorityError(
                        "persisted runtime binding cross-link changed"
                    )
                bindings.append((binding_payload, binding))
                continue
            if _path_has_entry(root / claim_path):
                raise PreparationAuthorityError(
                    "capture launch was spent without a binding; recapture is forbidden"
                )
            claim = _capture_claim(marker, genesis, event2, ordinal)
            claim = _claim_or_load(root, claim_path, claim, live_action)
            active_state = _audit_preparation_prefix(root, ordinal)
            if active_state["live_state"] not in {
                "RUNTIME_CAPTURE_A_CLAIMED_ACTIVE_PROCESS_ONLY",
                "RUNTIME_CAPTURE_B_CLAIMED_ACTIVE_PROCESS_ONLY",
            }:
                raise PreparationAuthorityError(
                    "runtime launch claim failed its immediate full scan"
                )
            if capture_oracle is None:
                raw_envelope, child_receipt = _run_runtime_child(
                    request_payload,
                    ordinal,
                    registration_bindings["RUNTIME_MODULE"],
                    registration_bindings["CONTRACTS_MODULE"],
                )
            else:
                result = capture_oracle(request_payload, ordinal)
                if (
                    type(result) is not tuple
                    or len(result) != 2
                    or type(result[0]) is not bytes
                    or type(result[1]) is not dict
                ):
                    raise PreparationAuthorityError(
                        "synthetic capture oracle result changed"
                    )
                raw_envelope, child_receipt = result
            returned_state = _audit_preparation_prefix(root, ordinal)
            expected_returned_state = (
                "RUNTIME_CAPTURE_A_CLAIMED_ACTIVE_PROCESS_ONLY"
                if ordinal == 0
                else "RUNTIME_CAPTURE_B_CLAIMED_ACTIVE_PROCESS_ONLY"
            )
            if returned_state["live_state"] != expected_returned_state:
                raise PreparationAuthorityError(
                    "runtime capture return failed its pre-binding full scan"
                )
            binding = runtime.project_envelope_binding(
                raw_envelope,
                request,
                claim["claim_sha256"],
                request[
                    "launch_binding_a_sha256"
                    if ordinal == 0
                    else "launch_binding_b_sha256"
                ],
                child_receipt,
            )
            binding = _validate_binding_against_capsule(root, static, request, binding)
            pre_binding_state = _audit_preparation_prefix(root, ordinal)
            if pre_binding_state["live_state"] != expected_returned_state:
                raise PreparationAuthorityError(
                    "runtime binding failed its immediate pre-publication scan"
                )
            raw_envelope = b""
            binding_payload, binding = _write_or_load_record(
                root,
                binding_path,
                "RUNTIME_ENVELOPE_BINDING",
                binding,
                live_action,
            )
            after_binding_state = _audit_preparation_prefix(root)
            if "TERMINAL" in after_binding_state["live_state"]:
                raise PreparationAuthorityError(
                    "runtime binding failed its immediate full scan"
                )
            bindings.append((binding_payload, binding))
        candidate = _candidate_record(
            marker,
            genesis,
            request,
            bindings[0][0],
            bindings[0][1],
            bindings[1][0],
            bindings[1][1],
        )
        if bindings[0][1]["child_process_id"] == bindings[1][1]["child_process_id"]:
            raise PreparationAuthorityError(
                "runtime captures did not use distinct child processes"
            )
        stable = candidate["candidate_state"] == "UNAPPROVED_PREPARATION_CANDIDATE"
        kind3 = (
            "RUNTIME_CANDIDATE_ADMITTED"
            if stable
            else "RUNTIME_DOUBLE_CAPTURE_REJECTED"
        )
        outcome3 = (
            "ADMITTED_UNAPPROVED_PREPARATION_ONLY"
            if stable
            else "REJECTED_DOUBLE_CAPTURE_MISMATCH"
        )
        claim3 = _nonce_claim(
            marker,
            genesis,
            "PREPARATION_EVENT",
            3,
            kind3,
            event2["event_sha256"],
            "DETERMINISTIC_MISSING_ROWS_MAY_RESUME",
        )
        claim3 = _claim_or_load(root, _event_claim_path(3), claim3, live_action)
        candidate_payload, candidate = _write_or_load_record(
            root,
            RUNTIME_CANDIDATE_PATH,
            "RUNTIME_CANDIDATE",
            candidate,
            live_action,
        )
        event3 = _event_record(
            marker,
            genesis,
            3,
            kind3,
            event2["event_sha256"],
            claim3,
            RUNTIME_CANDIDATE_PATH,
            candidate_payload,
            candidate,
            outcome3,
        )
        event3 = _write_or_load_event(root, 3, event3, live_action)
        if not stable:
            final_state = _audit_preparation_prefix(root)
            if final_state["live_state"] != (
                "PREPARATION_CLOSED_RUNTIME_CANDIDATE_REJECTED"
            ):
                raise PreparationAuthorityError("runtime rejection branch scan changed")
            return candidate
        kind4 = "PREPARATION_CLOSED_AWAITING_OPERATOR_APPROVAL"
        outcome4 = "CLOSED_AWAITING_OPERATOR_APPROVAL"
        claim4 = _nonce_claim(
            marker,
            genesis,
            "PREPARATION_EVENT",
            4,
            kind4,
            event3["event_sha256"],
            "DETERMINISTIC_MISSING_ROWS_MAY_RESUME",
        )
        claim4 = _claim_or_load(root, _event_claim_path(4), claim4, live_action)
        event4 = _event_record(
            marker,
            genesis,
            4,
            kind4,
            event3["event_sha256"],
            claim4,
            RUNTIME_CANDIDATE_PATH,
            candidate_payload,
            candidate,
            outcome4,
        )
        _write_or_load_event(root, 4, event4, live_action)
        final_state = _audit_preparation_prefix(root)
        if final_state["live_state"] != (
            "PREPARATION_CLOSED_AWAITING_OPERATOR_APPROVAL"
        ):
            raise PreparationAuthorityError("runtime success branch scan changed")
        return candidate
    finally:
        os.close(descriptor)


def _scientific_carrier_digest_rejected(value: Any, quarantine: Iterable[str]) -> bool:
    forbidden = set(quarantine)
    if type(value) is str:
        if value in forbidden:
            raise PreparationAuthorityError(
                "D1/V2 digest is forbidden in scientific carrier"
            )
        return True
    if type(value) is list or type(value) is tuple:
        for item in value:
            _scientific_carrier_digest_rejected(item, forbidden)
        return True
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise PreparationAuthorityError("scientific carrier key type changed")
            if key in {
                "seed",
                "seeds",
                "paired_seed",
                "paired_seeds",
                "training_seed",
                "registry",
                "seed_registry",
                "tagged_coordinate",
                "legacy_request_projection",
            } and _contains_exact_integer(item, 1729):
                raise PreparationAuthorityError("seed 1729 is development-only")
            _scientific_carrier_digest_rejected(item, forbidden)
        return True
    if value is None or type(value) in (bool, int, float):
        return True
    raise PreparationAuthorityError("scientific carrier value type changed")


def _contains_exact_integer(value: Any, target: int) -> bool:
    if type(value) is int:
        return value == target
    if type(value) in (list, tuple):
        return any(_contains_exact_integer(item, target) for item in value)
    if type(value) is dict:
        return any(_contains_exact_integer(item, target) for item in value.values())
    return False


def validate_future_scientific_carrier(workspace_root: Any, value: Any) -> bool:
    root = Path(workspace_root).absolute()
    qualification = v1_authority.load_dormant_protocol_qualification(root)
    quarantine_rows = qualification.snapshot()["completion_evidence_protocol"][
        "d1_execution_lineage_quarantine"
    ]["rows"]
    quarantine = [row["sha256"] for row in quarantine_rows]
    if len(quarantine) != 550 or len(set(quarantine)) != 550:
        raise PreparationAuthorityError("D1 quarantine roster changed")
    return _scientific_carrier_digest_rejected(value, quarantine)


def _preparation_tree_inventory(root: Path) -> Dict[str, Any]:
    preparation = root / PREPARATION_ROOT
    before = _tree_snapshot(preparation)
    directories = []
    files = []
    for relative, _ in before["directories"]:
        path = preparation / relative if relative else preparation
        information = path.lstat()
        if stat.S_IMODE(information.st_mode) != 0o700:
            raise PreparationAuthorityError("preparation directory mode changed")
        directories.append(relative)
    for relative, _ in before["files"]:
        path = preparation / relative
        information = path.lstat()
        if stat.S_IMODE(information.st_mode) != 0o600 or information.st_nlink != 1:
            raise PreparationAuthorityError(
                "preparation file mode or link count changed"
            )
        files.append(relative)
    after = _tree_snapshot(preparation)
    if before != after:
        raise PreparationAuthorityError("preparation tree changed during scan")
    return {"directories": directories, "files": files, "snapshot": before}


def _relative_to_preparation(relative_path: str) -> str:
    prefix = PREPARATION_ROOT + "/"
    if not relative_path.startswith(prefix):
        raise PreparationAuthorityError("operational path escapes preparation root")
    return relative_path[len(prefix) :]


def _validate_partial_capsule(
    root: Path, static: Mapping[str, Any], inventory: Mapping[str, Any]
) -> None:
    files = set(inventory["files"])
    directories = set(inventory["directories"])
    capsule_prefix = "capsule/"
    capsule_file_rows = [
        (capsule_prefix + row["capsule_relative_path"], row)
        for row in static["capsule_content_plan"]["rows"]
    ]
    present_rows = [row for path, row in capsule_file_rows if path in files]
    if present_rows != static["capsule_content_plan"]["rows"][: len(present_rows)]:
        raise PreparationAuthorityError("partial capsule files are not a frozen prefix")
    expected_capsule_directories = {"capsule"}
    expected_capsule_directories.update(
        "capsule" + ("/" + value if value else "")
        for value in static["capsule_content_plan"]["directories"]
    )
    observed_capsule_directories = {
        value
        for value in directories
        if value == "capsule" or value.startswith(capsule_prefix)
    }
    if not observed_capsule_directories.issubset(expected_capsule_directories):
        raise PreparationAuthorityError("partial capsule has an extra directory")
    for path, row in capsule_file_rows:
        if path not in files:
            continue
        payload, information = _read_stable_file(root / PREPARATION_ROOT / path)
        if (
            payload != _expected_capsule_payload(root, row)
            or stat.S_IMODE(information.st_mode) != 0o600
            or information.st_nlink != 1
        ):
            raise PreparationAuthorityError("partial capsule row changed")


def _assert_prefix_presence(root: Path, ordered_paths: Sequence[str]) -> int:
    present = [_path_has_entry(root / value) for value in ordered_paths]
    seen_gap = False
    count = 0
    for exists in present:
        if not exists:
            seen_gap = True
        elif seen_gap:
            raise PreparationAuthorityError("operational record appears after a gap")
        else:
            count += 1
    return count


def _strict_valid_marker_prefix(
    root: Path,
    registration_payload: bytes,
    registration: Mapping[str, Any],
    marker_payload: bytes,
    marker: Mapping[str, Any],
    active_capture_ordinal: int | None = None,
) -> Dict[str, Any]:
    preparation = root / PREPARATION_ROOT
    if not _path_has_entry(preparation):
        return {
            "live_state": "MARKER_CREATED_GENESIS_PENDING_DETERMINISTIC_RESUME",
            "marker_present": True,
            "marker_attempt_spent": True,
            "marker_sha256": marker["marker_sha256"],
            "preparation_event_count": 0,
            "closed": False,
            "retry_permitted": False,
            "execution_authorized": False,
        }
    inventory = _preparation_tree_inventory(root)
    fixed_directories_in_creation_order = [
        "",
        "ledger",
        "ledger/events",
        "ledger/nonce-claims",
        "ledger/receipts",
        "runtime-candidate",
    ]
    directories = set(inventory["directories"])
    files = set(inventory["files"])
    genesis_relative = _relative_to_preparation(LEDGER_GENESIS_PATH)
    lock_relative = _relative_to_preparation(LEDGER_LOCK_PATH)
    if genesis_relative not in files:
        observed_fixed = [
            value
            for value in fixed_directories_in_creation_order
            if value in directories
        ]
        if observed_fixed != fixed_directories_in_creation_order[: len(observed_fixed)]:
            raise PreparationAuthorityError("genesis directory creation has a gap")
        if directories != set(observed_fixed):
            raise PreparationAuthorityError(
                "genesis-pending tree has an extra directory"
            )
        if files not in (set(), {lock_relative}):
            raise PreparationAuthorityError("genesis-pending tree has an extra file")
        if lock_relative in files and len(observed_fixed) != len(
            fixed_directories_in_creation_order
        ):
            raise PreparationAuthorityError("writer lock precedes required directories")
        if (
            lock_relative in files
            and _read_stable_file(root / LEDGER_LOCK_PATH)[0] != b""
        ):
            raise PreparationAuthorityError("writer lock payload changed")
        return {
            "live_state": "MARKER_CREATED_GENESIS_PENDING_DETERMINISTIC_RESUME",
            "marker_present": True,
            "marker_attempt_spent": True,
            "marker_sha256": marker["marker_sha256"],
            "preparation_event_count": 0,
            "closed": False,
            "retry_permitted": False,
            "execution_authorized": False,
        }
    required_base_directories = set(fixed_directories_in_creation_order)
    if (
        not required_base_directories.issubset(directories)
        or lock_relative not in files
    ):
        raise PreparationAuthorityError("ledger genesis base custody is incomplete")
    if _read_stable_file(root / LEDGER_LOCK_PATH)[0] != b"":
        raise PreparationAuthorityError("writer lock payload changed")
    _, observed_marker, _, genesis = _load_marker_and_genesis(root)
    if observed_marker != marker:
        raise PreparationAuthorityError("marker changed across ledger reopen")
    expected_genesis = _genesis_record(
        registration_payload, registration, marker_payload, marker
    )
    if genesis != expected_genesis:
        raise PreparationAuthorityError("ledger genesis changed")

    known_files = {lock_relative, genesis_relative}
    known_files.update(_relative_to_preparation(value) for value in EVENT_FILE_PATHS)
    known_files.update(_relative_to_preparation(value) for value in EVENT_CLAIM_PATHS)
    known_files.update(
        _relative_to_preparation(value)
        for value in (
            RUNTIME_CAPTURE_A_CLAIM_PATH,
            RUNTIME_CAPTURE_B_CLAIM_PATH,
            CAPSULE_MANIFEST_PATH,
            CAPSULE_ADMISSION_PATH,
            RUNTIME_REQUEST_PATH,
            RUNTIME_BINDING_A_PATH,
            RUNTIME_BINDING_B_PATH,
            RUNTIME_CANDIDATE_PATH,
        )
    )
    known_files.update(
        "capsule/" + row["capsule_relative_path"]
        for row in registration["static_qualification_snapshot"][
            "capsule_content_plan"
        ]["rows"]
    )
    known_directories = set(required_base_directories)
    known_directories.add("capsule")
    known_directories.update(
        "capsule" + ("/" + value if value else "")
        for value in registration["static_qualification_snapshot"][
            "capsule_content_plan"
        ]["directories"]
    )
    if not files.issubset(known_files) or not directories.issubset(known_directories):
        raise PreparationAuthorityError("preparation tree contains an extra entry")
    for forbidden_name in RUNTIME_FORBIDDEN_OUTPUT_NAMES:
        if any(Path(value).name == forbidden_name for value in files):
            raise PreparationAuthorityError("forbidden runtime evidence path exists")

    static = registration["static_qualification_snapshot"]
    head = genesis["genesis_sha256"]
    event_count = 0

    opening_paths = (_event_claim_path(0), CAPSULE_MANIFEST_PATH, _event_path(0))
    opening_count = _assert_prefix_presence(root, opening_paths)
    if opening_count:
        expected_claim0 = _nonce_claim(
            marker,
            genesis,
            "PREPARATION_EVENT",
            0,
            "CAPSULE_MATERIALIZATION_OPENED",
            head,
            "DETERMINISTIC_MISSING_ROWS_MAY_RESUME",
        )
        _, claim0 = _load_contract(root, _event_claim_path(0), "OPERATION_NONCE_CLAIM")
        if claim0 != expected_claim0:
            raise PreparationAuthorityError("capsule-open claim changed")
    if opening_count >= 2:
        manifest_payload, manifest = _load_contract(
            root, CAPSULE_MANIFEST_PATH, "SOURCE_CAPSULE_MANIFEST"
        )
        expected_manifest = _capsule_manifest(static, marker, genesis)
        if manifest != expected_manifest:
            raise PreparationAuthorityError("capsule manifest changed")
    else:
        manifest_payload = b""
        manifest = None
    if opening_count == 3:
        _, event0 = _load_contract(root, _event_path(0), "LEDGER_EVENT")
        expected_event0 = _event_record(
            marker,
            genesis,
            0,
            "CAPSULE_MATERIALIZATION_OPENED",
            head,
            claim0,
            CAPSULE_MANIFEST_PATH,
            manifest_payload,
            manifest,
            "OPENED",
        )
        if event0 != expected_event0:
            raise PreparationAuthorityError("capsule-open event changed")
        head = event0["event_sha256"]
        event_count = 1
    else:
        if (
            any(
                _path_has_entry(root / value)
                for value in (
                    _event_claim_path(1),
                    CAPSULE_ADMISSION_PATH,
                    _event_path(1),
                    _event_claim_path(2),
                    RUNTIME_REQUEST_PATH,
                    _event_path(2),
                    RUNTIME_CAPTURE_A_CLAIM_PATH,
                    RUNTIME_BINDING_A_PATH,
                    RUNTIME_CAPTURE_B_CLAIM_PATH,
                    RUNTIME_BINDING_B_PATH,
                    _event_claim_path(3),
                    RUNTIME_CANDIDATE_PATH,
                    _event_path(3),
                    _event_claim_path(4),
                    _event_path(4),
                )
            )
            or "capsule" in directories
        ):
            raise PreparationAuthorityError("capsule state appears before event 0")
        return {
            "live_state": "CAPSULE_OPEN_RECORD_PUBLICATION_RESUMABLE",
            "marker_present": True,
            "marker_attempt_spent": True,
            "marker_sha256": marker["marker_sha256"],
            "genesis_sha256": genesis["genesis_sha256"],
            "preparation_event_count": 0,
            "current_preparation_head_sha256": head,
            "closed": False,
            "retry_permitted": False,
            "execution_authorized": False,
        }

    admission_paths = (_event_claim_path(1), CAPSULE_ADMISSION_PATH, _event_path(1))
    admission_count = _assert_prefix_presence(root, admission_paths)
    if admission_count == 0:
        _validate_partial_capsule(root, static, inventory)
        state = "CAPSULE_MATERIALIZATION_OPENED_RESUMABLE"
    else:
        if manifest is None:
            raise PreparationAuthorityError("capsule admission lacks manifest")
        _audit_capsule(root, static, manifest)
        expected_claim1 = _nonce_claim(
            marker,
            genesis,
            "PREPARATION_EVENT",
            1,
            "CAPSULE_ADMITTED",
            head,
            "DETERMINISTIC_MISSING_ROWS_MAY_RESUME",
        )
        _, claim1 = _load_contract(root, _event_claim_path(1), "OPERATION_NONCE_CLAIM")
        if claim1 != expected_claim1:
            raise PreparationAuthorityError("capsule-admission claim changed")
        expected_admission = _capsule_admission(
            root, static, marker, genesis, manifest_payload, manifest
        )
        if admission_count >= 2:
            admission_payload, admission = _load_contract(
                root, CAPSULE_ADMISSION_PATH, "SOURCE_CAPSULE_ADMISSION"
            )
            if admission != expected_admission:
                raise PreparationAuthorityError("capsule admission changed")
        else:
            admission_payload = b""
            admission = None
        if admission_count == 3:
            _, event1 = _load_contract(root, _event_path(1), "LEDGER_EVENT")
            expected_event1 = _event_record(
                marker,
                genesis,
                1,
                "CAPSULE_ADMITTED",
                head,
                claim1,
                CAPSULE_ADMISSION_PATH,
                admission_payload,
                admission,
                "ADMITTED_PREPARATION_CUSTODY_ONLY",
            )
            if event1 != expected_event1:
                raise PreparationAuthorityError("capsule-admission event changed")
            head = event1["event_sha256"]
            event_count = 2
            state = "CAPSULE_ADMITTED_RUNTIME_CAPTURE_NOT_OPENED"
        else:
            state = "CAPSULE_ADMISSION_PUBLICATION_RESUMABLE"
    if admission_count != 3:
        later = (
            _event_claim_path(2),
            RUNTIME_REQUEST_PATH,
            _event_path(2),
            RUNTIME_CAPTURE_A_CLAIM_PATH,
            RUNTIME_BINDING_A_PATH,
            RUNTIME_CAPTURE_B_CLAIM_PATH,
            RUNTIME_BINDING_B_PATH,
            _event_claim_path(3),
            RUNTIME_CANDIDATE_PATH,
            _event_path(3),
            _event_claim_path(4),
            _event_path(4),
        )
        if any(_path_has_entry(root / value) for value in later):
            raise PreparationAuthorityError(
                "runtime state appears before capsule admission"
            )
        return {
            "live_state": state,
            "marker_present": True,
            "marker_attempt_spent": True,
            "marker_sha256": marker["marker_sha256"],
            "genesis_sha256": genesis["genesis_sha256"],
            "preparation_event_count": event_count,
            "current_preparation_head_sha256": head,
            "closed": False,
            "retry_permitted": False,
            "execution_authorized": False,
        }

    runtime_open_paths = (_event_claim_path(2), RUNTIME_REQUEST_PATH, _event_path(2))
    runtime_open_count = _assert_prefix_presence(root, runtime_open_paths)
    request = _runtime_request(marker, genesis, manifest, admission)
    if runtime_open_count:
        expected_claim2 = _nonce_claim(
            marker,
            genesis,
            "PREPARATION_EVENT",
            2,
            "RUNTIME_DOUBLE_CAPTURE_OPENED",
            head,
            "DETERMINISTIC_MISSING_ROWS_MAY_RESUME",
        )
        _, claim2 = _load_contract(root, _event_claim_path(2), "OPERATION_NONCE_CLAIM")
        if claim2 != expected_claim2:
            raise PreparationAuthorityError("runtime-open claim changed")
    if runtime_open_count >= 2:
        request_payload, observed_request = _load_contract(
            root, RUNTIME_REQUEST_PATH, "RUNTIME_REQUEST"
        )
        if observed_request != request:
            raise PreparationAuthorityError("runtime request changed")
    else:
        request_payload = b""
    if runtime_open_count == 3:
        _, event2 = _load_contract(root, _event_path(2), "LEDGER_EVENT")
        expected_event2 = _event_record(
            marker,
            genesis,
            2,
            "RUNTIME_DOUBLE_CAPTURE_OPENED",
            head,
            claim2,
            RUNTIME_REQUEST_PATH,
            request_payload,
            request,
            "OPENED",
        )
        if event2 != expected_event2:
            raise PreparationAuthorityError("runtime-open event changed")
        head = event2["event_sha256"]
        event_count = 3
    else:
        if any(
            _path_has_entry(root / value)
            for value in (
                RUNTIME_CAPTURE_A_CLAIM_PATH,
                RUNTIME_BINDING_A_PATH,
                RUNTIME_CAPTURE_B_CLAIM_PATH,
                RUNTIME_BINDING_B_PATH,
                _event_claim_path(3),
                RUNTIME_CANDIDATE_PATH,
                _event_path(3),
                _event_claim_path(4),
                _event_path(4),
            )
        ):
            raise PreparationAuthorityError("capture state appears before event 2")
        return {
            "live_state": "RUNTIME_OPEN_RECORD_PUBLICATION_RESUMABLE",
            "marker_present": True,
            "marker_attempt_spent": True,
            "marker_sha256": marker["marker_sha256"],
            "genesis_sha256": genesis["genesis_sha256"],
            "preparation_event_count": event_count,
            "current_preparation_head_sha256": head,
            "closed": False,
            "retry_permitted": False,
            "execution_authorized": False,
        }

    binding_rows = []
    for ordinal, (claim_path, binding_path) in enumerate(
        (
            (RUNTIME_CAPTURE_A_CLAIM_PATH, RUNTIME_BINDING_A_PATH),
            (RUNTIME_CAPTURE_B_CLAIM_PATH, RUNTIME_BINDING_B_PATH),
        )
    ):
        claim_present = _path_has_entry(root / claim_path)
        binding_present = _path_has_entry(root / binding_path)
        if binding_present and not claim_present:
            raise PreparationAuthorityError(
                "runtime binding exists without launch claim"
            )
        if not claim_present:
            if ordinal == 0 and _path_has_entry(root / RUNTIME_CAPTURE_B_CLAIM_PATH):
                raise PreparationAuthorityError("runtime capture B precedes A")
            break
        expected_claim = _capture_claim(marker, genesis, event2, ordinal)
        _, claim = _load_contract(root, claim_path, "OPERATION_NONCE_CLAIM")
        if claim != expected_claim:
            raise PreparationAuthorityError("runtime launch claim changed")
        if not binding_present:
            if active_capture_ordinal == ordinal:
                later_paths = (
                    RUNTIME_CAPTURE_B_CLAIM_PATH,
                    RUNTIME_BINDING_B_PATH,
                    _event_claim_path(3),
                    RUNTIME_CANDIDATE_PATH,
                    _event_path(3),
                    _event_claim_path(4),
                    _event_path(4),
                )
                if ordinal == 1:
                    later_paths = later_paths[2:]
                if any(_path_has_entry(root / value) for value in later_paths):
                    raise PreparationAuthorityError(
                        "state appears after active capture claim"
                    )
                return {
                    "live_state": (
                        "RUNTIME_CAPTURE_A_CLAIMED_ACTIVE_PROCESS_ONLY"
                        if ordinal == 0
                        else "RUNTIME_CAPTURE_B_CLAIMED_ACTIVE_PROCESS_ONLY"
                    ),
                    "marker_present": True,
                    "marker_attempt_spent": True,
                    "marker_sha256": marker["marker_sha256"],
                    "genesis_sha256": genesis["genesis_sha256"],
                    "preparation_event_count": event_count,
                    "current_preparation_head_sha256": head,
                    "closed": False,
                    "retry_permitted": False,
                    "execution_authorized": False,
                }
            raise PreparationAuthorityError(
                "runtime launch claim is terminal without its in-memory result binding"
            )
        binding_payload, binding = _load_contract(
            root, binding_path, "RUNTIME_ENVELOPE_BINDING"
        )
        binding = _validate_binding_against_capsule(root, static, request, binding)
        if (
            binding["capture_ordinal"] != ordinal
            or binding["launch_claim_sha256"] != claim["claim_sha256"]
        ):
            raise PreparationAuthorityError("runtime capture binding ordinal changed")
        binding_rows.append((binding_payload, binding))
    if len(binding_rows) < 2:
        later = (
            _event_claim_path(3),
            RUNTIME_CANDIDATE_PATH,
            _event_path(3),
            _event_claim_path(4),
            _event_path(4),
        )
        if any(_path_has_entry(root / value) for value in later):
            raise PreparationAuthorityError(
                "candidate state appears before both captures"
            )
        state = (
            "RUNTIME_CAPTURE_B_NOT_YET_LAUNCHED"
            if len(binding_rows) == 1
            else "RUNTIME_CAPTURE_A_NOT_YET_LAUNCHED"
        )
        return {
            "live_state": state,
            "marker_present": True,
            "marker_attempt_spent": True,
            "marker_sha256": marker["marker_sha256"],
            "genesis_sha256": genesis["genesis_sha256"],
            "preparation_event_count": event_count,
            "current_preparation_head_sha256": head,
            "closed": False,
            "retry_permitted": False,
            "execution_authorized": False,
        }
    if binding_rows[0][1]["child_process_id"] == binding_rows[1][1]["child_process_id"]:
        raise PreparationAuthorityError(
            "runtime capture process identities are duplicated"
        )
    candidate = _candidate_record(
        marker,
        genesis,
        request,
        binding_rows[0][0],
        binding_rows[0][1],
        binding_rows[1][0],
        binding_rows[1][1],
    )
    stable = candidate["candidate_state"] == "UNAPPROVED_PREPARATION_CANDIDATE"
    kind3 = (
        "RUNTIME_CANDIDATE_ADMITTED" if stable else "RUNTIME_DOUBLE_CAPTURE_REJECTED"
    )
    outcome3 = (
        "ADMITTED_UNAPPROVED_PREPARATION_ONLY"
        if stable
        else "REJECTED_DOUBLE_CAPTURE_MISMATCH"
    )
    candidate_paths = (_event_claim_path(3), RUNTIME_CANDIDATE_PATH, _event_path(3))
    candidate_count = _assert_prefix_presence(root, candidate_paths)
    if candidate_count:
        expected_claim3 = _nonce_claim(
            marker,
            genesis,
            "PREPARATION_EVENT",
            3,
            kind3,
            head,
            "DETERMINISTIC_MISSING_ROWS_MAY_RESUME",
        )
        _, claim3 = _load_contract(root, _event_claim_path(3), "OPERATION_NONCE_CLAIM")
        if claim3 != expected_claim3:
            raise PreparationAuthorityError("candidate claim changed")
    if candidate_count >= 2:
        candidate_payload, observed_candidate = _load_contract(
            root, RUNTIME_CANDIDATE_PATH, "RUNTIME_CANDIDATE"
        )
        if observed_candidate != candidate:
            raise PreparationAuthorityError("runtime candidate changed")
    else:
        candidate_payload = b""
    if candidate_count == 3:
        _, event3 = _load_contract(root, _event_path(3), "LEDGER_EVENT")
        expected_event3 = _event_record(
            marker,
            genesis,
            3,
            kind3,
            head,
            claim3,
            RUNTIME_CANDIDATE_PATH,
            candidate_payload,
            candidate,
            outcome3,
        )
        if event3 != expected_event3:
            raise PreparationAuthorityError("candidate event changed")
        head = event3["event_sha256"]
        event_count = 4
    else:
        if any(
            _path_has_entry(root / value)
            for value in (_event_claim_path(4), _event_path(4))
        ):
            raise PreparationAuthorityError("closure state appears before event 3")
        return {
            "live_state": "RUNTIME_CANDIDATE_PUBLICATION_RESUMABLE",
            "marker_present": True,
            "marker_attempt_spent": True,
            "marker_sha256": marker["marker_sha256"],
            "genesis_sha256": genesis["genesis_sha256"],
            "preparation_event_count": event_count,
            "current_preparation_head_sha256": head,
            "closed": False,
            "retry_permitted": False,
            "execution_authorized": False,
        }
    if not stable:
        if _path_has_entry(root / _event_claim_path(4)) or _path_has_entry(
            root / _event_path(4)
        ):
            raise PreparationAuthorityError("rejected runtime branch contains event 4")
        state = "PREPARATION_CLOSED_RUNTIME_CANDIDATE_REJECTED"
        closed = True
    else:
        closure_paths = (_event_claim_path(4), _event_path(4))
        closure_count = _assert_prefix_presence(root, closure_paths)
        if closure_count:
            expected_claim4 = _nonce_claim(
                marker,
                genesis,
                "PREPARATION_EVENT",
                4,
                "PREPARATION_CLOSED_AWAITING_OPERATOR_APPROVAL",
                head,
                "DETERMINISTIC_MISSING_ROWS_MAY_RESUME",
            )
            _, claim4 = _load_contract(
                root, _event_claim_path(4), "OPERATION_NONCE_CLAIM"
            )
            if claim4 != expected_claim4:
                raise PreparationAuthorityError("closure claim changed")
        if closure_count == 2:
            _, event4 = _load_contract(root, _event_path(4), "LEDGER_EVENT")
            expected_event4 = _event_record(
                marker,
                genesis,
                4,
                "PREPARATION_CLOSED_AWAITING_OPERATOR_APPROVAL",
                head,
                claim4,
                RUNTIME_CANDIDATE_PATH,
                candidate_payload,
                candidate,
                "CLOSED_AWAITING_OPERATOR_APPROVAL",
            )
            if event4 != expected_event4:
                raise PreparationAuthorityError("closure event changed")
            head = event4["event_sha256"]
            event_count = 5
            state = "PREPARATION_CLOSED_AWAITING_OPERATOR_APPROVAL"
            closed = True
        else:
            state = "PREPARATION_CLOSURE_PUBLICATION_RESUMABLE"
            closed = False
    return {
        "live_state": state,
        "marker_present": True,
        "marker_attempt_spent": True,
        "marker_sha256": marker["marker_sha256"],
        "genesis_sha256": genesis["genesis_sha256"],
        "preparation_event_count": event_count,
        "current_preparation_head_sha256": head,
        "closed": closed,
        "retry_permitted": False,
        "execution_authorized": False,
    }


def _audit_preparation_prefix(
    root: Path, active_capture_ordinal: int | None = None
) -> Dict[str, Any]:
    if active_capture_ordinal is not None and active_capture_ordinal not in (0, 1):
        raise PreparationAuthorityError("active capture ordinal changed")
    registration_payload, registration, bindings = _load_registration(root)
    for relative_path in DORMANT_V1_PATHS:
        _require_absent(root / relative_path)
    _require_absent(root / PERMANENTLY_ABSENT_V1_SRC_ADAPTER)
    marker_path = root / MARKER_PATH
    preparation_path = root / PREPARATION_ROOT

    def repeat_static_inputs() -> None:
        repeated_payload, repeated_registration, repeated_bindings = _load_registration(
            root
        )
        if (
            repeated_payload != registration_payload
            or _canonical(repeated_registration) != _canonical(registration)
            or repeated_bindings != bindings
        ):
            raise PreparationAuthorityError(
                "registration inputs changed across full prefix scan"
            )
        for relative_path in DORMANT_V1_PATHS:
            _require_absent(root / relative_path)
        _require_absent(root / PERMANENTLY_ABSENT_V1_SRC_ADAPTER)

    try:
        marker_information = marker_path.lstat()
    except FileNotFoundError:
        _require_absent(preparation_path)
        repeat_static_inputs()
        return {
            "live_state": "AWAITING_EXPLICIT_MARKER_AUTHORIZATION",
            "marker_present": False,
            "marker_attempt_spent": False,
            "preparation_event_count": 0,
            "closed": False,
            "retry_permitted": False,
            "execution_authorized": False,
        }
    marker_invalid_reason = None
    marker_payload = b""
    marker = None
    if stat.S_ISLNK(marker_information.st_mode):
        marker_invalid_reason = "SYMLINK_OR_BROKEN_SYMLINK"
    elif not stat.S_ISREG(marker_information.st_mode):
        marker_invalid_reason = "NONREGULAR_ENTRY"
    elif marker_information.st_nlink != 1:
        marker_invalid_reason = "HARDLINK_COUNT_CHANGED"
    elif stat.S_IMODE(marker_information.st_mode) != 0o600:
        marker_invalid_reason = "MODE_CHANGED"
    elif marker_information.st_size > contracts.MAXIMUM_RECORD_BYTES:
        marker_invalid_reason = "OVERSIZED_MARKER"
    else:
        try:
            marker_payload, _ = _read_stable_file(marker_path)
            marker = contracts.parse_record(marker_payload, "ATTEMPT_MARKER")
            expected_marker = _marker_record(
                registration_payload,
                registration,
                bindings,
                marker["preparation_instance_nonce_sha256"],
            )
            if marker != expected_marker:
                raise PreparationAuthorityError("marker static bindings changed")
        except (
            contracts.ContractError,
            PreparationAuthorityError,
            OSError,
            ValueError,
        ):
            marker_invalid_reason = "INVALID_PARTIAL_OR_STATIC_BINDING_CHANGED"
    if marker_invalid_reason is not None or marker is None:
        repeat_static_inputs()
        return {
            "live_state": "MARKER_ATTEMPT_SPENT_TERMINAL_INVALID_OR_PARTIAL",
            "marker_present": True,
            "marker_attempt_spent": True,
            "marker_invalid_reason": marker_invalid_reason,
            "conflicting_preparation_root_present": _path_has_entry(preparation_path),
            "preparation_event_count": 0,
            "closed": True,
            "retry_permitted": False,
            "execution_authorized": False,
        }
    try:
        outer_before = (
            _tree_snapshot(preparation_path)
            if _path_has_entry(preparation_path)
            else None
        )
        result = _strict_valid_marker_prefix(
            root,
            registration_payload,
            registration,
            marker_payload,
            marker,
            active_capture_ordinal,
        )
        repeat_static_inputs()
        outer_after = (
            _tree_snapshot(preparation_path)
            if _path_has_entry(preparation_path)
            else None
        )
        if outer_before != outer_after:
            raise PreparationAuthorityError(
                "preparation tree changed across the full prefix scan"
            )
        return result
    except (
        PreparationAuthorityError,
        contracts.ContractError,
        OSError,
        ValueError,
    ) as error:
        return {
            "live_state": "PREPARATION_ATTEMPT_SPENT_TERMINAL_CUSTODY_INVALID",
            "marker_present": True,
            "marker_attempt_spent": True,
            "marker_sha256": marker["marker_sha256"],
            "terminal_reason_class": type(error).__name__,
            "preparation_event_count": 0,
            "closed": True,
            "retry_permitted": False,
            "execution_authorized": False,
        }


class ActivationPreparationQualification:
    __slots__ = ("_static", "_live", "_record_sha256")

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        raise TypeError("qualification is constructed only by the canonical loader")

    def static_snapshot(self) -> Dict[str, Any]:
        return json.loads(self._static.decode("ascii"))

    def live_transition(self) -> Dict[str, Any]:
        return json.loads(self._live.decode("ascii"))

    @property
    def record_sha256(self) -> str:
        return self._record_sha256

    def __setattr__(self, name: str, value: Any) -> None:
        del name, value
        raise AttributeError("qualification is immutable")


def load_qualification(workspace_root: Any) -> ActivationPreparationQualification:
    root = Path(workspace_root).absolute()
    _, registration, _ = _load_registration(root)
    live = _audit_preparation_prefix(root)
    value = object.__new__(ActivationPreparationQualification)
    object.__setattr__(
        value,
        "_static",
        _canonical(registration["static_qualification_snapshot"]),
    )
    object.__setattr__(value, "_live", _canonical(live))
    object.__setattr__(value, "_record_sha256", registration["record_sha256"])
    return value


def status(workspace_root: Any) -> Dict[str, Any]:
    qualification = load_qualification(workspace_root)
    live = qualification.live_transition()
    return {
        "schema": "heterodiff-a1-r1-activation-preparation-status-v2",
        "milestone_state": contracts.MILESTONE_STATE,
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "live_transition": live,
        "registration_record_sha256": qualification.record_sha256,
        "current_unresolved_null_count": 172,
        "current_open_blocker_count": 12,
        "runtime_approved": False,
        "scientific_campaign_nonce_minted": False,
        "scientific_authority_ledger_created": False,
        "execution_authorized": False,
    }


def _native_process_argv() -> Tuple[str, ...]:
    if sys.platform != "darwin":
        raise PreparationAuthorityError("live v2 writer requires Darwin native argv")
    try:
        libc = ctypes.CDLL(None)
        get_argc = libc._NSGetArgc
        get_argv = libc._NSGetArgv
        get_argc.argtypes = []
        get_argc.restype = ctypes.POINTER(ctypes.c_int)
        get_argv.argtypes = []
        get_argv.restype = ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))
        argc = get_argc().contents.value
        argv = get_argv().contents
        return tuple(
            argv[index].decode("utf-8", errors="strict") for index in range(argc)
        )
    except (AttributeError, OSError, UnicodeDecodeError, ValueError) as error:
        raise PreparationAuthorityError(
            "native process argv cannot be reopened"
        ) from error


def _require_live_cli_boundary(action: str) -> Path:
    if action not in LIVE_ACTIONS:
        raise PreparationAuthorityError("live action is not frozen")
    if __name__ != "__main__" or __spec__ is not None:
        raise PreparationAuthorityError("writer is direct-file __main__ only")
    main_module = sys.modules.get("__main__")
    if (
        main_module is not sys.modules.get(__name__)
        or main_module.__dict__ is not globals()
    ):
        raise PreparationAuthorityError("writer __main__ identity changed")
    root = WORKSPACE_ROOT.resolve(strict=True)
    if Path.cwd().resolve(strict=True) != root:
        raise PreparationAuthorityError("writer working directory is not canonical")
    if Path(__file__).resolve(strict=True) != root / AUTHORITY_PATH:
        raise PreparationAuthorityError("writer module path is not canonical")
    if sys.argv != [AUTHORITY_PATH, action]:
        raise PreparationAuthorityError("writer argv changed")
    expected_process = (
        NATIVE_PYTHON_ARGV0,
        "-I",
        "-S",
        "-B",
        AUTHORITY_PATH,
        action,
    )
    if tuple(getattr(sys, "orig_argv", ())) != expected_process:
        raise PreparationAuthorityError("writer Python process vector changed")
    if _native_process_argv() != expected_process:
        raise PreparationAuthorityError("writer native process vector changed")
    if sys.executable != (root / CANONICAL_PYTHON_RELATIVE_PATH).as_posix():
        raise PreparationAuthorityError("writer interpreter path changed")
    if (
        Path(sys.executable).resolve(strict=True).as_posix()
        != CANONICAL_INTERPRETER_REALPATH
    ):
        raise PreparationAuthorityError("writer interpreter realpath changed")
    observed_flags = {
        "isolated": sys.flags.isolated,
        "no_site": sys.flags.no_site,
        "dont_write_bytecode": sys.flags.dont_write_bytecode,
        "safe_path": sys.flags.safe_path,
    }
    if observed_flags != {
        "isolated": 1,
        "no_site": 1,
        "dont_write_bytecode": 1,
        "safe_path": True,
    }:
        raise PreparationAuthorityError("writer isolation flags changed")
    return root


def main(arguments: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if arguments is None else arguments)
    if argv == ["--status"]:
        sys.stdout.buffer.write(_canonical(status(WORKSPACE_ROOT)) + b"\n")
        return 0
    if len(argv) != 1 or argv[0] not in LIVE_ACTIONS:
        raise SystemExit(
            "usage: finite_association_r1_activation_preparation_authority_v2.py "
            "--status|--create-marker-after-explicit-authorization|"
            "--resume-genesis|--materialize-capsule|--capture-runtime-candidate"
        )
    action = argv[0]
    if action == "--create-marker-after-explicit-authorization":
        _execute_marker_live()
    elif action == "--resume-genesis":
        root = _require_live_cli_boundary(action)
        registration_payload, registration, _ = _load_registration(root)
        marker_payload, marker = _load_contract(root, MARKER_PATH, "ATTEMPT_MARKER")
        _ensure_genesis(
            root,
            registration_payload,
            registration,
            marker_payload,
            marker,
            action,
        )
    elif action == "--materialize-capsule":
        root = _require_live_cli_boundary(action)
        _execute_capsule_at_root(root, action)
    else:
        root = _require_live_cli_boundary(action)
        _execute_runtime_at_root(root, live_action=action)
    return 0


if __name__ == "__main__":  # pragma: no cover - explicit future command only
    raise SystemExit(main())


__all__ = [
    "AUTHORITY_PATH",
    "ActivationPreparationQualification",
    "CAPSULE_ROOT",
    "CONTRACTS_PATH",
    "DORMANT_V1_PATHS",
    "HUMAN_PATH",
    "MACHINE_PATH",
    "MARKER_PATH",
    "NONCLAIMS",
    "OPERATOR_AUTHORIZATION_CONTEXT",
    "OPERATOR_AUTHORIZATION_SHA256",
    "PREPARATION_ROOT",
    "PUBLICATION_ANONYMITY_BOUNDARY",
    "PreparationAuthorityError",
    "RUNTIME_PATH",
    "TEST_PATH",
    "load_qualification",
    "static_qualification_snapshot",
    "status",
    "validate_future_scientific_carrier",
]
