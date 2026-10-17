# Hybrid diffusion: claim ledger, proofs and focused theory plan

Date: 2026-09-13  
Scope: scientific claims for the [current mixed-configuration model](hybrid_diffusion_scientific_core_v1.md).

This is a working mathematical appendix and research plan. "Derived here" means
an argument is supplied under the listed assumptions; it is not shorthand for
novelty, peer review or successful training. Software tests corroborate specific
implementations but do not prove these statements.

## 1. Publication claims and honest status

| ID | Potential paper statement | Current status and required evidence |
|---|---|---|
| S1 | The mixed reference, target lift and observation kernel are normalized and preserve occurrence semantics. | Derived in the Sept. 8 amendment and summarized/proved below. Current scalar-fiber/domain scope only. |
| S2 | The capped birth/death-OU reference is reversible and its reference jump part is nonexplosive. | Derived below for the stated generator/domain; no mixing-time or learned-process claim. |
| S3 | The BASE objective has a nonnegative score/jump discrepancy as its population excess. | Detailed derivation below under explicit integrability and reversibility. Not a learning-rate/generalization/path theorem. |
| S4 | Joint/product logistic training identifies a likelihood ratio in the unrestricted class. | Derived below for the actual paired law. Current bounded/gated head is a restricted class, and the numerical time-law issue matters. |
| S5 | The analytic association guide and cap-conditioned reference posterior are exact for their stated ideal reference laws. | Complete independently reviewed [proof appendix](hybrid_diffusion_association_initializer_proof_v1.md), including multiplicities, total-count conditioning, overflow and cap-defect bound. Not exact for learned BASE or the capped propagated guide. |
| S6 | Smoothing/contamination introduce a bounded unconditional raw-F105 target shift. | Derived below for the finite training law and declared scalar chart. Conditional and numerical materialization errors remain separate. |
| S7 | G+R improves error or efficiency over DIR because it represents association structure analytically. | General hypothesis still open. The [first finite mechanism benchmark](../docs/FINITE_CONDITIONAL_BENCHMARK.md) has lower final G+R TV than DIR in 12/12 declared toy cases, but guide-only beats trained G+R in 2/12. No full-neural/general superiority or novelty inference. |
| S8 | The implementation is reusable outside the original two domains. | Interface/reproduction deliverable in progress; current exact typed adapters remain domain-specific. |
| S9 | Trained conditional paths converge to the desired raw-data posterior with an end-to-end KL/TV guarantee. | **Not claimed.** This is neither proved nor implied by the local results. |

The old C17 status remains
[C17 retired; no theorem or result claim](c17_retirement_no_claim_successor_v1.md).
No entry above changes that disposition. A useful theory section can consist of
specific structural/objective results and clearly isolated approximation
questions; it does not need an unproved headline path theorem.

The [conditional-law contract v2](hybrid_diffusion_conditional_law_contract_v2.md)
now selects and proves a common-grid, linearly gated finite benchmark contract,
including exact conditioning and a harmonic-defect approximation bound. The
query-refined/cubic-gated default described below is retained. An explicit
[mixed successor v3](hybrid_diffusion_mixed_conditional_contract_v3.md) now uses
one common grid and a linear gate in the actual neural learner. Its
[continuous-fiber benchmark](../docs/MIXED_CONTINUOUS_CONDITIONAL_BENCHMARK.md)
tests the real sampler against an independent target with exact-h and learned
controls. S9, global approximation control and a superiority claim remain open.
Neither result is a revival of C17.

## 2. Assumption-to-claim map

| Assumption | Used by | What the implementation cannot establish by itself |
|---|---|---|
| A1. Fixed context; countable legal key set; positive normalized rho; exact duplicate semantics; finite scientific cap N. | S1, S2, S5 | Clinical/business support validity, a TRAIN/no-leakage declaration or arbitrary-domain support. |
| A2. Scalar Euclidean fibers with Gaussian reference; generator acts on symmetric sufficiently regular functions with the required integration-by-parts domain. | S2, S3 | Global regularity from a handful of autograd checks; validity of a different chart with boundaries. |
| A3. Nonnegative measurable clocks with finite integrals; beta=theta delta, delta>0; births disabled at N. | S2 | Uniform rapid mixing, or nonexplosion of every unrestricted learned tilt. |
| A4. Finite TRAIN roster in Gamma_N, finite chart coordinates, normalized source weights; 0<alpha,tau<1; positive finite reference masses on source keys. | S1, S6 | Population consistency, optimal regularization or an empirically appropriate target shift. |
| A5. sigma>0, 0<epsilon<1, p=1/2, finite M; whole-observation mixture and declared overflow law. | S1, S4, S5 | Equivalence to exact noiseless observations, favorable evidence bounds for all possible keys. |
| A6. A positive density f and candidate V have finite objective terms; Gaussian integration by parts has no boundary remainder; jump terms permit change of variables/integration. | S3 | Automatic validity uniformly in forward time, cap, key or learned parameter. Those require additional analysis. |
| A7. Positive paired densities on the same support; genuinely independent whole trajectories at fixed context/time; precise time and numerical-path law. | S4 | Independence from deterministic replay alone or equality of two differently refined numerical grids. |
| A8. The function class contains the required log-ratio, including time normalizer and gated residual; optimization reaches its population infimum. | Exact classifier recovery only | A bounded encoder/head, short AdamW runs or finite synthetic checks do not prove either condition. |

Only the claims in the "Used by" column inherit an assumption. For example,
positive g does not imply the neural class contains log h, and a score-matching
identity does not imply a bound on a trained sampler's distribution.

## 3. Proposition 1: normalized reference and detailed balance

**Statement.** Under A1–A3, Pi_N from the scientific core is a normalized
probability measure. The reference generator (1) is symmetric with respect to
Pi_N on its stated test-function domain. The reference jump part has only
finitely many jumps almost surely on a finite horizon.

**Proof.** Each pushforward (S_n)_#nu^tensor n is a probability measure and
sum_n p_N(n)=1, so normalization follows. Write x for an (n-1)-occurrence
configuration and e for a further occurrence. The elementary identity

\[
n\,p_N(n)=\theta\,p_N(n-1),\qquad 1\le n\le N
\]

turns an integral summing one removed occurrence under Pi_N into theta times
the integral adding a nu-distributed occurrence under Pi_N restricted to
count<N. Hence the edge measure of a birth at rate beta equals that of its
reverse occurrence-death at rate delta, since beta=theta delta. This argument
uses labeled product variables before the quotient, so repeated occurrences
are counted correctly; it does not require the event law to be atomless.

On each fixed key tuple the Gaussian identity

\[
\int F\left(-\tfrac12r\partial_rG+\tfrac12\partial_r^2G\right)d\phi_1
=-\tfrac12\int(\partial_rF)(\partial_rG)d\phi_1
\]

is symmetric. Integrate over keys and remaining occurrences, then sum over
finite n and the continuous fibers. The required interchanges are justified by
the test-function integrability in A2. Each component shares Pi_N, so adding
their nonnegative time weights preserves symmetry and invariance.

The total reference jump rate is at most
gamma_J(s)(beta+delta N). Its finite time integral dominates the number of
jumps by an inhomogeneous Poisson count. Therefore the jump part is nonexplosive.
No spectral-gap, equilibration-rate or arbitrary learned-tilt conclusion is used.
QED.

**Implementation correspondence.** Reference corruption draws an actual capped
birth/death trajectory and OU transition, not a convenient replacement kernel.
Finite arithmetic/RNG and refusal limits are distinct from the ideal-law proof.

## 4. Proposition 2: the regularized target is dominated

**Statement.** Under A1, A4 and the scalar Gaussian chart, Q0 has a density
f0 relative to Pi_N with alpha<=f0<=C<infinity. Its first and second
within-fiber derivatives are bounded for the fixed finite training roster;
log f0 inherits bounded first/second fiber derivatives.

**Proof.** A source key indicator has density 1/rho(d_source) on its key.
For a continuous source coordinate mu,

\[
\sup_r\frac{\phi_\tau(r-\mu)}{\phi_1(r)}
=\tau^{-1}\exp\left(\frac{\mu^2}{2(1-\tau^2)}\right)<\infty.
\]

Its first two derivatives are polynomials in r times a Gaussian-decaying
function, hence bounded when 0<tau<1. Atomic fibers have no derivatives.
For each finite source, equation (3) is a finite sum of products of these
terms with the exact quotient prefactor. It is zero on other key/count
components. A finite weighted sum of source components is therefore bounded
with bounded first/second fiber derivatives. Adding alpha Pi_N yields

\[
f_0=\alpha+(1-\alpha)\sum_lw_l\,dL_l^\tau/d\Pi_N\ge\alpha.
\]

Then partial log f0=(partial f0)/f0 and
partial^2 log f0=(partial^2 f0)/f0-(partial f0)^2/f0^2 give the derivative
bounds. QED.

The reversible Markov semigroup preserves the scalar lower/upper density bounds.
It does not follow from that observation alone that all derivatives of f_s are
uniformly bounded in time; a derivative/domain argument is required. Constants
can deteriorate as alpha,tau approach zero or reference masses become tiny.

The observation counterpart is simpler: each channel (4) integrates to one
against eta, half-thinning defines a normalized occurrence law, and C_M is a
measurable collapse. Thus K_clean and lambda are probability kernels and
g_epsilon=(1-epsilon)g_clean+epsilon>=epsilon. Normalization must not be changed
by clipping likelihood values, dropping rare keys or renormalizing a failed draw.

## 5. Proposition 3: exact BASE population excess identity

This is a useful correctness theorem for the selected training objective, not
a claim that score matching itself is new.

Fix one active time and context. Let f=dQ/dPi_N>0, V*=log f and w=V-V*.
Let q0 be the reversible birth/death edge kernel. Assume A6, including the
integrability needed for every expression below. Put

\[
B_{\exp}(t)=e^t-1-t\ge0.
\]

**Statement.** The population objective (8) satisfies, time by time,

\[
\begin{aligned}
\mathcal L_{\rm BASE}(V)-\mathcal L_{\rm BASE}(V^*)
={}&\tfrac12\gamma_C\int f(x)\sum_{i:k(d_i)=1}
|\partial_iw(x)|^2\,\Pi_N(dx)\\
&+\lambda_J\gamma_J\int\Pi_N(dx)q_0(x,dy)\,
f(y)\,B_{\exp}(w(y)-w(x)).
\end{aligned}
\tag{14}
\]

The same identity can be integrated over the declared training time law
when the terms are integrable. Both discrepancies are nonnegative.

**Continuous proof.** Gaussian integration by parts gives

\[
\int f(\partial_i^2V-r_i\partial_iV)\,d\Pi_N
=-\int f\,(\partial_i\log f)(\partial_iV)\,d\Pi_N.
\]

Complete the square in
one-half |partial_i V|^2-(partial_i log f)(partial_i V), subtract its value
at V*, and sum over active fibers. This yields the first line of (14).
No derivative is taken through a discrete key or an atomic fiber.

**Jump proof.** Write Delta w=w(y)-w(x). Reversibility says that
Pi_N(dx)q0(x,dy) is a symmetric edge measure. The loss difference is

\[
\begin{aligned}
J(V)-J(V^*)
&=\int\Pi_N(dx)q_0(x,dy)
 \left[f(y)(e^{\Delta w}-1)+f(x)\Delta w\right]\\
&=\int\Pi_N(dx)q_0(x,dy)f(y)B_{\exp}(\Delta w).
\end{aligned}
\]

For the second equality, the leftover linear term is
integral (f(y)+f(x))Delta w d(edge measure), which is zero by exchanging x,y.
This is why the positive linear term in (8) is essential. Multiply by the
process clock and the declared lambda_J. QED.

**What equality does and does not identify.** Equality forces zero score
discrepancy where gamma_C f>0 and zero edit difference where gamma_J f(y)>0.
A further connectivity/irreducibility argument on the relevant support can
reduce the remaining ambiguity to an additive time/context constant. On a
zero-clock hold, (14) provides no identifiability. No finite-dimensional neural
realizability, stochastic optimization rate, generalization bound or conditional
path error follows from this identity.

## 6. Proposition 4: the paired law and the exact logistic statement

At a fixed u,z let mu_u be the latent marginal of the **chosen** base
simulation law. Let h_u(x,a) be its conditional observation density and
m_u(a)=integral h_u(x,a)mu_u(dx). Define

\[
P_u(dx,da)=\mu_u(dx)h_u(x,a)\lambda(da),\qquad
Q_u(dx,da)=\mu_u(dx)m_u(a)\lambda(da).
\]

These are the joint and independent-product class laws. Where both densities
are positive, let M_u=(P_u+Q_u)/2 and
eta_u=dP_u/d(P_u+Q_u). Sigma(t)=1/(1+e^{-t}) denotes the sigmoid.

**Statement.** Over unrestricted measurable logits with defined risk,

\[
\ell_u^*=\log\frac{dP_u}{dQ_u}=\log h_u-\log m_u,
\qquad
\mathcal R_u(\ell)-\mathcal R_u(\ell_u^*)
=\mathbb E_{M_u}
{\rm KL}\bigl({\rm Ber}(\eta_u)\,\|\,{\rm Ber}(\sigma(\ell))\bigr).
\tag{15}
\]

**Proof.** Under M_u the balanced class label has conditional positive
probability eta_u. Equation (11) is its conditional Bernoulli cross-entropy.
Pointwise minimization selects predicted probability eta_u and log-odds
log(dP_u/dQ_u). Subtracting Bernoulli entropy gives (15). QED.
Integrating (15) over a declared time law gives the corresponding mixture-risk
identity.

For a single common path law, m_u=m does not depend on u. With the current
query-refined grid family, that equality need not hold. The scientifically
precise present statement is:

> The current model is optimized against a well-defined mixture of numerical
> joint/product risks. Its class infimum is the best logistic risk attainable
> within the bounded, gated architecture under that mixture law. Actual finite
> AdamW iterates need not reach that infimum. Neither the infimum nor a small
> observed training loss implies exact recovery of the unrestricted Bayes
> logit, a common backward-harmonic likelihood or the raw-data posterior.

This describes a coherent diagnostic without an unearned theorem. The nuisance
receives only a,z, while the current numerical Bayes normalizer can depend on u.
The residual may absorb a state-independent time offset where its gate and bound
permit, so the observation-only nuisance is not by itself a proof that the
whole class cannot represent the Bayes logit. Conversely, no such bounded/gated
decomposition is established. Nuisance and residual components are not
individually identified by risk alone. A finite-width encoder and cubic gate
add further approximation restrictions.

**Concrete alternatives for the next design decision.**

- A common fixed trajectory grid with training times drawn from its interior
  points makes the terminal numerical evidence common, and is easy to audit.
  It changes the full-continuous-time objective to a declared discrete-time one;
  interpolation between training times then needs its own analysis.
- A time-aware nuisance can represent -log m_u(a) for the query-refined family
  without putting that state-independent nuisance into drift/rates. It changes
  the architecture and still does not turn the family into one common Markov
  semigroup or establish an exact conditional sampler.
- A single continuous-time path-law approximation with a coherent query
  mechanism would retain the original ideal statement most closely, but
  requires a justified simulator/query construction.

No option is silently selected or implemented by this document. The first
reader demonstration may report its empirical numerical risk while this
scientific choice is made; it must not claim Bayes realizability.

## 7. A limitation lemma: classifier accuracy alone is not drift accuracy

**Statement.** Vanishing balanced logistic excess does not, by itself, force
vanishing squared coordinate-gradient error even for smooth bounded logits.

**Proof by example.** Let the joint and product laws coincide, with one
coordinate X~N(0,1) and an observation independent of X. The Bayes logit is
zero. Choose ell_k(x)=sin(kx)/k. For balanced classes,

\[
\mathcal R(\ell_k)-\mathcal R(0)
=\mathbb E\log\cosh(\ell_k(X)/2)\le\frac{1}{8k^2}\longrightarrow0.
\]

But

\[
\mathbb E|\partial_x\ell_k(X)|^2
=\mathbb E\cos^2(kX)=\tfrac12(1+e^{-2k^2})\longrightarrow\tfrac12.
\]

Each ell_k is smooth and bounded. Thus logistic consistency alone is not
score consistency. QED.

The example has no uniform second-derivative bound as k increases. A
quantitative theorem with additional uniform regularity, support geometry and
coercivity assumptions may rule it out, but those assumptions and their
constants must actually be proved/checked. This elementary warning is not
advertised as a new impossibility result or a substitute for the retired C17.
It explains why numerical classifier loss cannot stand in for gradient/path
validation or a theorem.

## 8. Proposition 5: limited target-shift bounds

For the accepted F105 scalar chart, changing a continuous log magnitude by t
changes the corresponding bounded numeric coordinate by at most |t|/4.
The event Gaussian feature map is 1/ell_E-Lipschitz and the outer Gaussian
feature map is 1/ell_G-Lipschitz. Its event mean uses 1/n, not the trainable
encoder's 1/(1+n).

Let b be the metric event-channel scale, n_c the number of continuous events
and Psi the normalized configuration feature map. Couple each raw training
configuration with its lifted version, retaining count and discrete keys.
The triangle inequality, the feature Lipschitz bounds and
E|tau Z|=tau sqrt(2/pi) give

\[
{\rm MMD}_{F105}(P_{\rm TRAIN},Q_{\rm lift})
\le\frac{b\tau\sqrt{2/\pi}}{4\ell_E\ell_G}
\mathbb E[\mathbf1_{\{n>0\}}n_c/n]
\le\frac{b\tau\sqrt{2/\pi}}{4\ell_E\ell_G}.
\tag{16}
\]

The count feature agrees under this coupling. A normalized nonnegative
Gaussian outer kernel has embedding diameter at most sqrt(2). By linearity of
mean embeddings and the triangle inequality,

\[
{\rm MMD}_{F105}(P_{\rm TRAIN},Q_0)
\le(1-\alpha)\frac{b\tau\sqrt{2/\pi}}{4\ell_E\ell_G}
+\alpha\sqrt2.
\tag{17}
\]

The accepted F105 instance sets b=ell_E=ell_G=1.
This proof concerns a finite training probability law and the ideal real-valued
chart, not unknown-population consistency or finite-precision materialization.

For conditional claims, fix a and let epsilon<=g(a|.)<=B(a).
For any coupling (X,Y) of two candidate target laws P,Q, write z_P=E_P g.
Subtract the two normalized feature-weighted expectations and use
||Psi||<=1. The numerator difference contributes
B(a) E||Psi(X)-Psi(Y)||+E|g(X)-g(Y)|; the normalization difference contributes
at most another E|g(X)-g(Y)|. Hence

\[
\left\|\mathbb E_P[\Psi(X)\mid a]-\mathbb E_Q[\Psi(Y)\mid a]\right\|
\le
\frac{B(a)\mathbb E\|\Psi(X)-\Psi(Y)\|+
2\mathbb E|g(X)-g(Y)|}{z_P},
\quad z_P\ge\epsilon.
\tag{18}
\]

A small unconditional MMD alone does not bound the likelihood-sensitivity term.
Any usable conditional bound must evaluate that term and the evidence scale
for the declared observation regime. Low evidence can amplify target shift.

## 9. Focused theorem programme: useful next work

The following are mathematical tasks with concrete deliverables, not new
platform setup requirements.

### T1. Finish the guide and posterior-initializer appendix

Supply a complete occurrence-level derivation of the partial-matching
polynomial and the retained/overflow cap-conditioned initializer. Show
normalization, duplicate factors and zero-clock reduction in one proof.
The Sept. 8 derivation supplies much of the argument, but its mathematical
notation and current implementation extensions need a final independent review.

**Useful deliverable:** a correct reference-computation theorem, with explicit
distinction between uncapped propagated guide and capped prior conditioning.
Do not state that cap correction makes h_tilde the capped semigroup.

### T2. Separate and quantify the guide's cap approximation

Couple capped and uncapped reference processes until an attempted birth at
the cap. For bounded fixed-observation likelihood g, a basic starting bound is

\[
|\mathbb E g(X_S^{\rm cap})-\mathbb E g(X_S^{\infty})|
\le 2\|g\|_\infty\Pr\{\text{coupling separates before }S\}.
\]

This display is a proof direction, not a completed sharp theorem: define the
coupling with shared OU and occurrence bookkeeping, specify count-dependent
events and derive a useful count-tail bound. Positivity can convert a valid
likelihood bound into a log-guide bound, but constants depending on a may
make it vacuous. Determine useful and nonuseful regimes honestly.

**Useful deliverable:** an interpretable bound or negative example showing when
the analytic guide is accurate enough to be a helpful baseline.

### T3. Make conditional class approximation explicit

Resolve the numerical time/evidence choice in Section 6. Determine whether the
cubic gate's required residual decay is justified for the selected clock
schedule; if not, compare a scientifically justified gate family or keep an
explicit approximation term. State which errors depend on BASE approximation,
guide mismatch, restricted head, optimization, discretization and target shift.

**Useful deliverable:** a code-matched conditional objective proposition and
a transparent error decomposition. It need not imply end-to-end path KL.

### T4. Test the proposed advantage before pursuing a broad guarantee

On a known-law problem, compare G+R and DIR learning curves and held-out
conditional errors under the same target/noise/task and a fully counted budget.
Vary association ambiguity, rare-key overlap and cap pressure; include guide-only
and residual ablations when they isolate the hypothesized mechanism.

**Useful deliverable:** evidence about whether association structure improves
the approximation/optimization tradeoff. This cannot be replaced by a passing
software test or assumed from the analytic formula.

Only after T1–T4 support a coherent method should a new broad path-law theorem be
considered. Such a theorem would need explicit reference/learned generator
domains, integrability, absolute continuity, initial-law error, model
approximation and discretization control. No such theorem is promised here.

## 10. Progress checklist for this scientific work package

- [x] Consolidate the current mixed-configuration model and equations.
- [x] Map the equations to the actual BASE/conditional/sampler implementation.
- [x] Separate raw target, smoothed target, reference law, learned BASE and numerical laws.
- [x] Supply the structural/BASE/logistic/limited-target-shift derivations above.
- [x] Record the actual conditional time-law and gate representability gaps.
- [ ] Finish independent proof review and final theorem selection for the paper.
- [ ] Complete the occurrence-level guide/initializer appendix (T1).
- [ ] Establish a useful cap-error result or limitation example (T2).
- [ ] Select and test a coherent conditional time/head contract (T3).
- [ ] Produce scientific comparison outcomes and mechanism ablations (T4).
- [ ] Establish the final novelty claim against the closest literature.
- [ ] Complete public end-to-end paper reproduction and report actual resources.

These checkboxes track this new scientific work package only. They do not
silently renumber the historical timetable, close old compound obligations or
turn archived software milestones into scientific results.
