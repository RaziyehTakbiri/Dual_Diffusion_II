# Prospective fixed-observation learnability comparison

2026-09-13. Frozen before any fits in this new comparison. This follows the
separate single FD7 curvature control; that control's outcome cannot choose
these settings. No previous result, likelihood law, method baseline, acceptance
tolerance or installed release is replaced. There are no GPU/cloud/paid jobs.

## Scientific question

Can a bounded smooth residual learn a useful likelihood correction from forward
simulation, without exact backward likelihood, score or Hessian training labels?
This is a **new fixed-observation simulator-supervised likelihood objective**,
not the original amortized random-observation BCE learner. It is also not the
previous oracle-jet interpolation with noisy values substituted. No conditional
endpoint sampler is integrated or evaluated in this experiment.

## Target and label law

Keep the earlier zero-BASE cap-one numerical law and two settings unchanged:
A `(theta,y)=(0.8,0.7)`, B `(2.5,1.4)`, selected-key probability `393217/524288`,
death/continuous rates 1, observation SD 0.5, contamination 0.1, horizon 1 and
macro grid `0,1/8,...,1`. The numerical suffix applies an additive-noise Heun
half-step, the **complete** capped birth/death CTMC with frozen coordinates,
then the second Heun half-step in every macro interval. A C birth draws a fresh
standard-normal mark. The learner's label code independently uses Poisson
uniformization, not the backward target's matrix exponential or Gaussian
likelihood mixture. A 64-potential-event-per-macro watchdog fails the run if
exceeded; it never returns a truncated path as a valid label.

For input `(u,x)` generate a forward suffix and set `Y=g_raw(y|X_H)`. This is
the known terminal noisy-half-thinning observation density, including the
whole-observation contamination. It is not an oracle value of `h_u(x)`.
Its conditional mean equals the unchanged numerical-grid likelihood.
Forward terminal states are indeed simulated for labels; learned conditional
endpoint draws are not. See the [derivation](LOCALIZED_LEARNABILITY_FORMULATION.md).

## Fixed design, samples and model

- At every active node, use the repeated state pattern E/O/C/C: design masses
  1/4, 1/4 and 1/2. Continuous coordinates are uniform on [-4.5,4.5]. This is
  controlled design-domain learning, not sampling from the posterior or training
  marginal. Positive coverage of atoms and the core is explicit.
- Seeds **11,29,47**. Training budgets **1,024 and 8,192 suffix labels per node**
  are nested prefixes of the same generated data. Each input has one suffix.
  Both methods receive exactly the same input/label arrays. No labels are
  regenerated for the larger budget or the other method.
- Use **4,096 separate validation labels per node/seed/setting**, with distinct
  design and suffix RNG namespaces. Validation is reporting only; it does not
  choose regularization, coefficients, stopping, capacity or a winning seed.
- There are **24 routes and 192 fits**, with **393,216 unique training suffixes**
  and **196,608 validation suffixes**: 589,824 total. Save the 48 paired raw
  datasets, all frozen fits, solver status and subsequent evaluation arrays.
- Representation: a quintic clamped B-spline on [-4.5,4.5], **32 uniform cells**.
  Tie the first three and last three raw controls, giving 33 continuous free
  coefficients; add two learned atomic coefficients, 35 total per active node.
  Endpoint first/second derivatives vanish, permitting C² constant tails.
  Interior smoothness is C⁴. Tails are bounded extensions, not accurate targets.
  This is a smaller statistical subfamily of local quintics, not the 256-cell
  oracle-jet construction. Its capacity is not certified by that experiment.

## Objective, bounds and optimization

Use each method's unchanged known raw-density offset `b`: propagated uncapped
association likelihood for G+R, terminal observation likelihood for DIR.
No capped backward likelihood is supplied to either method during fitting.
The forward-only implementation computes these offsets directly and is
independently checked against the older analytic model formulas.

Let `c` be the known contamination density and
`M=c+(1-epsilon)/(2*sigma*sqrt(2*pi))` the analytical observation-density maximum.
Fit physical residual coefficients `a` with `|a_j| <= A = 2*log(M/c)` by minimizing

`mean((exp(b+Phi*a)-Y*(b+Phi*a))/M) + (1e-4/2)*a'R*a + (1e-6/2)*||a||²`.

`R` is the mean-core integrated squared-curvature matrix, computed with four-point
Gaussian quadrature per cell (exact for its degree-six integrand in real
arithmetic). Atomic entries of `R` are zero. Optimize physical coefficients to
avoid scaling regularization with remaining time; store quotient coefficients
`theta=a/(1-u)` and retain the explicit linear gate. Terminal residuals are zero.
This per-node construction does not establish a continuous-time terminal limit.

The initial informal fixed quotient cap of 8 was rejected during pre-run review:
it would reproduce a known amplitude obstruction. The final `A` uses only the
observation-channel constants, not new fit or evaluation outcomes. The selected
single-observation density lies in `[c,M]` for both capped and uncapped reference
processes. Thus the physical canonical correction has a value bound `log(M/c)`;
the coefficient box has explicit factor-two slack. This does not prove accuracy
of a fixed finite spline family with tied boundaries or regularization.

Use L-BFGS-B in float64 from zero coefficients, at most **200 iterations**,
`ftol=1e-12`, `gtol=1e-7`, `maxls=30`, one numerical thread. No retries, warm-start
from another budget or post-outcome refinement. Retain non-converged solver
statuses, objective values, projected gradients and active bounds. The ridge
makes the finite affine problem strongly convex; stopping at a budget does not
prove that its unique minimum was reached. Regularization changes its target.

## Evaluation and interpretation

Freeze **all 192 fits before importing/querying the independent backward target**.
Save the freeze record and its hash. Then evaluate physical likelihood, score
and Hessian at the unchanged 256 core probes on [-4,4], the eight active nodes,
the exact terminal and both atoms. The target provides no fitting label, tuning
decision or stopping criterion. Log target values are not used to clip a model.

Report all seeds, budgets, settings and methods: train/validation likelihood
risk relative to the zero-residual baseline; paired validation risk change with
descriptive stratified standard error; all fixed-probe error maxima/RMS/failures;
atomic and EMPTY-centered errors; bounds and solver diagnostics. Preserve the
existing approximation values `(atol,rtol)`:

- value `(2e-6,2e-5)`;
- score `(2e-5,2e-4)`;
- Hessian `(1e-4,1e-3)`.

They are deterministic diagnostic thresholds, **not** finite-sample success
promises. Report seed means/ranges descriptively; no superiority test, confidence
claim, power adequacy or posterior-law guarantee is inferred. Better quasi-risk
alone does not guarantee accurate scores or Hessians. The sample budgets and
coarser smooth family intentionally expose the finite-data bias/variance issue.

## Execution

One local CPU child with a **1,200-second parent deadline**. Write protocol and
source hashes before generating labels; save each dataset and frozen route;
preserve partial output if anything fails. The learner and its label module
import no evaluation oracle. No actual training comparison runs before review.
The old neural learner, forward model, accepted tolerances, archives and sampler
remain unchanged. No more curvature arms are added to either completed protocol.
