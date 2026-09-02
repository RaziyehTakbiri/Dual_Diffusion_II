"""Read-only custody and semantic validator for the three-record package."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Dict

from heterodiff.data import two_domain_precontact_definition_records as records

SCHEMA = "manuscript-v3-b02-b03-locally-decidable-definition-records-v1"
FIXTURE = Path(
    "research/fixtures/"
    "manuscript_v3_b02_b03_locally_decidable_definition_records_v1.json"
)
EXPECTED_BINDINGS = (
    ("PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION.md", 17235,
     "a7e882f209b26d9cf6dec449eb4fd93b78df0903be9294704ea857066dfe00ed",
     "sealed_activation_package_human"),
    ("PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION_INDEPENDENT_REVIEW.md", 10196,
     "a1baf2b04740ac38540a4008dcb09042f8c92fa978c51fe22ac54cb30c81f0d0",
     "sealed_activation_independent_review"),
    ("PROJECT_B02_B03_LOCALLY_DECIDABLE_DEFINITION_RECORDS.md", 2996,
     "29fc1c06ed81ac594ce24a23c2c8124d8bd1fef756d119d80a842b632682213a",
     "successor_human"),
    ("src/heterodiff/data/two_domain_precontact_definition_records.py", 12661,
     "eb4bd98f9190d2e9e7275e5a4f6f1c7fddfa34f8bf3435214b3060f4180d4e30",
     "pure_definition_source"),
)


class ValidationError(ValueError):
    pass


def _exact_dict(value: object, keys: tuple) -> Dict[str, Any]:
    if type(value) is not dict or tuple(value) != keys:
        raise ValidationError("closed-world mapping mismatch")
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
        value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
        value.st_size, value.st_mtime_ns, value.st_ctime_ns,
    )


def _read_stable(root: Path, relative: Path, expected_bytes: object) -> bytes:
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
        leaf = os.open(
            relative.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=current
        )
        opened.append(leaf)
        before = os.fstat(leaf)
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_IMODE(before.st_mode) != 0o644
            or before.st_nlink != 1
        ):
            raise ValidationError("binding is not a regular 0644 single-link file")
        limit = expected_bytes if expected_bytes is not None else 1_000_000
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


def _reject_duplicate_pairs(pairs: list) -> Dict[str, Any]:
    result = {}
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
        "schema_version", "package_kind", "state", "bindings",
        "definition_records", "active_split_contract_lineage",
        "blocked_non_f061_slots", "conflict_of_interest_determination_sha256",
        "owner_principals", "owner_acceptance_sha256s", "keys", "acl",
        "external_observations", "independent_review_receipt_sha256", "authority",
        "network_or_contact", "data_opened", "escrow_activated",
        "scientific_execution", "budgets", "closures", "tracker_edited",
    )
    _exact_dict(package, keys)
    if package["schema_version"] != SCHEMA:
        raise ValidationError("schema mismatch")
    if package["package_kind"] != "OFFLINE_DEFINITION_RECORDS_ONLY":
        raise ValidationError("package kind mismatch")
    if package["state"] != "THREE_OFFLINE_DEFINITIONS_FROZEN_OPERATIONAL_HOLD":
        raise ValidationError("state mismatch")
    if type(package["bindings"]) is not list or len(package["bindings"]) != 4:
        raise ValidationError("binding roster mismatch")
    for ordinal, binding in enumerate(package["bindings"]):
        _exact_dict(binding, ("ordinal", "path", "byte_count", "sha256", "role"))
        if type(binding["ordinal"]) is not int or binding["ordinal"] != ordinal:
            raise ValidationError("binding ordinal mismatch")
        expected_path, expected_count, expected_digest, expected_role = (
            EXPECTED_BINDINGS[ordinal]
        )
        if not _exact_equal(binding, {
            "ordinal": ordinal, "path": expected_path,
            "byte_count": expected_count, "sha256": expected_digest,
            "role": expected_role,
        }):
            raise ValidationError("binding semantic mismatch")
        expected = binding["sha256"]
        if type(expected) is not str or len(expected) != 64:
            raise ValidationError("binding digest invalid")
        data = _read_stable(root, _safe_path(binding["path"]), binding["byte_count"])
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValidationError("binding digest mismatch")
    actual = records.definition_records()
    expected_records = package["definition_records"]
    if type(expected_records) is not list or len(expected_records) != 3:
        raise ValidationError("definition roster mismatch")
    for ordinal, (name, _record, digest) in enumerate(actual):
        item = expected_records[ordinal]
        _exact_dict(item, ("ordinal", "name", "sha256"))
        if not _exact_equal(
            item, {"ordinal": ordinal, "name": name, "sha256": digest}
        ):
            raise ValidationError("definition record mismatch")
    state = records.unresolved_operational_state()
    for key in (
        "blocked_non_f061_slots", "conflict_of_interest_determination_sha256",
        "owner_principals", "owner_acceptance_sha256s", "keys", "acl",
        "external_observations", "independent_review_receipt_sha256", "authority",
        "network_or_contact", "data_opened", "escrow_activated",
        "scientific_execution", "budgets", "closures",
    ):
        if not _exact_equal(package[key], state[key]):
            raise ValidationError("unresolved state mismatch: " + key)
    if package["tracker_edited"] is not False:
        raise ValidationError("tracker edit claim invalid")
    lineage = package["active_split_contract_lineage"]
    expected_lineage = {
        "physionet": {"id": records.PHYSIONET_SPLIT_CONTRACT_ID,
                       "sha256": records.PHYSIONET_SPLIT_CONTRACT_SHA256},
        "retail": {"id": records.RETAIL_SPLIT_CONTRACT_ID,
                    "sha256": records.RETAIL_SPLIT_CONTRACT_SHA256},
    }
    if not _exact_equal(lineage, expected_lineage):
        raise ValidationError("active split lineage mismatch")
    return {"decision": "PASS_OFFLINE_DEFINITIONS_ONLY", "definition_count": 3,
            "operational_authority_present": False, "independent_review_present": False}


if __name__ == "__main__":
    project = Path(__file__).resolve().parents[2]
    print(json.dumps(validate(project), sort_keys=True, separators=(",", ":")))
