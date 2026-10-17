# Residual capacity: boundary condition, constructive approximation and controls

Date: 2026-09-13. Status: prospective local formulation and proof, before the
new controlled oracle-supervised comparison. This document does not modify
the archived neural model, its BCE objective, previous results or acceptance
tolerances. No fit, endpoint sample, GPU operation or real-data operation was
performed to establish the statements below.

## 1. Decision and scope

The old fixed outer `0.25*tanh(raw/0.25)` cannot represent the required
state-relative likelihood corrections on the declared benchmark. The
[capacity diagnosis](RESIDUAL_LIKELIHOOD_SCORE_ANALYSIS.md) proves that failure
independently of optimizer convergence and observation-only gauge. Retaining
the linear active-time gate is appropriate, but retaining an arbitrarily small
fixed amplitude ceiling is not a sufficient-capacity formulation.

The replacement principle is

\[
r_\theta(u,x,a)=\gamma(u)\,F_\theta(u,x,a),\qquad
\gamma(u)=(H-u)_+/H,                                      \tag{1}
\]

where H is the active endpoint (one in the present benchmark), the readout
coefficients of F are not confined to a preassigned amplitude box, and every
frozen finite model has a computable finite envelope. This is a finite
coefficient model with unbounded *available capacity*, not an infinite-valued
or unnormalizable realized potential. For the held segment u>=H set r=0.

The selected controlled formulation is a separate compactified Chebyshev
sieve: psi(z)=tanh(z/2), one expansion per discrete fiber and active macro
node, unrestricted finite coefficients, and degrees 16, 32 and 64 all reported.
Its coefficients are frozen after the deterministic fit. The diagnostic code
caps degree at 128; the mathematical family allows degree to grow, so the
existence theorem is not an arbitrary-accuracy claim for that finite code cap.
Terminal evaluation
returns zero; this comparison provides no between-node evaluation or
interpolation operation. It is not connected to the
old sampler. Its coefficient l1 envelope is a real-arithmetic bound, not an
outward-rounded floating-point sampling certificate.

Two implementations must be distinguished:

- Removing the outer tanh from a linear readout over bounded neural hidden
  features removes the proved amplitude obstruction. It does not prove that
  the existing fixed-width, compressed feature map can represent the target.
- A growing polynomial sieve over smoothly compactified coordinates gives a
  constructive sufficient-capacity theorem on the explicitly declared compact
  finite-fiber problem. This is the defensible oracle-supervised capacity
  control; it is not a silently substituted full general neural learner.

Neither statement asserts universality of width 128, injectivity of the old
observation encoder, representation of every discrete key, or approximation
uniformly over unbounded observations and coordinates.

## 2. The target and its normalization

For a fixed observation and context, let h_i^Delta be the independent
likelihood under the original zero-BASE numerical macro-grid law. Use its
native observation-reference convention consistently with the baselines

\[
b_{G+R}=\log\widetilde h_{\rm uncapped},\qquad
b_{DIR}=\log g,\qquad
d_{m,i}=\log h_i^\Delta-b_m.                              \tag{2}
\]

The common target h is unchanged by choosing a different residual basis.
The independent oracle returns raw observation density; subtract log lambda
when comparing absolute native log-potentials. The subtraction cancels from
(2) if both terms use the same raw convention. Coordinate derivatives do not
depend on this observation-only normalization.

The canonical supervised residual is d itself. Its compatible classifier
nuisance is -log m^Delta in native convention, or log lambda-log m_raw in raw
oracle notation. No nuisance needs to be fitted to diagnose this known target.
If a comparison instead uses state-centered potentials, it must retain the
reference state's value separately to identify this canonical gauge. An
observation-only shift is physically harmless, but arbitrary time-dependent
recentering changes the implemented classifier family and cannot silently be
attributed to its observation-only nuisance.

At the terminal node h_L=g and both baselines equal g, so d_{m,L}=0. This
identity motivates (1). The likelihood score means differentiation with
respect to a latent continuous coordinate, not the observation coordinate and
not the full posterior marginal score. OTHER fibers have zero target
likelihood score in the present selected-key cap-one projection.

## 3. What division by the gate assumes

### Fixed macro nodes: no extra boundary regularity is needed

On the actual active nodes u_0,...,u_{L-1}<H, define

\[
q_{m,i}(x,a)=d_{m,i}(x,a)/\gamma(u_i).                     \tag{3}
\]

There are finitely many strictly positive denominators. If each d_i is C^2
on a declared coordinate neighborhood, so is q_i. Terminal r_L=0 is set
exactly. These statements need no claim that the numerical-grid likelihood
has an identified value or time derivative between its macro nodes.

The [independent numerical target](../src/heterodiff/evaluation/continuous_fiber_grid_target.py)
is specifically a macro-node conditional likelihood. Its split jump and Heun
stages are not extra observations of one already identified continuous-time
conditional law. A continuous extension chosen for a potential is an
additional algorithmic interpolation policy, not a theorem about those stages.

### Continuous reference: an explicit sufficient assumption

Write D(tau,x,a)=d(H-H*tau,x,a), so tau=gamma on the active interval. Suppose
D(0,x,a)=0 and the mixed derivatives of partial_tau D through order two in
the continuous coordinates exist and are jointly continuous on a neighborhood
of the declared compact domain. Then

\[
q(\tau,x,a)=\begin{cases}D(\tau,x,a)/\tau,&\tau>0,\\
\partial_\tau D(0,x,a),&\tau=0,
\end{cases}
=\int_0^1\partial_\tau D(s\tau,x,a)\,ds.                 \tag{4}
\]

The fundamental theorem of calculus proves (4). Differentiating its integral
in coordinates, using continuity on a compact set, proves a continuous C^2
coordinate extension of q to tau=0. Stronger time-derivative claims require
the corresponding stronger mixed regularity. The positive-contamination,
finite-Gaussian-mixture benchmark satisfies these local conditions directly
from its explicit formulas. They are not assumed automatically for a general
learned jump-diffusion on every key and unbounded observation space.

An active-side nonzero derivative at H is compatible with a linear gate.
Extending by zero into a clean hold gives a continuous, piecewise time-smooth
potential, not necessarily a globally C^1 time join. Requiring every time
derivative to vanish would reintroduce an unjustified flat-boundary constraint.
Coordinate C^2 regularity and time-boundary regularity are distinct conditions.

## 4. Frozen envelopes without a fixed capacity ceiling

Let F_theta=sum_j theta_j phi_j, with a finite coefficient vector and known
global bounds |phi_j|<=M_j. Then

\[
|r_\theta(u,x,a)|\le\gamma(u)R_\theta,\qquad
R_\theta=\sum_j|\theta_j|M_j<\infty.                     \tag{5}
\]

For a neural linear readout over tanh-bounded hidden features this becomes
R=|bias|+sum_j|weight_j|. Hidden-feature training does not invalidate this
bound provided their final forward expressions remain bounded as stated.
Finite coefficients, the evaluated model and the certified envelope must be
bound together after training; the envelope cannot remain the old constant
0.25. This removes the former hard bound while preserving an explicit bound
for every frozen model.

For a residual-tilted initialization proposal Q with density proportional to
the same baseline used in (2), accepting a proposal x with probability
exp(r(0,x)-R) yields the law proportional to exp(r(0,x))Q(dx). Indeed the
accepted joint measure is exp(-R)exp(r(x))Q(dx), and normalization removes
exp(-R). Since -R<=r<=R, the acceptance probability is at least exp(-2R).
The same finite upper bound can be added to the baseline bound used by the
existing jump-envelope construction. These are validity statements, not
efficiency guarantees: exp(2R) may be impractically large, gradients may be
large, and finite-resource refusal remains possible. A sampler must fail
explicitly rather than silently truncate or change the law.

A polynomial in the raw coordinate need not have a global finite envelope.
The selected formulation uses the smooth compactification

\[
\psi(z)=\tanh(z/2).                                     \tag{6}
\]

with its scale fixed before fitting. The whole real line maps inside (-1,1).
Chebyshev features T_k(psi) obey |T_k|<=1, so (5) is the coefficient l1 bound.
Bernstein features used in the existence proof below are nonnegative and sum
to one, but are not a second fitted experimental basis. The selected features
are smooth globally. Raw T_k(z/s) outside [-s,s] or clipping z into that
interval does not provide this smooth bounded-feature construction.

The maximum of the finite node/fiber l1 bounds covers the declared roster.
No interpolation is selected. The transformation's tail saturation
is not a guarantee of tail approximation: the theorem below is explicitly on
compact coordinates. A finite coefficient envelope also does not establish
a small score error or a stable numerical integrator.

## 5. Constructive sufficient capacity, including scores and Hessians

**Theorem (finite-node, finite-fiber compact C^2 capacity).** Fix a finite
macro-grid, a finite set of discrete fibers and fixed observation/context
values. For each one-dimensional continuous fiber fix a finite compact
coordinate interval. Suppose q_i from (3) is C^2 on a neighborhood of each
interval. Atomic fibers require only a finite scalar value. Then for every
epsilon>0 there is a finite-degree compactified polynomial residual of form
(1), with a finite computable envelope, whose value, first coordinate
derivative and second coordinate derivative approximate d_i on all those
intervals and nodes within epsilon. The terminal residual is exactly zero.
The degree and coefficients may depend on epsilon; no fixed-degree guarantee
is asserted.

**Proof.** On a continuous fiber set t=psi(z). The inverse transformation is
smooth on the image [a,b], a compact subinterval of (-1,1). Thus
F(t)=q_i(psi^{-1}(t)) is C^2 near [a,b]. Extend F'' continuously to [-1,1],
for example by its endpoint values outside [a,b]. Integrating this extension
twice and matching F(a),F'(a) produces a C^2 extension of F to [-1,1].

For any continuous G on [0,1], its Bernstein polynomial is
B_nG(t)=E[G(K/n)] with K binomial(n,t). Uniform continuity and
Var(K/n)<=1/(4n) imply for every delta>0

\[
\sup_t|B_nG(t)-G(t)|
\le\omega_G(\delta)+\frac{\|G\|_\infty}{2n\delta^2},     \tag{7}
\]

where omega is the uniform modulus of continuity. Split the expectation on
|K/n-t|<=delta and its complement, and apply the variance bound to the latter
to obtain (7). First choosing delta small and then n large proves uniform
polynomial approximation of a continuous function. Apply it, after an affine
change of interval, to the extended F''. Let a polynomial P have this
approximating second derivative and match F(a),F'(a). If the second-derivative
error is at most eta, integration over an interval of length at most two gives

\[
\|P''-F''\|_\infty\le\eta,\quad
\|P'-F'\|_\infty\le2\eta,\quad
\|P-F\|_\infty\le2\eta.                                \tag{8}
\]

The error after composing with psi has first derivative bounded by
2eta sup|psi'|, and second derivative bounded by
eta sup|psi'|^2+2eta sup|psi''|. These constants are finite on the compact
coordinate interval. Multiplication by gamma_i<=1 preserves convergence.
Choose eta sufficiently small and then the largest required degree over the
finite node/fiber list. Atomic target quotients can be represented by constant
coefficients. Every finite polynomial has a finite Chebyshev or Bernstein
coefficient expansion and consequently a global frozen envelope from section
4. Set r_L=0. This proves the assertion. No sampled training outcome is used.

The theorem directly covers the cap-one EMPTY/OTHER/selected-coordinate
benchmark projection. OTHER may aggregate multiple native keys only because
the zero-BASE reference and selected observation make their target likelihood
identical and independent of OTHER coordinates. Such a symmetry argument is
required before aggregation; arbitrary keys cannot simply share a fitted
coefficient. Higher-dimensional event configurations require a corresponding
multivariate, permutation-compatible construction and proof. They are not
covered by the one-dimensional theorem or by a learned metadata compression.

For an actual continuum of observation values, contexts or times, finite-list
coverage is insufficient. A uniform extension would require compact domains,
joint mixed regularity and an expandable basis in those variables too. For
time alone, the continuous-reference assumption in (4), polynomial
approximation at sufficiently fine fixed knots, and convex interpolation of
the quotient give uniform coordinate-C^2 approximation by uniform continuity.
This mathematical existence construction does not refine the *training path*
grid or identify the existing eight-node numerical target between nodes.

## 6. No time interpolation or sampler integration is selected

The controlled sieve evaluates only the original macro nodes. Its active
quotients q_theta,i are independently represented; the terminal residual is
zero by definition. The terminal quotient is not inferred to be zero from
that residual identity. In particular, setting a zero quotient at the terminal
and linearly interpolating to it could inadvertently impose quadratic residual
decay in the last interval. This experiment avoids that assumption entirely:
no between-node evaluation or interpolation operation is provided by this
comparison. The primitive represents one remaining-time coefficient vector;
the comparison constructs and evaluates it only at the fixed macro nodes.

Nodewise oracle accuracy does not prove accuracy at Heun predictor stages or
midpoint jump stages. Nor does plugging the exact node likelihood into the
existing coefficient-tilted split sampler implement the normalized numerical
Doob transition. That transition is K_i(x,dy)h_{i+1}(y)/h_i(x); changing drift
and jump coefficients is a separate approximation. Neither the capacity
theorem nor a good supervised fit closes that algorithmic gap.

## 7. Controlled likelihood/score comparison

The next comparison should be labeled **oracle-supervised approximation**, not
another run of the archived BCE learner. Its purpose is to test whether the
formulation can recover a known correction and score, not to demonstrate
learning from the original paired observations or a sampling advantage.

Hold fixed the two original scenarios, observation values, type weights,
macro-grid, baselines, independent numerical target and acceptance tolerances.
The smooth coordinate map (6) and degrees 16, 32, 64 are fixed. Declare the
coordinate fitting points, distinct evaluation points and solver choices before
examining new fitted errors. There is no time extension. Keep
continuous-reference discrepancy separate.
An implementation should record the target-law identity, basis, gate,
coefficients and derived envelope; it should not reuse the archived model's
checkpoint format or its 0.25 sampling bound.

For a fixed basis the canonical residual value and derivative are linear in
the coefficients. This permits a transparent least-squares control. Two
prospectively fixed objectives are

\[
J_0=\operatorname{mean}\big[(r_\theta-d)^2\big],\qquad
J_1=J_0+\ell^2\operatorname{mean}
 \big[(\partial_z r_\theta-\partial_z d)^2\big],           \tag{9}
\]

where the coordinate scale ell and the respective measures/weights are
declared, not selected after viewing results. Fit the physical residual and
score errors in (9), not a differently weighted quotient error merely because
the parameterization uses q. Include atomic value constraints; atomic states
do not supply fictitious coordinate derivatives. An analytic derivative
design matrix and a declared rank-aware linear solver avoid an unnecessary
stochastic optimizer in this capacity control. Any ridge strength, coefficient
constraint or numerical rank threshold changes the approximation procedure
and must be fixed and reported.

Report both objectives' out-of-fit value contrasts, canonical values, selected
scores, OTHER spurious scores and Hessians at every fixed node, plus terminal
identity, degree, coefficient envelope and conditioning/rank diagnostics.
The Hessian can remain a held-out diagnostic rather than a fitted quantity.
Report all declared degrees and checkpoints; do not choose the best-looking
one as an unannounced success. A zero-residual baseline is a useful shared
reference. Archived neural outputs may be shown for context, but a change of
basis, objective and solver prevents treating that contrast as an isolated
causal test of the outer tanh.

The old 0.25 amplitude-class obstruction is retained as a proved counterexample
comparison, not a new bounded-coefficient fit relabeled as the old network.
A coefficient bound sufficient to bound a polynomial's output would not in
general be necessary, and would introduce a different constrained class.

The sufficient-capacity theorem is an existence result; finite collocation,
conditioning and a fixed degree can still cause approximation error. The
controlled result can support a mathematically coherent replacement
formulation and identify its local approximation limits. It cannot by itself
establish the general learned conditional law, endpoint accuracy, real-data
performance or a publication-level method advantage.
