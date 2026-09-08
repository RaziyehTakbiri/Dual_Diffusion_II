# Conditional training pipeline — local integration checkpoint

Date: 2026-09-07. **COMPLETE for the bounded local components below; the full
scientific training pipeline remains OPEN.** The user authorized local code and
plan work without paid jobs. No real data, cloud compute, CUDA execution, or
scientific outcome was used.

**Later same-day successor:** the numerical hybrid sampler, concrete trainable
observation/nuisance proposal and actual sampled-configuration integration
are now implemented; see the
[new milestone](PROJECT_HYBRID_SAMPLER_AND_OBSERVATION_INTEGRATION.md). The
finite-law tests and remaining-work statements below describe this earlier
checkpoint. Production real-domain definitions/adoption and qualification
remain open under the latest plan.

## What is now implemented

| Component | Completed implementation | Important boundary |
|---|---|---|
| Candidate-base joint/product population | Two independently addressed initial-to-u-to-terminal branches within the same domain/task/context/time; terminal observation draws; product pairs use the first latent and the second observation | Finite, time-homogeneous synthetic generator and finite observation kernel only; not a general learned hybrid simulator |
| G+R and DIR classifier loss | Actual equal-prior joint/product logistic objective, method-specific supplied baseline, one cubic clean-hold gate, observation-only nuisance branch, explicit unnormalized rational sampling-law weights | Production observation encoder, nuisance architecture and sampling laws are not selected by this implementation |
| Optimizer connection | Real FP32 forward/backward and AdamW updates through the original energy graph's additive training view | Short local synthetic schedules; not CUDA qualification or full scientific training |
| F105 checkpoint validation | Actual CPU64 factory scores for 128 ordered groups, exactly 64 supplied configurations per group, exact aggregation and earliest tied checkpoint selection | Certifies scoring of supplied configurations, not their generation, ground truth, admission or full campaign history |
| Checkpoint evidence | Retains the actual 128 score-factory objects in memory and binds them to run, update, model state and validation roster | Serialized evidence is a compact audit projection, not reconstituted factory objects or a hash of the complete optimizer archive |

Implementation:

- [Finite population](src/heterodiff/experiments/two_domain_joint_product_population.py).
- [Conditional classifier and loss](src/heterodiff/models/two_domain_conditional_training_loss.py).
- [Optimizer and checkpoint integration](src/heterodiff/experiments/two_domain_gpu_training.py).
- [F105 checkpoint adapter](src/heterodiff/experiments/two_domain_f105_checkpoint_validation.py).
- [Combined synthetic test](tests/unit/test_two_domain_conditional_training_pipeline.py).

## Mathematical and implementation checks

For a supplied finite candidate generator Q, initial law pi and terminal
observation kernel K, the test population computes
`p_u = pi exp(u Q)` and `H_u = exp((S-u) Q) K`. The joint table is
`J(x,a) = p_u(x) H_u(x,a)`; the product table is `p_u(x) p_A(a)`.
Both branches use the same declared task/context/time. No cross-context batch
shuffle replaces independence. The finite jump-tilt helper implements
`Q_phi(i,j) = Q_0(i,j) exp(V(j)-V(i))` off the diagonal, without rate clipping.

The loss is
`0.5 mean(w_J softplus(-logit_J)) + 0.5 mean(w_P softplus(logit_P))`.
The G+R baseline is the supplied propagated-guide log value; the DIR baseline
is the supplied terminal-likelihood log value. Both use the single declared
cubic gate and bounded conditioner. The nuisance depends on observation/task/
context and is excluded from the physical log-potential. Supplied baseline
values are detached: this adapter does not implement or certify their spatial
derivatives for the still-missing continuous sampler. Rational weights are
rounded directly to nearest-even FP32 and are not self-normalized; their exact
law declarations remain available for the caller to retain.

The finite population uses the existing matrix-exponential oracle, including
its documented floating-point repairs. It does not claim exact real-valued
transition probabilities. Purpose-separated PCG64 addresses establish replay
and address separation, not a mathematical IID guarantee. Fixed interior-time
test fixtures do not establish a production time law with full open-interval
support.

The end-to-end test uses deliberately synthetic feature/nuisance choices and
finite supplied validation configurations. It exercises both primary methods
and the PhysioNet 112-dimensional / Retail 10-dimensional interfaces. Its finite
model-weighted validation draw law is not a learned hybrid reverse trajectory
or an authenticated conditional generator. Tiny optimizer and scoring tests
must not be presented as scientific training, empirical model quality, or
compliance with the complete 4096-update checkpoint campaign.

The F105 bridge preserves the actual metric-domain identifiers (`R3-PHYS`,
`R4-RETAIL`) and records their mapping to the registry domain identifiers.
Review found that the old frozen F144 structural helper computes its expected
factory integrity using the registry identifier instead. The additive bridge
does not fabricate a replacement factory digest: it reports that historical
helper incompatibility explicitly. The frozen metric, training plan and source
records remain unchanged; a production consumer needs an explicit compatible
successor before claiming that complete route is satisfied.

## Verification and preserved evidence

**954 tests passed in 70.42 seconds**, with no failures or skips reported,
across 19 focused/adjacent suites: the optimizer, FP32 energy view, finite
population, classifier loss, F105 checkpoint bridge, combined pipeline,
budget amendment, supplied-input adapters/runtime facts, both admission
preflights, F061/F104/F105, baseline registry/contracts/B06 and frozen training
plan. Static checks pass for the six new implementation modules and seven
associated test modules; the tracked diff whitespace check is clean.

The new combined pipeline contributes **16 passing cases**: four checks for
each of the two methods in each domain, with one real AdamW update per fixture.
It covers real factory scoring, current-model dependence, exclusion of nuisance
from validation weights, checkpoint-state/update mismatch refusal and
inspection-only serialization. Separate equation tests check the equal-prior
formula, clean-hold, exact RN rounding and finite Bayes-risk oracle; population
tests check finite-table agreement, branch addressing/replay and immutable
bindings. No test-suite duration is used as a training-cost estimate.

This run used local **Python 3.11.5 and CPU Torch 2.12.1**, not Databricks Python
3.12 or a CUDA device. An independent source/plan review accepted the bounded
scope and separately ran 118 focused cases. Review corrections included
immutable population/time bindings, clean-hold agreement, exact RN midpoint
rounding and correct PhysioNet112/Retail10 test labels.

Integrity check: all **323 accepted CPU source payloads** match their previous
content hashes and sizes. The CPU manifest remains
`9a7d815ada69a7405552ac885b229e13f63eb24ff1ed6e57d0730734452ed5ff`
and the CPU dependency lock remains
`c6fa5d600cd2810c40ae47d5eeeba341e0467c4c75dd7c7d310cf3628ab6349f`.
The timetable was recounted at **61 checked / 102 open / 163 total**.

The accepted 323-file CPU release and its dependency lock are retained. These
additive modules are not part of that installed release, so the earlier
Databricks success does not certify them. No new Databricks run or paid cluster
is requested here, and no old one-shot candidate/custody workflow is revived.

## What remains before full training

1. Implement and test the scalable learned-base hybrid trajectory sampler and
   continuous observation kernel; integrate the initializer, guide/residual,
   continuous gradients and jump rules with the actual conditional generator.
2. Specify the production initial/task/context/time sampling laws and
   observation encoder, and choose/count the nuisance architecture. The
   current B06 parameter count covers the base plus conditioner, not these new
   trainable choices. Include any encoder and nuisance training work in the
   prospective matched-compute amendment; nuisance evaluation is not inference
   work when the sampler uses only the physical potential.
3. Connect authenticated generated draws and admitted truth to the new F105
   adapter, with a compatible production checkpoint-validation consumer.
4. Complete non-primary budget mappings and obtain data/split readiness,
   selected GPU/runtime facts, bounded qualification authority, spending and
   storage limits before any paid campaign.

These remaining obligations are actual model/data/resource work, not a request
for Docker/ECR setup. The local equation and metric components above are marked
complete without closing a compound timetable task. Counts remain **61 checked /
102 open / 163**, **25 fields open / 147 closed**, **8 blockers open / 4 closed**;
Formal Tests 28/29/30 remain **OPEN / OPEN / PENDING**, and results remain **0/4**.
