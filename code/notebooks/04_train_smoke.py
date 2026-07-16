# Databricks notebook source
# MAGIC %md
# MAGIC # M5/M6 — First real training smoke run + Δ-feedback sampling
# MAGIC
# MAGIC 1. **Gate:** full test suite (now includes the end-to-end train+sample smoke).
# MAGIC 2. **Smoke train** a reduced CFC model (d=128, 4 layers, 200 steps) on the
# MAGIC    real ASAP-gridded corpus you built (`maestro_asap_all.npz`).
# MAGIC 3. **Sample** with Δ-feedback and print first-look statistics.
# MAGIC
# MAGIC This validates the whole pipeline on real data; it is NOT an experiment —
# MAGIC no numbers from here go in the paper. GPU: ~3 min; CPU: ~20 min.

# COMMAND ----------

# MAGIC %pip install --quiet pytest pretty_midi pyyaml

# COMMAND ----------

CODE_DIR = "/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II/code"
DATA_NPZ = "/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II/code/results/maestro_asap_all.npz"
OUT_DIR = "/tmp/dmd_smoke_run"   # /tmp on purpose: /Workspace can't take checkpoints

import sys
sys.path.insert(0, CODE_DIR)
for _m in [m for m in list(sys.modules) if m == "dmd" or m.startswith("dmd.")]:
    del sys.modules[_m]
import torch
print("torch", torch.__version__, "| cuda:", torch.cuda.is_available())

# COMMAND ----------

# MAGIC %md ## 1. Gate

# COMMAND ----------

import os, pytest
os.environ.pop("PYTEST_ADDOPTS", None)
sys.dont_write_bytecode = True
rc = pytest.main([f"{CODE_DIR}/tests", "-q", "--no-header",
                  "-p", "no:cacheprovider"])
assert rc == 0, "TEST FAILURES - stop and report the log above to Claude verbatim"

# COMMAND ----------

# MAGIC %md ## 2. Smoke train on real data (reduced model, 200 steps)

# COMMAND ----------

import yaml

with open(f"{CODE_DIR}/configs/music_cfc.yaml") as fh:
    cfg = yaml.safe_load(fh)
cfg["model"].update({"d_model": 128, "trunk_layers": 4, "n_heads": 4})
cfg["train"].update({"batch_size": 16, "max_steps": 200, "warmup_steps": 20})
smoke_cfg = "/tmp/smoke_cfg.yaml"
with open(smoke_cfg, "w") as fh:
    yaml.safe_dump(cfg, fh)

from dmd.train.run import main as train_main
log = train_main(["--config", smoke_cfg, "--data", DATA_NPZ,
                  "--out", OUT_DIR, "--seed", "0", "--log_every", "25"])

first, last = log["history"][0], log["history"][-1]
print(f"\nloss {first['loss']:.3f} -> {last['loss']:.3f} "
      f"(l_d {first['l_d']:.3f}->{last['l_d']:.3f}, "
      f"l_c {first['l_c']:.3f}->{last['l_c']:.3f}), gamma={log['gamma']:.3f}")
assert last["loss"] < first["loss"], "no learning signal in 200 steps - report"

# COMMAND ----------

# MAGIC %md ## 3. Sample with Δ-feedback — first look

# COMMAND ----------

from dmd.data.loader import CorpusStats, destandardize_pitch
from dmd.diffusion.schedules import ScheduleTables
from dmd.models.denoiser import DualManifoldDenoiser
from dmd.sample.sampler import generate

ck = torch.load(f"{OUT_DIR}/ckpt.pt", weights_only=False)
model = DualManifoldDenoiser(P=88, K=2, d_model=128, n_layers=4, n_heads=4,
                             block="cfc", max_T=cfg["data"]["T"])
model.load_state_dict(ck["ema"]); model.eval()
stats = CorpusStats(**ck["corpus_stats"])
tables = ScheduleTables(cfg["diffusion"]["T_d"],
                        cfg["diffusion"]["schedule_alignment"])

res = generate(model, tables, stats, B=4, T=cfg["data"]["T"], P=88,
               steps=cfg["sampling"]["ddim_steps"],
               calibrate=cfg["sampling"]["unmask_calibration"],
               target_rate=0.03, seed=0)

import numpy as np
C = destandardize_pitch(res.C_pitch)
act = res.D.float().mean().item()
print(f"activation rate      : {act:.4f}  (train corpus ~0.02-0.04)")
print(f"delta (s)            : median {res.delta.median():.3f}, "
      f"IQR [{res.delta.quantile(0.25):.3f}, {res.delta.quantile(0.75):.3f}]")
on = res.D.bool()
print(f"velocity on active   : mean {C[...,0][on].mean():.3f} (human ~0.5)")
print(f"residual on active   : sd {C[...,1][on].std():.3f} (in r_norm units)")
logd = res.delta.clamp_min(1e-4).log()
r1 = np.corrcoef(logd[:, :-1].reshape(-1), logd[:, 1:].reshape(-1))[0, 1]
print(f"gen tempo-curve rho1 : {r1:.3f}  (human target 0.64; smoke model - "
      f"expect junk; this line matters in the real runs)")
print("\nSmoke run complete. If all cells are green, M5/M6 wiring is validated")
print("on real data and the experiment grid (5 seeds x 6 blocks) can start.")
