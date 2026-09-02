# Totalized Supplied-Word Factorization Closure: Incremental Code Audit

**Audit status:** **PASS WITH EXPLICIT SCOPE LIMITS**  
**Audit date:** 2026-08-16  
**Implementation:**
[checkpoint-43 source](../src/heterodiff/processes/plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure.py)  
**Focused tests:**
[checkpoint-43 tests](../tests/unit/test_plugin_bridge_counter_keyed_initial_tilt_rejection_factorization_closure.py)  
**Direct capability parent:**
[checkpoint-42 staged factorization](plugin_bridge_counter_keyed_initial_tilt_rejection_predecision_factorization_code_audit.md)  
**Abstract-law parent:**
[checkpoint-41 failure-aware source law](plugin_bridge_counter_keyed_initial_tilt_rejection_failure_aware_source_law_code_audit.md)  
**Method contract:** [executable method specification](executable_method_spec.md)  
**Claim controls:** [claim ledger](claim_ledger.md)

This document maps the forty-third incremental implementation checkpoint.
CP43 closes a deliberately bounded factorization gap by totalizing two exact
operational error classes as preparation failure, retaining CP42's modeled
quota-certification failure, and defining a supplied-word reference map whose
private semantic post-G kernel consumes decision words only after the
predecision stage has completed.

The result is a structural theorem about one fixed, certified owner and exact
caller-supplied uint64 tuples. It is not a theorem about the law of live Philox
words, not universal equivalence to every CP36/CP37 failure path, and not an
initializer, path, or sampler admission result. The separately callable public
replay facade also has a materially different operational chronology from
the private semantic kernel: it replays G to validate custody before applying
the kernel. That replay boundary is part of the theorem statement rather than
an implementation footnote.

## 1. Exact domain and factorization equation

Fix one certified CP42 owner, request identifier \(r\), initialization index
\(j\), attempt budget \(A\), and inherited proposal-word count \(M\). Let

\[
D=2^{64},\qquad [D]=\{0,\ldots,D-1\},\qquad
V\in[D]^M,\qquad W\in[D]^A,
\]

where both tuples are in the exact CP36-derived coordinate order. CP43 defines
the typed predecision map

\[
G^{43}_{r,j}:[D]^M\longrightarrow
\{F_{36},F_{37}\}\mathbin{\dot\cup}\mathcal R,
\]

where \(F_{36}\) is the totalized preparation-failure atom, \(F_{37}\) is
the modeled quota-certification-failure atom, and \(\mathcal R\) contains a
complete ready tuple \((K_0,\ldots,K_{A-1})\) together with its validated CP42
rows. The private semantic kernel is

\[
H^{43}_{\mathrm{sem}}:
\left(\{F_{36},F_{37}\}\mathbin{\dot\cup}\mathcal R\right)
\times[D]^A
\longrightarrow
\{F_{36},F_{37},E\}\mathbin{\dot\cup}\mathcal X,
\]

with

\[
\begin{aligned}
H^{43}_{\mathrm{sem}}(F_{36},W)&=F_{36},\\
H^{43}_{\mathrm{sem}}(F_{37},W)&=F_{37},\\
H^{43}_{\mathrm{sem}}(R,W)&=
\begin{cases}
x_{a^\star},&a^\star=\min\{a:w_a<K_a\}\text{ exists},\\
E,&\text{otherwise}.
\end{cases}
\end{aligned}
\]

The first two branches do not inspect, iterate, retain, hash, or compare
\(W\). The ready branch validates the complete exact \(W\) tuple before its
first word-to-quota comparison. The combined entry point implements

\[
T^{43}_{r,j}(V,W)
=H^{43}_{\mathrm{sem}}\!\left(G^{43}_{r,j}(V),W\right)
\]

by invoking one internal G evaluation followed by one private semantic-kernel
application.

This totality is conditional on the exact input domain, the declared typed-
error contract, one deterministic replay-stable owner, and the trusted runtime.
Malformed inputs, unexpected internal exceptions, error subclasses, custody
violations, and resource failures outside the declared contract remain
refusals. They are not silently added to \(F_{36}\) or \(F_{37}\).

## 2. Private semantic kernel versus public replay facade

`_apply_trusted` is the implementation counterpart of
\(H^{43}_{\mathrm{sem}}\). It
receives a validated CP43 predecision record and an owner snapshot. For
`preparation_failure`, it constructs the CP43 failure result directly. For
the CP42-backed branches, it delegates to CP42's applied-decision builder,
which passes modeled quota failure through without touching decision words and
fully preflights decision words on a ready record.

`apply_decision_words`, the public replay facade, is not a replay-free
realization of the same function.
It first validates the supplied predecision record by rerunning the exact
predecision computation on its retained \((r,j,V)\), compares the replayed
semantic digest, and only then calls `_apply_trusted`. Therefore:

- the private semantic failure branches are independent of \(W\);
- the public replay facade still performs G replay before reaching either
  branch;
- a transient first-call failure need not recur during public validation; and
- public failure pass-through requires deterministic, replay-stable failure
  behavior.

The certificate consequently records that the public replay facade replays G
for custody, while fixing both `separately_invoked_public_h_replay_free` and
`transient_failure_public_h_passthrough_certified` to false. The combined
entry point avoids this second G evaluation and is the direct executable
witness for the displayed composition equation.

## 3. Exact typed mapping to \(F_{36}\) and \(F_{37}\)

CP43 starts its parent-result slot with a private missing-value sentinel. It
catches only the exact CP28 reference-initializer operational error and exact
CP30 initial-tilt operational error. The catch path checks exact exception
type, requires that no CP42 value was retained, discards the exception payload,
and constructs \(F_{36}\). A wrong CP42 return, including `None`, is rejected
rather than being confused with totalized preparation failure.

All other CP28/CP30 exceptions remain refusals. In particular, subclasses of
the two declared types, a generic CP36 preparation exception, `ValueError`,
`ArithmeticError`, and unexpected internal failures are propagated under
their exact runtime types. Hence CP43 does not claim generic exception
totalization or unexpected-exception relabelling.

CP42 already maps only the exact CP37 quota-certification error to its modeled
`quota_certification_failure` status. CP43 preserves that status as
\(F_{37}\), retains the validated CP42 result and digest, and lets the private
semantic kernel return it without decision-word access. CP43 does not widen
the CP37 catch surface and does not claim that an unchanged valid parent
naturally reaches \(F_{37}\).

The operational partition is therefore

\[
G^{43}_{r,j}(V)=
\begin{cases}
F_{36},&\text{exact declared CP28 or CP30 operational error},\\
F_{37},&\text{CP42 returns modeled exact quota failure},\\
R,&\text{CP42 returns a complete ready record},\\
\text{refusal},&\text{outside the declared domain or contract}.
\end{cases}
\]

The last line is meta-level operational behavior, not another atom in the
mathematical codomain.

## 4. Owner, certificate, and replay custody

Certification accepts one exact CP42 owner and binds the following by exact
type, identity, inherited digest, or all three:

- the CP42 certificate and owner runtime identity;
- the CP41 certificate and factorization-hypothesis digest;
- the transitive CP36 and CP37 certificates and CP37 owner;
- process parameters, attempt budget, word counts, and coordinate digests;
- closure policy, role, supplied-word domain, theorem text, evidence ledger,
  product-uniform corollary, and reviewed F37 text; and
- the local runtime fingerprint.

Every public operation begins from a live CP43 owner snapshot. The snapshot
revalidates the complete CP43 certificate, exact frozen local identities,
live CP42 certificate identity, delegated CP42 snapshot, and CP37 ancestry.
Longer operations check the snapshot again after dependency calls and before
return. Certificate, result, witness, and owner records are exact-type,
sealed, nonsubclassable, immutable through their public surfaces, and
nonpickleable.

Semantic digests do not replace owner identity. Cross-owner predecision,
applied-decision, and witness records are refused even if an attacker
recomputes their ordinary record digest. Public result validation replays the
underlying operation and compares the replayed semantic digest. These are
same-process procedural custody controls, not cryptographic authentication.

## 5. Exact split/join partition

The inherited CP36 full tuple is interleaved by attempt. Within every attempt,
all proposal/transformation blocks precede the final one-word reserved
decision block. `split_full_words` walks the frozen block-count tuple in that
order, appends every nonfinal segment to \(V\), and appends the final segment
to \(W\). It requires exact tuple type, exact non-Boolean uint64 entries, the
certified total length, complete cursor consumption, and the certified output
lengths.

`join_full_words` requires the corresponding exact \(V\) and \(W\) domains,
reconstructs the attempt-interleaved full tuple, and calls the splitter to
verify the inverse identity

\[
\operatorname{split}(\operatorname{join}(V,W))=(V,W).
\]

Both operations take a live owner snapshot before reading their inputs and
require the same snapshot after construction; the nested split validation in
`join_full_words` does not replace the outer check. This establishes exact
coordinate custody for supplied tuples. It neither samples those tuples nor
establishes any distribution over them.

## 6. Conditional product-uniform corollary

The recorded corollary has explicit premises. For one fixed owner and runtime,
assume that G is deterministic, replay-stable, and total under the declared
typed-error contract, and introduce a separate abstract source

\[
V\sim\operatorname{Unif}([D]^M),\qquad
W\sim\operatorname{Unif}([D]^A),\qquad V\perp W.
\]

Because the spaces are finite, every \(F_{36}\), \(F_{37}\), and ready
fiber of G is measurable. Conditional on a ready value with quotas
\((K_0,\ldots,K_{A-1})\), the private kernel gives

\[
\Pr(a^\star=a\mid G(V)=R)
=\frac{K_a}{D}\prod_{i<a}\left(1-\frac{K_i}{D}\right),
\]

and

\[
\Pr(E\mid G(V)=R)
=\prod_{i=0}^{A-1}\left(1-\frac{K_i}{D}\right).
\]

The two failure fibers pass through with their V-marginal masses and no
\(W\) dependence. This is the ordinary conditional law of the explicit
finite product source; it is not a claim that live fixed-address Philox words
are uniform, independent, fresh, one-shot, or equal in law to the abstract
source.

The certificate field is deliberately named
`abstract_product_uniform_corollary_recorded_under_explicit_premises`. It
records the reviewed conditional corollary; it does not certify those premises
for the live generator. CP43 materializes no fiber cardinality, source mass,
failure probability, successful-batch law, initializer law, or live-source
comparison.

## 7. Reviewed F37 arithmetic argument

For every CP30/CP36 attempt, the exact gap is formed from three finite binary64
operands: the guide value, the residual value, and the global upper bound,

\[
\delta=(g+r)-U\le 0.
\]

Each finite binary64 value is an exact dyadic whose reduced denominator
divides \(2^{1074}\), and its magnitude is strictly less than \(2^{1024}\).
Putting all three operands over the common denominator \(2^{1074}\) gives
each scaled numerator magnitude below \(2^{2098}\). Therefore the reduced
gap can be written as

\[
\delta=\frac{n}{2^k},\qquad
0\le k\le1074,\qquad
|n|<3\cdot2^{2098}<2^{2100}.
\]

CP30 validates the two represented score operands and constructs their sum as
an exact rational. CP36 binds the represented finite upper bound and validates
the exact witness \(\delta=q-U\le0\). Thus wrong-type, nonfinite, nondyadic,
and positive-gap routes are outside the valid parent domain.

CP37 converts a nonzero dyadic \(n/2^k\) to an exact terminating decimal with
coefficient \(c=n5^k\) and exponent \(-k\). The conservative bound is

\[
\log_{10}|c|
<2100\log_{10}2+1074\log_{10}5
\approx1382.8568.
\]

Hence the coefficient has at most 1,383 decimal digits, below CP37's frozen
16,384-digit coefficient limit. The numerator and denominator bounds are also
well below CP37's 131,072-bit exact-integer limit. In the adaptive interval,
the represented value and Decimal exponent remain far inside the frozen
Decimal exponent range.

For \(D=2^{64}\), CP37's exact branch partition is

\[
K(\delta)=
\begin{cases}
D,&\delta=0,\\
0,&\delta\le-64,\\
D-1,&-D^{-1}<\delta<0,\\
\left\lfloor D e^\delta\right\rfloor,
&-64<\delta\le-D^{-1}\quad\text{(adaptive enclosure)}.
\end{cases}
\]

The zero branch is conservative because \(De^{-64}<1\). The below-one-cell
branch follows from \(e^\delta>1+\delta>1-D^{-1}\) and
\(e^\delta<1\). Equality at \(\delta=-D^{-1}\) deliberately enters the
adaptive branch, while \(\delta=-64\) enters the zero branch.

The adaptive routine uses correctly rounded Decimal exponentials, adjacent
rational enclosures, increasing precisions, nesting checks, and an exact
integer-floor separation test. All reviewed valid-parent type, dyadicity,
sign, coefficient-size, exact-resource, Decimal-range, enclosure-nesting, and
uint64-domain escape routes are excluded under the declared trusted runtime.
The remaining unresolved route is that, for some valid dyadic gap, the scaled
enclosure might still straddle an integer after the final 3,072-digit
precision. CP37 then raises the exact quota-certification error that CP42 and
CP43 represent as \(F_{37}\).

This is a reviewed mathematical argument, not a machine proof of uniform
floor separation. The current artifacts provide neither a natural valid-
parent example reaching that final ambiguity nor an impossibility proof.
Accordingly `natural_f37_reachability_resolved`,
`natural_f37_failure_exhibited`, and
`natural_f37_impossibility_proved` all remain false.

## 8. Exact text and digest binding

The reviewed F37 argument is stored as one frozen exact-text constant. Its
dedicated digest is domain-separated as

\[
\operatorname{SHA256}_{\mathrm{semantic}}
\bigl(\texttt{cp43-f37-arithmetic-argument-v1},\text{argument}\bigr).
\]

Certificate construction stores both the exact text and this digest.
Validation requires exact equality with the module constant, recomputes the
domain-separated argument digest, and includes both fields in the enclosing
certificate payload digest. The separate claim-evidence ledger is treated the
same way under domain `cp43-claim-evidence-ledger-v1`. The product-uniform
corollary and F37 conclusion are exact-text fields included in the certificate
payload, and the runtime fingerprint additionally includes the theorem,
ledger, corollary, F37 argument, and F37 conclusion.

Consequently an attacker who edits and redigests only a record cannot promote
a different F37 argument, ledger, corollary, or conclusion under the trusted
module constants. This is tamper detection within the running procedural
contract. It is not an authenticated signature, proof-carrying code, or an
attestation of the external test and review artifacts. The ledger explicitly
labels final test results and independent audits as external, not self-
attested evidence.

## 9. Runtime fingerprint and integrity limit

The local runtime fingerprint commits to the schema, policy, scope, supplied-
word domain, theorem, evidence ledger, product-uniform corollary, F37 argument,
F37 conclusion, Python implementation/version, platform system/machine, and
code-object digests for the captured CP42 evaluator and applied builder plus
the critical CP43 resolver, record builders, internal G operation,
predecision validator, private semantic kernel, public replay facade,
combined entry point, owner-snapshot constructor, and snapshot guard. Live
dependency-surface checks also require the captured CP42 validators/builders,
exact error classes, owner methods, and selected utility functions to retain
identity.

This fingerprint is intentionally narrower than portable loaded-code
attestation. It does not authenticate the environment, native libraries,
interpreter, transitive code closure, filesystem, or external evidence; nor
does it protect against arbitrary process compromise, concurrent monkeypatch,
or an ABA mutation that is completed between observations. The certificate
therefore fixes

- `runtime_portable=False`;
- `cryptographic_authentication=False`; and
- `loaded_code_integrity_certified=False`.

The scope text likewise calls custody trusted-runtime, procedural, nonportable,
and noncryptographic. SHA-256 fields here are deterministic content bindings,
not security claims.

## 10. Successful one-live-outcome witness

For one supplied successful selected-or-exhausted instance, CP43 can bind an
applied CP43 result to one exact validated live CP37 result. It first validates
and replays the CP43 applied decision, validates the supplied CP37 result for
the same \((r,j)\), and obtains CP42's successful predecision/threshold parity
witness. It then extracts the reserved CP37 decision words and records exact
equality of:

- the threshold projection inherited from CP42;
- the complete decision-word tuple and its digest;
- selected versus exhausted outcome;
- comparison count;
- selected attempt index; and
- selected-configuration digest.

The witness retains the exact CP42 parity witness and exact CP37 result with
their digests. Validation rechecks both against the same live owner ancestry.
This is a per-instance successful full-outcome projection witness. It does not
quantify over all \(V,W\), does not cover \(F_{36}\) or \(F_{37}\), does not
prove universal CP36/CP37 whole-record equivalence, and does not establish a
source distribution. Its fields fix `universal_equivalence_claimed=False` and
`live_failure_equivalence_claimed=False`.

## 11. Claim matrix

Positive scope is limited to:

- exact CP42 owner, CP41 hypothesis digest, and transitive CP36/CP37 binding;
- exact supplied-word domain and ordered \(V/W\) partition;
- exact typed totalization of the declared CP28/CP30 errors as \(F_{36}\);
- exact preservation of CP42's modeled quota failure as \(F_{37}\);
- a CP43-defined reference factorization discharged by construction;
- a private semantic failure kernel that does not access \(W\);
- full ready-W preflight before the first quota comparison;
- one-G combined-entrypoint chronology;
- public replay facade disclosure and replay validation;
- a reviewed product-uniform corollary under explicit abstract premises;
- the reviewed F37 dyadic/resource argument and checked terminal boundaries;
- exact-text and digest binding of the claim evidence; and
- a supplied successful per-instance full-outcome projection witness.

False, unresolved, conditional, or absent scope includes:

- generic exception totalization or relabelling unexpected exceptions;
- replay-free public replay facade or transient-failure public pass-through;
- natural \(F_{37}\) reachability, a valid-parent ambiguity example, or a
  uniform 3,072-digit floor-separation theorem;
- universal live CP36/CP37 failure or whole-record equivalence;
- discharge of CP41's live-parent factorization hypothesis;
- a live Philox law, uniformity, independence, freshness, or randomness;
- numeric fibers, source masses, failure probabilities, or initializer law;
- general initializer admission, path admissibility, or sampler admission;
- scientific, model-quality, or cross-domain generality promotion; and
- portable loaded-code integrity, cryptographic authentication, or external-
  evidence attestation.

## 12. Focused-test coverage

The focused matrix covers public exports and signatures; exact one- and two-
attempt split/join reconstruction; live custody snapshots; combined one-G then
one-private-semantic-kernel chronology; unchanged Python, NumPy, and PyTorch RNG states;
selected/exhausted first-success behavior; full late-word preflight before any
comparison; synthetic \(K=0\) and \(K=D\) semantic endpoints; injected exact
CP28 and CP30 \(F_{36}\) branches; injected exact CP37 \(F_{37}\) pass-through;
transient versus replay-stable public replay facade failure behavior; and wrong CP42
return-sentinel handling.

The refusal matrix covers invalid request identifiers, malformed proposal and
decision tuples, Boolean/NumPy-integer/out-of-range words, unexpected errors,
declared-error subclasses, a generic CP36 preparation error, cross-owner
records, sealed constructors, object-level mutation, redigested owner-binding
mutations, and plain or redigested record forgeries. Exact-text hostility
redigests forged F37 argument, evidence-ledger, and corollary text and requires
validation to refuse them.

The F37 review matrix covers \(\delta=0\), \(\delta=-64\), the strict
below-one-cell branch, the smallest negative dyadic with denominator exponent
1,074, the exact adaptive boundary \(-2^{-64}\), the nearest admissible dyadic
above \(-64\), the conservative \((2^{2100}-1)/2^{1074}\) coefficient bound,
and wrong-type, nondyadic, and positive-gap refusal routes. The live fixture
supplies one interior adaptive quota, but that single outcome is not a
reachability theorem for the unresolved final ambiguity.

Profiler-injected exceptions are exact branch evidence, not evidence that the
unchanged parent naturally produces those exceptions. Synthetic endpoint rows
exercise the semantic kernel, not the full live parent at those endpoints.
AST import screening excludes direct imports of `random`, `numpy.random`,
`torch.random`, and `secrets`; separate lexical source screening excludes the
exact call spellings `.prepare(`, `.decide(`, `.resolve(`, `.coordinate(`,
and `.admit(`. These static screens are not a call-graph proof. Separately,
successful-path runtime-profiler evidence records zero calls to those five
parent operational methods.

## 13. Frozen execution and audit evidence

The following values come from the frozen commands and external audit records;
the CP43 certificate does not self-attest them.

Frozen CP43 identity and focused evidence:

- source SHA-256:
  `12977ea4c38c8f5cb595d823e129f0f9dd8e0cadb1a151247d3278464c64fd64`;
- focused-test SHA-256:
  `5f8372c4e80e5539e08444170f687af36b755998e6e96ffbdbe57331178f9944`;
- collected test cases: `62`;
- focused result: **62/62 passed**;
- pytest time: **12949.69** seconds; and
- external wall time: **12950.26** seconds.

Frozen direct-parent and inherited regression evidence:

- CP42 source SHA-256:
  `a6dbe506c289992ec797a32b6e034a41681af5f18f5721f7c2e1a87af66d2a71`;
- CP42 primary-test SHA-256:
  `8814ba75e4b7eff2bd90309d1cd139a6c313dfaf16009e4e4e0497598610b153`;
- CP42 primary regression result:
  **29/29 passed**;
- CP42 primary regression pytest time: **3409.31** seconds;
- CP42 primary regression external wall time: **3409.78** seconds;
- CP42 additive-supplement-test SHA-256:
  `d3b8d1213ea4c94cd776f0628d2bae56fed4e041a975571d936bc43ab749e9fe`;
- CP42 additive-supplement regression result:
  **5/5 passed**;
- CP42 additive-supplement regression pytest time: **1205.53** seconds;
- CP42 additive-supplement regression external wall time: **1205.98** seconds; and
- pre/post regression hash status:
  `PASS (pre/post exact CP42 source and test hashes unchanged)`.

Frozen static and independent-control evidence:

- static gates: **PASS (Black, pyflakes, Python 3.9 byte-compilation, ASCII,
  and 62-test collection); line-length audit has five reviewed exceptions**;
- static details: `Black left both files unchanged; exactly five lines exceeded
  88 columns (source 56, 1683, 1705, and 1712; test 780), all identifier or
  qualified-name lines`;
- independent audit: **PASS WITH ONE EXPLICIT P2 SCOPE LIMIT**; and
- independent-audit details: `P0=0, P1=0; P2=1: only one live CP37 outcome has
  a full parity witness, while the opposite outcome is covered only by
  synthetic semantic-H tests; no universal live-equivalence claim is made`.

These frozen external values remain distinct from the in-process CP43
certificate and retain the scope limits stated throughout this audit.

## 14. Disposition and remaining dependencies

The final CP43 disposition is **PASS WITH EXPLICIT SCOPE LIMITS**. The
regression, static, and independent-audit evidence above is frozen. These
software-engineering results do not alter the remaining dependencies below.

CP43 leaves separate:

1. a uniform proof that every valid adaptive dyadic gap separates by 3,072
   Decimal digits, or a natural valid-parent counterexample;
2. universal live CP36/CP37 equivalence on both successful and failure paths;
3. numeric fiber counts, failure masses, and a proved comparison from live
   Philox words to the abstract product-uniform source;
4. global analytic tilted-law normalization, exact ideal rejection, and
   remaining initializer-strategy admission;
5. semantic tag-3 payload generation and global address guarantees;
6. Brownian consumption/coupling, drift, split-step path construction, and
   liveness; and
7. the complete learned/general sampler and remaining manuscript-level formal
   and empirical tests.

Until those dependencies close, CP43 may be cited only as **a fixed-owner,
typed-totalized, supplied-word reference factorization with exact private
semantic failure pass-through, fully preflighted decision semantics, an
explicit public replay facade, a conditional abstract product-uniform
corollary, a reviewed but not machine-proved F37 arithmetic boundary, and a
per-instance successful full-outcome witness, without a live source law or
universal live-failure equivalence**.
