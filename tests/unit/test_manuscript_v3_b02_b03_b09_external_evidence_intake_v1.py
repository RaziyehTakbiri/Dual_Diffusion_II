"""Qualification and hostile tests for the external-evidence intake contract."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from heterodiff.data import two_domain_external_evidence_intake as intake

ROOT = Path(__file__).resolve().parents[2]
DIAGNOSTIC = ROOT / (
    "research/diagnostics/"
    "manuscript_v3_b02_b03_b09_external_evidence_intake_v1.py"
)
SPEC = importlib.util.spec_from_file_location("external_intake_validator", DIAGNOSTIC)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def test_contract_has_exact_roles_slots_and_resolved_lineage() -> None:
    contract = intake.contract_record()
    assert len(contract["owner_roles"]) == 9
    assert len({item["role_id"] for item in contract["owner_roles"]}) == 9
    assert len({item["principal_field"] for item in contract["owner_roles"]}) == 9
    assert len({item["acceptance_field"] for item in contract["owner_roles"]}) == 9
    assert len(contract["definition_slots"]) == 9
    assert contract["resolved_local_definitions"] == intake.RESOLVED_LOCAL_DEFINITIONS
    contact = contract["definition_record_requirements"]["contact_target_roster"]
    assert contact["exact_target_count"] == 2
    assert contact["additional_or_fallback_targets_permitted"] is False
    coi = contract["definition_record_requirements"][
        "conflict_of_interest_determination"
    ]
    assert coi["determination"] == (
        "NO_PROHIBITED_ROLE_ALIAS_AND_NO_IDENTIFIED_CONFLICT_V1"
    )
    assert coi["managed_or_unmanaged_conflict_permitted_in_v1"] is False
    assert all(
        len(value) == 64 for value in intake.RESOLVED_LOCAL_DEFINITIONS.values()
    )


def test_contract_digest_is_domain_separated_and_deterministic() -> None:
    assert len(intake.intake_contract_sha256()) == 64
    record = {
        "schema_version": "heterodiff-principal-role-acceptance-v1",
        "acceptance": True,
    }
    first = intake.content_sha256("principal_acceptance", record)
    assert first == intake.content_sha256("principal_acceptance", record)
    assert first != intake.content_sha256("definition_record", record)
    with pytest.raises(intake.IntakeValidationError):
        intake.content_sha256("unknown", record)
    with pytest.raises(intake.IntakeValidationError):
        intake.content_sha256("definition_record", [])


def test_empty_template_is_hold_and_contains_no_claim() -> None:
    value = intake.empty_intake_instance()
    assert intake.validate_population(value) == {
        "decision": intake.EMPTY_DECISION,
        "owner_principals_present": 0,
        "definition_slots_present": 0,
        "evidence_objects_present": 0,
        "authority_present": False,
    }
    assert all(item is None for item in value["principals"].values())
    assert all(item is None for item in value["acceptance_receipts"].values())
    assert all(item is None for item in value["definition_bindings"].values())
    assert all(item is False for item in value["authority"].values())
    assert all(type(item) is int and item == 0 for item in value["attempt_budgets"].values())


def test_synthetic_complete_branch_is_review_only_not_authority() -> None:
    instance, evidence = intake.synthetic_complete_bundle()
    result = intake.validate_population(instance, evidence)
    assert result == {
        "decision": intake.COMPLETE_DECISION,
        "owner_principals_present": 9,
        "definition_slots_present": 9,
        "evidence_objects_present": 18,
        "authority_present": False,
    }


@pytest.mark.parametrize("surface", ["principal", "acceptance", "definition"])
def test_partial_population_rejected(surface: str) -> None:
    value = intake.empty_intake_instance()
    if surface == "principal":
        value["principals"][next(iter(value["principals"]))] = "SYNTHETIC-ONE"
    elif surface == "acceptance":
        value["acceptance_receipts"][next(iter(value["acceptance_receipts"]))] = "1" * 64
    else:
        value["definition_bindings"][next(iter(value["definition_bindings"]))] = "2" * 64
    with pytest.raises(intake.IntakeValidationError, match="PARTIAL"):
        intake.validate_population(value)


def test_principal_role_alias_and_personal_identifier_rejected() -> None:
    value, evidence = intake.synthetic_complete_bundle()
    fields = list(value["principals"])
    value["principals"][fields[1]] = value["principals"][fields[0]]
    with pytest.raises(intake.IntakeValidationError, match="ALIAS"):
        intake.validate_population(value, evidence)
    value, evidence = intake.synthetic_complete_bundle()
    value["principals"][fields[0]] = "person@example.org"
    with pytest.raises(intake.IntakeValidationError):
        intake.validate_population(value, evidence)


@pytest.mark.parametrize(
    ("field", "value"),
    [("contact_target_count", True), ("contact_target_count", 1),
     ("contact_target_count", 3),
     ("contact_roster_complete", 1), ("contact_roster_complete", False)],
)
def test_exact_count_and_completeness_types_enforced(field: str, value) -> None:
    packet, evidence = intake.synthetic_complete_bundle()
    packet["definition_bindings"][field] = value
    with pytest.raises(intake.IntakeValidationError):
        intake.validate_population(packet, evidence)


@pytest.mark.parametrize("field", [
    "network_or_contact", "authentication", "download_or_data_access",
    "snapshot_open", "split_execution", "escrow_activation", "final_opening",
    "scientific_execution", "publication_or_submission",
])
def test_any_authority_expansion_rejected(field: str) -> None:
    value, evidence = intake.synthetic_complete_bundle()
    value["authority"][field] = True
    with pytest.raises(intake.IntakeValidationError, match="AUTHORITY"):
        intake.validate_population(value, evidence)


@pytest.mark.parametrize("value", [1, True, -1])
def test_any_nonexact_zero_budget_rejected(value) -> None:
    packet, evidence = intake.synthetic_complete_bundle()
    packet["attempt_budgets"]["admin_contact"] = value
    with pytest.raises(intake.IntakeValidationError, match="BUDGET"):
        intake.validate_population(packet, evidence)


@pytest.mark.parametrize("mutation", [
    "missing_item", "role_order", "unsafe_path", "zero_bytes",
    "unverified", "bad_verification_digest",
])
def test_evidence_manifest_hostile_mutations_rejected(mutation: str) -> None:
    value, evidence = intake.synthetic_complete_bundle()
    if mutation == "missing_item":
        value["evidence_manifest"].pop()
    elif mutation == "role_order":
        value["evidence_manifest"][0]["role"] = value["evidence_manifest"][1]["role"]
    elif mutation == "unsafe_path":
        value["evidence_manifest"][0]["private_path"] = "../secret"
    elif mutation == "zero_bytes":
        value["evidence_manifest"][0]["byte_count"] = 0
    elif mutation == "unverified":
        value["evidence_manifest"][0]["external_authentication_verified"] = False
    else:
        value["evidence_manifest"][0]["verification_receipt_sha256"] = "BAD"
    with pytest.raises(intake.IntakeValidationError):
        intake.validate_population(value, evidence)


def test_self_review_tracker_and_blocker_claims_rejected() -> None:
    value, evidence = intake.synthetic_complete_bundle()
    value["external_independent_review_receipt_sha256"] = "3" * 64
    with pytest.raises(intake.IntakeValidationError, match="SELF_INGESTED"):
        intake.validate_population(value, evidence)
    value, evidence = intake.synthetic_complete_bundle()
    value["tracker_or_ledger_edited"] = True
    with pytest.raises(intake.IntakeValidationError, match="TRACKER"):
        intake.validate_population(value, evidence)
    value, evidence = intake.synthetic_complete_bundle()
    value["blockers_closed"] = ["B02"]
    with pytest.raises(intake.IntakeValidationError, match="BLOCKER"):
        intake.validate_population(value, evidence)


def test_closed_world_instance_and_nested_maps() -> None:
    value, evidence = intake.synthetic_complete_bundle()
    value["foreign"] = None
    with pytest.raises(intake.IntakeValidationError, match="CLOSED_WORLD"):
        intake.validate_population(value, evidence)


def test_raw_evidence_required_and_opaque_zero_laundering_rejected() -> None:
    value, evidence = intake.synthetic_complete_bundle()
    with pytest.raises(intake.IntakeValidationError, match="RAW_EVIDENCE"):
        intake.validate_population(value)
    for field in value["acceptance_receipts"]:
        value["acceptance_receipts"][field] = "0" * 64
    for field, exact_type in intake.UNRESOLVED_DEFINITION_SLOTS:
        if exact_type == "LOWERCASE_SHA256":
            value["definition_bindings"][field] = "0" * 64
    for item in value["evidence_manifest"]:
        item["raw_sha256"] = "0" * 64
        item["verification_receipt_sha256"] = "0" * 64
    with pytest.raises(intake.IntakeValidationError):
        intake.validate_population(value, evidence)


def test_fixed_identity_equality_lie_rejected() -> None:
    class Lie(str):
        def __eq__(self, _other):
            return True

        def __ne__(self, _other):
            return False

    value, evidence = intake.synthetic_complete_bundle()
    value["schema_version"] = Lie("FOREIGN_SCHEMA")
    with pytest.raises(intake.IntakeValidationError, match="EXACT_TYPE"):
        intake.validate_population(value, evidence)
    value, evidence = intake.synthetic_complete_bundle()
    value["intake_contract_sha256"] = Lie("FOREIGN_DIGEST")
    with pytest.raises(intake.IntakeValidationError, match="EXACT_TYPE"):
        intake.validate_population(value, evidence)


def test_raw_object_semantics_duplicate_keys_and_crosslinks_replayed() -> None:
    value, evidence = intake.synthetic_complete_bundle()
    evidence = dict(evidence)
    evidence["PHYSIONET_SELECTOR_RECORD"] = b"{}\n"
    with pytest.raises(intake.IntakeValidationError):
        intake.validate_population(value, evidence)
    value, evidence = intake.synthetic_complete_bundle()
    evidence = dict(evidence)
    role = "ACCOUNTABLE_GOVERNANCE_OWNER_ACCEPTANCE"
    raw = evidence[role]
    duplicate = raw.replace(b'{"authentication":', b'{"role":"FOREIGN","authentication":', 1)
    evidence[role] = duplicate
    with pytest.raises(intake.IntakeValidationError, match="DUPLICATE"):
        intake.validate_population(value, evidence)
    value, evidence = intake.synthetic_complete_bundle()
    evidence = dict(evidence)
    record = json.loads(evidence[role].decode("ascii"))
    record["payload"]["principal_id"] = "SYNTHETIC-PRINCIPAL-01"
    changed = intake.evidence_object_bytes(
        role, record["payload"], record["authentication"]
    )
    evidence[role] = changed
    manifest_item = value["evidence_manifest"][
        intake.EVIDENCE_OBJECT_ROLES.index(role)
    ]
    manifest_item["byte_count"] = len(changed)
    import hashlib
    manifest_item["raw_sha256"] = hashlib.sha256(changed).hexdigest()
    manifest_item["verification_receipt_sha256"] = json.loads(
        changed.decode("ascii")
    )["verification_receipt_sha256"]
    with pytest.raises(intake.IntakeValidationError, match="principal_id"):
        intake.validate_population(value, evidence)


def test_semantic_gregorian_timestamp_validation_and_crosslink() -> None:
    for timestamp in (
        "2026-02-29T00:00:00.000000000Z",
        "2026-02-31T00:00:00.000000000Z",
        "2026-04-31T00:00:00.000000000Z",
        "1900-02-29T00:00:00.000000000Z",
    ):
        with pytest.raises(intake.IntakeValidationError, match="GREGORIAN"):
            intake._require_rfc3339_utc(timestamp, "hostile")
    assert intake._require_rfc3339_utc(
        "2000-02-29T23:59:59.999999999Z", "leap"
    ) == "2000-02-29T23:59:59.999999999Z"

    class Lie(str):
        pass

    with pytest.raises(intake.IntakeValidationError, match="RFC3339"):
        intake._require_rfc3339_utc(
            Lie("2000-02-29T23:59:59.999999999Z"), "subclass"
        )

    value, evidence = intake.synthetic_complete_bundle()
    evidence = dict(evidence)
    role = "ACCOUNTABLE_GOVERNANCE_OWNER_ACCEPTANCE"
    record = json.loads(evidence[role].decode("ascii"))
    record["payload"]["issued_time_rfc3339_utc"] = (
        "2026-02-31T00:00:00.000000000Z"
    )
    changed = intake.evidence_object_bytes(
        role, record["payload"], record["authentication"]
    )
    evidence[role] = changed
    item = value["evidence_manifest"][intake.EVIDENCE_OBJECT_ROLES.index(role)]
    import hashlib
    item["byte_count"] = len(changed)
    item["raw_sha256"] = hashlib.sha256(changed).hexdigest()
    item["verification_receipt_sha256"] = json.loads(changed.decode("ascii"))[
        "verification_receipt_sha256"
    ]
    value["acceptance_receipts"][
        "accountable_governance_owner_acceptance_sha256"
    ] = intake.content_sha256("principal_acceptance", record["payload"])
    with pytest.raises(intake.IntakeValidationError, match="GREGORIAN"):
        intake.validate_population(value, evidence)


def test_private_custody_loader_replays_exact_0600_files(tmp_path: Path) -> None:
    value, evidence = intake.synthetic_complete_bundle()
    for item in value["evidence_manifest"]:
        target = tmp_path / item["private_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(evidence[item["role"]])
        target.chmod(0o600)
    result = validator.validate_populated_from_private_custody(
        tmp_path.resolve(), value
    )
    assert result["decision"] == intake.COMPLETE_DECISION
    first = tmp_path / value["evidence_manifest"][0]["private_path"]
    first.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="exact-mode"):
        validator.validate_populated_from_private_custody(tmp_path.resolve(), value)
    value, evidence = intake.synthetic_complete_bundle()
    value["principals"]["foreign"] = None
    with pytest.raises(intake.IntakeValidationError, match="CLOSED_WORLD"):
        intake.validate_population(value, evidence)


def test_read_only_validator_passes_exact_package() -> None:
    assert validator.validate(ROOT) == {
        "decision": "PASS_OFFLINE_EXTERNAL_EVIDENCE_INTAKE_CONTRACT_ONLY",
        "owner_role_count": 9,
        "unresolved_definition_slot_count": 9,
        "evidence_role_count": 18,
        "authority_present": False,
        "blocker_delta": 0,
    }


def _copy_package(tmp_path: Path) -> Path:
    fixture = json.loads((ROOT / validator.FIXTURE).read_text(encoding="ascii"))
    paths = [validator.FIXTURE] + [Path(item["path"]) for item in fixture["bindings"]]
    for relative in paths:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
        target.chmod(0o644)
    return tmp_path / validator.FIXTURE


@pytest.mark.parametrize("surface", [
    "state", "contract_digest", "role", "slot", "empty_instance", "closure",
])
def test_hostile_machine_fixture_mutation_rejected(tmp_path: Path, surface: str) -> None:
    fixture_path = _copy_package(tmp_path)
    value = json.loads(fixture_path.read_text(encoding="ascii"))
    if surface == "state":
        value["state"] = "OPERATIONAL"
    elif surface == "contract_digest":
        value["contract_record_sha256"] = "0" * 64
    elif surface == "role":
        value["owner_role_manifest"][0]["role_id"] = "FOREIGN"
    elif surface == "slot":
        value["unresolved_definition_slot_manifest"][0]["exact_type"] = "ANY"
    elif surface == "empty_instance":
        value["empty_intake_instance"]["authority"]["network_or_contact"] = True
    else:
        value["closure_effect"]["blocker_count_delta"] = 1
    fixture_path.write_text(json.dumps(value), encoding="ascii")
    fixture_path.chmod(0o644)
    with pytest.raises((validator.ValidationError, intake.IntakeValidationError)):
        validator.validate(tmp_path)


def test_duplicate_json_key_rejected(tmp_path: Path) -> None:
    fixture_path = _copy_package(tmp_path)
    raw = fixture_path.read_text(encoding="ascii")
    duplicate = raw.replace(
        '{\n  "schema_version":',
        '{\n  "tracker_edited": false,\n  "schema_version":',
        1,
    )
    fixture_path.write_text(duplicate, encoding="ascii")
    fixture_path.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="duplicate JSON key"):
        validator.validate(tmp_path)


def test_binding_path_digest_and_custody_rejected(tmp_path: Path) -> None:
    fixture_path = _copy_package(tmp_path)
    value = json.loads(fixture_path.read_text(encoding="ascii"))
    value["bindings"][0]["path"] = "../outside"
    fixture_path.write_text(json.dumps(value), encoding="ascii")
    fixture_path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(tmp_path)
    _copy_package(tmp_path)
    bound = tmp_path / validator.EXPECTED_BINDINGS[0][0]
    bound.chmod(0o600)
    with pytest.raises(validator.ValidationError, match="exact-mode"):
        validator.validate(tmp_path)


def test_absolute_or_alternate_fixture_path_rejected() -> None:
    with pytest.raises(validator.ValidationError, match="fixture path"):
        validator.validate(ROOT, ROOT / validator.FIXTURE)


def test_pure_contract_has_no_contact_or_execution_imports() -> None:
    text = (
        ROOT / "src/heterodiff/data/two_domain_external_evidence_intake.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "import os", "socket", "subprocess", "requests", "urllib", "httpx",
        "boto", "paramiko",
    ):
        assert forbidden not in text
