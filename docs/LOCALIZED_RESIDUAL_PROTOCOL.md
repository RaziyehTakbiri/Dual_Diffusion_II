# Prospective localized residual comparison

2026-09-13, declared before computing the new target-based constructions.
The old models, previous comparisons, scientific target and tolerance values
remain unchanged. This is a local synthetic oracle-approximation experiment,
not learner or sampler integration.

## Fixed representation and arms

Use a piecewise quintic Hermite–Bézier residual in the raw latent coordinate.
At each active macro node, the shared endpoint value, score and curvature define
each local polynomial. The residual is `(1-u)` times the interpolated quotient.
Its global real-arithmetic envelope is the largest absolute Bézier control
coefficient times `(1-u)`, not the sum of global polynomial coefficients.

Both of the following arms are mandatory and reported, without selecting a
replacement after seeing evaluation results:

1. **VS_FINITE_DIFFERENCE (primary):** consume exact residual values and scores
   at fixed knots. Estimate each shared knot curvature by the fixed fourth-order
   five-point derivative of the scores, using one-sided stencils at the first
   two and last two knots. Oracle Hessians are not supplied to construction.
2. **ORACLE_JET_VSH (diagnostic control):** consume exact value, score and Hessian
   at those same knots. This explicitly uses extra supervision; it is not the
   primary arm or an undeclared fallback if the primary fails.

The primary does not consume oracle Hessian labels, although the independent
analytic target may compute value/score/Hessian together internally. Hessians
remain evaluation quantities for that arm. No linear solve, stochastic optimizer,
regularization, hyperparameter search or data-dependent knot placement is used.

## Fixed settings and probes

- Same two zero-BASE, cap-one process settings and fixed observations as the
  previous comparison: `(theta,y)=(0.8,0.7)` and `(2.5,1.4)`, selected-key mass
  `393217/524288`, death/continuous rates 1, horizon 1, SD 0.5, contamination 0.1.
- Same independent **numerical macro-grid** likelihood, `u=0,1/8,...,1`, and the
  same G+R remaining-time uncapped baseline / DIR terminal-observation baseline.
  Raw observation-density conventions are used consistently. The continuous
  reference is computed separately and never substituted for the grid target.
- Uniform core knots on **[-4.5,4.5]**, with **64, 128, 256 cells**: respectively
  65, 129, 257 knot locations. All three resolutions are reported.
- The old **256 equally spaced evaluation coordinates on [-4,4]** are retained
  exactly. Check separation from every construction-knot roster exceeds `1e-12`.
  These are deterministic manufactured probes, not statistical held-out data.
- Fixed collars of width **1** on each side join the core endpoint jets to the
  same endpoint value with zero first/second derivatives at ±5.5, followed by
  constant tails. No oracle-accuracy claim is made for collars or tails.
  The collars are included in global coefficient/value/derivative envelopes.
- EMPTY/OTHER corrections are exact oracle constants, explicitly not learned.
  Whole-projected-state value bounds include those atomic corrections as well
  as the continuous core, collars and tails. Terminal residuals are exact zero.
- No time interpolation or intermediate-stage likelihood is introduced.

There are **24 routes**: two settings × two baselines × two arms × three
resolutions, comprising **192 active continuous profiles** and 24 terminal-zero
controls. Each route uses 2,048 active evaluation points plus 256 terminal points.

## Fixed comparisons and interpretation

Report every resolution's physical log likelihood, coordinate score, Hessian,
relative likelihood error, EMPTY-centered log potential and full E-to-C
log/relative-rate-ratio errors. Reuse the old comparison arithmetic unchanged:

| Quantity | Absolute tolerance | Relative tolerance |
| --- | ---: | ---: |
| Log value | 2e-6 | 2e-5 |
| Coordinate score | 2e-5 | 2e-4 |
| Coordinate Hessian | 1e-4 | 1e-3 |

The pointwise rule is `abs(error) <= atol + rtol*abs(target)`. These remain
deterministic approximation checks, not parity or endpoint-law acceptance.
Report maximum/RMS errors, every failure, knot jet discrepancies, coefficient
range and real-arithmetic derivative envelopes. All terminal identities and
atomic corrections are also checked. No acceptance tolerance is relaxed.

Comparison against the archived Chebyshev results is **descriptive**, not a
basis-only causal test or matched-compute/label-budget comparison. The new design
uses different knots, a wider construction interval, local interpolation instead
of least squares, and a separate extra-supervision control. At 128 cells the
primary uses 129 value/score locations, but they are not the old 129 locations.
Success cannot establish recovery from random paired observations, full mixed
learned-BASE generalization, or sampler accuracy. No successful resolution will
be silently promoted to those roles.

## Execution and preservation

One local CPU child, one numerical thread, 300-second parent deadline; no GPU,
cloud, downloads, real data or endpoint sampling. The portable command records
numeric protocol and source hashes before construction, and saves every route
and complete report in a new output folder. Partial failure output is preserved;
there are no automatic retries or settings changes. A direct API invocation
only has its caller's soft deadline callback. All floating-point output is
checked finite, but coefficient envelopes are **real-arithmetic bounds, not
outward-rounded floating-point rejection/thinning certificates**.
