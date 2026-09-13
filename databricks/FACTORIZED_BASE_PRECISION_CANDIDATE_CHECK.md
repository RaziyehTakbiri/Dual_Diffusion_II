# Bounded BASE precision-candidate check

Prepared and CPU-tested: 2026-09-13. **GPU execution remains pending.**

This is a separate notebook for `BASE_GRAPH_FP64_SHARED_V1`. Do not rerun the
old `factorized_gpu_parity_and_performance` notebook to test this candidate:
that notebook still exercises the legacy FP32 route.

## What to do now: sync and inspect

1. Push the project changes, including the new source module, notebook, tests
   and this guide. Pull them into the existing Databricks project folder.
   No package reinstall, Docker image, storage folder or cluster edit is part
   of this preparation.
2. In Databricks **Workspace**, open your pulled project:
   `/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II`.
3. Inside it, open **databricks → notebooks → factorized_base_precision_candidate_check**.
4. Choose **Run all** with `mode=INSPECT_ONLY`. The four input fields are created
   by the notebook and appear below its toolbar. Leave acknowledgement empty.
5. Expect `INSPECT_ONLY_COMPLETE`. If it reports `SOURCE_FOLDER_REQUIRED`, put
   the complete project path from step 2 into **repo_root**, then Run all again.
   This is a source-code path, not a `/Volumes` output path.

Inspection only reads source-path and package metadata. It does not import
Torch, query a GPU, launch a child, install anything or change environment
settings. It does not prove GPU availability. Attaching to or starting paid
compute is a separate operator action; the notebook does not create compute.

## One CUDA check, only after explicit run authorization

Use the existing intended GPU **test** compute, not an eight-GPU production
training allocation. The notebook executes on one visible device. In the four
fields below the notebook toolbar, enter:

| Field | Exact value |
| --- | --- |
| mode | `CUDA` |
| device | `cuda:0` |
| repo_root | The project path above, or blank if already detected |
| acknowledgement | `RUN BOUNDED BASE PRECISION CHECK` |

Then choose **Run all once**. There are no iteration, tolerance or duration
widgets to change. Do not modify the notebook source to enter these values.
The acknowledgement is specific to this workload; the old notebook's phrase
does not activate it. This guide/preparation does not itself authorize paid
execution or an automatic retry. A later deliberate CPU control uses
`mode=CPU_REFERENCE`, `device=cpu`, and the same workload acknowledgement.

An absent `CUBLAS_WORKSPACE_CONFIG` is set to `:4096:8` in the isolated CUDA
child only, before Torch imports. Valid inherited values are retained and
conflicting values stop before launch. `CUDA_VISIBLE_DEVICES` is never changed;
unset is permitted, but an explicitly empty or `-1` mask stops the CUDA route.
No cluster restart or environment repair is requested by this notebook.

## Fixed workload and acceptance

- Four domain/method routing cases represent **two unique BASE fixtures**.
  No method-specific conditional learner, sampler, trajectory or F105 scoring
  is exercised here.
- Each case starts six fresh BASE runs: original CPU FP32, candidate CPU FP64,
  target FP32 and its exact replay, target candidate FP64 and its exact replay.
  Initial FP32 weights must match exactly across all six routes.
- Exactly **24 BASE AdamW steps**: CUDA mode has **16 GPU / 8 CPU** steps;
  CPU_REFERENCE has 24 CPU / zero explicit GPU steps. There is one iteration,
  no warmup, no automatic retry and no real-data access.
- Candidate CPU/target forward values, coordinate gradients/Hessians, forward
  and objective parameter gradients, all three losses, updated parameters and
  AdamW moments use the original acceptance tolerances. Replay and step tensors
  must be exact. The candidate's actual forward/coordinate graph is FP64;
  trainable parameters, leaf gradients and AdamW moments remain FP32.
- Legacy CPU/target numeric differences and candidate-versus-legacy CPU drift
  are separately visible and non-gating. Missing/nonfinite controls or failed
  exact legacy replay stop completion. A candidate PASS never relabels the old
  FP32 parity failure or claims equivalence of the two update policies.
- A **120-second child deadline includes imports**, plus at most five seconds
  to confirm termination after a stop. The 2 GiB process-RSS/CUDA-reserved
  checks are soft observations, not a hard allocation quota. Timeout does not
  stop the cluster or guarantee recovery from a malfunctioning driver.
- Timing includes host metadata, CPU FP64 objective reduction, scalar control,
  copying/readback, synchronization and first-use costs. It is not kernel-only
  throughput, an all-GPU pipeline or a speedup claim.

## Reading the result

`PASS_SELECTED_CUDA_BASE_PRECISION_CANDIDATE_ONLY` means all four cases passed
the paired candidate comparison and integrity controls on that selected device.
It does not qualify full conditional paths, installed releases or production
training. `FAIL_BASE_PRECISION_CANDIDATE` retains the failed categories; a STOP
means incomplete execution or controls and is never accepted as a pass.

The complete compact JSON includes the decision, case/category summaries, legacy
controls, timings, step counts, device/build facts and termination status.
Copy the full output as an attachment. No large coordinate arrays are printed.
Both output streams are bounded during capture (64 KiB stdout / 16 KiB stderr).
If it reports `STOP_CHILD_QUIESCENCE_UNCONFIRMED`, stop and inspect the attached
compute before another run. Do not infer that the child stopped from a timeout
message alone.

## Local preparation evidence

**670 tests passed in 53.75 seconds** across 18 local suites, including 47 new
harness and 40 new notebook regressions. The actual isolated notebook CPU run
completed all four cases and 24 steps in about 2.80 seconds of harness time;
the complete wrapper output was about 22 KiB. This is not a GPU timing estimate.
Local Python 3.11.5 / Torch 2.12.1 CPU differs from the reported Databricks
Python 3.12.3 / Torch 2.7.0+cu126 environment. CUDA compatibility controls were
tested with fake backends only; the new candidate has not run on GPU.

The [complete CPU result](../research/fixtures/factorized_base_precision_candidate_cpu_check_2026_09_13.json)
has SHA-256 `4e8658ac91ca4f8f1e1ef1382c7e38b01a92ebe6588c82ac04f9437ab8a13c05`.
The harness SHA-256 is `c2c1dd4900d654881e4cad3fb78e2b637e378cabc3ac94b9a9f1d636377aac2e`;
the notebook SHA-256 is `28fa2957694f1cd7c81fbe8d16ecf3c22bd677e64d457a973ce94bbf5b7876ed`.
These identify the locally checked files, not authenticated remote execution.

Independent implementation review found no blocking issue. Its final count and
hybrid host-work reporting suggestions were incorporated. The historic CPU
release, old parity harness and old notebook remain unchanged.
