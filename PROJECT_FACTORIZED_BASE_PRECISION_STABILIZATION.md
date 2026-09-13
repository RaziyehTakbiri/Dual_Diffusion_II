# BASE precision analysis and local stabilization candidate

Date: 2026-09-13

## Decision and scope

**COMPLETE: local precision analysis, opt-in implementation, CPU qualification,
the subsequently reported bounded T4 BASE candidate GPU check, and the later
[local conditional-pipeline precision integration](PROJECT_FACTORIZED_PRECISION_PIPELINE_LOCAL_INTEGRATION.md).
NOT COMPLETE: legacy CPU/GPU parity or full-pipeline GPU/production qualification.**

User authority: proceed with local precision analysis and stabilization while
preserving the scientific objective and existing acceptance tolerances. The local
implementation did not launch GPU/paid work or access real data. The later
operator-executed GPU check is recorded in the [separate result review](PROJECT_FACTORIZED_BASE_PRECISION_CUDA_RESULT.md).

The candidate is `BASE_GRAPH_FP64_SHARED_V1`. It is explicit opt-in; the existing
`LEGACY_FP32` default and the existing Databricks qualification notebook/harness
are unchanged. The separate paired candidate check is now prepared and locally
tested as documented below. Its subsequent bounded GPU execution passed all
four cases; rerunning the old notebook would still test the old route.

## Completed GPU diagnostic review

The [four operator-supplied compact records](research/fixtures/factorized_cuda_base_update_compact_operator_report_received_2026_09_13.jsonl)
cover both domains and both methods exactly once. They report:
- all four original parity outcomes false, all same-device replays true;
- exact CPU-gradient optimizer controls;
- GPU-gradient CPU-replay maximum updated-parameter residual
  1.4901161193847656e-08, within the unchanged update tolerance in every case;
- no first-step moment-consistency anomalies.

The archived compact records' SHA-256 is
`f480ed48d615a6a9359eb9082b40298fcb1e07f8417674be1f9732e9a3f3841d`
(8,754 bytes). Archival added exactly one terminal newline; the original
8,753-byte attachment SHA-256 is
`1cfa13b150ea07d7c00b42ab8a0f106ef9226f39beac696d86825680ce187125`.
All preceding bytes and all four parsed records are unchanged.
These are operator-supplied remote observations, not independently repeated GPU
execution or authenticated receipts. The earlier full diagnostic paste was
truncated by Databricks and is not valid complete JSON. Its original attachment
SHA-256 is `b5462fee0ee7013c6049d9ba5cbfd699a77503e0a3eccd4706c0753b5f56492a`.
The compact recovery resolves the missing four-case summary, not the lost full
coordinate-detail payload. The strict descriptive residual label does not mean
the 1.49e-08 residual violates the original update threshold.

Together with the visible coordinate replays reviewed previously, the evidence
strongly supports gradient differences amplified by first-step AdamW as the
dominant original update discrepancy. It does not identify one CUDA kernel as
the exclusive cause.

## Local numerical finding

The loss already accumulated in CPU FP64. Its neural graph and branch parameter
gradients still used FP32, including higher-order differentiation of the
continuous-score term. Source and destination jump contributions can nearly
cancel with each other and with the continuous contribution.

Independent local CPU decomposition at the Physio readout weight [93,167] gave
approximately -1.386e-6 + 6.4724e-4 - 6.4586e-4, leaving -2.969e-9.
Its absolute-branch-sum / absolute-total diagnostic ratio is about 436,060;
this is an illustrative cancellation measure, not a formal condition-number
certificate or a GPU measurement. AdamW's unchanged epsilon is 1e-8.

The reproducible [CPU analysis](src/heterodiff/experiments/factorized_precision_analysis.py)
uses the unchanged four-case synthetic fixture, all 96,705 BASE parameters,
seven fixed variants, and 28 bounded synthetic optimizer steps. No parameter
search, clipping, threshold relaxation or data-dependent tuning is performed.
The [recorded result](research/fixtures/factorized_base_local_precision_analysis_2026_09_13.json)
is `PASS_LOCAL_PRECISION_CONTROLS_ONLY`.
Its SHA-256 is
`5f0ebd0db4a459d20705bc822ff8f7622b9f6ebee34b02f6235dc32d7df39432`.

Each domain's results were the same for G+R and DIR:

| CPU arithmetic comparison | Physio maximum update gap / failing scalars | Retail maximum update gap / failing scalars |
|---|---:|---:|
| FP32 batched vs rowwise | 1.15068e-4 / 54 | 1.61484e-4 / 62 |
| Shared FP64 batched vs rowwise | 0 / 0 | 0 / 0 |
| Shared FP64 vs separate FP64 parameter casts | 1.00210e-5 / 5 | 1.53109e-5 / 6 |
| Legacy FP32 vs shared FP64 candidate | 6.29667e-5 / 47 | 7.97063e-5 / 50 |

Failure counts use the original elementwise update tolerance:
`atol=2e-6, rtol=2e-5`. No tolerance was changed. Candidate replay and layout
stress produced bitwise-identical updated weights on this local CPU, but such
identity is not promised across hardware or software versions.

The local environment is Python 3.11.5 / Torch 2.12.1 CPU, not the reported
Databricks Python 3.12.3 / Torch 2.7.0+cu126 runtime. CPU layout stress is not
CUDA emulation, and local timing is not a GPU performance forecast.

## Mathematical and implementation preservation

The energy architecture, exact discrete metadata, occurrence multiplicities,
canonical ordering, bounded output and smooth coordinate transform are unchanged.
The continuous term remains 0.5 times squared coordinate gradient plus the exact
coordinate Hessian minus coordinate times gradient. Jump flux remains
rate times [exp(destination energy - source energy) + destination energy -
source energy], with the original positive linear sign and original jump weight.

The [precision implementation](src/heterodiff/experiments/factorized_base_precision.py)
promotes each trainable FP32 parameter once per objective and reuses that same
differentiable FP64 view across source, destination and all derivative branches.
It casts only the accumulated gradient back to the original FP32 leaf.
Per-layer or per-evaluation independent parameter casts are deliberately not
the candidate: they can reintroduce FP32 cancellation in the backward pass.

Stored input coordinates, time and context retain the original FP32 encoding,
then are promoted; internal derived features and constants are evaluated in FP64.
Trainable parameter storage and AdamW moments remain FP32. Learning rate,
betas, epsilon, weight decay, nonfused settings and all existing tolerances
remain unchanged. The candidate is connected to the actual reference-corruption
BASE training step through an explicit `precision_policy` argument.

A separate numerical-analysis agent implemented an independent inline FP64
functional reference and reproduced the candidate's loss and sensitive gradients.
This is separate from the code-review agent's use of the candidate itself.
The functional FP32 control reproduces
the original graph's losses, gradients and updated parameters exactly on both
domains, supporting algebraic equivalence rather than a changed scientific loss.

Higher precision is an implementation candidate, not a guarantee:
[PyTorch's numerical-accuracy documentation](https://docs.pytorch.org/docs/2.7/notes/numerical_accuracy.html)
explains that mathematically identical batched/sliced or CPU/GPU calculations
need not be bitwise identical.

## Verification

The combined regression suites cover FP32 control equivalence, shared-cast
accumulation, exact CPU replay, FP64 rowwise/batched stress, higher-order
finite-difference checks with Richardson extrapolation, unchanged FP32 optimizer
state, actual reference-corruption updates, zero-rate/constant-objective controls,
frozen parameters, input/resource rejection and explicit device placement.
Report regressions refuse hidden loss failures, malformed comparisons and a
final evaluation crossing the soft deadline.

Independent review identified and resolved a missing parameter-count guard and
missing loss/deadline checks in the report runner. Final regression: **583 tests
passed in 45.34 seconds** across the 16 factorized scientific/device/notebook
and new precision suites (552 existing plus 31 new tests). Final independent
review reran the precision, report and device-training subset: **49 passed in
9.02 seconds**, with no remaining blocking findings. No CUDA execution is
represented by these counts.

The 323 accepted historical CPU source payloads were reopened and verified
against their unchanged manifest. The dependency lock, legacy parity harness
and existing Databricks notebook remain byte-for-byte unchanged. Static checks
and the repository whitespace check passed.

## Completed next step: separate candidate-check preparation

The [new BASE-only notebook and operator guide](databricks/FACTORIZED_BASE_PRECISION_CANDIDATE_CHECK.md)
are COMPLETE locally. The candidate's real FP64 functional forward, coordinate
gradient/Hessian, FP32 leaf gradients, objective, updated parameters and AdamW
moments are paired against the same candidate on CPU. Exact target replay and
complete finite legacy controls are mandatory; legacy numeric disagreement and
CPU policy drift remain explicitly visible and non-gating.

The fixed workload is 24 BASE steps under four routing labels/two unique fixtures,
with 16 GPU / 8 CPU steps in a later authorized CUDA run. There is no conditional
training/sampling, scientific data or F105 execution in this check. The child
deadline is 120 seconds including imports, plus five seconds to confirm termination;
memory limits are soft. Both output streams are bounded during collection.

Final combined regression: **670 passed in 53.75 seconds** across 18 suites
(583 prior tests plus 47 harness and 40 notebook regressions). The actual isolated
CPU notebook route passed all four cases/24 steps; the complete compact output
is about 22 KiB. Its [archived CPU result](research/fixtures/factorized_base_precision_candidate_cpu_check_2026_09_13.json)
SHA-256 is `4e8658ac91ca4f8f1e1ef1382c7e38b01a92ebe6588c82ac04f9437ab8a13c05`.
Independent review found no blocking issue; its step-split and hybrid host-work
reporting recommendations were incorporated. No CUDA or paid work was launched.

## Subsequent bounded GPU milestone complete

The [operator result review](PROJECT_FACTORIZED_BASE_PRECISION_CUDA_RESULT.md)
records candidate CPU/T4 parity PASS in all four cases with unchanged tolerances,
exact candidate/legacy GPU replays, and 24 completed BASE steps in 22.44 seconds.
Candidate parameter gradients match exactly, with a maximum update residual
of 1.4901161193847656e-08. Legacy FP32 parity and CPU policy drift remain failed.
This is the narrow synthetic BASE candidate success, not broader GPU readiness.

## Remaining work and unchanged project state

The numerical mechanism is localized to cancellation in the BASE gradient graph;
this does not prove a unique offending CUDA operation. The old CPU/GPU result
remains FAIL/OPEN. The candidate also differs from legacy FP32 updates above the
old update threshold; this failure is retained prominently in the local report.

The subsequent [local explicit-policy integration](PROJECT_FACTORIZED_PRECISION_PIPELINE_LOCAL_INTEGRATION.md)
is complete for physical evaluation, learned-BASE populations and conditional
sampling, including the actual coordinate-cast and RNG-identity boundaries.
The [separate integrated GPU-check preparation](PROJECT_FACTORIZED_PRECISION_PIPELINE_GPU_CHECK_PREPARATION.md)
is now complete and CPU-tested; its CUDA execution awaits separate authorization.
The candidate must
then pass broader trajectory/checkpoint/installed-release and resource checks
before production adoption. No GPU speedup is claimed.

Current compound checklist: 61 checked / 102 open / 163 total. Fields:
31 open / 141 closed. Blockers: 8 open / 4 closed. Formal Tests 28/29/30:
OPEN/OPEN/PENDING. Scientific results: 0/4. These completed local milestones do
not close whole-method, scientific or production-qualification obligations.
