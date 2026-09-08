# Domain support, observation proposal and workload review

Date: 2026-09-07. **Completed bounded local implementation and review; full
real-domain definitions and budget adoption remain open.** No cloud/GPU job,
dataset access, package download or scientific campaign was launched.

## Outcome

Three parallel components are now implemented:

| Component | Completed locally | What it does not establish |
|---|---|---|
| Domain representation | Exact F105 semantic-image inverse/audit and explicitly supplied discrete-key/scalar-fiber charts | A complete production schema or permission to round/project arbitrary metric vectors |
| Alternative observation integration | Normalized affine association sampler, retained/overflow encoding, first-coordinate likelihood/guide gradients, and conditional-model/sampler connection | Adoption of a replacement for the frozen half-thinning identity kernel |
| Workload accounting | All-22-role semantic mapping and symbolic sampler, rejection, neural/encoder and F105 operation counts | Executable non-primary algorithms, measured operation weights, approved GPU-hours or spending/storage ceilings |

The implementation exposed a genuine mathematical decision. This is not an
additional Databricks setup prerequisite, and the accepted CPU installation
and its source-bound receipt remain valid for their original scope.

## Two incompatible assumptions must not be hidden

First, the F105 vectors are an **injective scoring representation**, not an
open Euclidean generative state. One-hot variables, missingness masks, exact
timestamps, UTF-8 codes and integer quantities cannot be diffused as arbitrary
Gaussian coordinates and then rounded back without changing the model law.
The [chart proposal](PROJECT_TWO_DOMAIN_GENERATIVE_CHART_PROPOSAL.md) implements
exact semantic image checks and small supplied fibers with fixed discrete
keys. It does not pick a production subset or discard unsupported records.

A literal PhysioNet flattening already needs 319,791 strata, exceeding the
current 4,096-type implementation bound. Retail's atomic time/string/quantity
support is much larger. Factorized discrete laws and compatible sampling,
balanced jump rates, architecture and capacity rules are still needed.
Recorded decimal atoms versus continuous latent measurements is itself an
explicit target-model choice, not settled by a logarithmic transform.

Second, the clean real-data observation rule is already defined as
`OCCURRENCE_INDEPENDENT_HALF_THINNING_IDENTITY_V1`: retain each occurrence with
probability 1/2 and leave its fields unchanged. Those closed definition fields
remain historical/current definitions; this work does not replace them.
For continuous marks, a retained exact value has positive point mass under
that conditional kernel but zero mass under an atomless Gaussian observation
reference. Adding a positive Gaussian contamination component does not remove
the singular component. In addition, half-thinning alone cannot produce an
observation not contained in the source state, so universal positive support
does not hold. F033/F034/F053/F054 remain open.

**The next scientific decision is a coherent target/reference/observation
amendment, not a GPU launch.** Two directions require explicit comparison:

- Preserve exact-record identity observations: use a justified atomic or
  singular-support modeling/theorem route, with corresponding reference and
  training changes. This is not automatically compatible with the existing
  smooth guide.
- Preserve a mixed discrete/continuous latent diffusion with a smooth
  dominated likelihood: define a scientifically justified measurement/noise
  model and an explicit successor to the current observation rule, alongside
  factorized discrete metadata and any measurement quantization semantics.

The second direction is the preferred investigation if the scientific target
is continuous latent measurements. It is **not adopted here**. Noise levels,
clutter, contamination, categorical laws, numeric policy and scientific support
must not be chosen merely to make tests pass. The local affine implementation
below makes one supported alternative testable before a decision.

## What the alternative association adapter computes

Code: [association adapter](src/heterodiff/experiments/association_observation_training_adapter.py),
[hybrid potential connection](src/heterodiff/experiments/hybrid_conditional_training.py).

All laws are supplied through an immutable analytic-family object and explicit
kernel/context declaration. There is no default real-domain noise parameter.
Sampling first selects one whole-observation contamination branch. The
reference branch draws an unconditional Poisson(1) count; the clean branch
draws independent occurrence detection indicators and Poisson clutter. Counts
above the declared cap collapse to the single overflow atom before Gaussian
coordinates are generated. No count is truncated, conditioned below the cap,
or redrawn. Observed types use physical channel probabilities, not their
Radon–Nikodym ratios. Duplicate occurrences are retained.

The retained log likelihood is evaluated by the existing association oracle.
The proposed G+R baseline uses the existing **uncapped auxiliary guide
restricted to the capped state**, not the exact capped-reference or learned-
base information function. DIR uses the terminal likelihood. The guide agrees
with that likelihood at the terminal/clean-hold endpoint. Overflow's first
coordinate derivative is zero specifically because this supplied family's
detection and overflow counts depend on types/counts, not coordinates.

The CPU first-derivative bridge evaluates the oracle at the same
FP32-represented latent coordinates used by the neural model, then explicitly
rounds its binary64 value/gradient. Nonfinite conversions fail. Stable
occurrence indices invert canonical sorting before gradients are assigned
back to tensor rows, including cases where FP32 rounding changes tie order.
This bridge is not a Hessian interface, a derivative of machine rounding, or
a new outward-rounded global certificate. The physical sampler still requires
a declared finite upper envelope and numerical qualification.

Only visible observations, declared task and static context reach the encoder.
No source alignment, signal/clutter label, latent count or diffusion time is
provided. Noisy anchor count is not mislabeled as latent cardinality. Overflow
is represented by an empty/unknown-count placeholder **plus an explicit bit**,
so it remains distinct from an ordinary empty observation while retaining
task/context information.

The wrapper adds a 65-to-64 affine/tanh layer to the existing retained encoder,
and an independently parameterized copy to the observation-only nuisance.
This adds 8,448 parameters to the retained-model proposal. It is separately
accounted for; it does not rewrite the old architecture. The nuisance enters
classification only, never physical drift, jumps or conditional initialization.
Kernel identity, baseline role, domain/task and exact declared static context
are checked across these local interfaces. Kernel digests are content bindings,
not authenticated authorship or proof of a scientific declaration.

## Budget outcome

The [expanded workload ledger](PROJECT_TWO_DOMAIN_COMPUTE_BUDGET_AMENDMENT.md)
now separates successful-path callback counts from primitive work, candidate
and accepted jump work, rejected initialization proposals, encoders, overflow
wrappers, neural calls and cardinality-dependent F105 pair work. It preserves
the frozen F104 formula and records all 22 method roles.

Eight control rows still name static configuration contracts; eight literature
family rows and two external author-extension adapters still lack complete
training/inference mechanisms. Four controls have no learned conditional
target, so inherited optimizer/checkpoint obligations need an explicit
decision. A declared role is not an implementation. No missing algorithm,
scalar operation weight, hardware speed, resource allocation or price has been
invented. F066/F072 and B06 remain open until the complete amendment is reviewed
and adopted. Logical event counts are not elapsed-time or monetary estimates.

## Verification and preserved state

**1,254 tests passed across 24 selected suites**, in three disjoint runs:

- 983 existing adjacent implementation/admission/metric/sampler/design tests
  in 61.17 seconds;
- 249 tests covering the existing full hybrid/F105 integration (11), new
  domain chart (197) and expanded budget (41), in 253.12 seconds;
- 22 new association-adapter tests in 3.83 seconds.

The new tests check duplicate atomic mass normalization against an independent
closed formula, physical mixture/confusion/count sampling via exact stream
replay, overflow without Poisson truncation, first-gradient finite differences,
FP32 occurrence permutation and nonfinite-cast refusal, exact context binding,
retained/overflow separation and input alias refusal, and independent model
parameter gradients. Both methods run actual two-pair learned-base sampling
through observations, oracle baselines, paired loss and one AdamW update;
separate small cases execute conditional rejection initialization and hybrid
paths. This is not full scientific training. The previously implemented four
128-group/R64 hybrid/F105 cases are included in the 249-test run; the new
alternative observation route does not claim its own full-size F105 campaign.

Static lint and whitespace checks pass. Independent code/mathematical review
checked the family/scoping arguments and independently reproduced the 2D
FP32 occurrence-gradient case. All 323 accepted CPU source payloads were
reopened and matched their recorded sizes and hashes. The old manifest remains
`9a7d815ada69a7405552ac885b229e13f63eb24ff1ed6e57d0730734452ed5ff`
and CPU lock remains
`c6fa5d600cd2810c40ae47d5eeeba341e0467c4c75dd7c7d310cf3628ab6349f`.
Tests used local Python 3.11.5/CPU Torch 2.12.1, not Databricks/CUDA.

This local milestone adds no timetable checkbox and closes no broader field or
blocker. Current totals remain **61 checked / 102 open / 163**, **25 fields
open / 147 closed**, **8 blockers open / 4 closed**; Formal Tests 28/29/30 stay
**OPEN / OPEN / PENDING**, scientific results **0/4**. The accepted F152 CPU
lock and 323-file release are preserved. These additive modules require a
future release; do not rerun the old bootstrap to qualify them.

No new Databricks action is requested. Dataset availability/permissions,
selected GPU facts, bounded spending/runtime and durable-storage limits remain
separate missing inputs; reported GPU count and host RAM do not supply them.
