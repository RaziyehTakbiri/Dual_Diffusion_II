from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for import_root in (ROOT, SRC):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from heterodiff.data import two_domain_offline_precontact_activation as core
from heterodiff.data import online_retail_ii_admission_preflight as retail
from heterodiff.data import physionet_2012_admission_preflight as physionet
from research.diagnostics.manuscript_v3_b02_b03_offline_precontact_activation_v1 import (
    EXPECTED_RECORD_SHA256,
    EXTERNAL_REVIEW_NULL_SLOTS,
    F061_POLICY_NULL_SLOTS,
    FROZEN_PATHS,
    MACHINE_PATH,
    OTHER_DEFINITION_NULL_SLOTS,
    OWNER_MANIFEST_KEYS,
    OWNER_ROLES,
    PACKAGE_PATHS,
    PREDICATE,
    STATE,
    ValidationError,
    _relative_parts,
    _semantic_sha256,
    _validate_binding_roster,
    _validate_semantics,
    validate_package,
)


def _machine_record() -> dict:
    return json.loads((ROOT / MACHINE_PATH).read_text(encoding="utf-8"))


def _copy_validation_tree(tmp_path: Path) -> Path:
    record = _machine_record()
    paths = [MACHINE_PATH]
    paths.extend(binding["path"] for binding in record["package_bindings"])
    paths.extend(binding["path"] for binding in record["frozen_inputs"])
    for relative in paths:
        source = ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        destination.chmod(0o644)
    return tmp_path


def _write_machine(root: Path, record: dict) -> None:
    path = root / MACHINE_PATH
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o644)


def test_read_only_validator_passes_current_package() -> None:
    assert validate_package() == {
        "state": STATE,
        "record_sha256": EXPECTED_RECORD_SHA256,
        "package_binding_count": 7,
        "frozen_input_count": 16,
        "completed_enabling_timetable_item": PREDICATE,
        "field_count_delta": 0,
        "blocker_count_delta": 0,
        "operational_task_count_delta": 0,
    }


def test_machine_semantic_digest_is_exact() -> None:
    record = _machine_record()
    assert record["record_sha256"] == EXPECTED_RECORD_SHA256
    assert _semantic_sha256(record) == EXPECTED_RECORD_SHA256


def test_every_bound_file_matches_current_bytes() -> None:
    record = _machine_record()
    assert tuple(item["path"] for item in record["package_bindings"]) == PACKAGE_PATHS
    assert tuple(item["path"] for item in record["frozen_inputs"]) == FROZEN_PATHS
    for section in ("package_bindings", "frozen_inputs"):
        for binding in record[section]:
            raw = (ROOT / binding["path"]).read_bytes()
            assert len(raw) == binding["bytes"]
            assert hashlib.sha256(raw).hexdigest() == binding["raw_sha256"]


def test_machine_keeps_all_external_and_owner_slots_null() -> None:
    record = _machine_record()
    machine_owners = record["unresolved_owner_manifest"]
    assert tuple(machine_owners) == OWNER_MANIFEST_KEYS
    core_owners = core.unresolved_owner_manifest()
    core_fields = {
        "accountable_governance_owner": (
            "accountable_governance_owner_id",
            "accountable_governance_owner_acceptance_sha256",
        ),
        "license_privacy_or_institutional_approval_endpoint": (
            "license_privacy_institutional_approval_endpoint_id",
            "license_privacy_institutional_approval_endpoint_acceptance_sha256",
        ),
        "raw_snapshot_custodian": (
            "raw_snapshot_custodian_id",
            "raw_snapshot_custodian_acceptance_sha256",
        ),
        "deterministic_split_operator": (
            "deterministic_split_operator_id",
            "deterministic_split_operator_acceptance_sha256",
        ),
        "independent_heldout_escrow_custodian": (
            "independent_held_out_escrow_custodian_id",
            "independent_held_out_escrow_custodian_acceptance_sha256",
        ),
        "final_opening_approver": (
            "independent_final_opening_approver_id",
            "independent_final_opening_approver_acceptance_sha256",
        ),
        "key_and_acl_acceptance_authority": (
            "key_acl_acceptance_authority_id",
            "key_acl_acceptance_authority_acceptance_sha256",
        ),
        "retention_and_deletion_owner": (
            "retention_deletion_owner_id",
            "retention_deletion_owner_acceptance_sha256",
        ),
        "incident_response_owner": (
            "incident_response_owner_id",
            "incident_response_owner_acceptance_sha256",
        ),
    }
    assert tuple(core_fields) == OWNER_ROLES
    for role, (principal_field, acceptance_field) in core_fields.items():
        assert machine_owners[role] == {
            "principal_id": getattr(core_owners, principal_field),
            "acceptance_sha256": getattr(core_owners, acceptance_field),
        }
    assert machine_owners["conflict_of_interest_determination_sha256"] is None
    assert (
        core.unresolved_definition_bindings().conflict_of_interest_determination_sha256
        is None
    )
    assert all(value is None for value in record["future_observations"].values())
    definitions = core.unresolved_definition_bindings()
    assert tuple(record["other_unresolved_definition_slots"]) == (
        OTHER_DEFINITION_NULL_SLOTS
    )
    for field in OTHER_DEFINITION_NULL_SLOTS:
        assert record["other_unresolved_definition_slots"][field] is None
        assert getattr(definitions, field) is None
    package = core.build_offline_precontact_activation("1" * 64)
    assert tuple(record["external_review_slots"]) == EXTERNAL_REVIEW_NULL_SLOTS
    for field in EXTERNAL_REVIEW_NULL_SLOTS:
        assert record["external_review_slots"][field] is None
        assert getattr(package, field) is None
    assert record["future_observations"]["access_log_head_sha256"] is None
    assert package.access_log_head_sha256 is None


def test_machine_keeps_all_operations_inert_and_original_tasks_open() -> None:
    record = _machine_record()
    assert record["execution_boundary"] == asdict(core.ZERO_EXECUTION_BOUNDARY)
    assert record["activation_contract"]["shared_core_schema_version"] == (
        core.SCHEMA_VERSION
    )
    assert [row["ordinal"] for row in record["operation_roster"]] == [0, 1, 2, 3]
    for row in record["operation_roster"]:
        assert row["maximum_attempt_count"] == 1
        assert row["retry_limit"] == 0
        assert row["redirect_limit"] == 0
        assert row["fallback_limit"] == 0
        assert row["current_execution_budget"] == 0
        assert row["authentication_permitted"] is False
        assert row["download_permitted"] is False
        assert row["data_opening_permitted"] is False
        assert row["protected_data_permitted"] is False
    assert len(record["operation_roster"][0]["administrative_questions"]) == 7
    assert (
        record["operation_roster"][0]["administrative_questions"]
        == record["operation_roster"][1]["administrative_questions"]
    )
    assert record["operation_roster"][2]["administrative_questions"] == []
    assert record["operation_roster"][3]["administrative_questions"] == []
    closure = record["closure_effect"]
    assert closure["completed_enabling_timetable_item"] == PREDICATE
    assert closure["b02_closed"] is False
    assert closure["b03_closed"] is False
    assert closure["seven_operational_tasks_closed_count"] == 0


def test_machine_preserves_two_stage_f061_policy_boundary() -> None:
    boundary = _machine_record()["shared_f061_policy_boundary"]
    assert boundary["schema_version"] == core.F061_ALLOCATION_SCHEMA
    assert boundary["allowed_method_id"] == core.F061_ALLOWED_METHOD_ID
    assert boundary["retail_adapter_id"] == core.RETAIL_F061_ADAPTER_ID
    assert boundary["retail_adapter_sha256"] == core.RETAIL_F061_ADAPTER_SHA256
    assert core.retail_f061_adapter_sha256() == core.RETAIL_F061_ADAPTER_SHA256
    assert boundary["physionet_adapter_id"] == core.PHYSIONET_F061_ADAPTER_ID
    assert (
        boundary["physionet_adapter_sha256"]
        == core.PHYSIONET_F061_ADAPTER_SHA256
    )
    assert (
        core.physionet_f061_adapter_sha256()
        == core.PHYSIONET_F061_ADAPTER_SHA256
    )
    assert boundary["f061_field_status"] == "OPEN"
    assert tuple(boundary["unresolved_policy_slots"]) == F061_POLICY_NULL_SLOTS
    unresolved = core.unresolved_definition_bindings()
    for field in F061_POLICY_NULL_SLOTS:
        assert boundary["unresolved_policy_slots"][field] is None
        assert getattr(unresolved, field) is None
    assert retail.SHARED_F061_POLICY_SCHEMA == core.F061_ALLOCATION_SCHEMA
    assert retail.INTEGRATED_F061_MODE == core.F061_ALLOWED_MODES[0]
    assert retail.RETAIL_F061_ADAPTER_ID == core.RETAIL_F061_ADAPTER_ID
    assert retail.RETAIL_F061_ADAPTER_SHA256 == core.RETAIL_F061_ADAPTER_SHA256
    assert retail.retail_f061_adapter_sha256() == core.RETAIL_F061_ADAPTER_SHA256
    assert physionet.SHARED_F061_POLICY_SCHEMA == core.F061_ALLOCATION_SCHEMA
    assert physionet.SHARED_F061_POLICY_MODE == core.F061_ALLOWED_MODES[0]
    assert (
        physionet.PHYSIONET_F061_ADAPTER_ID
        == core.PHYSIONET_F061_ADAPTER_ID
    )
    assert (
        physionet.PHYSIONET_F061_ADAPTER_SHA256
        == core.PHYSIONET_F061_ADAPTER_SHA256
    )
    assert (
        physionet.physionet_f061_adapter_sha256()
        == core.PHYSIONET_F061_ADAPTER_SHA256
    )
    assert boundary["shared_policy_present"] is False
    assert boundary["shared_policy_external_review_present"] is False
    assert boundary["shared_policy_is_exact_domain_allocation"] is False
    assert (
        boundary["retail_native_proposal_requires_shared_policy_definition_binding"]
        is True
    )
    assert boundary["retail_native_proposal_present"] is False
    assert boundary["physionet_natural_group_count_observed"] is False
    assert (
        boundary[
            "physionet_native_proposal_requires_shared_policy_definition_binding"
        ]
        is True
    )
    assert boundary["physionet_native_proposal_present"] is False
    assert (
        boundary["physionet_resolved_counts_require_separate_external_review"]
        is True
    )
    assert boundary["physionet_exact_count_external_review_present"] is False


def test_machine_binds_active_and_historical_split_contracts() -> None:
    boundary = _machine_record()["domain_split_contract_boundary"]
    phys = boundary["physionet-challenge-2012"]
    assert phys["active_contract_id"] == physionet.SPLIT_ALGORITHM_ID
    assert phys["active_contract_sha256"] == physionet.SPLIT_CONTRACT_SHA256
    assert (
        phys["active_implementation_sha256"]
        == physionet.SPLIT_IMPLEMENTATION_SHA256
    )
    assert phys["historical_design_id"] == physionet.CANDIDATE_SPLIT_ALGORITHM_ID
    assert phys["historical_design_raw_sha256"] == (
        physionet.HISTORICAL_CANDIDATE_SPLIT_CONTRACT_RAW_SHA256
    )
    assert phys["active_contract_runtime_recomputed"] is True
    retail_boundary = boundary["online-retail-ii"]
    assert retail_boundary["active_contract_id"] == (
        retail.ACTIVE_RETAIL_SPLIT_CONTRACT_ID
    )
    assert retail_boundary["active_contract_sha256"] == (
        retail.ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256
    )
    assert retail_boundary["historical_design_id"] == (
        retail.HISTORICAL_RETAIL_SPLIT_DESIGN_ID
    )
    assert retail_boundary["historical_design_raw_sha256"] == (
        retail.HISTORICAL_RETAIL_SPLIT_DESIGN_RAW_SHA256
    )
    assert retail_boundary["legacy_misbound_f105_semantic_sha256"] == (
        retail.LEGACY_MISBOUND_F105_SEMANTIC_SHA256
    )
    assert retail_boundary["legacy_misbound_digest_is_split_contract"] is False
    assert retail_boundary["active_contract_runtime_recomputed"] is True


def test_implementation_contracts_match_machine_nonclaims() -> None:
    record = _machine_record()
    package = core.build_offline_precontact_activation("1" * 64)
    decision = core.evaluate_offline_admission(package)
    assert decision["execution_budget"] == 0
    assert decision["operational_authority_present"] is False
    assert decision["admin_contact_authorized"] is False
    assert decision["data_access_authorized"] is False
    assert len(core.EXACT_OPERATION_ROSTER) == 4
    for source, machine in zip(
        core.EXACT_OPERATION_ROSTER, record["operation_roster"]
    ):
        assert machine["ordinal"] == source.global_ordinal
        assert machine["operation_id"] == source.operation_id
        assert machine["domain_id"] == source.domain_id
        assert machine["phase"] == source.phase
        assert machine["exact_target"] == source.exact_target
        assert machine["target_derivation"] == source.exact_target_derivation
        assert machine["selector_identity"] == source.selector_identity
        assert (
            machine["permitted_request_kind"]
            == source.exact_permitted_request_kind
        )
        assert machine["administrative_questions"] == list(
            source.administrative_questions
        )
        assert (
            machine["matching_admin_operation_id"]
            == source.matching_admin_operation_id
        )
        assert machine["required_prior_receipts"] == list(
            source.required_prior_receipts
        )
        assert machine["success_predicate"] == source.success_predicate
        assert machine["terminal_disposition"] == source.terminal_disposition
        assert machine["maximum_attempt_count"] == source.maximum_attempt_count
        assert machine["retry_limit"] == source.retry_limit
        assert machine["redirect_limit"] == source.redirect_limit
        assert machine["fallback_limit"] == source.address_fallback_limit
        assert machine["authentication_permitted"] is source.authentication_permitted
        assert machine["download_permitted"] is source.download_permitted
        assert machine["data_opening_permitted"] is source.data_opening_permitted
        assert machine["protected_data_permitted"] is False
        assert machine["current_execution_budget"] == 0
    assert (
        core.PHYSIONET_SPLIT_CONTRACT_ID == physionet.SPLIT_ALGORITHM_ID
    )
    assert (
        core.PHYSIONET_SPLIT_CONTRACT_SHA256
        == physionet.SPLIT_CONTRACT_SHA256
    )
    historical_path = (
        ROOT
        / "research/fixtures/"
        "manuscript_v3_physionet_patient_disjoint_split_design_v1.json"
    )
    historical_raw = historical_path.read_bytes()
    historical_record = json.loads(historical_raw)
    assert hashlib.sha256(historical_raw).hexdigest() == (
        physionet.HISTORICAL_CANDIDATE_SPLIT_CONTRACT_RAW_SHA256
    )
    assert historical_record["design_identity"]["algorithm_id"] == (
        physionet.CANDIDATE_SPLIT_ALGORITHM_ID
    )
    assert physionet.SPLIT_ALGORITHM_ID != physionet.CANDIDATE_SPLIT_ALGORITHM_ID
    assert physionet.SPLIT_CONTRACT_SHA256 != (
        physionet.HISTORICAL_CANDIDATE_SPLIT_CONTRACT_RAW_SHA256
    )
    assert core.RETAIL_SPLIT_CONTRACT_ID == retail.ACTIVE_RETAIL_SPLIT_CONTRACT_ID
    assert (
        core.RETAIL_SPLIT_CONTRACT_SHA256
        == retail.ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256
    )
    assert retail.active_retail_split_contract_sha256() == (
        retail.ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256
    )
    retail_historical_path = (
        ROOT
        / "research/fixtures/"
        "manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.json"
    )
    retail_historical_raw = retail_historical_path.read_bytes()
    retail_historical_record = json.loads(retail_historical_raw)
    assert hashlib.sha256(retail_historical_raw).hexdigest() == (
        retail.HISTORICAL_RETAIL_SPLIT_DESIGN_RAW_SHA256
    )
    assert retail_historical_record["design_identity"]["algorithm_id"] == (
        retail.HISTORICAL_RETAIL_SPLIT_DESIGN_ID
    )
    assert retail.ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256 not in {
        retail.HISTORICAL_RETAIL_SPLIT_DESIGN_RAW_SHA256,
        retail.LEGACY_MISBOUND_F105_SEMANTIC_SHA256,
    }
    assert retail.support_route_status(None) == "UNRESOLVED"
    support = physionet.unresolved_observation_support(
        physionet.synthetic_activation("PACKAGE-CROSSCHECK")
    )
    assert support.certified is False


def test_bound_sources_have_no_network_process_or_filesystem_imports() -> None:
    forbidden_roots = {
        "asyncio",
        "ftplib",
        "http",
        "multiprocessing",
        "os",
        "requests",
        "shutil",
        "socket",
        "ssl",
        "subprocess",
        "urllib",
    }
    for relative in PACKAGE_PATHS:
        if not relative.startswith("src/"):
            continue
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert imported.isdisjoint(forbidden_roots), (
            relative,
            imported & forbidden_roots,
        )


def test_tampered_bound_file_refuses(tmp_path: Path) -> None:
    root = _copy_validation_tree(tmp_path / "root")
    path = root / "PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION.md"
    path.write_bytes(path.read_bytes() + b"tamper\n")
    with pytest.raises(ValidationError):
        validate_package(root)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda record: record["operation_roster"][0].__setitem__(
            "current_execution_budget", 1
        ),
        lambda record: record["operation_roster"][1].__setitem__(
            "download_permitted", True
        ),
        lambda record: record["future_observations"].__setitem__(
            "observed_snapshot_versions", ["guessed"]
        ),
        lambda record: record["shared_f061_policy_boundary"].__setitem__(
            "physionet_exact_count_external_review_present", True
        ),
        lambda record: record["unresolved_owner_manifest"].__setitem__(
            "accountable_governance_owner", "self-appointed"
        ),
        lambda record: record["closure_effect"].__setitem__("b02_closed", True),
        lambda record: record["closure_effect"].__setitem__(
            "seven_operational_tasks_closed_count", 1
        ),
    ),
)
def test_semantic_authority_or_closure_smuggling_refuses(
    tmp_path: Path, mutation
) -> None:
    root = _copy_validation_tree(tmp_path / "root")
    record = json.loads((root / MACHINE_PATH).read_text(encoding="utf-8"))
    mutation(record)
    _write_machine(root, record)
    with pytest.raises(ValidationError):
        validate_package(root)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda record: record["authority_provenance"].__setitem__(
            "external_contact_or_browsing_authorized", 0
        ),
        lambda record: record["authority_provenance"].__setitem__(
            "offline_construction_and_review_authorized", 1
        ),
        lambda record: record["operation_roster"][0].__setitem__(
            "current_execution_budget", 0.0
        ),
        lambda record: record["operation_roster"][0].__setitem__(
            "current_execution_budget", False
        ),
        lambda record: record["operation_roster"][1].__setitem__(
            "maximum_attempt_count", True
        ),
        lambda record: record["activation_contract"].__setitem__(
            "data_rows_dormant", 1
        ),
        lambda record: record["execution_boundary"].__setitem__(
            "scientific_execution_budget", False
        ),
        lambda record: record["shared_f061_policy_boundary"].__setitem__(
            "shared_policy_present", 0
        ),
        lambda record: record["domain_split_contract_boundary"][
            "online-retail-ii"
        ].__setitem__("active_contract_runtime_recomputed", 1),
        lambda record: record["domain_readiness"][
            "physionet-challenge-2012"
        ].__setitem__("actual_domain_admission_present", 0),
        lambda record: record["closure_effect"].__setitem__(
            "field_count_delta", False
        ),
        lambda record: record["qualification_boundary"].__setitem__(
            "synthetic_inputs_only", 1
        ),
    ),
)
def test_semantic_scalar_type_confusion_refuses(mutation) -> None:
    record = _machine_record()
    mutation(record)
    with pytest.raises(ValidationError):
        _validate_semantics(record)


@pytest.mark.parametrize(
    "unsafe_path",
    (
        "",
        "../escape",
        "a/../escape",
        "./relative",
        "/absolute",
        1,
        None,
    ),
)
def test_unsafe_relative_path_refuses(unsafe_path) -> None:
    with pytest.raises(ValidationError):
        _relative_parts(unsafe_path)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda bindings: bindings[0].__setitem__("raw_sha256", "x" * 64),
        lambda bindings: bindings[0].__setitem__("raw_sha256", None),
        lambda bindings: bindings[0].__setitem__("bytes", True),
        lambda bindings: bindings[0].__setitem__("bytes", 17235.0),
        lambda bindings: bindings[0].__setitem__("path", "../escape"),
        lambda bindings: bindings[0].__setitem__("path", "/absolute"),
        lambda bindings: bindings[0].__setitem__("path", 1),
        lambda bindings: bindings[0].__setitem__("ordinal", False),
    ),
)
def test_malformed_binding_metadata_refuses(mutation) -> None:
    bindings = deepcopy(_machine_record()["package_bindings"])
    mutation(bindings)
    with pytest.raises(ValidationError):
        _validate_binding_roster(ROOT, bindings, PACKAGE_PATHS, "package bindings")


def test_duplicate_machine_key_refuses(tmp_path: Path) -> None:
    root = _copy_validation_tree(tmp_path / "root")
    path = root / MACHINE_PATH
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        '  "state":',
        '  "state": "DUPLICATE",\n  "state":',
        1,
    )
    path.write_text(text, encoding="utf-8")
    path.chmod(0o644)
    with pytest.raises(ValidationError, match="duplicate JSON key"):
        validate_package(root)


def test_symlinked_bound_file_refuses(tmp_path: Path) -> None:
    root = _copy_validation_tree(tmp_path / "root")
    path = root / "PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION.md"
    replacement = root / "replacement.md"
    replacement.write_bytes(path.read_bytes())
    replacement.chmod(0o644)
    path.unlink()
    path.symlink_to(replacement)
    with pytest.raises(ValidationError):
        validate_package(root)


def test_hardlinked_bound_file_refuses(tmp_path: Path) -> None:
    root = _copy_validation_tree(tmp_path / "root")
    path = root / "PROJECT_B02_B03_OFFLINE_PRECONTACT_ACTIVATION.md"
    os.link(path, root / "second-link.md")
    with pytest.raises(ValidationError):
        validate_package(root)


def test_symlinked_intermediate_directory_refuses(tmp_path: Path) -> None:
    root = _copy_validation_tree(tmp_path / "root")
    real_source = tmp_path / "real-source"
    (root / "src").rename(real_source)
    (root / "src").symlink_to(real_source, target_is_directory=True)
    with pytest.raises(ValidationError):
        validate_package(root)
    OTHER_DEFINITION_NULL_SLOTS,
