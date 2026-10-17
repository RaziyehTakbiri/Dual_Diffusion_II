# Residual formulation and controlled likelihood/score comparison

2026-09-13. **Both bounded deliverables are complete: the formulation/proof and
the fixed comparison. The general residual-learning and sampler problem is not
closed.** No old model, observation law, target or acceptance tolerance changed.

## What was established

The new family is `r_i(z)=(1-u_i) sum c[k] T_k(tanh(z/2))`, with a separate
finite coefficient vector for each declared macro node and discrete fiber.
It replaces a fixed amplitude ceiling with expandable finite coefficients.
The [constructive proof](RESIDUAL_CAPACITY_FORMULATION.md) establishes value,
score and Hessian approximation on compact one-dimensional finite-fiber domains
as degree grows. It does not guarantee accuracy at degree 64, arbitrary keys,
unbounded observations, learned BASE, or intermediate sampler stages. The
diagnostic implementation permits degree at most 128; that resource cap is not
an arbitrary-accuracy theorem for the finite implementation.

This comparison fits the independent numerical-grid residual directly. The
previous paired-observation BCE learner is untouched. Exact EMPTY/OTHER
corrections are supplied analytically, while the selected continuous fiber is
fitted. This separates representability and supervised approximation from the
remaining question of learning from random paired observations.

## Execution and preservation

The [prospective protocol](RESIDUAL_CAPACITY_COMPARISON_PROTOCOL.md) fixes two
settings, two baselines, degrees 16/32/64 and two objectives. Training uses 129
collocation coordinates; evaluation uses 256 different coordinates on [-4,4].
All eight active nodes and the exact terminal identity are evaluated.

The first invocation failed during first-route JSON export after eight fits.
Its output is preserved. An export-only repair converted a NumPy boolean to a
Python boolean; the [deviation note](RESIDUAL_CAPACITY_EXPORT_REPAIR.md) discloses
the repeat. No comparison numbers had been inspected, and no numerical choice
changed. This was not an uninterrupted no-retry run.

The repaired invocation completed **24/24 routes and 192/192 continuous fits**
in **0.771 seconds of child comparison time**, within its 300-second deadline.
This excludes process startup, final report serialization, the failed first
invocation and separate verification. It made no stochastic optimizer updates,
endpoint samples, GPU/cloud requests or real-data accesses.

[Full report](../research/fixtures/continuous_residual_capacity_cpu_2026_09_13_export_repair/report.json)
SHA-256: `7821074d779708fd6b58d273f65cea9f028280d8dca5753dda45db52a8bf8d98`.
All 24 route files, all fitted coefficients, singular values, training losses,
raw evaluation arrays and baseline comparisons are retained alongside it.
The numerical protocol hash is
`e57b2d865db4dae69ee3a4e44905a271457abad37792233dcb45e45f7264a768`.

## Results without selecting a winner

A denotes `(theta,y)=(0.8,0.7)`; B denotes `(2.5,1.4)`.
V fits values only; VS fits values plus coordinate scores with fixed weight 1.
Each error below is a maximum over **2,048 active continuous-fiber probes**,
not a posterior-weighted error, confidence interval or global bound.

The degree-64 results show the remaining limits most clearly. All lower-degree
outcomes remain in the full report; no best-degree model is promoted.

| Setting / baseline / objective | Max log-value error | Max score error | Max Hessian error | Score failures | Hessian failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| A / G+R / V | 1.28e-7 | 5.66e-6 | 3.51e-4 | 0 | 2 |
| A / G+R / VS | 1.56e-7 | 3.26e-6 | 1.06e-4 | 0 | 1 |
| A / DIR / V | 1.53e-6 | 4.70e-5 | 2.35e-3 | 9 | 356 |
| A / DIR / VS | 1.73e-6 | 3.98e-5 | 9.38e-4 | 0 | 333 |
| B / G+R / V | 5.21e-6 | 6.02e-4 | 2.93e-2 | 8 | 88 |
| B / G+R / VS | 7.18e-6 | 1.26e-4 | 9.82e-3 | 4 | 85 |
| B / DIR / V | 2.93e-5 | 2.11e-3 | 1.23e-1 | 1275 | 1865 |
| B / DIR / VS | 3.67e-5 | 6.90e-4 | 4.37e-2 | 1163 | 1811 |

Failures use the previously declared numeric values, applied here as new
**deterministic approximation checks**: `abs(error) <= atol+rtol*abs(target)`.
They are not GPU-parity checks. All eight degree-64 value comparisons pass
this mixed absolute/relative rule. Every one of the 24 routes has at least one
Hessian failure; none passes all value/score/Hessian checks together.

At degree 64, VS lowers the maximum score and Hessian errors relative to V in
all four setting/baseline combinations, while increasing the maximum value
error. This is the expected kind of tradeoff to report, not a claim that VS
dominates at every degree or point. For VS, coordinate-score RMS falls from the
uncorrected baseline to the fitted potential as follows:

| Setting / baseline | Baseline score RMS | Degree-64 VS score RMS |
| --- | ---: | ---: |
| A / G+R | 0.1773 | 3.95e-7 |
| A / DIR | 1.1909 | 1.17e-5 |
| B / G+R | 0.2943 | 1.42e-5 |
| B / DIR | 1.4038 | 2.04e-4 |

These are manufactured fixed-observation oracle controls, not a causal ablation
of the old outer tanh: the basis, supervision and solver all differ from the
archived neural fits. They show that substantial correction is representable
and fit-able in this richer class. They do not show that the old stochastic
learning gap has been solved.

## Numerical and sampling limitations

All 192 systems retain full column rank at the predeclared `1e-12` cutoff.
The largest equilibrated condition number for degree-64 VS is about **1.29e6**.
Full rank is not a guarantee of a well-conditioned or stable approximation.

The largest continuous-fiber coefficient envelope reaches **532.67** for
degree-64 V in setting B/DIR (415.65 for VS). These finite real-arithmetic
envelopes remove the fixed-cap obstruction but could make generic rejection
hopelessly inefficient. They exclude the separately recorded atomic constants
and are not outward-rounded floating-point sampler certificates. No sampler
uses these fitted coefficients.

The independently computed continuous-reference/grid discrepancy is recorded
separately. On this new probe roster its maximum log-value/score/Hessian
differences are approximately `(3.36e-4,4.03e-4,1.39e-3)` for A and
`(4.15e-4,5.19e-4,1.83e-3)` for B. These are finite-query observations and are
not folded into fitting error against the grid target. Different query rosters
explain why these maxima differ from the previous five-coordinate diagnosis.

## Verification and next step

The focused development regression passes **390 tests**. The new primitive and
fit layer account for **96 tests**, including independent derivative formulas,
manufactured-function recovery, objective weighting, disjoint evaluation points,
strict export and preservation. The reader wheel is verified separately outside
the checkout; see [the verification record](../research/fixtures/continuous_residual_capacity_verification_2026_09_13.json)
and [independent result audit](../research/fixtures/continuous_residual_capacity_independent_review_2026_09_13.json).

The next local scientific step is to control derivative accuracy and envelope
growth with a localized smooth residual representation, using the same target
and fixed checks. That must be a newly declared comparison, not retrospective
tuning of this one. Afterward, connect a justified residual to the paired-data
learner and an explicit conditional-transition/interpolation contract. Do not
launch another GPU check or claim posterior recovery based on these results.
