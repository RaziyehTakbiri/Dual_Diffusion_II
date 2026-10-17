# Actual mixed learner and sampler against a continuous-fiber target

Date: 2026-09-13. **The bounded local extension and comparison are complete.**
This is a known-law synthetic mechanism experiment, not a paper-level claim of
conditional recovery or superiority. No Databricks or GPU is needed.

## What changed

The [opt-in common-grid pipeline](../src/heterodiff/experiments/factorized_common_grid_pipeline.py)
connects the actual mixed neural BASE and conditional models to the existing
hybrid sampler. One frozen grid generates the entire joint/product training
experiment. Query times select existing path states; they no longer change the
path grid. Training is uniform over active left grid nodes, including time zero.

The explicitly selected `LINEAR_ACTIVE_TIME_V1` residual gate permits generic
first-order terminal residual behavior; it does not guarantee the fitted
coefficient is correct. The legacy cubic gate remains the default, with
regression checks; old checkpoint formats reject the new policy rather than
mislabel it. Snapshot metadata is available, but general successor resume is
not implemented. See the [mathematical contract v3](../manuscript_v3/hybrid_diffusion_mixed_conditional_contract_v3.md).

## The independent target

The [oracle](../src/heterodiff/evaluation/continuous_fiber_conditional_benchmark.py)
uses a cap-one birth/death process with an OU coordinate attached to each
continuous occurrence. Death removes that coordinate; a new birth starts a new
standard-normal coordinate. This is not an unrelated Gaussian appended to a
counting process.

An exact three-category projection (empty / other key / selected continuous key)
and an ancestry indicator give finite Gaussian-mixture initial and endpoint
conditional laws. Matrix exponentials, Gaussian algebra and independent
quadrature do not call the learned guide, neural model or numerical sampler.
The original full-support key/fiber reference is retained when materializing
OTHER. This particular exact projection is **not** valid for arbitrary neural
BASE potentials or larger cardinalities.

Fixed comparison: theta=0.8, death and OU rates=1, horizon=1, no clean hold,
state/observation caps=1, observation noise standard deviation=0.5, whole-channel
contamination=0.1, selected observation coordinate=0.7, stationary reference
initial law. The selected key's actual mass is **0.7500019073486328**, computed
from the full reference rather than rounded. All inputs are invented.

## Complete result, without selecting favorable routes

The five routes were specified before execution. The reference-control and
direct-posterior routes use 2,048 draws each. Each neural method gets eight
updates with two joint/product pairs per update, followed by 64 draws on an
eight-step grid. Both neural methods use the same frozen, all-zero neural BASE
and identical initial tensors. They use different guide/residual parameterizations
to approximate the same conditional target; their realized approximate laws differ.

| Route | Draws | Largest category-probability error | Largest joint-CDF-grid error |
|---|---:|---:|---:|
| Independent posterior direct draws | 2,048 | 0.001672 | 0.006243 |
| Actual sampler, exact h and exact initial law, 4 steps | 2,048 | 0.013519 | 0.012035 |
| Actual sampler, exact h and exact initial law, 16 steps | 2,048 | 0.007171 | 0.009349 |
| Actual trained G+R, 8 steps | 64 | 0.034027 | 0.056157 |
| Actual trained DIR, 8 steps | 64 | 0.109168 | 0.127683 |

The CDF is the **joint** probability of the selected key and coordinate<=x,
evaluated at 21 fixed values from -3 to 3. Together with three category indicators
and five routes, a union Hoeffding calculation at family alpha=0.01 gives
half-widths **0.049622** for 2,048 draws and **0.280705** for 64 draws, assuming
ideal independent draws within each fixed route (conditional on fitted weights).
The bound concerns sampling error around each route's own probabilities. The
comparison to the target is only a finite-indicator compatibility check; it is
not a bound on total approximation bias or proof of posterior accuracy.
Keyed finite pseudorandom streams do not themselves prove ideal independence.

The coarse/fine oracle-control results are encouraging, but their sampling
uncertainty does not establish a convergence rate or monotone grid improvement.
The neural sample sizes are too small for a reliable method ranking. In
particular, the lower observed G+R discrepancy is **not a superiority claim**.
Full loss histories and moment summaries are retained in the
[verified report](../research/fixtures/mixed_continuous_conditional_benchmark_cpu_2026_09_13_verified.json).
The preceding un-suffixed report is an earlier local run, before method-specific
initializer descriptions and sampling-bound wording were clarified; neither its
samples nor any failed sample was selected to improve the reported result.

## What each comparison isolates

- **Exact h control:** uses the capped oracle's h, derivatives and conditioned
  initial distribution in the actual Heun/jump sampler. Differences from the
  target are numerical and finite-sampling effects; no learned guide is involved.
- **Learned G+R:** uses the actual uncapped future-reference guide, conditioned
  only at the initial cap, plus a trained residual and its rejection initializer.
- **Learned DIR:** uses the zero-clock observation likelihood baseline plus its
  trained residual and initializer.
- **Separate trained-BASE integration:** `common_grid_integration_smoke()` runs
  both domains and methods with two actual BASE updates, two conditional updates
  and two conditional draws per case. It checks 8 BASE updates, 8 conditional
  updates and 24 paths. This confirms connection after BASE learning; the analytic
  reference posterior is not claimed to describe those changed BASE weights.

The neural benchmark combines approximation of the common-grid training law,
finite training, representation limits, guide/initialization error, off-grid
time interpolation and conditional integrator error. The exact continuous
reference target is not silently called the Bayes target of the Heun training
population. Small logistic loss does not establish coordinate-score accuracy.
The normalized finite-grid Doob theorem does not make these coefficient-tilted
hybrid transitions exact. These are substantive scientific limitations, not
extra administrative prerequisites.

## Reproduce

After the [ordinary reader installation](../REPRODUCING.md), run from any directory
with an existing writable parent:

```sh
python -m heterodiff.experiments.mixed_continuous_conditional_benchmark --output ./mixed-continuous-001.json
```

This starts one local CPU child with a fixed 600-second deadline and writes a
new JSON file only after completing all five routes. Choose a new output filename
to repeat. It does not install packages, contact a cloud service, query a GPU or
read real data. There are no automatic retries or discarded failed paths.
Direct `run_benchmark()` calls have a soft deadline; use the command for child
supervision. Smaller explicit `BenchmarkBudget` values support unit tests, not
relabelled default evidence. The default run took about one minute locally;
that is an observation, not a machine-independent runtime promise.

From a checkout, the focused suite is:

```sh
PYTHONPATH=src python -m pytest -q tests/unit/test_continuous_fiber_conditional_benchmark.py tests/unit/test_factorized_common_grid_pipeline.py tests/unit/test_mixed_continuous_conditional_benchmark.py
```

The oracle's 56 tests include independent quadrature of evidence, initial and
terminal laws, backward consistency, gradient/Hessian checks and Doob-transition
normalization, including nonstationary Gaussian mixtures. The pipeline and
benchmark tests exercise real neural updates, same-path queries, legacy
compatibility, actual sampler replay and the global likelihood-bound boundary.
See the [verification record](../research/fixtures/mixed_continuous_conditional_verification_2026_09_13.json)
for exact test/install scope.

## Next scientific work

The larger multi-seed comparison and guide-only/initializer controls are now
complete; its [recorded result](MIXED_CONTINUOUS_MULTISEED_RESULTS.md) combines
the original 20 routes with the missing pair completed under an authorized
local time extension. The original 40-minute timeout, settings and uncertainty
allocation remain visible. Diagnose the lack of demonstrated residual benefit,
then plan enough observations and draws to resolve meaningful differences
without selecting favorable outcomes. Quantify interpolation and numerical bias
separately before extrapolating beyond this exact submodel. Full experiments,
general domain adapters, general resume, GPU qualification of this successor
and paper-level guarantees remain open.
