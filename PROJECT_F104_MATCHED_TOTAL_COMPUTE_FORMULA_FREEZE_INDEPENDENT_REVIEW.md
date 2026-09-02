# Independent review of the F104 matched-total-compute formula freeze

**Reviewed:** 2026-08-31  
**Review state:** `INDEPENDENT_REVIEW_GO`  
**Subject state:** `F104_MATCHED_TOTAL_COMPUTE_FORMULA_FROZEN_RESOURCE_VALUES_NULL`  
**Accepted control predicate:** `MATCHED_TOTAL_COMPUTE_FORMULA_F104_FROZEN_PREOUTCOME`  
**Global project state preserved:** `DRAFT_NOT_EXECUTABLE`

## 1. Verdict

`GO` for the exact four-file F104 package identified below.

The review found no P0, P1, or P2 package finding. The package faithfully
promotes the already validated parameterized matched-total-compute formula
from the frozen baseline draft into exactly one additive pre-execution field
closure, F104. It neither chooses nor measures a calibration weight, resource
count, resource ceiling, method budget, hardware identity, runtime, capacity,
scientific result, or operational receipt.

The accepted registration delta is therefore exactly:

- F104 changes from `OPEN` to `CLOSED`;
- the effective pre-execution view changes from 146 open / 20 closed to
  145 open / 21 closed;
- the post-execution view remains 6 open / 0 closed; and
- every blocker, Formal Test, result slot, and execution gate keeps its prior
  state.

This receipt is an independent acceptance record only. It does not itself edit
the project timetable or evidence ledger and does not authorize runtime,
science, network access, external contact, data access, claim promotion, or
submission.

## 2. Exact reviewed package

All four files were reopened through their canonical project paths and were
regular, single-link `0644` files. Their exact bindings were:

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human record | `PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE.md` | 9,596 | `4d73909714e5227175b8c0f250876ffeddcd25ad9cc4d54b27d02499c562edfb` |
| Machine record | `research/fixtures/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json` | 12,639 | `c6275a6fb6941b28c2b0ed89196efdfeeba5530d8cabe47f173452cda364af54` |
| Read-only validator | `research/diagnostics/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py` | 33,938 | `817a64acaf2441314ad73190569bd969c304a9b1d01fc7533d7fdfc6dad1734b` |
| Hostile tests | `tests/unit/test_manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py` | 30,095 | `5ef4f22b71f24f980f9553c7e32f7de912ab85c23328b4d42019d2ae107e7693` |

The machine record is canonical duplicate-free ASCII JSON with one terminal
line feed. Its independently recomputed domain-separated semantic digest is
`ba1c3a7898c858ec7cf7b3073c869a134cd8a06b93aeb0f7778793c271c96d7b`,
exactly matching its embedded `record_sha256`.

## 3. Frozen predecessor verification

The review independently reopened every predecessor byte bound by the F104
validator. The four-file baseline capability/compute draft bindings were:

| Path | Bytes | Raw SHA-256 |
|---|---:|---|
| `PROJECT_BASELINE_CAPABILITY_COMPUTE_MODEL_DRAFT.md` | 10,754 | `33c9df737f45411861f2a60a9ed99220f61e4ac66461999ed0367c482b5dbe3d` |
| `research/fixtures/manuscript_v3_baseline_capability_compute_model_draft_v1.json` | 24,004 | `be7a96ab4898e89cf0167fcce48204142143bf071a194b24d480091a6c60530a` |
| `research/diagnostics/manuscript_v3_baseline_capability_compute_model_draft_v1.py` | 33,361 | `7032ad65de5b5f3f3aeed7e7d0b4866dbd318a3bc42850beeb9a1cfdd4a58297` |
| `tests/unit/test_manuscript_v3_baseline_capability_compute_model_draft_v1.py` | 20,209 | `2dbc64fd4830b410cda7c9911495cbfbf9603e4ec598f6af3e2094326a01cddc` |

The baseline machine semantic digest independently recomputes to
`4cad447dca7896d45c424ee16594cddf3cd83e8497ed0cb3ec875ced03dd5840`.

The five-file B05 current-count predecessor bindings were:

| Path | Bytes | Raw SHA-256 |
|---|---:|---|
| `src/heterodiff/evaluation/mixed_marked_ctmc_ou_known_law_certified_reference.py` | 124,895 | `98ffb1f42bee3efc097f378cc55a00b88f2d8570b9f3e8de1fe5f9a727f2e268` |
| `PROJECT_GATE_A_B05_KNOWN_LAW_DESIGN_FREEZE.md` | 13,766 | `ad03491578ba81c597906495f5aec5ceb36508cb9c0736f5f33af6d9babbc05d` |
| `research/fixtures/manuscript_v3_gate_a_b05_known_law_design_freeze_v1.json` | 269,205 | `c49ef829cab9c8a7459216d37cb70382d4c0027e20aa3c343c5fbd0ed825ee32` |
| `research/diagnostics/manuscript_v3_gate_a_b05_known_law_design_freeze_v1.py` | 33,523 | `d53a5656e4322e5b169bd859af531ea208ccaf413ddd9660a31c350d93cc2eb2` |
| `tests/unit/test_manuscript_v3_gate_a_b05_known_law_design_freeze_v1.py` | 18,517 | `052190e27ea71f06b1f93ba8df647867d813447464870c6e0f78c75f61b8524a` |

The B05 machine semantic digest independently recomputes to
`d81b52f94fe420b50f3aa5bf5d0edc97c5b55bdedf19c5bb9a8b499a23397e8b`.
It establishes the immediate predecessor view of 146 open and 20 closed
pre-execution fields, six open and zero closed post-execution fields, F104 in
the open roster, all 12 blockers open, no Formal Test closed, and no result
filled.

## 4. Formula and field-scope audit

The F104 machine value is byte-for-byte equal after canonical serialization to
the predecessor's `matched_compute_contract`. The human formula and the pure
calculator implement

`C[m,d] = sum_p sum_k n[m,d,p,k] * w[d,k]`,

with all four ordered phases and all ten ordered resource-event classes from
the predecessor. Counts are exact nonnegative built-in integers; weights are
strictly positive built-in integers or normalized `fractions.Fraction`
instances; booleans, floating-point values, subclasses, negative counts,
nonpositive weights, missing, extra, and reordered cells fail closed. The
4,096-bit input-component and 8,192-bit accumulated-component bounds are
enforced. The inherited synthetic vector replays exactly to phase costs
`4`, `20`, `31`, and `30`, with total exact cost `85`.

The formula retains the predecessor's calibration, fairness, attempt-charging,
nontransfer, no-top-up, shared-workload, and separate-hard-axis semantics. F104
owns that formula and those accounting semantics only. The package contains no
operand or resource value, so no other field is eligible for closure.

An independent roster calculation over F001--F172, with F164, F165, F168,
F169, F170, and F171 held as post-execution fields, confirmed:

- 166 pre-execution and six post-execution fields in total;
- the 20 exact predecessor closures;
- F104 as the sole successor closure;
- 21 closed and 145 open pre-execution fields afterward; and
- no change to any post-execution field.

## 5. Custody, mutation, and effect-surface audit

The validator performs stable no-follow reads, rejects noncanonical or escaping
relative paths, checks regular-file type, exact `0644` mode, one hard link,
descriptor/path identity and size stability, ancestor stability, exact byte
bindings, canonical duplicate-free JSON, predecessor semantic self-digests,
the current machine semantic self-digest, and the complete reconstructed
machine record.

Hostile qualification covered every current nonmachine package byte and every
predecessor byte; coherently redigested machine-record tampering; stale machine
self-digests; missing, extra, reordered, boolean, floating, negative,
zero-weight, subclass, and over-bound arithmetic inputs; noncanonical and
duplicate-key JSON; executable-mode, symlink, hard-link, and path-escape
substitutions; field/count drift; forbidden closure promotion; and effect-
surface exclusions. Mutations were confined to disposable test replicas.

Direct source inspection confirmed no project writer, network or connector
client, subprocess route, entropy source, project-science import, data access,
training route, runtime-capture route, production worker, or submission route.

## 6. Executed qualification

All qualification used Python bytecode writing disabled and pytest's cache
provider disabled.

| Working context | Qualification | Result |
|---|---|---|
| Project root | Canonical F104 validator entry point | `PASS`; semantic digest `ba1c3a7898c858ec7cf7b3073c869a134cd8a06b93aeb0f7778793c271c96d7b` |
| Project root | F104 hostile suite | `102 passed in 1.06s` |
| `/private/tmp` current working directory | F104 hostile suite against the canonical absolute package | `102 passed in 0.96s` |
| Project root | Frozen baseline-compute predecessor suite | `61 passed in 0.39s` |
| Clean `/private/tmp` replica containing exactly the 29 B05 package and predecessor files | Frozen B05 predecessor suite | `37 passed in 209.71s` |

One preliminary B05 run against the live workspace produced 36 passes and one
environment-cleanliness assertion because a Python-3.9 pytest cache file with
birth and modification time `2026-08-31 13:29:04 +0330` already existed before
this review. The cache file is not a bound F104 or B05 package byte and was not
created or modified by these cache-disabled Python-3.11 review commands. The
exact bound 29-file B05 roster then passed all 37 tests in the clean replica.
This is an isolated workspace observation, not a package finding.

## 7. Findings and preserved nonclosures

| Severity | Count | Disposition |
|---|---:|---|
| P0 | 0 | None |
| P1 | 0 | None |
| P2 | 0 | None |

The following remain expressly unclosed and unperformed:

- F062--F103, F139--F147, and F150--F162;
- all calibration weights, resource counts, budgets, ceilings, allocations,
  hardware/environment identities, capacity, and reservations;
- B06, B08, B12, and all 12 blockers;
- every Gate-A item not already independently closed by a predecessor;
- Formal Tests 28 and 29 (`OPEN`) and Formal Test 30 (`PENDING`);
- R1--R4 and all four result slots;
- network/contact/data/repository/license activity, operational receipts,
  scientific entropy, training, scientific or production execution, runtime
  authorization, claims, submission, and publication approval.

## 8. Independent acceptance boundary

The exact package receives `INDEPENDENT_REVIEW_GO`. A later tracker and
evidence-ledger reconciliation may register only F104 and the corresponding
146/20 to 145/21 pre-execution count transition. It must leave every listed
nonclosure unchanged and must cite both the exact four-file package and this
independent receipt. Any byte change to the reviewed four-file package or its
nine bound predecessor files invalidates this receipt and requires a fresh
independent review.
