# Paired forward-label variance reduction: prospective protocol

2026-09-13. Frozen before this comparison generates training labels or fits.
This is the authorized next synthetic, local-CPU experiment after the
[finite-data/bias diagnosis](LOCALIZED_ERROR_DECOMPOSITION_RESULTS.md).
It changes a label estimator in a **separate experiment**, not the existing
learner, manuscript objective, archived outcomes, sampling code or release.

## Question and strategy

Can removing Gaussian suffix noise reduce the recorded likelihood, score and
Hessian errors at the same marked-jump simulation budget?

The control simulates raw terminal observation densities. The candidate
integrates all Gaussian birth-coordinate and Heun noise conditional on exactly
the same marked birth/death skeleton. The discrete skeleton remains sampled.
Neither arm receives backward-target likelihood, score or Hessian labels.
The law is the existing zero-BASE cap-one numerical macro-grid submodel;
linear-Gaussian closure is not asserted for a general trained neural BASE.
The [formulation](LOCALIZED_VARIANCE_REDUCTION_FORMULATION.md) states the
conditional-expectation and derivative-error results and their limits.

## Fixed roster

- The same two scenarios: `(theta,y)=(0.8,0.7)` and `(2.5,1.4)`.
- Both unchanged baselines: association-aware guide plus residual, and DIR.
- Seeds 11, 29, 47; nested 1,024 and 8,192 training suffixes per active node.
- The same eight active nodes on `0,1/8,...,1`; terminal residual exactly zero.
- Balanced E/O/C/C input categories and uniform continuous coordinates in
  `[-4.5,4.5]`, using the previous design RNG addresses. These are paired
  mechanism comparisons on familiar scenarios, not unseen confirmatory tests.
- Two arms, 48 routes, 384 node fits, 96 paired training-noise problems.
- 4,096 separate validation suffixes per node/seed/scenario. Both arms use the
  same independent RB validation labels for the primary validation-risk
  comparison; the same raw labels provide a secondary descriptive check.
- 393,216 distinct training skeletons plus 196,608 validation skeletons:
  589,824 total, not multiplied by reused methods, arms or nested budgets.

The label RNG namespace is new: `[20260913,731,scenario,seed,node,split,stream]`,
with stream 0 for jump skeletons and 1 for Gaussian noise. The old labels are
not the paired raw control. Gaussian and skeleton streams are independent
under the ideal IID model; exact finite-PRNG independence is not proved.

## Matched work, explicitly defined

At a given budget, the two arms receive the **identical** number of suffixes,
macro intervals, jump proposals, accepted births/deaths, selected-key births,
and active Heun-update positions. Per-suffix integer counters permit exact
prefix accounting. The paired extractor computes both labels in one pass.
Shared work and joint elapsed time are reported once. Raw Gaussian draws,
conditional mean/variance affine updates and channel convolutions are separate
ledger entries. The raw arm retains the original half-step Gaussian simulation,
not an unreported terminal-normal shortcut.

This is matched stochastic-event work, **not equal FLOPs, random-number count,
wall-clock time, or demonstrated standalone efficiency**. RB may cost more or
less in a standalone implementation. This experiment cannot establish a speedup
from its joint generation timings. All fits have the same maximum work policy;
actual solver iterations/evaluations and fit times are reported, not presumed
equal. The existing zero initialization, L-BFGS-B maxiter 200, maxls 30,
ftol 1e-12 and gtol 1e-7 remain unchanged. No equal-total-runtime claim is made.

## Unchanged statistical problem and evaluation

Keep the 32-cell tied quintic family, 35 physical coefficients, coefficient box
`2 log(M/c)`, raw-density scale M, smoothness 1e-4 and ridge 1e-6. In particular,
do not replace M or the coefficient box by a tighter RB range. That would
change effective regularization or capacity. No validation/oracle tuning,
learning-rate or penalty sweep, adaptive sample budget, or retry is allowed.

Every model is serialized before the independent backward numerical target is
imported or queried. Evaluation then uses the unchanged 256 continuous probes
on `[-4,4]`, both atom values, and exact terminal zero. Report all 24 paired
route differences in value/score/Hessian RMS, all tolerance failure counts,
shared validation-risk differences, solver statuses and coefficient bounds.
The unchanged absolute/relative tolerances are value `(2e-6,2e-5)`, score
`(2e-5,2e-4)`, Hessian `(1e-4,1e-3)`.

After the freeze, the independent target also supplies each training input's
conditional mean for **diagnosis only**: label squared error and realized
empirical fitting-gradient noise. Analytically integrated per-skeleton raw
label variance supplies an unbiased estimate of the removed gradient covariance
matrix. This estimate is not itself an exact population covariance or a
confidence certificate. Three training seeds support descriptive comparisons,
not a population-wide superiority claim. All losses, failures and reversals
are retained; none determines model selection.

## Derivative bounds and nonclaims

The proof separates (i) label and gradient covariance reduction, (ii) a
variance-dependent bound on the ideal coefficient/derivative response, and
(iii) a simultaneous conservative Hoeffding bound using the known label range.
The numerical report uses family failure probability 0.05 over 96 problems
times two arms, 35 coordinates, both signs. Methods share each gradient-noise
event. It uses the unchanged ridge lower curvature bound 1e-6 and the coefficient
box diameter. The range-based bound is shared by both arms and may be vacuous
relative to the acceptance tolerances. No estimated variance is substituted
into a purported confidence guarantee.

These bounds concern exact noisy-label versus same-design conditional-mean
optima. Returned-solver error is separate: report the box first-order gap and
its conservative ridge response estimate. Empirical-design, regularization
and fixed-family projection errors remain additional. Float-evaluated norms
and inequalities are not interval certificates. The experiment does not
qualify a conditional sampler, train the full model, access real data, use a
GPU, launch paid jobs, download packages or replace an installed release.

## Execution and preservation

One fixed run, one numerical thread, 1,200-second child deadline, no retries.
Write protocol and source identities before training. Exclusively create a
new output directory and save paired datasets, frozen fits, a global freeze
barrier, complete evaluated routes and final report. Preserve incomplete output
on failure; no mutation of old evidence. A separate installed-wheel run in the
existing reader environment is a portability check, not another selected seed
or tuned replicate. Independent audit and unit regressions precede completion.
