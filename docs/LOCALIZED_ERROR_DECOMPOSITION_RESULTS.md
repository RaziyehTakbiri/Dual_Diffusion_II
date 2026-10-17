# Finite-label noise, design variation and fixed-family bias

2026-09-13. **The fixed diagnostic is complete; the learner is unchanged.**
The largest recorded contrast is the response to finite simulated labels in
all 24 routes and all three quantities (72/72 comparisons). Combined
regularization effects and fixed-family value-risk projection error also remain.
This is a realized controlled comparison, not independent variance attribution,
an all-tolerances pass, or sampler qualification.

## What was compared

The [prospective protocol](LOCALIZED_ERROR_DECOMPOSITION_PROTOCOL.md) and
[mathematical formulation](LOCALIZED_ERROR_DECOMPOSITION_FORMULATION.md) fix
the original data, family, box, targets and tolerances. We retained:

`A-T = (A-N) + (N-M) + (M-P) + (P-U) + (U-T)`.

A is the original noisy fit; N strictly re-solves the same objective; M uses
the same coordinates with independent conditional-mean labels; P uses the
penalized expected-design quadrature; U removes both penalties within the same
family/box; T is the independent numerical-grid target. M/P/U are explicitly
oracle-aided diagnostic controls, not learned models. Different G+R/DIR offsets
are retained; an identical residual basis does not imply identical full families.

All **512 predeclared controls** completed: 192 N, 192 M, and 128 shared
population profiles. All coefficients were frozen before the fixed evaluation
comparisons. No new forward labels were generated; no fit was retried. Primary
execution took 9.90 seconds locally. q32 per cell was the prospectively chosen
primary; all q16 sensitivity controls are also retained.

## Main separation

The table gives ranges of **route RMS contrasts** across all 24 routes, using
256 continuous probes at each of eight active nodes. They are norms of signed
differences, not additive contributions to the total error.

| Recorded contrast | Log value RMS | Score RMS | Hessian RMS |
| --- | ---: | ---: | ---: |
| Archived stopping discrepancy, A-N | 1.50e-5–4.26e-5 | 5.04e-5–9.33e-5 | 2.73e-4–4.22e-4 |
| Realized label-noise response, N-M | 0.08594–0.35248 | 0.24106–0.86634 | 1.16804–3.99335 |
| Realized design response, M-P | 0.000147–0.005912 | 0.000358–0.015666 | 0.001390–0.074490 |
| Combined regularization shift, P-U | 0.004334–0.039183 | 0.014464–0.159371 | 0.063205–0.820851 |
| Fixed-family risk projection, U-T | 0.000114–0.001124 | 0.001620–0.014969 | 0.016962–0.183385 |

Increasing the nested label budget from 1,024 to 8,192 reduces the recorded
label-noise RMS in every matched route/quantity. This supports addressing
label-estimation precision before simply enlarging the representation. It does
not establish a general sample-complexity law from three seeds.

The regularization effect is especially visible for DIR. The following are
the four unique expected-design controls, pooled across active nodes; their
repetition beside seeds and budgets does not create independent replications.

| Scenario / method | P score RMS | U score RMS | P Hessian RMS | U Hessian RMS |
| --- | ---: | ---: | ---: | ---: |
| Reference pressure / G+R | 0.014413 | 0.001620 | 0.062374 | 0.016962 |
| Reference pressure / DIR | 0.118101 | 0.007817 | 0.599420 | 0.091941 |
| Higher pressure / G+R | 0.035228 | 0.005331 | 0.154006 | 0.054875 |
| Higher pressure / DIR | 0.159115 | 0.014969 | 0.817477 | 0.183385 |

Removing penalties improves all four pooled value/score/Hessian errors and
reduces the common q32 unpenalized excess risk at all 32 distinct active-node
problems. This is not nodewise derivative monotonicity: U improves score RMS
at 25/32 nodes and Hessian RMS at 23/32. The exceptions are G+R nodes. This
diagnostic removes roughness and ridge together; it does not choose a new
penalty or isolate their separate continuous-coordinate effects.

U-T is not pure capacity bias or the best achievable derivative error. It
includes the fixed spline/box/boundary constraints and the geometry of a
value-risk projection, as well as numerical control error. Even U has
remaining tolerance failures. **A, N, M, P and U each have zero routes passing
every original value/score/Hessian threshold.**

## Cross terms and numerical limits

All ten cross terms per decomposition are saved and independently checked.
Across route/quantity summaries their summed contribution can raise or lower
the total squared error; for Hessians it ranges from approximately -18.53% to
+10.16% of the total. These percentages describe the *sum of cross terms*,
not source fractions. The maximum pointwise telescope discrepancy is 3.56e-15;
the squared-error reconstruction discrepancy is at most 5.33e-15.

All 512 solvers report success, but all stop on relative objective reduction,
not the requested 1e-11 gradient threshold. The largest projected gradient is
1.39e-8; the largest box gap is 3.15e-7. No coefficient reaches its box boundary.
The predeclared conservative whole-box coefficient-distance estimates span
0.153–54.87; their largest score/Hessian pointwise estimates are about
130.1/839.4. **These loose estimates do not certify negligible optimizer
contamination.** The small A-N difference alone is not such a certificate.

A [separate post-result sensitivity addendum](LOCALIZED_ERROR_SENSITIVITY_ADDENDUM.md)
uses the exponential-risk Hessian structure to analyze the same saved fits.
It is distinguished from the predeclared result, performs no new fits, and
does not erase the loose original bounds or claim interval certification.
Its independently reviewed Hessian-variation argument yields finite estimated
coefficient radii for all 512 saved fits, from 8.03e-7 to 0.003871. For the N/M
label contrast, the sum of the worst fitted-optimum Hessian RMS response
estimates is 0.000292, versus a smallest recorded N-M Hessian RMS of 1.168.
This strengthens the numerical evidence for a large label-noise response,
but remains a post-result, non-interval estimate. The unpenalized population
controls are less tightly resolved: their worst Hessian RMS response estimate
is 0.012974, so fine projection-error claims remain limited.
[Separate sensitivity record](../research/fixtures/continuous_localized_error_sensitivity_2026_09_13.json).

q16/q32 maximum physical differences are 1.085e-5 in value, 8.537e-5 in score
and 7.768e-4 in Hessian; the maximum coefficient difference is 4.450e-5.
They are small relative to the largest recorded label-noise contrasts but
can matter at the strict acceptance thresholds. They are quadrature-plus-solver
responses, not certified integration-error bounds.

Atom checks give max |M-P|=7.811e-7 and |U-T|=6.219e-7. The ideal atom
identities are exact; these nonzero computed residues are numerical controls,
not finite continuous-design variation. No atom error is hidden inside the
continuous-probe averages.

## Independent verification and reader reproduction

An independent script reconstructs the spline features, baseline formulas,
stage arrays, risks and decomposition arithmetic without importing the new
runner or weighted-risk helper. It passes **404,174 checks**, including all
512 fit objective/gradient/box checks, 960 common-risk values, 1,872 contrast
summaries and 18,720 cross-inner-products. Original archive and frozen-result
bindings remain unchanged. [Audit receipt](../research/fixtures/continuous_localized_error_decomposition_independent_review_2026_09_13.json).

The focused suite passes **638 tests in each environment**: development
NumPy 2.4.6/SciPy 1.17.1 and installed-reader NumPy 2.1.3/SciPy 1.15.1, both
Python 3.11.5. The reader run uses an installed wheel outside the checkout,
without source PYTHONPATH, and completes the same 512 controls in 10.03 seconds.
Only the project wheel was replaced; no dependencies were downloaded.
The separate post-result analytical script also passes 24 manufactured tests
in each environment; it is a repository analysis script, not an installed
learner component.

Source/protocol bindings agree. Numerical results are **not bitwise identical**:
maximum population coefficient difference is 6.60e-5; maximum population
value/score/Hessian readback differences are 1.09e-5/9.89e-5/1.107e-3. The
same-data N/M coefficient difference is at most 1.72e-6. These differences
must not be described as strict-tolerance replay or universal portability.
The broad mechanism conclusion is retained; tiny projection differences
remain numerically unresolved. See the [verification record](../research/fixtures/continuous_localized_error_decomposition_verification_2026_09_13.json)
and [reader commands](../REPRODUCING.md#13-fixed-noisedesignregularization-diagnosis).

Primary report SHA-256:
`85be711c6abf6340ffda39518290452fe9b19e1b220dec646f99f7cc1ffafa4b`.
Protocol SHA-256:
`a0612a26aa1994a7f900c5144c7a53b41ff99ad3e367c8085ab3ab8a1b3aa64a`.

## Decision before changing the learner

Keep the learner and original tolerances unchanged. The next substantive
design task is a **derivative-relevant statistical error/variance-control
formulation**: quantify how noisy forward-label estimates are amplified into
scores and curvature, and prospectively compare a justified variance-reduction
strategy under matched work. Representation and regularization limitations
must remain explicit; this result does not justify simply removing the
penalties, widening the box, or increasing spline capacity.

This completes one bounded mechanism diagnosis. It does not qualify the
learned sampler, general learned-BASE target, real datasets, method superiority,
or a production release. No GPU/cloud/paid jobs or real data were used.
