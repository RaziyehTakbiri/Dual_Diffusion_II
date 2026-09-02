# F146 checkpoint tie-rule freeze

**Reported:** 2026-09-01  
**State:** `F146_EARLIEST_STEP_TIED_BEST_CHECKPOINT_RULE_FROZEN_PREOUTCOME`  
**Global project state:** `DRAFT_NOT_EXECUTABLE`  
**Package kind:** `ADDITIVE_PREOUTCOME_EXACT_F146_FIELD_CLOSURE`  
**Control predicate:** `F146_EARLIEST_STEP_TIED_BEST_CHECKPOINT_RULE_FROZEN_PREOUTCOME`

## 1. Exact bounded decision

This additive package closes exactly one pre-execution field:

- `F146`, `/training_and_checkpoint_plan/checkpoint_tie_rule`.

The frozen rule is:

> Within one future canonical checkpoint-selection unit, if the later-frozen
> F144 validation semantics certify at least two eligible canonical
> checkpoints as the complete tied-best set, select the unique member having
> the smallest exact nonnegative completed optimizer-step index.

The rule identifier is
`F146_EARLIEST_STEP_TIED_BEST_CANONICAL_CHECKPOINT_RULE_V1`. It resolves only
an actual tie. If later F144 processing certifies one unique best checkpoint,
that checkpoint needs no F146 tie-break invocation. The package does not
inspect or compare a validation value and does not select a validation metric,
direction, numeric representation, equality relation, tolerance, checkpoint
cadence, stopping rule, or candidate roster.

The mandatory terminal selection-refusal disposition is
`F146_SELECTION_REFUSAL_NO_CHECKPOINT`. A refusal returns no checkpoint and
creates no authority for a fallback, retry, rerun, retraining, top-up, extra
optimizer step, new checkpoint, metric change, tolerance change, or altered
candidate roster.

After final independent acceptance and registration of the preceding F137
closure, the accepted baseline is 144 open / 22 closed pre-execution fields
and 3 open / 3 closed post-execution fields, or 147 open / 25 closed total.
The only permitted F146 delta is 143 open / 23 closed pre-execution fields,
with post-execution unchanged at 3 open / 3 closed, or 146 open / 26 closed
total. The method/runtime/compute workstream moves from 64 open / 1 closed to
63 open / 2 closed. Theory/statistics remains 34/20, data/governance/
reproduction remains 48/4, and final sealed freeze remains 1/0.

B12 remains open. B07 and all other blockers remain open. Formal Tests 28 and
29 remain `OPEN`, Formal Test 30 remains `PENDING`, all four result slots
remain empty, and the project remains `DRAFT_NOT_EXECUTABLE`.

No tracker, evidence-ledger, predecessor, production/training source, data,
runtime, or operational file is edited by this package.

## 2. Exact selection function

The rule is applied independently to one future canonical selection unit
`u`. A selection unit is an opaque content-addressed identity for one future
checkpoint-selection context. Its eventual contents may bind domain, method,
training seed, configuration, and other frozen context, but this package does
not select or populate any of those values.

Let `T_u` be the complete tied-best roster certified under later F144
semantics. Every row `c` in `T_u` contains:

- an ordinal establishing canonical row order;
- `step(c)`, the exact nonnegative built-in integer count of successfully
  completed optimizer update operations, with Python/JSON booleans and integer
  subclasses forbidden; the package-local decimal encoder is total for every
  such integer and independent of interpreter digit-safety settings;
- a SHA-256 digest of the immutable checkpoint content; and
- a domain-separated checkpoint identity binding `u`, `step(c)`, and the
  checkpoint-content digest.

For an actual tie, `|T_u| >= 2`, and the rule returns

```text
c_star = the unique c in T_u such that
         step(c) = min { step(q) : q in T_u }.
```

The minimum is unique because the admitted roster has a one-to-one mapping
between optimizer-step indices and checkpoint identities. The result carries
the selection-unit digest, the selected step, the selected checkpoint identity
and content digest, the complete tied-best roster digest, and the rule ID.

`step(c)` is a completed-optimizer-update counter, not an epoch number, file
timestamp, array position, filename, filesystem path, validation rank, or
wall-clock value. Step zero is permitted only if a later fully frozen
checkpoint schedule makes the initial state an eligible candidate and F144
certifies it as tied best. This package neither makes it eligible nor requires
it to exist.

The phrase “one canonical checkpoint per step” is local to the eligible roster
inside one selection unit. It does not require a checkpoint at every optimizer
step, does not define a checkpoint cadence, and does not prohibit two distinct
selection units from using the same numerical step index.

## 3. F144 certification and canonical roster boundary

The pure helper accepts no raw validation value. Its input must contain an
opaque digest of the later F144 semantics and exact affirmative certification
that:

1. every row is an eligible checkpoint under those semantics;
2. the referenced F144 semantics are final and frozen;
3. the supplied roster is the complete tied-best set, with no omitted or extra
   tied-best checkpoint;
4. the roster belongs to exactly one selection unit;
5. every checkpoint identity is canonical, content-addressed, and bound to its
   exact completed optimizer-step index; and
6. the roster digest matches the canonical ordered rows and the F144/selection-
   unit digests.

F144 remains responsible for the validation metric, favorable direction,
numeric representation, comparison relation, exact equality or tolerance
semantics, treatment of nonfinite values, eligibility criteria, and production
certificate. F146 may not infer, default, override, or repair any of them.
Without a valid future F144 certificate, the tie rule refuses selection.

Rows are canonically ordered by strictly increasing optimizer-step index and
carry exact zero-based ordinals. Keys use the frozen canonical key order.
Unknown keys, missing keys, out-of-order rows, noncanonical digest text, or a
noncanonical top-level object are invalid. The rule does not use first-seen,
last-seen, insertion, lexical-identity, path, modification-time, or filesystem
ordering as a fallback.

The exact step-bound identity preimage is canonical ASCII JSON with sorted
keys, no insignificant whitespace, and no terminal line feed:

```text
SHA256(
  ASCII("heterodiff-f146-step-bound-checkpoint-identity-v1\\0") ||
  ASCII('{"checkpoint_content_sha256":"<64-lowercase-hex>",'
        '"optimizer_step_index":<base-10-JSON-integer>,'
        '"selection_unit_sha256":"<64-lowercase-hex>"}')
)
```

The exact tied-best roster digest preimage is:

```text
SHA256(
  ASCII("heterodiff-f146-certified-tied-best-roster-v1\\0") ||
  canonical_ASCII_JSON({
    "f144_semantics_sha256": "<64-lowercase-hex>",
    "rows": [<rows in exact canonical order>],
    "selection_unit_sha256": "<64-lowercase-hex>"
  })
)
```

Every JSON object is serialized with `ensure_ascii=true`, `allow_nan=false`,
lexicographically sorted keys, separators `,` and `:`, and no trailing LF
inside a digest preimage. The literal domain labels include the shown NUL byte.
Optimizer-step integers use a package-local total base-`10^9` chunk encoder:
the most-significant nonzero chunk is emitted without zero padding and every
following chunk is emitted as exactly nine decimal digits. Thus every exact
nonnegative built-in integer has its unique ordinary base-10 JSON spelling,
with no sign or leading zero, regardless of an interpreter integer-to-string
digit guard.

The pure-helper top-level key order is exactly:

```text
certificate, rows, tied_best_roster_sha256
```

The nested certificate key order is exactly:

```text
all_rows_eligible_under_f144_certified,
candidate_set_closed_under_future_freeze_certified,
complete_tied_best_roster_certified,
f144_semantics_final_and_frozen_certified,
f144_semantics_sha256,
first_and_only_invocation_certified,
prior_tie_break_invocation_count,
production_history_authenticated_by_helper,
selection_unit_sha256
```

The row key order is exactly:

```text
checkpoint_content_sha256, checkpoint_identity_sha256,
optimizer_step_index, ordinal
```

The success-output key order is exactly:

```text
caller_certifications_structurally_accepted, checkpoint_content_sha256,
checkpoint_identity_sha256, checkpoint_selected, optimizer_step_index,
production_history_authenticated, rule_id, selection_disposition,
selection_unit_sha256, tied_best_candidate_count, tied_best_roster_sha256
```

The refusal-output key order is exactly:

```text
checkpoint_selected, disposition, reason_code, rule_id
```

The domain-separated step-bound identity is a synthetic qualification
contract, not a claim that current production checkpoint code already emits
this exact wrapper. Future integration must bind the admitted production
checkpoint bytes and selection-unit context before the rule can be used.

## 4. One-to-one identity and refusal semantics

Validation occurs before the minimum is evaluated. Any of the following yields
`F146_SELECTION_REFUSAL_NO_CHECKPOINT` and no selected row:

- absent, false, malformed, or inconsistent F144 eligibility or complete-tie-
  roster certification;
- an empty roster, a singleton roster passed to the tie helper, or an
  uncertified roster;
- a boolean, negative, noninteger, integer-subclass, or otherwise noncanonical
  optimizer-step index;
- a missing, malformed, or noncanonical selection-unit, F144-semantics,
  checkpoint-content, checkpoint-identity, or roster digest;
- a row duplicated byte-for-byte;
- the same optimizer-step index repeated with the same checkpoint identity;
- the same optimizer-step index associated with conflicting checkpoint
  identities or contents;
- one checkpoint identity associated with more than one optimizer-step index;
- an identity that does not recompute from the exact selection unit, step, and
  checkpoint-content digest;
- a tied-best row omitted from or added to the certified complete roster;
- noncanonical row/key/ordinal order; or
- any attempt to supply a raw metric, direction, tolerance, stopping, cadence,
  maximum-step, patience, tuning, compute, runtime, data, or result field to
  the helper.

The same checkpoint-content digest may legitimately occur at two different
steps. Each occurrence still has a different step-bound checkpoint identity.
Reusing one checkpoint identity across different steps is forbidden and
refuses selection.

Refusal is terminal for the selection call. It is not a sixth scheduled-run
terminal status and does not itself classify a future run as `COMPLETE`,
`ALGORITHMIC_FAILURE`, `NONFINITE`, `OOM_OR_TIMEOUT`, or `INFRA_ABORT`.
Before execution, later frozen failure-handling rules must map any realized
selection-integrity failure into the existing run-status taxonomy without
deletion or favorable retry. F146 does not close F149 or supply that mapping.

The helper requires exact caller-supplied structural certifications that the
future candidate set is closed, this is the first and only tie-break invocation,
and the prior invocation count is the exact integer zero. It also requires the
caller to state that production history is not authenticated by the helper.
The helper checks only the shape and values of those certifications. As a pure,
stateless, idempotent function it cannot observe call history, authenticate that
the candidate set is truly final, or prevent a caller from invoking it again.
Those are future integration and durable-custody obligations and remain open.

Production integration may invoke the rule only once after the future
candidate set and its F144 certificate are complete. Repeated application while
validation values arrive, stopping at the first apparent best value, adding
later candidates, or changing the roster after invocation is forbidden
sequential stopping.

## 5. Exact nonclosure boundary

F146 owns only the deterministic tie-breaking function and its structural
selection-refusal behavior. It supplies no value for:

- F139 optimizer;
- F140 learning-rate schedule;
- F141 precision;
- F142 batch construction;
- F143 maximum epochs or optimizer steps;
- F144 validation metric, direction, representation, equality, or tolerance;
- F145 early-stopping patience;
- F147 maximum tuning trials per method;
- F150--F162 hardware, environment, resource ceilings, allocations, reserve,
  or total compute ceiling; or
- any method, domain, seed, checkpoint cadence, checkpoint bytes, eligible
  roster, F144 certificate, data, entropy, runtime, result, claim, or
  submission value.

It does not close the Solo-Block-7 compound task to freeze checkpoint-selection
and training rules, because the other training/checkpoint fields remain open.
It does not close B12 because whole-method implementation, production
checkpoint integration, and the remaining training fields are absent.

The qualification helper is not a production selector. Production
checkpoint-selection integration, implementation evidence, invocation custody,
and authenticated final-roster enforcement remain absent. This package is a
plan-field freeze, not an implementation qualification.

## 6. Development-evidence exclusion and anti-selection boundary

The accepted A1 development-checkpoint V2 evidence remains
`FINAL_UPDATE_ONLY` with `NOT_APPLICABLE_NO_SELECTION`, no validation
checkpoint selection, and no early stopping. The later D1 diagnostic performed
no checkpoint selection and may not supply a candidate, F144 value, tie class,
or winner for this rule. Those artifacts are immutable scope-exclusion
witnesses, not production inputs.

The proposed F146 rule does not reinterpret the development final update as a
production checkpoint and does not use any exposed development metric or
outcome to choose earliest-step behavior. Earliest-step tie resolution is
frozen prospectively and outcome-independently.

This is a direct one-field closure, not a zero-field precursor. It therefore
satisfies the anti-drift requirement that new work reduce a named tracked
count. The package creates no extra project-control layer and does not claim
that a blocker, Formal Test, implementation gate, or result is complete.

## 7. Predecessor and construction boundary

The final machine record must byte-bind and, where available, semantically
bind:

- the authoritative execution preregistration human/machine pair;
- the accepted pre-execution-closure V2 human/machine pair;
- the anti-drift operating policy;
- the accepted A1 development-checkpoint V2 human/machine exclusion witnesses;
- the accepted D1 diagnostic-evidence-registration human/machine exclusion
  witnesses;
- the final B11 five-file package including its independent review, which
  anchors the 3/3 post-execution state; and
- the final accepted F137 four-file package and its independent-review receipt,
  which anchor the 144/22 pre-execution and 147/25 total baseline.

The F137 files visible during construction are not final bindings. The F146
machine record may be generated only after the exact final F137 package and
independent-review receipt exist. No in-progress F137 hash may be promoted or
treated as accepted evidence.

The timetable and evidence ledger are not immutable package predecessors;
they may be updated only later, after independent acceptance of this package.
This prevents a circular package/registration dependency.

## 8. Qualification package

The four intended files are:

- `PROJECT_F146_CHECKPOINT_TIE_RULE_FREEZE.md`;
- `research/fixtures/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.json`;
- `research/diagnostics/manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.py`;
  and
- `tests/unit/test_manuscript_v3_f146_checkpoint_tie_rule_freeze_v1.py`.

Machine construction was intentionally deferred until the final F137 receipt
became available. The final machine record binds that exact receipt, and the
read-only validator must require canonical
duplicate-free ASCII JSON; stable no-follow reads through held descriptors;
regular single-link `0644` files; exact package and predecessor hashes;
semantic self-digests; exact one-field/count/workstream effects; and complete
nonclosure surfaces.

The pure selector has no filesystem, RNG, entropy, network, connector,
subprocess, environment-build, data, training, runtime, checkpoint writer,
scientific-execution, result, or submission route. All executable examples are
synthetic digests and integer steps.

Hostile tests must cover known-answer selection; at-least-two invocation;
strict row/key/ordinal order; boolean, negative, and noninteger steps;
duplicate rows; same-step duplicate and conflicting identities; cross-step
identity aliasing; invalid step bindings; absent or false certification;
roster-digest mismatch; unknown metric/stopping/runtime fields; canonical JSON
and duplicate-key rejection; package/predecessor drift; custody mode/link/race
attacks; and fully re-signed attempts to close another field, alter counts,
close B12, populate F144, or claim implementation, runtime, data, or results.

All mutation tests use disposable package copies.

## 9. Prospective registration wording

Only after an independent read-only review accepts the exact four-file package
may a later authorized tracker and ledger update use this bounded wording:

> Upon independent acceptance, register only this delta: F146 (`/training_and_checkpoint_plan/checkpoint_tie_rule`) is closed by `F146_EARLIEST_STEP_TIED_BEST_CANONICAL_CHECKPOINT_RULE_V1`: within one future canonical selection unit, the unique smallest nonnegative completed optimizer-step index is selected from an at-least-two-member complete tied-best eligible checkpoint roster already certified under the later-frozen F144 metric semantics. Invalid, incomplete, uncertified, duplicate, conflicting, aliased, or noncanonical input yields `F146_SELECTION_REFUSAL_NO_CHECKPOINT` with no output or fallback. Effective pre-execution counts move from 144 open / 22 closed to 143 open / 23 closed; post-execution remains 3 open / 3 closed; totals move from 147 open / 25 closed to 146 open / 26 closed. Method/runtime/compute moves from 64/1 to 63/2. F139--F145 and F147, F150--F162, B12, all 12 blockers, Formal Tests, results, runtime, data, science, claims, and submission remain open or absent.

This paragraph is prospective evidence wording, not tracker registration,
independent acceptance, checkpoint selection, implementation, execution, or
runtime authority.
