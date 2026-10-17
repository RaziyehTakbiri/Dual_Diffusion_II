# Research and reproducibility plan

Updated: 2026-09-13. This is the current **paper-first** execution plan.
The older [completion timetable](PROJECT_COMPLETION_TIMETABLE.md) retains its
compound obligations and history; it is not the ordering for our next local work.

## Overnight work scheduled — September 13–14

A single approximately eight-hour continuation is scheduled for 23:00–07:00
Asia/Tehran (19:30–03:30 UTC). It covers fixed-design repeated jump-skeleton
noise identification, comparison with existing bias anchors, a math-only
forward derivative-estimator derivation, independent audit and reproduction.
The existing learner, penalties, tolerances and scientific target stay fixed.
No new GPU, paid work, real data, learner replacement or publication is included.

New work stays in a separate writable staged checkout so it can continue
without write access to the original checkout. The [bounded work package](/Users/mahtab/.codex/.chatgpt-projects/g-p-6a5f91c1e79c819183983ba0010bb151/overnight/2026-09-13-noise-bias/SCOPE.md)
contains the exact roster, resource limits and stop conditions. No new
experiments start after 06:30 Tehran, and the block stops by 07:00; it may
finish earlier. A sleeping/unavailable app does not extend this window.

These overnight deliverables are **scheduled, not complete**. The existing
22-complete / seven-broader-open status is unchanged. New completion marks and
the morning handoff will be recorded in the staged plan and reconciled with
this original plan only after reviewing the outputs.

## Where we stand

We have an implemented mixed discrete/continuous model, actual BASE and
conditional learners, a numerical sampler, bounded CPU/T4 checks and local
checkpoint diagnostics. We now also have a complete ideal-reference association
and initializer proof, a precise finite-grid conditional-law contract, and the
first independently computable known-law mechanism experiment. The common-grid,
linear-gate successor is now connected to the actual mixed neural learner and
tested against an independent occurrence-attached continuous-fiber target.
Readers can run the synthetic demonstration and known-law benchmarks without Databricks.

**Variance reduction and derivative bounds: 2 of 2 bounded deliverables complete.**
Derived an unchanged-target conditional-Gaussian label estimator and
variance-sensitive derivative-response bounds for the zero-BASE cap-one
submodel. All 384 fixed fits are complete: aggregate value/score/Hessian RMS
errors improve in all 24 paired comparisons at matched stochastic-event work.
The independent audit passes 100,800 checks and both local environments pass
730 focused tests. None of the 48 routes passes every accuracy tolerance;
G+R Hessian error remains worse than guide-only in all 12 RB routes. The bounds
are valid under their stated assumptions but too loose to certify accuracy.
The learner and tolerances remain unchanged. This completes the derivation and
experiment, not derivative learning or sampler qualification.
[Results](docs/LOCALIZED_VARIANCE_REDUCTION_RESULTS.md).

**Finite-data/bias diagnosis: 1 of 1 bounded deliverable complete.**
All 512 fixed controls are complete and independently audited. The recorded
label-noise response is the largest contrast in every route and quantity;
combined regularization and fixed-family value-risk projection error also
remain. The learner, old fits and tolerances are unchanged. Both local
environments complete the comparison and pass **638 focused tests**, but their
fine numerical readbacks are not strict-threshold identical. Conservative
predeclared solver bounds remain loose; this is a realized mechanism diagnosis,
not independent variance attribution or derivative/sampler qualification.
[Results](docs/LOCALIZED_ERROR_DECOMPOSITION_RESULTS.md).

**Focused curvature and controlled learnability: 2 of 2 bounded deliverables complete.**
The one fixed seven-point score-only curvature improvement passes all
value/score/Hessian checks in four routes, with unchanged tolerances and
whole-profile bounds below 2.92. The subsequent forward-label learner completes
all 192 fits across 24 routes without backward-target training labels. All
route-mean validation risks improve over their baselines, and the larger sample
budget reduces all three RMS errors in every matched pair. Nevertheless,
0/24 learned routes meet all accuracy tolerances, and G+R derivative improvement
over guide-only is not established. Both comparisons run from an installed
wheel outside the checkout; **553 focused tests pass in each of two local
environments**. This completes the experiments, not derivative learnability or
sampler qualification. [Results](docs/LOCALIZED_CURVATURE_AND_LEARNABILITY_RESULTS.md).

**Localized derivative/envelope work: 2 of 2 bounded deliverables complete.**
The C² local quintic construction has a reviewed derivative-accuracy theorem
and mesh-uniform real-arithmetic coefficient bound. All 24 fixed routes and
192 active profiles are recorded. At 256 cells, primary value/score checks pass
for both methods; G+R also passes Hessians, while DIR retains 16 and 28 failures.
The largest whole-profile bound is 2.91851. This is substantial improvement,
not an all-primary-tolerances pass or learner/sampler integration.
[Results and limits](docs/LOCALIZED_RESIDUAL_RESULTS.md).

**Residual formulation/comparison: 2 of 2 bounded deliverables complete.**
A compact finite-fiber C² capacity proof and the fixed 24-route oracle-supervised
comparison are complete. All degree-64 likelihood-value checks pass, but score
and Hessian errors remain, and some coefficient envelopes are impractically
large. This is not a repaired general BCE learner or qualified sampler.
[Results and limits](docs/RESIDUAL_CAPACITY_COMPARISON_RESULTS.md).

**Residual likelihood/score diagnosis: 1 of 1 bounded deliverable complete.**
All twelve original fits were reproduced exactly and inspected against independent
continuous and numerical-grid targets. The current residual amplitude is too
restrictive; five fits saturated at all active probes, and lower classifier loss
did not yield substantial score correction. No model repair is claimed.
[Diagnosis/results](docs/RESIDUAL_LIKELIHOOD_SCORE_RESULTS.md).

**Multi-seed follow-up: 2 of 2 bounded deliverables complete. All 22 fixed
routes are now recorded.** The authorized continuation finished the missing
seed pair in 504.54 seconds, preserving the original 20 routes, settings and
uncertainty allocation. The first attempt remains a 40-minute timeout; the
[time-extension note](docs/MIXED_CONTINUOUS_MULTISEED_TIME_EXTENSION.md) and
[complete result](docs/MIXED_CONTINUOUS_MULTISEED_RESULTS.md) disclose the deviation. The
mixed-learner extension is **2 of 2 complete**. The preceding
scientific follow-up is **3 of 3 complete**, and the reader/scientific-draft package
is **5 of 5 complete**: with the diagnosis, formulation/comparison and localized
follow-up, the two curvature/learnability tasks, the finite-data/bias diagnosis
and the two variance-reduction tasks,
**22 explicitly checked
sub-deliverables**. This does not mean that
the full engineering infrastructure or the paper is finished. The historical
compound count remains **61 checked / 102 open / 163 total**; the completed
sub-deliverables below are tracked explicitly rather than falsely closing
larger scientific/release obligations.

## Completed reader/scientific-draft package (5/5)

- [x] **Scientific core and proof draft.** Consolidated carrier/reference,
  target/observation laws, BASE objective, conditional risk and sampler;
  equation-to-code map; five limited propositions with explicit assumptions.
  [Specification](manuscript_v3/hybrid_diffusion_scientific_core_v1.md) and
  [proof/claim plan](manuscript_v3/hybrid_diffusion_claims_and_proof_plan_v1.md).
  These are working derivations, not final theorem or novelty certification.
- [x] **Independent scientific and literature review.** Checked the new algebra
  and assumption boundaries against the code, corrected initializer/nuisance
  wording, and reviewed five close primary papers.
  [Related-work audit](manuscript_v3/hybrid_diffusion_related_work_and_claim_audit_v1.md).
- [x] **Portable synthetic training → sampling → descriptive evaluation.**
  Added a public command, strict configuration, two editable examples and saved
  losses/paths/weights. Both methods use identical trained BASE weights.
  [Runner](src/heterodiff/research.py), [configuration](src/heterodiff/research_config.py)
  and [examples](configs/).
- [x] **Local install and behavior verification.** Built/installed a wheel in
  a new local environment, ran both examples outside the checkout, checked
  dependencies, replay and saved-weight reload. The new reader suite passes
  106 tests in both tested environments; the expanded development regression
  passes 1,256 tests. [Verification record](research/fixtures/reader_cpu_verification_2026_09_13.json).
- [x] **Reader-facing front door and reproducibility contract.** Replaced the
  infrastructure-heavy README with science/quickstart documentation, preserved
  its history, documented domain-extension requirements and prepared a
  manual-only CPU CI workflow. [README](README.md), [instructions](REPRODUCING.md),
  [domain contract](docs/DOMAIN_EXTENSION.md). Remote CI is **not** marked passing.

## Completed scientific follow-up (3/3)

- [x] **Association-guide and reference-posterior initializer proof.**
  Independently reviewed occurrence multiplicities, empty/overflow branches,
  total-count conditioning, residual-only rejection, and a quantitative
  capped/uncapped reference distinction. S5 is complete for its stated ideal
  reference laws, not for the learned posterior.
  [Proof appendix](manuscript_v3/hybrid_diffusion_association_initializer_proof_v1.md).
- [x] **Conditional-law approximation contract for the independent benchmark.**
  Selected one common grid, a linear residual gate and normalized conditional
  transitions. Proved exact-grid conditioning and a harmonic-defect path-ratio/TV
  bound; supplied a concrete counterexample to generic cubic-gate realizability.
  This resolves the benchmark's definitions, not every full-hybrid approximation.
  The legacy learner and C17 disposition are unchanged.
  [Contract v2](manuscript_v3/hybrid_diffusion_conditional_law_contract_v2.md).
- [x] **Independently computable known-law mechanism experiment.**
  Completed all three scenarios and four observation branches with guide-only,
  G+R and DIR, matched learned update counts and complete error/loss/work curves.
  G+R has lower final TV than DIR in 12/12 toy cases, but guide-only is better
  than trained G+R in 2/12. This is an atomic finite-population experiment, not
  a general superiority or real-domain result. **1,355 regression tests pass**;
  the installed-wheel default benchmark also runs outside the checkout.
  [Results and reproduction](docs/FINITE_CONDITIONAL_BENCHMARK.md),
  [verification record](research/fixtures/finite_conditional_benchmark_verification_2026_09_13.json).

## Completed mixed-learner extension (2/2)

- [x] **Carry the common-path and gate contract into the actual mixed learner.**
  Implemented an opt-in shared-trajectory-grid population, uniform active-node
  training including time zero, explicit linear residual gate, trained-population
  sampling checks and legacy-default/checkpoint protection. The four-case local
  smoke executes 8 actual BASE and 8 conditional updates plus 24 paths. This is
  integration, not a proof of posterior recovery or resumable successor release.
  [Implementation](src/heterodiff/experiments/factorized_common_grid_pipeline.py),
  [mathematical contract](manuscript_v3/hybrid_diffusion_mixed_conditional_contract_v3.md).
- [x] **Add an independent continuous-fiber target and test the actual sampler.**
  Implemented exact-submodel Gaussian-mixture target/initializer/likelihood
  derivatives with independent quadrature checks. Completed all five fixed CPU
  routes: direct target draws, exact-h sampler controls on two grids, and actual
  trained G+R/DIR. Reported category and joint-CDF errors with explicit finite-draw
  limits; the target is not falsely identified with the Heun training law.
  [Complete comparison](docs/MIXED_CONTINUOUS_CONDITIONAL_BENCHMARK.md),
  [verified result](research/fixtures/mixed_continuous_conditional_benchmark_cpu_2026_09_13_verified.json),
  [verification](research/fixtures/mixed_continuous_conditional_verification_2026_09_13.json).

## Completed multi-seed follow-up (2/2)

- [x] **Independently quantify the guide/initializer approximation in the
  continuous-fiber reference submodel.** Derived the uncapped retained-ancestor
  and immigrant likelihood without calling the neural guide; normalized the
  corresponding initial Gaussian mixtures under the same capped initial prior;
  added known-law mixed-TV quadrature and finite-query score diagnostics.
  Native-guide and independent checks pass. This is not a learned terminal-law
  guarantee. [Derivation](docs/CONTINUOUS_FIBER_GUIDE_INITIALIZATION_DIAGNOSTIC.md).
- [x] **Complete the predeclared 22-route, three-seed CPU comparison.**
  Two settings, both actual neural methods, 32 updates per fit, 512 final draws
  per fit and five 2,048-draw controls per setting. Settings are fixed before
  results, with uncertainty separated from descriptive seed variation.
  [Protocol](docs/MIXED_CONTINUOUS_MULTISEED_PROTOCOL.md),
  [execution/results](docs/MIXED_CONTINUOUS_MULTISEED_RESULTS.md).
  **22/22 routes; complete with an authorized time extension.** The
  [combined report](research/fixtures/continuous_multiseed_completion_cpu_2026_09_13/report.json)
  includes 26,624 endpoint draws and 384 conditional updates; unknown interrupted
  work remains additional. G+R has lower combined point error than DIR in all
  six seed pairs, but both mixture-advantage intervals include zero and residual
  benefit over guide-only is not demonstrated. DIR has lower category-only
  point error in the harder setting. The original 20-route partial review and
  timeout are preserved. **28 continuation tests and 46 installed-wheel tests
  pass**, in addition to the preceding 1,600-test regression. See the
  [completion verification](research/fixtures/continuous_multiseed_completion_verification_2026_09_13.json).

## Completed residual-learning diagnosis (1/1)

- [x] **Diagnose the fitted residual against independent likelihood/score targets.**
  Derived the classifier Bayes target and gauge-independent capacity obstruction;
  implemented an independent analytic zero-BASE numerical-grid likelihood;
  replayed all twelve original 32-update fits with all 60 digest/loss/population
  checks matching, and evaluated all four checkpoints on 5,184 fixed queries.
  All final classifier losses improved, but coordinate-score correction mostly
  remained near the analytic baselines. The tiny gated amplitude provably
  excludes the required state contrasts on the finite query roster, and five
  fitted residuals saturate at all active probes. This diagnoses a restriction,
  not its remedy or a complete causal attribution of endpoint errors.
  **294 focused development tests and 107 installed-wheel tests pass.**
  [Derivation](docs/RESIDUAL_LIKELIHOOD_SCORE_ANALYSIS.md),
  [results](docs/RESIDUAL_LIKELIHOOD_SCORE_RESULTS.md),
  [verification](research/fixtures/continuous_residual_diagnostic_verification_2026_09_13.json).

## Completed residual formulation and controlled comparison (2/2)

- [x] **Derive and implement a capacity-sufficient compact finite-fiber residual.**
  Proved constructive value/score/Hessian approximation as polynomial degree
  grows, with a linear terminal gate and finite frozen coefficient envelopes.
  Implemented immutable compactified Chebyshev expansions and exact terminal
  zeros without changing the old neural architecture or sampler. The theorem
  is compact/fixed-observation/finite-fiber; the diagnostic code's finite degree
  cap is not an arbitrary-accuracy guarantee. Floating-point-safe and efficient
  sampler envelopes remain open.
  [Formulation/proof](docs/RESIDUAL_CAPACITY_FORMULATION.md).
- [x] **Complete the predeclared independent likelihood/score comparison.**
  All 24 fixed scenario/baseline/objective/degree routes and 192 continuous fits
  completed, following a disclosed export-only repair. Both objectives and
  every degree are retained. All degree-64 value checks pass; score/Hessian
  failures prevent any complete approximation pass. This oracle-supervised
  result does not close learning from random paired observations. **390 focused
  development tests pass**; portable reader verification and independent
  all-route auditing accompany the result.
  [Protocol](docs/RESIDUAL_CAPACITY_COMPARISON_PROTOCOL.md),
  [results](docs/RESIDUAL_CAPACITY_COMPARISON_RESULTS.md),
  [verification](research/fixtures/continuous_residual_capacity_verification_2026_09_13.json).

## Completed localized derivative and envelope work (2/2)

- [x] **Derive and implement a localized C² residual with controlled coefficients.**
  Added immutable quintic Hermite–Bézier pieces with shared jets, a linear gate,
  C² collars and constant tails. Proved exact-input core value/score/Hessian
  orders h⁶/h⁵/h⁴ and a mesh-uniform real-arithmetic value-envelope bound.
  The primary estimates curvature from scores; the separate control uses exact
  Hessian labels. No old model or sampling envelope was replaced.
  [Formulation](docs/LOCALIZED_RESIDUAL_FORMULATION.md),
  [implementation](src/heterodiff/models/localized_fiber_residual.py).
- [x] **Complete the predeclared localized likelihood/derivative comparison.**
  All 24 routes and 192 active profiles completed without retry. Every arm and
  resolution is retained; tolerances and independent targets are unchanged.
  Coefficient bounds remain below 2.92; all finest-mesh primary value/score
  checks pass, with 16/28 DIR Hessian failures still visible. This completes
  the controlled comparison, not learning from paired observations or sampler
  qualification. **483 focused development tests and 324 installed-wheel tests
  pass**; the portable full comparison reproduces all physical arrays exactly
  in the two tested local environments.
  [Protocol](docs/LOCALIZED_RESIDUAL_PROTOCOL.md),
  [results](docs/LOCALIZED_RESIDUAL_RESULTS.md),
  [verification](research/fixtures/continuous_localized_residual_verification_2026_09_13.json).

## Completed focused curvature and controlled learnability (2/2)

- [x] **Complete one predeclared score-only curvature improvement.**
  Derived and tested the seven-point score-difference estimator, retaining the
  same 256-cell localized family, target and tolerances. All four routes and
  32 active profiles pass value, score and Hessian checks; the old FD5 failures
  and extra-Hessian controls remain archived and unchanged. Exact supplied
  values/scores are still required: this is not learning from noisy data.
  [Protocol](docs/LOCALIZED_CURVATURE_PROTOCOL.md),
  [proof](docs/LOCALIZED_CURVATURE_FORMULATION.md).
- [x] **Complete a controlled non-oracle localized likelihood-learning comparison.**
  Proved the forward-label conditional-mean target, convex quasi-risk and
  observation-derived physical coefficient bound. Implemented a fixed smooth
  35-coefficient family and all 24 scenario/method/seed/budget routes, 192 fits,
  and 589,824 shared/nested synthetic forward suffixes. Every fit freezes before
  independent backward-target evaluation; no validation/oracle tuning occurs.
  All solvers report convergence, but none of the learned routes passes the
  full accuracy checks. The largest physical coefficient envelope is 3.49010,
  with no active coefficient boundaries. This is a new fixed-observation
  likelihood experiment, not a repair of the general amortized BCE learner.
  [Protocol](docs/LOCALIZED_LEARNABILITY_PROTOCOL.md),
  [formulation](docs/LOCALIZED_LEARNABILITY_FORMULATION.md),
  [results](docs/LOCALIZED_CURVATURE_AND_LEARNABILITY_RESULTS.md),
  [verification](research/fixtures/continuous_curvature_learnability_verification_2026_09_13.json).

## Completed finite-data/bias diagnosis (1/1)

- [x] **Separate realized finite-label/design responses from regularization and
  fixed-family projection error before changing the learner.** Retained the
  archived noisy fit, strictly re-solved its objective, replaced labels by
  independent conditional means on the same coordinates, and compared fixed
  penalized/unpenalized expected-design quadratures. All 512 controls and all
  ten cross terms per decomposition are recorded. An independent audit passes
  404,174 checks; an installed-wheel rerun completes outside the checkout.
  Noise is the largest recorded contrast in all 72 route/quantity comparisons,
  but neither exact variance attribution nor negligible numerical error at the
  original strict thresholds is claimed. No learner amendment was made.
  [Protocol](docs/LOCALIZED_ERROR_DECOMPOSITION_PROTOCOL.md),
  [formulation](docs/LOCALIZED_ERROR_DECOMPOSITION_FORMULATION.md),
  [results](docs/LOCALIZED_ERROR_DECOMPOSITION_RESULTS.md),
  [verification](research/fixtures/continuous_localized_error_decomposition_verification_2026_09_13.json).

## Completed variance-reduction derivation and comparison (2/2)

- [x] **Derive an unchanged-target variance-reduction strategy and derivative
  response bounds.** Conditional Gaussian integration removes terminal
  diffusion-coordinate noise while retaining the same marked jump skeleton.
  Proved equal conditional mean, label and fitting-gradient covariance
  reduction, and strong-convexity coefficient/derivative bounds. Their scope
  separates sampling, optimization, design, penalties and projection; no
  pathwise improvement or total score-error guarantee is claimed. The reported
  known-range bounds are too loose for the acceptance tolerances.
  [Derivation](docs/LOCALIZED_VARIANCE_REDUCTION_FORMULATION.md).
- [x] **Complete the fixed paired comparison under matched stochastic-event
  work.** All 48 routes and 384 fits use identical designs and paired labels,
  with the original learner, family, penalties and tolerances unchanged. All
  24 aggregate RMS pairs improve in each quantity, with node-level reversals
  disclosed. No route passes all tolerances, and no RB G+R route improves
  guide-only Hessian RMS. The independent audit passes 100,800 checks and the
  installed-wheel reproduction confirms the conclusions; 730 focused tests
  pass in each environment. Equal FLOPs, equal wall time, general-model
  qualification and sampler readiness are not claimed.
  [Protocol](docs/LOCALIZED_VARIANCE_REDUCTION_PROTOCOL.md),
  [results](docs/LOCALIZED_VARIANCE_REDUCTION_RESULTS.md),
  [verification](research/fixtures/continuous_localized_variance_reduction_verification_2026_09_13.json).

## Next scientific work, in order

- [ ] **Quantify the remaining mixed conditional-law approximations.**
  The fixed curvature construction now passes; the non-oracle learnability
  comparison, finite-data/bias diagnosis and Gaussian variance-reduction
  comparison are complete, but derivative accuracy is insufficient. Next
  distinguish remaining jump-skeleton sampling error from the measured
  design/penalty/projection floor. The analytic Gaussian conditional mean also
  motivates a forward-only derivative-supervision derivation; any subsequent
  derivative-aware fitting control must be declared as an explicit objective
  amendment, not silently substituted for today's value-risk learner. Retain
  numerical uncertainty; do not infer that simply removing penalties or
  enlarging the family repairs learning.
  Preserve every current fit and tolerance; do not tune repeatedly against the
  evaluated target. Oracle controls remain diagnostic, never learned results.
  Learner/sampler integration additionally
  needs an explicit stage-time/conditional-transition policy, tail treatment
  and valid practical sampling envelopes. Preserve the scientific
  target and acceptance tolerances; every model-class amendment stays explicit.
  Separate reference/cap and initialization effects from finite training,
  restricted representation, stage-time interpolation and numerical integration.
  Extend exact targets beyond the present cap-one reference submodel or provide
  independently controlled numerical targets for learned BASE. A small logistic
  loss is not a score or path-law bound; no general end-to-end claim is checked.
- [ ] **Run a broader, statistically informative known-law comparison.**
  Predeclare a justified statistical power/sample-size plan, learning budgets
  and broader observations/cap pressure after the above diagnosis. The earlier
  512-endpoint-draw assessments and current three-seed summaries do not establish method superiority or
  a residual-learning benefit over the guide. Two earlier exact-h grids do not
  establish convergence order. Add matched-quality work/cost comparisons and
  controlled learned-BASE targets without relabelling the completed result.
- [ ] **Establish the final contribution and theorem selection.**
  Use the closest literature, completed proofs and actual known-law results
  to decide which claims are defensible. Generic jump diffusion or neural
  guidance alone is not the novelty claim.

These are local mathematical/code tasks first. No new cluster or GPU check is
needed simply to start them.

## Engineering required for the final reader release

- [ ] **Implement general domain adapters, not just this contract.**
  Remove the exact-two-key-class dependency through a reviewed interface and
  demonstrate a third distinct domain while retaining existing behavior.
- [ ] **Provide general experiment checkpoints and supported execution profiles.**
  The saved reader weights are not resume checkpoints. Extend configuration,
  optimizer/RNG/data-position restoration and tests beyond the earlier fixed
  CPU diagnostic; validate supported CPU/GPU profiles with bounded work.
- [ ] **Complete scientific data/experiment and figure reproduction.**
  Add actual dataset acquisition/parsing/split instructions, permitted inputs,
  selected scientific settings, budgets, trained outcomes and scripts for
  every claimed table/figure. No real data or full training has happened here.
- [ ] **Validate and publish the release package.**
  Execute supported-platform CI, complete dependency/reproduction profiles,
  get owner-approved license/citation information, review public content and
  validate the reader path from a clean checkout. No publication or paid/remote
  job is authorized by this local plan.

## Scope and historical continuity

The synthetic reader example reports descriptive count/coordinate summaries,
not F105 or posterior accuracy. The separate finite benchmark now reports actual
conditional TV/KL against its known toy law, not held-out real-data performance.
Its linear gate and population-risk tables are explicitly new benchmark choices.
The mixed extension now selects a linear gate through a separate opt-in API,
not a silent change to the legacy default or acceptance tolerances. The new
continuous benchmark reports finite indicator discrepancies, not empirical TV.

Reader documentation, packaging and the opt-in model-policy implementation now
form a source successor. The earlier README/pyproject-only difference described
the preceding checkpoint, not the current tree. The historical
manifest/CPU lock and accepted receipt are unchanged and apply to their original
revision. We do not force new research code through the old exact-snapshot route.

No GPU/paid/cloud jobs, real-data reads, commits, pushes or publication occurred.
Only temporary local installation and invented-data CPU computation were used.
The follow-up replaced only the project wheel in the existing temporary reader
environment; it downloaded no additional dependencies.
