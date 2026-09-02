# Gate-A Retail temporal-rule field freeze

**Date:** 2026-08-31  
**State:** `GATE_A_RETAIL_F060_TEMPORAL_RULE_FROZEN_PREOUTCOME`  
**Global state:** `DRAFT_NOT_EXECUTABLE`  
**Scientific execution:** none

## 1. Scope and authority

The normalized visible instruction is:

> Okay, sounds good. What I want you to do is to set aside a significant portion of work to do such that you are busy for around 8 hours, because I am going to sleep, and dont want my absence to make you idle.

It authorizes autonomous local project work. It does not authorize network or
source contact, data acquisition or access, entropy, real splitting, runtime or
scientific execution, training, submission, or claim promotion. Paths, schema,
the parameterized temporal rule, and validation cases are agent-selected
pre-outcome decisions. Raw transport bytes, trailing HTML-space representation,
account identity, and cryptographic authentication are unbound.

This is a four-file additive closure package:

- `PROJECT_GATE_A_RETAIL_TEMPORAL_RULE_FIELD_FREEZE.md`;
- `research/fixtures/manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.json`;
- `research/diagnostics/manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.py`; and
- `tests/unit/test_manuscript_v3_gate_a_retail_temporal_rule_field_freeze_v1.py`.

It does not modify the execution preregistration, any predecessor package, or a
tracker. It closes exactly one pre-execution field, F060.

## 2. Why F060 and F061 are separable

The immutable preregistration deliberately assigns two sibling JSON pointers:

- F060: `/split_and_leakage_plan/retail_temporal_cutoff_and_window_rule`; and
- F061: `/split_and_leakage_plan/train_validation_test_proportions_or_counts`.

The first pointer owns the deterministic mapping from complete customer time
intervals and a resolved target-count projection to temporal windows. The
second owns the proportions or counts, any proportion-to-count rounding rule,
and their power justification. Therefore F060 can be complete as a typed
function while F061 remains an unresolved input. This is
the same compositional principle by which an aggregation rule can be frozen
before the metric or sample counts supplied to it.

The earlier Retail design couples the temporal logic to a candidate Hamilton
70/15/15 allocation. This successor does **not** copy its
`RETAIL_CUSTOMER_DISJOINT_TEMPORAL_HAMILTON_70_15_15_V1` identity as the F060
value. Doing so would shadow-select F061. Instead it freezes the allocation-free
temporal projection below and requires the eventual exact target-count mapping
to be projected only from a complete F061 value. F061 may later use raw counts
or proportions plus its own exact rounding rule; this package chooses neither
representation nor conversion. The qualification covers the historical 70/15/15
instantiation and distinct non-70/15/15 target-count mappings. That differential
case prevents the temporal rule from secretly hard-coding an allocation.

## 3. Exact F060 value

F060 is closed to the structured rule identified by
`RETAIL_CUSTOMER_DISJOINT_TEMPORAL_EXHAUSTIVE_GAP_PAIR_F061_PARAMETERIZED_V1`.
Its exact inputs are:

1. a finite normalized Retail row projection with exactly `row_ordinal`,
   `customer_key_hex`, and `timestamp_utc_microseconds`; and
2. an exact positive integer count projection for `TRAIN`, `VALIDATION`, and
   `TEST`, resolved under the future complete F061 value and summing to the
   number of distinct customers. F061 itself may be counts or proportions plus
   its separately frozen rounding rule.

For each byte-exact customer, form the closed interval from its minimum through
maximum UTC-microsecond timestamp. Let
`T[0] < ... < T[M-1]` be all distinct row timestamps. Enumerate every ordered
pair `0 <= g1 < g2 <= M-2`. The windows are exactly:

- TRAIN: `t <= T[g1]`;
- VALIDATION: `T[g1] < t <= T[g2]`; and
- TEST: `t > T[g2]`.

A pair is feasible only when every complete customer interval lies wholly in
one window, all customers and rows are preserved exactly once, the observed
customer counts equal the caller-supplied F061 counts, every split has positive
customer and row counts, and the two observed inter-window time inequalities
are strict. Feasible pairs are ordered lexicographically by
`(T[g1], T[g1+1], T[g2], T[g2+1])`; the first is selected.

The rule is outcome-blind. Labels, outcomes, predictions, losses, test
indicators, and extra fields are rejected. A customer spanning a boundary makes
that pair infeasible. If no pair is feasible, the terminal code is
`NO_FEASIBLE_CUSTOMER_DISJOINT_TEMPORAL_BOUNDARY_PAIR`. There is no retry,
fallback, boundary relaxation, exclusion, censoring, quarantine, resplit,
customer migration, or row reassignment.

The frozen value is a rule, not an observed cutoff. No actual timestamp,
snapshot fact, customer count, or allocation is present.

## 4. Exact additive effect

Before this package, the independently qualified additive freezes close F107,
F113, F128, F129, F148, F106, and F108. The effective register therefore has
159 open and seven closed pre-execution fields, six open post-execution fields,
and 165 open fields in total.

This package closes only:

| Field | JSON pointer | Frozen value |
|---|---|---|
| F060 | `/split_and_leakage_plan/retail_temporal_cutoff_and_window_rule` | the complete parameterized rule in Section 3 |

Afterward, 158 pre-execution and six post-execution fields remain open, for 164
open and eight closed fields in total. All 12 blockers, all three Formal Tests,
and R1--R4 remain open. B03 is not closed because the Retail snapshot, schema,
license/privacy/governance evidence, task/admission rules, real split manifest,
F059, F061, and all other required domain fields remain absent.

## 5. Comprehensive remaining-field audit

The live register was reviewed field by field, not merely for the named seam.
No other PRE field is eligible in this batch:

- F001--F018 still require the final theorem/crosswalk or exact known-law
  fixtures, tolerances, and proof gates.
- F019--F057 require real snapshot custody, verified source/license/governance
  facts, exact admitted schemas/tasks/kernels, or training-only admission
  statistics. The local task and manifest artifacts are structural drafts only.
- F058 and F059 are paths to actual content-addressed PhysioNet and Retail split
  manifests. Draft schemas and synthetic manifests are not real paths.
- F061 remains null because 70/15/15 is an unpowered candidate; a later power
  review and receipt must justify exact proportions or counts.
- F062--F104 require final method, comparator, control, external-baseline, and
  matched-compute identities. Local inventories and drafts do not supply them.
- F105 and F109--F112 require an admitted exact primary-metric instance and its
  draws, effect, floor, and compatible confidence construction.
- F114--F127 require exact scalar constraint definitions and margins. In
  particular, composite calibration/coverage cannot receive a direction before
  its scalar is defined.
- F130--F138 require the minimum effect, blinded pilot variance, power-approved
  allocation, immutable seeds, domain sample sizes, analysis formula, and
  resample count.
- F139--F147 require the final implementation, primary metric, training budget,
  and checkpoint-selection semantics.
- F149 is a scientific operating threshold, not a consequence of retaining
  failures or forbidding retries; it remains open pending power and compute
  semantics.
- F150--F162 require actual hardware, environment, capacity, and compute-budget
  evidence.
- F163, F166, and F167 require verified domain-specific license, clinical
  governance, interpretation, privacy, duplicate-exposure, and membership-risk
  facts. A generic local plan would be another precursor.
- F172 is the final sealed-freeze leaf and may close only at Gate C.

The six POST fields are outside this PRE sweep and remain open.

## 6. Qualification and custody

The read-only validator hash-binds the immutable preregistration and closure,
the prospective no-acquisition seal quartet, the original Retail split-design
quartet, the Retail task/dual-manifest draft quartet, and both additive
field-freeze quartets that establish the 165-open/seven-closed baseline. It
recomputes every predecessor semantic self-digest that exists.

The pure reference selector accepts caller-supplied normalized rows and exact
target counts only. Hostile qualification covers arbitrary non-70/15/15 target
counts, the historical candidate allocation, input permutation, multirow
customers, spanning intervals, no-feasible cases, malformed rosters, duplicate
ordinals, Boolean/integer aliases, built-in subclasses, invalid hexadecimal
keys, signed-64-bit timestamp bounds, target-count mismatch, custody tampering,
hard links, symlinks, modes, duplicate JSON keys, noncanonical JSON, coherent
machine-record rehashing, and source-safety inspection.

The helper is not a production splitter and caller-supplied values are not
scientific evidence. Qualification creates only disposable test copies and
launches ordinary Python/pytest interpreters. The canonical validator has no
writer, network, connector, subprocess, entropy, data-access, training, or
scientific-worker route.

## 7. Preserved nonclaims

The historical zero-delta statements in the earlier Retail design and manifest
draft packages remain true descriptions of those immutable checkpoints. This
successor supersedes only their project-level current view of F060 through an
explicit additive closure; it does not rewrite their bytes or retroactively
claim they closed a field.

No real Retail snapshot was opened, no real cutoff or split was computed, no
feasibility was observed, no manifest was persisted, no allocation was chosen,
no power claim was made, and no domain was admitted. F058, F059, F061, all
remaining PRE fields, every blocker, every Formal Test, every result, Gate A,
and the global `DRAFT_NOT_EXECUTABLE` state remain unchanged except for the
single F060 field count.

This package is internal evidence only. A publication-safe derivative and a
fresh anonymity/methods/statistics audit are required before external use.
