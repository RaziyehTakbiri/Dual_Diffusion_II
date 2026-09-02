from __future__ import annotations

from copy import deepcopy
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from heterodiff.experiments import two_domain_baseline_registry as b06
from heterodiff.experiments import two_domain_training_checkpoint_plan as plan
from heterodiff.evaluation.two_domain_count_normalized_event_cks import (
    physionet_configuration,
)
from heterodiff.evaluation.two_domain_count_normalized_event_cks_production import (
    production_conditional_cks_score,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "src/heterodiff/experiments/two_domain_training_checkpoint_plan.py"
MACHINE_PATH = ROOT / (
    "research/fixtures/"
    "manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.json"
)
VALIDATOR_PATH = ROOT / (
    "research/diagnostics/"
    "manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.py"
)


def _domain_digest(domain: str, value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(domain.encode("ascii") + b"\0" + raw).hexdigest()


def _direct_b06_rows() -> list[tuple[str, str, str, str]]:
    registry = b06.FROZEN_REGISTRY
    rows = []
    for primary in registry["primary_pair"]:
        for domain_id in b06.DOMAIN_IDS:
            rows.append(
                (
                    primary["method_id"],
                    domain_id,
                    primary["config_sha256"],
                    "PRIMARY",
                )
            )
    for control in registry["controls"]:
        for domain_id in b06.DOMAIN_IDS:
            rows.append(
                (
                    control["control_id"],
                    domain_id,
                    control["config_sha256"],
                    "CONTROL",
                )
            )
    for family in registry["literature_families"]:
        for domain_id in b06.DOMAIN_IDS:
            implementation = family["implementation_by_domain"][domain_id]
            rows.append(
                (
                    implementation["implementation_id"],
                    domain_id,
                    implementation["config_sha256"],
                    "LITERATURE_FAMILY",
                )
            )
    for external in registry["external_baselines"]:
        rows.append(
            (
                external["method_id"],
                external["domain_id"],
                external["config_sha256"],
                "EXTERNAL_BASELINE",
            )
        )
    return sorted(rows)


def _validation_input(step: int = 256, value: float = 1.0) -> dict[str, object]:
    executable = plan.executable_configuration_rows()[0]
    checkpoint_sha = "1" * 64
    selection_sha = "2" * 64
    method_id = executable["method_id"]
    domain_id = executable["domain_id"]
    executable_sha = executable["executable_configuration_sha256"]
    rows = []
    for ordinal in range(128):
        group_sha = hashlib.sha256(
            "group-{}".format(ordinal).encode("ascii")
        ).hexdigest()
        formal_sha = hashlib.sha256(
            "formal-{}".format(ordinal).encode("ascii")
        ).hexdigest()
        factory_sha = _domain_digest(
            "heterodiff-production-cks-score-v1",
            {
                "binary64_score_hex": value.hex(),
                "domain_id": domain_id,
                "draw_count": 64,
                "formal_score_sha256": formal_sha,
                "integration_id": "F105_CKS_BINARY64_PROJECTION_V1",
                "metric_id": "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1",
                "score_direction": "LOWER_IS_BETTER",
                "symbolic_event_pair_work_units": 0,
            },
        )
        bound_sha = _domain_digest(
            "heterodiff-f144-bound-group-score-integrity-v1",
            {
                "binary64_score_hex": value.hex(),
                "checkpoint_content_sha256": checkpoint_sha,
                "domain_id": domain_id,
                "draw_count": 64,
                "executable_configuration_sha256": executable_sha,
                "f105_factory_score_integrity_sha256": factory_sha,
                "group_id_sha256": group_sha,
                "integration_id": "F105_CKS_BINARY64_PROJECTION_V1",
                "method_id": method_id,
                "metric_id": "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1",
                "ordinal": ordinal,
                "selection_unit_sha256": selection_sha,
            },
        )
        rows.append(
            {
                "binary64_score_hex": value.hex(),
                "f105_factory_score_integrity_sha256": factory_sha,
                "formal_score_sha256": formal_sha,
                "group_id_sha256": group_sha,
                "ordinal": ordinal,
                "score_integrity_sha256": bound_sha,
                "symbolic_event_pair_work_units": 0,
            }
        )
    roster = _domain_digest(
        "heterodiff-f144-complete-f134-validation-group-roster-v1",
        [row["group_id_sha256"] for row in rows],
    )
    subject = plan.complete_roster_certificate_subject_sha256(
        checkpoint_content_sha256=checkpoint_sha,
        domain_id=domain_id,
        executable_configuration_sha256=executable_sha,
        group_roster_sha256=roster,
        group_score_integrity_sha256s=[
            row["score_integrity_sha256"] for row in rows
        ],
        method_id=method_id,
        selection_unit_sha256=selection_sha,
    )
    return {
        "checkpoint_content_sha256": checkpoint_sha,
        "complete_roster_certificate_subject_sha256": subject,
        "completed_optimizer_updates": step,
        "domain_id": domain_id,
        "executable_configuration_sha256": executable_sha,
        "group_roster_sha256": roster,
        "group_scores": rows,
        "method_id": method_id,
        "selection_unit_sha256": selection_sha,
    }


def test_exact_all_or_nothing_field_projection() -> None:
    closures = plan.field_closures()
    assert [row["field_id"] for row in closures] == list(plan.FIELD_IDS)
    assert [row["json_pointer"] for row in closures] == [
        plan.FIELD_POINTERS[field_id] for field_id in plan.FIELD_IDS
    ]
    assert closures[4]["value"] == 4096
    assert all(
        row["status"]
        == "PROPOSED_CLOSED_ALL_OR_NOTHING_PENDING_INDEPENDENT_REVIEW"
        for row in closures
    )


def test_exact_b06_roster_is_derived_from_registry_not_old_b12_aliases() -> None:
    actual = [
        (
            row["method_id"],
            row["domain_id"],
            row["b06_config_sha256"],
            row["registry_kind"],
        )
        for row in plan.executable_configuration_rows()
    ]
    assert actual == _direct_b06_rows()
    assert len(actual) == len(set((row[0], row[1]) for row in actual)) == 22
    literature = [row for row in actual if row[3] == "LITERATURE_FAMILY"]
    assert len(literature) == 8
    assert all(row[0].startswith("B06-") and row[0].endswith("-V1") for row in literature)


def test_f144_factory_integrity_formula_matches_real_r64_production_record() -> None:
    empty = physionet_configuration(())
    score = production_conditional_cks_score((empty,) * 64, empty)
    expected = _domain_digest(
        "heterodiff-production-cks-score-v1",
        {
            "binary64_score_hex": score.binary64_score_hex,
            "domain_id": score.domain_id,
            "draw_count": 64,
            "formal_score_sha256": score.formal_score_sha256,
            "integration_id": score.integration_id,
            "metric_id": score.metric_id,
            "score_direction": score.score_direction,
            "symbolic_event_pair_work_units": (
                score.symbolic_event_pair_work_units
            ),
        },
    )
    assert score._integrity_sha256 == expected


def test_executable_row_digests_bind_every_configuration_component() -> None:
    for row in plan.executable_configuration_rows():
        payload = dict(row)
        claimed = payload.pop("executable_configuration_sha256")
        assert claimed == _domain_digest(
            "heterodiff-f139-f144-f147-executable-method-domain-config-v1",
            payload,
        )
        assert row["f144_semantics_sha256"] == plan.f144_semantics_sha256()
        assert row["f143_completed_optimizer_update_bound"] == 4096


def test_b06_update_and_batch_arithmetic_is_exact() -> None:
    for domain_id in b06.DOMAIN_IDS:
        budget = b06.training_compute_budget(domain_id)["phase_event_count_ceilings"]
        assert budget["TUNING"]["BASE_FORWARD"] == 8 * 1024
        assert budget["TUNING"]["DATA_ADAPTER_RECORD"] == 8 * 1024 * 16
        assert budget["FINAL_TRAINING"]["BASE_FORWARD"] == 256 * 4096
        assert budget["FINAL_TRAINING"]["DATA_ADAPTER_RECORD"] == 256 * 4096 * 16
    assert plan.TUNING_COMPLETED_OPTIMIZER_UPDATES_PER_TRIAL == 1024
    assert plan.F143_MAXIMUM_COMPLETED_OPTIMIZER_UPDATES == 4096
    assert plan.TRAINING_BATCH_SIZE == 16


def test_optimizer_schedule_and_precision_are_exact_and_nonadaptive() -> None:
    values = plan.field_values()
    optimizer = values["F139"]
    assert optimizer["algorithm_class"] == "torch.optim.AdamW"
    assert optimizer["beta1"] == {"denominator": 10, "numerator": 9}
    assert optimizer["beta2"] == {"denominator": 1000, "numerator": 999}
    assert optimizer["epsilon"] == {"denominator": 100000000, "numerator": 1}
    assert optimizer["gradient_accumulation_steps"] == 1
    schedule = values["F140"]
    assert schedule["schedule_kind"] == "CONSTANT_AT_SELECTED_PREDECLARED_CANDIDATE_BASE_RATE"
    assert schedule["adaptive_or_validation_driven_change_permitted"] is False
    assert schedule["warmup_completed_optimizer_updates"] == 0
    precision = values["F141"]
    assert precision["model_parameter_dtype"] == "IEEE754_BINARY32"
    assert precision["f105_group_score_representation"] == "IEEE754_BINARY64_HEX_BOUND"
    assert precision["autocast_permitted"] is False
    assert precision["tf32_permitted"] is False


def test_f142_is_exact_22_domain_local_no_shuffle_contract() -> None:
    value = plan.field_values()["F142"]
    rows = value["method_domain_contracts"]
    assert len(rows) == 22
    for row in rows:
        assert row["batch_size_logical_records"] == 16
        assert row["cross_domain_batch_permitted"] is False
        assert row["implicit_or_random_shuffle_permitted"] is False
        assert row["seed_or_trial_mixing_permitted"] is False
        assert row["test_record_permitted"] is False
        assert row["ordering"] == "CANONICAL_ASCENDING_TRAIN_RECORD_ID_BYTES"
        assert row["minimum_admitted_training_roster_size"] == 16


def test_f147_uses_exact_external_grids_and_singletons_elsewhere() -> None:
    rows = plan.field_values()["F147"]["rows"]
    assert len(rows) == 22
    external = [row for row in rows if row["candidate_grid_kind"] == "EXACT_B06_EXTERNAL_GRID"]
    singleton = [
        row
        for row in rows
        if row["candidate_grid_kind"] == "EXACT_SINGLETON_FROZEN_B06_CONFIGURATION"
    ]
    assert len(external) == 2
    assert len(singleton) == 20
    assert all(row["maximum_trials"] == 8 for row in external)
    assert all(row["maximum_trials"] == 1 for row in singleton)
    assert all(row["b06_global_tuning_trial_ceiling"] == 8 for row in rows)
    registry_external = {
        (row["method_id"], row["domain_id"]): row["tuning_budget"]
        for row in b06.FROZEN_REGISTRY["external_baselines"]
    }
    for row in external:
        budget = registry_external[(row["method_id"], row["domain_id"])]
        assert row["candidate_grid_or_singleton_sha256"] == budget["candidate_grid_sha256"]
        assert row["maximum_trials"] == budget["maximum_trials"]


def test_f144_contract_binds_every_requested_semantic() -> None:
    value = plan.field_values()["F144"]
    assert value["metric_id"] == "TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1"
    assert value["production_integration_id"] == "F105_CKS_BINARY64_PROJECTION_V1"
    assert value["direction"] == "LOWER_IS_BETTER"
    assert value["f134_validation_group_count"] == 128
    assert value["draw_count_per_group"] == 64
    assert value["checkpoint_cadence"] == {
        "every_completed_optimizer_updates": 256,
        "terminal_f143_bound_included": True,
    }
    assert value["equality"] == "EXACT_CANONICAL_BINARY64_HEX_IDENTITY_NO_TOLERANCE"
    assert value["test_data_permitted"] is False
    assert value["checkpoint_tie_rule"] == plan.F146_RULE_ID


def test_structural_f144_known_answer_is_exact_and_unauthenticated() -> None:
    result = plan.validate_structural_checkpoint_validation(_validation_input())
    assert result["aggregate_binary64_hex"] == 1.0.hex()
    assert result["completed_optimizer_updates"] == 256
    assert result["eligible_under_f144_structure"] is True
    assert result["production_history_authenticated"] is False
    assert result["f144_semantics_sha256"] == plan.f144_semantics_sha256()
    assert (
        result["complete_roster_certificate_subject_sha256"]
        == _validation_input()["complete_roster_certificate_subject_sha256"]
    )
    assert len(result["structural_receipt_sha256"]) == 64


@pytest.mark.parametrize("step", list(range(256, 4097, 256)))
def test_every_exact_cadence_and_terminal_step_is_admitted(step: int) -> None:
    result = plan.validate_structural_checkpoint_validation(_validation_input(step=step))
    assert result["completed_optimizer_updates"] == step


@pytest.mark.parametrize("step", [True, 0, 1, 255, 257, 4097])
def test_nonexact_checkpoint_cadence_refuses(step: object) -> None:
    value = _validation_input()
    value["completed_optimizer_updates"] = step
    with pytest.raises(plan.TrainingCheckpointPlanError):
        plan.validate_structural_checkpoint_validation(value)


def test_group_roster_missing_duplicate_reorder_and_digest_tamper_refuse() -> None:
    missing = _validation_input()
    missing["group_scores"].pop()
    with pytest.raises(plan.TrainingCheckpointPlanError):
        plan.validate_structural_checkpoint_validation(missing)

    duplicate = _validation_input()
    duplicate["group_scores"][1]["group_id_sha256"] = duplicate["group_scores"][0][
        "group_id_sha256"
    ]
    with pytest.raises(plan.TrainingCheckpointPlanError):
        plan.validate_structural_checkpoint_validation(duplicate)

    reordered = _validation_input()
    reordered["group_scores"][0] = {
        "group_id_sha256": reordered["group_scores"][0]["group_id_sha256"],
        "binary64_score_hex": reordered["group_scores"][0]["binary64_score_hex"],
        "ordinal": 0,
        "score_integrity_sha256": reordered["group_scores"][0]["score_integrity_sha256"],
    }
    with pytest.raises(plan.TrainingCheckpointPlanError):
        plan.validate_structural_checkpoint_validation(reordered)

    digest = _validation_input()
    digest["group_roster_sha256"] = "0" * 64
    with pytest.raises(plan.TrainingCheckpointPlanError):
        plan.validate_structural_checkpoint_validation(digest)


def test_f105_factory_group_binding_and_complete_roster_subject_tamper_refuse() -> None:
    factory = _validation_input()
    factory["group_scores"][0]["f105_factory_score_integrity_sha256"] = "0" * 64
    with pytest.raises(plan.TrainingCheckpointPlanError):
        plan.validate_structural_checkpoint_validation(factory)

    group = _validation_input()
    group["group_scores"][0]["score_integrity_sha256"] = "0" * 64
    with pytest.raises(plan.TrainingCheckpointPlanError):
        plan.validate_structural_checkpoint_validation(group)

    subject = _validation_input()
    subject["complete_roster_certificate_subject_sha256"] = "0" * 64
    with pytest.raises(plan.TrainingCheckpointPlanError):
        plan.validate_structural_checkpoint_validation(subject)

    method = _validation_input()
    method["method_id"] = "not-a-b06-method"
    with pytest.raises(plan.TrainingCheckpointPlanError):
        plan.validate_structural_checkpoint_validation(method)


@pytest.mark.parametrize("score_hex", ["nan", "inf", "-inf", "0x1p+0", " 0x1.0p+0"])
def test_nonfinite_or_noncanonical_binary64_refuses(score_hex: str) -> None:
    value = _validation_input()
    value["group_scores"][0]["binary64_score_hex"] = score_hex
    with pytest.raises(plan.TrainingCheckpointPlanError):
        plan.validate_structural_checkpoint_validation(value)


def test_f105_negative_interval_values_are_valid_but_out_of_range_refuses() -> None:
    negative = plan.validate_structural_checkpoint_validation(
        _validation_input(value=-1.0)
    )
    assert negative["aggregate_binary64_hex"] == (-1.0).hex()
    for number in (-2.000000000000001, 1.000000000000001):
        value = _validation_input()
        value["group_scores"][0]["binary64_score_hex"] = number.hex()
        with pytest.raises(plan.TrainingCheckpointPlanError):
            plan.validate_structural_checkpoint_validation(value)


def test_binary64_equality_is_exact_hex_identity_including_signed_zero() -> None:
    assert plan.validation_values_equal(1.0.hex(), 1.0.hex()) is True
    assert plan.validation_values_equal(0.0.hex(), (-0.0).hex()) is False


def test_exact_tree_rejects_bool_integer_and_container_subclasses() -> None:
    value = _validation_input()
    value["completed_optimizer_updates"] = True
    with pytest.raises(plan.TrainingCheckpointPlanError):
        plan.validate_structural_checkpoint_validation(value)

    class DictAlias(dict):
        pass

    with pytest.raises(TypeError):
        plan.validate_plan(DictAlias(plan.plan_semantics()))


def test_plan_builders_return_fresh_values_and_mutation_refuses() -> None:
    first = plan.plan_semantics()
    second = plan.plan_semantics()
    first["field_closures"][0]["value"]["algorithm"] = "SGD"
    assert second == plan.plan_semantics()
    with pytest.raises(plan.TrainingCheckpointPlanError):
        plan.validate_plan(first)


def test_effect_surface_has_no_runtime_or_science_claim() -> None:
    semantics = plan.plan_semantics()
    assert semantics["effects"] == {
        "b08_closed": False,
        "b12_closed": False,
        "blocker_delta": 0,
        "field_delta": 7,
        "formal_test_delta": 0,
        "result_delta": 0,
        "runtime_or_science_executed": False,
        "timetable_task_delta": 1,
    }
    source = SOURCE_PATH.read_text(encoding="ascii")
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert imported_roots.isdisjoint(
        {"os", "pathlib", "random", "secrets", "socket", "subprocess", "numpy", "torch"}
    )


def test_machine_record_and_hash_first_validator_when_present() -> None:
    if not MACHINE_PATH.exists() or not VALIDATOR_PATH.exists():
        pytest.skip("package record not sealed yet")
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), "--root", str(ROOT)],
        cwd="/private/tmp",
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "PASS_F139_F144_F147_SEVEN_FIELDS_ONLY"
