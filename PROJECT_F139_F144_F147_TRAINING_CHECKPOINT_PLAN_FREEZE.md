# F139--F144/F147 exact training and checkpoint plan freeze

**Reported:** 2026-09-01  
**Candidate state:** `PENDING_INDEPENDENT_REVIEW`  
**Control predicate:** `F139_F144_F147_TRAINING_CHECKPOINT_PLAN_FROZEN_PREOUTCOME_V1`  
**Package kind:** `ALL_OR_NOTHING_SEVEN_PREEXECUTION_FIELD_CLOSURE`  
**Execution state:** `DRAFT_NOT_EXECUTABLE`

## 1. Decision and exact scope

This candidate freezes exactly the seven still-open training/checkpoint fields:

| Field | Pointer | Frozen value class |
|---|---|---|
| F139 | `/training_and_checkpoint_plan/optimizer` | Exact single-group AdamW contract |
| F140 | `/training_and_checkpoint_plan/learning_rate_schedule` | Constant predeclared-candidate-rate schedule |
| F141 | `/training_and_checkpoint_plan/precision` | CPU binary32 training and binary64 F105 validation |
| F142 | `/training_and_checkpoint_plan/batch_construction` | Exact 22-row domain-local, no-shuffle batch contract |
| F143 | `/training_and_checkpoint_plan/maximum_epochs_or_steps` | Exact integer `4096`, in `COMPLETED_OPTIMIZER_UPDATES` |
| F144 | `/training_and_checkpoint_plan/validation_metric` | Complete-roster F105 binary64 validation contract |
| F147 | `/training_and_checkpoint_plan/maximum_tuning_trials_per_method` | Exact per-method/domain B06-grid-or-singleton roster |

The proposal is all or nothing. It does not modify or reclose F145 or F146.
It preserves F145 as
`DISABLED_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY`, F146 as
`F146_EARLIEST_STEP_TIED_BEST_CANONICAL_CHECKPOINT_RULE_V1`, and F148 as
`NEVER_TRUE_NO_INFRASTRUCTURE_RERUN`.

Independent acceptance would close the existing timetable task **“Freeze
checkpoint-selection and training rules using training/validation data only.”**
No new project-control checkbox is created. B12 remains open because this
package does not supply, bind, or independently accept adapter, runner,
capsule, ledger, checkpoint, runtime, or independent-recomputation receipts;
parallel implementation candidates are outside this package, and no real
production receipt exists. B08 remains open because no hardware, runtime identity,
calibration weight, resource ceiling, allocation, or capacity reservation is
supplied.

No empirical outcome, data row, validation value, checkpoint, runtime success,
capacity fact, training run, or scientific result was used to choose a value.

## 2. F139 exact optimizer

F139 is the exact contract
`TORCH_ADAMW_EXACT_RATIONAL_SINGLE_GROUP_V1`:

- implementation class `torch.optim.AdamW`;
- one parameter group containing all and only trainable parameters;
- beta1 `9/10`, beta2 `999/1000`, epsilon `1/100000000`, and weight decay `0`;
- `amsgrad=false`, `maximize=false`, `foreach=false`, `fused=false`,
  `capturable=false`, and `differentiable=false`;
- one admitted batch per completed optimizer update; and
- gradient accumulation exactly one.

Every decimal-looking quantity is stored as a reduced numerator/denominator
object. The optimizer contract contains no floating-point literal, adaptive
choice, second parameter group, hidden regularizer, or post-outcome override.
The pure source validates the exact object but does not import Torch or execute
an optimizer.

## 3. F140 exact learning-rate schedule

F140 is
`CONSTANT_CANDIDATE_BASE_RATE_NO_WARMUP_V1`. The multiplier is exactly `1/1`
at every completed optimizer update, warmup is exactly zero, and validation-
driven or adaptive rate change is forbidden.

Each B06 method/domain configuration has a predeclared exact rational base-rate
roster. CSDI uses its accepted B06 grid values `1/2000` and `1/1000`. Every
other row uses the singleton `1/1000`; this package selects that singleton
prospectively rather than reading an outcome. For CSDI, the candidate rate is
selected only together with the rest of its exact eight-member B06 tuning grid
using training and validation data. The schedule is constant at the selected
predeclared rate; there is no decay, restart, warmup, plateau monitor, or
test-driven change.

## 4. F141 exact precision

F141 is `CPU_BINARY32_TRAIN_BINARY64_F105_VALIDATION_V1`:

- model parameters, gradients, optimizer moments, and stored checkpoint
  parameters use IEEE-754 binary32;
- autocast, mixed precision, and TF32 are forbidden;
- each F105 validation group score is an exact factory-issued finite binary64
  record with its canonical `float.hex()` representation;
- the 128 group-score binary64 values are converted to exact integer ratios,
  summed exactly, divided by 128, and rounded once to binary64;
- equality means byte-identical canonical binary64 hexadecimal text, with no
  tolerance and with signed-zero identity preserved; and
- a nonfinite group or aggregate is terminal `NONFINITE`, is checkpoint-
  ineligible, and creates no fallback or retry.

Training precision and validation aggregation precision are deliberately
separate roles. F141 makes no claim that a future complete B12 runtime has yet
demonstrated the policy.

## 5. F142 exact method/domain batch construction

F142 is
`DOMAIN_LOCAL_CANONICAL_CYCLIC_EXACT16_NO_SHUFFLE_V1`. The B06 event ledger
fixes 16 `DATA_ADAPTER_RECORD` events per completed optimizer update in both
the tuning and final-training phases. The package therefore freezes exactly
16 logical records per update for every one of the 22 B06 method/domain rows.

For PhysioNet a logical record is one admitted patient training record. For
Retail it is one admitted customer-window training record. Every adapter must
provide a nonempty admitted training roster of at least 16 records in canonical
ascending training-record-ID byte order. For completed update `u`, batch
position `j` uses roster index `(16*u+j) mod N` for `j=0,...,15`. The wrap is
an explicit deterministic cyclic schedule, not padding or a hidden shuffle.

The exact policy forbids:

- cross-domain batches;
- implicit or random shuffling;
- mixing training and validation roles in a batch;
- test records;
- mixing seed or tuning-trial identities; and
- silent last-batch drop, padding, replacement, or batch-size change.

Every method/domain row binds its exact current B06 configuration digest and a
domain-separated batch-contract digest. The roster is derived directly from
the accepted B06 registry. It is not copied from the older B12 hardcoded
adapter alias.

## 6. F143 exact bound and B06 arithmetic

F143 is the positive exact integer `4096` in the sole unit
`COMPLETED_OPTIMIZER_UPDATES`. It is the maximum final-training horizon for one
method/domain/training-seed run. F145 permits no validation early stopping,
duration extension, retry, resume, restart, or top-up; a production training
checkpoint can be terminally complete only at this exact final-training bound,
unless one of the four already-frozen failure statuses occurs earlier.

The accepted B06 count identities independently reconstruct the values:

- tuning `BASE_FORWARD = 8192 = 8 * 1024`;
- tuning `DATA_ADAPTER_RECORD = 131072 = 8 * 1024 * 16`;
- final `BASE_FORWARD = 1048576 = 256 * 4096`; and
- final `DATA_ADAPTER_RECORD = 16777216 = 256 * 4096 * 16`.

Accordingly, each frozen external-grid tuning evaluation has a separate exact
sub-ceiling of 1024 completed optimizer updates under F147 and is never an
eligible production checkpoint. F143 remains the maximum final-training
horizon. These fixed tuning evaluations do not use validation early stopping:
they all consume the same predeclared 1024-update candidate-evaluation budget,
and failed or aborted evaluations are charged.

## 7. F144 exact validation and certificate semantics

F144 is `F105_COMPLETE_F134_BINARY64_EXACT_CHECKPOINT_RULE_V1` and binds:

- metric `TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1`;
- production projection `F105_CKS_BINARY64_PROJECTION_V1`;
- direction `LOWER_IS_BETTER`;
- exactly 64 conditional draws per group;
- the complete F134 validation roster of exactly 128 natural groups;
- validation at every 256 completed optimizer updates and at the terminal
  F143 bound, yielding steps 256, 512, ..., 4096;
- the exact arithmetic mean described under F141;
- exact canonical-binary64-hex equality with no tolerance;
- F146 only after the future complete tied-best roster is certified; and
- no test-data use.

The F105 unbiased score projection has the accepted formal binary64 interval
`[-2,1]`. Negative values are valid. The production evaluator permits a
512-binary64-epsilon boundary tolerance only while projecting the formal score,
refuses values outside that enlarged boundary, and clamps an admitted boundary
value to `-2` or `1`. The F144 helper accepts only the resulting canonical
finite factory value in `[-2,1]`; it does not add another tolerance. Negative
zero remains distinct from positive zero because equality is exact factory hex
identity.

Each future group-score row must bind and reproduce the exact F105 factory
integrity digest over metric ID, projection ID, domain, draw count, formal-score
digest, score hex, direction, and symbolic-work count. A second F144 digest
binds that factory digest to the method/domain executable-configuration digest,
selection unit, checkpoint content, group ID, and ordinal.

The complete-roster certificate subject then binds:

- the selection unit;
- method, domain, and exact executable configuration;
- checkpoint content;
- the F144 semantics digest;
- the complete F134 roster digest and count; and
- all 128 ordered bound group-score integrity digests.

The pure helper can recompute those relations and the exact mean, but it
returns `production_history_authenticated=false`. A future B12 runner must
authenticate the exact factory record type, checkpoint bytes, immutable
roster, and production history before a checkpoint is actually eligible.
The current package fabricates none of them.

The exact F144 semantics digest is
`040db767c5bae9879ca5f006095dace2c43d4a2640af19839994465cff2011d2`.

## 8. F147 exact per-method/domain tuning limits

F147 is `B06_GRID_OR_SINGLETON_MAXIMUM_TRIALS_V1`. It has exactly 22 ordered
method/domain rows. The two external B06 baselines retain their exact
eight-member grids and maximum eight trials. Every other B06 row is already a
single frozen configuration and receives maximum one candidate evaluation.
Every row remains under B06's global ceiling of eight; unused capacity cannot
be transferred or topped up.

Selection uses training and validation data only, uses F144 lower-is-better,
charges failed and aborted trials, permits no test access, and uses exactly
1024 completed optimizer updates per candidate evaluation.

| Method/config identity | Domain | B06 config SHA-256 | Kind | Max trials |
|---|---|---|---|---:|
| `B06-CLOSEST-VARIABLE-CARDINALITY-POINT-OR-EDIT-GENERATOR-ONLINE-RETAIL-II-V1` | `online-retail-ii` | `38e51c2df150939cb375877b30f0c049f8c2ad1cabf6c69996e6961e2515eeca` | literature | 1 |
| `B06-CLOSEST-VARIABLE-CARDINALITY-POINT-OR-EDIT-GENERATOR-PHYSIONET-CHALLENGE-2012-V1` | `physionet-challenge-2012` | `a5d626a0e9f25d203cacf5790a9396185e8849a5d9f58fdae61521298394e2a8` | literature | 1 |
| `B06-DEFT-STYLE-GENERALIZED-H-FROZEN-BASE-CORRECTION-ONLINE-RETAIL-II-V1` | `online-retail-ii` | `96550380cdd9161cb64b8d727fd2896c3dde7e0c40869c52457e3f654bc7b683` | literature | 1 |
| `B06-DEFT-STYLE-GENERALIZED-H-FROZEN-BASE-CORRECTION-PHYSIONET-CHALLENGE-2012-V1` | `physionet-challenge-2012` | `1d485e0372b70c3e020d2af464b782d20dc8c050d919eece0ab8260fbacb2300` | literature | 1 |
| `B06-NGDB-STYLE-AUXILIARY-GUIDE-PLUS-CORRECTION-ONLINE-RETAIL-II-V1` | `online-retail-ii` | `680bd6c50aa481c0232a00dfe65cac9949432e07e79bb245c01cd7355b0434bd` | literature | 1 |
| `B06-NGDB-STYLE-AUXILIARY-GUIDE-PLUS-CORRECTION-PHYSIONET-CHALLENGE-2012-V1` | `physionet-challenge-2012` | `4148c1e6f03781155eddc5ebe8446dbefce7c2de580a7914efc8b0a3ddca7586` | literature | 1 |
| `B06-TASK-COMPATIBLE-SAME-BASE-SMC-OR-FEYNMAN-KAC-ONLINE-RETAIL-II-V1` | `online-retail-ii` | `94b3bad18048f96a1b99f03012c116da3e550df06548a00d6cecf17c4367dad6` | literature | 1 |
| `B06-TASK-COMPATIBLE-SAME-BASE-SMC-OR-FEYNMAN-KAC-PHYSIONET-CHALLENGE-2012-V1` | `physionet-challenge-2012` | `57bbcb95f58b55d1154470d829daccd966d8ecc1b11a0c9368aec7af309a93c6` | literature | 1 |
| `CSDI-PHYSIONET-EVENT-MULTISET-ADAPTER-V1` | `physionet-challenge-2012` | `72fa143ace5a24e5338b89de37e2df1980174f10c1254f708dc238611c327046` | external | 8 |
| `EDITPP-RETAIL-STRUCTURED-MARK-ADAPTER-V1` | `online-retail-ii` | `64cdfe9a4f985ba069874a4da3178595856b6dc97bfb29ffa575b48bd805d7ee` | external | 8 |
| `analytic-guide-only-residual-removed` | `online-retail-ii` | `37d5178c836ced493dec1fe49b08ab042e738c5c24edc5867830528154b51ae4` | control | 1 |
| `analytic-guide-only-residual-removed` | `physionet-challenge-2012` | `37d5178c836ced493dec1fe49b08ab042e738c5c24edc5867830528154b51ae4` | control | 1 |
| `association-aware-guide-plus-residual` | `online-retail-ii` | `c44af50b915d024cb6019ee82a2998410afd3401fdb84c5313a84bc98fa543b1` | primary | 1 |
| `association-aware-guide-plus-residual` | `physionet-challenge-2012` | `c44af50b915d024cb6019ee82a2998410afd3401fdb84c5313a84bc98fa543b1` | primary | 1 |
| `association-destroyed-or-factorized-eventwise` | `online-retail-ii` | `a2f91e01e1bdc6854fef6a045df802eaf4a5e60ef124c4303b0694d40ed36008` | control | 1 |
| `association-destroyed-or-factorized-eventwise` | `physionet-challenge-2012` | `a2f91e01e1bdc6854fef6a045df802eaf4a5e60ef124c4303b0694d40ed36008` | control | 1 |
| `direct-or-residual-only-analytic-guide-removed` | `online-retail-ii` | `e175d468fb0df523c9adb2f6aa2e6f4b843b872e54234f63a1f41465f8bef212` | control | 1 |
| `direct-or-residual-only-analytic-guide-removed` | `physionet-challenge-2012` | `e175d468fb0df523c9adb2f6aa2e6f4b843b872e54234f63a1f41465f8bef212` | control | 1 |
| `unconditional-base-sanity-reference` | `online-retail-ii` | `7ecfb6dd842a781d70ac147e374a501f819c8f61cd20f38442526079fb607032` | control | 1 |
| `unconditional-base-sanity-reference` | `physionet-challenge-2012` | `7ecfb6dd842a781d70ac147e374a501f819c8f61cd20f38442526079fb607032` | control | 1 |
| `unified-direct-conditioner` | `online-retail-ii` | `f5c87a6c66defe9e1e8bb12e9578bc9317892af06dce0b88a5b1b81933b742a5` | primary | 1 |
| `unified-direct-conditioner` | `physionet-challenge-2012` | `f5c87a6c66defe9e1e8bb12e9578bc9317892af06dce0b88a5b1b81933b742a5` | primary | 1 |

## 9. B12 integration boundary

The source emits exactly 22 executable configuration rows. Each row binds:

- exact current B06 method, domain, kind, and configuration SHA-256;
- optimizer, schedule, precision, and batch-contract identities;
- exact F143 and F144 semantic identities;
- exact learning-rate candidate roster;
- exact tuning trial and update ceilings; and
- a domain-separated executable-configuration digest.

These are executable **configuration** bytes, not executable adapters or a
training runner. A future B12 successor must bind a separate nonzero adapter/
implementation-source digest and demonstrate that the implementation consumes
the exact row without a shadow default. It must also authenticate checkpoint
and F144 complete-roster receipts, the paired intent/outcome ledger, and an
independent recomputation. Upon independent acceptance, the package would
discharge only the training-plan residual; it cannot discharge the other B12
residuals.

The current B12 evidence-contract artifact contains an older hardcoded
literature-family alias whose eight identity/configuration rows do not match
the accepted B06 registry. This package deliberately does not copy that alias.
It derives all 22 rows from B06, making it suitable for a corrected B12
successor without treating the older alias as evidence.

## 10. Exact count and timetable delta

The live registered baseline is:

- PRE: 30 open / 136 closed;
- POST: 1 open / 5 closed;
- total: 31 open / 141 closed;
- method/runtime/compute: 17 open / 48 closed;
- blockers: 7 open / 5 closed;
- marked timetable tasks: 58 checked / 105 open / 163 total; and
- Gate A: 5/8.

Independent all-or-nothing acceptance permits only:

- PRE: 23 open / 143 closed;
- POST: unchanged at 1 open / 5 closed;
- total: 24 open / 148 closed;
- method/runtime/compute: 10 open / 55 closed;
- blockers unchanged at 7 open / 5 closed;
- marked timetable tasks: 59 checked / 104 open / 163 total; and
- Gate A unchanged at 5/8.

The one timetable change is the existing Solo-Block-7 training/checkpoint task.
B08, B12, Formal Tests 28--30, every result slot, and every execution,
capacity, data, governance, claim, release, and submission state remain
unchanged.

## 11. Package, validation, and nonclaims

The exact candidate package contains five new paths:

1. `PROJECT_F139_F144_F147_TRAINING_CHECKPOINT_PLAN_FREEZE.md`;
2. `src/heterodiff/experiments/two_domain_training_checkpoint_plan.py`;
3. `research/fixtures/manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.json`;
4. `research/diagnostics/manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.py`; and
5. `tests/unit/test_manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.py`.

The source performs no filesystem, network, connector, subprocess, entropy,
randomness, data, optimizer, training, checkpoint-write, F105 evaluation,
runtime, capacity, result, or tracker operation. The future-receipt helper
validates supplied structural bytes only and expressly does not authenticate
production history.

The machine record must be canonical duplicate-free ASCII JSON with a semantic
self-digest, package byte bindings, exact predecessor bindings, exact seven-
field projection, exact counts, exact 22-row roster, and explicit nonclaims.
The read-only validator must verify bytes before compiling the captured source,
reconstruct B06 identities directly, validate F105/F134/F145/F146/F148
semantics, reject the obsolete B12 literature alias as an authority, and
refuse coherent false closure, count, runtime, capacity, or science mutations.

No source under `sources/`, tracker, ledger, predecessor, runtime, data,
checkpoint, or result file is edited by this package. Self-validation is not
independent acceptance.

## 12. Prospective registration wording

Only after a separate independent review accepts the exact five-file package
may an authorized tracker/ledger integration use this bounded wording:

> Close all-or-nothing exactly F139--F144 and F147 through
> `F139_F144_F147_TRAINING_CHECKPOINT_PLAN_FROZEN_PREOUTCOME_V1`. The accepted
> values are the exact AdamW optimizer, constant predeclared-candidate learning-
> rate schedule, binary32-training/binary64-F105-validation precision contract,
> 22-row B06-derived exact-16 domain-local no-shuffle batch construction, exact
> F143 integer bound 4096 in completed optimizer updates, exact complete-F134-
> roster F105 validation/certificate semantics at every 256 updates plus the
> terminal bound, and exact B06-grid-or-singleton per-method/domain tuning caps.
> PRE moves from 30 open / 136 closed to 23 open / 143 closed; POST remains
> 1 open / 5 closed; total fields move from 31 open / 141 closed to 24 open /
> 148 closed; method/runtime/compute moves from 17/48 to 10/55. Mark the existing
> “Freeze checkpoint-selection and training rules using training/validation
> data only” item complete, moving the marked-task view from 58/105/163 to
> 59/104/163. Blockers remain 7/5, Gate A remains 5/8, and B08/B12 and Formal
> Tests 28--30 remain open or pending. No adapter/runtime/checkpoint/capacity,
> data access, entropy, training, result, science, claim, release, or submission
> is created.

This paragraph is evidence-ready wording only. It does not itself close a
field or task, edit the tracker or ledger, authenticate a future receipt, or
authorize execution.
