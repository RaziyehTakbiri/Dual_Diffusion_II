"""Read-only independent arithmetic audit of the fixed localized FD7 receipt.

Imports no heterodiff, NumPy, SciPy, Torch, target, fit or sampler modules.
Reconstructs saved arithmetic from archived labels and controls; performs no
new target queries, fitting, simulation, model selection or experiment run.
Prints one JSON audit record; the caller may preserve it separately.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

SCENARIOS = ("reference-pressure", "higher-pressure-shifted-observation")
METHODS = ("association-aware-guide-plus-residual", "unified-direct-conditioner")
ARMS = ("VS_FINITE_DIFFERENCE", "ORACLE_JET_VSH")
ARM = "VS_FD7_SIXTH_ORDER_SCORE_DIFFERENCES"
TOLERANCES = {"value": (2e-6, 2e-5), "gradient": (2e-5, 2e-4), "hessian": (1e-4, 1e-3)}
GRID = tuple(i / 8 for i in range(9))
ARCHIVE_SHA = "5cfc1a95284ce1149dd3211799666988b8b0422807affec2961c26264ab4c099"
PROTOCOL_SHA = "6a304da5e3bbf6d2f3bc19e2184122d803b8a8024997f5c8ebf4ccee5ab76f47"
ARCHIVE_PROTOCOL_SHA = "de45c892a45e67ccee208bb59077c58fe55e5bed9993fd5f876729db00ccc20e"


def payload(obj):
    return json.dumps(obj, sort_keys=True, indent=2, allow_nan=False).encode() + b"\n"


def digest(obj):
    return hashlib.sha256(payload(obj)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def equal(a, b, message):
    require(a == b, message)


def close(a, b, message, atol=2e-13, rtol=1e-11):
    require(math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, abs_tol=atol, rel_tol=rtol), message)


def tree_close(a, b, path=""):
    if isinstance(a, dict):
        equal(set(a), set(b), "dictionary keys: " + path)
        for key in a:
            tree_close(a[key], b[key], path + "/" + key)
    elif isinstance(a, (list, tuple)):
        equal(len(a), len(b), "array length: " + path)
        for j, (x, y) in enumerate(zip(a, b)):
            tree_close(x, y, path + "/" + str(j))
    elif type(a) is float:
        close(a, b, "numeric audit mismatch: " + path)
    else:
        equal(a, b, "exact audit mismatch: " + path)


def load(path, bindings):
    raw = path.read_bytes()
    require(len(raw) <= 64 * 1024 * 1024, "input size exceeded")
    bindings[str(path)] = hashlib.sha256(raw).hexdigest()
    obj = json.loads(raw, parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
    return obj


def metrics(approximation, target):
    result = {}
    for name, (atol, rtol) in TOLERANCES.items():
        a, t = approximation[name], target[name]
        equal(len(a), 256, "expected 256 probe values")
        equal(len(t), len(a), "aligned target arrays")
        require(all(math.isfinite(x) for x in a + t), "finite probe arrays")
        error = [abs(x - y) for x, y in zip(a, t)]
        thresholds = [atol + rtol * abs(y) for y in t]
        failures = sum(e > threshold for e, threshold in zip(error, thresholds))
        result[name] = {"count": len(t), "max_abs": max(error),
            "rms": math.sqrt(math.fsum(e * e for e in error) / len(t)),
            "failure_count": failures, "passed_pointwise_approximation_tolerance": not failures,
            "atol": atol, "rtol": rtol,
            "maximum_error_over_threshold": max(e / threshold for e, threshold in zip(error, thresholds))}
    return result


def aggregate(nodes):
    result = {}
    for name in TOLERANCES:
        rows = [n["candidate_errors"][name] for n in nodes[:-1]]
        result[name] = {"max_abs": max(r["max_abs"] for r in rows),
            "rms": math.sqrt(math.fsum(r["rms"] ** 2 for r in rows) / len(rows)),
            "failure_count": sum(r["failure_count"] for r in rows),
            "probe_count": sum(r["count"] for r in rows)}
    return result


def rational_weights(position):
    """Independent rational Gaussian elimination of polynomial reproduction."""
    matrix = [[Fraction((j - position) ** k) for j in range(7)] + [Fraction(k == 1)] for k in range(7)]
    for column in range(7):
        pivot = next(i for i in range(column, 7) if matrix[i][column])
        matrix[column], matrix[pivot] = matrix[pivot], matrix[column]
        value = matrix[column][column]
        matrix[column] = [x / value for x in matrix[column]]
        for i in range(7):
            if i != column:
                value = matrix[i][column]
                matrix[i] = [x - value * y for x, y in zip(matrix[i], matrix[column])]
    return tuple(matrix[j][-1] for j in range(7))


WEIGHTS = tuple(rational_weights(i) for i in range(7))


def fd7(scores, width):
    result = []
    for i in range(len(scores)):
        start = min(max(i - 3, 0), len(scores) - 7)
        result.append(math.fsum(float(w) * (scores[start + j] - scores[i])
            for j, w in enumerate(WEIGHTS[i - start])) / width)
    return result


def bezier_control(width, left, right):
    v, s, c = left
    w, t, d = right
    return [v, v + (width / 5) * s,
        v + 2 * (width / 5) * s + (width / 20) * (width * c),
        w - 2 * (width / 5) * t + (width / 20) * (width * d),
        w - (width / 5) * t, w]


def bernstein(control, t):
    """Independent direct Bernstein evaluation, not the source de Casteljau."""
    n = len(control) - 1
    return math.fsum(math.comb(n, j) * t ** j * (1 - t) ** (n - j) * v for j, v in enumerate(control))


def evaluate_controls(knots, controls, tau, coordinates):
    answer = {name: [] for name in TOLERANCES}
    for z in coordinates:
        i = min(max(bisect_right(knots, z) - 1, 0), len(controls) - 1)
        width = knots[i + 1] - knots[i]
        t = min(max((z - knots[i]) / width, 0.), 1.)
        b = controls[i]
        first = [5 * ((y - x) / width) for x, y in zip(b, b[1:])]
        second = [4 * ((y - x) / width) for x, y in zip(first, first[1:])]
        for name, vector in zip(TOLERANCES, (b, first, second)):
            answer[name].append(tau * bernstein(vector, t))
    return answer


def bounds(knots, controls, tau, atoms):
    b = [[tau * x for x in row] for row in controls]
    low, high = min(min(row) for row in b), max(max(row) for row in b)
    d1, d2 = [], []
    for left, right, row in zip(knots, knots[1:], b):
        w = right - left
        difference = [y - x for x, y in zip(row, row[1:])]
        d1 += [5 * v / w for v in difference]
        d2 += [20 * (y - x) / w ** 2 for x, y in zip(difference, difference[1:])]
    mixed_low, mixed_high = min(low, *atoms.values()), max(high, *atoms.values())
    return {"continuous_real_absolute_bound": tau * max(abs(x) for row in controls for x in row),
        "continuous_real_range": [low, high], "mixed_real_range": [mixed_low, mixed_high],
        "whole_projection_real_absolute_bound": max(abs(mixed_low), abs(mixed_high)),
        "whole_projection_real_oscillation_bound": mixed_high - mixed_low,
        "continuous_real_score_absolute_bound": max(map(abs, d1)),
        "continuous_real_hessian_absolute_bound": max(map(abs, d2)),
        "includes_core_collars_tails_and_atomic_values": True,
        "floating_point_outward_certificate": False, "used_by_sampler": False}


def audit(repo, directory, archive_path):
    bindings = {}
    report = load(directory / "report.json", bindings)
    protocol = load(directory / "protocol.json", bindings)
    execution = load(directory / "execution.json", bindings)
    archive = load(archive_path, bindings)
    equal(bindings[str(archive_path)], ARCHIVE_SHA, "fixed archive file hash")
    equal(digest(archive["protocol"]), ARCHIVE_PROTOCOL_SHA, "fixed archive protocol")
    equal(archive["protocol_sha256"], ARCHIVE_PROTOCOL_SHA, "archive protocol declaration")
    equal(report["protocol"], protocol, "saved report/protocol identity")
    equal(digest(protocol), PROTOCOL_SHA, "fixed FD7 protocol hash")
    equal(report["protocol_sha256"], PROTOCOL_SHA, "report protocol declaration")
    equal(execution["protocol_sha256"], PROTOCOL_SHA, "preconstruction protocol declaration")
    equal(execution["recorded_before_constructions"], True, "preconstruction marker")
    equal(execution["source_sha256"], report["source_sha256"], "source receipt binding")
    for name, expected in report["source_sha256"].items():
        paths = list((repo / "src" / "heterodiff").rglob(name))
        equal(len(paths), 1, "unique source identity " + name)
        equal(hashlib.sha256(paths[0].read_bytes()).hexdigest(), expected, "current source hash " + name)
    equal(protocol["approximation_tolerances"], {k: list(v) for k, v in TOLERANCES.items()}, "unchanged tolerances")
    equal(protocol["grid"], list(GRID), "fixed macro grid")
    equal(protocol["methods"], list(METHODS), "method order")
    equal([s["id"] for s in protocol["scenarios"]], list(SCENARIOS), "scenario order")
    equal(protocol["arm"], ARM, "fixed arm")
    equal(protocol["core_cells"], 256, "fixed cell count")
    equal(protocol["collar_width"], 1., "fixed collar")
    equal(protocol["oracle_hessian_labels_consumed"], False, "score-only label claim")
    equal(protocol["retries"], 0, "zero retry protocol")
    equal(protocol["stencil_fraction_weights"],
        {str(i): [[w.numerator, w.denominator] for w in WEIGHTS[i]] for i in range(7)},
        "independent polynomial reproduction weights")
    equal(protocol["core_knots"], archive["protocol"]["core_knots"]["256"], "same archived core knots")
    equal(protocol["evaluation_coordinates"], archive["protocol"]["evaluation_coordinates"], "same archived probes")
    equal(protocol["scenarios"], archive["protocol"]["scenarios"], "same archived process settings")
    knots, probes = protocol["core_knots"], protocol["evaluation_coordinates"]
    equal(len(knots), 257, "knot count")
    equal(knots, [-4.5 + (9 / 256) * j for j in range(257)], "uniform fixed knots")
    equal(len(probes), 256, "probe count")
    require(min(abs(a - b) for a in knots for b in probes) > 1e-12, "disjoint construction/probes")
    refs = {r["scenario"]: r for r in report["references"]}
    old_refs = {r["scenario"]: r for r in archive["references"]}
    equal(set(refs), set(SCENARIOS), "complete target references")
    for scenario in SCENARIOS:
        equal(refs[scenario]["target_rows"], old_refs[scenario]["target_rows"], "bitwise saved target/atom identity")
        equal(refs[scenario]["process"], old_refs[scenario]["process"], "target process")
        equal(refs[scenario]["grid_evidence"], old_refs[scenario]["grid_evidence"], "grid evidence")
        equal(refs[scenario]["continuous_evidence"], old_refs[scenario]["continuous_evidence"], "continuous evidence")
        equal(refs[scenario]["continuous_vs_grid"], old_refs[scenario]["continuous_vs_grid"], "archived law-separation diagnostics")
        equal(refs[scenario]["archived_target_identity"], {
            "all_continuous_target_arrays_bitwise_equal": True, "maximum_target_roundoff_difference": 0.,
            "same_mathematical_numerical_grid_target_checked": True}, "archived target identity declaration")
    old_routes = {(r["scenario"], r["method"], r["arm"]): r for r in archive["routes"] if r["core_cells"] == 256}
    expected_roster = [(s, m) for s in SCENARIOS for m in METHODS]
    equal([(r["scenario"], r["method"]) for r in report["routes"]], expected_roster, "fixed route roster")
    summaries, reconstruction_errors = [], {name: 0. for name in TOLERANCES}
    for ordinal, route in enumerate(report["routes"], 1):
        equal(route["ordinal"], ordinal, "route ordinal")
        equal(route["arm"], ARM, "route arm")
        equal(route["core_cells"], 256, "route cell count")
        separate = load(directory / f"route-{ordinal:02d}.json", bindings)
        equal(route, separate, "saved individual route/report equality")
        equal(tuple(n["u"] for n in route["nodes"]), GRID, "node roster")
        reference = refs[route["scenario"]]["target_rows"]
        old_primary = old_routes[(route["scenario"], route["method"], ARMS[0])]
        for node, target, old_node in zip(route["nodes"], reference, old_primary["nodes"]):
            tau = 1. - node["u"]
            construction = node["construction"]
            for field in ("baseline", "baseline_atoms", "atomic_residuals_exact_oracle_not_learned"):
                equal(node[field], old_node[field], "unchanged archived " + field)
            equal(construction["remaining_time"], tau, "one time gate")
            controls, full = construction["quotient_bezier_controls"], construction["full_knots_including_collars"]
            if tau:
                for field in ("knots", "residual_values", "residual_scores"):
                    equal(construction[field], old_node["construction"][field], "same archived input " + field)
                equal(construction["arm"], ARM, "construction arm")
                equal(construction["oracle_hessian_labels_consumed"], False, "no Hessian label")
                equal(full, [-5.5] + knots + [5.5], "complete collar grid")
                equal(construction["coefficient_sha256"], digest(controls), "control fingerprint")
                curvature = fd7(construction["residual_scores"], 9 / 256)
                equal(curvature, construction["residual_curvatures_used"], "exact score-only FD7 arithmetic")
                jets = list(zip((x / tau for x in construction["residual_values"]),
                    (x / tau for x in construction["residual_scores"]), (x / tau for x in curvature)))
                jets = [(jets[0][0], 0., 0.)] + jets + [(jets[-1][0], 0., 0.)]
                rebuilt = [bezier_control(b - a, x, y) for a, b, x, y in zip(full, full[1:], jets, jets[1:])]
                tree_close(controls, rebuilt, "independent Hermite control reconstruction")
                knot_eval = evaluate_controls(full, controls, tau, knots)
                for name, field, metric in (("value", "residual_values", "knot_value_interpolation_max_abs"),
                    ("gradient", "residual_scores", "knot_score_interpolation_max_abs"),
                    ("hessian", "residual_curvatures_used", "knot_curvature_interpolation_max_abs")):
                    measured = max(abs(x - y) for x, y in zip(knot_eval[name], construction[field]))
                    close(measured, construction[metric], "knot interpolation telemetry", atol=2e-10)
            else:
                equal(construction["terminal_zero_no_oracle_labels_consumed"], True, "terminal construction")
                require(all(x == 0 for row in controls for x in row), "terminal controls exactly zero")
                require(all(x == 0 for values in node["residual"].values() for x in values), "terminal residual arrays zero")
                require(all(x == 0 for x in node["atomic_residuals_exact_oracle_not_learned"].values()), "terminal atoms zero")
            reconstructed = evaluate_controls(full, controls, tau, probes)
            for name in TOLERANCES:
                delta = max(abs(a - b) for a, b in zip(reconstructed[name], node["residual"][name]))
                reconstruction_errors[name] = max(reconstruction_errors[name], delta)
                require(delta <= 2e-10, "independent Bernstein readback mismatch")
                equal(node["physical"][name], [b + r for b, r in zip(node["baseline"][name], node["residual"][name])],
                    "physical = baseline + residual")
            tree_close(node["candidate_errors"], metrics(node["physical"], target["evaluation"]), "raw candidate metrics")
            tree_close(node["baseline_errors"], metrics(node["baseline"], target["evaluation"]), "raw baseline metrics")
            atomic = node["atomic_residuals_exact_oracle_not_learned"]
            for state in ("EMPTY", "OTHER"):
                close(node["baseline_atoms"][state] + atomic[state], target["atoms"][state], "atomic correction")
            tree_close(node["coefficient_and_derivative_bounds"], bounds(full, controls, tau, atomic), "recomputed control bounds")
            value_errors = [a - b for a, b in zip(node["physical"]["value"], target["evaluation"]["value"])]
            contrasts = [(a - node["baseline_atoms"]["EMPTY"] - atomic["EMPTY"]) - (b - target["atoms"]["EMPTY"])
                for a, b in zip(node["physical"]["value"], target["evaluation"]["value"])]
            for key, measured in (("relative_likelihood_error_max_abs", max(abs(math.expm1(x)) for x in value_errors)),
                ("empty_centered_log_potential_error_max_abs", max(map(abs, contrasts))),
                ("E_to_C_log_rate_ratio_error_max_abs", max(map(abs, contrasts))),
                ("E_to_C_relative_rate_ratio_error_max_abs", max(abs(math.expm1(x)) for x in contrasts))):
                close(node[key], measured, key)
        computed = aggregate(route["nodes"])
        tree_close(route["active_probe_errors"], computed, "route aggregates")
        equal(route["all_active_value_score_hessian_checks_passed"],
            all(v["failure_count"] == 0 for v in computed.values()), "route pass flag")
        close(route["largest_whole_projection_real_absolute_bound"],
            max(n["coefficient_and_derivative_bounds"]["whole_projection_real_absolute_bound"] for n in route["nodes"]),
            "route largest bound")
        equal([c["arm"] for c in route["archival_controls"]], list(ARMS), "archive arm roster")
        archive_summary = []
        for control in route["archival_controls"]:
            source = old_routes[(route["scenario"], route["method"], control["arm"])]
            equal(control["source_route_sha256"], digest(source), "whole archived control identity")
            equal(control["source_route_ordinal"], source["ordinal"], "archived control ordinal")
            equal(control["refit_performed"], False, "archive not refitted")
            equal(control["nodes"], [
                {"u": n["u"], "candidate_errors": n["candidate_errors"],
                 "archived_physical_arrays_sha256": digest(n["physical"]),
                 "archived_coefficient_sha256": n["construction"].get("coefficient_sha256")}
                for n in source["nodes"]], "archived physical/coefficients/metrics unchanged")
            for n, target in zip(source["nodes"], reference):
                tree_close(n["candidate_errors"], metrics(n["physical"], target["evaluation"]), "archived raw metrics")
                saved = n["construction"]
                tree_close(n["coefficient_and_derivative_bounds"], bounds(
                    saved["full_knots_including_collars"], saved["quotient_bezier_controls"],
                    saved["remaining_time"], n["atomic_residuals_exact_oracle_not_learned"]), "archived raw control bounds")
                if "coefficient_sha256" in saved:
                    equal(saved["coefficient_sha256"], digest(saved["quotient_bezier_controls"]), "archived control fingerprint")
            tree_close(control["active_probe_errors"], aggregate(source["nodes"]), "archived aggregates")
            equal(control["largest_whole_projection_real_absolute_bound"],
                source["largest_whole_projection_real_absolute_bound"], "archived bound unchanged")
            close(control["largest_whole_projection_real_absolute_bound"], max(
                n["coefficient_and_derivative_bounds"]["whole_projection_real_absolute_bound"] for n in source["nodes"]),
                "archived largest bound aggregation")
            archive_summary.append({"arm": control["arm"], "active_probe_errors": control["active_probe_errors"],
                "largest_whole_projection_real_absolute_bound": control["largest_whole_projection_real_absolute_bound"]})
        summaries.append({"scenario": route["scenario"], "method": route["method"],
            "active_probe_errors": computed,
            "largest_whole_projection_real_absolute_bound": route["largest_whole_projection_real_absolute_bound"],
            "archival_controls": archive_summary})
    equal(report["completed_routes"], 4, "completed route count")
    equal(report["completed_active_profiles"], 32, "completed active count")
    equal(report["completed_terminal_zero_profiles"], 4, "completed terminal count")
    for path, before in bindings.items():
        equal(hashlib.sha256(Path(path).read_bytes()).hexdigest(), before, "input unchanged through audit")
    return {"schema_version": "independent-localized-fd7-raw-receipt-audit-v1",
        "decision": "PASS_INDEPENDENT_RAW_RECEIPT_AUDIT",
        "report_sha256": bindings[str(directory / "report.json")],
        "protocol_sha256": PROTOCOL_SHA, "archive_report_sha256": ARCHIVE_SHA,
        "checked_input_file_sha256": {str(Path(k).relative_to(repo)): v for k, v in bindings.items()},
        "checked_source_file_count": len(report["source_sha256"]),
        "checks": {"fixed_protocol_and_roster": True, "individual_routes_equal_report": True,
            "saved_targets_and_baselines_exactly_equal_archive": True, "archived_control_arrays_and_fingerprints_unchanged": True,
            "fraction_weights_independently_derived_by_polynomial_reproduction": True,
            "FD7_curvatures_reconstructed_from_scores_only": True, "Hermite_controls_reconstructed_from_saved_jets": True,
            "all_raw_metrics_recomputed": True, "all_control_bounds_recomputed": True, "four_terminal_profiles_exact_zero": True,
            "inputs_unchanged_during_audit": True},
        "independent_direct_Bernstein_vs_saved_de_Casteljau_max_abs": reconstruction_errors,
        "audit_readback_threshold": {"absolute": 2e-10, "scope": "arithmetic audit only, not scientific acceptance"},
        "all_unchanged_scientific_tolerance_failures": sum(v["failure_count"] for s in summaries for v in s["active_probe_errors"].values()),
        "active_probe_count_per_derivative_category": 8192,
        "largest_whole_projection_real_absolute_bound": max(s["largest_whole_projection_real_absolute_bound"] for s in summaries),
        "routes": summaries, "experiment_reported_elapsed_seconds": report["elapsed_seconds"],
        "scope": {"no_target_or_fit_or_sampler_imported": True, "no_refit_or_new_experiment": True,
            "no_input_mutation": True, "arithmetic_reconstruction_only": True,
            "exact_score_input_control_not_learnability": True, "sampling_envelope_FP_certified": False,
            "stage_time_or_tail_target_accuracy_claimed": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    directory = repo / "research/fixtures/continuous_localized_curvature_cpu_2026_09_13"
    archive = repo / "research/fixtures/continuous_localized_residual_cpu_2026_09_13/report.json"
    print(payload(audit(repo, directory, archive)).decode(), end="")


if __name__ == "__main__":
    main()
