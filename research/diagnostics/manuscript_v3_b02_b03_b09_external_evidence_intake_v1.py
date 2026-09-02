"""Read-only custody and semantic validator for the external-evidence intake."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Tuple

from heterodiff.data import two_domain_external_evidence_intake as intake

FIXTURE = Path(
    "research/fixtures/"
    "manuscript_v3_b02_b03_b09_external_evidence_intake_v1.json"
)
EXPECTED_BINDINGS: Tuple[Tuple[str, int, str, str], ...] = (
    (
        "PROJECT_B02_B03_B09_EXTERNAL_EVIDENCE_INTAKE_PACKAGE.md", 8700,
        "08813c91b11e33f34bd6ff5a3e41197d029bd3d90fd18431c43182771e6b16ad",
        "candidate_human_contract",
    ),
    (
        "src/heterodiff/data/two_domain_external_evidence_intake.py", 68846,
        "ede0c1890d1e1f39a522a064fe94a78ab65fe5618687ca525c05b4cba7001d85",
        "pure_machine_contract_and_structural_validator",
    ),
    (
        "PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION.md", 17235,
        "a7e882f209b26d9cf6dec449eb4fd93b78df0903be9294704ea857066dfe00ed",
        "accepted_activation_human",
    ),
    (
        "PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION_INDEPENDENT_REVIEW.md", 10196,
        "a1baf2b04740ac38540a4008dcb09042f8c92fa978c51fe22ac54cb30c81f0d0",
        "accepted_activation_review",
    ),
    (
        "research/fixtures/manuscript_v3_b02_b03_offline_precontact_activation_v1.json", 22137,
        "d74333a2c381daa953803e9346efb0ab63d6744265bfa8e7e260b1d1932fc0ee",
        "accepted_activation_machine",
    ),
    (
        "PROJECT_B02_B03_LOCALLY_DECIDABLE_DEFINITION_RECORDS.md", 2996,
        "29fc1c06ed81ac594ce24a23c2c8124d8bd1fef756d119d80a842b632682213a",
        "accepted_local_definitions_human",
    ),
    (
        "research/fixtures/manuscript_v3_b02_b03_locally_decidable_definition_records_v1.json", 3032,
        "7b8ae7f454fd094cb1ce1b7b3b93fc50f72bf329cc550d9365c3df1779344e7f",
        "accepted_local_definitions_machine",
    ),
    (
        "PROJECT_B02_B03_LOCALLY_DECIDABLE_DEFINITION_RECORDS_INDEPENDENT_REVIEW.md", 4836,
        "4206aaf45508f2d5bf66d14fe8ebb4fa7b837ec287abf6fe221538f454d4a817",
        "accepted_local_definitions_review",
    ),
    (
        "PROJECT_F061_PRESERVATION_FIRST_ALLOCATION_PROPOSAL.md", 12695,
        "2769df9d8da86b054857973b7025c03f6932e88fa683848171dd32af507ec052",
        "accepted_f061_human",
    ),
    (
        "research/fixtures/manuscript_v3_f061_guarded_power_review_receipt_v1.json", 1924,
        "906b12b78400cba6bc2b32527a1410c6d42f154bbad0775591d69ada7485668d",
        "accepted_f061_review_receipt",
    ),
    (
        "PROJECT_F061_PRESERVATION_FIRST_ALLOCATION_INDEPENDENT_REVIEW.md", 6841,
        "053de959f3fffabf0da21a4c9e997b96e170f1fbc4b9295d71fef8e8347835eb",
        "accepted_f061_review",
    ),
    (
        "PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS.md", 15756,
        "e2ab4740c530460e0b6352e33cd7c129ea80e928a7a2da7a8be2f40ef668a19c",
        "accepted_governance_controls_human",
    ),
    (
        "research/fixtures/manuscript_v3_two_domain_governance_release_controls_v1.json", 17729,
        "340448f48d577b620d3bad62a21184e0cdde24408aff230cf467d45670afb33c",
        "accepted_governance_controls_machine",
    ),
    (
        "PROJECT_RETAIL_CUSTOMER_DISJOINT_TEMPORAL_SPLIT_DESIGN.md", 11226,
        "49a38fbe8bfdbc2fcb93de766f7280ba8affd18b2ebedbcc004d079550b752d1",
        "accepted_retail_split_design_human",
    ),
    (
        "research/fixtures/manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json", 13409,
        "b27086c5979d2f7018b4b8b50b3fffacf03b3fe2691d60567bc42b179d53e98b",
        "accepted_retail_split_design_machine",
    ),
    (
        "PROJECT_PHYSIONET_PATIENT_DISJOINT_SPLIT_DESIGN.md", 10761,
        "2d84753fe87032a81d377a469f858f1702b14474371bfd2d147fd87824bb4b7a",
        "accepted_physionet_split_design_human",
    ),
    (
        "research/fixtures/manuscript_v3_physionet_patient_disjoint_split_design_v1.json", 16543,
        "a9fc01ae42ba7942e6c61def5120d6497b74fc99c82b0c5b68188f221b4b68a8",
        "accepted_physionet_split_design_machine",
    ),
)


class ValidationError(ValueError):
    pass


def _reject_duplicate_pairs(pairs: list) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key")
        result[key] = value
    return result


def _exact_equal(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return tuple(actual) == tuple(expected) and all(
            _exact_equal(actual[key], expected[key]) for key in expected
        )
    if type(expected) is list:
        return len(actual) == len(expected) and all(
            _exact_equal(left, right) for left, right in zip(actual, expected)
        )
    return actual == expected


def _exact_dict(value: object, keys: tuple, label: str) -> Dict[str, Any]:
    if type(value) is not dict or tuple(value) != keys:
        raise ValidationError(label + " closed-world mapping mismatch")
    return value


def _safe_path(value: object) -> Path:
    if type(value) is not str:
        raise ValidationError("path must be exact string")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or str(pure) != value:
        raise ValidationError("unsafe or noncanonical path")
    return Path(*pure.parts)


def _identity(value: os.stat_result) -> tuple:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _read_stable(
    root: Path, relative: Path, expected_bytes: object, expected_mode: int = 0o644,
) -> bytes:
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise ValidationError("required no-follow descriptor flags unsupported")
    if type(expected_bytes) is not int and expected_bytes is not None:
        raise ValidationError("invalid expected byte count")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    root_fd = os.open(str(root), directory_flags)
    opened = [root_fd]
    try:
        root_before = os.fstat(root_fd)
        current = root_fd
        for part in relative.parts[:-1]:
            child = os.open(part, directory_flags, dir_fd=current)
            opened.append(child)
            current = child
        leaf = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=current)
        opened.append(leaf)
        before = os.fstat(leaf)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != expected_mode
            or before.st_nlink != 1
        ):
            raise ValidationError("binding is not a regular exact-mode single-link file")
        limit = expected_bytes if expected_bytes is not None else 100_000
        if type(limit) is not int or limit < 1 or before.st_size > limit:
            raise ValidationError("unsafe byte count")
        chunks = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(leaf, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if (
            _identity(before) != _identity(os.fstat(leaf))
            or _identity(root_before) != _identity(os.fstat(root_fd))
        ):
            raise ValidationError("unstable descriptor read")
        if expected_bytes is not None and len(data) != expected_bytes:
            raise ValidationError("byte count mismatch")
        return data
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)


def _expected_role_manifest() -> list:
    return [
        {
            "ordinal": ordinal,
            "role_id": role,
            "principal_field": principal,
            "acceptance_field": acceptance,
        }
        for ordinal, (role, principal, acceptance) in enumerate(intake.OWNER_ROLES)
    ]


def _expected_slot_manifest() -> list:
    return [
        {"ordinal": ordinal, "field": field, "exact_type": exact_type}
        for ordinal, (field, exact_type) in enumerate(
            intake.UNRESOLVED_DEFINITION_SLOTS
        )
    ]


def validate(root: Path, fixture_path: Path = FIXTURE) -> Dict[str, Any]:
    if not isinstance(root, Path) or not isinstance(fixture_path, Path):
        raise ValidationError("Path values required")
    if not root.is_absolute() or root.resolve(strict=True) != root:
        raise ValidationError("root must be a canonical absolute directory")
    if fixture_path != FIXTURE:
        raise ValidationError("fixture path must be the exact root-confined path")
    raw = _read_stable(root, fixture_path, None)
    try:
        package = json.loads(
            raw.decode("ascii"), object_pairs_hook=_reject_duplicate_pairs
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError("fixture is not ASCII JSON") from exc
    keys = (
        "schema_version",
        "package_kind",
        "state",
        "contract_record_sha256",
        "bindings",
        "resolved_local_definitions",
        "owner_role_manifest",
        "unresolved_definition_slot_manifest",
        "evidence_role_manifest",
        "empty_intake_instance",
        "closure_effect",
        "tracker_edited",
    )
    _exact_dict(package, keys, "package")
    if package["schema_version"] != intake.SCHEMA_VERSION:
        raise ValidationError("schema mismatch")
    if package["package_kind"] != "OFFLINE_EXTERNAL_EVIDENCE_INTAKE_CONTRACT_ONLY":
        raise ValidationError("package kind mismatch")
    if package["state"] != intake.CONTRACT_STATE:
        raise ValidationError("state mismatch")
    if package["contract_record_sha256"] != intake.intake_contract_sha256():
        raise ValidationError("contract digest mismatch")
    bindings = package["bindings"]
    if type(bindings) is not list or len(bindings) != len(EXPECTED_BINDINGS):
        raise ValidationError("binding roster mismatch")
    for ordinal, item in enumerate(bindings):
        _exact_dict(
            item, ("ordinal", "path", "byte_count", "sha256", "role"), "binding"
        )
        path, count, digest, role = EXPECTED_BINDINGS[ordinal]
        expected = {
            "ordinal": ordinal,
            "path": path,
            "byte_count": count,
            "sha256": digest,
            "role": role,
        }
        if not _exact_equal(item, expected):
            raise ValidationError("binding semantic mismatch")
        data = _read_stable(root, _safe_path(path), count)
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValidationError("binding digest mismatch")
    if not _exact_equal(
        package["resolved_local_definitions"], intake.RESOLVED_LOCAL_DEFINITIONS
    ):
        raise ValidationError("resolved definition mismatch")
    if not _exact_equal(package["owner_role_manifest"], _expected_role_manifest()):
        raise ValidationError("owner role manifest mismatch")
    if not _exact_equal(
        package["unresolved_definition_slot_manifest"], _expected_slot_manifest()
    ):
        raise ValidationError("definition slot manifest mismatch")
    if not _exact_equal(
        package["evidence_role_manifest"], list(intake.EVIDENCE_OBJECT_ROLES)
    ):
        raise ValidationError("evidence role manifest mismatch")
    if not _exact_equal(package["empty_intake_instance"], intake.empty_intake_instance()):
        raise ValidationError("empty intake instance mismatch")
    outcome = intake.validate_population(package["empty_intake_instance"])
    if outcome["decision"] != intake.EMPTY_DECISION:
        raise ValidationError("empty intake decision mismatch")
    expected_closure = {
        "project_control_item_after_independent_acceptance": (
            "B02_B03_B09_EXTERNAL_EVIDENCE_INTAKE_CONTRACT_"
            "IMPLEMENTED_AND_QUALIFIED"
        ),
        "field_count_delta": 0,
        "blocker_count_delta": 0,
        "operational_task_count_delta": 0,
        "formal_test_count_delta": 0,
        "scientific_result_count_delta": 0,
        "b02_closed": False,
        "b03_closed": False,
        "b09_closed": False,
    }
    if not _exact_equal(package["closure_effect"], expected_closure):
        raise ValidationError("closure boundary mismatch")
    if package["tracker_edited"] is not False:
        raise ValidationError("tracker edit claim invalid")
    return {
        "decision": "PASS_OFFLINE_EXTERNAL_EVIDENCE_INTAKE_CONTRACT_ONLY",
        "owner_role_count": 9,
        "unresolved_definition_slot_count": 9,
        "evidence_role_count": len(intake.EVIDENCE_OBJECT_ROLES),
        "authority_present": False,
        "blocker_delta": 0,
    }


def validate_populated_from_private_custody(
    root: Path, populated_instance: object,
) -> Dict[str, Any]:
    """Load all future private evidence by descriptor and replay it semantically."""

    if not isinstance(root, Path) or not root.is_absolute():
        raise ValidationError("canonical absolute root required")
    if root.resolve(strict=True) != root:
        raise ValidationError("canonical absolute root required")
    if type(populated_instance) is not dict:
        raise ValidationError("exact populated mapping required")
    manifest = populated_instance.get("evidence_manifest")
    if type(manifest) is not list or len(manifest) != len(
        intake.EVIDENCE_OBJECT_ROLES
    ):
        raise ValidationError("private evidence manifest mismatch")
    bundle: Dict[str, bytes] = {}
    for ordinal, role in enumerate(intake.EVIDENCE_OBJECT_ROLES):
        item = manifest[ordinal]
        if type(item) is not dict or item.get("role") != role:
            raise ValidationError("private evidence role mismatch")
        relative = _safe_path(item.get("private_path"))
        raw = _read_stable(root, relative, item.get("byte_count"), 0o600)
        if hashlib.sha256(raw).hexdigest() != item.get("raw_sha256"):
            raise ValidationError("private evidence digest mismatch")
        bundle[role] = raw
    return intake.validate_population(populated_instance, bundle)


if __name__ == "__main__":
    project = Path(__file__).resolve().parents[2]
    print(json.dumps(validate(project), sort_keys=True, separators=(",", ":")))
