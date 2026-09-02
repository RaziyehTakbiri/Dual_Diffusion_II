# Independent review V2 of the F120 initializer-error direction freeze

**Reviewed:** 2026-09-01  
**Reviewer lane:** `/root/block2_final_redteam`  
**Review state:** `INDEPENDENT_REVIEW_GO`  
**Subject state:** `F120_INITIALIZER_ERROR_DIRECTION_UPPER_BOUND_FROZEN_PREOUTCOME`  
**Accepted control predicate:** `F120_INITIALIZER_ERROR_DIRECTION_UPPER_BOUND_FROZEN_PREOUTCOME`  
**Global project state preserved:** `DRAFT_NOT_EXECUTABLE`

## 1. Verdict and exact scope

`GO` for the exact four-file F120 package bound below. The independent review
found P0 = 0, P1 = 0, and P2 = 0.

The package closes solely F120,
`/metric_and_estimand_plan/constraint_metrics/3/direction`, to the exact
built-in string `UPPER_BOUND`; the zero-based constraint-metric index remains 3
and its identifier remains exactly `initializer-error`.

The accepted count delta is exactly:

- PRE: 142 open / 24 closed to 141 open / 25 closed;
- POST: unchanged at 3 open / 3 closed;
- total: 145 open / 27 closed to 144 open / 28 closed; and
- Theory/Statistics: 34 open / 20 closed to 33 open / 21 closed.

No blocker, Formal Test, result slot, operational task, runtime state, or
scientific state is closed. This receipt supplies independent acceptance
evidence only and grants no registration, execution, network, data, entropy,
runtime, science, claim-promotion, release, submission, or publication
authority.

## 2. Exact current package bindings

Each reviewed file was a regular, single-link exact-`0644` file with one
terminal line feed.

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human freeze | `PROJECT_F120_INITIALIZER_ERROR_DIRECTION_FREEZE.md` | 7,259 | `dc41516bc22ab5d8b908bf9935216c0aade1df0ddcb31d484f8104b53e759589` |
| Machine freeze | `research/fixtures/manuscript_v3_f120_initializer_error_direction_freeze_v1.json` | 11,986 | `d246c46f006e87a512985d67b8a446ccdc3cf1ab06f0ceb28990ae2e0e977808` |
| Read-only validator and synthetic comparator | `research/diagnostics/manuscript_v3_f120_initializer_error_direction_freeze_v1.py` | 33,065 | `74d141b6f871cffbe57dffbd29a4f900d64b8301f3ef1cc86136b420c338ec8f` |
| Hostile tests | `tests/unit/test_manuscript_v3_f120_initializer_error_direction_freeze_v1.py` | 17,983 | `72f91a3f6d1fa9e423449f87283086cf33408a4bfb61c207c0badb0c9e4128dd` |

The four files total 70,293 bytes. The machine is duplicate-free canonical
ASCII JSON plus one terminal line feed. Independent reconstruction produced
the schema-domain semantic digest
`c3d018a4bfc8eab4eaa80285edca8f87d1b6e980a09dd3b10abe126b6fbf1ad3`,
matching its embedded `record_sha256`. The machine reconstructs exactly the
sole closure and count transitions above, carries the exact four-path package
roster, and binds the three nonmachine files by exact size and raw digest.

## 3. Receipt lifecycle and validator authenticity boundary

The package roster consists only of the four files in section 2. Neither this
V2 receipt nor
`PROJECT_F120_INITIALIZER_ERROR_DIRECTION_FREEZE_INDEPENDENT_REVIEW.md` is a
package member, package binding, or predecessor. The validator does not name,
read, create, modify, or delete either receipt and contains no receipt-writing
route.

Lifecycle behavior was independently exercised in both directions:

- validation and all qualification tests passed in the live tree with the old
  receipt present; and
- validation passed in a disposable exact copy containing the four package
  files and all 15 predecessors while both F120 receipt files were absent.

The old receipt is 12,354 bytes with SHA-256
`aa4efb4cfb2aceba8333b2d1a44bf27915a3616968901542a6b2c5b45a7faa06`.
It is historical and superseded evidence for prior package bytes and is not an
authentication of the current package. This V2 receipt is the current durable
external authenticity anchor.

The package honestly declares
`INDEPENDENT_REVIEW_BOUND_NOT_SELF_AUTHENTICATING`. The machine records the
validator bytes and the validator reconstructs the complete machine record,
but an executing validator does not authenticate its own source. This receipt
binds the exact 33,065-byte validator and its raw digest without claiming an
internal fixed point, normalized self-anchor, or self-authentication.

## 4. Predecessors, exact semantics, and refusal boundary

All 15 machine-bound predecessor files were independently verified for exact
byte count, raw SHA-256, regular-file status, single-link status, exact `0644`
mode, and terminal-line-feed disposition. The bound groups are the anti-drift
policy (1), execution preregistration V1 (2), pre-execution closure V2 (2),
accepted B05 known-law orientation package (5), and accepted F145 package plus
independent review (5).

Applicable semantic self-digests were recomputed. The base preregistration
retains nine ordered constraint metrics and keeps index 3 as
`{"metric_id":"initializer-error","direction":null,"threshold_or_margin":null}`.
The F145 baseline and the count transitions in section 1 remain exact.

The accepted value is only `UPPER_BOUND`. For synthetic qualification inputs,
the comparator applies `PASS` exactly when a separately certified upper
endpoint is less than or equal to a separately final-and-frozen F121 threshold;
equality passes. Missing, false, malformed, nonfinite, negative, noncanonical,
identity-mismatched, unit-mismatched, unfrozen, reordered, or extra input
refuses with `F120_DIRECTION_REFUSAL_NO_GATE_DECISION` and creates no fallback.
Exact rational comparison uses built-in nonnegative integers in lowest terms,
with key order `denominator, numerator`, and no floating-point conversion.

F016 is not reused as F121. The B05 F016 qualification ceilings and width
budgets remain known-law fixture evidence only. F120 selects no F121 value,
threshold, margin, scalar definition, unit, normalization, aggregation,
population, conditioning, estimator, production numeric representation,
confidence method, interval, p-value, multiplicity procedure, or decision
count.

## 5. Preserved nonclosures and non-effects

The following remain open, null, absent, pending, or unperformed:

- F114--F119, F121--F127, and F149;
- B05 and all 12 project blockers;
- Formal Test 28 (`OPEN`), Formal Test 29 (`OPEN`), and Formal Test 30
  (`PENDING`), with zero Formal Tests closed;
- R1--R4 and all four result slots, with zero results filled;
- every actual initializer-error scalar, threshold, unit, aggregation,
  certified endpoint, data item, candidate, checkpoint, entropy source,
  training run, runtime, result, inference, claim, release, and submission; and
- every network, contact, repository, license, data-access, production,
  operational, runtime, training, evaluation, and scientific action.

The project remains `DRAFT_NOT_EXECUTABLE`. Neither the package nor this
receipt edits the timetable, evidence ledger, package predecessors, or any
operational receipt.

## 6. Custody and hostile review

The validator requires complete expected-record equality and separately checks
canonical encoding and the semantic digest. Stable reads use absolute-root,
componentwise no-follow traversal through held directory descriptors. Root,
ancestor, leaf namespace, and leaf descriptor fingerprints are compared before
and after reads. Regular-file type, exact `0644` mode, link count 1, device,
inode, size, modification time, change time, and namespace stability are
enforced. Symlinks, hard links, mode drift, ancestor or leaf substitution,
namespace changes, mid-read changes, and short reads fail closed.

Hostile coverage includes canonical and duplicate-key JSON, full machine
reconstruction under semantic re-signing, package and predecessor bindings,
field/index/identifier/value drift, rational key order and malformed rationals,
comparison boundaries and equality, false certifications, F016/F121 shadow
selection, count and nonclosure drift, validator-authenticity overclaims,
receipt lifecycle disjointness, and custody/race mutations. Test mutations are
confined to disposable copies.

## 7. Independent qualification evidence

Qualification used Python 3.11 with bytecode writing disabled and pytest's
cache provider disabled.

| Working context | Qualification | Independent result |
|---|---|---|
| Project root | Canonical F120 validator | `PASS`; 15 predecessors; semantic `c3d018a4bfc8eab4eaa80285edca8f87d1b6e980a09dd3b10abe126b6fbf1ad3` |
| `/private/tmp` | Canonical validator by absolute path | `PASS`; same predecessor count and semantic digest |
| Project root | F120 focused hostile suite | `113 passed` |
| `/private/tmp` | F120 focused hostile suite | `113 passed` |
| Project root | Accepted F145 plus F120 suites | `324 passed` |
| `/private/tmp` | Accepted F145 plus F120 suites | `324 passed` |
| Disposable copy, both F120 receipts absent | Canonical F120 validation | `PASS`; exact package and 15 predecessors accepted |

The live-tree runs occurred with the old receipt present. Its presence did not
alter package membership, validation, tests, effects, or authority.

## 8. Acceptance boundary

| Severity | Count | Disposition |
|---|---:|---|
| P0 | 0 | None |
| P1 | 0 | None |
| P2 | 0 | None |

The exact current package receives `INDEPENDENT_REVIEW_GO`. A separately
authorized later tracker/ledger reconciliation may register only F120 and the
exact count changes in section 1 while citing the current package and this V2
receipt. This receipt does not itself perform registration, populate F121 or
any other open field, reuse F016, authenticate production inputs, close B05 or
any blocker/Formal Test/result/task, or authorize operational or scientific
work.
