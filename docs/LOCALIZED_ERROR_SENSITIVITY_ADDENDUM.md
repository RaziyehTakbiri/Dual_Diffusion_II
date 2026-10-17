# Post-result exponential-Hessian sensitivity addendum

2026-09-13. **Post-result analytical follow-up**, not part of the primary
predeclared error-decomposition test. The original whole-box distance estimates,
fit coefficients, source bindings and acceptance tolerances are preserved.
No new fit, simulator label, oracle query, optimizer polish, learner change or
sampling experiment is introduced by this addendum.

The primary whole-box bounds can be loose because they use a likelihood floor
valid everywhere in a wide coefficient box. This motivates a separate question:
can the exponential structure bound the distance from an already saved fit to
the optimum of its **same finite weighted objective**, without pretending that
the Hessian eigenvalue at that fit is a constant global curvature modulus?

## Statement

Consider the fixed objective

\[
 F(a)=\sum_i\frac{w_i}{M}
 \{\exp(b_i+\phi_i^\top a)-Y_i(b_i+\phi_i^\top a)\}
 +\tfrac12a^\top P a,
\]

on a closed convex coefficient box C, with positive weights and M and a fixed
positive-semidefinite penalty P. Let a be any feasible point, a* a minimizer
on C, and

\[
 g=\nabla F(a),\quad H=\nabla^2F(a),\quad
 \lambda=\lambda_{\min}(H)>0,\quad
 L\ge\max_i\|\phi_i\|_2.
\]

For L>0, if `q=L*||g||_2/lambda < 1`, then

\[
 \|a-a^*\|_2\le
 -\frac{\log(1-q)}{L}.                       \tag{1}
\]

The norm is the **Euclidean raw-gradient norm**, not its largest coordinate.
One may conservatively replace `||g||_2` by `sqrt(35)*||g||_infinity` for this
family, but the numerical analysis below uses the saved full raw gradient.
The recorded maximum feature-row L1 norm is a conservative upper bound for L,
since each row's L2 norm is no larger than its L1 norm. No assumption that the
computed feature rows sum to exactly one is needed for that choice.

## Proof, including a constrained optimum

Write `d=a*-a` and `D=||d||_2`. Every positive weighted rank-one data term in
the Hessian satisfies

\[
 \exp(b_i+\phi_i^\top(a+td))
 \ge e^{-tLD}\exp(b_i+\phi_i^\top a),\quad 0\le t\le1.
\]

Because P is PSD and `e^(-tLD)<=1`, the penalty also dominates its scaled copy.
Consequently

\[
 H(a+td)\succeq e^{-tLD}H(a).                 \tag{2}
\]

This is a variation bound along the entire segment, **not** the assertion
`H(x)>=H(a)` everywhere. Integrating (2) yields, for D>0 and L>0,

\[
 [\nabla F(a^*)-\nabla F(a)]^\top d
 \ge\frac{\lambda D}{L}(1-e^{-LD}).          \tag{3}
\]

The constrained optimum obeys the variational inequality
`gradient F(a*) dot (a-a*) >= 0`. Thus the left side of (3) is at most
`-g dot d <= ||g||_2 D`. Canceling D gives

\[
 1-e^{-LD}\le L\|g\|_2/\lambda=q.
\]

For q<1, inversion proves (1). D=0 is immediate. This proof applies whether
the optimum or the observed point is interior or on the box boundary.
Positive H(a), together with (2), gives strict convexity along every nonzero
finite segment, so the box optimum is unique under these assumptions.

The bound can be sharp: for the scalar unpenalized objective `exp(a)-Y*a`,
with `0<Y<1`, observed point a=0, L=lambda=1 and a box containing `log(Y)`,
the optimum is `a*=log(Y)`, q=1-Y and (1) holds with equality.

If **L=0**, all feature rows vanish. The Hessian is the constant penalty P;
when lambda>0 the limiting bound is `||g||_2/lambda`. If lambda<=0, this argument
does not supply a Euclidean distance bound. For **q>=1**, (3) provides no finite
radius by this inversion; the sensitivity output is explicitly vacuous. A
finite box still gives an elementary diameter bound, but that is not silently
substituted for (1).

An optional mathematical sharpening replaces g by a minimum-norm normal-cone
residual at a: for n in N_C(a), `n dot d<=0`, and the proof uses `||g+n||_2`.
The saved-fit analysis deliberately uses **raw g** instead. It therefore needs
no active-set approximation and does not mistake a near-boundary coordinate
for an exact boundary normal. This changes no fitting procedure.

## What the numerical estimates do and do not establish

The theorem concerns true gradients and true positive spectral bounds in real
arithmetic. The report contains ordinary floating-point gradients and local
Hessian eigenvalues, not validated enclosures. Inserting those values into (1)
therefore produces **unvalidated analytical sensitivity estimates**, not
interval-certified coefficient-error bars. Positivity of a computed eigenvalue
does not by itself certify positivity of a true lower enclosure.

For each of the 512 saved fits, the standalone script records the raw gradient
L2 norm, computed lambda, recorded row-L1 upper bound, q, resulting radius or an
explicit vacuous reason, and the unchanged primary whole-box diagnostics.
It also checks feasibility and recorded exact-boundary activity. All 512 fits
are processed; none is refitted or selected as a replacement.

For a fixed saved probe matrix `B_k` of value, score or Hessian features, the
same-objective optimum response satisfies in real arithmetic

\[
 \|B_k(a-a^*)\|_\infty
 \le\max_j\|(B_k)_{j,:}\|_2\,D,
\]

and the continuous-probe RMS is at most
`||B_k,continuous||_2 * D / sqrt(256)`. The script uses the feature norms already
saved by the primary report. These are finite-roster response estimates and
inherit the noncertified status of the radius and recorded norms.

The optimum in this calculation is that of the **same finite empirical or
quadrature objective, with the same penalty, offsets and coefficient box**.
The bound does not remove population quadrature error, finite-label or
design-sampling error, representation bias, regularization bias, or mismatch
between the numerical-grid target and the continuous law. It does not certify
the original model, a sampler, or scientific superiority. In particular, this
post-result argument must not be presented as a predeclared success criterion.

## Reproduction and preservation

The new standalone script imports no model, optimizer or numerical oracle:
[analyze_localized_fit_sensitivity.py](../scripts/analyze_localized_fit_sensitivity.py).
It verifies the saved protocol hash, records the primary report hash, checks
that the input bytes remain unchanged, and writes only a new output file.

```bash
python scripts/analyze_localized_fit_sensitivity.py \
  --report research/fixtures/continuous_localized_error_decomposition_cpu_2026_09_13/report.json \
  --output research/fixtures/continuous_localized_error_sensitivity_2026_09_13.json
```

The destination must be absent. The predeclared primary bounds remain in their
original report and are copied, with hashes, into this separate sensitivity
record. Manufactured tests check the sharp scalar example, constrained and
zero-feature quadratic cases, the ratio threshold, finite-probe propagation,
and strict JSON handling without executing scientific fits.
