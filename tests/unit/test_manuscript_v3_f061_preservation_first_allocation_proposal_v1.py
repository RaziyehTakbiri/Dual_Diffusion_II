from __future__ import annotations

import ast
import copy
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
from typing import Any, Dict

import pytest

from heterodiff.data import online_retail_ii_admission_preflight as retail
from heterodiff.data import physionet_2012_admission_preflight as physionet
from heterodiff.data import two_domain_f061_preservation_first_successor as successor
from heterodiff.data import two_domain_offline_precontact_activation as activation


ROOT = Path(__file__).resolve().parents[2]
SOURCE_REL = Path(
    "src/heterodiff/data/two_domain_f061_preservation_first_successor.py"
)
MACHINE_REL = Path(
    "research/fixtures/"
    "manuscript_v3_f061_preservation_first_allocation_proposal_v1.json"
)
VALIDATOR_REL = Path(
    "research/diagnostics/"
    "manuscript_v3_f061_preservation_first_allocation_proposal_v1.py"
)


def _load_validator() -> Any:
    spec = importlib.util.spec_from_file_location(
        "f061_preservation_first_validator",
        ROOT / VALIDATOR_REL,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = _load_validator()


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _proposal_bindings_draft() -> activation.OfflineDefinitionBindings:
    return replace(
        activation.unresolved_definition_bindings(),
        f061_allocation_id=successor.ALLOCATION_ID,
        f061_mode=successor.MODE,
        f061_values=successor.VALUES,
        f061_denominator_is_null=successor.DENOMINATOR_IS_NULL,
        f061_denominator=successor.DENOMINATOR,
        f061_minimum_counts=successor.MINIMUM_COUNTS,
        f061_rounding_rule_id=successor.ROUNDING_RULE_ID,
        f061_power_requirement_id=successor.POWER_REQUIREMENT_ID,
    )


def _guarded_review_receipt_mapping(
    *, reviewer: str = "synthetic-independent-test-reviewer"
) -> Dict[str, Any]:
    receipt = {
        "schema_version": successor.GUARDED_REVIEW_SCHEMA,
        "review_scope": successor.GUARDED_REVIEW_SCOPE,
        "review_kind": "INDEPENDENT_TECHNICAL_STATISTICAL_POLICY_REVIEW",
        "decision": "ACCEPT_GUARDED_SHARED_POLICY",
        "accepted": True,
        "independent_reviewer_principal_id": reviewer,
        "independent_reviewer_attestation_sha256": "0" * 64,
        "shared_policy_proposal_sha256": successor.PROPOSAL_SHA256,
        "exact_count_guard_contract_sha256": successor.GUARD_CONTRACT_SHA256,
        "successor_source_path": successor.SUCCESSOR_SOURCE_PATH,
        "successor_source_raw_sha256": _digest("synthetic-test-source-bytes"),
        "successor_human_path": successor.SUCCESSOR_HUMAN_PATH,
        "successor_human_raw_sha256": _digest("synthetic-test-human-bytes"),
        "successor_machine_path": successor.SUCCESSOR_MACHINE_PATH,
        "successor_machine_raw_sha256": _digest("synthetic-test-machine-bytes"),
        "successor_machine_record_sha256": _digest(
            "synthetic-test-machine-semantic-record"
        ),
        "successor_package_aggregate_sha256": _digest(
            "synthetic-test-package-aggregate"
        ),
        "source_and_package_hashes_reopened_before_decision": True,
        "sole_supported_projection_resolution_entrypoints": list(
            successor.SOLE_SUPPORTED_ENTRYPOINTS
        ),
        "direct_generic_predecessor_entrypoints_supported": False,
        "reviewer_independence_and_conflict_checked": True,
        "institutional_operational_or_governance_approval": False,
        "reviewer_identity_externally_authenticated": False,
    }
    projection = dict(receipt)
    projection.pop("independent_reviewer_attestation_sha256")
    raw = json.dumps(
        projection,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    receipt["independent_reviewer_attestation_sha256"] = hashlib.sha256(
        b"heterodiff/two-domain-f061-guarded-power-reviewer-attestation/v1\0"
        + raw
    ).hexdigest()
    return receipt


def _guarded_review_receipt(
    *, reviewer: str = "synthetic-independent-test-reviewer"
) -> bytes:
    return json.dumps(
        _guarded_review_receipt_mapping(reviewer=reviewer),
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _reviewed_complete_bindings(
    receipt: bytes | None = None,
) -> activation.OfflineDefinitionBindings:
    """Synthetic-only carrier for exercising future review-validation code."""

    guarded_receipt = receipt or _guarded_review_receipt()
    draft = replace(
        _proposal_bindings_draft(),
        physionet_selector_record_sha256=_digest("test-physionet-selector"),
        retail_selector_record_sha256=_digest("test-retail-selector"),
        f061_power_review_receipt_sha256=(
            successor.guarded_power_review_receipt_sha256(guarded_receipt)
        ),
        f061_power_review_accepted=True,
        contact_target_roster_sha256=_digest("test-contact-roster"),
        contact_target_count=4,
        approval_requirement_roster_sha256=_digest("test-approval-roster"),
        approval_receipt_validator_roster_sha256=_digest(
            "test-approval-validator-roster"
        ),
        conflict_of_interest_determination_sha256=_digest("test-coi"),
        contact_roster_complete=True,
        escrow_control_binding_sha256=_digest("test-escrow-control"),
        held_out_material_definition_sha256=_digest("test-heldout-definition"),
        final_opening_rule_sha256=_digest("test-final-opening"),
        append_only_log_schema_sha256=_digest("test-append-only-schema"),
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


def _retail_shared_policy(
    receipt: bytes | None = None,
) -> retail.RetailSharedF061Policy:
    guarded_receipt = receipt or _guarded_review_receipt()
    return retail.RetailSharedF061Policy.create(
        allocation_id=successor.ALLOCATION_ID,
        values=successor.VALUES,
        denominator=successor.DENOMINATOR,
        minimum_counts=successor.MINIMUM_COUNTS,
        power_requirement_id=successor.POWER_REQUIREMENT_ID,
        power_review_receipt_sha256=(
            successor.guarded_power_review_receipt_sha256(guarded_receipt)
        ),
        power_review_accepted=True,
    )


def _reason(callable_: Any, *args: Any) -> str:
    with pytest.raises(successor.F061SuccessorError) as caught:
        callable_(*args)
    return caught.value.reason_code


def test_exact_proposal_and_known_answer_are_frozen() -> None:
    assert successor.ALLOCATION_ID == (
        "TWO_DOMAIN_F061_HAMILTON_70_15_15_EXACT_128_VALIDATION_TEST_V1"
    )
    assert successor.MODE == "EXACT_PROPORTIONS_HAMILTON"
    assert successor.VALUES == (70, 15, 15)
    assert successor.DENOMINATOR_IS_NULL is False
    assert successor.DENOMINATOR == 100
    assert successor.MINIMUM_COUNTS == (1, 128, 128)
    assert successor.ROUNDING_RULE_ID == (
        "HAMILTON_DESCENDING_INTEGER_REMAINDER_TIE_TRAIN_VALIDATION_TEST_V1"
    )
    assert successor.POWER_REQUIREMENT_ID == (
        "B07_F134_EXACT_128_VALIDATION_AND_TEST_GROUPS_NO_EXCLUSION_V1"
    )
    proposal = successor.recognized_proposal()
    assert successor.recognized_proposal_sha256(proposal) == (
        "cf26d91eb850990d3fb179c376ab27ca12d0ff0de490f2ee4a5c6020fe66c679"
    )


def test_all_three_accepted_codecs_agree_on_shared_proposal_digest() -> None:
    draft = _proposal_bindings_draft()
    core_digest = activation.f061_allocation_proposal_sha256(draft)
    physionet_digest = physionet.shared_f061_policy_proposal_sha256(
        allocation_id=successor.ALLOCATION_ID,
        values=successor.VALUES,
        denominator=successor.DENOMINATOR,
        minimum_counts=successor.MINIMUM_COUNTS,
        rounding_rule_id=successor.ROUNDING_RULE_ID,
        power_requirement_id=successor.POWER_REQUIREMENT_ID,
    )
    retail_digest = _retail_shared_policy().allocation_proposal_sha256
    assert core_digest == physionet_digest == retail_digest
    assert core_digest == successor.PROPOSAL_SHA256


def test_proposal_only_status_keeps_review_definition_and_f061_open() -> None:
    status = successor.proposal_only_status()
    assert status["state"] == (
        "F061_PROPOSAL_FROZEN_AWAITING_SEPARATE_INDEPENDENT_POWER_REVIEW"
    )
    assert status["f061_field_status"] == "OPEN"
    assert status["power_review_receipt_sha256"] is None
    assert status["power_review_accepted"] is None
    assert status["allocation_definition_sha256"] is None
    assert status["exact_count_guard_contract_sha256"] == (
        successor.GUARD_CONTRACT_SHA256
    )
    assert status["future_power_review_must_byte_bind_successor_package"] is True
    assert status["direct_generic_predecessor_entrypoints_supported"] is False
    assert status["independent_review_created_by_module"] is False
    assert status["tracker_or_evidence_ledger_edited"] is False


def test_exact_count_guard_contract_known_answer_and_supported_entrypoints() -> None:
    contract = successor.exact_count_guard_contract()
    assert successor.exact_count_guard_contract_sha256() == (
        "98a9ec44fb76b08285ac86e63e4fbb3db3b6b232f16a12b436f3d9f8283b3fef"
    )
    assert contract["required_exact_counts"] == {
        "VALIDATION": 128,
        "TEST": 128,
    }
    assert contract["all_natural_groups_must_be_allocated"] is True
    assert contract[
        "exclusion_topup_retry_resplit_or_proportion_change_permitted"
    ] is False
    assert contract[
        "direct_generic_predecessor_projection_or_resolution_supported_for_this_policy"
    ] is False
    assert tuple(contract["sole_supported_projection_resolution_entrypoints"]) == (
        successor.SOLE_SUPPORTED_ENTRYPOINTS
    )
    assert contract["guarded_review_receipt_carrier"] == (
        "CANONICAL_DUPLICATE_FREE_ASCII_JSON_NO_TERMINAL_LF"
    )
    assert contract["reviewer_attestation_domain_ascii"] == (
        "heterodiff/two-domain-f061-guarded-power-reviewer-attestation/v1"
    )
    assert contract["reviewer_attestation_domain_suffix_hex"] == "00"
    assert contract["reviewer_attestation_is_identity_signature"] is False
    assert contract["independent_custody_reopens_actual_candidate_bytes"] is True
    assert contract["source_self_pins_own_raw_sha256"] is False


def test_guarded_review_receipt_binds_proposal_guard_source_machine_and_package() -> None:
    receipt_raw = _guarded_review_receipt()
    receipt = _guarded_review_receipt_mapping()
    assert successor.validate_guarded_power_review_receipt(receipt_raw) == receipt
    digest = successor.guarded_power_review_receipt_sha256(receipt_raw)
    assert len(digest) == 64
    for field in (
        "shared_policy_proposal_sha256",
        "exact_count_guard_contract_sha256",
        "successor_source_raw_sha256",
        "successor_human_raw_sha256",
        "successor_machine_raw_sha256",
        "successor_machine_record_sha256",
        "successor_package_aggregate_sha256",
    ):
        changed = dict(receipt)
        changed[field] = "0" * 64
        changed_raw = json.dumps(
            changed,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        if field in (
            "shared_policy_proposal_sha256",
            "exact_count_guard_contract_sha256",
        ):
            assert _reason(
                successor.validate_guarded_power_review_receipt,
                changed_raw,
            ) == "F061_GUARDED_REVIEW_DRIFT:" + field
        else:
            assert _reason(
                successor.validate_guarded_power_review_receipt,
                changed_raw,
            ) == "F061_GUARDED_REVIEW_ATTESTATION_DIGEST_MISMATCH"


def test_guarded_review_exact_json_round_trip_uses_builtin_list() -> None:
    raw = _guarded_review_receipt()
    decoded = successor.validate_guarded_power_review_receipt(raw)
    assert type(decoded) is dict
    assert type(decoded["sole_supported_projection_resolution_entrypoints"]) is list
    assert decoded["sole_supported_projection_resolution_entrypoints"] == list(
        successor.SOLE_SUPPORTED_ENTRYPOINTS
    )
    assert raw == json.dumps(
        decoded,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    assert not raw.endswith(b"\n")


@pytest.mark.parametrize(
    "bad,reason",
    [
        ({}, "F061_GUARDED_REVIEW_RAW_BYTES_REQUIRED"),
        (bytearray(b"{}"), "F061_GUARDED_REVIEW_RAW_BYTES_REQUIRED"),
        (b"", "F061_GUARDED_REVIEW_RAW_BYTE_COUNT_INVALID"),
        (b"{", "F061_GUARDED_REVIEW_JSON_MALFORMED"),
        (b"\xff", "F061_GUARDED_REVIEW_NON_ASCII"),
        (b'{"value":NaN}', "F061_GUARDED_REVIEW_FORBIDDEN_JSON_CONSTANT"),
    ],
)
def test_guarded_review_rejects_nonraw_empty_malformed_or_nonascii(
    bad: Any,
    reason: str,
) -> None:
    assert _reason(successor.validate_guarded_power_review_receipt, bad) == reason


def test_guarded_review_rejects_duplicate_noncanonical_and_terminal_lf() -> None:
    raw = _guarded_review_receipt()
    duplicate = b'{"schema_version":"DUPLICATE",' + raw[1:]
    pretty = json.dumps(
        _guarded_review_receipt_mapping(),
        indent=2,
        sort_keys=True,
    ).encode("ascii")
    reordered = json.dumps(
        _guarded_review_receipt_mapping(),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=False,
    ).encode("ascii")
    assert _reason(
        successor.validate_guarded_power_review_receipt,
        duplicate,
    ) == "F061_GUARDED_REVIEW_DUPLICATE_JSON_KEY"
    for bad in (pretty, reordered, raw + b" "):
        assert _reason(
            successor.validate_guarded_power_review_receipt,
            bad,
        ) == "F061_GUARDED_REVIEW_NONCANONICAL_BYTES"
    assert _reason(
        successor.validate_guarded_power_review_receipt,
        raw + b"\n",
    ) == "F061_GUARDED_REVIEW_TERMINAL_LF_FORBIDDEN"


def test_reviewer_attestation_formula_is_independent_and_mutation_sensitive() -> None:
    receipt = _guarded_review_receipt_mapping()
    projection = dict(receipt)
    attestation = projection.pop("independent_reviewer_attestation_sha256")
    raw_projection = json.dumps(
        projection,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    expected = hashlib.sha256(
        b"heterodiff/two-domain-f061-guarded-power-reviewer-attestation/v1\0"
        + raw_projection
    ).hexdigest()
    assert attestation == expected

    changed = dict(receipt)
    changed["successor_source_raw_sha256"] = "f" * 64
    stale_raw = json.dumps(
        changed,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    assert _reason(
        successor.validate_guarded_power_review_receipt,
        stale_raw,
    ) == "F061_GUARDED_REVIEW_ATTESTATION_DIGEST_MISMATCH"


def test_exact_admissible_total_count_table() -> None:
    assert successor.ADMISSIBLE_NATURAL_GROUP_TOTALS == (852, 853, 854, 855)
    expected = {
        852: (596, 128, 128),
        853: (597, 128, 128),
        854: (598, 128, 128),
        855: (599, 128, 128),
    }
    assert dict(successor.ADMISSIBLE_TOTAL_COUNT_PAIRS) == expected
    for total, counts in expected.items():
        assert successor.hamilton_counts(total) == counts
        assert successor.exact_count_compatibility_predicate(total, counts) is True


def test_neighboring_hamilton_counts_explain_exact_compatibility_boundary() -> None:
    assert successor.hamilton_counts(850) == (595, 128, 127)
    assert successor.hamilton_counts(851) == (596, 128, 127)
    assert successor.hamilton_counts(856) == (599, 129, 128)
    assert successor.hamilton_counts(857) == (600, 129, 128)


def test_every_other_positive_total_through_2000_is_terminal_no_go() -> None:
    allowed = set(successor.ADMISSIBLE_NATURAL_GROUP_TOTALS)
    for total in range(1, 2001):
        if total in allowed:
            continue
        counts = successor.hamilton_counts(total)
        assert _reason(
            successor.exact_count_compatibility_predicate,
            total,
            counts,
        ) == successor.TERMINAL_NO_GO_CODE


@pytest.mark.parametrize("bad", [None, True, False, 1.0, "852", 0, -1])
def test_natural_group_total_requires_positive_exact_builtin_int(bad: Any) -> None:
    assert _reason(successor.hamilton_counts, bad) == (
        "F061_NATURAL_GROUP_COUNT_NONCANONICAL"
    )


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [596, 128, 128],
        (596, 128),
        (596, 128, 128, 0),
        (True, 128, 128),
        (596.0, 128, 128),
        (596, 128, 0),
    ],
)
def test_resolved_counts_require_positive_exact_builtin_int_triple(bad: Any) -> None:
    assert _reason(
        successor.exact_count_compatibility_predicate,
        852,
        bad,
    ) == "F061_RESOLVED_COUNTS_NONCANONICAL"


@pytest.mark.parametrize(
    "bad",
    [
        (595, 129, 128),
        (596, 127, 129),
        (597, 128, 128),
        (596, 128, 129),
    ],
)
def test_admissible_total_with_wrong_or_nonexhaustive_counts_fails(bad: Any) -> None:
    assert _reason(
        successor.exact_count_compatibility_predicate,
        852,
        bad,
    ) == "F061_RESOLVED_COUNTS_HAMILTON_MISMATCH"


@pytest.mark.parametrize("field", list(successor._PROPOSAL_KEYS))
def test_each_proposal_field_drift_fails_closed(field: str) -> None:
    proposal = successor.recognized_proposal()
    value = proposal[field]
    if type(value) is bool:
        proposal[field] = True
    elif type(value) is int:
        proposal[field] = value + 1
    elif type(value) is tuple:
        proposal[field] = tuple(reversed(value))
    else:
        proposal[field] = value + "_DRIFT"
    assert _reason(successor.validate_recognized_proposal, proposal) == (
        "F061_PROPOSAL_DRIFT:" + field
    )


def test_missing_extra_subclass_and_list_proposal_carriers_fail() -> None:
    missing = successor.recognized_proposal()
    missing.pop("power_requirement_id")
    extra = successor.recognized_proposal()
    extra["shadow_minimum"] = 128

    class DictSubclass(dict):
        pass

    assert _reason(successor.validate_recognized_proposal, missing) == (
        "F061_PROPOSAL_SCHEMA_NONCANONICAL"
    )
    assert _reason(successor.validate_recognized_proposal, extra) == (
        "F061_PROPOSAL_SCHEMA_NONCANONICAL"
    )
    assert _reason(
        successor.validate_recognized_proposal,
        DictSubclass(successor.recognized_proposal()),
    ) == "F061_PROPOSAL_SCHEMA_NONCANONICAL"
    listed = successor.recognized_proposal()
    listed["values"] = [70, 15, 15]
    assert _reason(successor.validate_recognized_proposal, listed) == (
        "F061_PROPOSAL_DRIFT:values"
    )


def test_proposal_only_bindings_cannot_pass_as_reviewed() -> None:
    draft = replace(
        _proposal_bindings_draft(),
        f061_allocation_proposal_sha256=successor.PROPOSAL_SHA256,
    )
    assert _reason(successor.validate_reviewed_shared_policy_bindings, draft) == (
        "F061_INDEPENDENT_POWER_REVIEW_RECEIPT_ABSENT"
    )


def test_reviewed_shared_bindings_and_retail_projection_revalidate() -> None:
    receipt = _guarded_review_receipt()
    bindings = _reviewed_complete_bindings(receipt)
    assert (
        successor.validate_reviewed_shared_policy_bindings(bindings, receipt)
        is bindings
    )
    projected = successor.project_reviewed_shared_policy_to_retail(
        bindings,
        receipt,
    )
    assert projected == {
        "schema_version": retail.F061_ALLOCATION_SCHEMA,
        "allocation_id": successor.ALLOCATION_ID,
        "mode": successor.MODE,
        "values": {"TRAIN": 70, "VALIDATION": 15, "TEST": 15},
        "denominator": 100,
        "minimum_counts": {"TRAIN": 1, "VALIDATION": 128, "TEST": 128},
        "power_requirement_id": successor.POWER_REQUIREMENT_ID,
    }


def test_reviewed_binding_digest_or_policy_drift_fails_closed() -> None:
    receipt = _guarded_review_receipt()
    bindings = _reviewed_complete_bindings(receipt)
    assert _reason(
        successor.validate_reviewed_shared_policy_bindings,
        replace(bindings, f061_allocation_proposal_sha256="0" * 64),
        receipt,
    ) == "F061_SHARED_PROPOSAL_BINDING_MISMATCH"
    assert _reason(
        successor.validate_reviewed_shared_policy_bindings,
        replace(bindings, f061_minimum_counts=(1, 127, 128)),
        receipt,
    ) == "F061_PROPOSAL_DRIFT:minimum_counts"
    assert _reason(
        successor.validate_reviewed_shared_policy_bindings,
        replace(bindings, f061_power_review_accepted=False),
        receipt,
    ) == "F061_INDEPENDENT_POWER_REVIEW_NOT_ACCEPTED"


def test_core_binding_alone_cannot_enter_supported_projection() -> None:
    bindings = _reviewed_complete_bindings()
    assert _reason(
        successor.validate_reviewed_shared_policy_bindings,
        bindings,
    ) == "F061_GUARDED_REVIEW_RECEIPT_REQUIRED"
    assert _reason(
        successor.project_reviewed_shared_policy_to_retail,
        bindings,
    ) == "F061_GUARDED_REVIEW_RECEIPT_REQUIRED"


def test_different_valid_guarded_receipt_cannot_launder_review_binding() -> None:
    receipt = _guarded_review_receipt()
    bindings = _reviewed_complete_bindings(receipt)
    other = _guarded_review_receipt(reviewer="other-synthetic-test-reviewer")
    assert _reason(
        successor.validate_reviewed_shared_policy_bindings,
        bindings,
        other,
    ) == "F061_GUARDED_REVIEW_RECEIPT_BINDING_MISMATCH"


@pytest.mark.parametrize(
    "total,expected",
    list(successor.ADMISSIBLE_TOTAL_COUNT_PAIRS),
)
def test_retail_wrapper_accepts_only_exact_128_128_resolutions(
    total: int,
    expected: Any,
) -> None:
    receipt = _guarded_review_receipt()
    resolved = successor.resolve_reviewed_retail_policy(
        _retail_shared_policy(receipt),
        total,
        receipt,
    )
    assert tuple(
        resolved["resolved_customer_counts"][name]
        for name in successor.SPLIT_NAMES
    ) == expected
    assert "temporal_boundary" not in resolved
    assert "split_receipt" not in resolved


@pytest.mark.parametrize("total", [1, 5, 850, 851, 856, 857, 1000, 2001])
def test_retail_wrapper_is_terminal_no_go_for_every_sampled_other_total(
    total: int,
) -> None:
    receipt = _guarded_review_receipt()
    assert _reason(
        successor.resolve_reviewed_retail_policy,
        _retail_shared_policy(receipt),
        total,
        receipt,
    ) == successor.TERMINAL_NO_GO_CODE


def test_retail_wrapper_rejects_other_power_reviewed_policy() -> None:
    receipt = _guarded_review_receipt()
    other = retail.RetailSharedF061Policy.create(
        allocation_id="OTHER_POWER_REVIEWED_POLICY_V1",
        values=(70, 15, 15),
        denominator=100,
        minimum_counts=(1, 128, 128),
        power_requirement_id=successor.POWER_REQUIREMENT_ID,
        power_review_receipt_sha256=(
            successor.guarded_power_review_receipt_sha256(receipt)
        ),
        power_review_accepted=True,
    )
    assert _reason(
        successor.resolve_reviewed_retail_policy,
        other,
        852,
        receipt,
    ) == (
        "F061_PROPOSAL_DRIFT:allocation_id"
    )


@pytest.mark.parametrize(
    "total,expected",
    list(successor.ADMISSIBLE_TOTAL_COUNT_PAIRS),
)
def test_physionet_future_interface_builds_exact_unreviewed_native_candidate(
    total: int,
    expected: Any,
) -> None:
    receipt = _guarded_review_receipt()
    candidate = (
        successor.project_reviewed_shared_policy_to_physionet_review_candidate(
            _reviewed_complete_bindings(receipt),
            total,
            receipt,
        )
    )
    assert candidate["state"] == successor.PHYSIONET_FUTURE_REVIEW_STATE
    assert candidate["patient_count"] == total
    assert candidate["counts"] == expected
    assert candidate["physionet_exact_count_review_receipt_sha256"] is None
    assert candidate["physionet_exact_count_review_accepted"] is None
    assert candidate["shared_review_accepts_resolved_counts"] is False
    assert candidate["f061_closed"] is False
    assert len(candidate["physionet_native_proposal_sha256"]) == 64


@pytest.mark.parametrize("total", [1, 5, 850, 851, 856, 857, 1000, 2001])
def test_physionet_future_interface_is_terminal_no_go_elsewhere(total: int) -> None:
    receipt = _guarded_review_receipt()
    assert _reason(
        successor.project_reviewed_shared_policy_to_physionet_review_candidate,
        _reviewed_complete_bindings(receipt),
        total,
        receipt,
    ) == successor.TERMINAL_NO_GO_CODE


def test_supported_wrappers_block_larger_than_128_generic_predecessor_bypass() -> None:
    """A coherent accepted-core policy cannot use predecessor minima as equality."""

    receipt = _guarded_review_receipt()
    bindings = _reviewed_complete_bindings(receipt)
    direct_physionet = activation.project_shared_policy_to_physionet_f061_proposal(
        bindings,
        856,
    )
    assert direct_physionet["counts"] == (599, 129, 128)
    direct_retail = retail.resolve_f061_allocation(
        _retail_shared_policy(receipt).retail_allocation(),
        856,
    )
    assert direct_retail["resolved_customer_counts"] == {
        "TRAIN": 599,
        "VALIDATION": 129,
        "TEST": 128,
    }
    assert _reason(
        successor.project_reviewed_shared_policy_to_physionet_review_candidate,
        bindings,
        856,
        receipt,
    ) == successor.TERMINAL_NO_GO_CODE
    assert _reason(
        successor.resolve_reviewed_retail_policy,
        _retail_shared_policy(receipt),
        856,
        receipt,
    ) == successor.TERMINAL_NO_GO_CODE


def test_source_has_no_operational_io_or_review_minting_surface() -> None:
    tree = ast.parse((ROOT / SOURCE_REL).read_text(encoding="utf-8"))
    imported = set()
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    assert imported.isdisjoint(
        {"asyncio", "http", "os", "pathlib", "random", "requests", "socket", "subprocess"}
    )
    assert called.isdisjoint(
        {
            "open",
            "request",
            "send",
            "sendall",
            "urlopen",
            "write_bytes",
            "write_text",
        }
    )


def test_no_function_can_create_an_independent_review_or_close_f061() -> None:
    source = (ROOT / SOURCE_REL).read_text(encoding="utf-8")
    tree = ast.parse(source)
    function_names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert not any(
        fragment in name
        for name in function_names
        for fragment in ("accept_review", "create_review", "close_f061")
    )
    assert "f061_closed\": True" not in source
    assert "power_review_accepted\": True" not in source


def _machine(root: Path) -> Dict[str, Any]:
    return json.loads((root / MACHINE_REL).read_text(encoding="ascii"))


def _write_resigned_machine(root: Path, record: Dict[str, Any]) -> None:
    record["record_sha256"] = V.record_sha256(record)
    target = root / MACHINE_REL
    target.write_bytes(V.canonical_bytes(record) + b"\n")
    target.chmod(0o644)


def _copy_bound_tree(target: Path) -> Path:
    paths = set(V.PACKAGE_ROSTER)
    paths.update(spec[1] for spec in V.PREDECESSOR_SPECS)
    for relative in sorted(paths):
        source = ROOT / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(0o644)
    return target


def _mutate_regular_file(path: Path) -> None:
    data = path.read_bytes()
    if data.endswith(b"\n"):
        path.write_bytes(data[:-1] + b"X\n")
    else:
        path.write_bytes(data + b"X")
    path.chmod(0o644)


def test_standalone_validator_and_machine_known_answers_pass() -> None:
    report = V.validate(ROOT)
    record = _machine(ROOT)
    assert report["decision"] == "PASS_PROPOSAL_ONLY_F061_REMAINS_OPEN"
    assert report["record_sha256"] == record["record_sha256"]
    assert report["package_aggregate_sha256"] == record[
        "package_aggregate_sha256"
    ]
    assert report["proposal_sha256"] == successor.PROPOSAL_SHA256
    assert report["exact_count_guard_contract_sha256"] == (
        successor.GUARD_CONTRACT_SHA256
    )
    assert report["accepted_predecessor_binding_count"] == 20
    assert report["package_nonmachine_binding_count"] == 4
    assert report["f061_closed"] is False
    assert report["power_review_present"] is False
    assert report["prior_review_receipt_created"] is False
    assert record["review_remediation"] == {
        "prior_independent_review_decision": "NO_GO",
        "prior_review_receipt_created": False,
        "p1_json_native_list_and_authoritative_raw_byte_validation_remediated": True,
        "p2_noncircular_domain_separated_reviewer_attestation_remediated": True,
        "remediation_is_review_acceptance": False,
        "f061_remains_open": True,
    }


def test_machine_is_canonical_duplicate_free_ascii_json_with_one_lf() -> None:
    data = (ROOT / MACHINE_REL).read_bytes()
    record = V.strict_json(data, canonical_lf=True)
    assert data == V.canonical_bytes(record) + b"\n"
    assert record["record_sha256"] == V.record_sha256(record)
    assert record["package_aggregate_sha256"] == V.package_aggregate_sha256(
        record["package_bindings_excluding_machine_self"]
    )


def test_machine_proposal_digest_known_answer_is_independently_recomputed() -> None:
    proposal = V._proposal_expected()
    raw = json.dumps(
        proposal,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    expected = hashlib.sha256(
        b"heterodiff/two-domain-f061-shared-policy-proposal/v1\0" + raw
    ).hexdigest()
    assert expected == successor.PROPOSAL_SHA256


def test_package_excludes_mutable_trackers_and_all_accepted_bytes_reopen() -> None:
    record = _machine(ROOT)
    bound_paths = {
        row["path"]
        for row in record["accepted_predecessor_bindings"]
        + record["package_bindings_excluding_machine_self"]
    }
    assert "PROJECT_COMPLETION_TIMETABLE.md" not in bound_paths
    assert "PROJECT_EVIDENCE_LEDGER.md" not in bound_paths
    assert record["package_file_roster"] == list(V.PACKAGE_ROSTER)
    for row in record["accepted_predecessor_bindings"]:
        data = (ROOT / row["path"]).read_bytes()
        assert len(data) == row["bytes"]
        assert hashlib.sha256(data).hexdigest() == row["raw_sha256"]


@pytest.mark.parametrize(
    "field,bad",
    [
        ("f061_power_review_receipt_sha256", "0" * 64),
        ("f061_power_review_accepted", False),
        ("f061_power_review_accepted", True),
        ("f061_allocation_definition_sha256", "1" * 64),
        ("f061_field_status", "CLOSED"),
    ],
)
def test_resigned_review_or_f061_closure_smuggling_fails(
    tmp_path: Path,
    field: str,
    bad: Any,
) -> None:
    root = _copy_bound_tree(tmp_path)
    record = _machine(root)
    record["proposal_slot_state"][field] = bad
    _write_resigned_machine(root, record)
    with pytest.raises(V.ValidationError):
        V.validate(root)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("f061_closed", True),
        ("b02_closed", True),
        ("b03_closed", True),
        ("field_count_delta", 1),
        ("blocker_count_delta", 1),
        ("formal_test_count_delta", 1),
        ("scientific_result_count_delta", 1),
        ("operational_task_count_delta", 1),
        ("timetable_checked_task_delta", 1),
        ("tracker_edited", True),
        ("evidence_ledger_edited", True),
    ],
)
def test_resigned_closure_or_tracker_smuggling_fails(
    tmp_path: Path,
    field: str,
    bad: Any,
) -> None:
    root = _copy_bound_tree(tmp_path)
    record = _machine(root)
    record["closure_effect"][field] = bad
    _write_resigned_machine(root, record)
    with pytest.raises(V.ValidationError):
        V.validate(root)


def test_resigned_minimum_only_bypass_and_observed_count_smuggling_fail(
    tmp_path: Path,
) -> None:
    root = _copy_bound_tree(tmp_path)
    record = _machine(root)
    record["exact_count_guard_contract"][
        "larger_than_128_validation_or_test_substitution_permitted"
    ] = True
    record["domain_projection_boundary"][
        "direct_generic_predecessor_entrypoints_supported_for_this_policy"
    ] = True
    record["domain_projection_boundary"]["physionet_natural_group_count_observed"] = 856
    _write_resigned_machine(root, record)
    with pytest.raises(V.ValidationError):
        V.validate(root)


def test_resigned_review_remediation_cannot_be_promoted_to_acceptance(
    tmp_path: Path,
) -> None:
    root = _copy_bound_tree(tmp_path)
    record = _machine(root)
    record["review_remediation"]["remediation_is_review_acceptance"] = True
    record["review_remediation"]["prior_review_receipt_created"] = True
    record["review_remediation"]["f061_remains_open"] = False
    _write_resigned_machine(root, record)
    with pytest.raises(V.ValidationError):
        V.validate(root)


@pytest.mark.parametrize("field", list(successor._PROPOSAL_KEYS))
def test_resigned_machine_proposal_field_drift_fails(
    tmp_path: Path,
    field: str,
) -> None:
    root = _copy_bound_tree(tmp_path)
    record = _machine(root)
    slot_name = {
        "schema_version": None,
        "allocation_id": "f061_allocation_id",
        "mode": "f061_mode",
        "values": "f061_values",
        "denominator_is_null": "f061_denominator_is_null",
        "denominator": "f061_denominator",
        "minimum_counts": "f061_minimum_counts",
        "rounding_rule_id": "f061_rounding_rule_id",
        "power_requirement_id": "f061_power_requirement_id",
    }[field]
    if slot_name is None:
        record["proposal_slot_state"]["f061_allocation_id"] += "_SCHEMA_DRIFT"
    else:
        current = record["proposal_slot_state"][slot_name]
        if type(current) is bool:
            record["proposal_slot_state"][slot_name] = True
        elif type(current) is int:
            record["proposal_slot_state"][slot_name] = current + 1
        elif type(current) is list:
            record["proposal_slot_state"][slot_name] = list(reversed(current))
        else:
            record["proposal_slot_state"][slot_name] = current + "_DRIFT"
    _write_resigned_machine(root, record)
    with pytest.raises(V.ValidationError):
        V.validate(root)


@pytest.mark.parametrize("ordinal", range(len(V.PREDECESSOR_SPECS)))
def test_each_accepted_predecessor_byte_mutation_fails(
    tmp_path: Path,
    ordinal: int,
) -> None:
    root = _copy_bound_tree(tmp_path)
    _mutate_regular_file(root / V.PREDECESSOR_SPECS[ordinal][1])
    with pytest.raises(V.ValidationError):
        V.validate(root)


@pytest.mark.parametrize("relative", list(V.NONMACHINE_PACKAGE_ROSTER))
def test_each_nonmachine_package_byte_mutation_fails(
    tmp_path: Path,
    relative: str,
) -> None:
    root = _copy_bound_tree(tmp_path)
    _mutate_regular_file(root / relative)
    with pytest.raises(V.ValidationError):
        V.validate(root)


def test_resigned_binding_path_hash_ordinal_and_tracker_inclusion_fail(
    tmp_path: Path,
) -> None:
    mutations = (
        lambda record: record["accepted_predecessor_bindings"][0].__setitem__(
            "ordinal", 1
        ),
        lambda record: record["accepted_predecessor_bindings"][0].__setitem__(
            "raw_sha256", "0" * 64
        ),
        lambda record: record["package_bindings_excluding_machine_self"][0].__setitem__(
            "path", "PROJECT_COMPLETION_TIMETABLE.md"
        ),
        lambda record: record["package_file_roster"].append(
            "PROJECT_EVIDENCE_LEDGER.md"
        ),
    )
    for index, mutate in enumerate(mutations):
        root = _copy_bound_tree(tmp_path / str(index))
        record = _machine(root)
        mutate(record)
        _write_resigned_machine(root, record)
        with pytest.raises(V.ValidationError):
            V.validate(root)


def test_duplicate_key_pretty_json_and_missing_lf_fail(tmp_path: Path) -> None:
    roots = [_copy_bound_tree(tmp_path / str(index)) for index in range(3)]
    canonical = (roots[0] / MACHINE_REL).read_bytes()
    duplicate = b'{"schema_version":"DUPLICATE",' + canonical[1:]
    (roots[0] / MACHINE_REL).write_bytes(duplicate)
    pretty = json.dumps(_machine(roots[1]), indent=2, sort_keys=True).encode("ascii") + b"\n"
    (roots[1] / MACHINE_REL).write_bytes(pretty)
    (roots[2] / MACHINE_REL).write_bytes((roots[2] / MACHINE_REL).read_bytes()[:-1])
    for root in roots:
        (root / MACHINE_REL).chmod(0o644)
        with pytest.raises(V.ValidationError):
            V.validate(root)


def test_leaf_symlink_hardlink_and_mode_drift_fail(tmp_path: Path) -> None:
    symlink_root = _copy_bound_tree(tmp_path / "symlink")
    target = symlink_root / V.HUMAN_PATH
    copy = symlink_root / "human-copy.md"
    shutil.copyfile(target, copy)
    target.unlink()
    target.symlink_to(copy)
    with pytest.raises(V.ValidationError):
        V.validate(symlink_root)

    hardlink_root = _copy_bound_tree(tmp_path / "hardlink")
    target = hardlink_root / V.HUMAN_PATH
    link = hardlink_root / "human-hardlink.md"
    os.link(target, link)
    with pytest.raises(V.ValidationError):
        V.validate(hardlink_root)

    mode_root = _copy_bound_tree(tmp_path / "mode")
    (mode_root / V.HUMAN_PATH).chmod(0o600)
    with pytest.raises(V.ValidationError):
        V.validate(mode_root)


def test_validator_passes_from_unrelated_working_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    assert V.validate(ROOT)["decision"] == (
        "PASS_PROPOSAL_ONLY_F061_REMAINS_OPEN"
    )


def test_alternate_pyc_is_ignored(tmp_path: Path) -> None:
    root = _copy_bound_tree(tmp_path)
    cache = root / "src/heterodiff/data/__pycache__"
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "two_domain_f061_preservation_first_successor.cpython-399.pyc").write_bytes(
        b"hostile alternate cache"
    )
    assert V.validate(root)["decision"] == (
        "PASS_PROPOSAL_ONLY_F061_REMAINS_OPEN"
    )


def test_validator_does_not_import_or_execute_candidate_source() -> None:
    tree = ast.parse((ROOT / VALIDATOR_REL).read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not any(
        module.startswith("heterodiff") for module in imported_modules
    )
    assert "exec(" not in (ROOT / VALIDATOR_REL).read_text(encoding="utf-8")
