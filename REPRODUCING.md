# Reproduce the portable synthetic demonstration

For the new actual mixed learner/common-grid sampler comparison against an
independent continuous-fiber target, use the same installation below and follow
[this benchmark guide](docs/MIXED_CONTINUOUS_CONDITIONAL_BENCHMARK.md). It is a
separate opt-in successor; the two small reader demonstrations retain their
legacy defaults and descriptive-only scope.

This is the first reader-facing research workflow, not the final paper benchmark.
It runs the actual BASE learner, conditional joint/product learner and numerical
conditional sampler. All input configurations are invented in code.

## 1. Install in a local environment

After cloning this repository, open a terminal in its root. Use Python 3.11:

```sh
python3.11 -m venv .venv-reader
source .venv-reader/bin/activate
python -m pip install --upgrade pip
```

On Linux, select the CPU PyTorch build before the remaining requirements:

```sh
python -m pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cpu
```

On macOS, the ordinary PyPI requirement below supplies PyTorch; omit that
Linux-only line. Then:

```sh
python -m pip install -r requirements/reader-cpu.txt
python -m pip install --no-deps .
python -m pip check
```

PyTorch distributes platform-specific CPU/CUDA builds; see its
[official installation guidance](https://pytorch.org/get-started/locally/).
Do not install the historical Databricks CPU lock or use the old
`reference` extra for this separate reader environment.

Direct requirements are pinned. This file is **not a complete transitive hash
lock**, and numerical equality across dependency releases/platforms is not
promised. The actual versions are saved in each report. Python 3.11 on macOS
ARM64 is tested locally; Linux CI is prepared below but not yet executed.
Windows instructions/validation and a supported GPU reader environment remain
release tasks. Package metadata now requires Python >=3.11 instead of making
an untested Python 3.9 promise for these current modules.

## 2. Inspect, train, sample and evaluate

```sh
heterodiff-research inspect --config configs/synthetic_physio_cpu.json
heterodiff-research run --config configs/synthetic_physio_cpu.json --output ./physio-demo-001
heterodiff-research run --config configs/synthetic_retail_cpu.json --output ./retail-demo-001
```

`python -m heterodiff.research` is the equivalent module entry point.
Inspection only validates/prints the effective configuration and imports no
numerical library. A run uses one supervised CPU child. It does not access
Databricks, change cluster settings, download data or launch remote jobs.

Each default example uses both methods, two BASE updates, two conditional
updates and two final draws per method. The command stops the child at the
configured wall-clock deadline (120 seconds by default). Direct calls to
`run_experiment` from another Python program have only the documented soft
budget; use the CLI for process-level supervision.

The output folder must not already exist; its parent must exist. The command
creates the final folder. To repeat a run, choose a new output name. On error,
a nonzero exit status and, where possible, `failure.json` are produced. A hard
timeout may leave partial files without that receipt. Only a successful exit
and `report.json` indicate completion.

## 3. Read the outputs

- `config.json`: every effective setting, including defaults and seed.
- `report.json`: run status, versions, policy, method summaries and elapsed time.
- One `<method>.json` per method: both training histories, exact key
  serialization, log coordinates, every generated path state, reference/model
  settings and descriptive statistics.
- One `<method>.weights.pt` per method: BASE and conditional tensor state.
  This is **weights-only**, not optimizer/RNG restoration or a resume checkpoint.
  Load only trusted files using `torch.load(..., weights_only=True)`.

The invented source contains an atom and two duplicate continuous occurrences.
The supplied observation retains one continuous occurrence. It is a chosen
synthetic observation, not a downloaded patient/customer record or a held-out
sample drawn for a scientific study.

The reported count/coordinate summaries show what the model generated. They
are **not F105**, posterior accuracy estimates, confidence intervals or evidence
that either method is better. Two draws are for usability, not statistical power.
Training loss need not decrease at every stochastic update.

Both methods receive identical BASE initialization, BASE updates and trained
BASE weights. Explicit labeled streams control conditional training and sampling.
This does not make their differing final path laws equal or promise bitwise
CPU/GPU equivalence. Same-runtime CPU replay is tested.

## 4. Adjust the supported configuration

The two JSON files in `configs/` are editable examples. Supported controls:

| Field | Allowed values |
|---|---|
| domain | R3-PHYS or R4-RETAIL |
| methods | One or both declared method identifiers |
| base_steps / conditional_steps | 1–16 each |
| base_samples / conditional_samples | 1–4 / 1–2 |
| draws | 2–16 |
| seed | Unsigned 64-bit integer |
| maximum_seconds | 1–300 |
| device / precision_policy | cpu / BASE_GRAPH_FP64_SHARED_V1 only |

Unknown fields, duplicate JSON keys, invalid types and nonfinite values fail
before execution. Increasing bounds may hit the time or existing model resource
limits; failed samples are not silently discarded. The reference cap, observation
model, schedule, architecture and AdamW policy are fixed toy settings recorded
in the outputs, **not selected scientific hyperparameters for the paper**.

The conditional learner currently optimizes a query-refined numerical
joint/product risk. Exact Bayes representability and the connection to one
common conditional path law are open theoretical questions; see
[the scientific core](manuscript_v3/hybrid_diffusion_scientific_core_v1.md).

## 5. Run the checks

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -p no:cacheprovider tests/unit/test_research_config.py tests/unit/test_research_workflow.py
```

These tests execute tiny real CPU runs for both domains/methods, compare
same-seed replays, restore weights into fresh models, recompute the summaries,
and check failure/output/deadline behavior. They are not substitutes for
scientific experiments.

The optional GitHub workflow `.github/workflows/reader-cpu.yml` is manual-only
and CPU-only. Adding it locally launches nothing; it still needs an actual
remote run before Linux CI can be marked passing.

## 6. Independently computable conditional benchmark

Using the same current installation, from an existing writable directory:

```sh
python -m heterodiff.experiments.finite_conditional_learning_benchmark --output ./finite-conditional-001.json
```

This separate CPU experiment enumerates a finite atomic law and compares
guide-only, G+R and DIR against its independently computed posterior. Defaults
cover three scenarios, all four observation branches and 2048 updates per
learned route within a 120-second supervised deadline. No file is overwritten.
The complete curves and measured limitations are in
[the benchmark guide](docs/FINITE_CONDITIONAL_BENCHMARK.md).

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -p no:cacheprovider tests/unit/test_finite_conditional_benchmark.py tests/unit/test_finite_conditional_learning_benchmark.py
```

All 99 benchmark tests pass under both tested CPU dependency profiles. The
default benchmark was also run from the installed wheel outside the checkout.
It is an exact-finite-population-risk mechanism study, not full mixed-neural
qualification or a finite-sample generalization experiment. Its selected
common-grid/linear-gate contract is separate from the older reader model above.

## 7. Multi-seed mixed continuous-fiber comparison

The independent continuous-fiber target and actual mixed neural/sampler
connection are implemented. The bounded multi-seed experiment has its own fixed
[prospective protocol](docs/MIXED_CONTINUOUS_MULTISEED_PROTOCOL.md):

```sh
python -m heterodiff.experiments.continuous_multiseed_benchmark --inspect
python -m heterodiff.experiments.continuous_multiseed_benchmark --output ./continuous-multiseed-001
```

Inspection prints the fixed settings without importing Torch or running a
sampler (NumPy/SciPy are imported). The full command runs one supervised CPU
child, with a 2,400-second deadline, three training seeds, two synthetic settings,
32 updates per fitted model and 512 final draws each. Five controls per setting
use 2,048 draws each. It downloads nothing, reads no real data and requests no GPU.

Use a new output directory under an existing parent. The child writes
`protocol.json` before computation, then `route-01.json` through `route-22.json`
and a complete `report.json`. A failure or timeout is not a completed comparison;
partial route files remain visible. There is no automatic retry, seed replacement
or early stopping. Reduced Python-API budgets are explicitly test scope, not the
full experiment. Direct API calls have a soft deadline only.

The [execution/result guide](docs/MIXED_CONTINUOUS_MULTISEED_RESULTS.md) separates
sampling uncertainty from descriptive training-seed variation. Completion is
not a superiority or posterior-recovery pass. Independent analytic initializer
TV compares two known laws; endpoint samples are evaluated with category and
joint-CDF indicators, not empirical continuous TV.

The first recorded local default run stopped at the deadline with 20/22 complete
routes. A faster machine may behave differently, but completion within this
bound is not promised. The user subsequently approved additional local CPU
time to finish the original missing pair; the
[time-extension note](docs/MIXED_CONTINUOUS_MULTISEED_TIME_EXTENSION.md) and
[results](docs/MIXED_CONTINUOUS_MULTISEED_RESULTS.md) distinguish that continuation
from the preserved incomplete first attempt.

For the one archived partial run only, the separate completion command is:

```sh
python -m heterodiff.experiments.continuous_multiseed_completion --source-root /absolute/path/to/checkout --inspect
python -m heterodiff.experiments.continuous_multiseed_completion --source-root /absolute/path/to/checkout --output ./continuous-multiseed-completion-001 --maximum-seconds 1800
```

This is a specific evidence-bound completion utility, **not general checkpoint
resume**. It requires the unchanged archived 20-route prefix, review, protocol
and implementation files in that checkout. Inspection verifies those files
without importing Torch. Actual completion additionally requires the original
development numerical versions; it deliberately refuses a different environment
because the population/RNG identity can change. The 28 new tests separately
exercise reduced equivalence rather than replaying this full archived run.
Ordinary readers should start with the general full-comparison command above;
they do not need this historical completion utility for a fresh experiment.

## 8. Diagnose the archived residual fits

The independent numerical-grid likelihood is now available as
`heterodiff.evaluation.continuous_fiber_grid_target.ContinuousFiberGridTarget`.
It computes likelihoods, scores, evidence and Gaussian-mixture laws without
calling the neural learner or drawing endpoints. It is restricted to the
explicit zero-BASE, cap-one reference and existing macro nodes; it is not a
general learned-model oracle. See the
[mathematical analysis](docs/RESIDUAL_LIKELIHOOD_SCORE_ANALYSIS.md).

The separate historical-fit diagnosis replays all twelve original training
prefixes, verifies their exact parameter/loss bindings, and evaluates fixed
likelihood/score queries without drawing new conditional endpoints:

```sh
python -m heterodiff.experiments.continuous_residual_diagnostic --archive /absolute/path/to/checkout/research/fixtures/continuous_multiseed_completion_cpu_2026_09_13/report.json --protocol /absolute/path/to/checkout/docs/RESIDUAL_LIKELIHOOD_SCORE_DIAGNOSTIC_PROTOCOL.md --output ./residual-diagnosis-001
```

Use a new output directory beneath an existing parent. The command has a
1,200-second child deadline and preserves completed route files on failure.
It requires the original development numerical versions and the unchanged
verification file beside the archived experiment directories. It intentionally
refuses a different environment instead of presenting new fits as the old ones.
This restriction is specific to retrospective exact replay, **not** a new
environment requirement for the normal reader demonstration or oracle tests.
The fixed [diagnostic protocol](docs/RESIDUAL_LIKELIHOOD_SCORE_DIAGNOSTIC_PROTOCOL.md)
and [results](docs/RESIDUAL_LIKELIHOOD_SCORE_RESULTS.md) explain the distinction.

The independently computable targets and diagnostic primitives can be tested
under the ordinary reader installation without reconstructing the historical
fits:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -p no:cacheprovider tests/unit/test_continuous_fiber_grid_target.py tests/unit/test_continuous_residual_diagnostic.py
```

## 9. Controlled residual-capacity comparison

This new portable comparison uses the independent numerical-grid likelihood,
not an archived training run or Databricks installation. The
[prospective protocol](docs/RESIDUAL_CAPACITY_COMPARISON_PROTOCOL.md) fixes both
baselines, three degrees and value-only/value-plus-score objectives:

```sh
python -m heterodiff.experiments.continuous_residual_capacity --inspect
python -m heterodiff.experiments.continuous_residual_capacity --output ./residual-capacity-001
```

Use a new output folder under an existing parent. Inspection imports NumPy/SciPy
but not Torch and fits nothing. The second command runs one local CPU child
with a 300-second deadline and one numerical thread. It writes the protocol and
source bindings before fits, then all 24 routes and the complete report. It
downloads nothing and uses no GPU, cloud, real data or endpoint sampler.
No original-development exact-version replay restriction applies to this new
command; actual versions and numerical ranks are reported.

These are oracle-supervised finite-fiber approximation results, not a replacement
neural learner or production sampler. All declared outcomes are retained, including
failures; completion is not an all-tolerances pass. The
[results](docs/RESIDUAL_CAPACITY_COMPARISON_RESULTS.md) document the preserved
first-attempt export failure, corrected repeat, remaining score/Hessian errors,
and coefficient-envelope limitations.

Focused portable tests:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -p no:cacheprovider tests/unit/test_compact_fiber_residual.py tests/unit/test_continuous_residual_capacity.py
```

## 10. Localized smooth residual comparison

The next independent-target comparison replaces a global polynomial expansion
with C² local quintic pieces and explicit coefficient envelopes. The
[formulation](docs/LOCALIZED_RESIDUAL_FORMULATION.md) and
[prospective protocol](docs/LOCALIZED_RESIDUAL_PROTOCOL.md) distinguish the
primary value/score-only construction from the extra-Hessian-label control.

After the ordinary reader installation:

```sh
python -m heterodiff.experiments.continuous_localized_residual --inspect
python -m heterodiff.experiments.continuous_localized_residual --output ./localized-residual-001
```

The output must be a new folder under an existing parent. Inspection imports
NumPy/SciPy but not Torch and constructs no target profiles. Execution uses one
local CPU child, one numerical thread and a 300-second deadline. It records the
protocol/source hashes before construction and retains all 24 routes, 192 active
profiles, terminal controls and complete report. There are no downloads, GPU/
cloud jobs, real data, neural updates or endpoint samples. The command works
from an installed package outside the checkout and does not require the archived
development environment. Envelopes are not floating-point sampling certificates.

Both arms and all three fixed meshes are reported; no success is selected for
learner/sampler promotion. At the finest mesh, primary likelihood/score checks
pass, but the DIR Hessian checks retain 16 and 28 failures. The
[results](docs/LOCALIZED_RESIDUAL_RESULTS.md) give the complete interpretation.

Focused tests, run from a checkout after installation:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -p no:cacheprovider tests/unit/test_localized_fiber_residual.py tests/unit/test_continuous_localized_residual.py
```

## 11. Focused score-only curvature control

This is a separate, fixed seven-point score-difference construction on the
existing 256-cell mesh. It uses exact values and scores, not Hessian labels.
It reads the preceding saved report as an unchanged control, without refitting
its FD5 or exact-Hessian arms. After reader installation, from the checkout:

```sh
python -m heterodiff.experiments.continuous_localized_curvature --inspect
python -m heterodiff.experiments.continuous_localized_curvature --archive-report research/fixtures/continuous_localized_residual_cpu_2026_09_13/report.json --output ./localized-curvature-001
```

When running outside the checkout, supply the absolute path to that archived
report. The archive hash is intentionally fixed for this particular comparison;
do not substitute another result or edit its expected hash. The new output
directory is created under an existing parent. One local child, one numerical
thread, 300-second deadline, four routes and no retries. The
[protocol](docs/LOCALIZED_CURVATURE_PROTOCOL.md),
[derivation](docs/LOCALIZED_CURVATURE_FORMULATION.md) and
[results](docs/LOCALIZED_CURVATURE_AND_LEARNABILITY_RESULTS.md) state the limits.

## 12. Controlled forward-label likelihood learnability

This independent command needs no archived fit, Databricks, GPU, credentials or
dataset. It trains a fixed-observation smooth residual from simulated forward
suffixes and the known terminal observation density. It is not the old
amortized BCE learner and does not train on oracle likelihood/score/Hessian
labels. Both methods share labels; the two budgets are nested. Every one of the
192 fits freezes before the independent backward target is first evaluated.

```sh
python -m heterodiff.experiments.continuous_localized_learnability --inspect
python -m heterodiff.experiments.continuous_localized_learnability --output ./localized-learnability-001
```

One local child, one numerical thread, 1,200-second deadline and no retries.
The command creates a new output directory and saves the protocol/source
bindings, 48 raw paired datasets, 24 frozen fit records, a freeze-barrier record,
24 evaluated routes and the complete report. It simulates forward terminal
states for labels, not learned conditional endpoint samples. Reported completion
is **not** an accuracy pass: all current learned routes retain tolerance
failures. Read the [prospective protocol](docs/LOCALIZED_LEARNABILITY_PROTOCOL.md),
[mathematical formulation](docs/LOCALIZED_LEARNABILITY_FORMULATION.md) and
[complete results](docs/LOCALIZED_CURVATURE_AND_LEARNABILITY_RESULTS.md).

Focused checks for both additions, from a checkout after installation:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -p no:cacheprovider tests/unit/test_localized_score_curvature.py tests/unit/test_continuous_localized_curvature.py tests/unit/test_continuous_forward_labels.py tests/unit/test_localized_likelihood_learner.py tests/unit/test_continuous_localized_learnability.py
```

## 13. Fixed noise/design/regularization diagnosis

This separate comparison reopens the archived forward-label experiment without
changing the learner. It compares the original fit, a stricter same-risk solve,
conditional-mean-label controls on the same inputs, and penalized/unpenalized
expected-design quadratures. The oracle-aided controls are **not** learned
models. No new labels are simulated and no hyperparameters are selected.

After ordinary reader installation, from the checkout:

```sh
python -m heterodiff.experiments.continuous_localized_error_decomposition --inspect
python -m heterodiff.experiments.continuous_localized_error_decomposition --archive research/fixtures/continuous_localized_learnability_cpu_2026_09_13 --output ./localized-error-decomposition-001
```

Outside the checkout, supply the absolute archive-directory path. The archived
report, all required datasets/frozen fits and old source bindings must match;
do not edit the expected archive hash to accept unrelated data. The command
creates a new output directory beneath an existing parent and uses one local
CPU child, one numerical thread, a 1,200-second deadline and no retries. It
records all 512 controls, frozen coefficients, both quadrature chains, raw
stage arrays and every cross term. It needs no Databricks, GPU, credentials,
real dataset or downloads. The archive is the fixed synthetic result being
diagnosed, not an external private data source.

Read the [protocol](docs/LOCALIZED_ERROR_DECOMPOSITION_PROTOCOL.md),
[derivation](docs/LOCALIZED_ERROR_DECOMPOSITION_FORMULATION.md) and
[complete results](docs/LOCALIZED_ERROR_DECOMPOSITION_RESULTS.md). Completion
does not imply strict derivative accuracy, independent variance attribution,
or sampler qualification. Two local dependency environments retain the broad
conclusions but do not give bitwise or strict-threshold-equivalent outputs.

The independent arithmetic audit and separate post-result sensitivity analysis
read saved fits only; they do not refit them. From the checkout:

```sh
python scripts/audit_localized_error_decomposition.py --repo . --result ./localized-error-decomposition-001 --output ./localized-error-audit-001.json
python scripts/analyze_localized_fit_sensitivity.py --report ./localized-error-decomposition-001/report.json --output ./localized-fit-sensitivity-001.json
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -p no:cacheprovider tests/unit/test_localized_population_risk.py tests/unit/test_continuous_localized_error_decomposition.py tests/unit/test_localized_fit_sensitivity.py
```

## 14. Matched-skeleton Gaussian variance reduction

This separate experiment compares raw terminal labels with their conditional
Gaussian averages on **the same simulated birth/death skeletons**. It keeps
the existing likelihood learner, spline family, penalties and tolerances.
Read the [prospective protocol](docs/LOCALIZED_VARIANCE_REDUCTION_PROTOCOL.md)
and [derivation](docs/LOCALIZED_VARIANCE_REDUCTION_FORMULATION.md).

After the ordinary reader installation, inside or outside the checkout:

```sh
python -m heterodiff.experiments.continuous_localized_variance_reduction --inspect
python -m heterodiff.experiments.continuous_localized_variance_reduction --output ./localized-variance-reduction-001
```

Use a new directory beneath an existing parent. One CPU child has a
1,200-second deadline and no retries. The fixed roster has 48 routes, 384 node
fits and 589,824 unique paired training/validation skeletons. It saves the
protocol, source bindings, paired labels, terminal Gaussian summaries,
per-suffix work counts, frozen models and complete target comparisons. All
fits freeze before target evaluation. No Databricks, GPU, credentials, private
data, network downloads or prior result archive is required.

The computational match is stochastic-event work, not equal FLOPs or wall
time. Joint generation times do not establish standalone speedup. The bound
on label-induced derivative error does not remove design, regularization,
representation or optimization error. The candidate applies to the stated
linear-Gaussian cap-one submodel, not every trained neural diffusion.

From the checkout, independently audit the saved arithmetic (no refitting).
Unlike the comparison command, this preservation audit also requires the
repository's prior learnability archive and its independent arithmetic helper
`scripts/audit_localized_error_decomposition.py`; retain those reference files.
The audit verifies saved terminal-moment arithmetic, not a replay of every jump:

```sh
python scripts/audit_localized_variance_reduction.py --repo . --result ./localized-variance-reduction-001 --output ./localized-variance-audit-001.json
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -p no:cacheprovider tests/unit/test_continuous_rao_blackwell_labels.py tests/unit/test_continuous_localized_variance_reduction.py
```

## 15. Scope still to complete for a paper release

Known targets beyond the cap-one, frozen-zero-BASE submodel and adequately
powered scientific comparisons remain open. The release also needs
general domain interfaces, general checkpoints/resume, dataset instructions
consistent with their permissions, real experimental configurations and one
script per reported table/figure. Licensing and citation metadata need the
owners' approval; no license is invented here.

The current README/packaging changes intentionally differ from the historical
B08 source manifest. That manifest/lock and its accepted receipt remain
historical, unchanged records, not a requirement that new research code match
an old snapshot.
