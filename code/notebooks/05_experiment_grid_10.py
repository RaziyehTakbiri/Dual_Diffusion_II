# Databricks notebook source
# MAGIC %md
# MAGIC # Experiment grid — one training run + sampling sweep per invocation
# MAGIC
# MAGIC **The 30-run matrix:** 6 blocks × 5 seeds (`run_index` 0–29; block order:
# MAGIC ffn=0–4, ffn_timecond=5–9, gated_ffn=10–14, gru=15–19, cfc=20–24, node=25–29).
# MAGIC
# MAGIC **How to parallelize:** create a Databricks Job from this notebook with a
# MAGIC `RUN_INDEX` parameter and launch it 30 times (or as a multi-task job), one
# MAGIC per GPU node. Suggested first wave: indices **0, 5, 10, 15, 20, 25** (one
# MAGIC seed of every block) to validate end-to-end, then the remaining 24.
# MAGIC
# MAGIC **What each invocation does:** mini-gate → (once) piece-level split +
# MAGIC human reference + jitter baselines → train (pilot: ~12 h) → sampling sweep
# MAGIC (Δ-mode: feedback / uniform / oracle) → metrics JSON.
# MAGIC
# MAGIC Prerequisite: notebook 04 green on this cluster type (full gate).

# COMMAND ----------

# MAGIC %pip install --quiet pytest pyyaml

# COMMAND ----------

CODE_DIR = "/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II/code"
DATA_ALL = "/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II/code/results/maestro_asap_all.npz"
WORK = "/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II/code/dmd"       # checkpoints/results (NOT /Workspace)
SCALE = "final"                          # 'final' only after scan optimization

import os, sys, json, time
sys.path.insert(0, CODE_DIR)
for _m in [m for m in list(sys.modules) if m == "dmd" or m.startswith("dmd.")]:
    del sys.modules[_m]
import numpy as np
import torch

try:
    dbutils.widgets.text("RUN_INDEX", "10")
    RUN_INDEX = int(dbutils.widgets.get("RUN_INDEX"))
except NameError:
    RUN_INDEX = int(os.environ.get("RUN_INDEX", "0"))
print(f"RUN_INDEX={RUN_INDEX}  scale={SCALE}  cuda={torch.cuda.is_available()}")
os.makedirs(f"{WORK}/prep", exist_ok=True)
os.makedirs(f"{WORK}/results", exist_ok=True)

# COMMAND ----------

# MAGIC %md ## 1. Mini-gate (fast; full gate lives in notebook 04)

# COMMAND ----------

import importlib.util, traceback
spec_ = importlib.util.spec_from_file_location(
    "test_grid_eval", f"{CODE_DIR}/tests/test_grid_eval.py")
tmod = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(tmod)
bad = []
for name in sorted(vars(tmod)):
    if name.startswith("test_"):
        try:
            getattr(tmod, name)()
        except Exception:
            bad.append(name); traceback.print_exc()
assert not bad, f"mini-gate failed: {bad} - STOP, report to Claude"
print("mini-gate green")

# COMMAND ----------

# MAGIC %md ## 2. One-time prep: split, human reference, jitter baselines

# COMMAND ----------

from dmd.exp.grid import write_split_npz
from dmd.eval.generated import batch_metrics, human_reference, jitter_excerpts

TRAIN_NPZ = f"{WORK}/prep/corpus_train.npz"
EVAL_NPZ = f"{WORK}/prep/corpus_eval.npz"
REF_JSON = f"{WORK}/prep/human_ref.json"
REF_VEL = f"{WORK}/prep/human_ref_velocity.npy"
BASE_JSON = f"{WORK}/prep/jitter_baselines.json"

if not os.path.exists(REF_JSON):
    paths = write_split_npz(DATA_ALL, f"{WORK}/prep/corpus", eval_frac=0.1)
    ev = np.load(EVAL_NPZ)
    idx = np.arange(len(ev["D"]))
    ref = human_reference(EVAL_NPZ, idx)
    np.save(REF_VEL, ref["velocity"])
    ref_json = {k: v for k, v in ref.items() if k != "velocity"}
    with open(REF_JSON, "w") as fh:
        json.dump(ref_json, fh, indent=2)
    base = {}
    for mode in ("iid", "ar1"):
        D, C, delta = jitter_excerpts(
            EVAL_NPZ, idx, mode, sigma=ref_json["residual_sigma"],
            rho1=ref_json["residual_rho1"] if mode == "ar1" else 0.0)
        ref_full = dict(ref_json); ref_full["velocity"] = np.load(REF_VEL)
        base[f"jitter_{mode}"] = batch_metrics(D, C, delta, ref_full)
    with open(BASE_JSON, "w") as fh:
        json.dump(base, fh, indent=2)

with open(REF_JSON) as fh:
    REF = json.load(fh)
REF["velocity"] = np.load(REF_VEL)
with open(BASE_JSON) as fh:
    print("jitter baselines:", json.dumps(json.load(fh), indent=1)[:600])
print("human ref:", {k: round(v, 4) for k, v in REF.items()
                     if not isinstance(v, np.ndarray)})

# COMMAND ----------

# MAGIC %md ## 3. Train this run

# COMMAND ----------

from dmd.exp.grid import prepare_run
from dmd.train.run import main as train_main

cfg_path, spec = prepare_run(f"{CODE_DIR}/configs/music_cfc.yaml",
                             RUN_INDEX, SCALE, f"{WORK}/configs")
run_dir = f"{WORK}/runs/run{RUN_INDEX:02d}_{spec['block']}_s{spec['seed']}"
t0 = time.time()
train_log = train_main(["--config", cfg_path, "--data", TRAIN_NPZ,
                        "--out", run_dir, "--seed", str(spec["seed"])])
train_sec = time.time() - t0
print(f"trained {spec} in {train_sec/3600:.2f} h")

# COMMAND ----------

# MAGIC %md ## 4. Sampling sweep (Δ-modes) + metrics

# COMMAND ----------

from dmd.data.loader import destandardize_pitch
from dmd.sample.sampler import generate
from dmd.train.run import load_checkpoint

model, tables, stats, run_cfg = load_checkpoint(
    f"{run_dir}/ckpt.pt", device="cuda" if torch.cuda.is_available() else "cpu")
T, P = run_cfg["data"]["T"], run_cfg["data"]["P"]
ev = np.load(EVAL_NPZ)
N_GEN, CHUNK = 64, 8

results = {"spec": spec, "scale": SCALE, "train_hours": train_sec / 3600,
           "final_loss": train_log["history"][-1]["loss"],
           "gamma": train_log["gamma"], "sampling": {}}
for mode in ("feedback", "uniform", "oracle"):
    t1 = time.time()
    Ds, Cs_, dl = [], [], []
    for c in range(N_GEN // CHUNK):
        kw = dict(delta_feedback=(mode == "feedback"))
        if mode == "oracle":
            rows = np.arange(c * CHUNK, (c + 1) * CHUNK) % len(ev["Delta"])
            kw["delta_init"] = torch.tensor(ev["Delta"][rows], dtype=torch.float32)
        res = generate(model, tables, stats, B=CHUNK, T=T, P=P,
                       steps=run_cfg["sampling"]["ddim_steps"],
                       calibrate=run_cfg["sampling"]["unmask_calibration"],
                       target_rate=0.03, seed=1000 * spec["seed"] + c,
                       device=str(next(model.parameters()).device), **kw)
        Ds.append(res.D.cpu().numpy())
        Cs_.append(destandardize_pitch(res.C_pitch).cpu().numpy())
        dl.append(res.delta.cpu().numpy())
    m = batch_metrics(np.concatenate(Ds), np.concatenate(Cs_),
                      np.concatenate(dl), REF)
    m["sampling_sec"] = round(time.time() - t1, 1)
    results["sampling"][mode] = m
    print(f"[{mode:8s}] " + " ".join(
        f"{k}={v:.4f}" for k, v in m.items()
        if isinstance(v, float) and k in
        ("velocity_w1", "residual_sigma", "residual_rho1", "tempo_rho1",
         "asynchrony_sigma_ms", "activation_rate")))

out_json = f"{WORK}/results/run{RUN_INDEX:02d}_{spec['block']}_s{spec['seed']}.json"
with open(out_json, "w") as fh:
    json.dump(results, fh, indent=2)
print(f"\nresults -> {out_json}")
print("Download all of {WORK}/results/*.json into the project's results/grid/")
print("folder once several runs finish; Claude aggregates them into Table 1.")
