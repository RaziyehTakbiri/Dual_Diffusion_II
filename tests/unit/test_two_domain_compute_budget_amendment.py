from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from heterodiff.experiments import two_domain_baseline_registry as b06
from heterodiff.experiments import two_domain_training_checkpoint_plan as training
from heterodiff.experiments import two_domain_compute_budget_amendment as amendment
from heterodiff.experiments.matched_total_compute import PHASES, RESOURCE_EVENTS, exact_compute_cost


@pytest.fixture(scope="module")
def report():
    return amendment.build_budget_amendment()


def test_complete_roster_and_nonclosure_are_explicit(report):
    assert len(report["method_domain_workloads"]) == 22
    assert len(report["primary_pair_ceiling_proposals"]) == 4
    assert report["tuning_trial_count_across_all_rows"] == 36
    assert report["scheduled_final_seed_runs_across_all_rows"] == 5632
    assert not report["role_rows_deduplicated_or_free_compute_claimed"]
    assert not report["f066_f072_or_b06_closed"]
    assert not report["budgets_adopted_or_old_frozen_records_changed"]
    assert not report["paid_job_launch_or_training_authorized"]


def test_all_frozen_schedules_and_trial_limits_preserved(report):
    original = {(r["method_id"], r["domain_id"]): r for r in training.executable_configuration_rows()}
    for row in report["method_domain_workloads"]:
        identity = (row["method_id"], row["domain_id"])
        assert row["b06_config_sha256"] == original[identity]["b06_config_sha256"]
        assert row["batch_size"] == 16
        assert row["final_updates_per_seed"] == 4096
        assert row["final_checkpoint_update_indices"] == list(range(256, 4097, 256))
        assert row["groups_per_validation_pass"] == 128
        assert row["draws_per_group"] == 64
        assert row["training_seed_count"] == 256
        assert row["tuning"]["updates_per_trial"] == 1024
        assert row["tuning"]["checkpoint_update_indices_per_trial"] == [256, 512, 768, 1024]
        assert row["tuning"]["maximum_trials"] == original[identity]["tuning_maximum_trials"]
        assert row["pilot_empirical_runs"] == row["additional_failure_reserve_runs"] == 0


def test_required_logical_validation_work_is_not_gpu_calls(report):
    for row in report["method_domain_workloads"]:
        per_seed = row["per_seed_final_validation"]
        final = row["final_training_roster"]
        assert per_seed["checkpoint_validation_passes"] == 16
        assert per_seed["group_score_calls"] == 2048
        assert per_seed["generated_conditional_draws"] == 131072
        assert final["scheduled_optimizer_updates"] == 1048576
        assert final["logical_training_record_visits"] == 16777216
        assert final["validation"]["generated_conditional_draws"] == 33554432
        assert final["validation"]["cks_unique_configuration_pair_evaluations"] == 524288 * 2080
        assert final["validation"]["actual_cks_symbolic_event_pair_work"] is None
        assert final["validation"]["actual_model_forward_calls"] is None
        assert final["validation"]["gpu_kernel_launches"] is None
        if row["registry_kind"] == "PRIMARY":
            assert per_seed["logical_reverse_sample_path_steps"] == 33554432
            assert final["validation"]["logical_reverse_sample_path_steps"] == 8589934592
        else:
            assert per_seed["logical_reverse_sample_path_steps"] is None
            assert not row["optimizer_applicability_for_removed_component_controls_verified"]


def test_tuning_validation_covers_singletons_and_eight_trial_external_grids(report):
    for row in report["method_domain_workloads"]:
        tuning = row["tuning"]
        trials = 8 if row["registry_kind"] == "EXTERNAL_BASELINE" else 1
        assert tuning["maximum_trials"] == trials
        assert tuning["scheduled_optimizer_updates_at_trial_cap"] == trials * 1024
        assert tuning["logical_training_record_visits_at_trial_cap"] == trials * 16384
        assert tuning["validation_at_trial_cap"]["group_score_calls"] == trials * 512
        assert tuning["validation_at_trial_cap"]["generated_conditional_draws"] == trials * 32768


@pytest.mark.parametrize("domain", b06.DOMAIN_IDS)
def test_primary_proposal_is_equal_and_preserves_every_old_allowance(report, domain):
    pair = [row for row in report["primary_pair_ceiling_proposals"] if row["domain_id"] == domain]
    assert len(pair) == 2
    assert pair[0]["proposed_combined_phase_event_ceiling"] == pair[1]["proposed_combined_phase_event_ceiling"]
    for proposal in pair:
        old = proposal["original_combined_phase_event_envelope"]
        extra = proposal["additional_checkpoint_validation_allowance"]
        new = proposal["proposed_combined_phase_event_ceiling"]
        assert tuple(new) == PHASES
        for phase in PHASES:
            assert tuple(new[phase]) == RESOURCE_EVENTS
            for event in RESOURCE_EVENTS:
                assert type(new[phase][event]) is int
                assert new[phase][event] == old[phase][event] + extra[phase][event]
        assert extra["FINAL_TRAINING"]["ODE_OR_SDE_STEP"] == 8589934592
        assert new["FINAL_TRAINING"]["ODE_OR_SDE_STEP"] == 8594128896
        assert extra["FINAL_TRAINING"]["METRIC_DRAW_EVALUATION"] == 2147483648
        assert extra["TUNING"]["ODE_OR_SDE_STEP"] == 8388608
        assert new["TUNING"]["ODE_OR_SDE_STEP"] == 8421376
        assert new["TUNING"]["METRIC_DRAW_EVALUATION"] == 2098176
        assert extra["PILOT"] == {event: 0 for event in RESOURCE_EVENTS}
        assert extra["CONFIRMATORY_INFERENCE"] == {event: 0 for event in RESOURCE_EVENTS}
        assert proposal["f147_trial_limit_unchanged"] == 1
        assert new["TUNING"]["CONDITIONER_BACKWARD"] == 8192
        assert not proposal["approved_for_execution_or_spend"]


def test_metric_and_adapter_allowances_follow_existing_b06_convention(report):
    for proposal in report["primary_pair_ceiling_proposals"]:
        domain = proposal["domain_id"]
        extra = proposal["additional_checkpoint_validation_allowance"]
        assert extra["FINAL_TRAINING"]["DATA_ADAPTER_RECORD"] == 33554432 * b06.MAXIMUM_EVENTS_BY_DOMAIN[domain]
        assert extra["TUNING"]["DATA_ADAPTER_RECORD"] == 32768 * b06.MAXIMUM_EVENTS_BY_DOMAIN[domain]
        assert extra["FINAL_TRAINING"]["BASE_BACKWARD"] == 0
        assert extra["FINAL_TRAINING"]["CONDITIONER_BACKWARD"] == 0
        assert extra["FINAL_TRAINING"]["GUIDE_EVALUATION"] == 8589934592


def test_scalar_and_hard_axis_values_are_unknown_not_unit_weight_fabrications(report):
    for proposal in report["primary_pair_ceiling_proposals"]:
        for name in ("weights", "scalar_ceiling", "wall_seconds", "gpu_hours", "peak_host_bytes", "peak_device_bytes", "storage_bytes", "f157_aggregate_model_evaluation_ceiling", "parameter_count_hard_axis_ceiling"):
            assert proposal[name] is None
        # Synthetic arithmetic qualification only, never part of the proposal.
        result = exact_compute_cost(proposal["proposed_combined_phase_event_ceiling"], {event: 1 for event in RESOURCE_EVENTS})
        assert result["total_cost"]["denominator"] == 1


@pytest.mark.parametrize("identity", [("unknown", b06.DOMAIN_IDS[0]), (b06.PRIMARY_METHOD_IDS[0], "unknown"), (True, b06.DOMAIN_IDS[0])])
def test_unknown_and_nonstring_identity_rejected(identity):
    with pytest.raises(amendment.BudgetAmendmentError):
        amendment.training_run_workload(*identity)


def test_nonprimary_event_ceiling_is_not_invented():
    row = next(r for r in training.executable_configuration_rows() if r["registry_kind"] == "EXTERNAL_BASELINE")
    with pytest.raises(amendment.BudgetAmendmentError, match="Only primary"):
        amendment.proposed_primary_phase_ceiling(row["method_id"], row["domain_id"])


def test_parent_objects_and_frozen_records_unchanged_and_outputs_detached():
    root = Path(__file__).resolve().parents[2]
    files = [root / "research/fixtures" / name for name in (
        "manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json",
        "manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.json")]
    before_files = [p.read_bytes() for p in files]
    before = deepcopy(b06.FROZEN_REGISTRY)
    first = amendment.build_budget_amendment()
    first["method_domain_workloads"][0]["batch_size"] = 999
    second = amendment.build_budget_amendment()
    assert all(r["batch_size"] == 16 for r in second["method_domain_workloads"])
    assert b06.FROZEN_REGISTRY == before
    assert [p.read_bytes() for p in files] == before_files
    sha = second.pop("record_sha256")
    assert sha == hashlib.sha256(json.dumps(second, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")).hexdigest()


def test_derivation_matches_frozen_fixture_fields(report):
    root = Path(__file__).resolve().parents[2]
    fixture = json.loads((root / "research/fixtures/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json").read_bytes())
    fields = {row["field_id"]: row["value"] for row in fixture["field_closures"]}
    for proposal in report["primary_pair_ceiling_proposals"]:
        method = proposal["method_id"]
        domain = proposal["domain_id"]
        field = "F066" if method == b06.PRIMARY_METHOD_IDS[0] else "F072"
        for phase in ("PILOT", "TUNING", "FINAL_TRAINING"):
            assert proposal["original_combined_phase_event_envelope"][phase] == fields[field][domain]["phase_event_count_ceilings"][phase]
        parameter_field = "F065" if method == b06.PRIMARY_METHOD_IDS[0] else "F071"
        qualification = proposal["conditional_training_accounting"]
        assert qualification["historical_base_and_conditioner_parameter_counts"] == fields[parameter_field][domain]


def test_additional_nuisance_and_encoder_counts_not_chosen_or_double_counted(report):
    expected = {
        b06.PHYSIONET_DOMAIN_ID: (105601, 211202),
        b06.RETAIL_DOMAIN_ID: (92545, 185090),
    }
    for proposal in report["primary_pair_ceiling_proposals"]:
        qualification = proposal["conditional_training_accounting"]
        one, total = expected[proposal["domain_id"]]
        assert qualification["historical_base_and_conditioner_parameter_counts"] == {
            "frozen_unconditional_base": one, "trainable_conditioner": one, "total": total,
        }
        assert qualification["already_counted_internal_context_mlp_parameters_per_module"] == 24960
        assert qualification["internal_context_mlp_already_in_both_base_and_conditioner_counts"]
        assert not qualification["raw_observation_task_context_feature_encoder_is_the_counted_internal_mlp"]
        for field in ("additional_unique_nuisance_parameters", "additional_unique_raw_encoder_parameters",
                      "successor_unique_parameter_total", "successor_frozen_and_trainable_parameter_partition"):
            assert qualification[field] is None
        assert not qualification["historical_configuration_or_parameter_fields_changed"]
        assert not qualification["prospective_configuration_or_parameter_successor_adopted"]
        assert not qualification["primary_pair_parameter_matching_reverified"]
        expected_fields = ["F064", "F065"] if proposal["method_id"] == b06.PRIMARY_METHOD_ID else ["F070", "F071"]
        assert qualification["required_prospective_configuration_and_parameter_fields"] == expected_fields
    assert not report["f064_f065_f070_f071_prospective_successors_adopted"]


def test_paired_loss_call_counts_are_conditional_facts_not_f104_or_gpu_counts(report):
    for proposal in report["primary_pair_ceiling_proposals"]:
        qualification = proposal["conditional_training_accounting"]
        facts = qualification["implementation_call_structure_not_f104_event_counts"]
        assert facts["condition"] == "ONE_CURRENT_PAIRED_LOSS_CALL_PER_SCHEDULED_OPTIMIZER_UPDATE"
        assert facts["call_count_unit"] == "BATCHED_FORWARD_PASS_NOT_PER_RECORD_EVALUATION"
        assert facts["logical_examples_per_class_forward_pass"] == 16
        assert facts["logical_classifier_evaluations_per_update"] == 32
        assert facts["logical_nuisance_evaluations_per_update"] == 32
        assert facts["classifier_calls_per_update"] == facts["nuisance_calls_per_update"] == 2
        assert facts["backbone_calls_per_valid_shared_time_update"] == [0, 2]
        assert facts["clean_hold_may_skip_backbone_but_not_nuisance"]
        for prefix in ("classifier", "nuisance"):
            assert facts[prefix + "_calls_per_final_training_seed"] == 8192
            assert facts[prefix + "_calls_complete_final_seed_roster"] == 2097152
            assert facts[prefix + "_calls_tuning_trial_roster"] == 2048
        assert facts["nuisance_excluded_from_current_physical_potential_surface"]
        assert not facts["nuisance_charged_automatically_per_reverse_step"]
        assert not facts["actual_execution_observed"]
        assert not qualification["f104_weights_or_scalar_cost_inferred_from_calls"]
        assert not qualification["f157_aggregate_ceiling_inferred_from_calls"]
        assert qualification["all_additional_operations_must_be_prospectively_declared_and_charged"]
        assert not qualification["other_declared_operation_numeric_allowance_chosen"]
        for field in ("classifier_nuisance_forward_backward_f104_event_mapping",
                      "raw_encoder_feature_preprocessing_f104_event_mapping",
                      "old_one_conditioner_forward_per_update_allowance_sufficient"):
            assert qualification[field] is None
        # No automatic event-weight mapping, numeric top-up, or inference charge.
        for phase in PHASES:
            assert proposal["proposed_combined_phase_event_ceiling"][phase]["OTHER_DECLARED_OPERATION"] == 0
            assert proposal["proposed_combined_phase_event_ceiling"][phase] == {
                event: proposal["original_combined_phase_event_envelope"][phase][event]
                + proposal["additional_checkpoint_validation_allowance"][phase][event]
                for event in RESOURCE_EVENTS}
    assert len(report["method_domain_workloads"]) == 22
    assert len(report["primary_pair_ceiling_proposals"]) == 4


def test_classifier_and_parameter_unknowns_are_present_and_detached(report):
    expected = {
        "PAIRED_CLASSIFIER_AND_NUISANCE_FORWARD_BACKWARD_F104_EVENT_MAPPING",
        "RAW_OBSERVATION_TASK_CONTEXT_ENCODER_AND_PREPROCESSING_F104_EVENT_MAPPING",
        "UNIQUE_NUISANCE_AND_RAW_ENCODER_PARAMETER_COUNTS_AND_PARAMETER_COUNT_HARD_AXIS",
        "F064_F065_F070_F071_PROSPECTIVE_CONFIGURATION_AND_PARAMETER_COUNT_SUCCESSORS",
    }
    assert expected <= set(report["unknowns"])
    first = amendment.build_budget_amendment()
    qualification = first["primary_pair_ceiling_proposals"][0]["conditional_training_accounting"]
    qualification["historical_base_and_conditioner_parameter_counts"]["total"] = 1
    qualification["required_prospective_configuration_and_parameter_fields"].clear()
    second = amendment.build_budget_amendment()
    untouched = second["primary_pair_ceiling_proposals"][0]["conditional_training_accounting"]
    assert untouched["historical_base_and_conditioner_parameter_counts"]["total"] > 1
    assert len(untouched["required_prospective_configuration_and_parameter_fields"]) == 2


def test_primary_population_counts_are_separate_from_validation_and_batched_calls(report):
    for row in report["method_domain_workloads"]:
        work = row["joint_product_population_generation"]
        if row["registry_kind"] != "PRIMARY":
            continue
        assert work["condition"] == "ONE_FRESH_JOINT_PRODUCT_PAIR_PER_LOGICAL_TRAINING_EXAMPLE"
        assert work["primary_pair_workload_applicability"]
        assert work["complete_learned_base_trajectories_per_training_example"] == 2
        assert work["branches_share_task_context_and_query_time"]
        assert work["branch_random_streams_are_separate"]
        assert work["nominal_reverse_steps_per_complete_trajectory"] == 256
        assert work["per_optimizer_update"] == {
            "scheduled_optimizer_updates": 1,
            "logical_training_examples": 16,
            "complete_learned_base_trajectories": 32,
            "nominal_reverse_sample_path_steps": 8192,
        }
        assert work["per_final_training_seed"] == {
            "scheduled_optimizer_updates": 4096,
            "logical_training_examples": 65536,
            "complete_learned_base_trajectories": 131072,
            "nominal_reverse_sample_path_steps": 33554432,
        }
        final = work["complete_final_training_seed_roster"]
        assert final == {
            "scheduled_optimizer_updates": 1048576,
            "logical_training_examples": 16777216,
            "complete_learned_base_trajectories": 33554432,
            "nominal_reverse_sample_path_steps": 8589934592,
        }
        assert work["population_work_is_separate_from_checkpoint_validation"]
        assert work["reference_initializer_and_observation_callback_calls_each"] == {
            "per_optimizer_update": 32,
            "per_final_training_seed": 131072,
            "complete_final_training_seed_roster": 33554432,
            "tuning_trial_roster_at_cap": 32768,
        }
        assert (final["nominal_reverse_sample_path_steps"]
                + row["final_training_roster"]["validation"]["logical_reverse_sample_path_steps"]
                == 17179869184)
        assert not work["reuse_or_free_population_construction_claimed"]
        assert not work["nominal_steps_are_model_calls_or_gpu_launches"]
        assert not work["actual_execution_or_production_law_qualification_claimed"]


def test_primary_population_tuning_uses_one_trial_not_256_final_training_seeds(report):
    for proposal in report["primary_pair_ceiling_proposals"]:
        work = proposal["joint_product_population_generation"]
        assert work["tuning_scope"] == "ONE_F147_TRIAL_ROSTER_NOT_MULTIPLIED_BY_FINAL_TRAINING_SEEDS"
        assert work["tuning_trial_roster_at_cap"] == {
            "scheduled_optimizer_updates": 1024,
            "logical_training_examples": 16384,
            "complete_learned_base_trajectories": 32768,
            "nominal_reverse_sample_path_steps": 8388608,
        }


def test_population_actual_work_and_nonprimary_algorithm_not_invented(report):
    for row in report["method_domain_workloads"]:
        work = row["joint_product_population_generation"]
        assert not work["nonprimary_or_control_applicability_inferred"]
        assert work["query_refinement_may_increase_actual_grid_interval_count"]
        for field in ("actual_query_refined_grid_intervals",
                      "actual_active_substeps_rejection_thinning_and_oracle_calls",
                      "actual_initializer_and_observation_kernel_work",
                      "actual_encoder_classifier_nuisance_and_backprop_work",
                      "f104_population_event_mapping", "numeric_population_event_allowance"):
            assert work[field] is None
        if row["registry_kind"] != "PRIMARY":
            assert not work["primary_pair_workload_applicability"]
            for field in ("complete_learned_base_trajectories_per_training_example",
                          "nominal_reverse_steps_per_complete_trajectory",
                          "branches_share_task_context_and_query_time",
                          "branch_random_streams_are_separate", "per_optimizer_update",
                          "reference_initializer_and_observation_callback_calls_each",
                          "per_final_training_seed", "complete_final_training_seed_roster",
                          "tuning_trial_roster_at_cap"):
                assert work[field] is None
    assert {
        "FRESH_JOINT_PRODUCT_POPULATION_GENERATION_F104_EVENT_MAPPING_AND_ALLOWANCE",
        "QUERY_REFINED_GRID_AND_ACTIVE_SUBSTEP_REJECTION_THINNING_ORACLE_WORK",
        "POPULATION_INITIALIZER_AND_OBSERVATION_KERNEL_OPERATION_WORK",
    } <= set(report["unknowns"])


def test_old_plus_validation_ceiling_is_explicitly_incomplete_for_population_work(report):
    for proposal in report["primary_pair_ceiling_proposals"]:
        assert proposal["proposed_event_ceiling_scope"] == "ORIGINAL_PLUS_CHECKPOINT_VALIDATION_ONLY_NOT_FULL_TRAINING"
        assert not proposal["population_work_mapped_into_proposed_event_ceiling"]
        assert not proposal["complete_training_budget_qualification_claimed"]
        assert not proposal["approved_for_execution_or_spend"]
        # New logical work must not be silently counted as a chosen F104 unit.
        for phase in PHASES:
            for event in RESOURCE_EVENTS:
                assert proposal["proposed_combined_phase_event_ceiling"][phase][event] == (
                    proposal["original_combined_phase_event_envelope"][phase][event]
                    + proposal["additional_checkpoint_validation_allowance"][phase][event])
    for domain in b06.DOMAIN_IDS:
        pair = [p for p in report["primary_pair_ceiling_proposals"] if p["domain_id"] == domain]
        assert pair[0]["joint_product_population_generation"] == pair[1]["joint_product_population_generation"]


def test_all22_declared_component_mappings_distinguish_static_contracts_from_algorithms(report):
    rows = report["method_domain_workloads"]
    assert {kind: sum(r["registry_kind"] == kind for r in rows) for kind in
            ("PRIMARY", "CONTROL", "LITERATURE_FAMILY", "EXTERNAL_BASELINE")} == {
                "PRIMARY": 4, "CONTROL": 8, "LITERATURE_FAMILY": 8, "EXTERNAL_BASELINE": 2}
    no_target = []
    for row in rows:
        mapping = row["declared_operation_mapping"]
        assert mapping["config_sha256"] == row["b06_config_sha256"]
        assert mapping["source_interface"]
        assert mapping["remaining_mechanism_decision"]
        assert not mapping["frozen_schedule_changed"]
        assert not mapping["free_cross_role_reuse_or_deduplication_claimed"]
        assert not mapping["upstream_defaults_are_adopted_runtime_settings"]
        if row["registry_kind"] != "PRIMARY":
            assert mapping["actual_nonprimary_sampler_steps"] is None
            assert mapping["implementation_status"].startswith("STATIC_")
        if row["registry_kind"] == "CONTROL" and not mapping["declared_learned_conditioner_target"]:
            no_target.append(row["method_id"])
            assert "WITHOUT_LEARNED_TARGET" in mapping["remaining_mechanism_decision"]
            assert row["final_updates_per_seed"] == 4096  # No implicit control-plan amendment.
    assert len(no_target) == 4
    assert set(no_target) == {"analytic-guide-only-residual-removed", "unconditional-base-sanity-reference"}
    external = [r["declared_operation_mapping"] for r in rows if r["registry_kind"] == "EXTERNAL_BASELINE"]
    assert sorted(m["frozen_upstream_defaults"].get("diffusion_steps", m["frozen_upstream_defaults"].get("sample_steps"))
                  for m in external) == [50, 100]


def test_hybrid_successful_path_counters_account_for_empty_heun_and_jump_clocks():
    result = amendment.hybrid_sampler_operation_counts(
        completed_paths=1, active_intervals=3, held_intervals=2,
        nonempty_heun_halfsteps=4, jump_candidates=5, waiting_time_draws=7,
        accepted_jumps=2, zero_intensity_terminations=1)
    assert result["actual_macrointervals"] == 5
    assert result["heun_halfstep_calls"] == 6
    assert result["physical_value_grad_calls"] == 8
    assert result["physical_value_grad_call_upper_bound"] == 12
    assert result["physical_value_calls"] == 12
    assert result["reference_intensity_preflight_calls"] == 8
    assert result["reference_intensity_preflight_lower_bound"] == 7
    assert result["reference_intensity_preflight_upper_bound"] == 8
    assert result["candidate_draw_calls"] == result["acceptance_uniform_draws"] == 5
    assert result["rejected_jumps"] == 3
    assert result["path_rng_stream_requests_excluding_observation_callback"] == 24
    assert result["normal_scalar_draws_and_coordinate_arithmetic"] is None
    assert not result["failed_or_partial_execution_work_covered"]


def test_intensity_terminal_preflight_not_invented_after_rounded_boundary():
    result = amendment.hybrid_sampler_operation_counts(
        completed_paths=1, active_intervals=1, held_intervals=0,
        nonempty_heun_halfsteps=0, jump_candidates=2, waiting_time_draws=2,
        accepted_jumps=0, zero_intensity_terminations=0)
    assert result["reference_intensity_preflight_calls"] == 2
    assert result["reference_intensity_preflight_upper_bound"] == 3
    assert result["physical_value_grad_calls"] == 0
    result = amendment.hybrid_sampler_operation_counts(
        completed_paths=1, active_intervals=0, held_intervals=1,
        nonempty_heun_halfsteps=0, jump_candidates=0, waiting_time_draws=0, accepted_jumps=0)
    assert result["physical_value_calls"] == result["heun_halfstep_calls"] == 0
    assert result["reference_intensity_preflight_calls"] is None
    assert result["path_rng_stream_requests_excluding_observation_callback"] == 1


@pytest.mark.parametrize("change", [
    {"completed_paths": True}, {"active_intervals": -1}, {"nonempty_heun_halfsteps": 3},
    {"waiting_time_draws": 4}, {"waiting_time_draws": 0}, {"accepted_jumps": 3},
    {"zero_intensity_terminations": 2}, {"completed_paths": 0},
])
def test_inconsistent_sampler_counters_rejected(change):
    arguments = dict(completed_paths=1, active_intervals=1, held_intervals=0,
                     nonempty_heun_halfsteps=1, jump_candidates=1,
                     waiting_time_draws=1, accepted_jumps=0)
    arguments.update(change)
    with pytest.raises(amendment.BudgetAmendmentError):
        amendment.hybrid_sampler_operation_counts(**arguments)


def test_query_refinement_adds_intervals_not_frozen_equivalence():
    result = amendment.hybrid_grid_workload(complete_paths=131072, nominal_intervals=256,
                                            query_refined_paths=131072)
    assert result["nominal_macrointervals"] == 33554432
    assert result["actual_macrointervals_for_supplied_refinement_count"] == 33685504
    assert not result["frozen_numerical_law_preserved_by_refinement"]
    with pytest.raises(amendment.BudgetAmendmentError):
        amendment.hybrid_grid_workload(complete_paths=1, nominal_intervals=10000, query_refined_paths=1)
    with pytest.raises(amendment.BudgetAmendmentError):
        amendment.hybrid_grid_workload(complete_paths=1, nominal_intervals=256, query_refined_paths=2)


def test_potential_counts_distinguish_base_path_conditional_path_and_initializer():
    base = amendment.neural_potential_operation_counts(
        value_calls=7, value_grad_calls=8, include_base=True, conditional=False)
    assert base["base_forward_calls"] == 15
    assert base["condition_observation_encoder_calls"] == base["baseline_callback_calls"] == 0
    conditional = amendment.neural_potential_operation_counts(
        value_calls=7, value_grad_calls=8, include_base=True, conditional=True,
        active_conditional_queries=14)
    assert conditional["base_forward_calls"] == conditional["baseline_callback_calls"] == 15
    assert conditional["condition_observation_encoder_calls"] == 15
    assert conditional["conditional_backbone_forward_calls"] == 14
    assert conditional["nuisance_forward_calls"] == 0
    assert conditional["coordinate_autograd_requests_upper_bound"] == 8
    assert conditional["actual_coordinate_autograd_requests"] is None
    initial = amendment.neural_potential_operation_counts(
        value_calls=4, value_grad_calls=0, include_base=False, conditional=True,
        active_conditional_queries=4)
    assert initial["base_forward_calls"] == initial["nuisance_forward_calls"] == 0
    assert initial["baseline_callback_calls"] == initial["conditional_backbone_forward_calls"] == 4
    with pytest.raises(amendment.BudgetAmendmentError):
        amendment.neural_potential_operation_counts(value_calls=1, value_grad_calls=0,
            include_base=True, conditional=False, active_conditional_queries=1)


def test_rejection_bounds_are_supplied_not_accepted_counts_or_new_caps():
    unknown = amendment.conditional_rejection_workload(completed_draws=64, max_proposals_per_draw=100)
    assert unknown["proposal_count_lower_bound"] == 64
    assert unknown["proposal_count_upper_bound"] == 6400
    assert unknown["actual_initial_factor_value_calls"] is None
    assert unknown["expected_rejection_proposals"] is None
    observed = amendment.conditional_rejection_workload(
        completed_draws=3, max_proposals_per_draw=5, proposal_counts=(1, 5, 2))
    assert observed["actual_reference_configuration_calls"] == 8
    assert observed["actual_initial_factor_value_calls"] == observed["actual_acceptance_uniform_draws"] == 8
    assert observed["base_potential_calls"] == observed["nuisance_calls"] == 0
    assert not observed["cap_adopted_for_science_or_spend"]
    for counts in ((1, 0, 2), (1, 6, 2), (1, True, 2), [1, 2, 3], (1, 2)):
        with pytest.raises(amendment.BudgetAmendmentError):
            amendment.conditional_rejection_workload(completed_draws=3, max_proposals_per_draw=5,
                                                      proposal_counts=counts)


@pytest.mark.parametrize("anchor,global_width,expected_encoder", [(228, 4, 27392), (24, 4, 14336), (4, 5, 13120)])
def test_encoder_parameter_and_dense_shape_arithmetic(anchor, global_width, expected_encoder):
    result = amendment.observation_design_operation_counts(anchor_dimension=anchor,
        global_dimension=global_width, batch_size=16, joint_anchor_count=3, product_anchor_count=5)
    assert result["unique_condition_encoder_parameters"] == expected_encoder
    assert result["additional_unique_parameters"] == 2*expected_encoder+2113
    assert result["all_encoder_dense_layer_calls"] == 16
    assert result["nuisance_head_dense_layer_calls"] == 4
    assert result["all_encoder_dense_mac_terms"] == 2*(8*(anchor*64+4096)+32*((64+global_width)*64+4096))
    assert result["nuisance_head_dense_mac_terms"] == 32*2080
    assert result["pooling_input_elements"] == 2*64*8
    assert result["pooling_normalization_divisions"] == 4*16*64
    assert result["gradient_and_optimizer_scalar_work"] is None
    assert not result["historical_internal_context_mlp_counted_again"]
    assert not result["production_schema_or_parameter_successor_adopted"]


def test_overflow_wrapper_is_separate_addition_without_skipped_retained_encoder():
    result = amendment.overflow_observation_wrapper_counts(batch_size=16, encoder_forward_passes=4)
    assert result["unique_parameters_per_wrapper"] == 4224
    assert result["two_independent_wrappers_unique_parameter_addition"] == 8448
    assert result["additional_dense_mac_terms"] == 4*16*65*64
    assert result["additional_bias_additions"] == result["additional_tanh_elements"] == 4096
    assert not result["retained_encoder_work_avoided_for_overflow_rows"]
    assert not result["production_design_adopted"]


def test_f105_symbolic_formula_matches_actual_factory_cardinality_procedure():
    from types import SimpleNamespace
    from heterodiff.evaluation.two_domain_count_normalized_event_cks_production import _symbolic_work_units
    # Tiny invented cardinalities only: no metric, factory score or dataset read.
    for counts, target in [((0,)*64, 0), ((1,)*64, 1), (tuple(i % 3 for i in range(64)), 4)]:
        draws = tuple(SimpleNamespace(events=(None,)*n) for n in counts)
        expected = _symbolic_work_units(draws, SimpleNamespace(events=(None,)*target))
        result = amendment.f105_symbolic_work_from_cardinalities(counts, target)
        assert result["symbolic_event_pair_work_units"] == expected
        assert result["configuration_kernel_calls"] == 2080
        assert not result["factory_score_evaluated"]
    for invalid in [(0,)*63, (False,)+(0,)*63, (-1,)+(0,)*63, [0]*64]:
        with pytest.raises(amendment.BudgetAmendmentError):
            amendment.f105_symbolic_work_from_cardinalities(invalid, 0)


def test_symbolic_ledger_lists_minimal_unresolved_decisions_not_budget_approval(report):
    assert report["symbolic_operation_ledger"]["all22_method_rows_have_explicit_semantic_mapping"]
    assert not report["symbolic_operation_ledger"]["nonprimary_executable_mechanisms_complete"]
    assert set(report["remaining_decisions"]) == {"scientific_or_implementation", "measurement", "operator"}
    for proposal in report["primary_pair_ceiling_proposals"]:
        calls = proposal["conditional_training_accounting"]["observed_model_pair_call_structure"]
        assert calls["condition_observation_encoder_passes_per_update"] == 2
        assert calls["nuisance_encoder_passes_per_update"] == 2
        assert calls["loss_backward_calls_per_update"] == calls["adamw_step_calls_per_update"] == 1
        assert calls["condition_encoder_is_evaluated_even_when_all_records_are_in_clean_hold"]
        assert not proposal["complete_training_budget_qualification_claimed"]
