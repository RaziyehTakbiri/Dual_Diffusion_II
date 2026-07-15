# Databricks notebook source
# MAGIC %md
# MAGIC # M2 — Data audit: representation tests, human-ACF study, dataset build
# MAGIC
# MAGIC **How to use this notebook**
# MAGIC 1. Get the repo's `code/` directory into Databricks: either **Repos** (preferred;
# MAGIC    sync the project's git repo) or **Workspace → Import** the folder.
# MAGIC 2. Point `CODE_DIR` below at it, point `MIDI_GLOB` / `MAESTRO_CSV` at your
# MAGIC    MAESTRO copy, then *Run all*.
# MAGIC 3. Start with `SMOKE = True` (20 pieces, ~1 min) to validate paths, then set
# MAGIC    `SMOKE = False` for the full corpus.
# MAGIC 4. Download the three output files listed by the last cell and drop them into
# MAGIC    the shared project folder under `results/`.
# MAGIC
# MAGIC Everything here is CPU-only; any small cluster works.

# COMMAND ----------

# MAGIC %pip install --quiet pretty_midi

# COMMAND ----------



# COMMAND ----------

# ---- configuration (edit these) ---------------------------------------------
CODE_DIR = "/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II/code"   
MIDI_GLOB = "/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Drafts/maestro-v3.0.0/**/*.mid*" 
MAESTRO_CSV = "/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Drafts/maestro-v3.0.0/maestro-v3.0.0.csv"
OUT_DIR = "/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II/code/results"

GRID = "fixed"           # 'fixed' now; rerun with 'asap' + ANNOTATION_MAP later
ANNOTATION_MAP = None    # CSV 'midi_path,annotation_path' once ASAP lands
SMOKE = True             # True: 20 pieces smoke run; False: full corpus

import os, sys, glob as _glob
sys.path.insert(0, CODE_DIR)
os.makedirs(OUT_DIR, exist_ok=True)
n_found = len(_glob.glob(MIDI_GLOB, recursive=True))
print(f"MIDI files found: {n_found}")
assert n_found > 0, "MIDI_GLOB matched nothing - check the path (note /dbfs prefix)"

# COMMAND ----------

# MAGIC %md ## 1. Ground-truth tests (must be 10/10 before trusting any numbers)

# COMMAND ----------

import importlib.util, traceback

spec = importlib.util.spec_from_file_location(
    "test_representation", f"{CODE_DIR}/tests/test_representation.py")
tmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tmod)

fns = [(k, v) for k, v in sorted(vars(tmod).items())
       if k.startswith("test_") and callable(v)]
failed = []
for name, fn in fns:
    try:
        fn(); print(f"PASS  {name}")
    except Exception:
        failed.append(name); print(f"FAIL  {name}"); traceback.print_exc()
print(f"\n{len(fns)-len(failed)}/{len(fns)} passed")
assert not failed, f"representation tests failed: {failed} - STOP, report to Claude"

# COMMAND ----------

# MAGIC %md ## 2. Human expressive-timing study (E4.3; ground-truth numbers for the paper)

# COMMAND ----------

from dmd.eval.human_acf import main as human_acf_main

acf_prefix = f"{OUT_DIR}/human_acf_{GRID}" + ("_smoke" if SMOKE else "")
argv = ["--midi_glob", MIDI_GLOB, "--grid", GRID,
        "--out", acf_prefix]
if SMOKE:
    argv += ["--max_pieces", "20"]
if ANNOTATION_MAP:
    argv += ["--annotation_map", ANNOTATION_MAP]
human_acf_main(argv)

# COMMAND ----------

import json
with open(f"{acf_prefix}.json") as fh:
    agg = json.load(fh)["aggregate"]
print("Headline human numbers (this grid):")
for k in ("sigma_ms", "rho_1", "rho_2", "asynchrony_sigma_ms",
          "keep_rate", "wrap_rate", "collision_rate"):
    print(f"  {k:22s} {agg[k]['mean']:8.4f} (sd across pieces {agg[k]['sd_across_pieces']:.4f})")

# COMMAND ----------

# MAGIC %md ## 3. Build training tensors + round-trip audit (E4.2)
# MAGIC Skipped in smoke mode - run once paths are validated.

# COMMAND ----------

from dmd.data.build_music import main as build_music_main

if not SMOKE:
    build_music_main([
        "--midi_glob", MIDI_GLOB,
        "--maestro_csv", MAESTRO_CSV,
        "--grid", GRID,
        "--T", "256", "--hop", "256",
        "--out", f"{OUT_DIR}/maestro_{GRID}",
    ] + (["--annotation_map", ANNOTATION_MAP] if ANNOTATION_MAP else []))
else:
    print("SMOKE mode - skipping dataset build")

# COMMAND ----------

# MAGIC %md ## 4. What to send back to the project folder

# COMMAND ----------

print("Copy these into the shared project folder under results/ :")
print(f"  1. {acf_prefix}.csv")
print(f"  2. {acf_prefix}.json")
if not SMOKE:
    print(f"  3. {OUT_DIR}/maestro_{GRID}_audit.csv")
print()
print("If OUT_DIR is under /dbfs/FileStore/, each file is downloadable in a browser at:")
print("  https://<databricks-host>/files/<path relative to /dbfs/FileStore/>")
print("The big .npz tensors STAY on Databricks - they are training inputs for M5.")
