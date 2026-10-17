# Seventh-point score-derived curvature: limited formulation

2026-09-13. This note supplements the
[localized residual proof](LOCALIZED_RESIDUAL_FORMULATION.md) without changing
its archived five-point construction, outcomes or tolerances. The seventh-point
control changes only the shared curvature estimate at the same fixed knots.
It does not add oracle Hessian labels, change the quintic interpolation, or
qualify learned noisy jets, tails, stage-time potentials or a sampler.

## 1. Fixed mathematical rule

Let q be the ungated residual quotient on a uniform knot grid z_j=a+jh.
The supplied values are q(z_j) and g_j=q'(z_j). For each knot differentiate
the degree-six interpolant of seven nearby supplied scores. At an interior
knot with three neighbors on each side the rule is

\[
\widehat c_j=
\frac{-g_{j-3}+9g_{j-2}-45g_{j-1}
      +45g_{j+1}-9g_{j+2}+g_{j+3}}{60h}.                 \tag{1}
\]

The first three knots use the degree-six interpolant on the first seven knots;
the last three use its reflected counterpart. Boundary weights must be fixed
by polynomial reproduction, not chosen separately for failing evaluation
locations. There must be at least seven knots. Compute one curvature at each
knot and share it between the two adjoining quintic cells.

## 2. Curvature error

If q is C8 on the core and M_8=sup|q^(8)|, then

\[
\max_j|\widehat c_j-q''(z_j)|\le M_8h^6/7.                \tag{2}
\]

Proof: write g=q', let P be its degree-six interpolant on the seven selected
knots and W(t) the product of their seven linear factors. At the queried knot
x, subtract [(g-P)'(x)/W'(x)]W from g-P. The result has seven zero values,
one of them with a repeated zero derivative. Repeated Rolle's theorem gives

\[
(g-P)'(x)=g^{(7)}(\xi)W'(x)/7!
\]

for some point in the stencil interval. If x is the j-th selected node,
j=0,...,6, then |W'(x)|=j!(6-j)!h^6. The successive absolute error constants
from the boundary toward the center are

\[
1/7,\quad 1/42,\quad 1/105,\quad 1/140.
\]

The reflected values agree. This proves (2). It is an exact-score,
real-arithmetic bound, not an interval-certified numerical estimate of M_8.

## 3. What order improves, and what does not

An endpoint curvature error at most delta perturbs a quintic Bézier control
by at most h^2 delta/20. The convex-hull derivative formulas bound the resulting
value, score and Hessian perturbations by h^2 delta/20, h delta/2 and 4delta.

Substitution of (2) therefore bounds the additional curvature-estimation
contributions by

\[
M_8h^8/140,\qquad M_8h^7/14,\qquad 4M_8h^6/7.             \tag{3}
\]

The exact-jet quintic still has its own value/score/Hessian approximation
orders h^6, h^5 and h^4 under C6 regularity. Thus this control suppresses the
curvature-reconstruction contribution; it does not turn the full quintic
interpolant into an overall sixth-order Hessian method. A pass is not
guaranteed by the asymptotic order, and the same target/tolerances must remain
unchanged when the finite control is evaluated.

## 4. Mesh-uniform value envelope

For h<=1 core cells and the fixed unit-width collars, let M_j=sup|q^(j)|
for j=0,1,2,8. The quotient control bound becomes

\[
\max|B_k|
\le M_0+\tfrac25M_1+\tfrac1{20}M_2+\tfrac1{140}M_8h^6.   \tag{4}
\]

As in the original proof, include every core/collar control and the atomic
quotient constants, then multiply by the active-time gate for a whole-profile
residual bound. The collars are an imposed C2 bounded extension, not an
oracle-accurate tail model. Equation (4) is not a floating-point-safe
rejection/thinning envelope.

## 5. Noise and learning remain separate

The centered seven-point derivative weights have absolute sum 11/(6h);
the centered five-point weights have sum 3/(2h). A uniform error epsilon in
the supplied scores can therefore contribute as much as 11 epsilon/(6h)
to the centered curvature estimate. One-sided weights amplify errors more.
Higher truncation order does not imply greater robustness to learned or noisy
scores, and decreasing h may amplify their errors.

Consequently this single control tests a deterministic approximation mechanism
with the same exact score-label types. It does not solve the non-oracle
learnability problem. A later learner must be evaluated from its own noisy
training source, with independent target formulas reserved for evaluation and
without relabeling this exact-input control as a training result.

