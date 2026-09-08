# Two-track readiness and GPU-training plan

Date: 2026-09-08
Status: the [mixed-domain scientific direction](PROJECT_MIXED_DOMAIN_SCIENTIFIC_AMENDMENT.md)
is ADOPTED structurally, with factorized state/reference, smooth-law oracle
and metadata-aware energy connected to actual BASE/conditional learning and
conditional sampling, with bounded local CPU qualification completed. The
structural choice and local connector no longer await work or user input.
The explicit-device successor and bounded parity/performance notebook are now
prepared and tested locally on CPU; **CUDA has not been executed or qualified**.
Numeric scientific settings and scalable whole-method integration remain open.
Authority: the user requested both tracks, local work without paid jobs, and
then delegated the scientific model-design choice. No real-data access,
scientific training or cloud job is authorized by this plan.

## Where we stand

The conventional Databricks installation and current-model synthetic integration succeeded: **235 required tests passed**, with the one agreed historical check still `OPEN_DEFERRED`. The [archived receipt](research/fixtures/b08_conventional_runtime_integration_2026_09_07_receipt.json) remains valid for its original CPU package and source snapshot. F152 remains closed for that accepted CPU lock; it is not a GPU dependency lock or qualification of new code.

| Parallel track | Completed locally | Still required to close the full track |
|---|---|---|
| Data and integration readiness | Supplied-input adapters for both domains; preservation, lineage and exact-F105 checks; split-input preparation; a source-only synthetic smoke notebook | Actual archives and source hashes, lossless Retail workbook decoding, applicable research-use determinations, eligible-group inventory, leakage/support checks, populated splits, admission and production-scale integration |
| Runtime and resource readiness | CPU facts reviewed; explicit-device optimizer/FP32 energy; actual classifier loss; numerical hybrid sampler, trainable visible encoder and independent nuisance; synthetic sampled-configuration F105 tests; expanded budget draft | Adopted structural amendment has a locally connected learner/sampler; numeric settings, real-dataset support and production-scale adapter remain open; numerical/scalable GPU qualification; admitted generation and compatible production checkpoint consumer; complete budget, spend and storage limits |

These are bounded completed components, not a claim that B02/B03/B08/B09/B12 or Waves 2/3 are closed. No real dataset was downloaded or opened; no GPU training or scientific run was launched. The user supplied successful adapter-smoke and CPU-runtime-facts reports; this agent did not independently execute those notebooks remotely.

## User inputs recorded without assumptions

- Databricks capacity reported by the user: **8 GPUs and up to 1000 GB memory**. GPU model, per-device VRAM, selected topology, actual allocation, hourly cost and spending limit are unknown. The memory statement is not interpreted as GPU VRAM or durable storage.
- Neither PhysioNet nor Retail source files are staged in Databricks yet. Research-use approval/determination references have not been supplied.
- The proposed project location is `/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II`. Keep code and notebooks there.
- Proposed bulk-data locations, subject to applicable permissions, retention and capacity approval:
  - `/Volumes/development/team_eds_supplychain/b08_runtime_output/datasets/physionet_challenge_2012`
  - `/Volumes/development/team_eds_supplychain/b08_runtime_output/datasets/online_retail_ii`

These are proposed paths only: no folder was created and no permission or quota was inferred from the earlier small Volume probe. Databricks recommends Volumes for data/archives and Workspace/Git folders for code. [Databricks file-location guidance](https://docs.databricks.com/aws/en/files/files-recommendations).

## Track 1: what the adapters do

The new [supplied-input adapter](src/heterodiff/data/two_domain_supplied_input_adapter.py) accepts complete supplied PhysioNet record texts or already-decoded Retail rows. It creates the exact F105 configuration representation while retaining source-order occurrence lineage, duplicates, missingness and context. Invalid inputs fail explicitly; no silent row filtering, deduplication, numeric/time coercion or source substitution is introduced.

PhysioNet text hashes identify supplied UTF-8 text, **not the original archive bytes**. Retail requires exact decimal price tokens and source-civil calendar values; an Excel-to-token decoder is still needed before actual workbook ingestion. The adapter prepares group/split inputs but does not issue a split, support certificate, governance approval or admission.

The existing F061 policy has a restrictive feasibility condition: preservation of all eligible groups under Hamilton 70/15/15 allocation, with exactly 128 validation and 128 test groups, admits only **852–855 total eligible groups**. This is a policy constraint, not an observed failure of either absent dataset. Here eligibility is determined only by the already-authorized complete-snapshot rules; it is not a new permission to filter natural groups until the target count fits. The code reports count compatibility without dropping or adding groups. If the actual eligible count is outside this range, stop for a pre-outcome split-policy amendment; do not take an arbitrary 128-group subset. [Existing F061 policy](PROJECT_F061_PRESERVATION_FIRST_ALLOCATION_PROPOSAL.md).

## Track 2: budget contradiction found and correction proposed

The frozen [training plan](research/fixtures/manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.json) and [B06 compute budgets](research/fixtures/manuscript_v3_b06_baseline_identity_matched_compute_freeze_v1.json) disagree. For **each primary method, in each domain**:

| Quantity | Frozen requirement |
|---|---:|
| Completed optimizer updates | 4,096 |
| Validation cadence | Every 256 updates, including terminal step |
| Checkpoints | 16 |
| Validation groups per checkpoint | 128 |
| Draws per group | 64 |
| Reverse steps per draw | 256 |
| Seeds | 256 |
| Validation-only reverse-step events | **8,589,934,592** |
| Existing FINAL_TRAINING reverse-step event ceiling | **4,194,304** |

Derivation: `16 × 128 × 64 × 256 × 256 = 8,589,934,592`, or **2,048 times** the ceiling, before other training work. The same phase also allows zero metric-draw events although checkpoint scoring is mandatory. Final confirmatory-inference budgets are a separate phase and cannot pay for checkpoint selection.

This is an accounting/design contradiction, not a Databricks installation error. GPU parallelism can shorten elapsed time but does not reduce logical event counts. The facts notebook independently reads these frozen files and reproduces all four primary-method/domain rows.

Proposed correction, **not yet adopted**: retain the approved validation schedule and seed/draw counts; reconcile the training-phase ledger to include checkpoint generation and scoring explicitly. Audit tuning and all comparator/control phases with the same event definitions, without mixing “one draw” and “one group score.” Recompute matched-compute envelopes and document the weights, aggregate budgets and hard limits before any scientific outcome is inspected. Do not simply use the validation-only lower bound as a complete training budget.

F066, F072 and B06 are therefore reopened as `OPEN_REQUIRES_PREOUTCOME_AMENDMENT`. Their historical freeze records remain unchanged; unaffected identities, licenses and configuration choices remain accepted. F144 remains frozen. At that September-7 budget checkpoint, totals were **61 checked / 102 open / 163 total**, **25 fields open / 147 closed**, and **8 blockers open / 4 closed**. The September-8 scientific amendment reopens six observation fields: current fields **31 open / 141 closed**; checkbox and blocker totals are unchanged. The decrease in checked boxes is an honest correction to B06, not loss of the successful runtime tests. Formal Tests 28/29/30 remain OPEN/OPEN/PENDING; scientific results remain 0/4.

## Completed local code-and-plan milestone (2026-09-07)

**COMPLETE — explicit-device synthetic training kernel.** The additive
[training module](src/heterodiff/experiments/two_domain_gpu_training.py) executes
real forward/backward/AdamW updates on caller-declared synthetic inputs. It
retains canonical cyclic batches of 16, the exact optimizer and constant-rate
contract, the full 4096/256 default schedule, no early stopping, CPU64 score
aggregation and earliest tied checkpoint selection. Short schedules are labelled
nonconfirmatory. Generic scalar callbacks remain uncertified; the new explicit
F105 callback route retains real factory records for supplied configurations,
without authenticating generation or admission. There is no production
retry/resume or cloud-job entrypoint.

**COMPLETE — actual energy graph's FP32 training view.** The separate
[model view](src/heterodiff/models/configuration_energy_training_torch.py) copies
the existing typed DeepSets encoders/readout without changing the CPU64 reference.
It retains architecture dimensions, occurrence multiplicity, the stable bounded
coordinate transform, tanh layers, normalized time/count and bounded output.
Device-local FP32 segment sums are explicitly different from the reference's
sorted CPU64 `math.fsum`: this is not a certified checkpoint or bitwise-equivalent
GPU implementation. Existing architecture/resource limits are retained, with an
additional bound on the draft segment-owner scans; domain-scale limit lifting
and performance qualification remain open.

**COMPLETE — prospective budget amendment draft.** The
[amendment](PROJECT_TWO_DOMAIN_COMPUTE_BUDGET_AMENDMENT.md) enumerates all 22 rows,
36 prospective tuning trials and 5632 scheduled final seed runs. It preserves the
scientific workload and proposes equal primary-pair envelopes by adding omitted
validation work. The proposed primary FINAL_TRAINING logical ODE ceiling is
8,594,128,896 per method/domain, not a GPU-hour or monetary budget. The all-22-role symbolic mapping is now implemented, but non-primary
executable mechanisms, calibrated weights and resource/spending limits remain
unassigned. F066/F072 and B06 remain OPEN until the complete amendment is reviewed
and adopted; no frozen historical budget was overwritten.

## Completed local conditional-loss and metric integration (2026-09-07)

**COMPLETE — actual equation and bounded population path.** The new classifier
implements the manuscript's equal-prior joint/product logistic objective for
G+R and DIR, the single cubic clean-hold gate, nuisance-free physical potential,
and explicit unnormalized rational sampling-law weights. The finite candidate-
base population constructs independent same-context/task/time branches with
terminal observation draws. This is a tested finite synthetic population,
not the later additive numerical hybrid sampler or a production continuous K_m.

**COMPLETE — actual supplied-configuration F105 checkpoint connection.** The
adapter computes real CPU64 factory scores for all 128 groups with 64 supplied
configurations each. The optimizer retains those factory objects and validates
their model-state/run/update/roster binding. Serialization exports compact
audit records only. No generated-draw, truth, admission or complete campaign
authentication is implied. The old frozen F144 helper's registry/metric domain
identifier mismatch is explicit, not bypassed by inventing a factory digest.

The [local integration record](PROJECT_CONDITIONAL_TRAINING_PIPELINE_LOCAL_INTEGRATION.md)
documents the implementation, combined synthetic tests and precise limits.
The older executable specification's unimplemented-objective status is now
historical for these additive local components; its frozen source is preserved.

**COMPLETE — later local hybrid and observation-model milestone.** Actual
continuous/jump trajectories, log-h-only conditional initialization, total
neural guide/residual composition, trainable visible encoding and independent
nuisance are now connected to the optimizer and F105 synthetic validation.
The [new record](PROJECT_HYBRID_SAMPLER_AND_OBSERVATION_INTEGRATION.md) separates
this executable numerical implementation from production qualification.
The [design proposal](PROJECT_TWO_DOMAIN_TRAINING_DESIGN_PROPOSAL.md) gives
concrete encoder/nuisance formulas and a synthetic law; no frozen scientific
choice is silently adopted. Paired base-generation work is separately
reported in the prospective budget amendment.

**COMPLETE — local support/observation review and symbolic work mapping.**
The [latest milestone](PROJECT_DOMAIN_SUPPORT_AND_OBSERVATION_REVIEW.md)
records exact F105 semantic-image checks and supplied discrete-key scalar
fibers, a separately labeled dominated affine observation proposal connected
to the local model/sampler, and all-22-role work formulas. The full-domain
schema is not finalized: discrete scoring fields cannot be arbitrary Gaussian
coordinates, and the frozen identity-half-thinning observation law has a
singularity/common-support conflict with the current smooth guide.

**COMPLETE — structural scientific amendment (2026-09-08).** The
user-delegated [mixed-domain direction](PROJECT_MIXED_DOMAIN_SCIENTIFIC_AMENDMENT.md)
is selected, with exact factorized keys, a normalized reference, a positive
smoothed target and noisy half-thinning observation law, plus a bounded
likelihood/guide oracle and shared metadata energy. The previous choice
between model families is no longer pending.

**COMPLETE — connected factorized local learner/sampler (2026-09-08).**
The [integration record](PROJECT_FACTORIZED_CONDITIONAL_PIPELINE_LOCAL_INTEGRATION.md)
connects actual BASE score/jump-flux training, full-interval conditional risk,
independent learned-BASE pairs, cap-correct reference-posterior initialization
and physical hybrid paths. Both domains and both primary methods are exercised
with real synthetic optimizer updates; exact keys/atoms, nuisance isolation and
clean hold are checked. This is source/local CPU qualification only.

**COMPLETE — explicit-device successor and bounded test preparation.** The
[device pipeline record](PROJECT_FACTORIZED_DEVICE_PIPELINE_LOCAL_QUALIFICATION.md)
documents the neural FP32 CPU/CUDA implementation, actual BASE/conditional
updates and CPU-orchestrated conditional paths, plus fixed-tolerance four-case
checks and the inspection-first [notebook](databricks/notebooks/factorized_gpu_parity_and_performance.py).
Both the complete connector tests and actual supervised harness passed locally
on CPU. The CUDA route is prepared but unexecuted. This is source-only, not an
installed GPU release; analytic matching, path RNG/control and F105 remain CPU.

**COMPLETE — inspection-driven compatibility repair (2026-09-08).** The
reported Torch 2.7 runtime now has a version-selected FP32-control path, and
an absent cuBLAS value is supplied only to the isolated test child before
Torch imports. No cluster edit, restart or package upgrade is needed for
these two issues. The updated local regression passed 480 tests; this is
not an actual Torch 2.7/CUDA pass. The user has authorized one bounded
GPU check, but its execution/result remain pending. See the
[follow-up record](PROJECT_FACTORIZED_DEVICE_PIPELINE_LOCAL_QUALIFICATION.md#2026-09-08-inspection-driven-compatibility-follow-up).

**Next local-to-GPU steps, still OPEN.** One separately authorized selected-
device synthetic run can now test the prepared route. Full trajectory/F105
checkpoint performance, installed GPU release qualification and scalable
matching/count measurements remain separate work. Specify the numerical
regularization/noise sensitivity instance prospectively and establish the
needed derivative/path/numerical bounds. Complete matched work totals and
real-data support/admission in parallel. No old finite-type certificate or
accepted CPU receipt is automatically transferred. No paid cluster or new
Databricks configuration is requested by this preparation milestone.

## Proposed GPU-training successor

The design below replaces the CPU-only *training* restriction when a successor is approved and implemented. For now, F141/F153 retain their closed CPU-reference definitions; this draft does not reinterpret their existing values. F155's accelerator-hour ceiling remains open, not zero.

### 1. Preserve the scientific workload

Use **one GPU per independent method/domain/seed run**, initially one run at a time for qualification. After qualification and budget approval, schedule up to eight independent runs concurrently, bounded by the GPUs actually allocated, host RAM, per-device VRAM and storage bandwidth. Distribute work by fixed run identifiers, never by completion order or observed score.

Retain each method's fixed 16-record logical batch, canonical ordering, 4,096 optimizer updates, optimizer/schedule, seed registry, 16 validation checkpoints, 128 validation groups and 64 draws per group. No eight-way distributed optimizer, batch-size multiplication, seed replacement, opportunistic early stopping, reduced validation, AMP or TF32 is introduced by this plan. Distributed training within a run would be a separate design change, not the default use of the eight GPUs.

### 2. Use a separate, ordinary GPU runtime

Keep the accepted CPU reference environment unchanged. Select a Databricks GPU runtime and a CUDA-enabled PyTorch build compatible with the observed GPU/driver/Python combination; resolve and hash-pin its dependencies as a separate GPU lock. The current `torch==2.12.1+cpu` wheel is not the GPU build. No Docker/ECR/custom-container route is required.

The new read-only notebook observes local NVIDIA device model, per-device memory and driver version when available. This is not CUDA execution qualification or proof of all worker devices. If only the current CPU cluster is attached, missing GPU metadata is expected; do not create or start a paid GPU cluster solely to satisfy this report. An existing cluster export can supplement unavailable facts.

Do not remove the CPU reference's `CUDA_VISIBLE_DEVICES` setting now. The future GPU-specific launch configuration must expose only the device allocated to that process, before PyTorch initialization; it must not inherit an empty CPU mask accidentally.

### 3. Implement the GPU training path, not just a device flag

The source contains explicit CPU/device checks and CPU RNG/checkpoint assumptions, for example in [reference training](src/heterodiff/models/reference_training.py) and the [training-plan precision contract](src/heterodiff/experiments/two_domain_training_checkpoint_plan.py). A global `.to("cuda")` replacement is insufficient. In particular, `reference_training.py` is a bounded CPU smoke trainer with permutation sampling: its sampler is not the frozen F142 canonical cyclic sampler and must not be ported unchanged as the scientific training schedule.

The explicit-device optimizer, model/input placement, AdamW state, synthetic random-stream separation and checkpoint inspection are now implemented and tested locally on CPU. The conditional loss and supplied-configuration CPU64 F105 connection are also implemented. The additive numerical hybrid sampler and trainable observation/nuisance proposal are now implemented and tested locally. The structural chart/kernel successor is now adopted; its numerical instance, full-domain support and new production adapter remain open, followed by sampler qualification, scalable device-local generation and installed GPU release/hardware qualification. Keep exact CPU-only reference/certification routines as reference routines; audit the remaining initializer/guide/residual/generation boundaries. Preserve source/order/seed bindings and checkpoint eligibility rules. Any random-stream or precision change needs an explicit versioned successor, not a claim of identical CPU trajectories. Synthetic archive inspection does not authorize production save/restore/retry.

Proposed numerics: binary32 model/gradient/optimizer state, mixed precision off, IEEE FP32 rather than TF32 for matrix/convolution operations. Retain the existing CPU binary64 F105 scoring and exact aggregation route. This limits the initial GPU change to training and compatible generation kernels; moving the certified metric to GPU is not implied. PyTorch exposes backend-specific FP32 controls; use one consistent API family for the selected version. [PyTorch CUDA precision documentation](https://docs.pytorch.org/docs/2.12/notes/cuda.html).

Enable deterministic algorithms in error-on-unsupported mode and disable cuDNN algorithm benchmarking. Select any required CUDA workspace configuration against the chosen build before initialization. Qualify repeatability on the selected device/build; do not promise bitwise equality between CPU and GPU or across library/hardware changes. [PyTorch reproducibility guidance](https://docs.pytorch.org/docs/2.12/notes/randomness.html).

### 4. Qualify with small nonconfirmatory checks

Before any full campaign, run the relevant unit/integration tests against the new installed GPU package, then tiny synthetic forward/backward, optimizer-update, save/reload/resume and fixed-run repeatability checks. Synthetic save/reload/resume checks test serialization correctness only; they do not authorize production resumption, restart, retry or top-up. Existing F145/F148 restrictions remain unchanged. Include finite gradients, device placement, no lost/duplicated records, event-counter correctness and independent metric recomputation. Define numeric comparison tolerances before the GPU comparison, and retain exact equality only for quantities whose contract requires it. A GPU test failure remains a failure; do not silently skip CPU-only assumptions and report the old suite as GPU-passed.

Refresh the release source manifest and wheel for the new adapter/GPU code, and verify that release once. The current new adapter is intentionally outside the previously accepted 323-file snapshot. This is normal release work, not a reason to reopen retired one-shot custody protocols.

### 5. Measure and cap cost before scaling

After authorization for a bounded synthetic benchmark, measure per-update time, full validation-checkpoint time, host/GPU peak memory and output size on the chosen hardware. The previous 22-minute unit-test run is not a training-duration estimate. Use the corrected ledger to project tuning, training, checkpoint validation, final inference and storage separately for every method/domain/seed roster. Account for CPU metric work and transfers as well as GPU work.

For accounting, allocated GPU-hours are `sum(allocated GPU count × allocation duration in hours)`; eight allocated GPUs for one hour are eight GPU-hours even if some are idle. Money projections must additionally include actual compute/Databricks rates and applicable storage charges. Freeze a monetary or equivalent enforceable total limit, per-run timeout, concurrency ceiling, memory limits and durable-storage allowance before campaign launch. No values are guessed from available RAM or GPU count.

### 6. Launch only after data and budget readiness

Admit the actual datasets with frozen splits and leakage/support checks, approve the coherent GPU/compute successor, then run the separately authorized training/evaluation campaign. Keep data acquisition, exploratory/synthetic qualification and confirmatory results clearly separated. No estimated completion time is committed until the workload and hardware measurements support it.

## Databricks status and what the user needs to do now

The two requested notebook reports have been received. The adapter smoke passed
on tiny invented inputs; its one-group F061 incompatibility is expected and is
not a finding about either absent real dataset. The runtime report identifies
the attached `m6i.8xlarge` single-node CPU environment, 32 CPUs and about 119.5 GiB
host RAM. NVIDIA metadata was unavailable; no GPU model, VRAM or CUDA readiness
was established. Its notebook-scoped missing Torch/heterodiff metadata does not
invalidate the earlier successful notebook's accepted installation receipt.
The supplied report's record digest is
`e155b6f04a4dd2ed5e7575c919edeea80b5e07f2ab08feff5ecbf414c20b5b70`;
these are operator-supplied observations, not independently repeated remote facts.

**No new Databricks execution is requested for this local milestone.** Sync the
changes through GitHub whenever convenient, but do not rerun the old conventional
bootstrap: it binds its earlier exact source roster, and these additive modules
belong to a future release. Do not start a paid GPU cluster or repeat the old
Docker/ECR/custody setup. The accepted CPU receipt and old release are preserved.

Still needed before paid qualification or bulk data staging: selected GPU
model/VRAM/driver/runtime, an enforceable spending or job-hour limit, durable
storage allowance, and the applicable research-use determination or route for
obtaining it. Unknown values stay uncommitted, not inferred from GPU count or RAM.

## Local verification record

**Latest local device checkpoint:** [GPU-capable preparation and CPU
qualification](PROJECT_FACTORIZED_DEVICE_PIPELINE_LOCAL_QUALIFICATION.md) is
complete. The new notebook/harness was exercised through an actual isolated
CPU child, not just mocked. Exact test counts and scope are recorded there.
CUDA qualification remains unexecuted, and no scientific field/compound box
closes from these local tests.

**Previous local scientific checkpoint:** the
[factorized conditional pipeline](PROJECT_FACTORIZED_CONDITIONAL_PIPELINE_LOCAL_INTEGRATION.md)
is connected and locally qualified. Its [synthetic qualification](PROJECT_FACTORIZED_LOCAL_QUALIFICATION.md)
does not establish GPU readiness, full-size performance, model quality or
scientific convergence. Numerical instance and full-production integration
remain open.

**Previous local support/observation checkpoint (2026-09-07):** see
[verification and preserved state](PROJECT_DOMAIN_SUPPORT_AND_OBSERVATION_REVIEW.md#verification-and-preserved-state).
This historical checkpoint recorded the then-unresolved structural choices;
the September-8 amendment above now resolves the family selection.

**Previous local hybrid checkpoint:** see the complete test result and scope in
[hybrid verification](PROJECT_HYBRID_SAMPLER_AND_OBSERVATION_INTEGRATION.md#verification-and-preserved-state).
The four end-to-end cases use actual hybrid paths, one conditional optimizer
update each, and 128-by-64 genuine F105 scoring. They do not establish real-
domain decoding/observation laws, model quality, production admission or CUDA.

**Earlier conditional-integration checkpoint (retained history): 954 tests passed in 70.42 seconds**,
including 16 combined pipeline cases; see the
[verification record](PROJECT_CONDITIONAL_TRAINING_PIPELINE_LOCAL_INTEGRATION.md#verification-and-preserved-evidence).
The new tests exercise the actual classifier objective and real F105 factory
records on explicitly finite synthetic populations. This is not a claim of
general hybrid-sampler completion, installed Databricks success or CUDA testing.

**Earlier local implementation checkpoint (retained history):** **795 tests passed in 25.69 seconds**
across the new trainer, energy view and budget amendment, plus the existing
adapter/facts, two-domain admission, F061, F104/F105, B06 registry and frozen
training-plan suites. The local interpreter was Python 3.11.5 with CPU Torch
2.12.1; this is not the Databricks Python 3.12 environment or a CUDA test.
The graph/optimizer integration performs two synthetic AdamW updates per domain
at the representative 112/10 coordinate dimensions, 64-dimensional context and
128-wide layers, then checks detached checkpoint serialization. It does not run
4096-update scientific training or the real joint/product loss. Static lint and
whitespace checks pass. Independent code/plan review found no remaining blocker
for this bounded local draft scope; GPU execution and production certification
remain unverified.

The latest integrity recheck found **zero changes in all 323 accepted CPU source
payloads**. The old manifest and CPU lock hashes are unchanged. The timetable
was independently recounted at **61 checked / 102 open / 163**; the local
milestone is marked COMPLETE in prose without closing broader compound tasks.

**Earlier adapter/facts preparation checkpoint (retained history):**

The combined local regression passed **519 tests in 18.49 seconds**: the 47 adapter/source-only-smoke cases, 32 runtime-facts cases, and adjacent PhysioNet/Retail admission, F105 exact-instance/production and F061 suites. The source-only notebook also passed under bare Python 3.14 with site packages disabled. Static lint and whitespace checks were clean. Runtime-facts tests use mocked Spark/GPU interfaces locally and bounded local test child processes; they do not inspect a remote cluster.

All 323 prior accepted source payloads were rechecked with zero content/size mismatches. The accepted manifest remains SHA-256 `9a7d815ada69a7405552ac885b229e13f63eb24ff1ed6e57d0730734452ed5ff`; the adapter and new training/budget modules are additive files outside that snapshot. Historical frozen scientific records and the accepted CPU lock/controller/support remain unchanged. Independent agents reviewed the adapter and the workload/budget/GPU-plan boundaries; this is source/planning review, not remote GPU qualification.
