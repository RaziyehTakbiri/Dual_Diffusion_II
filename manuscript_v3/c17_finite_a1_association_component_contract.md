# C17 finite-A1 association component contract

**Status:** `PARTIAL_COMPONENT_DIAGNOSTIC_CONTRACT`  
**Scope:** `FINITE_A1_CAPPED_ASSOCIATION_PATH_COMPONENTS_ONLY`  
**Claim promotion:** `NONE`  
**R1-A1:** `NOT_RUN`  
**R2-HYBRID:** `NOT_RUN`  
**Confirmatory execution authorized:** no

## 1. Purpose

This contract freezes a component-resolved evaluator for the locally rebuilt
finite A1 compatibility fixture. The current API accepts only an explicitly
test-only certified callback used solely to exercise and falsify the
evaluator. It rejects production-bound checkpoints because frozen-runtime
production path-content bytes have not yet been materialized and pinned. A
future production evaluator requires a separate lane-aware binding; it is not
silently represented by the local compatibility hash.

The local checkpoint must not be described as a trained result, a completed
A1 run, or evidence for a manuscript claim.

The scientific purpose is narrower: given an eligible candidate potential,
separate the finite path divergence into its normalized-initializer, birth,
death, and replacement terms under the **exact target conditioned
occupation**. This closes an evaluation-interface gap without bypassing the
frozen training permit.

## 2. Frozen subject

The subject is the existing A1 fixture with:

- `20` capped three-type latent count states;
- `21` observations: all retained count observations through cardinality
  three plus one overflow outcome;
- the positive, contaminated occurrence-association likelihood;
- active birth, death, and replacement edges;
- exact finite target information from
  `FiniteAtomicAssociationBridgeOracle`; and
- the existing canonical state, observation, and time order.

All observations must be evaluated. Retained and overflow outcomes remain
distinct. The evaluator must use `fixture.oracle.transition_family` to
classify every positive aggregate generator edge; no caller-supplied family
labels or hand-selected edge subsets are accepted.

## 3. Orientation and terms

For each observation `a`, the direction is

\[
\mathrm{KL}(P^{h,a}\Vert P^{\widehat h,a}).
\]

The target conditioned law supplies both the initial law and time-dependent
occupation measure. Define

\[
e_a(t,i)=\log\widehat h_a(t,i)-\log h_a(t,i),
\qquad
\Phi(v)=e^v-1-v.
\]

The required components are

\[
K_0(a)=\mathrm{KL}(\mu_0^{h,a}\Vert
                         \mu_0^{\widehat h,a}),
\]

and, for `J` in `birth`, `death`, `replacement`,

\[
K_J(a)=
\int_0^T\sum_i\mu_t^{h,a}(i)
\sum_{j:(i,j)\in J}q^{h,a}_{ij}(t)
\Phi(e_a(t,j)-e_a(t,i))\,dt.
\tag{A1.1}
\]

There are no continuous coordinates in this finite fixture. The continuous
term must therefore be represented as
`NOT_APPLICABLE_NO_CONTINUOUS_COORDINATES`, with no numeric zero masquerading
as measured continuous evidence.

The per-observation total, when issued, is exactly

\[
K_0(a)+K_+(a)+K_-(a)+K_R(a).
\]

It must agree with a separately invoked aggregate finite-bridge path-KL
calculation within the declared primary/refined numerical tolerance.

## 4. Eligible inputs and outcomes

The only result states are:

- `COMPLETE_FINITE_KNOWN_LAW_DIAGNOSTIC`;
- `PARTIAL_COMPONENT_DIAGNOSTIC`; and
- `REFUSED`.

The current wrapper requires `production_bound=false` and `test_only=true` and
publishes `production_checkpoint_evaluation_supported=false`. A test-only
evaluator can produce only
`PARTIAL_COMPONENT_DIAGNOSTIC`. Its numbers demonstrate the evaluator's
algebra and hostile-test coverage, not training success.

For this test-only callback, every exact time-vector request made by the
wrapper is evaluated twice immediately and compared byte for byte. The
wrapper also retains a SHA-256 digest for each exact requested time vector and
rejects a changed result on reuse. The complete 33-point fixture grid and the
singleton times `0`, `0.5`, and `1` are probed before and after all 21
observations. This is bounded same-call determinism checking only: it does not
establish provenance, determinism at unrequested inputs, or reproducibility
across processes or runtimes.

No total may be issued unless all of the following hold for the evaluated
branch:

- exact target information and target occupation are available;
- the candidate potential is positive and finite;
- the exact terminal boundary is shared;
- target and candidate have common support on every target-occupied edge;
- every positive aggregate generator edge is classified exactly once;
- birth, death, and replacement are all present;
- the normalized initializer uses the target-first KL orientation;
- all three family integrals and their refinement comparisons succeed; and
- the separately invoked pre-existing aggregate path calculation, with its
  independently propagated target occupancy but shared low-level numerical
  primitives, agrees within tolerance.

Failure is atomic: no partial record survives an exception.

## 5. Per-term record

Every component record must state:

- component identity and applicability;
- target measure (`EXACT_CONDITIONED_TARGET_INITIAL_LAW` for `K0`,
  `EXACT_CONDITIONED_TARGET_OCCUPATION` for jump terms, and explicit
  nonapplicability for `KC`);
- integration method and primary/refined settings;
- value, primary/refined difference, and numerical error estimate;
- whether the number is interval certified (`false` here);
- active aggregate edge count; and
- whether it entered the issued total.

The aggregate record must bind the fixture, evaluator certification, canonical
observation order, solver settings, per-observation records, and any
production identities. If a future artifact serializes this record, elapsed
timing is descriptive and must be excluded from that artifact's scientific
digest; the present in-memory record does not claim a result-level digest.

## 6. Required hostile checks

The focused suite must cover:

1. forward/reverse KL orientation and initializer-normalizer sign;
2. exact-potential zero error and constant-gauge invariance;
3. terminal mismatch rejection;
4. target-occupation versus candidate-occupation substitution;
5. omission, duplication, or swapping of an edit family;
6. incomplete or illegal arbitrary state-pair edges;
7. canonical state and observation reordering;
8. retained/overflow and clean/contaminated observation-law confusion;
9. fixture, feature, parameter, classifier, campaign, or receipt mismatch;
10. cap-outward edge invention and cap-defect insertion as an extra term;
11. value/envelope or average-NCE quantities substituted for `e`;
12. NaN, infinity, boolean, malformed arrays, resource failure, and
    quadrature disagreement; and
13. mutation, cache reuse across incompatible subjects, or partial issuance
    after failure.

## 7. Numerical boundary

The path identity and family partition are mathematical statements on this
finite subject. Matrix exponentials, adaptive ODE solves, and quadrature are
ordinary floating-point computations. Primary/refined agreement is a
diagnostic, not an interval proof. Consequently:

- `interval_certified=false`;
- `simultaneous_coverage_proved=false`;
- `rigorous_numerical_enclosure_present=false`; and
- numerical agreement cannot promote C17 or R1/R2.

## 8. Scientific boundary

Even a future genuine learned checkpoint evaluated under a separately frozen
production lane would establish only a finite known-law association
diagnostic. This contract does not supply:

- continuous-coordinate gradient energy;
- occurrence-attached heterogeneous mark fibers;
- dimension-changing replacement RN/Jacobian integration;
- a general exact mixed conditional `r*` or target occupation;
- a coercivity theorem from NCE risk to hybrid error;
- a clean-room or independent confirmatory learner run;
- real-domain evidence; or
- manuscript claim promotion.

At the present local checkpoint, no legitimate fitted result artifact exists,
so learned-result fields must remain absent and the outcome must remain
`PARTIAL_COMPONENT_DIAGNOSTIC`. The next transition requires both a separately
authorized frozen training run and frozen-runtime production path-content
custody in a new lane-aware binding; this evaluator must not manufacture or
bypass either prerequisite.
