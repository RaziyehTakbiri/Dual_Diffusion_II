# Localized residual: derivative accuracy and coefficient control

2026-09-13. **The bounded formulation and controlled comparison are complete.**
The new representation greatly reduces derivative error and coefficient bounds.
It does **not** yet pass every primary Hessian check or repair learning from
paired observations. Learner/sampler integration was deliberately not performed.

## Mathematical result and implementation

The residual now has local quintic Hermite–Bézier pieces, shared value/score/
curvature at knots, a linear terminal gate, and C² collars into constant tails.
The [independently reviewed derivation](LOCALIZED_RESIDUAL_FORMULATION.md) proves
core approximation orders **h⁶ for values, h⁵ for scores, h⁴ for Hessians**, under
the stated exact-input C⁶ assumptions. It also proves a mesh-uniform coefficient
envelope: refining the grid does not intrinsically force coefficient growth.

The global real-arithmetic residual bound uses the largest absolute local
Bernstein control, including both collars and atomic corrections. The prototype
is immutable and evaluates analytic derivatives. The proof is one-dimensional,
fixed-observation and finite-node/fiber; it is not a general learned-model theorem.
These bounds are not outward-rounded floating-point sampling certificates.

The primary **VS** construction uses only independent likelihood values and
scores. It estimates shared knot curvatures with fourth-order score differences.
The separately labeled **VSH control** uses exact oracle Hessian labels too.
Its success must not be substituted for primary success.

## Fixed experiment and outcome

The [prospective protocol](LOCALIZED_RESIDUAL_PROTOCOL.md) retained the same
independent numerical-grid likelihood, two scenarios, G+R/DIR baselines,
macro nodes, 256 evaluation coordinates and all tolerance values. Every declared
64/128/256-cell resolution and both supervision arms were run and retained.
There was no retry, resolution selection, endpoint sampling or stochastic fit.

**24/24 routes, 192/192 active profiles and 24 terminal-zero controls completed.**
Child comparison time was **1.177 seconds**, excluding process startup, final
report serialization and separate verification. This is small deterministic
interpolation work, not neural training throughput.

[Full report](../research/fixtures/continuous_localized_residual_cpu_2026_09_13/report.json)
SHA-256: `5cfc1a95284ce1149dd3211799666988b8b0422807affec2961c26264ab4c099`.
Numerical protocol SHA-256:
`de45c892a45e67ccee208bb59077c58fe55e5bed9993fd5f876729db00ccc20e`.
All controls, knot labels, raw evaluation arrays and 24 individual route files
are preserved alongside it.

A is `(theta,y)=(0.8,0.7)`; B is `(2.5,1.4)`. Each row below includes **2,048
active probes**, not a posterior-weighted integral or a uniform error certificate.
Failures are value/score/Hessian counts under the unchanged pointwise rule
`abs(error) <= atol + rtol*abs(target)`.

| Primary VS setting / baseline | Cells | Max score error | Max Hessian error | Failures V/S/H | Whole-profile absolute bound |
| --- | ---: | ---: | ---: | ---: | ---: |
| A / G+R | 64 | 1.14e-4 | 4.64e-3 | 0 / 0 / 57 | 0.602 |
| A / G+R | 128 | 4.75e-6 | 3.04e-4 | 0 / 0 / 0 | 0.602 |
| A / G+R | 256 | 1.32e-7 | 2.44e-5 | 0 / 0 / 0 | 0.602 |
| A / DIR | 64 | 9.96e-4 | 7.33e-2 | 0 / 328 / 891 | 2.083 |
| A / DIR | 128 | 3.88e-5 | 7.58e-3 | 0 / 0 / 373 | 2.082 |
| A / DIR | 256 | 1.64e-6 | 4.72e-4 | 0 / 0 / 16 | 2.082 |
| B / G+R | 64 | 2.83e-4 | 2.15e-2 | 0 / 3 / 116 | 0.937 |
| B / G+R | 128 | 1.18e-5 | 1.50e-3 | 0 / 0 / 0 | 0.937 |
| B / G+R | 256 | 4.14e-7 | 9.25e-5 | 0 / 0 / 0 | 0.937 |
| B / DIR | 64 | 1.40e-3 | 1.40e-1 | 2 / 389 / 913 | 2.919 |
| B / DIR | 128 | 7.19e-5 | 1.08e-2 | 0 / 1 / 370 | 2.918 |
| B / DIR | 256 | 2.53e-6 | 6.90e-4 | 0 / 0 / 28 | 2.918 |

At 256 cells, all four primary likelihood and score checks pass. Maximum log-value
errors are `1.91e-9, 1.21e-8, 4.49e-9, 2.49e-8` for A/G+R, A/DIR, B/G+R,
B/DIR respectively. Both G+R routes pass all three quantities. DIR's remaining
16 and 28 Hessian failures are retained, not hidden by an aggregate pass label.

The VSH control's Hessian failure counts at 64/128/256 cells are:

| Setting / baseline | 64 | 128 | 256 | Max Hessian error at 256 |
| --- | ---: | ---: | ---: | ---: |
| A / G+R | 0 | 0 | 0 | 8.09e-7 |
| A / DIR | 146 | 0 | 0 | 6.84e-6 |
| B / G+R | 0 | 0 | 0 | 1.90e-6 |
| B / DIR | 245 | 1 | 0 | 1.01e-5 |

Every VSH value/score check passes. Overall, **13/24 routes** pass all three
quantities: 4 primary and 9 stronger-supervision controls. Completion is not an
all-primary-tolerances pass. The same-knot VSH comparison isolates curvature
reconstruction as the changed input; it does not show that exact Hessian labels
are available to the eventual paired-data learner.

## What improved, and what remains

The largest whole-profile absolute bound is **2.91851** over all 192 profiles,
including collars/tails and atoms. It stays stable under the declared refinements.
The previous degree-64 score-supervised global expansion reached **415.65**
(value-only reached 532.67), even without atoms. This is a descriptive comparison
of different representations/extensions, not a basis-only causal or matched-label/
compute-budget ablation. Core, knots and interpolation differ; tail target
accuracy is not established for the new constant extension.

At 256 cells, primary B/DIR maximum score error falls from the earlier degree-64
VS `6.90e-4` to `2.53e-6`; Hessian error falls from `4.37e-2` to `6.90e-4`.
The independent continuous-reference versus numerical-grid discrepancy is unchanged
and remains separately reported. Small errors against the numerical-grid target
are not a continuous-time posterior guarantee.

The next focused scientific question is whether a separately declared,
higher-order **score-only** curvature reconstruction removes the remaining DIR
error without changing the target, labels or tolerances. No such extra arm was
run or selected retrospectively here. Before eventual learner integration,
coefficient/jet estimation noise must also be controlled: differentiation can
amplify score noise as the mesh shrinks. Stage-time policy, normalized conditional
transitions, tail approximation and floating-point-safe sampling bounds remain
separate open issues. No new cluster setup is needed for this work.

## Reproduction and verification

The [reader instructions](../REPRODUCING.md#10-localized-smooth-residual-comparison)
provide the installable command. **483 focused development tests pass**, including
93 new primitive/construction tests. An independently built/installed project
wheel passes **324 tests outside the checkout** under the existing reader
NumPy 2.1.3 / SciPy 1.15.1 environment. Its complete 24-route comparison reproduces
all failure counts and every exported physical value/score/Hessian array exactly.
This is observed portability across these two local environments, not a universal
bitwise reproducibility guarantee. No dependency download was needed.

See the [verification record](../research/fixtures/continuous_localized_residual_verification_2026_09_13.json)
and [independent all-route audit](../research/fixtures/continuous_localized_residual_independent_review_2026_09_13.json).
Old sources/results and acceptance tolerances are unchanged. No real data,
GPU/cloud/paid jobs, learner/sampler integration, commit, push or publication
occurred during this step.
