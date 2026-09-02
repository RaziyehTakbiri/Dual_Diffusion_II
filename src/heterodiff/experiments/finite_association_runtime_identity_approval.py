"""Procedural review and approval for the A1 runtime identity.

This module is deliberately standard-library-only.  It separates immutable,
approved-false capture evidence from the one interactive transition of the
checked-in placeholder.  The transition is a local procedural safeguard, not
a signature, an authenticated reviewer identity, or proof that producer and
reviewer were different people.

All ordinary builders and validators are pure.  The only authority-changing
entry point is :func:`approve_checked_in_runtime_identity_interactively`.  It
requires three values to be entered on a TTY, performs a fresh capture through
one narrow integration boundary *after* confirmation, publishes the approval
receipt first, and then compare-and-replaces only the exact frozen placeholder.

The path protocol assumes the repository's non-hostile local-host threat
model.  Stable no-follow reads and an immediate pre-replacement check close
ordinary stale, symlink, and accidental-replacement failures; they do not
eliminate a hostile same-account directory-entry TOCTOU race.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
import sys
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, TextIO, Tuple

from heterodiff.experiments import (
    finite_association_runtime_identity as runtime_identity,
)


TARGET_PROFILE_ID = "m1-reference-macos-arm64-py311"
REVIEW_SCHEMA = "heterodiff-a1-production-runtime-identity-review-v1"
APPROVAL_SCHEMA = "heterodiff-a1-production-runtime-identity-approval-v1"
CAPTURE_OPERATION = "CAPTURE_RUNTIME_IDENTITY_CANDIDATE_V1"
RECAPTURE_OPERATION = "RECAPTURE_RUNTIME_IDENTITY_CANDIDATE_V1"
APPROVAL_OPERATION = "PROCEDURAL_RUNTIME_IDENTITY_APPROVAL_V1"
APPROVAL_CONTRACT_SCHEMA = (
    "heterodiff-a1-production-runtime-identity-approval-contract-v1"
)
APPROVAL_SOURCE_RELATIVE_PATH = (
    "src/heterodiff/experiments/"
    "finite_association_runtime_identity_approval.py"
)

CANDIDATE_ROOT_RELATIVE_PATH = (
    "requirements/runtime-identity-candidates/" + TARGET_PROFILE_ID
)
BASELINE_ROOT_RELATIVE_PATH = CANDIDATE_ROOT_RELATIVE_PATH + "/baselines"
APPROVAL_RECEIPT_RELATIVE_PATH = (
    "requirements/m1-reference-macos-arm64-py311.runtime-identity.approval.json"
)

FROZEN_PLACEHOLDER_MANIFEST_SHA256 = (
    "b17f4371aff0fd6da326c6c33f4d2807a6e9fa6ca79c1de78619947d9921f941"
)
FROZEN_PLACEHOLDER_FILE_SHA256 = (
    "ff29f82b27826d855cc3468da9e9cea23782a2dc5c919a19af439c8fe614b506"
)
FROZEN_PLACEHOLDER_SIZE_BYTES = 18_368

MAXIMUM_REVIEW_BYTES = 4 * 1024 * 1024
MAXIMUM_APPROVAL_RECEIPT_BYTES = 256 * 1024
MAXIMUM_PENDING_ATTEMPTS = 128
MAXIMUM_CAS_READ_ATTEMPTS = 16
PENDING_PREFIX = ".runtime-identity-pending-"
PROCEDURAL_ACKNOWLEDGEMENT = (
    "I UNDERSTAND THIS IS PROCEDURAL, NOT CRYPTOGRAPHIC APPROVAL"
)

_HEX_DIGITS = frozenset("0123456789abcdef")
_COMPONENT_NAMES = (
    "profile",
    "lockfile",
    "python_files",
    "modules",
    "distributions",
    "editable_install",
    "native_libraries",
    "native_pools",
    "accelerators",
)
_REVIEW_KEYS = frozenset(
    {
        "schema",
        "target_profile_id",
        "candidate",
        "placeholder_baseline",
        "capture_protocol",
        "capture_assessment",
        "component_comparison",
        "inventory_projection",
        "checks",
        "approval_ready",
        "blockers",
        "approved_manifest_preview",
        "report_sha256",
    }
)
_CAPTURE_ASSESSMENT_SCHEMA = (
    "heterodiff-a1-production-runtime-identity-capture-assessment-v1"
)
_APPROVAL_KEYS = frozenset(
    {
        "schema",
        "target_profile_id",
        "candidate",
        "review_report",
        "placeholder_precondition",
        "approved_manifest",
        "transition",
        "fresh_revalidation",
        "approval_protocol",
        "operator_confirmation",
        "limitations",
        "approval_receipt_sha256",
    }
)
_CAPTURE_PROTOCOL_KEYS = frozenset(
    {
        "operation",
        "capture_contract_sha256",
        "source_relative_path",
        "source_sha256",
        "identity_source_relative_path",
        "identity_source_sha256",
        "sanitized_environment_sha256",
    }
)


@dataclass(frozen=True)
class RuntimeIdentityRecapture:
    """Narrow result required from the capture integration boundary."""

    record: Mapping[str, object]
    assessment: "RuntimeIdentityCaptureAssessment"


@dataclass(frozen=True)
class RuntimeIdentityCaptureAssessment:
    """Validated semantic projection of one capture envelope.

    The capture implementation must construct this exact type only after its
    fresh child envelope and complete live-file pass have been validated.
    Report construction accepts no loose Boolean assessment mapping.
    """

    capture_protocol: Mapping[str, object]
    complete_installed_file_verification: bool
    double_capture_stable: bool
    installed_distributions: Tuple[Tuple[str, str, str], ...]
    placeholder_paths_absent: bool
    scientific_compute_executed: bool


@dataclass(frozen=True)
class ApprovedRuntimeIdentityBundle:
    """Fully related and live-file-verified approval bundle."""

    manifest: runtime_identity.RuntimeIdentityManifest
    candidate: Mapping[str, object]
    review_report: Mapping[str, object]
    approval_receipt: Mapping[str, object]


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _canonical_json(value: object) -> bytes:
    try:
        encoded = json.dumps(
            _plain(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise TypeError("value is not canonical-JSON serializable") from error
    return encoded.encode("ascii")


def _canonical_file_bytes(value: object) -> bytes:
    return _canonical_json(value) + b"\n"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_canonical_json(value))


def _self_digest(value: Mapping[str, object], field: str) -> str:
    body = dict(value)
    body.pop(field, None)
    return _sha256_json(body)


def _deep_freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType(
            {key: _deep_freeze(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _exact_keys(value: object, expected: Iterable[str], *, name: str) -> dict:
    if type(value) is not dict:
        raise ValueError(name + " must be an object")
    expected_set = frozenset(expected)
    actual = frozenset(value)
    if actual != expected_set or any(type(key) is not str for key in value):
        raise ValueError(name + " has a non-exact schema")
    return value


def _sha256(value: object, *, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _HEX_DIGITS for character in value)
    ):
        raise ValueError(name + " must be a lowercase SHA-256 digest")
    return value


def _bounded_ascii(
    value: object, *, name: str, maximum: int = 4096
) -> str:
    if type(value) is not str or not value or len(value) > maximum:
        raise ValueError(name + " must be a bounded nonempty string")
    if "\x00" in value:
        raise ValueError(name + " contains NUL")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError(name + " must be ASCII") from error
    return value


def _relative_path(value: object, *, name: str) -> str:
    path = _bounded_ascii(value, name=name, maximum=8192)
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or pure.as_posix() != path
        or any(part in (".", "..") for part in pure.parts)
    ):
        raise ValueError(name + " must be a normalized relative POSIX path")
    return path


def _candidate_relative_path(manifest_sha256: str) -> str:
    digest = _sha256(manifest_sha256, name="candidate manifest digest")
    return "%s/%s/candidate.json" % (CANDIDATE_ROOT_RELATIVE_PATH, digest)


def _review_relative_path(
    candidate_manifest_sha256: str, report_sha256: str
) -> str:
    candidate = _sha256(
        candidate_manifest_sha256, name="candidate manifest digest"
    )
    report = _sha256(report_sha256, name="review report digest")
    return "%s/%s/%s.review.json" % (
        CANDIDATE_ROOT_RELATIVE_PATH,
        candidate,
        report,
    )


def _baseline_archive_relative_path(file_sha256: str) -> str:
    digest = _sha256(file_sha256, name="placeholder file digest")
    return "%s/%s.placeholder.json" % (BASELINE_ROOT_RELATIVE_PATH, digest)


def _binding(
    *,
    relative_path: str,
    schema: str,
    self_digest_name: str,
    self_digest: str,
    payload: bytes,
    approved: Optional[bool] = None,
) -> Dict[str, object]:
    result: Dict[str, object] = {
        "relative_path": _relative_path(relative_path, name="binding path"),
        "schema": _bounded_ascii(schema, name="binding schema", maximum=256),
        self_digest_name: _sha256(self_digest, name=self_digest_name),
        "file_sha256": _sha256_bytes(payload),
        "size_bytes": len(payload),
    }
    if approved is not None:
        if type(approved) is not bool:
            raise TypeError("binding approval must be an exact boolean")
        result["approved"] = approved
    return result


def _placeholder_binding(payload: bytes) -> Dict[str, object]:
    _frozen_placeholder_record(payload)
    return {
        "checked_in_relative_path": runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH,
        "archive_relative_path": _baseline_archive_relative_path(
            FROZEN_PLACEHOLDER_FILE_SHA256
        ),
        "schema": runtime_identity.RUNTIME_IDENTITY_MANIFEST_SCHEMA,
        "manifest_sha256": FROZEN_PLACEHOLDER_MANIFEST_SHA256,
        "file_sha256": FROZEN_PLACEHOLDER_FILE_SHA256,
        "size_bytes": FROZEN_PLACEHOLDER_SIZE_BYTES,
        "approved": False,
    }


def _candidate_record(value: object) -> Dict[str, Any]:
    checked = runtime_identity.validate_runtime_identity_manifest(_plain(value))
    if checked["approved"] is not False:
        raise ValueError("runtime identity candidate must remain approved=false")
    for row in _manifest_file_rows(checked):
        if row["path"] == "/UNAPPROVED" or row["path"].startswith(
            "/UNAPPROVED/"
        ):
            raise ValueError("runtime identity candidate contains placeholder paths")
    return checked


def _manifest_file_rows(
    record: Mapping[str, object]
) -> Iterable[Mapping[str, object]]:
    for row in record["python_files"]:
        yield row
    for row in record["modules"]:
        yield row
    for distribution in record["distributions"]:
        for row in distribution["metadata_files"]:
            yield row
        for row in distribution["record_payloads"]:
            yield row
    yield record["editable_install"]["direct_url_identity"]
    for row in record["native_libraries"]:
        yield row


def _frozen_placeholder_record(payload: object) -> Dict[str, Any]:
    if type(payload) is not bytes:
        raise TypeError("frozen placeholder payload must be exact bytes")
    if (
        len(payload) != FROZEN_PLACEHOLDER_SIZE_BYTES
        or _sha256_bytes(payload) != FROZEN_PLACEHOLDER_FILE_SHA256
    ):
        raise ValueError("checked-in runtime identity placeholder bytes differ")
    record = runtime_identity.parse_runtime_identity_manifest_bytes(payload)
    if (
        record["approved"] is not False
        or record["manifest_sha256"] != FROZEN_PLACEHOLDER_MANIFEST_SHA256
    ):
        raise ValueError("checked-in runtime identity placeholder is not frozen")
    return record


def _capture_protocol(value: object) -> Dict[str, str]:
    row = _exact_keys(value, _CAPTURE_PROTOCOL_KEYS, name="capture protocol")
    if row["operation"] != CAPTURE_OPERATION:
        raise ValueError("capture protocol operation is not frozen")
    source_path = _relative_path(
        row["source_relative_path"], name="capture source path"
    )
    return {
        "operation": CAPTURE_OPERATION,
        "capture_contract_sha256": _sha256(
            row["capture_contract_sha256"], name="capture contract"
        ),
        "source_relative_path": source_path,
        "source_sha256": _sha256(row["source_sha256"], name="capture source"),
        "identity_source_relative_path": _relative_path(
            row["identity_source_relative_path"], name="identity source path"
        ),
        "identity_source_sha256": _sha256(
            row["identity_source_sha256"], name="identity source"
        ),
        "sanitized_environment_sha256": _sha256(
            row["sanitized_environment_sha256"],
            name="capture sanitized environment",
        ),
    }


def runtime_identity_approval_contract() -> Dict[str, object]:
    """Return the frozen, source-independent procedural approval contract."""

    return {
        "schema": APPROVAL_CONTRACT_SCHEMA,
        "target_profile_id": TARGET_PROFILE_ID,
        "manifest_schema": runtime_identity.RUNTIME_IDENTITY_MANIFEST_SCHEMA,
        "review_schema": REVIEW_SCHEMA,
        "approval_schema": APPROVAL_SCHEMA,
        "candidate_root_relative_path": CANDIDATE_ROOT_RELATIVE_PATH,
        "baseline_root_relative_path": BASELINE_ROOT_RELATIVE_PATH,
        "approval_receipt_relative_path": APPROVAL_RECEIPT_RELATIVE_PATH,
        "runtime_identity_relative_path": (
            runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH
        ),
        "placeholder_manifest_sha256": FROZEN_PLACEHOLDER_MANIFEST_SHA256,
        "placeholder_file_sha256": FROZEN_PLACEHOLDER_FILE_SHA256,
        "placeholder_size_bytes": FROZEN_PLACEHOLDER_SIZE_BYTES,
        "confirmation_mode": "interactive-tty-three-part-confirmation-v1",
        "publication_order": ["approval_receipt", "manifest_cas"],
        "changed_json_pointers": ["/approved", "/manifest_sha256"],
        "non_hostile_local_host": True,
        "cryptographic_approval": False,
        "reviewer_independence_proven": False,
    }


def build_runtime_identity_approval_protocol(
    approval_source_sha256: str,
) -> Dict[str, str]:
    """Bind the exact approval implementation to its frozen contract."""

    return {
        "operation": APPROVAL_OPERATION,
        "source_relative_path": APPROVAL_SOURCE_RELATIVE_PATH,
        "source_sha256": _sha256(
            approval_source_sha256, name="approval source"
        ),
        "approval_contract_sha256": _sha256_json(
            runtime_identity_approval_contract()
        ),
    }


def _approval_protocol(value: object) -> Dict[str, str]:
    row = _exact_keys(
        value,
        {
            "operation",
            "source_relative_path",
            "source_sha256",
            "approval_contract_sha256",
        },
        name="approval protocol",
    )
    expected = build_runtime_identity_approval_protocol(row["source_sha256"])
    if row != expected:
        raise ValueError("approval protocol differs from its frozen contract")
    return expected


def _normalized_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _installed_distributions(
    value: object,
) -> Tuple[Tuple[str, str, str], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("installed distributions must be an ordered sequence")
    rows = []
    normalized = set()
    for index, raw in enumerate(value):
        if type(raw) not in (list, tuple) or len(raw) != 3:
            raise ValueError("installed distribution row is not an exact triple")
        name = _bounded_ascii(
            raw[0], name="installed distribution %d name" % index, maximum=128
        )
        version = _bounded_ascii(
            raw[1], name="installed distribution %d version" % index, maximum=128
        )
        origin = _bounded_ascii(
            raw[2], name="installed distribution %d origin" % index, maximum=8192
        )
        pure_origin = PurePosixPath(origin)
        if (
            not pure_origin.is_absolute()
            or pure_origin.as_posix() != origin
            or any(part in (".", "..") for part in pure_origin.parts)
        ):
            raise ValueError("installed distribution origin is not canonical")
        normalized_name = _normalized_distribution_name(name)
        if normalized_name in normalized:
            raise ValueError("installed distribution names are duplicated")
        normalized.add(normalized_name)
        rows.append((name, version, origin))
    expected_order = tuple(
        sorted(rows, key=lambda row: (_normalized_distribution_name(row[0]), row))
    )
    if tuple(rows) != expected_order:
        raise ValueError("installed distributions are not canonically ordered")
    return tuple(rows)


def _capture_assessment_record(
    assessment: RuntimeIdentityCaptureAssessment,
    *,
    candidate: Optional[Mapping[str, object]] = None,
) -> Dict[str, object]:
    if type(assessment) is not RuntimeIdentityCaptureAssessment:
        raise TypeError(
            "review construction requires a validated capture assessment"
        )
    protocol = _capture_protocol(_plain(assessment.capture_protocol))
    booleans = (
        assessment.complete_installed_file_verification,
        assessment.double_capture_stable,
        assessment.placeholder_paths_absent,
        assessment.scientific_compute_executed,
    )
    if any(type(value) is not bool for value in booleans):
        raise TypeError("capture assessment flags must be exact booleans")
    installed = _installed_distributions(assessment.installed_distributions)
    candidate_origins = {}
    editable_origin = None
    if candidate is not None:
        checked_candidate = _candidate_record(candidate)
        for distribution in checked_candidate["distributions"]:
            origins = {
                os.path.dirname(row["path"])
                for row in distribution["metadata_files"]
            }
            if len(origins) != 1:
                raise ValueError("candidate distribution metadata origin is ambiguous")
            candidate_origins[
                _normalized_distribution_name(distribution["name"])
            ] = next(iter(origins))
        editable_origin = os.path.dirname(
            checked_candidate["editable_install"]["direct_url_identity"]["path"]
        )
    expected_by_normalized = {
        _normalized_distribution_name(name): (
            name,
            version,
            candidate_origins.get(_normalized_distribution_name(name)),
        )
        for name, version in runtime_identity.REQUIRED_DISTRIBUTIONS
    }
    expected_by_normalized["heterodiff"] = (
        "heterodiff",
        "0.1.0",
        editable_origin,
    )
    observed_by_normalized = {
        _normalized_distribution_name(name): (name, version, origin)
        for name, version, origin in installed
    }
    unexpected = [
        [name, version, origin]
        for name, version, origin in installed
        if _normalized_distribution_name(name) not in expected_by_normalized
    ]
    blockers = []
    for normalized, (name, version, expected_origin) in expected_by_normalized.items():
        observed = observed_by_normalized.get(normalized)
        if observed is None:
            blockers.append("missing_distribution:%s==%s" % (name, version))
        elif observed[1] != version:
            blockers.append(
                "distribution_version:%s:expected=%s:observed=%s"
                % (name, version, observed[1])
            )
        elif expected_origin is not None and observed[2] != expected_origin:
            blockers.append(
                "distribution_origin:%s:expected=%s:observed=%s"
                % (name, expected_origin, observed[2])
            )
    blockers.extend(
        "unexpected_distribution:%s==%s" % (name, version)
        for name, version, _origin in unexpected
    )
    if not assessment.complete_installed_file_verification:
        blockers.append("complete_installed_file_verification:false")
    if not assessment.double_capture_stable:
        blockers.append("double_capture_stable:false")
    if not assessment.placeholder_paths_absent:
        blockers.append("placeholder_paths_absent:false")
    if assessment.scientific_compute_executed:
        blockers.append("scientific_compute_executed:true")
    body: Dict[str, object] = {
        "schema": _CAPTURE_ASSESSMENT_SCHEMA,
        "capture_protocol": protocol,
        "complete_installed_file_verification": (
            assessment.complete_installed_file_verification
        ),
        "double_capture_stable": assessment.double_capture_stable,
        "installed_distributions": [list(row) for row in installed],
        "exact_installed_distribution_set": not any(
            blocker.startswith(
                (
                    "missing_distribution:",
                    "distribution_version:",
                    "distribution_origin:",
                    "unexpected_distribution:",
                )
            )
            for blocker in blockers
        ),
        "unexpected_distributions": unexpected,
        "placeholder_paths_absent": assessment.placeholder_paths_absent,
        "scientific_compute_executed": assessment.scientific_compute_executed,
        "blockers": blockers,
        "approval_ready": not blockers,
    }
    record = dict(body)
    record["assessment_sha256"] = _sha256_json(body)
    return record


def _assessment_from_record(value: object) -> RuntimeIdentityCaptureAssessment:
    expected_keys = {
        "schema",
        "capture_protocol",
        "complete_installed_file_verification",
        "double_capture_stable",
        "installed_distributions",
        "exact_installed_distribution_set",
        "unexpected_distributions",
        "placeholder_paths_absent",
        "scientific_compute_executed",
        "blockers",
        "approval_ready",
        "assessment_sha256",
    }
    row = _exact_keys(value, expected_keys, name="capture assessment")
    if row["schema"] != _CAPTURE_ASSESSMENT_SCHEMA:
        raise ValueError("capture assessment schema is not frozen")
    supplied = _sha256(row["assessment_sha256"], name="capture assessment")
    if supplied != _self_digest(row, "assessment_sha256"):
        raise ValueError("capture assessment self-digest differs")
    for name in (
        "complete_installed_file_verification",
        "double_capture_stable",
        "exact_installed_distribution_set",
        "placeholder_paths_absent",
        "scientific_compute_executed",
        "approval_ready",
    ):
        if type(row[name]) is not bool:
            raise ValueError("capture assessment flags must be exact booleans")
    return RuntimeIdentityCaptureAssessment(
        capture_protocol=_capture_protocol(row["capture_protocol"]),
        complete_installed_file_verification=row[
            "complete_installed_file_verification"
        ],
        double_capture_stable=row["double_capture_stable"],
        installed_distributions=_installed_distributions(
            row["installed_distributions"]
        ),
        placeholder_paths_absent=row["placeholder_paths_absent"],
        scientific_compute_executed=row["scientific_compute_executed"],
    )


def derive_approved_runtime_identity_manifest(
    candidate: Mapping[str, object],
) -> Dict[str, Any]:
    """Derive the sole approved manifest from one approved-false candidate."""

    checked = _candidate_record(candidate)
    approved = deepcopy(checked)
    approved["approved"] = True
    approved["manifest_sha256"] = (
        runtime_identity.runtime_identity_manifest_self_digest(approved)
    )
    approved = runtime_identity.validate_runtime_identity_manifest(approved)
    changed = tuple(
        "/" + key for key in sorted(checked) if checked[key] != approved[key]
    )
    if changed != ("/approved", "/manifest_sha256"):
        raise RuntimeError("approved runtime identity transition is not minimal")
    return approved


def _component_digest(record: Mapping[str, object], name: str) -> str:
    return _sha256_json(record[name])


def _inventory_projection(candidate: Mapping[str, object]) -> Dict[str, object]:
    distributions = []
    for row in candidate["distributions"]:
        metadata = _plain(row["metadata_files"])
        origins = {os.path.dirname(item["path"]) for item in metadata}
        if len(origins) != 1:
            raise ValueError("distribution metadata lacks one exact origin")
        payloads = _plain(row["record_payloads"])
        distributions.append(
            {
                "name": row["name"],
                "version": row["version"],
                "metadata_origin": next(iter(origins)),
                "metadata_files": metadata,
                "record_entry_count": row["record_entry_count"],
                "record_payload_count": len(payloads),
                "record_payloads_sha256": _sha256_json(payloads),
            }
        )
    return {
        "python_files": _plain(candidate["python_files"]),
        "modules": _plain(candidate["modules"]),
        "distributions": distributions,
        "editable_install": _plain(candidate["editable_install"]),
        "native_libraries": _plain(candidate["native_libraries"]),
        "native_pools": _plain(candidate["native_pools"]),
        "accelerators": _plain(candidate["accelerators"]),
    }


def build_runtime_identity_review_report(
    candidate: Mapping[str, object],
    *,
    frozen_placeholder_payload: bytes,
    capture_assessment: RuntimeIdentityCaptureAssessment,
) -> Dict[str, Any]:
    """Build a deterministic, non-authorizing review report."""

    checked = _candidate_record(candidate)
    placeholder = _frozen_placeholder_record(frozen_placeholder_payload)
    assessment = _capture_assessment_record(
        capture_assessment, candidate=checked
    )
    protocol = assessment["capture_protocol"]
    candidate_payload = runtime_identity.canonical_runtime_identity_manifest_bytes(
        checked
    )
    approved = derive_approved_runtime_identity_manifest(checked)
    approved_payload = runtime_identity.canonical_runtime_identity_manifest_bytes(
        approved
    )
    comparisons = [
        {
            "component": name,
            "placeholder_sha256": _component_digest(placeholder, name),
            "candidate_sha256": _component_digest(checked, name),
            "equal": placeholder[name] == checked[name],
        }
        for name in _COMPONENT_NAMES
    ]
    body: Dict[str, object] = {
        "schema": REVIEW_SCHEMA,
        "target_profile_id": TARGET_PROFILE_ID,
        "candidate": _binding(
            relative_path=_candidate_relative_path(checked["manifest_sha256"]),
            schema=runtime_identity.RUNTIME_IDENTITY_MANIFEST_SCHEMA,
            self_digest_name="manifest_sha256",
            self_digest=checked["manifest_sha256"],
            payload=candidate_payload,
            approved=False,
        ),
        "placeholder_baseline": _placeholder_binding(
            frozen_placeholder_payload
        ),
        "capture_protocol": protocol,
        "capture_assessment": assessment,
        "component_comparison": comparisons,
        "inventory_projection": _inventory_projection(checked),
        "checks": {
            "candidate_approved": False,
            "target_profile_exact": True,
            "lock_identity_exact": True,
            "required_distribution_set_exact": True,
            "record_payload_inventory_complete": assessment[
                "complete_installed_file_verification"
            ],
            "editable_source_manifest_authoritative": True,
            "native_pool_library_alignment": True,
            "execution_device_enforced_cpu": True,
            "cuda_unavailable_uninitialized": True,
            "xpu_unavailable_uninitialized": True,
            "mps_operation_performed": False,
            "double_capture_stable": assessment["double_capture_stable"],
            "exact_installed_distribution_set": assessment[
                "exact_installed_distribution_set"
            ],
            "unexpected_distributions": deepcopy(
                assessment["unexpected_distributions"]
            ),
            "placeholder_paths_absent": assessment[
                "placeholder_paths_absent"
            ],
            "scientific_compute_executed": assessment[
                "scientific_compute_executed"
            ],
        },
        "approval_ready": assessment["approval_ready"],
        "blockers": deepcopy(assessment["blockers"]),
        "approved_manifest_preview": _binding(
            relative_path=runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH,
            schema=runtime_identity.RUNTIME_IDENTITY_MANIFEST_SCHEMA,
            self_digest_name="manifest_sha256",
            self_digest=approved["manifest_sha256"],
            payload=approved_payload,
            approved=True,
        ),
    }
    report = dict(body)
    report["report_sha256"] = _sha256_json(body)
    return report


def validate_runtime_identity_review_report(
    value: Mapping[str, object],
    *,
    candidate: Mapping[str, object],
    frozen_placeholder_payload: bytes,
) -> Dict[str, Any]:
    """Strictly validate a report by deterministic reconstruction."""

    raw = _exact_keys(_plain(value), _REVIEW_KEYS, name="review report")
    if raw["schema"] != REVIEW_SCHEMA or raw["target_profile_id"] != TARGET_PROFILE_ID:
        raise ValueError("review report identity is not frozen")
    supplied = _sha256(raw["report_sha256"], name="review report")
    if supplied != _self_digest(raw, "report_sha256"):
        raise ValueError("review report self-digest differs")
    assessment = _assessment_from_record(raw["capture_assessment"])
    expected = build_runtime_identity_review_report(
        candidate,
        frozen_placeholder_payload=frozen_placeholder_payload,
        capture_assessment=assessment,
    )
    if raw != expected:
        raise ValueError("review report differs from deterministic reconstruction")
    return raw


def canonical_runtime_identity_review_bytes(
    value: Mapping[str, object],
    *,
    candidate: Mapping[str, object],
    frozen_placeholder_payload: bytes,
) -> bytes:
    checked = validate_runtime_identity_review_report(
        value,
        candidate=candidate,
        frozen_placeholder_payload=frozen_placeholder_payload,
    )
    return _canonical_file_bytes(checked)


def _reject_duplicate_keys(pairs: Sequence[Tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("canonical record contains duplicate JSON keys")
        result[key] = value
    return result


def _parse_canonical_json(payload: object, *, maximum: int, name: str) -> dict:
    if type(payload) is not bytes:
        raise TypeError(name + " payload must be exact bytes")
    if not payload or len(payload) > maximum:
        raise ValueError(name + " has an invalid byte length")
    try:
        value = json.loads(
            payload.decode("ascii"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError("non-finite JSON constant " + token)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as error:
        raise ValueError(name + " is invalid JSON") from error
    if type(value) is not dict or payload != _canonical_file_bytes(value):
        raise ValueError(name + " bytes are not canonical")
    return value


def parse_runtime_identity_review_bytes(
    payload: object,
    *,
    candidate: Mapping[str, object],
    frozen_placeholder_payload: bytes,
) -> Dict[str, Any]:
    value = _parse_canonical_json(
        payload, maximum=MAXIMUM_REVIEW_BYTES, name="review report"
    )
    return validate_runtime_identity_review_report(
        value,
        candidate=candidate,
        frozen_placeholder_payload=frozen_placeholder_payload,
    )


def _confirmation_record() -> Dict[str, object]:
    return {
        "mode": "interactive-tty-three-part-confirmation-v1",
        "candidate_digest_reentered": True,
        "report_digest_reentered": True,
        "procedural_only_acknowledged": True,
    }


def _fresh_revalidation_record(
    *,
    candidate: Mapping[str, object],
    report: Mapping[str, object],
    recapture: RuntimeIdentityRecapture,
) -> Dict[str, object]:
    if type(recapture) is not RuntimeIdentityRecapture:
        raise TypeError("fresh capture boundary returned the wrong exact type")
    checked = _candidate_record(candidate)
    recaptured = _candidate_record(recapture.record)
    assessment = _capture_assessment_record(
        recapture.assessment, candidate=recaptured
    )
    if assessment["approval_ready"] is not True or assessment["blockers"] != []:
        raise ValueError("fresh candidate capture is not approval-ready")
    if assessment != report["capture_assessment"]:
        raise ValueError("fresh candidate capture assessment differs from review")
    candidate_payload = runtime_identity.canonical_runtime_identity_manifest_bytes(
        checked
    )
    recaptured_payload = runtime_identity.canonical_runtime_identity_manifest_bytes(
        recaptured
    )
    if recaptured_payload != candidate_payload:
        raise ValueError("fresh runtime identity recapture differs from candidate")
    protocol = report["capture_protocol"]
    return {
        "operation": RECAPTURE_OPERATION,
        "candidate_manifest_sha256": checked["manifest_sha256"],
        "candidate_file_sha256": _sha256_bytes(candidate_payload),
        "capture_contract_sha256": protocol["capture_contract_sha256"],
        "capture_source_sha256": protocol["source_sha256"],
        "identity_source_sha256": protocol["identity_source_sha256"],
        "capture_assessment_sha256": assessment["assessment_sha256"],
        "complete_installed_file_verification": True,
        "recaptured_after_operator_confirmation": True,
        "scientific_compute_executed": False,
    }


def build_runtime_identity_approval_receipt(
    candidate: Mapping[str, object],
    review_report: Mapping[str, object],
    *,
    frozen_placeholder_payload: bytes,
    recapture: RuntimeIdentityRecapture,
    approval_protocol: Mapping[str, object],
) -> Dict[str, Any]:
    """Build the deterministic conditional approval receipt."""

    checked = _candidate_record(candidate)
    report = validate_runtime_identity_review_report(
        review_report,
        candidate=checked,
        frozen_placeholder_payload=frozen_placeholder_payload,
    )
    if report["approval_ready"] is not True or report["blockers"] != []:
        raise PermissionError("runtime identity review report is not approval-ready")
    approved = derive_approved_runtime_identity_manifest(checked)
    approved_payload = runtime_identity.canonical_runtime_identity_manifest_bytes(
        approved
    )
    report_payload = _canonical_file_bytes(report)
    fresh = _fresh_revalidation_record(
        candidate=checked, report=report, recapture=recapture
    )
    checked_approval_protocol = _approval_protocol(_plain(approval_protocol))
    body: Dict[str, object] = {
        "schema": APPROVAL_SCHEMA,
        "target_profile_id": TARGET_PROFILE_ID,
        "candidate": deepcopy(report["candidate"]),
        "review_report": _binding(
            relative_path=_review_relative_path(
                checked["manifest_sha256"], report["report_sha256"]
            ),
            schema=REVIEW_SCHEMA,
            self_digest_name="report_sha256",
            self_digest=report["report_sha256"],
            payload=report_payload,
        ),
        "placeholder_precondition": deepcopy(report["placeholder_baseline"]),
        "approved_manifest": _binding(
            relative_path=runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH,
            schema=runtime_identity.RUNTIME_IDENTITY_MANIFEST_SCHEMA,
            self_digest_name="manifest_sha256",
            self_digest=approved["manifest_sha256"],
            payload=approved_payload,
            approved=True,
        ),
        "transition": {
            "changed_json_pointers": ["/approved", "/manifest_sha256"],
            "from_approved": False,
            "to_approved": True,
            "receipt_alone_grants_authority": False,
        },
        "fresh_revalidation": fresh,
        "approval_protocol": checked_approval_protocol,
        "operator_confirmation": _confirmation_record(),
        "limitations": {
            "threat_model": "non-hostile-local-host-v1",
            "cryptographic_approval": False,
            "reviewer_identity_authenticated": False,
            "reviewer_independence_proven": False,
            "producer_reviewer_separation_proven": False,
            "hostile_directory_toctou_closed": False,
        },
    }
    receipt = dict(body)
    receipt["approval_receipt_sha256"] = _sha256_json(body)
    return receipt


def validate_runtime_identity_approval_receipt(
    value: Mapping[str, object],
    *,
    candidate: Mapping[str, object],
    review_report: Mapping[str, object],
    frozen_placeholder_payload: bytes,
) -> Dict[str, Any]:
    """Validate relational receipt fields without claiming live revalidation."""

    raw = _exact_keys(_plain(value), _APPROVAL_KEYS, name="approval receipt")
    if raw["schema"] != APPROVAL_SCHEMA or raw["target_profile_id"] != TARGET_PROFILE_ID:
        raise ValueError("approval receipt identity is not frozen")
    supplied = _sha256(
        raw["approval_receipt_sha256"], name="approval receipt"
    )
    if supplied != _self_digest(raw, "approval_receipt_sha256"):
        raise ValueError("approval receipt self-digest differs")
    checked = _candidate_record(candidate)
    report = validate_runtime_identity_review_report(
        review_report,
        candidate=checked,
        frozen_placeholder_payload=frozen_placeholder_payload,
    )
    # Historical validation cannot repeat the capture here.  Reconstruct the
    # sole admitted receipt with an exact successful semantic recapture.
    semantic_recapture = RuntimeIdentityRecapture(
        record=checked,
        assessment=_assessment_from_record(report["capture_assessment"]),
    )
    expected = build_runtime_identity_approval_receipt(
        checked,
        report,
        frozen_placeholder_payload=frozen_placeholder_payload,
        recapture=semantic_recapture,
        approval_protocol=_approval_protocol(raw["approval_protocol"]),
    )
    if raw != expected:
        raise ValueError("approval receipt differs from deterministic reconstruction")
    return raw


def canonical_runtime_identity_approval_bytes(
    value: Mapping[str, object],
    *,
    candidate: Mapping[str, object],
    review_report: Mapping[str, object],
    frozen_placeholder_payload: bytes,
) -> bytes:
    checked = validate_runtime_identity_approval_receipt(
        value,
        candidate=candidate,
        review_report=review_report,
        frozen_placeholder_payload=frozen_placeholder_payload,
    )
    return _canonical_file_bytes(checked)


def parse_runtime_identity_approval_bytes(
    payload: object,
    *,
    candidate: Mapping[str, object],
    review_report: Mapping[str, object],
    frozen_placeholder_payload: bytes,
) -> Dict[str, Any]:
    value = _parse_canonical_json(
        payload,
        maximum=MAXIMUM_APPROVAL_RECEIPT_BYTES,
        name="approval receipt",
    )
    return validate_runtime_identity_approval_receipt(
        value,
        candidate=candidate,
        review_report=review_report,
        frozen_placeholder_payload=frozen_placeholder_payload,
    )


def _path_identity(metadata: os.stat_result) -> Tuple[int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


class _PathChangedDuringStableRead(RuntimeError):
    """Internal signal for a pathname replaced during a stable read."""


def _reject_symlink_ancestors(path: Path, *, name: str) -> None:
    absolute = Path(os.path.abspath(os.fspath(path)))
    current = absolute.parent
    while True:
        metadata = os.lstat(current)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(name + " ancestors must be non-symlink directories")
        if current.parent == current:
            break
        current = current.parent


def _read_regular_file_stably(
    path: Path, maximum_bytes: int, *, name: str
) -> bytes:
    path = Path(path)
    if not path.is_absolute():
        raise RuntimeError(name + " path must be absolute")
    _reject_symlink_ancestors(path, name=name)
    endpoint_before = os.lstat(path)
    if (
        stat.S_ISLNK(endpoint_before.st_mode)
        or not stat.S_ISREG(endpoint_before.st_mode)
        or endpoint_before.st_size > maximum_bytes
    ):
        raise RuntimeError(name + " is not a bounded regular file")
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    nonblock = getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(os.fspath(path), os.O_RDONLY | nofollow | nonblock)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > maximum_bytes:
            raise RuntimeError(name + " is not a bounded regular file")
        blocks = []
        remaining = before.st_size
        while remaining:
            block = os.read(descriptor, min(remaining, 1024 * 1024))
            if not block:
                raise RuntimeError(name + " was truncated while reading")
            blocks.append(block)
            remaining -= len(block)
        if os.read(descriptor, 1):
            raise RuntimeError(name + " grew while reading")
        after = os.fstat(descriptor)
        endpoint = os.lstat(path)
        if (
            _path_identity(endpoint_before) != _path_identity(before)
            or _path_identity(before) != _path_identity(after)
            or _path_identity(after) != _path_identity(endpoint)
            or stat.S_ISLNK(endpoint.st_mode)
        ):
            raise _PathChangedDuringStableRead(name + " changed while reading")
        return b"".join(blocks)
    finally:
        os.close(descriptor)


def _read_runtime_identity_cas_state(
    path: Path, approved_payload: bytes, *, name: str
) -> bytes:
    """Read one of the only two admissible CAS states with bounded retry.

    An identical concurrent approver may atomically replace the pathname after
    this process opens it.  The general stable reader must reject that inode
    change.  At this one CAS boundary, retry it a fixed number of times and
    still accept only the exact frozen placeholder or exact approved target.
    Every other read failure or byte state remains immediately fail-closed.
    """

    for _ in range(MAXIMUM_CAS_READ_ATTEMPTS):
        try:
            payload = _read_regular_file_stably(
                path,
                runtime_identity.MAXIMUM_MANIFEST_BYTES,
                name=name,
            )
        except _PathChangedDuringStableRead:
            continue
        if payload != approved_payload:
            _frozen_placeholder_record(payload)
        return payload
    raise RuntimeError(name + " did not stabilize during bounded CAS retry")


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(os.fspath(directory), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ensure_directory(directory: Path) -> None:
    missing = []
    current = directory
    while True:
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            missing.append(current)
            if current.parent == current:
                raise RuntimeError("cannot find a regular ancestor")
            current = current.parent
            continue
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError("publication directory ancestry is unsafe")
        break
    for path in reversed(missing):
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(
                metadata.st_mode
            ):
                raise RuntimeError(
                    "concurrent publication created an unsafe path"
                )
        _fsync_directory(path.parent)


def _new_pending_file(parent: Path) -> Tuple[int, Path]:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    for _ in range(MAXIMUM_PENDING_ATTEMPTS):
        path = parent / (PENDING_PREFIX + secrets.token_hex(16))
        try:
            descriptor = os.open(
                os.fspath(path),
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow,
                0o600,
            )
        except FileExistsError:
            continue
        return descriptor, path
    raise RuntimeError("could not allocate an exclusive pending approval file")


def _write_all(handle: Any, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = handle.write(view)
        if written is None:
            written = 0
        if written <= 0:
            raise RuntimeError("approval publication write did not progress")
        view = view[written:]


def _publish_exclusive_bytes(path: Path, payload: bytes, *, maximum: int) -> None:
    """Publish once, or adopt exact bytes from a concurrent publisher.

    A process crash can leave its random pending file behind.  Such a file is
    inert: it is never interpreted as evidence, never blocks a later random
    pending allocation, and cannot grant authority.  This lock-free protocol
    intentionally does not auto-delete old pending files because it cannot
    distinguish an orphan from another live concurrent writer.  Manual
    hygiene is bounded to regular, non-symlink files whose names are the exact
    ``PENDING_PREFIX`` plus 32 lowercase hexadecimal characters in the one
    affected directory.
    """

    if type(payload) is not bytes or not payload or len(payload) > maximum:
        raise ValueError("publication payload has an invalid size")
    _ensure_directory(path.parent)
    try:
        existing = _read_regular_file_stably(path, maximum, name="published record")
    except FileNotFoundError:
        existing = None
    if existing is not None:
        if existing != payload:
            raise FileExistsError("a different immutable record already exists")
        return
    descriptor, pending = _new_pending_file(path.parent)
    linked = False
    try:
        with os.fdopen(descriptor, "wb") as handle:
            _write_all(handle, payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(os.fspath(pending), os.fspath(path), follow_symlinks=False)
            linked = True
            _fsync_directory(path.parent)
        except FileExistsError:
            existing = _read_regular_file_stably(
                path, maximum, name="concurrent immutable record"
            )
            if existing != payload:
                raise FileExistsError(
                    "a different concurrent immutable record won publication"
                )
    finally:
        try:
            pending.unlink()
        except FileNotFoundError:
            pass
        _fsync_directory(path.parent)
    if not linked:
        existing = _read_regular_file_stably(
            path, maximum, name="adopted immutable record"
        )
        if existing != payload:
            raise RuntimeError("immutable publication did not converge")


def _workspace_path(root: Path, relative_path: str) -> Path:
    relative = _relative_path(relative_path, name="workspace-relative path")
    absolute_root = Path(os.path.abspath(os.fspath(root)))
    path = absolute_root / relative
    if os.path.commonpath((os.fspath(absolute_root), os.fspath(path))) != os.fspath(
        absolute_root
    ):
        raise RuntimeError("workspace-relative path escapes its root")
    return path


def _live_approval_protocol(root: Path) -> Dict[str, str]:
    source_payload = _read_regular_file_stably(
        _workspace_path(root, APPROVAL_SOURCE_RELATIVE_PATH),
        MAXIMUM_REVIEW_BYTES,
        name="runtime identity approval source",
    )
    source_sha256 = _sha256_bytes(source_payload)
    if source_sha256 != _IMPORTED_APPROVAL_SOURCE_SHA256:
        raise RuntimeError("live approval source differs from imported code")
    return build_runtime_identity_approval_protocol(source_sha256)


def _publish_candidate_and_review(
    root: Path,
    candidate: Mapping[str, object],
    report: Mapping[str, object],
    *,
    frozen_placeholder_payload: bytes,
) -> Tuple[Path, Path]:
    checked = _candidate_record(candidate)
    review = validate_runtime_identity_review_report(
        report,
        candidate=checked,
        frozen_placeholder_payload=frozen_placeholder_payload,
    )
    candidate_payload = runtime_identity.canonical_runtime_identity_manifest_bytes(
        checked
    )
    report_payload = _canonical_file_bytes(review)
    candidate_path = _workspace_path(
        root, _candidate_relative_path(checked["manifest_sha256"])
    )
    baseline_path = _workspace_path(
        root, _baseline_archive_relative_path(FROZEN_PLACEHOLDER_FILE_SHA256)
    )
    review_path = _workspace_path(
        root,
        _review_relative_path(
            checked["manifest_sha256"], review["report_sha256"]
        ),
    )
    _publish_exclusive_bytes(
        baseline_path,
        frozen_placeholder_payload,
        maximum=runtime_identity.MAXIMUM_MANIFEST_BYTES,
    )
    _publish_exclusive_bytes(
        candidate_path,
        candidate_payload,
        maximum=runtime_identity.MAXIMUM_MANIFEST_BYTES,
    )
    _publish_exclusive_bytes(
        review_path, report_payload, maximum=MAXIMUM_REVIEW_BYTES
    )
    return candidate_path, review_path


def publish_runtime_identity_candidate_and_review(
    candidate: Mapping[str, object], report: Mapping[str, object]
) -> Tuple[Path, Path]:
    """Publish non-authorizing content-addressed evidence in this workspace."""

    root = _repository_root()
    placeholder = _read_regular_file_stably(
        root / runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH,
        runtime_identity.MAXIMUM_MANIFEST_BYTES,
        name="frozen runtime identity placeholder",
    )
    _frozen_placeholder_record(placeholder)
    return _publish_candidate_and_review(
        root,
        candidate,
        report,
        frozen_placeholder_payload=placeholder,
    )


def _require_tty_streams(input_stream: TextIO, output_stream: TextIO) -> None:
    if not callable(getattr(input_stream, "isatty", None)) or not input_stream.isatty():
        raise PermissionError("runtime identity approval requires an interactive TTY")
    if not callable(getattr(output_stream, "isatty", None)) or not output_stream.isatty():
        raise PermissionError("runtime identity approval output requires a TTY")


def _read_confirmation(
    candidate_sha256: str,
    report_sha256: str,
    *,
    input_stream: TextIO,
    output_stream: TextIO,
) -> Dict[str, object]:
    """Read the sole three-part confirmation; streams are private test seams."""

    expected_candidate = _sha256(candidate_sha256, name="candidate digest")
    expected_report = _sha256(report_sha256, name="review report digest")
    _require_tty_streams(input_stream, output_stream)
    output_stream.write("Candidate manifest SHA-256: " + expected_candidate + "\n")
    output_stream.write("Review report SHA-256: " + expected_report + "\n")
    output_stream.write(
        "This is procedural only; it is not cryptographic or independent approval.\n"
    )
    output_stream.write("Re-enter candidate digest: ")
    output_stream.flush()
    candidate_text = input_stream.readline()
    output_stream.write("Re-enter review digest: ")
    output_stream.flush()
    report_text = input_stream.readline()
    output_stream.write("Enter the exact acknowledgement phrase: ")
    output_stream.flush()
    acknowledgement = input_stream.readline()
    if not candidate_text or not report_text or not acknowledgement:
        raise PermissionError("runtime identity approval confirmation ended early")
    if (
        candidate_text.rstrip("\r\n") != expected_candidate
        or report_text.rstrip("\r\n") != expected_report
        or acknowledgement.rstrip("\r\n") != PROCEDURAL_ACKNOWLEDGEMENT
    ):
        raise PermissionError("runtime identity approval confirmation differs")
    return _confirmation_record()


def _display_review_summary(
    review_report: Mapping[str, object], *, output_stream: TextIO
) -> None:
    """Display the bounded critical inventory before confirmation prompts."""

    report = _plain(review_report)
    if type(report) is not dict or set(report) != _REVIEW_KEYS:
        raise ValueError("review display requires one validated exact report")
    summary = {
        "schema": "heterodiff-a1-runtime-identity-operator-review-summary-v1",
        "target_profile_id": report["target_profile_id"],
        "candidate": report["candidate"],
        "review_report_sha256": report["report_sha256"],
        "approved_manifest_preview": report["approved_manifest_preview"],
        "approval_ready": report["approval_ready"],
        "blockers": report["blockers"],
        "component_comparison": report["component_comparison"],
        "installed_distributions": report["capture_assessment"][
            "installed_distributions"
        ],
        "unexpected_distributions": report["capture_assessment"][
            "unexpected_distributions"
        ],
        "python_files": report["inventory_projection"]["python_files"],
        "modules": report["inventory_projection"]["modules"],
        "distributions": report["inventory_projection"]["distributions"],
        "editable_install": report["inventory_projection"]["editable_install"],
        "native_libraries": report["inventory_projection"]["native_libraries"],
        "native_pools": report["inventory_projection"]["native_pools"],
        "accelerators": report["inventory_projection"]["accelerators"],
        "procedural_only": True,
        "cryptographic_approval": False,
        "reviewer_independence_proven": False,
    }
    payload = _canonical_file_bytes(summary)
    if len(payload) > MAXIMUM_REVIEW_BYTES:
        raise ValueError("operator review summary exceeds its fixed byte limit")
    output_stream.write(payload.decode("ascii"))
    output_stream.flush()


def _recapture_after_confirmation(root: Path) -> RuntimeIdentityRecapture:
    """Load the capture implementation only at the approval boundary.

    Parent integration must provide
    ``recapture_runtime_identity_candidate_for_approval(root)`` and return this
    module's exact :class:`RuntimeIdentityRecapture` type.  Until that exists,
    the interactive transition fails before publishing a receipt.
    """

    try:
        from heterodiff.experiments import (  # pylint: disable=import-outside-toplevel
            finite_association_runtime_identity_capture as capture,
        )
    except ImportError as error:
        raise RuntimeError(
            "runtime identity capture integration is not implemented"
        ) from error
    boundary = getattr(
        capture, "recapture_runtime_identity_candidate_for_approval", None
    )
    if not callable(boundary):
        raise RuntimeError(
            "runtime identity capture integration lacks the approval boundary"
        )
    result = boundary(root)
    if type(result) is not RuntimeIdentityRecapture:
        raise TypeError("runtime identity capture integration returned wrong type")
    return result


def _compare_and_replace_frozen_placeholder(
    path: Path, approved_payload: bytes
) -> None:
    """Perform the one admitted placeholder CAS under the local-host model."""

    if type(approved_payload) is not bytes:
        raise TypeError("approved manifest payload must be exact bytes")
    approved = runtime_identity.parse_runtime_identity_manifest_bytes(
        approved_payload
    )
    if approved["approved"] is not True:
        raise ValueError("CAS target is not an approved runtime identity")
    current = _read_runtime_identity_cas_state(
        path,
        approved_payload,
        name="checked-in runtime identity",
    )
    if current == approved_payload:
        return
    _ensure_directory(path.parent)
    descriptor, pending = _new_pending_file(path.parent)
    replaced = False
    try:
        with os.fdopen(descriptor, "wb") as handle:
            _write_all(handle, approved_payload)
            handle.flush()
            os.fsync(handle.fileno())
        # There is no hostile-safe pathname CAS in this standard-library
        # protocol.  This immediate stable recheck is the declared local-host
        # precondition for the following atomic replacement.
        current = _read_runtime_identity_cas_state(
            path,
            approved_payload,
            name="checked-in runtime identity CAS precondition",
        )
        if current == approved_payload:
            return
        os.replace(os.fspath(pending), os.fspath(path))
        replaced = True
        _fsync_directory(path.parent)
    finally:
        if not replaced:
            try:
                pending.unlink()
            except FileNotFoundError:
                pass
            _fsync_directory(path.parent)
    committed = _read_runtime_identity_cas_state(
        path,
        approved_payload,
        name="approved runtime identity",
    )
    if committed != approved_payload:
        raise RuntimeError("approved runtime identity CAS did not commit exact bytes")


def _load_candidate_and_review(
    root: Path, candidate_sha256: str, report_sha256: str, placeholder: bytes
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    candidate_digest = _sha256(candidate_sha256, name="candidate digest")
    report_digest = _sha256(report_sha256, name="review digest")
    candidate_payload = _read_regular_file_stably(
        _workspace_path(root, _candidate_relative_path(candidate_digest)),
        runtime_identity.MAXIMUM_MANIFEST_BYTES,
        name="runtime identity candidate",
    )
    candidate = runtime_identity.parse_runtime_identity_manifest_bytes(
        candidate_payload
    )
    candidate = _candidate_record(candidate)
    if candidate["manifest_sha256"] != candidate_digest:
        raise ValueError("candidate content address differs")
    review_payload = _read_regular_file_stably(
        _workspace_path(
            root, _review_relative_path(candidate_digest, report_digest)
        ),
        MAXIMUM_REVIEW_BYTES,
        name="runtime identity review report",
    )
    review = parse_runtime_identity_review_bytes(
        review_payload,
        candidate=candidate,
        frozen_placeholder_payload=placeholder,
    )
    if review["report_sha256"] != report_digest:
        raise ValueError("review report content address differs")
    return candidate, review


def _verify_checked_in_runtime_identity_approval(
    root: Path,
) -> ApprovedRuntimeIdentityBundle:
    manifest_path = _workspace_path(
        root, runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH
    )
    manifest = runtime_identity.load_runtime_identity_manifest(
        manifest_path,
        lockfile_path=_workspace_path(root, runtime_identity.LOCKFILE_RELATIVE_PATH),
    )
    if manifest.approved is not True:
        raise PermissionError("checked-in runtime identity is not approved")
    approved_record = _plain(manifest.record)
    candidate = deepcopy(approved_record)
    candidate["approved"] = False
    candidate["manifest_sha256"] = (
        runtime_identity.runtime_identity_manifest_self_digest(candidate)
    )
    candidate = _candidate_record(candidate)
    approval_path = _workspace_path(root, APPROVAL_RECEIPT_RELATIVE_PATH)
    approval_payload = _read_regular_file_stably(
        approval_path,
        MAXIMUM_APPROVAL_RECEIPT_BYTES,
        name="runtime identity approval receipt",
    )
    approval_value = _parse_canonical_json(
        approval_payload,
        maximum=MAXIMUM_APPROVAL_RECEIPT_BYTES,
        name="runtime identity approval receipt",
    )
    receipt_keys = _exact_keys(
        approval_value, _APPROVAL_KEYS, name="runtime identity approval receipt"
    )
    report_binding = _exact_keys(
        receipt_keys["review_report"],
        {
            "relative_path",
            "schema",
            "report_sha256",
            "file_sha256",
            "size_bytes",
        },
        name="approval review binding",
    )
    report_digest = _sha256(
        report_binding["report_sha256"], name="approval review digest"
    )
    expected_report_path = _review_relative_path(
        candidate["manifest_sha256"], report_digest
    )
    if report_binding["relative_path"] != expected_report_path:
        raise ValueError("approval receipt review path is not content-addressed")
    baseline_path = _workspace_path(
        root, _baseline_archive_relative_path(FROZEN_PLACEHOLDER_FILE_SHA256)
    )
    baseline_payload = _read_regular_file_stably(
        baseline_path,
        runtime_identity.MAXIMUM_MANIFEST_BYTES,
        name="archived frozen runtime identity placeholder",
    )
    _frozen_placeholder_record(baseline_payload)
    candidate_payload = runtime_identity.canonical_runtime_identity_manifest_bytes(
        candidate
    )
    candidate_path = _workspace_path(
        root, _candidate_relative_path(candidate["manifest_sha256"])
    )
    if _read_regular_file_stably(
        candidate_path,
        runtime_identity.MAXIMUM_MANIFEST_BYTES,
        name="approved runtime identity candidate",
    ) != candidate_payload:
        raise ValueError("approved manifest does not reconstruct its candidate")
    report_payload = _read_regular_file_stably(
        _workspace_path(root, expected_report_path),
        MAXIMUM_REVIEW_BYTES,
        name="approved runtime identity review report",
    )
    report = parse_runtime_identity_review_bytes(
        report_payload,
        candidate=candidate,
        frozen_placeholder_payload=baseline_payload,
    )
    if (
        _sha256_bytes(report_payload) != report_binding["file_sha256"]
        or len(report_payload) != report_binding["size_bytes"]
        or report["report_sha256"] != report_digest
    ):
        raise ValueError("approval review report binding differs")
    receipt = validate_runtime_identity_approval_receipt(
        receipt_keys,
        candidate=candidate,
        review_report=report,
        frozen_placeholder_payload=baseline_payload,
    )
    if receipt["approval_protocol"] != _live_approval_protocol(root):
        raise ValueError("approval receipt source differs from live approval code")
    approved_payload = runtime_identity.canonical_runtime_identity_manifest_bytes(
        approved_record
    )
    if derive_approved_runtime_identity_manifest(candidate) != approved_record:
        raise ValueError("checked-in approved manifest is not the reviewed transition")
    verified = runtime_identity.verify_runtime_identity_files(manifest)
    reloaded = runtime_identity.load_runtime_identity_manifest(
        manifest_path,
        lockfile_path=_workspace_path(root, runtime_identity.LOCKFILE_RELATIVE_PATH),
    )
    if _plain(reloaded.record) != approved_record:
        raise RuntimeError("approved runtime identity or lock changed during verification")
    # Stable re-read all authority-bearing bytes after installed-file checks.
    if _read_regular_file_stably(
        manifest_path,
        runtime_identity.MAXIMUM_MANIFEST_BYTES,
        name="approved runtime identity final reread",
    ) != approved_payload or _read_regular_file_stably(
        approval_path,
        MAXIMUM_APPROVAL_RECEIPT_BYTES,
        name="approval receipt final reread",
    ) != approval_payload or _read_regular_file_stably(
        candidate_path,
        runtime_identity.MAXIMUM_MANIFEST_BYTES,
        name="runtime identity candidate final reread",
    ) != candidate_payload or _read_regular_file_stably(
        _workspace_path(root, expected_report_path),
        MAXIMUM_REVIEW_BYTES,
        name="runtime identity review final reread",
    ) != report_payload or _read_regular_file_stably(
        baseline_path,
        runtime_identity.MAXIMUM_MANIFEST_BYTES,
        name="runtime identity baseline final reread",
    ) != baseline_payload or _live_approval_protocol(root) != receipt[
        "approval_protocol"
    ]:
        raise RuntimeError("approved runtime identity bundle changed during verification")
    return ApprovedRuntimeIdentityBundle(
        manifest=verified,
        candidate=_deep_freeze(candidate),
        review_report=_deep_freeze(report),
        approval_receipt=_deep_freeze(receipt),
    )


def verify_checked_in_runtime_identity_approval() -> ApprovedRuntimeIdentityBundle:
    """Verify the fixed checked-in approved bundle and every installed byte."""

    return _verify_checked_in_runtime_identity_approval(_repository_root())


def _approve_interactively(
    root: Path,
    candidate_sha256: str,
    report_sha256: str,
    *,
    input_stream: TextIO,
    output_stream: TextIO,
    recapture_boundary: Any,
) -> ApprovedRuntimeIdentityBundle:
    approval_protocol_snapshot = _live_approval_protocol(root)
    placeholder_path = _workspace_path(
        root, runtime_identity.RUNTIME_IDENTITY_RELATIVE_PATH
    )
    baseline_path = _workspace_path(
        root, _baseline_archive_relative_path(FROZEN_PLACEHOLDER_FILE_SHA256)
    )
    placeholder = _read_regular_file_stably(
        baseline_path,
        runtime_identity.MAXIMUM_MANIFEST_BYTES,
        name="archived frozen runtime identity placeholder",
    )
    _frozen_placeholder_record(placeholder)
    candidate, report = _load_candidate_and_review(
        root, candidate_sha256, report_sha256, placeholder
    )
    if report["approval_ready"] is not True or report["blockers"] != []:
        raise PermissionError("runtime identity review report is not approval-ready")
    approved = derive_approved_runtime_identity_manifest(candidate)
    approved_payload = runtime_identity.canonical_runtime_identity_manifest_bytes(
        approved
    )
    current = _read_runtime_identity_cas_state(
        placeholder_path,
        approved_payload,
        name="checked-in runtime identity approval precondition",
    )
    if current == approved_payload:
        return _verify_checked_in_runtime_identity_approval(root)
    receipt_path = _workspace_path(root, APPROVAL_RECEIPT_RELATIVE_PATH)
    try:
        existing_receipt_payload = _read_regular_file_stably(
            receipt_path,
            MAXIMUM_APPROVAL_RECEIPT_BYTES,
            name="existing runtime identity approval receipt",
        )
    except FileNotFoundError:
        existing_receipt_payload = None
    if existing_receipt_payload is not None:
        existing_receipt = parse_runtime_identity_approval_bytes(
            existing_receipt_payload,
            candidate=candidate,
            review_report=report,
            frozen_placeholder_payload=placeholder,
        )
        if existing_receipt["approval_protocol"] != approval_protocol_snapshot:
            raise ValueError("orphan approval receipt source differs from live code")
        _compare_and_replace_frozen_placeholder(placeholder_path, approved_payload)
        return _verify_checked_in_runtime_identity_approval(root)
    _require_tty_streams(input_stream, output_stream)
    _display_review_summary(report, output_stream=output_stream)
    _read_confirmation(
        candidate["manifest_sha256"],
        report["report_sha256"],
        input_stream=input_stream,
        output_stream=output_stream,
    )
    result = recapture_boundary(root)
    if type(result) is not RuntimeIdentityRecapture:
        raise TypeError("fresh recapture boundary returned the wrong exact type")
    if _live_approval_protocol(root) != approval_protocol_snapshot:
        raise RuntimeError("approval source changed during operator review")
    receipt = build_runtime_identity_approval_receipt(
        candidate,
        report,
        frozen_placeholder_payload=placeholder,
        recapture=result,
        approval_protocol=approval_protocol_snapshot,
    )
    receipt_payload = _canonical_file_bytes(receipt)
    _publish_exclusive_bytes(
        receipt_path,
        receipt_payload,
        maximum=MAXIMUM_APPROVAL_RECEIPT_BYTES,
    )
    if _live_approval_protocol(root) != approval_protocol_snapshot:
        raise RuntimeError("approval source changed before manifest CAS")
    _compare_and_replace_frozen_placeholder(placeholder_path, approved_payload)
    return _verify_checked_in_runtime_identity_approval(root)


def approve_checked_in_runtime_identity_interactively(
    candidate_sha256: str, report_sha256: str
) -> ApprovedRuntimeIdentityBundle:
    """Perform the sole explicit interactive authority transition.

    There is intentionally no ``yes``, environment, callback, executable,
    output-path, or force parameter.
    """

    return _approve_interactively(
        _repository_root(),
        candidate_sha256,
        report_sha256,
        input_stream=sys.stdin,
        output_stream=sys.stdout,
        recapture_boundary=_recapture_after_confirmation,
    )


def _cli_summary(
    operation: str, bundle: ApprovedRuntimeIdentityBundle
) -> Dict[str, object]:
    if type(bundle) is not ApprovedRuntimeIdentityBundle:
        raise TypeError("approval CLI received the wrong bundle type")
    receipt = bundle.approval_receipt
    report = bundle.review_report
    body = {
        "schema": "heterodiff-a1-runtime-identity-approval-cli-result-v1",
        "operation": operation,
        "status": "VERIFIED",
        "candidate_manifest_sha256": bundle.candidate["manifest_sha256"],
        "review_report_sha256": report["report_sha256"],
        "approved_manifest_sha256": bundle.manifest.manifest_sha256,
        "approval_receipt_sha256": receipt["approval_receipt_sha256"],
        "procedural_only": True,
        "cryptographic_approval": False,
        "reviewer_independence_proven": False,
    }
    result = dict(body)
    result["summary_sha256"] = _sha256_json(body)
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the narrow operator CLI; no noninteractive approval flag exists."""

    import argparse

    parser = argparse.ArgumentParser(
        prog="finite-association-runtime-identity-approval",
        allow_abbrev=False,
    )
    commands = parser.add_subparsers(dest="command", required=True)
    approve_parser = commands.add_parser("approve", allow_abbrev=False)
    approve_parser.add_argument("--candidate-sha256", required=True)
    approve_parser.add_argument("--report-sha256", required=True)
    commands.add_parser("verify", allow_abbrev=False)
    arguments = parser.parse_args(argv)
    if arguments.command == "approve":
        bundle = approve_checked_in_runtime_identity_interactively(
            _sha256(arguments.candidate_sha256, name="candidate digest"),
            _sha256(arguments.report_sha256, name="review digest"),
        )
    elif arguments.command == "verify":
        bundle = verify_checked_in_runtime_identity_approval()
    else:  # pragma: no cover - argparse freezes the command set
        raise RuntimeError("approval CLI command is not frozen")
    sys.stdout.write(
        _canonical_file_bytes(_cli_summary(arguments.command, bundle)).decode(
            "ascii"
        )
    )
    sys.stdout.flush()
    return 0


def _canonical_cli_main(argv: Optional[Sequence[str]] = None) -> int:
    """Run a direct-file or ``-m`` invocation in the canonical type universe."""

    from heterodiff.experiments import (  # pylint: disable=import-outside-toplevel
        finite_association_runtime_identity_approval as canonical_approval,
    )

    canonical_file = getattr(canonical_approval, "__file__", None)
    if type(canonical_file) is not str:
        raise RuntimeError("canonical approval module has no exact source path")
    try:
        direct_source = Path(__file__).resolve(strict=True)
        canonical_source = Path(canonical_file).resolve(strict=True)
    except OSError as error:
        raise RuntimeError("approval CLI source path cannot be resolved") from error
    if canonical_source != direct_source:
        raise RuntimeError("canonical approval source path differs from CLI source")
    canonical_digest = getattr(
        canonical_approval, "_IMPORTED_APPROVAL_SOURCE_SHA256", None
    )
    live_digest = _sha256_bytes(
        _read_regular_file_stably(
            direct_source,
            MAXIMUM_REVIEW_BYTES,
            name="approval CLI source",
        )
    )
    if (
        type(canonical_digest) is not str
        or canonical_digest != _IMPORTED_APPROVAL_SOURCE_SHA256
        or live_digest != _IMPORTED_APPROVAL_SOURCE_SHA256
    ):
        raise RuntimeError("canonical approval source digest differs from CLI source")
    result = canonical_approval.main(argv)
    if type(result) is not int:
        raise TypeError("canonical approval CLI returned the wrong exact type")
    return result


def _repository_root() -> Path:
    return Path(__file__).resolve(strict=True).parents[3]


__all__ = [
    "APPROVAL_RECEIPT_RELATIVE_PATH",
    "APPROVAL_SCHEMA",
    "ApprovedRuntimeIdentityBundle",
    "BASELINE_ROOT_RELATIVE_PATH",
    "CANDIDATE_ROOT_RELATIVE_PATH",
    "CAPTURE_OPERATION",
    "FROZEN_PLACEHOLDER_FILE_SHA256",
    "FROZEN_PLACEHOLDER_MANIFEST_SHA256",
    "FROZEN_PLACEHOLDER_SIZE_BYTES",
    "MAXIMUM_APPROVAL_RECEIPT_BYTES",
    "MAXIMUM_REVIEW_BYTES",
    "PROCEDURAL_ACKNOWLEDGEMENT",
    "RECAPTURE_OPERATION",
    "REVIEW_SCHEMA",
    "RuntimeIdentityCaptureAssessment",
    "RuntimeIdentityRecapture",
    "TARGET_PROFILE_ID",
    "approve_checked_in_runtime_identity_interactively",
    "build_runtime_identity_approval_receipt",
    "build_runtime_identity_review_report",
    "canonical_runtime_identity_approval_bytes",
    "canonical_runtime_identity_review_bytes",
    "derive_approved_runtime_identity_manifest",
    "main",
    "parse_runtime_identity_approval_bytes",
    "parse_runtime_identity_review_bytes",
    "publish_runtime_identity_candidate_and_review",
    "validate_runtime_identity_approval_receipt",
    "validate_runtime_identity_review_report",
    "verify_checked_in_runtime_identity_approval",
]


_IMPORTED_APPROVAL_SOURCE_SHA256 = _sha256_bytes(
    _read_regular_file_stably(
        Path(__file__).resolve(strict=True),
        MAXIMUM_REVIEW_BYTES,
        name="imported runtime identity approval source",
    )
)


if __name__ == "__main__":  # pragma: no cover - exercised by operator invocation
    raise SystemExit(_canonical_cli_main())
