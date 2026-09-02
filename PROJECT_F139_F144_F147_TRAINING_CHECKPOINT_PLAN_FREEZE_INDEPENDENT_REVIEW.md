# Independent review: F139--F144/F147 training/checkpoint plan freeze

**Review date:** 2026-09-01  
**Decision:** `GO_F139_F144_F147_ALL_OR_NOTHING_FIELD_AND_TASK_REGISTRATION`  
**Findings:** P0 = 0; P1 = 0; P2 = 0  
**Accepted control predicate:** `F139_F144_F147_TRAINING_CHECKPOINT_PLAN_FROZEN_PREOUTCOME_V1`  
**Boundary:** independent local exact-byte review; no data, entropy, network,
training, inference, checkpoint, runtime, capacity, result, science, claim,
release, submission, blocker, Formal-Test, or B12 acceptance

The review was restarted after final sealing and accepts only the five exact
bytes below. It permits a subsequent authorized tracker/ledger integration to
close the seven fields and the one existing timetable task exactly as stated
under **Accepted registration delta**. This review itself edits neither
project-control artifact.

## Exact accepted bytes

| Artifact | Bytes | Raw SHA-256 |
|---|---:|---|
| `PROJECT_F139_F144_F147_TRAINING_CHECKPOINT_PLAN_FREEZE.md` | 19,707 | `ac318d432b0634b96547ffd0773f93c3ad0f4978dc9db287b6b7f13e1cfdf442` |
| `src/heterodiff/experiments/two_domain_training_checkpoint_plan.py` | 33,918 | `9ac7d6e6d93bb0691fde67070dc97b566e716797dd05f82ed053c8dc77e2fbcf` |
| `research/fixtures/manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.json` | 82,095 | `ca43c2efa1b378e8ad2989cc258698a3fee9810b721b5e32294906b7ca221e1e` |
| `research/diagnostics/manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.py` | 59,448 | `edbc30484f1655fe38746b36dc68e227ef34536fab786e8687e0d02db812b62f` |
| `tests/unit/test_manuscript_v3_f139_f144_f147_training_checkpoint_plan_freeze_v1.py` | 19,373 | `433a2b8e746445371fc8bb50398c99040d0866d6f67b181e0ef4d749cb8b9449` |

All five were reopened after sealing through stable no-follow descriptors and
were regular `0644` single-link files with terminal LF. Any byte change
invalidates this review.

The machine record is duplicate-key-free canonical ASCII JSON with exactly one
terminal LF. Its independently reproduced semantic self-digest is
`0a0cc0ace3489f35dd9a5e4454c5ae467d64d36a514ea910b71a466c1f89fd56`.
The independently reproduced plan-semantics SHA-256 is
`dd1c74d655f4cfeb4a895c11eb09a9e3ef41c328ce432ad782bce204e59585db`,
and the F144-semantics SHA-256 is
`040db767c5bae9879ca5f006095dace2c43d4a2640af19839994465cff2011d2`.

## Verification results

- Final hash-first validator at the absolute project root: PASS with
  `PASS_F139_F144_F147_SEVEN_FIELDS_ONLY`.
- The exact 31-file package/predecessor closure was copied to a fresh canonical
  `/private/tmp` root; the copied validator, invoked by absolute path from an
  unrelated working directory, returned the same PASS token.
- Focused final-byte suite: 45/45 passed.
- Relevant B06, F105, F134/R64, F145, F146, F148, and accepted B12 predecessor
  suites: 733/733 passed.
- Combined final-byte focused and predecessor suites: 778/778 passed.
- Independent machine reconstruction, direct ledger/timetable recount,
  B06-roster reconstruction, exact arithmetic, negative-score, endpoint,
  cadence, and compatibility replay: PASS.
- Duplicate/NaN JSON, path traversal, forbidden-effect source, partial-field
  mutation, and fully re-signed false science/count/B12/task mutations: PASS
  fail-closed.

The source AST has no filesystem, network, connector, subprocess, entropy,
randomness, data-loader, optimizer execution, training, checkpoint-write,
metric-execution, runtime, capacity, result, or project-control route. Its
structural F144 helper explicitly returns
`production_history_authenticated=false`.

## Exact all-or-nothing field acceptance

The accepted roster contains exactly seven unique field/pointer pairs in this
order and no other field:

| Field | Pointer | Accepted value |
|---|---|---|
| F139 | `/training_and_checkpoint_plan/optimizer` | `TORCH_ADAMW_EXACT_RATIONAL_SINGLE_GROUP_V1` |
| F140 | `/training_and_checkpoint_plan/learning_rate_schedule` | `CONSTANT_CANDIDATE_BASE_RATE_NO_WARMUP_V1` |
| F141 | `/training_and_checkpoint_plan/precision` | `CPU_BINARY32_TRAIN_BINARY64_F105_VALIDATION_V1` |
| F142 | `/training_and_checkpoint_plan/batch_construction` | `DOMAIN_LOCAL_CANONICAL_CYCLIC_EXACT16_NO_SHUFFLE_V1` |
| F143 | `/training_and_checkpoint_plan/maximum_epochs_or_steps` | exact integer `4096` in `COMPLETED_OPTIMIZER_UPDATES` |
| F144 | `/training_and_checkpoint_plan/validation_metric` | `F105_COMPLETE_F134_BINARY64_EXACT_CHECKPOINT_RULE_V1` |
| F147 | `/training_and_checkpoint_plan/maximum_tuning_trials_per_method` | `B06_GRID_OR_SINGLETON_MAXIMUM_TRIALS_V1` |

Each closure remains marked
`PROPOSED_CLOSED_ALL_OR_NOTHING_PENDING_INDEPENDENT_REVIEW` inside the sealed
candidate because the candidate correctly predates this review. This review
accepts the seven together. No strict subset is authorized for registration.

F139 fixes one all-trainable-parameter AdamW group, exact rational betas
`9/10` and `999/1000`, epsilon `1/100000000`, zero weight decay, gradient
accumulation one, and all named boolean options false. F140 fixes a constant
unit multiplier, zero warmup, no adaptive change, CSDI's exact B06 candidate
rates `1/2000` and `1/1000`, and singleton `1/1000` everywhere else. F141
separates binary32 training/checkpoint state from exact-ratio aggregation of
factory-bound binary64 F105 validation values followed by one binary64 round;
autocast, mixed precision, and TF32 are forbidden.

F142 supplies exactly 22 method/domain-local contracts, each with 16 admitted
logical records per update, canonical cyclic record addressing, no shuffle,
no cross-domain batch, no role/seed/trial mixing, and no test record. Every
row carries its exact B06 configuration hash and a separately recomputed batch
contract digest.

## B06 roster and count arithmetic

The review derived the roster directly from the accepted
`FROZEN_REGISTRY`, without using the obsolete B12 adapter alias. The result is
exactly 22 unique method/domain identities: four primary, eight control, eight
domain-specific literature implementations, and two external baselines. All
configuration hashes independently recompute from their B06 configurations.

The accepted older B12 alias differs in exactly eight literature-family rows.
Those rows were refused as authority. The accepted package imports no B12
roster and uses B12 only for its stable residual/F144 semantics; it binds no
unaccepted B12 successor bytes.

The B06 event ceilings independently give:

- tuning `BASE_FORWARD = 8 * 1024 = 8192`;
- tuning `DATA_ADAPTER_RECORD = 8 * 1024 * 16 = 131072`;
- final `BASE_FORWARD = 256 * 4096 = 1048576`; and
- final `DATA_ADAPTER_RECORD = 256 * 4096 * 16 = 16777216`.

Thus F143 is exactly 4096 completed optimizer updates for final training.
F147 gives each of the two exact B06 external grids eight trials, each with
1024 completed updates, and gives the other 20 frozen configurations one
trial. Every row remains under the B06 global ceiling eight; failed/aborted
trials are charged and no unused transfer or post-result top-up is permitted.

## F144 arithmetic, interval, and neighboring-field compatibility

F144 binds metric `TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1`, projection
`F105_CKS_BINARY64_PROJECTION_V1`, lower-is-better direction, exactly 128 F134
groups, exactly 64 F136 draws per group, exact arithmetic-mean aggregation,
and validation at the 16 steps `256, 512, ..., 4096`. Every group row,
complete-roster digest, certificate subject, checkpoint content, selection
unit, executable configuration, method, domain, and ordinal is bound.

Independent structural receipts admitted the exact F105 interval endpoints
`-2` and `1`, intermediate negative values, and an alternating `-1, 1/2`
roster whose exact mean is `-1/4`. The immediate binary64 values outside both
endpoints, nonfinite values, missing/duplicate/tampered groups, wrong cadence,
and wrong method/configuration bindings refused. Exact hexadecimal equality
distinguishes positive and negative zero.

The package preserves rather than re-closes or modifies:

- F145 = `DISABLED_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY`;
- F146 = `F146_EARLIEST_STEP_TIED_BEST_CANONICAL_CHECKPOINT_RULE_V1`, invoked
  only after a complete tied-best F144-certified roster exists; and
- F148 = `NEVER_TRUE_NO_INFRASTRUCTURE_RERUN`.

The exact F143 terminal bound now supplies the final value required by the
already accepted F145 policy. F144 supplies the frozen representation,
direction, equality, cadence, and certificate semantics owned by the already
accepted F146 rule. Neither neighboring field is otherwise changed.

## Accepted registration delta

The live ledger was independently recounted before acceptance: PRE is
30 open / 136 closed, POST is 1 open / 5 closed, total is 31 open / 141
closed, and method/runtime/compute is 17 open / 48 closed. The seven target
fields are each uniquely OPEN. The timetable contains exactly one open
existing task named **“Freeze checkpoint-selection and training rules using
training/validation data only.”** Its live marked-task view is
58 checked / 105 open / 163 total.

An authorized integration may now apply only this atomic transition:

- PRE: `30/136 -> 23/143` open/closed;
- POST: unchanged at `1/5` open/closed;
- total: `31/141 -> 24/148` open/closed;
- method/runtime/compute: `17/48 -> 10/55` open/closed;
- mark that one existing timetable task complete:
  `58/105/163 -> 59/104/163` checked/open/total;
- blockers remain `7 open / 5 closed`; and
- Gate A remains `5/8`.

No new timetable task is created. B08 and B12 remain open; Formal Tests 28 and
29 remain OPEN and Formal Test 30 remains PENDING. No result slot or scientific
claim changes.

## Residual boundary

This acceptance freezes a training/checkpoint **plan**, not its execution.
The following remain open or absent:

- real method, control, literature, CSDI, and EditPP adapter implementations;
- the corrected integrated B12 runner, capsule, immutable paired ledger, and
  independent recomputation paths;
- actual trained checkpoints and authenticated F144 complete-roster
  production-history receipts;
- real data adapters, snapshots, splits, escrow, licenses, privacy, and
  external acceptances;
- B08 hardware, runtime identity, environment, calibration, ceilings,
  allocation, durability, and capacity evidence;
- domain-scale execution and no-truncation qualification;
- Formal Tests 28--30 production receipts, all results, scientific analysis,
  claims, release, and submission; and
- final B12 integration and closure.

