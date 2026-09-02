# Independent review of the F146 checkpoint tie-rule freeze

**Reviewed:** 2026-09-01  
**Reviewer lane:** `/root/block2_final_redteam`  
**Review state:** `INDEPENDENT_REVIEW_GO`  
**Subject state:** `F146_EARLIEST_STEP_TIED_BEST_CHECKPOINT_RULE_FROZEN_PREOUTCOME`  
**Accepted control predicate:** `F146_EARLIEST_STEP_TIED_BEST_CHECKPOINT_RULE_FROZEN_PREOUTCOME`  
**Global project state preserved:** `DRAFT_NOT_EXECUTABLE`

## 1. Verdict

`GO` for the exact four-file F146 package identified below.

The final independent review found zero P0, zero P1, and zero P2 defects. The
package closes exactly F146,
`/training_and_checkpoint_plan/checkpoint_tie_rule`, with the rule
`F146_EARLIEST_STEP_TIED_BEST_CANONICAL_CHECKPOINT_RULE_V1`. Within one future
canonical selection unit, an invocation on an at-least-two-member complete
tied-best eligible roster already certified under final frozen F144 semantics
selects the unique smallest exact nonnegative completed optimizer-step index.

The accepted count delta is exactly:

- pre-execution changes from 144 open / 22 closed to 143 open / 23 closed;
- post-execution remains 3 open / 3 closed;
- the total changes from 147 open / 25 closed to 146 open / 26 closed; and
- the method/runtime/compute workstream changes from 64 open / 1 closed to
  63 open / 2 closed.

No blocker, Formal Test, result slot, operational task, implementation gate,
runtime state, or scientific state is closed by this package or this receipt.
This receipt is independent acceptance evidence only. It does not itself edit
the project timetable or evidence ledger and supplies no execution,
registration, network, data, entropy, runtime, science, claim-promotion,
release, submission, or publication authority.

## 2. Exact reviewed package

All four files were independently reopened through their canonical project
paths. Each was a regular, single-link exact-`0644` file with one terminal line
feed. Their accepted byte bindings are:

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human freeze | `PROJECT_F146_CHECKPOINT_TIE_RULE_FREEZE.md` | 18,409 | `403858d0a1afe5c4498973b568ca2e528cb0cde54a02dde52f74123eb0b4c249` |
| Machine freeze | `research/fixtures/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.json` | 20,813 | `21dcfd76f4701f3be033f6ab70a7c93fd9b9b3475ab773d8709d5d027dcbf447` |
| Read-only validator and pure selector | `research/diagnostics/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.py` | 55,293 | `f260cf4cb34cf05a6ddbf55c9690207f10b8758c06a23f3afd28f6ad76670ab5` |
| Hostile tests | `tests/unit/test_manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.py` | 36,317 | `cfe4bd7689b6d40abd28b363e553172ecdbb1dc0bc1a759d61abb124e5332bbd` |

The four reviewed files total 130,832 bytes. The machine file is duplicate-free
canonical ASCII JSON plus one terminal line feed. An independent
implementation, without importing the package validator, recomputed the
domain-separated semantic digest
`33ae0137e1c41da0553b78d7790f4556ddf7d993bbf635fe9dd6abd46ec9c131`,
exactly matching the embedded `record_sha256`.

The machine file contains the exact four-path package roster, binds the three
nonmachine files by byte count and raw SHA-256, declares the noncyclic machine
self-binding correctly, and reconstructs exactly one field closure: F146 at
the authoritative JSON pointer. Any byte change to a reviewed package file
invalidates this receipt.

## 3. Predecessor and baseline verification

The review independently reopened all 19 machine-bound predecessor files.
Every byte count and raw SHA-256 matched, every file was regular, single-link,
and exact mode `0644`, and each terminal-line-feed disposition matched its
binding. The exact predecessor groups and counts are:

| Predecessor group | Bound files |
|---|---:|
| Execution preregistration v1 | 2 |
| Pre-execution closure v2 | 2 |
| Anti-drift policy | 1 |
| A1 development-checkpoint V2 exclusion | 2 |
| D1 diagnostic exclusion | 2 |
| Accepted B11 package and independent review | 5 |
| Accepted F137 package and independent review | 5 |
| **Total** | **19** |

Applicable predecessor semantic self-digests were recomputed, and the exact
base training/checkpoint projection was parsed. Before F146, F139--F147 remain
null in the authoritative preregistration, including F144 and F146, and
experiment-level optional stopping remains forbidden. The accepted A1
development record retains `FINAL_UPDATE_ONLY`,
`NOT_APPLICABLE_NO_SELECTION`, no early stopping, and no validation-checkpoint
selection. The D1 diagnostic selected no checkpoint and remains ineligible as
a future production checkpoint or F146 input.

The accepted B11 evidence preserves PRE at 145/21, changes POST to 3/3 by
closing only F168, F170, and F171, and leaves F164, F165, and F169 open. The
accepted F137 package then closes only F137, establishing the immediate F146
baseline of PRE 144/22, POST 3/3, and total 147/25. The F137 independent review
is `GO`, and the anti-drift policy requires a named count-reducing closure.
F146 supplies that direct one-field closure and creates no zero-delta precursor.

## 4. Rule and certification audit

The reviewed selector accepts no raw validation value. Its exact input schema
contains one ordered row tuple, one roster digest, and a certificate requiring:

- every row to be eligible under F144;
- the referenced F144 semantics to be final and frozen;
- the supplied candidate set to be closed and the tied-best roster complete;
- one exact selection-unit digest and one exact F144-semantics digest;
- first-and-only invocation certification with prior invocation count exactly
  the built-in integer zero; and
- the explicit statement that the pure helper does not authenticate production
  history.

This is a structural qualification contract, not an assertion that the
stateless helper can observe call history, prove that a future roster is truly
final, or prevent a second call. Those integration and durable-custody duties
remain open and must be satisfied before any future production use.

An actual tie invocation requires at least two rows. Every optimizer-step index
must have exact built-in `int` type, must not be a Boolean or subclass, and must
be nonnegative. Step zero is accepted only as a structurally eligible future
candidate. The package-local base-`10^9` chunked decimal encoder is total for
arbitrarily large exact integers and gives the same ordinary base-10 JSON bytes
regardless of the interpreter integer-to-string digit guard.

Rows have exact key order and zero-based ordinals and are strictly ordered by
increasing step. The step-bound checkpoint identity is a domain-separated
SHA-256 binding of selection-unit digest, step index, and immutable checkpoint-
content digest. The complete-roster digest is separately domain-separated and
binds the F144-semantics digest, canonical ordered rows, and selection unit.
The literal domain bytes, NUL suffixes, JSON rules, payload keys, and success
and refusal key rosters all match the human and machine contracts.

Byte-for-byte duplicate rows, a repeated step, conflicting rows at one step,
cross-step checkpoint-identity reuse, a stale step-bound identity, invalid
order, malformed digests, false certification, and roster-digest drift all
refuse before selection. The same checkpoint-content digest may occur at two
different steps, but its step-bound identities must differ. With a valid
canonical roster, the selected checkpoint is exactly its unique minimum-step
member.

## 5. Refusal, once-only, and F144 separation

Invalid or uncertified input produces the terminal call disposition
`F146_SELECTION_REFUSAL_NO_CHECKPOINT`, with no selected checkpoint and no
fallback. It creates no authority for retry, rerun, retraining, top-up, extra
steps, a new checkpoint, a changed metric or tolerance, or an altered roster.

That refusal is not a sixth scheduled-run terminal status. The unchanged
scheduled-run status roster is exactly `COMPLETE`, `ALGORITHMIC_FAILURE`,
`NONFINITE`, `OOM_OR_TIMEOUT`, and `INFRA_ABORT`. F146 does not close F149 or
choose how a future selection-integrity failure maps into that existing
taxonomy.

The frozen rule forbids sequential stopping and repeated application while
validation values arrive. It can be invoked only once after the future
candidate set and its F144 certificate are complete. The helper makes no
first-seen, last-seen, insertion-order, filename, path, timestamp, or fallback
selection.

F144 remains solely responsible for the validation metric, favorable
direction, numeric representation, comparison/equality relation, tolerance,
nonfinite-value treatment, eligibility rule, and production certificate. F146
does not infer, default, select, alter, or repair any of those semantics.

## 6. Custody and effect-surface audit

The validator performs canonical relative-path checks and componentwise
no-follow reads through held directory descriptors. It requires each leaf to
be a regular, single-link exact-`0644` file at the before-path,
before-descriptor, after-descriptor, and after-path observations. Its stable
fingerprint includes device, inode, size, modification time, change time, full
mode, and link count. Root, ancestor, descriptor, and final namespace identity
are rechecked, so permission, hard-link, symlink, inode-substitution, ancestor-
replacement, and mid-read races fail closed.

The machine must equal the fully reconstructed expected record and retain its
canonical encoding and semantic self-digest. Hostile tests cover exact domains
and independent digest known answers; step zero and a 5,001-digit step;
interpreter-guard independence; at-least-two cardinality; exact types and key
orders; every required certificate; changed selection-unit binding; duplicate,
conflicting, aliased, and reordered rows; repeated content at distinct steps;
digest tampering; five-status separation; package and all 19 predecessor byte
bindings; semantic drift; canonical and duplicate-key JSON; stable-read path,
mode, link, symlink, leaf-inode, and ancestor races; and fully re-signed false
field, count, implementation, execution, F144, B12, and nonclosure claims.
All hostile writes occur only in disposable test copies.

Direct source inspection found only standard-library hashing, JSON, read-only
filesystem, path, regular-expression, stat, and typing dependencies. The
source contains no writer, RNG or entropy source, network or connector client,
subprocess launcher, project-science import, data reader, training or optimizer
route, checkpoint writer, runtime-capture route, production worker, result or
claim promoter, or submission route. The selector is pure and idempotent; its
synthetic qualification output is not a production checkpoint selection.

## 7. Independent executed qualification

All qualification used Python bytecode writing disabled and pytest's cache
provider disabled.

| Working context | Qualification | Independent result |
|---|---|---|
| Project root | Canonical F146 validator entry point | `PASS`; semantic digest `33ae0137e1c41da0553b78d7790f4556ddf7d993bbf635fe9dd6abd46ec9c131` |
| `/private/tmp` current working directory | Canonical F146 validator by absolute path | `PASS`; same semantic digest |
| Project root | F146 focused hostile suite | `156 passed in 0.74s` |
| `/private/tmp` current working directory | F146 focused hostile suite against the canonical absolute package | `156 passed in 1.00s` |
| Project root | Accepted F137 and F146 suites together | `282 passed in 1.83s` |

The canonical four-file package and all 19 bound predecessor files retained
their exact byte receipts across these independent read-only checks.

## 8. Findings and preserved nonclosures

| Severity | Count | Disposition |
|---|---:|---|
| P0 | 0 | None |
| P1 | 0 | None |
| P2 | 0 | None |

Only F146 is accepted for later registration. The following remain expressly
unclosed, null, absent, or unperformed:

- F139 optimizer, F140 learning-rate schedule, F141 precision, F142 batch
  construction, F143 maximum epochs or optimizer steps, F144 validation
  semantics, F145 early-stopping patience, and F147 maximum tuning trials;
- F150--F162 hardware, environment, resource, reserve, allocation, storage,
  retention, and total-compute fields;
- F164, F165, and F169, while the accepted B11 closures of F168, F170, and F171
  remain unchanged;
- B07, B12, and all 12 blockers;
- the compound checkpoint-selection/training task and whole-method
  implementation, production integration, authenticated invocation custody,
  checkpoint cadence, storage and retention policy, capacity and maximum-step
  rule, and future F144 certificate;
- Formal Tests 28 and 29 (`OPEN`) and Formal Test 30 (`PENDING`);
- R1--R4 and all four result slots;
- every domain, method, seed, configuration, checkpoint byte sequence,
  candidate roster, validation value, metric, direction, representation,
  equality or tolerance rule, data item, entropy source, runtime, result,
  inference, decision, claim, release, submission, and publication approval;
  and
- network/contact/repository/license/data activity, operational receipts,
  training, checkpoint selection, scientific or production execution, tracker
  or evidence-ledger registration, and predecessor mutation.

The accepted A1 development V2 and D1 evidence retain their nonproduction and
nonselection boundaries. The project remains `DRAFT_NOT_EXECUTABLE`, with all
12 blockers open, zero Formal Tests closed, and zero result slots filled.

## 9. Independent acceptance boundary

The exact package receives `INDEPENDENT_REVIEW_GO`. A later separately
authorized timetable and evidence-ledger reconciliation may register only F146
and the corresponding 144/22 to 143/23 PRE transition, while preserving POST
at 3/3 and changing the total only from 147/25 to 146/26. It must cite the
exact four-file package and this receipt and leave every listed nonclosure
unchanged.

This receipt does not itself perform that registration, populate F144 or any
other open field; select a checkpoint; authenticate invocation history; choose
a roster, cadence, maximum step, storage policy, retention policy, metric,
tolerance, data, seed, or runtime; close B07 or B12; alter a Formal Test or
result; or authorize any operational or scientific action. Any byte change to
the reviewed four-file package or any of its 19 bound predecessor files
invalidates this receipt and requires a fresh independent review.
