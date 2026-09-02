# Byte-Source Full-Capsule Execution: Incremental Code Audit

**Audit status:** **PASS WITH EXPLICIT SCOPE LIMITS**  
**Audit date:** 2026-08-18  
**Implementation:** [checkpoint-48 source](../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution.py)  
**Focused tests:** [checkpoint-48 tests](../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution.py)  
**Direct parent:** [checkpoint-47 execution-adapter audit](plugin_bridge_counter_keyed_initial_tilt_rejection_external_full_capsule_execution_adapter_code_audit.md)  
**Claim controls:** [claim ledger](claim_ledger.md)

Checkpoint 48 supplies a concrete byte-acquisition layer above checkpoint 47.
It accepts one exact byte block, decodes that block by a fixed manual big-endian
bijection into the complete `L`-word capsule expected by CP47, executes CP47
once, and retains the exact originating bytes together with the decoded words
and CP47 result.

This closes a byte-to-capsule execution gap. It does not close the source-law,
entropy, totality, IID, or scientific-evidence gaps. The system profile
certifies only a cached operational call to Python's `os.urandom` API; the
external profile certifies only the exact binding and invocation of a
caller-supplied callable. Neither profile certifies a probability law.

## 1. Frozen object of review

The source contains `2025` lines and `82973` bytes and has SHA-256

```text
7be4c1bdf588950902bbdfe03e492dea15e42d0affff5d6e83f6104b798974cd
```

The focused test contains `1692` lines and `62124` bytes, collects exactly `37`
cases, and has SHA-256

```text
2fa6f429424d95e851496fc870ca1d2598cf44f83a6adb98c673cc93ebcdf282
```

The 37 cases divide into 28 source-independent cases and nine owner-bound
cases.

Each certificate records a selected CP48 `execution_runtime_sha256`. That
value is a same-process procedural fingerprint, distinct from the source-file
digest, and includes process-local identities. The final pytest transcript did
not export its in-process value, so this audit deliberately does not present a
runtime digest as a frozen cross-process pin. Fresh-process probes need not
agree across processes, Python versions, or interpreter implementations;
same-process construction and validation consistency is the certified use.

The public surface exports exactly 18 names: schema, policy, and scope
constants; two profile constants and their exact profile tuple; byte-order,
bytes-per-word, product-law, IID, and success-conditioning constants; one
certificate type, result type, owner type, and error type; and three
certification, matching, and certificate-validation operations. It exports no
free-standing random-byte generator, retry controller, draw allocator,
sampler, path constructor, or manuscript-facing scientific operation.

Any change to either frozen file invalidates this audit until the hashes,
static gates, focused tests, and runtime evidence are regenerated.

## 2. Exact byte interface and codec theorem

Let

```text
B_L = {0, ..., 255}^{8L}
W_L = {0, ..., 2^64 - 1}^L.
```

The manual fixed-big-endian decoder groups each exact eight-byte segment into
one uint64 word. Its inverse emits the eight big-endian bytes of every word.
Hence it is a bijection

```text
decode_BE : B_L <-> W_L,
|B_L| = |W_L| = 2^(64L).
```

CP48 requires an exact built-in `bytes` object of length exactly `8L`. It
rejects byte subclasses, `bytearray`, memory views, coercible objects, short
blocks, and long blocks. It accepts every possible byte value without
filtering, rejection, normalization, replacement, fallback, or retry. The
decoded output is an exact tuple of `L` exact built-in integers in `[0, 2^64)`.

The finite-domain tests independently verify boundary patterns, one-hot bits,
byte order, production encode/decode agreement, exhaustive toy-domain
bijectivity, uniform pushforward, and total-variation preservation under a
bijection.

The probability conclusion remains conditional. If the entire `8L`-byte
block is jointly uniform on `B_L`, its decoded capsule is product-uniform on
`W_L`. Uniform one-byte marginals alone do not imply joint block uniformity or
word independence. Reusing one uniform block across calls also demonstrates
that individually uniform capsules need not be IID.

IID capsules across distinct draw identifiers require a joint or sequential
external premise establishing the corresponding independence of complete
byte blocks. Distinct identifiers, local retirement, or distinct backend calls
do not imply fresh, unequal, independent, or uniformly distributed values.

A further conditioning qualification applies to returned results. Even if an
acquired block is uniform, value-dependent failure in any remaining CP48 or
downstream step can bias the law conditional on return. Uniformity among
returned results therefore requires positive return probability and a
complete CP48 success likelihood that is constant over the full capsule;
totality is sufficient but not necessary. CP48 records this caveat and makes
no unconditional returned-result-law or semantic-output total-variation
claim. For an IID statement about a returned sequence, the joint return event
must additionally have positive mass and the complete joint success likelihood
must be constant over the full capsule vector; separate per-call marginal
success conditions do not establish that sequence claim.

## 3. Exact source profiles and backend boundary

CP48 supports exactly two profiles.

The `external-exact-byte-block-unverified` profile binds one exact
caller-supplied callable by process identity. On reaching the provider
boundary, it is called once with exactly three positional arguments:

```text
(source_instance_sha256, draw_index, byte_count)
```

The third argument is exactly `8L`. The return must be the exact byte block
described above. Backend exceptions propagate by identity. Malformed returns
fail without coercion, decode, retry, replacement, or a second backend call.

The `system-os-urandom-operational` profile binds an internal wrapper around
the module's cached `os.urandom` callable. It establishes one Python API call
at the certified provider boundary and exact output-shape validation. It does
not inspect or certify operating-system internals, syscall count, blocking
behavior, entropy provenance, uniformity, IID behavior, freshness, fork
behavior, cryptographic security, or reproducibility. The source-instance
digest and draw identifier are operational labels; they do not seed or
authenticate `os.urandom`.

For both profiles, "exactly once" is conditional on reaching the backend
boundary. A request rejected earlier by exact scalar preflight, owner drift
checks, or CP47's already-retired decision makes no backend call.

## 4. CP47 execution, retirement, and retained custody

CP48 preflights `run_id`, `initialization_index`, and `draw_index` as exact
built-in uint64 values. It then opens one private provider invocation context
and calls the bound CP47 owner's `execute` method at most once, and exactly
once if that boundary is reached.

CP47 remains the sole draw-retirement and semantic-execution authority. CP48
does not reserve, unreserve, retry, or select another draw. Once CP47 retires a
draw identifier, every subsequent failure---including backend exception,
wrong byte type, wrong byte length, decode or custody failure, or downstream
semantic failure---leaves the draw retired. A duplicate draw is refused by
CP47 before the byte backend.

When execution succeeds, CP48 retains:

- the exact original `bytes` object returned by the backend;
- its exact SHA-256 digest and exact byte count;
- the exact decoded full-word tuple;
- the exact CP47 result, receipt digest, retirement ordinal, and
  retirement-chain digest; and
- explicit one-call and round-trip facts.

The result validator checks exact type, certificate and owner identity, all
semantic digests, exact raw-byte length, byte/word equality, fixed-endian round
trip, and CP47 structural consistency. It does not call the byte backend,
rerun CP47 execution, or recompute CP43 semantics.

## 5. Ancestry and ordinary validation boundary

Certification binds one exact ancestry chain

```text
CP48 -> CP47 -> CP46 -> CP45 -> CP44 -> CP43
```

including certificate identities and digests, owner runtime identities,
source-instance and role digests, process-parameter digest, word counts, byte
count, and retirement capacity. It also binds the exact provider, backend,
selected profile, cached local operations, and selected dependency surfaces.

Certification performs one explicit live CP46 ancestry revalidation through
CP47. Ordinary execution, result validation, and ledger operations use the
sealed cached binding. The owner separately exposes explicit live-ancestry
revalidation, and public certificate matching uses that path. Successful
ordinary validation must not be described as a new live-parent attestation.

Certificates, results, the owner, and the private provider are exact
module-created, nonsubclassable, nonpickleable records or objects. Plain
tampering, redigested claim promotion, cross-owner result splicing, stale
ledger snapshots, hostile scalar objects, callback substitution, local-helper
drift, and CP47 dependency drift fail closed within the tested procedural
boundary.

These measures do not constitute cryptographic authentication, complete
loaded-code integrity, portability, or resilience to arbitrary same-process
private-state mutation.

## 6. Token custody, race evidence, and reentry boundary

The final design does not serialize the whole owner execution under an
`RLock`. Each invocation instead receives a fresh exact-object token. A
thread-local LIFO stack associates that token with its draw identifier, while
a separately locked shared acquisition map associates retained bytes and
words with the token rather than merely with the draw.

The protocol is:

```text
_begin -> CP47 execute/provider call -> _claim -> _end
```

On a normal failure after `_begin` returns, `_discard` removes only that
invocation's retained acquisition and `_end` removes only its thread-local
token. Losing cleanup cannot delete another thread's retained bytes merely
because both threads attempted the same draw. Nested same-thread execution
similarly uses distinct LIFO tokens.

The final race fixture deliberately isolates CP47's retirement decision. Two
threads attempt the same draw. The winner reaches and blocks inside the sole
backend call. Before that backend is released, the loser completes with
CP47's exact "draw_index is already retired" error. The winner is then
released and receives the fixture's exact backend-failure object. Thus the
fixture expects no successful semantic result and does not run CP43 semantics
for the contested draw. It checks one backend boundary, exact error
identities, cleanup of both worker thread-local contexts, and an empty
acquisition map.

The same-thread reentry fixture attempts the same draw recursively from inside
the backend. The inner request is refused by CP47, the outer request completes,
its LIFO context is removed, and the acquisition map is empty afterward.

This evidence supports only the following conservative statement:

> For the tested same-draw schedules, CP47 makes the retirement decision
> atomic, and CP48's per-invocation token protocol keeps retained-byte custody
> and cleanup isolated across the tested concurrent and nested invocations.

It does not establish general linearizability, concurrent semantic safety
beyond CP47 retirement, safety for arbitrary different-draw schedules,
provider thread safety, deadlock freedom of user callbacks,
asynchronous-cancellation safety, or resilience to hostile introspection and
private-state mutation. The corresponding broad concurrency/reentry
certificate flag remains false.

### P3 asynchronous `CALL`-to-`STORE` nonclaim

The owner initializes `execution_token = None` and then assigns the result of
`_provider._begin(...)`. `_begin` rolls back its own stack mutation if an
ordinary exception occurs before it returns. Once the assignment completes,
the enclosing exception and `finally` paths discard retained custody and end
the token.

A narrow interpreter-level interruption remains outside the certified
boundary: an asynchronously injected exception could theoretically arrive
after `_begin` has returned but before its return value is stored in
`execution_token`. In that `CALL`-to-`STORE` window, the thread-local token
could remain installed while the caller's sentinel is still `None`, preventing
the outer cleanup from naming it. No ordinary frozen execution path or focused
test triggers this window.

This is retained as a P3 scope nonclaim, not represented as
asynchronous-cancellation safety and not promoted into a broader concurrency
guarantee.

## 7. Runtime fingerprint and its limits

The runtime fingerprint covers selected CP48 owner methods, all private
provider token and custody methods, local guards, frozen helper surfaces,
Python version and implementation, and the inherited marshal-v2
code-fingerprint format. The focused regression requires exact frozen local-
surface identities, detects a synthetic code-constant change, and verifies
late-string-interning stability. Separate hostile tests exercise provider,
local-backend, and CP47 binding drift and require fail-closed responses.

The fingerprint includes `_LOCK_FACTORY`, `_THREAD_LOCAL_FACTORY`, `_begin`,
`_active_token`, `_end`, `__call__`, `_claim`, `_discard`, and the owner's
`execute` path. This prevents the final token design from silently inheriting
the earlier owner-wide locking implementation while retaining the same
certificate.

The runtime digest is nevertheless selected-code, same-process procedural
evidence. It does not authenticate the source file, bind every Python or
native callee, establish backend loaded-code integrity, survive arbitrary
hostile mutation, or provide a portable identity across interpreters and
processes. The source-file SHA-256 above remains the frozen artifact
identifier.

## 8. Rejected authoritative attempts

Two long attempts preceded the frozen authoritative run. Neither is accepted
as positive execution evidence.

| Attempt | Collected outcome | Pytest elapsed | External real time | Disposition |
|---|---:|---:|---:|---|
| Owner-wide `RLock` revision | 26 passed, 9 owner-bound setup errors | `12271.97 s` | `12324.64 s` | Rejected |
| Token revision with old success-race fixture | 28 passed, 9 owner-bound setup errors | `10956.72 s` | `11152.76 s` | Rejected |
| Frozen token revision with isolated failure-race fixture | 37/37 passed | `15191.58 s` | `15192.11 s` | Authoritative pass |

The first attempt held an owner-wide reentrant lock across execution. Its race
fixture required observing the competing request while the first request was
held at the backend boundary. The broad lock prevented the competitor from
reaching CP47's duplicate-retirement decision during that interval, so the
shared owner fixture failed and all nine dependent cases ended as setup
errors. The result motivated removal of owner-wide execution serialization;
it is not evidence that the final token protocol passes.

The second attempt contained the per-invocation token protocol but retained
the older race fixture, which expected the winning invocation to continue
through successful downstream semantics. That fixture conflated CP47's atomic
retirement property with unrelated and expensive CP43 semantic completion and
again failed to yield admissible owner-bound evidence. Its 28 passing
source-independent cases remain useful diagnostic history but cannot
substitute for the successful frozen owner-bound run.

The final fixture stops the winning contested request immediately after the
sole backend boundary with an exact marker exception. It therefore isolates
the intended retirement and token-cleanup facts without asking the race to
complete CP43 semantics.

## 9. Focused evidence and final disposition

The 28 source-independent cases cover:

- exact public surface, signatures, profiles, claim sets, and negative claims;
- manual codec boundaries, one-hot bits, fixed byte order, exhaustive toy
  bijectivity, and production round trips;
- full-block uniform pushforward, marginal-law insufficiency, IID
  counterexamples, conditioning bias, support loss, and total-variation
  boundaries;
- exact byte type and length, hostile no-coercion inputs, one backend call,
  exception identity, and absence of retry or cache;
- system-wrapper operational shape only;
- private token cleanup, concurrent token separation, and custody isolation;
  and
- record sealing, synthetic code-digest sensitivity, late-interning stability,
  dependency drift, and AST operation-surface restrictions.

The nine owner-bound cases share one genuine CP46 construction and cover both
profiles; exact CP47/46/45/44/43 ancestry; certificate flags; execution and
validation call budgets; exact byte/word/CP47 custody; burned-draw failure
paths; duplicate refusal; the isolated same-draw race; same-thread reentry;
system-profile shape evidence; tamper and cross-owner splice rejection;
hostile scalar preflight; and local backend and CP47 drift.

The authoritative full command was:

```text
/usr/bin/time -p env PYTHONPATH=src /private/tmp/diffusion-recovery-20260815/.venv-m1/bin/python -m pytest -q -p no:cacheprovider -W error --durations=37 tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution.py
```

**Final result:** **37/37 passed** in pytest `15191.58 s` (`4:13:11`) under
warnings-as-errors. The shared owner fixture setup consumed `15048.01 s`. The
external timer recorded real `15192.11`, user `13929.09`, and sys `1211.79`
seconds. There were no failures, errors, skips, xfails, xpasses, or warnings.

The post-run source-independent partition returned **28/28 passed**, with the
nine owner-bound cases deselected, in `2.16 s`. Post-run static gates pass for
Black, locked-runtime `py_compile`, Pyflakes, and fatal Flake8
`E9,F63,F7,F82`. Post-run source and test hashes exactly match the frozen
values in Section 1.

Three independent final strict audits of the source, tests, and integrated
claim boundary ended at `P0=P1=P2=0`. The asynchronous `CALL`-to-`STORE`
interruption remains deliberately recorded as the P3 nonclaim in Section 6.

The venue-neutral Markdown and TeX manuscripts remain untouched with SHA-256
values

```text
0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8
0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9
```

Accordingly, CP48's disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

## 10. Scope limit and next dependency

CP48 implements exact operational byte acquisition, a bijective byte-to-word
codec, per-invocation custody, and direct CP47 execution. It does not prove
that either backend is total, uniform, IID, fresh, physically random,
cryptographically secure, authenticated, reproducible, or independent of
complete CP48 success. It does not establish global uniqueness across owners,
processes, forks, restarts, or machines.

It also does not admit an initializer, path, or sampler; establish model
quality, domain generality, or empirical scientific evidence; certify a
semantic-output total-variation lower bound; or promote a manuscript claim.
This checkpoint is code-and-evidence work only and does not itself revise the
venue-neutral manuscript.

A subsequent live-source dependency would need to state and test the exact
source-law and success assumptions required by the intended theorem. Any
stronger concurrency claim would require a separately specified concurrency
model and targeted evidence beyond the tested CP47 retirement schedules.
Initializer, path, sampler, multi-domain experiments, ablations, and
manuscript promotion remain separate later obligations.
