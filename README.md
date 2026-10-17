# HeteroDiff: hybrid diffusion on mixed event configurations

Research code for conditional generation of variable-cardinality event configurations
with exact discrete keys and continuous log-magnitude coordinates.

**Current status:** scientific specification, ideal-reference proofs, portable
synthetic demonstration and independently computable finite and continuous-fiber
conditional benchmarks connected to the actual mixed learner and sampler.
This is not yet a released reproduction of a completed paper. General-domain
plug-ins, full training/resume, scientific comparisons and final proofs remain
in progress.

## Start with the science

- [Model, objective and sampler](manuscript_v3/hybrid_diffusion_scientific_core_v1.md)
- [Claims, assumptions and five limited propositions](manuscript_v3/hybrid_diffusion_claims_and_proof_plan_v1.md)
- [Association-guide and initializer proof](manuscript_v3/hybrid_diffusion_association_initializer_proof_v1.md)
- [Conditional-law contract and approximation bounds](manuscript_v3/hybrid_diffusion_conditional_law_contract_v2.md)
- [Known-law benchmark, complete results and reproduction](docs/FINITE_CONDITIONAL_BENCHMARK.md)
- [Mixed neural extension and independent continuous target](docs/MIXED_CONTINUOUS_CONDITIONAL_BENCHMARK.md)
- [Multi-seed comparison and guide/initializer controls](docs/MIXED_CONTINUOUS_MULTISEED_RESULTS.md)
- [Residual capacity proof and controlled likelihood/score results](docs/RESIDUAL_CAPACITY_COMPARISON_RESULTS.md)
- [Localized smooth residual: derivative accuracy and coefficient bounds](docs/LOCALIZED_RESIDUAL_RESULTS.md)
- [Score-only curvature improvement and controlled non-oracle learnability](docs/LOCALIZED_CURVATURE_AND_LEARNABILITY_RESULTS.md)
- [Finite-label noise, design and regularization diagnosis](docs/LOCALIZED_ERROR_DECOMPOSITION_RESULTS.md)
- [Gaussian variance reduction, derivative bounds and matched-work comparison](docs/LOCALIZED_VARIANCE_REDUCTION_RESULTS.md)
- [Closest prior work and contribution audit](manuscript_v3/hybrid_diffusion_related_work_and_claim_audit_v1.md)
- [Current research and reproducibility plan](PROJECT_RESEARCH_AND_REPRODUCIBILITY_PLAN.md)

The research question is whether an association-aware reference guide improves
conditional generation relative to direct conditioning under the same task and
budget. The answer is not assumed. Software tests alone do not establish it;
the finite benchmark supplies the first explicitly limited mechanism experiment.

## Run a small example without Databricks

Use Python 3.11 and an ordinary local virtual environment. A CPU is sufficient;
no cloud account, Docker image, credentials or real dataset is needed.

See [REPRODUCING.md](REPRODUCING.md) for installation. Once installed, from the
repository root:

```sh
python -m heterodiff.research inspect --config configs/synthetic_physio_cpu.json
python -m heterodiff.research run --config configs/synthetic_physio_cpu.json --output ./physio-demo-001
python -m heterodiff.research run --config configs/synthetic_retail_cpu.json --output ./retail-demo-001
```

Each shipped configuration runs both methods with two BASE updates, two
conditional updates and two final draws per method. Each run has a 120-second
child-process deadline. Output must be a **new folder under an existing parent**;
the command creates it. It never replaces previous results.

The output contains the effective configuration, losses, generated configurations
and paths, descriptive evaluation, environment versions and model weights.
The weights are explicitly **not** a general resume checkpoint. The descriptive
metrics are **not** F105, held-out evaluation or evidence of method superiority.

## Run the independent conditional benchmark

After the same reader installation, run:

```sh
python -m heterodiff.experiments.finite_conditional_learning_benchmark --output ./finite-conditional-001.json
```

This CPU-only command compares guide-only, G+R and DIR against an independently
computed finite-state posterior across all 12 declared observation cases. It
reports conditional TV/KL, learning curves and counted work. The default run has
a 120-second deadline and writes a new JSON file. It needs no cloud or dataset.
See the [complete results and limitations](docs/FINITE_CONDITIONAL_BENCHMARK.md).

To test the actual mixed neural learner and hybrid sampler against an independent
continuous-fiber Gaussian-mixture target, use:

```sh
python -m heterodiff.experiments.mixed_continuous_conditional_benchmark --output ./mixed-continuous-001.json
```

This separate CPU command has a 600-second deadline and includes exact-likelihood
sampler controls plus both trained neural methods. It reports category/CDF errors,
not empirical continuous TV or a superiority claim. See the
[complete five-route comparison](docs/MIXED_CONTINUOUS_CONDITIONAL_BENCHMARK.md).

The larger, prospectively specified comparison adds three training seeds, two
synthetic settings and independent guide/initializer controls:

```sh
python -m heterodiff.experiments.continuous_multiseed_benchmark --inspect
python -m heterodiff.experiments.continuous_multiseed_benchmark --output ./continuous-multiseed-001
```

This is a separate 22-route CPU experiment with a 2,400-second child deadline,
not another environment setup. It saves each completed route and uses fixed finite-indicator
uncertainty bounds. Read the [prospective protocol](docs/MIXED_CONTINUOUS_MULTISEED_PROTOCOL.md)
and [results/limitations](docs/MIXED_CONTINUOUS_MULTISEED_RESULTS.md) before running it.
The first run reached its time limit with 20/22 routes complete. An authorized
local CPU continuation completed only the missing pair: **all 22 fixed routes
are now recorded**, with the original timeout preserved and no settings changed.
This is a completed synthetic comparison, not a method-superiority claim.

The follow-up [residual diagnosis](docs/RESIDUAL_LIKELIHOOD_SCORE_RESULTS.md)
compares the actual fitted likelihoods and scores with independent continuous
and numerical-grid targets. It identifies a restricted model-capacity issue
without changing the original results or claiming posterior recovery.
The [derivation](docs/RESIDUAL_LIKELIHOOD_SCORE_ANALYSIS.md) and
[reproduction instructions](REPRODUCING.md#8-diagnose-the-archived-residual-fits)
keep this scientific diagnosis separate from environment setup.

The next [residual formulation and controlled comparison](docs/RESIDUAL_CAPACITY_COMPARISON_RESULTS.md)
is now complete: an expandable compact-fiber residual corrects the fixed-cap
obstruction, and all 24 oracle-supervised routes are recorded. Degree-64 value
checks pass; remaining derivative errors and large global coefficient envelopes
prevent sampler promotion. The old paired-data neural learner is unchanged.

The [localized smooth follow-up](docs/LOCALIZED_RESIDUAL_RESULTS.md) now completes
another 24 fixed routes. Real-arithmetic coefficient bounds remain below 2.92.
At the finest mesh, all primary value/score checks pass; G+R also passes Hessians,
while DIR retains 16/28 Hessian failures in the two settings. This is controlled
oracle approximation before learner/sampler integration, not posterior recovery.
Readers can reproduce it with the separate
[`continuous_localized_residual` command](REPRODUCING.md#10-localized-smooth-residual-comparison).
See [the portable command](REPRODUCING.md#9-controlled-residual-capacity-comparison).

The separate [focused curvature and learnability comparison](docs/LOCALIZED_CURVATURE_AND_LEARNABILITY_RESULTS.md)
now distinguishes exact-input approximation from statistical learning. A fixed
seven-point score-only curvature estimator passes all four original finest-mesh
cases. A new forward-simulator-supervised smooth likelihood learner completes
192 fits without backward-target training labels: more data improves errors,
but none of its 24 routes meets the full accuracy tolerances. This is useful
scientific evidence of a remaining derivative-learning gap, not sampler
qualification. Both [portable commands](REPRODUCING.md#11-focused-score-only-curvature-control)
are local CPU experiments with frozen settings.

The [matched-work variance-reduction comparison](docs/LOCALIZED_VARIANCE_REDUCTION_RESULTS.md)
now completes 384 fixed fits. Conditional Gaussian averaging preserves the
submodel's target and lowers aggregate value/score/Hessian RMS errors in all
24 paired comparisons, without changing the learner or tolerances. Derived
derivative-response bounds are conservative, and none of the learned routes
meets every accuracy tolerance. This is completed statistical-method work,
not a qualified general sampler; the match is simulated event work, not FLOPs
or wall time. [Portable reproduction](REPRODUCING.md#14-matched-skeleton-gaussian-variance-reduction).

## Reusable implementation

The public entry point is `heterodiff.research`; its strict configuration layer
is `heterodiff.research_config`. The core model, learner, reference law and
sampler remain separate modules under `src/heterodiff/`.

[Domain extension contract](docs/DOMAIN_EXTENSION.md) describes what a new domain
must supply. Currently only the two typed Physio/Retail carriers are implemented;
an arbitrary-domain plug-in interface is not being claimed.

## Reproduction and release status

Local CPU examples and tests are the first public-facing workflow. Selected-T4
precision tests are separate bounded evidence, not qualification of this reader
interface on every GPU. Mathematical laws, numerical approximations and software
precision policies are distinguished in the scientific specification.

The final repository still needs full mixed-model scientific comparisons,
paper table/figure scripts, general checkpoints, supported-platform CI results,
and owner-approved licensing/citation information before public release.

## Historical Databricks work

Databricks is an optional execution venue, not part of the mathematical model.
The [previous infrastructure-focused README](docs/history/README_databricks_before_reader_workflow.md)
is retained for historical context; its operational directions are not the
current reader quickstart.

The old B08 lock, source manifest and accepted CPU receipt belong to their
original source snapshot. Reader packaging and the opt-in common-grid/linear-gate
model extension intentionally create a different source revision. No old receipt is relabelled as verification
of the current tree, and the old exact-snapshot notebook should not be rerun
against this revision.

For project history, see [the evidence ledger](PROJECT_EVIDENCE_LEDGER.md).
