# Explicit Source-Model Contract: Incremental Code Audit

**Audit status:** **PASS WITH EXPLICIT SCOPE LIMITS**  
**Audit date:** 2026-08-17  
**Implementation:** [checkpoint-46 source](../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract.py)  
**Focused tests:** [checkpoint-46 tests](../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract.py)  
**Direct parent:** [checkpoint-45 obstruction](plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction_code_audit.md)  
**Claim controls:** [claim ledger](claim_ledger.md)

Checkpoint 46 turns the checkpoint-45 source-support obstruction into an
explicit two-model contract. It keeps one fixed deterministic request separate
from an externally declared finite rational law over the two public uint64
request coordinates. The external declaration is a probability-law record,
not a sampler and not evidence that any caller realizes its probabilities.

Every source-law statement is conditional on one of two declared positive-mass
events: acquisition of a complete validated capsule or return of a checkpoint-
44 result. CP46 neither executes the request nor certifies that either event has
positive mass. It records exact support, total-variation, capacity, and fiber
criteria without promoting a live randomness or scientific claim.

## 1. Frozen object of review

The source contains `1777` lines and `79395` bytes and has SHA-256
`8c6d1ead643a127aa87d395de1ff707eb0506e619d53b513477777173d439318`.
The focused test contains `1185` lines and `45400` bytes, collects exactly `24`
cases, and has SHA-256
`04b73ec0f0fbd0a8a31973a02a2218cdd1ea3ad000a9648168a1f7194c7415ac`.

The public surface has exactly 28 unique exports: 17 contract, theorem, domain,
mode, and conditioning constants; six sealed record, owner, and error classes;
and five declaration, certification, matching, and validation operations. It
provides no request-law sampling operation, CP27 allocation, CP43 semantic
operation, or CP44 execution entry point.

## 2. Two source models and two conditioning events

Let `D = 2^64`, let the complete CP44 capsule contain `L` words, and let `U_L`
be uniform on `[D]^L`. CP45 supplies `L > 2` and the exact CP44 capsule
partition.

For one exact fixed `(run_id, initialization_index)` request and a declared
conditioning event `E` with `P(E) > 0`, deterministic replay gives one symbolic
capsule `z`. The conditional source law and exact distance are

```text
nu_E = delta_z,
TV(delta_z, U_L) = 1 - D^(-L) = 1 - 2^(-64L).
```

The fixed-request record is a cached symbolic descriptor. It records a
degenerate constant V/W factorization under the positive event, but it does not
execute the request, materialize `z`, instantiate a measured capsule law,
certify nondegenerate V/W independence, or certify fresh draws across calls.

For an externally declared finite request law with support size `s`, let `F` be
any deterministic partial request-to-capsule map. Conditioning on any event `E`
of positive mass can discard request atoms but cannot create new atoms, so

```text
|support(nu_E)| <= s,
TV(nu_E, U_L) >= 1 - s / D^L = 1 - s / 2^(64L).
```

This argument does not require success/value independence. Both the complete-
capsule and returned-result conditioning strings are exercised for both source
model classes; every other conditioning string is rejected. Positive event
mass is a premise recorded by each model, not a certified fact.

## 3. Request-surface capacity and the exact fiber criterion

The current live request surface contains exactly two uint64 coordinates and
therefore at most `D^2` request points. For any law on that full surface and any
deterministic partial map, positive-event conditioning yields capsule support
at most `D^2`. Since CP45 certifies `L > 2`, the current request surface cannot
produce the product-uniform law on `[D]^L`, whose support has size `D^L`.
Deriving additional coordinates deterministically from the same primitive
request does not increase this support capacity.

Support of at least `D^L` is necessary for a live product-uniform capsule law,
but it is not sufficient. Given a realized request law `mu`, deterministic map
`F`, and positive conditioning event, the conditional capsule law is product
uniform exactly when every output fiber has conditional request mass `D^(-L)`.
A nonuniform request law can therefore push forward to uniform when its
weighted conditional fibers balance, while an injective map preserves the
nonuniform weights. CP46 records this if-and-only-if criterion but certifies
neither realization of `mu` nor weighted fiber balance.

The source-to-output direction remains a nonconverse. Data processing gives an
upper bound on output TV; it does not transport the source lower bound to an
arbitrary semantic output. A constant semantic map can erase the entire source
discrepancy. CP46 consequently certifies no semantic-output TV lower bound.

## 4. Canonical finite-law declarations

The executable declaration is an exact rational PMF over
`(run_id, initialization_index)`. Its rows are exact triples
`(run_id, initialization_index, positive_numerator)` in strict lexicographic
order, with unique uint64 request pairs. The exact positive denominator equals
the numerator sum, the shared representation has greatest common divisor one,
and each integer is limited to 16384 bits. The support is nonempty and capped
at 4096 atoms.

The 4096-atom cap is an executable representation limit, not the analytic
`D^2` capacity theorem. In particular, CP46 does not claim that its declaration
API can enumerate every law on the full request surface. A declaration records
canonicality, normalization, reduction, support size, and whether it is a point
mass. It explicitly records no external realization, sampling rule, or physical
randomness.

Declarations are exact-type, digest-bound, frozen, module-created,
nonsubclassable, and nonpickleable. Empty, unordered, duplicate, zero-mass,
unnormalized, unreduced, oversized, out-of-range, over-bit-limit, coercible, and
hostile inputs fail closed. A stale digest rejects an otherwise valid law
change; after a valid alternate law is independently canonicalized and
redigested, it remains a valid declaration because declaration custody is
content-addressed rather than owner-identity-addressed.

## 5. Cached descriptors versus explicit live revalidation

Certification binds one exact CP45 owner and invokes the inherited live
boundary before and after certificate construction. Public owner matching and
public certificate validation explicitly replay CP45 live ancestry. The owner
also exposes `revalidate_live_ancestry()` for that purpose.

Ordinary fixed-model construction, external-model construction, and model
validation instead use the sealed cached CP46 certificate. They recheck local
and parent structural custody but do not call the CP45 owner's live-binding
method. Every returned model therefore records
`cached_descriptor_only=True` and
`live_checkpoint45_ancestry_revalidated_for_this_model=False`. This is a
deliberate temporal boundary: a cached descriptor must not be read as a fresh
live-ancestry attestation.

The owner-bound evidence traces declaration, CP46 certification, four model
descriptors spanning both modes and both conditioning events, cached validation
of one model of each type, and public certificate validation. Across that
fixture, Python, NumPy, and PyTorch caller/global RNG states are unchanged. The
exact operation and ancestry budgets are

```text
CP27 allocation calls                         0
CP43 combined-evaluation calls                0
CP43 G calls                                  0
CP43 semantic H calls                         0
CP44 execute calls                            0
CP45 live-binding calls                       3
CP45 structural certificate validations     26
```

The three live calls are the two-sided CP46 certification boundary plus the
explicit public certificate revalidation. Cached model operations add no CP45
live-binding call. CP46 does not claim absence of every transitive RNG call:
certification, structural ancestry checks, and explicit live revalidation may
inherit CP45's deterministic local Philox runtime probe.

## 6. Custody, tamper resistance, and exhaustive nonclaims

The certificate binds exact CP45 certificate and owner identities, the CP45 and
CP44 certificate digests, the CP44 process-parameter digest, runtime digest,
word counts, two-coordinate request surface, capsule partition, theorem text,
policy, scope, and role digest. It inherits the CP45 transitive CP44/CP36/CP27/
CP26 custody chain. Certificate and model validation require exact record and
owner identities where ownership matters; cross-owner model splicing is
rejected even when certificate contents match.

Declarations, certificates, both model classes, and the owner are frozen,
module-created, nonsubclassable, and nonpickleable. Semantic digests bind all
relevant record fields. Plain tampering, stale-digest valid changes, redigested
semantic-claim promotion, certificate/model owner splicing, hostile fields,
parent drift, local-helper drift, public-helper drift, guard replacement, and
owner-class replacement fail closed before substituted or hostile operations
execute. Exact-type preflight rejects bools, NumPy integers, coercible values,
and touch-bomb objects without invoking live ancestry or semantic operations.

The positive certificate fields are limited to exact custody, the two separated
model types, the conditional point-source and finite-support theorems,
conditioning support monotonicity, absence of a success/value-independence
premise, the current two-coordinate capacity obstruction, the source-to-output
nonconverse, operation-free construction, unchanged caller/global RNG state,
the cached/live boundary, the declaration-cap distinction, and the necessary-
support/weighted-fiber criterion.

All stronger interpretations remain explicitly false. CP46 does not certify
external-law realization or sampling; live request uniformity or coordinate
independence; full-capsule product uniformity or nondegenerate V/W independence;
numeric capsule-acquisition, return, or refusal probabilities; positive event
mass; unconditional capsule or output laws; semantic-output TV separation;
absence of transitive RNG calls; accounting for hidden entropy or environment;
physical randomness; cross-call freshness; per-model live CP45 revalidation;
sufficiency of the current request surface or source support; weighted fiber
balance; an external full-entropy source interface; loaded-code integrity;
runtime portability; cryptographic authentication; initializer, path, or
sampler admissibility; or scientific, model-quality, or generality promotion.
The controls are procedural and same-runtime, not cryptographic attestation.

## 7. Focused evidence and final disposition

The 24 cases divide into 15 source-independent cases and nine owner-bound
cases. The source-independent set comprises one exact API/scope test, five
declaration canonicality/sealing/digest/preflight tests, eight exact rational
mathematical oracles, and one AST surface test. The mathematical evidence
includes 1848 conditioned partial-pushforward checks; the uniform-input
bijection equivalence; a nonuniform law with balanced conditional fibers;
exact fixed-point TV; an externally reused request with equal marginals but a
non-IID joint law; the failure of uniform marginals to imply a product joint;
conditioning-induced dependence and an undefined zero-mass conditional law;
10000 derived-coordinate capacity checks; a nonuniform injection; and a
constant-map TV-erasure nonconverse. These are exhaustive on their stated small
finite domains, not Monte Carlo evidence or a proof by testing for all domains.

The AST gate finds no direct `random`, `secrets`, NumPy, or PyTorch import; no
exponentiation operator or built-in `pow` call; exactly the constant
`1 << 64`; and no direct sampling, CP27 allocation, CP43 evaluation, or CP44
execution call. It restricts direct CP45 live binding to certification and
explicit live revalidation and verifies that the three cached model methods do
not invoke either live path.

The nine owner-bound cases cover the exact ancestry truth table and every
positive/negative flag; both model types and both conditioning events; exact
formula fields; RNG, operation, live-call, and structural-validation budgets;
sealing; plain, redigested, and hostile tampering; valid-change stale digests;
cross-owner custody; hostile preflight; and local, parent, guard, owner-class,
and public-helper drift.

The authoritative full command is

```text
/usr/bin/time -p env PYTHONPATH=src /private/tmp/diffusion-recovery-20260815/.venv-m1/bin/python -m pytest -p no:cacheprovider -W error --durations=24 -q tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract.py
```

**Final result:** **24/24 passed** in `4765.71 s` (`1:19:25.71`) under
warnings-as-errors. The external timer recorded wall/real `4766.28`, user
`4360.90`, and sys `371.83` seconds. There were no failures, errors, skips,
xfails, xpasses, or warnings. The final source-independent run also returned
**15/15 passed** on the frozen source and test.

Post-run static gates pass for Black, pyflakes, flake8 `E9,F63,F7,F82`,
locked-runtime syntax compilation, ASCII, AST parsing, exact 24-case
collection, and the exact 28-symbol export surface. Post-run source and test
hashes exactly match the frozen values above. Independent final strict audits
of both the source and focused test ended at `P0=P1=P2=0`.

The venue-neutral Markdown and TeX manuscripts remain untouched with SHA-256
values `0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8`
and `0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9`.
Accordingly, CP46's disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

## 8. Scope limit and next dependency

CP46 is a conditional, declarative source-model checkpoint. It does not turn
the fixed CP44 request into a random draw, realize or sample the external PMF,
or supply enough primitive source capacity for a product-uniform `L`-word
capsule. It changes no manuscript claim.

A future live-source checkpoint would need an implemented and audited external
entropy interface, explicit realization of its law, at least `D^L` conditional
request support, weighted output-fiber balance, positive-event mass, entropy
and environment custody, and a reuse/freshness contract. Without that evidence,
product-uniform capsule laws and nondegenerate V/W independence must remain
counterfactual rather than live claims.
