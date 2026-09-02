"""Hostile qualification for the additive F060 temporal-rule freeze."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List, Mapping

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_REL = Path(
    "research/diagnostics/"
    "manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.py"
)
MACHINE_REL = Path(
    "research/fixtures/"
    "manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.json"
)
HUMAN_REL = Path("PROJECT_GATE_A_RETAIL_TEMPORAL_RULE_FIELD_FREEZE.md")
TEST_REL = Path(
    "tests/unit/"
    "test_manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.py"
)
OLD_RETAIL_VALIDATOR_REL = Path(
    "research/diagnostics/"
    "manuscript_v3_retail_customer_disjoint_temporal_split_design_v1.py"
)


class _StringSubclass(str):
    pass


class _IntegerSubclass(int):
    pass


class _ListSubclass(list):
    pass


class _DictSubclass(dict):
    pass


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load(VALIDATOR_REL, "gate_a_retail_f060_field_freeze_validator")


@pytest.fixture(scope="module")
def old_retail_validator() -> ModuleType:
    return _load(OLD_RETAIL_VALIDATOR_REL, "bound_retail_temporal_design_validator")


def _closed_roster(module: ModuleType) -> List[str]:
    paths = list(module.PACKAGE_ROSTER)
    paths.extend(spec[2] for spec in module.PREDECESSOR_SPECS)
    assert len(paths) == len(set(paths))
    return paths


def _copy_roster(module: ModuleType, tmp_path: Path) -> Path:
    for relative in _closed_roster(module):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o644)
    return tmp_path


def _rewrite_machine(
    module: ModuleType,
    root: Path,
    mutation: Callable[[Dict[str, Any]], None],
    *,
    recompute_digest: bool = True,
    canonical: bool = True,
) -> None:
    path = root / MACHINE_REL
    record = json.loads(path.read_text(encoding="ascii"))
    mutation(record)
    if recompute_digest:
        record["record_sha256"] = module.record_sha256(record)
    if canonical:
        raw = module.canonical_machine_bytes(record)
    else:
        raw = json.dumps(record, indent=2, sort_keys=True).encode("ascii") + b"\n"
    path.write_bytes(raw)
    path.chmod(0o644)


def _replace(record: Dict[str, Any], dotted: str, value: Any) -> None:
    current: Any = record
    tokens = dotted.split(".")
    for token in tokens[:-1]:
        current = current[int(token)] if type(current) is list else current[token]
    final = tokens[-1]
    if type(current) is list:
        current[int(final)] = value
    else:
        current[final] = value


def _tree_digest(root: Path, paths: Iterable[str]) -> Dict[str, str]:
    return {
        relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
        for relative in paths
    }


def _rows(timestamps: List[int]) -> List[Dict[str, Any]]:
    return [
        {
            "row_ordinal": index,
            "customer_key_hex": bytes([index + 1]).hex(),
            "timestamp_utc_microseconds": timestamp,
        }
        for index, timestamp in enumerate(timestamps)
    ]


def _expand_field_tokens(text: str) -> set[str]:
    result = set()
    for token in text.split(","):
        token = token.strip()
        if "-" not in token:
            result.add(token)
            continue
        first, last = token.split("-", 1)
        start = int(first[1:])
        stop = int(last[1:])
        result.update("F" + str(value).zfill(3) for value in range(start, stop + 1))
    return result


def test_canonical_package_validates_one_field_effect(validator: ModuleType) -> None:
    status = validator.validate(ROOT)
    assert status == {
        "schema_version": validator.SCHEMA,
        "state": "GATE_A_RETAIL_F060_TEMPORAL_RULE_FROZEN_PREOUTCOME",
        "global_state": "DRAFT_NOT_EXECUTABLE",
        "record_sha256": status["record_sha256"],
        "control_predicate": (
            "RETAIL_F060_PARAMETERIZED_TEMPORAL_CUTOFF_WINDOW_RULE_FROZEN"
        ),
        "F060_closed": True,
        "F060_rule_id": (
            "RETAIL_CUSTOMER_DISJOINT_TEMPORAL_EXHAUSTIVE_GAP_PAIR_"
            "F061_PARAMETERIZED_V1"
        ),
        "F061_closed": False,
        "F061_value": None,
        "unresolved_fields_closed": 1,
        "effective_pre_execution_open": 158,
        "effective_post_execution_open": 6,
        "effective_unresolved_field_count": 164,
        "effective_closed_field_count": 8,
        "effective_open_blocker_count": 12,
        "domain_admitted": False,
        "real_split_performed": False,
        "scientific_result": False,
        "tracker_edit_performed": False,
        "validation": "PASS",
    }
    assert len(status["record_sha256"]) == 64


def test_machine_is_canonical_and_matches_expected_record(validator: ModuleType) -> None:
    raw = (ROOT / MACHINE_REL).read_bytes()
    record = json.loads(raw.decode("ascii"))
    assert raw == validator.canonical_machine_bytes(record)
    assert record["record_sha256"] == validator.record_sha256(record)
    assert record == validator.expected_record(ROOT)


def test_authority_is_narrow(validator: ModuleType) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    authority = record["authority_provenance"]
    assert authority["normalized_visible_text"] == validator.AUTHORITY_TEXT
    assert authority["normalized_visible_text_sha256"] == hashlib.sha256(
        validator.AUTHORITY_TEXT.encode("utf-8")
    ).hexdigest()
    assert authority["local_autonomous_project_work_authorized"] is True
    assert authority[
        "agent_selected_paths_schema_parameterization_and_qualification_cases"
    ] is True
    assert authority["raw_transport_bytes_or_trailing_html_space_bound"] is False
    assert authority["network_source_contact_or_data_access_authorized"] is False
    assert authority[
        "entropy_runtime_training_scientific_execution_or_real_split_authorized"
    ] is False
    assert authority[
        "claim_promotion_submission_or_tracker_edit_authorized_by_this_package"
    ] is False


def test_exact_four_file_roster_and_noncyclic_bindings(validator: ModuleType) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    assert record["package_file_roster"] == [
        str(HUMAN_REL),
        str(MACHINE_REL),
        str(VALIDATOR_REL),
        str(TEST_REL),
    ]
    bindings = record["package_bindings_excluding_machine_self"]
    assert [row["role"] for row in bindings] == ["human", "validator", "test"]
    assert [row["path"] for row in bindings] == [
        str(HUMAN_REL),
        str(VALIDATOR_REL),
        str(TEST_REL),
    ]
    for row in bindings:
        raw = (ROOT / row["path"]).read_bytes()
        assert row["bytes"] == len(raw)
        assert row["raw_sha256"] == hashlib.sha256(raw).hexdigest()
        assert row["mode_octal"] == "0644"
        assert row["nlink"] == 1
        assert row["terminal_lf"] is True
    assert record["machine_self_binding"] == {
        "path": str(MACHINE_REL),
        "semantic_self_digest_field": "record_sha256",
        "raw_self_hash_embedded": False,
    }


def test_all_26_predecessor_files_are_exactly_bound(validator: ModuleType) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    bindings = record["predecessor_bindings"]
    assert len(bindings) == len(validator.PREDECESSOR_SPECS) == 26
    assert record["predecessor_group_counts"] == validator.PREDECESSOR_GROUP_COUNTS
    for ordinal, (binding, spec) in enumerate(
        zip(bindings, validator.PREDECESSOR_SPECS)
    ):
        group, role, path, byte_count, raw_sha, semantic_sha = spec
        assert binding["ordinal"] == ordinal
        assert binding["group"] == group
        assert binding["role"] == role
        assert binding["path"] == path
        assert binding["bytes"] == byte_count
        assert binding["raw_sha256"] == raw_sha
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == raw_sha
        if semantic_sha is None:
            assert "record_sha256" not in binding
        else:
            assert binding["record_sha256"] == semantic_sha


def test_predecessor_projection_establishes_exact_165_7_baseline(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    receipt = record["predecessor_projection_receipt"]
    assert receipt == {
        "preregistration_F058_F059_F060_F061_null": True,
        "prospective_seal_active_no_acquisition_or_opening": True,
        "historical_retail_design_f060_and_f061_zero_delta_preserved": True,
        "historical_manifest_drafts_f019_through_f061_zero_delta_preserved": True,
        "retail_temporal_projection_matches_bound_design_except_f061_parameterization": True,
        "baseline_closed_field_ids": [
            "F106",
            "F107",
            "F108",
            "F113",
            "F128",
            "F129",
            "F148",
        ],
        "baseline_pre_execution_open": 159,
        "baseline_pre_execution_closed": 7,
        "baseline_post_execution_open": 6,
        "baseline_total_open": 165,
        "baseline_total_closed": 7,
    }


def test_f060_value_is_complete_and_f061_is_only_typed_input(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    closure = record["field_closures"]
    assert len(closure) == 1
    assert closure[0]["field_id"] == "F060"
    assert closure[0]["json_pointer"] == validator.F060_POINTER
    assert closure[0]["value"] == validator.F060_VALUE
    assert closure[0]["separate_unresolved_input_field_id"] == "F061"
    assert closure[0]["separate_unresolved_input_json_pointer"] == validator.F061_POINTER
    assert closure[0]["separate_unresolved_input_value"] is None
    value = closure[0]["value"]
    assert value["target_customer_counts_source_json_pointer"] == validator.F061_POINTER
    assert value["target_customer_counts_input_semantics"] == (
        "EXACT_POSITIVE_INTEGER_COUNT_PROJECTION_PRODUCED_BY_COMPLETE_F061_"
        "VALUE_WHETHER_F061_USES_COUNTS_OR_PROPORTIONS_PLUS_ITS_OWN_ROUNDING_RULE"
    )
    assert value["target_customer_counts_value_frozen_by_this_rule"] is False
    assert value["f061_raw_representation_or_rounding_rule_frozen_by_this_rule"] is False
    assert value["observed_cutoff_or_window_frozen"] is False
    assert value["outcome_label_or_model_result_used"] is False
    assert value["no_feasible_pair_code"] == validator.NO_FEASIBLE
    assert value["feasibility_requirements"] == list(
        validator.FEASIBILITY_REQUIREMENTS
    )


def test_f060_f061_separation_does_not_shadow_hamilton_allocation(
    validator: ModuleType,
) -> None:
    record = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))
    split = record["f060_f061_separation"]
    assert split == {
        "distinct_sibling_json_pointers": True,
        "f060_owns_temporal_mapping_not_allocation": True,
        "f061_owns_target_proportions_or_counts_and_power_justification": True,
        "f061_may_use_counts_or_proportions_plus_its_own_rounding_rule": True,
        "f061_raw_representation_or_conversion_selected_by_package": False,
        "historical_hamilton_70_15_15_identity_used_as_f060_value": False,
        "historical_70_15_15_instantiation_qualified": True,
        "non_70_15_15_target_count_instantiation_qualified": True,
        "f060_rule_requires_exact_f061_counts_before_any_real_application": True,
        "f061_value_selected_or_shadow_bound_by_package": False,
    }
    serialized = json.dumps(record["field_closures"], sort_keys=True)
    assert "HAMILTON_70_15_15" not in serialized
    assert '"allocation_numerators"' not in serialized
    assert '"allocation_denominator"' not in serialized


def test_exact_count_transition_is_165_7_to_164_8(validator: ModuleType) -> None:
    transition = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))[
        "count_transition"
    ]
    assert transition == {
        "before": {
            "pre_execution_open": 159,
            "pre_execution_closed": 7,
            "post_execution_open": 6,
            "post_execution_closed": 0,
            "total_open": 165,
            "total_closed": 7,
        },
        "closed_by_package": {
            "field_ids": ["F060"],
            "pre_execution": 1,
            "post_execution": 0,
            "total": 1,
        },
        "after": {
            "pre_execution_open": 158,
            "pre_execution_closed": 8,
            "post_execution_open": 6,
            "post_execution_closed": 0,
            "total_open": 164,
            "total_closed": 8,
        },
        "blockers_open_after": 12,
        "blockers_closed": 0,
        "formal_tests_closed": 0,
        "results_filled": 0,
    }


def test_comprehensive_sweep_covers_every_remaining_pre_field_once(
    validator: ModuleType,
) -> None:
    sweep = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))[
        "comprehensive_pre_field_sweep"
    ]
    assert sweep["total_pre_fields"] == 166
    assert sweep["closed_before_ids"] == list(validator.PRIOR_CLOSED_FIELDS)
    assert sweep["eligible_now_ids"] == ["F060"]
    assert sweep["closed_after_ids"] == list(validator.CLOSED_AFTER)
    assert sweep["open_after_count"] == 158
    assert sweep["open_after_ids"] == list(validator.OPEN_PRE_AFTER)
    assert len(sweep["open_after_ids"]) == len(set(sweep["open_after_ids"])) == 158
    covered = set()
    for group in sweep["audit_groups"]:
        expanded = _expand_field_tokens(group["field_ids"])
        assert not covered.intersection(expanded)
        covered.update(expanded)
        assert type(group["reason"]) is str and group["reason"]
    assert covered == set(validator.OPEN_PRE_AFTER)
    assert sweep["additional_eligible_field_count"] == 0
    assert sweep["anti_drift_no_precursor_created_for_ineligible_fields"] is True


def test_nonclaims_keep_all_operational_scientific_states_open(
    validator: ModuleType,
) -> None:
    effects = json.loads((ROOT / MACHINE_REL).read_text(encoding="ascii"))[
        "project_effects_and_nonclaims"
    ]
    assert effects["only_field_closed"] == "F060"
    assert effects["F058_open_actual_physionet_manifest_absent"] is True
    assert effects["F059_open_actual_retail_manifest_absent"] is True
    assert effects["F061_open_null_unpowered"] is True
    assert effects["F105_F109_F110_F111_F112_open_no_admitted_metric_instance"] is True
    assert effects["F149_open_no_power_compute_operating_semantics"] is True
    assert effects["all_other_open_pre_fields_remain_open"] is True
    assert effects["B03_open"] is True
    assert effects["all_12_blockers_open"] is True
    assert effects["formal_tests_28_29_30_open"] is True
    assert effects["R1_R2_R3_R4_open"] is True
    assert effects["gate_a_closed_by_package"] is False
    assert effects["domain_admitted"] is False
    assert effects["real_snapshot_or_split_manifest_present"] is False
    assert effects["real_cutoff_or_window_observed"] is False
    assert effects["real_feasibility_observed"] is False
    assert effects["power_justification_complete"] is False
    assert effects["scientific_result"] is False
    assert effects["tracker_edit_performed"] is False


def test_non_70_15_15_target_counts_are_supported(validator: ModuleType) -> None:
    result = validator.select_temporal_boundary(
        _rows([10, 20, 30, 40]), {"TRAIN": 2, "VALIDATION": 1, "TEST": 1}
    )
    assert result["target_customer_counts"] == {
        "TRAIN": 2,
        "VALIDATION": 1,
        "TEST": 1,
    }
    assert result["boundary"] == {
        "train_last_timestamp_utc_microseconds": 20,
        "validation_first_timestamp_utc_microseconds": 30,
        "validation_last_timestamp_utc_microseconds": 30,
        "test_first_timestamp_utc_microseconds": 40,
    }
    assert result["caller_inputs_verified_as_real_or_scientific_evidence"] is False


def test_historical_70_15_15_instantiation_matches_bound_splitter(
    validator: ModuleType, old_retail_validator: ModuleType
) -> None:
    rows = _rows(list(range(10, 110, 10)))
    old = old_retail_validator.split_retail_rows(copy.deepcopy(rows))
    new = validator.select_temporal_boundary(
        copy.deepcopy(rows), {"TRAIN": 7, "VALIDATION": 2, "TEST": 1}
    )
    assert new["boundary"] == old["boundary"]
    assert new["customer_assignments"] == old["customer_assignments"]
    assert new["row_assignments"] == old["row_assignments"]
    assert new["target_customer_counts"] == old["customer_counts"]
    assert new["row_counts"] == old["row_counts"]


def test_input_permutation_is_invariant(validator: ModuleType) -> None:
    rows = _rows([10, 20, 30, 40, 50])
    targets = {"TRAIN": 2, "VALIDATION": 2, "TEST": 1}
    forward = validator.select_temporal_boundary(rows, targets)
    reverse = validator.select_temporal_boundary(list(reversed(rows)), targets)
    assert forward == reverse


def test_complete_multirow_customers_move_together(validator: ModuleType) -> None:
    rows = [
        {"row_ordinal": 0, "customer_key_hex": "01", "timestamp_utc_microseconds": 10},
        {"row_ordinal": 1, "customer_key_hex": "01", "timestamp_utc_microseconds": 11},
        {"row_ordinal": 2, "customer_key_hex": "02", "timestamp_utc_microseconds": 20},
        {"row_ordinal": 3, "customer_key_hex": "03", "timestamp_utc_microseconds": 30},
        {"row_ordinal": 4, "customer_key_hex": "03", "timestamp_utc_microseconds": 31},
        {"row_ordinal": 5, "customer_key_hex": "04", "timestamp_utc_microseconds": 40},
    ]
    result = validator.select_temporal_boundary(
        rows, {"TRAIN": 2, "VALIDATION": 1, "TEST": 1}
    )
    by_customer: Dict[str, set[str]] = {}
    for row, assignment in zip(rows, result["row_assignments"]):
        by_customer.setdefault(row["customer_key_hex"], set()).add(assignment["split"])
    assert all(len(values) == 1 for values in by_customer.values())
    assert result["row_count"] == len(rows)
    assert sum(result["row_counts"].values()) == len(rows)


@pytest.mark.parametrize(
    "rows,targets",
    [
        (
            [
                {"row_ordinal": 0, "customer_key_hex": "01", "timestamp_utc_microseconds": 10},
                {"row_ordinal": 1, "customer_key_hex": "01", "timestamp_utc_microseconds": 40},
                {"row_ordinal": 2, "customer_key_hex": "02", "timestamp_utc_microseconds": 20},
                {"row_ordinal": 3, "customer_key_hex": "03", "timestamp_utc_microseconds": 30},
            ],
            {"TRAIN": 1, "VALIDATION": 1, "TEST": 1},
        ),
        (_rows([10, 10, 10]), {"TRAIN": 1, "VALIDATION": 1, "TEST": 1}),
        (_rows([10, 20, 20]), {"TRAIN": 1, "VALIDATION": 1, "TEST": 1}),
    ],
)
def test_no_feasible_cases_fail_terminally(
    validator: ModuleType, rows: Any, targets: Any
) -> None:
    with pytest.raises(validator.TemporalRuleError, match=validator.NO_FEASIBLE):
        validator.select_temporal_boundary(rows, targets)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda rows: rows[0].__setitem__("label", 1),
        lambda rows: rows[0].pop("customer_key_hex"),
        lambda rows: rows[1].__setitem__("row_ordinal", 0),
        lambda rows: rows[0].__setitem__("row_ordinal", True),
        lambda rows: rows[0].__setitem__("row_ordinal", _IntegerSubclass(0)),
        lambda rows: rows[0].__setitem__("customer_key_hex", ""),
        lambda rows: rows[0].__setitem__("customer_key_hex", "A0"),
        lambda rows: rows[0].__setitem__("customer_key_hex", "0"),
        lambda rows: rows[0].__setitem__("customer_key_hex", "gg"),
        lambda rows: rows[0].__setitem__("customer_key_hex", _StringSubclass("01")),
        lambda rows: rows[0].__setitem__("timestamp_utc_microseconds", True),
        lambda rows: rows[0].__setitem__("timestamp_utc_microseconds", _IntegerSubclass(10)),
        lambda rows: rows[0].__setitem__("timestamp_utc_microseconds", -(2**63) - 1),
        lambda rows: rows[0].__setitem__("timestamp_utc_microseconds", 2**63),
        lambda rows: rows.__setitem__(0, _DictSubclass(rows[0])),
        lambda rows: rows[0].__setitem__(_StringSubclass("label"), 1),
    ],
)
def test_malformed_rows_fail_closed(
    validator: ModuleType, mutation: Callable[[Any], None]
) -> None:
    rows: Any = _rows([10, 20, 30, 40])
    mutation(rows)
    with pytest.raises(validator.TemporalRuleError):
        validator.select_temporal_boundary(
            rows, {"TRAIN": 2, "VALIDATION": 1, "TEST": 1}
        )


@pytest.mark.parametrize(
    "rows",
    [None, (), {}, "rows", _ListSubclass(_rows([10, 20, 30, 40])), []],
)
def test_row_container_must_be_exact_nonempty_list(
    validator: ModuleType, rows: Any
) -> None:
    with pytest.raises(validator.TemporalRuleError):
        validator.select_temporal_boundary(
            rows, {"TRAIN": 2, "VALIDATION": 1, "TEST": 1}
        )


@pytest.mark.parametrize(
    "targets",
    [
        None,
        [],
        _DictSubclass({"TRAIN": 2, "VALIDATION": 1, "TEST": 1}),
        {"TRAIN": 2, "VALIDATION": 1},
        {"TRAIN": 2, "VALIDATION": 1, "TEST": 1, "EXTRA": 1},
        {"TRAIN": 2, "VALIDATION": 1, "TEST": 0},
        {"TRAIN": 2, "VALIDATION": 1, "TEST": True},
        {"TRAIN": 2, "VALIDATION": 1, "TEST": _IntegerSubclass(1)},
        {"TRAIN": 3, "VALIDATION": 1, "TEST": 1},
        {_StringSubclass("TRAIN"): 2, "VALIDATION": 1, "TEST": 1},
    ],
)
def test_target_count_roster_types_positivity_and_coverage_fail_closed(
    validator: ModuleType, targets: Any
) -> None:
    with pytest.raises(validator.TemporalRuleError):
        validator.select_temporal_boundary(_rows([10, 20, 30, 40]), targets)


def test_output_digests_bind_rows_counts_and_assignments(validator: ModuleType) -> None:
    rows = _rows([10, 20, 30, 40])
    targets = {"TRAIN": 2, "VALIDATION": 1, "TEST": 1}
    result = validator.select_temporal_boundary(rows, targets)
    input_value = {"normalized_rows": rows, "target_customer_counts": targets}
    assert result["rule_input_sha256"] == hashlib.sha256(
        validator.INPUT_DOMAIN + validator._canonical_payload_bytes(input_value)
    ).hexdigest()
    digest = result.pop("assignment_manifest_sha256")
    assert digest == hashlib.sha256(
        validator.ASSIGNMENT_DOMAIN + validator._canonical_payload_bytes(result)
    ).hexdigest()


MACHINE_MUTATIONS: List[Callable[[Dict[str, Any]], None]] = [
    lambda record: record.__setitem__("state", "PASS"),
    lambda record: record.__setitem__("control_predicate", "PASS"),
    lambda record: _replace(record, "field_closures.0.field_id", "F061"),
    lambda record: _replace(record, "field_closures.0.json_pointer", "/wrong"),
    lambda record: _replace(record, "field_closures.0.value.rule_id", "HAMILTON_70_15_15"),
    lambda record: _replace(record, "field_closures.0.value.target_customer_counts_value_frozen_by_this_rule", True),
    lambda record: _replace(record, "field_closures.0.value.f061_raw_representation_or_rounding_rule_frozen_by_this_rule", True),
    lambda record: _replace(record, "field_closures.0.value.observed_cutoff_or_window_frozen", True),
    lambda record: _replace(record, "field_closures.0.value.outcome_label_or_model_result_used", True),
    lambda record: _replace(record, "field_closures.0.separate_unresolved_input_value", [70, 15, 15]),
    lambda record: _replace(record, "f060_f061_separation.f061_value_selected_or_shadow_bound_by_package", True),
    lambda record: _replace(record, "f060_f061_separation.f061_raw_representation_or_conversion_selected_by_package", True),
    lambda record: _replace(record, "count_transition.after.total_open", 163),
    lambda record: _replace(record, "count_transition.blockers_closed", 1),
    lambda record: _replace(record, "comprehensive_pre_field_sweep.additional_eligible_field_count", 1),
    lambda record: _replace(record, "project_effects_and_nonclaims.F061_open_null_unpowered", False),
    lambda record: _replace(record, "project_effects_and_nonclaims.domain_admitted", True),
    lambda record: _replace(record, "project_effects_and_nonclaims.real_split_performed", True),
    lambda record: _replace(record, "project_effects_and_nonclaims.scientific_result", True),
    lambda record: _replace(record, "qualification_boundary.production_splitter_claimed", True),
    lambda record: record["field_closures"].append(copy.deepcopy(record["field_closures"][0])),
    lambda record: record["predecessor_bindings"].pop(),
]


@pytest.mark.parametrize("mutation", MACHINE_MUTATIONS)
def test_coherently_rehashed_machine_tampering_fails_expected_projection(
    validator: ModuleType, tmp_path: Path, mutation: Callable[[Dict[str, Any]], None]
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(validator, root, mutation)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_machine_tamper_without_rehash_fails_self_digest(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(
        validator,
        root,
        lambda record: record.__setitem__("state", "PASS"),
        recompute_digest=False,
    )
    with pytest.raises(validator.ValidationError, match="self-digest"):
        validator.validate(root)


@pytest.mark.parametrize("index", range(26))
def test_every_predecessor_byte_binding_fails_closed(
    validator: ModuleType, tmp_path: Path, index: int
) -> None:
    root = _copy_roster(validator, tmp_path)
    relative = validator.PREDECESSOR_SPECS[index][2]
    path = root / relative
    raw = path.read_bytes()
    path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="predecessor exact-byte"):
        validator.validate(root)


@pytest.mark.parametrize("relative", [str(HUMAN_REL), str(VALIDATOR_REL), str(TEST_REL)])
def test_every_nonmachine_package_binding_fails_closed(
    validator: ModuleType, tmp_path: Path, relative: str
) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / relative
    path.write_bytes(path.read_bytes() + b"X")
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_noncanonical_machine_json_fails_closed(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    _rewrite_machine(validator, root, lambda record: None, canonical=False)
    with pytest.raises(validator.ValidationError, match="not canonical"):
        validator.validate(root)


def test_duplicate_machine_json_key_fails_closed(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / MACHINE_REL
    raw = path.read_bytes()
    path.write_bytes(b'{"schema_version":"duplicate",' + raw[1:])
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="duplicate JSON key"):
        validator.validate(root)


@pytest.mark.parametrize("payload", [b'\xff\n', b'{"x":NaN}\n', b'[]\n'])
def test_nonascii_nonfinite_and_nonobject_machine_json_fail_closed(
    validator: ModuleType, tmp_path: Path, payload: bytes
) -> None:
    root = _copy_roster(validator, tmp_path)
    path = root / MACHINE_REL
    path.write_bytes(payload)
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError):
        validator.validate(root)


def test_machine_mode_hardlink_and_symlink_fail_custody(
    validator: ModuleType, tmp_path: Path
) -> None:
    for case in ("mode", "hardlink", "symlink"):
        root = _copy_roster(validator, tmp_path / case)
        path = root / MACHINE_REL
        if case == "mode":
            path.chmod(0o600)
        elif case == "hardlink":
            backup = root / "machine-hardlink-backup"
            path.replace(backup)
            os.link(backup, path)
        else:
            backup = root / "machine-symlink-target"
            path.replace(backup)
            path.symlink_to(backup)
        with pytest.raises(validator.ValidationError):
            validator.validate(root)


def test_predecessor_semantic_self_digest_is_recomputed(
    validator: ModuleType, tmp_path: Path
) -> None:
    root = _copy_roster(validator, tmp_path)
    spec = next(
        item
        for item in validator.PREDECESSOR_SPECS
        if item[0] == "GATE_A_MINIMUM_CONTRIBUTION_REBASELINE_V1"
        and item[1] == "machine"
    )
    path = root / spec[2]
    record = json.loads(path.read_text(encoding="ascii"))
    record["record_sha256"] = "0" * 64
    path.write_bytes(validator.canonical_machine_bytes(record))
    path.chmod(0o644)
    with pytest.raises(validator.ValidationError, match="predecessor exact-byte"):
        validator.validate(root)


def test_validator_source_has_no_writer_network_process_entropy_or_science_route() -> None:
    tree = ast.parse((ROOT / VALIDATOR_REL).read_text(encoding="utf-8"))
    allowed_imports = {
        "__future__",
        "hashlib",
        "json",
        "math",
        "os",
        "pathlib",
        "stat",
        "typing",
    }
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported <= allowed_imports
    forbidden_names = {"open", "exec", "eval", "compile", "__import__"}
    assert not {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id in forbidden_names
    }
    forbidden_attributes = {
        "write",
        "write_text",
        "write_bytes",
        "mkdir",
        "unlink",
        "rename",
        "symlink_to",
        "hardlink_to",
        "system",
        "popen",
        "urandom",
    }
    assert not {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr in forbidden_attributes
    }
    text = (ROOT / VALIDATOR_REL).read_text(encoding="utf-8")
    for token in (
        "subprocess.",
        "socket.",
        "requests.",
        "urllib.",
        "http.client",
        "random.",
        "secrets.",
        "numpy",
        "torch",
        "heterodiff.",
        "os.replace(",
    ):
        assert token not in text


def test_validation_does_not_modify_canonical_roster(validator: ModuleType) -> None:
    paths = _closed_roster(validator)
    before = _tree_digest(ROOT, paths)
    validator.validate(ROOT)
    after = _tree_digest(ROOT, paths)
    assert after == before


def test_human_record_states_exact_closure_and_nonclaims() -> None:
    text = (ROOT / HUMAN_REL).read_text(encoding="utf-8")
    assert "closes exactly one pre-execution field, F060" in text
    assert "F061 remains null" in text
    assert "does **not** copy" in text
    assert "No actual timestamp" in text
    assert "F058 and F059 are paths to actual" in text
    assert "F149 is a scientific operating threshold" in text
    assert "All 12 blockers" in text
    assert "No real Retail snapshot was opened" in text
