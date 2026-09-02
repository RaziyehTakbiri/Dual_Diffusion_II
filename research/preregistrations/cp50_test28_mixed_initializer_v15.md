# CP50 Test-28 mixed-support initializer protocol v1 — DRAFT sidecar v15

## 1. Status and authority

This document is a **DRAFT**. It does not authorize a confirmatory run. It may
be frozen only after the implementation, independent oracle, fixtures, tests,
runner, dependency lock, and machine-readable manifest all exist and their
SHA-256 digests have been inserted into a separate freeze receipt. The frozen
copy must be byte-identical to the copy stored with every execution attempt.

This file is the additive v15 DRAFT sidecar.  Its scientific protocol
identifier remains `cp50-test28-mixed-initializer-v1`; the sidecar generation
does not create a new scientific protocol, rewrite the immutable v14 protocol
or manifest, freeze either v15 path, or authorize execution.  CP64's
construction-time v15-availability and v15-consumption flags remain false,
and its proposed lifecycle graph remains nonauthoritative for production
until this sidecar and a separately generated v15 machine manifest are both
frozen and consumed by a later bound artifact.

This is a new, forward-only CP50 protocol. It does not replace, reconstruct,
or validate the unavailable CP29 primary bundle. In particular, it must not
reuse the CP29 evidence identifier, timestamps, seed material, terminal digest,
one-shot claim, or any `identity-*` stub file.

## 2. Objective

The objective is to test a three-strategy initializer interface on known laws
over capped-Poisson mixed support while keeping the analytic and operational
state spaces separate.

Let \(\mathcal X_{\mathbb R}\) be the ideal mixed configuration space with
real-valued continuous coordinates.  The symbol \(\Pi_N^{rat}\) denotes the
analytic capped-Poisson reference with the declared exact-rational activity
and type weights; \(\Pi_N^{b64}\) denotes the distinct analytic reference
obtained by interpreting the stored binary64 activity and normalized type
weights exactly, while retaining ideal Gaussian fibers.  For an independently
specified, finite, measurable real-fiber score
\(\bar q_c:\mathcal X_{\mathbb R}\to(-\infty,U]\), define

\[
\bar\rho_c^{rat}(dx)=(\bar Z_c^{rat})^{-1}
e^{\bar q_c(x)}\Pi_N^{rat}(dx),\qquad
\bar Z_c^{rat}=\int e^{\bar q_c(x)}\Pi_N^{rat}(dx),
\]

with the analogous \(\bar\rho_c^{b64}\) and \(\bar Z_c^{b64}\) under
\(\Pi_N^{b64}\).  These two analytic laws are kept separate even when their
parameters are numerically close.

Let \(\mathcal X_{fp}\) be the configurations representable by the frozen
finite-precision reference sampler. Under an explicitly assumed law for that
sampler and its source, denote its proposal measure by \(\mu_{fp}\). The
known-law exact-score provider certifies an exact rational
represented-coordinate score
\(q_c^{repr}:\mathcal X_{fp}\to\mathbb Q\). The operational target is

\[
\rho_c^{repr}(dx)=Z_{repr}^{-1}e^{q_c^{repr}(x)}\mu_{fp}(dx),\qquad
Z_{repr}=\int e^{q_c^{repr}(x)}\mu_{fp}(dx).
\]

The strategies are selected before any random draw and are never changed in
response to observed proposals, scores, acceptance, exhaustion, or ESS:

1. complete finite-atomic enumeration;
2. fixed-attempt bounded rejection; and
3. fixed-particle sampling-importance-resampling (SIR).

The code-level target uses the exact rational score retained by the known-law
provider; its rounded binary64 display value is not substituted for that
score.  The provider binds the exact reference object and separately declares
a named real-polynomial \(\bar q_c\) and its pointwise restriction to
canonical binary64 coordinates.  This chosen algebraic bridge does **not**
prove that \(\Pi_N^{rat}=\Pi_N^{b64}=\mu_{fp}\), derive a normalizer by
itself, or verify the runtime sampler/source law.  A separate, stdlib-only
CP53 oracle now derives exact-rational outward predictions for the named
`T28-M1-Q` and `T28-M2-Q` laws under \(\Pi_N^{rat}\) and
\(\Pi_N^{b64}\).  Those fixture-specific analytic records neither identify
either reference with \(\mu_{fp}\) nor derive \(Z_{repr}\).  The completed
sealed, torch-lazy common score-provider facade admits separate CP30
learned-composer, exact-known-law, and count-keyed atomic score-table
adapters.  The completed kernel-v2
consumes that facade directly, retains the exact upper envelope and any
optional exact lower envelope, and does not convert the known-law provider
into the CP30 composer type.  The two named paths have development-test and
analytic-oracle evidence only.  This is neither a confirmatory execution nor
evidence for an operational proposal law, live target equality, or manuscript
result.  CP56 additionally carries the CP55 `T28-A0-Q` table through the
third adapter and one generic finite-atomic kernel-v2 enumeration, then binds
an exact count-keyed comparison with the stored-binary64 analytic interval
target.  That deterministic categorical-weight comparison executes no draw
and does not identify its base vector with a source law or its output with a
probability measure.

CP57 adds a sealed `T28-AESS` analytic stress oracle and the complete
fourteen-row `T28-INVALID` expectation table.  Module import and oracle/table
construction are stdlib-only; explicit verification of an observed production
exception lazily imports its exact production class.  CP57 also hardens the
kernel-v2 stochastic preflight so resource excess and count/type categorical
resolution or retained-CDF custody failures refuse before runtime hashing or
owned RNG construction.  The static refusal records bind expected behavior;
separate hostile tests exercise the five production-preflight rows.  These
artifacts remain nonconfirmatory and establish no runtime source or
categorical law.

CP58 adds a sealed, stdlib-only bounded-feature and SIR-diagnostic artifact.
It freezes exact finite feature registries for `T28-M1-Q` and `T28-M2-Q`,
including their rational projections, saturating coordinate transforms, and
count, type, coordinate, and pair-interaction features.  It also separates
proposal-configuration value uniqueness from same-cloud local particle-slot
ancestry, records the one-selection ancestry contract of the current kernel,
and derives a zero-draw conditional occupancy calculation for the
predeclared `T28-AESS` cloud.  Its calibration inputs are fixed arithmetic
checks only; they are not sampled output or target comparisons.  CP58 does not
replay a provider, kernel, sampler, or RNG and establishes no source,
categorical, iid, operational, or target law.

CP59 adds a sealed conditional finite-precision arithmetic artifact.  For one
supplied score cloud it independently recomputes the frozen binary64
normalization formula, requires byte-identical supplied weights, constructs
the sequential binary64 CDF with its last entry forced to one, and counts the
exact right-sided cells of the (2^{53})-point categorical grid.  For a
separately supplied finite proposal law it converts certified uint64 quotas
into exact first-acceptance, exhaustion, and selected-atom masses under an
abstract iid-proposal and independent-uniform-decision-word premise.  The
zero-argument records for `T28-M1-Q` and `T28-M2-Q` are predeclared arithmetic
tables, not sampled clouds or authenticated production observations.  CP59
does not execute the reference sampler, initializer owner or plan, kernel
normalization helper, or RNG; it does not identify \(\mu_{fp}\) or establish
NumPy/Philox, iid, role-independence, uniform-word, unconditional rejection,
refusal, or finite-\(J\) SIR laws.

CP60 chooses the correlated branch left open by that source boundary.  It
adds a sealed, stdlib-only definition of the whole-request pushforward under
one explicitly **assumed**, but not verified, uniform uint64 plan seed.  For
each future fully bound request and runtime it gives an exact mathematical
totalization into validated rejection selection, rejection exhaustion, SIR
selection, pre-execution refusal, execution failure, and nonreturn, and it
states each probability as an exact seed-fiber count divided by \(2^{64}\).
The zero-argument bundle contains sixteen prospective `T28-M1-Q`/`T28-M2-Q`
strategy-and-budget templates.  Those labels do not instantiate a request or
compiled runtime map, and CP60 enumerates no seed, computes no fiber count,
verifies no seed source, and executes no sampler, kernel, provider, NumPy,
SciPy, or RNG.  It requires a correlated whole-request model and deliberately
does not assert a common \(\mu_{fp}\), proposal iid, cross-request iid,
derived-word uniformity, role-stream independence, or rejection/SIR product
formula.

CP61 adds the sealed, stdlib-only **prospective design** for a later validated
Monte Carlo approximation of those correlated whole-request laws.  It freezes
the sixteen CP60 rows, 2,048 future external seed ordinals, a 300-second
external deadline, and 554 estimands: 72 exhaustive deadline-scoped observable
cells, 170 rejection first-attempt events, and 312 selected-conditioned CP58
bounded-feature means.  It also freezes simultaneous uncertainty, a full
stable semantic trace-projection requirement, exact planned work counts, and
failure/censoring rules.  CP61 draws no seed, executes no request, imports or
loads no CP58/CP60 module from its zero-argument builder, constructs no
operational interval, and leaves every request, runtime, source, supervisor,
sample, execution, operational, power, confirmatory, manuscript, and
Test-28-closure flag false.  In particular, the current fixed-hash seed plan is
not the future external iid seed sample required by this design.

CP62 adds a sealed, stdlib-only-at-import **calibration-only execution
capsule**.  It binds the exact sixteen CP61 row requests without seed values,
one source/runtime/ABI candidate, the future 2,048-seed capsule schema, a
fresh-process deadline supervisor contract, and raw-record and stable-trace
schemas.  Its only public execution entry point accepts four module-owned
deterministic calibration case identifiers; it exposes no production seed
ingest, arbitrary-seed execution, or campaign loop.  Two fresh-child executions
of each fixed case produced matching stable semantic projections after
volatile supervisor custody was excluded.  These eight development launches
are runtime-conditional calibration evidence only.  They are not draws from
the future external source, production requests, estimates, intervals,
operational predictions, a runtime-portability theorem, power evidence,
confirmatory evidence, a manuscript claim, or Formal Test 28 closure.

CP63 adds two sealed **development-rehearsal** surfaces.  The runner module
parses the exact future seed-capsule syntax, defines the seed-major 32,768-
request schedule, and generalizes the CP62 fresh-process supervisor and
raw/stable records across all sixteen rows.  Its executable surface remains
closed to sixteen module-owned case identifiers sharing the fixed development
seed `12a5228200019dae`; every row was launched twice and each pair produced
the same stable projection.  The separately implemented stdlib-only module
imports neither that runner nor CP62, the kernel, NumPy, or SciPy.  It
independently parses each stable trace and reproduces the complete 554-estimand
rehearsal receipt.  The future capsule contains no production seed values, the
logical schedule is not instantiated, and the 512-GiB raw and 256-GiB stable
aggregate values are arithmetic ceilings rather than a capacity receipt.
Nothing in CP63 binds an external seed source, production runtime, campaign,
durable writer, shard map, estimate, interval, decision, confirmatory result,
manuscript claim, or Formal Test 28 closure.

CP64 adds a sealed, stdlib-only-at-import, **zero-execution production-custody
preflight scaffold**.  It binds the historical v14 protocol and manifest,
the CP61--CP63 semantic predecessors, the exact dependency lock, future
external-seed acquisition and production-runtime receipts, a conservative
capacity reservation contract, durable path and publication rules, a fixed
32-shard candidate policy, a production shard-map receipt schema, a proposed
v15 lifecycle, and seventeen fail-closed production gates.  Its builder does
not read either proposed v15 path, acquire a seed, contact or authenticate a
source, observe a runtime or filesystem, reserve capacity, write an attempt,
materialize a production request, expose a campaign, authorize a launch, or
execute numerical work.  All seventeen gates are `MISSING`, all four
pre-existing production blockers remain open, and Formal Test 28 remains
**OPEN**.

This protocol is one prerequisite for Formal Test 28. It cannot close that
test while this document is DRAFT or while any required implementation,
independent-oracle, execution, or verification artifact is absent.

## 3. Mathematical contracts

### 3.1 Generic and operational bounded rejection

For any proposal probability measure \(\mu\), let
\(q:\mathcal X\to\mathbb R\) be finite, measurable, and bounded above by
\(U\).  Then \(W=e^q\) satisfies \(0<W\le M=e^U\) and
\(Z=\int W\,d\mu\in(0,M]\). Suppose proposals are iid from \(\mu\),
decision uniforms are iid and independent of the proposals, and comparisons
are exact. Set \(\alpha=Z/M\) and
\(\rho_{\mu,q}(dx)=Z^{-1}e^{q(x)}\mu(dx)\). For a fixed attempt budget \(A\),
first acceptance has augmented-state law

\[
K_A=\{1-(1-\alpha)^A\}\rho_{\mu,q}+(1-\alpha)^A\delta_E.
\]

Thus exhaustion is a result, not an exclusion, and

\[
\mathcal L(X\mid X\ne E)=\rho_{\mu,q}.
\]

The two analytic specializations use
\((\mu,q)=(\Pi_N^{rat},\bar q_c)\) and
\((\Pi_N^{b64},\bar q_c)\). The operational specialization uses
\((\mu,q)=(\mu_{fp},q_c^{repr})\), conditional on the unverified
source/sampler-law premise. No specialization proves either of the others,
and rejection requires no finite global lower bound on \(q\).

The operational uint64 rule uses

\[
K(x)=\left\lfloor 2^{64}e^{q_c^{repr}(x)-U}\right\rfloor
\]

and accepts iff the retained word is strictly below \(K(x)\). Conditional on
an identical represented proposal-and-exact-score batch, couple each
independent ideal decision uniform to an independent uniform 64-bit decision
word. The probability that either augmented outcome differs is then less than
\(A/2^{64}\). This narrow bound covers only decision quantization. It covers
no error in the proposal transform, source/PRNG law, score semantics, or
analytic-to-represented bridge. A
selected-conditioned error is never inferred from this unconditioned coupling
bound without an explicit lower bound on selection mass and conditioning
amplification.

The implemented kernel-v2 certifies the integer quota for every encountered
exact rational gap \(q_c^{repr}(x)-U\le0\), including non-dyadic gaps, under
the frozen trusted Python `Decimal`/libmpdec correctly-rounded-exponential
contract.  It is not a formal verification of that library contract and is
not an exact Bernoulli implementation.  Define

\[
p_{64}(x)=2^{-64}\left\lfloor
2^{64}e^{q_c^{repr}(x)-U}\right\rfloor,
\qquad
\alpha_{64}=\int p_{64}(x)\,\mu_{fp}(dx),
\]

and, when \(\alpha_{64}>0\),

\[
\rho_{64}(dx)=\alpha_{64}^{-1}p_{64}(x)\mu_{fp}(dx).
\]

Only **if** a future evidence bundle establishes iid \(\mu_{fp}\)-proposals,
independent uniform uint64 decision words, and the required stream premises
does fixed-budget first acceptance have exhaustion probability
\((1-\alpha_{64})^A\) and conditional selected law \(\rho_{64}\).  Those
antecedents are open; the present implementation evidence certifies neither
\(\alpha_{64}\), \(\rho_{64}\), nor equality with \(\rho_c^{repr}\).

There is also a separate conditional analytic quantization theorem.  Let
\(D=2^{64}\), let \(W=e^{q-U}\in(0,1]\) under one of the two named analytic
reference layers, put \(\beta=\mathbb E[W]\),
\(p_D=\lfloor DW\rfloor/D\), and \(\alpha_D=\mathbb E[p_D]\).  Then

\[
\beta-D^{-1}<\alpha_D\le\beta.
\]

When \(\beta>D^{-1}\), the fixed-budget exhaustion probability and the
selected-law discrepancy, with
\(\rho_D(dx)=p_D(x)\mu(dx)/\alpha_D\) and
\(\rho(dx)=W(x)\mu(dx)/\beta\), obey

\[
(1-\beta)^A\le (1-\alpha_D)^A
  <(1-\beta+D^{-1})^A,
\qquad
\lVert\rho_D-\rho\rVert_{TV}<\frac{D^{-1}}{\beta}.
\]

CP53 retains outward exact-Fraction records for
\(A\in\{1,4,16,64\}\), both reference layers, and both mixed fixtures.  This
is a synthetic analytic floor-quantization theorem, not a live prediction for
\(p_{64}\), \(\alpha_{64}\), or \(\rho_{64}\): the law of \(\mu_{fp}\),
the runtime score/source premises, and their independence remain open.

### 3.2 Fixed-budget SIR

For fixed \(J\), independent proposals \(Y_j\sim\mu\), and
\(W_j=e^{q(Y_j)}\), exact SIR has marginal

\[
Q_J(B)=\mathbb E\left[
\frac{\sum_{j=1}^J W_j\mathbf 1\{Y_j\in B\}}
     {\sum_{j=1}^J W_j}
\right].
\]

Finite \(J\) is not asserted to equal \(\rho_{\mu,q}\); in particular,
\(Q_1=\mu\). With \(0<W_j\le M<\infty\) and
\(Z=\mathbb E[W_j]>0\), the mathematical convergence claim is only
\(\lVert Q_J-\rho_{\mu,q}\rVert_{TV}\to0\). Operational categorical
rounding and finite-particle error are separate ledger terms.

More quantitatively, augment the proposal cloud with its selected index.  A
change-of-measure identity followed by data processing and
Cauchy--Schwarz gives, for \(S_J=\sum_{j=1}^J W_j\),

\[
\lVert Q_J-\rho_{\mu,q}\rVert_{TV}
\le \frac{\mathbb E|S_J-JZ|}{2JZ}
\le \frac{\sqrt{\operatorname{Var}(W)}}{2Z\sqrt J}.
\]

CP53 supplies exact-rational outward enclosures of the coefficient
\(\sqrt{\operatorname{Var}(W)}/(2Z)\) and the resulting bounds at
\(J\in\{8,32,128,512\}\) for both named analytic layers and fixtures.  These
are conservative exact-IID theorem bounds, not exact finite-\(J\)
distributions, and no operational antecedent is certified.

Kernel-v2 performs fail-closed binary64 normalization of the realized exact
rational log weights and uses one 53-bit categorical transform whose stream
binds \(J\). Therefore its retained trace is not an exact categorical draw
from the mathematical normalized weights, and its finite-\(J\) output is not
an exact target sample. The global lower envelope may be absent: it is
retained when available but is not required for SIR. Any future operational
law statement must separately establish the proposal, source, stream, and
categorical-transform premises and quantify both float64 normalization and
53-bit selection discrepancy.

For completeness, this convergence is a theorem rather than an empirical
extrapolation. With \(S_{J-1}=\sum_{j=2}^J W_j\), the Radon--Nikodym density of
\(Q_J\) with respect to \(\mu\) is

\[
g_J(x)=J e^{q(x)}\,\mathbb E\left[
  \{e^{q(x)}+S_{J-1}\}^{-1}
\right].
\]

For fixed \(x\), put \(w=e^{q(x)}>0\) and
\(G_J=\{S_{J-1}/(J-1)\ge Z/2\}\). On \(G_J\), for \(J\ge2\),

\[
\frac{J}{w+S_{J-1}}\le \frac{2J}{(J-1)Z}\le\frac4Z.
\]

Because \(0<W_j\le M\), Hoeffding's inequality gives

\[
\mathbb P(G_J^c)\le
\exp\!\left\{-\frac{(J-1)Z^2}{2M^2}\right\}.
\]

The integrand is at most \(J/w\) on \(G_J^c\), so its bad-event expectation
vanishes.  On \(G_J\), the strong law and dominated convergence give an
expectation limit of \(1/Z\). Hence
\(g_J(x)\to e^{q(x)}/Z\) for \(\mu\)-almost every \(x\); both densities
integrate to one, so Scheffé's lemma gives total-variation convergence. This
theorem still assumes iid \(\mu\)-proposals and exact positive weights. A
finite experiment cannot certify those premises or the asymptotic statement.

### 3.3 Finite-atomic enumeration

Enumeration is admissible only when every declared event dimension is zero
and the full support passes the finite-oracle resource gate. For count vector
\(m\), the unnormalized target mass is

\[
e^{q_c(m)}\theta^{|m|}
\prod_d\frac{w_d^{m_d}}{m_d!}.
\]

There is no additional \(|m|!\). Multiplicity factorials may not be dropped.
Exponentials are generally non-dyadic even when \(q_c\) is rational, so any
finite categorical implementation must report its numerical construction and
its discrepancy from the ideal enumerated target.

CP54 independently derives the cap-two, two-type base category masses from
primitive activity, type weights, and complete count-vector support.  Its
direct route uses

\[
u(m)=\theta^{|m|}\prod_d\frac{w_d^{m_d}}{m_d!},
\]

while its second route multiplies the unnormalized capped-Poisson count weight
\(\theta^n/n!\) by the conditional multinomial mass
\(n!\prod_d w_d^{m_d}/\prod_d m_d!\).  The two routes agree statewise and
their common support sum is \(\sum_{n=0}^2\theta^n/n!\).  For
\(\theta=1\) and two normalized type weights this is \(5/2\), yielding count
probabilities \((2/5,2/5,1/5)\).  The hash-bound records cover the separately
declared ideal-rational and stored-binary64 parameter layers; they do not
identify either layer with a runtime sampler law or apply a target tilt.
When any event type has positive dimension, this is only a derivation of the
finite type-count category marginal; it neither enumerates the continuous
configuration support nor makes the fixture eligible for finite-atomic
enumeration.

Kernel-v2's implemented enumeration lane starts from the reference
`finite_atomic_oracle()` binary64 mass vector, here denoted
\(P_{ref}^{oracle,b64}\), evaluates each state through the certified score
provider, and performs fail-closed float64 normalization using the exact
rational scores as inputs. It does not establish that
\(P_{ref}^{oracle,b64}\) equals \(\mu_{fp}\), \(\Pi_N^{rat}\), or
\(\Pi_N^{b64}\). CP55 supplies the independent high-precision analytic oracle
and a sealed count-keyed exact score-table provider for `T28-A0-Q`. CP56
admits that exact provider through a third sealed common-facade adapter and
carries it through one generic kernel-v2 finite-atomic enumeration. The
runtime finite-atomic support order differs from the protocol order, so the
hash-bound comparison maps by exact count vector rather than positionally.
It compares the resulting float64 categorical-weight record
\(P_{enum}^{kernel,b64}\) with the CP55 stored-binary64 analytic interval
target \(\Pi_{A0Q}^{b64}\). This is deterministic nonconfirmatory integration
evidence only: no reference sampler is replayed, no categorical draw occurs,
and no equality with \(\mu_{fp}\) or either analytic reference law follows.

### 3.4 Frozen bounded-feature IPM and SIR ancestry diagnostics

For a fixture-locked finite base registry \(F_0\), CP58 defines the implicit
sign-closed class \(F=F_0\cup(-F_0)\) and, for two nonempty supplied samples
\(A\) and \(B\), the exact empirical integral probability metric

\[
d_F(A,B)=\max_{f\in F_0}\left|
  |A|^{-1}\sum_{x\in A}f(x)-|B|^{-1}\sum_{x\in B}f(x)
\right|.
\]

Every coordinate must be a finite canonical built-in binary64 value, with
negative zero refused, and is converted by `Fraction.from_float` before any
feature arithmetic.  For an exact rational projection \(z\), the only
coordinate transforms are

\[
o(z)=\max(-1,\min(1,z)),\qquad e(z)=\min(1,z^2).
\]

The frozen `T28-M1-Q` registry contains six base features: the two count
one-hot indicators, the two cap-normalized type occupancies, and the odd and
even transforms of the type-one axis projection \((1)\).  The frozen
`T28-M2-Q` registry contains thirty-three base features.  Its projections are
the type-zero axis \((1)\), the two type-one axes \((1,0)\) and \((0,1)\),
and the type-one diagonals \((3/5,4/5)\) and \((3/5,-4/5)\).  Its feature
families are the three count one-hot indicators, two cap-normalized type
occupancies, odd and even transforms for all five projections, all three
unordered type-pair occupancies, and all fifteen admissible unordered
projected odd-product interactions.  Pair features use distinct event slots;
same-type features with different projections use the frozen symmetrization
rule.  The manifest serializes every projection and feature definition, its
formula identifier, bound, normalization denominator, and semantic digest.

This IPM is a finite-class pseudometric.  It is neither empirical
continuous-space TV or KL nor the independently listed sliced-Wasserstein
secondary diagnostic.  CP58's two predeclared four-configuration calibration
pairs merely exercise the exact evaluator: the M1 calibration has IPM
\(1/2\), witnessed by the even type-one axis feature, and the M2 calibration
has IPM \(1/4\), witnessed by the type-\((0,1)\) pair occupancy.  Their input
digest provenance remains unverified, and neither record compares an observed
sample with a target law.

An ancestor is a local particle **slot in one explicit proposal cloud**, not a
configuration value.  Equal configurations in different slots remain
different candidate ancestors, and selections from clouds with different
identifiers may not be pooled.  The current kernel makes one categorical
selection for one request, so its within-request selected-ancestor count is
identically one and its occupied-slot fraction is \(1/J\); this fact is a
construction contract, not evidence of resampling diversity.  Separately,
the predeclared `T28-AESS` cloud has eight slots but six distinct configuration
values, with two repeated-value excess slots.  That value-uniqueness summary
is explicitly not ancestor occupancy.

CP58 additionally records a conditional analytic counterfactual: if the
eight fixed `T28-AESS` particle slots with normalized weights
\((1,1,1,1,1,1024,1,1)/1031\) were subjected to \(R=J=8\) independent
categorical selections from the same cloud, then for the number \(K\) of
occupied particle slots,

\[
\mathbb E[K]=\sum_{i=1}^{8}\{1-(1-w_i)^8\},
\]

with the covariance-inclusive variance formula and exact rational result
bound in the manifest.  The record collapses no equal configuration values,
executes zero additional selections, and is report-only.  It is not output of
the one-selection kernel, a prediction of an authenticated categorical source,
or an observed production unique-ancestor statistic.

### 3.5 Runtime-conditional finite-precision arithmetic and source boundary

For one supplied realized score cloud \(q_1,\ldots,q_J\), CP59 applies the
same frozen normalization expression as kernel-v2 through an independent
local implementation,

\[
 m=\max_i \operatorname{float64}(q_i),\qquad
 \widetilde w_i=\exp\{\operatorname{float64}(q_i)-m\},\qquad
 S=\operatorname{fsum}_i\widetilde w_i,\qquad
 w_i=\widetilde w_i/S.
\]

The supplied built-in binary64 weights must match this independently
recomputed vector byte for byte.  CP59 then forms the current NumPy
sequential binary64 cumulative sums \(C_i\), forces \(C_{J-1}=1\), and embeds
the exact stored CDF increments as rational numbers.  Under the narrow
counterfactual assumption that the categorical input is uniform on
\(\{0,\ldots,2^{53}-1\}\), the current right-sided search rule has exact cell
counts

\[
 n_i=\lceil 2^{53}C_i\rceil-
     \lceil 2^{53}C_{i-1}\rceil,\qquad C_{-1}=0,
\]

and cell probabilities \(n_i/2^{53}\).  Exact-score exponential enclosures,
the supplied raw float vector, its explicitly nonoperational exact
renormalization, the CDF-increment probability vector, and the 53-bit cell
law are retained as distinct objects.  When the raw float vector does not sum
exactly to one, its discrepancy is half-L1 and is not labeled total
variation.  NumPy is loaded only by the builder; its observed version and a
cumsum runtime digest are custody fields, not a transform-law certificate.
The normalization implementation does not call kernel-v2.

For the finite rejection calibration law \(\nu=(\nu_i)\), exact scores
\(q_i\le U\), and \(D=2^{64}\), CP59 records

\[
 K_i=\lfloor D e^{q_i-U}\rfloor,\qquad
 p_i=K_i/D,\qquad
 \alpha=\sum_i\nu_i p_i.
\]

Conditional only on abstract iid proposals from the declared finite law,
independent uniform uint64 decision words, and proposal/decision
independence, it derives

\[
 \Pr(T=t)=(1-\alpha)^{t-1}\alpha,\qquad
 \Pr(E)=(1-\alpha)^A,\qquad
 \Pr(X=i\mid X\ne E)=\frac{\nu_i p_i}{\alpha}
\]

when \(\alpha>0\); the selected law is undefined when \(\alpha=0\).  The
predeclared calibration grid uses \(A\in\{1,4,16,64\}\), with uniform
four-atom M1 and six-atom M2 synthetic proposal tables.  These are exact
finite-law calculations, not live \(\alpha_{64}\), \(\rho_{64}\), refusal,
or operational proposal predictions.

The source boundary is substantive.  With one 64-bit plan seed the joint
trace support is at most \(D\), whereas two independent uniform uint64 words
have product support \(D^2\).  Hence every uniform-seed pushforward from the
current surface is at total-variation distance at least
\(1-D/D^2=1-2^{-64}\) from that two-word product law; a fixed seed is a point
mass at distance \(1-D^{-2}\).  A declaration of iid or role independence
cannot remove this support obstruction.  Unconditional closure therefore
requires either a richer external independent-word/capsule source API or a
whole-request pushforward law under a seed distribution, with correlated
predictions and without iid/role-independence formulas.  This source-law
lower bound supplies no output-law lower bound, because deterministic maps
can contract total variation.

### 3.6 Correlated whole-seed pushforward definition

CP60 adopts the whole-request alternative; it does not retrofit independent
words onto the current one-seed interface.  Let \(D=2^{64}\).  Its sole source
premise is that, for **one** future fully fixed seed-free request \(R\) and
fully fixed runtime \(E\), an external seed \(S\) is exactly uniform on
\(\{0,\ldots,D-1\}\).  This is an assumption-only theorem premise.  It is not
verified by the current fixed-hash seed plan and says nothing about a sequence
of requests, operating-system entropy, derived Philox words, Gaussian words,
categorical words, or independence between roles.

For a seed \(s\), let \(K_{R,E}(s)\) denote current kernel-v2 after inserting
that exact plan seed.  Its mathematical totalization \(F_{R,E}(s)\) retains
one of six pairwise-disjoint tags, together with the complete applicable
payload:

1. `returned-rejection-selected`;
2. `returned-rejection-exhausted`;
3. `returned-sir-selected`;
4. `preexecution-refusal`;
5. `execution-failure`; or
6. `nonreturn`.

The returned rejection trace retains configuration values, exact scores and
quota records, decision words, its acceptance vector, first selected index,
and selected value or exhaustion.  The returned SIR trace retains the entire
configuration cloud, exact scores, normalized-weight bytes, resampling word,
uniform-53 value, selected index, and selected configuration value.  A
selected empty configuration is not a refusal, failure, or nonreturn.  The
explicit nonreturn tag makes the mathematical alphabet exhaustive; it does
not prove backend termination or make failure versus nonreturn mechanically
observable from an ordinary returned Python object.  For a fixed strategy,
the returned-status tags belonging only to the other strategy have empty
fibers.

For every event \(B\) in that totalized outcome space, CP60 records only the
exact formula

\[
 N_B=\#\{s\in\{0,\ldots,D-1\}:F_{R,E}(s)\in B\},\qquad
 \Pr\{F_{R,E}(S)\in B\}=N_B/D.
\]

In particular, \(\Pr\{F_{R,E}(S)=y\}=N_y/D\), and the six aggregate
status-fiber masses sum to one.  For rejection, \(N_{\mathrm{first},t}/D\)
is the probability of a complete validated selected trace whose one-based
first-acceptance index is \(t\); exhaustion, refusal, execution failure, and
nonreturn are their separate fiber counts divided by \(D\).  The probability
that slot \(t\) is recorded accepted **and** the complete rejection result is
validated is \(N_{\mathrm{accept},t}/D\); this is an unconditional
subprobability and does not condition away execution failure or nonreturn.
The probability of no validated returned output is

\[
 (N_{\mathrm{preexecution\ refusal}}+N_{\mathrm{execution\ failure}}
   +N_{\mathrm{nonreturn}})/D.
\]

For a selected value \(c\), the unconditional mass is \(N_{\mathrm{select},c}/D\).
The selected-conditioned mass
\(N_{\mathrm{select},c}/N_{\mathrm{selected}}\) is defined only after
\(N_{\mathrm{selected}}>0\) is established.  SIR selected-value and arbitrary
cloud/weight/cell events use the same whole-trace fiber rule.  No common
\(\alpha_{64}\), \((1-\alpha_{64})^A\), \(\rho_{64}\), or
product-\(\mu_{fp}^J\) formula follows.

The joint realized proposal trace is one correlated pushforward of \(S\).
For each explicitly reached and recorded slot \(t\), CP60 permits only the
slot sublaw

\[
 \mu_{R,E,t}(C)=D^{-1}\#\{s:\text{slot }t\text{ is reached, recorded, and
 has configuration in }C\}.
\]

This is generally a subprobability measure.  It may be normalized
conditionally only if its reach mass is first established positive; CP60
performs no such division.  The family of slot projections does not identify
one common \(\mu_{fp}\) or an iid product law.  For one fixed seed \(s_0\), the
law is instead the point mass
\(\delta_{F_{R,E}(s_0)}\); deterministic replay neither establishes nor
samples the uniform-seed pushforward.

The bundle predeclares exactly sixteen prospective rows in fixture order
`T28-M1-Q`, `T28-M2-Q`; within each fixture, rejection budgets
\(1,4,16,64\) precede SIR budgets \(8,32,128,512\).  Every row has
`request_parameters_fully_bound=false` and
`fixed_request_map_instantiated=false`.  Source-file digests are custody
labels only; the optional dependency-lock and runtime-record digests are
absent.  No count defaults to zero: status, first-acceptance, selected-value,
refusal, exhaustion, execution-failure, and nonreturn counts are all
explicitly absent.

An operational use must first freeze the transitive local sources; exact
Python build and standard library; NumPy/SciPy distributions and loaded
extensions; Philox, SeedSequence, 53-bit uniform, standard-normal Ziggurat
code, tables, state schema, and variable word consumption; NumPy
`exp`/`cumsum`/`searchsorted`; SciPy `gammaln`/`logsumexp`; Decimal/libmpdec;
the linked libc/libm, compiler and ABI; and the operating system, architecture,
CPU, endianness, and floating-rounding environment.  A version string or the
current kernel runtime digest alone is insufficient.

Any later Monte Carlo approximation must bind that request and totalized map
before sampling; verify iid uniform uint64 seeds with replacement or freeze a
separate without-replacement finite-population design; retain every refusal,
failure, and nonreturn; prespecify a termination classifier or bounded
external supervisor while keeping timeout censoring distinct from semantic
nonreturn; forbid retry, drop, replacement, and data-dependent seed choice;
and prespecify uncertainty, familywise multiplicity, positive-selected-count,
and full custody rules.  CP60 performs none of those steps and computes no
operational probability.

### 3.7 Prospective whole-seed validated-Monte-Carlo design

CP61 freezes one future design without asserting that its premises have been
realized.  It preserves the CP60 row order exactly: `T28-M1-Q` precedes
`T28-M2-Q`; within each fixture, rejection budgets \(1,4,16,64\) precede SIR
budgets \(8,32,128,512\).  The future seed source must supply the ordered
sample

\[
 (S_1,\ldots,S_{2048}),\qquad
 S_i\mathrel{\mathrm{iid}}\operatorname{Unif}\{0,\ldots,2^{64}-1\},
\]

with replacement.  A repeated uint64 value is a retained draw, never grounds
for a retry.  Seed ordinal \(i\) is reused across all sixteen rows, so the rows
are paired by ordinal; their outcomes are not assumed independent.  The exact
uint64 value \(S_i\) is passed **unchanged** as `plan_seed` to every row at that
ordinal; no fixture-, strategy-, shard-, or request-hash runner derivation may
intervene.  No draw or outcome may be retried, dropped, replaced, or topped
up.  CP61 records these as future requirements only: it does not verify an
external source, and the current fixed-hash seed plan is not such a sample.

Every scheduled request has a 300-second external deadline.  For each of the
eight rejection rows, the five deadline-scoped observable cells are
`returned-rejection-selected-before-deadline`,
`returned-rejection-exhausted-before-deadline`,
`preexecution-refusal-before-deadline`,
`execution-failure-before-deadline`, and
`timeout-censored-at-deadline`.  For each of the eight SIR rows, the four cells
are `returned-sir-selected-before-deadline`,
`preexecution-refusal-before-deadline`,
`execution-failure-before-deadline`, and
`timeout-censored-at-deadline`.  This gives 72 binomial observable-cell
estimands.  A deadline timeout is retained censoring at the supervisor
boundary; it is **not** identified with CP60's mathematical semantic
`nonreturn` tag.  Returned cells require a structurally validated return before
the deadline.  Refusal and execution-failure cells require the corresponding
observation before the deadline and are not called returned outputs.

For each rejection row and every one-based attempt through its fixed budget,
CP61 separately freezes the event that a complete validated predeadline return
first selects at that attempt.  Across both fixtures this gives
\(2(1+4+16+64)=170\) further binomial estimands.  Every observable and
first-attempt proportion uses all 2,048 retained seed ordinals as its
denominator; no failure or censoring may be conditioned away.

For every row, CP61 also applies every feature in the row fixture's complete
CP58 registry to validated predeadline selected configurations.  There are six
M1 features and thirty-three M2 features, so the eight rows per fixture give
\(8\cdot6+8\cdot33=312\) selected-conditioned bounded-feature means.  Their
denominator is the selected count \(K\) in that row.  Together the frozen
family contains

\[
 72+170+312=554
\]

estimands.  These finite projections do not estimate a complete continuous
trace law or total variation.

The familywise error budget is \(1/100\).  CP61 assigns each of the 554
estimators a two-sided error budget \(1/55{,}400\), hence each tail receives

\[
 \delta=1/110{,}800,
 \qquad 554/55{,}400=2\cdot554/110{,}800=1/100.
\]

Every future binomial interval is the two-sided exact Clopper--Pearson interval
with exact-rational tail evaluation and an explicitly outward dyadic
bisection.  For \(X\sim\operatorname{Binomial}(n,p)\), the lower endpoint is
zero when \(k=0\).  Otherwise initialize \(lo=0,hi=1\), perform exactly 256
updates with \(mid=(lo+hi)/2\), and compute
\(T=\Pr_{mid}\{X\ge k\}\) exactly: if \(T<\delta\), set \(lo=mid\); otherwise,
including equality, set \(hi=mid\).  Publish \(lo\).  The upper endpoint is one
when \(k=n\).  Otherwise repeat 256 updates using
\(C=\Pr_{mid}\{X\le k\}\): if \(C>\delta\), set \(lo=mid\); otherwise,
including equality, set \(hi=mid\).  Publish \(hi\).  Thus zero observed events
still have a strictly positive upper endpoint.  CP61's public arithmetic
helper is deliberately restricted to calibration inputs with \(n\le128\);
the future \(n=2048\) intervals remain uncomputed.

A selected-feature interval is published only when \(K\ge1040\).  It clips
the sample feature mean plus or minus \(3/40\) of that feature's exact frozen
range to the feature bounds.  Thus the target half-width is \(0.075\) for a
\([0,1]\) feature and \(0.15\) for a \([-1,1]\) feature.  When \(K<1040\), the
result is `insufficient-selection`, with no interval and no top-up.  At the
minimum count, Hoeffding's one-sided exponent is exactly

\[
 2(1040)(3/40)^2=117/10.
\]

The exact positive Taylor partial sum

\[
 \sum_{j=0}^{17}\frac{(117/10)^j}{j!}
 =\frac{428914006377131589846189933005011}
 {3753164800000000000000000000}>110800
\]

shows \(e^{-117/10}<1/110800\).  Each one-sided bounded-feature tail is
therefore strictly below its assigned tail budget, the two-sided failure is
strictly below \(1/55{,}400\), and a union bound over all 554 estimators is at
most \(1/100\).  This is a simultaneous-coverage design calculation, not a
selected-count probability or power guarantee.

The future raw record must retain every complete raw trace and its digest.  A
separate stable semantic projection must retain stable request, fixture,
strategy, budget, plan-seed, local-source, facade/provider-certificate,
reference/source-parameter, role-context, stable-runtime, derived-role-seed,
RNG-state, canonical configuration-value/binary64-byte, independently
recomputed provider/configuration-digest, exact score, quota, word,
acceptance, complete rejection-attempt or SIR-cloud/weight/ESS/resampling, and
closed status/failure-code fields.  It excludes raw process/object identities,
address-bearing representations, unbounded exception text, and plan,
owner/execution-certificate, nested, or result hashes that inherit volatile
identity.  The projection does not replace the raw trace.  The compact
554-estimand projection is not the full stable trace.  CP61 requires this
contract but does not instantiate it on observations or establish
cross-process parity.

The fixed prospective work is 32,768 requests.  Its planned maxima are 348,160
rejection proposal slots, 2,785,280 SIR proposal slots, 3,133,440 total
proposal slots, 16,384 SIR resampling draws, 4,700,160 event occurrences, and
7,833,600 coordinates.  These are scheduled or worst-case design counts, not
observed consumption, timing evidence, an allocation receipt, or a power
calculation.

Any future supervisor, seed-source, durable-recording, or trace-custody
infrastructure failure invalidates the **entire** Monte Carlo attempt before
any interval is produced.  It is not an estimand cell, execution failure,
timeout, dropped draw, retry, replacement, or top-up.  The observable-cell
partition is conditional on infrastructure fidelity, which CP61 has not
verified.  Requests, runtime, source capsule, supervisor, seed sample, raw
trace sample, execution, estimates, intervals, operational predictions,
full-trace law, total variation, power, confirmatory evidence, and manuscript
promotion all remain absent.  Formal Test 28 therefore remains open.

### 3.8 Calibration-only whole-seed execution capsule

CP62 binds a concrete precursor to the future runner without enabling that
runner.  Its exact sixteen seed-free request bindings preserve the CP61 row
order and the CP60 rejection budgets (1,4,16,64) and SIR budgets
(8,32,128,512).  Each binding fixes its source, facade, kernel, residual
context, reference and score parameters, certificates, strategy, and budget,
but contains no seed value and has
`request_instance_fully_bound=false`.  Future logical requests remain ordered
seed-major by

\[
  (\text{seed ordinal}-1)16+\text{row ordinal}.
\]

The capsule binds one Darwin/arm64 CPython 3.11.5, NumPy 2.4.6, SciPy 1.17.1
runtime/source/ABI candidate, its dependency and executable/library closures,
the relevant local-source capsule, a sanitized child environment, and
round-to-nearest binary64 mode.  The candidate was observed in the fixed
calibration children, but the runtime path is deliberately nonsemantic and the
record keeps runtime portability, production-runtime matching, executed-bytecode
attestation, and a transform-law theorem false.  The externally bound CP62
source digest supplies self-custody; it does not convert a source-file
observation into executed-bytecode attestation.

The future seed-capsule contract fixes ordinals (1,\ldots,2048), ordered
lowercase sixteen-hex-digit uint64 values, exact JSON keys, a 131,072-byte cap,
duplicate retention, semantic ordering, and no retry, drop, replacement, or
top-up.  It contains no seed values, source method, source receipt, acquisition
session, or body digest.  The capsule is not instantiated, no external source
is bound, and neither digest nor frequency checks would by themselves prove
iid uniform sampling with replacement.

The supervisor contract requires one fresh POSIX spawn/exec child and process
group per request, a parent-monotonic 300-second deadline, completion strictly
before the deadline, equality classified as timeout, an exact one-frame
return, bounded request/raw/stderr frames, termination and reap ceilings, no
retry, and whole-attempt invalidation for supervisor or custody failure.  It
keeps timeout censoring distinct from CP60 semantic nonreturn.  Production
entry is disabled.  The public raw schema retains canonical values, complete
validated-return kernel traces, and volatile supervisor custody separately
from the stable projection.  It predeclares closed refusal and failure shapes,
but the calibration runner's closed refusal/failure classification is not
implemented, the production schema is not frozen, and no production record or
capacity receipt exists.

The only executable cases are the two (A=64) rejection rows and two (J=512)
SIR rows, one of each for `T28-M1-Q` and `T28-M2-Q`.  Their seeds are fixed
domain-separated calibration constants, are not external-source draws or
future capsule members, and cannot be supplied by a caller.  Each case is
precommitted to exactly two fresh-child executions, with concurrency one and
an eight-launch global maximum.  The stable projections matched across the
two processes for all four cases; the retained raw records differ in volatile
custody as expected.  The exact stable-projection receipts are:

- `m1-rejection-a64`: SHA-256
  `ad0fd60347f16adb6317d464d8708bd2b2f9277f2a5195b43441765a489f1d2a`,
  296,473 canonical JSON bytes;
- `m1-sir-j512`: SHA-256
  `7685a2357efd06a8b7dc473759ec19ba799d6039fc3841486428ac17620202e9`,
  850,656 canonical JSON bytes;
- `m2-rejection-a64`: SHA-256
  `146924d4a7c7504a4540b60249f46fb3ed71a7fc6b10195958b5b461f469d04f`,
  342,364 canonical JSON bytes; and
- `m2-sir-j512`: SHA-256
  `37a982bc3cc8744087f7b9d356fc8ff15c3bd371c81d5f9508095f27e3724ccb`,
  904,281 canonical JSON bytes.

Those four receipts establish deterministic parity only for the fixed
calibration cases in the bound candidate environment.  They do not establish
production cross-process parity, the full stable-trace law, total variation,
source iid, infrastructure fidelity, or production runtime matching.  CP62
ingests no production seed, runs no production campaign, computes no estimate
or interval, and derives no operational prediction.  The execution runner and
independent recomputation blocker therefore remains open even though this
capsule and calibration precursor is hash-bound.

### 3.9 Development-only all-row runner and independent recomputation rehearsal

CP63 binds a rehearsal of the next runner/recomputation interface without
instantiating the production experiment.  The runner's seed-capsule parser
accepts only the exact eleven-key, canonical, bounded future capsule shape,
retains ordered duplicate uint64 values, and binds its body digest.  Parsing
can establish syntax and digest consistency only; it cannot verify that the
values are iid uniform draws with replacement or authorize their execution.
The associated definition-only schedule has 2,048 seed ordinals, sixteen row
ordinals, and 32,768 logical requests ordered exactly as

\[
  L=(\text{seed ordinal}-1)16+\text{row ordinal}.
\]

Each future seed value would pass unchanged as `plan_seed`.  No fixture,
strategy, budget, or shard hash is interposed before that assignment;
duplicate values remain distinguishable by seed ordinal.  CP63 binds no
external capsule, source method, source receipt, acquisition session, shard
map, instantiated production request, or production authorization.

The executable rehearsal instead defines exactly sixteen module-owned cases,
one for every CP61 row.  All use the fixed development seed
`12a5228200019dae`, derived as the first eight big-endian bytes of
SHA-256(`cp63-test28-all-row-rehearsal-seed-v1\0`).  This seed is neither an
external-source draw nor a future capsule member.  Each case permits exactly
two launches; concurrency is one and the global limit is 32.  The raw schema
retains repetition, request identity, the complete semantic kernel trace, and
volatile supervisor custody.  The stable projection drops only repetition,
supervisor custody, and the raw-record digest, so the two launches can differ
in raw custody while remaining byte-identical in semantic projection.  Its
four closed arms distinguish return before deadline, pre-execution refusal,
execution failure, and timeout censoring; a returned rejection arm may record
selection or exhaustion.

The separately bound independent recomputation module is source-independent
of the runner: it imports neither the runner, CP62, the kernel, NumPy, nor
SciPy.  It independently validates canonical stable bytes, produces one
compact observation for each row, and enumerates exactly 72 observable, 170
rejection-first-attempt, and 312 selected-feature estimands, 554 total.  From
one complete sixteen-row set it creates a repetition-blind receipt; the two
rehearsal repetitions produced identical compact observations and identical
554-estimand receipts.

The exact runner bundle is 26,642 canonical JSON bytes with plain SHA-256
`8f7d52b0e1e5a529665d8f5d781a6381f8dfa5f8b4b17c62436c18c9c9018143`
and record digest
`442c4b0f134a96efe32b5246b4eb5b05233d61a13c62c0a7d1f21c9bbbd32f85`.
Its seed-capsule, schedule, lifecycle, raw-schema, and resource component
record digests are respectively
`1765adf642962c73b61634dde767fe9d2c2fef5fd71c21305fe43c6d338cf80d`,
`7ca5555de1aa852021c6b7fd181417a629dcec461455650ecafc495f5e6fb607`,
`e335fe95f81c69ebe632a00344248d48095ceffb5c8cc1b7e4c5770b4f5a951a`,
`29f17aa7528971e7892b6ea4ccb37b5943190a0e592191341ae444e8ed63b3cb`,
and
`17259329bbca1029e989029594af67570f81731d9b21355a5151277ba7938d40`.
The machine manifest serializes those complete records and all sixteen case
records, not merely this digest summary.

The exact independent bundle, including all 554 ordered estimand identifiers,
is 52,992 canonical JSON bytes with plain SHA-256
`e78ad0e95db723af47e6c5f90a6c58e28f24fbdbc6433e5e572113c62fa2ef74`,
record digest
`b219de24a17af7c06b503af07110ed863c339bca19c7457c163412ae0e76ddb9`,
and public tagged digest
`473f7aa7fec510c92ea5f47c5bab79636fc84932986f6c5f420fb0e4c189594b`.
The repetition-blind 554-estimand receipt is 12,939 canonical JSON bytes with
plain SHA-256
`4c281147b68adc5a83ddd88bab73c42cef619498a13a7f234acb4cd886a40ee7`,
record digest
`870b89d2252dd5e62fc0c10982d5d2f194402b2a941c4c7bd8a0b6214a2832dc`,
and public tagged digest
`895b3afbe514158fdfbc3c3d2ae67175cdab2a5834cbf25b00297e69aa179406`.

The retained final focused acceptance ran both launches for all sixteen rows:
151 tests passed in 281.71 seconds of pytest time (real 281.95, user 272.32,
sys 5.29 seconds).  Its complete 24,810-byte canonical receipt has plain
SHA-256
`83113460c4a4963ea815a2c54b9f1f7a8e2c1fbe7d4698fbb56a0f7addc1cf4d`
and domain-separated receipt digest
`2b2f41f14424ddb164b6db793991ece8b222a4e4295d7e0143c6b6496c50097b`.
The repetition-blind sixteen-launch semantic-pin receipt has digest
`d7dfdae440b3b26b289279ccdda6e665fe43fee965c0836fe1d6dac91ce8d5e7`.
The manifest retains the complete acceptance object, including all sixteen
stable/compact pins and both raw-launch custody receipts for every row.

CP63 conditionally reuses CP62's candidate runtime-lock record
`5b40737ba345315075c1e5e619ea1e7cd2a6628f1ba63a0101128ae9223e2460`.
It does not recompute the complete compiled runtime map or establish a
production match.  Pre/post source-file hashing binds the observed source
bytes but is not executed-bytecode or loaded-code-object attestation, and the
runtime path remains nonsemantic.  The raw and stable aggregate bounds of
549,755,813,888 and 274,877,906,944 bytes (512 and 256 GiB) are worst-case
ceilings only: no storage, throughput, or capacity receipt is present.

Accordingly, CP63 satisfies a new hash-bound nonconfirmatory rehearsal
prerequisite but remains only a completed precursor to the production runner
and unconditional operational-prediction blockers.  Production seed ingest,
arbitrary-seed execution, a campaign loop, durable attempt writing, shard
mapping, capacity allocation, complete 32,768-request recomputation, estimates,
intervals, a decision, a frozen production schema, runner-blocker closure,
confirmatory evidence, manuscript promotion, and Formal Test 28 closure all
remain absent or false.

### 3.10 Zero-execution production-custody preflight scaffold

CP64 defines the custody boundary required before any later production
attempt may become executable.  The sealed zero-argument bundle is
deterministic and standard-library-only at import.  It imports no project
module and performs no host-filesystem, process, network, clock, entropy, RNG,
runtime, capacity, or project-state observation.  The artifact binds the exact
v14 predecessor protocol and machine manifest and their DRAFT/OPEN state; it
also binds the CP61 design, CP62 runtime/supervisor/projection contracts, CP63
runner and independent-recomputation contracts, and
`requirements/m1-reference-macos-arm64-py311.lock`.  The CP64 source hash is
deliberately an external binding rather than a self-reference.

The proposed v15 lifecycle is
`DRAFT_PRE_FREEZE`, `FROZEN`, `STARTED`, and terminal `PASS`, `FAIL`,
`INVALID_PROTOCOL`, `ABORTED_INFRA`, or `INCOMPLETE`.  From `FROZEN`, an
attempt may either become `STARTED` or terminalize before start as
`INVALID_PROTOCOL`, `ABORTED_INFRA`, or `INCOMPLETE`; from `STARTED`, it may
enter any of the five terminal states.  Preflight and authorization are
artifact stages, not lifecycle states.  This extension remains merely
proposed: at bundle construction the v15 protocol/manifest availability and
consumption flags are false and the transition graph is not authoritative for
production.

External-source custody begins with exclusive, no-follow creation and durable
commit of both an acquisition journal and an acquisition-start receipt before
source contact.  The journal is preallocated as a non-sparse file for at most
2,048 fixed 80-byte chained binary entries, hence at most 163,840 bytes.  Its
journal formulas are exactly
`SHA256(cp64-external-seed-acquisition-journal-head-v1\0+acquisition-start-receipt-sha256)`
for the initial head and
`SHA256(cp64-external-seed-acquisition-journal-entry-v1\0+start-receipt-sha256+ordinal-uint64-be+value-uint64-be+previous-entry-sha256)`
for entry $i$.  Thus each entry binds the start receipt, the big-endian uint64
ordinal and value, and the previous entry digest.  The
journal path/device/inode is rechecked before the start receipt and before
every append, and every entry, including the final entry, must be file-fsynced
before another draw or a completed source receipt.  A completed receipt must
bind the journal digest, final head, exact count 2,048, and the same ordered
seed-value commitment later cross-checked against the capsule.  Canonical
syntax or a digest alone cannot establish source authority or iid uniform
sampling.

A durably committed acquisition start spends the attempt.  Any durable seed
value also spends it.  If a source returns a value that cannot be journaled
and fsynced, that value is not claimed retained, but the attempt is still
spent and must terminalize `INCOMPLETE`.  Recovery accepts only the longest
valid fsynced prefix; torn suffixes are not value evidence, and no resume,
top-up, redraw, replacement, or reselection is allowed.  A partial-acquisition
terminal receipt retains all durably journaled values.  The complete source
receipt and partial terminal receipt are mutually exclusive.

The runtime receipt must be attempt- and freeze-bound, postdate freeze, match
the exact dependency lock, bind a complete source manifest including the
externally bound CP64 source, record the pre-import environment, loaded local
source closure, executable/framework/stdlib and NumPy/SciPy payload closures,
and the compiled ABI map.  CP62's candidate runtime lock is a predecessor
binding only: CP64 neither recomputes the full production lock nor verifies a
production match.

Capacity passes only after exclusive, disjoint destination and auxiliary
reservations have actually been established on the same storage root and
filesystem.  The destination reservation floor is 1,099,511,627,776 bytes
(1 TiB); the conservative auxiliary-metadata reservation floor is
34,359,738,368 bytes (32 GiB); and the combined floor is
1,133,871,366,144 bytes.  Both physical non-sparse allocation and enforced
quota must satisfy the applicable floor before and after reservation, at
least 4,096 inodes must remain, and all filesystem/reservation verifications
must pass.  A free-space or quota snapshot alone is insufficient.  The
auxiliary reservation must remain exclusive, same-root, non-double-counted,
consumed in place, and retained until commit.  Because the complete auxiliary
type/range/size schema and bounded-size proof are not yet frozen or present,
the capacity predicate is false in CP64.

The frozen candidate policy partitions the 2,048 seed ordinals into 32
contiguous shards of 64 seeds and 1,024 seed-major logical requests each.  All
sixteen rows for one seed stay together.  Each candidate shard has a
26,910,665,728-byte payload ceiling and an exact 34,359,738,368-byte (32-GiB)
destination reservation; the 32 reservations total exactly 1 TiB.  Four
reserved destination partial files per shard cover requests, raw records,
stable traces, and bounded stderr records.  The future shard-map receipt must
reproduce every candidate range/path/partition exactly, bind four ordered
per-file reservation-entry digests, the schedule, capacity and durability
receipts, the reservation manifest, and the attempt.  The candidate policy is
frozen as a definition but is not selected, bound, or instantiated for
production.

The durability contract declares a closed relative-path inventory of 36
global paths, eight paths per shard, and two conditional paths for partial
seed acquisition and rejected authorization candidates.  Paths are
POSIX-relative with no empty, dot, dot-dot, absolute, or backslash components;
symlinks, hardlinks, overwrite, and post-commit append are forbidden.  This is
the scaffolded acquisition-path inventory, not a frozen complete production
roster.  Reserved partial inodes are exclusive, non-sparse, consumed in place,
verified against the reservation manifest and inode identity, truncated only
after complete writing, file-fsynced, hashed, renamed without replacement in
the same directory, and followed by a directory fsync.  Raw records remain
separately retained, and a stable projection never replaces them.
`COMMITTED.json`, created only after the terminal state and SHA-256 manifest,
is the sole publication boundary.

Launch selection is a two-stage durable choice.  Before an `AUTHORIZATION`
arm may win, an authorization candidate must already exist as an exclusive,
no-follow, fsynced `launch_authorization.json.partial`.  The exclusive
`preauthorization_outcome.json` chooses either `AUTHORIZATION` or one frozen
prestart terminal arm.  Recovery completes that winner without reselection:
the authorization winner publishes the verified prepared bytes by
rename-no-replace and directory fsync; a terminal winner never publishes a
final authorization and conditionally retains the losing prepared bytes as
`rejected_launch_authorization_candidate.json`.  After final authorization,
the exclusive `postauthorization_outcome.json` chooses either `STARTED` or a
postauthorization prestart terminal arm.  Its winner is likewise recoverable
without reselection.  A durable started arm and its binding `STARTED.json`
must both precede every production runner, RNG, or child process.

There are seventeen ordered production gates.  The preflight summary covers
the first fifteen and requires fifteen aligned `PASS` states and fifteen exact
nonzero evidence digests.  Independent signoff is gate 16, and explicit
launch authorization is gate 17.  The future digest graph has twenty nodes
and forty-four edges; it is acyclic and launch authorization is its sole
sink.  CP64 supplies schemas and cross-bindings only: all seventeen gate
states are `MISSING`, the evidence-present count is zero, and no summary,
signoff, authorization, `STARTED.json`, durable output, metric, interval, or
decision exists.

In order, the gates are:

1. `v15-protocol-sidecar-and-machine-manifest-frozen`;
2. `complete-production-source-manifest`;
3. `exact-dependency-lock-matched`;
4. `full-production-runtime-lock-recomputed-and-matched`;
5. `external-seed-source-receipt-and-authority`;
6. `external-seed-capsule-sequence-crosscheck`;
7. `production-request-schedule-materialized`;
8. `capacity-receipt-meets-usable-and-quota-floor`;
9. `durable-writer-qualified`;
10. `production-shard-map-selected-and-materialized`;
11. `production-runner-supervisor-qualified`;
12. `closed-refusal-failure-classifier-qualified`;
13. `independent-full-32768-recomputation-qualified`;
14. `independent-554-estimate-interval-decision-path-qualified`;
15. `power-review-and-32-primary-thresholds-frozen`;
16. `independent-review-signoffs-present`; and
17. `explicit-launch-authorization-present`.

Consequently CP64 satisfies only the hash-bound nonconfirmatory scaffold
prerequisite `whole_seed_production_custody_preflight_scaffold_definition`.
It does not close `runner_and_recomputation`,
`unconditional_operational_predictions`, `power_and_thresholds`, or
`confirmatory_custody`; it creates no production evidence and leaves Formal
Test 28 open.

## 4. Frozen-fixture design

The final machine manifest will serialize every scalar, array, support order,
feature definition, projection, and expected formula. The following fixture
families are mandatory; their final identifiers and numerical encodings cannot
change after protocol freeze.

### 4.1 Exact atomic target lane

`T28-A0-H` uses cap two, activity one, and two zero-dimensional types with
weights \((2/5,3/5)\). Its canonical support is

\[
[\varnothing,\{a\},\{b\},\{aa\},\{ab\},\{bb\}].
\]

The exact base masses are

\[
[2/5,4/25,6/25,4/125,12/125,9/125].
\]

For the independent multiplicative-factor oracle
\([1,2,1/2,3,3/2,1/4]\), the normalizer is \(549/500\) and the exact target is

\[
[200,160,60,48,72,9]/549.
\]

This lane is an independent enumeration/arithmetic oracle. It is not evidence
that any current production score provider can represent the logarithms of all
six rational factors exactly.

The CP54 ideal-rational record independently reconstructs the displayed base
vector from \(\theta=1\), cap two, weights \((2/5,3/5)\), and the complete
ordered count support.  Its stored-binary64 companion uses the separately
declared exact dyadic weights
\(3602879701896397/2^{53}\) and
\(5404319552844595/2^{53}\), and produces a distinct base vector while
preserving the cap-two count marginal.  Neither record applies the
multiplicative-factor oracle, establishes \(h=\exp(q)\), or certifies
finite-precision sampling.

`T28-A0-Q` uses the same reference with the exact-rational score table

\[
q(\varnothing,\{a\},\{b\},\{aa\},\{ab\},\{bb\})
  =(0,1/2,-1/2,1,1/2,-1),
\]

so its exact score envelope is \([-1,1]\). This is a new direct-score fixture;
the table is explicitly not the logarithm of the `T28-A0-H` multiplicative
factors. Put \(t=w_a\) and \(s=e^{-1/2}\). In protocol support order its base
mass vector is

\[
p(t)=\bigl(2/5,2t/5,2(1-t)/5,t^2/5,
           2t(1-t)/5,(1-t)^2/5\bigr),
\]

and its exponential score factors are
\((1,s^{-1},s,s^{-2},s^{-1},s^2)\). Hence

\[
Z(t)=\sum_i p_i(t)e^{q_i},\qquad
\pi_i(t)=\frac{p_i(t)e^{q_i}}{Z(t)}.
\]

For the ideal-rational layer \(t=2/5\), this specializes to

\[
Z(2/5)=\frac25+\frac{32}{125s}+\frac{6s}{25}
       +\frac{4}{125s^2}+\frac{9s^2}{125}.
\]

Equivalently, after shifting by the upper envelope \(U=1\), the factors are
\((s^2,s,s^3,1,s,s^4)\), the ideal acceptance mass is
\(\beta(t)=s^2Z(t)\), and the normalized probabilities are unchanged.

CP55 independently reconstructs the factorial base masses and encloses both
routes with exact `Fraction` endpoints at precision stages
\((64,128,192,256)\) bits for the ideal-rational weights
\((2/5,3/5)\) and the separately declared stored-binary64 parameter weights.
It also records the binary64-minus-ideal normalizer, acceptance-mass, category,
and total-variation perturbations. The strict signs are interval-certified,
not inferred from rounded displays.

The protocol order of count vectors is
\(((0,0),(1,0),(0,1),(2,0),(1,1),(0,2))\), whereas the runtime counting-space
order is \(((0,0),(0,1),(1,0),(0,2),(1,1),(2,0))\). The current hash-bound
DRAFT runtime-to-protocol permutation is \((0,2,1,5,4,3)\). CP56 verifies
that mapping by exact count-keyed lookup through the new atomic-table facade
adapter and generic kernel-v2 enumeration. The exact `Fraction.from_float`
sum of the retained runtime base-mass vector is \(1+11\cdot2^{-57}\). In
runtime order, the resulting float64 output weights are

\[
(\texttt{0x1.7ade79b3ae4fcp-2},
 \texttt{0x1.13c13c86fd12fp-3},
 \texttt{0x1.f3b835374e505p-3},
 \texttt{0x1.9168b59dc254ap-6},
 \texttt{0x1.2bd4ecbac896bp-3},
 \texttt{0x1.498f2ed7ae37fp-4}).
\]

Their exact `Fraction.from_float` sum is
\(1-2^{-57}\), not one. Every stored output point lies outside its CP55
analytic interval, and the rigorous output-minus-analytic half-L1 interval is
approximately \(8.508157450884242\times10^{-17}\). It is deliberately not
called total variation because the output vector is not an exact probability
measure. The manifest binds the exact residual, the runtime and protocol
weight-vector hashes, and the exact rational half-L1 endpoints through the
stable CP56 semantic comparison digest. The CP55 provider's own
`facade_integrated=false` and `kernel_integrated=false` fields remain correct
historical artifact-scope statements; CP56 does not rewrite that record.
Neither CP55 nor CP56 identifies either analytic layer with
\(P_{ref}^{oracle,b64}\), \(\mu_{fp}\), or an operational categorical law.

### 4.2 Mixed atom/continuous cap-one lane

`T28-M1-Q` uses ideal-rational activity one, cap one, a zero-dimensional
type of weight \(2/5\), and a one-dimensional standard-Gaussian type of
weight \(3/5\).  Its stored normalized binary64 weights are separately bound
as

\[
\texttt{0x1.999999999999ap-2}
=\frac{3602879701896397}{9007199254740992},\qquad
\texttt{0x1.3333333333333p-1}
=\frac{5404319552844595}{9007199254740992}.
\]

The ideal score is

\[
q(\varnothing)=q(\{a\})=0,\qquad q(\{(b,x)\})=-x^2/4.
\]

The continuous selected fiber is exactly Gaussian with variance \(2/3\). Its
integrated weight is \(\sqrt{2/3}\), giving analytic empty/atomic/continuous
category masses. The envelope is \(U=0\); the ideal-real score is unbounded
below, and no represented-domain lower bound is certified. The sealed
known-law provider and independent tests now bind the real polynomial, exact
represented restriction, context, support, reference parameters, and upper
envelope. They keep the ideal-rational analytic law, stored-binary64 analytic
law, and runtime proposal law distinct. Development tests now carry this
provider through the common facade and kernel-v2 without inventing a lower
envelope.  Put \(t=w_0\).  CP53 independently encloses

\[
Z_1(t)=\frac{1+t+(1-t)\sqrt{2/3}}2,
\qquad
H_1(t)=\mathbb E[W^2]
=\frac{1+t+(1-t)\sqrt{1/2}}2,
\]

with \(\operatorname{Var}(W)=H_1-Z_1^2\).  It retains the paired
ideal-rational and stored-binary64 category tables, ideal acceptance
\(Z_1\), second moment, variance, and exact-IID SIR coefficient.  If
\(\epsilon=1/(5\,2^{53})\) is the stored type-weight perturbation, the exact
proposal-law TV is \(\epsilon/2\).  The full analytic target TV equals its
configuration-category TV because the conditional fiber laws are identical
on disjoint categories.  These are named analytic-law predictions, not
distributional validation of the runtime `T28-M1-Q` path.

### 4.3 Heterogeneous cap-two lane

`T28-M2-Q` uses the same separately bound ideal-rational and stored-binary64
reference parameters, cap two, and one- and two-dimensional Gaussian event
types. Its score is a frozen additive negative rational quadratic plus a
frozen rational count penalty. The sealed known-law provider and independent
tests bind its pointwise score semantics and exact upper envelope \(U=0\),
without a finite ideal-real lower bound. The coefficient \(1/6\) makes the
represented score generally non-dyadic, so CP50-v1's dyadic-only rejection
quota cannot accept this fixture. Kernel-v2 development tests now exercise
the separate arbitrary-rational quota on real non-dyadic `T28-M2-Q` score
gaps while preserving the absent lower envelope. This closes the local
adapter/quota/kernel integration prerequisite only.  Put

\[
r(t)=t\sqrt{2/3}+(1-t)\sqrt{3/5},\qquad
s(t)=t\sqrt{1/2}+(1-t)\sqrt{2/5}.
\]

CP53 independently encloses

\[
Z_2(t)=\frac25+\frac25r(t)+\frac15e^{-1/4}r(t)^2,
\qquad
H_2(t)=\frac25+\frac25s(t)+\frac15e^{-1/2}s(t)^2,
\]

and retains the paired configuration-category, count, event-type, variance,
and exact-IID SIR records.  Its exact proposal-law perturbation is
\((16/25)\epsilon-(1/5)\epsilon^2\), and full analytic target TV again equals
configuration-category TV because the conditional fiber laws match.  These
analytic Gaussian quantities remain separated from runtime sampling and do
not supply operational predictions.

CP54 also rederives the `T28-M2-Q` untilted base configuration-category law
from its primitive cap, activity, type weights, and complete count support by
both factorial routes above.  The ideal-rational record reproduces the six
declared base masses, while the stored-binary64 record is a distinct analytic
parameter companion whose exact TV from the rational base vector agrees with
the independently derived CP53 parameter perturbation.  This consistency does
not apply the quadratic score or identify an operational proposal law.

### 4.4 Stress and refusal lanes

`T28-AESS` is a finite all-atomic exact-rational stress oracle on the ordered
support

\[
(\varnothing,a,b,aa,ab,bb).
\]

Its factorially reconstructed base masses are

\[
\left(\frac25,\frac4{25},\frac6{25},\frac4{125},
\frac{12}{125},\frac9{125}\right),
\]

and its multiplicative factors are \((1,1,1,1,1,1024)\).  Thus the
unnormalized target masses are

\[
\left(\frac25,\frac4{25},\frac6{25},\frac4{125},
\frac{12}{125},\frac{9216}{125}\right),
\qquad Z=\frac{9332}{125},
\]

with exact target probabilities

\[
\left(\frac{25}{4666},\frac5{2333},\frac{15}{4666},
\frac1{2333},\frac3{2333},\frac{2304}{2333}\right).
\]

The sole diagnostic cloud is predeclared analytic input, not a sampled cloud:
for \(J=8\) its support indices are \((0,1,2,3,4,5,0,1)\), giving raw
weights \((1,1,1,1,1,1024,1,1)\), sum 1031, squared sum 1,048,583,
and

\[
\operatorname{ESS}=\frac{1{,}062{,}961}{1{,}048{,}583},
\qquad
\frac{\operatorname{ESS}}{J}=\frac{1{,}062{,}961}{8{,}388{,}664}<\frac14.
\]

The bound expectation is therefore a strict ESS warning at threshold
\(J/4=2\).  Its policy is report-only: the expected reported particle count
remains eight, the precommitted and post-warning strategy is fixed-budget SIR,
exactly one resampling draw is expected, and the warning is expected to add no
particle, draw, fallback, or cloud reuse.  These are oracle expectations, not
observations of production behavior.  The factors are deliberately not
represented as exponentials of an exact rational score, and this fixture is
not integrated with the score facade or initializer kernel.

`T28-INVALID` binds fourteen exact malformed-input expectations spanning five
oracle-model rows, two direct categorical-helper rows, two direct
score-provider input rows, and five production-kernel-preflight rows.  The
categories are negative, NaN, and positive-infinite factors; a false envelope;
zero or nonnormalized categorical mass; wrong dimension; noncanonical negative
zero; stochastic occurrence and coordinate work limits; count/type sampling
resolution; and the finite-atomic support limit.  Every row binds an exact
refusal code, validation boundary, exception class and message, applicable
strategies, zero owned RNG-factory calls for the proposal,
rejection-decision, and SIR-resampling roles, byte-identical externally
supplied sentinel-state digests, and no result artifact.  Every static row and
the table itself keep `production_boundary_verified_by_this_record=false`.
The hostile suite separately invokes the live production boundaries for the
count/type resolution and three resource-limit rows and checks the exact
lazy-imported exception identity.  A supplied-observation verifier proves only
that caller-supplied fields match the current hash-bound DRAFT expectation; it
does not verify boundary-invocation or RNG-digest provenance, authenticate
evidence, run the production runner, or support a confirmatory claim.

## 5. Budgets, streams, and execution shape

CP61 supersedes the earlier DRAFT fixed-hash/per-shard execution proposal for
the sixteen correlated whole-seed rows.  The active prospective design uses
rejection caps \(A\in\{1,4,16,64\}\), SIR budgets
\(J\in\{8,32,128,512\}\), exactly 2,048 retained external seed ordinals per
row, and 32,768 total scheduled requests.  The old eight-shard proposal and
its fixed per-shard counts remain historical DRAFT metadata only and are
inadmissible for CP61.  CP61 freezes no shard count, shard assignment, or
runner implementation.  A later runner may partition the fixed ordered work
only after its mapping and custody are separately frozen without changing the
seed ordinals, rows, outcomes, denominators, or total request count.  The
power review must still justify adequate selected counts and every primary
threshold.

For future ordinal \(i\), the external source supplies \(S_i\), and the runner
must pass that exact uint64 value unchanged as `plan_seed` for all sixteen
rows.  It must not derive a replacement seed from a study root, fixture,
strategy, shard, request index, or any other field.  The current kernel then
derives its proposal, rejection-decision, and SIR-resampling role streams from
that plan seed.  Proposal and rejection-decision derivations deliberately omit
the attempt or particle budget, so within one seed ordinal and fixed
fixture/strategy a smaller budget consumes an exact prefix of the larger
budget stream.  SIR-resampling additionally binds \(J\), because each particle
set has a separate one-draw categorical decision.  Rejection and SIR bind
distinct strategy fields and do not share proposal roots.  These internal
derived streams do not make the paired row outcomes independent.

The earlier domain-separated runner-plan-seed rule, four study roots, eight
shards, and CI/bootstrap derivation remain preserved in the manifest under
explicit `historical_pre_cp61_*` labels; none is an admissible CP61 seed source
or active runner specification.  CP61 freezes no replacement bootstrap or
shard rule.  Before this protocol can leave DRAFT status, the exact external
seed record, direct seed-to-`plan_seed` assignment, any later shard mapping,
raw/stable trace custody, byte order, NumPy version, Philox class, internal
kernel role derivation, draw chronology, and initial/final state digests must
be frozen and independently verified.

CP62 now freezes the exact seed-free contents of all sixteen requests, one
candidate runtime/source/ABI closure, the future seed-capsule shape, and the
fresh-process supervisor and raw/stable-record contracts.  Its four fixed
development calibration cases exercise only rows 4, 8, 12, and 16, with two
fresh children per case; they do not instantiate any of the 32,768 future
production requests or supply a shard mapping.  A production runner must still
bind all exact seed-valued request instances, implement the predeclared closed
refusal/failure classifications, freeze the production record schema, retain
the complete raw records, recompute stable projections and metrics
independently, and reproduce the runtime/source/ABI requirements under the
production launch path.  The calibration-only launch limit and case seeds are
not a production seed source, runner partition, retry allowance, or campaign
budget.

CP63 now exercises the same sixteen row definitions in a bounded development
rehearsal while preserving the production boundary.  The rehearsal fixes
`seed_ordinal=1`, `logical_request_ordinal=row_ordinal`, and the one
module-owned seed `12a5228200019dae`; its request-instance digest excludes the
volatile repetition number, so each row's two fresh launches must project to
the same stable bytes.  This does not synthesize a production bound request or
an external capsule.  The future parser and schedule remain syntax/definition
only, the production 32,768-request campaign is not exposed, and there is no
durable attempt writer or shard map.  Complete rehearsal raw frames retain
volatile supervisor custody separately; independent recomputation consumes
only the complete canonical stable projection and removes repetition rather
than inventing a replacement value.

The runner records the same 300-second deadline, two-second termination grace,
five-second reap ceiling, bounded request/raw/stderr frames, one fresh
spawn/exec process group per launch, and whole-attempt infrastructure
invalidation inherited from the CP62 development path.  These exercised
rehearsal semantics do not bind the future production supervisor or prove
infrastructure fidelity.  Likewise, the computed 512-GiB raw and 256-GiB
stable maxima are aggregate ceilings, not evidence that storage or throughput
has been provisioned.  A production runner must still bind the external
2,048-seed capsule, exact production runtime and source attestation, full
seed-valued request schedule, durable raw retention, shard/capacity receipts,
and complete independent interval/decision recomputation.

CP64 freezes a candidate production partition and receipt topology without
instantiating either.  Logical request ordinal $L$ maps to shard
\(\lfloor(L-1)/1024\rfloor+1\), so each of 32 shards contains the sixteen
rows for 64 consecutive seed ordinals.  This candidate supersedes neither the
seed-major CP61/CP63 schedule nor the requirement for a later selected,
attempt-bound shard-map receipt.  Before source contact, a later writer must
durably establish the acquisition journal and start receipt; before launch
authorization, it must establish the complete source/capsule cross-check,
production runtime match, disjoint 1-TiB destination and 32-GiB auxiliary
reservations, durability qualification, all fifteen summarized preflight
gates, and independent signoff.  CP64 performs none of those operations and
its candidate partition supplies no production capacity or custody evidence.

Before certification and before any plan-owned execution RNG or stream is
created, every stochastic plan must pass worst-case retained-work bounds

\[
A_{work}N_{cap}\le 500{,}000,
\qquad
A_{work}N_{cap}D_{max}\le 4{,}000{,}000,
\]

where \(A_{work}\) is the fixed rejection or SIR budget, \(N_{cap}\) is the
reference total cap, and \(D_{max}\) is the largest declared event dimension.
The exact constants must be imported from and bound to the certified reference
surface. Enumeration certification must execute the complete finite-support
oracle and refuse an oversized support before issuing a certificate. These
are worst-case retained-object limits, not expected-work statements.

CP57 fixes the stochastic preflight order.  After strategy-budget validation,
the occurrence and coordinate work limits are checked first.  Only if they
pass does the kernel rebuild the count categorical law from the public
reference parameters and require exact byte equality with the retained count
sampling CDF.  When the cap is positive it likewise rebuilds the type law from
the public retained type weights, checks sampling resolution, and requires
exact byte equality with the retained type CDF.  A zero cap skips the
irrelevant type gate; finite-atomic enumeration is exempt from both stochastic
sampling-resolution gates.  All of these stochastic refusals precede runtime
hashing and owned RNG construction.  The preflight tests certify deterministic
code paths only, not the probability law of a categorical transform.

No finite PRNG battery or deterministic replay certifies an exact continuous
Gaussian, uniform, iid, independent, or physically random source law. Those
are explicit premises of the generic/analytic theorem and of any claimed law
for \(\mu_{fp}\). Object custody and deterministic replay do not convert the
runtime sampler into the analytic \(\Pi_N\) measure.

## 6. Primary metrics and gates

The final gate family, familywise error rate, per-gate allocation, sample
sizes, and thresholds must be power-reviewed and frozen before `STARTED.json`
is created. Unused error slots are never reallocated.

Mandatory primary measurements are:

- exact equality or certified numerical bounds for finite-atomic enumeration;
- categorical total variation only on finite atomic/count/type marginals;
- rejection acceptance, exhaustion, and attempt-index frequencies against the
  frozen ideal and operational predictions, with simultaneous exact binomial
  intervals;
- conditional one-dimensional CDF discrepancies with simultaneous DKW bounds;
- the CP58 finite sign-closed bounded-feature configuration IPM, using only
  its frozen count, type, coordinate, and pair-interaction registries;
- SIR results for the complete frozen \(J\) sequence, including ESS, maximum
  normalized weight, weight entropy, perplexity, same-cloud local particle-slot
  ancestry, and separately labeled proposal-value uniqueness summaries; and
- valid-fixture operational refusal rate, which must be zero.

Sliced Wasserstein, energy distance, and block-bootstrap intervals may be
secondary diagnostics. A finite empirical measure is singular with respect to
an absolutely continuous target, so empirical continuous-space TV and KL are
forbidden labels and cannot be pass criteria.

## 7. Decision and no-exclusion rules

The historical v14 attempt graph retained in predecessor custody is

`FROZEN -> STARTED -> {PASS, FAIL, INVALID_PROTOCOL, ABORTED_INFRA, INCOMPLETE}`.

This DRAFT v15 sidecar proposes the additive lifecycle

`DRAFT_PRE_FREEZE -> FROZEN`,

`FROZEN -> {STARTED, INVALID_PROTOCOL, ABORTED_INFRA, INCOMPLETE}`, and

`STARTED -> {PASS, FAIL, INVALID_PROTOCOL, ABORTED_INFRA, INCOMPLETE}`.

The three direct `FROZEN` terminal arrows are a prospective v15 amendment,
not an interpretation of the v14 graph.  Preflight and authorization remain
artifact stages rather than lifecycle states.  The amendment is not
authoritative for production until the separate v15 protocol and manifest are
frozen and consumed by a later integration checkpoint.

Algorithmic exhaustion is retained in the outcome denominator and is never an
exclusion. A valid-fixture refusal, nonfinite primary metric, insufficient
selected count, missing shard, digest mismatch, missing expected artifact, or
material protocol deviation yields `FAIL` or `INVALID_PROTOCOL`; it does not
authorize top-up, replacement, or a changed seed.

No seed, budget, threshold, fixture, feature, projection, metric, gate order,
or environment may change after `STARTED.json`.  A pre-durable-output
infrastructure abort may receive a new attempt number only after written
independent adjudication and with identical frozen inputs.  Once the
acquisition start is durably committed, any source value has been returned, or
any other stochastic output is durable, the attempt is spent.  A returned
value lost before journal fsync is not claimed retained, but still forces an
`INCOMPLETE` terminal attempt with no resume, top-up, redraw, or reselection.
A failed v1 may motivate a separately named v2 but cannot be rewritten or
replaced.

## 8. Required evidence tree

Every attempt directory must contain byte-identical frozen inputs and complete
receipts for protocol, source, fixtures, environment, launch authorization,
start, shards, raw outputs, RNG states, metrics, decisions, deviations,
failures, exclusions, reruns, terminal state, and a complete SHA-256 manifest.
Independent verification must recompute every primary metric and decision from
hashed raw records using a separately implemented oracle path. Plots are
nonauthoritative and every plotted value must reference a hashed raw or metric
record.

Under the proposed v15 extension, the prestart evidence graph is an acyclic
twenty-node, forty-four-edge digest DAG with launch authorization as its only
sink.  The preflight summary aligns the first fifteen gate identifiers,
`PASS` states, evidence-node identifiers, and nonzero evidence digests;
independent signoff and explicit launch authorization remain separate gates
16 and 17.  The two durable outcome receipts, terminal record, manifest, and
`COMMITTED.json` must preserve every winning prestart branch and crash cut.
CP64 freezes this topology only; it supplies none of the future evidence.

## 9. Explicit nonclaims

Even a passing execution would not by itself certify:

- exact laws for NumPy, Philox, OS entropy, Gaussian transforms, categorical
  transforms, iid sequences, or independence;
- equality among the runtime finite-precision proposal law \(\mu_{fp}\), the
  analytic ideal-rational reference \(\Pi_N^{rat}\), and the analytic
  stored-binary64-parameter reference \(\Pi_N^{b64}\);
- a general or uniquely inferred real-fiber extension from represented
  scores. For `T28-M1-Q` and `T28-M2-Q` only, the backend declares a named
  polynomial \(\bar q_c\) and verifies its pointwise canonical-binary64
  restriction, and CP53 verifies fixture-specific normalizers and marginals
  for that named score under the two declared analytic references.  This does
  not establish a general or unique extension, any proposal-law equality,
  operational \(Z_{repr}\), or equality with a posterior or true conditional
  factor;
- residual-network forward-error or statistical approximation-error bounds;
- finite-\(J\) SIR equality with the normalized target;
- interpretation of the `T28-AESS` factors as exponentials of an exact
  rational score, interpretation of its predeclared diagnostic cloud as a
  sample, or interpretation of its expected warning policy as observed
  production behavior;
- production-boundary or RNG-state provenance from the static `T28-INVALID`
  table or its supplied-observation matcher.  The separate hostile tests are
  unit-test evidence only and do not authenticate a runner execution;
- a proposal, categorical, iid, independence, or target law from the CP57
  stochastic work, sampling-resolution, or retained-CDF custody preflights;
- a probability-law metric, target comparison, or observed output from the
  CP58 calibration IPMs.  They are exact finite-class pseudometric arithmetic
  over fixed supplied inputs, not empirical continuous-space TV, KL, or a
  sliced-Wasserstein registry;
- resampled ancestry from repeated configuration values, cross-request
  selected positions, or pooled cloud identifiers.  CP58 proposal-value
  uniqueness is separate from particle-slot ancestry, the current per-request
  selected-ancestor count is one by construction, and the `T28-AESS` \(R=8\)
  occupancy record is a conditional zero-draw analytic counterfactual;
- an operational source or target law from CP59's predeclared arithmetic.
  Its supplied SIR clouds have unverified configuration and result-digest
  provenance; its finite rejection tables assume rather than verify iid
  proposals, uniform decision words, and independence; and its observed
  NumPy version/runtime digest is not a compiled-transform-law attestation;
- a product-uniform role-stream model for the current one-uint64-seed source
  surface.  Its support obstruction requires a richer external source API or
  a correlated whole-seed pushforward analysis, and the source-level TV lower
  bound does not imply an output-level TV lower bound;
- an operational probability from CP60's symbolic seed-fiber definitions.
  The uniform plan seed is an explicit one-request assumption only; the
  current fixed-hash plan does not realize or sample it, the sixteen grid rows
  are prospective request templates, no complete request/runtime map is
  instantiated, and no numeric fiber count is computed;
- a common \(\mu_{fp}\), proposal iid, cross-request iid, derived-word
  uniformity, role-stream independence, \(\alpha_{64}\)/\(\rho_{64}\) product
  formula, proved execution totality, or zero nonreturn mass from CP60.  Its
  file/runtime digests are unverified custody labels and its Monte Carlo
  requirements are future gates rather than completed evidence;
- any observed estimate, interval, operational probability, selected-count
  assurance, power guarantee, full stable trace law, or total-variation result
  from CP61.  Its 2,048 external seed ordinals, sixteen rows, 554 estimands,
  deadline classifier, stable projection, simultaneous uncertainty, and work
  counts are prospective design fields only; no source, request, runtime,
  supervisor, sample, trace, or execution is bound or observed;
- source-law evidence from CP61's requirement of iid uniform uint64 sampling
  with replacement.  The current fixed-hash seed plan is explicitly not that
  sample; duplicate retention and same-ordinal cross-row pairing do not imply
  cross-row independence; timeout censoring is not CP60 semantic nonreturn;
  and the infrastructure-invalidation rule has not been exercised;
- a complete continuous trace-law or TV estimate from CP61's 554 finite
  estimand projections.  CP62 instantiates the required stable semantic
  projection only for four fixed calibration cases and observes their
  two-process parity; that bounded calibration does not instantiate a
  production sample, estimate its law, or replace the separately retained raw
  trace;
- production seed or request custody from CP62's seed-free bindings and empty
  future seed-capsule schema.  Its four fixed calibration seeds are not
  external-source draws or future capsule members, its caller cannot supply an
  arbitrary seed, and no production seed ingest or campaign loop is exposed;
- production runner completeness from CP62's fresh-process calibration
  supervisor.  Closed refusal and failure record shapes are predeclared, but
  their calibration-runner classification is unimplemented, the production
  schema is not frozen, and no production supervisor, runner, shard mapping,
  infrastructure-fidelity receipt, capacity receipt, request, metric, or
  decision record is bound;
- a portable runtime or transform-law theorem from CP62's candidate lock and
  calibration parity.  The parity receipts cover exactly four fixed
  deterministic cases in the bound candidate environment, while production
  runtime matching and production cross-process parity remain false;
- external-seed or production-request custody from CP63's future capsule
  parser and logical schedule definition.  The parser verifies only canonical
  syntax and digests, the fixed rehearsal seed is not a source draw or capsule
  member, and the 32,768-request schedule is not instantiated;
- production runner completeness from CP63's all-row rehearsal.  Its sixteen
  case identifiers, two launches per row, complete raw/stable records, and
  stable pair parity are bounded development evidence; no arbitrary-seed API,
  production campaign, durable writer, shard map, durable production sample,
  or frozen production schema is exposed;
- a production estimate, interval, or decision from CP63's independent
  554-estimand rehearsal receipt.  Independent parsing and repetition-blind
  equality establish only deterministic custody for the sixteen development
  stable traces, not the N=2,048 sample or its law;
- allocated production capacity, a portable runtime theorem, or executed-code
  attestation from CP63.  The 512/256-GiB values are arithmetic ceilings, the
  CP62 runtime candidate is reused conditionally rather than fully recomputed
  and production-matched, and pre/post source-file hashes do not attest loaded
  bytecode;
- an external-source sample or source law from CP64's acquisition schemas.
  The journal, start/partial/completed receipt shapes, sequence commitments,
  and no-retry rules contain no seed value, source contact, authority
  verification, or iid-uniform evidence, and CP64 creates none of those
  artifacts;
- allocated capacity or durable-writer qualification from CP64's arithmetic
  floors and path inventory.  The candidate 1-TiB destination plus 32-GiB
  auxiliary reservations are absent, the bounded auxiliary-size proof is
  absent, no filesystem is observed, and no partial inode or publication
  boundary is created;
- a selected production shard map, materialized request, complete runtime
  match, or production runner from CP64.  Its 32-shard partition is a frozen
  candidate definition only, while every attempt-bound shard record,
  per-file reservation link, runtime receipt, and production API remains
  absent;
- freeze, signoff, authorization, start, or blocker closure from CP64's
  proposed lifecycle and seventeen-gate inventory.  The v15 paths are neither
  consumed nor authoritative at bundle construction, every gate is
  `MISSING`, and neither outcome receipt nor any terminal or committed attempt
  exists;
- equality between the CP55 `T28-A0-Q` analytic interval target and the CP56
  kernel-v2 float64 finite-atomic categorical-weight record. CP56 binds their
  nonzero half-L1 discrepancy interval, but the exact float64 output sum is
  not one, so this is neither total variation nor an operational categorical
  law;
- empirical TV or KL on positive-dimensional fibers;
- adaptive retry, adaptive particle counts, shared-cloud output independence,
  or liveness outside frozen resource bounds;
- CP40/CP49 source-law equivalence;
- Brownian lineage, path construction, downstream sampler correctness;
- real-domain validity, learned-model quality, cross-domain generality, or a
  manuscript result.

The manuscript files remain frozen while this protocol is DRAFT. Any later
claim promotion requires a terminalized execution, independent verification,
and a separate strict review of the exact evidence bundle.

## 10. Current DRAFT state and blockers

At the time of this draft, no confirmatory execution is authorized.

### 10.1 Completed CP52--CP64 nonconfirmatory prerequisites

The immutable v14 machine-readable DRAFT manifest remains the predecessor
digest authority for the completed CP52--CP63 source-and-test surfaces.  The
separate v15 DRAFT manifest binds this protocol sidecar and the additive CP64
source/test evidence.  Neither sidecar is a freeze receipt, and neither was
consumed by the already immutable CP64 bundle.  Any byte change requires
renewed testing and a new manifest binding before freeze review.

The bound implementation/test pairs are
`src/heterodiff/processes/certified_initial_score_provider_v1.py` with
`tests/unit/test_certified_initial_score_provider_v1.py`,
`src/heterodiff/processes/arbitrary_rational_uint64_exp_quota.py` with
`tests/unit/test_arbitrary_rational_uint64_exp_quota.py`, and
`src/heterodiff/processes/plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2.py`
with
`tests/unit/test_plugin_bridge_mixed_support_initial_tilt_initializer_kernel_v2.py`,
and
`src/heterodiff/evaluation/mixed_initializer_test28_predictions.py` with
`tests/unit/test_mixed_initializer_test28_predictions.py`, and
`src/heterodiff/evaluation/mixed_initializer_test28_factorial_derivation.py`
with
`tests/unit/test_mixed_initializer_test28_factorial_derivation.py`, and
`src/heterodiff/evaluation/mixed_initializer_test28_atomic_q_oracle.py` with
`tests/unit/test_mixed_initializer_test28_atomic_q_oracle.py`, and
`src/heterodiff/evaluation/mixed_initializer_test28_atomic_q_operational_comparison.py`
with
`tests/unit/test_mixed_initializer_test28_atomic_q_operational_comparison.py`,
and
`src/heterodiff/evaluation/mixed_initializer_test28_stress_refusal_oracle.py`
with
`tests/unit/test_mixed_initializer_test28_stress_refusal_oracle.py`, and
`src/heterodiff/evaluation/mixed_initializer_test28_bounded_sir_diagnostics.py`
with
`tests/unit/test_mixed_initializer_test28_bounded_sir_diagnostics.py`, and
`src/heterodiff/evaluation/mixed_initializer_test28_runtime_conditional_predictions.py`
with
`tests/unit/test_mixed_initializer_test28_runtime_conditional_predictions.py`,
and
`src/heterodiff/evaluation/mixed_initializer_test28_uniform_seed_pushforward.py`
with
`tests/unit/test_mixed_initializer_test28_uniform_seed_pushforward.py`, and
`src/heterodiff/evaluation/mixed_initializer_test28_whole_seed_mc_design.py`
with
`tests/unit/test_mixed_initializer_test28_whole_seed_mc_design.py`, and
`src/heterodiff/evaluation/mixed_initializer_test28_execution_capsule.py`
with
`tests/unit/test_mixed_initializer_test28_execution_capsule.py`, and
`src/heterodiff/evaluation/mixed_initializer_test28_runner_recomputation_rehearsal.py`
with
`tests/unit/test_mixed_initializer_test28_runner_recomputation_rehearsal.py`,
and
`src/heterodiff/evaluation/mixed_initializer_test28_independent_recomputation.py`
with
`tests/unit/test_mixed_initializer_test28_independent_recomputation.py`, and
`src/heterodiff/evaluation/mixed_initializer_test28_production_custody_preflight.py`
with
`tests/unit/test_mixed_initializer_test28_production_custody_preflight.py`.
The exact CP64 source binding is SHA-256
`d35cbacb84e3348ae10549e053a0bb1572569583cdd03e66119353af4148bec2`
over 109,716 bytes and 2,409 LF-terminated lines.  The exact CP64 test binding
is SHA-256
`5e2d3a4ee4803556812983a01506e1f0b146c62ac2e2017c98914474a799fca4`
over 125,001 bytes and 2,944 LF-terminated lines.
The
manifest also
binds the lazy `src/heterodiff/evaluation/__init__.py` package surface that
exposes CP53 without eagerly importing NumPy or SciPy while preserving the
legacy evaluation exports.

- The sealed, torch-lazy certified score-provider facade presents one exact
  represented-score contract with an exact upper envelope \(U\), an optional
  exact lower envelope \(L\), explicit context policy, retained source record,
  and bounded structural validation. Its separate adapters cover the CP30
  learned composer, the exact rational known-law provider, and the CP55
  count-keyed atomic score-table provider. Import or use of either exact
  adapter does not import PyTorch; structural validation does not replay a
  learned forward pass or consume RNG. The atomic adapter's structural
  validation inspects its retained CP55 evaluation records without calling
  the source provider's `evaluate` method.
- The arbitrary-rational uint64 quota certifies
  \(\lfloor2^{64}e^\Delta\rfloor\) for admitted exact rational
  \(\Delta\le0\), using exact rational terminal branches or adaptive outward
  enclosures under the recorded trusted Python `Decimal`/libmpdec contract.
  Ambiguity, runtime mismatch, and resource exhaustion fail closed. This is
  neither formal libmpdec verification, a portable cross-runtime theorem, nor
  an exact exponential Bernoulli sampler.
- Kernel-v2 consumes only the common certified facade and implements
  precommitted finite-atomic enumeration, fixed-attempt rejection, and
  fixed-particle SIR. It retains \(U\) and optional \(L\), but no strategy
  requires \(L\). It binds bounded work and strategy/role-separated streams,
  embeds and validates arbitrary-rational quota certificates, and offers
  structural result validation without replaying provider evaluation, the
  proposal sampler, or RNG.
- Hostile and integration tests exercise all three facade backends, sealed records,
  tamper/refusal paths, torch-lazy exact use, non-dyadic `T28-M2-Q` rejection
  gaps, and `T28-M1-Q`/`T28-M2-Q` development paths. They also exercise CP30
  finite-atomic enumeration against the reference oracle surface. These are
  deterministic implementation tests only, not fixture predictions,
  distributional evidence, source-law evidence, or a Formal Test 28 run.
- CP52 is additive. The audited CP50-v1 initializer remains unchanged,
  byte-frozen, and not type-compatible with the exact known-law provider;
  kernel-v2 neither imports it nor converts the exact provider into its CP30
  composer type.
- The CP53 oracle is stdlib-only and uses exact `Fraction` endpoints,
  256-bit integer-isqrt brackets, and alternating rational Taylor bounds.  It
  binds paired M1/M2 analytic normalizers, category/count/type tables,
  acceptance, second moments, variances, exact-IID SIR coefficients, and the
  exact rational-versus-binary64 proposal/target perturbations.  Its
  conditional \(A\)- and \(J\)-indexed theorem records keep every operational,
  source-law, confirmatory, and manuscript flag false.
- The CP54 oracle is stdlib-only and accepts no base-mass vector.  From the
  primitive activity, cap, type weights, and complete ordered count support it
  independently reconstructs every `T28-A0-H` and `T28-M2-Q` base mass by a
  product-factorial route and a count-times-multinomial route.  It binds the
  ideal-rational and stored-binary64 analytic parameter layers separately and
  keeps every operational, target-tilt, source-law, confirmatory, and
  manuscript flag false.
- The CP55 oracle is stdlib-only and accepts no injected base masses,
  exponentials, normalizer, or probabilities. It binds the direct exact
  `T28-A0-Q` score table, exact envelope, factorial base reconstruction,
  count-keyed runtime permutation, paired ideal-rational and stored-binary64
  analytic interval targets, direct and envelope-shifted derivations, and the
  binary64-minus-ideal perturbation. Its sealed table provider remains an
  analytic prerequisite whose own immutable record contains no common-facade
  adapter, kernel-v2 integration, categorical comparison, source-law evidence,
  confirmatory evidence, or manuscript claim; CP56 binds the separate
  integration layer described next.
- The CP56 comparison takes the exact CP55 oracle/provider pair, the third
  common-facade adapter, and an already executed generic kernel-v2 enumeration.
  It verifies the runtime-to-protocol permutation \((0,2,1,5,4,3)\) by count
  key, binds the exact binary64 base/output vectors and their hashes, records
  the output-sum residual \(-2^{-57}\), and encloses the output-minus-analytic
  half-L1 discrepancy. Structural comparison validation does not execute the
  kernel, replay provider evaluation, sample the reference, consume RNG, or
  run a learned model. It executes no categorical draw and makes no source-law,
  exact-target-equality, confirmatory, Formal Test 28, or manuscript claim.
- The CP57 stress/refusal oracle has a stdlib-only top-level import and
  oracle/table-construction path; explicit observed-production-exception
  verification lazily imports its exact class.  It binds the exact
  `T28-AESS` rational target,
  its one predeclared \(J=8\) ESS diagnostic and report-only expected policy,
  and all fourteen `T28-INVALID` expectation rows under one independently
  digested bundle.  Its observation verifier is comparison-only and leaves
  provenance, authentication, production-runner, confirmatory, Formal Test 28,
  and manuscript flags false.
- CP57 kernel-v2 stochastic preflight hardening checks work limits before
  categorical resolution, reconstructs the count and retained type laws from
  public parameters, verifies retained CDF byte custody, preserves the cap-zero
  and enumeration exemptions, and refuses before runtime hashing or RNG
  construction.  The five production-preflight cases are executed by separate
  hostile tests; the static table does not claim to have invoked them.
- The CP58 diagnostic artifact is stdlib-only, sealed, resource-bounded, and
  exact after converting canonical binary64 coordinates to rational values.
  It binds the complete six-feature M1 and thirty-three-feature M2 registries,
  all six rational projections, two predeclared evaluator calibrations,
  proposal-value uniqueness, the one-selection same-cloud ancestor contract,
  and the conditional zero-draw `T28-AESS` \(R=J=8\) particle-slot occupancy
  calculation.  Its tests independently enumerate feature IDs and projection
  coefficients, rederive every calibration mean and occupancy expression, and
  exercise cross-cloud, tamper, type, coordinate, resource, import, and claim-
  scope refusals.  Neither the artifact nor its tests observe production,
  authenticate a source, compare a sample with a target, or close a gate.
- The CP59 artifact is sealed and stdlib-only at import.  Its explicit SIR
  builder lazily imports NumPy, independently reproduces the frozen kernel-v2
  binary64 normalization expression, requires the supplied built-in-float
  vector to match byte for byte, forms the sequential CDF with final one, and
  exactly counts all right-sided \(2^{53}\)-grid cells.  Its finite-law
  rejection builder uses the hash-bound CP52 quota dependency to derive exact
  atom quotas and the complete \(A\in\{1,4,16,64\}\) first-acceptance and
  exhaustion grids under explicitly assumed abstract finite-law premises.
  The trusted Decimal/libmpdec contract remains formally unverified.  The
  zero-argument bundle is predeclared arithmetic only: no sampler, kernel
  owner/plan, kernel normalization helper, or RNG executes, and it makes no
  source-law, iid, independence, operational, confirmatory, Formal Test 28, or
  manuscript claim.
- CP59 also binds the current source-surface obstruction: one uniform 64-bit
  plan seed has joint-trace support at most \(2^{64}\), so it cannot realize a
  two-word product-uniform law of support \(2^{128}\).  This makes a richer
  external source API or a correlated whole-seed pushforward analysis a
  necessary future design choice; deterministic replay is not source-law
  evidence, and the support-level TV bound does not furnish an output-law
  lower bound.
- CP60 selects the correlated whole-request design and binds a sealed,
  stdlib-only, definition-only artifact.  Under one expressly assumed uniform
  uint64 plan seed for one future fully fixed request/runtime, it defines a
  six-tag totalized outcome alphabet and exact fiber-count formulas for every
  status, atom, rejection first-acceptance and exhaustion event, SIR selected
  value, no-returned-output event, joint realized proposal trace, and reached
  slot sublaw.  It also records the fixed-seed point-mass theorem.  It neither
  executes nor imports the kernel, NumPy, SciPy, provider, or RNG.
- The CP60 bundle binds sixteen prospective templates: M1 then M2; within each,
  rejection budgets \(1,4,16,64\) followed by SIR budgets
  \(8,32,128,512\).  Every request/runtime binding and every numeric status,
  selection, refusal, failure, exhaustion, and nonreturn count remains absent.
  The source and optional runtime digests do not attest a compiled runtime;
  the dependency-lock/runtime fields are absent, totality and zero nonreturn
  mass are unproved, validated Monte Carlo has not run, and every operational,
  production, confirmatory, Test-28-closure, and manuscript flag remains false.
  The artifact requires correlated whole-request predictions and does not
  identify a common \(\mu_{fp}\) or permit iid, role-independence, or
  \(\alpha_{64}\)/\(\rho_{64}\) product formulas.
- The CP61 artifact is a sealed, stdlib-only, zero-execution prospective
  validated-Monte-Carlo design.  It binds all sixteen CP60 rows, the complete
  2,048-ordinal with-replacement seed schedule, all 554 estimands and their
  compact semantic digests, every row's complete CP58 feature inventory, the
  300-second deadline classifier, the full stable-trace projection contract,
  and the exact planned resource budget.  Its builder neither imports nor
  loads CP58 or CP60; hostile tests independently compare the hard-coded
  predecessor sources, bundles, rows, registries, feature definitions, and
  ranges with the live hash-bound artifacts.
- CP61 assigns familywise error \(1/100\), per-estimator error
  \(1/55{,}400\), and per-tail error \(1/110{,}800\).  It freezes exact
  outward 256-step Clopper--Pearson bisection for the 242 binomial estimands
  and a minimum selected count 1,040 with half-width \(3/40\) of range for
  the 312 bounded-feature means.  Its exact Taylor/Hoeffding certificate and
  union bound are design arithmetic only.  The future \(n=2048\) intervals
  are uncomputed, and no selected-count or power guarantee is claimed.
- CP61 retains duplicate seed values, pairs rows by seed ordinal without
  assuming cross-row independence, forbids retry/drop/replacement/top-up,
  keeps timeout censoring distinct from CP60 semantic nonreturn, and makes any
  infrastructure failure invalidate the whole attempt.  Every live request,
  runtime, source, supervisor, infrastructure-fidelity, sample, execution,
  estimate, interval, operational, power, confirmatory, manuscript, and
  Test-28-closure field remains absent or false.
- CP62 is sealed and stdlib-only at import.  It hash-binds the exact sixteen
  seed-free request records, one runtime/source/ABI candidate, the uninstantiated
  future seed-capsule contract, a fresh-process deadline supervisor, and
  separate raw-record and stable-projection schemas.  The stable projection
  recomputes its owned semantic leaf hashes, excludes volatile custody, and
  never replaces the separately retained raw trace.
- CP62's only executable entry point admits four fixed module-owned
  development cases: M1/M2 (A=64) rejection and M1/M2 (J=512) SIR.  Each
  runs in two fresh children, for eight launches total.  Stable projections
  match across the two executions of every case.  The four case seeds are not
  CP61 external-source draws, and raw custody fields are allowed to differ.
  Production seed ingest, arbitrary-seed execution, and a production campaign
  remain unavailable.
- CP62 predeclares production refusal/failure record shapes but does not
  implement their calibration-runner classification or freeze the production
  schema.  It binds no production source, seed capsule, runtime match,
  supervisor, runner, shard mapping, request, metric, interval, operational
  prediction, power guarantee, confirmatory evidence, manuscript promotion,
  or Test 28 closure.
- CP63's runner surface is sealed and stdlib-only at import.  It freezes the
  future capsule syntax, exact seed-major logical order and arithmetic resource
  maxima, and all sixteen development rehearsal cases.  The all-row fixture
  executes each case twice in a fresh child under one fixed module-owned seed;
  complete raw records retain repetition and volatile supervisor custody while
  stable projection removes exactly those nonsemantic fields.
- CP63's independent surface imports neither the runner nor CP62, the kernel,
  NumPy, or SciPy.  It independently parses the complete stable bytes,
  enumerates all 554 ordered CP61 estimands, emits sixteen compact observations,
  and reproduces one repetition-blind receipt identically from both runs.  The
  manifest retains the exact runner and independent bundles, component and
  case receipts, full estimand inventories, sixteen stable/compact pins, and
  complete final acceptance receipt.
- CP63 remains development-only.  Its future capsule is syntax-only, the
  32,768-request schedule is uninstantiated, the fixed rehearsal seed has no
  external provenance, the reused CP62 runtime candidate is conditional, and
  file-byte hashes are not executed-code attestation.  No production campaign,
  durable writer, shard map, capacity receipt, durable production raw sample,
  estimate, interval, decision, production-schema freeze, runner-blocker
  closure, confirmatory evidence, manuscript promotion, or Test 28 closure is
  claimed.
- CP64 is sealed, stdlib-only at import, deterministic, and zero-execution.  It
  binds the immutable v14 predecessor custody, CP61--CP63 semantic digests,
  exact dependency lock, and future external-source, runtime, capacity,
  durability, shard-map, launch-authorization, and gate contracts.  Its
  builder performs no filesystem, runtime, source, process, network, clock,
  entropy, or RNG observation and imports no project module.
- CP64 freezes a 2,048-entry chained seed-acquisition journal contract, a
  no-resume spent-attempt rule, a 1-TiB destination plus conservative 32-GiB
  auxiliary reservation predicate, and one contiguous 32-shard candidate
  partition with four reserved destination files per shard.  These are future
  schemas and arithmetic definitions only: no seed, source authority,
  runtime match, capacity receipt, reservation, filesystem qualification,
  shard map, or durable output exists.
- CP64 predeclares two exclusive durable outcome selections, the proposed v15
  prestart terminal transitions, a twenty-node, forty-four-edge digest DAG,
  and seventeen ordered production gates.  The first fifteen gates would be
  summarized before independent signoff and authorization.  At construction,
  the v15 paths are unavailable/unconsumed, the lifecycle is nonauthoritative,
  every gate is `MISSING`, and all production, execution, estimate, interval,
  decision, confirmatory, manuscript, and Test-28-closure flags remain false.
- The current CP58 bounded-feature/SIR-diagnostic pair passes 81/81 focused
  hostile tests.  The CP57 stress/refusal pair passes 41/41 focused tests, and
  the current kernel-v2 regression passes 28/28 tests.  The prior ten-suite
  CP50--CP56 and eleven-suite CP50--CP57 aggregates remain historical 483/483
  and 524/524 records.  The manifest separately binds the historical twelve-suite
  CP50--CP58 aggregate at 605/605 tests passed with warnings treated as errors.
  It records exact commands, timings, and generation-appropriate hashes; prior
  records retain their historical facade or kernel-v2 hashes and are not
  rewritten as current-binding evidence.
- The CP59 runtime-conditional arithmetic pair passes 70/70 focused hostile,
  independent-math, normalization-parity, resource, type-sealing, digest,
  import, and nonclaim tests.  The manifest binds its source, tests, bundle,
  boundary, two SIR tables, and eight finite rejection records separately.
  The historical thirteen-suite aggregate passes 675/675 tests with warnings
  treated as errors and is recorded separately in the manifest; every earlier
  aggregate remains immutable historical evidence.
- The CP60 whole-seed definition pair passes 52/52 focused hostile,
  independent-math, totalization, correlated-source, variable-word-
  consumption, resource, type-sealing, digest, import, and nonclaim tests.
  The historical fourteen-suite aggregate passes 727/727 tests with warnings
  treated as errors.  The manifest records the exact focused and aggregate
  commands, timings, then-current source/test hashes, bundle and canonical-bundle
  digests, outcome-alphabet digest, and all sixteen child-definition digests;
  historical verification records remain unchanged.
- The CP61 prospective whole-seed validated-Monte-Carlo design pair passes
  40/40 focused hostile, independent-inventory, complete-estimand,
  multiplicity, exact-interval-calibration, Taylor/Hoeffding, resource,
  projection, deadline, infrastructure, seal, digest, import, tamper, and
  nonclaim tests.  The manifest serializes the exact complete CP61 bundle and
  records its source/test hashes, canonical byte count and digest, stable
  design semantic digest, bundle digest, projection digest, multiplicity
  digest, resource digest, focused command, and timing.  The historical
  fifteen-suite aggregate passes 767/767 tests with warnings treated as
  errors; its exact command, timing, and all 31 then-current non-protocol source and
  test bindings are recorded separately.  Every prior focused and aggregate
  verification record remains immutable historical evidence.
- The CP62 calibration-only execution-capsule pair passes 148/148 focused
  hostile, exact-binding, runtime/source/ABI, seed-capsule, supervisor,
  raw/stable-schema, fresh-child execution, cross-process parity, timeout,
  resource, import, seal, digest, tamper, and nonclaim tests with warnings
  treated as errors.  The authoritative acceptance replay took 190.38 seconds
  of pytest time.  The manifest binds the exact source/test hashes, bundle and
  semantic digests, canonical bundle byte count and digest, child-contract and
  calibration-case digests, four stable-trace digests and canonical byte
  counts, and the exact focused command and timing.  The historical sixteen-suite
  aggregate passes 915/915 tests with warnings treated as errors; its exact
  command, timing, and all 33 current non-protocol source and test bindings are
  recorded separately without rewriting any historical verification record.
  This is calibration-only development verification, not a production or
  confirmatory run.
- The CP63 runner and independent-recomputation pairs pass 151/151 focused
  tests with warnings treated as errors.  The retained acceptance executes all
  sixteen fixed rehearsal rows twice, validates 32 raw records, confirms
  within-row stable parity, independently reproduces every stable/compact pin,
  and obtains identical repetition-blind 554-estimand receipts.  Pytest time
  was 281.71 seconds (real 281.95, user 272.32, sys 5.29 seconds).  The
  manifest retains the complete 24,810-byte acceptance receipt, its
  domain-separated digest, the sixteen-launch semantic-pin receipt, the exact
  bundles and ordered inventories, output-file custody, command, and timing.
  This is development rehearsal evidence only.
- The CP64 production-custody-preflight pair passes 145/145 focused hostile,
  predecessor-custody, journal, runtime, capacity, path-closure, durable-CAS,
  shard, lifecycle, gate, digest-DAG, canonicalization, sealing, tamper,
  cross-version, concurrency, import, and nonclaim tests with warnings treated
  as errors.  Pytest time was 4.13 seconds (real 4.27, user 4.16, sys 0.07
  seconds).  Its exact 77,595-byte canonical bundle has plain SHA-256
  `31c1ff133f9dc6c3f9a5810359bd313f5fe5f46cb5e2bd6801b8dac0e241ae23`,
  record digest
  `32f7f0c62019d8ee906e6f74300f6c33fbe55984f69cfe4fe1061ffb92463f39`,
  and public tagged digest
  `caecd8630def94f7ac6da721422e3d9d71c26c351e753369abf17b224a90de83`.
  The predecessor, external-source, runtime, capacity, durability, shard-policy,
  production-shard-map, launch-authorization, and no-execution-gate component
  record digests are respectively
  `b3a6f04387a93eff4a327c8b8d9bf6951e13ce9a2dc8c7924bea8bd213398c4d`,
  `03d29e3d8514ef7d7c0930620e23b4e35f52a7dd5b0c77955e89e62bf438a0fa`,
  `0a347ca445aa300cdfa67204d01e81194783fc625c47b3974c8055c6782f1c3c`,
  `968108bda050687408fe989186aff3137560b827d1c83622f685a597d208ecfe`,
  `aced3702d8f1cbb240de9c41c6f97581a5ce019045e3300cc485bcb6328e76c2`,
  `8623c092772eaa0e40066d7e423967095e86491c01d869aa824c81fa9ee4b4ea`,
  `288bb8d9ff9970d7e6fedf8e78f50d91fbd83e0e2c700ae195b9615d03678196`,
  `0c60d5484e0efb50991a95fa7da4b191dae7c48f25568f24207e594132ac17b5`,
  and
  `7ceb4f12ce712e7123509eb6380e134876855bb91e90c64a951f7e1bcbcb2633`.
  The candidate shard-1 record digest is
  `8e298aad172c3ad1c09c4f5790c224ee25cd4ae6394a7ecdedd19a7de6db8d93`.
  This is definition-only development verification, not a production or
  confirmatory run.
- The historical eighteen-suite CP50--CP63 aggregate passes 1,066/1,066 tests
  with warnings treated as errors and no warning, error, or failure output.
  Pytest time was 972.67 seconds (real 973.37, user 951.79, sys 10.85
  seconds).  The manifest records the exact approved command and all 37
  non-protocol binding hashes without modifying any of the 33 historical
  verification records that preceded CP63.
- The current nineteen-suite CP50--CP64 aggregate passes 1,211/1,211 tests
  with warnings treated as errors and no warning, error, or failure output.
  Pytest time was 932.79 seconds (real 933.20, user 923.44, sys 6.18
  seconds).  This aggregate adds only the exact CP64 pair to the historical
  CP50--CP63 suite set and does not rewrite any prior verification record.

These completed prerequisites do not authorize production or confirmatory
execution, close any primary gate, identify either analytic target with the
operational target, establish
live \(p_{64}\), \(\alpha_{64}\), \(\rho_{64}\), or operational SIR, or
support a manuscript claim. Formal Test 28 remains **OPEN**.

### 10.2 Remaining blockers before freeze review

The DRAFT blocker ledger now contains nineteen entries: fifteen satisfied by
hash-bound nonconfirmatory artifacts and four still missing. CP60 satisfies
the symbolic `whole_seed_pushforward_definition` prerequisite, and CP61
satisfies the prospective `whole_seed_validated_mc_design` prerequisite. CP62
satisfies the calibration-only `whole_seed_execution_capsule_and_calibration`
prerequisite. CP63 satisfies the development-only
`whole_seed_runner_recomputation_rehearsal` prerequisite. CP62 and CP63 are
completed precursors to `runner_and_recomputation`; neither closes that runner
blocker or `unconditional_operational_predictions`.  CP64 satisfies the new
definition-only
`whole_seed_production_custody_preflight_scaffold_definition` prerequisite,
but closes none of the same four missing blockers.  The missing set is
unchanged.
Before a freeze review, the following missing items must all be present and
hash-bound:

- unconditional operational predictions under the selected correlated model:
  fully instantiate every request parameter and the complete compiled runtime
  map; bind the external supervisor and implement the full stable/raw trace
  custody contract; realize and verify CP61's external iid uniform
  uint64-with-replacement seed source; retain the complete seed and trace
  sample without retry, drop, replacement, or top-up; execute all 32,768
  scheduled requests under the frozen deadline and infrastructure-fidelity
  rules; and compute and independently reproduce all 554 estimates and
  applicable intervals.  A common \(\mu_{fp}\), proposal iid, derived-word
  uniformity, role independence, and \(\alpha_{64}\)/\(\rho_{64}\) product
  formulas are not required by this chosen within-request model and must not be
  asserted.  Same-ordinal cross-row outcomes are paired and are not assumed
  independent.  CP62's seed-free grid, empty seed schema, candidate runtime,
  and four deterministic parity calibrations are completed precursors, but do
  not satisfy any of these sample, campaign, estimate, or interval steps.
  CP63's syntax-only capsule parser, uninstantiated schedule, fixed-seed
  sixteen-row rehearsal, stable pair parity, and repetition-blind independent
  554-estimand receipt are also completed precursors only: they bind no
  external seed values or source law, production runtime, full 32,768-request
  sample, estimate, interval, or decision.  CP64 adds the spent-attempt
  acquisition journal and source/capsule cross-check schemas, but contains no
  source values or authority, materialized schedule, campaign, estimate,
  interval, or decision;
- the execution runner, source/fixture/seed manifests, exact dependency lock,
  complete runtime recorder, raw-record schema, and independent metric and
  decision recomputation path.  CP62 binds a candidate lock, supervisor and
  raw/stable schemas, and fixed calibration path, but a production seed ingest,
  campaign loop, closed refusal/failure classifier, frozen production schema,
  capacity receipt, production runtime match, runner/shard mapping, and
  independent metric/decision recomputation remain absent.  CP63 exercises
  all rows and independently recomputes the rehearsal receipt, but its external
  capsule is absent, production execution APIs remain mechanically unavailable,
  the CP62 runtime lock is only conditionally reused, source-file custody is
  not executed-code attestation, and no campaign, durable writer, shard map,
  capacity receipt, durable production raw retention, full recomputation,
  estimate, interval, or decision is bound.  CP64 adds candidate shard,
  runtime-receipt, reservation, durable-writer, classifier, and independent-
  recomputation qualification schemas, but implements, qualifies, selects,
  materializes, or observes none of them;
- a completed power review, exact frozen primary thresholds, and adequate
  selected-count justification for every one of the 32 gate slots.  CP64
  names the power-threshold receipt and gate but supplies neither artifact;
  and
- complete confirmatory custody: sidecar protocol digest, freeze receipt,
  independent reviewer signoffs, attempt/exclusion/deviation/terminal receipt
  machinery, and explicit launch authorization.  CP64's proposed lifecycle,
  path inventory, two-stage outcome selection, publication order, digest DAG,
  and authorization schema are definition-only; v15 sidecar freeze and later
  bound consumption, complete schemas and digest preimages, the signature
  preimage and verifier, receipts, signoffs, authorization, start, and a
  committed attempt remain absent.

Until those blockers are closed, confirmatory budgets, thresholds, unresolved
fixture encodings, predictions, runner inputs, and execution records remain
prospective DRAFT inputs. Development artifact bindings are not a freeze
receipt. There is no `STARTED.json`, no confirmatory output, and no CP50
evidence claim.
