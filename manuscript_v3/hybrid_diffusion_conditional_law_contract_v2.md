# Conditional-law approximation: selected finite-grid contract v2

Date: 2026-09-13

Contract identifier: COMMON_FIXED_GRID_LINEAR_GATE_NORMALIZED_TWIST_V2

Status: selected contract for the independent finite-state mechanism benchmark.
It is not a replacement of the existing mixed-domain neural training or sampler.

The [scientific core](hybrid_diffusion_scientific_core_v1.md) distinguished the
reference, learned BASE and numerical path laws. The
[proof plan](hybrid_diffusion_claims_and_proof_plan_v1.md) identified three
unresolved issues: query-dependent numerical path laws, residual behavior near
the terminal hold, and the gap between likelihood-ratio learning and an exact
conditioned sampler. This document resolves those definitions for a separate,
independently computable benchmark and proves its finite-grid statements.
It does not claim to resolve every approximation in the full hybrid learner.

The [association and initializer appendix](hybrid_diffusion_association_initializer_proof_v1.md)
proves the normalized uncapped association guide and its cap-conditioned
initial posterior. Those results supply an analytic baseline; they do not make
that baseline the capped or learned BASE conditional likelihood.

## 1. What changes, and what stays unchanged

The new benchmark uses one fixed Markov grid, an independently computed
conditional target, a linear remaining-time residual gate and explicitly
normalized transition twists. It compares guide-only, association-aware
guide-plus-residual (G+R), and the direct conditioner (DIR) on the same law.

The old mixed-domain code remains unchanged: its query-refined trajectories,
cubic residual gate and coefficient-tilted hybrid numerical sampler retain
their existing meanings. Prior CPU/GPU parity receipts remain numerical
comparisons of those declared implementations. They are not reclassified as
proof of this new conditional-law contract or of posterior accuracy.

The finite benchmark is an atomic special case, not a smaller simulation of
PhysioNet or Retail data. It does not contain continuous OU fibers, the neural
event encoder, learned BASE training, Heun integration, or real held-out F105
scoring. Its purpose is to make conditional approximation error observable
against an independent target before attributing scientific benefit to a
large neural implementation.

## 2. A fully specified, independently computable target

### 2.1 Finite state and observation laws

Let S_N={(n_0,n_1): n_j nonnegative integers, n_0+n_1<=N}; the selected N=3
gives ten states. Equal event types retain their occurrence multiplicities.
The two-type reference probabilities are rho=(0.65,0.35). With theta>0,

\[
\mu_0(n)=\frac{1}{Z_N(\theta)}
 \frac{(\theta\rho_0)^{n_0}(\theta\rho_1)^{n_1}}{n_0!\,n_1!},
\qquad
Z_N(\theta)=\sum_{k=0}^N\theta^k/k!.
\tag{1}
\]

The capped reference generator, using row-vector distributions, has

\[
Q_{\rm ref}(n,n+e_j)=\theta\delta\rho_j\,\mathbf1_{\{|n|<N\}},
\qquad
Q_{\rm ref}(n,n-e_j)=\delta n_j,
\tag{2}
\]

with diagonals minus off-diagonal row sums and delta=0.8.
A declared bounded potential V gives the toy BASE generator

\[
Q(n,m)=Q_{\rm ref}(n,m)e^{V(m)-V(n)}\quad(n\ne m).
\tag{3}
\]

This is a fixed, exactly specified toy BASE, not an estimate fitted to data.
Its stationary law is proportional to mu_0 exp(2V), by detailed balance,
but its selected **initial** law remains mu_0 in (1). Substituting the
stationary law would change the target.

Observations independently retain each occurrence with probability p=1/2.
At most M=1 retained occurrence is displayed; larger retained counts become a
distinct overflow atom. Thus the default observation alphabet is empty,
type 0, type 1 and overflow. The reference lambda is a rate-one Poisson process
with type probabilities rho, collapsed by the same observation cap:

\[
\lambda(\varnothing)=e^{-1},\quad
\lambda(e_j)=e^{-1}\rho_j,\quad
\lambda(\dagger)=1-2e^{-1}.
\tag{4}
\]

The whole-observation channel is 0.9 times clean half-thinning plus
0.1 times lambda. The finite benchmark uses observation probabilities,
equivalently densities against counting measure on its finite observation
alphabet. For a fixed observation a, write

\[
g_a(n)=0.9\,
 \Pr\{\text{clean half-thinning of }n\text{ gives }a\}+0.1\lambda(a).
\tag{5}
\]

Every entry is positive, in particular g_a>=0.1 lambda(a). The clean probabilities can
be independently enumerated by labeling the at most three initial occurrences
and summing all retention masks. This does not require the hybrid guide code.

This convention differs from the manuscript's lambda-density:
g_probability(a|n)=lambda(a) g_RN(a|n). The same factor relates all propagated
likelihoods and evidence at fixed a. Consistent conversion cancels from
posteriors, exact and normalized transition twists, and harmonic defects.
It does not leave an initially zero-nuisance classifier logit unchanged:
to reproduce the reported optimization curves, probability-valued baselines
and the stated zero nuisance initialization must be used together.

### 2.2 One grid and one endpoint evidence

The selected grid is

\[
(t_0,t_1,t_2,t_3,t_4)=(0,1/4,1/2,3/4,1),\qquad
K_i=e^{(t_{i+1}-t_i)Q}.
\tag{6}
\]

Let mu_{i+1}=mu_i K_i. Set

\[
h_4=g_a,\qquad h_i=K_i h_{i+1},\qquad
m(a)=\mu_4g_a=\mu_i h_i.
\tag{7}
\]

The last equality follows by repeated substitution, so the same endpoint
evidence m(a)=Pr(A=a) applies at every grid time. All h_i are positive. Exact finite-CTMC
formulas define the law; matrix exponentials are evaluated in floating point.
Stochastic row sums, nonnegativity, semigroup and Bayes identities therefore
have numerical residuals that must be checked, not described as exact arithmetic.

The independent oracle is
[finite_conditional_benchmark.py](../src/heterodiff/evaluation/finite_conditional_benchmark.py).
It does not import the hybrid learner, association guide or hybrid path sampler.
The learning experiment is
[finite_conditional_learning_benchmark.py](../src/heterodiff/experiments/finite_conditional_learning_benchmark.py).

### 2.3 Which reference guide is used

G+R and guide-only use the **uncapped** independent-reference likelihood
tilde_h_i obtained from the occurrence/immigration calculation, evaluated at
the finite current state and remaining duration 1-t_i. Births during that
reference future are not capped. DIR uses the terminal likelihood g_a at
every time as its analytic baseline.

Here tilde_h is the probability of the fixed observation, namely lambda(a)
times the appendix's lambda-density guide. The finite oracle's
observation_likelihood, uncapped_reference_likelihood and
capped_reference_likelihood all use that same probability convention.

The oracle also computes the capped-reference likelihood
exp((1-t_i)Q_ref)g_a, but only as a cap-defect diagnostic. It is not silently
substituted for the uncapped association guide. There are consequently three
distinct arrays:

- Uncapped reference guide tilde_h_i.
- Capped reference likelihood exp((1-t_i)Q_ref)g_a.
- Toy BASE likelihood h_i=exp((1-t_i)Q)g_a.

Their differences isolate cap effects and BASE/reference mismatch. The
initializer appendix bounds one part of this distinction; neither reference
array is generally the target h_i for nonzero V.

## 3. Theorem: exact finite-grid conditioning and its initializer

For fixed a, define

\[
\mu_0^a(x)=\frac{\mu_0(x)h_0(x)}{m(a)},\qquad
K_i^a(x,y)=K_i(x,y)\frac{h_{i+1}(y)}{h_i(x)}.
\tag{8}
\]

Then each K_i^a is a Markov kernel. Together with mu_0^a it gives the
unconditioned grid path law tilted by g_a(X_4)/m(a). Its terminal distribution
is the independently computed posterior

\[
\mu_4^a(y)=\frac{\mu_4(y)g_a(y)}{m(a)}.
\tag{9}
\]

**Proof.** Equation (7) gives sum_y K_i^a(x,y)=1. Multiplying the initial
probability and all transition probabilities in (8) cancels every interior
h_i:

\[
\mu_0^a(x_0)\prod_{i=0}^3 K_i^a(x_i,x_{i+1})
=\mu_0(x_0)\prod_{i=0}^3K_i(x_i,x_{i+1})
 \frac{g_a(x_4)}{m(a)}.
\tag{10}
\]

Summing paths ending at y gives (9). This is ordinary finite-space Bayes
conditioning; no diffusion or gradient approximation is used. QED.

The initial tilt in (8) is essential. Correct conditional transition rows
combined with the unconditioned mu_0 generally do **not** produce (9).
Conversely, a correct conditional initializer alone does not determine the
subsequent conditional path law.

## 4. The law learned by balanced classification

At each selected preterminal time i=0,...,3, the positive and negative class
state distributions for fixed observation a are

\[
p_i^+(x)=\frac{\mu_i(x)h_i(x,a)}{m(a)},\qquad
p_i^-(x)=\mu_i(x).
\tag{11}
\]

Both normalize to one. They are the fixed-observation conditional and
unconditional state laws obtained from one common path experiment. This is
equivalent, at fixed a, to joint-versus-product classification from that
experiment; it is not classification between arbitrarily paired simulators.

With equal class probabilities and equal weights over the four times, the
population logistic objective is

\[
L(\ell)=\frac{1}{8}\sum_{i=0}^3\sum_x
 \left[p_i^+(x)\log(1+e^{-\ell_i(x)})
       +p_i^-(x)\log(1+e^{\ell_i(x)})\right].
\tag{12}
\]

Its unrestricted minimizer is

\[
\ell_i^*(x,a)=\log h_i(x,a)-\log m(a).
\tag{13}
\]

**Proof.** For each i,x, differentiate its strictly convex binary logistic
term. The stationary equation gives exp(ell)=p_i^+/p_i^-=h_i/m.
All masses are positive in the selected experiment, so this determines the
pointwise optimum. QED.

The experiment evaluates (12) by exact finite sums, not by Monte Carlo
training pairs. Finite optimization error and restricted model error remain;
finite-sample generalization is deliberately absent from this mechanism test.

### 4.1 Selected learnable parameterizations

For i<4 let a_i=1-t_i. The two physical log-likelihood approximations are

\[
\begin{aligned}
\log\widehat h_i^{\rm G+R}(x,a)
 &=\log\widetilde h_i(x,a)+a_i\,4\tanh(W_i(x,a)),\\
\log\widehat h_i^{\rm DIR}(x,a)
 &=\log g_a(x)+a_i\,4\tanh(W_i(x,a)).
\end{aligned}
\tag{14}
\]

In both cases hat_h_4=g_a is pinned exactly. The classifier adds one
observation-only, time-independent scalar c(a) to log hat_h_i.
That nuisance scalar is not inserted into the physical transition or initial
law. Each observation has its own FP64 table and scalar in this benchmark;
this is not a claim about an encoder's ability to generalize across observations.

At a represented population optimum, (13) implies
hat_h_i=exp(-c)/m times h_i at every preterminal time. The common scalar does
not affect normalized transition rows or the normalized initial law, so
individual identification of c=-log m is unnecessary. Away from an exact
optimum, it would be incorrect to identify the nuisance and residual
separately merely from their sum.

The existence of a linear gate does not prove that the fixed bound 4 or the
finite optimizer reaches this optimum. The exact unrestricted loss and
posterior are reported precisely so this can be tested rather than assumed.

### 4.2 Comparison settings declared before results

The selected scenarios use V(n_0,n_1)=s(0.35n_0-0.2n_1+0.15n_0n_1):

| Scenario | theta | s |
|---|---:|---:|
| Weak BASE tilt, lower cap pressure | 0.4 | 0.1 |
| Strong BASE tilt, lower cap pressure | 0.4 | 1.0 |
| Strong BASE tilt, higher cap pressure | 2.5 | 1.0 |

These are toy mechanism settings, not real-data hyperparameters or a
claim to span all useful regimes. Each scenario includes all four observation
branches. Both learned routes start their table and nuisance at zero and use
the same AdamW settings: learning rate 0.001, betas=(0.9,0.999), epsilon=1e-8,
zero weight decay, and no fused, foreach, AMSGrad, maximization, capturable or
differentiable optimizer mode.

The full selected run has 2048 updates per learned route, with reported
checkpoints 0,32,128,512,2048. A shorter explicitly requested run is a shorter
diagnostic, not a completed 2048-update curve. Compare exact terminal TV,
target-to-approximation terminal KL, population logistic excess, work counts
and measured time against the independent target and guide-only control.
Report all scenarios and observations, including cases where G+R is worse.
No improvement or publication-level superiority is stipulated in advance.

## 5. Approximate likelihoods require normalized transition rows

Positive learned values hat_h_i need not satisfy hat_h_i=K_i hat_h_{i+1}.
Using hat_h_i in the denominator of (8) would then yield non-stochastic rows.
The selected approximation instead defines

\[
\widehat Z_0=\mu_0\widehat h_0,\qquad
\widehat\mu_0(x)=\frac{\mu_0(x)\widehat h_0(x)}{\widehat Z_0},
\qquad
\widehat K_i(x,y)=
 \frac{K_i(x,y)\widehat h_{i+1}(y)}
      {(K_i\widehat h_{i+1})(x)}.
\tag{15}
\]

This is a well-defined Markov chain for every positive finite hat_h array.
Its terminal law is computed by finite matrix multiplication. When
hat_h_i=h_i, (15) reduces to the exact conditional law. At general learned
values it is a normalized approximation, not an exact Doob transform of the
target endpoint event.

### 5.1 Proposition: harmonic defect gives an exact path-ratio identity

Define

\[
d_i(x)=\log[(K_i\widehat h_{i+1})(x)]-\log\widehat h_i(x).
\tag{16}
\]

Let P^a be the exact conditional grid path law (8) and hat_P the learned
normalized chain (15), both with hat_h_4=g_a. On their common path support,

\[
\frac{\widehat P(x_{0:4})}{P^a(x_{0:4})}
=\frac{m(a)}{\widehat Z_0}
 \exp\!\left[-\sum_{i=0}^3d_i(x_i)\right].
\tag{17}
\]

**Proof.** Substitute
(K_i hat_h_{i+1})(x_i)=hat_h_i(x_i) exp(d_i(x_i))
into the product defining hat_P. All intermediate hat_h values telescope,
leaving the unconditioned path probability times
g_a(x_4) exp(-sum_i d_i)/hat_Z_0. Divide by (10). QED.

This identity precisely states the error remaining after row normalization.
It needs no implication from classification loss to coordinate gradients.

### 5.2 Corollary: a conservative, computable finite-grid TV bound

If max_x |d_i(x)|<=epsilon_i and E=sum_i epsilon_i, then

\[
\operatorname{TV}(\widehat P,P^a),\
\operatorname{TV}(\widehat\mu_4,\mu_4^a)
\le \min\{1,\tfrac12(e^{2E}-1)\}.
\tag{18}
\]

**Proof.** Normalizing (17) gives
hat_Z_0/m=E_{P^a}[exp(-sum_i d_i)]. This lies in [exp(-E),exp(E)].
Therefore the likelihood ratio in (17) lies in
[exp(-2E),exp(2E)]. Integrating half its absolute difference from one yields
the first bound. Marginalization cannot increase total variation, proving
the second. QED.

The bound can be loose or equal to one. State-independent time scaling of
hat_h changes individual defects although normalized physical laws are
unchanged; (18) is sufficient, not necessary, for a useful approximation.
The exact finite terminal TV should therefore be reported alongside it.

Equations (17)–(18) are **finite-grid** algebraic statements about positive
arrays and declared Markov kernels. They neither restore the retired C17
continuous hybrid path theorem nor establish a general logistic-risk-to-path
guarantee. Floating-point error in their computed inputs is a separate
numerical consideration.

## 6. Why querying a new time can change the current learner's target

In the existing FactorizedBasePopulation.sample_pair, a requested time u is
inserted into the sampler's grid before two full independent paths are
generated. The paired observations are taken at those paths' endpoints.
For a fixed u, this defines a valid numerical path law P^{grid(u)} and
the Bayes logit has the form

\[
\ell_u^*(x,a)=\log h_u^{grid(u)}(x,a)-\log m_u(a).
\tag{19}
\]

Unless consistency of that numerical grid family is proved, m_u need not be
constant in u. Independence of the two generated paths does not establish
that consistency. A state-independent correction in the residual might
absorb some nuisance variation where its gate/capacity permits, but the
observation-only nuisance by itself is not a realizability proof.

A simple illustration is the OU SDE dX=-X dt/2+dW, X_0=0. One Euler step of
length one gives terminal variance 1. Inserting time 1/2 and taking two steps
gives variance (3/4)^2/2+1/2=25/32. Adding the same Gaussian observation noise
leaves different endpoint observation variances. Thus inserting a query time
can change evidence for an otherwise identical numerical SDE task.
These are illustrative Euler numbers, not a measurement of the existing
hybrid Heun sampler.

The selected benchmark avoids this ambiguity by (6)–(7): training uses only
the declared grid's preterminal times and one endpoint law. In ideal arithmetic
the finite-CTMC matrix exponential also has a consistent semigroup for added
times, but the benchmark deliberately retains one finite grid and explicit
time weights. No new continuous-time training law is inferred for the legacy
neural code.

## 7. Why coefficient tilting is not exact conditioning of a numerical step

For a suitable continuous-time Markov process and its positive backward
harmonic likelihood h, the formal Doob transform modifies diffusion drift
by a grad(log h) and jump rates by q(x,y)h(y)/h(x), where a is the diffusion
covariance. Under the required regularity, this specifies the conditioned
continuous-time process.

Applying a finite-step Euler, Heun or splitting rule to those modified
coefficients does not generally give the finite-step kernel
K_i(x,dy)h_{i+1}(y)/h_i(x). Discretization and conditioning do not automatically
commute. Moreover, a learned h that is not backward harmonic adds an additional
approximation before discretization is considered.

This benchmark therefore uses finite transition rows (15), not the legacy
continuous-gradient/physical-rate sampler. Its independently computed
posterior error is informative about guide-plus-residual likelihood learning,
initial tilt and row normalization. It does not certify continuous-fiber
gradient accuracy, the hybrid numerical sampler or a full conditional path.

## 8. Cubic decay is not a generic terminal residual property

Let tau denote remaining **active** time before a hold in which no evolution
occurs. For finite generators Q,Q_ref and a strictly positive terminal
likelihood vector g, set

\[
h_\tau=e^{\tau Q}g,\qquad b_\tau=e^{\tau Q_{\rm ref}}g.
\]

Taylor expansion at zero gives, componentwise and uniformly on the finite
state space,

\[
\log h_\tau-\log b_\tau
=\tau\,\frac{(Q-Q_{\rm ref})g}{g}+O(\tau^2).
\tag{20}
\]

Thus equality h_0=b_0=g gives zero residual at the boundary but generically
only first-order approach to zero, not cubic approach. For a direct terminal
baseline b_tau=g, take Q_ref=0 in (20).

### 8.1 Two-state counterexample used by the benchmark diagnostic

Take

\[
Q=\begin{pmatrix}-2&2\\1&-1\end{pmatrix},\qquad
Q_{\rm ref}=\begin{pmatrix}-1&1\\1&-1\end{pmatrix},\qquad
g=(0.2,0.8)^\top.
\tag{21}
\]

A positive endpoint weight suffices; multiplying g by a common constant to
express it relative to a chosen binary observation reference changes none of
the log-likelihood differences or conditioned laws. Direct evaluation gives

\[
e^{\tau Q}g=(0.6-0.4e^{-3\tau},\,0.6+0.2e^{-3\tau})^\top,
\quad
e^{\tau Q_{\rm ref}}g=(0.5-0.3e^{-2\tau},\,0.5+0.3e^{-2\tau})^\top.
\tag{22}
\]

The first-order coefficient in (20) is (3,0). In particular the state contrast
of the required correction is 3 tau+O(tau^2). An observation-only nuisance
cannot remove that state contrast.

A cubic gate a(tau)=(tau/H)^3 multiplying a uniformly bounded raw residual
would require the correction to be O(tau^3). Here its raw state contrast
instead grows as 3H^3/tau^2. Consequently a bounded cubic-gated head cannot
represent this conditional correction arbitrarily near the boundary.
A finite grid can conceal this singular limiting requirement; passing finitely
many replay cases cannot disprove the counterexample.

A cubic gate could be justified for a special model whose first two
coefficients cancel or whose physical clocks vanish sufficiently fast.
Such cancellation or clock behavior needs its own proof. It is not implied
by a clean hold or by smoothness alone.

The current FactorizedSchedule.remaining_clocks multiplies constant rates
by max(S-u-clean_hold,0). Those remaining clock exposures are linear at
the hold boundary; the schedule itself supplies no cubic-decay argument.

### 8.2 What a linear gate resolves, and what it does not

For a(tau)=tau/H, (20) has a finite limiting raw residual. More explicitly,
if g_min=min_x g(x)>0, Markov contraction gives

\[
\|\log e^{\tau Q}g-\log g\|_\infty
\le \tau\,\|Qg\|_\infty/g_{\min}.
\]

Indeed d/dtau e^{tau Q}g=e^{tau Q}Qg, its sup norm is at most ||Qg||_infinity,
and every semigroup likelihood is at least g_min. Applying this to Q and
Q_ref yields

\[
\frac{\|\log h_\tau-\log b_\tau\|_\infty}{\tau/H}
\le
\frac{H}{g_{\min}}
 \big(\|Qg\|_\infty+\|Q_{\rm ref}g\|_\infty\big).
\tag{23}
\]

This finite-generator result removes the generic cubic singularity.
It does not prove that the declared bound 4 is large enough, that a neural
architecture represents the quotient, or that finite optimization finds it.
It also does not automatically extend to an infinite/countable carrier with
unbounded rates or an uncapped analytic guide: the required uniform generator
and likelihood controls must then be established separately.

The selected benchmark adopts the linear gate in (14) as a prospective
structural candidate and measures the resulting approximation. The original
mixed-domain cubic gate is neither silently altered nor newly justified.

## 9. Scientific conclusions this step can support

The independently enumerated posterior and full-population objective allow
the following focused questions to be answered:

1. Does the analytic association baseline reduce posterior error or required
   optimization work relative to DIR for these declared atomic scenarios?
2. How much error is present before residual training, and how does greater
   cap pressure change the uncapped-guide discrepancy?
3. Does improved population logistic risk accompany improved conditional
   posterior error, and where do the metrics disagree?
4. Are remaining errors associated with insufficient residual range,
   finite optimization, initialization, or non-harmonic transition twisting?

The benchmark cannot answer real-domain predictive benefit, full neural
generalization, continuous-fiber conditioning accuracy, production runtime
efficiency or global novelty. Those require separate experiments or proofs.

This step completes a precise common-path conditional-law definition,
the exact grid initializer/Doob proof, an explicit approximate-kernel law,
a computable harmonic-defect bound, and a counterexample to generic cubic
realizability. Extending those choices to the full mixed learner remains an
explicit model-design and implementation decision, not an inference from
successful CPU/GPU parity.

## 10. Independent appendix review

A separate read-only review of the association/initializer appendix checked
the occurrence multiplicities and Janossy normalization, retained Gaussian
ancestor posterior, total-count cap evidence factor, whole-observation
contamination weights, overflow recursion, residual-only rejection proof,
and capped/uncapped boundary-coupling and posterior-TV bounds. The
one-atom hand-computed cap-defect example was also checked algebraically.
No correction was identified in those statements under their stated ideal-law
assumptions.

This is a bounded independent mathematical review, not a claim that floating
point, random number generation, metadata refusal behavior, large-cap runtime
or the subsequent learned sampler inherits exactness from those formulas.
