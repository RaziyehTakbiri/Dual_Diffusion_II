# Independent review: B12 integrated offline evidence-contract package

**Review date:** 2026-09-01  
**Decision:** `GO_B12_PARTIAL_EVIDENCE_CONTRACT_INDEXING_ONLY`  
**Findings:** P0 = 0; P1 = 0; P2 = 0  
**Boundary:** internal exact-byte engineering review only; no runtime, data,
scientific, Formal-Test, field, blocker, or timetable-task acceptance

The prior same-path review (SHA-256
`1608fe49101ff12b6a26fe0d73d425690fbd0786e7c47be4264b97a6f33887fc`)
was never registered. It was invalidated when a later hostile audit found that
duck-typed adapter and predicate members could reach method calls before exact
concrete-type rejection. This document replaces it and binds only the new
bytes below.

## Exact reviewed bytes

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `PROJECT_B12_INTEGRATED_OFFLINE_IMPLEMENTATION_GAP_PACKAGE.md` | 2,414 | `421ee28c8e4cf6e886e22759518fb8bfd125bf46891a42fbdecd8d7f589a9b95` |
| `src/heterodiff/evaluation/b12_integrated_offline_candidate.py` | 14,944 | `b77c6eea6859fa9d6181a94a27112d97555e5a4d60ab1df1ee03a30c7808defd` |
| `research/fixtures/manuscript_v3_b12_integrated_offline_gap_package_v1.json` | 8,755 | `825cfde8412474eba97dea4a4d2fb92fa8af99568ebeada05f6b33b71fcc680c` |
| `research/diagnostics/manuscript_v3_b12_integrated_offline_gap_package_v1.py` | 5,479 | `0e44f7f2022b8fe505006f1292f923f7fa5ab4e79f58b68cc6cd5b4ddd0ca2e9` |
| `tests/unit/test_manuscript_v3_b12_integrated_offline_gap_package_v1.py` | 11,579 | `10d9c98880e8818cfffd860cac8690732e6e5354a68a4cc18dd244a5e47a3dd7` |

All five were regular `0644` single-link files. Any byte change invalidates
this review. The independently reproduced semantic SHA-256 is
`c5196b6bf3b7cfa2055aaeeb50d990bc3263d4e304fcfdbce3d11b2a3245b545`;
the machine-record SHA-256 is
`5a37e70e4257e232205d7c6a4e30f342d45c4457596bdff5e59b5e7017c9b834`.

## Verification results

- Standalone hash-first validator: PASS; all 12 bound files were verified by
  stable no-follow descriptors before the captured source bytes were compiled
  and interpreted.
- Focused package, custody, semantic, and hostile suite: 23/23 passed.
- Relevant B06, F104, F105-production-integration, and Formal-Test-29/30
  predecessor regressions: 256/256 passed.
- Independent alias/roster/effect replay: PASS with exact private canonical
  snapshots of 50 residual predicates and 22 adapter rows.

## Prior-issue dispositions

The residual roster is now exactly 50 unique entries and includes
`TRAINING_CHECKPOINT_PLAN_F139_F144_F147_COMPLETE_AND_INTEGRATED`. Rebinding
the public `RESIDUALS` or `REQUIRED_ADAPTER_ROSTER` aliases does not alter
`semantics()`, `evaluate(None)`, or runner validation, which use private
canonical snapshots.

Runner validation now checks every adapter member is exactly
`AdapterReceipt` and every residual member is exactly
`AuthenticatedPredicateReceipt` before reading attributes or invoking methods.
Independent hostile replay confirmed rejection of duck objects and subclasses
on both surfaces; neither can impersonate a receipt or influence canonical
evaluation.

Every adapter receipt now carries separate `config_sha256` and
`implementation_source_sha256` fields. The configuration value is matched
against the exact 22-row B06 identity/domain/configuration roster; the future
implementation/source digest must be nonzero. Both values, the adapter
identity and domain, and input/output digests are included in the authenticated
adapter subject. The CSDI and EditPP four-plus-four author-extension predicates
remain separate from their two external adapter identities.

The complete runner requires exact concrete receipt types, the full ordered
adapter roster, a nonempty paired and chained immutable INTENT/OUTCOME ledger,
all 50 ordered residual receipts, and an independent recomputation receipt.
The recomputation execution subject binds the capsule manifest, all 22 ordered
adapter subjects, and every ordered ledger-event digest. Runner residuals bind
the resulting runner subject. Boolean claims, omitted/duplicate/reordered
rows, mutable lists, source/record mismatches, unsupported fields, wrong
counts, noncanonical machine JSON, and path/mode/link/custody substitutions
fail closed.

F142 remains only an open method-and-domain-adapter-defined batching
condition. F144 remains only an open candidate validation contract. F139--F144
and F147 remain open; F145/F146 are not reasserted by this package.

## Registration and nonclosure

The candidate names no exact timetable project-control registration predicate.
Therefore **no timetable checkbox is eligible to be checked** from this
review. The review permits only partial-evidence indexing of these exact bytes.

Field delta, blocker delta, Formal-Test delta, result delta, runtime/data/science
delta, and authority delta are all zero. B12 remains open; Formal Tests 28 and
29 remain OPEN, Formal Test 30 remains PENDING, and no result or scientific
claim is produced. The timetable and evidence ledger were not edited.
