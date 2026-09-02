# F145 validation early-stopping freeze

**Reported:** 2026-09-01  
**State:** `F145_VALIDATION_EARLY_STOPPING_DISABLED_F143_BOUND_ONLY_PREOUTCOME`  
**Global project state:** `DRAFT_NOT_EXECUTABLE`  
**Package kind:** `ADDITIVE_PREOUTCOME_EXACT_F145_FIELD_CLOSURE`  
**Control predicate:** `F145_VALIDATION_EARLY_STOPPING_DISABLED_F143_BOUND_ONLY_PREOUTCOME`

## 1. Exact bounded decision

This additive package closes exactly one pre-execution field:

- `F145`, `/training_and_checkpoint_plan/early_stopping_patience`.

The entire and sole F145 field value is the exact built-in string:

```text
DISABLED_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY
```

It is governed by policy identifier
`F145_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY_V1`. The sentinel is not
`null`, zero, a Boolean, an empty string, infinity, a numeric patience value,
or an alias for one. Case changes, leading or trailing whitespace, string
subclasses, alternative spellings, and structured replacements are invalid.

The sentinel freezes a neutral no-validation-early-stopping rule. It creates no
patience counter and no validation-driven authority to stop, extend, resume,
restart, retry, top up, or otherwise change training duration. Training may
reach `COMPLETE` only at a separately final-frozen, caller-certified positive
exact F143 horizon and its exact unit. This package does not select that F143
value or unit and does not make the project executable.

The mandatory policy-refusal disposition is
`F145_POLICY_REFUSAL_NO_EXECUTABLE_TRAINING_PLAN`. A refusal produces no
executable training plan and is not a scheduled-run terminal status.

## 2. F143-bound parameterization and field separability

F143 remains open at
`/training_and_checkpoint_plan/maximum_epochs_or_steps`. A future accepted
F143 value must be a positive exact built-in integer, not a Boolean or integer
subclass, and its exact unit must be one of:

- `COMPLETED_OPTIMIZER_UPDATES`; or
- `COMPLETED_EPOCHS`.

F145 owns only the absence of validation early stopping. F143 owns the future
maximum training horizon and its unit. This is the same kind of separability
already used by the accepted F060 parameterized temporal-rule closure: an exact
policy can be complete while the separately owned parameter remains open. The
F060 artifact is an analogy, not a new F145 input or mutable predecessor.

`F143_BOUND_ONLY` is therefore conditional. It supplies no F143 value, unit,
checkpoint cadence, validation cadence, batch size, optimizer schedule,
capacity, wall-clock duration, compute allocation, or runtime estimate.
Until F143 and every other prerequisite gate are separately frozen and
accepted, there is no executable training plan.

## 3. Exact scheduled-run boundary

The existing scheduled-run terminal-status roster remains exactly:

```text
COMPLETE
ALGORITHMIC_FAILURE
NONFINITE
OOM_OR_TIMEOUT
INFRA_ABORT
```

Let `B` be the separately certified positive F143 bound and `c` the exact
nonnegative number of completed units measured in the same certified unit.
The pure checker applies this exact truth table:

| Event | Exact condition | Required action |
|---|---|---|
| `PROGRESS` | `0 <= c < B` and status is `null` | `CONTINUE_TO_F143_BOUND` |
| `TERMINAL_STATUS` / `COMPLETE` | `c = B` | `TERMINAL_COMPLETE_AT_EXACT_F143_BOUND` |
| `TERMINAL_STATUS` / one of the four failure statuses | `0 <= c <= B` | `TERMINAL_EXISTING_FAILURE_STATUS` |

`COMPLETE` before the bound, progress reported at the bound without
`COMPLETE`, any event beyond the bound, an unknown status, a status on a
progress event, or a unit mismatch refuses. Earlier termination is possible
only through `ALGORITHMIC_FAILURE`, `NONFINITE`, `OOM_OR_TIMEOUT`, or
`INFRA_ABORT`; it is never validation-driven early stopping.

F148 remains the separately accepted
`NEVER_TRUE_NO_INFRASTRUCTURE_RERUN` predicate. Consequently an
`INFRA_ABORT` is terminal and gives no authority for rerun, retry,
replacement, resume, restart, threshold change, seed change, configuration
change, or route change.

## 4. Exact F143-bound digest and checker schema

The caller must provide a structural certificate stating that the referenced
F143 bound is final and frozen. The package does not authenticate that
statement or production history. The exact F143-bound digest is:

```text
SHA256(
  ASCII("heterodiff-f145-certified-f143-bound-v1\0") ||
  canonical_ASCII_JSON({
    "f143_bound_unit": "<exact allowed unit>",
    "f143_bound_value": <positive exact built-in integer>
  })
)
```

Canonical JSON uses `ensure_ascii=true`, `allow_nan=false`,
lexicographically sorted keys, separators `,` and `:`, and no terminal line
feed inside the digest preimage. The literal domain includes the shown NUL
byte. Integers use the package-local total base-`10^9` chunk encoder: the
leading nonzero chunk is unpadded and later chunks have exactly nine digits.
Thus every exact integer has the ordinary base-10 JSON spelling independent of
the interpreter integer-to-string digit guard.

The checker top-level key order is exactly:

```text
certificate, observation, policy_value
```

The certificate key order is exactly:

```text
f143_bound_final_and_frozen_certified,
f143_bound_sha256,
f143_bound_unit,
f143_bound_value,
policy_id,
production_history_authenticated_by_helper,
training_run_unit_sha256
```

The observation key order is exactly:

```text
completed_units, event_kind, scheduled_run_status, training_run_unit_sha256
```

The success-output key order is exactly:

```text
action,
caller_certifications_structurally_accepted,
completed_units,
f143_bound_sha256,
f143_bound_unit,
f143_bound_value,
policy_id,
policy_value,
production_history_authenticated,
scheduled_run_status,
training_run_unit_sha256,
validation_early_stopping_used
```

The refusal-output key order is exactly:

```text
disposition, executable_training_plan_produced, policy_id, reason_code
```

Both the certificate and success output state that production history is not
authenticated by the helper. The pure, stateless checker cannot prove that a future F143 record is truly final, authenticate a production run, observe
replay, or enforce integration custody. Those duties remain open.

## 5. No patience or shadow early-stopping mechanism

This package creates none of the following:

- a patience or plateau counter;
- a validation monitor or monitor direction;
- a minimum-delta or equality/tolerance rule;
- a grace period or warmup;
- a validation-check cadence;
- a reset, smoothing, or best-so-far rule;
- a validation stop signal;
- a checkpoint-selection proxy;
- adaptive horizon extension, extra epochs or optimizer updates, or top-up;
- retry, resume, restart, rerun, replacement, or favorable stopping; or
- a shadow field under another name.

Unknown, missing, reordered, or extra input keys fail closed. Raw validation
values, F144 metric semantics, checkpoint identities, F146 tie rosters,
patience-like fields, monitoring fields, timestamps, wall-clock values,
runtime estimates, and results are outside the checker schema and are refused.

The F146 checkpoint-tie rule remains a distinct accepted field. A checkpoint choice under F146 may not shorten, lengthen, restart, resume, or otherwise
change the F143 training horizon. F144 remains responsible for validation
metric semantics and does not provide a stopping signal under this F145 policy.

## 6. Development-evidence and nonexecution boundary

The accepted A1 development-checkpoint V2 evidence remains
`FINAL_UPDATE_ONLY` with `NOT_APPLICABLE_NO_SELECTION`, no validation
checkpoint selection, and `early_stopping=false`. The D1 diagnostic did not
perform training or checkpoint selection and supplies no F143 bound, duration,
patience, validation-stop signal, or production evidence.

Those artifacts are immutable exclusion witnesses only. This package does not
reinterpret their duration, final update, checkpoint, metric, or outcome as a
production F143/F145 choice.

The pure checker has no filesystem writer, RNG, entropy, network, connector,
subprocess, environment-build, data, training, optimizer, checkpoint,
runtime-capture, production, scientific-execution, result, claim, release, or
submission route. All checker inputs are synthetic qualification values.

## 7. Exact predecessor lineage

The machine record must fixed-bind 28 predecessor files:

| Group | Files |
|---|---:|
| Execution preregistration V1 | 2 |
| Pre-execution closure V2 | 2 |
| Anti-drift policy | 1 |
| A1 development-checkpoint V2 exclusion | 2 |
| D1 diagnostic exclusion | 2 |
| Accepted B11 package plus review | 5 |
| Accepted F137 package plus review | 5 |
| Gate-A local F148 package | 4 |
| Final accepted F146 package plus review | 5 |
| **Total** | **28** |

The first seven groups are the 19-file base lineage already verified by F146.
Adding the four-file Gate-A package yields the 23 pre-F146 files verified in
the no-write readiness audit. The final five-file F146 group establishes the
immediate 143/23 PRE, 3/3 POST, and 146/26 total baseline and the existing
five-status roster.

The Gate-A machine is parsed directly to require F148 exactly
`NEVER_TRUE_NO_INFRASTRUCTURE_RERUN`. The F146 machine and review are parsed
directly to require sole F146 closure, the exact baseline counts, B12
nonclosure, the five-status roster, and `INDEPENDENT_REVIEW_GO`.

The tracker and evidence ledger are mutable registration surfaces and are not
package predecessors. No tracker, ledger, predecessor, production/training source, data, runtime, or operational file is edited by this package.

## 8. Exact count delta and preserved nonclosures

The independently registered F146 baseline is:

- PRE: 143 open / 23 closed;
- POST: 3 open / 3 closed;
- total: 146 open / 26 closed; and
- method/runtime/compute: 63 open / 2 closed.

The sole permitted F145 delta is:

- PRE: 142 open / 24 closed;
- POST: unchanged at 3 open / 3 closed;
- total: 145 open / 27 closed; and
- method/runtime/compute: 62 open / 3 closed.

Theory/statistics remains 34/20, data/governance/reproduction remains 48/4,
and final sealed freeze remains 1/0.

F139--F144 and F147 remain open, including the F143 horizon and F144 validation
semantics. F146 and F148 retain their prior accepted closures. F150--F162,
F164, F165, and F169 remain open. B07, B12, and all 12 blockers remain open.
B12 remains open.
Formal Tests 28 and 29 remain `OPEN`; Formal Test 30 remains `PENDING`; all
four result slots remain empty; and the project remains
`DRAFT_NOT_EXECUTABLE`.

This is the second consecutive B12 package; any third consecutive B12 package requires explicit scope review before construction. This statement creates no
new blocker or tracker item and does not close B12.

## 9. Qualification and acceptance boundary

The four intended files are:

- `PROJECT_F145_VALIDATION_EARLY_STOPPING_FREEZE.md`;
- `research/fixtures/manuscript_v3_f145_validation_early_stopping_freeze_v1.json`;
- `research/diagnostics/manuscript_v3_f145_validation_early_stopping_freeze_v1.py`;
  and
- `tests/unit/test_manuscript_v3_f145_validation_early_stopping_freeze_v1.py`.

Machine construction occurs only after the human, validator, and hostile-test
bytes are stable. The validator requires canonical duplicate-free ASCII JSON,
semantic self-digest, exact package and predecessor byte bindings,
componentwise descriptor-held no-follow reads, regular single-link exact
`0644` files, exact terminal-line-feed dispositions, exact semantic
projections, and the sole field/count/workstream delta.

Hostile qualification covers exact sentinel and string type; whitespace, case,
`null`, zero, Boolean, infinity, subclass, and structured sentinel
substitutions; missing, false, or replay-authentication certificates; F143
bound type, positivity, unit, domain, digest, and training-run identity;
two bounds and both units; full boundary truth table; every scheduled status;
unknown and sixth statuses; all forbidden shadow fields; F146 and F148
separation; canonical/duplicate JSON; all 28 predecessor bindings and semantic
drift; fully re-signed false closures and nonclaims; permission, hard-link,
symlink, inode-swap, ancestor-swap, and mid-read races; and root plus
`/private/tmp` execution. All hostile writes use disposable copies.

Self-validation is not independent acceptance. No timetable or evidence-ledger
registration may occur until a separate read-only reviewer accepts the exact
four-file package.

## 10. Prospective registration wording

Only after independent acceptance may a separately authorized reconciliation
use this exact bounded wording:

> Upon independent acceptance, register only this delta: F145 (`/training_and_checkpoint_plan/early_stopping_patience`) is closed to the exact sentinel `DISABLED_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY` under policy `F145_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY_V1`. There is no validation early stopping and no patience counter, monitor, direction, minimum delta, warmup, cadence, reset, smoothing, best-so-far selection, adaptive extension, top-up, resume, restart, or retry. COMPLETE is admissible only at a separately final-frozen, caller-certified positive exact F143 completed-update or epoch bound with its exact unit. Earlier termination is limited to the existing four failure statuses; F148 forbids infrastructure rerun, and F146 checkpoint choice cannot change duration. Effective PRE moves from 143 open / 23 closed to 142 open / 24 closed; POST remains 3 open / 3 closed; total moves from 146 open / 26 closed to 145 open / 27 closed; method/runtime/compute moves from 63/2 to 62/3. F139--F144, F147, F150--F162, B12, all 12 blockers, Formal Tests, results, runtime, data, science, claims, and submission remain open or absent.

This paragraph is prospective evidence wording only. It does not register a
field, authenticate a future F143 certificate, create an executable plan,
perform training or early stopping, change a checkpoint or duration, edit the
tracker or ledger, or authorize execution.
