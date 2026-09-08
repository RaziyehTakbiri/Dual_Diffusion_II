# Shared factorized-metadata energy prototype

Date: 2026-09-08. Status: **additive local scientific-amendment implementation**,
not clinical/numeric-law selection or production qualification. The old typed
energy, frozen B06 records, accepted 323-file CPU release and dependency lock
are unchanged. No dataset, cloud/GPU job, package installation or full training
campaign was used.

## Implemented boundary

`src/heterodiff/models/factorized_configuration_energy_torch.py` supplies a
separate CPU FP32 graph over exact caller-declared metadata-key bytes. Every
byte is consumed by one shared 32-state recurrent encoder; no complete stratum
roster, per-type parameter layer, category vocabulary or hash embedding is
constructed. Thus the parameter count is independent of the number of possible
keys, and there is no inherited 4,096-type interface ceiling.

The input key must be a nonempty exact `bytes` value. Canonicalization and
semantic validity belong to the supplied domain-key adapter; this generic
module does not infer that arbitrary bytes describe legal patient/retail
records. The factorized domain keys' explicit `.canonical_bytes()` and
`.dimension` interfaces can populate this boundary, but no production adapter
or scientific-schema certificate is implied.

Keys are immutable discrete input data, not Euclidean diffusion coordinates.
Each occurrence separately declares dimension 0 or 1 and has a genuinely empty
or one-coordinate tensor. A 0D atom is not represented by a diffused zero or a
masked latent scalar. A zero scalar and an atomic event have different input
activity bits; same-key inconsistent dimensions are rejected within a batch.
The 1D coordinate alone receives the bounded coordinate transform and ordinary
autograd. No type/metadata coordinate is rounded, reassigned or overwritten.

This interface accommodates variable-length arbitrary-integer/rational key
encodings without asserting that their entire support fits in a finite vector.
The input byte sequence is exact, but **the learned finite-precision 32-state
compression is not injective**. Learned collisions, saturation and limited
expressive capacity are possible; there is no injectivity or universality claim
for its output or for the final energy. In particular, these are not the exact
F105 metric features.

## Graph and exact parameter count

For bytes `b_j`, start `h_0=0` and apply

`h_j = tanh(W h_(j-1) + v*(b_j/256) + c)`.

Each byte/256 is exactly representable in FP32. All sequence positions are
consumed, including zero bytes and the last byte. There is no sequence truncation
or learned vocabulary lookup. Prefix/length information enters through the
complete ordered recurrence, not through a claimed injective recurrent state.

Each event then has 34 neural features: 32 metadata channels, a dimension/activity
bit, and one bounded continuous scalar (fixed zero for 0D events). The graph is:

- shared event `34 -> 128 -> 128`, with tanh after both layers;
- existing-width context `65 -> 128 -> 128`, taking explicit 64-channel context
  and normalized forward time, with tanh after both layers;
- multiplicity-preserving event sum, context embedding and normalized count;
- readout `257 -> 128 -> 128 -> 1`, tanh after the first two layers; and
- bounded output `V*tanh(raw/V)`.

| Component | Unique parameters |
|---|---:|
| Shared byte recurrence `32²+32+32` | 1,088 |
| Shared event layers `34*128+128+128²+128` | 20,992 |
| Internal context layers (already counted here) | 24,960 |
| Readout layers | 49,665 |
| One energy | **96,705** |
| Separate BASE plus conditioner energies | **193,410** |

The last row does not include any independent raw-observation encoder, nuisance,
overflow wrapper, optimizer state or activation storage. It is not an adopted
F065/F071 value. Parameter count does not establish adequate expressive power
or fairness. BASE and conditioner must separately receive their own parameters.

Initialization uses an explicit CPU-local uint64-seeded generator and leaves
the global Torch RNG unchanged. Forward evaluation enforces finite CPU FP32
parameters and inputs. Moving/casting the model into an unqualified runtime
causes refusal rather than silent conversion or fallback. Positive architecture
scales/horizon/output bound must be exactly representable in FP32; this numeric
restriction is a local prototype boundary, not a scientific value selection.

## API and local limits

The immutable `FactorizedEnergyArchitecture` declares `metadata_schema_id`,
`total_cap`, `horizon`, `value_bound`, `coordinate_scale`, `context_scale` and an
explicit `FactorizedEnergyLimits`. Its canonical digest includes these fields,
the fixed graph widths, parameter count and all limits.

`FactorizedConfigurationBatch` contains that digest, aligned tuples of
`metadata_keys`, `coordinate_dimensions`, individual unpadded `coordinates`,
integer `owners`, and the `[B]` forward-time / `[B,64]` context tensors.

Limits are explicit for batch size, aggregate event count, per-event metadata
bytes and aggregate metadata bytes. All inputs are checked before neural key
encoding begins. Exceeding a limit or the declared configuration cap raises a
terminal resource error: nothing is truncated, clipped, top-coded, silently
dropped or redrawn. A resource limit is not a scientific support restriction,
proof that all legal data will fit, or permission to raise a frozen resource
ceiling. The unbounded support of a proposed integer/rational law still needs
an honest finite-resource failure policy.

Within each batch group, evaluation sorts immutable key bytes, dimensions and
represented coordinate values, then sums every occurrence. This produces
permutation-bitwise repeatability for the tested CPU graph and preserves
duplicates/gradient ownership. It is not the old certified exact segment-sum
implementation, a cross-device determinism proof or a sorted-boundary/Hessian
certificate. Canonical ordering is only computational order, not deduplication.

`workload(batch)` reports exact local graph counts, including one recurrence
step and 1,024 matrix MACs plus 32 byte multiplications per metadata byte. It
also reports event/context/readout affine MACs and actual fiber dimensions.
Biases, activations, sorting, pooling, autograd and optimizer work are explicitly
not included in those partial MAC figures. There is no measured F104 weight,
GPU-time estimate or budget adoption.

## Scientific and integration exclusions

The structural amendment direction is mixed discrete metadata/atomic strata
with continuous scalar fibers where justified. This file supplies no clinical
numeric probabilities, noise levels, reference activity, replacement rule,
measurement/quantization law, observation support proof or reference sampler.
The initial proposed reference direction remains birth/death plus OU with
replacement rate zero; that choice is not implemented or certified by an energy
module. A later process adapter must keep exact metadata and the declared fiber
dimension bound together.

Old `BoundedConfigurationEnergy` certificate/factory interfaces are unchanged.
This model is not their accepted type and does not inherit any global spectral,
first/second derivative, jump-tilt, initializer or checkpoint certificate. A
bounded scalar output alone is insufficient for those claims. Existing frozen
inference/training configuration identities and parameter counts are historical
references, not proof of this new graph's adoption.

The generic context interface permits autograd through a supplied context
encoder, but this module cannot prove that its upstream features are visible-only
or task-correct. Observation-only nuisance isolation remains a separate wrapper
obligation. No actual conditional diffusion training objective is supplied by
the synthetic squared-loss optimizer regression.

## Local checks

The synthetic tests exercise immutable bindings, full uint64 deterministic
initialization, exact parameter arithmetic, all 256 byte values/full recurrence
consumption, metadata-sensitive energy, >4,096-key validation, 0D atoms, empty
configurations, 1D gradients/finite differences, context/time dependence,
permutation/duplicate preservation, bounded output, pre-encoding resource
refusal, malformed/cross-boundary input refusal, and one CPU forward/backward
AdamW update. The larger-key test qualifies validation/counting only, not a
domain-scale forward/backward run. No timetable, field, scientific result or
blocker closes merely from these local checks.
