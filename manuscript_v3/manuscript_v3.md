# Association-Aware Bridges for Heterogeneous Event Configurations

> **Working title — `[NOVELTY-UNASSESSED]`**  
> **Manuscript v3 — result-free scientific skeleton, 2026-08-03**  
> **Authors:** withheld in this working draft  
> **Target:** ICML/ICLR/NeurIPS quality; venue format not yet selected

## Internal evidence-status notice

This notice is not part of a future submission. The manuscript currently
defines a candidate method and a falsifiable evaluation program. It contains no
admissible model-quality, cross-domain, perceptual, or generality result. The
candidate guide-plus-residual construction remains novelty-unassessed against
the nearest conditional-guidance literature. An internally cross-audited
mathematical candidate now fixes the association weights, common-space/cap
correction, base targets and loss, initializer, and simulator semantics in the
[executable method specification](executable_method_spec.md). Six incremental
layers are implemented and separately audited: the transformed configuration
reference ([first layer](configuration_reference_code_audit.md)), reversible
forward reference process
([second layer](reversible_hybrid_reference_code_audit.md)), and NumPy
reference-relative reverse-target/population-objective oracle
([third layer](reverse_energy_objective_code_audit.md)), followed by the bound
normalized endpoint association-observation oracle
([fourth layer](association_observation_code_audit.md)) and the analytic
association preconditioner with explicit cap-boundary diagnostic
([fifth layer](association_preconditioner_code_audit.md)), and the bounded
neural scalar plus snapshot certificate
([sixth layer](configuration_energy_code_audit.md)). The fifth layer is
an exact-oracle implementation for the declared conjugate family, not a
representative-scale association algorithm or the complete Section 6.3
defect report. The sixth is a CPU-float64 correctness implementation, not a
trained or selected checkpoint, scalable training pipeline, production edge
composer, or sampler-admission mechanism; none of the layers is a reverse
sampler. The method remains
**`[METHOD-DEFINITION-PENDING]`** until the remaining contract is implemented,
tested, numerically frozen, and re-audited as a whole. Text marked
`[THEOREM-TARGET]` or `[RESULT-PENDING]` is a
research obligation, not a claim. The companion
[novelty audit](novelty_audit_matrix.md), [claim ledger](claim_ledger.md), and
[execution preregistration](execution_preregistration.md) control promotion of
submission prose.

## Abstract — result-free draft

Real event data often combine a random number of categorical events, physical
timestamps, and continuous attributes whose meaning and support depend on event
type. Clinical measurements, transaction streams, and expressive musical
performances share this structure, yet differ in their time references,
multiplicity, and observation processes. We study conditional generation for
such data when the available evidence is an unordered, noisy subset of events
and its correspondence to latent generated events is not given. We represent a
record as a capped finite counting measure on a typed event space and use a
hybrid process with within-type continuous motion and discrete birth, death,
and replacement transitions. Conditioning is expressed through a scalar
backward-information function that tilts the valid reverse process. Our
candidate estimator combines a computable association-aware guide with a
learned residual and marginalizes compatible observation-to-event matchings.
The generic bridge construction is standard; the guide-plus-residual
specialization is a novelty hypothesis rather than an established
contribution. We specify the finite and mixed continuous known-law tests,
representative-cardinality scaling gates, strong fixed-base and end-to-end
baselines, and multi-domain evaluation that a preregistration must freeze.
**`[LEDGER-PENDING / RESULT-PENDING]`** Until every preregistration field
applicable to a result slot is frozen and that slot's staged authorization is
active, its decision-bearing run is exploratory and cannot unlock a claim.
Numerical findings will be inserted only after the applicable gates execute.

## 1. Introduction

Many sequences are neither purely symbolic nor ordinary real-valued time
series. An intensive-care record contains categorical measurement identities,
continuous values, tied or irregular timestamps, and variable event count. A
customer history couples product and transaction categories with quantities,
prices, returns, and invoice times. A musical performance couples a symbolic
score with onset, duration, velocity, and pedal behavior. In each case, the
continuous attributes are meaningful only relative to discrete event structure,
and physical time is part of the data rather than the noising clock of a
generative model.

This combination creates more than a feature-type mismatch. The number of
events is itself random; repeated events and exact ties may be semantically
valid; changing an event type may change which continuous fields exist; and
partial observations need not identify which generated occurrence they refer
to. A fixed padded tensor can be a useful implementation or baseline, but it
does not by itself define the probability law for these operations. Conversely,
independent models for event count, type, time, and marks can reproduce
marginals while missing their joint and temporal dependence.

Recent work already covers much of the surrounding landscape. Mixed-state and
arbitrary-state diffusion supports native categorical and continuous variables;
trans-dimensional jump processes and point/edit models support variable
cardinality; marked temporal models support irregular mixed events; and general
Doob-transform frameworks support conditional generation. These advances make
two broad claims untenable: joint native discrete–continuous generation is not
new, and a generic scalar conditional potential is not new. Our question must
therefore be narrower and empirically falsifiable.

We study the following setting. A latent record is a capped finite counting
configuration of typed events with physical time and type-valid marks. The
observation is a separately modeled unordered subset produced by a declared
detection, noise, and clutter process. Its association to latent event
occurrences is marginalized. One unconditional generator is trained per
domain, and one conditioning construction is evaluated across a frozen family
of observation tasks. “One generator” does not mean shared weights across
clinical, retail, and music data; it means the same probabilistic method and
conditioning semantics, with separately trained domain instances.

The candidate method uses a positive association-aware guide
\(\widetilde h\) and a learned residual \(r_\theta\) so that

\[
\widehat h_{u,m}^{\phi,\theta}(y;a,z)
=\widetilde h_{u,m}(y;a,z)
  \exp r_\theta(u,y,a,m,z).
\]

The resulting plug-in scalar changes the continuous drift and every already-valid
birth, death, and replacement edge through the corresponding conditional
ratios. The current mathematical candidate propagates a conjugate independent
uncapped reference guide, restricts it literally to the capped state, and
separates the resulting cap-boundary term from the still-pending base-mismatch
and numerical derivative terms. The normalized endpoint observation law and
this conjugate propagated-guide/cap calculation are now implemented as exact
theorem oracles. A production proposal with a frozen uncertainty rule and a
scalable association approximation remain open method gates. The central
scientific question is not whether a Doob transform exists, but whether this
association-aware preconditioning
produces a distinctive, scalable, and calibrated advantage over matched direct
conditioning and modern learned-guidance baselines.

The intended contribution package is deliberately conditional:

1. **Candidate method — `[METHOD-DEFINITION-PENDING / NOVELTY-UNASSESSED]`.** A computable
   association-aware guide plus a learned residual for one declared class of
   noisy unordered observations of capped heterogeneous event configurations.
2. **Candidate analysis — `[THEOREM-TARGET]`.** A code-matched result connecting
   guide approximation or target/reference discrepancy to residual or
   conditional-path error, beyond generic Doob and path-relative-entropy
   identities.
3. **Candidate evidence — `[RESULT-PENDING]`.** Exact known-law recovery,
   representative association scaling, and uncertainty-aware comparisons on
   three real domains, including at least two outside music.

If `METHOD-NOVELTY-GO` fails but the separately defined equal-compute
`EMPIRICAL-CONTRIBUTION-GO` passes, Route A may continue only as an empirical
or mechanism study and the new-method claim is retired. If neither passes, we
will not retain the bridge as a headline by relabeling standard machinery. The
planned Route-B fallback candidate asks when true physical elapsed time
improves dependence-sensitive mixed-event generation under identical-cell
clock interventions; it is not predeclared until its ledger is immutably
frozen. If only the score-aligned music effect survives, the work becomes an
application paper rather than a general framework.

## 2. Related Work and Exact Novelty Boundary

### 2.1 Mixed and arbitrary-state generative processes

[CoDi](https://proceedings.mlr.press/v202/lee23i.html) uses mutually conditioned
continuous and discrete diffusion branches for mixed tabular data.
[MultiFlow](https://proceedings.mlr.press/v235/campbell24a.html) combines native
discrete continuous-time Markov chains with continuous flow for coupled
sequence–structure generation. [Diffuse
Everything](https://openreview.net/forum?id=AjbiIcRt6q) develops diffusion on
products of arbitrary state spaces,
including mixed categorical and continuous components and modality-specific
schedules. [TabDiff](https://openreview.net/forum?id=152c06fde5afb804fa5e2d50486a172bd56ec4e6)
and [CDTD](https://openreview.net/forum?id=QPtoBPn4lZ) further occupy fixed-schema
mixed-table generation, while [JointDiff](https://openreview.net/forum?id=6jThckejtL)
jointly generates continuous multi-agent trajectories and synchronous discrete
events. [Generator Matching](https://proceedings.iclr.cc/paper_files/paper/2025/hash/819aaee144cb40e887a4aa9e781b1547-Abstract-Conference.html)
provides a general generator view encompassing drift, jump, and product-space
processes. These works occupy
native mixed-state generation, product-space corruption, and generic drift/jump
coupling. Our paper cannot claim novelty for maintaining categorical and
continuous variables in their native spaces or for conditioning two prediction
branches on one another.

### 2.2 Random cardinality and event generation

[Trans-dimensional jump diffusion](https://papers.neurips.cc/paper_files/paper/2023/hash/83a10a480fbec91c88f6a9293b4d2b05-Abstract-Conference.html)
learns dimension-destroying forward and dimension-creating reverse processes.
[Add-and-Thin](https://papers.neurips.cc/paper_files/paper/2023/hash/b1d9c7e7bd265d81aae8d74a7a6bd7f1-Abstract-Conference.html)
and [Point Set Diffusion](https://proceedings.iclr.cc/paper_files/paper/2025/hash/cceb6b5d1781b6eb848f7e87bff5f74b-Abstract-Conference.html)
generate random-cardinality point configurations. [Edit-Based Flow
Matching](https://openreview.net/forum?id=FNf9IV1P2L)
uses insertion, deletion, and substitution operations for temporal point
processes, while [Interacting Diffusion
Processes](https://proceedings.mlr.press/v235/zeng24f.html) couples event type
and inter-arrival-time diffusion. [Branching Diffusion for Point
Processes](https://openreview.net/pdf/574a07a3ab057971ab142c75a5fd8ad25a7c8312.pdf) already
combines continuous atom motion with birth/death counting-measure dynamics, and
the recent [Existence-Field Diffusion](https://arxiv.org/abs/2607.26428)
preprint provides another
variable-cardinality point-process construction. *Transformers for Mixed-type
Event Sequences* ([FlexTPP](https://papers.nips.cc/paper_files/paper/2025/hash/a6c7515ac435277dc92b75a07bb2257c-Abstract-Conference.html))
provides a strong probabilistic autoregressive model
for irregular events with event-dependent mixed marks. These methods are the
closest substrate and empirical competitors. The hybrid base generator in this
paper is not a novelty claim. A new paper must distinguish its observation law,
association treatment, and conditional estimator rather than present
birth/death/replacement dynamics or parallel event generation as new.

### 2.3 Conditional diffusion, bridges, and guided generators

General [conditional-diffusion frameworks](https://openreview.net/forum?id=k2PA7CUUJH)
and [DEFT](https://proceedings.neurips.cc/paper_files/paper/2024/hash/22d258dfbdf840ccbf266bbc545dd95f-Abstract-Conference.html)
describe conditional
generation through Doob corrections, including learned corrections to fixed
unconditional models. [Bridge-score learning](https://proceedings.mlr.press/v258/baker25a.html)
estimates bridge corrections without relearning a time reversal.
[Conditioning continuous-time Markov processes by
guiding](https://doi.org/10.1080/17442508.2022.2150081) uses approximate
information functions and jump-rate ratios. [Neural Guided Diffusion
Bridges](https://proceedings.mlr.press/v267/yang25af.html) combines a tractable auxiliary guide
with a learned neural correction. pCoMole, an ICLR 2026 DeLTa workshop paper,
[applies Doob guidance to edit flows](https://openreview.net/forum?id=tTILzscPs4).
Accordingly, “analytic guide plus neural residual” is not an adequate novelty
statement on its own. **`[NOVELTY-UNASSESSED]`** The candidate survives only if
the exact association-aware construction, common-space correction, or
code-matched empirical behavior remains distinct after direct comparison with
these methods.

### 2.4 Unordered association and partial observation

Random-finite-set filtering has long marginalized combinatorial data-association
hypotheses, including [Poisson multi-Bernoulli observation
models](https://doi.org/10.1109/TAES.2019.2920220). [Intermittent/missing-event
inference](https://proceedings.mlr.press/v130/gupta21a.html) and
[mark-censoring inference](https://proceedings.mlr.press/v216/boyd23a.html) are
also established in temporal point processes.
Our use of latent matching is therefore foundation rather than firstness. The
working hypothesis is that a declared heterogeneous observation kernel, a
computable association-aware guide, and one residual potential may provide a
useful conditioner across continuous motion and every edit family. This is not
called a literature gap or contribution until the method-freeze audit finds an
irreducible distinction.

### 2.5 Domain-specific models

[TimeDiff](https://academic.oup.com/jamia/article/31/11/2529/7747780) is a mixed
categorical–continuous diffusion model for EHR time series. For expressive
performance, [DExter](https://www.mdpi.com/2076-3417/14/15/6543), [*SyMuPe:
Affective and Controllable Symbolic Music Performance*](https://arxiv.org/abs/2511.03425)
(whose model is PianoFlow), [ScorePerformer](https://archives.ismir.net/ismir2023/paper/000069.pdf),
[VirtuosoNet](https://archives.ismir.net/ismir2019/paper/000112.pdf), and other
score-conditioned systems are stronger comparators than
the music-only related-work set in the supplied manuscript. Rule-Guided
Symbolic Music Diffusion [supports high-resolution symbolic
controls](https://proceedings.mlr.press/v235/huang24g.html).
[JointPianist](https://iclr.cc/virtual/2026/poster/10011863) uses diffusion for
style recommendation rather than as the core
renderer and must be compared only on its supported role. The original CFC
[paper](https://www.nature.com/articles/s42256-022-00556-7) establishes the
continuous-time cell; inserting that cell into a
diffusion Transformer is architecture transfer, not a broad method
contribution.

### 2.6 Provisional distinction

Among the primary works audited so far, several cover strict supersets of
individual ingredients used here. We therefore make no firstness claim. The
working distinction is:

> a scalable learned conditioner for capped typed finite multisets that
> marginalizes noisy unordered association and uses a shared residual potential
> to modify every declared transition family of one declared hybrid base
> process.

The novelty status remains **unassessed** until this wording survives a
property-level and code-matched audit against conditional-guidance, general
generator, point/edit, and random-finite-set methods.

## 3. Problem Definition

### 3.1 Typed finite-counting configurations

Let \(\mathcal D\) be a finite event-type set. Each type \(d\in\mathcal D\)
has a continuous mark space \(\mathcal C_d\), support, and reference measure.
On physical horizon \([0,H]\), define the disjoint-union event space

\[
\mathcal E
=\coprod_{d\in\mathcal D}
  \bigl([0,H]\times\{d\}\times\mathcal C_d\bigr).
\]

A latent record is the finite counting measure

\[
X=\sum_{j=1}^{J}m_j\delta_{(\tau_j,d_j,c_j)}
\in\Gamma_{\le N}^{\mathrm{count}}(\mathcal E),
\qquad
m_j\in\mathbb N,
\quad \sum_j m_j\le N.
\]

The displayed support triples are distinct, and
\(|x|:=x(\mathcal E)=\sum_j m_j\) counts occurrences rather than distinct
support points.

Let \(\lambda_H\) be the declared atomic, atomless, or mixed physical-time
reference and let \(\nu_d\) be the reference on \(\mathcal C_d\). Their
disjoint-union event reference is

\[
\nu
=\sum_{d\in\mathcal D}
  \lambda_H\otimes\delta_d\otimes\nu_d.
\]

Unless a domain requires a separately stated alternative, densities on
\(\Gamma_{\le N}^{\mathrm{count}}(\mathcal E)\) are taken relative to the
pushforward of
\(\sum_{n=0}^{N}(1/n!)\nu^{\otimes n}\) under
\((e_1,\ldots,e_n)\mapsto\sum_i\delta_{e_i}\). This symmetrized reference
makes occurrence labels unobservable and supplies the multiplicity factors for
repeated atoms. The exact normalized or sigma-finite convention, including its
cap, is frozen per domain and used unchanged in forward, reverse, and bridge
derivations. The \(n=0\) term is unit mass at the empty configuration; the
simple branch restricts each product stratum to pairwise-distinct tuples before
quotienting. Mixed atomic/atomless time references carry an explicit stratum
tag so only atomless coordinates receive gradients.

The count cap \(N\) is an implementation and theorem boundary, not a claim of
unbounded generation. A simple-configuration branch restricts \(m_j=1\) and
forbids collision-producing births or replacements. Sorting distinct physical
time groups is a serialization, not part of the probability law. Within an
exact tie, the model uses invariant aggregation or a permutation-equivariant
encoder; arbitrary occurrence-slot order is never visible.

An optional global context \(z\in\mathcal Z\) is specified separately. We model
\(p(X\mid z)\). Static clinical variables, for example, are observed context
unless a separate context generator is declared.

Each domain must freeze its physical-time reference (atomic, atomless, or
mixed), mark references and support transforms, multiplicity semantics,
inapplicability versus missingness, cap/window policy, and group-disjoint split.

### 3.2 Three distinct clocks

We distinguish:

- physical event time \(\tau\in[0,H]\), part of each event;
- forward noising time \(s\in[0,S]\); and
- reverse generative time \(u=S-s\).

Let \(Z_s\) denote the forward corruption, with \(Z_0\) distributed as data
and \(Z_S\) near or at the terminal reference. Its exact reversal is

\[
Y_u^\star=Z_{S-u},\qquad Y_0^\star\sim p_S(\cdot\mid z).
\]

The candidate learned generator is a separate process
\(Y^\phi\), initialized from \(\rho_0^\phi(\cdot\mid z)\) and governed by
\(\bar{\mathcal L}_u^\phi\). Thus \(Y_S^\phi\) is a generated data-space
configuration, but it equals the data law only when base and terminal errors
vanish. Every information function, classifier pair, and initializer below
refers to \(Y^\phi\); discrepancy from \(Y^\star\) is retained as base-model
and terminal-reference error. A temporal encoder such as CFC may consume
differences in physical time \(\Delta\tau\); that does not make the noising
process a continuous-time physical model.

### 3.3 Observation object and tasks

For task index \(m\), let an observation \(A\) of the candidate generated
endpoint \(Y_S^\phi\) follow a normalized kernel

\[
A\mid(Y_S^\phi=y,z,m)\sim K_m(da\mid y,z).
\]

**`[TASK-ADMISSION-PENDING]`** The intended confirmatory task is an unordered
Bernoulli-thinned subset of events, using native exact observations for
genuinely atomic coordinates and acquisition-justified noise for atomless
coordinates. Misses and clutter are included only where the application
supplies a defensible mechanism. Literal thinning has structural zeros and is
not automatically covered by the positive-density branch in Section 5.1.
Before RQ1 can be frozen, each confirmatory domain must therefore either admit
a naturally positive observation kernel or use a proved and implemented
common-support/structural-zero extension. Exact atomless anchors, deterministic
prefixes, and hard support-zero cardinality constraints remain outside the
primary dominated theory.

The observation is itself an unordered capped counting configuration
\(A\in\Gamma_{\le M_m}^{\mathrm{count}}(\mathcal E_m^{\mathrm{obs}})\), with a
declared symmetrized reference probability \(\lambda_m\). Its assignment to
latent events is not observed. For the clean association kernel
\(K_m^{\mathrm{clean}}\), write

\[
g_{\mathrm{assoc},m}^{\mathrm{clean}}(a\mid y,z)
=\sum_{\mu\in\mathcal M_m(a,y)}w_m(\mu;a,y,z),
\]

where \(\mathcal M_m(a,y)\) is the quotient set of compatible injective
occurrence matchings under permutations that exchange identical repeated
copies. Each weight contains the declared detection, confusion, mark-noise,
clutter, reference-density, orbit-multiplicity, and symmetry terms. An
implementation may temporarily label occurrence copies, but summing over the
equivalence classes must produce the same value under every relabeling. Exact
duplicate-atom invariance and
\(\int g_{\mathrm{assoc},m}^{\mathrm{clean}}(a\mid y,z)\lambda_m(da)=1\)
are known-law gates, not assumptions inferred from the displayed sum. The
model never receives \(\mu\). For the confirmatory association task we set
\(g_m^{\mathrm{clean}}:=g_{\mathrm{assoc},m}^{\mathrm{clean}}\); the positive
dominated density \(g_m\), when admitted, is the distinct mixture defined in
Section 5.1.

The current candidate instantiates \(\lambda_m\) as a unit-rate Poisson
configuration reference with an explicit overflow atom and instantiates the
clean kernel with independent detection, type confusion, affine-Gaussian or
finite-atomic mark noise, and Poisson clutter. Its occurrence-labelled
formula, duplicate-orbit coefficient, exact subset dynamic program, overflow
law, and refusal boundary are fixed in the
[executable method specification](executable_method_spec.md). This is a
method contract, not evidence that a real domain admits those semantics.

The association headline is admitted only after a method-blind,
training-split-only audit applies predeclared numerical ambiguity thresholds to
the frozen candidate domains. Domain admission is completed before any
guide-versus-direct outcome is inspected; frozen domains cannot be replaced by
more favorable ones. If fewer than two domains pass without arbitrary added
noise, the association headline is dropped.

### 3.4 Learning and generation objectives

For each domain and context policy, the system must support:

1. unconditional generation from the learned base law;
2. confirmatory conditional generation for the unordered subset task;
3. optional secondary continuation, reconstruction, or partial-mark tasks only
   when their observation kernels are admitted; and
4. one-checkpoint task generalization only under a preregistered
   train-task/held-out-task estimand.

The target is the conditional law of the complete configuration, not a single
best completion or independently predicted attributes.

## 4. Hybrid Configuration Process

### 4.1 Forward generator

For a suitable test function \(f\), a schematic capped forward generator is

\[
\begin{aligned}
(\mathcal L_s f)(x)
={}&\int x(de)\left[
b_s(e,x,z)^\top\nabla_e^{\mathrm{cont}}f(x)
+\tfrac12\operatorname{tr}\!\left\{
a_s(e,x,z)(\nabla_e^{\mathrm{cont}})^2f(x)
\right\}\right]\\
&+\mathbf 1_{\{|x|<N\}}
\int_{\mathcal A^+(x)}\lambda_s^+(v\mid x,z)
[f(x+\delta_v)-f(x)]\,\nu(dv)\\
&+\int x(de)\lambda_s^-(e\mid x,z)
[f(x-\delta_e)-f(x)]\\
&+\int x(de)\lambda_s^R(e\mid x,z)
\int_{\mathcal A^R(e,x)}
[f(x-\delta_e+\delta_v)-f(x)]
R_s(dv\mid e,x,z).
\end{aligned}
\]

The four terms describe continuous within-stratum motion, birth, death, and
typed replacement. Gradients act only on declared atomless continuous
coordinates; \(\nabla_e^{\mathrm{cont}}\) is the derivative obtained by moving
one occurrence while holding the rest of the configuration fixed. Every
continuous stratum declares a support transform or reflecting/absorbing
boundary condition. The admissible sets enforce cap, support, and simple-branch
collision constraints. The birth intensity must satisfy

\[
\Lambda_s^+(x,z)
=\int_{\mathcal A^+(x)}\lambda_s^+(v\mid x,z)\nu(dv)<\infty,
\]

and total exit intensity must obey the frozen nonexplosion bound. When the
replacement exit rate is positive,
\(R_s\) is normalized on \(\mathcal A^R(e,x)\); if that set is empty, the exit
rate is zero. Integration against \(x(de)\) provides occurrence-scaled death
and replacement for repeated atoms. The simple branch is used only if the
collision diagonal is inaccessible under the continuous dynamics or a proved
non-colliding boundary rule is supplied; otherwise the counting branch is the
primary state.

Type-changing reverse edges must contain the transposed flux and the correct
Radon–Nikodym/reference factors between source and destination mark fibers. A
Doob multiplier can tilt an already-valid reverse kernel; it cannot repair a
base kernel that omits those factors.

The first implementation candidate specializes this schematic generator. It
maps each atomless stratum bijectively to Euclidean standardized coordinates,
uses a normalized capped-Poisson reference \(\Pi_N\), and combines stationary
OU motion with reversible birth/death and type-replacement kernels. Birth and
death constants obey \(\beta/\delta=\vartheta\), and the type kernel obeys
\(w_d\kappa_{dd'}=w_{d'}\kappa_{d'd}\). Piecewise-constant schedules permit
exact integrated-clock forward simulation. A zero-generator clean hold at the
data end makes the untrained reverse endpoint segment an exact identity rather
than an extrapolation. Full measures, multiplicity
factors, and simulation semantics are fixed in the
[executable method specification](executable_method_spec.md); none is claimed
as novel.

### 4.2 Unconditional reverse model

The candidate reverse model \(Y^\phi\), not yet implemented as a learned
trajectory model, is defined to have generator
\(\bar{\mathcal L}_u^\phi\) with respect to the same configuration references.
Write
\(V_s^*(x,z)=\log\!\left(\frac{dP_s(\cdot\mid z)}{d\Pi_N}(x)\right)\).
Reversibility gives the
exact local reverse characteristics at \(u=S-s\):

\[
\bar b_u^*(e,x,z)
=-\tfrac12\gamma_C(s)r_e+\gamma_C(s)\nabla_eV_s^*(x,z),
\qquad
\bar q_u^*(x,dy\mid z)
=q_s^0(x,dy)e^{V_s^*(y,z)-V_s^*(x,z)}.
\]

One bounded, permutation-invariant \(C^2\) scalar \(V_\phi\) supplies both
corrections. The selected population risk combines Gaussian-reference relative
score matching,

\[
\mathcal L_C
=\mathbb E\sum_{e\in X_s}\gamma_C(s)
\left[\tfrac12\|\nabla_eV_\phi\|^2
+\Delta_eV_\phi-r_e^\top\nabla_eV_\phi\right],
\]

with the reversible jump-flux loss, where
\(\Delta_\phi(s,x,y)=V_\phi(s,y,z)-V_\phi(s,x,z)\),

\[
\mathcal L_J
=\mathbb E\int q_s^0(X_s,dy)
\left[e^{\Delta_\phi(s,X_s,y)}+\Delta_\phi(s,X_s,y)\right].
\]

The base time law has strictly positive density on the entire active noising
interval; the clean hold has zero generator and needs no energy target.
The positive linear sign follows from transposing reverse-jump flux through the
reversible reference edge measure. Both population excesses are nonnegative
and vanish at \(V^*\), up to the state-independent time/context gauge, under
the displayed candidate assumptions. Continuous-destination integrals use
unnormalized proposal weights; self-normalized loss estimators are forbidden.
These algebraic identities now have a third incremental NumPy equation-to-code
audit: Tests 7--10 are substantively closed in their declared
finite/Gaussian/importance-oracle scopes. A sixth incremental correctness
layer now implements the bounded permutation-invariant neural scalar, owned
snapshot certificate, exact/Hutchinson derivatives, both training-objective
primitives, output-gauge controls, and supplied-rate operational guards. It
supplies substantive Tests 11--12 evidence only in the declared
scalar/certificate/autodiff/supplied-rate scope and assumes a trusted,
unmodified Python/PyTorch runtime. It is not a trained checkpoint, production
edge validator, or sampler-admission mechanism. The end-to-end method
therefore remains **`[METHOD-DEFINITION-PENDING]`**; scalable training,
checkpoint selection, production proposal integration, and the complete
sampler contract remain governed by the
[executable method specification](executable_method_spec.md).

The source manuscript's absorbing D3PM plus Gaussian denoising objective is a
fixed-grid reference only. It does not train the native random-cardinality
generator. Focal loss, if retained for that reference, is labeled an imbalance
heuristic rather than a variational term.

### 4.3 Base-quality prerequisite

The bridge is evaluated only after one frozen unconditional base per domain
passes the primary unconditional metric, named-comparator noninferiority
margin, calibration/support constraints, and compute ceiling recorded in the
execution preregistration. Checkpoint selection uses validation data without
access to conditional test outcomes. Every same-base bridge comparison uses the
identical base checkpoint. End-to-end comparisons against fully trained
conditional systems are reported separately, so the bridge is not credited for
repairing a weak or differently tuned generator.

## 5. Association-Aware Conditional Bridge

### 5.1 Dominated observation branch

The clean kernel \(K_m^{\mathrm{clean}}\) may contain structural zeros. Only
where scientifically justified, a declared full-support observation component
\(R_{0,m}\) may define

\[
K_m=(1-\epsilon_m)K_m^{\mathrm{clean}}+\epsilon_m R_{0,m},
\qquad
g_m=(1-\epsilon_m)g_m^{\mathrm{clean}}+\epsilon_m r_{0,m}>0.
\]

For the primary dominated theory, this \(K_m\) has a positive density

\[
g_m(a\mid y,z)
=\frac{dK_m(\cdot\mid y,z)}{d\lambda_m}(a)
\]

relative to a normalized observation-reference probability \(\lambda_m\), with
\(r_{0,m}=dR_{0,m}/d\lambda_m\). For every sampler-admitted fixed
\((a,m,z)\), the density and propagated guide must have a finite statewise
upper envelope and the derivative/rate integrability specified in the method
contract; a uniform bound over all possible observations is not assumed.
Clean and mixture kernels are stored as
separate objects. The component and \(\epsilon_m\) are included only when part
of a defensible acquisition model; epsilon noise is not added solely to satisfy
a theorem. If two real domains do not admit a natural positive dominated law,
the project must prove a structural-zero/common-support extension or retire
this bridge headline. The formulas below use the positive \(g_m\); they are not
silently evaluated at zeros of \(g_m^{\mathrm{clean}}\).

### 5.2 Information function and conditioned generator

For an observation \(a\) of the generated endpoint, define

\[
h_{u,m}^{\phi}(y;a,z)
=\mathbb E_\phi\!\left[
g_m(a\mid Y_S^\phi,z)\mid Y_u^\phi=y,z
\right].
\]

For \(\lambda_m\)-almost every admitted \(a\), require \(h\) to be finite,
positive, in the extended-generator domain, differentiable on every continuous
stratum, and to have integrable jump ratios. It then satisfies the backward
boundary problem

\[
(\partial_u+\bar{\mathcal L}_u^\phi)h_{u,m}^\phi=0,
\qquad
h_{S,m}^\phi(y;a,z)=g_m(a\mid y,z).
\]

Under these conditions, the exact conditional drift and jump kernel of the
candidate base are

\[
\bar b_{u,m}^{\phi,a}(y)
=\bar b_u^\phi(y)
+\bar a_u^\phi(y)\nabla\log h_{u,m}^{\phi}(y;a,z),
\]

\[
\bar q_{u,m}^{\phi,a}(y,dy')
=\bar q_u^\phi(y,dy')
\frac{h_{u,m}^{\phi}(y';a,z)}
     {h_{u,m}^{\phi}(y;a,z)}.
\]

The exact conditional initial noise law is

\[
\rho_{0,m}^{\phi,a,z}(dy)
=\frac{\rho_0^\phi(dy\mid z)h_{0,m}^{\phi}(y;a,z)}
       {p_{A,m}^{\phi,\lambda}(a\mid z)}.
\]

Here
\(p_{A,m}^{\phi,\lambda}(a\mid z)
:=\int\rho_0^\phi(dy\mid z)h_{0,m}^\phi(y;a,z)\)
is the candidate base's observation density relative to \(\lambda_m\).

This initialization is part of the target conditional law. Its learned plug-in
counterpart and particle error are defined separately below. Ordinary reference
noise is an ablation. An endpoint refresh is not silently inserted; if later
used, its forward boundary kernel, reverse boundary kernel, and conditional tilt
must all be specified.

The common potential can induce coupling when the likelihood or base law is
nonseparable, but a shared scalar is not itself evidence of dependence. The
known-law and real-domain studies include separability and dependence-destroying
controls.

### 5.3 Computable guide plus learned residual

Let \(u_{\mathrm b}=S-s_{\mathrm{hold}}\) be the start of the reverse clean
hold and define the \(C^2\) boundary multiplier

\[
a_R(u)=\left(\max\left\{1-\frac{u}{u_{\mathrm b}},0\right\}\right)^3.
\]

It is identically zero on the hold, where the exact residual vanishes. The
candidate plug-in estimator is

\[
\widehat h_{u,m}^{\phi,\theta}(y;a,z)
=\widetilde h_{u,m}(y;a,z)
\exp r_\theta(u,y,a,m,z),
\qquad
r_\theta=a_R(u)\mathcal C_B(F_\theta(u,y,a,m,z)).
\]

The guide \(\widetilde h>0\) shares the terminal likelihood
\(\widetilde h_{S,m}(y;a,z)=g_m(a\mid y,z)\). It is called a reference
information function only after the reference and target processes are placed
on a common state space or their restriction and cap-boundary correction are
proved. The mathematical candidate uses an analytically tractable, independent
uncapped reverse-reference process and restricts its information function
literally to \(|y|\le N\), without conditioning on the cap. It explicitly
reports

\[
\mathfrak d_u^\phi
=\frac{(\partial_u+\bar{\mathcal L}_u^\phi)\widetilde h_u}
       {\widetilde h_u},
\]

including the blocked-birth boundary term and the learned-base/reference
mismatch. The exact sub-Markov propagation, overflow/positive-mixture guide,
cap-defect sign, and diagnostic estimator are fixed in the
[executable method specification](executable_method_spec.md). This makes the
approximation explicit; it does not turn the restricted guide into the exact
capped information function.
Replacing \(h\) by \(\widehat h\) in the drift and jump ratios defines a
plug-in controlled process. It equals the exact conditional law only when
\(\widehat h=h\); bounded-class approximation is included in potential error.

Under the candidate algorithm, joint classifier pairs would be sampled from
the learned base process once it is implemented and admitted: sample
\(Y_0^\phi\), roll to \(Y_S^\phi\), sample \(A\mid Y_S^\phi\), and retain an
intermediate \(Y_u^\phi\). Product negatives
require two independent base trajectories under the same fixed \(z\): use
\(Y_u^\phi\) from one and generate \(A\) from the other endpoint under task
\(m\). Batch permutation is not a valid substitute when contexts are unique or
continuous. This is standard
[joint-versus-product noise-contrastive density-ratio
estimation](https://proceedings.mlr.press/v9/gutmann10a.html), not a claimed
contribution. The equal-prior risk, conditional on \((m,z)\), is

\[
\begin{aligned}
\mathcal R_{u,m}(\ell)
={}&\tfrac12
\mathbb E_{P_{u,m}^{\phi,\mathrm{joint}}(\cdot\mid z)}
\operatorname{softplus}(-\ell)\\
&+\tfrac12
\mathbb E_{P_u^\phi(\cdot\mid z)
\otimes P_{A,m}^\phi(\cdot\mid z)}
\operatorname{softplus}(\ell).
\end{aligned}
\]

This risk is defined at fixed \(u\). Training averages both terms against the
same predeclared time law \(q(du\mid m,z)\), whose density is strictly positive
on \((0,S)\); neither class receives a different time distribution.

Over unrestricted measurable logits, under the displayed equal-prior sampling
law and mutual absolute continuity on the admitted common support, the Bayes
population optimum is

\[
\ell_m^*(u,y,a,z)
=\log h_{u,m}^{\phi}(y;a,z)+c^*(a,m,z),
\]

where the observation-only nuisance absorbs the generally intractable
observation marginal and is forbidden to depend on \(u\) or \(y\). Its network
receives only \((a,m,z)\), and dependency tests reject any path from \((u,y)\).
When the observation density is enumerable,
\(c^*(a,m,z)=-\log p_{A,m}^{\phi,\lambda}(a\mid z)\). We parameterize

\[
\ell_{\mathrm{G+R}}
=\log\widetilde h_{u,m}
+a_R(u)\mathcal C_B(F_\theta)
+c_\psi(a,m,z).
\]

Here \(\mathcal C_B\) is a predeclared smooth bounded model map, for example
\(\mathcal C_B(v)=B\tanh(v/B)\), with \(B\) frozen before comparison. The
bound is architectural rather than a runtime clip. The factor \(a_R\) enforces
the common boundary at the start of the clean hold without constraining the
observation-only nuisance.

The declared bounded residual class need not contain the unrestricted
Bayes logit. Its population solution is therefore the risk projection onto the
declared class, not an automatic recovery of \(h\). Approximation, bounded-class
projection,
nuisance-gauge, and common-support errors are separate terms in theorem targets
C17--C18 and separate diagnostics in both known-law gates.

The candidate plug-in initial tilt is defined as

\[
\widehat\rho_{0,m}^{\phi,\theta,a,z}(dy)
=\frac{\rho_0^\phi(dy\mid z)\widehat h_{0,m}^{\phi,\theta}(y;a,z)}
       {\int \rho_0^\phi(dv\mid z)
        \widehat h_{0,m}^{\phi,\theta}(v;a,z)}
\propto \rho_0^\phi(dy\mid z)
          e^{\ell_{\mathrm{G+R}}(0,y,a,m,z)}.
\]

The nuisance cancels in the normalization. With a certified envelope,
rejection sampling is exact for this plug-in law; it is exact for the desired
conditional initializer only when \(\widehat h=h\). Otherwise a frozen-budget
importance-resampling/SMC procedure introduces a separately measured particle
error.

The nuisance cancels from local bridge ratios and normalized initialization.
The exact observation marginal is required only in enumerable diagnostics. The
classifier targets the candidate base model's conditional law, not the
unknown data conditional law; same-base bridge accuracy and end-to-end data
fidelity are therefore separate estimands.

### 5.4 Matched direct and guidance controls

A matched direct learner shares task/context features, base rollouts, simulated
pair counts, optimizer updates, terminal likelihood, nuisance capacity,
initializer budget, and sampling compute, but receives no propagated guide.
Two fairness views are reported: equal trainable parameter/data budget and
equal total compute, the latter charging reference fitting, guide
precomputation, association approximation, tuning, initialization, and
inference. A boundary-matched form is

\[
\ell_{\mathrm{DIR}}
=\log g_m(a\mid y,z)
+a_R(u)\mathcal C_B(G_\eta)
+c_\omega(a,m,z).
\]

Additional controls include a preregistered stronger direct learner,
guide-as-input without additive preconditioning, mismatched guide, eventwise
potential, separate edit corrections, a Neural Guided Diffusion Bridges-style
auxiliary-guide-plus-correction control, a distinct DEFT-style learned
generalized-\(h\) correction over the frozen base, exact or task-compatible
SMC/Feynman--Kac conditioning where available, and oracle/exposed association
in known-law experiments. Every executable control and tuning space is frozen
before outcomes are inspected.

### 5.5 Training and sampling algorithms — `[MATHEMATICAL-CANDIDATE / METHOD-DEFINITION-PENDING]`

The steps below summarize the authoritative
[executable method specification](executable_method_spec.md). They do not
authorize training until its code-matched tests and numerical fields close.

**Algorithm 1: unconditional base training**

1. Sample a real configuration and context from the frozen training split.
2. Sample noising time \(s\) and the exact forward configuration corruption.
3. Evaluate relative score matching and the reversible jump-flux loss, using
   exact unnormalized proposal factors for continuous edit destinations.
4. Optimize the single bounded invariant scalar with derivative, support,
   multiplicity, and supplied-rate operational checks.
5. Validate unconditional known-law and base-quality gates before bridge work.

**Algorithm 2: bridge training**

1. Freeze one admitted base checkpoint.
2. Once implemented and admitted, roll the frozen learned base to obtain
   \((Y_u^\phi,Y_S^\phi)\).
3. Sample task/context-consistent observation \(A\mid Y_S^\phi\).
4. Construct matched joint and product pairs conditional on \((m,z)\).
5. Evaluate the guide and boundary-matched direct/control logits.
6. Optimize identical-risk learners under frozen pair, FLOP, and tuning budgets.

**Algorithm 3: conditional sampling**

1. Initialize from \(\widehat\rho_{0,m}^{\phi,\theta,a,z}\) with certified
   rejection or frozen SMC.
2. At each reverse time, evaluate \(\widehat h\), its continuous
   gradient/edit ratios, and its certified potential-oscillation envelope.
3. Simulate continuous coordinates with the frozen split-step integrator and
   every edit family, including continuous destinations, by certified
   reference-kernel thinning.
4. Return the complete configuration; do not expose hidden target cardinality
   or latent association.

## 6. Analysis Targets

This section contains no completed framework theorem.

### 6.1 Assumptions

The primary theorem route will require at least:

1. a capped, well-posed base process on the declared finite-counting space;
2. Lipschitz/linear-growth continuous coefficients and nonexplosive bounded
   jump characteristics;
3. normalized support-valid birth/death/replacement kernels;
4. sufficient positivity or an explicit common-support extension;
5. a normalized observation law and positive computable guide on target
   support;
6. common target/reference state space or an explicit restriction and
   cap-boundary flux;
7. an executable conditional initializer; and
8. learned rates positive wherever the exact conditional law has positive
   intensity, while preserving structural-zero edges.

### 6.2 Foundation results — not contributions

**`[FOUNDATION]`** The project already contains restricted finite/counting
identities and a positive dominated Bayes/log-score theorem. These do not yet
instantiate the full heterogeneous continuous configuration process and do not
establish novelty. Standard reverse-generator, Doob-transform, and path-KL
identities will be cited rather than advertised as new.

### 6.3 Main theorem target

**`[THEOREM-TARGET]`** Establish an estimator-specific statement that relates
the reference/target discrepancy and association ambiguity to the residual

\[
r^*=\log h-\log\widetilde h,
\]

or to an observable conditional-path error. A useful result must contain
executable quantities, include cap-boundary or guide-approximation error, and
match the declared learner and simulator once implemented. A generic existence
theorem or an unobservable error term does not unlock a theory contribution.

### 6.4 Reliability target

**`[THEOREM-TARGET]`** Decompose end-to-end conditional error into:

- unconditional base-model error;
- observation/association approximation error;
- learned-potential error;
- conditional-initialization error;
- terminal-reference error; and
- numerical simulation error.

The finite A1 count CTMC cannot unlock this claim. A mandatory mixed
CTMC–Gaussian/OU oracle must exercise continuous drift and every edit family.

## 7. Experimental Design

### 7.1 Confirmatory question and minimum package

The first confirmatory question remains **`[TASK-ADMISSION-PENDING]`**:

> **RQ1.** On one frozen noisy unordered-subset task, does the
> association-aware guide plus residual improve conditional configuration
> fidelity over a unified direct conditioner under one frozen base and matched
> total compute?

The confirmatory contrast is guide+residual versus unified direct. A separate
sample-efficiency estimand uses multiple frozen pair/FLOP budgets and compares
area under the learning curve or compute-to-threshold; a win at one budget is
not called sample efficiency. Other task patterns are secondary until RQ1
passes. The minimum package freezes one base architecture, one association
approximation, one initializer, one primary score, and a compact named baseline
set before scaling.

### 7.2 Known-law gates

**Finite A1 gate.** A capped count CTMC tests density-ratio orientation,
association likelihood, guide/residual recovery, tilted initialization, all
three edit families, endpoint law, and path diagnostics. This is an estimator
falsification experiment, not hybrid evidence.

**Mixed hybrid gate.** The oracle specification must freeze a capped finite
configuration CTMC and linear-Gaussian/OU mark propagation conditional on its
discrete path, with fixed or atomic event times and at least one type-changing
edge. A finite-path construction or matrix-analytic uniformization with a
certified truncation bound replaces an unsupported claim of a generally
enumerable CTMC--OU mixture. The certified conditional law tests
\(\bar a\nabla\log h\), birth/death/replacement ratios, initialization, endpoint
law, calibration, and numerical error. Exact or certified KL/TV is primary.

Both gates check source/destination Radon--Nikodym factors on type-changing
edges, multiplicity factorials, cap-boundary flux, association normalization,
the nuisance identity's constancy in \((u,y)\), nuisance invariance of drift,
jump ratios and normalized initialization, and exact-versus-plug-in
initialization error.

Both gates receive complete parameters, evaluation grids, and immutable
numerical tolerances in the execution preregistration before execution.

### 7.3 Real-domain admission

Candidate domains are:

| Domain | Event structure | Marks/time | Candidate task | Admission blocker |
|---|---|---|---|---|
| PhysioNet Challenge 2012 | Measurement type; static admission context separate | Value and elapsed ICU time; atomic/tied timestamps | Noisy unordered measurement-subset completion | Clinical semantics/governance and natural association ambiguity |
| Online Retail II | Product, cancellation, country | Quantity, price, invoice time; simultaneous line items | Noisy unordered basket/history-subset completion | Customer/time split, projection loss, and natural association ambiguity |
| ASAP | Performance-note/chord events; score context separate when used | Velocity, score/performed onset, duration, articulation | Noisy unordered performance-event-subset completion | Piece split, performer/composer leakage, tie handling, and observation semantics |

The task-conformance contract is not yet frozen:

| Domain | Generated endpoint \(Y_S^\phi\) and context \(z\) | Observation \(A\) | \(K_m^{\mathrm{clean}},\lambda_m\) | Positive/common-support route | Status |
|---|---|---|---|---|---|
| PhysioNet | Typed ICU measurement configuration; static admission fields in \(z\) | Unordered measurement-event configuration | Thinning/noise/reference all pending clinical review | Pending | **TASK-ADMISSION-PENDING** |
| Retail | Customer-window transaction-line configuration; declared customer/window context | Unordered transaction-event configuration | Thinning/coarsening/clutter/reference pending semantic review | Pending | **TASK-ADMISSION-PENDING** |
| ASAP | Performance-event configuration; score context in \(z\) only if frozen | Unordered performance-event configuration | Thinning/noise/reference pending alignment review | Pending | **TASK-ADMISSION-PENDING** |

The method-blind admission audit freezes the confirmatory domains before
guide/direct training, and every frozen domain is reported. No domain may be
replaced after an outcome is known. Two prespecified passing domains may answer
RQ1; a generality claim requires all three prespecified domains under one frozen
invariant method specification. MAESTRO is retained only for source-manuscript
reproduction; it does not validate score-relative rubato or non-music
generality.

Each admitted dataset freezes horizon \(H\), cap \(N\), segmentation, boundary
context, exclusion/overflow rate, and losses of long sequences, ties,
multiplicity, rare types, and marks. Patient, customer, or piece groups are
disjoint, and all preprocessing is fit on training data.

### 7.4 Association scaling

Before any framework-scale run, report:

- latent count and anchor count distributions;
- posterior-compatible matching count or association-entropy diagnostics;
- exact-computation threshold;
- approximation method and separate error bounds for \(\log h\),
  \(\nabla\log h\), and every edge ratio \(h(y')/h(y)\), including positivity,
  tails, and overflow;
- peak memory and latency versus count/ambiguity;
- failure and overflow behavior; and
- success at prespecified dataset count/anchor quantiles and ambiguity strata
  under frozen hardware, memory, latency, approximation, timeout, and OOM
  ceilings.

### 7.5 Baselines

The main matrix includes:

1. unified task-conditioned direct learner;
2. task-specific direct upper/reference model;
3. eventwise/factorized and separate-edit guidance;
4. Neural Guided Diffusion Bridges-style auxiliary guide plus correction;
5. DEFT-style learned generalized-\(h\) frozen-base correction;
6. exact or task-compatible SMC/Feynman--Kac same-base conditioning;
7. probabilistic autoregressive mixed-event model;
8. closest native parallel point/edit generator;
9. fixed-length mixed discrete–continuous reference; and
10. one task-compatible domain baseline.

Each baseline is frozen by repository/commit, license, native capability,
comparison intersection, tuning budget, and compute. Minimal extensions are
labeled as our extensions.

### 7.6 Metrics

For a characteristic event kernel \(k_{\mathcal E}\), embed a configuration as

\[
\mu_x=\int k_{\mathcal E}(e,\cdot)x(de),
\qquad
k_\Gamma(x,x')
=\exp\!\left(-\frac{\|\mu_x-\mu_{x'}\|^2}{2\sigma^2}\right).
\]

For target configuration \(x\) and conditional law \(P\), define the
configuration kernel score, up to target-only constant, by

\[
\operatorname{CKS}(P,x)
=\mathbb E k_\Gamma(X,X')-2\mathbb E k_\Gamma(X,x).
\]

For \(R\ge2\) independent conditional draws, use the U-statistic

\[
\widehat{\operatorname{CKS}}
=\frac{1}{R(R-1)}\sum_{r\ne r'}k_\Gamma(X_r,X_{r'})
-\frac{2}{R}\sum_{r=1}^R k_\Gamma(X_r,x).
\]

An applicable theorem must establish injectivity/characteristicness on the
exact admitted capped counting space before CKS is primary; empirical tests
cannot substitute for that property. If the theorem fails, the preregistration
selects a validated alternative score. Bandwidth selection on training data,
Monte Carlo \(R\), aggregation unit, meaningful-effect scale, and real--real
floor are frozen. Finite-sample power is tested on alternatives that preserve
marginals while destroying count, association, or temporal dependence.

Secondary metrics include proper categorical/continuous scores, coverage and
calibration by task/type/count, support validity, event-count distribution,
conditional marks, transition dependence, multi-lag and spectral temporal
statistics, diversity/coverage, exact/near-duplicate search, membership
inference, latency, memory, and number of model evaluations.

### 7.7 Statistical protocol

**`[LEDGER-PENDING]`** Before execution, power simulation selects an exact seed
count or a fully specified valid sequential design; “at least five” is not a
stopping rule. The analysis uses a frozen hierarchical paired bootstrap or
mixed-effects model over checkpoint seed, natural group, and conditioning case.
Repeated conditional draws are Monte Carlo samples, not independent replicates.
We report all runs and failures, paired effects, confidence intervals, and
Holm-corrected comparisons over a completely enumerated primary family. The
run ledger freezes test-set access, the accelerator-hour ceiling,
pilot/tuning/final allocation, futility rules, and failure reserve.

### 7.8 Confirmatory pass rule — `[RESULT-PENDING]`

Before execution, the linked [execution
preregistration](execution_preregistration.md) must contain numerical
tolerances for known-law KL/TV, coverage, minimum meaningful CKS effect,
per-domain no-regression, run failure, initialization, association
approximation, memory, and latency. Support preservation is either proved by
construction or assessed with a frozen sample size and one-sided upper
confidence bound; observing zero failures is not itself a zero-violation proof.
RQ1 requires a positive guide-specific known-law effect and the frozen effect
criterion in both prespecified admitted confirmatory domains, with no declared
calibration or support regression. A generality claim additionally requires the
third prespecified domain and the invariant-method gate.

## 8. Results — intentionally empty

No result prose is authorized at this stage.

### 8.1 Known-law recovery

**`[RESULT-PENDING]`** Insert only from frozen A1 and mixed-hybrid artifacts.

| Method | Potential/rate error | Conditional KL/TV | Calibration | Initialization error | Decision |
|---|---:|---:|---:|---:|---|
| Exact oracle | — | — | — | — | Pending |
| Guide + residual | — | — | — | — | Not run |
| Unified direct | — | — | — | — | Not run |
| Neural Guided-style correction | — | — | — | — | Not run |
| DEFT-style correction | — | — | — | — | Not run |

### 8.2 Base quality and association scaling

**`[RESULT-PENDING]`** No base checkpoint or representative association pilot
has passed the manuscript gate.

### 8.3 Cross-domain confirmatory result

**`[RESULT-PENDING]`** Report every domain separately. An average rank cannot
hide a failed non-music domain.

| Domain | Guide + residual | Unified direct | Neural Guided | DEFT | Probabilistic AR | Closest parallel | Paired effect and CI |
|---|---:|---:|---:|---:|---:|---:|---|
| PhysioNet | — | — | — | — | — | — | Pending admission |
| Online Retail II | — | — | — | — | — | — | Pending admission |
| ASAP | — | — | — | — | — | — | Pending admission |

### 8.4 Secondary tasks and failure cases

**`[RESULT-PENDING]`** Flexible-conditioning language is prohibited unless the
held-out-task estimand is executed. Include negative results, scaling failures,
rare types, high ambiguity, initializer sensitivity, and outlier-mixture
sensitivity.

### 8.5 Source-manuscript reproduction

**`[SOURCE-REPORTED / RESULT-PENDING]`** The source reports the lowest marginal
onset-offset distance for its CFC variant, variance contraction in one narrow
deterministic AR comparator, no monotone trend in one scalar-binning sweep, and
failure of all tested backbones on lag-one dependence. These findings remain
outside the revised result tables until the clean-room reproduction protocol
reaches a decision.

## 9. Fallback Candidate: Physical-Time Mechanism Study

**`[LEDGER-PENDING]`** This becomes predeclared only when its full route entry is
frozen before any Route-A confirmatory outcome is inspected. If the bridge
receives an objective novelty or known-law no-go and the reference
infrastructure is sound, the fallback tests:

> True physical elapsed time improves dependence-sensitive mixed-event
> generation only when temporal irregularity is informative, after recurrence,
> gating, capacity, optimization, and compute are held fixed.

The primary controlled contrast is true versus fixed \(\Delta\tau\);
removed, shuffled, and rescaled clocks are falsifiers. Each condition is
retrained from scratch with paired data splits, initialization seeds, tuning
budget, and architecture; only the clock intervention changes. The target
population, synthetic irregularity distribution, retraining policy, primary
metric, margin, sample size, and paired analysis must all be frozen.
Confirmatory evidence requires an effect that grows with synthetic irregularity
and exceeds the margin in PhysioNet and Online Retail II without declared
support/calibration regression; ASAP is secondary. Route B uses an untouched
test partition and a prespecified route-selection/multiplicity rule. If that
complete freeze does not occur before Route-A inspection, Route B is treated as
a future separate paper, not a fallback result in this manuscript.

## 10. Limitations, Ethics, and Broader Impact

### 10.1 Current scientific limitations

- The guide-plus-residual construction is novelty-unassessed.
- The full capped continuous process and estimator-specific theorem are not
  proved.
- The positive dominated observation branch excludes important singular tasks
  unless a common-support extension is developed.
- The analytic guide exists only in a finite reference regime; real-domain
  tractability and approximation error are open.
- The method has a finite cap and may lose long sequences, rare events, or
  multiplicity under windowing.
- Association may not be naturally ambiguous in the candidate domains.
- The unconditional base, initializer, and association approximation may
  dominate any guide effect.
- A shared scalar does not guarantee nonseparable coupling.
- No performance, generality, utility, or perceptual result currently exists.

### 10.2 Clinical data

[PhysioNet Challenge 2012](https://physionet.org/content/challenge-2012/1.0.0/)
is openly downloadable under its declared license, but open access does not
establish clinical validity, safety, or institutional governance. Patient
splits, parameter semantics, task construction, and train-only preprocessing
require review. Distributional fidelity is not a claim of clinical benefit.
Any downstream utility study must be separately frozen and interpreted
conservatively.

### 10.3 Transactions and privacy

Retail data can expose rare customer behavior. Customer-disjoint temporal
splits, exact/near-duplicate checks, nearest-neighbor exposure, and a named
membership-inference attack are required before release. Synthetic generation
does not itself guarantee privacy.

### 10.4 Music and human evaluation

ASAP and MAESTRO represent restricted repertoires, instruments, performance
traditions, and recording practices. MIDI-clock residuals are not automatically
rubato. Perceptual claims require score-valid stimuli and a powered, blinded,
randomized listening study with ethics/consent, hidden-real anchors, catch
trials, identical rendering, and participant/piece-level analysis. A protocol
without outcomes is not evidence.

### 10.5 Reproducibility and compute

Code, configurations, model artifacts, logs, and representative samples will be
released when permitted. Data that cannot be redistributed must be
reproducibly re-acquirable through source instructions, hashes, schemas, and
split manifests. The final paper reports total accelerator hours, tuning trials,
wall time, memory, sampling evaluations, failures, and quality–compute tradeoffs.

## 11. Conclusion — result-gated placeholder

**`[RESULT-PENDING]`** The final conclusion will state only the method,
theorems, and empirical effects unlocked by the claim ledger. Methodological
wording requires `METHOD-NOVELTY-GO`; if only
`EMPIRICAL-CONTRIBUTION-GO` passes, C3 is retired and Route A is framed solely
as an empirical or mechanism contribution. If Route A survives neither that
rule nor its known-law, scaling, and two-real-domain gates, it will not appear
as a claimed contribution. If the planned physical-time fallback candidate is
frozen and also fails, the paper will be narrowed to
the reproducible source-manuscript findings actually supported by executed
evidence.

## Appendix Roadmap

### A. Reference measures, adjoints, and support-valid replacement

Full configuration reference, multiplicity identities, boundary conditions,
and source/destination fiber factors.

### B. Conditional-bridge derivations

Positive dominated branch, initialization, nuisance gauge, path-risk identity,
and any common-support extension.

### C. Association algorithms

Exact dynamic program, guide computation, approximation, complexity, memory,
and ambiguity diagnostics.

### D. Known-law fixtures and theorem-to-code tests

Finite A1 and mixed CTMC–Gaussian/OU oracle definitions, tolerances, and
complete per-seed/per-coordinate outputs.

### E. Data and representation

Licenses, acquisition hashes, time references, type/mark schemas, cap/window
loss audits, group splits, train-only transforms, and leakage checks.

### F. Architectures, objectives, and algorithms

Model diagrams, parameter counts, pseudocode, numerical solvers, initializer,
hyperparameters, tuning spaces, and checkpoint semantics.

### G. Statistics, complete results, and failure cases

Power analysis, hierarchical uncertainty, Holm families, all seeds, failures,
secondary tasks, scaling curves, calibration, privacy tests, and compute.

### H. Source-manuscript reproduction

Missing-configuration ledger, fixed-grid D3PM/VP/Gumbel/CFC implementation,
probabilistic AR baseline, clock interventions, reported-versus-reproduced
tables, and listening materials if executed.

## Working Primary-Source Inventory

This is a prose-stage inventory, not the final bibliography.

- [CoDi (ICML 2023)](https://proceedings.mlr.press/v202/lee23i.html)
- [Trans-Dimensional Generative Modeling via Jump Diffusion Models (NeurIPS 2023)](https://papers.neurips.cc/paper_files/paper/2023/hash/83a10a480fbec91c88f6a9293b4d2b05-Abstract-Conference.html)
- [Add and Thin (NeurIPS 2023)](https://papers.neurips.cc/paper_files/paper/2023/hash/b1d9c7e7bd265d81aae8d74a7a6bd7f1-Abstract-Conference.html)
- [MultiFlow (ICML 2024)](https://proceedings.mlr.press/v235/campbell24a.html)
- [Interacting Diffusion Processes (ICML 2024)](https://proceedings.mlr.press/v235/zeng24f.html)
- [Rule-Guided Symbolic Music Diffusion (ICML 2024)](https://proceedings.mlr.press/v235/huang24g.html)
- [DEFT: Efficient Fine-tuning of Diffusion Models by Learning the Generalised h-transform (NeurIPS 2024)](https://proceedings.neurips.cc/paper_files/paper/2024/hash/22d258dfbdf840ccbf266bbc545dd95f-Abstract-Conference.html)
- [Diffuse Everything (ICML 2025)](https://openreview.net/forum?id=AjbiIcRt6q)
- [Point Set Diffusion (ICLR 2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/cceb6b5d1781b6eb848f7e87bff5f74b-Abstract-Conference.html)
- [Generator Matching (ICLR 2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/819aaee144cb40e887a4aa9e781b1547-Abstract-Conference.html)
- [Neural Guided Diffusion Bridges (ICML 2025)](https://proceedings.mlr.press/v267/yang25af.html)
- [Score Matching for Bridges Without Learning Time-Reversals (AISTATS 2025)](https://proceedings.mlr.press/v258/baker25a.html)
- [Transformers for Mixed-type Event Sequences (FlexTPP; NeurIPS 2025)](https://papers.nips.cc/paper_files/paper/2025/hash/a6c7515ac435277dc92b75a07bb2257c-Abstract-Conference.html)
- [Edit Flows: Variable Length Discrete Flow Matching with Sequence-Level Edit Operations (NeurIPS 2025)](https://proceedings.neurips.cc/paper_files/paper/2025/hash/cb43f46154e750746602faaffd65fbbb-Abstract-Conference.html)
- [JointDiff: Bridging Continuous and Discrete in Multi-Agent Trajectory Generation (ICLR 2026)](https://openreview.net/forum?id=6jThckejtL)
- [Edit-Based Flow Matching for Temporal Point Processes (ICLR 2026)](https://openreview.net/forum?id=FNf9IV1P2L)
- [Branching Diffusion for Point Processes in Time and Space (ICML 2026)](https://openreview.net/pdf/574a07a3ab057971ab142c75a5fd8ad25a7c8312.pdf)
- [Existence-Field Diffusion Model for Spatial Point Processes with Variable Cardinality (2026 preprint)](https://arxiv.org/abs/2607.26428)
- [A Unified Approach to Analysis and Design of Denoising Markov Models (JMLR 2026)](https://www.jmlr.org/papers/v27/25-0693.html)
- [A Framework for Conditional Diffusion Modelling](https://openreview.net/forum?id=k2PA7CUUJH)
- [Conditioning Continuous-Time Markov Processes by Guiding](https://doi.org/10.1080/17442508.2022.2150081)
- [pCoMole: Pareto-Constrained Molecule Editing with Discrete Flows (ICLR 2026 DeLTa workshop)](https://openreview.net/forum?id=tTILzscPs4)
- [Poisson multi-Bernoulli conjugate prior for multiple extended object filtering](https://doi.org/10.1109/TAES.2019.2920220)
- [Noise-contrastive estimation](https://proceedings.mlr.press/v9/gutmann10a.html)
- [TabDiff](https://openreview.net/forum?id=152c06fde5afb804fa5e2d50486a172bd56ec4e6)
- [CDTD](https://openreview.net/forum?id=QPtoBPn4lZ)
- [PhysioNet/Computing in Cardiology Challenge 2012](https://physionet.org/content/challenge-2012/1.0.0/)
- [Online Retail II (UCI)](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
- [ASAP aligned score-performance dataset](https://github.com/fosfrancesco/asap-dataset)
- [TimeDiff](https://academic.oup.com/jamia/article/31/11/2529/7747780)
- [DExter](https://www.mdpi.com/2076-3417/14/15/6543)
- [SyMuPe: Affective and Controllable Symbolic Music Performance (PianoFlow)](https://arxiv.org/abs/2511.03425)
- [VirtuosoNet](https://archives.ismir.net/ismir2019/paper/000112.pdf)
- [ScorePerformer](https://archives.ismir.net/ismir2023/paper/000069.pdf)
- [JointPianist](https://iclr.cc/virtual/2026/poster/10011863)
- [Canonical CFC](https://www.nature.com/articles/s42256-022-00556-7)
