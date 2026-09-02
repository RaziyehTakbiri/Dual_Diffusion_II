"""Synthetic and hostile tests for the Online Retail II admission preflight."""

from __future__ import annotations

import ast
import copy
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from heterodiff.data import online_retail_ii_admission_preflight as preflight


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/heterodiff/data/online_retail_ii_admission_preflight.py"


def _sha(character: str) -> str:
    return character * 64


def _shared_policy(**overrides: object) -> preflight.RetailSharedF061Policy:
    values = {
        "allocation_id": "SYNTHETIC-HAMILTON-70-15-15-V1",
        "values": (70, 15, 15),
        "denominator": 100,
        "minimum_counts": (1, 1, 1),
        "power_requirement_id": "SYNTHETIC-POWER-REQUIREMENT-V1",
        "power_review_receipt_sha256": _sha("b"),
        "power_review_accepted": True,
    }
    values.update(overrides)
    return preflight.RetailSharedF061Policy.create(**values)


class _EqualityLyingString(str):
    """A foreign carrier that claims equality with every fixed identity."""

    def __eq__(self, other) -> bool:
        return True

    def __ne__(self, other) -> bool:
        return False

    __hash__ = str.__hash__


def _resealed_receipt_values(receipt, domain: bytes, **overrides) -> dict:
    values = {
        name: getattr(receipt, name)
        for name in receipt.__dataclass_fields__
    }
    values.update(overrides)
    payload = {
        name: value
        for name, value in values.items()
        if name != "receipt_sha256"
    }
    values["receipt_sha256"] = preflight._digest(domain, payload)
    return values


def _bind_f061_proposal(value: dict) -> dict:
    proposal = {
        key: value[key]
        for key in (
            "schema_version",
            "allocation_id",
            "mode",
            "values",
            "denominator",
            "minimum_counts",
            "power_requirement_id",
        )
    }
    value["allocation_proposal_sha256"] = (
        preflight.f061_allocation_proposal_sha256(proposal)
    )
    return value


def _counts_allocation(
    train: int = 4,
    validation: int = 1,
    test: int = 1,
    *,
    minimum_train: int = 1,
    minimum_validation: int = 1,
    minimum_test: int = 1,
) -> dict:
    return _bind_f061_proposal({
        "schema_version": preflight.F061_ALLOCATION_SCHEMA,
        "allocation_id": "SYNTHETIC-EXACT-COUNTS-V1",
        "mode": "EXACT_COUNTS",
        "values": {"TRAIN": train, "VALIDATION": validation, "TEST": test},
        "denominator": None,
        "minimum_counts": {
            "TRAIN": minimum_train,
            "VALIDATION": minimum_validation,
            "TEST": minimum_test,
        },
        "power_requirement_id": "SYNTHETIC-POWER-REQUIREMENT-V1",
        "power_review_receipt_sha256": _sha("a"),
        "power_review_accepted": True,
    })


def _proportion_allocation(**overrides: object) -> dict:
    value = _shared_policy().retail_allocation()
    value.update(overrides)
    return _bind_f061_proposal(value)


def _row(ordinal: int, customer_id: str, timestamp: int) -> dict:
    return {
        "row_ordinal": ordinal,
        "customer_key_hex": customer_id.encode("ascii").hex(),
        "timestamp_source_civil_microseconds_since_2009_12_01": timestamp,
    }


def _six_rows() -> list[dict]:
    return [_row(index, str(index + 1), (index + 1) * 10) for index in range(6)]


def _cross_split_row_pair_count(
    split_receipt: preflight.RetailSplitReceipt,
) -> int:
    train, validation, test = split_receipt.row_counts
    return train * validation + train * test + validation * test


def test_exact_count_allocation_resolves_and_binds() -> None:
    result = preflight.resolve_f061_allocation(_counts_allocation(), 6)
    assert result["resolved_customer_counts"] == {
        "TRAIN": 4,
        "VALIDATION": 1,
        "TEST": 1,
    }
    assert len(result["allocation_definition_sha256"]) == 64
    assert len(result["resolved_allocation_sha256"]) == 64


@pytest.mark.parametrize(
    ("customer_count", "expected"),
    [
        (6, {"TRAIN": 4, "VALIDATION": 1, "TEST": 1}),
        (10, {"TRAIN": 7, "VALIDATION": 2, "TEST": 1}),
        (20, {"TRAIN": 14, "VALIDATION": 3, "TEST": 3}),
    ],
)
def test_hamilton_proportions_have_exact_fixed_tie_priority(
    customer_count: int, expected: dict
) -> None:
    result = preflight.resolve_f061_allocation(
        _proportion_allocation(), customer_count
    )
    assert result["resolved_customer_counts"] == expected


def test_underpowered_allocation_is_terminal() -> None:
    allocation = _counts_allocation(minimum_test=2)
    with pytest.raises(
        preflight.RetailPreflightError,
        match="F061_UNDERPOWERED_SPLIT:TEST",
    ):
        preflight.resolve_f061_allocation(allocation, 6)


def test_unresolved_power_review_is_terminal() -> None:
    allocation = _counts_allocation()
    allocation["power_review_accepted"] = False
    with pytest.raises(
        preflight.RetailPreflightError,
        match="F061_POWER_REVIEW_UNRESOLVED",
    ):
        preflight.resolve_f061_allocation(allocation, 6)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: value.__setitem__("extra", 1),
        lambda value: value.__setitem__("schema_version", "wrong"),
        lambda value: value.__setitem__("denominator", 1),
        lambda value: value["values"].__setitem__("TRAIN", True),
        lambda value: value["minimum_counts"].__setitem__("TEST", 0),
        lambda value: value.__setitem__("power_review_receipt_sha256", "A" * 64),
    ],
)
def test_exact_count_allocation_rejects_hostile_mutations(mutator) -> None:
    allocation = _counts_allocation()
    mutator(allocation)
    with pytest.raises(preflight.RetailPreflightError):
        preflight.resolve_f061_allocation(allocation, 6)


def test_f061_rejects_equality_lying_schema_version() -> None:
    allocation = _counts_allocation()
    allocation["schema_version"] = _EqualityLyingString("FOREIGN-F061-SCHEMA")
    proposal = {
        key: allocation[key]
        for key in (
            "schema_version",
            "allocation_id",
            "mode",
            "values",
            "denominator",
            "minimum_counts",
            "power_requirement_id",
        )
    }
    allocation["allocation_proposal_sha256"] = preflight._digest(
        preflight._ALLOCATION_PROPOSAL_DOMAIN,
        proposal,
    )
    with pytest.raises(preflight.RetailPreflightError, match="INVALID_F061_SCHEMA"):
        preflight.f061_allocation_proposal_sha256(proposal)
    with pytest.raises(preflight.RetailPreflightError, match="INVALID_F061_SCHEMA"):
        preflight.resolve_f061_allocation(allocation, 6)


def test_count_allocation_must_cover_exact_customer_roster() -> None:
    with pytest.raises(preflight.RetailPreflightError, match="DO_NOT_COVER"):
        preflight.resolve_f061_allocation(_counts_allocation(test=2), 6)


def test_proportions_must_sum_to_denominator() -> None:
    allocation = _proportion_allocation()
    allocation["values"]["TRAIN"] = 69
    _bind_f061_proposal(allocation)
    with pytest.raises(preflight.RetailPreflightError, match="DO_NOT_SUM"):
        preflight.resolve_f061_allocation(allocation, 10)


def test_source_civil_split_has_exact_v2_identity_and_boundaries() -> None:
    result = preflight.split_retail_source_civil_rows(
        _six_rows(), _counts_allocation()
    )
    assert result["schema_version"] == preflight.F060_ASSIGNMENT_SCHEMA
    assert result["rule_id"] == preflight.F060_RULE_ID
    assert result["target_customer_counts"] == {
        "TRAIN": 4,
        "VALIDATION": 1,
        "TEST": 1,
    }
    assert result["observed_customer_counts"] == result["target_customer_counts"]
    assert result["row_counts"] == result["target_customer_counts"]
    assert result["boundary"] == {
        "train_last_timestamp_source_civil_microseconds_since_2009_12_01": 40,
        "validation_first_timestamp_source_civil_microseconds_since_2009_12_01": 50,
        "validation_last_timestamp_source_civil_microseconds_since_2009_12_01": 50,
        "test_first_timestamp_source_civil_microseconds_since_2009_12_01": 60,
    }
    assert result["exclusion_count"] == 0
    assert result["retry_count"] == 0
    assert result["resplit_count"] == 0
    assert result["top_up_count"] == 0
    assert result["source_or_snapshot_opened"] is False


def test_generic_exact_counts_split_cannot_enter_integrated_admission() -> None:
    generic = preflight.split_retail_source_civil_rows(
        _six_rows(),
        _counts_allocation(),
    )
    assert generic["outcome"] == "PASS"
    assert generic["f061_mode"] == "EXACT_COUNTS"

    _, _, snapshot, split, _, _ = _receipt_bundle()
    with pytest.raises(
        preflight.RetailPreflightError,
        match="RETAIL_F061_ADAPTER_PROJECTION_MISMATCH",
    ):
        preflight.RetailSplitReceipt.create(
            snapshot_receipt_sha256=snapshot.receipt_sha256,
            normalized_rows=_six_rows(),
            allocation=_counts_allocation(),
            shared_policy=_shared_policy(),
            split_manifest_private_locator=split.split_manifest_private_locator,
        )
    result = _evaluate(
        _receipt_bundle(),
        replay_allocation=_counts_allocation(),
    )
    assert result["split_replay_status"] == "INTEGRATED_F061_MODE_MISMATCH"
    assert "INTEGRATED_F061_MODE_MISMATCH" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_integrated_split_binds_shared_policy_and_exact_retail_adapter() -> None:
    _, _, _, split, _, _ = _receipt_bundle()
    assert split.f061_mode == preflight.INTEGRATED_F061_MODE
    assert split.shared_policy_definition_sha256 == (
        _shared_policy().allocation_definition_sha256
    )
    assert split.retail_f061_adapter_id == preflight.RETAIL_F061_ADAPTER_ID
    assert split.retail_f061_adapter_sha256 == (
        preflight.RETAIL_F061_ADAPTER_SHA256
    )
    assert preflight.SHARED_F061_POLICY_SCHEMA == (
        "heterodiff-two-domain-f061-shared-policy-v1"
    )
    assert preflight.RETAIL_F061_ADAPTER_ID == (
        "SHARED_POLICY_TO_RETAIL_F061_PROPOSAL_ADAPTER_V1"
    )
    assert preflight.RETAIL_F061_ADAPTER_SHA256 == (
        "c442a1a7ee95078d07852d600f7ea2c35ec52c309b6f97d9cbdba41374f878ee"
    )


def test_active_split_contract_is_frozen_recomputable_and_nonaliased() -> None:
    record = preflight.active_retail_split_contract_record()
    assert preflight.active_retail_split_contract_sha256(record) == (
        preflight.ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256
    )
    assert preflight.ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256 == (
        "b1a4fef836a50987b5d723e2bd133605bd907b4d7904f7cd6e87ca1d83077659"
    )
    assert record["historical_provenance"] == {
        "design_id": preflight.HISTORICAL_RETAIL_SPLIT_DESIGN_ID,
        "design_raw_sha256": (
            preflight.HISTORICAL_RETAIL_SPLIT_DESIGN_RAW_SHA256
        ),
        "legacy_misbound_f105_semantic_sha256": (
            preflight.LEGACY_MISBOUND_F105_SEMANTIC_SHA256
        ),
        "legacy_misbound_digest_is_split_contract": False,
    }
    assert preflight.ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256 not in {
        preflight.HISTORICAL_RETAIL_SPLIT_DESIGN_RAW_SHA256,
        preflight.LEGACY_MISBOUND_F105_SEMANTIC_SHA256,
    }
    mutation = copy.deepcopy(record)
    mutation["allocation"]["integrated_admission_mode"] = "EXACT_COUNTS"
    assert preflight.active_retail_split_contract_sha256(mutation) != (
        preflight.ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256
    )


def test_runtime_active_split_contract_drift_is_fail_closed(monkeypatch) -> None:
    bundle = _receipt_bundle()
    record = preflight.active_retail_split_contract_record()
    record["integrated_receipt_and_replay"][
        "normalized_rows_and_f061_allocation_replayed"
    ] = False
    monkeypatch.setattr(
        preflight,
        "active_retail_split_contract_record",
        lambda: record,
    )
    result = _evaluate(bundle)
    assert "ACTIVE_RETAIL_SPLIT_CONTRACT_RUNTIME_DRIFT" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_unrelated_opaque_shared_policy_digest_cannot_be_laundered() -> None:
    with pytest.raises(
        preflight.RetailPreflightError,
        match="SHARED_F061_DEFINITION_DIGEST_MISMATCH",
    ):
        replace(_shared_policy(), allocation_definition_sha256=_sha("6"))


def test_split_is_input_permutation_invariant() -> None:
    rows = _six_rows()
    forward = preflight.split_retail_source_civil_rows(rows, _counts_allocation())
    reverse = preflight.split_retail_source_civil_rows(
        list(reversed(rows)), _counts_allocation()
    )
    assert reverse == forward


def test_complete_customer_intervals_and_duplicate_rows_are_preserved() -> None:
    rows = [
        _row(0, "1", 10),
        _row(1, "1", 20),
        _row(2, "2", 30),
        _row(3, "3", 40),
        _row(4, "4", 50),
        _row(5, "4", 50),
        _row(6, "5", 60),
        _row(7, "6", 70),
    ]
    result = preflight.split_retail_source_civil_rows(rows, _counts_allocation())
    assignments = {
        item["row_ordinal"]: item["split"]
        for item in result["row_assignments"]
    }
    assert assignments[0] == assignments[1] == "TRAIN"
    assert assignments[4] == assignments[5] == "TRAIN"
    assert sorted(assignments) == list(range(8))
    assert result["row_count"] == 8


def test_no_feasible_boundary_is_terminal_without_fallback() -> None:
    rows = [_row(index, str(index + 1), 10 + (index % 2) * 10) for index in range(6)]
    with pytest.raises(
        preflight.RetailPreflightError,
        match="NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR",
    ):
        preflight.split_retail_source_civil_rows(rows, _counts_allocation())


@pytest.mark.parametrize(
    "rows",
    [
        [{**_six_rows()[0], "timestamp_utc_microseconds": 10}] + _six_rows()[1:],
        [{**_six_rows()[0], "row_ordinal": True}] + _six_rows()[1:],
        [{**_six_rows()[0], "customer_key_hex": "30"}] + _six_rows()[1:],
        [{**_six_rows()[0], "customer_key_hex": "ABCDEF"}] + _six_rows()[1:],
        [
            {
                **_six_rows()[0],
                "timestamp_source_civil_microseconds_since_2009_12_01": (
                    preflight.RETAIL_HORIZON_SOURCE_CIVIL_MICROSECONDS
                ),
            }
        ]
        + _six_rows()[1:],
    ],
)
def test_split_rejects_wrong_carrier_and_malformed_rows(rows) -> None:
    with pytest.raises(preflight.RetailPreflightError):
        preflight.split_retail_source_civil_rows(rows, _counts_allocation())


@pytest.mark.parametrize(
    "identity_field",
    ("schema_version", "rule_id", "domain_id", "slot_id", "outcome"),
)
def test_assignment_projection_rejects_equality_lying_identities(
    identity_field: str,
) -> None:
    result = preflight.split_retail_source_civil_rows(
        _six_rows(),
        _counts_allocation(),
    )
    result[identity_field] = _EqualityLyingString("FOREIGN-F060-IDENTITY")
    manifest_payload = dict(result)
    manifest_payload.pop("assignment_manifest_sha256")
    result["assignment_manifest_sha256"] = preflight._digest(
        preflight._F060_ASSIGNMENT_DOMAIN,
        manifest_payload,
    )
    with pytest.raises(
        preflight.RetailPreflightError,
        match="F060_ASSIGNMENT_IDENTITY_MISMATCH",
    ):
        preflight._validated_assignment_projection(result)


def _receipt_bundle(*, duplicate_count: int = 0, near_count: int = 0):
    schema = preflight.RetailSchemaReceipt.create(
        schema_id="SYNTHETIC-RETAIL-SCHEMA-V1",
        source_schema_sha256=_sha("1"),
    )
    governance = preflight.RetailGovernanceReceipt.create(
        determination_id="SYNTHETIC-GOVERNANCE-DETERMINATION-V1",
        license_access_receipt_sha256=_sha("2"),
        privacy_determination_sha256=_sha("3"),
        retention_controls_receipt_sha256=_sha("4"),
        accountable_owner_acceptance_sha256=_sha("5"),
    )
    assignment = preflight.split_retail_source_civil_rows(
        _six_rows(), _proportion_allocation()
    )
    snapshot = preflight.RetailSnapshotReceipt.create(
        snapshot_version="SYNTHETIC-SNAPSHOT-V1",
        source_version_receipt_sha256=_sha("6"),
        raw_snapshot_sha256=_sha("7"),
        raw_snapshot_bytes=12345,
        archive_inventory_sha256=_sha("8"),
        schema_receipt_sha256=schema.receipt_sha256,
        license_access_receipt_sha256=governance.license_access_receipt_sha256,
        governance_receipt_sha256=governance.receipt_sha256,
        normalized_projection_sha256=assignment["normalized_projection_sha256"],
        normalized_projection_record_count=assignment["row_count"],
        private_locator="private-custody/online-retail-ii/synthetic/snapshot-v1",
    )
    split = preflight.RetailSplitReceipt.create(
        snapshot_receipt_sha256=snapshot.receipt_sha256,
        normalized_rows=_six_rows(),
        allocation=_proportion_allocation(),
        shared_policy=_shared_policy(),
        split_manifest_private_locator=(
            "private-custody/online-retail-ii/synthetic/split-v1"
        ),
    )
    support = preflight.RetailSupportReceipt.create(
        snapshot_receipt_sha256=snapshot.receipt_sha256,
        observation_reference_id="SYNTHETIC-OBSERVATION-REFERENCE-V1",
        observation_reference_sha256=_sha("a"),
        full_support_component_id="SYNTHETIC-FULL-SUPPORT-COMPONENT-V1",
        full_support_component_sha256=_sha("b"),
        mixture_weight_numerator=1,
        mixture_weight_denominator=10,
        support_proof_id="SYNTHETIC-DOMINATED-MIXTURE-PROOF-V1",
        support_proof_sha256=_sha("c"),
        support_implementation_id="SYNTHETIC-SUPPORT-IMPLEMENTATION-V1",
        support_implementation_sha256=_sha("d"),
        support_certificate_id="SYNTHETIC-SUPPORT-CERTIFICATE-V1",
        support_certificate_sha256=_sha("e"),
        acquisition_justification_receipt_sha256=_sha("f"),
        independent_review_receipt_sha256=_sha("0"),
    )
    duplicate = preflight.RetailDuplicateAuditReceipt.create(
        snapshot_receipt_sha256=snapshot.receipt_sha256,
        split_receipt=split,
        audit_id="SYNTHETIC-DUPLICATE-AUDIT-V1",
        audit_implementation_sha256=_sha("9"),
        completion_certificate_sha256=_sha("8"),
        checked_cross_split_row_pair_count=_cross_split_row_pair_count(split),
        complete_roster_checked=True,
        exact_duplicate_cross_split_lineage_count=duplicate_count,
        near_duplicate_cross_split_lineage_count=near_count,
        near_duplicate_rule_id="SYNTHETIC-NEAR-DUPLICATE-RULE-V1",
        model_outcome_or_metric_inspected=False,
        independently_verified=True,
    )
    return schema, governance, snapshot, split, support, duplicate


def _zero_counts() -> preflight.TrainingOnlyViolationCounts:
    return preflight.TrainingOnlyViolationCounts.from_mapping(
        {name: 0 for name in preflight.ADMISSION_COMPONENTS}
    )


def _all_flags(value: bool = True) -> preflight.AdmissionReceiptFlags:
    return preflight.AdmissionReceiptFlags.from_mapping(
        {name: value for name in preflight.REQUIRED_ADMISSION_RECEIPTS}
    )


def _evaluate(
    bundle,
    *,
    counts=None,
    flags=None,
    support_marker=True,
    replay_rows=None,
    replay_allocation=None,
    shared_policy=None,
    include_replay=True,
):
    schema, governance, snapshot, split, support, duplicate = bundle
    return preflight.evaluate_retail_training_admission(
        _zero_counts() if counts is None else counts,
        _all_flags() if flags is None else flags,
        normalized_rows=(
            (_six_rows() if replay_rows is None else replay_rows)
            if include_replay
            else None
        ),
        allocation=(
            (
                _proportion_allocation()
                if replay_allocation is None
                else replay_allocation
            )
            if include_replay
            else None
        ),
        shared_policy=(
            _shared_policy() if shared_policy is None else shared_policy
        ),
        schema_receipt=schema,
        governance_receipt=governance,
        snapshot_receipt=snapshot,
        split_receipt=split,
        support_receipt=support if support_marker else None,
        duplicate_audit_receipt=duplicate,
    )


def _forge_self_consistent_split_receipt(
    receipt: preflight.RetailSplitReceipt,
    **overrides,
) -> preflight.RetailSplitReceipt:
    """Build an internally valid receipt not derived from an F060 replay."""

    values = {
        name: getattr(receipt, name)
        for name in receipt.__dataclass_fields__
    }
    values.update(overrides)
    validation_names = (
        "f060_rule_id",
        "f060_assignment_schema",
        "active_split_contract_id",
        "active_split_contract_sha256",
        "normalized_projection_sha256",
        "rule_input_sha256",
        "f061_mode",
        "shared_policy_definition_sha256",
        "retail_f061_adapter_id",
        "retail_f061_adapter_sha256",
        "allocation_definition_sha256",
        "resolved_allocation_sha256",
        "assignment_manifest_sha256",
        "boundary_sha256",
        "row_count",
        "customer_count",
        "target_customer_counts",
        "observed_customer_counts",
        "row_counts",
    )
    validation_projection = {
        name: values[name]
        for name in validation_names
    }
    values["assignment_validation_receipt_sha256"] = preflight._digest(
        preflight._F060_ASSIGNMENT_VALIDATION_DOMAIN,
        validation_projection,
    )
    receipt_payload = {
        name: value
        for name, value in values.items()
        if name != "receipt_sha256"
    }
    values["receipt_sha256"] = preflight._digest(
        preflight._SPLIT_RECEIPT_DOMAIN,
        receipt_payload,
    )
    return preflight.RetailSplitReceipt(**values)


def _forge_self_consistent_duplicate_audit_receipt(
    receipt: preflight.RetailDuplicateAuditReceipt,
    **overrides,
) -> preflight.RetailDuplicateAuditReceipt:
    """Reseal caller-controlled coverage claims without replaying an audit."""

    values = {
        name: getattr(receipt, name)
        for name in receipt.__dataclass_fields__
    }
    values.update(overrides)
    audit_input = {
        "snapshot_receipt_sha256": values["snapshot_receipt_sha256"],
        "split_receipt_sha256": values["split_receipt_sha256"],
        "audit_algorithm_id": values["audit_algorithm_id"],
        "audit_implementation_sha256": values[
            "audit_implementation_sha256"
        ],
        "audited_normalized_projection_sha256": values[
            "audited_normalized_projection_sha256"
        ],
        "audited_assignment_manifest_sha256": values[
            "audited_assignment_manifest_sha256"
        ],
        "audited_row_count": values["audited_row_count"],
        "audited_customer_count": values["audited_customer_count"],
        "eligible_cross_split_row_pair_count": values[
            "eligible_cross_split_row_pair_count"
        ],
        "near_duplicate_rule_id": values["near_duplicate_rule_id"],
    }
    values["audit_input_manifest_sha256"] = preflight._digest(
        preflight._DUPLICATE_AUDIT_INPUT_DOMAIN,
        audit_input,
    )
    completion = {
        "audit_input_manifest_sha256": values["audit_input_manifest_sha256"],
        "completion_certificate_sha256": values[
            "completion_certificate_sha256"
        ],
        "checked_cross_split_row_pair_count": values[
            "checked_cross_split_row_pair_count"
        ],
        "complete_roster_checked": values["complete_roster_checked"],
        "exact_duplicate_cross_split_lineage_count": values[
            "exact_duplicate_cross_split_lineage_count"
        ],
        "near_duplicate_cross_split_lineage_count": values[
            "near_duplicate_cross_split_lineage_count"
        ],
        "model_outcome_or_metric_inspected": values[
            "model_outcome_or_metric_inspected"
        ],
        "independently_verified": values["independently_verified"],
    }
    values["completion_attestation_sha256"] = preflight._digest(
        preflight._DUPLICATE_AUDIT_COMPLETION_DOMAIN,
        completion,
    )
    receipt_payload = {
        name: value
        for name, value in values.items()
        if name != "receipt_sha256"
    }
    values["receipt_sha256"] = preflight._digest(
        preflight._DUPLICATE_AUDIT_DOMAIN,
        receipt_payload,
    )
    return preflight.RetailDuplicateAuditReceipt(**values)


@pytest.mark.parametrize(
    ("field_name", "foreign_value", "reason"),
    [
        (
            "raw_fields",
            (_EqualityLyingString("FOREIGN-RAW-FIELD"),)
            + preflight.RETAIL_RAW_FIELDS[1:],
            "RETAIL_RAW_FIELD_ROSTER_MISMATCH",
        ),
        (
            "timestamp_semantics",
            _EqualityLyingString("FOREIGN-TIMESTAMP-SEMANTICS"),
            "RETAIL_TIMESTAMP_SEMANTICS_MISMATCH",
        ),
        (
            "unit_price_semantics",
            _EqualityLyingString("FOREIGN-PRICE-SEMANTICS"),
            "RETAIL_UNIT_PRICE_SEMANTICS_MISMATCH",
        ),
    ],
)
def test_schema_receipt_rejects_equality_lying_fixed_strings(
    field_name: str,
    foreign_value,
    reason: str,
) -> None:
    schema, *_ = _receipt_bundle()
    values = _resealed_receipt_values(
        schema,
        preflight._SCHEMA_RECEIPT_DOMAIN,
        **{field_name: foreign_value},
    )
    with pytest.raises(preflight.RetailPreflightError, match=reason):
        preflight.RetailSchemaReceipt(**values)


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("analysis_scope", "INVALID_GOVERNANCE_ANALYSIS_SCOPE"),
        ("approval_state", "GOVERNANCE_APPROVAL_UNRESOLVED"),
    ],
)
def test_governance_receipt_rejects_equality_lying_fixed_strings(
    field_name: str,
    reason: str,
) -> None:
    _, governance, *_ = _receipt_bundle()
    values = _resealed_receipt_values(
        governance,
        preflight._GOVERNANCE_RECEIPT_DOMAIN,
        **{field_name: _EqualityLyingString("FOREIGN-GOVERNANCE-IDENTITY")},
    )
    with pytest.raises(preflight.RetailPreflightError, match=reason):
        preflight.RetailGovernanceReceipt(**values)


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("f060_rule_id", "SPLIT_F060_RULE_ID_MISMATCH"),
        ("f060_assignment_schema", "SPLIT_F060_SCHEMA_MISMATCH"),
        ("f061_mode", "RETAIL_INTEGRATED_F061_MODE_MISMATCH"),
        ("retail_f061_adapter_id", "RETAIL_F061_ADAPTER_ID_MISMATCH"),
        (
            "retail_f061_adapter_sha256",
            "RETAIL_F061_ADAPTER_SHA256_MISMATCH",
        ),
    ],
)
def test_split_receipt_rejects_equality_lying_fixed_strings(
    field_name: str,
    reason: str,
) -> None:
    _, _, _, split, _, _ = _receipt_bundle()
    with pytest.raises(preflight.RetailPreflightError, match=reason):
        _forge_self_consistent_split_receipt(
            split,
            **{field_name: _EqualityLyingString("FOREIGN-SPLIT-IDENTITY")},
        )


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("clean_observation_kernel_id", "OBSERVATION_KERNEL_ID_MISMATCH"),
        ("common_support_policy_id", "UNSELECTED_COMMON_SUPPORT_ROUTE"),
    ],
)
def test_support_receipt_rejects_equality_lying_fixed_strings(
    field_name: str,
    reason: str,
) -> None:
    _, _, _, _, support, _ = _receipt_bundle()
    values = _resealed_receipt_values(
        support,
        preflight._SUPPORT_RECEIPT_DOMAIN,
        **{field_name: _EqualityLyingString("FOREIGN-STRUCTURAL-ZERO-SHORTCUT")},
    )
    with pytest.raises(preflight.RetailPreflightError, match=reason):
        preflight.RetailSupportReceipt(**values)


def test_duplicate_audit_rejects_equality_lying_algorithm_identity() -> None:
    *_, duplicate = _receipt_bundle()
    with pytest.raises(
        preflight.RetailPreflightError,
        match="DUPLICATE_AUDIT_ALGORITHM_ID_MISMATCH",
    ):
        _forge_self_consistent_duplicate_audit_receipt(
            duplicate,
            audit_algorithm_id=_EqualityLyingString("FOREIGN-AUDIT-ALGORITHM"),
        )


@pytest.mark.parametrize(
    "field_name",
    ("clean_observation_kernel_id", "common_support_policy_id"),
)
def test_equality_lying_support_cannot_pass_final_evaluator(
    field_name: str,
) -> None:
    bundle = list(_receipt_bundle())
    support = bundle[4]
    object.__setattr__(
        support,
        field_name,
        _EqualityLyingString("FOREIGN-STRUCTURAL-ZERO-SHORTCUT"),
    )
    object.__setattr__(
        support,
        "receipt_sha256",
        preflight._digest(
            preflight._SUPPORT_RECEIPT_DOMAIN,
            preflight._dataclass_payload(support, ("receipt_sha256",)),
        ),
    )
    assert not preflight._revalidate_exact_dataclass(
        support,
        preflight.RetailSupportReceipt,
    )
    result = _evaluate(tuple(bundle))
    assert result["support_route_status"] == "INVALID"
    assert "SUPPORT_RECEIPT_MISSING_OR_INVALID" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_receipts_are_frozen_self_digesting_and_crosslinkable() -> None:
    bundle = _receipt_bundle()
    for receipt in bundle:
        assert len(receipt.receipt_sha256) == 64
        with pytest.raises(FrozenInstanceError):
            receipt.receipt_sha256 = _sha("0")


def test_schema_and_snapshot_enforce_source_civil_and_private_custody() -> None:
    schema, _, snapshot, _, _, _ = _receipt_bundle()
    assert (
        schema.timestamp_semantics
        == "SOURCE_CIVIL_SEVEN_TUPLE_NO_TIMEZONE_OR_INSTANT"
    )
    assert snapshot.private_locator.startswith("private-custody/online-retail-ii/")
    with pytest.raises(preflight.RetailPreflightError, match="private locator"):
        preflight.RetailSnapshotReceipt.create(
            snapshot_version="SYNTHETIC-SNAPSHOT-V1",
            source_version_receipt_sha256=_sha("1"),
            raw_snapshot_sha256=_sha("2"),
            raw_snapshot_bytes=1,
            archive_inventory_sha256=_sha("3"),
            schema_receipt_sha256=_sha("4"),
            license_access_receipt_sha256=_sha("5"),
            governance_receipt_sha256=_sha("6"),
            normalized_projection_sha256=_sha("7"),
            normalized_projection_record_count=1,
            private_locator="/tmp/public.xlsx",
        )


@pytest.mark.parametrize("bad_size", [0, -1, True])
def test_snapshot_rejects_invalid_exact_byte_count(bad_size) -> None:
    _, _, snapshot, _, _, _ = _receipt_bundle()
    values = {
        name: getattr(snapshot, name)
        for name in (
            "snapshot_version",
            "source_version_receipt_sha256",
            "raw_snapshot_sha256",
            "archive_inventory_sha256",
            "schema_receipt_sha256",
            "license_access_receipt_sha256",
            "governance_receipt_sha256",
            "normalized_projection_sha256",
            "normalized_projection_record_count",
            "private_locator",
            "post_snapshot_exclusion_count",
            "retry_resplit_topup_count",
        )
    }
    values["raw_snapshot_bytes"] = bad_size
    with pytest.raises(preflight.RetailPreflightError):
        preflight.RetailSnapshotReceipt.create(**values)


def test_receipt_digest_tampering_is_rejected() -> None:
    schema, *_ = _receipt_bundle()
    with pytest.raises(preflight.RetailPreflightError, match="DIGEST_MISMATCH"):
        replace(schema, receipt_sha256=_sha("0"))


@pytest.mark.parametrize(
    ("receipt_index", "field_name", "bad_value", "reason"),
    [
        (1, "approval_state", "PENDING", "GOVERNANCE_RECEIPT_MISSING_OR_INVALID"),
        (3, "f060_rule_id", "FOREIGN-RULE", "SPLIT_RECEIPT_MISSING_OR_INVALID"),
        (4, "clean_kernel_kept_separate", False, "SUPPORT_RECEIPT_MISSING_OR_INVALID"),
    ],
)
def test_post_construction_receipt_mutation_cannot_bypass_admission(
    receipt_index: int,
    field_name: str,
    bad_value,
    reason: str,
) -> None:
    bundle = list(_receipt_bundle())
    object.__setattr__(bundle[receipt_index], field_name, bad_value)
    result = _evaluate(tuple(bundle))
    assert result["decision"] == "NO_GO"
    assert reason in result["reasons"]


def test_split_receipt_recomputes_exact_f060_output() -> None:
    _, _, snapshot, _, _, _ = _receipt_bundle()
    rows = _six_rows()
    rows[0]["timestamp_source_civil_microseconds_since_2009_12_01"] = True
    with pytest.raises(preflight.RetailPreflightError):
        preflight.RetailSplitReceipt.create(
            snapshot_receipt_sha256=snapshot.receipt_sha256,
            normalized_rows=rows,
            allocation=_proportion_allocation(),
            shared_policy=_shared_policy(),
            split_manifest_private_locator=(
                "private-custody/online-retail-ii/synthetic/split-v1"
            ),
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"assignment_manifest_sha256": _sha("1")},
        {"rule_input_sha256": _sha("2")},
        {"allocation_definition_sha256": _sha("3")},
        {"resolved_allocation_sha256": _sha("4")},
        {"boundary_sha256": _sha("5")},
        {"shared_policy_definition_sha256": _sha("7")},
        {
            "target_customer_counts": (3, 2, 1),
            "observed_customer_counts": (3, 2, 1),
        },
    ],
)
def test_self_consistent_direct_constructor_forgery_fails_exact_replay(
    overrides,
) -> None:
    schema, governance, snapshot, split, support, duplicate = _receipt_bundle()
    forged_split = _forge_self_consistent_split_receipt(split, **overrides)
    assert preflight._revalidate_exact_dataclass(
        forged_split,
        preflight.RetailSplitReceipt,
    )
    rebound_duplicate = preflight.RetailDuplicateAuditReceipt.create(
        snapshot_receipt_sha256=snapshot.receipt_sha256,
        split_receipt=forged_split,
        audit_id=duplicate.audit_id,
        audit_implementation_sha256=duplicate.audit_implementation_sha256,
        completion_certificate_sha256=duplicate.completion_certificate_sha256,
        checked_cross_split_row_pair_count=(
            _cross_split_row_pair_count(forged_split)
        ),
        complete_roster_checked=True,
        exact_duplicate_cross_split_lineage_count=0,
        near_duplicate_cross_split_lineage_count=0,
        near_duplicate_rule_id=duplicate.near_duplicate_rule_id,
        model_outcome_or_metric_inspected=False,
        independently_verified=True,
    )
    result = _evaluate(
        (
            schema,
            governance,
            snapshot,
            forged_split,
            support,
            rebound_duplicate,
        )
    )
    assert result["split_replay_status"] == "MISMATCH"
    assert "SPLIT_RECEIPT_REPLAY_MISMATCH" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_changed_normalized_rows_cannot_reuse_an_old_split_receipt() -> None:
    rows = _six_rows()
    rows[0]["timestamp_source_civil_microseconds_since_2009_12_01"] = 11
    result = _evaluate(_receipt_bundle(), replay_rows=rows)
    assert result["split_replay_status"] == "MISMATCH"
    assert "SPLIT_RECEIPT_REPLAY_MISMATCH" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_changed_f061_review_cannot_reuse_an_old_split_receipt() -> None:
    allocation = _proportion_allocation()
    allocation["power_review_receipt_sha256"] = _sha("c")
    result = _evaluate(_receipt_bundle(), replay_allocation=allocation)
    assert result["split_replay_status"] == (
        "RETAIL_F061_ADAPTER_PROJECTION_MISMATCH"
    )
    assert "RETAIL_F061_ADAPTER_PROJECTION_MISMATCH" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_shared_policy_definition_drift_fails_crosslink_and_replay() -> None:
    foreign_policy = _shared_policy(
        allocation_id="SYNTHETIC-HAMILTON-60-20-20-V1",
        values=(60, 20, 20),
    )
    result = _evaluate(
        _receipt_bundle(),
        shared_policy=foreign_policy,
    )
    assert result["split_replay_status"] == (
        "RETAIL_F061_ADAPTER_PROJECTION_MISMATCH"
    )
    assert "RETAIL_F061_ADAPTER_PROJECTION_MISMATCH" in result["reasons"]
    assert result["decision"] == "NO_GO"


@pytest.mark.parametrize(
    ("adapter_id", "adapter_sha256"),
    [
        ("FOREIGN-RETAIL-F061-ADAPTER", preflight.RETAIL_F061_ADAPTER_SHA256),
        (preflight.RETAIL_F061_ADAPTER_ID, _sha("7")),
    ],
)
def test_retail_adapter_drift_is_no_go(
    adapter_id: str,
    adapter_sha256: str,
) -> None:
    policy = _shared_policy()
    object.__setattr__(policy, "retail_adapter_id", adapter_id)
    object.__setattr__(policy, "retail_adapter_sha256", adapter_sha256)
    result = _evaluate(
        _receipt_bundle(),
        shared_policy=policy,
    )
    assert result["split_replay_status"] == (
        "INTEGRATED_F061_PROVENANCE_INVALID"
    )
    assert "INTEGRATED_F061_PROVENANCE_MISSING_OR_INVALID" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_missing_integrated_f061_provenance_is_no_go() -> None:
    schema, governance, snapshot, split, support, duplicate = _receipt_bundle()
    result = preflight.evaluate_retail_training_admission(
        _zero_counts(),
        _all_flags(),
        normalized_rows=_six_rows(),
        allocation=_proportion_allocation(),
        schema_receipt=schema,
        governance_receipt=governance,
        snapshot_receipt=snapshot,
        split_receipt=split,
        support_receipt=support,
        duplicate_audit_receipt=duplicate,
    )
    assert result["split_replay_status"] == (
        "INTEGRATED_F061_PROVENANCE_INVALID"
    )
    assert "INTEGRATED_F061_PROVENANCE_MISSING_OR_INVALID" in result["reasons"]
    assert result["decision"] == "NO_GO"


@pytest.mark.parametrize(
    ("rows", "allocation"),
    [
        (None, _proportion_allocation()),
        (_six_rows(), None),
        ([], _proportion_allocation()),
        ([{"row_ordinal": 0}], _proportion_allocation()),
    ],
)
def test_missing_or_invalid_replay_evidence_is_no_go(rows, allocation) -> None:
    schema, governance, snapshot, split, support, duplicate = _receipt_bundle()
    result = preflight.evaluate_retail_training_admission(
        _zero_counts(),
        _all_flags(),
        normalized_rows=rows,
        allocation=allocation,
        shared_policy=_shared_policy(),
        schema_receipt=schema,
        governance_receipt=governance,
        snapshot_receipt=snapshot,
        split_receipt=split,
        support_receipt=support,
        duplicate_audit_receipt=duplicate,
    )
    assert result["split_replay_status"] == "MISSING_OR_INVALID"
    assert "SPLIT_REPLAY_INPUTS_MISSING_OR_INVALID" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_omitted_replay_evidence_is_no_go() -> None:
    result = _evaluate(_receipt_bundle(), include_replay=False)
    assert result["split_replay_status"] == "MISSING_OR_INVALID"
    assert "SPLIT_REPLAY_INPUTS_MISSING_OR_INVALID" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_support_is_explicitly_unresolved_when_absent() -> None:
    assert preflight.support_route_status(None) == "UNRESOLVED"
    result = _evaluate(_receipt_bundle(), support_marker=False)
    assert result["decision"] == "NO_GO"
    assert result["support_route_status"] == "UNRESOLVED"
    assert "COMMON_SUPPORT_POLICY_RECEIPT_UNRESOLVED" in result["reasons"]


@pytest.mark.parametrize(
    "override",
    [
        {"full_support_component_id": "PENDING"},
        {"support_certificate_id": "UNRESOLVED"},
        {"theorem_convenience_noise_added": True},
        {"clean_kernel_kept_separate": False},
        {"mixture_weight_numerator": 10},
        {"acquisition_justification_receipt_sha256": "0"},
    ],
)
def test_support_receipt_rejects_placeholders_noise_and_bad_justification(
    override,
) -> None:
    _, _, snapshot, _, _, _ = _receipt_bundle()
    values = {
        "snapshot_receipt_sha256": snapshot.receipt_sha256,
        "observation_reference_id": "SYNTHETIC-OBSERVATION-REFERENCE-V1",
        "observation_reference_sha256": _sha("1"),
        "full_support_component_id": "SYNTHETIC-FULL-SUPPORT-COMPONENT-V1",
        "full_support_component_sha256": _sha("2"),
        "mixture_weight_numerator": 1,
        "mixture_weight_denominator": 10,
        "support_proof_id": "SYNTHETIC-DOMINATED-MIXTURE-PROOF-V1",
        "support_proof_sha256": _sha("3"),
        "support_implementation_id": "SYNTHETIC-SUPPORT-IMPLEMENTATION-V1",
        "support_implementation_sha256": _sha("4"),
        "support_certificate_id": "SYNTHETIC-SUPPORT-CERTIFICATE-V1",
        "support_certificate_sha256": _sha("5"),
        "acquisition_justification_receipt_sha256": _sha("6"),
        "independent_review_receipt_sha256": _sha("7"),
    }
    values.update(override)
    with pytest.raises(preflight.RetailPreflightError):
        preflight.RetailSupportReceipt.create(**values)


def test_exact_zero_vector_and_six_receipts_are_only_structurally_eligible() -> None:
    result = _evaluate(_receipt_bundle())
    assert result["maximum_hard_violation_count"] == 0
    assert result["nonzero_components"] == []
    assert result["missing_or_false_receipt_flags"] == []
    assert result["split_replay_status"] == "MATCHED"
    assert result["decision"] == "ELIGIBLE_FOR_INDEPENDENT_ADMISSION"
    assert result["domain_admitted"] is False
    assert result["independent_admission_required"] is True
    assert result["external_authentication_performed"] is False
    assert result["source_or_data_access_performed"] is False


def test_any_nonzero_training_only_component_is_no_go() -> None:
    counts = {name: 0 for name in preflight.ADMISSION_COMPONENTS}
    counts["identity_failures"] = 1
    result = _evaluate(
        _receipt_bundle(),
        counts=preflight.TrainingOnlyViolationCounts.from_mapping(counts),
    )
    assert result["maximum_hard_violation_count"] == 1
    assert result["nonzero_components"] == ["identity_failures"]
    assert result["decision"] == "NO_GO"


def test_any_false_receipt_flag_is_no_go() -> None:
    flags = {name: True for name in preflight.REQUIRED_ADMISSION_RECEIPTS}
    flags["governance_approval_verified"] = False
    result = _evaluate(
        _receipt_bundle(),
        flags=preflight.AdmissionReceiptFlags.from_mapping(flags),
    )
    assert result["missing_or_false_receipt_flags"] == [
        "governance_approval_verified"
    ]
    assert result["decision"] == "NO_GO"


@pytest.mark.parametrize(("exact_count", "near_count"), [(1, 0), (0, 1), (2, 3)])
def test_cross_split_duplicate_or_near_duplicate_lineage_is_no_go(
    exact_count: int, near_count: int
) -> None:
    result = _evaluate(
        _receipt_bundle(duplicate_count=exact_count, near_count=near_count)
    )
    assert "CROSS_SPLIT_DUPLICATE_OR_NEAR_DUPLICATE_LINEAGE" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_duplicate_audit_binds_exact_split_roster_algorithm_and_certificate() -> None:
    *_, split, _, duplicate = _receipt_bundle()
    assert duplicate.audit_algorithm_id == preflight.DUPLICATE_AUDIT_ALGORITHM_ID
    assert duplicate.audited_normalized_projection_sha256 == (
        split.normalized_projection_sha256
    )
    assert duplicate.audited_assignment_manifest_sha256 == (
        split.assignment_manifest_sha256
    )
    assert duplicate.audited_row_count == split.row_count
    assert duplicate.audited_customer_count == split.customer_count
    assert duplicate.eligible_cross_split_row_pair_count == (
        _cross_split_row_pair_count(split)
    )
    assert duplicate.checked_cross_split_row_pair_count == (
        duplicate.eligible_cross_split_row_pair_count
    )
    assert duplicate.complete_roster_checked is True
    assert len(duplicate.audit_input_manifest_sha256) == 64
    assert len(duplicate.completion_certificate_sha256) == 64
    assert len(duplicate.completion_attestation_sha256) == 64


def test_partial_zero_pair_duplicate_audit_is_no_go() -> None:
    schema, governance, snapshot, split, support, _ = _receipt_bundle()
    partial = preflight.RetailDuplicateAuditReceipt.create(
        snapshot_receipt_sha256=snapshot.receipt_sha256,
        split_receipt=split,
        audit_id="SYNTHETIC-PARTIAL-DUPLICATE-AUDIT-V1",
        audit_implementation_sha256=_sha("9"),
        completion_certificate_sha256=_sha("8"),
        checked_cross_split_row_pair_count=0,
        complete_roster_checked=False,
        exact_duplicate_cross_split_lineage_count=0,
        near_duplicate_cross_split_lineage_count=0,
        near_duplicate_rule_id="SYNTHETIC-NEAR-DUPLICATE-RULE-V1",
        model_outcome_or_metric_inspected=False,
        independently_verified=True,
    )
    result = _evaluate(
        (schema, governance, snapshot, split, support, partial)
    )
    assert "DUPLICATE_AUDIT_COVERAGE_MISMATCH" in result["reasons"]
    assert "DUPLICATE_AUDIT_ROSTER_INCOMPLETE" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_false_complete_zero_pair_attestation_is_rejected() -> None:
    *_, snapshot, split, _, _ = _receipt_bundle()
    with pytest.raises(
        preflight.RetailPreflightError,
        match="FALSE_COMPLETION_ATTESTATION",
    ):
        preflight.RetailDuplicateAuditReceipt.create(
            snapshot_receipt_sha256=snapshot.receipt_sha256,
            split_receipt=split,
            audit_id="SYNTHETIC-FALSE-COMPLETE-AUDIT-V1",
            audit_implementation_sha256=_sha("9"),
            completion_certificate_sha256=_sha("8"),
            checked_cross_split_row_pair_count=0,
            complete_roster_checked=True,
            exact_duplicate_cross_split_lineage_count=0,
            near_duplicate_cross_split_lineage_count=0,
            near_duplicate_rule_id="SYNTHETIC-NEAR-DUPLICATE-RULE-V1",
            model_outcome_or_metric_inspected=False,
            independently_verified=True,
        )


def test_self_consistent_forged_duplicate_coverage_is_no_go() -> None:
    bundle = list(_receipt_bundle())
    forged = _forge_self_consistent_duplicate_audit_receipt(
        bundle[5],
        eligible_cross_split_row_pair_count=1,
        checked_cross_split_row_pair_count=1,
        complete_roster_checked=True,
    )
    assert preflight._revalidate_exact_dataclass(
        forged,
        preflight.RetailDuplicateAuditReceipt,
    )
    bundle[5] = forged
    result = _evaluate(tuple(bundle))
    assert "DUPLICATE_AUDIT_COVERAGE_MISMATCH" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_crosslink_mismatch_is_no_go() -> None:
    schema, governance, snapshot, split, support, duplicate = _receipt_bundle()
    foreign_split = preflight.RetailSplitReceipt.create(
        snapshot_receipt_sha256=_sha("0"),
        normalized_rows=_six_rows(),
        allocation=_proportion_allocation(),
        shared_policy=_shared_policy(),
        split_manifest_private_locator=split.split_manifest_private_locator,
    )
    foreign_duplicate = preflight.RetailDuplicateAuditReceipt.create(
        snapshot_receipt_sha256=snapshot.receipt_sha256,
        split_receipt=foreign_split,
        audit_id=duplicate.audit_id,
        audit_implementation_sha256=duplicate.audit_implementation_sha256,
        completion_certificate_sha256=duplicate.completion_certificate_sha256,
        checked_cross_split_row_pair_count=(
            _cross_split_row_pair_count(foreign_split)
        ),
        complete_roster_checked=True,
        exact_duplicate_cross_split_lineage_count=0,
        near_duplicate_cross_split_lineage_count=0,
        near_duplicate_rule_id=duplicate.near_duplicate_rule_id,
        model_outcome_or_metric_inspected=False,
        independently_verified=True,
    )
    result = preflight.evaluate_retail_training_admission(
        _zero_counts(),
        _all_flags(),
        normalized_rows=_six_rows(),
        allocation=_proportion_allocation(),
        shared_policy=_shared_policy(),
        schema_receipt=schema,
        governance_receipt=governance,
        snapshot_receipt=snapshot,
        split_receipt=foreign_split,
        support_receipt=support,
        duplicate_audit_receipt=foreign_duplicate,
    )
    assert "SPLIT_SNAPSHOT_CROSSLINK_MISMATCH" in result["reasons"]
    assert result["decision"] == "NO_GO"


def test_vectors_reject_missing_extra_and_boolean_values() -> None:
    counts = {name: 0 for name in preflight.ADMISSION_COMPONENTS}
    missing = dict(counts)
    missing.pop("observation_subset_failures")
    extra = {**counts, "extra": 0}
    boolean = dict(counts)
    boolean["raw_format_failures"] = False
    for candidate in (missing, extra, boolean):
        with pytest.raises(preflight.RetailPreflightError):
            preflight.TrainingOnlyViolationCounts.from_mapping(candidate)
    reordered = dict(reversed(list(counts.items())))
    assert (
        preflight.TrainingOnlyViolationCounts.from_mapping(reordered).as_dict()
        == counts
    )


def test_admission_rejects_equality_compatible_subclasses() -> None:
    class Counts(preflight.TrainingOnlyViolationCounts):
        pass

    values = {name: 0 for name in preflight.ADMISSION_COMPONENTS}
    impostor = Counts(**values)
    with pytest.raises(preflight.RetailPreflightError, match="VECTOR_TYPE"):
        preflight.evaluate_retail_training_admission(impostor, _all_flags())


def test_source_has_no_effectful_or_noise_synthesis_surface() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported = set()
    called_names = set()
    float_constants = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            called_names.add(node.func.id)
        elif isinstance(node, ast.Constant) and type(node.value) is float:
            float_constants.append(node.value)
    assert imported.isdisjoint(
        {
            "os",
            "pathlib",
            "socket",
            "ssl",
            "subprocess",
            "urllib",
            "requests",
            "httpx",
            "openpyxl",
            "pandas",
            "random",
            "secrets",
        }
    )
    assert called_names.isdisjoint(
        {"open", "exec", "eval", "compile", "input", "__import__"}
    )
    assert float_constants == []
    source_text = SOURCE.read_text(encoding="utf-8")
    assert "timestamp_utc_microseconds" not in source_text
    assert "THEOREM_CONVENIENCE_NOISE_FORBIDDEN" in source_text
    assert "source_or_data_access_performed" in source_text


def test_public_api_is_closed_and_explicit() -> None:
    assert preflight.__all__ == (
        "ACTIVE_RETAIL_SPLIT_CONTRACT_ID",
        "ACTIVE_RETAIL_SPLIT_CONTRACT_SHA256",
        "ADMISSION_COMPONENTS",
        "AdmissionReceiptFlags",
        "COMMON_SUPPORT_POLICY_ID",
        "DOMAIN_ID",
        "DUPLICATE_AUDIT_ALGORITHM_ID",
        "F060_ASSIGNMENT_SCHEMA",
        "F060_RULE_ID",
        "F061_ALLOCATION_SCHEMA",
        "HISTORICAL_RETAIL_SPLIT_DESIGN_ID",
        "HISTORICAL_RETAIL_SPLIT_DESIGN_RAW_SHA256",
        "INTEGRATED_F061_MODE",
        "LEGACY_MISBOUND_F105_SEMANTIC_SHA256",
        "OBSERVATION_KERNEL_ID",
        "REQUIRED_ADMISSION_RECEIPTS",
        "RETAIL_HORIZON_SOURCE_CIVIL_MICROSECONDS",
        "RETAIL_F061_ADAPTER_ID",
        "RETAIL_F061_ADAPTER_SHA256",
        "RETAIL_RAW_FIELDS",
        "RetailDuplicateAuditReceipt",
        "RetailGovernanceReceipt",
        "RetailPreflightError",
        "RetailSchemaReceipt",
        "RetailSharedF061Policy",
        "RetailSnapshotReceipt",
        "RetailSplitReceipt",
        "RetailSupportReceipt",
        "SLOT_ID",
        "SHARED_F061_POLICY_SCHEMA",
        "SHARED_F061_HAMILTON_ROUNDING_RULE_ID",
        "SPLITS",
        "TrainingOnlyViolationCounts",
        "active_retail_split_contract_record",
        "active_retail_split_contract_sha256",
        "evaluate_retail_training_admission",
        "f061_allocation_proposal_sha256",
        "resolve_f061_allocation",
        "retail_f061_adapter_record",
        "retail_f061_adapter_sha256",
        "split_retail_source_civil_rows",
        "support_route_status",
    )
