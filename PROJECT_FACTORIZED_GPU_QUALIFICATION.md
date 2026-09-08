# Factorized device qualification — bounded synthetic V1

Date: 2026-09-08

The local CPU reference path is qualified for the fixed cases below. The CUDA
path is prepared but **CUDA has not been executed or qualified**. This does not
adopt production numerical tolerances, training budgets, hardware selection,
scientific settings, or a checkpoint-selection result. Historical CPU/frozen
artifacts are not changed by this work.

## Entry point and bounded execution

`heterodiff.experiments.factorized_device_qualification.run_qualification`
accepts only these controls:

```python
run_qualification(
    mode="CPU_REFERENCE",       # or deliberate "CUDA"
    device="cpu",               # CUDA requires explicit "cuda:N"
    iterations=1,               # integer 1..3; all four cases each time
    maximum_seconds=120,        # integer 5..300, soft inner bound
)
```

The Databricks notebook is
`databricks/notebooks/factorized_gpu_parity_and_performance.py`.
Its default `INSPECT_ONLY` mode does not import this Torch-dependent harness.
The notebook supervises an isolated child with a hard process deadline; inner
wall-time and memory checks alone cannot cancel a blocked kernel or enforce a
hard allocation quota. The fixed memory threshold is 2 GiB, measured as process
lifetime peak RSS and, for CUDA only, selected-device reserved memory. Process
RSS is not exclusive task memory; allocator reservation is not hardware VRAM
ownership or a spend cap. Any incomplete roster, unsupported operation,
nonfinite result or failed comparison returns STOP/FAIL, never partial PASS.

Each run fixes three rows, state cap four, per-event metadata limit 2,048 bytes,
batch metadata limit 32,768 bytes, zero optional warmups, and one mandatory
fresh-weight replay per case. Extra iterations repeat the same initialized
fixture; they are not a production training schedule. The fixture is invented,
with no read of actual study/TRAIN/validation/test data.

## Complete four-case comparison

Both Physio and Retail are tested with association-aware guide-plus-residual
and unified direct conditioning. Mixed 0D/1D states include duplicate exact-key
occurrences. Observation rows cover retained, retained-empty and overflow.
Reverse times cover the active interval, the clean-hold boundary, and terminal
time. All paths start from identical weights and immutable visible inputs.

Each case compares:

- Exact parameter names, initial values, shapes, dtypes and missing-gradient/
  optimizer-state presence; no shared independent learned-parameter storage.
- BASE forward outputs, coordinate gradients and Hessians, and parameter
  gradients; actual relative-score/jump-flux BASE objective and its backward
  graph, with separate continuous and jump losses.
- Trainable observation encoder, independent nuisance, logits, paired logistic
  loss, coordinate gradients/Hessians of the guide-plus-residual graph, and
  conditional parameter gradients.
- One ordinary, nonfused AdamW update for BASE and one for the conditional
  model, including every updated parameter and `step`, `exp_avg`, `exp_avg_sq`.
  BASE and all three conditional components must actually change.
- Frozen physical values/coordinate gradients and one coupled Heun step with
  identical explicit Brownian increments; initializer residual is compared.
- Exact same-device replay of all recorded tensors from freshly initialized
  models. All four domain/method cases are mandatory; numeric failures do not
  remove the remaining cases from the requested roster.

The 297,923 unique learned parameters comprise 96,705 BASE, 96,705 conditioner,
51,200 observation encoder, and 53,313 independent nuisance. Physical snapshots
and replay copies add memory, not new independently trained scientific
parameters. Runtime counts are checked against this prototype count.

This physical seam is **not** a complete conditional path, a rejection-sampler
performance measurement, a production F105 factory run, or the full 128-group ×
64-draw checkpoint validation. Exact metadata generation, path RNG/control,
analytic association matching and F105 remain CPU work in the hybrid port.

## Prospective fixed parity policy

Policy ID: `factorized-device-parity-fixed-tolerances-v1`.
These tolerances were fixed before CUDA measurements and cannot be changed by
notebook widgets. They are engineering parity thresholds for these synthetic
graphs, not a scientific error guarantee. Every scalar must satisfy
`abs(target-reference) <= atol + rtol*abs(reference)`; no aggregate mean can hide
an outlier. Nonfinite tensors fail. Exact structure and same-device replay use
zero tolerance. Failure requires investigation/versioned review, not automatic
tolerance widening.

| Category | Absolute tolerance | Relative tolerance |
| --- | ---: | ---: |
| Forward and loss | 0.000002 | 0.00002 |
| Coordinate and parameter gradient | 0.00002 | 0.0002 |
| Coordinate Hessian | 0.0001 | 0.001 |
| Updated parameter | 0.000002 | 0.00002 |
| Optimizer moment | 0.000002 | 0.0002 |
| Physical value/gradient/Heun coordinate | 0.00002 | 0.0002 |

The CPU run observed zero absolute difference in all recorded numerical
categories, across all four cases and mandatory replays. Local focused tests
also exercise refusals, partial-run labels, fixed tolerances, ordinary AdamW
placement and serialized result safety. CPU results explicitly report
`PASS_CPU_REFERENCE_CUDA_NOT_EXECUTED`. They do not establish parity on the
Databricks Python/Torch build or a selected CUDA device until run there.

## Determinism, timing and honest scope

The harness temporarily uses one intra-op thread and deterministic algorithms
with errors rather than warnings, restoring prior settings afterward. It does
not override private optimizer safety checks. Ordinary Torch AdamW may internally
probe accelerator availability even when every parameter and moment is CPU.
CPU_REFERENCE requests no CUDA tensor allocation, discovery or synchronization
itself; INSPECT_ONLY is the stronger no-Torch/no-query boundary.

CUDA additionally requires an explicit visible ordinal, a CUDA-enabled Torch
build, and an already-set `CUBLAS_WORKSPACE_CONFIG` of `:4096:8` or `:16:8` before
launch. The harness never repairs that environment. It requires the new
`fp32_precision` API, temporarily sets global/CUDA-matmul/cuDNN precision to IEEE,
disables cuDNN benchmarking, and restores settings afterward. It never mixes the
new family with legacy `allow_tf32` flags, and does not enable autocast or mixed
precision. The executed Torch/build version and active controls are reported.
The current primary documentation explains the precision-family separation and
the need for synchronization around asynchronous CUDA timing:
[PyTorch CUDA semantics](https://docs.pytorch.org/docs/2.14/notes/cuda.html).

Reported phase timings are synchronized wall time, including relevant host
work and waits. Model transfer/copy and final host readback have separate
measurements. Analytic autograd transfers within graph execution are not
separated from graph time. Internal scalar synchronization counts and pure
kernel active time are explicitly unmeasured; harness-explicit synchronizations
are counted. First-use/import/allocator effects can bias comparisons and there
is no warmup-based throughput claim or speedup calculation. A device property
query is labeled context access; completed neural execution is labeled only
after an actual case completes.

Remaining operator action is a deliberate run on the chosen already-available
CUDA-enabled environment, subject to its external hard deadline and resource
authority. Passing this finite suite would establish only selected-build,
selected-device synthetic parity, not eight-GPU scaling, complete workload
cost, real-data admission, scientific convergence or production readiness.
