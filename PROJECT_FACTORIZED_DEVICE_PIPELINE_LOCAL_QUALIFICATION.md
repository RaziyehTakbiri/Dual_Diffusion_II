# Factorized device implementation and bounded qualification preparation

Date: 2026-09-08; latest operator-result review: 2026-09-13

Status: **LOCAL IMPLEMENTATION AND CPU QUALIFICATION COMPLETE; LATEST OPERATOR
CUDA RUN COMPLETED 4/4 CASES WITH EXACT REPLAYS BUT FAILED CPU/GPU UPDATE PARITY.**
This fulfills the requested preparation of the GPU-capable amended model and
bounded parity/performance checks. It does not launch paid work, admit data,
freeze scientific settings, or declare the GPU/production route qualified.

The requested September 13 follow-up is also **COMPLETE locally**: focused
BASE update diagnostics, CPU replays of captured gradients, local regression
and the then-required same-notebook instructions for one bounded GPU check. That
diagnostic collection/review is now complete; the precision candidate has been
validated only locally. See
the [completed three-task milestone](#2026-09-13-focused-update-diagnostics-and-local-qualification).

The subsequent [separate BASE precision-candidate check preparation](databricks/FACTORIZED_BASE_PRECISION_CANDIDATE_CHECK.md)
is also COMPLETE: 670 local tests passed, including actual supervised CPU
execution of all four routing cases and 24 BASE steps. The candidate GPU run
remains pending. This narrower check does not replace the legacy whole-component
parity report or qualify conditional paths, F105 or production training.

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

### 2026-09-08 bounded CUDA attempt and startup repair

The user supplied the result of the authorized one-iteration, 120-second
`cuda:0` check. This is an operator-reported result, not a run independently
performed by the local agent. The child completed normally, but its nested
decision was `STOP_DEVICE_QUALIFICATION_INCOMPLETE`: **0/4 cases completed**,
`RuntimeError`, elapsed inner-harness time 0.19489117099999476 seconds.
Torch reports `2.7.0+cu126` / CUDA build `12.6`; the child-only cuBLAS value
was correctly `:4096:8`. No active numerical-policy or selected-device record
was produced, and no explicit CUDA synchronization completed. This is not a
successful parity test, not proof of zero driver/device interaction, and not
evidence that the model or the cluster is defective. GPU model/VRAM remain
unobserved. Child return code 0 means report delivery, not qualification PASS.

Code review found a concrete cold-start ordering defect consistent with the
early failure: the harness reset allocator peaks before Torch initialized its
CUDA allocator. PyTorch 2.7's availability/count calls do not establish that
initialization; `get_device_properties` does, while `reset_peak_memory_stats`
calls the allocator directly. The allocator rejects an uninitialized device.
The original exception text was suppressed, so the exact historical cause is
not uniquely established. [PyTorch 2.7 device initialization](https://github.com/pytorch/pytorch/blob/v2.7.0/torch/cuda/__init__.py#L523-L537),
[memory reset](https://github.com/pytorch/pytorch/blob/v2.7.0/torch/cuda/memory.py#L327-L342),
[allocator check](https://github.com/pytorch/pytorch/blob/v2.7.0/c10/cuda/CUDACachingAllocator.cpp#L3405-L3425).

The local fix now initializes through the selected-device properties query
before resetting peaks and reuses those properties for reporting. No warm-up,
additional model step, fallback or tolerance change is introduced. Revision
`factorized-device-qualification-v2-initialization-order` reports startup stage,
bounded error text with path/URI/common-credential redaction, and bounded frame
locations without locals/source lines. Deferred CUDA initialization exceptions
receive the same STOP report; KeyboardInterrupt/SystemExit still propagate.
The notebook default, child-only cuBLAS handling and execution bounds are unchanged.

The updated 13-suite local regression passed **494 tests in 26.64 seconds**:
27 graph, 18 connector, 64 harness, 46 notebook/supervisor and 339 existing
scientific regressions. New stateful fake-CUDA tests enforce cold initialization
before reset/cases, failure-stage preservation, flag restoration, diagnostics
bounds/redaction and interrupt propagation. These tests and the genuine CPU
four-case harness do not establish actual CUDA success. No further GPU attempt,
package/cluster change, data access or paid/remote job was performed by the agent.
The 323 accepted CPU source payloads and lock remain unchanged; no completion
counts, field states, scientific tolerances or workload limits changed.

### 2026-09-13 received GPU result: execution complete, parity failed

The subsequent user-run, one-iteration/120-second check completed all four
mandatory cases on **Tesla T4, Torch 2.7.0+cu126, CUDA build 12.6**, with the
correct initialization-order harness revision. The nested decision is
`FAIL_DEVICE_PARITY`, not PASS. The archived [operator report](research/fixtures/factorized_cuda_parity_operator_report_received_2026_09_13.json)
is user-supplied evidence, not independently observed remote execution. The
date here is receipt/review date; the report provides no independently attested
execution timestamp. Archiving adds only a final LF to the supplied JSON;
no reported value changes.

| Check | Reported result |
| --- | --- |
| Roster and CUDA startup | 4/4 cases complete; allocator initialization/reset complete |
| Same-GPU replay | All four exact; every recorded tensor has zero difference |
| CPU/GPU forward, loss, coordinate gradient/Hessian, parameter gradient, moments, exact fields and physical seam | All pass the unchanged category tolerances |
| Updated parameters | FAIL only for BASE tensors: five tensor names in each PhysioNet case, two in each Retail case |
| Maximum updated-parameter absolute difference | PhysioNet 8.682161569595337e-5; Retail 1.0221358388662338e-4 |
| Inner elapsed time | 51.46031292600003 seconds; no supervisor timeout |
| Peak CUDA allocation / reservation | 87,648,256 / 90,177,536 bytes |
| Peak process RSS | 1,205,760,000 bytes; below the 2-GiB observational limit |

Every failed tensor name begins with `base/updated_parameters/`; no conditional
updated tensor fails. PhysioNet fails event_hidden.weight, event_output.weight,
context_output.weight, readout_hidden.weight and readout_middle.weight. Retail
fails context_output.weight and readout_hidden.weight. Failure rosters and BASE
maximum absolute gaps agree across the two methods within each domain. The
report gives failing tensor names, not the failing scalar coordinates.

The startup blocker is resolved for this reported runtime. The residual failure
is numerical CPU/GPU update parity, not missing CUDA configuration or a crash.
Exact GPU replay does not imply CPU/GPU equivalence. Large maximum relative
gradient differences use a denominator floored at 1e-30; they must be interpreted
with the actual absolute-plus-relative acceptance rule, not as standalone
failures. The corresponding failing-coordinate gradients are not in this report.

**Working hypothesis, not established cause:** near-zero BASE gradient
roundoff is amplified by the first AdamW step. With fresh moments, lr=0.001,
eps=1e-8 and zero weight decay, the ideal step is
`-0.001*g/(abs(g)+1e-8)`. A local CPU-only scalar illustration on Torch 2.12.1
used gradients 0 and 1e-9 at the same initial weight 0.05 with unchanged
ordinary AdamW settings. It produced a 9.090825915336609e-5 weight gap, while
moment differences were about 1e-10 and 1e-21. This demonstrates sensitivity
at the observed scale; it does not reproduce the actual GPU tensors or prove
the cause. [PyTorch 2.7 AdamW definition](https://docs.pytorch.org/docs/2.7/generated/torch.optim.AdamW.html).

**Follow-up identified by this result review (implemented below):** capture deterministic failing scalar
coordinates, initial weights, CPU/GPU objective gradients, moments and updates;
compare ideal first-step predictions and replay CPU AdamW with the already
captured GPU gradients (CPU-gradient replay as a control). This can distinguish
gradient sensitivity from optimizer/state arithmetic without additional GPU
optimizer steps, though collecting the extra values would require a newly
authorized bounded GPU invocation. The current report does not support that
coordinate-level reconstruction. At this result-review checkpoint no diagnostic
code, optimizer/epsilon change, tolerance widening, clipping, fixture change
or GPU retry had been made. The subsequent local implementation below changes
only diagnostic/reporting code; the historical CPU release remains unchanged.

The tiny hybrid timing is not a full-training speedup estimate: no warm-up,
first-use overhead, CPU path control and host/device transfers remain material.
It does not qualify full conditional trajectories, production checkpoint/F105
performance, scientific training, all cluster GPUs or an installed GPU release.
No field, blocker or compound timetable checkbox closes. Counts remain 61/102/163
checked/open/total; 31 fields open/141 closed; scientific results 0/4.

### 2026-09-13 focused update diagnostics and local qualification

The user-approved three-task **preparation milestone is COMPLETE**:

| Requested task | Status and evidence |
| --- | --- |
| Extend the existing notebook/harness with BASE gradient/state/update diagnostics | COMPLETE: explicit `diagnostics=BASE_UPDATE`, bounded coordinate details and first-step predictions |
| Add CPU replay with captured target/GPU gradients plus CPU-gradient control | COMPLETE: two ordinary AdamW steps on fresh CPU clones per case, with all BASE parameters/moments/steps compared |
| Test locally and prepare one further bounded GPU check | COMPLETE: 552 local tests passed at that preparation checkpoint; the subsequent remote diagnostic execution/review is complete as recorded below |

Implementation: [diagnostic helper](src/heterodiff/experiments/factorized_update_diagnostics.py),
[harness](src/heterodiff/experiments/factorized_device_qualification.py),
[existing notebook](databricks/notebooks/factorized_gpu_parity_and_performance.py),
and [focused tests](tests/unit/test_factorized_update_diagnostics.py).
The new revisions are `factorized-device-qualification-v3-base-update-diagnostics`
and `factorized-gpu-wrapper-v3-base-update-diagnostics`. Default diagnostics are
`NONE`; inspection still imports no Torch and starts no child. No new notebook,
dependency installation, cluster change, GPU run or scientific-data access was
performed by this local preparation.

`BASE_UPDATE` is explicitly limited to one iteration through the original four
cases. It runs after the original comparison and exact replay, using captured
`base/objective_parameter_gradients`, not forward-only gradients. Both CPU
replays start from the same exact initial weights with fresh moments and the
unchanged lr/betas/epsilon/decay/nonfused AdamW settings. No measured model,
captured tensor or global RNG is mutated. Two extra CPU optimizer steps per
case (eight total), zero extra GPU optimizer steps and zero extra model
forward/backward passes are requested. Ordinary AdamW may internally probe
accelerator availability; no claim of zero library-internal probes is made.

All BASE updates and optimizer states are compared, with exact equality,
existing-tolerance comparisons and stricter descriptive FP32 residual summaries
kept distinct. Up to eight failing scalar coordinates are reported per case:
one largest threshold-excess coordinate per failing tensor in lexical name
order, ties resolved by lowest flat index. Unreported failing scalars/tensors
are counted. Rows contain initial values, CPU/target objective gradients,
actual first-step state, updated weights/deltas, ideal FP64 first-step
predictions and both genuine CPU replay values/residuals.

Finite first-step moment anomalies are retained as diagnostic evidence with
`CAPTURED_FIRST_STEP_MOMENT_RESIDUAL_REQUIRES_REVIEW`, not hidden behind a
heuristic pre-gate. Malformed, nonfinite, different-initial-weight or non-first-
step inputs still stop the diagnostic because they do not support this replay.
Moment-anomaly names are sampled at four per side with explicit truncation;
all moments are still compared. The per-case compact diagnostic limit is
16,384 bytes; the existing child-output limit remains 262,144 bytes. Time and
memory checks include diagnostic CPU work. The 120-second requested deadline
and 2-GiB soft memory limit are unchanged.

The final 14-suite regression passed **552 tests in 42.20 seconds** on local
Python 3.11.5 / Torch 2.12.1 CPU: 27 device graph, 18 device connector, 69
harness, 51 notebook/supervisor, 48 diagnostic-helper and 339 existing
scientific tests. This includes the actual four-case CPU harness in both modes,
supervised notebook execution, RNG/policy restoration, no explicit CUDA work,
unchanged primary failure decisions, near-zero sensitivity, same-gradient
update residuals, moment anomalies/subnormal cases, malformed-input rejection,
sampling/output limits and timeout behavior. Static checks and whitespace
checks passed. Independent read-only review has no unresolved findings.

A separately executed notebook-to-harness `CPU_REFERENCE/BASE_UPDATE` run
returned `PASS_CPU_REFERENCE_CUDA_NOT_EXECUTED`: 4/4 cases, eight diagnostic
CPU steps, exact CPU-gradient and target-labelled-gradient replay controls,
zero explicit CUDA synchronizations and 36,400 serialized child-result bytes.
Here the target was also CPU, not a GPU. The local run took about 5.51 seconds
including about 0.09 seconds of diagnostic work; these are local synthetic
observations, not a CUDA speedup or production forecast. The illustrative
near-zero-gradient and perturbed-state tests do not establish the actual
Tesla T4 cause.

At the preparation checkpoint, the [GPU run instructions](databricks/FACTORIZED_GPU_PARITY_AND_PERFORMANCE.md#next-diagnostic-check-same-notebook-one-bounded-run)
used the same notebook and test GPU, one `cuda:0` device, one iteration, a
120-second limit, `diagnostics=BASE_UPDATE` and the existing explicit run
acknowledgement. That diagnostic collection is now complete. Do not repeat it
as a precision-candidate check: the old notebook still selects the legacy route.
No blind retry or automatic GPU execution is authorized.
Original parity acceptance is never replaced by a diagnostic interpretation.

The 323 accepted CPU source payloads, their manifest and dependency lock were
reverified unchanged. Model, fixtures, tolerances, optimizer settings,
scientific fields, blockers and all compound timetable counts are unchanged:
61/102/163 checked/open/total, 31/141 fields open/closed, 8/4 blockers open/closed,
and scientific results 0/4. **GPU update parity remains FAIL/OPEN.**

### 2026-09-13 focused GPU diagnostic execution and local precision candidate

**COMPLETE:** the operator's four compact diagnostic records are received,
archived and reviewed. The detailed original paste was truncated; the recovery
contains all four summary records, not the missing full coordinate payloads.
All same-device GPU replays and CPU-gradient controls pass exactly. The maximum
GPU-gradient CPU-replay parameter residual is 1.49e-08, within the unchanged
update tolerance. Original CPU/GPU update parity remains FAIL/OPEN.

**COMPLETE locally:** shared-FP64 BASE graph/derivative accumulation candidate,
actual bounded BASE-step connection, mathematical/precision regressions and
CPU-only stress analysis. **583 tests passed.** All four candidate CPU layout
stress cases have exact updated weights; original FP32 controls have 54/62
failing weights per Physio/Retail case. This does not prove CUDA parity, and
the new candidate differs from legacy FP32 updates beyond the original update
tolerance. Default execution and all thresholds are unchanged. See the
[complete precision record and archived evidence](PROJECT_FACTORIZED_BASE_PRECISION_STABILIZATION.md).
No GPU or paid job was launched in this local step. Exact compound-count delta
is zero: boxes61/102/163, fields31/141, blockers8/4, scientific results0/4.

### Pending qualification

The local preparation and reported GPU startup/execution milestone are complete.
Focused diagnostic implementation/local qualification and GPU-run handoff are
also complete, as are the GPU diagnostic review and local precision candidate.
CPU/GPU parameter-update parity is **FAIL/OPEN**. A separately declared bounded
precision-successor comparison must retain the legacy control and original
tolerances; no candidate GPU run, automatic retry or full campaign is authorized. Full
trajectory/checkpoint/installed-release qualification, scalable matching/count
workloads, prospective numerical sensitivity design and proofs, real-data
admission, and complete spend/storage/work budgets remain open in parallel.
