# Independent review of the F145 validation early-stopping freeze

**Reviewed:** 2026-09-01  
**Reviewer lane:** `/root/block2_final_redteam`  
**Review state:** `INDEPENDENT_REVIEW_GO`  
**Subject state:** `F145_VALIDATION_EARLY_STOPPING_DISABLED_F143_BOUND_ONLY_PREOUTCOME`  
**Accepted control predicate:** `F145_VALIDATION_EARLY_STOPPING_DISABLED_F143_BOUND_ONLY_PREOUTCOME`  
**Global project state preserved:** `DRAFT_NOT_EXECUTABLE`

## 1. Verdict

`GO` for the exact four-file F145 package identified below.

The final independent review found zero P0, zero P1, and zero P2 defects. The
package closes exactly F145,
`/training_and_checkpoint_plan/early_stopping_patience`, to the exact string
sentinel `DISABLED_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY` under policy
`F145_NO_VALIDATION_EARLY_STOPPING_F143_BOUND_ONLY_V1`.

The accepted count delta is exactly:

- pre-execution changes from 143 open / 23 closed to 142 open / 24 closed;
- post-execution remains 3 open / 3 closed;
- the total changes from 146 open / 26 closed to 145 open / 27 closed; and
- the method/runtime/compute workstream changes from 63 open / 2 closed to
  62 open / 3 closed.

No blocker, compound Solo Block 7 task, Formal Test, result slot, operational
task, implementation gate, runtime state, or scientific state is closed by
this package or this receipt. This receipt is independent acceptance evidence
only. It does not itself edit the project timetable or evidence ledger and
supplies no registration, execution, network, data, entropy, runtime, science,
claim-promotion, release, submission, or publication authority.

## 2. Exact reviewed package

All four files were independently reopened through their canonical project
paths. Each was a regular, single-link exact-`0644` file with one terminal line
feed. Their accepted byte bindings are:

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human freeze | `PROJECT_F145_VALIDATION_EARLY_STOPPING_FREEZE.md` | 14,003 | `ef31cab9d4d8a245d8e88b47590d90a335b31f230a499893629d3a46e9a8eee4` |
| Machine freeze | `research/fixtures/manuscript_v3_f145_validation_early_stopping_freeze_v1.json` | 20,891 | `d2149abb5bab067cd7465f17e1bb8d1515a076834071536e355e15f9bae23a81` |
| Read-only validator and pure policy checker | `research/diagnostics/manuscript_v3_f145_validation_early_stopping_freeze_v1.py` | 59,527 | `7916005b904dec0345d7db18750c869289c8125e01a8d20c02b9f8ff76c478bb` |
| Hostile tests | `tests/unit/test_manuscript_v3_f145_validation_early_stopping_freeze_v1.py` | 39,441 | `c8c796f331224f101d54af8f61c9c8d4f0d26e4478afe70ef8187b385da0bfe0` |

The four reviewed files total 133,862 bytes. The machine file is duplicate-free
canonical ASCII JSON plus one terminal line feed. An independent
implementation, without importing the package validator, recomputed the
schema-domain semantic digest
`a88a2d656d1d6f1af673609ab1127017e44f809d93ecb880bdd4c3f4d4c2f3e7`,
exactly matching the embedded `record_sha256`.

The machine file contains the exact four-path package roster, binds the three
nonmachine files by byte count and raw SHA-256, declares the noncyclic machine
self-binding correctly, and reconstructs exactly one field closure: F145 at
the authoritative JSON pointer. Any byte change to a reviewed package file
invalidates this receipt.

## 3. Predecessor and baseline verification

The review independently reopened all 28 machine-bound predecessor files.
Every byte count and raw SHA-256 matched, every file was regular, single-link,
and exact mode `0644`, and every terminal-line-feed disposition matched its
binding. The exact predecessor groups and counts are:

| Predecessor group | Bound files |
|---|---:|
| Execution preregistration V1 | 2 |
| Pre-execution closure V2 | 2 |
| Anti-drift policy | 1 |
| A1 development-checkpoint V2 exclusion | 2 |
| D1 diagnostic exclusion | 2 |
| Accepted B11 package and independent review | 5 |
| Accepted F137 package and independent review | 5 |
| Gate-A local F148 package | 4 |
| Accepted F146 package and independent review | 5 |
| **Total** | **28** |

Applicable predecessor semantic self-digests were recomputed. The base
preregistration retains null F143, F144, and F145 values, permits validation
early stopping only if separately frozen, and forbids experiment-level
optional stopping. The A1 development checkpoint remains `FINAL_UPDATE_ONLY`
with `NOT_APPLICABLE_NO_SELECTION`, no early stopping, and no validation-
checkpoint selection. The D1 diagnostic selected no checkpoint, performed no
training, and supplies no production F143 or F145 evidence.

The accepted B11 evidence preserves PRE at 145/21 and closes only F168, F170,
and F171 in POST, leaving POST at 3/3 and F164, F165, and F169 open. The
accepted F137 package closes only F137 and establishes PRE 144/22, POST 3/3,
and total 147/25. The accepted F146 package and its exact independent-review
receipt then close only F146 and establish the immediate F145 baseline of PRE
143/23, POST 3/3, total 146/26, and the unchanged five-status roster. The
Gate-A machine separately preserves F148 as
`NEVER_TRUE_NO_INFRASTRUCTURE_RERUN`.

## 4. Exact F145 policy audit

The sole field value is an exact built-in string, not `null`, a Boolean, zero,
infinity, an empty string, a numeric patience value, a string subclass, a case
or whitespace alias, or a structured replacement. It creates no patience or
plateau counter, validation monitor, direction, minimum delta, warmup, grace
period, validation cadence, reset, smoothing, best-so-far rule, validation
stop signal, adaptive extension, top-up, resume, restart, retry, rerun,
replacement, or shadow field.

F143 remains separately open. The pure checker accepts a caller-certified
future positive exact built-in integer bound in exactly one of two units:
`COMPLETED_OPTIMIZER_UPDATES` or `COMPLETED_EPOCHS`. The domain-separated
F143-bound digest is SHA-256 over the literal ASCII domain
`heterodiff-f145-certified-f143-bound-v1` followed by NUL and canonical ASCII
JSON containing the exact bound unit and value. Its package-local base-
`10^9` integer encoder remains total for arbitrarily large exact integers and
independent of the interpreter integer-to-string digit guard.

A changed bound value or unit with a stale digest refuses. A malformed digest,
nonpositive or non-exact bound, unrecognized unit, false final-and-frozen
certificate, changed training-run-unit digest, noncanonical key roster, or
extra input also refuses. Correctly recomputing the digest only establishes
structural consistency: the helper explicitly does not authenticate the
caller's F143-finality statement, production history, replay history, or
integration custody. Its success output reports
`production_history_authenticated=false`; its input must also explicitly state
that production history is not authenticated by the helper.

## 5. Terminal-status, optional-stopping, and field-separation audit

The scheduled-run terminal-status roster remains exactly:

- `COMPLETE`;
- `ALGORITHMIC_FAILURE`;
- `NONFINITE`;
- `OOM_OR_TIMEOUT`; and
- `INFRA_ABORT`.

For a structurally valid caller-supplied F143 bound `B` and completed-unit
count `c`, progress with null status is accepted only for `0 <= c < B`.
`COMPLETE` is accepted only at `c = B`. Each of the four pre-existing failure
statuses may terminate at `0 <= c <= B`. Progress at the bound, completion
before the bound, any overshoot, a status on a progress event, an unknown or
sixth status, and the F145 refusal disposition as a status all refuse.
`F145_POLICY_REFUSAL_NO_EXECUTABLE_TRAINING_PLAN` is not a sixth scheduled-run
terminal status.

The pure checker accepts no validation metric or value and cannot implement
optional or sequential validation stopping. F144 retains ownership of metric,
direction, representation, comparison/equality, tolerance, nonfinite
treatment, eligibility, and future certification. F146 retains ownership of
checkpoint tie selection and cannot shorten, lengthen, restart, resume, or
otherwise change the F143 horizon. F148 remains the no-infrastructure-rerun
predicate, so an `INFRA_ABORT` creates no rerun, retry, replacement, resume,
configuration-change, seed-change, or route-change authority.

## 6. Custody, canonicality, and effect-surface audit

The validator performs canonical relative-path checks and componentwise
no-follow reads through held directory descriptors. It requires every leaf to
be a regular, single-link exact-`0644` file at the before-path,
before-descriptor, after-descriptor, and after-path observations. Its stable
fingerprint includes device, inode, size, modification time, change time, full
mode, and link count. Root, ancestor, descriptor, and final namespace identity
are rechecked, so permission, hard-link, symlink, inode-substitution, ancestor-
replacement, and mid-read races fail closed.

The machine must equal the fully reconstructed expected record and retain its
canonical encoding and semantic self-digest. Hostile tests cover the exact
sentinel and built-in types; both F143 units and multiple bounds; an independent
digest known answer and a 5,001-digit guard-independent bound; digest and
training-run identity mismatch; explicit production-history
nonauthentication and replay; every boundary and scheduled status; unknown and
sixth statuses; all named patience, monitor, validation, F144, F146, retry,
resume, duration, and runtime shadow inputs; exact key order and output schemas;
all 28 predecessor byte bindings and semantic mutations; fully re-signed false
field, count, workstream, B12, F143, F146, F148, implementation, execution, and
nonclosure claims; canonical and duplicate-key JSON; and stable-read path,
mode, link, symlink, leaf-inode, ancestor, and mid-read races. All hostile
writes occur only in disposable test copies.

Direct source inspection found only standard-library hashing, JSON, read-only
filesystem, path, regular-expression, stat, and typing dependencies. The
source contains no writer, RNG or entropy source, network or connector client,
subprocess launcher, project-science import, data reader, training or optimizer
route, checkpoint writer, runtime-capture route, production worker, result or
claim promoter, or submission route. The checker is pure and idempotent; its
synthetic qualification output is not an executable or authenticated training
plan.

## 7. Independent executed qualification

All qualification used Python bytecode writing disabled and pytest's cache
provider disabled.

| Working context | Qualification | Independent result |
|---|---|---|
| Project root | Canonical F145 validator entry point | `PASS`; semantic digest `a88a2d656d1d6f1af673609ab1127017e44f809d93ecb880bdd4c3f4d4c2f3e7` |
| `/private/tmp` current working directory | Canonical F145 validator by absolute path | `PASS`; same semantic digest |
| Project root | F145 focused hostile suite | `211 passed in 1.92s` |
| `/private/tmp` current working directory | F145 focused hostile suite against the canonical absolute package | `211 passed in 1.95s` |
| Project root | Accepted F137, F146, and F145 suites together | `493 passed in 4.01s` |
| `/private/tmp` current working directory | Accepted F137, F146, and F145 suites together | `493 passed in 4.01s` |

The canonical four-file package and all 28 bound predecessor files retained
their exact byte receipts across these independent read-only checks.

## 8. Findings and preserved nonclosures

| Severity | Count | Disposition |
|---|---:|---|
| P0 | 0 | None |
| P1 | 0 | None |
| P2 | 0 | None |

Only F145 is accepted for later registration. The following remain expressly
unclosed, null, absent, unchecked, or unperformed:

- F139 optimizer, F140 learning-rate schedule, F141 precision, F142 batch
  construction, F143 maximum epochs or optimizer steps, F144 validation
  semantics, and F147 maximum tuning trials;
- F150--F162 hardware, environment, resource, reserve, allocation, storage,
  retention, and total-compute fields;
- F164, F165, and F169, while the accepted B11 closures of F168, F170, and F171
  remain unchanged;
- B07, B12, and all 12 blockers;
- the compound Solo Block 7 task, “Freeze checkpoint-selection and training
  rules using training/validation data only,” which remains unchecked and open;
- whole-method implementation, production integration, authenticated F143
  finality and production-history custody, checkpoint cadence, capacity,
  maximum-horizon selection, storage and retention policy, and future F144
  certificate;
- Formal Tests 28 and 29 (`OPEN`) and Formal Test 30 (`PENDING`);
- R1--R4 and all four result slots;
- every actual F143 value and unit, validation value, metric, direction,
  representation, equality or tolerance rule, dataset row, entropy source,
  training run, checkpoint, runtime, result, inference, decision, claim,
  release, submission, and publication approval; and
- network/contact/repository/license/data activity, operational receipts,
  training, early stopping, checkpoint selection, scientific or production
  execution, tracker or evidence-ledger registration, and predecessor mutation.

The accepted A1 development V2 and D1 evidence retain their nonproduction,
nontraining, and nonselection boundaries. The project remains
`DRAFT_NOT_EXECUTABLE`, with all 12 blockers open, zero Formal Tests closed,
and zero result slots filled.

## 9. Independent acceptance boundary

The exact package receives `INDEPENDENT_REVIEW_GO`. A later separately
authorized timetable and evidence-ledger reconciliation may register only F145
and the corresponding 143/23 to 142/24 PRE transition, while preserving POST
at 3/3, changing the total only from 146/26 to 145/27, and changing the
method/runtime/compute category only from 63/2 to 62/3. It must cite the exact
four-file package and this receipt and leave every listed nonclosure unchanged.

This receipt does not itself perform that registration; populate F143, F144,
or any other open field; authenticate F143 finality, production history, or
replay; choose a checkpoint, horizon, unit, validation metric, cadence,
capacity, storage policy, retention policy, data item, seed, or runtime; close
B07, B12, the compound Solo Block 7 task, or any other blocker or task; alter a
Formal Test or result; or authorize any operational or scientific action. Any
byte change to the reviewed four-file package or any of its 28 bound
predecessor files invalidates this receipt and requires a fresh independent
review.
