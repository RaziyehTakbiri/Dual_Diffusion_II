"""Human expressive-timing structure study (agenda E4.3, review W6).

Produces, per performance and aggregated:
  - micro-timing sigma (ms) and full deviation distribution stats
  - autocorrelation of the deviation series at lags 1..max_lag, computed on the
    CHORD-MEAN series (tempo/phrasing structure) [R5a]
  - within-chord asynchrony sigma (melody-lead structure) [R5b]
  - metrical profile: residual mean/spread by position-in-beat (meaningful for
    beat-anchored grids: asap/synthetic; arbitrary phase for 'fixed')
  - representation audit: keep/wrap/collision rates (round-trip validator)

This script pins the paper's ground-truth numbers: the manuscript's human
rho_1 ~ 0.12 was measured on an estimated constant-tempo grid; re-measuring on
the ASAP-annotated grid tests whether the old grid destroyed structure.

Usage (Databricks or laptop):
  python -m dmd.eval.human_acf --midi_glob '/dbfs/maestro/**/*.mid*' \
      --grid fixed --subdivision 4 --max_pieces 200 --out results/human_acf_fixed
  # once ASAP lands: --grid asap --annotation_map <csv midi_path,annotation_path>
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np

from dmd.data.music import Encoded, Grid, NoteSeq, encode, load_midi, make_grid
from dmd.data.validate import round_trip_report

CHORD_WINDOW_S = 0.030  # [R5] chord grouping window


# ------------------------------------------------------------ core estimators
def deviation_series_ms(notes: NoteSeq, enc: Encoded) -> np.ndarray:
    """Per kept note, residual in ms, ordered by onset."""
    idx = np.nonzero(enc.kept)[0]
    cells = enc.cell[idx]
    r = enc.C[cells, notes.pitch[idx] - 21, 1].astype(np.float64)
    return r * enc.grid.delta[cells] * 1000.0


def chord_group(onsets: np.ndarray, window_s: float = CHORD_WINDOW_S) -> np.ndarray:
    """Group ids for onset-sorted notes: a note joins the current group if it is
    within `window_s` of the group's FIRST onset."""
    gid = np.zeros(len(onsets), dtype=np.int64)
    if len(onsets) == 0:
        return gid
    start, g = onsets[0], 0
    for i in range(1, len(onsets)):
        if onsets[i] - start > window_s:
            g += 1
            start = onsets[i]
        gid[i] = g
    return gid


def chord_series(dev_ms: np.ndarray, gid: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """(chord-mean deviation series, within-chord asynchrony samples)."""
    n_g = gid.max() + 1 if len(gid) else 0
    sums = np.bincount(gid, weights=dev_ms, minlength=n_g)
    cnts = np.bincount(gid, minlength=n_g)
    means = sums / np.maximum(cnts, 1)
    asyn = dev_ms - means[gid]
    return means, asyn[cnts[gid] >= 2]


def acf(x: np.ndarray, max_lag: int) -> np.ndarray:
    """Standard biased ACF estimator, lags 1..max_lag."""
    x = np.asarray(x, dtype=np.float64)
    if len(x) < max_lag + 2:
        return np.full(max_lag, np.nan)
    x = x - x.mean()
    denom = float((x * x).sum())
    if denom == 0:
        return np.full(max_lag, np.nan)
    return np.array([(x[:-k] * x[k:]).sum() / denom for k in range(1, max_lag + 1)])


def metrical_profile(notes: NoteSeq, enc: Encoded) -> Dict[str, List[float]]:
    """Residual statistics by position-in-beat (cell index mod subdivision)."""
    idx = np.nonzero(enc.kept)[0]
    cells = enc.cell[idx]
    dev = deviation_series_ms(notes, enc)
    s = enc.grid.subdivision
    pos = cells % s
    prof = {"position": list(range(s)), "mean_ms": [], "sigma_ms": [], "count": []}
    for p in range(s):
        d = dev[pos == p]
        prof["mean_ms"].append(float(d.mean()) if len(d) else float("nan"))
        prof["sigma_ms"].append(float(d.std()) if len(d) else float("nan"))
        prof["count"].append(int(len(d)))
    return prof


# ------------------------------------------------------------- per-piece run
def analyze_piece(notes: NoteSeq, grid: Grid, max_lag: int = 8) -> Dict:
    enc = encode(notes, grid)
    rt = round_trip_report(notes, enc)
    dev = deviation_series_ms(notes, enc)
    onsets = notes.onset[enc.kept]
    gid = chord_group(onsets)
    cmeans, asyn = chord_series(dev, gid)
    rho = acf(cmeans, max_lag)
    return {
        "n_notes": int(len(notes)),
        "n_chord_groups": int(len(cmeans)),
        "sigma_ms": float(dev.std()) if len(dev) else float("nan"),
        **{f"rho_{k+1}": float(rho[k]) for k in range(max_lag)},
        "asynchrony_sigma_ms": float(asyn.std()) if len(asyn) else float("nan"),
        "keep_rate": rt.keep_rate,
        "wrap_rate": rt.wrap_rate,
        "collision_rate": rt.collision_rate,
        "onset_max_err_ms": rt.onset_max_ms,
        "metrical": metrical_profile(notes, enc),
    }


def aggregate(rows: List[Dict], max_lag: int = 8) -> Dict:
    """Note-weighted means +/- across-piece sd for the headline quantities."""
    w = np.array([r["n_notes"] for r in rows], dtype=np.float64)
    w = w / w.sum()

    def stat(key):
        v = np.array([r[key] for r in rows], dtype=np.float64)
        ok = np.isfinite(v)
        return (float(np.average(v[ok], weights=w[ok] / w[ok].sum())),
                float(v[ok].std()))

    out = {"n_pieces": len(rows), "n_notes_total": int(sum(r["n_notes"] for r in rows))}
    for key in (["sigma_ms", "asynchrony_sigma_ms", "keep_rate", "wrap_rate",
                 "collision_rate"] + [f"rho_{k}" for k in range(1, max_lag + 1)]):
        m, s = stat(key)
        out[key] = {"mean": m, "sd_across_pieces": s}
    return out


def main(argv: Optional[List[str]] = None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--midi_glob", required=True)
    ap.add_argument("--grid", default="fixed", choices=["fixed", "asap", "tracked"])
    ap.add_argument("--annotation_map", default=None,
                    help="CSV 'midi_path,annotation_path' (required for --grid asap)")
    ap.add_argument("--subdivision", type=int, default=4)
    ap.add_argument("--max_lag", type=int, default=8)
    ap.add_argument("--max_pieces", type=int, default=0, help="0 = all")
    ap.add_argument("--out", required=True, help="output prefix (.csv/.json)")
    args = ap.parse_args(argv)

    ann = {}
    if args.annotation_map:
        with open(args.annotation_map) as fh:
            ann = {r[0]: r[1] for r in csv.reader(fh) if len(r) >= 2}

    paths = sorted(glob.glob(args.midi_glob, recursive=True))
    if args.max_pieces:
        paths = paths[: args.max_pieces]
    rows, skipped = [], 0
    for path in paths:
        try:
            notes = load_midi(path)
            grid = make_grid(notes, args.grid, args.subdivision,
                             beat_annotation=ann.get(path))
            row = analyze_piece(notes, grid, args.max_lag)
            row["path"] = path
            rows.append(row)
        except Exception as e:  # noqa: BLE001 - survey robustness, log & skip
            skipped += 1
            print(f"[skip] {path}: {e}", file=sys.stderr)

    flat = [{k: v for k, v in r.items() if k != "metrical"} for r in rows]
    with open(f"{args.out}.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(flat[0].keys()))
        wr.writeheader()
        wr.writerows(flat)
    summary = {"config": vars(args), "skipped": skipped,
               "aggregate": aggregate(rows, args.max_lag)}
    with open(f"{args.out}.json", "w") as fh:
        json.dump(summary, fh, indent=2)

    agg = summary["aggregate"]
    print(f"pieces={agg['n_pieces']} notes={agg['n_notes_total']} skipped={skipped}")
    for k in ("sigma_ms", "rho_1", "rho_2", "asynchrony_sigma_ms",
              "keep_rate", "wrap_rate", "collision_rate"):
        print(f"  {k:22s} {agg[k]['mean']:8.4f}  (sd {agg[k]['sd_across_pieces']:.4f})")


if __name__ == "__main__":
    main()
