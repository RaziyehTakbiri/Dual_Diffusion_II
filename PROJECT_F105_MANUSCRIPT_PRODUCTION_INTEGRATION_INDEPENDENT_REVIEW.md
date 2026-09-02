# Independent review — F105 manuscript-display and production-evaluator integration

**Review date:** 2026-09-01  
**Disposition:** `GO`  
**Severity count:** `P0=0`, `P1=0`, `P2=0`  
**Accepted state:** `F105_MANUSCRIPT_DISPLAY_AND_PRODUCTION_EVALUATOR_INTEGRATED_PREOUTCOME`

## 1. Reviewed bytes

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Human integration record | `PROJECT_F105_MANUSCRIPT_PRODUCTION_INTEGRATION.md` | 7,358 | `954d914459362d6690028b93c3fa2c84fc37aeb2954e073a6c578bc3b812220a` |
| Production evaluator | `src/heterodiff/evaluation/two_domain_count_normalized_event_cks_production.py` | 21,619 | `42a023483816c391c1ba0e9d8bfb23c36d10d74d0ed55901727cda790c2f15ad` |
| Focused production tests | `tests/unit/test_two_domain_count_normalized_event_cks_production.py` | 8,782 | `bb259c370fcee1d1b21b08ab98903072d394e49510e7bc4a4a054017ed9557b4` |
| Markdown metric successor | `manuscript_v3/manuscript_v3_f105_metric_integration_successor_v2.md` | 6,355 | `65c852f669ea08f4993da2e8b3b427d864fffba8ae59a303a8722146edad78d2` |
| TeX metric successor | `manuscript_v3/manuscript_v3_f105_metric_integration_successor_v2.tex` | 3,812 | `558ab5f0067ebfe5cd08be615d03859415c400638688cfd54e9c8e0c3dbdbf56` |
| Additive claim boundary | `manuscript_v3/claim_ledger_f105_metric_integration_successor_v2.md` | 1,968 | `c373bd7fab96666de4b20870b41abdfa1d24c0e52e9de87e5e497a414bfebb80` |
| Machine integration record | `research/fixtures/manuscript_v3_f105_manuscript_production_integration_v1.json` | 5,495 | `251edc5792dd5545c40eb45ec528f98b133a0b154f5d0f5ef3bb3db4df325126` |
| Read-only validator | `research/diagnostics/manuscript_v3_f105_manuscript_production_integration_v1.py` | 19,071 | `1513686d2b2c7372129a1683d3443e1e1fe77e43460fb83a089a7c1a72efa6ae` |
| Package and custody tests | `tests/unit/test_manuscript_v3_f105_manuscript_production_integration_v1.py` | 8,326 | `2a04a35913ea6e0b20c739a518ca3fc8a089c1aac0f13a078cc425582e98728d` |

The independently recomputed machine semantic digest is
`6c5480374ed3d1993e28711ef8640d8f12c0cadf40a51e0ce7d8991f5233f5ae`.
It equals the embedded digest and the validator constant. The six non-self
package bindings match their current byte counts and hashes. The human table's
explicit Markdown, TeX, and claim-ledger bindings also match the same bytes.

All nine reviewed files are regular mode `0644` files with link count one and
terminal LF. The validator and its package tests are deliberately outside the
machine record's semantic self-binding; this receipt accepts them only at the
exact hashes above.

## 2. Frozen predecessor inputs

| Role | Path | Bytes | Raw SHA-256 |
|---|---|---:|---|
| Exact F105 source | `src/heterodiff/evaluation/two_domain_count_normalized_event_cks.py` | 25,342 | `567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881` |
| Exact F105 machine record | `research/fixtures/manuscript_v3_f105_two_domain_cks_metric_instance_v1.json` | 23,899 | `560b6275a4e30d188cc35ed8190118ba01ad8fc3bacc9199daf5b6f305cc96c9` |
| Historical locked-route predecessor | `manuscript_v3/manuscript_v3_locked_route_successor_v1.md` | 16,351 | `e06cb6780974dea98b85df03c04104b034bfcf4bdd7b3825d9b375d6983849db` |

The independently rerun exact-F105 validator returns semantic digest
`14cefa1f0b8e300c26373a9ffdfc01ede99f783a326feb78c68166d187168b52`.
No predecessor byte changed during this review.

## 3. Independent semantic and implementation review

The Markdown and TeX successors agree with the frozen exact source on the
count-plus-normalized-event embedding, empty-event convention, unit squared
parameters, Gaussian event and configuration kernels, ordered-pair
U-statistic, lower-is-better direction, positive direct-minus-guide
orientation, supported formal `2 <= R <= 128` domain, exact PhysioNet
`R^112` map, exact Retail `R^10` map, horizons, caps, and cross-domain refusal.
The successors do not promote source-documentation observations into snapshot,
license, governance, admission, runtime, or scientific receipts.

The production evaluator imports the frozen exact primitives and constructs
the same canonical `FormalCKSScore`. It performs only exact symbolic
construction followed by a finite binary64 projection. It performs no parser
operation, I/O, network access, random draw, fitting, training, threshold
decision, or scientific execution.

The initial red team exposed record-construction, audit-field mutation,
comparison work-ceiling, unrelated-working-directory, human binding-table,
and custody weaknesses. Every issue was repaired before this receipt:

1. score and comparison records are factory-only through the supported API;
2. normal `dataclasses.replace` construction is refused;
3. the formal digest, binary64 value and hex, paired effect, child score
   records, and a domain-separated digest over every public audit field are
   revalidated;
4. post-issuance mutations of domain, draw count, work count, provenance,
   numeric value, direction, or comparison fields are refused;
5. the caller-visible comparison ceiling is applied to combined
   direct-plus-guide symbolic work and refuses before any kernel evaluation;
6. package tests collect and pass from an unrelated working directory; and
7. the validator rejects noncanonical or symlinked roots, symlinked ancestors
   and leaves, hardlinked leaves, and unstable root/ancestor/leaf identities.

The construction seal and integrity digest are correctly described as
in-process misuse guards, not signatures or substitutes for execution custody.
No unresolved P0, P1, or P2 finding remains.

## 4. Qualification receipts

- The standalone integration validator passes from the project root and from
  `/private/tmp`, returning the accepted state, six bindings, zero field and
  blocker deltas, and semantic digest
  `6c5480374ed3d1993e28711ef8640d8f12c0cadf40a51e0ce7d8991f5233f5ae`.
- The focused production plus package/custody suite passes `49/49`.
- The expanded production, integration, exact-F105, generic theorem, and
  reference-implementation suite passes `326/326`.
- The production, integration, and exact-F105 suite passes `92/92` when
  collected from the unrelated `/private/tmp` working directory.
- An independent deterministic equivalence matrix passes `642/642` cases
  across both domains, empty configurations, duplicates, small `R`, and
  `R=128` boundary witnesses. Every production formal score equals the frozen
  public exact API and every binary64 value equals projection of that exact
  score.
- A separate hostile matrix refuses mutations of all score and comparison
  public fields, mutated child records, both public constructors, and normal
  `dataclasses.replace` attempts. The combined-work boundary refuses total
  work `18` under limit `17` before a kernel call and accepts the exact limit
  `18`.

These receipts use only synthetic exact configurations and read-only package
inspection. They do not open a dataset, execute a real parser, generate
entropy, train or evaluate a model, fill a scientific result, or establish
runtime or data custody.

## 5. Later R64 successor boundary

This receipt accepts the self-contained F105 integration against its frozen
predecessors. The general production evaluator's `2 <= R <= 128` domain is
compatible in principle with a later additive confirmatory successor that
narrows F109 to exactly `R=64`; the general engine need not falsely reject its
other theorem-supported values.

The later F109--F112 statistical package is not accepted or content-bound by
this receipt. It must independently bind this accepted package and this review,
enforce the exact R64 and pairing contract at its production-facing boundary,
and receive its own independent audit. Until then, the earlier statement that
F109--F112 and B04 remain open is exact for this immutable package checkpoint.
This one-way dependency avoids making F105 acceptance circularly depend on its
later successor.

## 6. Accepted closure and nonclosure

Acceptance closes exactly the bounded timetable predicate
`F105_MANUSCRIPT_DISPLAY_AND_PRODUCTION_EVALUATOR_INTEGRATED_PREOUTCOME`.
Its field-count, blocker-count, Formal-Test-count, and result-count deltas are
all zero: F105 and the necessary domain-schema fields were already closed by
the exact-instance predecessor.

At this package checkpoint F109, F110, F111, and F112 remain open; B04 and all
other blockers remain open; no Formal Test or result closes. Neither domain is
admitted. Data access, authentication, contact, license/governance approval,
privacy approval, entropy, runtime, capacity, training, science, claims, and
submission remain absent or outside this receipt.

## 7. Lifecycle

This review accepts only the exact bytes in Sections 1 and 2 and the exact
bounded closure in Section 6. Any later change to a reviewed byte, formula,
event map, production record, resource rule, machine semantics, validator, or
test invalidates this receipt and requires a new content-addressed package and
fresh independent review. Ledger and timetable registration may cite this
receipt but must not expand its closure or authority boundary.
