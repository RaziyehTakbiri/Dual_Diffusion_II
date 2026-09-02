# Formal Tests 29–30 supplied-input two-macrostep path precursor

**Prepared:** 2026-08-31  
**Project state:** `DRAFT_NOT_EXECUTABLE`  
**Candidate bounded predicate:**
`SYNTHETIC_SUPPLIED_INPUT_TWO_MACROSTEP_ROLLING_LINEAGE_PATH_VALIDATED`  
**Formal Test 28:** `OPEN`  
**Formal Test 29:** `OPEN`  
**Formal Test 30:** `PENDING`

## Decision

The prior Test-29/Test-30 composition stops after one supplied
left-Heun/edit/right-Heun macrostep. This additive development package
implements and tests the next bounded integration layer: exactly two such
macrosteps with the complete coordinate state, active serials, retired
serials, and next fresh serial carried across their shared boundary.

The implementation validates the complete two-step supplied-input roster
before the first numerical Heun operation. It then executes a deterministic
two-step composition and reconstructs the result from the same supplied input
for strict contextual comparison. The frozen qualification exhausts all
`32 x 32 = 1,024` ordered low-word pairs admitted by the dynamic rank-one
Test-29 fixtures.

This is a candidate bounded component control. It has not received a separate
custody validator or independent admission review and is not registered in the
project evidence ledger or completion timetable.

## Exact bounded behavior

The component begins from the existing deterministic Test-30 occurrences
`(1, A, 0.75)` and `(2, B, -0.4)`. At each of exactly two step indices it:

1. validates one CP23-shaped tag-4 physical-increment row for every currently
   live serial;
2. validates one CP24-shaped tag-6 supplied uint64 word at completed-proposal
   ordinal zero;
3. selects one birth, replacement, or death route using the exact finite
   Test-29 word map;
4. advances the rolling lineage with the Test-29 fresh/retired-lineage rule;
5. validates one CP23-shaped tag-5 physical-increment row for every post-edit
   live serial;
6. applies one left Heun half-step, the selected edit, and one right Heun
   half-step.

All rosters for both steps are preflighted before item 6 begins. Address
identities are required to be unique across both steps and all three tags.
Destination-bearing routes use the selected finite normal-quantile-cell
midpoint representative. That representative is not a continuous Gaussian
sample.

The dynamic one-step route fixture has route masses birth `1/2`, replacement
`1/4`, and death `1/4`. Its source law is exactly dyadic for each reachable
starting cardinality:

- cardinality 1: `(1)`;
- cardinality 2: `(1/2, 1/2)`;
- cardinality 3: `(1/2, 1/4, 1/4)`.

These are finite development fixtures, not a production tilted jump law.

## Frozen exhaustive receipt

The ordered 1,024-case qualification produces:

- route-family pairs:
  - birth→birth: 256;
  - birth→death: 128;
  - birth→replacement: 128;
  - death→birth: 128;
  - death→death: 64;
  - death→replacement: 64;
  - replacement→birth: 128;
  - replacement→death: 64;
  - replacement→replacement: 64;
- step-boundary cardinalities: 1 in 256 cases, 2 in 256, and 3 in 512;
- final cardinalities: 0 in 64 cases, 1 in 128, 2 in 320, 3 in 256, and
  4 in 256;
- 1,024 distinct canonical input digests;
- 1,024 distinct contextual report digests;
- exact boundary-state continuity, global address uniqueness, rolling
  fresh/retired-lineage preservation, and complete preflight-before-arithmetic
  in every case.

The ordered-case commitment is
`3273b1c5e553093a3d5a35f4e7686b018363ac609bb300dd6dbb87f66daf7591`.
The aggregate qualification-report digest is
`2a278585373d017b3b60bed28dcbc0ab3830f72c0512891658fc2ab54c666d53`.

The default replacement→death regression case has canonical input digest
`11decfb2a16606b69404958d2e7cac2b75808f78adc00ab8c562da8f993ece8e`
and contextual report digest
`9c66342668b2225cbe5d8705a175dd857fd1aa9d2411bbeea489a41e884b7c94`.

## Hostile and regression evidence

The focused suite contains 15 tests. It covers the full 1,024-case receipt,
replacement/death and replacement/replacement lineage continuity, safe
death/death transition to an empty coordinate roster, exact step-aware
CP23/CP24 addresses, global address disjointness, missing/extra/reordered
rosters, a wrong-step central word, object-mutated input scalars, contextual
rejection of coherently redigested result and aggregate forgeries, exact
parent-module boundaries, broader-claim nonpromotion, and a static refusal of
RNG, network, subprocess, writer, and tracker surfaces.

The focused command completed with `15 passed`.

## Exact nonclosures

This package does not provide or establish:

- a Test-28 initializer, initializer admission, tag-3 coordination, or a live
  source;
- a Brownian, Gaussian, independence, uniform-word, or source law;
- a continuous Gaussian destination sample;
- a waiting clock, acceptance/rejection, thinning, or the zero/multiple-edit
  jump-substep law;
- an arbitrary-length or production Strang path;
- a coupled step-halving study, endpoint-law result, learned/native drift, or
  independent scientific recomputation;
- authenticated parent custody, production runtime custody, data access,
  protected inputs, operational receipts, authority expansion, or scientific
  execution;
- a closed field, blocker, result slot, formal test, submission gate, or
  timetable task.

Formal Test 28 therefore remains `OPEN`, Formal Test 29 remains `OPEN`, Formal
Test 30 remains `PENDING`, and the project delta is exactly zero.

## Candidate registration rule

A later independently reviewed package may register only the named bounded
predicate. Before registration, that review must at minimum hard-pin and
stable-read the source, this human record, the tests, and every executed parent
source; reject coherent rebinding and effectful source drift before execution;
recompute the exact 1,024-case receipt; and preserve every nonclosure above.
Registration would still close no formal test, blocker, result, field, or
operational task.

