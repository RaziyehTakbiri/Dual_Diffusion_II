# F105 manuscript-display and production-evaluator integration

**Date:** 2026-09-01  
**Schema:** `heterodiff-f105-manuscript-production-integration-v1`  
**State:** `F105_MANUSCRIPT_DISPLAY_AND_PRODUCTION_EVALUATOR_INTEGRATED_PREOUTCOME`  
**Primary metric:** `TWO_DOMAIN_COUNT_NORMALIZED_EVENT_CKS_V1`  
**Production projection:** `F105_CKS_BINARY64_PROJECTION_V1`

## 1. Scope and outcome

This additive package completes the broader F105 task left open by the exact
two-domain instance:

1. the current manuscript now displays the exact count-plus-normalized-event
   embedding, both domain event maps, all unit squared parameters, the
   configuration kernel, U-statistic score, and direct-minus-guide direction;
2. an executable production evaluator imports the frozen F105 exact source,
   constructs the same formal score, emits a deterministic binary64 projection,
   and records exact formal provenance; and
3. hostile tests bind the display, source, exact/formal equivalence, both
   domains, direction, resource refusal, and output records.

The frozen historical manuscript and locked-route v1 successor remain
unchanged. The v2 display is a one-way additive override of only their stale
F105/CKS statements.

## 2. Exact package

| Path | Role | Bytes | SHA-256 |
|---|---|---:|---|
| `src/heterodiff/evaluation/two_domain_count_normalized_event_cks_production.py` | production evaluator | recorded by the machine package | recorded by the machine package |
| `tests/unit/test_two_domain_count_normalized_event_cks_production.py` | focused hostile tests | recorded by the machine package | recorded by the machine package |
| `manuscript_v3/manuscript_v3_f105_metric_integration_successor_v2.md` | current Markdown metric display | 6,355 | `65c852f669ea08f4993da2e8b3b427d864fffba8ae59a303a8722146edad78d2` |
| `manuscript_v3/manuscript_v3_f105_metric_integration_successor_v2.tex` | current TeX metric display | 3,812 | `558ab5f0067ebfe5cd08be615d03859415c400638688cfd54e9c8e0c3dbdbf56` |
| `manuscript_v3/claim_ledger_f105_metric_integration_successor_v2.md` | additive claim boundary | 1,968 | `c373bd7fab96666de4b20870b41abdfa1d24c0e52e9de87e5e497a414bfebb80` |
| `PROJECT_F105_MANUSCRIPT_PRODUCTION_INTEGRATION.md` | this human record | self | recorded by the machine package |
| `research/fixtures/manuscript_v3_f105_manuscript_production_integration_v1.json` | canonical machine record | self | semantic self-digest |
| `research/diagnostics/manuscript_v3_f105_manuscript_production_integration_v1.py` | read-only package validator | outside semantic self-binding | qualification-only |
| `tests/unit/test_manuscript_v3_f105_manuscript_production_integration_v1.py` | package/hostile validator tests | outside semantic self-binding | qualification-only |

The package also pins, without modifying:

- the exact F105 source SHA-256
  `567b0262ff8950b3ab297ce08137e89fa3e09d0953f559a4d9470cab1760f881`;
- the exact F105 machine-record raw SHA-256
  `560b6275a4e30d188cc35ed8190118ba01ad8fc3bacc9199daf5b6f305cc96c9`;
- the exact F105 machine semantic digest
  `14cefa1f0b8e300c26373a9ffdfc01ede99f783a326feb78c68166d187168b52`;
- the generic theorem and reference implementation through the accepted F105
  package; and
- the locked-route v1 successor as historical predecessor text.

## 3. Production code-match

The evaluator accepts only exact `ExactConfiguration` values from the frozen
F105 source. It does not duplicate a domain parser or event map. It constructs
the exact `FormalCKSScore` by the same public `configuration_kernel` primitive,
with a symmetric call cache that changes no coefficient or term. Tests compare
the result to the frozen `conditional_cks_score` API in both domains.

Each configuration-kernel symbol has the exact form

`exp(-(c + sum_j alpha_j exp(-q_j)))`.

The production layer projects this expression only at its exponential and
finite-sum boundary. It refuses a materially negative projected squared
distance, nonfinite output, cross-domain input, mismatched direct/guide draw
count, an F105-invalid draw count, or a symbolic-event-pair work request above
the caller-visible ceiling. The default work ceiling is exactly 10,000,000 and
the maximum caller-selected ceiling is exactly 1,000,000,000.

Each score returns:

- exact metric and integration IDs;
- domain and draw count;
- the complete exact `FormalCKSScore`;
- a canonical SHA-256 of that formal score;
- the finite binary64 score and its hexadecimal representation;
- the exact lower-is-better direction; and
- the precomputed symbolic work count.

The comparison API requires matched draw counts and returns
`score_direct - score_guide`; positive favors the guide. Its caller-visible
work ceiling applies to the combined direct-plus-guide request, not separately
to each arm.

Both audit-record classes are factory-only through the supported public API.
Their validation recomputes the formal digest, binary64 score, score hex,
bound score objects, direct-minus-guide effect, and a domain-separated
integrity digest over every public audit field before serialization or return.
This detects post-issuance changes to domain, draw count, formal provenance,
numeric result, direction, or work count. The construction seal and integrity
digest are in-process misuse guards, not signatures or substitutes for
file/runtime custody.

## 4. Manuscript code-match

The Markdown and TeX displays contain the exact formulas implemented by the
frozen source:

- `Phi_d(x)=(n_x,m_d(x))`, with `m_d(empty)=0`;
- unit squared `a`, `b`, event bandwidth, and outer bandwidth parameters;
- the Gaussian event and outer configuration kernels;
- the ordered-pair U-statistic for `2 <= R <= 128`;
- the exact PhysioNet `R^112` map and first-48-hour/cap/no-go semantics;
- the exact Retail `R^10` UTF-8/source-civil/signed-value map and
  horizon/cap/no-go semantics; and
- lower-is-better direct-minus-guide orientation.

The display explicitly states that source documentation facts are not snapshot
or admission receipts.

## 5. Qualification

Final package qualification requires:

1. exact byte/hash binding for every non-self package file;
2. semantic validation of the machine record;
3. formula-token agreement across Markdown, TeX, source, and machine record;
4. formal-score equality against the frozen exact API in both domains;
5. cross-domain, malformed-input, combined resource-ceiling, factory-bypass,
   and audit-record tampering refusals;
6. unchanged hashes for the frozen F105 inputs and historical manuscript
   predecessor; and
7. an independent review with no unresolved P0/P1/P2 finding.

## 6. Closure boundary

This package closes exactly the bounded timetable task
`F105_MANUSCRIPT_DISPLAY_AND_PRODUCTION_EVALUATOR_INTEGRATED_PREOUTCOME`.
It has zero field-count delta because F105 and its necessary domain schema
fields were already closed by the predecessor package.

It does not select or close F109, F110, F111, or F112, so B04 remains open
until those statistical choices are frozen. It does not close B01--B12, a
Formal Test, a result, domain admission, test-data secrecy, data access,
runtime/scientific execution, submission, or a scientific claim. The
production API is an implementation of the metric calculation, not evidence
that a model, dataset, conditional draw law, capacity reservation, or empirical
result exists.
