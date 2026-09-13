# BASE precision candidate: bounded CUDA result accepted

Review date: 2026-09-13.

**COMPLETE — reported selected-device synthetic BASE precision-candidate parity
and exact replay.** This is a component qualification milestone, not production
adoption or full conditional learner/sampler qualification.

## Evidence and review

The user supplied the complete compact notebook JSON in this conversation. Its
outer and inner decisions are `PASS_SELECTED_CUDA_BASE_PRECISION_CANDIDATE_ONLY`.
The [normalized review extract](research/fixtures/factorized_base_precision_candidate_cuda_operator_review_2026_09_13.json)
retains the acceptance categories, case roster, controls, resource observations,
runtime and claim boundaries. It is explicitly a selected-field transcription,
not a byte-exact archive of the raw user message or the full report. Its SHA-256
is `36d040dc49c6651d7af876b1836d33d3192cc21706f8a6e1e2549ec6b432ecac`.
Reported execution was not independently rerun, and underlying tensor payloads
were not provided. Review checks consistency with the predeclared harness, not
independent reconstruction of remote tensors or authentication of the runtime.

The supplied report has all four ordered domain/method routing cases, with two
unique BASE fixtures. Each case completed six fresh BASE steps with exact common
initial FP32 weights. Candidate CPU/target comparisons pass all eight categories:
exact tensors, forward, coordinate gradient, coordinate Hessian, parameter
gradient, losses, updated parameters and optimizer moments. Candidate and legacy
same-device replays are exact in every case.

| Reported quantity | Result |
| --- | --- |
| Device/runtime | Tesla T4, cuda:0; Torch 2.7.0+cu126; Python 3.12.3 |
| Cases and steps | 4/4 cases; 24/24 BASE steps: 16 GPU + 8 CPU |
| Candidate parameter-gradient maximum difference | 0 in all cases |
| Candidate updated-parameter maximum difference | 1.4901161193847656e-08 in all cases, over 96,705 parameters |
| Candidate moment maximum difference | 9.094947017729282e-13 |
| Candidate exact GPU replay | Zero difference in every category, all four cases |
| Harness elapsed time | 22.444928492 seconds |
| CUDA peak allocated/reserved memory | 72,496,640 / 73,400,320 bytes |
| Process-lifetime peak RSS | 1,188,839,424 bytes |
| Child completion | Exit 0, termination confirmed; zero stderr |

The original elementwise update criterion remains `atol=2e-6, rtol=2e-5`;
the observed candidate update residual is below even its absolute term. All
other tolerances also match the existing dictionary and reported hash
`c665d0d0d2f8c0ea9eca5407324c31c8bc4932d961901f488809a195af204ffd`.
No tolerance, scientific objective, optimizer setting or production default was
changed during this review.

## Legacy failures remain visible

Both methods have the same corresponding domain results:

| Comparison: maximum updated-parameter difference | Physio | Retail |
| --- | ---: | ---: |
| Legacy FP32 CPU/GPU, still FAIL | 8.682161569595337e-05 | 1.0221358388662338e-04 |
| Legacy CPU/candidate CPU drift, still outside legacy tolerance | 5.3241848945617676e-05 | 8.784793317317963e-05 |
| Shared-FP64 candidate CPU/GPU, PASS | 1.4901161193847656e-08 | 1.4901161193847656e-08 |

This is evidence that the chosen higher-precision graph stabilizes the tested
BASE computation across these CPU/GPU routes without relaxing acceptance. It
does not establish numerical stability for arbitrary data, batch sizes, weights,
long training runs or other hardware. The legacy reference is not relabelled.

The reported timing includes synchronization, transfers, host work and first-use
overheads. Candidate target steps are slower than candidate CPU steps on this
tiny fixture; there is no speedup or production-throughput claim. Memory peaks
are bounded synthetic observations, not full-training capacity estimates. The
notebook did not create a cloud job, but running on attached compute can incur
cost; this review does not claim the operator's run was free or stop the cluster.

## Subsequent local integration is complete

The [local precision-pipeline milestone](PROJECT_FACTORIZED_PRECISION_PIPELINE_LOCAL_INTEGRATION.md)
now records the implementation and CPU qualification of the three items below.
Four domain/method cases replay exactly through learned BASE, conditional updates
and tiny full paths. The existing physical FP32 gradient-return boundary is
preserved and tested. This does not extend the GPU evidence in this document:
candidate full-pipeline GPU qualification remains pending.

### Pre-integration inspection and completed work items

At the BASE-only GPU-review checkpoint, code inspection confirmed that the policy reached
`device_base_objective_on_corrupted_states` and `device_train_base_step`, but
`DeviceFactorizedPhysicalPotential._value` still evaluated the legacy FP32
model. Learned-BASE populations and conditional sampling constructed that potential.
The resulting local implementation/test work below is now complete, not another
environment setup or an immediate repeat of this successful GPU test:

1. Carry an explicit precision policy through physical BASE value/gradient
   evaluation, learned-BASE population generation and conditional sampling,
   preserving the legacy default. Include the policy in numerical population
   identity so incompatible routes cannot share an identity silently.
2. Test the actual physical coordinate-gradient path. It currently starts with
   CPU FP64 coordinates and crosses the existing FP32 input encoding before
   neural evaluation; merely promoting later does not remove that backward
   cast boundary. Do not silently change the observation/input definition.
3. Add bounded local end-to-end controls for trained BASE, paired populations,
   conditional learner and sampler. Use explicitly diagnostic common inputs and
   fixed noise for numerical parity, and exact replay within each route.
   Population law identities enter RNG keys, so equal run seeds alone do not
   couple different device/precision populations. Do not alter scientific law
   identities merely to force path equality.

Broader GPU execution would follow local qualification and a separate bounded
handoff. Trajectory/checkpoint validation, installed release, production-scale
cost, real-data admission and F105 integration remain open. No new GPU run,
package install, training campaign or source-code change was performed here.

## Plan delta

The bounded BASE candidate GPU milestone is marked COMPLETE. Compound timetable
tasks remain **61 checked / 102 open / 163 total**; fields **31 open / 141 closed**;
blockers **8 open / 4 closed**. Formal Tests 28/29/30 remain OPEN/OPEN/PENDING;
scientific results remain 0/4. A narrow successful component test does not close
the larger whole-method obligations.
