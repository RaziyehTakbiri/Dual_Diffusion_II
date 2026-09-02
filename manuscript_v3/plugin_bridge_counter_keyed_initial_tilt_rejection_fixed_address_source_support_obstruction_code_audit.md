# Fixed-Address Source-Support Obstruction: Incremental Code Audit

**Audit status:** **PASS WITH EXPLICIT SCOPE LIMITS**  
**Audit date:** 2026-08-17  
**Implementation:** [checkpoint-45 source](../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction.py)  
**Focused tests:** [checkpoint-45 tests](../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction.py)  
**Direct parent:** [checkpoint-44 adapter](plugin_bridge_counter_keyed_initial_tilt_rejection_factorized_execution_adapter_code_audit.md)  
**Claim controls:** [claim ledger](claim_ledger.md)

Checkpoint 45 records the source-law obstruction that must precede any
distributional interpretation of checkpoint 44. A same-runtime CP44 call at
one fixed owner and exact `(run_id, initialization_index)` address is
deterministic. If it returns one complete capsule, the canonical live source
law is a point mass, not the abstract product-uniform law used in CP36, CP41,
CP43, and CP44 counterfactual corollaries.

The checkpoint also records the sharp support-counting lower bound for a
deterministic partial capsule map driven by at most k free uint64 coordinates.
This is a source-space result conditional on positive success probability. It
requires no success/value-independence premise and supplies no semantic-output
lower bound, refusal probability, live independence, randomness, initializer,
sampler, or scientific claim.

## 1. Frozen object of review

The source contains `1019` lines and has SHA-256
`5c430ed18d8c14fd5359858b8a686c521c8cb61f5389b977b4c1f8fdc192bad5`.
The focused test contains `1009` lines, collects exactly `20` cases, and has
SHA-256
`53701f0c59634fe6be32d730e39b16e066cfa9d8879094e7c876e235742f9553`.

The public surface has exactly 15 unique exports: schema, policy, scope, two
theorems and one nonconverse, two domain constants, a sealed certificate, a
sealed symbolic bound, an immutable owner, a custody error, certification,
exact-owner matching, and certificate validation. It makes no source
allocation and invokes no CP43 or CP44 semantic operation.

## 2. Fixed returned request

Let D = 2^64, let Omega_L = [D]^L, and let U_L be uniform on Omega_L. Fix one
exact CP44 owner, runtime, and request. Under the inherited same-runtime replay
contract, if the request returns z in Omega_L, its canonical source law is
delta_z. Direct summation gives

```text
TV(delta_z, U_L) = 1 - D^(-L).
```

The equality includes L = 0, where Omega_0 is a singleton and the distance is
zero. The actual CP44 capsule has L greater than two, so the obstruction is
strict for a fixed request and for the present two-coordinate request surface.

This does not say every request succeeds. It describes the exact source law
for the specified fixed request conditional on its returning a capsule. CP44
pre- and post-combined refusals remain no-result events outside that returned-
capsule source space.

## 3. General support theorem

Let A be the successful subset of [D]^k for a deterministic partial map
f: A -> [D]^L. Give [D]^k any request law for which A has positive
probability, and let nu_success be the law of f conditional on success.
Conditioning removes request points but cannot create any, so

```text
|support(nu_success)| <= |A| <= D^k.
```

For any law nu supported on S inside Omega_L,

```text
TV(nu, U_L) >= nu(S) - U_L(S) = 1 - |S| / D^L.
```

Therefore, when L > k,

```text
TV(nu_success, U_L) >= 1 - D^(k-L) = 1 - 2^(-64(L-k)).
```

When L <= k, support counting alone gives only zero; a projection or bijection
can attain uniformity. CP45 therefore clamps the exponent gap at zero and does
not report a false positive lower bound. It stores symbolic exponents and
formula text rather than materializing enormous powers or floating values.

The proof permits nonuniform request laws, collisions, and arbitrary success
sets. No success/value independence is needed. Every external entropy-bearing
input must, however, be counted among the k coordinates. Hidden entropy,
runtime faults, physical noise, and random environments are not accounted for.

The public k domain is every exact nonnegative Python integer. Digesting uses
a tagged signed-hex encoding, so the API is independent of Python 3.11 decimal
conversion limits. The focused test exercises k = (1 << 16384) + 123 through
public construction, digesting, and validation.

For the current CP44 request surface, records for k = 0, 1, and 2 have gaps
L, L-1, and L-2. Those records do not make the address coordinates random;
they state the consequence if a law over no more than those coordinates is
supplied externally.

## 4. Source-to-output nonconverse

For a semantic map H, data processing gives

```text
TV(push_H(nu), push_H(U_L)) <= TV(nu, U_L).
```

This is an upper bound, not the lower bound needed to transport CP45's
obstruction to outputs. A constant H sends both source laws to the same point
mass, making output TV zero even when source TV is near one. CP45 therefore
sets `semantic_output_tv_lower_bound_certified=False`. An output lower bound
would need additional injectivity or distinguishability structure that is not
present here.

## 5. Ancestry, custody, and RNG wording

Certification binds one exact CP44 owner, certificate, runtime object
identity, process-parameter digest, full word count, and transitive CP36,
CP27, and CP26 identities. Exact CP44 validation supplies inherited CP43
split/join custody. CP27 exact-parent replay and within-allocation address
distinctness, CP26 same-runtime prefix replay, and the parent certificates'
negative live-randomness statements are checked before CP45 is sealed.

Certificates and bounds are frozen, module-created, nonsubclassable, and
nonpickleable. The immutable owner binds exact identities. Validation rejects
plain and redigested tampering, hostile fields before equality, cross-owner
bounds even when digests match, changed parent identity, parent-surface drift,
local-helper drift, guard replacement, and construction-token substitution.
The local frozen surface covers parent aliases, contract constants, tokens,
field sets, digest helpers, theorem helpers, record validators/builders, and
record classes.

The operation profiler requires zero CP27 allocation, zero CP43 combined
evaluation, zero CP43 G, and zero CP43 semantic H calls. Python, NumPy, and
PyTorch caller/global RNG states must remain unchanged. The policy does not
claim absence of every transitive RNG call: inherited ancestry validation may
run a deterministic local Philox runtime probe. CP45 explicitly records
`transitive_rng_call_absence_certified=False` and
`loaded_code_integrity_certified=False`. Its controls are procedural and
same-runtime, not cryptographic or portable attestation.

## 6. Focused evidence

The 20 cases comprise four API/ancestry/bound/helper checks, seven exact
mathematical oracles, and nine sealing, operation, tamper, cross-owner,
hostile-input, dependency-drift, and static-surface checks. Exact rational
enumeration covers injective and colliding maps, nonuniform request laws,
conditioned partial success, k = 0, L <= k, and the constant-map nonconverse.
The source-independent subset returned **9/9 passed**. Its finite checks
exhaust deterministic maps for the selected small domains and request laws;
they are not Monte Carlo evidence or a claim about every finite domain.

The authoritative full command is

```text
/usr/bin/time -p env PYTHONPATH=src /private/tmp/diffusion-recovery-20260815/.venv-m1/bin/python -m pytest -p no:cacheprovider -W error --durations=20 -q tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_fixed_address_source_support_obstruction.py
```

**Final result:** **20/20 passed** in `19448.25 s` (`5:24:08`) under
warnings-as-errors, with no failures, errors, skips, xfails, xpasses, or
warnings. `/usr/bin/time -p` recorded `real 19448.78`, `user 18123.18`, and
`sys 1248.91` seconds. The seven reported nontrivial durations were
`11106.46`, `2720.75`, `2252.13`, `1710.70`, `707.31`, `652.97`, and
`296.61` seconds; all remaining cases completed in at most `0.05` seconds.

Static gates pass for Black, pyflakes, flake8 `E9,F63,F7,F82`, locked-runtime
syntax compilation, ASCII, AST parsing, exact 20-case collection, and the
exact 15-symbol export surface. The independent strict source/test review
found no remaining blocking static issue after four repair rounds covering
type preflight, dependency custody, unbounded-k canonicalization, honest RNG
wording, local helper custody, and owner-token custody.

The post-run source and test hashes exactly match the pre-run frozen values
above. A fresh post-run check also reconfirmed Black, pyflakes, flake8
`E9,F63,F7,F82`, locked-runtime syntax compilation, ASCII/AST parsing, and
exact 20-case collection. The final independent severity count is
`P0=P1=P2=0`. Accordingly, CP45's disposition is **PASS WITH EXPLICIT SCOPE
LIMITS**.

The venue-neutral Markdown and TeX manuscripts remain untouched with SHA-256
values `0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8`
and `0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9`.

## 7. Scope limits and next dependency

CP45 does not provide a positive live CP27/Philox product-uniform law,
nondegenerate V/W independence, success/value independence, allocation or
refusal probabilities, an unconditional CP44 law, natural F37 reachability,
semantic-output discrepancy, numeric semantic masses, physical randomness,
freshness, initializer/path/sampler admission, or empirical/model/generality
evidence. It changes no manuscript claim.

The next distributional step cannot honestly assert that a fixed-address
capsule is live product uniform. It must either introduce and audit an explicit
external random-seed/request law with every entropy-bearing coordinate counted,
or keep product-uniform laws counterfactual and derive only conclusions valid
for the deterministic live source.
