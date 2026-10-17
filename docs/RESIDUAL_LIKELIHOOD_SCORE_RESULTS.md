# Residual-learning gap: completed likelihood/score diagnosis

Date: 2026-09-13. **The bounded diagnosis is complete; the model is not repaired.**

We found a concrete restriction in the current benchmark hypothesis class,
and reproduced the original fitted networks to examine its practical effect.
This is scientific model diagnosis, not a Databricks/environment qualification.
The [derivation](RESIDUAL_LIKELIHOOD_SCORE_ANALYSIS.md) proves the capacity
obstruction and identifies the correct conditional classifier target.

## What was actually done

The new independent oracle evaluates the ideal zero-BASE numerical-grid
likelihood, score, Hessian, evidence and Gaussian-mixture laws analytically.
It does not call the native guide, learner or sampler. This separates the
continuous reference target from the training grid's own target.

All **12 original fits** were reconstructed with their unchanged settings:
32 updates per fit, two pairs per update, and the original validation pairs.
All **60 replay checks** passed: each initial and final parameter digest,
population identity, complete update record sequence and validation-loss curve
matched the archived result. All four fixed checkpoints (0/8/16/32) were
inspected. No checkpoint was selected.

The fixed [protocol](RESIDUAL_LIKELIHOOD_SCORE_DIAGNOSTIC_PROTOCOL.md) was written
before these replays, but after the earlier scientific result: this is a
post-outcome explanatory analysis, not a prospectively powered hypothesis test.
It used one CPU process/thread and completed in **173.49 seconds** under its
1,200-second supervisor limit. It performed 384 replayed optimizer updates,
2,304 training/validation BASE paths and 5,184 fixed query rows, with **zero new
conditional endpoint draws**. The old results were neither overwritten nor
relabeled. Models, loss, gate, optimizer and acceptance tolerances are unchanged.

Full [report](../research/fixtures/continuous_residual_diagnostic_cpu_2026_09_13/report.json),
[derived summary](../research/fixtures/continuous_residual_diagnostic_summary_2026_09_13.json)
and [verification](../research/fixtures/continuous_residual_diagnostic_verification_2026_09_13.json).
Report SHA-256:
`c1ea8e051f23c214b1d3faa81116e9149c9f954051f70038159951b18ea2f0c5`.

## 1. The current residual class cannot represent the target

The inherited fixture fixes B=0.25 and
`r(u,x,a) = (1-u) * B * tanh(raw/B)`.
Thus the residual contrast between any two states is at most 0.5(1-u).
An observation-only nuisance or another state-independent normalization cannot
increase this contrast.

For a target-minus-baseline correction d, any such residual incurs at least

\[
\frac12\left[\max_{x\in S}d(x)-\min_{x\in S}d(x)-0.5(1-u)\right]_+
\]

maximum log-potential error on the fixed query set S, even after the best
state-independent shift. This is a necessary-condition lower bound, not a
claim that the network attains it.

The following witnesses use the **numerical training-grid target**, not just
the distinct continuous-time target:

| Setting | Method | Active nodes with an obstruction | Largest finite-query error floor |
| --- | --- | ---: | ---: |
| A: theta=0.8, y=0.7 | Guide + residual | 7/8 | 0.226686 |
| A | Direct conditioner | 8/8 | 1.019283 |
| B: theta=2.5, y=1.4 | Guide + residual | 8/8 | 0.505769 |
| B | Direct conditioner | 8/8 | 1.782302 |

For example, at u=0.75, the guide residual needs state variation 0.578373
in A and 1.136538 in B, but permits only 0.125. Additional optimization within
this class cannot remove that obstruction, although it could still improve
some errors within the class.

These floating-point evaluations have large violation margins; they are not
interval-certified global bounds. They use E, an atomic OTHER key, and five
coordinates on each of the selected/OTHER continuous fibers. The separate
proof appendix explicitly labels its denser 21-coordinate analytic witnesses.
Neither roster estimates endpoint TV or bounds the score by amplitude.

## 2. Lower classifier loss did not translate into substantial score correction

The relevant score here is the derivative of the **conditional likelihood**
with respect to the current latent coordinate, not a derivative of the
observation and not the entire marginal posterior score.

The table reports RMS error against the numerical-grid score over the **40
unweighted selected-coordinate probes** (eight active nodes times five
coordinates). It is not an expectation under the posterior. Final ranges
include all three seeds; no uncertainty or superiority claim is attached.

| Setting | Method | Zero-residual baseline RMS | Final learned RMS range |
| --- | --- | ---: | ---: |
| A | Guide + residual | 0.183616 | 0.183502–0.183616 |
| A | Direct conditioner | 1.439815 | 1.439689–1.439863 |
| B | Guide + residual | 0.296830 | 0.296828–0.297841 |
| B | Direct conditioner | 1.262195 | 1.262195–1.269743 |

Every final held-out paired loss was lower than its step-0 value. Nevertheless:

- Five of twelve final fits placed **all 96 active probes** at at least 99% of
  their allowed residual amplitude; another placed 90/96 there. The 99% cutoff
  is a **post-hoc descriptive summary**, not an acceptance criterion.
- In A, guide-plus-residual seeds 1201 and 1202 had exactly zero residual
  coordinate gradients on these probes. Their maximum within-time residual
  variations were only 8.57e-8 and 4.47e-7. A nearly state-constant offset
  cannot materially change the probed physical score or state ratios.
- Other fits were not completely saturated. Their state-relative errors
  sometimes improved and sometimes worsened; the diagnosis does not say that
  every fit behaves identically or that all error comes from saturation.
- The observation-only nuisance changed too. It participates in classification
  but is excluded from physical sampling. Nuisance movement and residual
  saturation are measured; attributing a precise fraction of the loss reduction to either
  requires an additional controlled decomposition, which was not performed.

Actual random initialization is also recorded separately from a zero residual:
guide-only is not literally the step-0 neural model.

## 3. The training objective and observation coverage explain the diagnostic choice

The balanced joint/product classifier has the correct population target
`log h_grid(x,a) - log m_grid(a)`. The shared-path construction gives a
time-independent observation marginal, as required by the observation-only
nuisance. We did not find a density-ratio construction error in this step.

But the training risk averages over the entire random observation channel.
The endpoint experiment fixes one selected-key observation. In the actual
replayed records, only **4–9 of 128 training observations** and **1–3 of 64
held-out observations** per fit contained that key within y +/- 0.5.
The window was fixed to one observation-noise standard deviation. These are
descriptive counts, not a proof of insufficient sample size.

Both methods used identical observation streams within each scenario/seed pair:
there are six distinct streams, not twelve independent coverage replications.
An improved global classifier loss does not establish a good derivative or
conditional law at the benchmark's fixed observation.

## 4. Numerical target mismatch is separately measurable

Over the same finite probes, maximum continuous-versus-grid discrepancy was:

| Setting | EMPTY-centered log-likelihood | Coordinate score | Coordinate Hessian |
| --- | ---: | ---: | ---: |
| A | 0.000333 | 0.000394 | 0.000893 |
| B | 0.000308 | 0.000386 | 0.001142 |

These local differences are much smaller than the measured residual-score
errors and capacity violations. Thus a target-definition difference alone does
not explain away the diagnosed restriction. This does **not** prove numerical
integration has negligible endpoint impact.

The new oracle describes macro-node conditional likelihoods for ideal random
draws and real-arithmetic split/Heun updates. The current mixed conditional
sampler still tilts drift and jump coefficients; it does not implement the
normalized Doob transition of that numerical grid. Midpoint-stage interpolation,
learned BASE, general caps, finite-RNG/refusal effects and end-to-end posterior
error remain open.

## Conclusion and next scientific step

The immediate issue is **a restricted and often saturated residual class,
together with a global classifier loss that has not delivered the required
state-dependent score correction**. We have a mathematically explicit target
and a reproducible way to examine that gap; we have not demonstrated a remedy.

The next step is to derive a capacity-sufficient residual parameterization and
a justified likelihood/score approximation contract, then predeclare a small
controlled comparison against these independent targets. Merely raising the
constant bound is not yet a justified fix: that bound also controls rejection
envelopes and can increase sampler cost. A valid tighter frozen-network bound
and the observation-dependent/global-support assumptions need consideration.
No new amplitude, regularizer, observation reweighting or training budget was
selected in this diagnostic turn. Full training or another GPU check is not
the next prerequisite.

Verification: **294 focused development tests pass**, including common-grid
and multiseed regressions; **107 tests pass against the installed wheel outside
the checkout** in the ordinary reader environment. The 107 comprise 82 new
grid-target tests and 25 new diagnostic tests. The exact historical-fit replay
uses the original numerical versions; the independent target/tests do not
impose that historical environment on ordinary readers.
