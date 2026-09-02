# F122 association-approximation-error direction freeze

**Reported:** 2026-09-01  
**State:** `F122_ASSOCIATION_APPROXIMATION_ERROR_DIRECTION_UPPER_BOUND_FROZEN_PREOUTCOME`  
**Global project state:** `DRAFT_NOT_EXECUTABLE`  
**Package kind:** `ADDITIVE_PREOUTCOME_EXACT_F122_FIELD_CLOSURE`

## 1. Exact bounded decision

This additive package closes exactly one pre-execution field:

- `F122`, `/metric_and_estimand_plan/constraint_metrics/4/direction`.

The base preregistration roster has exactly nine constraint metrics. At exact
zero-based index `4` the identifier is exactly `association-approximation-error`, its
direction is `null`, and its `threshold_or_margin` is `null`. The sole field
value frozen here is the exact built-in string:

```text
UPPER_BOUND
```

The control predicate is
`F122_ASSOCIATION_APPROXIMATION_ERROR_DIRECTION_UPPER_BOUND_FROZEN_PREOUTCOME`. Case changes,
whitespace, aliases, subclasses, structured replacements, a different index,
or a different metric identifier are invalid.

This is a direction-only closure: smaller association approximation error is favorable. It
does not define the association-approximation-error scalar, choose KL or TV, combine KL and
TV, define units, normalization or aggregation, select a threshold, margin,
interval or confidence procedure, or evaluate any scientific candidate.

## 2. Separately owned threshold and exact gate rule

F123 remains open at
`/metric_and_estimand_plan/constraint_metrics/4/threshold_or_margin`. A future
gate may pass only when all of the following caller assertions are structurally
present and true:

- the association-approximation-error scalar definition is final and frozen;
- the F123 threshold is final and frozen;
- the supplied upper endpoint is certified; and
- the endpoint and threshold use the same scalar identity and units.

For structurally valid inputs, the exact rule is:

```text
PASS iff certified_upper_endpoint <= f123_threshold
FAIL iff certified_upper_endpoint >  f123_threshold
```

Equality therefore passes. Missing, nonfinite, uncertified, identity-mismatched,
unfrozen, noncanonical, or schema-invalid input refuses with disposition
`F122_DIRECTION_REFUSAL_NO_GATE_DECISION`. Refusal is neither PASS nor FAIL and
produces no executable gate decision.

The pure checker accepts synthetic canonical exact-rational pairs only for
qualification: `{"denominator": d, "numerator": n}` with exact built-in
integers, `d > 0`, nonnegative value, and lowest terms. This local qualification
encoding is not a production numeric-type, serialization, scalar, unit,
threshold, or interval-method selection. It performs only cross-multiplied exact
comparison and never converts to floating point.

The checker requires exact lowercase SHA-256-shaped bindings for the separately
owned scalar-definition and F123-threshold records. It validates only their
shape and caller certifications; it does not authenticate their provenance,
finality, custody, units, or scientific correctness.

## 3. No shadow selection

This package supplies none of the following:

- an association-approximation-error formula or choice among KL, TV, maximum, conjunction,
  weighted combination, or another scalar;
- a production numeric representation;
- units, aggregation, normalization, population, conditioning, or estimator;
- an F123 threshold, margin, tolerance, default, fallback, or learned value;
- a confidence level, interval construction, multiplicity rule, p-value, or
  decision-count choice;
- a data source, candidate, checkpoint, runtime, result, claim, or submission;
  or
- permission to reuse the B05/F016 qualification ceilings as F123.

The accepted B05 package is bound only as immutable orientation evidence: it
uses certified upper endpoints and keeps B05 open. Its exact-self-reference
values and numerical-width budgets are not production thresholds and are not
imported here.

## 4. Exact input and output boundary

The checker top-level keys are exactly:

```text
certifications, certified_upper_endpoint, direction, f123_threshold,
f123_threshold_record_sha256, metric_id, metric_index,
scalar_definition_sha256
```

The certification keys are exactly:

```text
f123_threshold_final_and_frozen, same_scalar_and_units,
scalar_definition_final_and_frozen, upper_endpoint_certified
```

The success/failure result keys are exactly:

```text
decision, direction, equality_passes, metric_id, metric_index,
production_inputs_authenticated
```

Unknown, missing, reordered, or extra keys refuse. A valid comparison returns
only PASS or FAIL. `production_inputs_authenticated` is always `false`.
The rational-object key order is exactly `denominator, numerator`, matching
lexicographically sorted canonical JSON; the opposite order refuses.

## 5. Exact lineage and custody

The machine record fixed-binds fifteen immutable predecessors:

- anti-drift policy (1);
- authoritative execution preregistration human/machine (2);
- pre-execution closure V2 human/machine (2);
- the complete B05 known-law package and certified reference source (5); and
- the final accepted lifecycle-stable F120 package plus V2 independent review (5).

The complete B05 group is bound because its F016 evidence is all-or-nothing.
The F120 V2 group establishes the immediate baseline: PRE `141/25`, POST `3/3`,
total `144/28`, Theory/Statistics `33/21`, Method/Runtime/Compute `62/3`,
Data/Governance/Reproduction `48/4`, Final `1/0`.

Every bound file is read by componentwise, no-follow, stable-custody logic and
must remain a regular `0644`, single-link file with the exact size and SHA-256.
The tracker and evidence ledger are mutable registration surfaces and are not
predecessors.

The human and hostile-test bytes are fixed internally. The machine record binds
the current validator raw bytes, but the validator cannot authenticate its own
raw bytes. Its exact authenticity boundary is
`INDEPENDENT_REVIEW_BOUND_NOT_SELF_AUTHENTICATING`; validator-byte authenticity
becomes durable only through a later exact independent-review receipt. No
internal anchor artifact or self-authentication claim is created here.

## 6. Exact project effect and nonclosures

Subject to independent acceptance, the only permitted delta is F122:

- PRE `141 open / 25 closed` -> `140 open / 26 closed`;
- POST remains `3 open / 3 closed`;
- total `144 open / 28 closed` -> `143 open / 29 closed`; and
- Theory/Statistics `33/21` -> `32/22`.

Method/Runtime/Compute remains `62/3`, Data/Governance/Reproduction remains
`48/4`, and Final remains `1/0`.

F114--F119, F121, F123--F127, F149, B05, all twelve blockers, all Formal Tests,
results, runtime, data acquisition, scientific execution, claims, and
submission remain open or absent. No tracker, ledger, predecessor, runtime, or
scientific state is edited by this package. The package does not register its
own closure and is not independent acceptance.

Mechanically, Formal Test 28 remains `OPEN`, Formal Test 29 remains `OPEN`,
Formal Test 30 remains `PENDING`, `formal_tests_closed=0`, and
`results_filled=0`.

F121 specifically remains `OPEN/HOLD`; this package neither resolves nor
supplies its initializer-error threshold. This is the second consecutive B05
direction artifact. Any third consecutive B05 artifact requires a new explicit
scope review before construction.

## 7. Effect surface

The checker and validator are offline read-only standard-library code. They
have no writer, network, socket, connector, subprocess, RNG, entropy,
environment-authority, clock-authority, project-science import, data reader,
training, evaluation, result, claim, release, or registration path. Hostile
tests mutate disposable copies only.
