# Independently computable finite conditional benchmark

Date: 2026-09-13

This is a **known-law mechanism experiment**, not just a software parity
check. It has an independently enumerated conditional target and reports error
against that target. It is deliberately an atomic finite-state special case,
not the full mixed neural learner, a PhysioNet/Retail result or a submission-ready
comparison.

## Run it locally

Use the installation in [REPRODUCING.md](../REPRODUCING.md), including the reader
CPU dependencies and the current project wheel. Then, from any existing writable
working directory:

```sh
python -m heterodiff.experiments.finite_conditional_learning_benchmark --output ./finite-conditional-001.json
```

The output file must not already exist. Its parent must exist; the command writes
the complete result only after successful computation. Defaults are the declared
12 observation cases, 2048 updates per learned route and a 120-second supervised
child deadline. No GPU, Databricks, credentials, network or dataset is needed.
The CLI supervisor supplies the hard deadline; the Python function alone checks
a soft deadline. There is no automatic retry or outcome-based early stopping.

For a short implementation smoke check, explicitly use `--steps 1`. That is
not the full experiment. `--maximum-seconds` permits an explicit 1–300 second
limit, but this archived experiment used 120 seconds throughout.

## What is independently computable?

The [oracle](../src/heterodiff/evaluation/finite_conditional_benchmark.py) enumerates
ten occupancy states of two event types with a total-count cap of three. It
builds a capped birth/death reference generator and a fixed tilted toy BASE
generator. Starting from the truncated Poisson reference prior, it computes
transition matrices, endpoint probabilities and the conditional posterior by
finite linear algebra.

The observation alphabet has four branches: empty, one type-A event, one type-B
event and overflow. Occurrence-wise half-thinning is mixed with a 10% independent
Poisson observation channel. The benchmark uses **probability-valued**
likelihoods on this finite alphabet. These equal the general guide's
reference-density likelihood times the observation reference mass; that
convention is fixed in both the oracle and training initialization.

The oracle imports none of the hybrid association-guide, neural-learner or
hybrid-sampler implementation. Its tests additionally check observation
probabilities by enumerating labeled retention masks, transition matrices by
independent uniformization, path Bayes identities and necessary initialization.

Numerical matrix exponentials are a reference computation, not exact arithmetic
certification. In the archived run, exact-oracle conditional propagation had
maximum terminal TV residual 3.081e-16.

## Matched comparison, and its limits

All methods share the same prior, toy BASE, observations and time grid
`0, 0.25, 0.5, 0.75, 1`. The three scenarios vary BASE tilt and cap pressure;
their equations and values are declared in the
[conditional-law contract](../manuscript_v3/hybrid_diffusion_conditional_law_contract_v2.md).

- **Guide-only:** the uncapped independent-reference likelihood, evaluated on
  the capped states, with no learned residual.
- **G+R:** that same guide plus a bounded, linearly gated FP64 residual table.
- **DIR:** the terminal observation likelihood plus an identically sized,
  bounded, linearly gated FP64 residual table.

Both learned routes use the same balanced population logistic risk, zero
initialization, observation-only nuisance scalar and AdamW settings. Each
observation has its own saturated 40-entry residual table plus one scalar;
there is **no finite-sample or across-observation generalization** experiment.
The tilted BASE is specified, not trained. This setup intentionally removes
encoder and Monte Carlo error so conditional-law questions can be isolated.

For each route, 2048 updates evaluate 163,840 class/state terms. One final
objective diagnostic brings objective-evaluation work to 163,920 terms.
Across 24 learned routes this is 49,152 optimizer updates and 3,934,080
objective-evaluation class/state terms. Oracle preparation, analytic-guide
calculation and law evaluation are separate from these counts. The JSON
reports per-route training/checkpoint times and total elapsed time; guide-only
has zero optimizer updates, **not zero computation cost**.

The approximate conditional chain explicitly normalizes every transition row
and tilts its initial prior. It is not the existing coefficient-tilted
Heun/jump sampler. The legacy model's cubic gate and objective remain unchanged.

## Complete result: terminal total variation

Full machine-readable result:
[finite_conditional_benchmark_cpu_2026_09_13.json](../research/fixtures/finite_conditional_benchmark_cpu_2026_09_13.json).
Reported benchmark wall time was **10.06 seconds**, including first-use
overheads, on Python 3.11.5, Torch 2.12.1,
NumPy 2.4.6, SciPy 1.17.1. Timings are descriptive,
not a controlled hardware-speedup claim.

Lower TV is better. Learned columns are the fixed final checkpoint at 2048
updates, never the best observed checkpoint.

| Scenario | Observation | Guide-only TV | G+R TV | DIR TV |
|---|---|---:|---:|---:|
| Weak / low cap pressure | Empty | 0.000960 | < 1e-12 | 1.85e-7 |
| Weak / low cap pressure | Type B | 0.000659 | 0.004607 | 0.059741 |
| Weak / low cap pressure | Type A | 0.001815 | 0.001656 | 0.040278 |
| Weak / low cap pressure | Overflow | 0.003897 | 0.003518 | 0.047514 |
| Strong / low cap pressure | Empty | 0.012455 | < 1e-12 | 2.22e-7 |
| Strong / low cap pressure | Type B | 0.004338 | 0.006778 | 0.064927 |
| Strong / low cap pressure | Type A | 0.017840 | 0.003323 | 0.035262 |
| Strong / low cap pressure | Overflow | 0.040862 | 0.013894 | 0.052224 |
| Strong / high cap pressure | Empty | 0.023677 | 0.002634 | 0.008529 |
| Strong / high cap pressure | Type B | 0.033117 | 0.012362 | 0.022937 |
| Strong / high cap pressure | Type A | 0.017382 | 0.002023 | 0.023170 |
| Strong / high cap pressure | Overflow | 0.027431 | 0.005037 | 0.024152 |

G+R has lower final TV than DIR in all 12 specified cases. This includes two
near-zero comparisons for the empty observation; it is not a statistical
significance claim. **Guide-only is better than trained G+R in two type-B
cases** (both lower-cap-pressure scenarios). Thus this run does not establish
that adding/training the residual always improves a good guide.

Larger cap pressure increases the maximum absolute uncapped/capped reference
likelihood discrepancy over all observations from about **0.01550** to
**0.11576**. This directly measures an approximation exposed in the
[association/initializer proof](../manuscript_v3/hybrid_diffusion_association_initializer_proof_v1.md);
it does not imply that posterior error is monotone in cap pressure.

## Learning curves, without selecting a favorable endpoint

The following is an **unweighted macro-average across all four observations**
in each scenario, not an evidence-weighted population score. Per-observation
TV, KL, logistic losses, nuisance values, residual magnitudes and all five
checkpoints remain in the JSON.

| Scenario | Updates | Mean G+R TV | Mean DIR TV |
|---|---:|---:|---:|
| weak-base-tilt-low-cap-pressure | 0 | 0.001833 | 0.123432 |
| weak-base-tilt-low-cap-pressure | 32 | 0.001829 | 0.123171 |
| weak-base-tilt-low-cap-pressure | 128 | 0.001764 | 0.116477 |
| weak-base-tilt-low-cap-pressure | 512 | 0.008343 | 0.087924 |
| weak-base-tilt-low-cap-pressure | 2048 | 0.002445 | 0.036883 |
| strong-base-tilt-low-cap-pressure | 0 | 0.018874 | 0.110450 |
| strong-base-tilt-low-cap-pressure | 32 | 0.018713 | 0.110201 |
| strong-base-tilt-low-cap-pressure | 128 | 0.016412 | 0.103686 |
| strong-base-tilt-low-cap-pressure | 512 | 0.017859 | 0.083016 |
| strong-base-tilt-low-cap-pressure | 2048 | 0.005999 | 0.038103 |
| strong-base-tilt-high-cap-pressure | 0 | 0.025402 | 0.104496 |
| strong-base-tilt-high-cap-pressure | 32 | 0.025383 | 0.104392 |
| strong-base-tilt-high-cap-pressure | 128 | 0.024735 | 0.100489 |
| strong-base-tilt-high-cap-pressure | 512 | 0.016656 | 0.066608 |
| strong-base-tilt-high-cap-pressure | 2048 | 0.005514 | 0.019697 |

The weak-tilt G+R mean TV increases from 0.001833 initially to 0.008343 at
512 updates while mean logistic excess falls from 0.488776 to 0.131050.
It ends at 0.002445, still above its guide-only starting mean. Improving
classification risk therefore must not be presented as monotone improvement
of conditional posterior error.

The finite-grid harmonic-defect bound is also reported. At the final learned
checkpoint it equals the uninformative upper bound one in 10/12 cases for
each learned method. The remaining bounds are conservative, not tight
estimates. State-independent likelihood scaling can change this bound without
changing the normalized law; measured terminal TV remains the primary direct
diagnostic. No logistic-risk-to-gradient or global hybrid path guarantee is
claimed.

## Conditional approximation questions resolved here

1. A single fixed grid supplies a common endpoint law and observation evidence.
2. Exact backward likelihoods plus the correct initial tilt recover its
   Bayesian posterior.
3. Learned likelihoods need row normalization; the harmonic defect supplies a
   proved finite-grid path-ratio identity and conservative TV bound.
4. A two-state counterexample shows generic terminal correction is first order
   in remaining time. A bounded cubic gate cannot represent it arbitrarily
   near the boundary. The benchmark selects a linear gate, without asserting
   that its bound or optimizer is sufficient for exact recovery.
5. The uncapped guide, capped reference likelihood and toy BASE likelihood
   are separate objects with measurable differences.

These statements are developed and proved in the
[contract v2](../manuscript_v3/hybrid_diffusion_conditional_law_contract_v2.md).
The retired C17 theorem is not restored.

## What remains before a full paper claim?

Carry the common-path and gate choices into the actual mixed-domain learner,
then test an independently computable continuous-fiber conditional target and
the real numerical sampler. Add finite-sample trials, uncertainty, meaningful
parameter sweeps and matched-quality cost comparisons before claiming general
G+R superiority. The present toy settings and fixed population-risk optimization
were not selected using real data. They supply a reproducible first mechanism
result, not an ICML/ICLR/NeurIPS acceptance or novelty guarantee.
