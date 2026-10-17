# Gaussian variance reduction: matched-skeleton results

2026-09-13. The fixed local-CPU comparison is complete: **48 routes, 384 node
fits, no retry**. Both label arms use the unchanged learner, target, feature
family, penalties, coefficient box and accuracy tolerances.

## Main finding

Analytically integrating Gaussian suffix noise improved all three route-level
RMS errors in **24/24 paired comparisons**. Averaging the paired relative
reductions gives **42.8% for log-likelihood values, 43.1% for scores and 41.0%
for Hessians**. All 24 pairs also improve the shared independent validation
risk. These are descriptive outcomes across the fixed scenarios/seeds, not a
general superiority claim or a new theorem about nonlinear fitted estimators.

**No route meets all of the original accuracy tolerances.** This completes
the variance-control derivation and controlled experiment, not derivative
qualification, full-learner replacement or sampler integration.

## What was changed, and what was not

The new raw control and RB candidate use identical marked jump skeletons and
input coordinates. The candidate replaces Gaussian terminal-coordinate noise
by its conditional expectation using the same numerical Heun half-step law.
It retains birth/death and mark-selection randomness. The paired raw stream
is new; the earlier archived raw fits remain unchanged and are not silently
relabelled as this control.

This is classical conditional Monte Carlo, specialized and proved for the
current linear-Gaussian, zero-BASE, cap-one submodel. It does not automatically
extend to coordinate-dependent jump rates or nonlinear neural BASE dynamics.
See the [complete derivation](LOCALIZED_VARIANCE_REDUCTION_FORMULATION.md) and
[prospective protocol](LOCALIZED_VARIANCE_REDUCTION_PROTOCOL.md).

No backward numerical likelihood or derivative was supplied during fitting.
All 384 fits were frozen before the independent target was queried. All
settings and outcomes, including node-level reversals, remain in the report.

## Errors at the fixed budgets

Each table entry is the mean of the three route RMS errors, raw → RB. Each
route RMS pools the eight active macro nodes and 256 continuous probes.
“Reference” is `(theta,y)=(0.8,0.7)`; “higher pressure” is `(2.5,1.4)`.
G+R denotes association-aware guide plus residual; DIR is the direct baseline.

| Scenario | Method | Suffixes/node | Value RMS | Score RMS | Hessian RMS |
| --- | --- | ---: | ---: | ---: | ---: |
| Reference | G+R | 1,024 | .26805 → .16067 | .72151 → .39825 | 3.35410 → 1.89197 |
| Reference | G+R | 8,192 | .08842 → .05284 | .24998 → .14606 | 1.16912 → .68042 |
| Reference | DIR | 1,024 | .27147 → .16252 | .74196 → .41619 | 3.45023 → 1.99705 |
| Reference | DIR | 8,192 | .09357 → .06060 | .27914 → .19083 | 1.31253 → .92175 |
| Higher pressure | G+R | 1,024 | .34867 → .16372 | .82434 → .40219 | 3.47427 → 1.84236 |
| Higher pressure | G+R | 8,192 | .10570 → .05899 | .28571 → .14640 | 1.32930 → .68691 |
| Higher pressure | DIR | 1,024 | .35089 → .16690 | .83813 → .43144 | 3.57314 → 2.03053 |
| Higher pressure | DIR | 8,192 | .11344 → .06876 | .32424 → .20802 | 1.52939 → 1.03424 |

Across individual route pairs, RB/raw RMS ratios range from .4551 to .7503
for values, .4500 to .7209 for scores, and .4779 to .7469 for Hessians.
The unchanged tolerances remain value `(2e-6,2e-5)`, score `(2e-5,2e-4)` and
Hessian `(1e-4,1e-3)`, absolute/relative respectively. This improvement is not
close enough to substitute for those acceptance tests.

The aggregate result is not uniform over time. RB improves nodewise RMS in
188/192 value comparisons, 186/192 score comparisons and 188/192 Hessian
comparisons. All six score reversals occur at the last active node, `u=7/8`.
One score reversal is .21052 → .24349 (higher-pressure DIR, seed 11,
8,192 suffixes); the largest relative Hessian reversal is .96528 → 1.13952
(higher-pressure DIR, seed 47, 8,192 suffixes). Shared RB validation risk
improves at 186/192 nodes despite improving in all aggregate route pairs.

Comparison with guide-only remains essential. RB G+R improves value RMS in
12/12 routes and score RMS in 6/12 routes (the six larger-budget routes), but
**Hessian RMS in 0/12**. At 8,192 suffixes, reference-scenario mean G+R score
and Hessian RMS are .14606 and .68042 versus guide-only .17730 and .21177.
In the higher-pressure scenario they are .14640 and .68691 versus .29428 and
.39164. Thus reduced label noise has not established a useful curvature
correction over the guide. RB G+R beats RB DIR in all three aggregate RMS
quantities in the 12 matched cases; this is descriptive and does not override
the failed accuracy checks or establish general superiority.

## Mechanism and bounds

On the 96 fixed scenario/seed/node/budget data problems, RB label MSE against
the independently computed conditional mean is smaller in **96/96**. Mean
RB/raw MSE ratio is .3404 (range .2152–.4866). This measures error at the saved
design inputs, not a within-input repeated-sample variance estimate.

The realized empirical fitting-gradient noise norm is smaller in **89/96**,
with **seven reversals retained**. Its RB/raw ratio ranges .2458–1.7221.
This does not contradict the proved PSD covariance reduction: a guarantee
about covariance does not order every realized random vector or nonlinear fit.
The analytic conditional variance removed per label averages .001265–.005845
over these data problems; the trace of the estimated removed gradient
covariance ranges 6.2125e-7–2.8547e-5. These are not new training labels.

The derivation proves an unchanged-target identity, a PSD reduction in the
label-induced gradient covariance, and global strong-convexity bounds on the
noise-induced coefficient and derivative response. The variance-sensitive
bound improves under RB; the reported conservative known-range Hoeffding bound
is deliberately shared by both arms. Its RMS response bounds are **16.6–19.8
for values, 50.0–59.6 for scores, 298–355 for Hessians**: mathematically valid
in the stated ideal-arithmetic setting, but **vacuous relative to the required
accuracy**. Float evaluations are not interval-certified guarantees.

Those bounds compare ideal label-noisy fits with the ideal same-design
conditional-mean fit. Optimization, empirical-design, regularization and
fixed-family projection errors remain separate. In particular, the preceding
[bias diagnosis](LOCALIZED_ERROR_DECOMPOSITION_RESULTS.md) is not erased by
changing the label estimator. No total score-error guarantee is claimed.

All 384 solvers report success; the largest projected gradient is
9.96784e-8, the largest iteration count is 39, no coefficient hits its box,
and the largest physical coefficient envelope is 3.65526. Conservative
box-gap/ridge coefficient-distance estimates range 1.728–5.185 and are also
loose; success flags are not substituted for tighter numerical certificates.

## Computational work

Both arms share 589,824 distinct training/validation suffixes, 579,311
uniformization proposals, 385,298 accepted birth/death events, 121,631
selected-key births, and 2,452,916 active Heun half-step positions. Prefix
counts for each budget are saved and shared exactly. Methods and nested
budgets reuse labels; their reuse is not counted as new simulation work.

The paired pass also performs 2,574,547 raw Gaussian draws, conditional moment
updates and 264,614 positive-variance Gaussian channel convolutions. The full
ledger counts the extra moment helper's initialization and second-moment
arithmetic rather than hiding it. Joint paired label generation took about
0.325 seconds in this execution. The complete primary runner took 16.04
seconds including fitting, target diagnostics, serialization callbacks and
other host work (final report serialization is outside that recorded interval).

RAW uses 5,301 solver iterations and 5,916 objective/gradient evaluations;
RB uses 5,203 and 5,810. Recorded fit times are .882 and .885 seconds. These
small wall times are implementation observations, not controlled benchmarks.
**The match is stochastic-event work, not equal total FLOPs or runtime.**
No standalone RB speedup or variance-per-second advantage is established by
joint paired generation. No GPU, cloud job, real data or download was used.

## Evidence and reproduction

Primary report:
`research/fixtures/continuous_localized_variance_reduction_cpu_2026_09_13/report.json`.
SHA-256 `29849c4f18e1df312722d8899d9361d441398a39b9ea094fa9317151e434889f`;
52,678,889 bytes. Protocol SHA-256:
`add4d2b0b537c4d7dde09f0c70847c2c02fcfaa4b5e74560b71df35adfb033a7`.

The [independent arithmetic audit](../research/fixtures/continuous_localized_variance_reduction_independent_review_2026_09_13.json)
passes **100,800 checks**: all 589,824 saved Gaussian-label rows, 384
objective/gradient/box checks, 5,184 evaluation-array readbacks, 96 diagnostic
problems and 24 route pairs. It does not call the new estimator, runner or
optimizer; it recomputes arithmetic from saved terminal summaries and models.
It does not replay jump skeletons or authenticate execution history.

An installed-wheel rerun outside the checkout completes all 384 fits in
15.63 seconds with the same conclusions. The primary environment uses Python
3.11.5 / NumPy 2.4.6 / SciPy 1.17.1; the reader environment uses Python 3.11.5 /
NumPy 2.1.3 / SciPy 1.15.1. All 96 dataset payloads and work ledgers match
exactly. Maximum cross-environment physical value/score/Hessian differences
are 5.23e-10 / 9.06e-10 / 5.22e-9; fitted results are not bitwise identical.
Both environments pass **730 focused tests**, including 68 new estimator
and comparison tests. The four new source/test files also pass the static
undefined-name check. No remote CI result is claimed.

The [combined verification record](../research/fixtures/continuous_localized_variance_reduction_verification_2026_09_13.json)
binds the primary report, audit, reader reproduction and wheel. The
[reader instructions](../REPRODUCING.md#14-matched-skeleton-gaussian-variance-reduction)
provide the portable command, audit and tests. These checks do not alter the
frozen comparison or promote the learner.

## Consequence for the next scientific decision

Conditional Gaussian averaging is a justified variance-control mechanism for
this submodel, and it improves the fixed comparison without changing the
scientific objective. It is **not yet a sufficient derivative-accuracy fix**.
The next focused question is how much remaining error comes from sampled jump
skeletons versus the already measured design/penalty/projection floor. A
prospectively fixed control should settle that before adopting this estimator
in the general learner or claiming a qualified conditional sampler. Do not
relax tolerances, select penalties after viewing target errors, or launch GPU
training to conceal the unresolved statistical issue.
