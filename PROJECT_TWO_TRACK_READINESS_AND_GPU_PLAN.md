# Two-track readiness and GPU-training plan

Date: 2026-09-07  
Status: local adapter/facts deliverables complete; GPU successor **draft prepared, not activated**.  
Authority: the user requested both readiness tracks in parallel and selected “Prepare GPU-training plan.” This authorizes preparation, not training, paid jobs, data acquisition, or approval on behalf of a data owner.

## Where we stand

The conventional Databricks installation and current-model synthetic integration succeeded: **235 required tests passed**, with the one agreed historical check still `OPEN_DEFERRED`. The [archived receipt](research/fixtures/b08_conventional_runtime_integration_2026_09_07_receipt.json) remains valid for its original CPU package and source snapshot. F152 remains closed for that accepted CPU lock; it is not a GPU dependency lock or qualification of new code.

| Parallel track | Completed locally | Still required to close the full track |
|---|---|---|
| Data and integration readiness | Supplied-input adapters for both domains; preservation, lineage and exact-F105 checks; split-input preparation; a source-only synthetic smoke notebook | Actual archives and source hashes, lossless Retail workbook decoding, applicable research-use determinations, eligible-group inventory, leakage/support checks, populated splits, admission and production-scale integration |
| Runtime and resource readiness | Read-only cluster/GPU facts notebook; reproducible frozen-budget arithmetic audit; this GPU-training successor plan | Operator runtime report, GPU implementation/qualification, coherent prospective budgets, spending limit and approved durable-storage allocation |

These are bounded completed components, not a claim that B02/B03/B08/B09/B12 or Waves 2/3 are closed. No dataset was downloaded or opened; no GPU training or scientific run was launched. The new notebooks have been tested locally, not executed remotely by this agent.

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

F066, F072 and B06 are therefore reopened as `OPEN_REQUIRES_PREOUTCOME_AMENDMENT`. Their historical freeze records remain unchanged; unaffected identities, licenses and configuration choices remain accepted. F144 remains frozen. Current tracker totals are **61 checked / 102 open / 163 total**, **25 fields open / 147 closed**, and **8 blockers open / 4 closed**. The decrease in checked boxes is an honest correction to B06, not loss of the successful runtime tests. Formal Tests 28/29/30 remain OPEN/OPEN/PENDING; scientific results remain 0/4.

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

Implement a GPU-capable training adapter that handles model/input placement, optimizer state, declared random streams, checkpoint save/restore and per-run device allocation. Keep exact CPU-only reference/certification routines as reference routines; audit CPU/GPU boundaries for the initializer, guide, residual and metric components. Preserve source/order/seed bindings and checkpoint eligibility rules. Any changed random-stream algorithm or precision contract needs an explicit versioned successor, not a claim of identical CPU trajectories.

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

## What to do in Databricks now

1. Push these changes to the existing GitHub repository as usual, then pull them into the existing Databricks Git folder.
2. In **Workspace**, open `/Workspace/Users/Hadi.Mohebalizadeh@nike.com/Diffusion II/Dual_Diffusion_II`, then `databricks` → `notebooks` → **`two_domain_adapter_smoke`** (the source file ends in `.py`). Attach the existing compute and choose **Run all**. It uses tiny invented inputs only, in a separate source-only process; no installation or Python restart is needed. Expected decision: `PASS_TWO_DOMAIN_SUPPLIED_INPUT_ADAPTER_SYNTHETIC_SMOKE`; scope: `SOURCE_ONLY_ADAPTER_SMOKE_NOT_INSTALLED_WHEEL`.
3. Open **`b08_runtime_facts_and_budget_review`** in the same folder. Attach existing compute and choose **Run all**. Leave the optional `CLUSTER_JSON` box empty for the first run. Expected overall decision: `FACTS_COLLECTED_REVIEW_REQUIRED`. The budget section is expected to report `PREOUTCOME_BUDGET_RECONCILIATION_REQUIRED`; that is the known planning finding, not another setup failure. Missing GPU fields on CPU compute are not a failure.
4. Return both JSON summaries. If key cluster facts are unavailable and you already have a cluster JSON export, put that JSON in the **CLUSTER_JSON** input at the top of this second notebook, then run it again. No parameter is edited inside the source file.

Run **only these two new notebooks**, not the old conventional bootstrap or every notebook in the repository. The old bootstrap validates its earlier exact source roster and will reject newly added source files until a future release refresh; its successful historical receipt is preserved. The source-only smoke also bypasses unrelated legacy data-package initializer exports in its isolated child, so it is not a substitute for installed-package testing.

Still needed from the user before paid work or bulk data staging: a total compute-spending limit (or enforceable job-hour allocation), durable storage allowance, and the applicable research-use approval/determination or route for obtaining it. “Unknown” is an acceptable answer; these stay uncommitted, not inferred.

## Local verification record

The combined local regression passed **519 tests in 18.49 seconds**: the 47 adapter/source-only-smoke cases, 32 runtime-facts cases, and adjacent PhysioNet/Retail admission, F105 exact-instance/production and F061 suites. The source-only notebook also passed under bare Python 3.14 with site packages disabled. Static lint and whitespace checks were clean. Runtime-facts tests use mocked Spark/GPU interfaces locally and bounded local test child processes; they do not inspect a remote cluster.

All 323 prior accepted source payloads were rechecked with zero content/size mismatches. The accepted manifest remains SHA-256 `9a7d815ada69a7405552ac885b229e13f63eb24ff1ed6e57d0730734452ed5ff`; the new adapter is the only additional `src/heterodiff` Python file outside that snapshot. Historical frozen scientific records and the accepted CPU lock/controller/support remain unchanged. Independent agents reviewed the adapter and the workload/budget/GPU-plan boundaries; this is source/planning review, not remote GPU qualification.
