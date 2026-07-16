"""End-to-end CPU smoke: tiny synthetic corpus -> trainer v1 -> Δ-feedback
sampler. Asserts wiring, not quality: losses finite and not exploding, gamma
grad-matched, checkpoint written, samples well-formed (no residual MASK,
delta within the clamp range, sane activation rate).

Runnable via pytest or `python tests/test_train_smoke.py`. ~60-90 s CPU.
"""

import json
import os
import tempfile

import numpy as np
import torch
import yaml

from dmd.sample.sampler import generate
from dmd.train.run import main as train_main

T, P = 16, 88


def _synthetic_npz(path, n=32):
    rng = np.random.default_rng(0)
    D = (rng.random((n, T, P)) < 0.05).astype(np.uint8)
    C = np.zeros((n, T, P, 2), dtype=np.float32)
    C[..., 0] = rng.uniform(0.2, 0.9, (n, T, P))
    C[..., 1] = rng.uniform(-0.4, 0.4, (n, T, P))
    Delta = rng.uniform(0.08, 0.2, (n, T))
    np.savez(path, D=D, C=C, Delta=Delta.astype(np.float64),
             piece=np.zeros(n), start=np.zeros(n))


def _cfg(tmp):
    cfg = {
        "data": {"T": T, "P": P, "K": 2},
        "diffusion": {"T_d": 100, "schedule_alignment": "sqrt_alpha"},
        "model": {"d_model": 32, "trunk_layers": 2, "n_heads": 4,
                  "block": "cfc", "coupling": "gumbel",
                  "param_match": {"reference": "none"},
                  "tau": {"start": 2.0, "end": 0.5}},
        "loss": {"discrete": "focal", "focal": {"rho": 2.0},
                 "supervise_silent": False, "gamma": "auto_grad_match"},
        "train": {"batch_size": 8, "lr": 1e-3, "warmup_steps": 5,
                  "max_steps": 12, "ema": 0.99},
    }
    p = os.path.join(tmp, "cfg.yaml")
    with open(p, "w") as fh:
        yaml.safe_dump(cfg, fh)
    return p


def test_train_and_sample_smoke():
    with tempfile.TemporaryDirectory() as tmp:
        npz = os.path.join(tmp, "data.npz")
        _synthetic_npz(npz)
        out = os.path.join(tmp, "run")
        log = train_main(["--config", _cfg(tmp), "--data", npz, "--out", out,
                          "--seed", "0", "--device", "cpu", "--log_every", "4"])

        hist = log["history"]
        assert len(hist) >= 3
        assert all(np.isfinite(h["loss"]) for h in hist)
        assert hist[-1]["loss"] < 3.0 * hist[0]["loss"] + 1.0, "loss exploded"
        assert 1e-3 <= log["gamma"] <= 1e3
        assert os.path.exists(os.path.join(out, "ckpt.pt"))
        assert os.path.exists(os.path.join(out, "train_log.json"))

        # checkpoint-driven reconstruction (the only supported load path)
        from dmd.train.run import load_checkpoint
        model, tables, stats, _cfg = load_checkpoint(
            os.path.join(out, "ckpt.pt"))
        res = generate(model, tables, stats, B=2, T=T, P=P, steps=8,
                       target_rate=0.05, seed=0)

        assert res.D.shape == (2, T, P) and res.D.max() <= 1 and res.D.min() >= 0
        assert torch.isfinite(res.C_pitch).all() and torch.isfinite(res.C_step).all()
        assert (res.delta >= 0.02).all() and (res.delta <= 2.0).all()
        rate = res.D.float().mean().item()
        assert 0.0 < rate < 0.5, f"activation rate {rate} out of sane range"


if __name__ == "__main__":
    test_train_and_sample_smoke()
    print("PASS  test_train_and_sample_smoke")
