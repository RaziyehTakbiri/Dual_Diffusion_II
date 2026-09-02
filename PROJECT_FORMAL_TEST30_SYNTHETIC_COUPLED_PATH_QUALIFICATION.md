# Formal Test 30 synthetic explicit-input coupling precursor

**Package state:** `SYNTHETIC_EXPLICIT_INPUT_TEST30_COUPLING_PRECURSOR_VALIDATED`  
**Formal Test 30:** `PENDING`  
**Global project state:** `DRAFT_NOT_EXECUTABLE`  
**Scientific effect:** zero  
**Tracker effect:** none; independent audit is required before even the new
project-control predicate is eligible for registration

## 1. Authority and stopped scope

The normalized visible authority for this bounded local package is exactly:

> Okay, sounds good. What I want you to do is to set aside a significant portion of work to do such that you are busy for around 8 hours, because I am going to sleep, and dont want my absence to make you idle.

Its normalized UTF-8 encoding is 207 bytes with SHA-256
`44ed1336dd467043e3daebe7ad85093c5ab954921a895483153c98cb6d32bb9a`.
Raw transport bytes, the conversation envelope, account identity, and a
cryptographic signature are not bound. The sentence authorizes continued
bounded local work. It does not authorize network access, external contact,
data acquisition, live entropy, a scientific execution, runtime approval,
training, claim promotion, submission, or tracker edits.

This package adds one pure implementation and four evidence artifacts:

1. `src/heterodiff/evaluation/formal_test30_synthetic_coupled_path_qualification.py`;
2. `PROJECT_FORMAL_TEST30_SYNTHETIC_COUPLED_PATH_QUALIFICATION.md`;
3. `research/fixtures/manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.json`;
4. `research/diagnostics/manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.py`;
5. `tests/unit/test_manuscript_v3_formal_test30_synthetic_coupled_path_qualification_v1.py`.

The implementation has no RNG call, filesystem write, data access, network
call, or tracker operation. It consumes caller-supplied finite values as
data. The validator is read-only. No source or manuscript outside this
five-file package, and no ledger, timetable, or tracker, is modified.

Before executing any qualification source, the validator hard-pins the exact
SHA-256 of that source and all four semantic inputs: the executable method
specification, CP23 lineage/address source, static Test-30 gap inventory, and
its machine record. It compiles and executes exactly the already stable-read
source bytes in memory. It does not reopen the source path or consult a cached
bytecode loader. The machine receipt binds this execution-custody boundary.

This package is internal evidence. The visible authority text, internal file
paths, hashes, custody receipts, and machine record must not appear in an
anonymous submission or public artifact. Any publication use requires a
separately reviewed publication-safe derivative containing only sanitized
method content and unresolved status. No account identity, absolute local
path, credential, secret, raw data, or test-data content is included here.

## 2. Exact target and inherited CP23 boundary

Formal Test 30 in `manuscript_v3/executable_method_spec.md` requires:

> Coupled step halving converges on the mixed oracle for continuous paths,
> edit counts, and endpoint conditional law.

Section 8.2 additionally requires a frozen schedule and tolerances, tag-4 and
tag-5 Brownian domains, persistent occurrence lineage, and coarse increments
equal to sums of corresponding fine increments for every surviving lineage.
The static selection freeze records the minimum full closure as
`COUPLED_PATH_COARSE_EQUALS_SUM_FINE_PERSISTENT_LINEAGE_FROZEN_LEVELS_AND_TOLERANCES_WITH_RECOMPUTATION`.

Checkpoint 23 supplies the address layout

\[
K(r,d)=(r,d),\qquad C(s,\ell,p)=(0,s,\ell,p),
\]

with tag 4 for a left Brownian half-step, tag 5 for a right Brownian
half-step, positive occurrence serial \(\ell\), and proposal limb zero. Its
receipts are initially unused namespace objects. CP23 explicitly does not
certify Brownian consumption, a Gaussian law, independence, coarse/fine
coupling, or a path.

CP23 lineage bootstraps occurrence serials from canonical tuple positions,
retains survivor identifiers, retires the exact selected source on death or
replacement, gives each birth or replacement the next fresh monotone serial,
and carries a persistent retired-identifier ledger. The synthetic fixture
mirrors the parts needed here: serials 1 and 2 bootstrap; serial 3 is born;
serial 1 is retired and serial 4 is created by replacement; serial 2 is
retired by death; serials 3 and 4 survive to the endpoint. All levels replay
the same accepted edit transcript and exact edit-family counts.

## 3. The CP23 level-coordinate obstruction

The CP23 key/counter layout has no discretization-level limb. If a coupled
study independently issued a tag-4 or tag-5 stream at both a fine and a
coarse level under the same run, then a shared `(step_index,
occurrence_serial,tag)` would have the same CP23 address at both levels. That
would be address reuse, not a valid independent coarse draw, and a direct
Philox reconstruction at the coarse address would not equal the sum of the
two fine increments.

The version-one construction therefore permits direct CP23-shaped addresses
only on the finest frozen level. Coarser increments are mathematical derived
objects, never CP23 stream receipts. The input roster contains both tags for
every lineage live over each finest full step and rejects missing, extra,
duplicate, pre-birth, post-death, wrong-run, wrong-tag, wrong-key, or
wrong-counter entries.

This is a material route restriction: a later live implementation must either
derive coarse paths from one finest addressed tree, as done here, or introduce
an independently reviewed level-aware namespace. It must not draw each level
from the unchanged CP23 address schema.

## 4. Exact coupling construction

The input value is a physical half-step increment \(\Delta W\), not a
standardized normal \(z\). For adjacent levels, coarse step \(j\), and a
lineage surviving the relevant interval, the construction is

\[
\begin{aligned}
\Delta W^{L-1}_{j,4,\ell}
  &=\Delta W^{L}_{2j,4,\ell}+\Delta W^{L}_{2j,5,\ell},\\
\Delta W^{L-1}_{j,5,\ell}
  &=\Delta W^{L}_{2j+1,4,\ell}+\Delta W^{L}_{2j+1,5,\ell}.
\end{aligned}
\]

Every binary64 leaf is converted with `Fraction.from_float`, which is the
exact dyadic real represented by that leaf. All derived sums are exact
rational sums. A derived value is rounded to binary64 once, only when the
synthetic Heun map consumes it. Thus the equality is an exact dyadic-real
identity for the supplied leaves, not a floating tolerance and not a claim
about generic real-number input.

The frozen levels are dyadic exponents `(2,3,4,5)` over horizon 1. Edits occur
at coarsest-grid boundaries 1, 2, and 3, so no aggregation interval crosses a
lineage change. Only the finest level carries direct CP23-shaped addresses;
all 140 coarser half-increments are derived from the 160 supplied finest
entries. There are 80 tag-4 and 80 tag-5 supplied entries.

## 5. Synthetic mixed OU/edit oracle

Each live coordinate follows the additive-noise OU equation

\[
dX_t=-\kappa(X_t-\mu_q)dt+\sigma dW_t
\]

between boundary edits. Version one freezes \(\kappa=0.7\), \(\sigma=0.8\),
\(\mu_A=0.35\), and \(\mu_B=-0.25\). The initial state is
`(serial 1, A, 0.75)` and `(serial 2, B, -0.4)`. The accepted edits are:

1. at time \(1/4\), birth `(serial 3, A, 0.2)`;
2. at time \(1/2\), replace serial 1 by `(serial 4, B, -0.1)`;
3. at time \(3/4\), kill serial 2.

For half-step width \(\delta\), stochastic Heun with supplied physical
increment \(\Delta W\) is the affine map

\[
X'=\mu+A(X-\mu)+G\Delta W,
\quad
A=1-\kappa\delta+\tfrac12(\kappa\delta)^2,
\quad
G=\sigma(1-\tfrac12\kappa\delta).
\]

The deterministic path diagnostic compares adjacent coupled levels in the
maximum absolute coordinate norm at frozen shared pre-edit and post-edit
coarsest checkpoints. It is not a continuum supremum norm and is not an exact
SDE path oracle. The frozen path tolerance is 0.025, applied to the finest
adjacent-level gap, with strict contraction required across the three gaps.

Separately, under the hypothetical premise that each half increment is an
independent centered Gaussian with variance \(\delta\), the Heun moment
recurrence is

\[
m'=\mu+A(m-\mu),\qquad v'=A^2v+G^2\delta.
\]

The analytic OU endpoint law after a deterministic reset is

\[
m_*=\mu+(x_0-\mu)e^{-\kappa\tau},\qquad
v_*=\frac{\sigma^2}{2\kappa}(1-e^{-2\kappa\tau}).
\]

The endpoint metric is the maximum component one-dimensional Gaussian
Wasserstein distance

\[
W_2=\sqrt{(m-m_*)^2+(\sqrt v-\sqrt{v_*})^2}
\]

over the final live serials. This is a synthetic ideal-IID-Gaussian moment
oracle. It is independent of the realized deterministic payload and does not
assert that those supplied values, CP23 streams, or any live source satisfy
the Gaussian premise. The frozen finest-level tolerance is 0.006 with strict
contraction across all four endpoint errors.

The failure rule is
`FAIL_CLOSED_NO_RETRY_NO_FALLBACK_NO_TOLERANCE_SUBSTITUTION`.

## 6. Frozen local receipt

The exact version-one local receipt is:

| Item | Value |
|---|---:|
| Levels | `(2,3,4,5)` |
| Supplied finest entries | 160 |
| Tag-4 / tag-5 entries | 80 / 80 |
| Derived coarse entries | 140 |
| Adjacent path gaps | `(0.012165171492164367, 0.0031967310499734225, 0.0014979918645190993)` |
| Endpoint moment-oracle W2 errors | `(0.0007573522254040962, 0.00018472254789865305, 0.000045611333826692866, 0.000011332163239868087)` |
| Design SHA-256 | `72be25d5cf27b94330f9c42ea21013aef06b1ae8a70aa01b12fa23212506ed83` |
| Supplied-input SHA-256 | `fe19802595eac780b95954124b276bf121f2a014bd651de10d7adc280da44315` |
| Qualification report SHA-256 | `9f01d9e2de05836a463d64403d96ce441b45dc01a56160408db13e2b7e76b498` |

All three path gaps are positive and strictly contract. All four endpoint
moment-oracle errors are positive and strictly contract. Birth, death, and
replacement counts each equal one at every level. The final live lineage and
retired ledger agree at every level. Both frozen finest-level tolerances pass.

These decimal values are binary64 diagnostic outputs, not scientific results
and not proof of a stochastic convergence rate. The exact aggregation
statement rests on dyadic rational arithmetic, while the OU diagnostic is a
finite deterministic qualification of the implementation.

## 7. Proof/code/evidence crosswalk

| Obligation | Implementation | Evidence | Status |
|---|---|---|---|
| Exact CP23 tag-4/tag-5 input shape | `CP23BrownianAddress` and exact roster validation | wrong tag/key/counter/run/serial/proposal hostiles | closed in supplied-input scope |
| Physical \(\Delta W\) semantics | `INPUT_SEMANTICS` | exact-token and record tests | closed in v1 scope |
| Coarse equals sum fine | exact `Fraction` derivation in `_derive_all_levels` | all 140 identities recomputed | closed in v1 scope |
| No cross-level address reuse | finest-only addressed input boundary | no coarse receipt API; structure/AST checks | closed in v1 scope |
| Persistent edit lineage | `_replay_lineage`, `_live_roster_by_step`, `_apply_edit` | fresh/reuse/resurrection and roster hostiles | closed for the frozen transcript |
| Continuous-coordinate checkpoint convergence | Heun simulation and `_checkpoint_gap` | three positive contracting gaps and frozen tolerance | qualified only for the supplied synthetic fixture |
| Edit-family convergence | per-level exact count vectors | birth/death/replacement each one at all levels | qualified only for the frozen transcript |
| Endpoint conditional law | analytic OU and Heun moment recurrences | four contracting ideal-premise W2 errors | qualified only under the stated hypothetical moment premise |
| Frozen levels/tolerances/failure rule | exact v1 design equality and design digest | changed-design/tolerance hostiles | closed in v1 scope |
| Stochastic-law and whole-method integration | absent by construction | strict negative flags | open |
| Independent recomputation | not performed by package author | independent audit requested | open |

## 8. Hostile and safety surface

The focused hostile suites reject or detect:

- noncanonical integer components, boolean/int aliases, wrong domains, tags,
  keys, counters, proposal limbs, run IDs, and zero serials;
- noncanonical string subclasses or equality-spoof objects in occurrence kinds,
  edit kinds, and address domains;
- NaN, infinity, boolean, missing, extra, duplicate, or reordered supplied
  increments;
- pre-birth and post-death address use;
- changed levels, horizon, OU parameters, means, edits, tolerances, or failure
  policy under the named v1 schema;
- gapped or reused fresh serials, replacement retaining a source serial, and
  resurrection of retired lineage;
- tampered design, input, path, endpoint, count, negative-claim, custody, or
  self-digest fields in temporary package replicas;
- noncanonical JSON, symlinks, hard links, unsafe paths, executable modes,
  changed source, and execution from an unrelated current directory;
- harmless comment drift coherently rebound into a re-digested machine record
  for the source or any of the four semantic inputs;
- an effectful coherently rebound source before execution, plus an alternate
  source path with compiled bytecode, with proof that neither is executed;
- imports or calls that would introduce random, network, subprocess, tracker,
  or project-mutation behavior into the pure implementation.

All hostile mutations occur in temporary copies. The canonical package is
read only during validation.

## 9. Exact effect and remaining gaps

After a fresh independent audit, this package is eligible to set only the new
project-control predicate
`SYNTHETIC_EXPLICIT_INPUT_TEST30_COUPLING_PRECURSOR_VALIDATED=true`.
It closes no preregistration field, blocker, formal test, scientific result,
or manuscript claim. It does not by itself change any existing tracker row.

Formal Test 30 remains `PENDING`. In particular, the static inventory's four
missing obligations are not declared closed. Exact remaining work includes:

1. actual one-shot CP23 tag-4 and tag-5 stream consumption and a reviewed
   conversion from finite words to physical Gaussian increments;
2. a law for centered Gaussian marginals, independence across required
   addresses, and the cross-level coupling tree—none follows from supplied
   values or from CP23 namespace receipts;
3. a collision-free live level strategy, either finest-tree derivation or a
   new level-aware address contract;
4. stochastic coupling of the frozen jump proposals and destinations across
   levels, including new-occurrence source laws;
5. the actual left-Heun / exact frozen-jump / right-Heun whole split step with
   CP24/CP29 lineage and destination integration rather than boundary-aligned
   synthetic edits;
6. general learned/native drift, multiplicity, continuous marks, and
   configuration-valued paths;
7. a production endpoint conditional-law diagnostic, continuous-path norm,
   edit-count criterion, and preregistered thresholds;
8. immutable runner/runtime custody, failure recording, independently
   recomputed results, and authorized scientific execution.

Therefore this package is a substantive executable precursor and a no-go
restriction on unsafe cross-level CP23 reuse. It is not a completed Formal
Test 30 result.
