# Localized likelihood learning from forward simulation

2026-09-13. Prospective mathematical formulation for a synthetic, local-CPU
learnability check. This is a new fixed-observation learning experiment, not a
reinterpretation of the archived random-observation BCE results, an
oracle-supervised fit, or a conditional-sampler qualification. Existing targets,
acceptance tolerances, archived models and outcomes remain unchanged.

## 1. Question and fixed scope

The preceding localized interpolation controls ask whether exact supplied
values and scores can be represented accurately with controlled magnitude.
They do not establish that such a representation can be learned from random
observations. The next question is narrower and statistically meaningful:

> Can a fixed, smooth localized log-likelihood residual learn the backward
> likelihood and its coordinate derivatives from bounded forward-simulation
> labels, without using the independent backward likelihood or its derivatives
> as training labels or for model selection?

Work only with the existing cap-one, zero-BASE, selected-singleton synthetic
submodel. Its projected states are EMPTY (E), OTHER (O), and one selected
continuous occurrence C(z). The two fixed settings are
(theta,y)=(0.8,0.7) and (2.5,1.4), selected-key probability
rho=393217/524288, continuous and death rates one, horizon H=1, observation
standard deviation sigma=0.5, and contamination epsilon=0.1. The macro grid is

\[
u_i=i/8,\qquad i=0,\ldots,8.
\]

Separate residuals are fitted at the eight active nodes. The terminal
residual is exactly zero because both fixed baselines agree with the terminal
observation likelihood there. There is no interpolation between times,
no learned conditional endpoint generation, and no real-data access.

This projected model is not the general mixed-domain encoder. OTHER is an
exact aggregation here only because zero BASE, constant birth/death rates and
the selected-key observation make the coordinates of nonselected keys
irrelevant. That argument does not authorize the aggregation under arbitrary
learned potentials.

## 2. Forward-only label source

Let K_i be the unchanged numerical macro transition: a zero-BASE Heun half-step,
the full cap-one birth/death jump phase with continuous marks frozen, then a
second Heun half-step. For a continuous half-duration d and continuous rate
gamma, the ideal real-arithmetic map is

\[
z'=a_dz+\sqrt{v_d}\,Z,\quad
a_d=1-\gamma d/2+(\gamma d)^2/8,\quad
v_d=\gamma d(1-\gamma d/4)^2,\quad Z\sim N(0,1).       \tag{1}
\]

The middle phase has rates E to O equal to theta*delta*(1-rho), E to C
equal to theta*delta*rho, and occupied to E equal to delta. A selected birth
draws its mark independently from N(0,1). Births are blocked while occupied.
Marks do not evolve inside that middle phase, including after a birth; a
new mark receives only the final Heun half-step of that macro interval.

The label implementation uses uniformization, not backward Gaussian formulas.
For lambda=delta*max(theta,1), draw N~Poisson(lambda*Delta) per macro interval.
At each proposal accept an E birth with probability theta*delta/lambda or
an occupied death with probability delta/lambda; otherwise hold. An accepted
birth selects C with probability rho and draws its mark if needed. Proposal
times need not be generated because rates are constant and marks are frozen
inside the jump phase.

To verify the law, let Q be the projected generator and P=I+Q/lambda.
Conditional on N, the projected transition is P^N; averaging gives

\[
e^{-\lambda\Delta}\sum_{n\ge0}
\frac{(\lambda\Delta)^n}{n!}P^n=e^{\Delta Q}.
\]

The independent birth marks give the corresponding marked transition.
Composing with (1) proves equality with the specified ideal numerical
macro-kernel. The simulation does not evaluate this matrix exponential.

Define the reference density and positive contamination floor by

\[
\lambda_y=e^{-1}\rho\,\phi_1(y),\qquad c=\epsilon\lambda_y,
\]

where phi_v is the centered normal density with variance v. The known terminal
observation density is

\[
g_y(E)=g_y(O)=c,\qquad
g_y(C(z))=c+\frac{1-\epsilon}{2}\phi_{\sigma^2}(y-z).    \tag{2}
\]

Starting at a chosen active-node state x, independently simulate the remaining
macro transitions through H and set Y=g_y(X_H). Then

\[
\mathbb E[Y\mid X_{u_i}=x]
=(K_iK_{i+1}\cdots K_7g_y)(x)
=:h_i^\Delta(x).                                      \tag{3}
\]

Equation (3) is the tower property, not an oracle-label construction. Training
does simulate **forward terminal states** to evaluate the known observation
channel. It does not sample from the learned conditional endpoint law.

The source modules separate these roles:

- forward labels and specified model offsets:
  ../src/heterodiff/experiments/continuous_forward_labels.py;
- independent backward numerical target, used for evaluation only:
  ../src/heterodiff/evaluation/continuous_fiber_grid_target.py;
- statistical residual and convex fit:
  ../src/heterodiff/models/localized_likelihood_learner.py.

The equality in (3) concerns the ideal kernel. Finite random-number generators,
floating-point paths and resource failures are not certified exact samples.
A resource watchdog aborts rather than returning a truncated label, and a
failed route must not be silently replaced or reported as an unbiased
completed experiment. The watchdog threshold is not a truncation of the
mathematical CTMC.

## 3. Offsets, normalization and an observation-only capacity bound

For G+R, b_i is the log of the specified **uncapped** propagated association
likelihood. For DIR, b_i is log g_y, the zero-clock observation likelihood.
The ideal residuals for this experiment are

\[
d_{i,m}(x)=\log h_i^\Delta(x)-b_{i,m}(x),
\qquad m\in\{\mathrm{G+R},\mathrm{DIR}\}.               \tag{4}
\]

G+R's analytic guide is an allowed, fixed part of the model; it is not the
independent capped numerical backward target. Its approximation discrepancy
is precisely part of the residual to be learned. Neither a capped
continuous-time target nor a stage-time physical potential may be substituted
for h_i^Delta without changing the question.

All quantities in (2)--(4) use the same raw observation-density convention.
A consistently rescaled Radon--Nikodym convention would also be possible, but
would require transforming labels, offsets and normalization together.
There is no learned nuisance scalar or free post-fit gauge in this experiment.

A bound can be derived without inspecting any backward target values. Under
half-thinning, from any input count n, the probability of retaining exactly
one occurrence is n*2^(-n)<=1/2. Every noisy retained-mark density is at most
1/(sigma*sqrt(2*pi)); requiring the selected key only decreases the density.
Therefore, for both capped and uncapped configurations,

\[
c\le g_y(x)\le
M:=c+\frac{1-\epsilon}{2\sigma\sqrt{2\pi}}.             \tag{5}
\]

Every conditional expectation of g_y satisfies the same bounds. In
particular, h_i^Delta, the uncapped propagated G+R likelihood, and the
zero-clock DIR likelihood all lie in [c,M]. Thus

\[
|d_{i,m}(x)|\le L:=\log(M/c).                           \tag{6}
\]

The prospective physical coefficient box is [-A,A], A=2L. It uses only the
known observation channel and provides slack beyond the pointwise residual
bound. This replaced the proposed fixed quotient box [-8,8] **before fitting**
because the already archived capacity analysis showed that the latter
excluded required values. The replacement is not a result-selected
hyperparameter.

Equation (6) removes that particular fixed value-ceiling obstruction. It
does **not** prove that the fixed spline span or its bounded coefficients can
approximate every target value, score and Hessian to prescribed tolerances.
Spline coefficients need not themselves be bounded by the supremum of an
arbitrary represented function, and the boundary ties impose an additional
restriction.

## 4. Fixed affine localized family

On z in [-4.5,4.5], use degree-five clamped B-splines with 32 uniform cells,
cell width h=9/32 and 37 raw controls. Tie the first three raw controls and
the last three raw controls. There are 33 free continuous controls and two
atomic controls, hence 35 physical coefficients a per node.

Let Phi(x) denote these tied spline features on C(z) and the corresponding
one-hot features on E and O. The model is

\[
f_{i,m}(x)=b_{i,m}(x)+r_{i,m}(x),\qquad
r_{i,m}(x)=\Phi(x)^\top a_{i,m},\qquad
a_{i,m}\in[-A,A]^{35}.                                \tag{7}
\]

This is a quintic statistical subfamily, not the earlier oracle-jet Hermite
interpolant. Thirty-two spline cells, tied boundary derivatives and statistical
regularization deliberately differ from the 256-cell exact-input construction.
Success or failure is not a basis-only causal comparison with that construction.

B-spline nonnegativity and partition of unity are preserved by the endpoint
ties. Each endpoint has zero first and second derivative. Extending the
residual constantly outside the core is globally C2; it is C4 across interior
simple knots. These tails are imposed for bounded smoothness, not established
approximations to the true tail residual.

For storage at an active node, set tau_i=1-u_i and theta_i=a_i/tau_i.
Then r_i=tau_i*Phi^T theta_i and the quotient box is [-A/tau_i,A/tau_i].
Optimization is in physical a, not theta. This prevents a change in numerical
conditioning or regularization merely because a node has smaller tau.
The quotient bound is node-dependent: the notation r=tau*q alone does not
establish uniformly linear vanishing in a continuous-time limit. Terminal
r=0 is specified separately, and no between-node extension is provided.

## 5. Population target of the unpenalized risk

At each node and method, minimize the normalized Poisson quasi-risk

\[
\mathcal R(f)
=\mathbb E_\mu\!\left[
\frac{\exp(f(X))-Yf(X)}{M}\right].                      \tag{8}
\]

This is a conditional-mean loss for bounded, positive, real-valued density
labels. It does not assume that Y has a Poisson count distribution.

**Proposition 1 (unrestricted Fisher consistency).** At any design state x,
the unique finite pointwise minimizer of (8) is log h_i^Delta(x).

**Proof.** Conditional on x, the expected loss is
[exp(f)-h_i^Delta(x)*f]/M. Its first derivative is
[exp(f)-h_i^Delta(x)]/M and its second derivative is exp(f)/M>0.
Since h_i^Delta(x)>0, the sole zero of the derivative is log h_i^Delta(x).
Integrating over the design distribution proves uniqueness up to its
null sets. A shift of f changes exp(f); there is no arbitrary additive gauge.
This proves the claim. \(\square\)

Writing delta(x)=f(x)-log h_i^Delta(x), the exact excess risk is

\[
\mathcal R(f)-\mathcal R(\log h_i^\Delta)
=\mathbb E_\mu\!\left[
\frac{h_i^\Delta}{M}
\{\exp(\delta)-1-\delta\}\right].                       \tag{9}
\]

If |delta|<=D, Taylor's integral formula gives

\[
\mathcal R(f)-\mathcal R(\log h_i^\Delta)
\ge \frac{c\,e^{-D}}{2M}
\mathbb E_\mu[\delta^2].                               \tag{10}
\]

For the fixed box, D=A+L is a valid conservative bound. Equation (10)
controls log-likelihood value error under the design distribution. It does
not by itself control coordinate gradients or Hessians. For example,
delta_n(z)=sin(n*z)/n tends uniformly to zero on any compact interval while
its first derivatives need not tend to zero and its second derivatives grow.
A fixed finite spline family may admit design- and mesh-dependent norm
equivalences, but those do not supply a free accuracy guarantee for this
chosen family, penalty, finite sample and target.

## 6. Penalized empirical fit and what it changes

For each node, train with the fixed objective

\[
J_N(a)=
\frac1N\sum_{j=1}^N
\frac{\exp(b_j+\Phi_j^\top a)-Y_j(b_j+\Phi_j^\top a)}{M}
+\frac{10^{-4}}2\,a^\top R a
+\frac{10^{-6}}2\,\|a\|_2^2, \qquad a\in[-A,A]^{35}.    \tag{11}
\]

R is the positive-semidefinite matrix for the uniform-core mean of
(r''(z))^2, with zero atomic derivative blocks. Within each cell r'' is cubic,
so four-point Gauss--Legendre integration integrates its squared polynomial
exactly in real arithmetic. Its numerical evaluation is not interval-certified.
Both penalties apply to the **physical residual** coefficients at all nodes.

The data gradient and Hessian are

\[
\nabla J_{\rm data}
=\frac1{NM}\sum_j\Phi_j\{\exp(f_j)-Y_j\},\qquad
\nabla^2J_{\rm data}
=\frac1{NM}\sum_j\Phi_j\Phi_j^\top\exp(f_j).
\]

The Hessian is positive semidefinite. Adding 10^-4 R and 10^-6 I makes the
objective strongly convex with modulus at least 10^-6. The nonempty compact
convex coefficient box therefore has one unique empirical minimizer. The
same argument applies to the population penalized objective.

This theorem does not state that the minimizer equals log h_i^Delta.
The finite span, coefficient box, endpoint derivative ties, constant tails,
roughness penalty and ridge can all bias the population optimum.
Even infinite simulator data do not remove these fixed approximation and
regularization biases.

The fixed numerical optimizer is L-BFGS-B from zero physical coefficients,
maxiter=200, maxls=30, ftol=1e-12 and gtol=1e-7. It may terminate before
the unique optimum is accurately attained. Report its status, iteration count
and projected-gradient/KKT residual; do not infer convergence solely from
decreased loss or a successful program return. No backward-oracle evaluation,
validation risk or held-out derivative error changes this optimization rule.

## 7. Finite real-arithmetic value and derivative bounds

Let c_j be the full raw **physical** controls after tying, and t the clamped
knot vector. On the core define derivative controls

\[
D_j=\frac{5(c_{j+1}-c_j)}{t_{j+6}-t_{j+1}},\qquad
E_j=\frac{4(D_{j+1}-D_j)}{t_{j+6}-t_{j+2}}.             \tag{12}
\]

The derivative splines have nonnegative partition-of-unity bases. Consequently

\[
|r|\le\max_j|c_j|,\quad
|r'|\le\max_j|D_j|,\quad
|r''|\le\max_j|E_j|.                                  \tag{13}
\]

All relevant denominators are positive and at least h. The coefficient box
therefore implies the coarser bounds

\[
|r|\le A,\qquad |r'|\le10A/h,\qquad |r''|\le80A/h^2.    \tag{14}
\]

Atomic values also obey A, and constant tails have zero coordinate
derivatives. Stored quotient controls require multiplying their resulting
bounds by tau once. These bounds establish finite frozen residual magnitude
and derivatives; they do not establish small approximation error. They are
real-arithmetic bounds, not safe floating-point rejection/thinning envelopes,
cost bounds, or a certificate for the full offset-plus-residual physical
sampler.

## 8. Fixed sampling design, pairing and reporting

The prospective roster has two settings, both methods, three seeds
(11,29,47), two nested per-node training budgets (1024,8192), and eight active
nodes: 24 routes and 192 node fits. Training states follow the fixed repeated
pattern E,O,C,C. C coordinates are independent uniform draws on [-4.5,4.5].
Thus the design measure gives each atom mass 1/4 and C mass 1/2 with positive
density across the core.

Generate the larger training array once and use its exact prefix for the
smaller budget. Share the same state/label arrays across G+R and DIR; their
only method differences are the declared offsets and resulting fitted
coefficients. Generate 4096 independent validation labels per node/seed,
also shared across methods. Validation is descriptive and never selects a
checkpoint, optimizer stopping time, regularization, grid or reported budget.

With that reuse, the full roster contains 393216 unique training suffixes
and 196608 validation suffixes, 589824 in total. Summing remaining macro
intervals gives 2654208 suffix macro-interval executions, before counting
individual jump proposals or coordinate updates. This is a forward-label
budget, not a learned-conditional endpoint sample count.

The balanced stratified design is not an iid draw of category indicators, but
its exact category fractions and independent within-stratum labels give the
same population risk weights stated above. Positive population coverage
does not imply adequate finite-sample information in every local support.
Finite seeds and sample sizes require actual held-out assessments.

Report both budgets, both methods, every seed and every node, including solver
failures. Separate:

- simulator-only held-out unpenalized likelihood risk;
- independent numerical-target value, score and Hessian errors on the
  predeclared evaluation roster with unchanged tolerances;
- learned coefficient/envelope magnitudes, roughness, and solver diagnostics;
- comparisons to each fixed baseline and descriptive method/seed differences.

Independent capped numerical likelihood and derivative routines may be called
only for those evaluations, after the fit inputs and rules are fixed. They
must not supply labels, initialize coefficients, set penalty strengths, choose
spline resolution or stop a fit. This prohibits target leakage even though
the synthetic target is independently computable.

## 9. Scientific interpretation and remaining boundary

A favorable result would support one specific claim: bounded simulator
labels can train this localized fixed-observation residual sufficiently well
on the stated cap-one numerical-grid task. It would be evidence of
learnability beyond exact-jet interpolation. An unfavorable derivative result
would distinguish that learnability limitation from the already investigated
exact-input representation and curvature-reconstruction questions.

Neither outcome settles the original amortized random-observation BCE
learner. This experiment changes the objective, observation design, covariate
design, representation and regularization. It is not a pure causal test of a
single old architecture component. Three seeds do not establish universal
method superiority, and numerical-grid accuracy is not continuous-time
posterior accuracy.

No theorem here establishes a general full mixed-domain approximation result,
a uniform-in-observation/key-space bound, robustness to arbitrary noisy
learned jets, an interpolated stage-time potential, or an exact numerical
Doob sampler. Learning h on macro nodes does not by itself produce normalized
transition twists, a qualified initializer, or a stable full conditional path.
Those are separate integration questions, and the present comparison does
not launch that integration or relabel prior sampler outcomes.

