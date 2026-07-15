"""E4.1b: score-aligned note-level micro-timing (the clean instrument).

For each ASAP performance with an aligned score:
  1. Build the score-time -> performance-time warp through the PAIRED beat
     annotations (piecewise linear between beats, edge-slope extrapolation).
  2. Warp every score-note onset into performance time = its 'metronomic
     within-beat' expected time.
  3. Match performed notes to score notes (per pitch, monotone greedy,
     +/- window).
  4. Micro-deviation d = performed onset - warped expected onset. This is
     note-level timing relative to the LOCAL beat tempo - free of both
     drift aliasing (fixed grid) and subdivision-rhythm mismatch (asap grid),
     because expected times come from the score's actual rhythm.

Score-exact chords (identical score onsets) define chord groups: the ACF runs
on the chord-mean series; within-chord spread is the asynchrony (melody lead).
Score metrical position is exact, so notes are also stratified into
duple-aligned (on the sixteenth lattice) vs non-duple (triplets, ornaments).

Caveat (documented for the paper): ASAP beat annotations are derived from the
performances, so deviations of beat-defining notes are partially absorbed;
on-beat deviations are therefore biased low - stratified stats expose this.

Usage:
  python -m dmd.eval.score_align --asap_root <asap> --out results/score_align
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Dict, List

import numpy as np

from dmd.data.midi_lite import load_midi_lite
from dmd.data.music import NoteSeq, beats_from_annotation_txt
from dmd.eval.human_acf import acf

WINDOW_S = 0.250      # matching window around expected time
SUBDIV = 4            # sixteenth lattice for the duple/non-duple split
OFFGRID_TOL = 0.08    # fraction of a subdivision step


def make_warp(beats_score: np.ndarray, beats_perf: np.ndarray):
    """Piecewise-linear map score-time -> perf-time; edge-slope extrapolation."""
    bs, bp = beats_score, beats_perf

    def warp(t: np.ndarray) -> np.ndarray:
        t = np.asarray(t, dtype=np.float64)
        out = np.interp(t, bs, bp)
        s0 = (bp[1] - bp[0]) / (bs[1] - bs[0])
        s1 = (bp[-1] - bp[-2]) / (bs[-1] - bs[-2])
        out = np.where(t < bs[0], bp[0] + (t - bs[0]) * s0, out)
        out = np.where(t > bs[-1], bp[-1] + (t - bs[-1]) * s1, out)
        return out

    return warp


def match_notes(warped: np.ndarray, pitches_s: np.ndarray,
                perf: NoteSeq, window: float = WINDOW_S):
    """Per-pitch monotone greedy matching. Returns (score_idx, perf_idx)."""
    mi, mj = [], []
    for p in np.unique(pitches_s):
        si = np.nonzero(pitches_s == p)[0]
        pj = np.nonzero(perf.pitch == p)[0]
        si = si[np.argsort(warped[si], kind="stable")]
        w, o = warped[si], perf.onset[pj]
        i = j = 0
        while i < len(si) and j < len(pj):
            d = o[j] - w[i]
            if d < -window:
                j += 1                    # extra performed note (mistake/repeat)
            elif d > window:
                i += 1                    # unperformed score note
            else:
                mi.append(si[i]); mj.append(pj[j])
                i += 1; j += 1
    return np.asarray(mi, dtype=np.int64), np.asarray(mj, dtype=np.int64)


def metrical_split(onsets_score: np.ndarray, beats_score: np.ndarray,
                   subdiv: int = SUBDIV, tol: float = OFFGRID_TOL):
    """(position 0..subdiv-1, is_duple) per note from EXACT score positions."""
    k = np.clip(np.searchsorted(beats_score, onsets_score, "right") - 1,
                0, len(beats_score) - 2)
    frac = (onsets_score - beats_score[k]) / (beats_score[k + 1] - beats_score[k])
    sub = frac * subdiv
    pos = np.rint(sub)
    duple = np.abs(sub - pos) <= tol
    return (pos.astype(np.int64) % subdiv), duple


_SCORE_CACHE: Dict[str, tuple] = {}   # 1067 perfs share 235 scores


def _cached_score(score_mid: str, score_ann: str):
    key = score_mid
    if key not in _SCORE_CACHE:
        _SCORE_CACHE[key] = (load_midi_lite(score_mid),
                             beats_from_annotation_txt(score_ann)[0])
    return _SCORE_CACHE[key]


def analyze_pair(score_mid: str, score_ann: str, perf_mid: str, perf_ann: str,
                 max_lag: int = 8) -> Dict:
    score, bs = _cached_score(score_mid, score_ann)
    bp, _ = beats_from_annotation_txt(perf_ann)
    if len(bs) != len(bp):
        raise ValueError(f"beat count mismatch ({len(bs)} vs {len(bp)})")
    perf = load_midi_lite(perf_mid)
    if len(score) < 32 or len(perf) < 32:
        raise ValueError("too few notes")

    warped = make_warp(bs, bp)(score.onset)
    mi, mj = match_notes(warped, score.pitch, perf)
    if len(mi) < 32:
        raise ValueError("too few matches")
    d_ms = (perf.onset[mj] - warped[mi]) * 1000.0

    pos, duple = metrical_split(score.onset[mi], bs)
    order = np.argsort(warped[mi], kind="stable")
    d_ord, on_s = d_ms[order], score.onset[mi][order]

    # chords = identical score onsets (exact ties in the quantized score)
    gid = np.concatenate([[0], np.cumsum(np.diff(on_s) > 1e-6)])
    n_g = gid[-1] + 1
    cnt = np.bincount(gid, minlength=n_g)
    cmean = np.bincount(gid, weights=d_ord, minlength=n_g) / np.maximum(cnt, 1)
    asyn = (d_ord - cmean[gid])[cnt[gid] >= 2]
    rho = acf(cmean, max_lag)

    dup = d_ms[duple]
    # duple-only chord-mean series for a structure estimate free of ornaments
    ord_d = order[duple[order]]
    on_d, dd = score.onset[mi][ord_d], d_ms[ord_d]
    gd = np.concatenate([[0], np.cumsum(np.diff(on_d) > 1e-6)]) if len(on_d) else np.zeros(0, np.int64)
    cd = (np.bincount(gd, weights=dd) / np.maximum(np.bincount(gd), 1)) if len(on_d) else np.zeros(0)
    rho_dup = acf(cd, max_lag)

    return {
        "n_score": int(len(score)), "n_perf": int(len(perf)),
        "n_matched": int(len(mi)),
        "match_rate_score": float(len(mi) / len(score)),
        "match_rate_perf": float(len(mi) / len(perf)),
        "bias_ms": float(np.median(d_ms)),
        "sigma_ms": float(d_ms.std()),
        "sigma_duple_ms": float(dup.std()) if len(dup) > 32 else float("nan"),
        "sigma_offbeat_ms": float(d_ms[pos != 0].std()) if (pos != 0).sum() > 32 else float("nan"),
        "frac_nonduple": float(1.0 - duple.mean()),
        "asynchrony_sigma_ms": float(asyn.std()) if len(asyn) > 32 else float("nan"),
        **{f"rho_{k+1}": float(rho[k]) for k in range(max_lag)},
        **{f"rho_duple_{k+1}": float(rho_dup[k]) for k in range(max_lag)},
    }


def main(argv: List[str] | None = None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asap_root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max_lag", type=int, default=8)
    ap.add_argument("--max_pieces", type=int, default=0)
    ap.add_argument("--start", type=int, default=0,
                    help="slice start (for chunked runs on slow filesystems)")
    args = ap.parse_args(argv)

    rows, skipped = [], 0
    with open(os.path.join(args.asap_root, "metadata.csv"), newline="") as fh:
        rd = csv.DictReader(fh)
        ann_col = next(c for c in rd.fieldnames
                       if c.strip().lower() in ("performance_anotations",
                                                "performance_annotations"))
        meta = list(rd)
    if args.start:
        meta = meta[args.start:]
    if args.max_pieces:
        meta = meta[: args.max_pieces]
    for r in meta:
        j = lambda c: os.path.join(args.asap_root, r[c].strip())
        try:
            row = analyze_pair(j("midi_score"), j("midi_score_annotations"),
                               j("midi_performance"), j(ann_col), args.max_lag)
            row["path"] = j("midi_performance")
            row["composer"] = r.get("composer", "?")
            rows.append(row)
        except Exception as e:  # noqa: BLE001
            skipped += 1
            print(f"[skip] {r.get('midi_performance','?')}: {e}", file=sys.stderr)

    with open(f"{args.out}.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader(); wr.writerows(rows)

    w = np.array([r["n_matched"] for r in rows], dtype=float); w /= w.sum()
    def agg(key):
        v = np.array([r[key] for r in rows]); ok = np.isfinite(v)
        return {"mean": float(np.average(v[ok], weights=w[ok] / w[ok].sum())),
                "sd_across_pieces": float(v[ok].std())}
    keys = (["match_rate_score", "match_rate_perf", "bias_ms", "sigma_ms",
             "sigma_duple_ms", "sigma_offbeat_ms", "frac_nonduple",
             "asynchrony_sigma_ms"]
            + [f"rho_{k}" for k in range(1, args.max_lag + 1)]
            + [f"rho_duple_{k}" for k in range(1, args.max_lag + 1)])
    summary = {"n_pieces": len(rows), "skipped": skipped,
               "aggregate": {k: agg(k) for k in keys}}
    with open(f"{args.out}.json", "w") as fh:
        json.dump(summary, fh, indent=2)
    print(f"pieces={len(rows)} skipped={skipped}")
    for k in ("match_rate_score", "sigma_ms", "sigma_duple_ms", "frac_nonduple",
              "asynchrony_sigma_ms", "rho_1", "rho_duple_1", "rho_duple_2"):
        a = summary["aggregate"][k]
        print(f"  {k:20s} {a['mean']:8.4f} (sd {a['sd_across_pieces']:.4f})")


if __name__ == "__main__":
    main()
