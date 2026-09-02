# External Full-Capsule Execution Adapter: Incremental Code Audit

**Audit status:** **PASS WITH EXPLICIT SCOPE LIMITS**  
**Audit date:** 2026-08-17  
**Implementation:** [checkpoint-47 source](../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter.py)  
**Focused tests:** [checkpoint-47 tests](../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter.py)  
**Direct parent:** [checkpoint-46 source-model contract](plugin_bridge_counter_keyed_initial_tilt_rejection_explicit_source_model_contract_code_audit.md)  
**Claim controls:** [claim ledger](claim_ledger.md)

Checkpoint 47 adds the external full-capsule execution interface left absent by
checkpoint 46. One bound provider receives a source-instance digest, local draw
identifier, and exact word count and must return an exact tuple of all `L`
uint64 source words. The adapter ingests that tuple by the identity map, uses
the checkpoint-43 split/join construction, and invokes checkpoint 43's combined
semantic entry point.

This closes an executable interface gap, not a probability-law gap. CP47 does
not implement or certify the provider's law, totality, independence, freshness,
or physical origin. Its `D^L` statement is an interface-cardinality theorem.
Product-uniform and IID conclusions remain conditional on external source-law
premises, and a law conditional on returned results additionally requires
total or value-independent provider and downstream success.

## 1. Frozen object of review

The source contains `2512` lines and `108814` bytes and has SHA-256
`2c1522cd92f186d3d428e627bdd7ba6f29a7b8fbf727fb8ca8b7852f1badcf0b`.
The focused test contains `1446` lines and `52122` bytes, collects exactly `31`
cases, and has SHA-256
`46ab42233351a681b5b7618fcbff088e1e4f474f0350b636e081148fb2af2ced`.

The public surface has exactly 20 exported names: ten schema, policy,
scope, theorem, domain, bound, and provider-mode constants; seven record,
alias, owner, and error symbols; and three certification, matching, and
certificate-validation operations. It exposes no random-word generator,
provider implementation, retry controller, CP27 allocation operation, CP36
preparation operation, CP37 decision operation, or CP44 execution operation.

The certificate, provider receipt, execution result, and ledger snapshot are
module-created exact record types. The owner binds one exact CP46 owner, one
exact provider callback, one source-instance digest, two role digests, and one
bounded local retirement ledger. The public surface does not turn those
procedural bindings into a cryptographic or portable attestation.

## 2. Direct interface capacity and conditional probability statements

Let `D = 2^64`, let the full capsule contain `L` words, and let its fixed CP43
partition contain `M` proposal words and `A` decision words, with `L = M + A`.
The exact provider-return interface is

```text
[D]^L = {0, ..., 2^64 - 1}^L,
|[D]^L| = D^L = 2^(64L).
```

CP47 accepts that full tuple directly. The ingestion map from the provider
return to the source capsule is the identity, and hence is a bijection on all
`D^L` interface values. This establishes enough *interface capacity* to carry
a product-uniform capsule; it does not establish that any bound provider uses
that capacity according to the product-uniform law.

If one successfully returned provider capsule has law `U_L`, uniform on
`[D]^L`, the certified coordinate partition yields independent
product-uniform proposal and decision blocks. IID capsules across distinct
draw identifiers additionally require the provider to realize external IID
draws. Neither distinct identifiers nor the local retirement ledger imply
distinct, fresh, or independent values: the tests intentionally accept equal
capsule values under two different draw identifiers.

Provider or downstream failure can change the conditional law. If success
depends on capsule value, conditioning on a returned adapter result can bias
even an otherwise uniform source. Concluding that the capsule law among
returned adapter results remains `U_L` therefore requires provider and
downstream totality or the relevant value-independent success premise. CP47
records this caveat and certifies no provider success mass, refusal mass,
totality, unconditional returned-result law, or semantic-output
total-variation lower bound.

## 3. One-shot provider execution and local retirement

An execution preflights the run identifier, initialization index, and draw
identifier as exact built-in integers in `[0, 2^64)`. It then reserves the draw
identifier under the owner's lock before calling the provider. The immutable
ledger state is replaced by one new `(rows, retirement_chains)` pair, where a
row records the retirement ordinal, run identifier, initialization index, and
draw identifier. Domain-separated retirement-chain digests bind the
certificate, owner runtime identity, preceding chain state, and exact row.

Retirement uniqueness is deliberately local and keyed by draw identifier. A
second request using the same draw identifier is refused before the provider,
even if its run and initialization coordinates differ. The configured ledger
capacity is bounded between one and 65536 rows. It is an in-memory,
one-owner-lifetime property, not persistent uniqueness across owners,
processes, restarts, machines, or experiments.

Once an API-mediated reservation completes, CP47 never rolls it back. A
provider exception, a malformed outer return, a malformed word, or a later
downstream failure leaves the draw retired. The provider is invoked at most
once per execution and exactly once if execution reaches its boundary. There
is no coercion, retry, fallback, replacement draw, or adaptive draw-identifier
selection. The callback receives exactly

```text
(source_instance_sha256, draw_index, L)
```

and its return must be an exact tuple of length `L` whose elements are exact
built-in integers in `[0, 2^64)`. Bools, NumPy integers, lists, out-of-range
values, coercible objects, and hostile touch-bomb elements fail closed.

After exact preflight, the same full tuple is retained in the sealed provider
receipt and result. CP43 supplies the exact proposal/decision split, the join
must reconstruct the original tuple, and CP43's combined entry point evaluates
`G` once followed by the private semantic `H` once. CP47 calls neither CP44
`execute` nor the legacy CP27, CP36, or CP37 public execution routes.

## 4. Exact ancestry, cached operations, and nonreplaying validation

Certification binds the exact owner and certificate chain

```text
CP46 -> CP45 -> CP44 -> CP43
```

including every owner runtime identity, certificate identity and digest,
checkpoint-44 process-parameter digest, full/proposal/decision word counts,
and the checkpoint-43 split/join and combined-entrypoint contracts.
Certification performs exactly one explicit CP46 live-ancestry revalidation.
Ordinary execution, result validation, and ledger operations instead use the
sealed cached ancestry. The owner separately exposes explicit live
revalidation, and public matching and certificate validation use that path.
Cached operation success must not be read as a fresh live-parent attestation.

For each of the two successful fixture executions, the trace records no CP27
allocation, CP36 preparation, CP37 decision, CP44 execution, or CP46 live
revalidation. It records six CP46 cached-binding checks, two observed CP43
split calls, one join, one combined evaluation, one `G`, one semantic `H`, and
two structural applied-record validations. The second split observation is
intentional: CP43's join implementation internally reuses its split contract.

Duplicate refusal, provider exception, malformed outer return, and malformed
element paths each perform one cached CP46 binding check and no CP43 semantic
operation. Validation of two retained results performs four cached CP46 checks
and two CP43 structural validations but calls neither the provider nor CP43
`G` or `H`. Snapshot validation performs two cached CP46 checks and no source
or semantic operation.

Result validation is structural and nonreplaying. It checks the exact sealed
receipt, full words, partition, CP43 applied record, semantic status, owner
identity, retirement ordinal, and retirement-chain binding without calling the
provider or recomputing semantics. Ledger validation additionally requires an
exact match to the current owner state; a formerly valid but stale snapshot is
rejected.

## 5. Custody, tamper resistance, and concurrency boundary

Certificates, provider receipts, results, ledger snapshots, and the owner are
frozen, module-created, nonsubclassable, and nonpickleable. Semantic digests
bind every record payload. Owner snapshots bind the exact certificate,
provider, CP46/45/44/43 ancestry, local guard, lock, selected callbacks, and
immutable ledger-state representation. Results, receipts, and snapshots bind
the owner runtime identity where ownership matters; retirement-chain digests
bind that identity together with the exact rows. Cross-owner result and ledger
splicing is rejected even when the owners share the same CP46 ancestry,
provider, certificate contents, and retired row values.

Plain tampering, stale digests, redigested claim promotion, wrong exact types,
bool ordinals, hostile fields, stale snapshots, certificate substitution,
provider substitution, local-helper drift, CP46 validator drift, and CP43
method drift fail closed. Structural validation does not replay source or
semantic operations while rejecting these changes.

The lock makes one draw-retirement decision atomic. In the focused race, two
threads attempt the same draw identifier: exactly one obtains ordinal five and
the other receives the exact CP47 refusal. This is not a broader concurrent or
reentrant semantic-safety claim. CP47 does not certify provider thread safety,
operation linearizability beyond the reservation transition, immunity to ABA
mutation, or correctness under arbitrary hostile same-process interference.

In particular, a provider that obtains an ambient reference to its owner and
uses introspection or `object.__setattr__` to alter private state is outside the
procedural guarantee. The adapter promises that its own API does not roll back
a completed reservation; it does not promise resilience against arbitrary
same-process private-state mutation.

## 6. Runtime fingerprint repair and its exact scope

One pre-freeze authoritative attempt was rejected. Its 22 source-independent
tests passed, while all nine owner-bound cases ended as setup errors after
`3941.79 s`. During certificate creation, the first
`execution_runtime_sha256` differed from its immediate constructor-time
recomputation. The defect was fail-closed, but it made the execution evidence
inadmissible.

The cause was the default form of `marshal.dumps(code)`. CPython's default
marshal format can encode live shared-reference and string-interning state, so
unchanged code objects can acquire different serialized bytes after late
interning or under a different active reference topology. A long CP46 build
made that hidden state dependence observable at CP47's certificate boundary.

The frozen repair uses explicit marshal version two, whose representation has
no reference table. It requires an exact Python code object and recursively
limits code constants to exact `None`, Boolean, integer, text, tuple, and
code-object values. Function positional and keyword defaults must be `None` or
have exact tuple/dict container types; exact primitive and supported container
defaults are fingerprinted by value, while other default objects are
represented by exact runtime type and process identity. The runtime payload
binds the marker

```text
python-marshal-v2-no-reference-table-exact-constant-domain-process-identity-default-fingerprint-v1
```

Regression evidence requires an actual code-constant change to alter the
digest while late interning leaves it unchanged. It also mutates one selected
runtime code object, proves digest sensitivity, interns a new text constant,
proves stability, restores the original code, and recovers the original
runtime digest. Unsupported top-level and nested constants, malformed default
containers, and distinct nonprimitive default identities are separately
checked. The AST gate requires the sole cached marshal call to have the
literal version argument two.

This is a selected-code, same-process procedural fingerprint. It is not a
portable code identity, a signature, cryptographic authentication, or proof of
complete loaded-code integrity. It does not bind every Python or native callee,
the provider's implementation, arbitrary interpreter state, or behavior across
Python versions and processes. Those limitations are explicit negative claims,
not conclusions repaired by marshal version two.

## 7. Focused evidence and final disposition

The 31 cases divide into 22 fast source-independent cases and nine owner-bound
cases. The fast set covers the exact public API and signatures;
small finite-domain product-uniform, marginal, IID, conditioning, balanced-
fiber, support, bijection, and total-variation oracles; identity ingestion;
exact uint64 and hostile preflight; retirement bounds and claim polarities;
runtime-fingerprint stability and sensitivity; canonical ledger rows; and the
AST operation surface. These exact small-domain checks are not Monte Carlo
evidence and do not prove that a live provider realizes any source law.

The nine owner-bound cases share one genuine CP46 construction. They cover the
exact CP46/45/44/43 ancestry and every claim flag; certification, execution,
and structural-validation operation budgets; equal returned values under
distinct draw identifiers; exact provider receipts and results; provider
exception and malformed-return retirement; duplicate refusal; the atomic
same-draw reservation race; sealed custody; hostile scalar preflight; plain,
redigested, and hostile tampering; stale snapshots; cross-owner splicing; and
local, CP46, provider, and CP43 drift.

The AST gate finds no direct `random`, `secrets`, NumPy, or PyTorch import and
no OS entropy call. It finds no CP27 allocation, CP44 execution, CP36 prepare,
or CP37 decide call. CP43 split, join, and combined evaluation are restricted
to the owner's `execute` method. This is direct adapter-call evidence only;
provider effects are outside it.

The CP47 run exercises its genuine inherited construction but is not a
separate rerun of every complete CP43, CP44, CP45, or CP46 focused suite. Their
frozen certificate identities and hashes are inherited at this checkpoint.

The authoritative full command is

```text
/usr/bin/time -p env PYTHONPATH=src /private/tmp/diffusion-recovery-20260815/.venv-m1/bin/python -m pytest -q -p no:cacheprovider -W error --durations=31 tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter.py
```

**Final result:** **31/31 passed** in pytest `7763.03 s` (`2:09:23`) under
warnings-as-errors. The shared owner fixture setup consumed `7659.66 s`. The
external timer recorded real `30735.62`, user `7141.85`, and sys `545.25`
seconds; the real time includes host suspension and therefore is not the
active pytest elapsed time. There were no failures, errors, skips, xfails,
xpasses, or warnings. The post-run source-independent partition returned
**22/22 passed** in `1.17 s` on the frozen source and test.

Post-run static gates pass for Black, locked-runtime syntax compilation,
pyflakes, and flake8 `E9,F63,F7,F82`. Post-run source and test hashes exactly
match the frozen values above. Independent final strict audits of the source,
test, and repaired fingerprint boundary ended at `P0=P1=P2=0`.

The venue-neutral Markdown and TeX manuscripts remain untouched with SHA-256
values `0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8`
and `0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9`.
Accordingly, CP47's disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

## 8. Scope limit and next dependency

CP47 implements direct transport of one externally supplied full capsule into
the exact CP43 reference execution. It does not implement the external source
or establish that the source is live, total, product uniform, IID across calls,
fresh, physically random, or independent of provider and downstream success.
It certifies neither global cross-owner/process/restart uniqueness nor broad
concurrent or reentrant semantics. It provides no adaptive retry contract and
no semantic-output total-variation lower bound.

CP47 also does not admit an initializer, path, or sampler; establish scientific
or model-quality evidence; demonstrate domain generality; or promote any
manuscript claim. It changes no venue-neutral manuscript text.

A future live-source dependency would need an implemented provider with an
auditable realization of its full `L`-word law, totality or the required
value-independent success contract, explicit IID/freshness and entropy-origin
premises, and persistence or concurrency mechanisms for any stronger
uniqueness claim. Initializer/path/sampler integration and empirical model
evidence would remain separate subsequent obligations. Until those are
implemented and executed, CP47's `D^L` capacity and product-law statements
must remain interface and conditional theorems rather than live randomness or
scientific claims.
