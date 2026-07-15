# DMD — Dual-Manifold Diffusion (from-scratch pipeline)

Implements `paper/MODEL_SPEC.md` exactly. When math changes, the spec changes first, then the code.

## Layout

```
code/
  dmd/
    blocks/temporal.py    # B0–B5 ladder: ffn, ffn_timecond, gated_ffn, gru, cfc, node
    utils/params.py       # parameter matching (±1%) across ladder rungs
    data/                 # M2: MAESTRO/ASAP representation, IAM-OnDB, tabular adapters
    diffusion/            # M3: forward processes, schedules, objective
    models/               # M4: trunk (transformer + adaLN), heads, Gumbel bridge
    train/                # M5: Databricks/MLflow training harness
    sample/               # M6: DDIM + calibrated unmasking sampler
    eval/                 # M7: metrics suite (W1, ACF, conditional timing, Hellinger, FMD…)
    baselines/            # M8: jitter, AR (deterministic + distributional), SCHmUBERT-style, VQ-latent
  configs/                # YAML experiment configs (one file = one table row)
  tests/                  # CPU-runnable pytest; no GPU needed
```

## Build order (milestones)

- **M1 (done):** temporal block ladder + param matching + tests
- **M2:** music representation (ASAP grid, residuals, masks) + round-trip validator (E4.1/E4.2) + human-data ACF study (E4.3)
- **M3:** forward processes + objective (masked L_C, focal/elbo switch)
- **M4:** denoiser trunk + coupling
- **M5:** training harness (MLflow, seeds, DDP)
- **M6:** sampler (calibration-parity flag)
- **M7:** eval suite (jitter baselines E1.1 live here too — they're sampler-free)
- **M8:** baselines

## Databricks workflow (notebook-only; no terminal assumed)

1. Get `code/` into Databricks via **Repos** (preferred) or Workspace import.
2. **Every runnable module exposes `main(argv: list[str])`** — the notebook
   convention is `from dmd.x.y import main; main(["--flag", "value", ...])`.
   Never rely on a shell. Per-milestone driver notebooks live in `notebooks/`
   (`01_m2_data_audit.py` = Databricks source format, import directly).
3. Multi-GPU training (M5) will launch DDP from a notebook via
   `pyspark.ml.torch.distributor.TorchDistributor` (Databricks-native), not
   torchrun; single-GPU runs are a plain function call.
4. MLflow: each run logs config, matched param counts, git/spec version,
   metrics; final metrics JSON goes to `/dbfs/FileStore/dmd_results/` (browser-
   downloadable) and is dropped into this project's `results/` for analysis.
5. Before any training run: the test cells at the top of each driver notebook
   must pass (they execute the same suite as `pytest tests/ -q`).

## Conventions

- Every config field is read at most once, at startup; no hidden defaults in code.
- All randomness through a single seeded generator; seeds recorded in output filenames.
- All reported units follow MODEL_SPEC §2 (velocity ∈ [0,1]; timing in ms at metric time).
