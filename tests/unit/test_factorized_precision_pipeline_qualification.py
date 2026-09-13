"""Bounded local pipeline qualification; no CUDA or paid execution."""
from contextlib import nullcontext
from copy import deepcopy
import math
import time

import pytest
import torch

from heterodiff.experiments import factorized_precision_pipeline_qualification as q
from heterodiff.experiments.factorized_base_precision import PRECISION_POLICY


EXPECTED_CASES = (
    ("R3-PHYS", "association-aware-guide-plus-residual"),
    ("R3-PHYS", "unified-direct-conditioner"),
    ("R4-RETAIL", "association-aware-guide-plus-residual"),
    ("R4-RETAIL", "unified-direct-conditioner"),
)


@pytest.fixture(scope="module")
def actual_report():
    # One fixed real CPU workload is shared by the assertions below.
    previous_threads = torch.get_num_threads()
    previous_deterministic = torch.are_deterministic_algorithms_enabled()
    previous_warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    previous_rng = torch.random.get_rng_state().clone()
    report = q.run_local_precision_pipeline_check()
    assert torch.get_num_threads() == previous_threads
    assert torch.are_deterministic_algorithms_enabled() == previous_deterministic
    assert torch.is_deterministic_algorithms_warn_only_enabled() == previous_warn_only
    assert torch.equal(torch.random.get_rng_state(), previous_rng)
    return report


def test_actual_fixed_workload_completes_all_cases_and_steps(actual_report):
    report = actual_report
    assert report["decision"] == "PASS_LOCAL_CPU_PRECISION_PIPELINE_ONLY", report
    assert report["completed_case_count"] == 4
    assert tuple((row["domain_id"], row["method_id"]) for row in report["cases"]) == EXPECTED_CASES
    assert report["progress"]["stage"] == "COMPLETE"
    for name in ("base_updates_begun", "base_updates_completed",
                 "conditional_updates_begun", "conditional_updates_completed"):
        assert report["progress"][name] == 16
    assert report["bounds"]["fresh_runs_per_case"] == 2
    assert report["bounds"]["base_updates"] == report["bounds"]["conditional_updates"] == 16
    assert report["bounds"]["maximum_seconds_soft"] == 120
    assert report["bounds"]["maximum_memory_bytes_soft"] == 2 * 1024**3
    assert not report["bounds"]["hard_deadline_or_memory_quota_claimed"]
    assert math.isfinite(report["elapsed_seconds"]) and report["elapsed_seconds"] <= 120


def test_actual_replay_hash_covers_full_paths_optimizer_states_and_diagnostics(actual_report):
    for row in actual_report["cases"]:
        run = row["run"]
        assert row["fresh_full_run_exact_replay"]
        assert row["full_run_sha256"] == q._digest(run)
        assert run["base_frozen_during_conditional_work"] and run["sampler_did_not_mutate_models"]
        assert run["candidate_population_law_id"] != run["legacy_population_law_id"]
        assert run["candidate_population_law_id"].startswith("device-factorized-base-precision-v1-")
        for field in ("base_optimizer_snapshot", "conditional_optimizer_snapshot"):
            snapshot = run[field]
            assert snapshot["steps_match_actual_non_none_gradients"]
            assert snapshot["parameters_and_moments_dtype"] == "FP32"
            assert set(snapshot["parameter_tensor_step_histogram"]) <= {"0", "1", "2"}
            assert len(snapshot["parameters_moments_and_steps_sha256"]) == 64
        altered = deepcopy(run)
        altered["paired_paths"][0]["full_diagnostics_sha256"] = "f" * 64
        assert q._digest(altered) != row["full_run_sha256"]


def test_actual_paths_exercise_separate_streams_hold_and_record_true_activity(actual_report):
    all_paths = []
    for row in actual_report["cases"]:
        run = row["run"]
        paired = run["paired_paths"]
        assert len(paired) == 2
        assert paired[0]["stream_binding_sha256"] != paired[1]["stream_binding_sha256"]
        assert all(path["reference_initializer"] for path in paired)
        assert set(run["conditional_paths"]) == {"retained", "overflow"}
        assert all(not path["reference_initializer"] for path in run["conditional_paths"].values())
        assert len(run["conditional_source_paths"]) == 4
        paths = paired + run["conditional_source_paths"] + list(run["conditional_paths"].values())
        all_paths.extend(paths)
        for path in paths:
            assert path["base_precision_policy"] == PRECISION_POLICY
            assert path["grid"][0] == 0. and path["grid"][-1] == 1.
            assert .75 in path["grid"]
            assert path["cardinalities"][-1] == path["cardinalities"][-2]
            assert all(0 <= count <= 4 for count in path["cardinalities"])
            assert not path["exact_continuous_time_law_claimed"]
            assert len(path["full_diagnostics_sha256"]) == 64
    activity = actual_report["path_activity_first_runs_only"]
    assert activity["recorded_paths"] == len(all_paths) == 32
    for field in ("accepted_births", "accepted_deaths", "jump_candidates"):
        assert activity[field] == sum(path[field] for path in all_paths)
    assert activity["accepted_births"] + activity["accepted_deaths"] > 0


def test_actual_scripted_birth_death_controls_are_not_claimed_as_path_frequencies(actual_report):
    assert actual_report["bounds"]["scripted_single_jump_diagnostic_operations"] == 16
    for row in actual_report["cases"]:
        record = row["run"]["fixed_jump_controls"]
        assert record["scripted_streams_not_scientific_draws"] is True
        assert record["scope"] == "BASE_ONLY_ACCEPTED_JUMP_CONTROL_NOT_CONDITIONAL_PATH_FREQUENCY"
        assert set(record["controls"]) == {"birth", "death"}
        for kind, source_count, destination_count in (("birth", 0, 1), ("death", 4, 3)):
            control = record["controls"][kind]
            assert control["source_count"] == source_count
            assert control["destination_count"] == destination_count
            counts = control["counts"]
            assert counts["jump_candidates"] == counts["accepted_jumps"] == counts["accepted_" + kind] == 1
            assert len(control["state_and_journal_sha256"]) == 64


def test_actual_fixed_input_controls_do_not_claim_same_seed_law_coupling(actual_report):
    for row in actual_report["cases"]:
        controls = row["run"]["fixed_input_controls"]
        assert controls["candidate_snapshot_exact_replay"]
        assert controls["candidate_snapshot_maximum_difference"] == 0.
        assert controls["common_inputs"] == "EXPLICIT_STATE_AND_FIXED_BROWNIAN_INCREMENT_NOT_POPULATION_RUN_SEED"
        assert controls["continuous_coordinate_motion_exercised"]
        assert controls["duplicate_occurrences_preserved"]
        assert not controls["legacy_same_weights_fixed_input_drift"]["gates_candidate_completion"]
    scope = actual_report["scope"]
    assert scope["local_cpu_only"] and scope["synthetic_only"]
    for field in ("real_data_accessed", "explicit_CUDA_query_or_execution_requested",
                  "cloud_jobs_launched", "files_written", "packages_installed",
                  "scientific_training_or_convergence_claimed", "F105_executed",
                  "installed_release_qualified", "full_pipeline_GPU_qualified",
                  "legacy_default_or_acceptance_tolerances_changed",
                  "equal_seeds_across_different_population_laws_claimed_as_coupling"):
        assert scope[field] is False


def fake_run_record():
    def path(ordinal, reference):
        return {"accepted_births": 1, "accepted_deaths": 1, "jump_candidates": 2,
                "base_precision_policy": PRECISION_POLICY, "reference_initializer": reference,
                "stream_binding_sha256": str(ordinal) * 64, "full_diagnostics_sha256": "a" * 64,
                "state_grid_sha256": "b" * 64, "grid": q.GRID,
                "cardinalities": [1, 2, 1, 1, 1], "exact_continuous_time_law_claimed": False}
    return {"paired_paths": [path(1, True), path(2, True)],
            "conditional_source_paths": [path(i, True) for i in (5, 6, 7, 8)],
            "conditional_paths": {"retained": path(3, False), "overflow": path(4, False)},
            "base_updates": [{"base_precision_policy": PRECISION_POLICY}] * 2,
            "conditional_updates": [{"base_precision_policy": PRECISION_POLICY}] * 2,
            "fixed_input_controls": {"candidate_snapshot_exact_replay": True},
            "base_frozen_during_conditional_work": True, "sampler_did_not_mutate_models": True}


@pytest.fixture
def fake_execution(monkeypatch):
    class Budget:
        def __init__(self, request):
            self.started = time.perf_counter()
        def check(self):
            pass
    def run(domain, method, budget, progress):
        for key in ("base_updates_begun", "base_updates_completed",
                    "conditional_updates_begun", "conditional_updates_completed"):
            progress[key] += 2
        return fake_run_record()
    monkeypatch.setattr(q, "_Budget", Budget)
    monkeypatch.setattr(q, "_numerical_policy", lambda request: nullcontext())
    monkeypatch.setattr(q, "_run", run)
    return run


def assert_stopped(report, message):
    assert report["decision"] == "STOP_LOCAL_PRECISION_PIPELINE_INCOMPLETE", report
    assert message in report["error_diagnostics"]["message"], report
    assert report["progress"]["stage"] != "COMPLETE"


def test_valid_fake_complete_evidence_control_reaches_pass(fake_execution):
    report = q.run_local_precision_pipeline_check()
    assert report["decision"] == "PASS_LOCAL_CPU_PRECISION_PIPELINE_ONLY", report
    assert report["completed_case_count"] == 4
    assert report["path_activity_first_runs_only"] == {
        "recorded_paths": 32, "accepted_births": 32, "accepted_deaths": 32, "jump_candidates": 64}


def test_missing_final_case_cannot_pass(fake_execution, monkeypatch):
    def stopped(domain, method, budget, progress):
        if (domain, method) == EXPECTED_CASES[-1]:
            raise RuntimeError("injected final case failure")
        return fake_execution(domain, method, budget, progress)
    monkeypatch.setattr(q, "_run", stopped)
    report = q.run_local_precision_pipeline_check()
    assert_stopped(report, "injected final case failure")
    assert report["completed_case_count"] == 3
    assert report["progress"]["stage"] != "COMPLETE"


def test_duplicate_case_roster_cannot_replace_required_domains_and_methods(fake_execution, monkeypatch):
    monkeypatch.setattr(q, "CASE_ROSTER", (EXPECTED_CASES[0],) * 4)
    report = q.run_local_precision_pipeline_check()
    assert_stopped(report, "invalid fixed four-case roster")
    assert report["completed_case_count"] == 0


@pytest.mark.parametrize("field", ["base_updates_begun", "base_updates_completed",
                                  "conditional_updates_begun", "conditional_updates_completed"])
def test_wrong_optimizer_step_count_cannot_pass(fake_execution, monkeypatch, field):
    def wrong(domain, method, budget, progress):
        result = fake_execution(domain, method, budget, progress)
        progress[field] += 1
        return result
    monkeypatch.setattr(q, "_run", wrong)
    assert_stopped(q.run_local_precision_pipeline_check(), "incomplete local training step count")


def test_changed_full_diagnostics_replay_cannot_pass(fake_execution, monkeypatch):
    calls = [0]
    def different(domain, method, budget, progress):
        result = fake_execution(domain, method, budget, progress)
        calls[0] += 1
        if calls[0] % 2 == 0:
            result["paired_paths"][0]["full_diagnostics_sha256"] = "c" * 64
        return result
    monkeypatch.setattr(q, "_run", different)
    report = q.run_local_precision_pipeline_check()
    assert_stopped(report, "fresh CPU full-pipeline replay differs")
    assert report["completed_case_count"] == 0


def test_nonfinite_run_payload_cannot_pass(fake_execution, monkeypatch):
    shared = fake_run_record()
    shared["nonfinite_probe"] = float("nan")
    def nonfinite(domain, method, budget, progress):
        fake_execution(domain, method, budget, progress)
        return shared
    monkeypatch.setattr(q, "_run", nonfinite)
    report = q.run_local_precision_pipeline_check()
    assert_stopped(report, "JSON compliant")
    assert report["completed_case_count"] == 0


@pytest.mark.parametrize("failure", ["soft wall-clock bound exceeded", "process peak RSS exceeded fixed memory bound"])
def test_budget_error_cannot_be_relabelled_complete(fake_execution, monkeypatch, failure):
    class FailedBudget:
        def __init__(self, request): self.started = time.perf_counter()
        def check(self): raise RuntimeError(failure)
    monkeypatch.setattr(q, "_Budget", FailedBudget)
    report = q.run_local_precision_pipeline_check()
    assert_stopped(report, failure)
    assert report["completed_case_count"] == 0


def test_missing_aggregate_jump_activity_cannot_pass(fake_execution, monkeypatch):
    def no_activity(domain, method, budget, progress):
        result = fake_execution(domain, method, budget, progress)
        for path in result["paired_paths"] + result["conditional_source_paths"] + list(result["conditional_paths"].values()):
            path["accepted_births"] = path["accepted_deaths"] = 0
        return result
    monkeypatch.setattr(q, "_run", no_activity)
    report = q.run_local_precision_pipeline_check()
    assert_stopped(report, "generated paths did not exercise any accepted jumps")


def test_zero_observed_births_are_reported_without_imputing_scripted_counts(fake_execution, monkeypatch):
    def zero_births(domain, method, budget, progress):
        result = fake_execution(domain, method, budget, progress)
        for path in result["paired_paths"] + result["conditional_source_paths"] + list(result["conditional_paths"].values()):
            path["accepted_births"] = 0
        return result
    monkeypatch.setattr(q, "_run", zero_births)
    report = q.run_local_precision_pipeline_check()
    assert report["decision"] == "PASS_LOCAL_CPU_PRECISION_PIPELINE_ONLY"
    assert report["path_activity_first_runs_only"]["accepted_births"] == 0
    assert report["path_activity_first_runs_only"]["accepted_deaths"] == 32


def test_missing_conditional_source_path_record_cannot_pass(fake_execution, monkeypatch):
    def missing(domain, method, budget, progress):
        result = fake_execution(domain, method, budget, progress)
        result["conditional_source_paths"].pop()
        return result
    monkeypatch.setattr(q, "_run", missing)
    assert_stopped(q.run_local_precision_pipeline_check(), "incomplete full-path record count")


def test_path_summary_hash_covers_unprojected_diagnostics_too():
    from heterodiff.processes.factorized_hybrid_sampler import FactorizedTrajectory
    diagnostics = {"accepted_birth": 0, "accepted_death": 0, "jump_candidates": 0,
                   "reference_pi_n_initializer": True, "stream_binding_sha256": "a" * 64,
                   "base_precision_policy": PRECISION_POLICY,
                   "jump_journal": (), "stream_requests": 7}
    path = FactorizedTrajectory(q.GRID, ((),) * len(q.GRID), diagnostics)
    first = q._path_summary(path, "R3-PHYS")
    path.diagnostics["stream_requests"] = 8
    second = q._path_summary(path, "R3-PHYS")
    assert first["state_grid_sha256"] == second["state_grid_sha256"]
    assert first["full_diagnostics_sha256"] != second["full_diagnostics_sha256"]
    assert second["full_diagnostics_sha256"] == q._digest(path.diagnostics)


def tiny_model():
    model = torch.nn.Linear(2, 1, dtype=torch.float32, device="cpu")
    model.register_parameter("unused", torch.nn.Parameter(torch.ones(1, dtype=torch.float32, device="cpu")))
    return model


def test_optimizer_tracker_preserves_legitimate_none_gradient_branches():
    model = tiny_model()
    optimizer = q._optimizer(model)
    counts = {name: 0 for name, _ in model.named_parameters()}
    optimizer.zero_grad(set_to_none=True)
    model(torch.ones(1, 2)).sum().backward()
    q._gradient_steps(model, counts)
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    model.bias.sum().backward()
    q._gradient_steps(model, counts)
    optimizer.step()
    assert counts == {"weight": 1, "bias": 2, "unused": 0}
    report = q._optimizer_snapshot(model, optimizer, counts)
    assert report["steps_match_actual_non_none_gradients"]
    assert report["parameter_tensor_step_histogram"] == {"1": 1, "2": 1, "0": 1}


def test_zero_gradient_is_distinct_from_absent_gradient_for_step_tracking():
    model = tiny_model()
    optimizer = q._optimizer(model)
    counts = {name: 0 for name, _ in model.named_parameters()}
    (model.weight * 0).sum().backward()
    q._gradient_steps(model, counts)
    optimizer.step()
    assert counts == {"weight": 1, "bias": 0, "unused": 0}
    assert q._optimizer_snapshot(model, optimizer, counts)["parameter_tensor_step_histogram"] == {"1": 1, "0": 2}


def test_all_unused_optimizer_parameters_need_no_synthetic_state():
    model = tiny_model()
    optimizer = q._optimizer(model)
    counts = {name: 0 for name, _ in model.named_parameters()}
    report = q._optimizer_snapshot(model, optimizer, counts)
    assert report["parameter_tensor_step_histogram"] == {"0": 3}
    assert not optimizer.state


@pytest.mark.parametrize("tamper", ["unused_state", "wrong_step", "nonfinite_moment", "nonfinite_parameter"])
def test_optimizer_snapshot_rejects_inconsistent_or_nonfinite_state(tamper):
    model = tiny_model()
    optimizer = q._optimizer(model)
    model(torch.ones(1, 2)).sum().backward()
    counts = {name: int(p.grad is not None) for name, p in model.named_parameters()}
    optimizer.step()
    if tamper == "unused_state":
        optimizer.state[model.unused]["step"] = torch.tensor(1.)
    elif tamper == "wrong_step":
        optimizer.state[model.weight]["step"].fill_(4)
    elif tamper == "nonfinite_moment":
        optimizer.state[model.weight]["exp_avg"].fill_(float("nan"))
    else:
        with torch.no_grad(): model.weight.fill_(float("inf"))
    with pytest.raises(ValueError):
        q._optimizer_snapshot(model, optimizer, counts)
