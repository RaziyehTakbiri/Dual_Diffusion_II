# Localized learner: fixed noise/design/penalty diagnosis

Declared on 2026-09-13 before any new diagnostic fit. This is a local CPU-only,
synthetic experiment. It changes neither the learner nor its data, observations,
penalties, representation, coefficient box, or acceptance tolerances.

## Question and fixed chain

For every archived route, compare A (archived fit), N (strict same-noisy-risk
re-solve), M (same input coordinates with independent conditional-mean labels),
P (penalized expected-design quadrature fit), U (unpenalized fit with the same
representation and box), and T (independent numerical-grid log likelihood).
The exact pointwise and derivative identity is

`A-T = (A-N) + (N-M) + (M-P) + (P-U) + (U-T)`.

Save all ten cross-inner-products. These are realized contrasts, not independent
variance components or additive percentages. The last term is a constrained
value-risk projection residual, **not** the minimum possible score/Hessian
approximation error. P-U removes roughness and ridge together. The different
G+R/DIR offsets remain fixed, so their full-potential families need not coincide.
See the [derivation and limitations](LOCALIZED_ERROR_DECOMPOSITION_FORMULATION.md).

## Preserved input and work roster

- Original report: `research/fixtures/continuous_localized_learnability_cpu_2026_09_13/report.json`.
  SHA-256: `d8db24c1c4f2d22069da8ec15640cd9b553dfec5f3ecf87b5f0530069289a692`.
- Original protocol SHA-256: `c99b27fbd042359f65f54cd7c191a4bdd28e98f62303ad341fcdb8287ee8036e`.
- Original freeze digest: `ccd403105cc28b6391ed8f319faa817d6145217a01cb23b44d072c114193871b`.
- Same two scenarios, both methods, seeds 11/29/47, nested budgets 1024/8192,
  eight active macro nodes, terminal residual exactly zero, 35 physical
  coefficients in the existing tied 32-cell quintic family.
- 192 N fits and 192 M fits. No new forward labels or simulation seeds.
- 32 P and 32 U fits at each of two quadratures: 128 population controls,
  shared across seeds and sample budgets. **512 new diagnostic fits total.**
- Expected input design: E/O masses 1/4 each, C mass 1/2 uniform on [-4.5,4.5].
  Use positive Gauss-Legendre rules with 16 and 32 points per each of 32 cells.
  **32 is the primary**, 16 a fixed numerical sensitivity control. Neither
  nonlinear-risk integral is asserted exact; no post-result rule refinement.
- Box: `|a_j| <= 2 log(M/c)`; P uses existing roughness 1e-4 and ridge 1e-6;
  U uses zero penalties. No penalty or family search.

## Solver and validation

Every new control starts at zero and uses one L-BFGS-B call: maxiter 2000,
maxls 50, ftol 1e-15, gtol 1e-11. No warm starts, Newton polishing, retry,
target-error stopping or result-dependent extension. Preserve any unsuccessful
fit and disclose its numerical limitations. The parent has a 1200-second
deadline, one numerical thread, and retains partial outputs on failure.

Before fitting, reopen and verify the old report, protocol, source bindings,
all required datasets and prefixes, and frozen routes/barrier. Reconstruct
the original objectives and physical readbacks. No archive file is changed.
Manufactured tests check analytic gradients/Hessians, convex box gaps,
quadrature, validation and the telescoping/cross-term algebra before execution.

Report optimizer status, iterations, projected gradient, box first-order gap,
full-domain conservative strong-convexity estimate, coefficient-distance and
finite-probe readback bounds, as well as local Hessian spectra. These ordinary
float64 numbers are **not interval-certified bounds**. Loose bounds remain
visible and do not become evidence that solver contamination is negligible.

All control coefficients are saved and frozen before fixed-probe comparisons.
M/P/U consume exact conditional-mean labels for diagnostic purposes only;
they are not non-oracle learned models. Validation labels never enter a fit,
selection, stopping rule or diagnostic objective.

## Fixed readout

Use the original 256 continuous probes on [-4,4], both atoms separately and all
nine nodes. Aggregate continuous errors only across the eight active nodes.
Preserve value/score/Hessian tolerances exactly. Save raw stage arrays,
RMS/max errors, tolerance counts, all five signed contrasts and their Gram
matrix for both complete quadrature chains.

Report q16/q32 coefficient and physical/derivative differences and cross-rule
objective/gradient evaluations: **quadrature-plus-solver** sensitivity, not a
certified pure integration error. Evaluate every fitted stage against the same
q32 unpenalized excess risk using `h/M * (expm1(f-T) - (f-T))`.

Internal atom checks: exact-mean M-P atom values should vanish at the exact
minima because input category proportions are fixed; U-T atom values should
also vanish. Nonzero residuals are numerical/objective-consistency diagnostics,
not empirical continuous-design noise. Describe three-seed changes and nested
budget pairing without confidence or universal sample-complexity claims.

## Completion, reproducibility and next decision

Complete this diagnostic only after all 512 controls, saved readouts,
independent reconstruction and local installed-wheel reproduction are checked.
Reader rerun is a separate portability check with the same settings, not a
search for favorable outcomes. Update the plan for this bounded deliverable;
do not close derivative learnability or sampler qualification merely because
the experiment finishes. Interpret mixed, cancelling or unresolved effects
honestly, and propose any learner amendment separately after this diagnosis.

No real data, GPU or remote compute, cloud jobs, package downloads, sampler
integration, paid-job launch, repository publication or automatic learner
replacement is included.
