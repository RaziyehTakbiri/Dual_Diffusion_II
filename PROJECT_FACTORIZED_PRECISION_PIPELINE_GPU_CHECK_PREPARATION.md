# Integrated precision pipeline: bounded GPU-check preparation

Date: 2026-09-13

**COMPLETE — separate notebook, fixed integrated-device harness, local CPU
rehearsal and operator handoff. CUDA execution is PENDING and was not launched.**
This prepares the next selected-device check after the earlier BASE-only T4
pass and the completed local precision-policy integration. It does not promote
the candidate to production or replace the historical installed release.

## Delivered artifacts

- [New inspection-first notebook](databricks/notebooks/factorized_precision_pipeline_gpu_check.py)
- [Exact Databricks operator instructions](databricks/FACTORIZED_PRECISION_PIPELINE_GPU_CHECK.md)
- [Integrated-device check](src/heterodiff/experiments/factorized_precision_pipeline_device_check.py)
- [Harness tests](tests/unit/test_factorized_precision_pipeline_device_check.py)
- [Notebook/process-control tests](tests/unit/test_factorized_precision_pipeline_gpu_notebook.py)
- [Complete local CPU notebook result](research/fixtures/factorized_precision_pipeline_cpu_check_2026_09_13.json)

The new check is separate from both preceding GPU notebooks. It imports the
pulled source tree in an isolated child and verifies project import origins
before and after execution. Inspection uses only package metadata and source
folder discovery, without Torch import, a model process or CUDA discovery.
The parent validates result completeness and rejects malformed or contradictory
PASS output. These checks are not authentication of an untrusted source tree.

## Fixed scientific and numerical scope

Four cases cover both domains and both conditional methods. Each has three
fresh routes: CPU candidate, selected-device candidate, and selected-device
replay. A route performs one actual candidate BASE update, generates two BASE
source paths for one actual conditional update, and samples retained and
overflow conditional paths. A separate identical-input conditional update is
a diagnostic control, not a replacement for the generated-population learner.

The whole check contains **12 BASE + 12 generated-input conditional + 12
common-input conditional optimizer updates, and 48 tiny generated paths**.
CUDA mode accounts for 12 CPU and 24 GPU updates. CPU mode accounts for all
36 on CPU. Each model update uses the unchanged AdamW factory.

The acceptance gates are:

1. BASE CPU/device agreement on exact recorded corruption/proposal inputs.
2. Conditional CPU/device agreement on explicit common inputs and identical
   initial FP32 conditional weights.
3. Physical value/gradient and fixed-noise Heun agreement using a common
   CPU-trained post-BASE/post-conditional weight snapshot copied exactly to
   every device.
4. Exact fresh same-device replay of the real generated pipeline, including
   complete path/diagnostic hashes, losses, gradients, weights and AdamW state.

Generated CPU/GPU population identities depend on device and learned weights.
They can therefore select different random streams. Their path realizations
and generated-input conditional updates are **not** claimed to be common-noise
cross-device parity comparisons. Completeness, finiteness, ownership and
same-device replay are tested on those actual routes; the separate common-input
controls address cross-device numerical agreement.

The legacy fixed-weight physical drift remains visible and non-gating. It is
not a re-test or relabelling of the earlier failed legacy FP32 update parity.
The mathematical objective, scientific observation rule, precision defaults,
optimizer settings and tolerance values remain unchanged. The candidate is
explicitly `BASE_GRAPH_FP64_SHARED_V1`; trainable parameters, leaf gradients,
AdamW moments and conditional neural arithmetic remain FP32. The physical
CPU64 → FP32 encoding → FP64 BASE graph → FP32 return cast → CPU64 boundary is
preserved. Host metadata/RNG, analytic guide, reductions and path orchestration
remain part of execution; no all-GPU claim is made.

Paths have four-event capacity and a five-point base grid, with source-path
refinement at the requested training time, 20,000 jump-candidate and 256
initialization-trial guards. They are complete tiny numerical paths, not an
assertion of exact continuous-time simulation or production-scale sampling.

## Resource and operator controls

There is no automatic retry, warmup, iteration search, tolerance override or
production training action. The notebook supervises one child with a
**300-second deadline plus at most 5 seconds to confirm termination**. Capture
is limited during reading to 64 KiB stdout and 16 KiB stderr. The harness's
2 GiB RSS/CUDA-reserved observation limit is soft, not a hard memory quota.
Timing includes imports in the parent deadline and host work, transfers,
readback, first use and synchronization; it is not a throughput benchmark.

The acknowledgement is `RUN BOUNDED PRECISION PIPELINE CHECK`. The notebook
never changes CUDA visibility or parent/cluster settings. Missing cuBLAS
configuration is supplied only to a CUDA child's environment before import;
conflicting inherited settings stop before launch. No package install,
restart, Docker, cloud-job creation or research-data access is performed.

Inspection should use already-running test compute; a GPU is not needed for
inspection. Creating/starting paid GPU compute is not authorized by preparation.

## Actual local execution and evidence

The isolated notebook rehearsal returned
`PASS_CPU_PRECISION_PIPELINE_CONTROLS_CUDA_NOT_EXECUTED` with:

- Four complete cases and all required comparisons passed.
- 36/36 optimizer updates, 48 paths, exact full-route replay in every case.
- Zero explicit CUDA synchronization calls; no CUDA run.
- Harness time 26.081245833076537 seconds.
- Process-lifetime peak RSS 439,484,416 bytes.
- 51,601 captured stdout bytes, zero stderr bytes, child return code zero
  and confirmed termination.

This used local Python 3.11.5, NumPy 2.4.6 and Torch 2.12.1 CPU. It does not
establish compatibility or performance on the reported Databricks Python
3.12.3 / Torch 2.7.0+cu126 / T4 runtime. Only a separately authorized CUDA run
can supply that evidence.

Complete archived wrapper-result SHA-256:
`592b77b27629810e19a4317f2da072f7032c6a00438817790012c2bf6a4ba656`.

Prepared notebook SHA-256:
`29b9f9fa64dd4b3012ed185d786a3ec71e7d1229ef90dbc327300e4e63822db3`.

Prepared harness SHA-256:
`2cfe58a4d450b4f4740463e48702d38d37b5eee71371b81198229651fb25ff11`.

These identify local evidence/files, not authenticated remote execution.

The combined regression passed **1,042 tests in 123.49 seconds**: 765 prior
tests plus **277 new tests** (94 harness + 183 notebook). Static and whitespace
checks also passed.
They cover actual CPU execution, fixed workload and tolerance contracts,
missing/nonfinite/contradictory comparison evidence, replay/input/weight
bindings, FP32 optimizer state and legitimate unused gradients, partial-failure
accounting, no explicit CPU-mode CUDA operations, source import checks, strict
JSON, bounded output/deadlines and confirmed child termination. Independent
reviews found no remaining blocking issue.

All 323 historical CPU manifest payloads remain exact. The historical source
manifest, dependency lock and both preceding GPU notebooks/harnesses are
byte-identical to their prior committed versions. No installed release,
legacy model default or scientific acceptance threshold was changed.

## Plan delta and next action

**Completed:** preparation of this separate bounded integrated-pipeline GPU
check, local CPU rehearsal, tests and exact handoff.
**Pending:** one separately authorized execution on the selected test GPU,
followed by review of its complete output.

Compound totals remain **61 checked / 102 open / 163 total**. Fields remain
31 open / 141 closed; blockers 8 open / 4 closed; formal Tests 28/29/30 remain
OPEN/OPEN/PENDING; scientific results remain 0/4. A preparation milestone is not
whole-method or production qualification.

After sync, the user can open the new notebook and run `INSPECT_ONLY` on
already-running compute. The CUDA widget values and fixed scope are in the
operator guide, for a later separately authorized run. Full training,
long-trajectory/checkpoint qualification, installed-release checks, F105
integration, real-data admission and production budgets remain open.
