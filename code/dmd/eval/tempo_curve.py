"""Beat-level tempo-curve study (E4.1 macro-rubato ground truth).

Uses ONLY the ASAP beat annotations - no MIDI, no grid, no quantization - so
the numbers are free of the residual-channel artifacts (drift aliasing on the
fixed grid; subdivision-rhythm mismatch on the interpolated sixteenth grid).

Per performance:
  - beat-period series p_i = t_{i+1} - t_i (filtered to 0.1..4 s)
  - median tempo (BPM), period CV = sd(p)/mean(p)  -> macro-rubato MAGNITUDE
  - ACF of log p at lags 1..max_lag               -> macro-rubato STRUCTURE
  - ACF of diff(log p) at lags 1..4               -> smoothness beyond trend

Usage:
  python -m dmd.eval.tempo_curve --asap_root <asap> --out results/tempo_curve
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Dict, List

import numpy as np

from dmd.data.music import beats_from_annotation_txt
from dmd.eval.human_acf import acf


def analyze_annotation(path: str, max_lag: int = 8) -> Dict:
    times, is_db = beats_from_annotation_txt(path)
    p = np.diff(times)
    p = p[(p > 0.1) & (p < 4.0)]
    if len(p) < max_lag + 4:
        raise ValueError("too few beats")
    logp = np.log(p)
    rho = acf(logp, max_lag)
    drho = acf(np.diff(logp), 4)
    return {
        "n_beats": int(len(p)),
        "bpm_median": float(60.0 / np.median(p)),
        "period_cv": float(p.std() / p.mean()),
        **{f"rho_{k+1}": float(rho[k]) for k in range(max_lag)},
        **{f"drho_{k+1}": float(drho[k]) for k in range(4)},
    }


def main(argv: List[str] | None = None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asap_root", required=True)
    ap.add_argument("--max_lag", type=int, default=8)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    meta = os.path.join(args.asap_root, "metadata.csv")
    rows, skipped = [], 0
    with open(meta, newline="") as fh:
        rd = csv.DictReader(fh)
        ann_col = next(c for c in rd.fieldnames
                       if c.strip().lower() in ("performance_anotations",
                                                "performance_annotations"))
        for r in rd:
            path = os.path.join(args.asap_root, r[ann_col].strip())
            try:
                row = analyze_annotation(path, args.max_lag)
                row["path"] = path
                row["composer"] = r.get("composer", "?")
                rows.append(row)
            except Exception as e:  # noqa: BLE001
                skipped += 1
                print(f"[skip] {path}: {e}", file=sys.stderr)

    with open(f"{args.out}.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader(); wr.writerows(rows)

    w = np.array([r["n_beats"] for r in rows], dtype=float); w /= w.sum()
    def agg(key):
        v = np.array([r[key] for r in rows]); ok = np.isfinite(v)
        return {"mean": float(np.average(v[ok], weights=w[ok] / w[ok].sum())),
                "sd_across_pieces": float(v[ok].std())}
    keys = (["bpm_median", "period_cv"]
            + [f"rho_{k}" for k in range(1, args.max_lag + 1)]
            + [f"drho_{k}" for k in range(1, 5)])
    summary = {"n_pieces": len(rows), "skipped": skipped,
               "aggregate": {k: agg(k) for k in keys}}
    with open(f"{args.out}.json", "w") as fh:
        json.dump(summary, fh, indent=2)

    print(f"pieces={len(rows)} skipped={skipped}")
    for k in ("bpm_median", "period_cv", "rho_1", "rho_2", "rho_4", "rho_8",
              "drho_1"):
        a = summary["aggregate"][k]
        print(f"  {k:12s} {a['mean']:8.4f} (sd {a['sd_across_pieces']:.4f})")


if __name__ == "__main__":
    main()
