# Integrated precision pipeline: bounded CUDA result accepted

Review date: 2026-09-13.

**COMPLETE — reported selected-device synthetic integrated precision-candidate
pass and exact GPU replay.** The result is
`PASS_SELECTED_CUDA_PRECISION_PIPELINE_CANDIDATE_ONLY`. This closes the bounded
four-case GPU-check milestone, not multi-step/checkpoint qualification or
production training. No rerun is required for this milestone.

## Evidence and its limits

The [normalized selected-field review](research/fixtures/factorized_precision_pipeline_cuda_operator_review_2026_09_13.json)
combines two explicitly identified sources:

1. The user's supplied `pasted-text.txt` attachment, whose visible prefix and
   tail retain the decision, workload, runtime, numerical policy and resource
   observations. The 51,283-byte attachment contains an explicit
   `max output size exceeded, skipping output` marker and does **not** parse as
   complete original JSON. Its SHA-256 is
   `40926fec31a3079f62d8c2cf7398c095fd0e93e80ed30692654922d40834895f`.
2. The user's subsequent recovery summary, reporting all five named comparisons
   as `passed=true, failure_count=0` in each of the four domain/method cases,
   together with `exact_gpu_replay=true`.

The review extract's SHA-256 is
`7326cf85e01c7cdbd7165f7cd9257ba4fb91ed6d737c965bfdfe3068aa5ec771`.
It is deliberately not a reconstruction or byte-exact archive of the full
original result. Missing category values, tensor rosters, detailed hashes and
remote tensor payloads have not been invented or recovered. The reported
52,642 captured stdout bytes describe the operator's child capture; they are
not the size of the truncated attachment received by the reviewer.

Acceptance is a review of the reported bounded result and its consistency with
the predeclared local harness contract. It is not an independent remote rerun,
runtime authentication or recomputation of tensor hashes. The explicit recovery
summary supports the case-level acceptance recorded here; the full detailed
raw report remains unavailable.

## What passed

| Domain | Conditional method | Reported comparisons | Exact GPU replay |
| --- | --- | --- | --- |
| R3-PHYS | association-aware-guide-plus-residual | 5/5 pass; zero failures | true |
| R3-PHYS | unified-direct-conditioner | 5/5 pass; zero failures | true |
| R4-RETAIL | association-aware-guide-plus-residual | 5/5 pass; zero failures | true |
| R4-RETAIL | unified-direct-conditioner | 5/5 pass; zero failures | true |

The five reported comparisons are `common_base_cpu_vs_target`,
`common_conditional_cpu_vs_target`, `shared_weight_physical_cpu_vs_target`,
`candidate_target_exact_replay` and `legacy_shared_weight_physical_drift`.
The last is a **non-gating, fixed shared-weight physical comparison**. Its pass
does not reverse the previously recorded legacy FP32 training/update failures.

The declared integrated check exercises actual BASE updates, learned-BASE
source trajectories, conditional updates, retained/overflow conditional paths,
explicit common-input controls and fresh same-device replay. CPU/GPU generated
paths are not claimed to be common-noise draws: population identities depend on
device and weights. Numerical CPU/GPU parity comes from the separate explicit
common-input and shared-weight comparisons; generated-route reproducibility is
checked by same-device replay.

| Reported quantity | Result |
| --- | --- |
| Device and runtime | Tesla T4, cuda:0; Torch 2.7.0+cu126; Python 3.12.3 |
| Completed cases | 4/4, with three fresh routes per case |
| Optimizer updates | 36: 12 BASE + 12 generated-input conditional + 12 common-input conditional controls |
| CPU/GPU update split | 12 CPU + 24 GPU |
| Tiny generated paths | 48 |
| Harness elapsed time | 199.48732787899985 seconds |
| CUDA peak allocated/reserved memory | 79,369,728 / 79,691,776 bytes |
| Process-lifetime peak RSS | 1,218,785,280 bytes |
| Child completion | Exit 0; termination confirmed; zero captured stderr |
| Limits | 300-second child deadline; 5-second termination grace; 2 GiB soft RSS observation limit |

The precision policy remains `BASE_GRAPH_FP64_SHARED_V1`. Reported tolerances
match the existing `factorized-device-parity-fixed-tolerances-v1` dictionary and
reported digest `c665d0d0d2f8c0ea9eca5407324c31c8bc4932d961901f488809a195af204ffd`.
FP32 trainable parameters and AdamW moments, FP32 conditional neural arithmetic
and the CPU64 → FP32 encoding → FP64 BASE graph → FP32 gradient-return → CPU64
physical interface are retained. This is neither an all-FP64 nor an all-GPU
pipeline. No tolerance, optimizer setting or scientific default changed during
this documentation review.

These are four-event-capacity synthetic paths on the declared small numerical
grid, not a qualification of arbitrary capacities, continuous-time accuracy,
long-run stability, convergence or throughput. Timing includes host work,
transfers, readback, synchronization and first-use overheads. It is not a
speedup claim. GPU memory measurements are not full-training capacity estimates.
The operator used attached compute; this record does not imply that run was free
or that the cluster has been stopped.

## Current next step

Keep this successful bounded result and do not rerun the earlier GPU setup or
parity notebooks merely to repeat it. The user has authorized the next **local**
implementation and synthetic qualification work: multi-step training and
checkpoint save/load/resume, including model and optimizer state and reproducible
continuation. That work is not already proved by this one-step-per-route check,
and this record does not authorize another paid GPU job.

Production/installed-release qualification, real-data admission, full F105
validation, scientific outcomes, multi-GPU training and full-budget execution
remain separate open obligations. The broader compound tracker boxes are not
closed by this bounded pass. No new model execution, source-code edit, test run,
network access or data access was performed to create this documentation record.

See the [original bounded-check guide](databricks/FACTORIZED_PRECISION_PIPELINE_GPU_CHECK.md),
[local integration evidence](PROJECT_FACTORIZED_PRECISION_PIPELINE_LOCAL_INTEGRATION.md)
and [preceding BASE-only GPU result](PROJECT_FACTORIZED_BASE_PRECISION_CUDA_RESULT.md).
