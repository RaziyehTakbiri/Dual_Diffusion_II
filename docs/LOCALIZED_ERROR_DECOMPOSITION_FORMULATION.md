# Controlled error decomposition for the localized likelihood learner

2026-09-13. Prospective diagnostic formulation, after the preserved
[forward-label learnability comparison](LOCALIZED_LEARNABILITY_PROTOCOL.md).
This document does not change that learner, its objective, archived fits,
observations, model family, tolerances or outcomes. It authorizes no model
selection, sampler integration or new forward-label generation. The purpose
is to distinguish possible error mechanisms using explicitly different
diagnostic objectives.

## 1. Why one further diagnostic is informative

The archived comparison completed 24 routes and 192 node fits under its
fixed 200-iteration optimizer. Its held-out risk improvements coexist with
substantial coordinate-score and Hessian errors. Those facts do not identify
whether finite simulator labels, coordinate design, the penalty, or the
fixed representation is responsible. Optimizer status alone also does not
quantify how far each saved fit is from its objective's constrained minimum.

The diagnostic keeps the two scenarios, both methods, all three original
seeds, both nested sample budgets, eight active nodes, the 35-coefficient
physical residual family, the coefficient box, and the target law fixed.
It compares an explicit chain of fitted functions rather than changing the
learner and retrospectively calling a new fit the old result.

The main interpretation is a **controlled, realized telescoping contrast**.
It is not a classical orthogonal bias--variance decomposition and not a
causal identification of separate independent sources of error.

## 2. Common objects and objective

Fix one scenario, method, active macro node and archived seed/budget.
Write x for E, O, or C(z), b(x) for that method's unchanged raw-density
baseline, Phi(x) for the same tied quintic features, and

\[
f_a(x)=b(x)+\Phi(x)^\top a,\qquad
a\in\mathcal C=[-A,A]^{35},\qquad A=2\log(M/c).
\]

Here c and M are the original observation-channel bounds. The target is the
same zero-BASE cap-one **numerical macro-grid** conditional mean

\[
h(x)=\mathbb E[g_y(X_H)\mid X_{u_i}=x],\qquad T(x)=\log h(x).
\]

This is not the uncapped guide or the capped continuous-time target.
The same raw-density normalization must be used in labels, b, h and M.
Coordinate derivatives concern C(z); atom values are reported separately.

For a design measure nu and a label mean m(x), define

\[
J_{\nu,m,\Lambda}(a)
=\int\frac{\exp(f_a(x))-m(x)f_a(x)}{M}\,\nu(dx)
+\frac12a^\top\Lambda a,\qquad
\Lambda=10^{-4}R+10^{-6}I.                              \tag{1}
\]

R is exactly the previous mean-core squared-residual-curvature matrix.
The empirical noisy objective replaces the integral by the archived mean
over pairs (X_j,Y_j), using Y_j rather than m(X_j).

The expected design is unchanged:

\[
\mu=\tfrac14\delta_E+\tfrac14\delta_O+
\tfrac12\,\operatorname{Uniform}[-4.5,4.5].
\]

The stored E/O/C/C roster has these category fractions exactly. Consequently
its empirical-design randomness is in the continuous coordinates, not the
category proportions.

## 3. Five contrasts, with ideal definitions

Use distinct labels for the following functions.

| Symbol | Definition | What is changed relative to the preceding member |
| --- | --- | --- |
| A | The archived finite-optimizer fit, reopened without mutation | Nothing; this is the original result |
| N | The constrained minimum of the same noisy empirical objective, with the same archived X and Y | Optimization accuracy only |
| M | The constrained minimum on the same archived X, replacing Y_j by h(X_j), keeping both penalties | Removes realized conditional-label noise |
| P | The constrained minimum of J_mu,h,Lambda | Replaces continuous empirical-coordinate design by its expected design |
| U | The constrained minimum of J_mu,h,0 in the same family and box | Removes both smoothness and ridge penalties |
| T | The unchanged independent numerical-grid log likelihood | Leaves the constrained, value-risk-minimizing family |

In the table, M as a function label is distinct from the known scalar
observation-density upper bound M in (1); subscripts or explicit words must
disambiguate them in implementations.

For every common evaluation state, the algebraic identity is

\[
A-T=(A-N)+(N-M)+(M-P)+(P-U)+(U-T).                       \tag{2}
\]

Recommended term names are:

1. **Archived optimization discrepancy:** A-N.
2. **Realized conditional-label-noise response:** N-M.
3. **Realized empirical-coordinate-design response:** M-P.
4. **Combined regularization shift:** P-U.
5. **Unpenalized constrained-class risk-projection residual:** U-T.

The last term is not automatically “pure representation bias.” U minimizes a
likelihood-value risk, not score/Hessian error. The fixed spline span,
coefficient box, tied endpoint derivatives, imposed tails and the geometry of
the design-weighted value risk all enter this residual. Another member of the
same family could have smaller derivative error while having larger value
risk. P-U removes both penalties together, so it cannot isolate smoothness
from ridge.

The exact target values used in M, P and U are deliberate **oracle diagnostic
labels**, not a newly claimed non-oracle learning result. They must remain in
a separate diagnostic module and receipt. They may not retroactively enter
the archived learner or its original freeze-before-oracle claim.

## 4. Coordinate derivatives, cross terms and nonadditive summaries

All fitted functions are C2 on the continuous core. Differentiating the
linear identity (2) gives the same identity for k=1,2, with D^0 the identity
and D^k the k-th coordinate derivative. Since the baseline is identical within
each method's chain, its derivatives cancel in every consecutive fitted-pair
difference.

On the predeclared finite continuous evaluation roster, let

\[
e_{j,k}=D^k(F_{j-1}-F_j),\quad
(F_0,F_1,F_2,F_3,F_4,F_5)=(A,N,M,P,U,T),
\]

and use the same nonnegative, normalized probe weights w throughout.
Then

\[
\|D^k(A-T)\|_w^2
=\sum_{j=1}^5\|e_{j,k}\|_w^2+
2\sum_{1\le j<\ell\le5}\langle e_{j,k},e_{\ell,k}\rangle_w. \tag{3}
\]

All ten cross inner products must be retained if squared RMS is decomposed.
They may be negative, indicating cancellation. Dividing the five diagonal
terms by the total squared error does not produce additive percentages and
may yield a sum larger than 100 percent. Negative cross terms must not be
discarded to manufacture a positive attribution.

A useful report includes the five signed error arrays, their 5-by-5 Gram
matrix, each norm, the signed cross terms, and the reconstructed total.
The Gram matrix is positive semidefinite in real arithmetic even though
individual cross entries may be negative. Triangle inequalities give upper
bounds such as ||A-T||_w <= sum_j||e_j||_w, not equality of norms.

Report atom errors separately rather than silently blending two atoms with
256 continuous probes. An explicitly declared EMPTY-centering linear
operator also preserves (2)--(3). Relative-likelihood errors, maximum
absolute errors and tolerance-failure counts do not obey additive
decompositions. For example, exp(A-T) is the product of the five consecutive
likelihood ratios, not their sum.

The algebraic telescoping identity holds for any approximate computed
members as well. What depends on solution quality is the **interpretation**
of each contrast, not this identity.

## 5. Numerical population controls: two finite quadratures

P and U are population minimizers in their mathematical definitions.
The actual proposed computation uses positive Gauss--Legendre rules with
q=16 and q=32 points **per each of the same 32 spline cells**. Include E and O
with their exact masses 1/4 each; continuous quadrature weights total 1/2.

Call the computed members P_q and U_q, not exact population fits. Report
both complete chains

\[
A-T=(A-N)+(N-M)+(M-P_q)+(P_q-U_q)+(U_q-T),\quad q=16,32. \tag{4}
\]

The prospectively designated primary is q=32; q=16 is only the fixed
numerical sensitivity control. Do not choose the rule or add a finer rule
after inspecting favorable errors. Report differences P_16-P_32 and
U_16-U_32 for coefficients, physical values, scores and Hessians, together
with cross-rule objective/gradient evaluations. These are quadrature-plus-solver
differences, not certified pure quadrature errors.

Read all A, N, M, P and U functions against the same q=32 unpenalized
population-risk quadrature. Its excess over the target can be evaluated as
sum_j w_j*(h_j/M)*(expm1(delta_j)-delta_j), with delta_j=f_j-T_j.
This is nonnegative in real arithmetic and is less cancellation-prone than
subtracting two large risk values. It is a common reporting rule, not an
additional selection or stopping criterion, and remains a finite quadrature.

The risk integrand exp(b+Phi*a)-h*(b+Phi*a) is generally not polynomial.
Neither finite quadrature is therefore an exact population integral.
Agreement of two rules is evidence of numerical stability, not a certified
error bound or proof of convergence to P and U. Without a justified
population quadrature bound, M-P_q includes a quadrature contribution and
U_q-T includes a quadrature/optimization contribution.

The roughness term is not newly approximated differently in these controls:
its degree-six piecewise integrand remains the same previous R.
Similarly, the unweighted feature Gram integrand Phi*Phi^T has degree at most
ten on each cell, so both proposed rules integrate it exactly in real
arithmetic. That fact does not make the nonlinear risk exact.

The population problems are shared across seeds and budgets: there are
2 scenarios times 2 methods times 8 active nodes, or 32 distinct problems
per penalty choice and quadrature. P/U rows repeated beside different
archived fits are not independent statistical replicates.

## 6. Convexity, uniqueness and finite-solver controls

For any positive weighted design, the data Hessian is

\[
H(a)=\frac1M\sum_jw_j\exp(f_a(X_j))\Phi_j\Phi_j^\top.
\]

It is positive semidefinite. The original ridge makes all N, M and P_q
problems strongly convex with global modulus at least 10^-6. Their box
minimizers are unique, even if an empirical design lacks full rank.

The unpenalized U_q problems are also strictly convex in the declared family.
If a feature combination vanishes at all positive-weight quadrature nodes,
its quintic polynomial on each cell has at least 16 distinct roots and is
identically zero there. Uniqueness of the clamped B-spline representation and
the full-column-rank endpoint-tying map force all 33 continuous coefficients
to vanish. The two positive-weight atoms force the remaining coefficients
to vanish. Thus

\[
G_q=\sum_j w_j\Phi_j\Phi_j^\top
\]

is positive definite. The analogous expected-design Gram matrix is positive
definite for the same reason, with vanishing almost everywhere implying
vanishing of each cell polynomial. Because b>=log c and |Phi*a|<=A,

\[
H(a)\succeq \frac cM e^{-A}G_q,\qquad
\mu_{U_q}:=\frac cM e^{-A}\lambda_{\min}(G_q)>0.         \tag{5}
\]

This is a global real-arithmetic lower bound over the entire box. A Hessian
eigenvalue observed only at a solution is merely local information and may
not replace (5). A floating-point eigenvalue estimate without outward error
bounds does not create a certified numerical lower bound.

The strict diagnostic re-solves use L-BFGS-B from all-zero physical
coefficients, maxiter=2000, maxls=50, ftol=1e-15 and gtol=1e-11. There is no
Newton refinement or retry. These settings are frozen before execution and
recorded separately from the original 200-iteration learner. They are
diagnostics, not a revised original training protocol. No target derivative
error may stop, restart or select a strict solve.

For each computed feasible coefficient vector a and gradient g=grad J(a),
the convex-box gap

\[
\mathcal G(a)=g^\top a+A\|g\|_1                        \tag{6}
\]

is a nonnegative upper bound on J(a)-min_C J. Indeed, convexity bounds the
suboptimality by max_{v in C} g^T(a-v), and minimizing g^T v over the box
gives (6). If a global strong-convexity modulus mu is valid,

\[
\|a-a^\star\|_2\le\sqrt{2\mathcal G(a)/\mu}.            \tag{7}
\]

Also report feasibility and a well-defined projected-gradient or
normal-cone stationarity residual, not just the optimizer's success flag.
A near-boundary coordinate must not be declared exactly active merely to
zero an inconvenient gradient. Equations (6)--(7) concern exact objective
and gradient arithmetic; ordinary float64 evaluations should be labeled
diagnostic estimates rather than outward certificates.

For a derivative feature row Phi^(k)(x), the corresponding optimization
readback error is at most
||Phi^(k)(x)||_2*sqrt(2G(a)/mu). Large conservative bounds must be reported
as such, not silently treated as negligible.

If N, M, P_q or U_q is not sufficiently resolved under the predeclared
quality checks, its contrasts remain valid recorded differences but cannot
cleanly carry the ideal names in Section 3. Report optimizer contamination
or an inconclusive mechanism diagnosis rather than extending the solve until
a desired interpretation appears.

## 7. What the conditional-label contrast identifies

Conditional on the saved design X_1,...,X_n, let

\[
v=\frac1{nM}\sum_j\Phi_j\{Y_j-h(X_j)\}.
\]

The noisy and exact-mean empirical objectives differ by an a-independent
constant minus v^T a. This is especially useful: their Hessians are identical
at every a. The label intervention changes only the linear term, not
regularization, design, basis, offset, box or curvature of the objective.

Under independent ideal suffix simulations,

\[
\mathbb E[v\mid X]=0,\quad
\operatorname{Cov}(v\mid X)
=\frac1{n^2M^2}\sum_j
\operatorname{Var}(Y_j\mid X_j)\Phi_j\Phi_j^\top.         \tag{8}
\]

Since c<=Y<=M, variance is at most (M-c)^2/4. The features are nonnegative
and sum to one at every projected state, so ||Phi_j||_2<=1. Consequently,

\[
\mathbb E[\|v\|_2^2\mid X]
\le\frac{(M-c)^2}{4nM^2}.                              \tag{9}
\]

If a_N and a_M are the ideal constrained minimizers and their common
penalized objective has modulus mu, their variational inequalities and strong
monotonicity give

\[
\|a_N-a_M\|_2\le\|v\|_2/\mu,\qquad
\mathbb E[\|a_N-a_M\|_2^2\mid X]
\le\frac{(M-c)^2}{4nM^2\mu^2}.                         \tag{10}
\]

To prove the first bound, write d=a_N-a_M. The two optimality inequalities
imply
mu*||d||^2 <= [grad J_mean(a_N)-grad J_mean(a_M)]^T d
<= v^T d, and apply Cauchy--Schwarz. A derivative readback bound follows by
multiplying by the corresponding derivative-feature operator norm.

These are useful consistency bounds but may be very loose with the global
ridge modulus 10^-6. They do not predict the observed error magnitude or
guarantee small Hessian errors. In particular N-M for one archived label
array is a realized response, not an estimated variance. Nonlinear
minimization, active constraints and penalties mean that E[a_N|X] need not
equal a_M even though the gradient perturbation is conditionally centered.

Three seeds permit descriptive paired contrasts, not a strong variance
estimator or general statistical superiority claim. The two sample budgets
are nested and the methods share labels; neither pair is independent.

## 8. Atomic internal controls and regularization interpretation

The continuous and atomic coefficients decouple in the objective. Atom
roughness penalties vanish, and the ridge is diagonal. Every original
design has exact atom weight w=1/4. Therefore the ideal M and P objectives
have identical scalar atom problems:

\[
\min_{|a_s|\le A}\;
\frac{w}{M}\{\exp(b_s+a_s)-h_s(b_s+a_s)\}
+\frac{10^{-6}}2a_s^2,\qquad s=E,O.                    \tag{11}
\]

Thus M-P has exactly zero atom values in real arithmetic, independent of
the random continuous coordinates or budget. The same holds with either
quadrature rule because the atom terms are represented exactly. A material
nonzero atom contrast is an internal check for solver error, inconsistent
weights/normalization, or a different objective; it is not genuine
continuous-design variation.

For U, the atom optimum is exactly a_s=log h_s-b_s. This lies strictly
within the box because |a_s|<=L<A. Hence ideal U-T also has zero atom
values. With ridge retained, the optimum lies between zero and that exact
correction: the derivative of (11) is strictly increasing and has opposite
signs at those two endpoints. Consequently the atom part of P-U is a
ridge-only shrinkage effect. The continuous part still combines both
roughness and ridge; no claim about one penalty alone follows.

For the full unpenalized population risk F and quadratic penalty B(a),
optimality gives

\[
0\le F(a_P)-F(a_U)\le B(a_U)-B(a_P)\le B(a_U).          \tag{12}
\]

The analogous inequality applies to each fixed quadrature. It bounds
unpenalized-risk increase, not derivative error. With a valid global modulus
mu_U for F, the variational inequalities also give

\[
\|a_P-a_U\|_2\le\|\Lambda a_P\|_2/\mu_U.                \tag{13}
\]

Again this is a real-arithmetic bound and can be loose. A penalty may improve
or worsen a particular score/Hessian probe despite increasing the
unpenalized objective.

## 9. Pre-run checks and control boundaries

Before any diagnostic fit:

- Reopen and hash-check the original protocol, report, all required raw
  dataset records, archived fits and freeze records. Verify that each
  shorter design/label array is its declared exact prefix and that both
  methods used the same arrays.
- Reconstruct each archived A from its physical coefficients in the
  unchanged feature map; compare to its saved outputs and original objective.
  Do not generate replacement labels or revise any archived coefficient.
- Bind the exact original constants, roughness matrix, coefficient box,
  baseline formulas, numerical-grid target and evaluation roster. The
  independent conditional mean used in M must be h^Delta, not the
  continuous-time likelihood or an approximate learned prediction.
- Freeze strict solver settings, feasibility/stationarity diagnostics,
  the two population quadratures, route roster and timing bounds before
  observing any diagnostic result.
- Verify positive normalized quadrature weights, exact atom masses, feature
  dimensions, fixed box feasibility and the shared full-rank Gram structure.
  Target values must remain finite, positive and in [c,M] up to explicitly
  handled numerical roundoff; no target-informed clipping is permitted.

Keep M, P_q and U_q explicitly labeled oracle-aided **diagnostic** controls.
They do not preserve the original non-oracle training-label claim, and they
must not be installed or promoted as the learner from that original run.

The complete planned roster contains 192 N and 192 M re-solves, plus
32 P and 32 U problems at each of two quadratures: 512 strict diagnostic
fits if all controls are computed once and shared as specified. There are
no new forward suffixes, observations, sampler paths, seed searches or
capacity changes in this diagnostic.

Use the same 256 core probes on [-4,4], both atoms and eight active nodes;
terminal coefficients stay exactly zero without a new fit. Preserve all
tolerance values. Diagnostic solver/readback checks are separate from those
scientific approximation thresholds and may not relax them.

## 10. Decision logic after the fixed diagnostic

The next scientific step should depend on this bounded evidence, not be
precommitted to changing the model:

- A-N material: first resolve or characterize optimization limitations.
- N-M material while strict solves are resolved: conditional-label noise
  is a demonstrated response for those arrays, not automatically a
  universal sample-complexity conclusion.
- M-P_q material with quadrature agreement and resolved solves:
  investigate finite continuous-design coverage within this design.
- P_q-U_q material: the combined penalty shifts the fit; the sign of its
  derivative impact must be measured, not presumed.
- U_q-T material despite resolved solves and stable quadrature: a
  constrained-class/value-risk projection limitation remains. It does not
  identify a unique architectural repair or establish that a derivative
  loss is necessarily optimal.

Several effects may coexist, cancel, or reinforce. Cross terms in (3) are
part of the result. No term closes the general mixed-domain scientific
model, restores old BCE claims, proves stage-time accuracy, or qualifies
conditional sampling. The diagnostic should conclude with an evidence-based
choice about the next learner change, while retaining the original result
as the original result.
