# Localized residual: quintic Hermite–Bézier construction

Date: 2026-09-13. Status: prospective local formulation, before the localized
comparison. This is a new deterministic oracle-approximation control. The
archived neural model, BCE experiment, Chebyshev results, original targets and
acceptance tolerances remain unchanged. No sampler integration, fit, endpoint
draw, GPU work or real-data access was performed for this derivation.

## 1. Fixed decision and scope

Use piecewise quintic Hermite–Bézier polynomials in the raw coordinate z.
The primary arm, VS_FINITE_DIFFERENCE, consumes only oracle values and
scores at uniform knots. A fixed fourth-order five-point difference of the
scores supplies one shared curvature estimate per knot. The separate
ORACLE_JET_VSH arm additionally consumes oracle Hessians and must be labeled
as stronger supervision, not a like-for-like primary success.

The core is [-4.5,4.5], with 64, 128 and 256 uniform cells; every resolution
is reported. Keep the earlier 256 evaluation coordinates in [-4,4] unchanged,
and verify before fitting that none coincides with a fitting knot. Do not
replace a colliding point or choose a different resolution after seeing errors.
Fixed one-unit collars extend to -5.5 and 5.5. At each outer endpoint use
the corresponding core endpoint's value with zero slope and curvature;
beyond it extend constantly. No target-accuracy claim covers these collars
or constant tails.

Keep the independent numerical-grid target, two scenarios, method baselines,
observations and macro nodes fixed. There is no between-node time
interpolation. At u=1 the residual is zero without division by a zero gate.
The envelope is a real-arithmetic bound, not a floating-point-safe sampling
certificate. The profile is not connected to the old sampler.

All six controls on each cell are explicit functions of its endpoint jets:
there are no unseen coefficients or rank-deficient global fit. This does not
establish that locality alone causes better results. The expanded core,
collocation roster and interpolation algorithm differ from the old V/VS
least-squares comparison. VS denotes the same label types, not the same
objective or solver. Preserve these distinctions in reporting.

## 2. Gate, target and coordinate conventions

At an active macro node u_i<1 let tau_i=1-u_i and define

\[
d_{m,i}(z)=\log h_i^\Delta(z)-b_{m,i}(z),\qquad
q_{m,i}(z)=d_{m,i}(z)/\tau_i.                              \tag{1}
\]

Here b_GR is the propagated uncapped association log-likelihood and b_DIR is
the zero-clock observation log-likelihood. Both methods use the same capped
numerical-grid target, not their own different posterior target. Native
observation-reference densities and raw oracle densities must be converted
consistently; the observation-only factor cancels from (1) and its latent
coordinate derivatives. Fit the canonical gauge; retain state-centered
diagnostics and the reference state's canonical value separately.

Construct p_i approximating q_i and return r_i=tau_i*p_i. Scores and Hessians
differentiate in raw latent z, not an observation or compactified coordinate.
Apply the gate exactly once. Atomic fibers require only scalar quotients.
The OTHER continuous fiber has a constant target in this cap-one selected-key
projection and supplies a zero-score/zero-Hessian control. This aggregation
uses exact benchmark symmetry, not arbitrary equivalence of native keys.
No theorem here covers every count, key, observation or context.

## 3. Local polynomial, C2 joins and envelopes

For one cell [a,b] of width w, set t=(z-a)/w. Let its endpoint jets be
(v_a,s_a,c_a) and (v_b,s_b,c_b), for quotient value, slope and curvature.
Define

\[
\begin{aligned}
B_0&=v_a,& B_1&=v_a+\tfrac w5s_a,&
B_2&=v_a+\tfrac{2w}5s_a+\tfrac{w^2}{20}c_a,\\
B_3&=v_b-\tfrac{2w}5s_b+\tfrac{w^2}{20}c_b,&
B_4&=v_b-\tfrac w5s_b,& B_5&=v_b.
\end{aligned}                                               \tag{2}
\]

Then p(z)=sum_k B_k binom(5,k)t^k(1-t)^(5-k).
Differentiating verifies the six endpoint conditions. They determine a unique
polynomial of degree at most five: the difference of two solutions would
have zeros of multiplicity three at each endpoint and hence degree at least
six unless identically zero.

Write Delta B_k=B_{k+1}-B_k and let mathcal B denote a Bernstein basis.
Direct differentiation gives

\[
p'(z)=\frac5w\sum_{k=0}^4\Delta B_k\,\mathcal B_{k,4}(t),\qquad
p''(z)=\frac{20}{w^2}\sum_{k=0}^3\Delta^2B_k\,\mathcal B_{k,3}(t).
                                                               \tag{3}
\]

Nonnegativity and partition of unity therefore imply

\[
|p|\le\max_k|B_k|,\quad
|p'|\le\frac5w\max_k|\Delta B_k|,\quad
|p''|\le\frac{20}{w^2}\max_k|\Delta^2B_k|.                    \tag{4}
\]

For the whole frozen profile, take the maximum over every core and collar
cell, including atomic constants in the value bound, and multiply by tau_i.
Use each cell's actual width: collar width is one, not the core width.
Constant tails have zero derivatives and their endpoint values already appear
among the controls. Thus finite controls give finite global real-arithmetic
value, score and Hessian envelopes. A derivative-magnitude bound is not a
derivative-error bound.

Each interior knot uses one jet shared by both neighboring cells, including
one shared estimated curvature in the primary arm. Equations (2)–(3) give
matching value, first derivative and second derivative, so p is C2.
Each collar joins a core jet to the prescribed outer constant jet; the
constant extension preserves C2 at the outer joins. Third derivatives may
jump: this is not a C-infinity claim. For each frozen one-dimensional profile,
the bounded second derivative yields a globally Lipschitz gradient. That
statement does not certify a numerical sampler or conditional path law.

## 4. Primary VS curvature rule: no Hessian labels

For uniform knots z_j=a+jh, j=0,...,N, let g_j=q'(z_j) be the supplied
score quotient and require N>=4. Differentiate the quartic interpolant of
five supplied scores:

\[
\begin{aligned}
\widehat c_0&=(-25g_0+48g_1-36g_2+16g_3-3g_4)/(12h),\\
\widehat c_1&=(-3g_0-10g_1+18g_2-6g_3+g_4)/(12h),\\
\widehat c_j&=(g_{j-2}-8g_{j-1}+8g_{j+1}-g_{j+2})/(12h),
\quad 2\le j\le N-2.
\end{aligned}                                               \tag{5}
\]

At N-1 and N use the reflected derivative stencils: reverse the corresponding
left stencil and negate its weights. Compute each curvature once and share it
across cells. The primary constructor consumes only values and scores.
Oracle Hessians may be evaluated separately but must not leak into its
controls. The VSH arm instead explicitly sets c_j=q''(z_j).

If q is C6 on the core and M_6=sup|q^(6)|, then

\[
\max_j|\widehat c_j-q''(z_j)|\le\tfrac15 M_6h^4.             \tag{6}
\]

Proof: let g=q' and P be its degree-four interpolant on the selected five
knots. At one of those nodes x, set W(t)=product_k(t-z_k). Subtract from
g-P the multiple [(g-P)'(x)/W'(x)]W. The result has five zero values and a
repeated zero derivative at x. Repeated Rolle's theorem gives a point xi
where its fifth derivative vanishes, proving
(g-P)'(x)=g^(5)(xi)W'(x)/5!.
For the endpoint, adjacent-to-endpoint and central node of five uniform knots,
|W'(x)| is 24h^4, 6h^4 and 4h^4, respectively. The constants are thus
1/5, 1/20 and 1/30. Their maximum proves (6); differentiating the quartic
interpolant produces the weights in (5).

This is an exact-input real-arithmetic statement. Score roundoff or noise is
amplified by a factor proportional to 1/h. Finer grids need not improve an
actual floating-point result monotonically.

## 5. Constructive local value, score and Hessian approximation

**Theorem.** For each declared active macro node and one-dimensional continuous
fiber, suppose q is C6 with finite M_6 on the core. Use its exact values and
scores at uniform knots. The primary construction is C2 and approximates
q, q' and q'' uniformly on the core with orders h^6, h^5 and h^4.
The VSH arm has those orders with exact curvature labels. Constants may depend
on the compact target family, not h. Multiplication by tau_i gives the
residual bounds. The theorem covers a finite node/fiber roster.

**Exact-jet proof.** On a cell, let T_5 be the order-five Taylor polynomial of
q at the left endpoint. For R=q-T_5, Taylor's integral remainder gives
|R^(j)(z)|<=M_6 h^(6-j)/(6-j)! for j=0,1,2. Its left jet vanishes.
Applying (2) to R sets the first three controls to zero and bounds the last
three controls by (49/7200)M_6h^6, using
|R(b)|<=M_6h^6/720, |R'(b)|<=M_6h^5/120,
|R''(b)|<=M_6h^4/24.

The Hermite operator H reproduces T_5. Equation (4), together with
max|Delta B|<=2max|B| and max|Delta^2B|<=4max|B|, gives the valid non-sharp
bounds

\[
\begin{aligned}
\|q-Hq\|_\infty&\le(59/7200)M_6h^6,\\
\|q'-(Hq)'\|_\infty&\le(11/144)M_6h^5,\\
\|q''-(Hq)''\|_\infty&\le(211/360)M_6h^4.
\end{aligned}                                               \tag{7}
\]

These bounds estimate derivatives directly; they do not differentiate the
unspecified xi in a value-only interpolation remainder.

**Estimated-curvature perturbation.** Changing either endpoint curvature by
at most delta changes only B_2 or B_3, by at most h^2 delta/20. Equation (4)
bounds the resulting value, score and Hessian perturbations by
h^2 delta/20, h delta/2 and 4delta respectively. Combining with (6) preserves
the orders. Valid uniform constants for the primary arm in place of (7) are
131/7200, 127/720 and 499/360 respectively.

Apply this proof cellwise and take the maximum M_6 across the finite node/fiber
list. Atomic constants are represented directly; terminal tau=0 gives zero
residual and coordinate derivatives by definition. No optimizer-convergence
assumption is used.

The positive-contamination finite Gaussian-mixture likelihoods and the
declared baselines supply this smoothness on the compact benchmark through
their explicit formulas. General learned potentials, arbitrary counts,
unbounded observations and infinite metadata families are not covered.
For active nodes close to the terminal, q=d/tau may have a larger derivative
constant; the roster is finite and excludes tau=0. A uniform continuum-of-time
claim requires additional boundary regularity, as explained in
[the capacity formulation](RESIDUAL_CAPACITY_FORMULATION.md).

**Mesh-uniform value-envelope corollary.** Let M_j=sup_core|q^(j)| for
j=0,1,2,6, with exact supplied values and scores. Equation (6) gives
|c-hat|<=M_2+(1/5)M_6h^4. Every core cell has h<=1 and each collar has
width one. Applying (2) to either kind of cell therefore yields

\[
\max_{\text{core and collar controls}}|B_k|
\le M_0+\tfrac25M_1+\tfrac1{20}M_2+\tfrac1{100}M_6h^4.
                                                               \tag{8}
\]

The outer collar values equal core endpoint values, so no unknown tail-target
constant is needed for this bound. Take the maximum of (8) over the declared
continuous fibers and their atomic quotient constants, then multiply by tau_i
for the whole-profile residual envelope. For the VSH arm, omit the last term.
Consequently the exact-input C6 construction has a value envelope bounded
uniformly as the core mesh is refined; coefficient growth is not forced by
increasing the cell count. This is an analytic real-arithmetic corollary, not
a measurement of M_j, a numerical estimate of a certified upper bound, or a
floating-point-safe sampling certificate.

## 6. Limits of the tail and envelope construction

The one-unit collars do not shrink with the core grid and are excluded from
the local error theorem. They impose a globally bounded C2 extension, not an
independently established tail target. They may supply the largest value or
derivative envelope and must be included in the whole-profile maxima. No
control is discarded because it lies outside the evaluation range.

Real-arithmetic convex-hull bounds do not certify a floating-point upper
envelope. Numerical evaluation, overflow treatment and coefficient binding
need separate treatment before any bound is used for accept/reject or rate
thinning. This comparison does not build that machinery or connect the
profile to the old sampler. Small nodewise errors would not prove that
coefficient tilting implements normalized numerical Doob transitions, or
that Heun midpoint stages approximate the conditional law.

## 7. Required reporting and interpretation

Report every fixed resolution, both supervision arms, both scenarios and both
method baselines. Verify disjoint fitting/evaluation coordinates before
construction. At every node retain value, state-relative potential, score and
Hessian errors against the unchanged target, including the OTHER zero-score
control and terminal identity. Report knot interpolation errors, C2 joins,
collar/tail checks, maximum controls and whole-profile real-arithmetic value,
score and Hessian bounds. Do not change gauge to conceal a canonical error.

The primary arm's Hessian-label access is false for construction; the VSH
arm's is explicitly true. A VSH benefit cannot be relabeled as a VS result.
The primary theorem shows how score differences recover the required
curvature order without Hessian labels under stated smoothness. Finite
numerical results must still verify the behavior.

Keep the older Chebyshev failures visible in descriptive comparisons.
The changed core width, knots and interpolation rule prevent a basis-only
causal conclusion. No favorable resolution selection, new metric threshold,
endpoint top-up or training claim follows. The purpose is a localized,
interpretable likelihood/score approximation with explicit finite envelopes,
before separately assessed integration into a sampler or general learner.
