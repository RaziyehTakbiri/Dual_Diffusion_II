# F104 matched-total-compute formula freeze

**Reported:** 2026-08-31  
**State:** `F104_MATCHED_TOTAL_COMPUTE_FORMULA_FROZEN_RESOURCE_VALUES_NULL`  
**Global project state:** `DRAFT_NOT_EXECUTABLE`  
**Package kind:** `ADDITIVE_PREOUTCOME_EXACT_F104_FIELD_CLOSURE`  
**Control predicate:** `MATCHED_TOTAL_COMPUTE_FORMULA_F104_FROZEN_PREOUTCOME`

## 1. Decision

This additive package closes exactly one pre-execution field:

- `F104`, `/method_and_baseline_plan/matched_total_compute_formula`.

It freezes the already validated exact matched-total-compute formula from the
baseline capability and compute-model draft. The formula is parameterized by
future integer resource-event counts and future strictly positive exact
rational calibration weights. It does not select or measure those values.

Before this package, the current effective field view was 146 open and 20
closed pre-execution fields, plus six open and zero closed post-execution
fields. After this package, the view is 145 open and 21 closed pre-execution
fields, plus the same six open and zero closed post-execution fields. All 12
blockers remain open. In particular, B06 and B08 remain open.

No tracker or evidence-ledger file is edited by this package. A later tracker
integration may record the one-field delta only after an independent review
accepts the exact package.

## 2. Exact F104 value

For method `m`, domain `d`, phase `p`, and resource event `k`, let
`n[m,d,p,k]` be an exact nonnegative integer event count and let `w[d,k]` be a
strictly positive exact rational calibration weight. The frozen scalar cost is

`C[m,d] = sum_p sum_k n[m,d,p,k] * w[d,k]`.

The phase order is exact and complete:

1. `PILOT`;
2. `TUNING`;
3. `FINAL_TRAINING`; and
4. `CONFIRMATORY_INFERENCE`.

The resource-event order is exact and complete:

1. `BASE_FORWARD`;
2. `BASE_BACKWARD`;
3. `CONDITIONER_FORWARD`;
4. `CONDITIONER_BACKWARD`;
5. `GUIDE_EVALUATION`;
6. `RESAMPLING_STEP`;
7. `ODE_OR_SDE_STEP`;
8. `DATA_ADAPTER_RECORD`;
9. `METRIC_DRAW_EVALUATION`; and
10. `OTHER_DECLARED_OPERATION`.

Every future ledger must contain every phase/event cell. Counts are exact
nonnegative built-in integers, not booleans or floats. Weights are strictly
positive built-in integers or `fractions.Fraction` values, not booleans or
floats. Each normalized numerator and denominator is limited to 4,096 bits,
and every accumulated phase or total rational is limited to 8,192 bits.
Binary floating-point arithmetic is not permitted in this accounting formula.

The future weights must be calibrated once by a predeclared microbenchmark on
the frozen hardware and software environment before test access. A weight is
shared by methods within a domain and cannot be changed per method or after an
outcome. An operation outside the nine named concrete events must be declared
prospectively as `OTHER_DECLARED_OPERATION`; an undeclared operation makes the
run ineligible.

Within each domain, the primary pair must receive the same prospective scalar
ceiling and the same patient or customer groups, conditioning cases, draws,
unconditional base checkpoint, precision policy, and metric workload. The
ledger charges successful and failed attempts, author-added extensions, and
method-specific preprocessing. Unused allocation is not transferable, and no
post-result top-up is permitted.

The scalar cost is necessary but not sufficient. Wall time, accelerator time,
peak device memory, peak host memory, model-evaluation count, persistent
bytes, failure count, and parameter count remain separate hard axes. A run
that exceeds any frozen hard-axis ceiling is ineligible even when its scalar
cost remains below its scalar ceiling. Fairness means equal prospective
ceiling and selection opportunity, with all realized use reported; it does
not promise identical realized resource consumption.

## 3. Parameterization and nonclosure boundary

F104 owns only the formula and its accounting semantics. It does not own or
populate any operand or resource ceiling. The following remain unresolved:

- F062--F103: method, comparator, control, literature-family, and external
  baseline identities, configurations, capabilities, licenses, parameter
  counts, and method budgets;
- F139--F147: training and checkpoint policy;
- F150--F153: actual hardware and runtime identity, environment digest,
  lockfile digest, and deterministic settings; and
- F154--F162: wall-time, accelerator, memory, model-evaluation, pilot, tuning,
  final, reserve, and total compute ceilings or allocations.

No hardware has been selected or reserved. No microbenchmark was run. No
calibration weight, method budget, capacity, runtime receipt, production
runner, scientific threshold, seed schedule, domain admission, or result is
created. The synthetic arithmetic vector inherited from the draft is a pure
calculator qualification and is not a proposed workload or budget.

Consequently this package does not close B06, B08, B12, any Gate-A item, any
Formal Test, any result slot, or any submission blocker. Formal Tests 28 and 29
remain `OPEN`; Formal Test 30 remains `PENDING`; R1--R4 remain unexecuted.

## 4. Frozen predecessor boundary

The package byte-binds the complete four-file baseline capability and
compute-model draft and the complete five-file Gate-A B05 known-law freeze.
The former supplies the already validated formula and exact calculator. The
latter supplies the current additive field-count projection in which F104 is
open, 20 pre-execution fields are closed, all 12 blockers are open, no Formal
Test is closed, and no result exists.

The validator independently checks the relevant predecessor semantics rather
than treating raw hashes alone as scientific meaning. It requires the exact
draft formula, phase and resource vocabularies, exact-arithmetic domains,
future-weight boundary, fairness rules, and B06/B08 nonclosures. It also
requires the exact B05 count transition and verifies that F104 is present in
the 146-field pre-execution open roster before applying this one-field
successor.

No predecessor file is edited, superseded in place, or reinterpreted as an
execution receipt.

## 5. Qualification

The four-file package is:

- `PROJECT_F104_MATCHED_TOTAL_COMPUTE_FORMULA_FREEZE.md`;
- `research/fixtures/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.json`;
- `research/diagnostics/manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py`; and
- `tests/unit/test_manuscript_v3_f104_matched_total_compute_formula_freeze_v1.py`.

The read-only validator uses only the Python standard library. It performs
stable, no-follow reads; requires regular single-link `0644` files; verifies
all predecessor byte bindings and predecessor semantic self-digests; requires
canonical duplicate-free ASCII JSON; reconstructs the exact expected machine
record; and independently recomputes the package semantic digest.

Its pure calculator replays the exact integer/rational contract. Hostile tests
cover missing, extra, reordered, boolean, floating, negative, zero-weight, and
over-bound arithmetic inputs; coherent machine-record tampering; every
predecessor and current-package byte; noncanonical and duplicate-key JSON;
symlink, hard-link, and mode substitution; path escape; static effect-surface
exclusion; count drift; field-scope drift; and promotion of any forbidden
closure or execution claim. All mutations occur only in disposable test
copies.

Validation reads the canonical package and predecessors without writing them.
It imports no project science, contacts no source, draws no entropy, launches
no worker, accesses no data, trains no model, and performs no scientific or
production execution.

## 6. Authority and publication boundary

The standing visible instruction to continue substantial bounded local work
authorizes this offline construction. It does not authorize network access,
external contact, repository or license lookup, data access, hardware
reservation, operational receipt creation, entropy, training, scientific
execution, claim promotion, submission, or tracker mutation.

This package is internal project-control evidence. It is not approved for
anonymous or public inclusion. Any manuscript-facing derivative requires a
fresh review that removes internal paths, hashes, custody details, commands,
and conversation provenance while preserving the exact scientific boundary.

## 7. Evidence-ready registration wording

If and only if an independent read-only review accepts the exact four-file
package with no unresolved material finding, a later authorized tracker and
evidence-ledger integration may use the following bounded wording:

> Upon independent acceptance, register only this delta: F104 (`/method_and_baseline_plan/matched_total_compute_formula`) is closed by the exact parameterized formula `C[m,d] = sum_p sum_k n[m,d,p,k] * w[d,k]`, with exact nonnegative integer counts and strictly positive exact rational weights under the frozen phase, resource-event, calibration, fairness, and hard-axis rules. Effective pre-execution counts move from 146 open / 20 closed to 145 open / 21 closed; post-execution counts remain 6 open / 0 closed. B06, B08, B12, and all 12 blockers remain open; Formal Tests 28 and 29 remain OPEN, Formal Test 30 remains PENDING, and R1-R4 remain unexecuted. This registration supplies no resource value, operational receipt, runtime, scientific result, claim, submission, other field closure, or blocker closure.

The quoted paragraph is prospective integration text, not a tracker mutation,
independent acceptance, or permission to perform that later integration.
