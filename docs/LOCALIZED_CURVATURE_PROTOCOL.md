# Prospective score-only curvature improvement

2026-09-13. This protocol is declared before the new target-based comparison.
It authorizes one fixed local construction-layer comparison after independent
prototype review. It does not authorize a sampler experiment, model promotion,
GPU work, real-data access, or a change to the scientific objective.

## Question and fixed change

Can a sixth-order, seven-point derivative of the **same supplied scores** reduce
the curvature-approximation error of the existing localized representation?
Only the shared knot-curvature estimator changes. The prior FD5 implementation,
prior results, quintic Hermite–Bézier primitive, targets, baselines, knot locations,
collars, probes, and acceptance tolerances remain unchanged.

The new primary arm is `VS_FD7_SIXTH_ORDER_SCORE_DIFFERENCES`. Its construction
receives exact residual values and scores at 257 fixed knots; it does not receive
oracle Hessian labels. An oracle routine may compute derivatives together
internally, but only values and scores enter the new construction. No extra
score locations, adaptive stencil choices, stochastic fitting, numerical linear
solve, or resolution selection is introduced.

## Exact stencil definition

For uniform knots `z_i = z_0 + i h`, use seven consecutive scores. At knot `i`,
the stencil starts at `j = min(max(i-3,0), n-7)` and its evaluation position is
`r = i-j`. Thus the first and last three knots use shifted boundary stencils;
all other stencils are centered.

Let `L_k` be the degree-six Lagrange cardinal polynomial for integer nodes
`0,...,6`. The dimensionless weights are `w_k = L_k'(r)`. They are derived by
exact rational arithmetic:

```
w_r = sum_{m != r} 1/(r-m)
w_k = product_{m != k,r}(r-m) / product_{m != k}(k-m),  k != r.
```

They satisfy `sum_k w_k k^p = p r^(p-1)` for degrees `p=1,...,6` and have zero
sum for `p=0`. The centered weights are `(-1,9,-45,0,45,-9,1)/60`; the first-knot
weights are `(-147,360,-450,400,-225,72,-10)/60`. All seven rational stencil
vectors are recorded in the numeric protocol, including every boundary rule.

The implementation evaluates `sum_k w_k (score_{j+k}-score_i)/h` with a
compensated scalar summation. Subtracting the common score exploits the exact
zero-sum identity and makes constant-score inputs return zero. Conversion of
rational weights to floating point is still ordinary numerical computation;
this is not an exact-arithmetic or outward-rounded error certificate.

Under a C7 score and exact labels, this estimates its derivative with `O(h^6)`
truncation error, including the fixed boundary stencils. For a residual quotient
`q`, this assumes `q` is C8. It does **not** make a quintic interpolant sixth-order
accurate in its Hessian. Exact-jet quintic interpolation retains the core orders
`O(h^6)`, `O(h^5)`, and `O(h^4)` for value, score, and Hessian under C6 regularity.
An `O(h^6)` curvature perturbation contributes, respectively, `O(h^8)`, `O(h^7)`,
and `O(h^6)` on a core cell. No corresponding target-accuracy claim is made for
the fixed collars or constant tails. Noisy score errors can be amplified by
`1/h`; the present exact-label construction does not resolve learnability.

## Unchanged target and geometry

- Two cap-one, zero-BASE scenarios: `(theta,y)=(0.8,0.7)` and `(2.5,1.4)`.
  Selected-key mass is `393217/524288`, death and continuous rates are 1,
  horizon is 1, observation SD is 0.5, and whole-observation contamination is 0.1.
- The independent target is the actual ideal **numerical macro-grid** likelihood
  at `u=0,1/8,...,1`, not the exact continuous-time likelihood. The latter remains
  a separately labeled diagnostic and is never substituted for the grid target.
- Both baselines are mandatory: G+R uses the uncapped reference likelihood at
  `u`; DIR uses its terminal-observation value. Consistent raw observation-density
  conventions are retained. No new terminal gate or gauge convention is selected.
- Core is `[-4.5,4.5]`, with exactly **256 cells and 257 uniform knots**, matching
  the previous 256-cell construction. Evaluation retains the same **256 uniform
  coordinates on [-4,4]**, separated from every knot by more than `1e-12`.
  These are deterministic approximation probes, not statistical held-out data.
- Width-one C2 collars extend to `-5.5` and `5.5`. They connect each core endpoint
  jet to the same endpoint value with zero score/Hessian, followed by constant
  tails. The residual is `(1-u)` times its interpolated quotient; supplied
  residual jets are divided by that gate exactly once during construction.
- EMPTY and OTHER corrections are exact oracle constants, explicitly not learned.
  Terminal residuals are exact zero and consume no labels. No interpolation
  between macro nodes, midpoint conditioning phase, or sampler adapter is added.

There are exactly **four new routes**: two scenarios × two baselines, comprising
**32 active continuous profiles** and four terminal-zero controls. Each route
has 2,048 active probes and 256 terminal probes. There are no alternative new
arms, resolution sweeps, retries, or post-result adjustments in this comparison.

## Archival controls and unchanged acceptance

The only comparison archive is
`research/fixtures/continuous_localized_residual_cpu_2026_09_13/report.json`,
with SHA-256
`5cfc1a95284ce1149dd3211799666988b8b0422807affec2961c26264ab4c099`.
Its protocol SHA-256 is
`de45c892a45e67ccee208bb59077c58fe55e5bed9993fd5f876729db00ccc20e`.

For each scenario/baseline, select the already archived **256-cell** FD5 and
VSH routes. Reevaluate their preserved physical value/score/Hessian arrays
against the same current numerical oracle. Do not reconstruct or refit those
controls, change their coefficients, or rerun a resolution selection. The VSH
control originally used extra oracle-Hessian supervision; it is not a primary
score-only result or an undeclared fallback.

Before comparison, verify the archived target arrays and atomic values against
the current oracle, allowing only the fixed roundoff identity check
`atol=rtol=2e-13`. Record whether continuous arrays are bitwise equal and their
maximum discrepancy. This identity check is **not** a replacement or relaxation
of any approximation tolerance. Archive hashes, route digests, physical-array
digests, and coefficient digests bind the saved controls being compared.

| Quantity | Absolute tolerance | Relative tolerance |
| --- | ---: | ---: |
| Physical log likelihood | 2e-6 | 2e-5 |
| Coordinate score | 2e-5 | 2e-4 |
| Coordinate Hessian | 1e-4 | 1e-3 |

The unchanged pointwise rule is `abs(error) <= atol + rtol*abs(target)`. Report
maximum/RMS errors and all failure counts for every new and archived route,
including failures. Report knot interpolation discrepancies, relative likelihood
error, EMPTY-centered log-potential and E-to-C rate-ratio errors. Preserve all
raw new residual value/score/curvature arrays, Bézier controls, baseline and
physical evaluation arrays, oracle targets, and whole-projected-state bounds.

The global envelope includes continuous core, both collars, constant tails and
atomic corrections. Its meaning remains **real-arithmetic coefficient/range
bound**, not a floating-point rejection/thinning certificate. Passing finite
core probes cannot establish tail accuracy, statistical recovery, endpoint-law
accuracy, or general hybrid-model qualification.

## Prototype, execution and reproduction

Implementation:

- [Independent FD7 estimator](../src/heterodiff/models/localized_score_curvature.py)
- [Fixed comparison command](../src/heterodiff/experiments/continuous_localized_curvature.py)
- [Unchanged localized formulation](LOCALIZED_RESIDUAL_FORMULATION.md)
- [Previous protocol](LOCALIZED_RESIDUAL_PROTOCOL.md)

First inspect the fixed specification without evaluating scientific targets:

```bash
python -m heterodiff.experiments.continuous_localized_curvature --inspect
```

After independent prototype review and the one-run authorization, use an
**absent** output path beneath an existing parent:

```bash
python -m heterodiff.experiments.continuous_localized_curvature \
  --archive-report research/fixtures/continuous_localized_residual_cpu_2026_09_13/report.json \
  --output /tmp/continuous-localized-fd7-approved-run
```

The command validates the fixed archive, then launches one local CPU child with
one numerical thread and a **300-second parent deadline**. Protocol and source
hashes are recorded before new constructions. Route records are saved as each
finishes, followed by a complete report; partial failure output is preserved.
There are no automatic retries. A direct API call has only the deadline callback
supplied by its caller and is not the supervised reproduction path.

No GPU, cloud job, network request, package installation, real data, training,
endpoint sampling, or modification of prior scientific artifacts is requested.
No measured result is asserted by this prospective document.
