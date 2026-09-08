# Learned hybrid sampler and observation-model integration

Date: 2026-09-07. **Completed local implementation milestone; scientific
training and production adoption remain open.** User authority covers local
code, plan updates and synthetic CPU tests, without paid jobs.

## Completed parallel work

| Component | What now runs | Scope |
|---|---|---|
| Learned hybrid trajectories | Continuous stochastic-Heun updates, repeated birth/death/replacement thinning, bounded initialization and exact purpose-keyed replay | Local numerical implementation, not GPU/production qualification |
| Observation model | Trainable occurrence-preserving 64-channel encoder and a separately parameterized observation-only nuisance encoder/head | Concrete executable proposal; not an adopted real-domain configuration |
| Connected training path | Independent learned-base joint/product trajectories, real G+R/DIR loss, live encoder/nuisance/residual gradients and AdamW update | Explicit synthetic observation and time laws |
| Conditional validation | Conditional initialization, total neural potential, actual hybrid terminal samples and genuine 128-group/R64 F105 scoring | Synthetic chart and invented truth; not real-data admission or scientific results |
| Work accounting | Separate two-trajectory-per-example population-generation count and actual query-refined step diagnostics | Prospective budget amendment, not an approved ceiling or cost estimate |

Code: [hybrid sampler](src/heterodiff/processes/learned_hybrid_training_sampler.py),
[observation design](src/heterodiff/models/two_domain_observation_training_design.py),
[connected model interfaces](src/heterodiff/experiments/hybrid_conditional_training.py),
and [combined tests](tests/unit/test_hybrid_conditional_training.py).
The preferred architecture, parameter formulas and training-law choices are
specified in the [review-pending design proposal](PROJECT_TWO_DOMAIN_TRAINING_DESIGN_PROPOSAL.md).

## Mathematical connection

The reverse continuous drift is `-gamma_C(s) r/2 + gamma_C(s) grad Psi`, with
`s=S-u`. The same scalar `Psi` tilts reference jump rates by
`exp(Psi(y')-Psi(y))`. It is `V` for candidate-base simulation, and
`V+log(h_hat)` for conditional simulation. The classifier nuisance never enters
either physical potential. The residual uses the existing cubic clean-hold
gate once. The initialization target is `Pi_N*h_hat(0)`: **base V is excluded
from that initial tilt**.

Each paired training example starts two independently addressed reference
configurations and two learned-base paths at the same task, context and time.
The joint uses branch-one latent/observation; the product uses that same latent
and branch-two observation. Raw task/context identities are checked before
the equal-prior weighted logistic loss. Detached raw observations feed live,
trainable encoders; the nuisance owns independent parameters and no latent or
diffusion-time input. Exact raw identities are retained even when bounded FP32
features coincide.

The numerical path uses Strang continuous-half/jump/continuous-half splitting,
same-noise Heun predictor/corrector and repeated thinning proposals. Schedule
and hold boundaries are explicit grid points. An arbitrary requested interior
time is inserted by `refined_for_query`, never snapped. Active intervals use
the midpoint-owned schedule coefficient at both endpoint drift evaluations:
this is a declared one-sided numerical successor, not the old pointwise
coefficient convention. Inserting the query creates an explicitly different
numerical approximation; the plan reports its
actual grid/step count; it is not silently called the unchanged frozen
256-step law. Fully held intervals make no model or random calls. Probability,
rate, coordinate and proposal limits fail explicitly without clipping or
returning a partial path as success. Initial rejection also refuses acceptance
probabilities below the shared supported finite-RNG floor.

Global potential bounds, finite random streams and numerical exponentials are
not interval certificates, proofs of mathematical independence, or completed
coupled-step qualification. This remains a numerical successor proposal.

## What the end-to-end test actually proves

The four cases cover both primary methods and both F105 metric interfaces.
Each executes **one** real optimizer update on 16 paired examples, generated
from **32 complete learned-base trajectories**, followed by **8,192 distinct
conditional trajectory addresses** (128 groups times 64 draws). Across the
four cases, that is 128 base and 32,768 conditional trajectories. Tests check
that the conditioner, visible encoder and independent nuisance parameters
change, the caller's original model remains untouched, all 128 genuine score
records bind to the checkpoint, and serialization retains their audit rows.
The fixed initialized base is a candidate model, not a trained scientific base.
The one-update fixture is not a reusable multi-update population scheduler;
such a scheduler must include update/example occurrence in its stream keys.

The explicit synthetic sensor has a continuous angle `a` with density relative
to the uniform angle measure `g(a|y)=1+alpha*(-1)^n*cos(a)`, with `alpha=1/2`.
Its positive common support avoids using count-revealing full-event Gaussian
observations as a substitute for the manuscript's positive dominated branch.
The reference count birth/death semigroup computes the propagated guide;
that guide is not asserted equal to the learned-base conditional expectation.
Sensor parameters and arrays are immutable, and repeated exact-time oracle
values are cached without changing the formula.

The output chart is deliberately one-dimensional: each occurrence maps `x`
to positive `exp(x)` and fixed invented event metadata through the existing
binary64 F105 constructors. Overflow/underflow stops rather than projecting
or clipping. This preserves occurrence count and gives legitimate synthetic
PhysioNet112/Retail10 scoring inputs. It is **not an inverse of the F105
embedding**, nor a decoder or observation kernel for the actual two datasets.
The fixture has cap 1 and a short grid; separate sampler tests exercise larger
counts, duplicates, crossings, replacements and multiple jumps. No scalability
or model-quality claim follows from this fixture.

## Verification and preserved state

**1,015 tests passed across 22 focused/adjacent suites**, in three disjoint
runs: 983 tests across the earlier integration/admission/metric/sampler/design
suites; all 11 connected-model tests, including the four full hybrid/F105
cases; and 21 budget-amendment tests. The first two runs took 61.28 and 223.43
seconds respectively. There were no failures or skips in these selected
runs. Static checks pass for the added sampler, observation design, connected
model and budget code/tests, and the tracked whitespace check is clean.

All checks use local Python 3.11.5 and CPU Torch 2.12.1, not Databricks or CUDA.
Independent review checked the sampler equations, observation/nuisance boundary,
initial tilt, synthetic sensor/chart, query-refinement disclosure and error
paths. Test duration is not a run-cost estimate.

All 323 accepted CPU source payloads retain their recorded hashes and sizes.
The previous manifest and CPU lock are unchanged. These additive modules are
outside that accepted release: its earlier Databricks receipt is not evidence
that they are installed or GPU-qualified. No new Databricks run, Docker/ECR,
retired custody route, dataset access, commit, push or paid job occurred here.

## Remaining decisions and next implementation

1. Finalize and review real-domain generative charts, legal visible-observation
   schemas and normalized association/observation kernels. Adopt the proposed
   encoder/nuisance and task/context/time approximation only through an explicit
   prospective configuration revision; existing F064/F065/F070/F071 values
   remain historical-reference values.
2. Qualify the numerical sampler and batched/device-local production path,
   including coupled-step error, initialization limits, actual work/memory and
   unique multi-update stream addressing. The present bridge is CPU-only.
3. Complete the matched-compute amendment. At 16 paired examples, 4096 updates,
   256 nominal steps and 256 seeds, paired base generation adds
   **8,589,934,592 logical reverse-step events per primary method/domain**,
   separately from the same-sized mandatory validation subtotal. Query
   refinement, rejection, jump proposals, gradients, encoders, nuisance and
   oracle work still need appropriate accounting. Neither subtotal is a total
   budget. Non-primary mappings, weights and hard limits remain open.
4. Connect admitted real inputs/generated draws to the compatible production
   F105 checkpoint consumer, then perform bounded GPU qualification after
   hardware, spend/runtime and storage limits are supplied. Data admission,
   F061 feasibility and actual snapshots remain separate unresolved inputs.

The timetable and ledger mark this bounded milestone **COMPLETE**. No compound
task, scientific field, blocker or formal test closes: **61 checked / 102 open /
163 total**, **25 fields open / 147 closed**, **8 blockers open / 4 closed**;
Formal Tests 28/29/30 **OPEN / OPEN / PENDING**; scientific results **0/4**.
