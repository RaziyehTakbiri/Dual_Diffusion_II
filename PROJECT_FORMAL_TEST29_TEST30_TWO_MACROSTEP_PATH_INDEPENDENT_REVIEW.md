# Formal Tests 29–30 two-macrostep path independent review

**Review time (local, not externally attested):** 2026-08-31 23:14:52 +03:30  
**Verdict:** `GO_BOUNDED_DEVELOPMENT_PREDICATE_ONLY`  
**Predicate reviewed:**
`SYNTHETIC_SUPPLIED_INPUT_TWO_MACROSTEP_ROLLING_LINEAGE_PATH_VALIDATED`  
**P0 findings:** 0  
**P1 findings:** 0  
**P2 findings:** 1  
**Registration effected:** no  
**Project delta effected:** zero

## Decision

The exact candidate files and exact parent sources listed below support the
named bounded, synthetic, supplied-input predicate. Independent canonical
serialization reproduced all four published digests, the complete 1,024-case
ordered receipt, every published route/cardinality count, and both distinct
digest counts. Cache-disabled focused and parent regression suites passed.
Additional hostile checks rejected partial-preflight inputs before any Heun
arithmetic and rejected coherently redigested boundary and lineage forgeries.

This is a `GO` only for the exact reviewed development component. It is not an
evidence-ledger registration, production admission, operational receipt,
scientific result, formal-test closure, blocker closure, field closure, result
slot, submission gate, or timetable completion.

## Exact reviewed file receipts

The reviewed-file-set commitment is the SHA-256 of canonical ASCII JSON with
schema
`formal-test29-test30-two-macrostep-independent-review-files-v1`, key-sorted
objects, compact separators, and the following file rows in the displayed
order:

`b3d1f8d40a366d6c3961082cf9a69b5b402919ce820493c9676f782571bb5135`

| Role | Bytes | SHA-256 | Path |
|---|---:|---|---|
| Candidate source | 59,285 | `d1c3013aa0f4e7b31e19cef98d4aa5edf7991c5b8634dbfe091f8053b1808176` | `src/heterodiff/evaluation/formal_test29_test30_two_macrostep_path_qualification.py` |
| Candidate tests | 13,763 | `63940c0b2d8ffa5a714069df1c0942db0e7b98d1bd4f3a66b96d502e02d03b0f` | `tests/unit/test_formal_test29_test30_two_macrostep_path_qualification.py` |
| Candidate human record | 5,971 | `e00a55a923b63ad21076a582b7e1156c679a8dba7685ca1e55264aac3aa076aa` | `PROJECT_FORMAL_TEST29_TEST30_TWO_MACROSTEP_PATH_QUALIFICATION.md` |
| Single-macrostep parent | 61,434 | `e2f57ede06cb432f8507eb32eead7a77fbfc8d8d44cc7725a941182e7aedd0c7` | `src/heterodiff/evaluation/formal_test29_test30_single_macrostep_integration.py` |
| Test-29 parent | 52,186 | `308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089` | `src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py` |
| Test-30 parent | 42,349 | `373ef98c3605e0c0211da8dbc8782f2517cd5976026980e4fcd24435670839e0` | `src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py` |

Every listed file was hashed before the substantive executions and hashed
again afterward. All six post-execution receipts exactly matched their
pre-execution receipts. A mismatch would have produced `HOLD`; none occurred.

## Independent exhaustive recomputation

The review independently rebuilt the canonical input, path-report, and
qualification-report JSON payloads. It did not call the candidate's private
canonical-digest or payload-construction helpers. For every ordered pair
`(first_word, second_word)` in `{0, ..., 31} x {0, ..., 31}`, the independently
serialized input and report digests matched the returned contextual digests.

- ordered cases: 1,024;
- distinct canonical input digests: 1,024;
- distinct contextual report digests: 1,024;
- ordered-case commitment:
  `3273b1c5e553093a3d5a35f4e7686b018363ac609bb300dd6dbb87f66daf7591`;
- aggregate qualification-report digest:
  `2a278585373d017b3b60bed28dcbc0ab3830f72c0512891658fc2ab54c666d53`;
- default `(2, 27)` input digest:
  `11decfb2a16606b69404958d2e7cac2b75808f78adc00ab8c562da8f993ece8e`;
- default `(2, 27)` contextual report digest:
  `9c66342668b2225cbe5d8705a175dd857fd1aa9d2411bbeea489a41e884b7c94`.

The independently recomputed route-family counts were:

| Ordered route pair | Count |
|---|---:|
| birth→birth | 256 |
| birth→death | 128 |
| birth→replacement | 128 |
| death→birth | 128 |
| death→death | 64 |
| death→replacement | 64 |
| replacement→birth | 128 |
| replacement→death | 64 |
| replacement→replacement | 64 |

The independently recomputed step-boundary cardinality counts were
`((1, 256), (2, 256), (3, 512))`. The final-cardinality counts were
`((0, 64), (1, 128), (2, 320), (3, 256), (4, 256))`.

The five declared low bits are exactly the parent layout's two route bits,
two source bits, and one one-dimensional normal-cell bit. Therefore 32 words
per step exhaust the declared low-residue domain rather than sampling it.

## Hostile review evidence

The source and dynamic checks covered the requested failure classes:

- **Lineage and address aliasing:** exact CP23/CP24 types, tag-specific keys,
  step indices, occurrence serials, proposal ordinal, canonical counters,
  source selection, active/retired disjointness, and monotone fresh serials
  are revalidated at the input boundary. Address identities are checked for
  uniqueness across both steps and tags 4, 5, and 6.
- **Partial-preflight effects:** six additional hostile inputs were exercised:
  wrong-step second CP24 word, second-step CP23 address reuse, reordered
  first-step left roster, extra second-step right item, forged first step
  index, and wrong step cardinality. All 6/6 were rejected with exactly zero
  calls to the patched Heun arithmetic function.
- **Step-boundary forgeries:** a coherently modified and redigested shared
  boundary coordinate was rejected by contextual reconstruction.
- **Lineage forgeries:** a coherently modified and redigested source serial
  was rejected by contextual reconstruction.
- **Source order and cardinality:** every increment roster is compared in
  exact expected serial order and with exact cardinality before execution;
  missing, extra, reordered, cross-step, and wrong-length cases fail closed.
- **Empty terminal roster:** the death→death case safely reaches zero active
  coordinates and performs zero right-Heun applications in the second step.
- **Hidden effects:** AST inspection of the candidate source and all three
  executed parent sources found zero imports or call surfaces for RNG,
  entropy, network, subprocess, filesystem reads/writes, tracker mutation, or
  dynamic execution. The component run used supplied values only.
- **False closure:** all broader-claim flags remained false and every project
  delta counter remained zero in both path and aggregate reports.

## Cache-disabled regression evidence

Runtime: Python 3.9.13 and pytest 7.1.2. Python bytecode writes and the pytest
cache provider were disabled for the reported commands.

Focused command:

```text
PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider -q \
  tests/unit/test_formal_test29_test30_two_macrostep_path_qualification.py
```

Result: `15 passed in 11.44s`.

Candidate plus exact-parent regression command:

```text
PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider -q \
  tests/unit/test_formal_test29_test30_two_macrostep_path_qualification.py \
  tests/unit/test_manuscript_v3_formal_test29_test30_single_macrostep_integration_v1.py \
  tests/unit/test_formal_test29_finite_acyclic_route_oracle.py \
  tests/unit/test_manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.py
```

Result: `265 passed in 65.56s`.

## Findings

### P0

None.

### P1

None.

### P2-01 — Parent admission is review-bound, not intrinsic to the public API

The candidate's `_require_parent_modules` boundary requires exact
`ModuleType` objects, expected schema strings, and required symbol presence,
but it does not itself hash-authenticate module source or reject a coherently
rebound schema-compatible symbol implementation. This review closes that gap
only for this exact review execution by hard-pinning and stable-reading the
three parent sources above.

This is nonblocking for the named bounded predicate because the report
explicitly sets `parent_custody_authenticated=False`, the human record already
states that parent custody is not established, and no registration is being
performed. A reusable admission/registration package must still check the
exact parent receipts before importing or executing them and fail closed on
any mismatch.

## Preserved nonclosures

This review does not establish any of the following:

- a Test-28 initializer, initializer admission, tag-3 coordination, or live
  source;
- a Brownian, Gaussian, independence, uniform-word, or source law;
- a continuous Gaussian destination sample;
- a waiting clock, acceptance/rejection, thinning, or zero/multiple-edit
  jump-substep law;
- an arbitrary-length or production Strang path;
- a coupled step-halving study, endpoint-law result, learned/native drift, or
  independent scientific recomputation;
- candidate-intrinsic parent custody authentication, production runtime
  custody, data access, protected inputs, operational receipts, authority
  expansion, attempt-budget expenditure, or scientific execution;
- a closed field, blocker, result slot, formal test, submission gate,
  operational task, or timetable task.

Formal Test 28 remains `OPEN`, Formal Test 29 remains `OPEN`, and Formal Test
30 remains `PENDING`. The project delta remains exactly zero.

## Tracker and ledger preservation

This review process wrote only this independent-review record. It did not edit
`PROJECT_COMPLETION_TIMETABLE.md` or `PROJECT_EVIDENCE_LEDGER.md`. Those two
files changed concurrently in the shared workspace during this review, so
they are deliberately excluded from the stable reviewed-file set above and
this receipt makes no claim about their changing contents.

The pre-receipt observations were, respectively:

- `6dc3e88db9687194b1e42a352f932837e51b9a9c96db37539ed337536151b3f7`;
- `edb054100e55d2bf73a9a814d57ff9b63b40d5b57b279b73bd0f64fe962dc56c`.

The immediate post-creation observations were, respectively:

- `45dad5bda67c30172e20cd9cca850136931d726320654dc1f17a98054a6d3aa1`;
- `92cc1ffd0fc8191aea44adda4f9d2616190d236346b3b8eda13c060dce5a3eaa`.

All six candidate/parent files in the reviewed-file commitment remained
stable across the same interval.
