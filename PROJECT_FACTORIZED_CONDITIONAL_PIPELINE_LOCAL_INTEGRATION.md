# Factorized conditional learner and sampler: local integration

Date: 2026-09-08  
Scope: new mixed-key scientific amendment, local synthetic CPU qualification only  
Status: COMPLETE for the requested bounded local integration milestone

The user requested connection of the factorized state/reference, smooth target,
noisy observation law and energy model to a full conditional learner and sampler
before GPU work. The new path now performs actual BASE optimization, generates
independent learned-BASE trajectories, optimizes the conditional classifier,
and samples through a fixed conditional physical potential. It does not read
datasets, launch jobs or alter the accepted historical CPU release.

## Connected computation

1. Explicit synthetic TRAIN configurations enter the amended target
   `(1-alpha) Q_lift + alpha Pi_N`. Only continuous log-value fibers receive
   training jitter; all discrete keys and zero-dimensional atoms remain exact.
2. BASE examples are corrupted by the **reference** process: exact OU transition
   formulas and the complete capped birth/death CTMC, subject to finite RNG,
   arithmetic and declared resource limits. This is not learned Heun corruption.
3. BASE receives real AdamW updates for the relative-score/jump-flux objective.
   The continuous term is `gamma_C sum(0.5 V_r^2 + V_rr - r V_r)` over 1D fibers.
   The jump term is `lambda_J Lambda_s [exp(V(y)-V(x)) + V(y)-V(x)]` for one
   normalized reference proposal, retaining the unnormalized exit rate and the
   positive linear sign. BASE time is uniform on the strict active interval.
4. Freeze BASE. Two independently keyed **whole learned-BASE paths** start from
   `Pi_N`. Each terminal state generates an observation through the same amended
   half-thinning/noise/contamination law. Joint and product examples share the
   first path's interior state, time, task and static context; only the product
   observation comes from the second path. No TRAIN endpoint lookup substitutes
   for generation, and BASE is not retrained during these conditional updates.
5. Conditional training uses balanced joint/product logistic risk with a real
   metadata-aware observation encoder and independent observation-only nuisance.
   `reverse_time=None` samples uniform `q(u)` on the entire strict reverse
   interval, including the clean hold. Each drawn time is inserted into both
   path grids **before** generation. This changes the numerical path law and
   work; family/time identities and actual step counts explicitly record it.
   Fixed-time diagnostic training has a different law identity. Neither law
   uses an extra inverse-time-density multiplier for its own expectation.
6. Snapshot the trained physical potential. G+R uses
   `V + log(h_tilde) + gated residual`; DIR uses `V + log(g) + gated direct term`.
   The cubic residual gate appears exactly once. Nuisance never enters the
   physical drift, jump rates or initial distribution.
7. Conditional initialization samples the **cap-correct** `Pi_N h_tilde` or
   `Pi_N g` reference posterior, then applies bounded residual-only rejection.
   It does not include BASE energy or nuisance. The retained posterior conditions
   the combined ancestor/unobserved count on the scientific cap. Overflow uses
   its count-posterior law. Full-support normalization is not confused with
   efficient unconditional rejection on rare observed keys.
8. Learned reverse sampling uses Strang splitting, stochastic Heun motion and
   repeated midpoint-frozen birth/death thinning. Count/metadata edits use the
   complete reference key law, never numeric projection or a finite vocabulary.
   Duplicate occurrences carry their own noise/gradient indices through sorting.
   During the clean hold, the state is copied with no model/RNG calls; the BASE
   physical-time extension is also constant. Resource or representability failure
   refuses the path, not a clipped/retried/partially returned success.

## Implementation entrypoints

| Component | Local source |
|---|---|
| Differentiable guide and cap-correct initializer | `src/heterodiff/theory/factorized_association_guide_torch.py` |
| Actual BASE objective and update | `src/heterodiff/experiments/factorized_base_training.py` |
| Observation encoder, nuisance, conditional risk and snapshots | `src/heterodiff/experiments/factorized_conditional_training.py` |
| Reference and learned hybrid processes | `src/heterodiff/processes/factorized_hybrid_sampler.py` |
| Independent population, full-time updates and conditional path | `src/heterodiff/experiments/factorized_conditional_pipeline.py` |

The [learner note](PROJECT_FACTORIZED_CONDITIONAL_LEARNER.md) and
[guide note](PROJECT_FACTORIZED_GUIDE_AND_INITIALIZER.md) specify public APIs.
The [end-to-end qualification note](PROJECT_FACTORIZED_LOCAL_QUALIFICATION.md)
records the synthetic fixtures and actual optimization/sampling checks.

Per primary method, the new graph has 96,705 BASE parameters, 96,705 conditioner
parameters, 51,200 observation-encoder parameters and 53,313 independent nuisance
parameters: **297,923 total**, of which **201,218** are trained conditionally once
BASE is frozen. G+R and DIR share these graph sizes; differing guide evaluation,
matching, trajectory-generation and initialization work must still be counted.
This is not adoption of F104 cost weights or the old finite-type parameter freeze.

## What this qualifies, and what it does not

This qualifies a bounded **local CPU implementation** using real objectives,
gradients, updates and generated synthetic configurations in both amended domains.
FP32 learned graphs coexist with FP64 analytic guide/risk and sampler arithmetic.
Exact metadata is never stored as a continuous coordinate. Materialized raw-F105
scalars can have finite log/exp round-trip error; that error is measured, not
described as a bitwise lossless scientific transform.

The uncapped auxiliary guide is not the capped reference semigroup and not the
learned-BASE conditional function. Learned paths are numerical approximations;
finite PRNG output is not ideal continuous entropy. A bounded neural class and
short optimization do not prove recovery of `Q0` or the population optimum.
Starting BASE at `Pi_N` does not prove finite-horizon terminal equilibration.
The fixed-observation global jump envelope can be expensive for rare keys/large
observations. Small tests are not a uniform convergence, derivative/path-KL,
large-count throughput or numerical roundoff certificate. No old finite-type
certificate or 235-test Databricks receipt is automatically transferred.

Numeric scientific settings, noise/regularization sensitivity, production-scale
matching/work envelopes, current-release packaging, CUDA parity/performance,
real-data admission/splits, complete matched budgets and cost/storage limits
remain open. No 4,096-update training campaign or scientific result is claimed.

## Verification and preserved state

Final main-agent verification: **567 selected local CPU tests passed**, with
zero failures, errors, skips or warnings in these final runs:

- **339 passed in 8.87 seconds** across the nine factorized state, law, energy,
  guide, BASE, conditional learner, sampler and integration suites. This includes
  the independent 17-case end-to-end suite and 8-case BASE objective suite.
- **228 passed in 339.02 seconds** across nine adjacent historical local suites:
  learned hybrid sampler, hybrid conditional learner, conditional loss and
  pipeline, joint/product population, F105 checkpoint validation, energy training
  view, explicit-device trainer and observation adapter.

The counts are disjoint by test file. Agent-focused runs overlap these final
runs and are not added again. Python 3.11.5 / CPU Torch 2.12.1 was used; this is
not the Databricks Python 3.12 runtime, a GPU test or a full repository-suite claim.
Static analysis of all five new modules and their five new test files passed.
The known-law checks cover a small capped count CTMC against its matrix
exponential, exact forward OU, deterministic Heun drift-order refinement and
a correctly Brownian-coupled coarse/fine OU RMS comparison. Those are bounded
diagnostics, not a general learned-model convergence proof.

Both domains and both primary methods perform three actual BASE and three
conditional optimizer updates in the synthetic qualification. The tests
exercise the new direct sampler/metric seam with two generated draws and the
existing raw F105/CKS estimator, not the full 128-group by 64-draw checkpoint
campaign. Discrete fields remain exact and scalar round-trip errors are finite
and explicit. The independent reviews confirmed objective signs, single rate
weights, full-time risk construction, initializer/physical separation and
297,923 unique parameters without shared parameter storage across components.

The final integrity check found all **323 accepted CPU source payloads unchanged**.
The accepted manifest remains SHA-256
`9a7d815ada69a7405552ac885b229e13f63eb24ff1ed6e57d0730734452ed5ff`;
the CPU lock remains
`c6fa5d600cd2810c40ae47d5eeeba341e0467c4c75dd7c7d310cf3628ab6349f`.
The new modules are intentionally outside that accepted release.

The timetable's bounded integration milestone is marked COMPLETE without adding
another checkbox or closing compound scientific/production tasks. Current totals
remain **61 checked / 102 open / 163**, **31 fields open / 141 closed**, and
**8 blockers open / 4 closed**. Formal Tests 28/29/30 remain OPEN/OPEN/PENDING;
scientific results remain 0/4. No paid/cloud/GPU job, real-data access, commit or
push was performed. The accepted 323-source CPU manifest and CPU lock are
preserved unchanged.
