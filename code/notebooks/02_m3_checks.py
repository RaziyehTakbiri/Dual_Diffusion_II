# Databricks notebook source
# MAGIC %md
# MAGIC # M3 — Diffusion-core checks (schedules, forward corruption, objective)
# MAGIC
# MAGIC Runs the **entire test suite** (M1 blocks + M2 representation + M3 diffusion)
# MAGIC and prints the schedule tables for the paper's appendix.
# MAGIC
# MAGIC **Cluster requirement:** an ML runtime (PyTorch preinstalled). CPU is fine;
# MAGIC the whole notebook takes ~2 minutes.

# COMMAND ----------

# MAGIC %pip install --quiet pytest pretty_midi

# COMMAND ----------

CODE_DIR = "/Workspace/Repos/<you>/dual-diffusion/code"   # folder containing dmd/

import sys
sys.path.insert(0, CODE_DIR)
import torch
print("torch", torch.__version__)

# COMMAND ----------

# MAGIC %md ## 1. Full test suite (must be green before any training run)

# COMMAND ----------

import pytest
rc = pytest.main([f"{CODE_DIR}/tests", "-q", "--no-header"])
assert rc == 0, "TEST FAILURES - stop and report the log above to Claude verbatim"

# COMMAND ----------

# MAGIC %md ## 2. Schedule tables ([R6]) — sanity view for the appendix

# COMMAND ----------

from dmd.diffusion.schedules import ScheduleTables

T_d = 1000
print(f"{'t':>6} | {'alpha_bar':>10} | " +
      " | ".join(f"m_t ({al})" for al in ("sqrt_alpha", "alpha", "linear")))
tabs = {al: ScheduleTables(T_d, al) for al in ("sqrt_alpha", "alpha", "linear")}
for t in (1, 100, 250, 500, 750, 900, 1000):
    row = f"{t:>6} | {tabs['sqrt_alpha'].alpha_bar[t]:.5f}    | "
    row += " | ".join(f"{tabs[al].m[t]:.4f}    " for al in tabs)
    print(row)

# COMMAND ----------

# MAGIC %md ## 3. One joint forward draw (shape/dtype smoke test at model scale)

# COMMAND ----------

from dmd.diffusion.forward import BifurcatedForward

fwd = BifurcatedForward(tabs["sqrt_alpha"], vocab_size=2)
B, N, K = 8, 256 * 88, 2
g = torch.Generator().manual_seed(0)
D0 = (torch.rand(B, N, generator=g) < 0.03).long()      # ~3% activation, music-like
C0 = torch.randn(B, N, K, generator=g)
jc = fwd(D0, C0, generator=g)
print("t:", jc.t.tolist())
print("D_t masked frac per sample:",
      [round(x, 3) for x in jc.mask_positions.float().mean(1).tolist()])
print("C_t std per sample:", [round(x, 3) for x in jc.C_t.std(dim=(1, 2)).tolist()])
print("expected m_t:", [round(tabs['sqrt_alpha'].m[int(t)].item(), 3) for t in jc.t])
print("\nAll good if masked fractions track expected m_t. Nothing to download;")
print("this notebook is a gate, not a producer.")
