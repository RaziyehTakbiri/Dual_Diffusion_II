# One-Allocation Factorized Execution Adapter: Incremental Code Audit

**Audit status:** **PASS WITH EXPLICIT SCOPE LIMITS**  
**Audit date:** 2026-08-16  
**Implementation:**
[checkpoint-44 source](../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter.py)  
**Focused tests:**
[checkpoint-44 tests](../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter.py)  
**Direct semantic parent:**
[checkpoint-43 factorization closure](plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure_code_audit.md)  
**Abstract-law parent:**
[checkpoint-41 failure-aware source law](plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law_code_audit.md)  
**Method contract:** [executable method specification](executable_method_spec.md)  
**Claim controls:** [claim ledger](claim_ledger.md)

This document maps the forty-fourth incremental implementation checkpoint.
CP44 adds a new operational route that acquires one complete checkpoint-27
rejection-protocol capsule and feeds its exact word partition to checkpoint
43's supplied-word combined map. The route is additive: it does not modify,
call, or claim equivalence to the legacy checkpoint-36 `prepare` followed by
checkpoint-37 `decide` route.

The strongest supported statement is pointwise on calls that actually return
a CP44 result after successful source acquisition and final custody checks.
For one fixed certified owner and one exact request, the canonical semantic
projection of that result is the projection of the single retained CP43
combined result. Refusal before the combined call and refusal after CP43 has
evaluated both produce no CP44 result and remain outside the CP43 semantic
codomain. A separate finite product-uniform premise yields a symbolic CP41-form
pushforward only together with CP43's fixed-runtime, deterministic, replay-
stable total-\(G\) premise under its declared typed-error contract. The
implementation proves neither premise for live Philox words. This checkpoint
promotes no scientific, model-quality, application-generality, initializer-
admission, path, or sampler claim.

## 1. Exact object of review

The frozen source contains `1829` lines and has SHA-256

`42d0bdbf112628e7c2589f7e57b79e60b31b77105cd7be324716198dd3d63e9d`.

The frozen focused test contains `829` lines, collects exactly `26` cases,
and has SHA-256

`e0ad09b5b6bbc2143331d5e82c2eabf8d505f1829e25a321273eb73e34c442d6`.

The module exports a sealed certificate, sealed result, immutable owner,
procedural custody error, certification function, exact-owner matching
function, and certificate-validation function. Its execution method accepts
only an exact uint64 `run_id` and exact uint64 `initialization_index`; there is
no caller RNG, retry count, fallback mode, or rollback parameter.

The audit distinguishes three layers that must not be conflated:

1. the CP27 source boundary and initial capsule checks, which either reach the
   CP43 call with a complete validated capsule or refuse without a CP44 result;
2. the CP44 deterministic word transformation and CP43 invocation, which
   yield one retained CP43 applied record only if CP43 and every later
   structural/custody check return successfully; and
3. the optional abstract semantic-map model, which assumes a fixed runtime,
   deterministic replay-stable total CP43 \(G\), and a product-uniform full word
   tuple, none of which is asserted for the live source.

The exact policy, scope, theorem, source-failure statement, and abstract
corollary are bound into the certificate payload and runtime digest. Their
verbatim exported values are recorded in Section 12.

## 2. Deterministic map and pointwise theorem

Fix a certified CP44 owner, request coordinates \((r,j)\), inherited attempt
budget \(A\), inherited proposal-word count \(M\), and

\[
D=2^{64}.
\]

One successful CP27 rejection allocation returns a complete, validated,
attempt-interleaved word capsule

\[
Z=(z_0,\ldots,z_{M+A-1})\in[D]^{M+A}.
\]

The full tuple is flattened in chronological CP27 entry order. Within every
attempt, the certified CP36 layout places all proposal/transformation blocks
before its final one-word rejection-decision block. The exact CP43 splitter
therefore defines a coordinate permutation

\[
\operatorname{split}_{43}(Z)=(V,W),
\qquad V\in[D]^M,
\qquad W\in[D]^A.
\]

CP44 independently reconstructs this partition from the frozen CP36 block
layout, requires equality with the CP43 split, invokes CP43 join, and requires

\[
\operatorname{join}_{43}(V,W)=Z.
\]

It then invokes the exact CP43 combined entry point once. With CP43's
predecision map \(G^{43}_{r,j}\), private semantic kernel
\(H^{43}_{\mathrm{sem}}\), and combined map \(T^{43}_{r,j}\), the executable
map is

\[
Z
\xmapsto{\operatorname{split}_{43}}
(V,W)
\xmapsto{T^{43}_{r,j}}
T^{43}_{r,j}(V,W)
=H^{43}_{\mathrm{sem}}\!\left(G^{43}_{r,j}(V),W\right).
\]

Let \(\pi\) be the canonical CP44 projection

\[
\pi(y)=
\bigl(
\operatorname{status}(y),
\operatorname{comparison\_count}(y),
\operatorname{selected\_attempt\_index}(y),
\operatorname{selected\_configuration\_sha256}(y)
\bigr).
\]

For every exact valid \((r,j)\) whose call returns a CP44 result after the
single allocation produced a complete validated \(Z\) and all final custody
checks passed, CP44 constructs its semantic fields directly from the exact
CP43 applied record and requires

\[
\pi\bigl(T^{44}_{r,j}(Z)\bigr)
=\pi\bigl(T^{43}_{r,j}(V,W)\bigr).
\]

This equality is by construction: the adapter calls CP43's combined operation
and retains its exact applied record. It is not Python-record equality between
CP44 and CP43, and it is not equality to a CP36 or CP37 operational result.
The CP44 record additionally retains the CP27 capsule, its entry digests, all
full/proposal/decision words, partition digests, source-boundary flags, and a
CP44 result digest. Those fields have no counterparts in the displayed
semantic projection.

## 3. Execution chronology and the meaning of one allocation

The successful execution chronology is fixed as follows:

1. validate exact request coordinates and freeze the CP44/CP43/CP37/CP36/CP27
   owner snapshot;
2. invoke the exact CP27 `allocate` method once for the complete CP36 rejection
   layout, with zero additional selection words;
3. apply CP36's deep structural protocol-tree preflight and take a deep source
   snapshot;
4. flatten every CP27 entry's raw words in chronological order;
5. split with CP43, compare against the CP36-layout partition, join with CP43,
   and require exact round-trip equality;
6. invoke CP43 `evaluate_and_apply` once on \((r,j,V,W)\);
7. structurally validate the returned CP43 applied record without replaying G
   or H;
8. construct and structurally validate the sealed CP44 record; and
9. recheck source, owner, and dependency custody before return.

"One allocation" has a narrow and auditable meaning: CP44 makes one
adapter-level call to the exact CP27 `allocate` operation. CP27's own
implementation constructs a result and then calls its inherited public
validator, which deeply and deterministically replays the CP27 parent result.
CP44 deliberately records
`inherited_cp27_internal_validation_replay_free=False`. It does not claim one
underlying stream computation, a replay-free CP27 allocation, or physical
single-read entropy acquisition.

After CP27 returns, CP44 adds no second CP27 allocation and does not call the
CP27 public replay validator during `execute`. It also adds no extra source
word request, caller RNG, Python/NumPy/PyTorch global RNG use, retry, fallback,
or rollback. The only later CP27 *result-record validation* is the structural
validator used by the separate CP44 public `validate_result` method. Owner and
certificate custody may still query the captured CP27 live binding; that is
neither source generation nor CP27 result replay.

CP43 join performs its own inverse split check, so a successful execution can
enter the captured split implementation more than once without violating the
single combined-evaluation claim. The certified once-only operation is CP43's
combined G-then-semantic-H evaluation, not every pure partition helper.

## 4. Source or custody refusal is not \(F_{36}\) or \(F_{37}\)

Source acquisition and initial capsule validation precede the CP43 semantic
map, but the custody envelope does not end there: CP44 rechecks source, owner,
and dependency custody after the combined evaluation and again before return.
The operational partition is therefore

\[
\mathcal E^{44}_{r,j}=
\begin{cases}
\bot_{\mathrm{pre}},
  &\text{refusal before the CP43 combined evaluation},\\
\bot_{\mathrm{post}},
  &\text{CP43 or later structural/custody refusal before CP44 return},\\
F_{36},
  &\text{CP44 returns a result with preparation-failure status},\\
F_{37},
  &\text{CP44 returns a result with quota-certification-failure status},\\
x,
  &\text{CP44 returns a result selecting configuration }x,\\
E,
  &\text{CP44 returns a result exhausting all attempts}.
\end{cases}
\]

Here \(\bot_{\mathrm{pre}}\) and \(\bot_{\mathrm{post}}\) are meta-level refusal
markers, not result values and not atoms in CP43's codomain. Exact CP27
allocation exceptions propagate with
their original runtime object and type. Malformed source records, CP36
preflight failure, and split/join mismatch refuse before CP43 evaluation.
Repeated owner, dependency, and source-custody checks can instead refuse after
CP43 has evaluated but before a CP44 result is returned. Invalid request
coordinates refuse before allocation. Neither refusal chronology is caught
and relabelled as \(F_{36}\) or \(F_{37}\), and no refusal probability is
materialized.

Only after the acquisition-side source checks complete can CP43's exact
declared typed semantics produce `preparation_failure` or
`quota_certification_failure`. Generic exceptions, declared-error subclasses,
and other unexpected post-source exceptions remain refusals under CP43's
contract. A later custody refusal can also discard an already evaluated CP43
record before CP44 returns. CP44 neither widens CP43's caught error surface nor
totalizes any of these exceptions or refusals.

For an \(F_{36}\) or \(F_{37}\) CP43 result, CP43's applied record has
`decision_words=None`, zero comparisons, no selected index, and no selected
configuration digest. CP44 nevertheless retains \(W\) inside the complete
source capsule. That retained tuple is source-boundary custody evidence; it is
not evidence that CP43's semantic failure branch inspected or consumed W.

There is an important chronology limit. CP44 necessarily flattens, validates,
splits, joins, and later hashes the complete source capsule, including W. Thus
the adapter itself structurally handles W before CP43 completes G. The
certificate correctly fixes
`semantic_no_w_access_before_g_at_adapter_level_certified=False`. The narrower
CP43 semantic statement remains intact: CP43's private failure kernels do not
interpret W as decision words.

## 5. Exact ancestry and procedural custody

Certification begins from one exact CP43 owner and resolves the exact live
chain

\[
\mathrm{CP43}\longrightarrow\mathrm{CP37}
\longrightarrow\mathrm{CP36}\longrightarrow\mathrm{CP27}.
\]

It requires exact owner types, object identities, certificate identities, and
the CP37-to-CP36 and CP36-to-CP27 parent relationships. Through the CP43 and
CP42 certificates it also binds the CP42 certificate, CP41 certificate,
CP41 factorization-hypothesis digest, and their stored runtime owner
identities. Process-parameter digest, attempt budget, block counts, stream and
word counts, full/proposal/decision coordinate digests, and raw-word domain
size must agree across the ancestry.

The owner caches exact callback objects for CP27 allocation and structural
validation, CP36 preflight/snapshot/custody, CP43 split/join/combined
evaluation, and CP43 structural applied-record validation. Every owner
snapshot checks that the dependency module surfaces, owner methods,
properties, cached callbacks, exact certificate identities, and transitive
ancestry remain unchanged. Long operations recheck those snapshots around
dependency calls.

Source custody uses CP36's deep protocol-tree snapshot and parent-unchanged
guard. Result validation additionally snapshots the CP44 result, CP43 applied
record, and CP43 predecision record and checks field identities around nested
validation. Exact record types, sealed construction tokens, nonsubclassable
classes, frozen public surfaces, and nonpickleability raise the cost of
ordinary record substitution.

CP44 fingerprints its selected Python code objects with explicit marshal
version 2 after recursively checking that their constant graphs contain only
exact `None`, Boolean, integer, text, tuple, and code-object values. The runtime
payload binds the marker
`python-marshal-v2-no-reference-table-exact-constant-domain-v1`. Unlike the
default marshal versions 3 and 4, version 2 does not encode live shared-
reference topology; retaining CP44's real nested custody code or installing
the call profiler therefore cannot change the digest by reference count alone.
The regression also requires the digest to change under an actual selected-
function code replacement. This repair applies to CP44's selected-code
fingerprint only. It does not modify CP43 or certify arbitrary-instrumentation
stability for the inherited ancestry.

These remain same-process procedural controls. Runtime `id` values, semantic
SHA-256 digests, code-object hashes, and observation-point custody checks are
not cryptographic authentication, portable attestation, thread isolation, or
proof against arbitrary process compromise. They do not bind every function
default, global, closure value, native callee, or hostile interpreter state.
The certificate expressly leaves loaded-code integrity and concurrent/ABA
mutation resilience uncertified.

## 6. Structural, nonreplaying public validation

`validate_result` is intentionally different from CP43's public replay
facade. It performs structural and custody validation only:

- it checks the exact CP44 result type before operational work;
- it takes owner, source-tree, CP44-record, CP43-applied-record, and
  CP43-predecision snapshots;
- it invokes CP27's private structural record validator, not CP27 `allocate`
  or CP27's public deep replay validator;
- it reruns CP36 structural preflight but never CP36 `prepare`;
- it invokes CP43's private structural applied-record validator, not CP43's
  public validating replay facade;
- it re-flattens the retained capsule, reconstructs the CP36 layout
  partition, checks hashes and exact identities, and recomputes the CP44
  projection and result digest; and
- it checks custody between these stages.

Consequently public CP44 validation performs no new source allocation, no
CP36 preparation, no CP37 decision, no CP43 G evaluation, no CP43 semantic-H
application, and no CP43 combined evaluation. "Nonreplaying" refers to those
operational computations. It does not mean zero traversal, zero hashing, or
zero deterministic structural recomputation.

This design avoids a subtle invalid proof route. Calling CP43's public applied
decision validator would replay G and could make validation depend on whether
a transient typed failure recurs. CP44 instead binds the exact CP43 applied
record structurally and retains the pointwise construction witness created by
the single combined evaluation.

## 7. Relationship to the legacy CP41 premise

CP41's original factorization hypothesis concerned an unchanged live-parent
route. CP44 does not prove that route factorizes. It constructs a different
operational path:

\[
\text{CP27 full capsule}
\longrightarrow\text{CP43 supplied-word factorization},
\]

while explicitly bypassing CP36 `prepare` and CP37 `decide`. This supplies an
executable factorization by construction for the new adapter, not a theorem
about the legacy composition. In particular, CP44 does not establish:

- CP36 preparation-record equivalence;
- CP37 decision-record equivalence;
- legacy success- or failure-path equivalence;
- whole-record equality;
- equality of retry, validation, or exception chronology; or
- discharge or theorem-level supersession of CP41's original live-parent
  premise.

The CP41 certificate and hypothesis digest are retained as exact ancestry and
claim-context bindings. Their presence in CP44 is not evidence that the
hypothesis has been proved.

## 8. Abstract product-uniform corollary

Fix one certified owner and runtime for which CP43 \(G^{43}_{r,j}\) is
deterministic, replay-stable, and total under its declared typed-error contract.
This is an external premise inherited from CP43's abstract corollary, not a
conclusion of product-uniformity. Define the abstract successful-source
semantic map

\[
S^{44}_{r,j}(Z)=T^{43}_{r,j}(\operatorname{split}_{43}(Z)).
\]

Now introduce the separate full-word premise

\[
Z\sim\operatorname{Unif}\bigl([D]^{M+A}\bigr)
\]

with product measure over the exact, distinct CP36-derived coordinates.
Because `split43` is a coordinate permutation, this premise implies

\[
V\sim\operatorname{Unif}([D]^M),\qquad
W\sim\operatorname{Unif}([D]^A),\qquad V\perp W.
\]

Let CP43's G fibers be \(F_{36}\), \(F_{37}\), and ready bundles \(B\). Define

\[
N_{36}=\left|\left(G^{43}_{r,j}\right)^{-1}(F_{36})\right|,
\quad
N_{37}=\left|\left(G^{43}_{r,j}\right)^{-1}(F_{37})\right|,
\quad
N_B=\left|\left(G^{43}_{r,j}\right)^{-1}(B)\right|,
\]

and

\[
\phi_{36}=\frac{N_{36}}{D^M},\qquad
\phi_{37}=\frac{N_{37}}{D^M},\qquad
\lambda_B=\frac{N_B}{D^M}.
\]

If \(e_B\) is the CP43 conditional exhaustion probability under independent
uniform W for ready bundle B and \(m_B(x)\) is its conditional selected-output
mass, the \(S^{44}\) pushforward has the CP41 form

\[
\begin{aligned}
Q_{44}(F_{36})&=\phi_{36},\\
Q_{44}(F_{37})&=\phi_{37},\\
Q_{44}(E)&=\sum_B\lambda_B e_B,\\
Q_{44}(x)&=\sum_B\lambda_B m_B(x).
\end{aligned}
\]

This corollary is finite once both the fixed-runtime total-\(G\) and product-
uniform premises are introduced; it is not an empirical claim. The
implementation does not
materialize any fiber, cardinality, \(\phi\), \(\lambda\), \(e_B\), or
\(m_B\). More importantly, it does not prove that a live CP27/Philox capsule
has the assumed distribution, that V and W are live-independent, that words
are fresh, or that allocation success is independent of their values. Neither
pre-combined nor post-combined refusal has mass in this abstract semantic-map
pushforward. An unconditional adapter distribution would require a separate,
currently absent probability model for acquisition and refusal.

## 9. The unresolved \(F_{37}\) boundary

CP44 inherits CP43's exact typed `quota_certification_failure` branch. The
branch is a bounded post-source semantic result only after a complete capsule
has been acquired. It is not a source failure.

The prior arithmetic audit substantially narrows the possible natural CP37
failure route: valid parent gaps are dyadic and remain within the certified
integer, coefficient, and Decimal resource bounds. The unresolved case is
whether a valid adaptive dyadic gap can leave the scaled exponential interval
straddling an integer after the frozen 3,072-digit terminal precision. The
current chain supplies neither a natural valid-parent example that reaches
this ambiguity nor a proof that it cannot occur.

Accordingly CP44 fixes all of the following to false:

- `natural_f37_failure_exhibited`;
- `natural_f37_unreachability_proved`; and
- `adaptive_floor_separation_proved`.

Fault injection of the exact CP37 quota error is valid branch and custody
evidence, but it is not natural-reachability evidence. Whether the
\(F_{37}\) G fiber is empty changes the corresponding symbolic mass in the
abstract corollary; it does not change the pointwise split-and-compose
factorization.

## 10. Claim matrix

Positive scope is limited to:

- one exact CP43 owner and its certified CP42/CP41 context plus live
  CP37/CP36/CP27 ancestry;
- one adapter-level CP27 full-capsule allocation per exact valid request;
- complete CP36-layout preflight, chronological flattening, and exact CP43
  split/join coordinate custody;
- one CP43 combined G-then-semantic-H evaluation for each returned CP44 result;
- pointwise equality of the CP44 and CP43 canonical semantic projections on
  the returned-result domain;
- exact preservation of CP43's post-source preparation-failure,
  quota-certification-failure, selected, and exhausted statuses;
- explicit separation of both pre-combined and post-combined refusal from
  \(F_{36}\) and \(F_{37}\);
- source-decision-word retention as boundary evidence, including on semantic
  failure branches;
- structural public validation with no allocation, G, H, CP36 `prepare`, or
  CP37 `decide` replay;
- a new factorized route that bypasses the legacy CP36/CP37 route; and
- the CP41-form symbolic pushforward for the abstract successful-source
  semantic map under explicit external total-\(G\) and product-uniform premises.

False, absent, or unresolved scope includes:

- replay-free internals inside the inherited CP27 `allocate` operation;
- return after every successful source allocation, unconditional adapter
  totality, or a refusal-mass model;
- semantic no-W-access-before-G at the CP44 structural adapter layer;
- source-boundary totalization, source-failure mass, or allocation-success
  probability;
- generic exception totalization, retry, fallback, or rollback;
- equivalence to CP36 `prepare`, CP37 `decide`, their failures, their complete
  records, or their operational chronology;
- discharge or theorem-level supersession of CP41's original live-parent
  hypothesis;
- live Philox product-uniformity, V/W independence, freshness, randomness, or
  a live source law;
- natural \(F_{37}\) reachability, \(F_{37}\) impossibility, or uniform terminal
  adaptive-floor separation;
- numeric fibers, masses, initializer distributions, or source comparisons;
- global initializer, path, or sampler admission;
- scientific performance, model quality, or cross-domain generality; and
- portable runtime integrity, loaded-code attestation, cryptographic
  authentication, or arbitrary concurrent/ABA mutation safety.

## 11. Hostile-test design

The focused test source is designed to challenge the theorem boundary rather
than only exercise a successful example. Its principal controls are:

- exact public export and signature checks, certificate ancestry identity,
  positive/negative truth-table enforcement, and exact matching helpers;
- profiler-observed successful chronology for one CP27 allocation, CP27's
  inherited internal public validation and its exact three structural
  validations, one CP43 combined/G/H evaluation, zero CP36 `prepare`, and zero
  CP37 `decide`;
- exact flatten/split/join order, retained word/digest equality, and canonical
  projection equality;
- public-validation profiling requiring CP27 and CP43 structural validators
  while excluding CP27 allocation/public replay, CP43 combined/G/H, and the
  legacy CP36/CP37 route;
- exact source-exception identity propagation with no CP43 semantic call;
- injected exact post-source \(F_{36}\) and \(F_{37}\) branches, checking that
  CP43 retains no semantic W while CP44 retains W only as capsule evidence;
- generic and exact-error-subclass propagation rather than relabelling, with
  Python/NumPy/PyTorch global-RNG snapshots unchanged on refusal;
- sealed construction, nonsubclassability, nonpickleability, cross-owner
  refusal, plain tampering, and adversarial redigesting of false claim flags;
- exact-message nested source and semantic-record mutation, plus persistent
  mid-operation source mutation that completes one CP43 G/H evaluation before
  late custody refusal and leaves global RNG state unchanged;
- owner callback rebinding and dependency-surface drift;
- explicit marshal-v2 AST custody, constant-domain enforcement, runtime-digest
  stability while CP44's real nested custody code is retained and under
  profiling, and sensitivity to an actual selected-function code replacement;
- an exact AST import allowlist, no dynamic `__import__`/`import_module`, and
  static screening for legacy `.prepare(` / `.decide(` calls;
- code-object inspection showing no second CP27 structural validation is added
  inside `execute`; and
- invalid uint64 request and invalid result domains refusing before allocation
  or operational replay.

These controls are appropriately adversarial but must be interpreted
narrowly. Profiler counts are execution evidence for the exercised runtime,
not a language-level call-graph proof. AST and lexical screens are source
controls, not proof against arbitrary dynamic behavior. Fault-injected
\(F_{36}\) and \(F_{37}\) cases establish branch semantics, not their natural
frequency or reachability. Mutation checks cover the injected observation
windows, not all concurrent or ABA schedules.

## 12. Exact exported contract text

The following values are reproduced verbatim from the frozen source. The
once-only exact-string check in Section 13 confirms that all six blocks occur
exactly once and byte-match that source.

**Policy**

```text
exact-checkpoint43-owner-and-transitive-checkpoint27-36-37-41-42-ancestry;one-exact-checkpoint27-full-prefix-allocation-per-adapter-call;complete-CP36-layout-word-capsule-validation-before-factorized-execution;exact-CP43-V-W-coordinate-split-and-order;single-CP43-combined-G-then-semantic-H-evaluation;no-CP36-prepare-or-CP37-decide-invocation;no-second-source-allocation-extra-word-caller-global-RNG-retry-fallback-or-rollback;pre-combined-source-refusal-and-post-combined-exception-or-custody-refusal-remain-no-result-not-F36-or-F37;post-source-typed-F36-F37-selected-exhausted-semantics-inherited-from-CP43-for-returned-results;pointwise-returned-result-adapter-relation;abstract-supplied-product-uniform-semantic-map-corollary-only-under-fixed-runtime-deterministic-replay-stable-total-G43-typed-error-premise;new-factorized-operational-path-bypasses-but-does-not-prove-the-legacy-CP41-live-parent-premise-v2
```

**Scope**

```text
bounded-one-allocation-factorized-execution-adapter;for-exact-valid-r-j-and-a-returned-CP44-result-after-one-successful-validated-source-allocation-and-final-custody;one-full-interleaved-CP36-layout-word-capsule-split-into-V-and-W;pointwise-canonical-semantic-projection-equality-to-CP43-combined-semantics;typed-post-source-preparation-and-quota-failure-atoms;pre-or-post-combined-refusal-is-no-result-not-F36-or-F37;F37-is-bounded-quota-certification-failure-with-reachability-unresolved;abstract-supplied-word-product-uniform-semantic-map-pushforward-only-under-total-G43-premise;not-unconditional-return-after-successful-allocation-or-live-adapter-law;not-legacy-CP36-prepare-CP37-decide-failure-record-or-whole-record-equivalence;not-discharge-of-CP41-original-live-parent-factorization-hypothesis;not-live-Philox-uniformity-independence-freshness-or-randomness;not-numeric-fibers-source-or-refusal-masses-global-initializer-admission-path-or-sampler;not-scientific-model-quality-or-cross-domain-generality-evidence;trusted-runtime-procedural-not-portable-or-cryptographic-custody
```

**Theorem**

```text
for-one-exact-valid-r-j-on-every-call-that-returns-a-CP44-result-after-the-single-inherited-CP27-allocation-returned-a-complete-validated-full-word-capsule-Z-in-D^(M+A)-and-final-structural-and-custody-checks-passed;with-split43(Z)=(V,W)-the-adapter-made-no-further-source-allocation-and-pi(T44_rj(Z))=pi(T43_rj(V,W))=pi(H43_sem(G43_rj(V),W));pre-combined-source-refusal-and-post-combined-exception-or-custody-refusal-produce-no-CP44-result-and-are-neither-F36-nor-F37;under-a-separate-fixed-runtime-deterministic-replay-stable-total-G43-typed-error-premise-and-abstract-product-uniform-law-on-Z-the-coordinate-split-makes-V-and-W-independent-product-uniform-and-the-induced-successful-source-semantic-map-has-the-CP41-form-with-G43-fibers;this-is-not-a-live-Philox-law-unconditional-adapter-law-or-legacy-CP36-37-equivalence
```

**Source-failure semantics**

```text
CP27-allocation-exceptions-propagate-unchanged-with-no-result;malformed-source-preflight-split-or-join-failure-refuses-before-the-CP43-combined-call;unexpected-CP43-exception-or-late-owner-dependency-source-custody-failure-refuses-after-source-acquisition-and-may-follow-CP43-evaluation;every-refusal-produces-no-CP44-result-is-neither-F36-nor-F37-and-has-no-retry-fallback-or-relabeling
```

**Abstract product-uniform corollary**

```text
for-one-fixed-certified-owner-and-runtime-with-deterministic-replay-stable-total-G43-under-the-declared-typed-error-contract-and-exact-distinct-CP36-derived-coordinates;define-the-abstract-successful-source-semantic-map-S44_rj(Z)=T43_rj(split43(Z));if-an-abstract-supplied-full-word-capsule-Z-is-product-uniform-on-D^(M+A);then-split43-is-a-coordinate-permutation-so-V-and-W-are-independent-product-uniform;with-G43-fiber-masses-phi36-phi37-and-lambda_B-the-S44-pushforward-satisfies-Q44(F36)=phi36;Q44(F37)=phi37;Q44(E)=sum_B(lambda_B*e_B);Q44(x)=sum_B(lambda_B*m_B(x));no-operational-source-or-refusal-mass-numeric-fiber-or-mass-is-materialized-and-no-live-Philox-source-or-unconditional-adapter-law-follows
```

**CP41-form symbolic mixture**

```text
under-one-fixed-certified-owner-and-runtime-with-deterministic-replay-stable-total-G43-under-the-declared-typed-error-contract-a-separate-abstract-product-uniform-law-on-Z-and-the-CP44-CP43-factorization-by-construction-not-the-CP41-legacy-parent-factorization-premise;G43(V)=F36-or-F37-or-B;N36=card(G43^-1(F36));N37=card(G43^-1(F37));N_B=card(G43^-1(B));phi36=N36/D^M;phi37=N37/D^M;lambda_B=N_B/D^M;the-abstract-successful-source-semantic-map-S44-pushforward-has-Q44(F36)=phi36;Q44(F37)=phi37;Q44(E)=sum_B(lambda_B*e_B);Q44(x)=sum_B(lambda_B*m_B(x));CP41-form-symbolic-only-no-operational-source-or-refusal-mass-fibers-or-numeric-masses-materialized
```

## 13. Final execution evidence

The authoritative final command was

```text
/usr/bin/time -p env PYTHONPATH=src /private/tmp/diffusion-recovery-20260815/.venv-m1/bin/python -m pytest -p no:cacheprovider -W error --durations=26 -q tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter.py
```

It collected exactly **26** cases and returned **26/26 passed** in
**50165.86** seconds of pytest time and **50166.38** seconds external wall
time (`user 47414.26`, `sys 2520.59`, exit `0`). There were no failures,
errors, skips, xfails, xpasses, or warnings. Pre/post hashes remained

- source: `42d0bdbf112628e7c2589f7e57b79e60b31b77105cd7be324716198dd3d63e9d`;
  and
- focused test:
  `e0ad09b5b6bbc2143331d5e82c2eabf8d505f1829e25a321273eb73e34c442d6`.

The post-run static record is **PASS**:

- Black left both frozen files unchanged;
- pyflakes and flake8 `E9,F63,F7,F82` passed;
- Python 3.9.13 and the locked Python 3.11.5 runtime passed syntax
  compilation;
- ASCII screening and exact 26-case collection passed;
- the exact 16-symbol public export/signature check passed;
- all six contract strings occur once and byte-match the frozen source; and
- all 18 lines longer than 88 columns were individually reviewed and are
  formatter-stable, identifier-dominated lines.

Independent CP44 source and focused-test review reports **P0=P1=P2=0**.

Frozen ancestry identities were rechecked after the final run:

- CP36 source/test:
  `fd87881c04801510e74edde8676583d7068b387c3e091adeba8732f6b6ce4b59` /
  `8a7469dc18ab47c3b2dde1a3a8eeeb86c7764709a511b1b2ed105dd081d1ceeb`;
- CP37 source/test:
  `acbe2bd14305560360ec40595314a19a66f37ceec22d4e22321c05f14d050fed` /
  `ea255cc36ee17c20b355e237fd5a87de89bd9458ef42f5b850124b14f6b49f91`;
- CP42 source/primary test/additive supplement:
  `a6dbe506c289992ec797a32b6e034a41681af5f18f5721f7c2e1a87af66d2a71` /
  `8814ba75e4b7eff2bd90309d1cd139a6c313dfaf16009e4e4e0497598610b153` /
  `d3b8d1213ea4c94cd776f0628d2bae56fed4e041a975571d936bc43ab749e9fe`;
  and
- CP43 source/test:
  `12977ea4c38c8f5cb595d823e129f0f9dd8e0cadb1a151247d3278464c64fd64` /
  `5f8372c4e80e5539e08444170f687af36b755998e6e96ffbdbe57331178f9944`.

No parent suite was freshly rerun for CP44. The exact-hash inherited execution
record is the historical CP43 **62/62 passed** result
(**12949.69/12950.26** seconds pytest/wall), CP42 primary **29/29 passed**
result (**3409.31/3409.78** seconds), and CP42 supplement **5/5 passed** result
(**1205.53/1205.98** seconds).

The untouched venue-neutral Markdown and TeX manuscripts retain SHA-256
values `0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8`
and `0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9`.

The four consolidated CP44 evidence documents have frozen SHA-256 identities:

- `README.md`:
  `0db8728037c07e999896913c235080a44d4841ff3d0dd247aaa310a59fbdd601`;
- `executable_method_spec.md`:
  `16e6dad8471e50d98770f1219d7a5261dbb66ae849fccf0d1477000503dae887`;
- `executable_method_audit.md`:
  `e7a04a62623db0c55deec96ad5f51e8cf66efc070c3f3f9257de107798fc1176`;
  and
- `claim_ledger.md`:
  `2be2f3b893ae8ce73a3ea1f3f4bdec3fd4e66131f00961dbb729dfda04a32685`.

Two pre-freeze runs are retained only as repair provenance, not as final
evidence. The stale-test-literal run returned **1 passed, 1 failed** in
**1051.64** seconds of pytest time and **1052.30** seconds wall time. The
default-marshal reference-topology run returned **7 failed, 11 passed, 7
errors** in **3074.72** seconds of pytest time and **3075.42** seconds wall
time. Their causes were repaired before the frozen run above.

The resulting disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. This is a
scoped software-engineering result only. It does not promote a live source,
unconditional adapter law, numeric source/refusal/fiber mass, legacy-route
equivalence, initializer/path/sampler admission, or any scientific,
model-quality, cross-domain, generality, or manuscript claim.

## 14. Disposition and remaining dependencies

At the frozen source-contract and execution-evidence boundary, CP44 is
internally coherent: it
realizes a new one-allocation factorized path by direct CP43 composition,
separates source refusal from semantic failures, binds exact ancestry and
custody, exposes only a canonical projection theorem, and states its
abstract-law corollary under the required external premise. Section 13 records
the frozen focused, static, inherited-parent, and independent-audit evidence.
The final disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

The remaining research and engineering dependencies are separate:

1. resolve the terminal adaptive-floor question for natural \(F_{37}\)
   reachability or impossibility;
2. prove a live CP27/Philox source law, or state and validate a defensible
   alternative source assumption, before promoting the abstract mixture to a
   live distributional result;
3. materialize or bound relevant fibers and masses only if a later theorem
   genuinely requires numeric distributional conclusions;
4. decide whether legacy CP36/CP37 equivalence is scientifically necessary;
   CP44 deliberately does not provide it;
5. close the remaining global initializer, payload-address, path-construction,
   liveness, and sampler-admission obligations; and
6. supply independent empirical evidence for model utility and cross-domain
   generality before making any manuscript-level scientific claim.

Until those dependencies close, CP44 may be cited only as **a fixed-owner,
returned-result-conditional, one-adapter-allocation execution path from a
complete CP27 capsule through CP43's exact split and combined semantics, with
pre- and post-combined refusal kept outside \(F_{36}/F_{37}\), canonical
semantic-projection equality by construction, structural nonreplaying public
validation, and a CP41-form symbolic corollary for an abstract semantic map
under fixed-runtime deterministic replay-stable total \(G^{43}\) and product-
uniform \(Z\)—without unconditional adapter totality, refusal mass, legacy-
route equivalence, a live Philox law, natural \(F_{37}\) resolution, numeric
masses, or scientific/model/generality promotion**.
