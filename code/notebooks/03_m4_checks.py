# Databricks notebook source
# MAGIC %md
# MAGIC # M4 — Denoiser checks + Δ-feedback de-risk probe
# MAGIC
# MAGIC Two jobs:
# MAGIC 1. **Gate:** run the full test suite (M1–M4), including the coupling-gradient
# MAGIC    proof and whole-model parameter matching.
# MAGIC 2. **Probe ([R15] de-risk):** can each temporal block *learn* an
# MAGIC    autocorrelated log-tempo sequence (AR(1), φ=0.8 — the human tempo-curve
# MAGIC    regime) in a tiny denoising task? And does giving the CFC an oracle Δ
# MAGIC    help vs. a uniform Δ? This bounds the value of Δ-feedback before we pay
# MAGIC    for full training.
# MAGIC
# MAGIC ML runtime (torch preinstalled), CPU is fine, ~5 minutes total.

# COMMAND ----------

# MAGIC %pip install --quiet pytest pretty_midi

# COMMAND ----------

CODE_DIR = "/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II/code"

import sys
sys.path.insert(0, CODE_DIR)
# Purge any dmd modules cached by a previous run in this same kernel session -
# otherwise edited source files on disk are silently ignored (stale imports).
for _m in [m for m in list(sys.modules) if m == "dmd" or m.startswith("dmd.")]:
    del sys.modules[_m]
import torch
print("torch", torch.__version__)

# COMMAND ----------

# MAGIC %md ## 1. Full test suite (gate)

# COMMAND ----------

import os, sys, pytest
# Databricks kernels export PYTEST_ADDOPTS with flags stock pytest doesn't
# recognize (--cache-dir=...); drop it or pytest aborts before running tests.
os.environ.pop("PYTEST_ADDOPTS", None)
# The /Workspace mount cannot mkdir __pycache__ (Errno 95) and pytest's
# assertion rewriter hard-fails on that; keep rewritten bytecode in memory.
sys.dont_write_bytecode = True
rc = pytest.main([f"{CODE_DIR}/tests", "-q", "--no-header",
                  "-p", "no:cacheprovider"])
assert rc == 0, "TEST FAILURES - stop and report the log above to Claude verbatim"

# COMMAND ----------

# MAGIC %md ## 2. Block-expressivity probe on synthetic tempo curves
# MAGIC
# MAGIC Task: ε-prediction on VP-noised AR(1) sequences (T=128, 1 channel).
# MAGIC Reported: validation MSE after 400 steps (lower = block captures structure;
# MAGIC 1.0 = predicting pure noise ε with no signal use is impossible — the floor
# MAGIC depends on t; we compare blocks at IDENTICAL data, seeds, and step counts).

# COMMAND ----------

import importlib, numpy as np
import dmd.blocks.temporal
importlib.reload(dmd.blocks.temporal)
from dmd.blocks.temporal import build_temporal_block
from dmd.diffusion.schedules import ScheduleTables

def make_ar1(n, T, phi=0.8, seed=0):
    rng = np.random.default_rng(seed)
    e = rng.normal(0, np.sqrt(1 - phi**2), (n, T))
    x = np.zeros((n, T)); x[:, 0] = rng.normal(0, 1, n)
    for i in range(1, T):
        x[:, i] = phi * x[:, i - 1] + e[:, i]
    return torch.tensor(x, dtype=torch.float32).unsqueeze(-1)

class Probe(torch.nn.Module):
    def __init__(self, block, d=64):
        super().__init__()
        self.inp = torch.nn.Linear(2, d)   # [noisy value, t/T_d]
        # match_rtol=0.05: at d=64 the recurrent rungs' width granularity
        # cannot hit 1% (documented in dmd/blocks); actual counts are printed
        # in the results table, so near-matching stays transparent.
        self.block = build_temporal_block(block, d, hidden=None,
                                          target_params=34_000,
                                          match_rtol=0.05)
        self.out = torch.nn.Linear(d, 1)
    def forward(self, x_t, tfrac, dt):
        h = self.inp(torch.cat([x_t, tfrac.expand_as(x_t)], -1))
        return self.out(self.block(h, dt))

def run_probe(block, dt_mode, steps=400, T=128, seed=0):
    torch.manual_seed(seed)
    tab = ScheduleTables(1000)
    Xtr, Xva = make_ar1(512, T, seed=1), make_ar1(128, T, seed=2)
    model = Probe(block)
    n_params = sum(p.numel() for p in model.block.parameters())
    opt = torch.optim.Adam(model.parameters(), lr=2e-3)
    def batch(X, gseed):
        g = torch.Generator().manual_seed(gseed)
        idx = torch.randint(0, len(X), (64,), generator=g)
        x0 = X[idx]
        t = torch.randint(1, 1001, (64,), generator=g)
        ab = tab.alpha_bar.float()[t].view(-1, 1, 1)
        eps = torch.randn(x0.shape, generator=g)
        x_t = ab.sqrt() * x0 + (1 - ab).sqrt() * eps
        dt = (torch.exp(0.2 * x0[..., 0]) if dt_mode == "oracle"
              else torch.ones(x0.shape[:2]))
        return x_t, t.float().view(-1, 1, 1) / 1000.0, dt, eps
    for s in range(steps):
        x_t, tf, dt, eps = batch(Xtr, s)
        loss = ((model(x_t, tf, dt) - eps) ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad():
        x_t, tf, dt, eps = batch(Xva, 10_000)
        return float(((model(x_t, tf, dt) - eps) ** 2).mean()), n_params

print(f"{'block':<14}{'dt':<9}{'val eps-MSE':>12}{'block params':>14}")
results = {}
for block, dt_mode in [("ffn", "uniform"), ("gated_ffn", "uniform"),
                       ("gru", "uniform"), ("cfc", "uniform"),
                       ("cfc", "oracle"), ("node", "uniform")]:
    mse, n_params = run_probe(block, dt_mode)
    results[(block, dt_mode)] = mse
    print(f"{block:<14}{dt_mode:<9}{mse:>12.4f}{n_params:>14,}")

# COMMAND ----------

# MAGIC %md ## 3. Read-out

# COMMAND ----------

r = results
print("Interpretation guide:")
print(f"  recurrence value : ffn {r[('ffn','uniform')]:.4f} vs gru {r[('gru','uniform')]:.4f}")
print(f"  closed-form CT   : gru {r[('gru','uniform')]:.4f} vs cfc {r[('cfc','uniform')]:.4f}")
print(f"  Delta-feedback   : cfc uniform {r[('cfc','uniform')]:.4f} vs oracle {r[('cfc','oracle')]:.4f}")
print(f"  solver CT        : node {r[('node','uniform')]:.4f} vs cfc {r[('cfc','uniform')]:.4f}")
print()
print("If cfc-oracle ~= cfc-uniform, Delta-feedback [R15] is low-value on this")
print("proxy and stays as a mechanism ablation; if clearly better, it is core.")
print("Send this cell's output + the table above back to the tracker.")
