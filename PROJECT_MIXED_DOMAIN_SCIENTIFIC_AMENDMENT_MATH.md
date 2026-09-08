# Mixed-domain scientific amendment: mathematical specification

Date: 2026-09-08.

Status: the mixed discrete/continuous structural successor is selected for
local implementation. Its numerical scientific settings, real-data admission,
large-cardinality numerical qualification and prospective empirical protocol
are not selected or certified by this note. This is an additive amendment, not
a reinterpretation or deletion of the historical frozen CPU evidence.

The selected repair has three inseparable parts: a countable discrete-metadata
reference with genuine continuous fibers, a dominated noisy-observation
successor, and an explicitly smoothed/regularized training target. It preserves
raw held-out truths and the F105 scoring formula. It changes both the modeled
training target and the observation task; those changes must be shared by all
comparators and disclosed in the scientific method.

## 1. What is being repaired

The exact domain maps in
`manuscript_v3/manuscript_v3_f105_metric_integration_successor_v2.md` are
injective scoring representations. Arbitrary points in R112 or R10 are not
valid generated records. One-hot indicators, missingness, discrete times,
UTF-8 identities and integer quantities cannot be repaired by rounding a
Gaussian vector to a convenient record.

The frozen kernel in
`PROJECT_TWO_DOMAIN_GOVERNANCE_RELEASE_CONTROLS.md` retains occurrences
independently with probability one half and leaves retained fields unchanged.
Its continuous identity component is singular relative to an atomless
Gaussian observation reference. Mixing this singular kernel with a positive
reference component does not remove that singular mass. Separately, an
empirical distribution of exact positive magnitudes is atomic, so it has no
Gaussian-relative density during a zero-clock clean hold. Correcting only
the observation kernel would leave this second mismatch intact.

This note specifies a coherent successor to both contracts. No assertion that
the successor is numerically or scientifically equivalent to the predecessor
is made.

## 2. Event carrier and a normalized countable reference

Fix a domain and an explicitly supplied static context. Let D be its countable
set of complete, valid discrete event keys. Each key d has fiber dimension
k(d) in {0,1}. The event carrier is the disjoint union

    E = disjoint_union over d in D of {d} x R^{k(d)}.

An empty fiber has one point, not a hidden auxiliary Gaussian coordinate.
For a one-dimensional fiber, r is the log magnitude: a positive value is
exp(r), and a negative Retail price is -exp(r). Zero and missingness are
different zero-dimensional atoms. No diffusion is applied to type names,
times, masks, strings, signs or integer quantities.

The PhysioNet key contains exact integer minute, parameter and the required
missing/zero/continuous-branch information. GCS and MechVent values are kept
fully atomic. In this initial semantic carrier, their present numeric values
range over exact nonnegative rationals. This does not invent a GCS roster or
claim that arbitrary rational MechVent/GCS values are clinically meaningful.
It is the broader numeric semantic extension of the current F105 contract;
clinical-support claims would require a separately justified support grammar.
It must never be described as a validated binary/ordinal generative model.

The Retail key contains exact invoice token and its derived cancellation bit,
stock token, optional description, signed integer quantity, source-civil
microsecond, optional country, and price zero/sign branch. Group identity and
static context are not generated event coordinates. Original occurrence
multiplicity is retained.

Choose a normalized probability mass rho on D with rho(d)>0 for every key.
It is generated and evaluated from a valid-field grammar, not from an
enumerated type table or the vocabulary observed in a training sample:

- Finite legal rosters and exact finite time-index sets have positive
  normalized masses.
- Optional absence and present-empty strings are distinct grammar outcomes.
  A byte-budgeted UTF-8 grammar chooses only legal Unicode scalars fitting
  the remaining budget, has positive stop/continuation probabilities when
  allowed, and forces a first scalar for required nonempty fields. Summing
  over its finite stopping tree proves normalization and full support on the
  declared byte-bounded legal strings. It does not normalize invalid bytes.
- An unbounded signed integer has a normalized full-support integer law, for
  example a length law followed by a normalized conditional sign/magnitude
  law. A finite implementation resource limit must refuse, not renormalize
  this law onto a smaller observed range.
- Atomic nonnegative rationals use a unique canonical integer code and a
  normalized full-support code law. Unreduced numerator/denominator pairs
  cannot be assigned mass as though they were different rational values.
  A canonical continued-fraction or equivalent unique tree code is suitable
  only with a proved normalization of its stopping and digit laws.

Dependencies such as cancellation derived from the invoice are deterministic
grammar rules, not independently sampled potentially contradictory fields.
Exact-key equality, rather than equality of a lossy FP32 feature vector,
determines identity. Very small rho values are not rounded up to a floor.
There need not be a positive global minimum over the countably many keys.

The selected train-informed extension of this family is

    rho_beta_R(d) = (1-beta_R) rho_train(d) + beta_R rho_universal(d),
    0 < beta_R < 1.

Here rho_universal is the normalized full-support grammar above, and
rho_train(d)=C_d/T is the exact complete-key occurrence frequency over an
explicitly supplied TRAIN-only roster with T>0 total occurrences. The roster,
frequency definition and beta_R are shared and frozen across methods before
outcomes. Beta_R is a reference-mixture weight, not the birth rate beta below.
This remains normalized and satisfies rho_beta_R(d)>=beta_R rho_universal(d)>0;
it is not an observed-only vocabulary. The numerical beta_R and any actual
real-data empirical mass table are not selected by this note. The
[reference module](src/heterodiff/data/two_domain_factorized_state.py) now
implements both the universal law and this TRAIN-informed mixture on an
explicitly supplied nonempty roster, with exact rational beta/frequencies and
variable-bit mixture/index selection. Synthetic tests do not authenticate a
caller's TRAIN/no-leakage declaration or supply an admitted real-data roster.
A missing or empty training roster is not silently invented to fit a mixture.

This modification moderates inverse masses for complete keys seen in TRAIN.
It does not solve conditioning on unseen complete keys: such a key has mass
beta_R rho_universal(d). In particular, held-out Retail invoices/times can
make complete-key overlap absent even when individual fields are common.
No validation/test frequencies may be used to fix this difficulty, and no
claim of efficient posterior initialization follows from the mixture alone.

Let phi_k be standard Gaussian probability on R^k, with phi_0 a point mass.
The normalized event reference is

    nu(d, dr) = rho(d) phi_{k(d)}(dr).

No enumeration of D is needed to sample a key from its grammar. Ideal
normalization/full support is distinct from exact sampling by a finite-state
PRNG, finite binary64 representability, and finite memory/runtime. Those
implementation approximations or refusals remain explicitly reported.

### 2.1 Quotient configuration normalization

Let Gamma_N(E) contain counting measures with 0<=n<=N, preserving duplicates.
Write S_n for the map from an ordered n-tuple to its counting measure. For
theta>0 define

    Z_N(theta) = sum_{n=0}^N theta^n/n!,
    p_N(n) = theta^n / (n! Z_N(theta)),
    Pi_N = sum_{n=0}^N p_N(n) (S_n)# nu^{tensor n}.

This is the Poisson reference conditioned on count<=N, not a clipped Poisson
sample. The empty configuration has probability 1/Z_N. If the event reference
is purely atomic at a configuration with multiplicities m_e, its probability
is theta^n/Z_N times product_e nu({e})^{m_e}/m_e!. Thus the n! quotient and
the repeated-occurrence factorials are not interchangeable or optional.

The existing domain configuration caps are not reduced by this definition.
An oracle's small test limit is not a new scientific cap or a license to
discard rows or groups.

## 3. Initial reference process: birth/death plus within-fiber OU

The initial successor selects replacement/refresh rate kappa=0. Birth and
death already connect the configuration space through the empty state;
global refresh is not needed merely to obtain irreducibility. This is a
declared change from a predecessor with nonzero replacement, not an assertion
that the generators are equal.

For a suitable symmetric test function F and x=sum_i delta_{(d_i,r_i)}, use

    L_s F(x)
      = gamma_C(s) sum_{i:k(d_i)=1}
          [-r_i/2 * partial_i F(x) + (1/2) partial_i^2 F(x)]
        + gamma_J(s) beta 1_{n<N} integral [F(x+delta_e)-F(x)] nu(de)
        + gamma_J(s) delta sum_{i=1}^n [F(x-delta_{e_i})-F(x)],
    delta > 0, beta = theta delta.

Births draw a complete event from nu. Deaths select occurrences, including
duplicate occurrences separately. Zero-dimensional fibers have no OU term.
The clocks are nonnegative with finite integrated rates on the finite horizon.
The clean hold sets both clocks to zero on its declared physical-time segment.

The finite-count Mecke identity, with the birth term removed at n=N, gives
detailed balance of birth/death against Pi_N. Gaussian integration by parts
gives reversibility of each OU fiber. The countable key sum uses nonnegative
summation/Tonelli where applicable and finite-n fiber sums. This derives the
reference invariance/reversibility, subject to the stated generator domain.
The jump intensity is at most gamma_J(s)(beta+delta N), so finite integrated
clocks give nonexplosion of the capped reference jump part. Active death/birth
paths and full-support nu give support irreducibility; this is not a
mixing-time, spectral-gap or usable finite-budget sampling guarantee.

With reverse time u and physical time s=S-u, a smooth log-potential V gives
the intended transformed coefficients

    drift_i = gamma_C(S-u) [-r_i/2 + partial_i V],
    diffusion_i = sqrt(gamma_C(S-u)),
    q^V_u(x, dx') = gamma_J(S-u) q_0(x, dx') exp(V(u,x')-V(u,x)).

There is no extra one-half on the gradient correction. Coordinate gradients
exist only within their current fibers; birth/death handles changes of key
and dimension. The zero-clock reverse segment is identity. Bounded potential
differences bound the tilted jump intensity. These formulas do not by
themselves complete a countable-fiber Girsanov/path-KL theorem: generator
domains, integrability, absolute continuity and approximation hypotheses
still have to be checked in that theorem's actual statement.

## 4. Training-target lift and its exact reference density

Fix a finite admitted TRAINING roster x_1,...,x_L, normalized weights w_i,
and its declared context-conditioning scheme. This section does not select
a context law outside that supplied scheme or use held-out records for fitting.
For each temporary source occurrence j of x_i, keep its exact key d_ij and
replace a continuous log magnitude mu_ij by

    R_ij = mu_ij + tau Z_ij,   Z_ij independent N(0,1),  0<tau<1.

Keep every zero-dimensional atom unchanged. Push the occurrence product law
to the unordered counting measure to obtain L_i^tau. Distinct source
occurrences, even duplicates, remain distinct factors before this quotient.
Select the target family

    Q_lift = sum_i w_i L_i^tau,
    Q_0 = (1-alpha) Q_lift + alpha Pi_N,   0<alpha<1.

Alpha and tau are scientific regularization parameters, not technical
tolerances. Their numerical values are still to be frozen prospectively.
Q_0 is not the empirical raw training distribution. The reference mixture
also changes count and metadata probabilities; this target shift is explicit.

For a source occurrence define its single-event likelihood ratio ell_ij:

    ell_ij(d,r) = 1_{d=d_ij}/rho(d_ij)
                 * phi_tau(r-mu_ij)/phi_1(r)   for a 1D source,
    ell_ij(d)   = 1_{d=d_ij}/rho(d_ij)          for a 0D source.

If y has n=n_i occurrences e_1,...,e_n, its component density is

    dL_i^tau/dPi_N(y)
      = [1/(p_N(n) n!)] sum_{pi in permutations(1..n)}
            product_j ell_ij(e_{pi(j)}).

It is zero for another count or unmatched key multiplicities. Equivalently,
the prefactor is Z_N/theta^n. In the empty case the density is Z_N. The
permutation sum factors into one permanent per exact-key group; there is no
additional group factorial after those permanents. In particular, repeated
atomic occurrences must still contribute their multiplicity factorial. This
is the exact normalization used to audit a finite fixture oracle, not a claim
that large per-key permanents can be computed economically.

For a continuous source occurrence,

    sup_r phi_tau(r-mu)/phi_1(r)
       = tau^{-1} exp(mu^2/[2(1-tau^2)]) < infinity.

The ratio and its first two derivatives are bounded for fixed finite mu and
0<tau<1. Each observed key has positive rho; a finite source roster therefore
has a finite upper bound on its component densities and fiber derivatives,
even though inf_d rho(d)=0 is allowed. Consequently

    f_0 = dQ_0/dPi_N = alpha + (1-alpha) sum_i w_i dL_i^tau/dPi_N

is at least alpha, bounded above, and twice continuously differentiable with
bounded first/second derivatives on each finite configuration fiber. Its log
derivatives are bounded on those fibers as a consequence of f_0>=alpha.
The reversible Markov semigroup preserves the lower and upper density bounds.
Any stronger uniform derivative or pathwise regularity claim must use the
appropriate semigroup/domain argument, not just positivity.

This repairs the empirical-density mismatch even during the clean hold:
the held density is f_0, not an atomic empirical law disguised as a Gaussian
density. Restricting training times beyond the hold could smooth continuous
marks, but it would not preserve the same endpoint/clean-hold contract or
automatically supply the same global positivity and derivative bounds.

## 5. Minimal dominated observation successor

The successor retains the half-detection probability p=1/2 and exact discrete
keys, but changes the observation channel on continuous fibers. A detected
one-dimensional occurrence emits a=r+sigma Z with sigma>0; a detected
zero-dimensional occurrence emits its same atom. There is no initial clutter
or type confusion. This is noise in the log-value chart, not jitter of physical
time or a Gaussian perturbation of an entire F105 vector.

Use eta=nu as the one-event observation reference. The channel RN factor is

    q((d',a)|(d,r))
      = 1_{d'=d}/rho(d) * phi_sigma(a-r)/phi_1(a)    in 1D,
    q(d'|d) = 1_{d'=d}/rho(d)                      in 0D.

It integrates to one against eta. Atomic identity is now dominated because
rho(d)>0; continuous identity has actually been replaced by sigma>0 noise.
Tiny exact-key masses can make a fixed-observation RN factor large, but
never justify clipping that factor or silently deleting a key.

Let the observation collapse C_M preserve counts<=M and map larger counts to
one explicit overflow atom dagger. Define lambda=(C_M)#PPP(eta), with unit
Poisson intensity. It is a normalized whole-observation reference. Its
overflow mass is

    lambda_dagger = 1 - exp(-1) sum_{k=0}^M 1/k! > 0.

M must be explicitly declared. Collapsing after computing the complete
sampled count is part of this observation law, not a runtime truncation.
For a retained observation a=sum_{j=1}^k delta_{o_j} and latent count n,

    g_clean(a|x)
      = e * p^k (1-p)^(n-k)
          sum_{injective mu:{1..k}->{1..n}} product_j q(o_j|e_mu(j)),

with zero when k>n. There is no extra k! outside the injection sum. Identical
observed values still represent separate occurrences. For k=0 the value is
e(1-p)^n; the empty latent state has only a clean empty observation.
At dagger the clean density is Pr{Bin(n,p)>M}/lambda_dagger.

The complete kernel is the whole-observation mixture

    K_epsilon = (1-epsilon) K_clean + epsilon lambda,
    g_epsilon = (1-epsilon) g_clean + epsilon,   0<epsilon<1.

It is normalized and g_epsilon>=epsilon for retained and overflow outputs,
including an empty latent state. Epsilon is not applied independently to
each retained event. Its numerical value and sigma remain scientific
settings to be selected before outcomes; the mixture changes the task.

## 6. Exact independent-reference guide for kappa=0

The following guide uses the UNBOUNDED independent birth/death-OU reference,
then is evaluated at a capped latent state. It is not the exact propagated
likelihood of the capped reference or the learned base model. A cap-defect
term and the existing guide-residual distinction are not erased.

From reverse time u to S, define integrated physical clocks

    J = integral_u^S gamma_J(S-v) dv,
    C = integral_u^S gamma_C(S-v) dv,
    A = exp(-delta J),  a_C = exp(-C/2),
    D = p A,           K = p theta (1-A).

Each current occurrence survives with probability A; if detected, its key is
unchanged. Its terminal continuous coordinate has mean a_C r and variance
1-a_C^2. Combining this with the observation noise gives the matched factor

    zeta_i(o)
      = D * 1_{d_o=d_i}/rho(d_i)
          * phi_{sqrt(sigma^2+1-a_C^2)}(o-a_C r_i)/phi_1(o)   in 1D,
    zeta_i(o) = D * 1_{d_o=d_i}/rho(d_i)                     in 0D.

The missed-source factor is 1-D. Future immigrants surviving to terminal
time form a Poisson population with mean theta(1-A); their detected
observations form a Poisson background with mean K. This background is
present in the propagated guide even though the terminal observation kernel
has no initial clutter. Its normalized mark RN factor is

    q_bar(d,o) = phi_{sqrt(1+sigma^2)}(o)/phi_1(o)   in 1D,
    q_bar(d) = 1                                 in 0D.

The rho factors cancel in this stationary immigrant marginal. The clean
guide for retained observations is

    h_tilde_clean(u,x,a) = exp(1-K)
      * sum over partial one-to-one source/observation matchings M of
          [product_(i,j) in M zeta_i(o_j)]
          [product_unmatched_sources i (1-D)]
          [product_unmatched_observations j K q_bar(o_j)].

Only equal-key edges can match. The partial-matching polynomial therefore
factors over exact-key groups, with the global exponential included once.
There is neither an extra observation k! nor an extra source factorial.
The countable key sum in q_bar collapses to the one matching key; no finite
type enumeration is required. The per-key matching complexity is still real.

At overflow,

    h_tilde_clean(u,x,dagger)
      = Pr{Bin(n,D) + Pois(K) > M}/lambda_dagger.

Finally h_tilde_epsilon=(1-epsilon)h_tilde_clean+epsilon. At u=S, and throughout
an entirely zero-clock remaining segment, J=C=0, A=a_C=1 and K=0, so this
reduces exactly to g_epsilon. This clean-hold reduction must also be tested
in code; a numerically inserted active clock is not permitted.

### 6.1 Fixed-observation bounds without a minimum key mass

For a retained fixed observation o_j set

    B_j = 1/rho(d_j)                                          in 0D,
    B_j = 1/[rho(d_j) phi_1(o_j) sqrt(2*pi*sigma^2)]            in 1D.

These are finite bounds on q(o_j|e) over latent e. Thus, for k observations,

    g_clean(a|x)
       <= e (n)_k p^k(1-p)^(n-k) product_j B_j
       =  e k! Pr{Bin(n,p)=k} product_j B_j
       <= e k! product_j B_j.

This bound holds even for unbounded n, so conditional expectation gives the
same bound on h_tilde_clean. Both epsilon-mixture densities lie between
epsilon and epsilon+(1-epsilon)e k! product_j B_j. At dagger replace the
clean upper bound by 1/lambda_dagger. These are fixed-observation bounds,
not a finite constant uniform over every possible observation and key.
Gaussian derivative envelopes support bounded finite-fiber differentiation;
any interchange of derivative and expectation still requires its stated
domination argument. Tiny overflow masses and large bounds remain genuine
numerical obstacles, not certified by their theoretical finiteness.

### 6.2 Retained-observation stationary-reference posterior initializer

The following ideal-law derivation gives a concrete next implementation
without rejection on rare metadata. It is not implemented by the present
oracle and is not the learned-base or Q_0 posterior. Let the latent prior at
u first be the UNBOUNDED stationary PPP(theta nu). Use a retained observation
a with k<=M anchors and the independent-reference guide from Section 6.

Poisson thinning and superposition imply that the clean terminal observation
is PPP(p theta nu_bar), where dnu_bar/dnu=q_bar. Its evidence relative to the
retained part of lambda is therefore

    m_clean,infinity(a)
      = exp(1-p theta) (p theta)^k product_j q_bar(o_j).

Given this clean observation, each anchor independently has an ancestor in
the population at u with probability A. Its key is copied exactly from that
anchor; it is not rediscovered by an unconditional draw from rho. For a 1D
anchor with coordinate o, that ancestor's coordinate has the Gaussian law

    N(a_C o/(1+sigma^2), 1-a_C^2/(1+sigma^2)).

A 0D ancestor is its exact atom. Independently add the current occurrences
that generate no retained terminal observation: they form

    PPP(theta(1-p A) nu).

These claims follow by splitting the observed terminal process into
current-survivor intensity p theta A and future-immigrant intensity
p theta(1-A), which have the same stationary noisy mark law. The conditional
ancestry probability is thus A. The Gaussian formula is the ordinary
conditional law with Var(r_u)=1, Var(o)=1+sigma^2 and Cov(r_u,o)=a_C.
Every duplicate observed occurrence receives its own ancestry indicator.

The resulting latent count has law

    H_a = Bin(k,A) + Pois(theta(1-p A)),

with independent summands. Define

    c_prior = Pr{Pois(theta)<=N},
    c_a = Pr{H_a<=N}.

The clean posterior for the ACTUAL initial prior Pi_N weighted by
h_tilde_clean is this unbounded clean posterior conditioned on its TOTAL
count being <=N. Do not condition or clip the two count components
separately. Its clean evidence is

    m_clean,N(a) = m_clean,infinity(a) c_a/c_prior.

In particular, c_a can be zero at an endpoint when all k>N anchors would
require ancestors; that is a genuinely impossible clean branch, not a reason
to delete the positive epsilon branch. The complete epsilon-mixture evidence
and posterior clean-branch weight are

    m_epsilon,N(a) = epsilon + (1-epsilon) m_clean,N(a),
    w_clean(a) = (1-epsilon) m_clean,N(a) / m_epsilon,N(a).

With probability w_clean use the count-conditioned clean posterior above;
with the complementary probability use Pi_N itself, because the whole-
observation epsilon component is independent of the latent state. This
targets exactly the ideal reference-weighted initial law

    Pi_N(dx) h_tilde_epsilon(u,x,a) / m_epsilon,N(a).

It does not require a rare observed key to appear in a prior proposal.
Efficient/accurate capped-count sampling, tiny tail/evidence evaluation,
overflow-observation conditioning, finite-RNG qualification and any subsequent
bounded learned-residual acceptance step remain subsequent implementation
work. None is certified by this retained-observation derivation.

## 7. Quantifying, rather than hiding, the target shift in F105

The frozen F105 event kernel is exp(-||J(e)-J(e')||^2/2), and its nonempty
event channel is the mean with normalization 1/n, NOT 1/(1+n). Count scale,
event scale, event bandwidth and outer bandwidth are all exactly one in the
accepted instance. The 1/(1+n) normalization used by a trainable encoder is
not the F105 metric definition.

For clarity write event bandwidth ell_E, outer bandwidth ell_G and event
embedding scale b in this derivation; set all three to one for actual F105.
A single continuous log-magnitude perturbation t changes only one numeric
coordinate of J. The derivative of exp(r)/(1+exp(r)), or its negative Retail
counterpart, has absolute value at most 1/4. The Gaussian event feature map
therefore satisfies

    ||psi_E(e_r)-psi_E(e_{r+t})|| <= |t|/(4 ell_E).

The Gaussian outer feature map is 1/ell_G-Lipschitz in its Hilbert argument.
Couple each raw configuration to its lifted version with the same count and
metadata. If n_c denotes its number of continuous occurrences, Jensen and
the triangle inequality give

    MMD_F105(P_raw, Q_lift)
      <= [b tau sqrt(2/pi)/(4 ell_E ell_G)]
         E_P[1_{n>0} n_c/n]
      <= b tau sqrt(2/pi)/(4 ell_E ell_G).

Here P_raw is the weighted finite training empirical law, not an unknown
population distribution. Atomic-only configurations incur zero lift error.
The count channel contributes no difference under this lift coupling.
For the normalized nonnegative outer Gaussian kernel, any two probability
embeddings are at distance at most sqrt(2). Hence

    MMD_F105(P_raw, Q_0)
      <= (1-alpha) b tau sqrt(2/pi)/(4 ell_E ell_G) + alpha sqrt(2).

This is an unconditional ideal-law bound. The real-valued inverse chart uses
the continuous extension of the unchanged F105 formula. A finite binary64
record materializer introduces its own representation/refusal error; the old
exact source/metric certificates are not silently extended to that numerical
approximation. No assertion is made that an arbitrary real exp(r) is an exact
source decimal or an exactly represented generated binary64 value.

The family alpha,tau -> 0 converges to the finite empirical law under the
natural disjoint-fiber topology and in this bounded-kernel MMD: couple the
Gaussian jitter to tend to zero and let the contamination mass vanish.
This is not population consistency, a finite-sample guarantee, or a claim
that training/reversal approximation vanishes. Moreover the density bounds
and log-derivative constants can deteriorate as alpha or tau tends to zero.

### 7.1 Conditional and score implications

The same unconditional bound must not be relabeled as a conditional bound.
For a fixed observed a, let g=g_epsilon(a|.)<=B(a), let z_P=E_P g, and let
(X,Y) be any coupling of raw P and modeled Q. If Psi is the normalized
configuration feature map, direct numerator/denominator subtraction yields

    ||E_P[Psi(X)|a] - E_Q[Psi(Y)|a]||
      <= [B(a) E||Psi(X)-Psi(Y)|| + 2 E|g(X)-g(Y)|] / z_P,
    z_P >= epsilon.

Thus conditional target shift also depends on likelihood sensitivity and
evidence. A small unconditional MMD alone does not control this weighted
quantity; low-evidence observations can amplify error. Fiberwise Gaussian
likelihood derivative bounds can bound the second coupling term on a
declared finite setting, but that separate bound must actually be evaluated.
The raw-target population CKS excess is the squared conditional MMD only
under the matching conditional scoring law, not automatically under Q_0.

Keep validation/test target configurations RAW and unchanged. Generate their
observations from the explicitly amended K_epsilon applied to those raw
truths; do not smooth held-out truths to make a target match the model. All
methods receive the same observation task and target-lift specification.
The approximation to the raw posterior remains a scientific error source.

## 8. Numerical choices and the pre-outcome scientific comparison

The structural family is selected; alpha in (0,1), tau in (0,1), epsilon in
(0,1), beta_R in (0,1), sigma>0, theta>0 and delta>0 are not assigned empirically validated
numerical values here. Neither positivity of a theorem nor passage of a
synthetic unit test selects a scientifically appropriate noise level.
Choose and freeze a common pre-outcome sensitivity design before outcomes:

- Separate target regularization (alpha,tau) from observation/task noise
  (epsilon,sigma), and report both instead of attributing their effects to
  the learned guide.
- Specify the base target lift and reference grammar identically for the
  compared methods; select settings without held-out/test tuning. A proposal
  using multiple settings must have the same prospective selection and
  compute allocation across methods.
- Report the explicit unconditional shift bound, likelihood/evidence
  sensitivity when making conditional claims, and observed numerical
  approximation/refusal rates separately from model error.
- Retain exact row/group, split, context, occurrence and raw F105 target
  rules. No convenience vocabulary, range clip, resplit, top-up or filter is
  introduced by the countable grammar.
- Treat zero-noise/zero-contamination limits as theoretical comparisons,
  not executable settings falsely satisfying positive-density hypotheses.

This is the minimal selected successor preserving a genuine hybrid process,
a computable independent-reference guide and the same raw-record score.
It does not claim that the initial broader semantic carrier is a clinically
validated PhysioNet support model, that the old half-thinning task is still
the experiment, or that target regularization is free of scientific bias.

## 9. What the local implementation can and cannot establish

A finite synthetic oracle can check normalization, quotient factorials,
duplicate/empty behavior, equal-key matching, exact clean-hold reduction,
first coordinate gradients, target-density ratios and parameter rejection.
The present oracle uses uniform weights over its explicitly supplied training
roster; the general normalized weights above do not imply an implemented
arbitrary-weight training interface.
The current proposed oracle limits (128 latent events and 12 observed
anchors per exact-key DP group) are explicit LOCAL computation bounds, not
the full-domain caps. A refusal must not be converted into a different law.

Positive finite likelihood bounds also do not make unconditional-reference
rejection initialization efficient: a retained rare metadata key can have
extremely small reference probability, and the bounds contain its inverse.
Using the analytic matching/immigrant guide to construct a reference-posterior
initializer, followed by a bounded learned-residual correction, is a possible
subsequent algorithmic route; it is not implemented or qualified by this note.

The derivations above establish normalized mathematical laws and the stated
limited bounds. They do not establish a complete new countable-fiber
Girsanov/path-KL theorem, universal numerical certificates, scalable
full-cardinality matching, exact arbitrary-precision random sampling, real
data/support admission, a budget freeze, GPU qualification, training results,
or a scientific claim of superiority. Existing 323-file CPU source bindings
and historical receipts remain historical evidence, unchanged by this note.
