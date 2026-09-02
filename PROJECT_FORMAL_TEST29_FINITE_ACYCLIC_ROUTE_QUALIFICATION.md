# Formal Test 29 finite-acyclic route qualification

**State:** `FINITE_ACYCLIC_TEST29_ROUTE_CELL_LINEAGE_COMPLETION_QUALIFIED`

**Named predicate closed by this package:**
`FINITE_ACYCLIC_TEST29_ROUTE_CELL_LINEAGE_COMPLETION_QUALIFIED`

**Formal Test 29:** **OPEN**

**Project fields, blockers, result slots, and scientific claims changed:** none.

## 1. Visible authority and boundary

The exact visible user authority for this additive local work is:

> Okay, sounds good. What I want you to do is to set aside a significant portion of work to do such that you are busy for around 8 hours, because I am going to sleep, and dont want my absence to make you idle.

This authority permits continued safe local project work. It does not authorize
data access, external contact, entropy acquisition, a live runtime campaign,
scientific execution, training, result filling, submission, or tracker
promotion. This package performed none of those operations. It is a pure
implementation-and-qualification successor and is not a retry of any earlier
rehearsal.

## 2. Exact parent requirement and inherited boundary

Formal Test 29 requires certified thinning to reproduce:

1. the exact tilted total rate;
2. exact edit-family probabilities; and
3. continuous destination distributions on quadrature fixtures.

The current checkpoint chain intentionally stops before that complete result:

| Parent | Exact role inherited | Boundary retained here |
|---|---|---|
| CP19 | one local wait, normalized-reference route, represented-rate-ratio Bernoulli | finite-resolution route; successful-return only |
| CP20 | bounded repeated local proposals with rejection reuse and accepted-state refresh | active cap is refusal; no unconditional completion |
| CP21 | same-runtime continuous-route replay with pre/post Philox custody | no exact categorical/integer/Gaussian law and no bounded normal-word trace |
| CP22 | ordered full-loop replay overlay | no ideal route law or unconditional completion |
| CP23 | direct counter-key namespace and persistent-lineage sidecar | parent does not consume issued jump addresses |
| CP24 | direct tag-6 operational-epoch execution | bounded successful return, finite-resolution route, no general liveness |

The additive implementation does not import, modify, wrap, monkeypatch, or
execute those parents. Their exact source bytes are bound below.

| File | SHA-256 |
|---|---|
| `src/heterodiff/processes/plugin_bridge_operational_thinning.py` | `3773a113247da86015a4d8bbcb33f10d004ad66093f05d168decf46b35aea0fd` |
| `src/heterodiff/processes/plugin_bridge_operational_thinning_loop.py` | `312c5da26b695718ece0e0305a36fd050d206ae5b74bd5e934808d93e2353bf3` |
| `src/heterodiff/processes/plugin_bridge_continuous_route_evidence.py` | `a597f076f5cca1834515121e831f732a4ed1fbd2c23c5802672c2edd639e1a38` |
| `src/heterodiff/processes/plugin_bridge_operational_thinning_loop_route_evidence.py` | `90b2829b7df486ba780276fa684669ddab2f68c949e4d70f7046fec2234f969d` |
| `src/heterodiff/processes/plugin_bridge_counter_keyed_lineage_contract.py` | `e728ef0149a3c3275a3b7c1efba8f038279db86cc05e06c56a09545374197557` |
| `src/heterodiff/processes/plugin_bridge_counter_keyed_operational_epoch_loop.py` | `21fdf6931d50dd35022cf6d39e8d529a3da0e20e4875c55cca2188e0fa572320` |

## 3. Additive construction

The new pure implementation is
`src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py`.
It defines a finite, declared, strictly rank-decreasing frozen-jump fixture.
Every active state has exact positive rational base rates and tilt factors.
For route `j`,

\[
  \lambda_j^{\mathrm{tilt}}=
  \lambda_j^{0} w_j,
  \qquad
  p_j=\frac{\lambda_j^{\mathrm{tilt}}}
  {\sum_k \lambda_k^{\mathrm{tilt}}}.
\]

The constructor admits the fixture only when every route mass and conditional
source-index mass has an exact dyadic representation under the declared bit
layout. There is therefore no floating normalization, clipping, rejection, or
unclassified remainder in the route and integer-source laws.

Every admitted exact `Fraction` numerator and denominator is capped at 4,096
bits. The same cap is rechecked after each rate product, accumulated total,
normalization, route/source or route/cell product, and Gaussian-moment
operation before that value can be reused. Boundary values are admitted and
over-cap inputs or derived values fail closed. The qualification is therefore
over this explicitly resource-bounded fixture class, not arbitrary-size Python
rationals.

Each birth or replacement route carries an exact diagonal-Gaussian descriptor:
rational mean and rational positive variance. Its marginal raw moments through
order four are computed exactly. This is the ideal continuous conditional-law
descriptor and is kept separate from operational finite-word output.

One supplied uint64 word is partitioned into fixed low-bit fields for:

- route category;
- conditional source index; and
- one equiprobable standard-normal quantile-cell index per declared coordinate.

Every low residue has exactly `2^(64-used_bits)` uint64 preimages. Thus the
operational route, source, and normal-cell pushforward is exact under an
abstract uniform uint64 premise. It is not estimated from samples.

The complete supplied-word roster is first bound to and preflighted against
the CP24-compatible direct addresses

\[
  \mathrm{key}=(\mathrm{run\_id},6),\qquad
  \mathrm{counter}=(0,\mathrm{step\_index},0,
  \mathrm{completed\_proposals}).
\]

The public compatible-address constructor enforces the frozen CP24 operational
range `0 <= completed_proposals < 64`; proposal 63 is admitted and proposal 64
is rejected.

Missing, duplicated, reordered, alien-run, alien-step, or wrong-proposal
address records fail before route interpretation. The pure run then consumes
one distinct addressed word per jump. Birth allocates the next
fresh serial, death retires the selected serial, and replacement retires the
selected serial and allocates a fresh one. Active and retired serials remain
disjoint and the next serial is strictly monotone.

Every route strictly decreases a nonnegative integer rank. Therefore, for
every valid supplied-word tape of length equal to the initial rank, execution
reaches a declared terminal state in at most that many jumps. This is an
unconditional bounded-completion theorem for the admitted finite acyclic
fixture class; it is not a general cyclic thinning-liveness theorem.

## 4. Why the continuous Gaussian claim remains open

A deterministic map of `B` uint64 words has support size at most
`2^(64B)`. A nondegenerate Gaussian distribution is non-atomic and has
uncountable support. Consequently, no bounded finite-word deterministic map
can itself have an exact continuous Gaussian law.

The implementation therefore exposes both of the following without merging
them:

1. the exact ideal Gaussian disintegration and its exact moments; and
2. the exact bounded-word pushforward over Gaussian quantile cells.

The cell index has the exact Gaussian cell mass under the ideal descriptor,
and its finite-word law is exact. The cell midpoint is only a finite binary64
representative and is never called a Gaussian sample. The machine
qualification truth table consequently fixes
`exact_continuous_gaussian_from_bounded_words=false` and
`formal_test29_closed=false`.

## 5. Fixed hostile qualification fixture

The primary hostile fixture begins with rank two and two active lineages. Its
three initial tilted rates are exactly `2`, `1`, and `1`, giving birth,
replacement, and death probabilities `1/2`, `1/4`, and `1/4`. Replacement and
death each choose between two source indices with exact probability `1/2`.
The birth successor chooses among three source indices with exact probabilities
`1/2`, `1/4`, and `1/4`. Birth and replacement routes include one- or
two-dimensional diagonal Gaussian descriptors; death has no destination
coordinate law.

The small exhaustive layout uses two route bits, two source bits, one normal
cell bit for each of at most two coordinates: six used bits in one uint64 word.
All `64^2 = 4,096` two-word tapes were checked. Every tape terminated in one or
two jumps, every consumed address was unique, every transition decreased rank,
and the three declared terminal branches were all reached. This exhaustive
check is a deterministic finite proof aid, not a stochastic experiment.

## 6. Verification result

The cache-disabled focused suite passed **59/59** tests. It includes:

- exact tilted-rate, route, edit-family, and conditional integer-source
  identities;
- independent exhaustive low-word enumeration against the closed-form
  pushforward;
- independent numerical integration of Gaussian raw moments and every
  standard-normal quantile cell through six cell-bit levels;
- upper-word invariance and exact uint64 preimage reasoning;
- all 4,096 supplied-word completion paths;
- CP24-compatible address injectivity and the exact 63-accepted/64-rejected
  proposal boundary, complete-roster preflight, actual trace consumption, and
  missing/duplicate/reordered/alien-address refusals;
- birth, death, and replacement lineage algebra with non-resurrection;
- exact result recomputation and forged-record refusal;
- hostile type, range, dyadic-resolution, graph-cycle, cardinality, Gaussian-
  dimension, terminal, and resource-guard cases;
- exact-rational 4,096-bit input and derived-value boundary/overflow cases;
- canonical self-digest, semantic-mutation, predecessor-drift, mode, hardlink,
  and symlink attacks against the machine receipt and read-only validator;
- execution from the already stable-read, hard-hash-admitted source byte
  buffer, with hostile alternate source-path and bytecode bytes proved
  unexecuted;
- static exclusion of entropy, data, network, model, filesystem, clock, and
  parent execution imports; and
- exact SHA-256 checks over every CP19--CP24 source.

Static `pyflakes` validation reports zero findings. All five package files are
required to be regular `0644`, single-link files. The same cache-disabled suite
also passed **59/59**
from `/private/tmp`, an unrelated working directory. Final independent audit
remains required.

A separate cache-disabled, bytecode-disabled, warnings-as-errors combined
CP22--CP24 diagnostic collected 129 parent tests and returned **126 passed / 3
failed** in 1,872.99 seconds. The only failures were the three homologous
optional-PyTorch child-process boundary nodes: their child interpreter did not
inherit the project `src` import path and failed first with `No module named
'heterodiff'`. No parent semantic or custody test failed. An exact isolated
rerun of those three nodes with the project `src` path explicitly inherited
passed **3/3** under the same cache, bytecode, and warning settings. The machine
receipt retains both observations and explicitly does **not** claim that the
original combined invocation passed 129/129.

The exact original invocation, from the project root with `PYTHONPATH` unset,
was:

```text
PYTHONDONTWRITEBYTECODE=1 .venv-m1/bin/python -P -B -m pytest -p no:cacheprovider -W error -q tests/unit/test_plugin_bridge_operational_thinning_loop_route_evidence.py tests/unit/test_plugin_bridge_counter_keyed_lineage_contract.py tests/unit/test_plugin_bridge_counter_keyed_operational_epoch_loop.py
```

Its three exact failed node IDs were:

```text
tests/unit/test_plugin_bridge_operational_thinning_loop_route_evidence.py::test_optional_torch_import_boundary_is_explicit
tests/unit/test_plugin_bridge_counter_keyed_lineage_contract.py::test_optional_torch_import_boundary_is_explicit
tests/unit/test_plugin_bridge_counter_keyed_operational_epoch_loop.py::test_optional_torch_import_boundary_is_explicit
```

The exact isolated rerun, again from the project root, was:

```text
PYTHONPATH=/Users/mahtab/.codex/.chatgpt-projects/g-p-6a5f91c1e79c819183983ba0010bb151/src PYTHONDONTWRITEBYTECODE=1 .venv-m1/bin/python -P -B -m pytest -p no:cacheprovider -W error -q tests/unit/test_plugin_bridge_operational_thinning_loop_route_evidence.py::test_optional_torch_import_boundary_is_explicit tests/unit/test_plugin_bridge_counter_keyed_lineage_contract.py::test_optional_torch_import_boundary_is_explicit tests/unit/test_plugin_bridge_counter_keyed_operational_epoch_loop.py::test_optional_torch_import_boundary_is_explicit
```

These are owner-executed pre-freeze diagnostics, not an independent-audit
receipt. The environment seam remains disclosed and does not become a hidden
qualification premise.

| Frozen code artifact | SHA-256 | Bytes |
|---|---:|---:|
| `src/heterodiff/processes/formal_test29_finite_acyclic_route_oracle.py` | `308a16090128871c9a79cdaff265d3b6633e18b062a605b257f3173198d8a089` | `52186` |
| `research/diagnostics/manuscript_v3_formal_test29_finite_acyclic_route_qualification_v1.py` | `b962f9b9fcc957e1a25590d341f4fc0b9889fd041757d9c623b36d4fca300905` | `32631` |
| `tests/unit/test_formal_test29_finite_acyclic_route_oracle.py` | `6f9fc2576958992c5688123228128f2f56cecc47b4e8bc2de3b238e510d1662d` | `42876` |

The canonical machine record is
`research/fixtures/manuscript_v3_formal_test29_finite_acyclic_route_qualification_v1.json`.
It embeds its own canonical record SHA-256 and binds this human record, all
three frozen code artifacts, the six CP19--CP24 sources, and the three direct-
parent regression tests by exact byte hash. The machine record is generated
only after the human record is frozen, avoiding a circular human/machine hash.

## 7. Exact remaining gaps

Formal Test 29 remains **OPEN**. This package does not provide:

1. an exact continuous Gaussian coordinate from a bounded word trace;
2. a proved operational source law for live Philox words or physical entropy;
3. integration with the CP24 production owner or its rate/envelope/route
   objects;
4. an exact waiting-clock or acceptance-thinning law for this additive route
   oracle;
5. proof that the production active total rate equals the fixture total;
6. unconditional completion or liveness for cyclic, recurrent, or general
   capped configuration chains;
7. production-path independent recomputation or a terminal Test-29 receipt;
8. Brownian coupling, a conditional path, a whole-method sampler, or any
   scientific result.

Blocker `B12` and every project field and result slot retain their prior state.
No project tracker is edited by this package. An independent exact-scope audit
is required before the named finite-acyclic predicate may be recorded in a
tracker.

## 8. Anonymity and publication boundary

This five-file package is `internal_evidence_only=true`. Direct inclusion in
an anonymous or public submission is not permitted. Any manuscript-facing use
requires a separately reviewed, sanitized, publication-safe derivative.

That derivative must exclude the exact conversation-visible authority,
conversation or custody provenance, internal project paths, raw or record
hashes, byte counts, local test-command details, machine receipts, and any
information that could reconstruct excluded internal provenance. It may retain
only the sanitized mathematical construction, its accurately narrowed scope,
and the unresolved status of Formal Test 29. Creating such a derivative would
require a fresh anonymity review and is not performed by this package.
