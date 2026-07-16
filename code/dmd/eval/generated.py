"""Metrics on generated output + human reference + jitter baselines (M7 core).

Every quantity is computed with the SAME instrument on generated and human
data (the matched-instruments principle from the E4.1 saga):

  activation_rate     fraction of active cells
  velocity_w1         1-D Wasserstein-1 to the human velocity distribution
  residual_sigma      std of residual channel on active cells (r_norm units)
  residual_rho1       lag-1 ACF of the chord-mean deviation series, computed
                      by decoding to notes on the sample's own grid
  asynchrony_sigma_ms within-chord spread (30 ms grouping)
  tempo_cv, tempo_rho1  log-Δ curve statistics (the [R14] channel)

Jitter baselines (E1.1/W1): human test excerpts with the residual channel
replaced by (a) iid N(0, sigma_hat), (b) AR(1) matched to human sigma AND
rho1. By construction they match magnitude; the structure metrics are where
they must fail - if a trained model doesn't beat them there, its timing is
calibrated noise.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from dmd.data.music import Grid, NoteSeq, decode
from dmd.eval.human_acf import acf, chord_group, chord_series


def w1_1d(a: np.ndarray, b: np.ndarray, n_q: int = 512) -> float:
    """Wasserstein-1 via quantile functions."""
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    q = np.linspace(0.0, 1.0, n_q)
    return float(np.abs(np.quantile(a, q) - np.quantile(b, q)).mean())


def grid_from_delta(delta: np.ndarray) -> Grid:
    times = np.concatenate([[0.0], np.cumsum(np.asarray(delta, np.float64))])[:-1]
    return Grid(times, source="generated")


def excerpt_metrics(D: np.ndarray, C: np.ndarray, delta: np.ndarray,
                    max_lag: int = 4) -> Dict:
    """One excerpt: D (T,P) {0,1}; C (T,P,2) DE-standardized (velocity in
    [0,1], residual in r_norm units); delta (T,) seconds."""
    active = D.astype(bool)
    vel = C[..., 0][active]
    res = C[..., 1][active]
    grid = grid_from_delta(delta)
    notes = decode(D.astype(np.uint8), C.astype(np.float32), grid)

    out = {"activation_rate": float(active.mean()),
           "velocity": vel, "residual_sigma": float(res.std()) if len(res) else np.nan}

    if len(notes) >= 16:
        # NEAREST cell, like encode(): plain searchsorted-1 misassigns
        # negative residuals to the previous cell
        right = np.clip(np.searchsorted(grid.times, notes.onset),
                        1, len(grid.times) - 1)
        left = right - 1
        use_right = (np.abs(grid.times[right] - notes.onset)
                     < np.abs(notes.onset - grid.times[left]))
        cells = np.where(use_right, right, left)
        dev_ms = (notes.onset - grid.times[cells]) * 1000.0
        # chords = SAME GRID CELL (not a 30 ms onset window): jittered onsets
        # within a step spread past any fixed window, over-splitting groups
        # and destroying series structure (caught by ground-truth test).
        # human_acf.py keeps the window definition for raw performances where
        # no trusted grid exists; here the grid is the data.
        uniq_cells, inv = np.unique(cells, return_inverse=True)
        cnt = np.bincount(inv)
        cmean = np.bincount(inv, weights=dev_ms) / cnt
        asyn = (dev_ms - cmean[inv])[cnt[inv] >= 2]
        rho = acf(cmean, max_lag)   # ordered by grid step
        out["residual_rho1"] = float(rho[0])
        out["asynchrony_sigma_ms"] = float(asyn.std()) if len(asyn) > 8 else np.nan
    else:
        out["residual_rho1"] = np.nan
        out["asynchrony_sigma_ms"] = np.nan

    logd = np.log(np.clip(delta, 1e-4, None))
    out["tempo_cv"] = float(np.exp(logd).std() / np.exp(logd).mean())
    r = acf(logd, 2)
    out["tempo_rho1"] = float(r[0])
    return out


def batch_metrics(D: np.ndarray, C: np.ndarray, delta: np.ndarray,
                  ref: Optional[Dict] = None) -> Dict:
    """Aggregate over a batch of excerpts; attach W1s vs a reference."""
    rows = [excerpt_metrics(D[i], C[i], delta[i]) for i in range(len(D))]
    vel = np.concatenate([r.pop("velocity") for r in rows]) if rows else np.array([])
    agg = {k: float(np.nanmean([r[k] for r in rows])) for k in rows[0]} if rows else {}
    agg["n_excerpts"] = len(rows)
    if ref is not None:
        agg["velocity_w1"] = w1_1d(vel, ref["velocity"])
        agg["residual_sigma_gap"] = abs(agg["residual_sigma"]
                                        - ref["residual_sigma"])
        agg["residual_rho1_gap"] = abs(agg["residual_rho1"]
                                       - ref["residual_rho1"])
        agg["tempo_rho1_gap"] = abs(agg["tempo_rho1"] - ref["tempo_rho1"])
        agg["asynchrony_gap_ms"] = abs(agg["asynchrony_sigma_ms"]
                                       - ref["asynchrony_sigma_ms"])
    return agg


def human_reference(npz_path: str, idx: np.ndarray,
                    max_excerpts: int = 512) -> Dict:
    """Reference statistics from human eval excerpts (same instruments)."""
    z = np.load(npz_path)
    idx = idx[:max_excerpts]
    D, C, delta = z["D"][idx], z["C"][idx], z["Delta"][idx]
    rows = [excerpt_metrics(D[i], C[i], delta[i]) for i in range(len(D))]
    vel = np.concatenate([r.pop("velocity") for r in rows])
    ref = {k: float(np.nanmean([r[k] for r in rows])) for k in rows[0]}
    ref["velocity"] = vel
    return ref


def jitter_excerpts(npz_path: str, idx: np.ndarray, mode: str,
                    sigma: float, rho1: float = 0.0, seed: int = 0,
                    max_excerpts: int = 512):
    """Human eval excerpts with the residual channel replaced by calibrated
    noise. mode: 'iid' or 'ar1'. Returns (D, C, delta) ready for
    batch_metrics."""
    rng = np.random.default_rng(seed)
    z = np.load(npz_path)
    idx = idx[:max_excerpts]
    D, C, delta = z["D"][idx].copy(), z["C"][idx].copy(), z["Delta"][idx].copy()
    T = D.shape[1]
    for i in range(len(D)):
        tt, pp = np.nonzero(D[i])
        if mode == "iid":
            vals = rng.normal(0.0, sigma, len(tt))
        elif mode == "ar1":
            # STEP-level AR(1), broadcast to the step's notes: matches the
            # cell-mean instrument, so the baseline hits the target rho1 as
            # MEASURED (note-level AR would be attenuated by chord averaging)
            phi = rho1
            e = rng.normal(0.0, sigma * np.sqrt(max(1 - phi**2, 1e-6)), T)
            x = np.empty(T)
            x[0] = rng.normal(0.0, sigma)
            for j in range(1, T):
                x[j] = phi * x[j - 1] + e[j]
            vals = x[tt]
        else:
            raise ValueError(mode)
        C[i][..., 1][tt, pp] = np.clip(vals, -0.5, 0.5)
    return D, C, delta
