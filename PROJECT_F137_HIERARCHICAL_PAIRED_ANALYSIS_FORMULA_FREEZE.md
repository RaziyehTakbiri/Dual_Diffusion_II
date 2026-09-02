# F137 hierarchical paired-analysis formula freeze

**Reported:** 2026-09-01  
**State:** `F137_PARAMETERIZED_NATURAL_GROUP_HIERARCHICAL_PAIRED_ANALYSIS_FORMULA_FROZEN_PREOUTCOME`  
**Global project state:** `DRAFT_NOT_EXECUTABLE`  
**Package kind:** `ADDITIVE_PREOUTCOME_EXACT_F137_FIELD_CLOSURE`  
**Control predicate:** `F137_PARAMETERIZED_NATURAL_GROUP_HIERARCHICAL_PAIRED_ANALYSIS_FORMULA_FROZEN_PREOUTCOME`

## 1. Exact bounded decision

This additive package closes exactly one pre-execution field:

- `F137`, `/power_and_seed_plan/hierarchical_paired_analysis_formula`.

It freezes one parameterized, natural-group hierarchical paired point
estimator and one-replicate empirical resampling transform. It supplies no
primary metric, numeric production representation, score values, bounds,
effect margin, confidence method, resample count, group or case weight, group,
case, draw, or seed cardinality, seed identity, registry, data, entropy,
runtime, scientific result, or decision.

Before this package the accepted additive view is 145 open and 21 closed
pre-execution fields, plus three open and three closed post-execution fields.
After independent acceptance and later tracker registration, the sole allowed
delta is 144 open and 22 closed pre-execution fields. The post-execution view
remains three open and three closed; F168, F170, and F171 retain their B11 plan
closures, while F164, F165, and F169 remain open. All 12 blockers, every
Formal Test, and every result remain unchanged. In
particular, B07 remains open.

No tracker, evidence-ledger, predecessor, data, or operational file is edited
by this package.

## 2. Paired point estimator

The formula is applied separately to each future admitted domain `d`; domains
are never pooled. Let:

- `s = 0,...,S_d-1` index complete, distinct training-seed identities;
- `g = 0,...,G_d-1` index canonical admitted natural-group identities;
- `c = 0,...,C_{d,g}-1` index canonical cases within group `g`; and
- `r = 0,...,R_{d,g,c}-1` index canonical paired draws within a case.

The later admitted primary-score representation supplies two explicit ordered
row rosters, one for direct and one for guide. Every row carries canonical
domain, seed, group, case, draw, and conditioning identities plus one abstract
score. Both row rosters must equal the full ordered product of the separately
supplied canonical identity roster and must be byte-identical in every address
and conditioning field. Thus the evaluator rejects missing, extra, duplicate,
aliased-within-level, out-of-order, cross-domain, or mispaired rows before
using a score. Every supplied identity is a nonempty exact string encoded only
by ASCII bytes `0x21` through `0x7e`; whitespace, controls, NUL, and non-ASCII
text are invalid. Define

```text
Y[d,s,g,c,r]
  = primary_score_direct[d,s,g,c,r]
  - primary_score_guide[d,s,g,c,r]

A[d,s,g,c] = (1/R_{d,g,c}) * sum_r Y[d,s,g,c,r]
H[d,s,g]   = sum_c q[d,g,c] * A[d,s,g,c]
M[d,s]     = sum_g w[d,g] * H[d,s,g]
theta[d]   = (1/S_d) * sum_s M[d,s].
```

`w[d,g]` and `q[d,g,c]` are future pre-outcome exact positive rational
weights. The group weights sum exactly to one within a domain and the case
weights sum exactly to one within every group. They are parameters, not values
selected by this package. Draws are averaged inside a case and are never
independent replication units. Cases remain nested in natural groups.
Training seeds are the model-training replication units; seed-by-group cells
are not IID seeds.

The direct-minus-guide sign and natural-group-weighted aggregation were frozen
by predecessor fields F106 and F107. F137 does not select the primary metric
or reinterpret its sign.

## 3. Exact one-plan hierarchical transform

For one caller-supplied plan, let:

1. `i[0],...,i[S_d-1]` be seed indices drawn IID uniformly with replacement;
2. `j[0],...,j[G_d-1]` be natural-group indices drawn IID with replacement
   from the categorical probabilities `w[d,*]`; and
3. for group occurrence `b`, let
   `k[b,0],...,k[b,C_{d,j[b]}-1]` be case indices drawn IID with replacement
   from categorical probabilities `q[d,j[b],*]`.

The exact replicate statistic is

```text
theta_star[d]
  = (1 / (S_d * G_d))
    * sum_a sum_b
        (1 / C_{d,j[b]}) * sum_l A[d, i[a], j[b], k[b,l]].
```

The seed and group multiplicities form their full product: every selected seed
occurrence is crossed with every selected group occurrence. One case-index
vector is shared across all selected seed occurrences for the same group
occurrence, preserving the crossed case identity. If the same group is
selected at two different group-occurrence positions, those positions have
independent case-index vectors.

The weights are used exactly once, as the categorical group and case
probabilities. They are not multiplied into a selected occurrence again.
Seed selection is uniform because the point estimator is the equal mean over
the admitted seed roster. No draw index occurs in a plan and draws are never
resampled.

The evaluator accepts a caller-supplied finite nonempty tuple of explicit
plans, applies the exact one-plan transform independently to each plan, and
returns the ordered replicate vector. The package does not choose, recommend,
default, or report a plan count. The supplied tuple length is not evidence for
or a closure of F138.

## 4. Interpretation and degeneracy

This is a finite empirical resampling transform conditional on the later
admitted fixed seed, group, case, and draw roster. It does not assert a group
superpopulation law, coverage for unseen patients or customers, or any
confidence property. Those questions remain for F112 and later scientific
review.

The exact structural rules are:

- at least two complete, distinct training seeds per domain;
- at least one natural group, one case per group, and one draw per case;
- a complete paired array matching the explicit canonical roster, allowing
  each natural group its own positive case cardinality and each case its own
  positive draw cardinality;
- conditioning identities unique within each natural group and paired
  one-to-one with its canonical case identities; reuse of the same external
  token across different groups or domains is allowed because the full
  composite address remains distinct;
- identical direct/guide address rosters and conditioning inputs;
- no empty level, missing cell, duplicate base address, pairing mismatch,
  identifier alias, nonfinite value, or extra cell; and
- exact positive rational weights with exact normalization.

A singleton group, case, or draw layer is an allowed deterministic layer and
must be reported as such; it is never converted into extra replication. If all
supplied replicate values are identical, the evaluator reports
`ZERO_EMPIRICAL_BOOTSTRAP_SPREAD`. That is an algebraic flag only, not a PASS,
FAIL, interval, p-value, lower bound, power statement, or permission to switch
methods.

Invalid material has the terminal formula disposition
`F137_INPUT_INVALID_TERMINAL_NO_GO`. There is no drop, imputation,
replacement, retry, top-up, favorable selection, sequential stopping,
post-outcome reweighting, seed-only fallback, mixed-effects fallback, domain
pooling, draw resampling, or alternate analysis route inside this package.

## 5. Parameterization and nonclosure boundary

F137 owns only the formulas, resampling law, ordering, weight-use semantics,
and deterministic refusal behavior above. The following remain open and
null:

- F105 and F109--F112: primary metric, estimator details outside F137,
  minimum meaningful effect, and confidence method;
- F130--F136: power alternative, pilot source, seed count and values, natural
  group count, cases per group, and draws per case;
- F138: confidence-interval resample count;
- every actual score, bound, margin, weight, cardinality, seed, registry,
  snapshot, split, admitted domain instance, and pilot value; and
- every entropy, data, compute, runtime, operational, scientific, inference,
  decision, claim, and submission surface.

The validator's exact-rational synthetic qualification is only a proof of the
formula and its type/refusal behavior. It does not select a production metric
numeric type and it is not a pilot, bootstrap run, power calculation, or
scientific execution.

B07 remains open because the metric, bounds and margins, admitted instances,
pilot evidence, allocation, confidence method, resample count, seed registry,
and compute capacity required for a complete power-and-seed plan remain open.

## 6. Anti-drift and predecessor boundary

B07 already had two accepted zero-field precursor packages: the real-domain
power-allocation route and the pilot-variance/power-strategy draft. The
mandatory scope review therefore permitted no third zero-delta precursor.
This package is the direct F137 closure and creates no additional candidate
layer.

The machine record byte-binds and semantically checks the accepted execution
preregistration, pre-execution closure, both B07 precursor packages, the
Gate-A statistical freeze, the current F104 pre-execution count anchor and its
independent review, the final B11 three-plan-field package and independent
review that establish the current post-execution view, the PhysioNet patient
and Retail customer natural-group carriers, and the anti-drift policy. No
predecessor is edited or reinterpreted as execution evidence.

## 7. Qualification package

The four files are:

- `PROJECT_F137_HIERARCHICAL_PAIRED_ANALYSIS_FORMULA_FREEZE.md`;
- `research/fixtures/manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.json`;
- `research/diagnostics/manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.py`; and
- `tests/unit/test_manuscript_v3_f137_hierarchical_paired_analysis_formula_freeze_v1.py`.

The validator uses the Python standard library only. It performs
componentwise no-follow reads through held directory descriptors; requires
regular single-link `0644` files; checks exact predecessor bytes and semantic
self-digests; requires canonical duplicate-free ASCII JSON; reconstructs the
complete expected record; and recomputes its domain-separated semantic digest.

The evaluator consumes caller-supplied canonical identity/address rosters,
exact rational synthetic scores and weights, and a finite nonempty tuple of
explicit bootstrap index plans. It has no RNG, seed generation,
data reader, writer, project-science import, network, connector, subprocess,
worker, runtime, training, or production route.

Hostile tests must cover known-answer calculations, exact expectation on tiny
enumerated categorical examples, direct/guide reversal, common-shift
cancellation, relabeling invariance, domain separation, shared versus
per-seed case maps, duplicated group occurrences, no double weighting, draws
never resampled, variable per-group case counts, explicit address and pairing
failures, invalid weights and indices, degenerate layers, canonical custody,
mode/inode races, predecessor
drift, and fully re-signed attempts to close another field or introduce a
metric, F112 method, F138 count, operand, data, entropy, runtime, or result.

All tests operate on synthetic values or disposable package copies.

## 8. Prospective registration wording

Only after an independent read-only review accepts the exact four-file package
may a later authorized tracker and ledger update use this bounded wording:

> Register only F137 (`/power_and_seed_plan/hierarchical_paired_analysis_formula`) as closed by the exact parameterized natural-group hierarchical paired-analysis formula and fixed-roster empirical one-plan resampling transform. Effective pre-execution counts move from 145 open / 21 closed to 144 open / 22 closed; post-execution counts remain 3 open / 3 closed, so totals move from 148 open / 24 closed to 147 open / 25 closed. F168/F170/F171 retain their B11 closures; F164/F165/F169, B07, F112, F138, the primary metric, every weight, cardinality, seed, data, entropy, runtime, scientific result, Formal Test, and blocker remain open or unperformed.

This paragraph is prospective evidence wording, not tracker registration,
independent acceptance, or execution authority.
