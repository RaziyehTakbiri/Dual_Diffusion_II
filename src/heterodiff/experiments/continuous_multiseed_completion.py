"""Complete one fixed missing seed pair after an authorized CPU time extension.

This is not checkpoint resume or success of the original 2,400-second attempt.
The unchanged saved prefix is read-only. Only the unsaved final two routes are
computed from their original seeds, including recomputation of interrupted work.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np

from heterodiff.experiments import continuous_multiseed_benchmark as original
from heterodiff.evaluation.continuous_multiseed_statistics import (
    paired_contrast, paired_error_summary, route_report, seed_summary,
)

SCHEMA = "continuous-multiseed-authorized-completion-v1"
REVIEW_SHA256 = "1099b2bbc835568cd3eec73b22252ebe3bd405230e4fa9a840b118ac5a6d2652"
VERIFICATION_SHA256 = "ebfca4c9aad509023576b2e8d4a546574ed3fbda8d0e652a42180c381b47784b"
ORIGINAL_DIRECTORY = "research/fixtures/continuous_multiseed_cpu_2026_09_13"
REVIEW_PATH = ORIGINAL_DIRECTORY + "_review.json"
VERIFICATION_PATH = "research/fixtures/continuous_multiseed_verification_2026_09_13.json"
SOURCE_PATHS = (
    "src/heterodiff/experiments/continuous_multiseed_benchmark.py",
    "src/heterodiff/evaluation/continuous_multiseed_statistics.py",
    "src/heterodiff/evaluation/continuous_fiber_initialization_diagnostic.py",
    "src/heterodiff/experiments/factorized_prepared_conditional_sampler.py",
)


class CompletionError(ValueError):
    """Refusal before a result can be described as fixed-roster completion."""


def _need(condition, message):
    if not condition:
        raise CompletionError(message)


def _digest(payload):
    return hashlib.sha256(payload).hexdigest()


def _json(payload):
    def no_constant(value):
        raise CompletionError("nonfinite JSON constant: " + value)
    def unique(items):
        result = {}
        for key, value in items:
            _need(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(payload, parse_constant=no_constant, object_pairs_hook=unique)


def _normalized(value):
    return json.loads(json.dumps(value, allow_nan=False))


def _read_bound(path, expected_hash):
    payload = Path(path).read_bytes()
    _need(_digest(payload) == expected_hash, "artifact hash mismatch: " + str(path))
    return _json(payload), payload


def fixed_roster(budget):
    roster = []
    for name, _, _ in original.SCENARIOS:
        roster.extend((name, "control", method, None) for method in original.CONTROLS)
        roster.extend((name, "neural", method, seed)
                      for seed in budget.seeds for method in original.METHODS)
    return tuple(roster)


def _identity(route):
    return route["scenario"], route["kind"], route["route"], route.get("training_seed")


def validate_routes(routes, budget, *, complete):
    """Validate exact order, completeness, scientific counts and original bounds."""
    roster = fixed_roster(budget)
    expected = roster if complete else roster[:-2]
    _need(len(routes) == len(expected), "route count differs from fixed roster")
    _need(tuple(_identity(r) for r in routes) == expected, "duplicate, missing or reordered fixed route")
    targets = {}
    for route in routes:
        n = budget.neural_draws if route["kind"] == "neural" else budget.control_draws
        metrics = route["metrics"]
        _need(metrics["draw_count"] == n, "original draw count changed")
        recomputed = route_report(metrics["empirical_indicators"], metrics["target_indicators"], n,
                                  family_count=len(roster))
        _need(metrics == recomputed, "route statistical report or family changed")
        target = metrics["target_indicators"]
        _need(target == targets.setdefault(route["scenario"], target), "scenario target differs across routes")
        if route["kind"] == "neural":
            _need(len(route["updates"]) == budget.updates, "original update count changed")
            _need([r["update"] for r in route["held_out_paired_loss_curve"]] ==
                  original.specification(budget)["validation_checkpoints"], "validation checkpoints changed")
            _need(route["training_pairs"] == budget.updates * budget.pairs_per_update and
                  route["validation_pairs"] == budget.validation_pairs and
                  route["training_base_paths"] == 2 * budget.updates * budget.pairs_per_update and
                  route["validation_base_paths"] == 2 * budget.validation_pairs,
                  "original training or validation work changed")
    return targets


@dataclass(frozen=True)
class ValidatedPrefix:
    """In-memory evidence; not an authenticated or resumable checkpoint."""
    routes: tuple
    budget: original.ExperimentBudget
    bindings: dict
    expected_environment: dict


def validate_original(original_directory, review_path, verification_path, source_root):
    """Read and recheck the one reviewed 20-of-22 attempt without writing it."""
    directory, root = Path(original_directory), Path(source_root)
    review, _ = _read_bound(review_path, REVIEW_SHA256)
    verification, _ = _read_bound(verification_path, VERIFICATION_SHA256)
    _need(review["decision"] == "INCOMPLETE_CPU_DEADLINE_COMPLETE_ROUTES_REVIEWED",
          "review does not describe the original timeout")
    run = review["original_run"]
    _need(run["saved_complete_routes"] == 20 and run["declared_routes"] == 22 and
          run["predeclared_deadline_seconds"] == 2400 and run["parent_exit_code"] == 2 and
          run["child_termination_confirmed"] is True and run["directory"] == ORIGINAL_DIRECTORY,
          "original attempt disposition changed")
    _need(sorted(p.name for p in directory.iterdir()) ==
          ["protocol.json"] + [f"route-{i:02d}.json" for i in range(1, 21)],
          "original directory is not the exact reviewed 20-route namespace")
    protocol, _ = _read_bound(directory / "protocol.json", run["original_protocol_file_sha256"])
    budget = original.ExperimentBudget()
    _need(protocol == _normalized(original.specification(budget)), "original protocol differs from fixed default")
    source_hashes = verification["source_sha256"]
    _need(set(source_hashes) == set(SOURCE_PATHS), "original verified source roster differs")
    for relative, digest in source_hashes.items():
        _need(_digest((root / relative).read_bytes()) == digest, "original source hash mismatch: " + relative)
        module_name = relative.removeprefix("src/").removesuffix(".py").replace("/", ".")
        spec = importlib.util.find_spec(module_name)
        _need(spec is not None and spec.origin is not None and
              _digest(Path(spec.origin).read_bytes()) == digest, "importable implementation hash mismatch: " + relative)
    scientific = verification["scientific_protocol"]
    _need(scientific["path"] == "docs/MIXED_CONTINUOUS_MULTISEED_PROTOCOL.md", "scientific protocol path differs")
    _need(_digest((root / scientific["path"]).read_bytes()) == scientific["sha256"], "scientific protocol hash mismatch")
    expected_missing = [
        {"ordinal": 21, "scenario": original.SCENARIOS[1][0], "route": original.METHODS[0],
         "training_seed": 1203, "status": "INTERRUPTED_WITHOUT_COMPLETE_ROUTE_RECORD"},
        {"ordinal": 22, "scenario": original.SCENARIOS[1][0], "route": original.METHODS[1],
         "training_seed": 1203, "status": "NOT_REACHED"},
    ]
    _need(review["missing_routes"] == expected_missing, "missing pair differs from reviewed seed 1203 pair")
    entries = review["complete_route_metrics"]
    _need(len(entries) == 20, "review route binding count differs")
    routes, artifacts = [], []
    for ordinal, entry in enumerate(entries, 1):
        artifact = entry["artifact"]
        name = f"route-{ordinal:02d}.json"
        _need(artifact["path"] == ORIGINAL_DIRECTORY + "/" + name, "review route binding order differs")
        route, payload = _read_bound(directory / name, artifact["sha256"])
        _need(len(payload) == artifact["size_bytes"], "original route size mismatch")
        _need(all(route.get(k) == v for k, v in entry.items() if k != "artifact"), "review route projection mismatch")
        routes.append(route)
        artifacts.append(artifact)
    validate_routes(routes, budget, complete=False)
    return ValidatedPrefix(tuple(routes), budget, {
        "partial_review_sha256": REVIEW_SHA256, "original_verification_sha256": VERIFICATION_SHA256,
        "original_protocol_sha256": run["original_protocol_file_sha256"],
        "original_source_sha256": source_hashes, "scientific_protocol": scientific,
        "preserved_route_artifacts": artifacts,
    }, verification["tests"]["development_regression"]["versions"])


def run_neural_route(scenario, seed, method, budget, check, *, expected_population=None, expected_initial=None):
    """Original neural procedure, including namespaces and final-only evaluation.

Reduced budgets are for equivalence tests. The public completion entry point
accepts only the independently bound default protocol and its missing pair.
"""
    from heterodiff.experiments.factorized_common_grid_pipeline import (
        CommonGridDeviceFactorizedBasePopulation, common_grid_train_conditional_step,
    )
    from heterodiff.experiments.factorized_conditional_pipeline import _parameter_digest
    from heterodiff.experiments.factorized_device_qualification import _optimizer
    from heterodiff.experiments.factorized_prepared_conditional_sampler import PreparedCommonGridConditionalSampler
    check()
    began = time.monotonic()
    ref, oracle, key, base, model, context, observed = original.fixture(scenario, seed, method)
    initial_hash = _parameter_digest(model)
    population = CommonGridDeviceFactorizedBasePopulation(base, ref, original.GRID, context)
    _need(expected_population is None or population.law_id == expected_population,
          "prior BASE population mismatch before training")
    _need(expected_initial is None or initial_hash == expected_initial,
          "paired method initialization mismatch before training")
    validation = original.validation_pairs(population, seed, budget.validation_pairs, check)
    optimizer = _optimizer(model)
    losses = [{"update": 0, "held_out_paired_loss": original.validation_loss(model, validation)}]
    updates = []
    for step in range(1, budget.updates + 1):
        check()
        updates.append(common_grid_train_conditional_step(model, population, optimizer=optimizer,
            run_seed=original.seed_for(seed, "training-paths"), record_id=f"update-{step}".encode(),
            sample_count=budget.pairs_per_update))
        if step in original.specification(budget)["validation_checkpoints"]:
            losses.append({"update": step, "held_out_paired_loss": original.validation_loss(model, validation)})
    fit_seconds = time.monotonic() - began
    preparation_began = time.monotonic()
    sampler = PreparedCommonGridConditionalSampler(base, model, ref, original.GRID, context, observed,
        maximum_draws=budget.neural_draws, expected_population_law_id=population.law_id)
    preparation_seconds = time.monotonic() - preparation_began
    samples = []
    work = {"accepted_births": 0, "accepted_deaths": 0, "jump_candidates": 0, "macrosteps": 0}
    began = time.monotonic()
    for i in range(budget.neural_draws):
        check()
        path = sampler.sample_path(run_seed=original.seed_for(seed, "evaluation-paths"), record_id=f"evaluate-{i}".encode())
        samples.append(path.terminal_state)
        work["accepted_births"] += path.diagnostics["accepted_birth"]
        work["accepted_deaths"] += path.diagnostics["accepted_death"]
        work["jump_candidates"] += path.diagnostics["jump_candidates"]
        work["macrosteps"] += len(original.GRID) - 1
    evaluation_seconds = time.monotonic() - began
    target = original.target_indicators(oracle.terminal_posterior())
    return {"scenario": scenario[0], "kind": "neural", "route": method, "training_seed": seed,
        "initial_parameter_sha256": initial_hash, "final_parameter_sha256": _parameter_digest(model),
        "population_law_id": population.law_id, "prepared_sampler": sampler.snapshot_binding(),
        "fit_and_validation_seconds": fit_seconds, "evaluation_seconds": evaluation_seconds,
        "sampler_preparation_seconds": preparation_seconds, "initialization_attempt_count": None,
        "initialization_cost_included_in_evaluation_seconds": True,
        "updates": updates, "held_out_paired_loss_curve": losses,
        "training_pairs": budget.updates * budget.pairs_per_update, "validation_pairs": budget.validation_pairs,
        "training_base_paths": budget.updates * budget.pairs_per_update * 2,
        "validation_base_paths": budget.validation_pairs * 2, "work": work,
        "metrics": route_report(original.indicators(samples, key), target, len(samples),
                                family_count=original.specification(budget)["total_route_count"])}


def assemble_report(routes, budget, *, bindings, elapsed_seconds, maximum_seconds):
    """Recompute unchanged 22/4/2-family statistics over every complete route."""
    targets = validate_routes(routes, budget, complete=True)
    summaries, diagnostics = [], {}
    for scenario in original.SCENARIOS:
        name = scenario[0]
        _, oracle, _, _, _, _, _ = original.fixture(scenario, budget.seeds[0], original.METHODS[0])
        _need(targets[name] == original.target_indicators(oracle.terminal_posterior()), "saved target differs from independent oracle")
        diagnostics[name] = original.ContinuousFiberInitializationDiagnostic(oracle.spec).report()
        means, by_method = {}, {}
        for method in original.METHODS:
            selected = [next(r for r in routes if r["scenario"] == name and r["route"] == method and r.get("training_seed") == seed)
                        for seed in budget.seeds]
            means[method] = [r["metrics"]["empirical_indicators"] for r in selected]
            by_method[method] = seed_summary(means[method], targets[name], budget.neural_draws)
        gr, direct = [by_method[m] for m in original.METHODS]
        gap = direct["mixture_maximum_indicator_error"] - gr["mixture_maximum_indicator_error"]
        width = gr["mixture_sampling_half_width"] + direct["mixture_sampling_half_width"]
        summaries.append({"scenario": name, "methods": by_method, "training_seed_roster": list(budget.seeds),
            "paired_seed_error_gr_minus_dir": paired_error_summary(means[original.METHODS[0]], means[original.METHODS[1]],
                targets[name], budget.neural_draws, route_family_count=original.specification(budget)["total_route_count"]),
            "signed_probability_contrast_gr_minus_dir": paired_contrast(means[original.METHODS[0]], means[original.METHODS[1]], budget.neural_draws),
            "mixture_error_advantage_gr_point": gap,
            "mixture_error_advantage_gr_interval": [max(-1., gap - width), min(1., gap + width)],
            "advantage_scope": "EQUAL_WEIGHT_MIXTURE_OF_THIS_FITTED_SEED_ROSTER_FINITE_INDICATORS_NOT_TRAINING_SEED_POPULATION",
            "general_superiority_claimed": False})
    import torch
    return {"schema_version": SCHEMA, "decision": "COMPLETE_FIXED_ROSTER_WITH_AUTHORIZED_TIME_EXTENSION",
        "specification": original.specification(budget), "routes": list(routes), "summaries": summaries,
        "initializer_diagnostics": diagnostics, "original_evidence": bindings,
        "continuation": {"original_single_attempt_success": False, "original_attempt_timed_out": True,
            "original_deadline_seconds": budget.maximum_seconds, "separate_supervisor_seconds": maximum_seconds,
            "continuation_elapsed_seconds": elapsed_seconds, "preserved_completed_routes": len(routes) - 2,
            "new_complete_routes": 2, "interrupted_unsaved_prefix_recomputed_from_original_seed": True,
            "checkpoint_resumed": False, "additional_original_unsaved_work_unknown": True,
            "total_attempted_work_or_total_elapsed_time_known": False,
            "scientific_settings_or_statistical_families_changed": False,
            "implicit_retries": 0, "local_CPU_time_extension_authorized": True},
        "environment": {"python": platform.python_version(), "torch": torch.__version__,
                        "numpy": np.__version__, "device": "cpu", "threads": 1},
        "scope": {"real_data_accessed": False, "GPU_requested": False, "cloud_or_paid_jobs_launched": False,
            "failed_samples_discarded": 0, "checkpoint_or_hyperparameter_selection": False,
            "analytic_cap_one_reference_target": True, "base_weights_zero_frozen_not_trained": True,
            "actual_mixed_neural_conditional_learner_and_sampler": True, "same_target_both_methods": True,
            "full_posterior_recovery_or_general_superiority_claimed": False,
            "matched_quality_speedup_claimed": False, "continuous_TV_or_KL_estimated_from_samples": False}}


def _write(path, record):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _deadline_seconds(value):
    _need(type(value) is int and 1 <= value <= 86400, "separate execution deadline must be an integer in 1..86400")
    return value


def _complete(prefix, output_directory, maximum_seconds, *, progress=None):
    """Internal worker; reduced verified-equivalence tests use reduced prefixes."""
    import torch
    import scipy
    from heterodiff.experiments.finite_conditional_learning_benchmark import _cpu_policy
    _need(type(prefix) is ValidatedPrefix, "validated prefix required")
    _deadline_seconds(maximum_seconds)
    validate_routes(prefix.routes, prefix.budget, complete=False)
    versions = {"python": platform.python_version(), "torch": torch.__version__, "numpy": np.__version__, "scipy": scipy.__version__}
    _need(versions == prefix.expected_environment, "continuation environment differs from original development run")
    output = Path(output_directory)
    _need(not output.exists() and output.parent.is_dir(), "output must be absent beneath an existing directory")
    output.mkdir()
    started = time.monotonic()
    def check():
        if time.monotonic() - started > maximum_seconds:
            raise TimeoutError("continuation execution deadline exceeded; no complete result")
    _write(output / "continuation-intent.json", {"schema_version": SCHEMA,
        "decision": "AUTHORIZED_FIXED_MISSING_PAIR_COMPLETION_INTENT", "original_evidence": prefix.bindings,
        "specification": original.specification(prefix.budget), "separate_supervisor_seconds": maximum_seconds,
        "missing_routes": list(fixed_roster(prefix.budget)[-2:]), "checkpoint_resume": False,
        "interrupted_unsaved_prefix_recomputed": True, "original_single_attempt_success_claimed": False})
    routes = list(prefix.routes)
    try:
        with _cpu_policy(torch):
            initial = None
            expected_population = routes[-1]["population_law_id"]
            for method in original.METHODS:
                check()
                route = run_neural_route(original.SCENARIOS[-1], prefix.budget.seeds[-1], method, prefix.budget, check,
                                         expected_population=expected_population, expected_initial=initial)
                if initial is None:
                    initial = route["initial_parameter_sha256"]
                _need(route["initial_parameter_sha256"] == initial and route["population_law_id"] == expected_population,
                      "missing pair initialization or prior BASE population mismatch")
                routes.append(route)
                _write(output / f"route-{len(routes):02d}.json", route)
                if progress:
                    progress(route, len(routes), len(fixed_roster(prefix.budget)))
            check()
            report = assemble_report(routes, prefix.budget, bindings=prefix.bindings,
                elapsed_seconds=time.monotonic() - started, maximum_seconds=maximum_seconds)
            check()
            report["continuation"]["continuation_elapsed_seconds"] = time.monotonic() - started
            _write(output / "report.json", report)
            return report
    except Exception as error:
        _write(output / "continuation-failure.json", {"decision": "INCOMPLETE_AUTHORIZED_CONTINUATION_NO_IMPLICIT_RETRY",
            "error_type": type(error).__name__, "detail": str(error), "complete_routes_written": len(routes) - len(prefix.routes)})
        raise


def complete_missing_pair(original_directory, review_path, verification_path, source_root, output_directory,
                          *, maximum_seconds=1800, progress=None):
    prefix = validate_original(original_directory, review_path, verification_path, source_root)
    return _complete(prefix, output_directory, maximum_seconds, progress=progress)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--original-directory", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--verification", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--maximum-seconds", type=int, default=1800)
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    deadline = _deadline_seconds(args.maximum_seconds)
    directory = args.original_directory or args.source_root / ORIGINAL_DIRECTORY
    review = args.review or args.source_root / REVIEW_PATH
    verification = args.verification or args.source_root / VERIFICATION_PATH
    prefix = validate_original(directory, review, verification, args.source_root)
    if args.inspect:
        print(json.dumps({"decision": "FIXED_TWENTY_ROUTE_PREFIX_VALIDATED_NO_COMPLETION_RUN",
            "bindings": prefix.bindings, "missing_routes": fixed_roster(prefix.budget)[-2:],
            "separate_execution_deadline_seconds": deadline}, indent=2, sort_keys=True))
        return 0
    if args.output is None:
        parser.error("--output is required unless --inspect")
    if not args.child:
        _need(not args.output.exists() and args.output.parent.is_dir(), "output must be absent beneath an existing directory")
        command = [sys.executable, "-m", "heterodiff.experiments.continuous_multiseed_completion",
            "--source-root", str(args.source_root.resolve()), "--original-directory", str(directory.resolve()),
            "--review", str(review.resolve()), "--verification", str(verification.resolve()),
            "--output", str(args.output.resolve()), "--maximum-seconds", str(deadline), "--child"]
        try:
            return subprocess.run(command, check=False, timeout=deadline).returncode
        except subprocess.TimeoutExpired:
            if args.output.is_dir():
                _write(args.output / "continuation-timeout.json", {
                    "decision": "INCOMPLETE_CONTINUATION_SUPERVISOR_TIMEOUT_CHILD_TERMINATED",
                    "execution_deadline_seconds": deadline, "implicit_retry": False})
            print("Continuation deadline exceeded; child terminated; no implicit retry.", file=sys.stderr)
            return 2
    def progress(route, completed, total):
        print(json.dumps({"completed_fixed_roster_routes": completed, "total_routes": total,
                          "route": route["route"], "training_seed": route["training_seed"]}), flush=True)
    report = _complete(prefix, args.output, deadline, progress=progress)
    print(json.dumps({"decision": report["decision"], "output": str(args.output)}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
