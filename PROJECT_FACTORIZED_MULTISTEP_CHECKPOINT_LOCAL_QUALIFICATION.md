# Local multi-step training and checkpoint continuity

Date: 2026-09-13.

**COMPLETE — bounded synthetic CPU multi-step stability and fresh-object
checkpoint continuation.** The final actual run returned
`PASS_LOCAL_CPU_MULTISTEP_CHECKPOINT_RESUME_ONLY` for all four domain/method
cases. This follows the [reported integrated T4 pass](PROJECT_FACTORIZED_PRECISION_PIPELINE_CUDA_RESULT.md);
it does not launch or qualify another GPU run.

## What was implemented and exercised

The additive [qualification harness](src/heterodiff/experiments/factorized_multistep_checkpoint_qualification.py)
runs both R3-PHYS and R4-RETAIL with G+R and DIR. Each case has two fresh routes:

1. Four BASE updates followed by four conditional updates, uninterrupted.
2. The same work, with checkpoints after BASE update 2 and conditional update 2,
   written to local disk and restored into fresh models, optimizers and private
   random generators before continuation.

The existing actual BASE score/jump-flux objective, full-interval conditional
classifier objective, learned-BASE pair generation, numerical hybrid sampler,
retained/overflow observations and clean-hold rule are reused. BASE remains
frozen during conditional training. Final sampling must leave training state
unchanged. No proxy loss, injected-gradient update, early stopping, loss
monotonicity requirement or hyperparameter search was substituted.

The diagnostic schedule was fixed at four-plus-four before execution:
BASE batch size 2; conditional pair count 1; advancing BASE PCG64 seed 7;
conditional seed 501 with step-specific record keys; final-path seed 502;
the existing five-point grid `[0,.25,.5,.75,1]`; AdamW learning rate .001,
betas (.9,.999), epsilon 1e-8 and zero weight decay. These are **synthetic
qualification settings**, not a replacement for the full scientific campaign.

The opt-in `BASE_GRAPH_FP64_SHARED_V1` policy, FP32 trainable parameters,
gradients and AdamW moments, FP32 conditional arithmetic, existing scientific
objective and acceptance tolerances are unchanged. Same-runtime resume is
checked for exact equality, not by relaxing cross-device tolerances.

## Checkpoint contract

The new [CPU-only codec](src/heterodiff/experiments/factorized_training_checkpoint.py)
stores model state, current gradients including `None`, training modes,
trainability, complete AdamW groups/moments/per-parameter update counts, the
explicit PCG64 state (including its cached word), phase/update cursor and
conditional random-stream keys. A parameter may legitimately retain optimizer
moments after a later step with no gradient.

The harness supplies runtime, reference, architecture, context, fixture,
precision, schedule and optimizer bindings. The codec checks live schedule
ownership, clocks, clean hold and horizon, not only state-dictionary tensors.
Malformed/incompatible records are rejected before target mutation. Restoration
uses fresh CPU targets; the frozen learned-BASE population is reconstructed and
its law identity must match exactly.

Only trusted self-produced bytes are supported. The expected SHA-256 is checked
before restricted `weights_only=True` CPU decoding; per-file size is capped at
16 MiB. A digest is not proof of authorship and this is not approval to load
downloaded or arbitrary checkpoints. The codec's smaller optional-metadata
interface alone is not the complete harness semantic contract.

## Observed result

The [complete final local report](research/fixtures/factorized_multistep_checkpoint_cpu_check_2026_09_13.json)
records:

| Quantity | Actual result |
| --- | --- |
| Domain/method cases | 4/4 pass |
| Routes | 8: uninterrupted and resumed per case |
| Optimizer updates | 64: 32 BASE + 32 conditional |
| Tiny generated paths | 80: 64 conditional-source + 16 final |
| Disk checkpoints/restores | 8/8; both phase midpoints in every case |
| Exact comparisons | All seven checks pass in each case |
| Elapsed wall time | 34.91001533297822 seconds |
| Process-lifetime peak RSS | 402,554,880 bytes |
| Largest checkpoint | 4,862,439 bytes |
| Aggregate checkpoint bytes written | 27,486,920 bytes; temporary files cleaned |
| Runtime | Python 3.11.5, NumPy 2.4.6, CPU Torch 2.12.1 |
| Global random state | Unchanged |

Every post-step model/gradient/moment/RNG/cursor fingerprint, update record,
source-path record, population identity and final retained/overflow path agrees
between uninterrupted and resumed execution. All inspected parameters,
gradients and moments are finite FP32. Loss histories are finite and exactly
reproduced; they are not required to decrease and do not establish convergence.

The harness has fixed work limits, a 300-second **soft** elapsed-time check and
a 2 GiB **soft** RSS check. It is not a hard-deadline process supervisor or an
allocator-enforced memory reservation. There are no automatic retries.

Source/result SHA-256 bindings for this run:

- Harness: `befb09560d177bbfd62b47476a6ce82e5045ec7239f3da97566923b2a1a86ce4`.
- Checkpoint codec: `2b88f4f6a7c19c38029293982bf80461f11731213d9572b2db2073315f76f266`.
- Archived final report: `73dacd9c1cab6eb563aa6dcf4016907921e8bd36feb2dd85cb4cfc2c35b85ae9`.

## Regression and preserved state

The two [new test suites](tests/unit/test_factorized_training_checkpoint.py)
and [harness tests](tests/unit/test_factorized_multistep_checkpoint_qualification.py)
have **108 passing tests**. They cover restricted decoding, corruption and
cross-binding rejection before mutation, rollback, PCG64 cached-word continuity,
unused gradients with existing moments, actual four-case execution, truthful
report gating and temporary-file cleanup. Static lint is clean.

The final combined factorized-model and two-domain-state regression passed
**1,150 tests in 153.81 seconds**, including all 108 new checkpoint/harness tests
and the existing 1,042 tests. It ran locally on CPU with third-party pytest
plugin autoload and pytest's cache provider disabled. This is not a Databricks
or CUDA rerun.

All **323 accepted historical CPU source payloads** remain byte/size exact.
The accepted manifest hash is unchanged at
`9a7d815ada69a7405552ac885b229e13f63eb24ff1ed6e57d0730734452ed5ff`;
the CPU lock remains
`c6fa5d600cd2810c40ae47d5eeeba341e0467c4c75dd7c7d310cf3628ab6349f`.
No legacy defaults, old installation/bootstrap notebook or frozen scientific
record was changed.

The [plan](PROJECT_TWO_TRACK_READINESS_AND_GPU_PLAN.md) and
[ledger](PROJECT_EVIDENCE_LEDGER.md) now mark the bounded GPU milestone and this
local checkpoint milestone complete. Compound totals remain **61 checked /
102 open / 163 total**; fields **31 open / 141 closed**; blockers **8 open /
4 closed**; formal Tests 28/29/30 **OPEN/OPEN/PENDING**; scientific results **0/4**.
Those broader tasks require more than this local component result.

## Limits and next step

This is a same-runtime, same-device CPU test with fresh objects **within one
OS process**, not an actual OS-process restart, cross-version/device resume,
CUDA checkpoint qualification, distributed training, dataloader/dropout/global-RNG
checkpointing, production retry policy, F105 validation, long-run convergence
or a full training release. The event cap and paths remain tiny and synthetic.

No CUDA discovery/allocation was explicitly requested, no GPU or cloud job was
launched, no package was installed and no real dataset was accessed. Numerical
libraries may perform internal availability probes; the result does not claim
that every internal library probe is absent.

**Next:** prepare a separate bounded GPU multi-step/resume implementation and
check, with explicit device restoration and stop conditions. Preparation does
not authorize execution. There is no need to rerun the earlier successful
Databricks setup or integrated parity notebooks. Real-data admission, the
complete numerical/scientific instance, production integration and complete
compute/storage budgets remain separate open work.
