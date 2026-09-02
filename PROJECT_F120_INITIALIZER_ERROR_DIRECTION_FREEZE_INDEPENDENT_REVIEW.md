# Independent review of the F120 initializer-error direction freeze

**Reviewed:** 2026-09-01  
**Reviewer lane:** `/root/block2_final_redteam`  
**Review state:** `INDEPENDENT_REVIEW_GO`  
**Subject state:** `F120_INITIALIZER_ERROR_DIRECTION_UPPER_BOUND_FROZEN_PREOUTCOME`  
**Accepted control predicate:** `F120_INITIALIZER_ERROR_DIRECTION_UPPER_BOUND_FROZEN_PREOUTCOME`  
**Global project state preserved:** `DRAFT_NOT_EXECUTABLE`

## 1. Verdict

`GO` for the exact four-file F120 package identified below.

The final independent review found zero P0, zero P1, and zero P2 defects. The
package closes exactly F120,
`/metric_and_estimand_plan/constraint_metrics/3/direction`, to the exact
built-in string `UPPER_BOUND`. At zero-based constraint-metric index 3, the
authoritative identifier remains exactly `initializer-error`.

The accepted count delta is exactly:

- pre-execution changes from 142 open / 24 closed to 141 open / 25 closed;
- post-execution remains 3 open / 3 closed;
- the total changes from 145 open / 27 closed to 144 open / 28 closed; and
- the Theory/Statistics workstream changes from 34 open / 20 closed to
  33 open / 21 closed.

No blocker, Formal Test, result slot, operational task, runtime state, or
scientific state is closed by this package or this receipt. This receipt is
independent acceptance evidence only. It does not edit the project timetable
or evidence ledger and supplies no registration, execution, network, data,
entropy, runtime, science, claim-promotion, release, submission, or publication
authority.

## 2. Exact reviewed package

All four files were independently reopened through their canonical project
paths. Each was a regular, single-link exact-`0644` file with one terminal line
feed. Their accepted byte bindings are:

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human freeze | `PROJECT_F120_INITIALIZER_ERROR_DIRECTION_FREEZE.md` | 7,259 | `dc41516bc22ab5d8b908bf9935216c0aade1df0ddcb31d484f8104b53e759589` |
| Machine freeze | `research/fixtures/manuscript_v3_f120_initializer_error_direction_freeze_v1.json` | 11,986 | `21e36475741f5e8beae5233c0e0ad258e46426ceffb807c3f957bea9553db2c4` |
| Read-only validator and synthetic comparator | `research/diagnostics/manuscript_v3_f120_initializer_error_direction_freeze_v1.py` | 33,065 | `9eb9f33247d1e71c6f5cb7bd3a116b957c7d197aca88aa9047db7234f8b179e8` |
| Hostile tests | `tests/unit/test_manuscript_v3_f120_initializer_error_direction_freeze_v1.py` | 17,339 | `72bae77fca7fdbda3efdb2210c6f1fb5aa4137b0d3cfebdd1b48c34e6a4a9887` |

The four reviewed files total 69,649 bytes. The machine file is duplicate-free
canonical ASCII JSON plus one terminal line feed. An independent computation,
without importing the package validator, recomputed the schema-domain semantic
digest
`ac201dba296f3f0e09e92b3206f752dcb7cdd5cfe506f196f973af237389239e`,
exactly matching the embedded `record_sha256`.

The machine contains the exact four-path package roster and binds each
nonmachine file by byte count and raw SHA-256. It reconstructs exactly one field
closure and the exact count and workstream transitions above. Any byte change
to a reviewed package file invalidates this receipt.

## 3. Validator raw-authenticity boundary

The package truthfully declares
`INDEPENDENT_REVIEW_BOUND_NOT_SELF_AUTHENTICATING`. The machine records the
current validator raw bytes, and the validator reconstructs the complete
machine record, but an executing validator cannot establish the authenticity
of its own source bytes. The package makes no normalized-source, fixed-point,
internal-anchor, or self-authentication claim.

This independent receipt is the durable external raw-authenticity anchor for
the exact 33,065-byte validator whose SHA-256 is
`9eb9f33247d1e71c6f5cb7bd3a116b957c7d197aca88aa9047db7234f8b179e8`.
The receipt does not broaden the validator's authority or convert validation
into registration, execution, or scientific evidence.

## 4. Predecessor and baseline verification

The review independently verified all 15 machine-bound predecessor files.
Every byte count and raw SHA-256 matched; every file was regular, single-link,
exact mode `0644`; and every terminal-line-feed disposition matched its
binding. The exact predecessor groups and counts are:

| Predecessor group | Bound files |
|---|---:|
| Anti-drift operating policy | 1 |
| Execution preregistration V1 | 2 |
| Pre-execution closure V2 | 2 |
| Accepted B05 known-law orientation package | 5 |
| Accepted F145 package and independent review | 5 |
| **Total** | **15** |

Applicable predecessor semantic self-digests were recomputed. The base
preregistration retains exactly nine ordered constraint metrics and retains
index 3 as
`{"metric_id":"initializer-error","direction":null,"threshold_or_margin":null}`.
The accepted F145 package and independent review establish the immediate F120
baseline of PRE 142/24, POST 3/3, total 145/27, Theory/Statistics 34/20,
Method/Runtime/Compute 62/3, Data/Governance/Reproduction 48/4, and Final 1/0.

The complete accepted B05 group is bound only as immutable known-law
orientation evidence. Its F016 exact-self qualification ceilings and numerical
width budgets are not imported, reused, inferred, or promoted as the future
F121 production threshold. B05 remains open.

## 5. Exact direction and refusal audit

The sole F120 value is the exact built-in string `UPPER_BOUND`; case changes,
whitespace, aliases, structured replacements, Boolean or numeric substitutes,
other metric identifiers, and other indices refuse. The package freezes only
the direction that a smaller future initializer-error scalar is favorable.

For synthetic qualification inputs only, the pure comparator applies:

```text
PASS iff certified_upper_endpoint <= f121_threshold
FAIL iff certified_upper_endpoint >  f121_threshold
```

Equality passes. The comparator requires exact certifications that the future
initializer-error scalar definition and F121 threshold are separately final
and frozen, that the supplied endpoint is certified, and that the endpoint and
threshold use the same scalar identity and units. Missing, false, malformed,
nonfinite, negative, noncanonical, identity-mismatched, unfrozen, reordered, or
extra input refuses with
`F120_DIRECTION_REFUSAL_NO_GATE_DECISION`, produces no gate decision, and
creates no fallback.

The qualification rational objects use exact built-in nonnegative integers in
lowest terms with exact key order `denominator, numerator`; comparison is exact
cross multiplication without floating-point conversion. This synthetic
encoding is not a selected production representation. The helper checks digest
shape and caller certifications but explicitly does not authenticate production
provenance, finality, custody, scalar semantics, units, or scientific
correctness; successful synthetic output retains
`production_inputs_authenticated=false`.

## 6. Sole closure and preserved nonclosures

F120 selects no initializer-error formula; no KL, TV, maximum, conjunction,
weighted combination, scalar, unit, normalization, aggregation, population,
conditioning, estimator, numeric representation, threshold, margin, tolerance,
confidence method, interval construction, multiplicity procedure, p-value, or
decision count. F121 remains separately open and null.

The following remain expressly open, null, absent, pending, or unperformed:

- F114--F119, F121--F127, and F149;
- B05 and all 12 project blockers;
- Formal Test 28 (`OPEN`), Formal Test 29 (`OPEN`), and Formal Test 30
  (`PENDING`), with `formal_tests_closed=0`;
- R1--R4 and all four result slots, with `results_filled=0`;
- every actual initializer-error scalar, threshold, unit, aggregation,
  certified endpoint, data item, candidate, checkpoint, entropy source,
  training run, runtime, result, inference, claim, release, and submission;
- network, contact, repository, license, data-access, production, operational,
  runtime, training, evaluation, and scientific execution; and
- tracker, evidence-ledger, package, predecessor, or operational-receipt
  mutation.

The project remains `DRAFT_NOT_EXECUTABLE`. The direction freeze cannot be used
as an executable gate until a separately final and frozen F121 threshold,
scalar definition, units, certified endpoint, provenance, and production
integration exist.

## 7. Canonicality, custody, and effect-surface audit

The validator requires the machine to equal its complete reconstructed expected
record and separately verifies canonical encoding and the semantic self-digest.
Human and hostile-test bytes are fixed. All predecessor paths, ordering,
groups, roles, ordinals, byte counts, hashes, semantic receipts, modes, links,
and terminal-line-feed declarations are exact.

Stable reads use absolute-root validation and componentwise no-follow opens
through held directory descriptors. The root, each ancestor, the leaf
namespace, and the leaf descriptor are compared before and after reading. Each
leaf must remain a regular, single-link exact-`0644` file. Device, inode, size,
modification time, change time, full mode, and link count participate in the
fingerprint. Root symlinks, unsafe paths, hard links, mode changes, leaf swaps,
ancestor replacements, namespace changes, mid-read changes, and short reads
fail closed.

Hostile coverage includes exact key and rational order; comparator boundaries
and equality; nonfinite, negative, noncanonical, wrong-type, missing, false,
extra, and reordered inputs; F016/F121 shadow selection; every central machine
surface under semantic re-signing; false field, count, workstream, blocker,
Formal Test, result, authority, effect, and validator-authenticity claims;
fixed human/test bindings; the honest validator raw boundary; canonical and
duplicate-key JSON; all 15 predecessor bindings and semantic drift; and the
custody and race cases above. All hostile writes occur only in disposable test
copies.

Direct source inspection found only standard-library hashing, JSON, arithmetic,
read-only filesystem, path, syntax-tree, stat, and typing functionality. The
source contains no filesystem writer, RNG or entropy source, network or socket
client, connector, subprocess launcher, project-science import, data reader,
training route, production worker, result or claim promoter, registration
route, or submission route.

## 8. Independent executed qualification

Qualification used Python 3.11 with bytecode writing disabled and pytest's
cache provider disabled.

| Working context | Qualification | Independent result |
|---|---|---|
| Project root | Canonical F120 validator entry point | `PASS`; 15 predecessors verified; semantic digest `ac201dba296f3f0e09e92b3206f752dcb7cdd5cfe506f196f973af237389239e` |
| `/private/tmp` current working directory | Canonical F120 validator by absolute path | `PASS`; same predecessor count and semantic digest |
| Project root | F120 focused hostile suite | `113 passed` |
| `/private/tmp` current working directory | F120 focused hostile suite against the canonical absolute package | `113 passed` |
| Project root | Accepted F145 and F120 suites together | `324 passed` |
| `/private/tmp` current working directory | Accepted F145 and F120 suites together | `324 passed` |

The canonical four-file package and all 15 bound predecessor files retained
their exact byte receipts throughout these independent read-only checks.

## 9. Findings and independent acceptance boundary

| Severity | Count | Disposition |
|---|---:|---|
| P0 | 0 | None |
| P1 | 0 | None |
| P2 | 0 | None |

The exact package receives `INDEPENDENT_REVIEW_GO`. A later separately
authorized timetable and evidence-ledger reconciliation may register only F120
and the corresponding PRE 142/24 to 141/25 transition, while preserving POST at
3/3, changing the total only from 145/27 to 144/28, and changing the
Theory/Statistics category only from 34/20 to 33/21. It must cite the exact
four-file package and this receipt and leave every listed nonclosure unchanged.

This receipt does not itself perform that registration; populate F121 or any
other open field; reuse F016 as F121; select a scalar, threshold, unit,
aggregation, confidence method, data item, seed, checkpoint, runtime, or result;
close B05, a blocker, Formal Test, result, or task; authenticate production
inputs; or authorize any operational or scientific action.
