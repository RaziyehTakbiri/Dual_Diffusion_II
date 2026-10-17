# Conditional Gaussian variance reduction for the unchanged local learner

2026-09-13. Prospective, local-CPU mathematical formulation. This document
changes the forward label estimator, not the numerical target, spline family,
offsets, penalties, coefficient box, fitting algorithm, acceptance tolerances,
or archived outcomes. No scientific fit is executed by this derivation.

## 1. Scope, notation and the question

Use the cap-one, zero-BASE projected states E, O and C(z), the two already fixed
synthetic scenarios, and the existing macro grid u_i=i/8 through H=1. At a
fixed active node and initial state x, let K_i be the original numerical
transition: additive-noise Heun half-step, the entire capped birth/death
uniformization phase with marks frozen, and another Heun half-step. The target
remains

\[
h_i^\Delta(x)=(K_i\cdots K_7g_y)(x),\qquad
T_i(x)=\log h_i^\Delta(x).                                      \tag{1}
\]

There is no replacement by a continuous-time OU likelihood, backward oracle
label, or learned conditional endpoint sampler. The independent backward
numerical likelihood and its derivatives remain evaluation-only quantities.

Write phi_v(w) for the centered Gaussian density of variance v>0, and put

\[
c=\epsilon e^{-1}\rho\phi_1(y)>0,\quad
\beta=(1-\epsilon)/2,\quad
M=c+\frac{\beta}{\sigma\sqrt{2\pi}}.
\]

The known terminal observation channel is

\[
g_y(E)=g_y(O)=c,\qquad
g_y(C(z))=c+\beta\phi_{\sigma^2}(y-z).                         \tag{2}
\]

The original raw label is Y=g_y(X_H). Both Y and its conditional expectations
are in [c,M]. The question is whether integrating the Gaussian coordinate
randomness, while retaining the same stochastic jump skeletons, reduces
finite-label variability enough to improve the unchanged fitted likelihood
and derivatives at the fixed work roster. An improvement in fitted outputs is
an empirical question; the variance and stability results below distinguish
it from what is proved in advance.

Conditioning for Monte Carlo variance reduction is classical, not a new
statistical method. The use of “Rao--Blackwell” here refers to conditional
Monte Carlo, without a claim of statistical sufficiency or novelty. See
[Owen, Monte Carlo theory, methods and examples, Chapter 8, Section 8.7](https://artowen.su.domains/mc/Ch-var-basic.pdf)
for the general conditioning principle. The model-specific conditional law,
variance formula and learner bounds needed here are derived below.

## 2. What is conditioned on

For one forward suffix, define J to contain every macro interval's
uniformization proposal count, accepted or rejected transition decisions,
and selected/other category of every accepted birth. It identifies the
category path and all deaths and selected-key reset births. It does not
contain any birth Gaussian mark or Gaussian Heun increment. The initial
state and its given coordinate x are held fixed.

In this zero-BASE model, the birth/death rates and selected-key probabilities
are independent of coordinates. Consequently J is independent of these
Gaussian variables conditional on x. This is the essential structural
assumption. It does not automatically hold for a learned coordinate-dependent
birth/death intensity or acceptance probability.

It is sufficient to store a compressed summary of J that preserves the final
category and the affine Gaussian ancestry described below. The final category
alone is generally insufficient: a surviving initial C(z) and a later C birth
have different conditional means and variances. Conditional integration must
not silently replace one with the other.

The uniformization rate is lambda=delta*max(theta,1). Conditional on its
Poisson proposal count, the category chain is the same original jump phase.
Proposal times are unnecessary because marks are frozen during that phase
and the transition probabilities are constant. Multiple births and deaths
within one macro interval must be retained; this is not a one-jump
approximation.

## 3. Conditional Gaussian propagation

For a Heun half-duration d with continuous rate gamma, define

\[
A_d=1-\gamma d/2+(\gamma d)^2/8,\qquad
V_d=\gamma d(1-\gamma d/4)^2.                                  \tag{3}
\]

The original numerical coordinate update is
z'=A_d z+sqrt(V_d) Z, with independent Z~N(0,1). In each macro interval
d=(u_{j+1}-u_j)/2. These are the numerical Heun coefficients, not the exact
OU semigroup coefficients exp(-gamma*d/2) and 1-exp(-gamma*d).

Maintain a pair (m,v) only while the category is C:

1. An initial C(z) has (m,v)=(z,0).
2. A Heun half-step sends (m,v) to (A_d m,A_d^2 v+V_d).
3. A death erases the continuous coordinate. An O birth has no relevant
   selected-key coordinate.
4. A C birth resets (m,v)=(0,1), because its mark is an independent N(0,1).
5. There is no coordinate evolution during the middle jump phase. In
   particular, a C birth in that phase receives the final half-step only,
   not an additional duration measured from a fabricated birth time.

**Proposition 1 (conditional terminal coordinate).** In ideal real arithmetic,
if the final category is C then

\[
Z_H\mid x,J\sim N(m_J,v_J),                                    \tag{4}
\]

where (m_J,v_J) is obtained by the above recursion. A zero variance denotes a
point mass. Conditional on x,J, different suffixes use independent Gaussian
variables under the declared independent simulation streams.

**Proof.** The initial coordinate is a deterministic Gaussian with variance
zero. An affine transformation plus an independent Gaussian increment
preserves Gaussianity with the stated first two moments. A selected birth
replaces all previous coordinate ancestry by an independent standard Gaussian.
A death deletes it. Induction through every half-step and jump proposal gives
(4), including suffixes with repeated births and deaths. Coordinate-independent
jump decisions are needed to preserve the Gaussian conditional law when
conditioning on J. \(\square\)

No Gaussian coordinate samples are needed to evaluate this recursion. A
paired raw/Rao--Blackwell comparison may still generate them in order to
produce both labels on exactly the same realized jump skeleton.

## 4. Unbiased label and exact removed conditional variance

Define

\[
Y_{\rm RB}(x,J)=
\begin{cases}
c,&\text{terminal category E or O},\\
c+\beta\phi_{\sigma^2+v_J}(y-m_J),&\text{terminal category C}.
\end{cases}                                                    \tag{5}
\]

**Proposition 2 (same numerical target).** Y_RB=E[Y|x,J], hence

\[
\mathbb E[Y_{\rm RB}\mid x]=\mathbb E[Y\mid x]=h_i^\Delta(x).
                                                                  \tag{6}
\]

**Proof.** For terminal E/O the label is constant. For terminal C, convolution
of N(m_J,v_J) with the Gaussian channel in (2) gives
E[phi_(sigma^2)(y-Z_H)|x,J]=phi_(sigma^2+v_J)(y-m_J). This follows directly
by completing the square in the Gaussian integral, and also holds at v_J=0
by evaluation at the deterministic coordinate. Taking a second conditional
expectation proves (6). \(\square\)

This calculation integrates a known observation channel conditional on a
simulated forward jump skeleton. It does not evaluate the unconditional
backward likelihood, backward score, evidence integral or a matrix exponential
to obtain the training label.

The removed conditional variance W(x,J)=Var(Y|x,J) is zero for final E/O, and
for final C equals

\[
W(x,J)=\beta^2\left[
\frac{\phi_{v_J+\sigma^2/2}(y-m_J)}{2\sqrt\pi\,\sigma}
-\phi_{v_J+\sigma^2}(y-m_J)^2\right].                          \tag{7}
\]

To prove (7), use
phi_(sigma^2)(w)^2=phi_(sigma^2/2)(w)/(2*sqrt(pi)*sigma), then integrate as
in Proposition 2 and subtract the square of the conditional mean. The
contamination constant disappears from the variance. The expression is
nonnegative in real arithmetic. Any floating-point negative cancellation
needs explicit numerical handling and disclosure; a mathematical variance
must not be replaced by an unexplained negative estimate.

The total-variance decomposition gives the exact identity

\[
\operatorname{Var}(Y\mid x)-\operatorname{Var}(Y_{\rm RB}\mid x)
=\mathbb E[W(x,J)\mid x]\ge0.                                  \tag{8}
\]

The inequality is strict if a final C with v_J>0 has positive probability,
since the Gaussian observation density is then not almost surely constant.
It can be equality, for example when every terminal state is atomic, or when
the relevant continuous coordinate is deterministic and receives no random
birth or increment. Removing coordinate noise does not remove jump-skeleton
randomness or continuous-design randomness.

## 5. Fixed-design gradient covariance

Fix a node, method, budget n and the complete design X=(x_1,...,x_n). Let
Phi_j in R^p, p=35, be its unchanged feature rows; b_j is the unchanged
method offset. Write a for physical coefficients in the common box
C_A=[-A,A]^p, A=2*log(M/c). The objective is exactly

\[
J_Y(a)=\frac1{nM}\sum_j
\{e^{b_j+\Phi_j^\top a}-Y_j(b_j+\Phi_j^\top a)\}
+\frac12a^\top\Lambda a,
\quad\Lambda=10^{-4}R+10^{-6}I.                                \tag{9}
\]

Set h_j=h_i^Delta(x_j), and let J_h denote (9) with labels h_j. Neither h_j
nor J_h is supplied to the forward-label training routine. Define

\[
v_Y=\frac1{nM}\sum_j\Phi_j(Y_j-h_j).
\]

The objectives obey J_Y(a)=J_h(a)-v_Y^T a plus an a-independent constant.
Their Hessians as functions of a are identical. Under conditional independence
of suffixes,

\[
\mathbb E[v_Y\mid X]=0,\qquad
\Sigma_Y(X):=\operatorname{Cov}(v_Y\mid X)
=\frac1{n^2M^2}\sum_j\operatorname{Var}(Y_j\mid x_j)\Phi_j\Phi_j^\top.
                                                                  \tag{10}
\]

Combining (8) with (10) proves a positive-semidefinite covariance reduction:

\[
\Sigma_{\rm raw}(X)-\Sigma_{\rm RB}(X)
=D(X):=\frac1{n^2M^2}\sum_j
\mathbb E[W(x_j,J_j)\mid x_j]\Phi_j\Phi_j^\top\succeq0.          \tag{11}
\]

There is no fixed-design gradient bias introduced by RB. The common method
offset contributes no random term to (10). With shared features and labels,
the removed covariance (11) is the same for G+R and DIR; their fitted
responses may differ because their offset-dependent curvature differs.

For the actually realized paired skeletons, the computable matrix

\[
\widehat D(X,J)=\frac1{n^2M^2}\sum_j
W(x_j,J_j)\Phi_j\Phi_j^\top                                   \tag{12}
\]

has two precise interpretations. It is an unbiased estimator of D(X) over
the skeleton draws, and it is the **exact conditional covariance**, in ideal
arithmetic, of
v_pair=(nM)^(-1)*sum_j Phi_j*(Y_raw,j-Y_RB,j) given X,J. Formula (12) is not
the full remaining RB covariance. A single raw sample per distinct x_j does
not directly estimate Var(Y_j|x_j) by a within-state sample variance; pooled
label variances also contain between-design variation and must be named
accordingly.

## 6. Global stability and derivative-error bounds

Let a_Y and a_h be the ideal constrained minimizers of J_Y and J_h. They are
unique because (9) is globally mu-strongly convex on the box, with

\[
\mu=10^{-6}                                                     \tag{13}
\]

as a guaranteed real-arithmetic choice from the unchanged ridge penalty and
R positive semidefinite. No empirical Hessian eigenvalue is needed for (13).
A stronger valid global lower bound may be derived from the fixed box and
feature Gram matrix, but must be distinguished from the Hessian at one fit.

**Proposition 3 (fixed-design coefficient stability).**

\[
\|a_Y-a_h\|_2\le\|v_Y\|_2/\mu.                               \tag{14}
\]

**Proof.** With d=a_Y-a_h, constrained first-order optimality yields
(grad J_h(a_Y)-v_Y)^T d<=0 and grad J_h(a_h)^T d>=0. Subtracting and using
strong convexity gives mu*||d||^2<=v_Y^T d<=||v_Y||*||d||. The zero-difference
case is immediate; otherwise divide by ||d||. \(\square\)

For k=0,1,2, let L_k be a deterministic readback matrix whose rows are
sqrt(w_l)*partial_z^k Phi(x_l)^T, with w_l>=0, sum_l w_l=1, for the declared
value, score or Hessian probe norm. For atomic rows the derivative features
are zero. The same baseline cancels when comparing fits using different
labels, so

\[
\|f_Y^{(k)}-f_h^{(k)}\|_w^2
=\|L_k(a_Y-a_h)\|_2^2.
\]

Equations (10) and (14) imply

\[
\mathbb E[\|f_Y^{(k)}-f_h^{(k)}\|_w^2\mid X]
\le\frac{\|L_k\|_{\rm op}^2}{\mu^2}\operatorname{tr}\Sigma_Y(X).
                                                                  \tag{15}
\]

The same argument covers a supremum over a fixed coordinate region by
replacing ||L_k||_op with sup_x ||partial_z^k Phi(x)||_2. Finite-mesh derivative
feature norms can be large: this theorem does not assert that Hessian accuracy
follows cheaply from a small value-risk error.

By (11), RB has a no-larger **upper bound in (15)**. It does not follow that
E[||a_RB-a_h||^2] or every realized derivative error is no larger: constrained
nonlinear minimization is not a linear conditional-expectation operation.
In particular a_RB is not generally E[a_raw|X,J]. A superior valid bound is
not a monotonicity theorem about actual fitted risk.

There is also an exact conditional paired-response bound. The same proof
applied to the two objectives with labels raw and RB gives

\[
\mathbb E[\|f_{\rm raw}^{(k)}-f_{\rm RB}^{(k)}\|_w^2\mid X,J]
\le\frac{\|L_k\|_{\rm op}^2}{\mu^2}\operatorname{tr}\widehat D(X,J).
                                                                  \tag{16}
\]

The center of (16) is the RB fit conditional on the realized skeletons.
It bounds the effect of the remaining Gaussian raw-label randomness on the
paired fitting comparison; it is not an error bound relative to T_i.

### Finite-sample probability and simultaneous probes

For any eta in (0,1), Markov's inequality applied to ||v_Y||^2 yields

\[
\Pr\!\left\{\|v_Y\|_2>
\sqrt{\operatorname{tr}\Sigma_Y(X)/\eta}\mid X\right\}\le\eta.
                                                                  \tag{17}
\]

Indeed the probability that a nonnegative variable exceeds its mean/eta is at
most eta, by integrating that variable over the event. Combining (17) with
(14) proves, on one event of probability at least 1-eta, all three bounds

\[
\|f_Y^{(k)}-f_h^{(k)}\|_w
\le\frac{\|L_k\|_{\rm op}}\mu
\sqrt{\operatorname{tr}\Sigma_Y(X)/\eta},\qquad k=0,1,2.         \tag{18}
\]

No additional union over probe locations or derivative orders is required:
the single coefficient-norm event controls all deterministic readbacks.
For simultaneous different fits/nodes/routes, allocate failure probabilities
prospectively and use a union bound; sharing data does not invalidate that
union bound. Do not present many per-fit 95% statements as one 95% family
statement without such an allocation.

A fully observation-bound-only but potentially weak version follows from
Var(Y|x)<=(M-c)^2/4 and ||Phi_j||_2<=1:

\[
\operatorname{tr}\Sigma_Y(X)
\le\frac{(M-c)^2}{4nM^2}.                                     \tag{19}
\]

The variance bound follows because a variable in [c,M] has variance at most
its second moment about the interval midpoint, hence at most (M-c)^2/4.
Partition of unity proves the feature-norm bound. Equation (19) applies to
both arms and alone does not quantify an RB improvement. The conditional
paired analogue of (17)--(18), with Sigma replaced by the known matrix
widehat D and center changed as in (16), is directly computable without
backward oracle labels. Plugging an unqualified variance estimate into (18)
does not automatically create a valid confidence bound.

### The protocol's simultaneous bounded-range bound

There are Q=2 scenarios * 3 seeds * 8 nodes * 2 budgets = 96 distinct data
problems. For each there are two label arms. Both methods use the same labels
and feature matrix, so they share v_Y; an additional method factor is not
needed for this gradient-noise event. For a family failure probability
eta_F=0.05, define the coordinate bounds for each problem by

\[
e_k=\frac{M-c}{nM}
\sqrt{\frac12\sum_j\Phi_{jk}^2
\log\!\left(\frac{2pQ\cdot2}{\eta_F}\right)},
\qquad p=35.                                                   \tag{19a}
\]

With probability at least 1-eta_F, simultaneously over all 96 problems,
both label arms and all 35 coordinates, |v_Y,k|<=e_k. The first factor 2
inside the logarithm counts the two signs; the last factor 2 counts arms.
Nested budgets, shared method inputs and paired arms need not be independent
for this union bound. Conditional on all declared designs, only independence
of suffixes within a problem is used in its individual tail bound.

For completeness, a centered scalar Z of range length ell satisfies
log E[exp(tZ)]<=t^2*ell^2/8. The logarithm's second derivative is the variance
under exponential tilting, bounded by ell^2/4 using the interval-midpoint
argument; integrating twice from zero proves the claim. Apply it to the
independent centered terms Phi_jk*(Y_j-h_j)/(nM), whose range lengths are
|Phi_jk|*(M-c)/(nM). Multiplying moment-generating functions and optimizing
the exponential Markov bound over t gives

\[
\Pr\{|v_{Y,k}|>s\mid X\}
\le2\exp\!\left[
-\frac{2s^2n^2M^2}{(M-c)^2\sum_j\Phi_{jk}^2}\right].
\]

A zero feature-column sum makes v_Y,k identically zero. Substitution of
(19a), followed by the finite union bound, proves the family statement.
Consequently the common coefficient radius may be taken as

\[
\mathcal B=\min\{\|e\|_2/\mu,\ 2A\sqrt p\},                 \tag{19b}
\]

where the second bound is the deterministic diameter of the shared box.
The corresponding maximum probe error is bounded by
max_l ||partial_z^k Phi(x_l)||_2 * B; the equally weighted RMS error is
bounded by ||D_k||_op*B/sqrt(number of probes), where D_k is the unweighted
derivative-feature matrix. These are bounds for the ideal noisy-label
optimum versus the same-design exact-mean optimum, not total target error.
Both label arms share this conservative bounded-range bound. The genuine
variance reduction in (11) is a separate, stronger structural fact; it must
not be attributed to the shared worst-case number (19b).

These global ridge-based bounds can be extremely loose or vacuous and must be
reported honestly. A local sensitivity approximation H(a_h)^(-1) Sigma
H(a_h)^(-1) may be descriptively useful, but is not a global finite-sample
certificate, especially with active box constraints. Floating-point
eigenvalues, computed covariances and real-arithmetic positivity arguments
are not interval-certified probability guarantees for a software execution.

## 7. Bias and optimization are not removed

The target of both expected fixed-design objectives is the same constrained,
penalized exact-mean empirical fit a_h. Its difference from the numerical
likelihood T_i contains continuous-design discrepancy, both penalty effects,
and fixed-family/box/tail approximation error. RB does not change these
population objectives or prove that these bias terms vanish.

For an actual solver output tilde a_Y, the exact derivative identity is

\[
\widetilde f_Y^{(k)}-T_i^{(k)}
=(\widetilde f_Y^{(k)}-f_Y^{(k)})
+(f_Y^{(k)}-f_h^{(k)})+(f_h^{(k)}-T_i^{(k)}).                    \tag{20}
\]

The middle term is controlled by (15)--(19). The first is optimization error;
the last is unchanged fixed-design constrained/penalized bias. If squared
norms are reported, the three squared terms and all three doubled inner
products must be retained for an exact decomposition. They are not additive
independent variance components. The longer archived diagnostic telescoping
chain remains a separate, valid description of its own fitted controls.

For any feasible solver output a with gradient g=grad J_Y(a), convexity gives
the box gap and real-arithmetic distance bound

\[
0\le J_Y(a)-J_Y(a_Y)\le
G(a):=g^\top a+A\|g\|_1,\qquad
\|a-a_Y\|_2\le\sqrt{2G(a)/\mu}.                              \tag{21}
\]

For the first inequality, minimize the linear lower bound over the box; for
the second use strong convexity and constrained optimality at a_Y. Derivative
readback multiplies the distance by ||L_k||_op. Computed solver flags or a
small projected gradient are not substitutes for a tight certified gap.
The unchanged optimizer is still used in the experiment; (21) is a diagnostic,
not authorization for a retry, stricter re-solve or learner modification.

The conditional mean of the fitted estimator need not equal a_h. Thus even
the label-only term may have nonlinear estimator bias in addition to its
random variability. The propositions concern bounded perturbations of its
objective, not an assertion of unbiased learned coefficients or scores.

## 8. Prospective matched-work comparison

The controlled comparison keeps the previous two scenarios, two method
offsets, three declared seeds, two nested per-node budgets, eight active
nodes, 35 coefficients, box, roughness, ridge and original fitting settings.
There are 192 fits per label arm and 384 fits in total. All planned arms,
budgets, fits and failures are reported, without selecting a result-dependent
subset or using oracle derivatives for fitting or stopping.

The 384 fits correspond to 96 distinct data problems, two label arms and two
method offsets. Removed-covariance matrices (12) are computed once for each
of the 96 paired data problems, not treated as 384 independent estimates.

Each raw/RB pair uses exactly the same initial feature design and the same
new forward jump skeletons. Methods share labels and designs. Lower-budget
inputs and labels must be verified prefixes of the larger-budget objects if
nested comparisons are claimed. Re-running a vectorized simulator with a
different array length need not preserve its bitwise prefix; generate or
bind the declared full roster before selecting a prefix.

The old simulator interleaves Gaussian and jump draws in one generator.
Simply omitting Gaussian draws changes later jump bits. The new paired
construction therefore needs explicitly independent design, jump and
Gaussian namespaces, or a retained common skeleton with a separately sampled
Gaussian stream. The raw marginal law stays the same; this does **not** claim
bitwise identity with archived raw labels. Old archives are not the paired
Monte Carlo control and must remain untouched.

“Matched work” means matched initial states, forward suffix count, macro
intervals, potential uniformization proposals, accepted births/deaths and
category skeletons. It does not mean equal floating-point operations, random
variates or wall-clock time. A transparent work vector records at least:

- unique designed states, forward suffixes and macro intervals;
- uniformization proposals, accepted births/deaths and selected births;
- C half-step updates, Gaussian variates drawn and conditional moment updates;
- raw observation-density evaluations and RB Gaussian-convolution evaluations;
- learner objective/gradient evaluations and solver iterations;
- label construction and fit wall times, with hardware/concurrency caveats.

Joint paired label generation incurs both raw Gaussian work and RB moment
work. Its total time is not the time of either standalone estimator. No
arbitrary weighted sum of operations is an established total-compute measure.
Variance-per-suffix reduction and observed implementation timing are distinct
claims. A time-matched efficiency study would require its own predeclared
allocation/calibration and cannot be retroactively inferred from equal n.

The Gaussian work removed is exactly the conditional variance (7). Repeated
coordinate replicates on one skeleton, if separately studied, would share
that skeleton and change the covariance structure and work counts; they are
not independent suffixes. No such extra replication is part of this protocol.

## 9. Implementation crosswalk and nonclaims

The derivation was checked against these unchanged modules:

- `src/heterodiff/experiments/continuous_forward_labels.py`: GRID, observation
  density, uniformization decisions, birth-mark law and both Heun half maps;
- `src/heterodiff/models/localized_likelihood_learner.py`: physical affine
  features, 35-control box, R and ridge, and the fixed `fit_likelihood` call;
- `docs/LOCALIZED_LEARNABILITY_FORMULATION.md`: target, observation convention,
  offsets, finite family and approximation scope;
- `docs/LOCALIZED_ERROR_DECOMPOSITION_FORMULATION.md`: the distinction between
  label perturbation, design, combined penalties, representation and optimizer
  error, including cross terms.

The separate new `src/heterodiff/experiments/continuous_rao_blackwell_labels.py`
implements paired skeleton/noise streams and the conditional moments in
(5)--(7). The real-arithmetic covariance and confidence-bound calculation is
separate from the unchanged learner in
`src/heterodiff/experiments/continuous_localized_variance_reduction.py`.

The ideal law permits unbounded Poisson proposal counts. A computational
watchdog must abort rather than truncate the count, reuse only a favorable
prefix, or silently resample a failed route. An abort is not an unbiased
completed result. Numerical normal generators and Gaussian arithmetic are
also not certified exact real-arithmetic samples.

This is a conditional-Gaussian variance-reduction control on a fixed finite
synthetic model. It does not establish general mixed-domain Rao--Blackwell
tractability, observation-amortized learning, original BCE success,
between-node score regularity, a valid sampler envelope, conditional endpoint
correctness, or production/GPU qualification. It proposes neither a learner
change nor a tolerance relaxation. Its scientifically testable contribution
at this stage is a law-preserving reduction of one identified source of
training-label noise, paired with explicit bounds and an unchanged learner.
