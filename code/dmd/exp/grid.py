"""Experiment grid definition (Phase 1/E1 of the agenda).

TRAINING axis (one run each): block in the B0-B5 ladder x seeds. Sampling-
time switches (Δ-mode, calibration parity) are NOT training axes - every
trained model is swept over them post-hoc for free.

Scales:
  pilot: d=128, 4 layers, 20k steps  (~12 h/run on 1 GPU; validates science)
  final: d=512, 12 layers, 100k steps (AFTER the scan-optimization task)

Piece-level split: excerpts from the same performance must never straddle
train/eval (ASAP README: dedupe by piece; we split on the `piece` id stored
in the npz, hash-based, deterministic).
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from typing import Dict, List, Tuple

import numpy as np
import yaml

BLOCKS = ["ffn", "ffn_timecond", "gated_ffn", "gru", "cfc", "node"]
SEEDS = [0, 1, 2, 3, 4]

SCALES = {
    "pilot": {"d_model": 128, "trunk_layers": 4, "n_heads": 4,
              "batch_size": 32, "max_steps": 20_000, "warmup_steps": 500},
    "final": {"d_model": 512, "trunk_layers": 12, "n_heads": 8,
              "batch_size": 64, "max_steps": 100_000, "warmup_steps": 2000},
}


def run_matrix() -> List[Dict]:
    """The 30 training runs, index-addressable for parallel jobs."""
    return [{"run_index": i, "block": b, "seed": s}
            for i, (b, s) in enumerate((b, s) for b in BLOCKS for s in SEEDS)]


def make_config(base_config_path: str, block: str, seed: int,
                scale: str = "pilot") -> Dict:
    with open(base_config_path) as fh:
        cfg = yaml.safe_load(fh)
    sc = SCALES[scale]
    cfg["model"].update({"d_model": sc["d_model"],
                         "trunk_layers": sc["trunk_layers"],
                         "n_heads": sc["n_heads"], "block": block})
    cfg["train"].update({"batch_size": sc["batch_size"],
                         "max_steps": sc["max_steps"],
                         "warmup_steps": sc["warmup_steps"],
                         "seeds": [seed]})
    cfg["experiment"] = {"block": block, "seed": seed, "scale": scale}
    return cfg


def split_pieces(npz_path: str, eval_frac: float = 0.1,
                 salt: str = "dmd-v1") -> Tuple[np.ndarray, np.ndarray]:
    """Deterministic piece-level split -> (train_idx, eval_idx) over excerpts.

    Hash-based so it is stable across runs/machines and independent of piece
    ordering; salted so a future re-split is an explicit decision.
    """
    z = np.load(npz_path)
    piece = z["piece"]
    uniq = np.unique(piece)
    is_eval_piece = {
        int(p): (int(hashlib.sha1(f"{salt}:{int(p)}".encode()).hexdigest(), 16)
                 % 10_000) < eval_frac * 10_000
        for p in uniq
    }
    mask = np.array([is_eval_piece[int(p)] for p in piece])
    return np.nonzero(~mask)[0], np.nonzero(mask)[0]


def write_split_npz(npz_path: str, out_prefix: str, eval_frac: float = 0.1):
    """Materialize train/eval npz files + a manifest json. Returns paths."""
    z = np.load(npz_path)
    tr, ev = split_pieces(npz_path, eval_frac)
    paths = {}
    for name, idx in (("train", tr), ("eval", ev)):
        p = f"{out_prefix}_{name}.npz"
        np.savez_compressed(p, **{k: z[k][idx] for k in z.files})
        paths[name] = p
    manifest = {"source": npz_path, "eval_frac": eval_frac,
                "n_train": int(len(tr)), "n_eval": int(len(ev)),
                "n_train_pieces": int(len(np.unique(z["piece"][tr]))),
                "n_eval_pieces": int(len(np.unique(z["piece"][ev])))}
    with open(f"{out_prefix}_split.json", "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(manifest)
    return paths


def prepare_run(base_config_path: str, run_index: int, scale: str,
                out_dir: str) -> Tuple[str, Dict]:
    """Write the config for run `run_index`; returns (config_path, spec)."""
    spec = run_matrix()[run_index]
    cfg = make_config(base_config_path, spec["block"], spec["seed"], scale)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"run{run_index:02d}_{spec['block']}"
                                 f"_s{spec['seed']}.yaml")
    with open(path, "w") as fh:
        yaml.safe_dump(cfg, fh)
    return path, spec
