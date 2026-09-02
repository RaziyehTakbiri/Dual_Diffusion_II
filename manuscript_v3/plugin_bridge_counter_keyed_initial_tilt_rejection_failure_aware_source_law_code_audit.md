# Failure-Aware Abstract Rejection Source Law: Incremental Code Audit

**Audit status:** **PASS WITH EXPLICIT SCOPE LIMITS**  
**Audit date:** 2026-08-14  
**Implementation:**
[checkpoint-41 source](../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law.py)  
**Focused tests:**
[checkpoint-41 tests](../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law.py)  
**Direct capability parent:**
[checkpoint-40 target/admission](plugin_bridge_counter_keyed_initial_tilt_rejection_admission_code_audit.md)  
**Method contract:** [executable method specification](executable_method_spec.md)  
**Claim controls:** [claim ledger](claim_ledger.md)

This document maps the forty-first incremental implementation checkpoint. It
defines an **abstract product-uniform failure-aware source law conditional on
an explicit unproved factorization hypothesis**. That hypothesis says CP36's
word-free preparation success/failure projection and CP37's complete quota
tuple depend only on proposal/scoring coordinates \(V\), while one reserved
decision coordinate per attempt, \(W\), is used only after all quotas have
been certified.

The CP36--CP40 artifacts motivate but do not prove this functional
noninterference statement. CP41 binds it as an assumption, records that no
executable arbitrary-word equivalence proof exists, and does not identify the
abstract words with live fixed-address Philox replay. It enumerates no source
fiber and materializes no numeric failure, successful-batch, configuration,
exhaustion, or selection mass. The venue-neutral TeX manuscript is unchanged.

## 1. Exact mathematical boundary

Let \(D=2^{64}\), \(A\) be the attempt budget, \(V\in[D]^M\) contain every
CP36 proposal/scoring coordinate, and \(W\in[D]^A\) contain one reserved
decision coordinate per attempt. The counterfactual premise is

\[
V\sim\operatorname{Unif}([D]^M),\qquad
W\sim\operatorname{Unif}([D]^A),\qquad V\perp W.
\]

Conditional on the explicit unproved factorization hypothesis, totalize the
predecision map as

\[
G(V)\in\{F_{36},F_{37}\}\;\dot\cup\;\mathcal B,
\]

where \(F_{36}\) is preparation failure, \(F_{37}\) is quota-certification
failure, and \(B\in\mathcal B\) is a successful direct word-free batch. The
output space has four disjoint atom classes:

1. preparation failure \(F_{36}\);
2. quota-certification failure \(F_{37}\);
3. bounded decision exhaustion \(E\); and
4. configurations \(x\), including the empty configuration as a configuration
   atom rather than a failure or exhaustion atom.

The final no-cache, warnings-as-errors focused execution passed **28/28**.
Section 11 records the exact frozen identities, timings, static gates, and
independent source/test re-audit. The final independent documentation audits
report **P0=P1=P2=0**.

## 2. Coordinate partition versus factorization assumption

CP41 accepts one exact CP40 owner and derives CP39--CP36 ancestry and the CP36
and CP38 abstract-word hypotheses transitively. The normalized CP36 coordinate
template is partitioned by role: every CP28 transform block belongs to \(V\),
and each attempt's final one-word block belongs to \(W\).

Validation requires the exact attempt/block counts, a one-word final block,
the normalized stage-1/tag-7 template, pairwise distinct full coordinates,
disjoint and complete partition coverage, and parent-derived count and digest
equality in both the hypothesis and certificate.

This certifies the **coordinate partition**, not functional noninterference.
The positive field is
`reserved_decision_coordinate_partition_certified`; the executable-
factorization-proof field remains false.

## 3. Symbolic source fibers and normalized law

Define the exact but unenumerated counts and masses

\[
\begin{gathered}
N_{36}=|G^{-1}(F_{36})|,\quad
N_{37}=|G^{-1}(F_{37})|,\quad
N_B=|G^{-1}(B)|,\\
\phi_{36}=N_{36}/D^M,\quad
\phi_{37}=N_{37}/D^M,\quad
\lambda_B=N_B/D^M,\quad
\rho=\sum_B\lambda_B=1-\phi_{36}-\phi_{37}.
\end{gathered}
\]

For successful \(B\), CP38/CP40 supplies configuration masses \(m_B(x)\),
exhaustion mass \(e_B\), and \(Z_B=1-e_B\). CP41 defines

\[
\begin{aligned}
Q^{\mathrm{aug}}(F_{36})&=\phi_{36},&
Q^{\mathrm{aug}}(F_{37})&=\phi_{37},\\
Q^{\mathrm{aug}}(E)&=\sum_B\lambda_B e_B,&
Q^{\mathrm{aug}}(x)&=\sum_B\lambda_Bm_B(x).
\end{aligned}
\]

Duplicates aggregate within and across batches. Exact normalization is

\[
\phi_{36}+\phi_{37}
+\sum_B\lambda_B\left(e_B+\sum_xm_B(x)\right)=1.
\]

The symbolic common denominator is \(D^{M+A}\); its base and exponent are
recorded, but the enormous integer is not materialized. No \(N\), \(\phi\),
\(\lambda\), \(\rho\), successful-batch distribution, state mass, exhaustion
mass, or selection mass is numerically evaluated or stored.

## 4. Ideal comparison and the \(\rho=0\) boundary

The ideal comparison uses the same \(G\) and failure fibers; only successful
fibers replace \(p_j=K_j/D\) by \(r_j=e^{\delta_j}\). Hence failures have the
same mass in the ideal and dyadic laws. If \(\rho=0\),

\[
\operatorname{TV}(P^{\mathrm{aug}},Q^{\mathrm{aug}})=0.
\]

If \(\rho>0\), the finite mixture of CP38's strict fixed-\(B\) comparisons
gives

\[
\operatorname{TV}(P^{\mathrm{aug}},Q^{\mathrm{aug}})
<\frac{\rho A}{D},
\qquad
\operatorname{TV}(P^{\mathrm{aug}},Q^{\mathrm{aug}})<\frac{A}{D}.
\]

These are conditional abstract-law statements, not comparisons to the
deterministic live result.

## 5. Positive-\(S_Q\) boundary and factor-one conditioning

Let

\[
S_Q=\sum_B\lambda_BZ_B,\qquad
S_P=\sum_B\lambda_BZ_B^\star.
\]

Conservative quotas give \(S_P\ge S_Q\).
No dyadic selected law or comparison bound is defined when \(S_Q=0\).
If \(S_Q>0\), with
\(\Delta=\operatorname{TV}(P^{\mathrm{aug}},Q^{\mathrm{aug}})\),

\[
\operatorname{TV}(P^{\mathrm{sel}},Q^{\mathrm{sel}})
\le\frac{\Delta}{\max(S_P,S_Q)}
=\frac{\Delta}{S_P}
\le\frac{\Delta}{S_Q}
<\frac{\rho A}{D S_Q}
\le\frac{A}{D S_Q}.
\]

The coefficient one follows by conditioning on the shared selection set and
dividing by the larger selection mass. This is sharper than CP40's generic
factor-two ledger. CP41 stores no numeric \(S_P\), \(S_Q\), selected law, or
conditioned bound.

## 6. Arbitrary-source and live-source boundary

For any joint source law \(\nu\) on \((V,W)\), deterministic data processing
gives only

\[
\operatorname{TV}(H_\#\nu,H_\#U)\le\operatorname{TV}(\nu,U).
\]

No product-mixture formula is claimed for dependent or nonuniform \(\nu\), and
no bound between live Philox and \(U\) is supplied. CP41 is not a live Philox
law, live uniformity/independence or physical-randomness certificate, live
initializer distribution, sampled-failure semantics, ungated exact ideal
rejection law, or normalized global analytic plug-in tilt.

## 7. Descriptive no-operation API

The public declaration binds the explicit assumption. Certification creates a
sealed owner and cached symbolic specification. `owner.describe()` returns the
specification, and `owner.validate_specification(...)` validates it. These
operations call no CP40 `admit`, CP39 `coordinate`, CP38 `resolve`, CP37
`decide`, or CP36 `prepare` operation. CP41 consumes no source-law \(V/W\)
coordinate and no caller/global RNG, enumerates no fiber, and constructs no
live initializer result. Transitive certification/live-binding may execute
CP39's local fixed Philox runtime probe of three raw words for procedural
custody; that is not a live source draw, result, or fiber enumeration.

The public operations are:

- `declare_initial_tilt_rejection_predecision_factorization_hypothesis(...)`;
- `validate_initial_tilt_rejection_predecision_factorization_hypothesis(...)`;
- `certify_initial_tilt_rejection_failure_aware_source_law(...)`;
- `require_matching_initial_tilt_rejection_failure_aware_source_law(...)`;
- `validate_initial_tilt_rejection_failure_aware_source_law_certificate(...)`;
- `owner.describe()`; and
- `owner.validate_specification(specification)`.

There is no caller/global RNG or source-law \(V/W\) word argument, numeric
source mass, run/initialization coordinate, retry, fallback, rollback, or
alternative-strategy argument.

## 8. Custody and validation

Hypothesis, certificate, specification, and owner are exact-type, immutable,
nonsubclassable, nonpickle, token-sealed records. The owner binds exact CP40
and transitive owner/certificate identities, both parent hypotheses, the
factorization assumption, policy/role, builders, validators, ancestry
resolver, and cached specification.

The captured local operation bindings and explicitly listed late APIs are
identity-checked, together with the listed dependency/class surfaces.
Redigested forgeries, count/digest mismatches, callback substitution, ancestry
splicing, helper/policy replacement, listed late-API replacement, and listed
dependency-surface mutation fail closed.

These are same-process procedural custody controls under a trusted unchanged
runtime, not cryptographic authentication, loaded-code integrity proof, or
cross-runtime portability.

## 9. Claim matrix

Positive scope is limited to:

- exact CP40 and transitive ancestry/hypothesis binding;
- the normalized, distinct, complete \(V/W\) coordinate partition;
- binding of the explicit unproved factorization hypothesis;
- the product-uniform independence premise;
- distinct \(F_{36}\), \(F_{37}\), exhaustion, and configuration atoms;
- symbolic fibers, exact augmented normalization, and denominator exponent;
- the \(\rho=0\), \(\rho>0\), universal augmented-TV, and positive-\(S_Q\)
  factor-one bounds;
- arbitrary-source data processing only; and
- no CP36--CP40 operational call or numeric fiber enumeration.

False or absent scope includes:

- executable proof of functional noninterference;
- every numeric fiber, failure, batch, state, exhaustion, selection, and
  conditioned-bound value;
- live Philox/source/initializer laws or randomness;
- an arbitrary-source product mixture;
- exact ideal rejection, global analytic normalization, SIR, or all-strategy
  admission;
- Formal Test 28 closure;
- tag-3 semantics, Brownian consumption, drift, path, liveness, or sampler;
- scientific, model-quality, or generality promotion; and
- portable or cryptographic custody.

## 10. Focused-test coverage

The focused matrix covers API/signature/export and claim flags; exact ancestry;
coordinate partition/count/digest binding; assumption/proof separation; four
atom classes and absent masses; independent tiny-mixture normalization and
duplicate aggregation; the all-failure \(\rho=0\) case; factor-one
conditioning; zero CP36--CP40 operational calls; alien and redigested forgery
refusal; record sealing; local/late/dependency/class-surface hostility; hostile
equality; source-AST checks for no caller/global RNG or source-law coordinate
consumption, no enumeration, and no CP36--CP40 operational calls; package
export isolation; and the optional-PyTorch boundary.

## 11. Final focused evidence and inherited CP40 evidence

Final checkpoint-41 evidence:

- source SHA-256:
  `79827f05b1a157dfaaed53146a17a7f9e006170c36bf6823510a87d338abe254`;
- focused-test SHA-256:
  `36e445057613dff7ea5d0606fa4c7924886549b57f94b58c4b3850c51678fcc3`;
- **28 collected; 28/28 passed**;
- pytest time: **759.21** seconds; and
- external wall time: **759.70** seconds.

The run was no-cache and warnings-as-errors. Static gates were clean under
Black, pyflakes, Python 3.9 byte-compilation, ASCII, and the at-most-88-column
check. The final independent source/test re-audit reports **P0=P1=P2=0**.
The final independent documentation audits also report **P0=P1=P2=0**.

The certificate field `passed` is an internal truth-matrix/contract-consistency
flag; it is not the focused test result, final audit disposition, theorem
proof, or empirical/scientific claim.

Inherited direct-parent CP40 exact-hash evidence is:

- source SHA-256:
  `1d92574611498aeed62cd16bb232ef22f95b365b689b5351219e0539e0e6b115`;
- focused-test SHA-256:
  `30b5f93413b8c5448d85a1b7f768da5b394143d363061db418f5847272c80305`;
- **45/45 passed** in **3908.56** seconds of pytest time and **3909.19**
  seconds external wall time.

That exact CP40 pair was **not freshly rerun for checkpoint forty-one**. Its
evidence is inherited by exact identity, not relabelled as a new run.
The independent read-only review complements rather than substitutes for the
executed CP41 focused test.

The CP41 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

Formal Tests 28 and 29 remain **OPEN**, Test 30 remains **PENDING**, and
`R2-HYBRID` remains **NOT RUN**. No C-row, R-slot, nonconfirmatory-evidence
row, novelty decision, scientific/model-quality result, generality statement,
or manuscript conclusion is promoted. The venue-neutral TeX manuscript
remains untouched.

## 12. Remaining dependencies

CP41 leaves separate:

1. executable proof of factorization/noninterference;
2. numeric evaluation or bounds for preparation failure, quota failure,
   successful batches, exhaustion, configurations, and selection;
3. any proved live-Philox/product-uniform approximation and live initializer
   distribution;
4. ungated exact ideal rejection or global analytic normalization;
5. SIR, remaining strategies, semantic failure/source chronology, and general
   admission;
6. semantic tag-3 payload/coordinate generation and global address guarantees;
7. Brownian consumption/coupling, drift, split steps, and a path; and
8. the complete learned/general sampler and Formal Tests 28--30.

Until then, CP41 may be cited only as **an abstract product-uniform failure-
aware source law conditional on an explicit unproved factorization hypothesis,
with symbolic failure/success fibers, exact augmented normalization, and the
stated augmented and positive-\(S_Q\) factor-one boundaries**.
