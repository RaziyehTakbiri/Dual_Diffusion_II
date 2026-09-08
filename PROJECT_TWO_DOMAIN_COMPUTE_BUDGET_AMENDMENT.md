# Two-domain compute-budget amendment — draft

This is a pre-outcome arithmetic proposal, not an adopted budget, runtime
qualification, scientific result, paid-job authorization or replacement of the
frozen B06 records. F066/F072 and B06 stay open until review and adoption.
The existing CPU tests remain reference evidence; no GPU numerical-equivalence
or resource-capacity claim follows from this amendment.

## What is preserved

The proposal preserves every one of the 22 method/domain configuration rows,
batch size 16, 4096 final optimizer updates, 256 training seeds, checkpoint
validation at updates 256, 512, ..., 4096, 128 groups and 64 conditional draws per
group. Each tuning trial retains 1024 updates and four checkpoint validations.
F147 allows one trial for each of 20 singleton rows and eight trials for each
of two external-baseline rows: 36 total prospective candidate evaluations.
There is no empirical pilot or additional failure reserve. Failed attempts are
charged, with no replacement, retry, transfer or post-result top-up.

## Omitted checkpoint-validation work

For one method/domain/final-training seed, mandatory checkpoint validation has:

- 16 validation passes;
- 2048 group-score calls;
- 131,072 generated conditional draws; and
- 33,554,432 logical reverse sample-path steps for the primary 256-step sampler.

Across 256 seeds this becomes 524,288 group scores, 33,554,432 draws and
8,589,934,592 primary reverse sample-path steps. These are logical workload
counts, not batched model invocations or GPU-kernel launches.

The original whole-roster FINAL_TRAINING envelope has only 4,194,304
ODE_OR_SDE_STEP events and zero METRIC_DRAW_EVALUATION events. Its separately
scoped confirmatory allowance does not cover sixteen checkpoint validations.

## Separate joint/product training-population work

The current learned-base pair constructor simulates two complete independent
BASE trajectories for every training example, starting from the reference
initial law and sharing the task, context and query time. Branch one supplies
the state at the query time and its terminal observation for the joint pair;
branch two supplies an independent terminal observation for the product pair.
These are population-construction trajectories, not checkpoint-validation
conditional draws and not the two batched classifier forward calls.

Under one fresh pair per logical training example, each primary method/domain
therefore has the following separate prospective workload:

| Scope | Logical examples | Complete BASE trajectories | Nominal 256-grid reverse steps |
|---|---:|---:|---:|
| One optimizer update | 16 | 32 | 8,192 |
| One final-training seed (4096 updates) | 65,536 | 131,072 | 33,554,432 |
| All 256 final-training seeds | 16,777,216 | 33,554,432 | 8,589,934,592 |
| One primary tuning trial (1024 updates) | 16,384 | 32,768 | 8,388,608 |

The final-roster 8,589,934,592 nominal steps are **additional to** the same
number of checkpoint-validation path steps above. Together those two
activities alone require 17,179,869,184 nominal path steps per primary
method/domain under their respective 256-step conventions. This is not a
complete F104 event count, GPU-call count or measured workload. There is no
assumed free reuse between records, branches, methods or validation passes.
Tuning is not multiplied by the final-training seed roster.
Each complete BASE branch makes one reference-initializer and one observation
callback: 32 of each per update and 33,554,432 of each per final seed roster.
The internal randomness and work of those callbacks are not one model call.

A query-refined numerical grid can add intervals beyond the nominal 256.
Active Heun/jump substeps, rejection or thinning, potential-oracle calls,
initialization, observation-kernel sampling, encoders, classifier/nuisance
evaluation and backpropagation need their own runtime operation mapping.
This report assigns no numeric cap or measured total to those additional
operations; any local sampler limits are not a calibrated aggregate budget.
The primary rule is not assigned to controls or non-primary adapters without
their actual population-construction contracts.

## Partial equal primary-pair correction: validation only

`two_domain_compute_budget_amendment.py` preserves every original B06 event
allowance and adds a visible validation allowance. It scales the existing B06
per-group confirmatory convention: 64 draws, 256 logical reverse steps per draw,
the existing domain maximum-event adapter allowance, and 64² metric-resource
units per group score. Final training adds 16 times the original whole-roster
inference vector. Primary tuning adds four full validation passes for its one
allowed candidate, without enlarging F147's trial limit.
The numeric table below is retained as the original-plus-validation proposal
only. It does **not** yet map or add the separate population-generation work
above and must not be adopted as a complete training envelope.

| Event/phase | Original envelope | Added validation allowance | Proposed envelope |
|---|---:|---:|---:|
| FINAL_TRAINING ODE_OR_SDE_STEP | 4,194,304 | 8,589,934,592 | 8,594,128,896 |
| FINAL_TRAINING METRIC_DRAW_EVALUATION | 0 | 2,147,483,648 | 2,147,483,648 |
| TUNING ODE_OR_SDE_STEP | 32,768 | 8,388,608 | 8,421,376 |
| TUNING METRIC_DRAW_EVALUATION | 1024 | 2,097,152 | 2,098,176 |

The two primary methods receive exactly equal prospective envelopes within
each domain. Equal guide-operation opportunity does not mean a method without
an analytic guide must consume it. Preserving the older eight-trial resource
envelope does not permit extra trials: F147's one-trial primary limit still
binds. Pilot and confirmatory phase envelopes are unchanged.

The 64² metric allowance is the inherited B06 resource convention, not measured
F105 event-pair work. An F105 R64 score has 2080 distinct configuration-pair
evaluations; its symbolic event-pair work additionally depends on the actual
configuration cardinalities. The proposal does not call either quantity GPU
operations or FLOPs.

## All 22 rows and remaining gaps

The implementation reports each primary, control, literature-family and
external-baseline row separately. It derives their scheduled update, record,
validation-pass, score and draw counts, including the external eight-trial
grids. It does not deduplicate role rows or claim free reuse.

Only the primary pair receives a numeric F104-event ceiling proposal here.
For non-primary rows, upstream defaults or an adapter interface do not prove
the final sampling schedule, optimization applicability for removed-component
controls, or actual operation mapping. Those values remain explicitly unknown.
They must not be borrowed silently from the primary 256-step sampler.

F104 event-specific calibration weights, a scalar total, wall-time/GPU-hour
caps, model-evaluation aggregation, host/device memory and storage caps,
approved spending and capacity all remain unassigned. A runtime mapping must
also account for actual metric work and every author-added operation before
the proposed envelope can become an execution budget. No invented unit
weights or test-suite timing is used as calibration.

## Conditional-loss implementation audit (2026-09-07)

The [local conditional pipeline](PROJECT_CONDITIONAL_TRAINING_PIPELINE_LOCAL_INTEGRATION.md)
now implements the paired classifier loss. This does not change the preserved
16-record/4096-update/16-checkpoint/128-group/R64/256-seed workload or the
validation-count addition above. It exposes two additional unresolved parts
of the prospective *complete* budget:

- **Parameter-count hard axis:** the accepted B06 count covers a frozen base
  plus one conditional DeepSets: 211,202 parameters for PhysioNet and 185,090
  for Retail. Each module has `128 × event_dimension + 91,265` parameters.
  The new classifier also has a separately supplied nuisance network; its
  production architecture is not selected. The raw observation/task/context
  feature encoder is unresolved too. The internal 64-input context MLP is
  already counted and must not be counted twice. Count additional unique
  nuisance/encoder parameters, distinguish frozen and trainable parameters,
  and preserve matched primary/comparator capacity in a prospective
  F064/F070 configuration and F065/F071 parameter-count successor. The small
  nuisance network in the tests is not a production choice. Historical
  frozen values are unchanged, not applied to an unreviewed expanded model.
- **Training-operation mapping:** the current paired-loss implementation
  makes two batched forward passes through each classifier and nuisance per
  update, each pass containing 16 logical examples: 32 per-record evaluations
  of each per update. There are 8,192 batched passes of each per final seed and
  2,097,152 per 256-seed primary/domain roster. Valid paired batches
  invoke the backbone either zero or twice depending on the clean-hold gate.
  These are implementation-call counts, not calibrated F104 event units,
  GPU launches or FLOPs. The old one-conditioner-forward-per-update allowance
  is not proven sufficient. All classifier, nuisance, raw-encoder and gradient
  work needs an explicit event mapping; no numeric OTHER weight/allowance or
  larger ceiling is invented here.

The nuisance is excluded from the physical potential, so it does not
automatically add a nuisance evaluation to every reverse sampling step. The
model sampling implementation must determine its actual inference work.
Until population-generation charging, these mappings, the non-primary mappings, weights and resource limits
are resolved, the numeric primary envelope above is only a validation-work
arithmetic proposal—not a certified complete training budget.

## Implementation and review use

### Symbolic operation ledger: what the current implementation actually counts

The additive counters now resolve operations below the nominal-path-step level
without running a model or turning logical work into guessed compute weights.
Their input counts are explicit supplied quantities, not authenticated runtime
measurements. Failure/partial-run work must be charged separately.

For successful hybrid paths let A/H be active/held macrointerval totals, E be
nonempty Heun halfsteps, C be jump candidates and W be waiting-time draws:

| Current sampler operation | Exact count or truthful bound |
|---|---:|
| Macrointervals | A + H |
| Heun halfstep calls | 2A |
| Physical potential `value_grad` callbacks | 2E, with E ≤ 2A |
| Physical potential scalar `value` callbacks | W + C |
| Candidate draws and acceptance uniforms | C each |
| Intensity preflights | Between W and C + A; exact W + Z if zero-intensity returns Z are supplied |
| Path stream requests, excluding observation sampling | Number of paths + 2A + W + 2C |

A held interval calls neither Heun nor the potential; an empty Heun halfstep
calls no gradient. The final no-event clock is not universally present:
zero-intensity termination and floating-point addition reaching the interval
boundary prevent treating C + A as an unconditional exact preflight count.
A query refinement adds exactly one interval to each refined path; for P paths
on a nominal S-interval grid and Q refined paths, the count is P×S + Q. This
numerical-law change is not silently adopted or claimed equivalent to the freeze.

For the current uncached `TorchHybridPotential`, each scalar or gradient query
evaluates the base once when `include_base=True`. Each conditional query also
evaluates its baseline callback and observation encoder once, then the learned
conditioner only if the query is outside the clean-hold gate. The nuisance is
never evaluated on this physical surface. Coordinate-autograd requests are
bounded by the number of gradient queries; their internal arithmetic and the
baseline's oracle cost are separate from callback counts. The supplied CPU
adapter is not a GPU-sampler qualification.

Conditional rejection initialization uses only the time-zero conditional factor,
not the base potential. For N completed draws with supplied cap L, proposal
counts lie between N and N×L; supplied per-draw counts give the exact reference
proposal, factor-value and acceptance-uniform call totals. The counter neither
selects L nor assumes one successful proposal per draw, an expected acceptance
rate, free failed attempts or a fallback sampler.

For a paired observed loss, the implementation makes two classifier passes,
two condition-encoder passes and two independent nuisance-encoder/head passes.
There is one loss backward and AdamW step per completed optimizer update. Both
encoders still execute when all records are in the clean hold. Given visible
anchor counts and schema widths, `observation_design_operation_counts` counts
all dense matrix multiply-accumulate terms, biases, tanh elements, pooling
inputs and normalization divisions. Those are partial arithmetic counts, not
all FLOPs, sorting/validation/reduction cost or gradient work. If the anchor
width is a and global width is d, each V1 encoder has
`E = 64(a + 64 + d) + 8448` unique parameters; the two disjoint encoders and
nuisance head add `2E + 2113`. The already counted internal context MLP is not
counted again. Exact production schema selection/adoption remains separate.

The separate overflow-aware proposal wraps each retained encoder with 65→64
plus tanh. It adds 4,224 unique parameters per encoder, 8,448 across the two
independent graphs. `overflow_observation_wrapper_counts` reports only this
addition; it does not replace V1 counts or skip retained-encoder work for
overflow rows. Neither encoder proposal changes historical F064/F065/F070/F071.

Finally, F105's actual factory work formula is now available without evaluating
the score. With 64 draw cardinalities n_i, target cardinality t, s=Σn_i and
q=Σn_i², the event-pair work is `64q + 64t² + (s²-q)/2 + ts` across 2080 unique
configuration-kernel calls. Actual cardinalities, exact-rational bit complexity
and coordinate dimension still determine the cost; 64² resource units are not
a substitute for this workload.

### Non-primary rows: resolved semantics versus missing algorithms

Every one of the 22 rows now has a component/mechanism mapping. The 8 control
rows are static component contracts. Four (analytic-guide-only and unconditional
base, each in two domains) have no declared learned-conditioner target despite
inheriting 4096 optimizer updates and 16 checkpoint validations. We preserve
those schedules and flag an explicit prospective treatment; we do not invent
a dummy optimizer, silently train a frozen base or erase their charges. The
other 4 control rows need their residual-only or factorized-eventwise mechanism.

The 8 literature-family and 2 external rows currently bind identities and
already materialized outputs, not executable optimizer/population/sampler
implementations. The declared CSDI 50-step and EditPP 100-step upstream defaults
are retained as reference metadata only—not adopted domain-adapter schedules.
The family/external role equivalence does not create free reuse or remove a row.
Their scheduled record/score/draw counts are derivable; their missing model
mechanisms and actual event mappings are not inferable from an interface.

### Minimal decisions still required

- Scientific/implementation: review real-domain observation schema/law and
  numerical-sampler/architecture successors; resolve the 4 no-learned-target
  control schedules; implement the remaining 4 control, 8 family and 2 external
  mechanisms; define operation units and failure/checkpoint/transfer overhead.
- Measurement: obtain actual active/empty/clock/jump/rejection/cardinality
  counts and calibrate event weights, throughput and memory on chosen hardware.
- Operator: choose available hardware and explicit time, memory, storage and
  spending limits; review the equal matched-compute successor before launch.

This is the reason the retained numeric table is deliberately labeled partial.
Measured weights and hardware are not the only remaining inputs: missing
non-primary mechanisms and scientific successor choices cannot be fabricated
by multiplying existing counters. No cap is increased by this document.

### Public arithmetic entry points

- `training_run_workload(method_id, domain_id)` returns the inherited single-seed
  schedule, separate joint/product population counts and full-roster logical
  validation workloads for a GPU-path dry run.
- `proposed_primary_phase_ceiling(method_id, domain_id)` returns the original,
  additional and proposed four-phase/ten-event ledgers, explicitly scoped to
  the partial original-plus-validation allowance rather than all training work.
- `build_budget_amendment()` returns all 22 rows, four primary proposals,
  content-identity bindings and explicit unknowns.
- `method_operation_mapping`, `hybrid_grid_workload`,
  `hybrid_sampler_operation_counts`, `neural_potential_operation_counts`,
  `conditional_rejection_workload`, `observation_design_operation_counts`,
  `overflow_observation_wrapper_counts` and
  `f105_symbolic_work_from_cardinalities` expose the separate pure counters.

All functions are pure arithmetic/configuration code: no file I/O,
package installation, training, data access, device access, timing benchmark,
network request, checkpoint write or paid job is performed. Tests check exact
fixture agreement, separate population/validation counts, equal primary
opportunities, all trial counts, unknown
non-primary mappings, nonmutation and compatibility with the existing exact
F104 calculator. Synthetic unit weights appear only inside a calculator test,
never in the returned proposal.
