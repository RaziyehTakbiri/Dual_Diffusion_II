# Independent review of the F122 association-error direction freeze

**Reviewed:** 2026-09-01  
**Primary reviewer lane:** `/root/block2_final_redteam`  
**Corroborating reviewer lane:** `/root/b04_feasibility`  
**Review state:** `INDEPENDENT_REVIEW_GO`  
**Subject state:** `F122_ASSOCIATION_APPROXIMATION_ERROR_DIRECTION_UPPER_BOUND_FROZEN_PREOUTCOME`  
**Accepted control predicate:** `F122_ASSOCIATION_APPROXIMATION_ERROR_DIRECTION_UPPER_BOUND_FROZEN_PREOUTCOME`  
**Global project state preserved:** `DRAFT_NOT_EXECUTABLE`

## 1. Verdict and exact scope

`GO` for the exact four-file F122 package bound below. Two independent
byte-bound reviews found P0 = 0, P1 = 0, and P2 = 0.

The package closes solely F122,
`/metric_and_estimand_plan/constraint_metrics/4/direction`, to the exact
built-in string `UPPER_BOUND`; the zero-based constraint-metric index remains 4
and its identifier remains exactly `association-approximation-error`.

The accepted count delta is exactly:

- PRE: 141 open / 25 closed to 140 open / 26 closed;
- POST: unchanged at 3 open / 3 closed;
- total: 144 open / 28 closed to 143 open / 29 closed; and
- Theory/Statistics: 33 open / 21 closed to 32 open / 22 closed.

No blocker, Formal Test, result slot, operational task, runtime state, or
scientific state is closed. This receipt supplies independent acceptance
evidence only and grants no registration, execution, network, data, entropy,
runtime, science, claim-promotion, release, submission, or publication
authority.

## 2. Exact current package bindings

Each reviewed file was a regular, single-link exact-`0644` file with one
terminal line feed and no carriage return or NUL byte.

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human freeze | `PROJECT_F122_ASSOCIATION_ERROR_DIRECTION_FREEZE.md` | 7,664 | `7198ac7069f558add5862230dc4371037c57b6aa1054c8386ec9a13fff9d434c` |
| Machine freeze | `research/fixtures/manuscript_v3_f122_association_error_direction_freeze_v1.json` | 12,369 | `f90c0b1330f2baeebc6aa524d888ce88e7963f7f74492c882724670dd2e5fc94` |
| Read-only validator and synthetic comparator | `research/diagnostics/manuscript_v3_f122_association_error_direction_freeze_v1.py` | 33,531 | `cd87090e106fdcd064cb3de5646b3088727488156f27cb739f69fc33b31a6f2d` |
| Hostile tests | `tests/unit/test_manuscript_v3_f122_association_error_direction_freeze_v1.py` | 18,680 | `0ca79d214f0d2418e08bca87d1600913d8896d683410d1b520f4f54d12548e6f` |

The four files total 72,244 bytes. The machine is duplicate-free canonical
ASCII JSON plus one terminal line feed. Independent reconstruction produced
the schema-domain semantic digest
`4d4dc3abf2691b577c48ab97a02fd28b409f6cf1fdcc5521a93d2186fbaca43d`,
matching its embedded `record_sha256`. The machine reconstructs exactly the
sole closure and count transitions above, carries the exact four-path package
roster, and binds the three nonmachine files by exact size and raw digest.

## 3. Receipt lifecycle and validator authenticity boundary

The package roster consists only of the four files in section 2. Neither this
receipt nor a possible versioned successor receipt is a package member,
package binding, or predecessor. The validator does not name, read, create,
modify, or delete either receipt path and contains no receipt-writing route.

Lifecycle behavior was independently exercised in disposable exact copies:

- validation passed when both possible F122 receipt names were absent; and
- validation passed when disposable files with both possible F122 receipt
  names were present.

Receipt coexistence therefore cannot change package membership, validation,
tests, effects, or authority.

The package honestly declares
`INDEPENDENT_REVIEW_BOUND_NOT_SELF_AUTHENTICATING`. The machine records the
validator bytes and the validator reconstructs the complete machine record,
but an executing validator does not authenticate its own source. This receipt
binds the exact 33,531-byte validator and its raw digest without claiming an
internal fixed point, normalized self-anchor, or self-authentication.

## 4. Predecessors, exact semantics, and refusal boundary

All 15 machine-bound predecessor files were independently verified for exact
byte count, raw SHA-256, regular-file status, single-link status, exact `0644`
mode, and terminal-line-feed disposition. The bound groups are the anti-drift
policy (1), execution preregistration V1 (2), pre-execution closure V2 (2),
accepted B05 known-law orientation package (5), and the current accepted F120
package plus V2 independent review (5).

The final F120 predecessor is exactly
`PROJECT_F120_INITIALIZER_ERROR_DIRECTION_FREEZE_INDEPENDENT_REVIEW_V2.md`,
9,584 bytes, SHA-256
`6c98574385da17411ab01a28f94036505d9870462036cbfb9798b67c680187ef`.
The superseded F120 V1 review receipt is excluded. Applicable semantic
self-digests were independently recomputed. The base preregistration retains
nine ordered constraint metrics and keeps index 4 as
`{"metric_id":"association-approximation-error","direction":null,"threshold_or_margin":null}`.

The accepted value is only `UPPER_BOUND`. For synthetic qualification inputs,
the comparator applies `PASS` exactly when a separately certified upper
endpoint is less than or equal to a separately final-and-frozen F123 threshold;
equality passes. Missing, false, malformed, nonfinite, negative, noncanonical,
identity-mismatched, unit-mismatched, unfrozen, reordered, or extra input
refuses with `F122_DIRECTION_REFUSAL_NO_GATE_DECISION` and creates no fallback
or gate decision. Exact rational comparison uses built-in nonnegative integers
in lowest terms, with key order `denominator, numerator`, and no floating-point
conversion.

F016 and F121 are not reused as F123. The B05 F016 qualification ceilings and
width budgets remain known-law fixture orientation evidence only. F121 remains
`OPEN/HOLD`. F122 selects no F123 value, threshold, margin, scalar definition,
KL/TV choice, unit, normalization, aggregation, population, conditioning,
estimator, production numeric representation, confidence method, interval,
p-value, multiplicity procedure, or decision count.

## 5. Preserved nonclosures and anti-drift boundary

The following remain open, null, absent, pending, or unperformed:

- F114--F119, F121, F123--F127, and F149;
- B05 and all 12 project blockers;
- Formal Test 28 (`OPEN`), Formal Test 29 (`OPEN`), and Formal Test 30
  (`PENDING`), with zero Formal Tests closed;
- R1--R4 and all four result slots, with zero results filled;
- every actual association-error scalar, threshold, unit, aggregation,
  certified endpoint, data item, candidate, checkpoint, entropy source,
  training run, runtime, result, inference, claim, release, and submission; and
- every network, contact, repository, license, data-access, production,
  operational, runtime, training, evaluation, and scientific action.

The project remains `DRAFT_NOT_EXECUTABLE`. Neither the package nor this
receipt edits the timetable, evidence ledger, package predecessors, or any
operational receipt.

This is explicitly the second consecutive B05-adjacent direction artifact.
No third consecutive B05 artifact may be constructed without a fresh explicit
scope review. This receipt supplies no such review or permission.

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
comparison boundaries and equality, false certifications, F016/F121/F123
shadow selection, count and nonclosure drift, validator-authenticity
overclaims, receipt lifecycle disjointness, and custody/race mutations. Test
mutations are confined to disposable copies.

## 7. Independent qualification evidence

Qualification used Python 3.11 with bytecode writing disabled and pytest's
cache provider disabled.

| Working context | Qualification | Independent result |
|---|---|---|
| Project root | Canonical F122 validator | `PASS`; 15 predecessors; semantic `4d4dc3abf2691b577c48ab97a02fd28b409f6cf1fdcc5521a93d2186fbaca43d` |
| `/private/tmp` | Canonical validator by absolute path | `PASS`; same predecessor count and semantic digest |
| Project root | F122 focused hostile suite | `118 passed` |
| `/private/tmp` | F122 focused hostile suite | `118 passed` |
| Project root | Accepted F120 plus F122 suites | `231 passed` |
| Project root | Overnight accepted-package union through F122 | `1,059 passed` |
| `/private/tmp` | Overnight accepted-package union through F122 | `1,059 passed` |
| Disposable copies, F122 receipts absent and present | Canonical F122 validation | `PASS` in both lifecycle states |

## 8. Acceptance boundary

| Severity | Count | Disposition |
|---|---:|---|
| P0 | 0 | None |
| P1 | 0 | None |
| P2 | 0 | None |

The exact current package receives `INDEPENDENT_REVIEW_GO`. A separately
authorized later tracker/ledger reconciliation may register only F122 and the
exact count changes in section 1 while citing the current package and this
receipt. This receipt does not itself perform registration, populate F121,
F123, or any other open field, reuse F016, authenticate production inputs,
close B05 or any blocker/Formal Test/result/task, or authorize operational or
scientific work.
