# Integrated precision pipeline: separate bounded GPU check

## Status and scope

Preparation is complete locally; the selected-device CUDA result is still pending.
This is a new source-only notebook, separate from both earlier GPU notebooks.
It does not install packages, replace the installed release, change cluster
settings, access research data or launch a cloud job. Running its CUDA mode
does use the attached GPU compute, which may incur charges.

The candidate remains opt-in: `BASE_GRAPH_FP64_SHARED_V1`. Mathematical
objectives, AdamW settings, FP32 trainable parameters/moments, FP32 conditional
neural arithmetic and all existing acceptance tolerances are unchanged.
Legacy FP32 numerical disagreements have not been reclassified as passes.

## Exactly what to open

1. Push the current project changes to your normal repository, then pull them
   into the Databricks project folder.
2. In **Workspace**, open:
   `/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II`.
3. Open **databricks → notebooks → factorized_precision_pipeline_gpu_check**.
   This is the new notebook; do not select
   `factorized_gpu_parity_and_performance` or
   `factorized_base_precision_candidate_check`.
4. Use already-running test compute for inspection; a GPU is not required.
   Do not create or start GPU compute just for this preparation step.
   Leave the mode at `INSPECT_ONLY` and choose **Run all** once. This first
   run only checks metadata and locates the source folder; it does not import
   Torch or start a model process.
5. The notebook creates four input widgets below its toolbar. If source
   detection needs help, enter the full project-folder path from step 2 in
   `repo_root` and run inspection again.

There is no code cell to edit and no Docker, ECR, dependency-installation or
cluster-environment setup step in this notebook.

## One CUDA run, only after separate authorization

Preparation itself does not authorize this run. After approval for this exact
bounded check, attach the intended **test GPU compute**, not a production
training run, and set the four notebook widgets as follows:

| Widget | Exact value |
| --- | --- |
| `mode` | `CUDA` |
| `device` | `cuda:0` |
| `repo_root` | `/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II` |
| `acknowledgement` | `RUN BOUNDED PRECISION PIPELINE CHECK` |

Then choose **Run all once** and retain the entire JSON output. The device is
one process-visible GPU, not all GPUs on the cluster. Do not automatically
retry a FAIL or STOP result.

If `CUBLAS_WORKSPACE_CONFIG` is absent, the notebook sets `:4096:8` only in
the child environment before Torch import. It preserves a valid inherited
`:4096:8` or `:16:8` setting and rejects a conflicting one. It never changes
the parent/cluster environment or `CUDA_VISIBLE_DEVICES`. An empty or `-1`
CUDA visibility mask, or a conflicting TF32 override, stops before launch.
Do not copy the earlier CPU-only empty CUDA mask onto this test setup.

For a local CPU rehearsal, use `CPU_REFERENCE` and `cpu` with the same
acknowledgement. CPU success is explicitly not a CUDA result.

## Fixed workload and limits

Four cases cover Physio/Retail × primary/direct conditional methods. Each case
runs three freshly initialized routes: candidate CPU, selected device, and a
fresh selected-device replay.

Each route performs:

- One actual candidate BASE optimizer update.
- Two generated BASE source paths and one actual conditional optimizer update
  using those generated inputs.
- One retained-observation and one overflow-observation conditional path.
- One separate conditional optimizer update on explicit, identical diagnostic
  inputs for CPU/device comparison.
- Shared-weight physical value/gradient and fixed-noise Heun controls.

Totals are **36 optimizer updates and 48 tiny generated paths**. CUDA mode uses
12 CPU and 24 GPU updates. Paths use four-event capacity and a five-point base
time grid; source paths also insert the requested off-grid training time.
Initialization/jump-candidate guards are fixed. There is no iteration,
warmup, retry, tolerance or workload-size widget.

The parent supervises one child with a **300-second deadline**, then allows
up to **5 seconds to confirm termination**. Report capture is bounded to
64 KiB stdout and 16 KiB stderr. A **2 GiB memory observation limit is soft**;
it is not a hard operating-system or GPU memory reservation. Time includes
startup, CPU work, transfers, readback and synchronization.

## What PASS means

Expected CUDA decision:
`PASS_SELECTED_CUDA_PRECISION_PIPELINE_CANDIDATE_ONLY`.

A pass requires all four cases and the full workload, unchanged numerical
tolerances, common-input BASE and conditional comparisons, shared-weight
physical comparisons, and exact fresh same-device replay. Replay binds the
generated paths and their complete diagnostics, losses, gradients, updated
weights and AdamW state.

Generated population identities depend on device and weights. Therefore
generated CPU/GPU populations can use different random streams. Their sampled
paths and resulting conditional updates are **not** labelled common-noise
CPU/GPU parity comparisons. The explicit common-input control tests numerical
agreement separately; the real generated pipeline tests execution and exact
same-device replay.

The physical interface retains the documented
CPU64 → FP32 encoding → FP64 BASE graph → FP32 gradient-return → CPU64
boundary. The conditional network stays FP32. This is not an all-FP64 or
all-GPU pipeline.

A pass does not establish long-run stability, convergence, accurate
continuous-time simulation, performance speedup, real-data readiness, F105
scores, multi-GPU training, production qualification or installed-release
qualification. Timing from one tiny, cold run is diagnostic only.

## If it stops

Keep the complete output and do not change tolerances or rerun an old notebook.
The top-level decision distinguishes input requirements, incomplete child
execution, output/deadline limits, malformed output and numerical failure.
A child exit code of zero alone cannot produce PASS. The parent also checks
the result's mode/device, case roster, workload counts and comparison evidence.
If child termination is unconfirmed, stop and inspect the attached compute
before another attempt.

See the [preparation and local evidence](../PROJECT_FACTORIZED_PRECISION_PIPELINE_GPU_CHECK_PREPARATION.md)
and [preceding local integration](../PROJECT_FACTORIZED_PRECISION_PIPELINE_LOCAL_INTEGRATION.md).
