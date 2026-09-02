# Staged Predecision Factorization: Incremental Code Audit

**Audit status:** **PASS WITH EXPLICIT SCOPE LIMITS**  
**Audit date:** 2026-08-15  
**Implementation:**
[checkpoint-42 source](../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_predecision_factorization.py)  
**Focused tests:**
[checkpoint-42 tests](../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_predecision_factorization.py)  
**Additive boundary tests:**
[checkpoint-42 supplement](../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_predecision_factorization_supplement.py)  
**Direct capability parent:**
[checkpoint-41 source law](plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law_code_audit.md)  
**Method contract:** [executable method specification](executable_method_spec.md)  
**Claim controls:** [claim ledger](claim_ledger.md)

This document maps the forty-second incremental implementation checkpoint.
CP42 constructs a bounded staged **reference semantics** in which a partial
executable predecision operation \(G^{42}_{r,j}\) receives the complete
proposal/scoring word tuple \(V\), but no reserved decision word. On calls
whose direct CP28 transformation and CP30 scoring stages do not refuse, a
separate operation \(H\) receives \(W\) only after \(G^{42}_{r,j}\) has
produced either modeled quota failure or a ready record containing every
attempt quota.

The checkpoint narrows a real engineering gap in CP41: for the CP42 reference
evaluator, decision-word noninterference follows from the input signature and
the staged implementation. It does **not** prove that this evaluator is
universally equivalent to the live CP36/CP37 implementation, especially on
failure paths; consequently it does not discharge CP41's factorization
hypothesis and does not turn CP41 into a live-source law. The venue-neutral TeX
manuscript is unchanged.

## 1. Exact staged boundary

For fixed valid request/context parameters \(r,j\), let \(V\in[D]^M\) be the
ordered CP41 proposal/scoring-word tuple and \(W\in[D]^A\) the ordered reserved
decision-word tuple, where \(D=2^{64}\), \(A\) is the attempt budget, and
\(M\) is inherited from the exact CP41 coordinate partition. CP42's partial
executable operational map and subsequent decision stage are

\[
G^{42}_{r,j}:D^M\rightharpoonup
\{F_{37}\}\mathbin{\dot\cup}\mathcal R,
\qquad
H^{42}:\operatorname{im}(G^{42}_{r,j})\times D^A
\longrightarrow\{F_{37},E\}\mathbin{\dot\cup}\mathcal X.
\]

Here \(\mathcal R\) is the set of ready rows with a complete quota tuple,
\(E\) is bounded decision exhaustion, and \(\mathcal X\) is the configuration
space. The public schemas retain both failure tags so the output union matches
CP41, but reserved \(F_{36}\) lies outside the executable image. The
implementation has the following stricter operational boundary:

1. `preparation_failure` is reserved and is neither constructed nor accepted
   as an executable CP42 record;
2. CP28 transformation and CP30 scoring exceptions remain operational
   refusals and are not relabelled as preparation failure;
3. only an exact CP37 quota-certification error, after CP42 independently
   preflights a valid nonpositive dyadic score gap, becomes
   `quota_certification_failure`; and
4. `ready` is constructed only after every attempt has been transformed,
   scored, and assigned a certified quota.

The focused run, additive supplement, exact CP41 regression, static gates,
and final independent review are all recorded below. The final disposition is
**PASS WITH EXPLICIT SCOPE LIMITS**.

## 2. Exact ancestry and coordinate custody

Certification accepts one exact CP41 owner and binds its certificate and
explicit factorization-hypothesis object by identity. It resolves the exact
CP40--CP36 ancestry and checks the CP37 and CP36 owner/certificate identities.
The CP41 proposal and decision coordinate tuples, counts, order, and digests
are copied into the CP42 certificate and revalidated against the transitive
CP36 partition.

This establishes that the CP42 input tuple uses the frozen \(V/W\) partition.
It does not establish that every live CP36/CP37 behavior is a function only of
the same projected coordinates. CP42 therefore records
`cp42_noninterference_by_input_signature_and_staging=True` while retaining
`checkpoint41_factorization_assumption_discharged=False` and
`universal_equivalence_to_live_checkpoint36_37_failure_semantics_certified=False`.

## 3. Partial executable \(G^{42}_{r,j}(V)\)

`owner.evaluate_predecision(run_id, initialization_index, proposal_words)`
requires exact non-Boolean uint64 request identifiers and an exact tuple of
exact non-Boolean uint64 words of length \(M\). There is no \(W\) parameter,
caller RNG, or global RNG input.

On calls whose direct dependencies do not refuse, the evaluator uses
identity-bound direct CP28 slot materialization,
transformation, and validation callbacks and the identity-bound CP30 initial-
tilt evaluator. It processes all \(A\) attempts through the transformation and
scoring stages before entering the quota stage. Every retained object and
operation surface is checked throughout the operation. The quota stage then
uses CP37's exact floor-\(e^\delta D\) primitive on independently preflighted
nonpositive dyadic gaps.

The resulting ready row records the canonical configuration, exact score gap,
ideal-probability enclosure, dyadic quota, and strict \(1/D\) approximation
boundary. A ready result contains rows in exact attempt chronology and contains
all \(A\) quotas. A modeled quota failure contains no partial row tuple.

This is a partial executable finite reference semantics, not a totalized
source-fiber enumerator. It evaluates no probability mass and proves no
statement about the distribution of live Philox words.

## 4. Separate \(H\) stage

`owner.apply_decision_words(predecision_result, decision_words)` first validates
and exactly replays the CP42 predecision result. For a ready result, it then
preflights the **entire** exact \(W\in[D]^A\) tuple before the first comparison
and selects the first attempt satisfying \(w_i<K_i\); if none succeeds, it
returns exhaustion. Thus no malformed late word can be hidden by an earlier
successful comparison.

For a modeled quota failure, the pure \(H\) constructor passes the failure
through without inspecting, retaining, hashing, or comparing the supplied
decision-word object. The public owner method still performs exact validation
and replay of the parent predecision record before that pass-through. The
reserved preparation-failure tag remains non-executable.

The selected and exhausted results bind their parent by certificate identity
and result digest. Selected configurations are checked against the exact ready
row; duplicates retain first-success attempt chronology rather than being
silently deduplicated.

## 5. Successful-path live projection witness

For a finite successful instance, CP42 can compare a ready \(G\) record with an
exact live CP37 result whose CP36 proposal words are identical. The witness
checks attempt chronology, canonical configuration identities/digests, score
gaps, and every quota-enclosure field. The **parity comparison** is limited to
that successful predecision/threshold projection. For custody, however, the
witness retains and digest-binds the exact supplied live CP37 result; the CP37
result digest includes its decision records/words and selected-or-exhausted
outcome. The witness contains no CP42 applied-\(H^{42}\) record and asserts no
parity of \(W\), the CP37 decision/outcome, or a CP42 applied-\(H^{42}\)
result. The focused test separately compares one applied \(H^{42}\) result
with the corresponding live outcome, but that assertion is not part of the
sealed parity comparison.

This witness supports **per-instance successful projection parity**. It is not
a universal equivalence theorem, does not cover either failure fiber, and does
not show that CP36/CP37 whole records are invariant under \(W\). The witness
therefore fixes both `universal_equivalence_claimed` and
`live_failure_equivalence_claimed` to false.

## 6. Relationship to CP41

CP41's abstract product-uniform law was conditional on an unproved claim that
the totalized live predecision map factors through \(V\). CP42 supplies a new
map for which the staged signature makes the analogous decision-word
noninterference executable. That is useful constructive evidence, but the maps
cannot yet be identified universally:

- CP42 reserves rather than executes \(F_{36}\);
- CP42 deliberately propagates transform/score refusals;
- parity is certified only for supplied successful finite instances; and
- no arbitrary-input failure-equivalence harness or proof is present.

Accordingly, CP41's symbolic fiber counts, mixture law, normalization, and TV
bounds remain conditional exactly as before. CP42 computes none of their
numeric masses and promotes none of their source-law claims.

## 7. No-operation and RNG boundary

The CP42 evaluator calls no CP36 `prepare`, CP37 `decide`, CP38 `resolve`, CP39
`coordinate`, or CP40 `admit` operation. Tests profile all public CP42
evaluation, validation, decision, and witness paths and require zero calls to
those parent operations. CP42 instead uses a narrower set of captured direct
callbacks and validates their outputs.

The source contains no Python, NumPy, or PyTorch RNG call and no fiber-product
enumeration. Focused tests snapshot all three RNG states around the staged
operations and require them to remain unchanged. Transitive certification and
binding may still execute inherited fixed runtime probes used for procedural
custody; those probes are not CP42 \(V/W\) input draws or source-law evidence.

## 8. Validation and procedural custody

Certificate, row, predecision result, applied-decision result, successful-
parity witness, and owner are exact-type, immutable, nonsubclassable,
nonpickle records. Public validation replays both \(G\) and \(H\) and compares
their semantic digests. Equal digests do not substitute for owner/certificate
identity: cross-owner record splicing is refused even when semantic digests
coincide.

The owner captures and checks local builders/validators, direct CP28/CP30
callbacks, the CP37 quota primitive, CP41--CP36 ancestry operations, dependency
globals and classes, local and late public surfaces, and absent builtin-shadow
globals. Hostile tests require mutations and redigested semantic forgeries to
fail before substituted callbacks execute.

These controls are same-process procedural custody under a trusted unchanged
runtime. They do not provide cryptographic authentication, portable loaded-
code integrity, protection against concurrent monkeypatching, or resilience to
concurrent/ABA mutation of external parent records.

## 9. Claim matrix

Positive scope is limited to:

- exact CP41 owner/hypothesis and transitive CP36/CP37 identity binding;
- exact ordered proposal/decision coordinate partition binding;
- a partial bounded \(G^{42}_{r,j}(V)\) whose only random-word input is
  \(V\), on calls whose direct CP28/CP30 stages do not refuse;
- all attempts scored before quota construction and a complete quota tuple
  before the decision stage;
- a separate \(H\) with full-\(W\) preflight before its first comparison;
- modeled quota-failure pass-through without decision-word access;
- exact selected/exhausted first-success semantics;
- deterministic \(G\) and \(H\) replay validation;
- finite supplied successful predecision/threshold projection parity; and
- zero CP36--CP40 operational calls and no RNG/fiber enumeration.

False, reserved, or absent scope includes:

- an executable preparation-failure branch;
- universal live CP36/CP37 failure or whole-record equivalence;
- discharge of CP41's factorization hypothesis;
- a live Philox/product-uniform/source law or physical randomness certificate;
- numeric source fibers, failure probabilities, batch/configuration masses,
  selection probabilities, or conditioned bounds;
- a live initializer distribution or general initializer admission;
- tag-3 semantic payload generation, Brownian coupling, drift, split steps, a
  path, liveness, or a complete sampler;
- scientific, model-quality, or cross-domain generality promotion; and
- portable, cryptographic, concurrent-mutation, or loaded-code-closure
  custody.

## 10. Focused-test coverage

The frozen 29-test primary matrix covers public APIs/signatures/exports; exact
one- and two-attempt coordinate partition/interleaving; \(V\)-only
\(G^{42}\); interior \(K-1/K\) half-open quota boundaries; ready-path
full-\(W\) preflight; a private-constructor modeled-failure boundary; semantic
projection excluding bound \(W\) data; finite successful live
predecision/threshold projection parity; a separate one-instance \(H\)-outcome
comparison; zero CP36--CP40 operations and unchanged RNG; sealing; redigested and
cross-owner forgeries; row chronology; cached callback, local surface,
dependency/class, late-surface, policy, and builtin-shadow hostility; exact
uint64 and non-Boolean integer domains; hostile configuration/event/coordinate
preflight; exact nested digest-text preflight; claim flags; source-AST
exclusions; package export isolation; and the actionable optional-PyTorch
boundary.

The additive supplement separately targets \(K=0\) and \(K=2^{64}\) in the
validated pure \(H^{42}\) constructor, late-malformed \(W\) through the public
owner, dynamic all-transform/all-score-before-first-quota chronology, and the
actual \(G^{42}\) exact-exception catch followed by public-\(H^{42}\)
pass-through under a clearly labelled profiler-injected CP37 quota exception.
The injected case is branch evidence, not proof that a valid unchanged parent
naturally reaches quota failure. The supplement does not by itself establish
public-owner \(G^{42}/H^{42}\) endpoint integration at both quota extremes.

## 11. Final focused and inherited evidence

Frozen checkpoint-42 identities:

- source SHA-256:
  `a6dbe506c289992ec797a32b6e034a41681af5f18f5721f7c2e1a87af66d2a71`;
- focused-test SHA-256:
  `8814ba75e4b7eff2bd90309d1cd139a6c313dfaf16009e4e4e0497598610b153`;
- focused result: **29/29 passed**;
- pytest time: **3599.47** seconds; and
- external wall time: **3600.09** seconds.

Additive supplement identity and evidence:

- supplement SHA-256: `d3b8d1213ea4c94cd776f0628d2bae56fed4e041a975571d936bc43ab749e9fe`;
- supplement result: **5/5 passed**;
- pytest time: **1273.25** seconds; and
- external wall time:
  **1274.44** seconds.

One earlier supplement-development candidate, SHA-256
`a9f73febb6c24737812c3720992f620a8fdbccfff5c9bea6d87ff662566c841f`,
produced **4 passed, 1 failed** in **1255.87** seconds of pytest time and
**1256.56** seconds external wall time. Its dynamic chronology assertion
incorrectly expected one CP30 score call per attempt; the trace correctly
showed that exact CP30 validation replays every score, for two calls per
attempt, all before the first quota. That assertion was corrected. The failed
development run is retained here for transparency and is not final evidence.

The final commands use the locked macOS-arm64 Python 3.11 reference
environment, disable the pytest cache, and treat warnings as errors. Static
gates are **PASS (Black, pyflakes, Python 3.9 byte-compilation, ASCII,
<=88 columns, and 5-test collection)**. Final independent review is
**PASS (independent audit: P0=P1=P2=0)**.

Inherited direct-parent CP41 exact-hash evidence is:

- source SHA-256:
  `79827f05b1a157dfaaed53146a17a7f9e006170c36bf6823510a87d338abe254`;
- focused-test SHA-256:
  `36e445057613dff7ea5d0606fa4c7924886549b57f94b58c4b3850c51678fcc3`;
- historical result: **28/28 passed** in **759.21** seconds of pytest time and
  **759.70** seconds external wall time.

The exact CP41 pair was rerun as a separate regression for checkpoint 42:
**28/28 passed** in
**805.41** seconds of pytest time and
**806.05** seconds external wall time. This fresh
record does not relabel inherited evidence.

The certificate field `passed` is an internal truth-matrix and contract-
consistency flag. It is not the focused test result, an equivalence theorem,
the CP41 hypothesis discharge, or an empirical/scientific claim.

## 12. Disposition and remaining dependencies

The CP42 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. Formal
Tests 28 and 29 remain **OPEN**, Test 30 remains **PENDING**, and `R2-HYBRID`
remains **NOT RUN**. No C-row, R-slot, nonconfirmatory-evidence row, novelty
decision, model-quality result, generality statement, or manuscript conclusion
is promoted. The venue-neutral TeX manuscript remains untouched.

The supplement's \(F_{37}\) case is profiler-injected exact-exception branch
evidence, not evidence that an unchanged valid parent naturally reaches that
failure. Its \(K=0\) and \(K=2^{64}\) cases validate the pure \(H^{42}\)
constructor, not public-owner \(G^{42}/H^{42}\) endpoint integration.

CP42 leaves separate:

1. an arbitrary-input equivalence proof or exhaustive failure-path
   differential harness relating CP42 \(G\) to live CP36/CP37;
2. an executable, semantically justified preparation-failure atom;
3. numeric source-fiber/failure/selection evaluation and any proved live-
   Philox-to-product-uniform approximation;
4. ungated exact ideal rejection, global analytic normalization, SIR, and
   remaining strategy admission;
5. semantic tag-3 payload/coordinate generation and global address guarantees;
6. Brownian consumption/coupling, drift, split steps, and a path; and
7. the complete learned/general sampler and Formal Tests 28--30.

Until those dependencies close, CP42 may be cited only as **a bounded staged
reference evaluator implementing partial decision-word-free
\(G^{42}_{r,j}(V)\), complete
predecision quotas, separate fully preflighted \(H\), and finite successful
predecision/threshold projection parity, without universal live-failure
equivalence or discharge of CP41's source-law hypothesis**.
