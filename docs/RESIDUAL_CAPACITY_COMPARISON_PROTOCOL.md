# Prospective residual-capacity comparison

Declared 2026-09-13, before running the new fits. This is a deterministic,
oracle-supervised approximation experiment, not a rerun of the old BCE learner.
The old model, results, scientific target and acceptance tolerances are unchanged.
See [the formulation/proof](RESIDUAL_CAPACITY_FORMULATION.md).

## Fixed design

- Same zero-BASE cap-one process and two joint settings as the archived diagnosis:
  `(theta,y)=(0.8,0.7)` and `(2.5,1.4)`, selected-key mass `393217/524288`,
  death and continuous rates 1, horizon 1, observation SD 0.5, contamination 0.1.
- Same numerical-grid target: independent likelihood under the frozen split
  jump/Heun macro kernel at `u=0,1/8,...,1`. No replacement by the continuous law.
- G+R baseline is the independent uncapped remaining-time likelihood; DIR is
  the terminal observation likelihood. All use raw observation densities;
  the common reference-density factor cancels from residuals and derivatives.
- Separate expansions for each of the eight active nodes and each discrete
  projected fiber. EMPTY/OTHER residual constants are computed exactly from
  the oracle, not learned. CONTINUOUS uses
  `r(u,z)=(1-u) sum c[k] T_k(tanh(z/2))`. Terminal residual is exactly zero.
  No intermediate-time interpolation or sampler connection is included.
- All degrees **16, 32, 64**, both baselines and both objectives are reported:
  24 routes, 192 continuous fits. No winner is selected using evaluation errors.
- Training coordinates: 129 Chebyshev roots in
  `s in [-tanh(2),tanh(2)]`, mapped by `z=2*atanh(s)`.
  Evaluation coordinates: 256 equally spaced points including -4 and 4.
  They are checked to be separated by more than `1e-12`. These are manufactured
  collocation/probe sets, not independent real observations or statistical data.
- Objective V is mean squared residual-value error. Objective VS adds mean
  squared residual-coordinate-score error with weight **1.0**. Coordinates are
  the benchmark's standardized latent units; equivalently the derivative length
  scale is one coordinate unit. Hessians are evaluated but never supervised.
- Deterministic float64 linear least squares, column 2-norm equilibration,
  relative singular-value cutoff `1e-12`, no ridge, optimization iterations,
  stochastic updates, data-dependent degree changes or retries. All ranks,
  singular values, condition estimates and frozen coefficient l1 bounds are
  recorded. A rank-truncated fit is disclosed, not silently called full rank.

## Comparisons and interpretation

At every evaluation coordinate and node report baseline and fitted physical
log likelihood, likelihood-coordinate score and Hessian. Also report the
EMPTY-centered potential, relative likelihood error and oriented E-to-C log
likelihood-ratio errors. The conditional sampler tilts its jump rate by the
full likelihood ratio, not its square root. These are algebraic contrasts,
not proof of normalized conditional transitions or a sampler execution.
Report the old amplitude class's gauge-independent necessary approximation
error floor on the same finite evaluation roster including EMPTY and OTHER.
It is a structural lower bound, not an optimized old-model control.

For pointwise approximation summaries only, retain the existing numeric values:
log value `(atol,rtol)=(2e-6,2e-5)`, score `(2e-5,2e-4)`, Hessian
`(1e-4,1e-3)`, with threshold `atol+rtol*abs(target)`. These are newly labeled
approximation checks, **not** a CUDA parity pass or an endpoint-law guarantee.
Report maximum and RMS errors as well as all failures. Compute the continuous
reference versus numerical-grid discrepancy separately, never count it as
residual fit error. No unchanged scientific acceptance threshold is relaxed.

The theorem proves existence as degree grows; it does not guarantee that one of
these three finite degrees or this finite collocation solver reaches any given
tolerance. Success would show that the declared oracle correction is
approximable by this richer family, not that random-observation BCE can learn it
with the archived budget. No supervised oracle labels would be assumed available
for a general learned BASE or real data.

## Bounds and preservation

One local CPU child, one numerical thread, 300-second parent deadline, no GPU,
cloud, download, endpoint sampling or real-data access. Write protocol before
fits, then all routes and a completion report to a new output directory. Preserve
partial output on failure; no overwrite or retry. Record source and protocol
hashes and actual numerical versions. Direct Python API use has only its supplied
soft check callback. The coefficient bound is real arithmetic only and is not a
floating-point-safe rejection/thinning envelope. Large bounds can make rejection
impractical even when the approximation is accurate. All prior artifacts remain
historical and unchanged.
