# Domain extension contract

## What is reusable now

The model separates event representation, a normalized reference, observation
likelihoods, training, numerical sampling and evaluation. The public synthetic
runner supports two explicit typed carriers. It does **not** accept an arbitrary
user class: `FactoredEvent` and several reference/observation paths currently
check exact Physio/Retail key types.

This is a documented extension contract, not a claim that a general plug-in API
has already been implemented.

## What an additional adapter must supply

1. A declared countable legal key set, exact canonical serialization and
   occurrence equality. Preserve duplicates; never hash away or round scientific
   metadata.
2. Fiber dimensions and charts. Current implementation supports only zero- or
   one-dimensional Gaussian fibers. Vector fibers or bounded charts need
   corresponding transitions, likelihoods and derivatives.
3. A normalized reference mass with declared support, a sampler and log density.
   Any TRAIN-informed component must be fitted only on the appropriate training
   partition. Full support is distinct from plausible domain constraints.
4. A dominated observation channel, missingness/zero/atomic behavior and overflow
   semantics. Singular noiseless continuous observations require a different
   mathematical treatment, not an invented ordinary density.
5. Materialization back to the domain object, with explicit numerical conversion
   errors/refusals, and a scientifically justified evaluation function.
6. Scientific count caps versus computational refusal limits; dataset parsing,
   splitting and permissions are separate from the mathematical carrier.

## Implementation work still required

Replace the exact-two-class checks with a small reviewed protocol/registry,
while preserving existing encodings. Thread the protocol through reference
sampling, observation encoding, neural packing and output conversion. Add a
third genuinely different toy domain to demonstrate the interface, rather than
calling a renamed Physio/Retail fixture general.

Acceptance tests should cover normalization on a tractable domain, encode/decode
behavior, repeated/empty/atomic configurations, unseen keys, invalid values,
reference/observation consistency and train/sample/evaluate from the public API.
Existing two-domain tests must continue passing.

The equation/implementation map and current extension assumptions are in
[the scientific core](../manuscript_v3/hybrid_diffusion_scientific_core_v1.md).
