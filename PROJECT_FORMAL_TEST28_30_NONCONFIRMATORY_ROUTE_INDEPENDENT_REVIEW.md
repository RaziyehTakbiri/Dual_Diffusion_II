# Independent review — Formal Test 28–30 nonconfirmatory route

## Decision

**NO-GO for the proposed timetable registration.**

Final finding counts are **P0/P1/P2 = 0/1/0**.

The sealed route package is mechanically reproducible, hash-first, and honest
about the distinction between the historical CP63 execution and the fresh
Test-29/Test-30 supplied-input execution.  Its exact validator, focused hostile
suite, copied-package validation, and bounded dependency suite all pass.

The package nevertheless cannot authorize the exact existing checkbox:

> Required Tests 28–30 routes run end to end on nonconfirmatory/synthetic
> inputs.

The aggregate receipt materially relies on the sealed whole-method component
as the data-flow integration joining the Test-28 initializer/sampler to the
Test-29/Test-30 path.  That component now has an independent sealed NO-GO/P1:
the selected Test-28 configuration is only a sibling summary, never becomes or
binds the path initial state, and the path explicitly retains
`test28_initializer_admissible=False`.  Cryptographically joining that rejected
receipt to two individually valid route receipts does not establish an
end-to-end method route.

This review therefore authorizes **zero** timetable changes.  Formal Test 28
remains `OPEN`, Formal Test 29 remains `OPEN`, and Formal Test 30 remains
`PENDING`.  No candidate, tracker, ledger, field, blocker, result, runtime,
data, training, science, production, or authority record was edited.

## Exact reviewed package

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human candidate | `PROJECT_FORMAL_TEST28_30_NONCONFIRMATORY_ROUTE_CANDIDATE.md` | 8,266 | `0bb2337e2100f9e8efdd5948d6655f382103514b2f11871ead1e2c9eef3ce5f6` |
| Route source | `src/heterodiff/evaluation/formal_test28_30_nonconfirmatory_route.py` | 41,184 | `aabbea24156c63d833beaa7fe1a29d2c4879a8a0cbd0d171ec0ca558d3a34a32` |
| Canonical machine record | `research/fixtures/manuscript_v3_formal_test28_30_nonconfirmatory_route_candidate_v1.json` | 8,841 | `971f337f7e01be99372a7308c4036551c3660b11bb3d9a7a70487e88146cffe2` |
| Hash-first validator | `research/diagnostics/manuscript_v3_formal_test28_30_nonconfirmatory_route_candidate_v1.py` | 18,685 | `b3d35678f7e0cccd3c498fca2e88c0bc5b48a01ea2517a38ffa87c71168af001` |
| Focused hostile tests | `tests/unit/test_formal_test28_30_nonconfirmatory_route.py` | 16,290 | `22b044a949f6c622eb5ec76a30a1ab5585ad410559a096d216e056c4c4c43425` |

The canonical machine self-record is
`96e3b976603a42f559846e1b611ba410c6eea02d9e5c44c3e5de6f68d0360491`.
The aggregate route receipt is
`f26767444a3df2d5e7d353cf3930e806412902d6e837134a9f6dc821663740a8`.

The material predecessor pins reviewed here include:

- CP63 accepted fixture: 7,087,027 bytes, SHA-256
  `7faed3c5b07415fbc45fec02d026e36d465819a38e9187369bf0a42a91c29f68`;
- CP63 runner source: 83,080 bytes, SHA-256
  `27259edf2557a21b2527595eed7a954fc697755935e4a3deaeeb169765ba1c9c`;
- CP63 independent recomputation source: 94,515 bytes, SHA-256
  `5df076a008d8fe6848dc72083e2563e622c136ce0159441dd69db04c3b1cb9dc`;
- Test-29/Test-30 hash-first wrapper: 12,105 bytes, SHA-256
  `e71f145bc73b47a8d6a19329e05989523d0ca14d5726c4b02a8ec0e07f9a455e`;
  and
- whole-method machine receipt: 9,789 bytes, SHA-256
  `a5debbc0db537993191c1554529fdf52e34ace80a92cb24a3555889a11f0490b`,
  stable public receipt
  `677aedeac9fe02a3bac9a14316c2c1f1a0047d6839e9c7492063d344b5e93220`.

The whole-method independent NO-GO review is
`PROJECT_B12_WHOLE_METHOD_NONCONFIRMATORY_RUNNER_INDEPENDENT_REVIEW.md`,
10,598 bytes, SHA-256
`c4562cfc00b5c000f4aeb0f9e850ea7367806287ef0ef271f24e901e7ea54928`.

## Independent reproduction

The standalone validator passed from the project root with the exact machine
self-record and aggregate route receipt above.  A minimal physical copy in an
unrelated `/private/tmp` directory also passed using only copied package and
predecessor files.  Replacing its intermediate `src` directory with a symlink
failed closed before any candidate source could be trusted.

The exact test totals reproduced independently were:

- focused route hostile suite: **40/40 passed**;
- bounded predecessor compatibility suite: **105/105 passed**; and
- total focused plus compatibility checks: **145/145 passed**.

The 105-test compatibility roster was the accepted CP63 independent
recomputation suite, the hash-first Test-29/Test-30 parent-custody suite, and
the whole-method runner suite.  These mechanical results establish that the
route package faithfully reproduces its sealed inputs; they do not turn a
semantically rejected predecessor into accepted end-to-end evidence.

## Component findings

### CP63 Test-28 binding — mechanically accepted and truthfully historical

The route verifies the full CP63 fixture raw hash before semantic extraction,
pins both runner and independent-recomputation sources, verifies the
domain-separated acceptance receipt, and enforces the ordered roster of 16
rows with two repetitions per row.  It binds exactly 32 launches and 554
estimands, partitioned into 72 observable, 170 rejection-first-attempt, and 312
selected-feature estimands.

The route truthfully sets
`historical_nonconfirmatory_execution_receipt_revalidated=True` and
`fresh_execution_performed_here=False`.  It does not relaunch CP63 under a
different runtime or misdescribe historical receipt validation as a fresh run.
This component has no review finding.

### Test-29/Test-30 path — freshly executed on the bounded 1,024 cases

The exact captured wrapper and four captured parent sources are compiled from
their pinned bytes.  The wrapper executes the ordered supplied-input
two-macrostep qualification and internally requires 1,024 checked cases,
1,024 distinct input digests, 1,024 distinct report digests, and report SHA-256
`2a278585373d017b3b60bed28dcbc0ab3830f72c0512891658fc2ab54c666d53`.
It reopens the sources after qualification and fails closed on custody drift.

The aggregate route truthfully sets `fresh_execution_performed_here=True` for
this component and `confirmatory_evidence=False`.  Formal Tests 29 and 30 are
not closed.  This component has no review finding.

### Whole-method binding — exact bytes, rejected semantics

The route exactly captures the whole-method machine receipt and checks its
eight-field compact binding: receipt schema and digest, supplied-input digest,
19 implementation obligations, 50 open residual slots, independent-byte
parity, separate execution/validation, and `confirmatory_evidence=False`.

That is a valid byte-level binding, but the bound predecessor is not accepted
whole-method integration evidence.  Its independent review demonstrated that:

1. the sampler selects configuration digest
   `c9450132be2800eddc7e8e36547c49e8b7839e1e282e32f0736b453267b92b06`;
2. the selected configuration remains confined to the initializer/sampler
   subtree;
3. the path is separately constructed from its frozen synthetic occurrence
   words and receives no selected configuration, transform policy, or derived
   initial-state digest; and
4. the path is accepted only while `test28_initializer_admissible=False`.

The Formal-route human candidate expressly describes this predecessor as
composing the Test-28 initializer/sampler with the Test-29/Test-30 path.  The
executable data flow does not support that statement.  This is not a missing
production result; it is a missing method edge in the synthetic route itself.

## P1-01 — aggregate binding is not end-to-end integration

The aggregate route receipt strongly binds three component identifiers and
their stable receipts, so deletion, reordering, or substitution changes or
invalidates the aggregate digest.  However, receipt aggregation is not a
typed data-flow edge.  CP63's accepted Test-28 execution and the fresh
Test-29/Test-30 path remain disjoint rehearsals, while the package's designated
whole-method bridge is independently NO-GO for the exact missing edge between
them.

The timetable checkbox uses “run end to end.”  Under that wording, three
sibling receipts cannot substitute for a route in which the selected
initializer configuration deterministically becomes the path initial state.
Authorizing the checkbox would therefore overstate what these bytes execute.

This is P1 because it directly affects the only proposed timetable closure.
It does not invalidate the historical CP63 receipt, the fresh 1,024-case
two-macrostep execution, their nonconfirmatory use, or the package's hash-first
custody mechanics.

## Exact successor criterion

A successor may remain entirely offline, deterministic, supplied-input, and
nonconfirmatory.  To become eligible for this exact checkbox it must:

1. bind a repaired whole-method successor that deterministically transforms
   the exact Test-28 selected configuration into the path initial state;
2. bind the selected-configuration digest, transformation policy,
   derived-initial-state digest, path-input digest, and path-report digest in
   one recomputable custody chain;
3. have the separate recomputation independently reconstruct that same
   initializer-to-path edge;
4. truthfully replace `test28_initializer_admissible=False` only after the
   actual selected initializer output is validated at the path boundary;
5. receive an independent GO for that repaired whole-method successor;
6. reseal the Formal-route source, human record, machine receipt, validator,
   and hostile tests against the repaired whole-method machine and stable
   receipt; and
7. add hostile tests proving that omission, substitution, or alteration of
   the selected configuration, transform, or derived initial state either
   changes the route receipt deterministically or fails closed.

The successor must preserve the truthful CP63 boundary
`fresh_execution_performed_here=False`, must freshly execute and verify all
1,024 Test-29/Test-30 supplied-input cases, and must preserve every current
nonclaim and zero applied delta.  It need not run production data, issue a
confirmatory receipt, or close any Formal Test.

## Exact authorization and unchanged state

This review's exact authorization is:

- `Required Tests 28–30 routes run end to end on nonconfirmatory/synthetic inputs.`
  — **not authorized; remains open**.

All applied deltas are zero:

- timetable checkbox delta: **0**;
- Formal-Test delta: **0**;
- field delta: **0**;
- blocker delta: **0**;
- result-slot delta: **0**;
- B12 delta: **0**;
- runtime/data/network/entropy/science/training/authority delta: **0**;
- tracker edits: **none**; and
- evidence-ledger edits: **none**.

Formal Test 28 remains `OPEN`, Formal Test 29 remains `OPEN`, and Formal Test
30 remains `PENDING`.  No production receipt, scientific conclusion,
manuscript claim, or release decision follows from the candidate or this
review.
