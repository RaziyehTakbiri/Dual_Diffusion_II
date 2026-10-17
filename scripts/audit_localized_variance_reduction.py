"""Independent read-only arithmetic audit of the paired label experiment.

Imports hash-bound earlier audit arithmetic and the unchanged backward oracle,
not the new runner, paired-label implementation, learner, or optimizer.
No paths are simulated and no model is fitted. Optional output is exclusive.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import math
from pathlib import Path
import sys

import numpy as np
from threadpoolctl import threadpool_limits

DEPENDENCY_SHA256 = "20b043be40fe6bb03194631f3f46bf27e72a35abc25afedb36da5c7af0bc2cc7"
DEPENDENCY_PATH = Path(__file__).with_name("audit_localized_error_decomposition.py")
if hashlib.sha256(DEPENDENCY_PATH.read_bytes()).hexdigest() != DEPENDENCY_SHA256:
    raise RuntimeError("independent arithmetic dependency binding mismatch")
_spec = importlib.util.spec_from_file_location("independent_localized_audit_arithmetic", DEPENDENCY_PATH)
a = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(a)

ARMS = ("RAW", "RAO_BLACKWELL")
SOURCE_PATHS = (
    "experiments/continuous_localized_variance_reduction.py",
    "experiments/continuous_rao_blackwell_labels.py",
    "experiments/continuous_forward_labels.py",
    "experiments/continuous_localized_learnability.py",
    "models/localized_likelihood_learner.py",
    "experiments/continuous_residual_capacity.py",
    "evaluation/continuous_fiber_grid_target.py",
    "evaluation/continuous_fiber_conditional_benchmark.py",
    "evaluation/continuous_fiber_initialization_diagnostic.py",
)


def expected_process(theta, y):
    return {"theta": theta, "observation_value": y, "selected_probability": 393217 / 524288,
        "death_rate": 1., "continuous_rate": 1., "observation_sd": .5, "contamination": .1}


def audit_protocol(p):
    for key, value in (("schema_version", "continuous-localized-rao-blackwell-comparison-v1"),
            ("methods", list(a.METHODS)), ("seeds", list(a.SEEDS)), ("nested_budgets", list(a.BUDGETS)),
            ("arms", list(ARMS)), ("grid", list(a.GRID)), ("validation_size", 4096),
            ("route_count", 48), ("fit_count", 384), ("dataset_pair_count", 48),
            ("unique_training_skeletons", 393216), ("unique_validation_skeletons", 196608),
            ("unique_total_skeletons", 589824), ("retries", 0), ("threads", 1),
            ("maximum_seconds", 1200), ("tolerances_changed", False),
            ("raw_arm_is_new_paired_control_not_old_archive", True),
            ("equal_flops_random_draws_wall_time_or_actual_optimizer_evaluations_claimed", False),
            ("paired_generation_cost_reported_once_not_standalone_arm_timings", True),
            ("all_fits_frozen_before_backward_oracle", True),
            ("oracle_or_validation_selects_settings_or_stopping", False),
            ("learner_sampler_real_data_GPU_cloud_network_or_release_changed", False)):
        a.equal(p[key], value, "protocol " + key)
    a.equal(p["scenarios"], [{"id": name, "process": expected_process(theta, y)}
        for name, theta, y in a.SCENARIOS], "fixed scenarios")
    a.equal(p["evaluation_coordinates"], np.linspace(-4., 4., 256).tolist(), "fixed evaluation probes")
    a.equal(p["tolerances"], {k: list(v) for k, v in a.TOLERANCES.items()}, "unchanged tolerances")
    a.equal(p["fit"], {"family_cells": 32, "coefficients": 35, "smoothness": 1e-4, "ridge": 1e-6,
        "physical_box": "2*log(M/c)", "initial": "ZERO", "optimizer": "UNCHANGED_fit_likelihood_L_BFGS_B",
        "maxiter": 200, "maxls": 30, "ftol": 1e-12, "gtol": 1e-7}, "unchanged default learner")
    a.equal(p["uncertainty"]["family_failure_probability"], .05, "family alpha")
    a.equal(p["uncertainty"]["unique_noise_comparisons"], 96, "96 data problems")
    a.equal(p["uncertainty"]["same_noise_event_covers_both_methods"], True, "shared method events")


def original_bindings(reader, repo):
    old_dir = repo / "research/fixtures/continuous_localized_learnability_cpu_2026_09_13"
    old = reader.load(old_dir / "report.json")
    a.equal(reader.bindings[old_dir / "report.json"], a.ARCHIVE_HASH, "original report hash")
    protocol = reader.load(old_dir / "protocol.json")
    a.equal(a.digest(protocol), a.ARCHIVE_PROTOCOL_HASH, "original protocol hash")
    a.equal(old["protocol"], protocol, "original protocol contents")
    frozen = [reader.load(old_dir / f"frozen-{i:02d}.json") for i in range(1, 25)]
    barrier = reader.load(old_dir / "freeze-barrier.json")
    a.equal(a.digest(frozen), barrier["frozen_records_sha256"], "original freeze digest")
    a.equal(barrier, old["freeze_barrier"], "original barrier")
    for raw, route in zip(frozen, old["routes"]):
        a.equal({k: route[k] for k in raw}, raw, "original raw fits preserved")
        a.equal(reader.load(old_dir / f"route-{route['ordinal']:02d}.json"), route, "original route preserved")
    designs = {}
    for row in old["datasets"]:
        data = reader.load(old_dir / f"dataset-{row['ordinal']:02d}.json")
        a.equal(a.digest(data), row["record_sha256"], "original data preserved")
        for split, d in enumerate(data["splits"]):
            s, z = np.asarray(d["states"], dtype=np.int64), np.asarray(d["coordinates"], dtype=np.float64)
            a.equal(a.array_digest(s, z, np.asarray(d["labels"], dtype=np.float64)), d["sha256"], "original label hash")
            designs[data["scenario"], data["seed"], data["u"], split] = a.array_digest(s, z)
    return old, designs


def normal_density(difference, variance):
    return np.exp(-difference * difference / (2 * variance)) / np.sqrt(2 * math.pi * variance)


def audit_dataset(d, theta, y, u, size):
    s = np.asarray(d["states"], dtype=np.int64)
    z = np.asarray(d["coordinates"], dtype=np.float64)
    raw, rb, variance = [np.asarray(d[k], dtype=np.float64) for k in
        ("RAW", "RAO_BLACKWELL", "conditional_raw_label_variance")]
    a.equal(s.tolist(), np.tile((0, 1, 2, 2), size // 4).tolist(), "fixed balanced design")
    a.require(z.shape == (size,) and np.isfinite(z).all() and np.all(z[s != 2] == 0)
        and np.max(abs(z), initial=0) <= 4.5, "bounded initial coordinates")
    a.equal(a.array_digest(s, z), d["design_sha256"], "design binding")
    a.equal(a.array_digest(s, z, raw, rb, variance), d["payload_sha256"], "paired arrays binding")
    floor, maximum, _ = a.observation_bounds(theta, y)
    for label in (raw, rb):
        a.require(label.shape == (size,) and np.isfinite(label).all()
            and np.all(label >= floor) and np.all(label <= maximum), "bounded labels")
    a.require(variance.shape == (size,) and np.isfinite(variance).all() and np.all(variance >= 0), "nonnegative saved variance")
    terminal = d["terminal_gaussian_state"]
    ts = np.asarray(terminal["states"], dtype=np.int64)
    m, v, rz = [np.asarray(terminal[k], dtype=np.float64) for k in ("means", "variances", "raw_coordinates")]
    a.require(ts.shape == (size,) and np.isin(ts, (0, 1, 2)).all(), "terminal category roster")
    for x in (m, v, rz):
        a.require(x.shape == (size,) and np.isfinite(x).all() and np.all(x[ts != 2] == 0), "terminal aligned atomic placeholders")
    a.require(np.all(v >= 0), "terminal Gaussian variance")
    active = ts == 2
    rr, br, vr = np.full(size, floor), np.full(size, floor), np.zeros(size)
    rr[active] += .45 * normal_density(y - rz[active], .25)
    signal = normal_density(y - m[active], .25 + v[active])
    br[active] += .45 * signal
    second = normal_density(y - m[active], .125 + v[active]) / (2 * math.sqrt(math.pi) * .5)
    vr[active] = .45 ** 2 * (second - signal * signal)
    a.near(raw, rr, "raw terminal label")
    a.near(rb, br, "conditional Gaussian convolution")
    a.near(variance, vr, "conditional raw second moment variance")
    a.near(raw[active & (v == 0)], rb[active & (v == 0)], "deterministic conditional labels", atol=0, rtol=0)
    counts = {k: np.asarray(values, dtype=np.int64) for k, values in d["per_suffix_counts"].items()}
    for k, values in d["per_suffix_counts"].items():
        a.require(len(values) == size and all(type(x) is int and x >= 0 for x in values), "integer work roster")
        a.equal(int(counts[k].sum()), d["work"][k], "total prefix work " + k)
    a.equal((counts["accepted_births"] + counts["accepted_deaths"]).tolist(),
        counts["accepted_birth_death_events"].tolist(), "accepted work partition")
    a.equal((counts["raw_half_step_normal_draws"] + counts["raw_birth_normal_draws"]).tolist(),
        counts["raw_normal_draws_total"].tolist(), "normal draw partition")
    for k in ("conditional_gaussian_affine_updates", "raw_half_step_normal_draws"):
        a.equal(counts[k].tolist(), counts["continuous_half_step_updates"].tolist(), "matched half-step work")
    for k in ("raw_birth_normal_draws", "conditional_gaussian_birth_resets"):
        a.equal(counts[k].tolist(), counts["selected_births"].tolist(), "selected birth resets")
    a.equal(counts["conditional_gaussian_death_resets"].tolist(), counts["accepted_deaths"].tolist(), "death resets")
    a.equal(counts["skeleton_acceptance_uniform_draws"].tolist(), counts["potential_uniformization_events"].tolist(), "proposal decisions")
    a.equal(counts["skeleton_birth_uniform_draws"].tolist(), counts["accepted_births"].tolist(), "birth category decisions")
    suffix_intervals = 8 - a.GRID.index(u)
    a.equal(counts["skeleton_poisson_draws"].tolist(), [suffix_intervals] * size, "one Poisson count per macro")
    a.equal(((ts != 0).astype(int) - (s != 0).astype(int)).tolist(),
        (counts["accepted_births"] - counts["accepted_deaths"]).tolist(), "occupancy balance")
    a.require(np.all(counts["selected_births"] <= counts["accepted_births"])
        and np.all(counts["accepted_birth_death_events"] <= counts["potential_uniformization_events"])
        and np.all(counts["continuous_half_step_updates"] <= 2 * suffix_intervals), "bounded accepted work")
    a.equal(d["work"]["forward_suffix_count"], size, "suffix work count")
    a.equal(d["work"]["macro_intervals_per_suffix"], suffix_intervals, "remaining macro intervals")
    a.equal(d["work"]["terminal_state_counts"], {name: int(np.sum(ts == i))
        for i, name in enumerate(("EMPTY", "OTHER", "CONTINUOUS"))}, "terminal state work")
    for key, value in (("same_jump_skeleton", True), ("distinct_rng_objects", True),
            ("random_stream_independence_is_callers_responsibility", True),
            ("backward_likelihood_or_score_queried", False), ("conditional_endpoint_sampler_used", False)):
        a.equal(d["work"][key], value, "declared label scope " + key)
    a.require(math.isfinite(d["paired_generation_seconds"]) and d["paired_generation_seconds"] >= 0, "observational generation time")
    a.COUNTS["independent_gaussian_label_rows"] += size
    a.COUNTS["paired_dataset_splits"] += 1
    return s, z, raw, rb, variance, counts


def validation_change(f, b, y, maximum, states):
    values = (np.exp(f) - np.exp(b) - y * (f - b)) / maximum
    variance = math.fsum(float(np.mean(states == s) ** 2 * np.var(values[states == s], ddof=1)
        / np.sum(states == s)) for s in (0, 1, 2))
    return {"mean": float(values.mean()), "stratified_standard_error_descriptive": math.sqrt(variance),
        "negative_means_improved": True, "confidence_interval_or_multiple_testing_claim": False}


def comparison(values, truth):
    result = {}
    for k, (atol, rtol) in a.TOLERANCES.items():
        error = np.asarray(values[k]) - truth[k]
        threshold = atol + rtol * np.abs(truth[k])
        failure = np.abs(error) > threshold
        result[k] = {"count": len(error), "max_abs": float(np.max(abs(error))),
            "rms": float(np.sqrt(np.mean(error ** 2))), "failure_count": int(failure.sum()),
            "passed_pointwise_approximation_tolerance": not bool(failure.any()),
            "atol": atol, "rtol": rtol, "maximum_error_over_threshold": float(np.max(abs(error) / threshold))}
    return result


def check_noise_bound(saved, X, floor, maximum, A, F):
    eps = (maximum - floor) / (len(X) * maximum) * np.sqrt(.5 * np.sum(X * X, axis=0) * math.log(2 * 35 * 96 * 2 / .05))
    radius = min(float(np.linalg.norm(eps)) / 1e-6, 2 * A * math.sqrt(35))
    a.near(saved["gradient_noise_l2_bound"], np.linalg.norm(eps), "simultaneous Hoeffding gradient bound")
    a.near(saved["coefficient_distance_bound_with_box_cap"], radius, "global ridge box radius")
    a.equal(saved["ridge_curvature_lower_bound"], 1e-6, "global ridge modulus")
    a.equal(saved["family_failure_probability"], .05, "global family error")
    for key in ("optimizer_error_bias_and_floating_point_not_included", "raw_and_rb_share_conservative_bound"):
        a.equal(saved[key], True, "bound limitation " + key)
    a.equal(saved["floating_point_interval_certificate"], False, "no interval certificate")
    a.equal(saved["scope"], "EXACT_EMPIRICAL_LABEL_OPTIMUM_VS_SAME_DESIGN_CONDITIONAL_MEAN_OPTIMUM", "noise bound scope")
    for k, matrix in F.items():
        a.tree_near(saved["derivative_responses"][k], {
            "maximum_probe_error_bound": float(np.max(np.linalg.norm(matrix[2:], axis=1)) * radius),
            "rms_probe_error_bound": float(np.linalg.norm(matrix[2:], 2) * radius / 16)}, "derivative bound readback")


def audit(repo, out):
    reader = a.Reader()
    old, old_designs = original_bindings(reader, repo)
    report = reader.load(out / "report.json")
    protocol = reader.load(out / "protocol.json")
    execution = reader.load(out / "execution.json")
    barrier = reader.load(out / "freeze-barrier.json")
    audit_protocol(protocol)
    a.equal(report["protocol"], protocol, "embedded protocol")
    a.equal(a.digest(protocol), report["protocol_sha256"], "report protocol hash")
    a.equal(execution["protocol_sha256"], report["protocol_sha256"], "prefit protocol hash")
    a.equal(execution["before_training"], True, "execution prefit marker")
    a.equal(execution["source_sha256"], report["source_sha256"], "prefit source bindings")
    a.equal(set(report["source_sha256"]), set(SOURCE_PATHS), "complete source roster")
    for mapping in (old["source_sha256"], report["source_sha256"]):
        for relative, sha in mapping.items():
            a.equal(hashlib.sha256((repo / "src/heterodiff" / relative).read_bytes()).hexdigest(), sha, "source unchanged " + relative)
    a.equal(report["decision"], "MATCHED_SKELETON_VARIANCE_REDUCTION_COMPARISON_COMPLETE_REVIEW_ERRORS", "completed decision")
    a.equal(report["completed_routes"], 48, "48 routes")
    a.equal(report["completed_fits"], 384, "384 fits")
    a.require(not (out / "failure.json").exists(), "no terminal failure file")
    frozen = [reader.load(out / f"frozen-{i:02d}.json") for i in range(1, 49)]
    a.equal(a.digest(frozen), barrier["frozen_records_sha256"], "all fits frozen digest")
    a.equal(barrier, report["freeze_barrier"], "barrier payload")
    a.equal((barrier["frozen_routes"], barrier["frozen_models"], barrier["backward_target_queried_during_training"]),
        (48, 384, False), "barrier declaration")
    roster = [(name, seed, method, budget, arm) for name, _, _ in a.SCENARIOS for seed in a.SEEDS
        for method in a.METHODS for budget in a.BUDGETS for arm in ARMS]
    a.equal([(r["scenario"], r["seed"], r["method"], r["train_budget"], r["arm"]) for r in report["routes"]],
        roster, "fixed paired route roster")
    settings = {name: (theta, y) for name, theta, y in a.SCENARIOS}
    datasets = {}
    dataset_roster = [(name, seed, u) for name, _, _ in a.SCENARIOS for seed in a.SEEDS for u in a.GRID[:-1]]
    a.equal([(r["scenario"], r["seed"], r["u"]) for r in report["datasets"]], dataset_roster, "fixed data roster")
    work_totals = a.Counter()
    for index, row in enumerate(report["datasets"], 1):
        a.equal(row["ordinal"], index, "dataset ordinal")
        data = reader.load(out / f"dataset-{index:02d}.json")
        a.equal(a.digest(data), row["record_sha256"], "dataset content binding")
        key = data["scenario"], data["seed"], data["u"]
        a.equal(key, dataset_roster[index - 1], "dataset fixed identity")
        theta, y = settings[key[0]]
        si = [r[0] for r in a.SCENARIOS].index(key[0])
        arrays = []
        for split, d in enumerate(data["splits"]):
            arrays.append(audit_dataset(d, theta, y, key[2], 8192 if split == 0 else 4096))
            a.equal(d["design_sha256"], old_designs[key + (split,)], "original feature design retained")
            a.equal(d["rng_namespace"], [20260913, 731, si, key[1], a.GRID.index(key[2]), split], "declared RNG identity")
            a.equal(row["splits"][split], {k: d[k] for k in row["splits"][split]}, "dataset summary binding")
            for k, values in arrays[-1][-1].items():
                work_totals[k] += int(values.sum())
        datasets[key] = data, arrays
    sys.path.insert(0, str(repo / "src"))
    from heterodiff.evaluation.continuous_fiber_conditional_benchmark import ContinuousFiberSpec
    from heterodiff.evaluation.continuous_fiber_grid_target import ContinuousFiberGridTarget
    rho = 393217 / 524288
    oracles = {name: ContinuousFiberGridTarget(ContinuousFiberSpec(theta=theta, observation_value=y,
        type_probabilities=(1 - rho, rho)), a.GRID) for name, theta, y in a.SCENARIOS}
    es = np.r_[np.array((0, 1), dtype=np.int64), np.full(256, 2, dtype=np.int64)]
    ez = np.r_[0., 0., np.linspace(-4., 4., 256)]
    F = {k: a.features(es, ez, i) for i, k in enumerate(a.TOLERANCES)}
    truths = {(name, u): a.target(o, u, es, ez) for name, o in oracles.items() for u in a.GRID}
    P = a.penalty_matrix()
    evaluated = {}
    for index, (saved, raw_frozen) in enumerate(zip(report["routes"], frozen), 1):
        a.equal(saved["ordinal"], index, "route ordinal")
        a.equal({k: saved[k] for k in raw_frozen}, raw_frozen, "frozen fit content retained")
        a.equal(reader.load(out / f"route-{index:02d}.json"), saved, "individual route binding")
        name, seed, method, budget, arm = roster[index - 1]
        theta, y = settings[name]
        floor, maximum, A = a.observation_bounds(theta, y)
        a.equal(saved["process"], expected_process(theta, y), "route process")
        a.equal(len(saved["nodes"]), 8, "eight fitted nodes")
        a.equal(len(saved["evaluation_nodes"]), 9, "nine evaluation nodes")
        eval_rows = []
        for ni, u in enumerate(a.GRID):
            if u < 1:
                node = saved["nodes"][ni]
                a.equal(node["u"], u, "fit node")
                fit = node["fit"]
                c = np.asarray(fit["physical_coefficients"])
                q = np.asarray(fit["coefficients"])
                a.require(c.shape == (35,) and np.isfinite(c).all() and np.max(abs(c)) <= A, "physical box")
                a.near(c, (1-u)*q, "physical quotient binding")
                a.near(fit["remaining_time"], 1-u, "time gate")
                a.near(fit["physical_coefficient_bound"], A, "observation bound")
                a.near(fit["quotient_coefficient_bound"], A/(1-u), "quotient box")
                data, splits = datasets[name, seed, u]
                s, z, raw, rb, _, counts = splits[0]
                sv, zv, rv, bv, _, _ = splits[1]
                X, XV = a.features(s[:budget], z[:budget]), a.features(sv, zv)
                labels = (raw if arm == "RAW" else rb)[:budget]
                b = a.baseline(theta, y, u, method, s[:budget], z[:budget])["value"]
                baseline_v = a.baseline(theta, y, u, method, sv, zv)["value"]
                weights = np.full(budget, 1/budget)
                J, g = a.risk(c, X, labels, b, weights, maximum, P)
                a.near(fit["final_penalized_risk"], J, "default fitted objective")
                a.near(fit["initial_penalized_risk"], a.risk(np.zeros(35), X, labels, b, weights, maximum, P)[0], "default zero objective")
                projected = g.copy()
                projected[(c <= -A) & (g > 0)] = 0
                projected[(c >= A) & (g < 0)] = 0
                a.near(fit["projected_gradient_max_abs"], np.max(abs(projected)), "default projected gradient")
                gap = max(0., float(g @ c + A * np.sum(abs(g))))
                a.near(node["optimizer_box_gap_upper_bound"], gap, "default box gap")
                a.near(node["optimizer_coefficient_distance_bound"], min(2*A*math.sqrt(35), math.sqrt(2*gap/1e-6)), "default solver distance")
                a.equal(fit["coefficient_boundary_count"], int(np.sum(abs(c) >= A-1e-10)), "boundary control count")
                a.require(0 <= fit["iterations"] <= 200 and fit["function_evaluations"] >= 1, "default solver work limits")
                for k in ("hessian_score_or_exact_likelihood_labels_consumed", "regularization_selected_from_validation_or_oracle"):
                    a.equal(fit[k], False, "fit no selection " + k)
                a.equal(node["design_prefix_sha256"], a.array_digest(s[:budget], z[:budget]), "shared design prefix")
                a.equal(node["training_labels_sha256"], a.array_digest(labels), "training label prefix")
                a.equal(node["paired_dataset_payload_sha256"], data["splits"][0]["payload_sha256"], "paired full-data identity")
                a.equal(node["matched_skeleton_prefix_work"], {k: int(values[:budget].sum()) for k, values in counts.items()}, "exact prefix work")
                prediction_v = baseline_v + XV @ c
                a.near(node["validation_risk"], np.mean(np.exp(prediction_v)-bv*prediction_v)/maximum, "RB validation risk")
                a.tree_near(node["validation_paired_change"], validation_change(prediction_v, baseline_v, bv, maximum, sv), "RB validation change")
                a.tree_near(node["raw_validation_paired_change"], validation_change(prediction_v, baseline_v, rv, maximum, sv), "raw validation change")
                a.near(node["model_real_absolute_bound"], np.max(abs(c)), "fit model bound")
                a.near(fit["real_arithmetic_absolute_bound"], np.max(abs(c)), "stored model bound")
                a.COUNTS["default_fit_objective_gradient_box_checks"] += 1
            else:
                c = np.zeros(35)
            node = saved["evaluation_nodes"][ni]
            a.equal(node["u"], u, "evaluation time")
            baseline = a.baseline(theta, y, u, method, es, ez)
            residual = {k: matrix @ c for k, matrix in F.items()}
            physical = {k: baseline[k] + residual[k] for k in F}
            truth = truths[name, u]
            for category, values in (("baseline", baseline), ("residual", residual), ("physical", physical), ("target", truth)):
                for k in F:
                    a.near(node[category][k], values[k], category + " raw readback")
                    a.COUNTS["evaluation_array_readbacks"] += 1
            e = comparison({k: v[2:] for k, v in physical.items()}, {k: v[2:] for k, v in truth.items()})
            be = comparison({k: v[2:] for k, v in baseline.items()}, {k: v[2:] for k, v in truth.items()})
            a.tree_near(node["continuous_errors"], e, "pointwise physical acceptance")
            a.tree_near(node["continuous_baseline_errors"], be, "pointwise baseline acceptance")
            a.near(node["atomic_log_value_errors"], physical["value"][:2]-truth["value"][:2], "atomic value error")
            centered = physical["value"]-physical["value"][0]-truth["value"]+truth["value"][0]
            a.near(node["empty_centered_log_potential_error_max_abs"], np.max(abs(centered)), "empty-centered value")
            a.near(node["model_real_absolute_bound"], np.max(abs(c)), "evaluation envelope")
            if u == 1:
                for k in F:
                    a.near(node["residual"][k], np.zeros(len(es)), "terminal residual zero", atol=0, rtol=0)
                    a.near(physical[k], truth[k], "terminal channel identity")
            eval_rows.append({"continuous_errors": e, "continuous_baseline_errors": be})
        aggregate = {k: {kind: {"max_abs": max(n[kind][k]["max_abs"] for n in eval_rows[:-1]),
            "rms": math.sqrt(math.fsum(n[kind][k]["rms"]**2 for n in eval_rows[:-1])/8),
            "failure_count": sum(n[kind][k]["failure_count"] for n in eval_rows[:-1]), "probe_count": 2048}
            for kind in ("continuous_errors", "continuous_baseline_errors")} for k in F}
        a.tree_near(saved["active_errors"], aggregate, "active error aggregates")
        a.equal(saved["all_continuous_tolerances_passed"], all(v["continuous_errors"]["failure_count"] == 0 for v in aggregate.values()), "overall acceptance")
        a.equal(saved["solver_success_count"], sum(n["fit"]["solver_success"] for n in saved["nodes"]), "solver flag count")
        a.near(saved["maximum_projected_gradient"], max(n["fit"]["projected_gradient_max_abs"] for n in saved["nodes"]), "max default projected gradient")
        a.near(saved["mean_validation_risk_change"], np.mean([n["validation_paired_change"]["mean"] for n in saved["nodes"]]), "mean validation change")
        evaluated[name, seed, method, budget, arm] = saved
    expected_diag = [(name, seed, u, budget) for name, seed, u in dataset_roster for budget in a.BUDGETS]
    a.equal([(r["scenario"], r["seed"], r["u"], r["budget"]) for r in report["label_diagnostics"]], expected_diag, "96 diagnostic roster")
    h_cache = {}
    for row in report["label_diagnostics"]:
        name, seed, u, budget = row["scenario"], row["seed"], row["u"], row["budget"]
        theta, y = settings[name]
        floor, maximum, A = a.observation_bounds(theta, y)
        _, splits = datasets[name, seed, u]
        s, z, raw, rb, variance, _ = splits[0]
        key = name, seed, u
        if key not in h_cache:
            h_cache[key] = np.exp(a.target(oracles[name], u, s, z)["value"])
        h = h_cache[key][:budget]
        X = a.features(s[:budget], z[:budget])
        for arm, labels in (("RAW", raw), ("RAO_BLACKWELL", rb)):
            error = labels[:budget] - h
            noise = X.T @ error / (budget * maximum)
            a.tree_near(row["arms"][arm], {"label_mse_against_independent_mean": float(np.mean(error**2)),
                "label_bias_realized_mean": float(np.mean(error)), "empirical_gradient_noise": noise.tolist(),
                "empirical_gradient_noise_l2": float(np.linalg.norm(noise))}, "label mean and gradient noise")
        removed = X.T @ (variance[:budget, None] * X) / (budget * maximum)**2
        a.near(row["removed_gradient_covariance_estimate"], removed, "removed covariance matrix")
        a.near(row["removed_gradient_covariance_trace"], np.trace(removed), "removed covariance trace")
        a.near(row["mean_removed_conditional_label_variance"], variance[:budget].mean(), "removed label variance")
        a.require(np.linalg.eigvalsh((removed + removed.T)/2).min() >= -1e-18, "PSD removed covariance")
        a.equal(row["covariance_estimate_not_confidence_certificate"], True, "covariance caveat")
        check_noise_bound(row["noise_bound"], X, floor, maximum, A, F)
        a.COUNTS["independent_label_diagnostics"] += 1
    pair_roster = [(name, method, seed, budget) for name, seed, method, budget, arm in roster if arm == "RAW"]
    a.equal([(r["scenario"], r["method"], r["seed"], r["budget"]) for r in report["paired_comparisons"]], pair_roster, "24 paired comparison roster")
    for pair in report["paired_comparisons"]:
        name, method, seed, budget = pair["scenario"], pair["method"], pair["seed"], pair["budget"]
        raw = evaluated[name, seed, method, budget, "RAW"]
        rb = evaluated[name, seed, method, budget, "RAO_BLACKWELL"]
        for k in F:
            x, y = raw["active_errors"][k]["continuous_errors"]["rms"], rb["active_errors"][k]["continuous_errors"]["rms"]
            a.tree_near(pair["errors"][k], {"raw_rms": x, "rb_rms": y, "rb_over_raw_rms": y/x if x else None}, "paired RMS comparison")
        a.near(pair["validation_risk_rb_minus_raw"], np.mean([b["validation_risk"]-r["validation_risk"]
            for r, b in zip(raw["nodes"], rb["nodes"])]), "paired validation risk difference")
        a.equal(pair["exact_shared_design_and_skeleton"], True, "paired same skeleton declaration")
        for r, b in zip(raw["nodes"], rb["nodes"]):
            for k in ("design_prefix_sha256", "paired_dataset_payload_sha256", "matched_skeleton_prefix_work"):
                a.equal(r[k], b[k], "paired retained identity " + k)
        a.COUNTS["paired_route_comparisons"] += 1
    a.equal(a.COUNTS["default_fit_objective_gradient_box_checks"], 384, "all fits audited")
    a.equal(a.COUNTS["independent_gaussian_label_rows"], 589824, "all suffix labels audited")
    a.equal(a.COUNTS["independent_label_diagnostics"], 96, "all covariance diagnostics audited")
    a.equal(a.COUNTS["paired_route_comparisons"], 24, "all route pairs audited")
    for relative, sha in report["source_sha256"].items():
        a.equal(hashlib.sha256((repo / "src/heterodiff" / relative).read_bytes()).hexdigest(), sha, "source stable through audit")
    reader.unchanged()
    a.equal(hashlib.sha256(DEPENDENCY_PATH.read_bytes()).hexdigest(), DEPENDENCY_SHA256, "audit arithmetic unchanged")
    return {"schema_version": "independent-localized-variance-reduction-audit-v1",
        "decision": "PASS_INDEPENDENT_LOCALIZED_VARIANCE_REDUCTION_AUDIT", "errors": [],
        "report_sha256": reader.bindings[out / "report.json"], "protocol_sha256": report["protocol_sha256"],
        "original_report_sha256": a.ARCHIVE_HASH, "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "independent_arithmetic_dependency_sha256": DEPENDENCY_SHA256,
        "check_counts": dict(a.COUNTS), "maximum_arithmetic_discrepancies_by_check": dict(a.MAX_ERRORS),
        "unique_generation_work_totals": dict(work_totals),
        "paired_route_summaries": report["paired_comparisons"],
        "input_file_sha256": {str(p.relative_to(repo)): sha for p, sha in reader.bindings.items()},
        "scope": {"optimizer_or_fit_called": False, "new_runner_or_label_module_imported": False,
            "forward_simulator_called": False, "original_archive_unchanged_through_audit": True,
            "unchanged_backward_oracle_evaluation_only": True, "all_saved_terminal_gaussian_labels_recomputed": True,
            "full_jump_skeleton_replayed": False, "historical_execution_order_authenticated": False,
            "real_arithmetic_bounds_interval_certified": False, "statistical_superiority_certified": False,
            "audit_numeric_thresholds_change_scientific_acceptance_tolerances": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--output", type=Path, help="exclusive new audit receipt")
    args = parser.parse_args()
    repo = args.repo.resolve()
    result_dir = (args.result or repo / "research/fixtures/continuous_localized_variance_reduction_cpu_2026_09_13").resolve()
    with threadpool_limits(limits=1):
        result = audit(repo, result_dir)
    encoded = a.payload(result)
    if args.output is not None:
        with args.output.open("xb") as handle:
            handle.write(encoded)
    print(encoded.decode(), end="")


if __name__ == "__main__":
    main()
