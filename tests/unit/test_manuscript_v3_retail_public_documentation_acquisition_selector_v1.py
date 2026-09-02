from __future__ import annotations

from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from heterodiff.data import retail_public_documentation_acquisition_selector as source
from heterodiff.data import two_domain_external_evidence_intake as intake


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = (
    "research/diagnostics/"
    "manuscript_v3_retail_public_documentation_acquisition_selector_v1.py"
)
MACHINE_REL = (
    "research/fixtures/"
    "manuscript_v3_retail_public_documentation_acquisition_selector_v1.json"
)


@pytest.fixture(scope="module")
def validator():
    spec = importlib.util.spec_from_file_location(
        "retail_public_documentation_selector_validator", ROOT / VALIDATOR_REL
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def acquisition_receipt() -> dict:
    return {
        "schema_version": "heterodiff-retail-raw-acquisition-receipt-v1",
        "selector_core_sha256": source.selector_core_sha256(),
        "registered_metadata_target": source.ACQUISITION_SELECTOR_CORE[
            "registered_metadata_target"
        ],
        "exact_archive_target": source.ACQUISITION_SELECTOR_CORE[
            "exact_archive_target"
        ],
        "archive_http_status": 200,
        "redirect_count": 0,
        "fallback_count": 0,
        "raw_archive_sha256": digest("future-raw-archive"),
        "raw_archive_byte_count": 45622418,
        "archive_member_name": "online_retail_II.xlsx",
        "archive_member_sha256": digest("future-workbook"),
        "archive_member_byte_count": 45622278,
        "archive_inventory_sha256": digest("future-inventory"),
        "response_headers_sha256": digest("future-headers"),
        "durable_intent_sha256": digest("future-intent"),
        "exact_data_authority_sha256": digest("future-authority"),
        "custodian_acceptance_sha256": digest("future-custodian"),
        "raw_hash_recomputed_from_private_bytes": True,
        "archive_inventory_recomputed_from_private_bytes": True,
        "independent_custody_verification": True,
        "dataset_opened_or_parsed": False,
    }


def complete_readiness() -> dict:
    result = {}
    for ordinal, row in enumerate(source.EXTERNAL_READINESS_CHECKLIST):
        obligation = row["obligation_id"]
        result[obligation] = {
            "obligation_id": obligation,
            "principal_role": row["principal_role"],
            "principal_id": f"EXTERNAL-PRINCIPAL-{ordinal:02d}",
            "evidence_sha256": digest(f"evidence-{ordinal}"),
            "acceptance_sha256": digest(f"acceptance-{ordinal}"),
            "externally_authenticated": True,
            "independently_verified": True,
        }
    return result


def copy_capsule(destination: Path, validator) -> Path:
    paths = [row[0] for row in validator.PACKAGE_FILES + validator.PREDECESSORS]
    paths.append(VALIDATOR_REL)
    for relative in paths:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
        target.chmod(0o644)
    return destination


def test_public_metadata_and_selector_are_exact() -> None:
    public = source.PUBLIC_DOCUMENTATION_RECORD
    selector = source.ACQUISITION_SELECTOR_CORE
    assert public["dataset_id"] == 502
    assert public["doi"] == "10.24432/C5CG6D"
    assert public["advertised_member_name"] == "online_retail_II.xlsx"
    assert public["advertised_member_byte_count"] == 45622278
    assert public["advertised_archive_byte_count"] == 45622418
    assert public["immutable_revision_exposed_by_public_page"] is False
    assert public["raw_archive_sha256_exposed_by_public_page"] is False
    assert selector["redirect_limit"] == selector["fallback_limit"] == 0
    assert selector["retry_limit"] == 0
    assert selector["attempt_budget_before_fresh_authority"] == 0
    assert selector["authentication_permitted"] is False
    assert selector["additional_archive_members_permitted"] is False


def test_selector_digest_is_domain_separated_and_stable() -> None:
    expected = hashlib.sha256(
        source.SELECTOR_CORE_DIGEST_DOMAIN
        + source.canonical_bytes(source.ACQUISITION_SELECTOR_CORE)
    ).hexdigest()
    assert source.selector_core_sha256() == expected
    assert expected == "ad48db3ec83d55e9da9f8d7e02c85b8e094d237e87b10f34f72d4575d4310244"


def test_owner_bound_selector_matches_accepted_intake_codec() -> None:
    owner = "ACCOUNTABLE-OWNER-001"
    payload = source.owner_bound_intake_selector(owner)
    expected = intake.content_sha256(
        "definition_record", {"payload": payload, "role": "RETAIL_SELECTOR_RECORD"}
    )
    assert source.owner_bound_intake_selector_sha256(owner) == expected
    principals = {"accountable_governance_owner_id": owner}
    intake._validate_selector_payload("RETAIL_SELECTOR_RECORD", payload, principals)


@pytest.mark.parametrize("owner", ["PENDING", "NONE", "x", "bad owner", 7, True])
def test_owner_bound_selector_rejects_placeholder_or_wrong_types(owner) -> None:
    with pytest.raises(source.RetailSelectorError):
        source.owner_bound_intake_selector(owner)


def test_content_addressed_version_rejects_noncanonical_hashes() -> None:
    value = digest("archive")
    assert source.derive_content_addressed_snapshot_version(value) == (
        "UCI-502-C5CG6D-ARCHIVE-SHA256-" + value
    )
    for invalid in ("0" * 63, "A" * 64, True, None):
        with pytest.raises(source.RetailSelectorError):
            source.derive_content_addressed_snapshot_version(invalid)


def test_future_acquisition_receipt_is_candidate_only() -> None:
    row = acquisition_receipt()
    result = source.validate_future_acquisition_receipt(row)
    assert result["snapshot_version"].endswith(row["raw_archive_sha256"])
    assert result["raw_snapshot_sha256"] == row["raw_archive_sha256"]
    assert result["raw_snapshot_byte_count"] == 45622418
    assert result["structural_decision"].startswith("CANDIDATE_F038_F039")
    assert result["authority_created"] is False
    assert result["field_closed"] is False


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("exact_archive_target", "https://example.invalid/mirror.zip"),
        ("archive_http_status", 302),
        ("redirect_count", 1),
        ("fallback_count", 1),
        ("raw_archive_byte_count", 45622417),
        ("archive_member_name", "renamed.xlsx"),
        ("archive_member_byte_count", 45622279),
        ("raw_hash_recomputed_from_private_bytes", False),
        ("archive_inventory_recomputed_from_private_bytes", False),
        ("independent_custody_verification", False),
        ("dataset_opened_or_parsed", True),
    ],
)
def test_acquisition_receipt_rejects_drift(field: str, replacement) -> None:
    row = acquisition_receipt()
    row[field] = replacement
    with pytest.raises(source.RetailSelectorError):
        source.validate_future_acquisition_receipt(row)


def test_acquisition_receipt_rejects_bool_as_int_extra_and_bad_hash() -> None:
    for field in ("archive_http_status", "redirect_count", "raw_archive_byte_count"):
        row = acquisition_receipt()
        row[field] = True
        with pytest.raises(source.RetailSelectorError):
            source.validate_future_acquisition_receipt(row)
    row = acquisition_receipt()
    row["extra"] = False
    with pytest.raises(source.RetailSelectorError):
        source.validate_future_acquisition_receipt(row)
    row = acquisition_receipt()
    row["raw_archive_sha256"] = "F" * 64
    with pytest.raises(source.RetailSelectorError):
        source.validate_future_acquisition_receipt(row)


def test_empty_readiness_holds_all_twelve_obligations() -> None:
    result = source.assess_external_readiness(source.empty_readiness_status())
    assert result["decision"] == "HOLD_REAL_RETAIL_EVIDENCE_INCOMPLETE"
    assert result["completed_count"] == 0
    assert len(result["remaining_obligation_ids"]) == 12
    assert result["field_closure_authorized"] is False
    assert result["blocker_closure_authorized"] is False


def test_partial_readiness_is_forbidden() -> None:
    row = source.empty_readiness_status()
    first = source.EXTERNAL_READINESS_CHECKLIST[0]
    row[first["obligation_id"]] = complete_readiness()[first["obligation_id"]]
    with pytest.raises(
        source.RetailSelectorError, match="PARTIAL_READINESS_POPULATION_FORBIDDEN"
    ):
        source.assess_external_readiness(row)


def test_complete_readiness_is_still_not_closure_authority() -> None:
    result = source.assess_external_readiness(complete_readiness())
    assert result["completed_count"] == 12
    assert result["remaining_obligation_ids"] == []
    assert "PRIVATE_CUSTODY_REPLAY" in result["decision"]
    assert result["field_closure_authorized"] is False
    assert result["blocker_closure_authorized"] is False


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("principal_role", "WRONG_ROLE"),
        ("principal_id", "PENDING"),
        ("evidence_sha256", "0" * 63),
        ("acceptance_sha256", "A" * 64),
        ("externally_authenticated", False),
        ("independently_verified", False),
    ],
)
def test_complete_readiness_rejects_hostile_receipts(field, replacement) -> None:
    row = complete_readiness()
    first = source.EXTERNAL_READINESS_CHECKLIST[0]["obligation_id"]
    row[first][field] = replacement
    with pytest.raises(source.RetailSelectorError):
        source.assess_external_readiness(row)


def test_machine_is_canonical_and_semantically_self_bound() -> None:
    raw = (ROOT / MACHINE_REL).read_bytes()
    value = json.loads(raw)
    assert raw == source.canonical_bytes(value) + b"\n"
    semantic = value.pop("semantic_sha256")
    assert semantic == hashlib.sha256(
        b"heterodiff/retail/public-documentation-selector-machine/v1\0"
        + source.canonical_bytes(value)
    ).hexdigest()


def test_standalone_validator_passes_in_root(validator) -> None:
    result = validator.validate(ROOT)
    assert result["decision"] == (
        "PASS_RETAIL_PUBLIC_DOCUMENTATION_SELECTOR_NO_FIELD_CLOSURE"
    )
    assert result["eligible_field_ids"] == []
    assert result["eligible_blocker_ids"] == []


def test_standalone_validator_passes_unrelated_physical_copy(
    tmp_path: Path, validator
) -> None:
    capsule = copy_capsule(tmp_path / "unrelated-capsule", validator)
    assert validator.validate(capsule)["readiness_obligation_count"] == 12
    completed = subprocess.run(
        [sys.executable, "-B", str(capsule / VALIDATOR_REL), str(capsule)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "PASS_RETAIL_PUBLIC_DOCUMENTATION_SELECTOR" in completed.stdout


def test_validator_rejects_intermediate_parent_symlink(
    tmp_path: Path, validator
) -> None:
    capsule = copy_capsule(tmp_path / "linked-parent", validator)
    shutil.rmtree(capsule / "src")
    os.symlink(ROOT / "src", capsule / "src")
    with pytest.raises(validator.ValidationError, match="PARENT_COMPONENT_OPEN_FAILED"):
        validator.validate(capsule)


def test_validator_rejects_leaf_symlink_hardlink_mode_and_tamper(
    tmp_path: Path, validator
) -> None:
    relative = validator.PACKAGE_FILES[1][0]

    capsule = copy_capsule(tmp_path / "leaf-link", validator)
    leaf = capsule / relative
    leaf.unlink()
    os.symlink(ROOT / relative, leaf)
    with pytest.raises(validator.ValidationError, match="LEAF_OPEN_FAILED"):
        validator.validate(capsule)

    capsule = copy_capsule(tmp_path / "hard-link", validator)
    leaf = capsule / relative
    sibling = leaf.with_name("linked.py")
    os.link(leaf, sibling)
    with pytest.raises(validator.ValidationError, match="LEAF_LINK_COUNT_NOT_ONE"):
        validator.validate(capsule)

    capsule = copy_capsule(tmp_path / "bad-mode", validator)
    (capsule / relative).chmod(0o600)
    with pytest.raises(validator.ValidationError, match="LEAF_MODE_NOT_0644"):
        validator.validate(capsule)

    capsule = copy_capsule(tmp_path / "tamper", validator)
    leaf = capsule / relative
    leaf.write_bytes(leaf.read_bytes() + b"# drift\n")
    with pytest.raises(validator.ValidationError, match="BYTE_COUNT_MISMATCH"):
        validator.validate(capsule)


def test_nonclaims_are_exactly_zero_delta() -> None:
    nonclaims = source.NONCLAIMS
    assert nonclaims["tracker_or_ledger_edited"] is False
    assert nonclaims["dataset_downloaded_opened_or_parsed"] is False
    assert nonclaims["retail_selector_intake_slot_closed"] is False
    for field in ("F038", "F039", "F041", "F053", "F054", "F059"):
        assert nonclaims[field + "_closed"] is False
    assert nonclaims["B03_closed"] is False
    assert nonclaims["B09_closed"] is False
    assert nonclaims["blockers_closed"] == 0
    assert nonclaims["formal_tests_closed"] == 0
    assert nonclaims["scientific_results_created"] == 0
