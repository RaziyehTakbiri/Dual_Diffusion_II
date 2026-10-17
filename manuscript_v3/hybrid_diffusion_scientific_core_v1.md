# Hybrid diffusion on mixed event configurations: scientific core

Date: 2026-09-13  
Status: manuscript-facing specification and research programme, not a completed
paper or a scientific performance result.

This document consolidates the selected mixed-domain model into one account of
the statistical problem, mathematical laws, implemented learner and numerical
sampler. It does not replace historical frozen records. The separate
[claim and proof plan](hybrid_diffusion_claims_and_proof_plan_v1.md) states which
results have proofs here and which claims remain open.

Follow-up: the [association/initializer proof](hybrid_diffusion_association_initializer_proof_v1.md)
is complete for its stated ideal reference laws. A separate
[finite-grid conditional-law contract](hybrid_diffusion_conditional_law_contract_v2.md)
and [known-law benchmark](../docs/FINITE_CONDITIONAL_BENCHMARK.md) now provide
independent posterior-error measurements. They do not silently replace the
mixed neural implementation or certify its full conditional law.

## 1. Research question and contribution boundary

**Question.** Can an exact association-aware reference calculation make
conditional generation of variable-cardinality, mixed discrete/continuous event
sets more accurate or computationally efficient than learning the conditional
correction directly, under the same target, observation task and measured budget?

The proposed answer combines a mathematically valid mixed carrier, a normalized
reference observation/association calculation, an explicit reference-posterior
initializer and a learned correction to a frozen generative BASE process.
The paper must establish the advantage of that combination, not merely show that
the implementation runs.

The ingredients are not individually novel: variable-dimension jump diffusions,
guided processes with learned corrections, score matching and joint/product
density-ratio estimation all have prior literature. The
[related-work and claim audit](hybrid_diffusion_related_work_and_claim_audit_v1.md)
identifies the closest primary sources. A defensible contribution would concern
the particular association-aware mixed-configuration construction and an
established theoretical or empirical advantage. Neither "first general hybrid
diffusion" nor superiority is currently justified.

The current comparison is guide-plus-residual (G+R) against a direct conditioner
(DIR) that still includes the terminal observation likelihood. DIR is not an
unconditional model and not an entirely analytic-free black box. A literal
no-guide baseline, if needed, must be specified separately rather than
misdescribing this comparator.

## 2. Statistical object and scope of generality

Fix a static context z. It identifies information conditioned on throughout a
generation task; it is not part of the generated event coordinates. Contexts,
training populations and observation tasks must be shared by compared methods.

Let D_z be a countable set of valid complete discrete keys. Each key has an
associated continuous fiber of dimension k(d). The selected implemented carrier
has k(d) in {0,1}:

\[
E_z=\bigsqcup_{d\in D_z}\{d\}\times\mathbb R^{k(d)},\qquad
\Gamma_N(E_z)=\left\{\sum_{i=1}^{n}\delta_{e_i}:0\le n\le N\right\}.
\]

These are finite counting measures, not ordinary sets: duplicate occurrences
retain multiplicity. A zero-dimensional fiber has no hidden real coordinate.
Within a one-dimensional fiber r is a log magnitude; its sign/zero/missingness
branch is encoded in d. Birth/death changes keys and count; diffusion moves only
the continuous coordinate of an existing key.

Current PhysioNet and Retail adapters keep their exact discrete values, strings,
times and branch information out of the diffused vector. Their mathematical
support is not automatically a clinically or commercially meaningful support
grammar. In particular, the current broad rational-valued atomic extension for
GCS/MechVent is not a claim of a validated clinical ordinal/binary model.

The equations can be extended to finite-dimensional Euclidean fibers, but that
extension needs vector-valued transitions, likelihoods and derivatives. It is
not a claim that the current scalar implementation already supports every such
domain. A public general interface should require an adapter to supply:

- Valid key construction, canonical serialization, equality and fiber dimension.
- A normalized, sampleable, full-support reference mass on those keys.
- Forward/observation transitions and evaluation of their declared densities.
- Reversible chart/materialization rules and a metric on the actual data object.
- Declared scientific caps and separate computational refusal limits.

This defines a reusable family, not a promise of arbitrary-data support.

## 3. A reference law and reference corruption process

Choose rho_z(d)>0 with sum_d rho_z(d)=1 and standard Gaussian probability
phi_k on each fiber. The event reference is

\[
\nu_z(d,dr)=\rho_z(d)\phi_{k(d)}(dr).
\]

An optional TRAIN-informed reference is
rho_z=(1-beta_R)rho_TRAIN+beta_R rho_universal, with 0<beta_R<1.
Its empirical frequencies use complete TRAIN keys only; it does not reduce
support to the training vocabulary. Unseen complete keys can still have
extremely small reference mass. Full support alone is not an efficiency claim.

With theta>0, define

\[
Z_N(\theta)=\sum_{n=0}^{N}\frac{\theta^n}{n!},\qquad
p_N(n)=\frac{\theta^n}{n!\,Z_N(\theta)},\qquad
\Pi_N=\sum_{n=0}^{N}p_N(n)(S_n)_\#\nu_z^{\otimes n},
\]

where S_n forgets labels but preserves occurrences. This is a Poisson reference
conditioned on its total count being at most N, not a clipped Poisson draw.
The quotient factorial and duplicate factorials are essential.

Let forward time be s in [0,S], x=sum_i delta_(d_i,r_i), and beta=theta delta
with delta>0. The selected reference has no replacement/global-refresh term:

\[
\begin{aligned}
L_sF(x)={}&\gamma_C(s)\sum_{i:k(d_i)=1}
\left[-\tfrac12r_i\partial_iF+\tfrac12\partial_i^2F\right]\\
&+\gamma_J(s)\beta\mathbf1_{\{|x|<N\}}\int[F(x+\delta_e)-F(x)]\nu_z(de)\\
&+\gamma_J(s)\delta\sum_i[F(x-\delta_{e_i})-F(x)].
\end{aligned}
\tag{1}
\]

Nonnegative clocks have finite integrals. A declared clean hold [0,s_hold]
sets both clocks to zero. Equation (1) is reversible with respect to Pi_N:
Gaussian integration by parts handles the fibers, and the capped Mecke
identity balances one birth with removal of one occurrence. Its reference jump
intensity is bounded by gamma_J(s)(beta+delta N). The proof plan gives the
assumptions explicitly; this does not establish a mixing time.

## 4. Training target and observation task are explicit modeling choices

### 4.1 Smoothed training target

Let P_TRAIN=sum_l w_l delta_(x_l) be an explicitly supplied finite training
population at the declared context. Keep each source key unchanged. Replace
every continuous coordinate mu by mu+tau Z, independently before forgetting
occurrence labels, with 0<tau<1. This defines L_l^tau and

\[
Q_{\rm lift}=\sum_lw_lL_l^\tau,\qquad
Q_0=(1-\alpha)Q_{\rm lift}+\alpha\Pi_N,\quad 0<\alpha<1.
\tag{2}
\]

The current oracle selects sources uniformly; arbitrary normalized weights in
(2) are a mathematical family, not an implemented arbitrary-weight API.

Equation (2) is not the raw empirical law. Jitter changes magnitudes, and the
reference component changes count and key probabilities. Alpha and tau are
scientific regularizers and cannot be described as harmless numerical fixes.

For a source occurrence j, write ell_j=dL_j/dnu for its one-event lifted density.
For a candidate configuration y with the same count n, the source component has

\[
\frac{dL_l^\tau}{d\Pi_N}(y)=
\frac{1}{p_N(n)n!}
\sum_{\pi\in\mathfrak S_n}\prod_{j=1}^{n}\ell_j(e_{\pi(j)}).
\tag{3}
\]

Different counts or unmatched key multiplicities give zero. The empty-source
density is Z_N. Equal-key permanents calculate (3), including repeated atomic
occurrences. For a finite roster and 0<tau<1, the density
f_0=dQ_0/dPi_N is positive, bounded and twice differentiable within fibers;
in particular f_0>=alpha. Tiny key masses and small regularizers can make the
bounds large. Positivity does not make large permanents cheap.

### 4.2 Dominated noisy half-thinning

Independently retain each occurrence with p=1/2. Retained discrete keys stay
exact. A retained continuous coordinate r emits a=r+sigma Z, sigma>0; a
zero-dimensional atom emits itself. This replaces the old exact continuous
identity channel, rather than pretending it had a Gaussian-relative density.

The one-event observation density with respect to eta=nu is

\[
q((d',a)\mid(d,r))=
\frac{\mathbf1_{\{d'=d\}}}{\rho_z(d)}
\frac{\phi_\sigma(a-r)}{\phi_1(a)}
\tag{4}
\]

in a one-dimensional fiber and indicator/rho_z(d) in a zero-dimensional fiber.

Let C_M retain observations of count at most M and map larger counts to an
explicit overflow atom dagger. Set lambda=(C_M)_#PPP(eta), with unit intensity.
The complete observation kernel is the **whole-observation** mixture

\[
K_\epsilon=(1-\epsilon)K_{\rm clean}+\epsilon\lambda,\qquad
g_\epsilon(a\mid x)=(1-\epsilon)g_{\rm clean}(a\mid x)+\epsilon,
\quad0<\epsilon<1.
\tag{5}
\]

For a retained observation with k occurrences,

\[
g_{\rm clean}(a\mid x)
=e\,p^k(1-p)^{|x|-k}
\sum_{\mu:\{1,\dots,k\}\hookrightarrow\{1,\dots,|x|\}}
\prod_jq(o_j\mid e_{\mu(j)}).
\tag{6}
\]

There is no extra k! outside the injection sum. Overflow uses
Pr{Bin(|x|,p)>M}/lambda({dagger}). This is a defined observation outcome, not
a resource failure. Retained-empty and overflow are different observations.

All comparators receive the same (2) and (5). Held-out truths remain raw;
their observations are drawn from the declared amended channel. The original
raw F105 scoring formula is unchanged. Unconditional target-shift bounds do
not automatically control conditional error, especially for rare observations.

## 5. Learn a BASE reverse potential

Let Q_s=Q_0 P_(0,s) be reference-corrupted data, with f_s=dQ_s/dPi_N. Under
the stated reversal regularity, the ideal reverse coefficients at u=S-s use
V_s^*=log f_s:

\[
b_i^*=\gamma_C(s)(-\tfrac12r_i+\partial_iV_s^*),\qquad
q_u^*(x,dy)=\gamma_J(s)q_0(x,dy)e^{V_s^*(y)-V_s^*(x)}.
\tag{7}
\]

Here q_0 is the birth/death kernel without gamma_J. Exact reversal starts from
Q_S, not automatically Pi_N. The implemented candidate starts at Pi_N and
therefore has a terminal-initialization approximation unless Q_S=Pi_N or that
error is otherwise controlled.

Fit a shared permutation-invariant energy V_phi using actual reference
corruptions X_s~Q_s. The active-time population objective is

\[
\begin{aligned}
\mathcal L_{\rm BASE}(V)={}&
\mathbb E_{s,X_s}\gamma_C(s)\sum_{i:k(d_i)=1}
\left[\tfrac12(\partial_iV)^2+\partial_i^2V-r_i\partial_iV\right]\\
&+\lambda_J\mathbb E_{s,X_s}\gamma_J(s)
\int q_0(X_s,dy)
\left[e^{V(s,y)-V(s,X_s)}+V(s,y)-V(s,X_s)\right].
\end{aligned}
\tag{8}
\]

Lambda_J>0 is a declared objective weight, not a rate multiplier applied twice.
One normalized reference edit can estimate the integral only when multiplied
by the unnormalized exit rate. The linear jump term has a positive sign.

The BASE excess-risk identity in the proof plan explains what (8) targets.
It does not establish representability, optimization success or a finite-data
generalization guarantee. The energy class is bounded; declaring an ideal
optimizer does not prove it contains log f_s.

After BASE optimization, freeze its parameters. Write P^phi for the ideal
continuous-time candidate path law initialized at Pi_N and P^(phi,Delta) for
the implemented numerical path law. Neither symbol means Q_0 or the raw data
posterior. These distinctions are needed in every subsequent conditional claim.

## 6. Association guide, conditional learner and two competing methods

### 6.1 What the analytic guide is exact for

Let h_tilde_u(x,a) be the propagation of g_epsilon under the **uncapped**
independent birth/death-OU reference, evaluated at capped x. It is not the
capped reference semigroup or the learned BASE conditional likelihood.

For remaining integrated clocks J and C, set

\[
A=e^{-\delta J},\quad a_C=e^{-C/2},\quad D=pA,\quad K=p\theta(1-A).
\]

Each present occurrence can explain at most one observation. In a continuous
matching edge the factor is

\[
\zeta_i(o_j)=\frac{D\mathbf1_{\{d_i=d_j\}}}{\rho_z(d_j)}
\frac{\phi_{\sqrt{\sigma^2+1-a_C^2}}(o_j-a_Cr_i)}{\phi_1(o_j)}.
\]

The atomic version omits the Gaussian ratio. A missed source contributes
1-D. An unexplained observation contributes K q_bar(o_j), where q_bar is
the normalized stationary noisy immigrant mark ratio. Summing products over
partial one-to-one matchings and multiplying by exp(1-K) gives the clean guide;
then mix once with epsilon. Equal-key groups factor the matching polynomial.
At zero remaining clocks, h_tilde=g_epsilon exactly.

The same law provides a reference posterior initializer without demanding that
an unconditional rare-key proposal happens to hit every observed key. The
retained case samples observed ancestors and an independent unobserved Poisson
population, conditioning their **combined** count on <=N; overflow has its own
count-posterior law. Count conditioning is not truncation or deletion.
The explicit formulas and implementations are linked in Section 9.

### 6.2 Joint/product classifier

For one fixed context and time u, draw two independent learned BASE trajectories.
The positive example uses (Y_u^(1),A^(1)), with A^(1) drawn from the observation
kernel at the first terminal state. The negative example replaces only the
observation by A^(2), generated from the second trajectory. Do not shuffle
across different contexts.

For a single common BASE path law, define

\[
h_u^\phi(x,a)=\mathbb E[g_\epsilon(a\mid Y_S)\mid Y_u=x],\qquad
m^\phi(a)=\mathbb E[g_\epsilon(a\mid Y_S)].
\]

The unrestricted equal-prior logistic optimum is

\[
\ell^*(u,x,a)=\log h_u^\phi(x,a)-\log m^\phi(a).
\tag{9}
\]

The two implemented heads share a bounded residual and observation-only nuisance:

\[
\begin{aligned}
a_R(u)&=\left[\frac{\max\{S-u-s_{\rm hold},0\}}{S-s_{\rm hold}}\right]^3,\\
\ell_{\theta,\psi}^{\rm G+R}&=\log\widetilde h_u+a_R(u)R_\theta(u,x,a,z)+c_\psi(a,z),\\
\ell_{\theta,\psi}^{\rm DIR}&=\log g_\epsilon(a\mid x)+a_R(u)R_\theta(u,x,a,z)+c_\psi(a,z).
\end{aligned}
\tag{10}
\]

Train with

\[
\mathcal R(\ell)=\tfrac12\mathbb E_{\rm joint}\operatorname{softplus}(-\ell)
+\tfrac12\mathbb E_{\rm product}\operatorname{softplus}(\ell).
\tag{11}
\]

The encoder consumes complete exact key/context bytes and occurrences, but its
fixed-width learned representation is not guaranteed injective. Equation (11)
therefore fits a risk projection unless the model class contains (9).
The nuisance is intended to absorb an observation-only normalizer and is
excluded from physical dynamics and initialization. Its individual value is
not identified by the classifier risk: state-independent offsets can move
between the nuisance and residual wherever the residual class permits.

**Unresolved numerical law issue.** Current full-time training inserts the
sampled u into both trajectory grids before simulation. The resulting family
P^(phi,Delta(u)) can have terminal evidence m_u(a) depending on u. Its pointwise
Bayes logit is log h_u^(Delta(u))-log m_u, not necessarily (9) with a common m.
The observation-only nuisance cannot by itself absorb a genuinely time-varying
normalizer, but the residual can absorb a state-independent time offset where
its gate and bound permit. Thus this is an unestablished joint representability
condition, not a categorical impossibility result for the whole architecture.
A common fixed-grid/time law or a reviewed time-aware nuisance are concrete
alternatives, with the tradeoffs in the proof plan. Current smoke/parity passes
do not settle the issue.

A second expressivity condition is that the desired residual divided by a_R
remains bounded near the hold boundary. Exact zero residual *on* the hold does
not imply cubic decay *toward* it. Without that condition, (10) remains a
restricted approximation class; no theorem should silently assume it is exact.

## 7. Conditional sampling is an approximation, not a proof by construction

Define h_hat=h_baseline exp(a_R R_theta), with the baseline selected in (10).
The physical potential is

\[
W(u,x,a,z)=V_\phi(S-u,x,z)+\log\widehat h(u,x,a,z).
\tag{12}
\]

Use W in the drift/jump formulas (7). There is one residual gate and no nuisance
term. During the clean hold both process clocks vanish and BASE is extended
constantly, so the trajectory is held unchanged.

The intended initial conditional law is proportional to

\[
\Pi_N(dx)\widehat h(0,x,a,z).
\tag{13}
\]

To sample it, first use the analytic reference-posterior calculation: G+R uses
the remaining clocks at u=0 and DIR uses zero clocks, whose guide equals g.
Then apply bounded **residual-only** rejection. BASE is absent from (13) because the
candidate BASE's initial law is Pi_N; the analytic guide must not be charged
twice. In the exact h^phi case, (13) is the correct conditioned initial law for
that candidate BASE, not necessarily for the ideal reversed training law.

Implementation uses Strang splitting, stochastic Heun continuous motion and
repeated midpoint-frozen birth/death thinning. A fixed step size, finite entropy,
rounded arithmetic, resource refusals and approximated h each affect the
returned numerical law. Calling this an exact conditional sampler is unjustified.

For an exact continuous-time BASE and its exact backward-harmonic h^phi,
the familiar Markov conditioning construction yields the conditioned candidate
path law. The current learned restricted head and discretized simulator do not
automatically inherit that result. The retired C17 path-KL claim is not revived.

## 8. Reader-facing algorithm and first scientific experiment

**Training.**

1. Declare a valid domain adapter, TRAIN-only reference, scientific caps,
   context scheme, target regularization and observation parameters.
2. Train BASE with (8): sample a lifted/regularized target, reference-corrupt
   it to an active time, then evaluate its continuous and edit objective.
3. Freeze BASE. Declare the time/path-law contract for conditional examples.
   The current query-refined mixture is a well-defined empirical risk; resolve
   its Section 6 representability and path-interpretation issues before
   asserting exact Bayes recovery.
4. Generate independent whole-path joint/product examples and optimize (11)
   for each head under shared target/task/architecture and declared budgets.
5. Save the config, parameters, optimizer/RNG state needed for the supported
   restart contract, and separately report scientific metrics and numerical failures.

**Sampling and evaluation.**

1. Condition on the supplied observation and context, initialize by (13), and
   simulate the declared numerical conditional process.
2. Materialize valid records with explicit numerical error/refusal reporting.
3. Score against raw truths under the shared observation task. Never smooth
   held-out truths or select only successful/easy draws without disclosing it.
4. Compare G+R with DIR and focused ablations on known-law synthetic tasks.
   Measure conditional error, calibration/coverage where defined, and total
   compute including guide, initialization and generated training paths.
5. Scale to real data only after the model/task settings and experimental
   protocol are selected; synthetic checks do not choose those scientific values.

The immediate experiment should distinguish a useful guide from one that is
merely numerically correct. Start with a tractable finite/atomic or small
continuous-fiber problem with an independently computed posterior. Then vary
association ambiguity, unseen-key frequency, count pressure and observation noise.
Report learning curves and error/cost tradeoffs. These are experiment targets,
not outcomes already obtained.

## 9. Equations-to-implementation map

| Scientific role | Current implementation |
|---|---|
| Carrier, exact keys, universal/TRAIN reference | [two_domain_factorized_state.py](../src/heterodiff/data/two_domain_factorized_state.py) |
| Target lift, dominated observations and finite oracle | [factorized_smooth_amendment.py](../src/heterodiff/theory/factorized_smooth_amendment.py) |
| Association guide and reference posterior | [factorized_association_guide_torch.py](../src/heterodiff/theory/factorized_association_guide_torch.py) |
| BASE objective (8) | [factorized_base_training.py](../src/heterodiff/experiments/factorized_base_training.py) |
| Encoder, nuisance and risk (10–11) | [factorized_conditional_training.py](../src/heterodiff/experiments/factorized_conditional_training.py) |
| Reference and learned numerical samplers | [factorized_hybrid_sampler.py](../src/heterodiff/processes/factorized_hybrid_sampler.py) |
| Whole-path training law and final sampler (12–13) | [factorized_conditional_pipeline.py](../src/heterodiff/experiments/factorized_conditional_pipeline.py) |
| Explicit-device candidate path and precision policy | [factorized_device_training.py](../src/heterodiff/experiments/factorized_device_training.py) |

A conceptual equation is not a claim that every mathematical extension is
implemented. Current typed adapters remain domain-specific. The new portable
research workflow is a separate interface milestone, not proof of arbitrary
domain support.

The selected precision candidate promotes the BASE graph to shared FP64
evaluation while retaining FP32 trainable parameters/gradients/optimizer moments.
The physical coordinate route still contains its explicit FP32 input boundary;
it is not an end-to-end FP64 simulator. These are numerical policies to record,
not changes to the scientific objective.

## 10. What is complete, and what remains

This step completes a coherent scientific specification, an implementation
crosswalk and an explicit claim/proof roadmap. Existing bounded CPU/GPU
integration and local checkpoint results are implementation evidence, not
empirical evidence that the method improves conditional generation.

Open manuscript work is now concrete: select the conditional time-law contract;
justify or relax the head/gate approximation claims; finish independent proof
review; establish novelty against the closest methods; build known-law
comparisons; run matched scientific experiments; and publish the complete
reader reproduction route. These tasks should drive engineering work, not the
reverse.
