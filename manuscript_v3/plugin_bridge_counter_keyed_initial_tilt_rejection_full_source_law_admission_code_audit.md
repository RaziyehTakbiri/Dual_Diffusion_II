# Full-Source Law Admission: Incremental Code Audit

**Audit status:** **PASS WITH EXPLICIT SCOPE LIMITS**  
**Audit date:** 2026-08-20  
**Implementation:** [checkpoint-49 source](../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission.py)  
**Focused tests:** [checkpoint-49 tests](../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission.py)  
**Direct parent:** [checkpoint-48 byte-source audit](plugin_bridge_counter_keyed_initial_tilt_rejection_byte_source_full_capsule_execution_code_audit.md)  
**Claim controls:** [claim ledger](claim_ledger.md)

Checkpoint 49 adds an explicit assumption gate above checkpoint 48. It records
caller-declared mathematical premises for one individually fixed request,
states the resulting CP43/CP42 object-semantic reference pushforward, describes
that theorem without executing a source, and structurally admits an
already-returned CP48 record into the theorem's four-status codomain.

This closes a theorem-statement and structural-admission gap only under the
recorded assumptions. It does not verify either byte-source profile, establish
backend totality, execute CP48, replay CP43 or CP42, prove a sequence law,
admit a CP40 initializer, close formal Test 28, or supply scientific evidence.

## 1. Frozen object of review

The source contains `1913` lines and `84530` bytes and has SHA-256

```text
7951c02c60b6ca8dbbbf025f13e26e52eb7319cd4c48d416e5b841d99530bd39
```

The focused test contains `1765` lines and `70075` bytes, collects exactly 28
cases, and has SHA-256

```text
a799c68ebe2d9fa415bf1282a2f28c4f87570a7d21a728373d61f5a34a100e7a
```

The 28 cases divide into 21 source-independent cases and seven owner-bound
cases.

The public surface exports exactly 21 names: schema, policy, and scope
constants; the assumption mode and scope; the four-status tuple; the
pushforward theorem, return-conditioning caveat, selected-fiber theorem, and
sequence nonclaim; four record types, one owner type, and one error type; and
five declaration, validation, certification, and matching operations. The
owner exposes no `execute` method, and the module exports no byte generator,
retry controller, CP40 admission operation, initializer, path constructor, or
sampler.

Each certificate records an `admission_runtime_sha256` and a
`process_context_sha256` that incorporates the selected CP48 execution-runtime
fingerprint. These are same-process procedural witnesses, not portable
source-file identities. They include runtime-sensitive code and owner identity
context and need not agree across processes, Python versions, or interpreter
implementations. This audit therefore does not present either runtime value as
a frozen cross-process digest. The source-file SHA-256 above is the frozen
artifact identifier.

Any change to either frozen file invalidates this audit until the hashes,
static gates, focused tests, and runtime evidence are regenerated.

## 2. Exact external assumption declaration

CP49 supports one v1 assumption mode. A declaration binds the exact CP48
certificate digest, source-instance digest, one of CP48's two exact source
profiles, and an assumption-role digest. It then requires five exact built-in
`True` premises:

1. the backend returns one exact complete byte block almost surely;
2. the unconditional law of that complete block is jointly uniform;
3. the fixed pre-operation state has a fresh draw, available retirement
   capacity, and passing preboundary guards;
4. every exact byte value completes successfully after the backend boundary;
   and
5. the CP43/CP42 object semantics are fixed, runtime-deterministic,
   replay-stable, typed, and total for the stated kernel.

False premises, integer substitutes for booleans, subclasses, coercible hostile
objects, malformed digests, and invented profiles are refused. Declaration
creation performs no source query and does not inspect a backend.

The resulting record explicitly fixes `assumption_only=True`. It also records
positive complete-return mass and value-independent complete success as
assumed consequences of the v1 antecedent. At the same time it fixes sequence
IID, adaptive-query coverage, operational realization, backend-law
verification, backend-totality verification, `os.urandom` law verification,
and external-callback law verification to false.

The `system-os-urandom-operational` profile does not turn the declaration into
an attestation of Python, the operating system, entropy, uniformity,
independence, freshness, blocking behavior, or security. The
`external-exact-byte-block-unverified` profile similarly does not attest the
caller-supplied callback. Profile selection only binds the declaration to the
matching CP48 owner and certificate.

The declaration and role digests are semantic custody labels, not signatures,
authentication, or evidence that the declared premises hold in nature or in a
live runtime.

## 3. Pointwise one-draw pushforward theorem

Let

```text
B_L = {0, ..., 255}^{8L},
W_L = {0, ..., 2^64 - 1}^L,
```

and let `C : B_L <-> W_L` be CP48's certified fixed-big-endian bijection. For
one fixed request in one fixed admissible pre-operation state, CP49 defines the
enriched semantic projection

```text
T_obj(w) =
    (
        status,
        comparison_count,
        selected_attempt_index,
        canonical bit-exact CP42 configuration value or None,
    ).
```

The status is one of

```text
preparation_failure
quota_certification_failure
selected
exhausted
```

and the two failure atoms remain distinct from exhaustion. Replacing only the
last component of a selected atom by its canonical configuration SHA-256
recovers CP44's canonical projection of the retained CP43 applied decision.
The actual CP42 configuration object is separately retained by identity as
custody evidence.

For an unconditional complete-block law `mu`, the recorded theorem is

```text
Law(T_obj(C(B))) = (T_obj o C)#mu
```

and data processing gives

```text
TV((T_obj o C)#mu, T_obj#U_words) <= TV(mu, U_bytes).
```

Because `C` is bijective, the byte-to-word step preserves total variation
relative to uniform. The potentially many-to-one semantic map can only
contract it. There is no converse and no semantic-output total-variation lower
bound: a constant semantic map can erase an arbitrarily large source-space
discrepancy.

Under the declared jointly uniform complete-block premise, `mu=U_bytes`, so
the right-hand side is zero and the object-semantic law equals the stated
uniform-word reference pushforward. This is an assumption-gated mathematical
conclusion, not an observed law for either CP48 backend. Uniform byte marginals
do not discharge the premise; the entire `8L`-byte block must have the stated
joint law.

## 4. Return conditioning and sequence boundary

Let `R` be complete return, let

```text
s(b) = P(R | B=b),
Z = sum_b mu(b) s(b),
```

and assume `Z>0`. CP49 records the exact returned-word formula

```text
P(C(B)=w | R)
    = mu(C^-1(w)) s(C^-1(w)) / Z.
```

For a jointly uniform complete-block source, the returned word law is uniform
if and only if complete-success likelihood is positive and constant over the
whole block domain. Backend almost-sure exact-block return together with
post-boundary success for every byte value is sufficient inside the declared
kernel. CP49 does not operationally verify either condition.

The pre-operation antecedent remains essential. Declaring a fresh draw and
available capacity does not make an already-retired draw fresh, enlarge a
retirement ledger, or force malformed identifiers and failing guards to pass.
Duplicate-draw refusal, capacity exhaustion, and other preboundary refusals
remain outside the totalized kernel.

The theorem is pointwise for each individually fixed request. Separate
one-draw uniformity and separate value-independent marginal success do not
establish IID returned results. A sequence theorem would require a joint
product-uniform complete-block vector law, or a sequential premise that each
new block is conditionally uniform given the full prior and adaptive history
for distinct pre-admissible requests. It would also require positive joint
return mass and a joint complete-success likelihood constant over the entire
block vector.

Adaptive stopping, retry, fallback, replacement, and source-dependent request
selection remain outside CP49. Distinct draw identifiers do not imply distinct
sample values, value independence, freshness, or global uniqueness.

## 5. Four-status custody and selected-fiber witness

CP49 can structurally admit one already-returned CP48 result. It preserves:

- the exact CP48 result and result digest;
- the exact retained CP43 applied-decision object and digest;
- run, initialization, and draw identifiers;
- source-instance and source-profile custody;
- raw-byte and full-word digests;
- the natural semantic status and comparison count; and
- for selection, the exact selected-attempt index and exact nested CP42
  configuration object by identity and canonical digest.

For a selected result, the retained exact full-word capsule witnesses one
preimage under `T_obj` of the enriched selected atom. Hence that enriched fiber
is nonempty, and the coarser configuration-value fiber is also nonempty.

Under the separately declared uniform-word and total deterministic-semantics
premises, every individual word capsule has reference mass

```text
2^(-64L).
```

A witnessed selected fiber and the overall selection event therefore have
abstract reference mass at least `2^(-64L)`. This makes the
selected-conditioned reference law well-defined under those assumptions. It
is not a measured selection probability, source-law attestation, live
initializer distribution, or probability law over runtime object identities.

For a nonselected result, all selected-fiber, positive-selection-mass, and
selected-conditioned-reference flags remain false, and the single-preimage
denominator field remains `None`.

CP49 does not construct or retain a CP40 result, initializer result, intensity,
lineage, tag-3 payload, sampler path, or general initializer artifact.

## 6. Nonexecuting operational boundary

The CP49 owner has four relevant operations.

`describe(run_id, initialization_index, draw_index)` checks exact built-in
uint64 coordinates and constructs a fixed-request theorem description. It does
not acquire bytes, execute CP48 or CP47, evaluate CP43 or CP42, or verify the
preboundary and source-law premises.

`admit_returned_result(cp48_result)` invokes the bound CP48 structural result
validator and constructs a CP49 custody record. It does not rerun CP48,
reacquire bytes, replay CP43, or rebuild CP42 semantics.

`validate_admission_result(result)` structurally revalidates CP49 and CP48
custody. It likewise performs no source or semantic replay.

`revalidate_live_ancestry()` is the sole explicit live-parent operation. It
calls CP48's live-ancestry revalidation but does not call the byte backend,
CP48 execution, CP47 execution, or CP43 evaluation.

The frozen CP49 source contains no `os`, `random`, `secrets`, or NumPy import,
no retry loop, no CP48 execution binding, and no direct CP39 or CP40
operational route. The focused profiler fixtures fail immediately if
certification, description, admission, or ordinary validation crosses a
forbidden backend, execution, allocation, or semantic-evaluation boundary.

These properties do not convert structural validation into a fresh live-parent
attestation. Ordinary operations use the owner's sealed cached bindings;
explicit live revalidation remains separately named.

## 7. Exact ancestry, sealing, and runtime fingerprint

Certification binds the exact chain

```text
CP49 -> CP48 -> CP47 -> CP46 -> CP45 -> CP44 -> CP43
```

including CP48, CP47, and CP43 certificate digests; CP48 owner runtime identity;
the exact assumption-declaration object and digest; source-instance and
profile fields; assumption and admission role digests; raw-byte and word
counts; and the inherited CP48 runtime context.

Certification checks the exact CP48 owner and certificate binding and uses
CP48's sealed owner snapshot and dependency surfaces. The CP49 certificate
records that source law is an external assumption only. Its internal
`passed=True` field denotes successful creation of an internally consistent
assumption-gated certificate; it is not an authoritative pytest result,
backend-law verification, premise discharge, or operational realization.

Declarations, certificates, descriptions, and results are exact
module-created, frozen, nonsubclassable, and nonpickleable records. The owner
is immutable, nonsubclassable, and nonpickleable. The frozen validation
surfaces reject plain tampering, attacker-redigested claim promotion,
cross-owner declaration or result splicing, hostile scalar objects, substituted
nested parent records, cached-callback drift, owner-property drift, and local
or CP48 dependency-surface drift within the tested procedural boundary.

The runtime fingerprint covers selected owner methods and properties, frozen
local helpers, Python version and implementation, and CP48's inherited
code-fingerprint format. The process-context digest additionally includes the
selected CP48 execution-runtime digest.

This remains selected-code, same-process evidence. It is not cryptographic
authentication, a complete loaded-code integrity proof, protection from
arbitrary same-process private-state mutation, or a portable identity across
processes and interpreters. The corresponding loaded-code-integrity and
runtime-portability certificate flags remain false.

## 8. First-success evidence and unintended-repeat containment

The frozen review set is the
[first-success snapshot](../verification_runs/cp49_authoritative_7951c02c_a799c68e_attempt01/first_success_snapshot/).
Its status record has SHA-256

```text
190b69082932609ff0b380bfab61fdeb39e086e31d428228e34cc73435262f4e
```

and its JUnit record has SHA-256

```text
aab973e13c02da0abafba6d277b05c0cd39037d7dd3b1a77be5da5101d0fc26a
```

The [status record](../verification_runs/cp49_authoritative_7951c02c_a799c68e_attempt01/first_success_snapshot/status.env)
reports `state=complete`, `phase=post_pytest`, shell and pytest exit codes zero,
and stable expected, pre-run, and post-run source and test hashes. It records a
run window from `2026-08-20T03:48:25Z` through `2026-08-20T10:52:30Z`.

The [JUnit record](../verification_runs/cp49_authoritative_7951c02c_a799c68e_attempt01/first_success_snapshot/junit.xml)
independently reports 28 tests, zero failures, zero errors, zero skips, and
suite time `25354.321 s`. Its 28 exact testcase names match the frozen focused
suite.

The saved [text transcript](../verification_runs/cp49_authoritative_7951c02c_a799c68e_attempt01/first_success_snapshot/authoritative.log)
requires an explicit boundary. Lines 1--30 are the complete first-success
transcript, ending with

```text
CP49 runner finished: exit=0 pytest=0 stable=true
```

Lines 31--40 are excluded from authoritative evidence. They record an
unintended automatic launchd repeat that began one second after the successful
run, printed the 21 source-independent progress dots, and was stopped before
producing another result. The separate
[repeat marker](../verification_runs/cp49_authoritative_7951c02c_a799c68e_attempt01/UNINTENDED_REPEAT_STOPPED)
records repeat PID `94633`, distinct from first-success PID `83779` in the
snapshot's `COMPLETE` marker.

The first-success status, JUnit, and `COMPLETE` files are byte-identical to the
retained top-level copies. The first-success and repeat PIDs are absent, the
launchd label is absent, and an independent post-run process-table inspection
found no CP49 pytest, `caffeinate`, or locked-environment runner. The stopped
repeat is neither a second pass nor negative test evidence, and none of its
partial output is used in the disposition.

This containment note is part of the evidence boundary. Describing the entire
saved text file as one pristine run, or treating its trailing dots as another
result, would be incorrect.

## 9. Focused evidence and final disposition

The 21 source-independent cases cover:

- the exact public surface and all signatures;
- exhaustive toy codec bijectivity and total-variation preservation;
- joint-law, marginal-law, IID, adaptive-stopping, and return-conditioning
  counterexamples;
- selected-fiber existence, zero-selection undefinedness, data processing,
  and the absence of a converse output-TV bound;
- identifier uniqueness versus sample-value collision;
- pure exact-count helpers without source-law promotion;
- all four semantic-status extraction branches and exact flag partitions;
- AST-level no-execution, no-RNG, no-retry, and no-CP39/CP40-route gates;
- record sealing and nonpickleability;
- exact assumption-only behavior under both CP48 profiles;
- hostile scalar, false-premise, tamper, and attacker-redigested claim refusal;
  and
- preservation of Python, NumPy, and Torch global RNG states by declarations
  and pure arithmetic helpers.

The seven owner-bound cases share CP48's genuine heavyweight owner fixture.
They cover both CP48 profiles; a genuine selected result; exact
CP49-through-CP43 ancestry; certificate and nonclaim flags; nonexecuting
descriptions; natural-status and selected CP42 object custody; structural
validation and separately explicit live ancestry; cross-owner splices;
redigested claim promotion; hostile nested parents; and local, property, and
dependency-surface drift.

The selected fixture uses exact zero proposal and decision words in a genuine
one-attempt model to reach the first selected row. That deterministic branch
witness is custody evidence only. It does not verify the fixture callback's
probability law or convert the declared source assumptions into observations.

The authoritative full command executed by the captured launchd runner was:

```text
/usr/bin/caffeinate -i /usr/bin/time -p /usr/bin/env PYTHONPATH=src PYTHONUNBUFFERED=1 /private/tmp/diffusion-recovery-20260815/.venv-m1/bin/python -m pytest -q -p no:cacheprovider -W error --durations=28 --junitxml=/Users/mahtab/.codex/.chatgpt-projects/g-p-6a5f91c1e79c819183983ba0010bb151/verification_runs/cp49_authoritative_7951c02c_a799c68e_attempt01/junit.xml tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_full_source_law_admission.py
```

The environment reported CPython `3.11.5`, pytest `9.1.1`, NumPy `2.4.6`, and
PyTorch `2.12.1`.

**Final result:** **28/28 passed** in pytest `25354.31 s` (`7:02:34`) under
warnings-as-errors. The shared owner fixture setup consumed `17897.94 s`. The
external timer recorded real `25366.40`, user `23535.81`, and sys `1681.97`
seconds. There were no failures, errors, skips, xfails, xpasses, or warnings.

The independent post-run source partition returned **21/21 passed**, with the
seven owner-bound cases deselected, in pytest `2.04 s`. Its external timer
recorded real `2.62`, user `1.67`, and sys `0.45` seconds.

Post-run static gates pass for Black, locked-runtime `py_compile`, Pyflakes,
and fatal Flake8 `E9,F63,F7,F82`. Post-run source and test hashes exactly match
the frozen values in Section 1.

Independent strict final reviews of the code, tests, evidence boundary, and
integrated claims ended at `P0=P1=P2=0` after the stopped-repeat exclusion in
Section 8 was made explicit.

The venue-neutral Markdown and TeX manuscripts remain untouched with SHA-256
values

```text
0569b18aefb2aefa6c24af0559880f66c4a0daa6b2073169d30c892515e976a8
0ad9abccbc38ccc41e9fb3f7a1f8db6a4a197d23c3946da60a3cd4b93b475ba9
```

Accordingly, CP49's disposition is **PASS WITH EXPLICIT SCOPE LIMITS**.

## 10. Scope limit and next dependency

CP49 records a coherent pointwise one-draw CP43/CP42 object-semantic
pushforward under exact external premises. It provides a nonexecuting theorem
description, structural admission of an already-returned CP48 record, and a
selected nonempty-fiber witness under those premises.

It does not establish that either CP48 backend is total, jointly uniform, IID,
fresh, physically random, cryptographically secure, reproducible, or
independent of complete success. It does not verify positive operational
return mass, preboundary admissibility, value-independent success, or fixed
total live semantics. It does not totalize duplicate draws, capacity
exhaustion, or malformed requests.

It also does not prove a joint or adaptive sequence law, global uniqueness
across owners or runtimes, legacy CP36/CP37 universal equivalence, discharge of
CP41's premise, a CP40 fixed-batch target or initializer admission, a live
initializer distribution, general initializer admissibility, exact ideal
rejection, global analytic-tilt normalization, lineage or tag-3 custody,
Brownian-stream execution, a path, or a sampler.

No formal Test 28 closure follows. Formal Tests 28 and 29 remain **OPEN**,
Test 30 remains **PENDING**, and `R2-HYBRID` remains **NOT RUN**. No C-row,
R-slot, model-quality claim, domain-generality claim, scientific conclusion,
or manuscript claim is promoted. This checkpoint is code-and-evidence work
only and does not itself revise the venue-neutral manuscript.

A later operational dependency would need independent evidence for the actual
backend law, totality, admissible pre-operation state, and complete-success
conditions before the CP49 reference law could be described as a live
initializer distribution. Any sequence claim would additionally require the
joint or sequential conditional source and joint-return premises stated in
Section 4. Initializer integration, path and sampler construction, experiments,
ablations, and manuscript promotion remain separate obligations.
