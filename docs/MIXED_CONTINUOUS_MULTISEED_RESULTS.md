# Multi-seed mixed continuous-fiber comparison

The [prospective protocol](MIXED_CONTINUOUS_MULTISEED_PROTOCOL.md) fixes the
scientific choices before the default run. This document records execution,
results and limitations separately; it does not revise that protocol.

**Status: all 22 fixed routes are complete, with an authorized local CPU time
extension.** The first attempt remains recorded as a timeout. The combined
[complete report](../research/fixtures/continuous_multiseed_completion_cpu_2026_09_13/report.json)
preserves its 20 completed routes and adds only the two originally missing
routes. No scientific settings or uncertainty rules changed.

## Reproduce

Use the [ordinary reader installation](../REPRODUCING.md), then:

```sh
python -m heterodiff.experiments.continuous_multiseed_benchmark --inspect
python -m heterodiff.experiments.continuous_multiseed_benchmark --output ./continuous-multiseed-001
```

The output directory must be new under an existing parent. The command uses a
single local CPU child with a 2,400-second deadline, saves its settings first,
then each of 22 complete route records, and finally `report.json`. Reduced
budgets are unit/integration checks only. A failed/partial run is not a
successful comparison; no automatic retry or seed replacement occurs.

## What is compared

Two synthetic settings change count pressure and observation location jointly:
(theta,y)=(0.8,0.7) and (2.5,1.4). The actual mixed conditional learners use
matched initial tensors and paired training laws, three seeds, 32 updates,
two joint/product pairs per update and 512 final draws per fit. Five controls
each use 2,048 draws per setting. All numerical paths use the same eight-step
grid. The BASE is frozen at zero so that an independently computable cap-one
jump/OU Gaussian-mixture posterior remains available.

The primary discrepancy is the largest absolute probability error over three
category indicators and 21 selected-key joint-CDF indicators. It is not TV over
the continuous state space. The protocol supplies finite-roster sampling bounds
conditional on the fitted models, not confidence intervals over unseen training
seeds. Mixture discrepancy and average per-seed discrepancy are both retained.

Controls separate initialization and physical-guide changes by changing one
component at a time. Their contrasts are not an additive end-to-end error
decomposition. The [independent guide/initializer derivation](CONTINUOUS_FIBER_GUIDE_INITIALIZATION_DIAGNOSTIC.md)
also compares the two known initial laws directly by Gaussian-mixture quadrature.

## First attempt: deadline-limited partial execution (2026-09-13)

**20 of 22 routes completed in the original attempt.** Its supervisor
stopped the child at the predeclared 2,400-second CPU wall-clock limit and
returned exit code 2, confirming termination. No numerical exception was
reported before the timeout. The original output directory contains the
prospectively saved settings and `route-01.json` through `route-20.json`, but
no `report.json` or child `failure.json`. The second setting's seed-1203 G+R
route was interrupted without a complete record; its paired DIR route was
not reached. Neither was treated as a completed observation in that first attempt.

The [separate partial review](../research/fixtures/continuous_multiseed_cpu_2026_09_13_review.json)
binds all 20 original route files by hash, reports every completed route, and
retains the then-missing pair. It does not replace a missing success report.
The original protocol, partial review, verification and 20 route files are
preserved without editing. The user's subsequent authorization and the
[time-extension note](MIXED_CONTINUOUS_MULTISEED_TIME_EXTENSION.md) allowed
completion of only that pair, not new seeds or changed settings.

The completed records contain **25,600 endpoint draws and 320 conditional
updates**: 20,480 control draws and 5,120 neural draws. They also contain 1,280
training BASE paths, 640 validation BASE paths and 172,032 evaluation
macrosteps. These are saved completed-work totals, not total attempted work;
the interrupted unsaved route may have consumed additional computation.

## Authorized completion of the fixed roster

The separate continuation completed both original seed-1203 routes in
**504.54 seconds (8 minutes 25 seconds)**, within its separate 1,800-second
supervisor cap, and exited with code 0. Its final decision is
`COMPLETE_FIXED_ROSTER_WITH_AUTHORIZED_TIME_EXTENSION`.
The interrupted G+R calculation was recomputed from its original starting
seed; this was not checkpoint resume. DIR used its previously unexecuted
original seed. No completed prefix route was rerun or replaced. The continuation
checked the original numerical versions and BASE population identity before
training; it did not use the different reader-test environment for this run.

The final report includes **22 unique declared routes, 26,624 endpoint draws
and 384 conditional optimizer updates**. Of those draws, 20,480 are controls
and 6,144 are neural endpoints. Completed-record work also includes 768
training pairs, 1,536 training BASE paths, 768 validation BASE paths, 1,536
validation pair-loss evaluations on 384 distinct pairs across fitted models,
and 180,224 evaluation macrosteps. Unknown interrupted work from the first
attempt is additional; these totals do not claim total attempted work or cost.

This completes the scientific roster with a disclosed execution-time deviation.
It does not turn the original 40-minute attempt into a pass, establish a
runtime-independent completion promise, or certify general checkpoint resume.

### All completed controls

Each cell is the maximum absolute error over the 24 predeclared indicators.
Every control has 2,048 draws. A is the reference-pressure setting; B is the
higher-pressure/shifted-observation setting. These are two synthetic settings,
not the two real datasets.

| Control | A: theta=0.8, y=0.7 | B: theta=2.5, y=1.4 |
| --- | ---: | ---: |
| Direct posterior draws | 0.01560 | 0.02222 |
| Exact-h sampler, exact conditional initial law | 0.02562 | 0.02026 |
| Exact-h sampler, uncapped-guide initial law | 0.01985 | 0.01050 |
| Uncapped guide-only sampler and initializer | 0.03099 | 0.08374 |
| Zero-clock guide sampler and initializer | 0.12644 | 0.16563 |

The original simultaneous route half-width is **0.05471** for these controls.
In B, guide-only's interval has a positive lower bound of 0.02903, identifying
finite-observable discrepancy at this resolution under the stated sampling
assumptions. The zero-clock control also has a positive lower bound in both
settings. The other intervals include zero; that does not prove exactness.
In particular, the smaller point error for the guide initializer in an exact-h
sampler does **not** establish that it is preferable to the exact initializer.
Sampling uncertainty is too large for that ranking.

### All completed neural fits

G+R means association-aware guide plus residual; DIR means unified direct
conditioner. Every completed fit uses 32 updates and 512 final draws. The
paired validation loss is evaluated on the same held-out 32 pairs at updates
0, 8, 16 and 32; the table shows endpoints, while every checkpoint and update
record remains in the original files. No checkpoint is selected by its loss.

| Setting | Seed | Method | Maximum indicator error | Held-out loss: 0 → 32 | Sampling seconds |
| --- | ---: | --- | ---: | ---: | ---: |
| A | 1201 | G+R | 0.03640 | 0.67099 → 0.63543 | 180.47 |
| A | 1201 | DIR | 0.13230 | 0.69499 → 0.65972 | 159.05 |
| A | 1202 | G+R | 0.03840 | 0.74593 → 0.71168 | 182.19 |
| A | 1202 | DIR | 0.13425 | 0.79166 → 0.71782 | 154.96 |
| A | 1203 | G+R | 0.03246 | 0.72146 → 0.70029 | 184.09 |
| A | 1203 | DIR | 0.11011 | 0.80606 → 0.77712 | 143.42 |
| B | 1201 | G+R | 0.10610 | 0.60994 → 0.59802 | 317.52 |
| B | 1201 | DIR | 0.18858 | 0.62639 → 0.60648 | 180.53 |
| B | 1202 | G+R | 0.09456 | 0.64625 → 0.64058 | 322.80 |
| B | 1202 | DIR | 0.17882 | 0.75624 → 0.75225 | 189.85 |
| B | 1203 | G+R | 0.09253 | 0.64240 → 0.63937 | 296.12 |
| B | 1203 | DIR | 0.15929 | 0.71442 → 0.71028 | 181.55 |

The original neural-route half-width is **0.10942**. G+R has lower observed
error than DIR in all six declared seed pairs, but these data do not
establish general superiority. Nor do they demonstrate benefit from residual
learning over guide-only: every completed trained G+R point error exceeds its
setting's guide-only point error. The control and neural draw counts differ,
so their maxima have different sampling noise; this is not evidence that
training necessarily causes degradation. Lower validation loss alone is not
a posterior-error guarantee.

### Complete three-seed summaries

Both settings now have their complete predeclared three-seed roster. The
first-setting summary is unchanged from the partial review; the second is
computed only after its actual final pair has completed, without imputation.

| Quantity, setting A | G+R | DIR |
| --- | ---: | ---: |
| Mean per-seed maximum error | 0.03575 | 0.12555 |
| Per-seed sample SD (descriptive) | 0.00302 | 0.01341 |
| Seed-mixture category-only error | 0.02673 | 0.09745 |
| Seed-mixture joint-CDF-grid error | 0.02467 | 0.12318 |
| Equal-weight seed-mixture maximum error | 0.02673 | 0.12318 |
| Mixture error interval | [0, 0.08724] | [0.06267, 0.18370] |

| Quantity, setting B | G+R | DIR |
| --- | ---: | ---: |
| Mean per-seed maximum error | 0.09773 | 0.17556 |
| Per-seed sample SD (descriptive) | 0.00732 | 0.01492 |
| Seed-mixture category-only error | 0.08862 | 0.03833 |
| Seed-mixture joint-CDF-grid error | 0.08891 | 0.17556 |
| Equal-weight seed-mixture maximum error | 0.08891 | 0.17556 |
| Mixture error interval | [0.02839, 0.14942] | [0.11505, 0.23607] |

In B, **DIR has the smaller category-only point error**, despite its larger
joint-CDF and combined errors. The G+R advantage is not uniform across metrics.

The mixture half-width is 0.06051. The estimated G+R advantage in mixture
error (DIR minus G+R) is **0.09646**, with interval **[-0.02457, 0.21748]**.
It includes zero. In B, the advantage is **0.08666**, with interval
**[-0.03437, 0.20768]**, also including zero. Superiority in the primary error
therefore remains unresolved in both settings. B's two fitted mixtures each
have finite-indicator discrepancy intervals excluding zero, which identifies
remaining target mismatch under the stated sampling assumptions; it is not
a full-distribution error estimate or an attribution to one approximation.
The mean paired per-seed error difference is a separate estimand and likewise
has an interval containing zero in both settings. Seed SDs include draw noise and are not
confidence intervals over unseen training seeds.

Some signed finite probabilities are distinguishable without resolving the
overall accuracy ranking: 8 of 24 signed indicator intervals exclude zero in A,
and 9 of 24 in B.
For example, in setting A the selected-key joint CDF at x=1.2 has G+R−DIR = -0.14258,
interval [-0.25982, -0.02534]. The CDF indicators are nested, not independent
discoveries. A difference between two fitted laws is not a proof that one is
closer to the full target.

**No uncertainty budget was reassigned after timeout.** The original 22-route,
four-mixture and two-contrast family sizes and alpha split remain in force.
All bounds are conditional on these fitted models and the stated ideal
independent-draw assumptions; numerical oracle arithmetic is not interval-
certified. The primary discrepancy remains a finite indicator maximum, not
continuous-state TV or KL.

### Independent guide/initializer diagnostic

Using the actual selected-key reference mass 0.7500019073486328, independent
Gaussian-mixture quadrature gives the following differences between the exact
capped conditional initial law and the uncapped-guide conditional initial law
under the same capped initial prior:

| Setting | Initial-law TV | Quadrature error estimate |
| --- | ---: | ---: |
| A | 0.03529749909 | 4.95e-13 |
| B | 0.07880395964 | 3.50e-12 |

This is a known-law integral, not TV estimated from neural samples. The
reported quadrature errors are numerical estimates, not certified bounds.
It quantifies one initial-law approximation, not terminal sampler error or
an additive end-to-end error decomposition. Both theta and y change between
settings, so the difference cannot be attributed to count pressure alone.
The [derivation](CONTINUOUS_FIBER_GUIDE_INITIALIZATION_DIAGNOSTIC.md) explains
why the aggregated OTHER contribution also accounts for its unchanged
conditional key/fiber law.

### Verification and timing limits

The preceding expanded development regression passes **1,600 tests**. Its **141 new
tests** also pass using a locally installed wheel outside the checkout with
source-path injection disabled, including a reduced actual 14-route integration
run. The [verification record](../research/fixtures/continuous_multiseed_verification_2026_09_13.json)
binds source and wheel hashes and records both numerical-library environments.
Test success is separate from the scientific result. The continuation adds
28 focused tests, including reduced exact agreement with the original neural
procedure on every non-timing route field and both complete summaries. The
test-only environment-mismatch check was corrected to be portable across
Torch versions and rerun. No original benchmark implementation bytes changed.
The new completion tests and existing statistics tests also pass from the
installed package outside the checkout: **46 passed**. The separate
[completion verification record](../research/fixtures/continuous_multiseed_completion_verification_2026_09_13.json)
records the package hash, import origin and unchanged original evidence.

Sampling times include initialization, host work and first-use costs. Fit and
validation took approximately 8.2–8.9 seconds per completed A fit and
12.2–13.0 seconds per completed B fit. Local tests and packaging overlapped
parts of the original run. A final 19.38-second reduced test fixture may have
briefly overlapped continuation startup; no further numerical tests ran while
that continuation was active. Times are not exclusive-hardware measurements.
There is no matched-quality speedup or general performance conclusion.

## Next scientific work

The independent initializer diagnostic and the fixed two-setting, three-seed
comparison are complete within this synthetic scope. The next substantive
question is why residual training has not demonstrated improvement over the
analytic guide. Use the independent likelihood/score target to distinguish
training and representation error from the reference/cap, initialization,
common-grid and physical-sampler approximations. Predeclare any follow-up
learning budget or better-powered comparison; do not change this result or
its tolerance/statistical rules after seeing which method looks favorable.
No additional cluster setup is needed for that local mathematical analysis.

## Remaining scientific boundaries

- The exact target covers a cap-one, zero-BASE reference submodel. These are not
  PhysioNet or Retail observations, nor results for a trained BASE.
- Training pairs come from a common-grid numerical BASE path. This is not
  silently identified with the exact continuous-time reference law.
- The current physical sampler tilts drift/jump coefficients and approximates
  time evolution; it is not the exact normalized conditional transition kernel
  of that training path law. Stage-time interpolation remains an approximation.
- Three training seeds support descriptive variation only. Small losses do not
  establish score or posterior accuracy. No quality threshold, stopping rule,
  matched-quality cost crossing or general superiority claim is selected here.
- Runtime measurements include first use and host work. Initialization costs
  are included in sampling time, but attempt counts are not instrumented.
  There is no GPU, full-training, real-data or public-release qualification.
