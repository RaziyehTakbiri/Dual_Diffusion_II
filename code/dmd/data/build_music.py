"""Build training tensors from a MIDI corpus (M2 deliverable).

Per split: stacks excerpts into one .npz (D uint8, C float32, Delta float64,
piece_id, start) and writes a per-piece round-trip audit CSV (E4.2) so every
dataset build carries its own representation-quality report.

Usage:
  python -m dmd.data.build_music --midi_glob '/dbfs/maestro/**/*.midi' \
      --grid fixed --T 256 --hop 256 --out /dbfs/dmd/maestro_fixed
  # MAESTRO splits: pass --maestro_csv maestro-v3.0.0.csv to emit
  # train/validation/test files; otherwise one 'all' split.
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import sys
from collections import defaultdict

import numpy as np

from dmd.data.music import encode, excerpts, load_midi, make_grid
from dmd.data.validate import round_trip_report


def split_map(maestro_csv: str) -> dict:
    with open(maestro_csv) as fh:
        return {row["midi_filename"]: row["split"] for row in csv.DictReader(fh)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--midi_glob", required=True)
    ap.add_argument("--maestro_csv", default=None)
    ap.add_argument("--grid", default="fixed", choices=["fixed", "asap", "tracked"])
    ap.add_argument("--annotation_map", default=None,
                    help="CSV 'midi_path,annotation_path' for --grid asap")
    ap.add_argument("--subdivision", type=int, default=4)
    ap.add_argument("--T", type=int, default=256)
    ap.add_argument("--hop", type=int, default=256)
    ap.add_argument("--out", required=True, help="output prefix")
    args = ap.parse_args(argv)

    ann = {}
    if args.annotation_map:
        with open(args.annotation_map) as fh:
            ann = {r[0]: r[1] for r in csv.reader(fh) if len(r) >= 2}
    splits = split_map(args.maestro_csv) if args.maestro_csv else {}

    buckets = defaultdict(lambda: {"D": [], "C": [], "Delta": [],
                                   "piece": [], "start": []})
    audit_rows, skipped = [], 0
    paths = sorted(glob.glob(args.midi_glob, recursive=True))
    for pid, path in enumerate(paths):
        split = next((s for k, s in splits.items() if path.endswith(k)), "all")
        try:
            notes = load_midi(path)
            grid = make_grid(notes, args.grid, args.subdivision,
                             beat_annotation=ann.get(path))
            enc = encode(notes, grid)
            rep = round_trip_report(notes, enc)
            audit_rows.append({"path": path, "split": split, **rep.as_dict()})
            D, C, Delta, starts = excerpts(enc, args.T, args.hop)
            b = buckets[split]
            b["D"].append(D); b["C"].append(C); b["Delta"].append(Delta)
            b["piece"].append(np.full(len(D), pid)); b["start"].append(starts)
        except Exception as e:  # noqa: BLE001 - corpus robustness, log & skip
            skipped += 1
            print(f"[skip] {path}: {e}", file=sys.stderr)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    for split, b in buckets.items():
        np.savez_compressed(
            f"{args.out}_{split}.npz",
            D=np.concatenate(b["D"]), C=np.concatenate(b["C"]),
            Delta=np.concatenate(b["Delta"]),
            piece=np.concatenate(b["piece"]), start=np.concatenate(b["start"]),
        )
        print(f"{split}: {sum(len(d) for d in b['D'])} excerpts "
              f"-> {args.out}_{split}.npz")
    with open(f"{args.out}_audit.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(audit_rows[0].keys()))
        wr.writeheader(); wr.writerows(audit_rows)
    keep = np.array([r["keep_rate"] for r in audit_rows])
    wrap = np.array([r["wrap_rate"] for r in audit_rows])
    err = np.array([r["onset_max_ms"] for r in audit_rows])
    print(f"pieces={len(audit_rows)} skipped={skipped} | keep={keep.mean():.3f} "
          f"wrap={wrap.mean():.4f} max_onset_err={err.max():.4f} ms")


if __name__ == "__main__":
    main()
