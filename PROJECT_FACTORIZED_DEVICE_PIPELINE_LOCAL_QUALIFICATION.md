# Factorized device implementation and bounded qualification preparation

Date: 2026-09-08

Status: **LOCAL IMPLEMENTATION AND CPU QUALIFICATION COMPLETE; CUDA NOT RUN.**
This fulfills the requested preparation of the GPU-capable amended model and
bounded parity/performance checks. It does not launch paid work, admit data,
freeze scientific settings, or declare the GPU/production route qualified.

## Delivered implementation

The [device graph](src/heterodiff/models/factorized_device_energy_torch.py)
copies the existing CPU BASE, observation encoder, conditioner and independent
nuisance into explicitly selected CPU or CUDA FP32 modules. It preserves exact
metadata bytes, duplicates, parameter names, initial weights and individual
module modes. It does not mutate the CPU prototype or global random stream.
See the [graph contract](PROJECT_FACTORIZED_DEVICE_GRAPH.md).

The [device learner and sampler connector](src/heterodiff/experiments/factorized_device_training.py)
provides:

- Actual BASE target sampling, reference corruption, relative-score/Hessian
  and positive-sign jump-flux objective, and AdamW updates.
- Observation-conditioned G+R/DIR logits, balanced paired loss and updates of
  the conditioner, visible encoder and separate nuisance.
- Frozen learned-BASE populations with two independently keyed whole paths;
  full reverse-time conditional training with query-refined numerical grids.
- Conditional initialization and birth/death-OU path sampling through the
  unchanged numerical sampler and reference/observation rules.
- Explicit device/precision/optimizer ownership checks and schedule horizon/
  clean-hold checks before conditional training or sampling.

The scientific formula is unchanged: the guide enters G+R, the observation
likelihood enters DIR, the residual is gated exactly once, and nuisance enters
the classifier but not physical dynamics or initialization. Initial tilting
excludes BASE V. BASE coordinate derivatives are evaluated in neural FP32,
with loss accumulation transferred differentiably to CPU64. Physical gradients
propagate through CPU64-to-device-FP32-to-CPU64 transfers; transfers do not detach
the learned graph.

This is deliberately a **hybrid implementation**. Neural tensors, derivatives,
parameters and AdamW moments use the chosen device. Exact keys, reference/path
random draws, matching/guide computation, sampler control and raw held-out F105
remain CPU. The per-byte recurrence, host sorting and scalar synchronizations
may limit GPU throughput. GPU capability is not a speedup claim.

The numerical population identity distinguishes device/build and weights; no
claim is made that independently generated CPU/GPU paths are bitwise identical.
The original CPU model, laws and accepted release files are preserved.

## Qualification and bounds

The [fixed qualification harness](src/heterodiff/experiments/factorized_device_qualification.py)
covers both domains × both primary methods, with common starting weights and
inputs. It checks values, coordinate gradients/Hessians, parameter gradients,
BASE and conditional losses, actual updated parameters and AdamW moments,
physical gradients and one fixed-increment Heun step. Every case also requires
exact same-device reconstruction/replay. Category-specific tolerances are fixed
prospectively under `factorized-device-parity-fixed-tolerances-v1`; a failure
does not widen them or remove a case.

The fixed fixture uses 3 batch rows, a 4-event state cap, bounded exact metadata,
no warmup and one mandatory replay per case. An invocation permits 1–3 complete
four-case iterations. The notebook supervises one isolated child for 5–300
seconds (default 120), including imports, and kills it on timeout; termination
confirmation allows up to 5 further seconds. The 2-GiB process/CUDA memory
limits are **observational soft checks**, not hard allocation quotas. A timeout,
unsupported operation, exceeded limit or partial roster is not a pass.

Timings include host control, analytic matching and differentiable transfers.
CUDA timings explicitly synchronize the selected device. Initial model transfer
and output readback have separate timings, but not every internal transfer is
separately instrumented; pure kernel time is not measured. Peak memory and
first-use overhead are disclosed. These tiny tests cannot forecast full-size
training or checkpoint-validation cost.

The complete conditional trajectory is exercised in the new local CPU trainer
tests. The bounded CPU/CUDA comparison deliberately stops at the fixed Heun
seam: it does **not** establish full GPU trajectory/distribution parity, F105
checkpoint performance, installed-wheel compatibility, serialization/resumption
or complete scientific convergence. Those remain separate obligations.

## Ready-to-sync notebook

[factorized_gpu_parity_and_performance](databricks/notebooks/factorized_gpu_parity_and_performance.py)
contains visible parameters and complete [use instructions](databricks/FACTORIZED_GPU_PARITY_AND_PERFORMANCE.md).
Its default `INSPECT_ONLY` imports no Torch and makes no GPU query. Deliberate
CPU/CUDA numerical modes require an explicit device, time/iteration limits and
acknowledgement. CPU_REFERENCE requests CPU tensor computation only; ordinary
PyTorch optimizer internals may probe accelerator availability. No private
optimizer safety method is bypassed to manufacture a zero-query claim.

No package install/restart, network access, parent/cluster environment repair, Docker/ECR,
old custody candidate, dataset or remote job is part of this notebook. It uses
the current interpreter and the explicitly selected new source tree, not the
historical 323-file installed release. The child deadline does not stop the
Databricks cluster or cap its idle billing. Actual CUDA execution therefore
still needs an appropriate already-approved runtime and spending authority.

## Local verification and preserved state

The initial combined regression passed **442 tests in 26.88 seconds** across
13 suites: **103 new tests** (27 graph, 18 training/sampling connector,
28 qualification harness, 30 notebook/supervisor) and **339 existing factorized
scientific regressions**. The 30 notebook tests include an actual isolated-child
CPU run of all four domain-by-method cases; its decision was
`PASS_CPU_REFERENCE_CUDA_NOT_EXECUTED`. All comparison categories had zero
observed CPU differences and all four exact same-device replays passed.
Mocked prelaunch failures in separate tests are not GPU executions.

The local runtime is Python 3.11.5 with CPU PyTorch 2.12.1; it is not the
Databricks Python 3.12 or a CUDA environment. Synthetic parameter updates are
test executions, not scientific training or results.

Independent code review checked graph copying, derivatives, schedule binding,
loss/initializer/nuisance boundaries and harness failure handling. Review found
and corrected missing device-entrypoint horizon/hold checks and parent/mixed
module-mode preservation. No CUDA result was used to tune tolerances.

All 323 accepted CPU source payloads, the accepted source manifest and CPU lock
remain unchanged. No old CPU module is replaced by this successor. No scientific
field, blocker, formal test or compound timetable task closes: **61 checked /
102 open / 163**, **31 fields open / 141 closed**, **8 blockers open / 4 closed**,
Formal Tests **OPEN / OPEN / PENDING**, scientific results **0/4**.

## Next gate

### 2026-09-08 inspection-driven compatibility follow-up

The operator's `INSPECT_ONLY_COMPLETE` report identifies Python 3.12.3,
PyTorch 2.7.0 and an absent cuBLAS setting. It does not query a GPU or
establish a CUDA-enabled build. The wrapper now supplies `:4096:8` only to
the isolated CUDA child before Torch imports when the setting is absent;
valid inherited values are preserved and conflicting values are refused.
Parent/cluster environment, package versions and GPU visibility are unchanged.
An unset `CUDA_VISIBLE_DEVICES` is not an empty/disabled mask.

The harness selects documented legacy FP32 controls for stable Torch 2.7/2.8
and the newer API family for stable 2.9+ within major version 2, without mixing
families or changing fixtures, tolerances or bounds. Forced/ambiguous TF32
environment overrides are refused. This is an API-compatibility repair, not
a claim that the actual Torch 2.7 CUDA runtime has passed.

The updated 13-suite local regression passed **480 tests in 23.85 seconds**:
27 graph, 18 connector, 50 harness, 46 notebook/supervisor and 339 existing
scientific regressions. Legacy/modern backend and child-import-order checks
use test doubles; the real supervised four-case CPU check still passes on
local CPU Torch 2.12.1. No CUDA test or paid/remote job ran during this repair.
The older 323-file CPU release, lock, field states and timetable counts remain
unchanged. See the updated [run instructions](databricks/FACTORIZED_GPU_PARITY_AND_PERFORMANCE.md).

### Pending hardware result

The local device-port/preparation task is done. The user has authorized one
bounded selected-device synthetic check; actual Databricks execution and its
result remain pending. That check must be followed by
review of the actual result—not a full campaign or an eight-GPU launch. Full
trajectory/checkpoint/installed-release qualification, scalable matching/count
workloads, prospective numerical sensitivity design and proofs, real-data
admission, and complete spend/storage/work budgets remain open in parallel.
