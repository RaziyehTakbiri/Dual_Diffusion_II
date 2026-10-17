"""Independent read-only audit of the localized error-decomposition receipt.

No new runner, population-risk helper, optimizer, or simulator is called.
The unchanged backward oracle is queried only to verify saved diagnostic
mean-label hashes, target readbacks, and common-risk integrals. The tied
spline basis, objective arithmetic, contrast Gram matrices and bounds are
reconstructed here. Prints JSON; never writes or replaces an evidence file.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.interpolate import BSpline
from threadpoolctl import threadpool_limits

ARCHIVE_HASH = "d8db24c1c4f2d22069da8ec15640cd9b553dfec5f3ecf87b5f0530069289a692"
ARCHIVE_PROTOCOL_HASH = "c99b27fbd042359f65f54cd7c191a4bdd28e98f62303ad341fcdb8287ee8036e"
SCENARIOS = (("reference-pressure", .8, .7), ("higher-pressure-shifted-observation", 2.5, 1.4))
METHODS = ("association-aware-guide-plus-residual", "unified-direct-conditioner")
SEEDS, BUDGETS, LEVELS = (11, 29, 47), (1024, 8192), (16, 32)
GRID = tuple(i / 8 for i in range(9))
STAGES = ("A", "N", "M", "P", "U", "T")
TERMS = ("optimizer_stopping", "realized_label_noise", "realized_design_variation",
         "combined_regularization", "fixed_family_risk_projection")
TOLERANCES = {"value": (2e-6, 2e-5), "gradient": (2e-5, 2e-4), "hessian": (1e-4, 1e-3)}
OPTIMIZER = {"maxiter": 2000, "maxls": 50, "ftol": 1e-15, "gtol": 1e-11}
COUNTS = Counter()
MAX_ERRORS = Counter()


def payload(x):
    return json.dumps(x, sort_keys=True, indent=2, allow_nan=False).encode() + b"\n"


def digest(x):
    return hashlib.sha256(payload(x)).hexdigest()


def array_digest(*arrays):
    h = hashlib.sha256()
    for x in arrays:
        x = np.ascontiguousarray(x)
        h.update(str(x.shape).encode() + x.dtype.str.encode() + x.tobytes())
    return h.hexdigest()


def require(condition, label):
    COUNTS["checks"] += 1
    if not condition:
        raise ValueError(label)


def equal(a, b, label):
    require(a == b, label)


def near(a, b, label, atol=2e-11, rtol=2e-9):
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    require(x.shape == y.shape and np.isfinite(x).all() and np.isfinite(y).all(), label + " shape/finite")
    delta = float(np.max(np.abs(x - y), initial=0.))
    MAX_ERRORS[label.split("/")[0]] = max(MAX_ERRORS[label.split("/")[0]], delta)
    require(bool(np.allclose(x, y, atol=atol, rtol=rtol)), label + " arithmetic mismatch")


def tree_near(a, b, label):
    if isinstance(a, dict):
        equal(set(a), set(b), label + " keys")
        for k in a:
            tree_near(a[k], b[k], label + "/" + k)
    elif isinstance(a, (list, tuple)):
        equal(len(a), len(b), label + " length")
        for k, (x, y) in enumerate(zip(a, b)):
            tree_near(x, y, label + "/" + str(k))
    elif type(a) is float:
        near(a, b, label)
    else:
        equal(a, b, label)


class Reader:
    def __init__(self):
        self.bindings = {}

    def load(self, path):
        raw = path.read_bytes()
        require(len(raw) <= 256 * 1024 * 1024, "bounded JSON input")
        self.bindings[path] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw, parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))

    def unchanged(self):
        for path, expected in self.bindings.items():
            equal(hashlib.sha256(path.read_bytes()).hexdigest(), expected, "input changed during audit: " + str(path))


def features(states, coordinates, order=0):
    edges = np.linspace(-4.5, 4.5, 33)
    knots = np.r_[np.repeat(edges[0], 5), edges, np.repeat(edges[-1], 5)]
    mapping = np.zeros((37, 33))
    mapping[:3, 0] = 1.
    mapping[34:, 32] = 1.
    for j in range(3, 34):
        mapping[j, j - 2] = 1.
    spline = BSpline(knots, mapping, 5, extrapolate=False)
    result = np.zeros((len(states), 35))
    active = states == 2
    z = coordinates[active]
    values = spline(np.clip(z, -4.5, 4.5), nu=order)
    if order:
        values[(z <= -4.5) | (z >= 4.5)] = 0.
    result[active, :33] = values
    if not order:
        result[states == 0, 33] = 1.
        result[states == 1, 34] = 1.
    return result


def quadrature(q):
    roots, weights = np.polynomial.legendre.leggauss(q)
    edges = np.linspace(-4.5, 4.5, 33)
    half = 9 / 64
    zc = (edges[:-1, None] + half + half * roots).ravel()
    states = np.r_[np.array((0, 1), dtype=np.int64), np.full(len(zc), 2, dtype=np.int64)]
    z = np.r_[0., 0., zc]
    w = np.r_[.25, .25, np.tile(.5 * half * weights / 9, 32)]
    require(np.all(w > 0), "positive quadrature weights")
    near(math.fsum(w), 1., "quadrature weight sum", atol=1e-14, rtol=0)
    return states, z, w, features(states, z)


def penalty_matrix():
    roots, weights = np.polynomial.legendre.leggauss(4)
    edges = np.linspace(-4.5, 4.5, 33)
    half = 9 / 64
    z = (edges[:-1, None] + half + half * roots).ravel()
    w = np.tile(weights * half / 9, 32)
    X = features(np.full(len(z), 2, dtype=np.int64), z, 2)
    R = X.T @ (w[:, None] * X)
    P = 1e-4 * R + 1e-6 * np.eye(35)
    return .5 * P + .5 * P.T


def observation_bounds(theta, y):
    del theta
    rho = 393217 / 524288
    c = .1 * math.exp(-1) * rho * math.exp(-y * y / 2) / math.sqrt(2 * math.pi)
    M = c + .9 * .5 / (.5 * math.sqrt(2 * math.pi))
    return c, M, 2 * math.log(M / c)


def baseline(theta, y, u, method, states, z):
    """Independent raw offset formula; does not call the learner's helper."""
    c, _, _ = observation_bounds(theta, y)
    rho = 393217 / 524288
    tau = 1 - u if method == METHODS[0] else 0.
    retained = .5 * math.exp(-tau)
    immigrants = .5 * theta * (-math.expm1(-tau))
    a = math.exp(-tau / 2)
    variance = .25 - math.expm1(-tau)
    stationary = math.exp(-y * y / 2.5) / math.sqrt(2 * math.pi * 1.25)
    immigrant = immigrants * rho * stationary
    factor = .9 * math.exp(-immigrants)
    constant = c + factor * np.where(states == 0, 1., 1 - retained) * immigrant
    result = {"value": np.log(constant), "gradient": np.zeros(len(z)), "hessian": np.zeros(len(z))}
    active = states == 2
    signal = math.log(factor * retained) - .5 * (math.log(2 * math.pi * variance) + (y - a * z[active]) ** 2 / variance)
    logh = np.logaddexp(np.log(constant[active]), signal)
    weight = np.exp(signal - logh)
    slope = a * (y - a * z[active]) / variance
    result["value"][active] = logh
    result["gradient"][active] = weight * slope
    result["hessian"][active] = -weight * a * a / variance + weight * (1 - weight) * slope * slope
    return result


def target(oracle, u, states, z):
    atoms = [oracle.log_likelihood_derivatives(u, k) for k in ("EMPTY", "OTHER")]
    rows = [oracle.log_likelihood_derivatives(u, "CONTINUOUS", float(x)) if s == 2 else atoms[s] for s, x in zip(states, z)]
    return {k: np.asarray([r[v] for r in rows]) for k, v in
        (("value", "log_likelihood"), ("gradient", "gradient"), ("hessian", "hessian"))}


def physical(theta, y, u, method, c, states, z, F):
    b = baseline(theta, y, u, method, states, z)
    return {k: b[k] + F[k] @ c for k in TOLERANCES}


def risk(c, X, Y, b, w, M, P):
    f = b + X @ c
    e = np.exp(f)
    J = float(w @ (e - Y * f) / M + .5 * (c @ P @ c))
    g = X.T @ (w * (e - Y)) / M + P @ c
    return J, g


def audit_fit(row, c, X, Y, b, w, M, floor, A, P):
    equal(row["optimizer_options"], OPTIMIZER, "strict optimizer options")
    equal(row["initial_coefficients"], "ALL_ZERO", "strict zero start")
    equal(row["newton_polish_performed"], False, "no Newton")
    equal(row["retries"], 0, "no retry")
    near(row["physical_coefficients"], c, "fit coefficient identity", atol=0, rtol=0)
    require(np.isfinite(c).all() and np.max(abs(c)) <= A, "fit coefficient box")
    near(row["coefficient_bound"], A, "known coefficient bound", atol=1e-13, rtol=1e-13)
    J, g = risk(c, X, Y, b, w, M, P)
    near(row["final_objective"], J, "strict objective")
    near(row["initial_objective"], risk(np.zeros(35), X, Y, b, w, M, P)[0], "zero objective")
    near(row["gradient"], g, "strict gradient")
    pg = g.copy()
    pg[(c == -A) & (g > 0)] = 0.
    pg[(c == A) & (g < 0)] = 0.
    near(row["projected_gradient"], pg, "projected gradient")
    near(row["projected_gradient_max_abs"], np.max(abs(pg)), "projected maximum")
    gap = math.fsum(abs(float(v)) * (A + (float(a) if v >= 0 else -float(a))) for a, v in zip(c, g))
    near(row["box_first_order_gap"], gap, "convex box gap")
    G = X.T @ (w[:, None] * X)
    G = .5 * G + .5 * G.T
    eig = np.linalg.eigvalsh(G)
    near(row["weighted_gram_eigenvalues"], eig, "feature Gram spectrum")
    row_l1 = float(np.max(np.sum(abs(X), axis=1)))
    actual_floor = min(floor, math.exp(float(np.min(b))))
    peig = float(np.linalg.eigvalsh(P)[0])
    factor = (actual_floor / M) * math.exp(-A * row_l1)
    mu = factor * float(eig[0]) + peig
    distance = math.sqrt(2 * gap / mu) if mu > 0 else None
    gb = row["global_bounds"]
    near(gb["global_strong_convexity_lower_bound_estimate"], mu, "global curvature estimate")
    if distance is None:
        equal(gb["coefficient_distance_upper_bound_estimate"], None, "vacuous solve bound")
    else:
        near(gb["coefficient_distance_upper_bound_estimate"], distance, "coefficient distance estimate", atol=2e-8)
    equal(gb["floating_point_certificate"], False, "no FP certificate")
    equal(gb["local_hessian_eigenvalue_used_as_global_bound"], False, "no local-to-global relabel")
    COUNTS["strict_fit_objective_gradient_box_checks"] += 1
    return distance


def accuracy(values, truth):
    answer = {}
    for k, (atol, rtol) in TOLERANCES.items():
        error = np.asarray(values[k]) - truth[k]
        answer[k] = {"max_abs": float(np.max(abs(error))), "rms": float(np.sqrt(np.mean(error ** 2))),
            "failure_count": int(np.sum(abs(error) > atol + rtol * abs(truth[k]))), "probe_count": len(error)}
    return answer


def contrast(stages):
    xs = [np.asarray(stages[k]) for k in STAGES]
    require(all(x.ndim == 1 and x.shape == xs[0].shape and np.isfinite(x).all() for x in xs), "stage vector shape")
    pieces = np.array([x - y for x, y in zip(xs, xs[1:])])
    total = xs[0] - xs[-1]
    # Independent scalar reductions retain all cross inner-products.
    gram = np.array([[math.fsum(a * b for a, b in zip(x, y)) / len(total) for y in pieces] for x in pieces])
    COUNTS["contrast_summaries"] += 1
    COUNTS["cross_inner_products"] += 10
    return {"probe_count": len(total), "term_order": list(TERMS),
        "term_rms": np.sqrt(np.diag(gram)).tolist(), "term_max_abs": np.max(abs(pieces), axis=1).tolist(),
        "term_mean": np.mean(pieces, axis=1).tolist(), "gram_mean_inner_products": gram.tolist(),
        "cross_terms_twice_inner_product": [{"left": TERMS[i], "right": TERMS[j], "value": float(2 * gram[i, j])}
            for i in range(5) for j in range(i + 1, 5)],
        "total_error_rms": float(np.sqrt(np.mean(total * total))),
        "squared_error_sum_diagonal": float(np.trace(gram)),
        "squared_error_sum_including_cross_terms": float(gram.sum()),
        "pointwise_identity_max_abs": float(np.max(abs(pieces.sum(axis=0) - total))),
        "squared_error_identity_abs": float(abs(gram.sum() - np.mean(total * total))),
        "components_are_independent_variances": False}


def audit(repo, out, archive_dir):
    reader = Reader()
    old = reader.load(archive_dir / "report.json")
    equal(reader.bindings[archive_dir / "report.json"], ARCHIVE_HASH, "original report hash")
    old_protocol = reader.load(archive_dir / "protocol.json")
    equal(digest(old_protocol), ARCHIVE_PROTOCOL_HASH, "original protocol hash")
    equal(old["protocol"], old_protocol, "original protocol payload")
    old_frozen = [reader.load(archive_dir / f"frozen-{i:02d}.json") for i in range(1, 25)]
    old_barrier = reader.load(archive_dir / "freeze-barrier.json")
    equal(old_barrier, old["freeze_barrier"], "original freeze barrier")
    equal(digest(old_frozen), old_barrier["frozen_records_sha256"], "original frozen fits binding")
    old_data, dataset_by_key = {}, {}
    for record in old["datasets"]:
        raw = reader.load(archive_dir / f"dataset-{record['ordinal']:02d}.json")
        equal(digest(raw), record["record_sha256"], "original paired data record hash")
        for i, split in enumerate(raw["splits"]):
            s = np.asarray(split["states"], dtype=np.int64)
            z, labels = (np.asarray(split[k], dtype=np.float64) for k in ("coordinates", "labels"))
            equal(array_digest(s, z, labels), split["sha256"], "original raw array hash")
            equal(split["sha256"], record["split_sha256"][i], "original linked array hash")
        train = raw["splits"][0]
        key = raw["scenario"], raw["seed"], raw["u"]
        old_data[key] = (np.asarray(train["states"], dtype=np.int64), np.asarray(train["coordinates"]), np.asarray(train["labels"]))
        dataset_by_key[key] = record
    equal(len(old_data), 48, "paired training dataset count")
    report = reader.load(out / "report.json")
    protocol = reader.load(out / "protocol.json")
    execution = reader.load(out / "execution.json")
    barrier = reader.load(out / "freeze-barrier.json")
    equal(report["protocol"], protocol, "diagnostic protocol payload")
    equal(digest(protocol), report["protocol_sha256"], "diagnostic protocol hash")
    equal(execution["protocol_sha256"], report["protocol_sha256"], "prefit protocol hash")
    equal(execution["recorded_before_fits"], True, "prefit binding marker")
    equal(execution["sources"], report["source_sha256"], "diagnostic source mapping")
    for mapping in (old["source_sha256"], report["source_sha256"]):
        for relative, expected in mapping.items():
            equal(hashlib.sha256((repo / "src/heterodiff" / relative).read_bytes()).hexdigest(), expected, "bound source unchanged")
    equal(protocol["archive_report_sha256"], ARCHIVE_HASH, "predeclared archive")
    equal(protocol["archive_protocol_sha256"], ARCHIVE_PROTOCOL_HASH, "predeclared archive protocol")
    equal(protocol["scenarios"], [list(x) for x in SCENARIOS], "fixed scenarios")
    for key, expected in (("methods", METHODS), ("seeds", SEEDS), ("budgets", BUDGETS), ("grid", GRID),
            ("quadrature_points_per_cell", LEVELS), ("ordered_terms", TERMS)):
        equal(protocol[key], list(expected), "fixed " + key)
    equal(protocol["optimizer"], {"method": "L-BFGS-B", "start": "ZERO", **OPTIMIZER, "Newton_polishing": False}, "fixed optimizer")
    equal(protocol["primary_quadrature"], 32, "q32 primary")
    equal(protocol["penalty_P"], {"roughness": 1e-4, "ridge": 1e-6}, "fixed penalties")
    equal(protocol["penalty_U"], {"roughness": 0., "ridge": 0.}, "both penalties removed")
    equal(protocol["approximation_tolerances"], {k: list(v) for k, v in TOLERANCES.items()}, "scientific tolerances")
    frozen_pop = [reader.load(out / f"population-{i:03d}.json") for i in range(1, 129)]
    frozen_emp = [reader.load(out / f"empirical-{i:02d}.json") for i in range(1, 25)]
    equal(digest({"population": frozen_pop, "empirical": frozen_emp}), barrier["frozen_record_sha256"], "all controls freeze hash")
    equal(barrier, report["freeze_barrier"], "freeze barrier payload")
    equal(barrier["new_fits"], 512, "512 fixed diagnostic fits")
    equal(barrier["before_evaluation_probe_comparisons"], True, "freeze-before-probe marker")
    expected_pop = [(name, u, level, method, regular) for name, _, _ in SCENARIOS for u in GRID[:-1]
        for level in LEVELS for method in METHODS for regular in (True, False)]
    equal([(r["scenario"], r["u"], r["quadrature"], r["method"], r["regularized"]) for r in frozen_pop],
        expected_pop, "population roster")
    expected_emp = [(name, seed, method, n) for name, _, _ in SCENARIOS for seed in SEEDS for method in METHODS for n in BUDGETS]
    equal([(r["scenario"], r["seed"], r["method"], r["train_budget"]) for r in frozen_emp], expected_emp, "empirical roster")
    for raw, final in zip(frozen_pop, report["population_controls"]):
        equal({k: final[k] for k in raw}, raw, "population raw/final binding")
    for raw, final in zip(frozen_emp, report["routes"]):
        equal({k: final[k] for k in raw}, raw, "empirical raw/final binding")
        separate = reader.load(out / f"route-{final['ordinal']:02d}.json")
        equal(separate, final, "individual diagnostic route binding")
    # Only now import the unchanged target. No fit or new runner is imported.
    sys.path.insert(0, str(repo / "src"))
    from heterodiff.evaluation.continuous_fiber_conditional_benchmark import ContinuousFiberSpec
    from heterodiff.evaluation.continuous_fiber_grid_target import ContinuousFiberGridTarget
    rho = 393217 / 524288
    oracles = {name: ContinuousFiberGridTarget(ContinuousFiberSpec(theta=theta, observation_value=y,
        type_probabilities=(1 - rho, rho)), GRID) for name, theta, y in SCENARIOS}
    settings = {name: (theta, y) for name, theta, y in SCENARIOS}
    es = np.r_[np.array((0, 1), dtype=np.int64), np.full(256, 2, dtype=np.int64)]
    ez = np.r_[0., 0., np.linspace(-4., 4., 256)]
    F = {k: features(es, ez, i) for i, k in enumerate(TOLERANCES)}
    equal(protocol["evaluation_coordinates"], ez[2:].tolist(), "unchanged evaluation roster")
    feature_norms = {k: {"max_row_l2": float(np.max(np.linalg.norm(x, axis=1))),
        "continuous_spectral_norm_div_sqrt_n": float(np.linalg.norm(x[2:], 2) / 16)} for k, x in F.items()}
    tree_near(report["evaluation_feature_norms"], feature_norms, "feature readback norms")
    P = penalty_matrix()
    qs = {q: quadrature(q) for q in LEVELS}
    targets = {(name, u): target(o, u, es, ez) for name, o in oracles.items() for u in GRID}
    qt = {(name, u, q): target(o, u, qs[q][0], qs[q][1])["value"] for name, o in oracles.items()
        for u in GRID[:-1] for q in LEVELS}
    popmap, distances = {}, {}
    for r in report["population_controls"]:
        name, method, u, q, regular = r["scenario"], r["method"], r["u"], r["quadrature"], r["regularized"]
        theta, y = settings[name]
        floor, maximum, A = observation_bounds(theta, y)
        s, z, w, X = qs[q]
        labels = np.exp(qt[name, u, q])
        equal(array_digest(labels), r["target_label_sha256"], "population mean label hash")
        equal(array_digest(s, z, w), r["quadrature_input_sha256"], "population quadrature input hash")
        c = np.asarray(r["coefficients"])
        b = baseline(theta, y, u, method, s, z)["value"]
        distances["population", r["ordinal"]] = audit_fit(r["fit"], c, X, labels, b, w, maximum, floor, A, P if regular else np.zeros((35, 35)))
        values = physical(theta, y, u, method, c, es, ez, F)
        for k in TOLERANCES:
            near(r["evaluation"][k], values[k], "population coefficient readback", atol=2e-11, rtol=2e-11)
        popmap[name, method, q, regular, u] = r
    for r in report["population_controls"]:
        name, method, u, q, regular = r["scenario"], r["method"], r["u"], r["quadrature"], r["regularized"]
        theta, y = settings[name]
        other = popmap[name, method, 48 - q, regular, u]
        c, other_c = np.asarray(r["coefficients"]), np.asarray(other["coefficients"])
        s, z, w, X = qs[q]
        b = baseline(theta, y, u, method, s, z)["value"]
        J, g = risk(other_c, X, np.exp(qt[name, u, q]), b, w, observation_bounds(theta, y)[1], P if regular else np.zeros((35, 35)))
        expected = {"other_profile_ordinal": other["ordinal"], "other_coefficients_on_this_quadrature_objective": J,
            "other_coefficients_on_this_quadrature_gradient": g.tolist(),
            "other_coefficients_on_this_quadrature_gradient_max_abs": float(np.max(abs(g))),
            "coefficient_difference_max_abs": float(np.max(abs(c - other_c))),
            "coefficient_difference_l2": float(np.linalg.norm(c - other_c)), "pure_quadrature_error_claimed": False}
        tree_near(r["cross_quadrature_control"], expected, "cross-quadrature objective/gradient")
    means = {}
    for key, (s, z, _) in old_data.items():
        name, _, u = key
        means[key] = np.exp(target(oracles[name], u, s, z)["value"])
    original_routes = {(r["scenario"], r["seed"], r["method"], r["train_budget"]): r for r in old["routes"]}
    atom_max = {"M_minus_P": 0., "U_minus_T": 0.}
    route_summaries = []
    for route in report["routes"]:
        name, seed, method, n = route["scenario"], route["seed"], route["method"], route["train_budget"]
        theta, y = settings[name]
        floor, maximum, A = observation_bounds(theta, y)
        original = original_routes[name, seed, method, n]
        pooled = {q: {k: {stage: [] for stage in STAGES} for k in TOLERANCES} for q in LEVELS}
        for i, node in enumerate(route["evaluation_nodes"]):
            u = GRID[i]
            equal(node["u"], u, "ordered evaluation node")
            truth = targets[name, u]
            for k in TOLERANCES:
                near(node["target"][k], truth[k], "independent target readback", atol=2e-13, rtol=2e-13)
                near(original["evaluation_nodes"][i]["target"][k], truth[k], "unchanged original target", atol=2e-13, rtol=2e-13)
            cs = {stage: np.zeros(35) for stage in ("A", "N", "M")}
            if u < 1:
                saved = route["nodes"][i]
                s, z, Y = old_data[name, seed, u]
                h = means[name, seed, u]
                equal(array_digest(s[:n], z[:n], Y[:n]), saved["training_prefix_sha256"], "same archived noisy prefix")
                equal(saved["training_prefix_sha256"], original["nodes"][i]["training_prefix_sha256"], "original prefix link")
                X = features(s[:n], z[:n])
                b = baseline(theta, y, u, method, s[:n], z[:n])["value"]
                w = np.full(n, 1 / n)
                cs["A"] = np.asarray(saved["A_coefficients"])
                equal(saved["A_coefficients"], original["nodes"][i]["fit"]["physical_coefficients"], "A raw coefficients preserved")
                near(risk(cs["A"], X, Y[:n], b, w, maximum, P)[0],
                    original["nodes"][i]["fit"]["final_penalized_risk"], "original objective readback")
                for stage, labels in (("N", Y[:n]), ("M", h[:n])):
                    control = saved["controls"][stage]
                    cs[stage] = np.asarray(control["coefficients"])
                    equal(control["labels_sha256"], array_digest(labels), "same noisy/mean label identity")
                    distances["empirical", route["ordinal"], i, stage] = audit_fit(
                        control["fit"], cs[stage], X, labels, b, w, maximum, floor, A, P)
                v = X.T @ (Y[:n] - h[:n]) / (n * maximum)
                near(saved["realized_label_gradient_perturbation"], v, "conditional label perturbation")
                near(saved["realized_label_gradient_perturbation_l2"], np.linalg.norm(v), "conditional label perturbation norm")
            actual = {stage: physical(theta, y, u, method, c, es, ez, F) for stage, c in cs.items()}
            for stage, arrays in actual.items():
                for k in TOLERANCES:
                    near(node["stages"][stage][k], arrays[k], "stage raw coefficient readback", atol=2e-11, rtol=2e-11)
                    if stage == "A":
                        near(arrays[k], original["evaluation_nodes"][i]["physical"][k], "original A arrays preserved", atol=2e-11, rtol=2e-11)
            for q in LEVELS:
                ps = {stage: popmap[name, method, q, regular, u] for stage, regular in (("P", True), ("U", False))} if u < 1 else {}
                pc = {stage: np.asarray(ps[stage]["coefficients"]) if u < 1 else np.zeros(35) for stage in ("P", "U")}
                vals = {**actual, **{stage: physical(theta, y, u, method, c, es, ez, F) for stage, c in pc.items()}, "T": truth}
                chain = node["chains"][str(q)]
                equal(chain["population_profile_ordinals"], {stage: p["ordinal"] for stage, p in ps.items()}, "population links")
                # Use independently reconstructed arrays for all comparisons.
                for k in TOLERANCES:
                    tree_near(chain["continuous"][k], contrast({stage: v[k][2:] for stage, v in vals.items()}), "continuous five-term contrasts")
                    if u < 1:
                        for stage in STAGES:
                            pooled[q][k][stage].extend(vals[stage][k][2:].tolist())
                tree_near(chain["atomic_value"], contrast({stage: v["value"][:2] for stage, v in vals.items()}), "atomic five-term contrasts")
                for stage in STAGES[:-1]:
                    tree_near(chain["stage_accuracy"][stage], accuracy(
                        {k: vals[stage][k][2:] for k in TOLERANCES}, {k: truth[k][2:] for k in TOLERANCES}), "unchanged stage accuracy")
                if u < 1:
                    atom_max["M_minus_P"] = max(atom_max["M_minus_P"], float(np.max(abs(vals["M"]["value"][:2] - vals["P"]["value"][:2]))))
                    atom_max["U_minus_T"] = max(atom_max["U_minus_T"], float(np.max(abs(vals["U"]["value"][:2] - truth["value"][:2]))))
                else:
                    for stage in STAGES[:-1]:
                        for k in TOLERANCES:
                            near(vals[stage][k], truth[k], "terminal zero-residual chain", atol=2e-13, rtol=2e-13)
            if u < 1:
                sq, zq, wq, Xq = qs[32]
                bq = baseline(theta, y, u, method, sq, zq)["value"]
                tq = qt[name, u, 32]
                qc = {**cs, **{stage: np.asarray(popmap[name, method, 32, reg, u]["coefficients"]) for stage, reg in (("P", True), ("U", False))}}
                for stage, c in qc.items():
                    delta = bq + Xq @ c - tq
                    excess = float(wq @ (np.exp(tq) * (np.expm1(delta) - delta)) / maximum)
                    near(node["common_primary_population_excess_risk"][stage], excess, "common q32 unpenalized excess risk")
                    COUNTS["common_q32_stage_risks"] += 1
                for stage, reg in (("P", True), ("U", False)):
                    lo, hi = [popmap[name, method, q, reg, u] for q in LEVELS]
                    expected = {k: {"max_abs": float(np.max(abs(np.asarray(lo["evaluation"][k]) - hi["evaluation"][k]))),
                        "rms": float(np.sqrt(np.mean((np.asarray(lo["evaluation"][k])[2:] - hi["evaluation"][k][2:]) ** 2)))} for k in TOLERANCES}
                    tree_near(node["quadrature_plus_solver_response"][stage], expected, "q16/q32 physical response")
        for q in LEVELS:
            for k in TOLERANCES:
                tree_near(route["active_decomposition"][str(q)][k], contrast(pooled[q][k]), "pooled active contrasts")
        route_summaries.append({"scenario": name, "seed": seed, "method": method, "budget": n,
            "primary_term_rms": {k: route["active_decomposition"]["32"][k]["term_rms"] for k in TOLERANCES},
            "primary_total_rms": {k: route["active_decomposition"]["32"][k]["total_error_rms"] for k in TOLERANCES}})
    # Reconstruct all displayed probe bounds from the coefficient-distance estimates.
    def readback(distance):
        return {k: {"max_abs_upper_bound_estimate": None if distance is None else distance * norms["max_row_l2"],
            "continuous_rms_upper_bound_estimate": None if distance is None else distance * norms["continuous_spectral_norm_div_sqrt_n"],
            "interval_certified": False} for k, norms in feature_norms.items()}
    for r in report["population_controls"]:
        tree_near(r["solve_readback_bounds"], readback(distances["population", r["ordinal"]]), "population solve readback bounds")
    for r in report["routes"]:
        for i, row in enumerate(r["solve_readback_bounds"]):
            for stage in ("N", "M"):
                tree_near(row[stage], readback(distances["empirical", r["ordinal"], i, stage]), "empirical solve readback bounds")
    equal(COUNTS["strict_fit_objective_gradient_box_checks"], 512, "all strict fits checked")
    equal(COUNTS["common_q32_stage_risks"], 960, "all common-risk readouts checked")
    reader.unchanged()
    return {"schema_version": "independent-localized-error-decomposition-audit-v1",
        "decision": "PASS_INDEPENDENT_ERROR_DECOMPOSITION_AUDIT",
        "report_sha256": reader.bindings[out / "report.json"], "protocol_sha256": report["protocol_sha256"],
        "original_report_sha256": ARCHIVE_HASH, "original_protocol_sha256": ARCHIVE_PROTOCOL_HASH,
        "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "check_counts": dict(COUNTS), "maximum_arithmetic_discrepancies_by_check": dict(MAX_ERRORS),
        "atom_control_max_abs": atom_max, "route_summaries": route_summaries,
        "input_file_sha256": {str(p.relative_to(repo)): h for p, h in reader.bindings.items()},
        "scope": {"new_fit_or_optimizer_call": False, "new_runner_or_summary_helper_imported": False,
            "forward_label_simulation": False, "unchanged_backward_oracle_readback_only": True,
            "original_archive_unchanged_through_audit": True, "all_frozen_control_contents_bound": True,
            "historical_execution_order_independently_authenticated": False,
            "numeric_readback_thresholds_are_scientific_acceptance_tolerances": False,
            "global_bounds_are_interval_certified": False, "variance_or_causal_attribution_claimed": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--output", type=Path, help="optional exclusive new audit JSON receipt")
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = (args.result or repo / "research/fixtures/continuous_localized_error_decomposition_cpu_2026_09_13").resolve()
    archive = repo / "research/fixtures/continuous_localized_learnability_cpu_2026_09_13"
    with threadpool_limits(limits=1):
        result = audit(repo, out, archive)
    encoded = payload(result)
    if args.output is not None:
        with args.output.open("xb") as handle:
            handle.write(encoded)
    print(encoded.decode(), end="")


if __name__ == "__main__":
    main()
