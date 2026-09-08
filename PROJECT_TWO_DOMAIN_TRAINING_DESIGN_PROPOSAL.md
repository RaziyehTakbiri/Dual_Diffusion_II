# Two-domain observation and training-law design proposal v1

Status: **review-pending proposal**, not an adopted scientific revision, new
B06 freeze, admitted data law, GPU qualification or authorization to launch.
The accepted CPU bundle, old source snapshot and existing F064–F071 records
are unchanged. The architecture below is a preferred trainable proposal;
a parameter-free 64-channel summary is not substituted merely to fit an older
detached-feature interface.

## Mathematical boundary retained

Manuscript v3 §5.3–5.4 and executable method specification §7.1 require an
observation-only conditioner E(a,m,z), an independently parameterized nuisance
c(a,m,z), and two independent candidate-base trajectories at the same task,
static context and reverse time. The nuisance must have no process-time or
latent-state input and must never enter the physical potential or initializer.
The physical branch retains the existing single bounded energy and clean-hold
gate. This proposal does not substitute data-forward pairs for base rollouts.

## Preferred encoder and nuisance architecture

The tensorizer accepts only the existing model-visible `ObservationView`, never
ground-truth-aligned `ObservationPattern` or a target configuration. A declared
schema supplies legal event types, visible mark names/widths/scales, task IDs,
static-context feature names/scales and a physical-observation-time scale.
Unknown fields, types and widths are rejected. Physical event time is an
observation attribute; it is not the diffusion clock.

For T legal types and M visible mark coordinates, each anchor has A=3+T+2M
channels: time-known and bounded physical time; type-known and a type one-hot;
and each mark's visibility mask and bounded value. An absent value is not an
observed zero. Hidden types do not reveal inferred applicability or alignment.
All duplicate visible occurrences remain distinct. Global channels contain
visible anchor count n/(1+n), cardinality-known and known cardinality N/(1+N),
followed by K task one-hot and Z bounded static-context channels. Unknown
cardinality has no target-count feature. Numeric transforms use
(2/pi) atan2(value, positive declared scale); no outcomes set the scales.

The trainable encoder is:

- per-anchor MLP A→64→64 with tanh after each layer;
- occurrence-preserving sum divided by 1+n; no padding or truncation;
- readout MLP (64+3+K+Z)→64→64 with tanh after each layer.

The output is 64-dimensional and bounded in [-1,1]. This fits the existing
conditional energy's 64-input interface. It is a finite-feature model class,
not an injective encoding, universal approximation guarantee, certificate of
observation derivatives, or bitwise permutation-invariance claim. FP32 sums
are qualified to numerical tolerance. Oversized input is rejected; the local
implementation limit is not a new scientific cardinality cap.

The nuisance owns a **separate** encoder of the same architecture and a
64→32(tanh)→1 affine scalar head. Parameters are not shared with the physical
conditioner. It can therefore learn without introducing observation-encoder
parameter dependence into the physical branch. The raw tensors are detached;
gradients flow through both trainable encoders' parameters, not into latent or
clock tensors. An additive composite boundary is needed because the older
`ObservationOnlyInputs` contract intentionally requires detached features.
No old boundary is weakened.
The nuisance's final affine scalar is not architecturally saturated. A
whole-logit bound, nuisance-gauge qualification and curvature/certificate
requirements remain separate; finite local outputs do not certify them.

Exact task/context hashes retain the raw static-context float representations.
Joint/product pairing must compare those hashes, not only bounded FP32 feature
values, which can collide. These hashes bind supplied values; they are not
external provenance or proof that a falsely labeled feature is observation-only.

## Exact prospective parameter accounting

Let G=3+K+Z. One encoder has E=64(A+64+G)+8448 parameters. The nuisance head
has 2113. Complete added trainable capacity is **2E+2113**, provided the graphs
are disjoint and the old conditional backbone remains unchanged. The old
internal context MLP is already counted and is not added again.

For the illustrative one-type, one-task coordinate schema M=112 (PhysioNet)
or M=10 (Retail), this gives:

| Domain | One new encoder | Added capacity | Total with historical base+conditioner |
|---|---:|---:|---:|
| PhysioNet | 27,392+64Z | 56,897+128Z | 268,099+128Z |
| Retail | 14,336+64Z | 30,785+128Z | 215,875+128Z |

These formulas are proposals, not measured production-model counts. The actual
visible-coordinate schema, partial-observation mapping, static-context width
and scales still require data-definition review. A one-type F105 coordinate
interface is an illustrative accounting schema, not proof that a raw-domain
observation can be decoded into those coordinates without hidden information.
Both primary roles must use the same proposed encoder/nuisance capacity and
data opportunity. F064/F065/F070/F071 need a prospective successor before
adoption. Frozen base, trainable state, buffers and optimizer state must also
be accounted for on the appropriate hard axes.

## Task/context/time and initial-law proposal

For production review, propose uniform sampling over the explicitly admitted
roster of valid (task, training-context) pairs, with q(du|m,z)=du/S on the
**entire** open interval (0,S), including clean-hold times. No real roster,
task/kernel choice, context values or process horizon is invented here.
The initial distribution stays the selected process-owned capped reference
Pi_N; each paired example requires two independent draws and two independent
base trajectories at the same m,z,u. Observation A1 comes from the first
endpoint and A2 from the second; both classes use the first branch's Y_u.
Cross-context permutation is forbidden. Initial-law simulation and normalized
K_m are owned by separate process/observation components.

The executable synthetic law is explicitly versioned and fully specified by
its supplied finite task/context roster, exact Fraction horizon and 16-bit
uniform midpoint-time grid. It samples the three indices independently with
all task/context combinations explicitly declared valid in that synthetic
Cartesian roster. This is not a claim that a production task is valid for
every production context. Sampling uses
a supplied CPU generator, retains exact rational u and S-u, and supplies equal
class priors and unit RN factors **only for that declared finite synthetic
law**. A finite midpoint grid does not literally have continuous full support;
it is not silently equated to q, and no continuous-to-discrete RN correction
is claimed. The mathematical uniform density is separately available for
inspection. A production approximation/error contract remains necessary.

For either law, alternate task/context/time/trajectory/observation sampling
requires the exact unnormalized law change, not self-normalized weights. A
common-support claim also requires the selected normalized observation kernel;
a no-clutter same-count Gaussian toy observation does not establish the positive
dominated branch at empty configurations. Overflow must not be truncated or
redrawn under an unchanged law.

## Additional work, not a budget completion claim

Two-class loss uses two classifier and two nuisance evaluations per update;
feature encoding, nuisance gradients and raw preprocessing must be charged.
For 16 paired records/update, explicit independent base generation requires
32 trajectories/update: 131,072 per 4096-update seed. Under a 256-step path
convention this alone is 33,554,432 logical reverse steps/seed, in addition to
checkpoint validation. Inserted evaluation times may change actual substeps.
Neither these logical counts nor parameter counts are GPU launches, F104
weights, a scalar budget, calibrated time/memory, or spending authorization.
The earlier validation-only amendment remains incomplete for this new route.

## Implementation and evidence

`two_domain_observation_training_design.py` supplies the strict tensorizer,
trainable condition encoder, independent nuisance, exact parameter formulas,
immutable synthetic law and explicit continuous-q nonclaim. New synthetic-only
tests cover visibility/cardinality masks, duplicate occurrences, permutation
tolerance, bounded output, live parameter gradients, nuisance isolation,
context-identity collisions, parameter counts, deterministic local generators,
immutable law identity and resource-bound refusal. No actual dataset, paid job,
production design adoption, source-snapshot amendment or scientific result is
created by these tests.
