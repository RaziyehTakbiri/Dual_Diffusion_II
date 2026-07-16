"""Ground-truth tests for the experiment-grid utilities and the generated-
output metrics (numpy-only; runnable in Claude's sandbox).

Same philosophy as always: inject known statistics, require recovery.
"""

import os
import tempfile

import numpy as np

from dmd.exp.grid import run_matrix, split_pieces
from dmd.eval.generated import (batch_metrics, excerpt_metrics,
                                human_reference, jitter_excerpts, w1_1d)

T, P = 64, 88


def _synthetic_corpus(path, n_pieces=20, per_piece=6, sigma=0.15, phi=0.5,
                      seed=0):
    rng = np.random.default_rng(seed)
    D, C, Delta, piece = [], [], [], []
    for pid in range(n_pieces):
        for _ in range(per_piece):
            d = (rng.random((T, P)) < 0.04).astype(np.uint8)
            c = np.zeros((T, P, 2), dtype=np.float32)
            c[..., 0] = rng.uniform(0.3, 0.8, (T, P))
            # STEP-level AR(1) timing (chord notes share it) + small
            # within-chord jitter: matches how humans behave and how the
            # cell-mean instrument measures structure. Note-level AR would be
            # attenuated by chord averaging - that is theory, not a bug.
            x = np.empty(T)
            e = rng.normal(0, sigma * np.sqrt(1 - phi**2), T)
            x[0] = rng.normal(0, sigma)
            for j in range(1, T):
                x[j] = phi * x[j - 1] + e[j]
            tt, pp = np.nonzero(d)
            vals = x[tt] + rng.normal(0, 0.02, len(tt))
            c[..., 1][tt, pp] = np.clip(vals, -0.49, 0.49)
            D.append(d); C.append(c)
            Delta.append(np.full(T, 0.125)); piece.append(pid)
    np.savez(path, D=np.stack(D), C=np.stack(C),
             Delta=np.stack(Delta).astype(np.float64),
             piece=np.array(piece), start=np.zeros(len(piece)))


def test_run_matrix_is_stable_and_complete():
    m = run_matrix()
    assert len(m) == 30
    assert m[0] == {"run_index": 0, "block": "ffn", "seed": 0}
    assert {r["block"] for r in m} == {"ffn", "ffn_timecond", "gated_ffn",
                                       "gru", "cfc", "node"}


def test_split_is_deterministic_and_piece_level():
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "c.npz")
        _synthetic_corpus(p, n_pieces=40)
        tr1, ev1 = split_pieces(p, eval_frac=0.2)
        tr2, ev2 = split_pieces(p, eval_frac=0.2)
        assert np.array_equal(tr1, tr2) and np.array_equal(ev1, ev2)
        z = np.load(p)
        assert not set(np.unique(z["piece"][tr1])) & set(np.unique(z["piece"][ev1]))
        assert 0.05 < len(ev1) / (len(tr1) + len(ev1)) < 0.4


def test_w1_matches_analytic_shift():
    rng = np.random.default_rng(0)
    a = rng.normal(0, 1, 20_000)
    assert abs(w1_1d(a, a + 0.3) - 0.3) < 0.02


def test_metrics_recover_injected_statistics():
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "c.npz")
        _synthetic_corpus(p, sigma=0.15, phi=0.5)
        z = np.load(p)
        m = excerpt_metrics(z["D"][0], z["C"][0], z["Delta"][0])
        assert abs(m["residual_sigma"] - 0.15) < 0.04
        assert np.isnan(m["tempo_rho1"])  # constant delta -> zero variance
        ref = human_reference(p, np.arange(60))
        assert abs(ref["residual_sigma"] - 0.15) < 0.03
        assert abs(ref["residual_rho1"] - 0.5) < 0.12, ref["residual_rho1"]


def test_jitter_baselines_match_magnitude_not_structure():
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "c.npz")
        _synthetic_corpus(p, sigma=0.15, phi=0.5)
        idx = np.arange(60)
        ref = human_reference(p, idx)
        for mode, want_rho in (("iid", 0.0), ("ar1", 0.5)):
            D, C, delta = jitter_excerpts(p, idx, mode, sigma=0.15,
                                          rho1=0.5 if mode == "ar1" else 0.0)
            agg = batch_metrics(D, C, delta, ref)
            assert abs(agg["residual_sigma"] - 0.15) < 0.03, (mode, agg)
            assert abs(agg["residual_rho1"] - want_rho) < 0.12, (mode, agg)


if __name__ == "__main__":
    import sys, traceback
    fns = [(k, v) for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for name, fn in fns:
        try:
            fn(); print(f"PASS  {name}")
        except Exception:
            failed += 1; print(f"FAIL  {name}"); traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
