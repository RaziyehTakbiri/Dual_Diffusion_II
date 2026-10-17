# Localized residual: curvature control and forward-label learnability

2026-09-13. Both predeclared local CPU experiments completed without retries.
They answer different questions:

- **Exact-input representation:** the fixed seven-point score-differentiation
  control passes every declared value, score and Hessian check in all four cases,
  without using oracle Hessian labels to construct the residual.
- **Learning from simulated labels:** all 24 fitted routes improve mean held-out
  likelihood risk relative to their own zero-residual baseline, but **0/24 routes
  pass all fixed value/score/Hessian tolerances**. Derivative accuracy remains
  unresolved for this statistical learner.

Neither result qualifies the original amortized BCE learner, a general
mixed-domain model, or a conditional sampler. The experiments use manufactured
cap-one, zero-BASE processes; they are not PhysioNet or Retail data results.

## Common setting and interpretation

A denotes `(theta,y)=(0.8,0.7)` and B denotes `(2.5,1.4)`. Both retain the
selected-key probability `393217/524288`, observation SD 0.5, contamination 0.1,
continuous/death rates one, and the common macro grid `0,1/8,...,1`.
The target is the independent **numerical-grid likelihood**, not the
continuous-time likelihood. The two fixed offsets remain:

- **G+R:** the uncapped propagated association log likelihood;
- **DIR:** the terminal observation log likelihood.

All quantities use the same raw observation-density convention. For continuous
states, the reported errors cover 256 fixed coordinates on `[-4,4]` at each of
eight active nodes: **2,048 probes per route per quantity**. RMS means the square
root of the mean squared error over these equally weighted probes. It is not a
posterior-weighted error, empirical total variation, or uniform-domain certificate.
Atomic states and the terminal are reported separately in the raw records.

The unchanged pointwise rule is `abs(error) <= atol + rtol*abs(target)`:

| Quantity | Absolute tolerance | Relative tolerance |
| --- | ---: | ---: |
| Log likelihood | 2e-6 | 2e-5 |
| Coordinate score | 2e-5 | 2e-4 |
| Coordinate Hessian | 1e-4 | 1e-3 |

These are diagnostic approximation thresholds, not finite-sample guarantees.
No threshold, target, baseline or evaluation roster was tuned after either run.

## 1. One fixed seven-point curvature control

The [FD7 protocol](LOCALIZED_CURVATURE_PROTOCOL.md) fixed 256 core cells on
`[-4.5,4.5]`, width-one C² collars, constant outer tails, the previous value/score
labels and evaluation probes. Only the score-derived curvature rule was changed:
differentiate the degree-six interpolant of seven neighboring supplied scores,
using the declared shifted stencils near the boundaries. The construction also
uses the predeclared centered-score summation rule. No Hessian labels were used.

The [derivation](LOCALIZED_CURVATURE_FORMULATION.md) establishes an `O(h^6)`
exact-input curvature-estimation error under its stated smoothness assumptions.
This does **not** raise the underlying quintic Hermite approximation's overall
Hessian order from four to six. Noise and floating-point cancellation require
separate analysis.

All **4 routes, 32 active profiles and 4 terminal-zero profiles** completed.
The comparison took **0.880 seconds** within the child. The archived FD5 and
extra-supervision VSH controls were reevaluated from saved physical arrays, not
refitted. The following maxima use all 2,048 active probes in each row.

| Setting / offset | Construction | Max log-value error | Max score error | Max Hessian error | Failures V/S/H |
| --- | --- | ---: | ---: | ---: | ---: |
| A / G+R | Archived FD5 | 1.91e-9 | 1.32e-7 | 2.44e-5 | 0 / 0 / 0 |
| A / G+R | New FD7 | 1.48e-11 | 1.68e-9 | 3.48e-7 | 0 / 0 / 0 |
| A / G+R | Archived VSH | 4.17e-11 | 3.67e-9 | 8.09e-7 | 0 / 0 / 0 |
| A / DIR | Archived FD5 | 1.21e-8 | 1.64e-6 | 4.72e-4 | 0 / 0 / 16 |
| A / DIR | New FD7 | 2.93e-10 | 3.39e-8 | 1.42e-5 | 0 / 0 / 0 |
| A / DIR | Archived VSH | 2.54e-10 | 4.06e-8 | 6.84e-6 | 0 / 0 / 0 |
| B / G+R | Archived FD5 | 4.49e-9 | 4.14e-7 | 9.25e-5 | 0 / 0 / 0 |
| B / G+R | New FD7 | 4.42e-11 | 4.55e-9 | 1.41e-6 | 0 / 0 / 0 |
| B / G+R | Archived VSH | 9.79e-11 | 1.00e-8 | 1.90e-6 | 0 / 0 / 0 |
| B / DIR | Archived FD5 | 2.49e-8 | 2.53e-6 | 6.90e-4 | 0 / 0 / 28 |
| B / DIR | New FD7 | 5.33e-10 | 6.08e-8 | 2.39e-5 | 0 / 0 / 0 |
| B / DIR | Archived VSH | 5.51e-10 | 6.07e-8 | 1.01e-5 | 0 / 0 / 0 |

FD7 removes the earlier **16 and 28 DIR Hessian failures on this fixed roster**.
It is not uniformly closer than the extra-supervision VSH control, nor does a
finite-probe pass establish accuracy between the probes or outside the core.
The four whole-projected-state real absolute bounds are respectively
`0.601826, 2.082290, 0.937419, 2.917811` for A/G+R, A/DIR, B/G+R and B/DIR.
They include the core, collars, tails and atomic corrections. They are finite
real-arithmetic bounds, not outward-rounded floating-point sampling certificates.

This closes the **declared exact-input FD7 control**, not the broader learning
problem. No further stencil, resolution or fallback was selected from these results.

## 2. Learning from forward-only likelihood labels

The [learnability protocol](LOCALIZED_LEARNABILITY_PROTOCOL.md) was fixed before
fitting, independently of the FD7 outcome. It replaces oracle value/score labels
with one forward suffix per training input and the known terminal observation
density `Y=g_raw(y|X_H)`. The simulator implements the unchanged sequence of Heun
half-step, full capped jump phase, and Heun half-step. Its conditional label mean
is the numerical-grid likelihood. **Forward terminal states were simulated for
these labels; learned conditional endpoint draws were not performed.**

The new model is a smaller statistical family: a quintic B-spline with **32 cells**,
33 tied-edge continuous coefficients and two learned atomic coefficients at each
active node. It is not the 256-cell oracle-jet interpolant. The objective is the
fixed normalized likelihood quasi-risk with physical-coefficient roughness and
ridge penalties. The [formulation](LOCALIZED_LEARNABILITY_FORMULATION.md) proves
the unrestricted unpenalized target and convexity, while explicitly retaining
finite-basis, boundary, regularization and coefficient-box bias.

The run completed the complete roster: two settings × three seeds × two offsets
× two nested label budgets = **24 routes and 192 node fits**. It used:

- **393,216 unique training suffixes**, with 1,024-label prefixes of each
  8,192-label dataset;
- **196,608 independent validation suffixes**, 4,096 per node/setting/seed;
- **589,824 total forward suffixes**, comprising 2,654,208 macro-interval
  executions, 579,801 potential uniformization events, 385,909 accepted
  birth/death events and 2,449,616 continuous half-step updates.

The two methods share identical input/label datasets; validation namespaces are
separate and never select a fit or setting. All **192 fits were frozen before**
the backward numerical target was imported for evaluation. The saved freeze
record binds all 24 frozen routes. The run took **4.035 seconds** within the child.
This includes its in-run dataset/route exports but excludes process startup,
final report serialization and separate verification; it is not general training
throughput or a GPU speed comparison.

### Complete route-level results

`Delta risk` is the mean, over the eight active nodes, of independent validation
quasi-risk minus that route's own zero-residual baseline risk. Negative means
improved observed validation risk. Values are descriptive, not a significance
test; the nodewise raw reports include descriptive stratified standard errors.
The same baseline differs between G+R and DIR, so a more negative change is not
by itself a better final model or a fair cross-method improvement ratio.

| Setting | Seed | Offset | Labels per node | Log-value RMS | Score RMS | Hessian RMS | Delta risk |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| A | 11 | G+R | 1,024 | 0.266146 | 0.693596 | 3.351395 | -0.001320 |
| A | 11 | G+R | 8,192 | 0.118719 | 0.297678 | 1.230955 | -0.003204 |
| A | 11 | DIR | 1,024 | 0.265941 | 0.699045 | 3.417787 | -0.044943 |
| A | 11 | DIR | 8,192 | 0.118987 | 0.312763 | 1.392062 | -0.046832 |
| A | 29 | G+R | 1,024 | 0.241421 | 0.675929 | 3.151184 | -0.001969 |
| A | 29 | G+R | 8,192 | 0.098338 | 0.242952 | 1.174462 | -0.003700 |
| A | 29 | DIR | 1,024 | 0.242933 | 0.682881 | 3.180765 | -0.044791 |
| A | 29 | DIR | 8,192 | 0.103373 | 0.269570 | 1.296330 | -0.046493 |
| A | 47 | G+R | 1,024 | 0.271608 | 0.790001 | 3.847925 | -0.001436 |
| A | 47 | G+R | 8,192 | 0.085753 | 0.253136 | 1.269437 | -0.003603 |
| A | 47 | DIR | 1,024 | 0.271470 | 0.801310 | 3.925187 | -0.045638 |
| A | 47 | DIR | 8,192 | 0.090386 | 0.277424 | 1.383385 | -0.047785 |
| B | 11 | G+R | 1,024 | 0.344449 | 0.853934 | 3.983685 | -0.003373 |
| B | 11 | G+R | 8,192 | 0.103007 | 0.266262 | 1.197762 | -0.006362 |
| B | 11 | DIR | 1,024 | 0.342749 | 0.858288 | 4.030813 | -0.076832 |
| B | 11 | DIR | 8,192 | 0.114259 | 0.326536 | 1.541449 | -0.079773 |
| B | 29 | G+R | 1,024 | 0.346850 | 0.864358 | 3.657943 | -0.003815 |
| B | 29 | G+R | 8,192 | 0.116670 | 0.271819 | 1.218161 | -0.005904 |
| B | 29 | DIR | 1,024 | 0.351381 | 0.886147 | 3.779484 | -0.078222 |
| B | 29 | DIR | 8,192 | 0.121010 | 0.296815 | 1.345216 | -0.080319 |
| B | 47 | G+R | 1,024 | 0.351213 | 0.740015 | 3.317485 | -0.002970 |
| B | 47 | G+R | 8,192 | 0.114808 | 0.285524 | 1.199627 | -0.005748 |
| B | 47 | DIR | 1,024 | 0.353993 | 0.762612 | 3.388745 | -0.080595 |
| B | 47 | DIR | 8,192 | 0.120749 | 0.333949 | 1.495486 | -0.083417 |

Every route improves its mean validation risk. This is **24/24 route means**,
not every individual node: **184/192 nodewise changes** are negative and eight
are positive. The larger budget improves mean validation risk and all three
continuous RMS errors in **all 12 matched setting/seed/offset pairs**. This is
evidence on this complete finite roster, not an asymptotic rate, universal
sample-efficiency claim or adequacy guarantee for other settings.

Nevertheless, **0/24 learned routes pass all continuous approximation checks**.
Depending on the route and quantity, 2,045–2,048 of the 2,048 probes fail the
strict unchanged threshold. Neither a favorable mean loss nor a successful
optimizer flag is a derivative-accuracy pass.

### Baseline context: value learning is not automatically score improvement

The corresponding zero-residual baseline RMS errors are:

| Setting / offset | Log-value RMS | Score RMS | Hessian RMS |
| --- | ---: | ---: | ---: |
| A / G+R | 0.323617 | 0.177296 | 0.211774 |
| A / DIR | 1.019180 | 1.190948 | 2.457381 |
| B / G+R | 0.486729 | 0.294276 | 0.391640 |
| B / DIR | 1.407992 | 1.403807 | 2.790145 |

All 24 learned routes reduce log-value RMS relative to their own baseline.
However, G+R score RMS is worse than its already informative guide in **9/12
routes**, and G+R Hessian RMS is worse in **12/12**. Only the three B/G+R
8,192-label routes improve G+R score RMS. DIR score RMS improves in all 12
routes; its Hessian RMS improves in the six larger-budget routes but not the
six smaller-budget routes. These are descriptive comparisons on the same probes,
not superiority tests between methods.

This exposes the relevant remaining problem: noisy-label likelihood fitting can
improve value prediction while introducing derivative error. The experiment does
not identify how much is caused by label noise, the 32-cell approximation,
endpoint ties, or the fixed regularization. Those mechanisms were not separately
ablated. The earlier exact-input FD7 success cannot be substituted for this
learner's derivative performance.

### Coefficients and optimizer diagnostics

All **192/192 fits returned solver success**, with 22–40 iterations per fit,
5,397 total iterations and 6,018 objective/gradient evaluations. The maximum
projected-gradient magnitude was **2.15303668e-7**, above the configured `1e-7`
gradient stopping threshold. That one fit—B/DIR, seed 29, 8,192 labels, `u=0.25`—
stopped on relative objective reduction instead. The other 191 fit residuals
were below `1e-7`. Thus solver success is reported accurately, not relabeled as
proof of exact minimization.

The observation-derived physical boxes were **7.507232** for A and **8.952688**
for B. No coefficient was on a recorded box boundary. The largest realized
whole-projected-state real absolute residual bound was **3.490098**. The new
observation-derived box is not active in these fits; it avoids the earlier
fixed-ceiling obstruction. This does not rule out finite-basis or regularization
bias, or certify a sampling
envelope. Both atomic corrections were learned from forward labels in this
experiment, unlike the exact atomic corrections in the earlier interpolation
controls. All terminal residuals are exactly zero by construction.

## 3. Scientific conclusion and remaining work

The two results should be kept separate in the manuscript:

1. A localized exact-input residual can meet the fixed likelihood/derivative
   checks with score-only FD7 curvature construction in this four-case benchmark.
2. Forward-only simulation supplies legitimate, non-oracle training labels for
   a bounded convex localized likelihood fit. The complete three-seed comparison
   shows improved held-out likelihood risk and improved errors with more labels.
3. The learned derivatives are still insufficient under the existing tolerances.
   Learning values and representing accurate derivatives are different scientific
   requirements; this experiment does not bridge them automatically.

The next focused question is to separate finite-label derivative variability
from fixed-family and regularization bias under an explicitly stated design.
This report selects no new penalty, spline resolution, sample budget or stencil.
No additional variants were run. A general observation-conditioned learner,
stage-time policy, normalized numerical conditional transitions, tail accuracy,
initializer behavior and floating-point-safe sampler integration remain separate
work. Neither completed experiment promotes the model to full scientific
training or reinterprets an older receipt.

## 4. Records and verification status

Both raw reports preserve all predeclared routes, protocol/source bindings,
construction or fit records and evaluation arrays:

- [FD7 report](../research/fixtures/continuous_localized_curvature_cpu_2026_09_13/report.json):
  SHA-256 `d1e438b8f7b3f189e036f680b50467832bb8557425ee90e8ff830eeaaf269997`;
  protocol `6a304da5e3bbf6d2f3bc19e2184122d803b8a8024997f5c8ebf4ccee5ab76f47`.
- [Learnability report](../research/fixtures/continuous_localized_learnability_cpu_2026_09_13/report.json):
  SHA-256 `d8db24c1c4f2d22069da8ec15640cd9b553dfec5f3ecf87b5f0530069289a692`;
  protocol `c99b27fbd042359f65f54cd7c191a4bdd28e98f62303ad341fcdb8287ee8036e`.
- [Fit freeze barrier](../research/fixtures/continuous_localized_learnability_cpu_2026_09_13/freeze-barrier.json):
  frozen-records digest
  `ccd403105cc28b6391ed8f319faa817d6145217a01cb23b44d072c114193871b`.

The descriptive tables above were recomputed from the saved reports, with no
new fits or scientific runs during this review. The completed
[verification record](../research/fixtures/continuous_curvature_learnability_verification_2026_09_13.json)
records **553 focused tests passed** in each of the development and installed-wheel
reader environments (6.53 and 6.36 seconds respectively). Both full scientific
commands also completed outside the checkout with source `PYTHONPATH` disabled.
The reader used NumPy 2.1.3/SciPy 1.15.1, versus development NumPy 2.4.6/SciPy
1.17.1; both used Python 3.11.5.

The FD7 physical arrays were bitwise identical across these two environments.
All 48 forward-label dataset files were also identical. Learned physical arrays
were not bitwise identical: maximum absolute differences were `2.837e-10` for
log values, `6.019e-10` for scores and `3.618e-9` for Hessians; physical
coefficient differences were at most `4.099e-10`. Both environments retained
192 solver-success flags, all four FD7 passes, and zero learned-route tolerance
passes. This is two-environment reproducibility evidence, not universal platform
support or a remote-CI claim.

The independent [FD7 raw audit](../research/fixtures/continuous_localized_curvature_cpu_2026_09_13/independent_raw_audit.json)
passed, including rational stencils, supplied scores, reconstructed controls,
physical derivatives, archived comparisons and bounds. The independent
[learner audit](../research/fixtures/continuous_localized_learnability_independent_review_2026_09_13.json)
passed **28,970 checks with zero failures**, covering all 48 dataset files and
192 fits, paired data, the freeze barrier, coefficient derivatives, validation
risks, roughness penalties and projected-gradient records. These are in-session
independent code/result reviews, not external peer review. They verify the
reported failures as well as successes and do not confer scientific acceptance.

No GPU, cloud job, real dataset, learned conditional sampling, commit, push or
publication was involved in the two experiments.
