from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
from pathlib import Path

import pytest

from heterodiff.data import online_retail_ii_admission_preflight as retail_preflight
from heterodiff.data import physionet_2012_admission_preflight as physionet_preflight
from heterodiff.data import two_domain_offline_precontact_activation as activation


PREDECESSOR = hashlib.sha256(b"accepted-predecessor-set").hexdigest()


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _complete_owners() -> activation.OwnerManifest:
    return activation.OwnerManifest(
        accountable_governance_owner_id="governance-owner",
        accountable_governance_owner_acceptance_sha256=_digest("governance-accept"),
        license_privacy_institutional_approval_endpoint_id="approval-endpoint",
        license_privacy_institutional_approval_endpoint_acceptance_sha256=_digest(
            "approval-endpoint-accept"
        ),
        raw_snapshot_custodian_id="raw-custodian",
        raw_snapshot_custodian_acceptance_sha256=_digest("raw-accept"),
        deterministic_split_operator_id="split-operator",
        deterministic_split_operator_acceptance_sha256=_digest("split-accept"),
        independent_held_out_escrow_custodian_id="independent-escrow-custodian",
        independent_held_out_escrow_custodian_acceptance_sha256=_digest(
            "escrow-accept"
        ),
        independent_final_opening_approver_id="independent-final-approver",
        independent_final_opening_approver_acceptance_sha256=_digest(
            "final-accept"
        ),
        key_acl_acceptance_authority_id="key-acl-authority",
        key_acl_acceptance_authority_acceptance_sha256=_digest("key-acl-accept"),
        retention_deletion_owner_id="retention-owner",
        retention_deletion_owner_acceptance_sha256=_digest("retention-accept"),
        incident_response_owner_id="incident-owner",
        incident_response_owner_acceptance_sha256=_digest("incident-accept"),
    )


def _complete_bindings() -> activation.OfflineDefinitionBindings:
    draft = replace(
        activation.unresolved_definition_bindings(),
        physionet_selector_record_sha256=_digest("physionet-selector"),
        retail_selector_record_sha256=_digest("retail-selector"),
        f061_allocation_id="POWER_REVIEWED_TWO_DOMAIN_ALLOCATION_V1",
        f061_mode="EXACT_PROPORTIONS_HAMILTON",
        f061_values=(6, 2, 2),
        f061_denominator_is_null=False,
        f061_denominator=10,
        f061_minimum_counts=(1, 1, 1),
        f061_rounding_rule_id=activation.F061_HAMILTON_ROUNDING_RULE_ID,
        f061_power_requirement_id="B07_WIDTH6_256_ADDRESS_POWER_REQUIREMENT_V1",
        f061_power_review_receipt_sha256=_digest("f061-power-review"),
        f061_power_review_accepted=True,
        contact_target_roster_sha256=_digest("contact-target-roster"),
        contact_target_count=4,
        approval_requirement_roster_sha256=_digest("approval-requirements"),
        approval_receipt_validator_roster_sha256=_digest("approval-validators"),
        conflict_of_interest_determination_sha256=_digest("coi-determination"),
        contact_roster_complete=True,
        escrow_control_binding_sha256=_digest("escrow-control"),
        held_out_material_definition_sha256=_digest("heldout-definition"),
        final_opening_rule_sha256=_digest("final-opening-rule"),
        append_only_log_schema_sha256=_digest("append-only-log-schema"),
    )
    with_proposal = replace(
        draft,
        f061_allocation_proposal_sha256=(
            activation.f061_allocation_proposal_sha256(draft)
        ),
    )
    return replace(
        with_proposal,
        f061_allocation_definition_sha256=(
            activation.f061_allocation_definition_sha256(with_proposal)
        ),
    )


def _eligible_package() -> activation.OfflinePrecontactActivation:
    return activation.build_offline_precontact_activation(
        PREDECESSOR,
        _complete_owners(),
        _complete_bindings(),
    )


def _reseal_package(
    package: activation.OfflinePrecontactActivation,
) -> activation.OfflinePrecontactActivation:
    draft = replace(package, package_identity_sha256="0" * 64)
    return replace(
        draft,
        package_identity_sha256=activation._package_identity(draft),
    )


def _reseal_operation(
    operation: activation.OperationSpec,
) -> activation.OperationSpec:
    draft = replace(operation, operation_identity_sha256="0" * 64)
    return replace(
        draft,
        operation_identity_sha256=activation.operation_identity_sha256(draft),
    )


def test_exact_four_row_roster_questions_selectors_and_dispositions() -> None:
    rows = activation.EXACT_OPERATION_ROSTER
    assert len(rows) == 4
    assert [row.global_ordinal for row in rows] == [0, 1, 2, 3]
    assert [(row.domain_id, row.phase) for row in rows] == [
        (activation.PHYSIONET_DOMAIN, "ADMIN"),
        (activation.RETAIL_DOMAIN, "ADMIN"),
        (activation.PHYSIONET_DOMAIN, "DATA"),
        (activation.RETAIL_DOMAIN, "DATA"),
    ]
    assert rows[0].exact_target == activation.PHYSIONET_URL
    assert rows[1].exact_target == activation.RETAIL_URL
    assert rows[2].exact_target is None
    assert rows[3].exact_target is None
    assert rows[0].selector_identity == activation.PHYSIONET_SELECTOR_ID
    assert rows[2].selector_identity == activation.PHYSIONET_SELECTOR_ID
    assert rows[1].selector_identity == activation.RETAIL_SELECTOR_ID
    assert rows[3].selector_identity == activation.RETAIL_SELECTOR_ID
    assert len(activation.ADMIN_QUESTIONS) == 7
    assert rows[0].administrative_questions == activation.ADMIN_QUESTIONS
    assert rows[1].administrative_questions == activation.ADMIN_QUESTIONS
    assert rows[2].administrative_questions == ()
    assert rows[3].administrative_questions == ()
    for row in rows[:2]:
        assert row.success_predicate == activation.ADMIN_SUCCESS_PREDICATE
        assert row.terminal_disposition == "ADMIN_CONTACT_TERMINAL_NO_GO"
    for row in rows[2:]:
        assert row.success_predicate == activation.DATA_SUCCESS_PREDICATE
        assert row.terminal_disposition == "DATA_ACCESS_TERMINAL_NO_GO"


def test_all_rows_have_one_attempt_zero_limits_and_no_capability() -> None:
    for row in activation.EXACT_OPERATION_ROSTER:
        assert row.maximum_attempt_count == 1
        assert row.retry_limit == 0
        assert row.redirect_limit == 0
        assert row.address_fallback_limit == 0
        assert row.authentication_permitted is False
        assert row.download_permitted is False
        assert row.data_opening_permitted is False
        assert row.currently_eligible is False
        assert row.operation_identity_sha256 == activation.operation_identity_sha256(row)


def test_data_rows_bind_every_dependency_and_matching_admin() -> None:
    row0, row1, row2, row3 = activation.EXACT_OPERATION_ROSTER
    assert row2.matching_admin_operation_id == row0.operation_id
    assert row3.matching_admin_operation_id == row1.operation_id
    for row in (row2, row3):
        assert row.required_prior_receipts == (
            "MATCHING_ADMIN_EXACT_SUCCESS",
            "ALL_REQUIRED_APPROVAL_RECEIPTS",
            "SEPARATELY_REVIEWED_DATA_ACCESS_INSTANCE",
            "FRESH_EXACT_DATA_ACCESS_AUTHORITY",
            "DURABLE_INTENT",
        )


def test_unresolved_default_is_strict_null_state_zero_hold() -> None:
    package = activation.build_offline_precontact_activation(PREDECESSOR)
    report = activation.evaluate_offline_admission(package)
    assert report["decision"] == activation.OFFLINE_HOLD_DECISION
    assert report["current_state_ordinal"] == 0
    assert report["current_state"] == activation.STATE_MACHINE[0]
    assert report["missing_offline_fields"]
    assert all(value is None for value in vars(package.owner_manifest).values())
    bindings = vars(package.definition_bindings)
    for field in activation._FUTURE_BINDING_DIGEST_FIELDS:
        assert bindings[field] is None
    assert package.definition_bindings.f061_allocation_id is None
    assert package.definition_bindings.f061_mode is None
    assert package.definition_bindings.f061_values is None
    assert package.definition_bindings.f061_denominator_is_null is None
    assert package.definition_bindings.f061_denominator is None
    assert package.definition_bindings.f061_minimum_counts is None
    assert package.definition_bindings.f061_rounding_rule_id is None
    assert package.definition_bindings.f061_power_requirement_id is None
    assert package.definition_bindings.f061_power_review_accepted is None
    assert package.definition_bindings.contact_target_count is None
    assert package.definition_bindings.contact_roster_complete is None
    assert "definition_bindings.f061_denominator" in report["missing_offline_fields"]


def test_complete_population_is_only_eligible_for_external_review() -> None:
    package = _eligible_package()
    report = activation.evaluate_offline_admission(package)
    assert report["decision"] == activation.OFFLINE_ELIGIBLE_DECISION
    assert report["current_state_ordinal"] == 1
    assert report["current_state"] == activation.STATE_MACHINE[1]
    assert report["missing_offline_fields"] == []
    assert report["external_independent_review_required"] is True
    assert report["external_review_admitted"] is False
    assert report["execution_budget"] == 0
    assert report["operational_authority_present"] is False
    assert report["admin_contact_authorized"] is False
    assert report["data_access_authorized"] is False
    assert "GO" not in report["decision"]


def test_closed_definition_covers_required_surfaces() -> None:
    bindings = _complete_bindings()
    assert bindings.physionet_selector_id == activation.PHYSIONET_SELECTOR_ID
    assert bindings.retail_selector_id == activation.RETAIL_SELECTOR_ID
    assert bindings.physionet_split_contract_id
    assert bindings.retail_split_contract_id
    assert bindings.f061_allocation_schema == activation.F061_ALLOCATION_SCHEMA
    assert bindings.f061_allowed_method_id == activation.F061_ALLOWED_METHOD_ID
    assert bindings.f061_mode == "EXACT_PROPORTIONS_HAMILTON"
    assert bindings.f061_values == (6, 2, 2)
    assert bindings.f061_denominator == 10
    assert bindings.f061_allocation_proposal_sha256
    assert bindings.f061_power_review_accepted is True
    assert (
        bindings.f061_allocation_proposal_sha256
        == activation.f061_allocation_proposal_sha256(bindings)
    )
    assert (
        bindings.f061_allocation_definition_sha256
        == activation.f061_allocation_definition_sha256(bindings)
    )
    assert bindings.contact_target_roster_sha256
    assert bindings.approval_requirement_roster_sha256
    assert bindings.approval_receipt_validator_roster_sha256
    assert bindings.conflict_of_interest_determination_sha256
    assert bindings.escrow_control_binding_sha256
    assert bindings.held_out_material_definition_sha256
    assert bindings.final_opening_rule_sha256
    assert bindings.append_only_log_schema_sha256
    assert bindings.terminal_failure_map == activation.TERMINAL_FAILURE_MAP
    assert bindings.unknown_or_missing_outcome_is_success is False
    assert bindings.repair_retry_replacement_fallback_permitted is False


def test_cross_domain_contract_schema_and_mode_are_exact() -> None:
    assert (
        activation.PHYSIONET_SPLIT_CONTRACT_ID
        == physionet_preflight.SPLIT_ALGORITHM_ID
    )
    assert (
        activation.PHYSIONET_SPLIT_CONTRACT_SHA256
        == physionet_preflight.SPLIT_CONTRACT_SHA256
    )
    assert activation.F061_ALLOCATION_SCHEMA != retail_preflight.F061_ALLOCATION_SCHEMA
    assert (
        activation.RETAIL_F061_PROPOSAL_SCHEMA
        == retail_preflight.F061_ALLOCATION_SCHEMA
    )
    assert activation.F061_ALLOWED_MODES == ("EXACT_PROPORTIONS_HAMILTON",)
    assert (
        activation.F061_HAMILTON_ROUNDING_RULE_ID
        == physionet_preflight.F061_ROUNDING_RULE_ID
    )
    bindings = activation.unresolved_definition_bindings()
    assert bindings.retail_f061_adapter_id == activation.RETAIL_F061_ADAPTER_ID
    assert bindings.retail_f061_adapter_sha256 == activation.RETAIL_F061_ADAPTER_SHA256
    assert (
        bindings.physionet_f061_adapter_id
        == activation.PHYSIONET_F061_ADAPTER_ID
    )
    assert (
        bindings.physionet_f061_adapter_sha256
        == activation.PHYSIONET_F061_ADAPTER_SHA256
    )


def test_shared_policy_projects_without_codec_or_review_ambiguity() -> None:
    bindings = _complete_bindings()
    retail = activation.project_shared_policy_to_retail_f061_proposal(bindings)
    assert retail == {
        "schema_version": retail_preflight.F061_ALLOCATION_SCHEMA,
        "allocation_id": bindings.f061_allocation_id,
        "mode": "EXACT_PROPORTIONS_HAMILTON",
        "values": {"TRAIN": 6, "VALIDATION": 2, "TEST": 2},
        "denominator": 10,
        "minimum_counts": {"TRAIN": 1, "VALIDATION": 1, "TEST": 1},
        "power_requirement_id": bindings.f061_power_requirement_id,
    }
    retail_digest = retail_preflight.f061_allocation_proposal_sha256(retail)
    assert len(retail_digest) == 64
    assert retail_digest != bindings.f061_allocation_proposal_sha256

    physionet = activation.project_shared_policy_to_physionet_f061_proposal(
        bindings, 11
    )
    assert physionet["counts"] == (7, 2, 2)
    physionet_digest = physionet_preflight.f061_allocation_proposal_sha256(
        **physionet
    )
    assert len(physionet_digest) == 64
    assert physionet_digest not in {
        retail_digest,
        bindings.f061_allocation_proposal_sha256,
    }


def test_adapter_drift_and_unusable_physionet_counts_fail_closed() -> None:
    bindings = _complete_bindings()
    for field in ("retail_f061_adapter_id", "physionet_f061_adapter_sha256"):
        mutant = replace(bindings, **{field: "OTHER"})
        with pytest.raises(activation.OfflineActivationError, match="DEFINITION_DRIFT"):
            activation.project_shared_policy_to_retail_f061_proposal(mutant)
    for count, code in (
        (True, "PHYSIONET_NATURAL_GROUP_COUNT_INVALID"),
        (2, "PHYSIONET_F061_RESOLVED_COUNTS_UNDERPOWERED"),
    ):
        with pytest.raises(activation.OfflineActivationError, match=code):
            activation.project_shared_policy_to_physionet_f061_proposal(
                bindings, count
            )


def test_adapter_hashes_recompute_from_canonical_contract_records() -> None:
    retail = activation.retail_f061_adapter_record()
    physionet = activation.physionet_f061_adapter_record()
    assert activation.retail_f061_adapter_sha256(retail) == (
        activation.RETAIL_F061_ADAPTER_SHA256
    )
    assert activation.physionet_f061_adapter_sha256(physionet) == (
        activation.PHYSIONET_F061_ADAPTER_SHA256
    )
    assert activation.retail_f061_adapter_sha256() == (
        activation.RETAIL_F061_ADAPTER_SHA256
    )
    assert activation.physionet_f061_adapter_sha256() == (
        activation.PHYSIONET_F061_ADAPTER_SHA256
    )

    retail["algorithm"] = "AMBIGUOUS_MAPPING"
    physionet["review_semantics"] = "SHARED_REVIEW_IMPROPERLY_REUSED"
    assert (
        activation.retail_f061_adapter_sha256(retail)
        != activation.RETAIL_F061_ADAPTER_SHA256
    )
    assert (
        activation.physionet_f061_adapter_sha256(physionet)
        != activation.PHYSIONET_F061_ADAPTER_SHA256
    )


@pytest.mark.parametrize(
    ("record_constructor_name", "expected_domain"),
    [
        ("retail_f061_adapter_record", "retail"),
        ("physionet_f061_adapter_record", "physionet"),
    ],
)
def test_runtime_recomputation_rejects_canonical_adapter_record_drift(
    monkeypatch: pytest.MonkeyPatch,
    record_constructor_name: str,
    expected_domain: str,
) -> None:
    original = getattr(activation, record_constructor_name)

    def drifted_record() -> dict[str, object]:
        record = original()
        record["algorithm"] = "DRIFTED_ADAPTER_ALGORITHM"
        return record

    monkeypatch.setattr(activation, record_constructor_name, drifted_record)
    with pytest.raises(
        activation.OfflineActivationError,
        match=f"ADAPTER_CONTRACT_DIGEST_MISMATCH:{expected_domain}",
    ):
        activation.build_offline_precontact_activation(
            PREDECESSOR,
            _complete_owners(),
            _complete_bindings(),
        )


def test_unresolved_f061_does_not_select_the_historical_candidate() -> None:
    bindings = activation.unresolved_definition_bindings()
    assert bindings.f061_allocation_id is None
    assert bindings.f061_mode is None
    assert bindings.f061_values is None
    assert bindings.f061_denominator_is_null is None
    assert bindings.f061_denominator is None
    assert bindings.f061_minimum_counts is None
    assert bindings.f061_rounding_rule_id is None
    assert bindings.f061_power_requirement_id is None
    assert bindings.f061_allocation_proposal_sha256 is None
    assert bindings.f061_power_review_receipt_sha256 is None
    assert bindings.f061_power_review_accepted is None
    assert bindings.f061_allocation_definition_sha256 is None
    assert not hasattr(activation, "F061_NUMERATORS")


def test_owner_manifest_has_nine_distinct_principal_roles_and_acceptances() -> None:
    owners = _complete_owners()
    principal_fields = activation._OWNER_ID_FIELDS
    acceptance_fields = activation._OWNER_ACCEPTANCE_FIELDS
    assert len(principal_fields) == 9
    assert len(acceptance_fields) == 9
    principals = [getattr(owners, field) for field in principal_fields]
    assert len(set(principals)) == 9
    assert all(getattr(owners, field) for field in acceptance_fields)


def test_canonical_serialization_and_identities_are_stable() -> None:
    first = _eligible_package()
    second = _eligible_package()
    raw = activation.canonical_activation_bytes(first)
    assert first == second
    assert first.package_identity_sha256 == second.package_identity_sha256
    assert activation.activation_file_sha256(first) == hashlib.sha256(raw).hexdigest()
    assert raw.endswith(b"\n") and raw.count(b"\n") == 1
    decoded = json.loads(raw)
    assert decoded["package_identity_sha256"] == first.package_identity_sha256
    assert raw[:-1] == json.dumps(
        decoded,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def test_model_is_frozen_and_closed_rosters_are_tuples() -> None:
    package = _eligible_package()
    with pytest.raises(FrozenInstanceError):
        package.current_state_ordinal = 2  # type: ignore[misc]
    assert type(package.state_machine) is tuple
    assert type(package.operation_roster) is tuple
    assert type(package.external_observations) is tuple
    assert type(package.definition_bindings.terminal_failure_map) is tuple


@pytest.mark.parametrize(
    "missing_field",
    [
        "physionet_selector_record_sha256",
        "retail_selector_record_sha256",
        "f061_power_review_receipt_sha256",
        "f061_allocation_definition_sha256",
        "contact_target_roster_sha256",
        "approval_requirement_roster_sha256",
        "approval_receipt_validator_roster_sha256",
        "conflict_of_interest_determination_sha256",
        "escrow_control_binding_sha256",
        "held_out_material_definition_sha256",
        "final_opening_rule_sha256",
        "append_only_log_schema_sha256",
    ],
)
def test_missing_selector_f061_approval_or_escrow_binding_holds_state_zero(
    missing_field: str,
) -> None:
    bindings = replace(_complete_bindings(), **{missing_field: None})
    package = activation.build_offline_precontact_activation(
        PREDECESSOR,
        _complete_owners(),
        bindings,
    )
    report = activation.evaluate_offline_admission(package)
    assert report["decision"] == activation.OFFLINE_HOLD_DECISION
    assert report["current_state_ordinal"] == 0
    assert f"definition_bindings.{missing_field}" in report["missing_offline_fields"]


@pytest.mark.parametrize(
    "missing_field",
    [
        "f061_allocation_id",
        "f061_mode",
        "f061_values",
        "f061_denominator_is_null",
        "f061_minimum_counts",
        "f061_rounding_rule_id",
        "f061_power_requirement_id",
        "f061_power_review_accepted",
        "contact_target_count",
        "contact_roster_complete",
    ],
)
def test_missing_non_digest_definition_binding_holds_state_zero(
    missing_field: str,
) -> None:
    bindings = replace(_complete_bindings(), **{missing_field: None})
    package = activation.build_offline_precontact_activation(
        PREDECESSOR,
        _complete_owners(),
        bindings,
    )
    report = activation.evaluate_offline_admission(package)
    assert report["current_state_ordinal"] == 0
    assert f"definition_bindings.{missing_field}" in report["missing_offline_fields"]


@pytest.mark.parametrize("row_index", [0, 1])
def test_missing_or_changed_admin_questions_fail_closed(row_index: int) -> None:
    package = _eligible_package()
    rows = list(package.operation_roster)
    rows[row_index] = _reseal_operation(
        replace(
            rows[row_index],
            administrative_questions=rows[row_index].administrative_questions[:-1],
        )
    )
    mutant = _reseal_package(replace(package, operation_roster=tuple(rows)))
    with pytest.raises(activation.OfflineActivationError, match="OPERATION_ROSTER_DRIFT"):
        activation.evaluate_offline_admission(mutant)


@pytest.mark.parametrize("row_index", [0, 1, 2, 3])
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("selector_identity", "OTHER_SELECTOR"),
        ("success_predicate", "SELF_ATTESTED_SUCCESS"),
        ("terminal_disposition", "RETRY_OR_REPAIR"),
    ],
)
def test_selector_success_or_terminal_drift_fails_closed(
    row_index: int,
    field: str,
    value: str,
) -> None:
    package = _eligible_package()
    rows = list(package.operation_roster)
    rows[row_index] = _reseal_operation(replace(rows[row_index], **{field: value}))
    mutant = _reseal_package(replace(package, operation_roster=tuple(rows)))
    with pytest.raises(activation.OfflineActivationError, match="OPERATION_ROSTER_DRIFT"):
        activation.evaluate_offline_admission(mutant)


@pytest.mark.parametrize("owner_field", activation._OWNER_ID_FIELDS)
def test_each_missing_principal_role_holds_state_zero(owner_field: str) -> None:
    owners = replace(_complete_owners(), **{owner_field: None})
    package = activation.build_offline_precontact_activation(
        PREDECESSOR,
        owners,
        _complete_bindings(),
    )
    report = activation.evaluate_offline_admission(package)
    assert report["current_state_ordinal"] == 0
    assert f"owner_manifest.{owner_field}" in report["missing_offline_fields"]


def test_any_principal_alias_is_forbidden() -> None:
    owners = replace(
        _complete_owners(),
        incident_response_owner_id="raw-custodian",
    )
    with pytest.raises(
        activation.OfflineActivationError,
        match="PRINCIPAL_ROLE_ALIAS_FORBIDDEN",
    ):
        activation.build_offline_precontact_activation(
            PREDECESSOR,
            owners,
            _complete_bindings(),
        )


@pytest.mark.parametrize(
    "field",
    [
        "external_review_receipt_sha256",
        "external_review_decision",
        "external_reviewer_principal_id",
    ],
)
def test_invented_external_review_metadata_never_admits(field: str) -> None:
    package = _eligible_package()
    value = _digest(field) if field.endswith("sha256") else "SELF_ATTESTED_GO"
    mutant = _reseal_package(replace(package, **{field: value}))
    with pytest.raises(
        activation.OfflineActivationError,
        match="EXTERNAL_REVIEW_METADATA_NOT_ADMISSIBLE_HERE",
    ):
        activation.evaluate_offline_admission(mutant)


def test_caller_cannot_force_reviewed_state_two() -> None:
    package = _eligible_package()
    mutant = _reseal_package(replace(package, current_state_ordinal=2))
    with pytest.raises(
        activation.OfflineActivationError,
        match="FORWARD_ONLY_STAGE_SKIPPED_OR_REVERSED",
    ):
        activation.evaluate_offline_admission(mutant)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("admin_contact_attempt_budget", 1),
        ("data_access_attempt_budget", 1),
        ("snapshot_open_budget", 1),
        ("split_execution_budget", 1),
        ("escrow_activation_budget", 1),
        ("scientific_execution_budget", 1),
        ("admin_contact_attempt_budget", True),
    ],
)
def test_budget_smuggling_fails_closed(field: str, value: object) -> None:
    package = _eligible_package()
    boundary = replace(package.execution_boundary, **{field: value})
    mutant = _reseal_package(replace(package, execution_boundary=boundary))
    with pytest.raises(activation.OfflineActivationError, match="NONZERO_EXECUTION_BUDGET"):
        activation.evaluate_offline_admission(mutant)


@pytest.mark.parametrize(
    "field",
    [
        "operational_authority_present",
        "admin_contact_authority_present",
        "data_access_authority_present",
        "durable_intent_present",
        "network_or_contact_authorized",
        "authentication_authorized",
        "download_authorized",
        "data_opening_authorized",
        "split_execution_authorized",
        "escrow_activation_authorized",
    ],
)
def test_authority_smuggling_fails_closed(field: str) -> None:
    package = _eligible_package()
    boundary = replace(package.execution_boundary, **{field: True})
    mutant = _reseal_package(replace(package, execution_boundary=boundary))
    with pytest.raises(
        activation.OfflineActivationError,
        match="OPERATIONAL_AUTHORITY_SMUGGLED",
    ):
        activation.evaluate_offline_admission(mutant)


def test_definition_identity_and_failure_map_drift_fail_closed() -> None:
    package = _eligible_package()
    for field, value in (
        ("physionet_selector_id", "OTHER_SELECTOR"),
        ("retail_split_contract_id", "OTHER_SPLIT"),
        ("terminal_failure_map", activation.TERMINAL_FAILURE_MAP[:-1]),
        ("unknown_or_missing_outcome_is_success", True),
        ("repair_retry_replacement_fallback_permitted", True),
    ):
        bindings = replace(package.definition_bindings, **{field: value})
        mutant = _reseal_package(replace(package, definition_bindings=bindings))
        with pytest.raises(activation.OfflineActivationError, match="DEFINITION_DRIFT"):
            activation.evaluate_offline_admission(mutant)


def test_f061_proportions_and_hamilton_rounding_must_be_coherent() -> None:
    owners = _complete_owners()
    for changes, code in (
        (
            {
                "f061_denominator": 9,
            },
            "F061_HAMILTON_DEFINITION_INCOHERENT",
        ),
        ({"f061_mode": "EXACT_COUNTS"}, "F061_MODE_INVALID"),
    ):
        bindings = replace(_complete_bindings(), **changes)
        with pytest.raises(activation.OfflineActivationError, match=code):
            activation.build_offline_precontact_activation(
                PREDECESSOR,
                owners,
                bindings,
            )


@pytest.mark.parametrize(
    ("changes", "code"),
    (
        ({"f061_denominator": -1}, "F061_DENOMINATOR_INVALID"),
        ({"f061_denominator": 0}, "F061_DENOMINATOR_INVALID"),
        (
            {"f061_denominator_is_null": True},
            "F061_DENOMINATOR_NULL_FLAG_INVALID",
        ),
        (
            {"f061_rounding_rule_id": "OTHER_RULE"},
            "F061_ROUNDING_RULE_INVALID",
        ),
    ),
)
def test_partial_f061_malformed_present_values_fail_closed(
    changes: dict[str, object], code: str
) -> None:
    bindings = replace(activation.unresolved_definition_bindings(), **changes)
    with pytest.raises(activation.OfflineActivationError, match=code):
        activation.build_offline_precontact_activation(
            PREDECESSOR,
            definition_bindings=bindings,
        )


def test_f061_proposal_review_and_definition_cross_bindings_fail_closed() -> None:
    owners = _complete_owners()
    bindings = _complete_bindings()
    for field, value, code in (
        (
            "f061_allocation_proposal_sha256",
            _digest("wrong-proposal"),
            "F061_PROPOSAL_BINDING_MISMATCH",
        ),
        (
            "f061_allocation_definition_sha256",
            _digest("wrong-definition"),
            "F061_DEFINITION_BINDING_MISMATCH",
        ),
        (
            "f061_power_review_accepted",
            False,
            "F061_POWER_REVIEW_NOT_ACCEPTED",
        ),
    ):
        mutant = replace(bindings, **{field: value})
        with pytest.raises(activation.OfflineActivationError, match=code):
            activation.build_offline_precontact_activation(
                PREDECESSOR,
                owners,
                mutant,
            )


def test_f061_proposal_digest_binds_every_actual_definition_field() -> None:
    owners = _complete_owners()
    bindings = _complete_bindings()
    mutant = replace(bindings, f061_power_requirement_id="OTHER_POWER_REQUIREMENT")
    with pytest.raises(
        activation.OfflineActivationError,
        match="F061_PROPOSAL_BINDING_MISMATCH",
    ):
        activation.build_offline_precontact_activation(
            PREDECESSOR,
            owners,
            mutant,
        )


def test_any_non_null_external_observation_fails_closed() -> None:
    package = _eligible_package()
    observation = replace(
        package.external_observations[0],
        observed_snapshot_version="1.0.0",
    )
    mutant = _reseal_package(
        replace(
            package,
            external_observations=(observation, package.external_observations[1]),
        )
    )
    with pytest.raises(
        activation.OfflineActivationError,
        match="EXTERNAL_OBSERVATION_PRESENT_BEFORE_EXECUTION",
    ):
        activation.evaluate_offline_admission(mutant)


def test_data_row_cannot_be_activated_or_drop_a_dependency() -> None:
    package = _eligible_package()
    for field, value in (
        ("currently_eligible", True),
        ("required_prior_receipts", package.operation_roster[2].required_prior_receipts[1:]),
    ):
        rows = list(package.operation_roster)
        rows[2] = _reseal_operation(replace(rows[2], **{field: value}))
        mutant = _reseal_package(replace(package, operation_roster=tuple(rows)))
        with pytest.raises(activation.OfflineActivationError, match="OPERATION_ROSTER_DRIFT"):
            activation.evaluate_offline_admission(mutant)


def test_equality_compatible_string_subclasses_fail_closed() -> None:
    class StringAlias(str):
        pass

    package = _eligible_package()
    rows = list(package.operation_roster)
    rows[0] = _reseal_operation(
        replace(rows[0], exact_target=StringAlias(activation.PHYSIONET_URL))
    )
    mutant = _reseal_package(replace(package, operation_roster=tuple(rows)))
    with pytest.raises(
        activation.OfflineActivationError,
        match="OPERATION_TARGET_TYPE_INVALID",
    ):
        activation.evaluate_offline_admission(mutant)


def test_module_has_no_io_network_process_entropy_or_review_admission_surface() -> None:
    source_path = Path(activation.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert imports <= {"__future__", "dataclasses", "hashlib", "json", "typing"}
    banned_calls = {
        "open",
        "exec",
        "eval",
        "compile",
        "input",
        "socket",
        "urlopen",
        "request",
        "run",
        "Popen",
        "system",
        "urandom",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not (called_names & banned_calls)
    assert "OfflineReview" not in vars(activation)
    assert not any(name.startswith("admit_external") for name in vars(activation))
